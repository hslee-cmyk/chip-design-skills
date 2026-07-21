# verilog-tb-architect-advisor Planning Document

> **Summary**: TB(테스트벤치)/UVM 환경의 구조적 경계(새 컴포넌트·시퀀스 클래스 vs 기존에 접기)와 검증 방법론 적정성(UVM 도입 여부·과잉/과소 gearing)을 판단하는 read-only agent. `verilog-rtl-architect-advisor`와 정확히 대칭되는 TB 쪽 자매 agent이며, `verilog-tb-coder`(구현자)/`verilog-tb-reviewer`(정확성 최종 검증자)가 이미 "구조적 변경으로 보이면 사람에게 직접 refer"로 남겨둔 갭을 메운다. UVM 기반 TB뿐 아니라 legacy/non-UVM(class-based 또는 flat) 테스트벤치도 판단 대상에 포함한다.
>
> **Project**: chip-design-skills
> **Version**: 0.1
> **Author**: HSLEE
> **Date**: 2026-07-21
> **Status**: Draft

---

## ⚠️ 정합성 유지 — 이 문서를 고치기 전에 반드시 읽을 것

이 agent는 새 cross-repo 계약을 추가하지 않는다(RTL의 `verilog-rtl-architect-advisor`와 달리 xcelium-mcp `/sim` 워크플로우에 직접 걸리지 않음 — `verilog-tb-coder`/`verilog-tb-reviewer`가 이미 그 인터페이스를 소유). 대신 이 프로젝트 내부의 두 자매 plan 문서와 정합성을 유지해야 한다.

### 이 repo 내 관련 문서 (수정 필요 지점 포함)

| 문서 | 현재 상태 | 이 agent 신설 후 변경 필요 지점 |
|------|----------|--------------------------------|
| `docs/01-plan/features/verilog-tb-coder.plan.md` | FR-08(c): "새 시퀀스 클래스/UVM 컴포넌트 추가"처럼 보이면 STOP-and-Ask(사람에게 직접) | STOP-and-Ask 시 **이 agent로 route**하도록 갱신(사람은 이 agent의 ADR을 보고 최종 결정) |
| `docs/01-plan/features/verilog-tb-reviewer.plan.md` | §4.4 TB-ARCH-SUSPECT: "TB용 architect-advisor가 없으므로 직접 사람에게 refer" | `[TB-ARCH-SUSPECT]` 발견 시 **이 agent로 route**하도록 갱신 |
| `skills/chip-verification/SKILL.md` + `references/non-uvm-architectures.md` | 이번 세션에 이미 갱신 완료 — 듀얼탑 아키텍처를 UVM-비종속으로 일반화, legacy/flat/class-based 패턴·의사결정 기준·안티패턴 추가 | 이 agent의 "0. 기준" 정본으로 그대로 소비 |

### 계약 요약 (2026-07-21 시점)

**왜 신설하는가**: `verilog-tb-coder`/`verilog-tb-reviewer`(둘 다 이 repo, `2026-07-10` 세션에서 plan 작성)는 각자 "구조적 변경으로 보이는 항목"을 감지하지만, 둘 다 명시적으로 "TB용 architect-advisor가 없으므로 사람에게 직접 refer"라고 YAGNI 처리했다(당시 evidence base 부재). 이후 사용자가 "testbench도 UVM 환경으로 가면 architecturing을 잘 해야 구조적으로 확장이 쉽고 재활용성이 높다"고 지적했고, RTL 쪽에 이미 있는 "구조 경계 판단 + ADR + adversarial cross-review" 체계(`verilog-rtl-architect-advisor`)가 TB 쪽에 없다는 것이 실제 갭임을 확인했다.

**RTL과의 핵심 차이 — 이 agent가 반드시 처리해야 하는 두 축**:
1. **구조적 경계**(RTL과 동형): 새 UVM agent/component, 새 virtual sequence 클래스, 새 interface, scoreboard/predictor 구조 변경 vs 기존에 접기.
2. **방법론 적정성**(RTL에는 없는 TB 고유 축, 사용자 확인 완료): UVM 도입 자체가 이 프로젝트/이 IP에 적정한가 — 소규모 IP에 UVM을 과잉 적용하거나, 반대로 재사용 범위가 이미 팀 경계를 넘었는데 flat/legacy 구조를 고집하는 과소 적용 모두를 판단 대상에 포함한다(`references/non-uvm-architectures.md` §6 의사결정 기준을 근거로 사용).

