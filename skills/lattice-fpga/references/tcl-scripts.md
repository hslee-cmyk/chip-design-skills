# Lattice TCL Scripts Guide

## iCEcube2 TCL

### 프로젝트 생성

```tcl
# create_project.tcl - iCEcube2

# 새 프로젝트 생성
# Device: iCE5LP4K, Package: SWG36 (WLCSP)
set device iCE5LP4K
set package SWG36
set project_name "venezia_test"

# iCEcube2 프로젝트 디렉토리 설정
set project_dir [file join [pwd] $project_name]
file mkdir $project_dir

# 프로젝트 생성
open_project $project_dir

# 디바이스 설정
set_device -device $device -package $package

# RTL 소스 추가 (submodule 경로)
add_file -verilog "../rtl/digital/venezia_test_fpga_top.v"
add_file -verilog "../rtl/digital/cola_master.v"
add_file -verilog "../rtl/digital/pcm_receiver.v"

# Constraints 추가
add_file -constraint "constraints/venezia_test_fpga_top_swg36_io.pcf"

# SDC 타이밍 제약 추가
add_file -sdc "constraints/timing.sdc"

# 프로젝트 저장
save_project
close_project
```

### 빌드 스크립트

iCEcube2에는 `sbt_tcl.exe` 같은 통합 TCL 셸이 **없다**.
빌드는 시스템 `tclsh`로 TCL 스크립트를 실행하고, 스크립트 내에서
SBT 공식 TCL API(`sbt_backend/tcl/sbt_backend_synpl_top.tcl`)를 `source`하여
개별 단계를 호출하는 방식이다.

#### 빌드 흐름 (2-phase, 타이밍 게이트 포함)

```
Phase 1: synth → edifparser → placer → packer → router → netlister → timer
                                                                        ↓
                                              ┌─── TIMING GATE ────────┐
                                              │  타이밍 리포트 표시    │
                                              │  SDC/PCF 제약 표시     │
                                              │  사용자 승인 필요      │
                                              └────────────────────────┘
                                                                        ↓
Phase 2: bitmap → 출력 복사 (img/*.bin, *.hex, *.nvcm)
```

> **중요**: Bitmap(이미지) 생성 전에 반드시 타이밍 리포트를 확인하고
> 사용자가 승인해야 진행된다. `build_icecube2.sh` 가 이 게이트를 강제한다.

> **Claude 실행 규칙 (필수)**:
> 합성 실행 시 `echo y | build.sh` 등으로 타이밍 게이트를 자동 승인하지 마라.
> 반드시 다음 절차를 따를 것:
> 1. Phase 1만 실행 (`echo n | build.sh` 또는 `tclsh synth_icecube2.tcl`)
> 2. 아래 **타이밍 게이트 출력 형식**대로 사용자에게 보고
> 3. 사용자가 승인하면 Phase 2 실행 (`tclsh synth_icecube2.tcl --bitmap-only`)
> 4. 사용자 승인 없이 bitmap을 생성하는 것은 금지

#### 타이밍 게이트 출력 형식 (Claude 필수)

Phase 1 완료 후 사용자에게 아래 형식으로 보고한다:

```
Phase 1 완료. 타이밍 결과입니다:

**Clock Frequency Summary:**
| Clock | Frequency | Target | Result |
|-------|-----------|--------|--------|
| <clock_name> | XX.XX MHz | XX.XX MHz | **PASS** / **FAIL** |
| ...   | ...       | ...    | ...    |

**Constraint / Report Files:**

**1. Timing Report** — `<프로젝트 상대 경로>`
> <clock 수, PASS/FAIL 요약>

**2. User SDC** — `<프로젝트 상대 경로>`
> <create_clock 수와 각 clock 이름/주기 요약>

**3. Synplify SCF** — `<프로젝트 상대 경로>`
> <master clock, generated clock 수, false_path 수 요약>

**4. SBT Temp SDC** — `<프로젝트 상대 경로>`
> <edifparser 변환 결과 요약, generated→독립 clock 변환 여부>

**5. SBT SDC (P&R)** — `<프로젝트 상대 경로>`
> <netlister 최종 출력, clock 수, Temp SDC 대비 차이>

**6. PCF** — `<프로젝트 상대 경로>`
> <I/O 핀 수, 입력/출력 핀 목록 요약>
```

