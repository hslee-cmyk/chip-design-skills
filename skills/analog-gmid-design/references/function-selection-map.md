# 함수 선택 지도 — "이 상황엔 이 함수"

> 이 문서의 목적은 단 하나다: **AI가 스스로 계산 로직을 상상해서 대신하지 않도록**, 이 skill의
> 세 스크립트(`sizing_recipe.py`/`stick_diagram.py`/`topology_library.py`)에 이미 구현된 함수를
> "언제·왜" 호출해야 하는지 표로 못박는다. 함수의 내부 로직을 여기서 재서술하지 않는다 —
> 재서술은 틀릴 수 있고, 틀린 재서술을 코드 대신 신뢰하는 위험이 있다(SKILL.md 절대 원칙
> 참고). 정확한 동작은 항상 실제 코드(docstring 포함)를 읽거나 직접 호출해서 확인한다 — 아래
> 표는 "어느 파일의 어느 함수를 찾아야 하는지"까지만 안내한다.

## 0. Harness(오케스트레이션) — 작업 시작 전 반드시 여기부터 확인

SKILL.md 핵심 원칙: **harness → 원소 함수 → (없을 때만) 새 코드** 순서로 작업한다. 아래 5개가
이 skill의 전체 harness다 — 지금 하려는 작업이 이 중 하나로 끝나는지 먼저 확인하고, 아니면
그때 §1~§10의 원소 함수 표로 내려간다.

| 상황 | harness 함수 | 상세 |
|---|---|---|
| topology JSON 하나로 gm/ID 사이징 전체를 실행 | `run_sizing_pipeline(topology_json_path, design_spec)` | §10 |
| 다단 회로(Miller/NGCC/NMCNR 등) 전체를 한 번에 사이징 | `optimize_multistage(topology_fn, luts, L_candidates, VDS_candidates, gm_id_grid, objective, gain_min, w_max)` | §1 |
| 리포트를 완료로 선언하기 전 소자 수/net/matching/box-shape 전체 감사 | `run_full_circuit_audit(devices, expected_counts, dispositions, ...)` | §8 |
| box-shape 때문에 한 functional group을 여러 물리 행으로 다시 지을 때 Euler/box-shape/matching 순서대로 전부 확인 | `audit_row_split(rows, matching_pairs=None, pair_kinds=None, max_ratio=1.5)` | §9 |
| 사이징 완료 후 실제 layout(box-shape/matching/floorplan/coverage) 전체 계산 | `run_topology_pipeline(topology_json_path, sizing_overrides, floorplan_hints=None)` | §10 |

이 5개는 전부 여러 원소 함수를 정해진 순서로 묶어 실행하는 워크플로우다 — 그 내부 단계를
손으로 재현하지 말고 harness 자체를 호출한다. `load_topology()`/`load_sizing_targets()`/
`write_sizing_results()`/`save_instance_json()`은 harness가 파일 입출력에 쓰는 순수 I/O
함수라 원소 함수 표(§10)에 있다.

## 1. gm/ID 사이징 (`assets/sizing_recipe.py`)

| 상황 | 함수 | 비고 |
|---|---|---|
| 단일 소자, gm과 gm/ID가 이미 정해짐 → W 계산 | `size_transistor(gm, gm_id, L, lut, VDS, VS=0.0)` | 기생 반복 없는 1회 계산 |
| 단일 소자, 기생 커패시턴스까지 반복 수렴시켜 사이징 | `converge_with_parasitics(fT, C_external, gm_id, L, lut, ...)` | §1 스텝 3~5를 자동 반복 |
| fT(또는 GBW) 스펙에서 gm 역산 | `gm_from_fT(fT, C)` | `gm = 2π·fT·C` |
| 준정적 조건 확인 | `check_quasi_static(fT, gm, Cgg, margin=0.1)` → `QuasiStaticVerdict(ok)` | §5 체크리스트 항목 |
| slew-rate 계산 | `slew_rate(ID, C)` | |
| "이 gm/ID를 고르면 어떻게 되나"가 아니라 **"스펙(gain/면적/준정적) 만족하며 전력·면적 최소인 sizing을 찾아라"** | `find_optimal_sizing(lut, L_candidates, VDS_candidates, gm_id_grid, gm, objective, gain_min, w_max)` | 단일 소자, (L,VDS,gm/ID) 격자 이산 탐색 |
| 다단 회로 전체(topology마다 다른 위상보상 방정식 적용) | `optimize_multistage(topology_fn, luts, L_candidates, VDS_candidates, gm_id_grid, objective, gain_min, w_max)` | topology_fn은 §2 표에서 골라 씀. `objective="power"`면 **반드시 w_max도 같이 줄 것**(안 주면 W가 발산 — 물성, 버그 아님) |
| gm/ID→W가 역방향으로 필요할 때(W를 먼저 고정하고 결과 gm/ID를 알고 싶을 때) | `SemiEmpiricalGmIdLUT._solve_vgs()`를 이분탐색으로 역방향 사용 (SKILL.md §2.1 rule 1 상황) | 정방향 사이징이 비현실적 W를 낼 때 |
| 실측 LUT가 아니라 즉석에서 합성 LUT가 필요할 때(E.K.V. 해석식) | `build_toy_lut(n, UT, VTo, ISuo, ...)` | 실제 공정 데이터 있으면 쓰지 말 것 — `SemiEmpiricalGmIdLUT(...)`에 직접 4D 배열 로드 |

