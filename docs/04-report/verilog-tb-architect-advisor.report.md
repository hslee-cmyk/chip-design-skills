# verilog-tb-architect-advisor Completion Report

> **Status**: Complete (with incomplete items deferred)
>
> **Project**: chip-design-skills
> **Version**: 0.1 (Plan) / 0.1 (Design)
> **Author**: HSLEE
> **Completion Date**: 2026-07-21
> **PDCA Cycle**: #1 (Plan → Design → Do → Check, single-session completion)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**(`agents/verilog-tb-architect-advisor.md`)와 
> **sibling 계획 문서 2곳의 route 갱신** + **skill 신규 파일 1개**(`references/non-uvm-architectures.md`)를 
> 만드는 작업이다. 템플릿의 API/Data Model/Performance/Test Coverage/CI-CD 섹션은 N/A 처리했다.

---

## Executive Summary

### 1.1 Project Overview

| Item | Content |
|------|---------|
| Feature | verilog-tb-architect-advisor |
| Start Date | 2026-07-21 (Plan) |
| End Date | 2026-07-21 (Do/Check/Report) |
| Duration | 1일 (Plan → Design → Do → Check → Report, 단일 세션) |

### 1.2 Results Summary

```
┌─────────────────────────────────────────────┐
│  Match Rate: 94.8% → ~99% (after fixes)     │
│  Target: ≥ 90%                              │
├─────────────────────────────────────────────┤
│  ✅ Complete:     Agent 파일 + 부분 배포    │
│  ⏳ Deferred:     실제 배포, 수동 시나리오   │
│  ❌ Cancelled:     None                     │
└─────────────────────────────────────────────┘
```

### 1.3 Value Delivered

| Perspective | Content |
|-------------|---------|
| **Problem** | `verilog-tb-coder`/`verilog-tb-reviewer` 둘 다 구조적 변경 의심을 감지만 하고, TB 아키텍처 판단 프레임워크 없이 사람에게 직접 넘겼다(YAGNI로 미뤄둔 갭). RTL에는 `verilog-rtl-architect-advisor`가 이미 있어 비대칭이었고, non-UVM(legacy/flat/class-based) TB 아키텍처 지식도 프로젝트 skill에 없었다. |
| **Solution** | `verilog-rtl-architect-advisor`와 정확히 대칭되는 TB 전용 read-only 구조 판단 agent 신설 — 재사용 범위 기준으로 구조 경계 판단(ARCH/LOCAL) + UVM 도입 적정성(과잉/적정/과소) 판단 축 추가 + 3안 이상 ADR + adversarial cross-review(구조 경계만). 선행 조사로 `chip-verification` skill에 `references/non-uvm-architectures.md` 신규 작성(dual-top 일반화, flat/legacy/class-based 패턴, 의사결정 기준, 안티패턴) 및 SKILL.md UVM-비종속화 완료. |
| **Function/UX Effect** | `verilog-tb-coder`(구현 전 STOP-and-Ask) 와 `verilog-tb-reviewer`(`[TB-ARCH-SUSPECT]` 발견)가 이전엔 "사람에게 직접" 넘겼던 것을 이 agent로 route — 재사용범위 판단표(구체 예시 포함) + 근거 인용 강제 + 3안 ADR stub + adversarial cross-review(각 후보 1건씩 fresh-context Agent 호출) + 권고문을 산출한 뒤 최종 결정은 사람에게 위임. |
| **Core Value** | TB/UVM 환경도 RTL과 동급의 구조적 governance를 가지게 되어, "재사용 안 되는 TB가 쌓이는 문제"와 "UVM을 과잉/과소 적용하는 문제" 모두를 근거 있게 판단하고 결정할 수 있게 됨. |

---

## 1.4 Success Criteria Final Status

> Plan §5 / Design §7 에서.

