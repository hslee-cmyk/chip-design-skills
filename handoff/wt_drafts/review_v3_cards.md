# 독립 검토 -- V3 면제 묶기 card · V3 범위 정책 card · 결정 질문

검토자: 독립 reviewer(작성자 아님). 저장소 읽기 전용(gate `master` HEAD `7535799`), scratch `C:/g56`(끝나고 삭제). `$PY` = `C:/Python314/python.exe -B`(3.14.2).
대상: `draft_v3_exempt_binding.spec.md`, `draft_v3_scope_policy.spec.md`, `draft_v3_decision_question.md`, `v3_scope_systemic.md`.
대조한 원문: `tools/gates/mutate_changed.py`(전문), `reachability._approved_ids`·`iter_defs`, `merge_gate.parse_approval_header`, `test_lint.py` 729~733행, `weakening_diff.approved_hashes`,
`tests/tools/engine_dup_scan.py`, redteam `lib/rt.py`(`build_vrepo`·`_commit_case`·`_file_content`), `attacks/28·29·31`, design 05 §10 V3 행(317)·§18(555~), 계획 N4.2 V3(839)·N3.10 이동 규칙(533),
`.ai/verification/20260930-df36-instance-relpath.json`, P9 가지(`role/*/20260930-p9-kcl-edges`, 병합 `b7765b0`), `_drafts/draft_p3_g1.spec.v3.md`.

---

## 요약 판정

| card | 판정 | 막는 것 |
|---|---|---|
| 면제 묶기(20260930-v3-exempt-binding) | **승인 전 수정 필요** | B1(docstring 때문에 같은 해시에서 경로가 다른 문장을 가리킴 -- 묶기가 새 누수를 남긴다) |
| 범위 정책(20260930-v3-changed-stmt-scope) | **승인 전 수정 필요** | B2(def 머리만 바꾼 동작 변경은 대상 변이가 0개일 수 있고, 0개면 test가 하나도 없어도 V3 PASS) |
| 결정 질문 | 대체로 중립. 보완 필요 | S10(놓치는 결함 열이 없음, 측정 안 한 주장, "결정 없이 진행"이라는 표현), B2·S6을 반영해야 함 |

진행 중인 card 영향(실측): **P9(`b7765b0`)는 영향 없음** -- 바뀐 def는 `kcl_series_union`·`kcl_series_union.find`뿐이고, `load_topology` 해시 `c22bdd32…`와 `save_instance_json` 해시 `11a55c19…`는
`7535799`와 `b7765b0`에서 같다(C8 id 14개가 걸릴 def가 대상이 아님). P9 spec card도 1(d)를 택해 면제를 쓰지 않는다. 기존 redteam에는 V3 면제를 쓰는 케이스가 없다
(`grep` 0건) → 면제 card 계약 7은 그대로 성립한다. 기존 V3 케이스(28·31의 7단계)는 모두 새 def(`rt_scale`)만 바꾼다 → 범위 card 계약 6도 성립한다.

---

## Blocking

### B1. [면제 묶기] def 해시는 docstring을 빼고 재지만, 변이 경로는 docstring을 포함해 센다 → 해시가 같아도 같은 id가 다른 문장을 가리킨다

* 근거: `def_hash`는 `_strip_doc`을 적용한 트리를 해시한다(중첩 def·class의 docstring까지 지우고, 본문이 비면 `Pass`를 넣는다). 반면 `mutants(fn, …)`는 **docstring을 지우지 않은** `fn`을
  돌면서 `body[i]` 경로를 만든다. 실측(`C:/g56/docshift.py`, 도구 함수 그대로 import):
  ```
  A: def f(x): y = clamp(x); log(y); return y
  B: A에 docstring 한 줄만 더함
  hash equal: True
  body[1] | A: log(y)        | B: y = clamp(x)
  body[2] | A: return y      | B: log(y)
  ```
  A에서 승인한 `…:f:stmt_delete:body[1]@H`(`log(y)` 삭제, 등가로 면제)는 B에서도 해시가 같아(H) **`y = clamp(x)` 삭제 변이를 조용히 면제**한다.
