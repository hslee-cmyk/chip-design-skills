# 레지스트리 §7 보류 행 배선/삭제 결정 준비 (TS4·B26 이전)

R = `C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills`, A = `R/skills/analog-gmid-design/assets`, SR = `A/sizing_recipe.py`, SD = `A/stick_diagram.py`, 기준 HEAD = gate master `cd64170`.
읽기 전용(저장소·worktree 쓰기 0, git 상태 변경 0). 실측 스크립트는 `C:/g30`(`measure.py` 정의·참조 AST+`git grep -w`, `callers.py` AST 호출 그래프, `lib_measure.py`·`lib_measure2.py` library 9회로 실행)에서 돌렸다. 결과는 아래 표에 옮겼다. **`C:/g30` 삭제는 안전 검사가 막아 남아 있다(사람이 지워야 함).**

대상 25행: 레지스트리 §7 `보류(Phase 4)` 14행 + `보류(Phase 3)` 9행(Phase 3 초안 v2 D-10으로 `보류(Phase 4)`로 넘어갈 행) + `보류(Phase 6a)` 2행.

---

## 0. 결론 요약

| 묶음 | 행 | 기본안 성격 |
|---|---|---|
| **배선** | `validate_theta_declaration_order`, `find_euler_repair_options`, `apply_device_roles_gap_fill` | 원칙 유도(WP-01, 계획 N3.10 MOD2 '선언 순서 게이트', 사용자가 직접 든 미배선 사례) |
| **삭제(엔진에서 제거)** | `estimate_area_budget`, `solve_diode_stack_current`, `load_derived_bounds`(+R0 `derived_bounds_path`), `check_multi_leaf_hub_parity`+`MultiLeafHubParityVerdict`, `audit_vertical_stack_id_euler_feasibility`, `node_pole_estimate`+`signal_path_nodes`(test oracle로 이관), `_invq_newton`+`build_toy_lut`(tests 픽스처로 이관) | 원칙 유도. 단 **계획 소비자 grep이 0이 아닌 행이 셋**(estimate_area_budget: DF-09·TS4 / node_pole_estimate: DEC-25·DF-06 / validate는 배선이라 해당 없음) -- 같은 card에서 계획 정정 |
| **사용자 결정** | 회로 해석 ★ 3건(theta 작성 묶음 4함수, `find_diode_stacks` 묶음 3, `find_differential_and_mirror_forks`) + 기존 승인과 충돌 1건(`check_mirror_symmetry` 묶음 2) | 회로 해석 / 기존 승인 U-02 3항 번복 여부 |
| **이미 승인(6a)** | `lut_conditions_from_npz`, `derived_spec` | `20260930-restore-unwired-until-6a` 그대로. 새 결정 없음 |

**순서상 급한 것**(`prep_phase4_scope.md` §3.8 겹침): `estimate_area_budget`(DF-09·TS4 첫 red) → 삭제로 가면 **TS4의 명시 대상이 사라진다**(아래 §3 D-1 주의), `node_pole_estimate`(DF-06·B26 사이트) → 이관으로 가면 DF-06 사이트 4→3, B26 비운영 사이트 3개 중 1개 소멸, `find_differential_and_mirror_forks`(B26 사이트) → 사용자 결정 대기(B26-4 lint 면제 여부가 걸림), `propose_theta_kcl_gap_fill`(B26 사이트 3곳) → 사용자 결정 대기.

---

## 1. 새로 확인된 사실 (HEAD 실측)

