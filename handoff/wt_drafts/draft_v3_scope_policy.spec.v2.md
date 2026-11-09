---
id: 20260930-v3-changed-stmt-scope
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v3-changed-stmt-scope
---
## 의도

**선택적 게이트 변경(사용자 결정 대기 -- `draft_v3_decision_question.md`). 판정 기준의 적용 범위를 줄이는 약화다.** 사용자가 선택지 2(또는 2a·3)를 고를 때만 이 card를 쓴다
('선택지별 대상 정의' 절). 면제 누수 수정(`draft_v3_exempt_binding.spec.md`, 강화)은 이 card와 독립이고 먼저 병합한다.

V3(`tools/gates/mutate_changed.py`)는 지금 **AST 해시가 바뀐 def의 본문 전체**를 변이한다. 엔진 def는 수백~천 줄이라 몇 줄을 고친 card도 그 def의 기존 문장 전부가 병합 조건이 된다.
B28 병합 뒤에는 도구가 실제로 돌고 기준 실행 실패는 `ERROR`라, 기존 문장의 생존 변이가 그대로 V3 FAIL이다(`_drafts/v3_scope_systemic.md` §1).

이 card: V3 대상을 **바뀐 def 안의 '바뀐 문장'과 그것을 감싸는 제어문, 지운 문장 자리의 앞뒤, 바뀐 매개변수를 읽는 문장, 그리고 새 def 전체**로 좁힌다. 해시가 바뀐 기존 def에서는
`early_return`을 **항상** 대상으로 삼는다(그래서 대상 변이가 0개인 바뀐 def는 없다 -- 검토 B2). 좁힌 밖의 변이는 **실행하지 않고** 수와 id만 출력에 싣는다(`not_targeted`). 그 수는
'test 공백의 크기'가 아니라 '이번 판정에서 실행하지 않은 변이 수'다(대부분은 돌리면 죽을 수 있다 -- 검토 S9).

### 약화인가 -- 원문 대조

design 05 §10 V3 행(317행):
> ① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것(새 def 포함) ② 연산자: … ⑤ 살아남은 변이가 있으면 FAIL.

계획 N4.2 V3 행(839행):
> 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것. … 살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만.

design 05 §2 표 'V3~V7' 행: 판정 기준 소유 = `사용자`.

판단: 원문은 대상 단위를 **def**로 정하고 그 def의 변이가 하나라도 살면 FAIL이다. 문장 단위로 좁히면 지금 규칙이 죽이라고 요구하는 변이(B26-1 시뮬레이션 head에서 2,472 중 2,244 -- 아래 N2)가
판정에서 빠져 게이트가 거부하는 경우의 집합이 줄어든다. N0.4 '기준 약화' 8패턴(V5, test diff 대상)의 문자 그대로에는 들지 않지만 **판정 기준의 적용 범위를 줄이는 게이트 변경이므로 약화로 다루고
사용자 승인을 받는다**(DEC-40 취지 -- 약화는 매 건 사용자 승인). B28 승인의 "기준 약화가 아니다" 근거는 여기서 댈 수 없다.

약화를 받을 근거(사용자 판단 재료): V3의 목적은 DEC-38 "test의 독립성은 결과(V3, V4)로 검사한다" -- **이 변경을 위해 쓴 test가 이 변경의 코드를 실제로 판정하는가**다. 바뀌지 않은 문장의 생존 변이는
그 card의 test가 아니라 **기존 test의 강도**를 잰다. 그리고 그 일부는 어떤 test로도 실행되지 않는 줄이라 card마다 확정 생존이다('작성 전 실측' 3: B26-1 대상 def base 본문 2,376개 중 298개).

### 선택지별 대상 정의(측정한 정의)

정의는 모두 **해시가 바뀐 기존 def마다** base def와 head def를 AST로 맞춘 결과(계약 1)에서 나온다. 새 def는 모두 본문 전체(지금 규칙 그대로). 공통 = T1·T2·T5·T6.
* **N2(선택지 2, 이 card의 기본)**: 공통 + T3(b) + T4.
* **N2a(선택지 2a)**: 공통 + T3(a) + T4. def 머리가 바뀌면 본문 전체(검토 B2가 적은 보수 쪽).
* **D1(선택지 3)**: 공통 + T3(b) + 이름 한 단계 데이터 의존(T7, 계약 1 끝).
* (참고 측정) N1 = 공통 + T3(b)(T4 없음). 개정 전 정의(옛 N1·N2·D1)는 '작성 전 실측' 1에 교정용으로 적었다.

