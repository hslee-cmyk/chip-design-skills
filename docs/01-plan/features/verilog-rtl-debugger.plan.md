# verilog-rtl-debugger Planning Document

> **Summary**: xcelium-mcp MCP tool 접근 권한을 가진 **유일한** RTL agent. 실제 시뮬레이션 실행부터 bisect/CSV 추출/FSM 전이 대조까지 라이브 디버깅 루프를 직접 수행하고, 필요 시 기존 verilog-rtl-* agent(analyst/coder/reviewer/architect-advisor/prover) + 자매 agent `verilog-tb-analyst`(TB 분석서, 신설 예정)를 호출하는 라우터 역할을 겸한다.
>
> **Project**: chip-design-skills
> **Version**: 0.8
> **Author**: HSLEE
> **Date**: 2026-07-07
> **Status**: Draft

---

## ⚠️ 정합성 유지 — 이 문서를 고치기 전에 반드시 읽을 것

이 agent는 **xcelium-mcp repo가 요구사항을 정의하고, chip-design-skills repo가 구현·배포하는** cross-repo 계약이다. 요구사항의 정본은 이 repo가 아니라 **xcelium-mcp**에 있다. 이 문서를 다음 세션에서 이어서 작업(`/pdca design verilog-rtl-debugger` 등)하기 전에, 아래 3개 소스 문서가 이 문서 작성 시점 이후 바뀌지 않았는지 먼저 확인한다.

### 요구사항 정본 (xcelium-mcp repo, 절대경로)

| 문서 | 절대경로 | 참조 섹션 | 확인 시점 버전 |
|------|---------|----------|----------------|
| debugging workflow (핵심 정본) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-debugging-workflow.plan.md` | `## Agent 위임 구조` (Phase 개요 직후), §1D-5(v5.2 dump_scopes — Phase 2~4 루프가 알아야 할 최신 파라미터) | **v2.7** (2026-07-03) |
| tool-usage-guide skill 계획 | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-tool-usage-guide.plan.md` | FR-12, §7 Dependencies "`verilog-rtl-debugger` agent와의 관계" | **v0.8** (2026-07-03) |
| debug-workflow-v2 (`/sim` skill 계획) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-debug-workflow-v2.plan.md` | §4.5 Skill ↔ Backend 도구 매핑, `debug (RTL)` 행 | **v1.9** (2026-07-03) |

> **2026-07-03 갱신**: xcelium-mcp 쪽에서 소스 전수 감사를 거쳐 위 3개 문서 버전이 올라갔다(구 v2.4/v0.4/v1.7 → v2.6/v0.7/v1.9). 위임 매핑표 자체(6개 상황)는 변경 없음 — 감사로 추가된 내용은 (1) 24-tool 카운트 오류 정정(ssh-mcp 헬퍼 이중계산), (2) v5.2 `dump_scopes` 신규 파라미터 문서화, (3) 이 repo가 신경 쓸 필요 없는 CLAUDE.md/v3-improvements 상태 정정. **이 agent의 Phase 2~4 루프(§FR-04)가 Read할 대상인 `references/phase-2~4*.md`를 작성할 때 §1D-5(dump_scopes)를 반드시 반영해야 한다**는 점만 새로 추가됨.
>
> **2026-07-03 추가 갱신 (v2.6→v2.7, 뒤늦게 발견 — §정합성 유지 재확인 시점)**: debugging workflow 문서가 v2.7로 한 단계 더 올라가며 **위임 매핑표에 신규 행이 추가됨**: `.ai/analysis/tb_{env}_*.analysis.md`(TB 공유 컴포넌트·테스트케이스) 부재/stale → `verilog-tb-analyst`(신설 예정, Phase 0A/0B·1A). RTL 쪽(Phase 1B → `verilog-rtl-analyst`)과 대칭을 맞추기 위한 결정이며, `verilog-tb-analyst.plan.md`(이 repo, 별도 PDCA 사이클)에서 상세 설계 진행 중. 아래 위임 매핑표·§3 Requirements에 반영. Agent 미배포 시 fallback(`verilog-rtl-debugger`/Claude 직접 수행)은 RTL 쪽과 동일 원칙 — §6.2 참조.
>
> **2026-07-03 추가 갱신 (v0.7→v0.8, 전수 감사에서 재발견) — §5 Risk 블로킹 조건 이미 해소됨**: tool-usage-guide 문서도 FR-13(`verilog-tb-analyst` 위임 명시) 추가로 v0.8까지 올라갔다. 더 중요한 발견: 그 문서의 완료 Report(`xcelium-mcp-tool-usage-guide.report.md`, **Status: Complete, Match Rate 98%**, 2026-07-03)를 확인한 결과 **FR-04~FR-07이 전부 ✅ Complete**이고, 실측으로도 `~/.claude/skills/xcelium-sim/references/{phase-2-simulation,phase-3-triage,phase-4-waveform,phase-5-fix-regression}.md` **4개 파일이 이미 전부 배포되어 있으며(82/35/110/88줄, 실내용 확인)**, phase-4/5 파일엔 `verilog-rtl-debugger` 위임 지점(§4A/§5A)까지 이미 작성돼 있다. 즉 §5 Risk 표의 "phase-2~4*.md 부재, Likelihood High(현재 확정)" 항목과 §8 Next Steps #2의 선행 확인 절차는 **이미 충족된 과거 리스크**다 — Do 단계 착수 전 별도 대기가 불필요하다(아래 §5·§8 갱신).

