# ADR-NNNN: \<decision title\>

> Architecture Decision Record. Produced by **verilog-rtl-architect-advisor** when a change classifies
> **ARCH** (`boundary-classifier.py`). The agent fills the candidates + analysis; the **HUMAN ratifies** the
> chosen option. Once ratified, this ADR + its guarding property become **intent assets** the next agent reads
> (so escalation *manufactures* the missing intent layer — methodology §3). Store under `.ai/adr/`.

- **Status:** PROPOSED | RATIFIED | SUPERSEDED
- **Date:** \<YYYY-MM-DD\>
- **Trigger:** \<feature/edit that crossed the boundary\>
- **Structural delta:** \<boundary-classifier signal, e.g. `+ALW=5 +STATE=17 +INST=5` → ARCH score 47\>

## Context
\<The concurrent threads / clock domains / FSMs involved, and why a *partitioning* decision is needed.
Cite the whole-design model — `graphify-out/` community, `.ai/analysis/{module}.analysis.md`, clocks. This is
exactly the context a grep-fragment view loses.\>

## Responsibility decomposition  (FILL FIRST — this *drives* the candidates; advisor §2.0)
List each responsibility the change introduces, *before* deciding where state lives. host FSM = the existing
FSM a fold would target.

| Responsibility | lifetime/rate vs host FSM | concurrent with host? | producer/consumer decoupling? | independent reset/idle? |
|---|---|---|---|---|
| \<e.g. BTNOP timer countdown\> | \<spans many host iterations\> | \<yes\> | \<—\> | \<yes\> |
| \<e.g. next-packet pre-fetch & hold\> | \<async (FIFO fill rate)\> | \<yes\> | \<yes (FIFO→FSM)\> | \<—\> |

**DEFAULT-FLIP rule:** if any responsibility runs concurrently at a different lifetime/rate (cross-iteration
timer/counter · producer/consumer decoupling · a **wait-only state** that just stalls the host FSM until an
external time/event) → the DEFAULT is a **separate FSM/module (Option A below)**; folding into a host state
(Option B) must be justified *against* that default. Combinational depth is a 2nd-order concern *after* the
fold axis is chosen — never the 1st-order reason to fold.

## Candidate partitionings
### Option A — \<separate FSM + module + interconnect — the DEFAULT when a concurrent/diff-lifetime responsibility exists\>
- **Structural delta:** \<which FSMs / modules / nets / clocks change\>
### Option B — \<new state(s) in the existing FSM — must be justified against Option A, not assumed\>
- **Structural delta:** \<…\>

## Decision rubric  (answer from the WHOLE-design model — not a fragment)
| Factor | Option A | Option B |
|---|---|---|
| Different clock domain / gating? | | |
| Must run **concurrently** with the existing FSM (independent thread-of-control)? | | |
| Combinational-depth / timing budget if folded into an existing state | | |
| Resource sharing vs independence (reuse, area) | | |
| Verifiability / observability (separate FSM = separately coverable) | | |
| **Shared submodule** (`db/design` ↔ chip): ASIC area / timing-closure / DFT impact | | |
| Design history (past timing-closure or bugfix precedent) | | |

## Recommendation
\<Agent's recommended option + the rubric reasoning.\> — **the HUMAN decides; the agent does not.**

## Guarding property (ratified intent → Prover)
\<The machine-checkable property the chosen architecture must preserve. This is the edit-surviving intent the
next agent cannot grep around.\> Template: [→property-library.md] · proved by [→verilog-rtl-prover].

## Consequences / follow-ups
\<What the Implementer may now do within this ratified micro-architecture; required directed tests; what is
explicitly out of scope.\>

## References
\<analysis docs · prior `db/design` commits · `graphify-out/` community · related ADRs\>
