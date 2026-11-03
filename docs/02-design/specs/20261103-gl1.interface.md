# GL-1 interface card (card id `20261103-gl1`) -- 초안

- 기준: `design/gl1` 병합 뒤 master, 위임 A-28·A-29, 독립 검증 `wt/_drafts/evidence/2026-11-04/gl1_validation.md`.
- 병합 뒤 자리: `docs/02-design/specs/20261103-gl1.interface.md`. 순서 0 커밋에 spec card와 함께 넣는다.
- **test 작성 주체는 엔진 소스와 `structure_checks.py`를 보지 않고 이 문서만 쓴다.** 기대값은 픽스처 소스를 손으로 읽어 적는다. 피검 함수 출력을 옮기지 않는다.
- `E/` = `skills/analog-gmid-design/gmid_engine/`. `S/` = `E/tests/structure/`.
- 규칙 정의 근거: design 40 §2.4.10 ①②, §2.4.6(memo 호출), 계획 N6.37, N6.3 '같은 입력 재계산 0' (iv)(v).

## 0. test가 쓸 수 있는 기존 자리

`S/conftest.py` fixture.

| fixture | 쓰임 |
|---|---|
| `checks` | 검사기 모듈 |
| `engine_root` | 진짜 엔진 루트 `E/` |
| `fixture_tree(rule, kind)` | `S/fixtures/<rule>/<kind>/gmid_engine` 경로. 없으면 assert 실패 |
| `report(n_targets, n_violations)` | 실행 끝 요약 기록 |

`S/fixtures/` 아래는 수집·import되지 않는다. `__init__.py`를 두지 않아도 검사기는 파일을 읽는다. 패키지 재수출 픽스처에 필요한 `__init__.py`는 `fixtures/` 아래이므로 둘 수 있다.

`checks.Violation`: 속성 `kind`, `path`(엔진 루트 기준 posix 상대 경로), `line`, `detail`.

검사 대상 파일 = 루트 아래 `*.py` 중 `tests/`, `__pycache__`, 숨김 폴더 제외.

## 1. `checks.check_g8(root) -> (n_targets, violations)`

- `n_targets` = 대상 파일 수(허용 모듈 포함). 빈 트리는 `(0, [])`.
- `violations` = `Violation` 목록. (kind, path, line, detail) 오름차순.
- 허용 모듈(§1.2) 안에서는 어떤 kind도 내지 않는다.
- 기존 `checks.check_g`는 바뀌지 않는다.

**qualname**: 둘러싼 클래스·함수 이름을 `.`로 잇는다(`<locals>` 없음). 모듈 수준 = `<module>`.

### 1.1 kind 표

| kind | 거부 대상 | `detail` | `line` |
|---|---|---|---|
| `g8_attr_container` | 메서드(클래스 본문 바로 아래 `def`와 그 안 중첩 `def`) 안에서 그 메서드 첫 매개변수의 속성에 가변 값 대입: `self.a = {}`, `self.a: dict = {}`, `cls.a = []` | `클래스.a`(가장 안쪽 클래스) | 대입 문장 |
| `g8_class_container` | 클래스 본문 바로 아래 가변 값 대입: `a = {}`, `a: list = []` | `클래스.a` | 대입 문장 |
| `g8_default_factory` | `field(default_factory=dict)`·`list`·`set`, `dataclasses.field(...)`도 같음 | 클래스 본문의 필드면 `클래스.a`, 아니면 qualname | 호출 |
| `g8_cached_property` | 데코레이터 `cached_property`, `functools.cached_property` | `클래스.이름` | 데코레이터 |
| `g8_cache_call` | 호출형 `lru_cache(...)`, `functools.lru_cache(...)`, 이름 `cache(...)`, `functools.cache(...)`. `lru_cache(maxsize=1)(f)`는 **한 건**. 데코레이터 자리(`@lru_cache(...)`)는 내지 않는다(규칙 G 몫). `obj.cache(...)`처럼 `functools`가 아닌 받는 쪽은 내지 않는다 | qualname | 호출 |
| `g8_module_cache` | 모듈 수준(if·try·with·for·while·match 안 포함, def·class 안 제외) `BoundedLRU(...)`, `LutMemo(...)`, `OrderedDict(...)`, `WeakValueDictionary(...)` 대입. 호출 이름은 끝 이름으로 본다 | 대입 대상 이름 | 대입 문장 |
| `g8_id_call` | 이름 `id`를 부르는 모든 호출(쓰임 무관) | qualname | 호출 |
| `g8_memo_call_form` | `memo.call(...)`, `<식>.memo.call(...)`의 첫 인자가 다음 중 하나: 없음, `ast.Name`·`ast.Attribute`가 아님(lambda, `partial(...)` 호출 등), 또는 이름 사슬의 뿌리가 둘러싼 함수의 지역 이름(매개변수, 지역 대입, 중첩 `def`) | qualname | 호출 |
| `g8_memo_lookup_form` | `memo.lookup(...)`, `memo.lookup_persistent(...)`, `<식>.memo.lookup(...)`, `<식>.memo.lookup_persistent(...)` | qualname | 호출 |

