# 옛 엔진 레이아웃 파이프라인 분석과 새 엔진 사용 제안

- 대상 소스: `gmid-light` @ cb0ef86 (`skills/analog-gmid-design/assets/stick_diagram.py`=SD, `sizing_recipe.py`=SR). 행 번호는 이 커밋 기준.
- 실측: `/c/g460/repo` 복제본(끝난 뒤 삭제 확인)에서 `current_reuse_telescopic_ota`를 정본 spec(`run_harness.canonical_spec` + floorplan_target, SLSQP n_starts=3)으로 1회 실행(112.9 s). 소스는 고치지 않았고, 래퍼(monkeypatch)로 중간 입출력만 기록했다. 기록 스크립트: 세션 scratchpad `trace_layout.py`, 기록 `out/trace.jsonl`.
- 이전 결과 `spice_harness/results/current_reuse_telescopic_ota.instance.json`(C:/g452/repo)과 레이아웃 W가 같다(M3a 3.49 -> 36.02 um 재현).

## 1. 최상단 진입 함수와 호출 트리

최상단은 `run_topology_pipeline`이 아니라 **`SR optimize_full_circuit_budget` (SR:9087)** 이다. sizing(theta 탐색) 뒤 레이아웃 전체를 여기서 오케스트레이션한다. `run_topology_pipeline`(SD:8768)은 그 안에서 불리는 한 단계(검사 묶음)일 뿐이고, 행 분할·패턴 적용을 스스로 하지 않는다(docstring이 명시).

```
optimize_full_circuit_budget                                   SR:9087
├─ _build_theta_evaluator ... resolve_stack_layout             SR:8072 -> SR:6481
│    ├─ (declared vertical_stack_id) audit_vertical_stack_id_vs_kcl   SD:3142
│    └─ derive_horizontal_stack_groups                         SD:5021
│         └─ merge_layout_groups_by_matching_pairs             SD:4911  (_verified_euler_fix SD:4769)
├─ [theta 탐색 = sizing, W 결정]
├─ assign_finger_geometry(sizing, stack_groups_geometry)       SR:9283 -> SD:6021
│    ├─ search_stack_finger_w                                  SD:5932
│    └─ search_unit_cell_sizing (폴백)                         SD:5883  ← W 대폭 변경 지점
├─ run_topology_pipeline_with_finger_fixup                     SR:9306 -> SR:11903
│    ├─ run_topology_pipeline (매 라운드)                      SD:8768
│    │    ├─ load_topology                                     SD:8569
│    │    ├─ check_finger_width_compatibility                  SD:5161
│    │    ├─ split_into_stacks                                 SD:2952
│    │    ├─ audit_row_split                                   SD:7009
│    │    │    ├─ build_stick_diagram (행마다)                 SD:6655
│    │    │    │    ├─ mirror_symmetric_trail                  SD:6562
│    │    │    │    └─ build_graph/check_euler_condition/hierholzer  SD:5206/5293/5328
│    │    │    ├─ check_box_shape                              SD:6337
│    │    │    └─ select_layout_tool (3b/3c 필수 게이트 결정)  SD:6978
│    │    ├─ rebuild_floorplan -> pack_floorplan_grouped       SD:8153 -> SD:8344
│    │    └─ check_stick_diagram_coverage                      SD:6924
│    ├─ apply_and_revalidate_pair_adjustment (euler 1순위)     SR:11412
│    │    ├─ suggest_pair_finger_adjustments                   SD:5785
│    │    └─ revalidate_finger_override                        SR:11312
│    ├─ _sync_finger_fixup                                     SR:11500
│    └─ find_min_crossover_layout_with_branch_composite (2순위) SD:7484
└─ _evaluate_row_split (floorplan_target 있으면 반복)          SR:9333
     ├─ apply_explicit_row_split                               SD:6119
     ├─ audit_row_split                                        SD:7009
     ├─ run_matching_safety_with_finger_growth (audit 실패시)  SR:11726
     │    ├─ repair_matching_safety (라운드마다)               SD:7516
     │    │    ├─ _branch_composite_pair                       SD:7315
     │    │    ├─ select_layout_tool                           SD:6978
     │    │    ├─ interdigitate_layout(base=None)              SD:164
     │    │    ├─ common_centroid_layout                       SD:379
     │    │    └─ _layout_result_to_rows                       SD:7249
     │    ├─ apply_and_revalidate_matching_finger_growth       SR:11551 (revalidate_finger_override)
     │    └─ _finalize -> _fixup_euler_blocked_rows            SR:11595
     ├─ check_stick_diagram_coverage (repair 전후 이름 집합)   SR:9437 부근
     └─ rebuild_floorplan                                      SR:9464
→ save_instance_json (호출자: run_harness / engine_dump)       SD:9010
```

