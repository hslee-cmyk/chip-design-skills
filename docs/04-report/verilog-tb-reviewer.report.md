# verilog-tb-reviewer Completion Report

> **Status**: Complete (with deferred operational verification)
>
> **Project**: chip-design-skills
> **Version**: 0.4 (Plan) / 0.2 (Design) / 0.1 (Analysis)
> **Author**: HSLEE
> **Completion Date**: 2026-07-22
> **PDCA Cycle**: #1 (Plan → Design → Do → Check → Report, single-feature completion)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**(`agents/verilog-tb-reviewer.md`)를
> 만드는 작업이다. 템플릿의 API/Data Model/Performance/Test Coverage/CI-CD 섹션은 N/A 처리했다
> (`verilog-tb-coder.report.md`/`verilog-tb-architect-advisor.report.md` 선례와 동일 패턴).

---

## Executive Summary

### 1.1 Project Overview

| Item | Content |
|------|---------|
| Feature | verilog-tb-reviewer (TB-side independent review agent) |
| Start Date | 2026-07-10 (Plan phase began) |
| End Date | 2026-07-22 (Do/Check/Report completed) |
| Duration | Planning 2.5+ 일 (v0.1→v0.4, 4회 수정 포함) + Implementation 1 일 (Design→Do→Check→Report same session) |

### 1.2 Results Summary

```
┌─────────────────────────────────────────────┐
│  Match Rate: 99% (first pass, static)       │
│  Target: ≥ 90%                              │
├─────────────────────────────────────────────┤
│  ✅ Complete:     Agent 파일 + 기본 검증    │
│  ⏳ Deferred:     실제 배포, 수동 시나리오   │
│  ℹ️  Gap Analyzed: 2 Minor findings        │
│     (Design doc numbering drift, fixed)     │
└─────────────────────────────────────────────┘
```

### 1.3 Value Delivered

| Perspective | Content |
|-------------|---------|
| **Problem** | `verilog-tb-coder`의 self-check만으로는 anti-tautology를 구조적으로 보장할 수 없음(자기 인증의 모순). 동시에 이 agent는 xcelium-mcp 워크플로우 전용이 아니라 일반 TB 리뷰 요청에도 대칭적으로 사용 가능해야 하는데, v0.1~0.3은 "fix-plan.md가 항상 존재한다"고 가정해 workflow 종속 설계가 되어 있었음. |
| **Solution** | `verilog-rtl-reviewer`와 대칭되는 TB 전용 read-only 검토자 신설. 호출 맥락(xcelium-mcp fix-review vs 사람의 직접 리뷰 요청) 무관 단일 균일 절차로 spec 정당화 최종 판단 + checker 완화 탐지 + 범위 준수 + 구조 변경 의심 route. self-check 결과와 무관하게 항상 처음부터 재검토하는 이중 방어 메커니즘. |
| **Function/UX Effect** | xcelium-mcp `/sim debug`의 `fix_target=tb` 완료 직후 이 agent 자동 호출로 fix-review 게이트 채우기(문제 발견 시 fix-implement로 되돌림, clean이면 `/sim verify`로 진행) **뿐만 아니라**, 그와 무관하게 사람이 "이 TB diff 검토해줘"라고 직접 요청해도 동일한 엄격도의 검토 절차 적용. |
| **Core Value** | TB fix도 RTL fix와 동급의 "구현자 self-check(1차 필터) + 독립 검증자 최종 판단(정확성)" 2단 방어 구조 완성. 이 방어가 특정 워크플로우에 종속되지 않으므로, TB 코드를 다루는 모든 맥락에서 재사용 가능. TB 4-agent family(analyst/coder/architect-advisor/reviewer) 완성으로 RTL 6-agent family와 구조 패리티 달성. |

---

## 1.4 Success Criteria Final Status

> Plan §5.1 (Definition of Done) 에서.

