# Anthropic — Building Effective Agents (학습 노트)

> 원문: https://www.anthropic.com/engineering/building-effective-agents (2024-12)
> 한 줄 요지: **가장 단순한 해법에서 시작하라. 에이전트는 성능을 latency·cost와 맞바꾼다 — 필요할 때만 써라.**

---

## 1. Workflow vs Agent — 용어부터

둘 다 "agentic system"이지만 구분이 핵심이다.

- **Workflow**: LLM과 도구가 **미리 정해진 코드 경로(predefined code paths)** 로 오케스트레이션되는 시스템.
  → *흐름을 사람이 코드로 고정*한다.
- **Agent**: LLM이 **스스로 자기 프로세스와 도구 사용을 동적으로 지휘(dynamically direct)** 하는 시스템.
  → *흐름을 모델이 런타임에 결정*한다.

판단 기준: 단계 수·경로를 **미리 정할 수 있으면 workflow**, **미리 정할 수 없으면(open-ended) agent**.

---

## 2. 핵심 철학: Start Simple (이 문서의 중심 주장)

> "Find the simplest solution possible, and only increase complexity when needed."

- 많은 경우 **단일 LLM 호출 + retrieval + in-context 예시**로 충분하다.
- 에이전트는 더 나은 성능을 주지만 **latency·cost 증가, 오류 누적(compounding errors)** 위험이 있다.
- **프레임워크 주의**: LangGraph·SDK 등은 시작을 쉽게 하지만 추상화 레이어가 디버깅을 가린다.
  → 직접 LLM API로 시작하고, 프레임워크를 쓰더라도 **그 밑단 코드를 이해**하라.

> 의사결정: *복잡도를 올리는 것은 측정 가능한 개선이 입증될 때만.*

---

## 3. 빌딩 블록: The Augmented LLM

모든 패턴의 기본 단위. LLM에 **retrieval(검색) · tools(도구) · memory(메모리)** 를 붙인 것.
- 모델이 스스로 검색 쿼리를 만들고, 도구를 고르고, 무엇을 기억할지 정한다.
- 권고: 이 보강(augmentation)을 **(1) 유스케이스에 맞게 다듬고, (2) 모델이 쓰기 쉬운 인터페이스로** 제공.

---

## 4. Workflow 패턴 5종 (가장 실용적인 부분)

| 패턴 | 정의 | 언제 쓰나 |
|------|------|----------|
| **Prompt chaining** | 작업을 순차 단계로 쪼개 각 LLM 호출이 이전 출력을 처리 (중간 **gate** 가능) | **고정된 하위작업으로 분해 가능**할 때. 정확도를 위해 latency를 양보 |
| **Routing** | 입력을 분류해 **전문화된 후속 작업**으로 보냄 | 입력에 **구분되는 카테고리**가 있을 때. one-size-fits-all 최적화 충돌 방지 |
| **Parallelization** | 독립 하위작업 분할(**sectioning**) 또는 같은 작업 여러 번(**voting**) | 속도(sectioning) 또는 다중 관점 신뢰도(voting)가 필요할 때 |
| **Orchestrator-workers** | 중앙 LLM이 작업을 **동적으로** 쪼개 worker에 위임, 결과 합성 | 하위작업을 **미리 예측 못 하는** 복잡 작업(예: 다중 파일 코드 변경) |
| **Evaluator-optimizer** | 한 LLM이 생성, 다른 LLM이 평가 → **피드백 루프** | **명확한 평가 기준**이 있고, 반복 개선이 실제로 품질을 높일 때 |

> 포인트: **Orchestrator-workers**는 분할을 *모델이* 한다는 점에서 parallelization(분할을 *코드가* 고정)과 다르다.
> 이 5개는 *workflow* 다 — 흐름이 정해져 있다. 흐름 자체가 불확실하면 다음 절(Agents).

---

## 5. Agents (자율 시스템)

**언제**: open-ended 문제, 단계 수 예측 불가, 고정 경로를 하드코딩 못 함. "대화 + 행동 + 명확한 성공기준 +
피드백 루프 + 사람 감독"이 필요한 작업.

**동작**:
- 사람의 명령/논의로 시작 → 작업 명료화 후 **독립적으로 계획·실행**.
- 매 단계 **환경에서 ground truth 획득**(도구 결과, 코드 실행 결과)으로 진척을 평가.
- **체크포인트·블로커에서 사람에게 일시정지**할 수 있음.
- **종료 조건(stopping conditions, 예: 최대 반복수)** 으로 통제.

**주의**: 자율성이 높을수록 **비용·오류 누적**이 커진다 →
- 구현은 **단순하게**(보통 "도구를 루프로 쓰는 LLM"이면 충분),
- **샌드박스에서 광범위 테스트** + **적절한 guardrail** 필수.

---

## 6. 세 가지 구현 원칙 (꼭 기억)

1. **Simplicity** — 에이전트 설계를 단순하게 유지.
2. **Transparency** — 에이전트의 **계획 단계를 명시적으로 드러내라**(planning steps visible).
3. **Agent-Computer Interface (ACI)** — **도구 문서화와 테스트에 공을 들여라.**
   → "사람을 위한 UI(HCI)에 들이는 노력만큼, 모델을 위한 ACI에 투자하라."

---

## 7. Appendix 심화 — "도구를 prompt-engineering 하라" (ACI 실전)

도구는 그냥 함수 시그니처가 아니라 **모델이 읽는 인터페이스**다. 설계 규칙:

- **생각할 토큰을 줘라** — 모델이 *코너로 몰리기 전에* 추론할 여지(token space)를 남겨라.
- **자연스러운 포맷에 가깝게** — 모델이 학습 중 많이 본 형태를 써라.
- **포맷 오버헤드 제거** — 정확한 카운트 유지·문자열 escaping 같은 부담을 없애라.
  예: diff보다 **전체 파일 재작성**을 선호, 불필요한 JSON escaping 회피.
- **충분한 문서** — 예시 사용법, edge case, 입력 포맷 요구, **다른 도구와의 경계**를 적어라.
  → "신입 개발자에게 문서 쓰듯" 명확하게.
- **Poka-yoke(실수 방지) 설계** — 인자를 바꿔 **실수 자체를 어렵게**. 예: 상대경로 대신 **절대경로 요구**.
- **파라미터 이름을 명확하게** — 헷갈리지 않게.
- **광범위 테스트** — 워크벤치에서 여러 입력을 돌려 모델이 어떤 실수를 하는지 보고 반복 개선.
  (실제로 SWE-bench 에이전트에서 *전체 프롬프트보다 도구 최적화에 더 많은 시간*을 썼다.)

---

## 핵심 takeaways
- **단순함이 기본값**. workflow/단일 호출로 되면 agent를 쓰지 마라.
- workflow는 **5패턴**으로 거의 다 커버된다(chaining/routing/parallel/orchestrator/evaluator).
- agent는 **stop 조건 + guardrail + 샌드박스 테스트** 없이는 위험.
- **ACI(도구·인터페이스)** 가 성능을 좌우한다 — 프롬프트만큼 공들여라.

## 복습 질문 (셀프체크)
1. 내 작업은 workflow인가 agent인가? 단계 수를 미리 알 수 있나?
2. 5패턴 중 어느 것이 맞나? 왜?
3. 내 도구 설명은 "신입 개발자"가 실수 없이 쓸 만큼 명확한가? poka-yoke가 적용됐나?
4. 에이전트의 stop 조건과 guardrail은 무엇인가?