## 2. 단계별 입력·출력·결정 규칙

| 단계 | 입력 | 출력 | 결정 규칙 |
|---|---|---|---|
| matching 그룹 출처 | topology.json `symmetry.matching_pairs`(선언, `matching_sensitivity`·`current_forced`) + `load_topology`가 `propose_device_roles_gap_fill`로 자동 병합한 offset 쌍(SD:8569 이하) | `meta.symmetry.matching_pairs` | **태그(선언) 기반**이다. connectivity에서 쓰는 것은 축B `shares_diffusion_node()` 하나뿐(소스·드레인 공유 여부). 축C(`offset`/`ratio`)는 선언값을 그대로 믿는다(SD:7009 docstring "선언을 그대로 신뢰"). |
| 물리 행(그룹) 경계 | `device_roles.vertical_stack_id`(선언) + `current_forced=True` 쌍 | `{stack_id:[소자]}` | `resolve_stack_layout` 우선순위: override > declared vsid > analog-grammar 후보 > `geometry_colocation_union`. 그 뒤 kind로 쪼개고 `current_forced` 쌍으로 그룹 병합, 병합 결과가 Euler 불가능(한 번의 finger 조정으로도)이면 병합 안 함. **감사(audit)는 current_forced=False 쌍까지 모두 쓰는데 그룹 병합은 forced만 쓴다** -- 실측에서 7소자 미러 그룹(M18_bg/M8/M13/M17/M22/M60/M61)의 3b가 서로 다른 행이라 구조적으로 FAIL. |
| finger 배정 | sizing W, 행 그룹 | 소자별 `n_fingers, finger_w, w, stack_id` | 행 총 W 내림차순. 첫 행(seed)은 finger_w<=max_finger_w(40 um) 중 행 finger 수 최소 후보. 이후 행은 직전 행 finger 수 ±3 목표 → 실패면 목표 없이 → 실패면 `search_unit_cell_sizing`(앞 행들의 finger_w 중 **첫 소자** W에 가장 가까운 단위폭)으로 `n=max(1, round(W/unit))`. `search_stack_finger_w`는 grid_step 없이 호출돼 **행 안 모든 W가 finger_w의 정확한(1e-6) 정수배**여야 후보가 나온다. |
| Euler 판정 | 행 하나의 Transistor(n_fingers 포함) | `StickResult(status, node_sequence, transistor_sequence, odd_nodes)` | `build_graph`: kind 혼합이면 ValueError, finger를 라운드로빈으로 엣지 추가. `check_euler_condition`: 홀수차수 0=circuit, 2=path, 그 외 또는 비연결=impossible. matching_pairs가 있으면 먼저 `mirror_symmetric_trail`(대표 조합 2^n 탐색 후 거울반사, `check_walk_sequence`로 검증), 실패하면 hierholzer. |
| Euler 수리 | blocked 행 | finger 증가 또는 행 분할 | 1순위 `apply_and_revalidate_pair_adjustment`(홀수차수 개선 순 후보 → `revalidate_finger_override`로 제약 재판정, 첫 통과 후보 채택 → W 변경, ctx 동기화). 실패면 2순위 crossover 그룹분할(W 불변, `_seg{i}` 행). |
| box-shape | 행 목록 | `BoxShapeVerdict` | 행 물리 폭 비율 <= 1.5. 실측 FAIL(10.13). 이 결과로 W를 바꾸지는 않는다(row_split 재시도만). |
| matching 패턴 선택 | (a,b), 축C, 축B | 도구 이름 | `select_layout_tool`: offset → common_centroid; ratio+공유노드 → interdigitate; ratio+비공유 → common_centroid. audit 필수 게이트: 3c=common_centroid 선택 시, 3b=ratio+공유노드. |
| 패턴 적용 | audit FAIL한 필수 쌍 | 새 `_repair{i}` 행 | **반응형**이다 -- Euler trail은 먼저 hierholzer/거울대칭으로 만들고, 3b/3c가 FAIL한 쌍만 `repair_matching_safety`가 꺼내 재배치한다. 같은 source(hub)를 공유하거나 직렬 branch 대응(`_branch_composite_pair`)이 있을 때만 적용 가능, 아니면 건너뜀. `interdigitate_layout`은 늘 `base=None`으로 불려 `INTERDIGITATION_PATTERNS` 표는 운영 경로에서 쓰이지 않는다. `COMMON_CENTROID_PATTERNS`는 `common_centroid_layout`의 경로 2(N=2, 2행, 개수 다름)에서만 쓰인다. |
| matching 수리(성장) | 3c 필수 실패 쌍 | n_fingers 증가 또는 완화 | `failing_3c[0]`부터 `min_fingers=2`까지 성장 → 재검증 통과면 W 변경, gm/ID 위반(역산 실패 포함)이면 `relaxed_pairs`(interdigitate 강제, audit은 FAIL 그대로), 다른 사유면 **즉시 종료**. |
| floorplan | 최종 행 | `FloorplanResult` | spine_groups 없으면 kind별 2개 super-block, gap=중앙 폭 5%. floorplan_target이 있으면 row_split을 한 stack씩 +1 하며 점수 개선 탐색. |
| coverage | 이름 집합 | ok/missing | repair 전후 소자 이름 집합 동일성. |

