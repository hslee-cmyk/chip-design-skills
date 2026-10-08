# gmid_engine.authoring 회로 사이징 spec 로더 동작 계약 (MOD2, test 작성용)

- 대상: `load_sizing_spec` 과 spec 게이트 함수들(`gmid_engine.authoring.__all__`), core `MetricSignature`.
  test 는 `from gmid_engine.authoring import ...`·`from gmid_engine.core import ...` 만 쓴다. 배치는 규칙 D(H):
  `tests/authoring/test_spec_<파일>.py`, `tests/authoring/test__spec_fields.py`, `tests/core/test_metric_signature.py`,
  9회로 교차는 `tests/integration/`. **이 커밋에는 test 가 없다**(지시: 계약만) -- 규칙 H(`-m structure_test_mapping`)는
  이 16개 파일의 test 누락으로 FAIL 한다(기본 실행 밖). 7a 커밋(2026-10-07)이 더한 `spec_views.py`·`_feedback_cuts.py` 의
  test(`test_spec_views.py`·`test__feedback_cuts.py`)도 test 작성 역할 몫이다(같은 규칙 H 누락).
- 근거: `_drafts/engine/design_spec_format.md`(F1~F14 기본안 채택, 오케스트레이터 2026-10-07), `_drafts/user_decisions.md`
  2026-10-07, 계획 N3.15·N3.16·DEC-20·34·60·68·69·73·75·77, U-17·25·35·39. 실패 형식은 `CONTRACT.md` 0절과 같다.
- **배선**: `load_sizing_spec` 은 공개 진입점이다. **아직 엔진 안 호출자는 없다** -- 파이프라인 MOD10 이 S0 입력으로
  (MOD5 레지스트리에서 만든 이름표를 주입해) 부를 예정이다. 그 전까지 쓰는 곳은 이 계약의 test 와 9회로 로드 확인뿐이다.
- **요소 값 정본 = spec**(F5, 사용자 확정 2026-10-07): 수동소자·이상원 값은 `element_values` 에만 둔다. topology 의 옛
  값 필드 삭제와 `connectivity_fp` 투영에서 값 빼기는 topology 정리 단계 몫이라 이 커밋 밖이다(그동안 두 곳 값이
  어긋나면 `element_value_conflict` 로 거부).

---

## 0. 공개 진입점 `load_sizing_spec(path, topology, metric_catalog) -> SizingSpecDoc`

- `topology`: `load_topology` 가 만든 `TopologyDoc`(아니면 `TypeError`). None 경로 없음.
- `metric_catalog`: `Mapping[str, MetricSignature]`(아니면 `TypeError`). 빈 매핑이면 모든 제약이 `metric_unknown`.
- 순서: `load_json_checked` -> `check_spec_schema` -> `meta_cross_check` -> `supplies_declaration` -> `input_dc_declaration`
  -> `element_value_declaration` -> `constraint_declaration`(앞 게이트의 feedback 결과를 받아 기본 뷰를 `default_views` 로 로드
  한 번에 한 번 유도, 7a design) -> `compensation_target_declaration` ->
  `node_target_declaration` -> `intended_region_declaration` -> `settings_declaration` -> [2026-10-08]
  `theta_bound_declaration`(settings·elements 가 둘 다 나왔을 때만) -> `resolve_spec_references`.
- JSON 수준 위반은 `json_read` 예외 그대로. 그 밖 위반은 전부 모아 `SchemaRejectedError` **한 번**:
  detail = {`gate`: `"spec_load"`, `where`: 경로 문자열, `hits`, `rejected_gates`(정렬 tuple), `not_evaluated`}.
  `rejected_gates` 이름: `spec_schema`, `spec_meta`, `supplies`, `input_dc`, `elements`, `constraints`,
  `compensation_targets`, `node_targets`, `intended_region`, `settings`, `theta_bounds`, `untie_orbits`, `references`.
- `not_evaluated`: `all_sections`(최상위·`meta`·`human` 중 객체 아닌 것이 있음 -- 섹션 검사 없음),
  `topology_cross_checks`(meta 회로 이름 또는 topology 지문 불일치 -- 섹션 형식만 보고 topology 교차 검사는 안 함),
  `references`(앞 게이트에 위반이 있으면 참조 해석 안 함). 필수 human 키가 없으면 `missing_key` 하나만 내고 그 섹션 검사는 하지
  않는다(중복 보고 없음).
- `value_from_file` 대상: 같은 디렉터리 `<회로>.topology.json`(`load_topology`) + `<회로>.sizing_spec.json`(같은 로더, 같은
  이름표). 한 로드 안에서 같은 회로는 한 번만 읽는다. 사슬에 이미 있는 파일 = `ref_cycle`. 파일 없음 = `ref_unresolved`.
  대상 로드 거부(지문 불일치 포함) = `ref_file_rejected`(`elements` = 대상 hit 의 rule 들). **파일 사이 순환**(A→B→A)은
  대상 쪽 로드가 `ref_cycle` 로 거부되므로 바깥 hit 도 rule `ref_cycle`(`elements` = 대상 hit 의 rule 들, `ref_cycle` 포함)
  이다 -- `ref_file_rejected` 가 아니다.
- 캐시 없음: 같은 경로를 두 번 부르면 두 번 읽고 같은 `spec_fp` 를 낸다(결정론).

**측정 부하 표지 [사용자 결정 11, 2026-10-08]**: `element_values.<커패시터·저항 요소>` 항목(값 또는 engine)에 선택 키
`"measurement_load": true` 를 쓸 수 있다 -- 설계가 정하는 값이 아닌 측정 부하(CL·nmcnr RL 등)라는 선언이다. `ElementValue.measurement_load`
(기본 False)에 실리고 search 면적 축 `area_search_m2` 가 그 소자를 뺀다(이름이 아니라 이 선언이 정한다). true 가 아닌 값·커패시터/저항이
아닌 요소(전류원 등)는 `type`. 면적 예산은 일반 제약 `{metric: "area_search_m2", op: "<=", value: <m²>, source: user_spec}` 이다
(catalog 의 `area_search_m2`, view 없음, 판정 축 -- search 가 제약 행으로 잰다).

## 1. 파일 형식 (요약 -- 정본은 이 절과 각 파일 docstring)

`<topology_name>.sizing_spec.json`(topology 와 같은 디렉터리). 최상위 `{meta, human}` + `_` 주석 키(어떤 코드도 읽지 않음,
지문 밖). `meta = {schema_version: "5", circuit, topology_fp, origin}`. `origin` ∈ {canonical, fixture}.

