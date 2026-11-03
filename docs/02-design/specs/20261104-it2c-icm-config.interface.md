# interface card: 20261104-it2c-icm-config

card IT-2c(측정 구성) 재동결. 입력 = 계획 v6.38.8 N6.6, N3.6 정본, N3.8 '창 필드'·'ICMR 판정 = 영역 행 창', design 41 v1.16.3 §4.7-W(정본)·§4.7-2~4.7-4. 옛 재동결본 `card/it2c` `d95c8ff8`(v6.37·v1.14.1)을 대체한다. 바뀐 것 = 전도 행 R0 삭제, 판정 여유 0, 창 필드 하나, ICMR 판정 = 영역 행 창.

test 작성 주체는 엔진 소스를 보지 않고 이 문서와 기존 test 하네스(`E/tests/**`)만 쓴다. 피검 함수를 불러 기대값을 만들지 않는다. 공개 이름만 import한다. `E/` = `skills/analog-gmid-design/gmid_engine/`. base = 통합 브랜치에서 IT-1 범위 재작성(`20261104-it1-input-point`) 병합 head.

## 빈칸 답(test 작성자 보고, 2026-11-04)

**1. `g_bound` 수치 식**(design 41 §4.7-3b `graph.ss_nodal`). 스탬프 s마다 값 ĝ_s,ij와 연산 수 c_s(`StampSet.g_ops`)를 손으로 세어:
- S_ij = Σ_s |ĝ_s,ij|, k_ij = 항목 (i, j)의 스탬프 항 수, C_ij = Σ_s γ_{c_s}·|ĝ_s,ij|
- **E_ij = γ_{max(k_ij−1, 0)}·S_ij + C_ij + γ_{n+1}·|Ĝ_ij|**
- n = `size`, γ_m = m·u/(1 − m·u), γ_0 = 0, u = `sys.float_info.epsilon` / 2 = 2⁻⁵³. 값 0 항목은 스탬프에서 빠지므로 세지 않는다.
- 비교는 float 그대로 이 식을 계산한 값과 한다. 피검 함수로 기대값을 만들지 않는다.

**2. `Circuit.port_window`**: 인스턴스 메서드다(정적 아님). 레일 끝을 그 `Circuit`의 `node.dc_rail_v` 최소·최대에서 읽으므로 인스턴스가 필요하다. 레일 자름을 뺀 포트 창 단언은 `icm_config_window` 결과의 cfg로 한다.

**3. `region_rows` 행 값 test의 projection**: `Circuit(projection, *, lut, linear)`의 `projection`은 `.column(kind, field)`·`.value(kind, key, field)` 질의만 쓴다. `extras`를 읽지 않는다. 봉인된 toy 스냅샷을 그대로 넘긴다(`build_ctx` + `size_and_seal`, `.snapshot`). 손 조립이면 열 = `node.dc_writer`, `node.dc_rail_v`, `node.port_direction`, `device.pins`, `device.kind`, `device.bulk`, `device.dc_L`, `device.dc_colour`, `device.dc_coord`. `values` = `dict(snapshot.column("node", "dc_v"))`(레일 포함), `lut` = 커널 `LutAccess`, `linear` = `frozenset` 소자 이름. 기대값은 `mos_point`가 아니라 손 VDS·VSB·VGS와 `gmid_engine.lut.vdsat(memo, kind, w_key, L, vgs, vds, vsb)` 직접 호출로 낸다.

**4. 선언 뷰 병합 spec 예**: 제약의 `view` JSON은 `{"ac_excite": {<넷>: <가중>}, "sense_p": <넷>, "sense_n": <넷 또는 null>, "sense_mode": "single_ended" 또는 "differential"}`다(기존 `tests/authoring/test_spec_views.py:16`·`:213` 꼴, 포트 `in_p`·`in_n`, 출력 `out`).
- 같은 키: `{"ac_excite": {"in_p": 0.5, "in_n": -0.5}, "sense_p": "out", "sense_n": null, "sense_mode": "single_ended"}` → 뷰 하나, `source == "spec_constraint_view"`, `default_port is True`.
- 다른 키: `{"ac_excite": {"in_p": 1.0}, "sense_p": "out", "sense_n": null, "sense_mode": "single_ended"}` → 뷰 둘, 기본 뷰만 `default_port is True`.

**5. T-RN 도달 toy**: 지원 밖 kind(인덕터, 이상 전압원, 지원 밖 MOS kind)는 S1 `s1_dc_conduction`이 먼저 정지하므로(`SUPPORTED_SOURCE_KINDS = ("current_source",)`) 파이프라인과 `ss_evaluate`로는 닿지 않는다. T-RN은 **`ss_circuit_field`를 손 조립 스냅샷으로 직접 부른다**(위 READS 열, 소자 하나를 `voltage_source`·`inductor`·bulk None으로, 값은 기존 `tests/metrics/test_ss_circuit.py:99-119` 사례). 단언 = `StructureUnresolvedError`, `reason == "unsupported_rule_branch"`, `rule_branch == "ss_element_kind"`, 그 소자 이름. `metrics_ss` 소스·READS에서 조립 호출 0은 T-L10이 본다. '블록 계수 행'은 단언하지 않는다. 위치 = `tests/metrics/test_ss_circuit.py`.

