# gmid_engine 구조 규칙 test (`tests/structure/`)

새 gm/ID 엔진 패키지 `skills/analog-gmid-design/gmid_engine/`의 **구조**를 강제한다. 패키지 내용(엔진 코드)과 무관하게
소스 파일을 AST로만 읽으므로 엔진을 import하지 않고, legacy test(`legacy/tests/`)와 섞이지 않는다.

```bash
PY=C:/Python314/python.exe
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/structure            # 규칙 A~G·I·K + 픽스처 거부 test
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/structure -m structure_test_mapping   # 규칙 H만
```

실행 끝 요약 `gmid_engine 구조 규칙 -- 검사 대상 수`에 규칙별 **검사 대상 파일 수와 위반 수**가 항상 찍힌다.
패키지가 비어 있으면 대상 0개로 PASS하지만 0이라는 숫자가 보고되고, 파일이 생기면 같은 test가 그대로 적용된다.
검사기가 공허하게 통과하지 않는다는 증거는 `test_structure_rules_reject_fixtures.py`: 규칙마다 위반 픽스처를
**기대 위반 목록과 정확히 같게** 거부하고, 허용 픽스처는 통과시킨다(기본 실행에 포함, 규칙 H 픽스처도).

## 파일

| 파일 | 역할 |
|---|---|
| `structure_checks.py` | 검사기(규칙별 `check_a`~`check_i`·`check_k`·`check_m`, `library_names`, 복사 등록부 `copy_audit`·`check_copy_manifest`·`check_copy_source`). 상수마다 출처 행 주석 |
| `conftest.py` | `fixtures/` 수집 제외, 마커 `structure_test_mapping` 등록·기본 제외, 대상 수 요약 |
| `test_structure_rules.py` | 규칙 A~G·I·K·M(I 예외 목록이 실제로 쓰이는지, library 태그 하위 키 분류 포함)와 복사 등록부 대조(복사본·원본)를 진짜 엔진 트리에 건다 |
| `test_structure_test_mapping.py` | 규칙 H(마커 `structure_test_mapping`) |
| `test_structure_rules_reject_fixtures.py` | 규칙마다 위반 픽스처 거부 + 허용 픽스처 통과, 규칙 E 이름 집합 수집 확인, 복사 등록부 픽스처(`rule_copy`) |
| `test_g8_lint.py` | GL-1 `check_g8`: kind 8종마다 위반과 바로 옆 경계, 허용 모듈 14개(같은 이름 다른 폴더 포함), 같은 키 여러 건, 첫 줄·끝 줄, 빈 트리, 결정성 (`fixtures/rule_g8`) |
| `test_value_types_lint.py` | GL-1 `check_value_types`: `vt_annotation`·`vt_assign`, 자리(모듈 수준·클래스 본문·메서드 `self.a`)와 제외 (`fixtures/rule_vt`) |
| `test_g8_baseline.py` | GL-1 `baseline_doc`·`dump_baseline`·`load_baseline`(형식 오류 전 항목)·`ratchet`(new·stale·줄 이동), 진짜 트리 `test_rule_g8_baseline_ratchet`(`g8_baseline.json` 없으면 실패) |
| `test_scan_shared_calls_tool.py` | GL-1 `tools/audit/scan_shared_calls.py`를 프로세스로: 표본 toy 9종(`fixtures/shared_calls/<case>`), 종료 코드 2 입력, 다른 `PYTHONHASHSEED`·`--out` 바이트 동일 |
| `fixtures/rule_<x>/{bad,good}/gmid_engine/` | 가짜 소스 트리. `fixtures/` 아래에 `__init__.py`가 없고 수집 제외라 import되지 않는다. `rule_copy/{bad,good}/legacy/old.py`는 엔진 밖 가짜 원본 |

검사 대상 = `gmid_engine/` 아래 `*.py` 중 `tests/`·`__pycache__`·숨김 폴더 제외.

## 출처 약칭

