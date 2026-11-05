# gmid_engine.sizing 동작 계약 (MOD4 GB7 DC 정본 풀이 + 봉인, test 작성용)

> **[U17 ①-b] S0 수준 필드 이동**(설계 40 §2.4.7 `KernelContext` 행·§2.4.8 v1.9.1 D8, 2026-10-13) -- 이 단락이 아래 옛 서술보다 우선한다.
> * [XRUN-F1 B] `build_kernel_context(s1graph, inputs, lut, order_hints=NO_ORDER_HINTS, *, donors, counters) -> KernelContext` -- `donors`·`counters` 는 필수 키워드(기본값 없음, 빠지면 `TypeError`)이고
>   7개 블록에 넘긴다. 호출자가 `search.open_run()` 으로 만든 실행 하나의 블록 결과 색인·계수다(단계 B 는 `StageAResult` 의 두 칸을 넘긴다). 결과 `KernelContext.donors`·`.counters` 는 넘긴 객체 그대로(`is`)다.
>   커널 단계의 블록 호출(`run_kernel` 의 ②~⑤, `seal_dc` 의 봉인 블록)과 `metrics.ss_evaluate`·search 평가 커널은 이 두 칸으로 부른다.
> * `build_kernel_context(s1graph, inputs, lut, order_hints=NO_ORDER_HINTS) -> KernelContext` -- `l_classes` 인자는 없다: L 동치류는 S1v 필드 `graph/s1v: l_classes`(있으면)에서 읽는다.
>   순서 = lift(`widen(S2_WRITERS)` -- 권한표가 S1_WRITERS 를 덮는 S0 수준 스냅샷도 받는다) -> `dc_rails` -> `s1_symmetry` -> `dc_current_basis` -> `dc_writer_plan` -> `dc_scc_order` ->
>   **`kernel_fields`**(writer `kernel_context`, 새 계산 블록: `graph/kernel(KERNEL_KEY="kernel")`: `fixed_values`·`resistor_values`·`l_ties` -- L 묶음 검사 `ValueError` 포함) ->
>   `dc_theta_schema`(extras = engine 수동소자만; reads 에 `resistor_values`·`l_ties` 필드).
> * `KernelContext(base, inputs, lut, donors, counters)` -- **참조만**(`donors`·`counters` = XRUN-F1 card B 의 과도기 참조 칸, U17 ② G-7 재작성에서 정리). 옛 칸 `schema`·`fixed_values`·`resistor_values`·`plan_versions`·`l_ties` 는 없다: θ 스키마 = `base.value("graph", KERNEL_KEY, "theta_schema")`
>   (옛 `graph/dc: dc_theta_schema` 를 `graph/kernel: theta_schema` 로 옮김, writer `dc_theta_schema` 그대로), 고정 노드·저항·L 묶음 = 같은 레코드의 필드, 계획 블록 입력 버전 =
>   `base.block_version(w)`(`PLAN_WRITERS` = 위 계획 블록 + `kernel_context`·`dc_theta_schema`). `run_kernel` 의 parent 검사는 `ctx.base` writer 전부(`base.block_versions` 키)의 block_version 이 `base` 와 같은지로 하고 어긋나면 `ValueError`, 통과한 parent 는 `parent.snapshot.derive_child(keep)` 로 파생해 출발한다(IT-2a, 계획 N3.3, 설계 41 4.7-3c). keep = base writer(`base.block_versions` 키) ∪ 커널 블록 이름(`steps`·`later`) ∪ `seal.py` 모듈 상수 `SEAL_ITEM_BLOCKS`(봉인 항목 블록 여덟, 블록 객체 tuple)의 블록 이름 -- 봉인 4 가 받는 호출 목록과 같은 집합이다. `dc_seal_report` 는 keep 밖이라 같은 입력이면 S3 graft 다. `PLAN_WRITERS` 는 `context_fp` 전용이다.
> * `dc_writer_plan` 은 `device.dc_self_referential`(MOS 마다 bool -- 그 소자가 쓰는 노드가 자기 d·s·bulk 중 하나인가: diode gate 쓰기·소스 추종 source 쓰기)도 쓴다(S0 수준 필드,
>   설계 40 §2.4.8 '1변수 writer 집합'). `dc_columns` 의 1변수 노드 판정과 search `cell_floor` 가 이 필드를 읽는다(reads 에 `device.dc_self_referential`).
> * (카드 IT-2c) `node.dc_output_structure`(출력 포트 구조 분류)는 삭제됐다 -- 측정 구성은 출력 꼴과 무관하게 봉인점 KCL 로 잰다(계획 N3.8, 설계 41 §4.7-W).
> * 권한표: `S2_WRITERS` 에 `kernel_context` 필드·`theta_schema`·`dc_self_referential` 이 든다. sizing `__init__` 이 S0 수준 스냅샷 값 형식(`CurrentBasis`·`CurrentTerm`·`NodeWrite`·`DeviceCoord`·
>   `TieBreak`·`SccEntry`·`ColumnNeighbor`·`ThetaSchema`·`ZeroCancel`)을 core 타입 등록부에 올린다.

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
- **개정 r4(2026-10-08, GB7 열린 질문 O1 처리 -- lut r6 `vdsat`·`tol_vdsat_table` 배선)**: `[r4]`. 요지 -- (1) 봉인 7 이 VDSAT 열로
  실제 판정한다(6절 표): (옛 포화 여유 블록. [EO-1 범위 4] 아래 개정 r10 이 영역 판정 `dc_seal_region` 하나로 대체했다), 열 없는 LUT 세트(옛 12-L 등)만 undefined + reason
  `lut_vdsat_column_missing`. 이제 1~8 이 모두 pass 인 점은 `SealedSnapshot` 이 된다. (2) 1변수 bisection 구간의 VDS 쪽 끝 =
  writer 슬라이스의 **VDS 정의역 하한**(on_mask 가 끝 열까지 모두 켜진 첫 VDS 격자점, 데이터 유도 -- LUT v2 는 VDS = 0 열이 전류
  0 이라 그 열과 보간되는 첫 칸의 gm/ID 곡선이 `lut_curve_undefined`) + 구간 끝 부동소수 안쪽 보정(5.4). 반복 중(strict=False)
  에는 그 하한 아래의 `lut_curve_undefined` 도 일시 이탈로 본다. (3) W4 창·1변수 구간의 VDsat 항은 **넣지 않았다** -- 계획 블록
  (`dc_scc_order` 의존 규칙) 변경이 필요해 결정 대기(12절 O1 잔여, 실측 포함).
- **개정 r5(2026-10-08, DEC-92 / search S-20 -- engine 보상 수동소자 θ)**: `[r5]`. 요지 -- (1) `DcInputs.engine_elements`(spec 값
  mode `engine` 원소 이름) 신설, (2) θ 성분 종류 `capacitance`(engine 커패시터)·`ss_resistance`(DC 전류 0 engine 저항 중 영점 상쇄
  구조 규칙 밖) 신설 -- 둘 다 DC 블록이 읽지 않는다(4.4·5.1·7절), (3) `ThetaSchema.zero_cancel` = 가지치기된 engine 저항마다
  `ZeroCancel`(DEC-92 (3)(a) 구조 규칙 판정, 연결만으로) -- 규칙이 정하면 그 저항은 θ 가 아니고 metrics `ss_evaluate` 가 봉인
  스냅샷 gm 으로 R = 1/Σgm 을 계산한다(metrics CONTRACT 7.6 r5), (4) 수동소자 θ 의 탐색 상자는 sizing 이 아니라 search 선언 입력
  (12절 O13). 실측 10.3절. 이 개정과 어긋나게 된 기존 test 목록은 12절 O14(test 작성자 갱신 몫).
- **개정 r6(2026-10-08, 오케스트레이터 결정 -- O10·O11: Gauss-Seidel 이 수축하지 않는 SCC 는 감쇠 Newton)**: `[r6]`. 요지 -- 다변수 SCC
  에서 Gauss-Seidel 이 멈추거나(측정한 q 로 K_max 안 도달 불가) 수렴 판정 뒤 strict 검증에 실패하면 같은 시작값에서 SCC 잔차
  r = V − g(V) 에 감쇠 Newton(`scc_newton.newton_solve`, 야코비안 = LUT 미분, LU, 역추적 선 탐색, 상한 K_max). `SccLog` 에
  `method`·`fallback` 필드(기본값이 있어 기존 생성 호출과 호환). 5.4·5.5b·10.4절, 12절 O10·O11 닫음.
- **개정 r11(2026-10-08, 사용자 결정 '정준 라벨링 + 대칭 변수 묶음' + 'U2: 대칭 묶음 방식 b')**: `[r11]`. 요지 -- 정준 라벨링·자기동형은 **graph**(`canonical_form`·
  `automorphism_orbits`, graph CONTRACT 4.7)가 계산하고, `dc_struct_colour` 는 그 결과로 `dc_colour`·`dc_orbit`·`graph.dc_symmetry` 를 쓴다(extras = 선언 표시 둘, 3.0b).
  **`dc_colour` = 1-WL 색 안을 정준 위치로 구분한 순위 -- 정점마다 유일해 이름이 순서를 정하는 자리가 사라진다**(종래 (색, 이름) 키의 이름은 도달하지 않는다).
  **2단자 수동소자는 방향 없는 엣지**다(저항 끝 방향은 색에 들어가지 않는다 -- 방향 보존 자기동형 때문에 9회로 모두 묶음이 비던 결함을 고친다). 이름 키가 남았던
  자리도 색 키로: `scc_order`(deps 정렬), `block_columns`(writer 소자·SCC 소자 정렬, 기둥 시작값 합산의 방향·순서). 소비자는 search(θ 묶음, 정준 순서, 3.23~3.25)·
  metrics(합산·행렬 순서).
- **개정 r7(2026-10-08, 오케스트레이터 결정 -- 수렴 판정 = 노드전압 오차 상계)**: `[r7]`. Gauss-Seidel 은 Δk ≤ tol 에 사후 상계
  q/(1−q)·Δk ≤ tol 을 더한다(둘 다; q < 1, k ≥ 3; q ≥ 1 이면 받지 않음, Δk = 0 은 받음), Newton 은 ‖r‖∞ ≤ tol 에 더해 온전한 걸음 ‖Δ‖∞ ≤ tol.
  새 상수 없음(tol = 기존 노드 허용오차). 2절 SccLog 필드 목록 정정. 5.5·5.5b·10.5절.
- **개정 r8(2026-10-08, 오케스트레이터 결정 -- '봉인한 동작점은 모델이 분해하는 점이어야 한다')**: `[r8]`. 봉인 항목 8 -> 9개(봉인 9 = 전도 여유). 계기: two_stage_ota 첫
  최종 front 점이 pA 전류(0.07~0.27 pA)에서 봉인돼 SPICE free 에서 M2/M6 이 꺼짐. **[r10] 이 항목의 판정식(VGS = 0 누설 대 분해능)·소자별 하한 필드는 폐기**하고 봉인 9 는 영역 판정(선언 없는 소자 ID > 0)이 됐다.
- **개정 r9(2026-10-08, 오케스트레이터 결정 -- 영역 어휘 하나로)**: `[r9]`. 영역 낱말 정본 = authoring `REGION_TRIODE`("triode"). [r10] sizing 은 낱말을 따로 정의하지 않고 authoring `REGION_TRIODE`·`REGION_OFF` 를 읽는다.
- **개정 r10(2026-11-04, card 20261104-eo1r4-sf1l -- EO-1 범위 4, 계획 v6.38.11 O-202·O-204·O-205·O-210·O-221·O-222, 위임 A-1·A-2·A-45~A-49)**: `[r10]`. 요지 -- (1) **공용 영역 판정**
  `judge_region`/`region_mismatch`(`region_judge.py`·`region_mismatch.py`)가 전류와 VDS 대 VDSAT 만으로(수치 문턱 없음) 영역을 가르고 봉인 7·9 블록 하나 `dc_seal_region`(`seal_region.py`,
  소자마다 한 번)이 두 항목을 쓴다. 옛 포화·전도 블록 둘, 옛 소자별 누설·바닥 필드 둘, 봉인 9 의 VGS = 0 조회, 행 여유 부호 판정은 삭제. (2) 봉인 6 경계 0 V:
  `junction_forward` 식 하나. (3) S0 술어 필드 `device.region_decl`(writer `dc_region_decl`, `DcInputs.regions`) -- 옛 선형 영역 소자 칸은 `regions` 로 대체, 소자 열거 뿌리 넷(쓰기 계획·전류 기저·θ 스키마·
  search_domain kind 목록)은 `off` 소자를 뺀다. (4) `off` 소자의 동작점·1차 ΔV·관문은 metrics `ss_off_op`·`ss_off_delta`·`off_region_gate`. 1.1·1.2·2·6절.

---

## 0. 파일과 진입점 (구조 규칙 A~I, `_module_map.LAYERS["sizing"]`)

| 층 | 파일 | 진입점 / 종류 | 계산 블록(writer) |
|---|---|---|---|
| 0 | `s2_values.py` | 데이터 선언 모듈(값 형식·어휘·`S2_WRITERS`) | -- |
| 0 | `k_max.py` | `k_max` | -- |
| 0 | `bracket_root.py` [r9] | `bracket_root` | -- |
| 1 | `pre_layout_widths.py` [r2] | `pre_layout_lut_access` | -- |
| 1 | `symmetry_marks.py` [U17-1d] | `symmetry_marks` | -- (DcInputs -> graph `SymmetryMarks`; 옛 `struct_colour.py` 삭제) |
| 1 | `_helpers_lut.py` | helper: `terminal_voltages`·`w_key_of`·`with_device`·`forward_point`·`tol_v_cell` | -- |
| 1 | `_helpers_seal.py` | helper: `judge`·`node_values` | -- |
| 1 | `dc_inputs.py` | `dc_inputs_from_spec` | -- |
| 1 | `fixed_point.py` | `gauss_seidel` | -- |
| 1 | `s2_lift.py` | `lift_s1` | -- |
| 1 | `theta_check.py` | `check_theta` | -- |
| 1 | `w0_rails.py` | `dc_rails` | `dc_rails` |
| 1 | `current_basis.py` | `dc_current_basis` | `dc_current_basis` |
| 1 | `writer_plan.py` | `dc_writer_plan` | `dc_writer_plan` |
| 1 | `scc_newton.py` [r6] | `newton_solve` | -- |
| 1 | `scc_order.py` | `dc_scc_order` | `dc_scc_order` |
| 1 | `theta_schema.py` | `dc_theta_schema` | `dc_theta_schema` |
| 1 | `block_currents.py` | `dc_currents` | `dc_currents` |
| 1 | `block_lengths.py` | `dc_lengths` | `dc_lengths` |
| 1 | `seal_versions.py` | `seal_versions`(함수) | -- |
| 1 | `seal_writers.py` | `seal_writers`(함수) | -- |
| 0 | `junction_forward.py` [r10] | `junction_forward`(순수 함수 -- 봉인 6 과 `ss_off_op` 이 부른다) | -- |
| 0 | `region_judge.py` [r10] | `judge_region`(+ `RegionJudgment`·`OUT_OF_DOMAIN`) | -- |
| 1 | `region_mismatch.py` [r10] | `region_mismatch` | -- |
| 1 | `region_decl.py` [r10] | `dc_region_decl` | `dc_region_decl` |
| 1 | `seal_report.py` | `dc_seal_report` | `dc_seal_report` |
| 3 | `seal_region.py` [r10] | `dc_seal_region` | `dc_seal_region` |
| 2 | `_helpers_dc_solve.py` [IT-2c] | helper: `Circuit`(읽기 전용 열·`region_rows`·`port_window`·`kind_sign`) | -- |
| 3 | `block_columns.py` [IT-2c: `_Circuit` 은 `Circuit` 을 잇고 θ·`override` 만 더한다, 커널 창 = W4 뿌리 항목만] | `dc_columns` | `dc_columns` |
| 3 | `block_widths.py` | `dc_widths` | `dc_widths` |
| 3 | `kernel_context.py` | `build_kernel_context` | -- |
| 3 | `seal_tolerances.py` | `dc_tolerances` | `dc_tolerances` |
| 3 | `seal_node_conflict.py` | `dc_seal_node_conflict` | `dc_seal_node_conflict` |
| 3 | `seal_vgs_match.py` | `dc_seal_vgs_match` | `dc_seal_vgs_match` |
| 3 | `seal_kcl.py` | `dc_seal_kcl` | `dc_seal_kcl` |
| 3 | `seal_bulk_reverse.py` | `dc_seal_bulk_reverse` | `dc_seal_bulk_reverse` |
| 3 | `seal_kvl_branch.py` | `dc_seal_kvl_branch` | `dc_seal_kvl_branch` |
| 4 | `seal.py` | `seal_dc` | -- |
| 5 | `size_and_seal.py` | `size_and_seal` | -- |

계산 블록은 모두 core `compute_block`(core CONTRACT 6절)이다: 블록 함수는 선언 reads 투영 + 불변 extras 만 받고, 입력 버전 =
fp_of((이름, 코드 해시, 투영 지문)) = `block.input_version(snapshot, *extras)`(정본), 같으면 재사용(스냅샷 `is` 반환), 결과는 `snapshot.write` 로만 쓴다(열 교체 의미).
[XRUN-F1 B] 호출은 `block(snapshot, *extras, donors, counters)`(필수 키워드 둘)이고 계수는 실행 하나의 `RunCounters`(`counters.snapshot()` 의 `blocks` 행)가 잰다 -- 블록 객체에 계수 메서드는 없다.
**봉인 4**(`seal_versions`)는 입력 버전 식을 사본으로 두지 않고 `block.input_version(snapshot, *extras)` 를 부른다(판정은 그대로). **부분 스냅샷**: `run_kernel` 은 블록 단계마다 후보 실패 클래스
(`NonconvergentError`·`SealViolationError`)를 이름으로 잡아 그 블록에 들어간 스냅샷을 `core.attach_partial` 로 붙인 뒤 다시 낸다. `seal_dc` 는 봉인 항목 블록(`dc_tolerances` ~ `dc_seal_kvl_branch`)과 `dc_seal_report` 단계마다 후보 실패 클래스를 이름으로 잡아 그 블록에 들어간 스냅샷을 붙여 다시 내고,
스스로 내는 `SealViolationError` 에는 `dc_seal_report` 까지 쓴 스냅샷을 붙여 낸다(`exc.partial`). [IT-2e] 부분 스냅샷은 붙이기 전에 `derive_child(writers_in_scope(base, 앞 블록))` 로 줄인다 -- `writers_in_scope(base, blocks) -> frozenset` = `base.block_versions` 키 ∪ 블록 이름(`seal_versions.py`, 정의 하나; `base` None 이면 `TypeError`). 그래서 `exc.partial` 의 writer = base writer ∪ 실패 블록 앞 블록 (parent 의 낡은 필드 0)이고 지문은 (평가 키, 실패 지점)만으로 정해진다. 부르는 자리 = 파생 keep(`run_kernel`)·봉인 4 coverage(`seal_versions`)·부착(`run_kernel` `_call_block(…, before)`·`seal_dc`). ss 단계 부착은 변경 없음. `seal_dc(snapshot, calls, lut, resistances, raise_on_violation=True, *, base, donors, counters)`: `base`·`donors`·`counters` 필수 키워드, `base` = `ctx.base`(None 이면 `TypeError`; 봉인 4 (3)(4)는 항상 잰다). 봉인 항목 블록 일곱의 구성원·순서는 `seal.py` `SEAL_ITEM_BLOCKS`(정의 하나) -- `seal_dc` 는 그 순서로 부르고 extras 는 호출마다 만드는 블록 객체 키 지역 매핑에서 찾으며, 키가 빠지거나 상수 밖 키가 있으면 `ValueError`(fail-closed).

