---
id: 20260930-v3-changed-stmt-scope
phase: 0.5
evidence_type: red-green
gate_change: yes
approval: 20260930-v3-changed-stmt-scope
---
## 의도

**선택적 게이트 변경(사용자 결정 대기 -- `draft_v3_decision_question.md`). 판정 기준의 적용 범위를 줄이는 약화다.** 사용자가 선택지 2를 고를 때만 이 card를 쓴다(선택지 3이면 계약 1의 대상 정의만
'D1'로 바꾼다 -- '선택지별 대상 정의' 절). 면제 누수 수정(`draft_v3_exempt_binding.spec.md`, 강화)은 이 card와 독립이고 먼저 병합한다.

V3(`tools/gates/mutate_changed.py`)는 지금 **AST 해시가 바뀐 def의 본문 전체**를 변이한다. 엔진 def는 수백~천 줄이라 몇 줄을 고친 card도 그 def의 기존 문장 전부가 병합 조건이 된다.
B28 병합 뒤에는 도구가 실제로 돌고 기준 실행 실패는 `ERROR`라, 기존 문장의 생존 변이가 그대로 V3 FAIL이다(`_drafts/v3_scope_systemic.md` §1).

이 card: V3 대상을 **바뀐 def 안의 '바뀐 문장'과 그것을 감싸는 제어문, 그리고 새 def 전체**로 좁힌다. 좁힌 밖의 변이는 판정에 쓰지 않되 수를 출력에 싣고(`not_targeted`), 오케스트레이터가
기존 test 공백 백로그로 넘긴다(C8 때 B8과 같은 종류) -- 버리는 정보를 조용히 버리지 않는다.

### 약화인가 -- 원문 대조

design 05 §10 V3 행(317행):
> ① diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것(새 def 포함) ② 연산자: … ⑤ 살아남은 변이가 있으면 FAIL.

계획 N4.2 V3 행(839행):
> 대상 = diff가 닿은 def 중 AST 해시가 바뀐 것. … 살아남은 변이가 있으면 FAIL. 등가 변이 면제는 승인 기록으로만.

design 05 §2 표 'V3~V7' 행: 판정 기준 소유 = `사용자`.

판단: 원문은 대상 단위를 **def**로 정하고 그 def의 변이가 하나라도 살면 FAIL이다. 문장 단위로 좁히면 지금 규칙이 죽이라고 요구하는 변이(B26-1 시뮬레이션 head에서 2,472 중 2,296)가 판정에서 빠져
게이트가 거부하는 경우의 집합이 줄어든다. N0.4 '기준 약화' 8패턴(V5, test diff 대상)의 문자 그대로에는 들지 않지만 **판정 기준의 적용 범위를 줄이는 게이트 변경이므로 약화로 다루고 사용자
승인을 받는다**(DEC-40 취지 -- 약화는 매 건 사용자 승인). B28 승인의 "기준 약화가 아니다" 근거는 여기서 댈 수 없다.

약화를 받을 근거(사용자 판단 재료): V3의 목적은 DEC-38 "test의 독립성은 결과(V3, V4)로 검사한다" -- **이 변경을 위해 쓴 test가 이 변경의 코드를 실제로 판정하는가**다. 바뀌지 않은 문장의 생존 변이는
그 card의 test가 아니라 **기존 test의 강도**를 잰다. 그리고 그 일부는 어떤 test로도 실행되지 않는 줄이라 card마다 확정 생존이다('작성 전 실측' 3: B26-1 대상 def 본문의 298개, B34 75개).

### 선택지별 대상 정의(측정한 세 정의)

정의는 모두 **해시가 바뀐 def마다** base def와 head def를 AST로 맞춘 결과에서 나온다(새 def는 셋 모두 본문 전체 -- 지금 규칙 그대로).
* **N1(바뀐 문장만)**: 아래 계약 1의 T1·T2·T3·T5.
* **N2(바뀐 문장 + 감싸는 제어문) -- 이 card의 기본**: N1 + T4.
* **D1(바뀐 문장 + 이름 한 단계 데이터 의존 문장, 선택지 3)**: N1 + 바뀐 영역이 대입하는 이름을 읽는 문장, 바뀐 영역이 읽는 이름을 대입하는 문장(def 안 전체, 흐름 무시, 한 단계). 복합문은 머리 필드만 본다.

## 관찰 가능한 계약

