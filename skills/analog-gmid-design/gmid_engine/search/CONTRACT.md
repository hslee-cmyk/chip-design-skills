# gmid_engine.search 동작 계약 (MOD6 θ 탐색 -> (전력, 면적) 비지배 front, test 작성용)

> **[U17 ①-b] S0 수준 필드 이동**(설계 40 §2.4.1~§2.4.3·§2.4.7·§2.4.8 v1.9.1 D3~D8·D10, 2026-10-13) -- 이 단락이 아래 옛 서술보다 우선한다.
> * `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, model_error=(), *, code_fp, s0=None)` -- `s1v`·`ach` 인자는 없다. `dc_ctx.base` 를 S0 수준 권한표
>   `S0_WRITERS`(= S2 ∪ graph S1V ∪ metrics S0 ∪ search S0 표, `s0_fields.py`)로 넓히고 계산 블록을 차례로 부른다: `search_domain`(extras: lut, 실행 설정의 수동소자 상자 둘, pdk_decl, spec θ 상자, 면적 예산,
>   untie -- 벽시계 등 다른 실행 설정은 넣지 않는다) -> `junction_field` -> `mismatch_field` -> `model_error_field` -> `constraint_classes` -> `passive_area_decl` -> `metric_structure` -> `noise_decl` ->
>   (`graph/s1v: views` 필드가 있으면) `start_intervals`. 끝에서 `s0`(core `S0Slot`, `StageAResult.s0`)로 S0 수준 스냅샷을 **한 번** 쓴다(단계 B 층 writer `residual_probe`·`dof_numeric` 은 `transient`,
>   v1.9.1 D6). 같은 S0 의 다음 실행(디스크 적중)은 모든 S0 블록이 재사용이다(계산 0).
> * `SearchContext` 칸 = 참조(`dc` -- base 가 S0 수준 스냅샷, `spec`, `settings`, `archive`, `context_fp` = (S0 스냅샷 fp, LUT 손잡이, DcInputs) 지문, `code_fp`) + 실행 수명 상태(cache·counters·예산·
>   `cell_floors`). 옛 S0 칸(`domain`·`junction`·`mismatch`·`model_error`·`area_decl`·`structure`·`noise_decl`·`judged_constraints`·`ss_constraints`·`constraint_notes`·`start`·`element_values`·
>   `driving`·`schema_fp`)은 같은 이름의 **읽기 속성**이 부를 때마다 필드에서 읽는다(`start` 대신 `rungs` = `graph/start: rungs` 또는 None, 칸 0 = 선택점).
> * 새/바뀐 계산 블록: `search_domain`(-> `graph/kernel: search_domain`), `constraint_classes`(-> `graph/kernel: constraint_classes` = `ConstraintClasses(judged, ss = spec judged_constraints 위치, notes = (키, 값) 쌍)`),
>   `passive_area_decl`(extras (측정 부하 이름, pdk_decl) -> `graph/kernel: passive_area_decl`), `noise_decl`(extras (feedback, sampling_caps) -> `graph/s1v: noise_input_cells` = NoiseDecl 전체),
>   `start_intervals`(extras (spec, DcInputs, pdk_decl, lut) -> `device: start.row`·`start.point`, `graph/start(START_KEY="start")`: `conflicts`·`inactive`·`macro`·`rungs`·`records`·`area_est_m2`·`area_fraction`·
>   `uncovered`). 묶음 `StartIntervals`·`StartContext`·`CurveBook`(`iv_curves.py`)·`build_start_context` 는 없다: 블록 안 읽기 묶음 = `iv_context.start_view(projection, spec, inputs, pdk_decl, lut) -> StartView`,
>   곡선 읽기 = `_helpers_curves`(LUT 파생 기준 VDS·tol_vdsat·엣지 비용은 `lut.derived`), 이득 L 하한 입력은 필드 `graph/ach: local_inputs`. `current_symmetry`·`orbit_ties` 는 첫 인자로 필드 질의가 되는
>   스냅샷(또는 투영)을 받는다. `cell_floor` 의 1변수 writer 집합은 `device.dc_self_referential` 필드다.
> * search `__init__` 이 S0 수준 스냅샷 값 형식(`SearchDomain`·`Variable`·`ConstraintClasses`·`StartRow`·`StartConflict`·`MacroResult`·`StartRung`·`Bound`)을 올린다.

- 대상: `gmid_engine/search/` 공개 API(`gmid_engine.search.__all__`). test 는 `from gmid_engine.search import ...` 와 그보다 앞
  패키지(`core`·`lut`·`authoring`·`graph`·`sizing`·`metrics`)의 공개 이름만 쓴다(`_` 이름·파일 모듈 직접 import 금지).
  배치는 규칙 H: `gmid_engine/tests/search/test_<파일>.py`(지금은 docstring 만 있는 자리표 21개 -- 동작 test 는 독립 test
  작성자 몫), 9회로 교차는 `tests/integration/`, 불변식은 `tests/contracts/`.
- 근거: `_drafts/engine/design_mod6_search_front.md`(이하 설계, Q3·Q7·Q10 개정본), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝
  '확정 사항' 3(S3)·7(L bin), 계획 DEC-34·54·72·77·78·79·80·85·88·95, LR3·LR5·LR10, U-47·U-49·U-51, sizing `CONTRACT.md` r2
  (12절 O1 봉인 7), metrics `CONTRACT.md` 3.13·3.14, authoring `SPEC_CONTRACT.md`, core `CONTRACT.md`.
- 기대값은 test 쪽이 손계산·toy 커널(설계 9절 T1~T14)로 만든다(피검 함수로 기대값을 만들지 않는다). 10절 숫자는 작성자 측
  실행값(교차 확인용)이고 정본이 아니다.
- 이 브랜치는 ng-gb7 r2(2db91e2) 위에 master(8d16dd7 병합: metrics·lut r4 L bin·core pdk_decl)를 합친 상태다.
- **r2(2026-10-08, 오케스트레이터 결정 반영)**: 바뀐 곳에 `[r2]`. 요지 -- b_P 를 점마다 tol_I × |V_rail| 로 유도(S-2), θ 전류 상자를
  LUT 에서 유도(`current_box`, S-3), θ 저항 상자는 선언 필수·없으면 구조화 거부(S-3), ss 제약은 점마다 '미측정' 기록 + 연결 자리
  `ss_constraints`(S-1), 한도는 평가 수(E_B)로 세어 결정론(S-7/8), FD 양방향 실패 열은 변수 고정(S-16), sizing `__all__` 에
  `dc_seal_vgs_match` 추가(S-9). 층 0(S-4)은 설계 입력 셋이 없어 막힘(9절).
- **r3(2026-10-08, 오케스트레이터 결정 2차)**: `[r3]`. b_P 의 gm 을 동작점 gm(ID·gm/ID)으로(S-2b), **설계 개정 S-18** W ≥ W_min 제약
  (W_min = PDK 선언 `min_finger_w_m` = difftap.2, core `sky130_pdk_decl.json` 에 quantity 추가), b_A 도 PDK 선언 두 값의 곱,
  `build_search_context`·`search_domain` 이 `pdk_decl` 을 받는다, I_max 잠정 표기(S-3b).
- **r4(2026-10-08, master ss_linearize + ng-seal7 병합)**: `[r4]`. S-1 배선 -- 봉인 점은 `metrics.ss_evaluate`, 대기·미정 점은
  `metrics.metrics_dc` 로 S2 필드를 만들고 목적·제약을 그 필드에서 읽는다(옛 S-6 해소 -- search 는 전력·면적을 다시 계산하지 않는다).
  ss 제약 행은 `ss_constraint_rows(bundle, declared)`, Undefined 는 `unmeasured`. 평가의 `evaluation` = ss 필드를 담은 lineage
  (다음 평가 parent 가 재사용). 최종 `front` = 봉인 + ss 제약 모두 측정, `unmeasured_front` 신설. 층 0 은 여전히 막힘(9절 S-4).
  시연은 LUT v2(`resolve_lut_location`) -- 봉인 7 이 실제로 판정되어 `seal7_pending` 은 발동 0.

- **r5(2026-10-08, 층 0 최소형 -- 오케스트레이터 결정 'feasibility centering', 브랜치 ng-layer0 = ng-mod6 + 이 변경)**: `[r5]`.
  층 0(DEC-71 최소형 = R D18·U-49·PUD DF-10, '기둥 KVL 조립으로 DC 정합 시작점 하나')을 **gain 예산 역산이 아니라 topology 무관
  feasibility centering** 으로 구현했다 -- θ 상자 중심(자연 좌표) -> 전류 Chebyshev 중심(커널 0) -> 봉인 항목 여유 최대-최소
  (경성 W 하한·반전 하한·원뿔). 새 파일 `layer0_center.py`(3.21), `start_points` 에 선택 인자 `layer0`(3.12), `find_front` 가
  층 0 을 먼저 부르고 notes 의 `layer0_inputs_missing`(막힘) 을 층 0 결과 기록으로 바꿨다(3.16). 9절 S-4 를 다시 썼다
  (입력 = 봉인 margin + θ 상자 + 경성 행; GB3·GB4·knee·GB5 근사식은 최소형 밖 정밀화). 9회로 실측 10.0000.
  **[r5b]** Halton 시험의 θ 전류를 상자 ∩ 원뿔 안 hit-and-run 으로(3.21 3, I-18), sf·current_reuse 실패 분류표(10.0000).
  **[r5c]** 시험 ln_idu 하한 = 칸 정점 하한(모든 쓰기 소자, 3.21 3), search_domain 채택 제안(S-4f), 9회로 재측정(10.0000).
- **r11(2026-10-08, ng-layer0-canon -- 사용자 대원칙 '이름에 종속된 엔진 금지')**: `[r11]`. 3.21 의 변수 순서·Halton 차원 배정을 이름 정렬에서
  **이름 없는 정준 순서**로 바꿨다(3.21 3 '정준 순서'). 이름 치환·원소 순서 섞기에 층 0 시작점이 자기동형 범위에서 따라간다.
- **r13(2026-10-08, U2 -- 사용자 결정 '대칭 묶음 방식: b', 설계 40 §6)**: `[U2]`. 2단자 수동소자를 무향으로 다루는 자기동형(graph `canonical_form`)과 θ 전류의 **부호 −1 묶음·구조적 0**(`current_symmetry`, 3.24 2).
  라이브러리 `current_reuse` 의 묶음이 선다(성분 107 → 탐색 차원 73). `orbit_ties` 의 대표 = 구조 색 최소(이름이 아님, 3.24 1). `search_domain` 의 5번째 인자는 `area_budget_m2`, `untie` 는 6번째.
- **r12(2026-10-08, 사용자 결정 '정준 라벨링 + 대칭 변수 묶음, 기본값 묶음')**: `[r12]`. (1) 변수 정준 키를 1-WL 색에서 sizing `dc_struct_colour` 의 궤도 산출 의 자기동형
  궤도 id 로(3.23), (2) 같은 궤도 원소의 같은 종류 θ 성분을 한 탐색 변수로 묶음(`orbit_ties`·`expand_ties`, 3.24; `SearchDomain.ties`;
  spec `search.untie_orbits` 로 해제), (3) SLSQP 제약 행·원뿔 행/항을 이름 없는 정준 순서로(`canonical_rows`, 3.25). 결과: 이름 치환·섞기에 층 0 시작점과
  SLSQP 반복이 비트 단위로 같다(DC 파생 행 기준, 3.23 4).
- **r8(2026-10-08, ng-layer0 = master(MOD6 r7) 병합 + 오케스트레이터 결정)**: `[r8]`. (1) S-4f 채택 -- 새 파일 `cell_floor.py`
  (`ln_idu_floors`, 3.22): 1변수 노드 writer 의 ln_idu 상자 하한 = 시작 칸의 칸 정점 하한(시작 좌표는 넘지 않음)을 `solve_eps`
  (3.13)·층 0 최대-최소에 적용, 층 0 시험(모든 쓰기 소자)도 같은 함수. `search_domain`(S0 당 1회, 칸 없음)에는 넣지 않았다 -- 하한이
  칸에 따라 달라 칸이 정해지는 풀이 단위(`solve_eps`)가 자리다. `SearchContext.cell_floors`(캐시) 신설. (2) 층 0 1단계(3.21 3b):
  `no_root_in_window` 이고 창 양끝 h 가 유한한 시험 점에서 그 노드 writer 좌표를 bisection 으로 고친다(사슬). (3) 병합 충돌
  `fd_jacobian` L 스텝은 r5 결정(제조 격자)을 유지하고 master r6 의 수동소자 스텝 분기를 그대로 둔다. **독립 test 영향**(작성자는
  test 를 고치지 않음): `test_find_front.py::test_sealed_run_perf_and_invariants`(n_starts 1 -> 층 0 시작점 포함 2)·
  `test_notes_record_open_items`(`layer0_inputs_missing` -> `seal_margin_maxmin_centre`) 두 건이 r5 계약 변경 3.12·3.16 과 어긋난다 --
  test 작성자 몫.
- **r9(2026-10-08, 브랜치 ng-search-cond = master + 이 변경 -- sizing r8 봉인 9 전도 여유)**: `[r9]`. `cell_floor` 에 칸 전도 하한 추가
  (3.22 r9 항목): 봉인 9 조건 IDu(VGS)·(gm/ID)·tol_V ≥ IDu(VGS = 0) 은 W 와 무관한 ln_idu 좌표 하한이라 θ 전류 상자(current_box I_off)로는
  막을 수 없다(sizing O17). 모든 ln_idu 성분에 붙고 1변수 writer 는 정점 하한과 max. 봉인 9 가 판정 권한(하한은 평가 절약용).
- **r10(2026-10-08, ng-search-cond -- 사용자 결정 8·10: 원소별 θ 수동소자 상자)**: `[r10]`. θ `resistance`·`ss_resistance`·
  `capacitance` 성분의 상자는 **원소별**로 정한다. 우선순위(위가 이긴다):
  1. `SearchSettings.resistance_bounds_ohm` / `capacitance_bounds_f` 가 None 이 아니면 그 run 의 **그 종류 모든 원소**에 그 상자
     (명시 run 단위 재정의 -- 시연·실험용, spec 을 바꾸지 않는다).
  2. 아니면 spec `human.search.theta_bounds.<원소>`(authoring `ThetaBound(element, kind, lo, hi, source)`, SI 단위 Ω·F --
     authoring SPEC_CONTRACT 1절). `build_search_context` 가 `spec.search` 의 `SettingValue(field "theta_bounds")` 값을
     `search_domain(dc_ctx, settings, pdk_decl, spec_bounds)` 의 넷째 인자로 넘긴다(기본 `()`).
  3. 둘 다 없으면 변수를 만들기 전에 `SchemaRejectedError`(gate `search_domain`, reason `theta_resistance_bounds_undeclared` /
     `theta_capacitance_bounds_undeclared`, `resistors` / `capacitors` = **상자가 없는 원소만** θ 순). 커널 호출 0(I-11 그대로).
  변수 = (True, ln lo, ln hi). spec 상자는 `search_fp`(→ `spec_fp`)에 든다(값·원소·kind; 출처 문구는 지문 밖).
  `SearchContext` 지문은 바뀌지 않는 쪽(상자는 변수 bounds 로만 작용 -- 같은 θ 의 평가 결과는 상자와 무관). 1.1·3.7·I-11 은
  이 항목으로 읽는다. library 6회로 spec 에 상자 기입(10절 r10).

### r4 덮어쓰기 요약 (아래 본문보다 우선)
- `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, junction=None)`: `junction` = metrics `JunctionSource`
  (ng-junction, metrics 7.6 필수 키워드). None 이면 `ss_evaluate` 에 넘기지 않는다(master 에 아직 없음); 들어오면 필수로 바꾸고
  kernel 의 조건 한 줄을 지운다. 봉인 7 은 master 정식(153bf47) -- 포화는 봉인 7 결과로만 다루고 W4 창·1변수 구간에 VDsat 항은 없다
  (오케스트레이터 결정 2026-10-08).
- 3.6 `objective_values(snapshot) -> Objectives`: 값 = `graph.metrics_dc`(key `METRICS_KEY`) `MetricBundle` 의 `power_dc_w`·
  `area_search_m2`(None 이면 ValueError), detail 의 `per_rail_amp`·`kcl_residual_amp`·`passive_area_undeclared`·
  `passive_value_missing`(→ `passive_value_undetermined`), `gate_area_m2` = Σ dc_op W·L, b_P 는 r3 식 그대로.
- 3.10 `evaluate` 6단계: 상태 = `seal_status`. `STATUS_SEALED` 면 `ss_evaluate(ev.sealed, dc_ctx, θ, sctx.ss_constraints, (), ())`
  (`NonconvergentError`·`SealViolationError` 는 후보 실패로), `evaluation` = 결과 `lineage`, bundle = `.ss`. 그 밖이면
  `metrics_dc(ev.snapshot, 수동소자 값, ())`(수동소자 값 = spec 값 있는 수동소자 ∪ θ 저항, 이름 정렬 -- `ss_evaluate` 와 같은 값이라
  나중에 같은 점이 봉인되면 블록 재사용), `evaluation` = DcEvaluation(그 스냅샷, report, sealed). 그다음 목적·b_P(None 이면
  `STATUS_UNDEFINED`)·제약 = constraint_rows + 목적 축 spec 행 + `ss_constraint_rows(bundle, ss_constraints)`.
- 3.9: `ss_constraints` = judged·값 있음·목적 축 밖·`metric_registry()` 에서 view_kind 가 있는 metric 의 `ConstraintDecl` tuple(문서
  순서). 레지스트리 밖·view 없는 판정 제약은 notes(`metric_not_in_registry_or_no_ss_view`). (옛 `spec_passive_values` 칸은 U17 ① 에서 지웠다 -- 수동소자 값은 S2 필드 `device.passive_value`.)
- 3.20 `ss_constraint_rows(bundle, declared)`: 본문 docstring -- bundle None 이면 전부 `ss_requires_sealed_snapshot`, 값 None 이면
  (metric, op, Undefined code '+' 연결), 값이 있으면 `ss:<k>:<metric><op>` c = (값 − 목표)/|목표|(>=) 또는 반대, 목표 0 이면 분모 1,
  `active` False(S-19).
  **[CM 사용자 결정 2026-10-08 "A는 제안대로 해"]** view_kind `cm_loop` metric(구조 유도 CM 루프, 현재 파일럿 `pm_cm_ss_deg`)의 PM 이
  `dc_not_above_level`(|T_cm(0)| ≤ 1 -- 0 dB 교차 없음, CMFB 무효)로 None 이면 `unmeasured` 가 아니라 **위반 행**: c = 20·log10|T_cm(0)| / s
  (< 0, 0 dB 기준 -- 새 상수 없음; |T_cm(0)| = detail `dc_magnitude`), s = 이득 dB 분해능(metrics 9절; `MetricResult.resolution` 에 실림), 없거나 0 이면 1 dB
  (c 의 단위가 dB), |T_cm(0)| = 0 이면 c = −∞, `active` True. 임계값(60°)은 쓰지 않는다. 개루프 RHP 극점(`loop_open_rhp_poles`) 등 다른 사유는
  기존대로 unmeasured. 차동 `pm_ss_deg` 의미는 그대로(`dc_not_above_level` 이면 unmeasured). 위반 행은 T_cm(0) 이 오를수록 증가(c 가 0 으로)해
  SLSQP 가 쓸 신호가 된다.
- 3.15·3.16: 비지배 묶음 셋 -- `front`(봉인·미측정 없음), `unmeasured_front`(봉인·미측정 있음), `pending_front`(봉인 7 대기). L-b 뒤
  마지막 entries 로 셋 다 다시 거른다. `SearchFront.unmeasured_front`(기본 ()), runs 에 `unmeasured_front` 목록.
- 9절 추가: **S-19** ss metric 의 NFR-5 '격자 분해능' 정의 없음 -> 정규화 = |목표|(조건수용), 활성 판정 보류. **S-20** engine 값
  보상 수동소자(Cc·Rz·Cm, DEC-92)의 θ 성분이 sizing 스키마에 아직 없어 그 회로의 ss 제약은 전부 `passive_value_undeclared` --
  최종 front 에 들 수 없다(`unmeasured_front` 로만).
- **S-19 결정(오케스트레이터 2026-10-08)**: 정본 분해능 = 소자별 tol_V 셀(LUT 조회 불확실성)을 gm·gds·gmb·용량으로 옮긴 뒤 metric 마다
  1차 감도로 전파한 값과 MNA 수치 오차 중 큰 쪽 = metrics `MetricResult.resolution`(브랜치 ng-resolution bc76f6b, 검증 중). 병합 뒤
  `ss_constraint_rows` 의 분모 s = max(resolution, DEC-72 모델 오차(선언 시)), s 가 None 또는 0 이면 행 없이 `unmeasured`
  (사유 `resolution_undefined`), `active` = c ≤ 1. 그때까지는 아래 3.20 의 |목표| 축척(조건수용, active False)이 유지된다.

### r6 (2026-10-08, master 병합: metrics 9절 resolution·DEC-92 보상 수동소자 θ·junction 필수) -- 아래 본문보다 우선
- **S-19 적용**: `ss_constraint_rows(bundle, declared, model_error=())` -- 분모 = `MetricResult.resolution`. None -> unmeasured
  "resolution_undefined", 0 -> 모델 오차 선언(DEC-72)이 있으면 그 값, 없으면 unmeasured "resolution_zero_model_error_undeclared"(0 나누기
  없음), 둘 다 있으면 max. `active` = c ≤ 1. 모델 오차 선언은 아직 없어 kernel 은 () 를 넘긴다. (3.20 의 |목표| 축척 폐기.)
