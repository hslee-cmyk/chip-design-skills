# V8 N/A 문제 분석: Phase 4 첫 card들(B41·#2)과 게이트 rule10

작성 2026-10-06. 입력은 gate master `7243f28`(파일 읽기는 `git show 7243f28:<path>`)과 `_drafts/` 초안이다. 실측은 격리 복제본 `/c/g290`에서 했다(TMP/TEMP=`/c/g290/tmp`, clone `--no-hardlinks --no-local -c core.autocrlf=false -c core.hooksPath=`, origin 제거, `7243f28` detach). 끝난 뒤 `/c/g290`은 삭제했다. 실제 저장소는 `status --porcelain` 38줄, reflog 354줄로 시작과 끝이 같다.
이 기록은 작성자 측정이고 판정 수치가 아니다.

## 1. 결론

**(2) 계획이 서로 모순된다. 그래서 사용자에게 물어야 한다.** 게이트는 계획 N4.2 문장과 `00-common` §8.1 로더 규칙 10을 글자 그대로 구현했으므로, 그 조항만 놓고 보면 맞다. 그래서 design 40 P-38은 승인 안 된 초안이 그 조항과 충돌하는 것이고, 원칙 기본값으로 덮을 수 없다. 그런데 계획을 글자 그대로 따르면 #13 전 Phase 4 card의 V8은 어느 판정으로도 정직하게 병합할 수 없다.
- PASS: 측정할 대상이 없다.
- FAIL: 병합이 막힌다.
- N/A: 로더가 거부한다.

그러니 "P-38만 고치고 V8을 측정하면 된다"는 (1)이 성립하지 않는다.

## 2. 근거(줄 번호는 `7243f28`)

### 2.1 게이트 `tools/gates/merge_gate.py`
- 532–550 `rule10_phase`. 537 `if c["verdict"] == "N/A":`, 538 `intro = plan.v_intro.get(v)`. 541–542행에서 `order.index(spec_phase) < order.index(intro)`가 거짓이면 `LoaderReject(10, "%s N/A인데 Phase %s가 도입 %s보다 앞이 아니다")`를 낸다. 543–545행에서 basis가 `도입 (\S+?): `으로 시작하지 않거나 그 Phase가 intro와 다르면 거부한다.
- 118–149 `read_plan_tables_text`. `v_intro`는 계획 `### N4.2 ` 표의 '도입' 열에서 읽고, 괄호 밖 토큰이 정확히 하나여야 한다. `phase_order`는 `### N6.1 ` 표에서 읽는다. 사본은 없다.
- 1214–1217: `checks`에 `FAIL`이 하나라도 있으면 병합을 거부한다(`checks.%s = FAIL`).
- 547–549: basis 형식은 V4 PASS만 검사한다. **V8 PASS의 basis는 내용을 검사하지 않는다.**

### 2.2 계획 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`
- 835(N4.2 머리말): "'도입'은 병합 판정에 적용되는 Phase다. **도구는 모두 Phase 0.5에서 완성되고** … 도입 전 Phase에서는 PASS가 아니라 `N/A`로 적고 근거를 `도입 <Phase>: <사유>` 형식으로 쓴다(`00-common` §8.1)."
- 846(V8 행): "폴백 발동 0 | 정본 spec 실행 결과의 `fallback_events`{site, kind, device, detail}가 비어 있음 | **엔진 계측** | **4**".
- 1003(N6.1 Phase 4 행): Phase 4 범위 목록 안에 "`fallback_events` 계측(V8)"이 있다. 순서는 "TS4 → DF-35 → DF-36 → CC-4 앞부분 → CC-7·CC-8 → 나머지"이고, 계측은 '나머지'에 들어간다. 측정 도구인 CC-7·CC-8은 "이후 card에 쓰이도록 Phase 4 앞쪽에 둔다"고 명시했지만, V8 계측에는 그런 앞배치가 없다.
- 1021(N6.2 Phase 4 DoD): "**V8 도입**(정본 실행 `fallback_events` 0)". V8을 Phase 4가 *끝날 때 도입되는 것*으로 쓴 문장이다.
- 1031(N6.3): "auditor 판정 기록 PASS(N4.2 도입 표 기준)".

모순은 이렇게 생긴다. N4.2는 "도구는 0.5에서 완성되고 도입 Phase부터 병합 판정에 쓴다"를 전제로 한다. 그런데 V8의 도구는 엔진 계측이고, 계획 스스로 그 계측을 Phase 4 작업 항목(N6.1)으로 두었으며 DoD 문구도 "V8 도입"(N6.2)이다. 따라서 V8은 도입 Phase 안에서 도구가 생기는 유일한 검사다(V1~V7·V10은 0.5 도구가 있다). 결과적으로 "Phase 4 첫 병합부터 V8 판정"이라는 N4.2와 "V8은 Phase 4 중에 만들어 끝에 도입"이라는 N6.1·N6.2가 충돌한다.

