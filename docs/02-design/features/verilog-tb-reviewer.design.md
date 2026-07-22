# verilog-tb-reviewer Design Document

> **Summary**: `agents/verilog-tb-reviewer.md`(신규 agent 정의 파일 1개) 내부 구조 설계. `verilog-rtl-reviewer.md`와 **최상위 섹션 순서·이름을 동일하게** 맞추되(핵심설계 → 역할경계 → 검토항목 → 출력 → 하드제약 → 정직한한계), 내용은 Plan v0.4가 이미 확정한 TB 스케일 검토 항목(§4.1-4.7)을 그대로 담는다 — RTL의 STATIC/SIM 카탈로그·다단계 스텝(R/G/A/B/C/D)은 이식하지 않는다(TB엔 대응하는 taxonomy가 없음, YAGNI). 호출 맥락(xcelium-mcp Fix Sub-cycle vs 사람의 직접 리뷰 요청)과 무관하게 동일한 절차로 동작하도록 Plan v0.4의 일반화 결정을 그대로 반영한다.
>
> **Project**: chip-design-skills
> **Version**: 0.2
> **Author**: HSLEE
> **Date**: 2026-07-22
> **Status**: Draft
> **Planning Doc**: [verilog-tb-reviewer.plan.md](../01-plan/features/verilog-tb-reviewer.plan.md) (v0.4)

> 이 feature는 markdown agent 정의 파일 1개다. 템플릿의 DB 스키마/UI/Clean Architecture 레이어/보안/환경변수 섹션은 N/A(`verilog-tb-coder.design.md` 선례와 동일 패턴). "API Specification"은 Task() 호출 계약으로, "Data Model"은 리뷰 보고서/Manifest 포맷으로 대체했다.

---

## Context Anchor

> Plan v0.4에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | `verilog-tb-coder`의 self-check만으로는 anti-tautology를 구조적으로 보장할 수 없음(자기 인증의 모순). 동시에 이 agent 자체가 특정 워크플로우(xcelium-mcp)에 종속되지 않고 일반적으로 재사용 가능해야 함 |
| **WHO** | xcelium-mcp `/sim` 워크플로우를 사용하는 AI 에이전트, 그리고 이와 무관하게 TB 코드 변경을 독립적으로 검토받고 싶은 모든 프로젝트의 사람/AI 에이전트(일반 리뷰 요청) — 호출 경로가 다르다고 검토 규율이 달라지지 않음 |
| **RISK** | 이 agent 자신도 spec 참조 없이 "코드가 그럴듯해 보인다"로 안이하게 clean 판정을 내리면 방어선으로서 무력화됨 |
| **SUCCESS** | fix-plan.md 경유든 사람의 직접 리뷰 요청이든 동일한 시나리오에서 동일한 결과가 나옴(호출 맥락 무관 균일성), 순환 논리를 실제로 잡아냄 |
| **SCOPE** | agent 정의 파일(`agents/verilog-tb-reviewer.md`) 작성만(install.py는 glob 자동 인식) |

---

## 1. Overview

### 1.1 Design Goals

- Plan의 FR-01~FR-12와 §4.1-4.7 검토 항목을 `agents/verilog-tb-reviewer.md`의 구체 섹션으로 번역한다.
- `verilog-rtl-reviewer.md`와 **최상위 정보 구조**(무엇을 어떤 순서로 다루는지)를 동일하게 맞춰, 두 agent가 "대칭"이라는 관계가 실제 파일 구조에서도 드러나게 한다 — 단 RTL 전용 세부(taxonomy 카탈로그, 다단계 절차)는 이식하지 않는다.
- Plan v0.4가 확정한 "워크플로우 비종속" 원칙(fix-plan.md 경유/사람 직접 요청 경유가 동일 절차)을 agent 파일의 모든 섹션에서 일관되게 반영한다.

### 1.2 Design Principles

- **STATIC vs SIM 정직성 계약 재사용, 메커니즘화** — Plan §4.1a의 `[TB-STATIC]`/`[TB-NEEDS-SIM-VERIFY]` finding 라벨을 실제 절차로 구현.
- **architect-advisor와의 역할 분담 재사용** — 구조적 변경 의심은 판정하지 않고 `verilog-tb-architect-advisor`로 route(Plan FR-08).
- **self-certify 금지 무조건 재확인** — `verilog-tb-coder`의 self-check 결과와 무관하게 항상 처음부터 재검토(Plan FR-05).
- **호출 맥락 무관 단일 절차** — fix-plan.md 유무와 관계없이 §4의 절차는 동일(Plan 0.4 핵심 결정, 되돌리지 않음).

