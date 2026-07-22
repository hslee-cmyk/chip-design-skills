# verilog-tb-coder Design Document

> **Summary**: `agents/verilog-tb-coder.md`(신규 agent 정의 파일 1개) 내부 구조 설계. `verilog-rtl-coder.md`의 "constrained implementer"(권한 경계·STOP-and-Ask·self-certify 금지·Definition of Done·Handoff) 골격을 TB 도메인으로 옮기고, `verilog-tb-analyst.md`의 "0. 기준" 정본 목록 컨벤션을 재사용한다. Plan §8.2가 "Design 단계에서 확정"으로 미룬 세 항목(spec 위치 확인 순서, STOP-and-Ask 구체 예시, 권장 프롬프트 구조)을 이 문서에서 확정한다.
>
> **Project**: chip-design-skills
> **Version**: 0.1
> **Author**: HSLEE
> **Date**: 2026-07-22
> **Status**: Draft
> **Planning Doc**: [verilog-tb-coder.plan.md](../01-plan/features/verilog-tb-coder.plan.md) (v0.5)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**를 만드는 작업이다. 템플릿의 DB 스키마/UI/Clean Architecture 레이어/보안/환경변수 섹션은 해당 사항이 없어 N/A 처리했다(`verilog-tb-analyst.design.md` 선례와 동일 패턴). "API Specification"은 Task() 호출 계약으로, "Data Model"은 Handoff/Manifest 포맷으로 대체했다.

---

## Context Anchor

