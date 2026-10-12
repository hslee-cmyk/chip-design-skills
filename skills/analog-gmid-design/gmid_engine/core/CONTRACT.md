# gmid_engine.core 동작 계약 (test 작성용)

- 대상: `gmid_engine/core/` 공개 API(`gmid_engine.core.__all__`). test 는 `from gmid_engine.core import ...` 만 쓴다
  (파일 모듈 직접 import·`_` 이름 사용 금지). 경로: `gmid_engine/tests/conftest.py` 가 패키지 부모 디렉터리를
  `sys.path` 앞에 넣는다(설치 불필요). test 파일 배치는 규칙 D: `gmid_engine/tests/core/test_<파일>.py`.
  같은 basename 이 다른 패키지 test 에도 생기므로 test 디렉터리에 `__init__.py` 를 두거나 `--import-mode=importlib` 를 쓴다.
- 근거: `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항'(최우선)·1절·3.1·4절, 계획 N3.3·N3.4·N3.5·N3.14·NFR-2·NFR-4·WP-03·WP-10.
- 아래 "불변식"은 test 가 확인할 성질, "실패"는 반드시 그 예외로 거부해야 하는 입력이다.
- **개정 2026-10-08(사용자 승인 "1은 승인." -- sizing O7·O9)**: (1) 투영 지문 = 값 지문 합성(8절, 6.2) -- 블록 호출마다 값을 다시
  직렬화하지 않는다. (2) `GraphSnapshot.column_fields`·`extend_writers`(5.6). 실측은 10절.
- **개정 2026-10-08(사용자 승인 "2번 + 1번으로 진행해. 나머지도 함께 진행해." -- core 성능 2~5)**: (1) memo 키 = `canonical_key`(1.1절, 7절) --
  `BoundedLRU.lookup` 이 키마다 `fp_of` 직렬화+sha256 을 하지 않는다. (2) `GraphRecord.fp`·`GraphSnapshot.fp` 는 처음 읽을 때 한 번 계산해 보관
  (5.5·5.6), `GraphSnapshot.write` 는 레코드를 write 당 한 번만 새로 만들고 열 key 목록은 스냅샷마다 한 번만 정렬. (3) 투영 지문 식 개정(8절)
  -- 열 행 직렬화 제거. 값·동치 관계·공개 계약은 그대로이고 `fp_of` 출력(영속 지문)은 한 바이트도 바뀌지 않았다.

---

## 0. 구조 규칙 (사용자 확정 2026-10-07) -- core 파일 전부에 적용

판정 정의(이 계약이 쓰는 계수 방법):
- **독립 진입점(규칙 A)**: 파일의 모듈 최상위 `def`/`class` 중 이름이 `_` 로 시작하지 않는 것 가운데, 같은 파일의
  **다른 최상위 def/class 노드 안**(본문·기반 클래스 목록·데코레이터·주석 포함, `ast.walk`)에 `ast.Name` 으로
  나타나지 않는 것. 파일마다 정확히 1개. **데이터 선언 모듈**(공개 정의가 전부 dataclass/NamedTuple/Enum/Exception
  클래스이고 메서드는 dunder·property·from_* 생성자만)은 한 개념으로 통과, 공개 정의 0 파일도 통과(오케스트레이터 해석
  2026-10-07). `_module_map.MODULES[*].kind == "data"` 가 그 파일이고, `"entry"` 파일의 진입점은 `entry_point` 와 같다.
- **규칙 B**: 다른 파일의 `_` 이름 import 0. 비공개 helper 는 자기 파일에서만 쓴다.
- **규칙 C**: `@compute_block` 사용 수 ≤ 1 / 파일 (core 에는 0).
- **층**: `_module_map.LAYERS` 의 core 층 tuple 에서, 파일은 앞 층 파일만 import 한다(같은 층끼리 금지, 순환 0).
  패키지 간은 `_module_map.PACKAGE_ORDER` 앞쪽으로만.
- **숫자 리터럴**: 엔진 소스(tests 제외)의 int/float 리터럴은 {0, 1, -1, 2} 밖 0개(현재 core·_module_map 전부 0개, 예외는 단위 표 `units.py` 하나).
- **이름 리터럴**: 회로·소자·넷 이름 문자열 0개(core 문자열은 스키마 어휘 `"node"`·`"device"`·`"edge"`·`"graph"` 와
  N3.14 분류 키뿐).
- **광범위 except 0**: core 의 `except` 절은 `pdk_decl.py` 의 좁은 네 개(`json.JSONDecodeError`·`SyntaxError`·`LookupError`(코덱 이름)·
  `re.error` -> 선언 거부 `SchemaRejectedError` 로 바꾼다, 9절)뿐이다.
- **모듈 수준 가변 캐시 0**: 모듈 수준 dict/list/set 대입·`@lru_cache`/`@cache`·`global` 문 0(분류표는 읽기 전용 매핑).
- 자기 파일 self-test·`if __name__ == "__main__"` 0.

| 파일 | 층 | 독립 진입점 |
|---|---|---|
| determinism.py | 0 | `sorted_items` |
| canonical_key.py | 0 | `canonical_key` |
| fingerprint.py | 0 | `fp_of` |
| immutability.py | 0 | `require_immutable` |
| margin.py | 0 | `normalized_margin` |
| units.py | 0 | (공개 정의 0, 상수 표) `METRIC_UNITS`·`DOMAINS`·`AMPLITUDE_DB_PER_DECADE` -- 규칙 D 숫자 리터럴 예외 파일 |
| writer_error.py | 0 | `WriterPermissionError` |
| bounded_lru.py | 1 | `BoundedLRU` (`LruStats` 는 같은 파일 비진입 공개 이름) |
| failure_record.py | 1 | `FailureRecord` |
| field_value.py | 1 | `FieldValue` |
| metric_signature.py | 1 | (데이터 선언 모듈) `MetricSignature(unit, domain, view_kind=None, objective_axis=None)` + 어휘 `VIEW_KINDS`(transfer, loop, cm_loop, output_port, ratio)·`OBJECTIVE_AXES`(power, area) -- unit ∈ `METRIC_UNITS`, domain ∈ `DOMAINS`(units 표), view_kind ∈ {None} ∪ `VIEW_KINDS`(None = 뷰 없음, 문자열 `"none"` 은 어휘 밖), objective_axis ∈ {None} ∪ `OBJECTIVE_AXES`; 밖이면 `ValueError`. 뷰 종류 어휘는 이 파일 한 곳 |
| projection.py | 1 | `Projection` |
| writer_table.py | 1 | `WriterTable` (+ 상수 `ENTITY_KINDS`) |
| compute_block.py | 2 | `compute_block` (`ComputeBlock`·`BlockStats` 는 비진입 공개 이름) |
| failure_errors.py | 2 | (데이터 선언 모듈) N3.14 예외 클래스 7개 |
| graph_record.py | 2 | `GraphRecord` |
| failure_classes.py | 3 | (데이터 선언 모듈) `FailureClass` + 상수 `FAILURE_CLASSES`·`CANDIDATE_FAILURE_CLASSES`·`UNEXPECTED_EXIT_CODE` |
| graph_snapshot.py | 3 | `GraphSnapshot` |
| pdk_decl.py | 3 | `read_pdk_decl` (`PdkDecl`·`PdkQuantity`·`PdkRule`·[U3] `PdkMismatchModel`·`PdkMismatchBlock` 는 비진입 공개 이름, 9절) |
| canon_pointer.py | 4 | `CanonPointer` |
| exit_code.py | 4 | `exit_code_for` |
| (`gmid_engine/_module_map.py`) | -- | (데이터 선언 모듈) `ModuleEntry` + 상수 `PACKAGE_ORDER`·`LAYERS`·`MODULES` |

---

## 1. 내용 지문 `fp_of(obj) -> str`

- 출력: 64자 소문자 hex(sha256) 문자열.
- 결정론: 같은 내용이면 프로세스·`PYTHONHASHSEED`·dict 삽입 순서·set 순회 순서와 무관하게 같은 값.
- 정준 직렬화 규칙:
  - `float` 은 `float.hex` 로 직렬화 -- `0.0` 과 `-0.0` 은 다른 지문, `0.1` 과 `0.1 + 1e-18`(같은 float 이면 같음; `0.1 + 1e-17` 은 1 ulp 다른 float 이라 다른 지문) 처럼
    비트가 같으면 같고 1 ulp 라도 다르면 다르다.
  - `bool` 과 `int` 는 다른 태그: `fp_of(True) != fp_of(1)`, `fp_of(1) != fp_of(1.0)`, `fp_of("1") != fp_of(1)`.
  - `tuple` 과 `list` 는 같은 태그(내용 지문): `fp_of((1, 2)) == fp_of([1, 2])`. 순서가 다르면 다르다.
  - `dict`(모든 Mapping)은 키 정렬: 삽입 순서와 무관. `frozenset`·`set` 은 원소 정렬: 순서 무관, `fp_of({1, 2}) != fp_of((1, 2))`.
  - `bytes`·`bytearray` 같은 태그. `None` 지원. `str` 은 UTF-8.
  - 클래스에 `__canonical__(self)` 메서드가 있으면 (모듈.클래스 이름, 그 반환값) 을 직렬화한다 -- 같은 반환값이라도
    클래스가 다르면 다른 지문.
  - dataclass 인스턴스는 (모듈.클래스 이름, 선언 순서 (필드 이름, 값)) -- 필드 값이 하나라도 다르면 다른 지문.
  - 자기 구분적 인코딩: `fp_of(("ab", "c")) != fp_of(("a", "bc"))`, `fp_of(((1,), 2)) != fp_of((1, (2,)))`.
- 실패: 그 밖의 타입(일반 객체, 함수, 모듈, 클래스 객체 자체 등) -> `TypeError`. 중첩 안에 있어도 `TypeError`.

### 1.1 memo 키 정준화 `canonical_key(obj)` -> hashable (2026-10-08, 파일 `canonical_key.py`, 층 0)
- 목적: `fp_of` 와 **같은 동치 관계**를 직렬화·sha256 없이 `dict` 키로 옮긴다. 프로세스 안 dict 키 전용 -- 저장·기록·영속하지 않는다
  (영속·기록하는 지문은 항상 `fp_of`). 출력 형태(어떤 hashable 인지)는 계약이 아니다; 계약은 아래 동치와 거부뿐.
- 동치: `canonical_key(a) == canonical_key(b)` <=> `fp_of(a) == fp_of(b)` (sha256 충돌 제외). 파이썬 `==`·`hash` 가 뭉개는 구분을 살린다:
  `0.0` != `-0.0`, `1` != `1.0` != `True` != `"1"`, 모든 NaN 은 같은 키(`float.hex` 가 모두 'nan'), `bytes` != `str`, `tuple` != `frozenset`.
  dataclass 는 (모듈.qualname, 선언 순서 (필드 이름, 값)) -- 클래스가 다르면 다른 키, `__canonical__` 객체는 (모듈.qualname, 그 반환값의 키).
  tuple 은 `fp_of` 처럼 원소 순서 의존, frozenset 은 순서 무관.
- 실패: `require_immutable` 이 거부하는 값(dict, list, set, bytearray, 일반 객체, 비-frozen dataclass, 그 안에 든 가변 값)은 `TypeError` --
  불변 검사가 같은 순회에서 이뤄진다(`BoundedLRU.lookup` 은 따로 `require_immutable` 을 부르지 않는다).
- 불변식(test 작성용): (a) 임의 불변 값 쌍에서 위 동치 양방향; (b) 반환값은 항상 `hash` 가능하고, 같은 값을 여러 번 정준화하면 `==`;
  (c) PYTHONHASHSEED 와 무관하게 같은 동치; (d) 가변 값은 `TypeError`.

## 2. 불변 검사 `require_immutable(value) -> None`

- 허용(None 반환): None, bool, int, float(및 하위 클래스), str, bytes, `tuple`·`frozenset`(원소가 모두 허용),
  **frozen** dataclass(필드 값이 모두 허용), `__canonical__` 이 있는 객체(반환값이 허용).
- 실패 -> `TypeError`: dict, list, set, bytearray, 일반 객체, 비-frozen dataclass, 그리고 위 허용 컨테이너 안 어디에든
  그런 값이 있을 때(예: `(1, [2])`, frozen dataclass 필드에 list).
- 주의(계약 밖): `__canonical__` 이 자기 자신을 돌려주는 객체는 무한 루프 -- test 하지 않는다.

## 3. 결정론 `sorted_items(items, *, key=None) -> tuple`

- Mapping: `(키, 값)` 쌍의 tuple, 키 오름차순(`key` 가 있으면 `key(키)` 순). 반환은 항상 `tuple`.
- 그 밖 iterable(set·frozenset·list·generator): 원소를 `sorted(items, key=key)` 한 tuple.
- 같은 내용이면 입력 순서와 무관하게 같은 결과.
- 실패: 비교 불가 원소 혼합(예: `{1, "a"}`) -> `TypeError`.

## 4. 실패 규약 (계획 N3.14)

### 4.1 `FailureRecord(failure_class, devices=(), margin=None, detail=())` -- frozen dataclass
- 정규화: `devices` -> 중복 제거한 정렬 tuple, `margin` int -> float, `detail`(Mapping 또는 (키, 값) 쌍 iterable) ->
  키 정렬 ((키, 값), ...) tuple.
- `to_json()` -> `{"class": str, "devices": list, "margin": float|None, "detail": dict}`(정확히 이 4 키).
- `require_immutable(record)` 통과, `fp_of(record)` 결정론(같은 내용 -> 같은 지문, detail 순서 무관).
- 실패: `failure_class` 가 빈 문자열·비문자열 -> `ValueError`; `devices` 가 str -> `TypeError`; devices 원소 비문자열 ->
  `TypeError`; margin 이 bool·비수 -> `TypeError`; detail 키 비문자열 -> `TypeError`; detail 값이 가변(list 등) -> `TypeError`.

### 4.2 예외 클래스 (이름은 N3.14 그대로)
- 계층: `InfeasibleSizingError(ValueError)` 아래 `StructureUnresolvedError`, `InfeasibleTargetError`,
  `NonconvergentError`, `SealViolationError`, `SearchFailedError`. `SchemaRejectedError.__bases__ == (Exception,)`
  (ValueError·InfeasibleSizingError 하위가 아님).
- 생성: 키워드 전용 `devices=(), margin=None, detail=None`. 인스턴스는 `.record: FailureRecord` 를 가지며
  `record.failure_class` = 클래스 속성 `failure_class` = 아래 분류 키.
  | 클래스 | failure_class |
  |---|---|
  | StructureUnresolvedError | `STRUCTURE_UNRESOLVED` |
  | InfeasibleTargetError | `INFEASIBLE_TARGET` |
  | NonconvergentError | `NONCONVERGENT` |
  | SealViolationError | `SEAL_VIOLATION` |
  | SearchFailedError | `SEARCH_FAILED` |
  | SchemaRejectedError | `SCHEMA_REJECTED` |
- 실패: `InfeasibleSizingError()` 직접 생성 -> `TypeError`(기반 클래스). 위치 인자 -> `TypeError`.

### 4.3 `FAILURE_CLASSES` (읽기 전용 Mapping) / `FailureClass(exc, exit_code, parent, recorded_in_search)`
- 키 정확히 8개: 위 6개 분류 키 + 후보 실패 레코드 `structure_inconsistent`(parent `STRUCTURE_UNRESOLVED`),
  `local_infeasible`(parent `SEAL_VIOLATION`). 후보 실패 레코드는 `exc is None`, `exit_code is None`.
- 분류 키 항목은 `exc` = 위 표의 클래스, `parent is None`.
- `recorded_in_search` (N3.14 '탐색 중 처리'가 실패 기록인가): NONCONVERGENT·SEAL_VIOLATION·두 후보 레코드 = True,
  STRUCTURE_UNRESOLVED·INFEASIBLE_TARGET·SEARCH_FAILED·SCHEMA_REJECTED = False.
- 읽기 전용: 항목 대입 -> `TypeError`.
- 기반 `InfeasibleSizingError` 는 등록되지 않는다.

### 4.4 `CANDIDATE_FAILURE_CLASSES`, `UNEXPECTED_EXIT_CODE`
- `UNEXPECTED_EXIT_CODE == 1`(N3.14 '예상 밖 예외').
- `(NonconvergentError, SealViolationError)` (이 순서의 tuple). `InfeasibleSizingError`·`SchemaRejectedError` 미포함.

### 4.5 `exit_code_for(exc) -> int`
- 값(N3.14 '분류 순서대로 배정'): 예상 밖 1, STRUCTURE_UNRESOLVED 2, INFEASIBLE_TARGET 3, NONCONVERGENT 4,
  SEAL_VIOLATION 5, SEARCH_FAILED 6, SCHEMA_REJECTED 7. 모두 서로 다르다.
- MRO 앞에서부터 등록 클래스를 찾는다: 위 클래스의 사용자 하위 클래스는 부모의 code. 등록되지 않은 예외
  (`RuntimeError`, `ValueError`, `KeyError`, `WriterPermissionError` 등)는 1.
- 실패: 예외 인스턴스가 아닌 인자(클래스 객체, 문자열 등) -> `TypeError`.

### 4.6 `normalized_margin(magnitude, tol) -> float | None`
- `tol` 이 None 또는 0(0.0 포함) -> None. 그 밖 -> `float(magnitude) / float(tol)`(부호 보존, int 입력도 float 반환).

---

## 5. 불변 graph 저장 구조 (확정 사항 1·2)

### 5.1 `ENTITY_KINDS` = `("device", "edge", "graph", "node")`
레코드 종류. `"graph"` 는 스냅샷 전체 필드(θ·metric·레이아웃 결과 등)용.

### 5.2 `WriterPermissionError(Exception)`
N3.14 클래스가 아니다: `exit_code_for` -> 1, `CANDIDATE_FAILURE_CLASSES` 미포함, `InfeasibleSizingError` 하위 아님.

### 5.3 `WriterTable(entries)` -- frozen dataclass
- 입력: `(kind, field, writer)` 세 값 iterable 들의 iterable. `entries` 는 정렬된 `(((kind, field), writer), ...)` 로 정규화.
- 같은 (kind, field, writer) 반복은 한 항목. 선언 순서가 달라도 `==` 이고 `fp_of` 가 같다.
- `writer_of(kind, field)` -> writer 또는 None. `fields_of(writer)` -> 정렬된 (kind, field) tuple(없으면 ()).
- `require(writer, kind, field)`: 배정 writer 면 None, 선언 없음 또는 다른 writer -> `WriterPermissionError`.
- 실패: 같은 (kind, field) 에 다른 writer 둘 -> `WriterPermissionError`; kind 가 ENTITY_KINDS 밖 -> `ValueError`;
  field·writer 가 빈/비문자열 -> `ValueError`; 항목이 str 이거나 원소 수가 3 이 아님 -> `ValueError`.

### 5.4 `FieldValue(value, writer, input_version, write_count=1)` -- frozen dataclass
- `value_fp == fp_of(value)`(생성 시 계산, 인자로 넘길 수 없음).
- 실패: value 가변 -> `TypeError`; writer·input_version 빈/비문자열 -> `ValueError`; write_count 가 1 미만·bool·비정수 -> `ValueError`.

### 5.5 `GraphRecord(kind, key, fields)` -- frozen dataclass
- `fields`: (필드 이름, FieldValue) 쌍들 -> 이름 정렬 tuple. `get(field)` -> FieldValue|None, `field_names()` -> 정렬 tuple.
- `fp = fp_of((kind, key, ((이름, value_fp), ...)))` -- 값 내용만: writer·input_version·write_count 가 달라도 값이 같으면 같은 fp.
  [2026-10-08] 레코드가 불변이라 `fp` 는 **처음 읽을 때 한 번** 계산해 레코드에 보관한다(만들 때 계산하지 않는다 -- 읽지 않는 중간 레코드는
  직렬화하지 않음). 값은 즉시 계산했을 때와 같고(같은 fp_of 식), `dataclasses.fields` 에 `fp` 가 그대로 있다.
- 실패: key 비문자열 -> `TypeError`; 필드 이름 빈/비문자열 -> `ValueError`; 필드 값이 FieldValue 아님 -> `TypeError`; 이름 중복 -> `ValueError`.

### 5.6 `GraphSnapshot` -- 불변 스냅샷 (직접 생성하지 말고 `GraphSnapshot.empty(writers)` + `write`)
- `empty(writers)`: 레코드 0. `writers` 가 WriterTable 이 아니면 `TypeError`.
- 읽기: `kinds()`(레코드 있는 kind 정렬), `keys(kind)`(정렬, 없으면 ()), `record(kind, key)`(없으면 None),
  `field(kind, key, field)`(FieldValue|None), `value(kind, key, field)`(없으면 `KeyError`),
  `column(kind, field)` -> 그 필드가 있는 레코드의 `((key, value), ...)` key 정렬, `block_version(writer)`(없으면 None).
  [2026-10-08] `column_fields(kind, field)` -> `column` 과 같은 key·순서의 `((key, FieldValue), ...)`(값 지문·출처 메타를 함께 읽을 때).
  `tables`·`block_versions` 는 읽기 전용 매핑(대입 -> `TypeError`). 제자리 수정 API 없음.
- [2026-10-08, 사용자 승인 -- sizing O7] **`extend_writers(writers)` -- 권한표 확장**: 같은 레코드·block_versions 를 더 넓은 권한표
  `writers` 아래로 옮긴 새 스냅샷. `writers` 는 이 스냅샷 권한표의 모든 ((kind, field), writer) 를 같은 writer 로 포함해야 한다.
  - 결과: `writers` 가 새 표, 모든 레코드가 **같은 객체**(`is`), `fp`·모든 읽기 결과·필드 메타(writer·input_version·write_count)·
    `block_version` 이 원본과 같다. 원본 불변. 표가 원본과 `==` 면 `self` 그대로.
  - 실패: WriterTable 아님 -> `TypeError`; 원본 표의 항목이 빠졌거나 다른 writer -> `WriterPermissionError`(원본 불변).
  - 쓰기 API 가 아니다(값·메타를 바꾸지 않는다) -- 값을 바꾸는 길은 여전히 `write` 하나다.
- **`write(writer, input_version, columns)` -- 유일한 setter**:
  - `columns`: `{(kind, field): {key: value}}`. 열마다 `writers.require(writer, kind, field)`.
  - 열 교체 의미: 결과 스냅샷에서 그 (kind, field) 를 가진 레코드 key 집합 = 넘긴 key 집합. 넘기지 않은 key 의
    그 필드는 지워지고, 필드가 하나도 안 남은 레코드는 없어진다. 없던 key 는 레코드가 생긴다.
  - 필드 메타: 새로 쓴 필드는 `writer`, `input_version`, `write_count` = (이전 필드 있으면 이전 + 1, 없으면 1).
    값(value_fp)과 input_version 이 모두 이전과 같으면 그 FieldValue 객체를 그대로 둔다(write_count 불변).
  - `block_version(writer) == input_version` 이 된다(다른 writer 의 block_version 은 그대로).
  - 아무 레코드도 바뀌지 않고 block_version 도 이미 같으면 **`self` 그대로 반환**(`is`).
  - **구조 공유**: 이번 write 로 필드가 바뀌지 않은 레코드는 새 스냅샷에서 이전과 **같은 객체**(`is`)다 --
    다른 kind 의 레코드, 같은 kind 의 다른 key, 같은 key 라도 이번 열에 포함되지 않은 경우 모두. 값이 같아도
    input_version 이 바뀐 필드를 가진 레코드는 새 객체다(출처 기록이 바뀌었으므로).
  - 원본 불변: write 뒤에도 이전 스냅샷의 모든 읽기 결과·`fp` 가 그대로다.
  - `fp`: 값 내용 지문. 같은 값들을 다른 순서·다른 writer 경로·다른 input_version 으로 만들어도 같고,
    어느 한 값이라도 다르면 다르다. block_versions 는 fp 에 들어가지 않는다. [2026-10-08] 스냅샷이 불변이라 처음 읽을 때 한 번 계산해 보관
    (레코드 fp 도 그때 한 번) -- 값은 즉시 계산과 같다.
  - [2026-10-08] 한 `write` 안에서 같은 레코드의 여러 필드가 바뀌어도 새 `GraphRecord` 는 레코드당 하나만 만든다(중간 레코드 없음).
    열 key 목록(`column`·`column_fields`)은 스냅샷마다 kind 정렬 1회 + (kind, field) 당 1회만 만들어 보관한다(스냅샷 불변). 읽기 결과는 이전과 같다.
  - 실패: 권한 위반 -> `WriterPermissionError`(스냅샷 불변); input_version 빈/비문자열 -> `ValueError`;
    columns 가 Mapping 아님 또는 열 값이 Mapping 아님 -> `TypeError`; key 비문자열 -> `TypeError`; 값 가변 -> `TypeError`.
  - `==` 는 객체 동일성(eq=False). 내용 비교는 `fp` 로 한다.

### 5.7 `CanonPointer(initial)` -- 현재 정본 = 채택 스냅샷 포인터
- `current` -> 채택된 GraphSnapshot. `history` -> 채택 순서대로의 `fp` tuple(첫 스냅샷 포함, 같은 스냅샷 재채택도 한 번 더 기록).
- `adopt(snapshot)` -> snapshot 을 돌려주고 `current` 가 그것이 된다. 스냅샷 자체는 바뀌지 않는다.
- 실패: GraphSnapshot 아님 -> `TypeError`(생성·adopt 모두); `snapshot.writers != current.writers` -> `ValueError`(current 불변).

---

## 6. 계산 블록 `@compute_block(name, reads=(), writes=())`

### 6.1 선언 (데코레이트 시점)
- `name`: 비어 있지 않은 문자열 = 이 블록의 writer 이름. `reads`·`writes`: (kind, field) 쌍들. 반환 객체는 `ComputeBlock`
  (속성 `name`, `reads`, `writes`(정규화 tuple, 선언 순서), `code_hash`(64자 hex), `fn`).
- 실패 -> `ValueError`: name 빈/비문자열; writes 비어 있음; kind 가 ENTITY_KINDS 밖; field 빈/비문자열; 같은 쌍 중복; 쌍이 str 이거나 원소 수 ≠ 2.

### 6.2 호출 `block(snapshot, *extras) -> GraphSnapshot`
- `extras` 는 각각 불변이어야 한다: dict·list·set·가변 객체 -> `TypeError`(계수 변화 없음, 블록 함수 미호출).
- 블록 함수는 `Projection` 하나를 위치 인자로 받는다:
  - `projection.column(kind, field)` = 선언한 열의 `snapshot.column(kind, field)` 와 같은 값. 선언 밖 열 -> `KeyError`.
  - `projection.value(kind, key, field)`, `projection.extras` = extras tuple.
- 입력 버전 `v = fp_of((name, code_hash, projection.fp))`. `projection.fp` 는 (선언 열의 값 지문, extras) 만의 지문(8절).
- **재사용**: `snapshot.block_version(name) == v` 이면 블록 함수를 부르지 않고 `snapshot` 을 그대로(`is`) 돌려준다.
  -> 같은 스냅샷에 두 번 부르면 두 번째는 함수 호출 0. 선언하지 않은 필드·다른 블록 필드만 바뀐 스냅샷에서도 재사용.
  선언한 열의 값이나 extras 중 하나라도 바뀌면 재계산(IC10: 읽는 상태를 놓친 키 없음). 값이 같은 새 객체(다른
  lineage 에서 같은 값으로 만든 스냅샷)도 block_version 이 그 v 이면 재사용.
- **재계산**: 함수 결과는 키가 `writes` 와 정확히 같은 Mapping `{(kind, field): {key: value}}` 이어야 하고,
  `snapshot.write(name, v, result)` 로만 기록된다(5.6 의 열 교체·메타 규칙 그대로). 결과 스냅샷의 해당 필드는
  `writer == name`, `input_version == v`, `block_version(name) == v`.
  - 실패: 결과가 Mapping 아님·키 집합 ≠ writes -> `ValueError`; 권한표가 그 열을 name 에 배정하지 않음 ->
    `WriterPermissionError`; 블록 함수가 낸 예외는 그대로 전파(스냅샷 변화 없음).
- 블록 함수가 graph 를 쓰는 다른 길은 없다(Projection 은 스냅샷을 노출하지 않는다).

### 6.3 계수 `block.stats() -> BlockStats(name, calls, reuses, computes, recomputes_same_input)`
- 불변식: `calls == reuses + computes`(extras 검사로 거부된 호출은 세지 않는다; 블록 함수가 예외를 낸 호출은 computes 에 센다).
- `recomputes_same_input`: 이 블록 객체가 이전에 이미 계산한 v 로 다시 계산한 횟수. 예: 블록 결과가 없는 다른
  lineage 스냅샷에 같은 입력으로 부르면 +1. 블록 함수가 예외로 끝난 계산도 이력에 들어가므로, 같은 입력으로 다시
  부르면 +1(실패 캐시는 search 층 몫이다). 정상 파이프라인 기대값 0(확정 사항 5 '입력 버전 같은데 재계산하면 FAIL' 의 측정치).
- `reset_stats()`: 계수 전부 0, 계산 이력 비움(직후 같은 v 계산은 recompute 로 세지 않음).

## 7. LUT memo `BoundedLRU(capacity)`

- `capacity`: 1 이상 int(부르는 쪽이 계산). 실패: 0·음수·float·bool·비정수 -> `ValueError`. 숫자 기본값 없음.
- `lookup(key, compute)`: `key` 는 불변 값(가변 -> `TypeError`, compute 미호출). 키 동일성 = `fp_of` 와 같은 동치 관계
  (1.1절 `canonical_key` 를 dict 키로 쓴다 -- 키마다 직렬화·sha256 을 하지 않는다. `(0.0,)` 와 `(-0.0,)` 는 다른 키, `(1,)` 와 `(1.0,)` 와 `(True,)` 는
  서로 다른 키, NaN 을 담은 같은 내용 키는 적중, `(1, 2)` 와 `[1, 2]` 는 list 라서 TypeError). 상한(LRU)·결정론은 그대로.
  - 적중: 저장 값 그대로(`is`) 반환, compute 미호출, 그 키를 가장 최근으로.
  - 미적중: `compute()`(인자 없음) 1회 호출, 결과 저장·반환. 크기가 capacity 를 넘으면 가장 오래 안 쓴 항목 1개 퇴출.
    캐싱을 멈추지 않는다(DF-07): 상한 도달 뒤에도 새 키는 저장된다.
  - compute 가 예외를 내면 저장하지 않고 전파(misses 는 +1).
- `len(lru)` ≤ capacity 항상.
- `stats() -> LruStats(capacity, size, hits, misses, evictions, recomputes_after_eviction)`:
  `hits + misses` = 유효 lookup 수, `evictions` = 퇴출 수, `recomputes_after_eviction` = 퇴출됐던 키가 다시 미적중한 횟수.
  퇴출이 없으면 같은 키의 compute 호출은 정확히 1회(실행 내 같은 키 재계산 0).
- 예: capacity 2, 키 순서 1,2,1,3,2,2 -> hits 2, misses 4, evictions 2, recomputes_after_eviction 1, size 2.

## 8. `Projection` (블록 함수 인자; 직접 생성은 test 에서만)
- `Projection.from_snapshot(snapshot, reads, extras=())`: 선언 열마다 `snapshot.column` 을 담는다(빈 열도 포함 -> `column` 이 `()`).
- [2026-10-08 개정, 사용자 승인 '값 지문 합성'] `fp = fp_of((행 지문, extras))`, 행 지문 =
  sha256(정렬된 열마다 `(kind, field)` 자기 구분 텍스트 + 열 지문)(열 수에 비례하던 `fp_of` 재귀 직렬화 제거, 2026-10-08 두 번째 개정), 열 지문 = sha256(자기 구분 인코딩된 `((key, fp_of(value)), ...)`) -- 값 자리에 값의 지문. `from_snapshot` 은 그 자리에 스냅샷 필드의
  `FieldValue.value_fp`(= fp_of(value), 5.4)를 그대로 쓴다(값 재직렬화 없음). 직접 생성 `Projection(columns, extras)` 도 같은 식이라
  같은 열 값·extras 면 두 경로의 fp 가 같다.
- 불변식(옛 `fp_of((columns, extras))` 와 같은 동치 관계): 같은 열 값·extras 면 같은 fp, reads 선언 순서와 무관; 선언 열의 어느
  값·key 하나 또는 extras 가 다르면 다른 fp(값 지문이 다르므로 -- sha256 충돌 제외). fp 문자열 자체는 옛 식과 다르다(어떤 소비자도
  그 문자열을 다른 식으로 다시 만들지 않는다 -- 봉인 4 는 `Projection.from_snapshot(...).fp` 를 다시 부른다).
- 실패: extras 가변 -> `TypeError`; 선언 밖 열 -> `KeyError`; 열에 없는 key 의 `value` -> `KeyError`.

---

## 9. PDK 선언 `read_pdk_decl(decl_path, memo) -> PdkDecl` (계획 N3.16 'PDK 상수', U-30, WP-03, DEC-80 (i), DEC-91, DEC-93 (5), LY10)

근거: PDK 상수는 한 곳 선언, 값마다 출처 규칙 번호, 코드에 숫자를 박지 않는다. 소비자: MOD7 `LayoutPdk`(layout CONTRACT 4.1·4.10 --
`manufacturing_grid_m` 과 `PDK_RULE_QUANTITIES` 다섯 길이 + `rule_ids`), metrics 접합 용량(metrics CONTRACT 8절 -- 모델 카드 접합
파라미터 `junction_<kind>_<BSIM4 이름>` 과 LUT 생성 규칙 확산 기하 `lut_diffusion_*`, DEC-91).
- 양의 값 `value_m` 은 원본 단위 표(`units_m`)로 환산한 **SI 값**이다(길이 양은 m, 면적 m², 접합 용량 F/m²·F/m, 전위 V, 무차원, `tnom` °C --
  단위는 양 이름·`basis` 가 적는다; 필드 이름 `value_m`·`units_m` 은 r1 그대로).

### 9.1 선언 파일 (JSON, UTF-8) -- PDK 마다 데이터 하나 (sky130 = `skills/analog-gmid-design/assets/sky130_pdk_decl.json`)
- 최상위는 JSON 객체(배열·수·문자열이면 `pdk_decl_shape`). 키 정확히 `schema`(= `"gmid_pdk_decl/1"`), `pdk`(비지 않은 문자열),
  `pdk_root`(비지 않은 문자열), `sources`(비지 않은 객체), `quantities`(비지 않은 객체) + 선택 `note`·[U3] `mismatch_models`·`resistor_types`
  (9.6·9.7). 그 밖 키·빠진 키 -> `pdk_decl_keys`;
  `pdk`·`pdk_root`·`sources`·`quantities`·`sources.<이름>`·`quantities.<이름>` 의 타입·빈 값 위반 -> `pdk_decl_shape`.
- `sources.<이름>`: 경로는 `pdk_root + "/" + path`(선택 `base` 가 `"decl_dir"` 이면 `선언 파일 폴더(절대 경로) + "/" + path`). 공통 키
  `path`(비지 않은 문자열), `sha256`(정확히 64자 **소문자** hex 문자열 -- 아니면
  `pdk_decl_shape`, 형식은 맞는데 파일 값과 다르면 `pdk_source_sha256_mismatch`), `format`, `encoding`(원본 파일 바이트를 글로 풀 때 쓰는
  파이썬 코덱 이름, 예 `"utf-8"` -- 문자열이 아니거나 알 수 없는 코덱이면 `pdk_decl_shape`; 선언 파일 자체는 늘 UTF-8),
  `units_m`(단위 글자 -> SI 배율, 양의 유한 수(bool 아님), 비지 않은 객체) + 선택 `note`, 선택 `base`(`"pdk_root"`(기본)|`"decl_dir"`,
  그 밖 값·비문자열 -> `pdk_decl_shape`), 선택 `newline`(`"lf"` 만 -- 그 밖 -> `pdk_decl_shape`; 있으면 파일 바이트의 `\r\n` 을 `\n` 으로
  바꾼 뒤 sha256 을 재고 그 바이트를 푼다 -- 체크아웃마다 줄 끝이 바뀌는 저장소 안 원본용, 선언 sha256 = git blob 내용의 sha256;
  없으면 원본 바이트 그대로). `format`:
  - `"lef_statement"`: 줄에서 `#` 뒤를 버리고 `^\s*KEY\s+값\s*;\s*$` 인 줄마다 규칙 `KEY`(단위 글자 `""`). 그 밖 키 없음.
  - `"rule_table_csv"`: 추가 키 `section_pattern`(정규식 문자열, 그룹 1 = 접두), `section_column`·`id_column`·`value_column`·`unit_column`
    (열 번호, 0 이상 int, bool 아님). 정규식이 문자열이 아니거나 컴파일되지 않음, 열 번호가 정수 아님·음수·bool -> `pdk_decl_shape`.
    CSV 행을 차례로: section 열이 정규식에 맞으면 접두를 바꾸고, 아니면 접두가 있고 id 열이 비지 않을 때 규칙 `접두 + "." + id`
    (값 글자 = value 열, 단위 글자 = unit 열, 없는 열은 `""`, 행 번호 = csv `line_num`).
  - **SPICE 값 글자**(아래 두 형식 공통): `키 = 값` 쌍은 정규식 `([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\{[^}]*\}|'[^']*'|[^\s(){}=']+)` 로 찾고,
    키는 **소문자로** 바꾼다(SPICE 는 대소문자 무관 -- 선언 식도 소문자로 쓴다). 값이 `수(부호·소수·지수 허용) + 영문자*` 꼴이면 값 글자 =
    수 부분, 단위 글자 = 뒤 영문자(소문자로) -- 예 `2.5p` -> ("2.5", "p"), `0.44` -> ("0.44", ""); 그 꼴이 아니면(`{식}`·`'식'`) 값 글자 =
    그대로, 단위 글자 `""`(식이 그 규칙을 쓰면 `pdk_rule_not_numeric`).
  - `"spice_model_card"`(DEC-91 접합 파라미터): 추가 키 `model_pattern`(정규식 문자열 -- 모델 이름 전체 일치(`fullmatch`, 대소문자 그대로)).
    줄 단위로: 빈 줄·`*` 로 시작하는 줄은 건너뛴다; 줄의 `공백 + $` 또는 `공백 + ;` 뒤는 주석으로 버린다; `^\s*\.model\s+<이름>\s+<형>...`
    (대소문자 무관) 줄은 블록 머리 -- 이름이 `model_pattern` 에 맞으면 새 블록(머리 줄 나머지의 `키 = 값` 도 읽는다), 아니면 블록 밖;
    `+` 로 시작하는 줄은 블록 안이면 그 뒤를 읽는다; 그 밖 줄은 블록을 닫는다. 규칙 이름 두 가지:
    `<모델 이름(소문자)>.<키>` = bin 별(블록에서 나온 항목 그대로), `<키>` = bin 공통 -- 맞은 블록 전부의 (값 글자, 단위 글자) 가 하나면
    항목 1개(행 = 첫 블록에서의 행), 블록마다 다르거나 어느 블록에 키가 없으면(없는 블록은 (`""`, `""`, 그 블록 머리 행) 으로 셈) 서로 다른
    값마다 항목 하나 -> 식이 쓰면 `pdk_rule_ambiguous`(그때는 bin 별 이름을 써야 한다). 맞는 블록이 없으면 모든 규칙이 `pdk_rule_missing`.
  - `"spice_instance_line"`(LUT 생성 규칙 확산 기하): 추가 키 `line_pattern`(정규식 문자열, `re.search`). 맞는 줄마다 그룹이 있으면 그룹 1,
    없으면 맞은 글자 전체에서 `키=값` 을 읽어 규칙 `<키>` 항목(행 = 그 줄)을 더한다 -- 두 줄 이상에 나온 키는 쓰이면 `pdk_rule_ambiguous`.
  - 정규식 키(`section_pattern`·`model_pattern`·`line_pattern`)가 문자열이 아니거나 컴파일되지 않으면 `pdk_decl_shape`.
  - 그 밖 format -> `pdk_source_format_unknown`; 형식별 키가 다르거나 빠짐 -> `pdk_decl_keys`; `units_m` 위반 -> `pdk_source_units_invalid`.
  - 원본 하나의 검사 순서: 객체 아님(`pdk_decl_shape`) -> format -> 키 집합 -> `units_m` -> 값 모양(`pdk_decl_shape`) -> 파일 존재 -> sha256 대조.