결정 대기 표지 `{"pending": "<ID>"}`(주석 밖 키가 `pending` 하나): ID 형식 `SP-n`·`AC-n`·`CI-n`·`PA-n`·`ET-n`·`U-nn`·`MODn`.
모든 표지는 `SizingSpecDoc.pending`(경로, ID)에 모인다. 표지를 받는 자리: `input_dc`, `element_values.<이름>`, `feedback`,
제약 `metric`·`view`, 보상 목표 각 칸·`settling`, `node_voltage_targets_v`, `intended_region`, `objective.budgets`,
`search`·`spice_check`·`front_refilter` 각 칸. 그 밖 자리에 오면 그 섹션의 `type`.

human 키: 필수 = supplies_v, input_dc, element_values, feedback, constraints, node_voltage_targets_v, intended_region,
objective, search, spice_check, front_refilter. 선택 = pending_constraints, compensation_targets, [U5 2026-10-08]
gain_budget_db_override, driving_spec, structure_count_budget, [U5 후속 2026-10-09] noise_testbench(스키마 버전 `"5"` 그대로 -- 선택 키 추가).

[U5 2026-10-08, 설계 40 §3.1] 선택 섹션 3개(모두 `source` 필수, kind `user_spec` 만). **결정 대기 표지는 받지 않는다 -- 실제 거부**:
`driving_spec`·`structure_count_budget` 에 `{"pending": "<ID>"}` 를 쓰면 객체로 읽혀 `pending` 키가 `unknown_key`, 출처가 없어 `source_missing`
(두 hit; `driving_spec` 은 값 칸도 없어 `driving_spec_empty` 는 키 위반이 있으면 내지 않는다), `gain_budget_db_override` 는 list 가 아니라 `type`,
`noise_testbench` 는 `pending` 키 `unknown_key` + `sampling_caps` 없음 `type`:
* `gain_budget_db_override`: `[{"block": [<출력노드 넷>…], "value_db": 수, "source"}, …]`. `block` = **사전순 엄격 증가**로 정렬된 넷 이름
  배열(41 §1.7-3 블록 키 -- 정렬·중복 없음, 위반 `block_not_sorted`), topology 단자에 있는 넷(`block_net_unknown`), 같은 키 두 번
  `block_duplicate`. 결과 `GainOverrideDecl(block, value_db, source)` 블록 키순 tuple(없으면 `()`). 블록 키가 S1v 블록과 맞는지
  (`override_block_unknown`)는 구조 유도 뒤 GB5 가 본다.
* `driving_spec`: `{"slew_rate_v_per_s"?, "load_peak_amp"?, "load_dc_amp"?, "source"}`. 값 칸은 양의 유한 수(`type`), 하나 이상
  (`driving_spec_empty`). 결과 `DrivingDecl`(없는 칸 None) 또는 `None`.
* `structure_count_budget`: `{"value": 양의 정수(bool·실수 아님), "source"}`. 결과 `CountBudgetDecl` 또는 `None`(없으면 41 §0 의 LUT 격자 유도값).
* [U5 후속 2026-10-09] `noise_testbench`(41 §7.1 폐루프 모드 '스위치' kT/C): `{"sampling_caps": [{"element": <커패시터 이름>, "source"}, …]}`. `sampling_caps` 는
  비어 있지 않은 list(`type`), 항목 키는 {element, source}(그 밖 `unknown_key`), `element` 는 topology 수동소자 중 kind `capacitor`(`noise_cap_unknown`),
  같은 이름 둘 `noise_cap_duplicate`. 결과 `NoiseTestbenchDecl(sampling_caps=SamplingCapDecl(element, source)… 이름순)` 또는 `None`. 섹션 지문 `noise_testbench_fp`.
  소비자는 잡음 계산 단위(U8)이고 그 전에는 로드·지문만 한다.

[2026-10-08] `search` 의 선택 칸 `untie_orbits` = `{"<원소>": {"source": {...}}, ...}`(사용자 결정 '정준 라벨링 + 대칭 변수 묶음, 기본값 묶음', search
CONTRACT r12 3.24). 기본은 **자기동형 궤도 원소의 같은 종류 θ 성분을 한 변수로 묶는다**(대칭 사이징). 이 칸은 그 원소가 속한 궤도의 묶음을 풀어
의도한 비대칭 사이징을 허용한다(원소 하나만 적어도 궤도 전체가 풀린다). 닫힌 어휘 = 원소 이름을 키로, 값은 `{source}` 객체 하나뿐(`_` 주석 키 허용).
**출처 필수이고 kind 는 `user_spec` 만**(`record`·`decided` 필수 -- 섹션 이름 `search_untie`, `plan_rule` 은 받지 않는다: 비대칭 선택은 사용자 결정이다).
원소 = topology MOS 또는 수동소자 이름(아니면 `untie_element`). 궤도가 그 원소 하나뿐이면 search `orbit_ties` 가 `untie_orbit_trivial` 로 거부(그래프가
필요해 spec 로드가 아니라 search 정의역 만들 때). 결정 대기 표지는 받지 않는다. 결과 = `SettingValue("untie_orbits", ((원소, source), ...) 이름순)`
(theta_bounds 다음, 있을 때만, 공개 상수 `UNTIE_ORBITS`).

[2026-10-08] `search` 의 선택 칸 `theta_bounds` = `{"<원소>": {"min": <수>, "max": <수>, "source": {...}}, ...}`(사용자 결정 8·10,
search CONTRACT r10). 원소별 θ 수동소자 탐색 상자. 단위 = 원소 kind 의 SI 단위(resistor Ω, capacitor F -- 키 이름에 단위를 쓰지
않는다, kind 가 정한다). 원소 = topology 수동소자 중 kind ∈ {resistor, capacitor} 이고 spec `element_values.<원소>` 가 `engine`
인 것만(고정 값·결정 대기·MOS·이상원·모르는 이름은 `theta_bound_element`). min·max 양의 유한 수(bool 아님), min < max. 칸 키 =
{min, max, source} 닫힌 어휘(`_` 주석 키 허용), 출처 필수(search 섹션 허용 kind = user_spec·plan_rule). 결정 대기 표지는 받지
않는다(상자가 없으면 칸을 비운다 -- 그 원소는 search 가 `theta_*_bounds_undeclared` 로 거부). 칸이 없거나 빈 객체여도 로드는 통과.

[2026-10-08] `intended_region` 영역 어휘 = `REGIONS` = (`REGION_TRIODE` = `"triode"`,)(design_spec_format 표 1.6) -- 공개 상수
`REGION_TRIODE` 가 정본이다. 그 밖 낱말(예 `"linear"`, `"saturation"`)은 `type`. 소비자: sizing `LINEAR_REGION`(= 이 상수)이
`linear_devices`(봉인 7 포화 여유 제외 대상)를 만든다 -- sizing 은 낱말을 따로 정의하지 않는다.

