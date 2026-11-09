---
id: 20260930-v3-changed-stmt-scope
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v3-changed-stmt-scope
---
## 의도

**판정 기준의 적용 범위를 줄이는 게이트 변경(약화)이다. 사용자 결정 2026-10-01 A1-b "② N2"(def 머리 변경은 (b) 좁은 판)와 같은 날 A1-b 정정 "규칙을 안내에 맞게 넓힘"으로 승인됐다**
(승인 기록 `20260930-v3-changed-stmt-scope`, 범위 설명에 "약화 승인"). 병합 순서: 면제 묶기 card `20260930-v3-exempt-binding`(강화) **뒤**, B26-1 앞, Phase 3 G1(`20260930-p3-gate-move-aware`) 앞.
이 card의 base는 묶기 card 병합본이다 -- 도구 `main`의 면제 판정(묶기 card 계약 1~4)과 출력 키(`survivor_bindings`·`exempt_ignored`)가 이미 있다고 보고 계약 4·5를 그 위에 적는다.

V3(`tools/gates/mutate_changed.py`)는 지금 **AST 해시가 바뀐 def의 본문 전체**를 변이한다. 엔진 def는 수백~천 줄이라 몇 줄을 고친 card도 그 def의 기존 문장 전부가 병합 조건이 된다.
B28 병합 뒤에는 도구가 실제로 돌고 기준 실행 실패는 `ERROR`라, 기존 문장의 생존 변이가 그대로 V3 FAIL이다(`_drafts/v3_scope_systemic.md` §1).

이 card: 해시가 바뀐 **기존 def**에서 V3 대상을 **바뀐 문장**, 그것을 **감싸는 제어문**, **바꾸거나 지운 문장 자리 바로 뒤 문장**, **바뀌거나 지운 문장이 바꾸는 이름을 같은 블록 뒤쪽에서 읽는 문장**
(반복문 본문이면 그 본문의 모든 문장), **def 머리가 바뀌면 그 자기 필드(기본값·데코레이터 인자·주석)와 바뀐 매개변수를 읽는 문장**, 그리고 **항상 `early_return`**으로 좁힌다
(그래서 대상 변이가 0개인 바뀐 def는 없다). 새 def는 본문 전체(지금 그대로). 좁힌 밖의 변이는 **실행하지 않고** 수와 id만 출력에 싣는다(`not_targeted`). 그 수는 'test 공백의 크기'가 아니라
'이번 판정에서 실행하지 않은 변이 수'다(대부분은 돌리면 죽을 수 있다).

**놓치는 것(약화의 범위, 승인 기록 범위 설명과 같은 문장)**: 해시가 바뀐 기존 def에서 ① 바뀌지 않은 문장의 기존 test 강도(대상 밖 변이는 실행하지 않는다), ② 바뀌거나 지운 문장이 바꾼 값이
**다른 블록**(바깥 블록, 다른 절, 뒤 복합문의 안쪽 블록)에 있는 바뀌지 않은 문장으로 흐르는 경우 -- 블록 끝에서 지운 절의 뒤 영향 포함, ③ 값이 이름을 **두 단계 이상** 거쳐 흐르는 경우 --
매개변수 값이 다른 이름을 거쳐 흐르는 문장, 호출한 함수 안의 부작용 포함. 같은 블록 안에서 이름 한 단계로 흐르는 문장은 위치(바로 뒤인지)와 무관하게 대상이다(계약 1 T6).

### 약화인가 -- 원문 대조

design 05 §10 V3 행(317행):
> ① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것 ② 연산자: … ⑤ 살아남은 변이가 있으면 FAIL.

계획 N4.2 V3 행(839행):
> 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것. … 살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만.

design 05 §2 표 'V3~V7' 행: 판정 기준 소유 = `사용자`.

판단: 원문은 대상 단위를 **def**로 정하고 그 def의 변이가 하나라도 살면 FAIL이다. 문장 단위로 좁히면 지금 규칙이 죽이라고 요구하는 변이(B26-1 card v4 모의 head에서 2,442 중 2,141, 옛 시뮬레이션 head에서 2,472 중 2,178 -- '작성 전 실측' 1)가
판정에서 빠져 게이트가 거부하는 경우의 집합이 줄어든다. N0.4 '기준 약화' 8패턴(V5, test diff 대상)의 문자 그대로에는 들지 않지만 **판정 기준의 적용 범위를 줄이는 게이트 변경이므로 약화로 다루고
사용자 승인을 받았다**(DEC-40 취지 -- 약화는 매 건 사용자 승인).

약화를 받은 근거: V3의 목적은 DEC-38 "test의 독립성은 결과(V3, V4)로 검사한다" -- **이 변경을 위해 쓴 test가 이 변경의 코드를 실제로 판정하는가**다. 바뀌지 않은 문장의 생존 변이는
그 card의 test가 아니라 **기존 test의 강도**를 잰다. 그리고 그 일부는 어떤 test로도 실행되지 않는 줄이라 card마다 확정 생존이다('작성 전 실측' 3: B26-1 대상 def base 본문 2,376개 중 298개).

## 관찰 가능한 계약

