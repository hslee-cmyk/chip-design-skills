---
id: 20260930-restore-unwired-until-6a
date: 2026-09-30
target_kind: decision
target: skills/analog-gmid-design/assets/sizing_recipe.py::lut_conditions_from_npz, workspaces/run_harness.py::derived_spec
scope: 복원 card 20260930-restore-plan-functions -- 되살린 두 함수를 운영 경로에 배선하지 않은 채 두는 V7 미도달 면제(계획 I-A5·DEC-26 소비처가 생길 때까지)
---

## 사용자 원문

> 승인 (Recommended)

(질문: 복원하는 두 함수(lut_conditions_from_npz·derived_spec)를 계획대로 Phase 6a(S0 지문 배선, I-A5)까지 운영 경로에 배선하지 않은 채 둘까요? (V7 미배선 면제
승인 -- derived_spec은 DEC-26에 따라 spec 변형이 필요할 때 쓰는 경로이고 지금 호출자는 test뿐) -- 선택지 '승인 (Recommended)': decision 승인 기록(target = 두 def id),
재검토 조건 = Phase 6a S0 구현 때 lut_conditions_from_npz 배선, derived_spec은 spec 변형이 필요한 첫 사용처에서 배선)

## 범위 설명

덮는 것: V7(reachability) 미도달 판정에서 위 두 def id를 면제한다. 두 함수는 P5에서 잘못 지워져 복원하는 것이고, 계획서가 소비처를 정해 두었다 --
`lut_conditions_from_npz`는 N3.3 S0 지문(LUT 생성 메타)과 I-A5(6a에서 S0에 배선), `derived_spec`은 DEC-26(spec 변형의 유일한 경로, 짝 게이트 `require_declared_spec_source`).
덮지 않는 것: 다른 def의 미도달, 두 함수의 동작 변경.

## 재검토

Phase 6a S0 지문을 구현하는 card에서 `lut_conditions_from_npz`를 배선하고 이 면제에서 그 id를 뺀다. `derived_spec`은 spec 변형이 필요한 첫 운영 사용처(하네스 조사·
탐색 card)에서 배선하고 id를 뺀다. 두 id가 모두 빠지면 이 기록은 효력이 없다.
