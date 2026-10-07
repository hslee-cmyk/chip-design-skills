# gmid_engine.layout 동작 계약 (test 작성용) -- 1단계: 복사 단위 + canonical_rows, 2단계: 행 구성(4절)

- 대상: 0~3절 = 1단계 파일 14개(아래 0절 표). **4절 = 2단계 행 구성 7단계·입력/출력 계약·graph 레이아웃 필드**(파일 12개).
  MOD8 W_request 루프는 다음 단계라 이 계약에 없다.
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
| `_copy_manifest.py` | 0 | (데이터, 공개 정의 0) | `COPY_SOURCE`, `COPIED_DEFINITIONS`(59행) |
| `transistor.py` | 0 | `Transistor` | 복사 |
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
1. 행 수 59, (새 파일, 정의 이름) 중복 없음, DM 1.1 표와 같은 집합.
2. 행마다 `layout/<새 파일>` 의 같은 이름 최상위 정의가 정확히 1개 있고 그 해시 = manifest 해시.
3. SD 가 저장소에 있으면: SD 의 같은 이름 최상위 정의 해시 = manifest 해시, 그 노드의 `(lineno, end_lineno)` = manifest 행 범위
   (데코레이터 줄 제외). -> 3자 일치. SD 삭제 뒤에는 2자(manifest·새 파일).
4. 복사 파일(manifest 의 새 파일 12개)의 최상위 문장 = 모듈 docstring + import + manifest 등록 정의 + (`_helpers_hubleaf.py` 만)
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
1. 정의마다: 규칙 D 위반 리터럴의 정렬 다중집합 = manifest tuple(현재 합계 61개).
2. layout 전체의 규칙 D 위반은 모두 manifest 등록 정의 안에 있다(등록 밖 0). `canonical_rows.py`·`_copy_manifest.py` 는 0.
3. 등록 정의별 현재 집합(이 표가 바뀌면 복사 본문이 바뀐 것 -- 해시도 깨진다):

| 정의 | 리터럴 |
|---|---|
| `_repair_row_parity` | 50 |
| `_common_centroid_residual` | 0.5 |
| `_hubleaf_sequence_node_path` | 2 |
| `_MAX_CROSSOVER_PAIRING_NODES` | 8 |
| `_pair_odd_nodes_by_mirror`, `find_min_crossover_layout`, `check_euler_condition`, `_try_pattern_table_match` | 2 |
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

DM 8절 2 기본안 = 'lint 예외를 `_copy_manifest.py` 등록 정의로 한정 + 예외 리터럴 집합 고정'. 현재 `tests/structure` 검사기에는
manifest 예외 메커니즘이 없어서 아래가 FAIL 이다(모두 manifest 등록 정의 안, 등록 밖 0).

| 규칙 | 위반 수 | 위치 |
|---|---|---|
| D 숫자 리터럴 | 61 | 1.1 표 그대로 |
| E 회로 이름 | 12 | `'A'`·`'B'` 문자열(패턴 글자)이 library 한 회로의 넷 이름 `A`·`B` 와 전체 일치: `_common_centroid_from_pattern_table` 8, `_try_pattern_table_match` 2, `INTERDIGITATION_PATTERNS` 2 |
| G 모듈 수준 가변 객체 | 2 | `INTERDIGITATION_PATTERNS`, `COMMON_CENTROID_PATTERNS`(dict 리터럴 -- `MappingProxyType` 으로 감싸면 해시가 깨진다) |

A·B·C·F 는 위반 0. H(마커 `structure_test_mapping`)는 test 파일 14개 누락(이 계약으로 작성할 test).

---

## 4. 행 구성 (2단계) -- `run_layout` 과 계산 블록 5개

근거: DM 2절(입력 인터페이스)·3절(행 구성 7단계)·4절(graph 레이아웃 필드), 계획 N3.17 LY1~LY7·'레이아웃 입력·출력 계약',
core 계약 5·6절(GraphSnapshot·`compute_block`), lut 계약 1.6(`widths`)·5절(tol_V `id_equivalent`).
단위: 길이·폭 m, 면적 m^2, 전압 V. **폭 키** = finger_w / 제조 격자(정수, LUT 슬라이스 폭 키와 같은 것).

