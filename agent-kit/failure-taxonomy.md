> **Generic reference** — deployed to `~/.claude/agent-kit/` by chip-design-skills/install.py.
> The class structure / templates are universal; commit & module examples are from venezia-fpga
> and are illustrative.

# AI Verilog Failure Taxonomy

Derived from the `claude-implemented-version` → `master` diff (57 commits, 36 distinct root-cause mistakes).
This is the **canonical reference** cited by `verilog-rtl-reviewer` and `verilog-rtl-coder`. Each class lists
*why an LLM is structurally prone to it*, the *diff signature* to recognize it, and whether it is
**STATIC** (provable by reading/lint/elaboration) or **SIM** (provable only by simulation/timing).

## Quantified distribution (57 commits)

| Category | Commits | Distinct bugs | Severity | Detect |
|---|---:|---:|---|---|
| PROTOCOL_SPEC | 18 | ~10 | critical | mixed |
| STRUCTURE_STYLE | 7 | ~3 | medium | **STATIC** |
| FSM_CORNER_DEADLOCK | 6 | ~6 | high | SIM |
| POINTER_HANDSHAKE | 5 | ~5 | high | SIM (static smell) |
| TIMING_CYCLE | 5 | ~5 | high | SIM |
| CLOCK_RESET_CDC | 4 | ~4 | critical | **STATIC** (provenance) / SIM (symptom) |
| PORT_INTEGRATION | 3 | ~9¹ | critical | **STATIC** |
| WIDTH_TRUNCATION | 0² | ~2 | low | **STATIC** |
| CLEANUP / MERGE | 9 | — | — | — |

¹ Integration mistakes are spread across many commits; counted ~9 distinct in the module findings.
² Width bugs never appeared as a *primary* fix — they were bundled inside FSM/protocol commits (one-hot 9→10,
3→4) and the `c_pktData[17]` / `FIFO_MAX_PTR` cases.

---

## T1 · PROTOCOL_SPEC — inventing or mutating protocol state instead of obeying it
**Severity critical · Detect: mixed**

**Why LLM fails:** treats protocol-state signals (START/STOP detect, addressing-vs-legacy, param-vs-config
inheritance) as ordinary scratch flags it may set to force the FSM, rather than observations of an external bus
event it must passively honor. Reasons packet-locally (misses inter-packet inheritance) and over-engineers
happy-path corners by mutating state it does not physically drive.

**Signature:** a combinational `assign`/`c_` that CLEARS or OVERRIDES a signal whose name implies a detected
bus event (`*StartStopDet`, `*_detected`, `*_valid` from another block); a case branch handling a substate that
the enclosing guard makes unreachable (dead code); a register address/field derived from a byte without
switching on the mode bit that defines that byte's meaning; selection computed from only the current packet.

**Exemplar:** `ext_i2cSerialInterface.v` — `c_clearStartStopDet=1` in `STREAM_DEV→STREAM_REG` + invented
`STREAM_WRITE` repeated-START branch under a `START_DET`-only `CHK_ADR` block → dead code + read-byte-as-data
corruption; reverted in `5b61531`.

**Prevention rules:**
- Never assert a clear/override on a signal that latches a real bus/protocol event; advance the FSM only on the
  observed event itself.
- For any byte whose meaning depends on a mode bit, EVERY decode branch must switch on that mode bit; never
  extract a register address from a device-select byte in addressing mode.
- When parameters inherit across a packet stream, derive selection from BOTH current-packet fields AND retained
  previous-packet mode (`c_target_is_config = ~r_pcmParamMode & packet[17]`).
- Flag any `state==X` branch handling a substate that can only occur under `state!=X` as unreachable/dead.
- When adding a streaming/FIFO map entry, mirror the existing analogous interface, don't invent a write-strobe.

---

## T2 · PORT_INTEGRATION — "declared somewhere" ≠ "wired end-to-end & bidirectional"
**Severity critical · Detect: STATIC**

**Why LLM fails:** equates "I declared/used this" with "threaded through every hierarchy level, the build
manifest, and both read & write directions." Reasons at source-text scope, not elaboration scope: builds a
correct-looking producer and consumer as separate sub-tasks and never closes the loop. Builds the write half a
prompt exercises and omits the symmetric read-back + CDC ack; ties a constant `1'b1` to a functional mode port;
has no concept of a compile filelist or a status flag needing a register-map path in addition to its datapath
consumer.

