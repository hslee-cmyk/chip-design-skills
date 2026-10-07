# gmid_engine 구조 규칙 test (`tests/structure/`)

새 gm/ID 엔진 패키지 `skills/analog-gmid-design/gmid_engine/`의 **구조**를 강제한다. 패키지 내용(엔진 코드)과 무관하게
소스 파일을 AST로만 읽으므로 엔진을 import하지 않고, legacy test(`legacy/tests/`)와 섞이지 않는다.

```bash
PY=C:/Python314/python.exe
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/structure            # 규칙 A~G + 픽스처 거부 test
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -m structure_test_mapping   # 규칙 H만
```

실행 끝 요약 `gmid_engine 구조 규칙 -- 검사 대상 수`에 규칙별 **검사 대상 파일 수와 위반 수**가 항상 찍힌다.
패키지가 비어 있으면 대상 0개로 PASS하지만 0이라는 숫자가 보고되고, 파일이 생기면 같은 test가 그대로 적용된다.
검사기가 공허하게 통과하지 않는다는 증거는 `test_structure_rules_reject_fixtures.py`: 규칙마다 위반 픽스처를
**기대 위반 목록과 정확히 같게** 거부하고, 허용 픽스처는 통과시킨다(기본 실행에 포함, 규칙 H 픽스처도).

## 파일

| 파일 | 역할 |
|---|---|
| `structure_checks.py` | 검사기(규칙별 `check_a`~`check_h`, `library_names`, 복사 등록부 `copy_audit`·`check_copy_manifest`·`check_copy_source`). 상수마다 출처 행 주석 |
| `conftest.py` | `fixtures/` 수집 제외, 마커 `structure_test_mapping` 등록·기본 제외, 대상 수 요약 |
| `test_structure_rules.py` | 규칙 A~G와 복사 등록부 대조(복사본·원본)를 진짜 엔진 트리에 건다 |
| `test_structure_test_mapping.py` | 규칙 H(마커 `structure_test_mapping`) |
| `test_structure_rules_reject_fixtures.py` | 규칙마다 위반 픽스처 거부 + 허용 픽스처 통과, 규칙 E 이름 집합 수집 확인, 복사 등록부 픽스처(`rule_copy`) |
| `fixtures/rule_<x>/{bad,good}/gmid_engine/` | 가짜 소스 트리. `fixtures/` 아래에 `__init__.py`가 없고 수집 제외라 import되지 않는다. `rule_copy/{bad,good}/legacy/old.py`는 엔진 밖 가짜 원본 |

검사 대상 = `gmid_engine/` 아래 `*.py` 중 `tests/`·`__pycache__`·숨김 폴더 제외.

## 출처 약칭

- D = `wt/_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(1절, 3절, 끝 '확정 사항'), UD = `wt/_drafts/user_decisions.md` 끝 2026-10-07 항목
- P = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`

## 규칙