## 관찰 가능한 계약

용어: "블록 필드" = `body`·`orelse`·`finalbody`·`handlers`·`cases`. "지문" = `ast.dump(노드, include_attributes=False)`. "머리" = 블록 필드를 빈 목록으로 바꾼 노드의 지문.
"복합문" = 블록 필드 중 비지 않은 문장 목록이 있는 문장·`except` 절·`case` 절(중첩 def·class 포함). "자기 필드" = 복합문의 블록 필드 밖 필드(`test`·`iter`·`target`·`items`·`type`·`name`·`args`·
`decorator_list` 등). "문장 S의 몫" = S가 단순문이면 S의 부분 트리 전체, 복합문이면 자기 필드 안 변이 + S 자신의 `stmt_delete` + (S가 `except` 절이면) 그 `except_body_delete`.
맞추는 트리는 base·head 소스를 `ast.parse`한 def 노드 **원본**이다(docstring을 지우지 않는다 -- 변이 경로가 이 트리에서 나온다. docstring을 더하면 '새 문장'이 되지만 도구는 docstring에 변이를
만들지 않으므로 대상 수가 늘지 않는다).

1. **대상(해시가 바뀐 기존 def)**. base def와 head def의 같은 블록 필드 목록을 지문으로 맞춘다. 맞춤은 **규범 알고리즘** `difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes()`
   (Ratcliff-Obershelp -- 최장 공통 부분열과 다를 수 있다. 같은 지문의 문장이 반복되면 어느 사본이 '새 문장'인지가 이 알고리즘으로 정해진다 -- 검토 M5). `equal`은 바뀌지 않음, `insert`의 head
   원소는 **새 문장**, `delete`의 base 원소는 **지운 문장**이고 그 자리(head 목록에서 `j1`)가 **삭제 지점**이다. `replace` 구간에서는 head 원소가 복합문이면 같은 구간의 아직 짝 없는 base 원소 중
   종류가 같고 머리가 같은 복합문을, 없으면 종류가 같은 복합문을 짝으로 삼아 **머리 변경**(머리가 다를 때) 여부를 적고 블록 필드로 내려가 같은 절차를 되풀이한다. 짝이 없는 head 원소는 새 문장,
   짝이 없는 base 원소는 지운 문장이고 그 삭제 지점은 구간 끝(head `j2`)이다. def 자신의 머리(인자·기본값·주석·키워드 전용 표시·데코레이터·반환 주석·`type_params`)가 다르면 **def 머리 변경**이다.
   **바뀐 매개변수** = base·head 매개변수 이름의 대칭차 ∪ 종류(위치 전용·일반·`*args`·키워드 전용·`**kwargs`)·위치·기본값 지문·주석 지문이 다른 이름.
   변이(연산자·경로는 지금 그대로)가 대상인 조건:
   * T1 변이 노드가 새 문장의 부분 트리 안(그 문장 자신의 `stmt_delete` 포함).
   * T2 머리 변경 복합문의 몫.
   * T3 def 머리 변경일 때: **(b, 기본)** def 자기 필드(기본값·데코레이터 인자·주석) 안의 변이 + 바뀐 매개변수 이름을 읽는(`Name`, `Load`) 문장의 몫(단순문은 부분 트리 전체, 복합문은 자기 필드만 보고
     판단). **(a, 선택지 2a)** 본문 전체.
   * T4 T1·T2·T6 영역과 **삭제 지점**을 감싸는 모든 복합문(조상)의 몫. 조상은 대상 def 자신을 빼고, 대상 def와 그 영역 사이의 중첩 def·class를 포함한다(삭제 지점의 조상 = 그 블록을 가진
     복합문과 그 위).
   * T5 `early_return`: 해시가 바뀐 기존 def에서는 **항상**(조건 없음).
   * T6 삭제 지점 바로 뒤 문장(같은 블록 head 목록의 `j` 번째, 있으면)의 몫 -- 지운 문장이 바꾼 값을 쓰는 다음 문장(예: `x = clamp(x)`를 지운 뒤의 `return f(x)`).
   * (선택지 3만) T7 '바뀐 영역'(새 문장 전체, 머리 변경 복합문의 자기 필드, 지운 문장 전체)이 대입하는 이름(`Store`·`Del`)을 읽거나 그 영역이 읽는 이름을 대입하는 문장의 몫(def 안 전체, 흐름 무시,
     한 단계).
   바뀌지 않은 문장만 옮기거나 들여쓰기만 바꾼 것(감싸던 `if`를 없앰 등)은 새 문장이다(보수 쪽). 지역 변수 이름 바꾸기·표현식 문장 안의 컴프리헨션 변경도 그 문장이 새 문장이 된다.
   서식·주석·docstring만 바뀐 def는 지금처럼 대상이 아니다(① 해시 동일).
