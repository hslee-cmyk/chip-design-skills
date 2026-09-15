# 스키마 정리 분석: 필드 중복 제거와 JSON 이름 통일

사용자 요청(원문): "필드중복을 제거하고 json 이름을 통일했으면 좋겠어. 예를 들면, supply_nets와 supplies와 같은 것들 말이야."

저장소는 수정하지 않았다. 아래 근거는 모두 grep이나 파일 읽기로 확인한 것이다. 확인하지 못한 것은 "미확인"으로 적었다.

## 0. 약어와 조사 방법

| 약어 | 경로 |
|---|---|
| `lib/X` | `skills/analog-gmid-design/assets/library/X.topology.json` |
| `SR` | `skills/analog-gmid-design/assets/sizing_recipe.py` (15,269줄) |
| `SD` | `skills/analog-gmid-design/assets/stick_diagram.py` (12,935줄) |
| `T2M` | `skills/analog-gmid-design/assets/topology_to_markdown.py` |
| `ACF` | `skills/analog-gmid-design/assets/audit_current_forced.py` |
| `TL` | `skills/analog-gmid-design/assets/topology_library.py` |
| `RH` | `workspaces/run_harness.py` |
| `PLAN` | `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` (v5.9) |

조사 방법:
- 키 경로 전수 추출: scratchpad `review5/keys.py` → `keys_out.txt` (JSON 8개 파일의 전체 경로와 키별 줄 번호).
- 값 어휘, plan 백틱 토큰, 코드의 `get("k")`/`["k"]` 읽기 위치: `review5/scan2.py` → `scan2_out.txt`.
- 영향 범위: `grep -rIo` 출현 수. py/json은 `skills/analog-gmid-design` 전체와 `RH`, md는 `docs`와 스킬 폴더를 셌다.

---

## 1. 현황 인벤토리

### 1.1 topology.json 최상위 키 (keys_out.txt 1~9행)

| 키 | 있는 파일 | 코드가 읽는 곳 |
|---|---|---|
| `schema_version` | 8개 전부 | SD:8695 |
| `topology_name` | 8개 전부 | SD:8694, T2M:87 |
| `source` | 8개 전부 | SD:8696 |
| `linked_topology_files` | _TEMPLATE, nmcnr, pushpull, sf_pushpull, two_stage_ota_sf | SD:8599 |
| `compensation{function, parameters, stage_devices, notes, shared_gm_id_groups, vds_kvl_groups}` | 8개(null 포함) | SR:8723-8736, SR:6168-6178, SD:3657 |
| `netlist[]{name, kind, source, drain, gate}` | 8개 | SR:14639, SD:8592 |
| `symmetry{matching_pairs[]{names, current_forced, matching_sensitivity}, dispositions[]{tag, kind, key, category, reason}}` | 8개 | SD:8593-8605, SR:5402, ACF:86 |
| `sizing_roles{theta[], metrics{}, objective, constraints[]}` | 8개(null 포함) | SR:6896, SR:8316-8327, SD:3960, ACF:87 |
| `device_roles{<dev>: {headroom_role, gm_id_role, L_role, vertical_stack_id, vsb, fold_group, gm_id_match_vgs_of, vds_match_vgs_of, budget_reference_device, same_as_device}}` | 8개(null 포함) | SR:1815-1945, SD:4581-4611 |
| `passive_elements[]{name, kind, terminals, value_ohm, value_farad, value_from_spec, nulling_reference_device}` | current_reuse, pushpull, sf_pushpull, two_stage_ota_sf | SR:4171-4174, SR:5399, SR:5533-5535, T2M:84 |
| `ideal_sources[]{name, kind, terminals, value_amp, implementable}` | current_reuse, folded_cascode, sf_pushpull | SR:4485, SR:5403, T2M:85, T2M:169-171 |
| `ports{<net>: {role, direction}}` | current_reuse, pushpull, sf_pushpull, two_stage_ota, two_stage_ota_sf | SR:4674-4682 (`direction`만 읽음), SR:5406 |

### 1.2 `_`로 시작하는 키 (문서용이어야 하는 키)

| 키 | 파일 | 코드가 읽는가 |
|---|---|---|
| `_schema_note` | _TEMPLATE:6, folded_cascode:5, nmcnr:5 | 아니오 |
| `_note` | pushpull:5, sf_pushpull:5, two_stage_ota_sf:5 | 아니오 |
| `_comment` (필드 안 59곳 등) | 여러 파일 | 아니오 |
| `_<field>_comment`, `_metrics_comment_2`/`_3`, `_device_roles_comment_fold`, `_stage_devices_comment_session30` | current_reuse, folded_cascode, two_stage_ota 등 (keys_out.txt 11~155, 729~737) | 아니오 |
| `_correction_log`, `_correction_log_2` ~ `_correction_log_8` | current_reuse (keys_out.txt 16-23) | 아니오 |
| `_netlist_correction_2026-08-05` | folded_cascode | 아니오 |
| `_confidence_note`, `_value_amp_status`, `_kg_comment`, `_power_comment` | current_reuse, nmcnr | 아니오 |
| **`_compensation_status`** (enum: not_applicable / pending_topology_fn / resolved, "생략 금지" _TEMPLATE:26) | 7개 | 읽는 코드 없음(SR 픽스처 13968 등에 쓰기만 있음). **값이 기계 판정용 enum인데 `_` 접두사가 붙어 있다** |
| **`_netlist_sections_structured`** | current_reuse:240, two_stage_ota:28 | **읽음**: SD:8596, SD:8607. RH:472-473이 이 키가 없으면 SKIP한다 |
| `_netlist_sections` (텍스트) | current_reuse:238, two_stage_ota:26 | 아니오. structured와 내용이 중복된다 |
| **`_known_dangling_nets`** | current_reuse:154 | **읽음**: T2M:83 |
| **`_paper_target_spec`** (op/value 구조화 데이터) | nmcnr:30, pushpull:83, sf_pushpull:252, two_stage_ota_sf:118 | 아니오. PLAN:877(U-25)이 "문서 전용"이라고 적었다 |
| `_paper_target_spec_comment` | 같은 4개 파일 | 아니오 |
| `sizing_roles._target_spec_comment` | two_stage_ota:274 | 아니오. RH:84 docstring이 참조한다 |
| **`_spec_source`** (spec dict) | RH:100, 138, 230, 280, 413 | **읽음**: SR:8193, 8214, 8229 (`require_declared_spec_source`) |

