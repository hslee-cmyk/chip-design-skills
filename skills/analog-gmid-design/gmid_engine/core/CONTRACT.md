# gmid_engine.core 동작 계약 (test 작성용)

- 대상: `gmid_engine/core/` 공개 API(`gmid_engine.core.__all__`). test 는 `from gmid_engine.core import ...` 만 쓴다
  (파일 모듈 직접 import·`_` 이름 사용 금지). 경로: `gmid_engine/tests/conftest.py` 가 패키지 부모 디렉터리를
  `sys.path` 앞에 넣는다(설치 불필요). test 파일 배치는 규칙 D: `gmid_engine/tests/core/test_<파일>.py`.
  같은 basename 이 다른 패키지 test 에도 생기므로 test 디렉터리에 `__init__.py` 를 두거나 `--import-mode=importlib` 를 쓴다.
- 근거: `_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항'(최우선)·1절·3.1·4절, 계획 N3.3·N3.4·N3.5·N3.14·NFR-2·NFR-4·WP-03·WP-10.
- 아래 "불변식"은 test 가 확인할 성질, "실패"는 반드시 그 예외로 거부해야 하는 입력이다.

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
- **광범위 except 0**: core 에 `except` 절 자체가 없다.
- **모듈 수준 가변 캐시 0**: 모듈 수준 dict/list/set 대입·`@lru_cache`/`@cache`·`global` 문 0(분류표는 읽기 전용 매핑).
- 자기 파일 self-test·`if __name__ == "__main__"` 0.

| 파일 | 층 | 독립 진입점 |
|---|---|---|
| determinism.py | 0 | `sorted_items` |
| fingerprint.py | 0 | `fp_of` |
| immutability.py | 0 | `require_immutable` |
| margin.py | 0 | `normalized_margin` |
| units.py | 0 | (공개 정의 0, 상수 표) `METRIC_UNITS`·`DOMAINS`·`AMPLITUDE_DB_PER_DECADE` -- 규칙 D 숫자 리터럴 예외 파일 |
| writer_error.py | 0 | `WriterPermissionError` |
| bounded_lru.py | 1 | `BoundedLRU` (`LruStats` 는 같은 파일 비진입 공개 이름) |
| failure_record.py | 1 | `FailureRecord` |
| field_value.py | 1 | `FieldValue` |
| metric_signature.py | 1 | (데이터 선언 모듈) `MetricSignature(unit, domain, view_kind, objective_axis)` -- unit·domain 은 units 표 안 |
| projection.py | 1 | `Projection` |
| writer_table.py | 1 | `WriterTable` (+ 상수 `ENTITY_KINDS`) |
| compute_block.py | 2 | `compute_block` (`ComputeBlock`·`BlockStats` 는 비진입 공개 이름) |
| failure_errors.py | 2 | (데이터 선언 모듈) N3.14 예외 클래스 7개 |
| graph_record.py | 2 | `GraphRecord` |
| failure_classes.py | 3 | (데이터 선언 모듈) `FailureClass` + 상수 `FAILURE_CLASSES`·`CANDIDATE_FAILURE_CLASSES`·`UNEXPECTED_EXIT_CODE` |
| graph_snapshot.py | 3 | `GraphSnapshot` |
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
- 실패: key 비문자열 -> `TypeError`; 필드 이름 빈/비문자열 -> `ValueError`; 필드 값이 FieldValue 아님 -> `TypeError`; 이름 중복 -> `ValueError`.

### 5.6 `GraphSnapshot` -- 불변 스냅샷 (직접 생성하지 말고 `GraphSnapshot.empty(writers)` + `write`)
- `empty(writers)`: 레코드 0. `writers` 가 WriterTable 이 아니면 `TypeError`.
- 읽기: `kinds()`(레코드 있는 kind 정렬), `keys(kind)`(정렬, 없으면 ()), `record(kind, key)`(없으면 None),
  `field(kind, key, field)`(FieldValue|None), `value(kind, key, field)`(없으면 `KeyError`),
  `column(kind, field)` -> 그 필드가 있는 레코드의 `((key, value), ...)` key 정렬, `block_version(writer)`(없으면 None).
  `tables`·`block_versions` 는 읽기 전용 매핑(대입 -> `TypeError`). 제자리 수정 API 없음.
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
    어느 한 값이라도 다르면 다르다. block_versions 는 fp 에 들어가지 않는다.
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
- 입력 버전 `v = fp_of((name, code_hash, projection.fp))`. `projection.fp` 는 (선언 열의 값, extras) 만의 지문.
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
- `lookup(key, compute)`: `key` 는 불변 값(가변 -> `TypeError`, compute 미호출). 키 동일성 = `fp_of(key)`
  (`(0.0,)` 와 `(-0.0,)` 는 다른 키, `(1,)` 와 `(True,)` 다른 키, `(1, 2)` 와 `[1, 2]` 는 list 라서 TypeError).
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
- `fp = fp_of((columns, extras))`: 같은 열 값·extras 면 같은 fp, reads 선언 순서와 무관.
- 실패: extras 가변 -> `TypeError`; 선언 밖 열 -> `KeyError`; 열에 없는 key 의 `value` -> `KeyError`.
