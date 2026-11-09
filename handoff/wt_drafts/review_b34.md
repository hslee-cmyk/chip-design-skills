# review -- draft_b34.spec.md (20260930-b34-grammar-explicit)

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용, HEAD = gate `master` `7535799`.
`cd64170..7535799` 사이에 `stick_diagram.py`·`sizing_recipe.py`·tests 변경 없음(`git diff --stat` 0) -> 초안의 cd64170 줄 번호는 HEAD에서도 그대로 쓸 수 있다.
바뀐 것은 `tools/gates/mutate_changed.py`(B28 병합: `--head` 격리 복제본, 기준 실행 실패 = ERROR)뿐이다.
scratch `C:/g49`(`git archive HEAD` 사본 `base`·`clean`, 끝나고 삭제). Python `C:/Python314/python.exe -B`.

## 요약 판정

| 등급 | # | 제목 |
|---|---|---|
| **blocking** | B1 | `approval: 20260923-20-dead-code-dup-design`은 이 card를 덮지 않는다(그 승인은 "동작이 바뀌는 수정"을 명시적으로 뺐다). B26-1 검토 S3와 같은 결함이 반복됐다 |
| **blocking** | B2 | 계약 6·7의 "같은 값"을 `==`로 판정할 수 없다. `find_idiom_matches` 반환의 `idioms.Match`는 `__eq__`가 없어서 **같은 프로세스에서 두 번 부른 값도 `!=`** 다. `refine_…`의 `set` 값은 프로세스가 다르면 repr 순서가 달라진다(PYTHONHASHSEED 1·2에서 8/9 회로 차이) |
| **blocking** | B3 | "바뀐 문장의 변이는 모두 죽일 수 있다"는 새 test가 V3 인벤토리에 들어갈 때만 성립한다. V3 정적 그래프는 **데코레이터 `parametrize`의 이름 문자열과 모듈 상수 목록을 간선으로 보지 않는다**(실측). 14 × 9를 가장 자연스럽게 쓰는 모양(parametrize + `getattr`)으로 쓰면 비운영 def의 인벤토리에 새 test가 빠진다 |
| should-fix | S1 | 결정 1 (a)안: 면제 대응 절차가 정의되지 않았고, 비용이 두 배다(base 전수 실행 + head 전수 실행). 약화가 아닌 더 싼 안이 있다(아래 S1·결정 제안) |
| should-fix | S2 | 사이트 목록에 없는 거짓 docstring: SR `resolve_stack_layout` 6510~6512("analog-grammar 자체가 없어 candidates도 None이면 … 완전한 하위호환"). references 문서 118~121·440~443도 목록에 없다 |
| should-fix | S3 | 사이트 14 줄 번호가 틀렸다: `else:` 4110, `cascoded_active_load_legs = set()` 4111(초안 4112~4113은 주석). 본문 블록은 4088~4109(초안 4088~4111) |
| should-fix | S4 | 계약 7의 oracle이 "(c) base 실행 결과(auditor)"로 적혀 있는데, 계약 7은 test가 판정하는 항목이다. test 안의 oracle(부재 전 같은 프로세스 값)을 적어야 한다 |
| should-fix | S5 | 결정 3(B26-1과의 순서): 겹치는 두 def(`refine_…` 95+9, `propose_device_roles_gap_fill` 331)는 어느 쪽이 먼저여도 **V3를 두 번 낸다**. B26-1 U1(같은 V3 문제)과 한 결정으로 묶어야 한다 |
| minor | M1 | `작성 전 실측` 5의 "`docs/02-design` grep → 0건"이 사실과 다르다. `docs/02-design/specs/20260930-p9-kcl-edges.interface.md:60`이 잡힌다(생성된 interface card, `_import_analog_grammar` docstring). P9 spec 58행도 "ImportError면 조용히 None"에 기대어 실행 환경을 설명한다 |
| minor | M2 | '원칙의 계약화'에서 "진단 신호 분리 → 계약 3·4·5"라고 했는데, 계약 4는 분리가 아니라 **삭제**다(gate 소자 없음 사유도 함께 사라진다). 삭제 근거(소비처 0 = 만들고 배선 안 한 것)는 맞지만 표현을 고칠 것 |
| minor | M3 | interface card에 `Transistor`가 없다. dataclass라 생성기(`engine_defs`)가 잡지 못한다. 계약 4가 생성자를 쓰므로 계약 문장의 호출 예시(`stick_diagram.Transistor(name, kind, source=, drain=)`)만이 test-author의 근거다. 모듈 경로를 명시할 것 |