---

## 2. Architecture Options

### 2.0 Architecture Comparison

| Criteria | Option A: Minimal | Option B: Clean | Option C: Pragmatic |
|----------|:-:|:-:|:-:|
| **접근** | `verilog-tb-coder` 스타일 평평한 번호 섹션, §4.1-4.7 인라인 | `verilog-rtl-reviewer` 구조 완전 이식(STATIC/SIM 카탈로그, 스텝 0/R/G/A/B/C/D) | 최상위 섹션 순서/이름은 rtl-reviewer와 동일, 내용은 Plan §4.1-4.7 그대로 |
| **RTL reviewer와의 구조적 대칭성** | 낮음(파일 구조에서 안 드러남) | 높음(그러나 내용 없는 카탈로그를 억지로 채움) | 높음(구조만 맞추고 내용은 TB 스케일 유지) |
| **Risk** | 대칭 agent 관계가 파일에서 안 보임 | TB엔 없는 taxonomy를 억지로 채워야 해 과잉설계 | 낮음 |
| **Recommendation** | — | — | **기본 선택** |

**Selected**: **Option C**
**Rationale**: Checkpoint 3에서 사용자가 직접 선택. RTL reviewer와 "대칭 agent"라는 관계(Plan §1.3)를 파일 구조 차원에서도 드러내되, Plan이 이미 여러 버전(0.1→0.3)에 걸쳐 명시적으로 경계해온 "TB에 없는 taxonomy를 억지로 채우는" 과잉설계를 반복하지 않는다.

### 2.1 최상위 섹션 구조 (Component Diagram 대체) — rtl-reviewer 대비 매핑

```
verilog-rtl-reviewer.md 구조              verilog-tb-reviewer.md 구조 (0.2 갱신 — 실제 Do 결과 반영)
─────────────────────────────────         ─────────────────────────────────
frontmatter                        ──►    frontmatter (Plan FR-01/FR-02)
"왜 model: opus" 헤더               ──►    "왜 model: opus" 헤더 (Plan §5.1 DoD)
(기준 문서는 프로즈 나열)            ──►    §0 "기준 — 시작 시 반드시 로드"(tb-analyst/tb-coder 패밀리
                                           컨벤션대로 **가장 먼저** 배치 — 판단 전에 정본부터 적재)
§0 핵심설계(STATIC vs SIM 계약)      ──►    §1 핵심설계(재사용 선언 + §2.1a 메커니즘 예고 +
                                           "SIM-RISK 3-way 라우팅 재사용 안 함" 한 줄 명시)
§0.1 역할경계(architect-advisor)    ──►    §1.1 역할경계(verilog-tb-architect-advisor)
§0.2 라우팅 원칙                    ──►    (§1에 "재사용 안 함"으로 한 줄만 명시, 별도 섹션 없음)
§1 STATIC 체크리스트                ──►    (해당 없음 — §2 "검토 항목"에 흡수, Plan §4.1-4.7)
§2 SIM-RISK 체크리스트              ──►    (해당 없음 — §2.1a 라벨로 대체, 별도 카탈로그 없음)
§3 필수 분석 스텝(0/R/G/A/B/C/D)    ──►    §2 검토 항목(Plan §4.1-4.7 그대로, 스텝 세분화 없음)
§4 Directed Test 카탈로그           ──►    (해당 없음 — TB에 formal 대응 단계 없음, Out of Scope)
§5 출력 — 리뷰 보고서               ──►    §3 출력 — 리뷰 보고서 (Plan FR-10/FR-11)
(§5에 verdict 포함)                 ──►    §4 Verdict(독립 섹션 — rtl-reviewer의 §5 verdict 부분과
                                           더 정확히 대응하도록 분리)
§6 하드 제약                        ──►    §5 하드 제약
(없음)                              ──►    §6 정직한 한계(TB family 표준, Plan §5.1 DoD)
Manifest                            ──►    Manifest
```