용어: "블록 필드" = `body`·`orelse`·`finalbody`·`handlers`·`cases`. "지문" = `ast.dump(노드, include_attributes=False)`. "머리" = 블록 필드를 빈 목록으로 바꾼 노드의 지문.
"복합문" = 블록 필드 중 비지 않은 문장 목록이 있는 문장·`except` 절·`case` 절(중첩 def·class 포함). "자기 필드" = 복합문의 블록 필드 밖 필드(`test`·`iter`·`target`·`items`·`type`·`name`·`args`·
`decorator_list` 등). "문장 S의 몫" = S가 단순문이면 S의 부분 트리 전체, 복합문이면 자기 필드 안 변이 + S 자신의 `stmt_delete` + (S가 `except` 절이면) 그 `except_body_delete`.
"문장 S가 이름 n을 읽는다" = S가 단순문이면 부분 트리 전체에, 복합문이면 자기 필드 안에 `Name(id=n, ctx=Load)`가 있다.
"문장 R이 바꾸는 이름" = R 안(단순문과 새·지운 복합문은 부분 트리 전체, 머리 변경 복합문은 base·head 양쪽의 자기 필드)의 ⓐ `Name`(`Store`·`Del`)의 id, ⓑ `Attribute`·`Subscript`(`Store`·`Del`) 대상의 맨 앞 `Name` id
(`self.mode = …` → `self`, `d[k] = …` → `d`), ⓒ 메서드 호출 `a.b(…)`(`func`가 `Attribute`인 `Call`)의 맨 앞 `Name` id(`out.append(x)` → `out`), ⓓ `except … as e`의 `e`.
맞추는 트리는 base·head 소스를 `ast.parse`한 def 노드 **원본**이다(docstring을 지우지 않는다 -- 변이 경로가 이 트리에서 나온다. docstring을 더하면 '새 문장'이 되지만 도구는 docstring에 변이를
만들지 않으므로 대상 수가 늘지 않는다).

1. **대상(해시가 바뀐 기존 def)**. base def와 head def의 같은 블록 필드 목록을 지문으로 맞춘다. 맞춤은 **규범 알고리즘** `difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()`
   (Ratcliff-Obershelp -- 최장 공통 부분열과 다를 수 있다. 같은 지문의 문장이 반복되면 어느 사본이 '새 문장'인지가 이 알고리즘으로 정해진다). `equal`은 바뀌지 않음, `insert`의 head
   원소는 **새 문장**, `delete`의 base 원소는 **지운 문장**이고 그 자리(head 목록에서 `j1`)가 **삭제 지점**이다. `replace` 구간에서는 head 원소를 앞에서부터 차례로 보며, 복합문이면 같은 구간의 아직 짝 없는 base 원소 중
   종류가 같고 머리가 같은 복합문을, 없으면 종류가 같은 복합문을(후보가 여럿이면 base 목록에서 가장 앞의 것) 짝으로 삼아 **머리 변경**(머리가 다를 때) 여부를 적고 블록 필드로 내려가 같은 절차를 되풀이한다. 짝이 없는 head 원소는 새 문장,
   짝이 없는 base 원소는 지운 문장이고 그 삭제 지점은 구간 끝(head `j2`)이다. def 자신의 머리(인자·기본값·주석·키워드 전용 표시·데코레이터·반환 주석·`type_params`)가 다르면 **def 머리 변경**이다.
   **바뀐 매개변수** = base·head 매개변수 이름의 대칭차 ∪ 종류(위치 전용·일반·`*args`·키워드 전용·`**kwargs`)·위치(위치 전용·일반 매개변수는 둘을 이은 위치 인자 순번, 키워드 전용은 그 목록 안 순번)·기본값 지문·주석 지문이 다른 이름.
   "바뀐 영역" = 새 문장, 머리 변경 복합문, 지운 문장. 변이(연산자·경로는 지금 그대로)가 대상인 조건:
   * T1 변이 노드가 새 문장의 부분 트리 안(그 문장 자신의 `stmt_delete` 포함).
   * T2 머리 변경 복합문의 몫.
   * T3 def 머리 변경일 때: def 자기 필드(기본값·데코레이터 인자·주석) 안의 변이 + 바뀐 매개변수 이름을 읽는 문장의 몫(def 안 어느 블록이든).
   * T4 T1·T2·T6 영역과 **삭제 지점**을 감싸는 모든 복합문(조상)의 몫. 조상은 대상 def 자신을 빼고, 대상 def와 그 영역 사이의 중첩 def·class를 포함한다(삭제 지점의 조상 = 그 블록을 가진
     복합문과 그 위).
   * T5 `early_return`: 해시가 바뀐 기존 def에서는 **항상**(조건 없음).
   * T6 (가) 삭제 지점 바로 뒤 문장(같은 블록 head 목록의 `j` 번째, 있으면)의 몫, 그리고 (나) 바뀐 영역 R마다, **R과 같은 블록**(head 목록)에서 R 뒤에 오는 문장 중 R이 바꾸는 이름을 읽는 문장의
     몫. '뒤' = 새 문장·머리 변경 복합문은 head 위치 `j`보다 큰 위치, 지운 문장은 삭제 지점 `j` 이상. 그 블록이 반복문(`for`·`async for`·`while`)의 `body`이면 위치와 무관하게 그 블록의
     R 아닌 모든 문장(다음 회차로 흐름). 뒤 복합문의 안쪽 블록에 있는 문장은 '같은 블록'이 아니다(복합문 자신은 자기 필드로 판단).
   바뀌지 않은 문장만 옮기거나 들여쓰기만 바꾼 것(감싸던 `if`를 없앰 등)은 새 문장이다(보수 쪽). 지역 변수 이름 바꾸기·표현식 문장 안의 컴프리헨션 변경도 그 문장이 새 문장이 된다.
   서식·주석·docstring만 바뀐 def는 지금처럼 대상이 아니다(① 해시 동일). 실수 상수의 표기만 바뀐 문장(`0.5` → `0.50`)은 지문이 같아 바뀌지 않은 문장이다(그 상수 변이의 값은 표기 단위에서 나와
   달라지지만 대상 밖 -- 그 def의 다른 곳이 바뀌어 대상이 된 경우).
2. **대상 변이 하한**: 해시가 바뀐 기존 def마다 대상 변이는 1개 이상이다(T5). 인벤토리가 비면 그 변이는 생존이다(아래 4) -- 그래서 **바뀐 def에 닿는 test가 하나도 없으면 항상 FAIL**이다
   (def 머리만 바꾼 동작 변경 포함).
