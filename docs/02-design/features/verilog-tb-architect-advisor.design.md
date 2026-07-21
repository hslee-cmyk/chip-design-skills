# verilog-tb-architect-advisor Design Document

> **Summary**: `agents/verilog-tb-architect-advisor.md`(신규 agent 정의 파일 1개) 내부 구조 설계. `verilog-rtl-architect-advisor`의 "책임분해 → evidence recall → 3안 ADR → adversarial cross-review" 골격을 TB/UVM 도메인으로 옮기되, 판단 축을 **구조 경계**(새 컴포넌트/시퀀스 클래스 vs 접기)와 **UVM 도입 적정성**(과잉/적정/과소 gearing) 둘로 분리해, 후자는 ADR 없이 권고 사항으로만 보고하도록 설계한다. `verilog-tb-coder`/`verilog-tb-reviewer`가 route할 때 쓰는 Task() 호출 계약(자유 형식 프롬프트 권장 구조)도 이 문서에서 확정한다.
>
> **Project**: chip-design-skills
> **Version**: 0.1
> **Author**: HSLEE
> **Date**: 2026-07-21
> **Status**: Draft
> **Planning Doc**: [verilog-tb-architect-advisor.plan.md](../01-plan/features/verilog-tb-architect-advisor.plan.md) (v0.1)

> 이 feature는 Next.js/BaaS 웹앱이 아니라 **markdown agent 정의 파일 1개**를 만드는 작업이다. 템플릿의 DB 스키마/UI/Clean Architecture 레이어/보안/환경변수 섹션은 해당 사항이 없어 N/A 처리했고(`verilog-tb-analyst.design.md`의 선례 그대로 따름), "API Specification"은 이 agent의 실제 인터페이스인 **Task() 호출 계약**으로, "Data Model"은 **산출물(ADR stub) 포맷**으로 대체했다.

---

## Context Anchor

> Plan 문서에서 그대로 복사.

| Key | Value |
|-----|-------|
| **WHY** | `verilog-tb-coder`/`verilog-tb-reviewer` 둘 다 구조적 변경 의심을 감지만 하고 판단 프레임워크 없이 사람에게 직접 넘기도록 설계됨(YAGNI로 미뤄둔 갭). RTL에는 이미 이 역할(`verilog-rtl-architect-advisor`)이 있어 비대칭 |
| **WHO** | `verilog-tb-coder`(구현 전 STOP-and-Ask 시 경유), `verilog-tb-reviewer`(`[TB-ARCH-SUSPECT]` 발견 시 경유), 그리고 이들을 거치지 않고 TB/UVM plan·design 문서를 직접 검토받고 싶은 사람 |
| **RISK** | TB 구조 판단은 RTL과 달리 자동 diff 분류기가 없어, 이 agent의 프로즈 기반 판단이 부정확하거나 일관성이 없으면 "그럴듯한 감"에 불과해질 위험 — RTL의 P-모드(구조 delta 선언 → baseline 대조)와 동일한 엄격함 필요 |
| **SUCCESS** | 새 컴포넌트/시퀀스 클래스 도입이 필요한 경우와 기존에 접어도 되는 경우를 재사용 범위 기준으로 정확히 구분, UVM 과잉/과소 적용 사례를 실제로 잡아냄, 3안 이상 ADR + adversarial cross-review 산출, `verilog-tb-coder`/`verilog-tb-reviewer` 양쪽에서 자연스럽게 route됨 |
| **SCOPE** | `agents/verilog-tb-architect-advisor.md` 신설 + `install.py` 등록 + `verilog-tb-coder.plan.md`/`verilog-tb-reviewer.plan.md`의 route 대상 갱신. TB 전용 자동 classifier 스크립트 신설은 Out of Scope |

---

## 1. Overview

### 1.1 Design Goals