출처 `source`(모든 값 선언에 필수): kind ∈ {user_spec, pending_spice, reference, plan_rule}.
| kind | 필수 부필드 | 허용 섹션 |
|---|---|---|
| user_spec | `record`(비어 있지 않음), `decided`(YYYY-MM-DD); `origin` ∈ {user, paper, drawing, lecture, legacy_harness}, paper·drawing·lecture 면 `citation` | 전부 |
| pending_spice | `record` | constraints(판정 안 함, U-17) |
| reference | 없음(값 대신 `value_from_constraint`/`value_from_file`) | constraints, compensation_targets |
| plan_rule | `plan_id` | search, spice_check, front_refilter |

## 2. 위반 규칙 (hit `rule` -> 조건)

| rule | 조건 | 게이트 |
|---|---|---|
| `top_not_object` | 최상위가 객체 아님 | spec_schema |
| `missing_key` | `meta`·`human`·meta 4키·human 필수 키·search/spice_check/front_refilter 필드 없음 | spec_schema, settings |
| `unknown_key` | 닫힌 어휘 밖 키(옛 이름·회로 전용 키가 아닌 것) -- 모든 객체 | 해당 섹션 |
| `legacy_name` | 키가 옛 이름 표(`_spec_fields.LEGACY_NAMES`), 제약 metric·참조 문자열이 옛 이름, source kind `pending_7a` | 해당 섹션 |
| `circuit_specific_key` | 키가 회로 전용 키 표(`CIRCUIT_SPECIFIC_KEYS`: compensation, function, kg, Z, NDP, stage_devices, minimize, inherits, spec_fn …) | 해당 섹션 |
| `type` | 형식 위반(객체/list/문자열/유한 수/bool, 값 자리·모드 키 개수, sense_mode 어휘, region 어휘 …) | 해당 섹션 |
| `schema_version` | meta.schema_version ≠ `"5"` | spec_schema |
| `pending_id_format` | 결정 대기 ID·pending_constraints decision 형식 밖 | spec_schema, constraints |
| `circuit_name_mismatch` | meta.circuit ≠ topology.name, 또는 ≠ 파일 이름 stem | spec_meta |
| `topology_fp_mismatch` | meta.topology_fp ≠ topology.connectivity_fp | spec_meta |
| `source_missing` / `source_kind_unknown` / `paper_source_not_adopted` / `source_kind_not_allowed_here` / `source_record_missing` / `source_origin` / `citation_missing` | 1절 출처 표 위반(kind paper·paper_reference·literature·drawing 은 `paper_source_not_adopted`) | 해당 섹션 |
| `supplies_value` / `supplies_net_missing` / `supplies_net_extra` / `supplies_top_rail_ambiguous` | 레일 전압 비유한 / topology 레일 빠짐 / 레일 밖 넷 / 최고 전위 레일 둘 이상 | supplies |
| `input_dc_net_not_rail` / `input_dc_out_of_rails` | net 이 레일 밖 / value_v 가 레일 전압 범위 밖 | input_dc |
| `element_unknown` / `element_undeclared` | spec 이름이 topology 수동·이상원 밖 / topology 원소 선언 누락(F4) | elements |
| `element_value_key` / `element_value` | 값 키 ≠ kind 표(capacitor→value_farad, resistor→value_ohm, current_source→value_dc_amp, voltage_source→value_dc_v) / 수동소자 값 ≤ 0 | elements |
| `element_value_conflict` | topology 원소(수동소자·이상원)에 옛 값이 있는데 spec 이 다른 값·engine·pending(F5 이관 전 안전망 -- topology 값으로 spec 을 채우지 않는다) | elements |
| `feedback_element_unknown` | feedback.elements 이름이 topology 수동소자 밖 | elements |
| `feedback_element_not_on_input` | feedback.elements 소자의 두 단자 중 입력 포트 넷(direction input)에 물린 것이 없다 -- 루프를 끊을 단자가 없음(7a design 2.2 L2, 오라클 C14 막힘과 같은 조건) | elements |
| `feedback_cut_ambiguous` | feedback.elements 소자의 두 단자가 모두 입력 포트 넷 -- 끊을 단자가 정해지지 않음(오라클 C14 보강과 같은 조건) | elements |
| `node_target_net` | 노드 목표 넷이 레일이거나 단자 넷 밖 | node_targets |
| `intended_region_device` | 소자가 topology 밖 | intended_region |
| `metric_unknown` | 제약·pending_constraints metric 이 이름표 밖 | constraints |
| `op_value` | 제약 op ∉ {>=, <=}, 예산 op ≠ <= | constraints, settings |
| `value_and_ref` | value / value_from_constraint / value_from_file 이 정확히 하나가 아님 | constraints, compensation_targets |
| `ref_kind_mismatch` | 참조인데 source.kind ≠ reference, 또는 그 반대 | constraints, compensation_targets |
| `view_not_applicable` | view_kind None(뷰 없음)인 metric 에 view, metric 결정 대기 제약에 (결정 대기 아닌) view, **loop·cm_loop metric 에 결정 대기 아닌 view**(단 loop metric 의 내부 루프 선언 `{"loop_cut": [...]}` 와 cm_loop 의 `{"cm_sense_elements": ...}` 는 예외; 루프 뷰는 유도만 -- 7a design 2.9, CM 루프도 같다) | constraints |
| `view_shape_not_supported` | loop·cm_loop metric 에 명시 모양 `{"cut_weights": …}` -- 계약에 예약된 모양(7a design 2.9)이지만 첫 소비 spec 이 생길 때까지 구현하지 않는다(조용히 무시하지 않고 거부, 7절 S3) | constraints |
| `view_required` | ratio metric 에 view 없음 / transfer·loop(β = 1)에 view 없고 입력 포트가 차동쌍 1개(role differential_input_p·_n)·단일 1개(single_ended_input)가 아니거나 출력 포트가 단일 1개·차동쌍 1개(differential_output_p·_n)가 아님 / loop(β 루프)의 절단 넷 role 이 가중 어휘 밖 / **cm_loop(`pm_cm_ss_deg`)에 view 가 없고 구조 유도가 안 됨 -- 차동 출력쌍 없음·평균 수동소자로 gate 에 먹이는 감지 넷 없음·후보 둘 이상(3절 `cm_loop`)** / output_port 에 view 없고 출력 포트가 1개가 아님 | constraints |
| `view_excite_not_allowed` | output_port view 에 `ac_excite`(감지 전용 -- 여기는 DEC-66 이 고정) | constraints |
| `view_sense_fixed_net` | output_port 감지 넷(sense_p·sense_n)이 고정 넷: 레일·입력 포트 넷·gate 전용 미구동 넷(레일·입력 포트가 아니고 단자가 전부 MOS gate -- graph `ac_ground_class` 비 None 과 같은 정의) | constraints |
| `view_net_unknown` | 뷰 넷(ac_excite 키·sense_p·sense_n·loop_cut 원소)이 어느 단자에도 없음 | constraints |
| `constraint_duplicate` | 같은 (metric, op, view) 두 번(metric·view 결정 대기 제약은 비교 밖) | constraints |
| `settling_order` | settling.linear_s > total_s | compensation_targets |
| `budget_metric_not_objective` | 예산 metric 의 `objective_axis` 가 None 또는 이름표 밖 | settings |
| `search_method` / `optional_stage_unknown` | search_method ∉ {default, precision} / optional_stages 키 ∉ {inner_block_dp, middle_y_coordinate_descent, threshold_bisection, global_sample_budget_fill} | settings |
| `numeric_in_rule_field` / `rule_name_unknown` | 규칙 칸에 수 / 어휘 밖 규칙 이름 | settings |
| `type`(theta_bounds) | `theta_bounds` 가 객체 아님 / 원소 칸이 객체 아님 / min·max 가 양의 유한 수가 아님(0·음수·문자열·bool) | settings |
| `missing_key`(theta_bounds) | 원소 칸에 min 또는 max 없음(없는 키마다 하나, where `…theta_bounds.<원소>.<키>`) | settings |
| `theta_bound_range` | min ≥ max | settings |
| `unknown_key`·`source_*`(theta_bounds) | 원소 칸 키가 {min, max, source} 밖 / 출처 표 위반(1절) | settings |
| `theta_bound_element` | 원소가 topology 저항·커패시터 밖이거나 spec 값 mode 가 engine 아님 | theta_bounds |
| `legacy_name`(정합 metric, U5) | 제약 metric 또는 `value_from_constraint`·`value_from_file` 문자열이 `mismatch_sigma_mv`·`mirror_ratio_error_mv`·`mismatch_sigma_v`(및 대문자 V 판) -- 메시지가 새 이름을 안내(`_spec_fields.LEGACY_REPLACEMENT`: offset_in_sigma_mv / offset_excess / offset_sys_mv / mirror_ratio_sigma_pct). `input_dc_net`·`topology_hash`·`derived` 는 정본 이름이라 옛 이름 표에서 뺐다(키로 오면 어휘 밖이라 `unknown_key`) | constraints, 해당 섹션 |
| `block_not_sorted` / `block_net_unknown` / `block_duplicate` | gain override 블록 키가 사전순 엄격 증가 배열이 아님(중복 넷 포함) / 넷이 어느 단자에도 없음 / 같은 블록 키 두 항목 | gain_budget_db_override |
| `driving_spec_empty` | driving_spec 값 칸 3개 중 하나도 없음 | driving_spec |
| `noise_cap_unknown` / `noise_cap_duplicate` | noise_testbench 샘플링 커패시터가 topology 의 capacitor 수동소자가 아님(없는 이름·저항 등) / 같은 이름 두 항목 | noise_testbench |
| `type`(U5 섹션) | override 항목·block 이 모양 밖, driving 값이 양의 유한 수 아님, noise_testbench·sampling_caps·항목·element 가 모양 밖, count budget 이 양의 정수 아님(bool·실수·0·음수). `value_db` 가 `NaN`·`Infinity`·`1e999` 면 이 게이트에 오기 전에 `json_read` 가 `non_finite` 로 거부한다(`SchemaRejectedError`, `type` 이 아니다; 파싱된 값이 문자열·bool 등 비수면 `type`) | gain_budget_db_override, driving_spec, structure_count_budget, noise_testbench |
| `type`(untie_orbits) | `untie_orbits` 가 객체 아님 / 원소 칸이 객체 아님 | settings |
| `unknown_key`·`source_*`(untie_orbits) | 원소 칸 키가 {source} 밖 / 출처 없음(`source_missing`)·kind 가 user_spec 아님(`source_kind_not_allowed_here`)·record/decided 없음 | settings |
| `untie_element` | untie_orbits 원소가 topology MOS·수동소자 이름이 아님 | untie_orbits |
| `ref_unresolved` / `ref_ambiguous` / `ref_cycle` / `ref_file_rejected` | 참조 대상 없음·형식 틀림 / 같은 metric 제약 둘 이상 / 순환(파일 안·파일 사이) / 참조 파일 로드 거부 | references |