용어: "블록 필드" = `body`·`orelse`·`finalbody`·`handlers`·`cases`. "지문" = `ast.dump(노드, include_attributes=False)`. "머리" = 블록 필드를 비운 노드의 지문.
"자기 필드" = 복합문의 블록 필드 밖 필드(`test`·`iter`·`target`·`items`·`type`·`name` 등).

1. **대상(해시가 바뀐 기존 def)**. base def와 head def의 같은 블록 필드 목록을 지문의 최장 일치 부분열로 맞춘다(참조 알고리즘: `difflib.SequenceMatcher(None, a, b, autojunk=False)`의 opcode).
   `equal`은 바뀌지 않음, `insert`의 head 원소는 **새 문장**, `delete`의 base 원소는 **지운 문장**(head 노드가 없다), `replace` 구간에서는 head 원소마다 같은 구간의 아직 짝 없는 base 원소 중
   종류가 같고 머리가 같은 복합문을, 없으면 종류가 같은 복합문을 짝으로 삼아 **머리 변경**(머리가 다를 때) 여부를 적고 블록 필드로 내려가 같은 절차를 되풀이한다. 짝이 없는 head 원소는 새 문장,
   짝이 없는 base 원소는 지운 문장이다. def 자신의 머리(인자·데코레이터·반환 주석)가 다르면 **def 머리 변경**이다. 변이(연산자·경로는 지금 그대로)가 대상인 조건:
   * T1 변이 노드가 새 문장의 부분 트리 안(그 문장 자신의 `stmt_delete` 포함).
   * T2 변이 노드가 머리 변경 복합문의 자기 필드 안이거나 그 복합문 자신의 `stmt_delete`, 머리가 바뀐 `except` 절의 `except_body_delete`.
   * T3 def 머리 변경이면 def 자기 필드(인자 기본값 등) 안의 변이.
   * T4 T1·T2 영역을 감싸는 모든 복합문(조상)의 자기 필드 안 변이, 그 조상의 `stmt_delete`, 조상이 `except` 절이면 그 `except_body_delete`.
   * T5 `early_return`: 그 def에 새 문장·머리 변경·지운 문장 중 하나라도 있으면.
   바뀌지 않은 문장만 옮기거나 들여쓰기만 바꾼 것(감싸던 `if`를 없앰 등)은 새 문장이다(보수 쪽). 서식·주석·docstring만 바뀐 def는 지금처럼 대상이 아니다(해시 동일).
2. **대상(새 def)**: base에 같은 qualname이 없는 def는 본문 전체(지금 규칙 그대로).
3. **판정**: 대상 변이만 실행하고, 대상 변이 중 생존이 있으면 FAIL(exit 1). 인벤토리 없음 → 생존(지금과 같음). 면제는 `20260930-v3-exempt-binding` 규칙 그대로.
4. **대상 밖 출력(조용히 버리지 않음)**: 대상 밖 변이는 실행하지 않고 `--out`에 `{"id": …, "result": "not_targeted"}`로 적는다. 출력 JSON에 `not_targeted`(수)와 `targets_by_def`
   (`{"<파일>::<qualname>": {"targeted": n, "not_targeted": m, "deleted_statements": k}}`)를 더한다. 판정에는 쓰지 않는다.
5. **지운 문장**: 지운 문장에는 변이가 없다(지금도 없다). 지운 동작의 판정은 이 card 밖 -- spec card의 red-green 증거(V1·V2)가 맡는다. `deleted_statements`로 수만 보인다.
6. **무동작**: 기존 redteam V3 케이스(`v3_survivor/`, `attacks/28-v3-gmid-options/`, `attacks/31-v3-git-history/`, 공격 26·27f, `attacks/32-v3-exempt-binding/`)의 exit가 base와 같다
   (모두 새 def이거나 def 전체가 바뀐 구성 -- test-author가 케이스별로 확인한다).
7. **새 redteam 케이스** `tools/gates/redteam/attacks/33-v3-changed-scope/`(합성 저장소):
   (a) `unchanged-stmt-survivor`(control) -- base def에 약한 test로 생존하는 문장 S가 있고, head가 같은 def의 다른 문장 C만 바꾸며 C의 변이는 모두 죽는다 → exit 0, 출력 `not_targeted` ≥ 1
       (S의 변이). base 도구 exit 1 -- **red**.
   (b) `changed-stmt-survivor`(attack) -- head가 바꾼 문장 C의 변이가 생존 → exit 1.
   (c) `enclosing-guard-survivor`(attack) -- 바꾼 문장 C를 감싸는 바뀌지 않은 `if g:`의 `g` 뒤집기가 생존 → exit 1(T4). (N1을 택하면 이 단계는 control exit 0이 된다.)
   (d) `unwrapped-stmt`(attack) -- 감싸던 `if`를 없애 들여쓰기만 바뀐 문장의 변이가 생존 → exit 1(새 문장).
   (e) `header-only-change`(attack) -- `for` 머리(반복 대상)만 바꾸고 본문 불변, 머리의 변이가 생존 → exit 1(T2).
