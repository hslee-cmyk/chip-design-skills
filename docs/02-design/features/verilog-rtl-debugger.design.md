# verilog-rtl-debugger Design Document

> **Summary**: MCP-tool-aware 라우터 agent의 내부 구조 설계. 핵심은 (1) `mcp__xcelium-mcp__*` 24개 tool의 부여 범위(Option C: 전량 부여 + 문서화된 사용 규율), (2) Phase 2~4 방법론을 agent 내장 없이 런타임 Read하는 "0. 기준" 구조(v0.2부터 phase-0-discovery.md의 staleness 체크가 phase-2보다 먼저 실행되도록 포함), (3) 6개 자매 agent(analyst/coder/reviewer/architect-advisor/prover/tb-analyst)로의 Task() 위임 패턴 — `verilog-tb-analyst.design.md`에서 이미 확정한 6-파라미터 계약(env/target_type/target_name/target_paths/reason/tb_provenance)을 그대로 재사용한다.
>
> **Project**: chip-design-skills
> **Version**: 0.2
> **Author**: HSLEE
> **Date**: 2026-07-08
> **Status**: Draft
> **Planning Doc**: [verilog-rtl-debugger.plan.md](../01-plan/features/verilog-rtl-debugger.plan.md) (v0.8)

> 이 feature도 `verilog-tb-analyst`와 마찬가지로 웹앱이 아니라 **markdown agent 정의 파일 1개**를 만드는 작업이다. 템플릿의 DB/UI/Clean Architecture 섹션은 N/A 처리했고, "API Specification"은 이 agent가 **호출자 없이 스스로 다른 6개 agent를 호출하는 Task() 위임 계약**으로 대체했다 — `verilog-tb-analyst`가 "피호출자"였다면 이 문서는 "호출자" 관점의 동일 계약을 다룬다.

---

## Context Anchor

> Plan 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | xcelium-mcp 디버깅 워크플로우 Phase 2~4를 수행할 MCP-tool-aware agent가 없음 |
| **WHO** | xcelium-mcp를 사용해 RTL을 디버깅하는 모든 프로젝트의 AI 에이전트 (1차 소비자: venezia-fpga) |
| **RISK** | xcelium-mcp 쪽 요구사항(위임 매핑표)과 이 repo의 구현이 별도 PDCA 사이클로 진행되어 drift 가능 — 수동 대조 외 안전장치 없음 |
| **SUCCESS** | 위임 매핑표의 7개(v2.7, TB 행 포함) 상황 전부를 올바른 agent에 위임; Phase 2~4는 다른 agent 호출 없이 직접 수행 |
| **SCOPE** | agent 정의 파일(`agents/verilog-rtl-debugger.md`) 작성 + `install.py` 배포 등록만 |

---

## 1. Overview

### 1.1 Design Goals

- Plan FR-01~FR-10을 구체적인 agent 파일 섹션 구조로 번역한다.
- `mcp__xcelium-mcp__*` 24개 tool의 부여 범위를 Plan §8 Next Steps #3이 예고한 3-option 비교로 확정한다(Checkpoint 3).
- 7개 위임 매핑표 상황 각각에 대한 Task() 호출 패턴을 확정한다 — 그중 TB 행(`verilog-tb-analyst`)은 이미 그쪽 Design v0.5에서 계약이 확정되어 있으므로 **그대로 재사용**하고, 나머지 5개 상황(analyst/coder/reviewer/architect-advisor/prover)의 호출 패턴을 이 문서에서 새로 정의한다.
- Phase 2~4 방법론 비내장 원칙(Plan FR-04)을 실제 "0. 기준" 절 구조로 구현한다.
- **(v0.2 신설, Plan FR-10)** 분석서 staleness 체크(phase-0-discovery.md §0C hash 비교)를 Phase 2 진입보다 먼저 강제하고, `verilog-tb-analyst`로의 위임 시 그 hash(`tb_provenance`)를 실제로 전달하는 경로를 확정한다 — `verilog-tb-analyst.design.md` §4.1의 FR-14(수신측)와 반드시 짝을 이뤄야 완결되는 요구사항.

### 1.2 Design Principles