### 사용자 기억("최상단 함수가 오일러 패스와 pattern을 찾아 썼다")과의 대조

근거로 확인된 것: 최상단(`optimize_full_circuit_budget`)은 행마다 Euler trail을 실제로 계산하고(`build_stick_diagram`), 매칭 실패 쌍에 `interdigitate_layout`/`common_centroid_layout`을 실제로 호출한다(실측 65회 호출). 다만 (1) 패턴은 처음 배치를 정할 때가 아니라 **audit FAIL 뒤 수리 단계에서만** 쓰이고, (2) 문헌 패턴표는 사실상 안 쓰인다 -- 실측 65회 중 `interdigitate_layout` 39회 전부 `method=search, base=None`, `common_centroid_layout` 25회 중 24회 `search`(n_fingers=1이라 residual 1.0), 1회만 `rotation_exact`(M1a/M1b branch, 성장 후 nf=2). `pattern_table` 경로는 0회.

## 3. 총 W가 바뀌는 지점 전수

| # | 위치 | 무엇이 바뀌나 | 규칙 | sizing 재평가 |
|---|---|---|---|---|
| W1 | `assign_finger_geometry` SD:6021, 특히 단위셀 폴백 SD:6091-6095 | n_fingers·finger_w·w | 행 안 W가 정확한 정수배가 아니면 앞 행 finger_w를 단위로 `n=max(1, round(W/unit))` | **없음.** ctx.sized W는 옛 값 그대로 남는다 |
| W1' | 같은 함수, seed·target 경로 | w | `search_stack_finger_w`가 정확한 정수배만 내므로 이 경로는 W 보존 | 불필요 |
| W2 | `run_topology_pipeline_with_finger_fixup` → `apply_and_revalidate_pair_adjustment` SR:11412 | n_fingers(+delta) | Euler 홀수차수 개선 | 있음(`revalidate_finger_override`: ID·L·vds 고정, 새 W에서 gm_id 역산 → 전 metric·제약 재판정). 기준 W는 **ctx(sizing) W**라 W1에서 생긴 차이를 모른다 |
| W3 | `_fixup_euler_blocked_rows` SR:11595 | n_fingers | W2와 같은 전략 | 있음(같은 함수) |
| W4 | `apply_and_revalidate_matching_finger_growth` SR:11551 | n_fingers → min_fingers(2) | 3c 회전 최적을 위해 | 있음(같은 함수). 위반이면 적용 안 함 |
| W5 | `_evaluate_row_split` SR:9396-9401 | overrides의 n_fingers·w 재합산 | repair 뒤 행별 n_fingers 합 | 없음(W4의 결과를 옮겨 적기만) |
| W6 | `apply_explicit_row_split` SD:6119, `_layout_result_to_rows` SD:7249 | 행 분할만 | 소자 n_fingers를 행에 나눠 담음 | 총 W 불변(합 보존) |
| W7 | `check_finger_width_compatibility` SD:5161 | 바꾸지 않음 | 정수배 아니면 ValueError | -- |

