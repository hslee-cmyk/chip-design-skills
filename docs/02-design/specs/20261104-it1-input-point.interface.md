# interface card: 20261104-it1-input-point

card IT-1 범위 재작성(계획 v6.38.8 N6.5 범위 1~6, DEC-106, O-210 RR-6, O-173 P9-M1a). 옛 `20261021-it1-input-tie-removal`을 대체한다.

test 작성 주체는 엔진 소스를 보지 않고 이 문서와 기존 test 하네스(`E/tests/**`)만 쓴다. 피검 함수를 불러 기대값을 만들지 않는다. 공개 이름만 import한다. `E/` = `skills/analog-gmid-design/gmid_engine/`. 정본 문장 = design 41 v1.16.3 §4.7-V 1행·§4.7-1·§6.7-1a, 40 §3.11-4·-5, §2.4.8 S1v 행.

base = 이 card를 받은 통합 브랜치(`integ/it12` + master `7620f5ee` 병합). 이 base에 옛 IT-1(같은 DC 엣지 삭제)이 이미 있다 -- `input_tie` 부재는 재판정하지 않는다.

## 관찰 가능한 계약

### 공개 이름

| 모듈 | 심볼 | 값·서명 |
|---|---|---|
| `gmid_engine.sizing` | `REL_INPUT_POINT` | `"input_point"` (새로 생김) |
| `gmid_engine.sizing.s2_values` | `BRANCH_INPUT_CM_UNDEFINED` | `"input_cm_undefined"` (새로 생김) |
| `gmid_engine.sizing`·`gmid_engine.sizing.s2_values` | `BRANCH_INPUT_MULTIPLE_ROOTS` | **없음** |
| `gmid_engine.graph.s1_values` | `BRANCH_GVGS_SELF_EDGE` | **없음** |
| `gmid_engine.graph.s1_values` | `GvgsSummary` | 칸 `gate_source_same: tuple`(이름 정렬)이 늘어난다. 나머지 칸 `cyclomatic, v2_port0, v2_port1, v1, fixed_vgs, port_diff, vds_saturation` 불변 |
| `gmid_engine.graph` | `S1V_WRITES` | `("graph", "diode_nodes")`·`("graph", "composite_mos")`·`("graph", "composite_bundles")`·`("graph", "composite_internal")` 네 행이 늘어난다 |

서명 불변 진입점(행동 red를 맡는 자리): `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`, `dc_columns`, `s1_gvgs`, `s1v_fields`/`build_s1v`, `coupling_vars`, `run_kernel`/`size_and_seal`.

### 필드 -- 형식 불변, 값 어휘·y 키만 바뀜

| 필드 | 값 | writer | READS 변화 |
|---|---|---|---|
| `node.dc_writer` | `NodeWrite(tier, relation, element, known, y_key, order)`; `relation` ∈ {`rail`, `declared_target`, `input_dc`, `vgs_gate`, `vgs_source`, `resistor_drop`, `free_window`, `input_point`} | `dc_writer_plan` | + `node.port_role`, `graph.gvgs_summary` |
| `device.dc_coord` | `DeviceCoord(role, relation, partner)`; `relation` ∈ {`tree`, `parallel_vgs`, `cycle_vgs`, `fixed_vgs`} | `dc_writer_plan` | 같은 행 |
| `graph.gvgs_summary` | 위 `GvgsSummary` | `s1_gvgs` | 불변 |
| `graph.diode_nodes` 외 셋 | {S1V_KEY: 값}, 값은 `net_model` 결과의 같은 이름 속성과 같다 | `s1v_fields` | -- |
| `graph.vars` 외 `coupling_vars` 출력 | 값 불변 | `coupling_vars` | + 위 네 필드 |

### 입력 점 규칙(DEC-106 -- 손 판정 기준)

적용 조건: `input_dc_declared`가 거짓이고 `node.port_direction == "input"` 포트가 있다.

