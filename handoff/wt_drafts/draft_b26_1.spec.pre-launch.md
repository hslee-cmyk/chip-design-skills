---
id: 20260930-b26-rail-accessor-set
phase: 3
evidence_type: red-green
gate_change: no
approval: 20260930-b26-before-phase3
approval: 20261001-b26-phase3-cards
approval: 20260930-b26-b40-reason-key
---
## 의도

계획 DF-19·DF-26(담당 Phase 4)의 **넷 몫 첫 card(B26-1)**. 엔진은 지금 topology 최상위 `supply_nets`를 한 곳도 읽지 않고(운영 코드의 `supply_nets` 참조는 SR 4361 하나이며
그것은 metric 선언 안의 같은 이름 키다) 레일을 넷 이름 집합으로 정한다 -- SD `_RAIL_NETS = {"vdd","gnd","vss"}`, SR `_DEFAULT_RAIL_HI/LO`(대소문자 6개), SR `_metric_kcl_residual`
인라인 튜플(6개), SR `_build_theta_evaluator` 인라인(3개), SD `_propose_*` 씨앗(`vdd`·`gnd` 2개). 이 card는 **레일 선언을 읽는 정본 접근자 하나**를 만들고, **"이 넷이 레일인가"만 묻는
집합 판정 사이트**를 그 접근자가 준 선언으로 바꾼다. A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 cd64170
(계약 4·'작성 전 실측' 1). **P9·B34 병합 뒤(모의 base `b1`, 아래 'V3 계획' 1) 사이트 줄**: SD 1014·1571·1613·2092·2168·3133·3238·3973·4152·4288·4304·4351·4373(13줄 -- 3042는 P9가 없앴다),
SR 2207·4293(불변). 착수할 때 auditor가 실제 병합본에서 다시 잰다.

앞당김: 이 card는 Phase 4 DF를 Phase 2 DoD 뒤·Phase 3 M card 전에 한다(card `phase: 3` -- 사용자 결정 Q-B34-PHASE "phase 3 + 정정 기록 (Recommended)"(2026-10-01, AskUserQuestion [card phase]), 승인 기록 `20261001-b26-phase3-cards`가 A2 기록 ③의 'Phase 2 진행 중' 문구를 바로잡는다). 머리의 `approval: 20260930-b26-before-phase3`은 **사용자가 승인한 결정 A2**의 승인 기록(`target_kind: decision`)이다 --
(1) DEC-60 넷 전환기 종료 (2) DF-19·DF-26 넷 몫을 MG1에서 분리 (3) B26-1과 B34를 Phase 3 전에 착수. 사용자 원문 "승인 (Recommended)"(2026-10-01, `_drafts/user_decisions.md` A2.
질문 범위는 `_drafts/draft_b26_u2_approval_question.md`). 같은 기록을 B34 card(`20260930-b34-grammar-explicit`)도 가리킨다. 그 승인 기록은 gate `master` `2d58fd8`에
커밋됐다(`.ai/approvals/20260930-b26-before-phase3.md` -- merge gate 로더 규칙 6 충족). 단 그 기록의 범위 설명에는 아래 B40(`unavailable_reason` 키 삭제 -- 관찰 가능한 출력 변경)이 없다 --
'결정 필요 항목' U4(결정됨 -- 추가 decision 기록 `20260930-b26-b40-reason-key`). 옛 머리의 `approval: 20260923-20-dead-code-dup-design`은 design 20(P 목록)의 승인이라 B26을 덮지 않아
뺐다(review_b26_1 S3). 계획 정정(`_drafts/draft_b26_plan_patch.md`)은 이 card의 착수 조건이다 -- gate `8356c1e`(계획 정정(A2, 승인 20260930-b26-before-phase3))로 커밋됐다(충족, 착수 조건 2).
**순서(사용자 지정 + 원칙 기본안): P9 → P10 → P10b → Phase 2 DoD → V3 면제 묶기(`20260930-v3-exempt-binding`) → V3 범위 정책(`20260930-v3-changed-stmt-scope`) → B34 → b26pre(`20260930-b26-pre-test-strengthen`, test-only) → backfill 결함 card(`20261001-b26-backfill-interdig-final-audit`, red-green) → B26-1.** base = 이 순서로 병합한 뒤의 master다.
b26pre·backfill 두 card의 자리는 통합 질문(`_drafts/b26_survivor_final_question.md` '순서')의 원칙 기본안이고, backfill 수정 자체는 사용자 결정 U-BF "결함으로 고침 (Recommended)"(2026-10-01)이다.
엔진 소스로는 P9(`20260930-p9-kcl-edges`, 병합 `b7765b0`·판정 기록 `766b5c2` -- `kcl_series_union` 본문의 엣지 정의를 `_kcl_and_matching_edges` 호출로 합침)와 B34(`20260930-b34-grammar-explicit`,
analog-grammar 부재 시 `_import_analog_grammar`가 `ImportError`)를 더한 것이다. 두 V3 게이트 card는 이 card의 V3 판정 규칙이다('V3 계획'). P9가 SD 3042 판정을 없애므로 이 card에서 `kcl_series_union`은 `rails`를 받아 `_kcl_and_matching_edges`로
넘기기만 하는 함수가 된다. B34가 먼저 병합되어야 아래 '인계 삭제' 분기가 도달 불가가 된다(B34 앞에서 지우면 부재 시 동작이 바뀐다). B34·P9가 SD 줄을 옮기므로 착수할 때 줄 번호를 다시 잰다
(모의 base에서 B34 코드 변경만으로 1073 이후 사이트가 4줄 당겨진다. 예: 1575 → 1571. B34의 docstring 수정분은 따로 더해진다).

**B34에서 인계받은 삭제(B34 card '범위' 3·결정 3, `_drafts/b34_revision_log.md`)**: B34 병합 뒤에는 analog-grammar가 없으면 `_import_analog_grammar`가 먼저 `ImportError`를 낸다. 그래서
`refine_differential_and_mirror_relations`·`propose_device_roles_gap_fill` 안의 부재 분기는 도달할 수 없다. 이 card는 두 def의 본문을 어차피 바꾸므로(`rails` 인자) 그중 **문장 하나짜리
분기**를 여기서 지운다. 두 def는 이미 V3 대상이라 추가되는 대상 def는 중첩 def 하나뿐이다('V3 계획' 1). 백로그 **B40**(`propose_device_roles_gap_fill`이 analog-grammar가 있어도 gate 소자 없는 입력에
"analog-grammar를 import할 수 없어…"라는 틀린 사유를 싣는 문제)도 같은 분기를 정리하면서 닫는다. 줄 번호는 gate `master` `7535799`(B34·P9 병합 전 HEAD. `sed -n`으로 재측정, B34 card 표와 일치)와
모의 base `b1`(P9+B34 뒤):

| # | 함수 | 줄(7535799 / b1) | 바꾸는 것 |
|---|---|---|---|
| 9 | `refine_differential_and_mirror_relations` 내부 `classify` | 2400~2401 / 2396~2397 `if netclass is None: return None, None` | 삭제 |
| 9 | 같은 함수 | 2410~2411 / 2406~2407 `if cls_before is None: return None` | 삭제(`classify`가 늘 dict를 돌려주므로 도달 불가) |
| 10b | 같은 함수 | 2440~2441 / 2436~2437 `if relations is None: return None` | 삭제(같은 입력이 gate 소자 없음이면 2420 `candidates is None`에서 먼저 반환. `find_verified_…`의 `None`은 부재나 gate 소자 없음에서만 나온다) |
| 13 | `propose_device_roles_gap_fill` | 4071~4073 / 4052~4054 `_static_ref_roles = (…) if _netclass_lcmf is not None else ()` | 조건 없이 4원소 튜플 |
| B40 | 같은 함수 | 3966~3970 / 3947~3951 `if refined is None: return {…, "unavailable_reason": "analog-grammar를 import할 수 없어…"}` | 분기는 **남긴다**(gate 소자 없는 입력에서 `refined is None`은 여전히 참). 반환 dict에서 `unavailable_reason` 키만 지운다(소비처 0 -- `git grep` 7535799 `skills workspaces tools docs/01-plan docs/02-design`: SD 정의 줄 외 0) |

**B35로 넘기는 인계(v4, review2_b26_1 B2 E2·E2b)**: 사이트 **10**(`refine_…` 2495 / b1 2491 `if _netclass_al is not None:` 삭제 + 블록 내어쓰기)과 **14**(`propose_device_roles_gap_fill`
4087 / b1 4068 `if _idioms_lcmf is not None:`·`else:`·`cascoded_active_load_legs = set()` 삭제 + 블록 내어쓰기)는 이 card에서 **지우지 않는다**. 근거(실측): 내어쓰기는 범위 정책 card 계약 1에서
'들여쓰기만 바뀐 문장 = 새 문장'(T1)이라 두 블록의 부분 트리 전체가 V3 대상이 된다. 그 블록이 만드는 값(`active_load_leg_candidates`·`signal_referenced_mirror_legs`·`branch_load_partner_candidates`,
그 뒤 `gain_role_candidates |= cascoded_active_load_legs`)은 netclass·idioms 유래라 이 card의 '계약이 아닌 것'(계약 7)과 충돌하고, 기존 test도 보지 않는다 -- 모의 실측에서 생존 13 + 1(E2·E2b).
analog-grammar 진입 계약을 다시 쓰고 그 출력을 판정하는 card는 B35다. 두 분기는 B34 병합 뒤 도달 불가인 채로 남는다(동작 영향 없음 -- B34 docstring이 이미 적는다).