* 현실적인 경로: card 재시도에서 code-author가 docstring만 더하거나 지운다(검토 지적에 흔히 따라오는 수정). 승인은 시도 k의 head에 묶였고, 시도 k+1은 base와 해시가 달라 여전히 대상이다 →
  면제가 밀린 경로에 적용된다. 중첩 def의 docstring도 그 def 안의 경로를 똑같이 민다.
* card의 "해시가 같아지는 경우는 승인한 형태와 같은 코드뿐이라 면제가 맞다"(의도 절)는 **거짓**이다. 고치려던 '경로만 보는 누수'의 한 형태가 남는다.
* 고칠 것: 묶는 해시는 **변이 경로를 정하는 바로 그 트리**의 해시여야 한다 -- `sha256(ast.dump(fn, include_attributes=False))`(docstring을 지우지 않은 head def). design 05 ①의
  대상 선택 해시(docstring 제외)와는 이름을 달리해 정의한다(예: "묶기 해시"). `survivor_bindings`도 같은 해시를 쓴다. redteam에 (e) `docstring-shift`(attack: 승인 `X@<docstring 없는 def의
  묶기 해시>`, head가 docstring만 더한 def이고 X 경로의 새 문장 삭제 변이가 생존 → exit 1)를 더한다. 이 경우 base 도구는 `@`를 몰라 exit 1이므로 red는 (a)·(c)가 맡고 (e)는 회귀 방지 단계다.

### B2. [범위 정책] def 머리만 바꾼 동작 변경은 대상 변이가 0개일 수 있다 -- 0개면 test가 없어도 V3 PASS

* 계약 1의 T3은 def 머리 변경일 때 "def 자기 필드(인자 기본값 등) 안의 변이"만 대상으로 삼는다. 그런데 도구 연산자로 보면:
  * 상수 변이는 `int`/`float`만 대상이고 **`bool`은 뺀다**(`mutants` 160행 `not isinstance(node.value, bool)`). 문자열·`None`은 변이가 없다. → `def f(x, strict=False)` → `strict=True`,
    `mode="fast"` → `"exact"`, 기본값 `None` → `[]`는 T3 변이가 **0개**다.
  * 매개변수 추가·삭제·이름 바꾸기·순서 바꾸기·`*`(키워드 전용) 추가는 연산자가 걸릴 노드가 없다 → 0개.
  * **데코레이터 변이는 실행되지 않는다(도구 결함, 실측)**: `_replace_def`가 `nf.decorator_list = []`로 지우고 원래 데코레이터 줄을 그대로 둔다(`fn.lineno`는 `def` 줄). `C:/g56/deco.py`:
    `@functools.lru_cache(maxsize=128)`의 `const±` 변이 2개가 `NOOP`(바뀐 소스가 원본과 AST 동일). 데코레이터를 더하거나 빼는 변경(`@lru_cache` 추가 = 캐시로 낡은 값 반환 가능)도
    T3 실효 변이가 0개다.
  * T5(`early_return`)의 발동 조건 "새 문장·머리 변경·지운 문장"의 '머리 변경'이 **def 머리**를 포함하는지 정의가 없다. 포함하지 않으면 위 변경들은 대상 변이 0개다.
* 대상 변이가 0개면 `survivors`가 비어 **PASS**다 -- 인벤토리가 0이어도("인벤토리 없음 → 생존"은 변이가 있을 때만 작동한다). 지금 규칙에서는 같은 변경이 본문 전체를 대상으로 만들고,
  인벤토리 0이면 모든 변이가 생존해 FAIL이다. 즉 **의도한 약화(바뀌지 않은 문장 제외)를 넘는 구멍**이다: 이 card의 test가 바뀐 코드를 전혀 부르지 않아도 통과한다.