- 파일 경로는 프로젝트 루트 기준 상대 경로로 표시 (사용자가 링크로 열 수 있도록)
- 각 파일의 주요 정보를 1-2줄로 요약
- 보고 후 AskUserQuestion으로 bitmap 진행 여부를 반드시 확인

#### Phase 1 (tclsh로 실행)

```tcl
# synth_icecube2.tcl — Phase 1: Synth + Route + Timer
set sbt_root "C:/lscc/iCEcube2.2020.12"
set sbt_backend "$sbt_root/sbt_backend"
set ::env(SBT_DIR) $sbt_backend

# SBT 공식 TCL API 로드
source "$sbt_backend/tcl/sbt_backend_synpl_top.tcl"

# Step 1: Synplify Pro 합성
exec "$sbt_backend/bin/win32/opt/synpwrap/synpwrap.exe" \
    -prj venezia_syn.prj -log synth.log

# Step 2-6: SBT 개별 단계 호출
sbt_init_env
sbt_init_dirs $proj_dir $impl_subdir
sbt_run_edifparser_ip ...   ;# EDF → 내부 넷리스트
sbt_run_placer ...           ;# 배치
sbt_run_packer ...           ;# 패킹
sbt_run_router ...           ;# 라우팅
sbt_run_verilog_netlister .. ;# 넷리스트 생성 (timer SDC 필요)
sbt_run_timer_utility ...    ;# 타이밍 분석 → timing.rpt

# ▶ 여기서 종료 — bitmap은 Phase 2에서
```

#### Timing Gate (bash)

```bash
# build_icecube2.sh 가 Phase 1 후 자동으로 표시:
#   1. Clock Frequency Summary (PASS/FAIL 판정)
#   2. User SDC 파일 내용
#   3. Synplify SCF (합성 후 제약)
#   4. SBT Temp SDC (edifparser 변환)
#   5. SBT SDC (P&R 후 netlister 출력)
#   6. PCF 핀 제약 파일 내용
#
# 타이밍 리포트 위치:
#   db/work/venezia/venezia_Implmnt/sbt/outputs/router/<top>_timing.rpt
#
# 사용자가 y 입력 시 Phase 2 진행, 아니면 중단
read -r -p "[GATE] Proceed to bitmap generation? [y/N] " REPLY
```

#### Phase 2 (bitmap)

```tcl
# synth_icecube2.tcl --bitmap-only
sbt_run_bitmap ...           ;# 비트스트림 생성
# 출력: .bin (SPI Flash), .hex, .nvcm (OTP)
```

#### 필수 환경변수

```bash
export SBT_DIR="$ICECUBE2_PATH/sbt_backend"
export SYNPLIFY_PATH="$ICECUBE2_PATH/synpbase"
export LM_LICENSE_FILE="$ICECUBE2_PATH/license/license.dat"
```

> **iCEcube2 버그**: `sbt_run_edifparser_ip` 에 `--devicename` 옵션 누락.
> `synth_icecube2.tcl`에서 패치하여 수정됨.

### iCEcube2 Synplify 옵션

```tcl
# synplify_options.tcl

# Verilog define 설정 (예: CE5 매크로)
set_option -vlog_define CE5

# 최적화 목표
set_option -optimization_goal area    ;# area / speed
set_option -frequency 12              ;# 목표 주파수 (MHz)

# FSM 인코딩
set_option -symbolic_fsm_compiler true
set_option -resource_sharing true

# 합성 결과 포맷
set_option -write_verilog true
set_option -write_apr_constraint true
```

### NVCM / SPI 프로그래밍

```tcl
# program.tcl - iCEcube2 Programmer

# Diamond Programmer를 사용 (iCEcube2는 Diamond Programmer 호출)
# 또는 Lattice 독립 프로그래머 사용

# SPI Flash 프로그래밍
# pgr_project open "program.xcf"
# pgr_program run

# 커맨드라인 프로그래밍 (iceprog - 오픈소스)
# iceprog venezia_test.bin          # SPI Flash
# iceprog -n venezia_test.nvcm      # NVCM (비가역!)
```

> **NVCM 주의**: NVCM 프로그래밍은 **비가역(OTP)**. 한 번 쓰면 변경 불가.
> 개발 중에는 반드시 SPI Flash 사용.

## 오픈소스 빌드 플로우 (Yosys + nextpnr-ice40)