- **방법론 비내장** (Plan §정합성 유지 "방법론 출처") — Phase 2~4 절차를 system prompt에 복사하지 않고 `~/.claude/skills/xcelium-sim/references/phase-2~5*.md`를 런타임 Read.
- **fallback 영속성** (Plan §정합성 유지 "소비 측 배포 상태") — 이 agent가 완성돼도 xcelium-sim skill의 "agent 없으면 Claude가 직접 수행" fallback 문구는 유지 대상, 이 agent는 그 위의 우선 경로일 뿐.
- **최소 권한, 단 실행 중단 위험보다 우선순위 낮음** — Plan Risk 표가 "tool 목록 비대화"를 우려하지만, Checkpoint 3에서 라이브 디버깅 루프 중단 위험이 더 크다고 판단해 Option C 채택(§2.0).

---

## 2. Architecture Options

### 2.0 Architecture Comparison — `mcp__xcelium-mcp__*` 부여 범위

Plan §8 Next Steps #3이 예고한 3-option 비교. tool-map.md 기준 전체 24개는 7개 그룹(Sim Lifecycle 10 / Batch 2 / Signal Inspection 2 / Debug 4 / Checkpoint 1 / Waveform 2 / SimVision 3)으로 나뉜다.

| Criteria | Option A: 24개 전량 부여(무규율) | Option B: 최소 부여(14개, Sim Lifecycle 제외) | Option C: 전량 부여 + 문서화된 사용 규율 |
|----------|:-:|:-:|:-:|
| **Tool 개수** | 24 | 14 | 24 |
| **누락 위험** | 없음 | **있음** — 디버깅 도중 lifecycle tool(`mcp_config` 등) 필요 시 중단 | 없음 |
| **Tool 목록 비대화** (Plan Risk) | 완화 안 됨 | 완화됨 | system prompt 사용 규율로 완화 |
| **구현 복잡도** | 낮음 | 낮음 | 중간(사용 규율 문서 작성 필요) |
| **Phase 0(setup) 책임 경계** | 불명확 | 명확(호출자 책임 가정) — 단, 그 가정이 항상 맞지는 않음(재설치·재현 세션 등) | 명확 + 예외 상황도 이 agent가 커버 가능 |
| **Recommendation** | — | 정밀도 우선, 재현성 낮은 위험 감수 시 | **기본 선택** |

**Selected**: **Option C — 전량 부여 + 문서화된 사용 규율**
**Rationale**: Option B는 "Phase 0 setup은 호출자가 이미 처리했다"는 가정에 의존하는데, 실제 디버깅 세션에서는 이 가정이 항상 성립하지 않는다(예: 세션 재시작 후 `sim_discover` 캐시 만료, `mcp_config` 재확인 필요). 라이브 디버깅 루프 중간에 tool이 없어 막히는 것은 "tool 목록이 좀 길다"는 문제보다 명백히 더 심각하다. 따라서 24개 전량을 부여하되, system prompt에 "이 agent가 실제로 자주 쓰는 그룹(Batch/Signal/Debug/Checkpoint/Waveform)"과 "이미 호출자가 처리했을 가능성이 높아 재호출 전 확인부터 하는 그룹(Sim Lifecycle)"을 문서화해 행동을 규율한다 — Plan Risk 표의 "미사용 그룹 있으면 Design 단계에서 축소 검토"는 이 문서화로 충족한다(tool 자체를 빼지 않고, 사용 우선순위로 정리).

### 2.1 "0. 기준" 절차 (Component Diagram 대체)

> **v0.2 갱신(Plan FR-10)**: v0.1까지는 phase-2~5만 MUST였다 — 실제 실행(venezia-fpga T-002)에서 이 순서 때문에 기존 분석서를 hash 검증 없이 그대로 신뢰하고 Phase 2로 직행하는 실패 모드가 확인됐다. `phase-0-discovery.md`(§0C staleness 정의)를 **phase-2보다 먼저 읽는 MUST**로 추가한다 — 순서 자체가 핵심(§0C 비교를 먼저 해야 Phase 2 진입 여부·분석서 신뢰 여부를 올바르게 판단 가능).