- Plan의 FR-01~FR-12를 `agents/verilog-tb-architect-advisor.md`의 구체적 섹션 구조로 번역한다.
- Plan §8.2가 "Design 단계에서 확정"으로 미뤄둔 세 항목을 이 문서에서 확정한다: (1) 재사용범위 판단표의 구체 예시(UVM/non-UVM 각각), (2) UVM 적정성 판정 rubric의 세부 형식, (3) Task() 호출 시 권장 프롬프트 구조.
- 구조 경계 판단(무거운 ADR+adversarial cross-review 절차)과 UVM 적정성 판단(가벼운 권고 절차)을 하나의 입력·절차 흐름 안에서 수행하되 출력에서는 명확히 분리한다 — Checkpoint 3에서 이 지점을 아키텍처 선택지로 다룬다.

### 1.2 Design Principles

- **정본 Read, 재서술 금지** — `chip-verification`(+ `references/non-uvm-architectures.md`)/`uvm-verification`/`verilog-rtl` skill을 런타임에 전체 Read하고 판단 근거로 인용, system prompt에 지식을 복사하지 않는다(Plan FR-03).
- **`verilog-rtl-architect-advisor.md` 구조 벤치마크** — frontmatter, 책임분해·recall·ADR·adversarial cross-review 골격, 산출물 형식, "정직한 한계" 섹션까지 동형으로 재사용한다.
- **결정은 사람** — 구조 경계든 UVM 적정성이든 이 agent는 근거와 추천만 제시하고 최종 결정은 하지 않는다(Plan FR-11).

---

## 2. Architecture Options

### 2.0 Architecture Comparison

> 이 문서의 실제 설계 자유도는 "구조 경계 판단"과 "UVM 적정성 판단"이라는 서로 다른 두 축을 agent 내부에서 어느 정도로 분리·통합하는가에 있다. Plan §4가 이미 그 방향(입력은 통합, 출력은 분리)을 프로즈로 제안했으므로, 아래 비교는 그 제안을 공식 Checkpoint 3 선택지로 검증한다.

| Criteria | Option A: Minimal (완전 통합) | Option B: Clean (완전 분리) | Option C: Pragmatic (통합 입력·분리 출력) |
|----------|:-:|:-:|:-:|
| **접근** | 책임분해표 하나로 재사용범위+UVM 적정성 동시 판정, 출력도 단일 Verdict 하나 | 두 축을 독립 트리거·독립 절차·독립 출력 스키마로 완전 분리(사실상 agent 2개에 가까움) | 입력(Task 호출)은 하나로 통합 수신, 판단 절차는 순차 수행(§4.1→§4.2), 출력에서는 두 섹션으로 명확히 분리 |
| **새 파일** | 1 (`agents/verilog-tb-architect-advisor.md`) | 2(`agents/verilog-tb-architect-advisor.md` + 별도 UVM-적정성 전용 agent 또는 대형 서브섹션 파일) | 1 |
| **ADR/adversarial cross-review 적용 범위** | 구조 경계·UVM 적정성 모두에 무조건 적용 — UVM 적정성 하나 확인하는 데도 3안+cross-review가 발동되어 과잉 | 각 축마다 독립적인 ADR/cross-review 절차를 별도로 설계 | **구조 경계(ARCH)에서만** ADR+adversarial cross-review 발동, UVM 적정성은 근거 인용 권고문으로 종결 — RTL에 없는 "가벼운 축"을 무겁게 만들지 않음 |
| **복잡도** | Low(설계는 단순하나 UVM 적정성 확인마다 무거운 절차가 붙어 실사용 마찰 큼) | High(두 절차·두 트리거·두 출력 스키마 유지보수) | Medium |
| **유지보수성** | Medium(구분이 없어 향후 한쪽만 개선하기 어려움) | High(독립적이나 과설계) | High |
| **Effort** | Low | High | Medium |
| **Risk** | 사용자가 "UVM 쓸까 말까"만 물어봐도 3안 ADR이 나오는 것은 Plan §6 Risk("과잉 gearing 판단 신뢰성")를 오히려 해칠 수 있음(무거운 절차=신뢰 아님) | 두 agent에 가까운 구조라 `verilog-tb-coder`/`reviewer`의 route 로직이 "어느 쪽으로 보낼지"를 다시 판단해야 하는 새로운 분기 문제 발생 | 낮음 — Plan §4가 이미 이 형태로 설계 의도를 명시했고, RTL architect-advisor에 없는 신규 축(UVM 적정성)을 RTL과 동일한 무게로 다루지 않아도 될 근거가 §6 위험 분석에 이미 있음 |
| **Recommendation** | — | — | **기본 선택** |

