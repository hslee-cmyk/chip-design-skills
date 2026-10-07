# gmid_engine.sizing 동작 계약 (MOD4 GB7 DC 정본 풀이 + 봉인, test 작성용)

- 대상: `gmid_engine/sizing/` 공개 API(`gmid_engine.sizing.__all__`). test 는 `from gmid_engine.sizing import ...`,
  `from gmid_engine.graph import ...`, `from gmid_engine.authoring import ...`, `from gmid_engine.lut import ...`,
  `from gmid_engine.core import ...` 만 쓴다(파일 모듈 직접 import·`_` 이름 금지). 배치는 규칙 D(H):
  `gmid_engine/tests/sizing/test_<파일>.py`(지금은 docstring 만 있는 자리표 33개 -- 동작 test 는 독립 test 작성자 몫),
  9회로 교차는 `tests/integration/`, 불변식은 `tests/contracts/`.
- 근거: `_drafts/engine/design_gb7_dc_canonical.md`(이하 설계, DEC-88 개정본), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝
  '확정 사항'(최우선), 계획 N3.3~N3.6·N3.9·N3.14, DEC-08·31·32·60·61·64·70·87·88·95, core·lut·graph·authoring `CONTRACT.md`.
- 기대값은 test 쪽이 topology/spec JSON·LUT npz 를 직접 읽어 만든다(피검 함수로 기대값을 만들지 않는다). 11절 숫자는
  작성자 측 실행값(교차 확인용)이고 정본이 아니다.
- **master 기준**: lut r3(L = 앵커 이산 키, 다선형 보간, VDSAT 열 없음). r4(L bin 안 선형·Hermite·`vgs_for_current_density`)가
  들어오면 바뀌는 곳을 `[r4]` 로 표시했다.
- **개정 r2(2026-10-07, 오케스트레이터 결정 -- 열린 질문 O1·O2·O4·O5·O7 처리)**: 바뀐 곳에 `[r2]`. 요지 -- 이름 tie-break 를
  구조 색(1-WL) 키 뒤로 미루고 남은 동률을 `TieBreak` 로 기록(3·4.0·4.2절), θ 전류 정의역 = 전류 원뿔(4.4·5.1·5.2), 1변수 노드
  = 구간 bisection + 다변수 SCC 반복 중 투영·수렴 뒤 strict 검증(5.4·5.5), 레이아웃 전 폭 = LUT 생성 규칙 폭(1.3), 봉인 7 은
  VDSAT 접근자가 생길 때까지 미정 유지(6절·12절 O1).
- **개정 r3(2026-10-08, 독립 test 작성자 보고 반영)**: `[r3]`. judge 의 tol 0 margin = +inf(코드를 계약에 맞춤), 계약에 calls 형식·
  봉인 8 worst 이름·봉인 3 행 범위·margin 동률 규칙·`Window.constraints` 뜻·실패 최소 구성을 명시. S2 dc 필드는 r2 그대로
  28개(+ S1 필드).

---

## 0. 파일과 진입점 (구조 규칙 A~I, `_module_map.LAYERS["sizing"]`)

| 층 | 파일 | 진입점 / 종류 | 계산 블록(writer) |
|---|---|---|---|
| 0 | `s2_values.py` | 데이터 선언 모듈(값 형식·어휘·`S2_WRITERS`) | -- |
| 0 | `k_max.py` | `k_max` | -- |
| 0 | `bisect_root.py` [r2] | `bisect_root` | -- |
| 1 | `pre_layout_widths.py` [r2] | `pre_layout_lut_access` | -- |
| 1 | `struct_colour.py` [r2] | `dc_struct_colour` | `dc_struct_colour` |
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
ctx    = build_kernel_context(s1, inputs, pre_layout_lut_access(memo))         # S0 당 1회
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
- [r2] **레이아웃 전 폭 규칙** `pre_layout_lut_access(memo) -> LutAccess`: kind 마다 w_key =
  round(`memo.lut.cap_map[kind].w_ref_m` / `memo.lut.spec.manufacturing_grid_m`) -- LUT 생성 규칙 폭(기준 LUT 의 폭·확산 기하,
  계획 DEC-91 (2) '레이아웃 전 첫 사이징점은 LUT 생성 규칙의 확산 기하', lut CONTRACT 1.4 `w_ref_m`). kind 는 `cap_map` 키
  정렬. 그 (kind, w_key) 슬라이스가 `slice_map` 에 없으면 `ValueError`. 실데이터에서 nmos·pmos 모두 1000(5 µm). 레이아웃 뒤
  실현 폭 슬라이스는 DEC-89 재평가 몫(이 함수 밖).

### 1.4 `build_kernel_context(s1graph, inputs, lut) -> KernelContext`
- 인자 형식 위반 -> `TypeError`(s1graph 가 `S1Graph` 아님, inputs 가 `DcInputs` 아님, lut 가 `LutAccess` 아님).
- `supplies_declaration(dict(inputs.supplies_v), 레일 집합)`(graph) 위반 -> `SchemaRejectedError` 그대로.
  `fp_of(그 정규화 결과) != s1graph.key.supplies_v_fp` -> `ValueError`(S1 을 다른 supplies 로 만들었다).
- S1 MOS kind 마다 `w_keys` 에 kind 가 있고 `(kind, w_key)` 가 `memo.lut.slice_map` 에 있어야 한다 -> 아니면 `ValueError`.
- `node_targets` 넷이 S1 노드가 아니면 `ValueError`.
- 순서: `lift_s1` -> `dc_rails(supplies)` -> [r2] `dc_struct_colour()` -> `dc_current_basis(이상 전류원 ((이름, 값 또는 None), ...) 이름순)` ->
  `dc_writer_plan(정렬 W3 넷 tuple, input_dc_v is not None)` -> `dc_scc_order` -> `dc_theta_schema(값 선언 DC 저항 이름 tuple)`.
  계획 블록의 `StructureUnresolvedError`·`InfeasibleTargetError` 는 그대로 전파(탐색 전 정지).