**가변 값**(`g8_attr_container`, `g8_class_container`): dict·list·set 리터럴, dict·list·set 컴프리헨션, 그것을 원소로 가진 tuple 리터럴, 끝 이름이 `dict, list, set, bytearray, defaultdict, OrderedDict, Counter, deque, ChainMap, WeakValueDictionary, WeakKeyDictionary, WeakSet`인 호출.

**걸리지 않는 것**: 함수 지역 `d = {}`, `self.a = None`, `self.a = ()`, `self.a = tuple(x)`, `self.a = frozenset(x)`, `self.a[k] = v`, 메서드 밖 일반 객체의 `obj.a = {}`, `memo.call(module_fn, 1)`, `memo.call(pkg_mod.fn, 1)`(`pkg_mod`가 import 이름).

### 1.2 허용 모듈 `checks.G8_ALLOWED_MODULES`

tuple, 정확히 다음 14개(design 40 §2.4.10).

`core/graph_snapshot.py`, `core/compute_block.py`, `core/projection.py`, `core/graft.py`, `core/donors.py`, `core/field_value.py`, `core/graph_record.py`, `core/writer_table.py`, `lut/lut_memo.py`, `lut/table_cache.py`, `core/bounded_lru.py`, `search/archive.py`, `search/s3_index.py`, `core/run_counters.py`.

바로 다음 경계도 픽스처로 잡는다: 같은 이름이 다른 폴더에 있으면(`metrics/run_counters.py`) 허용 아님.

복사 등록부(`_copy_manifest.py`)에 등록된 정의도 면제하지 않는다. 규칙 D·E·G의 면제는 `check_g8`·`check_value_types`에 적용되지 않는다. 기존 위반은 기준선에 든다.

## 2. `checks.check_value_types(root) -> (n_targets, violations)`

**설계 값 타입 목록**: 대상 파일 전부(허용 모듈 포함)의 클래스 중 `@dataclass(frozen=True)`, `@dataclasses.dataclass(frozen=True)`(리터럴 `True`)가 붙은 것의 이름. 일반 `@dataclass`, NamedTuple, Enum은 아니다.

허용 모듈 안에서는 내지 않는다. 정렬은 §1과 같다.

| kind | 거부 대상 | `detail` | `line` |
|---|---|---|---|
| `vt_annotation` | 형식 주석이 목록 타입이거나 그것을 안에 가진 주석(`T`, `tuple[T, ...]`, `dict[K, T]`, `Optional[T]`, 문자열 주석 `"T"`, `mod.T`). 자리 = 모듈 수준 이름, frozen이 아닌 클래스 본문, 메서드 안 `self.a: T` | 모듈 수준 `이름:T`, 나머지 `클래스.a:T` | 문장 |
| `vt_assign` | 값이 `T(...)` 또는 그것을 원소로 가진 tuple·list·set·dict 리터럴(키·값), 컴프리헨션, 제너레이터, 그 하나를 인자로 받은 `tuple(...)`, `list(...)`, `set(...)`, `frozenset(...)`, `dict(...)`, `MappingProxyType(...)`. 자리는 위와 같다 | 위와 같음 | 문장 |

- 한 문장에 둘 다 해당하면 `vt_annotation` 하나만 낸다.
- 여러 타입이 걸리면 `T` = 이름 오름차순 첫째.
- **걸리지 않는 것**: 함수 지역 변수, 반환값, 함수 인자, frozen dataclass 본문, 원시 타입(숫자·문자열·bool·None)과 그 tuple, 목록에 없는 이름.

## 3. 기준선과 래칫

기준선 파일 = `S/g8_baseline.json`. **이 파일은 test 작성 주체도 코드 작성 주체도 만들지 않는다**(판정자가 병합본에서 만든다). 그래서 test가 이 파일을 기대값으로 커밋하지 않는다.

```text
checks.baseline_doc(violations, record_id, base_commit) -> dict
checks.dump_baseline(doc) -> bytes
checks.load_baseline(path) -> dict
checks.ratchet(violations, doc) -> RatchetResult(new, stale)
```