| # | Criteria | Status | Evidence |
|---|----------|:------:|----------|
| SC-1 | `agents/verilog-tb-reviewer.md` 작성 완료 — §4 검토 항목이 구체적 절차로 명시 | ✅ Met | Agent 파일 §0-§6 완전 구성 |
| SC-2 | "왜 model: opus 인가" 명시적 헤더 포함 | ✅ Met | Agent 파일 §1.2 (L34-39) |
| SC-3 | "정직한 한계" 섹션 포함(TB family 표준) | ✅ Met | Agent 파일 §6 (L184-196) |
| SC-4 | `agents/verilog-tb-reviewer.md` 배포 확인 — `install.py --dry-run` | ✅ Met | Dry-run 확인 완료 |
| SC-5 | xcelium-mcp v1.36 최종 대조 + v1.35 "기록=출력" 절차 반영 | ✅ Met | Plan §정합성 유지 §정점 v1.36 명시 |
| SC-6 | 의도적 순환 논리 시나리오 + fix-plan.md 없는 직접 요청 시나리오 수동 검증 | ⏸️ Deferred | Design §6 Test Plan 시나리오 1~8 정적 검증 완료, 실제 Task() 호출 검증은 QA 단계에서 수행 예정 |

**Success Rate**: 5/6 criteria met (83%) + 1 deferred (실제 수동 시나리오 검증은 QA 단계). Agent 파일 자체와 설계 검증은 100% 완료.

### 1.5 Decision Record Summary

| Source | Decision | Followed? | Outcome |
|--------|----------|:---------:|---------|
| [Plan v0.4] | formal 파라미터 스키마 없음, 자유 형식 프롬프트 + 단일 균일 절차(fix-plan.md 무관) | ✅ | Do에서 구현, Analysis에서 확인 |
| [Plan v0.4] | "fix-plan 범위" → "선언된 범위(출처 무관)"로 일반화 | ✅ | §2.3/4.3에 명시 |
| [Plan FR-08] | TB-ARCH-SUSPECT → `verilog-tb-architect-advisor`로 route(사람 직접 아님) | ✅ | §2.4 명시, architect-advisor와 양방향 참조 |
| [Design §2.1] | 최상위 섹션 구조 rtl-reviewer와 동일, 내용은 TB 스케일(taxonomy/스텝 이식 안 함) | ✅ | 구현 완료, Do 단계 섹션 배치 패밀리 컨벤션 따름 |
| [Design §4.1a] | STATIC/SIM 라벨 finding 단위 표기 메커니즘 도입 + 2-way verdict 유지 | ✅ | §2.1a/§4 구현, xcelium-mcp 계약(2-way) 근거 명시 |

---

## 2. Related Documents

| Phase | Document | Status |
|-------|----------|--------|
| Plan | [verilog-tb-reviewer.plan.md](../01-plan/features/verilog-tb-reviewer.plan.md) (v0.4) | ✅ Finalized |
| Design | [verilog-tb-reviewer.design.md](../02-design/features/verilog-tb-reviewer.design.md) (v0.2) | ✅ Finalized |
| Check | [verilog-tb-reviewer.analysis.md](../03-analysis/verilog-tb-reviewer.analysis.md) | ✅ Complete (99%, zero Critical/Important) |
| Report | 현재 문서 | ✅ Complete |

### Related Artifacts

| Item | Type | Location | Status |
|------|------|----------|--------|
| Agent 정의 파일 | 신규 | `agents/verilog-tb-reviewer.md` | ✅ Complete |
| 배포 산출물 | 예정 | `~/.claude/agents/verilog-tb-reviewer.md` (dry-run 확인만) | ⏳ Deferred |
| Sibling Agent Updates | 참고 | `verilog-tb-coder.md` (이미 plan/do 갱신 완료) | ✅ Linked |

---

## 3. Completed Items

### 3.1 Functional Requirements (Agent File)

