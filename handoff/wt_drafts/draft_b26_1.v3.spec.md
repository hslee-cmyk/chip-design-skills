---
id: 20260930-b26-rail-accessor-set
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260930-b26-before-phase3
---
## 의도

계획 DF-19·DF-26(담당 Phase 4)의 **넷 몫 첫 card(B26-1)**. 엔진은 지금 topology 최상위 `supply_nets`를 한 곳도 읽지 않고(운영 코드의 `supply_nets` 참조는 SR 4361 하나이며
그것은 metric 선언 안의 같은 이름 키다) 레일을 넷 이름 집합으로 정한다 -- SD `_RAIL_NETS = {"vdd","gnd","vss"}`, SR `_DEFAULT_RAIL_HI/LO`(대소문자 6개), SR `_metric_kcl_residual`
인라인 튜플(6개), SR `_build_theta_evaluator` 인라인(3개), SD `_propose_*` 씨앗(`vdd`·`gnd` 2개). 이 card는 **레일 선언을 읽는 정본 접근자 하나**를 만들고, **"이 넷이 레일인가"만 묻는
집합 판정 사이트**를 그 접근자가 준 선언으로 바꾼다. A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 cd64170.

앞당김: 이 card는 Phase 4 DF를 Phase 2 진행 중에 한다. 머리의 `approval: 20260930-b26-before-phase3`은 **사용자가 승인한 결정 A2**의 승인 기록(`target_kind: decision`)이다 --
(1) DEC-60 넷 전환기 종료 (2) DF-19·DF-26 넷 몫을 MG1에서 분리 (3) B26-1과 B34를 Phase 3 전에 착수. 사용자 원문 "승인 (Recommended)"(2026-10-01, `_drafts/user_decisions.md` A2.
질문 범위는 `_drafts/draft_b26_u2_approval_question.md`). 같은 기록을 B34 card(`20260930-b34-grammar-explicit`)도 가리킨다. **그 승인 기록이 gate에 커밋되기 전에는 이 card를 커밋하지
않는다**(merge gate 로더 규칙 6이 목록의 승인 기록 파일이 있는지 검사한다. HEAD `7535799`에는 아직 없다). 옛 머리의 `approval: 20260923-20-dead-code-dup-design`은 design 20(P 목록)의 승인이라 B26을 덮지 않아
뺐다(review_b26_1 S3). 계획 정정(`_drafts/draft_b26_plan_patch.md`)은 이 승인 기록과 함께 커밋하며, 이 card의 착수 조건이다.
**순서: P9 → B34 → B26-1. base = P9(`20260930-p9-kcl-edges`, `kcl_series_union` 본문의 엣지 정의를 `_kcl_and_matching_edges` 호출로 합침)와 B34(`20260930-b34-grammar-explicit`, analog-grammar
부재 시 `_import_analog_grammar`가 `ImportError`)를 병합한 뒤의 master**. P9가 SD 3042 판정을 없애므로 이 card에서 `kcl_series_union`은 `rails`를 받아 `_kcl_and_matching_edges`로
넘기기만 하는 함수가 된다. B34가 먼저 병합되어야 아래 '인계 삭제' 분기가 도달 불가가 된다(B34 앞에서 지우면 부재 시 동작이 바뀐다). B34·P9가 SD 줄을 옮기므로 착수할 때 줄 번호를 다시 잰다
(모의 base에서 B34 코드 변경만으로 1073 이후 사이트가 4줄 당겨진다. 예: 1575 → 1571. B34의 docstring 수정분은 따로 더해진다).

**B34에서 인계받은 삭제(B34 card '범위' 3·결정 3, `_drafts/b34_revision_log.md`)**: B34 병합 뒤에는 analog-grammar가 없으면 `_import_analog_grammar`가 먼저 `ImportError`를 낸다. 그래서
`refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill` 안의 부재 분기는 도달할 수 없다. 이 card는 두 def의 본문을 어차피 바꾸므로(`rails` 인자) 여기서 지운다.
두 def는 이미 V3 대상이라 추가되는 대상 def는 중첩 def 하나뿐이다('V3 계획' 1). 백로그 **B40**(`propose_device_roles_gap_fill`이 analog-grammar가 있어도 gate 소자 없는 입력에
"analog-grammar를 import할 수 없어…"라는 틀린 사유를 싣는 문제)도 같은 분기를 정리하면서 닫는다. 줄 번호는 gate `master` `7535799`(B34·P9 병합 전 HEAD. `sed -n`으로 재측정, B34 card 표와 일치):

| # | 함수 | 줄(7535799) | 바꾸는 것 |
|---|---|---|---|
| 9 | `refine_differential_and_mirror_relations` 내부 `classify` | 2400~2401 `if netclass is None: return None, None` | 삭제 |
| 9 | 같은 함수 | 2410~2411 `if cls_before is None: return None` | 삭제(`classify`가 늘 dict를 돌려주므로 도달 불가) |
| 10b | 같은 함수 | 2440~2441 `if relations is None: return None` | 삭제(같은 입력이 gate 소자 없음이면 2420 `candidates is None`에서 먼저 반환. `find_verified_…`의 `None`은 부재나 gate 소자 없음에서만 나온다) |
| 10 | 같은 함수 | 2494 `_netclass_al, _idioms_al = …`는 남기고, 2495 `if _netclass_al is not None:` 삭제 | 블록 2496~2523을 한 단계 내어쓰기(무조건 실행) |
| 13 | `propose_device_roles_gap_fill` | 4071~4073 `_static_ref_roles = (…) if _netclass_lcmf is not None else ()` | 조건 없이 4원소 튜플 |
| 14 | 같은 함수 | 4087 `if _idioms_lcmf is not None:`, 블록 4088~4109, `else:` 4110, 4111 `cascoded_active_load_legs = set()` | `if`·`else`·4111 삭제, 블록 내어쓰기 |
| B40 | 같은 함수 | 3966~3970 `if refined is None: return {…, "unavailable_reason": "analog-grammar를 import할 수 없어…"}` | 분기는 **남긴다**(gate 소자 없는 입력에서 `refined is None`은 여전히 참). 반환 dict에서 `unavailable_reason` 키만 지운다(소비처 0 -- `git grep` 7535799 `skills workspaces tools docs/01-plan docs/02-design`: SD 정의 줄 외 0) |

docstring(AST 해시 불변): `propose_device_roles_gap_fill` 3932~3933과 `refine_…` 2349~2350에서 B34가 고친 "도달 불가 -- 삭제는 B26-1" 구절을 지운다. 남는 서술은 "gate 소자가 없으면 빈 제안"
(`refine_…`은 "`None`")이다. 바꾸지 않는 것: `refine_…` 2420 `if candidates is None: return None`(gate 소자 없음 경로, B34 계약 5가 고정).

**원칙을 계약으로(전 범위)**:
1. **topology 무관**: 새 접근자와 바꾸는 사이트 전부에 넷·소자·회로 이름 리터럴이 없다. 레일 여부는 선언 `supply_nets`의 원소인가로만 정한다(대소문자 변환·접두어 규칙 없음).
2. **조용한 폴백 금지**: `supply_nets`가 없으면 `ValueError`로 거부한다. 이름 집합으로 대신 판정하는 경로를 두지 않는다(DEC-60 넷 전환기 종료 -- 계획 정정, U2). 레일 인자는 **기본값 없는
   키워드 전용 인자**다(기본값을 이름 집합이나 `None`→이름 집합으로 두면 원칙 위반이 되살아난다).