## 1. 공개 흐름과 입력

```
inputs = dc_inputs_from_spec(load_sizing_spec(spec_path, topo, catalog))     # 사람 선언 투영
s1     = build_s1(topo, dict(inputs.supplies_v))                              # graph CONTRACT
ctx    = build_kernel_context(s1, inputs, pre_layout_lut_access(memo))         # S0 당 1회
ev     = size_and_seal(ctx, theta, parent=None)                                # θ 마다 -> DcEvaluation
```

### 1.1 `DcInputs(supplies_v, input_dc_v=None, node_targets=(), element_values=(), regions=(), pending=(), engine_elements=())` -- frozen
- `supplies_v` ((레일, V), ...) / `input_dc_v` 입력 포트 공통 DC(V) 또는 None / `node_targets` ((넷, V), ...) W3 /
  `element_values` ((원소, 값 또는 None), ...) / [r10] `regions` authoring `RegionDecl` tuple(이름순, triode·off -- 옛 선형 영역 소자 칸 자리) / `pending` ((경로, 결정 ID), ...) /
  [r5] `engine_elements` 원소 이름 tuple(정렬) -- spec 값 mode 가 `engine` 인 원소(수동소자·이상원 모두; 수동소자만 4.4 가 쓴다).

### 1.2 `dc_inputs_from_spec(spec) -> DcInputs`
- `spec` 이 authoring `SizingSpecDoc` 이 아니면 `TypeError`.
- `supplies_v` = `spec.supplies_v` 그대로. `input_dc_v`: InputDc mode `net` -> `dict(spec.supplies_v)[net]`, `value` ->
  `value_v`, `engine`·`pending`(또는 None) -> None. `node_targets` = `spec.node_voltage_targets_v` 가 tuple 이면 그것, 아니면
  (PendingMark·None) (). `element_values` = `spec.element_values` 각 원소의 (name, mode == "value" 면 value 아니면 None).
  [r10] `regions` = intended_region 이 tuple 일 때 그 `RegionDecl` 전부(소자 이름순; pending·미선언은 ()). 영역 어휘 정본 = authoring `REGION_TRIODE`·`REGION_OFF`. `pending` = `spec.pending` 의
  (path, decision) 이름순 -- **결정 대기 칸은 '미선언'으로 투영하고 막지 않는다**(정지는 MOD10 몫, SPEC_CONTRACT 3절).
  [r5] `engine_elements` = `spec.element_values` 중 mode == `"engine"` 인 원소 이름 정렬 tuple. mode `pending` 은 들지 않는다
  (결정 대기 값은 엔진이 고르지 않는다 -- 그런 수동소자는 θ 도 구조 규칙도 아니고 소신호에서 `passive_value_undeclared`).

### 1.3 `LutAccess(memo, w_keys)` -- frozen, `__canonical__() = (memo.lut.fp, w_keys)`
> **[개정 예정 -- design 40 v1.15.1 §3.7-A, card WB-1(계획 v6.38.2 DEC-105 (2)); 이 절 아래 문언은 as-built 계약이고 WB-1 병합 때 바뀐다]**: 'kind당 폭 슬라이스 하나' 계약은 폐기된다 -- `LutAccess`는 `memo`만 담고(`w_keys` 칸·`pre_layout_lut_access`·`w_key_of(lut, kind)` 삭제), 소자 슬라이스는 DC 블록 `dc_solve`(노드 풀이 `dc_columns` + W `dc_widths`를 합친 블록) 안에서 손가락 규칙 W-bin 선택 함수 `lut.finger_slice`로 소자마다 정하며 기록은 `DeviceOp.w_key`, 손가락 기하는 새 필드 `device: dc_finger`(m, w_f)다. 4절 S1 MOS kind 마다 `w_keys` 검사, `dc_drop_current` 필드도 같은 변경에서 지운다. 반복 종료·실패 사유·범위 3a 순서 = design 40 v1.15.2 §3.7-A 2·5와 §3.11-1 참조(규칙 본문은 design 한 자리). 지금 계약을 근거로 새 코드를 쓰지 않는다.
- `memo` = lut `LutMemo`(graph 밖 유일 memo), `w_keys` = ((kind, w_key), ...) 레이아웃 전 사이징이 쓰는 폭 슬라이스.
- `require_immutable(LutAccess(...))` 통과(`__canonical__` 우선), `fp_of` = LUT 내용 지문 + w_keys 의 함수 -- memo 상태(캐시
  내용·상한)가 달라도 같은 지문. 그래서 블록 extras 로 넘겨도 입력 버전은 LUT 내용·슬라이스만 따른다.
- [r2] **레이아웃 전 폭 규칙** `pre_layout_lut_access(memo) -> LutAccess`: kind 마다 w_key =
  round(`memo.lut.cap_map[kind].w_ref_m` / `memo.lut.spec.manufacturing_grid_m`) -- LUT 생성 규칙 폭(기준 LUT 의 폭·확산 기하,
  계획 DEC-91 (2) '레이아웃 전 첫 사이징점은 LUT 생성 규칙의 확산 기하', lut CONTRACT 1.4 `w_ref_m`). kind 는 `cap_map` 키
  정렬. 그 (kind, w_key) 슬라이스가 `slice_map` 에 없으면 `ValueError`. 실데이터에서 nmos·pmos 모두 1000(5 µm). 레이아웃 뒤
  실현 폭 슬라이스는 DEC-89 재평가 몫(이 함수 밖).

### 1.4 `build_kernel_context(s1graph, inputs, lut, l_classes=()) -> KernelContext` (l_classes: 13절)
- 인자 형식 위반 -> `TypeError`(s1graph 가 `S1Graph` 아님, inputs 가 `DcInputs` 아님, lut 가 `LutAccess` 아님).
- `supplies_declaration(dict(inputs.supplies_v), 레일 집합)`(graph) 위반 -> `SchemaRejectedError` 그대로.
  `fp_of(그 정규화 결과) != s1graph.key.supplies_v_fp` -> `ValueError`(S1 을 다른 supplies 로 만들었다).
- S1 MOS kind 마다 `w_keys` 에 kind 가 있고 `(kind, w_key)` 가 `memo.lut.slice_map` 에 있어야 한다 -> 아니면 `ValueError`.
- `node_targets` 넷이 S1 노드가 아니면 `ValueError`. [r5] `engine_elements` 이름이 S1 원소가 아니면 `ValueError`.
- 순서: `lift_s1` -> `dc_rails(supplies)` -> [r2] `dc_struct_colour(원소 표시, 노드 표시)` -> `dc_current_basis(이상 전류원 ((이름, 값 또는 None), ...) 이름순)` ->
  `dc_writer_plan(정렬 W3 넷 tuple, input_dc_v is not None)` -> `dc_scc_order` -> `dc_theta_schema(값 선언 DC 저항 이름 tuple,
  [r5] engine_elements 중 S1 수동소자(element_class passive) 이름 정렬 tuple)`.
  계획 블록의 `StructureUnresolvedError`·`InfeasibleTargetError` 는 그대로 전파(탐색 전 정지).
- `KernelContext(base, inputs, lut, schema, fixed_values, resistor_values, plan_versions)`:
  `fixed_values` = W3 목표 ∪ (input_dc_v 가 있으면 입력 포트마다 그 값, W3 가 우선) ((넷, V), ...) 이름순,
  `resistor_values` = 잎 가지치기되지 않은 저항 중 spec 값이 있는 것 ((이름, Ω), ...), `plan_versions` = 계획 블록 6개의
  ((writer, block_version), ...) (`dc_rails`, `dc_struct_colour`, `dc_current_basis`, `dc_writer_plan`, `dc_scc_order`,
  `dc_theta_schema` 순).

### 1.5 `lift_s1(s1graph) -> GraphSnapshot`
- 권한표가 S1 필드(`S1_WRITERS`)를 덮지 않으면 `TypeError`(S1 권한표를 넓힌 S0 수준 스냅샷은 받는다 -- graph CONTRACT 10.1·설계 40 §2.4.1, v1.9.2 결정 9), S1 writer 중 돌지 않은 것이 있으면 `ValueError`.
- 결과 `writers == S2_WRITERS`. 모든 S1 필드 값이 원본과 같고 `block_version(w)` 가 원본과 같다(그래서 S1 블록을 이
  스냅샷에 다시 부르면 reuse). [2026-10-08, O7 닫음] 결과 = core `S1Graph.snapshot.extend_writers(S2_WRITERS)` -- **레코드
  객체를 원본과 공유한다**(`is`), `fp`·필드 메타(writer·input_version·write_count)도 원본과 같다(r8 까지는 setter 로 다시 써서
  공유하지 않았고 write_count 가 1 로 새로 시작했다).

## 2. S2 dc 필드 (권한표 `S2_WRITERS` = S1 권한표 전부 + 아래, 필드마다 writer 하나)

graph 레코드 key: `DC_KEY`(`"dc"`). 값은 모두 불변(frozen dataclass·tuple·float·None).

| (kind, field) | writer | 대상 레코드 | 값 |
|---|---|---|---|
| node.dc_rail_v | dc_rails | 레일 노드만 | float V |
| node.dc_colour [r2] | s1_symmetry(graph, U17-1d) | 모든 노드 | int 구조 색 |
| device.dc_colour [r2] | s1_symmetry(graph, U17-1d) | 모든 원소 | int 구조 색 |
| graph.orbits [U17-1d] | s1_symmetry(graph) | GRAPH_KEY | `Orbits` 자기동형 궤도 id(옛 node/device.dc_orbit) |
| graph.current_symmetry [U17-1d] | s1_symmetry(graph) | GRAPH_KEY | `CurrentSigns` 생성자별 (원소, 상, 부호)(옛 graph.dc_symmetry) |
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
| node.dc_window | dc_columns | W4 뿌리 노드(입력 포트인 뿌리 포함) [IT-2c: 뿌리 아닌 입력 포트·선언 포트 항목 없음 -- 측정 구성 `node.dc_window_cfg` 가 받는다] | `Window`(칸 `input_status`·`tol_v`) |
| device.dc_ln_idu | dc_columns | 모든 MOS | float |
| graph.dc_scc_log | dc_columns | DC_KEY | tuple[`SccLog`] |
| device.dc_op | dc_widths | 모든 MOS | `DeviceOp` |
| device.dc_tol_v | dc_tolerances | 모든 MOS | float V 또는 None |
| device.dc_gm | dc_tolerances | 모든 MOS | float S (= dc_op.gm_id × dc_op.current, 자기 동작점 gm -- 설계 40 §3.7-3 v1.6) |
| graph.dc_seal_1/2/3/6/8 | dc_seal_node_conflict / vgs_match / kcl / bulk_reverse / kvl_branch | DC_KEY | `SealItem` |
| [r10] graph.dc_seal_7, graph.dc_seal_9 | dc_seal_region | DC_KEY | `SealItem` |
| [r10] device.region_decl | dc_region_decl (S0) | 영역을 선언한 소자만 | authoring `RegionDecl` |
| graph.dc_seal_report | dc_seal_report | DC_KEY | `SealReport` |

[ss_linearize 2026-10-08] 권한표 `S2_WRITERS` 에는 위 dc 필드 뒤에 ss·metric 필드(`SS_WRITES`)가 더 있다 -- writer 는
metrics 계산 블록이고 정의·값은 metrics CONTRACT 7절. 이름만 여기서 선언한다(sizing 은 metrics 를 import 하지 않는다):

| (kind, field) | writer | 대상 레코드 | 값 |
|---|---|---|---|
| device.ss_dev | ss_dev | 모든 MOS | metrics `SsDevice` |
| graph.metrics_ss | metrics_ss | `METRICS_KEY`(`"metrics"`) | metrics `MetricBundle` |
| graph.metrics_dc | metrics_dc | `METRICS_KEY` | metrics `MetricBundle` |
| graph.metrics_aux | metrics_aux | `METRICS_KEY` | metrics `MetricBundle`(offset·미러비·스윙·ICMR·FF 비 + 블록 잔차 보고, metrics CONTRACT 12절, U7) |
| [U17 ①] device.passive_value | passive_values | 값이 정해진 수동소자(spec ∪ θ ∪ 영점 상쇄 R) | float(Ω·F), 영점 상쇄 R = 1/Σ`dc_gm`(설계 40 §2.4.8, GB5 블록) |
| [U17 ①] graph.gate_area_m2 | metrics_dc | `METRICS_KEY` | float m²(Σ_MOS W·L, 설계 40 §2.4.8) |
| [U17 ①] graph.power_resolution_w | metrics_dc | `METRICS_KEY` | float W 또는 None(b_P = Σ_레일 |V_k|·max(dc_tol_v·dc_gm), 설계 40 §2.4.8) |

노드전압 정본: 레일 = `dc_rail_v`, 그 밖 = `dc_v`(한 노드에 둘 중 하나만 -- 봉인 5). 소자 VGS/VDS/VSB 는 저장 필드가 아니고
`DeviceOp` 는 노드전압 차의 파생이다(설정 API 없음, N3.4).

값 형식(모두 frozen dataclass, `s2_values`):
- `NodeWrite(tier, relation, element=None, known=None, y_key=None, order=0)` -- tier ∈ `TIER_W0..W4`("W0".."W4"),
  relation ∈ `REL_RAIL`·`REL_TARGET`·`REL_INPUT_DC`·`REL_VGS_GATE`·`REL_VGS_SOURCE`·`REL_RESISTOR`·`REL_WINDOW`·`REL_INPUT_POINT`
  ("rail", "declared_target", "input_dc", "vgs_gate", "vgs_source", "resistor_drop", "free_window", "input_point"). 입력 포트인 W4 뿌리의 `y_key` = 그 뿌리 넷(계획 K-3, IT-1).
  `input_point`(DEC-106) = 입력 DC 미선언 차동 입력쌍의 두 포트(한 점): 점이 F 에 닿지 않으면 두 항목 모두 tier W4·`y_key` = role `differential_input_p` 포트 넷, p 포트가
  뿌리(known 없음)·n 포트는 known = p 포트(같은 전압); F 에 닿으면 y 성분이 없고(y_key 없음) 먼저 쓰인 포트가 MOS 관계를, 다른 포트가 `input_point`(known = 그 포트)를 받는다.
- `DeviceCoord(role, relation, partner=None)` -- role ∈ `COORD_WRITER`("writer")·`COORD_DEPENDENT`("dependent"), relation ∈
  `DEP_TREE`("tree", writer 전용)·`DEP_PARALLEL`("parallel_vgs")·`DEP_CYCLE`("cycle_vgs")·`DEP_FIXED`("fixed_vgs").
- `CurrentTerm(source, num, den)`, `CurrentBasis(ends, mos, free, fixed, rows, pruned, resistors, ties)`(4.2).
- [r2] `TieBreak(decision, candidates, chosen)` -- decision ∈ `TIE_KRUSKAL`("writer_edge")·`TIE_ROOT`("w4_root")·
  `TIE_CURRENT_PIVOT`("current_pivot"), candidates·chosen 이름순 tuple.
- `ColumnNeighbor(rails, pred, succ, position, length)`, `SccEntry(index, nodes, cyclic, devices)`,
  `ThetaSchema(components, current_cone=(), fixed=(), zero_cancel=())`([r5] 4.4),
  [r5] `ZeroCancel(resistor, end_net, far_nets, cells, reason=None)`(4.4), `Theta(values)`, `PathValue(relation, value)`, `Window(lo, hi, constraints, input_status=None, tol_v=None)`,
  `SccLog(index, nodes, iterations, deltas, tol, k_max, method="direct", fallback=None)`([r6] method·fallback 5.4),
  `DeviceOp(kind, current, ln_idu, gm_id, L, W, vgs, vds, vsb, w_key, idu_forward)`,
  `SealItem(item, status, magnitude=None, tol=None, margin=None, devices=(), nodes=(), detail=())`, `SealReport(items, status)`,
  `SealedSnapshot(snapshot, report)`, `KernelContext(...)`(1.4), `DcEvaluation(snapshot, report, sealed=None)`.

> **[U17-1d] 대체(2026-10-12, 설계 40 §6-8 D-2·§2.4.8)**: `dc_struct_colour`·`struct_colour.py` 는 삭제됐다. 구조 색 `device/node.dc_colour`, 궤도 `graph/s1: orbits`(옛
> `dc_orbit` 두 필드 대체), 전류 부호 `graph/s1: current_symmetry`(옛 `graph.dc_symmetry` 대체)는 graph 대칭 블록 `s1_symmetry`(graph CONTRACT 4.8)가 S1 하나에서 쓴다.
> MOS d/s 는 같은 채널 라벨 `c`, `wl` 은 선언 표시를 넣은 같은 그래프의 1-WL 색이다. `build_kernel_context` 는 `lift_s1` 뒤 `dc_rails` 다음에 같은 블록을
> `s1_symmetry(base, supplies, symmetry_marks(inputs))`(새 `symmetry_marks.py`, 선언 표시 형식은 아래 3.0b 그대로이고 레일 전위 표시는 블록이 supplies 에서 만든다)로
> 재호출한다 -- S1 이 같은 표시로 만들어졌으면 재사용(계산 0). 계획 블록 버전 목록의 `dc_struct_colour` 자리는 `s1_symmetry` 다. 아래 3.0·3.0b 는 그 블록의 규칙 기록으로 남긴다
> (writer 이름만 바뀜, 그래프 라벨은 graph CONTRACT 4.7·4.8 이 정본).
> **[U17-1d] 전류 기저 열 순서**(40 §6-3 v1.8, 사용자 결정 "3번 권고대로" (가)): `dc_current_basis` 는 `graph.orbits` 를 더 읽고 열 키 = (궤도 비자명인가, `dc_colour`, 이름)으로
> 정렬한다. 행사다리꼴은 왼쪽 열부터 pivot 을 잡으므로 비자명 궤도 열을 뒤에 두어 자유 열(θ 전류)로 먼저 남긴다.

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

## 3.0b [r11] 정준 라벨링·자기동형 궤도 (`dc_struct_colour` 의 확장 산출, 3.0 위에)

