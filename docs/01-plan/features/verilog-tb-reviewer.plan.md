# verilog-tb-reviewer Planning Document

> **Summary**: TB(테스트벤치) 소스 변경(diff)을 spec 정당화·checker 완화·범위 준수·구조적 변경 여부 관점에서 독립적으로 검토하는 read-only agent — **호출 맥락과 무관**하게 동일하게 동작한다(0.4 갱신: xcelium-mcp Fix Sub-cycle의 fix-review 게이트를 채우는 데도 쓰이지만, 그와 무관한 일반 TB 리뷰 요청 — "이 TB 변경 검토해줘", "이 checker 완화 아닌지 봐줘" — 에도 동일한 절차로 응답한다). `verilog-rtl-reviewer`와 정확히 대칭되는 TB 쪽 자매 agent이며, `verilog-tb-coder`가 스스로 수행하는 spec 정당화 self-check을 "빠른 1차 필터"로 두고 이 agent가 "권위 있는 최종 판단"을 내림으로써, 구현 당사자가 자기 작업을 스스로 인증하는 모순(anti-tautology 위반)을 해소한다.
>
> **Project**: chip-design-skills
> **Version**: 0.4
> **Author**: HSLEE
> **Date**: 2026-07-22
> **Status**: Draft

---

## ⚠️ 정합성 유지 — 이 문서를 고치기 전에 반드시 읽을 것

`verilog-tb-coder.plan.md`/`verilog-tb-analyst.plan.md`/`verilog-rtl-debugger.plan.md`와 동일한 cross-repo 계약 구조다. 요구사항 정본은 이 repo가 아니라 **xcelium-mcp**에 있다.

### 요구사항 정본 (xcelium-mcp repo, 절대경로)

| 문서 | 절대경로 | 참조 섹션 | 확인 시점 버전 |
|------|---------|----------|----------------|
| debug workflow v2 (Fix Sub-cycle, fix-review TB 경로 원본) | `C:\Users\HSLEE\Documents\Todoc\fpga\xcelium-mcp\docs\01-plan\features\xcelium-mcp-debug-workflow-v2.plan.md` | §5.8 "Fix Target: RTL vs TB", §5.8 "4) fix-review"(TB 경로), §4.5 매핑 표 "debug (TB, 근본원인·수정 구현)" 행. **(0.3 갱신)** v1.35가 추가한 "기록=출력" 절차(사람 구현자에게 findings 전달 시 `fix-review.md` append와 채팅 출력 텍스트를 동일하게 유지) 확인 필요 | v1.36 (2026-07-21, 0.3에서 v1.34→v1.36으로 버전 pin 갱신) |

### 계약 요약 (2026-07-10 시점)

**왜 신설하는가**: xcelium-mcp v1.33은 `verilog-tb-coder`(TB 전용 구현 agent) 신설과 함께, 그 agent 자신이 "spec 정당화 self-check"을 수행해 anti-tautology를 방어하도록 설계했다. 그러나 이는 `verilog-rtl-coder`가 이미 확립한 원칙 — "너는 의도(intent)를 스스로 인증하지 않는다. 정확성 property는 Prover가 구현과 독립적으로 저작한다"(coder §6 anti-tautology) — 와 정면으로 모순된다. 구현 당사자가 "내가 쓴 코드가 spec에 맞다"를 스스로 판단하면, 바로 그 판단 자체가 tautology(자기 인증)가 되어 방어 장치로서 무력화될 위험이 있다(사용자 지적: "작성한 agent가 self-check한다는 것은 모순이 있는 것 같다"). 이 agent는 `verilog-tb-coder`(또는 사람)의 TB 구현을 **독립적으로** 재검토해, RTL 쪽의 "coder self-check(구조적 필터) + reviewer/prover 독립 검증(정확성 판단)"이라는 2단 방어 구조를 TB 쪽에도 동일하게 적용한다.

또한 사용자는 "testbench도 architecturing이 가능하고 더 잘 만들게 할 수도 있잖아"라고 지적했다 — 이 agent의 역할은 단순히 "버그를 잡는 것"에 그치지 않고, TB 구조/coverage 관점에서 더 나은 방법이 있는지도 검토 대상에 포함한다(단, architecture를 **결정**하지는 않는다 — RTL의 reviewer가 architect-advisor에 판단을 넘기듯, 이 agent도 구조적 변경으로 보이는 항목은 스스로 판정하지 않고 **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 route한다).

**방법론 출처(중요 — 중복 금지)**: 이 agent는 TB 아키텍처 규칙을 system prompt에 복사해 내장하지 않는다 — `verilog-tb-analyst`/`verilog-tb-coder`가 이미 확립한 "0. 기준 — 시작 시 반드시 로드" 컨벤션을 그대로 재사용해, `verilog-rtl`/`chip-verification`/`uvm-verification` skill을 런타임에 전체 Read한다.

**RTL taxonomy를 이식하지 않는 이유**: `verilog-rtl-reviewer`는 `failure-taxonomy.md`(T1-T9)와 `bug-class-router.py`라는 정교한 도구 체계를 갖고 있지만, 이는 6개 ground-truth RTL 버그의 forensic 분석에서 귀납적으로 도출된 것이다. TB 버그에 대한 동등한 evidence base가 이 생태계에 아직 없으므로, 이 agent는 억지로 그 체계를 흉내 내지 않고 **자기 도메인에 맞는 축소된 검토 항목**(§4)만 가진다 — 필요성이 실전에서 확인되면 후속 feature로 정식 taxonomy를 만들 수 있다(YAGNI).

