---
id: 20261001-b47-md-sync
date: 2026-10-01
target_kind: decision
target: B47-MD-SYNC
scope: 백로그 B47 -- library 추적 md 2개(folded_cascode·current_reuse_telescopic_ota) 재생성 문서 커밋(Change-Id 20261001-topology-md-sync) + md·json 일치 영구 test card 20261001-topology-md-sync(test-only, 단독) 진행 -- 오케스트레이터가 알린 B47 처리 방침 1·2에 대한 사용자 답
---

## 사용자 원문

오케스트레이터 보고(2026-10-01 15:30 KST, B47 점검 결과와 처리 방침 -- 고치지 않고 그대로 옮긴다):

> B47 점검이 끝났습니다. library의 추적 md 6개 가운데 2개가 json과 어긋나 있고, 2개 모두 connectivity 표가 다릅니다.
>
> | 회로 | 어긋난 내용 | 원인 |
> |---|---|---|
> | folded_cascode | M1·M2 게이트 net이 서로 바뀌어 있음 | 9/17 입력 극성 정정 커밋(7ec8eff)에서 json만 고치고 md는 다시 만들지 않음 |
> | current_reuse | 수동소자 6개(CL·Cf·Cs)가 빠짐 | 9/10 커밋(8ae82e7)에서 json에 소자를 추가하고 md는 다시 만들지 않음 |
>
> - 나머지 4개 md는 json과 바이트 단위로 같습니다.
> - 이 md를 읽는 test, 게이트, 기준선은 없습니다. 다시 만들어도 판정은 바뀌지 않고, DEC-40과도 관계없습니다.
> - 위험은 사람이 읽을 때 생깁니다. 특히 UD-17 공동분석처럼 회로도와 대조할 때 틀린 표를 보게 됩니다.
> - md와 json이 일치하는지 검사하는 test가 없어서 이런 어긋남이 생겼습니다.
>
> **처리 방침 (원칙상 기본안이라 따로 여쭙지 않고 진행합니다)**
> 1. **md 2개 재생성:** 계획 쓰기 경로표상 이 md는 승인 조건이 없는 파생 문서입니다. 다음 문서 커밋에 함께 넣겠습니다. 커밋 전에 다른 4개 md의 diff가 0인지 확인합니다.
> 2. **일치 test card 추가:** md 표를 직접 파싱해 json과 대조하는 test-only card입니다. 렌더러를 부르지 않으므로 작성자와 검증자가 분리됩니다. 재발 방지를 위한 것이고, spec card 초안을 띄웠습니다(C:/g95).
>
> 이 방침과 다르게 하시려면 말씀해 주세요.
>
> 지금 6개가 돌고 있습니다.
> - P10b base 확인
> - B26-1 수정
> - B26-1 보강 card 초안
> - Phase 3 v6 최종 검토
> - Phase 4 v0.6
> - md 일치 test card 초안

사용자 답(2026-10-01 15:32 KST):

> 응, 그렇게 진행해

같은 날 md 일치 card 독립 검토 요약(16:34 KST) 뒤에도 같은 답을 받았다. 그 요약 원문:

> md 일치 card 검토가 끝났습니다. 측정값은 초안 주장과 모두 일치했고, 막는 문제 3건은 검토자가 정정본(`draft_md_sync.reviewed.spec.md`)에 반영했습니다.
>
> **확인된 것**
> - md를 다시 만들었을 때 나올 blob 값, 나머지 4개 md가 diff 0이라는 점, 변경 줄 수가 기대대로입니다.
> - 검토자가 card 문장만으로 판정기를 따로 짜서 돌렸습니다.
>   - 지금 md에서 실패하는 (계약, 파일) 쌍은 정확히 5개입니다.
>   - 다시 만든 md 6개는 모두 통과합니다.
>
> **막는 문제 3건 (정정본 반영)**
> 1. **재생성 명령이 그대로는 실행되지 않습니다.**
>    - 임시 디렉터리를 지우는 줄과 push 형태가 역할 게이트에 막힙니다.
>    - 고친 명령 블록을 검토 문서에 넣었습니다.
> 2. **판정 담당이 실패 쌍을 다 볼 수 없었습니다.**
>    - test가 첫 실패에서 멈춰 나머지 쌍이 가려졌습니다.
>    - 실패를 모두 모은 뒤 `계약 <k> <파일>` 형식으로 한 번에 내도록 바꿨습니다.
> 3. **변경 범위 계약이 너무 넓었습니다.**
>    - 다른 card의 문서 커밋까지 범위에 섞였습니다.
>    - 이 card의 Change-Id 커밋만 보도록 한정했습니다.
>
> **승인 기록**
> - 게이트 규칙상 필수는 아닙니다.
> - 다만 이 card를 덮는 승인이 아직 없어서 decision 기록을 남기는 편이 맞습니다.
> - 커밋할 때 제가 드린 제안(md 2개 재생성 + 일치 test card 추가)과 "응, 그렇게 진행해" 답을 원문 그대로 인용해 기록하겠습니다.
>
> **동시 작업이 5개인 이유**
> 남은 일은 대부분 P10b push 뒤의 문서 커밋·Phase 2 완료 판정과, B26-1 결정 대기에 묶여 있습니다. 그래서 지금 새로 띄울 준비 작업이 없습니다. P10b 판정이 나오면 바로 채우겠습니다.
>
> 지금 돌고 있는 5개:
> - P10b 판정
> - B26-1 수정
> - Phase 3 v7
> - 보강 card 검토
> - Phase 4 승인 전 검토

사용자 답(2026-10-01 16:40 KST):

> 응, 그렇게 진행해

(같은 날 같은 문구가 card 순서 보고의 답으로도 쓰였다(`_drafts/user_decisions.md` 2026-10-01 card 순서). 이 기록이 덮는 것은 위 두 오케스트레이터 메시지에 대한 답이다.
위 15:30 보고는 질문이 아니라 "원칙상 기본안이라 따로 여쭙지 않고 진행"한다는 알림이었고, 사용자는 다르게 하라는 지시 없이 진행을 확인했다.)

## 범위 설명

덮는 것:
* (1) `skills/analog-gmid-design/assets/library/folded_cascode.topology.md`·`current_reuse_telescopic_ota.topology.md`를 현재 json으로 다시 만드는 `Role: doc` 문서 커밋
  (`Change-Id: 20261001-topology-md-sync`, assets에서 `python -B topology_to_markdown.py library/<n>.topology.json`). 나머지 4개 md는 차이 0을 확인하고 바꾸지 않는다.
  보고 1번은 "다음 문서 커밋에 함께" 넣는다고 했지만, card 계약 9(이 card `Change-Id` 커밋으로 범위 한정)와 계약 8(`measured_at` = 재생성 커밋의 부모) 때문에
  재생성은 Change-Id를 단 별도 문서 커밋으로 한다(16:34 요약의 막는 문제 3 반영 -- 같은 내용, 커밋 경계만 다름).
* (2) spec card `20261001-topology-md-sync`(test-only) -- 새 영구 test `skills/analog-gmid-design/assets/tests/contracts/test_topology_md_sync.py` 하나가
  library 추적 md 표를 직접 파싱해 같은 이름의 json과 대조한다(렌더러를 import·실행하지 않음). 다른 card와 묶지 않고 단독으로 진행한다(보고 2번에 묶기 언급 없음,
  지금 묶을 test-only card 없음).

덮지 않는 것:
* library `*.topology.json`·엔진·렌더러(`topology_to_markdown.py`) 변경, `소스:` 줄 경로 정규화와 렌더러가 출력 경로 없이 추적 md를 덮어쓰는 기본 동작(별도 백로그),
  md가 없는 4회로(`_TEMPLATE`·`common_gate_amplifier`·`nmcnr_amplifier`·`two_stage_ota`)의 md 신설.
* 기준 약화(없음 -- 검사를 더하는 card다, DEC-40 무관), V3·V4·V7 면제(없음). 이 기록의 `target`(`B47-MD-SYNC`)은 결정 이름이며 변이 id·test id·`<path>::<rule>`이 아니다.
* 판정 표(`plan_tables_hash` 입력: N4.1·N4.2 `도입`·N6.1 `Phase` 열·N3.12.2) -- 바꾸지 않는다.