### 1.3 실행 spec(`RH`)의 키

**spec_fn 반환 dict에 들어 있는 키**
- `_spec_source`, `lut_by_kind{nmos,pmos}`, `lut`, `vdd`
- `L_candidates`, `L_grid_step`, `VDS_candidates`, `gm_id_grid`
- `GBW`, `CL`, `Z`, `NDP`, `kg`, `PM_target_deg`
- `stage_gain_min`, `L_min`, `L_min_by_kind{nmos,pmos}`, `W_bounds`, `min_vds_by_role{cascode,tail,mirror}`
- `stage_objective`, `stage_w_max`, `stage_power_tolerance`, `min_finger_w`, `max_finger_w`
- **`vth0_slope{nfet,pfet}`**, `stack_groups_override`, `row_split`
- `t_lln`, `Cc`, `Cf`, `Cs`, `C_Ltot`, `t_settle_total`, `omega_c`

근거: RH:100-127, 138-207, 230-244, 280-298.

**SPECS 항목에 들어 있는 키** (RH:305-350)
- `topology_file`, `spec_fn`, `grid_points_per_theta`, `report_dir`, `search_method`, `slsqp_kwargs`

**run()이 setdefault로 넣는 키** (RH:433-437)
- `floorplan_target{max_aspect_ratio, min_packing_density}`, `max_layout_retry_rounds`

### 1.4 plan이 정의하거나 예정한 필드 (백틱 토큰 전수는 scan2_out.txt 1~248행)
- 레일: `supply_nets`(21회, PLAN:97 첫 출현, 정의 PLAN:237 DEC-60), `supplies`(18회, PLAN:237), `bulk`(PLAN:238 DEC-61).
- `sizing_spec.json` v5 (PLAN:615-625):
  - `meta{schema_version, topology_hash, origin}`
  - `human{objective, constraints[]{metric, op, value, source}, ports, value_amp, compensation_targets{CL, GBW, PM}, driving_spec, wall_clock_budget_s, supplies, node_voltage_targets, gain_budget_db_override, cross_kind_matching, same_as}`
  - `derived{...}`
- S1 메모리 구조 (PLAN:326):
  - 노드 `{name, terminals, is_rail, ac_ground_class, port_role}`
  - 소자 `{name, kind, d, g, s, b, is_diode}`
  - **수동소자 `{name, type, nodes}`**
  - 관계 엣지 type ∈ `equal_vgs`, `vds_eq_vgs`, `same_as`, `budget_ref`, `stacked_vsb`, ...
- `structure.json` (PLAN:326, 794), `wall_clock_budget_s` (PLAN:211, 378), `driving_spec` (PLAN:233, 439), `value_from_constraint` (PLAN:198, 599).

---

## 2. 중복과 동의어 (중요도 순)

### D1. 레일(전원) 개념이 이름 9개, 저장 위치 8곳에 흩어져 있다 ★ 사용자 예시

| 형태 | 위치 | 내용 |
|---|---|---|
| `supply_nets` (계획) | PLAN:237 | topology 넷 목록 |
| `supplies{넷: 전압}` (계획) | PLAN:237, 620 | sizing_spec human |
| `supply_nets` (**현재 코드, 뜻이 다름**) | SR:4524 `spec.get("supply_nets") or ("vdd","VDD")` | `supply_current` **metric 선언 인자**. "공급 전류를 셀 레일 부분집합"이라 계획의 "모든 레일"과 뜻이 다르다. library의 metric 선언에는 이 인자를 쓰는 곳이 없어 늘 기본값으로 돈다(current_reuse:1990-1995의 키는 type/unit/_comment뿐) |
| `rail_nets` | SR:4456 (kcl_residual metric 인자, 기본 6개 이름), SR:7401·8552 (내부 컨텍스트, `{"vdd","gnd","vss"}` 하드코딩) | 레일 이름 집합 |
| `_DEFAULT_RAIL_HI`/`_DEFAULT_RAIL_LO` | SR:3882-3883 | 이름 집합 |
| `_RAIL_NETS` | SD:3147 | 이름 집합. SR:8552와 같은 값이 한 번 더 있다 |
| spec `vdd` (스칼라) | RH:104, 141, 233, 283(2.0). SR이 `spec["vdd"]`를 21곳에서 읽는다(scan2_out.txt 630행) | 가장 높은 레일 전압 |
| metric 인자 `rail: "vdd"`/`"gnd"` | current_reuse:1959, 1965. SR:4789 `ctx.spec["vdd"] if spec["rail"]=="vdd" else 0.0` | gnd를 0 V로 가정한다 |
| metric `excite{vdd: 1.0}` | current_reuse:1938, two_stage_ota:290 | 넷 이름 참조(PSRR 여기원) |
| `supply_v{vdd, vss}` | nmcnr:58-60 (±1 V, 문헌) | 문서 |
| `supplies_v{vdd, vss, agnd}` | pushpull:84-87, sf_pushpull:253-256 | 문서(사용자 확정 U-25) |

→ 문제는 세 가지다. 같은 개념에 이름이 다르다. 코드에 이름 집합이 5벌 있다. `supply_nets`라는 이름이 이미 다른 뜻으로 코드에 있다.

### D2. 부하 용량 CL이 이름 5개로, 한 회로에서 최대 4곳에 저장된다

| 형태 | 위치 |
|---|---|
| spec `CL` | RH:112(3e-12), RH:284(1e-10) |
| `compensation.parameters`의 `"CL"` (함수 인자 이름) | two_stage_ota:9, nmcnr:11. SR:8723-8724가 `spec[k]`로 끌어온다 |
| metric 인자 `CL` | folded_cascode:399(1e-12), nmcnr:474·495(1e-10). SR:3097, 3182가 읽는다 |
| `CL_farad` | nmcnr:34, pushpull:93, sf_pushpull:265, two_stage_ota_sf:125 (문서) |
| `passive_elements[name=CL].value_farad` (null) | pushpull:56-58, sf_pushpull:208-210, two_stage_ota_sf:87-89 |
| plan `compensation_targets{CL}`와 `driving_spec`(부하 용량) | PLAN:620. **계획 자체가 한 섹션에 두 번 둔다** |
| `C_Ltot` | RH:194, current_reuse compensation.parameters. CL과의 관계(같은 개념인지)는 미확인 |

