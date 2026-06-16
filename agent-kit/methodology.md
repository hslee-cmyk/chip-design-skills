> **Generic reference** — deployed to `~/.claude/agent-kit/` by chip-design-skills/install.py.
> The class structure / templates are universal; commit & module examples are from venezia-fpga
> and are illustrative.

# AI Verilog Coding Methodology — why LLMs mis-code RTL, and how to build agents that don't

> Synthesis of a design discussion + de-risking experiments (2026-06). Source data: the
> `claude-implemented-version → master` diff in `db/design` (57 human-correction commits on an
> AI-implemented feature). Companion artifacts:
> - Forensics: [`../analysis/claude-diff/`](../analysis/claude-diff/) (taxonomy T1–T9, evidence, report)
> - Experiments: [`../experiments/formal-demo/`](../experiments/formal-demo/) (boundary detector + formal)
> - Agents: [`../agent-proposals/`](../agent-proposals/) (architect-advisor, coder, reviewer, classifier)

## 0. The question

The first-generation agents we built (`verilog-rtl-coder`, `verilog-rtl-reviewer`) are good at procedural
languages (C/Python, where file order = execution order) but weak at Verilog, where **concurrency must be
guaranteed and textual order ≠ execution order**. The diagnosis from the user:

> The AI greps a fragment, understands only that fragment, fixes only that fragment — so it loses the whole-design
> context and idea. And it decides "new FSM vs new state within the existing FSM" too ad-hoc, because it judges
> from a local view. For a hardware-description language this is deeply inefficient.

This document records why that is true, what fixes it, and the experiments that validated the fix.

## 1. The forensic root cause (what the AI actually got wrong)

From the 57-commit diff (full taxonomy in `../analysis/claude-diff/failure-taxonomy.md`):

**Single root cause:** the LLM reasons about RTL as *sequential software at source-text scope*, losing (a) the
implicit 1-cycle register delay and (b) the elaboration/netlist scope of a real design. Distribution:
PROTOCOL_SPEC 18 · STRUCTURE_STYLE 7 · FSM_CORNER_DEADLOCK 6 · POINTER_HANDSHAKE 5 · TIMING_CYCLE 5 ·
CLOCK_RESET_CDC 4 · PORT_INTEGRATION 3. ~half of the 36 distinct bugs are STATIC-catchable, ~half SIM-only.

## 2. The methodology critique (the deeper why)

- **The real villain is not `grep` — it is *text as the comprehension primitive*.** RTL correctness lives in a
  *structural/temporal* representation (netlist graph, timing diagram, FSM interaction), not in line order. An
  expert re-represents text → parallel structure and reasons there. "Read more of the file" is still sequential
  text; the fix is reasoning in a *non-textual parallel representation*, treating text as its serialization.
  `grep` is right for *mechanical* checks (lint signatures); it is wrong as the *comprehension primitive for
  design/architecture* decisions. The error is **altitude mismatch**: a locality tool applied to a globality
  question.

- **"New FSM vs new state" is an architectural decision** that needs the whole concurrent datapath + all FSMs +
  clock domains in view — and (here) the *chip* side, since `db/design` is a shared submodule. The diff proves
  it: humans spun up a **separate FIFO-read FSM + module** (`3f979ac`) because FIFO-read/squash is an independent
  concurrent thread from token transmission — a re-architecture the locally-patching AI never considered.

- **Part of the deficit is capability, not just context.** Autoregressive generation is itself a sequential
  prior fighting parallel semantics. So even with perfect context the generator makes blocking/non-blocking and
  order≠execution errors. ⇒ lint/elaboration/formal/sim gates are **load-bearing**, not optional: the structural
  model reduces *architecture* errors (before generation); the gates catch the *concurrency residual* (after).

- **`grep`-driven comprehension is the upstream cause that *generates* the symptom classes** (T1 protocol, T2
  integration, T5 FSM-corner all partly stem from not holding the whole concurrent design in view).

