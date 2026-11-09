# 회로 사이징 spec 파일 형식과 로더 계약 (design_spec_format) -- 2026-10-07

- 성격: 설계 문서(코드 없음). 저장소 `chip-design-skills`는 읽기만 했다(HEAD 524b375). spec 파일을 만들지 않았다 -- 2절 초안은 표다.
- 근거 약어: **P** = 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(N3.8·N3.10·N3.14·N3.15·N3.16, DEC-20·26·34·60·62·68·69·72~80·86, U-11·13·17·25·26·29·31·35·36·44~48). **UD** = `_drafts/user_decisions.md` 2026-10-07. **PUD** = `_drafts/engine/PENDING_USER_DECISIONS.md`(SP·AC·CI·PA ID). **DP** = `_drafts/engine/decision_package_specs.md`. **TQ** = `_drafts/engine/TOPOLOGY_CORRECTION_QUEUE.md`. **M3** = `design_mod3_s1_graph.md`, **M15** = `design_mod1_lut_mod5_mna.md`. **AC2** = `gmid_engine/authoring/CONTRACT.md`. **T** = library `<회로>.topology.json`(2026-10-07 실측 덤프). **H** = `legacy/workspaces/run_harness.py`.
- 상위 원칙(이 문서가 따르는 것):
  1. **값마다 출처**(U-35, WP-04): 논문·도면 값은 사용자 채택 기록이 있을 때만 값이 되고, 그때도 출처 종류는 `user_spec`(채택)이며 원래 출처는 `origin`으로만 남는다. 채택 기록 없는 논문 값은 spec에 들어오지 않는다.
  2. **상수 금지**(WP-03, UD "상수는 배제하고 PDK로"): SPICE 판정·재필터 설정에는 숫자를 두지 않고 규칙 이름(닫힌 어휘)만 둔다. 숫자가 오면 로드 거부.
  3. **topology 종속 엔진 금지**(사용자 대원칙 2026-10-07, DEC-62): spec에 회로별 보상 함수 이름(`compensation.function: miller_ota_topology` 등)·회로 전용 파라미터 키(`kg`, `Z`, `NDP`, `f_slew`, `stage_devices` …)를 두지 않는다. 보상·제약은 **metric 레지스트리의 일반 metric**과 **S1 구조 유도 결과**로만 표현한다. 소자·넷·요소 이름은 키 어휘가 아니라 topology 원소를 가리키는 **값(또는 맵 키)**으로만 나타나고, 로더가 topology에 실재하는지 교차 검사한다. 로더 코드에 회로 이름 분기·회로 이름 리터럴이 없다.
  4. **없음과 미정의 구분**(WP-02, CI-12와 같은 원칙): 필수 키가 없으면 거부, 빈 값(`[]`·`{}`)은 '없음'의 명시 선언, 아직 사용자 결정이 없는 값은 `pending` 표지(결정 ID 필수)로 적는다. 기본값으로 조용히 채우지 않는다.
  5. **graph가 유일 정본**(UD 상태 구조 확정): 구조에서 유도되는 것(stage 구성, 기둥, 공유 gm_id, kvl 묶음, 예산 기준 소자)은 spec에 쓰지 않는다.
- **[2026-10-07 개정 -- reference 검토 Q3·Q5·Q8·Q9·Q11 추천안 확정("B는 추천대로 해.")과 MetricSignature 어휘 통일("A는 기본안으로 승인할께.")]** 계획 worktree `plan-rev4` 커밋 `defdc24`(DEC-53·88·90·93·94·96). 바뀐 것: (1) `saturation_rule`은 `vds_ge_vdsat` 확정(엔진 봉인 7이 +tol_VDsat로 더 보수, DEC-88) (2) 오라클이 못 재는 선언 제약은 `spice_unverifiable[]`로 로드 결과에 미리 낸다(DEC-90) (3) box 허용 비 등 레이아웃 기준 항목을 spec에 두지 않는다(Q8 (vi) (나), DEC-93) (4) 파일럿 CL1·CL2 각각 1 pF 확정(SP-10 해소, DEC-94) (5) 잡음·왜곡 metric은 레지스트리에 없어 선언되면 `metric_unknown`(9회로 스펙 없음, DEC-96) (6) `MetricSignature` 어휘(3.2). 아래 [개정 Q*] 표시.

---

## 1. 형식

### 1.1 위치·이름

- **회로마다 파일 하나**: `skills/analog-gmid-design/assets/library/<topology_name>.sizing_spec.json` (P N3.15 이름). topology 파일과 **같은 디렉터리, 다른 파일** -- 이름 stem으로 짝을 짓는다(`<name>.topology.json` ↔ `<name>.sizing_spec.json`). 짝 짓기는 파일 이름으로만 하고, 내용 검사는 `meta.circuit` = topology `topology_name`, `meta.topology_fp` = `TopologyDoc.connectivity_fp`로 한다.
- topology 파일은 connectivity(사용자 작성)만, spec 파일은 사람 선언 스펙만 담는다. 새 로더는 topology의 sizing 관련 필드(`sizing_roles`·`compensation`·`_declared_target_spec`)를 읽지 않는다(DEC-26, AC2 '태그 키는 읽지 않는다').
- 측정 산출값(모델 오차, DEC-72)은 사람 선언 파일에 쓰지 않는다 -- 별도 파일 `<name>.model_error.json`(형식 결정 F7). 이유: 엔진·오라클이 spec 파일을 고쳐 쓰면 spec 지문(S0)이 측정 때마다 바뀌어 사람이 바꾸지 않은 입력 때문에 캐시가 무효화되고, '사람 선언'과 '측정값'의 writer가 한 파일에 섞인다(필드마다 writer 1개 원칙).
- `_TEMPLATE.sizing_spec.json`은 만들지 않는다(쓰는 곳 없는 파일 -- 배선 원칙). 스키마 정본은 로더 CONTRACT.md(4절)다.

### 1.2 최상위 구조

```json
{
  "meta":  { ... },
  "human": { ... },
  "_<필드>_comment": "주석(어떤 코드도 읽지 않음, DEC-68)"
}
```

P N3.15의 `derived` 섹션은 두지 않는다(형식 결정 F7): 구조 유도 필드(stage 구성·`vertical_stack_id`·`vsb`·`vds_kvl_groups`·`compensation.stage_devices`·`budget_reference_device` …)는 S1/S2 graph 필드가 정본이고(UD 상태 구조 확정), `model_error_<metric>`은 1.1의 별도 파일이다.

### 1.3 `meta`

| 필드 | 형식 | 검사 |
|---|---|---|
| `schema_version` | 정수(값은 F13) | 로더 상수와 같아야 함 |
| `circuit` | 문자열 | = `TopologyDoc.name`, = 파일 stem |
| `topology_fp` | 64자 hex | = `TopologyDoc.connectivity_fp`(파일 sha256이 아님 -- 주석만 바꿔도 spec이 깨지지 않게, M3 5.1과 같은 기준). 불일치는 거부(P N3.15 `topology_hash`) |
| `origin` | `canonical` / `fixture` | 닫힌 어휘(P N3.15) |

### 1.4 출처 객체 `source` (모든 선언에 필수)

모든 '선언'(값 하나 또는 한 결정으로 함께 정해진 값 묶음 하나)은 `source` 객체를 가진다.

```json
"source": {
  "kind": "user_spec",
  "record": "UD 2026-10-07 항목 3 (\"5번 빼고, 1~7은 기본안대로 해.\")",
  "decided": "2026-10-07",
  "origin": "paper",
  "citation": "Xie & Chen, III.A (t_slew 10 ns / t_lln 30 ns)"
}
```