- nmcnr은 1e-10을 RH:284, nmcnr:474, nmcnr:495, nmcnr:34 네 곳에 따로 적었다.
- two_stage_ota_sf의 `added.CL_farad.node: "vout"`(two_stage_ota_sf:127)은 passive CL의 `terminals`(two_stage_ota_sf:90)와 같은 정보를 한 번 더 적은 것이다.

### D3. GBW와 PM 목표

| 개념 | 형태 | 위치 |
|---|---|---|
| GBW | `GBW` | RH:112, RH:284, two_stage_ota:8, nmcnr:10, SR:14595(픽스처) |
| GBW | `GBW_hz` | nmcnr:33 |
| GBW | `gbw_hz` 스칼라 | nmcnr:45 |
| GBW | `gbw_hz{op, value}` | sf_pushpull:274 |
| GBW | `eq10_gbw_hz` 등 | TL:303-328 (반환 키) |
| GBW | plan `GBW` | PLAN:620 |
| PM | `PM_target_deg` | RH:190, RH:285, current_reuse:191, nmcnr:12, current_reuse:2069(`value_from_spec`). py/json 61회, 8개 파일 |
| PM | `PM_target_deg` = 46.0 | nmcnr:35 (문헌) |
| PM | `pm_deg` = 46.0 | nmcnr:46 (문헌, 같은 값을 다른 이름으로 또 적음) |
| PM | metric 이름 `pm_deg` | folded_cascode:391, nmcnr:478 (**측정값**) |
| PM | plan `PM` | PLAN:620 |

- **의미 충돌**: `PM_target_deg`가 nmcnr:35에서는 46(논문), RH:285에서는 70(확정)이다. 같은 이름에 다른 값이 들어 있다. RH:268-272가 이 충돌을 글로 설명하고 있다. 컨테이너 `_paper_target_spec`이 둘을 구분하지만, 키 이름만 보고 grep하면 섞인다.
- **의미 충돌**: `pm_deg`는 목표(nmcnr:46)와 측정 metric(nmcnr:478)에 같이 쓰인다.

### D4. 이득 목표와 metric 이름
- `dc_gain_db{op, value}`: nmcnr:40, sf_pushpull:269 (문서).
- `gain_db`: metric 이름. two_stage_ota:284, folded_cascode:381, nmcnr:457, current_reuse:1883.
- `gain_full_circuit_db`: current_reuse:1944.
- `dc_gain_db`: TL:558과 SR:3191의 반환 dict 키.
- 문서 목표를 적을 때 metric 이름을 쓰지 않아서, `sizing_spec` constraints로 옮길 때 사람이 이름을 대응시켜야 한다.
- `rout_ohm`(pushpull:97, sf_pushpull:279, two_stage_ota_sf:130)은 `_METRIC_UNITS`(SR:5705-5729)에 대응하는 metric type이 없다. 이름은 있고 계산기는 없다.

### D5. 이상 전류원 값 (value_amp)
- `ideal_sources[].value_amp`: current_reuse:144, folded_cascode:105, sf_pushpull:222(null).
- `ideal_source_values.IBias_amp` = 5e-05: sf_pushpull:261 (문서). 같은 소스 IBias의 값이 두 곳에 있고 이름도 다르다(`value_amp` / `<name>_amp`).
- plan은 `value_amp`를 sizing_spec human에 둔다(PLAN:276, 620). topology에도 이미 있으므로, 7b 이관 뒤 topology에서 지우지 않으면 저장 위치가 두 곳이 된다(PLAN:625 이관 대상 목록은 `device_roles`/`sizing_roles`/`compensation`뿐이고 `ideal_sources[].value_amp`는 빠져 있다).
- 영향: `value_amp` py/json 17회(8개 파일), md 55회.

### D6. 소자 극성 어휘가 두 벌이다
- `nmos`/`pmos`: netlist kind(scan2_out.txt 276-277), `lut_by_kind`(RH:101), `L_min_by_kind`(RH:115).
- `nfet`/`pfet`: `vth0_slope`(RH:122, 187, 244, 298).
- 코드가 매번 변환한다: SR:4761 `"pfet" if kind == "pmos" else "nfet"`, SR:7349, tests/probe_mirror_ratio_bound.py:114.
- metric 인자 `kind: "nfet"`: SR:3255, SR:14733.

### D7. `vs`와 `vsb`: 템플릿이 옛 이름으로 남아 있다
- 코드는 옛 이름 `vs`를 거부한다: SR:5790-5810 `validate_no_legacy_vs_key`.
- 그런데 **_TEMPLATE:84, :87의 `_device_roles_comment`는 아직 `"vs": 소스 전압`, `"vs": 0.0`이라고 안내한다.** 템플릿대로 새 회로를 쓰면 로드 게이트가 거부한다.
- 같은 템플릿의 문제가 하나 더 있다. _TEMPLATE:35는 `matching_pairs` 항목에 `kind`를 둔다고 예시하지만, 실제 7개 회로의 matching_pairs 키는 `names`/`current_forced`/`matching_sensitivity`뿐이다(keys_out.txt 953-955). 템플릿과 데이터가 어긋나 있다.

### D8. 소자 참조 필드 이름이 제각각이다

| 뜻 | 쓰이는 이름 | 위치 |
|---|---|---|
| 소자 이름 목록 | `names` | matching_pairs (SR:4686, SD 35곳, ACF:98) |
| 소자 이름 목록 | `devices` | `_netlist_sections_structured.*.devices`, `feeds.devices`, pelgrom metric (SR:3257) |
| 소자 이름 목록 | `members` | plan S1 엣지 (PLAN:326), SD composites (SD:11450대) |
| 스테이지별 소자 | `stage_devices` | compensation |
| 스테이지별 소자 | `stages` | gain_stages_sum/noise metric, current_reuse |
| 스테이지별 소자 | `stage2_devices`, `stage3_devices` | nmcnr metric 인자 |
| 단일 소자 | `device` | rail_referenced_voltage (current_reuse:1958), `terms[].device` |
| 단일 소자 | `*_device` | `gm1_device`, `tail_device`, `high_device` |
| 관계 | `same_as_device` | topology (py/json 51회) |
| 관계 | `same_as` | plan human과 S1 엣지 (PLAN:326, 620) |
| 관계 | `budget_reference_device` | topology (py/json 90회) |
| 관계 | `budget_ref` | plan S1 엣지 (PLAN:326) |