3. **대상(새 def)**: base 같은 경로에 같은 qualname이 없는 def는 본문 전체(지금 규칙 그대로). 이 card는 Phase 3 이동 card G1(`20260930-p3-gate-move-aware`)보다 **먼저** 병합된다(A2 승인 -- B26-1·B34를
   Phase 3보다 먼저, A1 순서 -- 묶기 → 범위 → B26-1). G1 card가 자기 계약 4에 "def 안의 변이 선택은 `20260930-v3-changed-stmt-scope` 계약 1 그대로"를 더한다(백로그 B45 -- G1 초안 v7 계약 4에 반영됨,
   G1 spec card 커밋 때 확인).
   옮긴 def(해시 동일)는 두 card 모두에서 대상이 아니다.
4. **판정**: 대상 변이만 실행하고, 대상 변이 중 생존이 있으면 FAIL(exit 1). 인벤토리 없음 → 생존(지금과 같음). **대상 밖 변이는 면제 판정을 하지 않는다**(`not_targeted`가 먼저 -- 결과는
   `not_targeted`이고 `exempt`·`exempt_ignored`에 들지 않는다). 대상 변이의 면제는 `20260930-v3-exempt-binding` 규칙 그대로(그 card의 '이번 실행의 변이 id' = 대상 변이).
   변이 하나의 처리 순서: ① 대상 판정(계약 1·3) → 대상 밖이면 `not_targeted`(실행·면제 판정·인벤토리 생존 판정 없음) ② 대상이면 묶기 card의 면제 판정(`exempt` 또는 `exempt_ignored` 항목)
   ③ `exempt`가 아니면 지금처럼 실행(인벤토리 없음 → 생존). def마다의 기준 실행(인벤토리 test가 변이 없는 코드에서 통과하는지)은 지금 그대로다(대상 변이가 항상 1개 이상이라 생략할 def가 없다).
5. **대상 밖 출력**: 대상 밖 변이는 **실행하지 않고** `--out`에 `{"id": …, "result": "not_targeted"}`(키 순서 그대로, 도구가 변이를 만드는 순서대로 -- 대상 변이 레코드와 섞여)로 적는다. 출력 JSON은 묶기 card 뒤 키(`tool`, `verdict`, `targets`,
   `mutants`, `killed`, `survivors`, `survivor_bindings`, `exempt_ignored`) 뒤에 이 순서로 `not_targeted`(수 -- 실행하지 않은 변이 수이며 생존 수가 아니다), `targets_by_def`
   (`{"<파일>::<qualname>": {"targeted": n, "not_targeted": m, "deleted_statements": k, "def_header_changed": bool}}`, `<파일>`은 `targets`의 저장소 상대 경로, 키는 도구가 def를 처리한 순서)를 더한다. `mutants`(= 결과 레코드 수)는
   **대상 변이 수**다(`not_targeted` 레코드는 결과 목록에 넣지 않고 `--out`에만 적는다). 새 def는 `targeted` = 전체, `def_header_changed` = `false`. 판정에는 쓰지 않는다. 오케스트레이터는 `--out`의
   `not_targeted` id 목록을 기존 test 강도 백로그에 '돌려 보지 않은 변이'로 넘긴다(생존 여부는 모른다).
6. **지운 문장**: 지운 문장 자체에는 변이가 없다(지금도 없다). 지운 동작의 판정은 T4(감싸는 제어문)·T6(바로 뒤 문장과 같은 블록 뒤쪽의 사용)·T5와 spec card의 red-green 증거(V1·V2)가 맡는다.
   남는 공백(의도 절 '놓치는 것' ②): 블록 끝에서 지운 문장(예: `else` 절 통째 삭제)은 같은 블록에 뒤 문장이 없고, 지운 값을 쓰는 문장이 다른 블록에 있으면(예: `if` 뒤의 `return y`) 대상 밖이다.
7. **무동작**: 기존 redteam V3 케이스 `v3_survivor/`, `attacks/28-v3-gmid-options/`, `attacks/31-v3-git-history/`는 모든 단계가 base에 없던 새 def(`rt_engine.rt_scale`)를 더하는 구성이라 대상 집합이 지금과
   같고, 공격 26(없는 리비전 `rtbad1`·`rtbad2` -- 대상 선택 전 ERROR 경로)·27f(도구 소스 AST의 광범위 `except` 검사)는 대상 선택에 닿지 않는다 -- exit·관찰이 base와 같다. `attacks/34-v3-exempt-binding/`은 묶기 card 계약 9의 공통 구성(X는 바뀐 문장 안 또는 `early_return`, (c)의 head def는 모든 문장이 base와 다름)으로 X와 (c)의 모든 변이가
   대상 집합 안이다 -- exit와 기대 조각·관찰이 이 card 병합 전과 같다(test-author가 케이스별로 확인한다).