`dc_struct_colour(snapshot, element_marks, node_marks)`:
- **reads** 3.0 과 같다(`device.{element_class, kind, is_diode, pins, bulk}`, `node.{is_rail, port_direction}` -- 추가 읽기 없음).
- **writes** `node.dc_colour`, `device.dc_colour`, `node.dc_orbit`, `device.dc_orbit`, `graph.dc_symmetry`(key `DC_KEY`).
- **extras 둘 = 선언 표시**(호출자 `build_kernel_context` 가 `DcInputs`·`dc_rails` 에서 만든다). 형식: `element_marks`·`node_marks` = `((이름, ((표시 이름, float), ...)), ...)`,
  이름순 바깥 tuple, 안쪽 쌍은 표시 이름순, 모두 불변 값(`require_immutable`). 표시 이름 어휘:
  * 노드 표시: `rail_v`(레일 전위 V -- `node.dc_rail_v`), `target_v`(W3 노드 목표 전압 V), `input_dc_v`(입력 포트 노드의 입력 DC 공통 전압 V).
  * 원소 표시: `value`(spec 값 mode `value` 의 선언 값 -- 단위는 그 원소 kind 의 SI), `engine`(값 mode `engine`, 값 0.0), [EO-1 범위 4] `triode`(`triode` 선언 소자, 값 0.0), `off_l`·`off_w`(`off` 선언 소자의 `l_m`·`w_m` -- 짝 두 소자 중 하나만 `off` 거나 길이·폭이 다르면 `graph.orbits` 에서 갈려 θ 가 묶이지 않는다).
  표시가 없는 이름은 목록에 없다(빈 표시). 값이 다르게 선언된 두 원소·전위가 다른 두 넷은 같은 궤도가 아니다. 표시는 처음 색에만 들어가고 `dc_colour` 의 서로 다른 1-WL 색
  사이 순서(아래)에는 영향이 없다.
- **계산**: graph `canonical_form(projection, element_marks, node_marks)`(graph CONTRACT 4.7)가 1-WL 색 `wl`·정준 위치 `position`·자기동형 생성자를 돌려준다(2단자 수동소자
  무향). `automorphism_orbits` 가 정점 궤도를 만든다.
- **`dc_colour`** = (`wl`, `position`) 쌍의 정렬 순위 → 노드 안에서도 원소 안에서도 값이 유일하다. 1-WL 색이 다른 정점 사이의 순서는 종래와 같다(색이 이미 유일한 회로에서는
  정수 값도 종래와 같다). 3.0 의 "동률 → 이름" 은 도달하지 않는다: 같은 1-WL 색 안(자기동형 궤도 포함)은 정준 위치가 정한다. 정준 위치는 자기동형 γ 만큼의 선택 여지가 있지만
  정준 그래프(위치로 다시 쓴 그래프)는 이름 치환·원소 순서에 불변이라, 위치만 읽는 계산은 같은 정준 그래프에 같은 계산을 한 것이다. `dc_tie_breaks` 는 호환 필드로 남고
  (이름이 결정한 경우가 없어 비는 것이 정상) 새 TieBreak 를 만들지 않는다.
- **`dc_orbit`** = 궤도 구성원의 정준 위치 최솟값(같은 궤도 ⇔ 같은 값, 이름 치환·순서 섞기에 불변).
- **`graph.dc_symmetry`** = 자기동형 생성자 tuple: 각 생성자는 움직인 정점만 `((정점, 상), ...)`(정점 키 = `("n", 넷)` | `("e", 원소)`). search `current_symmetry` 가 θ 전류 부호 묶음을
  만드는 근거다.
- **2단자 수동소자(저항·커패시터)는 방향 없는 엣지**(사용자 결정 2026-10-08 '대칭 묶음 방식: b'). 전류 부호 규약은 종래 그대로(`current_basis._ends`: 단자 이름 순서 첫 단자 → 둘째,
  `block_columns.drop` 도 같음). 자기동형이 단자 순서를 뒤집어 대응하면 그 가지 전류는 부호 −1 로 대응한다(search CONTRACT 3.24 `current_symmetry`). 이상 전류원은 단자 라벨이
  방향이라 보존. library topology 의 단자 순서는 바꾸지 않는다.
- 이름 키를 색 키로 바꾼 자리(r11): `dc_scc_order` 의 deps 정렬(계획 순서 키), `dc_columns` 의 writer 소자·SCC 소자 정렬(구조 색)과 `start` 의 기둥 합산(출발 레일 = 색이 작은 쪽,
  이웃 정렬은 색). S1 기둥 데이터(`dc_column_nbrs` 의 레일 이름순 방향)와 `devices` 이름순 계약은 그대로다.
- 성질(test 가 확인할 것): (1) 이름 전단사·원소 순서에 `dc_orbit` 불변; (2) 손으로 쓴 그래프에서 기지의 궤도: 대칭 쌍(차동쌍 완전 대칭 회로) = 같은 궤도, 단일 종단 OTA 의 쌍 = 서로 다른
  궤도; 저항 terminals 순서를 뒤집어 그려도 궤도 분할이 같다; 1-WL 색이 같아도 비자기동형이면 다른 궤도; (3) 궤도 ⊆ 1-WL 색 클래스; (4) 다르게 선언된(값·레일 전위) 두 원소는 다른 궤도;
  (5) `dc_colour` 가 노드끼리·원소끼리 서로 다르다; (6) 같은 입력 → 같은 출력(결정론); (7) 이름 치환 σ 에 대해 두 사례의 정점을 `dc_colour` 같은 것끼리 짝지은 대응 τ 아래에서
  `dc_writer`(order·relation·known·element)·`dc_scc_order`·`dc_column_nbrs`·`dc_coord` 가 같다(σ 아래서가 아니라 τ 아래서 -- 궤도 구성원이 서로 바뀔 수 있다).

## 3. 쓰기 계획 `dc_writer_plan(snapshot, target_nets, input_dc_declared)` (θ 무관)

reads: device.{element_class, is_diode, kind, pins, dc_colour, dc_nets, region_decl}, node.{is_rail, port_direction, dc_colour}. (`off_only_node` 관문: 전도 엣지 = `dc_nets` 에서 off 소자·전류원을 뺀 것, 고정 넷에 안 닿는 넷에 off d·s 가 닿거나 off g 가 닿고 켜진 gate 가 없으면 정지)
writes node.dc_writer, device.dc_coord, graph.dc_tie_breaks. [r2] 모든 정렬 키 = (구조 색, 이름) -- 이름은 같은 색 안에서만.

1. 고정 노드 F 와 writer: 레일 -> (W0, rail), `target_nets` -> (W3, declared_target), `input_dc_declared` 면 입력 포트
   (`port_direction == INPUT_DIRECTION`) -> (W2, input_dc). 우선순위 W0 > W3 > W2(이미 배정된 노드는 건너뜀).
2. G_vgs 엣지: MOS 마다 (gate, source), 저항(`element_class == passive`, kind `"resistor"`, **잎 가지치기된 저항 포함**)마다
   (t0, t1), 커패시터·이상원은 엣지가 아님. '같은 DC' 엣지는 없다(K-3, IT-1) --
   입력 DC 가 선언되지 않아도 입력 포트는 MOS·저항으로만 G_vgs 에 닿는다.
3. 엣지 키 = (순위: 저항 < diode MOS < 그 밖 MOS, 원소 구조 색, 이름). F 를 한 점으로 묶고 Kruskal 최소
   신장 숲. 같은 (순위, 색) 원소 묶음이 트리/비트리로 갈리면 `TieBreak(writer_edge, 묶음, 트리로 간 원소들)`(묶음을 다 처리한
   뒤의 성분 분할은 묶음 안 순서와 무관하므로 이름이 가르는 것은 그 묶음 안의 선택뿐이다). 트리 MOS = `DeviceCoord(writer, tree)`. 비트리 MOS = dependent: gate·source 가 둘 다 F 면 `fixed_vgs`, 같은 kind·
   같은 (gate, source) 의 트리 MOS 가 있으면 `parallel_vgs`(partner = 그 소자), 그 밖 `cycle_vgs`. 비트리 저항 ->
   `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, rule_branch `dc_resistor_cycle`, nets, devices = 저항).
4. 방향(BFS, 트리 엣지 인접 목록은 (순위, 색, 이름)순): F 넷 전부((색, 이름)순)에서 시작, 아직 안 쓴 끝 노드를 쓴다 -- 저항 -> (W2, resistor_drop, element, known), MOS 가 gate 를 쓰면 (W1 if is_diode else W2,
   vgs_gate, element, known = source), source 를 쓰면 (W2, vgs_source, element, known = gate).
5. F 없는 성분(G_vgs 넷을 (색, 이름)순으로 훑어 처음 만나는 미배정 넷의 성분): 성분 안 F 밖 입력 포트가 있으면 그중 (색, 이름)
   최소를 뿌리, 없으면 성분 노드 중 (색, 이름) 최소를 뿌리; y 키 = 뿌리 넷.
   뿌리와 같은 색인 후보가 둘 이상이면 `TieBreak(w4_root, 그 후보들, (뿌리,))`. 뿌리 = (W4, free_window). 그다음 4 와 같은 BFS.
6. G_vgs 에 없는 남은 노드((색, 이름)순) = (W4, free_window, y_key = 넷).
6a. 입력 점·정지(DEC-106, IT-1): 입력 DC 미선언이고 입력 포트(G_vgs 밖 고립 입력 포트 포함)가 둘이며 role 이 `differential_input_p`·`differential_input_n` 각 하나이면 두 포트를
   Kruskal·성분 계산에서 한 점(입력 점)으로 묶는다 -- 평행·종속 판정도 묶은 뒤의 (gate, source)로 한다. 그 밖 둘 이상(차동쌍 둘, 차동쌍 없는 입력 둘 이상, 차동쌍 + 다른 입력)은 탐색 전에
   `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, rule_branch `BRANCH_INPUT_CM_UNDEFINED`("input_cm_undefined"), ports = 그 포트 넷들). 입력 포트 하나 또는 입력 DC 선언이면 무동작.
   같은 층의 둘째 정지: 입력 DC 미선언이고 차동 입력 두 포트(p·n 각 하나) 중 한 포트만 `node_voltage_targets_v` 로 선언하면(입력 점이 안 묶여 ΔV 가 θ 함수) `StructureUnresolvedError`(rule_branch `BRANCH_INPUT_TARGET_ONE_PORT`("input_target_one_port"), ports = 두 포트, declared = 선언한 포트).
7. `order` = 배정 순번(0부터, 1→4→5→6 순서). 모든 노드가 writer 하나를 받는다. order 의 같은 색 안 이름 순서는 SCC 안 갱신
   순서·시작값에만 쓰이고 수렴값(허용오차 안)을 바꾸지 않으므로 기록하지 않는다.

불변식(test 가 JSON 으로 셀 수 있는 것): MOS 수 = writer 수 + dependent 수; dependent 수 = G_vgs(F 를 한 점으로 묶은 다중
그래프, 엣지 = MOS·저항)의 순환수 = |E| − |V| + 성분 수(저항 비트리 0 일 때); W4 수 = F 없는 성분 수 + G_vgs 밖 노드 수.

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
  {gate(known), drain, bulk, 자기 자신}, resistor_drop = {known}, free_window = 그 노드에 d 또는 s 가 닿는 MOS 의 반대 채널 단자,
  input_point(known 있음) = {known}, input_point 뿌리 = 뿌리와 그 짝 포트 둘 다에 d 또는 s 가 닿는 MOS 의 반대 채널 단자.
- Tarjan(반복형) SCC, 의존이 먼저인 순서 = 풀이 순서. `SccEntry.nodes` = order 순, `cyclic` = 크기 > 1 또는 자기 의존,
  `devices` = d·g·s 중 하나가 SCC 노드인 MOS 이름순.
- `dc_column_nbrs` = S1 `Column` 경로(r1 에서 걷기)마다 내부 노드의 (rails, pred, succ, position, length) -- 시작값 전용.

### 4.4 `dc_theta_schema(snapshot, declared_resistors, engine_passives)` -- `ThetaSchema(components, current_cone, fixed, zero_cancel)`
- [r5] reads 에 device.{pins, bulk}, node.{terminals, is_rail, port_direction, ac_ground_class} 추가(S1 필드 -- 구조 규칙용).
- components (정렬): (`ln_idu`, writer MOS), (`L`, 모든 MOS), (`y`, W4 y 키), (`current`, `free` 원소), (`resistance`, DC 저항
  중 `declared_resistors` 밖). `l_class` 관계는 status proposed 라 읽지 않는다 -> L 은 소자마다.
  [r5] (DEC-92) + (`capacitance`, `engine_passives` 중 kind `"capacitor"`) + (`ss_resistance`, `engine_passives` 중 kind
  `"resistor"` 이고 `basis.pruned` 에 들며 `zero_cancel` 판정의 reason 이 None 이 아닌 것). `engine_passives` 중 가지치기 안 된
  저항은 지금처럼 `resistance`(값 미선언 DC 저항 규칙이 이미 덮는다 -- 이름이 두 종류에 동시에 들지 않는다). S1 수동소자가 아닌
  이름은 무시(호출자 `build_kernel_context` 가 걸러 넘긴다).
- [r5] **DC 무관 근거(요소 종류별)**: 커패시터 = S1 `dc_nets` None(DC 엣지 아님) -> G_vgs·KCL·dc_columns 어디에도 없다.
  가지치기 저항 = DC 전류 0(S1 4.3 잎 가지치기, `dc_currents` 가 0.0 을 쓴다) -> 강하 0 이라 값이 노드전압에 들어가지 않는다
  (`dc_columns` 의 resistor_drop 은 전류 0 이면 Δ = 0 이고 R 을 읽지 않는다). DC 경로 저항은 전류가 흘러 DC 를 바꾸므로 `resistance`
  (DC 블록이 읽음)로 남는다. 그래서 `capacitance`·`ss_resistance` 는 `THETA_PASSIVE_KINDS` 이고 `size_and_seal` 이 어느 DC 블록에도
  넘기지 않는다(7절).
- [r5] **영점 상쇄 구조 규칙**(DEC-92 (3)(a), `zero_cancel` = `engine_passives` 중 `basis.pruned` 에 든 저항마다 `ZeroCancel`,
  저항 이름순). 연결(S1 필드)만 쓴다:
  1. 내부 넷 = 레일 아님 · `port_direction` None · `terminals` 가 비지 않고 그 원소가 모두 수동소자 · 어떤 MOS 의 `bulk.net` 도 아님.
  2. 망 N(R): R 의 두 넷에서 시작해 내부 넷이면 그 넷에 닿는 수동소자를 모두 망에 넣고 그 소자의 다른 넷으로 넘어간다(내부 넷이
     아닌 넷에서는 멈춘다). 닿은 비내부 넷 = 경계 넷. `end_net` = R 의 두 넷 중 경계 넷(정확히 하나일 때, 아니면 None),
     `far_nets` = 경계 넷 − R 의 넷(정렬).
  3. 판정 순서와 reason: 망에 커패시터 없음 -> `ZC_NO_CAPACITOR`("network_without_capacitor"); R 밖 저항이 망에 있음 ->
     `ZC_MULTIPLE_RESISTORS`("network_multiple_resistors"); `end_net` None -> `ZC_RESISTOR_END`("resistor_end_not_unique");
     S = MOS(이름순) 중 source 넷의 `ac_ground_class` 가 None 아님(CS 셀) 이고 (drain == end_net 이고 gate ∈ far_nets) 또는
     (gate == end_net 이고 drain ∈ far_nets) 인 것 -- 비면 `ZC_NO_CELL`("no_cs_cell"), drain 쪽·gate 쪽 셀이 섞이면
     `ZC_MIXED_DIRECTION`("cs_cell_direction_mixed", cells 는 채움), 아니면 reason None(cells = S). reason 이 먼저 정해지는 경우
     cells = ().
     **`ZC_RESISTOR_END` 는 방어 분기다**(독립 test 보고 2026-10-08): 공개 로더 경로(topology 로드 -> `build_s1`)에서는 도달하지
     않는다 -- R 의 두 넷이 모두 내부 넷인 망(경계 없는 수동 섬)은 authoring `hidden_rails` 검사가 먼저 거부하고, 두 넷이 모두
     경계 넷이면 망이 R 하나뿐이라(수동소자는 내부 넷을 건너서만 망에 든다) `ZC_NO_CAPACITOR` 가 먼저 정해진다. 손으로 만든 S1 에서만 재현되며, 판정 순서·사유 값은
     위 그대로 유지한다.
  4. reason None -> R 은 θ 가 아니다(값 = 봉인 스냅샷에서 1/Σ_{c∈S} gm_c, metrics `ss_evaluate`). 그 밖 -> (`ss_resistance`, R)
     θ 성분(DEC-92 (3)(b) 폴백).
  - **규칙 문구 해석**(12절 O15 -- J7 ratify 대상): 계획 DEC-92 (3)(a) 'S = 저항 끝 넷을 출력으로 갖고 루프 반대쪽에서 신호를 받는
    CS 셀'을 R–C 직렬 순서와 무관하게 읽었다(직렬 임피던스 R + 1/sC 는 순서와 무관 -- 영점 s = 1/(C(1/gm − R)) 도 같다). 그래서
    end_net 이 셀의 drain(R 이 출력 쪽 -- nmcnr 배치)이든 gate(R 이 입력 쪽 -- two_stage_ota 배치)이든 같은 규칙이다. 문구를
    글자대로(drain == end_net 만) 읽으면 two_stage_ota 의 Rz 는 S = ∅ -> θ 폴백이 된다.
- [r2] **θ 전류 정의역** `current_cone` = MOS 이름순 ((MOS, 그 MOS 의 `rows` 항), ...), `fixed` = `basis.fixed`. 정의역 =
  {θ 전류 : 모든 MOS 행 Σ (num/den)·(θ 전류 또는 fixed 값) > 0} -- 전도 MOS 전류 > 0 을 KCL 기저에서 θ 의 선형 부등식으로 옮긴
  열린 다면체(원뿔 + 고정값 이동). 기저 원소가 MOS 자신인 행은 θ_I > 0 상자 하한이다. 탐색은 이 부등식을 선형 제약으로 받는다.

## 5. θ와 평가 블록

### 5.1 `check_theta(schema, values) -> Theta`
- `schema` 가 ThetaSchema 아님 -> `TypeError`. 키 집합 ≠ components -> `ValueError`(빠짐·남음 목록). 값이 bool·비실수·
  비유한 -> `ValueError`. `y` ∉ [0, 1], `L` ≤ 0, `resistance` ≤ 0, [r5] `capacitance` ≤ 0, `ss_resistance` ≤ 0 -> `ValueError`. [r2] `current_cone` 의 어떤 MOS 행이
  ≤ 0(유리수 정확 계산) -> `ValueError`(메시지에 (MOS, 전류) 목록) -- 정의역 밖이지 후보 실패가 아니다. 반환 = 키 정렬
  (((kind, key), float), ...).