## 2. Topology별 위상보상 방정식 (`assets/topology_library.py`)

`optimize_multistage()`의 `topology_fn` 인자로 그대로 넘긴다 — 새 토폴로지가 이 목록에 없으면
**직접 짜지 말고 먼저 `references/topology-fn-derivation-guide.md` §1을 읽고** 같은 패턴으로
`topology_library.py`에 추가한다.

| Topology | 함수 | 검증 상태(자세한 근거는 함수 docstring) |
|---|---|---|
| 2단 Miller OTA | `miller_ota_topology(GBW, CL, Z=10.0, NDP=4.0)` | 완전 결정(자유도 없음), 원문 수식 대조 완료 |
| 3단 NMCNR(RHP-zero 완전제거) | `nmcnr_3stage_topology(GBW, CL, PM_target_deg=65.0, kg=0.5)` | `kg`는 원문 자체가 남긴 자유도 — 기본값은 임의값, 실사용 전 SPICE 재확인 필수 |
| NMCNR 보상소자 실값(Cm1/Rm/Cm2) | `nmcnr_compensation_elements(gm1, gm2, gm3, CL, kg)` | §3(수동소자도 확정 필수)의 적용 사례 |
| NMCNR 사이징 후 GBW/PM/노치 재검증 | `nmcnr_predict_notch(gm1, gm2, gm3, R1, R2, R3, ...)` | 근사식(Eq 10/11)이 아니라 정확한 4-노드 전달함수 — **사이징 후 반드시 호출** |
| 3단 NGCC | `ngcc_3stage_topology(GB, k, CL, alpha, mu_ratio=None)` | gm1/gm2/gm3 전부 원문 Eq로 완전 결정. `mu_ratio`는 설계 자유도가 아니라 공정 파라미터 — 자기 공정 값으로 교체 |
| Miller OTA의 Cc(보상캡) 실값 | 별도 함수 없음 — `gms[0]/(2π·GBW)`로 호출자가 직접 계산 | `optimize_multistage()`가 반환하는 `gms[0]`(=gm1)과 스펙의 GBW만 있으면 1줄로 나온다 — "값이 없다"고 스킵하지 말 것(§3 참고) |
| Miller OTA의 nulling resistor Rz 실값 | 별도 함수 없음 — `1/gms[1]`(=1/gm2)로 호출자가 직접 계산 | `gm-id-methodology.md` §6.4/§6.7의 표준식(R≈1/gm2). NMCNR/NGCC 등 다른 토폴로지의 보상소자 식도 필요하면 같은 문서 §10에서 찾을 것 — 새로 유도하지 말 것 |
| NGCC의 보상소자 실값 | 아직 전용 함수 없음 | `topology-fn-derivation-guide.md`의 패턴을 따라 `topology_library.py`에 `ngcc_compensation_elements()`를 추가할 것 — 없다고 스킵하지 말 것(§3 참고) |

## 3. Matching 후보 탐지 (`assets/stick_diagram.py`)

| 상황 | 함수 | 비고 |
|---|---|---|
| 전류거울/차동쌍 후보를 구조적으로(gate/source 공유) 자동 탐지 | `find_matching_candidates(transistors)` | 오탐 가능 — 최종 판단은 항상 설계자 몫(§2.6 오탐 사례). **사이징 전(W 없음)에도 diff_pair 후보를 낸다** — W는 있으면 오탐 방지용 추가 필터일 뿐 필수 아니다. topology JSON 저작 단계(§10)에서도 이 함수 그대로 쓸 것, 수동으로 다시 구조 신호를 확인할 필요 없음 |
| **"이 두 소자가 current mirror인가?"를 판단할 때** | 위 함수의 판정 기준(같은 kind + 같은 **gate net**)을 그대로 적용 | 게이트가 다르면(예: 하나는 고정 바이어스, 하나는 피드백 제어) mirror 아님 — "논문이 매칭이라 안 했다"가 아니라 게이트 공유 여부로 판단 |
| stage 경계를 넘는 물리 행 병합 후보 탐지(**stack_id 배정 전에 반드시 먼저 실행**) | `find_hub_merge_candidates(transistors)` | §4.1 — stage별로 먼저 나누고 시작하면 이 탐지 자체가 누락된다 |
| leaf 3개 이상인 병합 후보의 실현 가능성 사전 스크리닝 | `check_multi_leaf_hub_parity(n_fingers_by_leaf)` | 최종 채택 전 `build_graph()`+`check_euler_condition()`으로 반드시 재확인 |
| 극성+finger폭 기준 자동 stack 그룹핑 | `split_into_stacks(transistors)` | `stack_id`로 회로 지식을 오버라이드 가능 |

## 4. Euler trail / Stick diagram 생성 (`assets/stick_diagram.py`)

