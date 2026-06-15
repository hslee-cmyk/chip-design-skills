# OpenAI — A Practical Guide to Building Agents (학습 노트)

> 원문(PDF): https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf (2025)
> 한 줄 요지: **강한 기초(Model·Tools·Instructions)에서 시작해 단일 agent를 최대화하고, 필요할 때만 multi-agent로,
> 모든 단계에 layered guardrail + 사람 개입을 둔다.**

---

## 1. Agent란 무엇인가

> "Agents are systems that **independently accomplish tasks on your behalf**."

- LLM이 **워크플로 실행을 관리**하고 결정을 내린다. **완료를 인식**하고, 필요하면 스스로 교정하며,
  **실패 시 실행을 멈추고 사람에게 제어를 넘긴다**.
- **도구**로 외부 시스템과 상호작용(컨텍스트 수집 + 행동), 상태에 따라 도구를 **동적으로 선택**, 항상 **guardrail 안에서**.
- ❌ agent가 아닌 것: 단순 챗봇, 단일턴 LLM, 감정분류기 — LLM을 쓰지만 **워크플로 실행을 제어하지 않음**.

---

## 2. 언제 agent를 만드나 (3가지 신호)

전통적 결정론·룰 기반이 막히는 곳을 노려라. (비유: 룰엔진=체크리스트 / agent=노련한 수사관)

| # | 신호 | 예시 |
|---|------|------|
| 1 | **Complex decision-making** — 미묘한 판단·예외·맥락 의존 결정 | 고객서비스 환불 승인 |
| 2 | **Difficult-to-maintain rules** — 룰셋이 비대해져 수정이 비싸고 오류나기 쉬움 | 벤더 보안 리뷰 |
| 3 | **Heavy reliance on unstructured data** — 자연어 해석·문서에서 의미 추출·대화 | 주택보험 청구 처리 |

> ⚠️ 만들기 전에 **이 기준을 명확히 충족하는지 검증**하라. 아니면 **결정론적 해법이 더 낫다.**

---

## 3. 세 가지 기초 (Foundations)

agent = **Model + Tools + Instructions**.

### 3-1. Model (추론 엔진 선택)
- 작업마다 복잡도·latency·cost 트레이드오프가 다르다 — **모든 작업에 최강 모델이 필요하진 않다**.
- 권장 절차:
  1. **evals로 성능 baseline 설정**.
  2. **가장 강한 모델로 정확도 목표 달성**(먼저 능력 한계를 막지 마라).
  3. **가능한 곳은 더 작은 모델로 교체**해 cost·latency 최적화.

### 3-2. Tools (외부 능력)
- 각 도구는 **표준화된 정의** → 도구↔agent의 유연한 다대다 관계. **잘 문서화·충분히 테스트·재사용 가능**해야
  discoverability↑, 버전관리↑, 중복정의 방지.
- **세 가지 타입**:
  | 타입 | 역할 | 예 |
  |------|------|----|
  | **Data** | 컨텍스트·정보 검색 | DB/CRM 조회, PDF 읽기, 웹검색 |
  | **Action** | 시스템에 행동 | 이메일/문자 전송, 레코드 갱신, 티켓 핸드오프 |
  | **Orchestration** | **다른 agent를 도구로** | Refund agent, Research agent (→ Manager 패턴) |
- 도구 수가 늘면 **여러 agent로 분리 고려**(§4).

### 3-3. Instructions (지시·가드라인)
지시 품질이 agent 성패를 좌우. 베스트 프랙티스 4:
- **기존 문서 활용** — 운영절차(SOP)·지원 스크립트·정책 문서를 LLM-friendly routine으로. (CS면 KB 문서 1개 ≈ routine 1개)
- **작업을 작게 쪼개라** — 밀도 높은 자료를 **더 작고 명확한 단계**로.
- **명확한 action 정의** — 모든 단계가 **구체 action/output**에 대응(예: "주문번호를 물어라", "API를 호출하라").
  사용자 메시지 문구까지 명시하면 해석 오류↓.
- **edge case 포착** — 정보 누락·예상 밖 질문 같은 결정 지점을 **조건 분기**로 미리 처리.
- 팁: 고급 모델(o1/o3-mini 등)로 **문서에서 지시를 자동 생성**할 수 있다.

---

## 4. Orchestration (점진적으로)

> "fully autonomous를 바로 만들지 말고 **incremental approach**로 가라."