3. **재계산 금지(NFR-2)**: 새 캐시를 만들지 않는다. `load_topology` 한 번에 진입 파일 선언을 한 번 읽어 `meta["rails"]`에 싣고, SR은 이미 `load_topology`의 `meta`를 보관하는
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
  (`propagate_node_voltages`, B26-2)을 지나야 하므로 **B26-2로 옮긴다**(같은 평가 경로의 극성 사이트와 한 card에서 합성 평가 test로 판정). 이것은 **판정할 수 있는 test가 없어서**
  옮기는 것이지 V3 대상을 줄이려는 것이 아니다 -- `_build_theta_evaluator`는 `kcl_series_union`·`resolve_stack_layout`에 `rails=`를 넘기므로 8003을 옮겨도 본문 전체가 이 card의 V3
  대상이다('V3 계획' 절, review_b26_1 B1).
* SR 3950 `node_pole_estimate`(운영 미도달, 레지스트리 §7 '삭제 후보, 보류(Phase 4)'), SD 3559·3561·3719 `propose_theta_kcl_gap_fill`(운영 호출 0, '배선 승인 필요, 보류(Phase 3)'):
  운영 경로에서 불리지 않는 함수에 레일 인자를 더하지 않는다(배선 원칙). 삭제·배선 결정과 함께 B26-4 lint가 처리한다.
* `skills/analog-grammar/assets/netclass.py`·`idioms.py`의 이름 집합 `RAILS`·`RAILS_POS`·`RAILS_NEG`: SD 운영 함수(직접 import 7, `find_stack_edges` 경유 `geometry_colocation_union`까지 8)가
  `_import_analog_grammar`로 부른다. **대부분 집합 소속 판정이다**(`RAILS` 소속: netclass 80·82·134·137·140·226·269·270·314·321·342, idioms 264·373·529·572·599·714. 극성은 netclass
  102·103 `SUPPLY/GROUND` 분류와 idioms 600·601뿐 -- review_b26_1 S2 실측). 이 card에서 빼는 이유는 극성이 아니라 둘이다: (1) 쓰기 경로 -- N3.12.2 표에 `skills/analog-grammar/**` 행이
  어느 주체에게도 없다(게이트 공백, 백로그 B36). (2) 대체 방식이 극성 선언(D1)과 게이트 범위 편입을 먼저 요구한다. 처리는 **B35**(`_drafts/prep_b34_b35_grammar.md` §3.2 권고 (1):
  analog-grammar 진입 함수 `classify_nets`·`stack_edges`에 기본값 없는 `rails` 인자, SD는 이 card의 `meta["rails"]`를 넘김. 착수 조건 = B36 게이트 변경 card + B26-2). review_b26_1 S2가
  권고한 **호출부 어댑터(이름 바꿔 넘기고 역치환)는 채택하지 않는다** -- prep §3.2 (2)의 다섯 결함(극성별 이름 원소 5개 상한이 topology 의존, 극성 필요, 넷 이름 키 출력 전부 역변환,
  SD가 이름 집합을 인코딩 통로로 참조해 B26-4 lint 취지를 우회, analog-grammar 자체는 여전히 이름 기반). 참고: netclass `HINT_*` 정규식(입력·바이어스 이름 힌트)도 이름 기반이지만
  레일과 다른 개념이다 -- B26-4 lint 범위에서 레일 이름 리터럴과 섞지 않는다.

## 관찰 가능한 계약

1. **접근자** `stick_diagram.rail_declaration(topology)`: 인자는 topology JSON 한 파일을 읽은 dict. 반환 `RailDeclaration(nets=frozenset(topology["supply_nets"]))`(frozen dataclass,
   필드 `nets` 하나 -- B26-2가 극성 필드를 더한다). 거부(`ValueError`, 메시지에 `supply_nets`와 DEC-60을 적는다): 키 없음 / 값이 list가 아님 / 원소가 빈 문자열이거나 str이 아님 /
   같은 원소 중복. **빈 list `[]`는 받는다**(레일 없음이라는 명시 선언 -- 조용한 기본값이 아니다). 선언 밖 넷 이름은 보지 않는다(`"vdd"`라는 넷이 있어도 선언에 없으면 레일이 아니다).
   docstring에 '검사하지 않는 것:' 절을 둔다: 선언 넷이 netlist·수동소자·이상원 단자에 실제로 있는가, 숨은 레일 후보(DEC-60 (iii)), 극성 -- 이것들은 GB0(6a)·B26-2 몫.
2. **`load_topology(json_path)`**: 진입 파일 dict로 `rail_declaration`을 **정확히 한 번** 부르고 결과를 `meta["rails"]`에 싣는다. `supply_nets`가 없으면 다른 분석 전에 `ValueError`.
   `linked_topology_files`의 파일이 `supply_nets`를 선언하면 그 선언도 **같은 형식 검사**(계약 1의 거부 규칙과 같은 `ValueError`)를 거치고, 그 집합이 진입 파일과 다르면 `ValueError`(어느
   쪽을 고를지 추측하지 않는다). 연결 파일에 선언이 없으면 진입 파일 선언을 쓴다(`test_ic3` 5-a 입력이 이 형태다). `meta`의 다른 키와 `transistors`는 base와 같다(계약 8).
3. **캐시(NFR-2)**: `_load_full_topology_cached`·`_topology_meta_cached`에 새 캐시·새 엔트리 필드를 만들지 않는다. SR 소비처는 `_topology_meta_cached(path)["rails"]`(이미 보관된 meta)나
   이미 손에 든 `meta["rails"]`를 쓴다. **불변식**: `stick_diagram.rail_declaration` 호출 수 = `load_topology` 호출 수 + (그 호출들에서 `supply_nets`를 선언한 연결 파일 수). 연결 파일이
   없는 topology에서는 `load_topology` 호출 수와 같다. **관찰**: 새 tmp 경로의 topology마다(모듈 수준 캐시가 test 사이에 남으므로 test마다 새 경로) 첫 평가(`compute_metric`(kcl_residual)
   1회 -- 이때 `_load_full_topology_cached`가 캐시를 못 찾아 `load_topology`를 한 번 부르는 것은 기존 구조다) 뒤, 같은 경로로 `compute_metric`(kcl_residual)을 N회·`l_sharing_classes`를
   N회 불러도 `rail_declaration` 호출 수가 늘지 않는다(review_b26_1 S1 실측: 계약대로 구현한 사본에서 `load_topology` 1회 → 1, 첫 `compute_metric` → 2, 그 뒤 추가 호출 0).
   계수 래퍼는 test가 `stick_diagram.rail_declaration`을 바꿔 센다. 그래서 **SR은 `rail_declaration`을 `from stick_diagram import`로 가져오지 않는다**(가져오면 SR 쪽 별칭 호출을 셀 수 없다 --
   SR은 선언을 `meta["rails"]`로만 받는다). 캐시 키가 경로 문자열인 것은 기존 결함이고(S0 지문 = 6a) 이 card는 같은 엔트리를 재사용만 한다.
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
6. **`_metric_kcl_residual`**(`compute_metric({"type": "kcl_residual", …}, ctx)`와 이름 직접 호출 `sizing_recipe._metric_kcl_residual(spec, ctx)` 둘 다 -- 시그니처 불변): 잔차에서 빼는 레일 =
   `ctx.topology_path`의 선언 레일. 선언에 metric 키 `rail_nets`가 있으면 **지금** `ValueError`(레일은 topology `supply_nets`로만 선언한다. 조용히 무시하면 폴백이다). 그 밖의 옛 키
   (`supplies`, 스칼라 `vdd`, metric `supply_nets`) 거부 게이트는 MG1(계획 정정 N3.16). library 선언의 `rail_nets` 사용 0건(실측). 본문의 다른 가지는 바꾸지 않는다: MOS `ID` 부호
   (NMOS drain→source, PMOS source→drain, 노드로 들어오는 전류 +), `ID` 없는 소자 → `KeyError`, `ideal_sources` 중 `kind != "current_source"`·단자 2개 미만은 건너뜀, `value_amp`가
   `null`이면 그 단자 노드를 잔차에서 뺌, 값이 있으면 `terminals[0] → terminals[1]`로 흘려 셈, `exclude_nets` 노드 제외, 반환 = 남은 노드 |합|의 최댓값(없으면 0.0).