```
0. 기준 — 시작 시 반드시 로드 (순서 중요)
┌──────────────────────────────────────────────────────────────────┐
│ 0) ~/.claude/skills/xcelium-sim/references/phase-0-discovery.md   │  ← (v0.2 신설) MUST, §0C
│    staleness(hash 비교) 정의 — phase-2보다 먼저 Read              │
├──────────────────────────────────────────────────────────────────┤
│ 1) ~/.claude/skills/xcelium-sim/references/phase-2-simulation.md  │  ← Phase 2(시뮬레이션 실행) 정본, MUST│
│ 2) ~/.claude/skills/xcelium-sim/references/phase-3-triage.md      │  ← Phase 3(로그 1차 판별) 정본, MUST │
│ 3) ~/.claude/skills/xcelium-sim/references/phase-4-waveform.md    │  ← Phase 4(CSV/FSM/bisect) 정본, MUST│
│ 4) ~/.claude/skills/xcelium-sim/references/phase-5-fix-regression.md│← Phase 5 위임 지점 확인용(§2.2), Read│
└──────────────────────────────────────────────────────────────────┘
```

> 5개 파일 모두 로컬(`~/.claude/skills/**`)이며 이미 배포 완료 확인됨(Plan §5 Risk, 2026-07-03 재확인 — 82/35/110/88줄 실내용, phase-4/5엔 이 agent 위임 지점까지 선반영; `phase-0-discovery.md`는 `verilog-tb-analyst`의 "0. 기준" §1과 동일 파일, 이미 배포됨). `verilog-tb-analyst`의 "0. 기준"과 원칙은 동일 — 재서술 금지, 런타임 Read.

### 2.2 위임 매핑표 → Task() 호출 패턴 (Delegation Flow 대체)

Plan §정합성 유지의 7개 상황을 실제 호출 패턴으로 번역한다.

| # | 상황 | 대상 | 호출 패턴 |
|---|---|---|---|
| 1 | `.ai/analysis/{module}.analysis.md` 부재/stale | `verilog-rtl-analyst` | `Task(subagent_type="verilog-rtl-analyst", prompt="{module} 분석서 {부재\|stale} — 작성/갱신 요청. 대상: {module_path}")` |
| 2 | `.ai/analysis/tb_{env}_*.analysis.md` 부재/stale | `verilog-tb-analyst` | **`verilog-tb-analyst.design.md` §4.1 계약 그대로 재사용(v0.5부터 6개 파라미터)**: `Task(subagent_type="verilog-tb-analyst", prompt="env={env}, target_type={component\|test}, target_name={name}, target_paths=[...], reason={missing\|stale}, tb_provenance={이번 실행의 sim_batch_run/sim_regression/sim_bridge_run 반환값}")`. **(v0.2 신설, Plan FR-10)** `tb_provenance`는 이 agent만 계산 가능(sim tool 접근권 보유) — 값이 있으면 항상 전달, 없으면(아직 sim을 안 돌린 상태 등) `null`을 명시적으로 전달(생략 아님). 미배포 시 이 agent 자신이 phase-0-discovery.md를 Read해 §0A/0B 직접 수행(FR-09 fallback) |
| 3 | 근본 원인 확정 → RTL 수정 | `verilog-rtl-coder` | `Task(subagent_type="verilog-rtl-coder", prompt="근본 원인: {hypothesis}. 수정 대상: {file}:{line}. 분석서: {analysis_path}")` |
| 4 | 수정 커밋 전 리뷰 | `verilog-rtl-reviewer` | `Task(subagent_type="verilog-rtl-reviewer", prompt="{coder가 만든 diff} AI-failure 패턴 리뷰 요청")` |
| 5 | 아키텍처 경계 판단 (신규 FSM/모듈) | `verilog-rtl-architect-advisor` | `Task(subagent_type="verilog-rtl-architect-advisor", prompt="{제안된 수정}이 아키텍처 경계를 넘는지 판단 요청")` |
| 6 | self-contained 로직/타이밍 증명 | `verilog-rtl-prover` | `Task(subagent_type="verilog-rtl-prover", prompt="{claim} 형식 증명 요청 — sby 대상: {module}")` |
| 7 | Verilog-A/AMS 디버깅 | (직접 수행) | Task() 없음 — `verilog-a` skill 참조하여 이 agent가 직접 |