| `kind` | 뜻 | 필수 부필드 | 허용되는 섹션 | 판정에 쓰이나 |
|---|---|---|---|---|
| `user_spec` | 사용자가 정한 값(논문·도면 값을 사용자가 채택한 경우 포함) | `record`(사용자 결정 기록 위치·원문), `decided`(날짜). `origin`이 `paper`·`drawing`·`lecture`이면 `citation` 필수 | 전부 | 예 |
| `pending_spice` (U-35 `pending_7a`의 새 이름, F2) | 값은 있으나 SPICE 대조에서 기준값을 다시 읽는다 | `record` | `constraints` | **아니오**(U-17: 구속하지 않는 상한, 로더가 `judged=false`로 표시) |
| `reference` | 다른 선언을 참조(DEC-20) | 값 대신 `value_from_constraint` / `value_from_spec` / `value_from_file`(F6) 중 하나 | `constraints`, `compensation_targets` | 참조 대상과 같음 |
| `plan_rule` (신설, F2) | 계획서 규칙이 정한 설정값(사용자 스펙이 아님) | `plan_id`(예 `DEC-34`) | **설정 섹션만**(`search`, `spice_check`, `front_refilter`) | 설정이라 판정 대상 아님 |

- **거부되는 kind**: 위 넷 밖 전부. 특히 `paper`·`paper_reference`·`literature`·`drawing`은 kind로 오면 규칙 `paper_source_not_adopted`로 거부한다(논문 값을 확정값으로 몰래 쓰는 길을 막는다. 채택된 논문 값은 `kind: user_spec` + `origin: paper` + `record`로만 들어온다). `origin` 어휘 = {`user`, `paper`, `drawing`, `lecture`, `legacy_harness`}.
- `plan_rule`은 성능 제약·요소 값·전원에 오면 거부(`source_kind_not_allowed_here`) -- 계획 기본값이 스펙 값으로 둔갑하지 않게.
- `pending` 표지(1.5)에는 `source` 대신 `pending`(결정 ID)만 쓴다.

### 1.5 미정 표지 `pending`

```json
"input_dc": { "pending": "SP-2" }
```

- 값 자리 어디서나 쓸 수 있다(필수 키를 '빠짐'이 아니라 '결정 대기'로 채운다). 결정 ID는 PUD ID 형식(`SP-n`·`AC-n`·`CI-n`·`PA-n`·`U-nn`) 정규식 검사.
- 로더는 통과시키고 `SizingSpecDoc.pending`(필드 경로, 결정 ID) 목록에 모은다. **사이징 실행(MOD10) 시작 전**에 그 실행이 읽는 필드에 `pending`이 하나라도 있으면 전부 모아 `SchemaRejectedError` 한 번(N3.14 '필수 선언 누락')으로 정지하고 결정 ID 목록을 낸다. 스펙이 필요 없는 합격 항목(T1~T4·T6·T8, P N1·U-44)은 `pending`이 있어도 돈다.
- 성능 제약은 `pending`을 쓰지 않는다: 값이 없는 metric은 **제약 목록에 넣지 않는다**(= 보고만, DF-1·U-29·U-44). 제약 목록 밖에 `pending_constraints[]{metric, decision}`로 '결정 대기 중인 제약'을 적어 보고서가 "보고만(결정 대기 SP-4)"과 "보고만(선언 안 함)"을 구분하게 한다.

### 1.6 `human` 섹션

모든 키는 닫힌 어휘다. 회로 이름·회로 전용 키가 들어올 자리가 없다. 맵 키로 쓰이는 이름(넷·요소·소자)은 topology 원소 참조이고 로더가 교차 검사한다.

| 키 | 형식 | 필수 | 교차 검사·규칙 | 근거 |
|---|---|---|---|---|
| `supplies_v` | `{"values": {<넷>: V}, "source": {...}}` | 예(9회로 전부 -- 4.1) | 넷 키 집합 = topology `supply_nets`(빠진 넷·남는 넷 둘 다 hit), 값은 유한 수, 최고 전위 레일은 하나(가장 높은 레일 유도 함수 하나, DEC-60) | DEC-60 (i), SP-1 |
| `input_dc` | `{"net": <레일 넷>}` / `{"value_v": V}` / `{"engine": true}` / `{"pending": id}` 중 하나 + `source` | 예 | `net`은 `supply_nets` 안, `value_v`는 레일 전압 범위 안 | P N3.16 `input_dc_net`, SP-2(G7-U2: `engine` = W4 자유 변수 후 '요구 입력 공통모드' 보고) |
| `element_values` | `{<요소 이름>: {<값 키>: 값} \| {"engine": true} \| {"pending": id}, + source}` | 예(topology 수동소자·이상원 **전부**, F4) | 이름 ∈ topology `passive_elements ∪ ideal_sources`, 누락·남는 이름 hit. 값 키는 요소 kind와 맞아야 함: capacitor→`value_farad`, resistor→`value_ohm`, current_source→`value_dc_amp`, voltage_source→`value_dc_v` | P N3.15·N3.16 '요소 값', DEC-79(수동소자 면적), U-31 |
| `feedback` | `{"elements": [<수동소자 이름>…], "source"}` | 예(빈 list = 되먹임 수동소자 없음 = β=1 루프) | 이름 ∈ topology `passive_elements` | U-48·N3.8 PM 정의(UD 9번), F12 |
| `constraints` | `[{metric, op, value \| value_from_*, view?, source}]` | 예(빈 list 허용) | 1.7 | U-35, DEC-20, N3.8 |
| `pending_constraints` | `[{metric, decision}]` | 아니오 | metric은 레지스트리 이름 | 1.5 |
| `compensation_targets` | `{gbw_target_hz?, pm_target_deg?, settling?}` 각 항목 `{value \| value_from_constraint, source}` | 아니오 | 부하 용량은 쓰지 않는다(요소 이름으로 `element_values` 참조). `settling` = `{total_s, linear_s}`(F11). **보상 함수 이름·회로 전용 인자 없음** -- GB5 일반 규칙(M15 3.5 `compensation.py`)이 S1v 극점 노드와 이 목표에서 보상 변수를 유도 | N3.15, DEC-70, 원칙 3 |
| `driving_spec` | `{slew_rate_*, load_peak_amp, load_dc_amp}` + source | 아니오 | 슬루율 필드 이름은 MOD5 레지스트리 단위표가 정한다(N3.15) | DEC-58 |
| `node_voltage_targets_v` | `{<넷>: {value_v, source}}` | 예(빈 맵 = W3 없음) | 넷 ∈ topology 넷, 레일 아님 | N3.4 W3, CI-15 |
| `intended_region` | `{<소자 이름>: {"region": "triode", source}}` | 예(빈 맵 = 전 소자 포화 검사) | 소자 ∈ topology devices | CI-18, AC-1 (ii) |
| `same_as` | `{<소자>: <소자>}` + source | 아니오 | 둘 다 topology devices, connectivity로 유도되는 것이면 거부(구조 유도 결과와 대조) | N3.15 |
| `cross_kind_matching` | 계획 N3.15 그대로 | 아니오 | 소자 실재 | N3.15 |
| `gain_budget_db_override` | `{value, source}` | 아니오 | source 필수 | N3.15 |
| `objective` | `{"budgets": {<목적 metric>: {op: "<=", value, source}}}` | 예(빈 `budgets` = 예산 미선언 → front 제시 후 정지) | 목적 metric은 레지스트리의 목적 축 이름만(`supply_current_dc`, 판정 축 면적 `area_layout_m2`). **최소화 대상 선언 키(`minimize`) 없음** -- 축은 (전력, 면적)으로 고정(DEC-77) | DEC-77~80, U-13, PA-1 |
| `search` | `{wall_clock_budget_s, front_budget_s, search_method, optional_stages, dof_rank_sample_count, L_candidates?}` 각 항목 source | 예 | `search_method` ∈ {`default`, `precision`}, `optional_stages` 키 ∈ DEC-75 화이트리스트 4개, `L_candidates`는 LUT L 앵커의 부분집합(LR3, 검사는 MOD1 로드 뒤 -- 4.3) | DEC-34·73·75, U-26(c), PA-2 |
| `spice_check` | `{acceptance_rule, saturation_rule, node_compare_rule, device_compare_rule, forced_warn_rule, front_points_rule}` 각 항목 `{rule, source}` | 예 | `rule`은 닫힌 어휘(아래), **숫자 값이 오면 `numeric_in_rule_field`로 거부** | UD 8번, AC-1, AC-3/U-45, F8 |
| `front_refilter` | `{axis_rule, tie_rule, cycle_cap_rule}` 각 `{rule, source}` | 예 | 닫힌 어휘, 숫자 거부. **끄는 키 없음**(범위 안 기능이라 DEC-75 화이트리스트 밖 -- 끌 수 있게 만들면 skip 분기) | UD 12번 (나), DEC-79·80, N3.6 `K_max` |

