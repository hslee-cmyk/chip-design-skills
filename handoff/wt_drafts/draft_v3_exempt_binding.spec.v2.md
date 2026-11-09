---
id: 20260930-v3-exempt-binding
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v3-exempt-binding
---
## 의도

게이트 V3(`tools/gates/mutate_changed.py`)의 **등가 변이 면제가 승인한 코드에 묶이지 않는 결함**을 고친다. 정책 질문이 아니라 결함이다(조용한 면제 = '게이트가 실제로 거부하는가' WP-02 위반).
V3 범위 정책(def 전체 대 바뀐 문장, `draft_v3_scope_policy.spec.md`)과 독립이며, 어느 정책을 택하든 먼저 병합한다.

지금 동작(HEAD 7535799 실측):
* 변이 id = `<모듈>:<함수 qualname>:<연산자>:<AST 노드 경로>`(도구 `main`의 `mid`). def 해시·card에 묶이지 않는다.
* 도구는 head 트리 `.ai/approvals/*.md` 중 머리에 `target_kind: decision`이 있는 **모든** 기록의 `target` 원소를 한 집합으로 읽고(`reachability._approved_ids`),
  변이 id가 그 집합에 있으면 실행하지 않고 `exempt`로 센다(`mutate_changed.main`, `if mid in approved`).
* 그래서 한 card에서 승인한 면제가 **뒤 card의 같은 경로 변이를 조용히 면제한다** -- 그 경로에 다른 문장이 와 있어도. 실측(`_drafts/v3_scope_systemic.md` §3):
  B26-1 시뮬레이션 head의 '닿지 않은 변이' 2,366개를 면제 목록으로 만들면 그 위에서 B34(v1 넓은 범위) 대상 def의 변이 1,402개 중 **619개**가 이미 면제된다.
* **이 누수는 실제 판정에 쓰였다(DF-36)**: 판정 기록 `.ai/verification/20260930-df36-instance-relpath.json`(커밋 `148bd6d`) V3 basis = head `b29be01`에서 변이 26 중 "killed 22, **exempt 4**
  (head 트리 승인 `20260922-ic3-v3-exempt`), 생존 0". 이 4개는 C8 기록의 `save_instance_json` id다. 그런데 `save_instance_json`은 DF-36 base `070cf69`(① 해시 `9cb09766…`)에서
  head `b29be01`(`11a55c19…`)로 **바뀌었다**(그래서 V3 대상이 됐다). C8 기록 범위 설명은 "두 함수의 본문 구조가 바뀌면 이 면제는 맞지 않는다"고 적었는데, 도구는 경로만 보고 4개를 면제했다.
  auditor는 4개가 base·head에서 같은 문장(`scope_note` 분기 `body[2]`·`body[2].body[0]`, `json.dump(indent=2)` ±1)을 가리킴을 손으로 확인했다(같은 판정 기록. 이 card 재측정
  `v3_scripts/out/v3_anchors.txt`도 같음). 그래서 결과는 맞았을 수 있으나 **승인 범위 밖 면제에 기댄 PASS**다. 자동 재판정으로 뒤집히지는 않는다(`integrity.py` 행 3(나)는 옛 판
  `merge_gate.py receive`를 돌리고, `merge_gate.py`는 V3를 부르지 않는다 -- `grep` 0건). 처리: 백로그 한 줄(아래 '결정 필요 항목').

고칠 방향: **면제 원소를 (변이 id, 승인 시점 def의 '묶기 해시') 쌍으로 묶는다.** 원소 형식 `<변이 id>@<묶기 해시>`. 면제는 head의 그 def 묶기 해시가 원소의 해시와 같을 때만 적용한다.
* **묶기 해시는 design 05 §10 V3 ①의 해시와 다르다.** ①(대상 선택, 도구 `def_hash`)은 docstring을 지운 트리를 해시한다. 그런데 변이 경로(`body[i]` 등)는 docstring을 **지우지 않은** 트리에서
  만든다(`mutants(fn, …)`). docstring 한 줄을 더하거나 빼면 ① 해시는 같고 경로는 한 칸씩 밀린다 -- 같은 해시에서 같은 id가 다른 문장을 가리킨다(검토 B1, 재측정
  `v3_scripts/out/v3_probes.txt`: `def f(x): y = clamp(x); log(y); return y`에 docstring만 더하면 ① 해시 같음, `stmt_delete:body[1]`이 `log(y)` → `y = clamp(x)`). 그래서 묶기 해시는
  **변이 경로를 정하는 바로 그 트리**(docstring·데코레이터를 포함한 head def 노드 원본)를 해시한다. 정의는 계약 머리.