### 4.0 파일·층·진입점 (`_module_map.LAYERS` layout 층 7~10, 층 0~2 에 더한 파일 포함)

| 파일 | 층 | 진입점 / 종류 | graph 필드(writer) |
|---|---|---|---|
| `_ly_fields.py` | 0 | 상수 표(공개 정의 0) -- 필드 이름·`LY_WRITERS`·`BLOCK_WRITERS` | -- |
| `contract_input.py` | 0 | 데이터 선언: `LayoutDevice`·`MatchingGroup`·`RowGroup`·`LayoutPdk`(`from_lut`)·`LayoutInput`, 상수 `KINDS`·`ROLE_DIFF_PAIR`·`PATTERN_COMMON_CENTROID`·`PATTERN_INTERDIGITATION`·`PATTERNS` | -- |
| `contract_output.py` | 0 | 데이터 선언: `FingerCandidate`·`WRequest`·`GroupAttempt`·`PatternRow`·`GroupLayout`·`DeviceFinger`·`RowLayout`·`BoxVerdict`·`RowsLayout`·`FloorplanSummary`·`DeviceLayout`·`LayoutResult` | -- |
| `w_tolerance.py` | 1 | `w_tolerance` | -- |
| `finger_candidates.py` | 2 | `finger_candidates`(@compute_block) | device `ly_fw_cand`(`ly_finger_candidates`) |
| `box_shape.py` | 7 | `box_verdict` | -- |
| `pattern_select.py` | 7 | `pattern_select`(@compute_block) | graph `ly_groups`(`ly_pattern_select`) |
| `row_euler.py` | 7 | `row_euler` | -- |
| `finger_geometry.py` | 8 | `finger_geometry`(@compute_block) | device `ly_finger`(`ly_finger_geometry`) |
| `rows.py` | 8 | `compose_rows`(@compute_block) | graph `ly_rows`(`ly_rows`) |
| `floorplan.py` | 9 | `floorplan`(@compute_block) | graph `ly_floorplan`(`ly_floorplan`) |
| `run.py` | 10 | `run_layout` | 입력 필드(`ly_input`) |

공개 API(`gmid_engine.layout.__all__`): `LayoutDevice`, `LayoutInput`, `LayoutPdk`, `LayoutResult`, `MatchingGroup`, `RowGroup`,
`run_layout`. 파일별 test 는 파일 모듈을 직접 import 해도 된다(1단계와 같다). 계산 블록은 core `ComputeBlock` 이라
`block(snapshot)` 으로 부르고 `block.stats()` 로 계수를 본다.

### 4.1 입력 계약 (`contract_input.py`, 전부 frozen dataclass, 값은 불변)

- `LayoutDevice(name, kind, drain, gate, source, body, W_m, L_m, ID_A, gm_id, vds_V, vsb_V, tol_v_V, diode, W_adjustable)`.
  `kind` ∈ `KINDS`. `W_m`·`L_m`·`gm_id`·`tol_v_V` 는 양의 **float**(int 거부). 위반 → `ValueError`.
  `tol_v_V` = 그 소자 동작점의 LUT tol_V `id_equivalent` 셀 값(부르는 쪽이 `lut.tol_v_table(...).at(L, vds, "id_equivalent")` 로 채움).
  `W_adjustable` = MOD8 이 이 소자 W 를 바꿀 수 있음.
- `MatchingGroup(gid, members, role, hub_net, allowed_patterns)`: `members` tuple(중복 없음, 2개 이상), `allowed_patterns` = `PATTERNS`
  의 비지 않은 부분 tuple, `role == "diff_pair"` 이면 `"common_centroid"` 포함 필수. `hub_net` 은 None 가능. 위반 → `ValueError`.
