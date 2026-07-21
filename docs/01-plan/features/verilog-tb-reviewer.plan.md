# verilog-tb-reviewer Planning Document

> **Summary**: `fix_target=tb`로 판정된 fix-implement(구현 주체 무관 — `verilog-tb-coder` 또는 사람)를 독립적으로 검토하는 read-only agent. `verilog-rtl-reviewer`와 정확히 대칭되는 TB 쪽 자매 agent이며, `verilog-tb-coder`가 스스로 수행하는 spec 정당화 self-check을 "빠른 1차 필터"로 두고 이 agent가 "권위 있는 최종 판단"을 내림으로써, 구현 당사자가 자기 작업을 스스로 인증하는 모순(anti-tautology 위반)을 해소한다.
>
> **Project**: chip-design-skills
> **Version**: 0.1
> **Author**: HSLEE
> **Date**: 2026-07-10
> **Status**: Draft

---

## ⚠️ 정합성 유지 — 이 문서를 고치기 전에 반드시 읽을 것

`verilog-tb-coder.plan.md`/`verilog-tb-analyst.plan.md`/`verilog-rtl-debugger.plan.md`와 동일한 cross-repo 계약 구조다. 요구사항 정본은 이 repo가 아니라 **xcelium-mcp**에 있다.

### 요구사항 정본 (xcelium-mcp repo, 절대경로)

