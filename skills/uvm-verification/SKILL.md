---
name: uvm-verification
description: |
  UVM (Universal Verification Methodology) 컴포넌트 구현 skill.
  agent, driver, monitor, scoreboard 등 개별 UVM 컴포넌트를 작성하거나
  UVM 검증 방법론(sequence, RAL, factory, coverage)을 적용하는 작업이라면
  반드시 이 스킬을 사용.
  다음 상황에서 사용:
  (1) UVM 환경 계층 설계 - agent, env, test 구성, config object, package 구조
  (2) 컴포넌트 작성 - driver, monitor, sequencer, scoreboard, predictor
  (3) 시퀀스/트랜잭션 - sequence item, virtual sequence, arbitration, pipelined
  (4) Coverage 연동 - uvm_subscriber, functional coverage, testplan, closure
  (5) Register Model (RAL) - register block, adapter, explicit prediction
  (6) 시뮬레이션 디버깅 - 로그 해석, report catcher, factory/config 문제
  (7) Factory / Config DB - factory override, config object 패턴
  (8) 고급 패턴 - slave agent, persistence, polymorphism, integration-level TB
  트리거: UVM, uvm_driver, uvm_monitor, uvm_agent, uvm_env, uvm_test,
    sequence, uvm_sequence_item, virtual sequence, scoreboard, RAL, config_db, factory,
    objection, uvm_subscriber, report catcher, TLM, analysis port, BFM
---

# UVM Verification Skill

UVM 기반 검증환경 구축 시 **계층 구조**, **phase 흐름**, **TLM 통신**을 핵심으로 다룬다.

## UVM 계층 구조

```
uvm_test
└── uvm_env
    ├── uvm_agent (active/passive)
    │   ├── uvm_sequencer
    │   ├── uvm_driver
    │   └── uvm_monitor
    ├── uvm_predictor
    ├── uvm_scoreboard
    ├── uvm_subscriber (coverage)
    └── uvm_reg_block (optional)
```

## 핵심 Phase 순서

```
[Build Phase]     build_phase()      → 컴포넌트 생성, config 설정
[Connect Phase]   connect_phase()    → TLM 포트 연결
[Run Phase]       run_phase()        → 시뮬레이션 실행 (time-consuming)
[Extract Phase]   extract_phase()    → 메트릭 수집
[Check Phase]     check_phase()      → 최종 검증
[Report Phase]    report_phase()     → 결과 출력
```

**주의:** build_phase는 top-down, connect_phase는 bottom-up 실행

### 추가 Phase

| Phase | 실행 | 용도 |
|-------|------|------|
| `end_of_elaboration_phase` | Bottom-up | 토폴로지 출력 (`print_topology`), 최종 구조 조정 |
| `start_of_simulation_phase` | Bottom-up | 배너 출력, 초기 설정 확인 |
| `final_phase` | Top-down | 시뮬레이션 종료 직전 마지막 정리 |

### Run-Time Sub-Phases (run_phase와 병렬 실행)

```
run_phase ─────────────────────────────────── (전체 기간)
  pre_reset → reset → post_reset →
  pre_configure → configure → post_configure →
  pre_main → main → post_main →
  pre_shutdown → shutdown → post_shutdown
```

- 대부분의 TB는 `run_phase`만 사용하면 충분
- Sub-phase 사용 시: 각 sub-phase에서 개별 objection raise/drop 필요
- `set_automatic_phase_objection(1)`: sequence에서 자동 objection (UVM 1.2+)

## 핵심 원칙

| 원칙 | 설명 |
|------|------|
| `uvm_field_*` 금지 | 성능 저하, 예측 불가. do_copy/do_compare/convert2string 직접 구현 |
| `uvm_do_*` 금지 | 흐름 숨김. start_item/finish_item + late randomization 사용 |
| Objection은 test/vseq에서만 | Driver/Monitor에서 objection 금지 |
| Explicit prediction 권장 | set_auto_predict(0) + uvm_reg_predictor 사용 |
| Config object 단위 전달 | 개별 필드가 아닌 config object 1개로 set/get |

## 필수 코딩 패턴

컴포넌트 등록(`uvm_component_utils`), 트랜잭션 등록(`uvm_object_utils`), Config DB 사용(set/get) 패턴:
→ `references/component-templates.md` 참조

## 워크플로우

1. **스펙 분석** → 검증 항목, coverage 목표 정의
2. **TB 아키텍처 설계** → config object, TB 클래스 계층, 조건부 빌드 (dual-top 구조는 chip-verification 참조)
3. **인터페이스 정의** → DUT 포트 기반 interface/BFM 작성
4. **트랜잭션 설계** → 자극/응답 데이터 모델링 (request=rand, response=NOT rand)
5. **Agent 구현** → Driver, Monitor, Sequencer
6. **Env 통합** → Predictor, Scoreboard, Coverage, Agent 연결
7. **Register Model** → RAL 정의, adapter, explicit prediction (필요 시)
8. **시퀀스 설계** → Sequence 계층, virtual sequence, arbitration
9. **테스트 작성** → Test + factory override + objection
10. **Coverage 분석** → UVM coverage subscriber + closure
    - SV covergroup/bins/cross 문법 → `verilog-rtl` skill
    - UVM subscriber 연동, testplan, closure → 본 스킬 item (4)

## 참조 파일

- `references/component-templates.md` — 각 컴포넌트 상세 템플릿 + config/predictor/scoreboard 패턴
- `references/sequence-patterns.md` — 시퀀스 작성 패턴 + driver use model + arbitration + interrupt
- `references/coverage-guide.md` — UVM coverage subscriber + register coverage 연동
- `references/debug-guide.md` — 시뮬레이션 디버깅 전략 + report catcher
- `references/ral-guide.md` — Register Abstraction Layer 전체 가이드
- `references/testbench-architecture.md` — Dual-top, DUT connection, config, factory, objection
- `assets/agent-template/` — 복사해서 사용할 agent 템플릿

## Cross-Skill 참조

- SV covergroup/coverpoint/bins/cross 문법 → `verilog-rtl` skill (UVM 없이 SV standalone 문법)
- UVM coverage 연동, testplan, closure는 본 스킬(item 4) 담당
- RTL-TB 인터페이스, 검증 프로세스 → `chip-verification` skill
- FPGA 구현, 비트스트림 → `lattice-fpga` skill