사실 확인에서 맞은 것: 사이트 1~13·10b·11b 줄, 전파·잔류 사이트, docstring 목록(SD 안), `unavailable_reason` 소비처 0, `install.py` 27~29행, 레지스트리 360행, 새 test 이름의 glob 충돌 없음,
V3 def 13개·변이 1,139개·인벤토리 4~159, `audit_theta_root_direction` 표본(죽음 29·생존 7, 같은 문장), red 모양(126/126 조용한 반환), 기존 test 조정 0(V5 불필요), V7 면제 불필요.

---

## 확인 1 -- 줄·사이트 재측정 (HEAD 7535799)

* 사이트 1~13·10b·11b와 `unavailable_reason` 두 곳(3533~3535, 3966~3970): `sed -n`으로 전부 초안과 같다.
* `ast.walk` If 범위: 2495→2523(body 2496~2523), 3381/3387/2410/2420/2440/1543/3296 전부 초안과 같다.
  **4087→4111, body 4088~4109, else 4111(`else:` 줄 4110)**. 초안 표 14와 실측 절의 "else 4112~4113"은 틀렸다. 4112~4113은 주석이다(S3).
* SD 안 부재 서술 grep(`analog-grammar` + 없/None/soft/못 불러/하위호환): 1028·1047·1304·1384·1533·1676·1892·2070·2152·2241·2349·3085·3282·3367·3374·3526·3932(+코드 3531·3968). 초안 목록과 일치한다.
* **SD 밖(누락, S2)**:
  * `sizing_recipe.py` 6509~6512(`resolve_stack_layout` docstring 3·4번): "analog-grammar 자체가 없어 candidates도 `None`이면 `geometry_colocation_union()`(레거시)으로 최종 폴백 -- … 완전한 하위호환을 보장한다". B34 뒤에는 거짓이다(부재 = `load_topology`에서 먼저 `ImportError`). docstring만 고치면 되고 AST 해시가 바뀌지 않아 V3 비용은 없다. 쓰기 주체는 code-author(`A/*.py`).
  * `references/analog-grammar-integration.md` 118~121("저장소 밖에서 … 자동으로 `None`이 되어 조용히 하위호환 경로로 빠진다(의도된 동작)")과 440~443(test 계획 4 "analog-grammar 부재 시 폴백 … `None`을 반환하는지"). 초안 목록(95~97·107·111·119·187~188·198·202)에 440이 없고 119만으로는 118~121 단락을 덮는지 모호하다. 오케스트레이터 문서 커밋.

## 확인 2 -- red 재현 (base, `C:/g49/absent.py`)

방법: 사본에서 `stick_diagram` import → 회로마다 `load_topology`로 `ts`·소자 이름을 먼저 얻음 → `sys.modules["netclass"/"idioms"] = None` → 진입점 호출 → 원래 값 복원 → 다시 호출. 케이스마다 JSONL append.

| 모드 | 결과(9회로 × 14 = 126) |
|---|---|
| 둘 다 None | **126/126 예외 없이 반환**(어댑터 7개 `None`, 두 제안 함수 `unavailable_reason` 든 dict, 나머지 값) |
| `idioms`만 None | 126/126 반환 |
| `netclass`만 None | 126/126 반환 |
| 복원 뒤 재호출 | 3모드 모두 126/126 부재 전 값과 같음(repr 해시) |

