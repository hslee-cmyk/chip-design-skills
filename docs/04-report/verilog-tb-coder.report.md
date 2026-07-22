# verilog-tb-coder Completion Report

> **Status**: Complete (with deferred operational verification)
>
> **Project**: chip-design-skills
> **Version**: 0.6 (Plan) / 0.1 (Design) / 0.1 (Analysis)
> **Author**: HSLEE
> **Completion Date**: 2026-07-22
> **PDCA Cycle**: #1 (Plan → Design → Do → Check, single-feature completion)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**(`agents/verilog-tb-coder.md`)를 
> 만드는 작업이다. 템플릿의 API/Data Model/Performance/Test Coverage/CI-CD 섹션은 N/A 처리했다 
> (`verilog-tb-architect-advisor.report.md` 선례와 동일 패턴).

---

## Executive Summary

### 1.1 Project Overview

| Item | Content |
|------|---------|
| Feature | verilog-tb-coder (TB-side constrained implementer agent) |
| Start Date | 2026-07-10 (Plan phase began) |
| End Date | 2026-07-22 (Do/Check/Report completed) |
| Duration | Planning 2.5 일 (v0.1→v0.6) + Implementation 1 일 (Design→Do→Check→Report same session) |

### 1.2 Results Summary

```
┌─────────────────────────────────────────────┐
│  Match Rate: 99.2% (first pass)             │
│  Target: ≥ 90%                              │
├─────────────────────────────────────────────┤
│  ✅ Complete:     Agent 파일 + 기본 검증    │
│  ⏳ Deferred:     실제 배포, 수동 시나리오   │
│  ⏸️ Dependency Gap: verilog-tb-reviewer    │
│                 (reviewer 아직 Plan 단계)   │
└─────────────────────────────────────────────┘
```

### 1.3 Value Delivered

| Perspective | Content |
|-------------|---------|
| **Problem** | xcelium-mcp Fix Sub-cycle에서 근본원인이 TB로 판정되는 경우가 실제로 발생하는데(v1.33에서 확인), TB 전담 구현 agent가 없었다 — `verilog-rtl-coder`는 RTL 전용으로 설계되어 있고, 일반적인 TB 코딩(새 testcase, scenario 보강 등) 수요도 별도로 존재한다(workflow-v2와 무관). 이 둘을 별도 "모드"로 이원화하려는 시도(Plan v0.3)가 벤치마크(`verilog-rtl-coder`)의 실제 설계와 맞지 않아 철회되었으며(v0.4), 단일 균일 규율이 필요했다. |
| **Solution** | `verilog-rtl-coder`와 정확히 대칭되는 TB 전용 constrained implementer `verilog-tb-coder` 신설. formal 파라미터 스키마 없이(자유 형식 Task 프롬프트), 호출 맥락(workflow-v2 vs 일반 요청)과 무관하게 단일 균일 규율을 적용 — spec 정당화 self-check(1차 필터) + STOP-and-Ask 조건(구조 변경은 `verilog-tb-architect-advisor`로 route) + 항상 `verilog-tb-reviewer`에게 독립 검토 인계(호출 맥락 무관). |
| **Function/UX Effect** | `fix_target=tb` 경로에서든, 일반 TB 코딩 요청에서든 동일한 처리 흐름으로 작동 — 명시된 스코프 내 수정 → spec 근거 1차 검증 → 구조 변경 감지 시 architect-advisor로 route → 항상 reviewer에게 인계. 구조 결정은 `verilog-tb-architect-advisor`가, 정확성 판단은 `verilog-tb-reviewer`가 담당하므로, coder는 "spec 근거 있는 범위 안에서만 구현"이라는 좁고 명확한 역할만 수행. |
| **Core Value** | Fix Sub-cycle 중 TB 버그 경로가 RTL 버그 경로와 대칭적으로 처리되어, 근본원인 정위치(TB vs RTL) 오류를 줄이고 anti-tautology(TB로 RTL 버그를 숨기는 위험)를 2단 방어(self-check + reviewer) 로 방어한다. |

---

## 1.4 Success Criteria Final Status

> Plan §5 에서.