---

## Executive Summary

| Perspective | Content |
|-------------|---------|
| **Problem** | (1) `verilog-tb-coder`(또는 사람)의 TB 구현을 독립적으로 검증하는 agent가 없어, anti-tautology 원칙이 TB 쪽에서만 깨져 있었다 — 구현 당사자의 self-check이 유일한 방어선. (2) **(0.4 갱신)** 이와 별개로, xcelium-mcp 워크플로우와 무관한 일반 TB 리뷰 수요("이 TB 변경 검토해줘")도 항상 존재하는데, 0.1~0.3은 이 agent를 fix-review 게이트 전용으로만 서술해 `verilog-tb-coder`가 0.3→0.4에서 겪은 것과 동일한 "특정 flow 종속" 오류를 그대로 반복하고 있었다 |
| **Solution** | `verilog-rtl-reviewer`와 대칭되는 TB 전용 read-only 검토자 신설 — spec 정당화 최종 판단, checker 완화 탐지, 범위 준수, 구조적 변경 의심 refer. **(0.4 갱신)** 호출자가 xcelium-mcp workflow-v2든 사람의 직접 리뷰 요청이든 **동일한 단일 절차**로 응답 — fix-plan.md는 근거의 한 형태일 뿐, 필수 입력이 아니다 |
| **Function/UX Effect** | xcelium-mcp `/sim debug`의 `fix_target=tb` fix-implement 완료 직후 이 agent가 자동 호출돼 fix-review 게이트를 채움(문제 발견 시 fix-implement로 되돌림, clean이면 `/sim verify`로 진행) — **뿐만 아니라(0.4 갱신)**, 그와 무관하게 사람이 "이 TB diff/커밋을 검토해줘"라고 직접 요청해도 동일한 검토 절차·동일한 엄격도로 응답한다 |
| **Core Value** | TB fix도 RTL fix와 동급의 "구현자 self-check + 독립 검증자" 2단 방어 구조를 갖게 되어, "TB를 완화해 진짜 RTL 버그를 숨기는" 가장 위험한 실패 양상을 정면으로 방어. 이 방어는 특정 워크플로우에 종속되지 않으므로, TB 코드를 다루는 모든 맥락에서 재사용 가능하다(0.4 갱신) |

---

## Context Anchor

