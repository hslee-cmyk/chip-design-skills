# gmid_engine.sizing 동작 계약 (MOD4 GB7 DC 정본 풀이 + 봉인, test 작성용)

- 대상: `gmid_engine/sizing/` 공개 API(`gmid_engine.sizing.__all__`). test 는 `from gmid_engine.sizing import ...`,
  `from gmid_engine.graph import ...`, `from gmid_engine.authoring import ...`, `from gmid_engine.lut import ...`,
  `from gmid_engine.core import ...` 만 쓴다(파일 모듈 직접 import·`_` 이름 금지). 배치는 규칙 D(H):
  `gmid_engine/tests/sizing/test_<파일>.py`(지금은 docstring 만 있는 자리표 30개 -- 동작 test 는 독립 test 작성자 몫),
  9회로 교차는 `tests/integration/`, 불변식은 `tests/contracts/`.
- 근거: `_drafts/engine/design_gb7_dc_canonical.md`(이하 설계, DEC-88 개정본), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝
  '확정 사항'(최우선), 계획 N3.3~N3.6·N3.9·N3.14, DEC-08·31·32·60·61·64·70·87·88·95, core·lut·graph·authoring `CONTRACT.md`.
- 기대값은 test 쪽이 topology/spec JSON·LUT npz 를 직접 읽어 만든다(피검 함수로 기대값을 만들지 않는다). 11절 숫자는
  작성자 측 실행값(교차 확인용)이고 정본이 아니다.
- **master 기준**: lut r3(L = 앵커 이산 키, 다선형 보간, VDSAT 열 없음). r4(L bin 안 선형·Hermite·`vgs_for_current_density`)가
  들어오면 바뀌는 곳을 `[r4]` 로 표시했다.

---

## 0. 파일과 진입점 (구조 규칙 A~I, `_module_map.LAYERS["sizing"]`)

| 층 | 파일 | 진입점 / 종류 | 계산 블록(writer) |
|---|---|---|---|
| 0 | `s2_values.py` | 데이터 선언 모듈(값 형식·어휘·`S2_WRITERS`) | -- |
| 0 | `k_max.py` | `k_max` | -- |
| 1 | `_helpers_lut.py` | helper: `terminal_voltages`·`w_key_of`·`with_device`·`forward_point`·`tol_v_cell` | -- |
| 1 | `_helpers_seal.py` | helper: `judge`·`node_values` | -- |
| 1 | `dc_inputs.py` | `dc_inputs_from_spec` | -- |
| 1 | `fixed_point.py` | `gauss_seidel` | -- |
| 1 | `s2_lift.py` | `lift_s1` | -- |
| 1 | `theta_check.py` | `check_theta` | -- |
| 1 | `w0_rails.py` | `dc_rails` | `dc_rails` |
| 1 | `current_basis.py` | `dc_current_basis` | `dc_current_basis` |
| 1 | `writer_plan.py` | `dc_writer_plan` | `dc_writer_plan` |
| 1 | `scc_order.py` | `dc_scc_order` | `dc_scc_order` |
| 1 | `theta_schema.py` | `dc_theta_schema` | `dc_theta_schema` |
| 1 | `block_currents.py` | `dc_currents` | `dc_currents` |
| 1 | `block_lengths.py` | `dc_lengths` | `dc_lengths` |
| 1 | `seal_versions.py` | `seal_versions`(함수) | -- |
| 1 | `seal_writers.py` | `seal_writers`(함수) | -- |
| 1 | `seal_saturation.py` | `dc_seal_saturation` | `dc_seal_saturation` |
| 1 | `seal_report.py` | `dc_seal_report` | `dc_seal_report` |
| 2 | `block_columns.py` | `dc_columns` | `dc_columns` |
| 2 | `block_widths.py` | `dc_widths` | `dc_widths` |
| 2 | `kernel_context.py` | `build_kernel_context` | -- |
| 2 | `seal_tolerances.py` | `dc_tolerances` | `dc_tolerances` |
| 2 | `seal_node_conflict.py` | `dc_seal_node_conflict` | `dc_seal_node_conflict` |
| 2 | `seal_vgs_match.py` | `dc_seal_vgs_match` | `dc_seal_vgs_match` |
| 2 | `seal_kcl.py` | `dc_seal_kcl` | `dc_seal_kcl` |
| 2 | `seal_bulk_reverse.py` | `dc_seal_bulk_reverse` | `dc_seal_bulk_reverse` |
| 2 | `seal_kvl_branch.py` | `dc_seal_kvl_branch` | `dc_seal_kvl_branch` |
| 3 | `seal.py` | `seal_dc` | -- |
| 4 | `size_and_seal.py` | `size_and_seal` | -- |

계산 블록은 모두 core `compute_block`(core CONTRACT 6절)이다: 블록 함수는 선언 reads 투영 + 불변 extras 만 받고, 입력 버전 =
fp_of((이름, 코드 해시, 투영 지문)), 같으면 재사용(스냅샷 `is` 반환), 결과는 `snapshot.write` 로만 쓴다(열 교체 의미).
`stats()`·`reset_stats()` 로 calls·reuses·computes·recomputes_same_input 을 잰다.

## 1. 공개 흐름과 입력

```
inputs = dc_inputs_from_spec(load_sizing_spec(spec_path, topo, catalog))     # 사람 선언 투영
s1     = build_s1(topo, dict(inputs.supplies_v))                              # graph CONTRACT
ctx    = build_kernel_context(s1, inputs, LutAccess(memo, w_keys))             # S0 당 1회
ev     = size_and_seal(ctx, theta, parent=None)                                # θ 마다 -> DcEvaluation
```

### 1.1 `DcInputs(supplies_v, input_dc_v=None, node_targets=(), element_values=(), linear_devices=(), pending=())` -- frozen
- `supplies_v` ((레일, V), ...) / `input_dc_v` 입력 포트 공통 DC(V) 또는 None / `node_targets` ((넷, V), ...) W3 /
  `element_values` ((원소, 값 또는 None), ...) / `linear_devices` 소자 이름 tuple / `pending` ((경로, 결정 ID), ...).