재평가 경로가 있어도 **SPICE 재검증·theta 재탐색 루프는 없다**: `revalidate_finger_override`는 ID를 고정한 채 gm_id만 역산하고 제약을 재판정할 뿐이며, 위반이면 그 후보를 버린다(완화 또는 중단). 그리고 W1은 아예 재판정 대상이 아니다.

### 실측: current_reuse_telescopic_ota 소자별 W (um)

sizing W = theta 탐색 직후 W, 최종 레이아웃 w = 최종 netlist의 Σ(n_fingers×finger_w), 최종 반환 sizing W = `optimize_full_circuit_budget` 반환 `sizing`(instance.json `sizing`과 같은 값).

| 소자 | sizing W | assign 후 nf×fw=w | euler-fixup 후 w | 최종 레이아웃 w | 최종 반환 sizing W | 레이아웃/sizing | 원인 |
|---|---|---|---|---|---|---|---|
| M18a | 1.193 | 1×36.0165=36.017 | 72.033 | 2×36.0165=72.033 | 72.033 | 60.39 | W1 + W2(euler, M18a/M9a +1, gm_id 15.5→16.76 재판정) |
| M9a | 1.193 | 1×36.0165=36.017 | 72.033 | 72.033 | 72.033 | 60.39 | 같음 |
| M18b | 1.051 | 36.017 | 36.017 | 36.017 | 1.051 | 34.28 | W1(재평가 없음) |
| M9b | 1.051 | 36.017 | 36.017 | 36.017 | 1.051 | 34.28 | W1 |
| M58 | 1.686 | 36.017 | 36.017 | 36.017 | 1.686 | 21.36 | W1 |
| M3b | 3.393 | 36.017 | 36.017 | 36.017 | 3.393 | 10.62 | W1 |
| M3a | 3.495 | 36.017 | 36.017 | 36.017 | 3.495 | 10.31 | W1 |
| M37b | 4.485 | 36.017 | 36.017 | 36.017 | 4.485 | 8.03 | W1 |
| M37a | 5.000 | 36.017 | 36.017 | 36.017 | 5.000 | 7.20 | W1 |
| M4a/M4b | 5.215 | 36.017 | 36.017 | 36.017 | 5.215 | 6.91 | W1 (W4 시도는 gm_id=30 역산 실패로 거부) |
| M11b/M20b | 12.012 | 36.017 | 36.017 | 2×36.0165=72.033 | 72.033 | 6.00 | W1 + W4(3c 성장, gm_id 17.6→21.1) -- 성장 뒤에도 3c dx=4.0 FAIL(공유 hub·branch 없어 재배치 불가) |
| M1a/M1b | 16.409 | 36.017 | 36.017 | 72.033 | 72.033 | 4.39 | W1 + W4(branch M1/M2 성장 1→2, 3c PASS) |
| M2b | 16.701 | 36.017 | 36.017 | 72.033 | 72.033 | 4.31 | 같음 |
| M2a | 19.795 | 36.017 | 36.017 | 72.033 | 72.033 | 3.64 | 같음 |
| M11a/M20a | 11.962 | 36.017 | 36.017 | 36.017 | 11.962 | 3.01 | W1 |
| M63 | 1.087 | 1×2.3665 | 2.366 | 2.366 | 1.087 | 2.18 | W1 |
| M10/M19 | 17.887 | 36.017 | 36.017 | 36.017 | 17.887 | 2.01 | W1 |
| M14a/M23a, M14b/M24b | 1.916 / 1.835 | 2.366 | 2.366 | 2.366 | 그대로 | 1.24 / 1.29 | W1 |
| M38 | 94.112 | 3×36.0165=108.05 | 108.05 | 108.05 | 94.112 | 1.15 | W1 |
| M6 | 125.900 | 108.05 | 144.066 | 144.066 | 144.066 | 1.14 | W1(감소) + W2(euler +1, 재판정) |
| M57 | 164.159 | 180.083 | 180.083 | 180.083 | 164.159 | 1.10 | W1 |
| M64 | 2.159 | 2.366 | 2.366 | 2.366 | 2.159 | 1.10 | W1 |
| M5 | 65.746 | 72.033 | 72.033 | 72.033 | 65.746 | 1.10 | W1 |
| M8/M17 | 68.071 | 72.033 | 72.033 | 72.033 | 68.071 | 1.06 | W1 |
| M60 | 4.280 | 4.549 | 4.549 | 4.549 | 4.280 | 1.06 | W1 |
| M61 | 4.964 | 4.549 | 4.549 | 4.549 | 4.964 | 0.92 | W1(감소) |
| M39 | 10.729 | 9.098 | 9.098 | 9.098 | 10.729 | 0.85 | W1(감소) |
| 나머지 19개 | -- | -- | -- | -- | -- | 1.00 | W 보존 (정수배 경로) |

