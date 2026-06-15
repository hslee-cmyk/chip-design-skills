# Agent Best-Practices Rubric

> chip-design-skills의 모든 `agents/*.md` 정의가 따라야 하는 best-practice 체크리스트.
> **agent를 새로 만들거나 수정할 때마다** 이 룰을 점검한다 (`python agent-quality/check_agents.py`).
>
> **출처** (두 문서를 종합):
> - **[A]** Anthropic, *Building Effective Agents* — workflows↔agents 구분, **3원칙(Simplicity·Transparency·Agent-Computer Interface)**, tool 설계(poka-yoke·생각할 토큰·자연스러운 포맷·충분한 문서·광범위 테스트).
> - **[O]** OpenAI, *A Practical Guide to Building Agents* — **3 foundation(Model·Tools·Instructions)**, single→multi-agent 점진적 orchestration, **layered guardrails**, human-in-the-loop(failure threshold·high-risk action).
>
> 점검 종류: **AUTO** = `check_agents.py`가 기계적으로 검사 · **JUDGE** = `agent-validation-prompt.md`로 LLM/사람이 판단.

---

## 핵심 원칙 (두 문서 공통)

> **"가장 단순한 해법에서 시작하고, 필요할 때만 복잡도를 올린다."** [A]
> **"먼저 단일 agent의 역량을 최대화하고, 필요할 때만 multi-agent로 나눈다."** [O]
> agent는 latency·cost를 성능과 맞바꾸므로, *fixed 경로로 충분하면 workflow/단일 호출*이 맞다.

---

## 규칙 (R1–R12)

| # | 규칙 | 무엇을 본다 | 점검 | 출처 |
|---|------|------------|------|------|
| **R1** | **Model fit** | `model:` 필드 존재 + task에 맞는 tier (분석/판단=opus, 기계적 구현=sonnet/haiku). 모든 task에 최강 모델을 쓰지 않는다. | AUTO+JUDGE | O(model), A(simplicity) |
| **R2** | **Tool minimality & clarity (ACI)** | `tools:` 가 **명시적 최소 목록** (`*`/"All tools" 지양). 도구는 distinct·non-overlapping. 이름/경계가 명확. | AUTO+JUDGE | A(ACI), O(tools) |
| **R3** | **Instructions: steps·actions·edge cases** | 본문이 **명확한 절차 단계**를 갖고, 각 단계가 **구체 action/output**에 대응하며, **edge case/분기**를 다룬다. | JUDGE(AUTO: 절차 섹션 존재) | O(instructions) |
| **R4** | **Single responsibility + boundaries** | description에 **when-to-use AND when-NOT-to-use**(do NOT / HANDS OFF / 되돌린다)가 둘 다 있다. 역할이 하나로 또렷. | AUTO | O(when to build), A(scope) |
| **R5** | **Simplicity / right altitude** | 과설계 아님. 이게 **진짜 agentic** 인가, 아니면 workflow/단일호출이 맞나? multi-agent 분리가 **complex-logic·tool-overload로 정당화**되나? | JUDGE | A(start simple), O(maximize single agent) |
| **R6** | **Routing triggers** | description에 **Triggers**(라우팅 키워드)가 있어 언제 호출되는지 분류 가능. | AUTO | O/A(routing) |
| **R7** | **Transparency** | **계획/추론 단계를 드러내고**, **명시적 보고/output 형식**(report format)을 요구한다. | AUTO(보고 섹션)+JUDGE | A(transparency) |
| **R8** | **Stop conditions** | **종료/반복 한계/scope-exit**(stop·max iteration·BLOCKER·scope 밖이면 되돌림)이 정의됨. | AUTO | A(stop conditions), O(failure threshold) |
| **R9** | **Guardrails / hard constraints** | **해서는 안 되는 것**(하드 제약·금지)이 명시. **high-risk/비가역 도구 사용**(write·삭제·외부전송)에 안전장치/리스크 인지. | AUTO+JUDGE | O(guardrails·tool safeguards), A(guardrails) |
| **R10** | **Human escalation / handoff** | failure threshold·high-risk 시 **사람/다른 owner로 escalate/handoff**. 단독 결정 금지 지점이 명확. | AUTO+JUDGE | O(human intervention), A(human oversight) |
| **R11** | **Honest limits** | **증명/수행 못 하는 것**을 정직히 적은 섹션이 있다(한계·limits). | AUTO | A(transparency·honest) |
| **R12** | **Evals / regression** | **answer-key/regression/test** 참조로 동작이 검증 가능(set up evals, test extensively). | AUTO | O(evals), A(test extensively) |

---

## "좋은 agent 정의"의 모습 (요약)

1. **Frontmatter**: `name`(=파일명, kebab-case) · `description`(역할 1줄 + when-to-use + **do-NOT-use** + **Triggers**) · `tools`(명시적 최소 목록) · `model`(task tier).
2. **Body**: 역할/원칙 → **절차(단계=action)** → **scope(OWN vs HANDS OFF)** → **하드 제약/금지** → **정직한 한계** → **regression/answer-key**.
3. **단순성**: workflow로 충분한 일을 agent로 만들지 않는다. multi-agent는 complex-logic·tool-overload가 있을 때만.
4. **제어**: stop 조건 + guardrail + 사람 escalate 지점이 빠지지 않는다.

---

## 사용법

```bash
# 모든 agent 점검 (CI / 커밋 전 게이트)
python agent-quality/check_agents.py

# 한 agent만
python agent-quality/check_agents.py agents/verilog-rtl-prover.md

# 판단(JUDGE) 항목은 LLM/사람이 agent-validation-prompt.md 로 리뷰
```

AUTO가 PASS여도 **R3/R5/R7/R9/R10의 JUDGE 부분**은 사람/LLM 리뷰가 필요하다 — AUTO는 *구조적 누락*을 잡고, JUDGE는 *내용의 적절성*을 본다 (Anthropic ACI: "도구·인터페이스에 프롬프트만큼 공을 들여라"의 정신).
