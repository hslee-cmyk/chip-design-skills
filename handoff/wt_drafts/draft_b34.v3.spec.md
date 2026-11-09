---
id: 20260930-b34-grammar-explicit
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260930-b26-before-phase3
---
## 의도

백로그 B34(`_drafts/backlog_additions.md` 7행, 준비 자료 `_drafts/prep_b34_b35_grammar.md` §1·§3.1): `stick_diagram.py`가 `skills/analog-grammar`를 import하지 못하면
**조용히 `None`을 돌려주고 호출자가 '보강 기능 없이' 계속 간다**. 그런데 이 기능은 보강이 아니라 사이징 입력의 원천이다. analog-grammar가 없으면 다음이 바뀐다(준비 자료 §1.3, 사본 `nog` 실측).
* `load_topology` meta가 library 9/9 회로에서 달라진다. 자동 채움 `device_roles`·`_matching_pairs_*`가 사라지고 `_device_roles_gap_fill_review_needed`가 9회로 모두 0건이 된다.
* 그래서 review 게이트 `require_device_roles_reviewed`(SR 7952에서 호출)가 검사할 재료를 잃는다. '검사 통과'와 '검사 못 함'이 구분되지 않는다.
* `current_reuse_telescopic_ota` θ\* 평가가 성공에서 `ValueError`(vertical_stack_id 그룹 순환)로 바뀐다.

설치본에서 실제로 일어나는 경로다: `install.py` `SKILLS`(27~29행)에 `analog-gmid-design`은 있고 `analog-grammar`는 없다.

원칙 기본안(메모리 '우회/skip 타당성 검토' 세 질문, 계획 §3.2 조용한 폴백 금지): (1) 대상은 설치본에서 실재한다 (2) 폴백 자체가 틀렸다(결과를 바꾸므로 '기존 동작' 전제가 거짓) (3) 명시적 의존으로 고칠 수 있다.

**범위(v2, 검토 review_b34 권고안 1·2 채택).** 문제의 정의(조용한 폴백)를 닫는 데 필요한 것과, 변이 비용이 작은 def의 부재 분기 정리만 한다. 운영 경로 큰 def의 도달 불가 분기 삭제는 그 def 본문을 어차피 바꾸는 card(B26-1·B35)로 넘긴다.
A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 gate `master` `7535799` 기준이다(`cd64170..7535799` 사이 SD·SR·tests 변경 없음 -- 검토 확인).

1. **지연 import는 유지한다.** `import stick_diagram`만으로 analog-grammar를 요구하지 않는다(Phase 3 뒤 레이아웃 전용 모듈이 analog-grammar 없이 import되어야 한다 -- 준비 자료 §3.1 (a) 기각 이유).
   `_import_analog_grammar`가 `ImportError`를 삼키지 않고, 필요한 skill 이름(`analog-grammar`)과 찾은 경로를 적은 `ImportError`를 원래 예외에 이어(`from`) 다시 던진다.
   **raise 모양은 고정이다**(V3 변이 수 55의 전제, review2 M2). 지금의 `except ImportError:` 절 하나를 `except ImportError as e:`로 바꾸고, 본문을 `raise ImportError(<메시지>) from e` 한 문장으로 둔다.
   메시지는 `'analog-grammar'`와 `_ag_path`를 담은 문자열 식 하나다(예: f-string 하나). 정수 상수를 더하지 않는다. 모듈·이름마다 raise를 반복하지 않는다. 새 지역 변수·도움 함수를 만들지 않는다.
   이 모양에서 벗어나면 변이 수가 달라진다. 그때 추가로 생기는 변이도 계약 1·3이 죽여야 한다. code-author는 모양을 지키고, auditor는 순서 3 뒤 변이 수를 다시 잰다.
   sys.path 주입 방식(레지스트리 360행 R1)은 바꾸지 않는다(별도 건). 지금의 주입 순서(맨 앞, 멱등)는 계약 4로 고정한다(아래 'V3 계획' -- 변이를 죽이는 계약).
2. **작은 def 3개의 부재 분기를 지운다**(사이트 2·3, 11·11b). `find_stack_edges`만 운영 도달, 나머지 둘은 비운영이고 V3 인벤토리가 4~66개다.
   이 def들의 기존 생존 변이는 면제하지 않고 죽이는 계약(4·6)을 더한다. 면제 0('V3 계획').
   `find_differential_and_mirror_forks`(사이트 4)는 넣지 않는다: 넣으면 기존 생존 3개 중 1개가 등가 변이라 별도 면제 승인이 필요하다(실측, 'V3 계획' 끝). 도달 불가 분기 1개는 백로그.
3. **운영 경로 큰 def의 부재 분기는 이 card에서 코드를 바꾸지 않는다.** 1번 뒤에는 도달 불가 분기가 된다(부재면 `_import_analog_grammar`가 먼저 `ImportError`). 동작 영향은 없다.
   docstring·주석은 이 card에서 전부 고친다(AST 해시 불변 → V3 비용 0): "부재는 `ImportError`, 이 함수의 `… is None` 분기는 도달 불가 -- 삭제는 B26-1/B35".
   * B26-1(`refine_…`·`propose_device_roles_gap_fill`에 `rails`를 넣는 card)로 인계: 사이트 9·10·10b·13·14와 `propose_device_roles_gap_fill` 3966~3970의 `unavailable_reason`(analog-grammar가 **있어도** gate 소자 없는 입력에 "analog-grammar를 import할 수 없어…"를 싣는 틀린 사유, 소비처 0).
   * B35(운영 함수에 `rails` 키워드를 넣는 card, 준비 자료 §3.2)로 인계: 사이트 5~8.
   * 백로그로: `find_differential_and_mirror_forks`의 사이트 4(위 2), `propose_theta_kcl_gap_fill`의 사이트 12와 3533~3535 `unavailable_reason`(비운영, 변이 242·기존 생존 추정 약 48 -- 이 card의 목표와 무관한 기존 test 강도 보강을 끌어들이지 않는다).