docstring(AST 해시 불변): `propose_device_roles_gap_fill` 3932~3933과 `refine_…` 2349~2350에서 B34가 고친 "도달 불가 -- 삭제는 B26-1" 구절을, 남는 두 분기만 가리키게
"`_netclass_al`·`_idioms_lcmf`의 `is not None` 분기는 도달 불가 -- 삭제는 B35"로 고친다. 그 밖의 서술은 "gate 소자가 없으면 빈 제안"(`refine_…`은 "`None`")이다.
바꾸지 않는 것: `refine_…` 2420 `if candidates is None: return None`(gate 소자 없음 경로, B34 계약 5가 고정), 사이트 10·14(B35).

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
   * **기본값 불변(E3 -- V3 필수, 생략 불가)**: 키워드 전용 `rails`를 더해 def 머리가 바뀌므로 그 def의 기존 기본값 상수가 V3 대상(범위 정책 card 계약 1 T3 자기 필드)이 된다. 이 card는 기본값을
     바꾸지 않는다: `inspect.signature(stick_diagram.refine_differential_and_mirror_relations).parameters["max_iterations"].default == 5`,
     `inspect.signature(stick_diagram.repair_matching_safety).parameters["max_iter"].default == 3`, `inspect.signature(stick_diagram.run_full_circuit_audit).parameters["row_width_tol"].default == 1.5`.
     그리고 세 함수의 `rails` 매개변수는 `inspect.Parameter.KEYWORD_ONLY`이고 `default is inspect.Parameter.empty`(기본값 없음 -- 원칙 2). 기본값 단언은 base에서도 참(green 회귀 고정),
     `rails` 단언은 base에서 `KeyError`(집계 밖).
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
   것이 아니다). **양성(E5 -- V3 필수, 생략 불가)**: 같은 kind·다른 gate의 두 소자가 **선언 밖** 넷을 source로 공유하면 후보에 **있다**. 입력(`rails` = `rail_declaration({"supply_nets": ["rail_hi", "rail_lo"]})`):
   `Da`(nmos, source `vdd`, drain `o1`, gate `i1`), `Db`(nmos, source `vdd`, drain `o2`, gate `i2`), `Dt`(nmos, source `rail_lo`, drain `vdd`, gate `vb`) -- 여기서 `vdd`는 **선언되지 않은 보통 넷**이다.
   기대: `find_matching_candidates(ts, rails=rails)["diff_pair"]`를 이름 목록으로 바꾼 값 = `{("nmos", "vdd"): ["Da", "Db"]}`, `_diff_pair_layer1_groups(ts, rails=rails)` = `{("nmos", "vdd", None): ["Da", "Db"]}`
   (값은 이름 목록으로), `find_differential_pair_candidates(ts, rails=rails)["candidates"]`에 `{"direction": "layer1_fallback", "position": None, "devices": ("Da", "Db"), "shared_source": "vdd"}`가 있다.
   (직접 호출이라 base는 `TypeError` -- 집계 밖. 양성이 없으면 층위1 루프를 지운 변이 -- 결과가 늘 빈 것 -- 를 죽이지 못한다: review2_b26_1 E5.)
   (b) `_kcl_and_matching_edges`·`kcl_series_union`이 선언 레일을 통해 소자를 잇지 않고, 그래서 `load_topology` meta `_vertical_stack_id_autofilled`에서 선언 레일만을 통해 이어진 소자가
   다른 소자의 선언 `vertical_stack_id`를 자동으로 받지 않는다;
   (c) 게이트가 선언 레일에 물린 소자는 `l_sharing_classes`의 미러 동치류를 만들지 않는다. **meta 획득 경로(review2_b26_1 S2)**: test는 합성 topology를 tmp 파일로 쓰고
   `ts, meta = stick_diagram.load_topology(<그 경로>)`로 얻은 `meta`와 `{t.name: t for t in ts}`를 `sizing_recipe.l_sharing_classes(by_name, meta)`에 넘긴다. `meta`를 `rail_declaration`으로
   직접 만들지 않는다(그러면 base red가 단언형이 아니라 신규 심볼 `AttributeError`가 된다). 이 경로로 base에서 단언 실패(red)다;
   (d) kcl_residual이 선언 레일 노드를 잔차에서 뺀다;
   (e) **`propose_device_roles_gap_fill`의 레일 사이트(E1 -- V3 필수, 생략 불가)** -- B26-1 사이트 4152·4288·4304·4351·4373(b1 줄)이 정하는 세 필드 `vds_match_vgs_of`·`budget_reference_device`·
   `fold_group`만 본다(같은 반환의 `gm_id_role`·`L_role`·`headroom_role`과 `review_needed`는 '계약이 아닌 것' 그대로). 관찰: `res = stick_diagram.propose_device_roles_gap_fill(ts, roles, [],
   compensation_stage_devices=["Qy", "Qz"], rails=rails)`, `rails = rail_declaration({"supply_nets": ["rail_hi", "rail_lo"]})`에서
   `{n: {f: p[f] for f in (세 필드) if f in p} for n, p in res["device_roles_proposals"].items()}`의 빈 값 아닌 항목. 규칙(손으로 적용 -- 기대값의 출처):
   (i) 보상단 Y(`compensation_stage_devices` 원소)의 gate가 선언 레일이면 그 Y로는 `vds_match_vgs_of`를 제안하지 않는다. 그렇지 않으면 `X.drain == Y.gate`·`X.source == Y.source`·X가 diode 아님·
   X가 보상단 아님·X에 `vertical_stack_id` 있음·기존 KVL 필드 없음인 X가 **정확히 하나**일 때 X에 `vds_match_vgs_of = Y`.
   (ii) `vertical_stack_id`가 있는 X의 열린 단자(source·drain 중 선언 레일도, 같은 `vertical_stack_id` 소자의 단자도 아닌 넷)가 **정확히 하나**이고, 그 넷을 drain으로 쓰는 다른 소자 Y가 정확히 하나이며
   Y.source가 **선언 레일**이고 `X.source != Y.source`이고 Y의 `vertical_stack_id`가 X와 다를 때만 X에 `budget_reference_device = Y`. 열린 단자가 둘이면 제안 없음.
   (iii) X.drain이 선언 레일이면 `fold_group` 없음. X.drain을 drain으로 쓰는 다른 소자 Y가 정확히 하나이고 kind가 다르며 **Y.source가 선언 레일이 아니고** 양쪽 `vertical_stack_id`가 있고 다르면
   두 소자에 `fold_group = f"{X.drain}_fold"`(Y.source가 선언 레일이면 그 방향으로는 없음).
   입력(12소자 -- 부분 회로끼리는 `rail_hi`·`rail_lo` 말고는 넷을 공유하지 않는다): `Qy`(nmos, s `rail_lo`, d `n_out`, g `n_a`), `Qx`(nmos, s `rail_lo`, d `n_a`, g `n_in`), `Qz`(nmos, s `rail_lo`, d `n_o2`, g `rail_hi`),
   `Qw`(nmos, s `rail_lo`, d `rail_hi`, g `n_b`), `Mx`(nmos, s `rail_lo`, d `n_m`, g `n_g1`), `My`(pmos, s `rail_hi`, d `n_m`, g `n_g2`), `Nx`(nmos, s `n_q`, d `n_p`, g `n_g3`), `Ny`(pmos, s `rail_hi`, d `n_p`, g `n_g4`),
   `Kx`(nmos, s `rail_lo`, d `n_r`, g `n_g5`), `Ky`(pmos, s `n_t`, d `n_r`, g `n_g6`), `Fx`(nmos, s `n_u`, d `rail_lo`, g `n_g7`), `Fy`(pmos, s `n_v`, d `rail_lo`, g `n_g8`)(`rail_lo`를 drain으로 쓰는 소자는 이 둘뿐이다 -- 그래야 'X.drain이 레일' 판정을
지운 변이에서 두 소자가 서로의 유일한 drain 이웃이 되어 `fold_group`이 생긴다. `rail_hi`는 `Qw`도 drain으로 쓴다).
   `roles` = `vertical_stack_id`만: `Qx` S1, `Qw` S2, `Mx` S3, `My` S3b, `Nx` S4, `Kx` S5, `Ky` S6, `Fx` S7, `Fy` S8.
   기대(위 규칙을 손으로 적용): `{"Qx": {"vds_match_vgs_of": "Qy"}, "Mx": {"budget_reference_device": "My"}, "My": {"budget_reference_device": "Mx"}, "Kx": {"fold_group": "n_r_fold"},
   "Ky": {"fold_group": "n_r_fold"}}` -- `Qw`(Qz의 gate가 레일)·`Nx`(열린 단자 둘)·`Kx`의 budget(Y.source가 레일 아님)·`Mx`/`My`의 fold(서로의 source가 레일)·`Fx`/`Fy`(drain이 레일)는 제안 없음.
   직접 호출이라 base는 `TypeError`(집계 밖). 같은 입력을 `load_topology` meta `_device_roles_autofilled`의 세 필드로 보면 시그니처 불변 진입점이라 단언 red가 되지만(review2_b26_1 §4),
   보상단 선언(`compensation.stage_devices`)과 `device_roles` 선언을 갖춘 topology 파일이 필요하다 -- 선택 사항(red 증거는 7(a)~(d)가 맡는다).
   **역방향**: 선언에 없는 넷이 `vdd`·`gnd`·`vss`라는 이름이어도 위 관찰 대상 -- meta `_matching_pairs_autofilled`, meta `_vertical_stack_id_autofilled`, `l_sharing_classes`,
   kcl_residual, 직접 호출한 `find_matching_candidates`·`_kcl_and_matching_edges`·`kcl_series_union` -- 에서 레일로 취급되지 않는다(보통 내부 노드와 같은 결과).
   **계약이 아닌 것(test 기대값으로 쓰지 않는다)**: `device_roles`·`_device_roles_autofilled`의 `headroom_role`, `_device_roles_gap_fill_review_needed`, analog-grammar(`netclass`·`idioms`) 유래
   필드, 역할 자동 채움(`L_role`·`gm_id_role`)의 `null` 여부, 그리고 **`load_topology` meta 전체의 넷 이름 불변**(7(e)의 세 필드 `vds_match_vgs_of`·`budget_reference_device`·`fold_group`은
순수 연결성 + 선언 레일 판정이라 **계약이다** -- 위 7(e)). 이것들은 병합본에서도 analog-grammar `netclass.RAILS`(대소문자 무관 이름
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
    * backfill 결함 card의 test 파일(`test_b26_backfill_interdig.py`)은 시그니처가 안 바뀌는 `run_matching_safety_with_finger_growth`만 부르므로 고치지 않는다.
    * B34 계약 test(`A/tests/contracts/test_b34_grammar_explicit.py`, B34 병합본)가 이 card에서 `rails`를 받게 되는 함수를 직접 부른다: `refine_differential_and_mirror_relations`(B34 계약 1·5),
      `find_differential_pair_candidates`·`propose_device_roles_gap_fill`·`propose_vertical_stack_id_gap_fill`(B34 계약 1). 위 규칙대로 `rails=`를 더한다. 부재 test에서는 선언을 부재를 만들기
      **전에** 얻는다(`rail_declaration`은 analog-grammar를 쓰지 않지만, `load_topology`는 부재에서 `ImportError`를 낸다). 판정·기대값은 그대로 둔다.
    * **넷리스트만 쓰는 직접 호출(review2_b26_1 S3)** -- topology 없이 `Transistor` 목록을 만들어 계약 4의 함수를 부르는 기존 test(selftest 49곳, P9 계약 test `test_dup_kcl_edges.py`의
      `kcl_series_union`·`_kcl_and_matching_edges` 호출 2곳 × 합성 넷리스트 11개, b26pre 계약 test `test_b26pre_existing_paths.py`의 `resolve_stack_layout`(b26pre 계약 5) 1곳·
      `propose_vertical_stack_id_gap_fill`(b26pre 계약 6) 2곳·`find_differential_pair_candidates`(b26pre 계약 11) 2곳 -- 이 셋은 `vdd`·`gnd`만 쓰므로 `rails = rail_declaration({"supply_nets": ["vdd", "gnd"]})`, '작성 전 실측' 7): `rails = stick_diagram.rail_declaration({"supply_nets": [그 넷리스트의 소자 단자(source·drain·gate)에
      나오는 넷 중 소문자 정확히 "vdd"·"gnd"·"vss"인 것, 처음 나온 순서, 중복 없이]})`. 그런 넷이 없으면 `[]`. base가 레일로 읽던 이름(SD `_RAIL_NETS`)을 그 넷리스트에 나오는 만큼 선언하는 것이라
      판정이 바뀌지 않는다(대문자 레일 이름 픽스처는 없다 -- '작성 전 실측' 7. P9 test의 레일 이름 입력은 `gnd` 3회 사용 케이스 하나이고 3회 사용 규칙으로 결과가 같다 -- review2_b26_1 §5).
    * **P9 계약 test의 시그니처 단언(review2_b26_1 B3)** -- `test_dup_kcl_edges.py`(P9 병합본 281~298행)의 `test_kcl_series_union_signature_unchanged`·`test_kcl_and_matching_edges_signature_unchanged`는
      매개변수 목록이 정확히 `["netlist", "matching_pairs"]`·`["transistors", "matching_pairs"]`인지, 그리고 **모든** 매개변수의 주석이 `list`(또는 `"list"`)이고 기본값이 없는지 단언한다.
      이 card의 계약 4가 그 'P9 시그니처 유지' 계약을 **대체**한다: 새 기대 = `["netlist", "matching_pairs", "rails"]`·`["transistors", "matching_pairs", "rails"]`, 앞 두 매개변수는 지금 단언
      그대로(주석 `list`, 기본값 없음), `rails`는 `KEYWORD_ONLY`·기본값 없음·주석 `RailDeclaration`(또는 `"RailDeclaration"`), 반환 주석 단언은 그대로. **이것은 기대값 변경이라 test-author가 혼자 할 수 없다**
      (작성자≠검증자, V5) -- 사용자 승인 U5 "갱신 승인 (Recommended)"(2026-10-01)를 받았다 -- 오케스트레이터가 `target_kind: diff` 승인 기록(`20261001-b26-p9-signature-update`, 사유: P9 '시그니처 유지' 계약을 B26-1 계약 4가 대체, 판정 기준 약화 아님 --
      매개변수 목록 정확 일치 단언은 유지하고 원소만 늘어남)을 **1차 시도** test 커밋 T1로 채워 2차 시도 착수 전에 커밋한다('승인 줄 배치' 4와 '두 번 시도 절차' -- 같은 시도 안에서는 head 트리에 넣을 수 없다). test-author는 interface card의 새 시그니처로 갱신한다('결정 필요 항목' U5, 착수 조건 9). test 이름의 `unchanged`는
      바꾸지 않는다(이름 변경은 V5 표시 대상만 늘린다).
    * 병합본에서 기존 기대값과 다르게 나오면 기대값을 고치지 않고 dispute로 올린다(작성자≠검증자). 특히 `_propose_*` 씨앗에 `vss`가 들어가므로 `vss` 픽스처를 주의한다.
13. **인계 삭제 -- 조용한 폴백 값이 나오는 경로 없음(B34 병합 뒤)**: analog-grammar 부재(`monkeypatch.setitem(sys.modules, "netclass", None)`·`"idioms"`. B34 계약과 같은 흉내 방식)에서
    `refine_differential_and_mirror_relations(ts, rails=…)`와 `propose_device_roles_gap_fill(ts, {}, [], rails=…)`는 library 9회로 전부 `ImportError`를 낸다(`__cause__`가 `ImportError`).
    옛 폴백 값(`None`, 빈 제안 dict)을 반환하는 경로가 없다. 동작 자체는 B34 병합 뒤 base에서도 같지만, 이 test는 `rails=`를 넘기므로 **base 실행은 `TypeError`다 -- red도 green도 아니라
    'base `TypeError`, red 집계 밖'**(계약 14와 같은 처리, review2_b26_1 S1). 인계 분기를 지운 것이 부재 시 동작을 바꾸지 않았다는 증거는 아래 auditor 대조가 맡는다.
    analog-grammar가 있을 때는 지운 분기가 동작을 바꾸지 않는다. 계약 8(E-LIB 9/9)과 함께, `refine_…`·`propose_device_roles_gap_fill`(`device_roles` = 그 topology 선언, `matching_pairs_meta` = `[]`)의 반환이
    9/9 base와 같다(auditor 대조, 같은 `PYTHONHASHSEED`. 모의 실측 9/9 같음 -- '재현할 수치').
    **auditor AST 측정(영구 test 아님)**: 병합본의 두 def(중첩 `classify` 포함)에서 `_import_analog_grammar` 반환을 받은 이름을 `None`과 비교하는 식이 **2개**이고 그것은 B35로 넘긴 사이트 10
    `_netclass_al is not None`·14 `_idioms_lcmf is not None`뿐이다(모의 base 4 = 사이트 9 `netclass is None`·10·13·14, 모의 head v4 2). 사이트 9 둘째 줄(`cls_before is None`)과 10b(`relations is None`)는
    모듈 이름 비교가 아니므로 이 측정에 잡히지 않는다. 그래서 auditor는 diff로 그 두 `if`가 지워졌는지도 확인한다.
14. **B40 -- gate 소자 없는 입력의 반환(analog-grammar 있음)**: `fx = [Transistor("Ma", "pmos", source="vdd", drain="n1"), Transistor("Mb", "nmos", source="gnd", drain="n1")]`(gate 없음, B34 계약 5와 같은
    입력), `rails` = `rail_declaration({"supply_nets": ["vdd", "gnd"]})`일 때 `propose_device_roles_gap_fill(fx, {}, [], rails=rails) == {"matching_pairs_proposals": [], "device_roles_proposals": {}, "review_needed": []}`이다.
    키는 정확히 셋이고 `unavailable_reason` 키가 없다. `refine_differential_and_mirror_relations(fx, rails=rails) is None`은 그대로다(B34 계약 5와 같다).
    **gate 없는 입력의 직접 호출(E4 -- V3 필수, 생략 불가)**: 같은 `fx`·`rails`로 `stick_diagram._propose_gm_id_roles(fx, (), (), (), (), (), rails=rails) is None`,
    `stick_diagram._propose_L_roles(fx, {}, (), (), (), (), (), rails=rails) is None`. 가드는 운영 흐름에서는 `refine_…`이 먼저 `None`으로 돌아가 도달하지 않지만 직접 부르면 도달한다 --
    `_propose_gm_id_roles`의 `candidates is None` 가드를 지우면 `TypeError`가 난다(review2_b26_1 E4, 모의 실측으로 죽음). `_propose_L_roles`의 두 가드(`gm_id_roles is None`·`candidates is None`)는
    서로 중복이라 하나만 지운 변이는 등가다. 계약 15의 정리 C1이 `candidates is None` 가드를 지우면 남는 `gm_id_roles is None` 가드의 삭제 변이를 이 test가 죽인다(통합 측정 B). base는 `TypeError`(집계 밖).
15. **동작 불변 정리 2줄(code-author, 엔진 변경 -- V3 필수, 통합 질문 Q1 1번(권고) 기준)**: 이 card가 이미 바꾸는 def 안에서 등가 변이 자리를 없애는 정리다. 관찰 가능한 동작은 바뀌지 않는다.
    * **C1** `stick_diagram._propose_L_roles`: 두 번째 `find_differential_pair_candidates(…, rails=rails)` 호출 뒤의 `if candidates is None: return None`을 지운다. 근거: `_propose_gm_id_roles`가 `None`을 돌려주는 유일한 경우는
      같은 인자의 `find_differential_pair_candidates`가 `None`일 때이고(모의 head 2086~2089), 그 경우 앞의 `if gm_id_roles is None: return None`이 먼저 같은 `None`을 돌려준다(등가 근거 1·2).
    * **C2** `stick_diagram.propose_device_roles_gap_fill`: `open_net = open_terminals[0]` → `(open_net,) = open_terminals`. 근거: 바로 앞 `if len(open_terminals) != 1: continue`로 원소가 정확히 하나다(등가 근거 3).
    * 판정: C1·C2 뒤 auditor V3 대상에 `_propose_L_roles` `if candidates is None` 삭제 변이와 `[0]` const− 변이가 없다(문장이 없거나 첨자가 없다). 남는 `gm_id_roles` 가드 삭제 변이는 계약 14(E4)가 죽인다.
      **정리로 새로 대상이 되는 4개도 죽어야 한다**: C1·C2로 대상 4개가 빠지고(지운 가드의 삭제·cmp_flip, `[0]` const±) 대신 4개가 새로 들어온다 -- `_propose_L_roles`의 지운 가드 바로 뒤 문장 삭제 1,
      `propose_device_roles_gap_fill`의 `open_net`을 읽는 문장 삭제·cmp_flip 3. auditor는 '대상 소멸'만 보지 않고 이 새 4개가 계약 7(e) E1·b26pre test로 죽는지 판정한다(통합 측정 B: E1 3, E1+b26pre 1, 독립 검토 `review_b26_final.md` §1.4).
      동작 불변은 계약 8(E-LIB 9/9·감사 9/9·E-INST)과 계약 14 E4가 확인한다(새 test 없음).
    * 하지 않는 것: C3(`range(i + 1, len(chains))` 이중 루프 → `itertools.combinations`). 측정 B에서 루프 본문 7문장이 새로 대상이 되어 생존 7 -- `range` const− 1개는 해시 묶기 면제로 둔다('V3 계획' 3).
    * 통합 질문 Q1이 2번(등가 4개 모두 면제)으로 답해지면 이 계약 항목 전체를 지운다(계약 14의 마지막 문장도 '등가 2개는 면제'로). 3번이면 C3까지 넣고 새 생존 7의 처리 계약이 필요하다.

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
| 7(c) | `sizing_recipe.l_sharing_classes`(meta = 합성 topology 파일의 `load_topology` -- 계약 7(c)) | 게이트가 `rail_hi`인 NMOS 둘 + 게이트 `bp`인 PMOS 둘 | `{Ma,Mb},{Pc,Pd}` → `{Pc,Pd}` |
| 7(d) | `compute_metric`(kcl_residual)·`sizing_recipe._metric_kcl_residual` | 합성 4소자 `ID` 1·2·1·2.5 µA | 3.5e-6 → 5.0e-7 |
| 2 | `load_topology` | `supply_nets` 없음 | base 받아들임(`pytest.raises` DID NOT RAISE = `Failed`, DF-36 판정 기록이 red로 셈) |
| 6 | kcl_residual | 선언에 `rail_nets` 키 | base 5.0e-7(키를 읽음) → `ValueError` |

7(b)는 위 `vertical_stack_id` 입력이 없으면 red가 oracle (b)(library `two_stage_ota`)뿐이다. 그 밖에 setup 수준 레일 이름 바꾸기 불변(oracle (b)). 신규 심볼(`rail_declaration`,
`RailDeclaration`)은 base에서 `ImportError`/`AttributeError`로 red 수집 플러그인의 신규 심볼 판정에 걸린다. 표의 병합 상당 값은 기대값의 **출처가 아니다** -- 기대값은 oracle (a)로 손으로
정한다(표는 red가 난다는 증거일 뿐).
**주의(V2)**: 계약 4의 새 키워드 인자를 직접 넘기는 test는 base에서 `TypeError`다 -- 허용 예외 타입 밖이라 red로 세지 않는다. red 증거는 위 공개 진입점 test가 맡는다. 판정 기록은
test를 **네 칸**으로 나눠 적는다(review2_b26_1 §4):

| 칸 | 계약 |
|---|---|
| 단언 red(시그니처 불변 진입점) | 2, 5, 6, 7(a)(b)(c)(d)의 공개 진입점 test, oracle (b) |
| 신규 심볼 red | 1, 3(`rail_declaration`·`RailDeclaration`) |
| base `TypeError`, red 집계 밖(`rails=` 직접 호출) | 7(a) 양성(E5)·역방향 직접 호출, 7(e)(E1), 13, 14(B40·E4), 4의 `rails` 매개변수 단언(base `KeyError`) |
| green 회귀 고정(base·head 모두 통과) | 4의 기본값 불변(E3), 8(동작 보존 -- auditor), 15(정리 C1·C2 -- 새 test 없음, 동작 불변은 8·14가 판정하고 대상 소멸은 auditor V3 측정) |

**인계 삭제(계약 13·14)의 증거 종류**: 계약 13 test는 `rails=`를 넘기므로 base에서 `TypeError`(집계 밖)다 -- green-green이 아니다(review2_b26_1 S1). 지운 분기가 도달 불가이므로 red가 날 수도 없다.
이 부분의 증거는 'base에서 도달 불가 → 지워도 동작 같음'이고, 계약 8·13의 9/9 대조와 계약 13의 AST 측정으로 확인한다. 계약 14(B40)는 base(P9+B34 병합본)에서 값이 다르다(`unavailable_reason` 키가 있음 -- 모의 base 실측).
하지만 `propose_device_roles_gap_fill`은 계약 4에서 `rails`를 받게 되므로 base 호출은 `TypeError`다(red로 세지 않음). 시그니처가 안 바뀌는 진입점으로는 관찰되지 않는다. 유일한 운영
호출자 `load_topology`는 반환의 `device_roles_proposals`·`matching_pairs_proposals`만 읽는다. 그래서 계약 14는 head에서 green인 계약 test로만 두고, 판정 기록에 'base `TypeError`, red 집계 밖'으로
적는다. 필요하면 auditor가 base 값 차이를 `rails` 없이 부른 base 호출로 따로 재서 basis에 적는다.

## oracle 종류와 출처

(a) 구성: 합성 topology(라이브러리에 없는 넷·소자·회로 이름, 선례 `tests/contracts/test_d_delete_telescopic.py` 185·215행 `_SYN_RAILS = ["rail_hi","rail_lo"]`, `supply_nets`
선언)에서 기대값을 손으로 적는다 -- 어느 쌍이 차동 층위1 후보인지, 어느 소자가 KCL로 이어지는지, KCL 잔차를 손으로 계산(계약 6의 가지 각각: 부호, 이상전원 값 있음/`null`, `exclude_nets`,
최댓값). (b) 변환 불변(IC11 `test_rail_origin_shift_invariance`와 같은 종류): library 사이징 대상 topology의 레일 넷 이름만 바꾼 사본(tmp)에서 `_build_theta_evaluator(사본, canonical_spec)`의
**setup 반환값** `stack_groups_kcl`·`stack_groups_geometry`가 이름을 되돌리면 원본과 같다(evaluate는 부르지 않는다 -- 평가는 B26-2·B26-3 사이트를 지나 아직 불변이 아니다).
scratch 실측: 병합 상당 사본 4/4 같음, base는 `two_stage_ota`에서 다름(red).
oracle (b)의 setup 불변 test는 `_build_theta_evaluator(<사본 경로>, <canonical spec>)`의 **setup 반환 키 `stack_groups_kcl`·`stack_groups_geometry`만** 비교하고 반환된 `evaluate`는
**부르지 않는다**(평가는 B26-2·B26-3 사이트를 지난다). 원본 경로와 이름 바꾼 경로의 두 호출은 인자 정규형이 다르므로 V4 `test_lint.py` (1)에 걸리지 않고, 이 비교의 독립성 판단은
auditor `checks.V4.basis`로 간다(review_b26_1 M4. 계약 14 아래에서 이 절로 옮김 -- review2_b26_1 M1).
(a)의 추가 계약(4 기본값·7(a) 양성·7(e)·14 E4)의 기대값도 card 문장의 규칙을 손으로 적용한 값이다(피검 함수를 불러 만들지 않는다).
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
  (이 측정의 head는 사이트 10·14도 지운 판이다. v4는 그 부분집합(9·10b·13·B40)만 지우므로 같은 결론이다 -- 착수 시 auditor가 병합본으로 다시 잰다.)
* V3(2026-10-01, 통합 측정 scratch C:/g103 -- 'V3 계획' 1·2, `_drafts/b26_survivor_final_question.md` '측정 요약'): v4 head 대상 301(N2b 235), 옮긴 264 중 기존 test 죽임 214, **기존 test 생존 50**
  = B26-1 계약 26 + b26pre 16 + trace 2 + backfill 결함 2 + 등가 4. backfill card 병합 base에서는 대상 299, 시제품 합집합 + 기존 test 뒤 남는 4 = 등가 4(시나리오 A).
  (옛 C:/g83 측정 '기존 인벤토리 150 + 계약 근사 87, 생존 27 → 남는 24'는 `_drafts/b26_1_revision_log_v4.md` §3.) 추가 계약 근사(`_drafts/b26_scripts/test_b26x_approx.py`)는 변이 없는 `b1`에서 5/5 통과(손으로 적은 기대값이 base 동작과 같음 -- 7(e) 입력의 `Fx`·`Fy` drain을
  `rail_lo`로 둔 판. `rail_hi`로 두면 `Qw`와 drain을 공유해 'X.drain이 레일' 판정 삭제 변이가 살았다 -- 실측).

## V3 계획

**판정 규칙(결정됨, U1)**: 사용자 결정 2026-10-01 -- A1-a "승인 (Recommended)"(면제 묶기 `20260930-v3-exempt-binding`: 면제 = 변이 id@함수 원본 해시, 해시가 같을 때만 적용),
A1-b "② N2 (Recommended)"(범위 정책 `20260930-v3-changed-stmt-scope`, def 머리 변경은 (b) 좁은 판)와 A1-b 정정 "규칙을 안내에 맞게 넓힘 (Recommended)"(T6 = 같은 블록 뒤쪽에서 바뀐 이름을 읽는
문장 전부). 원문 `_drafts/user_decisions.md`. 이 card는 두 게이트 card가 병합된 뒤 그 규칙으로 판정한다(착수 조건 5·6). 대상 = 범위 정책 card 계약 1(T1~T6): 바뀐 문장, 감싸는 제어문,
삭제 지점 바로 뒤 문장, 바뀐 이름을 **같은 블록 뒤쪽**(반복문 본문이면 그 본문의 다른 모든 문장)에서 읽는 문장, def 머리가 바뀐 def의 자기 필드와 바뀐 매개변수를 읽는 문장, `early_return`.
복합문은 **자기 필드**(블록 필드 밖)에서 읽을 때만 '읽는다'이고 그 몫도 자기 필드다(계약 1 용어). 새 def(`rail_declaration`)는 본문 전체. 대상 밖 변이는 실행하지 않고 `not_targeted`로 출력한다.
옛 선택지 (a)(b)(c)·`v3_scope_systemic.md` 권고·619개 누수 예시·'닿은 변이' 수치는 history로 옮겼다(`_drafts/b26_1_revision_log_v4.md` 부록 -- 문서 커밋 때 history H 절).

1. **대상 수(재측정 2026-10-01, 모의 사본 -- 착수할 때 auditor가 실제 병합본에서 다시 잰다)**.
   * 모의 base `b1` = gate `master` `2d58fd8` archive(엔진 = `7535799` + P9 `b7765b0`, 판정 기록 `766b5c2` 이후 엔진 변경 없음) + B34 코드 변경(사이트 1·2·3·11·11b). 모의 head = `b1` + B26-1 상당
     (계약 4의 20함수에 키워드 전용 `rails`, 호출부 `rails=rails`, 뿌리 선언 획득 문장, 사이트 교체 -- SD 13줄 + SR 2줄, 새 def 2개) + 인계 삭제. 스크립트 `_drafts/b26_scripts/`
     (`mk_b1.py`·`b26v4_head.py`·`b26v4_classify.py`. 분류기 = 범위 정책 card의 구현 기준 `v3_scope_widen.py` 그대로), scratch C:/g83(측정 뒤 삭제). 도구 함수만 읽기 전용 import, `main` 미실행.
   * **review2 head 재현**(인계 9·10·10b·13·14·B40): 바뀐 def 32, 변이 전체 **2,437**(review2 M3와 같음), **N2b 265**(review2와 같음), 넓힌 T6을 더한 **이 card 규칙 330**.
     review2의 '넓힌 T6 own 314 / deep 336'과의 차이: review2 스크립트(`m70.py`)는 지워져 대조할 수 없다. 범위 정책 card 계약 1의 '바꾸는 이름' ⓑ(속성·첨자 대입 대상)·ⓒ(메서드 호출 수신자)를
     빼면 317, ⓒ만 빼면 318이다 -- review2의 own은 이름 규칙이 더 좁았던 것으로 본다. **확정 수는 card 규칙(ⓐ~ⓓ 전부, 복합문 자기 필드) 값이다.**
   * **이 card(v4) head**(인계 9·10b·13·B40, 사이트 10·14는 B35 -- '의도'): 바뀐 def 32(최상위 30 + 중첩 `_evaluate_row_split`·`refine_…classify`), 변이 전체 2,442,
     **V3 대상 301**(N2b 235 + 넓힌 T6 66). 하한(× 5 s) 25분, 상한(Σ 대상 × 인벤토리 시간) 16.0 h, base 미실행 줄 대상 변이 9, 인벤토리 0 대상 변이 6(`_metric_kcl_residual` -- 아래 4로 0이 된다).
     비교용 deep 변형(복합문의 하위 블록에서 읽어도 셈) 411.
   * def별 대상(v4): `propose_device_roles_gap_fill` 52, `run_matching_safety_with_finger_growth` 19, `refine_…` 17, `audit_vertical_stack_id_vs_kcl` 16, `load_topology` 16, `_branch_composite_pair` 15,
     `rail_declaration`(새) 14, `find_differential_pair_candidates` 13, `optimize_full_circuit_budget`·`_propose_L_roles`·`_composite_collapse_for_crossover` 각 10, `resolve_stack_layout`·`_propose_gm_id_roles`·
     `repair_matching_safety` 각 8, `run_topology_pipeline_with_finger_fixup`·`run_full_circuit_audit` 각 7, `l_sharing_classes`·`_metric_kcl_residual`·`_build_theta_evaluator`·`_evaluate_row_split`·
     `_fixup_euler_blocked_rows` 각 6, `true_current_mirror_groups`·`propose_vertical_stack_id_gap_fill`·`find_min_crossover_layout_with_branch_composite` 각 5, `find_matching_candidates`·
     `_diff_pair_layer1_groups`·`_kcl_and_matching_edges`·`_kcl_branch_map` 각 4, `check_symmetry_dispositions`·`run_full_circuit_audit_from_topology` 각 3, `refine_…classify`·`kcl_series_union` 각 2.
   * 사이트 10·14를 B35로 넘긴 효과: `refine_…` 40 → 17, `propose_device_roles_gap_fill` 58 → 52(대상 330 → 301).
   * **착수 base(b26pre + backfill 결함 card 병합 뒤) 대상 299**: backfill card가 `run_matching_safety_with_finger_growth`의 `_backfill_interdig_ok(result)` 두 문장을 base에서 지우므로 v4 head 대상 301 → 299
     (통합 측정 시나리오 A `_drafts/b26_reconcile/out/plan_summary.txt`: 299 = 대응 있음 262 + 새 문장 37). 계약 15 정리 C1·C2 뒤에도 299다(`classify_planC12.txt`). **수는 같지만 대상 4개가 바뀐다**: 정리로 4개가 빠지고(지운 가드의 삭제·cmp_flip, `[0]` const±)
     지운 가드 바로 뒤 문장 1·`open_net`을 읽는 문장 3이 들어온다. 새 4개는 계약 7(e) E1·b26pre가 죽인다(측정 B: E1 3, E1+b26pre 1 -- 계약 15 '판정', `review_b26_final.md` §1.4).
     auditor는 착수 base(그 병합본)에서 도구로 다시 잰다(같은 블록 뒤 문장의 AST 경로 순번이 당겨진다).
   * 면제 누수 대조: 면제 묶기 card 병합 뒤에는 면제가 def 해시에 묶이므로 이 card의 바뀐 def에 옛 면제가 적용되지 않는다(그 card 계약). 이 card는 면제를 쓰지 않는다.
2. **기존 test와 계획된 계약이 죽이는가(모의 실측 2026-10-01)**. 방법은 review2_b26_1 §3 근사 그대로: head 대상 변이 중 **기존 문장**에 걸린 것을 `b1`의 같은 문장 변이로 옮겼다(대응 =
   (연산자, 정규화한 문장 글, 순번). 정규화 = `rails.nets`↔`_RAIL_NETS`, `rails=rails` 제거, 씨앗 dict, SR 두 줄). 실행 = 도구와 같은 pytest 인자 + `-x`, `--gmid-phase=2 --gmid-strict=`(측정 당시 값 -- 판정 명령은 `--gmid-phase=3`),
   `PYTHONHASHSEED=1`, 12개 병렬(벽시계 약 1시간 45분, CPU 합 20.9 h). 각 변이를 먼저 **추가 계약의 b1 근사**(`_drafts/b26_scripts/test_b26x_approx.py` -- 7(e) E1, 4 기본값 E3, 14 E4, 7(a) 양성 E5,
   7(c). b1은 레일을 이름으로 판정하므로 선언 레일 `rail_hi`/`rail_lo` 자리에 `vdd`/`gnd`)로 돌리고, 살면 `b1` 그 def의 기존 인벤토리(`test_ts6_probe_relocate` 2개 제외 -- 사본에 `.git` 없음)로 돌렸다.
   인벤토리 기준 실행 21종 모두 통과. 스크립트 `b26v4_kill.py`·`b26v4_contracts.py`, 결과 `C:/g83/out/kill_v4_N2d.jsonl`(사본 삭제 -- 수치는 여기와 `_drafts/b26_1_revision_log_v4.md`).
   * v4 대상 301 = 옮긴 변이 264 + 대응 없는 새 문장 변이 37(새 def `rail_declaration` 14, 선언 획득·연결 파일 검사·`meta["rails"]` 거부·`rail_nets` 거부·사이트 13·B40 문장 23 -- 계약 1·2·3·5·6·13·14가 죽인다고
     판단. 예: B40 `if refined is None` 삭제 → gate 없는 입력에서 다음 줄 `refined["relations"]` `TypeError`, 사이트 13 문장 삭제 → `_static_ref_roles` `NameError`).
   * **통합 측정(2026-10-01, scratch C:/g103 -- `_drafts/b26_survivor_final_question.md` '측정 요약', 원본 `_drafts/b26_reconcile/out/`)**: 옮긴 264 전부를 **기존 test**로 판정했다(187개는 이전 측정의 '죽음' 재사용 --
     엔진 소스 같고 test 집합은 늘기만 함, 77개는 `a796468`+B34 사본에서 다시 실행). **기존 test 죽임 214, 기존 test 생존 50.**
   * 생존 50의 처리(변이마다 head 줄·b1 줄·문장·시제품 판정 -- `_drafts/b26_reconcile/out/survivor_table.md`):

   | 묶음 | 수 | 누가 죽이나 | 변이(head 줄) |
   |---|---|---|---|
   | B26-1 자기 계약 | 26 | 이 card의 계약 test(모의 근사로 실측): 7(e) E1 14, 4 기본값 E3 6, 7(a) 양성 E5 2, 7(c) 1, 'V3 계획' 4 이름 직접 호출 3 | `_metric_kcl_residual` 4271 `early_return`·4298 `rails = …`·4299 `exclude = …` 삭제 3개(인벤토리 0)는 **직접 호출 근사 1 test로 죽음 실측**(`test_b26x_metric_approx.py`) |
   | 기존 동작 test 공백 -- b26pre card(test-only) | 16 | b26pre 계약 1~7(E6 11 + E7 5) | `optimize_full_circuit_budget`·중첩 `_evaluate_row_split` 9411·9413 삭제 각 2(LUT 없는 repair), `_fixup_euler_blocked_rows` 11704·11706·11708 삭제 3, `run_matching_safety_with_finger_growth` 11810·11886·11889·11890 삭제 4; `run_full_circuit_audit` 6875·6877 루프 삭제 2, `resolve_stack_layout` 6578 삭제 1, `propose_vertical_stack_id_gap_fill` 3272 삭제 1, `propose_device_roles_gap_fill` 4512 삭제 1 |
   | 기존 동작 test 공백 -- trace 루프 범위 | 2 | b26pre 계약 11 | `find_differential_pair_candidates` 1563 `range(i + 1, len(chains))`의 `1` const+ 1·`i + 1` arith 1 (바뀐 `ta.source in rails.nets`의 조상 반복문 머리, T4) |
   | 등가 아님 -- 결함(U-BF) | 2 | backfill 결함 card가 문장을 지운다(사용자 결정 "결함으로 고침 (Recommended)") | `run_matching_safety_with_finger_growth` 11809·11888 `_backfill_interdig_ok(result)` 삭제 -- 지운 쪽이 반환 audit과 맞는 `interdig_ok`를 낸다(구별 입력 있음, 독립 검토 재확인) |
   | **등가 변이**(어떤 test로도 죽지 않음) | 4 | 처리 = 통합 질문 Q1 -- 'V3 계획' 3 | `_propose_L_roles` 2161 `if gm_id_roles is None: return None`·2165 `if candidates is None: return None` 삭제 각 1 -- 두 가드는 서로 중복이다(`_propose_gm_id_roles`가 `None`을 돌려주는 유일한 경우가 같은 인자의 `find_differential_pair_candidates`가 `None`일 때다. 하나를 지워도 다른 하나가 같은 `None`을 돌려준다 -- review2 E4의 "가드를 지우면 `TypeError`"는 `_propose_gm_id_roles`에만 맞다, 그쪽 가드 변이는 E4 근사로 죽었다); `propose_device_roles_gap_fill` 4282 `open_terminals[0]` → `[-1]`(바로 앞에서 `len(open_terminals) == 1`); 1563 `range(i + 1, …)` → `range(i, …)`(늘어난 `j == i` 짝은 `a == b`로 모든 위치를 건너뛴다) |

   * 계획대로 다 했을 때(b26pre[trace 포함] + backfill card 병합 base, 시나리오 A -- 대상 299): 시제품 합집합(B26-1 계약 근사 + b26pre + trace + backfill red-green) 생존 61 중 기존 test까지 생존 **4 = 등가 4**.
     계약 15 정리 C1·C2를 더하면(시나리오 C, 측정 아닌 조합 -- def별 대상 id가 A·B와 같음을 확인) **1**(`range` const−).

   review2 §3의 'E6 17 + E7 12 = 29'와의 차이: review2는 deep 변형 대상(`_propose_*` 씨앗 `seeds[ga] = gb` 등, `propose_device_roles_gap_fill` 씨앗 3967·3968)까지 셌다 -- 이 card 규칙(자기 필드)에서는
   대상 밖이다(deep 변형에서만 생존 39개 더: `_build_theta_evaluator` 18, `run_matching_safety_with_finger_growth` 6, `_metric_kcl_residual` 5, `propose_vertical_stack_id_gap_fill`·
   `propose_device_roles_gap_fill` 각 3, `_propose_gm_id_roles`·`_propose_L_roles` 각 2 -- 참고). review2가 E1·E4로 분류한 `[0]` const−와 `_propose_L_roles` 가드 2개는 실측으로 등가다.
3. **남는 생존의 처리 -- 면제를 card가 정하지 않는다(사용자 결정 U3, 질문 `_drafts/b26_survivor_final_question.md` Q1)**:
   * 죽일 수 있는 18(b26pre 16 + trace 2): 앞선 test-only card **b26pre**(`20260930-b26-pre-test-strengthen`, **19 test, 1 파일** `test_b26pre_existing_paths.py`)가 이 경로들의 **기존 동작** test를 먼저 쓴다 --
     B26-1과 무관한 기존 test 공백이므로 이 card의 계약에 넣지 않는다. 그 card가 병합된 뒤 B26-1의 V3에서 이 18개가 죽는다(병합본 test가 인벤토리에 든다).
   * backfill 결함 2: 사용자 결정 U-BF "결함으로 고침 (Recommended)"(2026-10-01) -- backfill 결함 card(`20261001-b26-backfill-interdig-final-audit`, red-green, 승인 기록 id 후보 `20261001-b26-backfill-interdig-fix`)가
     두 문장을 지워 B26-1 V3 대상에서 없어진다(대상 301 → 299, 'V3 계획' 1).
   * 등가 4: test로 죽일 수 없다. **사용자 결정 U3 = Q1 1번 "정리 2줄 + 면제 1 (Recommended)"(2026-10-01)**: 계약 15의 동작 불변 정리 C1·C2로 3개(`_propose_L_roles` 가드 2 -- C1 뒤 남는 가드 삭제는 계약 14 E4가 죽임, `[0]` const− 1)를 없애고,
     정리로 없앨 수 없는 `range(i + 1, …)` const− 1개만 **변이 id@함수 원본 해시 decision 면제**(A1-a 규칙, 판정 범위 축소라 약화 승인 1건 -- 승인 기록 문안은 통합 질문 Q1 '1번이면 남길 면제 승인 기록 문안', id 후보 `20261001-b26-v3-equiv-range`).
     C3(`itertools.combinations`)는 하지 않는다 -- 측정 B에서 새 생존 7. 기각된 대안(Q1 2번): 정리 없이 등가 4개 모두 해시 묶기 면제(승인 기록 1건, id 후보 `20261001-b26-v3-equiv-4`).
4. **새 test 파일의 이름 직접 호출(필수)**: `A/tests/contracts/test_b26_rail_accessor.py`(test-author)는 `sizing_recipe._metric_kcl_residual(spec, ctx)`를 **이름으로 직접** 부르는 test를 둔다(시그니처가
   안 바뀌어 base에서도 호출된다 -- 인벤토리 0 → 1, 실측). 기대값은 계약 6의 가지를 각각 덮게 손으로 계산한다: MOS 부호, `ID` 없음 `KeyError`, `current_source` 아닌 이상원·단자 2개 미만
   건너뜀, `value_amp` `null` 노드 제외, `value_amp` 값 흘림, `exclude_nets` 제외, 선언 레일 제외, 최댓값·빈 경우 0.0, `rail_nets` 키 `ValueError`. (계약 7(d)만으로는 레일 제외 한 가지만
   덮는다.) 이 파일 이름은 `glob(` 사용처의 패턴(`probe_*.py`, `*.topology.json` 등)과 겹치지 않는다('작성 전 실측' 2).
   추가 계약(4 기본값 E3, 7(a) 양성 E5, 7(c), 7(e) E1, 14 E4)과 계약 15(정리 C1·C2)는 모두 **V3 필수 -- 생략 불가**다(위 2의 B26-1 자기 계약 26 중 23을 이 계약들이 죽인다, 나머지 3은 이 항목의 이름 직접 호출). test 모양은 앞 검토의 교훈대로: 이름은 `_b26_` 접두로 유일하게,
   진입점은 test 함수 본문에서 직접 호출, parametrize 이름 문자열·`getattr` 금지.
5. auditor는 착수 시(위 착수 조건의 병합본 base) 도구로 대상·`not_targeted` 수를 다시 재고, 판정 기록 `checks.V3.basis`에 범위 정책·면제 묶기 card id와 U3 결정(b26pre card id, backfill card id, 면제 승인 id)을 적는다.
6. **인계 삭제의 V3 몫(v4)**: 인계는 9·10b·13·B40뿐이라 지운 문장 뒤 문장(T6 가)과 감싸는 문장(T4)만 대상이 된다. 더해지는 대상 def는 중첩 `classify` 하나(대상 2). 사이트 10·14를 B35로 넘겨
   내어쓰기로 생기던 새 문장 블록(review2 E2·E2b 생존 13 + 1)이 없어졌다.

## 결정 필요 항목

* **U1 → 결정됨(2026-10-01)**: V3 처리는 게이트 규칙으로 정했다 -- A1-a "승인 (Recommended)"(면제 묶기 `20260930-v3-exempt-binding`: 면제 = 변이 id@함수 원본 해시, 해시가 같을 때만 적용),
  A1-b "② N2 (Recommended)"(범위 정책 `20260930-v3-changed-stmt-scope`: def 머리 변경은 (b) 좁은 판)와 그 정정 "규칙을 안내에 맞게 넓힘 (Recommended)"(T6 = 같은 블록 뒤쪽에서 바뀐 이름을 읽는
  문장 전부, 반복문 본문이면 그 본문 전체). 원문은 `_drafts/user_decisions.md` A1·A1-b 정정. 이 card는 두 게이트 card 병합 뒤 그 규칙으로 판정한다('V3 계획').
* **U2 → 승인됨(A2, 2026-10-01)**: DEC-60 넷 전환기 종료 + DF-19·DF-26 넷 몫을 MG1에서 분리 + B26-1·B34를 Phase 3 전(기록 문구 'Phase 2 진행 중' -- 병합 시점은 `20261001-b26-phase3-cards`가 'Phase 2 DoD 뒤·Phase 3 M card 전'으로 바로잡는다)에 착수. 한 건의 `target_kind: decision` 승인 기록
  `20260930-b26-before-phase3`(머리 `approval` 줄)이 B26-1·B34를 함께 덮는다. 사용자 원문 "승인 (Recommended)". 질문 범위 = `_drafts/draft_b26_u2_approval_question.md`. 기록은 gate `2d58fd8`에
  커밋됐다. 이 card는 V7 면제가 필요 없다. A2 기록의 `target`에는 변이 id가 없다. D1 극성·D2 MNA는 이 card 밖이다(B26-2·B26-3 착수 조건).
* **U3 → 결정됨(2026-10-01)**: Q1 1번 "정리 2줄 + 면제 1 (Recommended)" -- b26pre 19 test + backfill 결함 수정 + 계약 15 정리 C1·C2 + `range(i + 1, …)` const− 1개만 변이 id@def 해시 면제
  (약화 승인 1건, 기록 `20261001-b26-v3-equiv-range`는 1차 시도 code 커밋 K1 뒤 auditor 측정 해시로 2차 시도 착수 전에 커밋 -- '두 번 시도 절차'). 원문 `_drafts/user_decisions.md` 'B26 묶음 4문항'(질문 원문은 세션 jsonl 그대로 --
  `_drafts/b26_ask_payload.md` Q1과 백틱 유무·'쟽니다' 한 글자가 다르다). = 착수 조건 8의 'Q1 답 기록'(충족). 하위 결정 Q1-BF(backfill)는 U-BF "결함으로 고침 (Recommended)".
* **Q-B34-PHASE → 결정됨(2026-10-01)**: "phase 3 + 정정 기록 (Recommended)" -- B34·b26pre·backfill·B26-1 네 card `phase: 3`, 'Phase 2 DoD 뒤·Phase 3 M card 전' 순서 유지.
  A2 기록 ③의 'Phase 2 진행 중' 문구는 A2 기록을 고치지 않고 decision 기록 `20261001-b26-phase3-cards`가 바로잡는다(design 30 승인·U-03을 기다리지 않는다). auditor V1 명령은 `--gmid-phase=3`.
* **U4 → 결정됨(2026-10-01)**: "추가 승인 1건 (Recommended)" -- decision 기록 `20260930-b26-b40-reason-key`가 B40(`propose_device_roles_gap_fill`의 `refined is None` 분기 반환에서
  `unavailable_reason` 키 삭제)만 덮는다. 분기와 나머지 세 키는 그대로다(계약 14). 문안 `_drafts/approval_20260930-b26-b40-reason-key.md`.
* **U5 → 결정됨(2026-10-01)**: "갱신 승인 (Recommended)" -- P9 계약 test 2개의 시그니처 단언을 새 기대(원래 두 매개변수 + 키워드 전용·기본값 없음·주석 `RailDeclaration`인 `rails`)로
  갱신한다(계약 12 넷째 항목, review2_b26_1 B3). `target_kind: diff` 기록 `20261001-b26-p9-signature-update` -- 문안 `_drafts/approval_20261001-b26-p9-signature-update.md`(diff_base·diff_head·target은 1차 시도 test 커밋 T1 뒤에 채운다 -- '두 번 시도 절차').

**승인 줄 배치(언제·어디).** card 머리 `approval:` 줄은 그 id의 기록이 gate `master`에 커밋된 판에만 둔다. 게이트가 실제로 대조하는 것은 판정 기록 `approvals[]`(로더 규칙 6 -- 파일 존재·날짜)와
`checks.V5.basis`의 64자리 해시(병합 규칙 9 -- 새 master 트리의 `target_kind: diff` 기록 `target`)다. 머리 줄은 사람이 읽는 연결이다(이 card는 `gate_change: no`라 `gate_change_ok`가 보지 않는다).

| 순 | 승인 기록 | target_kind | 기록 커밋 시점 | 이 card 머리 `approval:` 줄 |
|---|---|---|---|---|
| 1 | `20260930-b26-before-phase3` | decision | gate `2d58fd8`(충족) | 첫 줄(지금 있음) |
| 2 | `20261001-b26-phase3-cards` | decision | 지금 채울 수 있다 -- 네 card 중 첫 card(B34)의 순서 0 커밋보다 먼저(별도 `Role: doc` 커밋) | 둘째 줄(이 초안에 있음 -- 기록 커밋 전에는 이 card를 커밋하지 않는다) |
| 3 | `20260930-b26-b40-reason-key` | decision | 2와 같은 커밋 또는 그 뒤, 이 card 순서 0 커밋 전(착수 조건 10) | 셋째 줄(이 초안에 있음 -- 2와 같은 조건이라 지금 넣었다. 기록 커밋 전에는 이 card를 커밋하지 않는다) |
| 4 | `20261001-b26-p9-signature-update` | diff | **1차 시도** test 커밋 T1 뒤(auditor 순서 3이 V5 FAIL을 `base_check.json`에 남긴 뒤)·**2차 시도 착수 전**, design 05 §12 'V5 승인 운반'. diff = 1차 base B1..T1의 `test_dup_kcl_edges.py`, target = 그 `weakening_diff.py` 출력 `diff_hash`(= `merge_gate.py diff-hash`). 아래 '두 번 시도 절차' 2 | 5·운반 blob과 **같은 `Role: doc` 커밋**의 card 개정으로 더한다(선례 P5b `7a1e191`, P10b `d6a9778` → `0f23786`) |
| 5 | `20261001-b26-v3-equiv-range` | decision | **1차 시도** code 커밋 K1 뒤(auditor가 T1+K1에서 `mutants()`로 잰 변이 id@def 원본 해시로, 착수 조건 8)·**2차 시도 착수 전**. 아래 '두 번 시도 절차' 2 | 4와 같은 커밋 |
| (6) | ④ 기존 픽스처 `supply_nets`·`rails=` V5 | diff | 생기지 않을 것으로 실측됨 -- 순수 삽입(`supply_nets` 키, 호출의 `rails=`)은 V5 발견이 아니다(`review_phase3_cards_set.md` (4) 실측: 픽스처·호출만 바꾼 구간 `weakening_diff.py` PASS·발견 0). test-author가 기존 리터럴을 **바꾸거나 지울** 때만 생긴다 -- 그때 1차 시도에서 멈추고 사용자 승인을 따로 묻는다 | 4와 같이 |

주의(4·5·6): `weakening_diff.py`는 발견이 있는 **모든** test 경로를 정렬해 diff 해시 **하나**를 내고(경로마다가 아니라 발견 경로 합집합에 해시 하나, 그 경로 blob 전체를 묶는다), V5 면제를 **head 트리**(`weakening_diff.approved_hashes(root, ns.head)`)에서 찾는다. V3 면제도 head 트리(`mutate_changed._approved(root, ns.head)`)에서 찾는다.
그런데 병합 모양(gate `0f23786` `merge_gate.receive` 1135~1168행)은 `old..M^1` = `Role: test`만의 첫 부모 사슬(`_first_parent_chain(repo, M1, old, …)`), `M^1..M^2` = `Role: code`만, **M 트리 = M^2 트리**, 커밋 집합 = test 사슬 ∪ code ∪ {M, new}(끼어든 커밋 거부)를 요구한다. 그래서 4·5의 기록은 test 사슬·code·M·audit 커밋 어디에도 넣을 수 없고 **시도의 base(old) 쪽 master에 이미 있어야 한다** -- 그런데 그 target은 T(4)·K(5)가 생긴 뒤에야 잴 수 있다.
**한 번의 시도 안에서는 실행할 수 없으므로 두 번 시도를 처음부터 계획한다**(아래). T1에서 `test_dup_kcl_edges.py` 밖의 test 경로나 두 시그니처 test 밖의 단위(같은 파일의 다른 test 포함)에서 발견이 나면 4의 기록으로 V5를 통과하지 못한다 -- 1차 시도에서 멈추고 (6)의 사용자 승인을 따로 받아 두 승인을 함께 인용하는 기록 하나(경로 합집합 `diff_path`)로 쓴다.

**두 번 시도 절차(계획된 재시도, 4·5를 한 번의 운반으로 묶음).** 정본 = design 05 §12 'V5 승인 운반' 행(gate `0f23786` `docs/02-design/features/gain-budget-gmid-sizing.05-role-separation.design.md` 399행, 원문):
"test 내용이 정해진 뒤 받는 V5(기준 약화) 승인은 병합 판정이 head 트리에서 찾으므로 1차 시도에서 2차 시도로 운반한다(2026-09-22 `10-test-separation` R1, U-42): (1) 1차 시도 순서 1~3, auditor가 `weakening_diff.py` 출력을 `base_check.json`에 남기고 V5 FAIL로 멈춘다 (2) 정리 **전에** 발견 경로마다 `git -C $W/<id>-test cat-file blob <T>:<path> > docs/03-analysis/<feature>-<design>/v5-carry/<id>/<blob id>.blob`(파일 이름은 blob id -- 판정 환경 이름 회피)와 대응표 `v5-carry/<id>/paths.tsv`(`<path>` 탭 `<blob id>`), 사용자 승인 뒤 승인 기록(`diff`, `diff_base` = base, `diff_head` = T, `diff_path` = 발견 경로, `target` = diff 해시) -- 정리 뒤 `Role: doc` 커밋·gate push (3) 2차 시도에서 test-author가 `paths.tsv`대로 `.blob`을 `cp`로 원래 경로에 두어 같은 blob을 만든다(diff 해시는 blob id라 같다, `00-common` §8.2) (4) 그 card 병합 뒤 운반 디렉터리 삭제(`Role: doc`)".
이 card는 그 절차에 V3 면제(5)를 함께 싣는다 -- §12 (1)은 V5 FAIL에서 멈추지만, 이 card의 1차 시도는 **병합하지 않는 계획된 측정 시도**라 순서 5(K1)까지 가서 V3 면제 target도 같은 운반에서 얻는다(1차 시도를 순서 3에서 멈추면 5가 또 한 번의 재시도를 부른다).

| 단계 | 누가 | 할 일 | 멈춤 조건 |
|---|---|---|---|
| 1. 1차 시도(병합 안 함) | 전 역할 | base B1(착수 조건 충족 master)에서 순서 0~3 그대로 → T1. auditor 순서 3이 `weakening_diff.py --base B1 --head T1`을 `base_check.json`에 남긴다 -- 기대: FAIL, 발견 = 두 시그니처 test '비교 완화'뿐, `diff_paths` = [`skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py`]. V5 FAIL은 예정된 것이라 순서 5(code-author → K1)까지 진행하고, auditor가 병합 후보 상당에서 V3를 잰다 -- 병합 커밋을 만들지 않고 `mutate_changed.py --base B1 --head K1`로 잰다(병합 모양이 M 트리 = M^2 트리를 요구하고 M^2 = code 끝 K1이며 K1은 T1 위에 있으므로 K1 트리 = 병합 후보 트리. 1차 audit worktree에 병합 상태를 남기지 않는다 -- review_b26_1_two_attempt m2). 출력(변이 목록·생존 id·def 원본 해시)은 `--out`으로 audit worktree 안 `.ai/verification/20260930-b26-rail-accessor-set/attempt1_v3.json`에 쓴다(단계 2 (a)가 보관) -- 기대 생존 = `find_differential_pair_candidates` `range(i + 1, …)` const− 1개(U3) | 발견 경로·단위가 위와 다르면 멈추고 (6) 승인을 묻는다. V3 생존이 그 1개가 아니면 멈춘다(계약·test 결함 -- 재설계). V1·V2·V4 등 다른 검사 FAIL도 멈춘다 |
| 2. 운반(추출·보관은 1차 정리 **전**, 커밋·push는 정리 **뒤**) | 오케스트레이터 | 아래 (a)→(b)→(c)→(d) 순서를 바꾸지 않는다. 운반 디렉터리 `D = docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/v5-carry/20260930-b26-rail-accessor-set/`(아래 '운반 경로'), 보관 디렉터리 `A = _drafts/b26_1_attempt1/`(저장소 밖, P10b `p10b_attempt1/` 선례).<br>**(a) 정리 전 -- 추출·보관(쓰기는 전부 메인 worktree의 `D`와 저장소 밖 `A`, 커밋 없음).** ① §12 (2)대로 발견 경로마다 `git -C $W/20260930-b26-rail-accessor-set-test cat-file blob T1:skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py > D/<blob id>.blob`, 대응표 `D/paths.tsv`(`<path>` 탭 `<blob id>`). 같은 `.blob`·`paths.tsv` 사본을 `A/v5-carry/`에도 둔다(push 전 사고 대비). ② 1차 시도 커밋 id(B1·T1·K1)를 `A/commits.txt`에. ③ `git show K1:<SD 경로>` 사본(`A/K1_SD.py`)과 `git -C <메인> show T1 > A/T1.patch`(T1의 test 변경 전체 -- 2차 test-author가 P9 밖 test 파일을 다시 쓸 때 읽는 출처, 단계 3). ④ **1차 auditor 산출물**(커밋되지 않아 정리 때 사라진다 -- 아래 '1차 산출물 보관'): `<audit worktree>/.ai/verification/20260930-b26-rail-accessor-set/base_check.json` → `A/attempt1_base_check.json`, 같은 디렉터리의 `attempt1_v3.json`(단계 1의 `--out`, 변이 목록·생존 id·def 원본 해시) → `A/attempt1_v3.json`, 그 밖에 auditor가 그 디렉터리에 남긴 원출력 전부(V1~V4 출력, 변이 목록 파일)를 `A/attempt1_audit/`로 그대로 복사. ⑤ `sha256sum` 목록 `A/SHA256SUMS`(①~④ 전부). ⑥ 승인 기록 4·5 작성(메인 worktree, 미커밋): 기록 4 `diff_base` = B1, `diff_head` = T1, `diff_path` = P9 경로, `target` = `A/attempt1_base_check.json`의 `diff_hash`; 기록 5 `target` = `A/attempt1_v3.json`의 변이 id@def 원본 해시. 두 기록 `merge_gate.py parse-approval` exit 0.<br>**(b) 정리** -- design 05 §12 '정리' 행(gate `5f643a9` 397행, 재시도 형태 원문: "`git worktree remove [--force] $W/<id>-{test,code,audit}`, `git branch -D role/{test,code,audit}/<id>`. … `--force`는 이 세 경로에만(§12-3 미커밋 기록·중단된 병합이 남은 재시도 정리, ⑤ 재생 D-3)"): audit worktree에 미커밋 `base_check.json`이 남아 있으므로 `git worktree remove --force` 세 경로, `git branch -D role/{test,code,audit}/20260930-b26-rail-accessor-set` 세 개. 정리 뒤 `git for-each-ref refs/heads/role/` 출력 0줄 확인. (`branch -D` 뒤에도 T1·K1 객체는 gc 유예 안에서 읽힌다 -- review_b26_1_two_attempt 모의 `cat-file -e` 0. 그래도 2차는 `A`의 사본을 쓴다.)<br>**(c) `Role: doc` 커밋 하나** = 두 기록 + `D`의 운반 blob·`paths.tsv` + card 개정(머리 `approval:` 줄 넷째·다섯째, '1차 시도 기록' 문단 -- `A`의 파일 이름과 sha256을 인용).<br>**(d) push** -- `git push gate master:master` 단독 실행·전체 출력 확인. 정리(b)가 먼저여야 한다: EL1 `role_hooks._judge_push`(gate `5f643a9` `tools/gates/role_hooks.py` 808~811행 -- `if is_main and args == ["gate", "master:master"]: rb = _role_branches(hc); if rb: _deny(hc, "진행 중인 변경이 있어(역할 브랜치 %s) 문서 커밋 push를 거부한다(review29 Q-08)" …)`)는 `refs/heads/role/`에 브랜치가 하나라도 있으면 메인 push를 거부한다(review_b26_1_two_attempt B1 -- scratch에서 이 함수를 직접 불러 확인). 정본 §12 (2)의 "정리 **전에** [추출] … 정리 뒤 `Role: doc` 커밋·gate push"와 같은 순서다 | 기록 파싱(`merge_gate.py parse-approval`) 실패면 (b) 전에 멈춘다(1차 브랜치가 남아 있어 다시 잴 수 있다). (a)④의 `base_check.json` 또는 `attempt1_v3.json`이 없으면 (b) 전에 멈춘다(기록 4·5 target의 출처가 사라진다). push 거부면 출력 전체를 보고하고 멈춘다(재시도 루프 금지) |
| 3. 2차 시도 | 전 역할 | base B2 = 2의 master. 착수 전 오케스트레이터가 `git diff --quiet B1 B2 -- skills/analog-gmid-design/assets/tests/contracts/test_dup_kcl_edges.py`(P9 경로 base blob 같음 → 해시 식 입력 같음). **test-author**는 `paths.tsv`대로 운반 `.blob`을 `cp`로 원래 경로에 둔다(P9 파일은 손으로 다시 쓰지 않는다 -- 1바이트라도 다르면 해시가 바뀐다). 나머지 test 파일은 T1과 같은 내용으로 다시 쓴다 -- 출처는 단계 2 (a)③의 `_drafts/b26_1_attempt1/T1.patch`(`git show T1` 전체. T1은 `Role: test` 커밋이라 test 분류 파일만 담는다 -- §6.4 소스 열람에 걸리지 않는다)이고, 그 patch의 `+` 줄로 최종 내용을 Write 도구로 쓴다(`git apply`·`patch`·cherry-pick 금지 -- `REF_MOVE`·show→Edit 원칙. 새 파일은 Write, 기존 파일 변경은 Edit). patch 안의 P9 경로 hunk는 무시한다(그 파일은 `.blob` `cp`만). 1차 브랜치가 지워졌으므로 `git show T1:<path>`에 기대지 않는다(gc 유예 안에서는 읽히지만 보관 사본이 정본). V5 발견이 없으므로 blob이 달라도 V5는 무방하고, 같으면 auditor 대조가 싸다. **code-author**는 K1의 면제 대상 def(`find_differential_pair_candidates`)를 단계 2 (a)③의 사본 `_drafts/b26_1_attempt1/K1_SD.py`(정본. `git show K1:<SD 경로>`는 gc 유예 안에서만 읽힌다) → Edit로 **같은 글자**로 만든다(역할 agent에 cherry-pick/apply 금지 -- show→Edit). 나머지 code 변경도 K1과 같게 | B1 ≠ B2인 P9 blob이면 멈추고 1부터 다시. def 원본 해시가 기록 5와 다르면 기록 5가 자동 무효(착수 조건 8 마지막 문장) → 재승인 |
| 4. 2차 판정 | auditor | 순서 3·6: V5 base B2..병합본 `approved: true`, 해시 = 기록 4 target(basis에 "B1·B2 사이 P9 blob 같음"을 적는다 -- P5b 판정 기록 V5 basis 문장 모양). V3 exempt 1(기록 5), 나머지 killed. V1 명령 `--gmid-phase=3`(V1 `-c` 캐시 경로의 old = **B2** -- 모의에서 B1을 적어 EL4가 거부했다). 1차 근거는 오케스트레이터가 넘긴 `_drafts/b26_1_attempt1/`의 `attempt1_base_check.json`·`attempt1_v3.json`(`SHA256SUMS` 대조 뒤)을 판정 기록에 옮겨 싣는다(P5b 선례 `attempt1_base_check.json`) | 해시가 다르면 기록을 쓰지 않고 멈춘다 |
| 5. 정리 | 오케스트레이터 | 병합 뒤 운반 디렉터리 `D` 삭제(`Role: doc`, §12 (4)) | -- |

**운반 경로(고정 -- review_b26_1_two_attempt m3).** 정본 문구 design 05 §12 (2): "`docs/03-analysis/<feature>-<design>/v5-carry/<id>/<blob id>.blob`". 이 card에서는
`<feature>` = `gain-budget-gmid-sizing`, `<design>` = `20-dead-code-dup`, `<id>` = `20260930-b26-rail-accessor-set` →
**`docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/v5-carry/20260930-b26-rail-accessor-set/`** (`<blob id>.blob` + `paths.tsv`).
근거: 이 card를 덮는 design 문서가 없고(옛 머리 design 20 승인은 뺐다) 게이트는 `docs/03-analysis/**` 아래 이름을 가리지 않으므로(모의에서 임의 이름도 받음) 디렉터리가 이미 있고 가장 최근 운반 선례 두 건이 쓴 곳을 고른다 -- P5b `7a1e191`(`…-20-dead-code-dup/v5-carry/20260923-d-delete-telescopic/`), 복원 card `04c7248`(`…-20-dead-code-dup/v5-carry/20260930-restore-plan-functions/`). 운반 위치일 뿐 이 card를 design 20 소속으로 만들지 않는다. 2차 test-author 브리핑의 `cp` 원본 경로도 이것이다.

**1차 산출물 보관(review_b26_1_two_attempt S1).** auditor 정의(`agents/gmid-verification-auditor.md` 48~49행)상 순서 3 결과 `base_check.json`은 audit worktree의 `.ai/verification/<id>/`에 쓰고 커밋은 순서 7인데, 1차 시도에는 순서 7이 없어 정리((b) `worktree remove --force`) 때 사라진다.
기록 4의 target(`diff_hash`)·기록 5의 target(변이 id@def 원본 해시)과 2차 판정 기록이 인용할 1차 근거가 모두 여기서 오므로 단계 2 (a)④에서 `_drafts/b26_1_attempt1/`로 먼저 복사한다(정리 전). 보관 목록: `attempt1_base_check.json`, `attempt1_v3.json`(변이 목록·생존 id·def 원본 해시), `attempt1_audit/`(auditor 원출력 전부), `commits.txt`, `K1_SD.py`, `T1.patch`, `v5-carry/`, `SHA256SUMS`.

예상 시간 비용: 1차 시도는 병합만 빼고 순서 0~5와 V3 측정 1회를 다 한다 -- V3는 모의 측정에서 12개 병렬 벽시계 약 1시간 45분(CPU 합 20.9 h, 'V3 계획' 2)이므로 1차 시도에 이 V3 1회 + 역할 agent 작업(test·code) 1벌이 더 든다. 2차 시도의 test·code 작업은 `cp`·show→Edit라 짧지만 V3(약 1시간 45분)와 V1 전체 pytest는 다시 돈다.
결론: **한 번 시도 대비 V3 측정 1회(약 2시간)와 1차 test·code 작업 1벌, 운반 `Role: doc` 커밋 1건이 더 든다.** 대안(1차를 순서 3에서 멈추고 p9만 운반)은 V3 면제(5)가 세 번째 시도를 부르므로 더 비싸다.

착수 조건(순서 P9 → P10 → P10b → Phase 2 DoD → V3 면제 묶기 → V3 범위 정책 → B34 → b26pre → backfill 결함 card → B26-1):
1. A2 승인 기록 `20260930-b26-before-phase3`이 gate에 있다(`2d58fd8`, 충족).
2. 계획 정정 커밋(`draft_b26_plan_patch.md`) -- gate `8356c1e`(충족).
3. P9 병합(`b7765b0`, 판정 기록 `766b5c2`, 충족).
4. P10(`20260930-p10-df23-inventory`)·P10b 병합(사용자 순서).
5. **`20260930-v3-exempt-binding` 병합**(면제 묶기 게이트 card). 명령: `chk 20260930-v3-exempt-binding` → exit 0.
   **5~7·10 기계 확인 공통**(`chk` 정의는 여기, 6·7·10이 같은 `R`·`H`·`chk`를 쓴다 -- 11과 같은 `H=$(git -C "$R" rev-parse gate/master)` -- MSYS2가 `gate/master:…` 인자를 깨뜨리므로 늘 40자리 sha로 먼저 푼다. 병합 = 그 card 판정 기록이 gate `master` 트리에 있고 V1~V10 `verdict`가 전부 PASS 또는 N/A):
   `J='import json,sys; d=json.loads(sys.stdin.buffer.read().decode("utf-8")); c=d["checks"]; sys.exit(0 if d["id"]==sys.argv[1] and len(c)==10 and all(v["verdict"] in ("PASS","N/A") for v in c.values()) else 1)'`,
   `chk() { git -C "$R" cat-file -e "$H:.ai/verification/$1.json" && git -C "$R" show "$H:.ai/verification/$1.json" | C:/Python314/python.exe -c "$J" "$1"; }` → 충족이면 exit 0.
   실측(2026-10-01, 격리 복제본 C:/g163, gate `master` = `5f643a9`): 5·6·7 `chk` exit 128(기록 없음), 10 `cat-file -e` exit 128 -- 넷 다 미충족과 일치. 대조: 충족된 3 `chk 20260930-p9-kcl-edges` exit 0,
   `chk 20261001-topology-md-sync` exit 0, `cat-file -e "$H:.ai/approvals/20261001-b26-backfill-interdig-fix.md"` exit 0. 거부 확인: P9 기록의 `"verdict": "PASS"` 8개를 FAIL로 바꿔 넣으면 exit 1, id 인자가 다르면 exit 1.
6. **`20260930-v3-changed-stmt-scope` 병합**(V3 범위 정책 게이트 card -- 이 card의 V3 대상 정의). 명령: `chk 20260930-v3-changed-stmt-scope` → exit 0.
7. **B34 병합**(`20260930-b34-grammar-explicit`. 인계 삭제 분기가 도달 불가가 되는 조건). 명령: `chk 20260930-b34-grammar-explicit` → exit 0.
8. U3 결정(Q1) -- **Q1 답 기록(`_drafts/user_decisions.md`, 2026-10-01 "정리 2줄 + 면제 1 (Recommended)" -- 충족)** + b26pre card(`20260930-b26-pre-test-strengthen`) 병합 + backfill 결함 card(`20261001-b26-backfill-interdig-final-audit`, U-BF 1번) 병합.
   등가 면제 승인 기록(Q1 1번 답 -- 1건 `20261001-b26-v3-equiv-range`)은 **착수 조건이 아니다**: 그 `target`(= B26-1 병합본 AST 경로 id@그 def 원본 해시, 묶기 규칙 `20260930-v3-exempt-binding`)은
   code 커밋 K 뒤 auditor가 `mutants()`로 잴 때만 나온다. 그래서 **1차 시도** K1 뒤 auditor 측정 id·해시로 decision 승인 기록을 써서 2차 시도 착수 전에 커밋하고, 그때 이 card 머리 `approval` 줄을 갱신한다
   ('두 번 시도 절차' 2. 선례: P10b 등가 9 면제 `20261001-p10b-v3-equiv` `d6a9778` → card 개정 `0f23786`). 재시도에서 면제 대상 def(`find_differential_pair_candidates`, 2번이면 4개의 def)가 바뀌면 해시가 달라져 기록이 자동 무효이므로 **재승인이 필요하다**.
9. U5 사용자 승인(P9 시그니처 단언 갱신) -- "갱신 승인 (Recommended)"(2026-10-01, 충족). 승인 기록 `20261001-b26-p9-signature-update`(diff)는 착수 조건이 아니다 -- diff가 test 커밋 T의 변경이라
   1차 시도 T1 뒤·2차 시도 착수 전에 채워 커밋한다('승인 줄 배치' 4, '두 번 시도 절차' 2).
10. U4 B40 추가 승인 -- "추가 승인 1건 (Recommended)"(2026-10-01). decision 기록 `20260930-b26-b40-reason-key`가 gate `master`에 커밋되어 있다(이 card 순서 0 커밋 전).
    명령(위 공통의 `H`): `git -C "$R" cat-file -e "$H:.ai/approvals/20260930-b26-b40-reason-key.md"` → exit 0.
11. card `phase: 3`(Q-B34-PHASE) -- decision 기록 `20261001-b26-phase3-cards`가 gate `master`에 커밋되어 있고 Phase 2 DoD가 PASS했다(확정 순서상 이 card 앞).
    명령(`H=$(git -C "$R" rev-parse gate/master)` 뒤 `"$H:<경로>"` -- MSYS2가 `gate/master:…` 인자를 깨뜨린다): `git -C "$R" cat-file -e "$H:.ai/approvals/20261001-b26-phase3-cards.md"`, 그리고
    `D2=docs/03-analysis/gain-budget-gmid-sizing-20-dead-code-dup/phase2-dod.md; test "$(git -C "$R" show "$H:$D2" | tr -d '\r' | grep -cx '판정: \(PASS\|FAIL\)')" = 1 && git -C "$R" show "$H:$D2" | tr -d '\r' | grep -qx '판정: PASS'` → 둘 다 exit 0.
    파일 존재만으로는 PASS가 아니다(브리핑은 FAIL도 결과 파일에 적게 한다 -- review_b26_1_two_attempt m4). 판정 줄 형식(결과 파일 규약): `## 판정` 제목 바로 다음의 단독 한 줄 `판정: PASS` 또는 `판정: FAIL`(앞뒤 공백·다른 글자 없음, 파일 전체에 정확히 1줄). PASS는 E0~E5 행과 N6.3 1~5가 모두 PASS일 때만이고 auditor가 결과 파일에 쓴다(오케스트레이터는 옮기기만 한다).

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
     **충돌(review2_b26_1 B3, 2026-10-01 재측정 `git show b7765b0:A/tests/contracts/test_dup_kcl_edges.py`)**: 같은 파일 281~298행 `test_kcl_series_union_signature_unchanged`·
     `test_kcl_and_matching_edges_signature_unchanged`가 매개변수 목록을 정확히 `["netlist", "matching_pairs"]`·`["transistors", "matching_pairs"]`로 단언한다 -- B26-1 병합본에서 두 test가 FAIL이다.
     P9 card '의도'의 "함수·시그니처 유지"(spec card `20260930-p9-kcl-edges`)와 이 card 계약 4가 충돌한다. 처리 = 계약 12 넷째 항목(U5 승인 뒤 기대값 갱신). 다른 시그니처 고정 test:
     `grep -rn "signature(" A/tests` → `test_dup_w_calc.py`(무관)뿐(review2_b26_1 §5).
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
   * **V5**: 기존 test에 `supply_nets` 키·`rails=` 인자를 더하는 것은 V5 발견이 아니다(독립 검토 실측 `review_phase3_cards_set.md` (4): gate `0f23786` 판 `weakening_diff.py`는
     리터럴 비교에서 `SequenceMatcher`의 `replace`·`delete`만 발견으로 세고 순수 삽입은 세지 않으며, `rails=` 추가는 `Assert`의 `Compare`를 바꾸지 않는다 -- 픽스처 12개·호출만 바꾼 구간 PASS·발견 0).
     test-author가 기존 리터럴을 바꾸거나 지울 때만 발견이 나고, 그때는 1차 시도에서 멈추고 오케스트레이터가 사용자 승인을 따로 묻는다('승인 줄 배치' (6)). 계약 test(`tests/contracts/`) 중 바뀌는 이름·파일을 참조하는 것은 없다(2 참조).
   * 판정 경로 밖(U-02 3항과 같은 취급): `workspaces/current-reuse-telescopic-ota-report/rerun_symmetry.py`·`stick.py`·`probe_group_split_wiring.py`가 깨진다.
   * 인계 삭제(계약 13·14): `unavailable_reason`을 읽거나 단언하는 test·운영 코드 0곳(`git grep` 7535799 `skills workspaces tools docs/01-plan docs/02-design` -- SD 3531·3535·3540(`propose_theta_kcl_gap_fill`,
     백로그 B39, 이 card 밖)과 3968 정의, 3933 docstring뿐). 조정할 기존 test 0개. B34 계약 test의 `rails=` 추가는 계약 12 셋째 항목이다.
8. **B34 인계 재측정(2026-10-01, `7535799`, scratch C:/g59 -- 측정 뒤 삭제)**: 인계 사이트 줄을 `sed -n`으로 확인했다('의도' 표. B34 card 사이트 표·검토 정정과 일치). 모의 base·head 구성과 V3 수치는 'V3 계획' 1,
   동작 수치는 '재현할 수치' 마지막 항목에 있다. 쓰기 경로: SD 코드·docstring = code-author. `references/analog-grammar-integration.md`의 폴백 서술은 B34가 오케스트레이터 문서 커밋으로 고친다(B34 card '작성 전 실측' 7). 이 card에서 더 고칠 문서는 없다.
   미배선(V7): 지우는 def 0, 새 def 0(인계분) → 면제 불필요.
