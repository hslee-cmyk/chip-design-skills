# Chip-Design Agents

Claude Code subagents for Verilog/SystemVerilog RTL, derived from an AI-failure forensic study of
`venezia-fpga` (57 human-correction commits on an AI-implemented feature). A **Constrain-&-Escalate**
4-agent + router system: detect the architectural boundary, escalate decisions, route each bug class to its
cheapest reliable verifier (formal / static / sim).

> This `agents/` dir holds **only valid agent `.md` files** (Claude Code scans `~/.claude/agents/*.md`).
> The tools and reference docs they call live in **`../agent-kit/`** → deployed to `~/.claude/agent-kit/`.

## Agents
| Agent | Role | model | tools |
|---|---|---|---|
| `verilog-rtl-architect-advisor` | COMPUTE "new FSM vs state" (structural-delta) → escalate (ADR) + route | opus | Read/Glob/Grep/Bash |
| `verilog-rtl-coder` (constrained Implementer) | code only within a ratified micro-arch; model-diff gate A0 | sonnet | + Write/Edit |
| `verilog-rtl-reviewer` | AI-failure signatures S1–S13 (static) / R1–R9 (routed) | opus | + Write |
| `verilog-rtl-prover` | independent formal intent properties (sby), FAIL-first | opus | + Write/Edit |

## agent-kit (`../agent-kit/` → `~/.claude/agent-kit/`)
- **tools**: `boundary-classifier.py` (structural-delta ARCH/IFACE/LOCAL) · `bug-class-router.py` (class→route+owner)
  · `harness_builder.py` (sby harness skeleton) · `pre-merge-check.py` (ARCH→BLOCK gate)
- **refs**: `failure-taxonomy.md` (T1–T9) · `property-library.md` (TPL-1..7) · `adr-template.md` · `methodology.md`
  · `evidence.md`
- Agents reference these by absolute path `~/.claude/agent-kit/...` (resolves in any project after install).

## Deploy
```bash
python install.py            # skills + agents + agent-kit -> ~/.claude/{skills,agents,agent-kit}/
python install.py --dry-run  # preview
python install.py --only agents
```

## Best-practices gate (`../agent-quality/`)
Every new or modified agent must pass the rubric distilled from Anthropic *Building Effective Agents*
(Simplicity · Transparency · ACI) + OpenAI *A Practical Guide to Building Agents* (Model/Tools/Instructions ·
single→multi-agent · layered guardrails · human-in-the-loop):
```bash
python agent-quality/check_agents.py                 # AUTO lint R1–R12 (exit 1 on FAIL)
python agent-quality/check_agents.py agents/foo.md    # one agent
```
- `agent-quality/AGENT_BEST_PRACTICES.md` — rubric (rule → source → AUTO/JUDGE)
- `agent-quality/agent-validation-prompt.md` — LLM-as-judge for the JUDGE rules (R3/R5/R7/R9/R10)

These live **outside** `agents/` on purpose: `agents/` is deployed verbatim to `~/.claude/agents/`, so it must
hold only valid agent `.md`. (`install.py` also skips any `agents/*.md` without YAML frontmatter as a backstop.)

## Generic vs project-specific
- **Here (shared, reusable):** agents, tools, templates, generic taxonomy/methodology.
- **In each project's `.ai/`:** module analyses (`.ai/analysis/{module}.analysis.md`), ADRs (`.ai/adr/`),
  the project's forensics / formal proofs / regression. Agents read those via the `.ai/` convention; commit &
  module examples in the kit docs are from venezia-fpga and are illustrative.

## Tool path note
`bug-class-router.py` / `pre-merge-check.py` operate on the design git tree — invoke from within it
(`cd db/design && python ~/.claude/agent-kit/bug-class-router.py --commit <hash>`). `boundary-classifier.py` and
the others are co-located in `agent-kit/` so their cross-calls resolve.