| 상황 | 함수 | 비고 |
|---|---|---|
| W가 stack의 finger 폭의 정수배인지 확인(오일러 분석보다 먼저) | `check_finger_width_compatibility(transistors, tol=1e-9)` | §3.5 게이트 |
| 그래프 차수 분석(홀수차수 노드 개수) | `build_graph(transistors)` → `check_euler_condition(g)` | 0/2개면 PASS, 4개 이상이면 §3(a/b/c) 해소 필요 |
| 실제 stick sequence(node열+transistor열) 생성 — **리포트 §5에 넣을 유일한 데이터 소스** | `build_stick_diagram(transistors)` | 이 반환값을 손으로 축약/재구성 금지(SKILL.md 절대 원칙) |
| 홀수차수 노드 ≥4개일 때 finger ±1 조정 제안 | `suggest_finger_adjustments(transistors)` | 순수 그래프 계산 — 제안이 스펙을 깨는지는 §5(gm/ID) 체크리스트로 별도 재검증 |
| PDF 스타일 텍스트 렌더링(터미널 확인용, **리포트의 시각 자료 아님**) | `render_stick_diagram(result)` | ⚠️ 이 함수의 출력 문자열을 리포트 HTML에 그대로 붙여넣지 말 것 — 리포트 시각화는 항상 `assets/report_template.html`의 `renderStack()`(SVG) 재사용 |

## 5. Box-shape / Cell 정사각형화 (`assets/stick_diagram.py`)

| 상황 | 함수 | 비고 |
|---|---|---|
| 여러 stack을 세로로 쌓을 때 stack별 다른 finger_w로 목표 행폭 맞추기(Case A) | `search_stack_finger_w(devices, target_row_fingers, min_finger_w=1.0, max_finger_w=40.0, tol_fingers=3)` | §8.2 |
| 여러 stage를 가로로 나란히 놓을 때 공통 finger_w 하나로 맞추기(Case B) | `search_shared_finger_w(devices, min_finger_w=0.4, max_finger_w=45.0, min_fingers=1)` | §4.2 — Case A/B 중 어느 쪽이 맞는지는 반드시 **둘 다 실행**해서 스냅오차/행폭비율로 비교 후 결정(schematic 방향은 출발 가설일 뿐) |
| box-shape 비율 PASS/FAIL 판정(SPICE 이전 필수 게이트) | `check_box_shape(row_widths, max_ratio=1.5)` | §8 — `check_euler_condition()`과 동급의 명시적 게이트, 눈대중 금지 |
| nominal W 근방 unit-cell 정수배 후보 생성 | `search_unit_cell_sizing(nominal_w, candidate_unit_widths, min_n=1, max_n=20)` | §5.5 |
| box-shape FAIL을 최종으로 받아들이기 전, 물리 행 분할 비용을 숫자로 계산 | (전용 함수 없음 — `ceil(총_핑거수 / (다른 극성 최대 행폭 × max_ratio))`을 호출자가 계산) | §8.5 — 정성적 설명만으로 FAIL을 최종 결론 삼지 말 것 |

## 6. Interdigitation / Common-centroid 배치 (`assets/stick_diagram.py`)