- 51소자 중 **29소자가 최종 반환 sizing W ≠ 레이아웃 w**(27소자는 5% 이상 차이). 총 W: sizing 1241.7 um → 레이아웃 2164.1 um(+74%), 반환 sizing 합 1740.4 um. `area_um2`(806.9) 등 metric은 반환 sizing 기준이라 레이아웃 W를 반영하지 않는다.
- **M3a 3.49 → 36.02 um의 정확한 원인**: `resolve_stack_layout`이 M3a/M3b/M4a/M4b/M5를 한 행 `diffpair_branch_a__nmos`로 묶음 → `assign_finger_geometry`가 이 행(W 3.49/3.39/5.22/5.22/65.75)에 `search_stack_finger_w`를 target=5와 무목표로 두 번 불렀으나, 다섯 W가 공통 finger_w의 정확한 정수배가 아니라 후보 0개(SD:5999 `abs(n-round(n))>1e-6`) → 단위셀 폴백(SD:6091)이 앞서 확정된 단위폭 [36.0165](seed 행 `cmfb_load_a` M36a/M36b 180.08/5)만 후보로 받아 첫 소자 M3a 기준 상대오차 9.31(931%)인 36.0165를 그대로 채택 → SD:6095 `n=max(1, round(3.49/36.02))=max(1,0)=1` → w=36.02. 오차 상한 검사도, gm/ID 재판정도 없다. 같은 규칙으로 M18b(1.05→36.02, 오차 34배), M58, M37a/b, M4a/b 등이 커졌다. seed 행의 단위폭(36 um)이 이후 거의 모든 행으로 전파되는 것이 핵심이다.

## 4. 차동쌍 common-centroid 필수 규칙 준수 여부 (실측)

`select_layout_tool`은 offset 쌍에 common-centroid를 필수로 정하고 audit도 3c를 필수 게이트로 둔다 -- **규칙은 코드에 있다.** 그러나 실측 최종 결과에서 차동쌍 3개 중 1개만 지켜졌다.