**6. `INPUT_STATUS_UNSETTLED`**: card WB-1까지 정의가 남고 `"unsettled"` 문자열도 커널 `node.dc_window`에 남는다. T-L8f 소스 grep에서 **뺀다**. cfg 쪽은 행동으로만 단언한다: `node.dc_window_cfg` 항목 `input_status` ∈ {`"measured"`, `"unmeasured"`}. 커널 항목 상태는 단언 금지. 위 '없음' 목록의 `"unsettled"`는 cfg 상태를 뜻한다.

**7. `conductance_matrix(bound=True)` 호출 규칙**: `conductance_matrix(ss.circuit, len(ss.nodes), bound=True) -> (g, g_bound)`. `ss` = `graph.ss_circuit` 값, `bound`는 키워드 전용, 기본 `False`면 `g` 하나(옛 소비자 값 불변). test는 직접 불러 T-L10 (k)를 단언해도 되고 `graph.ss_nodal.g_bound`로 봐도 된다. 자리 단언은 AST로 한다: 비test 엔진 소스에서 `bound=True` 키워드 호출 = `ss_nodal` 하나. 글자 패턴(`conductance_matrix(ss.circuit`)이나 옛 소비자 `block_model`·`ff_gm_ratio`의 `bound` 없는 호출은 세지 않는다.

## 관찰 가능한 계약

### 공개 이름과 서명

| 모듈 | 심볼 | 시그니처·값 |
|---|---|---|
| `gmid_engine.sizing` | `Circuit` | 아래 '`Circuit` 계약' |
| `gmid_engine.sizing` | `saturation_window` | 아래 '`saturation_window` 계약' |
| `gmid_engine.sizing` | `INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED` | `"measured"`·`"unmeasured"`. `INPUT_STATUS_F_COMPONENT_UNDECLARED`는 **없다**. `INPUT_STATUS_UNSETTLED`는 card WB-1까지 남는다(단언 금지) |
| `gmid_engine.sizing` | `SS_CIRCUIT_WRITER`·`SS_NODAL_WRITER`·`ICM_CONFIG_WRITER` | `"ss_circuit"`·`"ss_nodal"`·`"icm_config"` |
| `gmid_engine.metrics.ss_circuit` | `ss_circuit_field` | 블록(writer `ss_circuit`). `ss_circuit_field(snapshot, donors=, counters=)`, extras 없음 |
| `gmid_engine.metrics.ss_circuit` | `is_dc_conducting_passive(kind) -> bool` | `kind == "resistor"`일 때만 True |
| `gmid_engine.metrics.ss_circuit` | `CODE_PASSIVE_MISSING` | `"passive_value_undeclared"` |
| `gmid_engine.metrics.ss_nodal` | `ss_nodal_system` | 블록(writer `ss_nodal`). `ss_nodal_system(snapshot, donors=, counters=)` |
| `gmid_engine.metrics.icm_config` | `icm_config_window` | 블록(writer `icm_config`). `icm_config_window(snapshot, lut, linear_frozenset, donors=, counters=)` |
| `gmid_engine.metrics.icm_config` | `kvl_sensitivity` | 아래 '`kvl_sensitivity` 계약' |
| `gmid_engine.metrics.aux_types` | `NodalSystem` | frozen `NodalSystem(nodes, fixed, g, g_bound, factor)` |
| `gmid_engine.metrics.aux_types` | `IcmConfig` | frozen `IcmConfig(config, pivot_a_e, pivot_resolution, vcm0, vcm_lo, vcm_hi, undefined)` |
| `gmid_engine.metrics` | `StampSet` | `StampSet(g=(), c=(), g_ops=())`, `len(g_ops) != len(g)`이면 생성 때 `ValueError` |
| `gmid_engine.metrics` | `mos_stamps`, `two_terminal_stamps` | `g_ops` = `g`와 같은 길이·순서의 연산 수. MOS: (d, s)·(s, s) 항목 2, 나머지 0. 저항: 넷 각 1. 용량: 둘 다 빈 값 |
| `gmid_engine.metrics._helpers_nodal` | `conductance_matrix` | `conductance_matrix(circuit, size, *, bound=False)`. `bound=True`면 `(g, g_bound)` |
| `gmid_engine.graph` | `ViewSeed`·`ViewS1v` | 칸 `default_port: bool`(기본 False) 추가 |

서명 불변 진입점: `ss_evaluate(sealed, ctx, theta, constraints, counted_rails=(), *, junction, area_decl=None, noise_decl=None, mismatch=None, structure=None, driving=None, diffusion=())`, `dc_columns`, `dc_writer_plan`, `size_and_seal`, `metrics_ss`, `metrics_aux`, `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), stop_on_unsupported=True, donors, counters)`.

