# Agent Validation Prompt (LLM-as-judge)

> `check_agents.py`(AUTO)가 *구조적 누락*을 잡은 뒤, 이 프롬프트로 *내용의 적절성*(JUDGE 항목)을 본다.
> 사용: 아래 프롬프트에 대상 `agents/<name>.md` 전문을 붙여 LLM(또는 사람)에게 평가시킨다.
> 근거: Anthropic *Building Effective Agents* [A] · OpenAI *Practical Guide to Building Agents* [O].
> 루브릭 전체: `agent-quality/AGENT_BEST_PRACTICES.md`.

---

## 프롬프트

```
You are reviewing a Claude Code subagent definition against agent best practices
distilled from Anthropic "Building Effective Agents" and OpenAI "A Practical Guide
to Building Agents". The AUTO linter already checked structural presence; you judge
the QUALITY of the following dimensions. For each, answer PASS / WEAK / FAIL with a
one-sentence reason and, if not PASS, a concrete fix.

Evaluate this agent definition:
<<<
{paste the full agents/<name>.md here}
>>>

Judge these dimensions:

1. R5 SIMPLICITY / RIGHT ALTITUDE [A,O]
   - Is this genuinely agentic (open-ended, unpredictable step count, needs dynamic
     tool decisions), or could the job be a fixed WORKFLOW or a single augmented LLM
     call? If workflow-shaped, say which pattern (chaining/routing/parallel/
     orchestrator/evaluator) and recommend simplifying.
   - If it is one of several agents: is the split justified by COMPLEX LOGIC (many
     if-then-else) or TOOL OVERLOAD (overlapping tools), per OpenAI? Or should it be
     folded back into a single agent ("maximize a single agent first")?
   - Is the prompt over-engineered (ceremony that doesn't change behavior)?

2. R3 INSTRUCTIONS QUALITY [O]
   - Are the steps clear and ordered, each mapping to a SPECIFIC action/output?
   - Are EDGE CASES / decision points handled (what to do on missing info, blockers,
     ambiguous input) with explicit branches?
   - Could a "junior developer" follow it without guessing? [A: document like for a junior]

3. R1 MODEL FIT [O]
   - Is the model tier right for the task (analysis/judgment -> opus; mechanical/
     deterministic -> sonnet/haiku)? Is a cheaper model viable for part of the work?

4. R2 TOOL / ACI QUALITY [A,O]
   - Is the tool set MINIMAL and NON-OVERLAPPING? Any tool that is unused or
     redundant? Any missing tool the routine clearly needs?
   - Are tool uses well-scoped (read-only vs write) and poka-yoke (hard to misuse)?

5. R7 TRANSPARENCY [A]
   - Does it make the agent SHOW its planning/reasoning and produce an explicit,
     well-specified REPORT/OUTPUT format (so a human/next-agent can act on it)?

6. R9 GUARDRAILS / TOOL RISK [O,A]
   - Are HIGH-RISK / IRREVERSIBLE actions (file delete, external send, prod writes,
     editing shared/submodule RTL) gated, rated, or forbidden?
   - Are the hard constraints sufficient to prevent the failure modes this agent
     is prone to?

7. R10 ESCALATION / HUMAN-IN-THE-LOOP [O,A]
   - Are FAILURE THRESHOLDS (retry/iteration limits) and HIGH-RISK actions routed to
     a human or another owner? Is "don't decide this alone" explicit where it should be?

Finish with:
- OVERALL: PASS / NEEDS-WORK / FAIL
- TOP 3 concrete fixes (ordered by impact).
```

---

## 판정 기준 (요약)

- **PASS**: 7개 차원 모두 PASS, AUTO도 0 FAIL.
- **NEEDS-WORK**: WEAK가 있으나 FAIL 없음 → 권고 반영.
- **FAIL**: 어느 차원이든 FAIL(예: workflow로 충분한데 agent로 과설계 / high-risk 무방비 / 경계 없음).

> 두 문서의 공통 정신: **단순하게 시작하고, 투명하게 드러내고, 인터페이스(도구·지시·경계)에 공을 들이고, 위험·실패엔 사람을 끼운다.** AUTO가 뼈대를, JUDGE가 이 정신의 충족을 확인한다.