### 2.3 `00-common` §8.1 (`docs/02-design/features/gain-budget-gmid-sizing.00-common.design.md`)
- 319 로더 규칙 10: N/A이면 "그 Phase가 `v_intro[Vn]`보다 `phase_order`에서 앞이고, `basis`가 `도입 <Phase>: <사유>` 형식으로 시작하며 그 `<Phase>`가 `v_intro[Vn]`과 같다". 게이트 537–545와 같은 내용이다.
- 400: "merge gate: 로더 규칙 10(§8.1)의 `N/A` 판정이 `v_intro`와 `phase_order`를 쓴다."
- 05-role-separation 297: "`checks`에 FAIL 없음, N/A는 로더 규칙 10."

여기에는 '도입 Phase 안 예외'가 없다.

### 2.4 design 40 초안 v0.9.11(`_drafts/draft_phase4_design.md`, 승인 전)
- 844 **P-38**: "#13 병합 전 card의 V8 판정 = N/A". 근거 칸은 "계획 N4.2 V8 도입 = 4 … 선례 `20260930-v3-exempt-binding` V2~V9 N/A"다.
  - **선례는 성립하지 않는다.** 그 기록은 Phase **0.5** card이고, V8 basis가 `도입 4: 폴백 발동 0 검사는 Phase 4부터(N4.2). 엔진 무관 게이트 변경`이다. 0.5 < 4라서 받아들여진 것이다. Phase 2 card 7건의 V8 N/A도 모두 `도입 4: …`이고 Phase가 4보다 앞이다. 도입 Phase 안에서 N/A를 쓴 선례는 0건이다.
- 1007 §10.1-0: P-38 문구 'N/A -- 계측 미도입(#13 전)'이 `도입 4: ` 형식도 아니다.
- 1043 §10.1-4: 발동 > 0인 지점은 I(계측)로 남는다. "V8 = 정본 실행 0이므로 **Phase 4 DoD 전까지** 원인 card가 병합돼야 한다." 즉 design 40도 V8을 사실상 **Phase 4 DoD 판정(E1, 654행)**으로 취급한다. #13 병합 뒤에도 원인 card가 들어오기 전까지는 정본 실행의 `fallback_events`가 비지 않을 수 있다. 그러면 card 단위 V8 PASS는 #13 뒤에도 보장되지 않는다.

### 2.5 card 초안
- `draft_b41_scope_note.spec.md` 3행 `phase: 4`, 90행 "V8: design 40 P-38(§10.1-0)에 따라 'N/A -- 계측 미도입(#13 전), 폴백 경로 불변'"
- `draft_p4_first.spec.md` 3행 `phase: 4`, 125행 "V8: design v0.9.9 P-38(§10.1-0)에 따라 'N/A -- 계측 미도입, 폴백 경로 불변'"

두 card 모두 지금 게이트에서는 로더 규칙 10에 걸려 거부된다(3절 실측).

### 2.6 승인 질문 초안 `_drafts/phase4_approval_question.md`
- 30행: "폴백 기록 계측(#13)이 들어가기 전 card의 폴백 판정(V8)은 '해당 없음'"을 원칙 기본안 예시로 든다.
- 95행: "**원칙 기본값(UD-0이 덮는다 -- 따로 묻지 않음)**: P-1~P-38((v0.9.9) **P-38** #13 전 card의 V8 = N/A …)".
- **어디에도 게이트 rule10·`00-common` §8.1 규칙 10·계획 N4.2와 충돌한다는 언급이 없다.** 사용자가 UD-0을 그대로 승인하면 게이트가 거부하는 규칙을 '따로 묻지 않는 기본값'으로 승인하게 된다. design 문서 승인이 상위 정본(계획 표, 00-common 로더 규칙)을 바꿀 수도 없다.
- `user_decisions.md`에 Phase 4 UD-0 답은 아직 없다(마지막은 2026-10-02 Phase 3 절). `7243f28` `.ai/approvals/`에도 40-defect-fixes 승인 기록이 없다. 그래서 지금 고쳐도 되돌릴 승인은 없다.

## 3. 실측(`/c/g290`, `7243f28`, 실제 계획 표를 `read_plan_tables`로 읽음)

`v_intro` = {V1..V6: 1, V7: 2, **V8: 4**, V9: 6b, V10: 0.5}, `phase_order` = [0.5, 1, 2, 3, 4, 5, 6a, 6b, 6c, 7a, 7b, 7c].

`rule10_phase` 직접 호출(다른 V는 형식에 맞는 값으로 채움):