- `quantities.<이름>`: 키 정확히 `source`, `expression`, `basis`. 셋 다 문자열이어야 하고(아니면 -- 예 `expression: 5` -- `pdk_decl_shape`),
  `basis`(유도 근거 글)는 비지 않아야 한다(`pdk_decl_shape`). `expression` = 산술식: 수(int·float), `+ - * /`, 단항 `-`, 괄호,
  `max(...)`·`min(...)`(위치 인자 1개 이상, 키워드 없음), 그리고 **규칙 이름**(정규식 `[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)*`, 앞이
  숫자·`.`·글자가 아닌 곳; `max`·`min` 제외 -- 점으로 이어진 낱말 전체가 규칙 이름 하나라 `poly.2.x` 는 속성 접근이 아니라 규칙 `poly.2.x`).
  규칙 이름은 모두 `source` 원본에서 찾는다.
- **식 검사 순서**(앞 단계에서 걸리면 그 사유): (1) `source` 가 `sources` 에 없음 `pdk_source_undeclared` (2) 공백뿐인 식
  `pdk_expression_invalid` (3) 문법 오류 `pdk_expression_invalid` (4) **모양 검사 -- 규칙 이름을 찾기 전에**: 허용 밖 노드(`max`·`min` 밖
  함수 호출(`abs(...)`, `__import__(...)` 등 -- 함수 자리의 낱말은 이름 조회 없이 거부), 키워드 인자(`max(a, key=b)`), 문자열 상수
  (`'a'`), bool, `**`·`%`·`//`, 비교, 단독 `max` 등) -> `pdk_expression_invalid` (5) 규칙 이름이 하나도 없음 `pdk_expression_invalid`
  (6) 규칙 이름을 등장 순으로 찾음: `pdk_rule_missing`·`pdk_rule_ambiguous`·`pdk_rule_not_numeric`·`pdk_rule_unit_unknown`
  (7) 계산 중 0 나누기 `pdk_expression_invalid` (8) 결과가 유한하지 않거나 **음수** `pdk_quantity_invalid` -- **정확히 0 은 허용**
  (layout `LayoutPdk` 길이는 >= 0).