**RTL과 달리 자동 classifier가 없다**: `boundary-classifier.py`(RTL diff에서 구조 신호를 뽑는 자동 도구)에 대응하는 TB/SV 전용 자동 분류 도구는 만들지 않는다(Out of Scope, §2.2) — TB 구조 판단은 diff 신호보다 "재사용 범위"·"동시성/lifetime"·"방법론 적정성"이라는 판단적 요소가 크고, RTL의 P-모드(plan 산문에서 프로즈로 판단)와 동일한 방식을 시작점으로 삼는다. 자동화는 evidence가 쌓인 뒤 후속 검토.

**방법론 출처(중복 금지)**: TB 아키텍처 지식을 이 agent의 system prompt에 복사하지 않는다 — `verilog-tb-analyst`/`verilog-tb-coder`/`verilog-tb-reviewer`가 이미 확립한 "0. 기준" 컨벤션을 재사용해 `chip-verification`(듀얼탑+비-UVM 패턴, 이번 세션에 확장 완료) / `uvm-verification`(UVM 컴포넌트 세부) / `verilog-rtl`(SV 문법) skill을 런타임에 전체 Read한다.

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | TB/UVM 구조적 변경 판단(새 컴포넌트 vs 기존에 접기)과 UVM 도입 적정성 판단을 전담하는 agent가 없어, `verilog-tb-coder`/`verilog-tb-reviewer`가 감지한 구조적 변경 의심이 아무 판단 프레임워크 없이 그때그때 사람 감으로 처리되고 있었다. Legacy/non-UVM TB에 대한 아키텍처 지식도 프로젝트 skill에 없었다(UVM 전용으로만 문서화돼 있었음) |
| **Solution** | `verilog-rtl-architect-advisor`와 대칭되는 read-only 구조 판단 agent 신설 — 책임 분해(재사용 범위 기준) + evidence 기반 recall + 3안 이상 ADR + adversarial cross-review. UVM 기반/non-UVM class-based/flat legacy TB 모두를 판단 대상으로 포함(선행 조사로 `chip-verification` skill에 legacy 아키텍처 패턴 문서화 완료) |
| **Function/UX Effect** | `verilog-tb-coder`(구현 전 STOP-and-Ask)와 `verilog-tb-reviewer`(`[TB-ARCH-SUSPECT]` 발견)가 사람에게 직접 넘기던 것을 이 agent로 route — 이 agent는 구조 경계 여부(ARCH/LOCAL 상당)와 UVM 도입 적정성을 함께 판단해 ADR stub + 후보 비교 + 추천안(결정은 사람)을 산출 |
| **Core Value** | TB/UVM 환경도 RTL과 동급의 구조적 governance를 가지게 되어, "재사용 안 되는 TB가 쌓이는" 문제와 "UVM을 과잉/과소 적용하는" 문제 모두를 사람이 결정을 내리기 전에 구조화된 근거로 보여준다 |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | `verilog-tb-coder`/`verilog-tb-reviewer` 둘 다 구조적 변경 의심을 감지만 하고 판단 프레임워크 없이 사람에게 직접 넘기도록 설계됨(YAGNI로 미뤄둔 갭). RTL에는 이미 이 역할(`verilog-rtl-architect-advisor`)이 있어 비대칭 |
| **WHO** | `verilog-tb-coder`(구현 전 STOP-and-Ask 시 경유), `verilog-tb-reviewer`(`[TB-ARCH-SUSPECT]` 발견 시 경유), 그리고 이들을 거치지 않고 TB/UVM plan·design 문서를 직접 검토받고 싶은 사람 |
| **RISK** | TB 구조 판단은 RTL과 달리 자동 diff 분류기가 없어, 이 agent의 프로즈 기반 판단이 부정확하거나 일관성이 없으면 "그럴듯한 감"에 불과해질 위험 — RTL의 P-모드(구조 delta 선언 → baseline 대조)와 동일한 엄격함 필요 |
| **SUCCESS** | 새 컴포넌트/시퀀스 클래스 도입이 필요한 경우와 기존에 접어도 되는 경우를 재사용 범위 기준으로 정확히 구분, UVM 과잉/과소 적용 사례를 실제로 잡아냄, 3안 이상 ADR + adversarial cross-review 산출, `verilog-tb-coder`/`verilog-tb-reviewer` 양쪽에서 자연스럽게 route됨 |
| **SCOPE** | `agents/verilog-tb-architect-advisor.md` 신설 + `install.py` 등록 + `verilog-tb-coder.plan.md`/`verilog-tb-reviewer.plan.md`의 route 대상 갱신(Impact Analysis §7). TB 전용 자동 classifier 스크립트 신설은 Out of Scope |