- D = `wt/_drafts/engine/NEW_ENGINE_DESIGN_REQUIREMENTS.md`(1절, 3절, 끝 '확정 사항'), UD = `wt/_drafts/user_decisions.md` 끝 2026-10-07 항목
- P = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`

## 규칙

| 규칙 | 판정 | 출처 | 예외 |
|---|---|---|---|
| A 파일당 독립 진입점 1개 | 공개(`_` 없는) 최상위 함수·클래스 중 같은 파일의 다른 최상위 문장(다른 정의·모듈 수준 대입·데코레이터·주석(annotation) 포함)이 이름으로 참조하지 않는 것 = 진입점. 진입점 '개념' 수가 정확히 1이어야 한다. 자기 재귀는 참조로 치지 않는다. 보충(오케스트레이터 결정 2026-10-07, 사용자 규칙 취지 '한 파일에 너무 많은 함수'): (1) **데이터 선언 모듈**(최상위 공개 정의가 전부 클래스, 각 클래스가 `@dataclass`·NamedTuple·Enum 계열·Exception 계열(이름이 Error/Exception/Warning로 끝나는 기반 또는 같은 파일 데이터 클래스 기반), 자체 메서드는 dunder·`@property`·`@classmethod from_*`뿐) = 스키마 한 개념으로 통과. 최상위 공개 함수가 하나라도 있으면 일반 판정 (2) 공개 정의 0 파일(상수·단위 표) 통과 (3) **비공개 모듈**(`_`로 시작하는 파일) = 공유 helper: 진입점 판정 대신 공개 함수마다 같은 하위 패키지(루트 파일은 엔진 전체)의 **다른 파일 2개 이상**이 import(`from ._h import f` 또는 `from . import _h` 뒤 `_h.f`)해야 한다. 공개 함수 = 공개 최상위 def + 같은 파일 최상위 함수 이름을 값으로 갖는 공개 대입(별칭 `f = _f`, 오케스트레이터 결정 2026-10-07) | UD 127행 (A), D 1.2 (나)4 (A)·(B)·(다) | `__init__.py`, `tests/`. 레지스트리 데코레이터(`REGISTRY_DECORATORS = ("compute_block",)`, D 1.1 (나)2·3)로 등록된 진입점은 (데코레이터, 시그니처)가 같으면 한 개념 |
| B 다른 파일의 `_` 이름 import 금지 | `from x import _y`(`_y`가 모듈 파일이 아닌 이름) 와, import로 묶인 이름에서 시작하는 속성 사슬의 `._y` 접근(`amod._y`, `gmid_engine.core.a._y`) | UD 127행 (B), D 1.2 (나)4 (B) | dunder(`__name__` 등). `from . import _helpers_x`처럼 `_` 이름이 같은 패키지의 **모듈 파일**이면 허용(공용 helper 모듈, D 3.1 161행) |
| C 하위 패키지 계층·공개 API·순환 0 | (1) 하위 패키지는 층 표 `LAYER_ORDER`(core 0 < lut 1 < authoring 2 < graph 3 < sizing 4 < metrics 5 < search 6 < layout 7 < convergence 8 < report 9 < pipeline 10)에 있어야 한다 (2) 다른 하위 패키지 import는 층 번호가 **작은** 쪽만 (3) 형식은 `from gmid_engine.<pkg> import <이름>`(상대 import 동등)만, 이름은 그 `__init__.py`의 정적 `__all__` 안. `import gmid_engine.x`, `from gmid_engine import <pkg>`, `from gmid_engine.<pkg>.<file> import`, `import *` 금지 (4) 파일 단위 import 그래프(함수 안 import 포함)에 순환 0 | D 3.1 158행, D 1.2 (나)1·3, P N3.10 517행 | 루트 모듈(`gmid_engine/__init__.py` 등)은 층 맨 위로 보고 계층 검사를 하지 않는다(공개 API 형식은 검사). 하위 패키지가 루트를 import하면 위반 |
| D 숫자 리터럴 | 허용: 0, 1, −1(실수 0.0·1.0 포함), 산술식(`BinOp`·`AugAssign`)의 양수 2, 첨자·슬라이스 안 숫자. 그 밖은 같은 줄 `# derive: <함수명>` 태그가 있고 그 함수가 엔진 어딘가의 최상위 함수일 때만 허용. 복소수 금지 | P 844행 V6, D 1.3 (나) | `core/units.py`(D 1.3 "단위 환산 계수는 `core/units.py` 한 곳"). 복사 등록부 검증을 통과한 등록 정의 안(아래 '복사 등록부') |
| E 회로 이름 금지 | 엔진 소스의 문자열 상수(f-string 조각·docstring 포함)가 library 이름 집합의 원소와 **정확히 같으면** FAIL. 이름 집합 = `assets/library/*.topology.json`(`_TEMPLATE` 제외, `linked_topology_files` 포함)의 파일 이름·`topology_name`·소자 이름·수동소자·이상원 이름·단자 넷·`terminals`·포트 키·`supply_nets`(레일), **단 엔진이 선언한 어휘는 뺀다(O-198, 2026-10-31)**: LUT 축 선언 `lut/lut_types.AXES`, spec 키 상수 `authoring/_spec_fields.CIRCUIT_SPECIFIC_KEYS`, `_module_map.MODULES` 의 `plan_ids` 칸 -- `structure_checks.engine_vocabulary()` 가 그 선언 자리에서 읽는다(하드코딩 목록 없음). 그 밖 이름(진짜 회로 이름)은 계속 FAIL | D 1.4 (나), P WP-05·DEC-60·62 | 복사 등록부 검증을 통과한 등록 정의 안만(아래 '복사 등록부'). 이름 집합이 9회로·레일을 실제로 담는지 별도 test로 확인 |
| F 광범위 except 금지 | `except:`, `except Exception`, `except BaseException`(튜플 안, `builtins.Exception` 포함) | P N3.14(734~751행), D 1.6 | `pipeline/entry.py`에 1개까지(D 1.6 (다) "진입점 1곳 예외", D 3.1 pipeline `entry.py` = exit code) |
| G 모듈 수준 가변 캐시 금지 | 모듈 최상위(if/try/with/for/while/match 블록 안 포함, def·class 안 제외)에서 dict/list/set 리터럴·컴프리헨션, `dict()`·`list()`·`set()`·`defaultdict`·`OrderedDict`·`Counter`·`deque`·`ChainMap`·`bytearray`·Weak* 생성 호출(튜플 안에 든 것 포함)을 대입. 추가로 `@lru_cache`·`@cache` 데코레이터(전역 캐시)와 `global` 문(전역 상태 쓰기) | D '확정 사항' 5(계산 블록은 graph setter로만, 모듈 수준 dict·전역 캐시 lint FAIL), 확정 사항 1·4, D 1.1 (나)3 | `__all__`. tuple·`frozenset(...)`·`MappingProxyType(...)`·문자열·숫자 상수는 허용. 복사 등록부 검증을 통과한 등록 정의(대입·def 안 데코레이터·`global` 포함, 아래 '복사 등록부') |
| H test 파일 1:1 | `gmid_engine/<pkg>/.../<file>.py`(`__init__.py` 제외)마다 `tests/<pkg>/.../test_<file>.py`. 엔진 패키지 이름의 tests 하위 폴더에 원본 없는 `test_*.py`(고아)도 FAIL. 누락·고아 목록을 출력하고 FAIL(xfail 아님) | UD 127행 (D), D 1.2 (나)4 (D)·(다) `test_tests_mirror_sources`, D 3.1 162행 | 루트 바로 아래 파일(`_module_map.py` 등), 교차 관심사 폴더 `tests/{structure,contracts,integration,regression,oracles,perf,unit}`. 공개 동작이 없는 `_` 모듈 -- 최상위 함수·클래스가 하나도 없는 것(상수 표·등록부 `_copy_manifest.py`) 또는 데이터 선언 모듈(오케스트레이터 결정 2026-10-07). 함수가 있는 `_` 모듈(`_helpers_*.py`)은 대상 |
| I 회로별 정보로 행동 결정 금지 | 사용자 대원칙(2026-10-07) "topology 에 종속된 엔진은 만들지 않는다. 임의의 topology 에 적용할 수 있어야 한다." (a) `tag_key_lookup`: 회로 식별·태그 키(`FORBIDDEN_LOOKUP_KEYS` -- `topology_name`, 태그 섹션 `device_roles`·`symmetry`·`sizing_roles`·`compensation`, 역할 키 `vertical_stack_id`·`fold_group`·`headroom_role`·`shared_gm_id_groups`·`budget_reference_device`·`gm_id_role`·`L_role`, library 태그 하위 역할 키 `gm_id_match_vgs_of`·`vds_match_vgs_of`·`same_as_device`·`matching_pairs`·`stage_devices`·`vds_kvl_groups`)를 문자열 리터럴로 조회: `x["k"]`(읽기·쓰기), `x.get/pop/setdefault/__getitem__/__contains__("k")`, `"k" in x`, `getattr/hasattr(x, "k")`, `match` 의 `{"k": ...}`, 속성 `x.k`. (b) `name_branch`: 식별 표현(속성 `name`·`topology_name`·`connectivity_fp`·`file_sha256`·`d`·`g`·`s`·`bulk`·`terminals`·`net`·`nets`·`element`, 키 `name`·`topology_name`·`drain`·`gate`·`source`·`bulk`·`terminals`)을 비어 있지 않은 문자열 리터럴과 비교(`==`·`!=`·`in`·`not in`, 리터럴 tuple/list/set 포함), `.startswith/endswith/find/rfind/index/rindex/count/__contains__/__eq__("lit")`, `re.match/search/fullmatch("pat", 식별)`, `match 식별: case "lit"`, 리터럴 키 표 `{"lit": ...}[식별]`·`.get(식별)`. 리터럴이 규칙 E 이름 집합의 원소이면 E 몫이라 (b)에서 뺀다(`check_i(root, names)`, 이름 집합 없이 부르면 전부 본다) | 대원칙 + 키 출처: authoring `CONTRACT.md` 머리 10행(태그 키 4개 = `IGNORED_TAG_KEYS`), P U-50(1197행), P IC4(852행), library 태그 섹션 하위 키, 과제 지시(`topology_name`·`matching_pairs`) | `TAG_LOOKUP_EXEMPT`(파일 단위, 허용 키 + 사유): `authoring/topology_schema.py`(`topology_name` -- 스키마 화이트리스트 검사, CONTRACT 3.2), `authoring/topology_load.py`(`topology_name` -- `TopologyDoc.name` 출처 기록, 지문 투영 밖, CONTRACT 2절), `report/`(폴더, `topology_name` -- 보고 출력용). 키 목록을 담는 선언(`IGNORED_TAG_KEYS = (...)`)·dict 리터럴의 키는 조회가 아니라 대상 아님 |
| J 없음 | (규칙 글자 J는 쓰지 않는다) | 설계 40 v1.10 §2.4.3 '검사' 행: J 공동분석·`tests/integration/test_j_rules_library.py`·41 §5 'J3' 등과 이름이 겹쳐 건너뛰고 다음 규칙을 K로 쓴다 | -- |
| K front 조회 읽기 경로를 엔진 안에서 부르지 않음 | 엔진 소스(`tests/` 제외) 중 허용 파일 밖 전부를 AST로 훑어 거부: (K-a) `front_query_name` -- 이름 `node_across_front`·`read_front_entries`의 참조(import 이름·별칭, `ast.Name`, `ast.Attribute.attr`) (K-b) `front_query_module` -- 모듈 `front_query`·`front_entries`의 import(상대·절대, `from . import front_query` 같은 모듈 객체 import 포함) (K-c) `snapshot_read` -- `attr`이 `read_snapshot`·`_read_snapshot_file`인 모든 `ast.Attribute`(호출이 아닌 참조 `f = sctx.archive.read_snapshot` 포함)와 이름 `_read_snapshot_file`(import 이름 포함). 같은 줄의 다른 형식은 각각 센다 | 설계 40 v1.10 §2.4.3 'front 조회 전용 읽기 경로' 표 '검사'·'부를 수 있는 곳'·'결과의 쓰임' 행(U-90, 사용자 결정 2026-10-15 "나로 해" 실행 사이 재사용 제거 -- 다른 실행의 출력이 계산으로 새지 않게) | 허용 파일 `FRONT_QUERY_ALLOWED_FILES` = `search/front_query.py`(정의, 스냅샷 파일 읽기 `_read_snapshot_file`), `search/front_entries.py`(정의), `search/__init__.py`(재수출). 층 순서상 `search` 아래 패키지는 이미 규칙 C가 막는다 -- K는 `search` 안 다른 모듈과 `layout`·`convergence`·`report`·`pipeline`을 잡는다. test 이름은 `test_rule_k_` 접두(`-k rule_k_`가 `tests/authoring/test_topology_load.py`의 `test_cases_cover_all_32_rule_kinds`를 고르지 않게) |
| M 실행 비공유(색인·계수는 실행 하나에만) | **대상이 다르다**: 엔진 트리 전체(`tests/` 포함, 이 폴더의 `fixtures/` 제외 -- `m_files`). (M-a) `open_run_ref` -- `tests/` 밖 엔진 소스에서 `open_run` 참조(import 이름·별칭·모듈, 이름, 속성)는 허용 파일 `OPEN_RUN_ALLOWED_FILES` 밖이면 거부. (M-b) `direct_construct` -- `S3Index(...)`·`RunCounters(...)` 생성 호출(import 별칭·속성 꼴 포함)은 정의 모듈과 `search/open_run.py` 밖이면 거부(test 포함). (M-c) `run_stage_a` 호출마다: `run_pair_packed`(`*args`·`**kw`), `run_pair_source`(`donors`·`counters` 인자가 같은 함수 본문의 `a, b = open_run()` 튜플 풀기 (첫째, 둘째) 이름이 아님 -- 매개변수·속성·결과 칸·첨자·다른 호출 반환·자유 변수(안쪽 `def`·`lambda`)·`open_run()` 튜플 풀기가 아닌 방식으로도 묶인 이름·순서 바뀜·두 이름이 다른 `open_run()`·함수 밖 호출), `run_pair_reused`(`open_run()` 대입 하나가 그 함수 안 `run_stage_a` 둘 이상의 인자 -- 같은 이름 재대입은 대입마다 따로, 아래 해석 1), 호출 인식은 별칭·이름 대입·`getattr` 간접 호출 포함(fail-closed, 아래 해석 1), `run_pair_loop`(호출이 반복문·내포식·generator 식 안인데 그 `open_run()` 이 같은 가장 안쪽 반복문 본문에 없음). 키워드가 하나도 없는 호출은 쌍이 없어 M-c 대상이 아니다(키워드 빠짐 `TypeError` test). (M-d) `run_pair_stored` -- '쥔 값'(아래)을 모듈 수준 이름, 클래스 속성, session·module·package·class 범위 fixture 의 반환·yield, 함수 기본 인자값, `lru_cache`·`cache`(데코레이터·호출형) 함수의 반환, 모듈 수준 컨테이너 변경(`append`·`extend`·`add`·`update`·`setdefault`·`insert`·항목 대입)·`global` 이름, `config`·`pytestconfig` 사슬(`request.config`·`config.cache`·`config.stash`), conftest `pytest_configure`·`pytest_sessionstart` 안 생성, 모듈 수준 객체의 속성·모듈 수준에서 만든 클래스 인스턴스의 `self` 속성에 두면 거부. (M-f) `run_pair_persisted` -- 두 객체·그것을 쥔 값·내부 칸(`_` 속성 포함)·결과 칸 `.donors`·`.counters` 를 `pickle`·`json`·`marshal` 의 `dump`·`dumps`(별칭·`Pickler(...).dump` 포함) 인자나 `shelve.open` 항목 대입 값으로 넘기면 거부. **쥔 값** = `open_run()` 결과와 그 이름, 결과가 두 객체를 쥐는 진입(`PAIR_HOLDER_PRODUCERS` = `run_stage_a`·`run_stage_b`·`build_kernel_context`·`build_search_context`)의 결과, 같은 파일에서 쥔 값을 돌려주는 함수(helper 한 겹)의 결과, 속성 `donors`·`counters`, 컨텍스트 칸 속성(`CONTEXT_ATTRS` = `dc`(C6 `sctx.dc`)·`sctx`·`kctx`·`ctx`·`stage_a`), 쥔 값의 첨자, 그 값을 담은 tuple·list·dict·set·`CONTAINER_BUILDERS` 호출, 그 이름을 닫아 쥔 `lambda`. 그 밖 호출의 결과(예 `build_s1` 스냅샷, `counters.snapshot()` 값)와 쥔 값의 그 밖 속성(`res.s1`·`res.spec`·`ctx.base` 같은 스냅샷·선언 칸)은 쥔 값이 아니다 | XRUN-F1 card B interface card C9(설계 40 §2.4.5 '수명' (2), 사용자 결정 X-20 2026-10-16 "권고대로 구조로 막는 방향으로 진행해", X-21) | 허용 자리 `OPEN_RUN_ALLOWED_FILES`(`search/open_run.py`·`search/__init__.py`), `RUN_OBJECT_HOMES`. 함수 지역 이름·function 범위 fixture 의 `open_run()` 반환은 허용(C9). 범위는 `run_stage_a` 인자뿐 -- 감쌈 함수·블록을 직접 부르는 단위 test 는 한 test 함수 안 `open_run()` 하나를 여러 호출에 써도 된다(C9). test 이름은 `test_rule_m_` 접두 |