* card 묶음은 따로 두지 않는다: V3는 base와 ① 해시가 다른 def만 변이하므로, 승인한 def 형태가 병합된 뒤 그 def를 바꾸는 card에서는 ① 해시가 달라지고(그래서 대상이 되고) 묶기 해시도 달라져
  면제가 풀린다. 같은 card의 재시도에서 def를 바꾸면 -- docstring만 바꿔도 -- 묶기 해시가 달라져 풀린다. 묶기 해시가 같으면 변이 경로가 가리키는 노드가 승인한 형태와 같다
  (같은 트리, 같은 경로). 그래서 면제가 그 문장에 정확히 적용된다.
* 승인 기록 머리 형식(`merge_gate.parse_approval_header`, `00-common` §8.2)은 바꾸지 않는다 -- decision `target`은 쉼표로 나눈 비지 않은 원소 목록이고 `@`는 이미 허용된다. 새 키가 없으므로
  스키마·redteam 15-records 영향이 없다.
* **기존 승인 기록은 고치지 않는다**(N3.12.2: 기존 기록 수정·삭제 거부). 이행 규칙 = 해시 없는 V3 모양 원소는 **적용하지 않고 출력에 싣는다**(fail-closed).
  잃는 것: **앞으로의 card 기준으로는 없다**('작성 전 실측' 1). 다만 이미 내려진 DF-36 V3 PASS는 위 누수에 기댔다 -- 그 판정은 바뀌지 않고(재판정 경로에 V3 없음) 백로그로 확인한다.
  암묵 앵커(승인 커밋 시점의 def 해시)는 쓰지 않는다 -- 실측으로 틀린 앵커다(같은 절).
* 강화다(면제되는 변이 집합이 줄고 거부 집합이 넓어진다). 그래도 게이트 판정 기준 변경이므로(design 05 §2 표 'V3~V7' 행: 판정 기준 소유 = `사용자`) `target_kind: diff` **사용자 승인 요청**이다.

범위 밖(이 card에서 바꾸지 않는다, 근거는 '결정 필요 항목'):
* V7(`reachability.py`) 면제: 같은 읽기(`_approved_ids`)를 쓰지만 V7은 **base에 없던 def**만 판정하므로, 승인한 def가 병합되면 그 id는 다시 판정되지 않는다. 누수 조건은 '같은 qualname을
  지웠다가 다른 본문으로 다시 더함'뿐이다. 지금 V7 원소 2개(`20260930-restore-unwired-until-6a`)는 두 def가 HEAD에 있어 판정 대상이 아니다. 백로그로 넘긴다.
* V4(`test_lint.py`) 면제: 같은 부류의 누수(test id `<파일>::<test 이름>`에 묶임, test 본문 해시 미묶임)다. 그러나 V4는 바뀐 test 파일의 **모든** test를 lint하므로 기존 원소 2개
  (`20260923-c9-v4-exempt`)가 뒤 card에서 계속 필요하다 -- fail-closed 이행이 V3와 달리 무손실이 아니어서 이행 설계가 따로 필요하다. 백로그로 넘긴다.
* `reachability._approved_ids`의 반환값·동작은 바꾸지 않는다(V4·V7 소비자 불변).

## 관찰 가능한 계약

용어.
* "V3 모양 원소" = decision 승인 기록 `target` 원소 중 `@` 앞부분(아래 분리 규칙)이 `<모듈>:<qualname>:<연산자>:<경로>` 모양(연산자 ∈ `cmp_flip`, `arith`, `const+`, `const-`,
  `stmt_delete`, `early_return`, `except_body_delete`)인 것.