| 입력 포트 | 처리 |
|---|---|
| 하나(`single_ended_input` 등) | 무동작(옛 규칙: W4 뿌리 또는 KVL) |
| 둘이고 role이 `differential_input_p`·`differential_input_n` 각 하나 | 두 포트를 Kruskal·성분 계산에서 **한 점**으로 묶는다 |
| 그 밖(차동쌍 둘, 차동쌍 없는 입력 둘 이상, 차동쌍 + 다른 입력) | 탐색 전 정지: `StructureUnresolvedError`, `detail["reason"] == "unsupported_rule_branch"`, `detail["rule_branch"] == "input_cm_undefined"`, `detail["ports"]` = 그 포트 넷들(순서 단언 금지, 집합으로 비교) |

`input_dc_declared`가 참이면 위 표 전체가 무동작이다(포트 = F, relation `input_dc`).

한 점으로 묶은 뒤:
- **점이 F에 닿지 않음**: 성분 W4 뿌리 = 입력 점 하나. 두 포트 항목 모두 `relation == "input_point"`, `tier == "W4"`, `y_key == <role differential_input_p 포트 넷>`. θ 키 = `("y", <그 넷>)` 하나, 결과 JSON 키 `y:<그 넷>`. 입력 점 성분의 다른 넷은 입력 점에서 KVL로 쓰인다.
- **점이 F에 닿음**: v_cm은 KVL 종속, y 성분 0. 어느 포트 항목에도 `y_key`가 없고 두 포트 `node.dc_v`가 같다. 어느 포트가 어떤 relation을 받는지는 단언하지 않는다(어휘 안인지만).
- **종속**: 묶은 뒤 (gate, source)·kind가 같아지는 쌍은 하나가 `parallel_vgs`, `partner` = 다른 하나(어느 쪽인지 단언하지 않는다). 나머지 비트리 MOS는 기존 분류.
- **불변식**: 종속 수 = F 한 점·입력 점 한 점으로 묶은 G_vgs의 순환수(g = s 자기 고리는 순환 1).
- `node.dc_window` 항목 키 = 입력 점 뿌리 넷(p 포트) 하나. n 포트 항목은 없다.
- 고립 입력 포트(MOS gate·source와 저항 어디에도 닿지 않음)도 입력 포트로 세어 위 표를 따른다.

### g = s 규칙(O-210 RR-6 -- 손 판정 기준)

- gate 넷 == source 넷이면 레일이든 아니든 `s1_gvgs`가 정지하지 않고 `gate_source_same`에 그 소자를 적는다. `fixed_vgs` 칸은 옛 뜻(gate·source 둘 다 레일) 그대로라 레일 g = s 소자는 두 칸 모두에 든다.
- 쓰기 계획은 그 칸을 읽어 그 소자를 `DeviceCoord("dependent", "fixed_vgs")`로 둔다.
- 영역은 일반 선언 규칙이다. 꺼짐 분류·신호 경로 정지·사유 코드 없음.

### S1v 파생 술어(범위 6 -- 순수 리팩터링)

`diode_nodes`·`composite_mos`·`composite_bundles`·`composite_internal`이 S1v 필드다. `coupling_vars` 출력은 비트 동일이다.

### 단언 금지

`order` 칸 절대 순번(상대 순서만), `input_version` 문자열 값(같음·다름만), 평행 쌍 어느 쪽이 종속인지, F 닿는 입력 점의 포트별 relation 값, `detail["ports"]` 순서, TieBreak 후보 순서, `w4_root` 존폐(card TB-1 몫), `order_hints` 존폐(card TB-1 몫), 13회로 값(유보 -- O-225), `node.dc_window` 수치(card WB-1이 재작성).

## test 목록(위치 = 규칙 H 1:1, 이름 접두 `test_it1_`, 겹침 0 실측)

oracle: (손) toy 연결에서 손으로 유도, (독립) 어휘·소스 부재, (식) 위 규칙.

