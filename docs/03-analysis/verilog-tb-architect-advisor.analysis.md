# verilog-tb-architect-advisor Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: chip-design-skills
> **Analyst**: gap-detector agent + HSLEE
> **Date**: 2026-07-21
> **Design Doc**: [verilog-tb-architect-advisor.design.md](../02-design/features/verilog-tb-architect-advisor.design.md)

> 이 feature는 markdown agent 정의 파일 1개 + sibling plan 문서 2곳 수정이다. 템플릿의
> API/Data Model/Performance/Test Coverage/Clean Architecture(코드 레이어)/Convention(naming
> 등 TS 관례) 섹션은 해당 사항이 없어 N/A 처리하고(`verilog-tb-analyst.design.md` 선례 동일 적용),
> 정적(static-only) Match Rate 공식만 사용한다: `Structural×0.2 + Functional×0.4 + Contract×0.4`.

---

## Context Anchor

> Design 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | `verilog-tb-coder`/`verilog-tb-reviewer` 둘 다 구조적 변경 의심을 감지만 하고 판단 프레임워크 없이 사람에게 직접 넘기도록 설계됨(YAGNI로 미뤄둔 갭). RTL에는 이미 이 역할(`verilog-rtl-architect-advisor`)이 있어 비대칭 |
| **WHO** | `verilog-tb-coder`(구현 전 STOP-and-Ask 시 경유), `verilog-tb-reviewer`(`[TB-ARCH-SUSPECT]` 발견 시 경유), 그리고 이들을 거치지 않고 TB/UVM plan·design 문서를 직접 검토받고 싶은 사람 |
| **RISK** | TB 구조 판단은 RTL과 달리 자동 diff 분류기가 없어, 이 agent의 프로즈 기반 판단이 부정확하거나 일관성이 없으면 "그럴듯한 감"에 불과해질 위험 |
| **SUCCESS** | 새 컴포넌트/시퀀스 클래스 도입이 필요한 경우와 기존에 접어도 되는 경우를 재사용 범위 기준으로 정확히 구분, UVM 과잉/과소 적용 사례를 실제로 잡아냄, 3안 이상 ADR + adversarial cross-review 산출, `verilog-tb-coder`/`verilog-tb-reviewer` 양쪽에서 자연스럽게 route됨 |
| **SCOPE** | `agents/verilog-tb-architect-advisor.md` 신설 + sibling plan 문서 route 갱신. TB 전용 자동 classifier 스크립트 신설은 Out of Scope |

---

## Strategic Alignment Check

### Plan Success Criteria Status

| # | Criteria (Plan §Context Anchor SUCCESS) | Status | Evidence |
|---|---|:---:|---|
| SC-1 | 재사용 범위 기준으로 ARCH/LOCAL 정확히 구분 | ✅ Met | `agents/verilog-tb-architect-advisor.md` §2(L81-107) — 질문표 + UVM/non-UVM 구체 예시 6개 모두 Design §4.2와 일치 |
| SC-2 | UVM 과잉/과소 적용을 실제로 잡아내는 절차 존재 | ✅ Met | §3(L172-187) — `non-uvm-architectures.md` §6 인용 강제, Verdict와 무관하게 항상 수행(§4 하드 제약 L193) |
| SC-3 | 3안 이상 ADR + adversarial cross-review 산출 | ✅ Met | §2.1(L115-127)/§2.2(L129-170) — RTL architect-advisor와 동형, fresh-context Agent 호출 명시 |
| SC-4 | `verilog-tb-coder`/`verilog-tb-reviewer` 양쪽에서 자연스럽게 route | ✅ Met (수정 후) | 최초 gap-detector 실행 시 `verilog-tb-reviewer.plan.md`에 dangling reference 2곳 발견 → 이 세션에서 즉시 수정 완료(아래 §2 참조) |

**Success Rate**: 4/4 criteria met (수정 반영 후)

### Decision Record Verification

| Source | Decision | Followed? | Deviation |
|--------|----------|:---:|---|
| [Plan] | UVM 적정성 판단은 ADR/adversarial cross-review 없이 권고문으로만 종결 | ✅ | 없음 — §3(L185-186)에서 명시적으로 확인 |
| [Design] | Option C(통합 입력·분리 출력) 채택 | ✅ | 판단 절차는 순차 수행(§2→§3), 출력은 두 섹션 분리(§5) — Design §2.1 다이어그램과 일치 |
| [Design] | Task() 입력은 자유 형식 프롬프트, formal 스키마 없음 | ✅ | §1(L60-79) 권장 4요소 표만 제공, 강제 파라미터 없음 |

---

## 1. Gap Analysis (Design vs Implementation)

### 1.1 Structural Match — 100%

| Design §8.2 Implementation Order 항목 | 구현 위치 | 상태 |
|---|---|:---:|
| Frontmatter(name/description/tools/model) | L1-25 | ✅ |
| "0. 기준"(3개 skill 전체 Read) | L37-58 | ✅ |
| §1 입력 모드(P-only + 권장 프롬프트) | L60-79 | ✅ |
| §2 책임분해(재사용범위표+구체예시) | L81-107 | ✅ |
| §2.0.5 evidence recall | L109-113 | ✅ |
| §2.1 후보+ADR | L115-127 | ✅ |
| §2.2 adversarial cross-review | L129-170 | ✅ |
| §3 UVM 적정성(Verdict 독립) | L172-187 | ✅ |
| §4 하드 제약 | L189-197 | ✅ |
| §5 산출물 형식 | L199-210 | ✅ |
| §6 정직한 한계 | L212-226 | ✅ |

