# Consistency Map

## 사용법

SKILL.md 원칙 수정 시:
1. 아래 맵에서 해당 원칙의 반영 위치 확인
2. 모든 반영 위치를 함께 업데이트
3. **수정 후: `../skill-validation-prompt.md` 절차(6-Check)로 일관성 검증**

## 원칙별 반영 위치

| 원칙 | SKILL.md 섹션 | reference 반영 위치 |
|------|--------------|-------------------|
| UVM 계층 구조 (test→env→agent) | UVM 계층 구조 | component-templates > Agent, Env, Test |
| Phase 순서 (build→connect→run→extract→check→report) | 핵심 Phase 순서 | component-templates > 각 컴포넌트, debug-guide > Phase 디버깅 |
| build=top-down, connect=bottom-up | 핵심 Phase 순서 (주의 문구) | debug-guide > Phase 디버깅 |
| 컴포넌트 등록 (`uvm_component_utils`) | 필수 코딩 패턴 | component-templates > 모든 class |
| 트랜잭션 등록 (`uvm_object_utils`) | 필수 코딩 패턴 | component-templates > Transaction |
| 트랜잭션 필수 메서드 (do_copy/compare/convert2string) | - | component-templates > Transaction |
| Config DB set/get 패턴 | Config DB 사용 | component-templates > Driver, debug-guide > Config DB, testbench-architecture §6 |
| Active/Passive Agent | - | component-templates > Agent |
| TLM 포트 연결 | - | component-templates > Agent connect_phase, debug-guide > TLM |
| uvm_field_* 금지 | 핵심 원칙 테이블 | component-templates > Transaction, testbench-architecture §9 |
| uvm_do_* 금지 | 핵심 원칙 테이블 | sequence-patterns > Anti-patterns, testbench-architecture §9 |
| Objection은 test/vseq에서만 | 핵심 원칙 테이블 | testbench-architecture §8, debug-guide > Objection 규칙 |
| Explicit prediction 권장 | 핵심 원칙 테이블 | ral-guide §5, coverage-guide §4 |
| Config object 단위 전달 | 핵심 원칙 테이블 | testbench-architecture §6, component-templates > Config Object |
| Sequence 패턴 (basic/constrained/layered/virtual) | 워크플로우 #8 | sequence-patterns > 전체 |
| Virtual Sequence (null sequencer, init_vseq) | 워크플로우 #8 | sequence-patterns > Virtual Sequence |
| Late Randomization | - | sequence-patterns > Late Randomization |
| Sequence Arbitration (6종) | - | sequence-patterns > Arbitration |
| Driver Use Model (uni/bi/pipelined) | - | sequence-patterns > Driver-Sequence Use Models |
| Lock / Grab / Interrupt | - | sequence-patterns > Lock/Grab, Interrupt |
| UVM Coverage Subscriber | 워크플로우 #10 | coverage-guide > §1 Subscriber |
| Register Coverage (UVM_CVR_*) | - | coverage-guide > §5, ral-guide §11 |
| Analysis Path 기반 Coverage | - | coverage-guide > §4 |
| RAL 계층 구조 | 워크플로우 #7 | ral-guide §1, §2 |
| Register Adapter | - | ral-guide §4 |
| Built-in Register Sequences | - | ral-guide §7 |
| Register Scoreboarding | - | ral-guide §10 |
| Dual-Top Architecture | 워크플로우 #2 | testbench-architecture §1 |
| DUT Connection 패턴 (Signal/BFM/Abstract) | 워크플로우 #3 | testbench-architecture §2 |
| Russian Doll Config 패턴 | 워크플로우 #2 | testbench-architecture §6 |
| Factory Override | 워크플로우 #9 | testbench-architecture §7 |
| Predictor (분리된 예측) | UVM 계층 구조 | component-templates > Predictor |
| Scoreboard 3종 (In-Order Queue/FIFO, OOO) | - | component-templates > Scoreboard Patterns |
| Metric Analyzer | - | component-templates > Metric Analyzer |
| Sequence Persistence | - | sequence-patterns > Stimulus Generation Patterns |
| Sequence Polymorphism / Overriding | - | sequence-patterns > Stimulus Generation Patterns |
| get/put Alternative Pattern | - | sequence-patterns > get/put vs get_next_item/item_done 비교 |
| Interrupt Parallel Processing | - | sequence-patterns > Interrupt — Parallel Processing |
| Reactive Slave (Multi-SeqItem) | - | component-templates > Reactive Slave Agent |
| Wait-for-Signal Pattern | - | component-templates > Wait-for-Signal Pattern |
| Sequence Configuration (config_db from sequence) | - | sequence-patterns > Sequence Configuration |
| uvm_mem 상세 (burst/multi-map/test) | - | ral-guide §6 |
| Dynamic Address Map (unlock/unregister/lock) | - | ral-guide §3 |
| Command-Line Plusargs | - | debug-guide > Command-Line Plusargs 참조 |
| Package Organization (1class=1file, include규칙) | - | testbench-architecture §10 |
| Config 중첩 전파 (Russian Doll 확장) | 워크플로우 #2 | testbench-architecture §5.2 |
| Active→Passive 전환 (Vertical Reuse) | - | testbench-architecture §5.3 |
| Register Model 합성 (add_submap) | 워크플로우 #7 | testbench-architecture §5.4, ral-guide §2 |
| get_parent() 가드 (Block/Subsystem 공용) | - | testbench-architecture §5.5 |
| Bind + Prober (DUT 내부 관측) | - | testbench-architecture §5.6 |
| Sequencer 핸들 전파 (assign_sequencers) | - | testbench-architecture §5.7 |
| Interrupt Utility 공유 | - | testbench-architecture §5.8 |
| Report Catcher | - | debug-guide > Report Catcher |
| Verbosity 레벨 | - | debug-guide > 로그 레벨 |
| 일반 문제 해결 패턴 | - | debug-guide > 일반적인 문제 해결 |
| hdl_top config_db BFM 등록 (explicit import) | 워크플로우 #2 | testbench-architecture §1 > config_db BFM 등록 패턴 |
| `%m` String Formatter | - | testbench-architecture §1 > %m String Formatter |
| Dual-Top 시뮬레이션 실행 (vsim multi-top) | - | testbench-architecture §1 > Dual-Top 시뮬레이션 실행 |
| create() 네이밍 규칙 (name=handle) | - | testbench-architecture §6 > create() 네이밍 규칙 |
| VIF는 config object 경유 원칙 | 핵심 원칙 테이블 (Config object 단위 전달) | testbench-architecture §6 > Virtual Interface 전달 원칙 |
| Monitor Copy-on-Write 정책 | - | component-templates > Monitor > Copy-on-Write 정책 |
| 추가 Phase (end_of_elaboration 등) | 핵심 Phase 순서 > 추가 Phase | debug-guide > TLM 디버깅 (end_of_elaboration 코드) |
| Run-Time Sub-Phases | 핵심 Phase 순서 > Run-Time Sub-Phases | - |
| Config DB 우선순위 규칙 | - | testbench-architecture §6 > Config DB 우선순위 규칙 |
| External Coverage Monitor 권장 | - | coverage-guide §2 > External Monitor 권장 |
| Covergroup Factory Override (uvm_object wrapper) | - | coverage-guide §2 > External Monitor 권장 |
| Register Coverage 제어 API 흐름 | - | coverage-guide §5 > Register Block Coverage 제어 흐름 |