1. **`estimate_area_budget`는 운영 소비자가 구조적으로 없다.** 반환형이 float인데 소비처로 적힌 `select_layout_tool(area_budget: str|None)`은 문자열 `"generous"`만 본다(SD:6998-7025). 입력 `area_priors`는 어느 `SPECS`에도 없고(`workspaces/run_harness.py` grep 0), 유일한 전달 지점 `assign_finger_geometry(area_priors=spec.get("area_priors"))`(SR:9272)도 docstring이 "아직 계산에 쓰이지 않는다"(SD:6073)고 적는다. 계획 DEC-79는 면적을 두 단계(탐색 축 Σ(W·L)+선언 수동소자 / 판정 축 레이아웃 면적)로만 정의한다 -- 이 함수의 packing-density 블렌딩은 제3의 면적 모델이다. `cold_start_alpha=0.65`는 문헌 잠정값(WP-04)이고 식은 DF-09 결함.
2. **TS4의 명시 대상은 사실상 하나다.** tests에서 '자기참조' 표기가 붙은 판정은 `test_s028_estimate_area_budget`(`A/tests/unit/test_selftest_sizing_recipe.py:1785`) 하나뿐이다(나머지 두 건은 diode '자기참조' 연결을 말하는 다른 뜻). 삭제하면 TS4 범위는 V4 lint(`test_lint.py`, 05 design 318행) 산출 목록으로 다시 정해야 한다. redteam 재생 사례 `tools/gates/redteam/cases/e329283-area-alpha/v.json`은 `git e329283:` 원문을 읽으므로 HEAD 삭제와 무관하다.
3. **`audit_vertical_stack_id_euler_feasibility`는 LR8과 전제가 어긋난다.** library 9회로 실행: findings 17건 중 **16건이 `kind_mismatch`**(PMOS/NMOS 혼합 `vertical_stack_id` 그룹 -- current_reuse 10, nmcnr 3, two_stage 3). 계획 LR8 "branch(`vertical_stack_id`, 전기)와 row(물리 행)는 다르다: 물리 행은 (kind, body 넷)으로 먼저 나뉜다" -- 혼합 그룹은 정상 선언이다. 실제 문제는 1건(current_reuse `cmfb_tail`, `resolvable_by_finger_adjustment=true`)이고 이것은 운영 루프가 실제 행에서 잡는다(`_blocked_euler_rows`).
4. **`find_diode_stacks` 대 `is_diode_connected`**(stack_id = 선언 `vertical_stack_id`, 없으면 단독): 8회로에서 같은 집합, **current_reuse만 18 대 16**(`find_diode_stacks`에만 `M58`, `M63` -- 이웃 drain을 gate로 받는 소자). `find_diode_stacks`는 레이아웃 산출물인 `stack_id`가 있어야 동작한다(SD:2923 docstring, `analog-grammar-integration.md:51`) -- S1(레이아웃 전 구조층)의 정본이 될 수 없는 입력 조건이다.
5. **`find_differential_and_mirror_forks`는 운영 함수 `find_verified_differential_and_mirror_relations`가 못 찾는 관계를 낸다.** ports 선언 입력으로 돌린 결과: two_stage_ota(M1/M2 differential, M3/M4·M5/M7 mirror), two_stage_ota_sf 5쌍, ngcc 10쌍, folded 2쌍을 forks만 찾는다(verified는 이 4회로에서 0). 원인 추정: verified는 composite 구조가 같은 branch끼리만 비교하는데 능동 부하(diode 쪽/비diode 쪽)가 비대칭이면 branch 구조가 달라진다. 레지스트리의 "대체됨"은 측정상 성립하지 않는다 -- ★ diffpair/mirror 정본(레지스트리 §2) 공동분석의 입력이다.
6. **`audit_theta_root_direction`은 선언만으로 돌리면 오탐이 난다.** ports의 input 역할 넷만 주면 current_reuse에서 2건(`kcl_tail_M38` 대 `M37a`/`M37b`). 기존 test(S167)는 `feedbacks=("Voc","Voc_des")`를 손으로 넘겨 없앤다. topology `ports`에 feedback 역할 선언이 없다(9회로 전부) -- 배선하려면 feedback 넷 선언(사용자 몫 데이터)이 먼저다.
7. **`propose_theta_kcl_gap_fill`**: theta 미선언 5회로(common_gate 3, ngcc 16, pushpull 6, sf_pushpull 21, two_stage_sf 9 제안)에서 unresolved 0, 제안마다 `r_free_*` 자유 root(placeholder, 사람 확인 필요)가 1~9개. current_reuse는 unresolved 8(M1a/b, M2a/b, M9a/b, M18a/b). 신규 회로를 데이터만으로 사이징 대상으로 만드는 경로(DEC-62)가 지금은 이 함수 말고 없다.
8. **`validate_theta_declaration_order`**: 9회로 전부 위반 0 → 배선해도 library 결과 불변이 예상된다.
9. **`load_derived_bounds`**: 사이드카 `<topology>.derived.json`은 git에 0개, `value_from_achievable`를 선언한 library 회로 0개. 사이드카를 읽는 곳은 그 사이드카를 쓰는 도구 자신(`A/tests/tools/derive_achievable_bounds.py:69`)뿐이고, 엔진은 topology 제약의 `_derived`만 읽는다(`resolve_constraint_references`, SR:7831-7874).
10. **`node_pole_estimate`·`signal_path_nodes`의 유일한 호출자는 승격 test** `A/tests/unit/test_probe_parasitic_pm_all_circuits.py`(138·140·159·184·188·235·236행)다 -- 운영 metric `parasitic_pm_deg`(L2 MNA)의 구간 판정 oracle로 쓴다. 엔진 docstring(SR:4180-4193)은 L1을 "그 값(34.2도)은 무효"라고 적는다. 계획 DEC-25(220행)는 여전히 `node_pole_estimate`를 현재 동작처럼 인용한다(낡은 문장).
11. **`apply_device_roles_gap_fill`은 운영 게이트의 해결 경로로 지정돼 있다.** `require_device_roles_reviewed`(SR:7952에서 `_build_theta_evaluator`가 부름)가 내는 `ValueError` 메시지가 "`apply_device_roles_gap_fill(<path>, result)`로 써서 검토완료로 표시"하라고 안내한다(SD:4784). 코드 호출자는 0이지만 사람 호출 경로다.
12. `check_mirror_symmetry` 삭제는 **이미 U-02 승인 3항**(`20260923-u02-d-list`)에 이름으로 들어 있다("지우면 workspaces 진단 스크립트가 깨진다. 삭제하고 스크립트는 그대로 둔다"). 한편 계획 I-A13(7b)은 "매칭 interdigitation 행에 L이 섞일 때의 좌우 대칭 검사도 없다"를 미해결로 적는다 -- 같은 개념의 소비자 후보.
13. 게이트 함수 5개(`validate_theta_declaration_order`, `check_mirror_symmetry`, `check_multi_leaf_hub_parity`, `audit_theta_root_direction`, `audit_vertical_stack_id_euler_feasibility`)는 `A/tests/contracts/test_ic5.py` `_DOMAIN_TABLE`(47행~, `len == 21` 단언 251행)과 `10-test-separation` design §5.6 영역 표(260~268행)에 행이 있다. **이 중 하나라도 지우면 test_ic5가 FAIL** → 표 행 삭제가 test 변경(V5, DEC-40 승인)이다.