공개 아님(직접 부르지 않음): `collect_views`, `_transfer_resolution`.

**`Circuit` 계약**(자리 = `E/sizing/_helpers_dc_solve.py`, `block_columns._Circuit` 이동)
- 생성 `Circuit(projection, *, lut, linear)`. 두 키워드 빠지면 `TypeError`.
- `mos_point(m, values) -> (vgs, vds, vsb)`, `vds_vsb(m, values) -> (vds, vsb)`, `canonical_writers()`(쓰기 순번 순), 정적 `kind_sign(kind) -> ±1`.
- `region_rows(values)` -> 행 `(a, b, sign, slack, kind)`의 tuple 또는 None. `dc_coord` MOS마다 행 하나:
  - 선언 없음: `(d, s, kind_sign, VDS − VDSAT, "sat")`
  - `triode` 선언: `(d, s, −kind_sign, VDSAT − VDS, "triode")`
  - **tol 항 없음.** VDSAT = LUT `vdsat(memo, kind, w_key, L, vgs, vds, vsb)`. VDSAT 열이 없으면 None. tol_VDsat 미정은 행에 영향 없음.
  - `off` 선언 소자 행 없음(EO-1 전까지는 `linear`에 들지 않는 선언이 없으므로 대상 toy 없음 -- 단언 금지).
- `port_window(value, slope, dlo, dhi) -> (lo, hi)` = 두 끝 전압의 [min, max] ∩ 레일. slope = 0이면 두 끝 = value.
- `writer_head`·`declared_inputs`는 **없다**.
- 속성은 호출자가 바꿀 수 없다. `check_g8`·`check_value_types`가 이 모듈에 위반을 내지 않는다.

**`saturation_window` 계약**
- `saturation_window(unknown, root, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`. `root` = 넷 하나(쌍·묶음 없음).
- `slope`를 주면 감도 연립 없이 끝만 낸다(앞 넷 인자 무시, 반환 slope = 받은 값).
- 끝 = 행마다 `slack + sign·(slope[a] − slope[b])·Δ ≥ 0`의 교집합. 기울기가 `sys.float_info.epsilon` 이하인 행은 건너뛴다(V/V 행 분해능).

**`kvl_sensitivity` 계약**
- `kvl_sensitivity(nodal, drive, servo=None) -> (slope, a_e, ve) | None`. `drive` = 입력 포트 넷 tuple. `servo` = None 또는 `(excite, sense, span)`(excite = ((넷, e 가중), ...), sense = ((넷, 부호), ...), span = 레일 폭).
- `slope` = {넷: dV/dx}. servo None이면 구동 넷 = 1, 있으면 구동 넷 = 1 − e_p·(c·vx)/a_e. 그 밖 고정 넷·떠 있는 노드 = 0.
- `a_e` = (c·ve)/span(servo None이면 None), `ve` = 구동 {p: span·e_p}의 노드 전압.
- 인수분해 특이·풀이 None·a_e 정확히 0이면 None. `closure` 인자 없음(`TypeError`).

### 필드 -- writer 하나

| 필드 | 값 | writer | READS(블록) |
|---|---|---|---|
| `graph.ss_circuit` | `SsCircuit(nodes, circuit, resistors, capacitors, ground_nets, input_nets, missing)`. 노드 순서 = (`node.dc_colour`, 이름), 소자 = (`device.dc_colour`, 이름). `missing` = 값 없는 수동소자 이름 정렬 | `ss_circuit` | ⊇ {`device.element_class`, `device.kind`, `device.pins`, `device.bulk`, `device.ss_dev`, `device.dc_colour`, `device.passive_value`, `node.ac_ground_class`, `node.dc_colour`, `node.port_direction`} |
| `graph.ss_nodal` | `NodalSystem` 또는 `Undefined`(아래) | `ss_nodal` | ⊇ {`graph.ss_circuit`, `device.kind`} |
| `node.dc_window_cfg` | 입력 포트마다 `Window(lo, hi, constraints, input_status, tol_v)`(아래 'cfg 항목') | `icm_config` | 다음 행 |
| `graph.icm_config` | `IcmConfig` | `icm_config` | ⊇ {`node.dc_writer`, `node.dc_rail_v`, `node.port_direction`, `node.port_role`, `node.dc_v`, `device.pins`, `device.kind`, `device.bulk`, `device.dc_L`, `device.dc_colour`, `device.dc_coord`, `device.dc_tol_v`, `graph.ss_nodal`, `graph.views`}. **없음**: `node.dc_window`, `node.dc_output_structure`, `device.ss_dev`, `device.dc_op`, `device.dc_conduction_floor`, `device.dc_off_current`, `device.element_class`, `device.dc_nets`, `device.unsupported`, `node.is_rail` |
| `graph.views`(바뀜) | 기본 포트 뷰가 늘 든다(아래) | `s1v_fields` 그대로 | 그대로 |
| `node.dc_window`(바뀜) | 항목 = W4 뿌리 넷만(입력 점 뿌리 포함). 뿌리 아닌 입력 포트·선언 포트·F 성분 포트 항목 없음. 수치·상태 칸은 card WB-1이 재작성 -- **단언 금지** | `dc_columns` | 그대로 |
| `node.dc_window_def`·`node.dc_window_def_refined`·`node.dc_output_structure` | **없음** | -- | -- |