* 고칠 것(셋 다 필요):
  1. T5를 무조건으로: "해시가 바뀐 모든 기존 def에서 `early_return`은 대상"(그러면 인벤토리 0 → 생존 → FAIL이 살아난다).
  2. def 머리 변경(인자·기본값·데코레이터·반환 주석·`type_params`)이면 **본문 전체를 대상**으로(보수 쪽 -- 매개변수 의미가 바뀌면 그 매개변수를 읽는 모든 문장이 영향을 받는다). 더 좁히고 싶으면 '바뀐
     매개변수 이름을 읽는 문장'(D1과 같은 이름 기준)으로 정의한다.
  3. 계약에 "해시가 바뀐 기존 def의 대상 변이 ≥ 1"을 넣고, redteam `33-…`에 (f) `header-default-bool`(attack: 기본값 `False→True`만 바꾸고 그 def에 닿는 test 없음 → exit 1)을 더한다.
* 데코레이터 NOOP은 지금 규칙에도 있는 결함이다(실제 소스 `topology_library.py:248` `@functools.lru_cache(maxsize=256)` -- 그 def를 바꾸는 card는 지금도 확정 생존 2개를 받는다, 거짓 FAIL 쪽).
  범위 card에서는 T3이 이 변이를 명시적으로 대상으로 삼으므로 "데코레이터 안 변이는 `mutants`에서 내지 않거나 `_replace_def`가 데코레이터도 바꾼다"를 이 card 또는 별도 게이트 card로 정해야 한다
  (백로그만으로 두면 T3의 데코레이터 몫이 항상 확정 생존이 된다).

---

## Should-fix

### S1. [면제 묶기] oracle 출처 문장의 redteam 사실이 틀렸다 -- V 케이스는 `approval`·`more_approvals`·`base_files` 키를 쓰지 않고, 해시 치환 자리표시자도 없다
* `lib/rt.py`의 `approval`·`more_approvals`·`base_files`는 `_commit_case`(EL3/EL4 커밋형 케이스) 키다(446·459행). V 케이스(`build_vrepo`, 524행~)는 `base`·`head` 파일 사전과 V5용
  `approve_after_head`만 읽는다. 선례 V4 `attacks/29-v4-decision-exempt`는 승인 기록을 `head` 사전의 `.ai/approvals/<id>.md` 파일로 둔다(실측).
* `_file_content`의 치환은 `subst_str`(상태 변수)와 `replace` 쌍뿐이다 -- def 해시 자리표시자가 없다. "케이스 생성 쪽(`lib/rt.py`의 치환 자리표시자 등)에서 독립 계산"은 **rt.py 동작 추가**이고,
  선례 C10(`20260923-caa970b-replay`)은 "rt.py 실행 동작 하나"를 게이트 변경 승인 범위에 따로 적었다.
* 고칠 것: (i) 배치 문장을 "`head`(또는 `base`) 사전의 `.ai/approvals/<id>.md`"로 고친다. (ii) 해시를 어떻게 넣는지 정한다 -- rt.py에 자리표시자(예: `@{DEFHASH:<경로>:<qualname>}`,
  케이스 head 소스 텍스트에서 B1 정의로 계산)를 더하면 쓰기 경로(test-author, C10 행)와 승인 범위 설명에 적는다. 고정 리터럴을 v.json에 박으면 인터프리터가 바뀔 때 (c)가 조용히 깨진다(S4).
* (a) `legacy-unbound-leak`의 red(base exit 0)는 **X가 그 def의 유일한 생존 변이**일 때만 성립한다(다른 변이가 하나라도 살면 base도 exit 1). (c)에는 이 조건이 있지만 (a)에는 없다 -- 더한다.

