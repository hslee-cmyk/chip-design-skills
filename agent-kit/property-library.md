# Prover Property Library

Reusable, yosys-tested intent-property templates for the **verilog-rtl-prover**. Each is keyed to a bug
class the Prover OWNS (T4/T5/T6 + FSM safety). Grounded in the validated experiments in
[`../experiments/formal-demo/`](../experiments/formal-demo/).

## How the Prover uses this
1. **Build the harness** with [`harness_builder.py`](./harness_builder.py) (ties off every input, collapses
   clocks, instantiates all ports) → fill **TODO 1 (enabling protocol)** and **TODO 2 (intent property)**.
2. **Pick a template below** by the bug class ([`bug-class-router.py`](./bug-class-router.py)).
3. **FAIL-first**: confirm the property FAILS on the current bug, then PASSes after the fix (the timer demo:
   `bt_buggy` FAIL / `bt_fixed` PASS, solver picks the corner).
4. **Anti-tautology**: the property must encode the *spec intent*, never restate the implementation. Author it
   from the spec / consumer's expectation, independently of the code under test.

### yosys constraints (learned)
- yosys built-in frontend **rejects** `assert property (@(posedge clk) ...)` → use **immediate `assert` in a
  clocked block** + `(* anyconst *)` scenario constants.
- **Drive every input** (unconnected = free var = unsound). **Model the enabling protocol** (a fragment harness
  that skips it FAILS — both buggy and fixed).
- **Include transitive deps** (instantiated modules) or the proof is unsound.
- `(* anyconst *)` lets the solver pick the corner (timer demo: it chose `tval=0` / `load_val=0` unaided).

---

## TPL-1 · Observability / no-deadlock (T5 FSM-corner) — `mode bmc`
**When:** a consumer FSM waits to *observe* something (an `active`/`done`/`valid` from another engine) after a
trigger; a degenerate input (`count==0`) could make it never assert → hang. The biggest, proven class.

```verilog
// "the cycle after a (qualified) trigger, the observable must be high — for ALL values"
reg start_d;
always @(posedge clk or negedge rst_n)
    if (!rst_n) start_d <= 1'b0; else start_d <= trigger_qualified;  // trigger in the right state/mode
always @(posedge clk)
    if (rst_n) assert (!start_d || observable);   // e.g. observable = o_timer_active
```
**Exemplars:** toy `fsm_timer_demo.v`/`demo.sby` (`load_val=0` CEX); **real** `ftb.v`/`bt.sby` on
`ext_backTelInterface` (`bt_buggy` FAIL @ `tval=0`, `bt_fixed` PASS). **Limit:** single-clock; the real bug's
cross-domain 2-FF path is abstracted (→ directed sim for the CDC-timing tier).

## TPL-2 · Bounded-time response (T5 / T4 hang) — `mode bmc`
**When:** "every `req` must get `ack` within N cycles" (timeouts, no-livelock). A watchdog monitor, depth ≥ N+δ.

```verilog
reg waiting; reg [7:0] wd;
always @(posedge clk or negedge rst_n)
    if (!rst_n) begin waiting <= 0; wd <= 0; end
    else begin
        if (req && !waiting) begin waiting <= 1; wd <= 8'd0; end
        else if (waiting && ack) waiting <= 0;
        else if (waiting) wd <= wd + 8'd1;
    end
always @(posedge clk) if (rst_n) assert (!(waiting && wd > 8'dN));  // never wait > N
```
**Tip:** constrain data inputs small (`anyconst` range) so N stays BMC-tractable (a 100-tick prescaler ×255 count
is infeasible at full depth — prove the *observability* (TPL-1) instead of the full duration).

## TPL-3 · Synchronous-read latency (T4) — `mode bmc`
**When:** read data must NOT be sampled the same cycle as `rd_en`; popped word must stay stable while consumed.

```verilog
// (a) registered-read latency: data not valid until the cycle AFTER rd_en
reg rd_en_d;
always @(posedge clk or negedge rst_n) if(!rst_n) rd_en_d<=0; else rd_en_d<=rd_en;
always @(posedge clk) if (rst_n) assert (!rd_en || !data_consumed_this_cycle);  // no same-cycle consume
// (b) holding-register stability: latched word unchanged across the consume window
always @(posedge clk) if (rst_n && consuming) assert (r_hold == $past(r_hold));  // $past needs -formal
```
**Exemplar mapping:** `ext_askEncoder` sampled `w_fifoDataPacket` the cycle after `c_fifoRdEn` and drove the
multi-cycle mux from the live FIFO output (05a53c5/daad643/f77e3c9). **Limit:** cross-block/CDC read latency →
directed sim (variable latency, not single-clock-provable).

## TPL-4 · Circular-FIFO pointer (T6) — `mode bmc` + `mode cover`
**When:** wrap/full/single-entry boundary correctness of a pointer comparison; no overflow.

