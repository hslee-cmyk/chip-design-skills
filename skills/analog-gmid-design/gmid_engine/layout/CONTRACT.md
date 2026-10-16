# gmid_engine.layout 동작 계약 (test 작성용) -- 1단계: 복사 단위 + canonical_rows, 2단계: 행 구성(4절)

- 대상: 0~3절 = 1단계 파일 15개(아래 0절 표, 2026-10-07 `hub_candidates.py` 복사 추가). **4절 = 2단계 행 구성·입력/출력 계약·
  graph 레이아웃 필드**(파일 15개). MOD8 W_request 루프·레이아웃 뒤 재검증 실행은 `convergence`(U14, `convergence/CONTRACT.md`)가 하고 이 계약에는 요청 인터페이스만 있다(4.14).
- **2026-10-07 사용자 결정 Q4·Q8 반영판**(근거 `wt/_drafts/engine/reference_review/SYNTHESIS.md` Q4·Q8, G2-01~03·05~07·09·10·14·20):
  LY1 보존량 = (ID, gm/ID, L), 실현 W 의 기준 = `W_need(fw) = ID / J_slice(fw)`(4.2), 허용오차는 후보 순위 기준·실효 = max(상한, 하한)
  (4.3), 레이아웃 뒤 재검증 요청(4.14), branch_symmetric 행 swap·제외 role·review_needed(4.5~4.6), box 하드 게이트 폐지·판정 축 면적
  목적·dummy/tap/well 포함·hub 병합(4.9~4.11).