### S2. [면제 묶기] DF-36이 이 누수를 실제로 썼다 -- '잃는 것이 없다'에 그 사실을 적어야 한다
* `.ai/verification/20260930-df36-instance-relpath.json` V3 basis: head `b29be01`에서 "26 → killed 22, **exempt 4**(head 트리 승인 `20260922-ic3-v3-exempt`), 생존 0". 이 4개는
  `save_instance_json`(이 card가 적은 대로 `b29be01`에서 해시 `9cb09766…` → `11a55c19…`)의 id다. C8 기록 범위 설명("두 함수의 본문 구조가 바뀌면 이 면제는 맞지 않는다") 밖에서 적용된 것이다.
  auditor는 4개가 같은 문장을 가리키는지 손으로 확인했지만, 승인 범위로 보면 DF-36 V3 PASS는 누수에 기댄 판정이다.
* 판정이 뒤집히는가: 자동으로는 아니다. `integrity.py` 행 3(나) 재판정은 옛 판 `merge_gate.py receive`를 데이터만으로 돌리고, `merge_gate.py`는 V3를 부르지 않는다(`grep` 0건). 같은 입력으로
  다시 판정하면 4개를 실제로 돌리게 되고, `indent=2` ±1은 등가라 생존할 것이고 `scope_note` 2개는 B8 공백이라 생존할 가능성이 높다(돌리지 않음 -- 추정이 아니라 판정 구조만 적는다).
* 고칠 것: '작성 전 실측' 1의 `save_instance_json` 항에 "DF-36 V3가 이 4개를 면제로 썼다"를 적고, history에 기록하고, 백로그 한 줄(HEAD에서 4개 실제 실행 → test 보강 또는 묶인 면제)을 더한다.
  결정 질문의 "잃는 것이 없다"는 미래 card 기준으로만 맞다는 점도 함께 적는다.
* 곁가지: B34는 `load_topology`를 대상에 넣는다(`v3_scope_systemic.md` §2 전파 폴백). 선택지 1이면 묶기 뒤 C8의 `load_topology` B8 공백 변이 10개가 B34에서 다시 대상이 된다(지금 도구라면
  경로가 같을 때 조용히 면제됐을 것). 결정 질문 선택지 1 칸에 적는다.

### S3. [면제 묶기] 원소 해석 규칙이 정해지지 않았다
* 같은 id에 원소가 여럿일 때(시도마다 승인: `X@H1`, `X@H2`) 계약 1(맞는 해시 → exempt)과 계약 2(다른 해시 → `exempt_ignored`)가 함께 걸린다. "맞는 원소가 하나라도 있으면 exempt, 그때 맞지 않는
  원소는 싣지 않는다(또는 싣는다)"를 정한다.
* `@` 분리 규칙(`rpartition("@")`), 해시 형식(64자리 소문자 16진, 아니면 `reason: "malformed"`), `@`가 둘 이상인 원소의 처리를 정한다. 지금 문장으로는 redteam 기대값을 하나로 정할 수 없다.

### S4. [면제 묶기] 해시는 인터프리터 판에 따라 달라진다
* `ast.dump` 출력은 Python 판마다 바뀐다(3.13에서 `show_empty` 인자가 생기고 기본값이 빈 목록·`None` 필드를 빼도록 바뀌었다 -- 이 환경 3.14의 서명 `dump(node, annotate_fields=True,
  include_attributes=False, *, indent=None, show_empty=False)` 실측. 3.12의 `type_params`처럼 새 필드도 생긴다). 인터프리터를 올리면 묶인 면제가 전부 `hash_mismatch`가 된다(fail-closed라 누수는
  아니지만, 진행 중 card는 재승인이 필요하다).
* 고칠 것: 계약에 "해시는 gate 인터프리터(`$PY`, 3.14)의 `ast.dump` 기본 인자로 잰다"를 적고, 승인 범위 설명에 '인터프리터 판 변경 시 재승인'을 적는다. test-author의 독립 계산도 같은 인터프리터에서 한다.

### S5. [면제 묶기] exempt 결과는 `--out`에 적히지 않는다
* 지금 `main`은 `exempt`일 때 `results.append` 뒤 `continue`라 `--out` append(WP-11)를 건너뛴다(375~377행). 계약 1의 "결과 레코드에 `def_hash`를 담는다"가 어느 출력인지 모호하다 --
  `--out`에도 적는다고 정하면 그 결함도 같이 고쳐진다.