8. **문서**: design 05 §10 V3 행 ①을 "① 대상 = diff가 닿은 `def` 중 `ast.dump`(docstring 제외) 해시가 base와 다른 것. 새 def는 본문 전체, 기존 def는 base와 문장 단위로 맞춘 '바뀐 문장'과
   그것을 감싸는 제어문(정의: spec card `20260930-v3-changed-stmt-scope` 계약 1). 대상 밖 변이는 실행하지 않고 수를 출력한다(판정 제외)"로, 계획 N4.2 V3 행 "대상 = diff가 닿은 def 중 AST 해시가
   바뀐 것"을 "대상 = diff가 닿은 def 중 AST 해시가 바뀐 것의 바뀐 문장과 감싸는 제어문, 새 def는 전체(대상 밖 변이 수는 출력 -- 기존 test 공백 백로그 입력)"로 고친다. 모듈 docstring ①도
   같은 뜻으로(code-author). N4.2의 이 칸은 `plan_tables_hash` 입력이 아니다(`v_intro`만).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 7 (a)가 base 도구에서 exit 1(바뀌지 않은 문장 S의 생존으로 FAIL) -- red, 병합본에서 exit 0 -- green. (b)~(e)는 좁힌 뒤에도 거부가 남는지 보이는 attack(base·병합본 모두
exit 1 -- '게이트가 실제로 거부하는가' WP-02). design 05 §18.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py` V 케이스, base → head 이력). 어느 문장이 바뀌었는지와 어느 변이가 사는지가 케이스 구성(base·head 소스와 test)으로 정해진다. 기대 exit·출력 키는 이 card
계약 문장. 대상 판정 기대값은 피검 도구로 만들지 않는다(계약 1의 정의를 test-author가 구성으로 적용).

## 거부해야 할 입력

바뀐 문장·감싸는 제어문 머리·들여쓰기만 바뀐 문장·머리만 바뀐 복합문의 생존 변이 → exit 1(계약 7 (b)~(e)). 새 def의 생존 변이 → exit 1(`v3_survivor` 그대로).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

새 def만 있는 변경, def 전체를 새로 쓴 변경 -- 대상 집합이 지금과 같다(기존 redteam V3 케이스, 계약 6).

## 재현할 수치

없음(아래 비용은 결정 재료이지 판정 기대값이 아니다).

## 결정 필요 항목

* **사용자 결정(대기)**: V3 범위 정책 -- `draft_v3_decision_question.md` 선택지 1(지금 규칙 유지)·2(이 card, N2)·3(이 card의 계약 1을 D1로). 승인 기록 `20260930-v3-changed-stmt-scope`
  (`target_kind: diff`, 이 card + design 05 §10 V3 ① + 계획 N4.2 V3 문구). **범위 설명에 "판정 기준 적용 범위 축소(약화) 승인"을 명시한다.**
* 선택지 1이면 이 card는 쓰지 않는다. 그때 B26-1은 V3 전수(`_drafts/draft_b26_1.spec.md` 'V3 계획' (c))로 가고, 확정 생존(작성 전 실측 3)은 test 보강 또는 card별 변이 id 면제(누수 수정 뒤 해시에
  묶인)로 처리한다.

## 작성 전 실측

(측정 2026-09-30, gate `master` HEAD `7535799`(엔진 소스 = cd64170). 저장소 쓰기 없음, scratch `C:/g52`(`git archive HEAD` 사본, 끝나면 삭제). 시뮬레이션 head는 `_drafts/b26_v3_measure.py`의
`build_b26`·`build_p9`를 그대로 썼다(경로만 C:/g52). 도구 `mutate_changed`의 `changed_defs`·`mutants`·`_get`·`_path_nodes`와 `reachability.iter_defs`만 읽기 전용으로 import, 도구 `main`은 돌리지 않음.
스크립트 `C:/g52/scope_measure.py`(대상 정의 N1·N2·D1 분류), `C:/g52/covplug.py`·`cov_analyze.py`(test별 실행 줄). 수치는 아래에 옮겨 적었다.)

1. **정의별 변이 수(시뮬레이션 head).** 줄 기준 = `b26_v3_measure.py`의 `touched_count`(diff 줄에 걸린 변이, 복합문은 머리 줄만, `early_return`은 새 def만).

   | card | 대상 def | 지금(def 전체) | 줄 기준 | **N1** | **N2** | **D1** | 지운 문장 |
   |---|---|---|---|---|---|---|---|
   | P9 | 1 | 24 | 2 | 3 | 3 | 4 | 5 |
   | B26-1 | 31 | 2,472 | 106 | **139** | **176** | **506** | 39 |
   | B34 | 18(직접 12 + 전파 6) | 1,395(base 본문) | 미측정 | 미측정 | 미측정 | 미측정 | -- |

   * B34는 패치를 시뮬레이션하지 않아 좁힌 정의의 수를 재지 않았다(착수 시 도구가 `targets_by_def`로 잰다). B34 초안의 범위 축소안(세 def만) 변이 32는 def 전체 기준이다.
   * B26-1 큰 def(전체 / N2 / D1): `_build_theta_evaluator` 498/4/9, `propose_device_roles_gap_fill` 331/21/94, `optimize_full_circuit_budget` 230/9/18, `repair_matching_safety` 112/6/23,
     `_branch_composite_pair` 102/2/16, 새 def `rail_declaration` 14/14/14.
   * N1이 줄 기준보다 많은 몫: `early_return`(바뀐 def마다 1)과 들여쓰기·머리만 바뀐 복합문.
2. **시간(직렬, 도구 그대로).** 하한 = 변이 × 5 s(pytest 기동, 첫 test에서 죽음), 상한 = Σ 변이 × 그 def 인벤토리 전체 실행 시간(전부 생존). 인벤토리 시간은 `b26_v3_measure.out.txt`의 def별 값
   (177~192 s, 사본 전체 test 272 s).

   | card | 지금 | N1 | N2 | D1 |
   |---|---|---|---|---|
   | P9 | 2분 ~ 1.2 h | 15초 ~ 9분 | 15초 ~ 9분 | 20초 ~ 12분 |
   | B26-1 | 3.4 h ~ 122 h | 12분 ~ 6.9 h | 15분 ~ 8.8 h | 42분 ~ 25 h |
   | B34 | 2.0 h ~ 56 h(`v3_scope_systemic.md` §2: 직접 1.6 h~42 h + 전파 22분~14 h) | 미측정 | 미측정 | 미측정 |

   * 인벤토리 0 변이(실행 없이 생존): B26-1 지금 57(`_metric_kcl_residual` 전부), N1·N2 5, D1 9 -- 어느 정책이든 B26-1 card의 이름 직접 호출 test(초안 'V3 계획' 4)로 0이 된다.
3. **확정 생존 -- 어떤 test도 실행하지 않는 줄의 변이**(HEAD 사본 전체 test 1회를 `sys.monitoring` LINE 이벤트로 test별 실행 줄 기록, 813건 -- 796 passed·2 failed(사본에 `.git` 없음, ts6 두 건)·15 xfailed,
   추적 포함 437 s. 변이 노드의 줄 범위(복합문은 머리 줄)에 실행된 줄이 하나도 없으면 '실행 안 됨'). base 본문 기준:
   * P9 `kcl_series_union` 49 중 0.
   * B26-1 대상 def 본문 2,376 중 **298**(SD 20 def 76, SR 9 def 222 -- `_build_theta_evaluator` 70, `optimize_full_circuit_budget` 78, `_fixup_euler_blocked_rows` 41,
     `_branch_composite_pair` 25, `run_matching_safety_with_finger_growth` 16, `propose_device_roles_gap_fill` 13 …).
   * B34 대상 def 본문 1,395 중 **75**(직접 65, 전파 10).
   * 지금 규칙에서 이 변이들은 **test가 그 줄을 실행하게 만들기 전에는 반드시 생존**한다 -- 해당 card가 레일·폴백과 무관한 기존 동작의 test를 새로 쓰거나 id 면제(사용자 승인)를 받아야 한다.
     `v3_scope_systemic.md` §1의 인벤토리 과대 근사 때문이 아니라(그건 시간 문제) 실제 test 공백이다.
4. **좁힌 정의가 놓치는 것(위험).**
   * 바뀌지 않은 문장의 생존 변이 = 기존 test 강도. 좁히면 card의 병합 조건에서 빠진다 → `not_targeted` 수를 출력하고 백로그로 넘겨야 정보가 남는다(계약 4).
   * **바뀐 값이 흘러드는 바뀌지 않은 문장**: card가 새 값을 만들고 그 값을 쓰는 기존 문장이 test로 관찰되지 않아도 N1·N2는 모른다(그 문장의 변이가 대상 밖). D1이 이름 한 단계까지 덮는다
     (B26-1에서 N1 대비 +367개). 두 단계 이상·속성·컨테이너 경유 흐름은 D1도 놓친다.
   * 감싸는 조건: N1은 바뀐 문장을 지키는 기존 `if` 조건의 변이를 보지 않는다 -- test가 바뀐 코드를 조건의 한쪽에서만 부르는 경우. N2가 덮는다(B26-1 +37개).
   * 바뀐 def가 부르는 바뀌지 않은 def: 지금 규칙도 대상이 아니다(해시 동일) -- 차이 없음. 지운 문장: 지금 규칙도 변이가 없다 -- 차이 없음(계약 5).
5. **중간안 평가.**
   * **def 전체 + 시간·변이 수 예산 + 표본 추출**: 표본 밖 변이가 판정에서 빠지므로 약화이고, 빠지는 집합이 난수(또는 고정 시드)로 정해져 '바뀐 문장'을 빠뜨릴 수 있다 -- 선택지 2보다 약한 곳이
     생긴다. 예산 수치는 근거 없이 정하는 상수다(상수 임의 생성 금지 원칙). **권고하지 않는다.**
   * **def 전체 + 자동 기준선 차분**(base def에서도 같은 문장 지문으로 사는 변이는 자동 면제 -- B34 초안 (a)를 규칙으로): 약화(기존 공백을 통과시킴)이고, base에서도 생존 변이를 돌려야 해 비용이
     지금 이상이며 문장 대응 규칙이 따로 필요하다. 확정 생존 298개도 base에서 살아 자동 면제되므로 결과는 선택지 2와 비슷한데 비용만 크다. **권고하지 않는다.**
   * **바뀐 문장 + 데이터 의존(D1, 선택지 3)**: 약화 폭이 가장 작은 좁힘(B26-1 506 = 지금의 20%). 위험 4의 '바뀐 값이 흘러드는 기존 문장'을 한 단계 덮는다. 대신 D1에 드는 기존 문장의 생존은
     여전히 기존 test 공백일 수 있어(흐름 무시·이름 기준 과대 근사) card 밖 test 보강이 다시 생긴다.
   * **약화 없는 가속**(어느 선택지와도 함께 가능, 별도 게이트 card): 변이마다 그 줄을 실행하는 test만 돌리기(줄 커버리지 선택 -- 줄을 실행하지 않는 test는 그 변이를 죽일 수 없으므로 판정 불변,
     단 def 자기 필드 변이는 인벤토리 전체), 빠른 test 먼저, 병렬. 실측: B26-1 def 본문의 커버리지 선택 상한 70.3 h(추적 때문에 test 시간이 272 s → 437 s로 부풀려진 값) 대 인벤토리 상한 122 h.
     **확정 생존 298개는 가속으로 없어지지 않는다** -- 시간 문제는 줄지만 선택지 1의 핵심 비용(기존 코드 test 작성)은 그대로다.
6. **이름 충돌.** `ls tools/gates/redteam/attacks/` → `33-*` 없음. 출력 키 `not_targeted`·`targets_by_def`: `grep -rn "not_targeted\|targets_by_def" tools/ docs/` 0건.
7. **쓰기 경로.** `tools/gates/mutate_changed.py` = gmid-code-author(design 10 C11 행), `tools/gates/redteam/**` = gmid-test-author(C10 행), design 05·계획 문구 = 오케스트레이터 문서 커밋.
8. **계획서 소비자.** 계획서 533행 이동 규칙("해시가 같은 함수는 V3 대상에서 뺀다")은 def 단위 해시 비교라 이 card와 충돌하지 않는다(해시가 같으면 여전히 대상 0). `grep -rn "본문 전체\|def 전체" docs/01-plan
   docs/02-design` 중 V3 관련 0건(걸린 1건은 design 05 318행 V4 서술) -- 고칠 곳은 계약 8의 두 행뿐.
9. **미배선.** 새 def를 만들면 `mutate_changed.main`이 부른다.