### 9.2 결과
- `PdkDecl(pdk, decl_path, decl_sha256, sources, quantities, mismatch_models=())` -- frozen, `require_immutable` 통과, `fp_of` 결정론.
  [U3] `mismatch_models` = ((kind, `PdkMismatchModel`), ...) kind 정렬; `decl.mismatch_model(kind)` (선언에 없으면 `pdk_mismatch_undeclared`).
  `sources` = ((원본 이름, 경로, sha256), ...) 이름 정렬, `quantities` = ((이름, `PdkQuantity`), ...) 이름 정렬.
- `PdkQuantity(name, value_m, expression, rules, basis)`: `value_m` = 식에 규칙 값(m)을 넣은 float, `expression` = 선언 글 그대로,
  `rules` = 식에 나온 규칙 `PdkRule` 들(첫 등장 순, 중복 없음).
- `PdkRule(rule_id, value_m, value_text, unit_text, source, path, sha256, line)`: `value_m = float(value_text) x units_m[unit_text]`.
- `decl.quantity(name)` / `value(name)` / `values(names)`(순서 그대로 tuple) / `rule_ids(names)` = `((name, expression), ...)`.
  선언에 없는 이름 -> `pdk_quantity_undeclared`.
- 캐시: 원본마다 매 호출 sha256 을 다시 재고, 파싱 결과는 `memo.lookup((format, sha256, 파싱 인자), ...)` -- 같은 원본·같은 파싱 인자로
  두 번 부르면 두 번째는 memo 적중(파싱 0). 모듈 수준 캐시 없음.