- `doc` = `{"id": str, "base_commit": str, "rows": [{"kind", "path", "detail", "count"}, ...]}`.
- 행 키 = (kind, path, detail). **줄 번호는 키가 아니다**(줄이 밀려도 같은 행). `count` = 같은 키 위반 수. `rows`는 (kind, path, detail) 오름차순.
- `baseline_doc`: `record_id` 빈 문자열, `base_commit`이 40자리 소문자 hex가 아님 → `ValueError`.
- `dump_baseline`: UTF-8, LF, 키 정렬, 끝 개행 하나. 같은 `doc`이면 바이트 동일. 입력 위반 순서가 달라도 `baseline_doc` + `dump_baseline` 결과는 같다.
- `load_baseline`: 파일 없음 → `FileNotFoundError`. 형식 오류 → `ValueError`, 메시지에 `g8_baseline_malformed`. 형식 오류 = JSON 아님, 최상위가 dict 아님, 키가 정확히 셋이 아님, `id` 빈 값, `base_commit` 형식 위반, 행 키가 정확히 넷이 아님, `count`가 bool이거나 1 미만이거나 정수 아님, 같은 키 행 중복. 조용히 비우지 않는다.
- `ratchet`은 예외를 내지 않는다.
  - `RatchetResult`는 속성 `new`, `stale`을 가진 불변 값. 둘 다 (kind, path, detail, n) tuple의 정렬된 tuple.
  - `new`: 현재 수 > 기준선 수인 키, n = 차이. 기준선에 없는 키는 n = 현재 수.
  - `stale`: 현재 수 < 기준선 수인 키, n = 차이. 현재 없는 키는 n = 기준선 수.
  - 줄 번호만 바뀌면 둘 다 빈 tuple.

### 진짜 트리 test (test 이름 `test_rule_g8_baseline_ratchet`)

`check_g8` + `check_value_types` 위반을 합쳐 `load_baseline(S/g8_baseline.json)`과 `ratchet`한다. 두 검사 모두 n_targets ≥ 1 단언. `new`가 비어 있으면 통과. `stale`은 실패가 아니고 `report`와 assert 메시지 밖 출력으로 남긴다. 파일 없음은 그대로 실패한다(`pytest.skip`, `xfail` 금지 -- fail-closed).

이 test는 판정자가 기준선을 커밋하기 전까지 red다. 코드 작성 단계의 **기대 red는 이것 하나**다.

## 4. 공유 호출 감사 도구 `tools/audit/scan_shared_calls.py` (저장소 루트 기준)

test는 **프로세스로만** 부른다(`subprocess`, `sys.executable`). 저장소 루트 = `Path(__file__).parents[5]`(`S/test_*.py` 기준). 표준 라이브러리만 쓰고 대상 엔진을 import·실행하지 않는다.

```text
python scan_shared_calls.py --engine <dir> --out <dir> [--touching <상대 경로> ...]
```

- `--engine` 폴더 이름은 `gmid_engine`이어야 한다(모듈 이름 접두). 픽스처는 `S/fixtures/shared_calls/<case>/gmid_engine`을 쓴다.
- 종료 코드 0 = 성공. **2 = 입력 오류**: 폴더 없음, 이름이 다름, `.py` 0개, 구문 오류 파일, `--touching` 경로가 대상 파일에 없음. 2일 때 `b_candidates.tsv`를 남기지 않는다.
- `--out`은 없으면 만든다. 산출물 넷, UTF-8, LF, 절대 경로 없음. 두 번 실행(다른 `PYTHONHASHSEED`, 다른 `--out`)해도 **네 파일 바이트 동일**.

| 파일 | 내용 |
|---|---|
| `calls.json` | 해석된 모듈 간 호출 자리 목록. 원소 키 `callee_mod, callee, caller_mod, caller_fn, line, text, arg_keys, leaves`. (callee_mod, callee, caller_mod, line) 정렬 |
| `shared.tsv` | 호출 모듈 ≥ 2인 callee. 머리 `callee_mod	callee	n_caller_mods	n_sites	caller_mods` |
| `b_candidates.tsv` | 머리 `callee_mod	callee	class	n_sites	pairs_b	pairs_not_b	pairs_d`. `shared.tsv`와 같은 callee(`--touching`이면 그 파일에 호출 자리가 있는 callee만) |
| `limits.json` | `{"method_calls_unresolved": n, "sites_with_param_leaf": n}` |