### 1.2 `dc_inputs_from_spec(spec) -> DcInputs`
- `spec` 이 authoring `SizingSpecDoc` 이 아니면 `TypeError`.
- `supplies_v` = `spec.supplies_v` 그대로. `input_dc_v`: InputDc mode `net` -> `dict(spec.supplies_v)[net]`, `value` ->
  `value_v`, `engine`·`pending`(또는 None) -> None. `node_targets` = `spec.node_voltage_targets_v` 가 tuple 이면 그것, 아니면
  (PendingMark·None) (). `element_values` = `spec.element_values` 각 원소의 (name, mode == "value" 면 value 아니면 None).
  `linear_devices` = intended_region 이 tuple 일 때 region == `"linear"` 인 소자(이름순). `pending` = `spec.pending` 의
  (path, decision) 이름순 -- **결정 대기 칸은 '미선언'으로 투영하고 막지 않는다**(정지는 MOD10 몫, SPEC_CONTRACT 3절).

### 1.3 `LutAccess(memo, w_keys)` -- frozen, `__canonical__() = (memo.lut.fp, w_keys)`
- `memo` = lut `LutMemo`(graph 밖 유일 memo), `w_keys` = ((kind, w_key), ...) 레이아웃 전 사이징이 쓰는 폭 슬라이스.
- `require_immutable(LutAccess(...))` 통과(`__canonical__` 우선), `fp_of` = LUT 내용 지문 + w_keys 의 함수 -- memo 상태(캐시
  내용·상한)가 달라도 같은 지문. 그래서 블록 extras 로 넘겨도 입력 버전은 LUT 내용·슬라이스만 따른다.

### 1.4 `build_kernel_context(s1graph, inputs, lut) -> KernelContext`
- 인자 형식 위반 -> `TypeError`(s1graph 가 `S1Graph` 아님, inputs 가 `DcInputs` 아님, lut 가 `LutAccess` 아님).
- `supplies_declaration(dict(inputs.supplies_v), 레일 집합)`(graph) 위반 -> `SchemaRejectedError` 그대로.
  `fp_of(그 정규화 결과) != s1graph.key.supplies_v_fp` -> `ValueError`(S1 을 다른 supplies 로 만들었다).
- S1 MOS kind 마다 `w_keys` 에 kind 가 있고 `(kind, w_key)` 가 `memo.lut.slice_map` 에 있어야 한다 -> 아니면 `ValueError`.
- `node_targets` 넷이 S1 노드가 아니면 `ValueError`.
- 순서: `lift_s1` -> `dc_rails(supplies)` -> `dc_current_basis(이상 전류원 ((이름, 값 또는 None), ...) 이름순)` ->
  `dc_writer_plan(정렬 W3 넷 tuple, input_dc_v is not None)` -> `dc_scc_order` -> `dc_theta_schema(값 선언 DC 저항 이름 tuple)`.
  계획 블록의 `StructureUnresolvedError`·`InfeasibleTargetError` 는 그대로 전파(탐색 전 정지).
- `KernelContext(base, inputs, lut, schema, fixed_values, resistor_values, plan_versions)`:
  `fixed_values` = W3 목표 ∪ (input_dc_v 가 있으면 입력 포트마다 그 값, W3 가 우선) ((넷, V), ...) 이름순,
  `resistor_values` = 잎 가지치기되지 않은 저항 중 spec 값이 있는 것 ((이름, Ω), ...), `plan_versions` = 계획 블록 5개의
  ((writer, block_version), ...) (`dc_rails`, `dc_current_basis`, `dc_writer_plan`, `dc_scc_order`, `dc_theta_schema` 순).

### 1.5 `lift_s1(s1graph) -> GraphSnapshot`
- `S1_WRITERS` 권한표의 `S1Graph` 가 아니면 `TypeError`, S1 writer 중 돌지 않은 것이 있으면 `ValueError`.
- 결과 `writers == S2_WRITERS`. 모든 S1 필드 값이 원본과 같고 `block_version(w)` 가 원본과 같다(그래서 S1 블록을 이
  스냅샷에 다시 부르면 reuse). 레코드 객체는 원본과 공유하지 않는다(core 계약상 원시 생성 금지 -- 12절 O7).

## 2. S2 dc 필드 (권한표 `S2_WRITERS` = S1 권한표 전부 + 아래, 필드마다 writer 하나)

graph 레코드 key: `DC_KEY`(`"dc"`). 값은 모두 불변(frozen dataclass·tuple·float·None).

| (kind, field) | writer | 대상 레코드 | 값 |
|---|---|---|---|
| node.dc_rail_v | dc_rails | 레일 노드만 | float V |
| graph.dc_current_basis | dc_current_basis | DC_KEY | `CurrentBasis` |
| node.dc_writer | dc_writer_plan | 모든 노드 | `NodeWrite` |
| device.dc_coord | dc_writer_plan | 모든 MOS | `DeviceCoord` |
| graph.dc_scc_order | dc_scc_order | DC_KEY | tuple[`SccEntry`] 풀이 순서 |
| node.dc_column_nbrs | dc_scc_order | S1 기둥 내부 노드 | tuple[`ColumnNeighbor`] |
| graph.dc_theta_schema | dc_theta_schema | DC_KEY | `ThetaSchema` |
| device.dc_current | dc_currents | DC 원소 + 가지치기 저항 | float A(전도 방향 양수) |
| device.dc_drop_current | dc_currents | DC 저항 + 가지치기 저항 | float A |
| device.dc_L | dc_lengths | 모든 MOS | float m |
| node.dc_v | dc_columns | 레일 아닌 모든 노드 | float V |
| node.dc_path_values | dc_columns | 모든 노드 | tuple[`PathValue`] relation 순 |
| node.dc_window | dc_columns | W4 뿌리 노드 | `Window` |
| device.dc_ln_idu | dc_columns | 모든 MOS | float |
| graph.dc_scc_log | dc_columns | DC_KEY | tuple[`SccLog`] |
| device.dc_op | dc_widths | 모든 MOS | `DeviceOp` |
| device.dc_tol_v | dc_tolerances | 모든 MOS | float V 또는 None |
| device.dc_gm_bound | dc_tolerances | 모든 MOS | float S |
| graph.dc_seal_1/2/3/6/7/8 | dc_seal_node_conflict / vgs_match / kcl / bulk_reverse / saturation / kvl_branch | DC_KEY | `SealItem` |
| graph.dc_seal_report | dc_seal_report | DC_KEY | `SealReport` |