**Selected**: **Option C — Pragmatic (통합 입력·분리 출력)**
**Rationale**: Option A는 "UVM 적정성"이라는, RTL에 없는 가벼운 자문성 판단에까지 3안 ADR+adversarial cross-review라는 무거운 절차를 강제해 실사용 마찰을 만든다 — Plan Executive Summary가 지향하는 "구조화된 근거를 사람에게 보여준다"는 목표와 어긋난다(불필요하게 무거우면 사람이 이 agent를 우회하게 됨). Option B는 두 축을 독립 절차로 완전히 분리하면 사실상 agent 2개를 만드는 것과 같아, `verilog-tb-coder`/`verilog-tb-reviewer`의 route 로직에 "어느 것으로 보낼지"라는 새 판단 지점을 추가하게 되고, 이는 Plan이 명시적으로 피하려던 것(Task 호출자는 그냥 "구조 변경 의심"만 넘기면 됨)과 배치된다. Option C는 Plan §4.1/§4.2가 이미 프로즈로 제안한 구조를 그대로 공식화한 것이며, 무게가 다른 두 판단을 각각에 맞는 절차(무거운 것/가벼운 것)로 다루면서도 단일 Task 호출·단일 agent 파일 유지라는 이점을 지킨다.

### 2.1 판단 절차 흐름 (Component Diagram 대체)

```
Task() 호출 (자유 형식 프롬프트, §4.1)
       │
       ▼
0. 기준 — chip-verification(+non-uvm-architectures.md) / uvm-verification / verilog-rtl 전체 Read
       │
       ▼
§4.1 책임 분해 — 재사용 범위 판단표 (1차) + UVM 환경이면 phase/objection/arbitration 독립성 (2차)
       │
       ├── Verdict = LOCAL (기존에 접기) ──────────────────────────┐
       │                                                              │
       └── Verdict = ARCH (분리 필요)                                 │
              │                                                       │
              ▼                                                       │
       §4.1b evidence 기반 recall (.ai/analysis/tb_*.analysis.md, .ai/adr/, graphify)
              │                                                       │
              ▼                                                       │
       3안 이상 candidate + ADR stub(.ai/adr/NNNN-*.md)                │
              │                                                       │
              ▼                                                       │
       fresh-context adversarial cross-review (후보 수만큼 별도 Agent) │
              │                                                       │
              ▼                                                       │
       추천안 선정(결정은 사람)                                        │
              │                                                       │
              └──────────────────────┬────────────────────────────────┘
                                      ▼
                     §4.2 UVM 도입 적정성 판단 (독립 축, 항상 수행)
                     — non-uvm-architectures.md §6 기준표 인용
                     — 과잉/적정/과소 판정, ADR 없이 권고문으로 종결
                                      │
                                      ▼
                          §5 통합 출력(두 섹션 분리) 반환
```

> **왜 §4.2(UVM 적정성)를 Verdict와 무관하게 항상 수행하는가**: 구조 경계가 LOCAL(접기)이어도 "지금 UVM 자체가 이 프로젝트에 맞는가"는 별개 질문이다(예: 재사용 범위는 넘지 않지만 이미 UVM 풀스택을 쓰고 있는 소규모 1회성 IP). 두 축이 독립적이라는 것이 Option C 선택의 핵심 근거이므로 흐름에도 그대로 반영한다.

### 2.2 Delegation Flow (Data Flow 대체)

