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
  B26-1 시뮬레이션 head의 '닿지 않은 변이' 2,366개를 면제 목록으로 만들면 그 위에서 B34 대상 def의 변이 1,402개 중 **619개**가 이미 면제된다. 선례 `20260922-ic3-v3-exempt`의
  14개 id는 지금도 유효하게 읽힌다 -- 그중 `save_instance_json` 4개는 그 def가 C8 뒤 `b29be01`에서 바뀌었는데도(해시 `9cb09766…` → `11a55c19…`) B26-1 시뮬레이션 head에서 4개 모두
  같은 경로에 걸린다(`b26_v3_measure.out.txt` leak2). 그 기록의 범위 설명은 "두 함수의 본문 구조가 바뀌면 이 면제는 맞지 않는다"고 적었지만 도구는 경로만 본다.

고칠 방향: **면제 원소를 (변이 id, 승인 시점의 def 해시) 쌍으로 묶는다.** 원소 형식 `<변이 id>@<def 해시>`, def 해시 = design 05 §10 V3 ①의 해시(`ast.dump`, docstring 제외,
`include_attributes=False`의 sha256 16진 64자 -- 도구 `def_hash`). 면제는 head의 그 def 해시가 원소의 해시와 같을 때만 적용한다.
* card 묶음은 따로 두지 않는다: V3는 base와 해시가 다른 def만 변이하므로, 승인한 def 형태가 병합된 뒤 그 def를 바꾸는 card에서는 해시가 반드시 달라 면제가 풀린다. 같은 card의 재시도에서
  def가 바뀌어도 풀린다(C8 승인 범위 설명의 의도와 같다). 해시가 같아지는 경우는 승인한 형태와 같은 코드뿐이라 면제가 맞다.
* 승인 기록 머리 형식(`merge_gate.parse_approval_header`, `00-common` §8.2)은 바꾸지 않는다 -- decision `target`은 쉼표로 나눈 비지 않은 원소 목록이고 `@`는 이미 허용된다. 새 키가 없으므로
  스키마·redteam 15-records 영향이 없다.
* **기존 승인 기록은 고치지 않는다**(N3.12.2: 기존 기록 수정·삭제 거부). 이행 규칙 = 해시 없는 V3 모양 원소는 **적용하지 않고 출력에 싣는다**(fail-closed). 이것이 잃는 것이 없음은
  '작성 전 실측' 1(이행 근거)에 적었다. 암묵 앵커(승인 커밋 시점의 def 해시)는 쓰지 않는다 -- 실측으로 틀린 앵커다(같은 절).
* 강화다(면제되는 변이 집합이 줄고 거부 집합이 넓어진다). 그래도 게이트 판정 기준 변경이므로(design 05 §2 표 'V3~V7' 행: 판정 기준 소유 = `사용자`) `target_kind: diff` 사용자 승인을 받는다.

범위 밖(이 card에서 바꾸지 않는다, 근거는 '결정 필요 항목'):
* V7(`reachability.py`) 면제: 같은 읽기(`_approved_ids`)를 쓰지만 V7은 **base에 없던 def**만 판정하므로, 승인한 def가 병합되면 그 id는 다시 판정되지 않는다. 누수 조건은 '같은 qualname을
  지웠다가 다른 본문으로 다시 더함'뿐이다. 지금 V7 원소 2개(`20260930-restore-unwired-until-6a`)는 두 def가 HEAD에 있어 판정 대상이 아니다. 백로그로 넘긴다.
* V4(`test_lint.py`) 면제: 같은 부류의 누수(test id `<파일>::<test 이름>`에 묶임, test 본문 해시 미묶임)다. 그러나 V4는 바뀐 test 파일의 **모든** test를 lint하므로 기존 원소 2개
  (`20260923-c9-v4-exempt`)가 뒤 card에서 계속 필요하다 -- fail-closed 이행이 V3와 달리 무손실이 아니어서 이행 설계가 따로 필요하다. 백로그로 넘긴다.
* `reachability._approved_ids`의 반환값·동작은 바꾸지 않는다(V4·V7 소비자 불변).

## 관찰 가능한 계약

"V3 모양 원소" = decision 승인 기록 `target` 원소 중 `<모듈>:<qualname>:<연산자>:<경로>` 모양(연산자 ∈ `cmp_flip`, `arith`, `const+`, `const-`, `stmt_delete`, `early_return`,
`except_body_delete`)이고 `@` 뒤 해시가 있거나 없는 것. "head def 해시" = 변이를 만든 head의 그 qualname def의 ① 해시(중첩 def 노드를 바깥 def로 변이한 경우 바깥 def의 해시).