- **The partitioning decision crystallizes at PLAN altitude, not at code altitude — and that is where the
  re-occurrence happened.** The boundary gate (§4) was positioned at commit/implementation time, but a plan
  fixes the partition in *prose* ("add `TRF_FIFO_CHECK`/`TRF_PENDING` states to FSM2") long before any RTL diff
  exists. Forensic: `sync-xfr-extension.plan.md` folded a BTNOP timer (lives across many COLA transfers) and a
  FIFO pre-fetch/hold (producer/consumer decoupling) into FSM2 as new states, justifying it **only** on
  within-FSM combinational depth (§3.4 "상태 분리 근거") and never asking the concurrency/lifetime question —
  the exact code-time failure (`3f979ac` separate FIFO-read FSM), reproduced one altitude up. The plan carried
  *zero* "Alternatives considered" and produced *no* ADR, even though `adr-template.md` already encodes the
  deciding question ("Must run concurrently with the existing FSM?"). ⇒ Two fixes: (1) run the computed
  boundary detection at PLAN altitude (architect-advisor Mode P), and (2) make a **responsibility
  decomposition by concurrency/lifetime** the *forcing first step* — the default partition flips to a separate
  FSM when a responsibility runs concurrently at a different lifetime/rate; folding into a host state must be
  justified *against* that default, not assumed. Single-hypothesis anchoring (a plan with no alternatives) is
  itself an escalation trigger. The knowledge was already captured here; the gap was gate *placement* + a
  forcing function, not missing knowledge.

## 3. The decision: (B) Constrain & Escalate + externalize intent as formal

Two philosophies were weighed:

| | (A) Empower | (B) Constrain & Escalate — **CHOSEN** |
|---|---|---|
| Strategy | give the agent the model+rubric to decide architecture well | forbid the agent from architecture decisions; its skill is to *detect* the boundary and *escalate* with options |
| Answer to "ad-hoc" | a better rubric | **make it not decide alone** |

And: **the only edit-surviving form of design intent is a machine-checkable property (SVA/formal).** Comments
and analysis docs the agent greps around; a formal property it *cannot* bypass. The project has SymbiYosys.

**Organizing principle:** the agent's job is not to author RTL text — it is to keep three representations in
sync and refuse to desync them without authorization:
- **Structure** (machine: netlist / Yosys) — concurrency-native, order-independent.
- **Intent** (formal: SVA/properties) — the only enforced, edit-surviving layer.
- **Rationale** (semantic: `graphify-out/`, ADRs, analysis docs) — the *idea*; partially exists already.

The original bug = the AI edited a 4th, throwaway view (text) while the other three stayed empty/stale.
**Escalation is not overhead — it manufactures the missing Intent/Rationale layer** (each architectural decision
produces an ADR + a guarding SVA), so the agent compounds *out of* ad-hoc-ness over time.

## 4. The crux: architectural detection is COMPUTED, not judged

The technical heart of (B): the agent never *judges* "new FSM vs new state." It **declares its intended
structural delta** (which always/net/FSM/clock/instance changes) and a **mechanical diff against the elaborated
baseline** classifies it. Any change to {FSM count, net driver-map, clock-domain crossing, module instances,
case-arms, handshake} → auto-escalate. Bias to over-escalate (false positives cheap; false negatives dangerous).
The same model-diff is both the *classifier* (before) and a *guardrail* (after: catches unintended architectural
drift). Implemented in `../agent-proposals/boundary-classifier.py`.

## 5. Experiments — de-risking the two crux assumptions

### 5a. Boundary detector (validated, refined)
Ran the structural-delta classifier over all 57 commits.
- **Validated:** `3f979ac` (new FIFO FSM) tops at score 70; genuine FSM-structure changes next; pure-local fixes
  (typos, literals, off-by-one, pointer formula) at 0.
- **Two gaps found & fixed:** (1) clock/reset *connection* re-wire (caught `86a1796` gated-clock, was missed);
  (2) structural *removal* counting (caught `5b61531` removing an FSM case-arm, was missed). Both now ARCH.
- **Orthogonality confirmed:** the marquee *correctness* bugs (`2ebd51f` deadlock, `b353ad3` CDC, `de8b9d0`
  inheritance, `86a1796` logic) are mostly structurally **LOCAL** — the humans decided the architecture **once**
  (`3f979ac`) then spent ~40 commits fixing local-but-wrong logic. ⇒ boundary detector guards a *rare, cheap*
  gate; the *high-volume* correctness pain is formal/SVA's job.