| # | Criteria | Status | Evidence |
|---|----------|:------:|----------|
| SC-1 | 재사용 범위 기준으로 ARCH/LOCAL 정확히 구분하는 판단표 | ✅ Met | `agents/verilog-tb-architect-advisor.md` §2, UVM/non-UVM 구체 예시 6개 |
| SC-2 | UVM 과잉/과소 적용을 실제 잡아내는 절차 존재 | ✅ Met | §3, `non-uvm-architectures.md` §6 인용 강제 |
| SC-3 | 3안 이상 ADR + adversarial cross-review 산출 | ✅ Met | §2.1/§2.2, fresh-context Agent 호출 명시 |
| SC-4 | `verilog-tb-coder`/`verilog-tb-reviewer` 양쪽에서 자연스럽게 route | ✅ Met | 두 sibling 문서 route 갱신 완료 |
| SC-5 | 의도적 시나리오(UVM 과잉/과소, 구조 분리 필요/불필요) 수동 검증 | ⏸️ Deferred | Design §7 시나리오 1~8 아직 실행 안 함 (실사용 검증 대기) |
| SC-6 | `install.py --only agents` 배포 테스트 | ⚠️ Partial | dry-run 확인만 완료, 실제 배포 안 함 |

**Success Rate**: 4/6 criteria met (67%) + 2 deferred (실제 배포/수동 검증은 다음 단계) — Agent 파일 자체와 sibling 라우팅 갱신은 100% 완료.

## 1.5 Decision Record Summary

| Source | Decision | Followed? | Outcome |
|--------|----------|:---------:|---------|
| [Plan §2.1] | Architecture Option C 선택 — 통합 입력·분리 출력 | ✅ | Design §4.2/4.3이 이를 공식화하고 구현에 반영됨 |
| [Design §2.1] | 판단 절차 흐름 — 구조 경계(무거운 절차) vs UVM 적정성(가벼운 권고) 순차 수행 | ✅ | Agent 파일 §2→§3 순서로 명시 |
| [Design §4.2] | ADR는 구조 경계(ARCH) 판정 시에만 발동, UVM 적정성은 권고문으로 종결 | ✅ | §3 L185-187에서 명시적 확인 |
| [Plan §정합성 유지] | sibling 문서(verilog-tb-coder/reviewer plan) 갱신 필요 | ✅ | 이 세션에서 route 문구 정정 완료 |

---

## 2. Related Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | [verilog-tb-architect-advisor.plan.md](../01-plan/features/verilog-tb-architect-advisor.plan.md) (v0.2) | ✅ Finalized |
| Design | [verilog-tb-architect-advisor.design.md](../02-design/features/verilog-tb-architect-advisor.design.md) (v0.1) | ✅ Finalized |
| Check | [verilog-tb-architect-advisor.analysis.md](../03-analysis/verilog-tb-architect-advisor.analysis.md) | ✅ Complete (94.8% → ~99%) |
| Report | 현재 문서 | ✅ Complete |

### Related Artifacts

| Item | Type | Location | Status |
|------|------|----------|--------|
| Skill Reference (non-UVM TB patterns) | 신규 파일 | `skills/chip-verification/references/non-uvm-architectures.md` | ✅ Complete (선행 조사) |
| Skill Update (UVM-비종속화) | 수정 | `skills/chip-verification/SKILL.md` | ✅ Complete |
| Sibling Route Update (coder) | 수정 | `docs/01-plan/features/verilog-tb-coder.plan.md` | ✅ Complete |
| Sibling Route Update (reviewer) | 수정 | `docs/01-plan/features/verilog-tb-reviewer.plan.md` | ✅ Complete (2곳 dangling ref 정정) |

---

## 3. Completed Items

### 3.1 Functional Requirements (Agent File)