| 그룹 | 축C(선언) | 필수 게이트 | 적용 도구·method | 최종 결과 | 비고 |
|---|---|---|---|---|---|
| M1a/M1b (PMOS 입력 차동쌍) | offset | 3c | common_centroid(branch M1a-M2a/M1b-M2b), nf 1→2 성장 뒤 `rotation_exact` | **3c PASS** dx=0 dy=0 | 성장으로 W 16.4→72.0 |
| M4a/M4b (NMOS 입력 차동쌍) | offset | 3c | common_centroid(branch M4a-M3a) nf=1 `search` → 성장 거부(gm_id=30 LUT 범위 밖) → **relaxed: interdigitate 강제** | **3c FAIL** dx=1.0 | `relaxed_pairs`에 기록, audit FAIL 유지 |
| M37a/M37b (CMFB 차동쌍) | offset | 3c | common_centroid nf=1 `search` | **3c FAIL** dx=1.0 | 성장 시도조차 안 됨: 성장 루프가 앞선 M11b/M20b에서 `growth_not_applicable`로 즉시 종료 |
| M2a/M2b, M3a/M3b (캐스코드) | ratio, 비공유 | 3c | M1/M4 branch에 묶여 이동 | M2 PASS / M3 FAIL dx=3.0 | M3은 relaxed |
| M11b/M20b, M14a/M23a, M9a/M18a, M9b/M18b | ratio, 비공유 | 3c | 공유 hub·branch 없음 → repair 건너뜀 | 전부 FAIL(dx 3~4) | M11b/M20b는 쓸모없이 W만 6배 |
| M8/M17, M13/M22, M10/M19, M12/M21, M14b/M24b, M15/M25, M16/M26, M36a/M36b, M60/M61, M11a/M20a | ratio, 공유 | 3b | 초기 Euler trail 그대로 | 3b PASS | |
| 7소자 미러(M18_bg…) 비forced 조합 | ratio, 공유 | 3b | 서로 다른 행 | 3b FAIL 다수 | 그룹 병합은 forced만, audit은 전체 |

최종 `audit_ok=False`(box-shape 10.13 FAIL 포함), `unresolved_reason=growth_not_applicable`. 즉 **차동쌍 common-centroid 필수 규칙은 판정만 되고 보장되지 않는다.** 실패 원인 셋: (1) n_fingers=1이면 회전 최적 경로가 기하학적으로 불가능(dx=1.0), (2) 성장은 W를 늘리므로 gm/ID 위반이면 거부되고 interdigitation으로 완화된다(규칙 위반을 허용하는 분기), (3) 성장 루프가 첫 "적용 불가" 쌍에서 멈춰 뒤 쌍(M37)은 시도되지 않는다.

## 5. 새 엔진 제안

원칙(사용자 규칙): sizing이 gm/ID·L·ID로 총 W를 정한다. 레이아웃은 **총 W를 유지**하며 nf·finger_w·행 구성을 고른다. 차동쌍은 common-centroid 필수, 그 밖의 matching 그룹은 common-centroid 또는 interdigitation.

### (a) 그대로 import해 쓸 함수 (순수 그래프·기하, W를 안 바꿈)

| 함수 | 근거 |
|---|---|
| `build_graph`, `check_euler_condition`, `hierholzer`, `check_walk_sequence`, `mirror_symmetric_trail`, `build_stick_diagram` | 입력 Transistor(n_fingers)만 보고 W를 바꾸지 않음. 결정론(sorted 시작점). kind 혼합 하드 게이트 포함 |
| `common_centroid_layout`, `interdigitate_layout`, `_common_centroid_nway_exact` 등 하위 | hub-leaf 배치 생성기, W 불변. 단 `interdigitate_layout`은 `base`를 넘겨 패턴표 경로를 실제로 쓰도록 호출 측에서 지정 |
| `check_finger_width_compatibility`, `check_box_shape`, `compute_row_geometry` | 순수 판정 |
| `find_min_crossover_layout_with_branch_composite` | 행 분할만, W 불변(그래프 이론상 항상 성공) |
| `apply_explicit_row_split`, `_layout_result_to_rows` | 소자 finger를 행에 나눠 담음, 총 W 보존 |
| `pack_floorplan_grouped`, `rebuild_floorplan`, `check_stick_diagram_coverage` | 기하·완전성 |
| `search_shared_finger_w`, `_quantize_to_grid` | 후보 생성기(채택 정책은 새 엔진이 소유) |