8. **새 redteam 케이스** `tools/gates/redteam/attacks/35-v3-changed-scope/`(번호는 design v4 D-18 배정 35, 합성 저장소, V 케이스). **공통 구성**: 각 attack은 겨냥한 변이 X가 **대상 변이 중 유일한 생존**이다
   (나머지 대상 변이는 그 단계의 test가 모두 죽인다 -- 구성으로 정한다). 그래서 그 단계가 겨냥한 규칙(T1·T2·T4·T6 등)을 빠뜨린 구현에서는 X가 `not_targeted`가 되어 exit 0이다(판별력).
   기대 출력은 `message_contains`에 쓸 **정확한 JSON 조각**이고, `<X>`·`<n>`은 test-author가 계약 1을 구성에 손으로 적용해 정한 변이 id·정수다(피검 도구로 만들지 않는다).
   (a) `unchanged-stmt-survivor`(control) -- base def에 약한 test로 생존하는 문장 S가 있고(S는 바뀐 문장 C 바로 뒤 문장이 아니고, C와 다른 블록에 있거나 C가 바꾸는 이름을 읽지 않으며, C의 조상도 아니다), head가 같은 def의
       C만 바꾸며 C의 변이·`early_return`은 모두 죽는다 → exit 0, 조각 `"verdict": "PASS"`, `"survivors": []`, `"not_targeted": <n>`. 관찰 `"observe": "out_jsonl"`(묶기 card 계약 9의 rt.py 동작)
       → `observed_equals` = `{"lines": <대상 수 + n>, "by_result": {"not_targeted": [<대상 밖 id 오름차순>]}}`. base 도구 exit 1(S 생존) -- **red**.
   (b) `changed-stmt-survivor`(attack) -- head가 바꾼 문장 C 안의 변이 X가 유일 생존 → exit 1, 조각 `"verdict": "FAIL"`, `"survivors": ["<X>"]`.
   (c) `enclosing-guard-survivor`(attack) -- 바꾼 문장 C를 감싸는 바뀌지 않은 `if a < b:`의 비교 뒤집기 X(`cmp_flip`)가 유일 생존 → exit 1, 조각 `"survivors": ["<X>"]`(T4). (도구에는 진리값 부정
       연산자가 없어 맨 이름 조건 `if g:`로는 만들 수 없다.)
   (d) `unwrapped-stmt`(attack) -- 감싸던 `if`를 없애 들여쓰기만 바뀐 문장 안의 변이 X가 유일 생존 → exit 1, 조각 `"survivors": ["<X>"]`(새 문장).
   (e) `header-only-change`(attack) -- `for` 머리(반복 대상 식에 산술이나 비교가 있는 것)만 바꾸고 본문 불변, 머리의 변이 X가 유일 생존 → exit 1, 조각 `"survivors": ["<X>"]`(T2).
   (f) `header-default-bool`(attack) -- def 머리의 기본값만 `strict=False` → `strict=True`로 바꾸고 그 def에 닿는 test가 없다 → exit 1, 조각 `"verdict": "FAIL"`, `"mutants": <대상 수>, "killed"`(뒤 키까지 붙인다 -- 부분 문자열
       대조라 `"mutants": 2`만이면 `"mutants": 20`~`29`에도 맞는다. 키 순서는 계약 5로 고정)와 대상 변이 id마다 `"<id>"` 하나씩(순서를 묻지 않는다 -- test-author는 도구 소스를 보지 않으므로 생성 순서를 기대값으로 쓰지 않는다)
       (T5·T3의 대상 변이가 인벤토리 없음으로 생존. 구성: 본문에서 `strict`를 읽는 문장이 하나면 그 문장의 몫 + `early_return` -- 정확한 목록은 test-author가 계약 1로 정한다).
   (g) `delete-then-use`(attack) -- 같은 블록에서 `x = clamp(x)`만 지우고 바로 뒤 `return f(x)`의 `stmt_delete` X가 유일 생존(test가 반환값을 보지 않음) → exit 1, 조각 `"survivors": ["<X>"]`(T6 가).
   (h) `decorator-mutant-applied`(control, 계약 9) -- 데코레이터를 더한 def(`@functools.lru_cache(maxsize=128)`, def 머리 변경 → T3 자기 필드)와 `f.cache_info().maxsize == 128`을 보는 test →
       데코레이터 상수 ±1 변이가 실제로 적용되어 죽고 exit 0, 조각 `"verdict": "PASS"`. base 도구는 데코레이터 변이가 소스에 반영되지 않아(NOOP) 생존 → exit 1 -- **red**.
   (i) `same-block-later-use`(attack, 2차 검토 사례 11·14 꼴) -- `mode = "fast"` → `mode = "exact"`만 바꾸고, 바뀌지 않은 문장 하나(`LOG.append(x)` 등 `mode`를 읽지 않는 문장)를 건너
       같은 블록의 `if mode == "exact":`의 비교 뒤집기 X가 유일 생존 → exit 1, 조각 `"survivors": ["<X>"]`(T6 나). 승인 당시 정의(T6 = 바로 뒤 문장만)라면 X가 대상 밖 → exit 0.
   (j) `loop-carried-use`(attack) -- `for` 본문에서 뒤쪽 문장 `acc = x + 1`만 `acc = x + 2`로 바꾸고, 같은 본문 앞쪽의 바뀌지 않은 `out.append(acc - 1)` 안 변이 X(상수 ±1 등)가 유일 생존 → exit 1,
       조각 `"survivors": ["<X>"]`(T6 나의 반복문 규칙).
   (k) `cross-block-not-targeted`(control, 승인한 약화의 경계 고정) -- `if` 본문 안의 `y = x * 2` → `y = x * 3`만 바꾸고, 바깥 블록 뒤의 바뀌지 않은 `return y + 1` 안 변이 Y가 test로 죽지 않는다
       (나머지 대상 변이는 모두 죽는다) → exit 0, 조각 `"verdict": "PASS"`. 관찰 `out_jsonl` → `by_result.not_targeted`에 Y가 든다(`observed_equals`로 목록 전체). 지금 도구 exit 1(Y 생존) -- red.
       이 단계가 실패하면(구현이 다른 블록까지 넓히면) 승인 범위와 다른 규칙이다 -- 넓히는 것은 별도 card.
   rt.py 동작 추가 없음(묶기 card의 `out_jsonl` 관찰을 쓴다).
9. **데코레이터 변이 적용(도구 결함 수정)**: `_replace_def`가 def의 **첫 데코레이터 줄부터** `end_lineno`까지를 변이된 def(데코레이터 포함)의 `unparse`로 바꾼다. 지금은 `fn.lineno`(def 줄)부터 바꾸고
   `decorator_list`를 비워 원래 데코레이터 줄을 남기므로 `decorator_list` 안 변이가 소스에 반영되지 않는다(NOOP -- 확정 생존, 거짓 FAIL 쪽). 계약: `decorator_list` 안 변이마다 바꾼 소스의
   AST가 원본과 다르다.