4. **범위 밖(그대로 둔다):** '입력에 gate 소자가 없음 → `None`/빈 결과'(`_to_analog_grammar_devs`가 `[]`인 경우). `test_s120_section`이 고정한 동작이다(계약 5). docstring은 '부재'와 'gate 소자 없음'을 나눠 적는다.
5. **동작 보존:** analog-grammar가 있으면 E-LIB 9/9와 E-INST가 base와 같다.

이 card는 회로·넷·소자 이름을 읽지 않는다(import 실패 처리와 분기 삭제뿐). 레일 이름 집합(B35)과 analog-grammar 쓰기 경로·게이트 공백(B36)은 범위 밖이다.
`install.py` `SKILLS`에 `"analog-grammar"`를 더하는 것은 사용자 쓰기 경로(N3.12.2 `사용자 | install.py`)라서 이 card에 넣지 않고 **별도 사용자 작업**으로 보고한다.
이 card 뒤에는 그 편집이 없으면 설치본이 조용히 틀리는 대신 명시적으로 실패한다.

### 사이트 목록(7535799 재측정, 전부 SD)

코드를 바꾸는 것(이 card):

| # | 함수 | 줄 | 바꾸는 것 |
|---|---|---|---|
| 1 | `_import_analog_grammar` | 1057~1058 | `except ImportError: return tuple(None …)` → `except ImportError as e:` + 한 문장 `raise ImportError(<'analog-grammar'와 _ag_path를 담은 문자열 식 하나>) from e`(정수 상수·반복 raise·새 지역 변수 없음 -- 범위 1). docstring 1046~1048 |
| 2 | `find_idiom_matches` | 1073~1074 | `if netclass is None: return None` 삭제 |
| 3 | `find_stack_edges` | 1089~1090 | 같음 |
| 11 | `audit_theta_root_direction` | 3381~3382 `if netclass_mod is None or idioms_mod is None: return []` | 삭제 |
| 11b | 같은 함수 | 3387~3388 `if matches is None: return []` | 삭제. 3384 `if not devs` 가드 뒤라 `find_idiom_matches`는 부재에서만 `None`이었다(base에서는 3381이 먼저 잡아 도달 불가) |

코드를 바꾸지 않는 것(도달 불가가 된다 -- docstring만 이 card, 코드 삭제는 인계):

| # | 함수 | 줄 | 인계 |
|---|---|---|---|
| 4 | `find_differential_and_mirror_forks` | 1313~1314 `if netclass is None: return None` | 백로그(등가 변이 면제가 필요해 이 card에서 뺌) |
| 5 | `suggest_vertical_stack_composites` | 1445~1446 | B35 |
| 6 | `find_verified_differential_and_mirror_relations` | 1714~1715 | B35 |
| 7 | `_propose_vertical_stack_ids` | 1894~1895 | B35 |
| 8 | `_propose_headroom_roles` | 2259~2260 | B35 |
| 9 | `refine_differential_and_mirror_relations` | 2400~2401(내부 `classify`의 `return None, None`), 2410~2411 | B26-1 |
| 10 | 같은 함수 | 2494 `_netclass_al, _idioms_al = …`, 2495 `if _netclass_al is not None:`(블록 2496~2523) | B26-1 |
| 10b | 같은 함수 | 2440~2441 `if relations is None: return None` | B26-1 |
| 12 | `propose_theta_kcl_gap_fill` | 3529~3531(부재 → `unavailable_reason`), 3538~3540, 3533~3535의 `unavailable_reason` 키 | 백로그 |
| 13 | `propose_device_roles_gap_fill` | 4071~4073 `_static_ref_roles = (…) if _netclass_lcmf is not None else ()` | B26-1 |
| 14 | 같은 함수 | 4087 `if _idioms_lcmf is not None:`(블록 4088~4109), `else:` 4110, `cascoded_active_load_legs = set()` 4111 | B26-1 |
| -- | 같은 함수 | 3966~3970 `unavailable_reason`(`refined is None`, gate 소자 없음에서도 참 -- 틀린 사유) | B26-1 |

남기는 것(gate 소자 없음 경로 -- 코드 그대로, docstring만 고친다): `find_idiom_matches` 1076~1077, `find_stack_edges` 1092~1093, `find_differential_and_mirror_forks` 1316~1317,
`suggest_vertical_stack_composites` 1448~1449, `find_verified_…` 1717~1718, `_propose_headroom_roles` 2262~2263, `audit_theta_root_direction` 3384~3385,
전파 사이트 `find_differential_pair_candidates` 1543, `_propose_gm_id_roles` 2092, `_propose_L_roles` 2165·2169, `refine_…` 2420, `propose_vertical_stack_id_gap_fill` 3296, `geometry_colocation_union` 3115.

docstring·주석(코드 AST 불변. 부재 서술을 'ImportError'로, 도달 불가 분기가 남는 함수는 "`… is None` 분기는 도달 불가 -- 삭제는 B26-1/B35/백로그"를 한 구절, gate 소자 없음 서술은 남김):
* SD: 1025~1031 주석 블록, 1046~1048, 1304, 1384, 1533, 1676, 1891~1892, 2070, 2152, 2241, 2349, 3085, 3282, 3367, 3374~3375, 3526~3527, 3932~3933.
  3374~3375는 IC5 '검사하지 않는 것:' 절 안이다 -- 절 머리와 `영역: dc, ac_struct` 줄은 그대로 두고 analog-grammar 문장만 뺀다(`test_ic5` 대상).
* SR `resolve_stack_layout` docstring 6509~6512(4번 "analog-grammar 자체가 없어 candidates도 `None`이면 … 완전한 하위호환"): "candidates가 `None`(입력에 gate 소자가 없음)이면 `geometry_colocation_union()`으로 폴백. analog-grammar 부재는 그보다 먼저 `ImportError`"로 고친다. 쓰기 주체 code-author(`A/*.py`), AST 해시 불변.

