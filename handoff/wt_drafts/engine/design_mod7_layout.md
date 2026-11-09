# MOD7 레이아웃 설계 (`gmid_engine/layout/`) + MOD8 W_request 루프 계약

- 상태: 설계 문서(코드 없음). 작성 2026-10-07.
- 근거(정본 인용 기호): **UD** = `_drafts/user_decisions.md` 120~128행(2026-10-07 레이아웃 규칙·패턴 함수 재사용·차동쌍 완화 순서·W 허용오차·파일 규칙 A~D·graph 단일 정본), **R** = `_drafts/engine/ROADMAP.md` 끝 '정정' 절 1~8(317~331행), **LP** = `_drafts/engine/layout_pipeline_analysis.md` §2~§5, **NR** = `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(1.2 규칙 A~D, 1.3 상수 금지, 1.5 결정론, 2.2 레이아웃 반영, 3.1 `layout` 행, 3.3 계약, 4.1 캐시 표, 6절 E5), **P** = 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(N3.6 438~441행 K_max, LR8·LR9 512~513행).
- 옛 소스: **SD** = `chip-design-skills/skills/analog-gmid-design/legacy/stick_diagram.py`(9,010행, HEAD a21a24f, 마지막 변경 60727b0 = 내용 변경 없는 이동). 행 번호는 이 파일 기준(LP의 행 번호는 gmid-light cb0ef86 기준이라 수 행 다르다).
- 원문: **PDF** = F. Maloberti, *Layout of Analog CMOS IC* Part 2(`Layout02.pdf`, 38쪽). 위치·대조 결과는 7절.

- **[2026-10-07 개정 -- reference 검토 Q4·Q6·Q8 추천안 확정, 사용자 "B는 추천대로 해."]** 계획 worktree `plan-rev4` 커밋 `defdc24`: N3.17 LY1·LY2·LY4·LY5·LY7 개정, LY8~LY11 신설, DEC-89(보존량·재평가·SPICE 기하), DEC-91(확산 기하), DEC-93(matching 분류·접기·면적·hub 병합). 아래 [개정 Q*] 표시. 레이아웃 계약 문서(`gmid_engine/layout/CONTRACT.md`)는 이 문서가 고치지 않는다(담당 작업이 개정).

## 0. 확정 규칙 요약 (이 문서가 구현하는 것)

| # | 규칙 | 출처 |
|---|---|---|
| L1 | **[개정 Q4]** (ID, gm/ID, L) 보존(옛 '총 W 보존' 대체). 실현 W 목표 `W_need(fw) = ID / J_slice(kind, fw, gm/ID, L, VDS, VSB)`(폭 슬라이스 전류밀도, `ly.fw_cand` 키에서 1회). 허용 상한 `abs(dW/W) <= tol_V x (gm/ID)`(tol_V = `id_equivalent` 셀값), 실현 하한 `MANUFACTURINGGRID / (2 x finger_w)`, **실효 = max(상한, 하한)**, 하한 > 상한이면 '격자 지배' 기록. 허용오차는 후보 순위 기준이고 전기 타당성은 L13 재평가가 판정 | UD 123, R 8, P LY1, DEC-89 |
| L2 | W 변경은 레이아웃이 적용하지 않고 `W_request`로 MOD8에 반환 → sizing 재평가 | UD 125, R 4 |
| L3 | 패턴 선택은 행 구성 단계(수리 단계 아님). 패턴표 경로 우선 -- `interdigitate_layout`에 `base`를 넘겨 표 경로 실사용 | UD 121·125, R 6, LP §5 (c)5 |
| L4 | 차동쌍 = common-centroid 우선. 순서 (i) 같은 (ID, gm/ID, L)에서 finger_w·nf 조정 (ii) W_request(모든 차동쌍이 시도 -- `W_adjustable` 사전 분류 폐기, 판정은 MOD8) (iii) 둘 다 불가일 때만 interdigitation 완화 + 시도 기록. **[개정 Q8 (iv)]** 완화된 차동쌍은 결과 맨 앞 `review_needed` + dx·dy(pitch 단위) + 근본 원인 | UD 122, R 7, P LY5 |
| L5 | 그 밖의 matching 그룹 = common-centroid 또는 interdigitation 중 box·면적·residual로 선택. **[개정 Q8 (ii)]** 전류거울은 정렬 키 첫째 = interdigitation 성립. `branch_symmetric`(캐스코드 대칭쌍, 공유 hub 없음)은 두 행 swap 분배 common-centroid만, 실패 시 L4와 같은 완화 순서. 멤버 L이 다르면 `matching_L_mismatch` 기록 | UD 120, R 2, P LY4 |
| L6 | 행별 finger_w. seed 행 단위폭 전파 금지, 단위셀 폴백(SD 6085~6097) 삭제 | LP §5 (c)1·6, UD 125 |
| L7 | 수리·판정 루프는 전 그룹 판정(첫 실패에서 멈추지 않음) | LP §5 (c)4, UD 125 |
| L8 | matching 그룹 = MOD3 구조 유도 출력 레코드(`graph/matching_groups.py`), 선언 태그 아님 | R 2, NR 3.1 |
| L9 | finger_w 후보 = PDK 특성화 폭(DC 슬라이스) 집합(E5 (a)), 필요 시 (b) 1회 특성화 + 디스크 캐시. 무보정 임의 폭 금지 | UD 128, NR 6절 E5 |
| L10 | 패턴 함수는 legacy import가 아니라 본문 복사 + 함수별 AST 해시 대조 | 작업 지시(설계 요건 확정), NR 2.2 |
| L11 | 결과는 graph 레이아웃 필드로만, 필드마다 writer 1개 + 입력 버전(필드 = 캐시) | UD 128, NR 7절 1 |
| L12 | **[개정 Q8 (i)(iii)]** 레이아웃이 받는 matching 그룹 = role `diff_pair`·`mirror`·`branch_symmetric`의 derived·ratified만. `bias_distribution`·`feedback_shared`는 MOD3 `matching_dispositions[]`(레이아웃 matching 밖) | P DEC-93 (1), LY4 |
| L13 | **[개정 Q4 (ii)(iii)]** MOD7 결과마다(W_request 유무 무관) 실현 기하로 평가 커널 1회 + 봉인 1~8 후 freeze. diode는 ID 재보정만 불필요, 노드전압·봉인은 재계산 | P LY2·LY7, DEC-89 |
| L14 | **[개정 Q4 (v)·Q6 (ii)]** `ly.diffusion[dev]` = Euler 행 공유 확산 통계(내부 공유·끝 확산) → 엔진 `ss` 접합 용량과 오라클 소자별 ad/as/pd/ps에 같은 값. SPICE 합격 기하 = MOD8 수렴 스냅샷 | P LY8, DEC-89·91 |
| L15 | **[개정 Q8 (v)(vi)(vii)]** box 하드 게이트 없음(spec 허용 비 선언 없음) -- box 개선 목적 = 판정 축 면적(floorplan 외곽 + 행 끝 dummy 2·그룹 경계 tap·body 다른 그룹 사이 well 간격, PDK 규칙 번호 선언), 행 폭 비·packing 밀도는 기록. 행 접기는 matching 그룹 없는 행만 자동, matching 행은 패턴 함수로 n_rows = k 재구성, 접은 뒤 Euler + matching 감사 재실행·악화 시 거부 | P LY9·LY10, DEC-93 (3)~(5) |
| L16 | **[개정 Q8 (viii)(ix)]** stage를 넘는 hub 병합 = 판정 축 면적 비교로 채택, 노이즈 결합 우려는 `merge_decisions[]` 기록만. 복사 floorplan 리터럴이 A_L을 ΔA_tie 이상 바꾸면 본문 수정 승인 재질의(그 전엔 민감도 test 기록) | P LY11, DEC-93 (6)(7) |

## 1. MOD7 파일 목록 (규칙 A~D)

규칙(UD 127): (A) 파일당 독립 진입점 1 (B) 비공개 helper는 자기 파일만, 공유 helper는 `_helpers_*.py`(kind="helper") (C) 캐시 계산 블록 1 = 파일 1 (D) test 1:1 `tests/layout/test_<file>.py`. 층 번호 오름차순 import만(같은 층끼리 import 금지 -- 그래서 `crossover`(3) < `_helpers_hubleaf`(4) < 두 패턴 파일(5) 순으로 층을 둔다).

| 파일(층) | 독립 진입점 | 계산 블록(필드) | 출처 | 비고 |
|---|---|---|---|---|
| `contract_input.py`(0) | `LayoutInput`(frozen) | -- | 새 | NR 3.3 계약 0.2. 리터럴 없음 |
| `contract_output.py`(0) | `LayoutResult`(frozen) | -- | 새 | 소자·그룹·행·box·floorplan·`W_requests`·`attempts` |
| `transistor.py`(0) | `Transistor` | -- | 복사 | SD 48~78 |
| `_copy_manifest.py`(0, kind="data") | 없음(표) | -- | 새 | 복사 함수별 (새 파일, 이름, SD 행, `sha256(ast.dump)`) |
| `w_tolerance.py`(1) | `w_tolerance(gm_id, tol_v, finger_w, grid)` | -- | 새 | L1 두 식 + 실효 max·'격자 지배'. 입력은 `lut.tol_v`(**[개정 Q4 (iv)]** 지표가 `id_equivalent`로 타입된 조회만 -- gm/ID 역산 지표 입력은 거부), `core.pdk_decl` |
| `finger_candidates.py`(1) | `finger_w_candidates(kind, ID, gm_id, L, VDS, VSB, nf_min, slices, grid)` | `ly.fw_cand[kind, ID, gm_id, L, VDS, VSB]` | 새 | L9. **[개정 Q4 (i)]** 슬라이스 폭 fw마다 W_need(fw) = ID/J_slice, 후보마다 (nf, finger_w, W_need, err, lower, upper, 격자 지배) |
| `diffusion_stats.py`(층 미정) | `diffusion_stats(rows)` | `ly.diffusion[dev]` | 새 | **[개정 Q6]** L14 -- 행 Euler 결과에서 소자별 내부 공유·끝 확산 → ad/as/pd/ps(확산 연장 길이는 PDK 선언) |
| `match_audit.py`(층 미정) | `match_audit(rows, groups)` | `ly.match[gid]` | 새 | **[개정 Q8 (v)]** L15 재판정(3b `_count_isolated_pairs`·3c `_common_centroid_residual` 재사용, dx·dy·대칭) |
| `pattern_branch_symmetric.py`(5) | `branch_symmetric_layout` | -- | 새 | **[개정 Q8 (ii)]** 두 행 swap 분배 CC + dx·dy residual(손계산 test) |
| `hub_merge.py`(층 미정) | `hub_merge_decisions` | `ly.merge` | 새(옛 `find_hub_merge_candidates` 복사 여부는 별도 확인) | **[개정 Q8 (viii)]** L16 |
| `euler_graph.py`(1) | `build_graph` | -- | 복사 | SD 5194~5199 `StackGraph`, 5202~5258 |
| `euler_condition.py`(2) | `check_euler_condition` | -- | 복사 | SD 5261~5262, 5265~5277, 5281~5286, 5289~5317 |
| `euler_trail.py`(2) | `hierholzer` | -- | 복사 | SD 5324~5352 |
| `crossover.py`(3) | `find_min_crossover_layout` | -- | 복사 | SD 5364~5715(helper 8개 + `_MAX_CROSSOVER_PAIRING_NODES` 5556) |
| `_helpers_hubleaf.py`(4, helper) | 없음 | -- | 복사 | SD 265~290, 676~683, 686~717, 720~742, 745~784, 787~814, 817~836 (두 패턴 파일 공용) |
| `patterns_interdigitate.py`(5) | `interdigitate_layout` | -- | 복사 | SD 94~103 표, 130~161, 164~207 |
| `patterns_common_centroid.py`(5) | `common_centroid_layout` | -- | 복사 | SD 110~127 표, 293~342, 345~376, 379~510, 513~536, 539~637, 640~658, 661~673, 839~904 |
| `mirror_trail.py`(4) | `mirror_symmetric_trail` | -- | 복사 | SD 210~230, 6451~6456, 6459~6552, 6555, 6558~6648 |
| `row_fold.py`(1) | `apply_explicit_row_split` | -- | 복사 | SD 6115~6157(box용 행 접기, 총 W 보존) |
| `coverage.py`(1) | `check_stick_diagram_coverage` | -- | 복사 | SD 6914~6916, 6919~6955 |
| `floorplan_pack.py`(2) | `pack_floorplan_grouped` | -- | 복사 | SD 7705~8126, 8225~8385 (`block_from_rows` 8129·`rebuild_floorplan` 8144 제외) |
| `canonical_rows.py`(6) | `canonical_row(seq_result, members)` | -- | 새 | 7절 결정론 결함 보정(node_sequence 시작점을 정렬 규칙으로 재유도) |
| `row_euler.py`(7) | `row_euler(row)` | `ly.row[rid]` | 새 | 패턴 결과 검산(`check_walk_sequence`) 또는 graph+Euler, 막히면 crossover(W 불변) |
| `pattern_select.py`(7) | `place_group(group, devices, pdk)` | `ly.group[gid]` | 새 | L3·L4·L5·L7, 시도 기록 |
| `finger_geometry.py`(7) | `assign_row_fingers(row_group, placements)` | `ly.finger[dev]` | 새 | L6. 행 안 finger_w 공통, 행끼리 독립 |
| `box_shape.py`(7) | `box_verdict(rows, pdk, criterion)` | `ly.box` | 새 | 아래 2.3 -- SD `check_box_shape`는 복사하지 않음 |
| `rows.py`(8) | `compose_rows(layout_input)` | `ly.rows` | 새 | 행 그룹 → 그룹 배치 → finger → 행 Euler → box(→ `row_fold`) |
| `floorplan.py`(9) | `build_floorplan(rows, row_euler_fields, pdk)` | `ly.floorplan` | 새 | Euler 재계산 없음(SD 8212 `build_stick_diagram` 재호출 제거) |
| `run.py`(10) | `run_layout(layout_input)` | -- | 새 | `__all__` = `LayoutInput`, `LayoutResult`, `run_layout` |

- **[개정 Q4·Q6·Q8]** 새 파일 4개(`diffusion_stats`·`match_audit`·`pattern_branch_symmetric`·`hub_merge`)의 층 번호는 호출 방향(`rows`·`floorplan`·`run` 중 누가 부르는지)을 구현 때 AST로 확인해 정한다(같은 층 import 금지 규칙).
- 규칙 A 확인(설계 시 AST 실측, SD 호출 그래프): 복사 묶음의 뿌리는 각 1개다 -- `interdigitate_layout`·`common_centroid_layout`은 서로 부르지 않아 한 파일에 두면 뿌리 2개(A FAIL)라 두 파일로 나눴고, 공용 helper 7개는 `_helpers_hubleaf.py`로 뺐다. `build_graph`·`check_euler_condition`·`hierholzer`도 서로 부르지 않아 세 파일. `floorplan_pack.py`는 `pack_floorplan_grouped`에서 나머지 14개 정의가 모두 도달.
- 복사 파일의 모듈 import는 SD 34~40행 중 필요한 것만(`Counter`, `defaultdict`, `math`, `itertools`, `dataclass`, `field`, `replace as _dc_replace`) -- 함수 본문이 쓰는 전역 이름이 그대로 풀리도록 같은 별칭을 쓴다.
- 복사하지 않는 SD 함수와 이유: `assign_finger_geometry`(6017)·`search_unit_cell_sizing`(5879) = L6 위반 원천, `search_stack_finger_w`(5928)·`search_shared_finger_w`(6179) = 정수배·고정 오차(`max_snap_error=0.01`) 정책이 L1·L9와 다름, `select_layout_tool`(6973)·`audit_row_split`(7004)·`repair_matching_safety`(7508)·`_branch_composite_pair`(7310) = 선언 축C·2-tuple 펼침(L8 위반), `check_finger_width_compatibility`(5157) = 정확한 정수배 요구(L1이 대체), `check_box_shape`(6333)·`compute_row_geometry`(6279)·`pitch`(6258) = `PROCESS_GEOMETRY` 0.0·`row_width_tol=1.5` 리터럴(WP-03), `rebuild_floorplan`(8144) = Euler 재계산 + gap 0.05·`"nmos"` 기본값, `_layout_result_to_rows`(7244) = `_repair{i}` 이름 규칙(새 행 이름은 그룹 id 기반으로 `rows.py`가 정함).

### 1.1 복사 정의 전수표 (SD 행, 정의마다 AST 해시 1개)

닫힘 확인: 아래 정의들이 참조하는 SD 최상위 이름은 모두 이 표 안에 있다(설계 시 AST 호출 그래프로 확인, 밖 참조 0).

| 새 파일 | 정의 | SD 행 | 참조하는 SD 이름 |
|---|---|---|---|
| `transistor.py` | `Transistor` | 48~78 | -- |
| `euler_graph.py` | `StackGraph` | 5194~5199 | -- |
| `euler_graph.py` | `build_graph` | 5202~5258 | `StackGraph`, `Transistor` |
| `euler_condition.py` | `_degrees` | 5261~5262 | `StackGraph` |
| `euler_condition.py` | `_is_connected_ignoring_isolated` | 5265~5277 | `StackGraph` |
| `euler_condition.py` | `EulerVerdict` | 5281~5286 | -- |
| `euler_condition.py` | `check_euler_condition` | 5289~5317 | `EulerVerdict`, `StackGraph`, `_degrees`, `_is_connected_ignoring_isolated` |
| `euler_trail.py` | `hierholzer` | 5324~5352 | `StackGraph` |
| `crossover.py` | `_mirror_node_map_from_pairs` | 5364~5403 | -- |
| `crossover.py` | `_pair_odd_nodes_by_mirror` | 5406~5447 | -- |
| `crossover.py` | `_build_crossover_segments` | 5450~5496 | `build_graph`, `check_euler_condition`, `hierholzer` |
| `crossover.py` | `_count_matching_pair_splits` | 5499~5546 | -- |
| `crossover.py` | `_is_perfect_crossover_score` | 5549~5553 | -- |
| `crossover.py` | `_MAX_CROSSOVER_PAIRING_NODES` | 5556~5556 | `_MAX_CROSSOVER_PAIRING_NODES` |
| `crossover.py` | `_enumerate_perfect_matchings` | 5560~5570 | -- |
| `crossover.py` | `_select_crossover_pairing` | 5573~5618 | `_MAX_CROSSOVER_PAIRING_NODES`, `_build_crossover_segments`, `_count_matching_pair_splits`, `_enumerate_perfect_matchings`, `_is_perfect_crossover_score`, `_pair_odd_nodes_by_mirror` |
| `crossover.py` | `find_min_crossover_layout` | 5621~5715 | `_build_crossover_segments`, `_mirror_node_map_from_pairs`, `_select_crossover_pairing`, `build_graph`, `check_euler_condition`, `hierholzer` |
| `_helpers_hubleaf.py` | `_hubleaf_sequence_node_path` | 265~290 | -- |
| `_helpers_hubleaf.py` | `_row_feasible` | 676~683 | `Transistor`, `build_graph`, `check_euler_condition` |
| `_helpers_hubleaf.py` | `_repair_row_parity` | 686~717 | `_row_feasible` |
| `_helpers_hubleaf.py` | `_build_rows_from_shares` | 720~742 | `Transistor`, `build_graph`, `check_euler_condition`, `hierholzer` |
| `_helpers_hubleaf.py` | `_build_rows_from_shares_with_crossover` | 745~784 | `Transistor`, `build_graph`, `check_euler_condition`, `find_min_crossover_layout`, `hierholzer` |
| `_helpers_hubleaf.py` | `_common_centroid_residual` | 787~814 | -- |
| `_helpers_hubleaf.py` | `_count_isolated_pairs` | 817~836 | -- |
| `patterns_interdigitate.py` | `INTERDIGITATION_PATTERNS` | 94~103 | `INTERDIGITATION_PATTERNS` |
| `patterns_interdigitate.py` | `_try_interdigitation_table_match` | 130~161 | `INTERDIGITATION_PATTERNS`, `_hubleaf_sequence_node_path` |
| `patterns_interdigitate.py` | `interdigitate_layout` | 164~207 | `_build_rows_from_shares`, `_build_rows_from_shares_with_crossover`, `_common_centroid_residual`, `_count_isolated_pairs`, `_repair_row_parity`, `_try_interdigitation_table_match` |
| `patterns_common_centroid.py` | `COMMON_CENTROID_PATTERNS` | 110~127 | `COMMON_CENTROID_PATTERNS` |
| `patterns_common_centroid.py` | `_common_centroid_from_pattern_table` | 293~342 | `COMMON_CENTROID_PATTERNS`, `_hubleaf_sequence_node_path` |
| `patterns_common_centroid.py` | `_try_pattern_table_match` | 345~376 | `COMMON_CENTROID_PATTERNS`, `_common_centroid_from_pattern_table` |
| `patterns_common_centroid.py` | `common_centroid_layout` | 379~510 | `_common_centroid_nway_exact`, `_common_centroid_nway_search`, `_try_pattern_table_match` |
| `patterns_common_centroid.py` | `_fix_block_parity` | 513~536 | -- |
| `patterns_common_centroid.py` | `_common_centroid_nway_exact` | 539~637 | `Transistor`, `_fix_block_parity`, `build_graph`, `check_euler_condition`, `find_min_crossover_layout`, `hierholzer` |
| `patterns_common_centroid.py` | `_proportional_round_robin` | 640~658 | -- |
| `patterns_common_centroid.py` | `_slice_into_rows` | 661~673 | -- |
| `patterns_common_centroid.py` | `_common_centroid_nway_search` | 839~904 | `_build_rows_from_shares`, `_build_rows_from_shares_with_crossover`, `_common_centroid_residual`, `_count_isolated_pairs`, `_proportional_round_robin`, `_repair_row_parity`, `_slice_into_rows` |
| `mirror_trail.py` | `build_mirror_symmetric_pattern` | 210~230 | -- |
| `mirror_trail.py` | `WalkVerdict` | 6451~6456 | -- |
| `mirror_trail.py` | `check_walk_sequence` | 6459~6552 | `WalkVerdict` |
| `mirror_trail.py` | `_MAX_MIRROR_TRAIL_COMBO_PAIRS` | 6555~6555 | `_MAX_MIRROR_TRAIL_COMBO_PAIRS` |
| `mirror_trail.py` | `mirror_symmetric_trail` | 6558~6648 | `Transistor`, `_MAX_MIRROR_TRAIL_COMBO_PAIRS`, `build_graph`, `build_mirror_symmetric_pattern`, `check_euler_condition`, `check_walk_sequence`, `hierholzer` |
| `row_fold.py` | `apply_explicit_row_split` | 6115~6157 | -- |
| `coverage.py` | `CoverageVerdict` | 6914~6916 | -- |
| `coverage.py` | `check_stick_diagram_coverage` | 6919~6955 | `CoverageVerdict` |
| `floorplan_pack.py` | `FloorplanBlock` | 7705~7711 | -- |
| `floorplan_pack.py` | `PlacedBlock` | 7715~7720 | -- |
| `floorplan_pack.py` | `FloorplanResult` | 7724~7732 | -- |
| `floorplan_pack.py` | `_block_center` | 7735~7736 | -- |
| `floorplan_pack.py` | `_total_wire_cost` | 7739~7766 | `_block_center` |
| `floorplan_pack.py` | `skyline_pack` | 7769~7851 | `PlacedBlock`, `_block_center` |
| `floorplan_pack.py` | `_sweep_widths` | 7854~7874 | `skyline_pack` |
| `floorplan_pack.py` | `skyline_pack_best_width` | 7877~7901 | `_sweep_widths` |
| `floorplan_pack.py` | `pack_to_height` | 7904~7939 | `_sweep_widths`, `_total_wire_cost`, `skyline_pack` |
| `floorplan_pack.py` | `find_diffusion_safe_split_points` | 7942~7963 | -- |
| `floorplan_pack.py` | `evaluate_row_split_candidates` | 7966~8014 | `find_diffusion_safe_split_points` |
| `floorplan_pack.py` | `pack_floorplan` | 8017~8126 | `FloorplanBlock`, `FloorplanResult`, `PlacedBlock`, `evaluate_row_split_candidates`, `pack_to_height` |
| `floorplan_pack.py` | `_pack_by_subkind` | 8225~8261 | `FloorplanBlock`, `PlacedBlock`, `pack_to_height` |
| `floorplan_pack.py` | `pack_group_as_unit` | 8264~8332 | `FloorplanBlock`, `PlacedBlock`, `_pack_by_subkind`, `skyline_pack_best_width` |
| `floorplan_pack.py` | `pack_floorplan_grouped` | 8335~8385 | `FloorplanResult`, `PlacedBlock`, `pack_floorplan`, `pack_group_as_unit` |

## 2. 복사 함수의 입력 인터페이스 변경 (함수 본문은 그대로, 호출 측 어댑터가 바꿈)

| 함수 | SD 호출 방식 | 새 호출 방식(어댑터 = 호출 파일) |
|---|---|---|
| `interdigitate_layout(transistors, base, repeat)` | 늘 `base=None`(LP §2: 39회 전부 `search`) | `pattern_select.py`가 표에서 `base`를 고른다: 글자 종류 수 = 멤버 수이고, 어떤 repeat의 글자별 개수가 멤버 nf와 정확히 같은 base만. 멤버↔글자 대응은 nf 내림차순 정렬 + 이름 정렬(결정론). 맞는 base가 없으면 `base=None`(탐색 경로) + `method` 기록 |
| `common_centroid_layout(transistors, n_rows, max_candidates)` | `n_rows` 혼용, `max_candidates=24` 기본 | 멤버 nf 같음 → `n_rows=None`(회전 exact, 전제 nf >= 멤버 수 -- 미만이면 SD 556~561 `ValueError`이므로 호출 전 후보에서 제외). 2멤버 nf 다름 → `n_rows=2`(표 경로 SD 496~508). `max_candidates` = 그룹 총 finger 수(SD 871 `min(max_candidates, total)`에서 전 phase 시도 -- 리터럴 없음) |
| `mirror_symmetric_trail(group, matching_pairs)` | topology 선언 `matching_pairs` 2-tuple | 행 안 matching 그룹 레코드에서 같은 그룹 멤버 조합으로 만든 쌍(구조 유도) |
| `find_min_crossover_layout(transistors, matching_pairs, pair_sensitivity)` | 선언 쌍 + 선언 `matching_sensitivity` | 쌍 = 위와 같음, `pair_sensitivity` = 그룹 `role == diff_pair` → `"offset"`, 나머지 → `"ratio"`(SD 5499~5546 계약 그대로) |
| `apply_explicit_row_split(rows, row_split)` | 호출자 선언 `row_split` | `rows.py`의 box 개선 루프가 행마다 n_rows 후보를 만든다(아래 3단계 6) |
| `pack_floorplan_grouped(spine_groups, mirror_pairs, gap, ...)` | gap = 중앙 폭 x 0.05, kind별 super-block | `spine_groups` = 행 그룹의 (kind, body 넷)(LR8), `mirror_pairs` = matching 그룹, `gap` = PDK 간격 규칙(`core.pdk_decl`). `height_steps` 등 탐색 해상도 기본값은 그대로(아래 2.2) |
| `check_stick_diagram_coverage(sized, rows)` | repair 전후 이름 집합 | MOD8 매 반복(LR9) + `run_layout` 끝 |

### 2.1 AST 해시 대조 (L10)
- `_copy_manifest.py`에 함수·클래스·표마다 `sha256(ast.dump(node, annotate_fields=True, include_attributes=False))`를 SD 기준으로 기록(복사 card에서 1회 계산, 계산자 ≠ 복사자).
- `tests/structure/test_copied_ast_hash.py`: 새 파일의 같은 이름 정의를 파싱해 해시 일치. SD 파일이 저장소에 있으면 SD에서도 다시 계산해 3자 일치(옛 엔진 삭제 뒤에는 manifest와 새 파일 2자).
- docstring도 AST에 들어가므로 docstring까지 그대로 복사한다(문서 안의 '이미지에서 옮긴 표' 주석 정정은 7절 결과를 새 파일 머리 주석(정의 밖)에만 적는다).

### 2.2 복사본이 끌고 오는 리터럴 (NR 1.3 `test_numeric_literals_derived`와의 충돌)
- 복사 본문 안 리터럴: `max_iters=50`(SD 686), `max_candidates=24`(379), `_MAX_CROSSOVER_PAIRING_NODES=8`(5556), `_MAX_MIRROR_TRAIL_COMBO_PAIRS=12`(6555), `pack_*`의 `gap=1.0`·`height_steps=40`·`width_steps=60`·`height_tolerance=1.0`·`width_tolerance=2.0`.
- 기본안(원칙 WP-03 + L10에서): (a) 호출 측이 인자로 넘길 수 있는 것은 유도값을 넘긴다(`max_candidates`, `gap`) (b) 본문 내부 탐색 상한(`max_iters`, 두 `_MAX_*`, steps)은 결과 판정이 아니라 탐색 폭이라 복사본 그대로 두고, lint 예외를 `_copy_manifest.py` 등록 정의로 한정 + 예외 리터럴 집합을 test로 고정(새 리터럴 유입 0).

### 2.3 box 판정을 새로 쓰는 이유
SD `check_box_shape`는 `compute_row_geometry`→`pitch`(SD 6258, `PROCESS_GEOMETRY["finger_pitch_overhead_m"]=0.0` 6254)를 전역으로 읽는다. 복사하면 PDK 값을 넣을 길이 숨은 전역뿐이다. 새 `box_verdict`는 같은 정의(행 폭 비 = max/min, elongation)를 쓰되 pitch 여유 = PDK 선언(poly 간격 규칙). **[개정 Q8 (vi) (나)]** 허용 비 선언은 두지 않는다(옛 안 '사람 선언 필수, 없으면 로드 거부'는 9회로 전부 거부가 되어 폐기). `box_verdict`는 행 폭 비·packing 밀도를 **기록만** 하고, box 개선의 목적함수는 판정 축 면적(L15)이다. test는 overhead 0 입력에서 SD `check_box_shape`와 같은 행 폭 비 값(대조).

## 3. 행 구성 알고리즘 (`rows.compose_rows`)

입력: `LayoutInput`(소자별 `ID`, `gm_id`, `L_m`, `VDS`, `VSB`, sizing 기준 `W_m`(참고), kind·d·g·s·b, `self_biased_diode`; `matching_groups`(role·증거·status, L12); `row_groups`; PDK 격자·최소 finger 폭·슬라이스 폭 집합·dummy/tap/well 규칙; `tol_v` 조회(`id_equivalent`)). **[개정 Q4]** `W_adjustable`은 계약에서 뺀다(모든 W_request는 MOD8 재평가가 판정).

1. **행 그룹**: `row_groups`(MOD3 기둥 + matching 그룹에서 유도, (kind, body 넷)으로 먼저 분리 -- LR8). 같은 matching 그룹 레코드를 병합과 판정에 같이 쓴다(LP §2: 병합은 forced, 감사는 전체였던 불일치 제거).
2. **그룹 패턴 선택**(`pattern_select.place_group`, 그룹마다 독립, 전 그룹 순회):
   - (a) 멤버별 nf·finger_w 후보 = `finger_w_candidates`(L9): **[개정 Q4]** 슬라이스 폭 fw마다 W_need(fw) = ID/J_slice(fw), nf = W_need/fw를 정수로(내림·올림 둘), err = |nf·fw − W_need|/W_need, 하한 = grid/(2·fw), 상한 = tol_V·gm/ID, 실효 = max(상한, 하한). err <= 실효인 후보만(하한 > 상한이면 '격자 지배' 표시). 매칭 멤버는 같은 finger_w(같은 unit geometry, R 2).
   - (b) 패턴 후보: `role == diff_pair` → common-centroid만 먼저. **[개정 Q8]** `role == branch_symmetric` → `branch_symmetric_layout`(두 행 swap CC)만. `role == mirror` → 둘 다, 정렬 키 첫째 = interdigitation 성립. 그 밖 → common-centroid와 interdigitation 둘 다. common-centroid 후보는 nf >= 멤버 수(회전 전제) 또는 2멤버 표 경로 개수.
   - (c) 각 (nf 조합, 패턴)에 복사 함수 호출 → `method`(pattern_table|rotation_exact|search), `residual`, `crossover_count`, `isolated_pairs` 기록. 정렬 키(사전식): (method가 표·회전이면 0, 아니면 1, crossover_count, isolated_pairs, residual, 행 폭 합 = Σnf·pitch(L), 최대 err). 상수 가중치 없음.
   - (d) 차동쌍 시도 순서(L4): (i) 같은 총 W에서 nf 조정 = (a)의 후보 중 common-centroid 성립 조합 → 있으면 채택 (ii) 없으면 `W_request{device, W_new = nf_min · fw_min_ok, reason="cc_nf"}`를 그룹 모든 멤버에 같은 값으로(nf_min = 멤버 수, fw_min_ok = 슬라이스 폭 중 W_need/nf_min에 가장 가까운 것) 내고 이 그룹은 '대기'(**[개정 Q4]** `W_adjustable` 조건 삭제 -- 모든 차동쌍이 시도) (iii) MOD8이 그 요청을 거부(제약 위반)해 돌아오면 interdigitation으로 완화 + `relaxed=true`, `attempts=[{nf, finger_w, W, reason}]` 전부 기록, **[개정 Q8 (iv)]** 결과 맨 앞 `review_needed`에 dx·dy·근본 원인.
   - (e) 실패도 레코드로 남기고 다음 그룹으로 계속(L7). 그룹 결과 = 필드 `ly.group[gid]`.
3. **행별 finger 확정**(`finger_geometry`): 한 물리 행 안 finger_w는 하나(SD 6305~6310 물리 규칙). 행 안 그룹 배치들의 finger_w가 다르면 그 행을 finger_w별로 나눈다(R 2·LP §5 (c)1 (i)). 매칭 그룹이 없는 소자는 같은 행 소자 W들로 (a)를 다시 돌려 행 finger 수 합이 가장 작은 공통 fw. 다른 행의 fw는 후보로 쓰지 않는다(L6). 어떤 fw로도 상한을 못 지키면 그 소자는 `W_request{reason="finger_quantization"}`.
4. **Euler 판정**(`row_euler`): 행에 패턴 결과가 있으면 그 `transistor_sequence`를 `check_walk_sequence`로 검산, 없으면 `build_graph` → `check_euler_condition` → (행 안 matching 쌍이 있으면 `mirror_symmetric_trail`) → `hierholzer`. impossible이면 `find_min_crossover_layout`(W 불변, crossover 수 기록). 결과를 `canonical_row`로 정규화.
5. **box 개선**(**[개정 Q8 (v)(vi)]**, L15): 목적 = 판정 축 면적(floorplan 외곽 + dummy·tap·well). 행 폭 큰 순으로 접기 후보를 만든다 -- matching 그룹이 없는 행은 `apply_explicit_row_split` n_rows = 2, 3, ...(확산 안전 분할점만), matching 그룹이 있는 행은 패턴 함수를 n_rows = k로 다시 불러 재구성. 후보마다 `row_euler` + `match_audit`를 다시 돌려 matching(3b·3c·dx·dy)이 나빠지면 버리고, 남은 후보 중 전체 floorplan 판정 축 면적이 줄어드는 것만 채택(개선 없으면 정지 -- 반복 상한 = 그 행 finger 수, 리터럴 없음). 행 폭 비는 `ly.box`에 기록만(하드 게이트 없음). 행 접기는 소자 nf·fw 불변.
6. **floorplan**(`build_floorplan`): 4단계 결과의 sequence를 재사용(`transistor_sequences` 인자), `pack_floorplan_grouped` 호출. **[개정 Q8 (vii)(viii)]** 판정 축 면적에 행 끝 dummy 2개·그룹 경계 tap·body 다른 그룹 사이 well 간격을 넣고 '포함 항목'을 기록, stage를 넘는 hub 병합은 병합안·비병합안 면적 비교(`hub_merge`, 노이즈 우려는 기록만).
6a. **확산 기하**(`diffusion_stats`, **[개정 Q6]** L14): 최종 행 Euler에서 소자별 ad/as/pd/ps → `ly.diffusion[dev]`.
7. **coverage**: 입력 소자 이름 집합 = 행 소자 이름 집합.

`run_layout` 반환: `LayoutResult`(소자 `{n_fingers, finger_w, rows[{row_id, n_fingers}], W_realized, W_err_rel, W_tol_lower, W_tol_upper}`, 그룹 `{pattern, method, residual, crossover_count, ok, relaxed, attempts}`, 행 Euler, box, floorplan, coverage, `W_requests`). `W_err_rel > W_tol_upper`인 소자가 있는 결과는 `W_requests`가 비어 있을 수 없다(불변식, test).

## 4. graph 레이아웃 필드로 쓰는 방식 (필드 = 캐시, L11)

- 레이아웃 결과는 채택 S2 스냅샷에 붙는 `ly.*` 필드다. 필드마다 writer 파일 1개, 값 + `input_fp`(그 필드가 읽은 입력의 정규화 지문)를 함께 저장. 같은 `input_fp`면 재사용, 다르면 그 필드만 재계산(NR 4.1 행 Euler·패턴·finger 후보 키와 같음).

| 필드 | writer | input_fp에 들어가는 것 |
|---|---|---|
| `ly.fw_cand[kind, W]` | `finger_candidates.py` | kind, W_m(`float.hex`), gm_id, tol_v, 슬라이스 집합 지문, grid |
| `ly.group[gid]` | `pattern_select.py` | 멤버 정렬 튜플, role, hub 넷, 멤버별 `ly.fw_cand` 지문, `W_adjustable`, MOD8 거부 기록 |
| `ly.finger[dev]` | `finger_geometry.py` | 소속 행의 `ly.group` 지문들 + 비매칭 소자 W |
| `ly.row[rid]` | `row_euler.py` | 정렬 (이름, kind, s, d, nf) 튜플 + 패턴 sequence 지문 |
| `ly.rows`, `ly.box` | `rows.py`, `box_shape.py` | `ly.row` 지문 집합, L, PDK 지문, box 기준 선언 |
| `ly.floorplan` | `floorplan.py` | `ly.rows` 지문, matching 그룹, PDK 지문 |
| `ly.w_requests`, `ly.coverage` | `run.py` | 위 필드 지문 |

- MOD8이 소자 X의 W를 바꾸면 새 스냅샷은 X의 W를 읽는 필드(`ly.fw_cand[kind_X, W_X]`, X가 속한 그룹·행, 그 위 `ly.rows`/`box`/`floorplan`)만 miss, 나머지는 구조 공유로 그대로(NR 2.2 '바뀐 소자의 W를 읽는 블록만 miss').
- graph 밖 캐시는 LUT 슬라이스 memo(`lut/slices.py`, 디스크 E3)뿐.

## 5. MOD8 W_request 루프 계약 (`convergence/w_requests.py`, `convergence/loop.py`)

- 입력: 채택 front 점의 S2 스냅샷 + `LayoutResult.W_requests`. 출력: 수렴 스냅샷(레이아웃 필드 포함) 또는 `NONCONVERGENT` 실패 레코드(N3.14, margin = 마지막 |Δ|/tol).
- 한 반복 k: (1) 요청 W를 해당 소자의 W 고정 제약으로 MOD6 `evaluate`(θ 재탐색 포함, ID 고정 gm_id 역산만이 아님 -- LP §5 (c)2) (2) 봉인·제약 통과면 새 계약으로 `run_layout`, 위반이면 그 요청을 '거부'로 레이아웃에 돌려준다(→ 3단계 2(d)(iii)) (3) finger_w가 LUT `w_ref_m`와 다른 소자는 그 폭 슬라이스로 재평가(R 3, diode 연결 소자 제외) (4) `check_stick_diagram_coverage`(LR9).
- **[개정 Q4 (ii)(iii), L13]** 진입 조건 = '폭 키(finger_w 슬라이스·nf)가 사이징 스냅샷과 다름' 또는 'W_request 있음'. W_request가 없어도 MOD7 결과가 나오면 실현 기하를 S2 `layout`에 쓰고 평가 커널 1회 + 봉인 1~8을 다시 돌린 뒤 freeze한다(바뀐 폭 키 필드만 miss). diode 연결 소자도 노드전압·봉인은 재계산(ID 재보정만 생략). 결과 JSON에 metric 3열(엔진@sizing W / 엔진@실현 W / SPICE@실현 W)을 남긴다(L14·LY8).
- 수렴: `W_requests` 비어 있음 + 모든 소자 `W_err_rel <= W_tol_eff`(실효 허용오차) + 직전 반복과 W 계약 지문 같음 + 실현 기하 재평가·봉인 통과.
- 반복 상한(P N3.6 K_max 규칙을 W 축에 적용, 상수 없음): 요청 소자 i마다 구간폭_i = 그 소자 ID·L·VDS·VSB에서 LUT gm/ID 격자 범위가 허용하는 W 상대 범위 `(W_hi,i − W_lo,i) / W_m,i`(LUT에서 계산), 분해능_i = `W_tol_upper,i = tol_V·(gm/ID)_i`. `K_max = max_i ceil(log2(구간폭_i / 분해능_i))`.
- 조기 판정(N3.6 438~441행 그대로): Δk = max_i |W_k,i − W_k−1,i| / W_k−1,i, q = Δk/Δk−1(최소 3반복부터). q < 1이면 `q^(K_max−k)·Δk/(1−q) > min_i 분해능_i`로 남은 반복 안 도달 불가가 확정될 때, q >= 1이면 K_max에 닿을 때 NONCONVERGENT. 추가로 W 계약 지문이 앞선 반복의 것과 같아지면(순환) 즉시 NONCONVERGENT(cycle). 창 크기·횟수 상수 없음.
- 기록: 반복마다 (k, 요청 목록, 거부 목록, Δk, q, 지문)을 S3에 append(WP-11). 완화가 일어난 그룹은 결과 JSON `relaxed`·`attempts`로 보고(조용한 완화 금지).

## 6. test 계획 (규칙 D: `tests/layout/test_<file>.py`; 교차 = `tests/structure/`, `tests/integration/`)

기대값은 오라클(손계산·원문 표·옛 엔진 실측 기록)에서만. 작성 주체 분리(PROCEDURE 1).

| id | 대상 파일 | 픽스처 | 판정 |
|---|---|---|---|
| T1 M3a 단위셀 폴백 | `finger_geometry`, `rows` | 옛 행 `diffpair_branch_a__nmos`: M3a 3.495, M3b 3.393, M4a·M4b 5.215, M5 65.746 µm(LP §3) + 다른 행 fw 36.0165 µm 존재 | 어느 소자도 다른 행 fw를 쓰지 않음; 각 소자 `W_err_rel <= W_tol_upper` 또는 그 소자 `W_request`; M3a w = 36.02 µm(옛 SD 6091~6095 결과)이 나오지 않음 |
| T2 M4a 차동쌍 2x2.61 µm | `pattern_select`, `w_tolerance` | M4a·M4b W 5.2152 µm, role diff_pair, 슬라이스 집합에 2.61 µm 포함, grid 0.005 µm, 픽스처 tol_v·gm/ID >= 하한 | common_centroid `rotation_exact`, nf=2씩, residual 0, relaxed=false. 손계산: 2x2.610 = 5.220 → err 9.2e-4 <= 하한 0.005/(2x2.61) = 9.58e-4(격자 한계 안, 상한 이하). 옛 결과(1x36.02 → 성장 거부 → relaxed, LP §4)와 대조 기록 |
| T3 전 그룹 판정 | `pattern_select`, `run` | 첫 그룹이 적용 불가(공유 hub 없음)인 그룹 3개(옛 M11b/M20b → M37a/M37b 순서 재현) | 3그룹 모두 레코드, M37 쪽 그룹 판정 존재(옛 `growth_not_applicable` 중단과 대조) |
| T4 N멤버 그룹 | `pattern_select` | 7소자 미러 레코드(LP §4 M18_bg 그룹) | 그룹 레코드 1개로 판정(2-tuple 21쌍 아님) |
| T5 차동쌍 완화 순서 | `pattern_select` + MOD8 | **[개정 Q4·Q8]** (i) W < 2·최소 finger 폭이라 nf 조정 불가 + MOD8 거부 (ii) 같은 입력 + MOD8 수용(활성 제약 차동쌍 포함) | (i) `relaxed=true`, `attempts`에 nf·W·사유가 시도 순서대로, 결과 맨 앞 `review_needed` + dx·dy; (ii) W_request가 반드시 나가고 relaxed=false |
| T16 접기 재판정 | `rows`, `match_audit` | **[개정 Q8 (v)]** 매칭 2멤버 행 + box 개선 후보 | 접은 결과 3c가 나빠지면 미채택, 비매칭 행만 `apply_explicit_row_split` |
| T17 실현 기하 재평가 | `run` + MOD8 | **[개정 Q4 (ii)]** W_request 없는 MOD7 결과(폭 키만 다름) | 평가 커널 1회·봉인 1회, 바뀐 폭 키를 읽는 필드만 재계산 |
| T6 표 경로 실사용 | `pattern_select` | 2멤버 nf 4:2, 2멤버 2:2 | `common_centroid` `pattern_table` AAB/BAA; `interdigitate` base "AB" → `pattern_table` ABBA(옛 엔진 실측: 이 입력에서 같은 결과) |
| T7 결정론 | `canonical_rows` | 1 finger 단독·[A, A] 행 | PYTHONHASHSEED 1~5에서 node_sequence 같음(복사 원본은 다름 -- 7절 실측) |
| T8 W 보존 불변식 | `run` | 9회로 레이아웃 입력(MOD4 출력 픽스처) | 모든 소자 `W_err_rel <= W_tol_upper` 또는 `W_request`; 행 접기·crossover 전후 Σ nf·fw 같음 |
| T9 AST 해시 | `tests/structure/test_copied_ast_hash.py` | `_copy_manifest.py` | 전 항목 일치, 복사본 리터럴 집합 = 2.2 목록 |
| T10 원문 표 | `test_patterns_interdigitate.py`, `test_patterns_common_centroid.py` | test 작성자가 PDF p.15·p.19에서 독립 전사한 표 | 두 표 값 일치 + p.19 3·4행 열 부재를 `xfail(reason=표 확장 미결정)`으로 명시 |
| T11 허용오차 식 | `w_tolerance` | toy tol_v, gm/ID, fw, tlef 격자 | 상한·하한 손계산, 하한 > 상한 → 다른 후보 → 없으면 W_request |
| T12 MOD8 루프 | `convergence/loop` | toy 1회 수렴, 2-주기 순환, q >= 1 발산 | CONVERGED / NONCONVERGENT(cycle) / NONCONVERGENT(K_max), K_max 손계산 |
| T13 box 대조 | `box_shape` | overhead 0 입력 | SD `check_box_shape`와 같은 판정 |
| T14 Euler 막힘 | `row_euler` | 홀수차수 4개 행 | crossover 1개, 총 W 불변 |
| T15 필드 재사용 | `run` + MOD8 | 소자 1개 W 변경 | 그 소자를 읽는 `ly.*` 필드만 재계산(계산 블록 카운터) |

## 7. 원문 대조: `INTERDIGITATION_PATTERNS`·`COMMON_CENTROID_PATTERNS`

- 원문 위치: `C:/Users/HSLEE/OneDrive - 주식회사 토닥/work/Todoc/Design/vendor/analog/Layout02.pdf`(38쪽, sha256 앞 16자 `67225fc639670bfe`), 같은 폴더 `Layout02_stacked_layout(update).pptx`. 출처 표기는 `references/stick-diagram-euler-layout.md` 3~4행(`vendor/analog/Layout02.pdf`). `C:/Users/HSLEE/Documents/Todoc/fpga` 아래(저장소·references·assets zip 밖)에는 없다: `extract_pdf.py`·`pdf_gaps.txt`는 UVM cookbook 추출물이고, 그 밖 pdf/pptx는 alamo·austria·venezia·tb_build 문서뿐.
- 방법: PyMuPDF로 p.15·p.17~19 텍스트·단어 좌표 추출 + 170 dpi 렌더 육안 확인, SD 표는 `ast.literal_eval`로 읽어 기계 비교.

| 항목 | 결과 |
|---|---|
| p.15 Interdigitation 8 base x 4열 | **값 전부 일치**(A, AB, ABC, ABCD, ABA, ABABA, AABA, AABAA) |
| p.15 `*` 표시 | 원문은 base 열(AB*, ABC*, ABCD*, AABA*)과 3x 열 양쪽에 있다. SD 주석은 '3x `*`'만 적음 -- 값 영향 없음, 주석 불완전 |
| p.15 ABCD 3x `ABCBCADBCDA` | 원문도 11자(A3 B3 C3 D2) -- 원문 자체의 불균형. SD는 그대로 옮김. 표 경로는 nf (3,3,3,2)에서만 맞으므로 4소자 같은 nf 3x에는 사실상 쓰이지 않음 |
| p.19 Common Centroid 1열(2행 기본)·2열(2행 확장) | **4가족 모두 일치**(SD repeat 1·2 = 원문 1·2열) |
| p.19 3열·4열 | **SD에 없음**: 원문은 3행 배열(예: ABBAABBA / BAABBAAB / ABBAABBA)과 4행 배열(ABBAABBA / BAABBAAB / BAABBAAB / ABBAABBA)을 4가족 모두 싣는다. SD `common_centroid_layout`은 표를 n_rows = 2에서만 쓰므로 현 동작 영향 없음, 3·4행 표 경로는 없음(회전·탐색 경로가 대신 처리) |
| p.19 열 의미 | 원문에 열 머리글 없음. SD의 '반복 차수' 키(1, 2)는 해석이다: 2열은 균일 2배가 아님(ABCCBA → ABCCBAABC 9자, AAB → AABBAA). SD에서 키는 개수 대조용이라 동작 영향 없음 |
| p.17·p.18 | p.17 DA/DB 대각 배치, p.18 cross coupling vs tiling(ABBA/BAAB) -- SD docstring 설명과 일치 |

- 결론: 두 표의 **현재 값은 원문과 같다**(오기 0). 차이는 (1) p.19 3·4행 열 누락 (2) 주석의 `*`·'반복 차수' 표기. 복사 시 값은 그대로(L10), 정정은 새 파일 머리 주석에만. 3·4행 표 추가는 함수 본문 변경(해시 깨짐)이라 이 범위 밖 -- 필요해지면 별도 결정.
- 같은 대조에서 찾은 복사본 결정론 결함(NR 1.5): SD `_hubleaf_sequence_node_path`(265~290)가 `set` 순회로 시작 노드를 고른다. 실측(SD 그대로 실행): `interdigitate_layout([A nf=1], base="A")`의 node_sequence가 PYTHONHASHSEED=1에서 `[hub, da]`, 2·3에서 `[da, hub]`. 본문을 고치면 해시가 깨지므로 `canonical_rows.py`(새 코드)가 transistor_sequence에서 시작 노드를 정렬 순서로 다시 유도한다(T7).

## 8. 열린 항목 (기본안 포함)

1. ~~box 허용 비·pitch 여유: 사람 선언(spec)·PDK 선언으로 받는다~~ → **해소(사용자 2026-10-07 Q8 (vi) (나))**: box 허용 비 선언 없음, pitch 여유는 PDK 선언. spec 형식에 레이아웃 기준 항목을 추가하지 않는다.
4. 행 그룹 유도(기둥에서 서로소 행, 형제 배제)·floorplan 입력 의미(spine = 블록, sub_kinds, mirror_pairs = 좌우 대칭 행 쌍, net_weights) 정정은 reference 검토 E-3(엔진 내부)으로 별도 반영 대상.
2. 복사본 내부 탐색 상한 리터럴(2.2): 기본안 = manifest 한정 예외 + 리터럴 집합 test 고정.
3. p.19 3·4행 표 경로: 기본안 = 추가하지 않음(원문 대조 기록만).