* `sys.modules[name] = None`이면 `importlib.import_module(name)`은 `ModuleNotFoundError`를 낸다. 1045행이 그것을 삼키므로 base는 조용히 반환한다. 초안의 red 서술(모두 `Failed`/`AssertionError`, 비-ImportError 0개)과 일치한다. sys.path 주입은 부재 흉내에 영향이 없다(`None` 항목이 경로 탐색보다 먼저 걸린다).
* 병합본 상당 확인(`clean` 사본에서 **`_import_analog_grammar`의 except만** `raise ImportError(… _ag_path) from e`로 바꿈):
  둘 다 None → **126/126 `ImportError`**, `netclass`만 → 126/126, `idioms`만 → 108/126(`find_stack_edges`·`geometry_colocation_union`만 반환 -- idioms를 안 씀, 계약 2와 모순 없음).
  analog-grammar 있음 → 126/126 base와 같은 값(같은 seed), 복원 126/126. 메시지에 경로가 들어간다.
  -> **계약 1·2·3·5·6·7은 def 1개(`_import_analog_grammar`, 변이 12)만 바꿔도 전부 성립한다.** 초안 결정 1 (b)의 "세 def"보다 좁다. 계약 4만 두 제안 함수의 본문 변경이 필요하다.

## 확인 3 -- 캐시 오염·순서 의존

* SD·SR·AG 모듈 수준 캐시(`lru_cache`·`*_CACHE`): `topology_library.nmcnr_check_dominant_pole_approximation`(float 4개 입력의 순수 함수)과 SR의 LUT·knee·feasible-L·achievable-bound 캐시뿐이다. topology·import 결과를 쥐는 캐시는 없다. 확인 2의 복원 뒤 동일 126/126 × 3모드(base·병합 상당 모두)가 실측 근거다.
* `monkeypatch.setitem`은 원래 값이 있으면 그 객체를 되돌리고, 없었으면 키를 지운다. `idioms`를 처음 import하다 `netclass`가 `None`이라 실패하면 Python이 부분 초기화된 `idioms`를 `sys.modules`에서 지운다. 그래서 반쯤 import된 모듈이 남지 않는다.
* 순서 위험이 하나 남는다. 부재를 **첫 import 전에** 만들고 복원하면(키 삭제) 다음 import는 새 모듈 객체를 만든다. 옛 `Match` 클래스와 새 클래스가 섞일 수 있다. 계약 문장대로 `ts`를 부재 전에 `load_topology`로 얻으면 AG가 먼저 import되므로 이 경우는 생기지 않는다. test 쪽 권고로 "부재는 입력을 얻은 뒤 test 본문 안에서만 만든다(세션 fixture 안에서 만들지 않는다)"를 적어 두면 충분하다.
* **실제 문제는 캐시가 아니라 비교다(B2).**
  * `idioms.Match`는 `__init__`/`__repr__`만 있고 `__eq__`가 없다(`idioms.py` 60~65). 그래서 `find_idiom_matches(ts) == find_idiom_matches(ts)`가 **9/9 False**다(실측 SELF-UNEQUAL).
  * 계약 7("다시 base와 같은 값")과 계약 6("14 × 9 반환도 base와 같다")을 `==`로 쓰면 base·병합본 모두에서 실패한다. test-author는 analog-grammar 소스를 볼 수 없으니 이것을 알 방법이 없다.
  * `refine_…`의 `active_load_leg_candidates`는 `set`이다. base·병합본을 다른 프로세스에서 repr·JSON으로 대조하면 PYTHONHASHSEED에 따라 8/9 회로가 '다름'이 된다(seed 1 대 2 실측).
  * 고칠 것: 계약 6·7에 정규화를 적는다. `Match` → `(kind, devices, sorted(ports.items()), note, priority)` 튜플, `set`/`frozenset` → `sorted` 리스트, 나머지 dataclass는 `==`. auditor 대조도 같은 정규화를 쓰거나 PYTHONHASHSEED를 고정한다.