- `RowGroup(rid, kind, body_net, members)`: `members` tuple(중복 없음), `kind` ∈ `KINDS`.
- `LayoutPdk(manufacturing_grid_m, slice_width_keys, finger_pitch_overhead_m, row_gap_m, source_fp)`: 격자 > 0, 여유·간격 >= 0.
  `slice_width_keys` = ((kind, (폭 키 오름차순, ...)), ...). `LayoutPdk.from_lut(lut, overhead, gap)` = (`lut.spec.manufacturing_grid_m`,
  kind 마다 `lut.widths(lut, kind)`(kind 정렬), overhead, gap, `lut.fp`) -- overhead·gap 은 float 로 바뀐다.
- `LayoutInput(devices, matching_groups, row_groups, pdk, box_max_row_ratio, rejected_requests=())`. `ValueError` 조건:
  소자 이름 중복, gid·rid 중복, 행 그룹 멤버가 없는 소자, 한 소자가 두 행 그룹, 소자 (kind, body) != 행 그룹 (kind, body_net),
  어느 행 그룹에도 없는 소자, PDK 폭 키에 소자 kind 없음, 그룹 멤버가 없는 소자, 그룹 멤버가 두 행 그룹에 걸침,
  `rejected_requests` 중복, `box_max_row_ratio < 1`.

### 4.2 `w_tolerance(gm_id, tol_v, finger_w_m, grid_m) -> (lower, upper)`
`upper = tol_v * gm_id`, `lower = grid_m / (2 * finger_w_m)`. 손계산: (10.0, 0.01, 1e-6, 5e-9) -> (0.0025, 0.1).

### 4.3 `finger_candidates` -- device `ly_fw_cand`
reads device `ly_device`, graph `ly_pdk`. 소자마다 tuple: 그 kind 의 폭 키 오름차순, 키마다 nf ∈ sorted({max(1, floor(W/fw)), max(1, ceil(W/fw))})
(fw = 키 x 격자), `FingerCandidate(키, fw, nf, nf*fw, |nf*fw − W|/W, lower, upper, ok)`, `ok = err <= upper and lower <= upper`.
상한 밖 후보도 남는다(ok=False). 같은 (kind, W, gm/ID, tol_V) 소자는 같은 tuple 객체.

### 4.4 `pattern_select` -- graph `ly_groups` (key `"layout"`, 값 = gid 정렬 `GroupLayout` tuple)
reads device `ly_device`·`ly_fw_cand`, graph `ly_pdk`·`ly_groups_in`·`ly_rejected`. 그룹마다 독립(전 그룹 판정, LY6).

1. 전제(어기면 `pattern=None`, `ok=False`, `reason` = 아래, `attempts` = (step `"precondition"` 1개)):
   `hub_net is None` -> `"no_hub_net"`; 멤버의 source 도 drain 도 hub 가 아님 -> `"member_not_on_hub:<이름>"`; hub 반대쪽(leaf) 넷이 겹침 -> `"leaf_net_shared"`.
   전제를 만족하면 멤버를 hub 가 source 가 되게 세워 패턴 함수에 넘긴다(MOS source/drain 대칭).
2. 후보 조합 = 모든 멤버에게 `ok` 인 공통 폭 키 x 멤버별 그 키의 ok nf(곱집합). 조합 순서 = (행 폭 칸 수 = floor(sum(nf x (L_m + overhead)) / 격자),
   최대 err, 폭 키).
3. 패턴 호출: common-centroid -- 멤버 nf 가 모두 같고 nf >= 멤버 수면 `common_centroid_layout(trs, n_rows=None, max_candidates=총 finger)`,
   멤버 2개이고 nf 가 다르면 `n_rows=2`, 그 밖은 호출하지 않고 attempt `reason="cc_precondition"`.
   interdigitation -- `INTERDIGITATION_PATTERNS` 의 base 를 이름 정렬 순으로 보며 글자 수 = 멤버 수이고 어떤 repeat 의 글자별 개수를
   (개수 내림차순, 글자) 로 늘어놓은 것 = 멤버 nf 를 (nf 내림차순, 이름) 으로 늘어놓은 것인 첫 base 를 넘긴다(그 대응으로 글자 정렬
   순 = 소자 순서). 없으면 `base=None`.
