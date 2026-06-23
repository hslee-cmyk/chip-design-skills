# {{PROJECT_NAME}}

{{PROJECT_TAGLINE}}  <!-- 한 줄 설명 -->

> 간결한 진입점이다. 상세는 `.ai/` 문서를 참조하고, 여기엔 *자주 틀리는 규칙·라우팅*만 둔다.
> (`AGENTS.md`·`GEMINI.md`는 이 파일을 가리키는 stub — 작업 지침 정본은 CLAUDE.md + `.ai/`.)

## 레퍼런스 (필요할 때 읽기)
| 주제 | 문서 |
|------|------|
| 아키텍처·신호 흐름·디렉토리 | `.ai/project.md` |
| 코딩 규칙(네이밍·ifdef·Top I/O·인코딩·합성 속성) | `.ai/conventions.md` |
| 빌드·클럭·프로그래밍 | `.ai/build.md` |
| 원격 서버·ssh-mcp·xcelium-mcp | `.ai/servers.md`, `.ai/knowledge/` |
| 하드 IP·known issues | `.ai/knowledge/` |
| RTL 모듈 분석서 | `.ai/analysis/` (`{module}.analysis.md`) |

## Key Rules (자주 틀림)
- 🔒 **RTL 네이밍/코딩은 `verilog-rtl` skill 최우선(MUST)** — `.ai/conventions.md`는 프로젝트 고유 항목만 보강, 충돌 시 skill 우선. RTL 작업 전 skill 먼저 로드.
- 신호 네이밍: camelCase + `i_`/`o_`/`w_`/`r_`/`c_` 접두사 (정본=verilog-rtl skill) — `.ai/conventions.md`
- 파일 인코딩: **UTF-8 (BOM 없음)**
- `{{SUBMODULE_DIR}}/`은 공유 칩 RTL submodule — formal/lint scratch는 `<project>/formal/`에서(guard hook 강제), 수정 시 submodule commit.
- ⚠️ 원격 tcsh에서 `2>&1` 금지 → `>&` 사용.

## RTL 분석/디버깅
1. **로컬에서** `verilog-rtl` skill 로드 후 진행.
2. 대상·연계 모듈마다 `.ai/analysis/{module}.analysis.md` 확인/작성 — 없으면 **먼저 작성**. 수정 후 갱신.
3. 정적 분석으로 원인 미특정 → **즉시 xcelium-mcp 프로빙**(`.ai/servers.md`).
> 시작 전 `graphify-out/GRAPH_REPORT.md` 먼저 확인(있으면).

## RTL Agent Routing (Constrain & Escalate)
RTL 작업은 `.claude/agents/` 또는 `~/.claude/agents/`의 subagent로 라우팅 (단일 소스: `chip-design-skills`).
bkit `cto-lead`는 고정 Task() allow-list라 자동 위임 못 함 → **직접 호출** 또는 트리거.

| PDCA | Agent | 역할 |
|------|-------|------|
| Analyze (모든 단계 선행) | `verilog-rtl-analyst` | `.ai/analysis/*.analysis.md` 소유(skill §12 + graphify 골격). 부재/stale 시 여기로 라우팅. RTL 무수정 |
| Plan·Design 게이트 (구조 결정) | `verilog-rtl-architect-advisor` | structural-delta 계산 → ARCH면 escalate(ADR) |
| Do (비준된 micro-arch 구현) | `verilog-rtl-coder` | LOCAL/IFACE만, 정확성 self-certify 금지 |
| Check (AI-failure signature) | `verilog-rtl-reviewer` | STATIC-CONFIRMED 소유 + SIM-RISK 라우팅 |
| Check (logic/timing 증명) | `verilog-rtl-prover` | formal(sby) intent property 독립 작성 |

## 지식 프리플라이트 (RTL/버그 작업 착수 전)
공유 venv로 장기(전역 RAG)+단기(graphify) 지식을 조회한 뒤 PLAN-BEFORE-CODE:
```bash
KB_PY=/c/Users/HSLEE/Documents/Todoc/fpga/.tools/kb-venv/Scripts/python.exe
"$KB_PY" .ai/rag/preflight.py "<증상/주제>"
```
- 해결 확인 후 `docs/solutions/`에 자산화 → `"$KB_PY" docs/solutions/sync_rules.py`(bkit regression-rules 동기).
- **일반화**되면 정본 `chip-design-skills/kb-global/principles/`(git)에 추가·push → `kb_index` 재색인(전 프로젝트 공유). 런타임 `fpga/.tools/kb-global`엔 쓰지 말 것(인덱스 전용·비버전관리).
- 4계층/2-tier 모델·정본 경계: `chip-design-skills/kb-global/README.md`.

## RD-PDCA Team Overlay (선택 — 단계 세분화)
bkit `/pdca` 9-phase를 그대로 쓰되 Design/Do/Check를 sub-step council/swarm으로 세분화하려면:
`chip-cto-lead`(병행 lead)가 `.ai/rd-pdca-substeps.json`을 읽어 fan-out. 생성: `install.py --gen-rd-pdca --project <repo>`.
진짜 병렬은 `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. 상세: chip-design-skills `docs/04` §10.

## bkit 템플릿 override (PDCA 문서 생성 시)
아래 템플릿이 **존재하면** bkit 기본(`${CLAUDE_PLUGIN_ROOT}/templates/...`) 대신 사용. 없으면 bkit 기본.
| 문서 | override 템플릿 |
|------|----------------|
| Design | `.ai/bkit-templates/design.template.md` |
| Do | `.ai/bkit-templates/do.template.md` |
| Analysis(Check) | `.ai/bkit-templates/analysis.template.md` |

## Claude-Specific
- 모델: 분석/디버깅 = **Opus**, 구현·일반 = **Sonnet**.
- Skills: RTL=`verilog-rtl` · Lattice/iCE40=`lattice-fpga` · UVM/시뮬=`uvm-verification`/`chip-verification` · formal=`formal-verification` · 아날로그=`verilog-a`.