7. **행동(합성 topology, 라이브러리에 없는 넷 이름)** -- 관찰 대상은 **B26-1 사이트만으로 정해지는 값**으로 한정한다. 레일을 `rail_hi`·`rail_lo`처럼 library에 없는 이름으로 선언한
   topology에서:
   (a) 같은 kind 두 소자가 선언 레일을 source로 공유해도 `find_matching_candidates`의 `diff_pair`·층위1 폴백 후보가 아니고, `load_topology` meta `_matching_pairs_autofilled`에 그 쌍이
   없다(주의: `find_differential_pair_candidates`의 후보는 `trace_*`에서 오고 그 진입은 아직 이름 `"vdd"`/`"gnd"`다(B26-2). 이 항목은 **층위1 폴백 후보**에 대한 것이지 차동 후보 전반에 대한
   것이 아니다);
   (b) `_kcl_and_matching_edges`·`kcl_series_union`이 선언 레일을 통해 소자를 잇지 않고, 그래서 `load_topology` meta `_vertical_stack_id_autofilled`에서 선언 레일만을 통해 이어진 소자가
   다른 소자의 선언 `vertical_stack_id`를 자동으로 받지 않는다;
   (c) 게이트가 선언 레일에 물린 소자는 `l_sharing_classes`의 미러 동치류를 만들지 않는다;
   (d) kcl_residual이 선언 레일 노드를 잔차에서 뺀다.
   **역방향**: 선언에 없는 넷이 `vdd`·`gnd`·`vss`라는 이름이어도 위 관찰 대상 -- meta `_matching_pairs_autofilled`, meta `_vertical_stack_id_autofilled`, `l_sharing_classes`,
   kcl_residual, 직접 호출한 `find_matching_candidates`·`_kcl_and_matching_edges`·`kcl_series_union` -- 에서 레일로 취급되지 않는다(보통 내부 노드와 같은 결과).
   **계약이 아닌 것(test 기대값으로 쓰지 않는다)**: `device_roles`·`_device_roles_autofilled`의 `headroom_role`, `_device_roles_gap_fill_review_needed`, analog-grammar(`netclass`·`idioms`) 유래
   필드, 역할 자동 채움(`L_role`·`gm_id_role`)의 `null` 여부, 그리고 **`load_topology` meta 전체의 넷 이름 불변**. 이것들은 병합본에서도 analog-grammar `netclass.RAILS`(대소문자 무관 이름
   집합)와 B26-2 사이트 때문에 이름에 기댄다(review_b26_1 B2 실측: 선언 `[rail_hi, rail_lo]` 5소자 회로의 내부 노드 이름만 바꾼 7변형이 base·병합 상당 모두 7/7 다름 -- 달라지는 키는
   `headroom_role`). B35·B26-2 몫이다.
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
12. **test 입력 갱신 규칙(test-author -- 판정 기준·기대값은 바꾸지 않는다)**:
    * 새 키워드 인자를 받게 되는 함수를 직접 부르는 기존 test 호출에는 `rails=`를 더한다. `rails` 값은 그 test가 쓰는 topology의 `supply_nets`로 만든 선언이다(test는 `RailDeclaration`을
      `stick_diagram.rail_declaration(<그 topology dict>)`로 얻는다 -- 직접 생성하지 않는다). `tests/probes/`의 4파일은 이미 `load_topology`의 `meta`를 들고 있으므로 `rails=meta["rails"]`.
      `engine_dup_scan` 면제 키는 `path::rule`이라 줄이 바뀌어도 무관하다. `tests/contracts/test_probe_dup_scan.py` 213행의 `sr.true_current_mirror_groups(by)`는 스캔 입력 **문자열**이지
      호출이 아니므로 고치지 않는다.
    * `supply_nets` 없이 topology를 만들어 **로드 경로**(`load_topology`·`optimize_full_circuit_budget` 등)에 넣는 기존 픽스처에는 선언을 더한다: 그 픽스처가 쓰는 넷 중 base가 레일로 읽던
      이름(`vdd`·`gnd`·`vss`)을 선언하고, 레일 넷이 없으면 `[]`. 이러면 기존 판정이 바뀌지 않는다(review_b26_1 §1 `b26f` 실측: 두 selftest 파일 base 196 passed·3 xfailed = 픽스처 규칙
      근사 사본 196 passed·3 xfailed, 실패 집합 같음). **메시지 내용을 단언하는 픽스처**(`_COMPENSATION_REGISTRY`, 그룹 이름, 인자 지목 -- s003·s043·s125)는 선언이 없으면 `supply_nets`
      거부가 먼저 나서 다른 메시지가 되므로 반드시 선언을 더한다.
    * B34 계약 test(`A/tests/contracts/test_b34_grammar_explicit.py`, B34 병합본)가 이 card에서 `rails`를 받게 되는 함수를 직접 부른다: `refine_differential_and_mirror_relations`(B34 계약 1·5),
      `find_differential_pair_candidates`·`propose_device_roles_gap_fill`·`propose_vertical_stack_id_gap_fill`(B34 계약 1). 위 규칙대로 `rails=`를 더한다. 부재 test에서는 선언을 부재를 만들기
      **전에** 얻는다(`rail_declaration`은 analog-grammar를 쓰지 않지만, `load_topology`는 부재에서 `ImportError`를 낸다). 판정·기대값은 그대로 둔다.
    * 병합본에서 기존 기대값과 다르게 나오면 기대값을 고치지 않고 dispute로 올린다(작성자≠검증자). 특히 `_propose_*` 씨앗에 `vss`가 들어가므로 `vss` 픽스처를 주의한다.
13. **인계 삭제 -- 조용한 폴백 값이 나오는 경로 없음(B34 병합 뒤)**: analog-grammar 부재(`monkeypatch.setitem(sys.modules, "netclass", None)`·`"idioms"`. B34 계약과 같은 흉내 방식)에서
    `refine_differential_and_mirror_relations(ts, rails=…)`와 `propose_device_roles_gap_fill(ts, {}, [], rails=…)`는 library 9회로 전부 `ImportError`를 낸다(`__cause__`가 `ImportError`).
    옛 폴백 값(`None`, 빈 제안 dict)을 반환하는 경로가 없다. 이 동작은 B34 병합 뒤 base에서도 성립한다(green, 회귀 고정). 인계 분기를 지운 것이 부재 시 동작을 바꾸지 않았다는 증거다.
    analog-grammar가 있을 때는 지운 분기가 동작을 바꾸지 않는다. 계약 8(E-LIB 9/9)과 함께, `refine_…`·`propose_device_roles_gap_fill`(`device_roles` = 그 topology 선언, `matching_pairs_meta` = `[]`)의 반환이
    9/9 base와 같다(auditor 대조, 같은 `PYTHONHASHSEED`. 모의 실측 9/9 같음 -- '재현할 수치').
    **auditor AST 측정(영구 test 아님)**: 병합본의 두 def(중첩 `classify` 포함)에서 `_import_analog_grammar` 반환을 받은 이름을 `None`과 비교하는 식이 0개다(모의 head 0, 모의 base 4 = 사이트 9 `netclass is None`·10·13·14). 사이트 9 둘째 줄(`cls_before is None`)과 10b(`relations is None`)는 모듈 이름 비교가 아니므로
    이 측정에 잡히지 않는다. 그래서 auditor는 diff로 그 두 `if`가 지워졌는지도 확인한다.