## 확인 4 -- V3 비용과 결정 1

### 수치 재측정

* `mutate_changed.mutants`를 base 본문에 돌렸다. 13 def 변이 수는 12·11·9·50·79·69·141·55·95·9(`classify`)·36·242·331로, **합 1,139가 맞다**. 도구는 중첩 def를 바깥 def 변이에도 넣는다. 그래서 `classify` 9개는 `refine_…` 95개 안에도 들어 있어 두 번 돈다(도구 동작 그대로라 수치 자체는 맞다).
* 인벤토리(`reachability.build_graph` HEAD + `inventory`):

  | def | 인벤토리 |
  |---|---|
  | `_import_analog_grammar` | 159 |
  | `find_idiom_matches` | 15 |
  | `find_stack_edges` | 66 |
  | `find_differential_and_mirror_forks` | 10 |
  | `suggest_vertical_stack_composites` | 153 |
  | `find_verified_…` | 150 |
  | `_propose_vertical_stack_ids`·`_propose_headroom_roles`·`refine_…`·`classify` | 145 |
  | `audit_theta_root_direction` | 4 |
  | `propose_theta_kcl_gap_fill` | 5 |
  | `propose_device_roles_gap_fill` | 138 |

  초안과 같다.
* 표본(`C:/g49/mut_sample.py`, 도구의 `mutants`·`_replace_def`·pytest 명령, `-x`, 변이마다 복원):
  * `audit_theta_root_direction` 36개 전부: 기준 실행 9.7초. **죽음 29, 생존 7**(3381·3382·3384·3385·3387·3388·3402). 초안과 문장까지 같다.
  * `propose_theta_kcl_gap_fill` 무작위 40개(seed 1): 기준 실행 9.3초, 변이당 약 10초.
    결과: **죽음 32(시간 초과 1 포함, 302초), 생존 8**(3606·3609 const±, 3644·3655·3717·3721 stmt_delete, 3731·3772 const±). 모두 이 card가 건드리지 않는 기존 문장이다(대부분 중첩 `_run_rules_1_to_3`).
    생존율 20%를 전체 242에 비례하면 **기존 생존 약 48개**로 추정된다. 40개 실행에 703초가 걸렸으므로 전수는 약 1시간 + 시간 초과분이다.
* 인벤토리 145~159인 def 7개의 변이 약 790개가 비용의 대부분이다. 인벤토리가 작은 def(`audit_theta` 36, `propose_theta_kcl` 242, `find_idiom_matches` 11, `forks` 50)는 변이당 10초 안팎이라 **시간 문제가 아니다**. 초안의 "6시간~수십 시간"은 큰 인벤토리 def 몫이다.

### (a)안 평가

* **약화다 -- 사용자 승인이 필요하다는 작성자 판단에 동의한다.** 기존 test 강도를 면제하는 것이지 등가 변이 면제가 아니다.
* **정의되지 않은 절차가 있다.** 변이 id는 `<모듈>:<qualname>:<연산자>:<AST 경로>`다. 사이트를 지우면 뒤 문장의 경로가 밀린다.
  * 실측 예: base `audit_theta…:stmt_delete:body[4]`(3384)는 head에서 `body[3]`이 된다(3381 삭제).
  * 조건을 없앤 블록(사이트 10·14)은 `body[k].body[i]` → `body[k+i]`처럼 경로 모양 자체가 바뀐다.
  * '소스 문장 텍스트'는 유일하지 않다(`return []`, `return None`이 한 def에 여러 번 나온다).
  * 대응표를 누가 무슨 도구로 만드는지(auditor 수작업? 새 스크립트면 게이트 도구 변경?)와 대응 키(qualname + 연산자 + 정규화된 문장 `ast.dump` + 같은 문장 안 노드 경로 + 등장 순번)가 card에 없다.