---

## 2. 행별 조사표

열: 위치 = HEAD `파일:줄` / 호출자 = 코드 호출(AST)·docstring 인용은 따로 / 계획·design = 살아 있는 소비자(history·spec card 기록은 소비자가 아니므로 제외) / 리터럴 = 이름·넷 리터럴(topology 무관성).

### 2.1 sizing_recipe.py

| 함수 | 위치 | 하는 일 | 호출자 | 계획·design·문서 인용 | 리터럴 |
|---|---|---|---|---|---|
| `_invq_newton` | SR:1343 | EKV `VP/UT=2(q-1)+ln q` 뉴턴 역산 | `build_toy_lut`(SR:1382)만 | 계획 0. spec card `20260930-d-move-tests` 22행 "workspaces가 쓰고 엔진 docstring이 LUT 관례 예로 인용 -- 보류" | 숫자 0.05·1e-6(뉴턴 하한) |
| `build_toy_lut` | SR:1356 | EKV 합성 4D LUT(toy, VA=5V/µm·Cox 5e-15) | test: `tests/conftest.py:160-161`(`toy_lut` 픽스처), `test_selftest_sizing_recipe.py:339·2263`; 추적 workspaces `current-reuse-telescopic-ota-report/probe_group_split_wiring.py:5·9`. docstring 인용 SR:5·278·11318 | `10-test-separation` design 205행(`toy_lut` 픽스처 정의), references `function-selection-map.md:42`, `sky130-worked-example.md:369·381` | toy 상수 7개(픽스처 전용) |
| `solve_diode_stack_current` | SR:1499 | 직렬 diode 스택 VGS합 = 목표 전압이 되는 전류를 로그축 이분(단조성 미검사) | test `test_selftest_sizing_recipe.py:654` 한 곳. docstring 인용 SR:627·1475·9140, SD:2851 | 계획 plan.md 0. references `analog-grammar-integration.md:384` "세션18 K절에서 4개 회로 중 필요한 곳이 없다고 확인 -- 별도 결정 필요". 레지스트리 §2 '스택 KVL 합' 행 | 없음(기본 범위 `i_bounds`·`gm_id_bounds` 숫자 기본값) |
| `estimate_area_budget` | SR:2765(식 2793-2794) | `A_1D=n_fingers×pitch`, 표본 있으면 `A_1D/density`, 없으면 `(2-α)A_1D`(DF-09) | test `test_selftest_sizing_recipe.py:1791·1799`(TS4 대상). docstring 인용 SD:6074·7015. redteam `e329283-area-alpha`(git e329283 원문) | **계획 DF-09(919행), TS4(561행 "DF-09 등")**, N6.1 Phase 4 범위(DF-01~15), 05 design 318·456행(redteam 사례 설명, 원문 커밋 고정) | `cold_start_alpha=0.65`(문헌 잠정값) |
| `signal_path_nodes` | SR:3880 | gate/source→drain 방향 그래프에서 excite∩sense 도달 내부 노드 | test `test_probe_parasitic_pm_all_circuits.py:138·140·159·184·235`. 기록 원자료 `docs/03-analysis/.../probe_stage_partition.py:643`(D-9 불변 기록). docstring 인용 SR:4193(L2가 필요 없게 만듦) | 계획 plan.md 0(history만) | 없음 |
| `node_pole_estimate` | SR:3917 | 노드별 1차 pole `G/C`(L1), 못 세는 노드 `undetermined` | test 같은 파일 188·236행. docstring 인용 SR:4180 "L1 ... 무효" | **계획 DEC-25(220행) 현재 동작처럼 인용, DF-06(916행) 사이트**. `prep_b26_supply_nets.md` §1.1 3950행(B26 비운영 사이트), `draft_b26_1.spec.md:38` "삭제·배선 결정과 함께 B26-4 lint가 처리" | `_DEFAULT_RAIL_HI/LO` 넷 이름 집합(B26), 광범위 `except (KeyError, ValueError): pass`(SR:3975, DF-06) |
| `validate_theta_declaration_order` | SR:6296 | theta 배열 '선언 순서 = 실행 순서' 계약 위반 목록(읽기 전용) | test `test_selftest_sizing_recipe.py:3013-3061`, `contracts/test_ic5.py:54`. docstring 인용 SR:5663 | **계획 N3.10 MOD2 행(522행) "선언 순서 게이트" 대표 대상**, `10-test-separation` §5.6 260행 | 없음(스키마 키만) |
| `load_derived_bounds` | SR:7712 (짝 `derived_bounds_path` SR:7700, R0) | 사이드카 JSON 읽기 | 도구 `A/tests/tools/derive_achievable_bounds.py:69`(쓰기는 같은 파일 112행) | 계획 0. 레지스트리 143행(`derived_bounds_path` "엔진은 사이드카를 안 읽고 `_derived`를 씀") | 없음 |
| `lut_conditions_from_npz` | SR:4782 | npz의 corner/temp 기록 여부 | test `contracts/test_restore_plan_functions.py:115-143`, `test_d_delete_dead.py:66` | **계획 N3.3 S0(363행), N3.10 MOD1(521행), I-A5(955행 "6a S0에 배선")** | npz 키 이름만 |