### 1.2 Functional Depth — 98%

**가장 중요한 확인(Option C 위반 여부)**: §3(L185-186)이 "이 축은 ADR도 adversarial cross-review도
발동하지 않는다"를 명시적으로 서술 — Design의 Option C 채택 근거를 정확히 구현. §4 하드 제약(L193)이
"§3 UVM 적정성 판정을 §2 Verdict와 무관하게 생략하지 말 것"으로 이를 다시 강제 — 이중 방어 확인.

- 재사용범위 판단표 + UVM/non-UVM 구체 예시(§2, L87-104) — Design §4.2와 완전 일치
- Tool 목록/model: `Read, Glob, Grep, Bash, Agent, mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls` + `model: opus`(L23-24) — Plan FR-02와 정확히 일치
- Adversarial cross-review STEP 0(L143-147)이 `non-uvm-architectures.md` Read를 명시 — Design §4.4와 일치
- 모든 섹션이 placeholder 없이 실제 내용으로 채워짐

**Minor**: Plan FR-12/Design §8.2 step 8의 "install.py AGENTS 목록에 등록" 문구가 실제 메커니즘(별도
목록 없음, `agents/*.md` glob 자동 인식)과 달랐음 — agent 파일 자체의 결함은 아니며 문서 정정 사항.
**이 세션에서 Plan 문서 FR-12/§7.1을 정정 완료.**

### 1.3 Contract/Consistency Match — 89% → 수정 후 ~98%

| 확인 대상 | 최초 발견 상태 | 조치 |
|---|---|---|
| `verilog-tb-coder.plan.md` §2.1/FR-08(c) | ✅ 정합(route 갱신 완료, Version History 0.5) | 조치 불필요 |
| `verilog-tb-reviewer.plan.md` §2.1/§2.2/FR-08/§4.4 | ✅ 정합(정상 갱신됨) | 조치 불필요 |
| `verilog-tb-reviewer.plan.md` §1.2 L69 | ❌ dangling — "TB용 architect-advisor는 없으므로, 발견 시 사람에게 직접 refer한다" | **수정 완료** — `verilog-tb-architect-advisor`로 route하도록 정정 |
| `verilog-tb-reviewer.plan.md` §정합성 유지 L27 | ⚠️ 애매 — "이 agent도 …스스로 판정하지 않고 사람에게 refer한다" | **수정 완료** — `verilog-tb-architect-advisor`로 route하도록 정정 |
| `install.py --only agents --dry-run` | ✅ `verilog-tb-architect-advisor.md` 정상 인식 확인 | 조치 불필요 |
| `chip-verification` skill 경로 정합 | ✅ 오타 없음, `SKILLS` 배포 목록에 포함 확인 | 조치 불필요 |

### 1.4 Match Rate Summary

```
┌─────────────────────────────────────────────┐
│  Structural Match Rate:  100%                │
│  Functional Match Rate:   98%                │
│  Contract Match Rate:     89% → 98%(수정 후) │
│  ─────────────────────────────────────────── │
│  Overall Match Rate (최초): 94.8%            │
│  Overall Match Rate (수정 후): ~99%          │
│  = (Structural × 0.2) + (Functional × 0.4)  │
│    + (Contract × 0.4)   [static-only, no L1-L3 suite] │
└─────────────────────────────────────────────┘
```

---

## 2. Recommended Actions

### 2.1 완료된 조치 (이 세션 내 즉시 수정 — Checkpoint 5 "지금 모두 수정" 선택)

| Priority | Item | File | 상태 |
|---|---|---|---|
| 🟡 Important | dangling reference 정정 — "architect-advisor 없음" 서술 제거 | `verilog-tb-reviewer.plan.md:69` | ✅ 완료 |
| 🟢 Minor | "사람에게 refer" → route 문구 정정 | `verilog-tb-reviewer.plan.md:27` | ✅ 완료 |
| 🟢 Minor | install.py 메커니즘 오기술 정정(FR-12, §7.1) | `verilog-tb-architect-advisor.plan.md` | ✅ 완료 |

### 2.2 후속 (Plan §5.1 Definition of Done 잔여 항목 — 실사용 검증)

Plan/Design 문서가 이미 "수동 검증" 대상으로 명시한 항목이며, 이 gap analysis는 정적 문서/구조
비교만 다룬다. 실제 시나리오 실행 검증(Design §7 시나리오 1~8)은 QA 단계 또는 실전 사용 중 별도로
수행 권장.

---

## 3. Next Steps

- [x] Critical/Important gap 수정 완료
- [ ] Match Rate ≥ 90% 확인 완료 → `/pdca report verilog-tb-architect-advisor`로 진행 가능
- [ ] (선택) Design §7 수동 시나리오 1~8 실전 검증은 QA/실사용 단계에서 진행

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-21 | 초안 — gap-detector 최초 실행(94.8%) + Checkpoint 5 "지금 모두 수정" 반영 후 재확인(~99%) | HSLEE |