### 5.2 `dc_currents(snapshot, theta_currents)` -- reads graph.dc_current_basis
- `theta_currents` 키 집합 ≠ `free` -> `ValueError`. 원소 전류 = Σ (num/den)·전류(원천) (유리수로 합한 뒤 float).
- [r2] 어떤 MOS 전류 ≤ 0 -> `ValueError`(정의역 밖 θ 로 블록을 직접 부른 호출 계약 위반 -- `size_and_seal` 경로에서는
  `check_theta` 가 먼저 거부해 도달하지 않는다). 옛 `SealViolationError(device_current_nonpositive)` 는 없어졌다.
- writes dc_current(+ 가지치기 저항 0.0), dc_drop_current(= dc_current 중 `resistors` ∪ `pruned`).

### 5.3 `dc_lengths(snapshot, theta_lengths)` -- reads device.element_class; 키 ≠ MOS 집합 -> `ValueError`; writes dc_L.

### 5.4 `dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)` -- 노드전압 정본
- reads node.{dc_writer, dc_rail_v, dc_column_nbrs, port_direction}, device.{dc_drop_current, dc_L, pins, kind, bulk, element_class,
  dc_coord}, graph.dc_scc_order. `theta_items` = θ 중 ln_idu·y·resistance 성분.
- 부호 s = +1(nmos)/−1(pmos). 크기: vgs = s(V(g)−V(s)), vds = s(V(d)−V(s)), vsb = s(V(s)−V(b)).
- VGS(좌표) = lut `vgs_for_current_density(memo, kind, w_key, ln_idu, L, vds, vsb)` ([U3 2026-10-08] 옛 임시 우회
  `gm_id_for_target(W = w_m, current = exp(ln_idu)·w_m/L).vgs` 를 대체 -- `_vgs_of_coordinate`·`_vgs_signed` 두 곳; 같은 곡면의 칸 안 Hermite 근, 분지 끝 마디 좌표는 반올림 2 ulp 허용, lut CONTRACT 3.1).
  `lut_target_out_of_range` 의 `target`·`branch_max` 는 ln ID 단위로 서로 같아 `target > branch_max` 가 '필요한 VGS 가 격자 위'다.
- writer 식: vgs_gate V(x) = V(known) + s·VGS / vgs_source V(x) = V(known) − s·VGS / resistor_drop V(x) = V(known) + Δ,
  Δ = 0 (전류 0), 아니면 known 이 t0 이면 −I·R, t1 이면 +I·R(I = dc_drop_current, R = θ 또는 선언값) / free_window V = lo + y·(hi − lo).
- 창 [lo, hi]: 레일 전압 범위 [min, max] 에서 시작, x 에 채널이 닿는 MOS 마다 전류가 나가는 단자
  (nmos d, pmos s)면 lo = max(lo, V(반대 단자)), 들어오는 단자면 hi = min(hi, V(반대 단자)). lo > hi -> `SealViolationError`
  (devices (), margin None, detail item 7·reason `empty_window`·node·lo·hi·constraints). **VDsat 항 없음**(12절 O1 -- [r4] 열은
  생겼지만 창에 넣으려면 인접 MOS 의 gate·bulk·자기 노드를 W4 의존에 더해야 해서(4.3 변경) 결정 대기. 포화는 봉인 7 이 판정한다).
  [r3] `Window.constraints`(그리고 empty_window detail 의 `constraints`) = 창을 만든 순서 제약의 **개수**(위 MOS 마다 lo 또는
  hi 하나씩 -- x 에 채널(d 또는 s)이 닿는 MOS 수). 0 이면 창 = 레일 전압
  범위. 값이 lo·hi 를 실제로 좁혔는지는 뜻하지 않는다.
- [r2] **1변수 노드**(self-referential: writer MOS 의 d·s·bulk 중 하나가 x 자신 -- diode 의 gate 쓰기, 소스 추종의 source
  쓰기)는 **구간 bisection**(설계 3.4): h(x) = x − g(x). 구간 = 레일 전압 범위 ∩ {writer 의 vds ∈ [VDS 정의역 하한, VDS 격자
  최대]} ∩ {vsb ∈ [VS 격자 최소, 최대]}(vds·vsb 는 x 의 1차식 -- x = 0, 1 두 점에서 계수를 잰다).
  [r4] **VDS 정의역 하한** = writer 슬라이스(`pre_layout_lut_access` 의 (kind, w_key))의 `on_mask`((ID > 0) & (GM > 0))가 그 VDS 격자
  열부터 마지막 열까지 모든 (L, VGS, VS) 점에서 참인 첫 VDS 격자점(그런 열이 없으면 VDS 격자 최소 = r3 그대로). 왜: 그보다 작은 VDS
  는 꺼진 열(LUT v2 는 VDS = 0 열, 저장 ID 가 바닥값이고 GM = 0)과 보간되어 gm/ID 곡선 마디가 정의되지 않는다(lut `lut_curve_undefined`)
  -- 부호가 정해진 정의역 밖(`lut_target_out_of_range` 의 ±inf)이 아니라 LUT 가 그 VDS 의 동작점을 표현하지 못하는 구간이므로
  bisection 구간에서 뺀다. 그 구간의 점은 VDsat(약반전에서도 수십 mV 이상) 아래라 어차피 봉인 7 을 통과할 수 없다(LUT v2 실데이터:
  하한 = 0.0375 V, nmos·pmos w_key 1000). 값은 LUT memo derived 영역 키 `("sizing_vds_floor", kind, w_key)` 에 슬라이스당 1회.
  [r4] 구간 끝 x = (축 끝 − a)/b 는 부동소수 반올림으로 vds·vsb 가 축 끝을 한 ulp 넘을 수 있어, 1차식 값이 축 안에 들 때까지 반대 끝
  쪽으로 `math.nextafter` 한다(끝점 조회가 정의역 밖이 되지 않게 -- r3 에서는 VDS = 0 끝이 이 때문에도 실패했다). g 평가에서 lut 가
  `lut_target_out_of_range` 를 내면 목표 > branch_max 면 VGS = +inf, 아니면 −inf(부호가 정해진 정의역 밖); 그 밖 LUT 실패는
  `lut_query_failed`. tol = 구간 가운데 점의 writer `tol_v_cell`, [r9] 근 찾기 = `bracket_root`(5.6c; bisection 과 같은 수렴 판정:
  근과의 거리 ≤ tol/2, 평가 수 ≤ 2·k_max(hi − lo, tol) + 상수)이고 `SccLog.iterations`·`k_max` 칸은 변함없이 `k_max(hi − lo, tol)`(hi = lo 면 1,
  선언된 상한이지 실제 평가 수가 아니다), 근 x 뒤 g(x) 가 유한·구간 안이면 그것(한 번 다듬기). 구간이 비거나(lo > hi) 끝 부호가 같으면
  `SealViolationError`(devices (writer,), reason `no_root_in_window`, item = 구간 끝 출처에 `vds_axis` 가 있으면 7 아니면 6,
  margin = 유한한 끝 |h| 최솟값/tol(없으면 None), detail node·lo·hi·h_lo·h_hi·bounds(끝 출처 `rail`·`vds_axis`·`vs_axis`)).
- SCC 순서대로: 비순환 -> 한 번 평가. 크기 1 순환(= 1변수 노드) -> 위 bisection(`SccLog.iterations` = 반복 수, tol·k_max 기록).
  다변수 순환 -> 시작값(1단계: 기둥 위치 비례 평균 V(r1) + (V(r2) − V(r1))·position/length, 기둥 없으면 레일 중앙; 2단계 order
  순: 1변수 노드는 투영 bisection, 그 밖 MOS writer 는 VDS = 레일 범위/2, VSB = vgs_gate 면 현재값·vgs_source 면 0 에서 writer
  식 1회, 저항은 writer 식, W4 그대로) 뒤 `gauss_seidel`(width = 레일 범위, devices = entry.devices, 허용오차 =
  SCC 의 writer MOS(없으면 d·s·bulk 값이 있는 entry.devices)의 `tol_v_cell` 최솟값; 모두 None -> `SealViolationError`
  reason `tol_v_undefined`). [r2] **반복 중(strict=False) 투영**: 1변수 노드는 근이 없거나 구간이 비면 |h| 가 작은 구간 끝
  (빈 구간이면 두 끝 가운데), 그 밖 MOS writer 의 `lut_axis_out_of_range`·`lut_target_out_of_range`·[r4] VDS 정의역 하한 아래에서
  난 `lut_curve_undefined`(하한 이상에서 난 것은 반복 중에도 실패), W4 빈 창은 현재 값 유지 -- [r4] **시작값 2단계(투영 bisection·
  MOS writer 식 1회, 조회 VDS = 레일 범위/2)도 반복의 일부(strict=False)**라 같은 규칙으로 그 노드의 현재(1단계) 값을 유지하고,
  실패는 수렴 뒤 strict 검증 바퀴에서만 낸다 --
  이웃의 과도 반복값 때문에 수렴할 θ 를 거부하지 않게. **수렴 뒤 strict 검증 바퀴**: SCC 노드마다 writer 식을 strict 로 다시
  재서(1변수는 bisection 전체, 실패는 위 구조화 실패 그대로) |새 값 − 수렴값| > tol 이면 `NonconvergentError`(reason
  `strict_recheck_residual`, margin = 잔차/tol, detail node·nodes) -- 투영이 최종값에 남지 않는다.
- [r6] **Newton 으로 바꾸는 조건과 절차**(다변수 SCC 만, 크기 1 은 위 bisection 그대로):
  1. `gauss_seidel` 이 `NonconvergentError` 를 내면(측정한 Δ 열의 수축비 q 가 1 이상이라 K_max 에 닿거나, q < 1 이지만
     q^(K_max−k)·max(1, q/(1−q))·Δ > tol -- 둘 다 'Gauss-Seidel 이 K_max 안에 노드전압 오차 상계 tol 에 닿지 못한다'는 반복 자체의 데이터), 또는
  2. 수렴 판정 뒤 strict 검증 바퀴가 `NonconvergentError`(strict_recheck_residual)나 `SealViolationError`(반복 중 투영으로 멈춘 노드의
     writer 식이 수렴점에서 정의역 밖)를 내면,
  그 실패를 내지 않고 감쇠 Newton 으로 바꾼다. [r9 명시] 경우 2 는 **Gauss-Seidel 이 수렴한 뒤**(`solved` 있음)의 `SealViolationError` 만이다.
  Gauss-Seidel 이 수렴하기 전에 난 `SealViolationError`(반복 중 `tol_v_undefined`, strict=False 가 일시 이탈로 보지 않는 LUT 실패)는 Newton 으로
  넘기지 않고 그대로 낸다(수렴점도 Δ 열도 없다; r8 까지는 이때 `deltas` 가 대입되기 전이라 `UnboundLocalError` 로 평가가 죽었다). 시작점 = 다음 후보 중 정의역 안(아래 `newton_system` 이 None 아님)인 첫 것: (a) 시작값
  2단계 값, (b) 경우 2 면 Gauss-Seidel 수렴값, (c) 시작값 1단계(기둥 위치 비례) 값 -- 모두 밖이면 (a)(그러면 `newton_start_outside_domain`).
  Newton 이 수렴하면 같은 strict 검증 바퀴를 다시 돌고 그 실패는 그대로 낸다. Newton 실패(5.5b 사유)는 경우 1 과 경우 2 의
  `NonconvergentError` 면 그대로 낸다(후보 실패 `NonconvergentError`). **경우 2 의 `SealViolationError` 에서 Newton 도 실패하면 GS
  수렴점에서 잰 그 strict 검증 `SealViolationError` 를 그대로 낸다**(r5 와 같은 분류·detail·devices, `__cause__` = Newton 의
  `NonconvergentError`) -- strict 검증 규약은 바뀌지 않는다. Gauss-Seidel 이 수렴하고 strict 검증을 통과하면 Newton 은 돌지 않는다(값·반복 기록이 r5 와 같다).
- [r6] **SCC 잔차와 야코비안**(`newton_system`): r_i = V_i − g_i(V)(g_i = 노드 writer 식, 1변수 노드도 bisection 이 아니라 식 그대로 --
  x 를 읽는 VDS·VSB 항이 대각에 들어간다), J = I − ∂g/∂V(SCC 노드 열만). ∂g/∂V(`writer_grad`):
  MOS writer(부호 s, gate 쓰기 σ = +1, source 쓰기 σ = −1, g = V(known) + s·σ·VGS): VGS 는 lnID(VGS, VDS, VSB) = 목표의 음함수라
  ∂VGS/∂VDS = −1/(gm/gds), ∂VGS/∂VSB = gmb/gm -- 역산 VGS 점의 lut `op_point`(gm_over_id·gm_gds)와 lut `gmb`(같은 점, 폭 w_m,
  gm = gm_over_id·IDu·w_m/L). ∂g/∂V(known) += 1, ∂g/∂V(d) += σ·∂VGS/∂VDS, ∂g/∂V(s) += σ·(∂VGS/∂VSB − ∂VGS/∂VDS),
  ∂g/∂V(b) += −σ·∂VGS/∂VSB(같은 노드는 더한다). 저항 강하: ∂g/∂V(known) = 1. W4: lo 를 정한 이웃(그 이웃 값이 lo 를 엄격히
  올린 마지막 항)에 1 − y, hi 를 정한 이웃에 y(레일 끝이면 없음). 한 노드라도 writer 식이 정의역 밖(`SealViolationError` -- LUT 조회
  실패·빈 창)이면 None. 작성자 측 대조(LUT v2, folded·nmcnr·common_gate 통과 점): 중앙 차분과의 열별 최대 차 ≤ 1.0e−2
  (|J| ≈ 1.2 -- 역산이 쓰는 칸 보간과 순방향 미분의 차), W4 선형 SCC 는 6.6e−12.
- [r6] `SccLog.method` ∈ `SCC_DIRECT`("direct", 비순환)·`SCC_BISECTION`("bisection", 크기 1 순환)·`SCC_GAUSS_SEIDEL`("gauss_seidel")·
  `SCC_NEWTON`("newton"); `fallback` = Newton 으로 바꾼 경우 (원인, q, Gauss-Seidel Δ 열) -- 원인 = "gauss_seidel_stopped"(경우 1) 또는
  strict 검증 실패의 detail reason(경우 2: "strict_recheck_residual"·"lut_query_failed"·"empty_window" …), q = Δ 열 마지막 두 값의
  비(없으면 None); Newton 이면 `deltas` = 반복마다 ‖r‖∞, `iterations` = Newton 반복 수.
- [r3] **실패를 일으키는 최소 구성**(test 작성용):
  - `tol_v_undefined`: 보간 축 VGS·VDS·VS 가 모두 2점인 toy LUT(내부 격자점이 없어 lut CONTRACT 5절 축 양끝 규칙으로 모든
    tol_V 셀이 None) + 1변수 노드가 있는 회로. 작성자 측 확인(2026-10-08): tester conftest 의 toy 식에 VGS = VDS = VS = (0, 1.8)
    로 LUT 를 만들고 M1 nmos (x, x, gnd)(diode) + M2 pmos (x, pb, vdd), pb = 입력 포트(input_dc_v 0.9), θ = L 1 µm·전류 10 µA·
    ln_idu(M1) 아무 값 -> `size_and_seal` 이 `SealViolationError`(devices ("M1",), margin None, detail {reason: tol_v_undefined}).
    1변수 bisection 이 tol 을 먼저 재기 때문에 순환 노드가 하나라도 있으면 걸린다.
  - `strict_recheck_residual`: 방어 검사다. 마지막 Gauss-Seidel 바퀴가 수렴 판정을 통과했는데 그 뒤 앞 노드를 다시 재면 tol 을 넘게
    움직이는 경우 -- SCC 루프 이득이 1 보다 큰데 시작값이 불안정 고정점 근처라 첫 바퀴들이 우연히 작게 움직인 경우에만 생긴다
    (수축 루프에서는 다시 잰 변화 = q·Δ ≤ Δ ≤ tol 이라 구조상 생기지 않는다). 공개 API 만으로 재현되는 최소 구성은 찾지 못했다
    (12절 O12) -- test 가 덮지 못하는 것을 숨기지 않으려고 적는다.
- 종속 MOS: ln_idu = ln(op_point(노드 vgs, vds, vsb).IDu). writer: θ 값.
- path_values: MOS 마다 VGS(좌표 역산, 최종 vds·vsb) 로 gate 에 (`PATH_MOS`, m) V(s) + s·VGS, source 에 V(g) − s·VGS;
  resistor_drop writer 마다 두 끝에 (`PATH_RESISTOR`, r) 상대 끝 ± Δ; free_window 에 (`PATH_Y`, y_key) 자기 값; 고정 relation 에 (`PATH_FIXED`, relation) 자기 값.
- LUT 실패는 `SealViolationError`(devices = 소자, reason `lut_query_failed`, `lut_reason` = 원래 사유(`lut_axis_out_of_range`·
  `lut_target_out_of_range`·`lut_l_not_anchor` …), `device_query` = "vgs_of_coordinate"·"forward_point"·"tol_v_cell"). 계속
  (근사·클램프)하지 않는다.

### 5.5 `gauss_seidel(nodes, values, update, tolerance, width, devices=()) -> (values, (k, deltas, tol, K_max))`
- 반복 k 마다 nodes 순서로 `update(node, current)` 를 바로 반영, Δk = 최대 |변화|, tol = `tolerance(current)`,
  K_max = `k_max(width, tol)`. [r7] **수렴 = 노드전압 오차 상계 ≤ tol**(노드전압이 정본 -- Δ 만으로 받지 않는다):
  Δk = 0 이면 반환(정확한 고정점). 아니면 stop = (k ≥ K_max); k ≥ 3 이고 Δk−1 > 0 이면 q = Δk/Δk−1, q < 1 이면
  m = max(1, q/(1 − q))·Δk ≤ tol 일 때 반환(수축 사상의 사후 상계 ‖V_k − V*‖∞ ≤ q/(1−q)·Δk 와 마지막 걸음 Δk 둘 다 tol 안 --
  q < 1/2 이면 r6 와 같은 Δk ≤ tol; 상계만 쓰면 q ≈ 0.2 에서 한 바퀴 일찍 받아 봉인 1·2 잔차가 tol 을 넘는 점이 생겼다, 10.5),
  아니면 stop = stop or q^max(K_max − k, 0)·m > tol(K_max 반복에서의 같은 양도 tol 초과). q ≥ 1 이거나 k < 3 이면 Δk 가 tol 이하여도
  반환하지 않는다. stop -> `NonconvergentError`(devices, margin = Δk/tol, detail nodes·iterations·deltas·tol·k_max).
  입력 `values` 는 바꾸지 않는다. (r6 까지: Δk ≤ tol 이면 반환 -- 나쁜 조건 SCC 에서 해와 0.2 V 떨어진 점을 받은 사례가 있어 바꿈.)