### 5b. Formal feasibility on REAL RTL (validated — GO)
`../experiments/formal-demo/`. Toy reproducer first (count==0 deadlock: buggy FAIL w/ `load_val=0`, fixed PASS),
then the **real `ext_backTelInterface`**:
- **Make-or-break answered YES:** real RTL (+ deps `ext_fifo`, `ext_if_cdc`) elaborates under sby with **zero
  black-box stubs, zero source edits** (only `-DTp=1`). BMC sub-second.
- **Proven on the real module:** intent property "after a squash-mode `exec_pulse`, `o_timer_active` must read
  high for all timer values" → `bt_fixed` PASS, `bt_buggy` (2ebd51f reverted) FAIL, **solver autonomously chose
  `tval=0`** — the exact historical corner.
- **Friction (the real cost):** (1) clock collapse (3 clks → 1; gives up CDC-*timing* bugs — harder tier);
  (2) every input must be driven (unconnected = free var = unsound); (3) **must model the enabling protocol** —
  the timer only arms after a `pcmReg_wr_en` config-write propagates through `ext_if_cdc`; my *first* harness
  poked the timer pin without configuring the module → both tasks failed. **This closes the loop: formal itself
  depends on whole-module comprehension; a grep-fragment agent produces exactly my first (broken) harness.**