### S6. [범위 정책] 지운 문장만 있는 변경은 실질 대상이 `early_return` 하나다 -- 그리고 "지금 규칙과 차이 없음"은 틀린 문장이다
* 문장 삭제·`else`/`elif`/`except` 절 삭제만 한 변경: 새 문장·머리 변경이 없다(블록 필드는 머리 지문에서 빠지므로 `orelse`를 지워도 `If` 머리는 같다) → T1·T2·T4가 비고 T5 하나만 남는다.
  `early_return`은 그 함수를 부르는 거의 모든 test가 죽인다.
* 계약 5·실측 4의 "지운 문장: 지금 규칙도 변이가 없다 -- 차이 없음"은 정확하지 않다. 지금 규칙은 삭제로 동작이 바뀐 **남은 문장**(예: `x = clamp(x)`를 지운 뒤의 `return f(x)`)을 변이한다.
  좁히면 이것이 빠진다.
* T4는 T1·T2 영역의 조상만 본다 -- 삽입 지점을 감싸는 조건은 대상이지만 삭제 지점을 감싸는 조건은 아니다(비대칭).
* 고칠 것: 삭제 지점을 '바뀐 영역'으로 두어 T4(감싸는 제어문)를 적용하고, 같은 블록에서 삭제 지점 바로 뒤 문장을 대상에 넣는다. 아니면 이 몫을 결정 질문 '선택지 2가 놓치는 것'에 명시한다.

### S7. [범위 정책] redteam (c) `enclosing-guard-survivor`는 적힌 대로는 만들 수 없다
* "`if g:`의 `g` 뒤집기" -- 도구에는 진리값 부정 연산자가 없다. `cmp_flip`은 `ast.Compare`에만 걸린다. 맨 이름 `g`면 그 `If`의 변이는 `stmt_delete` 하나뿐이다.
  `if a < b:`처럼 비교식으로 고쳐 쓴다.

### S8. [범위 정책] 이동(G1)과의 관계에 사실 오류가 있고, 계약끼리 부딪친다
* 실측 8의 "계획서 533행 이동 규칙… 해시가 같으면 여전히 대상 0"과 `v3_scope_systemic.md` §2의 "Phase 3 이동 card는 계획 규칙으로 이 문제가 없다"는 지금 도구 기준으로 거짓이다. `main`은
  같은 경로의 base만 비교하고, 새 파일이면 `base_src = None`이라 그 파일의 def가 전부 대상이 된다(359~364행). `draft_p3_g1.spec.v3.md` 11~14행도 같은 사실을 적었다(구현 안 됨,
  엔진 4파일 상한 V3 대상 def 473·변이 15,677).
* G1 계약 4 "나머지 대상 선택은 지금과 같다(같은 입력에서 `changed_defs`와 같은 결과)"는 범위 card가 먼저 병합되면 성립하지 않는다. 범위 card 계약 2 "base에 같은 qualname이 없는 def는 본문
  전체"는 G1 뒤에는 "MOVED 단위는 빼고"가 붙어야 한다.
* 고칠 것: 두 문장을 고치고, 두 게이트 card의 병합 순서와 나중에 병합하는 card가 고칠 계약 문장을 결정 질문의 '선택하면 일어나는 일'에 적는다.
* 묶기와의 관계(참고, 결함 아님): 옮기면 id의 모듈 부분이 바뀌므로 묶인 면제는 따라가지 않는다(fail-closed). 해시가 같은 다른 모듈의 def로 새지도 않는다(id에 모듈이 들어 있다).

### S9. [범위 정책] `not_targeted`는 test 공백의 크기가 아니다
* 대상 밖 변이는 **실행하지 않고** 수만 센다(계약 4). 그래서 백로그는 '어느 변이가 사는지'를 모르고, 대부분 죽을 변이까지 포함한 수를 받는다. "조용히 버리지 않는다"와 "기존 test 공백
  백로그 입력"은 과장이다.