## Cross-Skill 참조

| 원칙 | 본 skill | 참조 skill |
|------|---------|-----------|
| RTL-TB 인터페이스 | 워크플로우 #3 | chip-verification > interface-mapping |
| Scoreboard/Ref Model | - | chip-verification > refmodel-patterns |
| SV Covergroup 문법, Bin/Cross | Cross-Skill 참조 | verilog-rtl > covergroup-patterns |
| Coverage 이론, Testplan, Closure | Cross-Skill 참조 | verilog-rtl > coverage-methodology |
| 실전 Coverage 예제 | Cross-Skill 참조 | verilog-rtl > coverage-examples |

## 변경 이력

- 2026-02-09 (12차): context 최적화 — coverage-guide.md SV 중복 제거, cross-skill coverage→verilog-rtl 재배치, stale "coverage skill" 참조 3건 수정 (SKILL.md, ral-guide, debug-guide)
- 2026-02-20 (13차): 6-Check 체계 전환 — "5-Check"→"6-Check" 표기 갱신, top-down/bottom-up 반영위치에서 testbench-architecture §6 제거 (명시적 미등장)
- 2026-02-09 (11차): VA Coverage 웹페이지 분석 — 신규 원칙 3개 추가 (External Coverage Monitor, Covergroup Factory Override, Register Coverage 제어 API)
- 2026-02-09 (10차): VA UVM Basics 11페이지 분석 — 신규 원칙 4개 추가 (Monitor Copy-on-Write, 추가 Phase, Run-Time Sub-Phases, Config DB 우선순위)
- 2026-02-09 (9차): VA UVM Testbench 웹페이지 분석 기반 보강 — 신규 원칙 5개 추가 (hdl_top config_db BFM 등록, %m Formatter, vsim multi-top, create() 네이밍, VIF config object 경유)
- 2026-02-09 (8차): Integration-Level Testbench §5 확장 — 신규 원칙 7개 추가 (Config 중첩 전파, Active→Passive 전환, Register Model 합성, get_parent() 가드, Bind+Prober, Sequencer 핸들 전파, Interrupt Utility 공유)
- 2026-02-09 (7차): UVM Cookbook PDF 2차 정밀 분석 — 신규 원칙 5개 추가 (Sequence Configuration, uvm_mem 상세, Dynamic Address Map, Command-Line Plusargs, Package Organization)
- 2026-02-09 (6차): Code Examples .tgz 분석 기반 보강 — 신규 원칙 6개 추가 (Persistence, Polymorphism/Overriding, get/put Alternative, Interrupt Parallel, Reactive Slave Multi-SeqItem, Wait-for-Signal)
- 2026-02-09 (5차): UVM Cookbook 기반 대폭 업데이트 — 신규 원칙 17개 추가, 신규 reference 2개(ral-guide, testbench-architecture), coverage skill cross-skill 참조 추가
- 2026-02-06 (4차): 5-Check 검증 완료 (5/5 PASS). 개선 권고: consistency-map "Phase 주의" → "핵심 Phase 순서 (주의 문구)"로 명확화
- 2026-02-06 (3차): [→§X] 참조 마커 시스템 도입, skill-validation-prompt.md 연동
- 2026-02-06 (2차): 필수규칙 vs 상세내용 모순 점검 — 절차적 가이드 구조로 해당 유형의 모순 없음 확인
- 2026-02-06 (1차): 전체 점검 완료 (SKILL.md ↔ 4개 reference 파일 일관성 확보)
