# 운영·안전 F (원칙 28–33)

> 정본. 2026-11-12 CLAUDE.md 개정(docs/01-plan/features/claude-md-restructure.plan.md)으로 옛 CLAUDE.md 원문을 그대로 옮겼다(의미 변경 0).
> 원칙 29의 셸 추가 쓰기 금지는 `.claude/hooks/append_guard.py`가 강제한다.

28. git은 `git -C`만 쓰고, 순서 있는 명령은 `&&`로 잇는다(Bash 도구 맨 위 `set -e`는 작동하지 않고, 파이프는 실패를 가리니 병합·커밋 줄에 쓰지 않는다). reset·checkout·stash(master·다른 worktree) 금지, push 금지. 승인 커밋 먼저, 병합 순서 plan → master → integ. 커밋 트레일러(`--trailer`; `git merge`는 둘째 `-m`).
29. 프로젝트 파일 수정은 Edit/Write 또는 Python 바이너리 치환만. **heredoc append 금지.**
30. 측정 스크립트·결과는 evidence 폴더에 파일로(케이스마다 append). 장시간 실행은 background.
31. agent 재개 목록(`wt/_drafts/agent_resume_list_*.md`) 갱신, worktree 주기적 정리.
32. agent 모델: 코드 = sonnet, 문서·분석 = opus, description 앞에 [opus]/[sonnet].
33. 목표는 엔진. legacy test는 버려도 된다. 인프라 작업은 엔진을 막을 때만.