| 규칙 | 판정 | 출처 | 예외 |
|---|---|---|---|
| A 파일당 독립 진입점 1개 | 공개(`_` 없는) 최상위 함수·클래스 중 같은 파일의 다른 최상위 문장(다른 정의·모듈 수준 대입·데코레이터·주석(annotation) 포함)이 이름으로 참조하지 않는 것 = 진입점. 진입점 '개념' 수가 정확히 1이어야 한다. 자기 재귀는 참조로 치지 않는다. 보충(오케스트레이터 결정 2026-10-07, 사용자 규칙 취지 '한 파일에 너무 많은 함수'): (1) **데이터 선언 모듈**(최상위 공개 정의가 전부 클래스, 각 클래스가 `@dataclass`·NamedTuple·Enum 계열·Exception 계열(이름이 Error/Exception/Warning로 끝나는 기반 또는 같은 파일 데이터 클래스 기반), 자체 메서드는 dunder·`@property`·`@classmethod from_*`뿐) = 스키마 한 개념으로 통과. 최상위 공개 함수가 하나라도 있으면 일반 판정 (2) 공개 정의 0 파일(상수·단위 표) 통과 (3) **비공개 모듈**(`_`로 시작하는 파일) = 공유 helper: 진입점 판정 대신 공개 함수마다 같은 하위 패키지(루트 파일은 엔진 전체)의 **다른 파일 2개 이상**이 import(`from ._h import f` 또는 `from . import _h` 뒤 `_h.f`)해야 한다 | UD 127행 (A), D 1.2 (나)4 (A)·(B)·(다) | `__init__.py`, `tests/`. 레지스트리 데코레이터(`REGISTRY_DECORATORS = ("compute_block",)`, D 1.1 (나)2·3)로 등록된 진입점은 (데코레이터, 시그니처)가 같으면 한 개념 |
| B 다른 파일의 `_` 이름 import 금지 | `from x import _y`(`_y`가 모듈 파일이 아닌 이름) 와, import로 묶인 이름에서 시작하는 속성 사슬의 `._y` 접근(`amod._y`, `gmid_engine.core.a._y`) | UD 127행 (B), D 1.2 (나)4 (B) | dunder(`__name__` 등). `from . import _helpers_x`처럼 `_` 이름이 같은 패키지의 **모듈 파일**이면 허용(공용 helper 모듈, D 3.1 161행) |
| C 하위 패키지 계층·공개 API·순환 0 | (1) 하위 패키지는 층 표 `LAYER_ORDER`(core 0 < lut 1 < authoring 2 < graph 3 < sizing 4 < metrics 5 < search 6 < layout 7 < convergence 8 < report 9 < pipeline 10)에 있어야 한다 (2) 다른 하위 패키지 import는 층 번호가 **작은** 쪽만 (3) 형식은 `from gmid_engine.<pkg> import <이름>`(상대 import 동등)만, 이름은 그 `__init__.py`의 정적 `__all__` 안. `import gmid_engine.x`, `from gmid_engine import <pkg>`, `from gmid_engine.<pkg>.<file> import`, `import *` 금지 (4) 파일 단위 import 그래프(함수 안 import 포함)에 순환 0 | D 3.1 158행, D 1.2 (나)1·3, P N3.10 517행 | 루트 모듈(`gmid_engine/__init__.py` 등)은 층 맨 위로 보고 계층 검사를 하지 않는다(공개 API 형식은 검사). 하위 패키지가 루트를 import하면 위반 |
| D 숫자 리터럴 | 허용: 0, 1, −1(실수 0.0·1.0 포함), 산술식(`BinOp`·`AugAssign`)의 양수 2, 첨자·슬라이스 안 숫자. 그 밖은 같은 줄 `# derive: <함수명>` 태그가 있고 그 함수가 엔진 어딘가의 최상위 함수일 때만 허용. 복소수 금지 | P 844행 V6, D 1.3 (나) | `core/units.py`(D 1.3 "단위 환산 계수는 `core/units.py` 한 곳"). 복사 등록부 검증을 통과한 등록 정의 안(아래 '복사 등록부') |
| E 회로 이름 금지 | 엔진 소스의 문자열 상수(f-string 조각·docstring 포함)가 library 이름 집합의 원소와 **정확히 같으면** FAIL. 이름 집합 = `assets/library/*.topology.json`(`_TEMPLATE` 제외, `linked_topology_files` 포함)의 파일 이름·`topology_name`·소자 이름·수동소자·이상원 이름·단자 넷·`terminals`·포트 키·`supply_nets`(레일) | D 1.4 (나), P WP-05·DEC-60·62 | 복사 등록부 검증을 통과한 등록 정의 안만(아래 '복사 등록부'). 이름 집합이 9회로·레일을 실제로 담는지 별도 test로 확인 |
| F 광범위 except 금지 | `except:`, `except Exception`, `except BaseException`(튜플 안, `builtins.Exception` 포함) | P N3.14(734~751행), D 1.6 | `pipeline/entry.py`에 1개까지(D 1.6 (다) "진입점 1곳 예외", D 3.1 pipeline `entry.py` = exit code) |
| G 모듈 수준 가변 캐시 금지 | 모듈 최상위(if/try/with/for/while/match 블록 안 포함, def·class 안 제외)에서 dict/list/set 리터럴·컴프리헨션, `dict()`·`list()`·`set()`·`defaultdict`·`OrderedDict`·`Counter`·`deque`·`ChainMap`·`bytearray`·Weak* 생성 호출(튜플 안에 든 것 포함)을 대입. 추가로 `@lru_cache`·`@cache` 데코레이터(전역 캐시)와 `global` 문(전역 상태 쓰기) | D '확정 사항' 5(계산 블록은 graph setter로만, 모듈 수준 dict·전역 캐시 lint FAIL), 확정 사항 1·4, D 1.1 (나)3 | `__all__`. tuple·`frozenset(...)`·`MappingProxyType(...)`·문자열·숫자 상수는 허용. 복사 등록부 검증을 통과한 등록 정의(대입·def 안 데코레이터·`global` 포함, 아래 '복사 등록부') |
| H test 파일 1:1 | `gmid_engine/<pkg>/.../<file>.py`(`__init__.py` 제외)마다 `tests/<pkg>/.../test_<file>.py`. 엔진 패키지 이름의 tests 하위 폴더에 원본 없는 `test_*.py`(고아)도 FAIL. 누락·고아 목록을 출력하고 FAIL(xfail 아님) | UD 127행 (D), D 1.2 (나)4 (D)·(다) `test_tests_mirror_sources`, D 3.1 162행 | 루트 바로 아래 파일(`_module_map.py` 등), 교차 관심사 폴더 `tests/{structure,contracts,integration,regression,oracles,perf,unit}` |