14. **B40 -- gate 소자 없는 입력의 반환(analog-grammar 있음)**: `fx = [Transistor("Ma", "pmos", source="vdd", drain="n1"), Transistor("Mb", "nmos", source="gnd", drain="n1")]`(gate 없음, B34 계약 5와 같은
    입력), `rails` = `rail_declaration({"supply_nets": ["vdd", "gnd"]})`일 때 `propose_device_roles_gap_fill(fx, {}, [], rails=rails) == {"matching_pairs_proposals": [], "device_roles_proposals": {}, "review_needed": []}`이다.
    키는 정확히 셋이고 `unavailable_reason` 키가 없다. `refine_differential_and_mirror_relations(fx, rails=rails) is None`은 그대로다(B34 계약 5와 같다).
    * oracle (b)의 setup 불변 test는 `_build_theta_evaluator(<사본 경로>, <canonical spec>)`의 **setup 반환 키 `stack_groups_kcl`·`stack_groups_geometry`만** 비교하고 반환된 `evaluate`는
      **부르지 않는다**(평가는 B26-2·B26-3 사이트를 지난다). 원본 경로와 이름 바꾼 경로의 두 호출은 인자 정규형이 다르므로 V4 `test_lint.py` (1)에 걸리지 않고, 이 비교의 독립성 판단은
      auditor `checks.V4.basis`로 간다(review_b26_1 M4).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|
| `stick_diagram` | `RailDeclaration` | `@dataclass(frozen=True) class RailDeclaration: nets: frozenset` |
| `stick_diagram` | `rail_declaration` | `def rail_declaration(topology: dict) -> RailDeclaration:` |

## 판정 유형 근거

red-green. base에서 실패(assertion)하는 입력 -- **계약 항목별 진입점**(모두 시그니처가 안 바뀌어 base에서도 호출된다. review_b26_1 S4 실측: base assertion 실패 → 병합 상당 통과):

| 계약 | 진입점 | 입력 | base → 병합 상당(review 실측) |
|---|---|---|---|
| 7(a) | `load_topology` meta `_matching_pairs_autofilled` | 합성 4소자(아래 '재현할 수치') | `[Qa,Qb offset layer1]` → `None` |
| 7(b) | `load_topology` meta `_vertical_stack_id_autofilled` | 합성 4소자 + `device_roles.Qa.vertical_stack_id = "S1"` | `{Pa,Pb,Qb: S1}` → `{Pa: S1}` |
| 7(c) | `sizing_recipe.l_sharing_classes` | 게이트가 `rail_hi`인 NMOS 둘 + 게이트 `bp`인 PMOS 둘 | `{Ma,Mb},{Pc,Pd}` → `{Pc,Pd}` |
| 7(d) | `compute_metric`(kcl_residual)·`sizing_recipe._metric_kcl_residual` | 합성 4소자 `ID` 1·2·1·2.5 µA | 3.5e-6 → 5.0e-7 |
| 2 | `load_topology` | `supply_nets` 없음 | base 받아들임(`pytest.raises` DID NOT RAISE = `Failed`, DF-36 판정 기록이 red로 셈) |
| 6 | kcl_residual | 선언에 `rail_nets` 키 | base 5.0e-7(키를 읽음) → `ValueError` |

7(b)는 위 `vertical_stack_id` 입력이 없으면 red가 oracle (b)(library `two_stage_ota`)뿐이다. 그 밖에 setup 수준 레일 이름 바꾸기 불변(oracle (b)). 신규 심볼(`rail_declaration`,
`RailDeclaration`)은 base에서 `ImportError`/`AttributeError`로 red 수집 플러그인의 신규 심볼 판정에 걸린다. 표의 병합 상당 값은 기대값의 **출처가 아니다** -- 기대값은 oracle (a)로 손으로
정한다(표는 red가 난다는 증거일 뿐).
**주의(V2)**: 계약 4의 새 키워드 인자를 직접 넘기는 test는 base에서 `TypeError`다 -- 허용 예외 타입 밖이라 red로 세지 않는다. red 증거는 위 공개 진입점 test가 맡고, 판정 기록은
두 종류를 나눠 적는다.
**인계 삭제(계약 13·14)의 증거 종류**: 계약 13은 B34 병합 뒤 base에서도 참인 회귀 고정(green-green)이다. 지운 분기가 도달 불가이므로 red가 날 수 없다. 이 부분의 증거는 'base에서 도달
불가 → 지워도 동작 같음'이고, 계약 8·13의 9/9 대조와 계약 13의 AST 측정으로 확인한다. 계약 14(B40)는 base(P9+B34 병합본)에서 값이 다르다(`unavailable_reason` 키가 있음 -- 모의 base 실측).
하지만 `propose_device_roles_gap_fill`은 계약 4에서 `rails`를 받게 되므로 base 호출은 `TypeError`다(red로 세지 않음). 시그니처가 안 바뀌는 진입점으로는 관찰되지 않는다. 유일한 운영
호출자 `load_topology`는 반환의 `device_roles_proposals`·`matching_pairs_proposals`만 읽는다. 그래서 계약 14는 head에서 green인 계약 test로만 두고, 판정 기록에 'base `TypeError`, red 집계 밖'으로
적는다. 필요하면 auditor가 base 값 차이를 `rails` 없이 부른 base 호출로 따로 재서 basis에 적는다.

## oracle 종류와 출처

(a) 구성: 합성 topology(라이브러리에 없는 넷·소자·회로 이름, 선례 `tests/contracts/test_d_delete_telescopic.py` 185·215행 `_SYN_RAILS = ["rail_hi","rail_lo"]`, `supply_nets`
선언)에서 기대값을 손으로 적는다 -- 어느 쌍이 차동 층위1 후보인지, 어느 소자가 KCL로 이어지는지, KCL 잔차를 손으로 계산(계약 6의 가지 각각: 부호, 이상전원 값 있음/`null`, `exclude_nets`,
최댓값). (b) 변환 불변(IC11 `test_rail_origin_shift_invariance`와 같은 종류): library 사이징 대상 topology의 레일 넷 이름만 바꾼 사본(tmp)에서 `_build_theta_evaluator(사본, canonical_spec)`의
**setup 반환값** `stack_groups_kcl`·`stack_groups_geometry`가 이름을 되돌리면 원본과 같다(evaluate는 부르지 않는다 -- 평가는 B26-2·B26-3 사이트를 지나 아직 불변이 아니다).
scratch 실측: 병합 상당 사본 4/4 같음, base는 `two_stage_ota`에서 다름(red).
**`load_topology` meta 전체의 이름 바꾸기 불변은 이 card의 계약이 아니다**(계약 7 '계약이 아닌 것'): 병합 상당 사본에서도 `_device_roles_gap_fill_review_needed`(4회로)와 `two_stage_ota`
`device_roles`가 달라진다 -- analog-grammar `RAILS`와 B26-2 사이트가 남아 있기 때문이다(실측: analog-grammar 집합을 바꾼 이름으로 맞추면 `two_stage_ota`는 같아지고 나머지 3회로
`review_needed`는 여전히 다르다).
(c) 동작 보존 = base 실행 결과(E-LIB·E-INST, auditor).

## 거부해야 할 입력

analog-grammar 부재 → `refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill` `ImportError`(계약 13. 옛 폴백 값 `None`·빈 제안 dict 반환 금지).
`supply_nets` 없음 / list 아님 / 빈 문자열·비문자열 원소 / 중복 원소 → `rail_declaration`·`load_topology` `ValueError`. 연결 파일의 `supply_nets`가 같은 규칙을 어기거나 진입 파일과
다른 집합 → `load_topology` `ValueError`. `meta`에 `"rails"` 없음 → `l_sharing_classes` `ValueError`. kcl_residual 선언의 `rail_nets` 키 → `ValueError`. 판정기 자기 점검: 거부 test는
**조용한 통과(기본값 대입)** 합성 구현을 넣으면 실패해야 한다(`test_d_delete_telescopic`의 `test_rejection_check_fails_on_silent_or_unlisted_refusal`과 같은 형태).

## library 회로 적용 여부