| id | 위치 | 내용 | oracle | base |
|---|---|---|---|---|
| T-1a | `tests/sizing/test_writer_plan.py` | 입력 DC 미선언 차동 toy(같은 꼬리 source): 두 포트 `input_point`, 같은 y 키 = p 넷, 입력쌍 둘째 소자 `parallel_vgs`, 종속 수 = 묶은 순환수(이 toy 1). base는 둘째 포트 `vgs_gate` W2 | (손) | red |
| T-1b | 같은 파일 | 두 포트가 서로 다른 G_vgs 성분인 차동 toy: 정지 없이 한 점, W4 뿌리 하나. base는 옛 사유로 정지 | (손) | red |
| T-1c | 같은 파일 | 입력 점이 F에 닿는 toy(입력쌍 source = 레일): y 성분 0(θ 키 없음), 두 포트 같은 전압, 쌍 둘째 `parallel_vgs` | (손) | red |
| T-1d | 같은 파일 | 입력 DC 선언 toy와 단일 입력 toy: 세 필드 = 손계산 | (손) | **green**(무동작 -- red 목록 제외) |
| T-1e | 같은 파일 | 정지 셋: 차동쌍 둘 / 차동쌍 없는 입력 둘 / 차동쌍 + 단일 입력. `rule_branch == "input_cm_undefined"`, `ports` 집합. base는 정지 없이 포트별 뿌리 | (식) | red |
| T-1f | `tests/search/test_orbit_ties.py`(기존 하네스) | 대칭 차동 toy(자기동형 궤도 묶음 + 입력 점): θ 성분 수·`domain.ties`·rank = 손계산, 이중 차감 0 | (손) | red |
| T-1g | `tests/sizing/test_writer_plan.py` | 이름 전단사: 넷·소자 이름을 맞바꾼 toy의 구조 결과가 같다(y 키는 맞바꾼 이름). role은 옮기고 이름 판별 없음 | (손) | red |
| T-1h | `tests/sizing/test_block_columns.py` | `dc_columns`: 입력 점 toy의 두 포트 `node.dc_v`가 같다, `node.dc_window` 키에 n 포트 없음 | (손) | red |
| T-5a | `tests/graph/test_gvgs_cycles.py` | 레일·비레일 g = s toy 같은 처리: 정지 없음, `gate_source_same` = 그 소자. base는 비레일 정지 | (손) | red |
| T-5b | `tests/sizing/test_writer_plan.py` | 비레일 g = s toy: `fixed_vgs` 종속, 종속 수 포함. 선언 없음 = 포화 기본·전도(봉인 진행, 꺼짐 표지 없음) | (손) | red |
| T-5c | `tests/structure` 또는 `test_writer_plan.py`(AST) | 쓰기 계획 소스에 gate·source 넷 동등 비교 0(READS만), g = s 판정식 자리 = `s1_gvgs` 하나 | (독립) | red |
| T-6a | `tests/graph/test_s1v_fields.py` | 네 필드 값 = `net_model` 같은 이름 속성(toy), 권한표 행 | (독립) | red |
| T-6b | `tests/graph/test_coupling_vars.py` | `coupling_vars` READS에 네 필드, 비test 엔진 소스 `net_model(` 호출 자리 = `s1v_fields` 하나(AST, 정의 줄 제외) | (독립) | red |
| T-6c | `tests/graph/test_coupling_vars.py` | 무동작: 기존 toy `graph.vars` 값 비트 동일 | (손) | green |
| T-RH | `tests/integration/test_stage_a_library.py` 또는 `tests/graph/test_s1v_build.py` | library 두 회로(`current_reuse_telescopic_ota`, `nmcnr_amplifier`): `structure.json` 사실이 여전히 적용됨. `graph.applied_facts` 비지 않음, findings에 `structure_fact_stale` 0. 기대 사실 = 그 JSON `facts`에서 직접 읽음 | (독립) | green(회귀 -- 재기록을 빼면 red) |
| T-G | `tests/structure/test_removed_names.py` | 비test 엔진 소스·CONTRACT에 `input_port_multiple_roots`·`BRANCH_INPUT_MULTIPLE_ROOTS`·`gvgs_self_edge`·`BRANCH_GVGS_SELF_EDGE`·`off_device_on_signal_path` 0 | (독립) | red |