* **비용이 두 배다.** base 생존 목록을 만들려면 base에서 같은 def에 같은 연산자를 **전수** 돌려야 한다. 인벤토리 145~159 def의 base 전수 실행이 head 전수와 같은 규모다(수 시간~수십 시간 × 2).

### 약화가 아닌 더 싼 안 (권고)

1. **B34 본체를 좁힌다. 문제의 정의(조용한 폴백)를 닫는 데 필요한 것만 남긴다.**
   * `_import_analog_grammar`(raise, 변이 12)만으로 계약 1·2·3·5·6·7이 전부 성립한다(확인 2 실측).
   * 여기에 인벤토리가 작은 def의 부재 분기 삭제를 넣는다: `find_idiom_matches`·`find_stack_edges`·`find_differential_and_mirror_forks`·`audit_theta_root_direction`. 변이 합은 12+11+9+50+36 = 118이다.
   * `propose_theta_kcl_gap_fill`(242, 기존 생존 추정 약 48)은 시간은 싸지만 **죽일 계약이 많다**. 넣는다면 순서 3에서 auditor 전수 목록 → test-author 보강의 1회 왕복이 추가된다. 빼면 사이트 12·`unavailable_reason` 두 곳과 계약 4 첫 줄이 빠지고 도달 불가 분기 1개가 남는다(비운영 함수라 동작 영향 없음, 백로그).
     기본안은 **빼는 것**이다. 이 card의 목표(조용한 폴백 제거)와 무관한 기존 test 강도 보강을 끌어들이지 않는다.
   * 이 def들의 기존 생존은 **죽이는 계약을 더해** 처리한다. 면제하지 않는다. 예:
     * `audit_theta` 3384·3385(head에서 `if not devs` 삭제 → `find_idiom_matches`가 `None` → A형 θ가 있으면 `propagate_reference_role_through_cascode(None, …)`): "gate 소자 없는 `fx` + `sizing_roles={"theta":[{"name":"t","feeds":{"type":"A","root":"Ma","reference":["Mb"]}}]}` → `[]`". oracle은 (c) base 동작이다.
     * 3402(`others = …` 삭제 → A_signed 분기에서 `others` 미정의): "gate 있는 소자 목록 + A_signed θ(`terms: []`) → `[]`". oracle은 (a) 구성이다(terms가 비면 발견 없음).
     * `find_idiom_matches`·`find_stack_edges`·`forks`의 기존 생존은 재지 않았다. 변이 70개·인벤토리 10~66이므로 순서 3에서 auditor가 base 전수로 목록을 내면 된다(수십 분).
2. **운영 경로 큰 def의 부재 분기 삭제(사이트 5~10·10b·13·14, `propose_device_roles_gap_fill` 3966 `unavailable_reason`)는 어차피 그 def 본문을 바꾸는 card로 옮긴다.** 추가 V3 비용이 0이다.
   * B26-1: `refine_…`·`propose_device_roles_gap_fill`에 `rails`를 넣는다(초안 계약). 사이트 9·10·10b·13·14와 3966이 여기 속한다.
   * B35(준비 자료 §3.2): 운영 함수 8개(`suggest_vertical_stack_composites`·`find_verified_…`·`_propose_vertical_stack_ids`·`_propose_headroom_roles` 포함)에 `rails` 키워드를 넣는다. 사이트 5~8이 여기 속한다.
   * 그 사이 이 분기들은 도달 불가다(부재면 import 단계에서 이미 `ImportError`). 동작 영향도 없다. **docstring은 이 card에서 전부 고친다**(해시 불변 → V3 비용 0). 예: "`netclass is None` 분기는 도달 불가 -- 삭제는 B26-1/B35".
   * Phase 3 M2 이동(해시 동일 증명)은 도달 불가 분기를 그대로 옮기면 되므로 순서 제약이 없다.
