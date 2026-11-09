---
id: 20260930-b34-grammar-explicit
phase: 2
evidence_type: red-green
gate_change: no
approval: 20260923-20-dead-code-dup-design
---
## 의도

백로그 B34(`_drafts/backlog_additions.md` 7행, 준비 자료 `_drafts/prep_b34_b35_grammar.md` §1·§3.1): `stick_diagram.py`가 `skills/analog-grammar`를 import하지 못하면
**조용히 `None`을 돌려주고 호출자가 '보강 기능 없이' 계속 간다**. 그런데 이 기능은 보강이 아니라 사이징 입력의 원천이다. analog-grammar가 없으면 다음이 바뀐다(준비 자료 §1.3, 사본 `nog` 실측).
* `load_topology` meta가 library 9/9 회로에서 달라진다. 자동 채움 `device_roles`·`_matching_pairs_*`가 사라지고 `_device_roles_gap_fill_review_needed`가 9회로 모두 0건이 된다.
* 그래서 review 게이트 `require_device_roles_reviewed`(SR 7952에서 호출)가 검사할 재료를 잃는다. '검사 통과'와 '검사 못 함'이 구분되지 않는다.
* `current_reuse_telescopic_ota` θ\* 평가가 성공에서 `ValueError`(vertical_stack_id 그룹 순환)로 바뀐다.

설치본에서 실제로 일어나는 경로다: `install.py` `SKILLS`(27~29행)에 `analog-gmid-design`은 있고 `analog-grammar`는 없다.

원칙 기본안(메모리 '우회/skip 타당성 검토' 세 질문, 계획 §3.2 조용한 폴백 금지): (1) 대상은 설치본에서 실재한다 (2) 폴백 자체가 틀렸다(결과를 바꾸므로 '기존 동작' 전제가 거짓) (3) 명시적 의존으로 고칠 수 있다.
그래서 이 card는 다음을 한다. A = `skills/analog-gmid-design/assets`, SD = `A/stick_diagram.py`. 줄 번호는 gate `master` `cd64170` 기준이다.

1. **지연 import는 유지한다.** `import stick_diagram`만으로 analog-grammar를 요구하지 않는다(Phase 3 뒤 레이아웃 전용 모듈이 analog-grammar 없이 import되어야 한다 -- 준비 자료 §3.1 (a) 기각 이유).
   `_import_analog_grammar`가 `ImportError`를 삼키지 않고, 필요한 skill 이름(`analog-grammar`)과 찾은 경로를 적은 `ImportError`를 원래 예외에 이어(`from`) 다시 던진다.
   sys.path 주입 방식(레지스트리 360행 R1)은 바꾸지 않는다(별도 건).
2. **부재 폴백 분기를 지운다.** analog-grammar 부재를 뜻하던 `None` 검사와 그것 때문에만 있던 분기를 모두 지운다(아래 '사이트 목록'). 지우지 않으면 1번 뒤에 도달 불가 코드가 되고,
   docstring이 거짓("없으면 None")이 된다.
3. **`unavailable_reason`을 지운다.** 만들어 놓고 읽는 곳이 0곳이다(만들고 배선하지 않은 상태, 저장소 전수 grep). 게다가 `propose_device_roles_gap_fill`은 analog-grammar가 **있어도** gate 없는 입력에
   "analog-grammar를 import할 수 없어…"라는 틀린 사유를 싣는다(실측, 아래 '작성 전 실측' 1). 진단 신호가 섞이는 원인이다.
4. **범위 밖(그대로 둔다):** '입력에 gate 소자가 없음 → `None`/빈 결과'(`_to_analog_grammar_devs`가 `[]`인 경우)는 이 card에서 바꾸지 않는다. `test_s120_section`이 고정한 동작이다.
   이 경로의 반환에서는 `unavailable_reason` 키만 빠진다(계약 4). docstring은 '부재'와 'gate 소자 없음'을 나눠 적는다.
5. **동작 보존:** analog-grammar가 있으면 E-LIB 9/9와 E-INST가 base와 같다.