### 5.5b [r6] `newton_solve(nodes, values, evaluate, tolerance, width, devices=()) -> (values, (k, norms, tol, K_max))`
- `evaluate(values) -> (residuals, jacobian) | None`(n 개 잔차, n × n 행 tuple, 정의역 밖이면 None). `values` 는 바꾸지 않는다.
- 시작점에서 evaluate 가 None 이면 `NonconvergentError`(reason `newton_start_outside_domain`, margin None, iterations 0, norms ()).
- 반복: ‖r‖∞ 를 `norms` 에 더하고 tol = `tolerance(current)`, K_max = `k_max(width, tol)`. J 를 `scipy.linalg.lu_factor`, LU
  대각에 0 이 있으면 reason `newton_singular`(수렴 판정 전 -- 잔차가 작아도 걸음을 못 풀면 오차를 잴 수 없다). Δ = `lu_solve(−r)`.
  [r7] **‖r‖∞ ≤ tol 이고 ‖Δ‖∞ ≤ tol 이면 반환**(현재 점, 걸음은 적용하지 않음; k = 받은 Newton 걸음 수) -- 온전한 Newton 걸음 =
  다음 보정 = 노드전압 오차 추정(2차 수렴). 잔차만 작고 걸음이 큰 점(나쁜 조건 SCC)은 받지 않고 계속 걷는다. (r6 까지:
  ‖r‖∞ ≤ tol 만 -- q ≈ 1.13·κ ≈ 59 toy 에서 해와 0.11 V 떨어진 점을 받은 사례가 있어 바꿈.) 아니면 k ≥ K_max 면 reason
  `newton_iteration_cap`. 선 탐색: α = 1, 1/2, 1/4, … 마다 시험점 V + αΔ(SCC 노드만), 정의역 안이고 ‖r‖₂ 가 줄면 받는다.
  받을 α 없이 α < 1 이고 α·‖Δ‖∞ < tol 이 되거나(더 줄인 걸음은 노드를 tol 보다 덜 움직인다) 시험점이 부동소수로 현재 점과
  같아지면(모든 노드) reason `newton_line_search`.
- 실패는 모두 `NonconvergentError`(devices, margin = ‖r‖∞/tol(시작점 밖이면 None), detail reason·nodes·iterations·norms·tol·k_max).
- 상수 없음: 감쇠 비 1/2(이분), 반복 상한 = bisection 과 같은 K_max(DEC-32), 선 탐색 끝 = tol(걸음 크기)·부동소수 해상도.

### 5.6 `k_max(width, tol)` = ceil(log2(width/tol)), width ≤ tol 이면 1. 양의 유한 수가 아니면 `ValueError`.

### 5.6b (삭제) 옛 `bisect_root` 는 5.6c `bracket_root` 가 대체했고 2026-10-08 삭제했다(운영 호출 0, 독립 test 는 test 쪽 참조 구현을 쓴다).

### 5.6c [r9] `bracket_root(f, lo, hi, tol) -> (x | None, f_lo, f_hi)` (사용자 승인 2026-10-08, 성능 항목 1)
- 옛 구간 bisection 과 같은 약속(f 는 실수 또는 ±inf, f(lo) == 0 이면 lo, f(hi) == 0 이면 hi, 끝점 부호 같으면 (None, f_lo, f_hi), f 는 끝점 2회
  먼저). 다른 점은 중간 점 선택뿐: Brent 법(유한한 점 3개면 역 2차 보간, 2개면 할선, 그 걸음이 구간 안쪽·감소 조건을 못 지키거나 ±inf 점이
  있으면 이분, 걸음이 tol/4 보다 작으면 tol/4 만큼 밀어 반대편을 확인).
- **수렴 판정 (bisection 과 같은 보증)**: 반환 x 는 부호가 바뀌는 구간의 한 끝이고 그 구간 폭 ≤ tol/2 -> 근과의 거리 ≤ tol/2. (bisection: 마지막
  구간 폭 ≤ tol 의 가운데 -> 거리 ≤ tol/2.) 허용오차를 느슨하게 하지 않는다. (bisection 과 답이 서로 tol 이내.)
- 평가 수(끝점 2회 포함) ≤ 2·`k_max(hi − lo, tol)` + 6 (보간 반복이 `k_max` 번을 넘으면 남은 반복은 순수 이분; 해석적 상계, 무작위 2만 함수 측정에서는
  ≤ 2·`k_max`). 숫자 기본값 없음(tol/4 는 판정식의 분수, 부동소수 해상도 2·eps·|x|).
- **h 평가 관측 (test 용)**: `solve_self` 의 h 1회 = `_vgs_signed` 1회 = lut `vgs_for_current_density` 조회 1회([U3] 전에는 `gm_id_for_target`; memo 함수 이름 칸 `vgs_for_current_density`)이며, 그 조회는 `LutMemo.lookup`(point/curve/root 영역)을
  지난다 -- `LutMemo.lookup` 호출 수(적중 포함)나 `_vgs_signed` 호출 수로 센다. `solve_self` 입력 재사용 적중 시 이 호출은 0이다
  (`LutMemo.lookup(region="root", fn_name="solve_self", ...)` 1회만).
- **Brent 만의 약속**: 매끈하고 단순한(단조·거의 선형) 근에서 평가 수가 같은 tol 의 순수 bisection(끝점 2 + k_max)보다 적다(10.7: 실제 회로 h 평가 약
  0.4~0.5배; 무작위 합성 함수 2만 개 평균 0.49배). 불연속·±inf 가 섞인 f 에서는 보증하지 않는다(상계 2·k_max+6 만).
- **입력 검증**: lo·hi 가 유한하지 않거나 lo > hi, tol 이 양의 유한 수가 아님(0·음수·NaN·inf) -> `ValueError`(f 호출 전). lo == hi 는 허용(f 1회씩 두 번
  불러 같은 값이면 부호 같음 -> `(None, …)`, 0 이면 그 끝점). f 가 NaN 을 돌려주면 `ValueError`(끝점이든 내부 점이든 즉시).
- `solve_self` 의 한 입력 재사용: 풀이(근 찾기 + 한 번 다듬기)는 (소자 종류, L, ln IDu, writer 관계, known 값, VDS·VSB 의 x 1차식 계수 4개, 구간
  lo·hi, tol) 만의 함수라 LUT memo `root` 영역(함수 이름 칸 `solve_self`, BoundedLRU 상한)에 그 키로 저장한다 -- 적중하면 h 평가 0. 근 없음
  (None, h_lo, h_hi) 도 저장되나 예외는 저장하지 않는다(부르는 쪽이 strict 에 따라 만든다). `_Circuit.tolerance` 는 한 평가(= 한 `dc_columns`
  호출) 안에서 같은 (소자, VDS) 의 `tol_v_cell` 조회를 한 번만 한다(성능 항목 6).

### 5.7 `dc_widths(snapshot, lut)` -- `DeviceOp`
- reads node.{dc_v, dc_rail_v}, device.{dc_current, dc_L, dc_ln_idu, pins, kind, bulk}. MOS 마다 vgs·vds·vsb(크기),
  op = lut op_point(노드 점), W = ID·L/exp(ln_idu), gm_id = op.gm_over_id, idu_forward = op.IDu, w_key = `w_keys[kind]`.

## 6. 봉인 (`seal_dc(snapshot, calls, lut, resistances, raise_on_violation=True, *, base, donors, counters) -> DcEvaluation`)

순서: `dc_tolerances(lut)` -> 1 `dc_seal_node_conflict()` -> 2 `dc_seal_vgs_match()` -> 3 `dc_seal_kcl(resistances)` -> 6
`dc_seal_bulk_reverse()` -> 7·9 `dc_seal_region(lut)`([r10] 영역 판정 한 블록 -- 소자마다 `judge_region` 한 번, 두 항목) -> 8 `dc_seal_kvl_branch()` ->
4 `seal_versions(snapshot, calls + 위 7개, base)` -> 5 `seal_writers(snapshot)` -> `dc_seal_report(item4, item5)`.

[r3] **`calls` 형식**(`seal_dc`·`seal_versions` 공통): ((ComputeBlock, extras), ...) -- extras = 그 블록을 부를 때 넘긴 추가 인자
tuple(블록 함수 호출 `block(snapshot, *extras)` 의 `extras` 그대로, 없으면 ()). `size_and_seal` 은 `((dc_currents,
(θ 전류 쌍 tuple,)), (dc_lengths, (θ L 쌍 tuple,)), (dc_columns, (θ 쌍, fixed_values, resistor_values, lut)), (dc_widths,
(lut,)))` 를 넘기고 `seal_dc` 가 봉인 블록 7개([r10] 7·9 는 블록 하나)를 같은 형식으로 덧붙여 `seal_versions` 에 넘긴다. base writer(`ctx.base.block_versions`)는 calls 에 들지 않는다 -- 봉인 4 (4) 서로소 단언, parent 검사 = base writer 전부.

`judge(item, rows)`(rows = (대상, 크기, tol 또는 None, devices, nodes)): tol 이 정의된 행 중 크기 > tol 이 있으면 fail(대상 = 그
행들), 없고 tol None 행이 있으면 undefined(대상 = 그 행들), 그 밖 pass. magnitude·tol·margin = margin 최대 행(fail 이면 fail 행
중), 행이 없으면 None. detail = n_checked·n_undefined·worst(대상) 키 정렬.
[r3] **margin** = 크기/tol(core `normalized_margin`), 단 **tol == 0 이면 크기 > 0 -> +inf, 크기 ≤ 0 -> 0.0**(core 는 tol 0 에
None 을 주지만 봉인에서는 '허용오차 0 을 넘은 위반' = 무한 위반이다; core 는 바꾸지 않고 sizing 이 정한다). **최대 margin 동률**이면
대상 이름(rows 의 첫 칸, 문자열 비교)이 가장 큰 행이 대표(`worst`)다.

| # | 블록 | 판정 |
|---|---|---|
| tol | `dc_tolerances` | dc_tol_v = lut `tol_v_table(kind, w_key).at(L, vds, "id_equivalent")`(None 가능), dc_gm = dc_op.gm_id × dc_op.current(자기 동작점 gm, 봉인 3 tol_I·`ss_dev`·b_P·영점 상쇄 R 공용, 설계 40 §3.7-3 v1.6) |
| 1 | `dc_seal_node_conflict` | 노드마다 spread = max − min of {노드 값} ∪ path_values; tol = 닿는 PATH_MOS 소자 tol_v 최댓값(정의된 것), 없으면 None; MOS 관계가 없는 노드는 n·eps·max|V|(n = 값 수) |
| 2 | `dc_seal_vgs_match` | MOS 마다 |ln idu_forward − ln_idu| / gm_id ≤ tol_v |
| 3 | `dc_seal_kcl` | [r3] 행 = DC 원소(`basis.ends` -- MOS·DC 저항·이상원, 가지치기 저항 제외)의 from·to 로 한 번이라도 나오는 레일 아닌 넷마다(DC 원소가 닿지 않는 넷 -- gate 전용 넷·커패시터만 닿는 넷 -- 은 행이 없고 n_checked 에 들지 않는다) |Σ from − Σ to|, MOS = idu_forward·W/L, 저항 = (V(from) − V(to))/R, 이상원 = dc_current; tol = tol_I = 채널이 닿는 MOS 의 tol_V·dc_gm 최댓값(설계 40 §3.7-3 v1.6 -- `dc_gm` = 자기 동작점 gm, `dc_tolerances` 필드; 정의된 것; MOS 는 있는데 모두 None 이면 None), MOS 없는 넷은 n·eps·Σ|I| |
| 4 | `seal_versions` | calls 의 블록마다 fp_of((이름, code_hash, Projection.from_snapshot(snapshot, reads, extras).fp)) == block_version 이고 그 블록 writes 필드의 input_version == block_version. 위반 블록 = detail `blocks`. 추가 단언 [IT-2a] (3) coverage: 스냅샷 모든 필드의 writer ∈ base writer(`base.block_versions` 키) ∪ calls 블록 이름, 위반 = detail `foreign_writers`(정렬 tuple); (4) 서로소: base writer ∩ calls 블록 이름 = ∅, 위반 = detail `base_call_overlap`(정렬 tuple). 두 키는 위반일 때만(해당 tuple 이 비어 있지 않을 때만) detail 에 더한다 -- 평소 detail 은 `blocks`·`n_checked` 둘. magnitude = 위반 이름 수 합, tol 0 |
| 5 | `seal_writers` | 모든 필드 writer == 권한표 writer; 노드마다 dc_writer 있음, (tier == W0) == is_rail, dc_rail_v·dc_v 중 정확히 하나, dc_rail_v 있음 == is_rail. 위반 노드 = nodes, 위반 필드 = detail `fields` |
| 6 | `dc_seal_bulk_reverse` | [r10] MOS 마다 `junction_forward(vds, vsb)` = max(0, −vsb, −(vds + vsb)) **> 0 이면 fail**(크기 무관 -- 경계 0 V, 문턱 없음), 0 이면 pass. `tol_V`(`dc_tol_v`)는 판정에 쓰지 않고 띠 기록만: detail `indistinct` = 순방향 0 이고 min(vsb, vds + vsb) < tol_V 인 ((소자, 값), ...), `band_undefined` = tol_V 미정 소자(항목을 미정으로 만들지 않는다). magnitude·tol·margin·worst·n_checked 는 `judge` 보고 형식 그대로(크기/tol_V -- 판정에 쓰지 않는다) |
| 7 | `dc_seal_region` | [r10] `device.dc_op` 의 MOS 마다 `judge_region(소자, 선언, 전류, VDS, vdsat)`(선언 = `device.region_decl` 의 region, 없으면 None)을 한 번 부르고 거부 판정 `region_mismatch` 중 triode/saturation 쪽(표 행 3·8·10)이 하나라도 있으면 fail(devices = 그 소자), 아니고 행 6(`unresolved` -- VDSAT 열 없음, lut `lut_column_unavailable`)이 있으면 undefined(devices = 그 소자, detail `reason` = `lut_vdsat_column_missing`), 아니면 pass. vdsat 입력: VDS < 0 이면 LUT 조회 없이 None, 아니면 그 점 LUT `vdsat`(열 없음 None, 축·L 위치 밖 `OUT_OF_DOMAIN`). 수치 문턱 없음(VDS = VDSAT 정확히는 포화). **출력 전용 기록**(판정을 바꾸지 않는다): detail `slack_v`(vdsat 이 수인 소자 중 최소 VDS − vdsat), `reverse_vds`(행 3 소자), `indistinct`(|VDS − vdsat| < tol_VDsat 인 ((소자, VDS − vdsat), ...), tol = lut `tol_vdsat_table(...).at(L, vds)`), `indistinct_undefined`(tol 미정·조회 실패 소자). magnitude·tol·margin 은 None |
| 8 | `dc_seal_kvl_branch` | S1 rel_kvl_branch 엣지마다 Σ_멤버 |ln idu_forward − ln_idu|/gm_id ≤ Σ 멤버 tol_v(하나라도 None 이면 None). [r3] 행 대상 이름(= detail `worst` 값) = 엣지 `members`(S1 이 정한 순서 그대로)를 `"+"` 로 이은 문자열(예 `"M1+M2+M3+M4"`), devices = members |
| 9 | `dc_seal_region` | [r10] 같은 블록의 둘째 항목: `cutoff`(선언 없음·triode 소자의 ID ≤ 0, 표 행 2)가 하나라도 있으면 fail(devices = 그 소자), 아니고 `out_of_domain`(행 5)이 있으면 undefined(devices = 그 소자, detail `reason` = `out_of_domain`), 아니면 pass. 출력 전용 기록 detail `domain_edge` = LUT 표본 끝에 닿은 ((소자, 축), ...)(`lut_axis_bounds`, 축 ∈ L·VGS·VDS·VS, 닿음 = 값 ≤ 축 첫 값 또는 ≥ 끝 값). 옛 VGS = 0 누설 조회와 소자별 누설·바닥 필드 둘은 삭제. magnitude·tol·margin 은 None. 통과한 봉인점의 선언 없는 MOS 는 모두 ID > 0, VDS ≥ VDSAT |

`SealReport.status`: fail 있으면 `REPORT_VIOLATED`("violated"), 아니고 undefined 있으면 `REPORT_UNDEFINED`, 아니면
`REPORT_SEALED`. items = item 번호순 9개([r8]; 7·9 는 writer `dc_seal_region` 하나). 결과: violated -> `SealViolationError`(devices = margin 최대 fail 항목의 devices,
margin = 그 margin, detail = item·nodes·items((번호, 상태, margin) 9개)·item_detail). [r3] fail 항목 선택 키 = (margin, 항목
번호) 최대 -- margin None(봉인 4·5 처럼 정규화가 없는 항목)은 +inf 로 치고, 동률이면 번호가 큰 항목. undefined -> `DcEvaluation(sealed=None)`.
sealed -> `DcEvaluation(sealed=SealedSnapshot(snapshot, report))`. [r4] VDSAT 열이 있는 LUT(v2)에서는 1~8([r8] 1~9)이 모두 pass 인 점이
SealedSnapshot 이 된다(10.2절 실측). 열이 없는 LUT 세트에서는 항목 7 이 undefined 라 여전히 나오지 않는다.

## 7. `size_and_seal(ctx, theta, parent=None) -> DcEvaluation`

- ctx 가 KernelContext 아님 -> `TypeError`. theta = Mapping 또는 `Theta` -> `check_theta`. parent 가 DcEvaluation 이 아니거나
  base writer 전부(`ctx.base.block_versions` 키)의 block_version 이 하나라도 다르면 `ValueError`.
- 시작 스냅샷 = `parent.snapshot.derive_child(keep)`(keep = base writer ∪ 커널 블록 ∪ `SEAL_ITEM_BLOCKS`) 또는 ctx.base. 호출 = `dc_currents((θ current 키, 값) ...)` -> `dc_lengths((L ...))` ->
  `dc_columns((((kind, key), v) for ln_idu·resistance·y), ctx.fixed_values, ctx.resistor_values, ctx.lut)` ->
  `dc_widths(ctx.lut)` -> `seal_dc(..., resistances = ctx.resistor_values + θ resistance 쌍)`. [r10] `off` 선언 소자가 있으면 `dc_lengths` 둘째 인자로 그 이름 tuple 을 준다(L 은 선언 `l_m`, θ 에 L 성분 없음), `dc_columns` 다섯째 인자 = `triode` 선언 소자 tuple(없으면 생략).