### H를 기본 실행에서 빼는 이유

core 골격 단계에서는 원본 파일이 test보다 먼저 생기므로 누락이 대부분이다. 기본 실행에 넣으면 매 변경 뒤 전체 pytest
(가벼운 절차 '남기는 것')가 늘 FAIL이어서 다른 규칙의 FAIL 신호가 묻힌다. 그래서 마커 `structure_test_mapping`으로
분리해 `-m structure_test_mapping`일 때만 돌린다(`-m`에 다른 식을 주면 그 식을 그대로 따른다). 검사기 자체가 누락·고아를
거부하는지는 H 픽스처 test가 기본 실행에서 확인한다. 골격 단계가 끝나면 마커를 떼어 기본 실행에 넣는다.

## 복사 등록부 (D·E·G 예외)

출처: `wt/_drafts/engine/design_mod7_layout.md` 8절 2 기본안 "manifest 한정 예외 + 리터럴 집합 test 고정"(같은 문서 1.1·2.1·2.2).
옛 엔진 정의를 본문 그대로 복사한 최상위 정의는 그 하위 패키지 폴더의 `_copy_manifest.py`에 등록한다. 등록부는 **이름으로** 찾는다
(`gmid_engine/<pkg>/_copy_manifest.py`, 층·패키지 무관 -- 지금은 `layout/`만 있다). 엔진 루트의 같은 이름 파일은 무시하고 위반으로 보고한다.

등록부 형식(검사기는 import하지 않고 AST + `ast.literal_eval`로 읽는다):

```python
COPY_SOURCE = "skills/analog-gmid-design/legacy/stick_diagram.py"   # 원본, 저장소 기준 상대 경로
COPIED_DEFINITIONS = (
    # (manifest 폴더 기준 .py, 최상위 정의 이름, 원본 "시작~끝" 행(def/class/대입 줄, 데코레이터 제외), sha256 hex, 리터럴 문자열 tuple)
    ("crossover.py", "_MAX_CROSSOVER_PAIRING_NODES", "5556~5556", "5246...", ("8",)),
)
```

**면제 범위**: (파일, 최상위 정의 이름) 쌍의 정의 노드(def·class·이름 하나 대입, 데코레이터 포함)와 그 하위 노드 안의 D·E·G 위반만.
같은 파일의 등록 안 된 정의는 그대로 검사한다.

**면제 조건**(하나라도 깨지면 그 정의의 면제 취소 + 위반, `copy_audit`):