규칙 어휘: spice_check = acceptance_rule{free_spec_and_all_saturated}, saturation_rule{vds_ge_vdsat, vds_ge_vdsat_plus_tol_v},
node_compare_rule{record_only}, device_compare_rule{record_only}, forced_warn_rule{forced_device_diff_gt_lut_tolerance},
front_points_rule{endpoints_and_budget_point, all_front_points, budget_point_only}; front_refilter = axis_rule
{layout_floorplan_outline}, tie_rule{manufacturing_grid_cell_area}, cycle_cap_rule{k_max_n3_6}. 끄는 키는 없다.

## 3. 결과 `SizingSpecDoc` (frozen, `require_immutable` 통과, `fp_of` 가능)

- 필드: `circuit`, `topology_fp`, `origin`, `supplies_v`((넷, V) 이름순), `input_dc`(`InputDc` mode net/value/engine/pending),
  `element_values`(`ElementValue` 이름순, mode value/engine/pending), `feedback`(이름순 tuple 또는 `PendingMark`),
  `constraints`(`ConstraintDecl` 문서 순서), `pending_constraints`((metric, ID) tuple), `compensation_targets`
  ((키, `TargetDecl`/`SettlingDecl`/`PendingMark`) 이름순), `node_voltage_targets_v`, `intended_region`, `objective`
  (`ObjectiveBudget` tuple 또는 `PendingMark`), `search`(`SettingValue` tuple -- [2026-10-08] `theta_bounds` 가 있으면 맨 앞에
  `SettingValue("theta_bounds", (ThetaBound(element, kind, lo, hi, source), ...) 원소 이름순)`, 공개 상수 `THETA_BOUNDS`; [2026-10-08] `untie_orbits` 가 있으면 그 다음 `SettingValue("untie_orbits", ((원소, source), ...) 이름순)`, 공개 상수 `UNTIE_ORBITS`),
  `spice_check`·`front_refilter`(`RuleChoice`), [U5] `gain_budget_db_override`(`GainOverrideDecl` 블록 키순 tuple, 없으면 `()`),
  `driving_spec`(`DrivingDecl` 또는 `None`), `structure_count_budget`(`CountBudgetDecl` 또는 `None`), `noise_testbench`(`NoiseTestbenchDecl` 또는 `None`),
  `pending`(`PendingMark` (경로, ID) 정렬), `section_fps`, `spec_fp`, `file_sha256`. 속성 `judged_constraints`.
