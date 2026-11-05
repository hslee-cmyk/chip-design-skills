---
id: 20261104-it1-input-point
phase: 해당 없음 (DEC-86 -- merge_gate 미사용, N6.3 절차)
evidence_type: red-green
gate_change: no
---
## 의도

card IT-1 범위 재작성. 입력 DC 미선언 회로에서 선언된 차동 입력쌍의 두 포트가 DC 변수 하나를 공유하게 한다(DEC-106, O-168). g = s 소자의 정지와 비대칭을 지운다(O-210 RR-6, N3.6 정본 (11)). `net_model` 둘째 호출을 지운다(N3.3 B4, 승인 O-173 P9-M1a).

물리 결정자 = 측정 구성. 한 차동쌍은 같은 원이 같은 공통모드로 구동하고, 두 포트의 DC 차는 설계 자유도가 아니라 계통 offset이라는 계산 결과다(DEC-23). 원칙 1·3·4·5·7·8·10·11·12를 전 범위에 적용한다: 이름이 아니라 role로 판별, 상수 0, fail-closed 정지, 값 사본 0.

결정 덮개: O-168·O-170(DEC-106), O-210 RR-6, O-173 P9-M1a, O-225·O-226(측정 유보·위임). design 41 v1.16.3 + A-27.

**표지**: as-built는 재작성 범위로만 인용한다(원칙 8). 이 card는 옛 IT-1 PASS 코드 위에서 범위 2~4를 다시 쓴다.

## 관찰 가능한 계약

interface card `20261104-it1-input-point.interface.md` 전체. 커밋 셋으로 나눈다(변화표 원인 분리, N6.5 완료 3·7):

| 커밋 | 범위 | 원인 칸 | 변경 종류 |
|---|---|---|---|
| ① | N6.5 범위 1~4(입력 점, `input_cm_undefined`, 옛 정지 삭제, `block_columns` 읽는 키, 문언) | DEC-106 | 동작 변경 |
| ② | 범위 5(g = s) | N6.35 E-19 | 동작 변경(library 발동 0 -- 사전 실측, 값은 유보) |
| ③ | 범위 6(B4) | P9 B4 | 순수 리팩터링 |

## 재작성 범위(엔진 인용 = 지울·바꿀 자리, integ/it12 `b9351eac`)

| 자리 | 일 |
|---|---|
| `E/sizing/writer_plan.py:176`(`free_inputs`)·`:243` 부근 뿌리 후보·`:254-258` 정지 | 입력 점 묶음으로 재작성, 옛 정지 삭제 |
| `E/sizing/writer_plan.py` READS | `node.port_role`·`graph.gvgs_summary` 추가 |
| `E/sizing/s2_values.py:94`, `E/sizing/__init__.py:23, :160`, `E/sizing/CONTRACT.md:327`, `writer_plan.py:29, :39` | 상수·export·문언 교체 |
| `E/sizing/block_columns.py` `input_roots`·`_solve_input_window`·writer 식·`_windows`의 뿌리 아닌 포트 거르기 | 읽는 키만 입력 점 y로. `_windows` 거르기에 `input_point` 포함(입력 점 두 항목 중 p는 뿌리 갈래, n은 항목 없음). 그 밖 비뿌리·F 성분 갈래는 IT-2c가 지운다. 루프·예외 추가 0, 덧대기가 필요해지면 멈춤 |
| `E/sizing/scc_order.py`·`E/metrics/achievability.py`·`path_values` 자리 | `input_point` relation 소비(grep으로 전수) |
| `E/graph/gvgs_cycles.py:68-79`, `E/graph/s1_values.py:125`, `E/graph/CONTRACT.md:256, :399, :556` | 정지·상수·문언 삭제, 칸 추가 |
| `E/graph/coupling_vars.py:179`, `E/graph/net_model.py`, `E/graph/s1v_fields.py:253`, `E/graph/s1_values.py:213` | B4 필드화 |
| `E/sizing/input_window.py`·`E/_module_map.py`·sizing CONTRACT 3절 | 문언 |
| `assets/library/{current_reuse_telescopic_ota,nmcnr_amplifier}.structure.json` `rule_hash` | 커밋 ③에서 줄만 재기록(`net_model.py`·`s1v_fields.py`가 rule 파일, A-33·A-34). 커밋 ①②는 rule 파일을 고치지 않는다. 사실·connectivity 변경 0 |

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `gmid_engine.sizing.s2_values` | `REL_INPUT_POINT` | `REL_INPUT_POINT = "input_point"` |
| `gmid_engine.sizing.s2_values` | `BRANCH_INPUT_CM_UNDEFINED` | `BRANCH_INPUT_CM_UNDEFINED = "input_cm_undefined"` |

## graph 단일 정본