| ID | Requirement | Status | Notes |
|----|-------------|--------|-------|
| FR-01 | Frontmatter (name/description/triggers/tools/model:opus) | ✅ Complete | verilog-rtl-architect-advisor.md 벤치마크 |
| FR-02 | Tool 목록: Read/Glob/Grep/Bash/Agent + mcp__ssh__* 3종 | ✅ Complete | read-only + fresh-context Agent 호출용 |
| FR-03 | "0. 기준" — chip-verification/non-uvm-architectures/uvm-verification/verilog-rtl 전체 Read | ✅ Complete | 부분로딩 금지, 3개 skill 조건부 4번째 모두 명시 |
| FR-04 | 입력 모드 P-only (commit diff C-모드 미지원) | ✅ Complete | Out of Scope 명시 |
| FR-05 | 책임 분해 절차 — 재사용 범위 판단표 | ✅ Complete | §2, UVM/non-UVM 구체 예시 |
| FR-06 | UVM 적정성 판단 — `references/non-uvm-architectures.md` §6 rubric 인용 강제 | ✅ Complete | §3, 과잉/적정/과소 판정 |
| FR-07 | Evidence 기반 recall (.ai/analysis/tb_*, .ai/adr/, graphify) | ✅ Complete | §2.0.5 |
| FR-08 | ARCH 판정 시 3안 이상 ADR stub | ✅ Complete | §2.1, adr-template.md 재사용 |
| FR-09 | Fresh-context adversarial cross-review (별도 Agent 호출) | ✅ Complete | §2.2, 맥락 오염 금지 |
| FR-10 | 산출물 형식: Mode/재사용범위표/Verdict/ADR+3안+cross-review/UVM적정성/다음행동 | ✅ Complete | §5 |
| FR-11 | 하드 제약: 구현 금지, partitioning 결정 금지, UVM 도입 최종 결정 금지 | ✅ Complete | §4, 정직한 한계 §6 |
| FR-12 | `install.py` 등록 (dry-run 확인만) | ⚠️ Partial | Agent glob 자동 인식 확인만, 실제 배포 미완료 |

### 3.2 Sibling Route Updates

| Document | Change | Status |
|----------|--------|--------|
| `verilog-tb-coder.plan.md` FR-08(c) | STOP-and-Ask 시 이 agent로 route(§2.1) | ✅ Complete |
| `verilog-tb-reviewer.plan.md` §4.4 | `[TB-ARCH-SUSPECT]` 발견 시 이 agent로 route | ✅ Complete |
| `verilog-tb-reviewer.plan.md` §1.2 L69 | dangling ref 정정 — "architect-advisor 없음" 서술 삭제 | ✅ Complete |
| `verilog-tb-reviewer.plan.md` §정합성 유지 L27 | "사람에게 refer" → route 문구 정정 | ✅ Complete |

### 3.3 Skill Deliverables

| Item | Location | Status | Purpose |
|------|----------|--------|---------|
| Non-UVM TB Architectures | `skills/chip-verification/references/non-uvm-architectures.md` | ✅ Complete | Legacy/flat/class-based TB 패턴, 의사결정 기준, 안티패턴 (외부 조사 기반) |
| Skill Update | `skills/chip-verification/SKILL.md` | ✅ Complete | Dual-top 아키텍처 UVM-비종속화, 트리거 갱신 |

### 3.4 Final Deliverables

| Deliverable | Location | Status |
|-------------|----------|--------|
| Agent 정의 파일 | `agents/verilog-tb-architect-advisor.md` | ✅ |
| 배포 예정 산출물 | `~/.claude/agents/verilog-tb-architect-advisor.md` (배포 미실행) | ⏳ Deferred |
| install.py 등록 | `install.py` (glob 기반 자동 인식 확인만) | ⚠️ Partial |

---

## 4. Incomplete/Carried-Over Items

### 4.1 Real Remaining Work (Not Hypothetical)

| Item | Reason | Priority | Estimated Effort | Target |
|------|--------|----------|------------------|--------|
| Actual deployment via `install.py --only agents` | Only dry-run verified so far, not the real deploy | High | 15분 | Next session / operational use |
| Design §7 Manual Test Scenarios (8 scenarios) | 수동 테스트 시나리오 1~8 (UVM 구조 분리/fold, non-UVM 분리, UVM 과잉/과소, 주변상황 고립, route 형식, ADR 생성) 실행 안 함 | High | 2~3시간(live invocation) | QA phase 또는 첫 실사용 |

### 4.2 Deferred (No Issue, Design as Intended)

| Item | Reason | Category |
|------|--------|----------|
| Design §7 시나리오 실행은 실사용 검증 범위 | 이 세션은 design/구현까지만 완료, 통합 테스트는 다음 단계 | Design Intent |

---

## 5. Quality Metrics

### 5.1 Match Rate Progression