| 상황 | 함수 | 비고 |
|---|---|---|
| 매칭쌍을 축대칭 순서로 생성(절반만 설계) | `build_mirror_symmetric_pattern(half, pair_map, center=None)` | §2.5.3 |
| 생성된(또는 기존) 시퀀스가 실제로 축대칭인지 검증 | `check_mirror_symmetry(sequence, pair_map)` | **Euler trail이 존재한다는 것과 매칭 대칭인 것은 별개** — 항상 별도로 검증할 것 |
| 사람이 제안·재배열한 순서가 실제로 하나의 연속된 diffusion(한붓그리기)으로 이어지는지 독립 검산 | `check_walk_sequence(transistor_sequence, transistors)` | **필수, `build_stick_diagram()`이 직접 반환한 게 아닌 모든 제안 순서에 적용**. finger 개수 일치 + 연속성(양쪽 시작점 시도) 둘 다 확인, 끊기면 `break_index`/`break_reason` 반환. finger 개수가 채택안과 같아도 순서가 실제로는 안 이어질 수 있다 — 반드시 이 함수로 재검산할 것(design-report-spec.md §1 표 5번) |
| 매칭쌍 개수가 홀수라 단독 좌우 분할이 안 될 때 | `find_interleaved_symmetric_splits(count_a, count_b)` | §2.5.4 |
| hub-leaf **N개(N>=2) 소자**를 connectivity 그대로 넣어 common-centroid 배치를 자동으로 찾기(개수가 달라도, row 개수를 자유롭게 지정해도) | `common_centroid_layout(transistors, n_rows=None, max_candidates=24)` | `transistors`는 `Transistor` 리스트(전부 같은 `source`=hub 공유, `drain`은 서로 달라야 함, `n_fingers`가 목표 개수) — `names`/`leafs`/`hub_net`을 따로 안 받고 여기서 직접 추론한다. 3단계 우선순위: **① `target_rows`(=`n_rows` 명시값 또는 미지정 시 N)가 소자 수와 같고 개수 전부 같음** — 증명된 최적 경로(회전 대칭, **잔차 정확히 0**). N개 leaf 회전(`name_i->name_{i+1 mod N}`)으로 N개 행을 만들면 모든 소자가 모든 열을 정확히 1번씩 지나감이 증명돼 있다. **② N=2 + `target_rows==2` + 개수가 다름(비율)** — `COMMON_CENTROID_PATTERNS`의 2-소자 문헌 패턴(예: `AAB`/`BAA`=2:1)이 정확히 맞으면 그 검증된 결과(잔차 0, `method="pattern_table"`)를 쓴다. **③ 그 외** — 휴리스틱 탐색 경로(증명된 최적 아님, `search_stack_finger_w()` 등과 같은 "candidate 생성+objective 정렬" 철학, `method="search"`) — 비례 라운드로빈으로 소자를 최대한 고르게 섞은 뒤 `n_rows`개로 균등 분할, 여러 절단 지점(phase) 중 `(crossover_count, isolated_pairs, residual)` 사전식 정렬로 최선을 채택. 반환에 `"residual"`/`"isolated_pairs"`/`"crossover_count"`/`"method"`(`"rotation_exact"`\|`"pattern_table"`\|`"search"`)가 포함되므로 호출자가 어느 경로로 나온 결과인지 항상 확인할 것. **한계**: 잔차 지표는 행 내부(x) 위치만 비교하므로 소자 개수 편차가 크면 y방향 비대칭까지는 못 잡는다. **`isolated_pairs`**: `n_rows`가 총 finger 수 대비 너무 많으면(모든 행 길이가 1) 소자가 서로 단 한 행에서도 공존 못 한 채 각자 대칭으로만 보여 `residual=0.0`(거짓 "완벽")이 나올 수 있다 — `isolated_pairs`가 0이 아니면 실제로 격리된 것(회전/표 경로는 항상 0). **crossover 폴백**: 0-crossover가 안 되면 `find_min_crossover_layout()`으로 최소 crossover 배치로 폴백한다 — `count>=N`(경로①) 또는 표에 안 맞는 비율(경로③)이기만 하면 사실상 실패하지 않는다(광범위한 조합 전수 검증됨). 기존 0-crossover 성공 케이스는 그대로 유지된다. 각 행의 `"segments"`/`"crossover_after"` 필드로 crossover 위치를 확인할 것 |
| hub-leaf 구조가 단일 연속 diffusion(0 crossover)으로 안 될 때 **최소 개수의 crossover routing**만으로 실현하는 배치 찾기 + 그 개수 표시 | `find_min_crossover_layout(transistors)` | 그래프 이론(route inspection/T-join의 표준 결과) 적용: 연결된 그래프의 홀수차수 노드가 2m개면 전체 edge를 정확히 **m개의 trail**로 쪼갤 수 있고 이보다 적게는 안 된다(m<=1이면 `check_euler_condition()`이 이미 처리하는 0-crossover 경우). 홀수차수 노드를 2개씩 짝지어 m개의 가상 edge를 추가하면 전체가 오일러 회로가 되고, `hierholzer()`로 계산한 뒤 가상 edge 지점마다 끊어서(가상 edge 자체는 버림) m개의 진짜 trail로 분해한다. **우선순위는 항상 0-crossover 먼저**(`check_euler_condition`이 impossible이 아니면 곧바로 그 결과를 반환, m개 분해로 안 감). 반환: `{"segments":[...], "crossover_count": m-1, "odd_nodes":[...]}` — `crossover_count`가 이어붙이는 데 필요한 최소 접합 개수. **짝짓기 방법과 무관하게 필요한 crossover 개수 자체는 항상 같다**(T-join 정리 — 어느 소자가 어느 segment에 속하는지만 달라짐). 각 segment가 실제로 유효한 walk인지는 `_hubleaf_sequence_node_path()`로 재확인할 수 있다 |
| hub-leaf 소자들을 1행 interdigitation으로 배치(문헌 패턴표 우선, 안 맞으면 crossover까지 감수하는 탐색으로 자동 폴백) | `interdigitate_layout(transistors, base=None, repeat=None) -> dict` | `transistors`는 `Transistor` 리스트(전부 같은 `source`=hub 공유, `drain` 서로 다름, `n_fingers`가 목표 개수) — `common_centroid_layout()`와 동일한 입력 스타일. **`base`(+`repeat`) 지정**: `INTERDIGITATION_PATTERNS` 표에서 소자 개수(`n_fingers`)와 정확히 맞고 hub-leaf로도 유효한 repeat을 자동으로 찾아 그 결과(`method="pattern_table"`, crossover 0)를 우선 쓴다(`repeat` 생략 시 표의 모든 repeat 중 자동 매칭). `INTERDIGITATION_PATTERNS`의 32개(base×repeat) 조합 중 표로 바로 성공하는 건 **7개뿐**(`base="A"` 전부(자명) + `base="AB"`의 repeat=1,2,3) — 나머지 25개(`ABC`/`ABCD`/`ABA`/`ABABA`/`AABA`/`AABAA` 등)는 표 자체가 hub-leaf로 무효(3개 이상 leaf 사이를 hub 안 거치고 바로 전환하는 구조라 그래프상 불가능)라 **자동으로 탐색 경로(`method="search"`)로 폴백**한다. 탐색 경로는 소자 개수 비율에 맞춘 배치를 직접 구성해 0-crossover 검증하고, 안 되면 `find_min_crossover_layout()`으로 최소 crossover 배치로 다시 폴백 — 32개 조합 전수 스윕에서 예외 0건, 사실상 실패하지 않는다. `base` 생략(또는 표에 없는 base)도 이 탐색 경로로 바로 가며, 정확히 2-소자로 제한되지 않고 N개(N>=1) 임의 개수를 지원한다. 반환은 `common_centroid_layout()`와 동일 스키마(`rows`/`method`/`crossover_count`/`residual`/`isolated_pairs`) — 호출자가 별도로 `_hubleaf_sequence_node_path()`를 불러 재검증할 필요가 없다 |