| 조건 | 어기면 | test |
|---|---|---|
| `COPY_SOURCE` 상수가 상대 경로 문자열, `COPIED_DEFINITIONS`가 정적 tuple, 항목이 5칸 형식(파일은 manifest 폴더 안 `.py`, `..` 금지) | `copy_manifest_format`(표 전체 또는 그 항목 무효) | `test_rule_copy_manifest_matches_copies` |
| 같은 (파일, 이름) 한 번만 | `copy_manifest_duplicate`(그 쌍 전부 무효) | 〃 |
| 그 파일에 그 이름 최상위 정의가 정확히 1개 | `copy_missing_definition` | 〃 |
| 복사본 정의의 AST 해시 == 등록 해시 | `copy_definition_changed`('복사 정의 변경') | 〃 |
| 복사본 정의 안 규칙 D 밖 숫자 리터럴 목록 == 등록 목록 | `copy_literal_mismatch` | 〃 |
| 원본 파일이 있다 -- 엔진 루트의 조상 폴더 중 처음으로 `<조상>/<COPY_SOURCE>`가 있는 곳(진짜 트리 = 저장소 루트) | `copy_source_missing` | `test_rule_copy_manifest_matches_original` |
| 원본이 엔진 트리 밖(복사본 자신을 원본으로 삼는 가짜 등록부 차단) | `copy_source_in_engine` | 〃 |
| 원본을 다시 파싱해 등록 행 범위(`lineno`·`end_lineno` 정확히 일치)에 같은 이름 최상위 정의가 있고 그 해시 == 등록 해시 | `copy_source_mismatch` | 〃 |

- **AST 해시** = `sha256(ast.dump(node, annotate_fields=True, include_attributes=False))`(docstring·데코레이터 포함, 주석·위치 제외).
  **리터럴 목록** = 정의 안 숫자 상수 중 규칙 D 허용 판정(`_number_allowed`) 밖인 것의 `repr`(단항 `-`이면 `-` 앞붙임), 정렬, 중복 유지.
  derive 태그는 보지 않는다.
- **작성자≠검증자**: 해시·리터럴·원본 행은 검사기가 복사본과 원본에서 직접 다시 잰다. 등록부의 값은 비교 대상일 뿐 계산에 쓰지 않는다.
  복사본 해시 == 등록 해시 == 원본 해시가 모두 성립해야 '옛 정의 본문 그대로'의 증거가 된다(새 코드에 자기 해시를 단 가짜 등록은
  원본 대조에서, 원본을 엔진 안 복사본으로 적은 등록은 `copy_source_in_engine`으로 걸린다).
- 복사본을 고치려면 복사를 끊는다: 새 정의로 쓰고 등록 항목을 지운다(그러면 D·E·G가 일반 규칙으로 돌아온다).

## 위반 픽스처