**ss_nodal 값**
- `NodalSystem`: `nodes` = `ss_circuit.nodes`, `fixed` = frozenset[int](ac 접지 ∪ 입력 넷 색인), `g`·`g_bound` 같은 모양 ndarray(S), `factor` 튜플. 모든 ndarray `flags.writeable is False`.
- 저항 결측: `Undefined("ss_nodal", "passive_value_undeclared", "definitional", (("elements", 결측 저항 이름 정렬 tuple),))`. 용량 이름은 들지 않는다.
- 용량만 결측: `NodalSystem`.

**cfg 항목**: `constraints == 0`. `input_status` ∈ {`"measured"`, `"unmeasured"`}. 측정 실패 = `Window(None, None, 0, input_status="unmeasured")`. `tol_v` = 봉인점 `device.dc_tol_v` 가운데 `device.dc_coord` MOS의 None 아닌 값의 최솟값, 모두 None이면 None(상태는 `"measured"`). 구성이 None이면 항목 없음.

**IcmConfig 칸**: `config` ∈ {`"servo"`, `"as_is_single_input"`, None}. `pivot_a_e`·`pivot_resolution` float 또는 None(출력 전용). `vcm0`·`vcm_lo`·`vcm_hi` float 또는 None(V). `undefined` = tuple[`Undefined`], 구성 None이면 원소 하나·quantity `"icm_config"`. 칸 `inverting_port`·`tied_ports`·`transfer`·`kvl`·`output_structure` 없음.

**권한표**: `SS_WRITES`에 `("graph", "ss_circuit")` → `ss_circuit`, `("graph", "ss_nodal")` → `ss_nodal`, `("node", "dc_window_cfg")`·`("graph", "icm_config")` → `icm_config`. `DC_WRITES`의 `dc_writer_plan` 행에서 `("node", "dc_output_structure")` 삭제.

**READS**: `metrics_ss` ⊇ {`graph.ss_circuit`, `device.ss_dev`}. `metrics_aux` ⊇ {`graph.ss_circuit`, `graph.ss_nodal`, `device.ss_dev`, `device.dc_colour`}.

**부르는 순서**: `ss_evaluate`는 `ss_dev` → `ss_circuit` → `metrics_ss` → (aux 요청 또는 views가 있으면) `ss_nodal` → `icm_config` → `metrics_aux` → `metrics_dc`.

### S1v 기본 포트 뷰(손 판정 기준)

- 입력 포트 둘, role `differential_input_p`·`_n` 한 쌍: 뷰 하나, 여기 p = +1/2, n = −1/2, 감지 = 출력 넷 전부.
- 그 밖: 입력 포트마다 뷰 하나, 여기 가중 1, 감지 = 출력 넷 전부. 입력 0이면 뷰 0.
- 선언 뷰와 기본 포트 뷰가 늘 함께 든다. 같은 (여기, 감지) 키는 하나로 합치고 선언이 먼저라 `source == "spec_constraint_view"`로 남는다. `default_port` = 키가 기본 포트 뷰 키 집합 안이면 True. 목록 순서 = 키 정렬. `view_required` 기록은 뷰가 하나도 없을 때만.
- gain·pm 제약 표시는 선언 뷰 기준 그대로.

### 측정 구성 규칙(손계산·판정 기준)

**갈래 순서**(앞이 이긴다, category 모두 `definitional`)

| # | 조건 | 결과 |
|---|---|---|
| 1 | `graph.ss_nodal`이 `Undefined` | None, `Undefined("icm_config", "passive_value_undeclared", "definitional", 같은 detail)` |
| 2 | 입력 포트 셋 이상 | None, `icm_inputs_unsupported`, detail `(("inputs", 포트 tuple),)` |
| 3 | 입력 포트 0 | None, `view_required`, detail `(("default_views", 0),)` |
| 4 | `default_port` 전달 뷰 둘 이상 | None, `view_required`, detail `(("default_views", 수),)` |
| 4′ | 그 뷰 감지가 출력 하나도 `differential_output_p`·`_n` 한 쌍도 아님 | None, `view_required`, detail `(("sense", 넷 tuple),)` |
| 5 | **미지수 넷 가운데 G 행이 모두 0인 넷이 있음**(DC 전도 경로 없는 용량 전용 노드, O-211 조건 (3)) | None, `icm_capacitive_only_node`, detail `(("nets", 넷 정렬 tuple),)` |
| 6 | 입력 포트 하나 | `"as_is_single_input"`. 보정 없음, 구동 = 그 포트. 피벗 두 칸은 기록(특이·레일 폭 0이면 None, 정의 불능 아님) |
| 7 | 입력 둘 | `"servo"`. 레일 폭 0·레일 값 없음·특이: None, `icm_servo_pivot_unresolved`, detail `(("rail_span", span),)` 또는 `(("singular", True),)`. \|a_e\|·span ≤ δV_out: 같은 code, detail `(("a_e", a_e), ("resolution", δA_num))` |