- **`build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl)`**: `lut_rule_decl` = core
  `read_pdk_decl(LUT 생성 규칙 선언)` -- 여기서 S0 당 1회 `JunctionSource.from_decls(pdk_decl, lut_rule_decl, lut)`(metrics 7.6 필수
  junction). r4/r5 의 `junction=None` 인자는 없어졌다(**독립 test 갱신 필요** -- test 작성자 몫).
- **DEC-92 θ 종류**: `capacitance` -> 변수 (ln, `settings.capacitance_bounds_f`), 선언 없으면 `SchemaRejectedError`
  (gate `search_domain`, reason `theta_capacitance_bounds_undeclared`, capacitors = θ 순) -- PDK 에서 유도 불가(sizing O13).
  `ss_resistance` -> `resistance_bounds_ohm`(없으면 기존 `theta_resistance_bounds_undeclared`, resistors 에 포함). 모르는 θ 종류는
  `ValueError`(조용히 건너뛰지 않는다). `SearchSettings` 끝에 `capacitance_bounds_f: object = None` 추가(기존 4필드 위치 불변).
- **FD 스텝**(DEC-92 θ, ln 좌표): 전 MOS `dc_tol_v·gm_id` 최솟값(소신호 모형 상대 분해능 -- LUT 축이 없는 수동소자). 
- **kernel**: 봉인 점 `ss_evaluate(sealed, dc, θ, ss_constraints, (), junction=sctx.junction)`(passive_theta 인자 삭제됨). 봉인 아닌 점의
  `metrics_dc` 수동 값 = spec 값 ∪ θ resistance·capacitance·ss_resistance(이름 정렬). 영점 상쇄 구조 규칙 저항(1/Σgm)은 ss_dev 가
  있어야 정해져 봉인 아닌 점에서는 `passive_value_missing` 이다(면적 단위 선언이 없어 면적 값은 같다).

- **r7 명확화(독립 test 9cbaaa0 대조)**:
  - `build_search_context` 는 무엇이든 만들기 전에 입력 형식을 본다: `pdk_decl`·`lut_rule_decl` 이 core `PdkDecl` 이 아니면 `TypeError`,
    그다음 `search_domain`(settings 형식 `TypeError` 포함), 그 뒤에 `JunctionSource` 를 만든다.
  - `ss_constraint_rows(..., model_error)` 의 `model_error` = ((metric 이름, 값 > 0 또는 None), ...) 쌍 iterable(dict 로 읽는다, metric
    마다 하나). 분모 s = max(resolution, model_error[metric] 또는 0): resolution > 0 이면 모델 오차가 없거나 작아도 resolution,
    resolution == 0 이면 모델 오차(> 0)가 있으면 그 값, 없으면 unmeasured `resolution_zero_model_error_undeclared`. resolution None 이면
    모델 오차와 무관하게 unmeasured `resolution_undefined`.
  - `eval_key` 는 θ 원소가 ((kind, key), 값) 모양이 아니면 `ValueError` -- 키 자리가 2-tuple 이 아닌 것(예 `(("L", 1e-6),)`) 포함.
  - `solve_eps` 의 예산 검사는 **새 x 를 커널로 평가하기 직전에만** 한다(캐시 적중은 커널 0 이라 예산을 쓰지 않는다). 그래서 시작점이 이미
    캐시에 있으면 deadline 이 지났어도 "start_wall_budget" 이 아니라 그 점을 받아들이고 SLSQP 를 시작하며, 첫 새 평가(보통 FD 열)에서
    "wall_budget"(또는 "eval_budget")으로 끝난다. 시작점이 캐시에 없을 때만 "start_wall_budget"·"start_eval_budget" 이 난다.
- **x 복사(r6, layer-0 작성자 지적)**: `solve_eps` 의 `point(x)` 는 SLSQP 가 넘긴 배열을 `np.array(..., copy=True)` 로 복사해 저장·키로 쓰고,
  재시작 중심도 복사본을 넘긴다. 회귀 확인(scratch, nmcnr): 콜백 뒤 x 를 제자리 변경해도 수락 점의 저장 x → θ 키 불일치 0. 단 scipy 1.18
  의 SLSQP 경로는 fun/jac 에 복사본을 넘겨 수정 전 코드에서도 이 회로에서는 재현되지 않았다(방어적 수정).

### r6 9회로 실측 (2026-10-08, LUT v2, master 병합본, B = 120 s)
- **A(선언 그대로)**: θ 수동소자 상자 미선언으로 6회로 거부 -- θ 저항(current_reuse R1·R2, sf_pushpull R1a~c), θ 커패시터(ngcc Cm1·Cm2,
  nmcnr Cm1·Cm2, two_stage_ota Cc, two_stage_ota_sf Cc). 돈 3회로 최종 front: common_gate 3(제약 없음), folded 2(제약 없음),
  pushpull 2 -- rout_ss_ohm 997.98 Ω(c = 0.076, **활성**), 619.18 Ω(c = 27.4) ≤ 1000.
- **B(시연 가정: θ R [100 Ω, 100 kΩ], θ C [0.1, 10] pF -- 결정 대기 값)**: two_stage_ota 1점(gain 82.40 dB ≥ 57, c = 25.7),
  two_stage_ota_sf 1점(gain 79.40 dB ≥ 57, rout 995.46 Ω ≤ 1000 c = 0.177 활성), ngcc·nmcnr 최종 0(gbw·pm 을 만족하는 봉인 점을 못 찾음 --
  시작점 2개·예산 120 s), current_reuse·sf_pushpull 시작점 0(탐침 200 전부 실패).
- 9회로 모두 `kernel_calls == unique_keys`, `recompute_same_key == 0`. 벽시계 정지는 pushpull·ngcc·two_stage(B)에서 기록됨.

### r5 명확화 (2026-10-08, 독립 test 1386711 대조 -- 의미 변경 없음, 아래 본문보다 우선)
- **`cells`**(evaluate·eval_key·StartPoint·EvalKey): MOS 마다 L 칸 index 의 tuple, 순서 = `SearchDomain.l_cells` 순서(MOS 이름순),
  값 j = 그 MOS 의 `l_cells[i][1]` 안 위치(0 부터).
- **`eval_key`**: θ 가 ((kind, key), 값) 2-tuple 들이 아니면(쌍이 아님·원소 수 ≠ 2·list 쌍) `ValueError`(3.2 -- TypeError 아님).
- **ss 행 이름** `ss:<k>:<metric><op>`: k = `sctx.ss_constraints`(선언 순서) 안의 0 부터 위치. unmeasured 사유 = 그 결과
  `undefined` 의 code 집합을 정렬해 '+' 로 이은 것(code 가 없으면 "undefined").
- **3.20 `declared`** = spec `ConstraintDecl` tuple(r4 -- (metric, op, value) 3-tuple 아님).
- **constraint_notes**: r2 의 'ss 제약마다 verdict unmeasured' note 는 r4 에서 없앴다(코드 그대로). 남는 것: 값 결정 대기
  (`judgment_pending`/`constraint_value_pending`), 레지스트리 밖·view 없는 판정 제약(`unmeasured`/`metric_not_in_registry_or_no_ss_view`).
  점마다 미측정은 `EvalResult.unmeasured` 와 find_front notes 의 `S-1` 항목(제약 목록·점 수).
- **solve_eps stop 어휘**(완전 목록): 시작점이 받아들일 상태가 아니거나 예산에 걸리면 "start_" + 사유 -- "start_candidate_failure",
  "start_constraint_set_changed", "start_eval_budget", "start_wall_budget". 그 밖 "converged", "slsqp_<status>", "eval_budget",
  "wall_budget", "restart_cap", "all_columns_frozen", 그리고 중단 사유 그대로("candidate_failure"·"constraint_set_changed" -- 재시작
  상한 전 SLSQP 가 끝났을 때 마지막 사유). `perf.stops_eval_budget`·`stops_wall_budget` 은 "eval_budget"·"wall_budget" 만 센다.
- **`S3Archive.read_snapshot(rel)`** → dict(`json.load` 결과: {fp, records[{kind, key, fields}]}).
- **`SearchDomain.current_box`** 의 kind = 그 회로 S1 의 MOS kind 집합(이름순) -- LUT 의 모든 kind 가 아니다.
- **효율 수정(r5)**: `solve_eps` 가 시작 좌표 x0 를 θ 로 되돌릴 때 bounds 로 잘리지 않은 성분은 시작 θ 원값을 그대로 쓴다(ln→exp
  왕복 1 ulp 차이로 시작점이 다른 평가 키가 되어 커널을 한 번 더 부르던 결함).
- **열린 항목 S-21(관찰, 알고리즘 변경 없음)**: 전력 최소 끝점 E_P(SLSQP 국소해)가 같은 실행의 ε 점에 지배당하는 경우가 있다(설계 PA 2.4
  국소해 실례와 같음) -- front 필터가 지배당한 끝점을 `removed` 로 뺀다. 끝점 multi-start 수·재시도 규칙은 결정 대기.

---

## 0. 파일·층·진입점 (`_module_map.LAYERS["search"]`)

| 층 | 파일 | 진입점 / 종류 |
|---|---|---|
| 0 | `search_values.py` | 데이터 선언 모듈(상태·단계·축·제약 접두 어휘, 2절 형식) |
| 1 | `archive.py` | `S3Archive` |
| 1 | `canonical_order.py` [r11] | `canonical_order` |
| 1 | `canonical_rows.py` [r12] | `canonical_row_key` |
| 1 | `current_symmetry.py` [r12] | `current_symmetry` |
| 2 | `orbit_ties.py` [r12] | `orbit_ties` |
| 1 | `tie_expand.py` [r12] | `expand_ties` |
| 1 | `cell_floor.py` [r8] | `ln_idu_floors` |
| 1 | `cone_rows.py` | `cone_rows` |
| 1 | `current_box.py` [r2] | `current_box` |
| 1 | `eval_key.py` | `eval_key` |
| 1 | `l_cells.py` | `l_cells` |
| 1 | `objectives.py` | `objective_values` |
| 1 | `pareto.py` | `nondominated` |
| 1 | `seal7_pending.py` | `seal_status` ★ 봉인 7 대기 스위치(4절) |
| 1 | `ss_constraints.py` [r2] | `ss_constraint_rows` ★ ss_linearize 연결 자리 |
| 2 | `constraints.py` | `constraint_rows` |
| 2 | `search_domain.py` | `search_domain` |
| 3 | `search_context.py` | `build_search_context`(+ 비진입 공개 클래스 `SearchContext`) |
| 4 | `kernel.py` | `evaluate` |
| 5 | `fd_jacobian.py` | `fd_jacobian` |
| 5 | `front_query.py` | `node_across_front` |
| 5 | `start_points.py` | `start_points` |
| 6 | `layer0_center.py` [r5] | `layer0_start`(+ 비진입 공개 클래스 `Layer0Result`, 상수 `SOURCE_LAYER0`·`STAGE_LAYER0`·`ROW_SEAL_ITEM`) |
| 6 | `slsqp_outer.py` | `solve_eps` |
| 7 | `l_bin_search.py` | `polish_l_cells` |
| 8 | `eps_sweep.py` | `sweep_front` |
| 9 | `find_front.py` | `find_front` |

계산 블록(`@compute_block`)은 없다 -- MOD6 은 조립자이고 graph 필드는 sizing 블록이 쓴다(설계 2.2). 모듈 수준 가변 캐시 없음:
평가 캐시는 `SearchContext` 객체가 소유한다.

## 1. 공개 흐름과 입력

```
dc_ctx = build_kernel_context(build_s1(...), dc_inputs_from_spec(spec), pre_layout_lut_access(memo))   # sizing, S0 당 1회
pdk    = read_pdk_decl(<PDK 선언 json>, BoundedLRU(…))                                              # core, [r3]
sctx   = build_search_context(dc_ctx, spec, settings, archive_root, pdk)                             # S0 당 1회
front  = find_front(sctx, given_starts)                                                               # -> SearchFront
```

### 1.1 [r2] `SearchSettings(front_budget_s, eval_budget, resistance_bounds_ohm, sources)` -- frozen, 기본값 없음
| 필드 | 뜻 | 상태 |
|---|---|---|
| `front_budget_s` | front 벽시계 예산 B(s) -- 바깥 정지(`wall_budget`, 기록)와 E_B 유도에만 | spec `search.front_budget_s` = PA-2 결정 대기, U-47 보류 -> 부르는 쪽 선언 |
| `eval_budget` | 커널 평가 수 예산 E_B(int) 또는 None | None -> `evaluate` 가 커널 평가 수가 n + 1(n = 정의역 연속 변수 수, FD 한 번)을 넘는 순간 E_B = ⌊B / median(평가 시간)⌋ 를 한 번 정하고 기록(`eval_budget_source` = "derived_once:floor(B/median_t_eval)@n_evals=<수>") -- 첫 평가의 LUT 파생표(tol_V) 1회 비용이 중앙값을 끌지 않게 한 sweep 뒤에 잰다. 같은 E_B 를 넘기면 같은 결과 |
| `resistance_bounds_ohm` | θ 저항 상자 (lo, hi) Ω 또는 None | PDK 선언에 수동소자 범위 없음 -> θ 저항이 있는 회로는 필수. 없으면 `search_domain` 이 `SchemaRejectedError`(3.7) |
| `sources` | ((필드, 출처 문자열), ...) | S3 runs 에 그대로 기록 |

b_P(전력 분해능)와 θ 전류 상자는 선언이 아니라 유도다(3.6·3.7·3.19).

### 1.2 `given_starts`
θ Mapping({(kind, key): 값}, 스키마 전 성분) 의 iterable. 설계 6.1 시작점 출처 ① 층 0 은 [r5] `layer0_start`(3.21)가 만든다
(~~[r2] 막힘~~), ③ 선언 x0 은 spec 필드가 없어 부르는 쪽이 넘긴다.

## 2. 값 형식 (`search_values`, 모두 frozen dataclass)

- 상태: `STATUS_SEALED`("sealed"), `STATUS_PENDING_SEAL7`("pending_seal_7"), `STATUS_UNDEFINED`("seal_undefined"),
  `STATUS_FAILED`("failed"), `STATUS_OUTSIDE_DOMAIN`("outside_domain"); `ACCEPTED_STATUSES` = (sealed, pending_seal_7) =
  탐색 경로가 따라가는 상태.
- 단계: `STAGE_START`·`STAGE_SLSQP`·`STAGE_FD`·`STAGE_L_SEARCH`. 축: `AXIS_POWER` = "power_dc_w", `AXIS_AREA` =
  "area_search_m2", `AXES`. 제약 이름 접두: `CON_SEAL6`("seal6_bulk")·`CON_INVERSION`("inversion_floor")·`CON_CONE`
  ("current_cone")·`CON_EPS`("eps")·[r3] `CON_WMIN`("w_min") + ":" + 소자/축. 목적 축 spec 제약은 "spec:" + metric + op.
- `Variable(component, log, lo, hi)`, [r3] `SearchDomain(variables, l_cells, area_resolution_m2, current_box, w_min_m, grid_m)`,
  `EvalKey(context_fp, schema_fp, cells, w_fixed_fp, theta_hex)`, `Objectives(power_w, area_m2, per_rail, kcl_residual_a,
  gate_area_m2, passive_area_undeclared, passive_value_undetermined, power_resolution_w=None)`, `ConstraintRow(name, c, active)`,
  `EvalResult(key, theta, status, evaluation, objectives, constraints, cone, failure, seq, unmeasured=())`(eq=False),
  `StartPoint(start_id, theta, cells, source)`, `SolveResult(best, eps, minimize, iterations, restarts, stop, history,
  aborts=(), frozen=())`,
  `FrontPoint(point_id, result, origin, dominated_by=None)`, `ParetoResult(kept, folded, dominated)`,
  `SearchFront(run_id, front, pending_front, failed_eps, resolution, perf, notes)`, `NodeRow(point_id, status, voltage,
  tier, devices)`.

## 3. 함수 계약

### 3.1 `nondominated(points, ties) -> ParetoResult`
- `points` = ((id, (축 값, ...), slack), ...), 축은 모두 최소화. `ties` = 축마다 음 아닌 수 또는 `width(id_p, id_q)` 호출 가능.
  점의 축 수 ≠ ties 수 -> `ValueError`.
- 축 비교: |a − b| ≤ 폭 -> 동률, a < b − 폭 -> 나음. p 가 q 를 지배 = 나쁜 축 0, 나은 축 ≥ 1. 모든 축 동률 -> 접힘.
- 처리 순서 = (첫 축 값 오름, slack 내림, id 이름순). 그 순서로 넣으며: 이미 남은 점 k 와 모든 축 동률이면 `folded` 에 (i, k),
  k 가 지배하면 `dominated` 에 (i, k); 아니면 새 점이 지배하는 남은 점을 `dominated` 에 (k, i) 로 빼고 남긴다.
- `kept` = 남은 index 를 같은 순서로 정렬. `folded`·`dominated` 는 정렬 tuple. 결정론: 입력 순서와 무관하게 같은 결과(id 유일 시).

### 3.2 `eval_key(context_fp, schema_fp, theta, cells, w_fixed_fp) -> EvalKey`
- `theta` 가 키 정렬 쌍이 아니면 `ValueError`. `theta_hex` = 값마다 `float.hex`(1 ulp 다르면 다른 키). ε·출처는 키 밖.

### 3.3 `seal_status(evaluation) -> str` -- 4절.

### 3.4 `l_cells(lut_access, kind) -> ((lo, hi), ...)`
- 레이아웃 전 폭 슬라이스(`lut_access.w_keys[kind]`)의 L 앵커(`grids[0]`)와 `l_bins`. bin 지도가 비면 앵커마다 (a, a).
  있으면 같은 `anchor_bin` 앵커들 -> (최소, 최대); `anchor_bin` 이 None 인 앵커는 자기 칸 (a, a). lo 오름차순.

### 3.5 `cone_rows(schema, theta) -> (ConstraintRow, ...)`
- `schema.current_cone` MOS 순서대로 c = Σ항 / Σ|항|(유리수, `schema.fixed` 포함; 항 합 0 이면 c = 0). `active` 는 항상 False.
  양의 유리수가 float 0 이 되면 `ArithmeticError`. c ≤ 0 ⇔ `check_theta` 가 정의역 밖으로 거부하는 θ.

### 3.6 `objective_values(snapshot, resistances, element_values) -> Objectives`
- 노드 = `node.is_rail` 열의 key 정렬 index. 레일 = `dc_rail_v`, 노드 전압 = `dc_v`. 채널·이상 전류원 = `dc_current_basis.ends`
  (from, to) + `dc_current`(값 없는 원소 생략), DC 저항 = `basis.resistors` 중 `resistances` 에 값이 있는 것.
- `power_w` = metrics `supply_currents(...).power_dc_w`(모든 레일), `per_rail` = (레일 넷, I_k), `kcl_residual_a`.
- `area_m2` = metrics `area_search(GateArea(dc_op.W, dc_op.L) 전 MOS, PassiveArea(값 있는 수동소자, 단위 면적 None))`.
  수동소자 값이 `element_values`·`resistances` 어디에도 없으면 `passive_value_undetermined`(이름순), 값은 있는데 단위 면적
  선언이 없으면 `passive_area_undeclared`(U-36).
- [U17 ①] `power_resolution_w` = graph 필드 `power_resolution_w`(writer metrics `metrics_dc`, 설계 40 §2.4.8): b_P = Σ_{레일 k} |dc_rail_v_k| · tol_I,k,
  tol_I,k = 채널 끝이 레일 넷 k 인 MOS 중 `dc_tol_v` 가 None 이 아닌 것의 `dc_tol_v · dc_gm` 최댓값(봉인 3 과 같은 gm 필드). 행이 있는 레일이 없거나
  합이 0 이면 None. `gate_area_m2` 도 같은 블록의 필드다. search 는 다시 계산하지 않는다(옛 `_power_resolution` 삭제). power_dc_w 는 모든 레일 합이라 합산 레일 = 모든 레일(전압 0 레일은 0 기여).
  `supply_current_dc` 는 합산 레일 선언(`counted_rails`)이 spec 에 없어 계산하지 않는다(notes `supply_current_dc_needs_counted_rails_declaration`).

### 3.7 `search_domain(dc_ctx, settings) -> SearchDomain`
- [r12] 진입 `search_domain(dc_ctx, settings, pdk_decl, spec_bounds=(), area_budget_m2=None, untie=())`: 위 변수·`l_cells` 를 만든 뒤 3.24 `orbit_ties` 로 같은 자기동형 궤도의 같은 종류 성분을
  한 변수(대표)로 묶는다 -- 묶인 구성원은 `variables`·`l_cells` 에서 빠지고 `SearchDomain.ties` 에 기록된다(구성원 bounds 불일치 `tied_orbit_bounds_differ`).
  `untie` = spec `search.untie_orbits` 원소 이름 tuple.
- [r3] 진입 `search_domain(dc_ctx, settings, pdk_decl)`. `settings` 가 SearchSettings 아님·`pdk_decl` 이 core `PdkDecl` 아님 ->
  `TypeError`. `pdk_decl` 에 `manufacturing_grid_m`·`min_finger_w_m` 이 없으면 core 의 `pdk_quantity_undeclared` 거부 그대로.
  변수(θ 스키마 성분 순, L 제외):
  `ln_idu` = (False, kind 포락선 lo, hi): hi = 레이아웃 전 슬라이스 on_mask 격자점의 ln(ID·L/w_m) 최댓값, lo = (L, VDS, VS)
  곡선마다 gm/ID(= exp(log_GM − log_ID)) 최대 VGS 격자점의 ln IDu 중 최솟값(정점 격자점이 on_mask 인 곡선만).
  `y` = (False, 0, 1). [r2] `current` = (True, ln I_off, ln I_max): 기저 원소가 MOS 면 그 kind 의 `current_box`, 아니면 그 원소를
  항으로 갖는 `current_cone` MOS 행들의 kind 상자 (최소 I_off, 최대 I_max)(그런 행이 없으면 `ValueError`).
  `resistance` = (True, ln lo, ln hi) -- [r2] θ 저항이 있는데 `resistance_bounds_ohm` 이 None 이면 변수를 만들기 전에
  `SchemaRejectedError`(detail {gate "search_domain", reason "theta_resistance_bounds_undeclared", resistors (θ 순)}).
  lo ≥ hi 인 변수 -> `ValueError`.