1. **묶인 면제 적용**: head 트리의 decision 승인 기록에 원소 `<id>@<H>`가 있고 H가 head def 해시와 같으면 그 변이는 실행하지 않고 결과가 `exempt`다. 결과 레코드에 `def_hash`(head def 해시)를 담는다.
2. **해시 불일치**: 원소 `<id>@<H'>`의 H'가 head def 해시와 다르면 면제하지 않는다 -- 변이를 정상 실행해 `killed`/`survived`로 센다. 출력 JSON `exempt_ignored`에
   `{"id": <id>, "reason": "hash_mismatch", "approved_hash": H', "head_hash": H}`가 든다.
3. **해시 없는 원소(기존 기록 포함)**: 원소가 이번 실행의 변이 id와 같고 `@`가 없으면 면제하지 않는다(정상 실행). 출력 `exempt_ignored`에 `{"id": <id>, "reason": "unbound"}`가 든다.
   이번 실행의 변이 id와 같지 않은 원소는 출력에 싣지 않는다(다른 도구의 id·다른 def의 id).
4. **판정**: 1의 `exempt`를 뺀 변이 중 생존이 있으면 FAIL(exit 1), 없으면 PASS(exit 0) -- 지금과 같다. `exempt_ignored`는 판정을 바꾸지 않는다(정보). 2·3으로 풀린 변이가 생존하면 FAIL이다.
5. **승인에 옮길 형태 출력**: 출력 JSON에 `survivor_bindings` = 생존 변이마다 `<id>@<head def 해시>`(순서는 `survivors`와 같음)를 더한다. `survivors`는 지금 형식 그대로다(변이 id만).
6. **다른 도구 무영향**: 같은 입력에서 V4(`test_lint.py`)·V7(`reachability.py`)의 출력 JSON과 exit가 base 도구와 같다(`_approved_ids` 불변). `@`가 든 원소는 V4·V7의 어떤 id와도 같지 않다.
7. **무동작**: 기존 redteam V3 케이스(`v3_survivor/` attack exit 1·control exit 0, `attacks/28-v3-gmid-options/`, `attacks/31-v3-git-history/`, 공격 26·27f)와 V4 `attacks/29-v4-decision-exempt/`의
   결과가 base와 같다. 승인 기록이 없는 저장소에서 V3 출력은 새 키(`exempt_ignored` 빈 목록, `survivor_bindings`)를 빼면 base와 같다.
8. **새 redteam 케이스** `tools/gates/redteam/attacks/32-v3-exempt-binding/`(합성 저장소, 생존 변이 집합이 구성으로 정해진 def):
   (a) `legacy-unbound-leak`(attack) -- base 커밋에 해시 없는 원소로 변이 id X를 면제하는 decision 승인 기록이 있고, head가 그 def를 바꿔 같은 경로의 변이 X가 생존한다 → exit 1,
       출력 `exempt_ignored`에 X·`unbound`. base 도구 exit 0(조용한 면제) -- **red**.
   (b) `hash-mismatch`(attack) -- 원소 `X@<바꾸기 전 def의 해시>`, head가 def를 바꿔 X가 생존 → exit 1, `exempt_ignored`에 X·`hash_mismatch`. (base 도구도 exit 1 -- 회귀 방지.)
   (c) `bound-exempt`(control) -- 원소 `X@<head def의 해시>`, X가 유일한 생존 변이 → exit 0, X의 결과 `exempt`. base 도구 exit 1(`@` 원소를 모른다) -- **red(green 쪽)**.
   (d) `bound-other-def`(attack) -- 원소가 다른 qualname def의 해시를 달고 있음(`X@<다른 def 해시>`) → exit 1.
9. **문서**: design 05 §10 V3 행 ⑤의 "등가 변이 면제는 `target_kind: decision`, `target` = 변이 id 목록인 승인 기록"을 "등가 변이 면제는 `target_kind: decision`, `target` 원소 =
   `<변이 id>@<def 해시>`(①의 해시, 승인할 때의 head def)인 승인 기록 -- head의 그 def 해시가 같을 때만 적용. 해시가 없거나 다른 원소는 적용하지 않고 출력 `exempt_ignored`에 싣는다"로
   고친다. 계획 N4.2 V3 행의 "등가 변이 면제는 승인 기록으로만"을 "등가 변이 면제는 승인 기록으로만(변이 id와 그 def의 AST 해시에 묶임)"으로 고친다. `mutate_changed.py` 모듈 docstring ⑤도
   같은 뜻으로(code-author). 계획 N4.2의 이 칸은 `plan_tables_hash` 입력이 아니다(`merge_gate.plan_tables_object`는 `v_intro`·`ic_parts`·`ic_test`·`phase_order`·`write_paths`만 -- 실측).

## 신규 시그니처

| 모듈 | 심볼 | 시그니처 |
|---|---|---|

## 판정 유형 근거