### 계약 요약 (2026-07-03 시점, 위 문서에서 발췌)

**왜 신설하는가**: 기존 5개 agent(analyst/architect-advisor/coder/prover/reviewer)는 전부 `tools: Read, Write, Edit, Glob, Grep, Bash`만 가진 정적 분석/코드 작성/formal 전용 agent다. `mcp__xcelium-mcp__*` tool 접근 권한이 없어 실제 시뮬레이션을 실행하고 waveform을 대조하는 **라이브 디버깅**을 아무도 못 한다 — 이게 이 agent가 메우는 공백이다.

**위임 매핑표** (xcelium-mcp-debugging-workflow.plan.md §Agent 위임 구조 원문):

| 상황 | 위임 대상 | 트리거 Phase |
|------|----------|-------------|
| `.ai/analysis/{module}.analysis.md` 부재/stale | `verilog-rtl-analyst` | Phase 1B |
| `.ai/analysis/tb_{env}_*.analysis.md`(공유 컴포넌트/테스트케이스) 부재/stale | `verilog-tb-analyst` (신설 예정, 이 repo 별도 PDCA) | Phase 0A/0B, 1A |
| 근본 원인 확정 후 실제 RTL 수정 코드 작성 | `verilog-rtl-coder` | Phase 5A |
| 수정 커밋 전 AI-failure 패턴 리뷰 | `verilog-rtl-reviewer` | Phase 5A~5B |
| 아키텍처 경계 판단 필요 (신규 FSM/모듈/case-arm) | `verilog-rtl-architect-advisor` | Phase 5A (수정 규모가 클 때) |
| self-contained 로직/타이밍 클레임 형식 증명 | `verilog-rtl-prover` | Phase 5B (필요 시) |
| Verilog-A / AMS 아날로그 컴포넌트 디버깅 | (본 agent가 직접 수행, `verilog-a` skill 참조) | Phase 1D-4/4E (AMS Tier 3) |

**본 agent가 직접 소유(위임하지 않음)**: xcelium-mcp-debugging-workflow.plan.md Phase 2(시뮬레이션 실행)~Phase 4(bisect_signal/simvisdbutil CSV 추출/FSM 전이 대조, Phase 4E "AI 자율 디버깅 + Human-in-the-Loop" 루프 전체).

**방법론 출처(중요 — 2026-07-03 결정, 중복 금지)**: 이 Phase 2~4 방법론을 agent의 system prompt에 **복사해 내장하지 않는다.** xcelium-mcp의 `~/.claude/skills/xcelium-sim/`(user-level, tool-usage-guide/debug-workflow-v2가 생성) `references/phase-2~4*.md`가 **유일한 정본**이고, 이 agent는 **런타임에 그 파일을 Read**해서 따른다. 이유: 같은 방법론이 skill 쪽 reference와 agent system prompt 양쪽에 독립적으로 존재하면 한쪽만 갱신될 때 drift가 발생하기 때문. 두 산출물 모두 user-level(`~/.claude/skills/`, `~/.claude/agents/`)이라 프로젝트 무관하게 고정 경로로 Read 가능 — 이 방식이 성립하는 전제조건이다.

**소비 측 배포 상태 및 fallback 영속성 원칙(2026-07-03 수정 — 최초 문구 오류 정정)**: xcelium-mcp 쪽 skill(`~/.claude/skills/xcelium-sim/`, Phase 1은 tool-usage-guide, Phase 2는 debug-workflow-v2)은 이 agent가 **아직 없어도** 동작하도록 "agent 없으면 Claude가 직접 수행" fallback 문구를 넣기로 되어 있다(FR-12). 이 문단은 원래 "agent 완성 시 fallback 문구를 agent 호출로 교체"라고 썼으나, 이는 **`verilog-tb-analyst.plan.md` §1.2 "agent와 skill의 관계 원칙"과 xcelium-mcp 정본(v2.7, TB 위임 절 "Agent가 아직 배포되지 않은 동안은... fallback을 유지한다")** 양쪽과 모순된다 — skill은 agent 설치 여부와 무관하게 항상 단독 동작해야 하므로, fallback은 "agent 완성 전 임시 대체"가 아니라 **agent 미설치/미사용 환경을 위한 영구 경로**다. 올바른 전환 방향: agent 완성 후에는 **"agent 호출을 우선 경로로 추가"**하되, fallback 문구 자체는 삭제·교체하지 않고 그대로 둔다 — xcelium-mcp-tool-usage-guide.plan.md §8 Next Steps 7번 항목도 이 방향으로 재작성 요청 필요(§8 Next Steps 6번 참조).