```
[verilog-tb-coder]                      [verilog-tb-reviewer]              [사람]
 FR-08(c) STOP-and-Ask                   §4.4 [TB-ARCH-SUSPECT]              직접 요청
 (구조적 변경 의심)                       (구조적 변경 의심)
       │                                       │                              │
       └───────────────┬───────────────────────┴──────────────────────────────┘
                        ▼
            Task(자유 형식 프롬프트, §4.1 권장 구조) ──► verilog-tb-architect-advisor
                        │
                        ▼
         §5 출력(구조 판단 + UVM 적정성 판단, 결정은 사람) 반환
                        │
                        ▼
              사람이 ADR/권고안을 보고 최종 결정
                        │
                        ▼
    (구조 결정 확정 후) verilog-tb-coder에게 구현 위임 재개
```

> `verilog-tb-coder.plan.md` FR-08(c), `verilog-tb-reviewer.plan.md` §4.4의 실제 문서 갱신(라우팅 문구를 "사람에게 직접" → "이 agent로 route")은 Do 단계 항목이다(§6.2 Implementation Order 7번).

### 2.3 Dependencies

| Component | Depends On | Purpose |
|-----------|-----------|---------|
| "0. 기준"(필수, 전체) | `~/.claude/skills/chip-verification/SKILL.md` + `references/non-uvm-architectures.md` (로컬) | 듀얼탑/flat/legacy TB 아키텍처, 의사결정 기준(§4.2 rubric의 정본) |
| "0. 기준"(필수, 전체) | `~/.claude/skills/uvm-verification/SKILL.md` (로컬) | UVM 컴포넌트 세부(§4.1 2차 기준: phase/objection/arbitration) |
| "0. 기준"(필수, 전체) | `~/.claude/skills/verilog-rtl/SKILL.md` (로컬) | SV 문법 |
| Recall 대상 | `.ai/analysis/tb_*.analysis.md`(`verilog-tb-analyst` 산출물), `.ai/adr/`(과거 ADR), graphify(가용 시) | evidence 기반 recall(§4.1b) |
| ADR 템플릿 | `~/.claude/agent-kit/adr-template.md` (RTL architect-advisor와 공유) | ADR stub 형식 재사용 — 이 문서 §3에서 재사용 가능 여부 확인 |
| Adversarial cross-review | `Agent` tool (fresh-context 별도 호출) | 맥락 오염 방지 |
| Task 호출자 | `verilog-tb-coder`(FR-08(c)), `verilog-tb-reviewer`(§4.4), 또는 사람 직접 | §2.2 Delegation Flow |
| 원격 TB 확인(read-only) | `mcp__ssh__file_read`/`file_grep`/`file_ls` (세션 내 가용 시) | 원격 TB 소스 확인(`verilog-tb-analyst`/`coder`와 동일 근거) |

---

## 3. Output Format (Data Model 대체)

이 agent는 TB 소스를 Write하지 않는다(read-only). 유일한 영속 산출물은 **ARCH 판정 시의 ADR stub**이다.

| 산출물 | 경로 패턴 | 필수 항목 정본 |
|---|---|---|
| ADR stub | `.ai/adr/NNNN-{topic}.md` | `~/.claude/agent-kit/adr-template.md`(RTL architect-advisor와 동일 템플릿 재사용 — 이 agent 전용 템플릿을 별도로 만들지 않음, §8.1에서 재사용 가능 여부 확인 완료 전제로 진행하고 불가능하면 §9.2에서 최소 필드만 별도 정의) |

> **N/A**: §3.2 Entity Relationships, §3.3 SQL/MongoDB Schema — 관계형/문서 DB를 다루지 않음.

나머지 출력(Verdict, 판단표, 추천안 등)은 **파일이 아니라 대화 응답 텍스트**로 반환한다 — §5 산출물 형식 참조.

---

## 4. Task() 호출 계약 (API Specification 대체)

Plan §8.2가 "Design 단계에서 확정"으로 남긴 두 항목(재사용범위 판단표 구체 예시, 권장 프롬프트 구조)을 여기서 확정한다.

### 4.1 입력 — 권장 프롬프트 구조 (자유 형식, Plan FR-04에 따라 formal 파라미터 스키마 없음)