4. 행마다 `canonical_row` 로 node_sequence 정규화 -> `PatternRow`. **dx·dy** = 멤버 무게중심 x·y 의 (최대 − 최소), finger 피치 단위:
   행 r(0부터, 행 수 R), 그 행 길이 n 의 i 번째 finger 의 x = i − (n−1)/2, y = r − (R−1)/2. 무게중심 일치(`centred`) = dx == dy == 0(정확한 유리수).
5. 정렬 키(사전식) = (centred 아니면 1, 방법이 `pattern_table`·`rotation_exact` 아니면 1, crossover_count, isolated_pairs, residual,
   행 폭 칸 수, 최대 err, 폭 키, 패턴 이름, nf tuple). 최선 = 최소 키. 앞 다섯 칸이 (0,0,0,0,0.0) 인 후보가 나온 뒤 행 폭 칸 수가 더 큰
   조합은 평가하지 않는다(attempts 에도 없다).
6. 차동쌍(`role == "diff_pair"`, LY5): (i) common-centroid 만으로 5의 최선을 찾고 centred 이면 채택, `reason="cc_same_W"`.
   (ii) 아니면 멤버 모두 `W_adjustable` 이고 `rejected_requests` 에 없을 때: `W_new = 멤버 수 x 키* x 격자`,
   키* = 그 kind 폭 키 중 |키 x 격자 − max(멤버 W)/멤버 수| 최소(동률은 작은 키), 멤버마다 `WRequest(이름, W, W_new, "cc_nf", gid)`,
   `pending=True`, `provisional=True`, `reason="w_request_pending"`, 배치 = (i) 의 최선(없으면 pattern None), attempts 끝에 step `"w_request"`
   (finger_w = W_new/멤버 수, nf = 멤버 수씩, reason `"cc_nf"`).
   (iii) 그 밖: attempts 에 step `"w_request"`(reason `"w_request_rejected"`(멤버 중 거부 있음) 또는 `"w_not_adjustable"`), interdigitation
   으로 5의 최선(step `"relax"`), `relaxed=True`, `reason="relaxed:<사유>"`. interdigitation 이 허용 밖이거나 후보가 없으면 pattern None,
   relaxed False.
7. 차동쌍이 아니면 허용 패턴 전부(`PATTERNS` 순)로 5의 최선, `reason="selected"`. 최선이 없으면 `"no_common_finger_w"`(공통 ok 폭 없음)
   또는 `"no_applicable_pattern"`.
- `GroupLayout.ok` = 채택 배치가 centred. `attempts` = 평가 순서대로 전부(`GroupAttempt(step, pattern, finger_w_m, n_fingers, W_realized_m,
  method, dx, dy, ok, reason)`, 전제 밖은 method/dx/dy None, 평가한 것은 reason `"evaluated"`).

### 4.5 `finger_geometry` -- device `ly_finger`
reads device `ly_device`·`ly_fw_cand`, graph `ly_groups`·`ly_row_groups`.
- pattern 이 있는 그룹 멤버: 그 그룹의 폭 키·nf 후보, `origin="group"`, `group=gid`.
- 나머지(행 그룹 rid 정렬, 행 그룹 안 이름 정렬): 남은 소자 중 **가장 많은 소자에게 ok 인 폭 키** -> 동률이면 그 소자들의
  (그 키에서 err 최소 nf) 합 최소 -> 동률이면 큰 키. 그 키가 ok 인 소자 모두에 그 키의 (err, nf) 최소 후보를 주고 남은 소자로 반복.
  다른 행 그룹의 폭은 보지 않는다(단위셀 폴백·seed 전파 없음).