이 card는 회로·넷·소자 이름을 읽지 않는다(import 실패 처리와 분기 삭제뿐). 레일 이름 집합(B35)과 analog-grammar 쓰기 경로·게이트 공백(B36)은 범위 밖이다.
`install.py` `SKILLS`에 `"analog-grammar"`를 더하는 것은 사용자 쓰기 경로(N3.12.2 `사용자 | install.py`)라서 이 card에 넣지 않고 **별도 사용자 작업**으로 보고한다.
이 card 뒤에는 그 편집이 없으면 설치본이 조용히 틀리는 대신 명시적으로 실패한다.

### 사이트 목록(cd64170 재측정, 전부 SD)

지우는 것(부재 폴백):

| # | 함수 | 줄 | 바꾸는 것 |
|---|---|---|---|
| 1 | `_import_analog_grammar` | 1057~1058 | `except ImportError: return tuple(None …)` → 메시지를 적은 `ImportError`를 `from`으로 다시 던진다. docstring 1046~1048 |
| 2 | `find_idiom_matches` | 1073~1074 | `if netclass is None: return None` 삭제 |
| 3 | `find_stack_edges` | 1089~1090 | 같음 |
| 4 | `find_differential_and_mirror_forks` | 1313~1314 | 같음 |
| 5 | `suggest_vertical_stack_composites` | 1445~1446 | 같음 |
| 6 | `find_verified_differential_and_mirror_relations` | 1714~1715 | 같음 |
| 7 | `_propose_vertical_stack_ids` | 1894~1895 | 같음 |
| 8 | `_propose_headroom_roles` | 2259~2260 | 같음 |
| 9 | `refine_differential_and_mirror_relations` | 2400~2401(내부 `classify`의 `return None, None`), 2410~2411(`if cls_before is None: return None` -- `classify`가 더는 `None`을 주지 않아 도달 불가) | 삭제 |
| 10 | 같은 함수 | 2494~2495 `if _netclass_al is not None:` | 조건을 없애고 블록(2496~2523)을 무조건 실행 |
| 10b | 같은 함수 | 2440~2441 `if relations is None: return None` | 삭제. 같은 transistor 목록으로 2420 `candidates is None` 가드를 이미 지났으므로 `find_verified_…`는 `None`을 줄 수 없다(base에서도 부재는 2410이 먼저 잡아 도달 불가였다). 같은 def가 이미 V3 대상이라 비용 추가 없음 |
| 11 | `audit_theta_root_direction` | 3381~3382 `if netclass_mod is None or idioms_mod is None: return []` | 삭제 |
| 11b | 같은 함수 | 3387~3388 `if matches is None: return []` | 삭제. 3384 `if not devs` 가드 뒤라 `find_idiom_matches`는 부재에서만 `None`이었다(base에서는 3381이 먼저 잡아 도달 불가). 표본 V3에서 이 두 문장의 변이가 생존했다(아래 결정 필요 1) |
| 12 | `propose_theta_kcl_gap_fill` | 3529~3531(부재 → `unavailable_reason`), 3538~3540(`if matches is None:` -- 3533~3535 가드 뒤라 부재에서만 참이었다) | 삭제 |
| 13 | `propose_device_roles_gap_fill` | 4071~4073 `_static_ref_roles = (…) if _netclass_lcmf is not None else ()` | 조건 없이 튜플 |
| 14 | 같은 함수 | 4087 `if _idioms_lcmf is not None:` … 4112~4113 `else: cascoded_active_load_legs = set()` | 조건과 `else`를 없애고 블록(4088~4111)을 무조건 실행 |

`unavailable_reason` 키만 지우는 것(분기는 gate 소자 없음 경로라 남긴다):

| 함수 | 줄 | 남는 반환 |
|---|---|---|
| `propose_theta_kcl_gap_fill` | 3533~3535 | `{"theta_proposals": [], "review_needed": [], "unresolved_devices": []}` |
| `propose_device_roles_gap_fill` | 3966~3970(`refined is None`, 이제 gate 소자 없음에서만 참) | `{"matching_pairs_proposals": [], "device_roles_proposals": {}, "review_needed": []}` |