`verilog-tb-coder`/`verilog-tb-reviewer`/사람이 이 agent를 Task()로 호출할 때, 다음 네 요소를 자연어로 포함하는 것을 권장한다(강제 스키마 아님 — 없으면 이 agent가 STOP-and-Ask 대신 먼저 되묻는다, §6.3):

| 권장 요소 | 설명 | 예시 |
|---|---|---|
| (a) 변경/검토 대상 설명 | 무엇을 추가/변경하려는지, 또는 무엇이 구조적으로 의심되는지 | "UART 프로토콜 체커를 새로 추가해야 하는데 기존 `apb_scoreboard`에 넣을지 새 컴포넌트로 뺄지 판단 필요" |
| (b) 현재 TB 스타일(알면) | UVM / non-UVM class-based / flat legacy / 모름 | "uvm 기반 env, `apb_env` 하위" |
| (c) 호출 출처 | `verilog-tb-coder` FR-08(c) / `verilog-tb-reviewer` §4.4 TB-ARCH-SUSPECT / 사람 직접 | "verilog-tb-reviewer의 [TB-ARCH-SUSPECT] 발견으로 route됨" |
| (d) 관련 분석서(있으면) | `.ai/analysis/tb_*.analysis.md` 경로 | ".ai/analysis/tb_uvm_apb_env.analysis.md" |

### 4.2 재사용범위 판단표 — 구체 예시 (Plan §4.1의 질문표를 UVM/non-UVM 각각으로 구체화)

**UVM 환경 예시**:

| 질문 | 예시 상황 | 판정 |
|---|---|---|
| 이 검증 관심사가 현재 테스트케이스 하나에서만 쓰이는가? | 특정 코너케이스 하나를 위한 1회성 assertion 추가 | 예 → 접기(기존 monitor에 assertion 추가) |
| 독립적인 phase/objection/virtual sequencer arbitration이 필요한가? | 새 프로토콜(예: 인터럽트 채널)이 기존 APB 시퀀스와 독립적으로 동시에 진행돼야 함 | 예 → 분리(새 `interrupt_agent`) |
| 기존 컴포넌트가 서로 다른 프로토콜을 동시에 책임지게 되는가? | `apb_scoreboard`에 UART 체크 로직까지 추가 요청 | 예 → 분리(새 `uart_scoreboard`) |

**Non-UVM class-based / flat 환경 예시**:

| 질문 | 예시 상황 | 판정 |
|---|---|---|
| 이 BFM 로직을 두 번째 테스트벤치에도 쓰는가? | 동일 `send()` task를 다른 테스트 파일에 복붙하려는 시도 | 예 → 분리(package로 추출) |
| checker가 driver에 내장돼 두 관심사가 뒤섞이는가? | `send()` 안에 `if (data_out != exp)` 직접 작성 | 예 → 분리(Command/Functional 계층 분리, `references/non-uvm-architectures.md` §7) |
| flat 구조가 gate-level/timing 시뮬레이션 전환 예정에 부합하는가? | 곧 SDF-annotated netlist 시뮬레이션 예정 | 아니오 → dual-top 전환 필요(ARCH) |

### 4.3 UVM 도입 적정성 판단 — rubric 형식

`references/non-uvm-architectures.md` §6 "UVM vs Non-UVM class-based(G5)" 표의 조건을 그대로 rubric으로 사용한다(재서술 금지 — 표 자체는 정본에서 Read). 판정은 다음 3가지 중 하나:

| 판정 | 의미 | 출력 시 반드시 포함 |
|---|---|---|
| **과잉(over-gearing)** | 소규모 IP(프로토콜 1~2개, 프로젝트 수명 6개월 미만)에 UVM 풀스택 요구 | 인용한 §6 조건 문구 + factory override 실제 필요 여부 확인 결과 |
| **적정** | 현재 규모/재사용 범위에 UVM 도입 수준이 부합 | 인용한 §6 조건 문구 |
| **과소(under-gearing)** | 이미 여러 프로젝트/팀 재사용 중이거나 SoC 통합 예정인데 flat/directed 구조 고집 | 인용한 §6 조건 문구 |