포트 role·회로 이름은 결과를 정하지 않는다. 입력 p/n 또는 출력 p/n을 맞바꾼 toy는 창·V_cm 칸이 같다. 선언 되먹임(`human.feedback`)은 읽지 않는다(선언 소자는 봉인점 회로 소자로 G에 든다). spec의 ICMR 기능 기준 칸을 읽지 않는다(O-215 임시).

**servo 감도(손 조립)**: 봉인점 DC 야코비안, W·바이어스 고정 KCL, 용량 개방, 고정 = ac 접지 ∪ 입력 넷. vx = 입력 포트 모두 1로 구동한 해, ve = 입력 p를 span·e_p로 구동한 해. c = 감지 벡터(단일 출력 e_out, 차동 출력 e_p − e_n). a_e = c·ve/span, s_n = vx_n − (ve_n/span)·(c·vx)/a_e. c·s = 0. θ 고정 감도가 아니고 follower도 아니다. 출력 꼴과 무관하다.

**경계 행**: 위 `region_rows` 행뿐. 경계 = VDS = VDSAT, **판정 여유 0**(O-204). 전도 행 없음(O-205 (3)). |VDS − VDSAT| < tol_VDsat 띠는 창 끝을 옮기지 않는다.

**창**: 이동량 [dlo, dhi] = 행 교집합. 끝 상태 레일 자름: s_p ≠ 0인 입력 포트마다 rail_min ≤ V_p0 + s_p·Δ ≤ rail_max로 [Δlo, Δhi]를 좁힌다. 포트 창 = V_p + s_p·Δlo, V_p + s_p·Δhi의 [min, max], s_p = 0이면 두 끝 = V_p. 행·감도·끝 가운데 하나라도 정의되지 않으면 모든 입력 포트 `"unmeasured"`. Δlo > Δhi이거나 건너뛴 행의 slack < 0이면 모든 입력 포트 `"unmeasured"`.

**V_cm 칸**: `vcm0` = 봉인점 입력 포트 전압 평균. 끝 상태 Δ의 V_cm = `vcm0` + s̄·Δ(s̄ = 입력 포트 감도 평균). `vcm_lo`·`vcm_hi` = 두 끝 상태 값의 min·max. s̄ = 0이면 둘 다 `vcm0`. 한 포트라도 `"unmeasured"`면 None. 차동쌍 기본 뷰면 s̄ = 1.

**구동 = 모든 입력 포트**: F 성분 미선언 포트도 구동에 든다. 입력 DC 둘 선언이면 같은 x로 함께 구동(포트별 훑기 아님).

**이어받기 없음**: 커널 `node.dc_window` 상태는 cfg·V_cm 칸에 영향 없음.

**판정 분해능(손 양 끝만)**: δV_out = Σ_u |z_u|·(|r_u| + Σ_j E_uj·|v_j|). z = 감지 관측의 수반 해, r = 풀이 잔차, E = `g_bound`, v = 구동 = 레일 폭 풀이. 판정 불능은 |c·v| ≤ δV_out.

### 정의 불능 code

- 낸다: `passive_value_undeclared`, `icm_inputs_unsupported`, `view_required`, `icm_capacitive_only_node`, `icm_servo_pivot_unresolved`.
- **없음**(결과 어디에든 나오면 red): `icm_inverting_port_none`·`_ambiguous`·`_unresolved`, `icm_config_differential_output_undeclared`·`_structure`, `icm_config_feedback_no_dc`·`_element_unsupported`·`_outputs_split`·`_cut`, `icm_config_output_root_w3`, `icm_view_ambiguous`, `icm_excite_common_mode`, `input_window_f_component_undeclared`, cfg 상태 `"f_component_undeclared"`·`"unsettled"`, `window_end_*`, 행 kind `"conduction"`, `off` 경계 행.

### 예외

- `StructureUnresolvedError`(`unsupported_rule_branch`): 지원 밖 원소·bulk 미정 MOS. 블록 `ss_circuit`이 낸다(detail 옛 `metrics_ss`와 같음, 실패 블록 이름만 바뀜).
- `ValueError`: `NodalSystem` ndarray 제자리 쓰기, `StampSet` 길이 불일치.
- `TypeError`: `Circuit` 키워드 누락, `kvl_sensitivity` `closure`.

### 단언 금지