| Key | Value |
|-----|-------|
| **WHY** | `verilog-tb-coder`의 self-check만으로는 anti-tautology를 구조적으로 보장할 수 없음(자기 인증의 모순). **(0.4 갱신)** 동시에 이 agent 자체가 특정 워크플로우(xcelium-mcp)에 종속되지 않고 일반적으로 재사용 가능해야 함 — `verilog-rtl-coder`/`verilog-tb-coder` 등 이 repo의 다른 agent들이 이미 지키는 원칙 |
| **WHO** | **(0.4 갱신)** xcelium-mcp `/sim` 워크플로우를 사용해 RTL/TB 검증을 수행하는 AI 에이전트, **그리고** 이와 무관하게 TB 코드 변경을 독립적으로 검토받고 싶은 모든 프로젝트의 사람/AI 에이전트(일반 리뷰 요청) — 호출 경로가 다르다고 이 agent의 검토 규율이 달라지지 않는다 |
| **RISK** | 이 agent 자신도 spec 참조 없이 "코드가 그럴듯해 보인다"로 안이하게 clean 판정을 내리면 방어선으로서 무력화됨 — RTL reviewer의 "STATIC vs SIM 정직성 계약"과 동급의 엄격함이 필요 |
| **SUCCESS** | 순환 논리(anti-tautology 위반) 근거를 담은 fix-plan/구현을 실제로 잡아내 fix-implement로 되돌림; 정당한 fix는 불필요하게 막지 않음. **(0.4 갱신)** fix-plan.md 경유든 사람의 직접 리뷰 요청이든 동일한 시나리오에서 동일한 결과가 나옴(호출 맥락 무관 균일성) |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-reviewer.md`) 작성만(install.py는 glob 자동 인식, 별도 등록 불필요) |

---

## 1. Overview

### 1.1 Purpose

TB 소스 diff를 호출 시 제시된 근거(선언된 범위 + 근거 — **그 근거가 fix-plan.md의 "근본원인 소재 판정"이든, 사람이 직접 진술한 리뷰 요청이든 형태만 다를 뿐 처리는 동일**, 0.4 갱신)와 대조해 spec 정당화·checker 완화·범위 준수·구조적 변경 여부를 독립적으로 검토한다. xcelium-mcp workflow-v2 맥락에서는 문제 발견 시 fix-implement로 되돌리는 fix-review 게이트로 소비되고, 그 밖의 맥락(일반 리뷰 요청)에서는 findings를 그대로 사람에게 보고한다 — 이 agent 자신의 검토 절차(§4)는 두 경우 모두 동일하다.

### 1.2 Background

`verilog-rtl-reviewer`는 이 repo의 "STATIC vs SIM 정직성 계약"(§0), "명시적 라우팅"(SIM-RISK를 가장 싼 신뢰 가능한 owner에게), "architect-advisor와의 역할 분담"(구조 판정은 하지 않고 refer만)이라는 세 가지 설계 축을 확립해뒀다. `verilog-tb-reviewer`는 이 중 **처음과 세 번째 축을 재사용**하고, 두 번째 축(SIM-RISK 라우팅)은 재사용하지 않는다:

- **재사용**: "정적으로 확정 가능한 것과 아닌 것을 구분해 정직하게 보고한다" — TB도 "spec 대비 명백히 어긋남"(정적 확정 가능)과 "실제 동작해봐야 아는 것"(시뮬레이션 필요, `/sim verify`로 위임)을 구분한다.
- **재사용**: "구조적 변경 의심은 스스로 판정하지 않고 refer한다" — **(2026-07-21 갱신)** 신설된 `verilog-tb-architect-advisor`로 route한다(§2.2 Out of Scope).
- **재사용 안 함**: RTL의 SIM-RISK는 Prover/formal, directed sim, STATIC reachability 3개 owner로 정교하게 라우팅되는데, TB 버그의 "시뮬레이션 필요" 판정은 이미 `/sim verify`(xcelium-mcp)라는 단일 owner로 귀결되므로 별도 라우팅 로직이 필요 없다 — 훨씬 단순하다.

**0.3 갱신 — Task() 입력 형식도 `verilog-rtl-reviewer` 벤치마크로 정정**: 0.1 초안의 FR-04는 `fix_plan_path`/`env`/`files_changed`/`implementer` 4개를 formal 파라미터로 명시했으나, 실제 `agents/verilog-rtl-reviewer.md`를 확인한 결과 그 파일에는 named parameter 표 자체가 없다 — 리뷰 대상(diff·모듈 범위)을 프로즈로 받는다. 이는 `verilog-tb-coder.plan.md`가 0.3→0.4에서 "Fix 모드/General 모드" formal 스키마를 철회하고 자유 형식 프롬프트로 정정한 것과 동일한 종류의 실수였다 — TB 패밀리(analyst 제외, coder/architect-advisor는 이미 자유 형식) 안에서 이 agent만 formal 스키마를 갖는 비일관성을 FR-04에서 바로잡는다.

**0.4 갱신 — 이 agent는 xcelium-mcp workflow-v2 전용이 아니다(중요, `verilog-tb-coder` 0.4와 동일한 교훈의 재적용)**: 0.3까지의 수정은 frontmatter 구조·model·정직한 한계 등 **agent 파일의 스타일 일관성**을 다뤘지만, §1.1 Purpose·§2.1 Scope·§4 검토 절차 자체는 여전히 "fix-plan.md가 항상 존재한다"고 가정하고 쓰여 있었다 — 이는 정확히 `verilog-tb-coder.plan.md`가 0.3에서 저질렀다가 0.4에서 철회한 실수(호출 맥락에 따라 다른 "모드"를 상정하는 설계)의 또 다른 얼굴이다. `verilog-tb-coder`가 이미 확립한 패턴을 그대로 재사용한다: 이 agent는 "무엇을 왜 검토하는가"(범위+근거)를 Task 프롬프트로 받되, 그 근거가 fix-plan.md에서 왔는지 사람의 직접 요청에서 왔는지 **agent 입장에서 구분하지 않는다.** §4의 모든 검토 절차는 "호출 시 제시된 근거/범위"라는 중립적 표현으로 재서술한다(§4.1/§4.3 참조) — "fix-plan.md" 문구는 그 근거가 실제로 fix-plan.md 형태일 때의 **예시**로만 남긴다.

### 1.3 Related Documents

- **요구사항 정본**: §정합성 유지 절의 xcelium-mcp 문서
- **대칭 agent(다른 도메인, 동일 컨벤션)**: `agents/verilog-rtl-reviewer.md` — "STATIC vs SIM 정직성 계약", "architect-advisor와의 역할 분담", 보고서/Manifest 구조를 벤치마크(단, T1-T9 taxonomy·`bug-class-router.py`는 이식하지 않음)
- **직접 대응 agent(구현 당사자)**: `agents/verilog-tb-coder.md`(chip-design-skills, 이 문서와 같은 세션에서 함께 갱신) — self-check을 1차 필터로 격하하고 이 agent를 최종 판단자로 참조하도록 이미 갱신됨
- **자매 agent(동일 도메인, 다른 역할)**: `agents/verilog-tb-analyst.md` — "0. 기준" 정본 skill 목록 벤치마크

---

## 2. Scope

### 2.1 In Scope

- [ ] `agents/verilog-tb-reviewer.md` 신규 작성 — `verilog-rtl-reviewer.md`의 "STATIC vs SIM 정직성 계약"·"architect-advisor 역할 분담"·보고서/Manifest 골격을 TB 도메인에 맞게 재구성(taxonomy T1-T9/`bug-class-router.py`는 이식 안 함, §2.2 참조) — 대신 §4의 TB 자체 검토 항목으로 대체
- [ ] "0. 기준 — 시작 시 반드시 로드" 절: `verilog-tb-analyst.md`/`verilog-tb-coder.md`와 동일한 정본 목록 — `~/.claude/skills/verilog-rtl/SKILL.md`(전체), `~/.claude/skills/chip-verification/SKILL.md`(전체, **0.3 갱신** — `references/non-uvm-architectures.md` 포함, `verilog-tb-coder`/`verilog-tb-architect-advisor`와 동일 근거), `~/.claude/skills/uvm-verification/SKILL.md`(전체), `~/.claude/skills/ssh-mcp/SKILL.md`(전체, `mcp__ssh__*` 가용 시에만)
- [ ] Tool 목록: `Read, Glob, Grep, Bash, Write` + `mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls`(read-only, `verilog-rtl-reviewer`와 동일하게 Write는 보고서 파일에만 — TB 소스 원격 접근은 read-only 3종으로 충분, `file_write` 불필요)
- [ ] **spec 정당화 최종 판단(§4.1, 이 agent의 핵심 규율)**: 호출 시 제시된 근거(fix-plan.md의 "근본원인 소재 판정"이든, 사람의 직접 리뷰 요청에 담긴 진술이든 — **0.4 갱신, 형태 무관 동일 처리**)와 실제 diff를 대조해, spec/tb 분석서를 실제로 인용하는지, `verilog-tb-coder`의 self-check을 통과했더라도(구현자가 있는 경우에 한함) 순환 논리("RTL에 맞춘다")가 남아있지 않은지 **독립적으로 재확인**
- [ ] checker 완화 탐지(§4.2): assertion 삭제, 조건 범위 확장, expected value 완화 등 diff에서 "검증을 약화시키는" 패턴 탐지
- [ ] 선언된 범위 준수 확인(§4.3, **0.4 갱신 — "fix-plan 범위"에서 일반화**): 호출 시 명시된 스코프(fix-plan.md의 `affected_paths`든, 사람이 직접 지정한 대상 파일 목록이든) 밖의 변경 여부
- [ ] 구조적 변경 의심 refer(§4.4): 새 시퀀스 클래스/UVM 컴포넌트 추가처럼 보이면 `[TB-ARCH-SUSPECT]`로 표시하고 판정하지 않고 **(2026-07-21 갱신)** 신설된 `verilog-tb-architect-advisor`로 route(그 agent가 재사용범위 판단표+ADR+adversarial cross-review를 거쳐 사람에게 최종 판단을 넘김 — `verilog-tb-architect-advisor.plan.md` 참조)
- [ ] TB 컨벤션 준수 확인(§4.5): `verilog-rtl`/`chip-verification`/`uvm-verification` skill 대비 문법/구조 정합
- [ ] `.ai/analysis/tb_*.analysis.md` 정합성 확인(§4.6): 이 diff 이후에도 분석서가 유효한지, stale이면 `verilog-tb-analyst` 라우팅 권고
- [ ] 보고서 생성(`.ai/reviews/{target}-tb-{YYYYMMDD}.review.md`, **0.4 갱신 — "{test}"에서 일반화**: 대상이 testcase가 아니라 공유 시퀀스/컴포넌트일 수도 있으므로 `verilog-rtl-reviewer`의 `{target}` 표기를 재사용) + verdict(`clean`/`issues_found`, xcelium-mcp `fix_review.status`와 동일 enum) + Manifest 반환
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
| FR-01 | **(0.3 갱신 — family 일관성)** `agents/verilog-tb-reviewer.md` frontmatter — `name`/`description`/`tools`/`model` 4-field 구조. `description`은 **TB 패밀리 표준**(`verilog-tb-analyst`/`verilog-tb-coder`/`verilog-tb-architect-advisor` 전부 채택)인 **"Use it when: / Do NOT use for: / Triggers:" 3-part**를 명시적으로 포함한다 — `verilog-rtl-reviewer`는 "Do NOT use for:"가 없지만(구식), TB 시리즈 내부 일관성을 우선한다(사용자 지시). **(0.4 갱신 — 일반 사용 트리거 추가)** Triggers 예시: "TB 리뷰", "fix-review TB", "testcase 검토", "checker 완화 확인", "이 TB 변경 검토해줘", "TB diff 리뷰", "테스트벤치 코드 리뷰"(workflow-v2 무관 일반 요청도 명시 — `verilog-tb-coder` FR-01의 "테스트케이스 추가, 시나리오 보강" 트리거 확장과 동일 정신) | High | Pending |
| FR-02 | Tool 목록: `Read, Glob, Grep, Bash, Write, mcp__ssh__file_read, mcp__ssh__file_grep, mcp__ssh__file_ls`(read-only, Write는 보고서 전용). `model: opus` — 프로젝트 규칙(구현=Sonnet, 분석/리뷰=Opus)과 `verilog-rtl-reviewer`/`verilog-tb-analyst`/`verilog-tb-architect-advisor` 전부와 동일 기준(**0.3 신규 — 이전 버전에 model 명시가 누락돼 있었음**) | High | Pending |
| FR-03 | "0. 기준"에 `verilog-tb-analyst`/`verilog-tb-coder`와 동일한 4~5개 정본 Read 지시(전체 로드, 부분로딩 금지). **(0.3 갱신)** `chip-verification/SKILL.md`는 `references/non-uvm-architectures.md`까지 포함해 Read — `verilog-tb-coder`/`verilog-tb-architect-advisor`가 legacy/non-UVM TB도 다루는 것과 동일한 이유(§4.5 TB 컨벤션 준수 확인이 non-UVM TB에도 적용돼야 함). `verilog-tb-analyst`는 이 참조를 로드하지 않지만, 이 agent는 "컨벤션 준수 확인"이라는 판단 역할이라 tb-coder 쪽 근거를 따른다 | High | Pending |
| FR-04 | **(0.3 갱신 — formal 스키마 철회, 0.4 갱신 — 호출자 범위 명확화)** Task() 입력은 `verilog-rtl-reviewer`와 동일하게 **formal 파라미터 스키마 없이** 리뷰 대상을 프로즈로 받는다. 호출자는 **xcelium-mcp fix-review 단계, 사람의 일반 리뷰 요청, 또는 다른 agent** 중 무엇이든 될 수 있으며(`verilog-tb-coder` FR-05와 동일 원칙), Task 프롬프트에 (a) 리뷰 대상(diff·변경 파일 목록·env), (b) fix-plan.md 경로(있으면 — 없으면 사람이 직접 진술한 근거로 대체), (c) 구현 주체(`verilog-tb-coder`/사람 — 참고용 기록일 뿐 검토 엄격도는 무관하게 동일)를 자연어로 포함하는 것을 권장한다. 이 agent는 이름 붙은 필드로 분기하지 않으며, 호출자가 xcelium-mcp인지 사람인지에 따라 절차를 바꾸지 않는다(0.4 핵심). 위 정보가 특정 불가할 만큼 불명확하면 BLOCKER로 명시(추측 금지) | High | Pending |
| FR-05 | **spec 정당화 최종 판단(핵심 규율)**: §4.1 절차대로 호출 시 제시된 근거(fix-plan.md든 사람의 직접 리뷰 요청이든, **0.4 갱신**)를 spec/tb 분석서 대비 독립 재확인 — self-check을 통과했어도(구현자가 있는 경우) 예외 없이 재검토(defense-in-depth). **(0.3 신규)** 각 finding에 §4.1a의 `[TB-STATIC]`/`[TB-NEEDS-SIM-VERIFY]` 라벨을 표기해 `verilog-rtl-reviewer`의 STATIC/SIM 정직성 계약을 finding 단위로 실제 적용(이전 버전은 원칙만 선언하고 메커니즘이 없었음) | High | Pending |
| FR-06 | checker 완화 탐지(§4.2): assertion/조건 제거·완화 diff 패턴 탐지 | High | Pending |
| FR-07 | **(0.4 갱신 — 일반화)** 선언된 범위 준수 확인(§4.3): fix-plan.md의 `affected_paths`든 사람이 직접 지정한 대상 파일 목록이든, 호출 시 명시된 스코프 밖의 변경 여부 확인 | High | Pending |
| FR-08 | 구조적 변경 의심 시 `[TB-ARCH-SUSPECT]`로 표시하고 판정 대신 **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 refer(§4.4) | High | Pending |
| FR-09 | TB 컨벤션 준수 확인(§4.5), `.ai/analysis/tb_*.analysis.md` 정합성 확인 + stale 시 `verilog-tb-analyst` 라우팅 권고(§4.6) | Medium | Pending |
| FR-10 | 보고서 `.ai/reviews/{test}-tb-{YYYYMMDD}.review.md` 생성(유일한 Write 대상) — Summary/spec 정당화 판정/checker 완화 findings/범위 준수/TB-ARCH-SUSPECT/컨벤션/분석서 상태/Verdict 섹션 포함. **경로에 `-tb-` infix를 유지**(`verilog-rtl-reviewer`의 `{target}-{YYYYMMDD}.review.md`와 달리) — 같은 `.ai/reviews/` 디렉터리에 동일 test 이름의 RTL/TB 리뷰가 공존할 수 있어 충돌 방지 목적, 임의 편차 아님 | Medium | Pending |
| FR-11 | Manifest 반환: 보고서 경로, verdict(`clean`/`issues_found`), findings 개수, TB-ARCH-SUSPECT 여부, 분석서 상태(+ tb-analyst 라우팅 여부). **verdict가 `verilog-rtl-reviewer`의 3-way(`BLOCK`/`CONDITIONAL`/`PASS`)가 아니라 2-way인 이유(0.3 검증 완료)**: xcelium-mcp `xcelium-mcp-debug-workflow-v2.plan.md` L637-639/L918이 `sim-state.json`의 `fix_review.status`를 정확히 `"clean"`/`"issues_found"` 2-value로 정의하는 **cross-repo 계약**이다 — 이 agent가 임의로 만든 편차가 아니라 실제로 소비하는 쪽(xcelium-mcp)의 스키마를 그대로 따른 것이므로 RTL과 다르게 유지한다 | Medium | Pending |
| FR-12 | `agents/verilog-tb-reviewer.md` 배포 확인 — **(0.3 갱신)** `install.py`에 별도 AGENTS 목록은 없음(glob 자동 인식), `--dry-run`으로만 확인 | Medium | Pending |

### 3.2 Non-Functional Requirements

| Category | Criteria | Measurement Method |
|----------|----------|---------------------|
| 독립성 | `verilog-tb-coder`의 self-check 결과에 의존하지 않고 항상 처음부터 재검토 | 리뷰 절차에 "self-check 결과 무시하고 독립 재확인" 명시 여부 확인 |
| Anti-tautology 최종 방어 | 순환 논리 fix-plan을 실제로 걸러내는지 | 의도적 순환 논리 시나리오 테스트 |
| 컨벤션 일관성 | `verilog-rtl-reviewer.md`(STATIC/SIM 계약, 역할 분담)와 구조·톤 일관 | agent 파일 diff 리뷰 |
| **(0.4 신규) 워크플로우 비종속성** | fix-plan.md 경유 호출과 사람의 직접 리뷰 요청 경유 호출에서 §4 검토 절차·verdict 판정 결과가 동일한지 | 동일 시나리오를 두 경로로 각각 호출해 대조(§5.1 DoD 0.4 신규 항목) |

---

## 4. `verilog-tb-reviewer`의 검토 항목 (Design 단계에서 agent 파일로 구체화할 핵심 내용)

> RTL reviewer의 taxonomy(T1-T9)에 대응하는 TB 자체 항목 — 정식 catalog 파일 없이 이 문서·agent 파일에 직접 정의(evidence base가 아직 없어 YAGNI).

### 4.1 spec 정당화 최종 판단 (가장 중요)

> **(0.4 갱신 — 호출 맥락 무관 일반화)** 아래 "근거"는 fix-plan.md의 "근본원인 소재 판정"일 수도, 사람이
> Task 프롬프트에 직접 진술한 리뷰 요청("이 checker를 이렇게 바꿨는데 spec §4.1 tolerance 규정 때문이야")일
> 수도 있다 — 이 agent는 그 출처를 구분하지 않고 동일한 절차를 적용한다. `verilog-tb-coder`가 있었다면(즉
> 구현자가 AI인 경우) 그 self-check 결과가 참고 가능하지만, 사람이 직접 구현한 경우 self-check 자체가
> 없을 수 있다 — 이 경우에도 절차는 동일하게 처음부터 수행한다(있으면 무시, 없어도 절차 자체는 안 바뀜).

1. 호출 시 제시된 근거(fix-plan.md의 "근본원인 소재 판정"이든, 사람의 직접 리뷰 요청 진술이든)를 `verilog-tb-coder`의 self-check 결과(있으면)와 **무관하게 처음부터** 재확인한다.
2. spec(또는 `.ai/analysis/tb_{env}_*.analysis.md`의 판별 신호/기대값 정의)을 실제로 인용하는지 확인.
3. "RTL이 이렇게 동작하니 TB를 맞춘다"류 순환 논리로 보이면 `[issues_found]`로 종결 — self-check을 통과했어도 예외 없음.

### 4.1a 개별 finding의 STATIC/SIM 정직성 라벨 (0.3 신규 — §1.2 "재사용" 축을 실제 메커니즘으로 구체화)

§1.2가 `verilog-rtl-reviewer`의 "STATIC vs SIM 정직성 계약"(정적으로 확정 가능한 것과 시뮬레이션 없이는
못 미는 것을 절대 섞지 않는다)을 재사용한다고 선언했으나, 0.1~0.2는 이를 배경 원칙으로만 서술하고 실제
절차에 반영하지 않았다 — 이 절에서 구체화한다. **overall verdict는 여전히 xcelium-mcp 계약상
`clean`/`issues_found` 2-way로 고정**(FR-11, 변경 없음)이며, 이 라벨은 **개별 finding**에만 붙인다:

- `[TB-STATIC]`: diff·호출 시 제시된 근거 문서(fix-plan.md 또는 spec/analysis 인용)만으로 정적으로 확정
  가능(§4.1~4.4 대부분 — 예: assertion 삭제, spec 인용 부재는 diff·문서 대조만으로 확정됨)
- `[TB-NEEDS-SIM-VERIFY]`: 정적으로는 의심되나 실제 동작 결과로만 확정되는 경우(예: checker 완화가 실제로
  어떤 실패를 놓치는지는 `/sim verify` 실행 결과로만 확인 가능) — 이 라벨이 붙어도 그 finding 자체는
  여전히 보고서에 기록되고 verdict 판정(§4.7)에 포함되나, "정적으로 100% 확정했다"고 과장하지 않는다

이 라벨은 보고서(FR-10)의 각 finding 항목에 표기하며, Manifest(FR-11) aggregate verdict 계산 방식(§4.7)에는
영향을 주지 않는다 — "정직하게 라벨링" 축과 "xcelium-mcp의 2-way 계약" 축은 서로 다른 레벨(finding-level
vs report-level)이라 공존 가능하다.

### 4.2 checker 완화 탐지

diff에서 다음 패턴이 있으면 "spec 정당화 없이 검증을 약화시킨 것"으로 의심하고 §4.1과 교차 확인:
- assertion/check 조건 삭제 또는 범위 확장(예: `==` → `<=`로 느슨해짐)
- expected value 자체가 실제 RTL 출력값으로 치환됨(가장 위험한 패턴 — anti-tautology 직접 위반 시그니처)
- 테스트 실패 조건 분기 자체가 제거됨

### 4.3 선언된 범위 준수 (0.4 갱신 — "fix-plan 범위 준수"에서 일반화)

diff가 호출 시 선언된 범위 밖의 파일/테스트를 건드렸는지 확인 — 그 범위가 fix-plan.md의 `affected_paths`(영향
테스트/시퀀스/checker 목록)로 왔든, 사람이 직접 리뷰 요청에서 "이 파일들만 바꿨어"라고 지정한 목록으로
왔든 동일하게 대조한다. 범위 자체가 불명확하면(호출 시 아무 범위도 제시되지 않음) diff에서 변경된 파일
전체를 대상으로 §4.1~4.2를 적용하되, 그 사실(범위 미제시)을 보고서에 명시한다.

### 4.4 구조적 변경 의심 (TB-ARCH-SUSPECT)

새 시퀀스 클래스, 새 UVM agent/컴포넌트 추가처럼 보이면 판정하지 않고 `[TB-ARCH-SUSPECT]`로 표시, 보고서 Verdict에 명시해 **(2026-07-21 갱신)** `verilog-tb-architect-advisor`로 refer한다 — 그 agent가 재사용범위 판단표+ADR+adversarial cross-review를 거쳐 최종적으로 사람에게 넘긴다.

### 4.5 TB 컨벤션 준수

"0. 기준"에서 로드한 `verilog-rtl`(SV 문법)/`chip-verification`(듀얼탑)/`uvm-verification`(UVM 계층) 정본 대비 diff의 문법/구조 정합 확인.

### 4.6 분석서 정합성

`.ai/analysis/tb_{env}_*.analysis.md`가 이 diff 이후에도 여전히 유효한지 확인 — stale이면 `verilog-tb-analyst` 라우팅을 보고서에 권고.

### 4.7 Verdict

- `issues_found`: §4.1~4.4 중 하나라도 문제 발견(spec 미정당화, checker 완화, 범위 이탈, TB-ARCH-SUSPECT 미해결) — `[TB-STATIC]`/`[TB-NEEDS-SIM-VERIFY]`(§4.1a) 어느 라벨이든 finding이 있으면 `issues_found`로 집계(xcelium-mcp는 2-way만 소비하므로 라벨 종류가 verdict 값 자체를 바꾸지 않음)
- `clean`: 위 전부 통과(§4.5/4.6은 권고 사항이라 통과 여부에 영향 없음 — 정보성)

---

## 5. Success Criteria

### 5.1 Definition of Done

- [ ] `agents/verilog-tb-reviewer.md` 작성 완료 — §4 검토 항목이 구체적 절차로 명시, 보고서/Manifest 형식 포함
- [ ] **(0.3 신규 — family 일관성)** "왜 model: opus 인가" 명시적 헤더 포함(`verilog-rtl-reviewer`/`verilog-rtl-analyst`/`verilog-rtl-prover`/`verilog-rtl-debugger` 전부가 채택한 컨벤션 — 분석/리뷰 작업은 Opus라는 근거를 이 agent 자신의 역할에 맞게 서술)
- [ ] **(0.3 신규 — TB family 내부 일관성)** "정직한 한계" 섹션 포함 — `verilog-tb-analyst`/`verilog-tb-coder`/`verilog-tb-architect-advisor` 전부가 갖고 있는 섹션(direct 벤치마크인 `verilog-rtl-reviewer`엔 이 섹션이 없지만, 사용자 지시대로 TB 시리즈 내부 일관성을 우선)
- [ ] `agents/verilog-tb-reviewer.md` 배포 확인 — **(0.3 갱신, verilog-tb-architect-advisor.plan.md 0.2/verilog-tb-coder.plan.md 0.6과 동일한 정정)** `install.py`에 별도 AGENTS 목록은 없음(`agents/*.md` glob 자동 인식), `--dry-run`으로 확인만
- [ ] xcelium-mcp v1.36의 fix-review TB 경로 서술과 Task() 인터페이스 최종 대조 — v1.35 "기록=출력" 절차(사람 구현자 경로) 반영 여부 포함
- [ ] 의도적 순환 논리 시나리오(`verilog-tb-coder`의 self-check을 통과하도록 교묘하게 작성된 fix-plan)로 이 agent가 여전히 잡아내는지 수동 검증 — self-check 실패 검증만으로는 부족함을 확인하는 것이 핵심
- [ ] **(0.4 신규)** 동일한 순환 논리 시나리오를 fix-plan.md 없이 **사람의 직접 리뷰 요청**으로 준 경우로도 반복 검증 — 두 호출 경로에서 동일한 `issues_found` 판정이 나오는지 확인(호출 맥락 무관 균일성 검증, `verilog-tb-coder.plan.md` §9 8번 항목과 대칭)

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
| `install.py` | 스크립트(변경 없음) | 별도 목록 편집 불필요 — glob 자동 인식 확인만(0.3 갱신) |

### 7.2 Current Consumers

| Resource | Operation | Code Path | Impact |
|----------|-----------|-----------|--------|
| **외부 계약(예정)**: xcelium-mcp `/sim` Skill(v1.36 §5.8 "4) fix-review" TB 경로) | INVOKE(완성 후) | `fix_target=tb`의 fix-implement 완료 직후 항상 호출. 구현 주체가 사람이면 v1.35 "기록=출력" 절차상 이 agent의 findings가 Skill을 거쳐 사람에게 전달됨(에이전트 자신이 사람에게 직접 전달하지 않음) | Needs verification |
| **외부 계약(예정)**: 일반 사용자/AI 에이전트의 직접 TB 리뷰 요청(workflow-v2 무관, **0.4 신규** — `verilog-tb-coder` §7.2의 동일 항목과 대칭) | INVOKE | 사용자가 직접 Task 위임(자유 형식 프롬프트로 리뷰 대상 + 근거 전달, fix-plan.md 없음) | Needs verification — 별도 승인 게이트 없이 바로 호출되므로 §4 검토 절차가 유일한 방어선임을 사용자에게 주지시킬 필요 |

---

## 8. Next Steps

1. [ ] `/pdca design verilog-tb-reviewer`
2. [ ] `agents/verilog-tb-reviewer.md` 작성
3. [ ] `agents/verilog-tb-coder.md` self-check 절 갱신(이미 plan 갱신 완료, agent 파일은 Design/Do 단계에서 함께 반영)
4. [ ] `install.py` 등록
5. [ ] xcelium-mcp v1.36와 최종 대조(v1.35 "기록=출력" 절차 포함)

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-10 | 초안 — xcelium-mcp v1.34에서 확정된 `verilog-tb-reviewer` 요구사항을 이 repo로 가져와 Plan 문서화. `verilog-rtl-reviewer.md`의 "STATIC vs SIM 정직성 계약"·"architect-advisor 역할 분담" 골격을 재사용하되 taxonomy(T1-T9)는 이식하지 않고 TB 자체 검토 항목(§4)으로 대체 | HSLEE |
| 0.2 | 2026-07-21 | 사용자 지적("testbench도 architecturing을 잘 해야 확장성·재사용성이 높아진다")을 계기로 신설된 `verilog-tb-architect-advisor`(`verilog-tb-architect-advisor.plan.md`)의 route 대상으로 §2.1/FR-08/§4.4를 갱신 — "TB-ARCH-SUSPECT를 사람에게 직접 refer"를 "이 agent로 route"로 변경. §2.2 Out of Scope의 "TB용 classifier 신설 YAGNI" 문구도 신설 agent가 자동 classifier 없이 동작한다는 사실과 정합하도록 수정 | HSLEE |
| 0.3 | 2026-07-22 | 사용자 지시("verilog agents들이 모두 일관성을 가지도록... 현재 reviewer가 다른 agents들의 설계철학과 다른 부분을 같은 설계철학으로 수정")를 반영해 전체 verilog agent 패밀리(rtl-analyst/coder/reviewer/prover/debugger/architect-advisor + tb-analyst/coder/architect-advisor) 대비 종합 정합성 감사 수행. **변경**: (1) FR-04 — `agents/verilog-rtl-reviewer.md`를 실제 Read해 named parameter 표가 없음을 확인, formal 스키마(`fix_plan_path`/`env`/`files_changed`/`implementer`) 철회하고 자유 형식 프롬프트로 정정. (2) FR-01 — TB 패밀리 표준인 "Use it when/Do NOT use for/Triggers" 3-part frontmatter 구조 명시(rtl-reviewer엔 없지만 TB 내부 일관성 우선). (3) FR-02 — **`model: opus` 누락 발견 및 추가**(전체 분석/리뷰 계열 agent와 동일 기준, 실제 결함이었음). (4) §5.1 DoD — "왜 model: opus" 헤더 + "정직한 한계" 섹션(TB 패밀리 표준, rtl-reviewer엔 없지만 사용자가 명시적으로 TB 내부 일관성을 우선하라고 지시) 포함 요구 추가. (5) FR-12/§7.1 — install.py 등록 문구를 실제 glob 메커니즘에 맞게 정정(tb-coder 0.6/tb-architect-advisor 0.2와 동일). **검증 후 유지(변경 안 함)**: FR-10/FR-11의 `-tb-` 파일명 infix와 `clean`/`issues_found` 2-way verdict는 `xcelium-mcp-debug-workflow-v2.plan.md` L637-639/L918을 직접 대조해 실제 cross-repo 계약(`fix_review.status` 스키마)임을 확인 — 임의 편차가 아니므로 RTL의 3-way(`BLOCK`/`CONDITIONAL`/`PASS`)로 통일하지 않음. **독립 fresh-context agent 검토(worktree isolation) 결과 5개 수정 전부 확인(confirmed correct), 과잉수정 없음 확인 후 3개 추가 gap 발견 및 반영**: (6) cross-repo 버전 pin이 v1.34로 정체돼 있던 것을 실제 최신 v1.36으로 갱신 + v1.35 "기록=출력"(사람 구현자 findings 전달) 절차 반영 필요성을 §정합성 유지/§5.1/§7.2/§8에 명시. (7) FR-03/§2.1 "0. 기준"에 `chip-verification/references/non-uvm-architectures.md` 누락 발견 — `verilog-tb-coder`/`verilog-tb-architect-advisor`와 동일 근거(legacy/non-UVM TB 컨벤션 확인 역할)로 추가. (8) §1.2가 "STATIC vs SIM 정직성 계약 재사용"을 선언만 하고 실제 절차에 반영 안 했던 것을 발견 — §4.1a 신설(`[TB-STATIC]`/`[TB-NEEDS-SIM-VERIFY]` finding별 라벨, overall verdict는 xcelium-mcp 계약대로 2-way 유지) + FR-05/§4.7 갱신 | HSLEE |
| 0.4 | 2026-07-22 | 사용자 지적("agents는 특정 flow에 종속되면 안 돼. 일반적으로 사용할 수 있어야 해")을 반영 — 0.3까지의 "family 일관성" 감사는 frontmatter/model/섹션 구조 같은 **스타일** 일관성만 다뤘고, §1.1 Purpose·§2.1 Scope·§4 검토 절차 자체는 여전히 "fix-plan.md가 항상 존재한다"고 가정하는 **workflow-v2 종속** 설계로 남아 있었다 — `verilog-tb-coder.plan.md`가 0.3→0.4에서 이미 겪고 철회한 것과 정확히 같은 종류의 실수. `verilog-tb-coder`가 확립한 패턴(호출 근거가 fix-plan.md든 사람의 직접 요청이든 agent 입장에서 구분하지 않는 단일 균일 절차)을 그대로 재적용: 상단 Summary/Executive Summary/Context Anchor(WHO/SUCCESS)를 general-purpose 우선으로 재작성, §1.1 Purpose를 "호출 시 제시된 근거"로 일반화, §1.2에 "workflow-v2 전용 아님" 경고 신설, §2.1/FR-05/FR-07/§4.1/§4.3을 "fix-plan 범위"에서 "선언된 범위(출처 무관)"로 일반화, FR-01 Triggers에 일반 리뷰 요청 키워드 추가, FR-10/§2.1 보고서 경로를 `{test}`→`{target}`으로 일반화(testcase 아닌 대상도 커버), §7.2에 일반 요청 consumer 행 신설(`verilog-tb-coder` §7.2와 대칭), §5.1 DoD·§3.2 NFR에 "두 호출 경로 동일 결과" 검증 항목 추가 | HSLEE |