### 갱신 규칙

- 이 문서(chip-design-skills 쪽)를 Design/Do로 진전시키다가 agent의 이름·tool 목록·위임 대상이 위 계약과 달라지면, **xcelium-mcp 쪽 3개 문서도 같이 갱신**해야 한다(Version History에 상호 참조 기록).
- 반대로 xcelium-mcp 쪽에서 위임 매핑표가 바뀌면, 이 문서의 위 "계약 요약" 절과 §3 Requirements를 다시 대조한다.
- 두 repo 사이에 자동 동기화는 없다 — 수동 대조가 유일한 안전장치다.

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | xcelium-mcp의 6-phase 디버깅 워크플로우에서 Phase 2~4(시뮬레이션 실행, bisect/CSV 추출, FSM 전이 대조)를 수행할 agent가 없다. 기존 5개 verilog-rtl-* agent는 전부 MCP tool 접근이 없는 정적 분석/코드 작성 전용이라, 이 라이브 디버깅 루프는 매번 Claude가 처음부터 판단해야 한다. |
| **Solution** | `mcp__xcelium-mcp__*` tool 접근 권한을 가진 신규 agent `verilog-rtl-debugger`를 만들어, Phase 2~4를 직접 소유하고 Phase 0/1/5의 다른 작업은 기존 4개 agent(analyst/coder/reviewer/architect-advisor) + 필요 시 prover + 자매 agent `verilog-tb-analyst`(TB 분석서, Phase 0A/0B/1A)에게 위임하는 라우터로 동작시킨다. |
| **Function/UX Effect** | RTL 디버깅 요청 시 이 agent가 bisect→CSV→FSM 대조 루프를 자율 수행하고, 분석서 갱신이나 수정 코드 작성처럼 자기 스코프 밖의 일은 자동으로 적절한 agent에 위임 — 매번 수동으로 5개 agent 중 뭘 부를지 판단할 필요가 없어짐. |
| **Core Value** | xcelium-mcp를 쓰는 모든 RTL 프로젝트(venezia-fpga 등)에서 디버깅 결과물의 완성도가 기존 5개 agent의 검증된 품질 기준(analysis 완전성, AI-failure 리뷰, formal 증명)을 그대로 상속받음. |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | xcelium-mcp 디버깅 워크플로우 Phase 2~4를 수행할 MCP-tool-aware agent가 없음 (§정합성 유지 계약 요약 참조) |
| **WHO** | xcelium-mcp를 사용해 RTL을 디버깅하는 모든 프로젝트의 AI 에이전트 (1차 소비자: venezia-fpga) |
| **RISK** | xcelium-mcp 쪽 요구사항(위임 매핑표)과 이 repo의 구현이 별도 PDCA 사이클로 진행되어 drift 가능 — 수동 대조 외 안전장치 없음 |
| **SUCCESS** | 위임 매핑표의 **7개**(v2.7, TB 행 포함) 상황 전부를 올바른 agent에 위임; Phase 2~4는 다른 agent 호출 없이 직접 수행 |
| **SCOPE** | agent 정의 파일(`agents/verilog-rtl-debugger.md`) 작성 + `install.py` 배포 등록만. xcelium-mcp MCP tool 구현이나 워크플로우 로직 자체는 xcelium-mcp repo 소관(Out of Scope) |

---

## 1. Overview

### 1.1 Purpose

xcelium-mcp의 라이브 시뮬레이션 디버깅(시뮬레이션 실행 → bisect/CSV 추출 → FSM 전이 대조)을 자율 수행하면서, 분석서 작성·RTL 수정·리뷰·formal 증명·아키텍처 판단처럼 기존 agent가 이미 잘하는 일은 위임하는 라우터형 agent를 만든다.

### 1.2 Background

기존 5개 verilog-rtl-* agent(analyst/architect-advisor/coder/prover/reviewer)는 `tools: Read, Write, Edit, Glob, Grep, Bash`만 갖고 있어 MCP tool(`mcp__xcelium-mcp__*`)에 접근할 수 없다. 반면 xcelium-mcp-debugging-workflow.plan.md의 Phase 2~4는 전적으로 이 MCP tool(`sim_batch_run`, `bisect_signal`, `inspect_signal`, `checkpoint` 등)로 이루어진다. 이 간극이 사용자가 실제로 xcelium-mcp를 쓸 때마다 반복 발견됐다.