### 9.3 실패 (전부 `SchemaRejectedError`, `record.detail["reason"]` = 아래 키) -- `memo` 가 `BoundedLRU` 아니면 `TypeError`
| reason | 조건 |
|---|---|
| `pdk_decl_missing` | 선언 파일 없음 |
| `pdk_decl_json` | JSON 문법 오류 |
| `pdk_decl_keys` / `pdk_decl_schema` | 키 집합 위반 / schema 값 다름 |
| `pdk_decl_shape` | 모양 위반: 최상위가 객체 아님(배열 등), `pdk`·`pdk_root` 빈/비문자열, `sources`·`quantities` 가 비지 않은 객체 아님, 원본·quantity 항목이 객체 아님, `path`·`encoding` 빈/비문자열, 알 수 없는 코덱, `sha256` 이 64자 소문자 hex 아님, `base` 가 `"pdk_root"`·`"decl_dir"` 밖(비문자열 포함), `newline` 이 `"lf"` 아님, 정규식 키(`section_pattern`·`model_pattern`·`line_pattern`) 비문자열·컴파일 실패, 열 번호가 0 이상 int 아님(bool 포함), quantity 의 `source`·`expression`·`basis` 비문자열, 빈 `basis` |
| `pdk_source_missing` / `pdk_source_sha256_mismatch` | 원본 파일 없음 / sha256 이 선언과 다름 |
| `pdk_source_undeclared` | quantity 의 `source` 가 `sources` 에 없음 |
| `pdk_rule_missing` / `pdk_rule_ambiguous` | 식의 규칙이 원본에 없음 / 두 번 이상 나옴(쓰일 때만 거부) |
| `pdk_rule_not_numeric` / `pdk_rule_unit_unknown` | 값 글자가 수가 아님(`N/A`, `0.170 *L` 등) / 단위 글자가 `units_m` 에 없음 |
| `pdk_expression_invalid` | 공백뿐인 식·규칙 이름 없는 식·문법 오류·허용 밖 노드(다른 함수, 키워드 인자, 문자열 상수, `**` 등 -- 규칙 이름 조회보다 먼저, 9.1 순서)·0 나누기 |
| `pdk_quantity_invalid` | 결과가 유한하지 않거나 음수(정확히 0 은 허용) |
| [U3] `pdk_mismatch_no_blocks` / `pdk_mismatch_parameter_unused` / `pdk_mismatch_undeclared` | mismatch 모델 원본에 `lmin` 블록이 없음 / 선언한 변수를 쓰는 블록이 하나도 없음 / `decl.mismatch_model(kind)` 인데 선언 없음 |
| [U3] `pdk_quantity_duplicate` | `resistor_types` 가 낸 이름이 `quantities` 에 이미 있음 |