`NodalSystem.factor` 내부 값, `input_version` 문자열 값, 분해능·`pivot_resolution`·`pivot_a_e` 수치(양 끝 toy만), S3 색인 내부, `ViewS1v`의 `default_port` 밖 칸 값 변화, `node.dc_window` 수치·상태(WB-1), 봉인 7·9 판정 여유와 `indistinct` 기록(card EO-1 §4.8-3), 13회로 값(유보).

## test 목록(규칙 H 1:1, 이름 접두 `test_it2c_`)

oracle: (손) 소자 스탬프 손 조립, (독립) AST·grep·READS, (식) 위 규칙.

| id | 위치 | 내용 | oracle | base |
|---|---|---|---|---|
| T-L8a | `tests/metrics/test_icm_config.py` | 되먹임 미선언 차동 입력·단일 출력 고임피던스 toy: cfg 끝 = 손 KCL servo 끝. test가 스탬프로 야코비안을 조립해 vx·ve·Schur 1칸을 푼다. 입력으로 읽는 것 = `device.ss_dev` gm·gds·gmb, `node.dc_v`, `device.dc_op` VGS·VDS·VSB·L·w_key. VDSAT = `gmid_engine.lut.vdsat(...)` 직접. 허용 = `device.dc_tol_v` dc_coord MOS 최솟값 손 계산(그 값 = cfg `tol_v`는 따로 단언). **기대 끝은 여유 0으로 유도**. 전제(어기면 무효): servo 끝 ≠ follower 손 끝, servo 끝 ≠ θ 손 끝(차 > 허용). 감지 slope = 0, `config == "servo"` | (손) | red |
| T-L8a′ | 같은 파일 | 여유 0 구별: 같은 toy에서 +tol_VDsat 행으로 낸 끝과 cfg 끝의 차 > 허용(전제), cfg 끝 = 여유 0 끝. +tol 끝이면 red | (손) | red |
| T-L8b | 같은 파일 | 차동 출력 toy 둘(되먹임 선언 없음·용량만 선언): 감지 V_op − V_on servo 끝 = 손계산, 두 toy 창·V_cm 같음 | (손) | red |
| T-L8c | 같은 파일 | KVL 고정 출력 toy(부하 저항 출력–레일)와 W3 목표 출력 toy: 부하 포함 KCL + servo 행 끝 = 손계산 | (손) | red |
| T-L8d | 같은 파일 | 저항 되먹임 선언 2입력 단일 출력 toy: `"servo"`, 창 = 같은 회로 servo 손계산. 단일 입력 + 선언: `"as_is_single_input"`(spec 로더가 받지 않으면 멈추고 보고) | (손) | red |
| T-L8e | 같은 파일 | 조립 상쇄 toy(a_e 설계상 0): None, `icm_servo_pivot_unresolved`. 전제: 옛 식 |z_u|ᵀ|r|로는 판정 가능. 기대 근거 = 정확 산술 참값 오차가 새 δV_out 안. 입력 셋·입력 0·2입력 비차동·출력 둘 비차동 toy는 위 표 code. role 맞바꿈 toy 같은 창. 선언 뷰 키가 기본과 달라도 창 = 기본 포트 뷰 손계산 | (손) | red |
| T-L8e′ | 같은 파일 | 용량 전용 노드 toy(넷이 커패시터와 MOS gate에만 닿음): None, `icm_capacitive_only_node`, 그 넷. 그 넷을 저항으로 이으면 정의됨 | (손) | red |
| T-L8f | 같은 파일(AST) | 비test 엔진 소스(docstring·주석 제외)에 `"declared_feedback"`·`"follower_beta1"`·`inverting_port`·`tied_ports`·위 '없음' code 전부(`"unsettled"` 제외 -- 빈칸 답 6)·`_dc_feedback_reaches`·`_conduction_rows`·`INPUT_STATUS_F_COMPONENT_UNDECLARED`·`writer_head`·`icmr_view`·`icm_view`·`dc_output_structure`·`_output_structure`·`dc_window_def` 0. `kvl_sensitivity` 서명에 `closure` 없음 | (독립) | red |
| T-L8g | 같은 파일 | V_cm 칸: 끝 = 같은 끝 상태 입력 전압 평균(손). 양수 감도 toy는 cfg 끝 평균과도 일치. 음수 감도 포트 toy: 손 평균(짝지은 평균이면 red, 전제 둘). 레일 자름 toy: 두 포트 끝과 V_cm 끝이 같은 끝 상태 | (손) | red |
| T-L8h | 같은 파일 | ICMR = 영역 행: 입력쌍 한쪽 전류가 먼저 줄어드는 toy에서 끝 = 영역 행 끝(전도 끝 아님). 경계 행 kind 집합 = {`"sat"`, `"triode"`}. `icm_config` READS에 전도 필드 0(READS 단언). `icmr_v`·`icm_margin_v` 값 판정은 IT-2d T-M | (손)+(독립) | red |
| T-D | `tests/metrics/test_icm_config.py`·`tests/sizing/test__helpers_dc_solve.py` | `triode` 선언 소자가 훑기 중 포화로 가는 toy: 행 영 교차 = cfg 끝(VDS = VDSAT, 여유 0). 전제: 동작점 triode. `region_rows` 소스에 VGS 상수 0 `op_point` 0, 전도 필드 읽기 0, EO-1 모듈 import 0(AST) | (손)+(독립) | red |
| T-P | `tests/metrics/test_icm_config.py`·`tests/sizing/test_input_window.py` | 음수 감도 포트 lo ≤ hi. 입력 DC 둘 선언: 일반 toy 끝 = servo 손계산, 대칭 toy(전제 둘)에서 포트 끝 차 = 선언 차. `saturation_window` 새 서명·`root` 하나·`slope` 갈래 | (손)+(식) | red |
| T-K | `tests/sizing/test_block_columns.py`·`test_icm_config.py` | 입력 DC 선언 toy: cfg 항목 `"measured"`, 커널 `node.dc_window` 입력 항목 없음. 미선언 2입력: 커널 뿌리 하나, cfg 두 포트. VDSAT 열 없는 LUT: cfg `"unmeasured"`. 행 교집합이 Δlo > Δhi인 합성 행: cfg `"unmeasured"`(양수 폭 창이면 red) | (손)+(독립) | red |
| T-L10 | `tests/metrics/test_ss_nodal.py`·`test_icm_config.py`·`test_ss_circuit.py`·`test__helpers_nodal.py`·`test_stamp_mos.py`·`test_stamp_two_terminal.py`·`test_records.py` | writer 하나씩. `bound=True` 키워드 호출 = `ss_nodal` 하나(AST, 빈칸 답 7), `ss_circuit(` 호출 = 블록 하나, `SsCircuit(` 생성 = 하나, `def _ss_of` 0, `kvl_sensitivity` 호출 자리 하나, θ 감도 호출 0. 결측 toy: 저항 / 용량만 / 둘 다. `def is_dc_conducting_passive` 1곳, 호출 = `ss_circuit`·`ss_nodal`. 불변 ndarray `ValueError`. `g_bound`만 다른 두 `NodalSystem`의 `fp_of` 다름. `g_ops` AST·항목 손 기대. `g_bound` 손 식(u = 2⁻⁵³). `graph.metrics_ss`·`metrics_aux` `value_fp` 비트 동일 | (손)+(독립) | red |
| T-L11c | `tests/metrics/test_ss_evaluate.py` | 같은 θ ss 재평가: `ss_circuit`(aux 요청이면 `ss_nodal`·`icm_config`)의 (computes, grafts, reuses) = (0, 1, 0) | (독립) | red |
| T-L12 | `tests/metrics/test_icm_config.py` | `k_max` 소진 커널 toy(전제: 봉인): cfg `"measured"`, V_cm 있음. F 성분 미선언 포트 toy(입력 = gate 전용 넷, source = gnd)와 2입력 변형: 함께 구동한 창 = 손계산, `node.dc_window` 항목 없음. READS에 `node.dc_window` 없음 | (손)+(독립) | red |
| T-S1V | `tests/graph/test_views.py` 또는 `test_s1v_build.py` | `build_s1v` 경유. 위 '기본 포트 뷰' 규칙 전부 | (손)+(식) | red |
| T-RN | `tests/metrics/test_ss_circuit.py` | 지원 밖 원소: `ss_circuit_field` 직접 호출에서 예외(빈칸 답 5) | (독립) | red(`ImportError`, 신규 함수) |
| T-RH | `tests/integration/test_stage_a_library.py` 또는 `tests/graph/test_s1v_build.py` | library 두 회로: 사실이 여전히 적용됨(`graph.applied_facts` 비지 않음, `structure_fact_stale` 0). 기대 사실 = 그 `structure.json` `facts` | (독립) | green(회귀 -- 재기록을 빼면 red) |
| T-E9 | `tests/sizing/test_writer_plan.py` | `node.dc_output_structure`·`OUTPUT_*`가 필드·어휘에 없음 | (독립) | red |

