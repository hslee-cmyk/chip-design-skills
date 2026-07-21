# verilog-tb-analyst Planning Document

> **Summary**: TB(테스트벤치) 공유 컴포넌트·테스트케이스 분석서(`.ai/analysis/tb_{env}_*.analysis.md`) 작성/갱신을 전담하는 신규 agent. `verilog-rtl-analyst`(RTL 분석서, Phase 1B)와 정확히 대칭되는 역할을 TB 쪽(Phase 0A/0B, 1A)에 만든다 — xcelium-sim skill이 "tool 사용법 전용"이면서 TB 분석 방법론 전체를 위임 없이 직접 안고 있던 비대칭 해소.
>
> **Project**: chip-design-skills
> **Version**: 0.10
> **Author**: HSLEE
> **Date**: 2026-07-08
> **Status**: Draft

---

## ⚠️ 정합성 유지 — 이 문서를 고치기 전에 반드시 읽을 것

`verilog-rtl-debugger.plan.md`와 동일한 cross-repo 계약 구조다. 요구사항 정본은 이 repo가 아니라 **xcelium-mcp**에 있다.

### 요구사항 정본 (xcelium-mcp repo, 절대경로)

| 문서 | 절대경로 | 참조 섹션 | 확인 시점 버전 |
|------|---------|----------|----------------|
| debugging workflow (TB 분석 규칙 원본) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-debugging-workflow.plan.md` | `## Agent 위임 구조`의 TB 행, `## Phase 0` 전체(0A/0B/0C) | v2.7 (2026-07-03) |
| tool-usage-guide (skill Phase 1 계획) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-tool-usage-guide.plan.md` | FR-13, §7 Dependencies "`verilog-tb-analyst` agent와의 관계" | v0.8 (2026-07-03) |
| **실제 방법론(agent가 런타임에 Read할 대상, 최우선)** | `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md` (user-level, xcelium-mcp의 `skill-src/xcelium-sim/references/phase-0-discovery.md`가 git 정본) | §0A(공유 컴포넌트)/§0B(테스트케이스)/§0C(캐시 관리 규칙) 전체 | 배포 완료(2026-07-03), 이미 verilog-tb-analyst 위임 문구 포함 |

### 계약 요약 (2026-07-03 시점)

**왜 신설하는가**: 기존 5개 verilog-rtl-* agent 중 TB(테스트벤치) 분석서를 다루는 agent가 없다. `verilog-rtl-analyst`는 RTL 쪽(`.ai/analysis/{module}.analysis.md`, Phase 1B)만 전담하고, TB 쪽(`.ai/analysis/tb_{env}_*.analysis.md`, Phase 0A/0B/1A)은 위임 대상이 없어 `verilog-rtl-debugger`(또는 Claude)가 그때그때 직접 수행하도록 방치돼 있었다. venezia-fpga 세션에서 이 비대칭이 지적되어 확정.

**방법론 출처(중요 — 중복 금지, 2026-07-03 결정)**: 이 agent는 TB 분석 방법론을 system prompt에 **복사해 내장하지 않는다.** `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md`(§0A/0B/0C)가 **유일한 정본**이고, 이 agent는 **런타임에 그 파일을 Read**해서 따른다. 이 원칙은 `verilog-rtl-debugger.plan.md`가 이미 확립한 패턴과 동일하며, **`verilog-rtl-analyst.md`(§0 "시작 시 반드시 로드" — `verilog-rtl` skill §12를 Read로 적재, 중복 서술 안 함) 자체가 이미 쓰고 있는 컨벤션과도 정확히 일치한다** — 이 repo의 "-analyst" 계열 agent는 원래 이렇게 만든다.

### TB 분석 규칙 발췌 (2026-07-03, phase-0-discovery.md 기준 — Design/Do 착수 전 재확인 필수)

아래는 이 문서 작성 시점의 규칙 요약이며, **agent 구현 시 이 요약이 아니라 위 표의 원본 파일을 직접 Read**해야 한다(요약은 drift 위험이 있음).

| 항목 | 규칙 |
|------|------|
| §0A 파일 네이밍 | `.ai/analysis/tb_{env}_{component_name}.analysis.md` — env prefix(`lgc`/`uvm`/`dsv`/`ams`) 항상 필수 |
| §0A 대상 식별 | 테스트케이스에서 `include`/`import`/인스턴스화되는 외부 파일·패키지 중 **여러 테스트에서 공통으로 쓰이는 것** |
| §0A 필수 항목 | 인터페이스 API, 프로토콜/시퀀스, 타이밍, 알려진 제약, DUT 계층 참조, 상위 호출 패턴, 판정 기여 |
| §0B 파일 네이밍 | `.ai/analysis/tb_{env}_{test_name}.analysis.md` |
| §0B 작성 절차(4단계) | 1) 테스트 파일 스캔(DUT 신호·task·include) 2) 시나리오 추출(`test_id`+주석) 3) 시퀀스 상세 파악 4) 공통 Dump 신호 추출(regression 직전 1회) |
| §0B 필수 항목 | 테스트 목적, 사용 공유 컴포넌트, 테스트 시나리오(tid별 표), 판별 방법, 판별 신호+기대값, DUT 내부 참조, 시뮬레이션 길이, 버그 이력 |
| §0C 캐시 관리 | 작성 시점=처음 디버깅할 때(lazy), 갱신 시점=파일 수정 시만, RTL만 바뀌고 TB 미변경 시 갱신 불필요, 저장 위치 `.ai/analysis/tb_*.analysis.md` |

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | xcelium-mcp 디버깅 워크플로우의 Phase 0A/0B/1A(TB 공유 컴포넌트·테스트케이스 분석서 작성)를 전담하는 agent가 없어, RTL 쪽(`verilog-rtl-analyst`)과 비대칭 — `verilog-rtl-debugger`나 Claude가 매번 즉흥적으로 수행 |
| **Solution** | `verilog-rtl-analyst`와 동일한 컨벤션(정본 skill/문서를 Read로 적재, 중복 서술 안 함, `.ai/analysis/**`만 Write)으로 `verilog-tb-analyst` agent를 신설 — 방법론은 `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md`를 런타임 Read |
| **Function/UX Effect** | TB 분석서 부재/stale 시 `verilog-tb-analyst`가 자동으로 §0A/0B 형식에 맞춰 작성 — env prefix 누락, 필수 항목 누락 같은 규칙 위반 없이 일관된 품질 보장 |
| **Core Value** | RTL/TB 양쪽 분석서 작성이 대칭적인 전담 agent 구조를 가지게 되어, xcelium-sim skill과 verilog-rtl-debugger가 "탐색·판별"에만 집중할 수 있음 |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | TB 분석서 작성 방법론(§0A/0B/0C)이 전담 agent 없이 방치되어 RTL 쪽과 비대칭 (§정합성 유지 계약 요약 참조) |
| **WHO** | xcelium-mcp를 사용해 RTL 디버깅을 수행하는 모든 프로젝트의 AI 에이전트 (1차 소비자: venezia-fpga) |
| **RISK** | xcelium-mcp 쪽 phase-0-discovery.md가 개정되는데 이 agent가 인지 못 하면 규칙 위반 분석서 생성 위험 — 수동 대조 외 안전장치 없음 |
| **SUCCESS** | §0A/0B 규칙(env prefix, 필수 항목, 4단계 절차)을 빠짐없이 지키는 분석서 생성; `verilog-rtl-analyst`와 동일한 품질 기준 |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-analyst.md`) 작성 + `install.py` 배포 등록만. xcelium-sim skill 자체나 TB 분석 방법론 정의는 xcelium-mcp repo 소관(Out of Scope) |

---

## 1. Overview

### 1.1 Purpose

TB 공유 컴포넌트·테스트케이스 분석서(`.ai/analysis/tb_{env}_*.analysis.md`)의 작성·갱신을 전담하여, xcelium-sim skill의 Phase 0(인프라 분석)/Phase 1A(캐시 미스 시)에서 위임받아 수행한다.

### 1.2 Background

`verilog-rtl-analyst`는 이미 이 repo의 "분석서 전담 agent" 컨벤션을 확립해뒀다(§0 "시작 시 반드시 로드"로 정본 skill을 Read, 중복 서술 없음, `.ai/analysis/**`만 Write, HANDS OFF로 원본 미수정). `verilog-tb-analyst`는 이 컨벤션을 TB 도메인에 그대로 적용하는 **자매(sibling) agent**다. 차이점은 정본 소스가 `verilog-rtl` skill(§12)이 아니라 **xcelium-sim skill(user-level, xcelium-mcp가 정본 관리)의 phase-0-discovery.md**라는 것 — cross-repo 참조라는 점이 유일한 구조적 차이.

**agent와 skill의 관계 원칙**: `verilog-tb-analyst`는 `xcelium-sim` skill(§0A/0B/0C 방법론)의 **대체물이 아니라 그 위의 선택적 최적화 계층**이다. skill 자체는 agent 설치 여부와 무관하게 항상 단독으로 동작 가능해야 한다 — agent가 없는 프로젝트, 또는 `verilog-rtl-debugger`/Claude가 직접 phase-0-discovery.md를 Read해 수행하는 경로(fallback)가 항상 유효해야 한다. 따라서 이 agent 완성은 fallback을 제거하는 게 아니라, "가능하면 agent에 위임(전담 분업으로 일관성↑), 불가능하면 skill을 직접 따라 수행(fallback으로 항상 동작)"이라는 **2단 경로**를 만드는 것이다 — 이는 §6.2/§8 Next Steps에도 동일하게 반영한다.

### 1.3 Related Documents

- **요구사항 정본**: §정합성 유지 절의 xcelium-mcp 2개 문서 + phase-0-discovery.md(외부 repo — 반드시 원본 확인)
- **자매 agent(동일 repo, 동일 컨벤션)**: `agents/verilog-rtl-analyst.md` — frontmatter 구조, "0. 기준 — 시작 시 반드시 로드", "하드 제약(HANDS OFF)", "Manifest" 섹션을 그대로 벤치마크
- **cross-repo 관계 선례**: `verilog-rtl-debugger.plan.md` — 같은 방식(정본 Read, 배포 경로, 갱신 규칙)의 cross-repo 계약 문서

---

## 2. Scope

### 2.1 In Scope

- [ ] `agents/verilog-tb-analyst.md` 신규 작성 — `verilog-rtl-analyst.md`와 동일 frontmatter 컨벤션(`name`/`description`(Use it when/Do NOT use for/Triggers)/`tools`/`model`)
- [ ] "0. 기준 — 시작 시 반드시 로드" 절에 `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md`를 Read로 적재하는 지시 포함 (agent엔 Skill tool 없으므로 파일 직접 Read — `verilog-rtl-analyst`와 동일 이유)
- [ ] "0. 기준"에 TB 코드 자체(SystemVerilog/UVM/듀얼탑 구조)를 정확히 해석하기 위한 3개 보조 스킬을 **전체 파일 Read**로 추가 적재: `verilog-rtl` SKILL.md 전체(FR-10), `chip-verification` SKILL.md 전체(FR-11), `uvm-verification` SKILL.md 전체(FR-12) — 2026-07-07 결정으로 "필요 절만 한정" 방침 폐기(§정합성 유지 이후 절 참조)
- [ ] **원격 TB 소스 접근 (host 파라미터 불필요)**: 분석 대상 TB 파일이 로컬이 아니라 원격 호스트(venezia-fpga의 경우 현재 `cloud0`)에 있을 수 있으므로 `mcp__ssh__file_read`/`file_grep`/`file_ls`를 tool 목록에 포함(FR-02/FR-13). 이 tool들은 호출 시 host 인자를 받지 않음(MCP 서버 등록 시점에 이미 고정) — agent는 세션에서 `mcp__ssh__*` 사용 가능 여부만으로 로컬/원격을 판단하며, `sim_discover` 호출이나 호스트명 하드코딩은 하지 않음(MCP 권한 없음, Out of Scope)
- [ ] **(v0.10 신설) `mcp__ssh__*` 사용 판단 정본 Read**: "0. 기준"에 `~/.claude/skills/ssh-mcp/SKILL.md`(user-level)를 **MUST** Read로 추가(FR-15) — `mcp__ssh__file_read`/`file_grep`/`file_ls` 사용 시의 판단 기준(장시간 걸릴 수 있는 호출의 처리, 세션/서버 재시작을 넘나드는 job 관리, 정리 시점 등)이 이 skill의 정본이므로 재서술하지 않고 런타임 참조
- [ ] §0A/0B/0C 규칙(env prefix, 필수 항목, 4단계 절차, 캐시 관리)을 **재서술하지 않고** phase-0-discovery.md 참조로 위임
- [ ] `.ai/analysis/tb_*.analysis.md`에만 Write하는 HANDS OFF 제약(RTL/TB 실제 코드 무수정) 명시
- [ ] `install.py` 배포 목록에 등록, 기존 `verilog-rtl-analyst`와 동일 경로(`~/.claude/agents/`)로 배포

### 2.2 Out of Scope

- TB 분석 방법론(§0A/0B/0C) 자체의 정의/변경 — xcelium-mcp repo(`xcelium-mcp-debugging-workflow.plan.md`, `xcelium-sim` skill) 소관
- xcelium-sim skill 자체의 구조·배포 — xcelium-mcp repo 소관, 독립 배포(**그 repo의** `xcelium-mcp-tool-usage-guide.plan.md` FR-10 — 이 문서 §3의 로컬 FR-10(verilog-rtl skill 로드)과 번호가 겹치므로 혼동 주의)
- RTL 분석서(`verilog-rtl-analyst`의 영역) — 별개 agent, 이 문서 무관
- `verilog-rtl-debugger`와의 라우팅 로직 구현 — 그쪽 Plan(`verilog-rtl-debugger.plan.md`) 소관, 이 문서는 "TB 분석서를 어떻게 작성하는가"만 다룸
- `verilog-rtl`/`chip-verification`/`uvm-verification` skill 자체의 구조·내용 변경 — 각 skill 소관, 이 agent는 정본을 Read만 함(FR-10/FR-11/FR-12)
- TB 실제 컴포넌트 구현(agent/driver/monitor/scoreboard 코드 작성) — `chip-verification`/`uvm-verification` skill이 다루는 "TB를 어떻게 만드는가"의 영역, 이 agent는 "이미 존재하는 TB를 어떻게 분석·문서화하는가"만 담당
- `sim_discover` 호출 및 시뮬레이션 환경 등록(`0-Prep`) — `mcp__xcelium-mcp__*` 접근권이 있는 호출자(`verilog-rtl-debugger`/Claude) 소관. 이 agent는 이미 확정된 `target_paths`를 Task() 파라미터로 **받기만** 함(FR-13). 원격 호스트 접속 자체는 `mcp__ssh__*` MCP 서버 등록에서 이미 해결되므로 이 agent도, 호출자도 호스트명을 알거나 다룰 필요가 없음

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `agents/verilog-tb-analyst.md` frontmatter — `verilog-rtl-analyst.md`와 동일 구조. Triggers 예시: "TB 분석", "테스트벤치 분석", "tb_*.analysis.md", "분석서 부재"(TB 맥락), "공유 컴포넌트 분석", "테스트케이스 분석" | High | Pending |
| FR-02 | Tool 목록: `Read, Write, Edit, Glob, Grep, Bash` + **`mcp__ssh__file_read`, `mcp__ssh__file_grep`, `mcp__ssh__file_ls`** (2026-07-06 수정 — 최초안 오류 정정) — `mcp__xcelium-mcp__*`(시뮬레이션 실행 MCP)는 여전히 불필요하지만, 분석 **대상**(TB 테스트케이스·공유 컴포넌트 원본)이 로컬이 아니라 원격 호스트(venezia-fpga는 현재 `cloud0`, 프로젝트별 상이)에 있을 수 있으므로 원격 파일 접근용 `ssh-mcp` 도구는 필수. **이 tool들은 host 인자를 받지 않음**(MCP 서버 등록 시 고정) — agent는 세션 내 `mcp__ssh__*` 가용 여부로 로컬/원격을 판단(FR-13), 로컬 `Read/Glob/Grep`은 `.ai/analysis/tb_*.analysis.md` 출력물 전용(및 ssh-mcp 미등록 프로젝트의 대상 스캔)으로 범위 유지 | High | Pending |
| FR-03 | "0. 기준 — 시작 시 반드시 로드"에 `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md`를 **MUST** Read로 명시 — §0A/0B/0C가 분석서 구조·갱신규칙의 정본, 여기 중복 서술 안 함(`verilog-rtl-analyst` §0과 동일 원칙) | High | Pending |
| FR-10 | "0. 기준"에 `~/.claude/skills/verilog-rtl/SKILL.md` **전체**를 **MUST** Read로 명시(2026-07-08 수정 — 이전엔 §8+coverage refs 3종만 한정, 아래 "부분로딩 폐기" 결정 참조) — TB 코드가 SystemVerilog(때로 Verilog-A)이므로 covergroup/coverpoint/cross/SVA assertion 문법을 정확히 해석하려면 §8이 필요하지만, RTL 합성·CDC·FSM 규칙(§1~§7, §11)도 함께 읽는다 | High | Pending |
| FR-11 | "0. 기준"에 `~/.claude/skills/chip-verification/SKILL.md` **전체**를 **MUST** Read로 명시(2026-07-08 수정 — 이전엔 §듀얼탑 아키텍처+interface-mapping.md만 한정) — env 무관 대부분의 TB가 hdl_top/hvl_top 듀얼탑 구조이므로 그 절이 핵심이지만, Reference Model/Scoreboard/AMS 아날로그 모델 교체 등 나머지 절도 함께 읽는다 | High | Pending |
| FR-12 | "0. 기준"에 `~/.claude/skills/uvm-verification/SKILL.md` **전체**를 **MUST** Read로 명시(2026-07-08 수정 — 이전엔 §UVM 계층 구조+component-templates.md/sequence-patterns.md만 한정) — env prefix `uvm`인 테스트벤치의 agent/driver/monitor/sequencer/scoreboard 용어 식별에 그 절이 핵심이지만, RAL/coverage subscriber/report catcher 등 나머지 절도 함께 읽는다 | High | Pending |
| FR-04 | §0A(공유 컴포넌트) 절차 반영: 대상 식별(여러 테스트 공통 include/import), 파일 네이밍(env prefix 필수), 필수 항목 7종 | High | Pending |
| FR-05 | §0B(테스트케이스) 절차 반영: 4단계 작성 절차(스캔→시나리오→시퀀스→공통신호), 파일 네이밍, 필수 항목 8종 | High | Pending |
| FR-06 | §0C(캐시 관리) 규칙 반영: lazy 작성, 파일 변경 시만 갱신, RTL 전용 변경 시 갱신 불필요 | High | Pending |
| FR-07 | HANDS OFF 제약: `.ai/analysis/tb_*.analysis.md`만 Write, TB 실제 코드(`tb_tests/*.v`, agent/BFM 소스 등)·RTL(`db/design`) 무수정 | High | Pending |
| FR-08 | Manifest(오케스트레이터 반환) 형식: 작성/갱신한 `tb_*.analysis.md` 경로 목록(신규/갱신 구분), phase-0-discovery.md 및 FR-10/FR-11/FR-12 보조 스킬 3종 적재 여부, 미해결 BLOCKER | Medium | Pending |
| FR-09 | `install.py` AGENTS 목록에 등록, 기존 배포 경로(`~/.claude/agents/`)와 동일하게 배포 | Medium | Pending |
| FR-15 | **(신설, 2026-07-08)** "0. 기준 — 시작 시 반드시 로드"에 `~/.claude/skills/ssh-mcp/SKILL.md`(user-level, 전체) **MUST** Read 추가 — `mcp__ssh__file_read`/`file_grep`/`file_ls`(FR-02) 사용 시 판단 기준(예: 호출이 오래 걸릴 수 있는 상황의 처리, 세션·서버 재시작을 넘나드는 백그라운드 job 관리, 정리 시점 판단)의 정본. 이 agent는 읽기 전용 3개 tool만 쓰므로 skill의 `ssh_bg_run`/`ssh_bg_poll`/`ssh_bg_kill` 관련 내용 대부분은 해당 없을 수 있으나, 판단 기준 자체를 재서술하지 않고 매 실행 시 Read로 참조한다는 원칙(FR-03/10/11/12와 동일)은 동일하게 적용 — 이 skill이 등록 안 된(=TB가 로컬인) 프로젝트에서는 §4.1a(FR-13) 판단대로 애초에 로드 대상이 아님 | High | Pending |
| FR-14 | **분석서 헤더 staleness hash(F-175 `tb_provenance`/`combined_sha256`) 기록 — 신설(2026-07-07, `verilog-rtl-debugger.plan.md` FR-10과 짝을 이루는 반쪽)**: phase-0-discovery.md §0C는 분석서 헤더에 작성 시점의 `tb_source`/`tb_provenance`(`{"files":[{"path","sha256"}],"combined_sha256"}`)를 기록해두고 다음 재사용 시 비교하도록 정의하는데, 이 값은 `sim_batch_run`/`sim_regression`/`sim_bridge_run`(`mcp__xcelium-mcp__*`) 반환값에서만 나온다 — 이 agent는 그 tool 접근권이 없다(FR-02, ssh-mcp 읽기 전용만 보유). 즉 이 값은 **호출자(`verilog-rtl-debugger`, 이미 sim tool을 실행한 뒤 위임)가 Task()로 넘겨줘야만** 기록 가능하다. Task() 시그니처(FR-13, 현재 5개: env/target_type/target_name/target_paths/reason)에 **6번째 파라미터 `tb_provenance`(nullable, JSON)**를 추가하고: (a) 값이 있으면 §0A/0B 작성·갱신 시 그 값을 헤더에 그대로 기록(재계산하지 않음 — xcelium-mcp가 계산한 값을 신뢰), (b) 값이 없으면(예: agent 미배포로 Claude가 phase-0-discovery.md를 직접 수행하는 fallback 경로, 혹은 호출자가 sim을 아직 안 돌린 상태) 헤더에 "hash 미기록(caller가 tb_provenance 미전달)"을 **명시적으로** 남겨 §0C 규칙 3번("기록 없으면 stale로 간주")이 다음 재사용 시 올바르게 작동하게 한다 — 조용히 생략하지 않는다. `verilog-rtl-debugger.plan.md` FR-10(§2 위임 매핑표 Task() 패턴에 `tb_provenance` 추가)과 반드시 함께 반영 — 한쪽만 고치면 값을 넘겨도 받는 쪽이 못 쓰거나, 받을 준비는 됐는데 아무도 안 넘기는 상태가 됨 | High | Pending |
| FR-13 | **원격 탐색 방법론 — host 파라미터 자체가 불필요함 확인** (2026-07-06 신설 → 07-06 1차 수정: `access_mode`/`ssh_host` 파라미터화 → 07-06 2차 수정: **그 파라미터마저 불필요함을 확인**): `mcp__ssh__file_read`/`file_grep`/`file_ls` tool 스키마를 직접 확인한 결과 **`host` 인자가 존재하지 않는다** — 접속 대상은 MCP 서버 등록 시점(프로젝트별 `.mcp.json`, `mcp__xcelium-mcp__*`와 동일하게 SSH stdio transport로 이미 고정)에 결정되고, tool 호출 시점엔 그냥 "이 서버에서"(this server) 동작한다. 즉 이 agent는 원격 호스트명을 **알 필요도, 파라미터로 받을 필요도 없다** — Task()에 `access_mode`/`ssh_host`를 추가할 필요 자체가 없었음(1차 수정 시의 과잉 설계, 2차 수정에서 제거). 대신 agent 내부 규칙만 필요: "0. 기준" 절 로드 후 대상 스캔 시 **`mcp__ssh__file_ls`/`file_grep`/`file_read`가 이 세션에서 사용 가능하면 그것으로, 없으면(그 프로젝트에 ssh-mcp가 등록 안 됨 = TB 소스가 로컬) 로컬 `Glob`/`Grep`/`Read`로** 스캔 — 이 판단은 호출자가 파라미터로 알려주는 게 아니라 agent 자신의 tool 가용성으로 즉시 판단 가능. Task() 시그니처는 원래의 5개 파라미터(env/target_type/target_name/target_paths/reason)로 되돌아감(§7.2 갱신) | High | Pending |

> **2026-07-08 결정 — "필요 절만 부분로딩" 방침 폐기, 전체 skill 파일 Read로 전환(FR-10/11/12)**: 원래 방침은 TB 분석과 "무관한" 절(RTL 합성/CDC, AMS 아날로그 모델 등)을 안 읽어서 컨텍스트를 아끼자는 것이었다. 그런데 이 회차에 `verilog-rtl-debugger.plan.md` FR-10을 등록하면서, 정확히 같은 종류의 "정적으로 박아둔 부분 로딩 목록"(그쪽은 절 단위가 아니라 파일 단위: phase-2~5만 MUST, phase-0 누락)이 실패 모드의 원인이었음을 실측 확인했다 — 부분로딩 목록은 skill이 개정되거나 새 요구사항이 생겨도 agent 파일 쪽에서 자동으로 안 따라가고, 그 drift를 잡는 유일한 수단이 사람의 수동 대조("정합성 유지" 섹션들이 각 plan 문서마다 따로 존재하는 이유)뿐이었다. 대상 skill들(verilog-rtl/chip-verification/uvm-verification SKILL.md)이 각각 수백 줄 내외로 전체를 읽어도 부담이 크지 않다는 점을 감안하면, 부분 절 curation이 절약하는 컨텍스트보다 그 목록을 정확히 유지하는 데 드는 비용(사람이 skill 개정마다 재대조)이 더 크다고 판단 — 전체 Read로 단순화하고, 그 목록 자체를 없애 drift 가능성을 원천 차단한다. 같은 패턴이 `verilog-rtl-analyst.md`(§12만 로드)에도 있으나, 그 agent엔 대응하는 `.plan.md`가 없어 이번 등록 범위에서는 제외 — 별도로 다룰지는 후속 확인 필요.

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|---------------------|
| Cross-repo Consistency | §0A/0B/0C 규칙이 xcelium-mcp phase-0-discovery.md와 100% 일치(재서술 아님, Read 참조) | Design 단계에서 원본 재확인 |
| 컨벤션 일관성 | `verilog-rtl-analyst.md`와 구조·톤·섹션 순서 동일 | 두 agent 파일 diff 리뷰 |
| 규칙 준수 | 생성되는 모든 `tb_*.analysis.md`가 env prefix 필수 규칙을 위반하지 않음 | 샘플 분석서 생성 후 네이밍 검증 |
보조 스킬 전체 로드 확인 | FR-10/FR-11/FR-12에서 지정한 3개 skill을 **전체 파일** 단위로 로드(부분 절 curation 없음, 2026-07-08 결정) | agent 파일의 "0. 기준" 절이 파일 경로만 지정하고 절 번호로 범위를 제한하지 않는지 확인 |

---

## 4. Success Criteria

### 4.1 Definition of Done

- [ ] `agents/verilog-tb-analyst.md` 작성 완료, `verilog-rtl-analyst.md`와 동일한 품질 기준(왜 별도 agent인가, 왜 이 model인지, HANDS OFF, 정직한 한계 섹션 포함) 충족
- [ ] `install.py` 배포 등록 + 배포 테스트(`~/.claude/agents/verilog-tb-analyst.md` 생성 확인)
- [ ] xcelium-mcp phase-0-discovery.md §0A/0B/0C와 최종 대조, 불일치 없음
- [ ] venezia-fpga 세션에서 실제 TB 분석서 생성 시나리오로 수동 검증(env prefix, 필수 항목 포함 여부)

### 4.2 Quality Criteria

- [ ] `verilog-rtl-analyst`와 트리거 키워드 중복 최소화(RTL vs TB 구분 명확)
- [ ] `verilog-rtl-debugger`(그쪽 문서 "계약 요약 > 위임 매핑표" TB 행에서 TB 분석서 부재 시 이 agent 호출)와의 위임 인터페이스가 자연스러움(Task 호출 시 필요한 입력: env, component/test 이름, 대상 파일 경로)

---

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| xcelium-mcp phase-0-discovery.md가 개정되는데 이 agent 구현이 낡은 규칙을 내장 | High | Medium | FR-03로 "런타임 Read, 재서술 금지" 원칙 강제 — 내장하지 않으므로 개정이 자동 반영됨 |
| `verilog-rtl-analyst`와 트리거 중복(둘 다 "분석서 작성" 관련) | Medium | Medium | Triggers를 RTL(`.analysis.md`, 모듈명)과 TB(`tb_*.analysis.md`, 테스트/컴포넌트명)로 명확히 구분(FR-01) |
| phase-0-discovery.md가 아직 참조 대상으로 충분히 자기완결적이지 않을 가능성 | Low | Low | 이미 tool-usage-guide feature의 Quality Criteria로 자기완결성이 검증됨(2026-07-03 Report, Match Rate 98%) — 재검증만 필요 |
| **(2026-07-06 신규)** 분석 대상 TB 소스가 로컬이 아니라 원격(venezia-fpga 기준 cloud0)에 있는데 최초 FR-02가 이를 놓치고 로컬 `Read/Glob/Grep`만으로 충분하다고 잘못 가정 | High | High (현재 확정, FR-02/FR-13으로 이미 수정) | `mcp__ssh__*` tool 추가로 해소. **부가 발견**: xcelium-mcp `phase-0-discovery.md` §0A 자체의 예시 명령(`grep -oE ... tb/**/*.sv`)도 로컬 glob 패턴이라 같은 가정 오류를 안고 있을 수 있음 — xcelium-mcp repo 쪽에 예시 명령을 `ssh-mcp` 기반으로 갱신 검토 요청 필요(Design 단계 이후 별도 확인) |
| **(2026-07-07 신규)** FR-14 없이는 이 agent가 작성하는 모든 분석서가 `combined_sha256` 미기록 상태로 남아, `verilog-rtl-debugger`(FR-10 반영 후)가 매번 "hash 기록 없음=stale"로 판정 → 매 세션 이 agent를 재호출 — §0C가 의도한 "lazy 작성, 파일 변경 시만 갱신" 캐싱 최적화가 무력화(정확성 문제는 아니고 효율성 회귀) | Medium | High(FR-10만 단독 반영 시 확정) | FR-14를 FR-10과 동시에 반영 — 어느 한쪽만 고치는 순서 금지(§8 Next Steps #7) |
| **(2026-07-06, 2차 수정)** "cloud0"라는 특정 호스트명을 agent 설계에 하드코딩할 뻔함 — venezia-fpga만의 `~/.ssh/config` 값이라 다른 RTL 프로젝트(다른 호스트, 또는 로컬 실행)에서 재사용 불가. **1차 수정(`access_mode`+`ssh_host` Task() 파라미터화)도 과잉이었음** — `mcp__ssh__*` tool 스키마 확인 결과 애초에 host 인자가 없어 그런 파라미터 자체가 불필요 | Medium | Medium (실제 발생, 2차 수정으로 완전 해소) | FR-13 최종 형태: Task() 파라미터 추가 없이, agent가 세션 내 `mcp__ssh__*` tool 가용성만으로 로컬/원격 스캔 방식을 스스로 결정 — 이 agent는 호스트명은 물론 "로컬이냐 원격이냐"조차 파라미터로 안 받아도 됨. 다른 프로젝트 배포 시 그 프로젝트의 `.mcp.json`에 ssh-mcp 등록 여부만 맞으면 자동 대응 |

---

## 6. Impact Analysis

### 6.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|---------------------|
| `agents/verilog-tb-analyst.md` | 신규 파일 | 신규 agent 정의 |
| `install.py` | 스크립트 | AGENTS 목록에 신규 agent 추가 |
| `~/.claude/agents/verilog-tb-analyst.md` | 배포 산출물 | install.py 실행 시 신규 생성 |

### 6.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| (신규 agent라 현재 소비자 없음) | — | — | — |
| **외부 계약(예정)**: `verilog-rtl-debugger` agent(그쪽 문서 "계약 요약 > 위임 매핑표" TB 행) | INVOKE(완성 후 우선 경로) | Phase 0A/0B/1A에서 TB 분석서 부재/stale 시 위임 | Needs verification — agent 완성 후에도 fallback(`verilog-rtl-debugger`/Claude가 phase-0-discovery.md를 직접 Read해 수행)은 **영구 유지**. agent는 fallback을 대체하는 게 아니라 그 위의 우선 경로(§1.2 "agent와 skill의 관계 원칙" 참조) |
| **외부 계약(예정)**: xcelium-sim skill(phase-0-discovery.md, phase-1-analysis.md) | READ(런타임) | 이 agent가 매 실행 시 참조하는 정본 | Needs verification — 두 파일이 자기완결적으로 유지되는지 |

### 6.3 Verification

- [ ] `verilog-rtl-debugger`가 이 agent를 정상적으로 Task 위임할 수 있는지 확인
- [ ] `install.py --only agents` 실행 후 배포 경로 확인

---

## 7. Convention Prerequisites

### 7.1 Existing Project Conventions

- [x] `agents/verilog-rtl-analyst.md` — 이 문서가 벤치마크하는 정확한 자매 agent, 구조 그대로 재사용
- [x] "정본 skill/문서를 Read로 적재, 재서술 안 함" 컨벤션 — `verilog-rtl-analyst` §0에서 이미 검증된 패턴
- [x] `install.py` agent 배포 스크립트 존재

### 7.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| Cross-repo 정본 Read 경로 표기 | `verilog-rtl-analyst`는 동일 repo 내 skill 참조(`~/.claude/skills/verilog-rtl/`) | 이 agent는 **다른 repo(xcelium-mcp)가 배포한** user-level skill(`~/.claude/skills/xcelium-sim/`)을 참조 — 경로 자체는 동일한 user-level이라 Read 메커니즘은 같지만, "정본이 다른 repo에 있다"는 점을 agent 문서에 명시할 필요 | High |
| 4-skill Read 우선순위/충돌 처리 | 미정 — xcelium-sim(TB 분석 방법론) + verilog-rtl(§8 SV 문법) + chip-verification(듀얼탑) + uvm-verification(UVM 구조) 4개 정본을 동시 Read | "0. 기준" 절에 Read 순서와 각 skill의 담당 범위를 명확히 구분 표기(어떤 절이 겹치지 않는지 §Cross-Skill 참조 표처럼 명시) — `uvm-verification` SKILL.md가 이미 "RTL-TB 인터페이스는 chip-verification 소관"이라 명시한 것과 정합성 유지 | High |
| `verilog-rtl-debugger`와의 Task 위임 인터페이스 | **재오픈(2026-07-07, FR-14)** — 5개 파라미터(env/target_type/target_name/target_paths/reason)로 확정했던 것에 **6번째 `tb_provenance`(nullable) 추가 필요**. staleness hash를 낼 수 있는 쪽(sim tool 접근권)과 그걸 기록해야 하는 쪽(분석서 Write 권한)이 서로 다른 agent라 이 필드 없이는 §0C 캐시 관리가 성립하지 않음이 실사용(venezia-fpga T-002) 중 드러남 | `verilog-rtl-debugger.plan.md` FR-10과 동시 반영 | High |
| **(2026-07-06, 최종 해소)** 원격 경로·호스트 표기 컨벤션 | **불필요함으로 결론(Design §4.1a)** — `cloud0:~/...` 문자열 prefix → `access_mode`+`ssh_host` 별도 필드 → **최종적으로 둘 다 폐기**. `mcp__ssh__*` tool이 host 인자 자체를 받지 않으므로(MCP 등록 시 고정) 경로/호스트 표기 컨벤션이라는 문제 자체가 성립하지 않음 — agent는 세션 내 tool 가용성으로만 로컬/원격 판단 | 해소 완료, 재론 불필요 | — |

---

## 8. Next Steps

1. [ ] 착수 전 §정합성 유지의 xcelium-mcp 2개 문서 + phase-0-discovery.md를 다시 Read — 버전이 위 표와 다르면 발췌 요약부터 갱신
2. [ ] `/pdca design verilog-tb-analyst` — Tool 목록 최종 확정(FR-02 검토), Task() 위임 인터페이스 설계(§7.2)
3. [ ] `agents/verilog-tb-analyst.md` 작성 (`verilog-rtl-analyst.md` 구조 그대로 벤치마크)
4. [ ] `install.py` 등록 + 배포 테스트
5. [ ] `verilog-rtl-debugger.plan.md`의 위임 로직에 이 agent 호출이 실제로 연결되는지 확인
6. [ ] xcelium-mcp 쪽 문구를 "fallback만 존재"에서 "agent 호출을 우선 경로로 추가하되, fallback(`verilog-rtl-debugger`/Claude가 phase-0-discovery.md 직접 Read)은 agent 미설치/미사용 환경을 위해 영구 유지"로 갱신하는 후속 체크리스트를 xcelium-mcp-debugging-workflow.plan.md/xcelium-mcp-tool-usage-guide.plan.md에 반영 요청 — fallback 제거가 아님에 주의
7. [ ] **FR-14 (Do 재진입, `verilog-rtl-debugger.plan.md` FR-10과 동시 진행)** — Task() 시그니처에 `tb_provenance`(nullable) 6번째 파라미터 추가 + §3 작성 절차에 헤더 기록 규칙(있으면 그대로 기록, 없으면 "미기록"을 명시적으로 남김) 반영. 이미 `agents/verilog-tb-analyst.md`가 배포돼 있다면 그 파일 + `~/.claude/agents/verilog-tb-analyst.md` 양쪽 갱신 후 `install.py` 재배포

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-03 | 초안 — xcelium-mcp repo에서 확정된 TB 분석서 위임 요구사항(xcelium-mcp-debugging-workflow.plan.md v2.7, xcelium-mcp-tool-usage-guide.plan.md v0.8 FR-13)을 이 repo로 가져와 Plan 문서화. `verilog-rtl-analyst.md`를 자매 agent 컨벤션으로 명시적으로 벤치마크, "정본 Read·재서술 금지" 원칙을 처음부터 반영(verilog-rtl-debugger에서 겪은 시행착오를 반복하지 않기 위함) | HSLEE |
| 0.2 | 2026-07-03 | TB 코드 자체가 SystemVerilog/UVM/듀얼탑 구조로 작성된다는 지적 반영 — "0. 기준" 보조 정본 3종 추가: `verilog-rtl`(§8+coverage refs, FR-10), `chip-verification`(§듀얼탑 아키텍처+interface-mapping.md, FR-11), `uvm-verification`(§UVM 계층 구조+component-templates.md/sequence-patterns.md, FR-12). 모두 "핵심 구조 절만" 한정 로드로 범위 확정(RTL 합성·CDC, AMS 아날로그 모델, RAL/coverage subscriber 등은 제외) — Scope/NFR/Convention Prerequisites/Manifest(FR-08)에 반영 | HSLEE |
| 0.3 | 2026-07-03 | fallback(`verilog-rtl-debugger`/Claude가 phase-0-discovery.md 직접 Read해 수행)은 "agent 완성 전 임시 대체"가 아니라 "skill이 agent 설치 여부와 무관하게 항상 단독 동작해야 하므로 영구 유지"라는 관점 반영 — §1.2에 "agent와 skill의 관계 원칙" 신설(agent=선택적 최적화 계층, fallback=영구 기본 경로), §6.2 Current Consumers 행과 §8 Next Steps 6번을 "fallback 제거/전환"에서 "agent를 우선 경로로 추가, fallback 영구 유지"로 수정 | HSLEE |
| 0.4 | 2026-07-03 | **두 자매 plan 문서 전수 정합성 감사 반영** — (1) §2.2 "독립 배포(FR-10)" 문구가 외부(xcelium-mcp tool-usage-guide.plan.md) FR-10을 가리키는데, 같은 문서 §3에 로컬 FR-10(verilog-rtl skill 로드)이 생기면서 번호가 겹쳐 혼동 가능했던 것을 "그 repo의 FR-10"으로 명시적으로 구분(자매 문서 `verilog-rtl-debugger.plan.md`가 이미 쓰던 패턴과 통일). (2) §6.2·§4.2에서 "§Agent 위임 구조 TB 행"이라고 외부 문서의 헤더명을 그대로 인용하던 것을, `verilog-rtl-debugger.plan.md`의 실제 로컬 섹션명("계약 요약 > 위임 매핑표")으로 정정. (3) 헤더 `Version: -` → `0.4`로 Version History와 동기화 | HSLEE |
| 0.5 | 2026-07-06 | **cloud0(원격) TB 소스 접근 공백 발견·수정** — Design 착수 중 "분석 대상 TB 파일이 실제로 어디 있는가"를 짚는 질문에서, 분석 산출물(`.ai/analysis/**`)은 로컬이지만 분석 **대상**(TB 테스트케이스·공유 컴포넌트 원본)은 cloud0(SSH 원격, xcelium-mcp Python server 실행 호스트)에 있다는 사실(`xcelium-mcp-v3-improvements.plan.md`에 이미 명시돼 있었음)을 최초 FR-02가 놓쳤던 것을 확인. FR-02에 `mcp__ssh__file_read`/`file_grep`/`file_ls` 추가, FR-13 신설(cloud0 탐색 방법론 — 호출자가 `sim_discover`로 경로 확정 후 Task()로 전달, 이 agent는 ssh-mcp로 스캔), §2.1/§2.2/§5 Risk/§7.2에 반영. 부가로 xcelium-mcp `phase-0-discovery.md` 자체의 예시 grep 명령도 로컬 경로를 가정하고 있어 같은 오류를 안고 있을 가능성 기록 | HSLEE |
| 0.6 | 2026-07-06 | **"cloud0" 하드코딩 제거 — 호스트 무관 일반화**: cloud0는 venezia-fpga만의 `~/.ssh/config` 값이라 agent 설계에 상수로 박으면 다른 RTL 프로젝트(다른 호스트, 또는 로컬 실행)에 재사용 불가하다는 지적 반영. FR-13을 `access_mode`(`"local"`\|`"ssh"`) + `ssh_host`(nullable) 두 Task() 파라미터로 재설계 — 이 agent는 호스트명을 전혀 모른 채 순수 파라미터로만 동작. §2.1 In Scope, FR-02, Risk 표(신규 항목 추가), §7.2(경로 표기 컨벤션 항목을 "해소"로 갱신 — 문자열 prefix 대신 별도 필드 방식 확정)에 반영 | HSLEE |
| 0.7 | 2026-07-06 | **`access_mode`/`ssh_host` 파라미터 자체가 불필요함을 확인 — 최종 단순화**: "ssh-mcp/xcelium-mcp는 이미 등록 시점에 host를 설정하는데, agent가 굳이 host를 알 필요가 있나"라는 지적에 `mcp__ssh__file_read`/`file_grep`/`file_ls` tool 스키마를 직접 확인 — **세 tool 모두 host 인자가 없음**(설명: "on this server"), 접속 대상은 `mcp__xcelium-mcp__*`와 동일하게 MCP 서버 등록 시점(SSH stdio transport)에 이미 고정됨을 확인. `verilog-rtl-debugger.plan.md`는 애초에 이 문제가 없었음(cloud0/host 언급 자체가 없이 처음부터 올바르게 설계됨, 확인 완료). FR-13을 "agent가 세션 내 `mcp__ssh__*` tool 가용성만으로 로컬/원격 스캔 방식을 스스로 판단"으로 재작성 — Task() 시그니처는 v0.5 이전의 5개 파라미터(env/target_type/target_name/target_paths/reason)로 복귀. §2.1/FR-02/Risk 표/§7.2에 반영 | HSLEE |
| 0.9 | 2026-07-08 | **부분로딩 방침 폐기 — FR-10/FR-11/FR-12를 전체 skill Read로 전환**: `verilog-rtl-debugger.plan.md` FR-10(부분 파일 목록 drift로 인한 staleness 체크 누락) 등록 직후, "agent가 skill의 일부만 읽는 게 정말 효율적인가"라는 근본 질문 제기 → 부분로딩(절 단위건 파일 단위건)이 절약하는 컨텍스트보다 그 목록을 정확히 유지하는 유지보수 비용이 크다고 판단해 폐기 결정. FR-10/11/12를 "전체 skill 파일 Read"로 재작성, §2.1 Scope 항목·§3.2 NFR 행 동반 수정, 결정 배경을 §3 상단에 콜아웃으로 기록. `verilog-rtl-analyst.md`(§12만 로드)도 동일 패턴이나 대응 plan 문서가 없어 이번 범위에서 제외 | HSLEE |
| 0.10 | 2026-07-08 | **FR-15 신설 — ssh-mcp skill Read 누락 발견**: 이 agent가 FR-02부터 `mcp__ssh__file_read`/`file_grep`/`file_ls`를 사용하도록 설계돼 있었는데, 그 tool들의 사용 판단 기준(오래 걸릴 수 있는 호출 처리, 세션/서버 재시작을 넘나드는 job 관리, 정리 시점 판단)을 담은 `ssh-mcp` skill(`~/.claude/skills/ssh-mcp/SKILL.md`) 자체를 "0. 기준"에서 Read하도록 지시한 적이 없었던 공백을 발견 — FR-03/10/11/12와 동일한 "정본 Read, 재서술 금지" 원칙이 유독 이 tool 그룹에만 빠져 있었음. FR-15 신설, §2.1 In Scope에 반영. `verilog-rtl-debugger`는 `mcp__ssh__*` tool 자체를 쓰지 않아(원격 TB 스캔을 전부 이 agent에 위임) 이번 범위에서 제외 | HSLEE |
| 0.8 | 2026-07-07 | **FR-14 신설 — staleness hash 기록 경로 부재 발견**: `verilog-rtl-debugger.plan.md` FR-10(분석서 staleness 체크 강제) 등록 과정에서, hash(`combined_sha256`)를 낼 수 있는 쪽(sim tool 접근권을 가진 `verilog-rtl-debugger`)과 그걸 분석서 헤더에 기록해야 하는 쪽(Write 권한을 가진 이 agent)이 서로 다른데, 정작 이 agent의 Task() 인터페이스(FR-13, §7.2에서 "해소"로 닫혀 있던 5개 파라미터)엔 hash를 넘겨받을 자리가 없었음을 확인. FR-14 신설(6번째 파라미터 `tb_provenance` 추가 + 헤더 기록 규칙), §7.2 해당 행 재오픈, §5 Risk 신규 행(캐싱 최적화 무력화 — 정확성 아닌 효율성 회귀), §8 Next Steps #7 추가. `verilog-rtl-debugger.plan.md` FR-10과 동시 반영 필수(한쪽만 고치면 값을 보낼 곳도, 받을 준비도 안 맞음) | HSLEE |
