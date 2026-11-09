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
A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`, SR = `A/sizing_recipe.py`. 줄 번호는 gate `master` `2d58fd8` 기준이다(재측정 -- '작성 전 실측' 0. `7535799..2d58fd8` 사이 SD 변경은 P9 `kcl_series_union` 한 def뿐이라 SD 3052행 이후가 −11 밀렸고, 이 card가 다루는 def·문장은 AST가 같다. SR·`install.py`·`references/analog-grammar-integration.md`·`test_selftest_stick_diagram.py` 변경 없음).
**measured at `0f23786`**('작성 전 실측' 00): `2d58fd8..0f23786`에서 SD·SR·`install.py`·references 문서·`tools/`·`test_selftest_stick_diagram.py` 차이 0(SD blob `ca46b5cd` 세 커밋 동일), 이 card의 줄 인용 전부 그 판에서 다시 읽어 같다.

1. **지연 import는 유지한다.** `import stick_diagram`만으로 analog-grammar를 요구하지 않는다(Phase 3 뒤 레이아웃 전용 모듈이 analog-grammar 없이 import되어야 한다 -- 준비 자료 §3.1 (a) 기각 이유).
   `_import_analog_grammar`가 `ImportError`를 삼키지 않고, 필요한 skill 이름(`analog-grammar`)과 찾은 경로를 적은 `ImportError`를 원래 예외에 이어(`from`) 다시 던진다.
   **raise 모양은 고정이다**(V3 변이 수 55의 전제, review2 M2). 지금의 `except ImportError:` 절 하나를 `except ImportError as e:`로 바꾸고, 본문을 `raise ImportError(<메시지>) from e` 한 문장으로 둔다.
   메시지는 `'analog-grammar'`와 `_ag_path`를 담은 문자열 식 하나다(예: f-string 하나). 정수 상수를 더하지 않는다. 모듈·이름마다 raise를 반복하지 않는다. 새 지역 변수·도움 함수를 만들지 않는다.
   이 모양에서 벗어나면 변이 수가 달라진다. 그때 추가로 생기는 변이도 계약 1·3이 죽여야 한다. code-author는 모양을 지키고, auditor는 순서 3 뒤 변이 수를 다시 잰다.
   sys.path 주입 방식(레지스트리 360행 R1)은 바꾸지 않는다(별도 건). 지금의 주입 순서(맨 앞, 멱등)는 계약 4로 고정한다(아래 'V3 계획' -- 기존 test가 못 죽이는 변이를 죽이는 계약).
2. **작은 def 3개의 부재 분기를 지운다**(사이트 2·3, 11·11b). `find_stack_edges`만 운영 도달, 나머지 둘은 비운영이고 V3 인벤토리가 4~66개다.
   이 def들의 기존 생존 변이는 면제하지 않고 죽이는 계약(4·6)을 더한다. 면제 0('V3 계획').
   `find_differential_and_mirror_forks`(사이트 4)는 넣지 않는다: 넣으면 기존 생존 3개 중 1개가 등가 변이라 별도 면제 승인이 필요하다(실측, 'V3 계획' 끝). 도달 불가 분기 1개는 백로그.
3. **운영 경로 큰 def의 부재 분기는 이 card에서 코드를 바꾸지 않는다.** 1번 뒤에는 도달 불가 분기가 된다(부재면 `_import_analog_grammar`가 먼저 `ImportError`). 동작 영향은 없다.
   docstring·주석은 이 card에서 전부 고친다(AST 해시 불변 → V3 비용 0): "부재는 `ImportError`, 이 함수의 `… is None` 분기는 도달 불가 -- 삭제는 B26-1/B35".
   * B26-1(`refine_…`·`propose_device_roles_gap_fill`에 `rails`를 넣는 card)로 인계: 사이트 9·10b·13과 `propose_device_roles_gap_fill` 3955~3959의 `unavailable_reason`(analog-grammar가 **있어도** gate 소자 없는 입력에 "analog-grammar를 import할 수 없어…"를 싣는 틀린 사유, 소비처 0. 키만 지우고 분기는 gate 소자 없는 입력 때문에 남김 -- 백로그 B40).
   * B35(운영 함수에 `rails` 키워드를 넣는 card, 준비 자료 §3.2)로 인계: 사이트 5~8, 그리고 **사이트 10·14**(B26-1 card v4가 B35로 넘김 -- 두 블록은 내어쓰면 V3 N2에서 블록 전체가 새 문장이 되고 기존 test가 블록 출력을 보지 않아, netclass·idioms 출력을 판정하는 B35에서 지운다. B26-1 2차 검토 `review2_b26_1.md` B2·E2·E2b).
   * 백로그로: `find_differential_and_mirror_forks`의 사이트 4(위 2), `propose_theta_kcl_gap_fill`의 사이트 12와 3522~3524 `unavailable_reason`(비운영, 변이 242·기존 생존 추정 약 48 -- 이 card의 목표와 무관한 기존 test 강도 보강을 끌어들이지 않는다).
4. **범위 밖(그대로 둔다):** '입력에 gate 소자가 없음 → `None`/빈 결과'(`_to_analog_grammar_devs`가 `[]`인 경우). `test_s120_section`이 고정한 동작이다(계약 5). docstring은 '부재'와 'gate 소자 없음'을 나눠 적는다.
5. **동작 보존:** analog-grammar가 있으면 E-LIB 9/9와 E-INST가 base와 같다.

이 card는 회로·넷·소자 이름을 읽지 않는다(import 실패 처리와 분기 삭제뿐). 레일 이름 집합(B35)과 analog-grammar 쓰기 경로·게이트 공백(B36)은 범위 밖이다.
`install.py` `SKILLS`에 `"analog-grammar"`를 더하는 것은 사용자 쓰기 경로(N3.12.2 `사용자 | install.py`)라서 이 card에 넣지 않고 **별도 사용자 작업**으로 보고한다.
이 card 뒤에는 그 편집이 없으면 설치본이 조용히 틀리는 대신 명시적으로 실패한다.
이 card의 착수·판정은 그 편집을 기다리지 않는다: test는 저장소 트리(`skills/analog-grammar/assets` 있음)에서 돌고 부재는 `sys.modules`로 흉내 내며, auditor 격리 복제본도 저장소 트리다
('작성 전 실측' 00 -- 설치 모양 사본에서 analog-grammar가 없으면 base는 9/9 회로가 예외 없이 다른 meta를, 모의 head는 9/9 `ImportError`를 내고, 있으면 base·head meta 9/9 같음).

### 사이트 목록(7535799 재측정, 줄은 2d58fd8 기준 -- 실측 0, 전부 SD)

코드를 바꾸는 것(이 card):

| # | 함수 | 줄 | 바꾸는 것 |
|---|---|---|---|
| 1 | `_import_analog_grammar` | 1057~1058 | `except ImportError: return tuple(None …)` → `except ImportError as e:` + 한 문장 `raise ImportError(<'analog-grammar'와 _ag_path를 담은 문자열 식 하나>) from e`(정수 상수·반복 raise·새 지역 변수 없음 -- 범위 1). docstring 1046~1048 |
| 2 | `find_idiom_matches` | 1073~1074 | `if netclass is None: return None` 삭제 |
| 3 | `find_stack_edges` | 1089~1090 | 같음 |
| 11 | `audit_theta_root_direction` | 3370~3371 `if netclass_mod is None or idioms_mod is None: return []` | 삭제 |
| 11b | 같은 함수 | 3376~3377 `if matches is None: return []` | 삭제. 3373 `if not devs` 가드 뒤라 `find_idiom_matches`는 부재에서만 `None`이었다(base에서는 3381이 먼저 잡아 도달 불가) |

코드를 바꾸지 않는 것(도달 불가가 된다 -- docstring만 이 card, 코드 삭제는 인계):

| # | 함수 | 줄 | 인계 |
|---|---|---|---|
| 4 | `find_differential_and_mirror_forks` | 1313~1314 `if netclass is None: return None` | 백로그(등가 변이 면제가 필요해 이 card에서 뺌) |
| 5 | `suggest_vertical_stack_composites` | 1445~1446 | B35 |
| 6 | `find_verified_differential_and_mirror_relations` | 1714~1715 | B35 |
| 7 | `_propose_vertical_stack_ids` | 1894~1895 | B35 |
| 8 | `_propose_headroom_roles` | 2259~2260 | B35 |
| 9 | `refine_differential_and_mirror_relations` | 2400~2401(내부 `classify`의 `return None, None`), 2410~2411 | B26-1 |
| 10 | 같은 함수 | 2494 `_netclass_al, _idioms_al = …`, 2495 `if _netclass_al is not None:`(블록 2496~2523) | **B35**(B26-1 card v4가 넘김 -- 내어쓴 블록 전체가 N2 대상이 되고 기존 test가 블록 출력을 보지 않음) |
| 10b | 같은 함수 | 2440~2441 `if relations is None: return None` | B26-1 |
| 12 | `propose_theta_kcl_gap_fill` | 3518~3520(부재 → `unavailable_reason`), 3527~3529, 3522~3524의 `unavailable_reason` 키 | 백로그 |
| 13 | `propose_device_roles_gap_fill` | 4060~4062 `_static_ref_roles = (…) if _netclass_lcmf is not None else ()` | B26-1 |
| 14 | 같은 함수 | 4076 `if _idioms_lcmf is not None:`(블록 4077~4098), `else:` 4099, `cascoded_active_load_legs = set()` 4100 | **B35**(같은 이유. 블록 뒤 `gain_role_candidates \|= cascoded_active_load_legs`도 함께) |
| -- | 같은 함수 | 3955~3959 `unavailable_reason`(`refined is None`, gate 소자 없음에서도 참 -- 틀린 사유) | B26-1(키만 삭제, 분기는 남김 -- 백로그 B40) |

남기는 것(gate 소자 없음 경로 -- 코드 그대로, docstring만 고친다): `find_idiom_matches` 1076~1077, `find_stack_edges` 1092~1093, `find_differential_and_mirror_forks` 1316~1317,
`suggest_vertical_stack_composites` 1448~1449, `find_verified_…` 1717~1718, `_propose_headroom_roles` 2262~2263, `audit_theta_root_direction` 3373~3374,
전파 사이트 `find_differential_pair_candidates` 1543, `_propose_gm_id_roles` 2092, `_propose_L_roles` 2165·2169, `refine_…` 2420, `propose_vertical_stack_id_gap_fill` 3285, `geometry_colocation_union` 3104.

docstring·주석(코드 AST 불변. 부재 서술을 'ImportError'로, 도달 불가 분기가 남는 함수는 "`… is None` 분기는 도달 불가 -- 삭제는 B26-1/B35/백로그"를 한 구절, gate 소자 없음 서술은 남김):
* SD: 1025~1031 주석 블록, 1046~1048, 1304, 1384, 1533, 1676, 1891~1892, 2070, 2152, 2241, 2349, 3074, 3271, 3356, 3363~3364, 3515~3516, 3921~3922.
  3363~3364는 IC5 '검사하지 않는 것:' 절 안이다 -- 절 머리와 `영역: dc, ac_struct` 줄은 그대로 두고 analog-grammar 문장만 뺀다(`test_ic5` 대상).
* SR `resolve_stack_layout` docstring 6510~6512(4번 "analog-grammar 자체가 없어 candidates도 `None`이면 … 완전한 하위호환". 6509는 3번의 끝 줄이라 그대로): "candidates가 `None`(입력에 gate 소자가 없음)이면 `geometry_colocation_union()`으로 폴백. analog-grammar 부재는 그보다 먼저 `ImportError`"로 고친다. 쓰기 주체 code-author(`A/*.py`), AST 해시 불변.

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
**계약 8의 판정 문장 모양(V4, `0f23786` 실측 추가).** V4 도구(`test_lint.py` (1))는 판정 문장 두 쪽에 **같은 진입점·같은 인자** 호출이 (지역 대입을 풀어) 들어 있으면 '기대값을 피검 호출로 만듦'으로 FAIL을 낸다.
계약 8을 `before = stick_diagram.f(ts)` … `after = stick_diagram.f(ts)`; `assert norm(after) == norm(before)`로 쓰면 V4 FAIL이다(합성 test 실측 -- `_drafts/b34_kit/out/v4probe_abc.txt`).
그래서 계약 8의 부재 전·복원 뒤 값은 진입점을 부르고 정규화하는 `_b34_` helper(예: `_b34_snapshot(ts)`)로 얻고 판정 문장은 그 결과끼리 비교한다(실측 V4 PASS -- `v4probe_de.txt`).
이 비교는 상태 변화(부재 → 복원) 전후의 같은 호출이 같은지를 보는 계약 자체이고 기대값을 피검 출력에서 '만든' 것이 아니다 -- auditor는 V4 basis의 `oracle 대조:` 줄에 이 사정을 적는다.

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
4. **탐색 경로는 맨 앞에 한 번(analog-grammar 있음). -- 생략 불가(review2 S2. 현행 V3 규칙에서는 V3 필수, N2에서는 대상 밖이지만 동작 고정 계약으로 유지 -- 'V3 계획').** 위 탐색 경로를 `sys.path`에서 뺀 상태(`monkeypatch.setattr(sys, "path", [x for x in sys.path if norm(x) != E])`)에서
   `stick_diagram.find_stack_edges(ts)`를 한 번 부르면 `norm(sys.path[0]) == E`이고, 한 번 더 불러도 `sys.path`에서 `norm(x) == E`인 항목이 정확히 한 개다(`norm`·`E`는 계약 3과 같다).
   (근거: analog-grammar 자신의 `netclass`·`idioms`가 같은 이름의 다른 모듈보다 먼저 잡혀야 한다. 지금 동작 그대로다.)
   이 계약만 죽이는 변이가 있다: `_import_analog_grammar:const+:body[3].body[0].value.args[0]`·`const-:…args[0]`(`insert(0, …)`의 `0` → `1`/`-1`)와 `_import_analog_grammar:stmt_delete:body[3]`(`if … not in sys.path` 블록 삭제).
   기존 test는 앞의 둘을 못 죽인다(실측). 현행 규칙에서는 이 계약을 빼면 V3 FAIL이다.
5. **gate 소자 없음 경로는 그대로(analog-grammar 있음).** `fx = [Transistor("Ma", "pmos", source="vdd", drain="n1"), Transistor("Mb", "nmos", source="gnd", drain="n1")]`(gate 없음)에 대해
   `find_idiom_matches(fx) is None`, `find_stack_edges(fx) is None`, `find_differential_and_mirror_forks(fx) is None`, `refine_differential_and_mirror_relations(fx) is None`, `audit_theta_root_direction(fx, None) == []`.
   부재 상태에서 `import stick_diagram`(새 프로세스, `sys.modules`에 두 이름을 `None`으로 둔 뒤)이 성공한다(모듈 최상위 import 아님).
6. **θ가 있어도 발견 없음인 두 입력(analog-grammar 있음). -- 생략 불가(review2 S2. 현행 V3 규칙에서는 V3 필수, N2에서는 이 세 변이가 대상 밖이지만 유지 -- 'V3 계획').** 기존 test가 못 죽이는 `audit_theta_root_direction` 변이 3개를 이 계약만 죽인다(실측):
   `audit_theta_root_direction:stmt_delete:body[3]`(`if not devs` 삭제), `…:stmt_delete:body[3].body[0]`(그 `return []` 삭제), `…:stmt_delete:body[6].body[5].orelse[0]`(A_signed 분기 `others = …` 삭제). 현행 규칙에서는 이 계약을 빼면 V3 FAIL이다.
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
  정규화 값을 문자열·해시로 바꿔 비교하려면 dict 키도 정렬해야 한다: `refine_differential_and_mirror_relations` 반환의 `vertical_stack_id_candidates["groups"]` 키 순서가 `PYTHONHASHSEED`마다 다르다(`2d58fd8` 실측 -- 키 순서를 두면 seed 1 대 2가 118/126, 정렬하면 126/126).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(새 심볼 없음. 지우는 def 없음. 바뀌는 것은 def 4개의 본문.)

## 판정 유형 근거

red-green. base(`7535799` 사본, 실측)에서 부재를 만들면 계약 1의 진입점 14개가 9/9 회로 전부 **예외 없이 반환한다**(126/126, `idioms`만 126/126, `netclass`만 126/126) --
`load_topology`·`run_topology_pipeline`·`audit_theta_root_direction`·`geometry_colocation_union`·`propose_vertical_stack_id_gap_fill`은 값을, 어댑터 7개는 `None`을, 두 제안 함수는 `unavailable_reason`이 든 dict를 준다.
`2d58fd8`·`8356c1e`(SD 같음) 재측정도 같다: 둘 다 부재·`idioms`만·`netclass`만 세 경우 모두 126/126 조용히 반환, 다른 예외 0.
그래서 base에서 `pytest.raises(ImportError)`가 'DID NOT RAISE'(`Failed`)로 실패한다. 계약 2·3은 같은 이유로 red다.
**red는 전부 단언형(`Failed`/`AssertionError`)이다** -- base에서 부재 시 다른 예외가 나는 진입점은 0개다(실측 OtherError 0).
test 쪽 안전장치(권고): 진입점 호출을 `try` / `except ImportError` / `except Exception as e: pytest.fail(...)` / `else: pytest.fail("조용히 반환")` 모양으로 쓰면 base가 어떤 비-ImportError를 내도 red가 단언형으로 남는다.
**이 `try`는 예외 객체를 돌려주는 `_b34_` helper 안에 두고, 메시지·경로·`__cause__` `assert`는 test 함수 본문의 `try` 밖에 쓴다**(`0f23786` 실측: `assert`를 `except` 절 안에만 두면 V4 도구 `test_lint.py` (3) 'assert가 if·try 안에만 있음'이 FAIL. helper 모양과 `with pytest.raises(ImportError) as ei:` 뒤 `assert` 모양은 PASS -- `_drafts/b34_kit/out/v4probe_fgh.txt`).
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

**판정 규칙.** B34는 V3 범위 card `20260930-v3-changed-stmt-scope`(사용자 결정 A1-b ② N2 + A1-b 정정 '넓힌 T6') 병합 **뒤**에 돈다(순서 P10 → P10b → Phase 2 DoD → V3 binding → V3 scope → B34). 그래서 V3 대상은 N2다.
범위 card가 늦어져 현행 규칙(AST 해시가 바뀐 def의 변이 전체)으로 돌아도 통과하도록 두 규칙을 모두 쟀다. V3 binding card(`20260930-v3-exempt-binding`, 면제 = 변이 id@묶기 해시)는 이 card에 영향이 없다(면제 0).
이 card는 def **4개**만 바꾼다(docstring·주석 수정은 해시 불변 -- 모의 head에서 `changed_defs` = 4 확인). 모의 head = gate `master` `2d58fd8` + 위 '코드를 바꾸는 것' 표(scratch) 실측('작성 전 실측' 0):

| def | 변이(현행 = def 전체) | N2 대상(N2b / 넓힌 T6로 추가) | 인벤토리(기존) | 새 test 포함 시(기존 + k) |
|---|---|---|---|---|
| `_import_analog_grammar` | 12 | 3 / +0 | 159 | 159 + k |
| `find_idiom_matches` | 8 | 2 / +0 | 15 | 15 + k |
| `find_stack_edges` | 6 | 2 / +0 | 66 | 66 + k |
| `audit_theta_root_direction` | 29 | 3 / +0 | 4 | 4 + k |
| 합 | **55** | **10** | | |

**N2 대상 10개와 죽이는 것**(변이마다 새 프로세스, 모의 head 실측. 'B34 계약' = 계약 1~6·8 판정, '기존 test' = 도구와 같은 pytest 명령으로 인벤토리 기존 test만):

| 변이 id(`stick_diagram:<def>:` 뒤) | 무엇 | B34 계약 | 기존 test |
|---|---|---|---|
| `_import_analog_grammar:stmt_delete:body[4]` | `try` 전체 삭제(`None` 반환) | 계약 8(부재 전 값 단계에서 예외) | 죽음 |
| `_import_analog_grammar:except_body_delete:body[4].handlers[0]` | 새 `raise` 삭제(부재 시 `None` 반환) | **계약 1·2·3만** | **생존** |
| `_import_analog_grammar:early_return:body[1]` | 첫 문장 앞 `return` | 계약 8 | 죽음 |
| `find_idiom_matches:stmt_delete:body[2]` | 지운 사이트 바로 뒤 `devs = …`(T6) | 계약 5·6 | 죽음 |
| `find_idiom_matches:early_return:body[1]` | | 계약 1·3·6 | 죽음 |
| `find_stack_edges:stmt_delete:body[2]` | 지운 사이트 바로 뒤 `devs = …`(T6) | 계약 4·5 | 죽음 |
| `find_stack_edges:early_return:body[1]` | | 계약 1·2·3·4 | 죽음 |
| `audit_theta_root_direction:stmt_delete:body[2]` | 지운 사이트 11 바로 뒤 `devs = …`(T6) | 계약 5·6 | 죽음 |
| `audit_theta_root_direction:stmt_delete:body[5]` | 지운 사이트 11b 바로 뒤 `findings = []`(T6) | 계약 6 | 죽음 |
| `audit_theta_root_direction:early_return:body[1]` | | 계약 1·3·5·6 | 죽음 |

* **N2에서 V3 필수 계약은 1·2·3이다**(새 `raise`를 지운 변이를 기존 test가 못 죽인다 -- 부재를 흉내 내는 기존 test가 없다).
* **현행 규칙(55개)**: B34 계약으로 39(계약 4가 `insert(0, …)` 상수 ±1 둘), 나머지 16(`find_stack_edges` 1, `audit_theta_root_direction` 15)은 기존 test로 죽는다(v2 측정 -- 4 def와 변이 id 목록이 `7535799`와 `2d58fd8`에서 같다, '작성 전 실측' 0). 55/55, 면제 0.
* 계약 4·6이 혼자 죽이는 변이(`_import_analog_grammar:const±:body[3].body[0].value.args[0]`, `audit_theta_root_direction:stmt_delete:body[3]`·`…body[3].body[0]`·`…body[6].body[5].orelse[0]`)는 **N2 대상 밖**이다(바뀐 문장·감싸는 제어문·삭제 지점 바로 뒤·같은 블록 뒤쪽 이름 사용 어디에도 들지 않는다).
  그래도 두 계약은 남긴다: 지금 동작(주입 순서, gate 소자 없음·`terms` 빈 θ의 빈 결과)을 고정하는 계약이고 비용이 작으며, 범위 card가 늦어 현행 규칙으로 돌면 V3 필수다. 빼는 것은 판정 강도를 줄이는 쪽이라 원칙상 기본안이 아니다.
* k = 그 def에 (본문 직접 호출로) 닿는 새 test 함수 수(review2 M3. v2의 '+1'은 새 test 함수가 1개라는 전제였다). reviewer 재현 test(함수 7개)에서는 166·19·72·8이었다.
* **auditor 인벤토리 확인(순서 3 freeze 뒤, review2 S1).** 새 test 파일을 넣은 그래프에서 4 def 인벤토리가 159·15·66·4 + k인지 본다(k ≤ 새 test 함수 수).
  이를 넘으면(실측 예: 237·236·234·234) 새 test의 def 이름이 다른 파일의 이름과 이어진 것이다('test 모양'의 이름 규칙 위반). V3를 돌리기 전에 test-author에게 이름 정정을 돌려보낸다.
* 방법: 모의 head에서 변이를 하나씩 적용(`mutate_changed.mutants`·`_replace_def`)해 (1) B34 계약 판정을 변이마다 새 프로세스에서 돌리고, (2) 기존 test 판정은 도구와 같은 pytest 명령으로 인벤토리의 기존 test만 돌렸다('작성 전 실측' 0·3·4).
* base에서 `audit_theta_root_direction`의 기존 생존 7개(검토 표본) 중 4개는 이 card가 지우는 문장(3370·3371·3376·3377)이고, 남는 3개(3373 `if not devs` 문장 삭제·`return` 삭제, 3391 `others = …` 삭제)는 **계약 6이 죽인다**(모의 head 실측. 셋 다 N2 대상 밖).
* 면제 없음(기존 생존 면제·등가 변이 면제 모두 0, N2·현행 두 규칙 모두). V3 기준 약화 승인 불필요. `2d58fd8` 승인 기록 decision id 27개와 이 card 변이 id 겹침 0(measured at `0f23786`: `_approved_ids` 원소 36개, 겹침 0 -- 원소 수는 기록이 더해질 때마다 바뀌므로 판단 기준은 '겹침 0'이다).
* 도구 동작 참고: 인벤토리 기준 실행이 실패하면 ERROR(B28). 새 test 파일은 test-author가 쓰므로 순서 3 freeze 뒤 auditor가 base·head 인벤토리 기준 실행을 확인한다.
  (scratch 사본은 git 이력이 없어 이력 의존 test 2개가 기준 실행에서 실패했다: `test_ts6_probe_relocate::test_base_blob_reader_reads_the_base_tree`와 `test_ts6_probe_relocate::test_moved_tool_matches_base_except_path_lines`(둘째는 review2 실측).
  사본 결함이다. 도구는 이력 있는 복제본에서 돌므로 해당 없다. 이 측정에서는 그 두 test를 빼고 돌렸다.)
* 기각한 확장(검토 권고안의 `find_differential_and_mirror_forks` 포함): 변이 47개 추가(인벤토리 10). B34 계약으로 22, 기존 test로 22 죽고 3개 생존 -- kind 검사 `if`·`continue` 삭제 2개는 계약("kind가 다른 두 소자는 fork 짝이 되지 않는다", 예 `Mp` pmos·`Mn` nmos가 `vdd`에 닿고 gate 공유)으로 죽일 수 있으나(실측),
  `stick_diagram:find_differential_and_mirror_forks:const-:body[8].body[2].value.generators[0].ifs[0].comparators[0]`(`len(members) >= 2` → `>= 1`)은 **등가 변이**다(구성원 하나인 fork는 쌍이 없음). 이 card에 넣으면 등가 변이 면제 decision 기록이 하나 더 필요하다(A2 기록 `20260930-b26-before-phase3`의 target에는 없다). 비운영 def의 도달 불가 분기 1개를 지우려고 승인을 늘리지 않는다 -- 백로그.

## 결정 필요 항목

1. **앞당김 -- 승인됨.** B34는 N6.1 Phase 2 범위 행에 없는 백로그 항목이고, 부재 시 반환이 `ImportError`로 바뀌는 **동작 변경**이다. design 20 승인(`20260923-20-dead-code-dup-design`)은 "동작이 바뀌는 수정"을 덮지 않는다(검토 B1).
   그래서 `approval`은 사용자가 승인한 A2 decision 기록 **`20260930-b26-before-phase3`**(DEC-60 넷 전환기 종료 + DF-19·DF-26 넷 몫 분리 + B26-1·B34의 Phase 3 전 착수를 한 기록으로 덮음, 사용자 원문 "승인 (Recommended)")를 가리킨다.
   **그 기록은 gate에 있다**: `.ai/approvals/20260930-b26-before-phase3.md`(커밋 `2d58fd8`). 이 card는 V3·V7 면제가 필요 없으므로 그 기록의 `target`(`U2-B26-BEFORE-PHASE3`, 결정 이름)에 변이 id를 더할 필요가 없다.
   **커밋된 기록이 review2 B1 조건을 채운다(2d58fd8 원문 대조).**
   * `scope:` 줄이 이 card id `20260930-b34-grammar-explicit`과 동작 변경("analog-grammar 부재 시 조용한 폴백 -> ImportError 동작 변경")을 적는다.
   * '덮는 것' ③ B34 항목이 card id, **동작 변경**(조용한 `None`·`[]`·`unavailable_reason` dict → skill 이름 `analog-grammar`와 탐색 경로를 적고 원래 예외를 `__cause__`로 이은 `ImportError`), **def 4개**(`_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`)를 이름으로 적는다.
     운영 경로 큰 def의 도달 불가 분기 코드 삭제를 B26-1·B35로 넘기는 순서와 docstring·`references/analog-grammar-integration.md` 정정도 덮는다(사이트 10·14를 B26-1에서 B35로 옮긴 것은 'B26-1·B35로 넘김' 안이라 기록 문구와 어긋나지 않는다).
   * '덮지 않는 것'이 V3·V7 면제 일체를 빼고 "B34는 V3 면제가 없다"를 적는다(이 card의 '면제 0'과 같다). `install.py` `SKILLS` 편집은 별도 사용자 작업으로 적는다(이 card의 범위 밖과 같다).
   * 사용자 원문 절이 실제로 물은 A2 질문을 인용하고, 그 ③이 "B26-1(…)과 B34(analog-grammar가 없으면 조용히 폴백하던 것을 명시적 오류로 바꿈)를 Phase 3 모듈 분할보다 먼저 합니다"다. 답은 "승인 (Recommended)".
   * 머리: `id: 20260930-b26-before-phase3`, `target_kind: decision`, `date: 2026-10-01`(`merge_gate.parse_approval_header` 통과 -- '작성 전 실측' 0).
   * '재검토' 절: B34가 병합되지 않은 채 Phase 3 M 카드가 `stick_diagram`을 나누기 시작하면 앞당김이 효력을 잃는다 -- 이 card는 Phase 3 M 카드보다 먼저 병합되어야 한다(순서는 `_drafts/user_decisions.md`: P10 → P10b → Phase 2 DoD → V3 binding → V3 scope → **B34** → B26-1 → B33).
   앞당기는 이유: Phase 3 M2(어댑터와 소비 함수를 MOD2 `topology_authoring`으로 이동)는 '함수별 AST 해시 동일' 증명이므로 최종형을 이동 전에 만들어 두는 것이 싸다. Phase 4(실패 규약 CC-4)로 미루지 않는 이유도 같다.
2. **범위(결정 아님, 원칙 기본안으로 확정).** v1의 전체 범위(def 13개, base 변이 1,139개)는 기존 생존 면제(기준 약화)나 B26-1 U1의 도구 결정 없이는 V3를 통과할 수 없다. 원칙(기준 약화 없음 + 같은 def는 한 번만 변이)으로 v2 범위를 기본안으로 정했다.
   기각한 대안과 비용:
   * **(v1 (a)) 전체 범위 + base 생존 면제 승인** -- 기각. (i) 기존 test 강도 면제라 **기준 약화 = 사용자 승인**. (ii) base 생존 목록을 만들려면 base에서 같은 def를 **전수** 변이해야 하고 head 전수와 규모가 같다(인벤토리 145~159 def의 변이 약 790개, 수 시간~수십 시간 × 2).
     (iii) 면제 대응 절차가 정의되지 않는다: 사이트를 지우면 뒤 문장의 AST 경로가 밀리고(`body[4]`→`body[3]`), 조건을 없앤 블록은 경로 모양이 바뀌며, 문장 텍스트는 def 안에서 유일하지 않다(`return []`, `return None`). 대응표를 만들 도구가 없다.
     (iv) `refine_…`·`propose_device_roles_gap_fill`은 B26-1도 바꾸므로 순서와 무관하게 V3를 두 번 낸다(약 435 변이).
   * 사용자가 v1 전체 범위를 원하면 B26-1 U1과 한 결정으로 정한다(같은 규칙 적용).
3. **B26-1·B35와의 순서.** 이 card는 B26-1과 겹치는 def가 없다(B26-1 card의 V3 대상에 이 card의 def 4개 없음 -- B26-1 v4 모의 측정에서도 겹침 0). 두 card는 같은 def를 두 번 변이하지 않는다. 병합 순서는 B34 → B26-1이다(B26-1 착수 조건이 B34 병합).
   인계(B26-1 card v4 반영 상태): B26-1은 사이트 9·10b·13의 도달 불가 부재 분기 삭제와 `propose_device_roles_gap_fill` 3955~3959 `unavailable_reason` 키 삭제(분기는 남김, 백로그 B40)를 맡는다.
   **사이트 10·14는 B35로 넘어갔다**(B26-1 2차 검토 `review2_b26_1.md` B2·E2·E2b: 두 블록을 내어쓰면 V3 N2에서 블록 전체가 새 문장이 되고 기존 test가 블록 출력을 보지 않아 생존 13+1개를 들여온다. netclass·idioms 출력을 판정하는 B35가 지운다).
   그래서 B35 인계 목록은 사이트 5~8·10·14다. B35 card 작성 때 오케스트레이터가 이 목록을 옮긴다. 두 블록은 B34 병합 뒤 도달 불가로 남고 docstring·주석은 이 card에서 고친다(동작 영향 없음).
4. **P9와의 관계.** P9(`20260930-p9-kcl-edges`)는 gate에 병합되었다(`93b18db`, 판정 기록 `766b5c2`). 그래서 이 card는 P9 판정에 영향이 없다.
   P9 spec 58행과 P9 interface card 60행의 "ImportError면 조용히 None" 서술, P9 판정 기록 스크립트 `.ai/verification/20260930-p9-kcl-edges/scripts/diff_dup.py` 17~20행(`_import_analog_grammar` 반환을 `is None`으로 검사해 `sys.exit`)은 과거 산출물이라 고치지 않는다.
   analog-grammar가 있으면 그 스크립트의 동작은 같고, 없으면 `sys.exit` 메시지 대신 `ImportError`로 끝난다(둘 다 비정상 종료).

5. **card `phase` 값 -- 미결(사용자 질문 Q-B34-PHASE = Phase 3 승인 질문 A2-③).** 이 초안은 승인 기록 '덮는 것' ③ 문장대로 `phase: 2`다. 순서 결정(Phase 2 DoD 뒤 병합)과 계획 1001행
   ("먼저 병합하는 card의 spec card `phase` 값은 병합 시점의 진행 Phase다")이 어긋나 답을 기다린다. 게이트는 card `phase`를 진행 Phase와 대조하지 않는다(`merge_gate.rule10_phase` 532~549행,
   `strict_set` 1042행, `v1_command_check` 1009~1010행 -- '작성 전 실측' 00). 답이 '`phase: 3`'이면 바뀌는 것은 머리 두 줄(`phase: 3`, 새 decision 기록 id의 `approval:` 줄 추가)과
   auditor 명령의 `--gmid-phase=3`뿐이고 계약·oracle·V3 대상은 같다. 답이 'Phase 2 DoD 앞으로'면 이 card는 지금 머리 그대로이고 Phase 2 DoD의 N6.3 목록(`^phase: 2$` card)에 든다.

## 작성 전 실측

00. **재확인(2026-10-01, gate `master` `0f23786`, scratch `C:/g123` -- 격리 복제본, 측정 뒤 삭제. 스크립트·출력 `_drafts/b34_kit/`).**
   * **줄 인용**: 이 card의 SD 줄(사이트·인계·남기는 것·docstring·호출부 12곳·3391·def 위치 3330·3834·8539), SR 7952·6510~6512, `install.py` 27~29, `test_selftest_stick_diagram.py` 2714~2717,
     레지스트리 360, P9 spec 58·interface 60, `diff_dup.py` 17~20을 그 판에서 다시 읽어 모두 같다(`b34_kit/out/sd_lines.txt`). references 문서만 줄 범위를 고쳤다('작성 전 실측' 7).
   * **V3(독립 모의 head = `0f23786` + 사이트 1·2·3·11·11b, `b34_kit/mk_head.py` -- 이전 측정 스크립트를 쓰지 않고 이 card 표에서 새로 작성)**: `changed_defs` 4, 변이 12·8·6·29 = 55,
     인벤토리 159·15·66·4, N2(범위 card 계약 1 독립 프로토타입 `v3scope_kit/scope_proto.py`) N2b 10 = N2w(넓힌 T6) 10 -- id 목록이 'V3 계획' 표의 10개와 같고 이전 키트 측정
     (`v3scope_kit/out/ids_b34_narrow.json`)과 55·10·10 모두 같다. 계약 4·6만 죽이는 변이 6개는 55 안·N2 밖. 승인 원소 36개와 겹침 0(`b34_kit/out/measure_b34.txt`).
     지금 gate 도구(`mutate_changed.py`, 범위 card 미병합)를 가짜 pytest로 돌린 선택 probe: 대상 55, `not_targeted` 0, 순서 = 'V3 계획' 순서(`b34_kit/out/probe_cur_all.txt`).
   * **문서 시퀀스 모의**(`b34_kit/sim_b34.py`, 격리 복제본 + 가짜 bare gate(pre-receive = old 판 `merge_gate receive`, 무결성 대조만 뺌)): spec card `parse_spec_card` 통과(phase 2, red-green, no,
     approval 1, 절 12), interface card 기존 함수 14개 전부 `stick_diagram`, references 패치 pending 5 → 적용 → 재실행 멱등, `test_phase2_stale_refs` 18 passed, push 통과(accept-log 줄),
     트레일러 없는 커밋 거부. `phase: 3` 변형(모의 decision 기록 + `approval:` 2줄)도 같은 결과. 사용자 `install.py` 커밋(`Role: user` + staged_diff 승인 기록)은 통과, 승인 기록 없이는 거부.
   * **phase 판정 지점**(병합된 phase 2 기록 `20260930-dup-w-calc` 재료): `rule10_phase` phase 2·3 모두 통과(V8 `도입 4`·V9 `도입 6b` N/A가 둘 다 유효), `strict_set` 둘 다 빈 집합,
     `v1_command_check`만 `--gmid-phase=<card phase>` 토큰을 요구한다.
   * **설치 모양 사본**(`b34_kit/install_probe.py`, `skills/<이름>`만 있는 디렉터리 -- `~/.claude/skills`와 같은 상대 위치): analog-grammar 없음 → base 9/9 예외 없이 반환하나 meta가 9/9 다름
     (`_device_roles_gap_fill_review_needed` 0·28·4·5·12·1·1·9·2 → 전부 0), 모의 head 9/9 `ImportError`(메시지에 탐색 경로, `__cause__` `ModuleNotFoundError`); 있음 → base·head meta 9/9 같음.
     사용자 전역 설치(`~/.claude/skills`)에는 지금 `analog-gmid-design`·`analog-grammar` 둘 다 없다(설치본이 이 card 병합으로 바로 깨지지 않는다 -- 다음 `install.py` 실행 전에 편집이 필요).

(1~10은 v2 측정: gate `master` `7535799`, 저장소 쓰기 없음. scratch `C:/g54` -- `git archive HEAD` 사본 `base`, 그 사본에 위 '코드를 바꾸는 것' 표만 적용한 모의 `head`(SD는 git blob의 LF 원문에서 편집). 게이트 함수는 저장소 `tools/gates`에서 읽기 전용 import(`main` 실행 안 함).
`$PY` = `C:/Python314/python.exe -B`. 측정 뒤 scratch 삭제 -- 수치는 이 절과 `_drafts/b34_revision_log.md`에 옮겨 적었다. 줄 번호는 0의 대응으로 `2d58fd8` 기준으로 바꿔 적었다 -- 대상 def·문장의 AST가 같아 수치는 그대로 유효하다.)

0. **최종 재측정(2026-10-01, gate `master` `2d58fd8`, 작업 중 `8356c1e`로 움직여 다시 확인).** scratch `C:/g84`(`git archive` 사본, 측정 뒤 삭제). 게이트 함수(`mutate_changed.changed_defs`·`mutants`·`_replace_def`·`inventory`·`def_hash`,
   `reachability.build_graph`·`iter_defs`·`_approved_ids`, `interface_card.build`·`engine_defs`, `role_paths.parse_spec_card`, `merge_gate.parse_approval_header`)와 `_drafts/v3_scripts`의 분류기(`v3_scope_classify.classify`·`build_b34`, `v3_scope_widen.classify_w`)만 읽기 전용 import, 도구 `main` 미실행.
   * **줄 대응.** `7535799..2d58fd8`의 SD 변경은 P9(`kcl_series_union`) 두 덩어리(옛 3020~3035 −6, 3038~3051 −11)뿐이다. 이 card가 적은 SD 줄 103개를 `difflib` 대응으로 옮겼다: card 줄은 3020행 미만(그대로)과 3052행 이후(전부 −11)에만 있다(문장 텍스트 일치 확인).
     `8356c1e`의 SD는 `2d58fd8`과 바이트 같다. SR 7952·6509~6512, `install.py` 27~29, `test_selftest_stick_diagram.py` 2714~2717, references 문서, 레지스트리 360행은 바뀌지 않았다.
   * **def 동일성.** 4 def를 포함한 진입점·인계 def 15개 모두 `def_hash`와 전체 `ast.dump`가 `7535799`과 같다(`audit_theta_root_direction` 3341 → 3330, `propose_device_roles_gap_fill` 3845 → 3834, `load_topology` 8550 → 8539 등 위치만 이동).
   * **V3(모의 head = `2d58fd8` + 사이트 1·2·3·11·11b).** `changed_defs` = 4, 변이 12·8·6·29 = 55, 변이 id 목록이 `7535799` 모의 head와 **같다**. 인벤토리 159·15·66·4(`2d58fd8`·`8356c1e` 둘 다 -- P9·P10 새 test는 이 4 def에 닿지 않는다).
     N2 분류(`v3_scope_classify.classify` = N2b, `v3_scope_widen.classify_w` = 넓힌 T6): 3·2·2·3 = **10**, 넓힌 T6 추가 0. 승인 decision id 27개와 겹침 0.
   * **계약(모의 head, 판정 스크립트).** 계약 1·3 126/126, 계약 2 `idioms`만 `load_topology` 9/9·`netclass`만 `find_stack_edges` 9/9, 계약 4·5·6 참, 계약 8 복원 = 부재 전(3모드). base(`8356c1e`) red: 세 부재 모드 각 126/126 조용히 반환, 다른 예외 0.
     계약 7: base 대 head 126/126 같음(같은 seed, 다른 seed 모두 -- dict 키 정렬 정규화).
   * **변이 판정.** 55개 전부 B34 계약 판정(변이마다 새 프로세스): 죽음 39, 나머지 16(`find_stack_edges` 1, `audit_theta_root_direction` 15 -- v2의 기존 test 몫과 같은 목록). N2 대상 10개는 B34 계약으로 10/10, 기존 test(기준 실행 통과 뒤, ts6 이력 test 2개 제외)로 9/10 -- `except_body_delete` 하나만 기존 test 생존('V3 계획' 표).
   * **interface card(모의 생성, `8356c1e` 사본 루트).** 기존 함수 14개 전부 `stick_diagram`, 계약 1의 진입점 14개와 정확히 같다. 계약 절 백틱 토큰 중 엔진 def와 이름이 겹치는 것은 이 14개와 `reachability.build_graph`(모듈 힌트가 엔진 밖이라 표에 안 실림)뿐이다.
   * **이름 충돌.** `8356c1e`의 `tests/contracts`에 `b34`·`grammar` 파일 없음, `_b34_`·`test_b34_` 이름 0개. 새 `glob` 사용처(`test_df23_inventory` library, `test_phase2_stale_refs` references `*.md`)는 새 test 파일 이름과 무관.
   * **승인 기록.** `.ai/approvals/20260930-b26-before-phase3.md`(`2d58fd8`) `parse_approval_header` 통과: `target_kind` decision, `target` `U2-B26-BEFORE-PHASE3`, `scope`에 이 card id와 동작 변경. '덮는 것' ③ B34에 def 4개 이름(결정 1).
   * **소비자 추가 발견.** P9 판정 기록 스크립트 `diff_dup.py` 17~20행이 `_import_analog_grammar`의 `None`을 검사한다(결정 4 -- 고치지 않음). 저장소의 analog-grammar sys.path 주입은 여전히 SD 한 곳(`analyze.py`의 자기 폴더 주입은 analog-grammar 내부).

1. **사실 문장 재측정.**
   * 사이트 줄: v1 측정(cd64170)과 검토 재측정(7535799, `sed -n`·`ast.walk`)이 일치했고, `2d58fd8`에서 줄 대응으로 다시 확인했다(0). 사이트 14는 `if` 4076, 본문 4077~4098, `else:` 4099, 4100(4101~4102는 주석).
   * `unavailable_reason` 소비처: 읽는 코드 0곳(v1 `git grep`, 검토 확인).
   * `_import_analog_grammar` 호출부: SD 12곳(1072·1088·1312·1444·1713·1893·2258·2399·2494·3369·3517·4059). 저장소의 다른 sys.path 주입(analog-grammar 경로) 0곳, `netclass.py`·`idioms.py`는 `skills/analog-grammar/assets`에만 있다.
   * `install.py` 27~29행 `SKILLS`에 `analog-grammar` 없음.
2. **계약 실측(모의 head, 9회로 × 14 진입점 = 126).** base는 `PYTHONHASHSEED=2`, head는 `=1`로 실행.
   * 계약 1·3: 둘 다 부재 → head **126/126 `ImportError`**, 메시지 `analog-grammar` 126, 탐색 경로 126, `__cause__` `ImportError` 126. base는 0/126(전부 반환, 비-ImportError 예외 0).
   * 계약 2: `idioms`만 → `load_topology` 9/9 `ImportError`(전체 108/126 -- `find_stack_edges`·`geometry_colocation_union`은 idioms를 안 써서 반환, 계약과 모순 없음). `netclass`만 → `find_stack_edges` 9/9(전체 126/126).
   * 계약 4: 모의 head에서 경로를 뺀 뒤 한 번 호출 → `sys.path[0]` = 탐색 경로, 두 번째 호출 뒤에도 1개. `insert(0, …)`의 `0` → `1`/`-1` 변이 둘 다 `sys.path[0]` 조건 실패(죽음).
   * 계약 5·6: base·head 모두 전부 참(`forks(fx) is None` 포함, 계약 6 두 입력 `[]`). 계약 6은 base `audit_theta` 기존 생존 3개(3373 두 개, 3391)를 모의 head에서 죽인다(실측).
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
   * `skills/analog-gmid-design/references/analog-grammar-integration.md`의 폴백 서술 95~98·106~107·118~119·186~188·197~198·440~443행(`0f23786` 재측정 -- 옛 '107·111·118~121·187~188·198·202'에서 111·202는 `if not devs: return None`(gate 소자 없음 경로, 범위 4)이라 **남기고**, 120~121은 빈 줄·절 머리라 뺐다): 오케스트레이터 문서 커밋.
     118~119는 "저장소 밖 사본은 조용히 하위호환 경로"를 "`ImportError`"로, 440~443(test 계획 4)은 "부재 시 `ImportError`"로. 문안 초안과 멱등 패치: `_drafts/b34_kit/patch_b34_refs.py`(앵커 5개, `--check` → pending 5).
   * 레지스트리 360행 `_import_analog_grammar` 설명: 이름 불변이라 필수 아님(code-author가 원하면 '명시적 ImportError' 한 구절).
   * references 문서를 고친 뒤 `tests/contracts/test_phase2_stale_refs.py`(P10 계약 5, `8356c1e`에 들어옴 -- `references/**/*.md` 줄마다 Phase 2 삭제·이동 이름 표시 검사)를 돌린다. 이 card의 문구는 그 이름 집합을 쓰지 않으므로 영향 없음이 기본값이다.
   * `install.py`: 사용자 경로 -- card 밖, 사용자 작업 1건. analog-grammar(`skills/analog-grammar/**`)는 고치지 않는다(B36).
8. **계획서·설계서 소비자.** `git grep -n "unavailable_reason\|조용히 None\|soft-fail\|analog-grammar가 없으면\|B34" -- docs/01-plan docs/02-design`: `docs/02-design/specs/20260930-p9-kcl-edges.interface.md:60`(생성된 interface card의 `_import_analog_grammar` docstring 인용)과
   P9 spec 58행("ImportError면 조용히 None"에 기댄 실행 환경 설명)이 잡힌다 -- 결정 4의 P9 알림으로 처리하고, 둘 다 P9 산출물이라 이 card에서 고치지 않는다(interface card는 B34 병합 뒤 생성 시 새 docstring을 따른다).
   `docs/03-analysis/…-20-dead-code-dup/d_inventory.json`·`d-dup-summary.md`·`function-audit/agent4_stick_diagram.md`는 과거 측정 기록이라 고치지 않는다.
9. **미배선(V7).** 새 def 0, 지우는 def 0, 되살리는 def 0 → V7 면제 불필요.
10. **기존 계약 test.** 부재를 흉내 내거나 폴백·`unavailable_reason`에 기대는 test 0개. analog-grammar 있음을 전제로 `is not None`을 단언하는 test(`test_selftest_stick_diagram` Test 30·33·35~46·48 계열)는 계약 7과 같은 방향.
    `test_s120_section`은 계약 5와 같다. `test_ic5`는 `audit_theta_root_direction` docstring의 '검사하지 않는 것:' 절과 `영역:` 줄을 본다 -- 절 머리·영역 줄을 남기면 통과. 조정 필요 test 0 → V5 승인 불필요.