---

## 1. Overview

### 1.1 Purpose

TB/UVM plan·design 문서 또는 구현 직전 선언된 구조적 delta("새 UVM agent 추가", "새 virtual sequence 클래스", "scoreboard를 어떻게 나눌지" 등)를 입력받아, (1) 이것이 구조적 경계를 넘는 변경인지, (2) 이 프로젝트/IP에 UVM 도입이 적정한지(과잉/과소) 판단하고, ARCH로 판단되면 3안 이상의 candidate + ADR + adversarial cross-review를 생성해 사람에게 escalate한다. 구현하지 않고, partitioning을 스스로 결정하지 않는다.

### 1.2 Background

`verilog-rtl-architect-advisor`는 이 repo의 "architectural gate" 컨벤션을 확립해뒀다 — 책임 분해(§2.0, concurrency/lifetime 기준 DEFAULT-FLIP) → evidence 기반 recall(§2.0.5) → 3안 이상 후보 + ADR(§2.1) → fresh-context adversarial cross-review(§2.2) → 추천안(결정은 사람). `verilog-tb-architect-advisor`는 이 골격을 TB 도메인에 재사용하되, 다음 두 지점에서 다르다:

- **책임 분해 기준의 대응 개념**: RTL의 "host FSM과 동시에 다른 lifetime/rate로 도는가"(concurrency/lifetime) 대신, TB는 "**재사용 범위가 현재 테스트케이스/컴포넌트 하나를 넘는가**"가 1차 기준이다(`references/non-uvm-architectures.md` §7 안티패턴 표의 "판단 규칙"과 동일 원칙 — 재사용 범위가 1개를 넘는 순간 분리 후보가 default가 된다). 여기에 UVM 환경이면 "독립적 phase/objection/virtual sequencer arbitration이 필요한가"라는 UVM 고유 축이 추가된다.
- **자동 classifier 부재**: `boundary-classifier.py` 같은 diff 기반 자동 분류 도구가 없다 — 이 agent는 RTL의 P-모드(plan 산문에서 선언된 구조적 delta를 baseline과 대조하는 프로즈 판단)를 유일한 입력 모드로 삼는다. C-모드(commit diff 자동 분류)는 이 최초 버전 Out of Scope.
- **두 번째 판단 축(UVM 도입 적정성)**: RTL architect-advisor에는 대응 개념이 없다 — RTL은 "이미 RTL로 구현하기로 정해진 것"의 구조만 판단하지만, TB는 "UVM으로 갈지 말지" 자체가 이 프로젝트에서 반복적으로 오판되기 쉬운 결정이라는 것이 이번 조사(`references/non-uvm-architectures.md` §1, §6)로 확인됐다.

### 1.3 Related Documents

- **대칭 agent(다른 도메인, 동일 컨벤션)**: `agents/verilog-rtl-architect-advisor.md` — 책임 분해·evidence recall·3안 ADR·adversarial cross-review 골격을 벤치마크(단, `boundary-classifier.py`/`bug-class-router.py`/RTL taxonomy는 이식하지 않음)
- **호출자(route 갱신 대상)**: `verilog-tb-coder.plan.md`(FR-08(c)), `verilog-tb-reviewer.plan.md`(§4.4 TB-ARCH-SUSPECT)
- **지식 정본(이번 세션에 신규/갱신)**: `skills/chip-verification/SKILL.md` + `skills/chip-verification/references/non-uvm-architectures.md`(dual-top 일반화, flat/legacy 패턴, 레이어드 원칙, 의사결정 기준, 안티패턴 — 외부 조사 기반, 출처 명시)
- **자매 agent(동일 도메인)**: `agents/verilog-tb-analyst.md`(구조 분석서 작성, read-only), `verilog-tb-coder`(구현), `verilog-tb-reviewer`(정확성 최종 검증) — 넷이 합쳐 RTL 쪽 analyst/coder/reviewer/architect-advisor 4-agent 체계와 대칭을 이룸

