### 3.4 현행 결정·제약 목록 (재작성용 인벤토리, 2026-09-14 추출)

> 추출 범위: 계획서 `gain-budget-gmid-sizing.plan.md`(v4.48, 이하 `plan:`), 이력 `gain-budget-gmid-sizing.history.md`(이하 `history:`),
> `.ai/context.md`(이하 `context:`), 메모리 `~/.claude/projects/.../memory/*.md`, 코드 `skills/analog-gmid-design/assets/`(이하 `SR`=`sizing_recipe.py`,
> `topo`=`library/current_reuse_telescopic_ota.topology.json`). 줄 번호는 2026-09-14 작업트리 기준.
> 상태 표기: **구현됨** / **부분 구현** / **유효·미구현** / **유효(원칙)**(구현 대상이 아닌 규칙) / **변경**(후속 결정으로 대체) / **착수 조건**(미결, 해당 Phase에서 결정) / **미확인**.
> 원문 확인이 안 된 것은 "미확인"으로 적었다.

#### 표 A -- 설계 결정 (회로·방법론·엔진 동작)

| # | 결정(사용자 원문 요지) | 날짜 | 원문 위치 | 적용 대상 | 현재 상태 |
|---|---|---|---|---|---|
| A01 | 재설계 방향: "stage를 먼저 나누고 gain을 배분한 뒤 gm_id를 유도" (VDS는 그 뒤) | 2026-09-04 | plan:79-81 | 전체(G2~G7) | **변경** -- gain 인과·배분은 A03/A05로 개정, "VDS는 gm_id 뒤"는 D1 노드전압 정본 writer 티어로 재정식화(plan:1417). 코드는 아직 L→VDS→gm_id 순(plan:1417 인용 `SR:9151→9236`) |
| A02 | stage 안 input+cascode의 L/gm_id를 gain 목표에서 **동시 결정**(캐스코드 L을 role 휴리스틱으로 따로 안 정함) | 2026-09-04 (AskUserQuestion) | plan:208-209 "사용자 확정: 동시 결정", plan:395-396 | G6 내층 | **유효·미구현** -- 형태 변형: stage gain = gm_in/G_out, 블록 DP(gm_id×L)(plan:1416, 1433). `resolve_stage_sizing` def 0(plan:1051-1052) |
| A03 | 인과 방향: ~~gain이 주도~~ → **보상이 (Cc, Rz, gm_1..gm_N)을 먼저 한 번에 결정**, gm_id_i가 자유 축 | 2026-09-04 → 2026-09-07(v4.0) | plan:215-219, plan:397-419, history:3041, context:14050-14052 | G5 | **부분 구현** -- Cc 유도식 구현(topology_library.py:470-489). "보상 먼저 → 3층 할당" 파이프라인은 Phase 7b(plan:1474) 미구현. §15 G5 "v4.0 인과 유지"(plan:1432) |
| A04 | "gain-budget-first"의 뜻 = "gain이 gm을 정한다"가 아니라 **단별 gain 예산을 엔진이 유도해 산출** | 2026-09-07(v4.0) | plan:421-423, context:14051-14052 | G6 | **유효·미구현** |
| A05 | 배분도 엔진이 유도, `gain_budget_db`는 **출력**(예외는 `gain_budget_db_override`만) | 2026-09-07(v3.1) | plan:220-224, plan:424-428, history:1433-1436, history:3037 | G6 | **유효·미구현** -- 해법은 1-D 해찾기→KKT(v3.2)→DP(v4.2)→3층 할당(plan:1421, 1433)으로 교체. `library/`에 `gain_budget_db`·`sizing_spec` 0건(grep) |
| A06 | gain 제약은 폐형식이 아니라 `compute_metric()`/`_METRICS_REGISTRY` **위임** | 2026-09-07(v4.0) | history:1506-1517, context:14053-14054 | G8 | **변경** -- G8 "gain metric은 전체회로 MNA(DM 뷰) 1종, stage gain은 분해 부산물"(plan:1435). 현 파일럿 제약 `gain_db`=`gain_stages_sum`(topo:1884, 2035-2037) → B21 결함 미해결(plan:738) |
| A07 | theta 폐기를 "자유 탐색 변수"로 **축소** -- `A_signed`/`C`/`metric_stage_budget`/servo `B`는 구조 선언으로 존속 | 2026-09-07(v4.0) | history:440-449, context:14055-14057 | G0/G1(유도·선언 필드 분리 plan:1414) | **유효·미구현** -- `*.sizing_spec.json` 0건(plan:1054) |
| A08 | **면적 제약형**: objective는 전력 최소 하나, 면적은 `area_um2` 상한 제약 | 2026-09-07(v3.3) | history:289-293, history:3039 | G0/G6 | **유효·미구현(조건부)** -- 전력 정의가 D6 착수 조건(plan:1196), `Area` 정의 미결 A2(plan:700). 현 파일럿 objective `power_uA`(topo:2030-2031)=`sum_current` 스택 중복계상(plan:1085), area 제약 미선언(topo:2033-2072) |
| A09 | 면적 예산 미선언 시 **Pareto front 제시 후 정지**(엔진이 예산을 지어내지 않음) | 2026-09-07(v3.4) | history:1655-1660, history:3040 | G6/G9(S3 Pareto plan:1433) | **유효·미구현** -- `sweep_area_power_pareto` def 0(plan:1051-1052) |
| A10 | P1 "전면 재설계도 가능하다. 무조건 버그free와 효율성이 원칙" -- 시그니처 무변경 제약 폐기 | 2026-09-07(v3.0) | plan:241-249, history:3036 | 전체 | **유효(원칙)** |
| A11 | P1-b "타당성을 따지지 않고 skip 로직을 만드는 경향이 있어. 그건 금지야." | 2026-09-08 | plan:257-277(원문 plan:259) | 전체, §14.5 A5/A6 | **유효(원칙)** -- 기계 강제(`tools/gates/`)는 미존재(ls) |
| A12 | P2 효율성: 재계산·중복 스캔 구조적 차단, 캐시 키 = 실제 읽는 가변 상태 | 2026-09-07(v3.0) | plan:279-283 | 전체, §12.5.2 C-d(plan:977) | **유효(원칙)** -- 현존 위반 #7·#13(plan:1003, 1082) |
| A13 | P3 기지 사고 재발 불가 -- C1~C10 강제 테스트가 DoD | 2026-09-07(v3.0)/v4.5 | plan:285-288, plan:297-318 | Phase 1 T7(plan:1162) | **유효·미구현** -- 강제 테스트 0건(plan:1055), 저장소 `def test_` 0건(grep) |
| A14 | 요구사항6: 사이징된 **모든** 소자의 KVL/KCL/VGS를 전체 netlist 단위로 상시 검증(최우선) | 2026-09-04 | plan:228-239, history:3031(사용자 지적) | G7 봉인 게이트 + G9 SPICE | **변경** -- 사후 검사기가 아니라 D1 불변식+봉인 게이트(plan:1418). 부분: `propagate_node_voltages`(SR:3895), vsb 게이트(SR:9441). conflicts 미검사(plan:998), `cross_check_with_spice` def 0(plan:1052) |
| A15 | `ideal_sources.value_amp`: **null이면 자유탐색, 값이 있으면 그 값을 실제 전류로** (v4.11 "참고값"을 번복) | 2026-09-08(v4.12) | plan:729(B14), history:3052-3053, context:13964 | G0 사람 선언(plan:1414, 1427) | **부분 구현** -- `_metric_kcl_residual`만 소비(SR:4474-4485). 사이징 경로 소비 없음(plan:729 "엔진 미구현", grep상 소비처는 metric뿐) |
| A16 | 파일럿 Iref 1.2µA는 **사용자가 논문 원문에서 직접 확인**한 값(Claude가 인용한 값과 구분) | 2026-08-03 | 메모리 feedback_no_paper_values_derive_rationally.md(Iref 사례), topo:144 | G0 | **유효(원칙)** -- A15 규약상 고정 대상이나 미배선 |
| A17 | B19'(가) 미러 **18소자 전부 강제** -- tail M5/M6를 bias 미러에 묶는 것이 설계 의도 | 2026-09-09(v4.21) | plan:735, history:3062 | G1/G3(K2) | **구현됨** -- `gm_id_match_vgs_of` 선언(topo:1027, 1036, 1043 등), `diode_vds_window(mirror_members)`(SR:3570, 호출 SR:8018), 착지 history:3072 |
| A18 | B19'(나) 공유 VGS는 **gain 기준**: "첫번째 differential input 단의 tail이기 때문에 gain에 직접적으로 영향을 미치는 id전류를 만들고 있어" | 2026-09-09 | plan:735, history:3062 | G6 중층(plan:1433 "사용자 확정 B19'") | **유효·미구현** -- 좌표강하 없음. pmos:Vcmfb 그룹은 gain 폭 0dB라 기준 미정(plan:735) |
| A19 | B20 승인: `_solve_vgs()`를 **rightmost root**로(비단조 PMOS LUT) | 2026-09-09(v4.23) | plan:736 "사용자 승인 후 수정", history:3064 | G4 LUT 곡선 검사 | **구현됨** SR:522-528. 잔여 #10 이분 역산 단조성 미검사(plan:1079) |
| A20 | B22 승인: diode 창이 VGS 공유 미러 멤버 W까지 확인(선언 옵트인, 미정 vds는 역할별 min_vds 바닥, L/ID 미정은 명시 실패) | 2026-09-09(v4.25) | plan:739 "구현 완료(사용자 승인)" | G7 T1/T2 | **구현됨** SR:3570/8018. "선언 옵트인"은 G1 connectivity 유도(plan:1428)·writer 티어(plan:1417)로 재정식화 대상 |
| A21 | B25 승인: 적층 diode를 **2변수 연립**(`vsb_lo = vsb_up + v_up`) + B9 vsb를 노드전압에서 유도 | 2026-09-09(v4.28) | plan:742 "승인 필요(공유 엔진)… 구현 완료", history:3069 | G7 T2(plan:1417) | **구현됨** `solve_stacked_diode_pair`(SR:3659, 호출 SR:7859), `reconcile_vsb_from_nodes`(SR:3976, 호출 SR:9207), 게이트 SR:9441. 잔여 #1 W·gds 버전 혼재(plan:997), #11 idu=1.0 대입(plan:1080) |
| A22 | diode의 vds는 나눠줄 몫이 아니라 **구간 제약 변수**(헤드룸 배분기 변경, 사용자 승인) + diode gm_id는 종속값(B16) | 2026-09-08(v4.17) | history:913 "(사용자 승인)", history:3057-3058, plan:731 | G7 T1 | **구현됨** `diode_vds_window`(SR:3570), `apply_diode_self_consistent_gm_id`(SR:3743, 호출 SR:9236). B16 개별 승인 문구는 미확인(history:3057 "사용자 승인 후 배선"만) |
| A23 | M11a/M11b/M20a/M20b `L_role`=`bias_replica`(class-AB 배터리 전압기준, 신호경로 미러 아님) | 2026-09-09(v4.27) | history:3068 "사용자 확정" | G1 | **구현됨** topo:1024, 1032, 1041 등 |
| A24 | L5c 픽스처: `r_cmfb_vocdes` 하한(0.02) 고정("1번"), `stop_after_sizing=True`(사용자 선택) | 2026-09-09~10 | history:3071, history:2132-2133 | Phase 1 T0~T2 | **구현됨** -- §14.3 "픽스처 입력 이동 = 기준 약화, 사용자 승인"(plan:1272) 규칙의 적용 대상. 이관 시 재승인 필요 여부 미확인 |
| A25 | 초기 L은 **knee에서 시작**, fT/mismatch/LUT 격자로 clamp, 부족하면 **VDS를 L보다 먼저**(R4b) -- "원칙은 지난번에 정했잖아" | 2026-09-07 | plan:510-533, plan:449, 메모리 feedback_default_from_principles_before_asking.md, history:3089(사용자 확정 원칙으로 존치) | G1/G6 | **부분 구현** -- `measure_L_knee`(SR:2305), `knee_L_for_kind`(SR:2555), `derive_role_L`(SR:2772, clamp `feasible_L_window` SR:2694). `L_bounds_from_ft_and_matching`·`search_gm_id_and_L_for_role`·`L_candidates_product` def 0(grep). fT 상한은 §7.11로 대체 |
| A26 | §7.7 L 변경 규칙 R1~R8(R7 branch/row 구분은 사용자 질의로 명확화) | 2026-09-04 | plan:443-462, history:3032, history:3089 | G1 / 레이아웃 수렴(§13.4 #8) | **유효(원칙)** -- 문장 단위 수정 필요(과제3) |
| A27 | "gain stage의 **tail이 L의 주인**이고, 특히 최초 input 단의 tail이 실제 주인… 두 stage의 gain을 모두 만족시키는 L을 sweep… 나머지 mirror구조로 연결된 소자들은 전부 L을 공유" / "M5가 주인이야" | 2026-09-10 | history:2266-2268, history:3078 | G1(plan:1428 "tail이 L의 주인") | **구현됨** `l_sharing_classes`(SR:2385), `gain_stage_tails`(SR:2434), `l_class_owners`(SR:2490). 한계: `gain_stage_tails`가 3회로에서 `{}`(plan:1406) → G2 유도로 교체 예정 |
| A28 | "L theta를 일반화해. **특정 이름으로 하지마.**" | 2026-09-10 | history:2366-2368, history:3079 | G1/G6 | **구현됨** `synthesize_l_class_thetas`(SR:2612, 호출 SR:8509), `_feed_l_class`(SR:6798). 기존 선언 L theta(`L_cascode`/`L_stage2out_*`) 존폐 결정은 미확인 |
| A29 | 미러 공통 L **3층 구조**("3층 구조는 맞아") + 층0 게이트(동치류 안 L 갈리면 에러) | 2026-09-10 | context:14308-14317 | G1/G7 | **구현됨** 층0 `audit_l_sharing_consistency`(SR:2518) 호출 SR:9454(배선됨 -- history:2356 "미배선"은 stale). 잔여 #3 게이트 `ValueError`가 탐색 크래시(plan:999) |
| A30 | "bias_replica 상수도 없애" → **(1) 전 회로 적용** | 2026-09-10 | history:2447, history:3080, context:14364 | G1 | **구현됨** `_L_ROLE_MULTIPLIERS` 정의 0(주석만 SR:2308/2557/2780), `derive_role_L`. 잔여 #21 `tests/probe_mirror_common_L_wiring.py:66`이 삭제된 상수 참조(plan:1090) |
| A31 | "warm start에 l_class 포함해서 재탐색해" | 2026-09-10 | history:2594, history:3081 | Phase 5 / G9 | **구현됨** `search_stage_budget_L_warm_start`(SR:10637), `_group_score_interior`(SR:10595, 호출 SR:10855), `l_class_L`(SR:11330) |
| A32 | "mirror_ratio_error 상한 걸어" → "상수를 임의로 자꾸 만들지마. 근거가 되는 mismatch_sigma_mV만 유지" → `value_from_constraint` | 2026-09-10 | history:2670-2672, history:3082 | G0 출처 / G8 | **구현됨** topo:2056-2059, `resolve_constraint_references`(SR:8370), `_mirror_ratio_error_pairs`(SR:4551). 잔여 #5 `names[0:2]`만(plan:1001) |
| A33 | `mismatch_sigma_mV=5.0`은 **근거 없음**을 기록, 재도출 방법은 사용자 확정 전 안 정함 → "1번으로 진행해" → 유도 실패 → 시스템 레벨 설계 입력으로 5.0 유지 | 2026-09-10 | history:2744-2763, history:2810, history:2872-2877 | G0 "제약값 출처 필수"(plan:1427) | **유효(근거 공백 지속)** topo:2040-2043. G0 착수 시 출처 결정 필요 |
| A34 | 임계값 **bisection(선택지 3)** 채택, 구현은 design 단계 후 | 2026-09-10 | history:2886-2887, history:3088, plan:809-866 | §15에 Phase 배치 없음(S3 "유도 임계값" plan:965) | **유효·미구현** -- `achievable_metric_bound`(SR:8271)에 bisect 모드 grep 0건 |
| A35 | `input_referred_offset`: **gm 가중 RSS, 캐스코드 제외**(쌍 = offset 선언 ∩ ports input 게이트) | 2026-09-10 | history:2781, history:3083, context:14486 | G8 | **구현됨** SR:4724/4644/4696(호출 SR:8517), topo:1909-1910. 잔여 #12(plan:1081), 다중 diff pair Case B/C 미해결(history:2976-2980) |
| A36 | "**Cc와 Rz는 보상망이 계산해서 확정해야지.**" | 2026-09-10 | history:2208, history:2210-2224 | G5(plan:1432) | **구현됨** topology_library.py:470-489(`Cc = sqrt(beta*tan(PM)*C_Ltot*Cgg2)`) |
| A37 | passive connectivity 추가: CL1/CL2, **Cf1/Cf2(교차)**, Cs1/Cs2 | 2026-09-10 | history:2186-2204 "사용자 확정" | G1 | **구현됨** topo:73-131. 타 회로 passive 누락은 J9(plan:1460) |
| A38 | M18b `budget_reference_device="M17"` 누락 보완(사용자 승인) | 2026-09-10 | history:2126-2129, history:3076 | G1 | **구현됨** topo:1172-1178. §15.4에서 budget_ref 유도 필드화·J8 대상(plan:1414, 1459) |
| A39 | 기생 pole clamp는 **N을 박지 말고 유도**(문헌 조사 사용자 지시, "수치로만 적용하면 이 회로에 특화된 값") | 2026-09-10 | plan:564, plan:606-619, history:3073 | G5 | **구현됨** `_metric_parasitic_pm_deg`(SR:4329), `full_circuit_response_at_omega`(SR:4267), 제약 `>= PM_target_deg`(topo:2067-2070) |
| A40 | **D1 노드전압이 DC 기준값(정본)** -- "D1은 DC기준값으로 해" | 2026-09-14 | plan:1012, plan:1017 | Phase 6b / G7 | **유효·미구현** |
| A41 | spec 정본화 -- "이번 실수가 재발하지 않도록 방법을 강구해" (`canonical_spec`/`derived_spec(why 필수)`/출처 게이트) | 2026-09-10 | history:1932-2000, history:3075 | G0 / S0 지문 | **구현됨** run_harness.py:354, 370; SR:8151, 8172(호출 SR:8492). 변경 예정: 지문 7키→S0 전체(plan:937, 960), 불일치=노트→없음 처리(plan:1004) |
| A42 | class-AB 배터리 기준: `V_bat = vdd − VGS(M15) − VGS(M16)` KVL을 gm_id 탐색 상한으로, 포화 하한은 `2/(gm/ID)` (사용자 선택 2건) | 2026-09-10 | history:2028-2045, history:3076 | G7 | **구현됨** `stack_kvl_vgs_limit`(SR:1835, 호출 SR:6716). M9a/M9b 역할 해석은 J3 공동분석(plan:1454) |
| A43 | 기준점 복구 -- "이 설계에만 적용되는 것은 안 돼. 반드시 일반화된 솔루션을 코드화" | 2026-09-10 | history:2065-2067 | Phase 5 / G9 | **구현됨** `repair_infeasible_baseline`(SR:10959, 호출 SR:11245/11311). 결함 #4 부분문자열 탐지(plan:1000) |
| A44 | "stage를 탐색할 때 역방향으로 탐색하지 않고 언제나 **input ports부터 output ports까지**" | 2026-09-10 | history:2934-2936 | G2 | **변경** -- `flow_dir` 단일 노드 속성 폐기 → S1v 여기 모드별 뷰 + 피드백 극성(plan:947, 962), DM 뷰 R2 규칙(plan:1398). 미구현 |
| A45 | CircuitGraph를 다음 baseline으로(§11) | 2026-09-10 | history:2891-2892 | -- | **변경** -- §12 CSG가 §11 대체(plan:893), §15에서 "graph는 기반"(plan:1373) |
| A46 | 계산 결과(노드전압·신호방향)를 **버리지 않고 재사용·점진 정제·글로벌 최적화** | 2026-09-14 | plan:888-891 | Phase 6 | **유효·미구현** |
| A47 | 파일 분리(3단계 harness) + self-test를 `tests/`로 분리("표준 pytest 관례") | 2026-09-04 | history:1731-1732, history:1745-1746 | Phase 1/3 | **변경** -- 파일표 §13.4(plan:1095-1111), test §13.5(plan:1121-1162), D9 pytest(plan:1199). 미구현: conftest 없음, 인라인 self-test SR:12571 / stick_diagram.py:8991 |
| A48 | `stick_diagram.py` self-test 이관도 범위에 포함 | 2026-09-04(v1.2) | history:1867-1869, history:3029 | Phase 1 T1(plan:1156) | **유효·미구현** stick_diagram.py:8991. "stick_diagram 소스 무변경"(history:1877-1879)은 구조 유도 함수 이관(plan:1108)으로 변경 |
| A49 | "모든 함수를 전수로 훑어… 재사용 함수목록… 화일분리와 self-test 분리 계획도 반드시 명시" | 2026-09-14 | plan:1025-1027 | Phase 0~3 | **부분 구현** -- 레지스트리 문서(Phase 0, plan:1040)만 |
| A50 | "코드를 작성하는 agent와 test를 작성하는 agent를 **반드시 분리**" ("가장 중요한 것") | 2026-09-14 | plan:1204-1207 | Phase 0.5 | **유효·미구현** -- `.claude/hooks/`·`tools/gates/`·`agents/gmid-*` 없음(ls) |
| A51 | D2 순환 블록 허용오차는 LUT 격자·보간 오차에서 **계산** | 2026-09-14(기본안) | plan:1018 | Phase 6 G7 | **유효·미구현** |
| A52 | D3 착수 순서 §13.6+§14.8 | 2026-09-14 | plan:1019 | 전체 | **변경** -- §15.8이 Phase 6·7을 6a~7c로 대체(plan:1466-1475) |
| A53 | D4 전역 샘플 수는 wall-clock ≤ 5분 안에서 실측으로 계산(5분=B4 DoD) | 2026-09-14 | plan:1020, plan:349-351 | G9 | **유효·미구현** |
| A54 | D5 `ports`는 Claude가 connectivity로 **제안 → 표로 확인 → 반영** | 2026-09-14 | plan:1021 | Phase 0 / 6a 착수 조건(plan:1470) | **유효·미구현** -- 파일럿은 존재(topo:159), folded·nmcnr 없음(plan:1408) |
| A55 | D6 목적함수 전력 정의(`sum_current` vs `supply_current`) | 2026-09-14 | plan:1196 | Phase 4 / 7a | **착수 조건** |
| A56 | D7 사장 코드 삭제/배선 목록 일괄 승인 | 2026-09-14 | plan:1197 | Phase 2 | **착수 조건** |
| A57 | D8 구조 개념 정본(diode·미러 키·diffpair/tail) 공동분석 → J1~J9로 확장 | 2026-09-14 | plan:1198, plan:1462 | Phase 4 / 6a | **착수 조건** |
| A58 | D9 test 프레임워크 pytest | 2026-09-04 확정 기록 | plan:1199 | Phase 1 | **유효·미구현** |
| A59 | D10 순서 예외 없음(#3·#18도 Phase 4), 그 전 보고에 두 결함 명시 | 2026-09-14 | plan:1200, plan:1184-1186 | Phase 4 | **유효·미구현** |
| A60 | D11 메인 세션 엔진·tests 편집 L1 금지 / D12 interface card+결과 검사 / D13 자체 AST 변이기 / D14 기준 약화 매 건 승인 | 2026-09-14 | plan:1356-1359 | Phase 0.5 | **유효·미구현** |
| A61 | D15 "D15는 등록해" -- 프로젝트 `.claude/settings.json`에 hook 등록(스크립트 완성·거부 확인 후, `gmid-*` 경로에만) | 2026-09-14 | plan:1012, plan:1360, plan:1336 | Phase 0.5 | **유효·미구현** |
| A62 | "gain budget first의 원래 계획이 **폐기된 것은 아니잖아?** graph를 이용해서 훨씬 더 잘 구현할 계획안" | 2026-09-14 | plan:1367-1375, context:14584-14585 | §15 전체 | **유효·미구현** |
| A63 | "gain분해에 관해서 기존 설계를 구현했을 때 발생했던 문제들을 조사… 보완한 계획도 추가해서 최종안" | 2026-09-14 | plan:1369-1370 | §15.2/§15.5 | **유효·미구현**(계획 반영 plan:1386-1440) |
| A64 | `gain_db` 목표 75.6 → **54dB**(실측 달성점 57.03dB − 3dB, 사용자 승인) | 2026-09-03(세션44) | topo:2029, context:13509 | G0 | **유효(원칙)** -- "마진 상수 없이" bisection 대체 가능 기록(plan:863) → 변경 후보 |
| A65 | bkit 단계 준수: plan에는 기록만, 구현은 design 단계를 거친 뒤(사용자 지적) | 2026-09-10 | context:14514-14515, history:3088 | 전체 | **유효(원칙)** -- plan:1167 "design 문서를 거쳐 착수" |
| A66 | two_stage `stage1_ref`/`stage1_out` 분리는 "여기서 멈춤, 별도 세션" | 세션41 | context:12420 | §10.15 선행(plan:865), 4회로 측정 선행(history:3004) | **유효·미구현**(이월) |
| A67 | 이력 분리(본문 무변경 이동) -- "3번을 먼저하고 다시 제안해" | 2026-09-14 | history:3089 | 문서 | **구현됨** |
| A68 | SLSQP(scipy) + multi-start 채택(사용자 승인) | 세션31 이전 | context:4931 | G6 외층 polish(plan:1433) | **변경** -- 시작점 전략을 아카이브·준난수 전역 샘플로 확장(plan:987-991) |
| A69 | `vs` → `vsb` 개명 | 2026-09-08 | context:14061, context:13984-13987 | G1 | **구현됨** `validate_no_legacy_vs_key`(SR:5790) |
| A70 | L 탐색 = **knee 창 + 경계 검사**(창 가장자리면 확장) | 2026-09-08(v4.7) | context:14058-14059("사용자 결정 사항"), history:3048 | G6 | **변경** -- 실제 L은 l_class theta 연속 탐색 + warm start 격자(A28/A31)로 구현. knee 창 전수 스캔 정책의 코드 존재는 미확인 |
| A71 | A12 metric 이름-단위 불일치 해소(공유 엔진 변경, 승인 필요로 기록) | 2026-09-08 | plan:709, context:13958 | G0/G8 | **구현됨** `validate_metric_units`(SR:5813). 승인 원문 미확인, plan:709 "승인 필요" 표기는 stale |
| A72 | B21(선언 gain 제약이 미러 18소자를 못 봄) 처리 방식 | 2026-09-09 결정 요청 | plan:738, plan:1442-1446 | G8 / Phase 7a | **착수 조건** -- §15.6 기본안(판정=전체회로 gain, 할당=부하 포함 블록 gain), M18a/M19/M18b 포함은 J6 공동분석 |
| A73 | 새 metric 상한은 **4개 회로에서 먼저 재고 정한다**(값을 지어내지 않는다) | 2026-09-08~10 | plan:702, plan:723, plan:671 | G8 | **유효(원칙)** -- `kcl_residual`·`stack_headroom_slack`는 아직 제약 아님(topo:2033-2072) |
| A74 | 파일럿 1개 먼저, 나머지 3개 토폴로지는 이후(§2.2) | 2026-09-04 | plan:17-18, plan:193-194 | -- | **미확인** -- 사용자 확정 원문을 찾지 못함. §4.1 DoD C7(plan:352-354)·§15.8 DoD 4회로(plan:1477)와 범위 충돌(plan:766) |

**표 A 집계(74행)**: 구현됨 24 / 부분 구현 4 / 유효·미구현 23 / 유효(원칙) 9 / 변경 9 / 착수 조건 4 / 미확인 1.

#### 표 B -- 작업 방식 원칙 (메모리·CLAUDE.md)

| # | 원칙 | 원문 위치 | 계획서 반영 위치(§) |
|---|---|---|---|
| B01 | **만들면 반드시 배선**, 대체 불가하면 승인 요구 ("만드는 것을 안 쓰는 것은 죄다") | `~/.claude/CLAUDE.md` ★절대원칙★, 메모리 feedback_build_it_wire_it_or_ask.md | §3.2 P1-b 끝(plan:276-277), §3.3 표 주석(plan:313-314), §14.5 A7 배선 검사(plan:1304) -- **반영** |
| B02 | 우회(skip/continue/예외 목록) 전 타당성 3문항, **광범위 except도 skip**, 게이트는 "거부한다"를 먼저 확인 | 메모리 feedback_no_skip_without_justification.md | §3.2 P1-b(plan:257-277), §14.5 A5/A6(plan:1302-1303), §14.6 거부 확인(plan:1309-1329), D14(plan:1359) -- **반영** |
| B03 | **상수를 임의로 만들지 마라** -- 근거 선언값 하나만 남기고 식을 코드로, 결과는 캐시(유도를 주석에 적고 숫자를 박는 것은 해결 아님) | 메모리 feedback_never_invent_constants_derive_and_cache.md | §7.11(5)(plan:606-619), §12.8 D2(plan:1018), §13.3 #20(plan:1089), §14.5 A6 "근거 필드 없는 새 숫자 리터럴"(plan:1303) -- **반영** |
| B04 | 논문 값 인용 금지, 사용자가 직접 지정한 값만 확정 | 메모리 feedback_no_paper_values_derive_rationally.md | §15.5 G0 "제약값 출처 필수(논문 출처 거부)"(plan:1427) -- **반영(한 줄뿐)** |
| B05 | 해결책은 일반화 -- 회로/소자/theta 이름·매직넘버 금지, **4개 회로 전수 측정으로 무동작 증명** | 메모리 feedback_generalize_never_circuit_specific.md | §15.8 각 Phase DoD(plan:1477), §13.5 `regression/test_four_circuits.py`(plan:1145), §3.3 C7(plan:305) -- **반영** |
| B06 | 회로 위상 **해석**은 항상 공동분석, 공유 엔진 변경은 논의·승인 후 | 메모리 feedback_act_decisively_within_analysis_authority.md | §13.8 D8(plan:1198), §15.7 J1~J9(plan:1448-1462), §13.6 "모든 단계는 승인 후"(plan:1167) -- **반영** |
| B07 | connectivity는 사용자 영역, topology.json이 유일 소스, 테스트에 손타이핑 lookalike 데이터 금지 | 메모리 feedback_topology_json_single_source.md, feedback_act_decisively_within_analysis_authority.md | §12.8 D5 근거(plan:1021)에 "topology.json 유일 소스"만 -- **부분 반영**(§13.5 conftest(plan:1131)에 lookalike 픽스처 금지 명시 없음) |
| B08 | connectivity 정정은 쌓았다가 "한꺼번에 반영" 지시 때 일괄 반영 + 표 재출력 | 메모리 feedback_batch_topology_corrections.md | §12.8 D5 근거(plan:1021) -- **부분 반영** |
| B09 | 회로도 이미지 판독은 부정확 -- net 기준 표(`topology_to_markdown.py`)로 재검증 | 메모리 feedback_schematic_image_reading_unreliable.md | **미반영**(plan grep "net 기준" 0건). §15.7 J9 ports/passive 추가 시 적용 대상 |
| B10 | iteration 안 계산은 쓰는 순간 캐시, 루프 불변식은 밖으로, 메모이제이션 상한 필수, cProfile+중복인자 계측으로 근거 | 메모리 feedback_always_check_recompute_efficiency.md | §3.2 P2(plan:279-283), §12.5.2 C-d(plan:977), §12.5.3(plan:979-983), §14.5 A6 "상한 없는 캐시"(plan:1303), §13.3 #13(plan:1082) -- **반영**(계측 근거 요구는 §12.1 검토 방법(plan:901)에만) |
| B11 | 조사 스크립트는 **결과를 파일에 직접 쓰고 케이스마다 append** | 메모리 feedback_scripts_write_results_to_file.md | **미반영**(plan grep "result.txt"/"파일에 쓴" 0건). §13.5 T6 probe 정리(plan:1161)에 넣을 자리 |
| B12 | 장시간 실행은 `run_in_background:true`(수동 &/nohup 금지) | 메모리 feedback_background_process_tracking.md | **미반영**(plan grep 0건) |
| B13 | **코드 작성자 ≠ 판정 기준·판정·보고 수치 소유자**, 같은 커밋에서 코드와 기준 동시 변경 금지 | 메모리 feedback_separate_author_and_verifier.md | §14 전체(plan:1202-1363) -- **반영** |
| B14 | 만들기 전 **재사용 레지스트리 개념별 정본표** 확인, 호출부도 grep, 대체하면 같은 커밋에서 옛 함수 삭제 | 메모리 feedback_check_function_registry_before_build.md | §13.2 방지 규칙(plan:1067-1072) -- **반영** |
| B15 | 만들기 전 기록 3곳(계획 §7/§10, context.md, `def` grep) 확인 + **context 70%면 무조건 기록** | 메모리 feedback_record_before_compact_check_before_build.md | §13.2 원인1(plan:1062)에 3곳만 -- **부분 반영**(70% 기록 규칙 미반영) |
| B16 | 결정은 **기존 원칙으로 기본안 확정**, 사용자 몫(spec·회로 해석·승인 사안)만 해당 Phase 착수 조건 | 메모리 feedback_default_from_principles_before_asking.md | §12.8 서두(plan:1012-1013), §14.9 끝(plan:1362) -- **반영** |
| B17 | 상상으로 채우지 말고 원문·함수 실제 출력 확인 후 진행 | 메모리 feedback_no_assumption_without_evidence.md | §14.3 oracle 4종(plan:1266-1271), §12.1 "근거는 파일:줄 또는 실측"(plan:897) -- **부분 반영**(일반 원칙 절 없음) |
| B18 | L/gm_id 권위 출처 4종(compensation/replica/metric_stage_budget/gm_target_convention)을 전부 확인하고 자동채움 | 메모리 project_sizing_authoritative_sources.md | **미반영**(plan grep `_AUTHORITATIVE` 0건). §15.4 §7.1 유도/선언 분리(plan:1414)·§12.5.2 C-a writer 권한표(plan:974)가 흡수할 자리 |
| B19 | 사용자에게 보이는 텍스트는 한글 | 메모리 feedback_korean_final_report.md | 해당 없음(계획서 규칙 아님) |
| B20 | bkit 단계 준수: plan 기록 → design → do | context:14514-14515 | §13.6 "design 문서를 거쳐 착수"(plan:1167), §14.7 "승인 후 착수"(plan:1331) -- **반영** |
| B21 | 패키지 최소 릴리스 나이 정책 유지(전역 설정 낮추기 금지) | `~/.claude/CLAUDE.md` | §14.9 D13 근거 "최소 릴리스 나이 정책과 무관"(plan:1358) -- **반영(간접)** |

**표 B 미반영 원칙**: B09(회로도 net 표 재검증), B11(결과를 파일에), B12(run_in_background), B18(권위 출처 4종). **부분 반영**: B07, B08, B15(70% 기록), B17.

#### 표 C -- §7.4 / §7.7 / §7.10 / §7.11 충돌 검사

판정: **여전히 유효** / **부분 수정 필요(어떻게)** / **대체됨**.

**§7.4와 v4.0 인과 전환의 관계**: §7.4 제목은 "사용자 승인 완료, 이번 세션 AskUserQuestion"(plan:393, 2026-09-04)이지만, 원래 원칙2 "gain이 주도"는 **이미 취소선 처리되고 v4.0 개정문(보상 먼저)으로 제자리 교체**돼 있다(plan:397-419). 따라서 "gain 주도 vs 보상 먼저"의 직접 충돌은 남아 있지 않다. 남은 충돌은 개정문 안의 **"gm_id가 유일한 자유도"** 표현, 폐기된 KKT 식을 논거로 쓴 부분, 원칙3의 해법 서술이다(아래).

| 절:줄 | 문장 요지 | 충돌 상대(근거) | 판정 |
|---|---|---|---|
| §7.4:393 | 제목 "사용자 승인 완료, 이번 세션 AskUserQuestion" | 원칙2·3이 v4.0/v3.1에서 개정됨(plan:397-398, 424) -- "이번 세션"이 어느 날짜인지 불명 | **부분 수정** -- "2026-09-04 AskUserQuestion, 원칙2는 2026-09-07 v4.0·원칙3은 v3.1에서 개정"으로 날짜 명시 |
| §7.4:395-396 | 원칙1: **stage 안** input+cascode의 L/gm_id를 gain 목표에서 동시 결정 | §15.4 §7.2 행: 캐스코드 gm/gds 최대화→이분 역산 폐기, stage gain = gm_in/G_out, G_out은 출력노드 소자 전부(plan:1416). §15.4 §7.9 행: stage 경계를 넘는 결합 K1~K6 때문에 DP 단독 불성립(plan:1421). 공통 L은 L 동치류 theta·tail이 주인(A27/A28) | **부분 수정** -- "stage 안 input+cascode" → "**결합 블록**(출력노드 부하·L 동치류·공유 VGS 포함) 안에서 gm_id×L을 함께 결정, 블록 간 결합변수 y는 중층"으로 |
| §7.4:397-398 | 원칙2 취소선 + "v4.0에서 사용자 확정으로 개정: 인과 방향은 반대" | §15.5 G5 "v4.0 인과 유지"(plan:1432) | **여전히 유효** |
| §7.4:400-408 | 뒤집힌 이유: `min Σ gm_i/gm_id_i`와 KKT `gm_i/gm_id_i²`는 gm_i가 상수여야 성립 | KKT 한계비 탐욕은 v4.2에서 폐기(history:3043), §15.4 "KKT 탐욕 폐기"(plan:1421) | **부분 수정** -- 논거를 "전력 최소화가 well-posed하려면 gm_i가 보상으로 고정돼야 한다"로 일반화하고 KKT 식은 이력 참조로 |
| §7.4:406-408 | Miller OTA에서 (gm_1, gm_2, Cc)는 동시에 묶이는 3-tuple, 문헌 §6.4 순서와 일치 | Cc 유도식 구현(topology_library.py:470-489)이 같은 결론 | **여전히 유효** |
| §7.4:414 | compensation이 (Cc, Rz, gm_1..gm_N)을 한 번에 결정 | A36 "Cc와 Rz는 보상망이 계산해서 확정" -- 일치 | **여전히 유효** |
| §7.4:415 | "자유 축: gm_id_i **[★ 유일한 설계 자유도]**" | L도 자유 축(G6 내층 DP gm_id×L, plan:1433; l_class theta A28), 자유 노드전압 배분(G7 writer T4, plan:1417), 공유 VGS 결합변수 y(plan:1430) | **부분 수정** -- "유일한" 삭제, "보상 확정 후 자유 축 = gm_id_i, L(동치류 단위), 자유 노드전압; 결합변수 y는 블록 간"으로 |
| §7.4:416 | 파생: ID_i = gm_i/gm_id_i, W_i = L_i·ID_i/IDu_i, k_i = ID_i/ID_ref | 파일럿 Iref 1.2µA 선언 시 `value_amp` 규약상 ID_ref 고정(A15) | **부분 수정** -- `value_amp`가 선언되면 ID_ref는 파생이 아니라 고정 입력임을 한 줄 추가 |
| §7.4:417 | 기생 C_1, C_2 → Cc 재계산 → gm_i 갱신 [수렴 루프] | §12.5.2 C-c "순환은 SCC 블록의 명시적 고정점, 수렴 판정·반복 상한·비수렴 거부"(plan:976), §15.4 "기생 반복 별도 축 폐기"(plan:1421) | **부분 수정** -- "수렴 루프"를 "C-c 순환 블록(허용오차 D2 계산값)"으로 |
| §7.4:418 | gain은 스펙이 아니라 부등식 제약이자 산출물 | G8 gain 제약 판정은 전체회로 MNA 1종(plan:1435) | **여전히 유효** -- 판정 metric이 전체회로 gain임을 덧붙이면 B21과 정합 |
| §7.4:421-423 | "gain-budget-first" = 단별 gain 예산을 엔진이 유도·산출 | §15 서두 "gain-budget-first가 목표, graph는 기반"(plan:1372-1375) | **여전히 유효** |
| §7.4:424-426 | 원칙3: 배분도 엔진이 유도, 총 gain 목표만 스펙 | G6 "`gain_budget_db`는 출력"(plan:1433) | **여전히 유효** |
| §7.4:426-427 | "§7.9 Phase 2의 `A_i,max` 실측 + **root current 1-D 해찾기** 결과로" | v3.2 KKT 재정식화(history:3038) → v4.2 분리형 DP(history:3043) → §15 3층 할당(plan:1433) | **대체됨**(해법 서술) -- "G4 달성가능성 표 + G6 3층 할당"으로 교체 |
| §7.4:427-428 | 사고4 본질 유지, 특정 배분 강제는 `gain_budget_db_override`로만 | §15.4 §7.1 사람 선언 필드 목록(plan:1414)에 override 없음 | **부분 수정** -- override를 사람 선언 필드로 존치할지 명시(G0 출처 필수 규칙 적용) |
| §7.7:440 | "§7.6이 L을 새 탐색 차원으로 열었으므로" | §7.6 L_combo 전수 스캔은 미구현(plan:141 미체크), 실제 L 자유도는 l_class theta + SLSQP(A28, A31) | **부분 수정** -- 참조를 "L 동치류 theta(G1) + G6 할당"으로 |
| §7.7:445 R1 | 누가 바꿀 수 있나 = §13.3의 **5개 구조 신호**로 판정 | 구현은 `l_sharing_classes`(진짜 미러=kind/gate/source + same_as + matching_pairs, history:2276-2282, SR:2385), §15.5 G1 "L 동치류"(plan:1428). 5신호 전용은 G6에서 철회 권장(plan:756) | **대체됨** -- "S1 L 동치류 멤버는 공통 L, 동치류 주인은 gain stage tail(A27), cross-kind VGS 매칭은 L 공유 안 함(history:2284-2286)"으로 |
| §7.7:446 R2 | 매칭 그룹은 전원 동시에 | `matching_pairs`가 동치류 edge(history:2282) | **여전히 유효** |
| §7.7:447 R3 | LUT 격자 밖 금지 -- "L 앵커 **전체 7개**, bounds 안 4개" | B15 ③ LUT 앵커 7→**12개**(plan:730, history:3059), 정본 spec `L_candidates` 41점(history:1941) | **부분 수정** -- 외삽 금지는 유지, 앵커 수를 12개로 갱신하고 정본 spec 격자와 LUT 앵커를 구분 |
| §7.7:448 R4 | L↑가 항상 이득이 아니다 -- 전수 스캔 | G4 "LUT 격자 전수 -- 비단조 무관"(plan:1431) | **여전히 유효** |
| §7.7:449 R4b | 이득 부족 시 L보다 **VDS를 먼저**, §7.9 inner 루프 | D1 노드전압 정본에서 VDS는 노드전압 차이로 유도(plan:1017), 배분 가능한 것은 T4 자유 노드뿐(plan:1417). diode·미러 공유 VGS·적층 vsb 노드는 자유롭지 않음(A20~A22). §7.9 중첩 루프는 §15.4에서 변형(plan:1421) | **부분 수정** -- "VDS 먼저"를 "G7 T4 자유 노드전압 재배분 먼저, 구조 고정 노드는 제외"로 좁히고 G6/G7 어느 층에서 쓰는지 명시 |
| §7.7:450-451 R5/R6 | L 변경 시 행 폭·n_fingers 재판정(`stick_diagram.py:6400/6421`) | 줄 번호 현행 여부 미확인 | **여전히 유효**(줄 번호는 재확인 필요) |
| §7.7:452 R7 | 오일러 패스는 L 무관, 같은 행 안 l 상이 허용·finger_w 동일 | 충돌 근거 없음 | **여전히 유효** |
| §7.7:453 R8 | L 변경은 §8.4 수렴 루프 **안에서만**, 매 반복 커버리지 재확인 | §8.4는 §13.4 #8 `sizing_layout_convergence.py`로 대체(plan:1109). 현 엔진은 SLSQP 수렴 후 레이아웃이 실패를 잡음(history:2487-2496) = 루프 밖 | **부분 수정** -- 참조를 §13.4 #8로, "현 구현은 루프 밖(미충족)"을 명시 |
| §7.7:455-462 | branch(전기)와 row(물리) 구분, M15 L=0.150µm / M16 L=0.830µm 실측 | 실측값은 2026-09-04 시점, 이후 L 유도 방식 변경(A27~A30) | **부분 수정** -- 실측값에 날짜 표기(원칙은 유효) |
| §7.10:476-480 | 현재 엔진은 `_L_ROLE_MULTIPLIERS` 고정배수만, `select_L_by_role()`이 cascode/signal 거부 | 상수 삭제(A30, SR 정의 0), `select_L_by_role` 삭제·가드는 `derive_role_L`로 이관(history:2588) | **대체됨** -- "왜 필요한가"를 이력 서술로 격하 |
| §7.10:482-495 | 측정1, "**fT가 L 상한을 정하는 진짜 제약**" | §7.11이 `fT ≥ N·GBW`를 노드 pole/PM 제약으로 대체(plan:618-619), 제약 `parasitic_pm_deg ≥ PM_target_deg`(topo:2067-2070) | **부분 수정** -- "L 상한 = `parasitic_pm_deg ≥ PM_target_deg`(§7.11)"로 |
| §7.10:506-508 | "kind와 gm_id를 바꿔도 knee는 **항상** `L ≈ 2~3 × L_min`", mirror 2.5× 사후 검증, 주석을 실측으로 대체할 것 | 구현 실측: nmos 중앙 **1.63×**, pmos **2.27×**, gm_id별 1.63~17.67×로 민감(history:2318-2327). 상수는 삭제됨(A30) | **부분 수정** -- "항상 2~3×" 삭제, "kind별 중앙값(격자 전체 중앙값), vds 무관·gm_id 민감"으로. 주석 대체 지시는 대체됨 |
| §7.10:515 | `L <= L_max(fT)`: `fT(L) >= N×GBW` (N~5~10) | §7.11(3)·(6): N은 상수가 아니라 α·tan(PM), 최종 구현은 PM 직접 계산(plan:584-595, 633-640) | **대체됨** |
| §7.10:516 | `L >= L_min(match)`: σ_VT ≤ 목표 | bounds 하한 = `mismatch_sigma_mV ≤ 선언값`(history:2355)인데 그 값 5.0이 근거 없음(A33) | **부분 수정** -- 하한이 근거 없는 임계값에 묶여 있음을 명시(A33/A34 bisection과 연결) |
| §7.10:518-523 | role별 방향 편향: cascode knee 이상 / mirror knee+mismatch / 속도 임계 knee 아래 / **tail·load: CMRR/PSRR 만족 최소 L** | `_L_ROLE_TARGETS` = mirror→knee, bias_replica→창 하한, cascode/signal→거부(history:2477-2482, 2588). **tail은 L의 주인이고 공유 theta가 모든 선언 제약을 동시 만족**(A27/A28, history:2379-2381) | **부분 수정** -- 편향 표를 `_L_ROLE_TARGETS` + l_class(tail 주인) 규칙으로 교체. "tail = CMRR/PSRR 최소 L"은 A27과 충돌하므로 삭제 |
| §7.10:525-529 | 시작점: §7.6 L_combo "면적 오름차순 첫 feasible", knee에서 시작 | L_combo 미구현(plan:141), warm start는 **선언 제약 최소 여유 최대화**(내부점)로 x0 선택(history:2621) | **부분 수정** -- "knee에서 출발(derive_role_L), 탐색 x0는 내부점 점수"로 |
| §7.10:531-533 | R4b와 결합: VDS 재배분(inner) → L(mid) | 위 §7.7 R4b와 같은 충돌 | **부분 수정**(R4b와 함께) |
| §7.10:535-538 | 면적이 L에 비단조 → knee도 격자 전수 | `measure_L_knee`가 Δ(W·L)≤0 구간 건너뜀(history:2314) | **여전히 유효** |
| §7.10:540-542 | 신규 `measure_L_knee`, `L_bounds_from_ft_and_matching`, `L_candidates_product()`가 호출 | `measure_L_knee` 구현(SR:2305). 나머지 두 함수 def 0(grep) -- 역할은 §7.11 제약·`feasible_L_window`(SR:2694)가 대신 | **부분 수정** -- 실제 구현 함수명으로 교체, 미구현 둘은 삭제 또는 G4에 흡수 |
| §7.10:545-549 | 상수→`measure_L_knee()` 대체로 `select_L_by_role()`의 cascode/signal 거부 제약도 "함께 해소" | 가드는 해소가 아니라 `derive_role_L`로 **이관·유지**(history:2588). B10 "사고4 경계는 명시적 승인 필요"(plan:725) | **부분 수정** -- "해소" → "가드 유지(사고4 경계)"로 |
| §7.10:550-552 | `search_gm_id_and_L_for_role()`로 L축 내부화, `_idu_scan` 공유 | def 0(grep). §15 G6 내층 블록 DP(gm_id×L)가 같은 목적 | **부분 수정** -- G6 블록 DP로 재명세 |
| §7.11:558-562 | "엔진에 이 검사가 없다(`fT()` 호출부 0개)" | 구현 완료(§7.11(6), SR:4329) | **대체됨** |
| §7.11:564-571 | 문헌 조사 표 | 충돌 없음 | **여전히 유효**(근거 기록) |
| §7.11:575-582 | `PM = tan⁻¹(ω_p2/ω_c)`는 "이 토폴로지의 정의식", ω_c=2.3e8 rad/s, f_c=36.6MHz | L2 주파수응답 `PM = 180 − 누적 지연`이 정본이고 atan 식은 pole 하나 특수케이스(history:2163-2168). ω_c는 loop-gain UGB, 실측 w_c 30.50MHz(history:2175-2182) -- 36.6MHz와의 차이 원인 미확인 | **부분 수정** -- "정의식"을 "특수케이스"로, f_c 수치 재확인 |
| §7.11:584-595 | N = α × tan(PM_target), §7.10의 5~10은 α∈[2,3.6] | 충돌 없음 | **여전히 유효** |
| §7.11:599-604 | tail 최소 fT/f_c: knee **L=0.375µm**에서 ~28 | 0.375µm는 옛 `mirror 2.5×` 상수값, 실측 knee는 0.245/0.340µm(history:2339) | **부분 수정** -- 측정 시점·L 기준 표기 |
| §7.11:606-619 | 숫자를 박지 말고 유도 경로를 배선 | 메모리 B03과 일치 | **여전히 유효** |
| §7.11:625-626 | L2 = "기존 51노드 MNA에서 **실제 pole 추출(고유값)**" | 고유값 방식은 bias 모드가 섞여 틀림 → `(G+jωC)v=b` 직접 풀기로 구현(history:2156-2170, SR:4267) | **대체됨** |
| §7.11:628-629 | clamp를 숨은 상수가 아니라 metric으로 노출 | 구현(SR:4329) | **여전히 유효** |
| §7.11:633-640 | 하한: `PM_parasitic = 90 − Σ atan(w_c/w_pole)` (L1) | L2가 L1을 특수케이스로 포함, 현행 metric은 L2(history:2165-2168, 2243-2250) | **부분 수정** -- L1 식은 근사·이력, 정본은 L2 |
| §7.11:642-648 | 신설 `signal_path_nodes`, `node_pole_estimate`(L1 구성요소) | 엔진 호출부 0개(plan:944; SR에서 정의 4043/4080 외 docstring·주석만) | **부분 수정** -- 사장 함수로 D7 삭제/배선 목록에 넣음 |
| §7.11:652-655 | 전 노드 합산은 틀림 → **어느 경로의 PM인지 선언**에 있어야 | L2에서는 신호경로 제한 불필요(history:2167-2168). 단 excite/sense 모드 선언은 S1v에 존속(plan:962) | **부분 수정** -- "L1 한정" 명시 |
| §7.11:656-660 | LUT에 Cdb/Csb 없음 → 고임피던스 노드 `undetermined` 명시 실패 | LUT 접합용량 추가는 여전히 미완(context:14327) | **여전히 유효**(L1 한정 표기) |
| §7.11:662-667 | 파일럿 실측 `PM_parasitic = −8.9°` | 비정본 spec 값(history:1959), 정본에서 +33.88°(v4.35) → 71.87°(v4.36, history:2250) | **대체됨**(실측값) |
| §7.11:669-671 | "**constraint로는 아직 안 건다** -- 4개 회로에서 먼저 재고 상한" | v4.36에서 `parasitic_pm_deg >= PM_target_deg` 제약으로 걸림(topo:2067-2070, history:2245). folded_cascode는 `omega_c` 미노출로 측정 불가(context:14324) -- 4회로 선측정(A73) 미충족 상태 | **대체됨** -- 현행 제약 상태 + 4회로 측정 미완을 함께 기록 |

**과제3 충돌 요약(50행)**: 대체됨 8 / 부분 수정 필요 26 / 여전히 유효 16.

#### 부록 -- 재작성 때 함께 고칠 stale 표기 (현행 코드·후속 기록과 어긋남)

| 위치 | 현재 표기 | 실제 |
|---|---|---|
| plan:709 (A12) | "공유 엔진 동작 변경이라 사용자 승인 필요" | `validate_metric_units`(SR:5813) 구현됨(context:13958) |
| plan:724 (B9) | "★ 수정 승인 대기" | B25와 함께 구현(`reconcile_vsb_from_nodes` SR:3976, 호출 SR:9207; history:3069) |
| plan:671 (§7.11) | "constraint로는 아직 안 건다" | topo:2067-2070에 제약 선언 |
| history:2356 (§10.9) | 층0 `audit_l_sharing_consistency` "파이프라인에 안 걸려 있다" | SR:9454에서 호출(배선됨) |
| plan:730 (B15) / §7.7 R3 | 앵커 7개 | 12개(history:3059) |
| history:3004 / plan:1004 | 지문 불일치는 노트만(의도적) | C-d 도입 시 픽스처/정본 구분 방법 결정 필요(plan:1004) -- 미결 |