`spice_check`·`front_refilter` 규칙 어휘(규칙의 정의는 엔진·오라클 코드 한 곳에 있고, spec은 이름만 고른다):

| 필드 | 어휘(초기) | 뜻 |
|---|---|---|
| `acceptance_rule` | `free_spec_and_all_saturated` | free 모드에서 선언 제약 전부 만족 + 전 MOS 포화(UD 8번) |
| `saturation_rule` | `vds_ge_vdsat` / `vds_ge_vdsat_plus_tol_v` | 포화 판정. 여유를 두려면 숫자가 아니라 tol_V(LUT LOO에서 계산) 규칙으로만. **[개정 Q3·Q5]** 9회로 값 = `vds_ge_vdsat`(확정). 꺼진 소자 FAIL(엔진이 전도로 예측한 MOS가 `off_current_A` 미만, DEC-90 (1))은 이 규칙의 일부이고 따로 고르는 키가 없다 |
| `node_compare_rule` | `record_only` | 노드전압 차는 기록(UD 8번) |
| `device_compare_rule` | `record_only` | 소자 ID/gm/gds 차 기록, 성능 차는 모델 오차로 제약 여유에(DEC-72) |
| `forced_warn_rule` | `forced_device_diff_gt_lut_tolerance` | 경고는 forced 모드에서 소자 차 > LUT 계산 허용오차일 때만(UD 8번) |
| `front_points_rule` | `endpoints_and_budget_point` / `all_front_points` / `budget_point_only` | AC-3/U-45 |
| `axis_rule` | `layout_floorplan_outline` | 판정 축 = MOD7 floorplan 외곽 면적(UD 12번) |
| `tie_rule` | `manufacturing_grid_cell_area` | 동률 = PDK `MANUFACTURINGGRID` 한 칸 면적(UD 12번) |
| `cycle_cap_rule` | `k_max_n3_6` | 재필터·MOD8 교대 상한 = N3.6 `K_max` 규칙(DEC-79) |

### 1.7 제약 항목

```json
{ "metric": "gain_ss_db", "op": ">=", "value": 57,
  "source": { "kind": "user_spec", "record": "T two_stage_ota 309 / U-35 기입", "decided": "2026-09-17" } }

{ "metric": "parasitic_pm_ss_deg", "op": ">=",
  "value_from_constraint": "pm_ss_deg",
  "source": { "kind": "reference" } }

{ "metric": "ratio_ss_db", "op": ">=", "value": 60,
  "view": { "num": {"ac_excite": {...}, "sense_p": "...", "sense_n": "...", "sense_mode": "..."},
            "den": {...} },
  "source": { ... } }
```

- `metric`: **metric 레지스트리에 등록된 이름만**(M15 3.4: `gain_ss_db`, `ratio_ss_db`, `ugf_ss_hz`, `gbw_ss_hz`, `parasitic_pm_ss_deg`, `rout_ss_ohm`, … + N3.8 `pm_ss_deg`). 미등록이면 `metric_unknown`. 회로 이름이 붙은 metric(옛 `_metric_folded_cascode_gain_db` 계열)은 레지스트리에 없으므로 자동 거부된다.
- `op` ∈ {`>=`, `<=`}. `value`(유한 수) 하나 또는 `value_from_constraint` / `value_from_spec` / `value_from_file` 중 하나(둘 이상·둘 다 없음은 거부). 참조는 로드 때 해석하고 순환이면 거부.
- 단위는 metric 이름의 접미사가 정한다(DEC-68). 단위 환산 키는 두지 않는다.
- `view`: 그 metric 레지스트리 항목이 뷰를 요구할 때만(필요 뷰 종류는 레지스트리 항목의 속성). 없으면 **포트 뷰**(topology `ports`의 입력 role → 출력 role)를 쓰되, 포트 뷰가 하나로 정해지지 않으면(예: 차동 출력 두 넷인데 `sense_mode` 미선언) 로더가 `view_required`로 거부한다. 뷰 안 넷 이름은 topology 넷 실재 검사.
- 같은 (metric, op, view)가 두 번 나오면 거부(`constraint_duplicate`).
- `pending_spice` 제약은 로드되지만 `judged=false`(U-17).

### 1.8 옛 이름·회로 전용 키 거부 목록 (로더의 첫 소비자 = 옛 이름 표)

AC2 5절 6은 "옛 이름 거부 훅은 쓰는 곳이 생길 때 행과 함께 만든다"고 적었다 -- spec 로더가 그 첫 소비자다. 표 행은 둘이다.

- **(a) N3.16 '흡수되는 옛 이름'**: `supplies`, 스칼라 `vdd`, `value_amp`, `PM_target_deg`, `PM`, `GBW`, `GBW_hz`, `CL`, `CL_farad`, `IBias_amp`, `same_as_device`, `node_voltage_targets`, `Voc_des`, `input_dc_v`(문자열), `input_common_mode`, `pm_deg`, `gain_db`, `dc_gain_db`, `rout_ohm`, `parasitic_pm_deg`, `mismatch_sigma_mV`, `mirror_ratio_error_mV`, `power_uA` … -- **키와 문자열 값 둘 다** 검사한다(`value_from_spec: "PM_target_deg"` 같은 값 안 이름, N3.16 끝 문단).
- **(b) 회로 전용 키(대원칙 2026-10-07)**: `compensation`, `function`, `parameters`, `stage_devices`, `shared_gm_id_groups`, `vds_kvl_groups`, `kg`, `Z`, `NDP`, `f_slew`, `t_lln`, `t_settle_total`, `omega_c`, `stack_groups_override`, `row_split`, `stage_gain_min`, `stage_objective`, `stage_power_tolerance`, `min_vds_by_role`, `vth0_slope`, `W_bounds`, `L_min`, `min_finger_w`, `max_finger_w`, `report_only`, `minimize`. (b)는 1.6의 닫힌 키 어휘 밖이므로 `unknown_key`로도 걸리지만, 이관 실수를 바로 알리게 규칙 `circuit_specific_key`로 따로 낸다.

---

## 2. 9회로 초안 (현재 확정 값, 파일로 만들지 않음)

표기: **값** + 출처 kind(줄임: US = `user_spec`, PS = `pending_spice`, REF = `reference`, PR = `plan_rule`). 미정 칸 = '미정(사용자 결정 대기: ID)'. '확인' = 값의 근거는 있으나 사용자 확정 기록을 찾지 못한 칸(값을 정하지 않았다 -- 확인만 받으면 된다).