### 9.4 sky130 실값 (2026-10-07, 선언 sha256 은 커밋본 기준으로 재야 한다)
원본: tlef `C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef`(sha256 `c8351e32...`), 공식 periphery 규칙표
`C:/pdk/skywater-pdk/docs/rules/periphery/periphery.csv`(sha256 `432c56b9...`, google/skywater-pdk 7198cf64, 같은 폴더 `PROVENANCE.txt`).

| 이름 | 식 | 값 |
|---|---|---|
| `manufacturing_grid_m` | `MANUFACTURINGGRID`(tlef 29행 0.005) | 5e-9 |
| `finger_pitch_overhead_m` | `max(poly.2, licon.1 + 2 * licon.11)`(402·624·642행 0.210·0.170·0.055) | 2.8e-7 |
| `row_gap_m` | `max(difftap.3, poly.8 + poly.2 + poly.8)`(324·408·402행) | 4.7e-7 |
| `dummy_w_m` | `poly.1a + poly.7 + max(poly.2, licon.1 + 2 * licon.11) / 2`(400·407행 ...) | 5.4e-7 |
| `tap_w_m` | `difftap.3 + max(difftap.1, licon.1 + 2 * licon.7)`(324·320·624·637행) | 6.8e-7 |
| `well_spacing_m` | `max(nwell.2a + 2 * difftap.8, difftap.9 + difftap.8)`(121·329·330행) | 1.63e-6 |
| `min_finger_w_m` [2026-10-08 추가] | `difftap.2`(321행 0.420 µm, areaid.sc 밖 FET 최소 채널 폭) | 4.2e-7 |