3. 위 1·2로 하면 **V3 기준 약화 승인이 필요 없다.** 남는 것은 사용자 결정이 아니라 순서 조정이다(원칙: 인프라가 아닌 엔진 결함을 먼저, 같은 def는 한 번만 변이).

## 확인 5 -- `propose_device_roles_gap_fill`의 틀린 사유

* 재현했다. analog-grammar가 있을 때 gate 소자 없는 입력에서 `refine_…`이 `None`(2420 경로)을 주고, 3966이 "analog-grammar를 import할 수 없어 …"를 싣는다.
* **범위 안이다.** 이 card의 주제(부재와 gate 소자 없음이 섞이는 문제)가 그대로 드러난 사례이고, 고치는 법(소비처 0인 키 삭제)도 계약 4와 같다.
* 다만 이 문장은 331개 변이·인벤토리 138의 def 안에 있다. 권고안 2대로 B26-1(같은 def를 이미 바꾼다)에 넣는 것이 V3 비용 면에서 맞다.
* 이 card에 남긴다면 계약 4의 두 번째 줄을 유지하되 결정 1의 V3 처리에 종속된다. B26-1로 옮긴다면 이 card는 'B26-1 계약에 넣을 한 줄'로 인계를 적는다.

## 확인 6 -- 순서 (B26-1, Phase 3 M2, P9)

* **B26-1:** 겹치는 def 2개(합 약 435 변이, 인벤토리 138~145)는 어느 쪽이 먼저여도 두 번 변이된다. 초안의 "어느 쪽이 먼저여도 된다"는 병합 충돌만 본 것이다. B26-1 검토의 U1(같은 V3 전수 문제, 사용자 결정 대기)과 **같은 뿌리**다. 결정 1을 별도로 묻지 말고 U1과 하나로 묶어 한 번에 정할 것(S5).
* **Phase 3 M2:** 권고안에서 B34 본체(1번)는 M2 전에 넣는 것이 좋다(작은 def라 이동 뒤에 해도 싸지만, 초안 논리 그대로 최종형을 먼저 만든다). 큰 def 정리(2번)는 B26-1(Phase 3 전)과 B35(M2 뒤라면 MOD2 파일에서)에 딸려 간다. M2 해시 동일 증명과 충돌하지 않는다.
* **P9(gate에 spec card 있음, 진행 중):** P9 spec 58행과 P9 interface card 60행이 "ImportError면 조용히 None"을 전제로 실행 환경을 설명한다. P9 판정이 B34 병합 전에 끝나면 영향이 없다. B34가 먼저 병합되면 P9 auditor에게 "트리 밖 사본은 이제 조용히 달라지는 대신 `ImportError`"라고 알린다. 판정 결과는 바뀌지 않는다(P9는 저장소 트리 복제본에서 실행).

## blocking 상세

### B1. approval 줄

`.ai/approvals/20260923-20-dead-code-dup-design.md` 범위 설명: "덮지 않는 것: … **동작이 바뀌는 수정**". B34는 부재 시 반환이 `ImportError`로 바뀌고 반환 dict 키가 빠지는 동작 변경이다. 그리고 결정 2(앞당김)를 "오케스트레이터가 사용자 보고 때 알린다"로 처리했다. B26-1 검토 S3("앞당김은 '알림'이 아니라 decision 승인 기록")와 그 뒤 B26-1이 `20260930-b26-before-phase3`로 바꾼 선례와 어긋난다.
**고칠 것:** `target_kind: decision` 승인 기록 한 건(대상 = B34를 Phase 2 진행 중에 앞당김 + 범위(권고안 1/2 중 택)). V3 처리 결정과 같은 기록으로 받아도 된다. card `approval` 줄을 그 id로 바꾼다.

### B2. 계약 6·7 비교 정의

