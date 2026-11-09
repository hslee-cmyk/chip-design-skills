---
id: 20260930-b26-rail-accessor-set
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

계획 DF-19·DF-26(담당 Phase 4)의 **넷 몫 첫 card(B26-1)**. 엔진은 지금 topology 최상위 `supply_nets`를 한 곳도 읽지 않고(운영 코드의 `supply_nets` 참조는 SR 4361 하나이며
그것은 metric 선언 안의 같은 이름 키다) 레일을 넷 이름 집합으로 정한다 -- SD `_RAIL_NETS = {"vdd","gnd","vss"}`, SR `_DEFAULT_RAIL_HI/LO`(대소문자 6개), SR `_metric_kcl_residual`
인라인 튜플(6개), SR `_build_theta_evaluator` 인라인(3개), SD `_propose_*` 씨앗(`vdd`·`gnd` 2개). 이 card는 **레일 선언을 읽는 정본 접근자 하나**를 만들고, **"이 넷이 레일인가"만 묻는
집합 판정 사이트**를 그 접근자가 준 선언으로 바꾼다. A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 cd64170.

앞당김: 계획 정정(`_drafts/draft_b26_plan_patch.md` -- DEC-60 넷 전환기 종료, DF-19·DF-26을 MG1에서 분리, Phase 3 전 가능)이 이 card의 착수 조건이다. **base = P9(`kcl_series_union`
본문 엣지 정의를 `_kcl_and_matching_edges` 호출로 통합) 병합 뒤 master**. P9가 SD 3042 판정을 없애므로 이 card에서 `kcl_series_union`은 `rails`를 받아 `_kcl_and_matching_edges`로
넘기는 통과 함수가 된다(착수 시 줄 번호 재측정).

**원칙을 계약으로(전 범위)**:
1. **topology 무관**: 새 접근자와 바꾸는 사이트 전부에 넷·소자·회로 이름 리터럴이 없다. 레일 여부는 선언 `supply_nets`의 원소인가로만 정한다(대소문자 변환·접두어 규칙 없음).
2. **조용한 폴백 금지**: `supply_nets`가 없으면 `ValueError`로 거부한다. 이름 집합으로 대신 판정하는 경로를 두지 않는다(DEC-60 넷 전환기 종료 -- 계획 정정). 레일 인자는 **기본값 없는
   키워드 전용 인자**다(기본값을 이름 집합이나 `None`→이름 집합으로 두면 원칙 위반이 되살아난다).
3. **재계산 금지(NFR-2)**: 새 캐시를 만들지 않는다. `load_topology` 한 번에 선언을 한 번 읽어 `meta["rails"]`에 싣고, SR은 이미 `load_topology`의 `meta`를 보관하는
   `_load_full_topology_cached` 엔트리(`_topology_meta_cached`)에서 꺼낸다. 평가 루프 안에서 접근자 호출 0회.
4. **만들면 배선**: 접근자는 `load_topology`가 부르고, 바꾼 사이트의 `rails`는 전부 그 호출에서 온다(운영 경로: `run_harness.run` → `optimize_full_circuit_budget`/
   `run_full_circuit_audit_from_topology` → `load_topology`).

**범위 밖(다른 card)**: 극성(높은/낮은 레일)이 필요한 사이트 = B26-2(사용자 결정 D1 대기): SD `trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`(1222·1233·1234·1270·1281·1282 --
종료 판정 `en in _RAIL_NETS`도 함수 전체가 극성 사이트라 함께 B26-2), 방향 라벨 비교(SD 1355·1357·1557·1558·1737), SR `propagate_node_voltages`·`derive_vsb_from_nodes` 기본 인자(3728·3790),
`_metric_supply_current`(4361), `_metric_rail_referenced_voltage`(4626), `_metric_battery_centering_deviation`(4650~4653). MNA 고정 노드 = B26-3(D2 대기): SR 4086·4991.
이름 상수 삭제·'운영부 레일 이름 리터럴 0' lint = B26-4. 레일 전압(`supplies_v`, 스칼라 `vdd`) = MG1.

