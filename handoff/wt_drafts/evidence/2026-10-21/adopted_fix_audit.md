# 채택된 검증자 수정안 감사 (2026-10-21, 읽기만)

기준 산출물: master `e87092b3`(계획), oracle design `509d2227`(design/oracle-eo1), design 40/41/42 `82dda662`(design/it2c-o79 HEAD), 엔진 master `skills/analog-gmid-design/gmid_engine`.
약어: E = `skills/analog-gmid-design/gmid_engine`, O-design = `docs/02-design/features/oracle-portability.design.md`, 41 = `docs/02-design/features/gain-budget-gmid-sizing.41-gain-budget.design.md`, gb = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`.

판정: OK / modify / reject. '원칙 점검' 칸: G = graph 단일 정본(필드·writer·READS 선례·기존 helper), P = 물리 우선·가장 일반형, DA = DC/AC 분리, C = 상수·조건 발명 금지, W = 만들면 배선, S7 = 계획 먼저, M = 측정은 보호 대상 성질을 잰다, PR = 기존 선례.

## 1. 계산이 읽는 것·식별 방식을 바꾸는 항목 (우선)

| 항목 | 출처 보고 | 채택 자리 | 판정 | 원칙 점검 | 근거 | 권고 수정 |
|---|---|---|---|---|---|---|
| A1 MOS 식별 = `device.pins` gate 단자 유무 | design41_v1127 MF-1 | 41 v1.12.7 둘째 커밋 `8258af89` | **reject (이미 철회)** | G 위반: 정본 S1 필드 `device.element_class`가 있었음 | `E/graph/s1_structure.py:63`(`put("device","element_class",…,ELEMENT_MOS)`), O-88 | 셋째 커밋 `d73d8edf`가 `device.element_class == ELEMENT_MOS` READS로 고침. 추가 조치는 A2 |
| A2 계획 (10)(f) '`device.element_class` 불요' 문구가 O-88 뒤에도 남음 | (A1 정정의 부수 결과) | gb 1515 (10)(f) | **modify** | S7 위반: design 41:731 READS 일곱에 `device.element_class`가 있는데 계획은 '불요·`device.kind`로 충분'이라고 적음. 계획과 design이 다름 | gb 1515 '이상원 구별은 `device.kind`로 충분 … `device.element_class` 불요'; 41:731 READS 목록; O-88(design만 고침) | 계획 v6.28 정오 한 구절: '`device.element_class` = MOS 식별 정본 READS(O-88), 이상 전류원 구별은 `device.kind`'. design 승인 전에 계획부터 반영(S-7) |
| A3 `_dc_feedback_reaches` 엣지 = `device.dc_nets` | design41_v1126 §2.2(판정 근거), n7 C1·C2 | 41:734 (가)(나) | **OK** | G: `device.dc_nets` = S1 writer `s1_structure`가 `dc_edges_unpruned`(엔진 유일 DC 엣지 정의)로 채운 필드. 재사용 후보 점검: `graph.dc_segments`(`dc_conduction`)는 레일·포트 아닌 '저항 하나뿐' 넷을 가지치기함 → MOS gate만 더 붙은 내부 넷(gate는 DC 엣지 아님)이 지워져 g→d 방향 경로를 잃음 = 쓰면 틀림. `signal_reach`는 커패시터 포함(AC, DA 위반). `stage_bfs`는 AC 셀 비용. `composite_diode._walk`는 직렬 사슬 전용. 재사용 가능한 DC 도달 helper 없음 | `E/authoring/dc_edges.py:1-21`, `E/graph/s1_structure.py:80-82`, `E/graph/dc_conduction.py:1-20`(2단계 잎 가지치기), `E/graph/signal_reach.py:1-12`, 레지스트리 §13 | 없음. 41:734 (나)에 'unpruned `dc_nets`를 쓰는 이유 = `dc_segments` 가지치기는 gate 엣지가 붙은 잎을 지움' 한 구절을 넣으면 뒤 card가 다시 묻지 않음(선택) |
| A4 이상 전류원 제외 = 인라인 술어 `element_class == ELEMENT_SOURCE and kind == CURRENT_SOURCE` (넷째 사본) | 오케스트레이터 추가 질의(82dda662) | 41:734 (나), IT-2c spec | **OK (IT-2c에서 helper 만들지 않음)** + 백로그 1건 | 아래 §3 상세. G 규칙 1 위반 아님(계산값·필드 아님). 규칙 3 취지: 네 자리가 같은 상수 두 개를 import해 쓰므로 정의가 갈릴 수 없음. 진짜 중복은 어휘 리터럴 `"current_source"`가 세 자리(`graph/s1_values.py:29`, `sizing/s2_values.py:22`, `authoring/spec_elements.py:41`)에 있는 것 -- 기존 부채. C: 계획 (10)(f)가 '지원 이상원 kind = `current_source` 하나, `device.kind`로 구별'을 정했으므로 발명 아님 | `E/metrics/ss_circuit.py:19·57`, `E/sizing/current_basis.py:90`, `E/sizing/kernel_context.py:80`, `E/sizing/s2_values.py:20-22`('graph가 공개하지 않는 지원 kind를 여기서 이름 붙인다'), gb 1515 | IT-2c: 지금 문언 유지(파일 범위 변경 없음, 계획 변경 불필요). 백로그: '이상원 kind 어휘 정본을 graph로' -- `CURRENT_SOURCE`를 `graph/s1_values.py`에 정의하고 `SUPPORTED_SOURCE_KINDS = (CURRENT_SOURCE,)`, graph `__all__` export, `sizing/s2_values.py`는 graph에서 import해 재export(기존 import 108곳 test 무변경) |
| A5 지원 밖 판정 = S1 `device.unsupported` READS | design41_v1126 R2, plan_o81 M2 | gb (10)(f)·N3.8, 41:734 (다), 코드 `icm_config_feedback_element_unsupported` | **OK** (관찰 1) | G: S1 writer `s1_structure`(`s1_structure.py:69·79`)의 필드를 READS로 읽어 kind 목록 둘째 계산을 지움 -- 맞음. W 관찰: 엔진 운영 경로에서는 `s1_dc_conduction`이 같은 원소로 먼저 멈춰(`graph/CONTRACT.md:394`, `dc_conduction.py:9-11`) 이 갈래에 닿지 않음 -- 합성 스냅샷 test만 부름. 판정 함수의 정의역을 닫는 갈래라 계획이 정한 것(O-85 (3)) | `E/graph/s1_structure.py:69·79`, 41:734 (다) | 그대로. 사용자 보고 한 줄: '운영 경로 도달 0, 정의 완결용 갈래'(W 원칙 예외임을 명시) |
| A6 절단 넷 순수 함수 `feedback_cut_nets(terminals, input_nets)` 위치·호출부 | plan_o81 M1·R-M1, design41_v1126 MF-A | gb N3.8·(10)(f), 41:734 '절단 넷 순수 함수', IT-2c card | **OK** | G: 구현 둘(`input_terminal_nets`·`noise_plan._input_side`)을 하나로, 래퍼 없음. 층: `authoring`(2) → `metrics`(5) import 허용(구조 규칙 C(2)), 공개 export 경유(C(3)). `_feedback_cuts.py` 비공개 모듈 규칙 A(3): authoring 안 importer 둘(`spec_elements`·`spec_views`) ≥ 2 충족. icm_config 입력 넷 = `node.port_direction == "input"`(S1 READS)이라 topology 밖 입력 없음 | `E/authoring/_feedback_cuts.py:11-16`, `spec_elements.py:104`, `spec_views.py:101`, `noise_plan.py:28·48`, `tests/structure/README.md:39·41` | 없음 |
| A7 끝점 helper 호출 꼴(원 계획 '`input_terminal_nets` 호출') | plan_o81 M1 | gb N3.8 정정 | **OK** | 원래 문구(n7 실측 C1을 그대로 옮김)는 icm_config에 topology 객체가 없어 구현 불능이었음 -- 검증자 지적이 실재. 채택안은 S1 READS만 씀(G 규칙 2·4) | plan_o81 §5, `ss_evaluate.py` topology 참조 0 | 없음 |
| A8 경유 금지 집합의 '교류 접지' → DC 이름(레일·바이어스 고정 넷), `node.ac_ground_class` READS 제거 | plan_o81 N3 | gb N3.8, (10)(f) READS | **OK** | DA: DC 판정에 AC 분류 필드를 읽지 않게 함 -- 원칙과 일치. gate 전용 넷은 들어오는 엣지가 없어 결과 불변 | plan_o81 재검증 N3 행 | 없음 |
| A9 서명에 출력 넷 인자 `_dc_feedback_reaches(view, output, cut_nets)` | design41_v1127 MF-2 | 41:731·734 (마) | **OK** | 결함 실재(두 출력 동시 출발이면 갈림을 원리적으로 못 잡음). 새 필드·cache 0, 출력마다 O(N) | 41:734 (마) | 없음 |
| A10 `MOS_GATE` 대신 공개 `MOS_TERMINAL_NAMES`(R-a, O-88로 축소) | design41_v1127 §14 R-a | 41:734 (나) | **OK** | 구조 규칙 C(3): `MOS_GATE`는 graph `__all__` 밖. 선례 `metrics/dc_metrics.py:28` | `E/graph/__init__.py:95·271` | 없음 |
| A11 오라클 `swing_math.dc_feedback_judgment` 새 함수 | oracle v039·v0310 graph 점검(채택 확인) | O-design §21.2 (0)(1868), §20 OP-5 | **OK** | G: 오라클 안 기존 그래프·도달 helper 없음(`tools/spice_oracle/*.py` grep: `loop_break_nets`만). 끝점은 기존 `oracle_netlist.py:234-253` `loop_break_nets`를 읽음(둘째 절단 규칙 없음). 엔진과 따로 구현은 NFR-P3 요구 | O-design 1868, `oracle_netlist.py:234` | 없음 |
| A12 `bias_not_gate_only` 새 사유 | oracle v039 N2 → v0310 N2 | O-design 481(범주 표시)·1868·1646 | **OK** (관찰 2) | 검사 자리가 지금 없음을 실측(스키마 100-104, 넷리스트 466-480, topology 대조 1233-1245) -- 둘째 검사 아님. 판정 전제 위반이라 '입력 계약' 범주 표시·OP-3 이관 때 같은 변경에서 삭제 명시 -- G 규칙 1 취지 충족. 관찰: `oracle_netlist.py:466-480`이 구동되는 넷의 bias 선언을 '조용히 건너뜀'은 skip 원칙 위반 후보(범위 밖) | O-design 481·1868, `O/oracle_netlist.py:466-480` | 백로그 한 줄: 조용한 건너뜀을 OP-3 입력 계약 거부로(이미 1655 백로그와 같은 card) |
| A13 `closure_common_asymmetric` | oracle v036 필수 3 → v037 | O-design 479, F-8 1757 | **OK (사용자 승인 O-78 (3))** (관찰 3) | G 규칙 3: ½(V_a+V_b) 고정과 c 가중 m이 갈리는 결함 실재. P 관찰: 가장 일반형은 Vcvs 이득·cm0를 c에서 유도하는 것(검증자 둘째 안)이고 fail-closed는 제한. 해당 회로 수 미확인(EO-1 생산자 전). 엔진 짝 없음(1650 '미확인') | O-design 479·1650·1757 | 그대로. EO-1 생산자 뒤 비대칭 c 회로 수를 재고, 1개 이상이면 c 유도 일반형으로(계획부터) |
| A14 `icmr_v` 정의 = 포트 창 교집합 폭(엔진 정의 인용) + lo/hi = 두 끝 기록의 min/max | oracle v036 필수 2, v037 N1·N4·N7 | O-design §21.2, §11.7 | **OK** | G 규칙 3: 같은 이름에 정의 둘을 엔진 정의 하나로 모음. min/max는 c < 0 반전을 막는 일반형(C 발명 아님) | oracle v038 §1 N1 행(엔진 41:780·784·811 일치 확인) | 없음 |
| A15 (d-1)/(d-2) 부호 test: 구조 단언 sign(T)·sign(닫힘) < 0, 루프 부호 = `.tf` 네 값의 A_d | oracle v036 필수 4, v037 N3 | O-design §18.1 (d), F-1 | **OK** | M: DC `.op`는 평형 안정성을 못 가려 옛 'red' 주장이 공허했음 -- 보호 대상(루프 부호)을 직접 잼. 새 측정 없음(이미 재는 `.tf` 값 재사용, G) | oracle v038 §1 N3 행(A_d 식 재유도) | 없음 |
| A16 (10)(a) 측정 = 의미 기준(정적 load 참조·동적 `__code__`·양성 대조·(e) 손계산) | design41_v1126 S-FB1, plan_o85 M1·N1·N4 | gb (10)(a)(v6.28), 41:812 L10 (a), card C-1 | **OK** | M: 옛 측정이 이름을 쟀고(IT-0 정적 0은 `_input_side` 이름 차이로 통과) 동적 래퍼가 공허했을 가능성 -- 새 측정은 함수 객체·code object로 세고 양성 대조로 '실제로 거부함'을 보임(사용자 규칙 '게이트는 거부부터 확인'과 일치). 다른 모듈로 옮기는 게이밍 기각 | plan_o85 §2, 41 v1.12.7 §3 표 | 없음 |
| A17 `[]` → `measure_feedback.kind = unity_follower` | oracle v036 필수 6, plan_o78 N6 | O-design §11.6, F-9 1758 | **OK** | G·PR: 엔진 정의 `E/authoring/spec_elements.py:19-20`('빈 list = β=1 루프') 인용만, 새 정의 없음. 엔진 `()` → `follower_beta1`과 같은 뜻 | O-design 1772 | 없음 |
| A18 C10 `.ic` 소유 = OP-4 | oracle v036 nice-1 → v038 M1 | O-design §4.2·§5·§8.3·§20 | **OK** | W: 칸·능력을 만드는 card와 쓰는 card를 같게 해 card 사이 소비자 없는 칸을 없앰. 계획 OP-4 행과 일치(S7) | oracle v039 §1 M1 행 | 없음 |
| A19 `detail.also = ["start_op_deferred"]` | oracle v038 N4(검증자 '선택 사항') | O-design §7 `feedback_config_undeclared`, graph 표 1785 | **modify (경미)** | W: 값 사본은 아니지만, 읽는 자리가 '거부 기록·검증자'로만 적혀 있고 그것을 읽는 test·대응표 행이 없음 -- 소비자 없는 칸 후보 | O-design 1785 | 둘 중 하나: (가) §18.1 test 한 행 또는 사유 대응표에 `also`를 읽는 자리를 적는다, (나) 소비자가 없으면 지운다(검증자도 선택 사항이라 함) |
| A20 사유·code 이름(`icm_config_feedback_no_dc`·`…_element_unsupported`·`…_outputs_split` 예약, 오라클 `icmr_feedback_dc_absent`·`dc_feedback_judgment_undefined`·`input_network_step_deferred`) | oracle v038 §3·N2, design41_v1126 R1, v1127 | 41:734·744, O-design §7·§19.2 대응표 | **OK** (관찰 4) | 사유 어휘는 graph 필드가 아님(규칙 3 대상 아님), 계획이 이름을 design에 맡김. 대응표 한 곳(O-design 1642-1650) | O-design 1643·1645 | `outputs_split` '예약'은 S-OS2 card design에서 확정(이름만 먼저 둔 것이 W에 어긋나지 않게 코드에는 넣지 않음 -- 지금 그렇게 적혀 있음) |

## 2. 그 밖의 채택 수정 (문언·범위·절차)

| 항목 | 출처 보고 | 채택 자리 | 판정 | 원칙 점검 | 근거 | 권고 수정 |
|---|---|---|---|---|---|---|
| B1 단일 출력 + 용량만 선언 = 정의 불능(정의 자리 gb N3.8 하나) | plan_o78 M1 | gb N3.8, oracle N3.9 인용 | OK | G 규칙 3(같은 `icmr_v`에 엔진 '개루프'·오라클 '정의 불능' 둘) 해소, O-52 '개루프 별도 정의 기각'과 일치 | plan_o78 §5-1·5-2 | 없음 |
| B2 R2 단일 입력이 먼저(`as_is_single_input`) | plan_o78 재검증 R2 | O-80 R2, 41:734 | OK | 기존 갈래 순서 정렬, 동작 변화 0 | O-80 | 없음 |
| B3 (10)(e) 용량 toy 기대 = 정의 불능, 손계산은 저항·혼합 toy | design41_v1125 MF-1 | O-81 (1), 41:812 | OK | S7: 계획부터 고침 | O-81 (1) | 없음 |
| B4 경로 기준 일반화(kind 판정 → DUT DC 망 방향 그래프) | design41_v1125 N7 | O-81 (2)·O-82, gb N3.8 | OK | P: 반례 Cf+Rb에서 kind 판정이 틀림 -- 물리 일반형 | n7_path_rule_feasibility | 없음 |
| B5 슬루율 측정 정의 정렬(587) | plan_o81 M3 | gb N3.8 587 | OK | G 규칙 3(정의 자리 하나) | plan_o81 재검증 M3 | 없음 |
| B6 슬루 1b 닫힘 `.op` → ICMR 공칭 점 기록 `v_in` 참조 | oracle v036 필수 1 | O-design §21.6 1b | OK | G 규칙 1·4(둘째 생산자 제거, 기록 참조) | oracle v036 필수 1 | 없음 |
| B7 1b 입력 망 계단 미룸·사유 `input_network_step_deferred` | oracle v036 필수 7, v038 M2 | O-87 (2) X-R6 | OK | W: 쓰는 회로 0인 경로를 만들지 않음, 원래 취지와 다름 보고·사용자 승인 | O-87 (2) | 없음 |
| B8 MF-A 2 갈래 공개 경로 test(`noise_feedback_cut_ambiguous`, base 먼저 green) | design41_v1126 MF-A | IT-2c card T-L10 (i) | OK | 동작 동일성 증거를 사본 없이(옛 함수 사본 금지) | design41_v1126 §3 | 없음 |
| B9 U-1 IT-2c 범위 확대(차동 결합) | design41_v1127 U-1 | 철회(O-87 (1)) | OK(철회됨) | W: 쓰는 곳 0 갈래를 만들지 않음 | O-87 (1) | 없음 |
| B10 DV-21 차동 결합 규칙 | oracle v039 §4·M2 | O-85 (1)·O-86 N3 | OK | 계획 정의 한 자리, 오라클 인용 | O-85 (1) | 없음 |
| B11 IT-1 dispute 3건(K-3 확장·기준 약화 0) | it1_dispute_analysis | O-84 | OK | 작성자≠검증자, 단언 6개 유지 | O-84 | 없음 |
| B12 문언 정리(M1-a~c, N1·N4 'DC 전도 원소', 경위 → history, DR-22 축약 등) | oracle v039 M1·N4, v0310 N1·N5·N6, plan_o78 N4·N5, plan_o81 N7 | 각 문서 | OK | 계획=design·이력=history 원칙 | 각 재검증 표 | 없음 |

## 3. A4 상세 -- 이상 전류원 술어 넷째 사본 (오케스트레이터 질의)

**Q1. 넷째 인라인 사본이 규칙 1 또는 규칙 3 취지의 '규칙 사본' 문제인가?**
- 규칙 1(계산값은 graph 필드, writer 하나): 해당 없음. 술어는 S1 필드 두 개(`device.element_class`·`device.kind`, writer `s1_structure`)를 상수와 비교할 뿐이고 새 값을 만들지 않는다.
- 규칙 3 취지: 절단 넷 함수와 다르다. 절단 넷은 서로 다른 두 구현(`a != b` 검사, 0/1/2 계약)이 있어 갈릴 수 있었다. 이 술어의 네 자리는 같은 상수 두 개(`ELEMENT_SOURCE` from graph, `CURRENT_SOURCE` from sizing)를 import해 같은 꼴로 쓴다. 상수를 바꾸면 네 자리가 함께 바뀌므로 정의가 갈릴 수 없다.
- 용도도 둘로 나뉜다. `ss_circuit.py:57`과 `_dc_feedback_reaches`는 '이상 전류원은 증분 컨덕턴스 0이라 엣지가 아님'이라는 물리 규칙이다. `current_basis.py:90`·`kernel_context.py:80`은 '전류값을 줄 원소를 고름'이라는 선택이다. helper 하나로 묶어도 물리 규칙 문장은 두 자리에 남는다.
- 실제 중복은 어휘 리터럴이다. `"current_source"`가 `graph/s1_values.py:29`(`SUPPORTED_SOURCE_KINDS`)·`sizing/s2_values.py:22`(`CURRENT_SOURCE`)·`authoring/spec_elements.py:41`(dict 키) 세 자리에 있다. 기존 부채이며 `s2_values.py:20` 주석이 이유('graph가 공개하지 않는 지원 kind')를 적고 있다.
- 결론: 규칙 위반 아님. 다만 계획 (10)(f)가 '이상원 구별은 `device.kind`로 충분'이라 했으므로 `kind == CURRENT_SOURCE` 하나로 줄일 수 있다(`"current_source"`는 element_class 사이에서 유일). design은 `ss_circuit` 선례 꼴을 따랐으므로 둘 다 받아들일 수 있다.

**Q2. IT-2c가 helper를 만들고 기존 세 자리를 같은 변경에서 바꾸고 레지스트리 행을 더해야 하나?** -- **아니다(권고).**
- 이유 1: 규칙 위반이 아니다(Q1). 이득은 표기 통일뿐이고 동작 변화는 0이다.
- 이유 2: `sizing/current_basis.py`·`sizing/kernel_context.py`는 커널 경로다. 이 파일들을 IT-2c 파일 범위에 넣으면 IT-2c 감사가 sizing 커널(V1~V10)까지 넓어진다. IT-2c 목적(ICMR 측정 구성)과 무관한 인프라 변경이다(메모리 '인프라 작업은 gmid 엔진을 막을 때만').
- 그래도 하겠다면 다음 실현성 평가를 따른다.
  - 호출 자리: 4곳 -- 기존 3곳(`metrics/ss_circuit.py:57`, `sizing/current_basis.py:90`, `sizing/kernel_context.py:80`)과 새 `icm_config` 1곳.
  - import: sizing(층 4)과 metrics(층 5)가 모두 graph(층 3)를 import할 수 있다(구조 규칙 C(2)). `ss_circuit.py:19`의 `from gmid_engine.sizing import CURRENT_SOURCE`는 쓰는 곳이 사라지면 지운다. `sizing/__init__.py:26·166` 재export는 test가 쓰므로 남긴다.
  - test 영향: `CURRENT_SOURCE`·`"current_source"`를 쓰는 test 줄이 108개다. 상수 export를 유지하면 바뀌지 않는다. 구조 test A·C가 새 파일을 검사한다. 동작 test는 변화 0이어야 한다(동일성 증거 = base·head 둘 다 green).
  - 계획 변경: **필요하다.** IT-2c (iii) 파일 범위(gb N6.6)와 card 파일 목록에 sizing·graph 파일이 늘어나므로, design보다 계획을 먼저 고친다(S-7). 레지스트리 §13에 행 하나를 같은 변경에서 더한다.

**Q3. helper를 둘 자리** -- graph가 맞다(층 3, `ELEMENT_SOURCE`·`SUPPORTED_SOURCE_KINDS`가 있는 어휘 정본 자리).
- `graph/s1_values.py`에 함수를 더하면 안 된다. 이 파일에는 공개 dataclass 다섯(`S1Key`·`SymmetryMarks`·`Orbits`·`CurrentSigns`·`BulkResult`, 231-277행)이 있다. 공개 함수가 하나라도 생기면 규칙 A 보충 (1)(데이터 선언 모듈)에서 빠져 일반 판정으로 가고, 진입점이 여럿이 될 수 있다.
- 새 파일(예: `graph/source_kind.py`, 진입점 하나)과 `graph/__init__.py` `__all__` export, 그리고 graph CONTRACT 한 줄이 필요하다.
- 더 작은 대안(권고 백로그): helper를 만들지 않는다. `CURRENT_SOURCE` 상수만 graph로 옮기고 `SUPPORTED_SOURCE_KINDS = (CURRENT_SOURCE,)`로 둔다. sizing은 graph에서 import해 재export한다. 이렇게 하면 어휘 리터럴 중복(실제 중복)이 사라지고 호출부 4곳은 그대로 둔다.

## 4. 미확인
- A4 대안 실행 시 구조 test A·C 결과(돌리지 않음).
- A13 비대칭 `dc_sweep.common` 회로 수(EO-1 생산자 전).
- A5 합성 스냅샷 test가 `device.unsupported` 열을 가진 채 `icm_config` 블록 READS 투영을 통과하는지(실행 안 함).
- A19 `detail.also`를 읽는 검증자 원인 변화표의 실제 소비 여부(오라클 코드 미작성).
- history 파일, design 40·42 본문은 이번에 다시 읽지 않았다(검증 보고 인용).