| 문서 | 절대경로 | 참조 섹션 | 확인 시점 버전 |
|------|---------|----------|----------------|
| debug workflow v2 (Fix Sub-cycle, fix-review TB 경로 원본) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-debug-workflow-v2.plan.md` | §5.8 "Fix Target: RTL vs TB", §5.8 "4) fix-review"(TB 경로), §4.5 매핑 표 "debug (TB, 근본원인·수정 구현)" 행 | v1.34 (2026-07-10) |

### 계약 요약 (2026-07-10 시점)

**왜 신설하는가**: xcelium-mcp v1.33은 `verilog-tb-coder`(TB 전용 구현 agent) 신설과 함께, 그 agent 자신이 "spec 정당화 self-check"을 수행해 anti-tautology를 방어하도록 설계했다. 그러나 이는 `verilog-rtl-coder`가 이미 확립한 원칙 — "너는 의도(intent)를 스스로 인증하지 않는다. 정확성 property는 Prover가 구현과 독립적으로 저작한다"(coder §6 anti-tautology) — 와 정면으로 모순된다. 구현 당사자가 "내가 쓴 코드가 spec에 맞다"를 스스로 판단하면, 바로 그 판단 자체가 tautology(자기 인증)가 되어 방어 장치로서 무력화될 위험이 있다(사용자 지적: "작성한 agent가 self-check한다는 것은 모순이 있는 것 같다"). 이 agent는 `verilog-tb-coder`(또는 사람)의 TB 구현을 **독립적으로** 재검토해, RTL 쪽의 "coder self-check(구조적 필터) + reviewer/prover 독립 검증(정확성 판단)"이라는 2단 방어 구조를 TB 쪽에도 동일하게 적용한다.

또한 사용자는 "testbench도 architecturing이 가능하고 더 잘 만들게 할 수도 있잖아"라고 지적했다 — 이 agent의 역할은 단순히 "버그를 잡는 것"에 그치지 않고, TB 구조/coverage 관점에서 더 나은 방법이 있는지도 검토 대상에 포함한다(단, architecture를 **결정**하지는 않는다 — RTL의 reviewer가 architect-advisor에 판단을 넘기듯, 이 agent도 구조적 변경으로 보이는 항목은 스스로 판정하지 않고 **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 route한다).

**방법론 출처(중요 — 중복 금지)**: 이 agent는 TB 아키텍처 규칙을 system prompt에 복사해 내장하지 않는다 — `verilog-tb-analyst`/`verilog-tb-coder`가 이미 확립한 "0. 기준 — 시작 시 반드시 로드" 컨벤션을 그대로 재사용해, `verilog-rtl`/`chip-verification`/`uvm-verification` skill을 런타임에 전체 Read한다.

**RTL taxonomy를 이식하지 않는 이유**: `verilog-rtl-reviewer`는 `failure-taxonomy.md`(T1-T9)와 `bug-class-router.py`라는 정교한 도구 체계를 갖고 있지만, 이는 6개 ground-truth RTL 버그의 forensic 분석에서 귀납적으로 도출된 것이다. TB 버그에 대한 동등한 evidence base가 이 생태계에 아직 없으므로, 이 agent는 억지로 그 체계를 흉내 내지 않고 **자기 도메인에 맞는 축소된 검토 항목**(§4)만 가진다 — 필요성이 실전에서 확인되면 후속 feature로 정식 taxonomy를 만들 수 있다(YAGNI).

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | `verilog-tb-coder`(또는 사람)의 TB 구현을 독립적으로 검증하는 agent가 없어, anti-tautology 원칙이 TB 쪽에서만 깨져 있었다 — 구현 당사자의 self-check이 유일한 방어선 |
| **Solution** | `verilog-rtl-reviewer`와 대칭되는 TB 전용 read-only 검토자 신설 — spec 정당화 최종 판단, checker 완화 탐지, 범위 준수, 구조적 변경 의심 refer |
| **Function/UX Effect** | xcelium-mcp `/sim debug`의 `fix_target=tb` fix-implement 완료 직후 이 agent가 자동 호출돼 fix-review 게이트를 채움 — 문제 발견 시 fix-implement로 되돌림, clean이면 `/sim verify`로 진행 |
| **Core Value** | TB fix도 RTL fix와 동급의 "구현자 self-check + 독립 검증자" 2단 방어 구조를 갖게 되어, "TB를 완화해 진짜 RTL 버그를 숨기는" 가장 위험한 실패 양상을 정면으로 방어 |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | `verilog-tb-coder`의 self-check만으로는 anti-tautology를 구조적으로 보장할 수 없음(자기 인증의 모순) |
| **WHO** | xcelium-mcp `/sim` 워크플로우를 사용해 RTL/TB 검증을 수행하는 모든 프로젝트의 AI 에이전트 |
| **RISK** | 이 agent 자신도 spec 참조 없이 "코드가 그럴듯해 보인다"로 안이하게 clean 판정을 내리면 방어선으로서 무력화됨 — RTL reviewer의 "STATIC vs SIM 정직성 계약"과 동급의 엄격함이 필요 |
| **SUCCESS** | 순환 논리(anti-tautology 위반) 근거를 담은 fix-plan/구현을 실제로 잡아내 fix-implement로 되돌림; 정당한 fix는 불필요하게 막지 않음 |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-reviewer.md`) 작성 + `install.py` 배포 등록만 |

---

## 1. Overview

### 1.1 Purpose

`fix_target=tb`의 fix-implement 완료 직후, 그 diff(TB 소스 변경분)를 fix-plan.md(선언된 범위 + 근본원인 소재 판정 근거)와 대조해 spec 정당화·checker 완화·범위 준수·구조적 변경 여부를 독립적으로 검토하고, 문제를 발견하면 fix-implement로 되돌린다.

### 1.2 Background

`verilog-rtl-reviewer`는 이 repo의 "STATIC vs SIM 정직성 계약"(§0), "명시적 라우팅"(SIM-RISK를 가장 싼 신뢰 가능한 owner에게), "architect-advisor와의 역할 분담"(구조 판정은 하지 않고 refer만)이라는 세 가지 설계 축을 확립해뒀다. `verilog-tb-reviewer`는 이 중 **처음과 세 번째 축을 재사용**하고, 두 번째 축(SIM-RISK 라우팅)은 재사용하지 않는다:

- **재사용**: "정적으로 확정 가능한 것과 아닌 것을 구분해 정직하게 보고한다" — TB도 "spec 대비 명백히 어긋남"(정적 확정 가능)과 "실제 동작해봐야 아는 것"(시뮬레이션 필요, `/sim verify`로 위임)을 구분한다.
- **재사용**: "구조적 변경 의심은 스스로 판정하지 않고 refer한다" — **(2026-07-21 갱신)** 신설된 `verilog-tb-architect-advisor`로 route한다(§2.2 Out of Scope).
- **재사용 안 함**: RTL의 SIM-RISK는 Prover/formal, directed sim, STATIC reachability 3개 owner로 정교하게 라우팅되는데, TB 버그의 "시뮬레이션 필요" 판정은 이미 `/sim verify`(xcelium-mcp)라는 단일 owner로 귀결되므로 별도 라우팅 로직이 필요 없다 — 훨씬 단순하다.

### 1.3 Related Documents

- **요구사항 정본**: §정합성 유지 절의 xcelium-mcp 문서
- **대칭 agent(다른 도메인, 동일 컨벤션)**: `agents/verilog-rtl-reviewer.md` — "STATIC vs SIM 정직성 계약", "architect-advisor와의 역할 분담", 보고서/Manifest 구조를 벤치마크(단, T1-T9 taxonomy·`bug-class-router.py`는 이식하지 않음)
- **직접 대응 agent(구현 당사자)**: `agents/verilog-tb-coder.md`(chip-design-skills, 이 문서와 같은 세션에서 함께 갱신) — self-check을 1차 필터로 격하하고 이 agent를 최종 판단자로 참조하도록 이미 갱신됨
- **자매 agent(동일 도메인, 다른 역할)**: `agents/verilog-tb-analyst.md` — "0. 기준" 정본 skill 목록 벤치마크

---

## 2. Scope

### 2.1 In Scope

- [ ] `agents/verilog-tb-reviewer.md` 신규 작성 — `verilog-rtl-reviewer.md`의 "STATIC vs SIM 정직성 계약"·"architect-advisor 역할 분담"·보고서/Manifest 골격을 TB 도메인에 맞게 재구성(taxonomy T1-T9/`bug-class-router.py`는 이식 안 함, §2.2 참조) — 대신 §4의 TB 자체 검토 항목으로 대체
- [ ] "0. 기준 — 시작 시 반드시 로드" 절: `verilog-tb-analyst.md`/`verilog-tb-coder.md`와 동일한 정본 목록 — `~/.claude/skills/verilog-rtl/SKILL.md`(전체), `~/.claude/skills/chip-verification/SKILL.md`(전체), `~/.claude/skills/uvm-verification/SKILL.md`(전체), `~/.claude/skills/ssh-mcp/SKILL.md`(전체, `mcp__ssh__*` 가용 시에만)
- [ ] Tool 목록: `Read, Glob, Grep, Bash, Write` + `mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls`(read-only, `verilog-rtl-reviewer`와 동일하게 Write는 보고서 파일에만 — TB 소스 원격 접근은 read-only 3종으로 충분, `file_write` 불필요)
- [ ] **spec 정당화 최종 판단(§4.1, 이 agent의 핵심 규율)**: fix-plan.md의 "근본원인 소재 판정 근거"와 실제 diff를 대조해, spec/tb 분석서를 실제로 인용하는지, `verilog-tb-coder`의 self-check을 통과했더라도 순환 논리("RTL에 맞춘다")가 남아있지 않은지 **독립적으로 재확인**
- [ ] checker 완화 탐지(§4.2): assertion 삭제, 조건 범위 확장, expected value 완화 등 diff에서 "검증을 약화시키는" 패턴 탐지
- [ ] fix-plan 범위 준수 확인(§4.3): 선언된 `affected_paths` 밖의 변경 여부
- [ ] 구조적 변경 의심 refer(§4.4): 새 시퀀스 클래스/UVM 컴포넌트 추가처럼 보이면 `[TB-ARCH-SUSPECT]`로 표시하고 판정하지 않고 **(2026-07-21 갱신)** 신설된 `verilog-tb-architect-advisor`로 route(그 agent가 재사용범위 판단표+ADR+adversarial cross-review를 거쳐 사람에게 최종 판단을 넘김 — `verilog-tb-architect-advisor.plan.md` 참조)
- [ ] TB 컨벤션 준수 확인(§4.5): `verilog-rtl`/`chip-verification`/`uvm-verification` skill 대비 문법/구조 정합
- [ ] `.ai/analysis/tb_*.analysis.md` 정합성 확인(§4.6): 이 diff 이후에도 분석서가 유효한지, stale이면 `verilog-tb-analyst` 라우팅 권고
- [ ] 보고서 생성(`.ai/reviews/{test}-tb-{YYYYMMDD}.review.md`) + verdict(`clean`/`issues_found`, xcelium-mcp `fix_review.status`와 동일 enum) + Manifest 반환
- [ ] `install.py` 배포 목록에 등록

