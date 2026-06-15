> **Generic reference** — deployed to `~/.claude/agent-kit/` by chip-design-skills/install.py.
> The class structure / templates are universal; commit & module examples are from venezia-fpga
> and are illustrative.

# Verified Evidence — Six Ground-Truth Bugs

These six commits were independently re-read from the raw `db/design` diffs to confirm the taxonomy is not
hallucinated. Each shows the AI code (at the tag) and the human fix, with the root cause. Hashes are in
`db/design`. Reproduce with `cd db/design && git show <hash>`.

---

## E1 · `5b61531` — i2c: AI invented an unreachable FSM corner  → T1 PROTOCOL_SPEC

Commit subject: *"i2c protocol처리에서 ai가 잘못 코딩한 것을 원복함."* (reverted what the AI coded wrong)
File: `d_i2c/mdl/ext_i2cSerialInterface.v`

The AI added a `STREAM_WRITE` branch under the `CHK_ADR` `START_DET` block and a manual `c_clearStartStopDet`.
The human's own commit comments are the diagnosis:

```verilog
// --- AI version (at tag): handling under CHK_ADR, gated by i_startStopDetState==START_DET ---
`STREAM_WRITE: begin
    // sync-xfr-extension: repeated START in addressing mode (write→read)
    if (i_addressing_mode_en) begin
        c_streamRwState = `STREAM_DEV;
        c_fifo_access = 2'd0;
    end
    else begin
        c_loopState = `LOOP_IDLE; // unexpected repeated-start in legacy mode
    end
end
// ... and in INC_ADR / STREAM_DEV:
if (i_addressing_mode_en) begin
    c_clearStartStopDet = 1'b1;     // <-- AI clears the bus-detected START state
    c_streamRwState = `STREAM_REG;
end

// --- Human fix (5b61531): commented OUT, with the reasoning ---
//`STREAM_WRITE: begin
//    c_loopState = `LOOP_IDLE; // unexpected repeated-start in legacy mode
//end
// AI가 불필요하게 만들었음.
// FIXME: 이게 왜 필요하지? STREAM_WRITE는 START_DET에서 실행될 수 없다.
//if (i_addressing_mode_en) begin ...
        //c_clearStartStopDet = 1'b1;   // <-- removed
        c_streamRwState = `STREAM_REG;
```

**Root cause:** the LLM defended a state combination (`STREAM_WRITE` while `START_DET`) that is **structurally
unreachable** — `STREAM_WRITE` only occurs under `NULL_DET`. It also *cleared* `i_startStopDetState`, a signal
that reflects real SCL/SDA edges it must passively observe. No reachability analysis; mutating non-owned protocol
state. **Detect: STATIC** (unreachable branch + clear-of-detected-state) for the *cause*; the resulting `0xFF`
write corruption is **SIM**.

---

## E2 · `86a1796` — decoder clocked from a gated clock  → T3 CLOCK_RESET_CDC

Commit subject: *"change decoding refClk source to original clock which is not gated by forward data"*
File: `d_top/mdl/ext_d_main.v`

```verilog
// --- AI version (at tag) ---
.i_refClk(w_askRefClk),   // ~=10MHz     <-- CKO of todoc_prim_icg u_askRefClk_icg (gated by forward link)

// --- Human fix (86a1796) ---
//.i_refClk(w_askRefClk),   // ~=10MHz
.i_refClk(i_refGenClk),   // ~=10MHz     <-- ungated free-running source
```

**Root cause:** `w_askRefClk` *looks* like a reference clock by name but is the gated output of an ICG whose
enable comes from the forward-link clock-gating FSM. The back-tel **decoder must run while forward data pauses**
— precisely when this clock stops. The LLM picked a clock by name without tracing its provenance to the gate.
**Detect: STATIC** if the reviewer traces the clock driver; **SIM** for the freeze symptom.

---

## E3 · `2ebd51f` — timer count==0 → consumer FSM deadlock  → T5 FSM_CORNER_DEADLOCK

Commit subject: *"fix FIFO read FSM deadlock condition when 0 count value sets to btnop timer"*
File: `d_dec/mdl/ext_backTelInterface.v`

```verilog
// --- AI version (at tag) ---
r_timer_active <= (i_btnop_timer_val != 8'd0);   // 0 → never active
...
if (r_timer_count == 8'd1) begin                 // exact-match expiry
    r_timer_count  <= 8'd0;
    r_timer_active <= 1'b0;
end

// --- Human fix (2ebd51f) ---
r_timer_active <= 1'b1;//(i_btnop_timer_val != 8'd0);
...
if (r_timer_count <= 8'd1) begin // 최초 timer값이 0으로 셋팅되는 것도 포함함.
                                 // timer 값이 0과 1은 모두 동일하게 1 cycle 동안 active 됨.
    r_timer_count  <= 8'd0;
    r_timer_active <= 1'b0;
end
```

**Root cause:** with `val==0`, `active` was never asserted, so the slow-`cellClk` 2-FF synchronizer feeding the
FIFO-read FSM's `w_timer_active_cdc` never saw a high level → the FSM waited forever. Two compounding errors: a
degenerate input (`count==0`) not modeled, and exact `==` terminal-count comparison. Fix: always assert one tick
(`0` and `1` both give 1-cycle active) and use `<=`. **Detect: SIM** (directed test `timer_val=0`).