**집합 판정인데 이 card에서 빼는 것(근거 실측)**:
* SR 7282 `_hr_resolve_vertical_group`, SR 8003·8091 `_build_theta_evaluator`의 `_rail_nets`(→ `_hr_thin_singleton_ideal_source_check` 6881·6886, `_hr_fold_group_check` 6920·6931·6948):
  **library에서 관찰되지 않는다** -- scratch 변이 실측(8003 → `frozenset()`, 7282 → `if False:`)에서 사이징 대상 4회로 평가(`_library_sized_contexts._theta_point` 점) 결과가 변이 전과
  같았다(파일럿·`folded_cascode` `ctx.sized`·metric 동일, `two_stage_ota`·`nmcnr_amplifier`는 같은 `InfeasibleSizingError`). 합성 레일 이름으로 red를 만들려면 평가가 레일 극성
  (`propagate_node_voltages`, B26-2)을 지나야 하므로 V3 변이를 죽일 test를 이 card에서 쓸 수 없다. **B26-2로 옮긴다**(같은 평가 경로의 극성 사이트와 한 card에서 합성 평가 test로 판정).
* SR 3950 `node_pole_estimate`(운영 미도달, 레지스트리 §7 '삭제 후보, 보류(Phase 4)'), SD 3559·3561·3719 `propose_theta_kcl_gap_fill`(운영 호출 0, '배선 승인 필요, 보류(Phase 3)'):
  운영 경로에서 불리지 않는 함수에 레일 인자를 더하지 않는다(배선 원칙). 삭제·배선 결정과 함께 B26-4 lint가 처리한다.
* `skills/analog-grammar/assets/netclass.py`·`idioms.py`의 이름 집합 `RAILS`·`RAILS_POS`·`RAILS_NEG`: SD 운영 함수 7개가 `_import_analog_grammar`로 부른다. 극성 판정이고
  code-author 쓰기 경로 밖이다 -- 계획 정정안 DF-19 비고에 새 사이트로 올린다(이 card 범위 밖).

## 관찰 가능한 계약

1. **접근자** `stick_diagram.rail_declaration(topology)`: 인자는 topology JSON 한 파일을 읽은 dict. 반환 `RailDeclaration(nets=frozenset(topology["supply_nets"]))`(frozen dataclass,
   필드 `nets` 하나 -- B26-2가 극성 필드를 더한다). 거부(`ValueError`, 메시지에 `supply_nets`와 DEC-60을 적는다): 키 없음 / 값이 list가 아님 / 원소가 빈 문자열이거나 str이 아님 /
   같은 원소 중복. **빈 list `[]`는 받는다**(레일 없음이라는 명시 선언 -- 조용한 기본값이 아니다). 선언 밖 넷 이름은 보지 않는다(`"vdd"`라는 넷이 있어도 선언에 없으면 레일이 아니다).
   docstring에 '검사하지 않는 것:' 절을 둔다: 선언 넷이 netlist·수동소자·이상원 단자에 실제로 있는가, 숨은 레일 후보(DEC-60 (iii)), 극성 -- 이것들은 GB0(6a)·B26-2 몫.
2. **`load_topology(json_path)`**: 진입 파일 dict로 `rail_declaration`을 **정확히 한 번** 부르고 결과를 `meta["rails"]`에 싣는다. `supply_nets`가 없으면 다른 분석 전에 `ValueError`.
   `linked_topology_files`의 파일이 `supply_nets`를 선언하고 그 집합이 진입 파일과 다르면 `ValueError`(어느 쪽을 고를지 추측하지 않는다). 연결 파일에 선언이 없으면 진입 파일 선언을 쓴다
   (`test_ic3` 5-a 입력이 이 형태다). `meta`의 다른 키와 `transistors`는 base와 같다(계약 8).
3. **캐시(NFR-2)**: `_load_full_topology_cached`·`_topology_meta_cached`에 새 캐시·새 엔트리 필드를 만들지 않는다. SR 소비처는 `_topology_meta_cached(path)["rails"]`(이미 보관된 meta)나
   이미 손에 든 `meta["rails"]`를 쓴다. 관찰: 같은 topology로 `load_topology` 1회 → `rail_declaration` 호출 1회, 그 뒤 `compute_metric`(kcl_residual)·`l_sharing_classes`를 몇 번 불러도
   추가 호출 0회(test가 `stick_diagram.rail_declaration`을 계수 래퍼로 바꿔 센다). 캐시 키가 경로 문자열인 것은 기존 결함이고(S0 지문 = 6a) 이 card는 같은 엔트리를 재사용만 한다.