### 규칙 M 의 해석(이 test 가 택한 것 -- C9 문구가 정하지 않은 자리)

1. **M-c '`open_run()` 대입 문장 하나는 그 함수 안 `run_stage_a` 호출 하나의 인자에만 닿는다'**(design 40 v1.11.1 §2.4.5 (2) M-c 원문, 사용자 결정 O-17 (1)): 판정 단위는 **`open_run()` 튜플 풀기 대입
   문장 하나**다 -- 대입 하나가 `run_stage_a` 호출 둘 이상의 인자가 되면 `run_pair_reused`. 같은 이름을 새 `open_run()` 튜플 풀기로 **다시 대입**해
   다음 호출에 쓰는 꼴은 대입마다 호출 하나라 허용한다(design 원문의 판정 단위가 대입 문장이다 -- O-17 (1)). 호출이 쓰는
   대입 = 그 호출을 구조적으로 앞서는(같은 문장 목록 또는 바깥 문장 목록에서 앞선) 같은 이름 대입 중 마지막 것. 그 이름이 `open_run()` 튜플 풀기
   말고 다른 방식(매개변수·`for`·다른 대입)으로도 묶이거나, 호출을 구조적으로 앞서는 같은 이름 대입이 없으면
   위반이다. `if`/`else`·`with`·`try`·`match` 가지·반복문 본문 안 대입은 그 밖의 호출을 앞서는 것으로 치지 않는다 -- **design 원문보다 엄격한
   안전 쪽 해석**(사용자 결정 O-17 (2), 2026-10-19 "card B 1~3 권고대로"; 예 `if` 양쪽 가지의 `open_run()` 대입 둘이 같은 호출에 닿는 꼴도
   거부, fail-closed). 같은 함수의 다른 쓰임(`assert res.donors is donors`, 같은 실행을 잇는 `build_kernel_context(..., donors=donors, ...)`)은
   막지 않는다 -- M-c 범위는 `run_stage_a` 인자뿐이고(design '범위 한정'), B-T16('StageAResult 두 칸이 넘긴 객체 is')이 그 이름을 다시 써야 한다.
   **`run_stage_a` 호출 인식(fail-closed)**: 이름 `run_stage_a` 호출, `<식>.run_stage_a(...)`, `from ... import run_stage_a as X` 의 `X(...)`, 어느
   scope 에서든 `X = run_stage_a`·`X = <식>.run_stage_a`·`X = <별칭>`(고정점)으로 대입된 이름 `X` 의 호출, `getattr(<식>, "run_stage_a")(...)` --
   모두 `run_stage_a` 호출로 보고 같은 판정을 건다(`_entry_aliases`·`_is_entry_call`). 같은 이름이 다른 값도 받는 경우까지 호출로 본다.
   **범위 밖**: 문자열 안 코드(하위 프로세스에 넘기는 `python -c` 코드 문자열 등)의 `run_stage_a` 는 AST 상 문자열 상수라 이 검사가 보지 않는다
   -- 그 실행의 1:1 은 그 test 자신(하위 프로세스 결과 단언)과 auditor 리뷰가 맡는다.