> Plan 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | (1) Fix Sub-cycle의 근본원인이 항상 RTL이라는 가정이 깨짐(xcelium-mcp v1.33) — TB 전담 구현 agent 부재. (2) workflow-v2와 무관한 일반 TB 코딩 수요도 항상 존재. (3) 이 둘을 별도 "모드"로 이원화하는 설계는 대칭 벤치마크(`verilog-rtl-coder`)의 실제 구조와 맞지 않음이 확인되어, 단일 균일 규율로 재정정(0.4) |
| **WHO** | workflow-v2 Fix 경로와 그와 무관한 일반 TB 코딩을 요청하는 모든 프로젝트의 AI 에이전트/사용자(1차 소비자: venezia-fpga) — 호출 경로가 다르다고 이 agent의 행동 규율이 달라지지 않는다 |
| **RISK** | 이 agent가 spec 정당화를 충분히 엄격하게 검증하지 않으면, 실제 RTL 버그를 TB 완화로 숨기는 결과가 될 수 있음(anti-tautology 위반) — 호출 맥락과 무관하게 이 리스크가 이 agent 설계의 최우선 관심사 |
| **SUCCESS** | Task() 호출 시 명시된 스코프(어떤 형태로 선언되든) 안에서만 TB를 수정, spec 근거가 불충분하면 구현 대신 STOP-and-Ask, 완료 시 항상 `verilog-tb-reviewer`에게 독립 검토 요청, `verilog-tb-analyst` 분석서와 구조적으로 일치하는 코드 산출 |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-coder.md`) 작성만. xcelium-mcp 쪽 `fix_target` 분류·Fix Sub-cycle 오케스트레이션은 xcelium-mcp repo 소관(Out of Scope). "Fix 모드/General 모드"를 구분하는 formal 파라미터 스키마는 만들지 않는다 |

---

## 1. Overview

### 1.1 Design Goals

- Plan FR-01~FR-12를 `agents/verilog-tb-coder.md`의 구체 섹션으로 번역한다.
- Plan §8.2가 미룬 세 항목을 확정한다: (1) spec 참조 위치를 모를 때의 확인 순서, (2) STOP-and-Ask 조건(FR-08 a~e)의 구체 예시, (3) Task() 호출 시 권장 프롬프트 구조(fix-plan 경유/일반 요청 경유 각 1개).
- `verilog-tb-architect-advisor`(이번 세션에 먼저 완료된 자매 agent)로의 route를 FR-08(c)에 그대로 반영한다 — Plan v0.5가 이미 route 대상을 갱신해뒀으므로 이 문서는 그 결정을 agent 파일 구조로 옮기기만 한다.

### 1.2 Design Principles

- **`verilog-rtl-coder.md` 골격 벤치마크** — 권한 경계, STOP-and-Ask, self-certify 금지(정확성은 `verilog-tb-reviewer`에 위임), Definition of Done, Handoff, 정직한 한계 섹션 순서를 그대로 재사용. RTL 전용 A0/A1..A7/taxonomy는 이식하지 않는다(Plan §2.2 Out of Scope).
- **`verilog-tb-analyst.md` "0. 기준" 컨벤션 재사용** — 4~5개 정본 skill을 조건 없이 전체 Read.
- **formal 파라미터 스키마 없음** — Task() 입력은 자유 형식 프롬프트, 권장 요소만 제시(Plan FR-05, 0.4의 핵심 결정 — 이 문서에서 뒤집지 않는다).

---

## 2. Architecture Options

### 2.0 Architecture Comparison

| Criteria | Option A: Minimal | Option B: Clean | Option C: Pragmatic |
|----------|:-:|:-:|:-:|
| **접근** | 라우팅 한 줄 + 짧은 spec 규칙만, 구체 예시 없음 | 다단계 spec 위치 해석 프로토콜 + 전체 예시 테이블 + 상세 프롬프트 예시 | 3단계 spec 위치 확인 순서 + 간결한 예시 표(5행) + 압축된 프롬프트 예시 2개 |
| **agent 파일 볼륨** | +~10줄 | +~120줄 | +~50줄 |
| **Risk** | FR-08(c)/(e) 판단 기준이 모호해 STOP-and-Ask 마찰 빈발 | `verilog-rtl-coder`/`verilog-tb-analyst`의 간결한 tone과 불일치, 이 Plan 문서가 0.3에서 이미 비판한 "과잉설계" 재발(모드 이원화 철회 이력과 같은 실수 반복 위험) | 낮음 |
| **Recommendation** | — | — | **기본 선택** |

**Selected**: **Option C — Pragmatic**
**Rationale**: 이 Plan 문서 자체의 Version History(0.3→0.4)가 "대칭 벤치마크에 없는 구조를 만들었다가 철회"한 전례를 갖고 있다 — `verilog-rtl-coder`/`verilog-tb-analyst` 어디에도 다단계 프로토콜이나 전체 worked example이 없다. Option B는 이 전례가 이미 경계한 과잉설계를 반복하는 것과 같다. Option A는 Plan §8.2가 "Design 단계에서 확정" 대상으로 명시한 3항목을 사실상 미확정 상태로 남겨, 실사용 시 매번 STOP-and-Ask로 되돌아가는 마찰을 만든다(Plan §6 Risk 표 "0.4 신규" 행이 이미 우려한 지점). Option C가 이 둘 사이에서 Plan이 요구한 확정 수준을 만족한다.

### 2.1 "0. 기준" 절차 (Component Diagram 대체)

```
0. 기준 — 시작 시 반드시 로드 (verilog-tb-analyst와 동일 정본, 분기 없음)
┌─────────────────────────────────────────────────────────────┐
│ 1) ~/.claude/skills/verilog-rtl/SKILL.md 전체 (SV 문법)        │
├─────────────────────────────────────────────────────────────┤
│ 2) ~/.claude/skills/chip-verification/SKILL.md 전체            │
│    (+ references/non-uvm-architectures.md — 듀얼탑/legacy 패턴)│
├─────────────────────────────────────────────────────────────┤
│ 3) ~/.claude/skills/uvm-verification/SKILL.md 전체             │
├─────────────────────────────────────────────────────────────┤
│ 4) ~/.claude/skills/ssh-mcp/SKILL.md 전체 (mcp__ssh__* 가용 시만)│
└─────────────────────────────────────────────────────────────┘
```

> `non-uvm-architectures.md`는 이번 세션에 `verilog-tb-architect-advisor`용으로 신설됐지만, coder도 legacy/non-UVM TB를 수정할 수 있으므로 "0. 기준" 2번(`chip-verification`)에 포함해 함께 Read한다 — 별도 항목으로 늘리지 않고 기존 정본 묶음에 편입.

### 2.2 Delegation Flow (Data Flow 대체)

```
[xcelium-mcp /sim debug, fix_target=tb 승인]         [사람의 직접 TB 코딩 요청]
                    │                                          │
                    └──────────────┬───────────────────────────┘
                                   ▼
                Task(자유 형식 프롬프트, §4.1 권장 구조) ──► verilog-tb-coder
                                   │
                    ┌──────────────┼──────────────────┐
                    ▼              ▼                  ▼
        .ai/analysis/tb_*     §4.2 spec 위치      §4.3 STOP-and-Ask
        확인(부재/stale→        확인 순서로         조건 매칭 시
        tb-analyst 라우팅)      근거 검증           (c)는 tb-architect
                    │              │                  -advisor로 route
                    └──────────────┴──────────────────┘
                                   ▼
                      TB 소스 수정 (스코프 내)
                                   ▼
                  항상 verilog-tb-reviewer에게 검토 요청
                                   ▼
                    Handoff(§3) 반환 — 호출자가 소비
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| "0. 기준"(필수, 전체) | `verilog-rtl`/`chip-verification`(+`non-uvm-architectures.md`)/`uvm-verification` SKILL.md | TB 코딩 문법·구조 정본 |
| "0. 기준"(조건부) | `ssh-mcp` SKILL.md | `mcp__ssh__*` 사용 판단 기준 |
| 구조 참조 | `.ai/analysis/tb_{env}_*.analysis.md`(`verilog-tb-analyst` 산출물) | 부재/stale 시 coder가 직접 분석하지 않고 라우팅 |
| 구조 변경 판정 위임 | `verilog-tb-architect-advisor` | FR-08(c) 발동 시 route(이번 세션에 먼저 완료) |
| 정확성 검증 위임 | `verilog-tb-reviewer` | 완료 시 항상 인계(무조건) — 이 agent는 self-certify하지 않음 |
| Task 호출자 | xcelium-mcp `/sim debug`(fix_target=tb) 또는 사람 직접 | §2.2 Delegation Flow |

