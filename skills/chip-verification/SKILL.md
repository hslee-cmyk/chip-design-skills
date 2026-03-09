---
name: chip-verification
description: |
  RTL-UVM 통합 검증환경 skill. DUT-TB 연결(듀얼탑 구조)과 시스템 레벨 검증 구성에 특화.
  Digital 및 Mixed-Signal(AMS) 모두 지원.
  UVM 컴포넌트 내부 구현보다 "DUT를 어떻게 TB에 연결하고 시스템 전체를 검증할지"가
  핵심인 작업이라면 반드시 이 스킬을 사용. (개별 UVM 컴포넌트 구현은 uvm-verification 사용)
  다음 상황에서 사용:
  (1) 듀얼탑 구조 설계 - hdl_top(DUT+Interface) + hvl_top(UVM) 분리
  (2) RTL-TB 인터페이스 - DUT 포트 → Interface → Virtual Interface 연결
  (3) Reference Model - RTL 사이클 분석 기반 예측 모델 작성
  (4) Scoreboard - Expected vs Actual 비교, 디버그 플로우
  (5) 아날로그 모델 교체 - Behavioral/Wreal/Spectre 선택 (AMS 프로젝트)
  (6) Connect Module - Spectre 연결 시 logic ↔ electrical 변환 (AMS)
  (7) 회귀 테스트 전략 - RTL 변경 시 검증 전략
  트리거: 듀얼탑, dual-top, hdl_top, hvl_top, DUT 연결, interface 연결,
    reference model, scoreboard 설계, AMS 검증환경, mixed-signal testbench,
    Verilog-AMS 시뮬레이션, Spectre, wreal, connect module, regression, 회귀 테스트
---

# Chip Verification Skill

RTL-UVM 통합 검증환경. **Digital 전용** 및 **Mixed-Signal** 프로젝트 모두 지원.

## 프로젝트 타입 선택

```
┌─────────────────────────────────────────────────────────────┐
│  Digital 전용                  Mixed-Signal (AMS)          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  chip_top.v                    chip_top.v                  │
│  └── digital_core              ├── digital_core            │
│                                └── analog_top (교체 가능)  │
│                                    ├── _behav.sv  (빠름)   │
│                                    ├── _wreal.sv  (중간)   │
│                                    └── _spectre.vams (정밀)│
│                                                             │
│  참조:                          참조:                       │
│  - interface-mapping.md        - 위 전부 +                 │
│  - refmodel-patterns.md        - analog-model-levels.md    │
│  - debug-flow.md               - connect-modules.md        │
│  - regression-strategy.md      - wreal-modeling.md         │
│                                - spectre-integration.md    │
└─────────────────────────────────────────────────────────────┘
```

## 듀얼탑 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        hdl_top.sv                           │
│                  [DUT + Interface Layer]                    │
├─────────────────────────────────────────────────────────────┤
│  ┌───────────────────────────────────────────────────────┐ │
│  │                 chip_top.v (Verilog)                  │ │
│  │  ┌──────────────────┐    ┌──────────────────────┐    │ │
│  │  │  Digital Core    │◄──►│  analog_top (옵션)   │    │ │
│  │  │  (컨트롤러, DSP) │    │  (AMS 프로젝트만)    │    │ │
│  │  └──────────────────┘    └──────────────────────┘    │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Interface (SystemVerilog)                │ │
│  │           Clocking blocks, Modports, Assertions       │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  Clock, Reset generation                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ virtual interface (config_db)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        hvl_top.sv                           │
│                   [UVM Environment]                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Agent     │  │  Reference  │  │    Scoreboard       │ │
│  │ (Drv/Mon)   │  │   Model     │  │  (Exp vs Actual)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                             │
│  config_db 설정, run_test(), Coverage                       │
└─────────────────────────────────────────────────────────────┘
```

**장점:**
- HDL/HVL 명확한 분리
- 에뮬레이션 환경 지원 (hdl_top만 합성)
- Digital/AMS 동일 구조
- 아날로그 모델 교체 용이 (AMS)

## 워크플로우

### 공통 (Digital & AMS)

```
1. RTL 설계      → verilog-rtl skill 참조
2. Interface     → references/interface-mapping.md
3. Ref Model     → references/refmodel-patterns.md  
4. Scoreboard    → assets/tb-template/
5. 디버깅        → references/debug-flow.md
6. 회귀 테스트   → references/regression-strategy.md
```

### AMS 추가 단계

```
A1. 아날로그 모델 선택  → references/analog-model-levels.md
A2. Connect Module     → references/connect-modules.md (Spectre 사용 시)
A3. Wreal 모델 작성    → references/wreal-modeling.md
A4. Spectre 연결       → references/spectre-integration.md
```

## 아날로그 모델 교체 (AMS 전용)

```
┌─────────────────────────────────────────────────────────────┐
│ 시뮬레이션 목적에 따라 analog_top만 교체                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  빠른 회귀 테스트    중간 정확도        정밀 검증            │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Behavioral  │   │   Wreal     │   │  Spectre    │       │
│  │ (SV real)   │   │ (이벤트)    │   │  (SPICE)    │       │
│  │ ~1000x 빠름 │   │  ~10x 빠름  │   │  기준 속도   │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         │                 │                 │               │
│         └─────────────────┼─────────────────┘               │
│                           ▼                                 │
│                  동일한 UVM 환경                            │
└─────────────────────────────────────────────────────────────┘

컴파일 옵션:
  make sim ANALOG_MODEL=BEHAV     # 일일 회귀
  make sim ANALOG_MODEL=WREAL     # 주간 회귀
  make sim ANALOG_MODEL=SPECTRE   # 테잎아웃 전
```

## 참조 파일

### 공통 (Digital & AMS)
- `references/interface-mapping.md` - RTL 포트 → Interface 변환
- `references/refmodel-patterns.md` - Reference Model 작성 패턴
- `references/debug-flow.md` - 시뮬레이션 실패 → RTL 버그 추적
- `references/regression-strategy.md` - RTL 변경 시 회귀 테스트 전략

### AMS 전용
- `references/analog-model-levels.md` - Behavioral/Wreal/Spectre 모델 작성
- `references/connect-modules.md` - logic ↔ electrical 변환
- `references/wreal-modeling.md` - Real-number 모델링
- `references/spectre-integration.md` - Spectre 설정

### 템플릿
- `assets/tb-template/` - 듀얼탑 테스트벤치 템플릿

## Cross-Skill 참조

- RTL 설계 규칙, 사이클 분석 → `verilog-rtl` skill
- UVM 컴포넌트, 시퀀스, Coverage → `uvm-verification` skill
- AMS behavioral model 작성 (Verilog-A) → `verilog-a` skill