2. **M-d '수명이 test 하나보다 긴 객체의 인스턴스 속성'**(design 40 §2.4.5 (2) M-d 원문 그대로 -- 대상은 좁히지 않는다): 이 정적 검사는 속성
   이름 휴리스틱이라 우회 꼴(사용자 클래스로 감싸기, 목록 `PAIR_ATTRS`·`CONTEXT_ATTRS` 밖 속성 이름, session fixture 가 만든 객체의 인스턴스
   속성)을 다 잡지 못한다 -- 남은 꼴은 auditor 리뷰 항목과 런타임 증거(B-T17 두 실행 격리, 같은 입력 재계산 계수 B-T21·B-T22)가 맡는다
   (사용자 X-22 2026-10-16). 검사기가 실제로 잡는 꼴: 모듈 수준 이름이 가리키는 객체의 속성 대입, 모듈 수준에서 만든 클래스 인스턴스의 `self` 속성,
   session fixture 의 `KernelContext` 처럼 두 객체를 칸으로 쥔 값의 fixture 반환('쥔 값' 정의 -- 결과 칸 producer).
3. **session fixture 가 지역 쌍으로 만든 S1 스냅샷**: 쌍을 반환·보관하지 않으므로 허용(good 픽스처). 스냅샷은 두 객체를 담지 않는다.
4. **한계**: (M-c `run_pair_reused`) 대입 하나를 쓰는 호출을 줄 번호 집합으로 세므로, 같은 줄의 `run_stage_a` 두 호출이 한 대입을 쓰면 한 곳으로 합쳐져 거부되지 않는다(`_m_calls` 줄 번호 중복 제거). 다른 파일의 helper 를 거친 보관, 상수가 아닌 이름의 `getattr`·`exec`·문자열 코드 같은 동적 경로는 보지 못한다(spec card 1.7.1
   '리뷰 항목'). M-c 호출 인식의 `getattr(<식>, "run_stage_a")` 은 이름이 문자열 상수일 때만 잡는다.

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
| A | 진입점 2개(`two_roots.py`), 같은 데코레이터·다른 시그니처(`mixed_signature_variants.py`), 변형군 + 일반 공개 함수(`decorated_and_plain.py`), 예외 클래스 + 공개 함수 2개(`failures_like.py`), 일반 메서드가 있는 dataclass 2개(`schema_with_method.py`), 한 파일만 쓰는 helper·아무도 안 쓰는 helper(`_helpers_lonely.py`), 한 파일만 쓰는 별칭 `impl = _impl`·아무도 안 쓰는 별칭 `spare = _impl`(`_helpers_alias.py`) | 함수가 쓰는 공개 클래스, `@compute_block` 같은 시그니처 변형 3개 + 비공개 helper, 자기 재귀, 공개 정의 0(`no_root.py`·`constants.py`), 데이터 선언 모듈(`records.py`: dataclass + `__post_init__`·property·`from_tuple`, Enum, NamedTuple, ValueError 기반 예외와 그 하위), 두 파일이 쓰는 helper·별칭(`_helpers_shared.py`의 `shared`·`inner = _inner` ← `use_a.py`·`use_b.py`) |
| B | `from .a import _secret`, `amod._secret()`, `gmid_engine.core.a._secret` | `from . import _helpers_text`(모듈), `self._value` |
| C | 순환 `cyc_a`↔`cyc_b`, lut→report(위 방향), `from gmid_engine.lut.query import`, `__all__` 밖 이름, `import *`, `import gmid_engine.lut`, `from gmid_engine import lut`, 층 표 밖 패키지 `widgets` | 아래 방향 공개 API import(절대·상대), 패키지 안 helper, 루트 `__init__`의 재수출 |
| D | 기본값 10, 비교의 2, 3, 0.5, −2, 없는 함수의 derive 태그, 2j, `units.py` 밖 1e-6 | 0·1·−1·0.0·1.0, 산술 2·`+= 2`, `x[3]`·`x[-2]`·`x[1:5]`·`x[:, 2]`, 있는 함수의 derive 태그, `core/units.py`의 1e-6 |
| E | `"vdd"`(레일), `"two_stage_ota"`(회로), `f"gnd"`, `"M1"`(소자), `"vin_p"`(넷·포트) | `"kind"`·`"drain"`·`"nmos"` 같은 스키마 키, 이름을 값으로만 다루는 코드 |
| F | `except:`, `except Exception`, `(ValueError, BaseException)`, `builtins.Exception`, 진입점의 두 번째 광범위 except | 좁은 except, 진입점의 광범위 except 1개 |
| G | `{}`, `TABLE: list = []`, `set()`, `defaultdict(list)`, dict 컴프리헨션, 튜플 안 `{}`, if·except 블록 안 대입, `@lru_cache(maxsize=None)`, `@functools.cache`, `global` | `__all__` 리스트, tuple, `frozenset({...})`, `MappingProxyType({...})`, 함수 지역 dict |
| H | 원본 `core/y.py`·`lut/q.py`·`core/_helpers_h.py`(함수 있는 `_` 모듈)의 test 없음, 고아 `tests/core/test_z.py` | 짝 맞는 test, 루트 `_module_map.py`, `tests/integration/`, test 없는 `core/_table.py`(상수만)·`core/_records.py`(데이터 선언) |
| I | (a) `sizing/roles.py`: `doc["device_roles"]`, `.get("fold_group")`, `"headroom_role" in`, `getattr(dev, "L_role")`, `case {"gm_id_role": ...}`, `dev.vertical_stack_id`; `search/branch.py` `doc.topology_name`; 예외 파일이라도 허용 키 밖(`authoring/topology_schema.py` 의 `device_roles`, `report/summary.py` 의 `fold_group`). (b) `search/branch.py`: `doc.name == "folded_mirror_amp"`, `dev.s in ("rail_core", "rail_io")`, `.startswith("telescopic")`, `match port.net: case "outp" \| "outn"`, `{"cascode_amp": 5}.get(...)`; `search/lib_name.py` `doc.name == "two_stage_ota"`(이름 집합을 주면 E 몫으로 빠짐 -- 별도 test) | 스키마 화이트리스트 선언과 `topology_name` 검사(`authoring/topology_schema.py`), 보고용 `topology_name` 읽기·쓰기(`report/summary.py`), `dev.kind == "nmos"`·`port.direction == "input"`(스키마 어휘), 이름끼리 비교·이름 집합 멤버십(리터럴 없음), `name.startswith(COMMENT_PREFIX)`(상수 이름), 빈 문자열 비교 |
| K | (K-a) `pipeline/run.py` `from gmid_engine.search import node_across_front`와 호출, `search/start_points.py` `read_front_entries(run_dir)`, `layout/view.py` `search.read_front_entries(d)`(속성), `report/table.py` `import node_across_front as across`(별칭); (K-b) `search/start_points.py` `from .front_entries import read_front_entries`, `search/kernel.py` `from . import front_query`(모듈 객체), `layout/view.py` `import gmid_engine.search.front_entries as fe`, `convergence/peek.py` `from gmid_engine.search.front_query import ...`; (K-c) `search/kernel.py` `reader = sctx.archive.read_snapshot`(호출 아닌 참조)·`front_query._read_snapshot_file(path)`, `convergence/peek.py` `import _read_snapshot_file as load`. bad 트리의 허용 파일(`search/__init__.py`·`search/front_query.py`)은 위반 0 | 허용 파일 셋 안의 정의·재수출·`_read_snapshot_file` 사용, 허용 파일 밖의 무관한 이름(`front_entries_count`), 문자열 안 언급(docstring의 `read_snapshot`, 값 `"front_query"`), 쓰기 메서드 `write_snapshot` |
| M | 엔진: `pipeline/session.py`(M-a import·이름·속성), `search/kernel.py`(M-b `S3Index()`·별칭 `Counters()`). tests: `test_mb_construct.py`(M-b 이름·속성 꼴), `test_mc_sources.py`(M-c 매개변수·결과 칸·다른 호출 반환·순서 바뀜·다시 묶임·서로 다른 `open_run()`), `test_mc_loops.py`(M-c 반복문 밖 `open_run`·내포식·같은 이름 두 호출·안쪽 `def`/`lambda` 자유 변수·`**kw`/`*args`), `test_mc_indirect.py`(M-c import 별칭 호출의 대입 재사용·이름 대입 간접 호출의 매개변수 쌍·`getattr` 호출의 결과 칸 쌍·`if` 가지 안 대입), `conftest.py`(M-d 모듈 수준·session·module fixture·`pytest_configure` `config.stash`·`request.config`), `test_md_store.py`(M-d 클래스 속성·기본 인자값·`lru_cache`·호출형 `cache`·모듈 리스트 `append`·모듈 수준 객체 인스턴스 속성·session fixture `KernelContext`·helper 거친 package fixture·컨텍스트 칸 `case.sctx` 모듈 리스트 append), `test_mf_dump.py`(M-f `pickle.dump`·내부 칸 `json.dumps`·`shelve` 항목·결과 칸 `pickle.dumps`). 정의 모듈 넷은 bad 트리에서도 위반 0 | 튜플 풀기 1:1(결과 칸 `is` 확인), 호출마다 자기 `open_run()`, 반복문 안 `open_run`, function fixture 의 `open_run()` 반환, 단위 test 한 쌍으로 감쌈 함수 여러 번, 스스로 `open_run` 하는 helper, session fixture 가 지역 쌍으로 만든 S1 스냅샷 반환, 키워드 하나 빠진 꼴, `counters.snapshot()` 값의 json 출력, 엔진 진입이 두 객체를 받기만 함, docstring 안 언급, 실행 결과 스냅샷 칸(`res.s1`)의 모듈 캐시, 같은 이름을 새 `open_run()` 으로 다시 대입해 호출마다 하나, import 별칭 호출의 1:1 |
| 복사 등록부(`rule_copy`) | 원본 `legacy/old.py`. 등록 안 된 정의(`graph/copied.py` `extra`의 7·`"B"`, 모듈 수준 `CACHE = {}`), 본문이 바뀐 등록 정의(`graph/changed.py`, 변수 이름만 바꿈 -> 해시 다름·면제 취소), 리터럴 목록 오기(`graph/miscount.py`, 실제 12·등록 ()), 없는 정의 등록(`gone`), 가짜 등록부(`lut/`: 새 코드 `invented`에 자기 해시 -> 원본 대조 실패, `../graph/copied.py` 경로), 원본이 엔진 안 자기 자신(`metrics/`), 짧은 항목·중복 항목(`search/`), 정적 tuple 아닌 표(`sizing/`), 엔진 루트 등록부. D·E·G 기대 위반은 면제가 없거나 취소된 정의 안의 것뿐 | `graph/`(규칙 D 밖 리터럴 3·4·40, 넷 이름 `"A"`·`"B"`, 모듈 수준 dict를 담은 등록 정의 2개 + 같은 파일의 미등록 정상 정의)와 `lut/`(리터럴 없는 등록 정의) -- 두 하위 패키지의 등록부. 면제가 없으면 D·E·G가 FAIL하므로 통과가 면제 동작의 증거 |