### D9. 여기(excite)와 감지(sense) 선언의 모양이 두 가지다
- 이득 metric: `excite{}` + `sense_p` + `sense_n` + `sense_mode: "diff"`. two_stage_ota:286-294, current_reuse:1946-1954.
- 비(ratio) metric: `excite_num{}` + `excite_den{}` + `sense_num: "diff"` + `sense_den: "common"` + `sense_p` + `sense_n`. current_reuse:1915-1943.
- `sense_num`/`sense_den`은 `sense_mode`와 같은 어휘("diff"/"common")를 쓰면서 이름이 다르다. 코드는 SR:5604-5627에서 두 경로를 따로 읽는다.

### D10. 포트: `role`과 `direction`이 같은 정보를 두 번 담는다
- `role`: `differential_input_p/_n`, `differential_output_p/_n`, `single_ended_input/_output` (scan2_out.txt 285-290).
- `direction`: `input`/`output`. role의 `_input`/`_output`에서 기계적으로 유도된다.
- 코드는 `direction`만 읽는다(SR:4682). topology `ports.role`을 읽는 코드는 grep으로 확인하지 못했다. SR에서 `"role"`을 읽는 5곳(2040, 2041, 8072, 8086, 13637)은 topology ports 경로인지 미확인이다.
- `ports`라는 이름은 SD에서 analog-grammar idiom의 포트 dict(`m.ports["bias"]`, `["rail"]`, `["tail"]`, SD:1019-1021)로도 쓰인다. 메모리 전용이라 JSON 충돌은 아니다.

### D11. `_paper_target_spec` 안의 구조가 파일마다 다르다

| 개념 | nmcnr | pushpull | sf_pushpull | two_stage_ota_sf |
|---|---|---|---|---|
| 레일 | `performance_targets_nmcnr.supply_v` | `supplies_v` | `supplies_v` | (상속) |
| 부하 | `loading_condition`(문자열) + `compensation_parameters.CL_farad` | `loading.CL_farad` | `loading.CL_farad` | `added.CL_farad{value, node}` |
| 성능 목표 컨테이너 | `performance_targets_nmcnr` | `performance_targets` | `performance_targets` | `added` |
| 입력 DC | 없음 | **`input_dc_v: "agnd"`** (pushpull:90) | `input_common_mode: "agnd"` (sf_pushpull:259) | 없음 |
| 목적 | 없음 | `objective: "minimize power"` (문자열) | 없음 | `inherits.constraints_and_objective` |

- **`input_dc_v`는 접미사 `_v`가 전압을 뜻하지만 값은 넷 이름**이다. 이름이 값의 종류와 맞지 않는다(SR:5790 docstring이 말하는 "이름이 의미를 거짓말한다"와 같은 부류).
- **컨테이너 이름 `_paper_target_spec`이 내용과 맞지 않는다**: pushpull, sf_pushpull, two_stage_ota_sf의 값은 논문 값이 아니라 사용자가 확정한 스펙이다(PLAN:877 U-25 "확정(2026-09-15 사용자)").
- two_stage_ota는 같은 역할의 기록을 `sizing_roles._target_spec_comment`(two_stage_ota:274)에 두었다. 다섯 회로 중 한 회로만 위치와 이름이 다르다.

### D12. 회로마다 같은 PDK 상수를 반복한다
`L_min`, `L_min_by_kind`, `W_bounds`, `min_finger_w`/`max_finger_w`, `vth0_slope`, `L_grid_step`, `lut_by_kind`가 4개 spec_fn에 똑같이 복사돼 있다(RH:105-122, 155-187, 234-244, 286-298). 값이 갈린 곳도 있다. `min_finger_w`는 two_stage_ota만 0.1e-6(RH:120)이고 나머지는 1e-6이다. 의도한 차이인지는 미확인이다.

### D13. `_` 접두사 규칙이 지켜지지 않는다
- 기계가 읽는 키에 `_`가 붙어 있다(1.2절): `_netlist_sections_structured`, `_known_dangling_nets`, `_spec_source`. `_compensation_status`도 enum이다.
- 주석 키 이름이 한 규칙으로 모이지 않는다: `_note`, `_schema_note`, `_comment`, `_X_comment`, `_X_comment_2`, `_X_comment_fold`, `_correction_log_N`, `_netlist_correction_<날짜>`.

### D14. 일반 필드명의 뜻이 여러 개로 겹친다
- `kind`:
  - 소자 종류(netlist, passive, ideal에서 nmos/pmos/resistor/capacitor/current_source). 이 쓰임은 일관적이다.
  - `dispositions[].kind` = 소자 극성(_TEMPLATE:39)이고, 패턴 종류는 `tag`에 둔다.
  - _TEMPLATE:35 matching_pairs 예시에서는 `kind: diff_pair`로 패턴 종류를 뜻한다. dispositions와 뜻이 뒤집혀 있다.
  - pelgrom metric 인자에서는 nfet/pfet를 뜻한다(SR:3255).
- `type`:
  - metric 계산기 이름(`metrics.*.type`)
  - theta 적용 메커니즘(`feeds.type` = A/B/C/A_signed/const/settling_split/metric_stage_budget)
  - `intended_role_type` A/B/C/D. _TEMPLATE:61-71이 "같은 글자, 다른 축, 혼동 금지"라고 스스로 경고한다.
  - plan S1 수동소자 `{name, type, nodes}`(PLAN:326). topology의 `{name, kind, terminals}`와 이름이 다르다.
- `min`/`max`의 위치: `L_min`, `stage_w_max`, `gm_id_min`(two_stage_ota feeds)은 뒤에 붙고, `min_finger_w`, `max_finger_w`, `min_vds_by_role`은 앞에 붙는다.