red-green: 계약 8 (a)는 base 도구에서 exit 0(해시 없는 면제를 경로만으로 적용), (c)는 base 도구에서 exit 1(`@` 원소를 모른다) -- 둘 다 red, 병합본 도구에서 green. design 05 §18: ⑤ 뒤 게이트 변경은
spec card(red-green, oracle (a)). (b)·(d)는 base·병합본 모두 exit 1인 회귀 방지 단계다.

## oracle 종류와 출처

(a) 구성: 합성 저장소(redteam `lib/rt.py`의 V 케이스 -- base 커밋 → head 커밋 이력, decision 승인 기록 파일은 케이스의 `approval`·`more_approvals`·`base_files` 경로로 둔다)에서 생존 변이 집합이
구성으로 정해진 def(예: `v3_survivor`처럼 0 입력만 보는 test)를 쓴다. 기대 exit·출력 키는 이 card 계약 문장. **def 해시 기대값은 피검 도구 함수(`mutate_changed.def_hash`)를 불러 만들지 않는다** --
test-author가 design 05 §10 V3 ①의 정의(docstring 제외 `ast.dump(…, include_attributes=False)`의 sha256)로 케이스 생성 쪽(`lib/rt.py`의 치환 자리표시자 등)에서 독립 계산한다.

## 거부해야 할 입력

해시 없는 원소로 면제된 변이가, 그 def가 바뀐 head에서 생존 → exit 1(계약 8 (a)). 다른 해시·다른 def의 해시를 단 원소 → exit 1(계약 8 (b)·(d)).

## library 회로 적용 여부

해당 없음(게이트 도구).

## 무동작 판정 입력(무발동 값)

기존 redteam 전체(`run_all.py --phase 0.5 --mode direct`)와 `--cases 0.5`의 케이스 판정이 base와 같다(계약 8의 새 케이스 제외). 승인 기록이 없는 저장소의 V3 판정·`survivors`가 base와 같다.

## 재현할 수치

없음.

## 결정 필요 항목