- `KernelContext(base, inputs, lut, schema, fixed_values, resistor_values, plan_versions)`:
  `fixed_values` = W3 목표 ∪ (input_dc_v 가 있으면 입력 포트마다 그 값, W3 가 우선) ((넷, V), ...) 이름순,
  `resistor_values` = 잎 가지치기되지 않은 저항 중 spec 값이 있는 것 ((이름, Ω), ...), `plan_versions` = 계획 블록 6개의
  ((writer, block_version), ...) (`dc_rails`, `dc_struct_colour`, `dc_current_basis`, `dc_writer_plan`, `dc_scc_order`,
  `dc_theta_schema` 순).

### 1.5 `lift_s1(s1graph) -> GraphSnapshot`
- `S1_WRITERS` 권한표의 `S1Graph` 가 아니면 `TypeError`, S1 writer 중 돌지 않은 것이 있으면 `ValueError`.
- 결과 `writers == S2_WRITERS`. 모든 S1 필드 값이 원본과 같고 `block_version(w)` 가 원본과 같다(그래서 S1 블록을 이
  스냅샷에 다시 부르면 reuse). 레코드 객체는 원본과 공유하지 않는다(core 계약상 원시 생성 금지 -- 12절 O7).

## 2. S2 dc 필드 (권한표 `S2_WRITERS` = S1 권한표 전부 + 아래, 필드마다 writer 하나)

graph 레코드 key: `DC_KEY`(`"dc"`). 값은 모두 불변(frozen dataclass·tuple·float·None).

| (kind, field) | writer | 대상 레코드 | 값 |
|---|---|---|---|
| node.dc_rail_v | dc_rails | 레일 노드만 | float V |
| node.dc_colour [r2] | dc_struct_colour | 모든 노드 | int 구조 색 |
| device.dc_colour [r2] | dc_struct_colour | 모든 원소 | int 구조 색 |
| graph.dc_current_basis | dc_current_basis | DC_KEY | `CurrentBasis` |
| node.dc_writer | dc_writer_plan | 모든 노드 | `NodeWrite` |
| device.dc_coord | dc_writer_plan | 모든 MOS | `DeviceCoord` |
| graph.dc_tie_breaks [r2] | dc_writer_plan | DC_KEY | tuple[`TieBreak`] |
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
- `CurrentTerm(source, num, den)`, `CurrentBasis(ends, mos, free, fixed, rows, pruned, resistors, ties)`(4.2).
- [r2] `TieBreak(decision, candidates, chosen)` -- decision ∈ `TIE_KRUSKAL`("writer_edge")·`TIE_ROOT`("w4_root")·
  `TIE_INPUT_ORDER`("input_tie_order")·`TIE_CURRENT_PIVOT`("current_pivot"), candidates·chosen 이름순 tuple.
- `ColumnNeighbor(rails, pred, succ, position, length)`, `SccEntry(index, nodes, cyclic, devices)`,
  `ThetaSchema(components, current_cone=(), fixed=())`, `Theta(values)`, `PathValue(relation, value)`, `Window(lo, hi, constraints)`,
  `SccLog(index, nodes, iterations, deltas, tol, k_max)`,
  `DeviceOp(kind, current, ln_idu, gm_id, L, W, vgs, vds, vsb, w_key, idu_forward)`,
  `SealItem(item, status, magnitude=None, tol=None, margin=None, devices=(), nodes=(), detail=())`, `SealReport(items, status)`,
  `SealedSnapshot(snapshot, report)`, `KernelContext(...)`(1.4), `DcEvaluation(snapshot, report, sealed=None)`.

## 3.0 [r2] 구조 색 `dc_struct_colour(snapshot)` (θ 무관) -- 이름 없는 정준 tie-break 키

reads device.{element_class, kind, is_diode, pins, bulk}, node.{is_rail, port_direction}; writes node.dc_colour,
device.dc_colour.
- 그래프: 정점 = 노드 ∪ 원소, 엣지 = 원소–넷 연결에 라벨: MOS `d`·`g`·`s`, bulk 넷이 있으면 `b`, 이상 전류원 `t0`·`t1`(방향
  있음), 그 밖 2단자(저항·커패시터 …) `t`(방향 없음).
- 처음 서명: 원소 ("e", element_class, kind, bool(is_diode)), 노드 ("n", bool(is_rail), port_direction 또는 "").
- 정제(1-WL): 서명 = (옛 색, ((라벨, 이웃 옛 색), ...) 정렬). 색 = 서명 집합을 정렬한 순위(0부터 int). 색 종류 수가 늘지 않는
  회에서 멈춘다(그 회 직전 색을 쓴다). 상수 없음.
- 성질(test 가 확인할 것): 이름 전단사·원소/키 순서 섞기를 해도 색 함수가 그 전단사로 옮겨진다(같은 정점 → 같은 색). 같은
  색 = 1-WL 로 구별 안 되는 정점.
- **동률 논증**: 같은 색 후보 사이 선택이 자기동형(전단사 σ 가 연결·kind·레일·포트 방향을 보존)으로 대응하면, 한쪽을 고른 계획과
  다른 쪽을 고른 계획은 σ 로 서로 옮겨지고 θ 를 σ 로 옮기면 노드전압·소자 op 가 σ 로 옮겨진 값이 된다(엔진이 이름을 읽는 곳은
  남은 동률 깨기뿐이라). 1-WL 은 완전하지 않아(정규 그래프류) 같은 색이 자기동형이 아닐 수 있다 -- 그래서 이름이 실제로 결정을
  가른 경우는 전부 `TieBreak` 로 기록한다(3절·4.2절). 기록이 없는 결정은 이름과 무관하다.

## 3. 쓰기 계획 `dc_writer_plan(snapshot, target_nets, input_dc_declared)` (θ 무관)

reads: device.{element_class, is_diode, kind, pins, dc_colour}, node.{is_rail, port_direction, dc_colour}.
writes node.dc_writer, device.dc_coord, graph.dc_tie_breaks. [r2] 모든 정렬 키 = (구조 색, 이름) -- 이름은 같은 색 안에서만.

1. 고정 노드 F 와 writer: 레일 -> (W0, rail), `target_nets` -> (W3, declared_target), `input_dc_declared` 면 입력 포트
   (`port_direction == INPUT_DIRECTION`) -> (W2, input_dc). 우선순위 W0 > W3 > W2(이미 배정된 노드는 건너뜀).