4. **바뀌는 시그니처**(모두 끝에 기본값 없는 키워드 전용 `rails: RailDeclaration`, 판정은 `rails.nets` 소속만):
   * 판정 사이트(SD): `find_matching_candidates(transistors, idiom_matches=None, *, rails)`(1014), `find_differential_pair_candidates(transistors, inputs=(), outputs=(), feedbacks=(),
     biases=(), clocks=(), *, rails)`(1575 -- 1557·1558 방향 라벨은 B26-2), `_diff_pair_layer1_groups(transistors, *, rails)`(1617), `_propose_gm_id_roles(transistors, base_inputs,
     outputs, feedbacks, biases, clocks, *, rails)`(2096 씨앗 = 선언 레일 각각을 자기 자신에), `_propose_L_roles(transistors, relations, base_inputs, outputs, feedbacks, biases, clocks,
     *, rails)`(2172 같음), `kcl_series_union(netlist, matching_pairs, *, rails)`(P9 뒤 통과), `_kcl_and_matching_edges(transistors, matching_pairs, *, rails)`(3148),
     `audit_vertical_stack_id_vs_kcl(transistors, matching_pairs, device_roles, *, rails)`(3253), `propose_device_roles_gap_fill(transistors, device_roles, matching_pairs_meta,
     compensation_stage_devices=None, vds_theta_authoritative=None, inputs=(), outputs=(), feedbacks=(), biases=(), clocks=(), *, rails)`(3992 씨앗, 4171·4307·4323·4370·4392).
   * 판정 사이트(SR): `true_current_mirror_groups(by_name, *, rails)`(2207).
   * 통과(레일을 아래로 넘기기만 한다, SD): `check_symmetry_dispositions(transistors, matching_pairs, dispositions=None, *, rails)`, `run_full_circuit_audit(devices, expected_counts,
     dispositions, box_shape_checks=None, row_width_tol=1.5, accept_fail_blocks=None, *, rails)`, `refine_differential_and_mirror_relations(transistors, inputs=(), outputs=(),
     feedbacks=(), biases=(), clocks=(), max_iterations=5, *, rails)`, `propose_vertical_stack_id_gap_fill(transistors, matching_pairs, device_roles, inputs=(), outputs=(),
     feedbacks=(), biases=(), clocks=(), *, rails)`, `_kcl_branch_map(devices, *, rails)`, `_branch_composite_pair(a, b, devices_by_name, matching_pairs, *, rails)`,
     `_composite_collapse_for_crossover(transistors, matching_pairs, pair_sensitivity=None, *, rails)`, `find_min_crossover_layout_with_branch_composite(transistors, matching_pairs,
     pair_sensitivity=None, *, rails)`, `repair_matching_safety(rows, matching_pairs, pair_sensitivity=None, max_iter=3, relaxed_pairs=None, *, rails)`.
   * 통과(SR): `resolve_stack_layout(transistors, matching_pairs, device_roles, stack_groups_override=None, *, rails)`.
   * 시그니처가 **안 바뀌는** 뿌리(선언을 스스로 얻는다): `load_topology`(계산), `run_full_circuit_audit_from_topology`(`load_topology` meta), SR `_build_theta_evaluator`(자기
     `load_topology` meta), `l_sharing_classes`·`l_class_owners`·`audit_l_sharing_consistency`·`synthesize_l_class_thetas`(`meta["rails"]`), `_metric_kcl_residual`(`ctx.topology_path`의
     `_topology_meta_cached`), `optimize_full_circuit_budget`·`run_topology_pipeline_with_finger_fixup`(topology 경로), `run_matching_safety_with_finger_growth`·`_fixup_euler_blocked_rows`
     (`ctx.topology_path`).