| spec phase | V8 verdict | basis | 결과 |
|---|---|---|---|
| 4 | N/A | `N/A -- 계측 미도입, 폴백 경로 불변`(P-38 문구) | **reject**: 로더 규칙 10: V8 N/A인데 Phase 4가 도입 4보다 앞이 아니다 |
| 4 | N/A | `도입 4: 계측 미도입(#13 전), 폴백 경로 불변` | **reject**(같은 메시지 -- 형식을 맞춰도 Phase 비교에서 거부) |
| 3 | N/A | `도입 4: …` | accept(대조군) |
| 4 | PASS | `계측 미도입 -- fallback_events 키 없음` | **accept** -- basis를 보지 않는다 |
| 4 | FAIL | `계측 미도입` | 로더는 accept, 병합 검사 1216에서 거부 |

`fallback_events`를 `skills/**`·`workspaces/**`의 `.py`에서 grep하면 0건이다(`git grep`의 `.md` 아닌 결과는 `.ai/verification/*.json`의 N/A basis 8건뿐). **계측이 없으므로 정본 실행 산출물에 그 키 자체가 없다.** design 40 §10.1-2(1026행)는 "키가 없으면 E1 FAIL(계측 미배선)"이라고 한다. 이 상태에서 정본 하네스 실행은 V8에 쓸 출력을 만들지 못하므로 돌리지 않았다. 측정 대상이 없다는 사실은 grep으로 확정된다.