| 규칙 | `bad` 트리가 담은 위반(기대 목록은 `test_structure_rules_reject_fixtures.py`) | `good` 트리가 보이는 허용 경우 |
|---|---|---|
| A | 진입점 2개(`two_roots.py`), 같은 데코레이터·다른 시그니처(`mixed_signature_variants.py`), 변형군 + 일반 공개 함수(`decorated_and_plain.py`), 예외 클래스 + 공개 함수 2개(`failures_like.py`), 일반 메서드가 있는 dataclass 2개(`schema_with_method.py`), 한 파일만 쓰는 helper·아무도 안 쓰는 helper(`_helpers_lonely.py`) | 함수가 쓰는 공개 클래스, `@compute_block` 같은 시그니처 변형 3개 + 비공개 helper, 자기 재귀, 공개 정의 0(`no_root.py`·`constants.py`), 데이터 선언 모듈(`records.py`: dataclass + `__post_init__`·property·`from_tuple`, Enum, NamedTuple, ValueError 기반 예외와 그 하위), 두 파일이 쓰는 helper(`_helpers_shared.py` ← `use_a.py`·`use_b.py`) |
| B | `from .a import _secret`, `amod._secret()`, `gmid_engine.core.a._secret` | `from . import _helpers_text`(모듈), `self._value` |
| C | 순환 `cyc_a`↔`cyc_b`, lut→report(위 방향), `from gmid_engine.lut.query import`, `__all__` 밖 이름, `import *`, `import gmid_engine.lut`, `from gmid_engine import lut`, 층 표 밖 패키지 `widgets` | 아래 방향 공개 API import(절대·상대), 패키지 안 helper, 루트 `__init__`의 재수출 |
| D | 기본값 10, 비교의 2, 3, 0.5, −2, 없는 함수의 derive 태그, 2j, `units.py` 밖 1e-6 | 0·1·−1·0.0·1.0, 산술 2·`+= 2`, `x[3]`·`x[-2]`·`x[1:5]`·`x[:, 2]`, 있는 함수의 derive 태그, `core/units.py`의 1e-6 |
| E | `"vdd"`(레일), `"two_stage_ota"`(회로), `f"gnd"`, `"M1"`(소자), `"vin_p"`(넷·포트) | `"kind"`·`"drain"`·`"nmos"` 같은 스키마 키, 이름을 값으로만 다루는 코드 |
| F | `except:`, `except Exception`, `(ValueError, BaseException)`, `builtins.Exception`, 진입점의 두 번째 광범위 except | 좁은 except, 진입점의 광범위 except 1개 |
| G | `{}`, `TABLE: list = []`, `set()`, `defaultdict(list)`, dict 컴프리헨션, 튜플 안 `{}`, if·except 블록 안 대입, `@lru_cache(maxsize=None)`, `@functools.cache`, `global` | `__all__` 리스트, tuple, `frozenset({...})`, `MappingProxyType({...})`, 함수 지역 dict |
| H | 원본 `core/y.py`·`lut/q.py`의 test 없음, 고아 `tests/core/test_z.py` | 짝 맞는 test, 루트 `_module_map.py`, `tests/integration/` |
| 복사 등록부(`rule_copy`) | 원본 `legacy/old.py`. 등록 안 된 정의(`graph/copied.py` `extra`의 7·`"B"`, 모듈 수준 `CACHE = {}`), 본문이 바뀐 등록 정의(`graph/changed.py`, 변수 이름만 바꿈 -> 해시 다름·면제 취소), 리터럴 목록 오기(`graph/miscount.py`, 실제 12·등록 ()), 없는 정의 등록(`gone`), 가짜 등록부(`lut/`: 새 코드 `invented`에 자기 해시 -> 원본 대조 실패, `../graph/copied.py` 경로), 원본이 엔진 안 자기 자신(`metrics/`), 짧은 항목·중복 항목(`search/`), 정적 tuple 아닌 표(`sizing/`), 엔진 루트 등록부. D·E·G 기대 위반은 면제가 없거나 취소된 정의 안의 것뿐 | `graph/`(규칙 D 밖 리터럴 3·4·40, 넷 이름 `"A"`·`"B"`, 모듈 수준 dict를 담은 등록 정의 2개 + 같은 파일의 미등록 정상 정의)와 `lut/`(리터럴 없는 등록 정의) -- 두 하위 패키지의 등록부. 면제가 없으면 D·E·G가 FAIL하므로 통과가 면제 동작의 증거 |

## 설계 문서에서 애매했던 점(이 test가 택한 해석)

1. **A의 레지스트리 데코레이터 이름**: 설계 문서에 이름이 나온 것은 `compute_block`뿐이다. D 1.2 (A)의 예시 'metric 레지스트리 항목들'의
   데코레이터 이름은 없다. 또 D 1.2 (C)는 `@compute_block`을 파일당 1개로 정하므로 `compute_block` 변형군 예외는 사실상 쓰이지 않는다.
   metric 레지스트리 데코레이터를 만들면 설계 문서에 이름을 적고 `REGISTRY_DECORATORS`에 더한다.