5. **meta 소비처**: `l_sharing_classes(by_name, meta, …)`(와 이것을 부르는 세 함수)는 `meta`에 `"rails"`가 없으면 `ValueError`(이름 집합으로 대신하지 않는다).
6. **`_metric_kcl_residual`**(`compute_metric({"type": "kcl_residual", …}, ctx)`): 잔차에서 빼는 레일 = `ctx.topology_path`의 선언 레일. 선언에 metric 키 `rail_nets`가 있으면
   `ValueError`(레일은 topology `supply_nets`로만 선언한다 -- 옛 키 거부 게이트 일반형은 MG1). library 선언의 `rail_nets` 사용 0건(실측).
7. **행동(합성 topology, 라이브러리에 없는 넷 이름)**: 레일을 `rail_hi`·`rail_lo`처럼 library에 없는 이름으로 선언한 topology에서 (a) 같은 kind 두 소자가 선언 레일을 source로 공유해도
   `find_matching_candidates`의 `diff_pair`·층위1 폴백 후보가 아니고 `load_topology` meta `_matching_pairs_autofilled`에 그 쌍이 없다 (b) `_kcl_and_matching_edges`·`kcl_series_union`이
   선언 레일을 통해 소자를 잇지 않는다 (c) 게이트가 선언 레일에 물린 소자는 `l_sharing_classes`의 미러 동치류를 만들지 않는다 (d) kcl_residual이 선언 레일 노드를 잔차에서 뺀다.
   **역방향**: 선언에 없는 넷이 `vdd`·`gnd`·`vss`라는 이름이어도 레일로 취급하지 않는다(보통 내부 노드와 같다).
8. **동작 보존**: E-LIB 9/9 -- `load_topology(c)`의 `transistors`와 `meta`(새 키 `"rails"` 제외)가 base와 같고 `meta["rails"].nets` = 그 회로의 `supply_nets`; `run_topology_pipeline(c)`
   출력이 base와 같다. `run_full_circuit_audit_from_topology` 9/9 결과(또는 같은 예외)가 base와 같다. E-INST(파일럿·`folded_cascode`) `instance.json` 해시 동일.
9. **남는 이름 리터럴(auditor AST 측정 -- 영구 test 아님)**: `prep_b26_supply_nets.md` §1 규칙의 스캔(대상 `A/*.py` + `workspaces/run_harness.py`, docstring 제외, 이름 상수·`.rail_nets`·
   레일 이름 문자열 리터럴)을 base와 병합본에서 돌려 (파일, 최상위 함수, 종류) 다중집합으로 비교한다: **병합본 = base − 아래 '작성 전 실측' 1의 B26-1 행**(새 행 0). 부수 관찰:
   병합본에서 `_RAIL_NETS` 참조 함수 = `trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`·`propose_theta_kcl_gap_fill`, `_DEFAULT_RAIL_HI/LO` 참조 함수 = `propagate_node_voltages`·
   `derive_vsb_from_nodes`·`node_pole_estimate`·`_hr_resolve_vertical_group`(상수 정의 제외).
10. **배선(V7)**: 새 def `rail_declaration`이 `reachability_roots`에서 도달한다(`load_topology` 경유). 계약 4의 판정 사이트마다 `rails` 실인자가 `load_topology`의 `meta["rails"]`에서 온다
    (auditor가 호출 그래프로 확인 -- 운영 코드에서 `RailDeclaration(...)`을 직접 만드는 곳은 `rail_declaration` 하나).
11. **레지스트리(code-author, 같은 커밋)**: §2 45행 '레일 넷 집합'의 정본 칸 = `stick_diagram.rail_declaration`(B26-1). 40행(전류미러 그룹)·43행(KCL 엣지)의 'B26 해소 뒤 확정' 조건 중
    레일 판정 몫을 해소로 고친다(다른 조건은 그대로). 42행(노드 DC 전압)·53~56행(MNA)은 그대로(B26-2·B26-3). §6 `_metric_kcl_residual` 행의 '인라인 튜플' 문장을 선언 기반으로 고친다.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `RailDeclaration` | `@dataclass(frozen=True) class RailDeclaration: nets: frozenset` |
| `stick_diagram` | `rail_declaration` | `def rail_declaration(topology: dict) -> RailDeclaration:` |

## 판정 유형 근거