| # | Criteria | Status | Evidence |
|---|----------|:------:|----------|
| SC-1 | 스코프 내 변경만, 근거 불충분 시 STOP-and-Ask | ✅ Met | `agents/verilog-tb-coder.md` §2/§3/§4 (L62-116) |
| SC-2 | anti-tautology — self-check은 1차 필터, `verilog-tb-reviewer` 항상 인계(호출 맥락 무관) | ✅ Met | §0/§3/§5 4곳에서 반복 강조 (L38-41, L93, L104, L130) |
| SC-3 | 구조적 변경 감지 시 `verilog-tb-architect-advisor`로 route(사람 직접 아님) | ✅ Met | §4(c) (L114), 양방향 참조 확인 |
| SC-4 | "Fix 모드/General 모드" 이원화 부재 | ✅ Met | §0/§8에서 명시적 부재 서술 (L65-66, L163-164) |

**Success Rate**: 4/4 criteria met (100%)

## 1.5 Decision Record Summary

| Source | Decision | Followed? | Outcome |
|--------|----------|:---------:|---------|
| [Plan v0.4] | formal 파라미터 스키마 없음, 자유 형식 프롬프트 + 단일 균일 규율 | ✅ | Do에서 구현, Analysis에서 확인 |
| [Plan v0.5] | FR-08(c) "구조적 변경" → 사람 직접 아닌 verilog-tb-architect-advisor로 route | ✅ | Agent §4(c) 정확히 반영 (L114) |
| [Design §4.2] | spec 위치 확인 3단계 순서(CLAUDE.md → .ai/spec/ → .ai/analysis/tb_*) | ✅ | §3 L96-99 일치 |
| [Design §4.3] | STOP-and-Ask 구체 5가지 예시(a~e) + (c)는 architect-advisor 명시 | ✅ | §4 표(L110-116) 설계와 100% 일치 |

---

## 2. Related Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | [verilog-tb-coder.plan.md](../01-plan/features/verilog-tb-coder.plan.md) (v0.6) | ✅ Finalized |
| Design | [verilog-tb-coder.design.md](../02-design/features/verilog-tb-coder.design.md) (v0.1) | ✅ Finalized |
| Check | [verilog-tb-coder.analysis.md](../03-analysis/verilog-tb-coder.analysis.md) | ✅ Complete (99.2%, zero Critical/Important) |
| Report | 현재 문서 | ✅ Complete |

### Related Artifacts

| Item | Type | Location | Status |
|------|------|----------|--------|
| Agent 정의 파일 | 신규 | `agents/verilog-tb-coder.md` | ✅ Complete |
| 배포 산출물 | 예정 | `~/.claude/agents/verilog-tb-coder.md` (dry-run 확인만) | ⏳ Deferred |
| Sibling Route Updates | 수정 | `verilog-tb-architect-advisor.plan.md` v0.5 | ✅ Complete |

---

## 3. Completed Items

### 3.1 Functional Requirements (Agent File)

| ID | Requirement | Status | Evidence |
|----|-------------|:------:|----------|
| FR-01 | Frontmatter(name/description/triggers/tools/model) — `verilog-rtl-coder.md` 벤치마크 | ✅ | L1-24 |
| FR-02 | Tool 목록: Read/Write/Edit/Glob/Grep/Bash + mcp__ssh__*(4종) — 로컬/원격 TB 모두 대응 | ✅ | L22 |
| FR-03 | "0. 기준" — `verilog-rtl`/`chip-verification`/`uvm-verification` 전체 Read(조건부 ssh-mcp) | ✅ | L48-56 |
| FR-04 | ssh-mcp SKILL 조건부 로드 — `mcp__ssh__*` 가용 시에만 | ✅ | L55-56 |
| FR-05 | Task() 호출 규약 — formal 스키마 없음, 자유 형식 + 3요소(스코프/근거/대상) 권장 | ✅ | §2 (L62-89), 예시 2개 |
| FR-06 | spec 정당화 self-check — 순환 논리 감지, 1차 필터임을 명시 | ✅ | §3 (L93-104) |
| FR-07 | `.ai/analysis/tb_*.analysis.md` 확인 — 부재/stale 시 tb-analyst로 라우팅 | ✅ | L57-58 |
| FR-08 | STOP-and-Ask 조건 5가지 + (c)는 tb-architect-advisor로 route | ✅ | §4 표 (L110-116) |
| FR-09 | HANDS OFF — RTL/분석서 무수정, 분석서 갱신은 위임 | ✅ | §7 (L145-150) |
| FR-10 | Definition of Done — 스코프 내/self-check/구문 오류 없음/분석서 갱신 위임/reviewer 항상 요청 | ✅ | §5 (L123-130) |
| FR-11 | Handoff — 변경 파일/근거/escalation/위임 여부/reviewer 요청/verify 안내 | ✅ | §6 (L134-141) |
| FR-12 | `install.py` 등록 — glob 자동 인식 확인 (dry-run만) | ⚠️ Partial | Dry-run 확인 완료, 실제 배포는 deferred |

