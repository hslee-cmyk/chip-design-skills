# agent-kit 구축 이력 (RTL agent·도구)

> 구 `agent-kit/methodology.md` §8(Build plan & status)을 그대로 옮긴 **이력 문서**다(2026-11-11, plan
> `agent-kit-routing-canon` FR-03). 방법론 지식의 정본은 ai-memory `memory/rtl/methodology.md`이고, 이 문서의
> 상태 표기는 2026-06 시점 기록이다. 이후 변경:
> - 2026-11-11: `bug-class-router.py` 삭제 — 라우팅 정본은 ai-memory `failure-taxonomy.md` Routing 절(FR-06).
> - 2026-11-11: failure-taxonomy·methodology·evidence·property-library 정본 → ai-memory,
>   `~/.claude/agent-kit/`에는 ai-memory 배포본(FR-01~04).
> - 아래 본문의 `run_regression.py`·`adr/0001-…`·`cdc_demo` 등은 venezia `.ai/experiments/`·`.ai/adr/`에 있다.

## 8. Build plan & status — (A) → (C) → (B)

- **(A) Architect-advisor — ✅ DONE.** Refined boundary detector (`boundary-classifier.py`), 2 gaps fixed
  (clock-rewire, removal counting), re-validated on 57 commits; agent doc written. (ADR template + pre-merge
  gate landed — see the live-regression bullet below.)
- **(C) Router — ✅ DONE.** `bug-class-router.py` (T1–T9 + ARCH/IFACE/LOCAL + CDC→SIM → route + owner, verified
  runnable); `verilog-rtl-coder` → constrained Implementer (model-diff gate A0, anti-tautology); reviewer →
  explicit per-R# routing + S12 ownership; new `verilog-rtl-prover`. Consistency-critiqued (all fixes applied;
  4 frontmatters valid YAML).
- **(B) Prover — ✅ DONE.** `harness_builder.py` (auto-generates the sby harness skeleton: ties off every input,
  collapses clocks, instantiates all ports, flags enable/config inputs; generated skeleton elaborates clean on
  `ext_backTelInterface`) + `property-library.md` (TPL-1..7 yosys-tested templates: observability/no-deadlock,
  bounded-response, sync-read, pointer cover, FSM-safety, dead-code, **CDC-timing multiclock**). Prover de-stubbed.
- **Architect-advisor finished + live regression — ✅ DONE.** `pre-merge-check.py` (ARCH→BLOCK gate) + `adr-template.md`
  + worked example `adr/0001-forward-fifo-read-fsm.md`; `run_regression.py` → **17/17 PASS** vs the answer key.
- **CDC-timing multiclock tier — ✅ DONE.** `cdc_demo.v`/`cdc.sby` proves the residual hazard (§9).
- **Plan-altitude gate + anti-overfit — ✅ DONE.** architect-advisor **Mode P** runs the boundary detector on a
  prose plan *before ratification* (partitioning crystallizes in prose, upstream of every RTL gate — §2) +
  forcing **§2.0 responsibility-decomposition** (DEFAULT-FLIP: a concurrent / different-lifetime responsibility
  ⇒ a separate FSM is the default; folding into a host state must be justified against it). `boundary-classifier.py`
  gained a name-INDEPENDENT **FOLD** signal (`+STATE/+ARM` with no `+MOD/+INST` = a thread folded into a host
  FSM) replacing an earlier name-regex heuristic. Rubric **R13** (criteria stated structurally — example-as-
  evidence, not example-as-rule) added to `AGENT_BEST_PRACTICES.md` + JUDGE prompt; plan-time regression added (§10).
- **Agents activated + deployed — ✅ DONE.** The 4 agents live in this `chip-design-skills` repo (the upstream)
  and install to `~/.claude/agents/` (global) or a project's `.claude/agents/` via `install.py --project`
  (bkit precedence: project overrides global); agent-kit deploys to `~/.claude/agent-kit/`.
- **Remaining (future):** wire the pre-merge gate into CI; the `r_streamRwState` carryover question (§9).