### 2.0 9회로 공통 칸 (회로별 표에서 생략)

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `objective.budgets` | 미정(사용자 결정 대기: PA-1) -- 기본안 `{}`(front 제시 후 정지). nmcnr 논문 전력 400 µW·면적 0.18 mm²는 채택 기록 없음 → 넣지 않음 | -- |
| `search.wall_clock_budget_s` | 300 | PR `DEC-34`·U-26(c) 기본안(회로별 변경은 PA-2) |
| `search.front_budget_s` | 미정(사용자 결정 대기: PA-2) | -- |
| `search.search_method` | `default` | PR `DEC-73` |
| `search.optional_stages` | `{}` | PR `DEC-75`(기본 비활성) |
| `search.dof_rank_sample_count` | 10 | PR `N3.7` |
| `spice_check.acceptance_rule` | `free_spec_and_all_saturated` | US UD 2026-10-07 "8번 수정안으로 확정해" |
| `spice_check.saturation_rule` | `vds_ge_vdsat` -- 8번 문언 "전 MOS 포화"를 여유 없는 포화로 읽은 것 | US UD 8번 + **[개정 Q3 (ii)] 확정**(2026-10-07 "B는 추천대로 해.": 오라클은 여유 0 그대로, 엔진 봉인 7이 +tol_VDsat로 보수) |
| `spice_check.node_compare_rule` / `device_compare_rule` / `forced_warn_rule` | `record_only` / `record_only` / `forced_device_diff_gt_lut_tolerance` | US UD 8번 |
| `spice_check.front_points_rule` | 미정(사용자 결정 대기: AC-3·U-45) -- 기본안 `endpoints_and_budget_point` | -- |
| `front_refilter.*` | `layout_floorplan_outline` / `manufacturing_grid_cell_area` / `k_max_n3_6` | US UD 2026-10-07 "12번은 (나)로 해." |
| `node_voltage_targets_v` | 미정(사용자 결정 대기: CI-15) -- 기본안 `{}`(선언된 것만 W3) | -- |
| `intended_region` | 미정(사용자 결정 대기: CI-18) -- 기본안 `{}`(전 소자 포화 검사) | -- |
| 모델 오차 파일 | 측정 전(파일 없음) -- 소비 판정은 '판정 보류'(DEC-72) | -- |

### 2.1 two_stage_ota

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, gnd 0} | US UD 2026-10-07 "1~7은 기본안대로" 항목 1 |
| `input_dc` | 미정(사용자 결정 대기: SP-2) | -- |
| `element_values` | Rz `engine`, Cc `engine`, CL `value_farad 3e-12` | Rz·Cc: US TQ Q4·Q4'("값은 엔진 계산"); CL: US UD "3pF으로 확정해"(TQ Q4', U-31). **전제: TQ Q4' 반영(현재 topology에 `passive_elements` 키 없음)** |
| `feedback.elements` | `[]`(β=1) | 기본안 -- 되먹임 수동소자 없음(Cc는 보상 소자). 확인: CI-19 |
| `constraints` | `gain_ss_db >= 57` | US(T 309, U-35 기입, 옛 이름 `gain_db`) |
|  | `mismatch_sigma_mv <= 5.0` | PS(U-17) |
| `pending_constraints` | `pm_ss_deg`(SP-3), `gbw_ss_hz` 제약 승격(SP-5·U-44) | -- |
| `compensation_targets` | `gbw_target_hz 7e6` | US 세션31(2026-08-13) GBW 무릎점 결정(H 105-113 주석) |
|  | `pm_target_deg` 미정(사용자 결정 대기: SP-3) -- 옛 설계 의도 ≈70°는 기록 아님 | -- |
| 이관 안 함 | `Z 10`·`NDP 4`(typical, 회로 전용 인자) → GB5 일반 규칙; `stage_gain_min`·`stage_objective`·`stack_groups_override`·`row_split` → 구조 유도·DEC-77 | 원칙 3 |

### 2.2 current_reuse_telescopic_ota (파일럿)

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, gnd 0} | US UD 항목 1 |
| `input_dc` | 미정(사용자 결정 대기: SP-2) | -- |
| `element_values` | CL1·CL2 `1e-12` 각각 | US UD 항목 4(C_Ltot 1 pF 채택, origin paper Table I) + **[개정 Q9 (iv)] SP-10 해소**(사용자 2026-10-07 "파일럿 CL1·CL2가 각각 1 pF" -- 차동 출력 양쪽 각각, 합계 2 pF) |
|  | Cf1·Cf2·Cs1·Cs2 `5e-13` 각각 | US UD 항목 4(origin paper Table I) |
|  | Cc1·Cc2 `engine` | **확인**(H 195 주석 "500 fF는 폴백, Cc는 보상망이 유도" -- 확정 기록 없음) |
|  | Rz1·Rz2 `engine` | **확인**(옛 Rz=1/gm 규칙, M15 3.5 GB5 `ss.passive`) |
|  | R1·R2 | 미정(값·엔진 계산 여부 기록 없음 -- 새 결정 필요, ID 미배정) |
|  | Iref `value_dc_amp 1.2e-6` | US 2026-09-08(T 144). θ 공존 규칙은 CI-17 |
| `feedback.elements` | 미정(사용자 결정 대기: CI-10) -- 후보 Cf1·Cf2·Cs1·Cs2(AC-2 문언의 예) | -- |
| `constraints` | `gain_ss_db >= 54` | US 세션44(T 2031, U-19 재도출 가능) |
|  | `pm_ss_deg >= 70` | US UD 항목 2 "파일럿 PM 하한 70도". **[개정 MetricSignature]** view_kind = loop라 7a design의 루프 뷰 정의 전까지 `judged=false`(pending 전용) -- 마일스톤 1 PM 판정 전에 뷰 정의가 필요 |
|  | `ratio_ss_db >= 60`(CMRR 뷰), `ratio_ss_db >= 60`(PSRR 뷰) | US(옛 `cmrr_estimate_db`·`psrr_estimate_db`, U-35). **뷰 선언(num/den)은 MOD5 design이 옛 정의에서 옮김**. **[개정 Q5 (ii)]** SPICE 합격(T5) 판정 대상 -- 오라클이 같은 num/den 여기 정의로 .ac 2회(DEC-90 (2)) |
|  | `classab_centering_dev_v <= 0.15` | US(U-35). **metric 레지스트리 미등록**(M15 3.4) -- 일반 metric으로 등록되기 전에는 로더가 거부 |
|  | `mismatch_sigma_mv <= 5.0` | PS(U-17) |
|  | `mirror_ratio_error_mv <= value_from_constraint mismatch_sigma_mv` | REF |
|  | `parasitic_pm_ss_deg >= value_from_constraint pm_ss_deg` | REF(옛 `value_from_spec: PM_target_deg` → 제약 참조로) |
| `compensation_targets` | `pm_target_deg` = `value_from_constraint pm_ss_deg` | REF |
|  | `settling {total_s 4e-8, linear_s 3e-8}` | US UD 항목 3(origin paper III.A). **[개정 Q5 (ii)]** SPICE는 측정·기록만(합격 밖, DEC-90 (2)) -- F11 기본안과 같다 |
| 이관 안 함 | `compensation.function current_reuse_telescopic_topology`·`parameters`·`stage_devices`·`shared_gm_id_groups`·`vds_kvl_groups`, `f_slew`, `omega_c` 폴백 → GB5 일반 규칙·S1 유도 | 원칙 3 |

