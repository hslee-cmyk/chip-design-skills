# verilog-tb-coder Planning Document

> **Summary**: TB(테스트벤치) 소스(testcase/시퀀스/checker/기대값)를 spec 대비로 정당화된 범위 안에서만 수정·작성하는 constrained implementer agent. `verilog-rtl-coder`(RTL 쪽 구현자)와 **동일한 패턴**을 따른다 — Task() 호출자가 스코프를 어떤 형태로 선언하든(승인된 `fix-plan.md` 경로 + "이 범위 안에서만" 지시, 또는 사용자의 직접 TB 코딩 요청 + 대상 파일) 이 agent는 그 선언된 스코프를 그대로 따르고, spec 정당화 self-check와 STOP-and-Ask 규율은 **호출 맥락(workflow-v2의 Fix Sub-cycle이든, 그와 무관한 일반 TB 코딩이든)과 무관하게 균일**하게 적용한다(0.4 갱신 — 사용자 지적: "verilog-rtl-coder는 이미 구현돼 있는데 workflow-v2에 부적합한가?"를 계기로, `verilog-rtl-coder.md`에 애초에 "Fix 모드"라는 별도 개념이 없고 스코프는 Task 프롬프트가 선언하는 것을 그대로 따르는 단일 균일 패턴임을 확인 → 이 문서의 0.3에서 만든 이원화를 철회). `verilog-tb-analyst`(TB 분석서 작성자, read-only)와도 자매 관계이지만 역할이 다르다 — analyst는 "이미 있는 TB를 분석"하고, 이 agent는 "TB를 spec 근거로 수정·작성"한다.
>
> **Project**: chip-design-skills
> **Version**: 0.4
> **Author**: HSLEE
> **Date**: 2026-07-10
> **Status**: Draft

---

## ⚠️ 정합성 유지 — 이 문서를 고치기 전에 반드시 읽을 것

`verilog-tb-analyst.plan.md`/`verilog-rtl-debugger.plan.md`와 동일한 cross-repo 계약 구조다. 요구사항 정본은 이 repo가 아니라 **xcelium-mcp**에 있다.

### 요구사항 정본 (xcelium-mcp repo, 절대경로)