## 7. 리포트 시각화 (`assets/report_template.html`)

| 상황 | 함수 | 비고 |
|---|---|---|
| §1 topology 스키매틱을 SVG로 그리기 | `renderSchematic(container, schem)` | `schem`은 `{rails, devices, wires, dots, labels, extras}` 구조화 객체 — **코드 그대로 복사해 재사용, 새로 작성 금지** |
| §5 stick diagram을 SVG로 그리기 | `renderStack(container, stackName, data)` | `data`는 `build_stick_diagram()`의 실제 반환값 그대로 — **코드 그대로 복사해 재사용, `rendered` 텍스트 필드를 `<pre>`로 덤프 금지** |

## 8. 전체회로 감사 harness (`assets/stick_diagram.py`, §6.6)

| 상황 | 함수 | 비고 |
|---|---|---|
| 2개 이상 sub-block으로 구성된 회로의 리포트를 완료로 선언하기 전 **반드시** | `run_full_circuit_audit(devices, expected_counts, dispositions, box_shape_checks=None, max_ratio=1.5, accept_fail_blocks=None)` | design-report-spec.md §1.6 — 소자 수/net 이름/전체 목록 매칭·hub-merge 판정/box-shape를 한 번에 감사. sub-block별로 나눠 국부 재확인하지 말 것(반복 실패 패턴, PRE-FLIGHT 사고 1~11) |
| 사이징 시작 전, 소스 대비 총 소자 수를 선언 | 위 함수의 `expected_counts` 인자를 채우는 게 그 자체로 이 단계 | differential 회로면 "mirror branch가 있는가"를 이 시점에 답할 것(사고10) |
| §5(stick diagram)에 §3에서 사이징된 소자 전부가 등장하는지 **독립적으로** 재확인(위 `run_full_circuit_audit()`와 별도 호출) | `check_stick_diagram_coverage(sized_device_names, stick_diagram_devices)` | design-report-spec.md §1.5 5단계 + PRE-FLIGHT 사고 27 — `run_full_circuit_audit()`는 자신에게 전달된 `devices` dict **안에서만** 커버리지를 보므로, sub-block 하나가 그 dict 자체에서 빠지면(예: bias-gen/CMFB/Class-AB는 사이징만 하고 stick diagram 호출을 아예 안 함) 잡지 못한다. `sized_device_names`는 §3 표에서 독립적으로 뽑을 것 — `run_full_circuit_audit()`에 넘긴 dict를 재사용하면 같은 누락이 그대로 안 보인다. **⚠️이 함수를 import만 하고 실제로 호출하지 않으면 아무 효과가 없다 — 완료 보고 전 `grep -n "check_stick_diagram_coverage("`로 실제 호출부가 있는지 확인할 것** |

## 9. Floorplan 패킹 (`assets/stick_diagram.py`, §6.7)