- `ConstraintDecl`: 참조는 해석된 `value`, `judged` = user_spec True / pending_spice False / reference 는 대상의 judged,
  metric 결정 대기면 `metric` None·`metric_decision`·`judged` False·`view` None. 참조 대상이 결정 대기면 `value` None +
  `value_decision`(그 ID 가 `pending` 에도 들어간다). `view.mode` ∈ none/port/transfer/ratio/pending/loop/sense/cm_output
  (공개 상수 `VIEW_MODE_NONE`·`_PORT`·`_TRANSFER`·`_RATIO`·`_PENDING`·`_LOOP`·`_SENSE`·`_CM_OUTPUT`, 묶음 `VIEW_MODES` -- 정본 `spec_model`;
  role 상수 `ROLE_DIFFERENTIAL_INPUT_P`·`_N`·`ROLE_SINGLE_ENDED_INPUT`·`ROLE_DIFFERENTIAL_OUTPUT_P`·`_N`, 방향 `INPUT_DIRECTION`·
  `OUTPUT_DIRECTION`, 감지 모드 `SENSE_DIFFERENTIAL`·`SENSE_SINGLE_ENDED`·`SENSE_MODES`도 `__all__` -- graph 가 문자열을 복제하지 않는다).
- `ViewDecl` 유도 필드(view 를 적지 않은 제약 -- `default_views(topology, feedback)` 가 로드 한 번에 한 번 계산, 7a design
  2.2·2.3·2.5·3.1):
  - 입력 포트 role 가중: 차동 입력 포트 집합 D 의 p = +1/|D|, n = −1/|D|(|D| = 2 → v_id = 1, v_cm = 0), 단일 입력 = 1.
  - `port`(transfer 기본): `weights` = 입력 포트 (넷, 가중) 넷순, `sense` = `SenseDecl(sense_p, sense_n, sense_mode)`
    (출력 1개 → single_ended, 차동 출력쌍 → differential).
  - `loop`(pm_ss_deg 기본): `beta` ∈ {`declared`, `unity`}(`BETA_DECLARED`·`BETA_UNITY`). declared(feedback 비지 않음):
    `cuts` = (되먹임 소자, 절단 넷) 소자 이름순 -- 절단 넷 = 소자의 입력 포트 넷 쪽 단자 넷, `weights` = 절단 넷 (넷, 가중)
    넷순, `sense` None. unity(feedback 빈 list): `weights`·`sense` 가 `port` 와 같다. feedback 이 결정 대기 표지면 view =
    `pending`(decision = feedback 의 ID -- 새 표지를 `pending` 에 더하지 않는다, 이미 `human.feedback` 표지로 들어 있다).
  - `cm_loop`(pm_cm_ss_deg, [CM 2026-10-08] 공통 모드 루프 PM -- 출력 포트 CM 주입, 사용자 결정 2026-10-08): 선언된 차동 출력 포트 쌍(role differential_output_p·_n 각 하나, 다른 출력 없음)이 있으면
    `ViewDecl("cm_output", weights=((p, 1/2), (n, 1/2)), cuts=((구동자 MOS, 출력 넷), …))`. 구동자/소비자 분류는 `cm_partition`(metrics CONTRACT 7.11: 출력 넷에 channel 이 물린 MOS 의 다른 channel 단자에서
    MOS channel·수동소자를 따라 레일(공급 레일·이상원 단자 넷)에 닿으면 구동자, 안 닿으면 소비자, 닿지만 gate 가 걸린 감지 쪽 넷을 거치면 모호; 절단 교차 검사). 모호하면 `view_required` 사유(`DefaultViews.cm_loop` 가 문자열) --
    제약 `view` 로 **`{"cm_sense_elements": [소비자(CM 감지) MOS 이름…]}`** 을 선언해 대체한다(닫힌 어휘: 그 키 하나만; 서로 다른 MOS 이름 list, 빈 list 가능; 이 제약의 `source.kind` 는 `user_spec` 필수). 선언은 분류를 덮어쓰지만
    구조가 명확하면 구조 소비자 집합과 같아야 한다. 거부 규칙: `cm_sense_unknown`(topology MOS 아님), `cm_sense_not_on_output`(drain·source 가 출력 넷에 안 물림), `cm_sense_disagrees`(구조 명확 + 불일치),
    `cm_sense_source`(출처 user_spec 아님), `cm_partition_ambiguous`(선언해도 절단 교차 검사 실패), `cm_pair_missing`(차동 출력쌍 없음), `cm_switched`(수동소자·이상원 kind ∈ `SWITCHED_KINDS` = "switch"/"clock" -- 스위치드
    커패시터 CMFB 는 연속시간 소신호 MNA 로 표현할 수 없어 명시적 정지). 선언이 없으면 `DefaultViews.cm_loop`(ViewDecl 또는 사유 문자열). 제약이 선언돼야 판정하고, 선언이 없으면 metrics 가 보고 전용으로만 계산한다(7.11).
  - `sense`(rout_ss_ohm): `sense` = `SenseDecl`(기본 = 출력 포트 1개면 그 넷 single_ended, 선언이면 그 감지 칸).
  - topology 교차 검사를 못 한 로드(meta 불일치 -- 어차피 거부)나 feedback 이 거부된 로드에서는 유도하지 않은 mode 만 담는다.
- 유도된 내용이 `ViewDecl` 에 들어가므로 `constraints_fp` 가 feedback·ports 변경을 따라간다(feedback 만 바꿔도 loop 제약이
  있으면 `feedback_fp` 와 `constraints_fp` 가 함께 바뀐다).
- 지문: `SpecSource` 는 `kind` 만 지문에 든다(`record`·`citation`·`decided`·`origin` 문구는 밖). `_` 주석 키 밖. 참조는
  해석된 값으로. 제약은 내용 지문 정렬(순서만 바꾼 spec 은 같은 지문). 섹션 지문(`SECTION_GROUPS`):
  supplies_fp(supplies_v), operating_fp(input_dc·node_voltage_targets_v·intended_region), elements_fp, feedback_fp,
  constraints_fp(constraints·pending_constraints), compensation_fp, objective_fp, search_fp, spice_check_fp, refilter_fp,
  [U5] gain_override_fp(gain_budget_db_override), driving_fp(driving_spec), count_budget_fp(structure_count_budget), noise_testbench_fp(noise_testbench).
  `spec_fp` = `fp_of(section_fps)`. spice_check 만 바꾸면 spice_check_fp·spec_fp 만 바뀐다. `theta_bounds`(원소·kind·min·max·
  출처 kind)는 `search_fp` 에 든다 -- 상자만 바꾸면 search_fp·spec_fp 만 바뀐다.