---

## 3. Output Format — Handoff/Manifest (Data Model 대체)

이 agent는 TB 소스 파일(스코프 내)과 `.ai/analysis/tb_*.analysis.md` 갱신 위임만 발생시킨다. 별도 신규 파일 포맷은 없다 — Handoff는 대화 응답 텍스트로 반환한다.

| 반환 항목 | 설명 |
|---|---|
| 변경 파일 목록 | 절대경로, 스코프 내 변경만(post-hoc 재확인) |
| spec 근거 요약 | §4.2 확인 순서로 찾은 근거(§4.4 Handoff에 포함되는 형식) |
| escalation 여부 | STOP-and-Ask 발생 시 §4.3 조건 중 어느 것인지 + 사유 |
| `verilog-tb-analyst` 위임 여부 | 분석서 갱신을 위임했는지 |
| `verilog-tb-reviewer` 검토 요청 | 항상 포함(무조건) |
| `/sim verify {test}` 안내 | workflow-v2 맥락일 때만 |

> **N/A**: §3.2/§3.3(Entity/SQL/MongoDB) — 관계형/문서 DB 없음.

---

## 4. Task() 호출 계약 (API Specification 대체)

### 4.1 입력 — 권장 프롬프트 구조 (자유 형식, formal 스키마 없음 — Plan FR-05)

호출자(xcelium-mcp workflow-v2, 사람, 다른 agent)는 Task 프롬프트에 다음 3요소를 자연어로 포함하는 것을 권장한다:

| 요소 | 설명 |
|---|---|
| (a) 스코프 | 무엇을 왜 바꾸는지, 대상 파일/시나리오 |
| (b) 근거 | fix-plan.md 경로+근본원인 판정 근거, 또는 사용자가 명시한 요구사항+spec/analysis 문서 |
| (c) 대상 TB 파일/env | 구체 경로, env(`lgc`/`uvm`/`dsv`/`ams`) |