없음(게이트 변경 승인 기록 `20260930-v3-exempt-binding` -- `target_kind: diff`, 이 card + design 05 §10 V3 ⑤ + 계획 N4.2 V3 문구. 범위 설명에 "강화: 면제 적용 범위 축소, 기존
`20260922-ic3-v3-exempt`의 V3 원소 14개는 해시가 없어 더는 적용되지 않는다(무손실 근거 = 이 card '작성 전 실측' 1)"를 적는다).
* V7·V4 동급 수정은 이 card 밖 -- 오케스트레이터가 백로그에 둘을 더한다: (i) V7 면제 원소를 def 해시에 묶기(누수 조건 = 같은 qualname 삭제 후 재추가, 지금 영향 0),
  (ii) V4 면제 원소를 test 함수 해시에 묶기(기존 2원소의 이행 설계 필요 -- V4는 바뀐 파일의 모든 test를 보므로 fail-closed가 무손실이 아니다).
* 관찰(이 card 밖, 백로그 후보): 도구는 중첩 def의 노드를 바깥 def 변이로도, 해시가 바뀐 중첩 def 자신의 변이로도 만든다 -- B26-1 시뮬레이션 head에서 `optimize_full_circuit_budget`
  안의 `_evaluate_row_split` 62개가 두 id로 두 번 돈다. 판정은 같고 비용만 는다.

## 작성 전 실측

(측정 2026-09-30, gate `master` HEAD `7535799`(엔진 소스는 cd64170과 같음 -- `git diff --stat cd64170 HEAD -- skills/`는 변경 0, tools/gates만 B28). 저장소 쓰기 없음, scratch `C:/g52`
(`git archive HEAD` 사본 + 스크립트, 끝나면 삭제). `$PY` = `C:/Python314/python.exe -B`.)

1. **사실 문장 재측정.**
   * 도구 읽기: `mutate_changed.py` `main`의 `approved = _approved(root, ns.head)`·`if mid in approved:` → `exempt`, `_approved` = `rch._approved_ids(root, rev)`. `reachability._approved_ids`는
     head 트리 `.ai/approvals/*.md`(이름이 `_`로 시작하는 것 제외) 중 `---\n`으로 시작하고 `\ntarget_kind: decision\n`이 있는 기록의 `target: ` 줄을 쉼표로 나눠 합집합. 소비처 3곳:
     `mutate_changed._approved`(V3), `reachability.main`(V7), `test_lint.py` 731행(V4 규칙 (1)) -- `grep -rn "_approved_ids" tools/`.
   * 승인 기록 머리 파서: `merge_gate.parse_approval_header`는 모르는 키를 거부하고(APPROVAL_KEYS 8개), decision `target` 원소는 비지 않음만 검사한다 → `@` 원소 허용, 새 키는 불가(그래서 새 키
     대신 원소 접미사).
   * HEAD의 decision 기록 10개, `_approved_ids(HEAD)` 원소 **26개**(`C:/g52/hash_anchor.py`): 결정 id 7(`C2-E4`, `C9-IC11-SPLIT`, `F4`, `U-01`, `U-02`, `U-38`, `U-39`), V3 모양 **14**
     (전부 `20260922-ic3-v3-exempt` -- `load_topology` 10, `save_instance_json` 4), V4 test id 2(`20260923-c9-v4-exempt`), V7 def id 2(`20260930-restore-unwired-until-6a`), probe 스캐너 1
     (`20260929-p4-scan-exempt`, `…probe_mirror_gain_ranking.py::lut-private` -- `_approved_ids` 소비처가 아닌 스캐너용).
   * **이행 근거(해시 없는 원소를 적용하지 않아도 잃는 것이 없다)** -- def 해시 앞 16자, `C:/g52/hash_anchor.txt`:
     * `load_topology`: 승인 커밋 `58e954c`(와 그 부모) = `104fac77…`, C8 code `6a4ded2`·병합 `6fe9cff`·판정 `0127bf5`·cd64170·HEAD = `c22bdd32…`. `6fe9cff..HEAD` first-parent에서 변경 0.
       → 면제가 승인한 형태(`c22bdd32…`)가 지금 base다. V3는 base와 해시가 다른 def만 변이하므로 뒤 card가 `load_topology`를 대상으로 삼는 순간 head 해시는 `c22bdd32…`가 아니다 --
       어떤 앵커를 붙여도 적용되지 않는다. fail-closed와 결과가 같다.
     * `save_instance_json`: 승인 커밋 = `0f519721…`, C8 병합 = `9cb09766…`, `b29be01`에서 `11a55c19…`로 바뀜(cd64170·HEAD). 승인한 형태는 이미 지나갔고 지금 도구는 그 4개를 여전히 적용한다
       (B26-1 시뮬레이션 head leak2 4/4). fail-closed가 의도(범위 설명)와 맞다.
     * **암묵 앵커(승인 커밋의 def 해시)는 틀린 앵커다**: V3 승인 기록은 card 병합 **전**에 master에 커밋된다(`58e954c` → 병합 `6fe9cff`) -- 승인 커밋의 def는 card 전 형태(`104fac77…`)다.
       V7 기록 `c31e0b6`에는 두 def가 아예 없다(`no-def`; 복원 병합은 `f1c4b7d`). 병합 커밋 앵커는 승인 기록에 card id가 기계 판독으로 없어 정할 수 없다.
   * B26-1 → B34 누수 619/1,402: `_drafts/b26_v3_leak.py`·`b26_v3_measure.out.txt`(C:/g39, cd64170) -- 재사용(auditor 측정 재사용 규칙). 엔진 소스가 HEAD와 같아 다시 재지 않았다.
2. **이름 충돌.** `ls tools/gates/redteam/attacks/` 마지막 = `31-v3-git-history` → `32-v3-exempt-binding` 없음. 출력 키 `exempt_ignored`·`survivor_bindings`: `grep -rn "exempt_ignored\|survivor_bindings" tools/ docs/` 0건.
3. **원칙의 계약화.** 조용한 면제 금지 → 계약 2·3(적용하지 않은 원소를 출력에 싣는다)과 8 (a). 거부 집합이 실제로 넓어짐(WP-02) → 계약 8 (a)·(b)·(d) attack. 다른 도구 무영향 → 계약 6.
4. **쓰기 경로.** `tools/gates/mutate_changed.py` = gmid-code-author(design 10 C11 행 "spec card `gate_change: yes` + 승인 기록일 때"), `tools/gates/redteam/**` = gmid-test-author(C10 행),
   design 05 §10·계획 N4.2 문구 = 오케스트레이터 문서 커밋(승인 기록이 덮는다). 설치 사본 재설치 불필요(`mutate_changed.py`는 §4.4 캐시에서 실행 -- B28 card와 같음).
5. **계획서 소비자.** `grep -rn "변이 id" docs/01-plan docs/02-design` → design 05 317행(고침), design 10 382행(C8 서술, 형식 주장 없음 -- 그대로), P9 spec card 118·168행(면제 형식 언급 -- 병합된
   기록이라 고치지 않음). agent 정의(`agents/gmid-verification-auditor.md` 41행)는 도구 이름만 -- 고칠 것 없음. 지우거나 옮기는 이름 없음.
6. **미배선.** 새 def를 만들면 `mutate_changed.main`이 부른다(V7 면제 불필요).
7. **기존 계약 test.** redteam `v3_survivor`·28·31·26·27f·29 -- 계약 7로 불변 판정. `tests/`의 엔진 test는 도구를 부르지 않는다.