red 예상 목록 = 엔진 동작·트리를 보는 test. 새 키워드 직접 호출 `TypeError`는 red로 세지 않는다. `tests/graph/canon_graphs.py`의 helper 클래스 `Circuit`과 같은 파일에서 쓰면 별칭을 쓴다.

**쓰지 않는 옛 toy**(W5): 전도 행 R0 toy(옛 T-L8h), `off` 경계 toy, `triode` +tol 단언, 띠 거부·기록 toy(봉인 7 = card EO-1), E-22 단위 다른 행 toy(대상 소멸).

### green·기준선 공통 규칙(test 작성자 빈칸 답, 2026-11-04)

- **base green**: 표의 base 칸이 red여도 사례가 base에서 green이면, 그 사례가 옛 동작과 새 동작 모두에 성립하는 회귀 보호인지 확인하고 test는 유지한다. 그 사례는 red 예상 목록에서 빼고 판정자에게 나열한다. 사례 전체가 green이라 새 동작을 가르지 못하면 그 id에 red 사례가 하나는 남아야 한다.
- **회귀 기준선 fixture**(`tests/integration/fixtures/*`, NFR-4 덤프): test 작성자는 고치지 않는다. 판정자가 code 병합본에서 재측정하고 원인 칸을 적으며, 값 변화표는 O-225 보류 표지로 둔다(A-39). 재측정 전 그 test 실패는 판정 전 상태로 보고하고 통과로 세지 않는다.
- **폐기**: 정의가 바뀌어 전제가 깨진 test는 고치지 않고 지우며, 판정 기록 근거에 `retired_tests`(이름·사유)로 적는다. 판정자가 그 목록을 확인한다.
- 봉인 통과가 전제인 toy는 EO-1 전 봉인(봉인 7 +tol_VDsat, 봉인 9 I_off ≤ ε·ID)을 지나는 동작점을 쓴다. 입력쌍 전류가 먼저 줄어드는 꼴(T-L8h)은 봉인점이 아니라 훑기 끝 상태라 해당 없다.
- `Undefined` = `gmid_engine.metrics.Undefined(quantity, code, category, detail)`.
- `k1_undeclared_input_ports_both_have_windows`·`k2_non_root_port_window`는 IT-1에서 폐기됨, 이 card에서 cfg로 옮기는 대상은 나머지 항목.