### 2.2 stick_diagram.py

| 함수 | 위치 | 하는 일 | 호출자 | 계획·design·문서 인용 | 리터럴 |
|---|---|---|---|---|---|
| `MirrorSymmetryVerdict` | SD:234 | 결과 레코드 | `check_mirror_symmetry` | -- | -- |
| `check_mirror_symmetry` | SD:238 | finger 순서의 좌우 대칭(`pair_map` 기준) | test `test_ic5.py:56`(표), 추적 workspaces `current-reuse-telescopic-ota-report/stick.py:11·165` | **U-02 승인 3항이 삭제 명시**. 계획 I-A13(960행, 개념 소비자 후보: 7b 좌우 대칭 검사 부재). `10-test-separation` §5.6 262행. references SKILL.md:326, `function-selection-map.md:97`, `design-report-spec.md` 5곳, `stick-diagram-euler-layout.md:178·1224` | 없음 |
| `find_idiom_matches` | SD:1061 | analog-grammar Stage1~3 원본 Match | `audit_theta_root_direction`(SD:3386), `propose_theta_kcl_gap_fill`(SD:3537) -- 둘 다 D. `find_matching_candidates(idiom_matches=)` 인자는 운영 호출자가 안 넘긴다 | references `analog-grammar-integration.md` 12곳, SKILL.md:451 | 없음 |
| `find_differential_and_mirror_forks` | SD:1287 | 하향+상향 branch tree의 첫 fork 쌍을 mirror/differential로 분류 | test `test_selftest_stick_diagram.py:426·2929`. docstring 인용 SD:1251·1634·1652(verified 쪽이 '대체' 서술) | 계획 0. `prep_b26_supply_nets.md` §1.2 1355행(B26 비운영 사이트) | `"vdd"`/`"gnd"` 방향 라벨, `"INPUT"` 넷 클래스 |
| `MultiLeafHubParityVerdict` | SD:2800 | 결과 레코드 | `check_multi_leaf_hub_parity` | -- | -- |
| `check_multi_leaf_hub_parity` | SD:2806 | leaf별 finger 수 홀짝으로 hub 병합 오일러 가능성 공식 스크리닝 | test `test_ic5.py:58`, `test_selftest_stick_diagram.py:1436·1466`(공식 = 실제 `build_graph`+`check_euler_condition` 64조합 일치 확인). docstring 인용 SD:2657·2659·6224 | `10-test-separation` §5.6 264행. references `design-report-spec.md` 4곳, `stick-diagram-euler-layout.md` 6곳, `function-selection-map.md:69`("최종 채택 전 build_graph로 반드시 재확인") | 없음 |
| `DiodeStackMember`/`DiodeStack` | SD:2910/2918 | 결과 레코드 | `find_diode_stacks` | -- | -- |
| `find_diode_stacks` | SD:2923 | 같은 `stack_id` 안에서 gate가 자기 또는 이웃 drain인 소자 | test `test_selftest_stick_diagram.py:2255·2281`. docstring 인용 SR:1428·1502 | 레지스트리 §2 diode 행 ★. references `analog-grammar-integration.md` 9곳(§7 "find_hub_merge_candidates 배선 적용 불가로 결론") | 없음(단 `stack_id` 필요) |
| `audit_theta_root_direction` | SD:3341 | theta A/A_signed feed의 root가 캐스코드 체인에서 방향이 거꾸로인지 lint | test `test_ic5.py:60`, `test_selftest_stick_diagram.py:542·4148-4204` | `10-test-separation` §5.6 266행, `analog-grammar-integration.md:476`, `analog-grammar/assets/idioms.py:28` | 없음. 단 입력 넷 역할(inputs/feedbacks)을 호출자가 넘김 -- feedback 선언 없음 |
| `propose_theta_kcl_gap_fill` | SD:3442(346줄) | connectivity+idiom 고정점 규칙(1 diffpair 50/50, 2 캐스코드 추종, 2.5 declared mirror, 2.7 gate mirror, 3 KCL 합, 4 자유 root)으로 theta 전류 구조 제안 | test `test_selftest_stick_diagram.py:553-581·4221-4277` | `known-incidents.md:436`, library `nmcnr_amplifier.topology.json` `_comment` 4곳(이 함수 제안으로 채웠다는 기록) | `_RAIL_NETS`(SD:3559·3561·3719, B26), placeholder 0.5·1e-5 |
| `apply_theta_kcl_gap_fill` | SD:3790 | 위 제안을 topology.json `sizing_roles.theta`에 병합 기록 | test `test_selftest_stick_diagram.py:4332` | -- | 파일 쓰기 |
| `apply_device_roles_gap_fill` | SD:4553 | `device_roles`·`matching_pairs` 제안을 topology.json에 기록(검토완료 표시) | test `test_selftest_stick_diagram.py:3925·3942·3995·4066`. **운영 게이트 메시지가 해결 경로로 지정**(SD:4784, `require_device_roles_reviewed` ← SR:7952) | -- | 파일 쓰기 |
| `audit_vertical_stack_id_euler_feasibility` | SD:4832 | 선언 vsid 그룹이 그 자체로 오일러 실현 가능한지 + 1순위 finger 조정 실검증 | test `test_ic5.py:62`, `test_selftest_stick_diagram.py:462·3448·3508` | `10-test-separation` §5.6 268행 | 없음. 전제가 LR8과 충돌(§1-3) |
| `find_euler_repair_options` | SD:5096 | blocked 그룹을 (1) 같은 행 finger 조정 실검증 (2) 후보 행 병합으로 푸는 선택지 | test `test_selftest_stick_diagram.py:3532·3539·3557` | 계획 plan.md 0. **사용자 메모리의 '미배선 죄' 반복 사례로 명시된 함수** | 없음 |