| `mim_cap_density_f_per_m2` [2026-10-08 추가, 사용자 결정 11] | `camimc`(`models/r+c/res_typical__cap_typical__lin.spice` 의 `.param` 줄, `spice_instance_line`, 원본 F/µm² x units_m 1e12) | 2.0e-3 |

`mim_cap_density_f_per_m2` 는 MIM 커패시터 단위 면적 용량(sky130 typical 모서리, 공개 문서 ~2 fF/µm² 와 일치)이다. cap_mim_m3 셀 모델
원본이 로컬에 없어 이 모서리 파라미터가 유일한 로컬 출처다. 소비자 `search.passive_area_decl`(수동 커패시터 면적 = 값 / 이 값).

`min_finger_w_m` 은 MOD6 설계 개정 S-18(search W ≥ W_min 제약, 소비자 `search.build_search_context`)로 더한 quantity 다. 선언 형식·
읽기 규칙은 9.1~9.3 그대로이고 엔진 코드 변경은 없다(선언 파일 sha256 은 바뀐다).

(값은 float 연산 결과 그대로 -- 예 `row_gap_m` = 4.6999999999999995e-07. test 는 손계산과 상대 오차로 비교한다.)
식(기하 해석)은 선언 파일의 `basis` 에 적었고 사용자 ratify 대상이다.
**[2026-10-08] 사용자 ratify 완료**(출처: 사용자 결정, 오케스트레이터 전달 2026-10-08): 레이아웃 길이 다섯 식 `finger_pitch_overhead_m`·
`row_gap_m`·`dummy_w_m`·`tap_w_m`·`well_spacing_m` 을 위 표 그대로 승인. 적용 확인(layout 계약 4.10): well 간격은 (kind, body) well 이
다른 묶음 사이에만 들어간다; `dummy_w_m` 의 `overhead/2` 항은 끝 확산이 nf+1 개라 끝 하나당 반 피치가 맞고 dummy L = poly.1a 는
periphery.csv `X.1a`(dummy_poly L = 그 소자 최소 L)가 정한다 -- 식 변경 없음. (`min_finger_w_m`·접합 파라미터는 이 ratify 범위 밖.)

**접합 파라미터(DEC-91, 2026-10-08)** -- 같은 선언 파일에 원본 둘 추가: `nfet_01v8_tt_model_card` =
`C:/pdk/sky130_fd_pr/cells/nfet_01v8/sky130_fd_pr__nfet_01v8__tt.pm3.spice`(sha256 `eec2f478...`, `model_pattern`
`sky130_fd_pr__nfet_01v8__model\.[0-9]+` -> 블록 180개), `pfet_01v8_tt_model_card` = `.../pfet_01v8/sky130_fd_pr__pfet_01v8__tt.pm3.spice`
(sha256 `3ecdcb8c...`, 블록 108개) -- 둘 다 LUT v2 meta `model_files_sha256` 과 같은 파일, `units_m` `{"": 1.0}`. 줄 끝(정정
2026-10-08): `C:/pdk/sky130_fd_pr` 는 git 체크아웃이고(`core.autocrlf=true`) **git blob 은 LF, 이 설치의 작업 사본은 CRLF**
(`git ls-files --eol` 실측 `i/lf w/crlf`, 두 파일 모든 줄 CRLF). 선언 sha256 은 작업 사본(CRLF) 바이트 값 = LUT meta 가 기록한 값이라
`newline` 키를 두지 않는다. LF 로 체크아웃한 다른 설치(또는 LF 사본)에서는 `pdk_source_sha256_mismatch` 로 거부된다 -- 그때는 그 설치의
바이트로 선언을 다시 고정하거나 `newline: "lf"` + blob sha256 으로 바꾼다(LUT meta sha256 과는 어긋남을 감수). 파서는 줄 끝과 무관하다.
양 이름 `junction_<kind>_<BSIM4 이름>`(kind = `nmos`·`pmos`, 이름 = metrics `JunctionParams` 필드 27개). 접합 파라미터는 **bin 전부에서
같은 값**(작성자 전수 확인 2026-10-08)이라 식은 bin 공통 규칙 이름이다. drain 쪽 이름(cjd·cjswd·cjswgd·mjd·mjswd·mjswgd·pbd·pbswd·pbswgd)은
모델 카드에 없어 식이 source 쪽 규칙(BSIM4 기본값: 미지정 drain = source). `dwj` 식 = `dwc - xw / 2`(dwj 미지정 -> dwc, Weffcj 의 xw 포함).

| kind | cjs | cjsws | cjswgs | mjs | mjsws | mjswgs | pbs | pbsws | pbswgs | tcj | tcjsw | tcjswg | tpb | tpbsw | tpbswg | tnom | permod | dwj |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| nmos | 0.001339749237 | 3.67354204e-11 | 2.38232788e-10 | 0.44 | 0.0009 | 0.8 | 0.729 | 0.2 | 0.95578 | 0.000792 | 1e-05 | 0.0 | 0.0012287 | 0.0 | 0.0 | 30.0 | 1.0 | 0.0 |
| pmos | 0.0007380194454 | 9.888892e-11 | 2.39155046e-10 | 0.34629 | 0.29781 | 0.9274 | 0.6587 | 0.7418 | 1.4338 | 0.0012407 | 0.00037357 | 2e-12 | 0.0020386 | 0.001246 | 0.0 | 30.0 | 1.0 | 0.0 |

규칙 행(nfet 파일, 첫 블록 `sky130_fd_pr__nfet_01v8__model.0`): cjs 231, pbs 230, tnom 240, permod 47, dwc 175, xw 216(pfet: cjs 277,
tnom 38, permod 69). 거부 실례: 식 `vth0`(bin 마다 값이 다름) -> `pdk_rule_ambiguous`, `sky130_fd_pr__nfet_01v8__model.26.vth0`(값이
`{...}` 식) -> `pdk_rule_not_numeric`, `dwj` -> `pdk_rule_missing`, `sky130_fd_pr__nfet_01v8__model.26.cjs` -> 0.001339749237(행 7199).

**LUT 생성 규칙 선언** `skills/analog-gmid-design/assets/sky130_lut_rule_decl.json`(같은 스키마, 2026-10-08): 원본 `lut_generator` =
`base: "decl_dir"` + `sky130_lut_sweep.py`(LUT 생성기), `newline: "lf"`, sha256 `735220532101...`(git blob -- [U3] 생성기에 `.noise`·mismatch 모드를 더해 바뀜; DUT 줄은 그대로 90행), `spice_instance_line`,
`line_pattern` `^DUT_LINE\s*=\s*"([^"]*)"`(90행, 글자 `xdut d g s b sky130_fd_pr__{devcell} l={L_um}u w=5u ad=2.5p as=2.5p pd=7u ps=7u`),
`units_m` `{"u": 1e-6, "p": 1e-12}`.

| 이름 | 식 | 값 |
|---|---|---|
| `lut_diffusion_ad_per_w_m` | `ad / w` (2.5e-12 / 5e-6) | 5e-7 |
| `lut_diffusion_as_per_w_m` | `as / w` | 5e-7 |
| `lut_diffusion_pd_extra_m` | `pd - w` (7e-6 − 5e-6) | 2.0000000000000003e-06 |
| `lut_diffusion_ps_extra_m` | `ps - w` | 2.0000000000000003e-06 |

(규칙 `l` 의 값 글자는 `{L_um}` -> 쓰이면 `pdk_rule_not_numeric`.)

### 9.4b [U3, 2026-10-08] 잡음·mismatch·저항 PDK 양 (`sky130_pdk_decl.json` 추가분, 설계 41 §6.4-2·§7.2, 40 §7.1 Q9)
새 원본 4개(전부 `pdk_root` 기준, sha256 고정): `nfet_01v8_mismatch_slopes`·`pfet_01v8_mismatch_slopes`(= 모델 카드가 include 하는 `*__mismatch.corner.spice`,
형식 `spice_instance_line`, `line_pattern` `^\.param\s+(.*)$` -> 규칙 이름 = `.param` 이름 소문자, 값은 수), `scale_option`(`models/all.spice` 2행 `.option scale=1.0u`,
`units_m` `{"u": 1e-6}`), `poly_res_params`(`models/r+c/res_typical__cap_typical.spice` 21행 `rp1 = 48.2`).