남기는 것(gate 소자 없음 경로 -- 코드 그대로, docstring만 고친다): `find_idiom_matches` 1076~1077, `find_stack_edges` 1092~1093, `find_differential_and_mirror_forks` 1316~1317,
`suggest_vertical_stack_composites` 1448~1449, `find_verified_…` 1717~1718, `_propose_headroom_roles` 2262~2263, `audit_theta_root_direction` 3384~3385,
전파 사이트 `find_differential_pair_candidates` 1543, `_propose_gm_id_roles` 2092, `_propose_L_roles` 2165·2169(두 함수는 test 41 등이 직접 부르므로 gate 소자 없음 입력의 `None`이 뜻을 가진다), `refine_…` 2420,
`propose_vertical_stack_id_gap_fill` 3296, `geometry_colocation_union` 3115.

docstring·주석(코드 AST 불변, 부재 서술을 'ImportError'로, gate 소자 없음 서술은 남김): 1025~1031 주석 블록, 1046~1048, 1304, 1384, 1533, 1676, 1891~1892, 2070, 2152, 2241, 2349, 3085, 3282,
3367, 3374~3375, 3526~3527, 3932~3933. 3374~3375는 IC5 '검사하지 않는 것:' 절 안이다 -- 절 머리와 `영역: dc, ac_struct` 줄은 그대로 두고 analog-grammar 문장만 뺀다(`test_ic5` 대상).

## 관찰 가능한 계약

A = `skills/analog-gmid-design/assets`. '부재'는 test가 파일 시스템을 건드리지 않고 흉내 낸다: `monkeypatch.setitem(sys.modules, "netclass", None)`과 `monkeypatch.setitem(sys.modules, "idioms", None)`
(둘 다, 또는 계약 2의 한쪽만). 이렇게 하면 그 이름의 import가 `ImportError`(하위형 `ModuleNotFoundError`)를 낸다. 엔진 모듈(`stick_diagram`)은 부재를 만들기 전에 import해도 되고 뒤에 해도 된다(모듈 import 자체는 analog-grammar를 요구하지 않는다 -- 계약 5).

1. **부재 → 명시적 오류.** 두 모듈이 모두 부재일 때, 아래 공개 진입점이 전부 `ImportError`(하위형 포함)를 낸다. 반환값을 내지 않는다.
   * `stick_diagram.load_topology(p)` -- `p` = `A/library/*.topology.json` 중 `_`로 시작하지 않는 9개 각각.
   * `stick_diagram.run_topology_pipeline(p, overrides)` -- 같은 9개, `overrides` = 소자마다 `{"n_fingers": 2, "finger_w": 1.0, "w": 2.0, "stack_id": "stack_<소자 이름>"}`(소자 이름은 부재를 만들기 **전에** `load_topology(p)`로 얻은 transistor 목록에서 읽는다 -- `test_ic3.py` 3절과 같은 구성).
   * transistor 목록을 받는 함수(목록은 부재를 만들기 **전에** `load_topology`로 얻는다): `find_stack_edges(ts)`, `find_idiom_matches(ts)`, `find_differential_and_mirror_forks(ts)`,
     `suggest_vertical_stack_composites(ts)`, `find_differential_pair_candidates(ts)`, `find_verified_differential_and_mirror_relations(ts)`, `refine_differential_and_mirror_relations(ts)`,
     `audit_theta_root_direction(ts, None)`, `propose_theta_kcl_gap_fill(ts, [])`, `propose_device_roles_gap_fill(ts, {}, [])`, `geometry_colocation_union(ts, [])`,
     `propose_vertical_stack_id_gap_fill(ts, [], {}, inputs=("vinp",))`.
2. **한쪽만 부재여도 오류.** `idioms`만 부재(`netclass`는 정상)이면 `load_topology(p)`(9개)가 `ImportError`를 낸다. `netclass`만 부재이면 `find_stack_edges(ts)`가 `ImportError`를 낸다.
3. **오류 메시지와 원인.** 계약 1·2의 `ImportError`는
   * `str(exc)`에 문자열 `analog-grammar`가 있고,
   * `str(exc)`에 analog-grammar 탐색 경로가 있다 -- `os.path.normpath(<저장소 루트>/skills/analog-grammar/assets)`(저장소 루트는 test 파일 위치에서 구한다. 대소문자·구분자는 `os.path.normcase`로 맞춰 비교해도 된다),
   * `exc.__cause__`가 `ImportError`(하위형 포함)다(원래 import 실패를 잃지 않는다).
