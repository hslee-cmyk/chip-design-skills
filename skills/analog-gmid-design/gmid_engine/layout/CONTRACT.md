# gmid_engine.layout 동작 계약 (test 작성용) -- 1단계: 복사 단위 + canonical_rows

- 대상: `gmid_engine/layout/` 중 이번 단계 파일 14개(아래 0절 표). 행 구성 7단계(`rows.py` 등)·graph 레이아웃 필드·MOD8 루프는
  다음 단계라 이 계약에 없다.
- 근거: `wt/_drafts/engine/design_mod7_layout.md`(이하 DM) 1절 표·1.1 복사 정의 전수표·2.1 AST 해시·2.2 리터럴·7절 끝 결정론
  결함·8절 2 기본안, `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 1.5(결정론).
- import 경로: `layout/__init__.py` 의 `__all__` 은 아직 비어 있다(공개 API 는 다음 단계 `run.py` 의 `LayoutInput`·
  `LayoutResult`·`run_layout`, DM 1 표). 이번 단계 test 는 파일 모듈을 직접 import 한다
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