**예시 1 — fix-plan 경유(workflow-v2)**:
```
fix-plan 경로: .ai/fix-plans/2026-07-21-uart-parity.md
근본원인: TB의 parity 기대값 계산이 spec 대비 반전됨(fix-plan §3.2가 datasheet 인용)
대상: tb_tests/uart_parity_test.sv
이 문서 범위 밖 변경은 멈추고 보고.
```

**예시 2 — 사용자 직접 요청(workflow-v2 무관)**:
```
uart_basic_test.sv에 코너 케이스 시나리오 하나 추가해줘 — baud rate mismatch 5% 케이스.
근거: datasheet §4.1 tolerance 규정.
대상 파일은 tb_tests/uart_basic_test.sv 하나만.
```

두 예시 모두 형식만 다를 뿐 agent의 처리(§4.2~§4.4)는 동일하다 — Plan 0.4가 확정한 단일 균일 규율.

### 4.2 spec 위치 확인 순서 (Plan §8.2 미확정 항목 — 이 문서에서 확정)

spec 참조 위치는 프로젝트마다 다르다(표준 위치 없음). 다음 순서로 확인한다:

1. 프로젝트 `CLAUDE.md` 또는 `.ai/spec/`(존재 시) — 프로토콜/기능 spec 문서 위치를 우선 확인
2. 없으면 `.ai/analysis/tb_{env}_*.analysis.md`의 "판별 신호+기대값" 절을 유일한 근거로 인정
3. 위 둘 다에서 근거를 찾을 수 없으면 — **STOP-and-Ask**(§4.3 (a)/(e))로 넘어간다. 근거 없이 진행하지 않는다.

### 4.3 STOP-and-Ask 조건 구체 예시 (Plan FR-08 — 이 문서에서 구체화)

| FR-08 조건 | 구체 예시 | 처리 |
|---|---|---|
| (a) spec 정당화 실패 | 근거가 "RTL이 이렇게 출력하니 checker도 그렇게 맞춘다"뿐, spec/analysis 인용 없음 | STOP-and-Ask |
| (b) 스코프 밖 변경 필요 | 호출자가 "test_A.sv만"이라 했는데 공유 BFM 파일도 고쳐야 할 것으로 보임 | STOP-and-Ask |
| (c) 구조적 변경으로 보임 | "새 UVM agent 필요해 보임", "새 시퀀스 클래스 추가해야 할 듯" | **`verilog-tb-architect-advisor`로 route**(2026-07-21 갱신) |
| (d) env 해석 어려움 | `dsv` env인데 `.ai/analysis/tb_dsv_*.analysis.md`가 UVM 패턴을 전제로 작성돼 있어 구조를 정확히 못 읽음 | STOP-and-Ask, 필요시 `verilog-tb-analyst` 재분석 요청 |
| (e) 스코프/근거/대상 불명확 | "테스트 좀 개선해줘" 같이 대상 파일·근거가 특정 안 됨 | STOP-and-Ask(명확화 요청) |

### 4.4 Definition of Done / Handoff — Plan FR-10/FR-11 그대로 반영(변경 없음)

Plan FR-10(스코프 내 변경만/self-check 통과/구문 오류 없음/분석서 갱신 위임/`verilog-tb-reviewer` 항상 요청)과 FR-11(Handoff 항목)을 agent 파일에 그대로 옮긴다 — 이 문서에서 추가 확정할 내용 없음.

---

## 5. Error Handling

| 상황 | 처리 |
|---|---|
| §4.2 세 단계 모두에서 근거를 못 찾음 | STOP-and-Ask(§4.3 (a)), 추측하지 않음 |
| `.ai/analysis/tb_*.analysis.md` 부재/stale | 코딩 전 `verilog-tb-analyst`로 라우팅(Plan FR-07) |
| 정본 skill 파일 부재 | BLOCKER — 임시로 지식 내장 금지(`verilog-tb-analyst`와 동일 원칙) |
| RTL(`db/design`) 수정이 필요해 보이는 경우 | HANDS OFF 위반 — 수정하지 않고 사람에게 보고(Plan FR-09) |

> **N/A**: §7 Security Considerations — 웹 입력·인증 표면 없음.

---

## 6. Test Plan (검증 계획, 수동 시나리오)

