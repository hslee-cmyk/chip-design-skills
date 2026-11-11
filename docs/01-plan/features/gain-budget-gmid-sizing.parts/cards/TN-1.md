### N6.26 card TN-1 -- 절단 넷 규칙 구현 둘 → 하나(사용자 결정 O-83 R-N1, v6.35 둘째 커밋)

**근거**: 사용자 결정 O-83(2026-10-21 AskUserQuestion "R-M1·R-N1 넣고 승인 (권고)", `_drafts/user_decisions.md` O-83 행) R-N1(IT-2c card 파일 범위 = 순수 함수 분리·`_input_side` 대체·동작 동일성 test)·R-M1(래퍼 없음·둘째 이름 금지). v6.35 사용자 결정 O-115로 `icm_config` 호출이 없어져 IT-2c 범위에서 빠지지만, 목적(같은 규칙의 구현 둘 → 하나, graph 규칙 1)은 ICMR과 무관하게 남으므로 번호 있는 card로 둔다(검증 `wt/_drafts/evidence/2026-10-23/plan_v635_validation.md` S-3).

**사실**(integ/it12 `ee9bcf5b`, 착수 때 재측정): `E/authoring/_feedback_cuts.py:11` `input_terminal_nets(name, topology)`(호출 `E/authoring/spec_elements.py:104`·`E/authoring/spec_views.py:101`)와 `E/metrics/noise_plan.py:28` `_input_side(ss, element)`(호출 `:48`)가 같은 규칙(되먹임 수동소자의 두 단자 가운데 입력 포트 넷 쪽 = 절단 넷)을 따로 구현한다.

**범위**(v6.38.4 P9 재작성 -- N3.3 '같은 입력 → 필드 하나' 배정 B8; **원래 취지와 다름**: 사용자 결정 O-83 R-N1의 '순수 함수 분리·세 자리 직접 호출'을 대체, 승인 O-173 P9-TN): (1) 절단 넷 = S0 필드 하나(되먹임 소자마다 입력 포트 넷 쪽 단자 넷; writer = 되먹임 선언 S0 블록 하나, 규칙 정의는 그 블록 본문 한 자리 -- 이름은 design, 옛 design 이름 `feedback_cut_nets`) -- 세 자리의 입력(topology + spec `feedback`)이 같아 값이 같으므로(감사 B8, G1·G7) (2) 로더 검사(`spec_elements`)는 writer 블록 안 거부(첫 소비자 앞, N3.3 G1)로, 루프 뷰(`spec_views`)와 `noise_plan`은 그 필드를 READS한다(θ마다 다시 세지 않음) -- `input_terminal_nets`·`_input_side`는 래퍼로도 남기지 않는다(O-83 R-M1) (3) 함수 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`) 개념 행 하나, 같은 변경 (4) IT-2c 범위가 아니다.

**변경 종류**: 값 동일 리팩터링(O-34 (1) -- 절단 넷 값 비트 동일; 새 S0 필드 1·writer 블록 1 -- 필드 소유표 행 추가, v6.38.4 P9; SPICE 다리 '대상 없음' N6.3 (ii)).

**완료 조건**: (1) 동작 동일성 test -- 같은 입력에서 옛 두 함수와 새 writer 블록 필드의 절단 넷이 같음(0개·1개·2개 갈래; 기대값은 손으로 쓴 toy) (2) `git grep` -- 절단 넷 계산 자리 = writer 블록 하나(옛 '호출 자리 셋' 대체 -- v6.38.4 P9), 세 소비자는 필드 READS(N6.3 '같은 입력 재계산 0' 측정), `def input_terminal_nets`·`def _input_side` 정의 0 (3) **DC 망 정적 가드**(v6.35 둘째 커밋, 검증 N-8 -- 옛 IT-2 완료 조건 (10)(a) (i)을 옮김): 그 계산의 함수 객체 참조(load -- 호출·값으로 넘김·별칭, import 경로 무관, docstring·주석 제외)가 엔진 소스(`tests/` 제외) 가운데 writer 블록 한 자리에만 있고 `E/sizing` 전체와 봉인점 DC 망 조립 자리(`ss_nodal` 블록, `E/metrics/_helpers_nodal.py`)에는 0 -- AST 검사, red 변형 하나(그 자리에 참조를 넣으면 FAIL해야 함). 남기는 근거: v6.35 ICMR은 봉인점 회로를 선언 되먹임 소자 포함 그대로 재고(N3.8 'ICMR 측정 구성'), DEC-100 (2) 'DC는 저항이 작동'이 DC 망 조립에서 루프 절단을 쓰지 않음에 기대므로 비용이 작은 정적 가드는 남긴다; 동적 계수 (ii)와 양성 대조는 전제였던 S-3 정의 불능 규칙이 없어져 두지 않는다 (4) N6.3 공통(graph 정본 -- 같은 규칙 생산자 하나, 새 필드 = 절단 넷 1, cache 0).

**순서·착수 조건**: 선행 = IT-1 + IT-2 통합 병합(master 병합 뒤). 착수 조건 = 계획 v6.35 승인 → design(함수 레지스트리·CONTRACT 행) → design↔계획 gap → 착수 사실 재측정.