4. **`unavailable_reason` 없음(analog-grammar 있음).** gate가 없는 소자만 든 목록(예: `[Transistor("Ma","pmos",source="vdd",drain="n1"), Transistor("Mb","nmos",source="gnd",drain="n1")]`)에 대해
   * `propose_theta_kcl_gap_fill(fx, [])` == `{"theta_proposals": [], "review_needed": [], "unresolved_devices": []}`
   * `propose_device_roles_gap_fill(fx, {}, [])` == `{"matching_pairs_proposals": [], "device_roles_proposals": {}, "review_needed": []}`
   * library 9회로의 `ts`에 대한 두 함수 반환에도 키 `unavailable_reason`이 없다.
5. **gate 소자 없음 경로는 그대로(analog-grammar 있음).** 계약 4의 `fx`에 대해 `find_idiom_matches(fx) is None`, `find_stack_edges(fx) is None`, `refine_differential_and_mirror_relations(fx) is None`,
   `audit_theta_root_direction(fx, None) == []`. `import stick_diagram`은 부재 상태에서도 성공한다(모듈 최상위 import 아님).
6. **동작 보존(analog-grammar 있음).** E-LIB 9/9(`load_topology`, `run_topology_pipeline` V1·V2)와 E-INST(파일럿·`folded_cascode`)가 base와 같다. 계약 1의 진입점 14개 × 9회로 반환도 base와 같다
   (auditor가 base 실행 결과와 대조 -- `propose_theta_kcl_gap_fill`·`propose_device_roles_gap_fill`는 base에서도 이 입력에 `unavailable_reason`이 없으므로 그대로 같다).
7. **부재 후 복구.** 한 프로세스에서 부재를 되돌리면(monkeypatch 해제) 같은 진입점이 다시 base와 같은 값을 낸다(상태 누수·잘못된 캐시 없음).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

(새 심볼 없음. 지우는 def 없음. 바뀌는 것은 함수 본문과 반환 dict의 키 하나.)

## 판정 유형 근거

red-green. base(`cd64170` 사본, 실측)에서 부재를 만들면 계약 1의 진입점 14개가 9/9 회로 전부 **예외 없이 반환한다** -- `load_topology`·`run_topology_pipeline`·`audit_theta_root_direction`·
`geometry_colocation_union`·`propose_vertical_stack_id_gap_fill`은 값을, 어댑터 7개는 `None`을, 두 제안 함수는 `unavailable_reason`이 든 dict를 준다. 그래서 base에서
`pytest.raises(ImportError)`가 'DID NOT RAISE'(`Failed`)로 실패한다. 계약 3은 계약 1이 red라 같이 red이고, 계약 4는 base 반환에 키가 있어 `assert`가 `AssertionError`로 실패한다.
**red는 전부 단언형(`Failed`/`AssertionError`)이다** -- base에서 부재 시 `TypeError` 등 다른 예외가 나는 진입점은 실측상 0개다.
test 쪽 안전장치(권고): 진입점 호출을 `try` / `except ImportError` / `except Exception as e: pytest.fail(...)` / `else: pytest.fail("조용히 반환")` 모양으로 쓰면 base가 어떤 비-ImportError를 내도 red가 단언형으로 남는다.
계약 5·6·7은 base에서도 green(동작 보존 부분).

## oracle 종류와 출처

* 계약 1·2·3: (a) 구성 -- 부재를 test가 만들었으므로 '거부해야 한다'가 구성으로 정해진다. 탐색 경로는 test 파일 위치에서 구한 저장소 루트로 test가 만든다(피검 출력으로 만들지 않는다).
* 계약 4: (a) 구성 -- 기대 dict는 이 card 계약 문장 그대로(빈 리스트·빈 dict).
* 계약 5: (c) 기존 동작 -- `test_s120_section`이 고정한 값과 같다.
* 계약 6·7: (c) base 실행 결과(auditor).

## 거부해야 할 입력