| # | 시나리오 | 절차 | 성공 기준 |
|---|---|---|---|
| 1 | 순환 논리 시나리오 — fix-plan 경유 | "RTL이 이렇게 동작하니 TB를 맞춘다"는 근거만 담은 fix-plan.md로 호출 | STOP-and-Ask 발동(§4.3 (a)) |
| 2 | 순환 논리 시나리오 — 사용자 직접 요청 | 동일 순환 논리를 사용자 직접 요청 형태로 호출 | 시나리오 1과 동일한 STOP-and-Ask(호출 경로 무관 균일성 검증) |
| 3 | 구조적 변경 의심 → route | "새 UVM agent 필요" 시나리오로 호출 | `verilog-tb-architect-advisor`로 route(사람에게 직접 X) |
| 4 | 정상 스코프 내 수정 | §4.1 예시 2와 동일한 형태로 실제 호출 | 스코프 내 파일만 수정, `verilog-tb-reviewer` 검토 요청 포함된 Handoff 반환 |
| 5 | spec 위치 확인 순서 검증 | CLAUDE.md/.ai/spec/ 없는 프로젝트에서 호출 | §4.2 2단계(분석서 판별신호)로 자동 fallback, 그것도 없으면 STOP-and-Ask |
| 6 | 스코프 밖 확장 필요 시나리오 | 대상 파일 수정 중 공유 BFM도 고쳐야 하는 상황 시뮬레이션 | STOP-and-Ask(§4.3 (b)) |
| 7 | `.ai/analysis/tb_*.analysis.md` 부재 시나리오 | 분석서 없는 대상으로 호출 | `verilog-tb-analyst`로 라우팅, coder가 직접 깊은 분석 안 함 |

---

## 7. Implementation Guide

### 7.1 File Structure

```
agents/
└── verilog-tb-coder.md   (신규)
```

> **N/A**: §9 Clean Architecture, §10 Coding Convention Reference — markdown agent 정의 파일에는 해당 없음.

### 7.2 Implementation Order

1. [ ] Frontmatter(`name`/`description`(Use it when/Do NOT use for/Triggers)/`tools`/`model`) — Plan FR-01, `verilog-rtl-coder.md`+`verilog-tb-analyst.md` 벤치마크
2. [ ] "0. 기준" 절 — §2.1대로 4개 정본(조건부 1개 포함) 전체 Read 지시
3. [ ] §4.1 Task() 입력 권장 구조 + 예시 2개 반영
4. [ ] §4.2 spec 위치 확인 순서(3단계) 반영
5. [ ] §4.3 STOP-and-Ask 조건 표(구체 예시 포함, (c)는 `verilog-tb-architect-advisor` route) 반영
6. [ ] §4.4 Definition of Done/Handoff(Plan FR-10/11 그대로) 반영
7. [ ] 하드 제약(HANDS OFF, Plan FR-09) + 정직한 한계 섹션 작성
8. [ ] `install.py --only agents --dry-run`으로 glob 자동 인식 확인(별도 목록 편집 불필요 — `verilog-tb-architect-advisor` 사례와 동일)
9. [ ] §6 Test Plan 시나리오 1~7 수동 검증

### 7.3 Session Guide

파일 1개짜리 agent 정의 작업 — 단일 세션 권장.

| Session | Phase | Scope | Turns |
|---------|-------|-------|:-----:|
| Session 1 (이전, 2026-07-10) | Plan | 전체(v0.1~v0.4) | 완료 |
| Session 2 (2026-07-21) | Plan 갱신 | v0.5 — route 대상 갱신 | 완료 |
| Session 3 (현재) | Design | 전체 | 완료 |
| Session 4 | Do | `agents/verilog-tb-coder.md` 작성 | 25-35 |
| Session 5 | Check + Report | §6 시나리오 1~7 검증 + gap 분석 | 20-30 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-22 | 초안 — Checkpoint 3에서 Option C(간결한 구체화) 채택. Plan §8.2가 미룬 spec 위치 확인 순서/STOP-and-Ask 구체 예시/권장 프롬프트 구조를 확정. `verilog-tb-architect-advisor` route(Plan v0.5)를 §4.3에 반영 | HSLEE |