## 관찰 가능한 계약

A = `skills/analog-gmid-design/assets`. 모듈 경로: 모든 진입점과 `Transistor`는 `stick_diagram` 모듈(`A/stick_diagram.py`)의 최상위 이름이다. `Transistor`는 dataclass이고 생성은 `stick_diagram.Transistor(name, kind, source=…, drain=…, gate=…)`(gate 생략 = `None`)다.
'부재'는 test가 파일 시스템을 건드리지 않고 흉내 낸다: `monkeypatch.setitem(sys.modules, "netclass", None)`과 `monkeypatch.setitem(sys.modules, "idioms", None)`(둘 다, 또는 계약 2의 한쪽만). 이렇게 하면 그 이름의 import가 `ImportError`(하위형 `ModuleNotFoundError`)를 낸다.
입력(`ts`, 소자 이름)은 부재를 만들기 **전에** `load_topology(p)`로 얻고, 부재는 **test 함수 본문 안에서만** 만든다(세션·모듈 fixture 안에서 만들지 않는다 -- 첫 import 전에 부재를 만들면 복원 뒤 모듈 객체가 바뀔 수 있다).
**부재 상태에서는 `stick_diagram`(SD) 진입점만 부른다.** `sizing_recipe`(SR) 모듈의 함수는 하나도 부르지 않는다(review2 M4). 특히 SR의 topology 캐시 함수와 그것을 거치는 함수가 그렇다(이름을 백틱으로 적지 않는 것은 interface card 생성기가 그 함수를 진입점으로 싣지 않게 하려는 것이다).
SR 캐시는 경로를 키로 `load_topology` 결과를 쥐고 있다. 그래서 앞선 test가 채운 캐시가 부재를 가려, 오류 대신 캐시 값을 돌려줄 수 있다.

**test 모양(V3 인벤토리 조건).** 아래 각 진입점은 test 함수 **본문**에서 `stick_diagram.<이름>(…)` 형태로 직접 부른다. `@pytest.mark.parametrize`의 이름 문자열이나 모듈 수준 이름 목록 + `getattr`로만 부르면 안 된다 --
V3 정적 인벤토리(`reachability.build_graph`)는 데코레이터 인자와 모듈 상수를 test 노드의 간선으로 보지 않아, 새 test가 비운영 def(`find_idiom_matches`·`audit_theta_root_direction`)의 인벤토리에서 빠진다(실측 -- '작성 전 실측' 3).
회로 9개에 대한 반복은 parametrize로 해도 된다(회로 경로는 진입점 이름이 아니다).
**def 이름은 저장소 그래프에서 유일하게 짓는다**(review2 S1). 새 test 파일의 모든 def가 대상이다. helper·중첩 함수·fixture는 `_b34_` 접두로(예: `_b34_snapshot`, `_b34_normalize`), test 함수는 `test_b34_` 접두로 짓는다. 이유: V3 정적 그래프(`reachability.build_graph`)는 다른 모듈에서 해석하지 못한 이름 참조를 **이름만으로** 전 그래프에 잇는다.
그래서 snap·run·check·norm 같은 흔한 이름은 다른 파일(예: probes/probe_classab_battery_headroom.py의 snap 호출)과 이어져 인벤토리를 suite 전체로 부풀린다.
실측: 중첩 함수 `snap` 하나로 인벤토리가 159·15·66·4에서 237·236·234·234로 커졌다. `_b34_snapshot`으로 바꾸자 기존 값 + 새 test 함수 수로 돌아왔다.

1. **부재 → 명시적 오류.** 두 모듈이 모두 부재일 때, 아래 공개 진입점이 전부 `ImportError`(하위형 포함)를 낸다. 반환값을 내지 않는다.
   * `stick_diagram.load_topology(p)` -- `p` = `A/library/*.topology.json` 중 `_`로 시작하지 않는 9개 각각.
   * `stick_diagram.run_topology_pipeline(p, overrides)` -- 같은 9개, `overrides` = 소자마다 `{"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_<소자 이름>"}`(`test_ic3.py` 3절과 같은 구성).
   * transistor 목록을 받는 함수: `find_stack_edges(ts)`, `find_idiom_matches(ts)`, `find_differential_and_mirror_forks(ts)`,
     `suggest_vertical_stack_composites(ts)`, `find_differential_pair_candidates(ts)`, `find_verified_differential_and_mirror_relations(ts)`, `refine_differential_and_mirror_relations(ts)`,
     `audit_theta_root_direction(ts, None)`, `propose_theta_kcl_gap_fill(ts, [])`, `propose_device_roles_gap_fill(ts, {}, [])`, `geometry_colocation_union(ts, [])`,
     `propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))`.
2. **한쪽만 부재여도 오류.** `idioms`만 부재(`netclass`는 정상)이면 `load_topology(p)`(9개)가 `ImportError`를 낸다. `netclass`만 부재이면 `find_stack_edges(ts)`(9개)가 `ImportError`를 낸다.
3. **오류 메시지와 원인.** 계약 1·2의 `ImportError`는
   * `str(exc)`에 문자열 `analog-grammar`가 있고,
   * `str(exc)`에 analog-grammar 탐색 경로가 있다 -- 기대 경로 `E = norm(<저장소 루트>/skills/analog-grammar/assets)`(저장소 루트는 test 파일 위치에서 구한다).
     **경로 정규화 `norm(x)` = `os.path.normcase(os.path.realpath(x))`이고, 비교는 양쪽에 같은 정규화를 쓴다**(review2 M1). SD의 `_ag_path`는 `os.path.dirname(__file__)`에서 만들고 resolve하지 않는다.
     그래서 test 쪽 `Path(__file__).resolve()`와 글자가 다를 수 있다(sys.path 항목 기준 `__file__`, 드라이브 문자 대소문자, 링크).
     통과 조건은 둘 중 하나다: (i) `os.path.normcase(str(exc))`에 `E`가 있다. (ii) `os.path.normcase(str(exc))`에 `M = os.path.normcase(os.path.normpath(os.path.join(os.path.dirname(stick_diagram.__file__), "..", "..", "analog-grammar", "assets")))`가 있고 `norm(M) == E`다
     (M은 test가 모듈 위치에서 만든 값이고 피검 출력이 아니다),
   * `exc.__cause__`가 `ImportError`(하위형 포함)다(원래 import 실패를 잃지 않는다).