### 2.3 folded_cascode

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, gnd 0} | US UD 항목 1 |
| `input_dc` | 미정(사용자 결정 대기: SP-2) | -- |
| `element_values` | CL `1e-12` | US UD "CL 1pF를 넣어줘"(TQ Q5, U-31). **전제: TQ Q5 반영** |
|  | Ibg `engine` | **확인**(T 107: "theta 자유 탐색 -- 설계상 의도", 사용자 기록 없음; CI-17 규칙과 함께) |
| `feedback.elements` | `[]` | 기본안, 확인 CI-19 |
| `constraints` | `[]` | U-35(자기 역산값 삭제) |
| `pending_constraints` | `gain_ss_db`(SP-4), `gbw_ss_hz`(SP-5), `pm_ss_deg`(SP-3), CMRR·PSRR `ratio_ss_db`(SP-7) | -- |
| `compensation_targets` | 없음(SP-3·SP-5 결정 뒤) | -- |
| 비고 | M1·M2 kind nmos 정정(TQ Q1)이 `topology_fp`를 바꾼다 | -- |

### 2.4 nmcnr_amplifier

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 0.9, vss -0.9} | US 2026-09-15 "+-0.9로 고치고"(U-26(a), T.decl) |
| `input_dc` | 미정(사용자 결정 대기: SP-2) | -- |
| `element_values` | CL `1e-10` | US(T.decl, 논문 값 채택 origin paper; TQ Q3) |
|  | RL `value_ohm 25000` | US UD "25kOhm을 넣어."(TQ Q3''', origin paper 측정 조건) |
|  | Cm1·Cm2·Rm `engine` | US TQ Q3("값은 엔진 계산") |
| `feedback.elements` | `[]` | 기본안, 확인 CI-19(Cm1·Cm2는 보상 소자) |
| `constraints` | `gbw_ss_hz >= 816000` | US(T.decl, 논문 값 채택) |
|  | `pm_ss_deg >= 70` | US 세션37(논문 46° 기각) |
| `pending_constraints` | `gain_ss_db`(SP-4, 논문 >100 dB는 참고), 슬루·PSRR(SP-7) | -- |
| `compensation_targets` | `gbw_target_hz`·`pm_target_deg` = `value_from_constraint` | REF |
| 이관 안 함 | `compensation.function nmcnr_3stage_topology`·`kg`·`stage_devices` → GB5 일반 규칙. 논문 `_paper_target_spec` 값 전부(채택 기록 없는 것) | 원칙 1·3 |
| 비고 | **TQ Q3''' 반영 전에는 `passive_elements` 키가 없어 topology 로드가 거부(AC2 4절)** | -- |

### 2.5 ngcc_3stage_ff

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, gnd 0} | US 2026-09-16 "2는 1.8에 맞춰"(T.decl) |
| `input_dc` | 미정(사용자 결정 대기: SP-2) | -- |
| `element_values` | CL `1e-11` | US(T.decl, 논문 CL 채택 origin paper) |
|  | Cm1·Cm2 `engine` | **확인**(논문 Table 4 1.68/1.32 pF는 참고값, 채택 기록 없음 → 값으로 옮기지 않음) |
| `feedback.elements` | `[]` | 기본안, 확인 CI-19 |
| `constraints` | `gbw_ss_hz >= 1e7` | US(T.decl) |
|  | `pm_ss_deg >= 63.4` | US(T.decl) |
|  | 입력 범위 `>= 0.6 V` | US(T.decl `icmr_v`). **metric 레지스트리 이름 없음**(N3.8 '스윙·입력 범위' `ls` metric -- MOD5 design이 이름을 정해야 로드 가능) |
| `pending_constraints` | `gain_ss_db`(SP-4) | -- |
| `compensation_targets` | `gbw_target_hz`·`pm_target_deg` = `value_from_constraint` | REF |

### 2.6 pushpull_follower_buffer

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, vss 0, agnd 0.9} | US U-25 |
| `input_dc` | `{net: agnd}` | US U-25 |
| `element_values` | CL `1e-12` | US U-25(origin drawing) |
| `feedback.elements` | `[]` | 기본안(버퍼 단독, 루프 없음) |
| `constraints` | `rout_ss_ohm <= 1000` | US U-25(origin drawing) |
| 이관 안 함 | `objective: minimize power`(DEC-77로 축 고정), `report_only: buffer_bandwidth_hz`(제약 목록 밖 metric은 모두 보고 -- 별도 키 불필요) | DEC-77, DF-1 |

### 2.7 sf_pushpull_output_opamp

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, vss 0, agnd 0.9} | US U-25 |
| `input_dc` | `{net: agnd}` | US U-25 |
| `element_values` | IBias `value_dc_amp 5e-5` | US U-25(origin drawing) |
|  | CL `1e-12` | US U-25 |
|  | Cc `engine`, R1a·R1b·R1c `engine` | US U-25(`derived_not_declared`: "보상망이 계산", "사이징에서 유도(사용자 결정)") |
| `feedback.elements` | `[]` | 기본안, 확인 CI-19 |
| `constraints` | `gain_ss_db >= 65`, `gbw_ss_hz >= 6e7`, `rout_ss_ohm <= 1000` | US U-25(origin drawing) |
| `pending_constraints` | `pm_ss_deg`(SP-3) | -- |
| `compensation_targets` | `gbw_target_hz` = `value_from_constraint`; `pm_target_deg` 미정(사용자 결정 대기: SP-3) | -- |

### 2.8 two_stage_ota_sf

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, gnd 0} | US UD "two_stage_ota_sf도 1.8로 확정" |
| `input_dc` | 미정(사용자 결정 대기: SP-2) -- 상속 대상 정본도 미정 | -- |
| `element_values` | CL `3e-12`(vout) | US U-25 |
|  | Cc `engine` | **확인**(two_stage_ota의 Cc 규칙(TQ Q4)과 같은 처리로 옮김 -- 이 회로 결정 기록은 없음) |
| `feedback.elements` | `[]` | 기본안, 확인 CI-19 |
| `constraints` | `gain_ss_db >= value_from_file two_stage_ota#gain_ss_db`, 뷰 감지 노드 vout | REF(U-25 "참조로 상속", 감지 vout) |
|  | `mismatch_sigma_mv` 같은 참조 | REF → 대상이 PS이므로 판정 안 함 |
|  | `rout_ss_ohm <= 1000` | US U-25(origin lecture) |
| `pending_constraints` | `pm_ss_deg`(SP-3, 정본도 미정) | -- |
| `compensation_targets` | `gbw_target_hz` = `value_from_file two_stage_ota#gbw_target_hz` | REF |
| 이관 안 함 | `inherits.spec_fn`(옛 하네스 함수 이름) → 값 단위 파일 참조로 대체(F6) | 원칙 3 |

### 2.9 common_gate_amplifier

| 섹션.필드 | 값 | 출처 |
|---|---|---|
| `supplies_v` | {vdd 1.8, gnd 0} | US UD 항목 1 |
| `input_dc` | 미정(사용자 결정 대기: SP-2) | -- |
| `element_values` | `{}`(topology 수동소자 0) | -- |
| 부하 CL | 미정(사용자 결정 대기: SP-6 (c)) -- 정해지면 topology에 CL 요소 추가(connectivity, 사용자) + `element_values` | -- |
| `feedback.elements` | `[]` | 기본안(단일단) |
| `constraints` | `[]` | -- |
| `pending_constraints` | `gain_ss_db`(SP-4), `gbw_ss_hz`(SP-5) | -- |

### 2.10 집계