**Signature:** a new registered output with zero downstream fan-out; a new mode input that only feeds reset/CDC
and selects no datapath signal; a literal `1'b0`/`1'b1` tied to a functional module port; a writable register
entry whose read-back returns hardcoded 0; a new `.v` absent from the filelist; a FIFO/LUT with `wr_*` but no
`rd_*`/`rd_ack`.

**Exemplar:** `ext_backTelInterface.v` — built `r_timer_active` but left `o_backtel_dec_en` on the legacy
condition with ZERO references to the new timer → entire feature dead (`dcfa6d2`/`a3be708`); new `ext_fwd_fifo.v`
missing from `d_filelist.f` (build break, `759af25`/`b26d292`).

**Prevention rules:**
- Every new `.v` file is in the build filelist at its real path; elaboration reports no unresolved instance.
- Every new registered output drives ≥1 consumer (grep); every new mode input changes a datapath signal. Zero
  fan-out = unintegrated feature.
- Reject any constant literal tied to a functional control/mode port — it must trace to a register bit or top pin.
- Every register/I2C-accessible FIFO/LUT implements BOTH write and read paths + the same CDC req→ack the
  analogous existing FIFO uses; every writable entry returns a defined non-zero read-back unless spec'd write-only.
- Every host-polled status flag has a path into the register-map status group, not only its datapath consumer.
- Any new addressing/offset pin is threaded through every hierarchy level (top→main→leaf).
- Open-drain pads: when disabled, drive the release level so the pad floats; never tie an OD output to a data signal.

---

## T3 · CLOCK_RESET_CDC — gated-clock & async-reset provenance
**Severity critical · Detect: STATIC (provenance) / SIM (symptom)**

**Why LLM fails:** treats any net named `*Clk`/`*RefClk` as free-running and clocks logic from it without
tracing the driver to a primary input/PLL/oscillator; cannot see it passes through an ICG and stops in some
modes; assumes "the clock used to transmit is also the right clock to receive." Drives async reset pins from
decoded combinational FSM outputs, conflating "logically correct level" with "glitch-free enough for async reset."

**Signature:** a module `*Clk` port driven by the CKO of an ICG/`BUFGCE`/gated net (suffix `_g`,
`todoc_prim_icg`, `*Gate`) when the sink must run while that gate is closed; an async reset/set pin
(`i_rst_n & ~c_xxx`) driven by an `always @(*)` combinational expression.

**Exemplar:** `ext_d_main.v` — clocked `ext_askDecoder.i_refClk` with `w_askRefClk` (CKO of
`todoc_prim_icg u_askRefClk_icg`, enable from the forward-link gating FSM) → back-tel decode froze exactly when
forward data paused; fixed to ungated `i_refGenClk` in `86a1796`.

**Prevention rules:**
- Before connecting any clock port, trace the driver to a primary input or PLL/oscillator; if it passes through
  a clock gate/ICG, do NOT use it to clock logic that must run while the gate is closed. Receivers/decoders use
  the free-running source clock.
- Async reset/set inputs are driven ONLY by reset-tree or REGISTERED signals; register the decoded clear
  (`r_fifoClr <= c_fifoClr`) before feeding `i_rst_n`.
- Give every cross-mode block its mode-enable/clear inputs so it behaves in all modes.

---

## T4 · TIMING_CYCLE — synchronous-read / cycle-latency (sampling data the same cycle as the enable)
**Severity high · Detect: SIM (static smell)**

**Why LLM fails:** models a FIFO/RAM as a software queue whose `pop()` returns the value "now" and persists; has
no implicit representation of the one-cycle registered-read latency or that the output changes the instant the
read pointer advances. Encodes "a read takes N cycles" as a hard constant rather than a data-valid/ack handshake.

**Signature:** `rd_en` asserted and read data sampled the same/next state with no wait; a multi-cycle consumer
reading combinational FIFO/RAM output directly without latching; a fixed-depth `_d[N]` shift register used as a
read-valid for a source with variable/cross-domain latency.

**Exemplar:** `ext_askEncoder.v` — asserted `c_fifoRdEn` then next state tested `w_fifoDataPacket[18]` and drove
the multi-cycle mux from the combinational output; fixed by latching to `r_fifoDataPacket` (`05a53c5`) + splitting
`FIFO_RD_DATA`/`FIFO_RD_CHK` (`daad643`, `f77e3c9`); i2c used fixed `r_data_rd_en_d[2]` instead of a per-source
ack (`090d3dd`).