### 4.4 정상 흐름 검증 — Adversarial Cross-Review 프롬프트 골격은 Plan §4.3을 그대로 사용(변경 없음)

---

## 5. 산출물 / 보고 형식 (Output, RTL architect-advisor §5와 동형)

- **Mode**: `P`(plan/design 문서 또는 route된 구조 변경 선언) — 이 버전은 P-모드만 지원(Plan FR-04, C-모드 Out of Scope)
- **재사용범위 판단표**(§4.2 형식): 질문별 답 + 판정 근거
- **Verdict**: `ARCH` / `LOCAL`
- **ARCH면**: ADR stub 경로(`.ai/adr/NNNN-*.md`) + 후보 3개 이상(각 structural 특성) + adversarial cross-review 표(약점/방어/잔존위험) + 추천안(잔존위험 최소, 결정은 사람)
- **UVM 적정성 판정**(§4.3 형식, Verdict와 독립적으로 항상 포함): 과잉/적정/과소 + 인용 근거
- **다음 행동**: `verilog-tb-coder` 구현 위임 재개 / 사람 비준 대기 / (필요시) `verilog-tb-analyst` 분석서 갱신 요청 중 하나

---

## 6. Error Handling (Error Handling 대체)

| 상황 | 처리 |
|---|---|
| Task 프롬프트에 §4.1 (a)~(c) 중 하나라도 특정 불가할 만큼 불명확 | 추측하지 않고 명확화 질문으로 되묻는다(구현이 아니므로 STOP-and-Ask보다는 clarifying question에 가까움) |
| `chip-verification`/`uvm-verification`/`verilog-rtl` skill 파일 부재 | BLOCKER로 명시적 중단 — 임시로 지식을 내장하지 않음(§1.2 원칙) |
| `references/non-uvm-architectures.md` 부재(배포 누락 등) | BLOCKER — §4.3 UVM 적정성 판단의 근거 정본이므로 이것 없이 임의 판단 금지 |
| ADR 후보가 3개 미만으로만 도출됨 | 그 자체로 single-hypothesis anchoring 위험 신호로 보고 — 추가 후보 도출을 다시 시도, 그래도 안 되면 그 사실을 명시적으로 보고(조용히 2개로 진행 금지) |
| adversarial cross-review용 Agent 호출 실패(일부만 반환) | 반환된 후보만으로 종합 판정하되 Manifest에 "N개 중 M개만 응답" 명시 |

> **N/A**: §7 Security Considerations — 웹 입력·인증 표면이 없음.

---

## 7. Test Plan (검증 계획, L1/L2/L3 대신 수동 시나리오)

Plan §5.1 Definition of Done을 실행 가능한 시나리오로 구체화한다.

| # | 시나리오 | 절차 | 성공 기준 |
|---|---|---|---|
| 1 | UVM 환경 — 구조 분리가 맞는 경우 | §4.1 "독립 phase/arbitration 필요" 예시(인터럽트 채널 신규)로 호출 | Verdict=ARCH, 후보 A에 새 컴포넌트 분리안 포함, 3안 이상 |
| 2 | UVM 환경 — 접어도 되는 경우 | 재사용 범위 1개 한정 assertion 추가로 호출 | Verdict=LOCAL, ADR 미생성 |
| 3 | Non-UVM — 구조 분리가 맞는 경우 | BFM 복붙 시도 시나리오로 호출 | Verdict=ARCH, 후보에 package 추출안 포함 |
| 4 | UVM 과잉(over-gearing) | 소규모 1~2 프로토콜 IP에 UVM 풀스택 요구 시나리오 | §4.3 판정=과잉, `non-uvm-architectures.md` §6 조건 문구 인용 확인 |
| 5 | UVM 과소(under-gearing) | 이미 재사용 중인 VIP가 flat 구조 고집하는 시나리오 | §4.3 판정=과소, 근거 인용 확인 |
| 6 | Adversarial cross-review 실제 fresh-context 검증 | ARCH 판정 시나리오 실행 후 cross-review 단계에서 별도 Agent가 호출되는지 확인 | 이 agent의 §4.1/§4.1b 분석 내용이 cross-review Agent 프롬프트에 전달되지 않음(맥락 오염 금지 준수) |
| 7 | route 입력 형식 검증 | `verilog-tb-coder`/`verilog-tb-reviewer`가 route할 때 쓸 §4.1 권장 프롬프트 구조로 실제 호출 | 4요소 없이도 동작하되, 없으면 명확화 질문으로 되묻는지 확인 |
| 8 | ADR stub 생성 검증 | ARCH 판정 시나리오에서 `.ai/adr/NNNN-*.md` 실제 생성 확인 | `adr-template.md` 형식 준수, 경로/번호 규칙 정합 |