확인 3 참조. 계약 7에 test 쪽 oracle과 정규화 규칙을 적는다(S4와 함께): "부재 전 같은 프로세스에서 얻은 값과 복원 뒤 값을 정규화해 `==`. 정규화: `Match`류(속성 `kind`·`devices`·`ports`·`note`·`priority`를 가진 객체) → 튜플, set → 정렬 리스트". 계약 6의 auditor 대조에도 같은 정규화나 PYTHONHASHSEED 고정을 적는다.
test-author는 `Match`의 속성 이름을 모른다. interface card에 `find_idiom_matches`의 반환 요소 모양이 없으므로 **card 계약 문장에 속성 이름을 적어야 한다.**

### B3. V3 인벤토리와 test 모양

실측(`C:/g49/invshape.py`, HEAD 그래프 + 합성 test 파일):

| test 모양 | 정적 도달(`find_idiom_matches`·`forks`·`audit_theta`·`propose_theta_kcl`·`_import_analog_grammar`) |
|---|---|
| `@pytest.mark.parametrize("name", ["find_idiom_matches", …])` + `getattr(stick_diagram, name)` | **없음** |
| 모듈 상수 `NAMES = [...]` + 본문 루프 `getattr` | **없음** |
| 본문 직접 호출 `stick_diagram.find_differential_and_mirror_forks(...)` | forks, import |
| 본문 안의 문자열 리터럴 + `getattr` | 있음 |

`reachability._refs`는 test 함수 **본문**만 보고(데코레이터 제외), 모듈 수준 상수는 `<module>` 노드에 붙어 test 노드와 이어지지 않는다.
비운영 def 4개(`find_idiom_matches`·`forks`·`audit_theta`·`propose_theta_kcl`)는 `load_topology`에서 도달하지 않는다. 새 test가 이들을 데코레이터로만 부르면 기존 test(인벤토리 4~15)만 돌아 새 문장(예: `propose_theta_kcl` 3533 dict에서 키 삭제)의 변이가 살 수 있다.
**고칠 것:** 계약 절(또는 판정 유형 근거의 'test 쪽 안전장치')에 "각 진입점은 test 함수 본문에서 `stick_diagram.<이름>(…)` 형태로 직접 부른다(V3 정적 인벤토리가 데코레이터·모듈 상수의 이름 문자열을 보지 않는다)"를 적는다.

## 사용자 결정 (진짜 사용자 몫만)

1. **V3 기존 생존 처리 -- B26-1 U1과 한 결정으로.**
   * 기본안(원칙: 기준 약화 없음 + 같은 def는 한 번만 변이): B34를 권고안 1(import raise + 소형 def 4개, 기존 생존은 죽이는 계약 추가)로 좁힌다. `propose_theta_kcl_gap_fill`의 정리와 계약 4는 백로그로 보낸다. 운영 경로 큰 def의 도달 불가 분기 삭제는 B26-1·B35로 넘긴다. 이 경우 약화 승인이 필요 없다.
   * 사용자가 초안 전체 범위를 원하면 그때 (a)(base 생존 면제, 약화 승인)나 B26-1 U1 (a)(V3 범위를 바뀐 문장으로 좁히는 도구 결정)를 정한다. 어느 쪽이든 B26-1과 같은 규칙을 써야 한다.
2. **앞당김 승인(B1).** decision 승인 기록 한 건. 1과 같은 기록으로 받아도 된다.
3. (결정 아님, 사용자 작업) `install.py` `SKILLS`에 `"analog-grammar"` 추가. 초안 서술 그대로이고, 검토에서 이견은 없다.

## 산출물·정리

scratch `C:/g49`: `absent.py`·`absent_clean.py`(부재 매트릭스), `count_mut.py`, `inv.py`, `invshape.py`, `mut_sample.py`. 결과는 이 문서에 옮겨 적었고, 측정 뒤 `C:/g49`를 삭제했다. 저장소 쓰기와 상태 변경 git은 없었다(`git archive`·`git show` 읽기만).