analog-grammar 부재(두 모듈, `idioms`만, `netclass`만 -- 계약 1·2). 판정기 자기 점검: 부재에서 조용히 `None`·`[]`·dict를 돌려주는 합성 구현(예: test 안의 가짜 진입점 `lambda *a: None`,
`lambda *a: {"unavailable_reason": "x"}`)을 같은 판정 함수에 넣으면 실패해야 한다. 메시지에 `analog-grammar`가 없는 `ImportError`, `__cause__`가 없는 `ImportError`도 판정 함수가 거부해야 한다
(`test_d_delete_telescopic`의 거부 점검과 같은 형태).

## library 회로 적용 여부

적용한다. library 9회로 전부가 계약 1(부재 → 오류)·계약 6(보존) 대상이다. SPECS 4회로 θ 평가(준비 자료 §1.3 (a))는 계약 6의 E-INST와 base 대조로 덮고 따로 계약하지 않는다
(부재 시 SR 경로는 `load_topology`에서 먼저 `ImportError`가 난다).

## 무동작 판정 입력(무발동 값)

analog-grammar가 있는 모든 실행 -- library 9회로, E-INST, 기존 test 전부. 이 card의 새 동작(오류)은 부재에서만 발동한다. gate 소자 없음 경로(계약 5)도 무발동이다(반환에서 `unavailable_reason` 키가 빠지는 것만 다르다 -- 소비처 0).

## 재현할 수치

없음.

## 결정 필요 항목

1. **V3 범위와 기존 생존 변이(착수 조건).** V3 도구(`mutate_changed.py`)는 '바뀐 줄'이 아니라 **AST 해시가 바뀐 def 전체**를 변이한다(docstring은 해시에서 빠진다).
   이 card는 def 13개(내부 `classify` 포함)의 본문을 바꾸므로 base 기준 변이 **1,139개**가 대상이다(`_import_analog_grammar` 12, `find_idiom_matches` 11, `find_stack_edges` 9,
   `find_differential_and_mirror_forks` 50, `suggest_vertical_stack_composites` 79, `find_verified_…` 69, `_propose_vertical_stack_ids` 141, `_propose_headroom_roles` 55, `refine_…` 95 + `classify` 9,
   `audit_theta_root_direction` 36, `propose_theta_kcl_gap_fill` 242, `propose_device_roles_gap_fill` 331. 삭제 문장만큼 조금 준다).
   인벤토리는 def마다 4~159개 test다(`reachability.build_graph` + `mutate_changed.inventory`). 145개 인벤토리(`_propose_headroom_roles`·`refine_…` 등) 기준 실행 1회가 137초다(실측, 사본).
   생존 변이는 인벤토리 전체를 돌고, 무한 반복을 만드는 변이는 도구 시간 상한(기본 600초)까지 간다 -- 대략 추정으로 6시간~수십 시간이다.
   **바뀐 문장 자체의 변이는 모두 죽일 수 있다**('V3 실행 가능성' 아래). 문제는 이 card가 건드리지 않는 기존 문장의 변이다. base 표본 실측(`C:/g37/mut_sample.py`, 도구의 `mutants`·`_replace_def`·`inventory`와 같은 pytest 명령):
   * `audit_theta_root_direction` 변이 36개 전부: 죽음 29, **생존 7**. 생존 중 4개는 이 card가 지우는 문장이다(3381 부재 분기 2개, 3387 `if matches is None` 2개 -- 사이트 11·11b). 남는 **기존 생존 3개**: 3384 `if not devs: return []` 문장 삭제·`return` 삭제, 3402 `others = …` 문장 삭제.
   * `propose_theta_kcl_gap_fill`(인벤토리 5개) 표본 30개 중 6개 실행: 죽음 5, 1개는 900초 시간 초과(무한 반복 -- V3에서는 죽음으로 세지만 시간 상한만큼 든다). 나머지는 시간 때문에 멈췄다.
   이 기존 생존은 이 card가 들여온 것이 아니지만 V3 규칙상 FAIL이다. 다른 큰 def(`propose_device_roles_gap_fill` 331, `_propose_vertical_stack_ids` 141 등)에도 있을 것으로 보지만 재지 않았다.
   기본안(원칙: 조용한 폴백 금지 + 기준 약화는 사용자 승인):
   * **(a) 기본안 -- 이 card 그대로 + 기존 생존 면제 승인.** auditor가 순서 3에서 **base**의 같은 def에 같은 도구 연산자를 돌려 base 생존 변이 목록을 먼저 만든다. head 생존 중 같은 문장(소스 문장 텍스트와 def qualname으로 대응)의
     base 생존과 대응하는 것만 `target_kind: decision` 승인 기록(대상 = 변이 id 목록)으로 면제한다. 이 승인은 '등가 변이' 면제가 아니라 '기존 test 강도' 면제라서 **기준 약화 = 사용자 승인**이 필요하다.
     대응이 없는 head 생존(=이 card가 새로 만든 생존)은 면제하지 않는다.
   * (b) 대안 -- 범위 축소. 계약 1~3·7은 `_import_analog_grammar`·`find_idiom_matches`·`find_stack_edges` 세 def만 바꿔도 전부 성립한다(나머지 def는 import 단계에서 이미 `ImportError`가 난다). 이때 V3 변이는 32개다.
     대신 사이트 4~14의 분기는 도달 불가 코드로 남고 계약 4(`unavailable_reason` 삭제)는 빠진다 -- 조용한 폴백은 막히지만 죽은 분기와 틀린 사유 문자열이 남는다. 사용자가 (a)의 면제를 승인하지 않으면 (b)로 card를 다시 쓴다.