---

## 8. Implementation Guide

### 8.1 File Structure

```
agents/
└── verilog-tb-architect-advisor.md   (신규)

install.py   (AGENTS 목록에 추가)
```

> **N/A**: §9 Clean Architecture, §10 Coding Convention Reference — markdown agent 정의 파일에는 해당 사항 없음.

### 8.2 Implementation Order

1. [ ] Frontmatter 작성(`name`/`description`(Use it when/Do NOT use for/Triggers)/`tools`/`model: opus`) — Plan FR-01, `verilog-rtl-architect-advisor.md` 벤치마크
2. [ ] "0. 기준" 절 작성 — `chip-verification`(+`references/non-uvm-architectures.md`)/`uvm-verification`/`verilog-rtl` 전체 Read 지시 — Plan FR-03
3. [ ] §2.1 판단 절차 흐름 반영 — §4.1 책임분해 → (ARCH면) §4.1b recall → 3안 ADR → adversarial cross-review → §4.2 UVM 적정성(항상) — Plan FR-05~FR-09
4. [ ] §4.2/§4.3의 구체 예시표(이 문서 §4.2/§4.3)를 agent 파일에 반영
5. [ ] Adversarial cross-review 프롬프트 골격(Plan §4.3) 반영, STEP 0에 non-uvm-architectures.md Read 명시
6. [ ] §5 산출물 형식 반영
7. [ ] 하드 제약(구현 금지, partitioning/UVM 도입 최종 결정 금지) + "정직한 한계" 섹션 작성 — Plan FR-11
8. [ ] `install.py` AGENTS 목록에 등록
9. [ ] `docs/01-plan/features/verilog-tb-coder.plan.md` FR-08(c), `docs/01-plan/features/verilog-tb-reviewer.plan.md` §4.4의 route 문구를 "사람에게 직접" → "이 agent로 route"로 갱신
10. [ ] §7 Test Plan 시나리오 1~8으로 수동 검증 후 `install.py --only agents` 재배포

### 8.3 Session Guide

파일 1개짜리 agent 정의 작업이라 모듈 분할 불필요 — 단일 세션 권장.

| Session | Phase | Scope | Turns |
|---------|-------|-------|:-----:|
| Session 1 (이전) | Plan | 전체 + `chip-verification` skill 확장(non-uvm-architectures.md) | 완료 |
| Session 2 (현재) | Design | 전체 | 완료 |
| Session 3 | Do | `agents/verilog-tb-architect-advisor.md` 작성 + install.py 등록 + 두 sibling plan 문서 route 갱신 | 30-40 |
| Session 4 | Check + Report | §7 시나리오 1~8 검증 + gap 분석 | 20-30 |

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-07-21 | 초안 — Checkpoint 3에서 Option C(통합 입력·분리 출력) 채택. Plan §8.2가 미뤄둔 세 항목(재사용범위 구체 예시, UVM 적정성 rubric 형식, 권장 프롬프트 구조)을 이 문서에서 확정. 웹앱 전용 섹션은 `verilog-tb-analyst.design.md` 선례를 따라 N/A 처리 | HSLEE |