GL-1 픽스처(기대 목록은 `test_g8_lint.py`·`test_value_types_lint.py`·`test_scan_shared_calls_tool.py`):

| 자리 | `bad`/case가 담은 위반 | `good`이 보이는 허용 경우 |
|---|---|---|
| `rule_g8` | `attr.py`(self/cls 속성 가변 값, 중첩 def, 중첩 클래스), `classc.py`, `factory.py`(`default_factory`), `cached.py`, `cachecall.py`(`lru_cache(...)(f)` 한 건), `modcache.py`(if·try·with·for·match 안), `idcall.py`, `edges.py`(첫 줄·끝 줄·같은 키 둘), `memocall.py`·`memolookup.py`, `graph/registered.py`(유효한 복사 등록부에 등록된 정의도 위반), `metrics/run_counters.py`(허용 모듈과 이름만 같음), 허용 모듈 14개 파일(위반을 담지만 안 나옴) | `clean.py`(`None`·`()`·`tuple(x)`·`frozenset(x)`, 지역 `{}`, `memo.call(module_fn, 1)`, `x.id(1)`), 허용 `core/run_counters.py` |
| `rule_vt` | `valtypes.py`(frozen 3종 + 아닌 것 3종), `use.py`(주석 8건), `assign.py`(대입 13건), `places.py`(클래스 본문·메서드 `self.a`), `use2.py`(허용 모듈에서 정의된 타입), `metrics/run_counters.py` | `ok.py`(함수 지역·인자·반환, frozen 본문, 원시 tuple, 클래스 자체 `R = Pt`) |
| `shared_calls/<case>` | `same_input`·`diff_input`·`local_trace`·`helper_trace`·`reexport`·`param_only`·`one_caller`·`method`·`touching` | -- |