10. **문서**: design 05 §10 V3 행 ①을 "① 대상 = diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는 base와 문장 단위로 맞춘 바뀐 문장·
    감싸는 제어문·바꾸거나 지운 문장 자리 바로 뒤 문장·바뀌거나 지운 문장이 바꾸는 이름을 같은 블록 뒤쪽(반복문 본문이면 그 본문 전체)에서 읽는 문장·def 머리가 바뀌면 그 자기 필드(기본값·데코레이터
    인자·주석)와 바뀐 매개변수를 읽는 문장, 그리고 `early_return`(정의: spec card `20260930-v3-changed-stmt-scope` 계약 1). 대상 밖 변이는 실행하지 않고 수와 id를 출력한다(판정 제외)"로,
    계획 N4.2 V3 행 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것"을 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의 바뀐 문장과 그 주변(정의: spec card `20260930-v3-changed-stmt-scope`), 새 def는 전체
    (대상 밖 변이는 실행하지 않고 id를 출력)"로 고친다. 두 문구는 묶기 card가 고친 ⑤·면제 문구와 겹치지 않는 부분만 바꾼다. 모듈 docstring ①도 같은 뜻으로(code-author). N4.2의 이 칸은
    `plan_tables_hash` 입력이 아니다(`v_intro`만 -- `merge_gate.py` 123~133·158~168행).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 8 (a)가 base 도구에서 exit 1(바뀌지 않은 문장 S의 생존으로 FAIL) -- red, 병합본에서 exit 0 -- green. (h)·(k)도 base exit 1(데코레이터 NOOP 생존, 다른 블록 Y 생존) → 병합본 exit 0.