2. **A와 데이터·helper 모듈**(해결, 오케스트레이터 결정 2026-10-07): 규칙 표 A의 보충 (1)~(3)으로 정했다. 그래서
   `core/failures.py`처럼 예외 클래스와 공개 함수(`exit_code_for`·`normalized_margin`)를 한 파일에 두면 FAIL이고, 함수는 별도 파일로 옮긴다.
   보충 (3)은 공개 **함수**만 센다(비공개 모듈의 공개 클래스는 사용 수를 보지 않는다).
3. **A의 '참조'**: 같은 파일 다른 최상위 문장의 이름(`ast.Name`) 참조로 판정한다. 문자열 주석(`"Foo"`)은 참조로 치지 않는다.
4. **C의 패키지 안 층(`_module_map.py` 층 번호)**: D 3.1 둘째 규칙(패키지 안 import는 `_module_map.py` 층 오름차순)은 지도 형식이
   아직 없어 강제하지 않는다(파일 단위 순환 0만 강제). 함수 안 지연 import·`TYPE_CHECKING` import도 계층·순환에 센다.
5. **D의 `core/units.py` 예외**: D 1.3이 "단위 환산 계수는 `core/units.py` 한 곳"이라 적은 것을 그 파일의 리터럴 허용으로 읽었다.
   2는 비교(`x == 2`)·음수(`-2`)에서는 허용하지 않는다('산술식의 2'를 좁게 읽음). derive 태그의 함수는 엔진 최상위 함수만 인정.
6. **E의 일치 방식**: 대소문자를 구분하는 **문자열 전체 일치**다(넷 `A`·`B`·`X`·`Y`가 casefold로 단자 키 `b` 등과 겹치는 것을 피함).
   메시지 안 부분 문자열은 잡지 않는다. docstring도 문자열 상수로 센다.
7. **F의 진입점 예외**: 과제 지시는 예외를 적지 않았고 D 1.6 (다)는 "진입점 1곳 예외"를 둔다. `pipeline/entry.py` 1개로 좁혔다.
   D 1.6은 `except ValueError`·`InfeasibleSizingError`도 금지 목록에 두지만 이 test는 과제 지시대로 세 형태만 본다.
8. **G의 범위**: 확정 사항 5의 '전역 캐시'를 `@lru_cache`·`@cache`(maxsize와 무관) + `global` 문까지로 읽었다. 확정 사항 4의
   'LUT 조회 memo'가 어디에 사는지(모듈 수준 객체인지 Lut 인스턴스 소유인지) 설계에 없다 -- 모듈 수준 사용자 정의 객체
   (`X = BoundedLRU(...)`)는 이 test가 잡지 않는다. 클래스 본문 속성·인스턴스 속성 캐시(D 1.1 (나)3)도 보지 않는다.
9. **H의 helper 파일**: `_helpers_geom.py`의 짝은 글자 그대로 `test__helpers_geom.py`로 본다.
10. **복사 등록부의 해시와 Python 버전**: `ast.dump` 출력은 Python 버전 사이에 바뀔 수 있다(노드 필드 추가 등). 해시는 test를 돌리는
    Python(현재 3.14)으로 다시 재므로, 버전을 올려 해시가 어긋나면 복사본·원본 해시가 **서로는** 같고 등록부만 다르다
    (`copy_definition_changed`와 `copy_source_mismatch`가 같은 항목에 함께 뜬다). 그때는 등록부 해시를 새 버전으로 다시 적는다.
    `rule_copy` 픽스처 등록부의 해시도 같다.
11. **등록부 파일 자신**: 공개 정의 0(상수 표)이라 규칙 A를 통과하고, 숫자 대신 문자열을 적어 규칙 D 대상이 없다. 규칙 H는
    `tests/<pkg>/test__copy_manifest.py`를 요구한다(H는 아직 기본 실행 밖) -- 등록부 검증은 이 폴더의 test가 하므로 H 예외로 둘지는 열린 항목.
12. **리터럴 '집합'**: 설계 8절 2는 '집합'이라 적었지만 등록부(`layout/_copy_manifest.py`)는 중복을 유지한 정렬 tuple로 적었다.
    이 test도 중복 유지 목록으로 비교한다(같은 값의 리터럴이 하나 더 들어와도 잡는다).