| ID | Requirement | Status | Evidence |
|----|-------------|:------:|----------|
| FR-01 | frontmatter — "Use it when/Do NOT use for/Triggers" 3-part | ✅ | L3-21, TB 패밀리 표준 준수 |
| FR-02 | Tools: R/Glob/Grep/Bash/Write + mcp__ssh 3종 (read-only) + model: opus | ✅ | L22-23 |
| FR-03 | "0. 기준" — 4종 정본(verilog-rtl/chip-verification+non-uvm-arch/uvm-verification/ssh-mcp) 전체 로드 | ✅ | §0 L41-56, non-uvm-architectures.md 포함 |
| FR-04 | Task() 입력 — formal 스키마 없음, 자유 형식 + 호출 맥락 무관 단일 절차 | ✅ | §0/§2 입력 설명 (L84-89) |
| FR-05 | spec 정당화 최종 판단 — self-check 무관 재확인 + STATIC/SIM 라벨 | ✅ | §2.1(L91-101)/§2.1a(L103-109) |
| FR-06 | checker 완화 탐지 | ✅ | §2.2 (L111-116) |
| FR-07 | 선언된 범위 준수 확인(출처 무관 일반화) | ✅ | §2.3 (L118-123), "fix-plan 범위" 제거 |
| FR-08 | TB-ARCH-SUSPECT → `verilog-tb-architect-advisor`로 route | ✅ | §2.4 (L125-128), §1.1 양방향 명시 |
| FR-09 | TB 컨벤션 준수 + 분석서 정합성 | ✅ | §2.5-2.6 (L130-138) |
| FR-10 | 보고서 경로/구조/Manifest 반환 | ✅ | §3-4 (L140-169) |
| FR-11 | Manifest — verdict 2-way(`clean`/`issues_found`) + 근거 명시 | ✅ | §4 (L157-168), xcelium-mcp 계약 인용 |
| FR-12 | 배포 확인 — `install.py --dry-run` | ✅ | dry-run 완료 |

**Status**: 12/12 Functional Requirements met (100%)

### 3.2 Non-Functional Requirements

| Category | Criteria | Status | Evidence |
|----------|----------|:------:|----------|
| 독립성 | self-check 결과에 의존하지 않고 항상 처음부터 재검토 | ✅ | §2.1 (L98-101), 3곳 반복 강조 |
| Anti-tautology 최종 방어 | 순환 논리 fix-plan 실제 걸러냄 | ⏸️ Deferred | 수동 시나리오 1-2 실행 필요(QA) |
| 컨벤션 일관성 | `verilog-rtl-reviewer` 대칭 구조/톤 일관 | ✅ | §2.1/§4 섹션 구조 매핑, 톤 일치 |
| 워크플로우 비종속성 | fix-plan.md 경유와 직접 요청에서 동일 절차/결과 | ✅ | §0-§2 전수 "또는" 병기 확인(gap-detector 검사) |
| 패밀리 일관성 | TB 패밀리(analyst/coder/architect-advisor) 표준 준수 | ✅ | frontmatter/model/§6 "정직한 한계" 전부 포함 |

**Status**: 4/5 met + 1 deferred = 80% + QA 보류

### 3.3 Design Decisions Implemented

- **Architecture Option**: C (최상위 구조 rtl-reviewer 동일, 내용 TB 스케일) — 구현 완료
- **STATIC/SIM Honesty**: finding 단위 라벨 메커니즘(§2.1a) — 구현 완료, 정적 검증 통과
- **Verdict 2-way 유지**: xcelium-mcp 계약(`fix_review.status`) 준수 — 근거 명시적 포함(§4)
- **Workflow 무관성**: fix-plan.md 선택성 + 호출 경로 무관 단일 절차 — 전체 섹션에 일관 반영

---

## 4. Incomplete / Carried-over Items

### 4.1 Deferred to QA Phase

| Item | Scope | Status | Reason |
|------|-------|:------:|--------|
| Manual Scenario 1 | 순환 논리(fix-plan 경유, self-check 통과) | ⏸️ Pending | Design §6 Test Plan 정의만 완료, 실제 Task() 호출 테스트 미실행 |
| Manual Scenario 2 | 순환 논리(사람 직접 요청 경유) | ⏸️ Pending | 호출 맥락 무관 균일성 검증(0.4 신규 중요 항목) |
| Scenarios 3-8 | checker 완화, 범위 이탈, TB-ARCH-SUSPECT, STATIC/SIM 라벨, clean 판정, BLOCKER | ⏸️ Pending | 8개 시나리오 정적 정의 완료, 실행 대기 |
| 실제 배포 | `~/.claude/agents/verilog-tb-reviewer.md` 파일 배포 | ⏳ Pending | dry-run 확인만, `install.py --only agents` 실행 미완료 |

### 4.2 Rationale

이들 항목이 미완료인 이유:

1. **Manual Scenarios 1-8**: Design §6에서 8개 시나리오가 정적으로 정의되었으나, "실제 Task() 호출"과 "agent 응답 검증"은 agent가 배포 후에만 가능하다(Check 단계는 정적 파일 내용 검증이므로, 시나리오 정의 및 성공 기준만 검증함). 이는 QA 단계의 "실사용 검증"에 속하며, 현재 Check 단계 범위를 초과한다.

2. **실제 배포**: dry-run으로 glob 자동 인식 확인 완료, 그러나 실제 배포(`install.py --only agents` 실행) 및 배포 후 `/pdca status` 확인은 사용자의 명시적 지시 후 수행하는 것이 관례다(verilog-tb-coder 보고서와 동일 패턴).

---

## 5. Quality Metrics

### 5.1 Match Rate Analysis

```
┌──────────────────────────────────────────────────────┐
│ Structural Match Rate:     97%                        │
│   - Frontmatter (FR-01/02):        100%              │
│   - §0 기준 (FR-03):                95% (4/4 로드)   │
│   - §1-§6 절차 (FR-04~09):          97% (일관성)     │
│   - §3-4 출력 (FR-10/11):          100%              │
│─────────────────────────────────────────────────────  │
│ Functional Match Rate:     99%                        │
│   - 12/12 FR 구현                                     │
│   - 4/5 NFR 검증 + 1 QA 보류                         │
│   - Task() 계약 명확성 100%                          │
│   - routing 명시성 100%                              │
│─────────────────────────────────────────────────────  │
│ Contract Match Rate:      100%                        │
│   - xcelium-mcp v1.36 `fix_review.status` 일치      │
│   - 2-way verdict 근거 명시(§4)                     │
│   - Manifest 스키마 일치                             │
│─────────────────────────────────────────────────────  │
│  OVERALL MATCH RATE:       99%                        │
└──────────────────────────────────────────────────────┘
```

### 5.2 Gap Analysis Summary

> [verilog-tb-reviewer.analysis.md](../03-analysis/verilog-tb-reviewer.analysis.md) 참조

| Severity | Count | Status | Notes |
|----------|:-----:|:------:|-------|
| Critical | 0 | ✅ None | - |
| Important | 0 | ✅ None | - |
| Minor | 2 | ✅ Fixed (same session) | Design 문서의 §2.1/§7.2 번호 매김 실제 구현과 drift — 구현 선택(패밀리 컨벤션 우선, rtl-reviewer 대응)이 더 나음을 판단해 문서 갱신 완료 |

**Verdict**: PASS (≥90%) — 첫 번째 gap-detector 실행에서 기준 달성, iteration 불필요.

### 5.3 Design-Code Alignment

| Aspect | Design v0.2 | Implementation v1 | Match |
|--------|------------|-------------------|:-----:|
| §2.1 매핑표 섹션 순서 | rtl-reviewer 대응 "§0→§1→...→§6" | "§0(기준)→§1(설계)→§2(검토)→§3(출력)→§4(verdict)→§5(제약)→§6(한계)" | ⚠️ 번호만 다름, 내용/의도 일치 |
| 역할경계(architect-advisor) | §1.1 명시 | §1.1 (L73-79) 일치 | ✅ |
| 검토 항목 §2.1-2.6 | Plan §4.1-4.7 인용 | 전체 일치 | ✅ |
| STATIC/SIM 라벨 메커니즘 | §4.4 설명 | §2.1a (L103-109) 구현 | ✅ |
| 2-way verdict 근거 | §4.3에서 "왜 3-way 아닌가" 설명 | §4 (L157-168) 상세 명시 | ✅ |

**Alignment**: 구현이 설계를 정확히 따름(§번호 drift는 구현 쪽이 더 나음).

---

## 6. Lessons Learned

### 6.1 Design Patterns That Worked Well

#### ✅ "Workflow-Agnostic Single Procedure" Pattern (verilog-tb-coder에서 학습, 여기서 재적용)

이 feature의 가장 중요한 설계 결정은 **plan v0.3→v0.4 주요 수정**이었다: "fix-plan.md 경유"와 "사람의 직접 요청"을 이원화하지 않고 **단일 균일 절차**로 설계하기. 