2. **앞당김 근거.** B34는 N6.1 Phase 2 범위 행에 없는 백로그 항목이다. B26-1 초안과 같은 '원칙 기본안 앞당김' 형식이고 `phase: 2`는 지금 진행 중인 Phase다(판정 기록 V `N/A`·XFAIL 만료 판정 입력).
   Phase 3 M2(어댑터와 소비 함수를 MOD2 `topology_authoring`으로 이동)는 '함수별 AST 해시 동일' 증명이므로, 최종형을 이동 전에 만들어 두는 것이 싸다. 이동 뒤에 하면 같은 변경을 새 모듈에서 다시 해야 한다.
   Phase 4(실패 규약 CC-4)로 미루지 않는 이유도 같다. 오케스트레이터가 사용자 보고 때 앞당김을 알린다.
3. **B26-1과의 순서.** `refine_…`·`propose_device_roles_gap_fill`이 겹친다. 두 card를 동시에 열지 않는다(어느 쪽이 먼저여도 된다 -- 준비 자료 §4).

## 작성 전 실측

(측정: gate `master` `cd64170`, 저장소 쓰기 없음, scratch `C:/g37`(`git archive HEAD`로 만든 사본)과 저장소 파일 읽기 전용 import(`-B`). 명령은 `$PY` = `C:/Python314/python.exe -B`. scratch는 측정 뒤 삭제했다 -- 수치는 이 절에 옮겨 적었고, 재측정은 같은 명령으로 새 사본에서 한다.)