4. **탐색 경로는 맨 앞에 한 번(analog-grammar 있음). -- 생략 불가(V3 필수, review2 S2).** 위 탐색 경로를 `sys.path`에서 뺀 상태(`monkeypatch.setattr(sys, "path", [x for x in sys.path if norm(x) != E])`)에서
   `stick_diagram.find_stack_edges(ts)`를 한 번 부르면 `norm(sys.path[0]) == E`이고, 한 번 더 불러도 `sys.path`에서 `norm(x) == E`인 항목이 정확히 한 개다(`norm`·`E`는 계약 3과 같다).
   (근거: analog-grammar 자신의 `netclass`·`idioms`가 같은 이름의 다른 모듈보다 먼저 잡혀야 한다. 지금 동작 그대로다.)
   이 계약만 죽이는 변이가 있다: `_import_analog_grammar:const+:body[3].body[0].value.args[0]`·`const-:…args[0]`(`insert(0, …)`의 `0` → `1`/`-1`)와 `_import_analog_grammar:stmt_delete:body[3]`(`if … not in sys.path` 블록 삭제).
   기존 test는 앞의 둘을 못 죽인다(실측). 이 계약을 빼면 V3 FAIL이다.
5. **gate 소자 없음 경로는 그대로(analog-grammar 있음).** `fx = [Transistor("Ma", "pmos", source="vdd", drain="n1"), Transistor("Mb", "nmos", source="gnd", drain="n1")]`(gate 없음)에 대해
   `find_idiom_matches(fx) is None`, `find_stack_edges(fx) is None`, `find_differential_and_mirror_forks(fx) is None`, `refine_differential_and_mirror_relations(fx) is None`, `audit_theta_root_direction(fx, None) == []`.
   부재 상태에서 `import stick_diagram`(새 프로세스, `sys.modules`에 두 이름을 `None`으로 둔 뒤)이 성공한다(모듈 최상위 import 아님).
6. **θ가 있어도 발견 없음인 두 입력(analog-grammar 있음). -- 생략 불가(V3 필수, review2 S2).** 기존 test가 못 죽이는 `audit_theta_root_direction` 변이 3개를 이 계약만 죽인다(실측):
   `audit_theta_root_direction:stmt_delete:body[3]`(`if not devs` 삭제), `…:stmt_delete:body[3].body[0]`(그 `return []` 삭제), `…:stmt_delete:body[6].body[5].orelse[0]`(A_signed 분기 `others = …` 삭제). 이 계약을 빼면 V3 FAIL이다.
   * `audit_theta_root_direction(fx, {"theta": [{"name": "t", "feeds": {"type": "A", "root": "Ma", "reference": ["Mb"]}}]}) == []` -- gate 소자가 없으면 θ 선언과 무관하게 빈 리스트(예외 없음).
   * `gx = [Transistor("M1", "nmos", source="gnd", drain="n1", gate="n1"), Transistor("M2", "nmos", source="gnd", drain="out", gate="n1")]`에 대해
     `audit_theta_root_direction(gx, {"theta": [{"name": "t", "feeds": {"type": "A_signed", "root": "M1", "terms": []}}]}) == []` -- `terms`가 비면 비교할 상대가 없어 발견 없음(예외 없음).
7. **동작 보존(analog-grammar 있음, auditor 대조).** E-LIB 9/9(`load_topology`, `run_topology_pipeline` V1·V2)와 E-INST(파일럿·`folded_cascode`)가 base와 같다. 계약 1의 진입점 14개 × 9회로 반환도 base와 같다.
   비교는 아래 정규화 뒤 `==`다(base·head를 다른 프로세스에서 돌리므로 `set` 순서가 다를 수 있다. 정규화 대신 두 실행의 `PYTHONHASHSEED`를 같은 값으로 고정해도 된다).
8. **부재 후 복구(test 판정).** 한 test 함수 안에서 부재를 만들었다 되돌리면(monkeypatch `undo` 또는 `with monkeypatch.context()`), 같은 진입점이 **부재 전에 같은 프로세스에서 얻은 값**과 정규화 뒤 `==`인 값을 낸다(상태 누수·잘못된 캐시 없음).
   oracle은 부재 전 값이다(피검 함수를 두 번 부른 값끼리의 비교).
**정규화(계약 7·8).** 값을 재귀로 바꾼다.
* `Match`류 -- `find_idiom_matches` 반환 리스트의 원소: 속성 `kind`·`devices`·`ports`(dict)·`note`·`priority`를 가진 객체이고 `__eq__`가 없다(같은 입력으로 두 번 부른 값도 `!=`). → 튜플 `(kind, tuple(devices), sorted(ports.items()), note, priority)`.
* `set`/`frozenset` → 원소를 정규화한 뒤 정렬한 리스트(원소 종류가 섞일 수 있으므로 정렬 키는 `repr` 또는 `json.dumps(…, sort_keys=True)`).
* `dict` → 값을 정규화한 dict(키 순서는 `==`에 영향 없음). `list`/`tuple` → 원소 정규화. dataclass(`Transistor` 등)와 나머지 값은 그대로 `==`.

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(새 심볼 없음. 지우는 def 없음. 바뀌는 것은 def 4개의 본문.)

## 판정 유형 근거

