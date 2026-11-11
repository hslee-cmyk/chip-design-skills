# ACTIVE — 진행 중인 작업 (작업메모리 색인)

> 모든 AI는 세션 시작 시 이 파일을 먼저 읽는다(Claude Code는 SessionStart hook이 자동 주입). 관련 작업이 있으면 그 파일만 열어 이어서 한다.
> 규칙: 작업 1개 = `working/<slug>.md` 1개(≤ 60줄), 여기엔 1줄씩(≤ 20줄). 작업 칸은 `[slug](slug.md)`, 상태 칸에 `진행`(hook이 이 두 칸을 읽는다). 끝나면 `/wrap`(증류) 후 둘 다 삭제.
> worktree: 이 repo의 다른 worktree에서 띄운 세션도 메인 worktree의 이 파일을 쓴다(hook이 찾아 절대 경로로 안내 — worktree에 `.ai/working`을 새로 만들지 않는다). 그 세션들의 자동 기록이 이 파일을 고치므로 작업 파일은 수시로 commit한다(미commit이면 메인 checkout의 branch 전환·병합이 막힐 수 있다).

| 작업 | 상태 | 한 줄 요약 | 갱신 |
|---|---|---|---|