red 예상 목록 = 엔진 동작·엔진 트리를 보는 test. T-1d·T-6c·T-RH 제외. 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다.

## 고칠 기존 test(test 주체 몫, 약화 아님 -- `broken_tests`에 나열)

건수 = `scope_grep.txt` 실측(integ/it12 `b9351eac`).

| 파일 | 이유 |
|---|---|
| `tests/sizing/test_writer_plan.py`(옛 정지 3건 + 차동 입력 기대) | DEC-106 (7) |
| `tests/sizing/test_s2_values.py`(옛 상수 1건, 어휘에 `input_point`) | DEC-106 |
| `tests/search/test_orbit_ties.py`(옛 정지 1건) | DEC-106 (7) |
| `tests/graph/test_gvgs_cycles.py`(2)·`tests/graph/test_s1_values.py`(2)·`tests/graph/graph_u2_oracle.py`(1) | O-210 RR-6 |
| `tests/graph/test_net_model.py`, S1v 권한표 단언 | 범위 6 |
| `tests/integration/fixtures/u17_1b_s0_baseline.json` | 입력 DC 미선언 회로 쓰기 계획이 바뀜. 갱신 주체 = test 주체, 원인 칸 DEC-106 |
| `tests/sizing/test_block_columns.py`·`test_input_window.py`·`test_kernel_context.py`·`test_scc_order.py`·`test_scc_newton.py`·`test_current_basis.py`·`test_kernel_run.py`·`test_size_and_seal*.py`·`tests/generality/pipeline.py` | 입력쌍 둘째 포트 `vgs_gate` 전제 -- 실행으로 확인 |

기대값을 현재 출력으로 붙여넣지 않는다. 손 유도가 안 되는 회귀 기준선은 원인 칸과 함께 나열하고 보고한다.

## 판정 측정(audit)

| # | 측정 | 합격 |
|---|---|---|
| A1 | 위 test 전부, red는 base에서 assertion 실패 | PASS |
| A2 | 새 test 체계 전체(test 파일당 프로세스 하나) | 전체 0 failed. base에 실패가 남으면 그 목록을 오케스트레이터에 올리고 판정을 멈춘다(A-31 병합 여부 확인, master에 아직 없음) |
| A3 | 구조 규칙 A~I, `tests/structure` | PASS + GL-1 병합 뒤 base에서 `ratchet.new` 0(새 키·수 증가 0). `block_columns.py` 쪽 줄어든 키는 판정자가 줄임. 행 추가로 통과시키면 `criteria_weakened`. |
| A4 | 잔재 grep(T-G와 같은 패턴, 엔진 전체) | 0 |
| A5 | 13회로 변화표, IT-0b 값 | **미완료(보류 다리)** -- 통과로 세지 않음, base sha 기록 |
| A6 | 연기 시험(병합 때 통합 브랜치 한 번): 입력 DC 미선언 차동 1회로 + 입력 DC 선언 또는 단일 입력 1회로 | 예외 없이 끝남(성능 판정 아님) |
| A7 | **`rule_hash` 공통 규칙**(위임 A-33·A-34): rule 파일(`S1V_RULE_FILES` ∪ `STRUCTURE_RULE_EXTRA_FILES`)을 고치는 커밋은 같은 커밋에서 `assets/library/{current_reuse_telescopic_ota,nmcnr_amplifier}.structure.json`의 `rule_hash` 줄만 재기록한다. 재기록하지 않으면 사실이 `structure_fact_stale`로 조용히 안 쓰인다(fail-open). `git diff` 두 파일 = `rule_hash` 줄뿐, 커밋 ③ 안, connectivity 변경 0, 값 비교 근거 기록, T-RH·Stage A 두 회로 | PASS |