```
xcelium-sim skill (Phase 2~4 루프 중 판단 지점)
       │
       ▼
verilog-rtl-debugger (이 agent, "0. 기준" 정본 Read 완료 상태)
       │
       ├─ 분석서 부재/stale? ──► Task(verilog-rtl-analyst / verilog-tb-analyst)
       ├─ 근본원인 확정? ──────► Task(verilog-rtl-coder) → Task(verilog-rtl-reviewer)
       ├─ 아키텍처 경계? ──────► Task(verilog-rtl-architect-advisor)
       ├─ formal 증명 필요? ───► Task(verilog-rtl-prover)
       └─ AMS/Verilog-A? ─────► 직접 수행 (verilog-a skill 참조)
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| "0. 기준" (필수, v0.2부터 phase-2보다 우선) | `~/.claude/skills/xcelium-sim/references/phase-0-discovery.md` §0C (로컬) | 분석서 staleness(hash 비교) 정의 — Plan FR-10 |
| "0. 기준" (필수) | `~/.claude/skills/xcelium-sim/references/{phase-2,3,4,5}*.md` (로컬) | Phase 2~4 방법론 정본, Phase 5 위임 지점 확인 |
| Task 대상 6개 | `verilog-rtl-analyst`/`coder`/`reviewer`/`architect-advisor`/`prover`(기존 5개, 무수정) + `verilog-tb-analyst`(신설, 별도 PDCA) | 위임 매핑표 실행 |
| MCP tool 24개 | `mcp__xcelium-mcp__*`(Option C, 전량) | Phase 2~4 직접 수행 |

---

## 3. Frontmatter 설계 (Data Model 대체)

이 feature의 "데이터 모델"은 agent 정의 파일의 frontmatter 구조다.

| 필드 | 값 |
|---|---|
| `name` | `verilog-rtl-debugger` |
| `tools` | `mcp__xcelium-mcp__*`(24개, §2.0 Option C) + `Read, Glob, Grep`(RTL/분석서 참조, Write/Edit 없음 — FR-02) + `Task`(6개 agent 위임) |
| `model` | Do 단계에서 결정(기존 5개 agent의 model 선택 기준과 대조 — Plan §4.1 Definition of Done) |
| `description` | Use it when / Do NOT use for / Triggers 구조(FR-01), Triggers는 FR-07 라이브-디버깅 특화 키워드로 한정 |

> **N/A**: §3.2/§3.3 Entity/DB Schema — 이 feature는 데이터베이스를 다루지 않음.

---

## 4. Task() 위임 계약 (API Specification 대체)

### 4.1 6개 위임 대상별 계약 상태

| 대상 | 계약 상태 | 근거 |
|---|:---:|---|
| `verilog-tb-analyst` | **확정** (재사용) | `verilog-tb-analyst.design.md` §4.1 — **v0.5부터 6개 파라미터**(env/target_type/target_name/target_paths/reason/`tb_provenance`), 호스트 관련 필드 없음(tool 가용성 기반 자동 분기, §4.1a) |
| `verilog-rtl-analyst` | 이번 문서에서 확정 | §2.2 #1 패턴 — 기존 agent, 이 agent가 처음으로 Task() 호출하는 소비자가 됨(기존엔 사람이 직접 호출) |
| `verilog-rtl-coder` | 이번 문서에서 확정 | §2.2 #3 패턴 |
| `verilog-rtl-reviewer` | 이번 문서에서 확정 | §2.2 #4 패턴 |
| `verilog-rtl-architect-advisor` | 이번 문서에서 확정 | §2.2 #5 패턴 |
| `verilog-rtl-prover` | 이번 문서에서 확정 | §2.2 #6 패턴 |

### 4.2 공통 규칙

- 모든 Task() 호출은 **prompt 안에 대상 파일 경로·근본 원인 가설·분석서 경로를 명시**한다 — 대상 agent가 이 agent의 세션 컨텍스트를 공유하지 않으므로(Claude Code Agent 격리 원칙), 필요한 정보를 전부 prompt에 담아야 함.
- `verilog-tb-analyst` 호출 시 **HANDS OFF 원칙**(그쪽 Design §3)과 동일하게, 이 agent도 위임 대상이 `.ai/analysis/**` 또는 지정 수정 대상 외 건드리지 않았는지 결과를 받은 뒤 확인.
- 분석서 부재 BLOCKER(analyst/tb-analyst 공통 패턴) 없이 Phase 4 FSM 대조로 진행하지 않는다(Plan FR-05/FR-09).
- **(v0.2 신설, Plan FR-10) staleness 정의**: 분석서(`.ai/analysis/{module}.analysis.md`, `.ai/analysis/tb_*.analysis.md`) **존재 ≠ fresh**. `tb_source`/`tb_provenance`의 `combined_sha256`이 이번 실행에서 sim tool이 반환한 hash와 **불일치**하거나, 애초에 헤더에 **기록 자체가 없으면** stale로 간주하고 §2 #1/#2(analyst/tb-analyst) 위임을 트리거한다(phase-0-discovery.md §0C 원문 그대로). 이 비교는 "0. 기준" §0(§2.1) Read 직후, Phase 2 진입 **이전**에 수행한다.

### 4.3 에러 처리 (Error Handling 대체)

| 상황 | 처리 |
|---|---|
| `~/.claude/skills/xcelium-sim/references/phase-{2,3,4}*.md` 부재 | BLOCKER — 방법론 임시 내장 없이 명시적 중단(Plan §정합성 유지 원칙). 단, Plan §5 Risk에서 이미 배포 확인됨(2026-07-03) |
| Task() 위임 대상 agent가 설치돼 있지 않음(`verilog-tb-analyst` 미배포 등) | `verilog-tb-analyst`는 FR-09 fallback(이 agent 자신이 직접 수행) 적용. 나머지 5개(analyst 등)는 기존에도 항상 존재하는 agent라 이 경로 해당 없음 |
| MCP tool 호출 실패(시뮬레이터 연결 끊김 등) | xcelium-sim skill의 각 phase reference에 정의된 재시도/에러 처리를 그대로 따름(이 agent가 별도 재정의하지 않음 — 방법론 비내장 원칙) |

> **N/A**: §7 Security Considerations — 외부 입력·인증 표면 없음. HANDS OFF에 준하는 유일한 안전장치는 Write/Edit tool을 아예 부여하지 않는 것(§3) — RTL 수정은 반드시 `verilog-rtl-coder` 위임을 거침.

### 4.4 Manifest 형식 (v0.2 신설, Plan FR-10)

> v0.1엔 Manifest 절이 없었다 — 배포된 agent 파일(`agents/verilog-rtl-debugger.md` 하단)엔 이미 자유서술 형태로 존재했으나 이 Design 문서가 그 구조를 정의한 적이 없었던 문서화 공백. Plan FR-10이 "staleness 체크 수행 여부/결과" 필드를 필수 보고 항목으로 못박으면서 이 기회에 Design에도 명문화한다 — 배포본과 동일한 자유서술 5항목 구조를 그대로 표로 옮기고 신규 항목만 추가(재작성 아님).

| 필드 | 설명 |
|---|---|
| 수행 Phase | 이번 실행에서 수행한 Phase(2~4 중 어디까지) 및 로드한 정본 목록 |
| 위임 내역 | 위임한 agent 목록(§2 상황 번호 + Task() 호출 대상) 및 각 위임의 결과 요약 |
| tb-analyst fallback 여부 | `verilog-tb-analyst` 미배포로 fallback 경로를 탄 경우 그 사실 명시 |
| **staleness 체크 결과** | **(v0.2 신설)** "0. 기준" §0 Read 후 수행한 hash 비교 결과 — 대상 분석서별 fresh/stale 판정 + stale이면 어느 위임(§2 #1/#2)이 트리거됐는지, `tb_provenance` 전달 여부 |
| 실행 MCP tool | 실행한 MCP tool 목록("확인 후 사용" 그룹 호출 시 사유 포함) |
| 미해결 BLOCKER | 정본 부재, MCP 연결 실패, 위임 대상 agent 부재 등 |

---

## 5. Test Plan (검증 계획)

Plan §4.1 Definition of Done을 실행 가능한 시나리오로 구체화. `verilog-tb-analyst`와 동일하게 수동 시나리오 검증으로 대체.

| # | 시나리오 | 절차 | 성공 기준 |
|---|---|---|---|
| 1 | Phase 2~4 자율 루프 | 실제 실패 테스트(TOP01x 등)로 시뮬레이션 실행 → bisect → FSM 대조 요청 | phase-2~4 reference를 Read해 절차 수행, 다른 agent 호출 없이 완주 |
| 2 | RTL 분석서 위임 | 분석서 없는 모듈로 디버깅 요청 | `verilog-rtl-analyst`에 Task() 위임, 분석서 생성 후 FSM 대조로 진행(BLOCKER 없이) |
| 3 | TB 분석서 위임, `tb_provenance` 전달 검증 | TB 분석서 없는 테스트로 디버깅 요청 | `verilog-tb-analyst`에 §4.1 계약대로 위임(env/target_type/target_name/target_paths/reason/**`tb_provenance`** 6개), **v0.2**: sim tool 반환값에서 계산한 hash가 실제로 6번째 파라미터에 담겨 전달됨(Manifest §4.4로 확인), `verilog-tb-analyst` 미배포 시 이 agent가 직접 §0A/0B 수행 |
| 3b | staleness 체크 우선순위 검증 | 헤더에 hash가 기록된 기존 분석서 대상으로 재실행, 이번 sim 결과의 hash와 **일부러 불일치**시킴 | **(v0.2 신설, Plan FR-10)** "0. 기준" §0(phase-0-discovery.md) Read가 phase-2 진입보다 먼저 일어나고, hash 불일치를 감지해 Phase 2 직행 없이 §2 #1/#2 위임(analyst/tb-analyst)이 먼저 트리거됨. Manifest `staleness 체크 결과` 필드에 판정 근거 기록 |
| 4 | 수정→리뷰 체인 | 근본 원인 확정 후 요청 | `verilog-rtl-coder`→`verilog-rtl-reviewer` 순서로 Task() 위임, 중간 결과가 prompt에 올바르게 전달됨 |
| 5 | 아키텍처 경계 판단 위임 | 신규 FSM 필요한 규모의 수정 요청 | `verilog-rtl-architect-advisor` 위임, 판단 전 코드 수정 시도하지 않음 |
| 6 | formal 증명 위임 | self-contained 타이밍 클레임 발생 | `verilog-rtl-prover` 위임 |
| 7 | AMS 직접 수행 | Verilog-A 컴포넌트 디버깅 요청 | Task() 호출 없이 `verilog-a` skill 참조해 직접 수행 |
| 8 | Tool 사용 규율 검증(§2.0 Option C) | Phase 2~4 루프 실행 중 tool 호출 로그 확인 | Sim Lifecycle 그룹 tool은 "이미 처리됐는지 확인 후" 호출하는 패턴을 실제로 따르는지(불필요한 재호출 없음) |

> venezia-fpga 세션 수동 검증(Plan §4.1 4번째 항목)은 시나리오 1~4를 실제 프로젝트 데이터로 재현하는 것으로 충족.

---

## 6. Implementation Guide

### 6.1 File Structure

```
agents/
└── verilog-rtl-debugger.md   (신규 파일 1개)

install.py                     (AGENTS 목록에 1줄 추가)
```

> **N/A**: §9 Clean Architecture, §10 Coding Convention Reference — markdown agent 정의 파일에는 해당 없음.

### 6.2 Implementation Order

> **v0.2 갱신 범위**: 1~6은 최초 구현(2026-07-06 완료, `agents/verilog-rtl-debugger.md` 배포됨) 기준. gap-detector 재검증(2026-07-08) 결과 Match Rate 85% — FR-10 4개 하위항목(a~d)이 전부 미반영으로 확인됐다. **v0.2에서 실제로 손대야 할 항목은 2번(phase-0-discovery.md MUST 추가)과 3번(staleness 정의 명문화 + tb_provenance 파라미터 + Manifest 필드)뿐** — 1/4/5/6은 변경 없음.

1. [x] Frontmatter 작성(§3) — `verilog-rtl-analyst.md` 등 기존 5개와 동일 스타일, `tools:`에 MCP 24개 + Read/Glob/Grep + Task — FR-01/FR-02, 완료·변경 없음
2. [ ] **"0. 기준" 절 수정**(§2.1, v0.2) — `phase-0-discovery.md`를 phase-2보다 먼저 읽는 MUST로 추가 — FR-10(a) (**Do 재진입 대상**)
3. [ ] **위임 매핑표·공통규칙·Manifest 수정**(§2.2 #2, §4.2, §4.4) — staleness 정의(hash 불일치/미기록) 명문화 + `tb_provenance` 6번째 파라미터 + Manifest "staleness 체크 결과" 필드 — FR-10(b)(c)(d) (**Do 재진입 대상, `verilog-tb-analyst.plan.md` FR-14와 동시 반영 필수**)
4. [x] Tool 사용 규율 문서화(§2.0 Option C) — "자주 쓰는 그룹 vs Phase 0 처리 확인 후 호출" 구분, 완료·변경 없음
5. [x] Trigger 키워드 작성 — 기존 5개와 비충돌 — FR-07, 완료·변경 없음
6. [x] `install.py` AGENTS 목록 등록 — FR-08, 완료·변경 없음
7. [ ] §5 Test Plan 시나리오 3(tb_provenance 전달)·3b(staleness 우선순위)로 자체 점검 후 `install.py --only agents` 재배포

### 6.3 Session Guide

| Session | Phase | Scope | Turns |
|---------|-------|-------|:-----:|
| Session 1 | Design (v0.1) | 전체 | 완료 |
| Session 2 | Do | `agents/verilog-rtl-debugger.md` 전체 작성 + install.py 등록 | 완료(2026-07-06) |
| Session 3 | Check | gap 분석 — Match Rate 85%(Plan v0.8 기준), FR-10 4개 하위항목 미반영 확인 | 완료(2026-07-08) |
| Session 4 (현재) | Design (v0.2) | §2.1 phase-0-discovery.md MUST 추가 + §4 FR-10 계약 반영 + §4.4 Manifest 신설 | 완료 |
| Session 5 | Do (재진입) | §6.2 항목 2/3만 수정 — `verilog-tb-analyst.plan.md` FR-14와 동시 진행 | 15-20 |
| Session 6 | Check + Report | §5 시나리오 3/3b 재검증 + gap 재분석 | 15-20 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-06 | 초안 — Checkpoint 3에서 Option C(24개 전량 부여 + 문서화된 사용 규율) 채택. Plan §7.2 미정 항목이었던 6개 agent Task() 위임 패턴을 확정(TB 행은 `verilog-tb-analyst.design.md` 계약 재사용, 나머지 5개는 신규 정의). 템플릿 웹앱 전용 섹션 N/A 처리 | HSLEE |
| 0.2 | 2026-07-08 | **Plan v0.8(FR-10 staleness 체크) 반영 — gap-detector 재검증 후 Design 갱신**: 2026-07-08 재검증에서 Match Rate 85% 확인, FR-10 (a)~(d) 4개 하위항목이 배포된 agent 파일에 전혀 반영되지 않았음을 확인(`verilog-tb-analyst` 쪽 FR-14 미반영과 쌍을 이루는 결함 — 값을 보낼 경로도, 받을 경로도 없던 상태). **§1.1** Design Goals에 FR-10 목표 추가. **§2.1** "0. 기준"에 `phase-0-discovery.md`를 phase-2보다 먼저 읽는 MUST로 추가(순서가 핵심). **§2.2** #2(tb-analyst) Task() 패턴에 6번째 파라미터 `tb_provenance` 추가(값 없으면 null 명시 전달, 생략 아님). **§2.3** Dependencies에 phase-0-discovery.md 행 추가. **§4.1** tb-analyst 계약 상태를 "5개→6개 파라미터"로 갱신. **§4.2** 공통 규칙에 staleness 정의(hash 불일치 또는 미기록 시 stale, phase-0-discovery.md §0C 원문) 신설. **§4.4 Manifest 형식 신설** — v0.1엔 이 섹션 자체가 없었고 배포본에만 자유서술로 존재하던 문서화 공백을 이번에 메움, 기존 5항목 표로 옮기고 "staleness 체크 결과" 필드만 신규 추가(재작성 아님). **§5** 시나리오 3(tb_provenance 전달)에 조건 추가, 신규 시나리오 3b(staleness 우선순위) 추가. **§6.2/§6.3** 완료/재작업 항목 구분, 실제 세션 이력 반영. `verilog-tb-analyst.plan.md` FR-14 및 그 Design v0.5와 동시 반영 필수 — 한쪽만 고치면 값을 보내도 못 씀 | HSLEE |