1. **사실 문장 재측정.**
   * 사이트 줄: `grep -n "_import_analog_grammar\|unavailable_reason\|_netclass_al\|_idioms_lcmf\|analog-grammar" A/stick_diagram.py`와 `sed -n`으로 각 줄을 읽었다. 블록 범위는
     `ast.walk`로 `If` 노드 `lineno/end_lineno`를 뽑았다(2495→2523, 4087→4111, else 4112~4113, 3296→3297, 1543→1544).
   * `unavailable_reason` 소비처: `git grep -n unavailable_reason`(`*.jsonl` 제외) → SD 3527·3531·3535·3540·3933·3968(전부 생산·docstring)과 `docs/03-analysis/…-20-dead-code-dup/d_inventory.json` 3325~3327(옛 줄 번호로 적은 문자열 목록)뿐. 읽는 코드 0곳.
   * 부재 동작(base): `$PY C:/g37/absent.py`(사본에서 `sys.modules["netclass"/"idioms"]=None`, 9회로 × 진입점 14개, 결과 `C:/g37/absent.jsonl`). 부재에서 예외 0건 --
     `load_topology`·`run_topology_pipeline` V1·`audit_theta_root_direction`·`geometry_colocation_union`·`propose_vertical_stack_id_gap_fill(inputs=("vinp",))`는 값 반환 9/9, 어댑터 7개는 `None` 9/9,
     `propose_theta_kcl_gap_fill`·`propose_device_roles_gap_fill`은 `unavailable_reason` 든 dict 9/9. analog-grammar 있음에서는 14개 모두 정상 반환이고 두 제안 함수에 키 없음 9/9.
   * gate 소자 없음(analog-grammar 있음): `$PY C:/g37/nogate.py`(저장소 파일 import) → `find_idiom_matches`·`find_stack_edges`·`refine_…` = `None`, `audit_theta_root_direction` = `[]`,
     `propose_theta_kcl_gap_fill` = `unavailable_reason: "gate가 있는 소자가 없음"`, `propose_device_roles_gap_fill` = `unavailable_reason: "analog-grammar를 import할 수 없어 …"`(**analog-grammar가 있는데도 틀린 사유**).
   * 캐시: SD·SR에 topology·import 결과 캐시 없음(`grep -n "cache\|lru_cache"` -- LUT 조회 캐시만). 그래서 monkeypatch 부재가 앞 test의 결과에 가려지지 않는다.
   * `install.py` 27~29행 `SKILLS`에 `analog-grammar` 없음.
   * V3 규모: `$PY C:/g37/count_mut.py`(바뀌는 def마다 `mutate_changed.mutants` 개수, `count_mut.json`), `$PY C:/g37/inv.py`(def마다 인벤토리 test 수, `inv.json`),
     145개 인벤토리 기준 실행 `pytest -c tools/gates/pytest_gate.ini … --gmid-phase=2 --gmid-strict=` → 137초(사본에 `tools/migrate`가 없어 `test_extract_selftest` 38건은 사본 결함으로 실패 -- 시간 추정에만 썼다).
     표본 변이 `$PY C:/g37/mut_sample.py audit_theta_root_direction 0`, `… propose_theta_kcl_gap_fill 30`(결과 `mut_sample.jsonl`, 변이마다 원본 복원).
2. **이름 충돌.** 새 test `A/tests/contracts/test_b34_grammar_explicit.py`. `grep -rn "glob(" A/tests/` 결과와 대조: `probe_*.py`(ts6) 불일치.
   `contracts/*.py`를 읽는 `test_ic_markers_match_plan`은 `gmid_ic` 표식만 AST로 본다(이 card는 IC를 켜지 않으므로 표식 없음). `tests/**/*.py` 내용 전수 스캔(`test_d_delete_dead`·`test_d_delete_telescopic`·
   `test_d_move_tests`·`test_ts3_no_print_verdicts`)은 삭제 이름 참조·print 판정 토큰을 본다 -- 이 card는 def 이름을 지우지 않고, test는 print로 판정하지 않는다. `ls A/tests/contracts | grep -i "b34\|grammar"` → 없음.
3. **원칙의 계약화.** 조용한 폴백 금지 → 계약 1·2(진입점 14개 × 9회로, 한쪽 부재 포함). 진단 신호 분리 → 계약 3·4·5. 만들고 배선 안 한 것 제거 → 계약 4. 동작 보존 → 계약 6·7. 회로 무관(이름을 읽지 않음) → 의도 절 끝 문장, 계약 1이 9회로 전부.
4. **쓰기 경로(N3.12.2).**
   * SD 코드·docstring·주석: gmid-code-author(`skills/analog-gmid-design/assets/*.py`).
   * test: gmid-test-author(`A/tests/**`) -- `A/tests/contracts/test_b34_grammar_explicit.py`. 기존 `tests/unit/test_selftest_stick_diagram.py` `test_s120_section` docstring 2714~2717("ImportError 경로는 … 검증 가능")은 판정을 바꾸지 않으므로 이 card에서 고치지 않는다(원하면 test-author 몫).
   * `skills/analog-gmid-design/references/analog-grammar-integration.md` 95~97·107·111·119·187~188·198·202행의 폴백 서술: 오케스트레이터 문서 커밋.
   * 레지스트리(`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`) 360행 `_import_analog_grammar` 설명: 이름 불변이라 필수 아님(code-author가 원하면 '명시적 ImportError' 한 구절).
   * `install.py`: 사용자 경로 -- card 밖, 사용자 작업 1건.
   * analog-grammar(`skills/analog-grammar/**`)는 고치지 않는다(쓰기 경로표에 행이 없다 -- B36).