* 고칠 것: (i) 표현을 "실행하지 않은 변이 수(공백 아님)"로 고치거나, (ii) 판정에 쓰지 않는 선택 실행 모드(예: `--report-untargeted`)를 두어 백로그가 생존 id를 받게 한다.
  아울러 묶기 card 계약 3의 "이번 실행의 변이 id"에 `not_targeted` id가 드는지 정한다.

### S10. [결정 질문] 중립성과 완결성 보완
1. "먼저 알릴 것(결정 없이 진행 -- 강화)"인데 같은 문단 끝에 "승인 기록 한 건은 필요하다"가 있다. design 05 §2(판정 기준 소유 = 사용자)에 따라 **승인 요청**이다. "승인 요청(강화 -- 거부
   집합이 넓어짐)"으로 쓴다.
2. 표에 **'놓치는 결함' 열**이 없다. 놓치는 것이 권고 문단에만, 선택지 2에 대해서만 있다. 열을 더한다 -- 1: 추가로 놓치는 것 없음(비용만 큼). 2: 바뀐 값이 흘러드는 바뀌지 않은 문장,
   삭제만 한 변경(S6), def 머리만 바꾼 변경(B2를 고치기 전). 3: 2와 같고 이름 한 단계 흐름만 덮음(두 단계 이상·속성·컨테이너 경유는 놓침).
3. "3은 … 그 몫도 대부분 기존 공백이다"는 측정하지 않은 주장이다(D1에 더해진 330개의 생존 여부를 재지 않았다). 지우거나 잰다.
4. 선택지 1의 시간: 상한 122 h는 '전부 생존' 가정이라 부풀려진 값이다. 확정 생존 298개는 인벤토리 전체를 돌아야 하므로 면제하지 않으면 298 × 177~192 s ≈ **15 h가 하한에 더해진다**
   (≈3.4 h + 15 h). 이 현실적 하한이 판단에 더 쓸모 있다.
5. 묶기 뒤의 운영 비용을 적는다: 승인한 def를 재시도에서 고치면 면제가 풀려 **시도마다 재승인**이 필요하다(의도된 동작이지만 사용자 부담). S2의 B34·`load_topology` 10개도 적는다.
6. B2·S6을 고친 뒤의 N2 수치는 다시 재야 한다(머리 변경 → 본문 전체 규칙이 들어가면 B26-1 176이 늘 수 있다).

### S11. [두 card 공통] 수치를 다시 낼 스크립트가 남아 있지 않다
* `scope_measure.py`·`covplug.py`·`cov_analyze.py`·`hash_anchor.py`는 `C:/g52`에 있었고 그 폴더는 지워졌다(실측: 없음). `_drafts`에는 `b26_v3_*` 셋만 있다. 사용자에게 결정을 묻는 N1/N2/D1 수치,
  확정 생존 298/75, 해시 앵커를 아무도 다시 낼 수 없다(작성자≠검증자 원칙).
* 해시 앵커 두 개는 이 검토에서 다시 쟀다: `load_topology` `c22bdd32278748f4…`, `save_instance_json` `11a55c19fc03d7cc…`(`7535799`·`b7765b0` 모두) -- card와 일치.
* 고칠 것: 네 스크립트와 출력을 `_drafts`로 옮긴다.

---

## Minor

* M1 [묶기] "HEAD의 decision 기록 10개" → 실측 **11개**(u38-jsonschema, f4, u01, u39, c2, c9-ic11, ic3-v3-exempt, c9-v4-exempt, u02, p4-scan-exempt, restore-unwired-until-6a).
  `20260923-v4-decision-exempt`는 `target_kind: diff`다. 원소 26개는 일치(실측).
* M2 [묶기] 승인 소비자: `merge_gate.parse_approval_header`는 `@` 원소를 통과시키고(비지 않음만 검사), `target_list`는 다른 곳에서 쓰지 않는다. V4 `test_lint`·V7 `reachability`는 `in` 집합
  비교라 `@` 원소가 어떤 id와도 같지 않다. `weakening_diff.approved_hashes`는 `target_kind: diff`만 읽는다 → 모두 영향 없음(확인). 다만 card의 소비처 목록에 다섯째 읽기
  `tests/tools/engine_dup_scan.py`(decision `target`을 직접 파싱, 집합 비교 -- 영향 없음)를 더한다.