2. G_vgs 엣지: MOS 마다 (gate, source), 저항(`element_class == passive`, kind `"resistor"`, **잎 가지치기된 저항 포함**)마다
   (t0, t1), `input_dc_declared` 가 거짓이면 F 밖 입력 포트를 (색, 이름) 순으로 놓고 이웃 쌍마다 '같은 DC' 엣지(같은 색 포트가
   둘 이상이면 `TieBreak(input_tie_order, 그 포트들, 그 포트들)`). 커패시터·이상원은 엣지가 아님.
3. 엣지 키 = (순위: 같은 DC 엣지 < 저항 < diode MOS < 그 밖 MOS, 원소 구조 색, 이름). F 를 한 점으로 묶고 Kruskal 최소
   신장 숲. 같은 (순위, 색) 원소 묶음이 트리/비트리로 갈리면 `TieBreak(writer_edge, 묶음, 트리로 간 원소들)`(묶음을 다 처리한
   뒤의 성분 분할은 묶음 안 순서와 무관하므로 이름이 가르는 것은 그 묶음 안의 선택뿐이다). 트리 MOS = `DeviceCoord(writer, tree)`. 비트리 MOS = dependent: gate·source 가 둘 다 F 면 `fixed_vgs`, 같은 kind·
   같은 (gate, source) 의 트리 MOS 가 있으면 `parallel_vgs`(partner = 그 소자), 그 밖 `cycle_vgs`. 비트리 저항 ->
   `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, rule_branch `dc_resistor_cycle`, nets, devices = 저항).
4. 방향(BFS, 트리 엣지 인접 목록은 (순위, 색, 이름)순): F 넷 전부((색, 이름)순)에서 시작, 아직 안 쓴 끝 노드를 쓴다 -- 같은 DC 엣지 ->
   (W2, input_tie, known = 아는 쪽), 저항 -> (W2, resistor_drop, element, known), MOS 가 gate 를 쓰면 (W1 if is_diode else W2,
   vgs_gate, element, known = source), source 를 쓰면 (W2, vgs_source, element, known = gate).
5. F 없는 성분(G_vgs 넷을 (색, 이름)순으로 훑어 처음 만나는 미배정 넷의 성분): 성분 안 F 밖 입력 포트가 있으면 그중 (색, 이름)
   최소를 뿌리, y 키 `INPUT_GROUP_KEY`("input_common_mode"), 없으면 성분 노드 중 (색, 이름) 최소를 뿌리, y 키 = 그 넷.
   뿌리와 같은 색인 후보가 둘 이상이면 `TieBreak(w4_root, 그 후보들, (뿌리,))`. 뿌리 = (W4, free_window). 그다음 4 와 같은 BFS.
6. G_vgs 에 없는 남은 노드((색, 이름)순) = (W4, free_window, y_key = 넷).
7. `order` = 배정 순번(0부터, 1→4→5→6 순서). 모든 노드가 writer 하나를 받는다. order 의 같은 색 안 이름 순서는 SCC 안 갱신
   순서·시작값에만 쓰이고 수렴값(허용오차 안)을 바꾸지 않으므로 기록하지 않는다.

불변식(test 가 JSON 으로 셀 수 있는 것): MOS 수 = writer 수 + dependent 수; dependent 수 = G_vgs(F 를 한 점으로 묶은 다중
그래프, 엣지 = MOS·저항·같은 DC)의 순환수 = |E| − |V| + 성분 수(저항 비트리 0 일 때); W4 수 = F 없는 성분 수 + G_vgs 밖 노드 수.

## 4. θ 무관 계획 블록

### 4.1 `dc_rails(snapshot, supplies)` -- reads node.is_rail; writes node.dc_rail_v = 레일마다 float(supplies 값).

### 4.2 `dc_current_basis(snapshot, declared_sources)` -- 원소 단위 KCL
- reads device.{dc_nets, element_class, kind, pins, dc_colour}, node.is_rail, graph(`GRAPH_KEY`).dc_pruned.
- DC 원소 = `dc_nets` 가 None 아닌 원소 − 가지치기 원소. `ends` = (원소, from, to): nmos (d, s), pmos (s, d), 2단자 (t0, t1)
  (pins 의 단자 이름순) -- 양의 전류 = from -> to.
- 고정 = 원소가 이상원이고 kind `"current_source"` 이며 `declared_sources` 값이 None 아님 -> `fixed` ((이름, float), ...).
- 미지수 열 = 고정 밖 DC 원소, [r2] (구조 색, 이름)순. 레일 아닌 넷마다 KCL 행(from 이면 +1, to 이면 −1), 유리수 기약
  행사다리꼴(열 왼쪽부터 pivot -- RREF 는 행 순서와 무관하다). pivot 이 아닌 열 = `free`(θ 전류 성분, 이름순 tuple). `rows` =
  (원소, (CurrentTerm, ...)): free·고정 원소는 자기 자신 ×1/1, pivot 원소는 −(RREF 계수)를 free·고정 원소에 건 항(0 계수
  생략, 열 순서). [r2] 같은 색 열 묶음이 free/pivot 으로 갈리면 `ties` 에 `TieBreak(current_pivot, 묶음, free 로 간 원소들)`.
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

### 4.4 `dc_theta_schema(snapshot, declared_resistors)` -- `ThetaSchema(components, current_cone, fixed)`
- components (정렬): (`ln_idu`, writer MOS), (`L`, 모든 MOS), (`y`, W4 y 키), (`current`, `free` 원소), (`resistance`, DC 저항
  중 `declared_resistors` 밖). `l_class` 관계는 status proposed 라 읽지 않는다 -> L 은 소자마다.
- [r2] **θ 전류 정의역** `current_cone` = MOS 이름순 ((MOS, 그 MOS 의 `rows` 항), ...), `fixed` = `basis.fixed`. 정의역 =
  {θ 전류 : 모든 MOS 행 Σ (num/den)·(θ 전류 또는 fixed 값) > 0} -- 전도 MOS 전류 > 0 을 KCL 기저에서 θ 의 선형 부등식으로 옮긴
  열린 다면체(원뿔 + 고정값 이동). 기저 원소가 MOS 자신인 행은 θ_I > 0 상자 하한이다. 탐색은 이 부등식을 선형 제약으로 받는다.

## 5. θ와 평가 블록

### 5.1 `check_theta(schema, values) -> Theta`
- `schema` 가 ThetaSchema 아님 -> `TypeError`. 키 집합 ≠ components -> `ValueError`(빠짐·남음 목록). 값이 bool·비실수·
  비유한 -> `ValueError`. `y` ∉ [0, 1], `L` ≤ 0, `resistance` ≤ 0 -> `ValueError`. [r2] `current_cone` 의 어떤 MOS 행이
  ≤ 0(유리수 정확 계산) -> `ValueError`(메시지에 (MOS, 전류) 목록) -- 정의역 밖이지 후보 실패가 아니다. 반환 = 키 정렬
  (((kind, key), float), ...).

### 5.2 `dc_currents(snapshot, theta_currents)` -- reads graph.dc_current_basis
- `theta_currents` 키 집합 ≠ `free` -> `ValueError`. 원소 전류 = Σ (num/den)·전류(원천) (유리수로 합한 뒤 float).
- [r2] 어떤 MOS 전류 ≤ 0 -> `ValueError`(정의역 밖 θ 로 블록을 직접 부른 호출 계약 위반 -- `size_and_seal` 경로에서는
  `check_theta` 가 먼저 거부해 도달하지 않는다). 옛 `SealViolationError(device_current_nonpositive)` 는 없어졌다.
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
  [r3] `Window.constraints`(그리고 empty_window detail 의 `constraints`) = 창을 만든 순서 제약의 **개수**(위 MOS 마다 lo 또는
  hi 하나씩 -- x 와 입력 묶음 전원에 채널(d 또는 s)이 닿는 MOS 수, 같은 MOS 가 두 묶음 전원에 닿으면 둘). 0 이면 창 = 레일 전압
  범위. 값이 lo·hi 를 실제로 좁혔는지는 뜻하지 않는다.
- [r2] **1변수 노드**(self-referential: writer MOS 의 d·s·bulk 중 하나가 x 자신 -- diode 의 gate 쓰기, 소스 추종의 source
  쓰기)는 **구간 bisection**(설계 3.4): h(x) = x − g(x). 구간 = 레일 전압 범위 ∩ {writer 의 vds ∈ [VDS 격자 최소, 최대]} ∩
  {vsb ∈ [VS 격자 최소, 최대]}(vds·vsb 는 x 의 1차식 -- x = 0, 1 두 점에서 계수를 잰다). g 평가에서 lut 가
  `lut_target_out_of_range` 를 내면 목표 > branch_max 면 VGS = +inf, 아니면 −inf(부호가 정해진 정의역 밖); 그 밖 LUT 실패는
  `lut_query_failed`. tol = 구간 가운데 점의 writer `tol_v_cell`, 반복 수 = `k_max(hi − lo, tol)`(hi = lo 면 1) -> 마지막 구간
  폭 ≤ tol, 가운데 점 x 뒤 g(x) 가 유한·구간 안이면 그것(한 번 다듬기). 구간이 비거나(lo > hi) 끝 부호가 같으면
  `SealViolationError`(devices (writer,), reason `no_root_in_window`, item = 구간 끝 출처에 `vds_axis` 가 있으면 7 아니면 6,
  margin = 유한한 끝 |h| 최솟값/tol(없으면 None), detail node·lo·hi·h_lo·h_hi·bounds(끝 출처 `rail`·`vds_axis`·`vs_axis`)).
- SCC 순서대로: 비순환 -> 한 번 평가. 크기 1 순환(= 1변수 노드) -> 위 bisection(`SccLog.iterations` = 반복 수, tol·k_max 기록).
  다변수 순환 -> 시작값(1단계: 기둥 위치 비례 평균 V(r1) + (V(r2) − V(r1))·position/length, 기둥 없으면 레일 중앙; 2단계 order
  순: 1변수 노드는 투영 bisection, 그 밖 MOS writer 는 VDS = 레일 범위/2, VSB = vgs_gate 면 현재값·vgs_source 면 0 에서 writer
  식 1회, 저항·같은 DC 는 writer 식, W4 그대로) 뒤 `gauss_seidel`(width = 레일 범위, devices = entry.devices, 허용오차 =
  SCC 의 writer MOS(없으면 d·s·bulk 값이 있는 entry.devices)의 `tol_v_cell` 최솟값; 모두 None -> `SealViolationError`
  reason `tol_v_undefined`). [r2] **반복 중(strict=False) 투영**: 1변수 노드는 근이 없거나 구간이 비면 |h| 가 작은 구간 끝
  (빈 구간이면 두 끝 가운데), 그 밖 MOS writer 의 `lut_axis_out_of_range`·`lut_target_out_of_range`, W4 빈 창은 현재 값 유지 --
  이웃의 과도 반복값 때문에 수렴할 θ 를 거부하지 않게. **수렴 뒤 strict 검증 바퀴**: SCC 노드마다 writer 식을 strict 로 다시
  재서(1변수는 bisection 전체, 실패는 위 구조화 실패 그대로) |새 값 − 수렴값| > tol 이면 `NonconvergentError`(reason
  `strict_recheck_residual`, margin = 잔차/tol, detail node·nodes) -- 투영이 최종값에 남지 않는다.
- [r3] **실패를 일으키는 최소 구성**(test 작성용):
  - `tol_v_undefined`: 보간 축 VGS·VDS·VS 가 모두 2점인 toy LUT(내부 격자점이 없어 lut CONTRACT 5절 축 양끝 규칙으로 모든
    tol_V 셀이 None) + 1변수 노드가 있는 회로. 작성자 측 확인(2026-10-08): tester conftest 의 toy 식에 VGS = VDS = VS = (0, 1.8)
    로 LUT 를 만들고 M1 nmos (x, x, gnd)(diode) + M2 pmos (x, pb, vdd), pb = 입력 포트(input_dc_v 0.9), θ = L 1 µm·전류 10 µA·
    ln_idu(M1) 아무 값 -> `size_and_seal` 이 `SealViolationError`(devices ("M1",), margin None, detail {reason: tol_v_undefined}).
    1변수 bisection 이 tol 을 먼저 재기 때문에 순환 노드가 하나라도 있으면 걸린다.
  - `strict_recheck_residual`: 방어 검사다. 마지막 Gauss-Seidel 바퀴가 Δ ≤ tol 이었는데 그 뒤 앞 노드를 다시 재면 tol 을 넘게
    움직이는 경우 -- SCC 루프 이득이 1 보다 큰데 시작값이 불안정 고정점 근처라 첫 바퀴들이 우연히 작게 움직인 경우에만 생긴다
    (수축 루프에서는 다시 잰 변화 = q·Δ ≤ Δ ≤ tol 이라 구조상 생기지 않는다). 공개 API 만으로 재현되는 최소 구성은 찾지 못했다
    (12절 O12) -- test 가 덮지 못하는 것을 숨기지 않으려고 적는다.
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

### 5.6b [r2] `bisect_root(f, lo, hi, iterations) -> (x | None, f_lo, f_hi)`
- f 는 실수 또는 ±inf. f(lo) == 0 이면 lo, f(hi) == 0 이면 hi. 부호가 같으면 (None, f_lo, f_hi). 아니면 `iterations` 번 반으로
  줄이며(가운데 값 0 이면 그 점) 마지막 구간의 가운데를 돌려준다. f 는 끝점 2회 + 반복마다 1회 부른다.

### 5.7 `dc_widths(snapshot, lut)` -- `DeviceOp`
- reads node.{dc_v, dc_rail_v}, device.{dc_current, dc_L, dc_ln_idu, pins, kind, bulk}. MOS 마다 vgs·vds·vsb(크기),
  op = lut op_point(노드 점), W = ID·L/exp(ln_idu), gm_id = op.gm_over_id, idu_forward = op.IDu, w_key = `w_keys[kind]`.

## 6. 봉인 (`seal_dc(snapshot, calls, lut, resistances, linear_devices) -> DcEvaluation`)

순서: `dc_tolerances(lut)` -> 1 `dc_seal_node_conflict()` -> 2 `dc_seal_vgs_match()` -> 3 `dc_seal_kcl(resistances)` -> 6
`dc_seal_bulk_reverse()` -> 7 `dc_seal_saturation(linear_devices)` -> 8 `dc_seal_kvl_branch()` -> 4 `seal_versions(snapshot,
calls + 위 7개)` -> 5 `seal_writers(snapshot)` -> `dc_seal_report(item4, item5)`.

[r3] **`calls` 형식**(`seal_dc`·`seal_versions` 공통): ((ComputeBlock, extras), ...) -- extras = 그 블록을 부를 때 넘긴 추가 인자
tuple(블록 함수 호출 `block(snapshot, *extras)` 의 `extras` 그대로, 없으면 ()). `size_and_seal` 은 `((dc_currents,
(θ 전류 쌍 tuple,)), (dc_lengths, (θ L 쌍 tuple,)), (dc_columns, (θ 쌍, fixed_values, resistor_values, lut)), (dc_widths,
(lut,)))` 를 넘기고 `seal_dc` 가 봉인 블록 7개를 같은 형식으로 덧붙여 `seal_versions` 에 넘긴다. 계획 블록(rails·struct_colour·
current_basis·writer_plan·scc_order·theta_schema)은 calls 에 들지 않는다(parent 검사가 plan_versions 로 대신한다).

`judge(item, rows)`(rows = (대상, 크기, tol 또는 None, devices, nodes)): tol 이 정의된 행 중 크기 > tol 이 있으면 fail(대상 = 그
행들), 없고 tol None 행이 있으면 undefined(대상 = 그 행들), 그 밖 pass. magnitude·tol·margin = margin 최대 행(fail 이면 fail 행
중), 행이 없으면 None. detail = n_checked·n_undefined·worst(대상) 키 정렬.
[r3] **margin** = 크기/tol(core `normalized_margin`), 단 **tol == 0 이면 크기 > 0 -> +inf, 크기 ≤ 0 -> 0.0**(core 는 tol 0 에
None 을 주지만 봉인에서는 '허용오차 0 을 넘은 위반' = 무한 위반이다; core 는 바꾸지 않고 sizing 이 정한다). **최대 margin 동률**이면
대상 이름(rows 의 첫 칸, 문자열 비교)이 가장 큰 행이 대표(`worst`)다.

| # | 블록 | 판정 |
|---|---|---|
| tol | `dc_tolerances` | dc_tol_v = lut `tol_v_table(kind, w_key).at(L, vds, "id_equivalent")`(None 가능), dc_gm_bound = max(gm_id_curve(L, vds, vsb) 의 id·gm/id)·W/w_m |
| 1 | `dc_seal_node_conflict` | 노드마다 spread = max − min of {노드 값} ∪ path_values; tol = 닿는 PATH_MOS 소자 tol_v 최댓값(정의된 것), 없으면 None; MOS 관계가 없는 노드는 n·eps·max|V|(n = 값 수) |
| 2 | `dc_seal_vgs_match` | MOS 마다 |ln idu_forward − ln_idu| / gm_id ≤ tol_v |
| 3 | `dc_seal_kcl` | [r3] 행 = DC 원소(`basis.ends` -- MOS·DC 저항·이상원, 가지치기 저항 제외)의 from·to 로 한 번이라도 나오는 레일 아닌 넷마다(DC 원소가 닿지 않는 넷 -- gate 전용 넷·커패시터만 닿는 넷 -- 은 행이 없고 n_checked 에 들지 않는다) |Σ from − Σ to|, MOS = idu_forward·W/L, 저항 = (V(from) − V(to))/R, 이상원 = dc_current; tol = 채널이 닿는 MOS 의 tol_v·gm_bound 최댓값(정의된 것; MOS 는 있는데 모두 None 이면 None), MOS 없는 넷은 n·eps·Σ|I| |
| 4 | `seal_versions` | calls 의 블록마다 fp_of((이름, code_hash, Projection.from_snapshot(snapshot, reads, extras).fp)) == block_version 이고 그 블록 writes 필드의 input_version == block_version. 위반 블록 = detail `blocks`. magnitude = 위반 수, tol 0 |
| 5 | `seal_writers` | 모든 필드 writer == 권한표 writer; 노드마다 dc_writer 있음, (tier == W0) == is_rail, dc_rail_v·dc_v 중 정확히 하나, dc_rail_v 있음 == is_rail. 위반 노드 = nodes, 위반 필드 = detail `fields` |
| 6 | `dc_seal_bulk_reverse` | MOS 마다 max(0, −vsb, −(vds + vsb)) ≤ tol_v |
| 7 | `dc_seal_saturation` | 항상 undefined(reason `lut_vdsat_column_missing`), devices = current > 0 이고 linear_devices 밖인 MOS, n_checked = 그 수 |
| 8 | `dc_seal_kvl_branch` | S1 rel_kvl_branch 엣지마다 Σ_멤버 |ln idu_forward − ln_idu|/gm_id ≤ Σ 멤버 tol_v(하나라도 None 이면 None). [r3] 행 대상 이름(= detail `worst` 값) = 엣지 `members`(S1 이 정한 순서 그대로)를 `"+"` 로 이은 문자열(예 `"M1+M2+M3+M4"`), devices = members |

`SealReport.status`: fail 있으면 `REPORT_VIOLATED`("violated"), 아니고 undefined 있으면 `REPORT_UNDEFINED`, 아니면
`REPORT_SEALED`. items = item 번호순 8개. 결과: violated -> `SealViolationError`(devices = margin 최대 fail 항목의 devices,
margin = 그 margin, detail = item·nodes·items((번호, 상태, margin) 8개)·item_detail). [r3] fail 항목 선택 키 = (margin, 항목
번호) 최대 -- margin None(봉인 4·5 처럼 정규화가 없는 항목)은 +inf 로 치고, 동률이면 번호가 큰 항목. undefined -> `DcEvaluation(sealed=None)`.
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
| [r2] θ 전류가 원뿔 밖(MOS 전류 ≤ 0) | check_theta | ValueError(정의역 밖, 후보 실패 아님) | 메시지 (MOS, 전류) | -- | -- |
| W4 창이 빔(strict) | ④ | SealViolationError | empty_window(item 7) | () | None |
| [r2] 1변수 노드 근 없음·구간 빔 | ④ | SealViolationError | no_root_in_window(item 6/7) | writer | 끝 |h|/tol |
| [r2] 다변수 SCC strict 검증 잔차 > tol | ④ | NonconvergentError | strict_recheck_residual | SCC 소자 | 잔차/tol |
| LUT 축 밖·목표 밖·앵커 아님 | ④⑤·tol | SealViolationError | lut_query_failed + lut_reason | 소자 | LUT 값(None) |
| 허용오차 셀 전부 미정 | ④ | SealViolationError | tol_v_undefined | SCC 소자 | None |
| 순환 블록 비수렴 | ④ | NonconvergentError | detail nodes·iterations·deltas·tol·k_max | SCC 소자 | Δk/tol |
| 봉인 위반 | 봉인 | SealViolationError | item·items·item_detail | 최악 항목 | 최악 margin |

## 9. 결정론

- 같은 doc·spec·LUT·θ 면 `size_and_seal(...).snapshot.fp` 가 같다(netlist 순서 섞기·`PYTHONHASHSEED` 무관). 작성자 측 실측:
  generality `shuffle_order` seed 1~3 로 9회로 모두 node.dc_writer 동일, 통과 θ 가 있는 7회로는 dc_v 비트 동일.
- [r2] **이름 전단사**: 구조 색이 먼저라 쓰기 소자·θ 기저·W4 뿌리가 전단사로 옮겨진다 -- `TieBreak` 기록의 후보 안에서만 예외.
  불변식(test 대상): 전단사 σ 로 이름을 바꾼 topology 의 (writer 집합, θ 스키마 키 집합) = σ(원래 것), 차이가 있으면 그 원소는
  모두 원래 계획의 `dc_tie_breaks`·`CurrentBasis.ties` 후보에 든다. 작성자 측 실측(generality `random_renaming` seed 1·2):
  9회로 모두 계획 구조 요약 동일, 8회로 writer 집합·θ 키 동일, current_reuse 만 차이 -- 차이는 전부 기록된 동률 후보 안
  (`writer_edge` {M1a, M1b}·{M4a, M4b}, `w4_root`·`input_tie_order` {Vim, Vip}, `current_pivot` {R1, R2}). 통과 θ 를 σ 로 옮긴
  7회로의 dc_v 최대 차 = 0.0(비트 동일).

## 10. 9회로 실측 (2026-10-07, 이 커밋 코드, 작성자 측 시연 -- 정본 아님)

LUT = `_drafts/engine/lut_slices/manifest.json`(32 슬라이스) + `assets/sky130_nfet_pfet_lut_sample.npz`, w_keys =
`pre_layout_lut_access`(nmos·pmos 1000 = 5 µm). spec = library `*.sizing_spec.json`(결정 대기 칸은 미선언 투영).
탐침 θ(탐색 아님): L = 1 µm 앵커, writer ln IDu = gm/ID {8, 12, 16, 20, 24} 점(VDS = 레일 범위/2, VSB 0), y ∈ {0.25, 0.5, 0.75},
전류 LP(최소 MOS 전류 최대화, 1~100 µA) + 무작위 200개(writer gm/ID U[6, 26], y U[0.05, 0.95], 전류 log-U[1, 100] µA·KCL 양수,
R log-U[100 Ω, 100 kΩ]) = 회로당 215 θ.

| 회로 | θ 차원 (L/ln_idu/current/y/R) | 티어 W0/W1/W2/W4 | 종속(parallel/cycle) | 순환 SCC 크기 | 일관 DC 점 | 대표 실패 |
|---|---|---|---|---|---|---|
| common_gate_amplifier | 9 (3/3/1/2/0) | 2/0/3/2 | 0/0 | [2] | 184/215 | NONCONVERGENT 25 (W4–W4 창 결합) |
| current_reuse_telescopic_ota | 105 (51/29/22/1/2) | 2/13/21/1 | 15/7 | [4, 4, 2, 2, 1×16] | 0/215 | no_root_in_window(item 7) M11b 123, M37b 54, M20b 13 |
| folded_cascode | 29 (13/8/5/3/0) | 2/4/5/3 | 4/1 | [3, 2, 1×4] | 81/215 | no_root_in_window M2 84, M6 25 |
| ngcc_3stage_ff | 35 (16/8/9/2/0) | 2/3/6/2 | 7/1 | [1×4] | 92/215 | no_root_in_window M2 123 |
| nmcnr_amplifier | 36 (15/11/8/2/0) | 2/2/12/2 | 3/1 | [2, 1×3] | 62/215 | no_root_in_window M103 119, lut_query_failed M301 16 |
| pushpull_follower_buffer | 14 (6/5/3/0/0) | 3/0/6/0 | 0/1 | [1, 1] | 9/215 | lut_query_failed(VS 축) M5 197 |
| sf_pushpull_output_opamp | 47 (22/14/7/1/3) | 3/1/18/1 | 6/2 | [9, 3, 1×6] | 0/215 | lut_query_failed(목표 밖) M17 114, M20 58, NONCONVERGENT 26 |
| two_stage_ota | 16 (7/4/3/2/0) | 2/1/5/2 | 2/1 | [1, 1] | 113/215 | no_root_in_window M2 75 |
| two_stage_ota_sf | 20 (9/5/4/2/0) | 2/1/5/2 | 3/1 | [1, 1, 1] | 78/215 | no_root_in_window M8(item 6) 75, M2 46 |

'일관 DC 점' = 봉인 1·2·3·4·5·6·8 pass, 7 undefined(`REPORT_UNDEFINED`). 계획 단계 정지 0/9, 정의역 밖 θ 0(탐침 생성기가 KCL
양수를 지킴). 첫 통과 점의 최대 margin: 봉인 1 ≤ 0.29, 봉인 2 ≤ 0.28, 봉인 3 ≤ 0.10, 봉인 8 ≤ 0.04. [r2] 1변수 bisection
도입 뒤 대표 실패가 반복 중 LUT 축 이탈(`lut_query_failed`)에서 margin 있는 `no_root_in_window` 로 바뀌었다. sf_pushpull 은 구조
색 기준 writer 선택으로 순환 블록이 [3, 3] -> [9, 3] 이 되어 탐침 통과 1 -> 0(실패는 strict 검증 뒤의 목표 밖 -- 그 θ 에서 진짜로
전류를 못 내는 점; 반복 과도 상태 탓인지 더 가르지 못했다 -- 12절 O10). 포화(봉인 7)는 판정하지 않았으므로 '일관'은 포화를
뜻하지 않는다(예: two_stage_ota 통과 점 tail CS = 0.061 V).

### 10.1 재사용·시간 (FD 스윕: L 밖 θ 성분마다 +δ 한 번, parent = 기준점)
- 같은 θ + parent: dc 블록 computes 0, reuses 12(4회로). [r2] FD 스윕 recomputes_same_input: two_stage·folded·nmcnr·ngcc 0
  (r1 측정의 sf_pushpull 5 는 형제 lineage 사이 같은 입력 -- O8; r2 에서는 sf 통과 θ 가 없어 재지 못했다).
- [r2] 계측 없는 FD 평가 1회(parent 재사용): two_stage 34 ms, folded 120 ms, nmcnr 59 ms, ngcc 49 ms(1변수 bisection 이 역산
  호출을 늘려 folded 가 r1 73 ms 에서 늘었다). 첫 평가(parent 없음) 33/62/44/49 ms. build_s1 21~42 ms, build_kernel_context
  13~50 ms. tol_V 표는 LUT derived memo 로 프로세스당 kind 마다 1회(~14 s/kind, lut CONTRACT 5절).
- cProfile(r2, 계측 포함): core `fp_of` 비율 two_stage 63%, folded 35%, nmcnr 69%, ngcc 73%(투영 지문·`GraphSnapshot.write`).
  LUT memo 퇴출 0, 퇴출 뒤 재계산 0. 중복 인자 호출(folded FD 16회): gm_id_for_target 2442/817 고유, op_point 263/73 --
  중복은 전부 LUT memo hit(계산 0). `TolVTable.at` 494/158 은 memo 밖 표 조회(O9).

## 11. 설계와 다르게 정한 점

1. **저장 = core GraphSnapshot 하나**: 설계 2.1 `DcField`·`setter.py`·`field_reuse.py`·`writer_table.py` 대신 core 의
   `FieldValue`·`GraphSnapshot.write`·`compute_block`·`WriterTable` 을 그대로 쓴다(같은 개념 두 정의 금지). S1 과 같은 스냅샷에
   산다(`lift_s1`, 권한표 `S2_WRITERS`).
2. **SCC 필드 단위 재사용 대신 블록 단위**: core `write` 는 열 교체라 SCC 마다 같은 필드에 부분 쓰기를 할 수 없다 -> `dc_columns`
   한 블록. 바뀌지 않은 SCC 의 LUT 조회는 memo hit. 전류만 바뀐 θ 는 `dc_drop_current` 분리로 노드전압 블록 자체를 건너뛴다.
3. [r2] 1변수 노드는 설계대로 구간 bisection. **다변수 SCC 의 반복 중 투영 + 수렴 뒤 strict 검증 바퀴**는 설계에 없던 추가다
   (오케스트레이터 결정 '과도 이탈로 수렴할 θ 를 거부하지 않는다'). 1변수 bisection 뒤 writer 식 한 번 다듬기도 추가(봉인 2 가
   같은 tol 로 재므로).
4. **W4 창 = 인접 전도 MOS 순서 제약**(설계 3.4 는 기둥 VDsat 합). S1 기둥은 노드-단순 경로라 전류 방향을 거스르는 경로를 포함해
   창이 뒤집혔다(nmcnr NodeF1 실측). VDsat 항 없음(O1).
5. **봉인 4·5 는 함수**(메타데이터를 읽어야 해서 투영 기반 계산 블록으로 쓸 수 없다), 결과는 `dc_seal_report` 의 extras 로 graph 에 든다.
6. **봉인 2·3·8 은 `dc_op.idu_forward` 를 읽는다**: 순방향 조회를 `dc_widths` 에서 한 번만 한다(설계는 항목마다 lut.query).
7. **봉인 8 = 멤버 ID 환산 차의 절대값 합**(부호 있는 잔차의 상계), 봉인 1 tol = 관계 소자 tol 최댓값, KCL tol_I = 노드 단위.
8. **core 계층 수학(bisect_root·fixed_point_iter·k_max)은 sizing 에** 둔다: 소비자가 sizing 하나뿐(배선 원칙). 층 0 국소
   고정점(DEC-71 (4)(d))이 생기면 core 로 옮긴다.
9. **L 은 소자마다 θ**(`l_class` proposed 라 평가 경로가 읽지 않음, N3.3).
10. 파일 이름: `seal/item*_*.py` 대신 `seal_<항목>.py`(하위 폴더 없이), `size_and_seal` 의 θ 검사는 `theta_check.py`.
11. [r2] **설계 3.1 의 '이름 정렬 첫 노드'·'같은 단계는 소자 이름 정렬'을 구조 색 키로 바꿨다**(이름은 같은 색 안에서만, 결정을
    가른 경우 `TieBreak` 기록). DEC-95 (3) 의 '③ 대칭 궤도 대표'는 같은 구조 색 = 같은 궤도 후보로 실현된다.

## 12. 열린 질문 (결정 필요 -- 추측으로 채우지 않았다)

처리 상태(r2, 오케스트레이터 결정 2026-10-07): O2·O4·O6 해결, O10 부분 해결, O1 대기(우회 없음), O7·O9 사용자 승인 대기,
O3·O8 기록 유지.

- **O1 VDSAT 접근자 (대기 -- 우회 없음)**: 봉인 7 은 lut 에 VDSAT 접근자가 생길 때까지 undefined, SealedSnapshot 0, W4 창에
  VDsat 항 없음. lut CONTRACT r5(브랜치 ng-hermite)에도 VDSAT 접근자가 없다. **이 계약이 요구하는 lut 공개 API**(로더가 LUT v2
  VDSAT 열을 읽은 뒤): (a) `vdsat(memo, kind, w_key, L, vgs, vds, vsb) -> float`(V, 크기, point 영역 memo, 축 규칙·실패는 op_point
  와 같음 -- 오라클 `@m[vdsat]` 과 같은 양, DEC-88), (b) `tol_v_table(...).at(L, vds, "vdsat")` 처럼 `TOL_V_METRICS` 에 VDSAT 열
  leave-one-out 지표 `"vdsat"` 를 더하거나 별도 `tol_vdsat_table` -- 셀 = (kind, w_key, L, VDS), 셀 값 = VDSAT 열 LOO 최댓값
  (DEC-87 방법). 생기면 `dc_seal_saturation` 이 (a)·(b) 로 ID > 0 MOS 마다 `VDS − VDsat ≥ +tol_VDsat`(margin =
  (VDS − VDsat − tol_VDsat)/tol_VDsat)을 재고, `dc_columns` 의 W4 창과 1변수 구간에 VDsat 항을 더한다. 지금은 `DcEvaluation(sealed=None)`.
- **O2 (해결)** 레이아웃 전 폭 = LUT 생성 규칙 폭(`pre_layout_lut_access`, DEC-91 (2), 1.3절).
- **O3 DEC-95 (3) ②**(GB5 gm 요구·뒤 stage): 그 정보를 내는 S1v·GB5 가 없어 아직 적용하지 않는다(① diode, ③ 대칭 궤도 =
  구조 색은 적용). 남은 동률은 `TieBreak` 로 기록(9회로 중 current_reuse 만 5건). front 정규화 해시 metamorphic 은 탐색 뒤.
- **O4 (해결)** F 없는 성분 뿌리 = (구조 색, 이름) 최소, 같은 색 후보는 `w4_root` 기록.
- **O5 결정 대기 입력 DC(SP-2, 7회로)**: U2 기본안 (a)대로 W4(입력 공통모드 y). 노드 목표(CI-15)·의도 영역(CI-18)은 9회로 모두
  결정 대기 -> W3 0개, 선형 선언 0개.
- **O6 (해결)** θ 전류 정의역 = `ThetaSchema.current_cone`(KCL 기저에서 유도한 선형 부등식), 밖이면 `check_theta` 가 거부.
- **O7 core 권한표 확장 API (사용자 승인 대기)**: `lift_s1` 이 S1 필드를 setter 로 다시 써서 레코드 구조 공유가 없다.
- **O8 형제 lineage 재계산 (기록)**: FD 형제 평가끼리 같은 입력은 재계산된다(graph 가 곧 캐시라 다른 lineage 값을 볼 길이 없음).
- **O9 성능 (사용자 승인 대기)**: 시간의 35~73% 가 core 투영 지문(`fp_of` 재직렬화). 투영 지문을 (key, `FieldValue.value_fp`) 로
  만들면 블록 호출·봉인 4 모두 줄어든다 -- core 변경. `TolVTable.at` 중복 조회는 memo 밖.
- **O10 (부분 해결)** 1변수 노드 = 구간 bisection, 다변수 SCC = 반복 중 투영 + strict 검증. 남은 위험: 다변수 SCC 에서 투영으로
  멈춘 노드 때문에 실제 근이 있는데 strict 검증이 실패할 수 있다(sf_pushpull 0/215 가 그 경우인지 가르지 못함). 다변수 블록을
  Newton·연속법 등으로 바꿀지는 설계 결정.
- **O12 [r3] `strict_recheck_residual` 재현 구성 없음**: 방어 검사(5.4 '실패를 일으키는 최소 구성'). 공개 API 만으로 덮을
  구성이 생기면 계약에 더한다.
- **O11 W4–W4 결합 비수렴**: 인접 W4 두 노드의 창이 서로를 읽으면 선형 수축비 y1(1 − y2) 가 1 에 가까울 때 K_max 안에 못
  들어와 NONCONVERGENT(common_gate 25/215). 설계 규칙('bisection 보다 느린 고정점 = 비수렴') 그대로의 결과다.