---

## 2. Scope

### 2.1 In Scope

- [ ] `agents/verilog-tb-architect-advisor.md` 신규 작성 — `verilog-rtl-architect-advisor.md`의 "책임 분해 → evidence recall → 3안 ADR → adversarial cross-review → 추천(결정은 사람)" 골격을 TB 도메인으로 재구성
- [ ] "0. 기준 — 시작 시 반드시 로드": `~/.claude/skills/chip-verification/SKILL.md`(전체, 이번 세션에 확장된 듀얼탑+non-UVM 패턴 포함) / `~/.claude/skills/uvm-verification/SKILL.md`(전체) / `~/.claude/skills/verilog-rtl/SKILL.md`(전체, SV 문법) — `verilog-tb-analyst`/`coder`/`reviewer`와 동일한 부분로딩 금지 원칙
- [ ] Tool 목록: `Read, Glob, Grep, Bash, Agent`(adversarial cross-review용 별도 Agent 호출) + `mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls`(원격 TB 소스 read-only 확인, `verilog-tb-analyst`/`coder`와 동일 근거)
- [ ] **입력 모드**: RTL P-모드와 동일 — TB/UVM 변경을 제안하는 plan/design 문서, 또는 `verilog-tb-coder`/`verilog-tb-reviewer`가 route한 "구조적 변경 의심" 선언(자연어, 자유 형식)을 입력으로 받는다. Commit diff 자동 분류(C-모드 대응)는 Out of Scope
- [ ] **책임 분해(§4.1에서 상세)**: 재사용 범위(현재 테스트케이스/컴포넌트 하나에 한정되는가, 여러 곳에서 쓰이는가)를 1차 기준으로, UVM 환경이면 독립 phase/objection/virtual sequencer arbitration 필요 여부를 2차 기준으로 판단
- [ ] **UVM 도입 적정성 판단(§4.2에서 상세)**: `references/non-uvm-architectures.md` §6 의사결정 기준(재사용 범위, 팀/프로젝트 수명, factory override 실제 필요 여부 등)을 근거로 과잉/과소 gearing 여부를 판단
- [ ] evidence 기반 recall — 이 repo에 이미 있는 `.ai/analysis/tb_*.analysis.md`(구조 정본), 과거 ADR(`.ai/adr/`), graphify(가용 시)를 참조해 유사 분할의 전례를 회수
- [ ] 3안 이상 candidate + ADR stub(`.ai/adr/NNNN-{topic}.md`, RTL과 동일 템플릿 재사용) — anti-anchoring(제안안을 특권화하지 않음) 원칙 동일 적용
- [ ] fresh-context adversarial cross-review — 후보 수만큼 별도 Agent 호출, RTL §2.2와 동일 절차(맥락 오염 금지)
- [ ] 출력: Mode(P만 지원) / 재사용범위 판단표 / Verdict(ARCH/LOCAL) + UVM 적정성 판정(과잉/적정/과소) / ARCH면 ADR 경로 + 3안 + adversarial cross-review 표 + 추천안(결정은 사람) / 다음 행동
- [ ] `install.py` 배포 목록에 등록
- [ ] `verilog-tb-coder.plan.md` FR-08(c), `verilog-tb-reviewer.plan.md` §4.4를 "사람에게 직접 refer" → "이 agent로 route"로 갱신(Design/Do 단계에서 실제 문서 반영, 이 Plan 문서는 그 필요성만 명시)

### 2.2 Out of Scope