red-green. base(`7535799` 사본, 실측)에서 부재를 만들면 계약 1의 진입점 14개가 9/9 회로 전부 **예외 없이 반환한다**(126/126, `idioms`만 126/126, `netclass`만 126/126) --
`load_topology`·`run_topology_pipeline`·`audit_theta_root_direction`·`geometry_colocation_union`·`propose_vertical_stack_id_gap_fill`은 값을, 어댑터 7개는 `None`을, 두 제안 함수는 `unavailable_reason`이 든 dict를 준다.
그래서 base에서 `pytest.raises(ImportError)`가 'DID NOT RAISE'(`Failed`)로 실패한다. 계약 2·3은 같은 이유로 red다.
**red는 전부 단언형(`Failed`/`AssertionError`)이다** -- base에서 부재 시 다른 예외가 나는 진입점은 0개다(실측 OtherError 0).
test 쪽 안전장치(권고): 진입점 호출을 `try` / `except ImportError` / `except Exception as e: pytest.fail(...)` / `else: pytest.fail("조용히 반환")` 모양으로 쓰면 base가 어떤 비-ImportError를 내도 red가 단언형으로 남는다.
계약 4~8은 base에서도 green(현재 동작 고정·보존).

## oracle 종류와 출처

* 계약 1·2·3: (a) 구성 -- 부재를 test가 만들었으므로 '거부해야 한다'가 구성으로 정해진다. 탐색 경로는 test 파일 위치에서 구한 저장소 루트로 test가 만든다(피검 출력으로 만들지 않는다).
* 계약 4: (c) 기존 동작(주입 순서 맨 앞·멱등, 지금 코드 그대로) + (a) 구성(탐색 경로는 test가 만든다).
* 계약 5: (c) 기존 동작 -- `test_s120_section`이 고정한 값과 같다(`forks`도 base 실측 `None`).
* 계약 6: (a) 구성 -- 첫째는 gate 소자가 없어 비교할 소자가 없고, 둘째는 `terms`가 비어 비교 상대가 없다. 두 기대값 모두 base 실측과 같다.
* 계약 7: (c) base 실행 결과(auditor, 정규화 또는 같은 `PYTHONHASHSEED`).
* 계약 8: (c) 같은 test 안에서 부재 전에 얻은 값(test가 판정, 정규화 뒤 `==`).

## 거부해야 할 입력

analog-grammar 부재(두 모듈, `idioms`만, `netclass`만 -- 계약 1·2). 판정기 자기 점검: 부재에서 조용히 `None`·`[]`·dict를 돌려주는 합성 구현(예: test 안의 가짜 진입점 `lambda *a: None`,
`lambda *a: {"unavailable_reason": "x"}`)을 같은 판정 함수에 넣으면 실패해야 한다. 메시지에 `analog-grammar`가 없는 `ImportError`, `__cause__`가 없는 `ImportError`도 판정 함수가 거부해야 한다
(`test_d_delete_telescopic`의 거부 점검과 같은 형태). 계약 8의 비교 함수는 정규화 없이 `Match` 리스트를 `==`로 비교하는 판정(항상 '다름')을 쓰지 않았음을 자기 점검한다(같은 값 두 번 → 같음).

## library 회로 적용 여부

적용한다. library 9회로 전부가 계약 1·2(부재 → 오류)·계약 7·8(보존·복구) 대상이다. SPECS 4회로 θ 평가(준비 자료 §1.3 (a))는 계약 7의 E-INST와 base 대조로 덮고 따로 계약하지 않는다
(부재 시 SR 경로는 `load_topology`에서 먼저 `ImportError`가 난다).

## 무동작 판정 입력(무발동 값)

analog-grammar가 있는 모든 실행 -- library 9회로, E-INST, 기존 test 전부. 이 card의 새 동작(오류)은 부재에서만 발동한다. gate 소자 없음 경로(계약 5·6)도 무발동이다(반환 불변).

## 재현할 수치

없음.

## V3 계획

`mutate_changed.py`는 AST 해시(docstring 제외)가 바뀐 def 전체를 변이한다. 이 card는 def **4개**만 바꾼다(docstring·주석 수정은 해시 불변 -- 모의 head에서 `changed_defs` = 4 확인).
모의 head(`7535799` + 위 코드 변경, scratch) 실측:

| def | 변이(head) | 인벤토리(기존) | 새 test 포함 시(기존 + k) | B34 계약 1~3·5·6·8로 죽음 | 기존 test로 죽음(나머지 중) | 남는 것 |
|---|---|---|---|---|---|---|
| `_import_analog_grammar` | 12 | 159 | 159 + k | 10 | 0/2 | 2 = `sys.path.insert(0, …)`의 `0` ±1 → **계약 4가 죽인다**(실측) |
| `find_idiom_matches` | 8 | 15 | 15 + k | 8 | -- | 0 |
| `find_stack_edges` | 6 | 66 | 66 + k | 5 | 1/1 | 0 |
| `audit_theta_root_direction` | 29 | 4 | 4 + k | 14 | 15/15 | 0 |
| 합 | **55** | | | 37 | 16/18 | 0(계약 4가 2개) |

* k = 그 def에 (본문 직접 호출로) 닿는 새 test 함수 수(review2 M3. v2의 '+1'은 새 test 함수가 1개라는 전제였다). reviewer 재현 test(함수 7개)에서는 166·19·72·8이었다.
* **auditor 인벤토리 확인(순서 3 freeze 뒤, review2 S1).** 새 test 파일을 넣은 그래프에서 4 def 인벤토리가 159·15·66·4 + k인지 본다(k ≤ 새 test 함수 수).
  이를 넘으면(실측 예: 237·236·234·234) 새 test의 def 이름이 다른 파일의 이름과 이어진 것이다('test 모양'의 이름 규칙 위반). V3를 돌리기 전에 test-author에게 이름 정정을 돌려보낸다.