* **"묶기 해시"(binding hash)** = `hashlib.sha256(ast.dump(F, annotate_fields=True, include_attributes=False, indent=None, show_empty=False).encode("utf-8")).hexdigest()`(소문자 16진 64자).
  F = 변이를 만든 head 소스를 `ast.parse`한 트리에서 그 qualname의 def 노드 **원본**(docstring을 지우지 않고, 데코레이터·중첩 def·중첩 docstring 포함 -- `mutants(fn, …)`가 받는 `fn`과
  같은 노드). 중첩 def의 노드를 바깥 def의 변이로 만든 id면 F는 바깥 def다(id의 qualname = F의 qualname). `ast.dump`의 인자는 **모두 명시**한다(3.13에서 생긴 `show_empty`처럼 기본값이
  판마다 바뀌어도 출력이 따라 바뀌지 않게). 측정 인터프리터는 gate 인터프리터 `$PY`(`C:/Python314/python.exe`, 3.14.2)다. AST 노드 필드 집합이 바뀌는 Python 판 변경(예: 3.12의
  `type_params`)은 해시를 바꾼다 -- 그때 묶인 면제는 모두 `hash_mismatch`(계약 2)가 되고(fail-closed, 누수 아님) 필요한 면제는 다시 승인한다(승인 범위 설명에 적는다).
  ①의 해시(`def_hash`, docstring 제외 -- 대상 선택용)와 이름·용도가 다르다. 도구 안에서 둘을 섞지 않는다.
* **원소 분리 규칙**: 원소 문자열(앞뒤 공백 제거)에 `@`가 없으면 '해시 없는 원소'(id = 원소 전체). `@`가 정확히 하나면 `id, h = 원소.split("@")`. `h`가 정규식 `^[0-9a-f]{64}$`에 맞지 않거나
  `@`가 둘 이상이면 '형식 오류 원소'(id = 첫 `@` 앞). 변이 id에는 `@`가 들어갈 수 없다(모듈·qualname·연산자·경로 문자 집합 -- 도구 `mid` 구성).
* "이번 실행의 변이 id" = 도구가 이번 실행에서 **실행 대상으로 만든** 변이의 id(범위 정책 card `20260930-v3-changed-stmt-scope`가 병합된 뒤에는 그 card의 `not_targeted`를 뺀 것).

1. **묶인 면제 적용**: head 트리의 decision 승인 기록에 원소 `<id>@<H>`가 있고 H가 그 변이의 head def 묶기 해시와 같으면 그 변이는 실행하지 않고 결과가 `exempt`다.
   결과 레코드 `{"id": <id>, "result": "exempt", "bind_hash": H}`를 결과 목록에 넣고 **`--out`에도** append한다(지금은 `exempt`가 `continue`로 `--out` append를 건너뛴다 -- WP-11 기록 누락을
   함께 고친다).