### 2.3 기타

| 함수 | 위치 | 하는 일 | 호출자 | 계획 | 리터럴 |
|---|---|---|---|---|---|
| `derived_spec` | `workspaces/run_harness.py:375` | `canonical_spec` 복사 + override + `_spec_source` 기록(why 필수) | test `contracts/test_restore_plan_functions.py:192-304`. 짝 게이트 `require_declared_spec_source`는 운영(SR:7617, 호출 SR:7943) | **DEC-26(221행) "변형은 `derived_spec(why 필수)`로만"** | 없음 |

---

## 3. 제안표 (일괄 승인용)

### 3.1 배선 (원칙 유도)

| # | 함수 | 배선 지점(호출자 · 대체하는 것) | 필요한 증거 | E-LIB 영향(예상) | card 후보 |
|---|---|---|---|---|---|
| W-1 | `validate_theta_declaration_order` | `_build_theta_evaluator`(SR:7930) -- `load_topology`(7944)·`require_device_roles_reviewed`(7952) 바로 뒤, **파생 L-class theta를 붙인 뒤의 최종 `thetas`**로 검사하고 위반이 있으면 거부(CC-4 전에는 옆 게이트와 같은 `ValueError`, CC-4 뒤 N3.14 클래스). **대체**: 지금은 `for theta in thetas` 루프가 순서 위반을 `KeyError`나 stale `ctx.sized` 복제로 조용히 넘긴다(docstring 6296-6330 사고 2건) | red: library topology를 로드해 theta 순서만 뒤바꾼 픽스처(WP-07)가 evaluator 생성에서 거부됨. 무동작: 9회로 위반 0(실측) → E-LIB·E-INST 해시 동일 | 없음(위반 0) | `theta-order-gate`(red-green). Phase 3 MOD2 이동 뒤 |
| W-2 | `find_euler_repair_options` | `run_topology_pipeline_with_finger_fixup`(SR:11887) -- `fix["applied"]`가 거짓일 때 그룹 분할 폴백(11984) **앞**에서 `find_euler_repair_options(row_transistors, sorted(row_names), row_pairs)`를 부르고, `same_row_fix`가 있으면 그 실검증 제안을 overrides에 적용하고 `continue`, 없으면 `merge_candidates`를 `fixup_rounds` 기록에 남기고 기존 분할로. **대체**: 같은 행 조정으로 풀리는데 분할·`max_rounds_exceeded`로 끝나는 경로(Test S146 실사례 `cmfb_tail`·`biasgen_ref`) | red: S146 두 blocked 그룹(파일 로드 입력)에서 현 루프가 분할/미해결로 끝나고 배선 뒤 같은 행에서 풀림. 사이징 대상 4회로 E-INST 전후(unresolved_row·group_splits 수, 행 배치) -- auditor. DUP 루프 `_fixup_euler_blocked_rows`(SR:11663)에는 넣지 않는다(§2 정본은 위 함수) | 동작 변경 가능(행 분할 감소) -- DEC-47 측정, 달라지면 DEC-40 | `euler-repair-wire`(red-green). **D-5(vsid 감사 삭제)와 같은 card 권장** -- vsid 감사의 유효 부분(cmfb_tail)을 이 배선이 대체 |
| W-3 | `apply_device_roles_gap_fill` | 운영 게이트 `require_device_roles_reviewed`(SR:7952)의 해결 경로. 도구 진입점 하나(`tools/` CLI: 제안 계산 → 기록)를 만들고 게이트 메시지가 그 명령을 가리키게 한다. **대체**: 지금은 사람이 REPL에서 함수를 직접 불러야 하는 문서상 경로 | 도구 test(합성 topology 사본에 기록·재로드 시 게이트 통과), 게이트 메시지 문자열 변경은 V5 | 없음(파일 쓰기는 도구 실행 시만) | `roles-ratify-cli`(red-green). 6a S1 `ratified` 전이(N3.3)가 오면 그 기록 형식으로 흡수 |