**Prevention rules:**
- For any synchronous-read memory/FIFO, never sample read data the same cycle as `rd_en`; insert a registered-read
  wait state; if consumed over multiple cycles, latch into a holding register that stays stable.
- Make `rd_en` a single-cycle pulse (deassert once the registered enable is observed) to avoid double-pop.
- Capture cross-block read data on an explicit data-valid/ack from the source, never a fixed cycle count; a read
  crossing a clock domain needs a CDC-synchronized ack.

---

## T5 · FSM_CORNER_DEADLOCK — happy-path-only FSM; missing async-event & degenerate-input transitions
**Severity high · Detect: SIM**

**Why LLM fails:** builds the FSM around the nominal flow and does not enumerate the *state × async-event* matrix
of THIS design: omits transitions for mid-sequence packet arrival, mode-disable/abort flush, FIFO full/empty,
illegal one-hot state, and the degenerate `count==0` load. When it adds a "wait until done" branch it rarely
reasons about the degenerate input where "done" arrives before a slow-domain synchronizer can observe it →
deadlock.

**Signature:** a wait state blocking on a cross-domain busy/active level with only a mode-disable escape and no
timeout; an expiry compare using `==` (`count==1`) instead of `<=`; a FIFO whose only reset sources are error
conditions (no mode-exit flush); FSM default/illegal states that don't flush/recover; no defer/pending
bookkeeping for a packet arriving while a timer runs.

**Exemplar:** BTNOP timer value of 0 with `r_timer_active <= (val!=8'd0)` + exact `==` expiry never asserted
active across the slow 2-FF synchronizer → read FSM hung forever; fixed to one-tick-active + `<= 1` (`2ebd51f`).

**Prevention rules:**
- Construct a state × async-event matrix (new packet, mode-disable, FIFO empty/full, illegal state, zero-duration
  load) and require an explicit defined transition for every cell.
- Any state waiting on a cross-domain active level must guarantee the level is held ≥2 destination cycles OR add a
  timeout/abort, and must special-case a zero-duration load so it cannot wait forever.
- Use `<=` boundary compares for counter expiry, never exact `==`, so min/zero loads still produce exactly one
  expiry edge; add a directed test with the timer/count value = 0.
- Provide an explicit flush/clear path on mode-exit/abort for every mode-gated buffer; assert it is empty on
  enable-deassert.

---

## T6 · POINTER_HANDSHAKE — circular FIFO pointer arithmetic & read/write handshake
**Severity high · Detect: SIM (static smell on zero-extension)**

**Why LLM fails:** reasons about circular FIFO pointers as plain monotonic linear indices: assumes `wr>rd` always
holds, computes `+1` offsets at native pointer width (so the add wraps mod 2^W), and derives occupancy from a raw
magnitude comparison rather than the occupancy counter. Does not model the wrap boundary where the most lookahead
data exists (FIFO full, `wr==0`).

**Signature:** a comparison like `rd+1 > wr` / `rd+1 < wr` to gate validity; `+1`/`-1` applied to a pointer at its
declared width with no zero-extension; FIFO write-enable asserted with no `~full` guard; a request/sync output
from `count>=threshold` omitting the full flag; same-cycle read+write with no arbitration semaphore.

**Exemplar:** `ext_fwd_fifo.v` lookahead `if((r_rd_ptr+1) > r_wr_ptr)` at native width → off-by-one for a single
entry, wraps at MAX. `737070b`/`06f19b0` rewrote it as `({1'b0,r_rd_ptr}+1) <= ({1'b0,r_wr_ptr}-1)`, but that is
**still a raw-pointer test and was later proven flawed** (FP/FN at the 0-straddle boundary, formal FAIL) — the
correct fix is the occupancy counter `o_fifo_counter >= 2` (venezia BUG-002, 2026-06-15).

**Prevention rules:**
- Derive "has N-ahead entry" from the occupancy counter (`count>=2`), not a raw pointer magnitude test;
  zero-extend any pointer by one bit before adding a comparison offset so the add cannot wrap.
- Explicitly unit-test the single-entry, `ptr==MAX`, and wr-wraps-to-0/FIFO-full boundaries.
- Never assert a FIFO write-enable without ANDing `~full`; surface full/almost-full into any flow-control output.
- Arbitrate same-cycle read vs write with an explicit halt/pass semaphore.