**해석**: `from .. import`, `import .. as`, 패키지 `__init__` 재수출을 따라 호출을 **정의 모듈**로 해석한다. `callee_mod`는 재수출 패키지가 아니라 정의 파일 모듈이다. 메서드 호출 `obj.f(x)`는 자리로 세지 않고 `method_calls_unresolved`에 센다. 같은 모듈 안 호출은 공유 판정에 넣지 않는다.

**인자 잎**(`arg_keys` = 인자마다 잎으로 치환한 문자열, `leaves` = 쓰인 잎 목록):

| 잎 | 조건 |
|---|---|
| 필드 `F[종류.필드]` | `<식>.column("종류", "필드")`, `<식>.value("종류", <키>, "필드")`. 두 문자열이 리터럴일 때 |
| 지역 추적 | 지역 이름은 같은 함수의 대입·`for`·컴프리헨션 식으로 치환. 값 식은 잎을 찾을 때까지 따라간다 |
| 매개변수 `P[이름]` | 둘러싼 함수 매개변수. 같은 모듈 호출자가 위치 인자를 넘기면 그 식으로 치환하고, 호출자가 없으면 잎 |
| 리터럴 | 값 자체 |
| 전역 `G[이름]` | 모듈 수준 이름 |

**쌍 분류**(호출 모듈이 다른 두 자리):

| 쌍 | 조건 |
|---|---|
| B | `arg_keys`가 같고 두 자리에 필드 잎 ≥ 1 |
| not_B | `arg_keys`가 다르고 두 자리 모두 필드 잎 ≥ 1, 매개변수 잎 0 |
| D | 그 밖(매개변수 잎만, 필드를 찾지 못함 등) -- **판정 불가**, 손 분류 입력 |

**callee `class`**: B 쌍 ≥ 1이면 `B`, 아니면 D 쌍 ≥ 1이면 `D`, 아니면 `not_B`.

### 표본 toy(손 분류 필수 케이스)

| case | 구성 | 기대 class |
|---|---|---|
| `same_input` | 두 모듈이 `f(p.column("device", "dc_op"))` | B |
| `diff_input` | 한쪽 `"dc_op"`, 다른 쪽 `"ss_dev"` | not_B |
| `local_trace` | 한쪽은 `v = p.column(...)` 뒤 `f(v)`, 다른 쪽은 바로 넘김, 같은 필드 | B |
| `helper_trace` | 한쪽은 같은 모듈 `_row(p.column(...))` 안에서 매개변수로 `f(x)`, 다른 쪽은 바로 넘김, 같은 필드 | B |
| `reexport` | 호출이 패키지 재수출 경유, 다른 모듈은 정의 모듈 직접 import, 같은 필드 | B, `callee_mod` = 정의 모듈 |
| `param_only` | 두 모듈 모두 `def g(x): f(x)`, 호출자 없음 | D, `sites_with_param_leaf` 증가 |
| `one_caller` | 한 모듈에서만 두 번 호출 | `shared.tsv`·`b_candidates.tsv`에 없음 |
| `method` | `obj.f(p.column(...))` | 자리 아님, `method_calls_unresolved` = 호출 수 |
| `touching` | B callee 하나, 다른 callee 하나. `--touching`으로 한 파일 지정 | 그 파일 callee만 `b_candidates.tsv`에 |

## 5. 픽스처와 test 파일 자리

| 자리 | 내용 |
|---|---|
| `S/fixtures/rule_g8/{bad,good}/gmid_engine/` | §1 kind마다 위반, 바로 옆 경계, 허용 모듈. `bad`: 유효한 등록부에 등록된 정의 안의 `default_factory` 한 건 -- 위반으로 나옴(픽스처 꼴 = 기존 `rule_copy`) |
| `S/fixtures/rule_vt/{bad,good}/gmid_engine/` | §2 kind, 자리, 제외 |
| `S/fixtures/shared_calls/<case>/gmid_engine/` | §4 표 |
| `S/test_g8_lint.py` | §1 기대 목록 정확 비교, 빈 트리, 결정성(두 번 호출 같음) |
| `S/test_value_types_lint.py` | §2 기대 목록 정확 비교 |
| `S/test_g8_baseline.py` | §3 전부. 기준선 밖 위반 추가 → `new`, 진짜 트리 test 포함 |
| `S/test_scan_shared_calls_tool.py` | §4 표 전부, 종료 코드 2 입력, 바이트 동일 |

기대 비교는 (kind, path, line, detail) 정렬 목록 **정확히 같음**이다(기존 `test_structure_rules_reject_fixtures.py` 꼴). 이 card는 기존 test를 고치지 않는다.

`S/README.md` '파일'·'규칙'·'위반 픽스처' 표에 test 쪽 행을 더한다. 검사기 행은 코드 쪽이 더한다.