**Completion Rate**: 11/12 complete, 1 partial (배포는 다음 단계)

### 3.2 Non-Functional Requirements

| Category | Criteria | Status | Evidence |
|----------|----------|:------:|----------|
| Anti-tautology 준수 | self-check이 1차 필터이고 reviewer가 항상 최종 판단 — 호출 맥락 무관 | ✅ | §0 L38-41, §3 L104, §5 L130 |
| 컨벤션 일관성 | `verilog-rtl-coder` 구조(formal 파라미터 없음) + `verilog-tb-analyst` "0. 기준" 재사용 | ✅ | §0~§1 구조 동일, "0. 기준" L48-56 |
| Cross-repo 정합성 | xcelium-mcp v1.34 `fix_target=tb` 경로와 Task 호출 규약 일치 | ✅ | §2 자유 형식 프롬프트, Plan v0.6 정정 반영 |

### 3.3 Final Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Agent 정의 파일 | `agents/verilog-tb-coder.md` | ✅ Complete |
| 배포 확인 | `install.py --only agents --dry-run` | ⚠️ Partial |

---

## 4. Incomplete/Carried-Over Items

### 4.1 Real Remaining Work (Not Hypothetical)

| Item | Reason | Priority | Estimated Effort | Target |
|------|--------|----------|------------------|--------|
| Actual deployment via `install.py --only agents` | 실제 배포만 미완료 (dry-run 인식은 확인) | High | 15분 | 다음 세션 / 실제 사용 전 |
| Design §6 Manual Test Scenarios (7 scenarios) | 의도적 순환논리(fix-plan 경유/사용자 직접)/구조변경 route/정상 edit/spec 위치 fallback/스코프 확장 필요/분석서 부재 시나리오 실행 안 함 | High | 2~3시간 (live invocation) | QA phase 또는 첫 실사용 |

### 4.2 Dependency Gap (Real External Blocker)

| Item | Status | Impact | Mitigation |
|------|--------|--------|-----------|
| `verilog-tb-reviewer` (anti-tautology 최종 판단 agent) | Plan 단계(2026-07-10 이후 idle, 미작성) | 이 agent의 "항상 reviewer에게 인계" 절차가 실시간 agent로 라우팅되지 못하고, 사람의 수동 검토로 fallback됨 | reviewer가 Build되기 전까지는 구조적으로 문제 아님 — coder→reviewer 라우팅 경로가 모두 설계되었고, 배포 후 실사용 시에 reviewer 구현이 되면 자동으로 연결됨. reviewer.plan.md는 이미 작성됨. |

---

## 5. Quality Metrics

### 5.1 Final Analysis Results (Gap-Detector)

| Metric | Target | Final | Status |
|--------|--------|-------|--------|
| Structural Match Rate | 90% | 98% | ✅ Exceed |
| Functional Match Rate | 90% | 99% | ✅ Exceed |
| Contract/Consistency Match | 90% | 100% | ✅ Exceed |
| **Overall Match Rate** | **90%** | **99.2%** | **✅ Exceed (first pass)** |

**Formula (static-only, markdown agent)**: (Structural×0.2) + (Functional×0.4) + (Contract×0.4)

### 5.2 No Iteration Required

정상적으로 첫 gap-detector 실행에서 99.2% 달성 → `/pdca iterate` 불필요 → 바로 report 단계로 진행.

### 5.3 Resolved Findings