> **0.2 갱신 — Check 단계 gap-detector가 발견한 문서-구현 번호 drift 정리**: Do 단계에서 실제로는
> "0. 기준"을 §0으로 가장 먼저 배치(TB 패밀리 컨벤션 우선)하고 Verdict를 §3(출력)에서 분리해 독립된
> §4로 뒀다 — 둘 다 이 문서의 0.1 초안이 미리 정하지 못했던 지점이며, 구현 쪽 선택이 더 낫다고 판단해
> (전자는 패밀리 일관성, 후자는 rtl-reviewer와의 대응 정확도) 문서를 구현에 맞춰 갱신했다.

> 위 매핑에서 "해당 없음" 행은 Plan §2.2 Out of Scope가 이미 명시적으로 제외한 항목이다 — 억지로 빈 섹션을
> 만들지 않고, 그 사실 자체를 §0에 한 줄로 남겨 "왜 없는지"가 나중에도 추적 가능하게 한다.

### 2.2 Delegation/Consumer Flow (Data Flow 대체) — 두 호출 경로 대칭

```
[xcelium-mcp /sim debug, fix_target=tb 승인]      [사람/AI의 직접 TB 리뷰 요청]
                    │                                          │
                    └──────────────┬───────────────────────────┘
                                   ▼
                Task(자유 형식 프롬프트, §4.1 권장 구조) ──► verilog-tb-reviewer
                                   │
                    ┌──────────────┼──────────────────────┐
                    ▼              ▼                      ▼
        §4.1 spec 정당화    §4.2-4.3 checker/범위    §4.4 구조 변경 의심
        최종 판단(self-check  준수 확인                → verilog-tb-architect
        결과 무관 재확인)                                -advisor로 route
                    │              │                      │
                    └──────────────┴──────────────────────┘
                                   ▼
                    §4.1a로 finding별 [TB-STATIC]/
                    [TB-NEEDS-SIM-VERIFY] 라벨 부여
                                   ▼
              보고서(.ai/reviews/{target}-tb-{YYYYMMDD}.review.md)
              + verdict(clean/issues_found) + Manifest 반환
                                   │
                    ┌──────────────┴──────────────────────┐
                    ▼                                      ▼
       [workflow-v2 맥락] issues_found→          [일반 요청 맥락] findings를
       fix-implement로 되돌림(xcelium-mcp        그대로 호출자에게 보고
       Skill 소관, agent 밖)                      (agent의 역할은 여기서 끝)
```

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| "0. 기준"(필수, 전체) | `verilog-rtl`/`chip-verification`(+`non-uvm-architectures.md`)/`uvm-verification` SKILL.md | TB 컨벤션 준수 확인(§4.5) 정본 |
| "0. 기준"(조건부) | `ssh-mcp` SKILL.md | `mcp__ssh__*` 사용 판단 기준 |
| 구조 참조 | `.ai/analysis/tb_{env}_*.analysis.md` | spec 정당화 판단(§4.1) 근거, stale 시 `verilog-tb-analyst` 라우팅 권고(§4.6) |
| 구조 변경 판정 위임 | `verilog-tb-architect-advisor` | §4.4 TB-ARCH-SUSPECT 발견 시 route |
| 대칭 벤치마크 | `agents/verilog-rtl-reviewer.md` | 최상위 구조·톤 벤치마크(§2.1) |
| Task 호출자 | xcelium-mcp `/sim debug`(fix_target=tb) **또는** 사람/AI의 직접 리뷰 요청 | §2.2, 둘 다 동등 |

---

## 3. Output Format — 리뷰 보고서 + Manifest (Data Model 대체)

이 agent는 read-only다. 유일한 Write 대상은 리뷰 보고서.

| 산출물 | 경로 패턴 | 필수 항목 |
|---|---|---|
| 리뷰 보고서 | `.ai/reviews/{target}-tb-{YYYYMMDD}.review.md`(Plan FR-10, `{target}`은 testcase명 또는 공유 컴포넌트명) | Summary / §4.1 spec 정당화 판정(+`[TB-STATIC]`/`[TB-NEEDS-SIM-VERIFY]` 라벨) / §4.2 checker 완화 findings / §4.3 범위 준수 / §4.4 TB-ARCH-SUSPECT / §4.5 컨벤션 / §4.6 분석서 상태 / §4.7 Verdict |

Manifest(Plan FR-11): 보고서 경로, verdict(`clean`/`issues_found`), findings 개수(+라벨별 분해), TB-ARCH-SUSPECT 여부, 분석서 상태(+ tb-analyst 라우팅 여부).