- **실행 전 정지(MOD10 몫, 이 로더 밖)**: 사이징 실행이 읽는 필드에 `pending` 이 하나라도 있으면 전부 모아
  `SchemaRejectedError` 한 번(결정 ID 목록). 로더는 표지를 통과시키고 모으기만 한다.

## 4. `MetricSignature(unit, domain, view_kind=None, objective_axis=None)` (core, 데이터 선언)

- frozen. `unit` ∈ `core.units.METRIC_UNITS`(db, hz, deg, ohm, mv, amp, w, m2, [U5] pct, ratio, v, v2_per_hz -- DEC-68 이름 접미사 어휘),
  `domain` ∈ `core.units.DOMAINS`(dc, ss, ls, geom), `view_kind` ∈ {None} ∪ `VIEW_KINDS`(transfer, loop, cm_loop, output_port,
  ratio -- MOD5 레지스트리 어휘, 정본은 `core.metric_signature.VIEW_KINDS` 한 곳; None = 뷰를 쓰지 않는 metric, 문자열
  `"none"` 은 어휘 밖), `objective_axis` ∈ {None} ∪ `OBJECTIVE_AXES`(power, area). 밖이면 `ValueError`.
- `ViewDecl.mode`(3절, none/port/transfer/ratio/pending/loop/sense/cm_output)는 로드 결과의 뷰 모양이고 `view_kind` 어휘와 별개다
  (view_kind None 인 metric 의 결과 mode 가 `none`, loop 는 `loop`, output_port 는 `sense`).
- loop·output_port 뷰는 7a design(`_drafts/engine/design_7a_loop_output_views.md`)에서 정의되어 판정한다 -- 결정 대기 표지
  전용이던 제한(옛 `view_not_defined_yet`)은 해제됐다.
- 이름표 정본은 MOD5 레지스트리(core 에 이름 없음). `metrics.metric_catalog()` = 레지스트리 서명 + [U5] **계산 대기 서명**
  (`metrics/pending_metrics.py`: offset_in_sigma_mv·offset_excess·offset_sys_mv·mirror_ratio_sigma_pct·swing_out_v·icmr_v·icm_margin_v·ff_gm_ratio(ratio, ss, transfer)·
  noise_th_in_v2hz·noise_fc_in_hz·noise_excess_th·noise_out_int_vrms -- 서명만, 계산은 U7·U8). 로더는 이 이름의 제약을 받는다.
  카탈로그에 있고 레지스트리에 없는 이름이 계산 대기이며, 탐색 문맥이 `constraint_notes` 에 `unmeasured`/`metric_computation_pending` 으로 남긴다.

## 5. 9회로 spec 로드 결과 (2026-10-07, 이 커밋 코드 + library, 픽스처 이름표)

픽스처 이름표 = gain_ss_db·ugf_ss_hz·gbw_ss_hz·parasitic_pm_ss_deg(transfer), pm_ss_deg(loop), rout_ss_ohm(output_port), ratio_ss_db(ratio),
mismatch_sigma_mv·mirror_ratio_error_mv·power_dc_w·area_search_m2(None), supply_current_dc(power), area_layout_m2(area).
9/9 통과(0 hit), 두 번 로드 `spec_fp` 동일. 레지스트리 이름이 없는 2건(파일럿 옛 `classab_centering_dev_v`, ngcc 입력 범위
옛 `icmr_v`)은 제약 `metric: {"pending": "MOD5"}` 로 값·출처를 남기고 판정 밖으로 두었다.

| 회로 | 제약(판정) | pending 표지 |
|---|---|---|
| common_gate_amplifier | 2(2) | 6 |
| current_reuse_telescopic_ota | 13(12) | 11 |
| folded_cascode | 3(3) | 7 |
| ngcc_3stage_ff | 6(6) | 6 |
| nmcnr_amplifier | 7(7) | 6 |
| pushpull_follower_buffer | 2(2) | 5 |
| sf_pushpull_output_opamp | 6(6) | 6 |
| two_stage_ota | 5(5) | 7 |
| two_stage_ota_sf | 6(6) | 6 |

[U5 2026-10-08] 위 표는 U5 반영 뒤 실측이다(옛 표 값 -- 파일럿 9(6)·ngcc 3(2) 등 -- 은 면적 예산 제약(결정 11)·`[CM]` 제약을 반영하기
전이라 낡았고, U5 직전 master 실측은 파일럿 10(7)이었다). 변경(설계 40 §9·§9.2, 픽스처 이름표가 아니라 `metrics.metric_catalog()` 로 로드):
* 파일럿 +3(=10(7) → 13(12)): 옛 `mismatch_sigma_mv`(pending_spice)·`mirror_ratio_error_mv`(참조)를 지우고 `offset_in_sigma_mv <= 3.3`,
  `offset_sys_mv <= (value_from_constraint offset_in_sigma_mv)`, `swing_out_v >= 2.4`, `icm_margin_v >= 0`(입력 DC SP-2 대기 -- 계산은
  `input_dc_pending` 보고), `noise_out_int_vrms <= 3e-4` 를 더했다. 판정 7 → 12(옛 두 줄은 판정 밖이었다).
* two_stage_ota 2(1) → 5(5): `mismatch_sigma_mv` 폐기, `gbw_ss_hz >= 7e6`(Q5, 보상 목표를 제약으로 승격 -- `compensation_targets.gbw_target_hz` 는
  `value_from_constraint: gbw_ss_hz` 로 바꿨다), `offset_excess <= sqrt(2)`, `noise_excess_th <= 2`. pending_constraints 에서 `gbw_ss_hz`(SP-5) 삭제.
* two_stage_ota_sf: `mismatch_sigma_mv` 참조 폐기, `gbw_ss_hz`(`value_from_file two_stage_ota#gbw_ss_hz`), `offset_excess`, `noise_excess_th`.
* ngcc: 제약 `metric: {"pending": "MOD5"}` → `icmr_v >= 0.6`(값·출처 유지), 가드 `offset_excess`·`noise_excess_th`. pending 표지 7 → 6.
* nmcnr: `icmr_v >= 0.5`, `swing_out_v >= 0.5`, 가드 `offset_excess`·`noise_excess_th`. folded·sf_pushpull: 두 가드. common_gate: `noise_excess_th` 만.
  pushpull_follower_buffer: 변경 없음(offset·잡음 제약 없음, 보고만).