- **TB/SV 전용 자동 구조-delta classifier(`boundary-classifier.py` 대응물) 신설** — YAGNI, evidence 축적 전까지 프로즈 판단(P-모드)만 지원
- **C-모드(commit diff 자동 분류) 지원** — 자동 classifier가 없으므로 이 최초 버전에서는 불가능, 후속 검토
- **RTL taxonomy(T1-T9)/`bug-class-router.py`/pre-merge-check.py 이식** — 카테고리 오류(RTL 구조 신호와 TB 구조 신호는 다름)
- **TB 코드 수정, 구현** — read-only, 구현은 `verilog-tb-coder`/사람 소관
- **정확성 검증(spec 정당화, checker 완화 탐지)** — `verilog-tb-reviewer` 소관, 이 agent는 구조만 판단
- **xcelium-mcp `/sim` 워크플로우 직접 연동** — 이 agent는 xcelium-mcp의 fix_target 판정 로직과 무관, `verilog-tb-coder`/`reviewer`를 통해서만 간접적으로 route됨

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `agents/verilog-tb-architect-advisor.md` frontmatter — `verilog-rtl-architect-advisor.md`와 유사 구조(`name`/`description`(Use it when/Do NOT use for/Triggers)/`tools`/`model`). Triggers 예시: "TB 아키텍처 검토", "새 UVM 컴포넌트", "새 시퀀스 클래스", "UVM 도입 판단", "TB-ARCH-SUSPECT", "legacy TB 구조", "non-UVM 구조 검토" | High | Pending |
| FR-02 | Tool 목록: `Read, Glob, Grep, Bash, Agent, mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls` | High | Pending |
| FR-03 | "0. 기준"에 `chip-verification`/`uvm-verification`/`verilog-rtl` skill 전체 Read를 MUST로 명시(부분로딩 금지) | High | Pending |
| FR-04 | 입력 모드는 P-모드(plan/design 문서 또는 route된 구조 변경 선언, 자연어)만 지원 — C-모드(commit diff)는 미지원을 frontmatter/본문에 명시 | High | Pending |
| FR-05 | 책임 분해 절차: 재사용 범위(1차) + UVM 환경이면 독립 phase/objection/arbitration 필요 여부(2차)를 표로 판단 — RTL §2.0 책임 분해표와 동형의 표 사용 | High | Pending |
| FR-06 | UVM 도입 적정성 판단 절차: `references/non-uvm-architectures.md` §6 기준표를 근거로 과잉/적정/과소 gearing 판정 — 근거를 반드시 그 표의 조건 항목을 인용해 서술(추측 금지) | High | Pending |
| FR-07 | evidence 기반 recall: `.ai/analysis/tb_*.analysis.md`, `.ai/adr/`, graphify(가용 시) 참조 — RTL §2.0.5와 동일 절차 | Medium | Pending |
| FR-08 | ARCH 판정 시 3안 이상 candidate + ADR stub 작성(`.ai/adr/NNNN-*.md`, 기존 `adr-template.md` 재사용) — anti-anchoring 원칙(제안안 특권화 금지) | High | Pending |
| FR-09 | fresh-context adversarial cross-review: 후보 수만큼 별도 Agent 호출, 맥락 오염 금지(RTL §2.2 절차 그대로 재사용) | High | Pending |
| FR-10 | 출력 형식: Mode / 책임분해표 / Verdict(ARCH·LOCAL) / UVM 적정성 판정 / (ARCH면) ADR 경로+3안+cross-review 표+추천안 / 다음 행동 — RTL §5 산출물 형식과 동형 | Medium | Pending |
| FR-11 | 하드 제약: 구현 금지, partitioning 결정 금지(escalate), UVM 도입 여부 최종 결정 금지(판단 근거만 제시, 결정은 사람) | High | Pending |
| FR-12 | `agents/verilog-tb-architect-advisor.md` 배포 확인 — **(2026-07-21 갱신)** `install.py`에 별도 AGENTS 목록은 없음(`install_agents`가 `agents/*.md`를 frontmatter 유무로 glob 자동 인식), `--dry-run`으로 인식 여부만 확인 | Medium | Done |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|---------------------|
| 컨벤션 일관성 | `verilog-rtl-architect-advisor.md`(책임분해/recall/ADR/adversarial cross-review 골격)와 구조·톤 일관 | 두 agent 파일 diff 리뷰 |
| 지식 소스 정합성 | UVM 적정성 판단이 `references/non-uvm-architectures.md` §6 기준표를 실제로 인용하는지(추측 금지) | 의도적 UVM 과잉/과소 시나리오로 수동 검증 |
| Route 정합성 | `verilog-tb-coder`/`verilog-tb-reviewer`의 route 대상 갱신과 이 agent의 입력 형식(자유 형식 프롬프트)이 일치 | 세 plan 문서 교차 대조 |

