---
id: 20260930-phase2-e4-baseline
date: 2026-09-30
target_kind: diff
target: 0d8ae146eefc5459fae1bae0511b0c2af18cd1aaa3eb8cfb419e972caf6a8904
diff_base: 8790b24cac0f809129d179a5752e4d611f6f5fa8
diff_head: 2140da8ac9ebf835ec877488e0c3ac7199146ac5
diff_path: docs/02-design/features/gain-budget-gmid-sizing.20-dead-code-dup.design.md
scope: design 20-dead-code-dup §10 E4(Phase 2 DoD 동작 보존 기준값) 정정 승인 -- Phase 2 완료 판정 착수 조건
---

## 사용자 원문

> 둘다 기본안으로 진행해

(질문 맥락: Phase 2 DoD 사전 점검 결과 결정 D1·D2를 보고했고, 사용자가 "1번을 좀더 설명해"라고 해 설명했다 -- E4 원문 "Phase 1 DoD와 같은 값(회로 9/9 로드,
instance.json 해시 동일)"은 Phase 1 DoD 기록에 E-LIB·E-INST 값이 없고 DF-36이 `topology_ref`를 의도적으로 바꿔 그대로 잴 수 없다, 기본안 = da03c0e와 Phase 2
마지막 병합본을 같은 경로에서 비교하고 `topology_ref`만 DF-36 계약값으로 판정, 대안 = card별 판정 기록 사슬로 갈음. 그 뒤 사용자 원문. 교체 문안은 정정 커밋
2140da8에 그대로 반영했다.)

## 범위 설명

덮는 것: design 20 §10 E4 행 교체(비교 기준을 Phase 1 DoD 대상 커밋 da03c0e의 같은 경로 실측으로, E-LIB `hash` 동일, E-INST `without_topology_ref_sha256` 동일 +
병합본 `topology_ref` = DF-36 계약 1 값, da03c0e 판은 DF-35 base 모드) -- 판정 기준 변경.
덮지 않는 것: E0~E3·E5, 결정 D2(남은 probe 관찰 기록 -- 기준 변경 아님), 계획 N6.2 문장.