---

## E4 · `737070b` + `06f19b0` — circular FIFO pointer comparison  → T6 POINTER_HANDSHAKE

File: `d_enc/mdl/ext_fwd_fifo.v`

```verilog
// --- AI version (at tag): native-width, wrong direction, two regs in one always block ---
always @(posedge i_clk or negedge i_rst_n)
  if (~i_rst_n) begin o_buf_out<=0; o_nxt_buf_out_valid<=1'b0; o_nxt_buf_out<=0; end
  else if (i_rd_en && !o_buf_empty) begin
    o_buf_out <= r_buf_mem[r_rd_ptr];
    if ((r_rd_ptr + 1) > r_wr_ptr) begin          // native width, ">" — off-by-one + wraps at MAX
      o_nxt_buf_out_valid <= 1'b0; ...
    end else begin
      o_nxt_buf_out_valid <= 1'b1;
      o_nxt_buf_out <= r_buf_mem[(r_rd_ptr + 1)];
    end
  end

// --- Human fix step 1 (737070b): split into two always blocks, zero-extend, "<" ---
if (({1'b0, r_rd_ptr} + 1) < {1'b0, r_wr_ptr}) begin ... end

// --- Human fix step 2 (06f19b0): (r_rd_ptr+1) <= (r_wr_ptr-1) — ⚠️ 후에 결함 판명 (CORRECTION 참조) ---
if (({1'b0, r_rd_ptr} + 1) <= ({1'b0, r_wr_ptr} - 1)) begin
  o_nxt_buf_out_valid <= 1'b1;
  o_nxt_buf_out <= r_buf_mem[(r_rd_ptr + 1)];
end

// --- CORRECTION (2026-06-15, venezia BUG-002): step2도 raw 포인터라 0 경계 straddle에서 FP/FN ---
//   FP rd=127,wr=0,count=1 → 128<=255 참 (다음 없는데 valid); FN rd=127,wr=2(straddle) → 128<=1 거짓 (누락).
//   진짜 fix = occupancy counter (R1). formal(fwd_tb): step2 FAIL@step7 / 아래 PASS@depth24.
if (o_fifo_counter >= 2) begin
  o_nxt_buf_out_valid <= 1'b1;
  o_nxt_buf_out <= r_buf_mem[(r_rd_ptr + 1)];
end else o_nxt_buf_out_valid <= 1'b0;
```

**Root cause:** the LLM treated circular pointers as monotonic linear indices: assumed `wr>rd`, did `+1` at
native width (wraps mod 2^W at `ptr==MAX`), and used a raw magnitude test instead of occupancy. It also bundled
`o_buf_out` and `o_nxt_buf_out` (different reset semantics) into one always block. **Detect: SIM** at boundaries;
the missing `{1'b0,...}` zero-extension is a **STATIC** smell.

---

## E5 · `d68ae6a` — prescaler advances one cycle too early after load  → T4 TIMING_CYCLE

Commit subject: *"fix prescaler loading timing bug"*
File: `d_dec/mdl/ext_backTelInterface.v`

```verilog
// --- AI version (at tag): prescaler counts immediately after a timer load ---
if (...load...) begin c_btnop_tmr_load = 1'b1; c_timer_count = i_btnop_timer_val; end
else if (r_prescaler == 7'd98) begin ... end       // no guard for the cycle after load

// --- Human fix (d68ae6a): skip the post-load cycle ---
else if (r_btnop_tmr_load) begin
    // r_prescaler value is NOT APPLYED to counting logics
end
else if (r_prescaler == 7'd98) begin ... end
```

**Root cause:** the load is registered, so the freshly-loaded prescaler/count is not valid until the cycle after
`r_btnop_tmr_load`. The AI let the prescaler comparison fire in that gap → off-by-one-cycle. (Compounded by the
`98`→`97` prescaler boundary in `d0c5584`.) **Detect: SIM/timing.**

---

## E6 · `72b2219` — non-compiling Verilog + implicit undriven net  → T7 STRUCTURE_STYLE

Commit subject: *"fix syntax error"*
Files: `d_enc/mdl/ext_askEncoder.v`, `d_pcm/mdl/ext_pcmInterface.v`

The AI emitted: a base-less sized literal `1'0` (legal Verilog needs a base char → `1'b0`); an `if(cond) else`
with an empty then-branch; two un-braced statements under one `if` (so the second ran unconditionally); and
`o_fifo_btnop = sync_xfr_en && ...` — referencing `sync_xfr_en` when the port is `i_sync_xfr_en`, creating an
**implicit undriven net** that pinned the BTNOP flag to 0.

**Root cause:** loosely-shaped, Python/C-flavored Verilog — indentation treated as scope, no literal-base
checking, inconsistent `i_` prefixes silently making implicit nets. **Detect: STATIC** — a
`` `default_nettype none `` compile would have rejected every one. They shipped because no lint gate ran.

---

### Verification note
All six were read directly from `db/design` history during this analysis; the multi-agent forensic synthesis
independently produced the same hashes, signals, and root causes — high confidence the taxonomy reflects real
engineering, not model confabulation.