---

## T7 · STRUCTURE_STYLE — non-compiling / structural Verilog
**Severity medium · Detect: STATIC**

**Why LLM fails:** writes loosely-shaped, Python/C-flavored Verilog: treats indentation as scope (newline-separated
second statement looks "inside" the `if`), does not syntax-check sized-literal base notation, is inconsistent
about `i_`/`o_`/`w_` prefixes (silently creating implicit nets), and declares registers next to their use instead
of in the declaration region.

**Signature:** sized literals without a base char (`` '<digit> ``); an `if`/`case` branch with >1 statement and no
begin/end; identifiers differing from a declared port only by a missing prefix; reg/wire/localparam declared
mid-body; assignment to a bit index outside the declared range.

**Exemplar:** `ext_askEncoder` BTNOP packing — base-less `1'0` (must be `1'b0`), empty `if(cond) else`, two
un-braced statements under one `if`; `ext_pcmInterface` `o_fifo_btnop = sync_xfr_en && ...` dropping the `i_`
prefix → implicit undriven net → BTNOP flag stuck 0 (all `72b2219`).

**Prevention rules:**
- Lint/compile every file with `` `default_nettype none `` before any functional review; treat
  implicit-net/undeclared-identifier and out-of-range index warnings as build errors.
- Reject any `` '<digit> `` literal lacking a base char and any multi-statement branch lacking begin/end.
- Keep all reg/wire/localparam in the declaration region; body contains only assign/always/instances.
- Cross-check every RHS identifier against the module's declared port/reg/wire list (prefix-exact).

---

## T8 · FPGA_RAM — memory inference & physical-resource modeling
**Severity medium · Detect: STATIC**

**Why LLM fails:** writes idealized behavioral memory (any number of write ports, arbitrary dynamic indexing, no
init) with no model that vendor RAM macros have exactly one write port, need a ramstyle pragma, and (on
Synplify/Lattice) crash on dynamic-index reads. Picks attributes by surface familiarity (`syn_preserve`) rather
than the correct RAM-inference attribute.

**Signature:** an array with two write ports in one always block; a memory tagged `syn_preserve` instead of
`syn_ramstyle`; a dynamic-index read of an array targeted to RAM; an inferred-RAM array with no reset/init when
reads can precede writes.

**Exemplar:** Duration LUT `reg [7:0] r_dur_lut[0:31]` with TWO write ports in one block tagged `syn_preserve=1`,
un-reset → XO2 cannot infer; fixed to `syn_ramstyle="distributed"`, second port under `` `ifndef XO2 ``, power-on
init loop (`c69a048`, `1851ac0`).

**Prevention rules:**
- Arrays targeted to FPGA RAM have exactly one write port and the correct vendor ramstyle attribute; confirm via
  the synthesis RAM-inference report.
- Read RAM arrays with an explicit case MUX, never a dynamic index, on Synplify/Lattice; guard non-synthesizable
  extra ports with `` `ifndef ``.
- Reset/init the array if reads can precede the first write.
- (Full vendor detail → `lattice-fpga` skill.)

---

## T9 · WIDTH_TRUNCATION — value vs index-width confusion
**Severity low · Detect: STATIC**

**Why LLM fails:** holds two inconsistent width models simultaneously (18-bit in comments/intent, 17-bit in the
declaration) and never reconciles them; conflates an index width (`log2(SIZE)`) with the value it must hold
(`SIZE-1`).

**Signature:** a bit index in an always block exceeding the declared vector range; header/comment width
disagreeing with the reg/port declaration; a value-holding localparam given a `[WIDTH-1:0]` slice where RHS max
exceeds it.

**Exemplar:** `ext_pcmInterface` header described an 18-bit payload with BTNOP at bit[17] but declaration was
`reg [16:0] r_pktData`; `c_pktData[17]=1'b1` targets a non-existent bit, silently dropped (`f451926`). Related:
`localparam [FIFO_PTR_WIDTH-1:0] FIFO_MAX_PTR = FIFO_SIZE-1` truncated for non-power-of-two sizes (already in
`synthesis-check.md`).

**Prevention rules:**
- Bit indices must be within the declared range; enable index-out-of-bounds lint; keep header/comment widths in
  sync with declarations.
- Keep range/limit constants unsized and slice explicitly only at the point of comparison against a pointer.