### (1)을 가정할 때 B41·#2의 V8 PASS 조건과 가능성
- PASS 조건(N4.2 846): 그 card 병합본에서 사이징 대상 4회로의 정본 spec을 실행하고, 그 결과의 `fallback_events`가 존재하면서 빈 목록이어야 한다(design 40 E1 판정 방식과 같다).
- `7243f28`(그리고 #13 전 모든 base)에서는 **불가능하다.** 키를 만드는 코드가 없다. "키 없음 = 비어 있음"으로 PASS를 적으면 로더는 받지만(위 표 4행), 계측 없이 발동 0을 주장하는 것이다. 이는 작성자≠검증자·자기결함 은폐 금지 원칙(§14)과 "게이트는 실제로 거부하는가" 원칙에 어긋난다. 그래서 선택지에서 뺀다.
- 대안 측정인 design 40 §10.1-4의 '사본 계수 래퍼'(AST로 D·I 지점의 기본값 사용·핸들러 진입을 외부에서 세기)는 V8 정의의 `fallback_events` 필드가 아닌 대리 지표다. §10.1-4 자체가 지금 발동 > 0 지점이 있으리라 예상한다(I 분류의 존재 이유). 그래서 대리 측정을 해도 #13·원인 card 전에는 FAIL이 나올 가능성이 높고, 그러면 병합이 막힌다.
- #13을 맨 앞으로 당겨도 같다. 원인 card가 병합되기 전에는 정본 실행의 `fallback_events`가 빌 보장이 없다(§10.1-4). 그러면 #13 자신과 그 뒤 card가 V8 FAIL로 막힌다.

## 4. 원칙 기반 기본안

- 기준 정본은 계획이다(N4.2·N6.1·N6.2). 그런데 계획끼리 충돌하므로 오케스트레이터가 혼자 정하지 않는다. 판정 기준을 바꾸는 일이라 사용자 승인이 필요하다.
- 게이트 우회 금지: P-38을 그대로 쓰거나 공허한 PASS를 적으면 안 된다.
- 최소 변경 + 실제 거부 유지: N6.2 Phase 4 DoD의 "V8 도입(정본 실행 `fallback_events` 0)"과 design 40 E1이 이미 Phase 4 끝의 실측 판정을 갖고 있다. V8 '도입' 열을 **5**로 정정하면 다음이 모두 일관된다.
  - N4.2 "도입 = 병합 판정에 적용되는 Phase"
  - N6.1 "계측은 Phase 4 작업"
  - N6.2 "Phase 4 DoD에서 V8 도입"

  게이트 코드 변경은 0이다(게이트가 표를 직접 읽는다). Phase 4 card는 `도입 5: <사유>` N/A로 로더를 통과한다. Phase 4 DoD는 E1(4회로 키 존재 + 빈 목록)로 V8을 실측하고, Phase 5 병합부터 card마다 V8이 걸린다. 실제로 거부하는 판정(E1)은 그대로 남는다.
  - 보완: #13 병합 뒤 Phase 4 card는 N/A basis에 '참고 측정 `fallback_events` = …'(선례 `20260930-v3-exempt-binding`의 "참고 실행" 모양)를 적는다고 design 40 §10.1-0에 규정한다. 이렇게 하면 새 폴백 유입을 card 단위로 기록한다.
  - 절차: 계획 표 개정이므로 승인 기록(target_kind `plan_tables`, 선례 `20261002-p3-f1-workspaces-write-path`), plan_tables 해시 갱신, history 기록이 필요하다. B41·#2의 V8 줄과 design 40 P-38·§10.1-0 문구는 `도입 5: 폴백 계측은 Phase 4 작업(N6.1), V8은 Phase 4 DoD(E1)에서 도입 -- 이 card는 부록 C 사이트 불변`으로 고친다.
- 같은 구조가 다시 생길 곳: V9(도입 6b, 도구 'contracts test'). 그 판정 대상인 봉인 항목 N3.6·IC1은 6b 작업으로 생긴다(N6.1 6b 행 "IC1·IC2·IC9·IC10 활성"). 6b 착수 전에 같은 점검이 필요하다. 이 질문에는 넣지 않고 백로그 후보로 둔다.

## 5. 사용자 질문 초안(AskUserQuestion, 1문항)

```json
{
 "questions": [
  {
   "header": "V8 도입",
   "multiSelect": false,
   "question": "계획 N4.2는 V8(폴백 발동 0)을 Phase 4 첫 병합부터 card마다 판정하라고 하고(도입 = 4, 도입 Phase에서는 N/A 불가 -- 00-common §8.1 규칙 10, 게이트 merge_gate.py 537~545가 그대로 거부), N6.1·N6.2는 그 계측(fallback_events) 자체를 Phase 4 작업으로 두고 'Phase 4 완료 때 V8 도입'이라고 씁니다. 지금(7243f28) 엔진에 fallback_events가 없어 #13 전 Phase 4 card(첫 card B41·#2 포함)는 V8을 PASS로 잴 수 없고, FAIL이면 병합이 막히고, N/A는 로더가 거부합니다(격리 복제본 실측). design 40 초안 P-38('#13 전 card V8 = N/A')은 이 규칙과 충돌하며 Phase 4 승인 질문에는 '따로 묻지 않는 기본값'으로만 들어가 있습니다. 어떻게 정할까요?",
   "options": [
    {
     "label": "V8 도입을 5로 (Recommended)",
     "description": "계획 N4.2 V8 '도입' 칸 4→5(계획 표 개정 승인 기록 1건, 게이트 코드 변경 0). Phase 4 card는 `도입 5: …` N/A(#13 뒤 card는 참고 측정값을 basis에 적음), V8 실측은 Phase 4 DoD E1(4회로 fallback_events 키 존재·빈 목록)이 하고 Phase 5부터 card마다 판정. N6.2 'Phase 4 완료 때 V8 도입' 문구와 일치."
    },
    {
     "label": "게이트에 예외 추가",
     "description": "도입 4 유지, 00-common §8.1 규칙 10과 merge_gate rule10을 고쳐 '도입 Phase 안에서 계측 card(#13) 병합 전'의 N/A를 허용(게이트 변경 card 1건 + redteam 공격 추가, 계측 존재를 게이트가 판별할 규칙 필요). #13 뒤에도 원인 card 전까지 발동 > 0이면 card마다 FAIL로 막히는 문제는 따로 정해야 함."
    },
    {
     "label": "#13·원인 card 먼저",
     "description": "규칙은 그대로 두고 Phase 4 순서(N6.1)를 바꿔 #13과 발동 지점 원인 card를 B41·#2보다 먼저 병합. #13의 선행 card와 발동 > 0 지점 때문에 그 card들 자신이 V8 FAIL로 막힐 수 있어 실현 가능성 미확인(§10.1-4 사본 계수 실측 먼저 필요)."
    }
   ]
  }
 ]
}
```

## 6. 답을 받은 뒤 바꿀 곳(기본안 선택 시)
1. 계획 N4.2 V8 행 '도입' 4→5. 머리말 "도구는 모두 Phase 0.5에서 완성"에 'V8 계측은 Phase 4 작업(N6.1)' 예외를 한 줄 추가한다. 이와 함께 승인 기록(plan_tables)과 history H 항목을 쓴다.
2. design 40 P-38·§10.1-0 문구를 `도입 5: …` 형식과 참고 측정 규정으로 고치고, E1을 V8 도입 판정으로 명시한다.
3. `draft_b41_scope_note.spec.md` 90행·`draft_p4_first.spec.md` 125행 V8 줄, `p4_first_briefs.md` §0.2 조치를 (가)로 확정한다(basis 형식 = `도입 5: `).
4. `phase4_approval_question.md` 30·95행에서 P-38을 'UD-0이 덮는 기본값'에서 빼고 이 질문의 결과를 인용한다.
5. 백로그 후보: V9(도입 6b)도 도구가 도입 Phase 안에서 생기는 같은 구조인지 6b 착수 전에 점검한다.