red-green. base에서 실패(assertion)하는 입력: 계약 7(합성 레일 이름 topology를 `load_topology` meta·`compute_metric`·`l_sharing_classes`에 넣는다 -- 이 셋은 시그니처가 안 바뀌어
base에서도 호출되고 이름 집합 때문에 틀린 값을 낸다), 계약 2(`supply_nets` 없는 topology를 base는 받아 들인다, 연결 파일 선언 충돌도 받는다), 계약 6(`rail_nets` 키를 base는 읽는다),
setup 수준 레일 이름 바꾸기 불변(아래 oracle (b)). 신규 심볼(`rail_declaration`, `RailDeclaration`)은 base에서 `ImportError`/`AttributeError`로 red 수집 플러그인의 신규 심볼 판정에 걸린다.
**주의(V2)**: 계약 4의 새 키워드 인자를 직접 넘기는 test는 base에서 `TypeError`다 -- 허용 예외 타입 밖이라 red로 세지 않는다. red 증거는 위 공개 진입점 test가 맡고, 판정 기록은
두 종류를 나눠 적는다.

## oracle 종류와 출처

(a) 구성: 합성 topology(라이브러리에 없는 넷·소자·회로 이름, 선례 `tests/contracts/test_d_delete_telescopic.py` 185·215행 `_SYN_RAILS = ["rail_hi","rail_lo"]`, `supply_nets`
선언)에서 기대값을 손으로 적는다 -- 어느 쌍이 차동 후보인지, 어느 소자가 KCL로 이어지는지, KCL 잔차를 손으로 계산. (b) 변환 불변(IC11 `test_rail_origin_shift_invariance`와 같은 종류):
library 사이징 대상 topology의 레일 넷 이름만 바꾼 사본(tmp)에서 `_build_theta_evaluator(사본, canonical_spec)`의 **setup 반환값** `stack_groups_kcl`·`stack_groups_geometry`가 이름을 되돌리면
원본과 같다(evaluate는 부르지 않는다 -- 평가는 B26-2·B26-3 사이트를 지나 아직 불변이 아니다). scratch 실측: 병합 상당 사본 4/4 같음, base는 `two_stage_ota`에서 다름(red).
**`load_topology` meta 전체의 이름 바꾸기 불변은 이 card의 계약이 아니다**: 병합 상당 사본에서도 `_device_roles_gap_fill_review_needed`(4회로)와 `two_stage_ota` `device_roles`가 달라진다 --
analog-grammar `RAILS`와 B26-2 사이트가 남아 있기 때문이다(실측: analog-grammar 집합을 바꾼 이름으로 맞추면 `two_stage_ota`는 같아지고 나머지 3회로 `review_needed`는 여전히 다르다).
(c) 동작 보존 = base 실행 결과(E-LIB·E-INST, auditor).

## 거부해야 할 입력

`supply_nets` 없음 / list 아님 / 빈 문자열·비문자열 원소 / 중복 원소 → `rail_declaration`·`load_topology` `ValueError`. 연결 파일의 다른 `supply_nets` → `load_topology` `ValueError`.
`meta`에 `"rails"` 없음 → `l_sharing_classes` `ValueError`. kcl_residual 선언의 `rail_nets` 키 → `ValueError`. 판정기 자기 점검: 거부 test는 **조용한 통과(기본값 대입)** 합성 구현을
넣으면 실패해야 한다(`test_d_delete_telescopic`의 `test_rejection_check_fails_on_silent_or_unlisted_refusal`과 같은 형태).

## library 회로 적용 여부

library 9회로 전부 `supply_nets` 선언(`_TEMPLATE` 제외 -- 작성 틀이고 base에서도 `load_topology`가 `AttributeError`로 못 읽는다). 계약 8(E-LIB 9/9, 감사 9/9, E-INST 2)과 oracle (b)
(사이징 대상 4회로)에 쓴다. `agnd`(두 pushpull 회로)는 커패시터 단자에만 나와 이 card의 트랜지스터 단자 판정 결과를 바꾸지 않는다.

## 무동작 판정 입력(무발동 값)

library 9회로 전부: 선언 레일 ∩ 트랜지스터 단자 넷 = 옛 이름 집합 ∩ 트랜지스터 단자 넷이라 바꾼 사이트의 판정이 base와 같다(scratch 실측 -- '재현할 수치'). `_propose_*` 씨앗은 base가
`vdd`·`gnd`뿐이라 vss 회로 3개(`nmcnr_amplifier`, `pushpull_follower_buffer`, `sf_pushpull_output_opamp`)에서 씨앗이 하나 늘지만 `load_topology` 결과는 9/9 같다.