| 문서 | 절대경로 | 참조 섹션 | 확인 시점 버전 |
|------|---------|----------|----------------|
| debug workflow v2 (Fix Sub-cycle, `fix_target` 분류 원본) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-debug-workflow-v2.plan.md` | §5.8 "Fix Target: RTL vs TB", §5.8 "3) fix-implement"(TB 표), §5.8 "4) fix-review"(TB 경로), §4.5 매핑 표 "debug (TB, 근본원인·수정 구현)" 행 | v1.34 (2026-07-10) |

### 계약 요약 (2026-07-10 시점)

**왜 신설하는가**: xcelium-mcp의 Fix Sub-cycle(`/sim debug`)은 v1.32까지 근본원인이 항상 RTL에 있다고 가정했다. 그러나 `verilog-rtl-debugger`는 조사 중 RTL과 TB를 함께 읽으므로, 결론이 "TB의 기대값·자극 생성 자체가 spec과 다르게 잘못 작성됨"일 수 있다(사용자 지적, xcelium-mcp v1.33). 이 경우 fix-plan은 `fix_target=tb`로 판정되고, 구현 주체로 AI를 선택하면 **이 agent**가 호출된다. `verilog-rtl-coder`가 TB까지 겸하는 것은 부적절하다 — coder는 "이미 비준된 RTL micro-architecture 안에서만 구현"하는 좁은 역할로 설계돼 있고, TB 작성은 spec 이해·coverage 모델·프로토콜 준수라는 다른 판단이 필요하다(사용자 지적: "coding한 agent가 testbench를 작성한다는 것이 말이 안 된다").

**이 agent는 workflow-v2 전용이 아니다(0.4 갱신 — 중요)**: 이 신설 동기는 xcelium-mcp의 Fix Sub-cycle에서 출발했지만, `verilog-rtl-coder.md`(이미 구현·배포된 대칭 agent)를 실제로 읽어보면 그 파일 어디에도 "fix-plan.md", "fix_target", "Fix 모드" 같은 workflow-v2 전용 개념이 없다. `verilog-rtl-coder`의 트리거는 "implement/add/modify RTL... 또는 `always` 블록을 쓰는 모든 요청"으로 되어 있어 애초에 범용이며, 입력은 "구조적 delta 선언"(A0 model-diff gate)뿐이고 이게 fix-plan에서 왔는지 Design 문서에서 왔는지 사용자의 직접 요청에서 왔는지 가리지 않는다. xcelium-mcp가 실제로 이 agent를 부르는 방식도 "Task, **fix-plan 파일 경로를 명시적으로 전달** + '이 문서 범위 밖 변경은 멈추고 보고' **지시**"(xcelium-mcp-debug-workflow-v2.plan.md v1.34, 367번째 줄 부근)로, 이는 agent 자체의 공식 파라미터가 아니라 **Task() 호출 프롬프트에 얹는 컨텍스트**일 뿐이다. 즉 `verilog-rtl-coder`는 "어디서 호출됐는지"를 모드로 구분하지 않고, 호출자가 프롬프트에 어떤 스코프를 선언하든 agent 자신의 균일한 STOP-and-Ask 규율(추측 금지, 애매하면 escalate)을 그대로 적용하는 **단일 패턴**이다. `verilog-tb-coder`도 이 패턴을 그대로 따른다 — workflow-v2의 Fix Sub-cycle에서도, 그와 무관한 일반 TB 코딩 요청에서도 동일하게 동작하며, 별도의 "모드"나 전용 파라미터 스키마를 두지 않는다.

**방법론 출처(중요 — 중복 금지)**: 이 agent는 TB 아키텍처 규칙(듀얼탑, UVM 계층, SV 검증 문법)을 system prompt에 복사해 내장하지 않는다 — `verilog-tb-analyst`가 이미 확립한 "0. 기준 — 시작 시 반드시 로드" 컨벤션을 그대로 재사용해, `verilog-rtl`/`chip-verification`/`uvm-verification` skill을 런타임에 전체 Read한다. TB의 **현재 구조**는 `.ai/analysis/tb_{env}_*.analysis.md`(`verilog-tb-analyst` 산출물)를 정본으로 삼아 참조만 하고, 이 agent 자신은 그 분석서를 재작성하지 않는다(Write 대상이 다름 — analyst는 `.ai/analysis/**`, 이 agent는 실제 TB 소스).

**anti-tautology — 1차 필터일 뿐 권위 있는 판단이 아니다(0.2 갱신, 사용자 지적: "작성한 agent가 self-check한다는 것은 모순이 있는 것 같다")**: 0.1은 이 agent 자신의 spec 정당화 self-check을 "유일한 두 번째 방어선"으로 서술했으나, 이는 `verilog-rtl-coder` §6이 명확히 금지하는 것 — "너는 의도를 스스로 인증하지 않는다. 정확성 property는 Prover가 구현과 독립적으로 저작한다" — 과 정확히 같은 종류의 모순이다. 구현 당사자가 "내가 쓴 코드가 spec에 맞다"를 스스로 최종 판단하면, 그 판단 자체가 자기 인증(tautology)이 되어 방어 장치로서 무력화될 위험이 있다. **확정**: 이 agent의 spec 정당화 확인은 **빠른 1차 필터**로만 기능한다 — 명백한 순환 논리("RTL에 맞춘다")가 보이면 그 자리에서 STOP-and-Ask해 헛수고를 줄이지만, 애매하거나 통과된 경우라도 **권위 있는 최종 판단은 아니다**. 최종 판단은 완료 직후 독립적으로 호출되는 **`verilog-tb-reviewer`**(신규, read-only, `verilog-tb-reviewer.plan.md` 별도 문서)가 내린다 — RTL 쪽의 "coder self-check(구조적 필터) + reviewer/prover 독립 검증(정확성 판단)" 2단 구조를 TB에도 동일하게 적용하는 것이며, `verilog-rtl-coder` §5.6/§7이 호출 맥락과 무관하게 항상 라우팅을 자신의 Definition of Done/Handoff에 포함시키듯, 이 agent도 호출 맥락과 무관하게 항상 `verilog-tb-reviewer`로의 인계를 자신의 완료 조건에 포함한다(0.4 갱신 — "Fix 모드는 강제, General 모드는 권장"이라는 0.3의 차등 적용을 철회. rtl-coder가 self-certify 금지를 무조건적 원칙으로 삼듯, 이 agent도 무조건 인계한다. xcelium-mcp v1.34의 fix-review TB 경로는 이 인계가 일어나는 오케스트레이션 지점 중 하나일 뿐, 그 존재 여부를 좌우하지 않는다).

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | Fix Sub-cycle에서 근본원인이 TB에 있다고 판정된 경우 이를 구현할 agent가 없다 — `verilog-rtl-coder`는 RTL 전용으로 설계돼 있고 TB까지 겸하면 정체성이 흐려짐. 동시에, workflow-v2와 무관한 일반 TB 코딩(신규 testcase 작성, 시나리오 보강 등) 수요도 항상 존재하므로, 이를 fix-plan.md 전용 인터페이스로 좁게 설계하면 안 됨(0.3에서 처음 지적) |
| **Solution** | `verilog-rtl-coder`와 정확히 동일한 패턴의 TB 전용 constrained implementer `verilog-tb-coder` 신설 — Task() 호출자가 스코프를 어떤 형태로 선언하든(fix-plan.md 경로든, 사용자 직접 요청이든) 그 선언을 그대로 따르는 **단일 균일 규율**로 설계(0.4 갱신 — 0.3의 "Fix 모드/General 모드" 이원화는 대칭 벤치마크에 실재하지 않는 구조였음을 확인하고 철회). `verilog-tb-analyst`의 분석서를 구조 참조로 삼고, spec 대비 정당화(anti-tautology) 1차 필터를 거친 뒤 TB 소스를 수정·작성, 완료 시 항상 `verilog-tb-reviewer`에게 독립 검토를 요청 |
| **Function/UX Effect** | workflow-v2 Fix 경로(`/sim debug`가 `fix_target=tb`로 판정 → 승인 → Task 위임)든, 이와 무관한 사용자의 직접 TB 코딩 요청이든 **동일한 흐름**으로 처리된다 — 호출 시 명시된 스코프 안에서 구현 → spec 근거 self-check(1차 필터) → `verilog-tb-reviewer`의 독립 검토 요청(항상) → workflow-v2 안에서는 그 검토가 fix-review 게이트로, 그 밖에서는 일반 코드 리뷰로 소비됨 → 필요 시 `/sim verify`로 재검증 |
| **Core Value** | RTL 버그 fix와 TB 버그 fix가 대칭적으로 처리되고, "TB를 고쳐서 RTL 버그를 숨기는" 실수를 self-check(1차 필터) + `verilog-tb-reviewer`의 독립 검증(항상 요청)이라는 2단으로 방어한다. 이 규율은 호출 맥락(workflow-v2 여부)에 따라 달라지지 않으므로, 별도 모드·파라미터 분기 없이도 두 용도를 자연스럽게 모두 커버한다(0.4 갱신) |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | (1) Fix Sub-cycle의 근본원인이 항상 RTL이라는 가정이 깨짐(xcelium-mcp v1.33) — TB 전담 구현 agent 부재. (2) workflow-v2와 무관한 일반 TB 코딩 수요도 항상 존재. (3) 이 둘을 별도 "모드"로 이원화하는 설계는 대칭 벤치마크(`verilog-rtl-coder`)의 실제 구조와 맞지 않음이 확인되어, 단일 균일 규율로 재정정(0.4) |
| **WHO** | workflow-v2 Fix 경로와 그와 무관한 일반 TB 코딩을 요청하는 모든 프로젝트의 AI 에이전트/사용자(1차 소비자: venezia-fpga) — 호출 경로가 다르다고 이 agent의 행동 규율이 달라지지 않는다 |
| **RISK** | 이 agent가 spec 정당화를 충분히 엄격하게 검증하지 않으면, 실제 RTL 버그를 TB 완화로 숨기는 결과가 될 수 있음(anti-tautology 위반) — 호출 맥락과 무관하게 이 리스크가 이 agent 설계의 최우선 관심사 |
| **SUCCESS** | Task() 호출 시 명시된 스코프(어떤 형태로 선언되든) 안에서만 TB를 수정, spec 근거가 불충분하면 구현 대신 STOP-and-Ask, 완료 시 항상 `verilog-tb-reviewer`에게 독립 검토 요청, `verilog-tb-analyst` 분석서와 구조적으로 일치하는 코드 산출 |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-coder.md`) 작성 + `install.py` 배포 등록만. xcelium-mcp 쪽 `fix_target` 분류·Fix Sub-cycle 오케스트레이션 자체는 xcelium-mcp repo 소관(Out of Scope). **"Fix 모드/General 모드"를 구분하는 formal 파라미터 스키마는 만들지 않는다**(0.4 갱신, Out of Scope로 재확정 — `verilog-rtl-coder`에도 그런 스키마가 없다) |

---

## 1. Overview

### 1.1 Purpose

TB 소스(testcase 파일, 공유 시퀀스/컴포넌트, checker/expected-value 로직)를 spec 대비로 정당화된 방식으로만 수정·작성한다. `verilog-rtl-coder`가 "구조적 delta 선언"을 Task 프롬프트로 받아 그 안에서만 구현하듯(0.4 갱신), 이 agent도 호출자가 Task() 프롬프트에 명시하는 스코프를 그대로 따른다 — 그 스코프가 승인된 fix-plan.md(경로 + 영향 파일 목록)든, 사용자의 직접 요청(예: "이 testcase에 코너 케이스 시나리오 추가")이든 agent 입장에서 처리 방식은 동일하다: 명시된 스코프 밖으로 나가지 않고, spec 근거가 불충분하면 STOP-and-Ask한다.

### 1.2 Background

`verilog-rtl-coder`는 이 repo의 "constrained implementer" 컨벤션을 확립해뒀다(비준된 계획 범위 안에서만 구현, STOP-and-Ask, self-certify 금지 — 정확성은 독립된 검증자에게 위임). `verilog-tb-coder`는 이 컨벤션을 TB 도메인에 그대로 적용하는 **자매(sibling) agent**다. 차이점:

- **입력**: `verilog-rtl-coder`는 Task 프롬프트로 "structural delta 선언"(어떤 always/net/FSM이 바뀌는가)을 받는다 — 이때 그 선언이 fix-plan.md에서 왔는지 다른 문서에서 왔는지는 agent 입장에서 구분되지 않는다. 이 agent도 동일하게, Task 프롬프트로 "무엇을 왜 바꾸는가"(영향받는 테스트/시퀀스/checker 목록 + 근거)를 받는다 — 근거가 fix-plan.md의 "근본원인 소재 판정"이든, 사용자가 직접 명시한 요구사항이든 agent의 처리 규율(§4)은 동일하다(0.4 갱신 — 0.3에서 만든 "Fix 모드"/"General 모드" 이원화, `fix_plan_path`/`scope_description` 파라미터 분기를 철회. 대칭 agent에 실재하지 않는 구조였음).
- **정확성 검증자(0.2/0.4 갱신)**: `verilog-rtl-coder`는 정확성을 `verilog-rtl-prover`(formal)/`verilog-rtl-reviewer`(STATIC)로 위임한다(self-certify 금지) — 이는 호출 맥락과 무관하게 **항상** 적용되는 자신의 Definition of Done/Handoff 항목이다(§5.6/§7). 이 agent도 동일 원칙을 따른다 — **`verilog-tb-reviewer`**(신규, 별도 plan 문서)가 그 역할이며, 호출 맥락(workflow-v2 여부)과 무관하게 완료 시 항상 인계를 요청한다. 이 agent 자신의 spec 정당화 확인(아래 §4)은 **1차 필터**일 뿐이고, 권위 있는 최종 검증은 `verilog-tb-reviewer` → (workflow-v2 안이면) `/sim verify`(실제 회귀) 순으로 이어진다.
- **구조 참조**: `verilog-rtl-coder`는 `.ai/analysis/{module}.analysis.md`(`verilog-rtl-analyst` 산출물)를 읽는다. 이 agent는 `.ai/analysis/tb_{env}_*.analysis.md`(`verilog-tb-analyst` 산출물)를 읽는다 — 부재/stale이면 **coder가 처음부터 깊게 분석하지 않고 `verilog-tb-analyst`로 라우팅**(`verilog-rtl-coder` §1.3의 동일 원칙 재사용).

### 1.3 Related Documents

- **요구사항 정본**: §정합성 유지 절의 xcelium-mcp 문서
- **대칭 agent(다른 도메인, 동일 컨벤션)**: `agents/verilog-rtl-coder.md` — "constrained implementer", "STOP-and-Ask", "self-certify 금지·검증 위임" 원칙을 벤치마크(단, RTL 전용 taxonomy T1..T9·`boundary-classifier.py`는 이 agent에 그대로 이식하지 않는다 — TB 버그의 실패 양상이 RTL과 다르기 때문, §2.2 참조). **0.4 갱신**: 이 문서 전체의 "모드 이원화 철회" 결정은 이 파일을 실제로 Read해서 확인한 사실(fix-plan 관련 개념이 전무함)에 근거한다.
- **자매 agent(동일 도메인, 다른 역할)**: `agents/verilog-tb-analyst.md` — "0. 기준" 정본 skill 목록(verilog-rtl/chip-verification/uvm-verification 전체 Read, ssh-mcp 조건부)을 그대로 벤치마크. analyst는 Read-only(`.ai/analysis/**`만 Write)이고 이 agent는 TB 소스 자체를 Write한다는 점이 유일한 근본 차이
- **cross-repo 관계 선례**: `verilog-tb-analyst.plan.md`, `verilog-rtl-debugger.plan.md` — 동일 계약 구조
- **최종 검증자(0.2 신규)**: `verilog-tb-reviewer.plan.md` — 이 agent(및 사람 구현 경로)의 spec 정당화 판단을 독립적으로 재확인하는 별도 agent, 같은 세션에서 함께 작성됨

---

## 2. Scope

### 2.1 In Scope

- [ ] `agents/verilog-tb-coder.md` 신규 작성 — `verilog-rtl-coder.md`의 "constrained implementer" 골격(권한 경계, Mandatory Setup, STOP-and-Ask, Definition of Done, Handoff, 정직한 한계)을 TB 도메인에 맞게 재구성. RTL 전용 요소(A0 model-diff gate/boundary-classifier.py, A1..A7 taxonomy 표, T1-T9 signature)는 이식하지 않음(§2.2 Out of Scope 참조) — 대신 §4의 TB 자체 규율(spec 정당화 self-check, STOP-and-Ask 조건)로 대체
- [ ] "0. 기준 — 시작 시 반드시 로드" 절에 `verilog-tb-analyst.md`와 동일한 4~5개 정본 Read 지시: `~/.claude/skills/verilog-rtl/SKILL.md`(전체, SV 문법), `~/.claude/skills/chip-verification/SKILL.md`(전체, 듀얼탑), `~/.claude/skills/uvm-verification/SKILL.md`(전체, UVM 계층), `~/.claude/skills/ssh-mcp/SKILL.md`(전체, `mcp__ssh__*` 가용 시에만) — TB 코드를 정확히 쓰려면 정확히 읽을 수 있어야 하므로 analyst와 동일 정본이 필요
- [ ] Tool 목록: `Read, Write, Edit, Glob, Grep, Bash` + `mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls, mcp__ssh__file_write`(TB 소스가 원격일 수 있음 — `verilog-tb-analyst`와 동일 근거이되, 이 agent는 Write 권한도 필요하므로 `file_write` 추가)
- [ ] `.ai/analysis/tb_{env}_*.analysis.md` 확인 — 부재/stale이면 코딩 전에 `verilog-tb-analyst`로 라우팅(agent 미배포 시 fallback: Claude가 phase-0-discovery.md를 직접 참조해 최소 확인)
- [ ] Task 호출 수신 시(스코프 선언 형태는 호출자가 정함 — fix-plan.md 경로든 사용자 직접 지시든) **spec 정당화 self-check**(§4) — "무엇을 왜 바꾸는가"의 근거가 spec/analysis 문서를 실제로 인용하거나 명확히 도출 가능한지 재확인, 순환 논리("RTL 동작에 맞춘다")로 보이면 구현하지 않고 STOP-and-Ask(0.2 갱신 — 이 self-check는 빠른 1차 필터일 뿐이며, 최종 판단은 통과 여부와 무관하게 항상 독립된 `verilog-tb-reviewer`가 내림. 이 인계는 호출 맥락과 무관하게 항상 수행 — 0.4 갱신)
- [ ] 명시된 스코프(호출 시 선언된 영향 파일/시나리오 목록) 밖의 변경 필요 시 STOP-and-Ask(`verilog-rtl-coder`의 STOP-and-Ask 원칙과 동일 정신)
- [ ] "구조적 변경으로 보이는 경우"(새 시퀀스 클래스, 새 UVM agent/컴포넌트 추가 등) STOP-and-Ask — **(2026-07-21 갱신)** 신설된 `verilog-tb-architect-advisor`로 route한다(자동 classifier는 여전히 없음 — 그 agent도 프로즈 기반 판단이지만, 재사용범위 판단표+ADR+adversarial cross-review라는 구조화된 절차를 거친 뒤 사람에게 넘긴다. `verilog-tb-architect-advisor.plan.md` §정합성 유지 참조)
- [ ] 스코프 선언 자체가 모호해 대상 파일/시나리오를 특정할 수 없는 경우 STOP-and-Ask(0.4 갱신 — 호출 맥락 무관 공통 조건)
- [ ] Definition of Done: (1) 명시된 스코프 내 변경만(post-hoc 재확인), (2) spec 근거 self-check(1차 필터) 통과, (3) 변경한 TB 파일의 구문 오류 없음(육안/가능하면 도구 확인 — 전용 TB lint 도구가 없으므로 "정직한 한계"로 남김), (4) `.ai/analysis/tb_*.analysis.md` 갱신 또는 `verilog-tb-analyst`에 위임, (5) `verilog-tb-reviewer`에게 독립 검토를 **항상** 요청(0.4 갱신 — 호출 맥락에 따라 강제/권장을 가르지 않는다. workflow-v2 안에서는 그 요청이 fix-review 게이트로 소비되고, 밖에서는 일반 리뷰로 소비될 뿐 — 요청 자체는 이 agent의 무조건적 책임)
- [ ] Handoff: 변경 파일 목록, spec 근거 요약, escalation 여부(STOP-and-Ask 발생 시 그 이유), `verilog-tb-reviewer` 검토 요청, (workflow-v2 맥락이면) `/sim verify {test}` 재검증 안내
- [ ] `install.py` 배포 목록에 등록, 기존 경로(`~/.claude/agents/`)로 배포

### 2.2 Out of Scope

- **RTL 전용 taxonomy(T1-T9)/`boundary-classifier.py`/A1..A7 산출물 표를 이 agent에 이식** — TB 버그의 실패 양상(잘못된 기대값, 잘못된 자극 순서, 프로토콜 위반 시뮬레이션, coverage 누락)은 RTL의 실패 양상(FSM deadlock, CDC race, pointer wrap)과 범주가 다르다. 억지로 대응시키면 카테고리 오류(category error)가 된다 — 이 agent는 자기 도메인에 맞는 자체 규율(§4)만 갖는다
- **TB용 ARCH/IFACE/LOCAL 자동 classifier 신설** — YAGNI, xcelium-mcp v1.33이 이미 "정직한 한계"로 명시. 구조적 변경 감지는 이 agent의 판단(STOP-and-Ask)에 맡긴다
- **TB용 정적/formal 사전 검증 게이트(RTL의 fix-review 대응물) 신설** — YAGNI, `verilog-tb-reviewer` 인계 + (workflow-v2 안이면) `/sim verify`가 유일한 사후 검증
- **`fix_target`(RTL vs TB) 판정 로직 자체** — `verilog-rtl-debugger`(xcelium-mcp 소관)가 debug 단계에서 판정, 이 agent는 이미 판정된 결과(fix-plan.md)를 스코프 선언 중 하나로만 받음
- **TB 분석서 작성/갱신 방법론(§0A/0B/0C) 자체** — `verilog-tb-analyst`/xcelium-mcp 소관, 이 agent는 그 산출물을 참조만 함
- **시뮬레이션 실행/재검증** — `/sim verify`(xcelium-mcp) 소관, 이 agent는 코드 수정까지만
- **"Fix 모드/General 모드"를 구분하는 formal 파라미터 스키마(`fix_plan_path`/`scope_description`/`reason` enum 등) 신설**(0.4 신규, 0.3에서 만들었다가 철회) — `verilog-rtl-coder`에 그런 스키마가 없다. 스코프는 Task() 프롬프트가 자유 형식으로 선언하는 것을 그대로 따르며, 이 agent는 그 소스를 구분하지 않는다

---

## 3. Requirements

### 3.1 Functional Requirements

| ID | Requirement | Priority | Status |
|----|-------------|----------|--------|
| FR-01 | `agents/verilog-tb-coder.md` frontmatter — `verilog-rtl-coder.md`/`verilog-tb-analyst.md`와 유사한 구조(`name`/`description`(Use it when/Do NOT use for/Triggers)/`tools`/`model`). Triggers 예시: "TB 수정", "testcase 수정", "fix_target=tb", "checker 수정", "expected value 수정", "TB fix-plan 구현", "테스트케이스 추가", "시나리오 보강"(0.4 갱신 — 일반 TB 코딩 트리거도 명시) | High | Pending |
| FR-02 | Tool 목록: `Read, Write, Edit, Glob, Grep, Bash, mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls, mcp__ssh__file_write` — 로컬/원격 TB 소스 모두 대응(`verilog-tb-analyst` FR-02와 동일 근거 + Write 권한 추가) | High | Pending |
| FR-03 | "0. 기준"에 `~/.claude/skills/verilog-rtl/SKILL.md`(전체), `~/.claude/skills/chip-verification/SKILL.md`(전체), `~/.claude/skills/uvm-verification/SKILL.md`(전체)를 **MUST** Read로 명시 — `verilog-tb-analyst` FR-10/11/12와 동일(부분로딩 금지, drift 방지 원칙 재사용) | High | Pending |
| FR-04 | "0. 기준"에 `~/.claude/skills/ssh-mcp/SKILL.md`(전체, `mcp__ssh__*` 가용 시에만 MUST) 명시 — `verilog-tb-analyst` FR-15와 동일 | High | Pending |
| FR-05 | **Task() 호출 규약(0.4 갱신 — `verilog-rtl-coder`와 동일하게 formal 파라미터 스키마 없이 자유 형식 프롬프트)**: 호출자(xcelium-mcp workflow-v2, 사람, 다른 agent)는 Task 프롬프트에 (a) 무엇을 왜 바꾸는지(스코프), (b) 그 근거(fix-plan.md 경로 + 근본원인 판정 근거, 또는 사용자가 명시한 요구사항 + spec/analysis 문서), (c) 대상 TB 파일/env를 자연어로 명시한다. 이 agent는 이 세 가지가 프롬프트에 없으면 스스로 추정하지 않고 STOP-and-Ask한다(FR-08) — `fix_plan_path`/`scope_description` 같은 이름 붙은 필드를 agent 내부에서 분기하지 않는다 | High | Pending |
| FR-06 | **spec 정당화 self-check(0.2 갱신 — 이 agent 쪽의 1차 필터, 권위 있는 최종 판단 아님, 호출 맥락 무관 균일 적용)**: Task 프롬프트에 명시된 근거(§FR-05 (b))를 읽고, spec(또는 `.ai/analysis/tb_*.analysis.md`의 판별 신호/기대값 정의) 대비 근거가 명시적으로 인용·연결되는지 확인. "RTL이 이렇게 동작하니 TB를 맞춘다"류의 순환 논리로 판단되면 **구현하지 않고 STOP-and-Ask** — 이미 사람의 승인(fix-plan 등)을 받은 근거여도 예외 없이 재확인(defense-in-depth, §머리말 anti-tautology 참조). 사용자가 직접 명시한 요구사항도 유효한 근거로 인정되나, spec과 모순되거나 근거 자체가 모호하면 동일하게 STOP-and-Ask. 이 self-check을 통과해도 구현은 완료 상태가 아니며, 반드시 `verilog-tb-reviewer`에게 독립 검토를 요청해야 한다(호출 맥락 무관 — 자신이 작성한 코드를 자신이 최종 승인할 수 없다는 원칙, §1.2) | High | Pending |
| FR-07 | `.ai/analysis/tb_{env}_*.analysis.md` 확인 — 부재/stale이면 코딩 전 `verilog-tb-analyst`로 라우팅(Task 또는 fallback으로 Claude가 직접 수행) | High | Pending |
| FR-08 | STOP-and-Ask 조건(추측 금지, 호출 맥락 무관 공통 기준): (a) FR-06 spec 정당화 실패, (b) Task 프롬프트에 명시된 스코프(대상 파일/시나리오) 밖의 변경이 필요해 보임, (c) 변경이 "새 시퀀스 클래스/UVM 컴포넌트 추가" 등 구조적으로 보임 → **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 route(자동 classifier는 여전히 없지만 그 agent가 구조화된 판단 절차를 수행 — §2.2), (d) env(`uvm`/`dsv`/`ams`)에 따라 TB 구조를 정확히 해석하기 어려움, (e) Task 프롬프트에 스코프/근거/대상 파일 중 하나라도 불명확해 특정할 수 없음(0.4 갱신 — "General 모드 전용"이 아니라 모든 호출에 적용되는 공통 조건으로 일반화) | High | Pending |
| FR-09 | 하드 제약(HANDS OFF): RTL(`db/design`) 무수정. `.ai/analysis/tb_*.analysis.md`는 직접 재작성하지 않고 `verilog-tb-analyst`에 위임(단, 변경 내용을 반영해 갱신 요청은 이 agent의 책임) | High | Pending |
| FR-10 | Definition of Done(0.4 갱신 — 호출 맥락 무관 단일 기준): (1) Task 프롬프트에 명시된 스코프 내 변경만(post-hoc 재확인), (2) FR-06 spec 정당화 self-check(1차 필터) 통과, (3) 변경 파일 구문 오류 없음(가능하면 `verilog-rtl` skill이 다루는 SV 문법 정본으로 육안 대조 — 전용 TB lint 도구 없음, 정직한 한계로 명시), (4) `.ai/analysis/tb_*.analysis.md` 갱신 위임 완료, (5) `verilog-tb-reviewer`에게 독립 검토를 **항상** 요청 — (2)+(5) 모두 완료해야 최종 완료(workflow-v2 안이면 그 요청이 fix-review 게이트로 소비, 밖이면 일반 리뷰로 소비 — 요청 자체는 무조건적) | High | Pending |
| FR-11 | Handoff/Manifest: 변경 파일 목록(절대경로), spec 근거 요약(무엇을 왜 바꿨는지), escalation 발생 여부+이유, `verilog-tb-analyst` 위임 여부, `verilog-tb-reviewer` 검토 요청, (workflow-v2 맥락이면) `/sim verify {test}` 재검증 안내 | Medium | Pending |
| FR-12 | `agents/verilog-tb-coder.md` 배포 확인 — **(2026-07-22 갱신)** `install.py`에 별도 AGENTS 목록은 없음(`install_agents`가 `agents/*.md`를 frontmatter 유무로 glob 자동 인식), `--dry-run`으로 인식 여부만 확인 | Medium | Done |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|---------------------|
| Anti-tautology 준수 | FR-06 self-check(1차 필터)이 "RTL에 맞춘다"류 순환 논리를 실제로 걸러내는지, 걸러내지 못해도 `verilog-tb-reviewer`(2차, 권위 있는 최종 판단)가 걸러내는지 — 호출 맥락(workflow-v2 여부)과 무관하게 동일 결과가 나오는지 포함(0.4 갱신) | 의도적으로 순환 논리 근거를 담은 fix-plan.md 시나리오와, 동일한 순환 논리를 사용자의 직접 요청으로 준 시나리오 둘 다로 테스트(self-check 우회 시 tb-reviewer가 잡는지까지 포함) |
| 컨벤션 일관성 | `verilog-rtl-coder.md`(constrained implementer 골격 — 특히 "formal 파라미터 스키마 없음" 패턴)·`verilog-tb-analyst.md`("0. 기준" 정본 목록)와 구조·톤 일관 | 세 agent 파일 diff 리뷰 |
| Cross-repo 일관성 | xcelium-mcp v1.34의 `fix_target=tb` 경로 서술(fix-implement+fix-review)과 이 agent의 Task 호출 규약(FR-05, 자유 형식)이 100% 일치 | Design 단계에서 원본 재확인 |

---

## 4. `verilog-tb-coder`의 자체 규율 (Design 단계에서 agent 파일로 구체화할 핵심 내용)

> 이 절은 `agents/verilog-tb-coder.md` 작성 시 반드시 반영해야 하는 설계 의도를 미리 정리한 것 — Design 문서에서 최종 확정한다.

### 4.1 왜 RTL taxonomy를 이식하지 않는가

`verilog-rtl-coder`의 A0(model-diff gate)와 A1..A7(taxonomy 산출물)은 RTL의 구조적 성질(always 블록, net driver, FSM state, clock domain)에 강하게 결합돼 있다. TB 코드의 실패 양상은 이와 범주가 다르다 — 예를 들어 "잘못된 expected value", "빠진 테스트 시나리오", "프로토콜 위반을 관측 못 하는 checker", "race를 유발하는 TB 자체 타이밍" 등. 이걸 RTL taxonomy 항목에 억지로 매핑하면(예: "expected value 오류를 T9 bit-width 오류로 취급") 카테고리 오류가 되고, 오히려 진짜 위험(anti-tautology)을 놓치게 된다. 따라서 이 agent는 **자기 도메인에 맞는 축소된 자체 규율**(spec 정당화 self-check + STOP-and-Ask 조건 목록)만 가진다 — RTL coder만큼 정교한 다단계 산출물 체계를 억지로 재현하지 않는다(YAGNI).

### 4.2 spec 정당화 self-check(1차 필터)의 구체 형태(Design에서 확정)

> **0.2/0.4 갱신**: 이 self-check는 "권위 있는 최종 판단"이 아니라 **빠른 1차 필터**다 — 순환 논리를 놓치는 비용이 크므로 명백한 경우만 여기서 걸러내고, 통과/불통과와 무관하게 최종 판단은 항상 `verilog-tb-reviewer`(독립 agent)가 내린다. 작성한 agent 자신이 자기 판단의 최종 심판이 되는 모순(사용자 지적)을 피하기 위한 구조다 — 자세한 배경은 §1.2 "정확성 검증자" 참조. **0.4 갱신**: 이 절차는 호출 맥락(workflow-v2 Fix 경로인지, 일반 TB 코딩 요청인지)과 무관하게 항상 동일하게 수행된다 — 0.3에서 시도했던 "Fix 모드"/"General 모드" 절차 분기는 철회.

1. Task 프롬프트에 명시된 근거를 읽는다 — fix-plan.md의 "근본원인 소재 판정 근거"든, 사용자가 직접 명시한 요구사항이든 형태만 다를 뿐 다음 단계는 동일하다.
2. 그 근거가 다음 중 하나를 **명시적으로 인용하거나 명확히 도출 가능**한지 확인: (a) 프로토콜/기능 spec 문서(프로젝트마다 위치가 다를 수 있음 — datasheet, 설계 사양 등), (b) `.ai/analysis/tb_{env}_*.analysis.md`의 "판별 신호+기대값" 절, (c) 사용자가 직접 명시한 요구사항 자체(예: "이 프로토콜의 코너 케이스 A를 검증하는 시나리오 추가")도 (a)/(b)와 모순되지 않으면 유효한 근거로 인정.
3. 인용이 없거나, 인용된 내용이 "현재 RTL이 이렇게 동작한다"는 사실 서술뿐이고 "그래서 spec상 옳다"는 연결이 빠져 있으면, 또는 근거 자체가 spec/analysis와 모순되거나 모호해 대상 파일/시나리오를 특정할 수 없으면 → **STOP-and-Ask**(FR-08 (a)/(e)).
4. 통과하면 그 근거를 Handoff에 그대로 요약해 남긴다(추후 감사 가능하도록) — 이 요약은 이어지는 `verilog-tb-reviewer`의 검토 입력으로도 재사용된다.
5. **이 1차 필터를 통과했다는 것이 곧 완료를 의미하지 않는다.** 통과 후에도 `verilog-tb-reviewer`가 동일한 "근거 인용" 판단을 독립적으로 재수행하며(§4.1 of `verilog-tb-reviewer.plan.md`), 두 판단이 모두 clean이어야 종료된다 — 이는 호출 맥락과 무관하게 항상 요구된다(0.4 갱신, `verilog-rtl-coder`의 무조건적 self-certify 금지 원칙과 동일).

### 4.3 TB 소스 변경 시 지켜야 할 최소 규율

- 기존 코딩 스타일/네이밍 컨벤션을 따른다(`verilog-rtl`/`chip-verification`/`uvm-verification` skill이 정본).
- 새 테스트 시나리오를 추가하는 게 아니라 **기존 시나리오의 checker/기대값/자극을 명시된 스코프 안에서 고치는 것**이 기본 케이스다 — 새 시나리오·새 컴포넌트가 필요해 보이면 FR-08(c)로 STOP.
- 변경 후 `.ai/analysis/tb_*.analysis.md`가 stale해지므로, 갱신을 `verilog-tb-analyst`에 위임하거나(권장) 직접 위임 요청을 Handoff에 명시한다.

---

## 5. Success Criteria

### 5.1 Definition of Done

- [ ] `agents/verilog-tb-coder.md` 작성 완료 — "왜 별도 agent인가"(§1.2 대칭 비교), spec 정당화 self-check(§4.2, 1차 필터임을 명시)이 구체적 절차로 명시, `verilog-tb-reviewer`로의 검토 인계가 호출 맥락과 무관하게 항상 완료 조건에 포함(0.4 갱신), HANDS OFF, 정직한 한계 섹션 포함
- [ ] `install.py` 배포 등록 + 배포 테스트(`~/.claude/agents/verilog-tb-coder.md` 생성 확인)
- [ ] xcelium-mcp v1.34의 `fix_target=tb` 서술(fix-implement+fix-review)과 이 agent의 Task 호출 규약(자유 형식 프롬프트, FR-05) 최종 대조, 불일치 없음
- [ ] 의도적으로 "RTL에 맞춘다"는 순환 논리 근거를 담은 시나리오(fix-plan.md 경유 + 사용자 직접 요청 경유 둘 다)로 STOP-and-Ask가 실제로 발동하는지 수동 검증

### 5.2 Quality Criteria

- [ ] `verilog-rtl-coder`와 트리거 키워드 중복 최소화(RTL vs TB 구분 명확 — 대상 파일 확장자/경로로 이미 구분되므로 트리거 자체의 중복 위험은 낮음)
- [ ] `verilog-tb-analyst`와의 위임 인터페이스가 자연스러움(분석서 부재/stale 시 라우팅)
- [ ] 이 agent의 파일 어디에도 "Fix 모드"/"General 모드" 같은 호출-맥락 기반 분기가 남아있지 않음(0.4 신규 — `verilog-rtl-coder`와의 구조적 대칭성 검증)

---

## 6. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| spec 정당화 self-check(1차 필터)이 너무 관대해 순환 논리를 통과시킴 — 진짜 RTL 버그를 TB 완화로 숨김 | Critical | Medium(0.2 갱신 — 이 agent 단독 방어에서 Low~Medium으로 완화: `verilog-tb-reviewer`의 독립 재확인이 2차 방어선으로 항상 존재, 호출 맥락 무관 — 0.4) | FR-06을 구체적 절차(§4.2)로 명시, 애매하면 관대하게 통과시키지 말고 STOP-and-Ask 쪽으로 편향(RTL coder의 "false-positive escalation은 싸고 false-negative는 치명적" 원칙과 동일 정신). 1차 필터 실패 시에도 `verilog-tb-reviewer`가 동일 판단을 독립적으로 재수행하므로 단일 실패점이 아님 |
| TB용 구조적 변경(ARCH 대응물) classifier가 없어 이 agent가 실제로는 구조적인 변경을 LOCAL처럼 처리할 위험 | High | Medium | FR-08(c)로 "새 시퀀스 클래스/컴포넌트 추가처럼 보이면" 무조건 STOP — 애매하면 escalate하는 보수적 기준 채택(자동 판정 도구 부재를 사람 개입으로 보완) |
| 전용 TB lint 도구가 없어 구문 오류가 사후에야 드러남(xcelium-mcp v1.33 §11에서 이미 인지된 비대칭) | Medium | Medium | 이 plan 범위에서 대응하지 않음(YAGNI) — `verilog-rtl` skill의 SV 문법 정본으로 육안 대조하는 수준까지만, 필요성이 확인되면 후속 검토 |
| `verilog-tb-analyst`와 트리거·책임 경계가 모호해질 위험 | Low | Low | analyst=read-only 분석, coder=spec 근거 기반 수정으로 frontmatter Do NOT use for에 명시적으로 상호 참조 |
| (0.4 신규) 호출자(특히 workflow-v2 밖의 일반 요청)가 Task 프롬프트에 스코프/근거/대상 파일을 충분히 명시하지 않아, 이 agent가 매번 STOP-and-Ask로 되돌리는 마찰이 생길 위험 | Low | Medium | `agents/verilog-tb-coder.md`의 description/Triggers에 "호출 시 스코프와 근거를 명시해 달라"는 기대치를 명시(FR-01) — `verilog-rtl-coder`도 동일하게 호출자가 structural delta를 평문 선언하는 것을 전제로 하므로 새로운 문제가 아님 |

---

## 7. Impact Analysis

### 7.1 Changed Resources

| Resource | Type | Change Description |
|----------|------|---------------------|
| `agents/verilog-tb-coder.md` | 신규 파일 | 신규 agent 정의 |
| `install.py` | 스크립트(변경 없음) | 별도 목록 편집 불필요 — `agents/*.md` glob 자동 인식 확인만(2026-07-22) |
| `~/.claude/agents/verilog-tb-coder.md` | 배포 산출물 | install.py 실행 시 신규 생성 |

### 7.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| (신규 agent라 현재 소비자 없음) | — | — | — |
| **외부 계약(예정)**: xcelium-mcp `/sim` Skill(`xcelium-mcp-debug-workflow-v2.plan.md` v1.34 §5.8 "3) fix-implement"/"4) fix-review" TB 표) | INVOKE(완성 후) | fix-plan 승인 + 구현 주체로 AI 선택 + `fix_target=tb`일 때 Task 위임(자유 형식 프롬프트로 fix-plan 경로 + 스코프 전달), 완료 후 `verilog-tb-reviewer` fix-review로 인계 | Needs verification — 사람이 직접 수정하는 경로(fallback)는 이 agent 미배포 환경에서도 항상 유효(xcelium-mcp v1.33이 이미 대칭 경로로 설계) |
| **외부 계약(예정)**: 일반 사용자/AI 에이전트의 직접 TB 코딩 요청(workflow-v2 무관, 0.4 신규) | INVOKE | 사용자가 직접 Task 위임(자유 형식 프롬프트로 요구사항 + 대상 파일 전달) | Needs verification — 별도 승인 게이트 없이 바로 호출되므로, self-check(§4.2)이 유일한 사전 필터임을 사용자에게 주지시킬 필요 |
| **외부 계약(예정)**: `verilog-tb-analyst`(`.ai/analysis/tb_*.analysis.md`) | READ(런타임) | 코딩 전 구조 참조, 코딩 후 갱신 위임 | Needs verification — 분석서가 최신 상태로 유지되는지 |

### 7.3 Verification

- [ ] xcelium-mcp `/sim debug`가 `fix_target=tb` 승인 후 이 agent를 정상적으로 Task 위임할 수 있는지 확인
- [ ] `install.py --only agents` 실행 후 배포 경로 확인

---

## 8. Convention Prerequisites

### 8.1 Existing Project Conventions

- [x] `agents/verilog-rtl-coder.md` — "constrained implementer" 골격 벤치마크(RTL taxonomy 부분 제외). **0.4 확인**: 이 파일에는 formal 파라미터 스키마도, "모드" 개념도 없음 — 스코프는 Task 프롬프트 자유 형식
- [x] `agents/verilog-tb-analyst.md` — "0. 기준" 정본 skill 목록, HANDS OFF 컨벤션 벤치마크
- [x] `install.py` agent 배포 스크립트 존재

### 8.2 Conventions to Define/Verify

| Category | Current State | To Define | Priority |
|----------|---------------|-----------|:--------:|
| TB "구조적 변경" 판단 기준 | 없음(RTL의 ARCH/IFACE/LOCAL 같은 자동 classifier 부재) | Design 단계에서 STOP-and-Ask 조건 목록(FR-08)을 구체 예시와 함께 확정 — 자동 도구는 만들지 않음(§2.2) | High |
| spec 참조 위치 컨벤션 | 프로젝트마다 다름(datasheet, 프로토콜 명세 등 표준 위치 없음) | Design 단계에서 "spec 위치를 모르면 어떻게 확인할지"(예: 프로젝트 CLAUDE.md나 `.ai/spec/`을 먼저 확인, 없으면 tb 분석서의 기대값 정의를 유일한 근거로 인정) 확정 | High |
| Task() 호출 시 프롬프트에 무엇을 담아야 하는지의 관례(0.4 갱신 — formal 스키마 대신 "권장 프롬프트 구조") | 이 문서 FR-05(스코프/근거/대상 파일 3요소를 자연어로 포함) | Design 단계에서 `agents/verilog-tb-coder.md`의 "0. 기준" 또는 별도 절에 권장 프롬프트 예시(fix-plan 경유/일반 요청 경유 각 1개)를 기재 | High |

---

## 9. Next Steps

1. [ ] 착수 전 §정합성 유지의 xcelium-mcp v1.34 §5.8 관련 절을 다시 Read — 버전이 바뀌었으면 이 문서 갱신 우선
2. [ ] `/pdca design verilog-tb-coder` — Tool 목록 최종 확정, Task 호출 규약(자유 형식 프롬프트 권장 구조, §8.2) 확정, STOP-and-Ask 조건 구체 예시 확정
3. [ ] `agents/verilog-tb-coder.md` 작성(`verilog-rtl-coder.md`+`verilog-tb-analyst.md` 골격 결합)
4. [ ] `install.py` 등록 + 배포 테스트
5. [ ] xcelium-mcp 쪽 §4.5/§5.8 서술과 최종 대조 — Task 호출 방식(자유 형식 프롬프트로 fix-plan 경로 전달) 불일치 없는지 확인
6. [ ] 의도적 순환 논리 시나리오(fix-plan.md 경유)로 FR-06 self-check(1차 필터) 수동 검증
7. [ ] (0.2 신규) 같은 시나리오를 `verilog-tb-reviewer`의 검토 단계까지 통과시켜, self-check을 우회한 경우에도 2차에서 실제로 걸러지는지 end-to-end 검증
8. [ ] (0.4 갱신) 동일한 순환 논리/모호한 스코프 시나리오를 fix-plan.md 없이 **사용자 직접 요청**으로 준 경우로도 반복 검증 — 두 호출 경로에서 동일한 STOP-and-Ask 결과가 나오는지 확인(호출 맥락 무관 균일성 검증)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-10 | 초안 — xcelium-mcp `xcelium-mcp-debug-workflow-v2.plan.md` v1.33에서 확정된 `fix_target=tb` 구현 주체 요구사항을 이 repo로 가져와 Plan 문서화. `verilog-rtl-coder.md`(constrained implementer 골격)와 `verilog-tb-analyst.md`("0. 기준" 정본 목록)를 결합한 자매 agent로 설계, RTL taxonomy(T1-T9/boundary-classifier)는 카테고리 오류를 피하기 위해 이식하지 않고 대신 spec 정당화 self-check(anti-tautology)를 이 agent의 핵심 규율로 신설 | HSLEE |
| 0.2 | 2026-07-10 | 사용자 지적("작성한 agent가 self-check한다는 것은 모순이 있는 것 같아")을 반영 — 0.1은 spec 정당화 self-check을 "이 agent의 핵심 규율"이자 사실상 유일한 방어선으로 서술했는데, 이는 `verilog-rtl-coder.md` §6이 명시적으로 경고하는 "구현자가 자기 정확성의 유일한 심판이 되는" 것과 동일한 모순이었다. 이를 바로잡기 위해 신규 자매 agent `verilog-tb-reviewer`(chip-design-skills 소유, `verilog-tb-reviewer.plan.md`로 별도 작성)를 도입하고, self-check을 "권위 있는 최종 판단"에서 "빠른 1차 필터"로 재정의. Requirement traceability 대상 버전을 xcelium-mcp v1.33→v1.34로 갱신. RTL+TB 동시 수정 케이스는 이 문서 범위가 아니며 xcelium-mcp v1.34가 "두 개의 독립된 fix-plan으로 분리"로 결정함(`fix_target="both"` 신설 안 함) | HSLEE |
| 0.3 | 2026-07-10 | 사용자 지적("verilog-tb-coder는 workflow-v2에서도 사용되고, 일반적인 tb coding에도 사용될 거야. stop and ask조건에 fix-plan만으로 한정하면 안 될 것 같아")을 반영 — 이 agent를 fix-plan.md 전용 입력에서 "Fix 모드"(fix-plan.md 기반)와 "General 모드"(사용자 명시 요구사항 `scope_description` 기반) 두 입력 경로로 이원화. FR-05에 `fix_plan_path`(optional)/`scope_description`(신규) 파라미터 분기 도입, `verilog-tb-reviewer` 검토를 Fix 모드는 강제/General 모드는 권장으로 차등 적용 | HSLEE |
| 0.4 | 2026-07-10 | 사용자 지적("근데 verilog-rtl-coder는 이미 구현되어 있잖아. 그건 workflow-v2에서 사용하기 부적합한가?")을 계기로 `agents/verilog-rtl-coder.md`를 실제로 Read해 확인한 결과, 그 파일에는 "fix-plan.md"/"fix_target"/"Fix 모드" 같은 workflow-v2 전용 개념이 전혀 없고, 애초에 호출 맥락을 가리지 않는 단일 균일 패턴(스코프는 Task 프롬프트가 자유 형식으로 선언, STOP-and-Ask는 소스 문서 종류와 무관)임을 확인(xcelium-mcp-debug-workflow-v2.plan.md v1.34의 실제 호출 서술 — "Task, fix-plan 파일 경로를 명시적으로 전달 + 지시"가 agent의 공식 파라미터가 아니라 프롬프트 컨텍스트일 뿐임을 대조 확인). 이에 따라 0.3에서 도입한 "Fix 모드/General 모드" 이원화(FR-05 파라미터 분기, FR-08(e) 별도 조건, §4.2 모드별 절차, DoD/Handoff의 강제·권장 차등)를 전부 철회하고, `verilog-rtl-coder`와 동일한 단일 균일 규율로 재설계: Task 호출은 자유 형식 프롬프트(FR-05), STOP-and-Ask 조건은 호출 맥락 무관 공통(FR-08), `verilog-tb-reviewer` 인계는 호출 맥락과 무관하게 항상 무조건 수행(FR-06/FR-10, `verilog-rtl-coder`의 self-certify 금지 원칙과 동일 정신으로 재정렬). Executive Summary, Context Anchor, §1.1, §1.2, §2.1/§2.2, §3.1 전체, §3.2, §4.2, §5, §6, §7.2, §8.2, §9 전면 갱신 | HSLEE |
| 0.5 | 2026-07-21 | 사용자 지적("testbench도 architecturing을 잘 해야 확장성·재사용성이 높아진다")을 계기로 신설된 `verilog-tb-architect-advisor`(`verilog-tb-architect-advisor.plan.md`)의 route 대상으로 §2.1/FR-08(c)를 갱신 — "구조적 변경으로 보이는 경우 사람에게 직접 STOP-and-Ask"를 "이 agent로 route, 그 agent가 재사용범위 판단표+ADR+adversarial cross-review를 거친 뒤 사람에게 넘김"으로 변경. TB용 자동 classifier가 여전히 없다는 사실 자체는 바뀌지 않음(§2.2 Out of Scope 그대로 유지) | HSLEE |
| 0.6 | 2026-07-22 | Do 완료 후 gap-detector 검증(Match Rate 99.2%) 결과 반영 — FR-12/§7.1 "install.py AGENTS 목록 등록" 문구가 실제 메커니즘(별도 목록 없음, `agents/*.md` glob 자동 인식)과 달라 정정(`verilog-tb-architect-advisor.plan.md` 0.2와 동일한 정정) | HSLEE |