2. **대상 변이 하한**: 해시가 바뀐 기존 def마다 대상 변이는 1개 이상이다(T5). 인벤토리가 비면 그 변이는 생존이다(아래 3) -- 그래서 **바뀐 def에 닿는 test가 하나도 없으면 항상 FAIL**이다
   (def 머리만 바꾼 동작 변경 포함 -- 검토 B2).
3. **대상(새 def)**: base 같은 경로에 같은 qualname이 없는 def는 본문 전체(지금 규칙 그대로). Phase 3 이동 card G1(`20260930-p3-gate-move-aware`)이 먼저 병합되면 이 문장은 "base 같은 경로에 같은
   qualname이 없고 G1 계약 4의 옮긴 def(`(경로, qualname, def_hash)` 일치)도 아닌 def는 본문 전체, 옮긴 def는 대상 아님"으로 읽는다('결정 필요 항목' -- 나중에 병합하는 card가 문장을 고친다).
4. **판정**: 대상 변이만 실행하고, 대상 변이 중 생존이 있으면 FAIL(exit 1). 인벤토리 없음 → 생존(지금과 같음). 면제는 `20260930-v3-exempt-binding` 규칙 그대로(그 card의 '이번 실행의 변이 id' =
   대상 변이).
5. **대상 밖 출력**: 대상 밖 변이는 **실행하지 않고** `--out`에 `{"id": …, "result": "not_targeted"}`로 적는다. 출력 JSON에 `not_targeted`(수 -- 실행하지 않은 변이 수이며 생존 수가 아니다)와
   `targets_by_def`(`{"<파일>::<qualname>": {"targeted": n, "not_targeted": m, "deleted_statements": k, "def_header_changed": bool}}`)를 더한다. 판정에는 쓰지 않는다. 오케스트레이터는 `--out`의
   `not_targeted` id 목록을 기존 test 강도 백로그에 '돌려 보지 않은 변이'로 넘긴다(생존 여부는 모른다).
6. **지운 문장**: 지운 문장 자체에는 변이가 없다(지금도 없다). 지운 동작의 판정은 T4(감싸는 제어문)·T6(바로 뒤 문장)·T5와 spec card의 red-green 증거(V1·V2)가 맡는다. 남는 공백: 블록 끝에서
   지운 문장(예: `else` 절 통째 삭제)은 T6 대상이 없고, 지운 값을 쓰는 문장이 다른 블록에 있으면(예: `if` 뒤의 `return y`) 대상 밖이다('작성 전 실측' 4).
7. **무동작**: 기존 redteam V3 케이스(`v3_survivor/`, `attacks/28-v3-gmid-options/`, `attacks/31-v3-git-history/`, 공격 26·27f, `attacks/32-v3-exempt-binding/`)의 exit가 base와 같다
   (모두 새 def이거나 def 전체가 바뀐 구성 -- test-author가 케이스별로 확인한다).