| 이름 | 식(원본) | 값 | 쓰임 |
|---|---|---|---|
| `noise_ef_nmos` / `noise_ef_pmos` | `ef`(모델 카드 bin 공통 키, nfet 201행·pfet 223행) | 0.84 / 1.0 | 잡음 LUT 의 1/f 지수 EF -- `LutSpec.noise_ef` 의 출처(lut CONTRACT 9) |
| `noise_fnoimod_*` / `noise_tnoimod_*` | `fnoimod` / `tnoimod` | 1.0 | unified flicker·holistic thermal 전제 -- 소비자가 1 인지 확인 |
| `mismatch_slope_geometry_unit_m` | `scale`(all.spice 2행) | 1e-6 | mismatch 식 `sqrt(l*w*mult)` 의 l·w 가 µm 수치로 읽히는 배율(아래 단위 확인) |
| `poly_generic_sheet_ohm_per_sq` | `rp1` | 48.2 | poly 저항 R□ [Ω/□] |
| `poly_generic_min_w_m` | `poly.3` | 3.3e-07 | poly 저항 최소 폭 |
| `poly_generic_head_area_m2` | `2 * poly.3 * (licon.1 + 2 * licon.8a)` | 2.178e-13 | 저항마다 한 번 더하는 접촉 머리 면적(레이아웃 기하 해석 -- 사용자 ratify 대상) |
| `poly_res_sheet_ohm_per_sq` / `poly_res_min_w_m` / `poly_res_head_area_m2` | `resistor_types` 규칙이 고른 후보의 양(9.7) | 48.2 / 3.3e-07 / 2.178e-13 | search `passive_area_decl`(저항 단위 면적 W_min²/R□ = 2.2593e-15 m²/Ω + 머리) |

**단위 확인(41 §6.4-2 '구현 첫 커밋에서 ngspice 소자 쌍 MC')**: 모델 카드는 `p = p0 + p_slope_spectre·(p_slope/sqrt(l·w·mult))` 로 변수를 흔들고, 모델 파일 최상위
`.option scale=1.0u` 아래에서 소자 줄의 l·w 숫자(단위 글자 없음)는 µm 이다. 그래서 spectre std = 1.0 일 때 vth0 의 1σ = `vth0_slope`/√(l·w[µm²])(V), 즉 slope 의 길이
단위는 µm 다(`vth0_slope` 3.356e-3 V·µm 등). LUT 생성기 DUT 줄처럼 l·w 를 `0.5u` 로 m 로 직접 주면 같은 1σ 가 `*_slope_spectre` = `scale` = 1e-6 이다. 두 표기가 같은 1σ 임을
ngspice 쌍 MC(`assets/sky130_pair_mc.py`, 같은 난수·같은 전류에서 σ(ΔVGS) 비트 동일)로 확인했고, 쌍 σ·√(W·L) = √2·slope(vth0 만 흔들 때)와 일치함도 확인했다 -- 결과 표와 표본 수·재현 명령은
`docs/03-analysis/gain-budget-gmid-sizing.u3-lut-pdk-record.md`. 출처: 파일 sha256·행 = `PdkRule.sha256`·`line` (`scale` 2행, `vth0_slope` 등 mismatch 파일 행).

### 9.6 [U3] `mismatch_models` -- bin 별 mismatch slope 지도
`"mismatch_models": {<kind>: {"model_source": <원본 이름>, "slope_source": <원본 이름>, "parameters": [<BSIM4 변수 이름>, ...]}}`. `model_source` = `spice_model_card` 원본,
`slope_source` = `.param 이름=값` 줄을 규칙으로 읽는 `spice_instance_line` 원본. 결과 `PdkMismatchModel(kind, parameters, blocks, model_path, model_sha256, slope_path, slope_sha256)`,
`blocks` = `PdkMismatchBlock(model, lmin_m, lmax_m, wmin_m, wmax_m, slopes, line)` ((wmin, wmax, lmin, lmax, 이름) 정렬; `.model` 블록마다 하나).
`slopes` = ((변수, slope 이름, slope 값, slope 원본 행), ...) 선언 순서 -- 블록의 변수 식 `{p0 + <..._slope_spectre>*(<slope 이름>/sqrt(l*w*mult))}` 에서 slope 이름을
정규식 `([A-Za-z_]\w*_slope\d*)\s*/\s*sqrt` 로 읽고(이름은 bin 마다 `slope`·`slope1` 로 다르다), 식이 없으면 (변수, None, None, None). 경계 `lmin·lmax·wmin·wmax` 는 모델 카드 값(단위 표 `""`).
거부: 4 키 위반 `pdk_decl_keys`, `parameters` 모양 `pdk_decl_shape`, 원본 이름 없음 `pdk_source_undeclared`, `lmin` 블록 없음 `pdk_mismatch_no_blocks`, 선언 변수를 쓰는 블록이 없음
`pdk_mismatch_parameter_unused`, slope 이름이 slope 원본에 없음/모호/비수 -> `pdk_rule_missing`·`pdk_rule_ambiguous`·`pdk_rule_not_numeric`.
sky130 실측: nmos 180 블록 -- `vth0_slope1`(7.356e-3) 4 블록(L 4–8 µm·좁은 W), 나머지 `vth0_slope`(3.356e-3); pmos 108 블록 -- L < 0.5 µm 36 블록 `vth0_slope1`(7.356e-3),
L ≥ 0.5 µm `vth0_slope`(5.856e-3). 옛 `legacy/sizing_recipe.py:3073` 은 pfet 에 5.856e-3 하나만 썼다(결함, 대조 기준선으로만 기록).
bin 소속 판정(`bin_index`, 양끝 닫힘·경계 공유 시 아래 bin)은 lut `mismatch_sigma_vgs` 가 한다(core 는 지도만 준다).

### 9.7 [U3] `resistor_types` -- Ω당 면적이 가장 작은 저항 종류
`"resistor_types": {"selected_as": <접두>, "candidates": {<이름>: {"sheet_ohm_per_sq": <quantity 이름>, "min_w_m": <quantity 이름>, "head_area_m2": <quantity 이름>}}}`.
후보마다 본체 Ω당 면적 W_min²/R□ [m²/Ω]를 계산해 가장 작은 후보(동률은 이름 순)의 세 양을 `<접두>_sheet_ohm_per_sq`·`<접두>_min_w_m`·`<접두>_head_area_m2` 이름의
`PdkQuantity`(식 = `select_min_area_per_ohm(<후보>.<양>)`, `rules` = 그 후보 양의 규칙, `basis` = 선택 규칙 + 후보별 m²/Ω)로 `quantities` 에 더한다 -- **고정 상수가 아니라 규칙**(사용자 결정 Q9).
거부: 키 위반 `pdk_decl_keys`/`pdk_decl_shape`, 후보가 가리키는 양이 없음 `pdk_quantity_undeclared`, R□ <= 0 `pdk_quantity_invalid`, 이름이 이미 있음 `pdk_quantity_duplicate`.
sky130 로컬 PDK(sparse checkout)에는 `cells/` 에 nfet_01v8·pfet_01v8 만 있어 정밀 poly 저항(res_high_po·res_xhigh_po)의 시트 저항을 읽을 수 없다 -- 후보는 `poly_generic`(res_generic_po) 하나뿐이고,
다른 후보는 선언만 더하면 같은 규칙이 고른다(모델 파일 확보 뒤 사용자 결정).

### 9.5 소비자 호출 (layout 브랜치 병합 시 `LayoutPdk` 를 만드는 쪽)
```python
from gmid_engine.core import BoundedLRU, read_pdk_decl
decl = read_pdk_decl(decl_path, memo)            # memo = 부르는 쪽 BoundedLRU(원본 수 이상)
pdk = LayoutPdk.from_lut(lut, *decl.values(PDK_RULE_QUANTITIES), decl.rule_ids(PDK_RULE_QUANTITIES))
```
`PDK_RULE_QUANTITIES` 순서 = `from_lut` 위치 인자 순서(overhead, gap, dummy, tap, well). 격자는 `from_lut` 가 `lut.spec.manufacturing_grid_m`
에서 읽으므로 LUT 를 만드는 쪽이 `LutSpec(decl.value("manufacturing_grid_m"), ...)` 로 같은 선언값을 쓴다.

접합 용량 소비자(DEC-91): `metrics.JunctionParams.from_pdk_decl(decl, kind)`·`metrics.DiffusionGeometry.from_lut_rule(lut_rule_decl, finger_w, m)`
-> `metrics.junction_caps(...)` (metrics CONTRACT 8.5 -- ss_linearize `ss_dev` 가 부른다). 두 선언을 같은 memo 로 읽으면 원본 5개
(memo 상한 5 이상이면 두 번째 호출부터 파싱 0).

---

## 10. 성능 실측 (2026-10-08, 개정 근거 -- sizing O9)
- 조건: `tests/search/test_kernel.py` 15개 test(S0 컨텍스트 생성 + `evaluate` 반복) 를 cProfile 로 실행, `Projection.from_snapshot` 971 호출.
  - 옛 식 `fp_of((columns, extras))`: `from_snapshot` 누적 1.57 s(호출당 1.6 ms), 그 중 지문 1.40 s.
  - 값 지문 합성(열 지문 = 값 지문들의 sha256 한 번): `from_snapshot` 누적 0.80 s(호출당 0.82 ms), 그 중 지문 0.51 s. 약 49 % 감소.
  - 남은 지문 시간의 대부분은 호출자가 넘기는 `extras` 의 직렬화(`fp_of`)이고 열 지문(`_column_fp`)은 0.07 s.