---

## 4. `verilog-tb-architect-advisor`의 자체 규율 (Design 단계에서 agent 파일로 구체화할 핵심 내용)

### 4.1 책임 분해 — 재사용 범위 기준 (RTL §2.0 DEFAULT-FLIP의 TB 대응)

RTL은 "host FSM과 동시에, 다른 lifetime/rate로 도는 책임"을 만나면 분리가 default로 뒤집힌다(DEFAULT-FLIP). TB는 이 축이 성립하지 않는 경우가 많다(TB 컴포넌트는 애초에 병렬 실행되는 경우가 흔함). 대신 이번 조사(`references/non-uvm-architectures.md` §7)로 확인된 실질적 기준은 **재사용 범위**다:

| 질문 | 답 = 분리(새 컴포넌트/클래스)가 default | 답 = 기존에 접기가 default |
|------|------------------------------------------|------------------------------|
| 이 검증 관심사(체커/드라이버/시퀀스)가 현재 테스트케이스 하나에서만 쓰이는가? | 아니오(2개 이상에서 재사용) → **분리** | 예 → 접기 |
| (UVM 환경) 독립적인 phase 제어·objection·virtual sequencer arbitration이 필요한가? | 예 → **분리(새 agent/컴포넌트)** | 아니오 → 접기 |
| 기존 컴포넌트에 넣으면 그 컴포넌트가 서로 다른 프로토콜/관심사를 동시에 책임지게 되는가? | 예 → **분리** | 아니오 → 접기 |

이 표가 비어있거나 모든 질문이 "접기" 방향이면 state-fold(기존에 접기)가 정당. 하나라도 "분리" 방향이면 새 컴포넌트/클래스를 후보 A로 포함한다(RTL의 "별도 FSM을 A안으로 강제 포함"과 동형).

### 4.2 UVM 도입 적정성 — 과잉/과소 gearing 판단

`references/non-uvm-architectures.md` §6 "UVM vs Non-UVM class-based(G5)" 기준표를 그대로 판단 근거로 쓴다:

- **과잉(over-gearing) 신호**: 소규모 IP(프로토콜 1~2개, 프로젝트 수명 6개월 미만)에 UVM 전체 스택(factory/config_db/phase/RAL)을 요구하는 plan — factory override가 실제로 필요한지 먼저 확인
- **과소(under-gearing) 신호**: 이미 여러 프로젝트/팀이 재사용 중이거나 SoC 레벨 통합이 예정된 VIP인데 flat/directed 구조를 고집하는 plan
- 판정은 반드시 위 기준표의 구체 조건 문구를 인용해 서술 — "UVM이 나은 것 같다"류의 근거 없는 판단 금지(RTL의 anti-tautology 원칙과 동일 정신)

### 4.3 Adversarial Cross-Review 프롬프트 골격 (RTL §2.2 재사용, STEP 0만 교체)

```
【STEP 0 — 반드시 먼저】
Read ~/.claude/skills/chip-verification/SKILL.md 와
~/.claude/skills/chip-verification/references/non-uvm-architectures.md 를 Read 툴로 적재한다.
(UVM 컴포넌트 세부가 후보에 포함되면 ~/.claude/skills/uvm-verification/SKILL.md 도 Read)
Skill 파일을 Read하지 않고 검토를 시작하는 것은 금지한다.

【STEP 1 — 역할】
너는 TB/UVM 아키텍처 안 [X]의 adversarial reviewer다.
[X]의 치명 약점을 찾고, 나머지 후보 [Y], [Z]와 비교해 [X]가 열등한 이유를 구체적으로 서술하라.
재사용 범위·UVM 적정성·유지보수성·verifiability를 공격 기준으로 쓴다.

【STEP 2 — 출력】
{ "weakness": ["…"], "mitigant": ["…"], "residual_risk": "低|中|高" }
```

---

## 5. Success Criteria

### 5.1 Definition of Done