## 재현할 수치

scratch(C:/g23, cd64170 사본 두 벌 -- 원본 / B26-1 사이트만 선언 레일로 바꾼 사본):
* `load_topology` 9/9 같음(`transistors`·`meta` 전체, float는 `float.hex`), `run_full_circuit_audit_from_topology` 9/9 같음(2회로 결과 동일, 7회로 같은 `ValueError`
  `_netlist_sections_structured`가 없다 -- 경로 문자열만 사본 위치 차이).
* 사이징 대상 4회로 `_build_theta_evaluator` + `_theta_point` 평가: `current_reuse_telescopic_ota`(metric 19, sized 51)·`folded_cascode`(metric 5, sized 13) 같음,
  `two_stage_ota`('stage1_ref' 헤드룸)·`nmcnr_amplifier`('stage2_diode_ref', 0.525 V) 같은 `InfeasibleSizingError`.
* 합성 4소자(NMOS `Qa`·`Qb` source `rail_lo`, 게이트 다름 / PMOS `Pa`·`Pb` source `rail_hi`, 게이트 `bias_p`, `supply_nets = [rail_hi, rail_lo]`): base `find_matching_candidates`
  `diff_pair = {(nmos, rail_lo): [Qa, Qb]}` → 병합 상당 `{}`; `_kcl_and_matching_edges` base 4엣지(`rail_lo`·`rail_hi` 경유 2개 포함) → 2엣지; `kcl_series_union` base 1그룹
  `{Qa: [Qa, Qb, Pa, Pb]}` → 2그룹; `load_topology` meta base `_matching_pairs_autofilled = [{names: [Qa, Qb], matching_sensitivity: offset, source=layer1_diff_pair_fallback}]`와 네 소자
  `L_role: mirror`·`gm_id_role: matching` 자동 채움 → 병합 상당 `null`, `headroom_role`만.
* oracle (b) setup 불변: base `two_stage_ota` 다름 / 나머지 3 같음, 병합 상당 4/4 같음.

## 결정 필요 항목

사용자 결정 없음(D1 극성·D2 MNA는 이 card 밖). 착수 조건 셋:
1. 계획 정정 커밋(`draft_b26_plan_patch.md` -- 원칙 기본안, DEC-60은 사용자 확정 결정이므로 **보고 때 알린다**).
2. P9 병합(이 card의 base).
3. **앞당김 확인**: 이 card는 Phase 4 DF를 Phase 2 진행 중에 하는 것이고, 머리의 `approval`(design 20 승인)은 DF-35·DF-36 선례를 따른 것이다. 그 두 card는 사용자 지시("DF-36도 같이
   진행해")로 당겼다 -- B26-1은 원칙 기본안(Phase 3 전이 싸다)으로 당기므로, 사용자에게 앞당김을 알리고 이의가 없음을 기록한다(필요하면 `target_kind: decision` 승인 기록을 `approval`
   줄로 더한다).

## 작성 전 실측

(cd64170, 2026-09-30. 저장소·worktree 쓰기 없음. scratch C:/g23 -- `git archive cd64170 skills/analog-gmid-design/assets skills/analog-grammar workspaces/run_harness.py tools/gates docs/01-plan`
두 벌. 끝나면 C:/g23 삭제.)