> **N/A**: §3.2/§3.3(Entity/SQL/MongoDB) — 관계형/문서 DB 없음.

---

## 4. Task() 호출 계약 (API Specification 대체)

### 4.1 입력 — 권장 프롬프트 구조 (자유 형식, Plan FR-04)

| 요소 | 설명 | 비고 |
|---|---|---|
| (a) 리뷰 대상 | diff·변경 파일 목록·env | 필수 |
| (b) 근거 | fix-plan.md 경로 **또는** 사람이 직접 진술한 근거 | 형태 무관, 있어야 §4.1 수행 가능 |
| (c) 구현 주체(참고용) | `verilog-tb-coder`/사람 | 검토 엄격도에 영향 없음 |

**예시 1 — fix-plan 경유**: `fix-plan 경로: .ai/fix-plans/2026-07-21-uart-parity.md, env=lgc, 대상: tb_tests/uart_parity_test.sv, 구현 주체: verilog-tb-coder`
**예시 2 — 일반 요청 경유(0.4 신규)**: `이 UART BFM 변경 검토해줘 — 근거: datasheet §4.1 tolerance 규정 반영. 대상: tb_lib/uart_bfm.sv`

### 4.2 검토 항목 — Plan §4.1-4.7 매핑 (변경 없이 그대로 구현)

Design 단계에서 추가 확정할 내용 없음 — Plan §4.1(spec 정당화)/§4.2(checker 완화)/§4.3(범위 준수)/§4.4(TB-ARCH-SUSPECT)/§4.5(컨벤션)/§4.6(분석서 정합성)/§4.7(Verdict)를 agent 파일 §2로 그대로 옮긴다.

### 4.3 verdict 2-way 유지 근거 (재확인, 변경 없음)

Plan FR-11이 검증한 대로 `clean`/`issues_found`는 xcelium-mcp `fix_review.status`와 일치하는 **이 agent 자신의 고유 verdict**다 — RTL reviewer의 `BLOCK`/`CONDITIONAL`/`PASS` 3-way를 TB에 강제하지 않는다(사용자와의 논의로 재확인: TB는 SIM-RISK owner-routing 복잡도가 없어 2-way가 자기 스코프에 맞는 자연스러운 선택). xcelium-mcp의 번역 책임은 RTL 경로에서도 동일하게 존재하며(rtl-reviewer/rtl-prover 각각 자기 고유 verdict를 유지), 이 agent도 같은 패턴을 따른다.

### 4.4 STATIC/SIM 정직성 라벨 메커니즘 (Plan §4.1a 구현)

각 finding에 `[TB-STATIC]`(diff·근거 문서만으로 정적 확정) 또는 `[TB-NEEDS-SIM-VERIFY]`(정적으로는 의심되나 `/sim verify` 실행 결과로만 확정) 라벨을 부여한다. 이 라벨은 보고서에만 기록되고 Manifest의 aggregate verdict 계산(§4.7)에는 영향을 주지 않는다.

---

## 5. Error Handling

| 상황 | 처리 |
|---|---|
| (a)/(b)/(c) 중 리뷰 대상·근거가 특정 불가할 만큼 불명확 | BLOCKER로 명시(추측 금지) |
| 정본 skill 파일 부재 | BLOCKER — 임시로 지식 내장 금지 |
| `.ai/analysis/tb_*.analysis.md` 부재/stale | §4.6대로 `verilog-tb-analyst` 라우팅 권고를 보고서에 기록(리뷰 자체는 가능한 범위까지 진행) |
| TB-ARCH-SUSPECT 발견 | §4.4대로 `verilog-tb-architect-advisor`로 route, 보고서에 명시 |

> **N/A**: §7 Security Considerations — 웹 입력·인증 표면 없음.

---

## 6. Test Plan (검증 계획, 수동 시나리오)