- 같은 실행의 `fp_of` 재귀 호출 수 285,299 -> (값 지문 합성) 감소. 실행 전체 시간은 컴퓨터 부하(파일 열기 지연)로 흔들려 비교에 쓰지 않는다.

### 10.1 core 성능 2~5 실측 (2026-10-08, 사용자 승인 "2번 + 1번으로 진행해. 나머지도 함께 진행해.")
- 조건: 9회로 표준 탐침 θ(회로당 215 + 통과 θ 의 FD 형제), LUT v2, `fp_of`·`canonical_key`·`require_immutable` 을 최상위 호출 단위로 `perf_counter` 계측(재귀 중복 제외). 옛/새 엔진 동시 실행(같은 부하).
- 계측 합(초, 옛 -> 새): common_gate 26.0 -> 7.2, current_reuse 10.4 -> 2.0, folded 50.9 -> 10.1, ngcc 84.9 -> 15.5, nmcnr 27.0 -> 7.3,
  pushpull_follower 2.3 -> 0.4, sf_pushpull 20.6 -> 2.7, two_stage 32.9 -> 5.0, two_stage_sf 21.9 -> 4.0 (fp_of+require_immutable+canonical_key).
- 평가당 CPU(ms, 옛 -> 새, 부하 잡음 있음): common_gate 24.8 -> 13.0, folded 116.5 -> 83.7, ngcc 46.7 -> 21.2, nmcnr 57.7 -> 34.1, two_stage 33.0 -> 18.0, sf_pushpull 336.6 -> 249.9.
- two_stage find_front(E_B=150) 는 LUT 역산이 지배해 비프로파일 CPU 차이가 부하 잡음 안(최소값 32.1 s -> 30.2 s); fp 계열 호출 합 2.8 s -> 0.8 s.
- 동일성: perf 계수(kernel_calls 100, unique_keys 100, recompute_same_key 0, block 1074/896/178/48)·front·evals(code_fp 제외)·schema_fp·w_fixed_fp·
  xcheck 4801줄(스냅샷 fp 포함) 옛/새 완전 일치. 바뀐 영속 값: 투영 지문 식 개정(8절)으로 archive 스냅샷 파일 필드의 `input_version` 문자열.

---

## 11. S0 수준 graph 스냅샷 영속화 (U17 단계 ①-a, 설계 40 §2.4.1 (d)·§2.4.3·§2.4.12 Q1·Q2, §3.10.11 U-68)

### 11.1 `type_registry() -> 등록부` (파일 `type_registry.py`, 층 0)
- 프로세스에 하나. `.register(cls)`: frozen dataclass 클래스만(아니면 `TypeError`), 그대로 돌려준다. 같은 클래스 재등록은 무동작,
  같은 이름(`<모듈>.<qualname>`)의 다른 클래스는 `ValueError`. `.lookup(name)` / `.name_of(cls)`: 목록 밖이면 `KeyError`. `.names()`: 정렬 tuple.
- 등록은 각 패키지 `__init__` 이 한다(아래에서 위로). 지금 등록 = graph S1 필드 값 형식 12개(`BulkResult`, `Evidence`, `Segment`, `Branch`,
  `Column`, `ColumnOrphan`, `GsGroup`, `DcRole`, `RelEdge`, `MatchingGroup`, `MatchingDisposition`, `GvgsSummary`). core 는 등록하지 않는다.

### 11.2 `engine_code_fp(engine_root=None) -> str | None` (파일 `engine_code_fp.py`, 층 1)
- `engine_root`(기본 = `gmid_engine` 폴더) 아래 `.py` 중 `tests/`·숨김 폴더·`__pycache__` 밖 파일마다 (posix 상대 경로, 바이트 sha256) 을
  상대 경로로 정렬한 tuple 의 `fp_of`. 폴더가 아니거나 대상 파일 0 이면 None. 파일 하나의 바이트가 바뀌면 값이 바뀐다.
- 소비자: S0 수준 스냅샷 키 (iii), S3 기록의 `code_fp`(`search.build_search_context`, 옛 6개 패키지 `_code_fp` 대체).

### 11.3 `S0SnapshotStore(directory, code_fp)` -- frozen dataclass (파일 `snapshot_codec.py`, 층 4)
- `S0SnapshotStore.default(code_fp)`: `directory` = `gmid_engine/.s0_snapshot`(저장소 `.gitignore`). `directory`·`code_fp` 가 빈 문자열이거나
  문자열이 아니면 `ValueError`.
- `key_of(inputs, sources) -> dict`: `inputs` = {비어 있지 않은 이름(`KEY_CODE_FP`="engine_code_fp" 와 `source.` 접두 금지): 문자열 | None},
  `sources` = {비어 있지 않은 역할: (경로 | None, 원본 바이트 sha256 | None)}(경로 None 이면 sha256 도 None). 위반은 `TypeError`.
  결과 = `inputs` + 역할마다 `source.<역할>.path`(경로가 엔진 폴더 위 첫 `.git` 폴더(저장소 top) 안이면 `repo:<top 기준 posix 상대 경로>`,
  밖이면 `abs:<resolve 한 절대 posix 경로>`, 경로 None 이면 None)·`source.<역할>.sha256` 을 이름 정렬한 뒤 `KEY_CODE_FP`: code_fp.
  `path_of(inputs, sources)` = `<directory>/<fp_of(key_of(...))>.json.gz`.
- `load(inputs, sources) -> (GraphSnapshot | None, outcome)`: 파일 없음 -> (None, `OUTCOME_MISS`="miss"). 정상 -> (스냅샷, `OUTCOME_HIT`="hit"): 돌려준
  스냅샷의 `fp`·`block_versions`·`writers`·모든 필드의 값·writer·input_version·write_count 가 저장한 스냅샷과 같다. 다음은 전부
  (None, `OUTCOME_CORRUPT`="corrupt") + `RuntimeWarning`: gzip·JSON 깨짐, `body_sha256` 불일치, `schema_version` 다름, 저장된 `key` 가 `key_of(...)` 와 다름,
  권한표와 다른 writer 의 필드, 권한표 밖 writer 의 block_version, 등록부 밖 `__type__`, 타입 없는 JSON 값(맨 숫자 float·list·`__type__` 없는 객체),
  dataclass 필드 이름이 init 필드와 다름, 다시 만든 스냅샷 `fp` 가 저장된 `fp` 와 다름.
- `save(inputs, sources, snapshot) -> 경로 | None`: `snapshot` 이 GraphSnapshot 아니면 `TypeError`. 값에 등록부 밖 dataclass·지원 밖 형식이 있으면
  `TypeError`(파일을 쓰지 않는다). 키 파일이 이미 있고 `load` 가 hit 이면 쓰지 않고 그 경로. 아니면(없음·손상) 원자적으로 쓰고(같은 폴더 임시
  파일 -> `os.replace`, 손상 파일은 같은 이름으로 교체) 경로를 돌려준다. 쓰기 OSError 는 `RuntimeWarning` 뒤 None. 같은 입력·같은 스냅샷이면
  파일 바이트가 같다(gzip mtime 0, 정준 JSON).
- 파일 형식(gzip JSON): `{schema_version: 1, key, writers[[kind, field, writer]], block_versions{writer: 입력 버전}, records[{kind, key,
  fields{name: {value, writer, input_version, write_count}}}], fp, body_sha256}`. `body_sha256` = `body_sha256` 를 뺀 문서의
  `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True)` 바이트 sha256. 값 인코딩: None·bool·int·str 그대로, float
  `{"__type__": "float", "hex": float.hex(x)}`, bytes `{"__type__": "bytes", "hex"}`, tuple `{"__type__": "tuple", "items"}`, frozenset
  `{"__type__": "frozenset", "items"}`(원소 `fp_of` 오름차순), 등록 dataclass `{"__type__": "<모듈>.<qualname>", "fields": {init 필드: 값}}`.
- 옛 파일 정리(U-68, 사용자 결정 원문 범위 = topology·spec·LUT·PDK 선언·엔진 코드): `save` 가 실제로 쓴 뒤 1회. 폴더 안 `<64 소문자 hex>.json.gz`
  이름의 일반 파일(방금 쓴 파일·심볼릭 링크 제외, 읽을 수 없거나 키 모양이 틀린 파일은 건드리지 않음) 중 다음을 만족하는 checkout 이 하나도 없는
  파일만 지운다: 키의 `abs:` 입력 파일마다 지금 그 경로 파일의 원본 sha256 이 저장값과 같고(파일 없음 = None) / 이 저장소 top 과 `git worktree list` 의
  worktree W 중 하나에서 `W/<엔진 상대 경로>` 의 `engine_code_fp` 가 키의 `engine_code_fp` 와 같고 키의 `repo:` 입력 파일마다 `W/<상대 경로>` 원본
  sha256 이 저장값과 같다(없음 = None). git 실패면 아무것도 지우지 않는다. 엔진을 실행하지 않는다(원본 sha 와 코드 지문만 본다).
- 배선: `pipeline.run_stage_a` 가 S1 생성 경로에서 부른다(pipeline CONTRACT §1). 계수 `perf.s0_snapshot{hit, miss, corrupt}` 는 `RunCounters`
  (40 §2.4.9, 단계 ②) 몫이고, 지금은 단계 A 보고서 `s0_snapshot` 에 outcome 을 남긴다.