* M3 [묶기, 기존] `_approved_ids`는 머리 블록만이 아니라 **파일 전체**에서 `target: `로 시작하는 줄을 읽는다(본문 줄도 원소가 된다). 이 card 범위 밖이지만 묶기 뒤에도 남는 위조 경로다 -- 백로그.
* M4 [묶기, 기존] 같은 qualname의 def가 둘인 경우(`@x.setter`, 조건부 정의): `changed_defs`의 `bmap`은 마지막 것만 남고 변이 id가 겹친다. 묶기 해시로 일부 구분되지만 대상 선택은 여전히
  틀릴 수 있다 -- 백로그.
* M5 [범위] `SequenceMatcher`는 최장 공통 부분열(LCS)이 아니다(Ratcliff-Obershelp). '참조 알고리즘'이 아니라 **규범**으로 정한다. 같은 지문의 문장이 반복되면 어느 사본이 '새 문장'인지가
  알고리즘에 따라 갈리고, 그러면 대상 경로도 갈린다 → redteam은 지문이 겹치는 문장을 피하거나 규범 알고리즘으로 기대값을 정한다.
* M6 [범위] T4 '조상'에 중첩 def의 바깥 def가 드는지, T5 '머리 변경'이 def 머리를 포함하는지(B2)를 정의한다. 맞출 트리가 docstring을 지운 def인지 원본 def인지도 정한다(docstring 추가는
  새 문장으로 잡히지만 `mutants`가 docstring의 `stmt_delete`를 내지 않아 무해하다).
* M7 [범위] 계약 1의 '서식·주석·docstring만 바뀐 def는 대상이 아니다'는 맞다(해시 동일). 바뀌지 않은 문장을 옮기기만 한 경우, 지역 변수 이름 바꾸기, 표현식 문장 안의 컴프리헨션 변경은
  모두 그 문장이 '새 문장'이 된다(보수 쪽 -- 확인함, 문제 없음).

---

## 이 검토에서 확인한 것(결함 아님)

* 묶기 방향 자체(id + def 해시, 해시 없으면 fail-closed)는 맞다. `load_topology`에 대해 "어떤 앵커도 다시 적용되지 않는다"는 논리(승인한 형태 = 지금 base → 대상이 되는 순간 해시가 다르다)는 맞다.
  B1만 고치면 B26-1 → B34 619개 누수와 C8 `save_instance_json` 4개 누수가 모두 닫힌다.
* 계약 8 (b)·(c)·(d)는 정해진 구성으로 판정할 수 있다((c)는 X가 유일한 생존 변이라는 조건이 이미 있다). (a)는 S1의 조건을 더하면 판정할 수 있다.
* 범위 card 계약 7 (a)·(b)·(d)·(e)는 구성으로 판정할 수 있다((e)는 반복 대상 식에 산술·비교가 있어야 한다). (c)는 S7을 고쳐야 한다.

## 실측 스크립트(삭제 전 내용 요지)

* `C:/g56/docshift.py` -- `mutate_changed.mutants`·`def_hash`·`_get` import. docstring만 다른 두 def의 해시가 같음과 `stmt_delete` 경로별 문장이 다름을 출력(B1 표).
* `C:/g56/deco.py` -- `@functools.lru_cache(maxsize=128)` def의 모든 변이를 `_replace_def`에 넣어 원본과 AST를 비교. 데코레이터 `const±` 2개가 NOOP(B2).
* 그 밖에는 읽기 전용 명령만 썼다: `reachability._approved_ids(HEAD)` 26원소, P9 `changed_defs(7535799, b7765b0)`, 두 def 해시, DF-36 판정 기록 V3 basis, redteam V 케이스 키.