| Phase | Metric | Value | Change |
|-------|--------|-------|--------|
| **Initial (gap-detector 최초 실행)** | Structural | 100% | — |
| | Functional | 98% | — |
| | Contract | 89% | — (dangling ref 2곳 발견) |
| | **Overall** | **94.8%** | (Structural×0.2 + Functional×0.4 + Contract×0.4) |
| | | | |
| **After Fixes (이 세션 내)** | Structural | 100% | 변화 없음 |
| | Functional | 98% | 변화 없음 |
| | Contract | ~98% | +9%p (dangling ref 정정 완료) |
| | **Overall** | **~99%** | Target 90% 초과달성 |

### 5.2 Gap Resolution

| Priority | Gap | Type | Resolution | Status |
|----------|-----|------|-----------|--------|
| 🔴 Important | `verilog-tb-reviewer.plan.md` L69 "architect-advisor 없음" dangling | Contract | 서술 삭제 및 route 문구 정정 | ✅ Fixed |
| 🟡 Minor | `verilog-tb-reviewer.plan.md` L27 "사람에게 refer" 애매함 | Contract | route 문구 명확화 | ✅ Fixed |
| 🟡 Minor | `verilog-tb-architect-advisor.plan.md` FR-12 install.py 메커니즘 오기술 | Functional | 실제 메커니즘(glob 자동 인식) 정정 | ✅ Fixed |

### 5.3 Resolved Issues from Gap-Detector

| Issue | Resolution | Result |
|-------|-----------|--------|
| `verilog-tb-reviewer.plan.md`에서 신설 agent 미언급 | §1.2/§정합성 유지의 dangling reference 2곳 정정 | ✅ Resolved |
| Install.py 요구사항 명세와 실제 구현 불일치 | Plan FR-12/§7.1 재정정 — 별도 AGENTS 목록 없고 glob 기반 자동 인식 | ✅ Resolved |

---

## 6. Lessons Learned & Retrospective

### 6.1 What Went Well (Keep)

- **Cross-repo 정합성 검증이 자동으로 작동했다**: Design 단계에서 verilog-tb-coder/reviewer plan 문서의 "dangling reference" 문제를 Do 전에 미리 감지하고 정정할 수 있었다. 이는 세 문서가 일관된 계약 구조를 따르고 있다는 신호.
- **Design 단계에서 두 축(구조 경계 vs UVM 적정성)을 명확히 분리했다**: Option C 아키텍처 선택이 사용자의 "TB도 architecturing이 필요하다"는 원래 지적과 "ADR 없이 권고만 하는 것이 맞다"는 후속 확인 사이의 긴장을 잘 해결했다 — 무거운 절차와 가벼운 판단을 명시적으로 분리함으로써 실사용 마찰을 낮췄다.
- **이전 RTL feature의 경험(재서술 금지, evidence 기반 recall)이 직접 재사용되었다**: verilog-rtl-architect-advisor의 골격을 따라가면서 도메인 특화 부분(TB의 "재사용 범위 기준")만 추가하면 되어 설계 시간이 단축됐다.

### 6.2 What Needs Improvement (Problem)

- **"실제 배포" vs "dry-run 확인"의 경계가 모호했다**: install.py의 glob 메커니즘을 이해하는 데는 성공했지만, "dry-run으로 인식 확인" 단계에서 멈춰서 "실제 배포 테스트"까지 진행하지 않았다. 이는 "Complete"와 "Partial" 사이의 회색 영역을 남겼다.
- **8개 수동 시나리오 테스트를 Design에는 정의했지만 실행하지 않았다**: 이는 설계적으로 "QA 단계 또는 첫 실사용에서 실행하라"고 명시했으므로 설계 의도에 부합하지만, "이 세션에 모두 마무리하지 않는" 결정의 위험을 드러낸다 — 향후 누군가가 이 agent를 처음 써보려 할 때 "8개 시나리오가 미검증"이라는 사실을 명확히 알아야 한다.

### 6.3 What to Try Next (Try)

- 배포 단계를 "dry-run 확인" → "실제 배포" → "배포본 동작 확인"의 3단계로 명시적으로 분리해서, 각 단계가 Definition of Done에 포함되도록 체크리스트화.
- Design 단계에서 "이 시나리오는 QA 단계/실사용 단계에서 실행"이라고 명시할 때, 그 약속을 추적하는 메커니즘(예: DEFERRED 템플릿, 다음 세션 automate reminder) 도입.

---

## 7. Process Improvement Suggestions