### 2.2 Out of Scope

- **RTL taxonomy(T1-T9)/`bug-class-router.py`/SIM-RISK 3-way 라우팅 이식** — TB 버그 실패 양상이 범주가 다르고, TB의 "시뮬레이션 필요" 판정은 이미 `/sim verify` 단일 owner로 귀결되므로 다중 라우팅이 불필요
- **TB용 formal 대응 단계 신설** — TB 코드에 자연스러운 formal 검증 대상이 없음(YAGNI)
- **TB용 ARCH/IFACE/LOCAL 자동 classifier 신설** — YAGNI, `verilog-tb-architect-advisor`(2026-07-21 신설)도 자동 classifier 없이 프로즈 기반으로 판단함, 이 문서 범위는 아님
- **`fix_target`(RTL vs TB) 판정 로직 자체** — `verilog-rtl-debugger`(xcelium-mcp 소관)
- **TB 코드 수정** — 이 agent는 read-only, 수정은 `verilog-tb-coder`/사람 소관
- **시뮬레이션 실행/재검증** — `/sim verify`(xcelium-mcp) 소관

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `agents/verilog-tb-reviewer.md` frontmatter — `verilog-rtl-reviewer.md`/`verilog-tb-coder.md`와 유사 구조. Triggers 예시: "TB 리뷰", "fix-review TB", "testcase 검토", "checker 완화 확인" | High | Pending |
| FR-02 | Tool 목록: `Read, Glob, Grep, Bash, Write, mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls`(read-only, Write는 보고서 전용) | High | Pending |
| FR-03 | "0. 기준"에 `verilog-tb-analyst`/`verilog-tb-coder`와 동일한 4~5개 정본 Read 지시(전체 로드, 부분로딩 금지) | High | Pending |
| FR-04 | Task() 입력 파라미터: `fix_plan_path`, `env`, `files_changed`(fix-implement 산출물, 실제 변경 파일 목록), `implementer`(`"verilog-tb-coder"` \| `"human"` — 보고서에 참고용으로만 기록, 검토 엄격도를 다르게 하지 않음: 구현 주체와 무관하게 동일 기준 적용) | High | Pending |
| FR-05 | **spec 정당화 최종 판단(핵심 규율)**: §4.1 절차대로 fix-plan.md의 근거를 spec/tb 분석서 대비 독립 재확인 — self-check을 통과했어도 예외 없이 재검토(defense-in-depth) | High | Pending |
| FR-06 | checker 완화 탐지(§4.2): assertion/조건 제거·완화 diff 패턴 탐지 | High | Pending |
| FR-07 | fix-plan 범위 준수 확인(§4.3) | High | Pending |
| FR-08 | 구조적 변경 의심 시 `[TB-ARCH-SUSPECT]`로 표시하고 판정 대신 **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 refer(§4.4) | High | Pending |
| FR-09 | TB 컨벤션 준수 확인(§4.5), `.ai/analysis/tb_*.analysis.md` 정합성 확인 + stale 시 `verilog-tb-analyst` 라우팅 권고(§4.6) | Medium | Pending |
| FR-10 | 보고서 `.ai/reviews/{test}-tb-{YYYYMMDD}.review.md` 생성(유일한 Write 대상) — Summary/spec 정당화 판정/checker 완화 findings/범위 준수/TB-ARCH-SUSPECT/컨벤션/분석서 상태/Verdict 섹션 포함 | Medium | Pending |
| FR-11 | Manifest 반환: 보고서 경로, verdict(`clean`/`issues_found`), findings 개수, TB-ARCH-SUSPECT 여부, 분석서 상태(+ tb-analyst 라우팅 여부) | Medium | Pending |
| FR-12 | `install.py` AGENTS 목록에 등록 | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|---------------------|
| 독립성 | `verilog-tb-coder`의 self-check 결과에 의존하지 않고 항상 처음부터 재검토 | 리뷰 절차에 "self-check 결과 무시하고 독립 재확인" 명시 여부 확인 |
| Anti-tautology 최종 방어 | 순환 논리 fix-plan을 실제로 걸러내는지 | 의도적 순환 논리 시나리오 테스트 |
| 컨벤션 일관성 | `verilog-rtl-reviewer.md`(STATIC/SIM 계약, 역할 분담)와 구조·톤 일관 | agent 파일 diff 리뷰 |