* 남은 표지 총 60(옛 61 -- ngcc MOD5 metric 표지 1개 해소, MOD5 6 → 5).
* 가드 6회로(offset) = two_stage·two_stage_sf·folded·ngcc·nmcnr·sf_pushpull, 잡음 가드 7회로 = 위 6 + common_gate. 새 제약의 기본 뷰는 전부
  `port`(차동/단일 입력·출력 포트 유도)로 풀렸고 `view_required` 는 없다. swing·icmr·icm_margin 은 뷰가 없다(`none`).

남은 표지 61개(U5 전; 지금은 위 U5 문단) = AC-3 9, PA-1 9, PA-2 9, CI-15 9, CI-18 9, SP-2 7, MOD5 6(파일럿 뷰 4·metric 1, ngcc metric 1), SP-3 2,
CI-17 1(folded Ibg). CI-10 해소(사용자 2026-10-08 "5번도 네 의견에 동의해"): 파일럿 feedback = {Cf1, Cf2}(출력->입력),
Cs1·Cs2 는 입력 부하라 되먹임이 아니다 -- spec 에 선언하고 `pm_ss_deg` 뷰 표지(MOD5)를 지워 loop 뷰(declared, cuts (Cf1, Vip)·(Cf2, Vim),
가중 (Vim −½, Vip +½))가 유도되게 했다. 기존 결정으로 푼 칸(오케스트레이터 적용 2026-10-07): 포화 규칙 `vds_ge_vdsat`(UD 8번, 여유 0), 파일럿 밖 8회로 feedback `[]`(UD 9번 PM 정의 β=1), 보상 소자
engine(파일럿 Cc1·Cc2·Rz1·Rz2, ngcc Cm1·Cm2, two_stage_ota_sf Cc -- nmcnr·two_stage 확정과 같은 원칙), SP-10 = 파일럿
CL1·CL2 각각 1 pF(사용자 2026-10-07 "파일럿 CL1·CL2가 각각 1 pF", user_spec).

거부 실측(임시 스크립트, 원본 한 곳씩 깨뜨림): 2절 규칙 전부가 실제로 hit 를 냈다(`ref_ambiguous`·`source_origin`·
`settling_order`·`view` 형식 `type` 은 미실측).

7a 재측정(2026-10-07, 이 커밋 코드 + library, 픽스처 이름표 -- 위 표·표지 수는 바뀌지 않았다: 9/9 통과, pending 63):
- 유도 뷰: loop β = 1 2건(ngcc_3stage_ff·nmcnr_amplifier `pm_ss_deg` -- 가중 (n −½, p +½), 출력 1개 single_ended), β 루프
  유도 0건(8회로 feedback `[]`, 파일럿은 결정 대기). sense 3건(pushpull·sf_pushpull·two_stage_ota_sf `rout_ss_ohm` = 출력
  포트 single_ended). 파일럿 `pm_ss_deg` 는 (2026-10-08 이전) 선언 표지 MOD5 가 있어 mode `pending` 이었고, CI-10 해소 뒤 표지를 지워 loop declared 가 되었다.
- 파일럿 feedback 후보를 넣은 복사본 로드: {Cf1, Cf2} → loop declared, cuts (Cf1, Vip)·(Cf2, Vim), weights (Vim −½, Vip +½);
  {Cf1, Cf2, Cs1, Cs2} → 같은 절단 넷·가중, cuts 4개; `[]` → loop unity, 차동 출력 sense (Vop, Vom).
- 새 규칙 거부(복사본 한 곳씩): `feedback_element_not_on_input`(파일럿 feedback CL1), `feedback_cut_ambiguous`(파일럿에
  Vip–Vim 커패시터 추가), `view_excite_not_allowed`·`view_sense_fixed_net`(pushpull rout 에 ac_excite / sense_p = 입력 vin),
  `view_shape_not_supported`·`view_not_applicable`(nmcnr pm 에 cut_weights / 감지 모양 view) -- 전부 그 규칙 하나만 냈다.

[CM 2026-10-08] 공통 모드 루프 제약: 파일럿에 `pm_cm_ss_deg >= 60`(source user_spec, decided 2026-10-08, 사용자 "6번도 네 의견에 동의하고 제안한 값을 사용해") 한 건을 더했다(제약 8(5) → 9(6), view 는
적지 않음; pending 표지 수 11·총 61 은 그대로 -- 이 계약 표가 정본). library 9회로에 `default_views().cm_loop` 를 전수 실행: 파일럿만 `cm_output`(가중 ((Vom, 1/2), (Vop, 1/2))), 나머지 8회로는 차동 출력쌍이
없어 view_required 사유. 그 8회로 중 하나에 이 제약을 적으면 `view_required`. 픽스처 이름표 갱신 대상: `pm_cm_ss_deg`(deg, ss, cm_loop) 추가(레지스트리 이름 11개). 옛 평균 수동소자 감지 넷 구조 규칙은 삭제.. 구동자/소비자 구조 분류(`cm_partition`)와 선언 `cm_sense_elements` 는 3절 `cm_loop` 항 참조 -- 파일럿은 분류가 명확해 선언이 필요 없다.

theta_bounds 측정(2026-10-08, 이 커밋 코드 + library): 6회로에 상자 기입(current_reuse Cc1·Cc2·R1·R2, ngcc·nmcnr Cm1·Cm2,
sf_pushpull Cc·R1a·R1b·R1c, two_stage_ota·two_stage_ota_sf Cc) -- 9/9 로드 통과, 표지 수 불변(상자는 표지를 받지 않는다).
거부 실측(sf_pushpull 복사본 한 곳씩, 16건 전부 거부·그 규칙 하나만): 객체 아님·칸 객체 아님·0·음수·문자열·bool → `type`,
min ≥ max·min = max → `theta_bound_range`, max 없음 → `missing_key`, 칸 키 `unit` → `unknown_key`, 출처 없음 → `source_missing`,
출처 reference → `source_kind_not_allowed_here`, paper → `paper_source_not_adopted`, 모르는 이름·고정 값 `CL`·MOS `M1` →
`theta_bound_element`(gate `theta_bounds`). 지문: 출처 record 만 바꾸면 section_fps 불변, min 만 바꾸면 `search_fp` 만 바뀐다.

## 6. 설계(design_spec_format)와 다르게 정한 점

1. `schema_version` 은 문자열 `"5"`(topology `"2.0"` 과 같은 관례 + 구조 규칙 D: 숫자 리터럴 5 금지).
2. 파일: `legacy_names.py` 대신 공용 helper `_spec_fields.py`(표 + key_hits·value_slot 등). `spec_meta.py`·
   `spec_input_dc.py`·`spec_targets.py`·`spec_node_targets.py`·`spec_regions.py` 를 따로 두었다(규칙 A 진입점 1개).