library 9회로 전부 `supply_nets` 선언(`_TEMPLATE` 제외 -- 작성 틀이다). 계약 8(E-LIB 9/9, 감사 9/9, E-INST 2)과 oracle (b)(사이징 대상 4회로)에 쓴다. `agnd`(두 pushpull 회로)는
커패시터 단자에만 나와 이 card의 트랜지스터 단자 판정 결과를 바꾸지 않는다.
`_TEMPLATE.topology.json`: base에서 `load_topology`가 `AttributeError: 'str' object has no attribute 'items'`로 못 읽고, 병합본에서는 `ValueError(supply_nets)`로 예외 종류가 바뀐다. E-LIB
대상 밖이라 판정 영향은 없다. 다만 이제 필수인 `supply_nets`가 작성 틀에 없다 -- 틀에 필드를 더하는 것은 오케스트레이터 몫이고 `library/*.topology.json` 변경이라 승인 기록 조건이다.
**백로그로 올린다**(이 card 범위 밖, review_b26_1 M2).

## 무동작 판정 입력(무발동 값)

library 9회로 전부: 선언 레일 ∩ 트랜지스터 단자 넷 = 옛 이름 집합 ∩ 트랜지스터 단자 넷이라 바꾼 사이트의 판정이 base와 같다(scratch 실측 -- '재현할 수치'). `_propose_*` 씨앗은 base가
`vdd`·`gnd`뿐이라 vss 회로 3개(`nmcnr_amplifier`, `pushpull_follower_buffer`, `sf_pushpull_output_opamp`)에서 씨앗이 하나 늘지만 `load_topology` 결과는 9/9 같다.

## 재현할 수치

scratch(C:/g23, cd64170 사본 두 벌 -- 원본 / B26-1 사이트만 선언 레일로 바꾼 사본; review_b26_1은 C:/g32에서 재현):
* `load_topology` 9/9 같음(`transistors`·`meta` 전체, float는 `float.hex`), `run_full_circuit_audit_from_topology` 9/9 같음(2회로 결과 동일, 7회로 같은 `ValueError`
  `_netlist_sections_structured`가 없다 -- 경로 문자열만 사본 위치 차이).
* 사이징 대상 4회로 `_build_theta_evaluator` + `_theta_point` 평가: `current_reuse_telescopic_ota`(metric 19, sized 51)·`folded_cascode`(metric 5, sized 13) 같음,
  `two_stage_ota`('stage1_ref' 헤드룸)·`nmcnr_amplifier`('stage2_diode_ref', 0.525 V) 같은 `InfeasibleSizingError`.
* 합성 4소자(NMOS `Qa`·`Qb` source `rail_lo`, 게이트 다름 / PMOS `Pa`·`Pb` source `rail_hi`, 게이트 `bias_p`, `supply_nets = [rail_hi, rail_lo]`): base `find_matching_candidates`
  `diff_pair = {(nmos, rail_lo): [Qa, Qb]}` → 병합 상당 `{}`; `_kcl_and_matching_edges` base 4엣지(`rail_lo`·`rail_hi` 경유 2개 포함) → 2엣지; `kcl_series_union` base 1그룹
  `{Qa: [Qa, Qb, Pa, Pb]}` → 2그룹; `load_topology` meta base `_matching_pairs_autofilled = [{names: [Qa, Qb], matching_sensitivity: offset, source=layer1_diff_pair_fallback}]` → 병합 상당 `None`.
  **계약 아님(관찰값)**: base의 네 소자 `L_role: mirror`·`gm_id_role: matching` 자동 채움이 병합 상당에서 `null`이 되고 `headroom_role`만 남는 것. `Pa`·`Pb`(같은 게이트 `bias_p`, 같은 소스
  레일)는 실제 전류미러이므로 `null`은 물리로 정한 값이 아니고, `headroom_role`(`cascode`)은 netclass 유래라 틀린 값이다. test 기대값으로 고정하지 않는다.
* oracle (b) setup 불변: base `two_stage_ota` 다름 / 나머지 3 같음, 병합 상당 4/4 같음.
* 계약 3 호출 수: `load_topology` 1회 → `rail_declaration` 누적 1, 첫 `compute_metric`(kcl_residual) → 2, 그 뒤 `compute_metric` 3회·`l_sharing_classes` 3회 → 2(review_b26_1 S1).
* 계약 13·14(2026-10-01, scratch C:/g59. 모의 base `b1` = `7535799` + P9 + B34 코드 변경, 모의 head = `b1` + B26-1 상당(rails) + 인계 삭제. 두 사본 모두 `PYTHONHASHSEED=1`):
  library 9/9에서 `load_topology`(meta는 `rails` 제외, `transistors`), `refine_…(ts)`, `propose_device_roles_gap_fill(ts, <선언 device_roles 또는 {}>, [])`의 정규화 해시가 base와 같다.
  `fx`(gate 없음): `refine_…` 둘 다 `None`. `propose_device_roles_gap_fill`는 base가 `{…3키…, 'unavailable_reason': 'analog-grammar를 import할 수 없어…'}`, head가 3키 dict다.
  부재(`sys.modules` 두 이름 `None`): 두 함수 모두 base·head `ImportError`(`__cause__` `ModuleNotFoundError`).

## V3 계획

**사용자 결정 U1 대기**(아래 3의 권고). 결정 전에는 착수하지 않는다(착수 조건 5).