2. **해시 불일치**: 같은 id의 원소가 모두 `<id>@<H'>`(H' ≠ head 묶기 해시)이면 면제하지 않는다 -- 변이를 정상 실행해 `killed`/`survived`로 센다. 출력 JSON `exempt_ignored`에 원소마다
   `{"id": <id>, "reason": "hash_mismatch", "approved_hash": H', "head_hash": H}`가 든다.
3. **해시 없는 원소·형식 오류 원소**: 원소의 id가 이번 실행의 변이 id와 같으면 면제하지 않는다(정상 실행). 출력 `exempt_ignored`에 `{"id": <id>, "reason": "unbound"}` 또는
   `{"id": <id>, "reason": "malformed", "element": <원소 문자열>}`이 든다. id가 이번 실행의 변이 id와 같지 않은 원소는 싣지 않는다(다른 도구의 id·다른 def의 id·대상 밖 변이).
4. **같은 id에 원소가 여럿**(시도마다 승인한 경우 등): 하나라도 계약 1에 맞으면 `exempt`이고 그 id의 다른 원소는 `exempt_ignored`에 싣지 않는다. 하나도 맞지 않으면 원소마다 계약 2·3의 항목을 싣는다.
   여러 기록에 같은 원소 문자열이 있으면 한 번만 센다.
5. **판정**: 1의 `exempt`를 뺀 변이 중 생존이 있으면 FAIL(exit 1), 없으면 PASS(exit 0) -- 지금과 같다. `exempt_ignored`는 판정을 바꾸지 않는다(정보). 2·3으로 풀린 변이가 생존하면 FAIL이다.
6. **승인에 옮길 형태 출력**: 출력 JSON에 `survivor_bindings` = 생존 변이마다 `<id>@<head def 묶기 해시>`(순서는 `survivors`와 같음)를 더한다. `survivors`는 지금 형식 그대로다(변이 id만).
7. **다른 도구 무영향**: 같은 입력에서 V4(`test_lint.py`)·V7(`reachability.py`)의 출력 JSON과 exit가 base 도구와 같다(`_approved_ids` 불변). `@`가 든 원소는 V4·V7의 어떤 id와도 같지 않다.
   `merge_gate.parse_approval_header`·`weakening_diff.approved_hashes`(`target_kind: diff`만 읽음)·`A/tests/tools/engine_dup_scan.py`(decision `target` 원소 `<path>::<rule>` 집합 비교)의 결과도 같다.
8. **무동작**: 기존 redteam V3 케이스(`v3_survivor/` attack exit 1·control exit 0, `attacks/28-v3-gmid-options/`, `attacks/31-v3-git-history/`, 공격 26·27f)와 V4 `attacks/29-v4-decision-exempt/`의
   결과가 base와 같다. 승인 기록이 없는 저장소에서 V3 출력은 새 키(`exempt_ignored` 빈 목록, `survivor_bindings`)를 빼면 base와 같다.
9. **새 redteam 케이스** `tools/gates/redteam/attacks/32-v3-exempt-binding/`(V 케이스 `v.json`, 합성 저장소, 생존 변이 집합이 구성으로 정해진 def -- 예: `v3_survivor`처럼 0 입력만 보는 test).
   승인 기록은 V 케이스의 `head`(또는 `base`) 파일 사전 안 `.ai/approvals/<id>.md` 파일로 둔다(선례 `attacks/29-v4-decision-exempt`). 원소의 해시는 아래 rt.py 자리표시자로 넣는다.
   (a) `legacy-unbound-leak`(attack) -- base 커밋에 해시 없는 원소로 변이 id X를 면제하는 decision 승인 기록이 있고, head가 그 def를 바꿔 같은 경로의 변이 X가 생존하며, **X가 그 def의 유일한
       생존 변이**다(다른 변이는 test가 모두 죽인다) → exit 1, 출력 `exempt_ignored`에 X·`unbound`. base 도구 exit 0(조용한 면제) -- **red**.
   (b) `hash-mismatch`(attack) -- 원소 `X@<바꾸기 전 def의 묶기 해시>`, head가 def를 바꿔 X가 생존 → exit 1, `exempt_ignored`에 X·`hash_mismatch`. (base 도구도 exit 1 -- 회귀 방지.)
   (c) `bound-exempt`(control) -- 원소 `X@<head def의 묶기 해시>`, X가 유일한 생존 변이 → exit 0, X의 결과 `exempt`(`--out`에도 기록). base 도구 exit 1(`@` 원소를 모른다) -- **red(green 쪽)**.
   (d) `bound-other-def`(attack) -- 원소가 다른 qualname def의 묶기 해시를 달고 있음(`X@<다른 def 묶기 해시>`) → exit 1.
   (e) `docstring-shift`(attack, 검토 B1) -- base def D0, 시도 k의 def Dk(D0과 ① 해시가 다르다)의 소스를 V3 대상 밖 경로(예: `notes/attempt_k.py`)에 두고 원소 `X@<Dk의 묶기 해시>`(X는
       Dk에서 등가 변이). head def = Dk에 docstring 한 줄만 더한 것(① 해시는 Dk와 같고 X 경로가 한 칸 밀린 다른 문장을 가리킨다), 그 X 변이가 생존 → exit 1, `exempt_ignored`에 X·`hash_mismatch`.
       (① 해시로 묶었다면 exit 0 -- 개정 전 초안의 결함. base 도구는 `@`를 몰라 exit 1이므로 red는 (a)·(c)가 맡고 (e)는 회귀 방지 단계다.)
   (f) `malformed-element`(attack) -- 원소 `X@abc`(64자 16진 아님), X 생존 → exit 1, `exempt_ignored`에 X·`malformed`.
   **rt.py 동작 추가(test-author, design 10 C10 행)**: V 케이스 파일 텍스트의 자리표시자 `@bindhash(<base|head>:<경로>:<qualname>)`를 그 케이스의 `base`/`head` 사전에 있는 `<경로>` 파일
   텍스트(다른 치환을 마친 뒤)에서 그 qualname def의 묶기 해시로 바꾼다. 계산은 표준 라이브러리 `ast`·`hashlib`만으로 위 정의대로 한다 -- **피검 도구 모듈(`mutate_changed`)을 import하지 않는다**.
   기존 `subst_str`의 `@{…}`(상태 변수)와 겹치지 않는 문법이다(`@{BINDHASH:…}`는 `subst_str`가 상태 변수 `BINDHASH`로 읽어 '치환 변수 없음'으로 실패한다 -- `rt.py` 39~48행 정규식).
   자리표시자가 없는 케이스의 동작은 그대로다.
10. **문서**: design 05 §10 V3 행 ⑤의 "등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록"을 "등가 변이 면제는 `target_kind: decision`, `target` 원소 =
    `<변이 id>@<묶기 해시>`(승인할 때 head def 노드 원본 -- docstring 포함 -- 의 `ast.dump` sha256, 정의: spec card `20260930-v3-exempt-binding`)인 승인 기록 -- head의 그 def 묶기 해시가 같을
    때만 적용. 해시가 없거나 다르거나 형식이 틀린 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다"로 고친다. 계획 N4.2 V3 행의 "등가 변이 면제는 승인 기록으로만"을 "등가 변이 면제는
    승인 기록으로만(변이 id와 그 def의 AST 묶기 해시에 묶임)"으로 고친다. `mutate_changed.py` 모듈 docstring ⑤도 같은 뜻으로(code-author). 계획 N4.2의 이 칸은 `plan_tables_hash` 입력이
    아니다(`merge_gate.plan_tables_object`는 `v_intro`·`ic_parts`·`ic_test`·`phase_order`·`write_paths`만 -- 실측).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 9 (a)는 base 도구에서 exit 0(해시 없는 면제를 경로만으로 적용), (c)는 base 도구에서 exit 1(`@` 원소를 모른다) -- 둘 다 red, 병합본 도구에서 green. design 05 §18: ⑤ 뒤 게이트 변경은
spec card(red-green, oracle (a)). (b)·(d)·(e)·(f)는 base·병합본 모두 exit 1인 회귀 방지 단계다.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py`의 V 케이스 -- `build_vrepo`가 `base` 사전으로 base 커밋, `head` 사전으로 head 커밋을 만든다)에서 생존 변이 집합이 구성으로 정해진 def를 쓴다.
승인 기록은 `head`(또는 `base`) 사전의 `.ai/approvals/<id>.md` 파일이다(V 케이스는 `_commit_case`의 `approval`·`more_approvals`·`base_files` 키를 읽지 않는다 -- `rt.py` 446·459행, `build_vrepo` 523행~).
기대 exit·출력 키는 이 card 계약 문장. **묶기 해시 기대값은 피검 도구 함수를 불러 만들지 않는다** -- test-author가 계약 머리의 정의(표준 `ast.dump` 인자 명시 + sha256)로 rt.py 자리표시자
`@bindhash(…)`(계약 9)에서 독립 계산한다. 같은 인터프리터(`$PY` 3.14)에서 계산한다.

## 거부해야 할 입력

해시 없는 원소로 면제된 변이가, 그 def가 바뀐 head에서 생존 → exit 1(계약 9 (a)). 다른 해시·다른 def의 해시·docstring만 다른 def의 해시·형식 오류 해시를 단 원소 → exit 1(계약 9 (b)·(d)·(e)·(f)).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

기존 redteam 전체(`run_all.py --phase 0.5 --mode direct`)와 `--cases 0.5`의 케이스 판정이 base와 같다(계약 9의 새 케이스 제외). 승인 기록이 없는 저장소의 V3 판정·`survivors`가 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

* **사용자 승인 요청(강화 -- 거부 집합이 넓어짐)**: 게이트 변경 승인 기록 `20260930-v3-exempt-binding`(`target_kind: diff`, 이 card + design 05 §10 V3 ⑤ + 계획 N4.2 V3 문구). 범위 설명에 적을 것:
  (i) 강화: 면제 적용 범위 축소. 기존 `20260922-ic3-v3-exempt`의 V3 원소 14개는 해시가 없어 더는 적용되지 않는다(앞으로의 card 기준 무손실 -- '작성 전 실측' 1. 이미 내려진 DF-36 V3 PASS는
  그 4개에 기댔다 -- 백로그 1).
  (ii) redteam `lib/rt.py`에 실행 동작 하나 추가(자리표시자 `@bindhash(…)`, 계약 9) -- 선례 C10(`20260923-caa970b-replay`)처럼 승인 범위에 따로 적는다.
  (iii) 묶기 해시는 gate 인터프리터(3.14)의 `ast.dump`(인자 명시)로 잰다. 인터프리터 판을 올리면 묶인 면제가 풀릴 수 있다(fail-closed) -- 그때 필요한 면제는 다시 승인한다.
  (iv) **운영 비용**: 승인한 def를 재시도에서 고치면(docstring만 고쳐도) 면제가 풀려 **시도마다 재승인**이 필요하다. 의도된 동작이다(승인한 코드와 다른 코드에 면제를 쓰지 않는다).
* 백로그(오케스트레이터가 더한다):
  1. DF-36 V3 확인: HEAD에서 `save_instance_json` 면제 id 4개(`scope_note` 분기 2, `indent` ±1 2)를 실제로 돌려 생존이면 test 보강(B8과 같은 기존 공백) 또는 묶인 면제 승인. 판정 기록은 고치지 않는다.
  2. V7 면제 원소를 def 해시에 묶기(누수 조건 = 같은 qualname 삭제 후 재추가, 지금 영향 0).
  3. V4 면제 원소를 test 함수 해시에 묶기(기존 2원소의 이행 설계 필요 -- V4는 바뀐 파일의 모든 test를 보므로 fail-closed가 무손실이 아니다).
  4. `reachability._approved_ids`는 머리 블록만이 아니라 **파일 전체**에서 `target: `로 시작하는 줄을 읽는다(본문 줄도 원소가 된다 -- 묶기 뒤에도 남는 위조 경로, 검토 M3).
  5. 같은 qualname의 def가 둘인 경우(`@x.setter`, 조건부 정의): `changed_defs`의 `bmap`이 마지막 것만 남기고 변이 id가 겹친다(검토 M4). 묶기 해시로 면제는 구분되지만 대상 선택은 틀릴 수 있다.
  6. 관찰: 도구는 중첩 def의 노드를 바깥 def 변이로도, 해시가 바뀐 중첩 def 자신의 변이로도 만든다 -- B26-1 시뮬레이션 head에서 `optimize_full_circuit_budget` 안의 `_evaluate_row_split`
     62개가 두 id로 두 번 돈다. 판정은 같고 비용만 는다.
* redteam 번호: Phase 3 G1 초안(`_drafts/draft_p3_g1.spec.md` 220행)도 `attacks/32-moved-defs/`를 쓴다. 디렉터리 이름은 달라 충돌하지 않지만(선례 `17-*` 여럿) 번호 머리가 겹친다 --
  나중에 병합하는 card가 번호를 바꾼다(이 card가 먼저 병합되는 순서면 G1 card 쪽 수정).

## 작성 전 실측

(측정 2026-10-01, gate `master` HEAD `7535799`. 저장소 쓰기 없음, scratch `C:/g60`(`git archive 7535799` 사본 + 스크립트, 끝나면 삭제). 스크립트·출력 사본은
`wt/_drafts/v3_scripts/`(재현 방법은 그 폴더 `README.txt`). `$PY` = `C:/Python314/python.exe -B`(3.14.2). 도구 함수는 저장소 `tools/gates`에서 읽기 전용 import, 도구 `main`은 돌리지 않음.)

1. **사실 문장 재측정.**
   * 도구 읽기: `mutate_changed.py` `main`의 `approved = _approved(root, ns.head)`·`if mid in approved:` → `results.append({"id": mid, "result": "exempt"})`·`continue`(375~377행 -- `--out`
     append(394~396행)를 건너뛴다), `_approved` = `rch._approved_ids(root, rev)`. `reachability._approved_ids`(180행)는 head 트리 `.ai/approvals/*.md`(이름이 `_`로 시작하는 것 제외) 중
     `---\n`으로 시작하고 `\ntarget_kind: decision\n`이 있는 기록의 `target: ` 줄을 쉼표로 나눠 합집합. 소비처 3곳: `mutate_changed._approved`(V3, 219행), `reachability.main`(V7, 233행),
     `test_lint.py` 731행(V4 규칙 (1)) -- `grep -rn "_approved_ids" tools/ skills/`. decision `target`을 따로 읽는 넷째 소비처 `A/tests/tools/engine_dup_scan.py`(102~122행, `<path>::<rule>`
     집합 비교 -- `@` 원소와 겹치지 않음).
   * 승인 기록 머리 파서: `merge_gate.parse_approval_header`는 모르는 키를 거부하고(APPROVAL_KEYS 8개), decision `target` 원소는 비지 않음만 검사한다 → `@` 원소 허용, 새 키는 불가(그래서 새 키
     대신 원소 접미사).
   * HEAD의 decision 기록 **11개**(`v3_anchors.txt`: u38-jsonschema, f4-user-approval-row, u01-test16-intent, u39-paper-target-spec, c2-extract-repro-path-line, c9-ic11-split, ic3-v3-exempt,
     c9-v4-exempt, u02-d-list, p4-scan-exempt, restore-unwired-until-6a), `_approved_ids(7535799)` 원소 **26개**, V3 모양 **14**(전부 `20260922-ic3-v3-exempt` -- `load_topology` 10,
     `save_instance_json` 4). 나머지: 결정 id 7, V4 test id 2(`20260923-c9-v4-exempt`), V7 def id 2(`20260930-restore-unwired-until-6a`), probe 스캐너 1(`20260929-p4-scan-exempt`).
     (`20260923-v4-decision-exempt`는 `target_kind: diff`라 decision이 아니다.)
   * **해시 앵커**(앞 16자, ① = `def_hash` docstring 제외, 묶기 = 계약 머리 정의) -- `v3_anchors.txt`:

     | def | 58e954c(C8 승인 커밋) | 6fe9cff(C8 병합)·070cf69 | b29be01(DF-36 병합)·cd64170·7535799·b7765b0(P9 병합) |
     |---|---|---|---|
     | `load_topology` ① | `104fac77…` | `c22bdd32…` | `c22bdd32…` |
     | `load_topology` 묶기 | `0b9eb2d6…` | `7e81d370…` | `7e81d370…` |
     | `save_instance_json` ① | `0f519721…` | `9cb09766…` | `11a55c19…` |
     | `save_instance_json` 묶기 | `043c6c88…` | `1dbcaa2d…` | `4a96ecf0…` |

   * **이행 근거(앞으로의 card 기준, 해시 없는 원소를 적용하지 않아도 잃는 것이 없다)**:
     * `load_topology`: 면제가 승인한 형태(C8 병합 `c22bdd32…`)가 지금 base다. V3는 base와 ① 해시가 다른 def만 변이하므로 뒤 card가 `load_topology`를 대상으로 삼는 순간 head ① 해시는
       `c22bdd32…`가 아니고 묶기 해시도 `7e81d370…`가 아니다 -- 어떤 앵커를 붙여도 적용되지 않는다. fail-closed와 결과가 같다.
       (참고: B26-1 시뮬레이션 head에서는 `load_topology` 본문 앞쪽에 문장이 들어가 C8 경로 10개가 이미 다른 경로가 된다 -- 지금 도구로도 면제되지 않는다(`b26_v3_measure.out.txt` leak2:
       B26-1 head 적중 4개 = `save_instance_json`뿐). 좁힌 B34(def 4개)는 `load_topology`를 대상으로 삼지 않는다 -- `v3_scope_classify.txt`.)
     * `save_instance_json`: 승인 커밋 = `0f519721…`, C8 병합 = `9cb09766…`, `b29be01`에서 `11a55c19…`로 바뀜. 승인한 형태는 이미 지나갔는데 지금 도구는 4개를 여전히 적용한다
       -- DF-36(`070cf69` → `b29be01`)에서 실제로 적용됐고(의도 절), B26-1 시뮬레이션 head에서도 4/4 적중한다(leak2). fail-closed가 C8 범위 설명과 맞다.
     * **암묵 앵커(승인 커밋의 def 해시)는 틀린 앵커다**: V3 승인 기록은 card 병합 **전**에 master에 커밋된다(`58e954c` → 병합 `6fe9cff`) -- 승인 커밋의 def는 card 전 형태(① `104fac77…`)다.
       V7 기록 `c31e0b6`에는 두 def가 아예 없다(`no-def`; 복원 병합은 `f1c4b7d`). 병합 커밋 앵커는 승인 기록에 card id가 기계 판독으로 없어 정할 수 없다.
   * **B1 재현**(`v3_probes.py` → `v3_probes.txt`): `def f(x): y = clamp(x); log(y); return y`와 docstring만 더한 판 -- ① 해시 같음(True), 묶기 해시 다름(False),
     `stmt_delete:body[1]` = `log(y)` 대 `y = clamp(x)`, `body[2]` = `return y` 대 `log(y)`. 두 판의 (연산자, 경로) 집합이 겹친다 -- ① 해시로 묶으면 밀린 문장에 면제가 적용된다.
   * `ast.dump` 서명(3.14.2 실측): `(node, annotate_fields=True, include_attributes=False, *, indent=None, show_empty=False)` -- `show_empty`는 3.13에서 생겼다(그 전 판에는 인자가 없다 --
     다른 판 인터프리터는 이 환경에 없어 출력 차이는 재지 않았다. 계약은 판 변경을 fail-closed + 재승인으로 다룬다).
   * B26-1 → B34(v1) 누수 619/1,402: `_drafts/b26_v3_leak.py`·`b26_v3_measure.out.txt`(C:/g39, cd64170) -- 재사용(auditor 측정 재사용 규칙). 엔진 소스가 HEAD와 같아 다시 재지 않았다.
   * DF-36 V3 basis(판정 기록 `checks.V3.basis`): 도구 직접 실행은 사본에 `.git`이 없어 기준 실행 ERROR, 대체 측정(`scripts/mut_def.py`, 도구 함수 그대로)으로 26 → killed 22·exempt 4·생존 0.
2. **이름 충돌.** `ls tools/gates/redteam/attacks/` 마지막 = `31-v3-git-history` → `32-v3-exempt-binding` 없음(Phase 3 G1 초안의 `32-moved-defs`와 번호 머리만 겹침 -- '결정 필요 항목').
   출력 키 `exempt_ignored`·`survivor_bindings`·`bind_hash`: `grep -rn "exempt_ignored\|survivor_bindings\|bind_hash" tools/ docs/` 0건. rt.py 자리표시자 `@bindhash(`: `grep -rn "@bindhash" tools/` 0건.
3. **원칙의 계약화.** 조용한 면제 금지 → 계약 2·3(적용하지 않은 원소를 출력에 싣는다)과 9 (a). 거부 집합이 실제로 넓어짐(WP-02) → 계약 9 (a)·(b)·(d)·(e)·(f) attack. 다른 도구 무영향 → 계약 7.
   기록 누락 금지(WP-11) → 계약 1의 `--out`. oracle 독립 → 계약 9의 rt.py 자리표시자(피검 모듈 import 금지).
4. **쓰기 경로.** `tools/gates/mutate_changed.py` = gmid-code-author(design 10 C11 행 "spec card `gate_change: yes` + 승인 기록일 때"), `tools/gates/redteam/**`(새 케이스 + `lib/rt.py` 자리표시자)
   = gmid-test-author(C10 행), design 05 §10·계획 N4.2 문구 = 오케스트레이터 문서 커밋(승인 기록이 덮는다). 설치 사본 재설치 불필요(`mutate_changed.py`는 §4.4 캐시에서 실행 -- B28 card와 같음).
5. **계획서 소비자.** `grep -rn "변이 id" docs/01-plan docs/02-design` → design 05 317행(고침), design 10 382행(C8 서술, 형식 주장 없음 -- 그대로), P9 spec card 118·168행(면제 형식 언급 -- 병합된
   기록이라 고치지 않음). agent 정의(`agents/gmid-verification-auditor.md` 41행)는 도구 이름만 -- 고칠 것 없음. 지우거나 옮기는 이름 없음.
6. **미배선.** 새 def(묶기 해시 계산, 원소 분리)를 만들면 `mutate_changed.main`이 부른다(V7 면제 불필요).
7. **기존 계약 test.** redteam `v3_survivor`·28·31·26·27f·29 -- 계약 8로 불변 판정. 기존 redteam에 V3 면제를 쓰는 케이스 없음(검토 `grep` 0건). `tests/`의 엔진 test는 도구를 부르지 않는다.
