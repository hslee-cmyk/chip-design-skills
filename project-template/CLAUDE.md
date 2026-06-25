<!--
FILL GUIDE — 신규 프로젝트 CLAUDE.md 작성 시, 이 주석 블록 따른 뒤 삭제
[1] {{PROJECT_NAME}}    : 레포 루트 디렉토리명
[2] {{PROJECT_TAGLINE}} : 한 줄 기능 설명 (예: PCM → COLA 프로토콜 변환기)
[3] {{SUBMODULE_DIR}}   : db/design 서브모듈 레포명 (Key Rules 항목에도 동일하게 대체)
[4] PROJECT-SPECIFIC RULES 주석 줄을 프로젝트 고유 실수방지 항목으로 교체
    (항목 없으면 해당 줄 삭제)
-->
# {{PROJECT_NAME}}
{{PROJECT_TAGLINE}} — 상세: `.ai/project.md`

> (`AGENTS.md`·`GEMINI.md`는 이 파일을 가리키는 stub — 작업 지침 정본은 CLAUDE.md + `.ai/`.)

## TOOL-FIRST — 직접 해결 전 필수 체크

> **어떤 작업이든 직접 구현·분석·검색하기 전에 아래 표를 먼저 본다.**
> 도구가 있으면 반드시 그 도구를 쓴다. 도구 없을 때만 직접 해결.

| 작업 | 트리거 | 도구 |
|------|--------|------|
| RTL 착수 전 지식 조회 | `always` 블록 작성 전, 버그 분석 전 | `"$KB_PY" .ai/rag/preflight.py "<주제>"` |
| 모듈 분석서 없음/stale | `.ai/analysis/{module}.analysis.md` 부재 | Agent → `verilog-rtl-analyst` |
| RTL 구조 결정 | 새 FSM/module/instance/clock rewire 판단 | Agent → `verilog-rtl-architect-advisor` |
| RTL 구현 | `always`/FSM/FIFO/레지스터 작성·수정 | Agent → `verilog-rtl-coder` |
| RTL 리뷰 | 머지 전, AI 작성 RTL 검토 | Agent → `verilog-rtl-reviewer` |
| RTL 형식 증명 | deadlock/off-by-one/pointer 경계 | Agent → `verilog-rtl-prover` |
| RTL 코딩 규칙 | 네이밍·리셋·ifdef·Top I/O 불확실 시 | Skill → `verilog-rtl` (세션 첫 RTL 작업 시) |
| iCE40/합성/프로그래밍 | Lattice, nextpnr, .pcf, bitstream | Skill → `lattice-fpga` |
| Formal verification | sby, BMC, SVA, assert, SMT | Skill → `formal-verification` |
| UVM/시뮬레이션 환경 | testbench, sequence, scoreboard | Skill → `uvm-verification` / `chip-verification` |
| 시뮬레이션 디버깅 | 신호 프로빙, 파형, 반례 재현 | MCP → `xcelium-mcp` (cloud0) |
| 솔루션 격상 | 버그 해결 후, sync_rules [A]/[B] 감지 | Skill → `/kb-promote` |
| 그래프·모듈 의존 탐색 | 신호 경로, 모듈 연결, community | MCP → graphify / `/graphify` |
| bkit audit 전문 검색 | details 포함 검색 (MCP는 top-level만) | `"$KB_PY" .ai/rag/audit_search.py "<쿼리>"` |
| PDCA 사이클 | plan·design·do·check·act phase 전환 | bkit `/pdca` |

`KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe`

## Key Rules (자주 틀림)

- 🔒 **RTL 네이밍/코딩은 `verilog-rtl` skill 최우선(MUST)** — `.ai/conventions.md`는 프로젝트 고유 항목만 보강, 충돌 시 skill 우선. RTL 착수 전 skill 먼저 로드.
- **`{{SUBMODULE_DIR}}/` 은 공유 칩 RTL submodule** — formal/lint scratch는 `<project>/formal/`에서 (guard hook 강제), 수정 시 submodule commit.
- **파일 인코딩: UTF-8 (BOM 없음)**
- **원격 tcsh: `2>&1` 금지 → `>&` 사용** (`&1`을 파일명으로 해석)
- **RTL 분석/디버깅**: `verilog-rtl` skill 로드 → `.ai/analysis/{module}.analysis.md` 확인/선작성 → 정적 미특정 시 **xcelium-mcp 즉시 프로빙** (정적 분석만으로 순환 금지)
  - 시작 전 `graphify-out/GRAPH_REPORT.md` 먼저 확인 (전체 모듈 구조·커뮤니티)
  - 특정 신호 경로·의존성 추적은 MCP `graphify query "<질문>"` 사용