8. **새 redteam 케이스** `tools/gates/redteam/attacks/33-v3-changed-scope/`(합성 저장소, V 케이스):
   (a) `unchanged-stmt-survivor`(control) -- base def에 약한 test로 생존하는 문장 S가 있고, head가 같은 def의 다른 문장 C만 바꾸며 C의 변이·`early_return`은 모두 죽는다 → exit 0, 출력
       `not_targeted` ≥ 1(S의 변이). base 도구 exit 1 -- **red**.
   (b) `changed-stmt-survivor`(attack) -- head가 바꾼 문장 C의 변이가 생존 → exit 1.
   (c) `enclosing-guard-survivor`(attack) -- 바꾼 문장 C를 감싸는 바뀌지 않은 `if a < b:`의 비교 뒤집기(`cmp_flip`)가 생존 → exit 1(T4). (도구에는 진리값 부정 연산자가 없어 맨 이름 조건
       `if g:`로는 만들 수 없다 -- 검토 S7.)
   (d) `unwrapped-stmt`(attack) -- 감싸던 `if`를 없애 들여쓰기만 바뀐 문장의 변이가 생존 → exit 1(새 문장).
   (e) `header-only-change`(attack) -- `for` 머리(반복 대상 식에 산술이나 비교가 있는 것)만 바꾸고 본문 불변, 머리의 변이가 생존 → exit 1(T2).
   (f) `header-default-bool`(attack, 검토 B2) -- def 머리의 기본값만 `strict=False` → `strict=True`로 바꾸고 그 def에 닿는 test가 없다 → exit 1(T5·T3의 대상 변이가 인벤토리 없음으로 생존).
       (개정 전 정의라면 대상 변이 0개 → exit 0.)
   (g) `delete-then-use`(attack, 검토 S6) -- 같은 블록에서 `x = clamp(x)`만 지우고 바로 뒤 `return f(x)`의 `stmt_delete`가 생존(test가 반환값을 보지 않음) → exit 1(T6).
   (h) `decorator-mutant-applied`(control, 계약 9) -- 데코레이터를 더한 def(`@functools.lru_cache(maxsize=128)`, def 머리 변경 → T3 자기 필드)와 `f.cache_info().maxsize == 128`을 보는 test →
       데코레이터 상수 ±1 변이가 실제로 적용되어 죽고 exit 0. base 도구는 데코레이터 변이가 소스에 반영되지 않아(NOOP) 생존 → exit 1 -- **red**.
9. **데코레이터 변이 적용(도구 결함 수정)**: `_replace_def`가 def의 **첫 데코레이터 줄부터** `end_lineno`까지를 변이된 def(데코레이터 포함)의 `unparse`로 바꾼다. 지금은 `fn.lineno`(def 줄)부터 바꾸고
   `decorator_list`를 비워 원래 데코레이터 줄을 남기므로 `decorator_list` 안 변이가 소스에 반영되지 않는다(NOOP -- 확정 생존, 거짓 FAIL 쪽). 계약: `decorator_list` 안 변이마다 바꾼 소스의
   AST가 원본과 다르다.
10. **문서**: design 05 §10 V3 행 ①을 "① 대상 = diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는 base와 문장 단위로 맞춘 '바뀐 문장'·
    감싸는 제어문·지운 문장 자리의 앞뒤·바뀐 매개변수를 읽는 문장과 `early_return`(정의: spec card `20260930-v3-changed-stmt-scope` 계약 1). 대상 밖 변이는 실행하지 않고 수와 id를 출력한다(판정 제외)"로,
    계획 N4.2 V3 행 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것"을 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의 바뀐 문장(정의: spec card `20260930-v3-changed-stmt-scope`), 새 def는 전체
    (대상 밖 변이는 실행하지 않고 id를 출력)"로 고친다. 모듈 docstring ①도 같은 뜻으로(code-author). N4.2의 이 칸은 `plan_tables_hash` 입력이 아니다(`v_intro`만).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 8 (a)가 base 도구에서 exit 1(바뀌지 않은 문장 S의 생존으로 FAIL) -- red, 병합본에서 exit 0 -- green. (h)도 base exit 1(데코레이터 NOOP 생존) → 병합본 exit 0. (b)~(g)는 좁힌 뒤에도