(원칙 7, `fpga/CLAUDE.md` '★graph 단일 정본', 계획 N3.3 G0~G7·N6.3 '같은 입력 재계산 0')

* 새 필드 넷(`graph.diode_nodes` 외) = writer `s1v_fields` 하나, 권한표 `S1V_WRITES` 행 하나. 새 블록 0.
* 칸 `GvgsSummary.gate_source_same` writer = `s1_gvgs` 하나. 쓰기 계획은 READS(g = s 재판정 0).
* v_cm 값 사본 0. 값은 y 성분 하나 또는 노드 풀이가 쓰는 KVL 종속 값.
* 새 cache·memo·dict·context 슬롯·결과 값 칸·사본 0.
* B4 해소, 새 B 0(측정 도구 = card GL-1).
* 정본 자리가 없으면 만들지 않고 멈추고 보고한다.

## 소비자

| 새·바뀐 필드·def | 엔진 소비자 |
|---|---|
| `relation == input_point`, y 키 | `E/sizing/block_columns.py`(노드 풀이), `E/sizing/theta_schema.py:142`, `E/search/fd_jacobian.py:57` |
| `BRANCH_INPUT_CM_UNDEFINED` | `dc_writer_plan` 정지 |
| `GvgsSummary.gate_source_same` | `dc_writer_plan` |
| `graph.diode_nodes` 외 셋 | `coupling_vars` |