## 설계 문서에서 애매했던 점(이 test가 택한 해석)

1. **A의 레지스트리 데코레이터 이름**: 설계 문서에 이름이 나온 것은 `compute_block`뿐이다. D 1.2 (A)의 예시 'metric 레지스트리 항목들'의
   데코레이터 이름은 없다. 또 D 1.2 (C)는 `@compute_block`을 파일당 1개로 정하므로 `compute_block` 변형군 예외는 사실상 쓰이지 않는다.
   metric 레지스트리 데코레이터를 만들면 설계 문서에 이름을 적고 `REGISTRY_DECORATORS`에 더한다.
2. **A와 데이터·helper 모듈**(해결, 오케스트레이터 결정 2026-10-07): 규칙 표 A의 보충 (1)~(3)으로 정했다. 그래서
   `core/failures.py`처럼 예외 클래스와 공개 함수(`exit_code_for`·`normalized_margin`)를 한 파일에 두면 FAIL이고, 함수는 별도 파일로 옮긴다.
   보충 (3)은 공개 **함수**만 센다(비공개 모듈의 공개 클래스는 사용 수를 보지 않는다). 복사 정의처럼 `_` 이름 함수를
   공개 별칭(`build_rows_from_shares = _build_rows_from_shares`)으로 내보내면 그 별칭도 공개 함수로 센다 -- 세지 않으면
   비공개 모듈이 공개 함수 0개로 공허하게 통과한다(2026-10-07 `layout/_helpers_hubleaf.py` 판정에서 발견, 오케스트레이터 승인).
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
11. **등록부 파일 자신**: 공개 정의 0(상수 표)이라 규칙 A를 통과하고, 숫자 대신 문자열을 적어 규칙 D 대상이 없다. 규칙 H에서는
    제외한다(공개 동작이 없는 `_` 모듈, 규칙 표 H 예외, 오케스트레이터 결정 2026-10-07) -- 등록부 검증은 이 폴더의 test가 한다.