### D15. 단위를 표기하는 방식이 섞여 있다
- **metric 이름**: 앞자리 단위 접두어와 대소문자가 섞인다. `power_uA`, `mismatch_sigma_mV`, `area_um2`, `classab_centering_dev_v`, `rz1_ohm`, `mirror_ratio_error_pct`, `noise_v_rthz`. 이름 접미사와 `unit` 필드가 같은 정보를 두 번 담지만, `validate_metric_units`(SR:5813)가 둘이 일치하는지 검사하므로 게이트가 있는 중복이다.
- **spec 키**: 접미사 없이 SI 단위를 가정한다. `GBW`, `CL`, `Cc`, `t_lln`, `vdd`, `L_min`, `W_bounds`, `stage_w_max`.
- **topology 값**: 단위를 풀어 쓴다. `value_ohm`, `value_farad`, `value_amp`.
- **문서 기록**: `_hz`, `_farad`, `_ohm`, `_amp`, `_v`, `_w`, `_us`, `_v_per_us`, `_mm2`, `_db`, `_deg`.
- **접미사 레지스트리** `_UNIT_NAME_SUFFIXES`(SR:5746-5758)에는 `_hz`, `_farad`, `_amp`, `_s`, `_w`가 없다.
- **대소문자**: 물리 기호는 대문자를 섞는다(`GBW`, `CL`, `NDP`, `Z`, `C_Ltot`, `L_role`, `W_bounds`, `VDS_candidates`, `PM_target_deg`). 나머지는 snake_case다.

---

## 3. 제안

### 3.1 명명 규칙 (기본안)

| # | 규칙 | 근거 |
|---|---|---|
| R1 | JSON 키는 소문자 snake_case. 물리 기호도 소문자로 쓴다(`gbw_hz`, `cl`이 아니라 아래 R3 적용). 예외는 소자·넷 **이름 값**(M1a, Vip)뿐이다 | D15 대소문자 혼재 |
| R2 | **사람이 선언하는 수치**(sizing_spec human, topology 소자 값, 문서 목표)는 단위 접미사를 필수로 붙인다. 접미사는 풀어 쓴 형태 하나만 쓴다: `_v`, `_amp`, `_farad`, `_ohm`, `_hz`, `_deg`, `_db`, `_s`, `_m`, `_w`. metric **이름**에는 기존 레지스트리(SR:5746)대로 표시용 접두 단위(`_ua`, `_mv`, `_um2`, `_pct`)를 허용한다 | 짧은 `_a`는 소자 leg 접미사와 겹친다(`fold_leg_a` folded_cascode:382, `stage1_fold_leg_a` nmcnr). 짧은 `_f`는 `f_slew`(_TEMPLATE:51)의 `f`(비율)와 헷갈린다. 풀어 쓴 형태는 이미 `value_amp`/`value_farad`/`value_ohm`으로 43곳이 쓰고 있어 바꿀 곳이 적다 |
| R3 | 단위 접미사는 **값이 그 단위일 때만** 붙인다. 넷 이름 값에는 `_net`을 붙인다(`input_dc_v: "agnd"` → `input_common_mode_net`) | D11 |
| R4 | 모음(list/map)은 복수형이고, 단위가 있으면 복수형 뒤에 붙인다(`supplies_v`, `supply_nets`) | 기존 `ports`, `metrics`, `device_roles`, `passive_elements` |
| R5 | 소자 이름 목록은 `devices`, 단일 소자는 `device`, 역할 인자는 `<역할>_device`. `names`/`members`는 JSON에서 쓰지 않는다(`members`는 메모리 S1 엣지 전용) | D8 |
| R6 | 범위와 한계는 `<양>_min`/`<양>_max`/`<양>_bounds`(양이 앞) | D14 |
| R7 | 극성 어휘는 `nmos`/`pmos` 하나. `nfet`/`pfet` 폐지 | D6 |
| R8 | `_` 접두사는 **어떤 코드도 읽지 않는 문서**에만 쓴다. 코드가 읽거나 enum인 키는 `_`를 뗀다. 주석 키 형식은 `_<필드>_comment` 하나(문자열이나 문자열 배열). 번호 붙은 로그는 `_correction_log: [...]` 배열 하나로 합친다. `_note`와 `_schema_note`는 `_comment`로 통일한다 | D13 |
| R9 | 개념 하나에 이름 하나, 저장 위치 하나. 다른 곳은 **참조**로만 연결한다(`value_from_spec`, `value_from_constraint`, 소자 이름) | 사용자 원칙("근거 하나만 남기고 계산"), DEC-20 |
| R10 | `kind`는 요소 종류(nmos/pmos/resistor/capacitor/current_source)에만 쓴다. 패턴 분류는 `pattern`, 계산기와 메커니즘은 `type`에 둔다. plan S1 수동소자 `{type, nodes}`도 `{kind, terminals}`로 맞춘다 | D14 |
| R11 | 문서 목표 기록은 sizing_spec human과 **같은 스키마·같은 키**로 쓴다(constraints의 `metric`은 실제 metric 이름). 컨테이너 이름은 출처를 그대로 드러낸다: 논문 값은 `_paper_target_spec`, 사용자 확정 초안은 `_declared_target_spec` | D4, D11 |

### 3.2 개념별 정본 표

변경 비용은 `grep -rIo` 출현 수다(py/json은 skills/analog-gmid-design 전체와 RH, md는 docs와 스킬 폴더).

