---
id: 20261001-p2dod-e2-wording
date: 2026-10-01
target_kind: diff
target: <rev-parse>
diff_base: <rev-parse>
diff_head: <rev-parse>
diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
scope: design 20-dead-code-dup §10 E2(Phase 2 DoD probe 엔진 식 재구현 0) 통과 기준을 'exit 0, 발견 0'에서 'exit 0, 면제되지 않은 발견 0'(면제 = decision 승인 기록의 path::rule로 스캐너가 exempt true를 붙인 발견, 현재 20260929-p4-scan-exempt 1건, DoD 기록에 path·line·rule·승인 id)으로 정정 -- Q-P2DOD-E2, Phase 2 완료 판정 착수 조건
---

## 사용자 원문

> 문구 정정 (Recommended)

(AskUserQuestion 답, 2026-10-01 19:25 KST. 질문 원문(2026-10-01 19:21 KST, 고치지 않고 그대로): "[Q-P2DOD-E2] Phase 2 완료 판정 E2(probe 중복 스캐너)의 기준 문구와 실제 스캐너 계약이 어긋납니다. design 20 §10 E2는 'exit 0, 발견 0'(2026-09-23 작성)인데, 그 뒤 2026-09-29에 '승인대로 진행'하신 면제(20260929-p4-scan-exempt)로 스캐너는 면제된 줄도 '발견'으로 출력하되 exempt:true를 붙이고 exit 0을 냅니다. 지금 결과는 면제 발견 1건(probe_mirror_gain_ranking.py:183 lut-private), exit 0입니다. design 문구 그대로면 E2 FAIL, 스캐너 계약('면제 아닌 발견 0')대로면 PASS입니다. 판정 기준 문구를 바꾸는 것이라 승인이 필요합니다. 어떻게 할까요?"
선택지: "문구 정정 (Recommended)" -- "Phase 2 완료 판정 전에 design E2를 'exit 0, 면제되지 않은 발견 0(면제 = decision 승인 기록이 적힌 path::rule, 현재 1건)'으로 고치는 커밋 + 승인 기록을 넣습니다. 이미 승인하신 면제를 완료 기준에 반영하는 것이고 기준을 새로 느슨하게 하는 것은 아닙니다." /
"문구 그대로 판정" -- "E2 FAIL로 Phase 2 완료 판정이 FAIL이 됩니다. 면제는 Phase 4 LUT 공개 조회 API card에서 해소됩니다." /
"면제 자체를 없앰" -- "Phase 2 안에 LUT 공개 조회 card를 앞당겨 면제 줄을 없앤 뒤 완료 판정을 합니다. Phase 4 일을 앞당기고 범위가 늘어납니다."
사실 보충: 질문의 "'승인대로 진행'하신"은 요약이다 -- 승인 기록 `20260929-p4-scan-exempt`의 사용자 원문은 "제안대로 승인 (Recommended)"(2026-09-29)이다. 질문 준비 문서: `_drafts/pending_questions.md` Q-P2DOD-E2, 드라이런 `_drafts/phase2_dod_dryrun.md` E2 행.)

## 범위 설명

덮는 것: design 20 §10 E2 행의 '통과 기준' 칸 한 줄 교체(정정 커밋 = 이 기록의 `diff_head`, Change-Id `20261001-p2dod-e2-wording`) -- 옛 "exit 0, 발견 0"을 "exit 0, 면제되지 않은 발견 0(면제 = `target_kind: decision` 승인 기록이 적은 `<path>::<rule>`로 스캐너가 `"exempt": true`를 붙인 발견 -- 현재 승인 `20260929-p4-scan-exempt` 1건; 면제 발견은 DoD 기록에 path·line·rule·승인 id로 적는다)"로 바꾼다 -- 판정 기준 문구 변경.
근거: 스캐너 계약(P4 spec card `20260929-probe-engine-dup` 계약 1 -- 면제 줄도 '발견 한 건'으로 출력하고 `"exempt": true`를 붙여 exit 판정에서 뺀다, `main --root <병합본>` exit 0 = 면제 아닌 발견 0)과 그 면제 승인(2026-09-29)을 DoD 문구에 반영한다. 새 면제를 더하지 않는다.
덮지 않는 것: 새 면제(각각 별도 `target_kind: decision` 승인 기록 필요), 스캐너 범위(`tests/probes/**` -- 결정 D2 (a) 그대로, `tests/probe_physical_consistency.py`는 범위 밖 관찰), 스캐너 코드·규칙, E2 측정 명령, E0·E1·E3·E4·E5, 계획 N6.2 문장.

## 재검토

면제 `20260929-p4-scan-exempt`가 Phase 4(LUT VGS 기준 gm·gds 공개 조회)에서 지워지면 design E2 칸의 '현재 승인 … 1건' 문구도 같은 card에서 고친다(그 뒤 면제 0건이면 '면제되지 않은 발견 0' = '발견 0').