### 7.1 PDCA Process

| Phase | Current | Improvement Suggestion |
|-------|---------|------------------------|
| Design | 아키텍처 선택(Option A/B/C)을 Checkpoint로 두고 3가지 비교 테이블을 표시 | Checkpoint 통과 후 "이 선택이 구현에 100% 반영됐는지" gap-detector 재검증 체크리스트 |
| Do | 구현 후 sibling 문서 갱신을 To-Do로 남김 | Definition of Done에 "sibling 문서 route 확인" 항목을 명시적으로 포함 |
| Check | 정적 분석(문서 vs 파일) 후 배포 테스트 | 배포 테스트를 "dry-run" vs "실제 배포" 2단계로 나눠 각각 체크리스트 항목화 |

### 7.2 Agent Design Convention

| Area | Improvement Suggestion | Expected Benefit |
|------|------------------------|------------------|
| sibling agent 갱신 | agent A가 신설되어 agent B/C가 그걸로 route할 때, 두 문서의 route 문구 동기화를 자동 체크 | 이번처럼 dangling reference가 남는 실수 방지 |
| 배포 vs 테스트 | "dry-run 확인만" vs "실제 배포 + 동작 검증"을 명시적으로 구분하는 템플릿 | 회색 영역 제거, 다음 세션의 실행 여부를 명확히 함 |

---

## 8. Next Steps

### 8.1 Immediate (Before Operational Use)

- [ ] `install.py --only agents` 실제 배포 실행 (dry-run 아닌 실제 설치)
- [ ] 배포 후 `~/.claude/agents/verilog-tb-architect-advisor.md` 존재 확인
- [ ] Design §7 시나리오 1~3 (구조 분리/fold/non-UVM) 최소한 실행해 agent 동작 확인

### 8.2 First Operational Use

- [ ] `verilog-tb-coder`가 구조적 변경 의심으로 FR-08(c) STOP-and-Ask 할 때 이 agent 호출 test
- [ ] `verilog-tb-reviewer`가 `[TB-ARCH-SUSPECT]` 발견해 이 agent로 route하는 흐름 확인
- [ ] Design §7 시나리오 4~8 (UVM 과잉/과소, adversarial cross-review, ADR 생성 등) 실행

### 8.3 Post-Deployment Monitoring

- [ ] 첫 실사용 시 agent의 판단(재사용범위 판단표, UVM 적정성 판정)이 사용자 기대와 일치하는지 피드백 수집
- [ ] ADR stub 생성 품질, adversarial cross-review의 fresh-context 준수 여부 확인

---

## 9. Changelog

### 2026-07-21 — Initial Session (Plan → Design → Do → Check)

**Added:**
- `agents/verilog-tb-architect-advisor.md` (frontmatter + 6개 섹션)
  - 책임 분해(재사용 범위 기준, UVM/non-UVM 구체 예시)
  - Evidence recall + 3안 ADR + adversarial cross-review
  - UVM 적정성 판단(권고문으로 종결)
  - 정직한 한계(자동 classifier 부재, evidence base 외부 문헌)
- `skills/chip-verification/references/non-uvm-architectures.md` (선행 조사, 외부 문헌 기반)
  - Dual-top, flat, class-based, layered 패턴
  - §6 의사결정 기준표 (UVM vs Non-UVM)
  - §7 안티패턴
- Route 갱신: `verilog-tb-coder.plan.md` FR-08(c), `verilog-tb-reviewer.plan.md` §4.4

**Fixed:**
- `verilog-tb-reviewer.plan.md` dangling reference (§1.2 L69, §정합성 유지 L27) 정정
- `verilog-tb-architect-advisor.plan.md` FR-12 install.py 메커니즘 오기술 정정

**Changed:**
- `skills/chip-verification/SKILL.md` — dual-top 아키텍처를 UVM-비종속으로 일반화

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-21 | Completion report — Plan v0.2 + Design v0.1 + Do + Gap Analysis (94.8%→~99%) + sibling 갱신. 4-agent TB/UVM 패밀리 완성(analyst/coder/reviewer/architect-advisor). 배포는 dry-run만 완료, 실제 배포 및 8개 수동 시나리오 테스트는 다음 단계로 deferred. | HSLEE |