| 개념 | 정본 이름 | 저장 위치 | 흡수되는 옛 이름 | 읽는 코드(현재) | 변경 비용 |
|---|---|---|---|---|---|
| 레일 넷 | `supply_nets` (list) | topology | SR `_DEFAULT_RAIL_HI/LO`(SR:3882-3883), `rail_nets`(SR:4456, 7401, 8552), SD `_RAIL_NETS`(SD:3147), metric 인자 `supply_nets`(SR:4524, 뜻 다름, §3.3) | 위 5곳 | 코드 5곳. topology 7개 파일에 필드 추가(사용자, U-26) |
| 레일 전압 | `supplies_v` ({넷: V}) | sizing_spec human (7b 전에는 SPECS spec) | spec `vdd`(RH 4곳, SR `spec["vdd"]` 21곳), plan `supplies`(md 18), `supply_v`(nmcnr:58), `supplies_v`(pushpull:84, sf_pushpull:253), metric `rail`의 `else 0.0`(SR:4789) | SR 21곳 | `vdd` 읽기 21곳을 `max(supplies_v)` 유도 함수 하나로 바꾼다. plan md 18곳 |
| 소자 벌크 | `bulk` | topology `netlist[]`(선택) | S1 `b` (메모리) | 없음(신규, DEC-61) | 0 |
| 소스-바디 전압 | `vsb` | sizing_spec derived | `vs` | SR 42곳 | _TEMPLATE:84, 87 두 줄 |
| 요소 값(R/C/I) | `value_ohm`/`value_farad`/`value_amp` | sizing_spec human `element_values{<요소 이름>: {...}}` (topology에는 name/kind/terminals만 남김) | topology `passive_elements[].value_*`, `ideal_sources[].value_amp`, `IBias_amp`(sf_pushpull:261), `CL_farad`(4개 파일) | SR:4171, 4485, 5533, T2M:169 | value_farad 16, value_ohm 10, value_amp 17 (py/json) |
| 부하 용량 | 부하 요소(이름 예: `CL`)의 `value_farad` | 위와 같음 (compensation과 metric은 요소 이름으로 참조) | spec `CL`(RH:112, 284), metric 인자 `CL`(folded_cascode:399, nmcnr:474, 495), `CL_farad`, plan `compensation_targets.CL`, `driving_spec` 부하 용량 | SR:3097, 3182, 8723 | `"CL"` 19회(9개 파일). **folded_cascode, nmcnr, two_stage_ota에는 CL 요소가 없다 → connectivity 추가는 사용자 몫** |
| GBW 목표 | `gbw_hz` | sizing_spec human `compensation_targets` | `GBW`, `GBW_hz`, `gbw_hz` 스칼라 | SR:8723(comp 인자 경유), TL 함수 인자 | `"GBW"` 8회(5개 파일) + TL 함수 인자(§5 결정 8) |
| PM 목표 | `pm_target_deg` | 위와 같음 | `PM_target_deg`, `PM`, 문헌 `pm_deg` | SR:8723, value_from_spec current_reuse:2069 | 61회(8개 파일), md 30 |
| PM 측정 | metric 이름 `pm_deg` | topology sizing_roles (7b 뒤 sizing_spec) | 없음 (목표 쪽 `pm_deg`는 위 행으로 흡수) | SR metric | 0 |
| DC 이득 목표 | constraint `{metric: "gain_db", op, value, source}` | sizing_spec human `constraints` | `dc_gain_db{op, value}`(nmcnr:40, sf_pushpull:269) | SR:8316-8327 | 문서 2곳 |
| 이상원 구현 가능성 | `implementable` | topology | 없음 | T2M:171 | 0 |
| 포트 | `ports{<넷>: {role}}` | topology | `direction`(role에서 유도) | SR:4682(`direction`) | SR 한 곳을 role 유도로 교체 + 5개 파일 × 2~4줄. 사용자 결정 7 |
| 극성 어휘 | `nmos`/`pmos` | 전체 | `nfet`/`pfet` | SR:3255, 4761, 7349, tests 3개 파일 | vth0_slope 25회(6개 파일) |
| 동일 치수 | `same_as` | sizing_spec human | `same_as_device` | SR:2422, 2423, 9100 | 51회(7개 파일), md 27 |
| 전압 예산 기준 | `budget_reference_device` 유지. S1 엣지 type `budget_ref`는 메모리 전용이라 명시적 대응표로 연결 | sizing_spec derived | 없음 | SR:1945 외 | 0 (plan에 대응표만 추가) |
| 소자 목록 | `devices` | 전체 | `names`(matching_pairs), `stages`(→ `stage_devices`) | SR 17, SD 35, ACF:98, 103, design_report.py:65 | 약 90줄(추정, `names` 출현 합계) |
| 여기/감지 | `excite{}`, `sense_p`, `sense_n`, `sense_mode`. 비 metric은 `num{같은 4키}`, `den{같은 4키}` | metric 선언 | `excite_num/den`, `sense_num/den` | SR:5604-5627 | current_reuse 2개 metric(1915-1943), 코드 한 함수 |
| 섹션 구조 | `netlist_sections` | topology | `_netlist_sections_structured`, `_netlist_sections`(텍스트 중복 → 삭제) | SD:8596, 8607, RH:472 | 11회(4개 파일) |
| 알려진 dangling 넷 | `known_dangling_nets` | topology | `_known_dangling_nets` | T2M:83 | 3회 |
| 보상 상태 | `compensation_status` | topology | `_compensation_status` | 없음(픽스처만) | 16회(9개 파일) |
| spec 출처 | `spec_source` | spec | `_spec_source` | SR:8193, 8214, 8229 | RH 5 + SR 3 |
| 문서 목표 기록 | `_paper_target_spec`(논문) / `_declared_target_spec`(사용자 확정 초안). 둘 다 R11 스키마 | topology(문서) → 7b에서 sizing_spec human으로 이관 | `_target_spec_comment`(two_stage_ota:274), `performance_targets_nmcnr`, `compensation_parameters`, `loading(_condition)`, `added`, `input_dc_v` | 없음 | 문서 5개 파일 |
| PDK 상수 | `vth0_slope`, `l_min_m`, `w_bounds_m`, `finger_w_min_m`, `finger_w_max_m`, `l_grid_step_m` | 공정 기록 한 곳(예: LUT npz 메타 또는 PDK dict 하나. PLAN:325 `lut_conditions_from_npz`와 연결 가능) | spec_fn 4개에 복사된 사본 | SR `W_bounds` 12곳 등 | 중간. 사용자 결정 10 |

### 3.3 `supply_nets` / `supplies` 구체안

세 가지 형태를 비교했다.