1. **사실 재측정 -- B26-1 행**: AST 스캔(`prep` §1 규칙 그대로 다시 구현, docstring 제외) 113행 중 이 card가 바꾸는 행:
   SD 1014 `find_matching_candidates` · 1575 `find_differential_pair_candidates` · 1617 `_diff_pair_layer1_groups` · 2096 `_propose_gm_id_roles`(`vdd`·`gnd` 리터럴 2) ·
   2172 `_propose_L_roles`(2) · 3042 `kcl_series_union`(P9가 먼저 없앤다) · 3148 `_kcl_and_matching_edges` · 3253 `audit_vertical_stack_id_vs_kcl` · 3992·4171·4307·4323·4370·4392
   `propose_device_roles_gap_fill`; SR 2207 `true_current_mirror_groups`(이름 참조 2) · 4293 `_metric_kcl_residual`(리터럴 6). = 11함수, 16줄. `prep`의 줄 번호와 전부 일치.
   명령: `python -B C:/g23/scan.py` (`grep -n "_RAIL_NETS\|_DEFAULT_RAIL_HI\|_DEFAULT_RAIL_LO\|rail_nets\|supply_nets\|_rail_nets" A/stick_diagram.py A/sizing_recipe.py workspaces/run_harness.py`와 교차 확인).
   호출 그래프(AST, 모듈 간 import 포함): 새 인자를 받는 함수 20개(SD 18, SR 2 -- 계약 4), 선언을 스스로 얻는 뿌리 10개. `_metric_kcl_residual`은 `_METRICS_REGISTRY` 경유 운영 도달.
   "엔진은 `supply_nets`를 읽지 않는다": 운영 코드 참조는 SR 4361(metric 키) 하나, 최상위 선언을 읽는 것은 test 보조 `tests/unit/_library_sized_contexts.py` `declared_supply_nets`뿐.
   **새로 찾은 것**: analog-grammar `netclass.py` 33~35행 `RAILS_POS/NEG/RAILS` 이름 집합 -- SD 11함수(운영 7)가 부른다(`prep` 스캔 범위 밖이었다).
2. **이름 충돌**: `grep -rn "rail_declaration\|RailDeclaration" skills workspaces tools docs/01-plan docs/02-design` → 0. 이름을 `validate_*`·`check_*`로 짓지 않았다 -- IC5 대상 규칙
   (`tests/contracts/test_ic5.py` `_TARGET_NAME_RES`)과 영역 표(21행 고정)에 걸리지 않게. 새 test 파일(예: `tests/contracts/test_b26_rail_accessor.py`)은 `glob(` 사용처 전수(`grep -rn "glob(" A/tests/` -- contracts 20곳, tools 3곳, unit 1곳)의
   이름 패턴(`probe_*.py`, `*.topology.json` 등)과 겹치지 않는다. 다만 contracts의 파일 스캔형 test가 `tests/**/*.py` 내용을 읽으므로 새 test에 삭제된 이름 참조·print 판정 토큰을 두지 않는다.
3. **원칙의 계약화**: topology 무관 = 계약 1·7(역방향 포함)·9, 폴백 금지 = 계약 1·2·5·6과 '거부해야 할 입력', 재계산 금지 = 계약 3, 배선 = 계약 10.
4. **쓰기 경로**(N3.12.2): SD·SR = code-author, 레지스트리 = code-author(계약 11), test·픽스처·probe = test-author(`A/tests/**`), 계획 정정 = 오케스트레이터. test-author는 엔진 소스를 못
   읽는다 -- interface card(계약 4의 새 시그니처 전부, 계약 2·5·6의 거부, 아래 7의 픽스처 규칙)만으로 쓸 수 있게 적었다.
5. **계획서 소비자**: 지우는 이름 없음(상수 3개는 B26-2·B26-4까지 남는다). 바뀌는 계획 문구(DEC-60 전환기) 소비자 = 계획서 254·314·388·769·802·870·929·936·1001·1021·1101행
   (정정안 §1~§6), `docs/02-design`의 "전환기 이름집합" 인용 0건.
6. **미배선**: 새 def `rail_declaration`은 `load_topology`가 부른다 -- 운영 도달(scratch 호출 그래프: `run_harness.run` → `run_full_circuit_audit_from_topology`/`optimize_full_circuit_budget`
   → `load_topology`). V7 면제 불필요. `RailDeclaration`은 클래스.