### (b) 입력 인터페이스를 바꿔야 할 함수 (태그 대신 구조 유도 출력을 받도록)

| 함수 | 지금 입력 | 바꿀 입력 | 근거 |
|---|---|---|---|
| `select_layout_tool`, `audit_row_split`, `repair_matching_safety` | `pair_sensitivity`(선언 `matching_sensitivity` 문자열) + 2-tuple 펼침 | 구조 유도 matching group 레코드: `{members, role: diff_pair/mirror/cascode_pair/..., shares_node, hub_net, required_pattern}` | 축C를 선언에 의존. 차동쌍 판정은 connectivity(공유 source + 서로 다른 gate + 입력 포트)로 유도 가능. N소자 그룹을 2-tuple로 펼쳐 7소자 미러가 21쌍 3b 요구로 폭증 |
| `resolve_stack_layout`, `merge_layout_groups_by_matching_pairs`, `derive_horizontal_stack_groups` | `device_roles.vertical_stack_id`(선언) + `current_forced` 쌍 | 구조 유도 KCL branch + matching group(위와 같은 레코드) | 그룹 병합 기준(forced만)과 감사 기준(전체)이 달라 구조적 FAIL을 만든다. 같은 matching group 레코드 하나를 둘 다 쓰게 |
| `_branch_composite_pair` | 선언 matching_pairs + 레일 | 구조 유도 branch 대응 | 같은 이유 |
| `assign_finger_geometry` | `sizing_results`(W) + 그룹 | 소자별 **W 계약값(고정) + 허용 오차** + matching group | 지금은 W를 출력이 바꿔 버린다(아래 c) |

### (c) 고쳐야 할 규칙

1. **총 W 보존을 하드 불변식으로**: `assign_finger_geometry`의 단위셀 폴백(`n=max(1, round(W/unit))`, 오차 상한 없음)을 없앤다. 행 안 W가 공통 finger_w의 정수배가 아니면 (i) 그 행을 소자별 finger_w가 다른 행으로 쪼개거나(finger_w 균일은 행 안에서만 필요, 참고문서 §8.1), (ii) `grid_step`·`max_snap_error`(예: 1%)를 켠 `search_stack_finger_w`로 근사 후보만 허용한다. 오차가 허용치를 넘으면 레이아웃이 W를 고치지 말고 실패를 반환한다. 근거: 실측 29/51 불일치, M3a ×10.3, M18b ×34.
2. **W가 바뀌면 sizing 재평가 루프**: 레이아웃이 W 변경(finger 증가 등)을 원할 때는 레이아웃이 직접 적용하지 말고 `W_request`로 sizing에 돌려준다. sizing은 그 소자를 W 고정 제약으로 다시 풀고(ID 고정 gm_id 역산만이 아니라 theta·헤드룸 재탐색), 통과하면 새 W 계약으로 레이아웃을 다시 돈다. 반복 상한과 수렴 판정(W 계약 불변)을 둔다. 지금의 `revalidate_finger_override`는 판정기로는 재사용 가능하나 기준 W가 ctx W라 W1 차이를 모르는 점을 고쳐야 한다(레이아웃 실제 w를 기준으로).
3. **차동쌍 common-centroid는 완화 금지**: `relaxed_pairs`의 interdigitation 강제는 차동쌍에 쓰지 않는다. common-centroid가 불가능하면(n_fingers 부족) 해법은 sizing 쪽 "nf>=2를 만족하는 W 분할"(같은 총 W에서 finger_w를 줄여 nf를 늘리는 것 -- 총 W 보존으로 가능)이다. 실측 M4a/M4b는 sizing 총 W 5.22 um을 2×2.61 um(spec min_finger_w 1 um 이상)으로 나누면 W 변경 없이 nf=2 회전 최적이 가능했으나, 옛 엔진은 W1에서 이미 36.02 um(1×36.02)로 키운 뒤 finger_w를 고정하고 nf만 늘려 72 um로 만들려다 gm_id 역산(=30, LUT 범위 밖)에서 거부됐다.
4. **matching 수리 루프가 첫 실패에서 멈추지 않게**: 쌍마다 독립 판정하고 실패 사유를 모두 모은다(M37 미시도 사례).
5. **패턴 선택을 선행(구성)으로**: audit FAIL 뒤 수리가 아니라, 행 구성 단계에서 matching group마다 패턴(표 경로 우선, 없으면 rotation/search)을 먼저 고르고 그 배치로 Euler trail을 검증한다.
6. **seed 단위폭 전파 금지**: 첫 행 finger_w가 모든 후속 행 단위폭 후보가 되는 정책(§7.9 질문12(a) 미결 표기)은 버린다. 행마다 자기 W들에서 finger_w를 정한다.