- `l_cells` = ((MOS, l_cells(kind)), ...) MOS 이름순. [r3] `grid_m` = PDK `manufacturing_grid_m`, `w_min_m` = PDK
  `min_finger_w_m`, `area_resolution_m2` = grid_m × w_min_m. `current_box` = ((kind, (I_off, I_max)), ...) MOS kind 이름순
  (I_max 잠정 -- S-3b). [결정 11] `area_budget_m2` = spec 판정 제약 `area_search_m2 <= v` 중 최솟값 또는 None(`search_domain(..., area_budget_m2)`).
  있으면 `current_box` 의 I_max 는 단일 finger 슬라이스 값이 아니라 **예산이 정하는 참 상한** ID_max = IDu_max · A / L_lo²
  (IDu_max = `_ln_idu_envelope` 상한 exp, L_lo = kind 의 최소 L 앵커; 소자 하나의 W·L ≤ A 이므로 W ≤ A/L) -- S-3b 닫힘.

### 3.19 [r2] `current_box(lut_access, kind) -> (I_off, I_max)`
- I_off = 레이아웃 전 폭 슬라이스(`w_keys[kind]`)의 VGS 격자 중 0(|v| ≤ ulp(격자 끝 크기)) 인 첫 index 면에서 on_mask 이고 ID > 0
  인 점의 ID 최솟값(SPICE 오라클 `off_current_A` 와 같은 열 -- LUT VGS=0 누설 ID).
- I_max = 그 kind 의 모든 슬라이스(`slice_map` 의 (kind, *))에서 on_mask 점 ID 최댓값(각 슬라이스 자기 폭의 ID -- finger 수 상한
  선언이 없어 다중 finger 합은 넣지 않는다, S-3b). **잠정값** -- 참 상한은 선언된 최대 nf 또는 면적 상한이 필요하다(notes
  verdict `provisional`).
- VGS 0 없음 -> `SchemaRejectedError`(reason `lut_vgs_zero_missing`), 유효 점 없음 -> (reason `lut_current_box_empty`).

### 3.20 [r2] `ss_constraint_rows(evaluation, declared) -> (rows, unmeasured)`
- `declared` = ((metric, op, value), ...). 비면 ((), ()). `evaluation.sealed is None` -> ((), 선언마다 (metric, op,
  "ss_requires_sealed_snapshot")). 봉인됨 -> ((), (metric, op, "ss_linearize_unavailable")). 행은 아직 만들지 않는다.
- **연결 자리**: metrics `ss_linearize` 가 `__all__` 에 들어오면 봉인된 경우 분기 하나를 '봉인 스냅샷 -> ss 레코드 -> metric_value
  -> 정규화 행'으로 바꾼다(호출부 `evaluate` 는 그대로). 봉인 7 대기 점은 그 뒤에도 '미측정'이다(DEC-67).

### 3.21 [r5] `layer0_start(sctx, origin=()) -> Layer0Result` -- 층 0 최소형(DEC-71 최소형, R D18·U-49)
`Layer0Result(start, t, hard_ok, stop, centre_u, start_status, start_failure, iterations, restarts, aborts, frozen,
kernel_calls, rows, probes, origin_point)`(frozen dataclass, 필드 뜻은 docstring). **의미 한정**: 층 0 시작점은 DC 정합(봉인
통과) 가능성만 뜻한다 -- W·면적 상한 선언이 없어(S-3b) pA 전류·거대 W 점일 수 있고, 탐색은 출발 근거 이상으로 쓰지 않는다(front·보고
값 아님; find_front notes `meaning "feasibility_only"`). 단계(정확히 이 순서):
1. **상자 중심**: `domain.variables` 마다 (lo + hi)/2(ln 변수는 ln 좌표 중점 -> θ 값 exp). L: `domain.l_cells` 의 MOS 마다 칸 j =
   argmin_j |(ln lo_j + ln hi_j)/2 − (ln min_k lo_k + ln max_k hi_k)/2|(동률 index 작은 쪽), θ L = (lo_j + hi_j)/2, 칸이 구간
   (lo_j < hi_j)이면 L 변수 `Variable((L, MOS), False, lo_j, hi_j)` 를 변수 목록 끝에 MOS 이름순으로 더한다. cells = 그 j 벡터.
2. **전류 중심**(θ 전류 변수가 있고 `schema.current_cone` 이 비지 않을 때, 커널 0): 변수 z = θ 전류 변수의 ln 값, u ≥ 0.
   q_m(z) = I_m(z)/I_c,m, I_m = Σ (num/den)·(e^z 또는 `schema.fixed` 값), I_c,m = √(I_off·I_max)(그 MOS kind 의
   `domain.current_box`). scipy SLSQP(기본 ftol·maxiter): 최소화 u, 제약 q_m − e^(−u) ≥ 0·e^u − q_m ≥ 0(원뿔 행 중 θ 전류
   변수를 하나라도 읽는 행 -- `schema.fixed` 만 읽는 행은 움직일 수 없어 빼고, 그 행의 원뿔 판정은 3 의 `cone_rows` 가 한다),
   bounds = 변수 bounds·u ∈ [0, ∞), 출발 z = 1 의 값, u = 양의 q 중 max |ln q|(없으면 0). 결과 z 를 bounds 로 자른 값으로 θ 전류를
   바꾸고 `centre_u` = 해 u. 해의 원뿔 행(`cone_rows`)에 c ≤ 0 이 있으면 커널 없이 3 의 시험으로 간다(`start_status`
   "centre_outside_cone").
3a. **[r11] 정준 변수 순서·Halton 차원**(구현 = 3.23 `canonical_order`): 변수 목록(정의역 변수 + 칸이 구간인 L)을 (L 인가, 성분 종류, 키 구조 색) 오름차순으로 정렬한
   뒤 이름은 같은 키 안에서만 tie-break 로 쓴다. 키 궤도 id = sizing `dc_struct_colour` 의 궤도 산출(3.0b, 정준 라벨링의 자기동형 궤도)의 원소
   `device.dc_orbit`(`y` 성분의 키가 넷이면 `node.dc_orbit`, 둘 다 아니면 -1). [r12] 묶이지 않은 변수는 키가 유일하다. **Halton 차원 = 서로 다른 (성분 종류, 구조 색) 키의
   순위**(L 키는 맨 뒤 -- 종래 'L 은 변수 목록 끝'과 같은 자리): 차원 d 에 (d+1) 번째 소수 기저, **같은 키의 변수는 같은 차원 =
   같은 좌표 φ**(1-WL 로 구별되지 않는 변수 = 자기동형 궤도 후보를 한 차원으로 묶어, 궤도 구성원의 어느 쪽이 먼저인지 이름에 기대지 않는다).
   hit-and-run 의 방향 d_j = 2φ − 1 도 차원 좌표라 궤도 안에서 같고, 걸음 비율 φ_s = 마지막 차원(키 수 + 1 번째 소수). 시험 점·
   방향·걸음은 원소 치환 σ(이름 전단사)에 대해 θ 를 σ 로 옮긴 것과 같다(키 순위가 이름을 읽지 않으므로). 한계: 1-WL 이 자기동형이
   아닌 원소를 같은 색으로 남기면(정정규 그래프류) 그 원소들도 같은 좌표를 받는다(결정론은 유지, 탐색 다양성만 줄어든다).
   최대-최소 SLSQP·전류 중심·수리의 변수 순서도 이 정준 순서다(`_box_centre` 가 정렬해 돌려줌).