7. **기존 test 영향**(test-author 몫, 판정 기준을 바꾸지 않는 입력 갱신):
   * 새 키워드 인자를 받게 되는 함수의 test 호출(AST, cd64170): `test_selftest_stick_diagram.py` 12함수 49곳(`find_matching_candidates` 9, `refine_…` 9, `propose_device_roles_gap_fill` 8,
     `repair_matching_safety` 7, `check_symmetry_dispositions` 4, `propose_vertical_stack_id_gap_fill` 3, `run_full_circuit_audit` 2, `audit_vertical_stack_id_vs_kcl` 2,
     `_composite_collapse_for_crossover` 2, `_branch_composite_pair`·`find_min_crossover_layout_with_branch_composite`·`find_differential_pair_candidates` 각 1),
     `test_selftest_sizing_recipe.py` `resolve_stack_layout` 2곳, `tests/probes/` 4파일 `true_current_mirror_groups` 각 1곳. **P9 병합 뒤 추가**: P9 계약 test가 `kcl_series_union`·
     `_kcl_and_matching_edges`를 직접 부른다(P9 card 계약 2·4) -- B26-1 base에서 다시 세고, 그 계약 test에 `rails=`를 더하는 것은 test-author 몫(판정·기대값 불변).
   * `supply_nets` 없이 topology를 만들어 로드 경로에 넣는 픽스처: `test_selftest_sizing_recipe.py` 15개(180·237·289·457·585·878·1008·1899·1924·1987·2079·2161·2227·2273·2459행),
     `test_selftest_stick_diagram.py` 4개(1780·1787·2798·3988행). `test_ic3.py` 78행은 instance이고 286행은 연결 파일(진입 파일이 library 사본이라 선언이 있다) -- 조정 불필요.
     `test_d_delete_telescopic.py` 합성 topology는 이미 선언이 있다. `test_df36_instance_relpath.py`·`test_probe_*`는 library 파일을 읽는다 -- 조정 불필요.
   * **픽스처 규칙(동작 보존)**: 기존 픽스처에는 그 픽스처가 쓰는 넷 중 base가 레일로 읽던 이름(`vdd`·`gnd`·`vss`)을 선언한다(`tests` 트리 안 대문자 레일 이름은 각 1회 -- 해당 픽스처를
     확인). 레일 넷이 없는 픽스처(585 `bad_fixture`, 878·1008 `m3a_row`, 3988 `conflict_fixture` -- 넷리스트가 변수라 test-author가 확인)는 실제 넷에 맞춰 선언하고 없으면 `[]`.
     585는 `ValueError` 메시지에 `_COMPENSATION_REGISTRY`를 기대한다 -- 선언이 없으면 `supply_nets` 거부가 먼저 나므로 반드시 선언을 더한다.
   * 위험: `_propose_*` 씨앗은 base가 `vss`를 몰랐다 -- `vss` 픽스처(237·289·1987·2079·2161·2227)에서 결과가 바뀔 수 있다(library vss 3회로 불변, 아래 전체 실행에서도 판정 불변). 병합본에서 기존 기대값과
     다르면 test-author는 기대값을 고치지 않고 dispute로 올린다(작성자≠검증자).
   * scratch 전체 test 실행(`-P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. skills/analog-gmid-design/assets/tests --gmid-phase=2 --gmid-strict=`, 원본 사본 대
     B26-1 상당 사본 -- 사본은 픽스처마다 선언 대신 전역 레일 `{vdd, gnd, vss}`를 쓰므로 위 픽스처 규칙의 근사): 둘 다 **744 passed · 54 failed · 15 xfailed이고 실패 집합이 같다**
     (54건은 사본에 `.git`·`docs/03-analysis`·`workspaces` 일부가 없어서 나는 환경 실패 -- `test_extract_selftest` 38, `test_ts6_probe_relocate` 11 등, AssertionError 42·FileNotFoundError 12).
     즉 `vss` 씨앗 추가를 포함해 기존 test 판정은 바뀌지 않았다(근사 측정 -- 병합본 판정은 auditor).
   * **V5**: 기존 test에 `supply_nets` 키·`rails=` 인자를 더하는 것은 '픽스처 입력 리터럴 변경'으로 잡힐 수 있다 -- 기준 약화가 아니라 선언 추가이므로, `weakening_diff.py`가 표시하면
     오케스트레이터가 `target_kind: diff` 승인 기록(사유: 선언 추가, 기대값·비교 불변)을 받는다. 계약 test(`tests/contracts/`) 중 바뀌는 이름·파일을 참조하는 것은 없다(2 참조).
   * 판정 경로 밖(U-02 3항과 같은 취급): `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py`·`stick.py`·`probe_group_split_wiring.py`가 깨진다.