- 어떤 키도 ok 가 아닌 소자: 전체 후보 중 (err, nf, −키) 최소를 잠정으로 쓰고 `w_request = WRequest(이름, W, 그 후보 실현 W,
  "finger_quantization", None)`. 단 그 소자가 어떤 그룹의 `w_requests` 에 이미 있으면 `w_request=None`(그룹 요청이 대신). 그 밖은 `w_request=None`.

### 4.6 `row_euler(transistors, matching_pairs, pair_sensitivity) -> dict`
소자를 source·drain 넷 연결 성분(diffusion 섬)으로 나눠(섬 = 이름 정렬, 섬 순서 = 첫 이름 정렬) 섬마다: `build_graph` ->
`check_euler_condition`; 가능하면 섬 안 쌍이 있을 때 `mirror_symmetric_trail`(성공 시 "mirror"), 아니면 `hierholzer`("euler");
불가면 `find_min_crossover_layout(섬, matching_pairs=섬 안 쌍, pair_sensitivity=섬 안 쌍의 값 또는 None)`("crossover").
반환: `transistor_sequence`, `node_sequence`(`canonical_row` 결과), `segments`, `crossover_after`(각 segment 끝 finger index, 마지막 제외),
`method`(crossover > mirror > euler 우선 표기), `crossover_count`(섬별 합), `n_components`. finger 수는 바꾸지 않는다.

### 4.7 `box_verdict(rows, max_row_ratio, folds) -> BoxVerdict`
`rows` = ((id, 폭, 높이), ...). width_ratio = 최대 폭 / 최소 폭(동률은 id 순으로 정렬해 가장 넓은·좁은 id), `ok = width_ratio <= max_row_ratio`,
total_width = 최대 폭, total_height = 높이 합, elongation = max/min(두 값), `folds` 는 tuple 로 옮긴다.

### 4.8 `compose_rows` -- graph `ly_rows`(`RowsLayout(rows, box)`)
reads device `ly_device`·`ly_finger`, graph `ly_groups`·`ly_groups_in`·`ly_row_groups`·`ly_pdk`·`ly_box_ratio`.
- 행 그룹(rid 정렬)마다: pattern 있는 그룹(gid 정렬, 멤버 ⊂ 행 그룹)의 i 번째 패턴 행 -> 행 id `"<rid>/<gid>/<i>"`, method `"pattern:<방법>"`,
  `walk_ok` = segment 마다 `check_walk_sequence(segment 순서, segment 안 finger 수의 Transistor)` 모두 ok, crossover_count = len(crossover_after).
  나머지 소자는 폭 키별로 행 id `"<rid>/w<키>"`, `row_euler`(쌍 = 각 입력 그룹 멤버를 이름 정렬해 (0,1),(2,3),... 로 묶은 것,
  민감도 = 차동쌍 `"offset"`, 그 밖 `"ratio"`).
- 행 폭 = sum(nf x (L_m + overhead)), 높이 = finger_w. `devices` = ((이름, 그 행 finger 수), ...) 이름 정렬.
- box: `box_verdict` FAIL 이고 가장 넓은 행이 `<rid>/w<키>` 행(아직 안 접은 것)이면 n = 2, 3, ..., (그 행 최대 nf) 로
  `apply_explicit_row_split` 해 각 조각을 `row_euler`, 행 폭 비가 직전 n 보다 줄지 않으면 멈추고 가장 좋은 n 을 원래 비보다 작을 때만
  적용(`folds` 에 (행 id, n)), 접은 조각 id = `"<행 id>_split<j>"`(복사 함수 규칙). 반복. 가장 넓은 행이 패턴 행이거나 개선이 없으면
  멈추고 그 판정을 남긴다. 행은 id 정렬.

### 4.9 `floorplan` -- graph `ly_floorplan`(`FloorplanSummary`)
reads graph `ly_rows`·`ly_pdk`. 행마다 `FloorplanBlock(행 id, 폭/격자, finger_w/격자)`, `spine_groups` = {행 그룹 id: 그 행 블록들}(행 id 순),
`mirror_pairs = []`, `gap = row_gap_m / 격자`, `transistor_sequences` = {행 id: 순서}로 `pack_floorplan_grouped`. 결과 길이 x 격자 -> m.
`outline_area_m2 = bbox 폭 x bbox 높이`, `area_tie_m2 = 격자^2`, `placements` = 행 id 정렬 (id, x, y, 폭, 높이).