### 3.2 삭제·이관 (원칙 유도)

계획 소비자 = `docs/01-plan/.../plan.md`·살아 있는 feature design 본문(history·spec card·판정 기록 제외). 0이 아니면 같은 card에서 정정.

| # | 함수 | 근거(원칙) | 계획 소비자 | 영향·필요한 증거 | card 후보 |
|---|---|---|---|---|---|
| D-1 | `estimate_area_budget` | DEC-79가 면적을 두 단계로만 정의(제3 모델 금지), 소비처 형 불일치(float 대 `"generous"`), 입력 `area_priors` 선언 0, WP-04(α 문헌값). **지울 코드를 고치지 않는다** -- DF-09는 삭제로 닫는다(DF-29 선례) | **2**: DF-09 행(919) → 닫힘·경위 history, TS4 행(561) "DF-09 등" → "V4 lint(`test_lint.py`) 산출 목록"으로 | test `test_s028_*` 삭제(test-author 먼저). SD:6074·7015 docstring 정정. `area_priors` 인자(SR:9272, SD:6042)는 예약 필드로 남음 → 백로그. **TS4는 명시 대상이 없어지므로 TS4 card 작성 전 V4 lint 실측이 필요**. E-LIB·E-INST 동일 | `d4-delete-unwired`(equivalence) -- **TS4보다 먼저** |
| D-2 | `solve_diode_stack_current` | 선언으로 도달 불가(G-1) → 미래 topology도 코드 수정 없이는 못 쓴다. 적층 diode 운영 해법은 `solve_stacked_diode_pair`(B25, SR:3491 ← 7304). 자기 docstring이 호출 규약 미검증 자인, 단조성 미검사(DF-10 부류). 일반 KVL 해는 N3.6·DEC-71(6b) 몫 | 0 | test S0xx(`test_selftest_sizing_recipe.py:638-660`) 삭제, docstring 인용 4곳 정정, 레지스트리 §2 '스택 KVL 합' 행 정정, references 1곳(B22). E-LIB·E-INST 동일 | 〃 |
| D-3 | `load_derived_bounds` + `derived_bounds_path`(R0) | 같은 유도값의 두 번째 저장 위치. 엔진은 topology `_derived`만 읽고, 여러 지문 누적은 S3 '유도 임계값'(N3.3, 7b)의 자리 | 0 | 도구 `derive_achievable_bounds.py`에서 사이드카 읽기·쓰기 제거(test-author 영역), `value_from_achievable` 선언 회로 0이라 E-LIB 동일 | 〃 |
| D-4 | `check_multi_leaf_hub_parity` + `MultiLeafHubParityVerdict` | 정본 판정 `build_graph`+`check_euler_condition`과 **항상 같은 답**(test가 64조합으로 증명) → 정보가 없는 사본(WP-14 정본만). 속도용 사전 스크리닝은 cProfile 근거가 없다(WP-10) | 0 | `test_ic5` `_DOMAIN_TABLE` 행 삭제 + `len == 21` 수정(V5, DEC-40 승인), `10-test-separation` §5.6 264행, test 1428-1470 삭제, docstring 3곳, references 12곳(B22가 "build_graph+check_euler_condition로"로 교체) | 〃 |
| D-5 | `audit_vertical_stack_id_euler_feasibility` | 전제(선언 vsid 그룹 = 한 행)가 LR8과 충돌 -- 실측 17건 중 16건이 정상 선언에 대한 `kind_mismatch`. 유효 1건은 실제 행에서 W-2가 처리 | 0 | `test_ic5` 행(V5), `10-test-separation` §5.6 268행, test S144(462·3448·3508) -- S146이 `s144_state`를 공유하므로 test 재구성. `_verified_euler_fix`는 다른 호출자 2곳이 있어 유지 | W-2와 한 card |
| D-6 | `node_pole_estimate` + `signal_path_nodes` → **test oracle로 이관** | 엔진에서 L2(MNA)가 대체, 엔진 docstring이 L1 값 무효 자인. 다만 승격 test가 `parasitic_pm_deg`의 독립 모델 oracle로 쓰고 있어(판정 가치 있음) 지우지 않고 test 쪽 헬퍼로 옮긴다. 옮길 때 레일은 test가 이미 읽는 `supply_nets` 선언(`lsc.declared_supply_nets`)에서, `except ... pass`는 `undetermined` 분류로(조용히 버리지 않는다) | **2**: DEC-25(220행)의 `node_pole_estimate` 문장 → "노드별 근사는 test oracle" 또는 삭제, DF-06(916행) 위치 열에서 제거 | 엔진 B26 비운영 사이트 1개·DF-06 사이트 1개 소멸. test는 판정 불변(헬퍼만 이동) -- V5 판정 대상. 기록 원자료 `probe_stage_partition.py`는 D-9 불변 기록이라 그대로(깨져도 기록) | `pole-oracle-to-tests`(test-author 이관 → code-author 삭제). **DF-06 card·B26-4 lint보다 먼저** |
| D-7 | `_invq_newton` + `build_toy_lut` → **tests 픽스처로 이관** | toy 상수를 가진 합성 LUT는 test 기반(WP-19, 레지스트리 목적지 'tests/ 픽스처'). 테스트를 위해 존재하는 것이 아니라 엔진을 돌리는 test 입력이라 이관이 맞다 | 0 (`10-test-separation` 205행 픽스처 설명의 출처 문구만) | `tests/conftest.py:160` import 변경, SR docstring 인용 3곳 정정(AST 해시 무관), 추적 workspaces `probe_group_split_wiring.py` import는 Phase 3 F1 또는 U-02 3항 방식. E-LIB 동일 | `toy-lut-to-tests`(test-only 이동, `d-move-tests` 선례) |