### 새 sizing 출력 → 레이아웃 입력 데이터 계약(초안)

```jsonc
{
  "contract_version": "layout-input/0.1",
  "topology_ref": "skills/.../X.topology.json",
  "process": {"grid_step_m": 5e-9, "min_finger_w_m": 4.2e-7, "max_finger_w_m": 4.0e-5,
              "l_grid_step_m": 5e-9},
  "devices": {
    "M4a": {
      "kind": "nmos", "d": "N3a4a", "g": "Vip", "s": "Vy", "b": "gnd",
      "W_m": 5.2152e-6,            // sizing이 정한 총 W -- 레이아웃이 바꾸면 안 되는 계약값
      "W_tol_rel": 0.01,           // 스냅 허용 오차(넘으면 레이아웃 실패 반환)
      "L_m": 1.0e-6, "ID_A": ..., "gm_id": ..., "vds_V": ..., "vsb_V": ...,
      "min_fingers": 2,            // matching group 요구에서 유도(차동쌍 회전 최적 nf>=2)
      "W_locked": true             // false면 레이아웃이 W_request를 낼 수 있는 비-critical 소자
    }
  },
  "matching_groups": [
    {"id": "mg_diff_in_n", "members": ["M4a", "M4b"],
     "role": "diff_pair",                 // 구조 유도: 공유 source + 서로 다른 gate + 입력 포트
     "evidence": {"hub_net": "Vy", "shares_node": true, "gates": ["Vip", "Vim"]},
     "required_pattern": "common_centroid",   // diff_pair -> 필수, 완화 금지
     "allowed_patterns": ["common_centroid"],
     "branch_with": [["M4a","M3a"],["M4b","M3b"]]},   // 직렬 branch 대응(구조 유도)
    {"id": "mg_mirror_bg", "members": ["M18_bg","M60","M61"], "role": "current_mirror",
     "evidence": {"gate_net": "...", "source_net": "vdd"},
     "required_pattern": null, "allowed_patterns": ["common_centroid","interdigitation"]}
  ],
  "row_groups": [   // 구조 유도 KCL branch + matching group 병합 결과(같은 레코드로 병합·감사)
    {"id": "row_diff_n", "kind": "nmos", "members": ["M3a","M3b","M4a","M4b","M5"]}
  ]
}
```

레이아웃 출력 계약(역방향): 소자별 `{n_fingers, finger_w, rows:[{row_id, n_fingers}], W_realized, W_err_rel}`, matching group별 `{pattern, method, residual, dx, dy, ok}`, 행별 `{node_sequence, transistor_sequence, crossover_after}`, 그리고 W를 바꾸고 싶을 때만 `W_requests:[{device, W_new, reason}]`(sizing이 재평가해 새 계약으로 응답). `W_realized`가 `W_m`에서 `W_tol_rel`을 넘으면 그 결과는 무효다.