### 5c. Formal's boundary — E1 dead-branch is protocol-relational (formal-HARD)
Tried to prove the AI's `STREAM_WRITE`-under-`START_DET` dead branch (`5b61531`) unreachable on the real
`ext_i2cSerialInterface`. Deep BMC (140) **FAILED** — with `i_startStopDetState` *free*, the solver reached the
violation using an **illegal input value (`2'd3`)** and arbitrary `START` glitching. So the deadness is
**protocol-relational** (needs the detector's contract: legal values + START-held-until-STOP), NOT a
self-contained FSM invariant like the timer. **Open question surfaced:** `r_streamRwState` is only reset to
`STREAM_DEV` at async-reset (no in-FSM reset found) → it may carry over across transactions, so the AI branch
might be reachable even *with* a perfect detector contract — worth re-checking the human's `5b61531` reasoning.

## 6. The core design output — a bug-class ROUTER

Formal is a *targeted tool*, not a hammer. Route each AI-failure class to its cheapest reliable verifier
(empirically grounded):

| Class | Cheapest reliable verifier | Evidence |
|---|---|---|
| self-contained logic/timing (deadlock, off-by-one, in-block pointer) | **FORMAL (sby)** | timer: proven on real RTL |
| protocol-relational dead-code / reachability | **STATIC reachability** (reviewer S12); formal needs env-contract (costly) | E1: free-input deep BMC FAIL |
| architectural partitioning (new FSM vs state) | **STATIC structural-delta** (architect-advisor) → escalate | boundary detector validated |
| cross-domain (CDC) timing | **multiclock formal** (TPL-7, proven in `cdc_demo`) or **directed sim** (cloud0/xcelium-mcp) | real deadlock is cross-domain; multiclock exposes count==0 pulse-loss |
| integration / fan-out / lint / RAM-inference | **STATIC** (reviewer S1–S13) | T2/T7/T8 all static |

## 7. Agent architecture (3 agents + router + human)

- **Architect-advisor** (opus, read-only) — runs the structural-delta classifier; ARCH → escalate ADR with
  options; routes by §6. Does NOT implement or decide partitioning. → `../agent-proposals/verilog-rtl-architect-advisor.md`
- **Implementer** (sonnet, constrained) — implements *within* a ratified micro-architecture + property set; the
  model-diff gate blocks unintended architectural drift. (revision of `verilog-rtl-coder`)
- **Prover** (opus, adversarial) — writes intent properties *independently* of the implementation (anti-tautology)
  and runs sby; for a bugfix, writes the property that FAILS on the current bug first. Harness templates in
  `../experiments/formal-demo/`. Its hard part is modeling the module's enabling protocol (needs comprehension).
- **Human** — architect / ratifier: picks partitioning, ratifies properties.

Anti-tautology rule: the Implementer must never self-certify intent (it would write a property restating its
bug). Assurance comes from independently-authored properties — hence the separate Prover.

Anti-circularity rule (spec-level — sibling of anti-tautology): expression-level anti-tautology is *necessary
but not sufficient*. A property that is independent of the implementation can still encode the **wrong intent**.
A FAIL on the **current (shipping) RTL** is ambiguous — (H1) RTL bug vs (H2) wrong-spec property — and the
"FAIL→PASS after my fix" transition is sound **only when one side is a known-good reference** (answer key /
human-fixed commit, e.g. the `2ebd51f` revert). For a novel hypothesis on shipping RTL with no answer key, the
Prover must derive intent from the **consumer's observed contract** (not the signal name or a code smell),
verify the **fix preserves that intent**, and otherwise **escalate the H1/H2 ambiguity** rather than declare a
bug. Forensic: BUG-001 (`r_i2c_stop` level-vs-pulse false positive) — see `verilog-rtl-prover.md` §1b.

## 8. Build plan & status — (A) → (C) → (B)

- **(A) Architect-advisor — ✅ DONE.** Refined boundary detector (`boundary-classifier.py`), 2 gaps fixed
  (clock-rewire, removal counting), re-validated on 57 commits; agent doc written. Remaining (minor): ADR
  template, wire into a pre-merge step.
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
- **Remaining (future):** wire the pre-merge gate into CI; activate agents in `.claude/agents/`; upstream the
  skill patch to chip-design-skills; the `r_streamRwState` carryover question (§9).

## 9. Open questions / honest limits
- `r_streamRwState` cross-transaction carryover (§5c) — may be a real reachability issue in `ext_i2cSerialInterface`.
- CDC-timing tier — the *real* deadlock is cross-domain (refClk **10MHz** → cellClk **2MHz**, 5:1 fast→slow).
  Multiclock formal proves the GENERAL rule "source held ≥2 dest cycles" (`cdc_demo`: a 1-tick pulse is lost).
  **RESOLVED for this design: the `2ebd51f` fix is CDC-SAFE.** The fix holds `active` for a full prescaler dwell
  (~97 refClk ≈ 9.9µs ≈ **~20 cellClk cycles**) even for count==0 — well above the ~2 cellClk (1µs) a 2-FF needs.
  Confirmed by the faithful 5:1 model `cdc_ratio` (hold1=1-tick **FAIL** / hold_real=dwell **PASS**, any phase).
  **Lesson:** plug the *real* min-dwell + real frequencies into the model — `cdc_demo`'s 1-tick abstraction
  over-stated the risk; reading the actual RTL timing (prescaler) + the actual clocks gave the true verdict.
- Escalation fatigue — 23/57 ARCH is intentionally over-flagged; use score tiering (major ≥20 vs minor ≤3) and
  let the compounding ADR corpus narrow it over time.
- yosys built-in frontend rejects full SVA `assert property (@(posedge clk)...)`; use immediate `assert` +
  `anyconst`. (Verific would accept full SVA but isn't in this OSS build.)

## 10. Falsifiability
Every claim here is testable against the 57-commit ground truth. The standing regression for the agents:
run the architect-advisor on the `claude-implemented-version` tree + the feature request and confirm it escalates
the FIFO-FSM partitioning (`3f979ac`); run the Prover and confirm it emits the count==0 property catching
`2ebd51f`. We have the answer key.

**Plan-altitude regression (added — same failure, one altitude up).** Run the architect-advisor in **Mode P**
on `sync-xfr-extension.plan.md` (the prose, no RTL yet). It MUST: (a) extract the declared structural delta
(new states `TRF_FIFO_CHECK`/`TRF_PENDING` in FSM2) → ARCH; (b) fill the §2.0 responsibility-decomposition
table and flag the BTNOP timer (cross-iteration lifetime) + FIFO pre-fetch/hold (producer/consumer) as
concurrent/different-lifetime; (c) by DEFAULT-FLIP, emit a **separate FIFO/timer-management FSM as candidate
A** in the ADR; (d) flag the missing "Alternatives considered" section as a single-hypothesis-anchoring
escalation. FAIL = silently adopting the FSM2 state-fold without surfacing the separate-FSM option. This is
the plan-time twin of the `3f979ac` code-time answer key.