- **`.ai/project.md` 작성/갱신 시**: `find <루트> -maxdepth 2 -not -path '*/.git/*'` 먼저 실행 → 실제 디렉토리 구조 확인 후 반영 (context compaction 후 기억에서 쓰면 누락 발생)
- **`TODO.md` 유지관리** (미해결 문제 추적):
  - 새 문제·버그 발생 → 즉시 `TODO.md` 추가 (문제 설명 + 필요 조치)
  - 해결 완료 → 해당 항목 **삭제** (이력 불필요 — 미해결만 유지)
  - 해결 직후 자산화 확인 **필수**: `sync_rules.py --dry-run` → [A]/[B] 있으면 `/kb-promote` 실행

<!-- PROJECT-SPECIFIC RULES — 프로젝트 고유 실수방지 항목만 추가 (디바이스·빌드·서버 등 고유 정보는 .ai/project.md·.ai/ops/ 에) -->

## RTL Agent Routing (Constrain & Escalate)

RTL 작업은 `.claude/agents/`의 subagent로 라우팅 (단일 소스: `chip-design-skills`, `install.py --project <repo>`).
bkit `cto-lead`는 고정 Task() allow-list → **직접 호출** 또는 description-Trigger.

| PDCA / 작업 | Agent | model | 역할 · 경계 |
|---|---|---|---|
| Analyze — 분석서 작성·갱신 (모든 단계 선행물) | `verilog-rtl-analyst` | opus | `.ai/analysis/*.analysis.md` 소유. 부재/stale 시 coder·reviewer·prover → 여기 라우팅. RTL 무수정 |
| Plan·Design 게이트 — 구조 결정 | `verilog-rtl-architect-advisor` | opus | structural-delta 계산 → ARCH면 escalate(ADR+후보). 구현·partitioning 결정 안 함 |
| Do — 비준된 micro-arch 구현 | `verilog-rtl-coder` | sonnet | LOCAL/IFACE만. ARCH면 중단→advisor. 정확성 self-certify 금지 |
| Check — AI-failure signature | `verilog-rtl-reviewer` | opus | STATIC-CONFIRMED 소유 + SIM-RISK 라우팅 (read-only) |
| Check — logic/timing 증명 | `verilog-rtl-prover` | opus | formal(sby) intent property 구현과 독립 작성 |

순서: analyst → advisor → coder → reviewer + prover. partitioning escalation: advisor만 결정.

## 지식 프리플라이트 (RTL/버그 착수 전)

```bash
KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe
"$KB_PY" .ai/rag/preflight.py "<증상/주제>"
```

→ ① `docs/solutions/patterns/critical-patterns.md` 강제 규칙 ② RAG 의미검색(L4) ③ graphify 관계 항법(L3).

**capture→curate→격상→recall 루프**: 해결 후 `docs/solutions/`에 자산화 → `sync_rules.py`(bkit regression-rules 동기) → 일반화 시 `chip-design-skills/kb-global/principles/`(git)에 추가·push → `kb_index.py` 재색인. L1 로그(`.bkit/**`)는 bkit MCP로 질의.

## bkit Integration

| 항목 | 내용 |
|------|------|
| PDCA 템플릿 override | `.ai/bkit-templates/` 파일이 있으면 bkit 기본 대신 사용 (`design`·`do`·`analysis`) |
| RD-PDCA 세분화 | `chip-cto-lead` → `.ai/rd-pdca-substeps.json` fan-out (bkit `/pdca`와 병행, 대체 아님) |
| 병렬 council/swarm | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` 필요 (없으면 prose-fallback) |

## References (필요할 때 읽기)

| 주제 | 문서 |
|------|------|
| 아키텍처·신호 흐름·빌드 요약·디렉토리 | `.ai/project.md` |
| RTL 코딩 규칙 (네이밍·ifdef·Top I/O·합성 속성) | `.ai/conventions.md` |
| 빌드·P&R·프로그래밍 상세 | `.ai/ops/build.md` |
| 원격 서버·ssh-mcp·xcelium-mcp | `.ai/ops/servers.md` |
| hard IP·known issues | `.ai/design-knowledge/` |
| 지식 시스템 정본 경계 | `.ai/KNOWLEDGE_MAP.md` |
| 모듈 분석서 | `.ai/analysis/{module}.analysis.md` |
| 미해결 문제·필요 조치 | `TODO.md` |

## Claude 설정

- **모델**: 분석/디버깅 = **Opus**, 구현·실행·일반 = **Sonnet**. 안 맞으면 `/model`로 변경.
- **Skills**: RTL = `verilog-rtl` · Lattice/iCE40 = `lattice-fpga` · UVM/시뮬 = `uvm-verification`/`chip-verification` · formal = `formal-verification` · 아날로그 = `verilog-a`.