### 1.3 Related Documents

- **요구사항 정본**: §정합성 유지 절의 xcelium-mcp 3개 문서 (WITHIN THIS repo가 아니라 외부 repo — 반드시 원본 확인)
- **자매(sibling) PDCA 사이클(동일 repo)**: `docs/01-plan/features/verilog-tb-analyst.plan.md` — FR-09가 위임하는 대상. 이 문서의 위임 매핑표(TB 행)와 그쪽 §정합성 유지 표가 서로 상호 참조하므로, 한쪽을 고치면 반드시 다른 쪽도 대조
- 기존 agent 컨벤션 참조: `agents/verilog-rtl-analyst.md`, `agents/verilog-rtl-reviewer.md` 등 5개 (frontmatter 스타일: `name`/`description`(Use it when / Do NOT use for / Triggers 구조)/`tools`/`model`)
- 도구·참조 문서: `agent-kit/failure-taxonomy.md`, `agent-kit/methodology.md`, `agent-kit/evidence.md`
- bkit customization 컨벤션: `docs/04-bkit-customization-guide.md`, `bkit/README.md` §1 agents (copy-rename 방식 — 단, 이 agent는 bkit agent의 copy-rename이 아니라 순수 신규 agent이므로 `bkit/agents/`가 아니라 top-level `agents/`에 위치)

---

## 2. Scope

### 2.1 In Scope

- [ ] `agents/verilog-rtl-debugger.md` 신규 작성 (기존 5개 agent와 동일한 frontmatter 컨벤션)
- [ ] Tool 목록 확정: 기존 5개에 없는 MCP tool 접근권 추가(§3 FR-02) + 다른 agent를 호출하기 위한 `Task(...)` 권한
- [ ] 위임 매핑표(§정합성 유지)를 agent 본문(system prompt)에 그대로 반영
- [ ] `install.py`의 agent 배포 목록에 등록 (기존 5개와 동일 경로로 `~/.claude/agents/`에 배포)
- [ ] Trigger 문구 작성 — 기존 5개 agent와 트리거 중복 최소화(특히 verilog-rtl-analyst와 Phase 1B 경계, verilog-rtl-coder/reviewer와 Phase 5A 경계)

### 2.2 Out of Scope