- [ ] `agents/verilog-tb-architect-advisor.md` 작성 완료 — §4의 두 판단 축(구조 경계·UVM 적정성)이 구체 절차로 명시, ADR/adversarial cross-review 형식 포함
- [ ] `install.py` 배포 등록 + 배포 테스트
- [ ] `verilog-tb-coder.plan.md` FR-08(c), `verilog-tb-reviewer.plan.md` §4.4의 route 대상 갱신을 Next Steps에 반영(Design/Do 단계에서 실제 문서 수정)
- [ ] 의도적 시나리오(소규모 IP에 UVM 풀스택 요구 / 이미 재사용 중인데 flat 고집 / 새 컴포넌트가 필요한데 접으려는 시도) 각각으로 이 agent가 올바른 방향으로 escalate하는지 수동 검증

### 5.2 Quality Criteria

- [ ] `verilog-rtl-architect-advisor`와 구조·톤 일관(§4 판단 골격 diff 리뷰)
- [ ] `verilog-tb-analyst`/`coder`/`reviewer`와 트리거 키워드 중복 최소화(이 agent는 "구조 판단"에만 고유하게 트리거)
- [ ] `references/non-uvm-architectures.md`를 실제로 인용하는 판단 로직인지(추측성 판단이 아닌지) 확인

---

## 6. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 자동 classifier가 없어 이 agent의 판단이 일관성 없는 "감"에 그침 | High | Medium | §4.1/§4.2를 반드시 인용 가능한 근거(재사용범위 질문표, non-uvm-architectures §6 기준표)로 강제, 근거 없는 판단은 STOP-and-Ask 쪽으로 편향(RTL의 false-positive escalation 원칙 재사용) |
| UVM 적정성 판단이 `references/non-uvm-architectures.md`의 판단을 그대로 답습해 프로젝트별 맥락(예: 이 프로젝트의 실제 팀 규모·수명)을 반영 못함 | Medium | Medium | 기준표의 조건은 "출발점"이고, 프로젝트 고유 맥락(CLAUDE.md, 과거 ADR)을 반드시 함께 인용하도록 §4.2에 명시 |
| `verilog-tb-coder`/`verilog-tb-reviewer`의 route 갱신이 이 Plan 완료 후 누락되어, 여전히 "사람에게 직접 refer"로 남을 위험 | Medium | Low | Next Steps에 두 문서 갱신을 명시적 항목으로 포함, Design 단계 완료 조건에 추가 |
| non-UVM 패턴 조사가 이 프로젝트의 실제 legacy TB 사례 없이 순수 외부 문헌 기반이라 현실과 괴리될 위험 | Low | Medium | evidence recall(§4.1/FR-07)에서 이 repo `.ai/analysis/tb_*.analysis.md`/과거 ADR을 함께 인용하도록 요구 — 프로젝트 사례가 쌓일수록 외부 문헌 의존도 감소 |

---

## 7. Impact Analysis

### 7.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|---------------------|
| `agents/verilog-tb-architect-advisor.md` | 신규 파일 | 신규 agent 정의 |
| `install.py` | 스크립트(변경 없음) | 별도 목록 편집 불필요 — `agents/*.md` glob 자동 인식 확인만(2026-07-21) |
| `skills/chip-verification/SKILL.md` | 수정(이번 세션 완료) | 듀얼탑 아키텍처 UVM-비종속화, 트리거 키워드 추가, 참조 파일 목록 갱신 |
| `skills/chip-verification/references/non-uvm-architectures.md` | 신규 파일(이번 세션 완료) | legacy/non-UVM TB 아키텍처 패턴, 의사결정 기준, 안티패턴 |
| `docs/01-plan/features/verilog-tb-coder.plan.md` | 수정 필요(미완료) | FR-08(c) route 대상을 "사람 직접" → "이 agent" |
| `docs/01-plan/features/verilog-tb-reviewer.plan.md` | 수정 필요(미완료) | §4.4 TB-ARCH-SUSPECT route 대상을 "사람 직접" → "이 agent" |