### 3.3 사용자 결정 필요

| # | 함수 | 왜 사용자 몫인가 | 기본안(제안) | 대안 | 결정이 막는 것 |
|---|---|---|---|---|---|
| U-A | `propose_theta_kcl_gap_fill`, `apply_theta_kcl_gap_fill`, `audit_theta_root_direction`, `find_idiom_matches` (theta 작성 묶음) | 규칙 1~4(diffpair 50/50, 캐스코드 추종, 자유 root 승격)는 회로 해석 규칙(WP-06). `audit_theta_root_direction`은 feedback 넷 선언이 없으면 오탐(실측 2건) -- 선언을 더하는 것은 topology 데이터(ports 역할) | **배선**: device_roles와 같은 운영 패턴 -- `load_topology`(SD:8550)가 theta 미선언·부분 선언 회로에 제안을 메모리로 계산하고, `_build_theta_evaluator`에 `require_device_roles_reviewed`와 같은 '검토 필요' 게이트(자유 root·placeholder가 있으면 거부), 기록은 W-3 도구로. `audit_theta_root_direction`은 ports에 feedback 역할 선언을 허용한 뒤 그 게이트의 보고 항목으로. 근거: DEC-62(새 topology는 데이터만으로) 경로가 지금 이것뿐, 5회로가 theta 0 | **삭제**: 6a S1 `kcl_group` 유도·DEC-71 기둥 조립이 theta 전류 구조를 대체한다고 보고 지움(그러면 6a 전까지 새 회로 사이징 경로 없음) | B26-4 lint(SD:3559·3561·3719 사이트), `find_idiom_matches` 처리 |
| U-B | `find_diode_stacks`, `DiodeStack`, `DiodeStackMember` | ★ diode 정의(레지스트리 §2). current_reuse `M58`·`M63`(이웃 drain을 gate로 받음)을 diode로 볼지 | **삭제**: S1 `is_diode` = `is_diode_connected`(gate==drain, 계획 MOD3 대표 대상, B1 결정). 이웃 관계는 is_diode가 아니라 S1 관계 엣지(6a에서 type 결정)로. 근거: `stack_id`(레이아웃 산출물)가 입력이라 S1(레이아웃 전) 정본이 될 수 없음, 8/9회로에서 결과 동일 | 유지해 6a S1 유도의 '이웃 diode' 엣지 원형으로 이관 | 6a S1 diode 정의, 레지스트리 §2 diode 행 |
| U-C | `find_differential_and_mirror_forks` | ★ diffpair/mirror 정본(레지스트리 §2 '미정'). 운영 `find_verified_...`가 능동 부하 차동쌍을 못 찾는 회로가 4개(실측) | **6a ★ 공동분석까지 유지(비운영 면제)**, B26 작업은 하지 않고 B26-4 lint에서 이 함수만 면제. 측정 결과(§1-5)를 공동분석 입력으로 | **삭제**(docstring대로 fork 단위 비교의 무관 조합 문제, `vdd`/`gnd` 라벨 리터럴) -- 단 유일 검출이 사라진다 | B26-2 극성 라벨·B26-4 lint 범위 |
| U-D | `check_mirror_symmetry`, `MirrorSymmetryVerdict` | 기존 승인 U-02 3항이 삭제를 이름으로 승인 -- 뒤집으려면 사용자 승인 | **7b I-A13 좌우 대칭 검사의 바탕으로 배선**(L 동일성 검사를 더해 MOD8 행 감사에서 호출). 7b까지 미배선 면제(`restore-unwired-until-6a` 형식) | U-02 3항대로 **삭제**(test_ic5 행 V5 포함), I-A13은 7b에서 새로 작성 | 7b I-A13 |