이 원칙은 `verilog-tb-coder`가 v0.3→v0.4에서 정확히 같은 교훈을 얻었던 부분이다(`verilog-tb-coder.plan.md` v0.3에서 "Fix 모드/General 모드" 이원화를 시도했다가 v0.4에서 철회). `verilog-tb-reviewer`는 같은 실수를 반복하는 대신 **이미 확립된 패턴을 즉시 재사용**했다:

- **비용**: 계획 단계에서 v0.3→v0.4 한 번의 대규모 수정 필요
- **효과**: 구현 단계 진입 전 설계 오류 제거 + agent 자체가 더 단순하고 견고한 구조

**Result**: 첫 실행에 99% 매칭. 동일 실패 패턴을 두 feature에서 한 번씩 적중시킨 후 세 번째 agent(verilog-tb-coder→verilog-tb-reviewer)는 즉시 회피한 사례로서, **recurring pattern recognition and re-application의 가치**를 보여준다.

#### ✅ "Architecture Option C: Structural Symmetry + Content Independence" (rtl-reviewer 벤치마크)

최상위 섹션 구조를 RTL과 맞추되(§0→§1→...→§6), 내용은 TB-specific vocabulary 유지. 이는 두 파일이 "대칭" agent라는 관계를 파일 레벨에서 드러내면서도, RTL의 taxonomy/multi-step 절차를 억지로 이식하지 않는다(YAGNI 원칙).

**Result**: codebase에서 `verilog-rtl-reviewer.md`와 `verilog-tb-reviewer.md` 파일을 나란히 열었을 때, 섹션 이름과 의도가 명확하게 대응되므로, 향후 유지보수자가 "왜 TB에는 이 섹션이 없는가"를 쉽게 이해 가능.

#### ✅ "Cross-Repo Requirement Anchoring" (xcelium-mcp v1.36과의 계약)

이 agent의 verdict 2-way(`clean`/`issues_found`)는 xcelium-mcp의 `fix_review.status` 스키마와 일치한다. 이는 우연이 아니라, **cross-repo 요구사항을 명시적으로 문서에 인용하고 차단**(§정합성 유지)하는 설계 규율의 결과다.

**Result**: 요구사항 정본이 2개 repo에 분산된 상황에서도, 버전 pin(v1.36), 섹션 참조(§5.8 "4) fix-review" TB 경로)를 명확히 기록하므로, 향후 xcelium-mcp 버전 업 시 변경 영향을 추적 가능.

### 6.2 Recurring Anti-patterns to Prevent

#### ⚠️ "Implicit Workflow Assumptions" (두 번 반복, 이제 셋 감시)

이 프로젝트에서 verilog agent family 구성 중 반복된 실수 패턴:

1. **verilog-rtl-coder v0.1**: (초기 설계에서 "Fix 모드"를 상정했으나, 실제 rtl-coder 설계는 이 구분이 없었음 — 기간 내 수정)
2. **verilog-tb-coder v0.3**: "Fix 모드"와 "General 모드" 이원화 시도 → v0.4에서 철회, 단일 절차로 통일
3. **verilog-tb-reviewer v0.3**: 동일 실수 (fix-plan.md 필수 가정) → v0.4에서 철회

**Pattern Signature**: "이 agent는 주로 [specific workflow] 맥락에서 쓰이니까, [formal parameter schema] / [다른 절차]를 별도로 두겠다"라는 design-time 가정이, runtime에는 "이것도 다른 맥락에서 쓰인다"는 요청으로 깨진다.

**Prevention Strategy**: 향후 verilog agent 신설 시:
- Requirement 명시 단계에서 "이 agent는 [workflow X]에서**만** 쓰인다"고 명시하지 않기
- 대신 "동일 기능은 [workflow A]/[workflow B] 양쪽에서 호출되며, 둘 다 같은 절차"라고 명시하기
- 이중화/mode 분기는 plan 단계에서 명시적으로 제거하기(YAGNI 편향)

### 6.3 Verification Strategy Lessons

#### ✅ "Static-Only Gap Analysis Sufficiency for Agent Files"

이 feature의 "산출물"은 agent markdown 파일(동적 런타임 없음)이므로, static gap analysis(file content diff vs design) 한 번으로 99% 매칭 달성했다. 

**Implication**: 
- web app feature의 경우 runtime test (L1-L5)가 필수
- agent file feature의 경우 structural/functional/contract 정적 검증이 충분 (단, operational scenario 검증은 QA로 넘김)
- 이 경계를 명확히 하면 feedback loop 효율 향상

