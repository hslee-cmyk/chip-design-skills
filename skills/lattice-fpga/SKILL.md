---
name: lattice-fpga
description: |
  Lattice FPGA 합성/구현/검증 workflow. iCEcube2/Radiant/Diamond 환경에서 RTL 합성,
  타이밍 분석, 비트스트림 생성, 하드웨어 검증. Lattice FPGA 관련 작업이라면 반드시 이 스킬을 사용.
  다음 상황에서 사용:
  (1) Lattice 프로젝트 구성 - iCEcube2, Radiant(.rdf), Diamond(.ldf) 프로젝트 설정
  (2) Constraints 작성 - .pcf(iCEcube2), .pdc(Radiant), .lpf(Diamond) 핀/타이밍 제약
  (3) IP 활용 - PLL, SERDES, DDR, MIPI 등 Lattice IP 설정
  (4) iCE40 Ultra 하드 IP - SB_HFOSC, SB_IO, SB_IO_OD, SB_GB_IO, SB_I2C, SB_SPI 프리미티브
  (5) Reveal 디버깅 - 내장 로직 분석기 사용 (ILA 대응)
  (6) FPGA vs ASIC 차이 - 합성 최적화, 리소스 고려
  (7) Git submodule 연계 - RTL 공유, UVM 검증 연동
  트리거: Lattice, iCEcube2, Radiant, Diamond, FPGA, iCE40, iCE5LP, Nexus, Certus, ECP5, MachXO, Reveal, .pcf, .pdc, .lpf, SB_IO,
    Yosys, nextpnr, icestorm, Synplify, NVCM, bitstream, SPI Flash, place and route, P&R, iCEBurn, iceprog
---

# Lattice FPGA Synthesis & Implementation Skill

Lattice FPGA 기반 합성/구현/프로그래밍 환경. UVM 검증(Linux)과 Git submodule로 연계.

## 환경 구조

```
fpga_project/                   # FPGA 프로젝트 루트 (Windows)
│
├── .ai/                        # LLM 공통 지식 베이스
│   ├── project.md              #   프로젝트 개요, 아키텍처
│   ├── conventions.md          #   코딩 규칙
│   ├── build.md                #   빌드 방법
│   └── knowledge/              #   도메인 지식
│
├── CLAUDE.md / GEMINI.md / AGENTS.md  # LLM 도구별 진입점
│
├── db/
│   ├── design/  ◄──────────── Git submodule (칩 RTL 공유)
│   │   ├── d_*/mdl/            #   기능 블록별 RTL 모듈
│   │   └── d_filelist.f        #   소스 파일 목록
│   │
│   ├── top/                    # FPGA 전용 탑 모듈
│   │   └── *_fpga_top.v        #   SB_HFOSC, SB_IO 등 하드 IP 인스턴스
│   │
│   ├── sdc/                    # 제약 파일
│   │   ├── *_io.pcf            #   핀 할당 (.pcf)
│   │   └── *.sdc               #   타이밍 제약 (.sdc)
│   │
│   ├── scripts/                 # CLI 빌드 스크립트
│   │   ├── config.sh            #   공유 설정 (디바이스, 소스 목록, 경로)
│   │   ├── build.sh             #   통합 래퍼 (도구 자동 감지, --clean)
│   │   ├── build_*.sh           #   툴체인별 빌드 (icecube2, yosys, …)
│   │   ├── *.tcl                #   벤더 TCL 배치 스크립트
│   │   └── program.sh           #   프로그래밍 (SPI Flash / NVCM)
│   │
│   └── work/                   # iCEcube2 프로젝트
│       └── project_name/       #   빌드 디렉토리
│           ├── *_sbt.project   #     iCEcube2 프로젝트 파일
│           └── *_syn.prj       #     Synplify Pro 설정
│
├── doc/                        # 데이터시트, 사양서
│
├── img/                        # 비트스트림 출력
│   ├── *.bin                   #   SPI Flash 프로그래밍용
│   ├── *.hex                   #   NVCM hex
│   └── *.nvcm                  #   NVCM 전용 포맷
│
└── sim/                        # 시뮬레이션
    └── ip/                     #   Lattice IP 모델 (ILVDS, PUR, ...)
```

## Lattice 툴 선택

| FPGA Family | Tool | Project | Constraints | 특징 |
|-------------|------|---------|-------------|------|
| **iCE40 Ultra (iCE5LP)** | iCEcube2 | .project | .pcf | 초저전력, NVCM, 40nm |
| **iCE40 UltraPlus** | Radiant | .rdf | .pdc | 초저전력 (대기~75µW, 동작~1mW) |
| **MachXO2** | Diamond | .ldf | .lpf | 저전력 + Instant-on |
| **LatticeXP2** | Diamond | .ldf | .lpf | FlashBAK, 비휘발성 |