---

## 4. `verilog-tb-reviewer`의 검토 항목 (Design 단계에서 agent 파일로 구체화할 핵심 내용)

> RTL reviewer의 taxonomy(T1-T9)에 대응하는 TB 자체 항목 — 정식 catalog 파일 없이 이 문서·agent 파일에 직접 정의(evidence base가 아직 없어 YAGNI).

### 4.1 spec 정당화 최종 판단 (가장 중요)

1. fix-plan.md의 "근본원인 소재 판정 근거"를 `verilog-tb-coder`의 self-check 결과와 **무관하게 처음부터** 재확인한다.
2. spec(또는 `.ai/analysis/tb_{env}_*.analysis.md`의 판별 신호/기대값 정의)을 실제로 인용하는지 확인.
3. "RTL이 이렇게 동작하니 TB를 맞춘다"류 순환 논리로 보이면 `[issues_found]`로 종결 — self-check을 통과했어도 예외 없음.

### 4.2 checker 완화 탐지

diff에서 다음 패턴이 있으면 "spec 정당화 없이 검증을 약화시킨 것"으로 의심하고 §4.1과 교차 확인:
- assertion/check 조건 삭제 또는 범위 확장(예: `==` → `<=`로 느슨해짐)
- expected value 자체가 실제 RTL 출력값으로 치환됨(가장 위험한 패턴 — anti-tautology 직접 위반 시그니처)
- 테스트 실패 조건 분기 자체가 제거됨

### 4.3 fix-plan 범위 준수

diff가 fix-plan.md 선언 범위(`affected_paths`, 영향 테스트/시퀀스/checker 목록) 밖의 파일/테스트를 건드렸는지 확인.

### 4.4 구조적 변경 의심 (TB-ARCH-SUSPECT)

새 시퀀스 클래스, 새 UVM agent/컴포넌트 추가처럼 보이면 판정하지 않고 `[TB-ARCH-SUSPECT]`로 표시, 보고서 Verdict에 명시해 **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 refer한다 — 그 agent가 재사용범위 판단표+ADR+adversarial cross-review를 거쳐 최종적으로 사람에게 넘긴다.

### 4.5 TB 컨벤션 준수

"0. 기준"에서 로드한 `verilog-rtl`(SV 문법)/`chip-verification`(듀얼탑)/`uvm-verification`(UVM 계층) 정본 대비 diff의 문법/구조 정합 확인.

### 4.6 분석서 정합성

`.ai/analysis/tb_{env}_*.analysis.md`가 이 diff 이후에도 여전히 유효한지 확인 — stale이면 `verilog-tb-analyst` 라우팅을 보고서에 권고.

### 4.7 Verdict

- `issues_found`: §4.1~4.4 중 하나라도 문제 발견(spec 미정당화, checker 완화, 범위 이탈, TB-ARCH-SUSPECT 미해결)
- `clean`: 위 전부 통과(§4.5/4.6은 권고 사항이라 통과 여부에 영향 없음 — 정보성)

---

## 5. Success Criteria

### 5.1 Definition of Done

