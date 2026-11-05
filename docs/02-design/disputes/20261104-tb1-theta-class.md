---
id: 20261104-tb1-theta-class
spec_card: docs/02-design/specs/20261104-tb1-theta-class.spec.md
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_dependent_member_name_bijection_outside_loop
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_dependent_member_ratify_agreeing_fact_is_noop_and_disagreeing_stops
test_id: gmid_engine/tests/sizing/test_writer_plan.py::test_w4_root_tie_stops_with_dc_colour_not_unique
test_id: gmid_engine/tests/sizing/test_dc_inputs.py::test_library_projection
test_id: gmid_engine/tests/sizing/test_dc_inputs.py::test_spec_path_triode_populates_regions
test_id: gmid_engine/tests/sizing/test_s2_values.py::test_s2_writers_is_s1_plus_dc_table_exactly
test_id: gmid_engine/tests/sizing/test_s2_values.py::test_dc_writes_constant_matches_table
test_id: gmid_engine/tests/sizing/test_s2_values.py::test_block_reads_declared_as_contract[dc_writer_plan]
test_id: gmid_engine/tests/graph/test_s1v_fields.py::test_block_name_and_writes_are_design_fields
test_id: gmid_engine/tests/graph/test_s1v_fields.py::test_writes_exactly_d1_fields_no_copies
---
## 문제의 test

code 커밋 뒤에도 실패하는 test 열 묶음. 구현은 interface 계약(§1 분류, §2 종속 멤버·ratify·W4)대로 했고, 아래 test 의 기대가 그 계약과 맞지 않거나 입력을 만들 수 없다. 측정은 모두 이 worktree 의 head 에서 단독 실행한 결과이고 코드 변경 없이 재현된다.

**A. 계약과 모순 또는 만들 수 없는 입력 (3건, 카드 T-T6·T-T7·T-T9)**

1. `test_dependent_member_name_bijection_outside_loop` (T-T6 고리 밖): 입력 `_sym4`는 (MA,MB)·(MC,MD) 평행 쌍 둘이 서로 자기동형(분기 oa-쪽 {MA,MC} <-> ob-쪽 {MB,MD})이다. 이름 전단사 σ(MA->Z1, MB->A1, MC·MD 그대로) 뒤 `dc_colour`(정준 위치)가 분기 대응을 따라 뒤집힌다: 실측 원 입력 MA=0 MB=1 MC=2 MD=3 (넷 oa=6 ob=7), σ 입력 A1=0 Z1=1 MC=3 MD=2 (넷 oa=7 ob=6). 계약 §2의 키는 `dc_colour`뿐이고(이름 금지) 한 분기를 고르는 어떤 `dc_colour` 규칙도 두 입력에서 서로 반대 분기를 고른다. 구현 결과: 원 입력 종속 {MB, MD} -> σ 이미지 {A1, MD}, σ 입력 종속 {Z1, MC} (분기가 뒤바뀐 같은 구조). 자기동형 분기의 선택은 이름 없이 σ-등변으로 만들 수 없다(`s1_symmetry`는 자기동형 정점의 정준 위치를 이름 순 정준 형식으로 매기며, `_p_port_first`가 이를 p 포트 하나에만 고정한다 -- 이 toy는 차동 p 포트가 없다). 고리 안 `loop_symmetric_a`·`b`·`inverter`·`triangle` 변형은 통과한다.
2. `test_dependent_member_ratify_agreeing_fact_is_noop_and_disagreeing_stops` (T-T7): '일치' 단계가 `build_ctx`(S1v 없음 -> interface §1 '전부 B', J-T5)로 구한 유도 종속을 `_ctx_with_facts`(`build_s1v` 사용 -> 인버터 두 MOS 의 AC 역할이 `input`, 매크로 비활성이라 §1 표대로 둘 다 F)의 사실 값으로 쓰고 좌표 동일을 단언한다. 인버터 고리의 유도는 B(정준 위치 앞쪽이 종속)와 F(뒤쪽이 종속)에서 반대이므로 두 컨텍스트의 유도가 다르다(실측: plain -> Mn, S1v -> Mp). 사실을 유도 결과와 일치시키려면 같은 S1v 컨텍스트에서 유도를 구해야 한다. §1 표(S1v 있으면 input -> F)와 J-T5(S1v 없으면 B)는 둘 다 계약이라 어느 쪽도 고칠 수 없다.
3. `test_w4_root_tie_stops_with_dc_colour_not_unique` (T-T9): `tamper(s1.snapshot, s1_symmetry.name, "node", "dc_colour", {"o2": col["o1"]})` 뒤 `build_kernel_context(S1Graph(...), **run)`은 같은 실행(`donors`)의 `s1_symmetry` 결과 색인 graft 로 주입을 되돌린다(`compute_block.__call__`: block_version 불일치 -> `donors.find(name, ..., version)` -> graft). 실측: 주입한 색이 커널 컨텍스트 안에서 원래 값으로 돌아가 정지가 나지 않는다(DID NOT RAISE). 구현은 W4 뿌리 후보 색 동률(성분 안·성분 뿌리끼리·G_vgs 밖 노드끼리)을 정지시키므로, 주입이 살아남는 입력(예: 다른 실행 `open_run()`으로 `build_kernel_context`, 또는 `dc_writer_plan` 단위 호출 직전 tamper)이면 통과한다.