3. **출발점 평가** `evaluate(sctx, θ, cells, origin = origin + (("stage", "layer0"),))`(`start_status` = 그 상태, `start_failure` =
   그 레코드). 받아들일 상태가 아니면 [r5, S-4b] **Halton 시험**: 변수 차원 d(3a 의 정준 순서)에 (d+1) 번째 소수 기저, 시험 k = 1, 2, … 의 점
   x_i = lo_i + φ_{b_i}(k)·(hi_i − lo_i)(φ = 근기 역순(radical inverse), 스크램블 없음; ln 변수는 ln 좌표라 ln 균등), 나머지 θ
   (전류 중심을 거친 θ 의 고정 성분)·cells 는 그대로. [r5b] **θ 전류는 원뿔 안 hit-and-run**(전류 중심이 원뿔 안이고 θ 전류·원뿔
   행이 있을 때): 기저 수 = 변수 수 + 1(마지막 소수 = 걸음 비율 φ_s). 선형 전류 좌표의 점 p(처음 = 전류 중심)에서 방향
   d_j = 2·φ_{b_j}(k) − 1(전류 변수 j), 열린 현 (t_lo, t_hi) = 상자 [e^lo, e^hi] 와 원뿔 행 Σ w·(p + t·d) + 고정 > 0 의 교집합,
   t_lo·t_hi 가 둘 다 유한이고 t_lo < t_hi 면 p ← p + (t_lo + φ_s·(t_hi − t_lo))·d, 아니면 p 그대로([r8b] 방향이 0 -- 예: θ 전류 변수
   하나에서 기저 2 의 첫 시험 φ = 1/2 -- 이면 현의 양끝이 무한이라 걸음 없음; 무한 × 0 = NaN 을 만들지 않는다), θ 전류 = p(상자로 자름). p 는 받아들임과 무관하게 다음
   시험으로 이어진다(사슬). 전류 중심이 원뿔 밖이면 전류도 위 상자 Halton. [r5c] **칸 정점 하한**: `ln_idu` 변수(= 쓰기 소자 m)의
   시험 하한 lo'_m = max over {m 의 L 칸 [lo, hi] 안 LUT L 앵커(± spacing)} × {VDS·VS 전 격자} 의 곡선(정점 마디가 on_mask 인 곡선만)
   에서 gm/ID 정점 마디의 ln IDu(= lnID + ln L − ln w_m) -- (kind, w_key, 칸) 마다 이 호출 안에서 1회. lo < lo'_m < hi 일 때만 적용
   (그 밖은 원래 상자), 시험 점 = lo'_m + φ·(hi − lo'_m). **모든 쓰기 소자에 적용**: 보장('어느 격자 동작점에서도 좌표가 강반전 분지
   시작 위' = 그 칸 앵커 L 에서 `inversion_floor` 행 c ≥ 0)이 소자 역할과 무관하게 (kind, w_key, 칸) 만으로 정해져 diode 와 같다
   (diode 는 이 보장이 곧 노드 근 존재의 필요조건, 일반 writer 는 연속 제약 하나를 미리 만족). 칸 안 앵커 사이 L(선형 보간)의 정점은
   따로 묶지 않았다(앵커 최댓값). 최대-최소 SLSQP 의 bounds 는 원래 상자 그대로. k 마다 시험 전 한도: `_budget_stop`(kernel_calls ≥ E_B 또는 벽시계 -> stop 접미
   `probe_eval_budget`·`probe_wall_budget`), deadline 이 None 일 때만: E_B 도 None 이면 `probe_budget_undeclared`, 시험 수 ≥ E_B 면
   `probe_eval_budget`(원뿔 밖 점은 커널 0 이라 커널 수만으로 끝나지 않는다 -- deadline 이 있으면 벽시계가 끝을 보장한다). `evaluate(..., origin = tag + (("probe", k),))`, 처음
   받아들일 상태인 점에서 멈추고 그 점이 4 의 출발점(`origin_point` "halton:<k>", `probes` = k). 없으면 start None, stop =
   "start_" + (출발 실패 사유 또는 상태) + "+" + 한도 사유. 중심이 받아들여지면 `probes` 0, `origin_point` "centre".
   [r8] 칸 정점 하한 계산은 `cell_floor.ln_idu_floors(sctx, variables, cells)`(3.22, 캐시 `sctx.cell_floors`).
3b. **[r8] 1단계(시험 묶음마다)**: 시험을 묶음 n + 1 개(n = 변수 수, FD 한 sweep -- E_B 유도와 같은 단위)씩 센다. 묶음 안에서 '수리 가능'
   실패(reason `no_root_in_window`, detail 에 `h_lo`·`h_hi` 가 있고 둘 다 유한, record margin 있음 -- 위반 크기 = margin = 창 끝 |h|
   최솟값 / writer tol_V, sizing 정규화) 중 margin 최소인 점(동률 = 먼저 시험한 점)을 고르고, 묶음이 끝나면 그 점에서 **좌표 수리**:
   (i) 실패 소자 m(record devices[0])이 이 사슬에서 이미 나왔으면 끝 (ii) 후보 좌표 = [m, 실패 노드(detail `node`) writer 식의 '아는
   쪽' 노드(`dc_writer.known`)를 쓰는 소자(있고 m 이 아니면)] 순서, `ln_idu` 변수가 없는 후보는 건너뜀. 후보마다 끝값 (칸 정점 하한 또는
   lo, hi) 순서로 그 좌표만 바꿔 평가, m 의 같은 실패(`no_root_in_window` 이고 devices[0] = m -- 유한·무한 무관)가 아닌 첫 끝을 통과 끝으로
   하고 그 후보를 쓴다(모든 후보·끝이 같은 실패면 끝). 두 번째 후보는 적층 diode 처럼 근이 창 밖인 원인이 아래 노드 전압일 때다(r8
   초안 실측: current_reuse 수리 6회 모두 m 좌표 양끝이 같은 실패) (iii) 불변식 '현재 좌표 쪽 = 같은 실패, 통과 끝 쪽 = 아님'으로 ⌈log2(|끝 − x| / res)⌉ 번 bisection(|끝 − x| ≤ res 면
   0 번), res = tol_V · (gm/ID 최대), tol_V = 그 record 의 끝 |h| 최솟값 / margin, gm/ID 최대 = 고르는 후보 소자 kind 의 레이아웃 전 슬라이스 on_mask 점의
   GM/ID 최댓값(d ln ID = gm/ID·dVGS 의 상한) (iv) 통과 쪽 마지막 점이 받아들일 상태면 출발점(`origin_point` "repair:<k>", k = 그때까지
   시험 수), 아니면 그 점의 실패로 (i)부터(사슬). 평가 전마다 `_budget_stop`. 사슬 기록 = `Layer0Result.repairs`(묶음마다 고친 소자 tuple).
   위반 크기가 없는 실패(빈 창·NONCONVERGENT·LUT 실패·h 무한)는 그 점에서 수리하지 않는다. SLSQP 대신 좌표 bisection 인 이유: 커널은
   SCC 순서의 첫 실패 노드에서 멈춰 한 점이 위반 크기 하나만 주고(최대·합을 만들 수 없다), FD 스텝이 받아들인 기준 스냅샷을 읽어
   실패 점에서 Jacobian 을 만들 수 없다.
4. **최대-최소**: 변수 x(1 의 목록, [r8] 1변수 노드 writer 의 ln_idu 하한 = 칸 정점 하한 -- 출발 좌표는 넘지 않음, S-4f) + t. t 행 = 출발점 봉인 보고 항목 중 margin 이 유한한 항목 i(번호순), 이름
   `ROW_SEAL_ITEM:<i>`, s_i = 1 − margin_i. 경성 행 = 커널 제약 중 이름이 `w_min:`·`inversion_floor:` 로 시작하는 행(커널 순서) +
   원뿔 행. SLSQP: 최소화 −t, 제약 [s − t ; c] ≥ 0, bounds = 변수 bounds + t 무한, ftol 1. 행 이름 집합이 출발점과 다르거나 점이
   받아들일 상태가 아니면 중단 -> `solve_eps`(3.13)와 같은 재시작·열 고정·한도·예산 규칙(maxiter·재시작 상한 식 동일, stop 어휘
   동일: converged / slsqp_<status> / eval_budget / wall_budget / restart_cap / all_columns_frozen). 출발 t = 그 중심점의 min s.
5. 결과 = 수락 반복 중 키 (경성 행 모두 ≥ 0, min s, −seq) 최대인 점. `start = StartPoint("layer0", 그 점 θ, cells, "layer0")`,
   `t` = 그 점 min s, `hard_ok` = 그 점 경성 행 모두 ≥ 0, `kernel_calls` = 이 호출 동안 늘어난 `counters["kernel_calls"]`,
   `rows` = t 행 이름.
- 넓은 except 없음(`evaluate` 가 후보 실패만 상태로 바꾼다). 결정론: 난수·시간 없음(예산·벽시계 정지만 3.13 과 같이 기록).
- 범위 밖(최소형): 블록 gain 예산(GB3·GB4), LR5 knee, GB5 근사식, spec 성능 제약(ss 행·`spec:` 행은 t·경성 행에 넣지 않는다).
  출발점이 받아들일 상태가 아닐 때 '봉인 위반 margin 으로 끌어오는' 연속 1단계 대신 Halton 시험을 쓴다(9절 S-4b).

### 3.22 [r8] `ln_idu_floors(sctx, variables, cells, one_var_only=False, start=None) -> {변수 index: 하한}` (`cell_floor.py`)
- 칸 정점 하한(kind, w_key, 칸) = 칸 [lo, hi] 안 LUT L 앵커(± `np.spacing`) × VDS·VS 전 격자의 곡선 중 gm/ID 정점 마디가 on_mask 인
  곡선마다 정점 마디의 lnID + ln L − ln w_m, 그 최댓값. `sctx.cell_floors` 에 (kind, w_key, 칸) 키로 1회.
- `variables` 의 `ln_idu` 성분(소자 m, kind = device.kind, w_key = 레이아웃 전 폭)마다 m 의 칸(`cells` 는 `domain.l_cells` 순)의 하한.
  `one_var_only` 면 1변수 노드 writer 만: `node.dc_writer` 의 관계가 `REL_VGS_GATE`·`REL_VGS_SOURCE` 이고 그 노드가 writer 소자의
  d·s·bulk 중 하나(sizing `self_referential` 과 같은 판정; 집합은 `sctx.cell_floors` 에 1회). `start`(θ Mapping)가 있으면 하한 =
  min(하한, start[성분]). 원래 lo < 하한 < hi 일 때만 결과에 넣는다.
- 쓰는 곳: `solve_eps._layout`(one_var_only, start = 시작 θ), 층 0 최대-최소(같은 인자), 층 0 시험·수리(모든 쓰기 소자, start 없음).
- **[r9] 전도 하한**(sizing r8 봉인 9 -- 판정 권한은 봉인 9, 이 하한은 그 거부 영역에서 평가를 아끼는 상자): 칸 전도 하한(kind, w_key,
  칸) = 칸 안 L 앵커 a × VDS 격자 k × VS 격자 s 곡선마다(tol = lut `tol_v_table(memo, kind, w_key).at(L_a, VDS_k, "id_equivalent")`,
  None·0 이면 그 (a, k) 곡선 제외; VGS 격자의 0 마디 z(|VGS| ≤ spacing(max|VGS|), 없으면 칸 전도 하한 None)가 on_mask 인 곡선만)
  f_i = log_GM[a, i, k, s] + ln tol − log_ID[a, z, k, s](= ln(gm·tol_V / I_off), 같은 슬라이스 폭 -- W/L 지워짐, 봉인 9 margin = 1 ⇔
  f = 0). on_mask 이고 f ≥ 0 인 첫 마디 j 가 있고 j > 0 이고 j − 1 마디도 on_mask 이면 근 = lnID[j−1] + t·(lnID[j] − lnID[j−1]) + ln L_a
  − ln w_m, t = −f[j−1]/(f[j] − f[j−1]); 그 밖의 곡선은 제외. 칸 전도 하한 = 근들의 최댓값(곡선이 하나도 없으면 None). 캐시
  `sctx.cell_floors[("conduction", kind, w_key, 칸)]`.
- [r9] 성분별 하한 = max(칸 전도 하한(None 아니면), 칸 정점 하한(one_var_only 가 아니거나 m 이 1변수 writer 일 때)). 전도 하한은
  **모든 `ln_idu` 성분**에 붙는다(one_var_only 여도). 둘 다 없으면 그 성분은 결과에 없다. `start` 캡은 start 에 그 성분이 있을 때만
  (없으면 캡 없음 -- r8 은 KeyError).
- [r9] 실측(LUT v2): L 칸 (0.7, 1) µm 에서 nmos 전도 하한 ln IDu −26.48(VDS 격자 중간·VS 0 곡선에서 VGS 0.142 V), pmos −38.36(0.136 V);
  칸 정점 하한은 nmos −30.22(0.006 V), pmos −42.00(0.015 V) -- 전도 하한이 더 크다(보수: 격자 전체 최댓값이라 sizing O17 의 L 1 µm
  VGS* nmos ≈ 0.14 V·pmos ≈ 0.12 V 보다 pmos 쪽이 조금 높다).
- [r9] **기대값이 바뀌는 기존 test(작성자 갱신 몫, 고치지 않음)**: `tests/search/test_cell_floor.py::test_one_var_only_selects_diode_writer`·
  `test_one_var_only_empty_for_gate_writers`·`test_start_coordinate_caps_floor`·`test_cell_floor_cache_is_read`(캐시 키 수)·
  `test_real_lut_v2_multi_anchor_cells`, `tests/search/test_layer0_center.py::test_halton_hit_and_run_probe_points`·
  `test_repair_bisection_count_and_points` -- 모두 전도 하한이 더해져 하한 값·성분 집합·캐시 키가 바뀐 것.

### 3.8 [r3] `constraint_rows(snapshot, lut_access, w_min_m, grid_m) -> (rows, undefined)`
- MOS 마다(`dc_op` 열 순서) 먼저 [r3] `w_min:<m>` c = (dc_op.W − w_min_m)/grid_m(**설계 개정 S-18**, tol 과 무관하게 늘 있음),
  그다음 tol = `dc_tol_v`; None 또는 ≤ 0 이면 `undefined` 에 이름(정렬) 하고 그 MOS 의 나머지 행 없음.
- `seal6_bulk:<m>` c = (min(vsb, vds + vsb) + tol)/tol. 쓰기 소자(`dc_coord.role == "writer"`)면 `inversion_floor:<m>`
  c = (ln_idu − r_peak)·gm_id/tol, r_peak = ln(curve.id_vals[argmax gm_id_vals]) + ln L − ln w_m(`gm_id_curve(memo, kind,
  w_key, L, vds, vsb)`). `active` = c ≤ 1.

### 3.9 [r3] `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl) -> SearchContext`
- 정의역 = `search_domain(dc_ctx, settings, pdk_decl)`.
- `context_fp` = fp_of((base.fp, plan_versions, lut, fixed_values, resistor_values, inputs)), `schema_fp` = fp_of(schema),
  `code_fp` = core·lut·graph·sizing·metrics·search `*.py` 바이트 sha256 묶음의 fp.
- [r2] `spec.judged_constraints` 를 문서 순서로: 값 None -> `constraint_notes`(verdict `judgment_pending`, reason
  `constraint_value_pending`, decision), metric ∈ AXES -> `judged_constraints` ((metric, op, value), ...), 그 밖 ->
  `ss_constraints`(같은 형식) + `constraint_notes`(verdict `unmeasured`).
- `eval_budget` = settings.eval_budget, `deadline` = None(find_front 가 정함).
- `archive_root` 가 None 이면 S3 없음. 아니면 `S3Archive(root, context_fp, code_fp)` 이고 `disk_failures` = evals 의 ok 아닌 줄
  (같은 schema_fp·code_fp) -> {EvalKey: FailureRecord}.
- `counters` 키: requests, kernel_calls, hits, fail_hits, disk_hits, outside_domain, recompute_same_key(모두 0 시작).

### 3.10 `evaluate(sctx, theta, cells, parent=None, origin=(), geometry=None) -> EvalResult`
[U14] `geometry` = `RealizedGeometry(w_request, w_keys, diffusion=())`(search_values, `search.__all__`; MOD8 `convergence` 의 재검증 입력, LY7·LY8): 있으면 1 의 키 `w_fixed_fp = fp_of(geometry)`,
5 의 커널은 `LutAccess(memo, geometry.w_keys)` 로 `size_and_seal(dc, θ, parent=parent.evaluation, w_request=geometry.w_request)`, 6 의 `ss_evaluate`·`constraint_rows` 도 같은 `dc`
(`ss_evaluate(diffusion=geometry.diffusion)` -- 접합 용량이 실현 확산 기하). 없으면(None) 아래가 종전과 같다. 같은 (θ, cells, geometry) 는 캐시 적중, 계획 블록 버전은 슬라이스와 무관해
`parent` 를 그대로 쓴다. S3 evals 줄의 `w_fixed_fp` 도 이 값이다.
순서와 계수(정확히 이 순서):
1. requests +1. 키 = `eval_key(..., 키 정렬 θ, cells, None)`.
2. 메모리 캐시 적중 -> hits +1(실패면 fail_hits 도 +1), 같은 객체(`is`) 반환. 커널 0.
3. 디스크 실패 적중 -> disk_hits +1, `STATUS_FAILED`(failure = 디스크 레코드, seq −1), 캐시 저장. 커널 0.
4. `cone_rows` 에 c ≤ 0 -> outside_domain +1, `STATUS_OUTSIDE_DOMAIN`(seq −1), 캐시 저장. 커널 0, S3 줄 없음.
5. kernel_calls +1, seq +1, `size_and_seal(dc, θ, parent=parent.evaluation)`. `NonconvergentError`·`SealViolationError` 만
   잡아 `STATUS_FAILED` + `exc.record`. 그 밖 예외는 전파(캐시·계수는 kernel_calls 까지 증가한 채).
6. 성공: 상태 = `seal_status`. 목적 = `objective_values`(저항 = dc resistor_values + θ resistance). [r2] b_P 가 None 이면
   상태 = `STATUS_UNDEFINED`. `STATUS_UNDEFINED` 가 아니면 제약 = `constraint_rows` 행 + 목적 축 spec 행(`spec:<m><op>`,
   c = (값 − 목표)/분해능(>=) 또는 (목표 − 값)/분해능(<=), 분해능 = 그 점의 b_P 또는 b_A) + `ss_constraint_rows` 행,
   `unmeasured` = ss_constraint_rows 의 미측정 목록.
7. 캐시 저장, archive 가 있으면 evals 한 줄(8절). [r2] `eval_budget` 이 None 이고 평가 시간 수 > n 이면 E_B 를 정한다(1.1).
- 같은 키를 커널로 두 번 계산하면 recompute_same_key +1(캐시가 막으므로 정상 0).

### 3.11 `fd_jacobian(sctx, variables, x, base, cells, to_theta, origin, skip=frozenset()) -> ((EvalResult | None, step), ...)`
- [r2] index ∈ `skip`(고정된 변수) -> (base, 0.0), 평가 없음.
- 스텝(base 스냅샷에서): `ln_idu` = (dc_op.vgs 를 품는 VGS 격자 칸 폭) × gm_id; `y` = 첫 w_key 슬라이스 VDS 격자 최소 간격 /
  (그 y 키를 쓰는 노드 `dc_window` 의 hi − lo)(창 없음·폭 0 -> None); `current` = 그 기저를 항으로 갖는 MOS 의 tol·gm_id 최솟값
  (없으면 전 MOS 최솟값, 그것도 없으면 None); `resistance` = (전 MOS tol 최솟값) / (|dc_drop_current|·R)(강하 0 -> 0);
  `L` = [r5] PDK 제조 격자 한 칸 `domain.grid_m`(유도: bin 안 L 은 이웃 앵커 사이 선형 보간이라 앵커 칸 안 어느 할선도 같은
  기울기 -- 앵커 간격 스텝은 칸 중점에서 양방향 모두 칸 밖이 되어 r4·r5 초안 실측 9회로 L 열이 전부 고정됐다. 격자 한 칸은 실현
  가능한 최소 L 변화이고 칸 안에 머물러, 고정은 양쪽 평가가 실제로 실패할 때만 일어난다 -- S-16). ~~r4: 그 변수 칸 안 앵커 간격~~.
- 스텝 0 -> (base, 0.0)(평가 없음). None -> (None, 0.0). x + h > hi 면 h = −h. h, −h 순으로: 값 = x + 스텝, bound 와 1 ulp
  이내면 bound 로 맞추고 스텝 = 값 − x; bounds 밖이거나 값 == x 면 건너뜀; 아니면 `evaluate(..., parent=base)`. 처음 받아들일
  상태인 것을 (결과, 실제 스텝)으로. 둘 다 아니면 (None, h).

### 3.12 `start_points(sctx, given, layer0=()) -> (starts, log)`
- [r5] 후보 = `layer0`(StartPoint iterable -- 그 `source`·`theta` 를 쓴다, 보통 `layer0_start` 결과 0 또는 1개) 다음 S3 runs(같은
  schema_fp·code_fp)의 front·pending_front 점 θ(`theta_hex` 복원) 다음 `given`. `layer0` 기본값 () 이면 r4 와 같다.
  층 0 점의 평가는 이미 캐시에 있어 여기서 커널 0(hits +1). 칸 = L 마다 [lo − ulp, hi + ulp]
  가 품는 첫 칸(없으면 `ValueError`). 후보마다 `evaluate`(id "s<n>", 1부터) 1회 -> log 항목 {id, source, status, seq, fail?}.
  받아들일 상태이고 처음 보는 키면 `StartPoint`.

### 3.13 [r2] `solve_eps(sctx, start, minimize, eps, origin) -> SolveResult`
- 변수 = domain.variables + 시작 칸이 구간인 MOS 의 L(칸 bounds). 칸이 한 점인 L 은 칸 lo 로 고정. [r8, S-4f] 1변수 노드 writer 의
  ln_idu 하한 = `ln_idu_floors(sctx, 변수, start.cells, one_var_only=True, start=시작 θ)`(3.22). x0 = 시작 θ(log 변수는 ln),
  bounds 로 자름. 축 분해능 = {power: 첫 받아들인 점(시작점)의 b_P, area: b_A} -- 풀이 하나 동안 고정. 목적 = 축 값/분해능,
  제약 = 커널 행 + 원뿔 행 (+ ε 행 (ε − 값)/분해능).
- 시작점이 받아들일 상태가 아니면 즉시 `SolveResult(None, eps, minimize, 0, 0, "start_<사유>", ())`.
- 같은 x(float.hex)는 한 번만 평가. x 평가 parent = 직전 수락 반복, FD parent = 그 x 평가.
- **한도(평가 수, 결정론)**: maxiter = max(1, Σᵢ max(⌈log2((hiᵢ − loᵢ)/hᵢ)⌉, 1))(hᵢ = 시작점 FD 실제 스텝 크기 > 0 인 변수만),
  재시작 상한 = max(1, ⌈log2(max 반경 / 최소 hᵢ)⌉). 새 x 를 평가하기 전 `kernel_calls ≥ eval_budget` -> stop `eval_budget`,
  `perf_counter > deadline` -> stop `wall_budget`(둘 다 재시작 없이 끝).
- 중단 사유: `candidate_failure`·`constraint_set_changed` -> 재시작(마지막 수락 x 중심, 반경 = (hi − lo)/2 / 2^k; 중심이 바뀌면 고정
  해제). `fd_column_failure`(열 i) -> 그 점이 마지막 수락 x 가 아니면 먼저 수락(고정 해제), 열 i 를 고정(bounds lo = hi = 중심 값)하고
  같은 중심에서 다시(재시작 수에 안 넣음); 모든 변수가 고정되면 stop `all_columns_frozen`. `aborts` = 순서대로 사유("frozen:<kind>:<key>"
  포함), `frozen` = 고정한 변수. 정상 끝: SLSQP(ftol 1) success 면 "converged", 아니면 "slsqp_<status>".
- `best` = 수락 반복 중 모든 c ≥ 0 이고 (목적, seq) 최소. 없으면 None.

### 3.14 [r2] `polish_l_cells(sctx, solved, origin) -> (SolveResult, ...)`
- 설계 4.3 L-b(본문 docstring). 새 칸의 L = 위로 이동이면 새 칸 lo, 아래로면 hi. 시험 조건: 받아들일 상태 ∧ (목적 감소 ∨ 음의
  제약 합 증가). 수락 = 재시작 해 목적 개선 ≥ 1(정규화 한 칸 -- 전력은 그 바퀴 기준점의 b_P). 한 바퀴 수락 없음 또는 평가 예산·
  벽시계 도달 -> 끝.

### 3.15 [r2] `sweep_front(sctx, starts) -> dict`
- 키: `solves`((id, SolveResult) -- 끝점 id "EP:<start>"/"EA:<start>", ε 점 "eps:<축>:<k>", L-b "L:<점>:<n>"), `failed_eps`
  (항목 {eps, minimize, stop, aborts, accepted, start?}), `resolution`(정렬 쌍: b_A_m2, b_P_rule, estimated True, coarse_factor,
  E_refilter 0, refilter "mod8_not_implemented", E_B; 끝점이 둘 다 있으면 N_eps·e_eps·E_fixed·b_P_grid_w),
  `front`·`pending_front`(FrontPoint), `*_removed`((id, 지배자 id)), `*_folded`.
- ε 격자 점 수 = 열린 구간 (lo, hi) 안 hi − k·간격 점 수. N_ε = ⌊(E_B − E_fixed)/e_ε⌋(e_ε = 끝점 풀이 kernel_calls 중앙값).
  총수 > max(N_ε, 0) 이면 간격 배수 ×2 반복. 전력 간격 = max(b_P(E_P), b_P(E_A)). 비지배 필터 전력 동률 폭 = max(b_P(p), b_P(q)).

### 3.16 [r2] `find_front(sctx, given_starts) -> SearchFront`
- [r5] 순서: deadline 설정 -> `layer0_start(sctx)` -> `start_points(sctx, given_starts, (층 0 start,) 또는 ())` -> 스윕. notes 의
  옛 `{verdict "blocked", reason "layer0_inputs_missing"}` 대신 `{verdict "layer0_minimal"(시작점 있음) | "layer0_no_start",
  rule "DEC-71", reason "seal_margin_maxmin_centre", stop, t, hard_ok, start_status, centre_u, kernel_calls, probes,
  origin_point, meaning "feasibility_only", meaning_reason "w_area_upper_bound_undeclared_S-3b",
  refinements_out_of_scope [GB3·GB4 블록 gain 예산, LR5 knee, GB5 근사식]}`. 층 0 평가도 perf 계수(kernel_calls 등)에 든다.
- deadline = 시작 시각 + B. E_B 는 선언 또는 `evaluate` 의 한 번 유도(1.1) -- perf `eval_budget_source` 에 기록. ε 게이트 때
  E_B 가 아직 None 이면 N_ε = 0.
- `front` = 봉인된 점만(지금은 항상 ()), `pending_front` = 봉인 7 대기 비지배 점. `notes` 에 판정 보류 사유: constraint_notes,
  DEC-79 review_needed, DEC-72 추정, MOD8 재필터 미실행, 층 0 막힘(`layer0_inputs_missing` + 빠진 입력 목록), supply_current_dc
  미계산, ss 미측정(`unmeasured` -- 제약 목록과 점 수), 봉인 7 대기.
  `perf` = counters + unique_keys, eval_time_median_s, wall_s, lut_memo_evictions, block_*(sizing 계산 블록 12개), n_starts, n_solves,
  eval_budget, eval_budget_source, frozen_columns, stops_eval_budget, stops_wall_budget.
- `run_id` = fp_of((context_fp, code_fp, settings, E_B, 시작 θ들)). archive 가 있으면 runs 한 줄 + front·대기 front 점 스냅샷 파일.

### 3.17 `node_across_front(front, node, archive=None) -> (NodeRow, ...)`
- 원소가 `FrontPoint` 면 메모리 스냅샷, dict(runs front 항목)면 `archive.read_snapshot(entry["snapshot_ref"])`(archive 없으면
  `ValueError`). 노드 없음 -> `KeyError`. 전압 = dc_rail_v 또는 dc_v, tier = dc_writer.tier, devices = pins 에 그 넷이 있는 MOS
  ((소자, 단자들, ((vgs, vds, vsb, current, gm_id, W, L) 쌍))). 커널 호출 0.

### 3.18 `S3Archive(root, context_fp, code_fp)` -- 8절.

### 3.22 [r11, 사용자 결정 11] 면적 예산 `passive_area_decl(dc_ctx, spec, pdk_decl) -> PassiveAreaDecl` (`area_decl.py`)
- 면적 예산 = spec 일반 제약 `area_search_m2 <= v`(판정 축). 새 제약 종류가 아니다: `build_search_context` 가 `judged`(AXES)로 받고
  `kernel._spec_rows` 가 `spec:area_search_m2<=` 행 c = (v − 점 면적)/b_A 로 잰다(분모 = `area_resolution_m2`, 설계 5절 NFR-5). 면적 =
  MOS 게이트 W·L + 회로 안 커패시터(PDK `mim_cap_density_f_per_m2` 의 역수 x 값) -- 저항은 PDK 단위 면적 선언이 없어 `passive_area_undeclared` 로 보고.
- 제외 = spec `element_values.<원소>.measurement_load` 가 true 인 수동소자(CL·nmcnr RL). 이름 기반 코드 없음. `SearchContext.area_decl`
  (`PassiveAreaDecl`)이 `ss_evaluate`(봉인 점)와 `metrics_dc`(그 밖 점) 둘 다에 같이 들어간다 -- 점 상태와 무관하게 같은 면적.
- 레이아웃 판정 축(MOD7 floorplan 외곽 면적, MOS 행만)은 수동소자를 이미 포함하지 않으므로 같은 제외(부하 없음)이다. 재필터(MOD8)는 아직 없다.
- 입력 검사: `pdk_decl` 에 그 quantity 가 없으면(`pdk_quantity_undeclared`) 커패시터도 미선언 보고, 다른 거부 사유는 그대로 올린다.

### 3.23 [r11, r12] `canonical_order(sctx, variables) -> (정렬된 변수 tuple, 변수별 차원 index list, 차원 수)` (`canonical_order.py`)
이름을 읽지 않는 θ 변수 순서. `variables` = `Variable` 열(정의역 변수 + 칸이 구간인 L 변수, 순서 무관). 호출부: `layer0_center`
(`_box_centre`·`_halton_probe`), `slsqp_outer` (`_layout`). `fd_jacobian`·`ln_idu_floors`·`eps_sweep`·`find_front` 는 호출부가 넘긴 변수
순서를 따를 뿐 스스로 정하지 않는다.
1. 키 = (성분 종류 == L, 성분 종류, 궤도 id). 궤도 id = `device.dc_orbit`(성분 키가 원소일 때), 아니면 `node.dc_orbit`(`y` 의 넷), 둘 다
   없으면 -1. 정렬 = (키, 구조 색, 이름) -- 같은 키 안은 정점마다 유일한 구조 색이 정한다. [r12] 정의역 변수는 3.24 묶음 뒤라 키가 유일하다; 같은 키는 spec 이
   묶음을 푼 궤도(`untie_orbits`) 안에서만 남는다.
2. 차원 = 서로 다른 키의 오름차순 순위(0 부터). 변수의 차원 = 자기 키의 순위. 차원 수 = 서로 다른 키 수.
3. 불변식(test 가 확인할 성질): (a) 이름 전단사 σ·원소 순서 섞기에 대해 정렬된 변수의 (종류, 키, 차원) 열이 같다(이름만 σ 로 옮겨짐);
   (b) 같은 키 ⇔ 같은 차원; (c) 입력 순서에 결과가 불변(순열에 대해 같은 출력); (d) L 키는 모든 비-L 키 뒤; (e) 같은 입력이면 같은 출력
   (결정론); (f) 반환 변수 집합 = 입력 집합, 개수 보존; (g) 차원 index 는 0 .. 차원 수 − 1 을 빠짐없이 쓴다.
4. **비트 동일성 (r12)**: 묶음(3.24)·정준 행 순서(3.25)·metrics/objectives 의 정준 합산·행렬 순서(`dc_colour`, metrics CONTRACT r12) 뒤에는 탐색 변수·제약 행·원뿔 항·
   소신호 선형계·합산 어디에도 이름이 순서를 정하는 자리가 없다(spec 이 묶음을 푼 궤도 제외). 그래서 이름 치환·원소 순서 섞기에 대해 층 0 시작점(θ·L 칸·t·
   `origin_point`)과 SLSQP 반복·평가 값(봉인 margin, W 하한·반전 하한·원뿔 행, `ss:` 행, 전력·면적·b_P)이 **비트 동일**하다(허용오차 없음). 묶음을 푼 궤도 안
   변수의 상대 순서만 이름을 따른다(비대칭 사이징을 명시한 선택 -- 거기서는 이름 치환 불변이 보장되지 않는다). 한계: 정준 순서는 모든 정점을 구별하는 키가
   아니라 자기동형 궤도 단위다 -- 같은 궤도(= 묶음) 원소끼리의 합산 순서는 이름이 정하지만, 궤도 구성원은 θ 가 같고 자기동형 대응이라 합산 항의 다중집합이 같아
   (묶음 안 항의 순열) 합이 바뀌는 건 부동소수 결합 순서뿐이다 -- 이 잔여는 측정 항목(9회로 중 궤도가 둘 이상인 회로는 current_reuse 하나, 10.1 측정).

> **[U17-1d] 개정(2026-10-12, 설계 40 §6-8·§2.4.8)**: (a) 궤도는 graph 대칭 블록 필드 `graph/s1: orbits`(옛 `device/node.dc_orbit`), 생성자별 전류 부호는
> `graph/s1: current_symmetry`(옛 `graph.dc_symmetry` + 여기서의 수동소자 첫 단자 부호 계산 -- 삭제)를 읽는다. 부호 −1 은 MOS d/s 맞바꿈도 포함한다(graph `reverses_orientation`).
> 전도 MOS 자기 맞바꿈은 graph 가 `ds_self_swap_zero_current` 로 정지시켜 여기 오지 않는다. (b) **D-1**: `search_domain` 에서 대표와 다른 궤도인(KCL 이 유도한) θ 전류 구성원(부호 +1)은
> 대표 상자를 구성원 상자와의 교집합으로 줄이고, 비면 `SchemaRejectedError`(gate `search_domain`, reason `tied_current_box_empty`, elements, box)로 거부한다. 같은 궤도 안 불일치는
> 종래대로 `tied_orbit_bounds_differ`. 아래 본문의 `dc_orbit`·`dc_struct_colour`·`dc_symmetry` 는 이 필드로 읽는다.

### 3.24 [r12, U2] `orbit_ties(dc_ctx, components, untied, symmetry=None) -> (대표 성분 tuple, ties)` · `current_symmetry(dc_ctx, untied) -> CurrentSymmetry(ties, negated, zeros)` · `expand_ties(ties, theta, negated=(), zeros=()) -> dict`
사용자 결정(2026-10-08): 같은 자기동형 궤도 원소의 같은 종류 θ 성분은 **한 탐색 변수**로 묶는다(기본 묶음). 공유 gm/ID(`ln_idu`)·L·`y`·저항·커패시터 값은 같은 값, **θ 전류는 자기동형이 만드는
부호 관계**('대칭 묶음 방식: b')로 묶는다. 자기동형은 graph `canonical_form`(2단자 수동소자 무향)의 생성자다.
1. **비전류 성분**(ln_idu·L·y·저항·커패시터): 궤도 id = `device.dc_orbit`(키가 원소일 때), `y` 의 넷 키는 `node.dc_orbit`. 묶음 키 = (성분 종류, 궤도). 대표 = **구조 색 `dc_colour` 최소**
   (1-WL 색 + 정준 위치, 정점마다 유일 -- 이름 치환에 불변), 나머지 = 묶인 성분(값은 같다).
2. **θ 전류 성분**(`current_symmetry`): 기저(sizing `graph.dc_current_basis`)의 모든 DC 원소 전류는 독립 θ 전류의 선형식이다. 대칭 점의 전류는 군 불변이므로 생성자 γ 마다 모든 DC 원소
   e 에 `I(γ e) = σ_γ(e) · I(e)`: σ = −1 은 방향 없는 2단자 수동소자(원소 종류 passive)의 **앞 끝**(단자 이름 순서 첫 단자의 넷, `current_basis._ends` 규약)이 γ 아래 앞 끝으로 가지 않을 때(자기동형이 단자
   순서를 뒤집음), 그 밖(MOS·이상원)은 +1. 이 식들은 독립 θ 전류에 대한 선형 연립이다. 구조 색이 큰 쪽이 먼저 소거되도록 유리수 기약 행사다리꼴을 만든다. 행 중 (i) **`x_p = ±x_q`**(q 소거되지
   않는 독립 전류) → 묶음(대표 q = 구조 색 작은 쪽, 구성원 p, 부호 −1 이면 `negated`), (ii) **`x_p = 0`** → 구조적 0(`zeros`: 대칭·KCL 이 이 가지 전류를 0 으로 정한다 -- 예 파일럿의 CMFB 감지 저항
   R1/R2 는 Voc 가 게이트만 구동해 직렬이라 I = 0), (iii) 그 밖(항 둘 이상·상수 남음)은 묶지 않는다(탐색 공간이 넓어질 뿐 정확하다). 구조적 0 은 θ 전류 성분을 **값 0.0 으로 고정**하고
   탐색 변수에서 뺀다(θ 전류 정의역은 전류 원뿔이라 0 이 허용된다; 저항 강하 0). 이름을 읽는 분기 없음.
3. `ties` = ((대표 성분, (묶인 성분, ...)), ...)(비전류 묶음 + 전류 묶음, 대표의 구조 색 순서). 구성원은 `negated` 에 들면 평가 θ 에서 −대표 값, 아니면 대표 값. 한 성분은 대표이거나 구성원이거나 구조적 0 이거나
   묶이지 않거나 넷 중 하나다(사슬 없음).
4. `search_domain(dc_ctx, settings, pdk_decl, spec_bounds=(), area_budget_m2=None, untie=())`: `variables`·`l_cells` 에서 묶인 구성원·구조적 0 을 뺀다(`SearchDomain.ties`·`negated`·`zeros` 에 기록).
   부호 −1 이 **아닌** 구성원의 bounds(log, lo, hi)가 대표와 다르면 `SchemaRejectedError`(gate `search_domain`, reason `tied_orbit_bounds_differ`, **detail `elements` = θ 성분 tuple
   `((종류, 키), ...)` -- 첫 원소는 대표, 이어서 상자가 다른 구성원들(묶음 안 구조 색 순서)**) -- 비대칭 상자를 선언한 원소는 `untie_orbits` 로 풀거나 상자를 같게 한다. 부호 −1 구성원은 상자 비교를 하지 않는다
   (값 = −대표, 상자는 대표 것). 자기동형이 선언 값(원소 값·레일 전위·노드 목표 등)을 보존하므로(sizing 3.0b) 값이 다르게 선언된 원소는 애초에 같은 궤도가 아니다.
5. `evaluate(sctx, theta, cells, ...)` 는 맨 앞에서 `expand_ties(sctx.domain.ties, theta, sctx.domain.negated, sctx.domain.zeros)` 로 채운다 -- 호출부는 대표 성분만 넘겨도 되고, 구성원 값이 있으면 대표가 이긴다.
   평가 키·`EvalResult.theta`·S3 기록은 확장된 전체 θ 다. 원뿔 행이 묶인 θ 전류를 읽으면 `layer0_center` 는 항을 대표 변수 열에 부호만큼 곱해 합치고, 구조적 0 전류는 상수 0 으로 읽는다
   (`_current_alias`·`_current_fixed`). `_repair` 의 후보 소자가 묶인 구성원이면 대표의 `ln_idu` 좌표를 움직인다.
6. L: `l_cells` 는 대표 MOS 만 갖는다(`cells` 벡터도 대표만). 구성원은 대표와 같은 칸이다(같은 kind 표, 자기동형). `polish_l_cells` 가 대표 칸을 옮기면 구성원도 함께 옮겨진다(평가 확장이 같은 L 을 준다).
7. spec 해제: `human.search.untie_orbits = {<원소>: {"source": {...user_spec}}}`(SPEC_CONTRACT). 원소가 속한 궤도를 묶지 않는다: 비전류 성분은 그 궤도의 묶음을 만들지 않고, θ 전류는 (연립을 그대로 풀되) 그 궤도의
   원소가 소거 변수이거나 대표인 관계·구조적 0 을 받지 않는다(다른 원소의 대칭이 KCL 로 만드는 관계도 그 궤도 변수에는 걸지 않는다). 원소가 없으면 `untie_element_unknown`, 궤도가 그 원소 하나뿐이면
   `untie_orbit_trivial`(둘 다 gate `search_domain`, detail `element`).
8. 실측(2026-10-08, 이 구현): 9 library 회로 중 묶음이 서는 회로는 `current_reuse_telescopic_ota` 하나 -- 성분 107 → 탐색 차원 73(변수 + L 칸 대표; 묶음 33, 구조적 0 전류 1 = 직렬 CMFB 감지 저항). 나머지 8회로(단일 종단,
   궤도 모두 단일)는 변화 없음.
9. 불변식(test 가 확인할 성질): (a) 대칭 쌍이 있는 회로에서 차원 + 묶인 구성원 수 + 구조적 0 수 = 스키마 성분 수; (b) `expand_ties` 는 입력을 바꾸지 않고, 구성원 값이 대표 값(`negated` 는 −대표, `zeros` 는 0.0)과 같다;
   (c) 묶음 있는 회로에서 평가한 θ 의 구성원 성분 값 = 대표 성분 값(비트); (d) `untie_orbits` 로 푼 궤도는 변수 수가 늘고 두 구성원이 따로 움직인다; (e) 비대칭 회로(궤도 모두 단일)에서는 `ties == ()` 이고 변수가 종래와 같다;
   (f) 위 4 의 거부; (g) 이름 치환 뒤 묶음이 치환표로 옮겨진다; (h) 저항 terminals 순서를 뒤집어 그린 사본은 같은 궤도·같은 묶음 그룹·같은 차원을 주고, 뒤집은 쪽 구성원의 θ 전류는 평가 θ 에서 −대표 값(저항 값은 같은 값)이다;
   (i) 파일럿에서 R1/R2 가 한 궤도.

### 3.25 [r12] `canonical_row_key(sctx) -> key 함수` (`canonical_rows.py`)
제약 행 이름 `<접두>:<소자>`(`w_min`·`seal6_bulk`·`inversion_floor`·`current_cone`)와 `<접두>:<번호>:<metric>`(`ss`·`spec`)의 정렬 키 = (접두, 소자 구조 색 `dc_colour`
(정점마다 유일, 없으면 -1), 나머지 이름). `solve_eps`(`_rows`)와 `layer0_start`(`_hard`·원뿔 행·원뿔 항 `_cone_canonical`)가 SLSQP 에 넘기는 제약 벡터·Jacobian 행 순서를 이 키로 정렬한다
(이름 순서에 따라 합산 순서가 바뀌어 끝자리가 달라지는 일을 막는다). 불변식: 이름 치환 σ 에 대해 정렬 결과가 σ 로 옮겨진다; 접두 순서는 사전식; 같은 궤도 행 사이만 이름.

## 4. ★ 봉인 7 대기 스위치 (`seal7_pending.seal_status`, sizing O1)

| 입력 DcEvaluation | 결과 |
|---|---|
| report.status sealed 이고 `sealed` 있음 | `STATUS_SEALED` |
| report.status undefined, 미정 항목이 정확히 봉인 7 하나, 그 detail reason == `REASON_VDSAT_MISSING` | `STATUS_PENDING_SEAL7` |
| report.status undefined, 그 밖 | `STATUS_UNDEFINED` |
| report.status violated | `ValueError`(size_and_seal 이 예외로 내므로 도달 불가) |
| DcEvaluation 아님 | `TypeError` |

- 대기 점은 탐색이 따라가지만(목적·제약이 정의됨) **최종 `front` 에 들어갈 수 없다** -- `pending_front` 로만 나온다(봉인 7 을 통과로
  치거나 2/(gm/ID) 로 대신하지 않는다). 봉인 7 행은 제약에 없다(VDSAT 없음).
- VDSAT 접근자가 생겨 `dc_seal_saturation` 이 pass/fail 을 내면 `REASON_VDSAT_MISSING` 이 사라져 이 표의 둘째 줄이 발동 0 이 되고
  `front` 가 채워진다(코드 변경 없음). 그때 `seal7_pending.py` 는 무동작이다.

## 5. 불변식 (test 가 확인할 성질)

| # | 성질 |
|---|---|
| I-1 | 중복 평가 0: 한 실행에서 `kernel_calls == unique_keys`, `recompute_same_key == 0`(같은 θ 의 fun·jac·cons·ε 재방문은 hits) |
| I-2 | 캐시 적중은 커널·S3 줄 0, 같은 객체 반환. evals 줄 수 = kernel_calls(archive 있을 때) |
| I-3 | 같은 code_fp·S0 면 디스크 실패 적중(커널 0), code_fp 가 다르면 무효 |
| I-4 | FD 열 parent = base: 전류 성분 열에서 sizing `dc_columns` computes 0(DC 저항 전류가 같을 때) |
| I-5 | 넓은 except 없음: 커널이 낸 ValueError·TypeError 는 evaluate 밖으로 전파 |
| I-6 | 봉인 7 대기 점은 `SearchFront.front` 에 0개(4절) |
| I-7 | `nondominated` 결과는 입력 순서 섞기에 불변, kept 안 두 점은 서로 지배하지 않고 모든 축 동률도 아니다 |
| I-8 | [r2] 결정론: 같은 입력·같은 `eval_budget`(선언 또는 기록된 유도값)이고 `stops_wall_budget == 0` 이면 `PYTHONHASHSEED` 무관 같은 front -- 평가 수 예산에 묶인 실행도 포함 |
| I-11 | [r2] θ 저항이 있고 `resistance_bounds_ohm` 이 None 이면 `build_search_context` 가 `SchemaRejectedError`(reason `theta_resistance_bounds_undeclared`) -- 커널 호출 0 |
| I-12 | [r2] 봉인 7 대기 점의 ss 제약은 모두 `unmeasured`(사유 `ss_requires_sealed_snapshot`), 행 0 -- 제약이 조용히 빠지지 않는다 |
| I-9 | `node_across_front` 커널 호출 0(counters 불변) |
| I-10 | 엔진 소스 숫자 리터럴·회로 이름 0(구조 test D·E) |
| I-13 | [r5] `layer0_start` 의 start 가 있으면 그 θ 의 평가는 받아들일 상태이고, 이어 `start_points(sctx, (), (start,))` 는 커널 0(캐시 적중)으로 그 점을 첫 시작점(source "layer0")으로 돌려준다 |
| I-14 | [r5] 원뿔의 모든 행이 항 하나(계수 1)이고 그 원천이 행 MOS 와 같은 kind 의 MOS 이면 전류 중심 = 상자 중심(u = 0) -- θ 전류 값이 상자 기하 중심과 같다(다른 kind 원천 행이 있으면 두 kind 상자 중심 차만큼 u > 0: 9회로 u = 4.28 ~ 4.83) |
| I-15 | [r5] 같은 sctx 입력으로 두 번(새 컨텍스트) 부르면 같은 start θ·t(결정론, `PYTHONHASHSEED` 무관) |
| I-18 | [r5b] 원뿔이 있고 전류 중심이 원뿔 안이면 Halton 시험 점은 모두 원뿔 안(`counters["outside_domain"]` 증가 0, 부동소수 경계 반올림 제외) -- 선형 원뿔·상자의 열린 현 안 걸음 |
| I-17 | [r5, r11] Halton 시험 점 k 의 좌표 = lo + φ_b(k)(hi − lo)(b = 3.21 3a 정준 차원의 소수 2, 3, 5, …, 같은 (종류, 구조 색) 키는 같은 b; θ 전류는 I-18 의 걸음): toy 커널이 처음 k* 번째 점만 받아들이면 `probes` = k*, `origin_point` = "halton:k*", 최대-최소 전까지 커널 평가 수 ≤ 1(중심) + k*(원뿔 밖 점은 0) |
| I-19 | [CM] `ss_constraint_rows`: view_kind cm_loop metric 의 `dc_not_above_level`(detail dc_magnitude = m, resolution = s) → 행 1개 `ss:<k>:<metric><op>`, c = 20·log10(m)/s(s 없음·0 이면 /1), active True, unmeasured 0. m = 0 → c = −∞. 예: m = 0.01075805, s = 3.2 → c = 20·log10(m)/s = −12.301665259916554 |
| I-20 | [CM] 같은 입력에서 view_kind loop 인 `pm_ss_deg` 의 `dc_not_above_level` 은 행 0·unmeasured 1(사유 code 그대로), cm_loop 의 `loop_open_rhp_poles` 는 위반 행(예 rhp_poles ((3.0, 4.0),) -> c = −0.6; ((2.0, 0.0),) -> c = −1.0; Re ≤ 0 인 항목만 있으면 행 없음) |
| I-21 | [CM] 위반 행의 c 는 |T_cm(0)| 에 단조 증가(같은 s), 값이 있는 PM(≥/<=) 행 의미(c = (값 − 목표)/s)는 변화 없음 |
| I-22 | [CM] 경고 표면: `EvalResult.warnings` == `ss_evaluate(...).ss.warnings`(봉인 아닌 점·실패 점은 ()); `find_front` 점 기록 `warnings` = [[코드, [[키, 값], ...]], ...]; run notes 에 `{verdict: "warning", code, points}` (코드별 점 수, 캐시 전 점 기준). 경고는 front 소속·제약 행·unmeasured 에 영향이 없다 |
| I-16 | [r5] 층 0 은 spec 성능 제약·목적 축 값을 읽지 않는다: spec judged 제약을 바꿔도(`judged_constraints`·`ss_constraints`) start θ 가 같다 |

## 6. S3 기록 형식 (`<root>/<context_fp>/`, 줄마다 flush)

- `evals.jsonl`: {seq, schema_fp, cells, w_fixed_fp, theta_hex, theta, status, ok, origin, fail?, objectives?{power_dc_w,
  area_search_m2}, power_resolution_w?, constraints[{name, c, active}], unmeasured[[metric, op, 사유]], snapshot_fp?, code_fp}.
- `runs.jsonl`: {run_id, s0, schema_fp, settings, starts, resolution, front[], pending_front[], removed[], failed_eps,
  notes, perf, code_fp}; 점 = {point_id, status, seq, theta_hex[[키, hex]], cells, power_dc_w, area_search_m2, gate_area_m2,
  passives_in_area(sctx.area_decl 이 있으면 True -- 수동 커패시터 면적이 area_search_m2 에 들어 있다, 결정 11), power_resolution_w, unmeasured, active, origin, snapshot_fp, snapshot_ref}.
- `snapshots/<snapshot_fp>.json.gz`: {fp, records[{kind, key, fields{이름: {value, writer, input_version}}}]}.
- Windows 경로 길이(260자) 때문에 `root` 는 짧아야 한다(지문 두 개가 64자).

## 7. 결정론
- 정렬: θ 키·MOS 이름·front 남기는 순서(3.1). 난수 없음. [r2] 탐색 안 한도(maxiter·재시작 상한·ε 수·평가 예산)는 모두 평가 수와
  LUT 해상도에서 나온다. 시간이 들어가는 곳은 두 곳뿐이고 둘 다 기록된다: E_B 를 유도할 때 한 번 잰 t_ref(`eval_budget` 으로
  다시 넘기면 재현), 바깥 벽시계 정지(`stops_wall_budget`). 그래서 I-8.

## 8. 설계와 다르게 정한 점

1. 파일: 설계의 `theta_schema.py`(sizing `dc_theta_schema` 가 이미 정본)·`kernel_context.py`(sizing `KernelContext` 정본 +
   `search_context.py`)·`eval_cache.py`(캐시 = SearchContext 필드)·`budget.py`(예산 게이트는 eps_sweep 안 식)·`layer0_columns.py`
   ([r5] 기둥 KVL 역산 대신 `layer0_center.py` -- feasibility centering, 9절 S-4)·`budget_point.py`(예산 선언 PA-1 대기 -- 쓰는 곳이 없어 만들지 않음)는 없다. `cone_rows.py`·`current_box.py`·
   `l_cells.py`·`objectives.py`·`seal7_pending.py`·`search_domain.py`·`ss_constraints.py` 를 더했다.
2. L 은 소자마다(sizing 스키마 -- `l_class` proposed), "동치류 bin" = 소자별 L 칸.
3. 신뢰 상자: 전역 bounds 에서 시작해 실패 때 절반(S-7). 실패 점에 부분 목적값이 없어(size_and_seal 이 예외로 끝남) 봉인 6·7
   실패도 재시작한다(S-10, 오케스트레이터 승인 2026-10-08). FD 열 양방향 실패는 재시작 대신 변수 고정(S-16).
6. [r2] b_P 는 상수가 아니라 점마다 유도(3.6). 풀이 하나·ε 격자·동률 폭은 그 점들의 b_P 를 쓴다(3.13·3.15).
7. [r2] sizing `__all__` 에 `dc_seal_vgs_match` 를 더했다(이 브랜치 한 줄, sizing 쪽 누락 수정 -- 블록 계수 12개).
4. 목적 값은 graph 필드가 아니라 metrics 순수 함수를 search 가 부른다(S-6). 전력 축 = power_dc_w(S-5).
5. 평가 캐시는 모든 결과의 스냅샷을 든다(설계 7.2 는 front·parent 사슬만) -- 메모리 정책은 cProfile 뒤.

## 9. 열린 항목 ([r2] 오케스트레이터 결정 2026-10-08 반영 상태)

- **S-1 (처리)** ss 제약은 점마다 `unmeasured` 로 기록(빠뜨리지 않음), 연결 자리 `ss_constraint_rows`(3.20) -- ng-sslin 의
  `ss_linearize` 가 들어오면 한 분기만 바꾼다. 그 전에는 제약이 없어 전력 최소·면적 최소가 같은 방향으로 모인다(S-12).
- **S-2 (처리)** b_P = Σ|V_rail|·tol_I(3.6). r2 는 gm_bound 를 써서 b_P 가 점 전력과 같은 크기 이상이었다 -> r3 에서 동작점 gm.
- **S-3 (처리)** θ 전류 상자 = `current_box`(3.19), θ 저항 상자 = 선언 필수·없으면 구조화 거부(3.7). **S-3b** finger 수 상한
  선언이 PDK 선언에 없어 I_max 는 단일 finger 최대 폭 슬라이스 값이다(다중 finger 소자의 상한은 열린 항목). 시연에서 θ 저항이 있는
  sf_pushpull·current_reuse 는 선언이 없어 거부된다(10절).
- **S-4 [r5 처리 -- 아래 두 r2·r4 문단은 기록]** 층 0 최소형(R D18·U-49: DC 정합 시작점 하나)의 입력 = **봉인 항목 margin(sizing
  봉인 보고) + θ 상자(`SearchDomain`) + 경성 행(W 하한·반전 하한·원뿔)** 이다(오케스트레이터 결정 2026-10-08, 3.21). r2·r4 의
  '세 입력 없음'은 DEC-71 전체판(블록 gain 예산으로 소자별 필요 gm 을 역산)의 입력이었고, 최소형은 gain 예산을 받지 않는다(DEC-73 의
  예산 배분·gain bin front 는 U-49 범위 밖). 그래서 다음은 **최소형 밖 정밀화**로 남는다: GB3 블록 분해·GB4 블록 gain 상한표,
  LR5 knee 앵커, GB5 층 0 근사식(DEC-92 (2)), 슬루 하한 전류.
  - **S-4a (기록, knee -- 지금 만들지 않음)** knee 를 만들 때의 결정: (Q1, 오케스트레이터 결정) PDK bin 경계를 건너는 앵커 구간은
    knee 후보에서 뺀다(LR3 근거 -- 경계 구간은 모델 불연속을 잰다; LUT v2 실측 nmos 352 경우 중 28, pmos 25 가 경계 구간 knee).
    열린 항목: (Q2) 동치류 gm/ID 가능역 안 여러 gm/ID 의 knee 집계 규칙(legacy 중앙값은 I-A15 '근거 없음'; LUT v2 에서 같은
    (VDS, VS) 의 gm/ID 만 바꿔도 knee 2~6 종), (Q3) knee 를 재는 (VDS, VSB)·폭 슬라이스(층 0 에서 VDS 는 배분 결과라 순환),
    (Q4, 사용자 몫) knee 가 L 격자 밀도에 의존함(LUT v2 nmos 70 % 가 0.18 µm = 첫 칸 위 끝, legacy 12-L 격자의 1.63×L_min 재현 안 됨)
    -- LR5 'kind 별 knee' 를 공정 성질로 유지할지, (Q7) GB5 근사식의 topology 무관 정의(DEC-92 (2), 회로별 함수 금지).
  - **S-4b (처리 -- 오케스트레이터 결정 2026-10-08)** 출발점(상자 중심 + 전류 중심)이 받아들일 상태가 아니면 Halton 시험(3.21 3)
    으로 첫 받아들일 점을 찾고 거기서 최대-최소. 연속 1단계(봉인 위반 margin 으로 끌어오기)는 두지 않는다 -- 위반 점에는 경성 행이
    없고 ④ 실패에는 margin 이 없다(클래스가 다른 margin 혼합 금지). [r5b] θ 전류는 원뿔 안 hit-and-run 으로 뽑는다(원뿔 밖 0).
    **남은 열린 항목**(10.0000 r5b): current_reuse·sf_pushpull 은 600 s 안에 받아들일 점 없음 -- sf 는 9 노드 다변수 SCC 의
    Gauss-Seidel 비수렴(sizing O10·O11, 구조적 -- sizing 브랜치 ng-scc-newton 몫), current_reuse 는 [r5c 진단] **diode writer 의
    ln_idu 표본이 강반전 분지 아래**(창 정의는 정상, 표본 정의역 문제 -- 10.0000 r5c). [r5c 처리, 오케스트레이터 승인] 층 0 시험의
    ln_idu 하한 = 칸 정점 하한(3.21 3, `_peak_floors`).
  - **S-4f ([r8] 채택 -- 오케스트레이터 결정 2026-10-08)** 1변수 노드 writer(diode 의 gate 쓰기·소스 추종의 source 쓰기)의 ln_idu
    상자 하한 = 시작 칸의 칸 정점 하한(`cell_floor`, 3.22), 칸 고정인 `solve_eps` 한 번 안에서 상수(L-b 의 새 칸 풀이는 새 칸 하한).
    근거 -- 그 소자는 정점 아래 좌표에서 노드 근이 늘 없어(분지 규칙) 그 아래 상자는 SLSQP 가 실패 재시작만 하는 영역이다. 일반
    writer 는 연속 제약 `inversion_floor` 가 같은 정보를 이미 준다. 받아들인 시작 좌표가 하한 아래면 하한 = 시작 좌표(시작점을 상자
    밖으로 내몰지 않음). 자리: `search_domain` 은 S0 당 1회라 칸을 모른다 -- 칸이 정해지는 `solve_eps._layout` 에서 적용.
  - **S-4c (기록 -- 의미 한정)** 상자 중심은 전류 상자(꺼짐 전류 ~ 단일 finger 최대 ID)의 기하 중심이라 pA 대 전류·약반전 점이고,
    Halton 점은 W 가 m~Gm 급일 수 있다. 근본 원인 = W·면적 상한 미선언(S-3b, 오케스트레이터가 사용자 선언 요청 중). 층 0 시작점은
    **DC 정합 가능성만** 뜻하며(`Layer0Result` docstring, find_front notes `meaning "feasibility_only"`) 탐색은 출발 근거 이상으로 쓰지
    않는다.
  - **S-4d (기록)** 최대-최소의 t 는 일관성 항목(봉인 1·2 margin)이 1 근처로 묶는다(t ≤ 1) -- 물리 여유(봉인 7)가 허용오차 한 칸
    이상이면 더 밀지 않는다(ftol 1 과 같은 분해능 규칙). [r5 처리] L FD 스텝을 제조 격자 한 칸으로 바꿔(3.11) L 이 칸 안에서 움직인다
    (초안: 칸 폭 스텝이라 칸 중점에서 양방향 칸 밖 -> 9회로 L 전부 고정).
  - **S-4e (열린 항목)** `solve_eps` 의 점 저장도 `np.asarray(x)`(복사 아님)라 SLSQP 가 제자리 갱신하면 저장 x 와 키가 어긋날 수 있다
    -- 층 0 에서 재현·수정한 결함과 같은 패턴(slsqp_outer 는 이 변경 범위 밖이라 그대로 둠).
- **S-4 (r2 기록 -- 막힘 -- 추측 없이는 구현 불가)** 설계의 층 0 최소형(설계 6.1 '① 층 0 조립점: ℓ = LR5 knee 앵커, r = 역산 후보, y = 창
  중앙', DEC-71 (4))은 세 입력이 필요한데 엔진에 없다: (a) LR5 knee(`measure_L_knee` 는 gm/ID·VDS 를 입력으로 받는다 -- 그 값이
  (b) 에서 온다) (b) (4)(a) 필요 gm(블록 gain 예산 -- GB4 상한표·GB5·`ss_linearize`) (c) (4)(c) VDS 배분의 VDsat 하한(lut VDSAT
  접근자 -- 봉인 7 과 같은 대기). y = 창 중앙만 유도 가능하다. 층 0 은 (b)·(c) 가 들어온 뒤 구현하고, 그동안 시작점은 S3 이전
  front 점 + `given_starts` 이며 notes 에 `layer0_inputs_missing` 을 남긴다. spec `n_starts`·x0 필드는 설계가 시작점을 유도하므로
  만들지 않았다.
- **S-5 (처리)** 전력 축 = power_dc_w. supply_current_dc 는 합산 레일 선언이 필요하다(notes 기록).
- **S-6** metrics 계산 블록 배선(S2 metric 필드) 없음 -> search 가 순수 함수 호출.
- **S-7 (U-47 보류 유지)** 신뢰 상자 초기 반경 m.
- **S-8 (처리)** 반복 상한·ε 수·평가 예산을 평가 수로(3.13·3.15) -- 벽시계는 바깥 정지(기록).
- **S-9 (처리)** sizing `__all__` 에 `dc_seal_vgs_match` 추가.
- **S-10 (승인)** 부분 목적값이 없어 재시작(기록).
- **S-11** FD y 스텝의 'VDS 격자 간격'(비균등 격자) -> 최소 간격으로 읽었다.
- **S-13** 원뿔 제약 정규화(설계 5절 표에 없음) -> Σ항/Σ|항|.
- **S-14** T_refilter(판정 축 재필터 시간) = 0 -- `find_front` 안에서는 0이다. 판정 축 재필터는 `convergence.converge(sctx, pdk_decl, front.front)`(U14, 패키지 순서상 search 위)가 하고 U16 이 부른다. `find_front` 의 `not_run` 노트와 `refilter: "mod8_not_implemented"` 는 `find_front` 산출물의 상태(재필터 전)를 가리킨다.
- **S-15** L-b 의 'LR5 격자 안' -- LR5 knee 격자 미구현이라 LUT 의 모든 L 칸이 격자다.
- **S-16 (처리)** FD 양방향 실패 열 = 변수 고정(3.13), 모두 고정되면 끝.
- **S-17** 예산 초과: 예산 검사는 새 x 평가 때만 해서 FD 한 번·L-b 시험 한 번만큼(평가 수로 n + 1 이하) 넘을 수 있다.
- **S-18 (r3 처리 -- 설계 개정)** W ≥ W_min 제약 행 c = (W − W_min)/g 를 더했다(3.8). W_min = PDK 선언 `min_finger_w_m`
  (difftap.2 = 0.42 µm, core CONTRACT 9.4 에 추가), g = `manufacturing_grid_m`. 설계 5절 제약 표에 없던 행이라 계획 기록은
  오케스트레이터 몫. b_A 도 같은 두 PDK 값의 곱(LutSpec 의 슬라이스 최소 폭 대신 -- 한 출처).
- **S-2b (r3 처리)** b_P 의 gm = 동작점 gm(3.6).
- **S-3b [결정 11, 2026-10-08 닫힘 -- 예산 선언 spec 한정]** 면적 예산이 선언된 spec 은 I_max = IDu_max · A / L_lo²(3.14 `area_budget_m2`),
  find_front notes `{"verdict": "closed", "rule": "S-3b", ...}`, 층 0 `meaning_reason` = `w_bounded_by_area_budget`. 예산이 없는 spec 은
  아래 잠정 동작 그대로.
- **S-3b (잠정 유지 -- 예산 미선언 spec)** I_max = 단일 finger 최대 슬라이스 ID -- 참 상한은 선언된 최대 nf 또는 면적 상한이 필요(열린 항목, notes
  `provisional`).
- **S-4 (r4 -- 병합 뒤에도 막힘)** ss_linearize·VDsat 이 들어왔지만 층 0 최소형의 세 조각이 모두 (4)(a) '소자별 필요 gm' 에 매달린다:
  필요 gm 은 블록 gain 예산(GB3 블록 분해·GB4 상한표·GB5 보상 규칙)에서 오는데 셋 다 엔진에 없다(`ss_evaluate` 는 전회로 metric 만
  낸다 -- 블록 국소 이득 모델이 아니다). knee(`measure_L_knee`, legacy 만 -- 미이식)는 gm/ID 를 입력으로 받고, VDS 배분의 VDsat
  하한은 있으나(lut `vdsat`) 소자 반전 수준이 (a) 에서 온다. y = 창 중앙만 유도된다. 그래서 층 0 은 구현하지 않고 notes
  `layer0_inputs_missing` 에 위 목록을 남긴다(GB3·GB4·GB5 가 들어오면 다시).

## 10. 9회로 실측 -- 작성자 측 시연(정본 아님)

### 10.r10 [r10] spec 원소별 θ 상자만으로 실측 (2026-10-08, LUT v2, master d672985 병합, B = 120 s, 시연 R/C 상자 없음)
- 수동소자 상자는 전부 spec `search.theta_bounds`(SearchSettings 재정의 None). 시연 시작점 탐침도 수동소자 값을 `sctx.domain`
  변수 상자에서 log-U 로 뽑는다(옛 하드코딩 R [100 Ω, 100 kΩ]·C [0.1, 10] pF 제거). 미선언으로 남은 것 = W/면적 상한(I_max 잠정).
- 상자가 있는 6회로 모두 `search_domain` 통과(r2 의 current_reuse R1·R2 / sf_pushpull R1a·R1b·R1c 거부 해소). 커널 호출 = 고유 키,
  `recompute_same_key` 0(9/9).

| 회로 | 수동 θ 상자 | 시작점 | front | 최종 front 점 (P, A, ss) |
|---|---|---|---|---|
| common_gate_amplifier | -- | 2 | 1 | P 2.39e-12 W, A 1.26e-12 m² |
| current_reuse_telescopic_ota | Cc1·Cc2 [0.1, 10] pF, R1·R2 [10 k, 10 M] Ω | 0 | 0 | 탐침 200 전부 DC 실패(no_root_in_window 233·lut_query_failed 3) |
| folded_cascode | -- | 2 | 1 | P 9.98e-7 W, A 2.0e-5 m² |
| ngcc_3stage_ff | Cm1·Cm2 [0.1, 10] pF | 2 | 0 | ε 풀이 6건 실패(봉인 점 377) |
| nmcnr_amplifier | Cm1·Cm2 [0.1, 10] pF | 2 | 0 | 봉인 2 / 실패 139(lut_query_failed 93) |
| pushpull_follower_buffer | -- | 1 | 2 | rout 998.3 Ω(P 2.79e-5 W) / 619.2 Ω(P 1.95e-4 W) ≤ 1000 |
| sf_pushpull_output_opamp | Cc [0.1, 10] pF, R1a·R1b·R1c [1 k, 1 M] Ω | 0 | 0 | 탐침 200 전부 실패(lut_query_failed 104·newton 82·no_root 13) |
| two_stage_ota | Cc [0.1, 10] pF | 2 | 1 | gain 80.02 dB ≥ 57, P 1.36e-7 W, A 1.54e-9 m² |
| two_stage_ota_sf | Cc [0.1, 10] pF | 2 | 1 | gain 80.54 dB, rout 859.4 Ω ≤ 1000, P 5.93e-5 W |

r9(시연 상자) 결과와 front 점이 같다 -- 커패시터 상자 값이 시연 값과 같고, 저항 상자가 생긴 두 회로는 상자보다 앞 단계(DC 봉인)에서
막힌다(0 시작점은 상자 문제가 아니라 DC 해: 창 안 근 없음·LUT 범위 밖 -- 9절 열린 항목). engine 값 저항 `Rm`(nmcnr)·`Rz`
(two_stage_ota)·`Rz1`·`Rz2`(current_reuse)는 θ schema 성분이 아니라(실측: 변수 목록에 없음) 상자가 필요 없다.

### 10.0000 [r5] 층 0 실측 (2026-10-08, LUT v2, `layer0_start` 단독 -- 새 컨텍스트, 평가 예산 미선언·B = 600 s)

θ 저항이 있는 두 회로(current_reuse R1·R2, sf_pushpull R1a~R1c)는 **시연 전용 상자 (1e2, 1e5) Ω**(GB7 §10 탐침 범위, 엔진 밖 하네스
값 -- 사용자 선언 대기 S-3)로 돌렸다. wall 은 첫 평가의 LUT 파생표(tol_V) 1회 비용(~15 s)을 포함한다.

최종 코드(Halton 시험 S-4b + L FD 스텝 = 제조 격자 + 고정 이상원 행 제외). E_B 는 미선언이라 `evaluate` 가 한 번 유도했다(1.1),
벽시계 B = 600 s(deadline). current_reuse 는 최종 시험 한도 규칙(deadline 이 있으면 시험 수 상한 없음)으로 따로 다시 쟀다.

| 회로 | 변수 | 출발 | stop | 층 0 시작점 | Halton 시험(k) | t | 경성 행 | kernel = 고유 키 | 원뿔 밖(커널 0) | 재시작 | L 움직임 | wall(s) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 6 | 중심 sealed | converged | **있음** | 0 | 1.00 | ≥ 0 | 11 = 11 | 0 | 0 | 2/3 | 33.6 |
| current_reuse_telescopic_ota | 54 | 중심 실패(M4a tol_V 셀 VDS −3.8 mV) | `start_lut_query_failed+probe_wall_budget` | 없음 | 164,289 | -- | -- | 4,296 = 4,296 | 159,994 | -- | -- | 601.1 |
| folded_cascode | 16 | 중심 sealed | converged | **있음** | 0 | 0.88 | ≥ 0 | 31 = 31 | 0 | 0 | 9/13 | 42.0 |
| ngcc_3stage_ff | 19 | 중심 sealed | converged | **있음** | 0 | 0.95 | ≥ 0 | 38 = 38 | 0 | 1 | 11/16 | 38.2 |
| nmcnr_amplifier | 21 | 중심 실패(M301 VDS 7.9e-14 V) | converged | **있음**(halton:7122) | 7,122 | 0.96 | ≥ 0 | 3,289 = 3,289 | 4,724 | 2 | 15/15 | 286.7 |
| pushpull_follower_buffer | 8 | 중심 sealed | converged | **있음** | 0 | 0.93 | ≥ 0 | 32 = 32 | 0 | 1 | 5/6 | 37.2 |
| sf_pushpull_output_opamp | 25 | 중심 실패(M11 VDS 0.55 mV) | `start_lut_query_failed+probe_wall_budget` | 없음 | 1,248 | -- | -- | 1,249 = 1,249 | 0 | -- | -- | 600.4 |
| two_stage_ota | 9 | 중심 sealed | converged | **있음** | 0 | 0.93 | ≥ 0 | 18 = 18 | 0 | 0 | 6/7 | 39.1 |
| two_stage_ota_sf | 11 | 중심 sealed | converged | **있음** | 0 | 0.89 | ≥ 0 | 22 = 22 | 0 | 0 | 5/9 | 28.9 |

- **7/9 회로가 봉인 통과 층 0 시작점**(전부 `sealed`, 경성 행 ≥ 0, `recompute_same_key` 0). Halton 시험이 nmcnr 을 살렸다(7,122 번째
  점, 커널 3,289). current_reuse·sf_pushpull 은 600 s 안에 받아들일 점이 없다: current_reuse 는 시험의 97 % 가 원뿔 밖(θ 전류 22개를
  상자에서 독립으로 뽑으면 차 전류 행이 거의 늘 음), 커널 평가 4,296 은 모두 실패; sf 는 원뿔 밖 0 인데 커널 1,249 모두 실패.
  둘 다 θ 저항 상자가 시연 전용 값이다.
- **[r5b] 원뿔 안 hit-and-run 재측정**(같은 조건, 세 회로):

  | 회로 | stop | Halton 시험 | kernel = 고유 키 | 원뿔 밖 | 실패 분류(커널 평가 중) | 실패 소자 상위 | wall(s) |
  |---|---|---|---|---|---|---|---|
  | current_reuse | `..+probe_wall_budget`, 시작점 없음 | 6,338 | 6,339 | **0**(r5: 97 %) | `no_root_in_window`(봉인 7 단계) 6,338, `lut_axis_out_of_range`(중심, tol_V VDS) 1 | M66 2,670, M14b 1,532, M24b 903, M36a 376, M36b 325, M39 264 | 600.1 |
  | sf_pushpull | `..+probe_wall_budget`, 시작점 없음 | 1,166 | 1,167 | 0 | NONCONVERGENT 924(79 %), `lut_curve_undefined` 142(VDS = 0 -- 대부분 M20), `lut_target_out_of_range` 60, `no_root_in_window` 41 | NONCONVERGENT 는 매번 같은 SCC 16소자(M1·M5·M6·M9·M10·M12~M22) | 600.6 |
  | nmcnr | converged, 시작점 있음(halton:1872, t 0.94) | 1,872 | 1,909 | 0 | `no_root_in_window` 992, `lut_target_out_of_range` 563, VDS 축 밖 191, NONCONVERGENT 75, `lut_curve_undefined` 48 | M203 798, M201 326, M105 302, M103 256, M301 232 | 146.3 |

  - sf 진단(150 s 별도 실행): NONCONVERGENT 210건 모두 **같은 9 노드 SCC**(N13·N5·N12·N1·N1516·N910·Y·N20·N17), K_max 12, 마지막 두
    Δ 비 중앙값 1.00(p10 0.76) -- Gauss-Seidel 이 수축하지 않는다(Δ 0.4~0.9 V 대 tol 0.73 mV). 표본과 무관하게 같은 SCC 에서 일어나므로
    **구조적(다변수 SCC 풀이법, sizing O10·O11 '다변수 블록을 Newton·연속법으로 바꿀지는 설계 결정')** 이고 엔진 결함이라 단정할 수
    없어 코드는 바꾸지 않았다. θ 저항 상자(시연 값)는 SCC 를 만들지 않는다(SCC 는 구조).
  - current_reuse: 원뿔 밖 문제는 해결됐지만 커널 평가가 모두 1변수 노드 창 근 없음. writer 가 여러 소자(M66·M14b·M24b 등)로 흩어져
    한 소자 고정 구조(늘 VDS≈0)는 아니다.
  - **[r5c] current_reuse 진단**(150 s 별도 실행, `no_root_in_window` 2,365건, 스크립트 scratchpad `l0_cr_diag.py`):

    | writer | 관계 | 창 [lo, hi] 끝 출처 | 창 폭 | h 끝 부호(건수) | 실패 표본 ln_idu 상자 위치 | 그 ln_idu 만 훑었을 때 노드 근이 생기는 위치 |
    |---|---|---|---|---|---|---|
    | M66(nmos diode, s = gnd) | vgs_gate | VDS 축 하한 / 레일 | 1.7625 V | (+inf, +inf) 975, (+, +inf) 38, (+, +) 35 | 0.00 ~ 0.42 | ≥ 0.425 |
    | M14b(nmos diode, gnd) | vgs_gate | VDS 축 / 레일 | 1.7625 V | (+inf, +inf) 535 / 572 | 0.00 ~ 0.42 | ≥ 0.425 |
    | M24b(nmos diode, gnd) | vgs_gate | VDS 축 / 레일 | 1.7625 V | (+inf, +inf) 313 / 333 | 0.00 ~ 0.42 | ≥ 0.425 |
    | M36a(pmos diode, vdd) | vgs_gate | VDS 축 / VDS 축 | 1.7625 V | (−inf, −inf) 128 / 147 | 0.00 ~ 0.99(중앙 0.19) | ≥ 0.325 |
    | M39(pmos diode, vdd) | vgs_gate | VDS 축 / VDS 축 | 1.7625 V | (−inf, −inf) 112 / 115 | 중앙 0.15 | ≥ 0.325 |
    | M36b·M18_bg·M20a·M11a(pmos diode) | vgs_gate | VDS 축 / VDS 축 | 1.7625 V | 대부분 (−inf, −inf) | 중앙 0.11 ~ 0.26 | ≥ 0.325(M36b) |

    - 실패 writer 는 **모두 diode**(gate = drain, source = 레일)이고 창은 VDS 정의역 전체(1.7625 V = VDS 하한 ~ 레일)다 -- 창이 좁아서가
      아니다. h 끝이 ±inf 인 것은 그 VDS 전 구간에서 목표 IDu 가 그 곡선의 **강반전 분지 시작(gm/ID 정점) 아래**라는 뜻이다(분지 규칙상
      정점 왼쪽 근은 해가 아니다). 다른 θ 를 고정하고 그 소자 ln_idu 만 상자 위에서 훑으면 nmos 는 상자 위치 0.425, pmos 는 0.325 부터
      그 노드 근이 생기고, 그때는 다음 diode 가 같은 이유로 실패한다(M66 -> M14b -> M11a·M18_bg 사슬).
    - 판정: **창 정의(구조)가 아니라 표본 정의역 문제**다. ln_idu 상자 하한은 전 (L, VDS, VS) 곡선 정점 중 최솟값(search_domain 3.7)이라
      실제 동작점의 정점보다 훨씬 낮고, writer 일반은 이를 `inversion_floor` 연속 제약으로 다루지만 diode writer 는 1변수 노드라 정점 아래
      표본이 곧 근 없음이다. diode 가 16개라 독립 표본이 모두 정점 위일 확률이 작다(대략 0.6^16). 전류(걸음)는 diode 노드 근에 영향이 없다
      (VGS 는 ln IDu·L·VDS·VSB 로만 정해짐, DEC-88). 엔진 결함으로 단정할 근거가 없어 코드는 바꾸지 않았다 -- 제안은 9절 S-4b.
  - 선형 전류 좌표 걸음은 부피상 큰 전류 쪽에 몰린다(nmcnr 시작점 전류 20 µA ~ 2 mA, W 최대 2.6e9 m -- S-3b 상한 미선언).
- **[r5c] 칸 정점 하한 적용 후 9회로 재측정**(같은 조건, E_B 유도·B = 600 s):

  | 회로 | 결과 | 출발 | Halton 시험 | kernel = 고유 키 | t | 실패(커널 평가 중) | wall(s) |
  |---|---|---|---|---|---|---|---|
  | common_gate·folded·ngcc·pushpull·two_stage_ota·two_stage_ota_sf | **있음**(변화 없음) | 중심 | 0 | 11·31·38·32·18·22 | 1.00·0.88·0.95·0.93·0.93·0.89(r5b 와 같음) | -- | 26 ~ 32 |
  | nmcnr | **있음** | halton:**156**(r5b 1,872) | 156 | 193 | 0.93 | curve_undefined 101(M301), no_root 51, target 밖 4 | **44.3**(r5b 146) |
  | current_reuse | 없음(`..+probe_eval_budget`) | -- | 511 | 512(= 유도 E_B) | -- | no_root_in_window 481, tol_V VDS 축 밖 31 | 284.2 |
  | sf_pushpull | 없음(`..+probe_wall_budget`) | -- | 1,171 | 1,172 | -- | NONCONVERGENT 966 등(r5b 와 같은 SCC) | 600.4 |

  - **7/9 유지, 회귀 0**(중심 출발 6회로는 시험을 쓰지 않아 경로 동일). nmcnr 시작점: 전류 0.54 ~ 12 µA, W 최대 1,653 m(S-3b).
  - current_reuse: 유도 E_B 가 512(하한 덕에 커널이 더 깊이 풀려 평가 중앙값 ≈ 1.2 s)라 284 s 에 평가 예산으로 멈췄다. 실패 분류가
    바뀌었다(300 s 진단, 267건, `l0_cr_diag.py`): 레일 diode(M66·M14b·M24b·M36a·M39 …)의 '분지 아래(±inf)' 실패는 사라지고(남은 몇 건은
    유한 동부호 = 창 위), 상위가 **적층 diode**(M11b 위 M11a, M14a 위 M14b, M23a, M20b -- source 가 다른 diode 노드, 창 폭 0.01 ~ 1.6 V,
    h 동부호: 필요한 gate 전압이 창 밖)와 source 추종(M4a: 창이 빔 -- VS 축·VDS 정의역 교집합 공집합, M37b·M18b·M9b: h 동부호)이다.
    실패 표본의 ln_idu 는 상자 위치 0.73 ~ 0.99(강반전 쪽) -- 하한이 '분지 아래'를 막자 이번에는 **적층 VGS 합이 레일 차를 넘는 고반전
    조합**이 남았다. 창 정의 결함이 아니라 표본(높은 ln_idu 끼리의 적층) 쪽이며 구조적 하한은 아니다(같은 소자도 낮은 위치에선 통과).
    엔진 결함 근거가 없어 코드는 바꾸지 않았다(열린 항목: 적층 diode 의 ln_idu 상한을 '레일 차 − 아래 diode VGS' 로 묶는 규칙은 아직 정의
    없음).
- **[r8] master(MOD6 r7) 병합 + S-4f + 1단계 수리 재측정**(B = 600 s, E_B 유도; r7 의 DEC-92 수동소자 θ 성분 때문에 변수 수가 늘었다
  -- current_reuse 54 -> 56, ngcc 19 -> 21, nmcnr 21 -> 23, sf 25 -> 26, two_stage 9 -> 10, two_stage_sf 11 -> 12; θ 커패시터 상자는 시연
  전용 (1e-13, 1e-10) F, θ 저항 상자는 시연 전용 (1e2, 1e5) Ω -- 둘 다 하네스 값):

  | 회로 | 결과 | 출발 | 시험 | kernel = 고유 키 | t | 수리(묶음 수 / 고친 좌표) | wall(s) |
  |---|---|---|---|---|---|---|---|
  | common_gate | 있음 | 중심 | 0 | 11 | 1.00 | -- | 24.2 |
  | folded | 있음 | 중심 | 0 | 31 | 0.88 | -- | 31.1 |
  | ngcc | 있음 | 중심 | 0 | 40 | 0.95 | -- | 30.5 |
  | pushpull | 있음 | 중심 | 0 | 32 | 0.93 | -- | 25.9 |
  | two_stage_ota | 있음 | 중심 | 0 | 19 | 0.93 | -- | 23.9 |
  | two_stage_ota_sf | 있음 | 중심 | 0 | 23 | 0.89 | -- | 25.6 |
  | nmcnr | 있음 | halton:299 | 299 | 377 | 0.89 | 7 / M103 ×3(수리로 받아들일 점에 닿지 못하고 시험 점이 먼저) | 27.6 ~ 63.3 |
  | current_reuse | 없음(`..+probe_eval_budget`, E_B 954) | -- | 919 | 954 | -- | 8 / M18a·M39 각 1(6회는 후보 양끝 모두 같은 실패) | 300.6 |
  | sf_pushpull | 없음(`..+probe_eval_budget`, E_B 1,643) | -- | 1,526 | 1,643 | -- | 17 / M10 ×2·M15 ×6 | 524.0 |

  - **7/9 유지, 회귀 0**(중심 출발 6회로 t 는 r5c 와 소수 3자리까지 같다 -- ngcc·two_stage 는 수동소자 θ 성분이 더해져 끝자리만 다름).
    nmcnr 시험 수가 r5c 156 -> 299 로 는 것은 θ 차원이 바뀌어 Halton 열이 달라진 탓이다(같은 규칙). 
  - current_reuse: 1단계 수리는 실패 writer 좌표와 그 '아는 쪽' 노드 writer 좌표를 상자 양끝까지 움직여도 대부분 같은 노드 실패가
    남는다 -- 적층 diode(M23a·M20b·M11b·M14a)·소스 추종(M37b·M4a)의 근이 창 밖인 원인이 한두 좌표가 아니라 사슬 전체(여러 diode 의
    VGS 합)에 걸려 있다. 남은 열린 항목: 다좌표 수리(사슬 전체의 위반을 한 번에 줄이는 규칙) 정의 없음.
  - sf_pushpull: 실패의 78 %가 같은 SCC NONCONVERGENT(ng-scc-newton 몫), 수리는 1변수 노드(M10·M15)만 움직였다.
- L FD 스텝 = 제조 격자로 바꾼 뒤 L 열 고정 0(r5 초안: 모든 L 고정), L 이 칸 안에서 움직였다(위 'L 움직임' = 칸 중점에서 벗어난 소자
  수 / L 변수 수).
- 시작점의 모양(S-4c·S-4d, **의미 = DC 정합 가능성뿐**): 상자 중심 출발 회로는 전류 0.4 pA ~ 4.3 nA, gm/ID 26 ~ 33.5(약반전),
  W 0.70 µm ~ 254 m(pushpull); Halton 출발 nmcnr 은 전류 1e-16 ~ 4.4e-4 A, W 최대 3.4e9 m. 원인은 W·면적 상한 미선언(S-3b,
  사용자 선언 요청 중). t 는 봉인 1·2 margin 이 묶는다(0.88 ~ 1.00).
- [r5 초안 기록] 중심만 쓰던 초안: 6/9(중심 sealed 6), 실패 3 은 출발점 ④ 실패. 고정 이상원 행을 편차 경쟁에 넣은 초안은 current_reuse
  u = 19.1(원뿔 밖, M16 c = −1.2e-4) -> 고정 행 제외 뒤 u = 4.40. 최대-최소 점 저장에서 SLSQP 가 넘긴 배열을 복사하지 않아 제자리 갱신으로
  키가 어긋나던 결함(nmcnr Halton 출발에서 재현)을 복사로 고쳤다 -- 같은 패턴(`np.asarray(x)` 저장)이 `solve_eps` 에도 있다(열린 항목).
- find_front 배선(two_stage_ota, E_B = 150 선언, given 없음, 초안 코드): 시작점 1(층 0), kernel 151 = 고유 151, 미측정 front 1점(Cc·Rz
  값 미선언, S-20), notes 에 `layer0_minimal`.

### 10.000 [r4] r4 실측 (2026-10-08, LUT v2 `resolve_lut_location`, ng-seal7 병합 -- 봉인 7 실판정, B = 120 s 만 선언)

| 회로 | 변수 | 시작점 | requests | kernel = 고유 키 | 블록 reuse | E_B | 풀이 | 실패 ε | wall(s) | 최종 front | 미측정 front | 대기 | spec ss 제약 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 6 | 2 | 36204 | 5019 | 0.16 | 8605 | 799 | 70 | 89.6 | **3** | 0 | 0 | 없음 |
| current_reuse_telescopic_ota | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부(θ 저항 상자 미선언) | | | |
| folded_cascode | 16 | 2 | 1879 | 289 | 0.18 | 1023 | 16 | 12 | 81.8 | **2** | 0 | 0 | 없음 |
| ngcc_3stage_ff | 19 | 2 | 4368 | 249 | 0.19 | 2969 | 50 | 46 | 13.9 | 0 | 1 | 0 | gbw ≥ 10 MHz, pm ≥ 63.4° -- 미측정(Cm1·Cm2 값 없음) |
| nmcnr_amplifier | 21 | 2 | 3990 | 259 | 0.18 | 3806 | 44 | 40 | 14.1 | 0 | 1 | 0 | gbw ≥ 816 kHz, pm ≥ 70° -- 미측정(보상 수동소자 값 없음) |
| pushpull_follower_buffer | 8 | 1 | 1282 | 570 | 0.15 | 5132 | 18 | 0 | 9.8 | **1** | 0 | 0 | rout ≤ 1000 Ω -- **856.2 Ω 만족**(c = 0.144) |
| sf_pushpull_output_opamp | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부(θ 저항 상자 미선언) | | | |
| two_stage_ota | 9 | 2 | 30967 | 316 | 0.18 | 5055 | 300 | 0 | 59.2 | 0 | 2 | 0 | gain ≥ 57 dB -- 미측정(Cc·Rz 값 없음) |
| two_stage_ota_sf | 11 | 2 | 22537 | 189 | 0.15 | 6012 | 159 | 112 | 10.5 | 0 | 2 | 0 | gain ≥ 57 dB, rout ≤ 1000 Ω -- 미측정(Cc 값 없음) |

- 7회로 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0, 벽시계 정지 0. 봉인 7 대기 점 0(스위치 발동 0 --
  VDSAT 열이 있어 `seal7_pending` 무동작).
- 최종 front 6점(3회로). 실제 성능 제약이 있는 최종 점은 pushpull 1점뿐이다 -- 나머지 두 회로는 판정 제약이 없어 front 가 전류 하한
  쪽으로 간다(common_gate 한 점 P = 4.6e-14 W). 4회로는 engine 값 보상 수동소자의 θ 성분이 아직 sizing 스키마에 없어(DEC-92, S-20)
  ss 제약이 전부 `passive_value_undeclared` -- 최종 front 0.
- 결정론: common_gate E_B = 800 선언·B = 900 s, seed 1·2 -- kernel 575·575, 최종 front 동일.
- cProfile(cumtime): folded 81.8 s 중 size_and_seal 73.8 s, core `fp_of` 38.4 s, LUT `gm_id_for_target` 37.4 s; two_stage 59.2 s 중
  size_and_seal 40.2 s, `fp_of` 27.5 s -- evaluate 의 metrics_dc·ss·캐시 적중 처리(30957 요청) 약 9 s.

### 10.00 [r3] r3 실측 (2026-10-08, 이 커밋 코드 -- B = 120 s 만 선언, b_P 동작점 gm, W ≥ W_min)

| 회로 | 변수 | requests | kernel = 고유 키 | 블록 reuse | E_B(유도) | 풀이 | 고정 열 | 실패 ε | wall(s) | 대기 front 점: P(W), A(m²), b_P/P, w_min 활성 |
|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 6 | 7924 | 188 | 0.17 | 6891 | 203 | 602 | 0 | 6.0 | 4.6e-14, 1.4e-12, 0.18, 0 |
| current_reuse_telescopic_ota | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부(θ 저항 상자 미선언) |
| folded_cascode | 16 | 940 | 209 | 0.16 | 309 | 6 | 18 | 3 | 93.3 | 9.2e-6, 3.7e-9, 0.055, 1 / 1.7e-5, 1.6e-10, 0.061, 0 |
| ngcc_3stage_ff | 19 | 3941 | 240 | 0.20 | 2370 | 42 | 22 | 38 | 19.0 | 2.5e-5, 1.0e-8, 0.022, 0 |
| nmcnr_amplifier | 21 | 13963 | 356 | 0.20 | 2810 | 47 | 402 | 0 | 26.0 | 1.35e-5, 4.4e-9, 0.16, 1 |
| pushpull_follower_buffer | 8 | 26278 | 3718 | 0.17 | 4014 | 252 | 1753 | 126 | 101.4 | 5.5e-14, 1.1e-7, 0.089, 2 / 1.3e-10, 3.5e-10, 0.094, 0 |
| sf_pushpull_output_opamp | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부(θ 저항 상자 미선언) |
| two_stage_ota | 9 | 4313 | 2569 | 0.15 | 4397 | 117 | 107 | 107 | 120.1(벽시계 정지 1) | 7.8e-13, 6.4e-10, 0.041, 0 / 3.9e-11, 2.7e-10, 0.036, 0 |
| two_stage_ota_sf | 11 | 1861 | 104 | 0.16 | 4593 | 40 | 8 | 37 | 5.9 | 6.5e-6, 2.5e-8, 0.31, 0 |

- 7회로 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0. 대기 점 소자 W 최솟값 ≥ 0.42 µm(W_min) 전부.
- **b_P/P = 0.02~0.31**(r2 의 1~2000 배에서 내려옴). 결정론: two_stage_ota E_B = 600 선언·B = 900 s, seed 1·2 -- kernel 505·505, 대기
  front 동일.
- 남은 비물리: W ≥ W_min 을 지켜도 전류가 꺼짐 전류 근처(pW)까지 내려간다(common_gate·pushpull·two_stage 대기 점 P ~ 1e-14~1e-10 W) --
  성능 제약(S-1)이 없어서다. 실패 ε 는 SLSQP status 4·8.

### 10.0 [r2] r2 실측 (2026-10-08, r2 코드)

조건: 아래 r1 과 같은 LUT·spec·시작점 탐침(시작점 생성은 시연 하네스 몫 -- 층 0 막힘). **선언 가정은 B = 120 s 하나**이고
b_P·θ 전류 상자·E_B 는 유도, θ 저항 상자는 미선언(그래서 θ 저항이 있는 두 회로는 거부). 최종 front 0/9(봉인 7 대기).

| 회로 | θ / 변수 | 시작점 | requests | kernel = 고유 키 | recompute_same_key | 블록 reuse 비 | E_B(유도) | 풀이 수 | 고정 열 | 실패 ε | wall(s) | 대기 front (P W, A m²) | b_P(격자) / P |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 9 / 6 | 2 | 382 | 37 | 0 | 0.16 | 11000 | 19 | 0 | 15(slsqp_4) | 0.6 | 1.37e-12, 6.4e-18 | 8.4e-7 / 1.4e-12 |
| current_reuse_telescopic_ota | 105 | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부: `theta_resistance_bounds_undeclared` (R1, R2) | -- |
| folded_cascode | 29 / 16 | 2 | 1037 | 140 | 0 | 0.17 | 406 | 12 | 11 | 8(slsqp_4) | 53.9 | 1.52e-5, 1.35e-10 | 7.0e-6 / 1.5e-5 |
| ngcc_3stage_ff | 35 / 19 | 2 | 23962 | 1560 | 0 | 0.25 | 1555 | 76 | 1070 | 0 | 112.4 | 3.79e-4, 2.68e-8 | 4.7e-2 / 3.8e-4 |
| nmcnr_amplifier | 36 / 21 | 2 | 8890 | 1524 | 0 | 0.20 | 1891 | 48 | 255 | 0 | 102.3 | 2.71e-4, 1.34e-10 | 1.8e-4 / 2.7e-4 |
| pushpull_follower_buffer | 14 / 8 | 2 | 824 | 434 | 0 | 0.16 | 1757 | 25 | 1 | 0 | 15.3 | 3.27e-5, 3.41e-12 | 1.2e-4 / 3.3e-5 |
| sf_pushpull_output_opamp | 47 | -- | -- | -- | -- | -- | -- | -- | -- | -- | -- | 거부: `theta_resistance_bounds_undeclared` (R1a, R1b, R1c) | -- |
| two_stage_ota | 16 / 9 | 2 | 271 | 70 | 0 | 0.16 | 1199 | 7 | 0 | 3(slsqp_4) | 11.8 | 4.01e-6, 6.67e-11 | 4.8e-6 / 4.0e-6 |
| two_stage_ota_sf | 20 / 11 | 2 | 16645 | 1663 | 0 | 0.18 | 4514 | 379 | 81 | 0 | 63.3 | 6.21e-6, 8.97e-13 | 1.3e-2 / 6.2e-6 |

- 7회로 모두 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0, `stops_wall_budget == 0`.
- 결정론(I-8, 평가 수 예산에 묶인 실행): nmcnr_amplifier 를 E_B = 300 선언, `PYTHONHASHSEED` 1·2 로 따로 -- kernel 323·323,
  대기 front 동일.
- **b_P(S-2b)**: 유도된 b_P 가 점의 전력과 같은 크기이거나 수십~수천 배 크다(ngcc 120 배, two_stage_ota_sf 2000 배) --
  tol_I = tol_V·gm_bound 의 gm_bound(곡선 전체 gm 최대 × W/w_m)가 W 큰 소자에서 크다. 전력 축 해상도가 사실상 한 칸이라 ε 전력
  방향 격자가 비거나 배수가 커진다(ngcc ε 배수 2097152).
- **W 하한 없음(S-18)**: θ 전류 하한이 LUT 꺼짐 전류(~pA)라 전력·면적 최소화가 전류를 꺼짐 수준까지 내린다(common_gate 대기 점
  P = 1.4 pW, A = 6.4e-18 m² -- W 가 최소 finger 폭보다 훨씬 작은 비물리 점). 설계 5절 제약 표에 W ≥ 최소 finger 폭(PDK)
  행이 없어 넣지 않았다(결정 필요).
- 고정 열(S-16): ngcc 1070, nmcnr 255 -- 대부분 L 열(칸 끝에서 양방향 실패). 실패 ε 는 모두 SLSQP status 4(부등식 양립 불가).
- ss 제약은 대기 점마다 `unmeasured`(사유 `ss_requires_sealed_snapshot`)로 S3 evals 에 기록, notes 에 제약 목록.
- cProfile(cumtime): folded_cascode 53.9 s 중 size_and_seal 52.8 s(98%), LUT `gm_id_for_target` 32.0 s, core `fp_of` 20.6 s;
  two_stage_ota 11.8 s 중 size_and_seal 11.3 s, `fp_of` 7.1 s(60%). search 자체는 1~4%.

### 10.1 r1 실측 (2026-10-07, 결정 전 -- 기록)

조건: LUT = `_drafts/engine/lut_slices/manifest.json` + `assets/sky130_nfet_pfet_lut_sample.npz`(옛 LUT, VDSAT 열 없음),
`pre_layout_lut_access`, spec = library(metric 이름표 = `metric_catalog()` + integration 픽스처의 mismatch_sigma_mv·
mirror_ratio_error_mv·area_layout_m2). **시연 가정(결정 대기 값, 엔진 밖)**: B = 120 s, b_P = 1e-7 W, θ 전류 [1, 100] µA,
θ 저항 [100 Ω, 100 kΩ](GB7 §10 탐침 범위), 시작점 = GB7 §10 탐침식(L = 1 µm, writer gm/ID U[6, 26] -> ln IDu, y U[0.05, 0.95],
전류 log-U, seed 1) 중 받아들인 2개(최대 200 탐침). 결과는 모두 봉인 7 대기 -> **최종 front 0점(9/9)**.

| 회로 | θ / 연속 변수 | 탐침 -> 시작점 | requests | kernel = 고유 키 | hits | recompute_same_key | 블록 reuse 비 | 평가 중앙값 | wall(s) | 풀이 수 | ε 배수 | 실패 ε | 대기 front |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 9 / 6 | 2 -> 2 | 5097 | 64 | 5033 | 0 | 0.17 | 19 ms | 2.0 | 292 | 1024 | 287(FD 열 L 양방향 실패) | 1 |
| current_reuse_telescopic_ota | 105 / 54 | 200 -> 0 | 192 | 192 | 0 | 0 | -- | 163 ms | -- | 0 | -- | -- | 0(시작점 없음: no_root_in_window 191) |
| folded_cascode | 29 / 16 | 6 -> 2 | 714 | 120 | 593 | 0 | 0.19 | 282 ms | 48.6 | 11 | 64 | 7(slsqp_4) | 1 |
| ngcc_3stage_ff | 35 / 19 | 5 -> 2 | 7341 | 360 | 6922 | 0 | 0.22 | 46 ms | 20.9 | 84 | 262144 | 0 | 1 |
| nmcnr_amplifier | 36 / 21 | 8 -> 2 | 3623 | 184 | 3434 | 0 | 0.20 | 62 ms | 14.1 | 48 | 32 | 44(slsqp_4) | 1 |
| pushpull_follower_buffer | 14 / 8 | 30 -> 2 | 3927 | 133 | 3794 | 0 | 0.17 | 31 ms | 4.3 | 180 | 16384 | 175(FD 열 L) | 1 |
| sf_pushpull_output_opamp | 47 / 25 | 200 -> 1 | 1143 | 334 | 809 | 0 | 0.18 | 134 ms | 37.0 | 9 | 128 | 7(slsqp_4) | 1 |
| two_stage_ota | 16 / 9 | 7 -> 2 | 1344 | 87 | 1257 | 0 | 0.17 | 145 ms | 14.4 | 39 | 4 | 35(slsqp_4) | 1 |
| two_stage_ota_sf | 20 / 11 | 9 -> 2 | 4458 | 109 | 4349 | 0 | 0.18 | 42 ms | 6.6 | 107 | 16 | 103(slsqp_4) | 1 |

- kernel 은 탐침 선별 평가 포함. 9회로 모두 `kernel_calls == unique_keys`, `recompute_same_key == 0`, LUT memo 퇴출 0(I-1).
  requests/kernel = 5~80 배 -- 같은 x 의 fun·jac·cons·ε 재방문이 커널 0 으로 모였다(옛 SLSQP 811 중 784 중복 대조).
- 블록 reuse 비 = sizing 계산 블록(11개) reuses/calls. `block_recomputes_same_input` 1~492 -- FD 형제 lineage 사이 같은
  입력(sizing O8, graph 가 곧 캐시라 다른 lineage 값을 못 본다).
- FD 열 재사용(two_stage_ota, 열마다 sizing 블록 computes): current 열 = dc_currents 1·dc_columns **0**·dc_widths 1,
  ln_idu·y 열 = dc_columns 1·dc_widths 1·dc_currents 0, 같은 x 의 FD 반복 = 커널 0(I-4).
- 결정론: two_stage_ota 를 `PYTHONHASHSEED` 1·2 로 따로 돌려 대기 front 동일(I-8, 예산 미구속).
- front 가 한 점으로 줄어든다: 성능 제약을 잴 수 없어(S-1) 전력·면적이 같은 방향(전류 하한)으로 움직인다. ε 점은 대부분 그 한 점에
  지배당하거나 warm start 에서 ε 제약을 못 맞춰 SLSQP status 4(부등식 양립 불가)로 끝난다 -- 엔진 동작 확인용이고 front 로 의미가 없다.
- cProfile(cumtime): folded_cascode 48.6 s 중 size_and_seal 47.3 s(97%), LUT `gm_id_for_target` 27.5 s, core `fp_of` 19.5 s
  (40%), `Projection.from_snapshot` 10.6 s; two_stage_ota 14.4 s 중 size_and_seal 13.4 s, `fp_of` 8.5 s(59%). search 자체
  (키·캐시·원뿔·목적·제약·SLSQP 조립)는 2~7% -- 핫스팟은 sizing O9(투영 지문)·LUT 역산이다.
- [2026-10-08 core 성능 2~5 후 주석] 위 cProfile 의 `fp_of` 비중(40~60 %)은 옛 core(memo 키·레코드·투영마다 직렬화) 기준이다. 이제 memo 키는 `canonical_key`,
  레코드·스냅샷 지문은 읽을 때 한 번, 투영은 행 단위 sha256 이라 9회로 평가에서 fp 계열 비용이 옛의 약 1/3~1/10 이다(core CONTRACT 10.1).

### 10.x [r11, 사용자 결정 11, 2026-10-08] 면적 예산 9회로 재실행 (작성자 측 시연, 정본 아님; B = 120 s, 시연 harness mod6_demo)
- 예산: common_gate 0.005, pushpull_follower 0.005, folded_cascode 0.01, two_stage_ota 0.015, two_stage_ota_sf 0.015, sf_pushpull 0.02, ngcc 0.025,
  nmcnr 0.025, current_reuse 0.04 mm² (spec 제약 `area_search_m2 <= v`, 부하 CL·CL1·CL2·RL 은 `measurement_load` 로 제외, MIM 2 fF/µm²).
- 결과(시작점 / front 점): common_gate 2/2, current_reuse 0/0, folded 2/0, ngcc 2/0, nmcnr 2/0, pushpull 1/0, sf_pushpull 0/0, two_stage_ota 2/1,
  two_stage_ota_sf 2/1. front 점 면적은 전부 예산 이내(common_gate 0.55~2.4e-6 mm², two_stage_ota 6.2e-4 mm² (Rz 면적 미선언),
  two_stage_ota_sf 7.3e-3 mm²), W 최대 common_gate 1.1 µm · two_stage_ota 0.39 mm · two_stage_ota_sf 3.2 mm (종전 2.6e5 m 급 해소).
- SLSQP 입력 척도(slsqp_outer): 행 c 는 면적 예산 행처럼 크기가 1e6 급이라 종전 그대로는 QP 부분문제가 '제약 비호환'(status 4)으로 끝났다.
  SLSQP 에 넘기는 행·목적에만 양의 상수 배(행: 1/max(1,|시작점 c|), 목적: 1/max(1,|시작점 f|), ftol 도 같은 배)를 곱한다 -- 가능 집합·`best`
  판정(원 c ≥ 0)·`SolveResult` 값은 그대로.
- 남은 한계: 예산 때문에 시작점이 예산을 약간 넘는 회로(folded 등)는 120 s 안에 가능 점을 못 찾는다(front 0). 저항 면적은 PDK 단위 면적 선언이 없어 미포함.

## U9. `count_budget(lut, kinds, declared=None) -> int` (설계 41 §0·40 §10.1, D-NS; 파일 `count_budget.py`)

* 계수 예산 N_S = kind 들의 LUT 격자점 수 합 Σ_kind Σ_(폭 슬라이스) |L|·|VGS|·|VDS|·|VS|(시간 무관·결정론, 같은 LUT·kind 면 같다. 가산적: 두 kind 합 = 각 kind 합의 합). `declared`(authoring `CountBudgetDecl`)가
  있으면 `declared.value` 가 대체한다. 합이 1 미만이면(kind 없음·슬라이스 없음) `ValueError`.
* 쓰임: `pipeline.run_stage_a`(→ `build_s1v(count_budget=)` 사이클 열거·복합 블록 Π 상한)와 `run_stage_b`(→ `metrics.achievability` 블록 격자 곱 게이트). `pipeline.structure_count_budget` 은 이 함수의 얇은 호출이다.
* `passive_area_decl`(`area_decl.py`)을 공개 API 에 올렸다(`run_stage_b` 가 GB4 면적 하한의 커패시터 항 입력으로 부른다).

## 11. 잡음 제약 배선 (구현 단위 U8, 2026-10-09 -- 설계 41 §7.4, metrics CONTRACT 11절)

- `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, s1v=None)`: 끝에 선택 인자 `s1v`(`graph.build_s1v` 결과). 기존 호출(6인자)은 그대로 동작한다.
  - 값이 있는 판정 제약 중 잡음 metric(레지스트리 결과 형식 `NoiseAnalysis`)이 있으면 `search_domain` 뒤·`JunctionSource` 앞에서 `lut.require_lut_data(lut, MOS kind 들, noise=True)`:
    잡음 r1 데이터(`LutSet.noise`)가 없으면 `SchemaRejectedError(noise_lut_missing)`. (잡음 r1 없이 만든 LUT 로 library spec 의 잡음 제약을 올리면 이제 거부된다 -- test 입력은 `load_lut_set(noise_npz=)`
    와 `LutSpec.noise_ef` 로 잡음 데이터를 실어야 한다: **독립 test 갱신 필요**, test 작성자 몫.)
  - [U13 후속, 2026-10-09 오케스트레이터 결정: fail-closed] 같은 자리에서, 값이 있는 `offset_in_sigma_mv` 또는 `offset_excess` 판정 제약이 있고 MOS kind 의 mismatch 감도 r1 데이터(`LutSet.mismatch`)가 없으면
    `SchemaRejectedError(mismatch_lut_missing)`(설계 41 §6.4-2b, lut CONTRACT 9.5) -- `noise_lut_missing` 과 같은 시작 검사. library spec 은 `offset_excess` 를 선언하므로 mismatch r1 을 싣지 않은 LUT 는
    이제 거부된다(**독립 test harness 갱신 필요**, test 작성자 몫). `iv_matching_l` 의 `lut_mismatch_*` 비활성 사유는 이 검사를 우회해 직접 부르는 경우의 방어로 남는다.
  - `SearchContext.noise_decl` = `noise_decl(spec, s1v)`(metrics `NoiseDecl`): spec feedback 소자·`noise_testbench.sampling_caps`·S1v 전달 뷰의 첫 이득 블록 input 셀. `s1v=None` 이면 input 셀이 없어
    `noise_excess_th` 는 정의 불가(`noise_input_cell_undefined`) -- 미측정으로 보고된다(조용히 통과하지 않는다).
- `kernel.evaluate`: 봉인 점 `ss_evaluate(..., area_decl=, noise_decl=sctx.noise_decl)`. 잡음 metric 은 이제 `search_context` 가 `ss_constraints` 로 분류한다(레지스트리에 있고 view_kind 가 있다) --
  `constraint_notes` 의 `metric_computation_pending` 에서 빠지고 점마다 `ss:<k>:<metric><op>` 행(c = (목표 − 값)/분해능 등 기존 `ss_constraint_rows` 규칙)이나 `unmeasured` 사유(예
  `noise_thermal_unknown`, `resolution_undefined`)가 된다.



## U13. 출발 구간·매크로 모델 (설계 41 §6·§7.5·§5.8, 40 §11 U13 · §7.1 면적 예산 출발점; D-SIa~g, D-DN, D-NZ5)

**목적**: 층 0 의 상자 기하 중점(ln IDu −26~−34 = LUT 정의역 밖, 전류 pA·면적 예산의 12~99 배 퇴화점)을 스펙에서 유도한 소자별 gm/ID·L·전류 출발 구간의 선택점으로 바꾼다. 출발값과 보고에만 쓴다(EP-7).

### U13.1 공개 API와 배선

| 이름 | 파일 | 서명 / 뜻 |
|---|---|---|
| `start_intervals` | `start_intervals.py` | `start_intervals(s1v, ach, kctx, spec, pdk_decl, domain) -> StartIntervals` (S0 당 1회) |
| `build_search_context` [U13] | `search_context.py` | `build_search_context(dc_ctx, spec, settings, archive_root, pdk_decl, lut_rule_decl, s1v=None, ach=None, model_error=())` -- `s1v`(U7·U8 과 공유 한 인자)를 주면 `ctx.start = start_intervals(...)`. 안 주면 `ctx.start = None`(상자 중심) |
| `layer0_start` [U13] | `layer0_center.py` | `ctx.start.ladder`(StartRung 사다리)를 칸 순서로 커널에 확인해 처음 받아들일 상태인 칸에서 출발. 칸이 모두 안 되면 위반 크기가 가장 작은 칸에 S-4b 1단계 보정(`_repair`), 그래도 안 되면 Halton 시험(종전). `Layer0Result.origin_point` = `centre`(칸 0) · `ladder:k` · `ladder_repair:k` · `halton:k` · `repair:k` |
| `dominant_node` | `dominant_node.py` | `dominant_node(view) -> DominantNode(nets, rule)` -- Miller 루프 앞 노드 / 출력 포트 노드 / 버퍼 앞 마지막 이득 블록 노드(구조 판정, 매크로 모델 비사용) |
| `EvalBudget` | `eval_budget.py` | `EvalBudget(wall_s, times, reserve_evals=0)` · `.limit()` = ⌊B/t_eval⌋ − reserve · `.remaining()` = limit − 지금까지 평가 수 · `.t_eval()` = 중앙값. `kernel.evaluate` 의 E_B 한 번 유도가 `limit()` 을 쓴다(`derived_once:floor(B/median_t_eval)` 문자열·값 불변) |
| 값 형식 | `start_values.py` | `Bound`·`StartConflict`·`StartRow`·`StartRung`·`MacroResult`·`StartIntervals`·`StartContext` + 경계 식 이름 `SRC_*`·비활성 사유 `WHY_*`·`PM_FLOOR_DEG` |
| 내부 | `iv_context`(입력 묶음) · `iv_curves`(`CurveBook`: U3 곡선 API 를 gm/ID 축 묶음으로) · `iv_headroom`(§6.2) · `iv_speed`(§6.3·§6.4-4) · `iv_gain_l`(§6.4-1 블록 국소 모델 L 하한; 입력 묶음은 `iv_context`) · `iv_matching_l`(§6.4-2·2a) · `iv_noise`(§7.5) · `iv_area`(§6.4-5·최소 폭) · `iv_domain`(LUT 역산 정의역) · `iv_currents`(블록 gm -> 소자·θ 전류 아핀 전파) · `macro_poles`(§6.5) · `_helpers_curves`·`_helpers_area`·`_helpers_guard` | |

### U13.2 계산 순서와 경계 식 (설계 41 §6.1 의 순서, 순환 없음)

0. 주극점 노드 `dominant_node`. 1. gm/ID 하한: U9 `headroom_bound` 를 모든 MOS 단자 넷의 창으로 불러(복제 없음) 소자 엣지 예산 `U(윗 넷) − L(아랫 넷)`(다른 소자는 최소 비용) + 스윙·ICMR·입력 DC 분할 -> `vdsat_curve`·VGS 역산(`hull`).
2. L 상한(속도 §6.4-4, 면적 §6.4-5)·L 하한(matching §6.4-2; 이득 §6.4-1 = U9 블록 국소 모델이 블록 목표 g_i = G·A_i,max/ΣA_max 를 맞추는 최소 L -- A_max 미인증·이득 제약 없음이면 비활성 사유). 3. 1회차 매크로(gm/ID = 하한)로 전류. 4. L = max(하한), 동치류·자기동형 묶음 교집합, LUT L 칸으로 맞춤.
5. 그 L 에서 gm/ID: 하한(헤드룸, **LUT 역산 정의역 `iv_domain`**, 최소 폭 W ≥ W_min), 상한(속도 f_T ≥ f_np, offset·열잡음 가드, 면적, LUT 정의역 중점). 같은 VGS 묶음(`parallel_vgs`)은 구간 교집합 하나를 공유.
6. 선택 = 구간의 최댓값(t = 1), 면적 예산 안이고 매크로가 GBW·PM 을 풀 수 있는 최대 t(`bracket_root`); 7. 출발 사다리 = t, t/2, t/4, … (길이 = ⌈log2(gm/ID 구간 폭 최댓값 / LUT 곡선 gm/ID 최솟값)⌉ + 1, 선택 t = 0 이면 1칸).

* **경계는 항상 '나머지는 최소로 두고 k 가 가질 수 있는 최대'** (41 §6.2): 헤드룸 예산, 면적 A_k,avail, 가드의 level_k. 비어 있으면(하한 > 상한) 자르지 않고 `StartConflict` 를 남기고 헤드룸 쪽(포화)으로 닫는다.
* **gm 고정 전류 모델**(iv_area): 매크로가 정하는 것은 gm 이고 I(g) = gm/g. W(g) = gm·L/(g·IDu), 면적 gm·L²/(g·IDu) -- g 에 대해 증가.
* **비활성 사유**(조용히 빠지지 않는다): 제약 미선언(`constraint_not_declared`), LUT 데이터 없음(`lut_mismatch_unavailable`·`lut_noise_unavailable`), A_max 미인증(`u9_value_not_certified`), 전류 미정(`stage_current_unavailable`),
  PM 목표 없음(`pm_target_missing`, 속도 상한), `noise_out_int_vrms` 의 C_eff·1/f 하한 비활성 사유(U8 병합 뒤: LUT 잡음 없음 `lut_noise_unavailable`, 없는 입력 `c_eff_not_a_start_bound`(출발 어휘에 수동소자 값 경계·C_eff 소자 지정 없음)·`feedback_factor_beta_unavailable`(되먹임율 β 없음)).
* **매크로 모델**(`macro_poles`): 전달 뷰의 이득 블록마다 VCCS(gm_b, G_out = gm_b/A_intr, 버퍼는 A = 1) + 노드 용량(소자 cgg·cdd 는 전류에 비례하는 아핀 계수) + 수동소자(Miller C·영점 상쇄 R = 1/Σgm) + feedforward VCCS(G_ff = r_ff·gm_in(B_b), r_ff = 1).
  풀이 = |H(jω_GBW)| = 1 과 PM(ω_GBW) ≥ 목표를 지키는 **전원 전류 합 최소**(SLSQP). 비볼록(주극점이 어느 단에 놓이는지가 국소 최소를 가른다)이라 단마다 그 단을 주극점으로 하는 실행 가능한 출발점(나머지 단 gm 을 올리고 그 단 gm 으로 UGF = GBW)에서 다중 출발하고,
  구조 주극점 노드(`dominant_node`)의 단을 먼저 시도해 만족해 중 전류가 가장 작은 것을 쓴다(상대 1e-6 안 동률이면 먼저 얻은 쪽). 설계 §6.5 의 순차 바퀴는 gm_1 모서리로 퇴화해 쓰지 않았다(설계 41 §6.5 as-built 절). 극점·UGF·PM 은 U7 `solve_responses`·`analyze_loop`. 근 괄호가 없으면 `macro_root_missing`, 반복 한도에서 `macro_nonconvergent`.
  PM 목표가 없으면 PM_FLOOR_DEG = atan(1) = 45°(비주극점이 UGF 에 놓인 경계)를 **매크로 풀이 안에서만** 쓰고 기록한다(`pm_floor_pole_at_ugf`); 속도 gm/ID·L 상한(§6.3)은 PM 목표가 없으면 비활성(`pm_target_missing`).
  GBW 목표가 없으면 매크로 비활성(`macro_inactive`). 출력노드 컨덕턴스 G_i = gm_i/A_i: 이득 제약 + 전 블록 A_max 인증이면 블록 목표 g_i, 아니면 입력 소자의 LUT 진성 이득(설계의 중간 단계 'A_i,max' 는 쓰지 않았다 -- 이득 제약이 없으면 인증 상한을 실제 이득으로 볼 근거가 없다).
* **헤드룸 예산 분할**(설계 §6.2): 출력 DC 가 선언되지 않은 스윙·ICMR 창은 남는 여유(창 폭 − 요구)를 위·아래 부분 기둥의 남는 여유 중 최솟값이 가장 크도록(같은 몫) 나눈다. 판정 어휘가 `no_target`(레일–레일 경로가 VGS 엣지를 지나지 않는 창)이어도 선언 요구는 분할에 쓴다.
  곡선 전체가 예산을 만족해 하한이 곡선 최솟값이면 구간을 좁히지 않으므로 출처로 남기지 않는다.
* **가드(offset·열잡음)**: 입력 쪽 기여는 입력 소자가 가질 수 있는 최대(가드가 아닌 경계의 상한 안에서 기여가 최대인 곡선 마디, LUT 가 정의하지 못하는 마디는 제외), 부하는 최소에서 잰다 -- 가능한 가장 느슨한 경우라 거짓 충돌이 없다.
  mismatch/잡음 질의의 폭은 W_min 이상으로 맞춘다(모델 bin 밖 폭 방지). matching L 하한이 어느 앵커로도 안 맞으면 충돌 레코드를 남기고 가장 긴 앵커로 닫는다. 곡선 읽기(`at_gm_id`)는 gm/ID 를 품은 칸이 여럿이면(pmos 중반전 상승) 가장 오른쪽(강반전) 칸에서 읽는다.
* **최소 폭 보정**: 확정된 전류에서 W = I·L/IDu(g) < W_min 인 소자(같은 VGS 묶음은 함께)의 gm/ID 를 W = W_min 이 되는 g 로 올린다(전류가 입력 소자를 따르는 미러 부하는 gm 고정 하한이 1회차 전류로 재서 어긋난다). 전류가 바뀌므로 고정점까지 되풀이하고(상한 4),
  상한을 넘기면 충돌 레코드로 남긴다.
* **전류 확정**: 블록 입력 소자 방정식 `I_d = gm_b/(gm/ID)_d` + KCL 기저 행 + 미러(같은 VGS 묶음 폭 비 1) + FF 묶음 소자(G_ff/(gm/ID)) 전파. 정해지지 않은 소자의 자리값
  (`StartIntervals.current_ref`) = max(선택 점에서 W = W_min 인 전류 W_min·IDu/L, 정해진 전류들의 기하 평균). 층 0 의 Chebyshev 중심이 상자 기하 중심 대신 이 값을 기준 전류로 쓰고, 해의 편차 u(ln)만큼
  움직이는 θ 전류를 모두 올려(원뿔이 유지될 때만) 모든 MOS 가 기준 이상 = 폭 ≥ W_min 이 되게 한다(최소 폭 hard 제약 `w_min:*` 위반 방지).

### U13.3 불변식 (test 가 확인할 성질)

* 같은 입력이면 같은 표·같은 θ. 소자 순회·합산은 구조 색 순서이고 이름은 행 이름에만 쓰인다(이름 전단사 불변).
* 절대 offset 제약(`offset_in_sigma_mv`)이 없는 회로에서는 matching L 하한 무동작, 가드 제약(`offset_excess`·`noise_excess_th`)이 없으면 가드 상한 무동작.
* `ctx.start is None`(s1v 미전달)이면 `layer0_start` 는 종전과 같은 상자 중심 한 점.
* `StartIntervals.ladder[0]` 의 θ·cells·current_ref 는 `StartIntervals.theta`·`cells`·`current_ref` 와 같고, 각 칸의 `t` 는 절반씩 줄어든다.
* 매크로 풀이 값(gm·C)은 `macro_root_missing`·`macro_nonconvergent` 가 있으면 버린다(전류는 정해지지 않은 것으로 센다).

## [U17 ①-a] `build_search_context(..., *, code_fp)` -- 필수 키워드 인자

- `code_fp` = 단계 A 가 잰 엔진 코드 지문(`pipeline.StageAResult.code_fp` = core `engine_code_fp()`). 빠지면 파이썬 `TypeError`, 비어 있지 않은 문자열이 아니면 `TypeError`. `SearchContext.code_fp`·S3 기록 `code_fp` 가 이 값 그대로다. 옛 `_code_fp()`(core·lut·graph·sizing·metrics·search 6개 패키지)는 삭제됐고 여기서 다시 재지 않는다(설계 40 §2.4.3 (iii)).