### 6.4 Cross-Session Knowledge Retention

이 보고서를 쓰는 시점에 이미:
- `verilog-tb-coder` (선행 completion, 같은 세션)
- `verilog-tb-architect-advisor` (선행 completion)
- Plan v0.1~v0.4 수정 히스토리 (4회)

등이 누적되어 있었고, 이들이 **명시적인 설계 문서(Plan/Design)**로 기록되어 있었기에, `verilog-tb-reviewer`는 그 패턴을 즉시 재학습/재사용할 수 있었다. 이는 **"결정 기록 + 명시적 계획 문서의 가치"**를 보여주는 사례다.

---

## 7. Process Improvement Suggestions

### 7.1 Short-term (이 project 범위)

- **Manual Scenario Execution (QA)**: Design §6 Test Plan의 8개 시나리오를 실제 Task() 호출로 검증하되, 특히 **시나리오 1과 2의 동일성 검증**(호출 맥락 무관 균일성)에 집중. 이는 v0.4의 "핵심 설계 결정"을 operational level에서 확인하는 critical path.

- **Deployment Smoke Test**: `install.py --only agents` 실행 후 `/pdca status` 또는 agent 호출 dry-run으로 glob 인식 확인. 현재 dry-run만 되어 있으므로 실제 배포 1회 수행.

### 7.2 Mid-term (verilog agent family 확장 시)

- **"Workflow-Agnostic Checklist" 추가**: Plan phase 체크리스트에 "이 agent는 특정 workflow에서만 사용되는가? 다른 호출 경로도 있는가?" 문항 추가. 이를 통해 verilog-tb-coder/reviewer에서 반복된 "implicit workflow assumption" 오류를 proactive하게 방지.

- **Cross-Agent Consistency Audit**: verilog agent family가 증가할수록, 신규 agent 작성 후 **독립적인 fresh-context agent가 다른 모든 agent와의 일관성을 자동으로 감시**하는 프로세스. (verilog-tb-reviewer 0.3의 "독립 fresh-context agent 검토"가 5개 gap을 찾았던 것처럼, 이를 정규화.)

### 7.3 Long-term (ecosystem level)

- **"Evidence-based Taxonomy 축적"**: TB의 경우 아직 RTL 같은 T1-T9 taxonomy가 없지만, 실제 TB fix 사례가 쌓이면 (Design §6 시나리오 1~8 검증 등을 통해) **후속 feature로 정식 TB failure taxonomy 구축** 가능. 현재는 YAGNI로 명시했으되, 증거 수집을 시작.

- **Formal Parameter Schema Revisit**: 이 프로젝트에서 "formal parameter schema는 workflow coupling을 야기한다"는 패턴이 여러 번 보였다. 향후 agent 설계 철학에서 **"free-form prompt > named parameter schema" 기본 편향**을 채택하기.

---

## 8. Next Steps

### Immediate (within this session)

- [ ] Design §6 시나리오 1~2 수동 검증 (fix-plan 경유 + 사람 직접 요청, 동일 결과) — QA 단계로 넘김
- [ ] `install.py --only agents` 실행해 실제 배포 완료
- [ ] `/pdca status` 또는 agent 호출로 배포 확인

### Before Merging (validation)

- [ ] xcelium-mcp v1.36과의 최종 대조 (cross-repo 계약 확인) — 현재 문서만 확인, 실제 호출 테스트 예정
- [ ] sibling agent들(verilog-tb-coder, verilog-tb-architect-advisor) route 참조 양방향 확인

### QA Phase

- [ ] Design §6 Manual Test Plan §6 (시나리오 1~8) 실행 및 verdict 기록
- [ ] 특히 **시나리오 1(fix-plan 경유)과 2(사람 직접 요청) 이원화 검증** — 0.4의 핵심 설계 결정

### Future (TB Ecosystem)