| 상황 | 함수 | 비고 |
|---|---|---|
| §5의 stack들을 하나의 사각형으로 집계 | `block_from_row_widths(name, row_widths)` | width=최대 행 finger 수, height=행 개수 — 비율 프록시일 뿐 물리 치수 아님 |
| 공유 blocks(기능 그룹 2개 이상) + 좌우 대칭쌍을 빈 공간 최소화하며 packing — **일반적으로 이걸 쓸 것** | `pack_floorplan_grouped(spine_groups, mirror_pairs, gap=1.0, height_steps=40, transistor_sequences=None, net_weights=None, height_tolerance=1.0, width_tolerance=2.0, sub_kinds=None)` | design-report-spec.md §1.7 — Stage-1/bias-gen/CMFB 등 기능 그룹을 각각 원자적 블록으로 먼저 packing한 뒤 상위 packing. **이걸 기본 진입점으로 쓸 것** — `pack_floorplan()`을 spine에 직접 쓰지 말 것(PRE-FLIGHT 사고15: 기능 그룹이 깨져 배치됨). `net_weights`(실제 net 연결)를 채우면 신호선 근접 배치까지 반영(§1.7 2.5단계) — 이때 **`width_tolerance>0`이 반드시 켜져 있어야** 효과가 있다(`width_tolerance=0`이면 `pack_to_height()`가 가장 좁은 폭만 골라 배치 후보가 하나뿐이라 `net_weights`가 무효, PRE-FLIGHT 사고16) |
| 공유 blocks(기능 그룹이 1개뿐이거나 없음) + 좌우 대칭쌍을 packing | `pack_floorplan(spine, mirror_pairs, gap=1.0, height_steps=40, transistor_sequences=None)` | design-report-spec.md §1.7 — skyline 2D packing + 대칭 유닛의 joint-height 결합. aspect_ratio만 보고 끝내지 말고 **packing_density**를 반드시 확인할 것 — ratio만 보면 빈 공간이 있어도 놓친다(PRE-FLIGHT 사고12) |
| 기능 그룹 하나(예: CMFB의 4개 stack)를 그 자체로 원자적 블록 하나로 캡슐화, 폴러리티별 분리 배치가 더 나은지도 비교 | `pack_group_as_unit(name, blocks, gap=1.0, target_ratio=1.0, net_weights=None, height_tolerance=1.0, sub_kind=None)` | `pack_floorplan_grouped()`가 내부적으로 쓰는 것 — 직접 호출은 커스텀 그룹 구조가 필요할 때만. `sub_kind`를 주면 flat packing과 폴러리티-분리 packing을 **둘 다 계산**해 aspect-ratio가 더 정사각형에 가까운 쪽을 채택한다 — 밀도만으로 고르면 그룹 자체는 나아 보여도 전체 회로 결합 시 악화될 수 있다(PRE-FLIGHT 사고17) |
| 같은 그룹 안의 block을 폴러리티(또는 임의의 "같은 diffusion" 기준)로 나눠 공통 높이로 packing 후 옆으로 배치 | `_pack_by_subkind(blocks, sub_kind, gap=1.0, height_steps=40)` | `pack_group_as_unit()`이 내부적으로 쓰는 후보 생성 함수 — kind가 2종 미만이면 `None` 반환 |
| 완성된 배치 하나의 실제 배선 비용(가중 거리 합) 집계 | `_total_wire_cost(placements, connections, y_targets=None)` | `pack_to_height()`가 폭 후보들 중 고를 때 내부적으로 쓰는 평가 함수 — 직접 호출은 서로 다른 배치안을 비교하고 싶을 때만 |
| 대칭쌍 없는 단일 그룹만 그 자체로 정사각형에 packing | `skyline_pack_best_width(blocks, gap=1.0, width_steps=60, target_ratio=1.0)` | `pack_floorplan()`이 내부적으로 대칭쌍 결합에 쓰는 것과 다른 용도 — 대칭쌍이 있으면 이 함수를 각 조각에 독립적으로 쓰지 말 것(높이가 안 맞아 결합 결과가 길쭉해짐, 함수 docstring 참고). 폭 후보 스윕 자체는 `pack_to_height()`와 내부 헬퍼 `_sweep_widths()`를 공유한다 |
| 폭이 주어졌을 때의 순수 skyline packing(저수준) | `skyline_pack(blocks, max_width, gap=1.0)` | 위 두 함수가 내부적으로 쓰는 기본 연산 — 직접 호출은 컨테이너 폭을 이미 알고 있을 때만 |
| 특정 block이 bbox 비율을 지배해 box-shape를 깨뜨리는지 진단 | `evaluate_row_split_candidates(blocks, bbox_width, bbox_height, dominance_ratio=0.6, transistor_sequences=None)` | design-report-spec.md §1.7 — 후보가 있으면 §8.5처럼 그 stack만 다시 `search_stack_finger_w()`/`check_box_shape()`로 재검토하고, finger 수/W가 실제로 바뀌면 §3 사이징 표 + §6 SPICE cross-check까지 재실행할 것(이 함수 자체는 finger 수를 바꾸지 않는다). `transistor_sequences`를 반드시 채워서 호출할 것 — 안 채우면 diffusion 안전성 미확인 상태로 후보만 나온다 |
| row-split 후보가 실제로 MOS diffusion을 깨지 않고 쪼갤 수 있는지 확인 | `find_diffusion_safe_split_points(transistor_sequence)` | **필수, 생략 금지** — 위 함수에 `transistor_sequences`로 넘기면 자동 호출됨. 소자 finger가 인터리브된 행(예: 이 회로의 S1_TAILP, M6:M7 7:3 tail)은 안전한 분할 지점이 하나도 없을 수 있다 — 그 경우 분할을 제안하지 말 것. **주의**: diffusion 안전(이 함수)과 matching 안전(`check_mirror_symmetry()`)은 별개다 — `build_mirror_symmetric_pattern()`으로 만든 행(예: S1_PMOS/S1_NMOS row0/row1)은 diffusion-safe 분할점이 있어도 그 지점에서 자르면 대칭이 깨질 수 있다(PRE-FLIGHT 사고14) — 분할 전 두 검사 모두 확인할 것 |
| box-shape 때문에 한 functional group을 여러 물리 행으로 **처음부터 다시 지을 때**, Euler/box-shape/matching을 순서대로 전부 강제 확인 | `audit_row_split(rows, matching_pairs=None, pair_kinds=None, max_ratio=1.5)` | **필수, 생략 금지 — design-report-spec.md §1.7 3.5단계**(PRE-FLIGHT 사고20: 이 단계를 빼먹어 전류거울 쌍이 두 행에 완전 분리 배치됨). `build_stick_diagram()`(행별 Euler)→`check_box_shape()`→matching(`matching_pairs`마다 3a solo-row/3b interdigitation/3c common-centroid)을 고정 순서로 전부 실행하고 전부 보고한다. **interdigitation과 common-centroid는 서로 다른 성질**이라 반드시 둘 다 계산·보고하지만, **어느 쪽이 pass/fail을 좌우하는 필수 게이트인지는 pair 종류로 갈린다**(stick-diagram-euler-layout.md §2.7 기준): 전류거울(같은 gate 공유)=interdigitation(3b)만 필수, 차동쌍(같은 source 공유+다른 gate)=common-centroid(3c)만 필수, 나머지는 참고정보. `pair_kinds` 없이 부르면 `rows`의 실제 gate/source로 자동 분류(`find_matching_candidates()`와 같은 구조적 신호, W 비교는 불필요) — 애매하면 `pair_kinds`로 수동 override. **전류거울 쌍은 common-centroid dx=1.0이어도 실패가 아니다** — kind별 필수 게이트가 다르므로 모든 쌍에 두 체크를 동일하게 강제하지 말 것. **3번째 kind `branch_symmetric`**(같은 gate 공유 + source/drain 전부 다름 — §2.6 캐스코드 대칭쌍): interdigitation(3b)은 공유 노드가 없어 그래프상 불가능(참고정보로만 표시) — 하지만 **common-centroid(3c)는 diff_pair와 같이 필수 게이트**다. solo(한쪽 행에 통째로 배치)는 최선이 아니다 — 양쪽 행에 swap-대칭으로 분배하면 dy가 크게 개선된다(solo는 dy=1.00으로 FAIL) — solo 여부로 판단하지 말고 항상 실제 dx/dy로 판정할 것 |