신호 경로 술어 필드는 만들지 않는다(LA-1 범위 15 (c), 표 #19). 바이어스 고정 넷 필드도 만들지 않는다.

## 판정 유형 근거

동작 변경(O-34). 기준 = 원칙 2: E-0·정의 동일성. SPICE와 수치가 같은가는 기준이 아니다. e_m 칸 없음. SPICE 다리·13회로 변화표는 보류 다리(A-5·A-10, 채울 card = EO-1·OP-5·CL-1), 통과로 세지 않는다.

## oracle 종류와 출처

(a) 구성으로 정답이 정해진 toy: 묶은 G_vgs 순환수·relation을 연결에서 손으로 유도. 물리 불변식이라 피검 구현과 가장 멀다. 대칭 toy는 DOF·rank 손계산. 범위 6은 (c) 기존 기준 비트 동일.

## 거부해야 할 입력

| 입력 | 기대 |
|---|---|
| 입력 DC 미선언 + 차동쌍 둘 | `input_cm_undefined` 정지 |
| 입력 DC 미선언 + 차동쌍 없는 입력 둘 | 같음 |
| 입력 DC 미선언 + 차동쌍 + 단일 입력 | 같음 |

## library 회로 적용 여부

대상 = 입력 DC 미선언 차동 입력쌍 회로, 무동작 = 선언 회로·단일 입력. 13회로 n/N과 IT-0b는 **유보(O-225, A-7)**: 판정 기록에 base sha와 '미완료(보류 다리: 변화표·IT-0b, LA-1 측정 시점)'. held-out 0개라 A' 일반성 판정 정지(O-181).

## 무동작 판정 입력(무발동 값)

입력 DC 선언 toy·단일 입력 toy: `node.dc_writer`·`device.dc_coord`·`graph.dc_tie_breaks` 필드별 동일. g = s 없는 toy: `gate_source_same == ()`. B4: `graph.vars`·`graph.column_block_map`·`graph.bias_columns` 비트 동일.

## 재현할 수치

없음(toy 손계산은 수치가 아니라 구조 값). 회로 값 유보.

## 결정 필요 항목

| 항목 | 물리 결정자 | 식·원문 | 실측 | 판정 |
|---|---|---|---|---|
| D-1 base 실패 처리 | 해당 없음(절차) | N6.5 완료 6 '0 failed', 커밋 `d7800c03` 메시지 'O-181 영향 23건', A-31 `fix/o181-tests` | 미측정, `fix/o181-tests`는 master 미병합(2026-11-04 `git merge-base --is-ancestor`) | 기준 = 전체 0 failed. base에 실패가 남으면 그 목록을 오케스트레이터에 올리고 판정을 멈춘다 |
| J2 F 닿는 입력 점 둘째 포트 표기 | KVL(같은 전압) | 40 §3.11-4 'KVL 종속' -- relation 미정 | 단언 금지로 test 분리 | 맞음. 기본안 = p 포트 KVL relation, n 포트 `input_point`·`known = p`. 작성자 판단 |
| J3 칸 이름 `gate_source_same` | g = s KVL | 40 §3.11-5 '칸 이름은 재동결 때' | grep 충돌 0 | 맞음 |
| J6 `rule_hash` 재기록 | 해당 없음 | N6.6 완료 (14)는 IT-2c만 적음 | `S1V_RULE_FILES`에 `net_model.py`·`s1v_fields.py` 포함(scope_grep.txt) | 결정됨(A-33·A-34): 커밋 ③ 안에서 줄만 재기록, T-RH, 감사가 diff·값 비교 근거. TB-1·EO-1은 이 재기록 뒤 base에서 잰다 |

## 원래 취지와 다름

* card 성격 확장: 범위 6(S1v 소비자 정리) -- 계획 표지(승인 O-173 P9-M1a).
* O-168 '입력 포트들을'을 한 차동쌍으로 좁힘 -- 계획 표지(승인 O-170).
* K-3 '대칭 포트는 묶음이 대신' 대체 -- 승인 O-168.
* 계획 N6.5 완료 5 '새 필드 = 바이어스 고정 넷'은 범위 5·표 #19·40 §3.11-5와 맞지 않아 이 card는 만들지 않는다. 계획 문언 잔재(정정 요청, 동작 판단 아님).
* SPICE 다리·변화표·IT-0b 보류 -- 위임 A-5·A-7.
* `rule_hash` 재기록을 IT-1로 앞당김, 계획 표지 '재비준은 사용자 승인'을 위임으로(A-33·A-34).

## 절차

(계획 DEC-86이 남긴 넷 그대로, 정본 = 계획 N6.3)

1. 코드 작성 주체와 test·기대값 작성 주체 분리(WP-13).
2. 깨진 test·기준 약화는 숨기지 않고 보고.
3. 변경당 커밋 1(이 card는 위 ①②③).
4. 매 변경 뒤 새 test 체계(`gmid_engine/tests/`) 전체 실행.

* **판정 기록**: 독립 검증자가 `.ai/verification/20261104-it1-input-point.json`을 남긴다(`_schema.json` 필수 칸: id, spec_card, evidence_type, base_commit, test_commit, code_commit, checks V1~V10, reproduced_numbers, approvals, auditor_run; 선택 red). 보류 표지는 해당 V 칸 `basis`에 '미완료(보류 다리: 13회로 변화표·IT-0b·SPICE, 채울 card = EO-1·OP-5·CL-1, base = <sha>)'로 적고 통과로 세지 않는다(A-10). `approvals`는 빈 배열(O-226은 형식 id가 아님), 근거는 basis에 적는다.
* **test 이의**: 코드 주체는 `docs/02-design/disputes/20261104-it1-input-point.md`에 쓰고 멈춘다.

## 작성 전 실측

(2026-11-04, 측정 = `scope_grep.txt`, 스크립트 = `measure_it_scope.sh`, `git grep` on integ/it12 `b9351eac`·master `7620f5ee`)

1. 사실 재측정: 위 표 줄 번호 = `writer_plan.py`·`gvgs_cycles.py`·`s2_values.py` 직접 읽기와 `scope_grep.txt`. 계획 줄 인용(d759838a)은 옮기지 않고 다시 쟀다.
2. 엔진 인용 용도: 재작성 범위·소비자 목록뿐.
3. 이름 충돌: `input_point`·`REL_INPUT_POINT`·`input_cm_undefined`·`BRANCH_INPUT_CM_UNDEFINED`·`gate_source_same`·`test_it1_` 0 파일. `diode_nodes` 외 셋은 `NetModel` 속성으로 이미 있고 같은 뜻이라 충돌 아님. test glob은 `structure_checks.py:131, :979, :1248`·`test_block_columns.py:1600`(rglob)뿐, 새 모듈 파일 없음.
4. 원칙 계약화: 'role로 판별·이름 판별 0'을 T-1g로, fail-closed를 T-1e로.
5. 쓰기 경로: 코드 ≠ test ≠ 판정.
6. 계획서 소비자: `input_port_multiple_roots` 계획 6·40 4·41 4·42 2, `gvgs_self_edge` 계획 3·graph-consumption 8·40 1·41 1·42 1(history 제외). 모두 '옛 문언·삭제' 표지 문맥으로 card 범위 밖, 잔재 정리는 병합 때 history로(N6.5 표지).
7. 미배선: 위 소비자 표 전부 운영 경로.
8. 기존 test: interface '고칠 기존 test'. 기준 약화 없음 예상, 나오면 보고.
9. 승인 줄: 의도 절. approval 머리 줄 없음.
10. 범위 계약: diff 계약 없음.
11. test 이름: 접두 `test_it1_`, 피검 함수를 본문에서 직접 부른다.
12. 같음 판정: `NodeWrite`·`DeviceCoord`는 frozen dataclass 칸 비교, 포트 목록은 집합.
13. red 모양: T-1a·b·c·e·g·h·5a·5b는 시그니처 불변 진입점의 assertion red. 어휘 부재 T-G는 소스 문자열 red.
14. 상수·회로 이름: 새 상수 둘 다 이름 문자열, 숫자 0, 회로 이름 0.
