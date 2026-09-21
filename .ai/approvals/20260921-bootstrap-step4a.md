---
id: 20260921-bootstrap-step4a
date: 2026-09-21
target_kind: staged_diff
target: 020200ab39d16f6c34989f86b63364236e8258c2cd20617393e9d94579641087
diff_base: 8387e26ff008ea61115ea2f8d502020829e0c7a7
diff_path: .githooks/commit-msg
diff_path: .githooks/gmid_gate.py
diff_path: .githooks/pre-commit
diff_path: .githooks/pre-merge-commit
diff_path: .gitignore
scope: 부트스트랩 ④(a) -- .githooks 갱신(pre-commit·commit-msg·pre-merge-commit·gmid_gate.py)과 .gitignore 두 줄, hook 설치 전 한 번
---

## 사용자 원문

> 모델은 고치지 말고 4를 진행해.

## 범위 설명

덮는 것: 위 다섯 경로를 이 커밋에서 바꾸는 것. `.githooks/`의 네 파일은 부트스트랩 산출물(승인 기록 `20260921-bootstrap-outputs`)의 `tools/gates/githooks/`와 바이트 동일한 사본이다(새 pre-commit은 기존 agent 검사를 흡수했다). `.gitignore`에 `skills/analog-gmid-design/assets/library/*.search_archive/`와 `runs/`를 더한다(계획 N3.12.6 ①, EL2 무시 목록). 기존 `.githooks/pre-push`는 그대로 둔다. 이 경로들은 사용자 전용이고, 계획 N3.12.2에 따라 부트스트랩 ④(hook 설치 전)에 오케스트레이터가 이 승인 기록과 함께 한 번 쓴다.

덮지 않는 것: `.claude/**`(④(d) -- git 추적 대상이 아니다), gate 저장소(④(b), 사용자).

해시는 `tools/gates/merge_gate.py diff-hash --base HEAD --head :`(00-common §8.2 staged_diff, 승인 기록 자신은 제외)로 계산했다.