**B. card 의 test 목록에 없어 갱신되지 않은 기존 test (7개 묶음 -- interface 변경의 직접 결과)**

4. `test_dc_inputs.py::test_library_projection`(7 회로)·`test_spec_path_triode_populates_regions`: `expected_projection`이 `DcInputs`의 새 칸(`has_gbw_target`·`has_rout_limit`·`has_settling`)을 기대 False 로 만든다. interface §1 은 `dc_inputs_from_spec`이 spec 선언 유무로 이 칸을 채운다(J-T1, '재작성 범위 dc_inputs.py 선언 사실 투영'). 실측 차이 칸: current_reuse_telescopic_ota 는 `has_settling`, ngcc_3stage_ff·nmcnr_amplifier·two_stage 류는 `has_gbw_target`, pushpull_follower_buffer 는 `has_rout_limit`(회로별 차이 칸을 test 출력에서 읽었다).
5. `test_s2_values.py::test_s2_writers_is_s1_plus_dc_table_exactly`·`test_dc_writes_constant_matches_table`: 표 `DC_TABLE`에 `("device","theta_class"): "theta_class"`가 없다(interface §1 새 필드).
6. `test_s2_values.py::test_block_reads_declared_as_contract[dc_writer_plan]`: 기대 READS 에 새 입력(`device.theta_class`·`graph.orbits`·`graph.views`·`graph.dependent_facts`)이 없다(interface §2 입력).
7. `test_s1v_fields.py::test_block_name_and_writes_are_design_fields`·`test_writes_exactly_d1_fields_no_copies`: S1v 필드 집합 `ALL_FIELDS`에 `dependent_facts`가 없다(spec J-T2 새 S1v 필드).

## 근거(oracle 또는 사용자 원문)

interface card §1(S1v 없으면 전부 B, 있으면 매크로 비활성 `input` -> F), §2(키 = `device.dc_colour`, 이름 금지, ratify 표, W4 뿌리), spec card J-T1·J-T2·J-T5. 위 1·2·3 은 측정으로 확인한 구성상의 불가능이고(원 구현 변경으로 풀리지 않는다), 4~7 은 card 가 test 주체에게 준 파일 목록(`conftest.py`, `test_kernel_run.py`, `test_s2_values.py`, `test_size_and_seal.py`, `test_writer_plan.py`)에서 `test_dc_inputs.py`·`test_s1v_fields.py`와 `test_s2_values.py`의 표 셋이 빠져 생긴 갱신 누락이다.

## 요청

1 -- 이 toy 에서 σ-등변성을 요구하지 않도록 test 를 바꾸거나(자기동형 분기의 선택은 정준 형식 안에서 한 입력 안의 일관성 -- 두 평행 쌍의 종속이 같은 분기에 있음 -- 으로 단언), 자기동형이 없는 구조의 고리 밖 red toy 로 바꾼다. 2 -- plain 컨텍스트도 `build_s1v`로 구한다(또는 일치 단계의 값을 S1v 컨텍스트의 `_co`에서 유도). 3 -- 주입이 graft 로 되돌려지지 않는 구성(다른 `open_run()` 쌍 또는 `dc_writer_plan` 직접 호출)으로 바꾼다. 4~7 -- 새 칸·필드·READS 를 기대에 반영한다(기대값 주체: test 작성자). 구현 쪽 변경은 요청하지 않는다.