- xcelium-mcp MCP tool 자체의 구현/수정 — xcelium-mcp repo 소관
- xcelium-mcp-debugging-workflow.plan.md의 6-phase 워크플로우 로직 자체 변경 — xcelium-mcp repo 소관, 이 agent는 그 워크플로우를 **수행**할 뿐 **정의**하지 않음
- `~/.claude/skills/xcelium-sim/`(tool-usage-guide/debug-workflow-v2) skill 파일 자체 작성 — xcelium-mcp repo 소관, 독립 배포(그 repo의 FR-10)
- AMS/Verilog-A 세부 방법론 — 기존 `verilog-a` skill이 이미 커버, 이 agent는 그 skill을 참조만 함

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `agents/verilog-rtl-debugger.md` frontmatter — `name`, `description`(Use it when / Do NOT use for / Triggers 구조로 기존 5개와 통일), `tools`, `model` | High | Pending |
| FR-02 | Tool 목록: `mcp__xcelium-mcp__*` 전체(24개 tool) + `Read, Glob, Grep`(RTL/분석서 참조) + `Task`(다른 agent 위임 호출) — Write/Edit는 원칙적으로 불필요(RTL 수정은 verilog-rtl-coder에 위임) | High | Pending |
| FR-03 | System prompt에 §정합성 유지의 위임 매핑표(**7개** 상황, v2.7 TB 행 반영)를 명시적 라우팅 규칙으로 포함 | High | Pending |
| FR-04 | Phase 2~4 자율 루프(bisect→CSV→in-memory 분석→FSM 대조→가설 검증) 수행 로직 — **agent 자체에 내장하지 않고, 런타임에 `~/.claude/skills/xcelium-sim/references/phase-2~4*.md`를 Read하여 따름**(§정합성 유지 "방법론 출처" 참조). system prompt에는 "이 경로들을 먼저 Read하라"는 지시만 포함 | High | Pending |
| FR-05 | `.ai/analysis/{module}.analysis.md` 부재/stale 감지 시 `verilog-rtl-analyst` 호출 (분석서 없이 FSM 대조로 넘어가지 않음 — 기존 analyst의 "분석서 부재 BLOCKER" 패턴과 동일 원칙) | High | Pending |
| FR-09 | `.ai/analysis/tb_{env}_*.analysis.md` 부재/stale 감지 시 `verilog-tb-analyst` 호출(Phase 0A/0B/1A) — FR-05와 동일 원칙(RTL/TB 대칭). **`verilog-tb-analyst`가 아직 배포되지 않은 동안은 이 agent(`verilog-rtl-debugger`) 자신이 xcelium-sim skill의 §0A/0B 절차를 phase-0-discovery.md를 Read해 직접 수행**하는 fallback을 겸함(xcelium-mcp-debugging-workflow.plan.md v2.7 "TB 분석서 위임" 절 원칙과 동일) | High | Pending |
| FR-06 | 근본 원인 확정 후 `verilog-rtl-coder`에 수정 위임, 커밋 전 `verilog-rtl-reviewer`로 라우팅 | High | Pending |
| FR-07 | Trigger 키워드 — 기존 5개와 중복 최소화, "시뮬레이션 디버깅", "waveform 분석", "bisect", "FSM 대조" 등 라이브-디버깅 특화 키워드로 한정 | Medium | Pending |
| FR-08 | `install.py` AGENTS 목록에 등록, 기존 배포 경로(`~/.claude/agents/`)와 동일하게 배포 | Medium | Pending |
| FR-10 | "0. 기준 — 시작 시 반드시 로드" 목록에 `phase-0-discovery.md`(§0C, `tb_source`/`tb_provenance.combined_sha256` 비교 기반 분석서 staleness 체크)를 **phase-2보다 먼저 읽는 MUST 항목**으로 추가. 기존 `.ai/analysis/**` 문서 내용을 Phase 2~4 추론의 근거로 삼기 **전에** 이 hash 비교를 먼저 수행하도록 §2 위임 매핑표의 "부재/stale" 정의를 명문화(불일치뿐 아니라 문서에 hash 기록 자체가 없는 경우도 stale로 간주 — §0C 원문). Manifest(오케스트레이터 반환) 항목에도 "분석서 staleness 체크 수행 여부/결과"를 필수 보고 필드로 추가. **§2 위임 매핑표 #2(`verilog-tb-analyst`) Task() 패턴에 6번째 파라미터 `tb_provenance`(이번 실행의 `sim_batch_run`/`sim_regression`/`sim_bridge_run` 반환값에서 그대로 전달) 추가** — hash를 낼 수 있는 건 이 agent뿐이고 그걸 헤더에 기록하는 건 `verilog-tb-analyst`이므로, 넘겨주지 않으면 그쪽이 받을 자리가 있어도(FR-14) 쓸 값이 없음. `verilog-tb-analyst.plan.md` FR-14와 동시 반영 필수 | High | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|---------------------|
| Cross-repo Consistency | 위임 매핑표가 xcelium-mcp-debugging-workflow.plan.md §Agent 위임 구조와 100% 일치 | 두 문서 diff 리뷰 (§정합성 유지) |
| Trigger 비충돌 | 기존 5개 agent 및 다른 project skill과 트리거 키워드 충돌 없음 | 전체 agent description 스캔 |
| Tool 최소 권한 | 실제로 필요한 tool만 부여(예: Write/Edit 미부여 — 수정은 coder 위임) | frontmatter 리뷰 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `agents/verilog-rtl-debugger.md` 작성 완료, 기존 5개 agent와 동일한 품질 기준(model 선택 근거, "왜 별도 agent인가" 절 등) 충족
- [ ] `install.py` 배포 등록 + 실제 배포 테스트(`~/.claude/agents/verilog-rtl-debugger.md` 생성 확인)
- [ ] xcelium-mcp 쪽 3개 문서의 위임 매핑표와 최종 대조 완료, 불일치 없음
- [ ] venezia-fpga 세션에서 실제 디버깅 시나리오로 수동 검증 (analyst/coder/reviewer 위임이 실제로 동작하는지)

### 4.2 Quality Criteria