- [ ] `agents/verilog-tb-reviewer.md` 작성 완료 — §4 검토 항목이 구체적 절차로 명시, 보고서/Manifest 형식 포함
- [ ] `install.py` 배포 등록 + 배포 테스트
- [ ] xcelium-mcp v1.34의 fix-review TB 경로 서술과 Task() 인터페이스 최종 대조
- [ ] 의도적 순환 논리 시나리오(`verilog-tb-coder`의 self-check을 통과하도록 교묘하게 작성된 fix-plan)로 이 agent가 여전히 잡아내는지 수동 검증 — self-check 실패 검증만으로는 부족함을 확인하는 것이 핵심

### 5.2 Quality Criteria

- [ ] `verilog-rtl-reviewer`와 트리거 키워드 중복 최소화
- [ ] `verilog-tb-coder`와의 인터페이스가 자연스러움(fix-implement Manifest → 이 agent Task 입력으로 그대로 연결)

---

## 6. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| 이 agent도 결국 "그럴듯해 보인다"로 안이하게 clean 판정 — 독립 검증자라는 이름값을 못함 | Critical | Medium | §4.1을 "self-check 결과와 무관하게 처음부터 재확인"으로 명시 — self-check 통과 여부를 참고조차 하지 않는 절차로 설계 |
| TB-ARCH-SUSPECT 판정 기준이 모호해 과소/과다 refer | Medium | Medium | RTL reviewer의 "false-positive escalation은 싸고 false-negative는 치명적" 편향을 그대로 채택 — 애매하면 refer |
| RTL reviewer 대비 evidence base(taxonomy) 부재로 검토 항목이 임시방편적 | Medium | High | 정직하게 인지하고 YAGNI로 남김 — 실전 사례가 쌓이면 후속 feature로 정식 catalog화 검토 |

---

## 7. Impact Analysis

### 7.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|---------------------|
| `agents/verilog-tb-reviewer.md` | 신규 파일 | 신규 agent 정의 |
| `agents/verilog-tb-coder.md` | 수정 | self-check을 1차 필터로 격하, 이 agent를 최종 판단자로 참조(같은 세션에서 함께 갱신) |
| `install.py` | 스크립트 | AGENTS 목록에 신규 agent 추가 |

### 7.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| **외부 계약(예정)**: xcelium-mcp `/sim` Skill(v1.34 §5.8 "4) fix-review" TB 경로) | INVOKE(완성 후) | `fix_target=tb`의 fix-implement 완료 직후 항상 호출 | Needs verification |

---

## 8. Next Steps

1. [ ] `/pdca design verilog-tb-reviewer`
2. [ ] `agents/verilog-tb-reviewer.md` 작성
3. [ ] `agents/verilog-tb-coder.md` self-check 절 갱신(이미 plan 갱신 완료, agent 파일은 Design/Do 단계에서 함께 반영)
4. [ ] `install.py` 등록
5. [ ] xcelium-mcp v1.34와 최종 대조

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-10 | 초안 — xcelium-mcp v1.34에서 확정된 `verilog-tb-reviewer` 요구사항을 이 repo로 가져와 Plan 문서화. `verilog-rtl-reviewer.md`의 "STATIC vs SIM 정직성 계약"·"architect-advisor 역할 분담" 골격을 재사용하되 taxonomy(T1-T9)는 이식하지 않고 TB 자체 검토 항목(§4)으로 대체 | HSLEE |
| 0.2 | 2026-07-21 | 사용자 지적("testbench도 architecturing을 잘 해야 확장성·재사용성이 높아진다")을 계기로 신설된 `verilog-tb-architect-advisor`(`verilog-tb-architect-advisor.plan.md`)의 route 대상으로 §2.1/FR-08/§4.4를 갱신 — "TB-ARCH-SUSPECT를 사람에게 직접 refer"를 "이 agent로 route"로 변경. §2.2 Out of Scope의 "TB용 classifier 신설 YAGNI" 문구도 신설 agent가 자동 classifier 없이 동작한다는 사실과 정합하도록 수정 | HSLEE |