* 방법: 모의 head에서 변이를 하나씩 적용(`mutate_changed.mutants`·`_replace_def`)해 (1) B34 계약 판정을 같은 프로세스에서 돌리고, (2) 거기서 안 죽은 것을 도구와 같은 pytest 명령으로 인벤토리의 기존 test만 돌렸다('작성 전 실측' 3·4).
* base에서 `audit_theta_root_direction`의 기존 생존 7개(검토 표본) 중 4개는 이 card가 지우는 문장(3381·3382·3387·3388)이고, 남는 3개(3384 `if not devs` 문장 삭제·`return` 삭제, 3402 `others = …` 삭제)는 **계약 6이 죽인다**(모의 head 실측).
* 면제 없음(기존 생존 면제·등가 변이 면제 모두 0). V3 기준 약화 승인 불필요.
* 도구 동작 참고: 인벤토리 기준 실행이 실패하면 ERROR(B28). 새 test 파일은 test-author가 쓰므로 순서 3 freeze 뒤 auditor가 base·head 인벤토리 기준 실행을 확인한다.
  (scratch 사본은 git 이력이 없어 이력 의존 test 2개가 기준 실행에서 실패했다: `test_ts6_probe_relocate::test_base_blob_reader_reads_the_base_tree`와 `test_ts6_probe_relocate::test_moved_tool_matches_base_except_path_lines`(둘째는 review2 실측).
  사본 결함이다. 도구는 이력 있는 복제본에서 돌므로 해당 없다. 이 측정에서는 그 두 test를 빼고 돌렸다.)
* 기각한 확장(검토 권고안의 `find_differential_and_mirror_forks` 포함): 변이 47개 추가(인벤토리 10). B34 계약으로 22, 기존 test로 22 죽고 3개 생존 -- kind 검사 `if`·`continue` 삭제 2개는 계약("kind가 다른 두 소자는 fork 짝이 되지 않는다", 예 `Mp` pmos·`Mn` nmos가 `vdd`에 닿고 gate 공유)으로 죽일 수 있으나(실측),
  `stick_diagram:find_differential_and_mirror_forks:const-:body[8].body[2].value.generators[0].ifs[0].comparators[0]`(`len(members) >= 2` → `>= 1`)은 **등가 변이**다(구성원 하나인 fork는 쌍이 없음). 이 card에 넣으면 등가 변이 면제 decision 기록이 하나 더 필요하다(A2 기록 `20260930-b26-before-phase3`의 target에는 없다). 비운영 def의 도달 불가 분기 1개를 지우려고 승인을 늘리지 않는다 -- 백로그.

## 결정 필요 항목

1. **앞당김 -- 승인됨.** B34는 N6.1 Phase 2 범위 행에 없는 백로그 항목이고, 부재 시 반환이 `ImportError`로 바뀌는 **동작 변경**이다. design 20 승인(`20260923-20-dead-code-dup-design`)은 "동작이 바뀌는 수정"을 덮지 않는다(검토 B1).
   그래서 `approval`은 사용자가 승인한 A2 decision 기록 **`20260930-b26-before-phase3`**(DEC-60 넷 전환기 종료 + DF-19·DF-26 넷 몫 분리 + B26-1·B34의 Phase 3 전 착수를 한 기록으로 덮음, 사용자 원문 "승인 (Recommended)")를 가리킨다.
   그 기록은 이 card 커밋 전에 gate에 있어야 한다(오케스트레이터). 이 card는 V3·V7 면제가 필요 없으므로 그 기록의 `target`에 변이 id를 더할 필요가 없다.
   **그 기록의 범위에 B34가 이름으로 있어야 한다**(review2 B1). 기록의 `scope:` 줄과 '덮는 것'이 이 card id(`20260930-b34-grammar-explicit`)를 적고, 동작 변경(analog-grammar 부재 → `ImportError`)과 def 4개를 명시해야 한다.
   사용자 원문 절은 실제로 물은 A2 질문을 인용해야 한다. 그 질문의 ③이 "B26-1(…)과 B34(analog-grammar가 없으면 조용히 폴백하던 것을 명시적 오류로 바꿈)를 Phase 3 모듈 분할보다 먼저 합니다"다.
   B26-1만 적은 기록이면 이 card의 `approval`은 동작 변경을 덮지 못한다. 커밋할 기록 문안은 `_drafts/approval_20260930-b26-before-phase3.md`다(`merge_gate.py parse-approval` 통과).
   앞당기는 이유: Phase 3 M2(어댑터와 소비 함수를 MOD2 `topology_authoring`으로 이동)는 '함수별 AST 해시 동일' 증명이므로 최종형을 이동 전에 만들어 두는 것이 싸다. Phase 4(실패 규약 CC-4)로 미루지 않는 이유도 같다.
2. **범위(결정 아님, 원칙 기본안으로 확정).** v1의 전체 범위(def 13개, base 변이 1,139개)는 기존 생존 면제(기준 약화)나 B26-1 U1의 도구 결정 없이는 V3를 통과할 수 없다. 원칙(기준 약화 없음 + 같은 def는 한 번만 변이)으로 v2 범위를 기본안으로 정했다.
   기각한 대안과 비용:
   * **(v1 (a)) 전체 범위 + base 생존 면제 승인** -- 기각. (i) 기존 test 강도 면제라 **기준 약화 = 사용자 승인**. (ii) base 생존 목록을 만들려면 base에서 같은 def를 **전수** 변이해야 하고 head 전수와 규모가 같다(인벤토리 145~159 def의 변이 약 790개, 수 시간~수십 시간 × 2).
     (iii) 면제 대응 절차가 정의되지 않는다: 사이트를 지우면 뒤 문장의 AST 경로가 밀리고(`body[4]`→`body[3]`), 조건을 없앤 블록은 경로 모양이 바뀌며, 문장 텍스트는 def 안에서 유일하지 않다(`return []`, `return None`). 대응표를 만들 도구가 없다.
     (iv) `refine_…`·`propose_device_roles_gap_fill`은 B26-1도 바꾸므로 순서와 무관하게 V3를 두 번 낸다(약 435 변이).
   * 사용자가 v1 전체 범위를 원하면 B26-1 U1과 한 결정으로 정한다(같은 규칙 적용).