### 4.10 `run_layout(layout_input, previous=None) -> LayoutResult`
1. 스냅샷 = `previous.snapshot`(있으면) 아니면 `GraphSnapshot.empty(LY_WRITERS)`. writer `"ly_input"`, 입력 버전 `fp_of(layout_input)` 으로
   device `ly_device`({이름: LayoutDevice}), graph(key `"layout"`) `ly_pdk`·`ly_groups_in`(입력 tuple 그대로)·`ly_row_groups`·`ly_box_ratio`·
   `ly_rejected`(정렬 tuple) 를 쓴다.
2. 블록 순서 `finger_candidates` -> `pattern_select` -> `finger_geometry` -> `compose_rows` -> `floorplan`. `computed_blocks` = 이번 호출에서
   block_version 이 바뀐 writer 이름(순서대로).
3. `devices` = 입력 순 `DeviceLayout(이름, finger_w, nf, ((행 id, nf), ...) 행 id 순, W, 실현 W, err, lower, upper, origin)`.
   `w_requests` = 그룹 요청 + 소자 finger_quantization 요청, (device, reason) 정렬. `coverage_ok`·`coverage_missing`(정렬) =
   `check_stick_diagram_coverage(입력 이름, {행 id: 행 소자 이름})`.
   `w_invariant_ok` = 모든 소자에서 (행별 nf 합 == nf) 이고 (err <= upper 또는 그 소자 이름의 W_request 있음).

### 4.11 불변식 (test 대상)
1. **총 W 보존(LY1)**: 모든 소자 `W_err_rel <= W_tol_upper` 또는 그 소자 `W_request` 존재. 행 접기·crossover 전후 소자별 행 finger 합 불변.
2. **W 를 바꾸지 않는다(LY3)**: `DeviceLayout.W_m` = 입력 W. W 변경은 `w_requests` 로만.
3. **행별 finger_w(LY2·L6)**: 한 행의 finger_w 는 하나, 비그룹 소자의 폭 키는 같은 행 그룹 소자의 ok 후보에서만.
4. **전 그룹 판정(LY6)**: `groups` 는 입력 그룹 전부(gid 정렬). 앞 그룹이 전제 밖이어도 뒤 그룹 판정이 있다.
5. **조용한 완화 금지(LY5)**: `relaxed=True` 이면 attempts 에 step `"cc_same_W"`(또는 후보 없음) 와 `"w_request"` 가 `"relax"` 앞에 있다.
6. **결정론(NFR-4)**: 같은 입력이면 `PYTHONHASHSEED` 와 무관하게 결과(snapshot 제외)가 같다.
7. **필드 = 캐시(L11)**: 같은 입력으로 `previous` 를 주면 `computed_blocks == ()` 이고 결과가 같다. `box_max_row_ratio` 만 바꾸면
   `("ly_rows", ...)` 부터만(앞 세 블록 재사용), 소자 하나의 W 만 바꾸면 `ly_finger_candidates` 부터 다시 계산(결과가 같은 블록 뒤는 재사용될 수 있다).
   각 블록 `stats().recomputes_same_input == 0`.
8. coverage: `coverage_ok` 이고 `coverage_missing == ()`.