12. **리터럴 '집합'**: 설계 8절 2는 '집합'이라 적었지만 등록부(`layout/_copy_manifest.py`)는 중복을 유지한 정렬 tuple로 적었다.
    이 test도 중복 유지 목록으로 비교한다(같은 값의 리터럴이 하나 더 들어와도 잡는다).
13. **I의 범위(무엇을 '회로별 정보'로 보나)**: 엔진은 회로를 구조(connectivity)로만 다루고 이름은 불투명한 값으로만 옮긴다.
    그래서 (a) 손선언 태그를 읽는 입구(키 리터럴 조회)와 (b) 이름을 특정 문자열과 맞대 보는 분기를 막는다. 이름을 값으로
    들고 다니는 것(`dev.name` 을 dict 키로 쓰기, 이름끼리 비교)은 허용한다. 변수 이름만 보고는 식별자인지 알 수 없어
    (b)는 식별 속성·키를 통한 표현만 잡는다(`name == "x"` 처럼 지역 변수와의 비교는 잡지 않는다 -- 이 빈틈은
    `tests/generality/` 의 이름 치환 metamorphic test 가 동작으로 메운다).
14. **I (a) 키 목록의 library 하위 키**: 태그 섹션 전체가 유도 입력이 아니므로(authoring CONTRACT 머리, U-50) 섹션 아래 역할·대응
    선언 키로 바로 조회하는 것도 같은 우회다. 일반 낱말(`vsb`·`theta`·`metrics`·`constraints`·`objective`·`function`·`notes`·
    `parameters`·`dispositions`)은 엔진 자신의 값 키와 겹쳐 `TAG_SUBKEYS_NOT_BANNED` 로 뺐다(spec·constraints 는 U-50 이 입력으로
    둔다). library 에 새 태그 하위 키가 생기면 `test_rule_i_library_tag_subkeys_classified` 가 둘 중 하나로 분류를 요구한다.
15. **I 예외의 `report/`**: 아직 파일이 없는 폴더 접두 예외다(과제 지시 '보고 모듈이 topology_name 을 출력용으로 담는 것').
    파일 항목 예외는 `test_rule_i_exemptions_are_used` 가 '예외를 빼면 실제로 걸리는 조회가 있다'(낡은 예외 0)를 확인한다.
16. **tests/ 와 규칙 I**: 검사 대상은 다른 규칙과 같이 `tests/` 제외다. `tests/generality/topogen/`(합성 topology 생성기)은 스스로
    규칙 A·B 검사기를 건다(`test_topogen_helpers_obey_structure_rules_a_b`). `tests/generality/` 는 엔진 하위 패키지 이름이 아니라
    규칙 H 의 고아 검사 대상이 아니다.