```verilog
// safety: never write when full / read when empty
always @(posedge clk) if (rst_n) assert (!(wr_en && full));
always @(posedge clk) if (rst_n) assert (!(rd_en && empty));
// reachability of the dangerous boundary (cover proves the test is exercised)
// (as a separate `mode cover` task)
// cover (full && wr_ptr==0);                  // wr-wraps-to-0 / FIFO-full corner
// cover (occupancy==1 && nxt_valid==1'b0);    // single-entry lookahead is correctly false
```
**Exemplar:** `ext_fwd_fifo` next-packet lookahead `(r_rd_ptr+1) > r_wr_ptr` at native width
(737070b/06f19b0; the `(rd+1)<=(wr-1)` rewrite was later proven flawed — the sound property is occupancy
`o_fifo_counter>=2`, venezia BUG-002). reviewer co-flags the missing `{1'b0,..}` zero-extend as a STATIC smell (R4); the Prover owns
the boundary proof.

## TPL-5 · FSM safety invariants — `mode prove` (k-induction)
**When:** one-hot integrity / no illegal state, as an *unbounded* proof.

```verilog
always @(posedge clk) if (rst_n) assert ($onehot(r_state) || r_state == RESET_STATE);
always @(posedge clk) if (rst_n) assert (r_state != ILLEGAL);   // default/illegal unreachable
```
**Note:** `mode prove` may report the property true-but-not-inductive (a spurious step-CEX from an unreachable
start state) → strengthen with helper invariants. Basecase = BMC from reset.

## TPL-6 · Dead-code / unreachability (T1) — ⚠️ formal-HARD, prefer reviewer STATIC
**When:** "this case-arm under this state guard is unreachable" (an AI-invented corner). **The Prover usually
does NOT own this** — it is *protocol-relational* and needs an environment contract.

```verilog
// assert (!(loopState==CHK_ADR && i_startStopDetState==START_DET) || r_streamRwState==STREAM_DEV);
```
**Experiment (E1, `i2c.sby`/`i2c_inv.v`):** with `i_startStopDetState` FREE, deep BMC(140) **FAILED** — the
solver used an *illegal* input value (`2'd3`) and arbitrary START glitching. Proving it needs the detector's
contract (legal values + START-held-until-STOP) modeled as assumptions — costly. **Route to reviewer S12
(STATIC reachability)** unless an environment model is justified. Open: `r_streamRwState` cross-transaction
carryover may make it genuinely reachable.

## TPL-7 · CDC-timing pulse-loss (multiclock) — `mode bmc` — ⚠️ HARD tier
**When:** a source-domain pulse/level crosses to another clock domain via a 2-FF synchronizer; a short
(1-cycle) source pulse may be **lost** if the destination is comparably slow. The tier single-clock collapse
HIDES. The Prover owns this **only when a multiclock harness is justified**; else → directed sim.

**Model two domains as clock-ENABLES on one global clk** (robust; avoids sby `multiclock`-mode quirks):
```verilog
(* anyseq *) reg fast_en, slow_en;          // domain clock-enables — solver picks phase & ratio
reg [3:0] wdf, wds;                          // fairness: neither clock may stall
always @(posedge clk or negedge rst_n)
  if(!rst_n) begin wdf<=0; wds<=0; end
  else begin wdf<=fast_en?4'd0:wdf+4'd1; wds<=slow_en?4'd0:wds+4'd1; end
always @(posedge clk) if(rst_n) begin assume(wdf<=W); assume(wds<=W); end
// source logic gated by `fast_en`; 2-FF sync + consumer gated by `slow_en`; track `started`/`seen`
always @(posedge clk) if(rst_n && g==DEADLINE) assert (!started || seen);   // event never lost
```
**Exemplar:** `cdc_demo.v` / `cdc.sby` — `count0` (1-tick active, the 2ebd51f FIX) **FAIL** (solver phases
`slow_en` to miss the g=7-8 active window), `count_big` (held ≥8 ticks) **PASS**. This is the formal PROOF of
the skill's CDC rule (**"source held ≥2 destination cycles"**) and exposes the residual count==0 hazard TPL-1
cannot see. **Fix direction:** pulse-stretch (min active ≥2 dest cycles) / handshake / toggle CDC, or guarantee
dest ≥ ~2× source. **Cost:** needs fairness `W` + a `DEADLINE`; constrain `fire`/`load_val` per task for BMC
tractability (unconstrained `fire` → spurious FAIL).
⚠️ **Faithfulness:** plug the *real* minimum source-hold + *real* clock ratio into the model — an abstracted
1-tick pulse over-states risk. Ex: the `ext_backTelInterface` timer dwells a full prescaler period (~97 refClk)
even for count==0, so at 10MHz:2MHz it is SAFE (`cdc_ratio.sby`: `hold1` FAIL vs `hold_real` PASS, ~10× margin).

---

## sby mode cheat-sheet
| mode | proves | use for |
|---|---|---|
| `bmc` (depth N) | no violation within N cycles (bounded) | TPL-1/2/3/4 — find the CEX corner; bound the scenario |
| `prove` (k-induction) | unbounded safety invariant | TPL-5 — one-hot / no-illegal-state |
| `cover` | a state/branch IS reachable; if unreached → dead | TPL-4 boundary exercised; dead-branch evidence |

## Honest limits
- **State explosion** → bound the scenario (`anyconst` small ranges) or split; fall back to directed sim.
- **CDC-timing** = multiclock (hardest tier) → **multiclock formal (TPL-7, proven in `cdc_demo`)** when a
  fairness harness is justified, else directed sim (cloud0/xcelium-mcp). NOT single-clock formal.
- **Protocol-relational** (TPL-6) needs env-contract → usually reviewer STATIC, not Prover.