- **재사용 계약**(확정 사항 1·5): 같은 θ·parent 로 부르면 DC 13블록 computes 0, 커널 4·봉인 항목 8 outcome `reuse`(합 12), `dc_seal_report` outcome `graft` 1(keep 밖 -- 같은 입력이면 S3 graft, design 41 v1.12.8 753·756).
  θ 한 성분만 다른 parent 에서: `current` 성분 -> dc_currents·dc_widths·dc_tolerances 와 그 하류 봉인만 다시(DC 저항 전류가
  바뀌지 않으면 dc_columns·봉인 1 은 reuse), `ln_idu`·`y`·`resistance` -> dc_columns 와 하류(dc_currents·dc_lengths reuse).
  하류 봉인 항목 블록은 입력 값이 같으면 reuse, `dc_seal_report` 는 parent 경로에서 입력이 같으면 graft(reuse 아님).
  [r5] `capacitance`·`ss_resistance`(`THETA_PASSIVE_KINDS`) 성분만 다른 θ 를 parent 에서 부르면 **dc 블록 전부 computes 0**(커널 4·봉인 항목 8 `reuse` 12, `dc_seal_report` `graft` 1)
  (어느 블록의 extras 에도 들지 않는다 -- `seal_dc` 의 `resistances` 도 θ `resistance` 만). 결과는 parent 와 같은 봉인 상태이고,
  소신호 쪽은 metrics `ss_evaluate` 에서 `ss_dev` graft(parent 경로 -- 입력 같음)·`metrics_ss`·`metrics_dc` 만 계산(metrics CONTRACT 7.6).
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
| [r2] 다변수 SCC strict 검증 잔차 > tol (r6: Newton 뒤 검증에서만 -- Gauss-Seidel 뒤 실패는 Newton 으로 바꾼다) | ④ | NonconvergentError | strict_recheck_residual | SCC 소자 | 잔차/tol |
| [r6] Newton 시작점 정의역 밖 / 영 피벗 / 선 탐색 실패 / K_max 도달 | ④ | NonconvergentError | newton_start_outside_domain / newton_singular / newton_line_search / newton_iteration_cap | SCC 소자 | ‖r‖∞/tol (시작점 밖 None) |
| LUT 축 밖·목표 밖·앵커 아님 | ④⑤·tol·[r4] 봉인 7(device_query `vdsat`·`tol_vdsat_cell`)·[r8] 봉인 9(device_query `off_current`) | SealViolationError | lut_query_failed + lut_reason | 소자 | LUT 값(None) |
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
  (`writer_edge` {M1a, M1b}·{M4a, M4b}, `w4_root` {Vim, Vip}, `current_pivot` {R1, R2}). 통과 θ 를 σ 로 옮긴
  7회로의 dc_v 최대 차 = 0.0(비트 동일).

## 10. 9회로 실측 (2026-10-07, 이 커밋 코드, 작성자 측 시연 -- 정본 아님)

LUT = `_drafts/engine/lut_slices/manifest.json`(32 슬라이스) + 옛 기준 LUT(옛 sample LUT 는 O-180 으로 삭제 -- 기록), w_keys =
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
  중복은 전부 LUT memo hit(계산 0). `TolVTable.at` 494/158 은 memo 밖 표 조회(O9; [r9] 에서 한 평가 안 재사용으로 닫음).

### 10.2 [r4] LUT v2 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님)
LUT = `resolve_lut_location(assets/lut_v2_location.json, os.environ)`(재생성 슬라이스 32개 GMBS·VDSAT 포함 + 기준 LUT + 검증 중점),
LutSpec grid = tlef MANUFACTURINGGRID, w_keys = `pre_layout_lut_access`(nmos·pmos 1000). 탐침 θ 는 10절 규칙(L 1 µm, writer gm/ID
{8..24}×y {0.25, 0.5, 0.75} 15점 + 전류 LP(scipy linprog), 무작위 200개 seed 20261008, 탐침 R 10 kΩ) = 회로당 215 θ.
'일관' = 봉인 1·2·3·4·5·6·8 pass. 봉인 7 margin 은 6절 표의 N3.14 방향(> 1 = fail).

| 회로 | 일관: r3 코드(master) | 일관: r4 VDS 하한만 | SealedSnapshot (r4) | 봉인 7 fail (r4) | 봉인 7 fail 대표 소자 | fail margin 최소 | 통과 margin 최대 | 평가 ms p50/p90 |
|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 181 | 181 | 140 | 41 | M1 21, M3 16, M2 4 | 7.18 | −1.21 | 21/32 |
| current_reuse_telescopic_ota | 0 | 0 | 0 | 0 | -- | -- | -- | 144/189 |
| folded_cascode | 0 | 76 | 22 | 54 | M5 24, M4 14, M3 8, M11 4 | 1.45 | −0.40 | 130/244 |
| ngcc_3stage_ff | 0 | 86 | 65 | 21 | M0 18, M14 2, M7 1 | 2.98 | −1.16 | 37/104 |
| nmcnr_amplifier | 0 | 57 | 17 | 40 | M301 22, M107 5, M104 4, M101 4 | 1.84 | −4.37 | 32/140 |
| pushpull_follower_buffer | 0 | 7 | 2 | 5 | M6 4, M5 1 | 59.9 | 0.63 | 29/41 |
| sf_pushpull_output_opamp | 0 | 1 | 0 | 1 | M8 1 | 63.3 | -- | 122/208 |
| two_stage_ota | 0 | 96 | 70 | 26 | M2 9, M5 7, M1 6, M6 2 | 3.96 | 0.78 | 23/58 |
| two_stage_ota_sf | 0 | 72 | 50 | 22 | M5 7, M2 6, M6 4, M9 3 | 3.12 | −0.05 | 28/88 |

- r3 코드(master)에서 8회로가 0 인 것은 1변수 bisection 구간 끝 VDS = 0 의 `lut_curve_undefined`(LUT v2 의 VDS = 0 열) 때문이다
  (회로당 215/215 가 그 사유; common_gate 는 1변수 노드가 없다). r4 VDS 하한 뒤 남은 대표 실패: `no_root_in_window`(item 7) --
  current_reuse 210, folded 100, ngcc 120, nmcnr 125, two_stage 94, two_stage_sf 131; pushpull `lut_axis_out_of_range`(VS 축) 199;
  sf_pushpull 하한 아래(VDS = 0) `lut_curve_undefined` 158(strict 경로 -- 실패 유지)·NONCONVERGENT 29; common_gate NONCONVERGENT 26.
- SealedSnapshot + 봉인 7 fail = 일관 점 수('r4 VDS 하한만' 열, 봉인 7 판정 전 실행)와 회로마다 같다(같은 seed 두 실행의 개수 대조 --
  봉인 7 판정이 다른 항목·노드전압 풀이를 바꾸지 않는다).
- 옛 12-L 세트(VDSAT 열 없음)에서 같은 탐침: two_stage_ota·common_gate·folded 의 일관 점 15·24·10 개가 모두 undefined + reason
  `lut_vdsat_column_missing`, SealedSnapshot 0(열 없는 세트의 정직한 경로 유지).
- 시간: 봉인 7 은 소자마다 `vdsat` 1회(point memo) + `TolVdsatTable.at`. 평가 중앙값은 VDS 하한만 넣은 실행과 같은 수준(잡음 범위,
  다른 agent 부하 있음). `tol_vdsat_table` 은 kind 마다 프로세스당 1회(derived memo).

### 10.3 [r5] DEC-92 수동소자 θ 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님)
LUT·탐침 = 10.2 와 같음(seed 0, 회로당 첫 SealedSnapshot 점). θ `capacitance` = 1 pF, θ `ss_resistance` = 10 kΩ(탐침값, 설계값 아님).
spec 제약 + 관측 요청(`gbw_ss_hz`·`ugf_ss_hz`·`pm_ss_deg`·`gain_ss_db`, 로더 기본 뷰 port / loop β = 1)을 metrics `ss_evaluate` 로 평가.

| 회로 | engine 원소 | θ 수동 성분 | zero_cancel (end, far, S, reason) | 구조 R (Ω) | 탐침 수 | GBW (Hz) | PM (°) | 수동 θ ×1.1 뒤 dc 블록 computes / ss (ss_dev, metrics_ss, metrics_dc) |
|---|---|---|---|---|---|---|---|---|
| ngcc_3stage_ff | Cm1, Cm2 | capacitance Cm1, Cm2 | -- | -- | 4 | 1.890e8 | 214.98 | 0 / (0, 1, 1) |
| nmcnr_amplifier | Cm1, Cm2, Rm | capacitance Cm1, Cm2 | Rm: Vout, {NodeM2, NodeS2}, {M301}, None | 870.7 | 23 | 8.222e6 | −40.49 | 0 / (0, 1, 1) |
| two_stage_ota | Cc, Rz | capacitance Cc | Rz: O1, {OUT}, {M6}, None | 838.6 | 6 | 1.178e8 | 15.46 | 0 / (0, 1, 1) |
| two_stage_ota_sf | Cc | capacitance Cc | -- | -- | 6 | 1.237e8 | −12.36 | 0 / (0, 1, 1) |

- r4(master)까지 이 네 회로의 소신호 요청은 전부 `passive_value_undeclared`(search S-20). r5 에서 모든 요청이 값(Undefined 0) --
  spec 판정 제약 `gbw_ss_hz`·`pm_ss_deg`(ngcc·nmcnr), `gain_ss_db`(two_stage·two_stage_sf), `rout_ss_ohm`(two_stage_sf 685.2 Ω) 포함.
  값은 탐침 θ 의 값이라 판정 통과 여부는 뜻이 없다(PM 214.98° 처럼 metrics PM 정의 범위 밖으로 보이는 값은 metrics 쪽 관찰로 남긴다).
- 같은 θ 를 lineage 에서 다시: dc 블록 computes 0·ss 블록 computes 0, 값 비트 동일(4회로). 수동 θ 만 ×1.1: dc 12블록 모두 reuse
  (`size_and_seal` 8.9~21.8 ms -- 계산 0 인 호출의 남은 비용, 프로파일은 재지 않음), ss 쪽 `ss_dev` reuse·`metrics_ss`·`metrics_dc` 1회씩, `gain_ss_db`
  는 수치상 불변(이 시연 4회로에서는 출력 자릿수 그대로; 독립 test 실측으로 `ss_resistance` 만 바꾸면 1 ulp 차가 날 수 있어 비트 동일을
  계약하지 않는다 -- metrics S-16)·GBW/PM 변화(예 two_stage GBW 1.178e8 -> 1.093e8).
- 9회로 판정(일반성): 수동 θ·구조 규칙이 생기는 회로는 engine 수동소자가 있는 6회로뿐 -- common_gate·folded·pushpull 은 engine
  수동소자가 없어 무동작(θ 차원 불변). sf_pushpull = capacitance Cc 만(R1a~R1c 는 DC 경로 engine 저항 = 기존 `resistance`),
  current_reuse(파일럿) = capacitance Cc1·Cc2, Rz1: Vop1 / {Vom} / {M16}, Rz2: Vom1 / {Vop} / {M26} 구조 규칙(R1·R2 는 DC 경로
  `resistance`). θ 폴백(`ss_resistance`)은 library 9회로에서 0건 -- toy(CS + Rz–Cz 를 out–gnd 에 건 망)에서 `ZC_NO_CELL` -> `ss_resistance`
  θ 가 소신호에 들어가고, Cz 를 out–in 에 걸면 S = {M1} 구조 규칙으로 바뀌는 것을 확인(dc 블록 reuse 동일).
- 이름 전단사(테스트 helper `rename`, seed 1·2, `engine_elements` 도 σ 로 옮김): 9회로 모두 θ 수동 성분 집합·`zero_cancel`(end·far·
  S·reason)이 σ 로 옮겨진 것과 같다.

### 10.4 [r6] SCC 감쇠 Newton 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님)
탐침 = 10절 θ 생성기(LUT v2, seed 20261008, 회로당 215 θ: gm/ID 탐침 × y 탐침 격자 + 난수, θ `resistance` 10 kΩ·`capacitance`
1 pF 탐침값). '일관' = `size_and_seal` 이 실패 없이 돌고 봉인 7 외 항목이 모두 통과, '봉인' = SealedSnapshot. before = master
(Gauss-Seidel 만), after = 이 개정(선 탐색 α·‖Δ‖∞ < tol 정지, 경우 2 SealViolationError 유지 규칙 포함 최종 코드). ms = 점당
`size_and_seal` 시간 p50/p90, 합 = 215 점 합(s).

| 회로 | 일관 before -> after | 봉인 before -> after | ms p50/p90 before -> after | 합 s | after 실패 reason(상위) |
|---|---|---|---|---|---|
| common_gate_amplifier | 190 -> 207 | 144 -> 155 | 21.7/29.6 -> 25.0/32.3 | 27 -> 31 | NONCONVERGENT 17 -> 0 |
| current_reuse_telescopic_ota | 0 -> 0 | 0 -> 0 | 125.1/175.5 -> 151.4/193.5 | 29 -> 34 | 봉인 7 no_root_in_window 208(변화 없음) |
| folded_cascode | 79 -> 84 | 31 -> 31 | 141.5/256.1 -> 182.7/305.0 | 30 -> 36 | no_root_in_window 96, strict_recheck_residual 2 |
| ngcc_3stage_ff | 90 -> 90 | 74 -> 74 | 40.3/116.4 -> 40.0/114.2 | 13 -> 13 | 변화 없음 |
| nmcnr_amplifier | 57 -> 57 | 20 -> 20 | 38.3/136.6 -> 35.8/156.8 | 12 -> 14 | 변화 없음 |
| pushpull_follower_buffer | 6 -> 6 | 1 -> 1 | 29.4/37.9 -> 25.5/34.4 | 6 -> 5 | 변화 없음(lut_axis_out_of_range 190) |
| sf_pushpull_output_opamp | 2 -> 5 | 0 -> 0 | 135.1/253.2 -> 218.5/361.0 | 33 -> 51 | lut_curve_undefined 180 -> 172, newton_line_search 10 |
| two_stage_ota | 101 -> 101 | 72 -> 72 | 40.6/83.9 -> 29.9/72.2 | 8 -> 7 | 일부 재분류(lut_axis_out_of_range 9) |
| two_stage_ota_sf | 56 -> 56 | 38 -> 38 | 21.4/70.4 -> 21.4/67.4 | 6 -> 6 | 일부 재분류(lut_axis_out_of_range 4) |

- 일관·봉인 수가 줄어든 회로 없음(9회로). 늘어난 곳: common_gate +17 일관·+11 봉인(W4–W4 선형 SCC, O11), folded +5, sf_pushpull +3.
- 실패 θ 에서 Newton 도 해를 못 찾은 경우 경우 2(strict 검증 `SealViolationError`)는 그 위반을 그대로 내므로 reason 분포가 before 와
  거의 같다. 정체 증거(sf_pushpull, 선 탐색 조기 정지·유지 규칙 전 실행): 실패 θ 의 반복별 ‖r‖∞ 가 0.22~0.30 V 에서 멈추고
  `newton_iteration_cap` margin ≈ 250~350 -- 정의역 안 극소가 0 이 아닌 잔차라 그 θ 에는 정의역 안 해가 없다고 본다(증명 아님, 관찰).
- 시간: 늘어난 비용은 실패 θ 에서 도는 Newton 이다. 선 탐색 조기 정지(α·‖Δ‖∞ < tol) 전 실행은 sf p50/p90 605/924 ms·folded
  275/661 ms 였고 정지 규칙으로 218/361·183/305 ms 로 줄었다(통과 수 동일).
- current_reuse 는 0 그대로: 주 원인이 SCC 풀이가 아니라 봉인 7 writer 창 no_root_in_window(208/215) -- 이 개정 범위 밖.
- 야코비안 대조(순환 SCC 가 있는 회로의 첫 봉인 θ, 중앙 차분 h = 1e-5 V): MOS writer 열 max|FD − J| ≤ 1e-2(|J| ≈ 1.2, LUT
  Hermite 미분과 차분의 차), W4 선형 노드 6.6e-12.

### 10.5 [r7] 수렴 판정 = 노드전압 오차 상계 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님)
탐침 = 10.4 와 같음. before = master 7db148e(r6), after = r7. 두 실행을 연달아 같은 기계에서 돌렸다.

| 회로 | 일관 | 봉인 | ms p50/p90 before -> after | 합 s |
|---|---|---|---|---|
| common_gate_amplifier | 207 -> 207 | 155 -> 155 | 19.1/28.3 -> 14.3/21.6 | 20.3 -> 15.8 |
| current_reuse_telescopic_ota | 0 -> 0 | 0 -> 0 | 111.4/153.7 -> 77.6/111.4 | 25.5 -> 19.0 |
| folded_cascode | 84 -> 84 | 31 -> 31 | 110.3/190.1 -> 116.3/197.5 | 22.6 -> 22.7 |
| ngcc_3stage_ff | 90 -> 90 | 74 -> 74 | 34.3/89.4 -> 24.9/69.6 | 10.4 -> 8.3 |
| nmcnr_amplifier | 57 -> 57 | 20 -> 20 | 27.5/98.8 -> 27.0/99.3 | 9.0 -> 9.3 |
| pushpull_follower_buffer | 6 -> 6 | 1 -> 1 | 14.3/20.7 -> 15.2/23.3 | 3.2 -> 3.4 |
| sf_pushpull_output_opamp | 5 -> 5 | 0 -> 0 | 129.4/217.0 -> 177.1/290.4 | 30.6 -> 40.4 |
| two_stage_ota | 101 -> 101 | 72 -> 72 | 22.8/50.3 -> 21.0/53.5 | 5.2 -> 5.7 |
| two_stage_ota_sf | 56 -> 56 | 38 -> 38 | 11.1/44.1 -> 14.2/53.0 | 4.1 -> 5.0 |

- 점 수 변화 없음(9회로). 점별 비교(θ 마다 두 코드의 SCC 풀이값): 두 쪽 모두 푼 SCC 의 노드전압 차 최대 = common_gate 6.9e-4·
  sf_pushpull 4.6e-4·folded 1.2e-4·nmcnr 4.9e-5·current_reuse 1.6e-6 V(모두 그 SCC tol ≈ 8.5e-4 V 미만), 최종 dc_v 차 최대 8.0e-4 V.
  r6 GS 가 받은 수렴 중 새 상계로 tol 초과였던 것: common_gate 5·folded 1·sf_pushpull 4(나머지 958 은 상계 ≤ tol) -- r7 은 그 SCC
  를 더 돌리며 값이 tol 미만만큼 바뀐다. 이 코퍼스에서는 tol 을 넘게 틀린 채 받아진 점이 없었다.
- toy(test_scc_newton `ctx_q`, y = 0.99·z* = 0.3, q ≈ 1.13): r6 Newton 은 ‖r‖∞ = 3.8e-3 ≤ tol(1.8e-2)에서 받아 닫힌 해와 0.110 V
  차, r7 은 ‖Δ‖∞ > tol 이라 한 걸음 더(‖r‖∞ 4.9e-6) -> 차 1.4e-4 V. y = 0.9·z* = 1.0 은 두 쪽 같음(1 걸음, 차 0.017 V < tol).
- 상계만 쓰는 GS 판정(오케스트레이터 문안 그대로)을 먼저 재 보니 folded 2 점(θ 83·111)이 일관 -> 불일치로 떨어졌다: q ≈ 0.2 에서
  q/(1−q)·Δ3 = 7.3e-4 ≤ tol 이라 k = 3 에 받았는데(r6 은 Δ4 ≤ tol 인 k = 4), 봉인 1·2 가 1.20·1.53 으로 실패(r6 점은 0.46·0.62).
  그래서 Δk ≤ tol 도 함께 요구한다(5.5 m = max(1, q/(1−q))·Δk) -- q < 1/2 이면 r6 와 같고 q ≥ 1/2 에서만 상계가 더 엄격하다.