노드전압 정본: 레일 = `dc_rail_v`, 그 밖 = `dc_v`(한 노드에 둘 중 하나만 -- 봉인 5). 소자 VGS/VDS/VSB 는 저장 필드가 아니고
`DeviceOp` 는 노드전압 차의 파생이다(설정 API 없음, N3.4).

값 형식(모두 frozen dataclass, `s2_values`):
- `NodeWrite(tier, relation, element=None, known=None, y_key=None, order=0)` -- tier ∈ `TIER_W0..W4`("W0".."W4"),
  relation ∈ `REL_RAIL`·`REL_TARGET`·`REL_INPUT_DC`·`REL_VGS_GATE`·`REL_VGS_SOURCE`·`REL_RESISTOR`·`REL_TIE`·`REL_WINDOW`
  ("rail", "declared_target", "input_dc", "vgs_gate", "vgs_source", "resistor_drop", "input_tie", "free_window").
- `DeviceCoord(role, relation, partner=None)` -- role ∈ `COORD_WRITER`("writer")·`COORD_DEPENDENT`("dependent"), relation ∈
  `DEP_TREE`("tree", writer 전용)·`DEP_PARALLEL`("parallel_vgs")·`DEP_CYCLE`("cycle_vgs")·`DEP_FIXED`("fixed_vgs").
- `CurrentTerm(source, num, den)`, `CurrentBasis(ends, mos, free, fixed, rows, pruned, resistors)`(4.2).
- `ColumnNeighbor(rails, pred, succ, position, length)`, `SccEntry(index, nodes, cyclic, devices)`,
  `ThetaSchema(components)`, `Theta(values)`, `PathValue(relation, value)`, `Window(lo, hi, constraints)`,
  `SccLog(index, nodes, iterations, deltas, tol, k_max)`,
  `DeviceOp(kind, current, ln_idu, gm_id, L, W, vgs, vds, vsb, w_key, idu_forward)`,
  `SealItem(item, status, magnitude=None, tol=None, margin=None, devices=(), nodes=(), detail=())`, `SealReport(items, status)`,
  `SealedSnapshot(snapshot, report)`, `KernelContext(...)`(1.4), `DcEvaluation(snapshot, report, sealed=None)`.

## 3. 쓰기 계획 `dc_writer_plan(snapshot, target_nets, input_dc_declared)` (θ 무관)

reads: device.{element_class, is_diode, kind, pins}, node.{is_rail, port_direction}. writes node.dc_writer, device.dc_coord.

1. 고정 노드 F 와 writer: 레일 -> (W0, rail), `target_nets` -> (W3, declared_target), `input_dc_declared` 면 입력 포트
   (`port_direction == INPUT_DIRECTION`) -> (W2, input_dc). 우선순위 W0 > W3 > W2(이미 배정된 노드는 건너뜀).
2. G_vgs 엣지: MOS 마다 (gate, source), 저항(`element_class == passive`, kind `"resistor"`, **잎 가지치기된 저항 포함**)마다
   (t0, t1), `input_dc_declared` 가 거짓이면 F 밖 입력 포트(이름순)의 이웃 쌍마다 '같은 DC' 엣지. 커패시터·이상원은 엣지가 아님.