| 안 | topology | spec | 장점 | 단점 |
|---|---|---|---|---|
| A. 같은 키, 다른 내용 | `supplies: {"vdd": {"polarity": "positive"}, "gnd": {...}}` | `supplies: {"vdd": 1.8, "gnd": 0.0}` | 개념어가 하나로 보인다 | **같은 이름에 다른 스키마**라 R9와 D14류 의미 충돌이 생긴다. grep과 로더 오류 메시지만으로 어느 파일의 `supplies`인지 알 수 없다. `polarity`는 전압에서 유도되는 값이라 저장하면 중복이 되고, agnd(중간 전위)처럼 모순이 생길 수 있다(PLAN:238 DEC-61은 bulk 기본값을 "가장 낮은/높은 전위 넷"으로 전압에서 유도한다) |
| B. 현재 plan | `supply_nets: ["vdd", "gnd"]` | `supplies: {"vdd": 1.8, "gnd": 0.0}` | 역할이 나뉜다(connectivity / 값) | `supplies`에 단위가 없다(R2 위반). 문서 기록 `supplies_v`와 이름이 한 글자 다르다 |
| **C. 권고** | `supply_nets: ["vdd", "vss", "agnd"]` (넷 목록만, 극성 없음) | `supplies_v: {"vdd": 1.8, "vss": 0.0, "agnd": 0.9}` | 이름이 역할(넷 / 전압)과 단위를 드러낸다. 이미 pushpull:84, sf_pushpull:253 문서 기록이 `supplies_v`라서 그대로 옮기면 된다. 코드에 `supplies`가 0회라 plan md 18곳만 고치면 된다 | spec 쪽 넷 키 집합이 topology `supply_nets`와 **같아야 한다**. 이 일치는 로드 게이트로 강제한다(GB0, PLAN:276에 이미 자리가 있다) |

C안에서 함께 해야 할 일:
1. spec 스칼라 `vdd`를 폐지하고 "가장 높은 레일 전압 = max(`supplies_v`)"를 유도 함수 하나로 둔다. SR의 `spec["vdd"]` 21곳이 그 함수를 부른다. `rail_referenced_voltage`의 `else 0.0`(SR:4789)도 `supplies_v[rail]`로 바꾼다. 이렇게 하면 DF-24/IC11(PLAN:647, 735)과 같은 변경 단위가 된다.
2. **현재 코드의 metric 인자 `supply_nets`(SR:4524)는 이름을 비워야 한다.** 이 인자는 "공급 전류로 셀 레일 부분집합"이라는 다른 개념이다. 기본안은 인자를 없애고, 선언된 전압 중 가장 높은 레일(DEC-61 bulk 규칙과 같은 방식)에서 유도하는 것이다. agnd처럼 여러 레일에서 전류를 끄는 회로의 정의는 metric 정의 문제이므로 사용자 결정 9로 남긴다. `rail_nets`(SR:4456)는 topology `supply_nets`를 그대로 쓴다.
3. 문서 기록: nmcnr:58 `supply_v` → `supplies_v`. PLAN:237은 "문헌 필드는 출처일 뿐 레일 정본이 아니다"라고 했으므로, 이름만 맞추고 정본 역할은 주지 않는다.
4. 넷 이름의 대소문자(`VDD` 등)는 `supply_nets`가 선언되면 이름 집합으로 추정할 필요가 없어지므로 기본 집합 5벌을 전부 삭제한다(DF-19, PLAN:730).

---

## 4. 마이그레이션 순서와 위험

### 4.1 원칙
- **옛 이름을 조용히 같이 읽지 않는다.** 새 이름으로 바꾸는 커밋에서 옛 키를 거부하는 로드 게이트를 같이 넣는다. 선례는 `validate_no_legacy_vs_key`(SR:5790-5810, "조용히 읽어주면 두 이름이 공존해 다시 모호해진다")다. 게이트는 "실제로 거부한다"를 먼저 검증한다.
- **작성자와 검증자 분리**: 이름 변경 코드는 code-author가 쓴다. 옛 키 거부 red test와 기준선 equivalence 비교는 test-author가 쓴다. 코드와 기대값을 한 커밋에서 같이 바꾸지 않는다. SR self-test 픽스처들(SR:13968, 14588, 14730 등)이 옛 키를 품고 있으므로, 픽스처 키 갱신은 test-author 커밋으로 분리하고 **값은 바꾸지 않는다**.
- **영역 구분**:
  - 사용자 영역(connectivity: `netlist`, `supply_nets`, `bulk`, `ports`, 요소 `terminals`, CL 요소 추가)은 제안표를 만들어 사용자 확인을 받은 뒤 오케스트레이터가 반영한다(U-16, PLAN:537).
  - 메타데이터 이름 변경(`_` 접두사 정리, 주석 키 통합, `same_as_device` → `same_as` 등)은 사용자가 수정하지 않는 영역이지만, topology.json 파일 변경이므로 plan 규정대로 사용자 확인 기록을 남긴다.
- **equivalence 기준**: 이름만 바꾼 뒤 4개 사이징 회로의 `theta_star`, `metrics`, `instance.json` 수치가 바이트 단위로 같아야 한다(키 이름을 매핑해서 비교). 수치가 하나라도 달라지면 이름 변경이 아니라 동작 변경이다.

### 4.2 Phase 배치 제안

| 단계 | 내용 | 담당 | 근거 Phase |
|---|---|---|---|
| M0 (즉시, 문서) | plan 명칭 확정: `supplies` → `supplies_v`, S1 수동소자 `{type, nodes}` → `{kind, terminals}`, `compensation_targets{CL, GBW, PM}` → 요소 참조 + `gbw_hz`/`pm_target_deg`, `driving_spec`의 부하 용량과 CL 중복 제거, N3.15 이관 목록에 `ideal_sources[].value_amp`와 `passive_elements[].value_*` 추가, 규칙 R1~R11을 N3.15 옆에 명칭 절로 추가. `_TEMPLATE`의 `vs` → `vsb`(84, 87행)와 matching_pairs `kind` 예시(35행) 정정 | 오케스트레이터(템플릿은 사용자 확인) | 문서만 |
| M1 | 레일: topology `supply_nets`, spec `supplies_v`, `vdd` 유도 함수, 이름 집합 5벌 삭제, metric 인자 `supply_nets`/`rail_nets` 정리. red test: 이름 집합 제거 뒤에도 기존 4개 회로가 같은 결과인지, `supply_nets` 미선언 신규 회로를 거부하는지, IC11 원점 이동 불변성 | code-author / test-author | Phase 4 (DF-19·DF-24·DF-26, U-26 (a)가 이미 여기 배치됨) |
| M2 | `_` 접두사 정리(`netlist_sections`, `known_dangling_nets`, `compensation_status`, `spec_source`), 주석 키 통합, `nfet`/`pfet` → `nmos`/`pmos`, `names` → `devices`, excite/sense 모양 통일. 각각 옛 키 거부 게이트 포함 | code-author / test-author | 6a (S0 해시와 S1 스키마를 정하는 단계. 해시 입력 키 이름이 여기서 굳으므로 이후에 바꾸면 ratified 기록 전부가 review_needed로 넘어간다, PLAN:340) |
| M3 | spec 값 이름(`gbw_hz`, `pm_target_deg`, 요소 값 참조, `same_as`, `element_values`, PDK 상수 분리)과 `_paper_target_spec`/`_declared_target_spec`의 R11 스키마화 | code-author / test-author, 오케스트레이터(topology 필드 제거) | 7b (`sizing_spec.json` v5 이관과 equivalence가 이미 계획돼 있음, PLAN:625, 798. 이관 한 번에 이름을 같이 바꿔 비용을 한 번만 치른다) |

