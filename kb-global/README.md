# kb-global → ai-memory로 이전됨 (2026-11-10)

전역 장기지식(영구메모리)의 정본과 RAG 툴링은 별도 repo **ai-memory**로 옮겼다.
어느 PC·프로젝트·AI에서도 쓰기 위해 칩 키트에서 분리했다.

| 무엇 | 새 위치 |
|---|---|
| 원칙 정본 (구 `kb-global/principles/`) | `ai-memory/memory/<domain>/*.md` |
| `kb_index/kb_search/kb_eval/eval_gate.py` | `ai-memory/tools/` (경로 해석 `am_paths.py`) |
| 골드셋 `eval/queries.json` | `ai-memory/eval/queries.json` |
| 인덱스 (구 `fpga/.tools/kb-global/kb.sqlite`) | `AI_MEMORY_HOME`(기본 `~/.ai-memory/`)`/kb.sqlite` |
| `agent-kit/failure-taxonomy.md` | `ai-memory/memory/rtl/failure-taxonomy.md` (2026-11-11 이전). `~/.claude/agent-kit/`엔 ai-memory가 배포본을 쓴다 |

- repo: `git@github.com:hslee-cmyk/ai-memory.git` → `~/ai-memory` (env `AI_MEMORY_REPO`로 변경 가능)
- 설치: `python install.py --only ai-memory` (없으면 clone)
- 격상: `/kb-promote` [B] → `ai-memory/memory/` 편집 → `eval_gate.py` PASS → ai-memory commit·push
- 이 repo의 옛 pre-push(kb-global·taxonomy eval 게이트)는 삭제됐다 — 게이트는 ai-memory repo의 pre-push.