iCE40 Ultra는 오픈소스 툴체인으로도 합성 가능. 단, 알려진 제약이 있음.

### 빌드 실행

```bash
# 자동 감지 (iCEcube2 우선, Yosys fallback)
bash db/scripts/build.sh

# Yosys 강제
bash db/scripts/build.sh --tool yosys
```

스크립트: `config.sh` → `build.sh` → `build_yosys.sh`
출력: `db/work/yosys_build/` (중간), `img/*_bitmap.bin` (최종)

### 빌드 4단계

1. **Yosys 합성**: `synth_ice40 -device u -abc2` → JSON
2. **nextpnr P&R**: `--u4k --package sg48 --pre-pack prepack_swg36.py` → ASC
3. **icepack**: ASC → BIN
4. **icetime**: 타이밍 분석 (선택)

### 핵심 설정 (config.sh)

```bash
DEVICE_NEXTPNR="u4k"           # iCE5LP4K (up5k 아님!)
PACKAGE_LOWER="swg36"          # 실제 HW 패키지
DEFINES="TODOC_FUNC CE5 INC_EXT_DTOP"  # 3개 define 필수
```

### 알려진 제약 (2026-03 검증)

| 제약 | 원인 | 우회 방법 |
|------|------|-----------|
| **SWG36 패키지 미지원** | nextpnr chipdb에 sg48만 존재 | `--package sg48` + `prepack_swg36.py`로 SG48 호환 핀만 배치. 6핀(A2,B1,B4,D2,E5,F4)은 SG48에 대응 IO tile 없어 자동 배치 |
| **SB_IO_OD 미지원** | nextpnr가 iCE40 Ultra 전용 오픈드레인 프리미티브 미구현 | `ifdef YOSYS` → SB_IO 트라이스테이트로 대체 (venezia_test_fpga_top.v) |
| **BRAM 미추론** | FIFO의 비동기 리셋 읽기 패턴이 Yosys BRAM 규칙과 불일치 | **미해결**. Yosys 4494 LUT (128%) vs iCEcube2 1885 LC (54%)+BRAM 3개. 공유 RTL 수정 필요 |
| **Combinational loop** | 리셋 가드 셀 CKE 경로 | `--ignore-loops` 플래그 |
| **경로 인식** | Yosys(OSS CAD Suite)가 Git Bash `/c/...` 절대경로 미인식 | 상대 경로 사용 (`cd $PROJECT_ROOT` 후) |

> **현재 상태**: Step 1 합성 성공, Step 2 P&R은 BRAM 미추론으로 LUT 초과 실패.
> 공유 RTL의 FIFO 비동기 리셋을 동기 리셋으로 변경하면 BRAM 추론 가능.

### 도구 설치 (OSS CAD Suite)

yosys 0.64+68, nextpnr-0.10, icepack/iceprog/icetime 모두 OSS CAD Suite에 포함.

```bash
# PATH 설정 (build_yosys.sh 또는 config.sh에 추가)
export PATH="/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:$PATH"
```

`config.sh`에 위 export를 추가하면 빌드 스크립트에서 자동으로 사용됨.

---

## Radiant TCL

### 프로젝트 생성

```tcl
# create_project.tcl

# 새 프로젝트 생성
prj_create -name "my_project" \
           -impl "impl_1" \
           -dev LIFCL-40-9BG400C \
           -synthesis "synplify"

# RTL 소스 추가 (submodule 경로)
prj_add_source "../rtl/digital/top.v"
prj_add_source "../rtl/digital/core.v"
prj_add_source "../rtl/digital/fsm.v"

# Constraints 추가
prj_add_source "constraints/pins.pdc"
prj_add_source "constraints/timing.pdc"

# IP 추가
prj_add_source "ip/pll/pll.ipx"

# 프로젝트 저장
prj_save
```

### 빌드 스크립트

```tcl
# build.tcl

# 프로젝트 열기
prj_open "my_project.rdf"

# Synthesis
prj_run Synthesis -impl impl_1

# Map
prj_run Map -impl impl_1

# Place & Route
prj_run PAR -impl impl_1

# Bitstream 생성
prj_run Export -impl impl_1 -task Bitstream

# 리포트 확인
prj_run Export -impl impl_1 -task TimingReport

prj_close
```

### 배치 실행