### 3.4 이미 승인됨 (Phase 6a, 새 결정 없음)

| 함수 | 배선 지점 | 근거 기록 |
|---|---|---|
| `lut_conditions_from_npz` | 6a S0 지문 구현 card(MOD3 `circuit_state_graph`, N3.3 S0 'LUT 생성 메타') -- 그 card에서 면제 id 제거 | `20260930-restore-unwired-until-6a`, 계획 I-A5 |
| `derived_spec` | spec 변형이 필요한 첫 운영 사용처(짝 게이트 `require_declared_spec_source` SR:7943은 이미 운영). Phase 4 후보: IC11 원점 이동 비교·U-30 전후 비교를 하네스 변형 실행으로 할 때 | 같은 기록, DEC-26 |

---

## 4. card 배치와 순서

```
[Phase 4 앞머리, TS4 전]
  d4-delete-unwired (D-1·D-2·D-3·D-4, equivalence, 계획 DF-09·TS4 정정 동반)
  pole-oracle-to-tests (D-6, test 이관 → 엔진 삭제, 계획 DEC-25·DF-06 정정)   ── DF-06 card, B26-4 lint 앞
  toy-lut-to-tests (D-7, test-only)                                            ── Phase 3 F1과 묶어도 됨
[Phase 4]
  theta-order-gate (W-1, red-green)
  euler-repair-wire (W-2 + D-5, red-green, E-INST 전후)
  roles-ratify-cli (W-3)
[사용자 결정 뒤]
  U-A 결정 → theta-authoring-wire 또는 d4-delete-theta-authoring
  U-B·U-C → 6a S1 design으로(지금은 면제 기록만)
  U-D → 면제 기록(7b) 또는 d4-delete-unwired에 합류
```

* `test_ic5` `_DOMAIN_TABLE`을 건드리는 card(D-4·D-5, U-D 삭제안)는 한 card에서 표를 한 번만 고치는 게 V5 승인 한 번으로 끝난다 -- D-5를 W-2 card에 두면 표 수정이 두 번 생기므로, **표 행 삭제만 `d4-delete-unwired`에 몰고** W-2 card는 그 병합 뒤에 두는 순서를 권한다.
* Phase 3 D-10(9행 이동 후 D 유지)과의 관계: 여기서 삭제로 정한 행은 Phase 3에서 **옮기지 않고** 지우는 편이 이동 card 수를 줄인다(계획 N3.10 "등급 D 함수는 옮기기 전에 처리한다(Phase 2)" 문구와도 맞다). Phase 3 착수 전에 이 결정이 나면 D0b 배정에서 제외한다.

## 5. 한계

* W-2·U-A의 동작 영향은 실제 사이징 실행(수 분~) 없이 판단했다 -- 이 조사는 로드·구조 함수만 library 9회로에서 돌렸다. E-INST 전후 비교는 card의 auditor 몫이다.
* §1-5의 '능동 부하 비대칭' 원인은 추정이다(코드 docstring과 결과 모양에서). 공동분석 때 재측정.
* `find_diode_stacks` 비교는 stack_id를 선언 `vertical_stack_id`로 준 조건이다(레이아웃 산출 stack_id로는 다를 수 있다).