### 4.3 위험
1. **compensation.parameters는 함수 인자 이름이다**(SR:8723-8724 `spec[k] for k in comp["parameters"]`). spec 키를 `gbw_hz`로 바꾸면 TL 함수 시그니처(`GBW`, `CL`, `Z`, `NDP`, `kg`, `t_lln`, `PM_target_deg`)도 바꾸거나 매핑표를 둬야 한다. 매핑표를 두면 이름 두 벌이 공존하므로 R9와 부딪친다(사용자 결정 8).
2. **S0 해시 입력**: M2를 6a 이후로 미루면, 키 이름이 해시에 들어간 ratified `structure.json`이 전부 무효가 된다. 반드시 6a 전이나 6a 안에서 바꾼다.
3. **`value_from_spec` 문자열 참조**(current_reuse:35 등 9곳, current_reuse:2069 `"PM_target_deg"`): 문자열 값 안의 이름은 grep 키 검색에 걸리지 않는다. 이름 변경 도구가 **값 문자열까지** 바꾸는지 test-author가 따로 검사해야 한다.
4. **워크스페이스 산출물**(`workspaces/*-report/*.instance.json`, 보고서 HTML)은 옛 키로 저장돼 있다. `design_report.py:44, 64`가 instance와 topology를 읽으므로, 옛 산출물 재생성이나 거부 방침을 정해야 한다. 산출물 키 목록은 이번에 전수 조사하지 않았다(미확인).
5. **md 문서 참조 수**: `stage_devices` md 88, `value_amp` md 55, `budget_reference_device` md 49, `PM_target_deg` md 30. 레지스트리와 계획 문서 동기화 비용이 코드보다 크다.

---

## 5. 사용자 결정 목록 (기본안은 위에 적은 대로 진행 가능하고, 아래만 사용자 몫)

1. **레일 이름 형태**: C안(`supply_nets` + `supplies_v`, 권고) / B안(`supplies`, 현재 plan) / A안(같은 키 `supplies`) 중 선택.
2. **단위 접미사 형태**: 풀어 쓴 형태(`_farad`, `_amp`, `_ohm`, `_hz`, 권고) / 짧은 SI 형태(`_f`, `_a`. `fold_leg_a`, `f_slew`와 충돌 위험).
3. **접미사 규칙 적용 범위**: 사람이 선언하는 값(human, topology, 문서)만(권고) / 하네스 탐색 설정과 PDK 키(`L_candidates`, `W_bounds`, `min_finger_w` 등)까지.
4. **connectivity 추가**: 7개 회로의 `supply_nets`(U-26에 이미 있음). CL을 요소 값으로 통일한다면 CL 요소가 없는 folded_cascode, nmcnr, two_stage_ota(와 current_reuse의 `C_Ltot` 대응 여부)에 부하 커패시터 요소를 추가할지.
5. **nmcnr 레일 전압**: 문헌 ±1 V / 하네스 단일 기준 `vdd` 2.0(U-26 (a)와 같은 항목).
6. **문서 목표 컨테이너 이름**: pushpull, sf_pushpull, two_stage_ota_sf의 사용자 확정 스펙을 `_paper_target_spec`에서 `_declared_target_spec`으로 바꿀지.
7. **`ports.direction` 삭제**(role에서 유도) 여부. ports는 사용자 확인 대상이다.
8. **보상 함수 인자 이름**: TL 함수 시그니처를 snake_case와 단위 접미사로 바꿀지 / spec 키만 바꾸고 매핑표를 둘지.
9. **`supply_current` metric 정의**: 레일이 셋 이상인 회로(agnd)에서 "공급 전류"를 어느 레일 기준으로 셀지. 기본안은 가장 높은 전위 레일.
10. **PDK 상수 단일 위치**: 회로별 spec_fn 복사본을 한 곳으로 모을지. two_stage_ota의 `min_finger_w` 0.1e-6(RH:120)이 의도된 차이인지 확인이 필요하다.

---

## 6. 변경 비용 요약

| 묶음 | 코드 | 데이터(JSON) | 문서(md) | 배치 |
|---|---|---|---|---|
| 레일(M1) | SR 이름 집합 4곳 + SD 1곳 + `spec["vdd"]` 21곳 → 유도 함수 1개 | topology 7개 파일에 `supply_nets` 추가(사용자), spec 4곳 | plan `supplies` 18곳 | Phase 4 |
| `_` 접두사와 주석(M2) | SD 2곳, T2M 1곳, SR 3곳, RH 6곳 | 약 30개 키(current_reuse에 집중) | 소량 | 6a |
| 극성, 소자 목록, sense(M2) | SR:3255, 4761, 7349, 5604-5627 / `names` SR 17 + SD 35 + ACF 2 | vth0_slope 25회, names 약 34줄, metric 2개 | vth0_slope md 24 | 6a |
| spec 값 이름과 요소 값(M3) | SR:3097, 3182, 4171, 4485, 5533, 8723 + TL 함수 인자 | PM_target_deg 61회, CL 19회, GBW 8회, value_* 43회, same_as_device 51회 | PM 30, value_amp 55, same_as_device 27 | 7b(이관과 동시) |
| 즉시(M0) | 0 | _TEMPLATE 3줄 | plan 명칭 절 | 지금 |