```powershell
# Windows PowerShell
& "C:\lscc\radiant\3.2\bin\nt64\pnmainc.exe" build.tcl

# 또는 래퍼 스크립트
radiantc build.tcl
```

## Diamond TCL

### 프로젝트 생성

```tcl
# create_project.tcl

# 새 프로젝트
prj_project new -name "my_project" \
                -impl "impl1" \
                -dev LFE5U-45F-8BG381C \
                -synthesis "synplify"

# 소스 추가
prj_src add "../rtl/top.v"
prj_src add "../rtl/core.v"

# Constraints
prj_src add "pins.lpf"

# 저장
prj_project save
```

### 빌드 스크립트

```tcl
# build.tcl

prj_project open "my_project.ldf"

# 전체 빌드
prj_run Synthesis -impl impl1
prj_run Translate -impl impl1
prj_run Map -impl impl1
prj_run PAR -impl impl1
prj_run Export -impl impl1 -task Bitstream

prj_project close
```

## 자동화 Makefile

```makefile
# Makefile for Lattice FPGA

#--------------------------------------------
# Tool Paths
#--------------------------------------------
ICECUBE2_PATH := C:/lscc/iCEcube2.2020.12
RADIANT_PATH  := C:/lscc/radiant/3.2/bin/nt64
DIAMOND_PATH  := C:/lscc/diamond/3.12/bin/nt64

# Tool 선택: icecube2 / radiant / diamond
TOOL ?= radiant

# iCEcube2: sbt_tcl.exe 없음 — 시스템 tclsh로 TCL 스크립트 실행
# Radiant/Diamond: pnmainc.exe 가 TCL 셸 역할
ifeq ($(TOOL), icecube2)
    TCL_SHELL := tclsh
else ifeq ($(TOOL), radiant)
    TCL_SHELL := $(RADIANT_PATH)/pnmainc.exe
else
    TCL_SHELL := $(DIAMOND_PATH)/pnmainc.exe
endif

#--------------------------------------------
# Project
#--------------------------------------------
PROJECT := my_project
IMPL    := impl_1

#--------------------------------------------
# Targets
#--------------------------------------------
.PHONY: all synth par bit program clean

all: bit

# 합성만
synth:
	$(TCL_SHELL) scripts/synth.tcl

# Place & Route
par: synth
	$(TCL_SHELL) scripts/par.tcl

# Bitstream
bit: par
	$(TCL_SHELL) scripts/bitgen.tcl

# 프로그램
program:
	$(TCL_SHELL) scripts/program.tcl

# 클린
clean:
	rm -rf $(PROJECT)_$(IMPL)
	rm -rf synlog par_* *.bit *.bin

#--------------------------------------------
# RTL submodule 업데이트
#--------------------------------------------
update_rtl:
	cd ../rtl && git pull
```

## 유용한 TCL 명령

### 리포트 확인

```tcl
# 타이밍 요약
prj_run Export -impl impl_1 -task TimingReport

# 리소스 사용량
prj_run Export -impl impl_1 -task AreaReport

# 전력 예측
prj_run Export -impl impl_1 -task PowerReport
```

### 조건부 빌드

```tcl
# 에러 체크 후 진행
if {[prj_run Synthesis -impl impl_1] != 0} {
    puts "ERROR: Synthesis failed"
    exit 1
}

if {[prj_run PAR -impl impl_1] != 0} {
    puts "ERROR: PAR failed"
    exit 1
}

puts "Build successful!"
```

### 타이밍 확인

```tcl
# 타이밍 위반 체크
set timing_rpt [prj_get_timing_report -impl impl_1]

if {[regexp {Timing constraint NOT met} $timing_rpt]} {
    puts "WARNING: Timing not met!"
    # 상세 리포트 출력
    puts $timing_rpt
}
```

## CI/CD 통합

```yaml
# .github/workflows/fpga_build.yml (예시)
name: FPGA Build

on:
  push:
    paths:
      - 'rtl/**'
      - 'fpga/**'

jobs:
  build:
    runs-on: self-hosted  # Lattice 툴이 설치된 러너
    steps:
      - uses: actions/checkout@v2
        with:
          submodules: recursive
      
      - name: Build FPGA
        run: |
          cd fpga
          make bit
      
      - name: Upload Bitstream
        uses: actions/upload-artifact@v2
        with:
          name: bitstream
          path: fpga/*.bit
```