- 시간: 같은 순서로 연달아 잰 두 실행 사이 SCC 와 무관한 회로도 ±25% 흔들려(ngcc −20%, two_stage_sf +24%) 차이를 r7 탓으로
  나누지 못한다. sf_pushpull +32%(합 30.6 -> 40.4 s)는 실패 θ 의 Newton 이 수렴 판정 전에 LU 를 매 반복 풀고, 잔차만 작은 점에서
  멈추지 않고 더 걷는 몫으로 본다(분리 측정 안 함).

### 10.6 [r8] 봉인 9 전도 여유 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님)
before = master 6d6e708(r7), after = r8. 두 탐침, 9회로.

**(a) 표준 탐침(10.4 와 같음 -- ln_idu 는 gm/ID 6~26 의 VGS, 전류 1~100 µA)**: 일관·봉인 수 9회로 모두 그대로(common_gate 207/155,
folded 84/31, ngcc 90/74, nmcnr 57/20, pushpull 6/1, sf_pushpull 5/0, two_stage 101/72, two_stage_sf 56/38, current_reuse 0/0). 봉인 9
margin 최댓값 ≤ 1.0e-3 -- 이 탐침은 봉인 9 가 겨누는 영역(VGS ≈ 0)에 닿지 않는다.

**(b) 약반전 탐침**(scratch `lowvgs_probe.py`: (a) 와 같되 ln_idu = VGS ~ U(0.02, 0.35) V(VDS = 레일 범위/2, VSB 0, L 1 µm)의 ln IDu,
전류 10^U(−13, −5) A, 회로당 200 θ, seed 20261008):

| 회로 | 일관 before -> after | 봉인 before -> after | 봉인 9 만 실패(7 제외 통과) | 봉인 9 margin 최소/중앙/최대 |
|---|---|---|---|---|
| common_gate_amplifier | 192 -> 84 | 191 -> 84 | 108 | 0.005 / 1.81 / 24.8 |
| current_reuse_telescopic_ota | 0 -> 0 | 0 -> 0 | 0 | -- |
| folded_cascode | 138 -> 42 | 121 -> 40 | 96 | 0.024 / 2.71 / 14.8 |
| ngcc_3stage_ff | 162 -> 14 | 148 -> 14 | 148 | 0.14 / 7.44 / 20.4 |
| nmcnr_amplifier | 2 -> 0 | 1 -> 0 | 2 | 2.00 / 10.8 / 10.8 |
| pushpull_follower_buffer | 200 -> 83 | 200 -> 83 | 117 | 0.006 / 1.64 / 21.6 |
| sf_pushpull_output_opamp | 1 -> 0 | 1 -> 0 | 1 | 3.20 |
| two_stage_ota | 172 -> 39 | 160 -> 39 | 133 | 0.011 / 3.37 / 22.0 |
| two_stage_ota_sf | 153 -> 45 | 143 -> 45 | 108 | 0.034 / 3.48 / 26.6 |

- 봉인 수가 줄어든 점은 모두 봉인 9 단독 실패(다른 항목 통과)다 -- 봉인 1~8 은 r7 과 같은 판정.
- 문턱(LUT v2, L 1 µm, VSB 0): margin = 1 이 되는 VGS ≈ nmos 0.135~0.14 V(gm/ID 27.4, tol_V 8.5~9.2e-4 V), pmos 0.12 V(gm/ID 30.1,
  tol_V 9.0e-4 V) -- VDS 0.3·0.9 V 에서 같다. 즉 ε ≈ 2.3~2.7 % 이고, 그보다 VGS 가 낮은 점은 누설이 소자 자기 전류 분해능보다 크다.
- toy LUT(test conftest)의 `ctx_q` y = 0.99·z* = 0.3 점은 M1 봉인 9 margin 2.61 로 violated(r7 은 undefined -- 봉인 7 미정).
- 시간: (a) 합 s 9회로 모두 ±20% 안(봉인 블록 하나·소자당 LUT 점 조회 1회 추가).

### 10.7 [r9] 1변수 풀이 성능 실측 (2026-10-08, 작성자 측 시연 -- 정본 아님)
방법: master(6a3351a) 와 이 변경을 같은 LUT v2·같은 탐침(10.2: 회로당 215 θ, seed 20261008)으로 2개 프로세스를 동시에(다른 부하 없이) 돌려 `process_time`(CPU) 비교, tol_V 표
데우기(프로세스당 1회 비용) 12 θ 는 시간 밖. 호출 수 = 회로당 `solve_self` 호출, `_vgs_signed`(= h 평가) 호출.

| 회로 | solve_self 호출 | h 평가: master -> 변경 | CPU s: master -> 변경 |
|---|---|---|---|
| common_gate_amplifier (1변수 노드 없음, 대조군) | 0 | 0 -> 0 | 8.47 -> 8.77 |
| current_reuse_telescopic_ota | 3059 | 40363 -> 16966 | 43.47 -> 28.48 (−34%) |
| folded_cascode | 3065 | 36627 -> 14107 | 49.97 -> 31.80 (−36%) |
| ngcc_3stage_ff | 860 | 11050 -> 4958 | 18.14 -> 13.31 (−27%) |
| nmcnr_amplifier | 1223 | 11855 -> 4063 | 17.03 -> 12.70 (−25%) |
| pushpull_follower_buffer | 420 | 6095 -> 2537 | 6.39 -> 4.08 (−36%) |
| sf_pushpull_output_opamp | 4281 | 43390 -> 18594 | 69.61 -> 54.95 (−21%) |
| two_stage_ota | 332 | 3496 -> 1691 | 10.53 -> 7.53 (−28%) |
| two_stage_ota_sf | 563 | 6243 -> 2813 | 9.67 -> 8.67 (−10%) |

- 같음(9회로 1935 θ): 통과(일관) θ 수 동일(155/0/31/74/20/1/0/72/38), 통과한 θ 의 봉인 항목별 pass/fail 동일, 노드전압 최대 차 1.05e-4 V
  (writer tol_V ≈ 0.85~0.9 mV 의 약 1/8 -- 선언 tol 이내). 실패한 θ 5개(folded 2, sf_pushpull 3)는 양쪽 모두 실패인데 실패 분류만 다르다
  (`strict_recheck_residual`/`newton_line_search` <-> 봉인 위반): 반복 중 투영의 sub-tol 차이가 경계 θ 의 Gauss-Seidel·Newton 궤적을 바꾼 것.
- two_stage_ota `find_front`(LUT v2, E_B = 150, 평가 100회): 전선 `[EP:s1]` 동일, 평가별 상태·origin 순서 동일. θ 궤적은 12번째 평가부터 sub-tol 차이로
  갈라진다(FD·SLSQP 가 노드전압의 tol 이하 차이를 증폭) -- 점 단위 동일성은 보증하지 않는다. h 평가 2166 -> 316, `solve_self` CPU 1.5 -> 0.7 s,
  find_front CPU 8.9 -> 8.1 s(같은 조건 두 번 반복에서 모두 −8~13%; 기계 부하에 따라 CPU 초가 ±30% 흔들려 동시 대조군으로 확인).
- **프로파일 해석 정정**: find_front cProfile 에서 `solve_self` 누적이 135 s 중 ~80 s 로 보인 것은 첫 `solve_self` 안의 `tolerance` 가 부른 **tol_V 표
  최초 구성**(`lut/tolerance.py` `compute`, kind 마다 ~14~19 s CPU, `_inverse_cell` -> `strong_inversion_root` -> `hermite_root`)이다. 표 구성을 빼면 bisection
  자체는 find_front CPU 의 ~15%(1.6 / 10 s)였고 이번 변경은 그 절반을 줄였다. 남은 지배 항목 = tol_V 표 구성(프로세스당 ~30~40 s, lut 몫).
- `solve_self` 입력 재사용(LUT memo `root` 영역): 탐침 215 θ 에서 적중 two_stage_ota 21/332, folded 806/3076 -- 효과가 근 찾기 교체보다 작다.

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
8. **core 계층 수학(bracket_root·fixed_point_iter·k_max)은 sizing 에** 둔다: 소비자가 sizing 하나뿐(배선 원칙). 층 0 국소
   고정점(DEC-71 (4)(d))이 생기면 core 로 옮긴다.
9. **L 은 소자마다 θ**(`l_class` proposed 라 평가 경로가 읽지 않음, N3.3).
10. 파일 이름: `seal/item*_*.py` 대신 `seal_<항목>.py`(하위 폴더 없이), `size_and_seal` 의 θ 검사는 `theta_check.py`.
11. [r2] **설계 3.1 의 '이름 정렬 첫 노드'·'같은 단계는 소자 이름 정렬'을 구조 색 키로 바꿨다**(이름은 같은 색 안에서만, 결정을
    가른 경우 `TieBreak` 기록). DEC-95 (3) 의 '③ 대칭 궤도 대표'는 같은 구조 색 = 같은 궤도 후보로 실현된다.

## 12. 열린 질문 (결정 필요 -- 추측으로 채우지 않았다)

처리 상태(r2, 오케스트레이터 결정 2026-10-07): O2·O4·O6 해결, O10 부분 해결, O1 대기(우회 없음), O7·O9 사용자 승인 대기,
O3·O8 기록 유지. [r4] O1 봉인 7 판정 해결, 창 VDsat 항은 결정 대기(아래).