- [ ] `agent-kit/failure-taxonomy.md` 참조 여부 검토(리뷰 위임 시 이 taxonomy를 중복 적용하지 않도록 경계 명확화)
- [ ] 다른 4개 agent의 툴/스코프와 겹치는 부분 없음(코드 리뷰로 확인)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| xcelium-mcp 쪽 요구사항이 이 문서 작성 이후 바뀌었는데 모르고 진행 | High | Medium | Design 착수 전 §정합성 유지의 3개 문서를 다시 Read하여 버전 비교 |
| Trigger가 기존 5개 agent와 겹쳐 오라우팅 | Medium | Medium | FR-07, 라이브-디버깅 특화 키워드로 한정 |
| MCP tool 24개 전체 부여로 tool 목록이 비대해짐 | Low | Low | 실제 필요한 tool만(§3.1 FR-02) — Signal/Waveform/Debug/Checkpoint 계열 위주, 미사용 그룹 있으면 Design 단계에서 축소 검토 |
| 위임 대상 agent(analyst/coder/reviewer)가 이 agent로부터 Task() 호출을 받는 상황이 기존 컨벤션(사람이 직접 호출)과 달라 예상 밖 동작 | Medium | Medium | Design 단계에서 Task() 호출 패턴을 기존 chip-cto-lead(bkit orchestrator) 사례와 대조 |
| ~~`~/.claude/skills/xcelium-sim/references/phase-2~4*.md`가 아직 없음~~ — **해소됨(2026-07-03 재확인)**: 4개 파일(`phase-2-simulation`/`phase-3-triage`/`phase-4-waveform`/`phase-5-fix-regression.md`) 실측 확인, `xcelium-mcp-tool-usage-guide.report.md`(Match Rate 98%)에 FR-04~07 전부 ✅ Complete로 기록됨. phase-4/5엔 이 agent 위임 지점까지 선반영됨 | ~~High~~ 해소 | ~~High~~ 없음 | 해소되었으므로 §8 Next Steps #2의 "선행 확인" 절차는 스킵 가능. 단, 이 문서를 계속 Design/Do로 진전시키기 전 §정합성 유지 절대로 재확인 원칙(수동 대조)은 유지 — 파일 존재만 확인했을 뿐 내용의 최신성까지 보증하지는 않음 |
| 이미 배포된 `agents/verilog-rtl-debugger.md`의 "0. 기준"이 phase-2~5만 MUST로 명시하고 phase-0-discovery.md(§0C staleness 체크)를 누락 — agent가 실행 시 기존 분석서를 hash 검증 없이 그대로 신뢰하고 Phase 2로 직행하는 실패 모드 실측 확인(2026-07-06, venezia-fpga T-002 COV-GAP 재검증 세션: `sim_batch_run`이 반환한 hash를 분석서 헤더의 기록과 비교하지 않고 넘어감) | High | 확인됨(재발 가능) | FR-10으로 등록 — Do 재진입 시 "0. 기준"에 phase-0-discovery.md MUST 추가 + §2 공통규칙에 stale 정의(hash 불일치/미기록) 명문화 + Manifest 보고 필드 추가 |

---

## 6. Impact Analysis

### 6.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|---------------------|
| `agents/verilog-rtl-debugger.md` | 신규 파일 | 신규 agent 정의 |
| `install.py` | 스크립트 | AGENTS 목록에 신규 agent 추가 |
| `~/.claude/agents/verilog-rtl-debugger.md` | 배포 산출물 | install.py 실행 시 신규 생성 |

### 6.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| (신규 agent라 현재 소비자 없음) | — | — | — |
| **외부 계약(예정)**: xcelium-mcp `~/.claude/skills/xcelium-sim/` skill | INVOKE (완성 후 우선 경로) | xcelium-mcp-tool-usage-guide/debug-workflow-v2의 phase reference에서 이 agent를 호출하도록 작성 예정 | Needs verification — agent 완성 후에도 fallback("verilog-rtl-debugger 없으면 Claude가 직접 phase-2~4 reference를 Read해 수행")은 **영구 유지**. agent는 fallback을 대체하는 게 아니라 그 위의 우선 경로(§정합성 유지 "소비 측 배포 상태 및 fallback 영속성 원칙" 참조) |

### 6.3 Verification

- [ ] 신규 agent가 기존 5개 agent의 Task() 호출 인터페이스와 호환되는지 확인
- [ ] `install.py --only agents` (또는 해당 옵션) 실행 후 배포 경로 확인

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `agents/*.md` frontmatter 컨벤션 존재 (기존 5개 agent가 정본 — `name`/`description`/`tools`/`model`)
- [x] `agent-kit/failure-taxonomy.md` 등 공유 참조 문서 존재
- [x] `install.py` agent 배포 스크립트 존재

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| MCP tool 권한 부여 방식 | **해소(Design §2.0)** — Option C(24개 전량 부여 + 문서화된 사용 규율) 채택. Option B(최소 부여)는 Phase 0 setup을 호출자가 이미 처리했다는 가정이 항상 성립하지 않아 기각 | 완료 | High |
| Agent 간 Task() 위임 패턴 | **해소(Design §2.2/§4)** — 6개 위임 대상(analyst/coder/reviewer/architect-advisor/prover/tb-analyst) 전부 확정. prompt에 대상 파일·근본원인·분석서 경로 명시하는 공통 규칙(§4.2) | 완료 | Medium |
| `verilog-tb-analyst`와의 Task() 위임 인터페이스 | **해소** — `verilog-tb-analyst.design.md` §4.1의 5개 파라미터(env/target_type/target_name/target_paths/reason) 계약을 이 agent Design에서 그대로 재사용(§4.1). 양쪽 Design 문서가 동일 계약을 인용해 불일치 없음 | 완료 | Medium |