### 4-1. Single-agent (run loop)
- 도구를 **점진적으로 추가**해 한 agent로 많은 일을 처리 — 복잡도·평가·유지가 쉬움.
- 핵심은 **`run` 루프**: 종료 조건까지 반복. 종료 = (a) final-output 도구 호출, (b) 도구 호출 없는 응답, (c) **최대 반복수**, (d) 에러.
- 복잡도 관리 팁: **prompt template + 변수**. 유스케이스마다 프롬프트를 새로 쓰지 말고, **변수만 교체**하는 단일 베이스 프롬프트.

### 4-2. 언제 multi-agent로 쪼개나
> 일반 원칙: **먼저 단일 agent의 능력을 최대화**하라. agent를 늘리면 직관적 분리는 되지만 복잡도·오버헤드가 는다.

분리 신호 2가지:
- **Complex logic** — 프롬프트에 if-then-else 분기가 많아 template 확장이 어려울 때 → 논리 구간별로 agent 분리.
- **Tool overload** — *개수가 아니라 유사/중복*이 문제. 잘 정의된 도구는 15개+도 OK, 겹치는 도구는 10개 미만도 헤맴.
  → 먼저 **이름·파라미터·설명을 명확히** 해보고, 그래도 안 되면 분리.

### 4-3. Multi-agent 두 패턴
- **Manager (agents as tools)** — 중앙 "manager"가 전문 agent들을 **도구 호출**로 조율·합성.
  *한 agent가 흐름과 사용자 접점을 통제*하고 싶을 때 이상적. (예: 번역 manager → 스/프/이 agent)
- **Decentralized (handoffs)** — agent들이 동등하게 서로에게 **handoff(일방향 제어 이전)**.
  *중앙 합성이 필요 없고 각 agent가 완전히 인수*해도 될 때(예: CS triage → 해당 전문 agent).
- 공통 원칙: 컴포넌트를 **flexible·composable·명확한 프롬프트**로.

---

## 5. Guardrails (계층 방어) + 사람 개입

> 단일 guardrail로는 부족. **여러 특화 guardrail을 겹쳐(layered)** 견고하게. 인증·권한·접근통제 등
> 표준 보안과 **함께** 가야 함.

### Guardrail 타입
| 타입 | 역할 |
|------|------|
| **Relevance classifier** | 응답이 의도된 범위를 벗어나면 flag(off-topic) |
| **Safety classifier** | jailbreak·prompt injection 탐지 |
| **PII filter** | 출력의 개인식별정보 노출 방지 |
| **Moderation** | 혐오·괴롭힘·폭력 등 유해 입력 flag |
| **Tool safeguards** | 도구별 **risk rating(low/med/high)** — read-only vs write, 가역성, 권한, 금전영향. high면 **실행 전 일시정지/사람 escalate** |
| **Rules-based protections** | blocklist, 입력 길이 제한, regex(예: SQL injection) |
| **Output validation** | 브랜드 가치 정렬, 부적절 출력 차단 |

### 구축 휴리스틱
1. **데이터 프라이버시 + 콘텐츠 안전** 먼저.
2. **실제 edge case·실패**를 만나며 guardrail 추가.
3. **보안과 UX 둘 다** 최적화하며 진화.

### 사람 개입 (human-in-the-loop) — 2가지 트리거
- **Failure threshold 초과** — retry/행동 횟수 한계 초과(예: 의도 파악 반복 실패) → 사람에게 escalate.
- **High-risk action** — 민감·**비가역**·고위험 행동(주문 취소, 큰 환불 승인, 결제)은 신뢰가 쌓이기 전까지 사람 감독.

---

## 핵심 takeaways
- agent는 **complex decision / unstructured data / brittle rules**에 적합. 아니면 결정론적 해법.
- 기초 **Model·Tools·Instructions**가 전부의 토대 — 특히 **명확한 단계·action·edge case 지시**.
- **single agent 최대화 먼저**, 분리는 complex-logic·tool-overload일 때만.
- **layered guardrail + human-in-the-loop(failure threshold·high-risk)** 는 모든 단계에 필수.
- **Start small, validate with real users, grow.**

## 복습 질문 (셀프체크)
1. 내 유스케이스가 3신호(복잡판단/유지난해룰/비정형데이터)를 정말 충족하나?
2. 각 작업에 맞는 모델 tier를 골랐나? 더 싼 모델로 대체 가능한 부분은?
3. 도구가 data/action/orchestration로 분류되고, 중복 없이 명확한가?
4. single agent로 충분한가, 아니면 complex-logic/tool-overload가 분리를 정당화하나?
5. high-risk·비가역 행동에 사람 개입 트리거가 걸려 있나?