> **참고**: iCE40 Ultra는 오픈소스 툴체인(Yosys + nextpnr-ice40 + icestorm)도 지원

### 사용 환경
```
iCE40 Ultra            iCE40 UltraPlus       MachXO2              LatticeXP2
─────────────────     ─────────────────     ─────────────────    ─────────────────
Tool: iCEcube2        Tool: Radiant         Tool: Diamond        Tool: Diamond
 (또는 Yosys+nextpnr)
Constraints: .pcf     Constraints: .pdc     Constraints: .lpf    Constraints: .lpf
초저전력 (~71µA stby) 초저전력 (~75µW)      Instant-on           FlashBAK (비휘발)
최대 3.5K LUT         5.3K LUT              최대 6.9K LUT        최대 40K LUT
80Kb EBR, DSP         1Mbit SPRAM           EBR 메모리           EBR + DSP
NVCM 내장             -                     내장 Flash           내장 Flash
```

## 워크플로우

```
┌────────────────────────────────────────────────────────────┐
│ 1. RTL 설계 (Claude + verilog-rtl skill)                  │
│    - 사이클 분석, always 블록 분류                         │
│    - FPGA 리소스 고려 (BRAM, DSP)                         │
├────────────────────────────────────────────────────────────┤
│ 2. Lattice 프로젝트 설정                                  │
│    - RTL 소스 추가 (submodule 경로)                       │
│    - Constraints 작성 (.pcf/.pdc/.lpf)                     │
│    - IP 설정 (PLL, Memory 등)                             │
├────────────────────────────────────────────────────────────┤
│ 3. 합성 & 구현 (Phase 1)                                  │
│    - bash db/scripts/build.sh (iCEcube2 자동 감지)        │
│    - bash db/scripts/build.sh --tool yosys (Yosys 강제)   │
│    - Synthesis → Map → Place & Route → Timer              │
│    - 타이밍 리포트 확인                                    │
│    - 리소스 사용량 확인                                    │
├─── TIMING GATE (필수) ────────────────────────────────────┤
│ ** 반드시 사용자에게 결과를 보여주고 승인을 받아야 함 **   │
│    - Clock Frequency Summary (PASS/FAIL) 테이블 표시      │
│    - 6개 파일 링크 + 주요 정보 요약:                      │
│      1) Timing Report  2) User SDC  3) Synplify SCF      │
│      4) SBT Temp SDC   5) SBT SDC   6) PCF               │
│    - 사용자가 확인 후 bitmap 진행 여부를 결정              │
│    - echo y 파이프 등으로 자동 승인 절대 금지              │
│    → 출력 형식: references/tcl-scripts.md "타이밍 게이트   │
│      출력 형식" 섹션 참조                                  │
├────────────────────────────────────────────────────────────┤
│ 4. Bitmap 생성 (Phase 2) — 사용자 승인 후에만 진행        │
│    - Bitstream 생성 & img/ 복사                           │
├────────────────────────────────────────────────────────────┤
│ 5. FPGA 검증                                              │
│    - bash db/scripts/program.sh (SPI Flash / NVCM)        │
│    - 다운로드 & Reveal로 실시간 디버깅                    │
│    - 하드웨어 동작 확인                                    │
├────────────────────────────────────────────────────────────┤
│ 6. Git Push → UVM 검증 (Linux)                            │
│    - RTL submodule 커밋                                   │
│    - Linux에서 상세 시뮬레이션                            │
└────────────────────────────────────────────────────────────┘
```

## 참조 파일

- `references/device-guide.md` - iCE40 Ultra, iCE40UP, MachXO2, XP2 디바이스 가이드
- `references/constraints-guide.md` - PCF/PDC/LPF 작성법
- `references/reveal-debug.md` - Reveal 디버거 사용법
- `references/fpga-vs-asic.md` - FPGA/ASIC 공통 RTL 작성법
- `references/tcl-scripts.md` - iCEcube2/Radiant/Diamond TCL 자동화
- `references/consistency-map.md` - 일관성 맵

## Cross-Skill 참조

- RTL 설계 규칙, 합성 체크 → `verilog-rtl` skill
- FPGA-UVM 연동, 듀얼탑 아키텍처 → `chip-verification` skill
- UVM 검증환경 설계 (Step 6 Linux 시뮬레이션) → `uvm-verification` skill
