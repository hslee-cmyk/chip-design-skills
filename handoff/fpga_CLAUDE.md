# FPGA Project — Claude Instructions

## 실행 환경

- 셸: MSYS2 bash (`/c/msys64/usr/bin/bash`)
- Python: `C:\Python314\python.exe` (Windows 네이티브, 3.14.2)
- 하드웨어: OSS CAD Suite 내장 `libftdi1.dll`, `libusb-1.0.dll` → FTDI 기반 FPGA 프로그래머 연결 가능

## OSS CAD Suite (FPGA 핵심 툴)

설치 경로: `C:\oss-cad-suite\oss-cad-suite\`

모든 FPGA 관련 작업 전 PATH 설정 필수:
```bash
export PATH="/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:$PATH"
```

툴 목록 및 워크플로우 → `lattice-fpga` skill  
Formal verification → `formal-verification` skill

verilator (5.047), gtkwave (3.4.0) OSS CAD Suite에 포함 — PATH 설정 후 바로 사용 가능.
시뮬레이션은 verilator 사용 (lint + C++ testbench 빌드).

## ngspice (아날로그 SPICE 시뮬레이터)

설치 경로: `C:\ngspice\Spice64\bin\`

OSS CAD Suite는 디지털/FPGA 전용이라 아날로그 SPICE 툴이 없음 — 별도 설치(ngspice-46, Windows 네이티브
빌드, BSD 계열 라이선스). 아날로그 회로 sizing/특성화 작업 전 PATH 설정 필요:
```bash
export PATH="/c/ngspice/Spice64/bin:$PATH"
```
배치 실행은 `ngspice_con.exe`(콘솔 전용, GUI 없음) 사용 권장: `ngspice_con.exe -b <netlist.cir>`.

용도: gm/ID 공정 LUT 생성(오픈소스 PDK 예: sky130, gf180mcu와 조합) → `analog-gmid-design` skill의
`references/lut-generation-checklist.md` §2/§7 참조.

## ★graph 단일 정본 -- 계산과 cache는 graph로만 (analog-gmid-design, 사용자 지정 2026-10-20)

계획·design·spec card 문서를 쓸 때와 엔진 code를 쓸 때 모두 지킨다. 잘못된 구현이나 문서 기술을 막기 위한 강제 규칙이다.

1. **계산값은 graph 필드로만 둔다.** 필드마다 writer 블록은 하나다. 다른 곳은 그 필드를 READS로 읽는다. 같은 값을 다른 자리에서 다시 계산하는 둘째 생산자는 금지한다.
2. **재사용(cache)은 두 길만 쓴다.**
   - graph reuse: 입력 버전이 같으면 그대로 쓴다.
   - 실행 수명 S3 블록 결과 색인: (블록, 분할, 입력 버전) 키로 graft한다.

   새 cache, memo, dict, context 슬롯(`sctx.*` 등), 결과 객체의 값 칸(`EvalResult` 값 칸 등), 값 사본은 만들지 않는다. 쓸 수 있는 예외는 계획 N3.3·N3.5가 적은 승인 예외뿐이다. LUT memo·파생표 디스크 캐시(U-87), 블록 안 local memo(O-15 (E)), `ly_point` 사본 부채(O-27·LI-1) 등이 여기에 해당한다.
3. **같은 정의의 양은 필드 하나로 둔다.** 정의가 다를 때만 새 필드를 둔다. 이때 어떤 축(측정 구성, 판정 여유, 정밀도 등)이 다른지 문서에 적는다.
4. **단계 사이 전달은 참조로 한다.** 값 사본 대신 graph 필드나 기록 참조(`record_id` 등)를 넘긴다.
5. **스냅샷 파생 규칙**(gain-budget 계획 v6.22 N3.3, O-61 P1): child 스냅샷에는 `ctx.base`에 있는 writer(그 스냅샷의 `block_versions`) ∪ 그 평가가 부르는 블록이 쓴 필드만 남긴다. 봉인 4는 base writer ∩ 부르는 블록 = ∅을 단언한다. `_CONTEXT_WRITERS`는 `context_fp` 전용이라 keep 정본이 아니다.
6. **정본 자리가 없으면 멈추고 보고한다.** 정본 자리를 찾지 못하거나 graph 밖 저장이 필요해 보이면 만들지 않는다. 계획부터 고친다(S-7).
7. **전달·검증 단계에서도 이 규칙으로 점검한다.**
   - 오케스트레이터는 agent의 권고나 design 판단을 사용자에게 전하기 전에 이 규칙으로 점검한다.
   - 모든 작성 agent 브리핑에 이 규칙을 넣는다.
   - design-validator, 감사자, 판정자는 위반 여부를 별도 검사 항목으로 둔다.

## MSYS2 보조 툴

| 툴 | 버전 | 용도 |
|----|------|------|
| `ghdl` | 5.1.1 (LLVM) | VHDL 시뮬레이터 |
| `gcc` | 15.2.0 | C/C++ 컴파일러 (MinGW) |
| `tclsh` | 8.6.17 | Tcl 스크립트 실행 |

## Skills

| Skill | 트리거 | 용도 |
|-------|--------|------|
| `lattice-fpga` | Lattice, iCEcube2, nextpnr, iCE40, .pcf, P&R, bitstream | FPGA 합성/구현/프로그래밍 워크플로우 |
| `formal-verification` | formal, sby, BMC, assert property, SMT, z3 | RTL formal verification |
| `verilog-rtl` | always, FSM, CDC, synthesis, lint | RTL 설계 규칙 |
| `chip-verification` | testbench, simulation, coverage | 기능 검증 |
| `uvm-verification` | UVM, sequence, agent, scoreboard | UVM 환경 |
| `verilog-a` | Verilog-A, analog, behavioral model | 아날로그 모델링 |
| `kb-promote` | kb-global 격상, promote to global, sync_rules [B], toolflow 격상 | docs/solutions → kb-global 격상 워크플로우 |

Skills 위치: `~/.claude/skills/`