| Priority | Finding | Resolution | Status |
|----------|---------|-----------|--------|
| 🟡 Minor | "0. 기준" 라벨(§0 기준 vs §1 Mandatory Setup 의 컨벤션 차이 | 기능 영향 없음 — verilog-rtl-coder.md의 "§1" 스타일 채택(verilog-tb-analyst의 "§0" 컨벤션과 다르지만 의미 동일) | ✅ Accept (설계 의도, 반복 금지) |
| 🟡 Minor | Plan FR-12 문구 vs 실제 install.py 메커니즘 불일치 | Plan v0.6에서 정정 완료(별도 AGENTS 목록 없고 glob 자동 인식) — 이미 반영됨 | ✅ Accept |

**Critical/Important Gaps**: 0개

---

## 6. Lessons Learned & Retrospective

### 6.1 What Went Well (Keep)

- **Plan v0.3에서의 "모드 이원화" 철회가 좋은 판단이었다**: 벤치마크(`verilog-rtl-coder`)를 직접 읽어서 실제 설계를 확인했고, "formal 파라미터 스키마 없음 + 자유 형식 프롬프트"라는 단순 원칙을 찾아냈다. 이를 통해 복잡한 이원화 구조를 피하고 `verilog-tb-architect-advisor`(동시 완성)와의 명확한 책임 분리를 달성했다.
- **Anti-tautology 원칙의 일관된 적용**: self-check을 "1차 필터"로 명시하고, reviewer 인계를 "무조건적"으로 설계하는 것이 처음부터 명확했다. 이는 "구현자가 자기 판단을 최종 승인한다"는 모순을 구조적으로 방어한다.
- **sibling agent(`verilog-tb-architect-advisor`)와의 동시 완성**: 구조 변경 감지 시 route 대상이 명확히 존재하므로, "사람에게 직접 escalate"라는 불명확한 상태가 없다.

### 6.2 What Needs Improvement (Problem)

- **수동 테스트 시나리오를 Design 단계에서는 정의했지만 실행하지 않았다**: 의도적으로 "QA 단계 또는 첫 실사용"으로 deferred했지만, 이로 인해 agent의 실제 동작을 검증한 사람이 없다는 위험을 남겼다. 특히 "순환 논리를 실제로 잡아내는가"를 고의로 테스트하지 못했다.
- **배포 테스트가 "dry-run 확인"에서 멈췄다**: install.py의 glob 메커니즘은 이해했지만, 실제 `~/.claude/agents/`에 파일이 생기는지 확인하지 않았다. "partial"과 "complete" 사이의 회색 영역을 남겼다.

### 6.3 What to Try Next (Try)

- Design 단계의 수동 시나리오를 Do 단계 끝에 최소한 2~3개 실행해 agent의 핵심 기능(순환 논리 감지, 구조 변경 route)을 검증한 후 Check로 진행.
- 배포 테스트를 "dry-run 확인" → "실제 설치" → "배포본 동작 확인"의 3단계로 명시적으로 분리하고, 각각을 Definition of Done 체크리스트 항목으로 포함.

---

## 7. Process Improvement Suggestions

### 7.1 PDCA Process

| Phase | Current | Improvement Suggestion |
|-------|---------|------------------------|
| Plan | 초안 후 여러 iteration(v0.1→v0.6)을 거쳤으나, 핵심 결정(v0.4 "모드 이원화 철회")은 벤치마크 재검증으로 비로소 확인됨 | Plan 단계에서 벤치마크 agent 파일을 먼저 전체 Read하는 "벤치마크 검증 gate" 추가 — 설계 이원화를 결정하기 전에 "기존 agent가 정말로 이원화되어 있는가"를 먼저 확인 |
| Design | 아키텍처 3안(A/B/C) 비교는 잘했으나, 실제 구현 후 "이 설계가 100% 반영됐는가"를 gap-detector 외에 별도 검증 안 함 | 설계→구현 후 "Key Design Decision Verification" 체크리스트(예: 스코프 확인 순서 3단계가 코드에 있는가, STOP-and-Ask 5가지 예시가 모두 반영되었는가) 추가 |
| Do | 구현 시 sibling 문서(`verilog-tb-architect-advisor.plan`) route 갱신을 To-Do로만 남김 | Definition of Done에 "sibling 문서 route 확인" 항목을 명시적으로 포함 — 이 feature가 다른 agent에 영향을 미친다는 사실을 do 단계에서 인지 |
| Check | gap-detector 실행으로 Match Rate 확인하지만, "설계 의도상 나중에 테스트하기로 한 시나리오"와 "놓친 시나리오"를 구분하지 않음 | Check 단계의 출력에 "Deferred Scenarios(설계 의도) vs Gap Findings(구현 누락)"을 명시적으로 구분 — "모두 완료되지 않았다"는 사실과 "무엇이 정상 흐름인지"를 사용자가 구분할 수 있도록 |

### 7.2 Agent Design Convention

| Area | Improvement Suggestion | Expected Benefit |
|------|------------------------|------------------|
| sibling agent 갱신 | agent A가 신설되어 agent B/C가 route할 때, 문서의 route 문구 일관성을 자동/수동 체크 목록화 | 이 report처럼 "실제로는 route가 구현됐는데 문서는 outdated"인 상황 방지 |
| 수동 시나리오 추적 | Design에서 "QA/실사용 단계에서 실행"으로 deferred한 시나리오를 DEFERRED_SCENARIOS.md로 명시적 추적 | 배포 후 누군가가 "이 agent는 언제 테스트되었는가"를 물었을 때, "이 7개 시나리오는 아직"이라고 명확히 답변 가능 |

---

## 8. Next Steps

### 8.1 Immediate (Before Operational Use)

- [ ] `install.py --only agents` 실제 배포 실행 (dry-run 아닌 실제 설치)
- [ ] `~/.claude/agents/verilog-tb-coder.md` 존재 확인
- [ ] Design §6 시나리오 최소 3개(순환 논리 fix-plan/사용자 요청, 구조 변경 route) 실행해 agent 동작 확인

### 8.2 First Operational Use

- [ ] xcelium-mcp workflow-v2에서 `fix_target=tb` 승인 후 이 agent가 정상적으로 호출되는지 확인
- [ ] Task 프롬프트에 "스코프/근거/대상"이 충분하지 않을 때 agent가 실제로 STOP-and-Ask하는지 확인
- [ ] 구조적 변경 의심 시 `verilog-tb-architect-advisor`로 실제로 route되는지 확인
- [ ] 완료 후 `verilog-tb-reviewer`로 인계가 정상 작동하는지 확인

### 8.3 `verilog-tb-reviewer` Dependency

- [ ] `verilog-tb-reviewer.plan.md`(이미 작성됨)에서 Plan 단계를 벗어나 실제 구현으로 진행
- [ ] reviewer 완성 후, 이 agent의 "항상 reviewer에게 인계" 절차가 실시간으로 작동하는지 검증
- [ ] workflow-v2 fix-review 게이트에 reviewer 라우팅이 제대로 연결되는지 확인

---

## 9. Changelog

### 2026-07-22 — Completion Session (Do → Check → Report)

**Added:**
- `agents/verilog-tb-coder.md` (frontmatter + 8개 섹션)
  - 권한경계(constrained role, anti-tautology, HANDS OFF)
  - Mandatory Setup(정본 skill 4개)
  - Task() 호출 규약(자유 형식, 예시 2개)
  - spec 정당화 self-check(1차 필터)
  - STOP-and-Ask 조건(5가지, (c)는 architect-advisor route)
  - Definition of Done / Handoff
  - 정직한 한계(자동 classifier 부재, tool 제한)

**Changed:**
- Plan v0.6 FR-12/§7.1 install.py 메커니즘 문구 정정(glob 자동 인식)
- `verilog-tb-architect-advisor.plan.md` v0.5에서 route 갱신 반영

**Fixed:**
- 없음 (99.2% 첫 패스 달성)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-22 | Completion report — Plan v0.6 + Design v0.1 + Do + Gap Analysis (99.2%, zero Critical/Important). 4-agent TB/UVM 패밀리 중 3번째(analyst/coder/reviewer/architect-advisor). 배포는 dry-run 확인만 완료, 실제 배포 및 7개 수동 시나리오는 deferred. verilog-tb-reviewer 완성 시 마지막 의존성 해결. | HSLEE |