3. **B26-1과의 순서.** v2는 B26-1과 겹치는 def가 없다(B26-1 초안의 V3 대상에 이 card의 def 4개 없음). 두 card는 어느 순서로 병합해도 같은 def를 두 번 변이하지 않는다.
   B26-1 card에 넣을 인계 한 줄(오케스트레이터가 B26-1 card 개정 때 반영): "사이트 9·10·10b·13·14의 도달 불가 부재 분기 삭제와 `propose_device_roles_gap_fill` 3966~3970 `unavailable_reason` 삭제(계약: gate 소자만 없는 입력의 반환에 `unavailable_reason` 키 없음)" -- B34 병합 뒤에만 도달 불가이므로 B26-1은 B34 뒤에 이 줄을 넣는다.
4. **P9와의 관계.** P9 spec 58행과 P9 interface card 60행이 "ImportError면 조용히 None"을 전제로 실행 환경을 설명한다. P9가 먼저 병합되면 영향 없음. B34가 먼저 병합되면 오케스트레이터가 P9 auditor에게 "트리 밖 사본은 조용히 달라지는 대신 `ImportError`"를 알린다(P9는 저장소 트리 복제본에서 실행하므로 판정 불변).

## 작성 전 실측

(측정: gate `master` `7535799`, 저장소 쓰기 없음. scratch `C:/g54` -- `git archive HEAD` 사본 `base`, 그 사본에 위 '코드를 바꾸는 것' 표만 적용한 모의 `head`(SD는 git blob의 LF 원문에서 편집). 게이트 함수는 저장소 `tools/gates`에서 읽기 전용 import(`main` 실행 안 함).
`$PY` = `C:/Python314/python.exe -B`. 측정 뒤 scratch 삭제 -- 수치는 이 절과 `_drafts/b34_revision_log.md`에 옮겨 적었다.)

1. **사실 문장 재측정.**
   * 사이트 줄: v1 측정(cd64170)과 검토 재측정(7535799, `sed -n`·`ast.walk`)이 일치. 사이트 14는 검토 정정대로 `if` 4087, 본문 4088~4109, `else:` 4110, 4111(4112~4113은 주석).
   * `unavailable_reason` 소비처: 읽는 코드 0곳(v1 `git grep`, 검토 확인).
   * `_import_analog_grammar` 호출부: SD 12곳(1072·1088·1312·1444·1713·1893·2258·2399·2494·3380·3528·4070). 저장소의 다른 sys.path 주입(analog-grammar 경로) 0곳, `netclass.py`·`idioms.py`는 `skills/analog-grammar/assets`에만 있다.
   * `install.py` 27~29행 `SKILLS`에 `analog-grammar` 없음.
2. **계약 실측(모의 head, 9회로 × 14 진입점 = 126).** base는 `PYTHONHASHSEED=2`, head는 `=1`로 실행.
   * 계약 1·3: 둘 다 부재 → head **126/126 `ImportError`**, 메시지 `analog-grammar` 126, 탐색 경로 126, `__cause__` `ImportError` 126. base는 0/126(전부 반환, 비-ImportError 예외 0).
   * 계약 2: `idioms`만 → `load_topology` 9/9 `ImportError`(전체 108/126 -- `find_stack_edges`·`geometry_colocation_union`은 idioms를 안 써서 반환, 계약과 모순 없음). `netclass`만 → `find_stack_edges` 9/9(전체 126/126).
   * 계약 4: 모의 head에서 경로를 뺀 뒤 한 번 호출 → `sys.path[0]` = 탐색 경로, 두 번째 호출 뒤에도 1개. `insert(0, …)`의 `0` → `1`/`-1` 변이 둘 다 `sys.path[0]` 조건 실패(죽음).
   * 계약 5·6: base·head 모두 전부 참(`forks(fx) is None` 포함, 계약 6 두 입력 `[]`). 계약 6은 base `audit_theta` 기존 생존 3개(3384 두 개, 3402)를 모의 head에서 죽인다(실측).
   * 계약 7: 정규화 digest base(seed 2) 대 head(seed 1) **126/126 같음**.
   * 계약 8: 복원 뒤 재호출 = 부재 전 값 378/378(3모드 × 126), base·head 모두.
   * 정규화 필요성: 같은 프로세스에서 두 번 부른 raw `==`가 `find_idiom_matches`만 9/9 거짓(`Match`에 `__eq__` 없음), 정규화 뒤 126/126 같음.
   * 부재 상태 `import stick_diagram`(새 프로세스) 성공, 뒤이은 `load_topology` → `ImportError`(메시지에 경로, `__cause__` = `ModuleNotFoundError`).
3. **V3 규모(모의 head).** `mutate_changed.changed_defs(base, head)` → 4개(위 'V3 계획' 표). `mutants` 개수 12·8·6·29 = 55(base 판 같은 def 12·11·9·36 = 68).
   인벤토리 `reachability.build_graph`(HEAD 트리 + 모의 head SD) + `mutate_changed.inventory`: 159·15·66·4. 승인 기록 면제 id와 겹침 0.
   test 모양: 합성 test 파일(test 함수 1개)을 그래프에 넣어 비교 -- 본문 직접 호출이면 각 def 인벤토리 +1(일반적으로 + 닿는 새 test 함수 수), `parametrize` 이름 문자열 + `getattr`이나 모듈 상수 목록 + `getattr`이면 +0.
   변이를 모의 head에서 하나씩 적용해 B34 계약 1~3·5·6·8 판정을 돌렸다(프로세스당 변이 하나): 55개 중 죽음 37, 나머지 18.
   (`find_differential_and_mirror_forks`를 넣은 모의 head도 쟀다: 그 def 47개 중 22 죽음 -- 'V3 계획' 끝의 기각한 확장.)