1. **대상(재측정 2026-10-01, B34 → B26-1 순서)**. `tools/gates/mutate_changed.py`의 `changed_defs`·`mutants`·`inventory`와 `reachability.build_graph`·`_approved_ids`만 읽기 전용으로
   import했다(도구 `main`은 돌리지 않음). scratch C:/g59(gate `master` `7535799`의 `git archive`)에서 모의 사본 두 벌을 만들었다.
   * **모의 base `b1`** = `7535799` + P9(`kcl_series_union` 본문을 `_kcl_and_matching_edges` 호출로) + B34 코드 변경(사이트 1·2·3·11·11b. docstring 변경은 AST 해시와 무관해 넣지 않음).
     `changed_defs(7535799+P9, b1)` = B34의 4 def(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`)로 B34 card와 같다.
   * **모의 head** = `b1` + B26-1 상당 패치(계약 4의 20함수에 키워드 전용 `rails`, 그 호출부 전부에 `rails=rails`, 뿌리 8곳에 선언 획득 문장, 사이트 교체 -- P9 뒤 SD 13줄 + SR 2줄, 새 def 2개)
     + **B34 인계 삭제**('의도' 표 9·10·10b·13·14·B40).
   * 스크립트: 옛 `_drafts/b26_v3_measure.py`(cd64170, C:/g39)의 head 생성 함수에 P9·B34·인계 삭제를 내용 기준 치환으로 더했다. 사이트 줄은 `b1`에서 다시 찾았다. 측정 뒤 C:/g59는 지웠다.
     수치는 이 절과 `_drafts/b34_revision_log.md` §6에 옮겨 적었다.
   * 도구는 **AST가 바뀐 def의 본문 전체**를 변이한다(① 대상 = def, ② 연산자는 def의 모든 노드. 중첩 def는 따로 대상이 되고, 바깥 def의 변이에도 들어간다). 결과:
     바뀌는 def **32개**(최상위 30 + 중첩 `optimize_full_circuit_budget._evaluate_row_split`·`refine_differential_and_mirror_relations.classify`), 변이 **2,438개**. 뿌리 밖 호출자는 없다(계약 4의 뿌리 =
     SD `load_topology`·`run_full_circuit_audit_from_topology`, SR `_build_theta_evaluator`·`_fixup_euler_blocked_rows`·`l_sharing_classes`·`optimize_full_circuit_budget`·
     `run_matching_safety_with_finger_growth`·`run_topology_pipeline_with_finger_fixup` + `_metric_kcl_residual`). B34의 4 def와 겹치는 def 0개.
   * 그중 **diff가 닿은 문장·식에 걸린 변이는 135개**(좁은 정의: 복합문은 머리 줄만, 조기 return은 새 def에서만. 새 def `rail_declaration` 14개 포함). 인계 삭제 없이 `rails`만 넣은 비교 head는
     def 31·변이 2,447·닿은 변이 105다. 인계 삭제가 더한 몫은 **def +1(`classify` 6변이), 변이 순 −9**(`refine_…` 95 → 84, `propose_device_roles_gap_fill` 331 → 327, `classify` +6),
     **닿은 변이 +30**이다. +30의 대부분은 사이트 10·14 블록을 내어쓴 줄이다(줄 diff 기준이라 들여쓰기만 바뀐 문장도 '닿음'으로 센다). 나머지 2,303개는 이 card가 쓰지 않은 기존 문장이다.
     (옛 측정 cd64170·P9 전: def 31·변이 2,472·닿은 변이 106. P9가 `kcl_series_union`을 49 → 24로 줄인 것이 rails만 넣은 비교 head의 −25다.)
   * def별(변이 / 닿은 변이 / 인벤토리 test 수): `_build_theta_evaluator` 498/3/60, `propose_device_roles_gap_fill` **327/24**/138, `optimize_full_circuit_budget` 230/2/60,
     `repair_matching_safety` 112/3/69, `_branch_composite_pair` 102/1/70, `run_matching_safety_with_finger_growth` 100/4/62, `_fixup_euler_blocked_rows` 90/2/62,
     `refine_differential_and_mirror_relations` **84/28**/145, `run_topology_pipeline_with_finger_fixup` 65/2/61, `find_differential_pair_candidates` 65/4/146, `load_topology` 65/9/137,
     `_evaluate_row_split` 62/1/60, `find_matching_candidates` 60/2/146, **`_metric_kcl_residual` 57/4/0**, `audit_vertical_stack_id_vs_kcl` 56/6/63, `_composite_collapse_for_crossover` 55/1/65,
     `run_full_circuit_audit` 53/1/64, `propose_vertical_stack_id_gap_fill` 48/1/140, `l_sharing_classes` 42/5/60, `check_symmetry_dispositions` 37/1/140, `_propose_L_roles` 30/3/145,
     `_kcl_and_matching_edges` 30/2/140, `resolve_stack_layout` 26/2/61, `_propose_gm_id_roles` 26/2/145, `kcl_series_union` **24/1**/70, `run_full_circuit_audit_from_topology` 23/2/63,
     `_diff_pair_layer1_groups` 22/2/146, `true_current_mirror_groups` 17/1/60, `rail_declaration`(새) 14/14/137, `_kcl_branch_map` 7/1/70, **`refine_…classify` 6/0/145**(새 대상),
     `find_min_crossover_layout_with_branch_composite` 5/1/64. (인벤토리 수는 도구의 test 노드 규칙 -- `tests/tools/` 제외, `test*` 함수 노드 -- 로 센 값이다. 모의 사본에는 B34·P9의
     새 test 파일이 없다. 그 test들이 들어오면 B34 계약 test가 직접 부르는 `refine_…`·`propose_*` 등의 인벤토리가 늘어난다.)
   * **`_metric_kcl_residual`의 인벤토리는 0이다**(`compute_metric` → `_METRICS_REGISTRY` dict 경유라 정적 그래프에 간선이 없다). 57개 전부 '인벤토리 없음 → 생존' = V3 FAIL이다. 모의
     head에 `sr._metric_kcl_residual`을 **이름으로** 부르는 test 파일 하나를 더하면 인벤토리가 1이 되고 '인벤토리 없음' 변이가 0이 된다(재측정에서도 같음).
   * 면제 누수 대조: HEAD `7535799` 트리의 decision 승인 기록 id 26개 중 모의 head 변이 id와 겹치는 것 0개.
   * 시간(cd64170 측정을 그대로 씀. 이번에는 pytest를 돌리지 않았다): scratch 사본 전체 test 1회 813건 272 s(pytest 벽시계 299 s, 796 passed·2 failed -- `.git` 없는 사본의 `test_ts6_probe_relocate` 환경 실패). def별 인벤토리 실행 시간은
     177~192 s다(느린 test 몇 개가 거의 모든 인벤토리에 든다: `test_probe_parasitic_pm_all_circuits` 55 s, `test_s157_M1_known_limitation` 43 s, `test_s157_M1` 24 s, `test_s014_section` 17 s).
     pytest 한 번 기동 4.7~7.1 s. 도구는 변이를 **직렬**로 돈다.
2. **선택지와 비용(U1)** -- 아래 수치는 cd64170 측정 기준이다. 재측정 값으로 바꾸면 (a) 실행 135개(하한 ≈ 11분), (c) 실행 2,438개(하한 ≈ 3.4시간)이고, 결론은 같다:
   * **(a) 이 card의 V3를 diff가 닿은 문장과 새 def로 좁힌다.** 실행 106개: 하한 106 × ~5 s ≈ 9분, 상한(전부 생존·인벤토리 전체 실행) ≈ 5.3시간. 나머지 2,366개는 변이 id 목록 면제
     (`target_kind: decision`, `target` = 변이 id 목록, id는 도구 `mutants()`로 최종 head에서 생성). **실측 결함**: 면제 id는 `<모듈>:<qualname>:<연산자>:<AST 경로>`이고 def 해시나 card에
     묶이지 않으며, 도구(`reachability._approved_ids`)는 head 트리의 **모든** decision 승인 기록을 읽는다. 그래서 이 목록은 뒤 card에서도 같은 경로의 변이를 조용히 면제한다 -- B26-1
     시뮬레이션 head 위에서 B34 대상 def를 변이하면 1,402개 중 **619개**의 id가 이 면제 목록에 이미 있다(B34 자신의 편집으로 경로가 밀리는 몫은 빠지므로 상한). 선례 `20260922-ic3-v3-exempt`도
     같은 구조다(범위 설명에 "본문 구조가 바뀌면 이 면제는 맞지 않는다"고 적었지만 도구는 경로만 본다). (2026-10-01 보충: 이제 B34가 먼저 병합되고 B34 범위가 4 def로 좁아져서, 위 619개 예시는
     B34에 그대로 해당하지 않는다. 같은 구조의 누수는 뒤 card(B35·B26-2 등 같은 def를 다시 바꾸는 card)에 남는다.)
   * **(b) card를 더 잘게 나눈다.** 기본값 없는 키워드 인자는 피호출자에서 뿌리까지 모든 호출자의 AST를 바꾼다. `kcl_series_union`·`resolve_stack_layout`에 `rails`를 넘기는 한
     `_build_theta_evaluator`(498)가 대상이고, `kcl_series_union`·`audit_vertical_stack_id_vs_kcl`은 로드 경로와 평가 경로에 함께 쓰여 경로별로 나눌 수 없다. 나눈 card들의 대상 합은 2,472
     이상이다(여러 card가 같은 def를 바꾸면 그 def는 매번 전부 다시 변이된다). **비용을 줄이지 못한다.**
   * **(c) 전수 실행을 받아들이고 생존 변이마다 test를 보강한다.** 실행 2,472개: 하한(전부 첫 test에서 죽음) 2,472 × ~5 s ≈ 3.4시간, 상한(전부 생존) Σ 변이 × 인벤토리 시간 ≈ 122시간(≈5.1일,
     직렬). 생존 변이 중 등가가 아닌 것은 이 card와 무관한 기존 문장(예: `_build_theta_evaluator` 1,005줄 중 닿은 변이 3개)의 test 공백이라, test-author가 레일과 무관한 기존 동작의 test를
     써야 한다. 등가 변이는 (a)와 같은 id 면제가 필요하다(같은 누수).
3. **권고**: **(a)의 판정 범위를 card별 면제 목록이 아니라 게이트 규칙으로** 한다 -- `_drafts/v3_scope_systemic.md`의 게이트 변경 card(V3 대상 = diff가 닿은 문장 + 새 def, 면제 id를 def
   해시·card에 묶음)를 먼저 병합하고 B26-1은 그 규칙으로 판정한다. 근거: (i) 이 비용은 B26-1 한 건이 아니라 이후 엔진 card 전부의 문제다(B34 1,395개 등 -- 같은 문서), (ii) card별 목록은 위
   실측처럼 뒤 card로 새는 조용한 면제라 '조용한 폴백 금지' 원칙에 어긋난다, (iii) (b)는 비용을 줄이지 못하고 (c)는 이 card 범위 밖의 기존 test 공백을 이 card에 묶는다. 게이트 규칙 변경은
   현 V3 문언 대비 판정 범위 축소(약화)이므로 사용자 승인이 필요하다(같은 문서 §3). 사용자가 게이트 변경을 받지 않으면: (c)를 기본으로 하고 등가 변이만 id 면제(누수는 승인 기록 '재검토'에
   적는다). (a)를 card별 목록으로 받는 것은 누수를 알고 받는 경우에만.
4. **어느 쪽이든 할 것**: 새 test 파일 `A/tests/contracts/test_b26_rail_accessor.py`(test-author)는 `sizing_recipe._metric_kcl_residual(spec, ctx)`를 **이름으로 직접** 부르는 test를 둔다(시그니처가
   안 바뀌어 base에서도 호출된다 -- 인벤토리 0 → 1, 실측). 기대값은 계약 6의 가지를 각각 덮게 손으로 계산한다: MOS 부호, `ID` 없음 `KeyError`, `current_source` 아닌 이상원·단자 2개 미만
   건너뜀, `value_amp` `null` 노드 제외, `value_amp` 값 흘림, `exclude_nets` 제외, 선언 레일 제외, 최댓값·빈 경우 0.0, `rail_nets` 키 `ValueError`. (계약 7(d)만으로는 레일 제외 한 가지만
   덮는다.) 이 파일 이름은 `glob(` 사용처의 패턴(`probe_*.py`, `*.topology.json` 등)과 겹치지 않는다('작성 전 실측' 2).
5. auditor는 착수 시(P9·B34 병합본 base) 도구로 대상 def·변이 수를 다시 재고, 판정 기록 `checks.V3.basis`에 택한 선택지와 면제 승인 id를 적는다.
6. **인계 삭제의 V3 몫**: 두 def(`refine_…`·`propose_device_roles_gap_fill`)는 `rails` 때문에 이미 전체가 대상이다. 그래서 인계 삭제가 더하는 대상 def는 중첩 `classify` 하나(6변이, 인벤토리 145)뿐이고,
   변이 수는 순 −9다('V3 계획' 1). 지운 분기(부재 비교·`unavailable_reason` 키)의 변이는 head에 없으므로 면제할 것도 없다. 내어쓴 블록(사이트 10·14)의 변이 id는 AST 경로가 바뀐다(`body[k].body[i]` →
   `body[k']`). base 생존 목록과 대응시키는 판정을 쓰지 않는 한 영향이 없다. U1의 어느 선택지에서도 이 몫 때문에 승인을 늘릴 필요가 없다.

## 결정 필요 항목

* **U1(사용자 결정, 대기)**: V3 처리 -- 'V3 계획' 2의 (a)/(b)/(c). 권고는 'V3 계획' 3(게이트 규칙으로 한 (a)). 사용자에게 아직 묻지 않았다(`_drafts/user_decisions.md` "아직 묻지 않음: A1 V3 범위 정책" --
  `draft_v3_decision_question.md`, `draft_v3_exempt_binding.spec.md`).
* **U2 → 승인됨(A2, 2026-10-01)**: DEC-60 넷 전환기 종료 + DF-19·DF-26 넷 몫을 MG1에서 분리 + B26-1·B34를 Phase 3 전(Phase 2 진행 중)에 착수. 한 건의 `target_kind: decision` 승인 기록
  `20260930-b26-before-phase3`(머리 `approval` 줄)이 B26-1·B34를 함께 덮는다. 사용자 원문 "승인 (Recommended)". 질문 범위 = `_drafts/draft_b26_u2_approval_question.md`. 기록 파일은 오케스트레이터가
  계획 정정 커밋과 함께 gate에 올린다(아직 없음). 이 card는 V7 면제가 필요 없다. V3 면제가 필요한지는 U1에 달렸고, A2 기록의 `target`에는 변이 id가 없다. D1 극성·D2 MNA는 이 card 밖이다(B26-2·B26-3 착수 조건).

착수 조건:
1. A2 승인 기록 `20260930-b26-before-phase3`이 gate에 있다.
2. 계획 정정 커밋(`draft_b26_plan_patch.md` -- A2 기록과 함께).
3. P9 병합.
4. **B34 병합**(`20260930-b34-grammar-explicit`. 인계 삭제 분기가 도달 불가가 되는 조건. 순서 B34 → B26-1).
5. U1 결정. 권고안이면 `v3_scope_systemic.md`의 게이트 변경 card 병합이 먼저다.

## 작성 전 실측

(cd64170, 2026-09-30. 저장소·worktree 쓰기 없음. scratch C:/g23 -- `git archive cd64170 skills/analog-gmid-design/assets skills/analog-grammar workspaces/run_harness.py tools/gates docs/01-plan`
두 벌. 끝나면 C:/g23 삭제. V3 측정은 C:/g39 -- 'V3 계획' 1.)

1. **사실 재측정 -- B26-1 행**: AST 스캔(`prep` §1 규칙 그대로 다시 구현, docstring 제외) 113행 중 이 card가 바꾸는 행:
   SD 1014 `find_matching_candidates` · 1575 `find_differential_pair_candidates` · 1617 `_diff_pair_layer1_groups` · 2096 `_propose_gm_id_roles`(`vdd`·`gnd` 리터럴 2) ·
   2172 `_propose_L_roles`(2) · 3042 `kcl_series_union`(P9가 먼저 없앤다) · 3148 `_kcl_and_matching_edges` · 3253 `audit_vertical_stack_id_vs_kcl` · 3992·4171·4307·4323·4370·4392
   `propose_device_roles_gap_fill`; SR 2207 `true_current_mirror_groups`(이름 참조 2) · 4293 `_metric_kcl_residual`(리터럴 6). = 11함수, 16줄. `prep`의 줄 번호와 전부 일치(review 재측정 일치).
   명령: `python -B C:/g23/scan.py` (`grep -n "_RAIL_NETS\|_DEFAULT_RAIL_HI\|_DEFAULT_RAIL_LO\|rail_nets\|supply_nets\|_rail_nets" A/stick_diagram.py A/sizing_recipe.py workspaces/run_harness.py`와 교차 확인).
   호출 그래프(AST, 모듈 간 import 포함): 새 인자를 받는 함수 20개(SD 18, SR 2 -- 계약 4), 선언을 스스로 얻는 뿌리 10개. `_metric_kcl_residual`은 `_METRICS_REGISTRY` 경유 운영 도달.
   "엔진은 `supply_nets`를 읽지 않는다": 운영 코드 참조는 SR 4361(metric 키) 하나, 최상위 선언을 읽는 것은 test 보조 `tests/unit/_library_sized_contexts.py` `declared_supply_nets`뿐.
   **새로 찾은 것**: analog-grammar `netclass.py` 33~35행 `RAILS_POS/NEG/RAILS` 이름 집합 -- SD 운영 함수가 부른다(`prep` 스캔 범위 밖이었다. 처리 = B35, '의도' 범위 밖 3번째 항목).
2. **이름 충돌**: `grep -rn "rail_declaration\|RailDeclaration" skills workspaces tools docs/01-plan docs/02-design` → 0. 이름을 `validate_*`·`check_*`로 짓지 않았다 -- IC5 대상 규칙
   (`tests/contracts/test_ic5.py` `_TARGET_NAME_RES`)과 영역 표(21행 고정)에 걸리지 않게. 새 test 파일 `tests/contracts/test_b26_rail_accessor.py`는 `glob(` 사용처 전수(`grep -rn "glob(" A/tests/` --
   contracts 20곳, tools 3곳, unit 1곳)의 이름 패턴(`probe_*.py`, `*.topology.json` 등)과 겹치지 않는다. 다만 contracts의 파일 스캔형 test가 `tests/**/*.py` 내용을 읽으므로 새 test에 삭제된
   이름 참조·print 판정 토큰을 두지 않는다.
3. **원칙의 계약화**: topology 무관 = 계약 1·7(역방향 포함)·9, 폴백 금지 = 계약 1·2·5·6·13·14와 '거부해야 할 입력', 재계산 금지 = 계약 3, 배선 = 계약 10.
4. **쓰기 경로**(N3.12.2): SD·SR = code-author, 레지스트리 = code-author(계약 11), test·픽스처·probe = test-author(`A/tests/**`), 계획 정정 = 오케스트레이터. test-author는 엔진 소스를 못
   읽는다 -- interface card(계약 4의 새 시그니처 전부)와 spec card의 '관찰 가능한 계약'(거부 규칙 2·5·6, 계약 7의 '계약이 아닌 것', 계약 12의 입력 갱신 규칙)·'oracle'·'거부해야 할 입력'·
   '재현할 수치'만으로 쓸 수 있게 적었다(test-author가 읽는 절 -- agent 정의 21~22행).
5. **계획서 소비자**: 지우는 이름 없음(상수 3개는 B26-2·B26-4까지 남는다). 바뀌는 계획 문구(DEC-60 전환기) 소비자 = 계획서 254·314·388·769·802·870·929·936·1001·1021·1101행
   (정정안 §1~§6), `docs/02-design`의 "전환기 이름집합" 인용 0건.
6. **미배선**: 새 def `rail_declaration`은 `load_topology`가 부른다 -- 운영 도달(scratch 호출 그래프: `run_harness.run` → `run_full_circuit_audit_from_topology`/`optimize_full_circuit_budget`
   → `load_topology`). V7 면제 불필요. `RailDeclaration`은 클래스.
7. **기존 test 영향**(test-author 몫, 판정 기준을 바꾸지 않는 입력 갱신 -- 규칙은 계약 12):
   * 새 키워드 인자를 받게 되는 함수의 test 호출(AST, cd64170): `test_selftest_stick_diagram.py` 12함수 49곳(`find_matching_candidates` 9, `refine_…` 9, `propose_device_roles_gap_fill` 8,
     `repair_matching_safety` 7, `check_symmetry_dispositions` 4, `propose_vertical_stack_id_gap_fill` 3, `run_full_circuit_audit` 2, `audit_vertical_stack_id_vs_kcl` 2,
     `_composite_collapse_for_crossover` 2, `_branch_composite_pair`·`find_min_crossover_layout_with_branch_composite`·`find_differential_pair_candidates` 각 1),
     `test_selftest_sizing_recipe.py` `resolve_stack_layout` 2곳, `tests/probes/` 4파일 `true_current_mirror_groups` 각 1곳(`monkeypatch`로 이 함수들을 바꾸는 test 0개). **P9 병합 뒤 추가**:
     P9 계약 test가 `kcl_series_union`·`_kcl_and_matching_edges`를 직접 부른다(P9 card 계약 2·4) -- B26-1 base에서 다시 세고, 그 계약 test에 `rails=`를 더하는 것은 test-author 몫(판정·기대값 불변).
   * `supply_nets` 없이 topology를 만들어 **로드 경로**에 넣는 픽스처(엄격 거부 사본 전체 실행으로 확인 -- review_b26_1 §1: base 52 failed·746 passed·15 xfailed → 거부 사본 65 failed·729
     passed·15 xfailed·4 errors, 새 실패 17건 전부 `supply_nets missing`): `test_selftest_sizing_recipe.py` **15개**(180·237·289·457·585·878·1008·1899·1924·1987·2079·2161·2227·2273·2459행
     -- FAILED 11 + setup ERROR 4: s039·s041·s050·s053, 픽스처 `s037_state`·`s038_state`·`s040_state`·`s052_state`), `test_selftest_stick_diagram.py` **2개**(s071 1780·1787행, s125 2798행).
     3988행(`test_s160` `conflict_fixture`)은 `apply_device_roles_gap_fill`만 부르고 로드하지 않는다 -- 선언 없이 병합 상당에서 PASS(더해도 해는 없다). `test_ic3.py` 78행은 instance이고
     286행은 연결 파일(진입 파일이 library 사본이라 선언이 있다) -- 조정 불필요. `test_d_delete_telescopic.py` 합성 topology는 이미 선언이 있다. `test_df36_instance_relpath.py`·`test_probe_*`는
     library 파일을 읽는다 -- 조정 불필요.
   * `tests` 트리 안 대문자 레일 이름의 유일한 출현은 픽스처가 아니라 `tests/probe_physical_consistency.py` 40행의 probe 레일 집합(`RAIL_HI, RAIL_LO = {"vdd","VDD"}, {…}`)이다. library
     파일만 읽으므로 B26-1 영향은 없고, B26-4 lint 대상 후보다.
   * 위험: `_propose_*` 씨앗은 base가 `vss`를 몰랐다 -- `vss` 픽스처(237·289·1987·2079·2161·2227)에서 결과가 바뀔 수 있다(library vss 3회로 불변, 픽스처 규칙 근사 사본에서 두 selftest
     파일 판정 불변 -- review §1). 병합본에서 기존 기대값과 다르면 test-author는 기대값을 고치지 않고 dispute로 올린다.
   * **V5**: 기존 test에 `supply_nets` 키·`rails=` 인자를 더하는 것은 '픽스처 입력 리터럴 변경'으로 잡힐 수 있다 -- 기준 약화가 아니라 선언 추가이므로, `weakening_diff.py`가 표시하면
     오케스트레이터가 `target_kind: diff` 승인 기록(사유: 선언 추가, 기대값·비교 불변)을 받는다. 계약 test(`tests/contracts/`) 중 바뀌는 이름·파일을 참조하는 것은 없다(2 참조).
   * 판정 경로 밖(U-02 3항과 같은 취급): `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py`·`stick.py`·`probe_group_split_wiring.py`가 깨진다.
   * 인계 삭제(계약 13·14): `unavailable_reason`을 읽거나 단언하는 test·운영 코드 0곳(`git grep` 7535799 `skills workspaces tools docs/01-plan docs/02-design` -- SD 3531·3535·3540(`propose_theta_kcl_gap_fill`,
     백로그 B39, 이 card 밖)과 3968 정의, 3933 docstring뿐). 조정할 기존 test 0개. B34 계약 test의 `rails=` 추가는 계약 12 셋째 항목이다.
8. **B34 인계 재측정(2026-10-01, `7535799`, scratch C:/g59 -- 측정 뒤 삭제)**: 인계 사이트 줄을 `sed -n`으로 확인했다('의도' 표. B34 card 사이트 표·검토 정정과 일치). 모의 base·head 구성과 V3 수치는 'V3 계획' 1,
   동작 수치는 '재현할 수치' 마지막 항목에 있다. 쓰기 경로: SD 코드·docstring = code-author. `references/analog-grammar-integration.md`의 폴백 서술은 B34가 오케스트레이터 문서 커밋으로 고친다(B34 card '작성 전 실측' 7). 이 card에서 더 고칠 문서는 없다.
   미배선(V7): 지우는 def 0, 새 def 0(인계분) → 면제 불필요.