### 7.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| **예정 소비자**: `verilog-tb-coder`(FR-08(c) STOP-and-Ask 발동 시) | INVOKE(완성 후) | Task 위임(자유 형식 프롬프트로 구조 변경 의심 내용 전달) | Needs verification — `verilog-tb-coder.plan.md` 갱신 완료 후에만 실제 연결됨 |
| **예정 소비자**: `verilog-tb-reviewer`(§4.4 `[TB-ARCH-SUSPECT]` 발견 시) | INVOKE(완성 후) | Task 위임 | Needs verification — `verilog-tb-reviewer.plan.md` 갱신 완료 후에만 실제 연결됨 |
| **예정 소비자**: 사람이 TB/UVM plan·design 문서를 직접 검토 요청 | INVOKE | `/pdca design` 등에서 TB 아키텍처가 걸린 경우 직접 호출 | Needs verification |

### 7.3 Verification

- [ ] `install.py --only agents` 실행 후 배포 경로 확인
- [ ] `verilog-tb-coder.plan.md`/`verilog-tb-reviewer.plan.md` 갱신 후 route 서술이 이 agent의 입력 형식(자유 형식 프롬프트)과 일치하는지 대조

---

## 8. Convention Prerequisites

### 8.1 Existing Project Conventions

- [x] `agents/verilog-rtl-architect-advisor.md` — 책임분해/recall/ADR/adversarial cross-review 골격 벤치마크
- [x] `skills/chip-verification/references/non-uvm-architectures.md` — 이번 세션에 신규 확보된 non-UVM 판단 근거
- [x] `install.py` agent 배포 스크립트 존재
- [x] `.ai/adr/adr-template.md`(agent-kit) — ADR stub 템플릿 재사용 가능 여부 Design 단계에서 확인

### 8.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| TB "구조적 변경" 재사용범위 기준의 구체 예시 | §4.1에 질문표만 정의 | Design 단계에서 UVM/non-UVM 각각 구체 예시(실제 코드 스니펫)와 함께 확정 | High |
| UVM 적정성 판정의 "과잉/과소" 경계값 | §4.2에 정성적 기준만 정의 | Design 단계에서 `references/non-uvm-architectures.md` §6 표를 그대로 판정 rubric으로 쓸지, 프로젝트별 가중치를 추가할지 확정 | Medium |
| `verilog-tb-coder`/`verilog-tb-reviewer` route 갱신 문구 | 현재 "사람에게 직접" | Design/Do 단계에서 두 문서에 실제 반영 | High |

---

## 9. Next Steps

1. [ ] `/pdca design verilog-tb-architect-advisor` — §4 판단 절차 구체 예시 확정, ADR 템플릿 재사용 여부 확인
2. [ ] `agents/verilog-tb-architect-advisor.md` 작성(`verilog-rtl-architect-advisor.md` 골격 + `references/non-uvm-architectures.md` 지식 결합)
3. [ ] `install.py` 등록 + 배포 테스트
4. [ ] `verilog-tb-coder.plan.md` FR-08(c), `verilog-tb-reviewer.plan.md` §4.4 route 대상 갱신
5. [ ] 의도적 시나리오(UVM 과잉/과소, 구조 분리 필요/불필요) 각각으로 수동 검증

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-21 | 초안 — 사용자가 "TB도 architecturing이 필요하다"고 지적한 것을 계기로, `verilog-tb-coder`/`verilog-tb-reviewer` plan 문서가 이미 남겨둔 "TB용 architect-advisor 부재" 갭을 메우기 위해 신설. `verilog-rtl-architect-advisor` 골격을 벤치마크하되 (1) legacy/non-UVM TB도 커버(선행 조사로 `chip-verification` skill에 `references/non-uvm-architectures.md` 신규 작성 및 SKILL.md UVM-비종속화 완료), (2) 구조 경계 판단에 더해 UVM 도입 적정성(과잉/과소 gearing) 판단 축을 추가 | HSLEE |
| 0.2 | 2026-07-21 | Do 완료 후 gap-detector 검증(Match Rate 94.8%) 결과 반영 — FR-12/§7.1 "install.py AGENTS 목록 등록" 문구가 실제 메커니즘(별도 목록 없음, `agents/*.md` glob 자동 인식)과 달라 정정. `verilog-tb-reviewer.plan.md`의 dangling reference(§1.2 L69 "TB용 architect-advisor는 없으므로", §정합성 유지 L27 "사람에게 refer한다")도 이 세션에서 함께 정정 완료 | HSLEE |