4. **V3 계획 실측(기존 test).** 나머지 18개를 모의 head 사본에서 도구와 같은 pytest 명령(`-P -m pytest -c tools/gates/pytest_gate.ini --rootdir --confcutdir -x -q -p no:cacheprovider --gmid-phase=2 --gmid-strict=`)으로 인벤토리 기존 test만 돌렸다(기준 실행 통과 확인 뒤):
   죽음 16(`audit_theta` 15/15, `find_stack_edges` 1/1), 생존 2(`_import_analog_grammar` `insert` 상수 ±1 → 계약 4 실측으로 죽음). scratch 사본은 git 이력이 없어 이력 의존 test 2개(`test_ts6_probe_relocate::test_base_blob_reader_reads_the_base_tree`, `test_ts6_probe_relocate::test_moved_tool_matches_base_except_path_lines`)가 기준 실행에서 실패한다(사본 결함 -- 도구는 이력 있는 복제본에서 돈다). 그 두 test를 빼고 돌렸다.
   계약 4 실측: 경로를 뺀 뒤 한 번 호출 → `sys.path[0]` = 탐색 경로, 두 번째 호출 뒤에도 1개(head·base 같은 문장). `insert(1)`/`insert(-1)` 변이는 실패.
5. **이름 충돌.** 새 test `A/tests/contracts/test_b34_grammar_explicit.py`. `grep -rn "glob(" A/tests/`와 대조: `probe_*.py`(ts6) 불일치. `ls A/tests/contracts | grep -i "b34\|grammar"` → 없음.
   `contracts/*.py`를 읽는 `test_ic_markers_match_plan`은 `gmid_ic` 표식만 본다(이 card는 IC를 켜지 않음). `tests/**/*.py` 전수 스캔 test(`test_d_delete_dead`·`test_d_delete_telescopic`·`test_d_move_tests`·`test_ts3_no_print_verdicts`)는 삭제 이름 참조·print 판정 토큰을 본다 -- 해당 없음.
6. **원칙의 계약화.** 조용한 폴백 금지 → 계약 1·2(진입점 14개 × 9회로, 한쪽 부재 포함). 진단 신호(원인) 보존 → 계약 3. gate 소자 없음과 부재의 분리 → 계약 5(gate 소자 없음은 값, 부재는 오류). 동작 보존 → 계약 7·8. 기준 약화 없음 → 계약 4·6(기존 생존을 면제하지 않고 죽이는 계약). 회로 무관(이름을 읽지 않음) → 계약 1이 9회로 전부.
   (v1의 '만들고 배선 안 한 것 제거(`unavailable_reason`)'는 해당 def가 이 card 밖으로 나가 B26-1·백로그로 인계했다.)
7. **쓰기 경로(N3.12.2).**
   * SD 코드·docstring·주석, SR docstring: gmid-code-author(`skills/analog-gmid-design/assets/*.py`).
   * test: gmid-test-author(`A/tests/**`) -- `A/tests/contracts/test_b34_grammar_explicit.py`. 기존 `tests/unit/test_selftest_stick_diagram.py` `test_s120_section` docstring 2714~2717은 판정을 바꾸지 않으므로 고치지 않는다.
     다만 그 docstring의 "analog-grammar 미설치 상황(ImportError 경로)은 … self-test로 하기엔 위험 … 하지 않는다"는 B34 뒤 낡은 서술이 된다(B34 계약 test가 `sys.modules`로 재현한다).
     **백로그 한 줄**(B44, `_drafts/backlog_additions.md`에 추가함 -- 오케스트레이터가 .ai/context.md로 옮긴다): "`test_s120_section` docstring의 analog-grammar 미설치 서술을 B34 계약 test(`test_b34_grammar_explicit.py`) 참조로 고친다 -- 판정 불변, test-author 경로, 다음에 그 파일을 고치는 card에서"(review2 §6).
   * `skills/analog-gmid-design/references/analog-grammar-integration.md`의 폴백 서술 95~97·107·111·118~121·187~188·198·202·440~443행: 오케스트레이터 문서 커밋. 118~121은 "저장소 밖 사본은 조용히 하위호환 경로"를 "`ImportError`"로, 440~443(test 계획 4)은 "부재 시 `ImportError`"로.
   * 레지스트리 360행 `_import_analog_grammar` 설명: 이름 불변이라 필수 아님(code-author가 원하면 '명시적 ImportError' 한 구절).
   * `install.py`: 사용자 경로 -- card 밖, 사용자 작업 1건. analog-grammar(`skills/analog-grammar/**`)는 고치지 않는다(B36).
8. **계획서·설계서 소비자.** `git grep -n "unavailable_reason\|조용히 None\|soft-fail\|analog-grammar가 없으면\|B34" -- docs/01-plan docs/02-design`: `docs/02-design/specs/20260930-p9-kcl-edges.interface.md:60`(생성된 interface card의 `_import_analog_grammar` docstring 인용)과
   P9 spec 58행("ImportError면 조용히 None"에 기댄 실행 환경 설명)이 잡힌다 -- 결정 4의 P9 알림으로 처리하고, 둘 다 P9 산출물이라 이 card에서 고치지 않는다(interface card는 B34 병합 뒤 생성 시 새 docstring을 따른다).
   `docs/03-analysis/…-20-dead-code-dup/d_inventory.json`·`d-dup-summary.md`·`function-audit/agent4_stick_diagram.md`는 과거 측정 기록이라 고치지 않는다.
9. **미배선(V7).** 새 def 0, 지우는 def 0, 되살리는 def 0 → V7 면제 불필요.
10. **기존 계약 test.** 부재를 흉내 내거나 폴백·`unavailable_reason`에 기대는 test 0개. analog-grammar 있음을 전제로 `is not None`을 단언하는 test(`test_selftest_stick_diagram` Test 30·33·35~46·48 계열)는 계약 7과 같은 방향.
    `test_s120_section`은 계약 5와 같다. `test_ic5`는 `audit_theta_root_direction` docstring의 '검사하지 않는 것:' 절과 `영역:` 줄을 본다 -- 절 머리·영역 줄을 남기면 통과. 조정 필요 test 0 → V5 승인 불필요.