- **[r4] O1 처리 상태**: (a)·(b) API 는 lut r6 의 `vdsat`·`tol_vdsat_table(...).at(L, vds)` 로 생겼고 봉인 7 판정식을 배선했다
  (6절 표). **잔여(결정 대기) -- W4 창·1변수 구간의 VDsat 항**: 인접 MOS 의 VDsat(L, vgs, vds, vsb)은 그 MOS 의 gate·bulk 와 x 자신을
  읽으므로, 창에 넣으려면 4.3 의 free_window 의존에 {인접 MOS gate, bulk, x} 를 더해야 한다(설계 3.4 'W4 노드는 그 기둥의 SCC 에
  함께 든다'). 작성자 측 측정(LUT v2, 이 커밋 계획 블록 + 의존만 바꾼 계산): 순환 SCC 크기가 common_gate [2] -> [5], folded
  [3, 2, …] -> [3, 3, …], ngcc [1×4] -> [2, 1×4], nmcnr [2, 1×3] -> [4, 1×3], two_stage_ota [1, 1] -> [4, 1], two_stage_ota_sf
  [1×3] -> [3, 1×3](current_reuse·pushpull·sf_pushpull 변화 없음) -- 6회로에서 1변수 bisection 이 다변수 Gauss-Seidel 로 바뀌고
  (O10·O11 위험), 4.3·`test_scc_order`·창 test 가 함께 바뀐다. 그래서 이 개정에서는 넣지 않았고 포화는 봉인 7 이 판정한다(창은 위치
  매개화일 뿐 봉인 판정과 무관). 1변수 구간의 writer 자신의 포화 하한(vds ≥ VDsat + tol)은 h 가 단조이면 '근이 그 쪽에 있는가'와
  같아 봉인 7 의 writer 행과 같은 판정(실패 분류만 no_root_in_window 로 앞당김)이라 따로 두지 않았다.
- **O1 VDSAT 접근자 (r3 까지의 기록)**: 봉인 7 은 lut 에 VDSAT 접근자가 생길 때까지 undefined, SealedSnapshot 0, W4 창에
  VDsat 항 없음. lut CONTRACT r5(브랜치 ng-hermite)에도 VDSAT 접근자가 없다. **이 계약이 요구하는 lut 공개 API**(로더가 LUT v2
  VDSAT 열을 읽은 뒤): (a) `vdsat(memo, kind, w_key, L, vgs, vds, vsb) -> float`(V, 크기, point 영역 memo, 축 규칙·실패는 op_point
  와 같음 -- 오라클 `@m[vdsat]` 과 같은 양, DEC-88), (b) `tol_v_table(...).at(L, vds, "vdsat")` 처럼 `TOL_V_METRICS` 에 VDSAT 열
  leave-one-out 지표 `"vdsat"` 를 더하거나 별도 `tol_vdsat_table` -- 셀 = (kind, w_key, L, VDS), 셀 값 = VDSAT 열 LOO 최댓값
  (DEC-87 방법). 생기면 봉인 7(현재 `dc_seal_region`)이 (a)·(b) 로 ID > 0 MOS 마다 `VDS − VDsat ≥ +tol_VDsat`(margin =
  (VDS − VDsat − tol_VDsat)/tol_VDsat)을 재고, `dc_columns` 의 W4 창과 1변수 구간에 VDsat 항을 더한다. 지금은 `DcEvaluation(sealed=None)`.
- **O2 (해결)** 레이아웃 전 폭 = LUT 생성 규칙 폭(`pre_layout_lut_access`, DEC-91 (2), 1.3절).
- **O3 DEC-95 (3) ②**(GB5 gm 요구·뒤 stage): 그 정보를 내는 S1v·GB5 가 없어 아직 적용하지 않는다(① diode, ③ 대칭 궤도 =
  구조 색은 적용). 남은 동률은 `TieBreak` 로 기록(9회로 중 current_reuse 만 5건). front 정규화 해시 metamorphic 은 탐색 뒤.
- **O4 (해결)** F 없는 성분 뿌리 = (구조 색, 이름) 최소, 같은 색 후보는 `w4_root` 기록.
- **O5 결정 대기 입력 DC(SP-2, 7회로)**: IT-1 규칙대로 W4(입력 포트인 뿌리의 y 키 = 그 뿌리 넷; 같은 DC 엣지·input_tie 없음). 노드 목표(CI-15)·의도 영역(CI-18)은 9회로 모두
  결정 대기 -> W3 0개, 선형 선언 0개.
- **O6 (해결)** θ 전류 정의역 = `ThetaSchema.current_cone`(KCL 기저에서 유도한 선형 부등식), 밖이면 `check_theta` 가 거부.
- **O7 (닫음, 2026-10-08 사용자 승인)** core `GraphSnapshot.extend_writers` 로 `lift_s1` 이 S1 레코드를 공유한다(1.5).
- **O8 형제 lineage 재계산 (기록)**: FD 형제 평가끼리 같은 입력은 재계산된다(graph 가 곧 캐시라 다른 lineage 값을 볼 길이 없음).
- **O9 (닫음, 2026-10-08 사용자 승인)** 투영 지문 = (key, `FieldValue.value_fp`) 합성(core CONTRACT 8절) -- 블록 호출·봉인 4 가
  값을 다시 직렬화하지 않는다. 실측은 core CONTRACT 10절. `TolVTable.at` 중복 조회는 [r9, 2026-10-08 사용자 승인 성능 항목 6] `_Circuit.tolerance` 가 한 평가 안에서 (소자, VDS) 마다 한 번만 부른다
  (5.6c). 효과는 작다: `at` 1회 ≈ 80 µs, two_stage_ota find_front 의 `dc_columns` 조회 158회 중 고유 41개.
- **O10 (닫음, r6)** 1변수 노드 = 구간 bisection, 다변수 SCC = Gauss-Seidel(수축할 때) -> 못 하거나 strict 검증 실패 시 감쇠 Newton
  (5.4 [r6]). sf_pushpull 의 9노드 SCC 실측: Newton 이 정의역 안 시작점에서 돌고, 실패한 θ 는 ‖r‖∞ 가 0.22~0.30 V 에서 멈추는
  정체(잔차가 0 이 아닌 극소 -- 그 θ 에 정의역 안 해가 없다고 관찰). 그 θ 는 GS strict 검증 위반(주로 lut_curve_undefined)
  이나 `newton_line_search` 로 거부된다(10.4).
- **O12 [r3] `strict_recheck_residual` 재현 구성 없음**: 방어 검사(5.4 '실패를 일으키는 최소 구성'). 공개 API 만으로 덮을
  구성이 생기면 계약에 더한다.
- **O11 (닫음, r6)** W4–W4 결합으로 Gauss-Seidel 이 느리게 수축해 K_max 안에 못 닿으면 Newton 으로 바꾼다 -- 선형 SCC 라 한
  걸음에 수렴(common_gate NONCONVERGENT 17 -> 0, 10.4).
- **O13 [r5] 수동소자 θ 탐색 상자 (search 몫, 배선 대기)**: 커패시터 상자는 PDK 선언에서 유도할 수 없다 -- 로컬 PDK 원본을 확인한
  결과 periphery 규칙표(`skywater-pdk/docs/rules/periphery/periphery.csv`)의 `capm.*` 행(최소 폭·최대 면적 등)은 값이 모두 `N/A`
  이고, `sky130_fd_pr/models/capacitors/sky130_fd_pr__model__cap_mim.model.spice` 가 include 하는 `cells/cap_mim_m3/` 는 로컬에
  없다(용량 밀도·한계 수치 원본 없음). 그래서 core `pdk_decl` 에 선언 항목을 더하지 않았다(원본 없는 수치 = 지어낸 상수). θ 저항
  상자와 같은 규칙으로 **search 선언 입력**이어야 한다: search `SearchSettings` 에 커패시터 상자(F)를 두고, θ `capacitance` 가 있는데
  선언이 없으면 `search_domain` 이 변수를 만들기 전에 `SchemaRejectedError`(gate `search_domain`, reason
  `theta_capacitance_bounds_undeclared`, capacitors = θ 순). θ `ss_resistance` 는 θ `resistance` 와 같은 `resistance_bounds_ohm`
  (없으면 기존 `theta_resistance_bounds_undeclared`, resistors 에 포함). sizing 은 정의역(> 0)만 강제한다(5.1). search 는 master 에
  없어(브랜치 ng-mod6) 이 커밋에서 배선하지 못했다 -- ng-mod6 병합 때 `search_domain`·`fd_jacobian`(θ 종류 분기)·`kernel`(아래 O16)
  이 함께 바뀌어야 한다.
- **O14 [r5] 이 개정과 어긋나게 된 기존 test (test 작성자 갱신 몫 -- 작성자는 test 를 고치지 않았다)**, 32건:
  `tests/sizing/test_dc_inputs.py::test_library_projection[current_reuse·ngcc·nmcnr·sf_pushpull·two_stage·two_stage_sf]`(기대 DcInputs 에
  `engine_elements` 없음), `tests/sizing/test_s2_values.py::test_vocabulary_constants`(THETA_KINDS 집합)·`::test_value_fields_as_contract`
  (ThetaSchema 필드), `tests/sizing/test_theta_schema.py::test_library_schema[같은 6회로]`(capacitance 성분)·`::test_block_reuse`
  (`dc_theta_schema(base, ())` -- extras 가 이제 2개), `tests/sizing/test_writer_plan.py::test_library_renaming_metamorphic[같은 6회로 ×
  seed 1·2]`(σ 로 옮긴 DcInputs 를 6칸으로 만들어 engine_elements 가 빠짐 -- 7번째 칸도 σ 로 옮기면 9회로 모두 성립, 10.3절),
  `tests/metrics/test_ss_evaluate.py::test_s10_passive_theta_conflicts_rejected[4]`·`::test_passive_theta_supplies_engine_value`
  (`passive_theta` 인자 삭제 -- metrics CONTRACT 7.6 r5; engine CL 은 이제 θ `capacitance`).
- **O15 [r5] 영점 상쇄 규칙 문구 해석 (J7 ratify 대상)**: 4.4 의 순서 무관 해석. 회로별 S(작성자 측 판정): two_stage_ota Rz -> {M6},
  nmcnr Rm -> {M301}, current_reuse(파일럿) Rz1 -> {M16}·Rz2 -> {M26}. 글자대로 해석하면 two_stage_ota·파일럿에서 R 이 입력 쪽에 있어
  S = ∅(θ 폴백)이 된다 -- 어느 쪽인지는 사용자 ratify.
- **O16 [r5] search(ng-mod6) 병합 시 바뀌어야 할 호출부**: `ss_evaluate` 의 6번째 위치 인자 `passive_theta` 삭제(metrics 7.6) --
  ng-mod6 `search/kernel.py` 의 `ss_evaluate(..., sctx.ss_constraints, (), (), **extra)` 는 `()` 하나를 지워야 한다. 봉인 아닌 점의
  `metrics_dc` 수동 값(당시 `spec_passive_values + θ resistance`)에 θ `capacitance`·`ss_resistance` 를 더해야 면적이 같은 값을 쓴다
  (봉인 점과 같은 입력 -> 재사용). **[U17 ① 폐기됨]** `spec_passive_values` 칸과 그 합산은 지웠다 -- 봉인·봉인 아닌 점 모두 GB5 블록
  `passive_values` 가 쓴 `device.passive_value` 필드를 읽는다(설계 40 §2.4.8). `search_domain` 은 지금 모르는 θ 종류를 조용히 건너뛴다(코드 읽기로 확인, 변수 없음) --
  그 θ 가 빠진 후보는 `check_theta` 키 불일치가 될 것으로 본다(ng-mod6 에서 실행해 보지는 않았다). O13 상자 배선이 필요하다.
- **O17 [r8] search 쪽 일관 조임 (search 몫 기록 -- search 는 고치지 않았다. [r10] 그 필드는 폐기됐고 이 기록은 history)**: 봉인 9 가 냈던 소자별 ID 하한(I_off/ε)은 **그 점의 W 에 비례**한다(I_off = IDu(VGS=0)·W/L, ID = IDu(VGS)·W/L). 그래서
  ID ≥ floor ⇔ IDu(VGS)·(gm/ID)·tol_V ≥ IDu(VGS = 0) 로 **전류 크기가 지워진다** -- 실제 제약은 θ `ln_idu` 좌표(= VGS, 같은 L·VDS·
  VSB)의 하한이다. (1) `search/current_box.py` 의 I_off(격자 전체 VGS = 0 ID 최솟값, nmos 2.7e-19·pmos 2.4e-26 A)를 올려도 이
  조건은 지켜지지 않는다(W 가 따라 작아지면 같은 VGS). (2) 일관된 조임 = 소자마다 ln_idu ≥ ln IDu(VGS*) 인 VGS*(L, VDS, VSB) --
  margin(VGS*) = 1 의 근(10.6: L 1 µm 에서 nmos ≈ 0.14 V, pmos ≈ 0.12 V). VDS·VSB 가 θ 로 정해지기 전이라 search 는 (L 격자, VDS 축)
  위에서 VGS* 최댓값(보수) 또는 봉인 뒤 하한/ID(= margin) 를 쓰는 사후 제약을 고를 수 있다 -- 선택은 search 결정.
  pA 전류 자체(전력 0.6 pW)는 W 최소값(MOD6 W_min)이 막을 몫이다.
- **O18 [r8] 이 개정과 어긋나게 된 기존 test (test 작성자 갱신 몫 -- 작성자는 test 를 고치지 않았다)**, 16건(전체 suite 16 failed,
  5655 passed): 봉인 항목 수 8 고정 -- `test_seal.py::test_undefined_evaluation`·`test_violation_reports_worst_item`·
  `test_sealed_snapshot_when_all_pass[0.5-0.6-0.7]`·`[0.4-0.8-0.55]`, `test_seal_report.py::test_status_rule[sts0..sts5]`(6)·
  `test_report_of_real_evaluation`, `test_size_and_seal.py::test_failure_seal_violation`·`test_diode_mirror_full_evaluation`;
  권한표 정확 일치 -- `test_s2_values.py::test_s2_writers_is_s1_plus_dc_table_exactly`·`test_dc_writes_constant_matches_table`;
  동작 변화 -- `test_scc_newton.py::test_gauss_seidel_not_contracting_newton_converges[0.99-0.3]`(그 toy 점이 봉인 9 violated, M1
  margin 2.61 -- 기대 `REPORT_UNDEFINED`).
- **O19 [r9] 영역 어휘 결정 근거와 바뀌는 test (test 작성자 갱신 몫)**: 정본 = `"triode"`. 근거 순서 -- 계획 DEC-88 봉인 7 행은
  `intended_region: "linear"` 를 **기본안**으로 두고 '이름은 6b design 확정'이라 미뤘고, 그 design(`_drafts/engine/design_spec_format.md`
  표 1.6)이 `{"region": "triode"}` 로 정했으며 spec 로더(authoring 23b45c4)가 그것을 구현했다. sizing(b1b3a37, 설계
  design_gb7_dc_canonical 봉인 7 행)은 계획 기본안 낱말을 그대로 옮겨 어긋났다. spec 이 사용자 어휘라 sizing 이 spec 상수를 읽게
  했다(같은 개념 두 정의 금지 -- 값을 복사하지 않고 `from gmid_engine.authoring import REGION_TRIODE`). 오라클 `predictions.devices[].region`
  어휘(sat|triode|off)와도 같아진다. 바뀌는 test: `tests/sizing/test_dc_inputs.py` 의 영역 투영 test
  (손으로 만든 `RegionDecl("M7", "linear")` 를 linear 로 기대 -- 이제 "triode" 여야 한다, 실패). 같은 파일 42행 9회로 spec 경로
  비교도 `"linear"` 로 걸러 기대값을 만들지만 9회로 spec 의 intended_region 이 모두 pending(결정 대기 CI-18)이라 양쪽 다 빈 tuple
  로 지금은 통과한다(triode 선언이 생기면 틀린다 -- 같이 고칠 것).


---

## 13. [U1 배선] L 동치류 공유 -- `build_kernel_context(..., l_classes=())`, `KernelContext.l_ties`

설계 40 §3.2 보완 1, 계획 DEC-17·LR1. 소비하는 쪽 계약:

* `build_kernel_context(s1graph, inputs, lut, l_classes=())`: `l_classes` = `graph.build_s1v` 결과 `S1v.l_classes`(LClass tuple). 생략하면 `()` 이고 이전 동작과 같다
  (`ctx.l_ties == ()`). [14.1 이 대체] θ 스키마는 동치류가 있으면 멤버 L 성분을 뺀다(없으면 불변).
* **status 의미 유지**: S1 `rel_l_class` 는 proposed 그대로라 읽지 않는다. `LClass.status == derived` 인 동치류만 묶는다(`review_needed` 동치류 = 멤버 DC 역할 미확정 --
  묶지 않는다). 주인 선택(DEC-17)은 S1v 가 이미 했다.
* `KernelContext.l_ties` = ((멤버, 주인), ...) 이름순, 주인이 아닌 derived 동치류 멤버만. 멤버 이름이 S1 원소가 아니면 `ValueError`.
* `size_and_seal`: 멤버 소자의 L = 주인 소자의 θ L 값(`dc_lengths` 입력이 바뀐다). θ 의 멤버 L 값은 무시된다(주인 값과 달라도 오류가 아니다 -- 멤버 L 성분은 중복 변수).
  search 는 멤버 L 성분을 변수에서 빼야 한다(U4/U11 후속: `search_domain`·`slsqp_outer`·`layer0_center` 가 아직 소자마다 L 을 변수로 둔다).

## 14. [U4 보강] 설계 40 §3.7·§3.2-1, 41 §4.6·§5.3 (독립 test 작성자용 계약, 2026-10-08)

대상 확인 행: DEC-17 (θ 쪽)·32·70 (일부)·95 (3), D-GB7a·c·d, D-LS, D-J5 (U4 몫). **미러 비 강제(D-GB7b, DEC-70)는 구현하지 않았다** -- 15절.

### 14.1 L 동치류 L 공유 (D-GB7a)
* `build_kernel_context(s1graph, inputs, lut, l_classes=(), order_hints=NO_ORDER_HINTS)`. `l_classes` = U1 `S1v.l_classes` (LClass: `owner`, `members`,
  `status`; 이 모듈은 속성만 읽는다). `status == derived` 인 동치류만 묶고 `review_needed`·proposed 는 묶지 않는다(소자마다 L). 멤버·주인 이름이
  S1 원소가 아니거나 MOS 가 아니거나, 주인이 다른 동치류의 멤버이거나, 한 소자가 두 동치류의 멤버면 `ValueError`.
* `KernelContext.l_ties` = ((멤버, 주인), ...) 정렬(비주인 멤버만; 동치류가 없으면 `()`).
* **θ 스키마**: `THETA_L` 성분은 동치류당 **주인 하나**, 동치류에 들지 않은 MOS 는 소자마다 하나. 멤버의 `("L", 멤버)` 성분은 **없다**(`check_theta` 가
  넣으면 `ValueError` 남음). `dc_theta_schema(snapshot, declared_resistors, engine_passives, l_ties=())` -- l_ties 가 비면 extras 를 3번째까지 주지 않는다
  (블록 입력 버전 불변; 기존 2-extras 호출과 재사용 계약 유지).
* `size_and_seal`: 멤버 L = 주인 θ L (`dc_lengths` 입력). 주인 이름은 DEC-17 순서로 U1 이 정해 `LClass.owner` 로 준다(이 모듈은 고르지 않는다).
* 소비자 주의: search 가 L 변수를 소자마다 두는 곳(`layer0_center`·`slsqp_outer`·`l_bin_search`·`start_points`)은 `schema.components` 의 L 성분(주인만)을 따라야 한다.
  `search_domain` 은 이미 성분 목록에서 L 변수를 만든다.

### 14.2 tol_I = tol_V × 자기 동작점 gm (계획 N3.6 v6.4, 설계 40 §3.7-3 v1.6, U17 ①)
* `dc_tolerances(snapshot, lut)`: `device.dc_gm` = `dc_op.gm_id × dc_op.current`(writer 이 블록 하나). 봉인 3 tol_I = tol_V × 노드에 닿는 소자 `dc_gm` 최댓값.
  `ss_dev` gm·`metrics_dc` b_P·`passive_values` 영점 상쇄 R 이 같은 필드를 읽는다.
* parent 에 의존하지 않는다: 같은 θ 는 parent 와 무관하게 같은 봉인 결과. 옛 S2p 경로(`previous_gm_id`·`inherited_gm_id`·`canonical_gm_id`·`gm_grid_max`·
  `dc_gm_bound`)는 지웠다. 수동소자 θ 만 바뀐 자식의 DC 재사용은 입력 버전 일치로 성립한다(`dc_gm` 이 수동소자 θ 를 읽지 않는다).

### 14.3 W_request 고정 W (D-GB7d, LY3)
* `size_and_seal(ctx, theta, parent=None, w_request=())`, `w_request` = {MOS: W[m]} 또는 ((MOS, W), ...). MOS 가 아닌 이름·비양수·비유한 W·**같은 소자 이름이 두 번 있는 요청**((MOS, W) 쌍 목록에서) -> `ValueError`(호출 계약 위반; 값이 같아도 거부).
* 쓰기 소자(`dc_coord.role == writer`): θ `ln_idu` 는 무시되고 ln IDu = ln(ID·L/W) 가 `dc_columns` 에 간다. 종속 소자: 좌표는 순방향 그대로. 모든 요청 소자의
  `DeviceOp.W` = 요청값 (`dc_widths(snapshot, lut, w_request=())`). 종속 소자의 ID 어긋남은 봉인 3 이 판정한다(순방향 IDu × W/L 로 다시 센 KCL).
* 요청이 없으면 블록 extras 가 종래와 같다(재사용 계약 유지).

### 14.4 DEC-95 (3) 전체 순서 (D-GB7c)
* `OrderHints(independent, gm_required, stage)`(모두 MOS 이름 tuple 또는 ((MOS, 번호), ...)), `NO_ORDER_HINTS`. `dc_writer_plan(snapshot, target_nets, input_dc_declared,
  order_hints=NO_ORDER_HINTS)`: 엣지 키 = (종류: 저항 < MOS, [MOS] ratified 독립 < 그 밖, diode < 그 밖, gm 요구 < 그 밖, 뒤 stage(번호 큰 쪽) < 앞, 구조 색, 이름).
  Kruskal 에서 키가 작은 엣지가 트리(독립), 큰 쪽이 종속. 힌트가 비면 종래 순서(diode < 그 밖, 색, 이름)와 같고 TieBreak 기록도 같다.
* **스텁**: 힌트의 출처(U1 S1v stage 번호, GB5 gm 요구, `structure.json` ratified 로더)는 U1 이 채운다. 지금은 `build_kernel_context(..., order_hints=)` 로 넣는
  호출부가 없다(기본값만 쓴다).

### 14.5 국소 봉인 (D-LS, 41 §5.3)
* `size_and_seal_local(ctx, theta_block, fixed, columns) -> LocalSeal`; `theta_name(kind, key)` = `"kind:key"`. `LocalSeal{ok, failures, snapshot_fragment, gain_db, power_w, area_m2}`,
  `SnapshotFragment{devices, nodes}`. 상세는 `size_and_seal_local.py` 머리 설명.
* `theta_block ∪ fixed` = `ctx.schema.components` 정확히 (겹침·빠짐·모르는 키 `ValueError`), `columns` = {str(Column.id)} 비어 있지 않음.
* 판정 대상 = 봉인 1·2·3(KCL)·6·7·8(KVL) 중 위반 소자·넷이 덮는 집합과 겹치는 것. 4·5·9 는 국소 판정이 아니다. ②~⑤ 중 후보 실패 예외는 `ok = False` 와 그 FailureRecord 1건.
* **스텁**: `gain_db` 는 항상 None (`metrics.block_local_gain`, U7). 전회로를 푸는 커널이라 계산이 블록 크기에 비례하지 않는다 -- 결과 캐시는 U15(N_T,i 상한) 몫.

### 14.6 y_icm = 입력 포화 창 (J-E SP-2 (c), D-J5 U4 몫)
* 입력 DC 미선언이라 입력 포트인 W4 뿌리(최대 하나, y 키 = 그 넷)가 있으면 `dc_columns` 가 풀이를 되풀이한다: (1) y = 1/2 로 푼 해에서 (2) `input_window.saturation_window` 로
  입력 공통모드 x 의 포화 창(x 를 따라 움직이는 노드의 VDS 변화율 = 노드 writer 식 야코비안 연립의 해, 소자별 포화 여유 VDS − VDsat 의 1차 외삽 -- [IT-2c] 판정 여유 0, tol 항 없음)을 재고
  (3) 순서 창과 교집합을 y_icm 범위로 삼아 요청 y 로 다시 풀며 (4) 경계가 tol_V 안에서 변하지 않을 때까지 되풀이(상한 `k_max(레일 폭, tol_V)`). `node.dc_window` 는 마지막 범위를 낸다.
* (1)이 풀리지 않거나 VDSAT 열 없음·tol 미정이면 종래 사상(순서 창 = 레일 범위). `dc_columns(...)` 5번째 extras 는 `triode` 선언 소자 이름 tuple(필드 `device.region_decl` 에서)이고 비어 있지 않을 때만 준다.
* 효과(toy 차동쌍): 종래 y ∈ [0.05, 0.95] 무작위 60점 중 봉인 19, 이후 60. 평가 시간 약 3배(IT-2b 전 측정, `_refine_ends` 경로).
* (1)이 y = 1/2 에서 풀리지 않으면 순서 창 안을 1/4, 3/4, 1/8, 3/8, ... 순으로 훑어(시도 수 ≤ k_max(레일 폭, 레일 폭 절반 VDS 셀의 최소 tol_V)) 풀리고 창을 잴 수 있는 첫 점의 해로 (2)를 시작한다. 어디서도 안 풀릴 때만 종래 사상이다.
* (5) [IT-2b 개정, 설계 41 4.7-3 1] 커널은 창 끝을 다듬지 않는다(`_refine_ends` 를 부르지 않음 -- 끝 x 고정 풀이는 다듬은 창 블록 몫). 커널 `node.dc_window` 뿌리 항목 = 순서 창 ∩ 마지막 `override`(선형 감도 끝),
  `input_status` = 수렴 `measured` / 미수렴·tol 미정 `unsettled`(y 범위로는 그대로 쓴다) / 창을 못 잼 `unmeasured`(순서 창). 따라서 y = 0·1 끝 점의 봉인 7 여유는 1차 외삽 오차만큼 음수일 수 있다.
* (6) [IT-2c, 설계 41 4.7-W W1·4.7-3 2·3] `node.dc_window` 의 항목은 **W4 뿌리뿐**이다(입력 점 뿌리 포함). 뿌리 아닌 입력 포트·입력 DC 선언 포트·F 성분 미선언 포트의 창은 이 필드가 아니라 측정 구성
  블록 `icm_config`(metrics)의 `node.dc_window_cfg` 가 받는다(모든 입력 포트를 함께 구동한 봉인점 KCL 선형 감도 끝). 창 경계 행은 공용 `Circuit.region_rows`(`sat`·`triode`, 여유 0)이고 끝 식은
  `saturation_window(unknown, root, ...)` 하나다(`root` = 넷 하나, 쌍·묶음 없음). 동작점 불일치(`op_mismatch`)는 이 card 밖(EO-1 묶음, 사용자 결정 O-98).
  커널 입력 창 측정(`_measure`·`_interior_solution`·`_dyadic_ys`·`INPUT_STATUS_UNSETTLED`)은 card WB-1 범위 3a 가 재작성한다.

## 15. 구현하지 않은 것 (정지 후 보고)

* **D-GB7b 미러 비 강제(DEC-70)**: 설계 문구는 `matching_ratio` 를 전류 기저의 강제 관계로 넣고 비율 출처를 θ 변수로 둔다. 구현하려면 새 θ 종류(`mirror_ratio`, I_out = ρ·I_ref)가 필요하고
  (1) θ 전류 정의역 원뿔이 θ 에 비선형(곱)이 되며 (2) `search_domain`(상자: 멤버·기준 전류 상자에서 도출 가능)·`fd_jacobian`·`orbit_ties`·`current_symmetry`·
  `layer0_center`·`start_points`·`cone_rows` 가 모두 새 종류를 알아야 한다 -- 소유가 다른 단위(U11 search 정비·U15)의 파일이라 이 단위에서 쓰면 쓰이지 않는 코드가 되거나 search 를 깨뜨린다.
  대칭 묶음의 비율 1 은 이미 search `orbit_ties` 가 같은 궤도 전류 성분을 한 변수로 묶어 준다(U2).