---

## 10. Topology JSON 라이브러리 (`assets/stick_diagram.py` §6.9, `assets/sizing_recipe.py` §6.5)

> 정본: `docs/02-design/features/analog-topology-json-library.design.md`. 목적: topology
> netlist가 Python 코드에 하드코딩돼 있으면 새 topology마다 코드를 새로 짜야 하고, agent마다
> 해석이 달라져 sub-block별 stick diagram/floorplan을 통째로 빠뜨리는 등 커버리지 누락이
> 생긴다. `library/*.topology.json`에 **사이징과 무관한 정보만**(연결성 + 대칭성/matching
> kind + 위상보정 함수 참조) 담아 재사용하고, 실제 layout(finger 배분/row 분할/floorplan
> 좌표)은 사이징 이후 오케스트레이션 함수로 계산한다.

⚠️ **`layout` 관련 필드는 topology JSON에 없다** — matching 배치(interdigitation/
common-centroid)·Euler trail·row 분할·floorplan은 전부 finger 개수·finger_w가 정해져야
계산 가능한 사이징 결과값이라 topology 단계엔 존재하지 않는다. `layout` 가이드 필드를 넣지
말 것.

| 상황 | 함수 | 비고 |
|---|---|---|
| `library/*.topology.json`을 읽어 회로 connectivity를 얻음 | `load_topology(json_path) -> tuple[list[Transistor], dict]` | 반환된 `Transistor`는 connectivity만(name/kind/source/drain/gate) — `n_fingers`(기본 1)/`finger_w`/`w`/`stack_id`는 아직 없다. `meta`는 `{"symmetry": {"matching_pairs":...,"dispositions":...}, "compensation": ..., "topology_name": ..., "schema_version": ..., "source": ..., "_linked_files_loaded": [...]}`. **회로가 여러 topology JSON 파일로 쪼개져 있으면**(`linked_topology_files` 필드) 어느 파일을 진입점으로 읽든 형제 파일 전부를 자동으로 합쳐서 반환한다(사고8 재발 방지 — sub-block별로 나눠 매칭 탐지를 돌리면 stage 경계를 넘는 매칭 관계를 놓친다) |
| `symmetry.matching_pairs`를 다 채운 뒤, `find_matching_candidates()`/`find_hub_merge_candidates()`가 찾은 후보 중 빠뜨린 게 없는지 + net 이름 대소문자 자기모순이 없는지 확인 (**필수, 저장 전 생략 금지**) | `check_symmetry_dispositions(transistors, matching_pairs, dispositions=None) -> SymmetryDispositionsVerdict` | `run_full_circuit_audit()` 2번+3번 체크(net-name case consistency + "모든 후보에 disposition 기록")와 같은 원리를 topology-authoring 단계용으로 경량화한 것. **0번(먼저 실행): net 이름 대소문자 스캔** — `Vbias1`/`vbias1`처럼 표기만 다른 같은 net이 있으면 그 자체로 `ok=False`(사고9 재발 방지 — `linked_topology_files`로 여러 파일을 합칠 때 특히 위험). 대소문자가 꼬이면 후보 탐지 자체가 신뢰 불가하므로 자동 소문자 통일 없이 반드시 사람이 원본을 고치게 한다. **1번: 후보마다**(`current_mirror`/`diff_pair`/`hub_merge` 세 tag 전부 — `hub_merge` 누락은 사고1과 같은 종류) (a) `matching_pairs`에 채택되거나 (b) `dispositions`(`{(tag,kind,key):(category,reason)}`, topology JSON에선 `symmetry.dispositions` 리스트로 저장)에 기각 사유가 있어야 `ok=True`. **3개 이상 소자를 묶는 후보는 `matching_pairs` 항목 하나로 전부 기록할 것** — pairwise로 쪼개면 부분집합 검사가 실패해 UNDISPOSED로 남는다. `hub_merge` 후보는 공급 레일(vdd/gnd) 공유만으로도 넓게 잡히는 경우가 많다 — 그 자체는 병합 배치 후보가 아니므로 `false_positive_shared_supply_rail`/`false_positive_cascode_stack_node` 같은 category로 기각 기록할 것. 반환에 `case_collisions`/`undisposed` 둘 다 포함 |
| 사이징이 끝난 뒤 실제 layout(box-shape/matching-safety/floorplan/coverage)을 계산 | `run_topology_pipeline(topology_json_path, sizing_overrides, floorplan_hints=None) -> dict` | `sizing_overrides`(소자별 n_fingers/finger_w/w/stack_id — **필수**)로 connectivity를 채운 뒤 `split_into_stacks()`→`check_box_shape()`→`audit_row_split()`(matching kind는 `symmetry`에서)→`pack_floorplan_grouped()`→`check_stick_diagram_coverage()`를 design-report-spec.md §1.6/§1.7 순서 그대로 호출. **row 분할을 자동 탐색하지 않는다** — `audit_row_split` FAIL이면 `search_stack_finger_w()`/`common_centroid_layout()`로 새 배분을 찾아 `sizing_overrides`를 조정해 재호출할 것(이 문서 §6의 기존 피드백 루프와 동일 패턴). `run_full_circuit_audit()`는 `dispositions` 판단이 필요해 의도적으로 미포함 — 완전한 감사가 필요하면 이 문서 §8의 그 함수를 별도로 호출. **`sizing_overrides`가 topology의 소자 하나라도 빠뜨리면 즉시 `ValueError`** — 빠뜨린 소자를 `n_fingers=1`/`stack_id=None` 기본값+`(kind,"unspecified")` 폴백 그룹으로 조용히 흡수하면 `check_stick_diagram_coverage()`도 못 잡는 사고27과 같은 유형이 된다 |
| 위 파이프라인 결과를 instance-output JSON으로 저장 | `save_instance_json(path, topology_json_path, sizing_results, pipeline_result)` | `pipeline_result`를 손대지 않고 그대로 옮겨 씀(§1 표 5번 원칙). 저장되는 최상위 키: `sizing`/`netlist`(최종 Transistor 전체)/`floorplan`/`box_shape`/`audit_row_split`/`coverage` |
| instance-output JSON(또는 별도 spec JSON)에서 gm/ID sizing 목표를 읽음 | `load_sizing_targets(json_path) -> dict` (`sizing_recipe.py`) | `design_spec` 키가 있으면 그 안쪽을, 없으면 파일 전체를 반환(단순 스펙 JSON도 지원) |
| 사이징 결과를 instance-output JSON에 기록 | `write_sizing_results(json_path, results: dict[str, SizingResult])` (`sizing_recipe.py`) | `sizing` 섹션에 병합해 씀(파일 없으면 새로 생성, 다른 섹션은 안 건드림) |
| topology JSON의 `compensation` 참조로 위상보정 함수를 안전하게 호출 | `run_sizing_pipeline(topology_json_path, design_spec: dict)` (`sizing_recipe.py`) | `compensation.function`을 `_COMPENSATION_REGISTRY`(명시적 allowlist — `miller_ota_topology`/`nmcnr_3stage_topology`/`ngcc_3stage_topology`만 등록, `eval`/`getattr(module, name)` 금지)로 조회. **반환 타입이 갈린다**: `compensation` 있으면 그 함수가 반환하는 `topology_fn(prev_cggs) -> list[gm_i]` 클로저를 그대로 반환(`optimize_multistage()`에 넘길 것), `compensation`이 `null`이면 `design_spec` dict를 그대로 반환(`size_transistor()`를 직접 쓸 것). allowlist에 없는 함수명은 `ValueError` |

**새 topology를 논문/스펙에서 처음 만들 때**: `library/_TEMPLATE.topology.json`을 복사해
시작(3개 섹션 — `netlist`/`symmetry`/`compensation` — 빈 구조 + 필드별 인라인 주석). 절차는
Design 문서 §4.5 참고 — netlist는 원문 직접 확인(상상 금지), symmetry는
`find_matching_candidates()` 실제 호출 후 5가지 패턴으로 필터링, compensation은 회로
**구조**가 기존 3개 함수 중 하나와 일치하는지(현재 W값의 역산 여부가 아니라)로 판단.

---

## 이 문서 자체의 사용 원칙

- 이 표에 상황이 없으면 **먼저 실제 코드(docstring 포함)를 읽어 해당 함수가 있는지 확인**한다 —
  없다고 판단하기 전에 `grep -n "^def " assets/*.py`로 전체 함수 목록을 직접 확인할 것(추측 금지).
- 정말 필요한 계산 함수가 없으면(§2의 NGCC 보상소자처럼), **SKILL.md §1.5 규칙에 따라
  스킵하지 않고** `topology-fn-derivation-guide.md`의 패턴대로 새로 추가한 뒤 이 표도 갱신한다.