- 근거: `wt/_drafts/engine/design_mod7_layout.md`(이하 DM) 1절 표·1.1 복사 정의 전수표·2.1 AST 해시·2.2 리터럴·7절 끝 결정론
  결함·8절 2 기본안, `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 1.5(결정론).
- import 경로: 1단계 test 는 파일 모듈을 직접 import 한다(2단계 공개 API 는 4.0 -- `from gmid_engine.layout import ...`)
  (예: `from gmid_engine.layout.canonical_rows import canonical_row`). `_` 이름은 test 에서도 쓰지 않는다
  (`_helpers_hubleaf` 는 끝의 공개 별칭으로 접근).
- test 배치(규칙 H): `gmid_engine/tests/layout/test_<파일>.py`(`_helpers_hubleaf.py` -> `test__helpers_hubleaf.py`,
  `_copy_manifest.py` -> `test__copy_manifest.py`). 해시·리터럴 교차 검사는 DM 6 T9 대로
  `tests/structure/test_copied_ast_hash.py`.
- 옛 원본(SD): `skills/analog-gmid-design/legacy/stick_diagram.py`(9,010행, HEAD a21a24f, 마지막 변경 60727b0 = 내용 변경 없는 이동).
  저장소에 있는 동안 SD 는 대조 오라클로 import 가능하다(`legacy/` 를 `sys.path` 에 넣고 `import stick_diagram`).

---

## 0. 파일·층·진입점

층 = `_module_map.LAYERS` 의 layout tuple 위치. 파일은 앞 층 파일만 import 한다(같은 층끼리 금지).

| 파일 | 층 | 독립 진입점 | 내용 |
|---|---|---|---|
| `_copy_manifest.py` | 0 | (데이터, 공개 정의 0) | `COPY_SOURCE`, `COPIED_DEFINITIONS`(60행) |
| `transistor.py` | 0 | `Transistor` | 복사 |
| `hub_candidates.py` | 0 | `find_hub_merge_candidates` | 복사(SD 2635~2658, 2026-10-07 Q8 (viii)) |
| `coverage.py` | 1 | `check_stick_diagram_coverage` | 복사(+`CoverageVerdict`) |
| `euler_graph.py` | 1 | `build_graph` | 복사(+`StackGraph`) |
| `row_fold.py` | 1 | `apply_explicit_row_split` | 복사 |
| `euler_condition.py` | 2 | `check_euler_condition` | 복사(+`EulerVerdict`, `_degrees`, `_is_connected_ignoring_isolated`) |
| `euler_trail.py` | 2 | `hierholzer` | 복사 |
| `floorplan_pack.py` | 2 | `pack_floorplan_grouped` | 복사(15개 정의) |
| `crossover.py` | 3 | `find_min_crossover_layout` | 복사(9개 정의) |
| `_helpers_hubleaf.py` | 4 | (공용 helper) | 복사 7개 + 공개 별칭 6개 |
| `mirror_trail.py` | 4 | `mirror_symmetric_trail` | 복사(+`build_mirror_symmetric_pattern`, `WalkVerdict`, `check_walk_sequence`) |
| `patterns_common_centroid.py` | 5 | `common_centroid_layout` | 복사(9개 정의) |
| `patterns_interdigitate.py` | 5 | `interdigitate_layout` | 복사(3개 정의) |
| `canonical_rows.py` | 6 | `canonical_row` | 새 코드 |

`_helpers_hubleaf.py` 공개 별칭(정의 이름 앞 `_` 를 뗀 이름 = 같은 함수 객체): `build_rows_from_shares`,
`build_rows_from_shares_with_crossover`, `common_centroid_residual`, `count_isolated_pairs`, `hubleaf_sequence_node_path`,
`repair_row_parity`. 두 패턴 파일은 `from ._helpers_hubleaf import <별칭> as _<원래 이름>` 으로 묶어 복사 본문의 이름이
그대로 풀린다(구조 규칙 B: 다른 파일의 `_` 이름 import 금지). 불변식: `_helpers_hubleaf.<별칭> is _helpers_hubleaf._<별칭>`.

---

## 1. 복사 정의 = '옛 동작과 같음' (AST 해시)

판정 함수(정의 하나): `sha256(ast.dump(node, annotate_fields=True, include_attributes=False).encode("utf-8")).hexdigest()`.
`node` = 모듈 최상위의 그 이름 정의(`FunctionDef`·`ClassDef`·이름 하나에 대입하는 `Assign`). docstring 포함, 주석·줄 번호 제외.
`ast.dump` 결과는 Python 버전에 따라 달라질 수 있다 -- 해시는 Python 3.14.2(`C:\Python314\python.exe`)에서 계산했다.

`_copy_manifest.COPIED_DEFINITIONS` 의 행 = `(새 파일, 정의 이름, "SD시작~SD끝", 해시, 리터럴 tuple)`.

불변식:
1. 행 수 60, (새 파일, 정의 이름) 중복 없음, DM 1.1 표 59행 + `('hub_candidates.py', 'find_hub_merge_candidates')`(Q8 (viii))와 같은 집합.
2. 행마다 `layout/<새 파일>` 의 같은 이름 최상위 정의가 정확히 1개 있고 그 해시 = manifest 해시.
3. SD 가 저장소에 있으면: SD 의 같은 이름 최상위 정의 해시 = manifest 해시, 그 노드의 `(lineno, end_lineno)` = manifest 행 범위
   (데코레이터 줄 제외). -> 3자 일치. SD 삭제 뒤에는 2자(manifest·새 파일).
4. 복사 파일(manifest 의 새 파일 13개)의 최상위 문장 = 모듈 docstring + import + manifest 등록 정의 + (`_helpers_hubleaf.py` 만)
   공개 별칭 대입 `x = _x`. 등록 밖 정의 0.
5. 복사 파일마다 모듈 전역 이름 해석 완전: 정의가 읽는 전역 이름은 모두 그 모듈에서 묶이거나 builtin(symtable 기준 미해결 0),
   모든 layout 모듈 import 성공.
6. 동작 대조(오라클 = SD, 같은 `PYTHONHASHSEED`): 같은 입력에서 SD 함수와 복사 함수의 반환이 같다. 비교는 반환 dict 를
   재귀 직렬화(dataclass 는 필드 dict)해서 한다. 작성자 실측(참고, 판정 아님): seed 0·1·2 에서 아래 8개 입력 모두 같음 --
   `interdigitate_layout`(nf 4:2 base "AB" / 3:3:2 base 없음), `common_centroid_layout`(3멤버 nf 4 회전, 2멤버 4:2
   `n_rows=2` 표, 6:4:2 `n_rows=4` 탐색), `find_min_crossover_layout`(홀수 leaf 4개 + 쌍 1개), `mirror_symmetric_trail`,
   `check_stick_diagram_coverage`.

### 1.1 복사본 리터럴 집합 (DM 2.2·8절 2 -- 새 리터럴 유입 0)

manifest 리터럴 tuple = 그 정의 안 숫자 리터럴 중 구조 규칙 D(`tests/structure/structure_checks._number_allowed`)가 허용하지 않는
것의 repr 문자열(USub 가 붙으면 앞에 `-`), 정렬. 불변식:
1. 정의마다: 규칙 D 위반 리터럴의 정렬 다중집합 = manifest tuple(현재 합계 62개).
2. layout 전체의 규칙 D 위반은 모두 manifest 등록 정의 안에 있다(등록 밖 0). 새 코드 파일(`canonical_rows.py`·4절 파일)·`_copy_manifest.py` 는 0.
3. 등록 정의별 현재 집합(이 표가 바뀌면 복사 본문이 바뀐 것 -- 해시도 깨진다):

| 정의 | 리터럴 |
|---|---|
| `_repair_row_parity` | 50 |
| `_common_centroid_residual` | 0.5 |
| `_hubleaf_sequence_node_path` | 2 |
| `_MAX_CROSSOVER_PAIRING_NODES` | 8 |
| `_pair_odd_nodes_by_mirror`, `find_min_crossover_layout`, `check_euler_condition`, `_try_pattern_table_match`, `find_hub_merge_candidates` | 2 |
| `skyline_pack` | 1e-09 |
| `skyline_pack_best_width` | 3, 60 |
| `pack_to_height` | 60 |
| `evaluate_row_split_candidates` | 0.6, 100 |
| `pack_floorplan` | 0.3, 0.5, 2.0, 2.2, 40 |
| `_pack_by_subkind` | 0.3, 0.5, 2, 2.2, 40 |
| `pack_floorplan_grouped` | 2.0, 40 |
| `_MAX_MIRROR_TRAIL_COMBO_PAIRS` | 12 |
| `common_centroid_layout` | 2, 2, 2, 24 |
| `COMMON_CENTROID_PATTERNS` | 2 x4 |
| `_fix_block_parity` | 2, 3 |
| `INTERDIGITATION_PATTERNS` | 2 x8, 3 x8, 4 x8 |

### 1.2 표 값 (DM 7절, T10)

`INTERDIGITATION_PATTERNS`(8 base x repeat 1~4)·`COMMON_CENTROID_PATTERNS`(4가족 x repeat 1·2) 값은 원문(Maloberti
Layout02.pdf p.15·p.19)과 같다. p.19 3·4열(3행·4행 배열)은 표에 없다 -- 기대값 test 는 그 열을
`xfail(reason="표 확장 미결정")` 으로 둔다(DM 6 T10, 8절 3 기본안 = 추가하지 않음).

---

## 2. `canonical_row(seq_result, members) -> dict` (DM 7절 끝, T7)

입력:
- `seq_result`: 행 결과 dict 하나. 필수 `transistor_sequence`(소자 이름 list). 선택 `segments`(list of
  `{transistor_sequence, node_sequence}`), `node_sequence`, `crossover_after` 등 -- 복사 패턴 함수(`interdigitate_layout`·
  `common_centroid_layout` 의 `rows[i]`, `find_min_crossover_layout` 결과 평탄화 행)와 같은 모양.
- `members`: `name`·`source`·`drain` 속성을 가진 소자들(`Transistor`).

출력: 새 dict(입력 dict·list 는 바꾸지 않는다). 입력의 다른 키는 그대로 옮기고:
- `segments` 가 비어 있지 않으면: segment 마다 `node_sequence` 를 다시 유도, 행 `node_sequence` = segment `node_sequence` 를 순서대로
  이어 붙인 것(복사본의 평탄화와 같다). segment 의 `transistor_sequence` 는 같은 값.
- 그 밖(`segments` 없음·빈 list): `transistor_sequence` 전체를 한 walk 로 유도.
- `transistor_sequence` 는 입력과 같은 값.

유도 규칙(walk): 시작 노드 후보 = 그 열에 나오는 소자들의 source·drain 넷 집합을 **`sorted()` 순서**로. 후보마다 finger 를 차례로
건너며(현재 노드가 그 소자의 source 면 drain 으로, drain 이면 source 로, 둘 다 아니면 실패) 끝까지 가는 첫 후보의 node 열을 쓴다.
빈 열 -> `[]`.

불변식:
1. **결정론**: 같은 `(seq_result 의 transistor_sequence·segments 의 transistor_sequence, members 연결)` 이면 결과가 같다 --
   `PYTHONHASHSEED` 1~5 별도 프로세스에서 같은 값, 입력 `node_sequence` 값과 무관.
2. walk 성질: 각 segment(또는 행)에서 `len(node_sequence) == len(transistor_sequence) + 1`(빈 열 제외), i 번째 finger 의
   `{source, drain}` = `{node_sequence[i], node_sequence[i+1]}`(source == drain 이면 둘 다 그 넷).
3. 시작 노드 = 유효한 시작 노드 중 정렬 최소.
4. 유효한 시작 노드가 하나뿐인 행에서는 결과 `node_sequence` = 입력 `node_sequence`(복사 함수 출력과 같음).

오라클(손계산, hub = "hub", leaf = "da"·"db"):
- 1 finger `A(hub→da)`: 유효 시작 {da, hub} -> `["da", "hub"]`. 복사 원본 `interdigitate_layout([A nf=1], base="A")` 의
  `rows[0]["node_sequence"]` 는 seed 에 따라 `["hub","da"]`/`["da","hub"]`(DM 7절 실측; 작성자 재실측 seed 1~5 에서 2가지),
  `canonical_row` 결과는 늘 `["da", "hub"]`.
- `[A, A]`(A nf=2): `["da", "hub", "da"]`.
- `[A, B]`(같은 hub): 유효 시작 {da} 하나 -> `["da", "hub", "db"]`.
- 2멤버 nf 4:2 `common_centroid_layout(..., n_rows=2)`(표 AAB/BAA): 행 `["A","A","B"...]` 는 시작 하나뿐 -> 입력과 같음
  (작성자 실측 `["hub","da","hub","db"]`, `["db","hub","da","hub"]`).

실패:
- `transistor_sequence` 에 `members` 에 없는 이름 -> `KeyError`.
- 어떤 시작 노드로도 walk 가 안 되는 열(예: 서로 넷을 공유하지 않는 두 소자 `[A(h→x), B(k→y)]`) -> `ValueError`.

---

## 3. 구조 규칙과의 현재 충돌 (예외 메커니즘 없음 -- 구조 test 소관)

DM 8절 2 기본안 = 'lint 예외를 `_copy_manifest.py` 등록 정의로 한정 + 예외 리터럴 집합 고정'. 아래는 manifest 등록 정의 안의
규칙 위반 원자료다(등록 밖 0). [2026-10-07 실측] 현재 `tests/structure` 검사기는 manifest 등록 정의를 면제하므로(copy audit) A~G·I
모두 PASS 다.

| 규칙 | 위반 수 | 위치 |
|---|---|---|
| D 숫자 리터럴 | 62 | 1.1 표 그대로 |
| E 회로 이름 | 12 | `'A'`·`'B'` 문자열(패턴 글자)이 library 한 회로의 넷 이름 `A`·`B` 와 전체 일치: `_common_centroid_from_pattern_table` 8, `_try_pattern_table_match` 2, `INTERDIGITATION_PATTERNS` 2 |
| G 모듈 수준 가변 객체 | 2 | `INTERDIGITATION_PATTERNS`, `COMMON_CENTROID_PATTERNS`(dict 리터럴 -- `MappingProxyType` 으로 감싸면 해시가 깨진다) |

A·B·C·F 는 위반 0. H(마커 `structure_test_mapping`)는 test 파일 14개 누락(이 계약으로 작성할 test).

---

## 4. 행 구성 (2단계) -- `run_layout` 과 계산 블록 4개 (2026-10-07 Q4·Q8 반영판)

근거: DM 2절(입력 인터페이스)·3절(행 구성)·4절(graph 레이아웃 필드), 계획 N3.17 LY1~LY7·'레이아웃 입력·출력 계약',
core 계약 5·6절(GraphSnapshot·`compute_block`), lut 계약 1.6(`widths`)·4절(`vgs_for_gm_id`·`op_point`)·5절(tol_V `id_equivalent`),
사용자 결정 2026-10-07 Q4 (i)~(iv)·Q8 (i)~(ix)(`reference_review/SYNTHESIS.md`).
단위: 길이·폭 m, 면적 m^2, 전압 V, 전류 A, 전류 밀도 A/m. **폭 키** = finger_w / 제조 격자(정수, LUT 슬라이스 폭 키와 같은 것).

### 4.0 파일·층·진입점 (`_module_map.LAYERS` layout)

| 파일 | 층 | 진입점 / 종류 | graph 필드(writer) |
|---|---|---|---|
| `_ly_fields.py` | 0 | 상수 표(공개 정의 0) -- 필드 이름·`LY_WRITERS`·`BLOCK_WRITERS` | -- |
| `contract_input.py` | 0 | 데이터 선언: `LayoutDevice`·`MatchingGroup`·`RowGroup`·`LayoutPdk`(`from_lut`·`from_decl`)·`LayoutInput`, 상수 `KINDS`·`ROLE_*`·`LAYOUT_ROLES`·`EXCLUDED_ROLES`·`ROLES`·`CC_REQUIRED_ROLES`·`PATTERN_*`·`PATTERNS`·`PDK_RULE_QUANTITIES`·`GRID_QUANTITY` | -- |
| `contract_output.py` | 0 | 데이터 선언: `SliceDensity`·`WTolerance`·`FingerCandidate`·`WRequest`·`GroupAttempt`·`PatternRow`·`GroupLayout`·`MatchingDisposition`·`DeviceFinger`·`RowLayout`·`BoxVerdict`·`FoldAttempt`·`MergeDecision`·`GroupRebuild`·`RowsLayout`·`FloorplanSummary`·`DeviceLayout`·`ReviewItem`·`RealizedDevice`·`Revalidation`·`LayoutResult`·`LayoutOutputs`, 상수 `REVALIDATION_*`·`AREA_ITEM_*`·`MERGE_NOISE_NOTE` | -- |
| `hub_candidates.py` | 0 | `find_hub_merge_candidates`(복사, 1절) | -- |
| `slice_density.py` | 1 | `slice_density` | (run_layout 이 device `ly_slices` 에 씀, writer `ly_slice_density`) |
| `w_tolerance.py` | 1 | `w_tolerance` | -- |
| `area_tie.py` | 1 | `area_tie_m2`(ΔA_tie, 4.10) | -- |
| `diffusion.py` | 1 | `diffusion_geometry`(`ly.diffusion`, 4.10a) | -- (`compose_rows` 가 부른다) |
| `passives.py` | 1 | `passives_from_decl`(수동소자 블록 면적, 4.10) | -- |
| `finger_candidates.py` | 2 | `finger_candidates`(@compute_block) | device `ly_fw_cand`(`ly_finger_candidates`) |
| `floorplan.py` | 3 | `floorplan_of`(계산 블록 아님 -- `compose_rows` 가 부른다) | -- |
| `_helpers_pattern.py` | 7 | 공용 helper: `orient`·`offsets`·`pattern_rows`(반환 모양은 아래) | -- |
| `box_shape.py` | 7 | `box_verdict` | -- |
| `row_euler.py` | 7 | `row_euler` | -- |
| `patterns_row_swap.py` | 8 | `row_swap_layout` | -- |
| `pattern_select.py` | 9 | `pattern_select`(@compute_block) | graph `ly_groups`·`ly_dispositions`(`ly_pattern_select`) |
| `finger_geometry.py` | 9 | `finger_geometry`(@compute_block) | device `ly_finger`(`ly_finger_geometry`) |
| `rows.py` | 9 | `compose_rows`(@compute_block) | graph `ly_rows`·`ly_floorplan`·`ly_diffusion`(`ly_rows`) |
| `outputs.py` | 10 | `layout_outputs`(필드 파생 출력, 4.12 5~8) | -- (읽기만) |
| `run.py` | 10 | `run_layout` | 입력 필드(`ly_input`), device `ly_slices`(`ly_slice_density`) -- 설계점 스냅샷 위(4.12) |

`_helpers_pattern` 반환 모양:
- `orient(group, devices)` -> 성공 `(ends, "")`, ends = 멤버 순서(`group.members`) tuple of `(이름, hub 넷, leaf 넷)` 3-tuple(hub 가 source 쪽).
  실패 `(None, 사유)`, 사유 ∈ `"no_hub_net"`, `"member_not_on_hub:<이름>"`(멤버 순서로 처음 닿지 않은 이름), `"leaf_net_shared"`.
  `devices` = {이름: `name·source·drain` 속성 객체}.
- `offsets(rows, members)` -> `(dx, dy)` 둘 다 `fractions.Fraction`(4.5 4 의 정의), `rows` = `transistor_sequence` 속성을 가진 객체들
  (`PatternRow`·`RowLayout`), finger 가 하나도 없는 멤버는 계산에서 빠진다(모든 멤버가 없으면 `ValueError` -- 빈 max).
- `pattern_rows(result, transistors)` -> tuple of `PatternRow(transistor_sequence tuple, node_sequence tuple(canonical_row), segments =
  ((seg transistor tuple, seg node tuple), ...) -- 입력에 segments 없으면 (), crossover_after tuple -- 없으면 ())`, `result["rows"]` 순서.

공개 API(`gmid_engine.layout.__all__`): `LayoutDevice`, `LayoutInput`, `LayoutPdk`, `LayoutResult`, `LayoutOutputs`, `MatchingGroup`, `RowGroup`,
`run_layout`, `layout_outputs`, 소비자가 읽는 필드 이름 `LAYOUT_KEY`(= graph 레코드 key `"layout"`)·`F_DEVICE`·`F_GROUPS_IN`·`F_GROUPS`·`F_FINGER`·
`F_FLOORPLAN`·`F_DIFFUSION`. 파일별 test 는 파일 모듈을 직접 import 해도 된다(1단계와 같다). 계산 블록은 core `ComputeBlock` 이라
`block(snapshot, donors=, counters=)` 으로 부르고(필수 키워드 둘, core 6.2) 계수는 실행 하나의 `RunCounters` 행으로 본다(블록 객체의 `stats()` 는 없다). `_ly_fields.BLOCK_WRITERS` = (`ly_finger_candidates`, `ly_pattern_select`,
`ly_finger_geometry`, `ly_rows`). 옛 `floorplan` 계산 블록·`ly_floorplan` writer 는 없다(`ly_floorplan` 필드는 writer `ly_rows`).

### 4.1 입력 계약 (`contract_input.py`, 전부 frozen dataclass, 값은 불변)

- `LayoutDevice(name, kind, drain, gate, source, body, W_m, L_m, ID_A, gm_id, vds_V, vsb_V, diode, W_adjustable)`.
  `kind` ∈ `KINDS`. `W_m`·`L_m`·`ID_A`·`gm_id` 는 양의 **float**(int 거부). 위반 → `ValueError`.
  **보존량 = (`ID_A`, `gm_id`, `L_m`)**(Q4 (i)). `W_m` = sizing 이 기준 슬라이스에서 낸 **참고 W** -- 보존 대상이 아니고
  `DeviceLayout.W_m`·`no_usable_slice` 요청에만 옮겨진다. `L_m` 은 lut 계약 4.0(r4) 규칙을 따른다: L 앵커이거나 같은
  모델 bin 안 두 앵커 사이(보간). 그 밖이면 그 소자의 슬라이스가 lut 사유(`lut_l_not_anchor`(빈 bin 지도 포함)·`lut_l_outside_model_bins`·
  `lut_l_bin_unbracketed`·`lut_l_cross_bin`·`lut_axis_out_of_range`)로 빠진다(4.2). 레이아웃은 L 판정을 따로 하지 않는다. 옛 `tol_v_V` 필드는 없다(tol_V 는 슬라이스마다 레이아웃이 LUT 에서 읽는다, 4.2). `diode` = 재검증 때 ID 재보정
  불필요 표시(Q4 (iii)), `W_adjustable` = MOD8 이 이 소자 W 를 바꿀 수 있음.
- `MatchingGroup(gid, members, role, hub_net, allowed_patterns)`: `members` tuple(중복 없음, 2개 이상), `role` ∈ `ROLES` =
  `LAYOUT_ROLES`(`"diff_pair"`, `"mirror"`, `"branch_symmetric"`) + `EXCLUDED_ROLES`(`"bias_distribution"`, `"feedback_shared"`),
  `allowed_patterns` = `PATTERNS` 의 비지 않은 부분 tuple, role ∈ `CC_REQUIRED_ROLES`(diff_pair·branch_symmetric) 이면
  `"common_centroid"` 포함 필수. `hub_net` 은 None 가능(branch_symmetric 은 읽지 않는다). 위반 → `ValueError`.
- `RowGroup(rid, kind, body_net, members)`: `members` tuple(중복 없음), `kind` ∈ `KINDS`.
- `LayoutPdk(manufacturing_grid_m, slice_width_keys, finger_pitch_overhead_m, row_gap_m, dummy_w_m, tap_w_m, well_spacing_m,
  rule_ids, source_fp)`: 격자 > 0, `PDK_RULE_QUANTITIES` 다섯 길이(`finger_pitch_overhead_m`, `row_gap_m`, `dummy_w_m`, `tap_w_m`,
  `well_spacing_m`) >= 0, `rule_ids` = ((이름, 규칙 번호), ...) 이름 중복 없음이고 다섯 이름 모두 비지 않은 규칙 번호(Q8 (vii)).
  위반 → `ValueError`. `slice_width_keys` = ((kind, (폭 키 오름차순, ...)), ...).
  `LayoutPdk.from_lut(lut, overhead, gap, dummy, tap, well, rule_ids)` = (`lut.spec.manufacturing_grid_m`, kind 마다 `lut.widths(lut, kind)`
  (kind 정렬), 다섯 길이(float 로), `tuple(rule_ids)`, `lut.fp`).
  **정본 생성 경로 `LayoutPdk.from_decl(lut, decl)`**(core 계약 9.5, `decl = core.read_pdk_decl(decl_path, memo)`, sky130 =
  `assets/sky130_pdk_decl.json`): `decl.value("manufacturing_grid_m")` 와 `lut.spec.manufacturing_grid_m` 의 차가 `math.ulp(선언 격자)` 를
  넘으면 `ValueError`, 아니면 `from_lut(lut, *decl.values(PDK_RULE_QUANTITIES), decl.rule_ids(PDK_RULE_QUANTITIES))`. 이때 `rule_ids` 의
  값 = 선언 식 문자열(예 `"max(poly.2, licon.1 + 2 * licon.11)"`). 상수 `GRID_QUANTITY = "manufacturing_grid_m"`.
  실측(sky130 선언 + 실 LUT, LutSpec 격자 = 선언 격자): (overhead, gap, dummy, tap, well) = (2.8e-7, 4.7e-7, 5.4e-7, 6.8e-7, 1.63e-6)
  (float 잔차 그대로), 격자를 2배로 만든 LUT 는 `ValueError`. `from_lut` 의 손으로 넘기는 길이는 toy·test 용이다.
  **사용자 ratify(2026-10-08, 오케스트레이터 전달)**: 다섯 길이 식(finger_pitch_overhead_m·row_gap_m·dummy_w_m·tap_w_m·well_spacing_m,
  `assets/sky130_pdk_decl.json`)을 사용자가 승인했다. 적용 확인 2건은 4.10(well 간격 적용 범위·dummy 폭 해석).
- `LayoutPassive(name, area_m2)`(U12): 판정 축 면적의 수동소자 블록 하나, 면적 양의 유한 수. `passives.passives_from_decl(area_decl, values)`
  가 `metrics.PassiveAreaDecl`·{이름: 값} 에서 만든다(면적 식 = `PassiveArea.area_m2` 하나, 4.10).
- `LayoutInput(devices, matching_groups, row_groups, pdk, rejected_requests=(), passives=())`(`passives` = `LayoutPassive` tuple, 이름 중복 없음). `ValueError` 조건:
  소자 이름 중복, gid·rid 중복, 행 그룹 멤버가 없는 소자, 한 소자가 두 행 그룹, 소자 (kind, body) != 행 그룹 (kind, body_net),
  어느 행 그룹에도 없는 소자, PDK 폭 키에 소자 kind 없음, 그룹 멤버가 없는 소자, `LAYOUT_ROLES` 그룹 멤버가 두 행 그룹에 걸침
  (`EXCLUDED_ROLES` 그룹은 이 검사 없음 -- 블록을 넘는 바이어스 분배가 정상), `rejected_requests` 중복.
  `rejected_requests` 원소 = **소자 이름 문자열**(그 소자의 W_request 가 MOD8 에서 거부됨), tuple. 소자 목록에 없는 이름은 검사하지 않는다
  (그 이름은 어떤 그룹 판정에도 영향이 없다).
  **box 행 폭 비 허용치는 없다**(Q8 (vi): 하드 box 게이트 폐지 -- 옛 `box_max_row_ratio` 필드 삭제).

### 4.2 `slice_density(memo, device, keys) -> tuple[SliceDensity]` (Q4 (i)(iv))

`memo` = MOD1 `LutMemo`. `keys` 순서 그대로, 키마다 finger_w = 키 x `memo.lut.spec.manufacturing_grid_m`:
1. `vgs = vgs_for_gm_id(memo, kind, 키, gm_id, L_m, vds_V, vsb_V)`, `op = op_point(memo, kind, 키, L_m, vgs, vds_V, vsb_V)`,
   `J = op.IDu / L_m`(A/m, = ID/W 그 슬라이스), `W_need = ID_A / J`,
   `tol = tol_v_table(memo, kind, 키).at(L_m, vds_V, "id_equivalent")`(다른 지표는 쓰지 않는다).
2. `SliceDensity(키, finger_w, vgs, J, W_need, float(tol), "")`.
3. 1 의 어느 조회가 `SealViolationError` 이면 `SliceDensity(키, finger_w, None, None, None, None, <그 예외 detail 의 reason>)`
   (예: `lut_no_strong_inversion_root`, `lut_axis_out_of_range`, `lut_l_not_anchor`, [r5] `lut_hermite_nonmonotone_cell`(lut 계약 4.2 --
   역산 칸이 Fritsch–Carlson 위반)). tol 이 None 이면
   `SliceDensity(키, finger_w, vgs, None, None, None, "tol_v_undefined")`. 다른 예외는 그대로 올라간다.
- 조회 캐시는 `memo` 가 한다(같은 인자 두 번째 조회 = memo hit).
- [r5] 손계산(lut 계약 **7.1 r5 toy** 슬라이스 2장, 단 `LutSpec(1e-8, (("nmos", 1e-6),), (("toyn","nmos"),), (("nmos","_n"),))` -- 최소 finger
  1e-6 이라 폭 키 (100, 200); lut 7.1 의 1.5e-6 이면 (200,) 뿐): gm_id **14.0**, L 1e-6, vds 0.5, vsb 0.0 이면 두 키 모두
  vgs = 0.5(gm/ID = 20 − 12v 의 근, 격자점), **I1 = 1e-7·e^8.55 A**(= 키 100 슬라이스(W 1e-6)의 그 점 ID, 8.55 = 20·0.5 − 6·0.25 + 0.1·0.5)
  = 5.16675443e-4 A, **J0 = I1 / 1e-6 = 0.1·e^8.55 = 516.675443 A/m**(키 200 은 ID x2 / W x2 라 같은 J), 그래서
  **W_need = (ID_A / I1) x 1e-6 m**(작성자 실측: ID_A = I1 이면 W_need = 9.999999999999953e-07 -- 상대 1e-13 이내로 비교).
  tol_V(`id_equivalent`) = 0 수준(r5 Hermite 가 2차식 ln ID 를 정확히 재현, Richardson 환산 뒤에도 0 수준; 실측 키 200 셀 7.9e-18 V) ->
  상한 = tol_V x 14 ≈ 1e-16(실측 키 100 3.3e-16, 키 200 1.1e-16), 실효 = 하한, `grid_dominated=True`. gm_id 25.0 이면 모든 키
  `lut_no_strong_inversion_root`. **r4 toy(lut 7.2)는 VGS 칸 [0, 0.5] 이 FC 위반이라 역산이 `lut_hermite_nonmonotone_cell` 로 거부되어
  모든 슬라이스가 빠진다 -- layout 오라클에 쓰지 않는다.**

### 4.3 `w_tolerance(gm_id, tol_v, finger_w_m, grid_m) -> WTolerance` (LY1, Q4 (iv))
`upper = tol_v * gm_id`, `lower = grid_m / (2 * finger_w_m)`, `effective = max(upper, lower)`, `grid_dominated = lower > upper`.
손계산: (10.0, 0.01, 1e-6, 5e-9) -> (0.0025, 0.1, 0.1, False); (10.0, 0.0, 1e-6, 1e-8) -> (0.005, 0.0, 0.005, True).
이 허용오차는 **후보 순위 기준**이다(합격 판정은 레이아웃 뒤 재검증, 4.14).

### 4.4 `finger_candidates` -- device `ly_fw_cand`
reads device `ly_device`·`ly_slices`, graph `ly_pdk`. 소자마다 tuple: `ly_slices` 순서(폭 키 오름차순)로 `reason == ""` 인 슬라이스만,
슬라이스마다 nf ∈ sorted({max(1, floor(W_need/fw)), max(1, ceil(W_need/fw))}),
`FingerCandidate(키, fw, nf, W_need, nf*fw, |nf*fw − W_need|/W_need, lower, upper, effective, grid_dominated, ok)`,
허용오차 = `w_tolerance(gm_id, 슬라이스 tol_v_V, fw, 격자)`, `ok = err <= effective`. 밖 후보도 남는다(ok=False).
같은 (gm_id, 슬라이스 tuple) 소자는 같은 tuple 객체. 사용 가능 슬라이스가 없으면 빈 tuple.

### 4.5 `pattern_select` -- graph `ly_groups`(gid 정렬 `GroupLayout` tuple), `ly_dispositions`(gid 정렬 `MatchingDisposition` tuple)
reads device `ly_device`·`ly_fw_cand`, graph `ly_pdk`·`ly_groups_in`·`ly_rejected`. 그룹마다 독립(전 그룹 판정, LY6).

0. **제외 role(Q8 (iii))**: role ∈ `EXCLUDED_ROLES` 그룹은 `ly_groups` 에 없고 `MatchingDisposition(gid, role, members,
   "excluded_from_layout_matching", 사유)` 로 `ly_dispositions` 에 간다. 사유 문자열: bias_distribution =
   `"gate shared by a diode reference and consumers in other blocks: bias distribution, not a matched pair (Q8 (iii))"`,
   feedback_shared = `"loop signal gate shared: feedback sharing, not a matched pair (Q8 (iii))"`. 그 멤버는 일반 행 소자로 배치되고
   행 matching 쌍(4.11)에도 들어가지 않는다.
1. 전제(어기면 `pattern=None`, `ok=False`, `reason` = 아래, `attempts` = (step `"precondition"` 1개)):
   - diff_pair·mirror(hub-leaf): `hub_net is None` -> `"no_hub_net"`; 멤버의 source 도 drain 도 hub 가 아님 -> `"member_not_on_hub:<이름>"`;
     hub 반대쪽(leaf) 넷이 겹침 -> `"leaf_net_shared"`. 만족하면 멤버를 hub 가 source 가 되게 세워 패턴 함수에 넘긴다.
   - branch_symmetric(Q8 (i)(ii)): 멤버의 (kind, gate) 가 모두 같지 않으면 `"branch_gate_differs"`. hub 는 보지 않고 소자 source·drain
     그대로 넘긴다.
2. 후보 조합 = 모든 멤버에게 `ok` 인 공통 폭 키 x 멤버별 그 키의 ok nf(곱집합). 조합 순서 = (행 폭 칸 수 = floor(sum(nf x (L_m + overhead)) / 격자),
   최대 err, 폭 키).
3. 패턴 호출: common-centroid -- branch_symmetric 이면 `row_swap_layout(trs, 멤버 수, 쌍, 민감도)`(4.6, 쌍 = 멤버 이름 정렬 (0,1),(2,3),...,
   민감도 `"ratio"`). 그 밖은 멤버 nf 가 모두 같고 nf >= 멤버 수면 `common_centroid_layout(trs, n_rows=None, max_candidates=총 finger)`,
   멤버 2개이고 nf 가 다르면 `n_rows=2`, 그 밖은 호출하지 않고 attempt `reason="cc_precondition"`.
   interdigitation -- `INTERDIGITATION_PATTERNS` 의 base 를 이름 정렬 순으로 보며 글자 수 = 멤버 수이고 어떤 repeat 의 글자별 개수를
   (개수 내림차순, 글자) 로 늘어놓은 것 = 멤버 nf 를 (nf 내림차순, 이름) 으로 늘어놓은 것인 첫 base 를 넘긴다. 없으면 `base=None`.
4. 행마다 `canonical_row` 로 node_sequence 정규화 -> `PatternRow`. **dx·dy** = 멤버 무게중심 x·y 의 (최대 − 최소), finger 피치 단위:
   행 r(0부터, 행 수 R), 그 행 길이 n 의 i 번째 finger 의 x = i − (n−1)/2, y = r − (R−1)/2. `centred` = dx == dy == 0(정확한 유리수).
5. 정렬 키(사전식) = 머리 + 꼬리. 머리 = (**mirror 만** 앞에: interdigitation 성립 아니면 1 (Q8 (ii)) ; 그다음 공통: centred 아니면 1,
   방법이 `pattern_table`·`rotation_exact` 아니면 1, crossover_count, isolated_pairs, residual), 꼬리 = (행 폭 칸 수, 최대 err, 폭 키,
   패턴 이름, nf tuple). **interdigitation 성립** = 패턴이 interdigitation 이고 결과 crossover_count == 0. 최선 = 최소 키.
   머리가 모두 0 인 후보가 나온 뒤 행 폭 칸 수가 더 큰 조합은 평가하지 않는다(attempts 에도 없다).
6. diff_pair·branch_symmetric(LY5, Q8 (ii)): (i) common-centroid 만으로 5의 최선을 찾고 centred 이면 채택, `reason="cc_same_W"`.
   (ii) 아니면 멤버 모두 `W_adjustable` 이고 `rejected_requests` 에 없을 때: 멤버 모두에게 사용 가능한(후보가 있는) 폭 키 중
   |키 x 격자 − max(멤버 W_need(키))/n| 최소(동률은 작은 키) 키*, `W_new = n x 키* x 격자`(n = 멤버 수), 멤버마다
   `WRequest(이름, W_need(키*), W_new, "cc_nf", gid)`, `pending=True`, `provisional=True`, `reason="w_request_pending"`,
   배치 = (i) 의 최선(없으면 pattern None), attempts 끝에 step `"w_request"`(finger_w = W_new/n, nf = n씩, reason `"cc_nf"`).
   (iii) 그 밖: attempts 끝에 step `"w_request"`(reason `"w_request_rejected"`(멤버 중 거부 있음) / `"w_not_adjustable"` /
   `"no_usable_slice"`(조정 가능하지만 공통 사용 가능 폭 키 없음)). **즉시 완화하지 않는다**(U12, LY5 마지막 문장 -- 옛 interdigitation
   완화(`relax`)·무게중심 불일치 행 swap 채택과 `relaxed` 필드를 지웠다. 완화 판정은 MOD8 몫): pattern None, `ok` False,
   **2 의 후보 조합이 하나 이상 있으면**(멤버 모두에게 ok 인 공통 폭 키가 있음) reason = (iii) 사유, 조합이 없으면 `"no_common_finger_w"`.
   (`"no_applicable_pattern"` 은 6 에서 나오지 않는다.) (i) 시도의 dx·dy 는 attempts 에 남는다.
   예: 4.15 toy 차동쌍 ID = I1(W_need 1e-6), `W_adjustable=False` -> 키 100 nf 1 조합 있음 -> reason `"w_not_adjustable"`, pattern None
   (`allowed_patterns` 와 무관).
   - LY4 `matching_L_mismatch`: 6(및 7) 어느 경로든 `GroupLayout.l_mismatch` = 멤버 L 이 모두 같으면 `()`, 아니면 ((멤버, L_m), ...) 멤버 순서
     (L 비교는 float 정확 일치 -- 같은 L 동치류는 같은 값을 받는다). 기록만이고 배치·사유를 바꾸지 않는다(L 통일은 LR2 소관).
   - pending·provisional: (ii) 경로면 배치 유무와 관계없이 `pending = provisional = True`(pattern None 이어도), 그 밖은 둘 다 False.
7. mirror: 허용 패턴 전부(`PATTERNS` 순)로 5의 최선, `reason="selected"`. 최선이 없으면 `"no_common_finger_w"`(공통 ok 폭 없음)
   또는 `"no_applicable_pattern"`.
- `GroupLayout.ok` = 채택 배치가 centred. `attempts` = 평가 순서대로 전부(`GroupAttempt(step, pattern, finger_w_m, n_fingers, W_realized_m,
  method, dx, dy, ok, reason)`, 전제 밖은 method/dx/dy None, 평가한 것은 reason `"evaluated"`).

### 4.6 `row_swap_layout(transistors, n_rows, matching_pairs, pair_sensitivity) -> dict` (Q8 (ii))
1. `apply_explicit_row_split({"row_swap": transistors}, {"row_swap": n_rows})` -- 멤버마다 nf 를 n_rows 조각(앞 조각부터 +1, 0 조각 없음).
2. 조각 행 r(0부터)마다 `row_euler(조각 소자 이름 정렬, matching_pairs, pair_sensitivity)` 의 segment 를 r 칸 순환 회전
   (segment 수 k 이면 `segments[r % k:] + segments[:r % k]`), `crossover_after` = segment 경계 직전 finger index, `canonical_row` 정규화.
3. 반환 `{"rows": [...], "method": "row_swap", "crossover_count": 행 Euler crossover_count 합, "isolated_pairs": count_isolated_pairs(rows,
   이름 정렬), "residual": common_centroid_residual(rows)}`.
손계산: E(p→q), F(r→t) 같은 gate, nf 2·2, n_rows 2 -> 행 `("E","F")`, `("F","E")`, segment 2개씩, dx = dy = 0, crossover_count 0.
nf 1·1, n_rows 2 -> 조각 행 1개(`("E","F")`)뿐 -> dx 1.0(무게중심 불일치).

### 4.7 `finger_geometry` -- device `ly_finger`
reads device `ly_fw_cand`, graph `ly_groups`·`ly_row_groups`.
- pattern 이 있는 그룹 멤버: 그 그룹의 폭 키·nf 후보, `origin="group"`, `group=gid`.
- 나머지(행 그룹 rid 정렬, 행 그룹 안 이름 정렬): 남은 소자 중 **가장 많은 소자에게 ok 인 폭 키** -> 동률이면 그 소자들의
  (그 키에서 err 최소 nf) 합 최소 -> 동률이면 큰 키. 그 키가 ok 인 소자 모두에 그 키의 (err, nf) 최소 후보를 주고 남은 소자로 반복.
  다른 행 그룹의 폭은 보지 않는다(단위셀 폴백·seed 전파 없음).
- 어떤 키도 ok 가 아닌 소자: 전체 후보 중 (err, nf, −키) 최소를 잠정으로 쓰고 `w_request = WRequest(이름, 그 후보 W_need, 그 후보 실현 W,
  "finger_quantization", None)`. 단 그 소자가 어떤 그룹의 `w_requests` 에 이미 있으면 `w_request=None`. 그 밖은 `w_request=None`.
- 후보가 하나도 없는 소자(모든 슬라이스 제외)는 `ly_finger` 에 값이 없다(4.12 가 `no_usable_slice` 로 기록).
- `DeviceFinger(name, 키, fw, nf, W_need, 실현 W, err, lower, upper, effective, grid_dominated, ok, origin, group, w_request)`.

### 4.8 `row_euler(transistors, matching_pairs, pair_sensitivity) -> dict` (변경 없음)
소자를 source·drain 넷 연결 성분(diffusion 섬)으로 나눠(섬 = 이름 정렬, 섬 순서 = 첫 이름 정렬) 섬마다: `build_graph` ->
`check_euler_condition`; 가능하면 섬 안 쌍이 있을 때 `mirror_symmetric_trail`(성공 시 "mirror"), 아니면 `hierholzer`("euler");
불가면 `find_min_crossover_layout(섬, matching_pairs=섬 안 쌍, pair_sensitivity=섬 안 쌍의 값 또는 None)`("crossover").
반환: `transistor_sequence`, `node_sequence`(`canonical_row` 결과), `segments`, `crossover_after`(각 segment 끝 finger index, 마지막 제외),
`method`(crossover > mirror > euler 우선 표기), `crossover_count`(섬별 합), `n_components`. finger 수는 바꾸지 않는다.

### 4.9 `box_verdict(rows, folds) -> BoxVerdict` (Q8 (vi) -- 기록만)
`rows` = ((id, 폭, 높이), ...). `BoxVerdict(width_ratio, elongation, total_width_m, total_height_m, widest_row, narrowest_row, folds)`:
width_ratio = 최대 폭 / 최소 폭. 행을 (폭, id) 오름차순으로 정렬해 첫 행 = `narrowest_row`, 마지막 행 = `widest_row` -- 즉 폭 동률이면
narrowest 는 **id 가 가장 작은** 행, widest 는 **id 가 가장 큰** 행(문자열 비교). 행 하나면 둘 다 그 행, width_ratio 1.0. total_width = 최대 폭, total_height = 높이 합,
elongation = max/min(두 값), `folds` 는 tuple 로 옮긴다. **ok 필드·허용치 없음**.

### 4.10 `floorplan_of(rows, bodies, pdk) -> FloorplanSummary` (Q8 (vii), 판정 축 면적)
`rows` = `RowLayout` 들(비어 있지 않음), `bodies` = {행 그룹 id: body 넷}. 격자 g = `pdk.manufacturing_grid_m`.
- 행마다 `FloorplanBlock(행 id, (행 폭 + 2 x dummy_w_m)/g, finger_w/g)` -- 행 끝 dummy 양끝 둘. **body tap 은 행마다가 아니라 행 그룹 경계에만**
  (LY10, U12): 행 그룹을 복사 함수 `pack_group_as_unit(gap = row_gap_m/g)` 로 묶은 뒤 그 외곽 오른쪽에 폭 `tap_w_m/g`, 높이 = 그룹 높이인 tap 띠를
  붙여 그룹 블록 폭 = 그룹 폭 + tap 으로 둔다(`placements` 에 `tap:<행 그룹>`; tap_w_m == 0 이면 띠 없음).
- **well 묶음 = (행 kind, 행 그룹 body 넷)**(2026-10-08 개정 -- 전에는 body 넷만이라 nmos·pmos 행이 같은 body 넷 이름을 가지면 한
  묶음으로 행 간격만 받았다). 묶음 (kind, body) 정렬 순으로 묶음마다 그룹 블록들(위 tap 포함)을 복사 함수
  `pack_floorplan(그룹 블록들, [], gap = row_gap_m/g, transistor_sequences = {행 id: 순서})`(`pack_floorplan_grouped` 가 하는 일과 같은 순서)로
  배치하고, 그 배치를 bbox 왼쪽 아래 원점으로 옮긴다.
- 묶음이 하나이고 수동소자 블록이 없으면 그 결과가 전부. 아니면 묶음마다 `FloorplanBlock("body:<kind>:<body>", 그 bbox 폭, 높이)` 와
  수동소자 블록(아래)을 복사 함수 `pack_floorplan(blocks, [], gap = max(row_gap_m, well_spacing_m)/g)` 로 배치하고 안쪽 배치를 그 자리로 옮긴다.
- **수동소자 블록(D-LY4, 사용자 결정 11·Q9)**: `floorplan_of(rows, bodies, pdk, passives=())` 의 `passives` = `LayoutPassive(name, area_m2)`
  (이름순 정렬해 사용). 블록 `passive:<이름>` = 폭 max(1, ceil(sqrt(A/g²))) 칸 x 높이 ceil((A/g²)/폭) 칸(면적 >= A, 정사각형에 가까운 격자 블록 --
  모양에 대한 PDK 선언이 없어 새 수치를 만들지 않는다). MIM 배치 여유 = 블록 사이 배치 간격(max(행 간격, well 간격)). 면적 A 는
  `passives.passives_from_decl(PassiveAreaDecl, {이름: 값})` 가 `metrics.PassiveArea.area_m2`(= 값 x PDK 선언 단위 면적 + 머리 면적, 탐색 축
  `area_search` 와 같은 식 하나)로 만든다: MIM 커패시터 = 값/밀도(PDK `mim_cap_density_f_per_m2`), poly 저항 = 값 x W_min²/R□ + 접촉 머리
  (PDK `poly_res_*`), 측정 부하(`measurement_load`)·단위 면적 미선언 소자는 만들지 않는다(탐색 축과 같은 제외, 결정 11).
  **well 간격은 well 이 다른 묶음 사이(nmos 행 대 pmos 행, 또는 같은 kind 라도 body 넷이 다른 행 -- 다른 nwell / 격리 pwell)에만 들어가고,
  같은 (kind, body) 행 사이에는 절대 들어가지 않는다**(행 그룹이 달라도 같은 well 이면 행 간격만). 묶음이 셋 이상이면 모든 쌍이 서로 다른
  well 이라 균일한 top gap 이 맞다.
- `placements` = 행 id 정렬 (id, x, y, 폭, 높이) m(폭은 dummy·tap 포함), `outline_area_m2 = bbox 폭 x bbox 높이`(수동소자 블록 포함), `grid_m = g`
  (옛 `area_tie_m2 = g²` 를 지웠다 -- ΔA_tie 는 두 점이 정한다: `area_tie.area_tie_m2(a, b) = g x max(a.bbox_width_m, a.bbox_height_m,
  b.bbox_width_m, b.bbox_height_m)`, DEC-79·DEC-95 (2). 두 점 격자가 다르면 `ValueError`), `passive_area_m2` = 수동소자 블록 면적 합,
  `aspect_ratio` = max/min(bbox 두 변), `packing_density` = 블록 면적 합 / 외곽 면적,
  `included` = (("finger_pitch_overhead", overhead, 규칙), ("row_end_dummy_x2_per_row", dummy_w, 규칙), ("body_tap_per_group", tap_w, 규칙),
  ("row_gap", gap, 규칙)) + well 묶음이 둘 이상이면 ("well_spacing_between_bodies", well, 규칙) + 수동소자 블록이 있으면
  ("passive_blocks_mim_poly_resistor", 블록 면적 합, "PassiveArea.area_m2 (PDK mim_cap_density_f_per_m2 / poly_res_*)"). 규칙 = `pdk.rule_ids` 의 그 이름 값.
- **행 끝 dummy 폭 해석(2026-10-08 검토, 선언 식 변경 없음)**: 행 폭 Σ nf x (L + overhead) 는 gate nf 개 + contact 확산 nf 개를 센다.
  양끝 dummy gate 를 두면 실제 행은 gate nf + contact 확산 nf+1 + dummy gate 둘 + dummy 바깥 확산 연장 둘이다. 그래서 늘어나는 폭 =
  overhead 하나(끝 확산 하나 더) + 2 x (dummy L + poly.7) -> 끝 하나당 `poly.1a + poly.7 + overhead/2` = 선언 `dummy_w_m` 그대로.
  dummy gate 와 마지막 gate 사이는 contact 확산 하나(= overhead = max(poly.2, licon.1 + 2·licon.11) = 0.28 µm >= poly.2 0.21 µm)라 poly
  간격을 만족한다. dummy L = poly.1a(0.150 µm) 는 periphery.csv `X.1a`("Min & max dummy_poly L is equal to min L allowed for corresponding
  device type")가 정하는 값이다(nfet_01v8·pfet_01v8 최소 L 0.15 µm). 반 피치 항은 과소 추정이 아니다. 한계(기록): lvt pfet(poly.1b 0.35 µm)
  처럼 최소 L 이 다른 소자 kind 를 쓰면 kind 별 dummy 식이 필요하고, 행 안 diffusion break(crossover)의 확산 간격(difftap.3)은 행 폭에 없다.

### 4.10a `diffusion_geometry(rows, devices, pdk) -> tuple[DeviceDiffusion]` (LY8, DEC-89 (5)·DEC-91 (2), U12 D-LY3)
`ly.diffusion[dev]` = 소자별 finger 하나 평균 확산 기하 `DeviceDiffusion(name, finger_w_m, n_fingers, ad_m2, as_m2, pd_m, ps_m)`(소자 이름순).
엔진 접합 용량 `metrics.DiffusionGeometry(finger_w_m, ad_m2, as_m2, pd_m, ps_m, m = n_fingers)` 과 오라클 `devices[].diffusion{ad_m2, as_m2,
pd_m, ps_m}`(C3·C22)이 같은 값을 쓴다(소비자 배선 = MOD8, `RealizedDevice.diffusion` 으로 실어 보낸다).
- 입력: 최종 행(접기·재구성 뒤) 각각의 diffusion 섬(`segments`; 없으면 행 전체가 한 섬) -- 섬 안 finger k 개와 영역 k+1 개
  (영역 j = `node_sequence[j]`, finger i 는 영역 i 와 i+1 사이). 영역 길이 D = `pdk.finger_pitch_overhead_m`(행 폭 식이 finger 마다 접촉 확산 하나를
  세는 그 양), 영역 폭 = 행 finger_w W.
- finger 마다 두 영역(소자 source 와 같은 넷인 쪽 = source 쪽, 같은 넷이 양쪽이면 왼쪽을 source) 에서: 영역에 닿는 finger 수 q(공유 = 2, 섬 끝 = 1)
  로 나눠 면적 += W·D/q, 둘레 += W(자기 게이트 쪽 변) + 2D/q(위·아래 STI 변) + (섬 끝이면 W: 반대쪽 끝 변). BSIM4 perMod=1 규약(둘레에 게이트 쪽 변
  포함, `junction_cap` 이 `PD − Weffcj` 를 STI 측벽으로 씀). 섬 끝 반대쪽 변은 행 끝 dummy·섬 사이 break 의 게이트 변이고 dummy 는 넷리스트에 없으므로
  그 변과 영역 전체를 finger 에 합산한다(한계: dummy 가 실제 소자로 추출되면 절반씩 나뉜다).
- 소자 값 = 모든 행·섬·finger 합 / n_fingers. 손계산 예: 한 행 (A, B), 노드 (da, h, db), A.source = h, W = 1 µm, D = 0.28 µm -> A 의 drain 영역 da =
  섬 끝: ad = W·D = 0.28 pm², pd = W + 2D + W = 2.56 µm; source 영역 h = 공유: as = W·D/2 = 0.14 pm², ps = W + D = 1.28 µm.

### 4.11 `compose_rows` -- graph `ly_rows`(`RowsLayout(rows, box, fold_attempts, merge_decisions, rebuilt_groups)`), `ly_floorplan`
reads device `ly_device`·`ly_finger`, graph `ly_groups`·`ly_groups_in`·`ly_row_groups`·`ly_pdk`.
행 matching 쌍 = `ly_groups_in` 중 `LAYOUT_ROLES` 그룹(gid 정렬) 멤버를 이름 정렬해 (0,1),(2,3),... 로 묶은 것, 민감도 = diff_pair `"offset"`,
그 밖 `"ratio"`. **matching 소자** = `LAYOUT_ROLES` 그룹 멤버.
1. 초기 행(행 그룹 rid 정렬): pattern 있는 그룹(gid 정렬, 멤버 ⊂ 행 그룹)의 i 번째 패턴 행 -> 행 id `"<rid>/<gid>/<i>"`, method
   `"pattern:<방법>"`, `walk_ok` = segment 마다 `check_walk_sequence(segment 순서, segment 안 finger 수의 Transistor)` 모두 ok,
   crossover_count = len(crossover_after), `group=gid`, `matching=True`. 나머지 소자(`ly_finger` 값이 있는 것)는 폭 키별 행 `"<rid>/w<키>"`,
   `row_euler`, `group=None`, `matching` = 그 행에 matching 소자가 있음. 행 폭 = sum(nf x (L_m + overhead)), 높이 = finger_w,
   `devices` = ((이름, 그 행 finger 수), ...) 이름 정렬.
2. **hub 병합(Q8 (viii))**: `group is None and not matching` 인 행을 (kind, body, 폭 키) 로 나눠(정렬 순) 행이 둘 이상인 묶음마다
   그 행들의 Transistor 로 `find_hub_merge_candidates` -> 후보 (kind, 넷) 를 넷 이름 정렬 순으로: 그 후보 소자가 지금 들어 있는 행들
   (정렬, 이미 합친 행 포함)이 둘 이상이면 그 행들의 소자 전부를 `row_euler` 한 행(id = 행 id 들을 `"+"` 로 이은 것, 행 그룹 = 첫 행의
   행 그룹)으로 합친 시험안을 만들고, 판정 축 면적(`floorplan_of`)이 **줄면** 채택. 시도마다
   `MergeDecision(행 id tuple, 넷, merged, "area_decreased"|"area_not_decreased", 전 면적, 후 면적, MERGE_NOISE_NOTE)`.
   노이즈 결합 우려는 거부 사유로 쓰지 않는다(note 기록만).
3. **box 개선(Q8 (v)(vi))** -- 목적 = 외곽 면적 A(현재 행 집합의 `floorplan_of`). 2 뒤의 행을 (−폭, id) 순으로 한 번씩:
   - `group` 이 있는 행(그 그룹 첫 등장만): 패턴이 common-centroid(행 swap 포함)이면 재구성: k = (현재 그 그룹 행 수 + 1) .. (멤버 최대 nf)
     마다 `row_swap_layout(trs, k, ...)`(branch_symmetric) 또는 `common_centroid_layout(trs, n_rows=k, max_candidates=총 finger)`,
     새 행 id `"<rid>/<gid>/<i>"`, Euler(walk)·matching 재판정: walk 실패 또는 max(dx, dy) > 현재 max(dx, dy) 또는 행 crossover 최대 증가면
     `FoldAttempt(... "rebuild", k, 면적, dx, dy, False, "matching_worse")` 로 남기고 다음 k. 아니면 `"evaluated"`, 직전 채택 후보 면적
     이상이면 멈춘다. 가장 작은 면적이 현재 A 보다 작으면 적용(그 시도 `adopted=True, reason="adopted"`) + `GroupRebuild(gid, k, method, dx, dy)`.
     interdigitation 패턴은 `FoldAttempt(행 id "<rid>/<gid>", "rebuild", 현재 행 수, A, None, None, False, "pattern_not_rebuildable")`.
   - `group` 없고 `matching` 인 행: 자동으로 접지 않는다 -- `FoldAttempt(id, "fold", 1, A, None, None, False, "matching_row_not_auto_folded")`.
   - 그 밖(matching 없음): n = 2, 3, ..., (그 행 최대 nf) 로 `apply_explicit_row_split({id: 행 소자}, {id: n})`, 조각마다 `row_euler`
     (조각 id = `"<id>_split<j>"`, 복사 함수 규칙), `FoldAttempt(id, "fold", n, 면적, None, None, False, "evaluated")`; 면적이 직전 n 보다
     줄지 않으면 멈추고, 가장 작은 면적이 현재 A 보다 작을 때만 적용(`folds` 에 (id, n), 그 시도 adopted).
4. 행은 id 정렬, `box = box_verdict(((id, 폭, finger_w), ...), folds)`, `ly_floorplan` = 최종 행의 `floorplan_of(수동소자 블록 포함)`,
   `ly_diffusion` = 최종 행의 `diffusion_geometry(rows, devices, pdk)`(LY8, 아래 4.11a).
   초기 행이 하나도 없으면(모든 소자에 사용 가능 슬라이스 없음) `ValueError`.
   같은 행 집합 내용의 `floorplan_of` 와 같은 행 내용의 `row_euler` 는 블록 호출 안에서 한 번만 계산한다(memo).

### 4.12 `run_layout(layout_input, memo, design_point, previous=None, *, donors, counters) -> LayoutResult` (설계 40 v1.6 §2.4.7·§2.4.8, U17 ①)
[XRUN-F1 B] `donors`·`counters` = 필수 키워드(기본값 없음, 빠지면 `TypeError`) -- 실행 하나의 블록 결과 색인·계수(`place_layout` 이 `converge_point` 의 `sctx.dc` 에서 받아 넘긴다). 네 계산 블록 호출에 그대로 쓴다.
레이아웃 필드는 그 **설계점 스냅샷**(봉인 S2)의 S2 `layout` 필드다. 별도 lineage(옛 `GraphSnapshot.empty(LY_WRITERS)`)는 없다.
1. `memo.lut.fp != layout_input.pdk.source_fp` -> `ValueError`. `design_point` 가 GraphSnapshot 이 아니면 `TypeError`.
2. 스냅샷 = `previous.snapshot`(있으면 -- 같은 설계점 위 앞 호출. 레이아웃 재시도는 같은 설계점 lineage 의 새 스냅샷이다. 레이아웃 writer 를 뺀
   block_version 이 `design_point` 와 하나라도 다르면 `ValueError`) 아니면 `design_point.extend_writers(설계점 권한표 ∪ LY_WRITERS)`.
   writer `"ly_input"`, 입력 버전 `fp_of(layout_input)` 으로
   device `ly_device`({이름: LayoutDevice}), graph(key `"layout"`) `ly_pdk`·`ly_groups_in`(입력 tuple 그대로)·`ly_row_groups`·
   `ly_rejected`(정렬 tuple)·`ly_passives`(이름순 `LayoutPassive` tuple) 를 쓴다.
3. 슬라이스: 버전 = `fp_of((memo.lut.fp, pdk.slice_width_keys, ((이름, kind, L, ID, gm_id, vds, vsb), ...) 입력 순))`. 스냅샷의
   `block_version("ly_slice_density")` 가 같으면 건너뛰고, 다르면 소자마다 `slice_density(memo, 소자, 그 kind 폭 키)`(같은 (kind, L, ID, gm_id,
   vds, vsb) 는 한 번) 를 device `ly_slices` 에 쓴다.
4. 블록 순서 `finger_candidates` -> `pattern_select` -> `finger_geometry` -> `compose_rows`. `computed_blocks` = 이번 호출에서 값을 쓴 writer 이름 -- 계산 또는 이식
   (`"ly_slice_density"` 를 다시 계산했으면 맨 앞, 그다음 block_version 이 바뀐 블록 순서대로; 판정은 호출 전후 block_version 비교 그대로이고 계산·이식 구분은 `RunCounters` 행이 맡는다).
5~8 은 `run_layout` 결과가 아니라 **필드 파생 출력** `layout_outputs(snapshot) -> LayoutOutputs(review_needed, devices, coverage_ok,
coverage_missing, w_requests, w_invariant_ok, revalidation)` 이다(필드에서 읽어 만드는 반환값, 저장하지 않는다). `LayoutResult` =
`(snapshot, computed_blocks)` 뿐이고, groups·dispositions·rows·box·folds·merges·floorplan·diffusion 은 스냅샷의 `ly_groups`·`ly_dispositions`·
`ly_rows`·`ly_floorplan`·`ly_diffusion` 필드로 읽는다.
5. `devices` = 소자 이름순(`ly_device` key 순) `DeviceLayout(이름, finger_w, nf, ((행 id, nf), ...) 행 id 순, W_m(참고), W_need, 실현 W, err, lower, upper, effective,
   grid_dominated, origin, excluded_slices = ((키, 사유), ...) 제외된 슬라이스)`. `ly_finger` 값이 없는 소자는 finger_w·nf·W_need 이후
   숫자 필드가 None, rows `()`.
   `w_requests` = 그룹 요청 + 소자 finger_quantization 요청 + `ly_finger` 없는 소자마다 `WRequest(이름, W_m, W_m, "no_usable_slice", None)`,
   (device, reason) 정렬. `coverage_ok`·`coverage_missing`(정렬) = `check_stick_diagram_coverage(입력 이름, {행 id: 행 소자 이름})`.
   `w_invariant_ok` = 모든 소자가 `ly_finger` 를 갖고 (행별 nf 합 == nf) 이고 (err <= effective 또는 그 소자 이름의 W_request 있음).
6. `review_needed`(결과 첫 필드, Q8 (iv)) = `groups` 순으로 role ∈ `CC_REQUIRED_ROLES` 이고 pattern None 이고 pending 아닌
   그룹마다 `ReviewItem(gid, role, reason, dx, dy)` -- dx·dy 는 그 그룹이 4.11 3 에서 재구성됐으면 `GroupRebuild` 값, 아니면 그룹 값.
7. (필드) `ly_dispositions`, `ly_rows`(rows·box·fold_attempts·merge_decisions·rebuilt_groups), `ly_floorplan`,
   `ly_diffusion`(`DeviceDiffusion` tuple, 소자 이름순). 재검증 요청의 `RealizedDevice.diffusion` = 그 소자의 `DeviceDiffusion`.
8. `revalidation` = 4.14.

### 4.13 불변식 (test 대상)
1. **보존량 (ID, gm/ID, L)(LY1, Q4 (i))**: `DeviceLayout.W_need_m` = 그 소자 finger_w 슬라이스의 `ID_A / J_slice`; 모든 배치 소자
   `W_err_rel = |W_realized − W_need| / W_need` 이고 `W_err_rel <= W_tol_effective` 또는 그 소자 `W_request` 존재. 행 접기·crossover·hub 병합·
   재구성 전후 소자별 행 finger 합 불변. 같은 matching 그룹 멤버는 같은 finger_w(같은 슬라이스).
2. **실효 허용오차(Q4 (iv))**: `W_tol_effective = max(W_tol_upper, W_tol_lower)`, `grid_dominated = W_tol_lower > W_tol_upper`,
   `W_tol_upper = (그 슬라이스 id_equivalent tol_V 셀) x gm/ID`.
3. **W 를 바꾸지 않는다(LY3)**: `DeviceLayout.W_m` = 입력 W_m. W 변경은 `w_requests` 로만.
4. **행별 finger_w(LY2·L6)**: 한 행의 finger_w 는 하나, 비그룹 소자의 폭 키는 같은 행 그룹 소자의 ok 후보에서만(hub 병합은 같은 폭 키 행끼리만).
5. **전 그룹 판정(LY6)**: `groups` 는 `LAYOUT_ROLES` 입력 그룹 전부(gid 정렬), `matching_dispositions` 는 `EXCLUDED_ROLES` 입력 그룹 전부.
6. **즉시 완화 없음(LY5, U12)**: 차동쌍·branch_symmetric 은 무게중심이 안 맞고 W_request 도 못 내면 pattern None 이다 -- attempts 에
   step `"cc_same_W"`(또는 후보 없음)와 `"w_request"` 가 있고 `"relax"` 단계·`relaxed` 필드는 없다. 그 그룹은 `review_needed` 에 있다.
7. **자동 접기 범위(Q8 (v))**: `"fold"` 로 adopted 된 행에는 matching 소자가 없다. matching 패턴 행은 `"rebuild"` 로만 바뀌고, 채택된 rebuild 의
   max(dx, dy) 는 원래 이하.
8. **하드 box 게이트 없음(Q8 (vi))**: 접기·재구성·병합 채택은 판정 축 외곽 면적 감소로만 정해진다(채택 시도의 면적 < 그 시점 면적).
9. **결정론(NFR-4)**: 같은 입력이면 `PYTHONHASHSEED` 와 무관하게 레이아웃 필드 값(`value_fp`)과 `layout_outputs` 가 같다.
10. **필드 = 캐시(L11)**: 같은 설계점·같은 입력·같은 memo LUT 로 `previous` 를 주면 `computed_blocks == ()` 이고 스냅샷이 `previous.snapshot` 그대로다.
    `rejected_requests` 만 바꾸면 `ly_slice_density`·`ly_finger_candidates` 는 재사용, `ly_pattern_select` 부터 다시 계산될 수 있다.
    소자 하나의 ID 만 바꾸면 `ly_slice_density` 부터 다시 계산한다. 각 블록 행 `recomputes_same_input == 0`(`RunCounters`).
11. coverage: 모든 소자에 사용 가능 슬라이스가 있으면 `coverage_ok` 이고 `coverage_missing == ()`.
12. **재검증 요청(Q4 (ii))**: `revalidation.required is True` 가 W_request 유무와 무관하게 항상 참.

### 4.14 레이아웃 뒤 재검증 요청 (Q4 (ii)(iii)) -- 소비자 = MOD8 `convergence` (U14)
- `Revalidation(required=True, status=REVALIDATION_PENDING ("pending_wiring"), seals=REVALIDATION_SEALS ("seal_1".."seal_8"),
  devices = 이름순 배치 소자의 RealizedDevice(`layout_outputs`), consumer=REVALIDATION_CONSUMER, reason=REVALIDATION_PENDING_REASON)`.
- `RealizedDevice(name, kind, finger_w_key, finger_w_m, n_fingers, W_need_m, W_realized_m, ID_A, gm_id, L_m, vds_V, vsb_V, recalibrate_id,
  recompute_node_voltages)`: `recalibrate_id = not diode`(Q4 (iii): diode 는 ID 재보정 불필요), `recompute_node_voltages = True`(모든 소자 --
  diode 도 노드전압·봉인은 다시 계산).
- **소비 계약([U14] 배선됨)**: MOD8 `convergence.converge_point` 가 `run_layout` 결과 스냅샷의 실현 기하(폭 키·nf·실현 W = `ly_finger`, 확산 = `ly_diffusion` 필드 = `RealizedDevice.diffusion`
  과 같은 값)로 평가 커널을 1회 다시 돌리고(`search.evaluate(geometry=)`) 봉인 1~8·spec 제약 행을 재확인한 뒤, 통과하면 그 점으로 다시 놓아 같은 기하가 나오는 고정점에서
  freeze 하고 위반하면 W_request 응답 대기 그룹의 요청을 거부(`rejected_requests`)한다. LY1 허용오차는 후보 순위 기준일 뿐이다. `LayoutResult` 가 불변이라 `status` 는 늘
  `"pending_wiring"` 이고 소비 결과는 `convergence.ConvergedPoint` 에 기록된다(`convergence/CONTRACT.md`).
- 계획 LY7('평가 커널은 W_request 가 있을 때만')은 Q4 (ii)로 바뀐다: MOD7 결과마다 재검증 1회는 W_request 와 무관하게 돈다. 레이아웃
  재시도(기하 판정)는 여전히 전기 재계산 없이 돈다.

### 4.15 손계산 오라클 ([r5] toy -- lut 계약 **7.1 r5 toy** LUT, 최소 finger 1e-6)
`spec = LutSpec(1e-8, (("nmos", 1e-6),), (("toyn","nmos"),), (("nmos","_n"),))`(lut 7.1 의 LutSpec 에서 최소 finger 만 1e-6), 슬라이스 2장
(lut 7.1 r5 toy `toy_w100`(W 1e-6)·`toy_w200`(W 2e-6, ID·GM·GDS x2)), 기준 LUT 는 lut 7.1 그대로,
`memo = LutMemo(lut, point=…, curve=…, root=…)`, `pdk = LayoutPdk.from_lut(lut, 0.0, 0.0, 0.0, 0.0, 0.0, rules)`(rules = 다섯 이름에 아무
규칙 문자열) -> 폭 키 (100, 200), finger_w 1e-6·2e-6. 소자 공통: kind nmos, body "sub", L 1e-6, **gm/ID 14.0**, vds 0.5, vsb 0.0,
diode False, adjustable True, W_m 4e-6(참고). **전류 단위 I1 = 1e-7·e^8.55 A = 5.16675443e-4 A**(4.2). 아래 소자 전류는 `ID_A = c x I1` 로
주고, 4.2 에 의해 **W_need = c x 1e-6 m**(두 키 모두 같은 J0; 실측 상대 오차 ~5e-15 -- 정수배 err 은 0 이 아니라 ~5e-15 이므로 ok 판정에는
영향 없음). tol_V ≈ 0 이라 상한 ≈ 1e-16, 실효 = 하한(키 100: 0.005, 키 200: 0.0025), `grid_dominated=True`.
(r4 toy 에서 쓰던 `ID 1e-6 -> W_need 1e-6`, gm/ID 10 은 r5 에서 성립하지 않는다 -- r4 toy 는 역산이 FC 위반으로 거부된다.)
- 소자 C(s x, d y, c 0.75): 후보 키 100 nf 1(W_need 0.75e-6, err 1/3, ok False), 키 200 nf 1(err 5/3, ok False) -> ok 없음 ->
  `finger_quantization` 요청 `WRequest("C", W_old ≈ 0.75e-6, 1e-6, "finger_quantization", None)`(err 최소 = 키 100 nf 1).
- 차동쌍 g1 = A(s h, d da), B(s h, d db), hub "h":
  - c 2 씩: 조합 순서(행 폭 칸 수)상 키 200 nf (1,1)(200 칸, W_need 2e-6 = 1 x 2e-6, err ≈ 0, ok)이 키 100 nf (2,2)(400 칸)보다 먼저
    평가되어 `cc_precondition`(nf 1 < 2), 그다음 키 100 nf (2,2) -> `rotation_exact`, 행 `("A","B")`/`("B","A")`, dx = dy = 0, `reason="cc_same_W"`, ok.
    attempts = (("cc_same_W", "cc_precondition"), ("cc_same_W", "evaluated")).
  - c 1 씩: 키 100 nf 1 만 ok -> cc 는 nf 1 < 2 라 `cc_precondition` -> adjustable 이면 `w_request`: 키* = |키 x 1e-8 − 1e-6/2| 최소 = 100,
    `WRequest(A, W_old ≈ 1e-6, 2e-6, "cc_nf", "g1")`·B 같음, `pending = provisional = True`, pattern None, `review_needed` 에 없음(pending).
    `W_adjustable=False` 면 attempts `cc_same_W`(cc_precondition) -> `w_request`(w_not_adjustable), 이후 완화 없음: pattern None,
    reason `"w_not_adjustable"`, `review_needed` = (ReviewItem("g1", "diff_pair", "w_not_adjustable", None, None),)
    (`allowed_patterns` 와 무관 -- 옛 interdigitation 완화는 지웠다).
- branch_symmetric g2 = E(s p, d q), F(s r, d t), 같은 gate "gc", c 2 씩: 키 100 nf 2 -> `row_swap`, 행 `("E","F")`/`("F","E")`, dx = dy = 0,
  `reason="cc_same_W"`(키 200 nf 1 조합은 조각 행 1개라 중심 불일치로 먼저 평가된다). gate 를 다르게 하면 `precondition` `"branch_gate_differs"`.
- bias_distribution g3 = (C, D): `ly_groups` 에 없고 `matching_dispositions` 에 사유와 함께 있다. C·D 는 일반 Euler 행.
- hub 병합: 같은 body 의 행 그룹 r(C(s x, d y), D(s y, d z), c 1 씩) 과 r2(G(s y, d w), c 1) -> 두 행 `r/w100`·`r2/w100` 이 넷 "y" 후보,
  합친 행 소자 C·D·G -> `MergeDecision(("r/w100","r2/w100"), "y", merged, ...)` 이 하나 있고 merged 는 (후 면적 < 전 면적)과 같다.
- 접기: 행 그룹 r3 의 H(s k, d m, c 12) 혼자 -> 키 200 nf 6 행 `r3/w200` -> "fold" 시도 n = 2, 3, ... 가 기록되고, 채택이 있으면 그 면적이
  그 시점 면적보다 작다(H 의 행별 nf 합 = 6 유지).
- 작성자 실측(참고, 판정 아님 -- PDK 길이 모두 0): 위 r/r2/r3 입력(C·D·G·H 만)에서 merged = False(면적 감소 없음), "fold" 시도 n = 2, 3
  둘 다 미채택, `w_invariant_ok` True.

### 4.16 결정·범위 밖·다른 패키지 대기
- MOD8(W_request 를 받아 sizing 재평가·`rejected_requests` 를 채워 다시 부르기)·재검증 실행(4.14)은 다음 단계.
- 패턴 행은 `apply_explicit_row_split` 로 접지 않는다(matching 배치 보존) -- 패턴 함수로만 재구성한다(4.11 3).
- 블록 단위 재사용(core `compute_block`): 한 블록이 읽는 열 중 하나라도 바뀌면 그 블록 전체를 다시 계산한다(소자별 부분 재사용은 MOD8 단계 과제).
- **다른 패키지 생산자 대기(레이아웃은 소비만 구현)**:
  - graph(MOD3): `branch_symmetric` 유도(stack 전파: 확정 쌍 위 같은 kind·같은 gate 쌍, 증거 {base_pair, shared_gate}), `bias_distribution`·
    `feedback_shared` 분류, 차동쌍 유도에서 바이어스 형제 제외, matching 레코드 status(derived·ratified 만 레이아웃에 전달), stage 별 행 그룹
    (`graph/row_groups.py` -- 같은 (kind, body)의 행 그룹이 여럿일 때만 hub 병합이 stage 를 넘는다). 현재 graph 에는 `rel_matching_ratio`·
    `rel_matching_offset` 만 있고 위 role 생산자가 없다.
  - core: `read_pdk_decl` 은 있다(core 9절) -- 정본 경로는 `LayoutPdk.from_decl`(4.1). `run_layout` 을 부르는 엔진 쪽 호출자(MOD8·pipeline)는 아직 없다.
  - MOD5·MOD6·MOD8: 평가 커널·봉인 1~8·수렴 루프(4.14 소비자).
- `pack_floorplan` 의 H 스윕은 면적이 아니라 aspect ratio 최소를 고른다(복사 본문) -- 판정 축 면적은 그 결과의 bbox 다. 복사 본문 리터럴의
  A_L 민감도는 4.17.

### 4.17 복사 floorplan 본문 리터럴의 A_L 민감도 (Q8 (ix) -- 작성자 실측, 참고·판정 아님)
- 방법: `floorplan_pack.py` 사본(저장소 밖 임시 모듈)에서 리터럴 하나씩 ±1 단계(정수 ±1, 소수 끝자리 ±1, 1e-9 는 x10·/10) 바꿔
  `floorplan_of` 의 `outline_area_m2` 를 원본과 비교. 대상: `pack_floorplan` H 스윕 0.3·2.2, `height_steps` 40(grouped·pack_floorplan),
  `width_tolerance` 2.0(grouped·pack_floorplan), `width_steps` 60(`skyline_pack_best_width`·`pack_to_height`), 반올림 자릿수 3, 맞춤 여유 1e-9.
  (0.5 는 제곱근 지수, 0.6·100 은 `evaluate_row_split_candidates` 보고용이라 면적과 무관.)
- 입력: 무작위(seed 1~7) 행 6·12·16·20·30·30·45개, 행 그룹 4·8개, body 2개, 격자 5e-9, PDK 길이(행 간격 0.27 µm, dummy 0.15 µm,
  tap 0.17 µm, well 1.27 µm).
- 결과(2026-10-07): 7 입력 x 20 변경 = 140 경우 모두 ΔA_L = 0(격자 한 칸 기준 grid^2·grid x 긴 변 둘 다 미만). 따라서 Q8 (ix) 의
  '본문 수정 승인 재요청' 조건은 발동하지 않았다. 큰 변경(예: 2.2 -> 0.1)은 A_L 을 바꾸므로(+28 %) 계측 자체는 유효하다.
  test 화(`test_floorplan_literal_sensitivity.py`)는 test 작성자 몫.

### 4.18 실 LUT 실측 -- 파일럿 T1 행 M3a (작성자 실측, 참고·판정 아님)
- [r5 주의] 아래 수치는 2026-10-07 **r3/r4 LUT(VGS·VDS 다선형, 선형 LOO tol_V)** 시점 값이다. r5(Hermite 보간·Richardson 환산 tol_V)에서는
  W_need·tol_V·선택 키가 달라질 수 있어 재측정 전에는 기대값으로 쓰지 않는다(옛/새 규칙의 비교 방법만 참고).
- 입력: 실 LUT(`wt/_drafts/engine/lut_slices/manifest.json`, nmos 폭 키 20개, 격자 5e-9), 파일럿 `engine.json` sizing 의 M3a·M3b(L 1 µm,
  gm/ID 15, VDS 0.2, ID 4.98 µA)·M4a·M4b(L 1.4 µm -> 측정 편의상 가장 가까운 앵커 1.5 µm), 행 그룹 하나, matching 그룹 없음.
- 옛 규칙(7ac0210: err = |nf fw − W_m|/W_m, 상한 = 기준 슬라이스(키 1000) id_equivalent 셀 x gm/ID): 상한 M3a 0.492, M4a 0.074 ->
  네 소자 모두 키 1000 nf 1 선택, M3a 오차 43.1 %(통과). 같은 선택의 **실제** 오차(그 슬라이스 W_need 대비): M3a 47.4 %, M4a 10.2 %
  -- M4a 는 자기 상한 7.4 % 를 넘는데도 옛 지표(4.1 %)가 숨겼다.
- 새 규칙: M3a W_need(fw) 가 슬라이스에 따라 3.18~4.45 µm(키 1400~148, 참고 W 3.49 µm 대비 −9 %~+27 %). 키 1000 이 M4a·M4b 에서
  ok 가 아니게 되어(W_need 대비 10.2 % > 7.3 %) 공통 키가 600 으로 바뀌고 M3a 오차 17.1 %, M4a 1.4 %. M3a·M3b 를 branch_symmetric
  그룹으로 주면 행 swap 키 336 nf 2, 오차 8.2 %, dx = dy = 0.
- 남는 한계: M3a 동작점의 id_equivalent 셀이 30~33 mV 라 상한이 45~50 % 다(이 행 다른 소자가 없으면 키 1000 nf 1 의 47 % 도 순위
  허용 안). 이 크기의 실현 오차를 막는 것은 4.14 재검증(MOD8 `convergence`)과 tol_V 측정 정의(SYNTHESIS T05·Q2) 몫이다.
- 비용: 첫 `run_layout` 490 s 중 대부분이 슬라이스 20장의 `tol_v_table`(장당 약 14~24 s, `LutMemo` derived 영역에 캐시 -- 같은 memo
  재호출에서는 다시 계산하지 않는다).