거부가 남는지 보이는 attack(base·병합본 모두 exit 1 -- '게이트가 실제로 거부하는가' WP-02). design 05 §18.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py` V 케이스, `base` 사전 → `head` 사전 이력). 어느 문장이 바뀌었는지와 어느 변이가 사는지가 케이스 구성(base·head 소스와 test)으로 정해진다. 기대 exit·출력 키는
이 card 계약 문장. 대상 판정 기대값은 피검 도구로 만들지 않는다(계약 1의 정의를 test-author가 구성으로 적용 -- 케이스는 같은 지문의 문장을 반복하지 않게 만든다, 계약 1의 규범 알고리즘).

## 거부해야 할 입력

바뀐 문장·감싸는 제어문 머리·들여쓰기만 바뀐 문장·머리만 바뀐 복합문·지운 문장 바로 뒤 문장의 생존 변이 → exit 1(계약 8 (b)~(e)·(g)). def 머리만 바꾸고 test가 닿지 않는 변경 → exit 1(계약 8 (f)).
새 def의 생존 변이 → exit 1(`v3_survivor` 그대로).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

새 def만 있는 변경, def 전체를 새로 쓴 변경 -- 대상 집합이 지금과 같다(기존 redteam V3 케이스, 계약 7).

## 재현할 수치

없음(아래 비용은 결정 재료이지 판정 기대값이 아니다).

## 결정 필요 항목

* **사용자 결정(대기)**: V3 범위 정책 -- `draft_v3_decision_question.md` 선택지 1(지금 규칙 유지)·2(이 card, N2)·2a(이 card의 T3를 (a)로)·3(이 card의 계약 1에 T7). 승인 기록
  `20260930-v3-changed-stmt-scope`(`target_kind: diff`, 이 card + design 05 §10 V3 ① + 계획 N4.2 V3 문구). **범위 설명에 "판정 기준 적용 범위 축소(약화) 승인"을 명시한다.**
* 선택지 1이면 이 card는 쓰지 않는다. 그때도 **계약 9(데코레이터 변이 NOOP)는 지금 규칙의 결함**이므로 그 몫만 떼어 별도 게이트 card(강화 쪽 -- 거짓 생존 제거, 대신 진짜로 사는 데코레이터 변이는
  드러난다)로 낸다. 실제 소스 `topology_library.py` 248행 `@functools.lru_cache(maxsize=256)` -- 그 def를 바꾸는 card는 지금 확정 생존 2개를 받는다(검토 B2). B26-1은 V3 전수로 가고, 확정 생존
  ('작성 전 실측' 3)은 test 보강 또는 card별 변이 id 면제(누수 수정 뒤 해시에 묶인)로 처리한다.
* **G1(Phase 3 이동 card)과의 순서**: 두 게이트 card는 모두 `mutate_changed.py`의 대상 선택을 바꾼다. 나중에 병합하는 card가 고칠 문장 -- 이 card가 나중이면 계약 3(위에 적은 G1 읽기),
  G1이 나중이면 G1 계약 4의 "나머지 대상 선택은 지금과 같다(같은 입력에서 `changed_defs`와 같은 결과)"에 "def 안의 변이 선택은 `20260930-v3-changed-stmt-scope` 계약 1 그대로"를 더한다.
  옮긴 def(해시 동일)는 두 card 모두에서 대상이 아니다. redteam 번호: 이 card `33-…`, 면제 묶기 `32-…`, G1 초안 `32-moved-defs` -- 나중에 병합하는 card가 번호를 바꾼다.
* 대상 밖 변이 판정(선택, 별도 card 후보): 판정에 쓰지 않는 실행 모드(예: `--report-untargeted`)를 두면 백로그가 '돌려 보지 않은 변이'가 아니라 '생존 id'를 받는다(검토 S9 (ii)). 이 card는
  (i) 표현 정정만 한다.

## 작성 전 실측

(측정 2026-10-01, gate `master` HEAD `7535799`(엔진 소스 = cd64170). 저장소 쓰기 없음, scratch `C:/g60`(`git archive 7535799` 사본, 끝나면 삭제). 스크립트·출력 사본 `wt/_drafts/v3_scripts/`
(재현 방법 `README.txt`). 시뮬레이션 head는 `_drafts/b26_v3_measure.py`의 `build_b26`·`build_p9`를 그대로 썼다(`v3_scripts/sim_head.py` -- 경로만 C:/g60). P9 실제는 `git show 7535799/b7765b0`,
B34 좁힌 초안은 `v3_scope_classify.py`의 `build_b34`(`draft_b34.spec.md` v2 2차 '코드를 바꾸는 것' 사이트 1·2·3·11·11b, docstring 제외 -- 그 card의 `changed_defs` 4개·변이 12·8·6·29 = 55와 일치).
도구 `mutate_changed`의 `changed_defs`·`mutants`·`_get`·`_path_nodes`·`inventory`와 `reachability.iter_defs`·`build_graph`만 읽기 전용으로 import, 도구 `main`은 돌리지 않음.
인벤토리 시간 = 사본 전체 test 1회의 junit(test별 시간, 796 passed·2 failed(사본에 `.git` 없음, ts6 두 건)·15 xfailed, 309.8 s)에서 인벤토리 test 시간 합. 수치 출력 `v3_scope_classify.txt`/`.json`.)

1. **정의별 대상 변이 수(시뮬레이션·실제 head).**

   | card | 바뀐 def(머리 변경) | 지금(def 전체) | 옛 N1 / 옛 N2 / 옛 D1 | **N2(기본)** | N2a | N1 | **D1** |
   |---|---|---|---|---|---|---|---|
   | P9 실제(`b7765b0`) | 2(0) | 28 | 4 / 4 / 5 | **12** | 12 | 8 | **11** |
   | P9 시뮬레이션 | 1(0) | 24 | 3 / 3 / 4 | **5** | 5 | 5 | **8** |
   | B26-1 시뮬레이션 | 31(20, 새 def 1) | 2,472 | 139 / 176 / 388 | **228** | 1,309 | 191 | **399** |
   | B34 좁힌 초안 | 4(0) | 55 | 5 / 6 / 6 | **10** | 10 | 9 | **14** |

   * 교정: 옛 N1 139·옛 N2 176(검토 전 card 수치)을 같은 시뮬레이션에서 **그대로 재현**했다. 옛 D1은 388로 검토 전 card의 506과 다르다 -- 그때 스크립트(`C:/g52/scope_measure.py`)가 지워져
     D1의 이름 규칙 차이를 확인할 수 없다. 이 card의 D1은 계약 1 T7의 정의(위 스크립트 `names()`)다.
   * N2 228 = 옛 N2 176 + T6·삭제 지점 T4 50 + T3(b) 2. B26-1의 def 머리 변경 20개는 모두 키워드 전용 `rails` 추가이고, `rails`를 읽는 문장은 대부분 이미 새 문장이다.
   * N2a 1,309: 머리가 바뀐 20개 def는 본문 전체가 대상이다(`propose_device_roles_gap_fill` 331, `repair_matching_safety` 112, `_branch_composite_pair` 102 …). B26-1의 본질(매개변수 추가)에서는
     선택지 2a가 def 전체에 가깝다(2,472의 53%).
   * B26-1 큰 def(지금 / N2 / D1): `_build_theta_evaluator` 498/5/9, `propose_device_roles_gap_fill` 331/30/79, `optimize_full_circuit_budget` 230/10/18, `repair_matching_safety` 112/8/10,
     `_branch_composite_pair` 102/3/3, 새 def `rail_declaration` 14/14/14.
   * P9 실제는 `kcl_series_union`(23)과 중첩 `kcl_series_union.find`(5)가 바뀐다(검토 전 수치 24는 시뮬레이션 1 def).
2. **시간(직렬, 도구 그대로).** 하한 = 대상 변이 × 5 s(pytest 기동, 첫 test에서 죽음), 상한 = Σ 대상 변이 × 그 def 인벤토리 전체 시간(전부 생존). 인벤토리 시간 187~202 s(이번 junit; 검토 전
   177~192 s). **현실 하한** = 하한 + 'base에서 어떤 test도 실행하지 않은 줄'의 대상 변이(아래 3, 반드시 생존 → 인벤토리 전체를 돈다) × 인벤토리 시간.

   | card | 지금 | N2 | N2a | D1 |
   |---|---|---|---|---|
   | P9 실제 | 2.3분 ~ 1.5 h | 1.0분 ~ 0.6 h | 1.0분 ~ 0.6 h | 0.9분 ~ 0.6 h |
   | B26-1 | 3.4 h ~ 129 h, **현실 하한 19.2 h** | 19분 ~ 12.0 h, 현실 하한 0.6 h | 1.8 h ~ 71 h, 현실 하한 5.8 h | 33분 ~ 21 h, 현실 하한 1.6 h |
   | B34 좁힌 초안 | 4.6분 ~ 1.0 h | 0.8분 ~ 0.3 h | 0.8분 ~ 0.3 h | 1.2분 ~ 0.3 h |

   * 인벤토리 0 변이(실행 없이 생존): B26-1 `_metric_kcl_residual`(지금 57, N2 6) -- 어느 정책이든 B26-1 card의 이름 직접 호출 test(초안 'V3 계획' 4)로 0이 된다.
   * B34 좁힌 초안은 그 card가 55개 전부를 실제로 돌려 죽였다(`draft_b34.spec.md` 'V3 계획' -- 계약 4·6 포함 55/55, 면제 0). 선택지와 무관하게 통과 가능.
3. **확정 생존 -- 어떤 test도 실행하지 않는 줄의 변이**(사본 전체 test 1회를 `sys.monitoring` LINE 이벤트로 기록 -- `covplug.py`, 위치마다 첫 실행 뒤 DISABLE, 실행 줄 합집합. 변이 노드의 줄
   범위(복합문은 머리 줄, `early_return`은 첫 문장 줄)에 실행된 줄이 하나도 없으면 '실행 안 됨'. test가 띄운 하위 프로세스 안의 실행은 잡지 않는다):
   * base 본문 기준(검토 전 card 수치 재현): B26-1 대상 def(중첩 `_evaluate_row_split` 제외) 2,376 중 **298**(`_evaluate_row_split` 포함 2,438 중 314), 넓은 B34(v1, 18 def) 1,395 중 **75**,
     좁힌 B34(4 def) 68 중 6, P9 `kcl_series_union` 0.
   * head 대상 기준(head 줄을 같은 base 줄로 대응, 새 줄은 판정 불가로 뺌): B26-1 지금 **306**(판정 불가 119) / N2 **6** / N2a 74 / D1 20, P9 실제 0, B34 좁힌 초안 지금 1(그 card의 새 test가 죽임).
   * C8이 면제한 `load_topology` 기존 공백 10개(B8, 실행은 되나 test가 결과를 보지 않아 C8에서 생존)는 B26-1 시뮬레이션 head에서 `body[11]`·`body[26]` → `body[14]`·`body[29]`로 경로가 밀린다
     (`v3_c8_in_b26.txt`) -- 지금 도구로도 면제되지 않고(묶기와 무관), 선택지 1이면 다시 대상, N2·N2a·D1이면 대상 밖이다. 좁힌 B34는 `load_topology`를 바꾸지 않는다.
   * 지금 규칙에서 미실행 줄 변이는 **test가 그 줄을 실행하게 만들기 전에는 반드시 생존**한다 -- 해당 card가 레일·폴백과 무관한 기존 동작의 test를 새로 쓰거나 id 면제(사용자 승인)를 받아야 한다.
4. **좁힌 정의가 놓치는 것(위험).**
   * 바뀌지 않은 문장의 생존 변이 = 기존 test 강도. 좁히면 card의 병합 조건에서 빠진다 → `not_targeted` id를 출력하고 백로그로 넘긴다(계약 5 -- 실행하지 않았으므로 생존 여부는 모른다).
   * **바뀐 값이 흘러드는 바뀌지 않은 문장**: card가 새 값을 만들고 그 값을 쓰는 기존 문장이 test로 관찰되지 않아도 N2는 모른다(같은 블록 바로 뒤 문장만 T6로 본다). D1이 이름 한 단계까지 덮는다
     (B26-1에서 N2 대비 +171개). 두 단계 이상·속성·컨테이너 경유 흐름은 D1도 놓친다.
   * **def 머리 변경**: N2(T3 b)는 바뀐 매개변수를 직접 읽는 문장만 본다 -- 매개변수 값이 다른 이름을 거쳐 흐르는 문장, 데코레이터 동작(캐시 등 -- 어떤 연산자도 이것을 변이하지 않는다)은 놓친다.
     N2a는 머리가 바뀌면 본문 전체라 이 공백이 없지만 B26-1에서 대상이 5.7배(228 → 1,309)다. 어느 쪽이든 test가 닿지 않으면 T5로 FAIL(계약 2) -- 개정 전의 '대상 0개 → PASS'는 없다
     (합성 사례 `v3_b2_cases.txt`: 기본값 bool·str·`None`, 매개변수 이름 바꾸기, `*` 추가는 N2 대상 2개, 쓰지 않는 매개변수 추가는 1개(`early_return`), 데코레이터 추가는 3개).
   * **지운 문장**: 개정 전 card의 "지금 규칙도 변이가 없다 -- 차이 없음"은 틀렸다(지금 규칙은 삭제로 동작이 바뀐 **남은 문장**을 변이한다). 개정 정의는 감싸는 제어문(T4)과 같은 블록 바로 뒤 문장(T6)을
     본다(합성 사례: 블록 안 문장 삭제 → 대상 6, `else` 절 삭제 → 대상 5). 남는 공백은 계약 6.
   * 감싸는 조건: N1은 바뀐 문장을 지키는 기존 `if` 조건의 변이를 보지 않는다. N2가 덮는다(B26-1 +37개).
   * 바뀐 def가 부르는 바뀌지 않은 def: 지금 규칙도 대상이 아니다(해시 동일) -- 차이 없음.
5. **중간안 평가.**
   * **def 전체 + 시간·변이 수 예산 + 표본 추출**: 표본 밖 변이가 판정에서 빠지므로 약화이고, 빠지는 집합이 난수(또는 고정 시드)로 정해져 '바뀐 문장'을 빠뜨릴 수 있다 -- 선택지 2보다 약한 곳이
     생긴다. 예산 수치는 근거 없이 정하는 상수다(상수 임의 생성 금지 원칙). **권고하지 않는다.**
   * **def 전체 + 자동 기준선 차분**(base def에서도 같은 문장 지문으로 사는 변이는 자동 면제 -- B34 초안 (a)를 규칙으로): 약화(기존 공백을 통과시킴)이고, base에서도 생존 변이를 돌려야 해 비용이
     지금 이상이며 문장 대응 규칙이 따로 필요하다. 확정 생존 298개도 base에서 살아 자동 면제되므로 결과는 선택지 2와 비슷한데 비용만 크다. **권고하지 않는다.**
   * **약화 없는 가속**(어느 선택지와도 함께 가능, 별도 게이트 card): 변이마다 그 줄을 실행하는 test만 돌리기(줄 커버리지 선택 -- 줄을 실행하지 않는 test는 그 변이를 죽일 수 없으므로 판정 불변,
     단 def 자기 필드 변이는 인벤토리 전체), 빠른 test 먼저, 병렬. 검토 전 실측: B26-1 def 본문의 커버리지 선택 상한 70.3 h(추적 때문에 test 시간이 부풀려진 값) 대 인벤토리 상한 122 h.
     이번 개정에서는 다시 재지 않았다(test별 실행 줄 기록 스크립트 `covplug.py` 판은 합집합만 기록한다). **확정 생존은 가속으로 없어지지 않는다**.
6. **이름 충돌.** `ls tools/gates/redteam/attacks/` → `33-*` 없음. 출력 키 `not_targeted`·`targets_by_def`·`def_header_changed`: `grep -rn "not_targeted\|targets_by_def\|def_header_changed" tools/ docs/` 0건.
7. **쓰기 경로.** `tools/gates/mutate_changed.py` = gmid-code-author(design 10 C11 행), `tools/gates/redteam/**` = gmid-test-author(C10 행), design 05·계획 문구 = 오케스트레이터 문서 커밋.
8. **계획서 소비자.** 계획서 533행 이동 규칙("무변경 증명 = … 해시 동일 … 해시가 같은 함수는 V3 대상에서 뺀다")은 **지금 도구에 구현돼 있지 않다**: `main`은 같은 경로의 base만 비교하고
   새 파일이면 `base_src = None`이라 그 파일의 def가 전부 대상이 된다(`mutate_changed.py` 359~364행, `changed_defs` 91~95행). `draft_p3_g1.spec.v3.md` 11~14행도 같은 사실(엔진 4파일 상한
   V3 대상 def 473·변이 15,677)을 적었고, 그 구현이 G1 card다. 그래서 개정 전 card의 "해시가 같으면 여전히 대상 0"과 `v3_scope_systemic.md` §2의 "Phase 3 이동 card는 계획 규칙으로 이 문제가
   없다"는 **G1 병합 전에는 거짓**이다(검토 S8 -- 후자는 `v3_scope_systemic.md`에서 고쳤다). G1과의 순서는 '결정 필요 항목'. `grep -rn "본문 전체\|def 전체" docs/01-plan docs/02-design` 중 V3
   관련 0건(걸린 1건은 design 05 318행 V4 서술) -- 고칠 곳은 계약 10의 두 행뿐.
9. **미배선.** 새 def(맞춤·대상 분류)를 만들면 `mutate_changed.main`이 부른다. 계약 9는 기존 `_replace_def`를 고친다(새 함수 없음).
10. **도구 결함 재현**(`v3_probes.txt`): 데코레이터 def `@functools.lru_cache(maxsize=128)`의 `const±:decorator_list[0].keywords[0].value` 2개가 지금 `_replace_def`로는 NOOP(바뀐 소스 AST = 원본),
    첫 데코레이터 줄부터 바꾸는 판으로는 NOOP 아님. 같은 파일: def 머리만 바꾼 합성 변경 7종 중 6종은 def 자기 필드 변이(개정 전 T3)가 0개(데코레이터 추가만 2개).
