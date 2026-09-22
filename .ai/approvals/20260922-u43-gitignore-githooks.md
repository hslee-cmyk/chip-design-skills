---
id: 20260922-u43-gitignore-githooks
date: 2026-09-22
target_kind: staged_diff
target: 49a670ff1a6feab627b1a8af230620d90c4786164c300603c4bebd08eab02a0f
diff_base: f48f5f656851ec6268c17f8ba8eea1f04f48c85c
diff_path: .githooks/gmid_gate.py
diff_path: .gitignore
scope: U-43 -- .gitignore 기준선 예외 3줄 삭제(C5 병합 뒤)와 .githooks/gmid_gate.py 재설치 사본 커밋(20260921-gate-output-utf8·gate-flow-liveness §13.4)
---

## 사용자 원문

> 네가 해. 내가 허락할께.

(오케스트레이터의 `.gitignore` 쓰기는 EL1이 거부(사용자 전용 경로)해, 사용자가 `!`로 삭제·stage했다.)

## 범위 설명

덮는 것: `.gitignore` 17~19행(`# 예외: self-test 회귀 기준선은 추적한다 ...` 두 줄, `!skills/analog-gmid-design/assets/tests/baseline/*.log`) 삭제 --
U-43 확정(C5 `20260922-ts5-baseline-retire` 병합 뒤, design 10 §6.4), 이로써 design §10 D5 출력 0줄. `.githooks/gmid_gate.py`를 설치 원본
`tools/gates/githooks/gmid_gate.py`(두 게이트 변경 반영판)와 같게 한 재설치 사본.
덮지 않는 것: 다른 `.gitignore` 줄, `.githooks`의 다른 파일.