---

## 8. Next Steps

1. [ ] 착수 전 §정합성 유지의 xcelium-mcp 3개 문서를 다시 Read — 버전이 위 표와 다르면 계약 요약부터 갱신
2. [x] ~~선행 확인: `~/.claude/skills/xcelium-sim/references/phase-2~4*.md` 배포 여부~~ — **완료 확인(2026-07-03)**: 4개 파일 모두 실측 존재 + `xcelium-mcp-tool-usage-guide.report.md`(Match Rate 98%)에 FR-04~07 Complete 기록. Do 단계 착수 전 별도 대기 불필요(§5 Risk 표 갱신 참조)
3. [x] `/pdca design verilog-rtl-debugger` — **완료**(`verilog-rtl-debugger.design.md` v0.1): Tool 목록 Option C(전량+사용규율) 확정, 6개 agent Task() 위임 패턴 확정, "0. 기준"(phase-2~5 reference) 구조 확정
4. [ ] `agents/verilog-rtl-debugger.md` 작성
5. [ ] `install.py` 등록 + 배포 테스트
6. [ ] xcelium-mcp 쪽 문구를 "fallback만 존재"에서 "agent 호출을 우선 경로로 추가하되 fallback(Claude 직접 수행)은 영구 유지"로 갱신 요청 (xcelium-mcp-tool-usage-guide.plan.md §8 Next Steps 7번과 연동) — fallback 제거가 아님에 주의, `verilog-tb-analyst.plan.md` §8 Next Steps 6번과 동일 원칙
7. [ ] **FR-10 (Do 재진입, `verilog-tb-analyst.plan.md` FR-14와 동시 진행)** — 이미 배포된 `agents/verilog-rtl-debugger.md`(chip-design-skills 정본) + `~/.claude/agents/verilog-rtl-debugger.md`(배포본) 양쪽에 다음을 반영: (a) "0. 기준"에 `phase-0-discovery.md`를 phase-2보다 먼저 읽는 MUST 항목으로 추가, (b) §2 위임 매핑표 공통 규칙에 "분석서 존재 ≠ fresh — `tb_source.combined_sha256` 불일치 또는 미기록 시 stale로 간주하고 FR-05/FR-09(analyst/tb-analyst) 위임을 트리거"를 명문화, (c) §2 위임 매핑표 #2 Task() 패턴에 `tb_provenance` 파라미터 추가(FR-10 본문 참조), (d) Manifest 섹션에 "분석서 staleness 체크 수행 여부/결과" 보고 필드 추가. 반영 후 `install.py` 재배포 확인 — `verilog-tb-analyst` 쪽 FR-14(6번째 파라미터 수신·헤더 기록) 없이 (c)만 반영하면 보내는 값을 받는 쪽이 버림

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-03 | 초안 — xcelium-mcp repo에서 확정된 Agent 위임 구조(xcelium-mcp-debugging-workflow.plan.md v2.4, xcelium-mcp-tool-usage-guide.plan.md v0.4 FR-12, xcelium-mcp-debug-workflow-v2.plan.md v1.7 §4.5)를 이 repo로 가져와 Plan 문서화. cross-repo 정합성 유지를 위한 전용 절 신설 | HSLEE |
| 0.2 | 2026-07-03 | **방법론 중복 문제 해결**: Phase 2~4 방법론을 agent system prompt에 내장(FR-04 원안)하지 않고, **런타임에 `~/.claude/skills/xcelium-sim/references/phase-2~4*.md`를 Read**하도록 결정 — skill과 agent 양쪽에 같은 내용이 독립적으로 존재해 drift되는 것을 방지. FR-04 갱신, 신규 Risk(skill reference 부재 시 동작 불가) 추가, §8 Next Steps에 "skill 먼저 존재해야 함" 선행 조건 삽입 | HSLEE |
| 0.3 | 2026-07-03 | **xcelium-mcp 소스 감사 반영** — xcelium-mcp 쪽 3개 요구사항 정본 문서가 소스 전수 감사를 거쳐 버전 상승(v2.4/v0.4/v1.7 → v2.6/v0.7/v1.9). 위임 매핑표 자체는 불변, §정합성 유지 표의 버전 참조만 갱신 + v5.2 `dump_scopes` 반영 필요성 명시 | HSLEE |
| 0.4 | 2026-07-03 | **위임 매핑표 TB 행 누락 발견·반영** — `verilog-tb-analyst.plan.md`(자매 문서) §6.2가 이미 "§Agent 위임 구조 TB 행"을 참조하고 있었는데 정작 이 문서엔 그 행이 없던 불일치를 발견. xcelium-mcp 정본을 재확인한 결과 debugging-workflow.plan.md가 v2.6→**v2.7**로 이미 개정되어 TB 위임 행이 추가돼 있었음(우리 쪽이 재동기화를 놓친 것). 위임 매핑표에 TB 행 추가, FR-09 신설(verilog-tb-analyst 호출 + agent 미배포 시 이 agent 자신이 fallback 수행), FR-03을 "6개→7개 상황"으로 갱신, §1.3에 자매 PDCA 문서 상호 참조 추가, §정합성 유지 버전을 v2.7로 갱신 | HSLEE |
| 0.5 | 2026-07-03 | **fallback 영속성 원칙 재정정** — "계약 요약 > 소비 측 배포 상태" 문단이 "agent 완성 시 fallback 문구를 agent 호출로 교체"라고 쓰여 있던 것을 발견, 이는 같은 세션에서 `verilog-tb-analyst.plan.md` §1.2에 확립한 "fallback은 agent 미설치 환경을 위해 영구 유지" 원칙 및 xcelium-mcp 정본 v2.7 자체의 문구("Agent가 아직 배포되지 않은 동안은... fallback을 유지한다")와도 모순되는 이 문서 최초 작성 시점의 오류였음. 해당 문단 정정 + §6.2 Current Consumers 행 + §8 Next Steps 6번을 "agent=우선 경로 추가, fallback=영구 유지"로 일괄 수정 | HSLEE |
| 0.6 | 2026-07-03 | **두 자매 plan 문서 전수 정합성 감사 반영** — (1) tool-usage-guide 버전 인용 v0.7→**v0.8**로 정정(실제 최신, `verilog-tb-analyst.plan.md`는 이미 정확했음). (2) **§5 Risk "phase-2~4*.md 부재, Likelihood High" 및 §8 Next Steps #2 선행확인을 "해소됨"으로 정정** — 실측 결과 4개 reference 파일 전부 이미 배포돼 있고 `xcelium-mcp-tool-usage-guide.report.md`(Match Rate 98%)에 FR-04~07 Complete 기록 확인, Do 단계 블로킹 조건 아님. (3) Context Anchor SUCCESS "6개→7개" 상황 수 정정(FR-03과 불일치했던 것). (4) 최상단 Summary·Executive Summary Solution 행에 `verilog-tb-analyst` 위임(FR-09) 반영 — v0.4/v0.5 편집 때 누락됐던 부분. (5) §7.2에 `verilog-tb-analyst`와의 Task() 인터페이스 대칭 행 추가. (6) 헤더 `Version: -` → `0.5`(현재는 0.6)로 Version History와 동기화 | HSLEE |
| 0.7 | 2026-07-06 | **Design 완료** — `verilog-rtl-debugger.design.md` v0.1 작성. §7.2의 3개 미정 항목(MCP tool 부여 방식, Task() 위임 패턴, tb-analyst 인터페이스) 전부 해소로 갱신, §8 Next Steps #3 완료 표시. Tool 부여는 Option C(24개 전량+문서화된 사용 규율), tb-analyst 위임은 그쪽 Design v0.4 계약을 그대로 재사용 | HSLEE |
| 0.8 | 2026-07-07 | **FR-10 신설 — staleness 체크 누락 실패 모드 발견·반영**. venezia-fpga에서 이미 배포된 `agents/verilog-rtl-debugger.md`를 실제로 실행(T-002 COV-GAP 재검증)한 세션에서, "0. 기준"이 phase-2~5만 MUST로 명시하고 phase-0-discovery.md(§0C `tb_source.combined_sha256` staleness 체크)를 누락하고 있어 agent가 기존 분석서를 hash 검증 없이 그대로 신뢰한 채 Phase 2로 직행하는 실패 모드를 실측 확인. FR-10 추가(§3.1), §5 Risk 표에 해당 행 추가, §8 Next Steps #7(Do 재진입 — 이미 배포된 agent 정본+배포본 양쪽 갱신) 추가. **추가 발견(같은 세션, 자매 문서 검토 중)**: hash를 낼 수 있는 이 agent와 그걸 헤더에 기록해야 하는 `verilog-tb-analyst`가 서로 다른데 Task() 위임 인터페이스에 hash 전달 자리가 없어 FR-10만으론 완결되지 않음을 확인 — FR-10 본문에 `tb_provenance` 파라미터 추가 요구 반영, `verilog-tb-analyst.plan.md` FR-14와 쌍으로 등록. 이 버전은 Plan 등록만 하고 실제 agent 파일 수정은 별도 Do 사이클에서 진행 | HSLEE |
