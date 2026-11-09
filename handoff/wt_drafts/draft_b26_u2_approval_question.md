# A2(U2 + B34 앞당김) 승인 -- `20260930-b26-before-phase3`

v2(2026-10-01, review2_b34 B1 반영). v1(`draft_b26_u2_approval_question.v1.md`)은 실제로 묻기 전의 초안이었다. 그래서 질문 원문·`scope`·'덮는 것'이 B26-1만 적었다.
사용자에게 실제로 물은 것은 아래 A2 질문이다. ③에 B26-1과 B34가 함께 있다. 답은 "승인 (Recommended)"이다(질문 2026-09-30, 답 2026-10-01, `user_decisions.md` A2).
그래서 기록은 실제 질문을 인용하고 B26-1과 B34를 함께 덮는다. 별도 B34 기록 초안(`draft_b34_approval_question.md`, `20260930-b34-before-phase3`)은 폐기됐다.

이 기록을 가리키는 spec card:
* B26-1 `20260930-b26-rail-accessor-set`(`draft_b26_1.spec.md`)
* B34 `20260930-b34-grammar-explicit`(`draft_b34.spec.md`)

두 card의 머리 `approval` 줄이 모두 이 id다. 기록 파일은 두 card 커밋보다 **먼저** gate에 있어야 한다(계획 정정 커밋과 함께, 오케스트레이터).

## 실제로 물은 질문(AskUserQuestion 원문, 고치지 않음)

> [A2] 다음 세 가지를 한 건의 승인 기록으로 받아도 될까요? ① DEC-60의 '넷 이름으로 전원을 판정하는 전환기' 조항을 끝냅니다. 앞으로 전원은 topology의 supply_nets 선언으로만 정하고, 선언이 없으면 오류를 냅니다. ② DF-19·DF-26 가운데 전원 넷 판정 부분을 MG1(전압값 작업)과 분리합니다. ③ B26-1(전원 선언을 읽는 접근자와 '전원인가'만 묻는 곳 교체)과 B34(analog-grammar가 없으면 조용히 폴백하던 것을 명시적 오류로 바꿈)를 Phase 3 모듈 분할보다 먼저 합니다. 먼저 하면 모듈 분할 때 생기는 역방향 import와 이동 비용이 줄어듭니다. 9회로 결과는 사본 실측에서 같았습니다.

선택지(원문):
* **승인 (Recommended)** -- 승인 기록 1건으로 ①②③을 모두 덮습니다. 계획서 정정 커밋과 함께 올리고, B26-1·B34 spec card의 approval 줄이 이 기록을 가리킵니다.
* **①②만 승인, ③은 Phase 3 뒤** -- 계획서 정정만 하고 B26-1·B34는 Phase 4 순서대로 둡니다. 모듈 이동이 이름 기반 전원 상수를 함께 옮기게 됩니다.
* **보류** -- B26-1·B34를 착수하지 않고 P10·P10b와 Phase 2 완료 판정까지만 진행합니다.

사용자 답: **"승인 (Recommended)"**.

## 승인 기록

* 커밋할 최종본은 `_drafts/approval_20260930-b26-before-phase3.md`다. 내용 그대로 `.ai/approvals/20260930-b26-before-phase3.md`로 쓴다.
* 머리 블록은 `C:/Python314/python.exe -B tools/gates/merge_gate.py parse-approval`로 파싱 통과를 확인했다. scratch에 `<id>.md` 이름으로 복사해 돌렸고 rc 0, `target_list` = `["U2-B26-BEFORE-PHASE3"]`이었다.

요지:
* `target_kind: decision`, `target: U2-B26-BEFORE-PHASE3`, `date: 2026-10-01`.
  * `date`는 사용자 답 날짜다. id 앞 8자리 20260930은 질문 날짜이고, 두 card가 이미 이 id를 가리킨다.
  * 파서는 id 날짜와 `date`가 같기를 요구하지 않는다(`parse_approval_header`·로더 규칙 6 확인).
* `scope`: ①②와 함께 **B26-1과 B34를 card id로** 적는다. B34의 동작 변경(analog-grammar 부재 → `ImportError`)을 명시한다.
* '덮는 것':
  * ①②의 계획 정정 항목(v1과 같은 목록, `draft_b26_plan_patch.md` §1~§6).
  * B26-1의 Phase 2 병합.
  * **B34의 Phase 2 병합과 동작 변경.** def 4개가 바뀐다: `_import_analog_grammar`는 예외를 다시 던지고, `find_idiom_matches`·`find_stack_edges`·`audit_theta_root_direction`은 부재 분기를 지운다.
  * 운영 경로 큰 def 분기를 B26-1·B35로 넘기는 순서.
* '덮지 않는 것': 레일 전압(MG1), B26-2·B26-3 방식, **V3·V7 면제 일체(B34는 V3 면제 없음)**, `install.py`(사용자 작업), sys.path 주입 방식 R1, B35·B36, 판정 표.

## target 값 근거

* V3 도구와 V7 도구는 head 트리의 **모든** decision 승인 기록 `target` 원소를 면제 id로 읽는다(`reachability._approved_ids`).
* 그래서 target은 def id(`<파일>::<qualname>`)나 변이 id(`<모듈>:<qualname>:<연산자>:<경로>`) 모양이 아닌 결정 이름으로 둔다. 기존 결정 기록 `U-02`·`U-38`·`U-39`·`C9-IC11-SPLIT`과 같은 방식이다.
* B26-1과 B34 모두 이 기록으로 면제를 받지 않는다. 그래서 다른 원소를 더하지 않는다. 같은 이름의 기존 `target` 원소는 없다(`.ai/approvals/*.md` grep 0).
* 이름은 v1과 card 문서가 이미 쓰는 `U2-B26-BEFORE-PHASE3`을 유지한다. B34가 덮인다는 사실은 `scope`와 본문이 적는다. 이름을 바꾸면 이미 쓴 문서 참조만 늘어난다.