3. 엣지 순위 (같은 DC 엣지 < 저항 < diode MOS < 그 밖 MOS), 같은 순위는 원소 이름순. F 를 한 점으로 묶고 Kruskal 최소
   신장 숲. 트리 MOS = `DeviceCoord(writer, tree)`. 비트리 MOS = dependent: gate·source 가 둘 다 F 면 `fixed_vgs`, 같은 kind·
   같은 (gate, source) 의 트리 MOS 가 있으면 `parallel_vgs`(partner = 그 소자), 그 밖 `cycle_vgs`. 비트리 저항 ->
   `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, rule_branch `dc_resistor_cycle`, nets, devices = 저항).
4. 방향(BFS, 트리 엣지 인접 목록은 순위·이름순): F 넷 전부(이름순)에서 시작, 아직 안 쓴 끝 노드를 쓴다 -- 같은 DC 엣지 ->
   (W2, input_tie, known = 아는 쪽), 저항 -> (W2, resistor_drop, element, known), MOS 가 gate 를 쓰면 (W1 if is_diode else W2,
   vgs_gate, element, known = source), source 를 쓰면 (W2, vgs_source, element, known = gate).
5. F 없는 성분(G_vgs 넷 이름순으로 처음 만나는 미배정 넷의 성분): 성분 안 F 밖 입력 포트가 있으면 이름순 첫 포트를 뿌리,
   y 키 `INPUT_GROUP_KEY`("input_common_mode"), 없으면 이름순 첫 넷을 뿌리, y 키 = 그 넷. 뿌리 = (W4, free_window).
   그다음 뿌리에서 4 와 같은 BFS.
6. G_vgs 에 없는 남은 노드(이름순) = (W4, free_window, y_key = 넷).
7. `order` = 배정 순번(0부터, 1→4→5→6 순서). 모든 노드가 writer 하나를 받는다.

불변식(test 가 JSON 으로 셀 수 있는 것): MOS 수 = writer 수 + dependent 수; dependent 수 = G_vgs(F 를 한 점으로 묶은 다중
그래프, 엣지 = MOS·저항·같은 DC)의 순환수 = |E| − |V| + 성분 수(저항 비트리 0 일 때); W4 수 = F 없는 성분 수 + G_vgs 밖 노드 수.

## 4. θ 무관 계획 블록

### 4.1 `dc_rails(snapshot, supplies)` -- reads node.is_rail; writes node.dc_rail_v = 레일마다 float(supplies 값).

### 4.2 `dc_current_basis(snapshot, declared_sources)` -- 원소 단위 KCL
- reads device.{dc_nets, element_class, kind, pins}, node.is_rail, graph(`GRAPH_KEY`).dc_pruned.
- DC 원소 = `dc_nets` 가 None 아닌 원소 − 가지치기 원소. `ends` = (원소, from, to): nmos (d, s), pmos (s, d), 2단자 (t0, t1)
  (pins 의 단자 이름순) -- 양의 전류 = from -> to.
- 고정 = 원소가 이상원이고 kind `"current_source"` 이며 `declared_sources` 값이 None 아님 -> `fixed` ((이름, float), ...).
- 미지수 열 = 고정 밖 DC 원소(이름순). 레일 아닌 넷마다 KCL 행(from 이면 +1, to 이면 −1), 유리수 기약 행사다리꼴(열 왼쪽부터
  pivot). pivot 이 아닌 열 = `free`(θ 전류 성분). `rows` = (원소, (CurrentTerm, ...)): free·고정 원소는 자기 자신 ×1/1, pivot
  원소는 −(RREF 계수)를 free·고정 원소에 건 항(0 계수 생략).
- 고정값끼리 KCL 불일치(정확 유리수) -> `InfeasibleTargetError`(devices = 고정 원소, reason `declared_source_kcl_conflict`).
- 항이 하나도 없는 MOS(KCL 상 항상 0) -> `StructureUnresolvedError`(rule_branch `mos_zero_current_structural`).
- `mos` = MOS 원소, `pruned` = 가지치기 저항 이름순, `resistors` = DC 저항(가지치기 제외).
- `matching_ratio` 는 비율 선언이 없어 전류를 강제하지 않는다(미러 출력 전류도 free).

### 4.3 `dc_scc_order(snapshot)` -- 읽기 의존과 SCC
- reads node.dc_writer, device.{pins, bulk, element_class}, graph(S1).{columns, branches}.
- 의존(고정 relation rail/declared_target/input_dc 노드는 제외): vgs_gate = {source, drain, bulk 넷, known}, vgs_source =
  {gate(known), drain, bulk, 자기 자신}, resistor_drop·input_tie = {known}, free_window = 그 노드(입력 묶음 뿌리면 input_tie 로
  이어진 묶음 전원)에 d 또는 s 가 닿는 MOS 의 반대 채널 단자.
- Tarjan(반복형) SCC, 의존이 먼저인 순서 = 풀이 순서. `SccEntry.nodes` = order 순, `cyclic` = 크기 > 1 또는 자기 의존,
  `devices` = d·g·s 중 하나가 SCC 노드인 MOS 이름순.
- `dc_column_nbrs` = S1 `Column` 경로(r1 에서 걷기)마다 내부 노드의 (rails, pred, succ, position, length) -- 시작값 전용.

### 4.4 `dc_theta_schema(snapshot, declared_resistors)` -- `ThetaSchema(components)` 정렬
- (`ln_idu`, writer MOS), (`L`, 모든 MOS), (`y`, W4 y 키), (`current`, `free` 원소), (`resistance`, DC 저항 중
  `declared_resistors` 밖). `l_class` 관계는 status proposed 라 읽지 않는다 -> L 은 소자마다.

## 5. θ와 평가 블록

### 5.1 `check_theta(schema, values) -> Theta`
- `schema` 가 ThetaSchema 아님 -> `TypeError`. 키 집합 ≠ components -> `ValueError`(빠짐·남음 목록). 값이 bool·비실수·
  비유한 -> `ValueError`. `y` ∉ [0, 1], `L` ≤ 0, `resistance` ≤ 0 -> `ValueError`. 반환 = 키 정렬 (((kind, key), float), ...).

### 5.2 `dc_currents(snapshot, theta_currents)` -- reads graph.dc_current_basis
- `theta_currents` 키 집합 ≠ `free` -> `ValueError`. 원소 전류 = Σ (num/den)·전류(원천) (유리수로 합한 뒤 float).
- 어떤 MOS 전류 ≤ 0 -> `SealViolationError`(devices = 그 MOS들 이름순, margin None, reason `device_current_nonpositive`,
  detail `currents`).
- writes dc_current(+ 가지치기 저항 0.0), dc_drop_current(= dc_current 중 `resistors` ∪ `pruned`).

### 5.3 `dc_lengths(snapshot, theta_lengths)` -- reads device.element_class; 키 ≠ MOS 집합 -> `ValueError`; writes dc_L.

### 5.4 `dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)` -- 노드전압 정본
- reads node.{dc_writer, dc_rail_v, dc_column_nbrs}, device.{dc_drop_current, dc_L, pins, kind, bulk, element_class,
  dc_coord}, graph.dc_scc_order. `theta_items` = θ 중 ln_idu·y·resistance 성분.
- 부호 s = +1(nmos)/−1(pmos). 크기: vgs = s(V(g)−V(s)), vds = s(V(d)−V(s)), vsb = s(V(s)−V(b)).
- VGS(좌표) = lut `gm_id_for_target(memo, kind, w_key, L, vds, vsb, W = w_m, current = exp(ln_idu)·w_m/L).vgs`
  (w_m = 그 슬라이스 폭). `[r4]` `vgs_for_current_density` 로 바뀐다.
- writer 식: vgs_gate V(x) = V(known) + s·VGS / vgs_source V(x) = V(known) − s·VGS / resistor_drop V(x) = V(known) + Δ,
  Δ = 0 (전류 0), 아니면 known 이 t0 이면 −I·R, t1 이면 +I·R(I = dc_drop_current, R = θ 또는 선언값) / input_tie
  V(x) = V(known) / free_window V = lo + y·(hi − lo).
- 창 [lo, hi]: 레일 전압 범위 [min, max] 에서 시작, x(입력 묶음이면 묶음 전원)에 채널이 닿는 MOS 마다 전류가 나가는 단자
  (nmos d, pmos s)면 lo = max(lo, V(반대 단자)), 들어오는 단자면 hi = min(hi, V(반대 단자)). lo > hi -> `SealViolationError`
  (devices (), margin None, detail item 7·reason `empty_window`·node·lo·hi·constraints). **VDsat 항 없음**(12절 O1).
- SCC 순서대로: 비순환 -> 한 번 평가. 순환 -> 시작값(1단계: 기둥 위치 비례 평균 V(r1) + (V(r2) − V(r1))·position/length,
  기둥 없으면 레일 중앙; 2단계 order 순: MOS writer 는 VDS = 레일 범위/2, VSB = vgs_gate 면 현재값·vgs_source 면 0 에서 writer
  식 1회, 저항·같은 DC 는 writer 식, W4 그대로) 뒤 `gauss_seidel`(width = 레일 범위, devices = entry.devices, 허용오차 =
  SCC 의 writer MOS(없으면 d·s·bulk 값이 있는 entry.devices)의 `tol_v_cell` 최솟값; 모두 None -> `SealViolationError`
  reason `tol_v_undefined`).
- 종속 MOS: ln_idu = ln(op_point(노드 vgs, vds, vsb).IDu). writer: θ 값.
- path_values: MOS 마다 VGS(좌표 역산, 최종 vds·vsb) 로 gate 에 (`PATH_MOS`, m) V(s) + s·VGS, source 에 V(g) − s·VGS;
  resistor_drop writer 마다 두 끝에 (`PATH_RESISTOR`, r) 상대 끝 ± Δ; input_tie 마다 두 끝에 (`PATH_TIE`, 그 노드);
  free_window 에 (`PATH_Y`, y_key) 자기 값; 고정 relation 에 (`PATH_FIXED`, relation) 자기 값.
- LUT 실패는 `SealViolationError`(devices = 소자, reason `lut_query_failed`, `lut_reason` = 원래 사유(`lut_axis_out_of_range`·
  `lut_target_out_of_range`·`lut_l_not_anchor` …), `device_query` = "vgs_of_coordinate"·"forward_point"·"tol_v_cell"). 계속
  (근사·클램프)하지 않는다.

### 5.5 `gauss_seidel(nodes, values, update, tolerance, width, devices=()) -> (values, (k, deltas, tol, K_max))`
- 반복 k 마다 nodes 순서로 `update(node, current)` 를 바로 반영, Δk = 최대 |변화|, tol = `tolerance(current)`,
  K_max = `k_max(width, tol)`. Δk ≤ tol 이면 반환. 아니면 stop = (k ≥ K_max); k ≥ 3 이고 Δk−1 > 0 이면 q = Δk/Δk−1, q < 1 이면
  stop = stop or q^max(K_max − k, 0)·Δk/(1 − q) > tol. stop -> `NonconvergentError`(devices, margin = Δk/tol, detail nodes·
  iterations·deltas·tol·k_max). 입력 `values` 는 바꾸지 않는다.

### 5.6 `k_max(width, tol)` = ceil(log2(width/tol)), width ≤ tol 이면 1. 양의 유한 수가 아니면 `ValueError`.

### 5.7 `dc_widths(snapshot, lut)` -- `DeviceOp`
- reads node.{dc_v, dc_rail_v}, device.{dc_current, dc_L, dc_ln_idu, pins, kind, bulk}. MOS 마다 vgs·vds·vsb(크기),
  op = lut op_point(노드 점), W = ID·L/exp(ln_idu), gm_id = op.gm_over_id, idu_forward = op.IDu, w_key = `w_keys[kind]`.

## 6. 봉인 (`seal_dc(snapshot, calls, lut, resistances, linear_devices) -> DcEvaluation`)

순서: `dc_tolerances(lut)` -> 1 `dc_seal_node_conflict()` -> 2 `dc_seal_vgs_match()` -> 3 `dc_seal_kcl(resistances)` -> 6
`dc_seal_bulk_reverse()` -> 7 `dc_seal_saturation(linear_devices)` -> 8 `dc_seal_kvl_branch()` -> 4 `seal_versions(snapshot,
calls + 위 7개)` -> 5 `seal_writers(snapshot)` -> `dc_seal_report(item4, item5)`.

`judge(item, rows)`(rows = (대상, 크기, tol 또는 None, devices, nodes)): tol 이 정의된 행 중 크기 > tol 이 있으면 fail(대상 = 그
행들), 없고 tol None 행이 있으면 undefined(대상 = 그 행들), 그 밖 pass. magnitude·tol·margin = margin(크기/tol, tol 0 이면 무한)
최대 행(fail 이면 fail 행 중), 행이 없으면 None. detail = n_checked·n_undefined·worst(대상) 키 정렬.

| # | 블록 | 판정 |
|---|---|---|
| tol | `dc_tolerances` | dc_tol_v = lut `tol_v_table(kind, w_key).at(L, vds, "id_equivalent")`(None 가능), dc_gm_bound = max(gm_id_curve(L, vds, vsb) 의 id·gm/id)·W/w_m |
| 1 | `dc_seal_node_conflict` | 노드마다 spread = max − min of {노드 값} ∪ path_values; tol = 닿는 PATH_MOS 소자 tol_v 최댓값(정의된 것), 없으면 None; MOS 관계가 없는 노드는 n·eps·max|V|(n = 값 수) |
| 2 | `dc_seal_vgs_match` | MOS 마다 |ln idu_forward − ln_idu| / gm_id ≤ tol_v |
| 3 | `dc_seal_kcl` | 레일 아닌 넷마다 |Σ from − Σ to|, MOS = idu_forward·W/L, 저항 = (V(from) − V(to))/R, 이상원 = dc_current; tol = 채널이 닿는 MOS 의 tol_v·gm_bound 최댓값(정의된 것; MOS 는 있는데 모두 None 이면 None), MOS 없는 넷은 n·eps·Σ|I| |
| 4 | `seal_versions` | calls 의 블록마다 fp_of((이름, code_hash, Projection.from_snapshot(snapshot, reads, extras).fp)) == block_version 이고 그 블록 writes 필드의 input_version == block_version. 위반 블록 = detail `blocks`. magnitude = 위반 수, tol 0 |
| 5 | `seal_writers` | 모든 필드 writer == 권한표 writer; 노드마다 dc_writer 있음, (tier == W0) == is_rail, dc_rail_v·dc_v 중 정확히 하나, dc_rail_v 있음 == is_rail. 위반 노드 = nodes, 위반 필드 = detail `fields` |
| 6 | `dc_seal_bulk_reverse` | MOS 마다 max(0, −vsb, −(vds + vsb)) ≤ tol_v |
| 7 | `dc_seal_saturation` | 항상 undefined(reason `lut_vdsat_column_missing`), devices = current > 0 이고 linear_devices 밖인 MOS, n_checked = 그 수 |
| 8 | `dc_seal_kvl_branch` | S1 rel_kvl_branch 엣지마다 Σ_멤버 |ln idu_forward − ln_idu|/gm_id ≤ Σ 멤버 tol_v(하나라도 None 이면 None) |

`SealReport.status`: fail 있으면 `REPORT_VIOLATED`("violated"), 아니고 undefined 있으면 `REPORT_UNDEFINED`, 아니면
`REPORT_SEALED`. items = item 번호순 8개. 결과: violated -> `SealViolationError`(devices = margin 최대 fail 항목의 devices,
margin = 그 margin, detail = item·nodes·items((번호, 상태, margin) 8개)·item_detail). undefined -> `DcEvaluation(sealed=None)`.
sealed -> `DcEvaluation(sealed=SealedSnapshot(snapshot, report))`. **지금은 항목 7 이 항상 undefined 라 SealedSnapshot 이
나오지 않는다**(O1).

## 7. `size_and_seal(ctx, theta, parent=None) -> DcEvaluation`

- ctx 가 KernelContext 아님 -> `TypeError`. theta = Mapping 또는 `Theta` -> `check_theta`. parent 가 DcEvaluation 이 아니거나
  `plan_versions` 의 block_version 이 하나라도 다르면 `ValueError`.
- 시작 스냅샷 = parent.snapshot 또는 ctx.base. 호출 = `dc_currents((θ current 키, 값) ...)` -> `dc_lengths((L ...))` ->
  `dc_columns((((kind, key), v) for ln_idu·resistance·y), ctx.fixed_values, ctx.resistor_values, ctx.lut)` ->
  `dc_widths(ctx.lut)` -> `seal_dc(..., resistances = ctx.resistor_values + θ resistance 쌍, ctx.inputs.linear_devices)`.
- **재사용 계약**(확정 사항 1·5): 같은 θ·parent 로 부르면 모든 dc 블록 computes 0(reuses 12: 4 평가 + 7 봉인 + report).
  θ 한 성분만 다른 parent 에서: `current` 성분 -> dc_currents·dc_widths·dc_tolerances 와 그 하류 봉인만 다시(DC 저항 전류가
  바뀌지 않으면 dc_columns·봉인 1 은 reuse), `ln_idu`·`y`·`resistance` -> dc_columns 와 하류(dc_currents·dc_lengths reuse).
  하류 봉인 블록은 입력 값이 같으면 reuse(예: 값이 같은 SealItem 이면 dc_seal_report reuse).
- 후보 실패(`CANDIDATE_FAILURE_CLASSES`) = SealViolationError·NonconvergentError. ValueError·TypeError 는 호출 계약 위반.

## 8. 실패 규약 요약 (N3.14)

| 상황 | 시점 | 예외 | reason / detail | devices | margin |
|---|---|---|---|---|---|
| 비트리 저항 | 계획 | StructureUnresolvedError | unsupported_rule_branch / rule_branch dc_resistor_cycle | 저항 | None |
| KCL 상 0 전류 MOS | 계획 | StructureUnresolvedError | unsupported_rule_branch / mos_zero_current_structural | MOS | None |
| 선언 이상원 KCL 충돌 | 계획 | InfeasibleTargetError | declared_source_kcl_conflict | 고정 원소 | None |
| MOS 전류 ≤ 0 | ② | SealViolationError | device_current_nonpositive | MOS | None |
| W4 창이 빔 | ④ | SealViolationError | empty_window(item 7) | () | None |
| LUT 축 밖·목표 밖·앵커 아님 | ④⑤·tol | SealViolationError | lut_query_failed + lut_reason | 소자 | LUT 값(None) |
| 허용오차 셀 전부 미정 | ④ | SealViolationError | tol_v_undefined | SCC 소자 | None |
| 순환 블록 비수렴 | ④ | NonconvergentError | detail nodes·iterations·deltas·tol·k_max | SCC 소자 | Δk/tol |
| 봉인 위반 | 봉인 | SealViolationError | item·items·item_detail | 최악 항목 | 최악 margin |

## 9. 결정론

- 같은 doc·spec·LUT·θ 면 `size_and_seal(...).snapshot.fp` 가 같다(netlist 순서 섞기·`PYTHONHASHSEED` 무관 -- 이름순 tie-break만
  쓴다). 작성자 측 실측: generality `shuffle_order` seed 1~3 로 9회로 모두 node.dc_writer 동일, 통과 θ 가 있는 8회로는 dc_v 비트 동일.
- 이름 전단사에는 **불변이 아니다**: Kruskal·RREF·W4 뿌리의 마지막 tie-break 가 이름이라 쓰기 소자·θ 기저가 바뀐다(12절 O3).
  계획 구조 요약(티어·종속 관계 종류·SCC 크기·θ 종류 다중집합)도 seed 에 따라 6회로에서 달라진다(current_reuse·folded·nmcnr·
  pushpull·sf_pushpull·two_stage_ota_sf -- 쓰기 소자 선택과 W4 뿌리 선택이 이름순이라).

## 10. 9회로 실측 (2026-10-07, 이 커밋 코드, 작성자 측 시연 -- 정본 아님)

LUT = `_drafts/engine/lut_slices/manifest.json`(32 슬라이스) + `assets/sky130_nfet_pfet_lut_sample.npz`, w_keys = 용량 기준
폭(nmos·pmos 1000 = 5 µm, `cap_map[kind].basis` 의 w_key). spec = library `*.sizing_spec.json`(결정 대기 칸은 미선언 투영).
탐침 θ(탐색 아님): L = 1 µm 앵커, writer ln IDu = gm/ID {8, 12, 16, 20, 24} 점(VDS = 레일 범위/2, VSB 0), y ∈ {0.25, 0.5, 0.75},
전류 LP(최소 MOS 전류 최대화, 1~100 µA) + 무작위 200개(writer gm/ID U[6, 26], y U[0.05, 0.95], 전류 log-U[1, 100] µA·KCL 양수,
R log-U[100 Ω, 100 kΩ]) = 회로당 215 θ.

| 회로 | θ 차원 (L/ln_idu/current/y/R) | 티어 W0/W1/W2/W4 | 종속(parallel/cycle) | 순환 SCC 크기 | 일관 DC 점 | 대표 실패 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | 9 (3/3/1/2/0) | 2/0/3/2 | 0/0 | [2] | 184/215 | NONCONVERGENT 25 (W4–W4 창 결합) |
| current_reuse_telescopic_ota | 105 (51/29/22/1/2) | 2/13/21/1 | 15/7 | [4, 4, 2, 1×16] | 0/215 | lut_query_failed M18b VDS<0 103, M37b VSB<0 50, M58 32 |
| folded_cascode | 29 (13/8/5/3/0) | 2/4/5/3 | 4/1 | [4, 1×5] | 18/215 | lut_query_failed M8 128 |
| ngcc_3stage_ff | 35 (16/8/9/2/0) | 2/3/6/2 | 7/1 | [1×4] | 96/215 | lut_query_failed M1 VSB<0 113 |
| nmcnr_amplifier | 36 (15/11/8/2/0) | 2/2/12/2 | 3/1 | [2, 1×3] | 54/215 | lut_query_failed M102 117 |
| pushpull_follower_buffer | 14 (6/5/3/0/0) | 3/0/6/0 | 0/1 | [1, 1] | 7/215 | lut_query_failed M3 VDS>1.8 125, M6 72 |
| sf_pushpull_output_opamp | 47 (22/14/7/1/3) | 3/1/18/1 | 6/2 | [3, 3, 1×8] | 1/215 | lut_query_failed M14 79 |
| two_stage_ota | 16 (7/4/3/2/0) | 2/1/5/2 | 2/1 | [1, 1] | 105/215 | lut_query_failed M1 VSB<0 97 |
| two_stage_ota_sf | 20 (9/5/4/2/0) | 2/1/5/2 | 3/1 | [1, 1, 1] | 63/215 | lut_query_failed M1 103 |

'일관 DC 점' = 봉인 1·2·3·4·5·6·8 pass, 7 undefined(`REPORT_UNDEFINED`). 계획 단계 정지 0/9. 첫 통과 점의 최대 margin:
봉인 1 0.0~0.38, 봉인 2 0.0~0.27, 봉인 3 0.0~0.05, 봉인 8 ≤ 0.08. 포화(봉인 7)는 판정하지 않았으므로 '일관'은 포화를
뜻하지 않는다(예: two_stage_ota 통과 점 tail CS = 0.061 V).

### 10.1 재사용·시간 (FD 스윕: L 밖 θ 성분마다 +δ 한 번, parent = 기준점)
- 같은 θ + parent: dc 블록 computes 0, reuses 12(4회로). FD 스윕 recomputes_same_input: two_stage·folded·nmcnr 0,
  sf_pushpull 5(dc_seal_node_conflict 3·dc_seal_report 2 -- 서로 다른 θ 섭동이 같은 저항 전류 변화를 만들어 형제 평가 사이 입력이
  같아진 경우, 다른 lineage 라 재사용 경로가 없다 -- O8).
- 계측 없는 평가 1회: two_stage 37 ms, folded 73 ms, nmcnr 61 ms, sf_pushpull 105 ms(FD, parent 재사용). 첫 평가(parent 없음)
  29/52/58/84 ms. build_s1 30~60 ms, build_kernel_context 24~52 ms. tol_V 표는 LUT derived memo 로 프로세스당 kind 마다 1회
  (~14 s/kind, lut CONTRACT 5절).
- cProfile(sf_pushpull FD 25회, 10.8 s 계측 포함): core `fp_of` 65%(투영 지문 `Projection.from_snapshot` 44%, `GraphSnapshot.write`
  25%), `seal_versions` 22%(투영 지문 재계산), `gm_id_for_target` 24%. LUT memo 퇴출 0, 퇴출 뒤 재계산 0.
- 중복 인자 호출(sf FD 25회): op_point 718 호출/125 고유, gm_id_for_target 1470/334, gm_id_curve 550/119 -- 중복은 전부 LUT memo
  hit(계산 0). `TolVTable.at` 1264/243 은 memo 밖 표 조회(O9).

## 11. 설계와 다르게 정한 점

1. **저장 = core GraphSnapshot 하나**: 설계 2.1 `DcField`·`setter.py`·`field_reuse.py`·`writer_table.py` 대신 core 의
   `FieldValue`·`GraphSnapshot.write`·`compute_block`·`WriterTable` 을 그대로 쓴다(같은 개념 두 정의 금지). S1 과 같은 스냅샷에
   산다(`lift_s1`, 권한표 `S2_WRITERS`).
2. **SCC 필드 단위 재사용 대신 블록 단위**: core `write` 는 열 교체라 SCC 마다 같은 필드에 부분 쓰기를 할 수 없다 -> `dc_columns`
   한 블록. 바뀌지 않은 SCC 의 LUT 조회는 memo hit. 전류만 바뀐 θ 는 `dc_drop_current` 분리로 노드전압 블록 자체를 건너뛴다.
3. **1변수 SCC 도 Gauss-Seidel**(설계 3.4 는 bisection). 같은 q·K_max 규칙. 시작값 2단계(5.4).
4. **W4 창 = 인접 전도 MOS 순서 제약**(설계 3.4 는 기둥 VDsat 합). S1 기둥은 노드-단순 경로라 전류 방향을 거스르는 경로를 포함해
   창이 뒤집혔다(nmcnr NodeF1 실측). VDsat 항 없음(O1).
5. **봉인 4·5 는 함수**(메타데이터를 읽어야 해서 투영 기반 계산 블록으로 쓸 수 없다), 결과는 `dc_seal_report` 의 extras 로 graph 에 든다.
6. **봉인 2·3·8 은 `dc_op.idu_forward` 를 읽는다**: 순방향 조회를 `dc_widths` 에서 한 번만 한다(설계는 항목마다 lut.query).
7. **봉인 8 = 멤버 ID 환산 차의 절대값 합**(부호 있는 잔차의 상계), 봉인 1 tol = 관계 소자 tol 최댓값, KCL tol_I = 노드 단위.
8. **core 계층 수학(bisect_root·fixed_point_iter·k_max)은 sizing 에** 둔다: 소비자가 sizing 하나뿐(배선 원칙). 층 0 국소
   고정점(DEC-71 (4)(d))이 생기면 core 로 옮긴다.
9. **L 은 소자마다 θ**(`l_class` proposed 라 평가 경로가 읽지 않음, N3.3).
10. 파일 이름: `seal/item*_*.py` 대신 `seal_<항목>.py`(하위 폴더 없이), `size_and_seal` 의 θ 검사는 `theta_check.py`.

## 12. 열린 질문 (결정 필요 -- 추측으로 채우지 않았다)

- **O1 VDSAT 열 부재(U-27)**: 봉인 7 은 항상 undefined -> SealedSnapshot 0. W4 창에 VDsat 항이 없어 W4 노드가 인접 소자를 선형
  영역에 둘 수 있다. 열이 생기기 전 '일관 DC 점(봉인 7 미정)'을 탐색 층이 후보로 받을지(지금: `DcEvaluation(sealed=None)`).
- **O2 레이아웃 전 폭 슬라이스**: 지금 w_keys = 용량 기준 폭(5 µm). 설계는 셀 = (kind, w_key, L, VDS)만 말하고 사이징 단계의 w_key
  선택 규칙이 없다(E5 finger_w 는 MOD7 몫). 소자별 선택이 필요한지.
- **O3 DEC-95 (3) 구조 우선순위 ②③**(GB5 gm 요구·뒤 stage·대칭 궤도): S1v·GB5 가 없어 diode → 이름만 적용. 이름 전단사 시
  9회로 중 8회로가 seed 1·2 중 적어도 하나에서 쓰기 소자 집합이 바뀐다(대칭차 2~8개, common_gate 만 불변). front 정규화 해시 metamorphic(DEC-95)은 탐색이 생긴 뒤 확인 가능.
- **O4 F 없는 G_vgs 성분 뿌리**: 입력 포트가 없으면 이름순 첫 노드를 W4 로 둔다(설계 3.1 3) -- 구조 규칙으로 고를지.
- **O5 결정 대기 입력 DC(SP-2, 7회로)**: U2 기본안 (a)대로 W4(입력 공통모드 y)로 풀었다. 노드 목표(CI-15)·의도 영역(CI-18)은
  9회로 모두 결정 대기 -> W3 0개, 선형 선언 0개.
- **O6 θ 전류 정의역**: MOS 전류 ≤ 0 은 margin 없는 후보 실패다. 탐색 bounds/부등식 제약으로 둘지(설계 미정).
- **O7 core 권한표 확장 API**: `lift_s1` 이 S1 필드를 setter 로 다시 써서 레코드 구조 공유가 없다(S0 당 1회 비용).
- **O8 형제 lineage 재계산**: FD 형제 평가끼리 같은 입력은 재계산된다(graph 가 곧 캐시라 다른 lineage 값을 볼 길이 없음).
- **O9 성능**: 시간의 65% 가 core 투영 지문(`fp_of` 재직렬화). `FieldValue.value_fp` 가 이미 있으므로 투영 지문을 (key, value_fp)
  로 만들면 블록 호출·봉인 4 모두 줄어든다 -- core 변경이라 승인 필요. `TolVTable.at` 중복 조회는 memo 밖.
- **O10 고정점 과도 상태**: Gauss-Seidel 반복 중 LUT 축 밖으로 나간 반복값이 후보 실패로 기록될 수 있다(수렴 가능한 θ 를
  거부할 위험). 1변수 SCC 를 설계대로 창 안 bisection 으로 바꿀지, 축 경계 투영을 둘지(클램프 금지 원칙과 충돌) 결정 필요.
- **O11 W4–W4 결합 비수렴**: 인접 W4 두 노드의 창이 서로를 읽으면 선형 수축비 y1(1 − y2) 가 1 에 가까울 때 K_max 안에 못
  들어와 NONCONVERGENT(common_gate 25/215). 설계 규칙('bisection 보다 느린 고정점 = 비수렴') 그대로의 결과다.