(b)~(g)·(i)·(j)는 좁힌 뒤에도 거부가 남는지 보이는 attack(base·병합본 모두 exit 1 -- '게이트가 실제로 거부하는가' WP-02)이고, X가 유일 생존이라 해당 규칙을 빠뜨린 구현에서는 exit 0이다. design 05 §18.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py` V 케이스, `base` 사전 → `head` 사전 이력). 어느 문장이 바뀌었는지와 어느 변이가 사는지가 케이스 구성(base·head 소스와 test)으로 정해진다. 기대 exit·출력 조각은
이 card 계약 문장. 대상 판정 기대값은 피검 도구로 만들지 않는다(계약 1의 정의를 test-author가 구성으로 적용 -- 케이스는 같은 지문의 문장을 반복하지 않게 만든다, 계약 1의 규범 알고리즘).

## 거부해야 할 입력

바뀐 문장·감싸는 제어문 머리·들여쓰기만 바뀐 문장·머리만 바뀐 복합문·지운 문장 바로 뒤 문장·같은 블록 뒤쪽에서 바뀐 이름을 읽는 문장·반복문 본문 앞쪽에서 바뀐 이름을 읽는 문장의 생존 변이 → exit 1
(계약 8 (b)~(e)·(g)·(i)·(j)). def 머리만 바꾸고 test가 닿지 않는 변경 → exit 1(계약 8 (f)). 새 def의 생존 변이 → exit 1(`v3_survivor` 그대로).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

새 def만 있는 변경, def 전체를 새로 쓴 변경 -- 대상 집합이 지금과 같다(기존 redteam V3 케이스와 34, 계약 7).

## 재현할 수치

없음(아래 비용은 결정 재료이지 판정 기대값이 아니다).

## 결정 필요 항목

* **사용자 결정 완료**: 2026-10-01 A1-b "② N2 (Recommended)"(def 머리 변경은 (b) 좁은 판)와 A1-b 정정 "규칙을 안내에 맞게 넓힘 (Recommended)"(T6를 '같은 블록 뒤쪽에서 바뀐 이름을 읽는 문장 전부'로).
  승인 기록 `20260930-v3-changed-stmt-scope`(`target_kind: diff`, 이 card + interface card + design 05 §10 V3 ① + 계획 N4.2 V3 문구). 범위 설명에 "판정 기준 적용 범위 축소(약화) 승인"과
  의도 절 '놓치는 것' 문장을 그대로 적는다(원문 인용은 승인 기록에).
* 기각한 대안(2026-10-01 결정 질문 `draft_v3_decision_question.md`): 선택지 1(지금 규칙 유지), 2a(def 머리가 바뀌면 본문 전체 -- B26-1 1,309), 3(이름 한 단계 의존을 def 전체에서 -- B26-1 399).
  경위·옛 정의·옛 수치는 history(`v3_cards_revision_log.md` → 문서 커밋 때 history H 절).
* 백로그(오케스트레이터): B45 G1 초안 계약 4 문장(계약 3), B46 두 규칙 공통의 기존 한계(아래 '작성 전 실측' 4), 대상 밖 변이 판정 모드(`--report-untargeted` -- 판정에 쓰지 않는 실행으로
  '돌려 보지 않은 변이'를 '생존 id'로 바꾸기, 별도 card 후보).

## 작성 전 실측

(측정 2026-10-01, gate `master` HEAD `7535799`(엔진 소스 = cd64170). 저장소 쓰기 없음, scratch `C:/g69`(`git archive 7535799` 사본, 끝나면 삭제). 스크립트·출력 사본 `wt/_drafts/v3_scripts/`
(재현 방법 `README.txt`). 시뮬레이션 head는 `_drafts/b26_v3_measure.py`의 `build_b26`를 그대로 썼다(`v3_scripts/sim_head.py`). P9 실제는 `git show 7535799/b7765b0`,
B34 좁힌 초안은 `v3_scope_classify.py`의 `build_b34`(`draft_b34.spec.md` v2 2차 '코드를 바꾸는 것' 사이트 1·2·3·11·11b -- 그 card의 `changed_defs` 4개·변이 55와 일치). 이 card의 정의(계약 1)는
`v3_scope_widen.py`(`v3_scope_classify.classify`에 T6 나를 더한 것, 맞춤 결과가 원래 분류기와 같음을 단언). 도구 `mutate_changed`의 `changed_defs`·`mutants`·`_get`·`_path_nodes`·`inventory`와
`reachability.iter_defs`·`build_graph`만 읽기 전용으로 import, 도구 `main`은 돌리지 않음. 인벤토리 시간·실행 줄 = 같은 HEAD 사본 전체 test 1회(junit, 796 passed·2 failed(사본에 `.git` 없음, ts6 두 건)·
15 xfailed, 309.8 s)의 기록을 재사용(`v3_scripts/out/junit_base.xml`·`executed_lines.json`, auditor 측정 재사용 규칙 -- 엔진 소스 동일). 수치 출력 `v3_scope_widen.txt`/`.json`.)

**재측정 2026-10-01, gate `master` `0f23786`**(착수 키트 `_drafts/v3scope_kit/`, scratch `C:/g109` -- 격리 복제본 `repo`(origin 없음, 빈 hooksPath)에 모의 커밋을 만들고 끝나면 삭제. 저장소 쓰기 없음).
`7535799..0f23786` 사이 `tools/` 변경 0, 엔진 소스는 P9 병합(`93b18db`)뿐 -- 도구 사실 문장은 그대로다. 대상 분류는 계약 1 문장만 보고 새로 쓴 **독립 프로토타입**(`v3scope_kit/scope_proto.py`,
위 분류기를 import·복사하지 않음)으로 다시 쟀고, 도구 `main`과 같은 경로(`git diff --name-only --no-renames --diff-filter=AM` → `_is_source` → `changed_defs` → `mutants` → 변이 id)를 탔다
(`measure_b26.py`). 결과는 아래 1·2의 모든 수와 같고, 변이 id 집합도 위 분류기와 대칭차 0(B26-1 v4·review2 head, N2b·N2w 모두), 적대 21건 변이별 불일치 0(`adv21_proto.py`).

1. **대상 변이 수(시뮬레이션·실제 head).**

   | card | 바뀐 def(머리 변경) | 지금(def 전체) | 승인 당시 N2(T6 = 바로 뒤만) | **이 card(T6 넓힘)** |
   |---|---|---|---|---|
   | P9 실제(`6bf510b..93b18db`, 실제 P9 병합 -- `b7765b0`은 버려진 1차 병합, 같은 수) | 2(0) | 28 | 12 | **12** |
   | **B26-1 card v4 head**(정본 -- `_drafts/draft_b26_1.spec.md` v4: 인계 9·10b·13·B40, 사이트 10·14는 B35. 모의 base = `0f23786` + B34 코드) | 32(새 def 1) | 2,442 | 235 | **301** |
   | B26-1 review2 head(인계 9·10·10b·13·14·B40, 같은 모의 base) | 32(새 def 1) | 2,437 | 265 | **330** |
   | B26-1 옛 시뮬레이션(`7535799` + `build_b26` -- 승인 질문의 228이 이 head) | 31(20, 새 def 1) | 2,472 | 228 | **294** |
   | B34 좁힌 초안(`0f23786` → B34 코드) | 4(0) | 55 | 10 | **10** |

   * **B26-1 수치는 v4 head 301**(N2b 235 + 넓힌 T6 66)이다. 사용자에게 간 수의 흐름: 승인 질문 228(옛 시뮬레이션, N2b) → A1-b 정정 뒤 294(옛 시뮬레이션, 넓힘) → B26-1 card v4 head 301
     (사이트 10·14를 B35로 넘긴 판; 넘기기 전 review2 head면 330). v4 def별 넓힘 몫: `propose_device_roles_gap_fill` 34 → 52, `_branch_composite_pair` 3 → 15, `run_matching_safety_with_finger_growth`
     11 → 19, `_composite_collapse_for_crossover` 5 → 10, `refine_…` 13 → 17, `load_topology` 12 → 16, 그 밖 +1~2(`v3scope_kit/out/measure_b26.txt`).
   * 옛 시뮬레이션 B26-1 +66의 def별(승인 당시 → 이 card): `propose_device_roles_gap_fill` 30 → 48, `_branch_composite_pair` 3 → 15, `run_matching_safety_with_finger_growth` 11 → 19,
     `refine_differential_and_mirror_relations` 10 → 14, `load_topology` 12 → 16, `_composite_collapse_for_crossover` 5 → 10, 그 밖 10개 def +1~2. B26-1의 def 머리 변경 20개는 모두 키워드 전용
     `rails` 추가이고, `rails`를 읽는 문장은 대부분 이미 새 문장이다.
   * 기각한 대안 참고(같은 시뮬레이션): 선택지 2a 1,309, 선택지 3 399.
2. **시간(직렬, 도구 그대로).** 하한 = 대상 변이 × 5 s(pytest 기동, 첫 test에서 죽음), 상한 = Σ 대상 변이 × 그 def 인벤토리 전체 시간(전부 생존). **현실 하한** = 하한 + 'base에서 어떤 test도
   실행하지 않은 줄'의 대상 변이(아래 3, 반드시 생존 → 인벤토리 전체를 돈다) × 인벤토리 시간. 인벤토리 시간 187~202 s.

   | card | 지금 | 승인 당시 N2 | **이 card** |
   |---|---|---|---|
   | P9 실제 | 2.3분 ~ 1.5 h | 1.0분 ~ 0.6 h | **1.0분 ~ 0.6 h** |
   | B26-1 v4 head(정본) | -- | 19.6분 ~ 12.4 h, 현실 하한 0.64 h | **25.1분 ~ 16.0 h, 현실 하한 0.89 h** |
   | B26-1 옛 시뮬레이션 | 3.4 h ~ 129 h, 현실 하한 19.2 h | 19분 ~ 12.0 h, 현실 하한 0.6 h | **24.5분 ~ 15.6 h, 현실 하한 0.9 h** |
   | B34 좁힌 초안 | 4.6분 ~ 1.0 h | 0.8분 ~ 0.3 h | **0.8분 ~ 0.3 h** |

   * v4 head 상한·현실 하한은 `0f23786` 트리의 인벤토리(P10 test 포함)에 `7535799` junit 시간을 붙였다 -- 시간 기록이 없는 인벤토리 test 4개는 0초로 셌다(상한이 조금 작다).
   * 인벤토리 0 변이(실행 없이 생존): B26-1 `_metric_kcl_residual`(v4 head 대상 6) -- B26-1 card의 이름 직접 호출 test(초안 'V3 계획' 4)로 0이 된다.
   * B34 좁힌 초안은 그 card가 55개 전부를 실제로 돌려 죽였다(`draft_b34.spec.md` 'V3 계획' -- 55/55, 면제 0). 이 card와 무관하게 통과 가능.
3. **확정 생존 -- 어떤 test도 실행하지 않는 줄의 변이**(사본 전체 test 1회를 `sys.monitoring` LINE 이벤트로 기록 -- `covplug.py`, 실행 줄 합집합. 변이 노드의 줄 범위(복합문은 머리 줄,
   `early_return`은 첫 문장 줄)에 실행된 줄이 하나도 없으면 '실행 안 됨'. test가 띄운 하위 프로세스 안의 실행은 잡지 않는다):
   * base 본문 기준: B26-1 대상 def(중첩 `_evaluate_row_split` 제외) 2,376 중 **298**, 넓은 B34(v1, 18 def) 1,395 중 75, 좁힌 B34(4 def) 68 중 6, P9 `kcl_series_union` 0.
   * head 대상 기준(head 줄을 같은 base 줄로 대응, 새 줄은 판정 불가로 뺌): B26-1 옛 시뮬레이션 지금 **306**(판정 불가 119) / 승인 당시 N2 6 / **이 card 9**, B26-1 v4 head 승인 당시 N2 6 / **이 card 9**,
     P9 실제 0, B34 좁힌 초안 0.
   * C8이 면제한 `load_topology` 기존 공백 10개(B8)는 B26-1 시뮬레이션 head에서 `body[11]`·`body[26]` → `body[14]`·`body[29]`로 경로가 밀린다(`v3_c8_in_b26.txt`) -- 지금 도구로도 면제되지 않고
     (묶기와 무관), 이 card에서는 대상 밖이다.
4. **놓치는 것 -- 적대적 동작 변경 21건 재측정**(`v3_adv21.py` → `v3_adv21.txt`. 2차 검토 `review2_v3_cards.md` §2의 21건을 그 표의 설명대로 다시 썼다 -- 검토 scratch가 지워져 소스가
   검토와 같지 않아 변이 수는 다르다. 사례마다 weak test(base·head 통과, 변경을 관찰하지 않음)·strong test(base 실패·head 통과), 변이는 도구 `mutants` + 계약 9 판 치환, 실행 = exec 후 test 호출.
   'weak 판정 PASS' = 변경을 관찰하는 test 없이 병합 가능, '변경 고유' = strong만 죽이는 대상 변이 수. 형식: 대상 / weak 판정 / 변경 고유):

   | # | 동작 변경 | 지금 | 승인 당시 N2 | **이 card** | 분류 |
   |---|---|---|---|---|---|
   | 1c | bool 기본값 → 별칭 `s = strict` → 바뀌지 않은 `if s and x < 0` | 12 / FAIL / 3 | 2 / PASS / 0 | **2 / PASS / 0** | 놓침 ③(매개변수 → 다른 이름 → 사용, 두 단계) |
   | 4b | 기본값 lambda `key=lambda r: r[0] → -r[0]` | 9 / FAIL / 1 | 4 / PASS / 0 | **4 / PASS / 0** | 놓침 ③(매개변수 `key` → `s = sorted(…, key=key)` → `return s[0][1]`, 두 단계) |
   | 6 | 문장 순서 바꾸기 | 10 / FAIL / 4 | 6 / FAIL / 0 | **10 / FAIL / 4** | 덮음(넓힌 T6) |
   | 11 | `mode` 값 변경, 한 문장 건너 같은 블록 `if mode == 'exact'` | 16 / FAIL / 4 | 3 / PASS / 0 | **5 / FAIL / 2** | **덮음(T6 나)** |
   | 11b | 11과 같되 사용하는 `if`가 바로 뒤 | 16 / FAIL / 4 | 4 / FAIL / 2 | **4 / FAIL / 2** | 덮음 |
   | 12 | 문장 삽입 `y = max(y, 0)` | 12 / FAIL / 3 | 4 / FAIL / 3 | **8 / FAIL / 3** | 덮음 |
   | 14 | `neg` 값 변경, 두 문장 뒤 같은 블록 `if neg:` | 7 / FAIL / 2 | 3 / PASS / 0 | **4 / FAIL / 1** | **덮음(T6 나)** |
   | 15 | `else` 절 통째 삭제(뒤 `return y * 3`) | 15 / FAIL / 3 | 5 / FAIL / 0 | **5 / FAIL / 0** | 놓침 ②(다른 블록 -- weak FAIL은 변경과 무관한 `x > -1` 생존) |

   * 나머지 13건(1a·1b·2·3a·3b·4a·5·7·8·9·10a·10b·13)은 지금 규칙과 이 card의 weak 판정이 같다. 그중 1a·2·3a·3b·7·8·9·10b는 **두 규칙 모두** 변경을 관찰하지 않는 test로 PASS다 -- 연산자 집합
     (bool·문자열·이름·예외 종류 변이 없음)과 'def만 본다'(모듈 수준 상수·별칭 변경은 변이 0)의 기존 한계이고 이 card의 약화가 아니다(백로그 B46). 합계 대상 지금 179 / 승인 당시 N2 87 / 이 card 98.
   * 경계 확인(`v3_widen_boundary.py` → `v3_widen_boundary.txt`): 반복문 본문 앞쪽 `out.append(acc - 1)`은 뒤쪽 `acc` 변경으로 대상(4개 더함), `if` 안 변경 뒤 바깥 `return y + 1`은 대상 밖(②),
     `self.mode = …` 변경 뒤 같은 블록 `if self.mode > 1`과 새 `out.append(x)` 뒤 `return len(out) + 1`은 대상(속성·메서드 수신자 이름), `a` 변경 → `b = a` → `if b > 1`의 `if`는 대상 밖(③).
   * 그래서 이 card가 지금 규칙보다 더 놓치는 사례는 모두 의도 절 '놓치는 것' ②·③ 안이다(1c·4b = ③, 15 = ②). 승인 당시 정의가 안내 밖으로 놓친 같은 블록·인접하지 않은 흐름(11·14)은 덮인다.
   * 독립 프로토타입 재측정(`0f23786`, `v3scope_kit/out/adv21_proto.txt`): 21건 표가 위와 칸마다 같고(합계 179 / 87 / 98), 경계 사례 3건을 더 쟀다 -- 반복문 앞쪽 사용(계약 8 (j) 꼴) 지금 15 / N2b 6 /
     이 card 10, 다른 블록 사용(계약 8 (k) 꼴) 16 / 9 / 9(넓힘 몫 0), 두 단계 흐름 17 / 6 / 6(넓힘 몫 0).
5. **중간안 평가(기각, 결정 질문 때 제시).** def 전체 + 시간·변이 수 예산 + 표본 추출(표본 밖이 난수로 빠지는 약화, 예산은 근거 없는 상수), def 전체 + 자동 기준선 차분(base에서도 사는 변이 자동 면제 --
   약화이고 비용이 지금 이상). **약화 없는 가속**(변이마다 그 줄을 실행하는 test만, 빠른 test 먼저, 병렬)은 어느 규칙과도 함께 가능한 별도 게이트 card 후보다 -- 확정 생존은 가속으로 없어지지 않는다.
6. **이름 충돌.** `ls tools/gates/redteam/attacks/` 마지막 `31-v3-git-history`, 32~35 없음(번호는 D-18 배정). 출력 키 `not_targeted`·`targets_by_def`·`def_header_changed`:
   `grep -rn "not_targeted\|targets_by_def\|def_header_changed" tools/ docs/` 0건(`0f23786` 재확인).
7. **쓰기 경로.** `tools/gates/mutate_changed.py` = gmid-code-author(design 10 C11 행), `tools/gates/redteam/**` = gmid-test-author(C10 행), design 05·계획 문구 = 오케스트레이터 문서 커밋.
8. **계획서 소비자.** 계획서 533행 이동 규칙("무변경 증명 = … 해시 동일 … 해시가 같은 함수는 V3 대상에서 뺀다")은 **지금 도구에 구현돼 있지 않다**: `main`은 같은 경로의 base만 비교하고
   새 파일이면 `base_src = None`이라 그 파일의 def가 전부 대상이 된다(`mutate_changed.py` 359~364행, `changed_defs` 90~95행 -- `0f23786` 줄 번호. 묶기 card가 같은 파일을 고치므로 병합 뒤 줄 번호는 착수 때 다시 잰다). 그 구현이 G1 card다(계약 3 -- G1이 뒤). `grep -rn "본문 전체\|def 전체"
   docs/01-plan docs/02-design` 중 V3 관련 0건(걸린 1건은 design 05 318행 V4 서술) -- 고칠 곳은 계약 10의 두 행뿐.
9. **미배선.** 새 def(맞춤·대상 분류)를 만들면 `mutate_changed.main`이 부른다. 계약 9는 기존 `_replace_def`를 고친다(새 함수 없음).
10. **도구 결함 재현**(`v3_probes.txt`): 데코레이터 def `@functools.lru_cache(maxsize=128)`의 `const±:decorator_list[0].keywords[0].value` 2개가 지금 `_replace_def`로는 NOOP(바뀐 소스 AST = 원본),
    첫 데코레이터 줄부터 바꾸는 판으로는 NOOP 아님. 2차 검토 사례 10a·이번 재측정 10a에서 계약 9 판 치환으로 그 변이가 실제로 적용되어 strong test가 죽인다.
11. **계약 1의 해석 자리 확정**(2026-10-01 재측정 때 독립 프로토타입을 쓰며 문장이 정하지 않은 곳 -- 계약 1에 적었다): `replace` 구간 짝 후보가 여럿이면 base 목록에서 가장 앞의 것, 새·지운 복합문이
    바꾸는 이름은 부분 트리 전체, 매개변수 '위치'는 위치 전용·일반 매개변수는 둘을 이은 위치 인자 순번, 키워드 전용은 그 목록 안 순번이다. '같은 종류 목록 안 순번'으로 읽으면
    `def f(a, /, b)` → `def f(a, z, /, b)`에서 `b`가 받는 위치 인자가 바뀌어도 `b`를 읽는 문장이 대상 밖이 된다(review3 S1 -- 승인 범위보다 좁음). 그 구성에서 고친 정의는 대상 5/14(`b`를 읽는
    `if`의 몫 4 포함), 옛 정의는 1/14(`early_return`만)이고, 키워드 전용 앞에 일반 매개변수를 더하는 의미 불변 변경(`def f(a, *, k=1)` → `def f(a, z=0, *, k=1)`)에는 `k`를 더하지 않는다
    (시그니처 전체 순번이면 `k`를 읽는 몫 4를 더함 -- `v3scope_kit/probe_s1_posonly.py` → `out/probe_s1_posonly.txt`).
    **어느 해석이든 수가 같다**의 근거: 해석 자리 3개(짝 후보 순서·새 복합문이 바꾸는 이름의 범위·매개변수 위치)의 2×2×2 = 8 조합 전부로 다시 세어 B26-1 v4·review2·옛 시뮬레이션·P9·B34의
    수와 변이 id 집합이 같았다(`_drafts/review3_v3_scope.md` §1.1, 검토자 `rv_variants.py` -- 이 head들에서 해석 자리가 발동하지 않기 때문이고, 해석이 중립이라는 뜻은 아니다. 키트
    `variants.py`는 2 조합만 쟀다). 위치 정의를 고친 뒤 `measure_b26.py`를 다시 돌려도 B26-1 v4 301·P9 12·B34 10(review2 330·옛 시뮬레이션 294)이고 다섯 head 모두 변이 id 집합이 고치기 전과 대칭차 0이다(scratch `C:/g124`, `v3scope_kit/out/measure_b26.s1.json`·
    `measure_b26.s1_vs_v1_ids.txt`).