## 고칠 기존 test(test 주체 몫, 승인 동작 변경 O-109·O-115·O-118·O-204·O-205, 약화 아님)

건수 = `scope_grep.txt`.

| 파일 | 일 |
|---|---|
| `tests/sizing/test_s2_values.py` | `DC_TABLE`에서 `dc_output_structure` 행(34 → 33), `SS_TABLE` 네 행, `OUTPUT_*`·`f_component_undeclared` 단언 삭제(합 8건) |
| `tests/metrics/test_ss_types.py:102-105` | `SS_WRITES` 정확 집합(5 → 8) |
| `tests/sizing/test_writer_plan.py` | OS test 삭제(23건 줄, 대체 = T-E9) |
| `tests/sizing/test_block_columns.py` | 커널 입력 포트 항목 단언을 cfg로, `region_rows`·`_Circuit` 12건 새 위치, tol 항 5건 기대를 여유 0으로 손 재유도, `f_component_undeclared` 3건 삭제 |
| `tests/sizing/test_input_window.py` | 새 서명, 쌍 roots 사례 삭제(18건), tol 3건 |
| `tests/metrics/test_ss_metrics.py`, `tests/metrics/test_ss_evaluate.py` | `graph.ss_circuit` 먼저 쓰는 픽스처, 블록 계수 |
| `tests/sizing/test_seal_saturation.py`·`test_size_and_seal_local.py` | **그대로**(봉인 7 +tol은 EO-1 전까지 유지) |

기대값을 현재 출력으로 붙여넣지 않는다.

## 판정 측정(audit)

| # | 측정 | 합격 |
|---|---|---|
| A1 | 위 test, red는 base assertion 실패 | PASS |
| A2 | 새 test 체계 전체 | IT-1 card D-1과 같은 기준 |
| A3 | G1~G7(writer 하나·새 cache 0·사본 칸 0·소비자 ≥ 1 또는 출력 전용), G-10·WP-10 | PASS, `dc_seal_7`과 `region_rows`의 VDSAT 같은 입력 재계산은 HC-S 배정으로 기록 + GL-1 병합 뒤 base에서 `ratchet.new` 0(새 키·수 증가 0). `block_columns.py` 쪽 줄어든 키는 판정자가 줄임. 행 추가로 통과시키면 `criteria_weakened`. |
| A4 | `graph.ss_nodal`·`ss_circuit`·`icm_config` 같은 입력 버전 computes 0 | PASS |
| A5 | **`rule_hash` 공통 규칙**(위임 A-33·A-34): rule 파일(`S1V_RULE_FILES` ∪ `STRUCTURE_RULE_EXTRA_FILES`)을 고치는 커밋은 같은 커밋에서 `assets/library/{current_reuse_telescopic_ota,nmcnr_amplifier}.structure.json`의 `rule_hash` 줄만 재기록한다. 재기록하지 않으면 사실이 `structure_fact_stale`로 조용히 안 쓰인다(fail-open). `git diff` 두 파일 = `rule_hash` 줄뿐, rule 파일을 고친 커밋 안, connectivity 변경 0, 값 비교 근거 기록(완료 (14)), T-RH·Stage A 두 회로 | PASS |
| A6 | 13회로 변화표(N6.6 (3)), 착수 실측 (a)(b)(d)(e), SPICE 다리 | **미완료(보류 다리)** -- 통과로 세지 않음 |
| A7 | 연기 시험(통합 병합 때): `graph.icm_config` 경로를 지나는 입력 둘 회로 + 단일 입력 또는 선언 회로 | 예외 없이 끝남 |