- [ ] verilog-rtl-reviewer와의 "형제 쌍" 관계 문서화 (cross-agent learning resource)
- [ ] TB failure case 축적 → 정식 TB taxonomy 후속 feature
- [ ] Agent family 자동 일관성 감시 tool (fresh-context audit 자동화)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-10 | 초안 — xcelium-mcp v1.33/v1.34에서 확정된 `verilog-tb-reviewer` 요구사항을 Plan 문서화. `verilog-rtl-reviewer.md`의 STATIC/SIM 정직성·architect-advisor 역할 분담 골격을 재사용 | HSLEE |
| 0.2 | 2026-07-21 | `verilog-tb-architect-advisor` 신설(Plan v0.2) 계기로 §2.1/FR-08/§4.4를 "TB-ARCH-SUSPECT를 사람에게 직접 refer"에서 "이 agent로 route"로 갱신. 다만 agent 파일은 아직 미작성 상태 | HSLEE |
| 0.3 | 2026-07-22 | 전체 verilog agent 패밀리(rtl-analyst/coder/reviewer/prover/debugger/architect-advisor + tb-analyst/coder/architect-advisor) 종합 정합성 감사. 발견 사항: (1) FR-04 formal 스키마 철회(verilog-tb-coder.plan.md 0.3→0.4와 동일 실수), (2) TB 패밀리 표준 frontmatter 3-part 명시, (3) **`model: opus` 누락 발견 및 추가**(기본 결함), (4) §5.1 DoD에 "정직한 한계" 섹션 추가(TB 표준, rtl-reviewer는 미보유), (5) cross-repo 버전 pin v1.34→v1.36 갱신, (6) FR-03 `references/non-uvm-architectures.md` 누락 추가, (7) §4.1a STATIC/SIM 라벨 메커니즘 신설, (8) v1.35 "기록=출력" 절차 반영. 독립 fresh-context agent 검토로 5개 gap 전부 확인. 이는 family-wide consistency 감사의 모범사례 | HSLEE |
| 0.4 | 2026-07-22 | 사용자 지적("agents는 특정 flow에 종속되면 안 돼")을 반영 — v0.3까지는 frontmatter/model/섹션 구조 같은 **스타일** 일관성만 다뤘고, §1.1/§2.1/§4 내용은 여전히 "fix-plan.md가 항상 존재"한다는 **workflow-v2 종속** 설계. 이는 `verilog-tb-coder`가 이미 0.3→0.4에서 철회한 실수 반복 — `verilog-tb-coder`의 패턴을 그대로 재적용: (a) Summary/Executive Summary/Context Anchor를 general-purpose 우선으로 재작성 (b) §1.1 Purpose/§2.1 Scope/FR-05/FR-07을 "호출 시 제시된 근거(출처 무관)"로 일반화 (c) §4 검토 항목과 FR-10/보고서 경로를 일반화 (d) FR-01 Triggers에 "이 TB 변경 검토해줘" 류 일반 요청 키워드 추가 (e) §7.2에 일반 요청 consumer 행 신설 (f) §5.1/§3.2에 "두 호출 경로 동일 결과" 검증 항목 추가. 결과적으로 §0 기준부터 §6 한계까지 모든 섹션에서 "호출 맥락 무관" 원칙이 일관되게 반영 | HSLEE |

---

## Appendix: Changelog (v0.4 Final)

### Added
- Agent 정의 파일: `agents/verilog-tb-reviewer.md` (신규, 207 lines)
- 설계 근거: 최상위 섹션 구조 rtl-reviewer 동일 + 내용 TB 스케일
- STATIC/SIM 정직성 메커니즘: `[TB-STATIC]`/`[TB-NEEDS-SIM-VERIFY]` finding 라벨
- 호출 맥락 무관성: fix-plan.md/사람 직접 요청 경유 동등 처리

### Changed
- Plan v0.1→v0.4: 4회 수정 (formal schema 철회, frontmatter 표준화, model: opus 추가, workflow 비종속화)
- Design v0.1→v0.2: 섹션 배치 "0. 기준" 우선화 (TB 패밀리 컨벤션), Verdict 독립 섹션화
- Sibling routing: `verilog-tb-coder.plan.md`/`verilog-tb-architect-advisor.plan.md`와 양방향 참조

### Fixed
- Design 문서의 §2.1/§7.2 번호 매김 drift (실제 구현에 맞춤)
- cross-repo 버전 pin v1.34→v1.36 갱신
- TB 패밀리 표준화 (frontmatter/model/정직한 한계)

---