- 9회로 모두 `supplies_v` 확정 → **spec 파일 9개 모두 로드 가능**(DEC-60 (i)이 9회로 전부에 걸린다).
- 전제 정정: TQ Q1(folded 극성)·Q3'''(nmcnr)·Q4'(two_stage)·Q5(folded)가 반영돼야 해당 회로 `topology_fp`와 `element_values` 교차 검사가 맞는다(현재 library HEAD에는 미반영 -- 3회로 `passive_elements` 키 없음, 실측).
- 레지스트리 이름 공백 2건(로더가 거부할 것): 파일럿 `classab_centering_dev_v`, ngcc 입력 범위 metric. 사용자 결정이 아니라 MOD5 design 몫(일반 metric 정의).
- '확인' 칸 9건(값을 정하지 않음): ~~saturation_rule 해석~~(**확정** Q3 (ii)), ~~파일럿 CL1·CL2 해석~~(**확정** SP-10 해소)·Cc·Rz(**[개정 Q7]** 값 미선언 보상 수동소자는 엔진 θ 성분, Rz는 구조 규칙 R = 1/Σgm 기본 + θ 폴백 -- `engine` 표기 그대로 맞다, DEC-92), folded Ibg, ngcc Cm1·Cm2, two_stage_ota_sf Cc, feedback `[]` 8회로(CI-19와 함께). 파일럿 R1·R2는 기록이 없어 새 결정이 필요하다.

---

## 3. 로더 계약

### 3.1 위치 (계획 N3.10 정합)

- **MOD2 `authoring` 패키지 안 파일들**로 둔다(하위 하위 패키지를 만들지 않는다). 근거: N3.10 MOD2 책임 = "topology·회로 spec 로딩, 스키마·정본 이름·단위·참조·선언 순서·출처 게이트, 레일 선언"; N6.1 단위 2(로더·로드 게이트); NR 3절 `authoring/spec_load.py`; M3 1절 표('회로 spec 로드'를 MOD2 다음 단계로 남김); D-19(rail_declaration = MOD2). '파일 하나 = 한 개념'(규칙 A~D)이 분리를 이미 강제하므로 패키지를 더 나눌 이유가 없다.
- 파일(규칙 A: 독립 진입점 1개, `_module_map` 층은 기존 authoring 층 뒤에 이어 붙임):

| 파일 | 진입점 | 층(제안) |
|---|---|---|
| `spec_model.py` | (데이터 선언) `SizingSpecDoc`, `SpecSource`, `ConstraintDecl`, `ElementValueDecl`, `RuleChoice`, `PendingMark` | 0 |
| `legacy_names.py` | (데이터 선언) 1.8 (a)(b) 표 -- topology 쪽 옛 이름(TQ Q2) 검사도 같은 표를 쓴다 | 0 |
| `spec_sources.py` | `source_declaration_checks`(1.4: kind·부필드·섹션별 허용 kind·논문 거부) | 1 |
| `spec_schema.py` | `check_spec_schema`(닫힌 키 어휘, 1.8 거부, 형식·유한 수, `pending` ID 형식, 규칙 필드 숫자 거부) | 1 |
| `spec_supplies.py` | `supplies_declaration`(넷 키 = `RailDeclaration.nets`, 값, 최고 레일 유일) | 2 |
| `spec_elements.py` | `element_value_declaration`(전수·kind↔값 키·이름 실재, `feedback` 이름 실재) | 2 |
| `spec_constraints.py` | `constraint_declaration`(metric ∈ 카탈로그, op, 값/참조 배타, 뷰 실재·포트 뷰 모호성, 중복) | 2 |
| `spec_refs.py` | `resolve_spec_references`(`value_from_*` 해석, 파일 참조 로드·그 파일의 `topology_fp` 검사, 순환 거부) | 3 |
| `spec_settings.py` | `settings_declaration`(`search`·`spice_check`·`front_refilter`·`objective` -- 화이트리스트·닫힌 어휘) | 2 |
| `spec_load.py` | `load_sizing_spec` | 4 |

### 3.2 공개 진입점

`load_sizing_spec(path, topology, metric_catalog) -> SizingSpecDoc`

- `topology`: 이미 검증된 `TopologyDoc`(파일을 다시 읽지 않는다). **필수** -- 교차 검사를 끄는 `None` 경로를 두지 않는다(skip 금지).
- `metric_catalog`: `{metric 이름: MetricSignature(unit, domain, view_kind, objective_axis)}` 불변 매핑. **[개정 -- MetricSignature 어휘 통일, 사용자 2026-10-07 "A는 기본안으로 승인할께.", 계획 DEC-53·N3.16]** `unit` ∈ `core/units.METRIC_UNITS`(`mv` 추가), `domain` ∈ `core/units.DOMAINS` 하나(`METRIC_DOMAINS` 삭제), `view_kind` ∈ {None, transfer, loop, output_port, ratio}(MOD5 레지스트리 어휘, 상수 한 곳), `objective_axis` ∈ `OBJECTIVE_AXES`. `pm_ss_deg` = loop, `rout_ss_ohm` = output_port, `area_search_m2` domain = geom. `spec_constraints._view`는 None/loop/output_port를 처리한다. **loop·output_port 뷰 제약은 7a design의 뷰 정의 전까지 로드는 하되 `judged=false`(pending 전용)**. 레지스트리 항목의 `oracle_measure` 필드로 `SizingSpecDoc.spice_unverifiable[]`(오라클이 못 재는 선언 제약, **[개정 Q5]** DEC-90 (3))를 로드 때 만든다. **import 방향 문제의 해법**: MOD2는 MOD5(metric 레지스트리)를 import할 수 없다(N3.10 작은 번호 쪽으로만). 그래서 레지스트리 이름표를 **인자로 주입**한다 -- MOD10 파이프라인이 MOD5 레지스트리에서 만들어 넘긴다. `MetricSignature` 데이터 클래스는 두 쪽이 함께 쓰므로 `core`에 데이터 선언 모듈 하나(`core/metric_signature.py`)로 둔다. 레지스트리 정본은 MOD5 하나이고 core에는 이름표를 두지 않는다(개념 하나 저장 위치 하나). 필수 인자라 빈 카탈로그를 주면 모든 제약이 `metric_unknown`으로 거부된다(조용히 통과하지 않음). test는 픽스처 카탈로그를 쓰고, 실제 레지스트리 대조는 MOD10 배선에서 처음 돈다.
- 순서: `load_json_checked`(기존 MOD2, 엔진의 유일한 JSON 파서 -- BOM·중복 키·NaN 거부) → `check_spec_schema` → `source_declaration_checks` → meta 대조(`circuit`, `topology_fp`) → `supplies_declaration` → `element_value_declaration` → `constraint_declaration` → `settings_declaration` → `resolve_spec_references`.

### 3.3 위반 일괄 거부

- AC2 0절 형식 그대로: 위반을 전부 모아 `SchemaRejectedError` **한 번**(exit 7), `record.detail` = {`gate: "spec_load"`, `where: path`, `hits`(SchemaHit 전부, 개수로 자르지 않음), `rejected_gates`, `not_evaluated`}.
- `not_evaluated`(앞 단계 거부로 판정 입력이 없는 검사): `topology_cross_checks`(`topology_fp` 불일치 -- 다른 회로판에 대한 교차 검사는 의미가 없음), `references`(스키마 거부가 있으면 참조 해석 안 함), `constraints.metric_catalog`(제약 목록 형식 자체가 거부).
- 규칙 키(hit `rule`): `missing_key`, `unknown_key`, `legacy_name`, `circuit_specific_key`, `type`, `non_finite`, `schema_version`, `circuit_name_mismatch`, `topology_fp_mismatch`, `source_missing`, `source_kind_unknown`, `paper_source_not_adopted`, `source_kind_not_allowed_here`, `source_record_missing`, `citation_missing`, `pending_id_format`, `supplies_net_missing`, `supplies_net_extra`, `supplies_value`, `supplies_top_rail_ambiguous`, `element_unknown`, `element_undeclared`, `element_value_key`, `feedback_element_unknown`, `input_dc_net_not_rail`, `input_dc_out_of_rails`, `node_target_net`, `intended_region_device`, `metric_unknown`, `op_value`, `value_and_ref`, `view_required`, `view_net_unknown`, `constraint_duplicate`, `ref_unresolved`, `ref_cycle`, `ref_file_topology_fp`, `optional_stage_unknown`, `search_method`, `budget_metric_not_objective`, `rule_name_unknown`, `numeric_in_rule_field`.
- 각 규칙마다 '실제로 거부한다'를 먼저 보이는 거부 test(9회로 원본에서 한 곳씩 깨뜨린 변형 + 합성 입력). 9회로 원본은 0 hit(오거부 0)이어야 한다.

### 3.4 결과 `SizingSpecDoc`와 지문

- frozen dataclass(`require_immutable` 통과, `fp_of` 가능). 필드: `circuit`, `topology_fp`, `supplies_v`, `input_dc`, `element_values`, `feedback`, `constraints`(참조 해석된 값 + `judged` 표시), `pending_constraints`, `compensation_targets`, `driving_spec`, `node_voltage_targets_v`, `intended_region`, `objective`, `search`, `spice_check`, `front_refilter`, `pending`(필드 경로, 결정 ID), `spice_unverifiable`(**[개정 Q5]** 오라클 측정 없는 선언 제약 목록, DEC-90 (3)), `file_sha256`(출처 기록, 지문 밖).
- **지문 = 계산이 실제로 읽는 상태**(NFR-2, M3 5.1과 같은 기준): `_` 주석 키, `source.record`·`citation`·`decided` 문자열은 지문에 넣지 않는다(문구를 고쳐도 캐시가 살아 있다). `source.kind`는 넣는다(`pending_spice`는 판정 여부를 바꾼다). 참조는 **해석된 값**으로 넣는다(참조 대상 파일 값이 바뀌면 이 지문도 바뀐다).
- **섹션 지문**(필드가 곧 캐시 -- 바뀐 섹션의 소비자만 무효화): `supplies_fp`(S1 bulk 기본 규칙의 입력 -- M3 5.1 `supplies_v_fp`가 이것을 받는다), `elements_fp`, `constraints_fp`, `compensation_fp`, `objective_fp`, `search_fp`, `spice_check_fp`, `refilter_fp`, 그리고 전체 `spec_fp`(= 섹션 지문들의 정렬 지문). S0 지문(P N3.3)의 'spec 전체 해시'는 `spec_fp`다. SPICE 판정 규칙만 바꾸면 S1·S2는 다시 계산하지 않는다.
- 같은 경로를 두 번 부르면 두 번 읽는다(캐시 없음 -- graph 밖 memo는 LUT 하나뿐, AC2 1절과 같음). 실행당 1회 로드(NR 4절).

### 3.5 topology 교차 검사 요약

| spec 쪽 | topology 쪽(`TopologyDoc`) | 규칙 |
|---|---|---|
| `meta.circuit` / `meta.topology_fp` | `name` / `connectivity_fp` | 같아야 함 |
| `supplies_v` 넷 키 | `rails.nets`(`supply_nets`) | 집합 같음(DEC-60 (i)) |
| `input_dc.net` | `rails.nets` | 원소 |
| `element_values` 이름·kind | `passives ∪ sources` 이름·kind | 전수 일치 + kind↔값 키 |
| `feedback.elements` | `passives` | 원소 |
| 제약 `view` 넷, 포트 뷰 | `ports`, 전체 단자 넷 | 실재, 모호하면 거부 |
| `node_voltage_targets_v` 넷 | 단자 넷 − 레일 | 원소 |
| `intended_region`·`same_as` 소자 | `devices` | 원소 |
| 제약 `metric` | (주입) `metric_catalog` | 등록 이름 |

**[개정 Q9 (i)(iii), 계획 DEC-94]** topology 쪽 로드 게이트(이 spec 로더가 아니라 MOD2 topology 로더 몫, 같은 일괄 거부 형식): gate에만 붙는 외부 바이어스 넷은 `ports` 바이어스 입력 role로 선언해야 하고 미선언이면 `gate_only_undeclared`, 선언했는데 gate 전용이 아니면 거부. 선택 키 `source_manifest{figure, device_count, passive_count}`가 있으면 netlist 수와 대조. 6회로 선언은 topology 정정 대기열(TQ). follower body(two_stage_sf M8, pushpull M1~M4, sf M18~M22)는 사용자 답 대기(Q9 (ii)).

LUT 범위 교차(`L_candidates` ⊂ L 앵커, 레일 최대 전위 차 ≤ LUT VS 축)는 spec 로더가 하지 않는다 -- MOD1 축 밖 거부(LR3)가 정본이고, MOD10이 LUT 로드 뒤 한 번 대조해 같은 방식으로 일괄 거부한다(spec 로더가 LUT를 읽으면 실행당 1회 로드가 깨진다).

### 3.6 일반성(임의 topology) 보장

- 로더 코드에 회로·소자·넷 이름 리터럴 0(기존 AST 이름 리터럴 test 적용), 회로 이름 분기 0.
- 9회로가 같은 코드 경로를 지난다는 것을 보이는 test + **library 밖 합성 회로**(새 topology + spec 한 쌍)를 코드 변경 없이 로드하는 test -- DEC-62 "새 토폴로지 추가는 데이터만으로".
- 회로별 보상 함수·회로 전용 파라미터는 스키마에 자리가 없고(1.6 닫힌 어휘), 들어오면 `circuit_specific_key`로 거부된다(1.8 (b)).

---

## 4. `_declared_target_spec` 이관 계획

### 4.1 순서

0. **선행**: TQ Q1~Q5(현재 '대기')와 Q2 옛 이름 정리를 topology에 반영(사용자 "한꺼번에 반영" 지시 이미 있음, UD 140행). `topology_fp`가 여기서 확정되므로 spec 파일은 그 뒤에 쓴다(먼저 쓰면 9개 모두 `topology_fp_mismatch`). Q 반영 때 **수동소자·이상원의 값은 topology가 아니라 spec `element_values`로** 간다(N3.16 '요소 값' 정본 위치) -- TQ Q3'''의 CL 100 pF·RL 25 kΩ, Q4'의 CL 3 pF, Q5의 CL 1 pF는 topology에 요소(connectivity)만, 값은 spec에.
1. 로더(3절)와 거부 test를 먼저 만든다(거부가 실제로 발동하는지 먼저).
2. 9회로 spec 파일 작성: 2절 표 그대로, 출처 객체 포함. 출처 원천 = `_declared_target_spec`(5회로), `sizing_roles.constraints`(4회로), H `SPECS`(4회로), UD 2026-10-07. 미정 칸은 `pending`.
3. **대조표 산출**(검토용 기록, 커밋에 동봉): 옛 원천의 잎 필드마다 `→ spec 경로` 또는 `이관 안 함(사유 분류)` 한 줄. 잎이 하나라도 행이 없으면 이관 미완(누락 0 확인). 분류:

| 분류 | 대상(옛 필드) | 처리 |
|---|---|---|
| 값 이관 | `supplies_v`, `loading.CL_farad`, `ideal_source_values.IBias_amp`, `performance_targets.{gbw_hz, pm_deg, dc_gain_db, rout_ohm, icmr_v}`, `input_dc_net`, `sizing_roles.constraints`(출처 있는 것), H `GBW`·`CL`·`PM_target_deg`·`t_lln`·`t_settle_total`·`Cf`·`Cs`·`C_Ltot` | 정본 이름으로 개명(N3.16), 출처 객체 부착 |
| 이관 안 함 -- **엔진 GB5 일반 규칙으로 대체**(대원칙) | topology `compensation.function`(`miller_ota_topology`, `current_reuse_telescopic_topology`, `nmcnr_3stage_topology`), `compensation.parameters`, H `Z`·`NDP`·`kg`·`f_slew`·`omega_c` 폴백·`stage_gain_min`·`stage_objective`·`stage_power_tolerance` | 버림. GB5(`metrics/compensation.py`)가 S1v 극점 노드 + `compensation_targets`로 일반 계산 |
| 이관 안 함 -- **구조 유도로 대체** | `compensation.stage_devices`·`shared_gm_id_groups`·`vds_kvl_groups`, H `stack_groups_override`·`row_split`, `sizing_roles` 역할 태그 | S1/S2 graph 필드(U-50) |
| 이관 안 함 -- **PDK·LUT 선언으로 대체** | H `L_min`·`W_bounds`·`min_finger_w`·`max_finger_w`·`vth0_slope`·`L_candidates`·`VDS_candidates`·`gm_id_grid` | core PDK 선언(U-30), LUT 앵커(LR3) |
| 이관 안 함 -- **축 고정·규칙으로 대체** | `objective: minimize power(_uA)`, `report_only` | DEC-77(축 고정), DF-1(제약 밖은 보고) |
| 이관 안 함 -- **채택 기록 없는 문헌 값** | `_paper_target_spec` 전부(채택된 값은 이미 `_declared_target_spec`·UD에 있음), nmcnr 논문 gain·SR·PSRR·전력·면적, ngcc Table 4 | topology 문서 필드에 그대로 남음(아래 4.2) |
| 이관 안 함 -- **출처 없음** | 파일럿 R1·R2 값(없음) | 2.2 '미정' |