5. **계획서 소비자.** `git grep -n "unavailable_reason\|조용히 None\|soft-fail\|analog-grammar가 없으면\|B34" -- docs/01-plan docs/02-design` → 0건. 지우는 이름(def) 없음.
   `docs/03-analysis/…-20-dead-code-dup/d_inventory.json`·`d-dup-summary.md`·`function-audit/agent4_stick_diagram.md`는 과거 측정 기록(줄 번호 기준)이라 고치지 않는다.
6. **미배선(V7).** 새 def 0개, 지우는 def 0개, 되살리는 def 0개 → V7 면제 승인 불필요. 바뀌는 def는 모두 이미 운영 경로(`before_phase3` 루트)에서 도달한다(준비 자료 §2.1 -- `audit_theta_root_direction`·`propose_theta_kcl_gap_fill`·
   `find_idiom_matches`·`find_differential_and_mirror_forks`는 운영 도달 아님이지만 이 card가 새로 만든 것이 아니다).
7. **기존 계약 test.** `grep -rn "sys.modules\|analog-grammar\|netclass\|unavailable_reason" A/tests/` → 부재를 흉내 내거나 폴백에 기대는 test 0개. `unavailable_reason`을 읽는 test 0개.
   analog-grammar 있음을 전제로 `is not None`을 단언하는 test(`test_selftest_stick_diagram` 2617~3360 Test 30·33·35~46·48 계열)는 계약 6과 같은 방향이라 그대로 통과한다.
   `test_s120_section`(gate 소자 없음 → `None`)은 계약 5와 같다. `test_ic5`는 `audit_theta_root_direction` docstring의 '검사하지 않는 것:' 절과 `영역: dc, ac_struct`를 본다 -- 사이트 docstring 수정에서 절 머리·영역 줄을 남기면 그대로 통과(위 docstring 목록 주의).
   `test_df35_harness_paths`의 `sys.modules` 정리는 assets·workspaces 모듈만 지운다(analog-grammar 모듈 무관). 조정 필요 test 0 → V5 승인 불필요.

### V3 실행 가능성(바뀐 문장의 변이)

`mutate_changed.mutants`의 연산자(비교 뒤집기·산술·정수 상수·문장 삭제·조기 return·except 본문 삭제)로 바뀐 문장을 따져 보았다. 문자열 상수는 변이하지 않는다.
* `_import_analog_grammar`(변이 12): `except` 본문 삭제·`raise` 문장 삭제 → 함수가 `None`을 돌려줘 부재 test에서 `ImportError` 대신 언패킹 `TypeError` → 계약 1 test가 죽인다. 조기 `return` → analog-grammar 있음에서도 언패킹 `TypeError` → 기존 test 전부가 죽인다.
  `if _ag_path not in sys.path` 뒤집기·`sys.path.insert` 삭제 → 새 프로세스에서 analog-grammar를 못 찾아 `ImportError` → 기존 test가 죽인다(V3는 변이마다 새 pytest 프로세스). `insert(0, …)`의 `0` ±1 → `insert(1)`/`insert(-1)`은 경로가 여전히 들어가 동작이 같을 수 있다 -- **등가 변이 후보 2개**(base 판 def에도 같은 문장이 있으므로 이 card가 들여온 것은 아니다. 계약 3의 경로 문자열 검사로는 못 잡는다). auditor가 생존 확인 시 (a)의 면제 대상으로 적는다.
* 삭제한 `if … is None` 분기: 문장이 사라져 변이도 없다.
* 조건을 없앤 블록(사이트 10·14)과 조건 없는 튜플(사이트 13): 문장 내용은 base와 같고 들여쓰기·경로만 바뀐다. 이 문장들의 변이는 base에서 같은 문장의 변이와 대응한다 -- base 생존이면 (a)의 면제 대상, base에서 죽던 것은 head에서도 같은 test가 죽인다.
* `unavailable_reason` 키를 뺀 두 반환 dict: 문장 삭제 변이 → `None` 반환 → 계약 4의 `==` 단언이 죽인다.