### 4.12 손계산 오라클 (toy)
`pdk = LayoutPdk(5e-9, (("nmos", (200, 400, 1000)),), 0.0, 0.0, "toy")`(폭 1·2·5 µm). 소자(kind nmos, body "sub", L 1e-6, ID 1e-6,
gm/ID 10.0, vds 0.5, vsb 0.0, tol_V 0.01 -> upper 0.1, diode False, adjustable True): A(s h, d da, W 4e-6), B(s h, d db, W 4e-6),
C(s x, d y, W 3e-6), D(s y, d z, W 6e-6). 그룹 `MatchingGroup("g1", ("A","B"), "diff_pair", "h", PATTERNS)`, 행 그룹 `("r", "nmos", "sub", (A,B,C,D))`,
box 기준 1.5.
- C 후보: (200, nf 3, err 0, ok), (400, 1, 1/3, x), (400, 2, 1/3, x), (1000, 1, 2/3, x). lower = 0.0025 / 0.00125 / 0.0005.
- g1: 첫 조합(폭 칸 = 4 fingers x 1e-6 / 5e-9 = 800) = 키 400, nf (2,2) -> `rotation_exact`, 행 `("A","B")`/`("B","A")`, node `("da","h","db")`/
  `("db","h","da")`, dx = dy = 0, ok, `reason="cc_same_W"`, attempts 1개(다음 조합 키 200 nf (4,4) 는 폭 칸 1600 이라 평가 안 함).
- C·D: 공통 ok 키는 200 뿐 -> C 3, D 6 finger, 행 `"r/w200"` 폭 9e-6 -> 행 폭 비 9/2 = 4.5 > 1.5 -> 접기 n=2 (C 2/1, D 3/3: 폭 5,4 -> 비 2.5),
  n=3 (C 1/1/1, D 2/2/2: 3,3,3 -> 비 1.5), n=4 (3,3,2,1 -> 비 3.0, 증가 -> 멈춤) -> n=3 적용, folds `(("r/w200", 3),)`, 각 조각 순서
  `("C","D","D")`, node `("x","y","z","y")`, method "euler", box ok(비 1.5).
- 행 5개: `r/g1/0`, `r/g1/1`(폭 2e-6, 높이 2e-6), `r/w200_split0..2`(폭 3e-6, 높이 1e-6). `w_requests == ()`, `w_invariant_ok`.
- 차동쌍 완화 순서(T5), 행 그룹 `("r", "nmos", "sub", ("A","B"))` 만:
  - A·B W `1.5e-6`(모든 후보 err 1/3 > 0.1 -> ok 후보 없음, 조합 0): adjustable -> pattern None, `pending=True`, `reason="w_request_pending"`,
    attempts = (`("w_request", "cc_nf")`), w_requests = A·B 각 `WRequest(이름, 1.5e-6, 2e-6, "cc_nf", "g1")`(키* = |키 x 5e-9 − 0.75e-6| 최소 = 200,
    W_new = 2 x 1e-6) -- finger_quantization 요청은 따로 내지 않는다. `W_adjustable=False` -> pattern None, relaxed False, `reason="no_common_finger_w"`,
    attempts `(("w_request","w_not_adjustable"),)`, w_requests = A·B `"finger_quantization"`(group None). `rejected_requests=("A","B")` -> 같은 모양,
    사유 `"w_request_rejected"`. 세 경우 모두 `w_invariant_ok`.
  - A·B W `1.1e-6`, `W_adjustable=False`: 키 200 nf 1 (err 0.0909 ok) -> cc 는 nf 1 < 2 라 `cc_precondition` -> `w_request`(`w_not_adjustable`) ->
    `relax`: interdigitation `pattern_table`(base "AB"), 행 `("A","B")`, dx 1.0, ok False, `relaxed=True`, `reason="relaxed:w_not_adjustable"`,
    attempts step 순서 `cc_same_W`, `w_request`, `relax`, w_requests ().

### 4.13 결정·범위 밖
- MOD8(W_request 를 받아 sizing 재평가·`rejected_requests` 를 채워 다시 부르기)은 다음 단계. 이번 범위는 W_request 를 결과로 내보내기만.
- box FAIL 은 W 를 바꾸지 않고 FAIL 로 남긴다. 패턴 행은 접지 않는다(matching 배치 보존).
- 블록 단위 재사용(core `compute_block`): 한 블록이 읽는 열 중 하나라도 바뀌면 그 블록 전체를 다시 계산한다(소자별 부분 재사용은 MOD8 단계 과제).