4. 9회로 `load_topology` + `load_sizing_spec` 통과(0 hit) 기록, 지문 기록.
5. topology 정리(4.2).

### 4.2 이관 뒤 topology 쪽 (기본안)

| topology 필드 | 기본안 | 근거 |
|---|---|---|
| `_declared_target_spec`(5회로) | **삭제**(spec 파일 작성 커밋과 같은 커밋) | 같은 값이 두 곳에 있으면 조용히 갈린다(two_stage_ota_sf 복붙 사고, `require_declared_spec_source` 교훈; 개념 하나 저장 위치 하나 DEC-68). 읽는 코드 0(`.py` grep 0건 실측)이라 삭제 영향 없음. 이력은 git과 spec `source.record`에 남는다 |
| `_paper_target_spec`(5회로) | **남김**(문서 전용) | 스펙이 아니라 회로 출처 문헌 기록이고 spec에 대응 칸이 없다(채택 안 된 값은 spec에 들어오지 않음) |
| two_stage_ota `_target_spec_comment` | 남김(문서) | 위와 같음 |
| `sizing_roles`(`constraints`·`objective`·`theta`·`metrics`), `compensation` 블록 | **남김** | 새 로더는 읽지 않지만(IGNORED_TAG_KEYS) 옛 엔진 기준선(`legacy/workspaces/run_harness.py`가 같은 library 파일을 읽음, 실측 430행)이 읽는다 -- 지우면 대조 기준선이 깨진다. 옛 엔진 퇴역(ET-2) 때 함께 삭제 |
| `passive_elements[].value_*`·`value_from_spec`, `ideal_sources[].value_amp` | **삭제하고 spec `element_values`로**(F5) -- 단 옛 엔진이 읽는 값(파일럿 Iref, `value_from_spec`)은 퇴역까지 남기는 안도 있음 | N3.16 '요소 값' 정본 위치 = spec. 남기면 AC2 지문(`connectivity_fp`에 값 포함)이 값 변경 때 바뀌어 spec의 `topology_fp`가 깨진다 → 남길 경우 AC2 투영에서 값을 빼야 한다(F5) |

---

## 5. 사용자 결정 필요 (형식만, 값 아님)

각 항목 기본안은 위 원칙에서 나온 것이다. 표시 없는 것은 기본안으로 진행해도 기준 변경이 아니다.

| ID | 결정 | 기본안 | 대안 |
|---|---|---|---|
| F1 | spec 파일 위치 | `assets/library/<name>.sizing_spec.json`(topology 옆, 별도 파일) | 별도 디렉터리 `assets/specs/` |
| F2 | 출처 kind 어휘 | `user_spec` / `pending_spice` / `reference` / `plan_rule`(설정 섹션 전용) 넷, 논문 채택은 `user_spec`+`origin: paper`+`record` 필수, kind `paper*`는 거부 | U-35 이름 `pending_7a` 유지(7a Phase가 새 로드맵에 없어 개명 제안) / `plan_rule` 없이 설정값도 `user_spec`만 |
| F3 | 미정 표기 | `{"pending": "<결정 ID>"}` 허용, 로드는 통과·사이징 실행 전 일괄 거부. 제약은 `pending` 대신 목록 생략 + `pending_constraints` | 미정이면 필드 생략(없음과 미정이 구분 안 됨) |
| F4 | 요소 값 전수 선언 | topology 수동소자·이상원 **전부** `element_values`에 (값 / `engine` / `pending`)으로 적어야 함, 누락 거부 | 생략 = `engine`(조용한 기본값) |
| F5 | 요소 값 정본 위치 | topology `value_*` 필드 삭제, spec만(로더가 topology 값 필드를 옛 위치로 거부). AC2 `connectivity_fp` 투영에서 값을 뺀다(MOD2 계약 정정) | 옛 엔진 퇴역까지 topology 값 유지 + 투영에서만 제외 |
| F6 | 회로 간 상속(two_stage_ota_sf) | 값 단위 파일 참조 `value_from_file: "<회로>#<경로>"`(로더 해석, 순환 거부, 대상 `topology_fp` 검사) | 파일 단위 `inherits` + `overrides` |
| F7 | `derived` 섹션 | 두지 않음: 구조 필드는 graph 정본, 모델 오차는 `<name>.model_error.json` 별도 파일(writer = 오라클) | 계획 N3.15대로 spec 안 `derived`(측정 때마다 spec 지문 변경) |
| F8 | SPICE 판정·재필터 설정 위치 | 회로 spec마다 규칙 이름 선택(지문에 포함, 숫자 금지) | library 공통 파일 하나(`_acceptance.json`) |
| F9 | `ports` 위치 | topology(현행·N3.16·AC2). 계획 N3.15 human `ports` 문구와 "direction 없음" 문구를 정정 | 계획 N3.15대로 spec으로 이동 |
| F10 | 입력 DC 필드 모양 | `input_dc` 하나(`net` / `value_v` / `engine` / `pending`) | N3.15 `input_dc_net` 유지 + `input_dc_v` 추가 |
| F11 | 정착 목표 필드 | `compensation_targets.settling{total_s, linear_s}` 신설(N3.15에 없음). SPICE 판정은 과도 metric이 레지스트리에 없어 **보상 목표로만** 쓰이고 합격 판정 대상이 아님을 보고에 명시. **[개정 Q5 (ii)]** 오라클은 슬루·정착을 측정해 기록만 한다(DEC-90) -- 합격 밖 유지 | 과도 metric(정착 시간)을 레지스트리·오라클(`.tran`)에 추가해 제약으로 |
| F12 | 되먹임 선언 | `feedback.elements` 필수 키, 빈 list = β=1 명시 | 키 없음 = β=1 |
| F13 | `schema_version` | 계획 N3.15 값 5 | 새 형식이므로 1 |
| F14 | 이관 뒤 topology | `_declared_target_spec` 삭제, `_paper_target_spec`·`sizing_roles`·`compensation` 유지(옛 기준선) | `_declared_target_spec`도 남김(두 곳 유지) |

형식 결정이 아니어서 여기서 묻지 않은 것: 2절의 '미정' 값(SP·AC·CI·PA, PUD에 이미 있음), '확인' 9건(값 확인만 -- 2.10), 파일럿 R1·R2 값(새 값 결정), metric 레지스트리 이름 공백 2건(MOD5 design 몫), `MetricSignature` core 배치(import 방향에서 나오는 구조라 기본안 확정).