| # | 시나리오 | 절차 | 성공 기준 |
|---|---|---|---|
| 1 | 순환 논리 — fix-plan 경유, self-check 통과하도록 교묘하게 작성 | fix-plan.md 경유로 호출 | `issues_found`, self-check 결과 무관 재확인 확인 |
| 2 | 순환 논리 — 사람 직접 요청 경유(0.4 신규) | 동일 시나리오를 fix-plan.md 없이 직접 요청으로 호출 | 시나리오 1과 동일한 `issues_found`(호출 맥락 무관 균일성 검증) |
| 3 | checker 완화 탐지 | expected value가 실제 RTL 출력값으로 치환된 diff | `[TB-STATIC]` 라벨 + `issues_found` |
| 4 | 범위 이탈 | 선언 범위 밖 파일 변경 | `issues_found`, 범위 이탈 finding 기록 |
| 5 | TB-ARCH-SUSPECT route | 새 UVM 컴포넌트 추가처럼 보이는 diff | `verilog-tb-architect-advisor`로 route, 판정하지 않음 |
| 6 | STATIC/SIM 라벨 구분 | checker 완화 의심이나 실제 영향은 시뮬레이션 필요한 diff | `[TB-NEEDS-SIM-VERIFY]` 라벨 부여, verdict는 여전히 `issues_found`(§4.7) |
| 7 | clean 판정 | 정당한 fix, 모든 항목 통과 | `clean`, 불필요하게 막지 않음 |
| 8 | 정본 부재 시나리오 | skill 파일 임시 삭제 후 호출 | BLOCKER로 명시적 중단 |

---

## 7. Implementation Guide

### 7.1 File Structure

```
agents/
└── verilog-tb-reviewer.md   (신규)
```

### 7.2 Implementation Order

1. [x] Frontmatter(Plan FR-01/FR-02: name/description 3-part/tools/model:opus) — `verilog-rtl-reviewer.md` 벤치마크
2. [x] "왜 model: opus" 헤더 (Plan §5.1 DoD)
3. [x] **(0.2 갱신 — 순서 변경)** §0 "기준 — 시작 시 반드시 로드" — 4~5개 정본 전체 Read 지시(non-uvm-architectures.md 포함), tb-analyst/tb-coder 패밀리 컨벤션대로 판단 절차보다 먼저 배치
4. [x] §1 핵심설계 — STATIC/SIM 정직성 계약 재사용 선언 + §2.1a 메커니즘 예고 + "SIM-RISK 라우팅 재사용 안 함" 한 줄 명시
5. [x] §1.1 역할경계 — `verilog-tb-architect-advisor`와의 분담(구조 판정 안 함, refer만)
6. [x] §2 검토 항목 — Plan §4.1(+4.1a)/4.2/4.3/4.4/4.5/4.6/4.7 그대로 반영, 호출 맥락 무관 문구 유지
7. [x] §3 출력 — 리뷰 보고서 형식 + Manifest
8. [x] **(0.2 갱신 — 독립 섹션화)** §4 Verdict — 2-way 유지 근거(xcelium-mcp 계약 vs RTL 3-way 미채택 이유) 명시적 서술 포함, §3에서 분리
9. [x] §5 하드 제약(read-only, `verilog-tb-architect-advisor`/`verilog-tb-coder`와의 권한 경계)
10. [x] §6 정직한 한계
11. [x] `install.py --only agents --dry-run`으로 glob 자동 인식 확인
12. [ ] §6(Test Plan) 시나리오 1~8 실전 호출 검증(특히 2번 — 호출 맥락 무관 균일성) — 정적 gap 분석 통과 후 남은 실사용 검증, QA/실사용 단계에서 수행

### 7.3 Session Guide

| Session | Phase | Scope | Turns |
|---------|-------|-------|:-----:|
| Session 1-2 (이전) | Plan | v0.1~v0.4(family 일관성 + workflow 비종속 감사 포함) | 완료 |
| Session 3 (현재) | Design | 전체 | 완료 |
| Session 4 | Do | `agents/verilog-tb-reviewer.md` 작성 | 30-40 |
| Session 5 | Check + Report | §6 시나리오 1~8 검증 + gap 분석 | 20-30 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-22 | 초안 — Checkpoint 3에서 Option C(RTL과 최상위 구조 동일, 내용은 TB 스케일) 채택. Plan v0.4의 워크플로우 비종속 결정과 §4.1a STATIC/SIM 라벨 메커니즘을 agent 파일 구조로 확정 | HSLEE |
| 0.2 | 2026-07-22 | Do 완료 후 gap-detector 검증(Match Rate 99%, Critical/Important 없음) 결과 반영 — "0. 기준" 배치 순서(핵심설계보다 먼저, TB 패밀리 컨벤션 우선)와 Verdict 섹션 독립화(§3에서 분리해 §4로, rtl-reviewer 대응 정확도 향상)를 실제 Do 산출물에 맞춰 §2.1 매핑표/§7.2 Implementation Order 갱신 | HSLEE |