3. 옛 이름 표에서 library 이름과 글자가 같은 `CL`·`vdd`·`Voc_des` 는 뺐다(구조 규칙 E) -- `unknown_key` 로 거부된다.
4. 쓰는 spec 이 없는 선택 키 `same_as`·`cross_kind_matching`·`search.L_candidates`
   와 참조 `value_from_spec` 은 만들지 않았다(배선 원칙) -- 지금은 `unknown_key`/`legacy_name` 으로 거부되고, 쓰는 spec 이
   생길 때 그 행과 함께 만든다. [U5 2026-10-08] `driving_spec`·`gain_budget_db_override` 는 설계 40 §3.1(R10 복원)에 따라 만들었고
   `structure_count_budget` 도 더했다(1절).
5. 새 규칙: `ref_kind_mismatch`, `ref_ambiguous`, `ref_file_rejected`(설계 `ref_file_topology_fp` 를 포함), `view_not_applicable`,
   `element_value_conflict`(F5 이관 전 안전망), `settling_order`, `source_origin`.
6. `numeric_in_rule_field` 는 `spec_schema` 가 아니라 `spec_settings` 가 낸다(규칙 칸을 읽는 곳).
7. 결정 대기 ID 에 `ET-n`·`MODn` 을 더했다(`MOD5` = 레지스트리 이름·뷰 정의를 MOD5 design 이 정할 칸).
8. 섹션 지문에 `operating_fp`·`feedback_fp` 를 더했다(설계 목록에 자리가 없던 input_dc·노드 목표·영역·feedback).
9. `MetricSignature.view_kind` 어휘는 MOD5 레지스트리와 같은 None/transfer/loop/cm_loop/output_port/ratio([CM] `cm_loop` 추가, 4절, 정본
   `core.metric_signature.VIEW_KINDS`). `pm_ss_deg` = loop(view 미기재 → `feedback`·ports 유도 뷰, 결정 대기 아닌 선언 view
   거부), `rout_ss_ohm` = output_port(감지 전용 `{sense_p, sense_n?, sense_mode}`, 미기재 → 단일 출력 포트). 정의는 7a design
   (`_drafts/engine/design_7a_loop_output_views.md` 2.9·3.1).
12. 7a 의 transfer 기본 포트 뷰도 같은 유도(`default_views`)를 쓴다: 입력 포트 모양(차동쌍 1개·단일 1개) 검사가 더해지고
    차동 출력쌍(role differential_output_p·_n)을 받으며, `ViewDecl("port")` 에 가중·관측이 담긴다(7a design 4.2 view_required
    수정 -- β = 1 루프와 같은 MnaSystem 이라 같은 유도를 쓴다).
13. role 어휘(`ports.ROLE_*` 다섯 개)는 유도가 읽는 값으로만 정했다 -- 포트 로드는 여전히 role 형식만 본다.
14. gate 전용 미구동 넷 판정은 graph `static_ac_ground` 와 같은 정의를 authoring(`spec_views`)이 TopologyDoc 에서 따로 한다
    (authoring 은 graph 보다 아래 층이라 import 할 수 없다) -- MOD10 배선 때 한 곳으로 줄일 대상(6절 11번과 같은 처리).
10. optional_stages 화이트리스트 이름(DEC-75 네 기능)은 이 파일이 snake_case 로 정했다.
11. graph(MOD3, master 병합분)에 `graph/supplies.py` `supplies_declaration`(supplies_v 인자 검사)이 따로 있다 -- 이
    파일의 `spec_supplies.supplies_declaration` 과 같은 개념의 두 검사다. MOD10 배선 때 graph 쪽이 `SizingSpecDoc.supplies_v`
    를 받도록 하나로 줄일 대상(이 커밋은 손대지 않음).

## 7. 열린 항목

| # | 항목 | 현재 처리 |
|---|---|---|
| S1 | loop(`pm_ss_deg`)·output_port(`rout_ss_ohm`) metric 의 선언 view 모양 | **닫음**(2026-10-07) -- 7a design: loop 는 유도만(2절·3절), output_port 는 감지 전용, `view_not_defined_yet` 삭제 |

| S3 | [CM 2026-10-08: 공통 모드 루프는 별도 metric `pm_cm_ss_deg`(view_kind `cm_loop`) 의 구조 유도로 닫음 -- 아래 명시 모양은 여전히 예약] 명시 loop view `{"cut_weights": {<절단 넷>: 가중}}`(β 루프) / `{<입력 포트 넷>: 가중}`(β = 1) -- 공통 모드 루프 같은 다른 모드 선택(7a design 2.9) | 계약에만 정의, 로더는 `view_shape_not_supported` 로 거부(배선 원칙: 첫 소비 spec -- 예: 7a Q2 에서 CM 루프 판정이 정해지면 -- 과 함께 구현). 키 집합 = 유도 절단 넷 집합(β = 1 은 입력 포트 집합), 0 아닌 유한 가중, 관측·절단 위치는 바꾸지 못한다 |
| S2 | **닫음(U5 2026-10-08)**: 옛 `mismatch_sigma_mv`·`mirror_ratio_error_mv`·`mismatch_sigma_v` 는 옛 이름 표로 거부하고 library 3 spec 은 새 이름·값으로 바꿨다(offset_in_sigma_mv 등 11개는 `metric_catalog()` 의 계산 대기 서명). 아래는 닫기 전 기록: `mismatch_sigma_mv`·`mirror_ratio_error_mv` 가 MOD5 레지스트리(`metrics.metric_catalog()`)에 없다 -- library spec(파일럿·two_stage_ota·two_stage_ota_sf)과 픽스처 이름표에만 있다 | 실제 레지스트리 이름표로 로드하면 `metric_unknown`. 레지스트리 등록(정합 metric 계산 위치 포함) 또는 spec 쪽 결정 대기 표지 전환을 MOD10 배선 전에 정한다 |

**내부 루프 뷰 선언 [U1b-jrules]**: loop metric(`pm_ss_deg` 등)의 제약 view `{"loop_cut": [<끊는 넷>, ...]}` -- 비지 않은 서로 다른 넷 이름 list(위반 `type`), 넷은 topology 단자에 있어야 한다(`view_net_unknown`), 닫힌 어휘라 다른 키 동반은 `unknown_key`(`cut_weights` 와 같이 적어도 `unknown_key`). 결과 `ViewDecl(mode loop, beta None, cuts=(("", 넷), ...) 넷순)`. 41 §1.8 안정도 선언이며 단계 A 가 `declared_loop_cuts` 로 모아 엔진 루프 뷰의 끊는 gate 넷과 대조한다(`undeclared_loop_constraint` 해제 / `loop_cut_unmatched`). feedback 에서 유도된 β 루프(`beta == declared`)는 그대로 대조 밖이다.

