> **Generic reference (프로젝트 무관)** — deployed to `~/.claude/agent-kit/` by chip-design-skills/install.py.
> classes·signatures·prevention·Review Catalog(S/R)는 **모든 프로젝트 공유 일반지식** — commit 해시·모듈명 같은
> 프로젝트 특정 정보를 두지 않는다. exemplar는 일반 코드 *패턴*(설명용)이다.
> 구체 venezia 출처(commit/모듈)는 `evidence.md`(포렌식). **자기 프로젝트의 instance/흉터는 그 repo의
> 지식시스템**(preflight: `docs/solutions`·graphify)에서 recall한다. → reviewer/prover/coder/architect는
> 이 일반 정본을 적용하고, 프로젝트 구체사례는 recall로 보강한다.

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

**Exemplar (general pattern):** a `c_clear*=1` combinational override on a detected bus-event signal; a case-arm
for a substate unreachable under its enclosing guard (dead code). (venezia 출처: `evidence.md` E1)

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

**Exemplar (general pattern):** a new registered signal built but never referenced by the legacy consumer → dead
feature; a new `.v` missing from the build filelist → elaboration unresolved instance. (venezia 출처: `evidence.md`)

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

**Exemplar (general pattern):** a decoder `*Clk` port driven by an ICG CKO whose enable stops in the very mode the
decoder must keep running → froze when the gate closed; fix = ungated source clock. (venezia 출처: `evidence.md` E2)

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

**Exemplar (general pattern):** `rd_en` asserted then the combinational FIFO output sampled the next state without
latching → unstable over multi-cycle consume; fix = latch to a holding reg + per-source data-valid/ack (not a
fixed `_d[N]` shift). (venezia 출처: `evidence.md` E5)

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

**Exemplar (general pattern):** a timer `r_active <= (val!=0)` + exact `==` expiry → a zero/min load never asserts
active across a slow 2-FF synchronizer → wait state hangs forever; fix = one-tick-active + `<=` boundary compare.
(venezia 출처: `evidence.md` E3)

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

**Exemplar (general pattern):** lookahead `if((rd+1) > wr)` at native width → off-by-one for a single entry, wraps
at MAX. A zero-extended raw-pointer rewrite (`({1'b0,rd}+1) <= ({1'b0,wr}-1)`) is **still a raw-pointer test and
fails formal** at the 0-straddle boundary — correct fix = occupancy counter (`count >= k+1`). (venezia 출처: `evidence.md` E4)

**Prevention rules:**
- Derive "has k-ahead entry" from the occupancy counter (`count >= k+1`; 1-ahead ⇒ `>=2`), not a raw pointer magnitude test;
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

**Exemplar (general pattern):** base-less literal `1'0` (must be `1'b0`); empty `if(cond) else`; two un-braced
statements under one `if`; an RHS identifier dropping the `i_` prefix → implicit undriven net → flag stuck 0.
(venezia 출처: `evidence.md` E6)

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

**Exemplar (general pattern):** a `reg [W:0] lut[0:N]` with TWO write ports in one block tagged `syn_preserve`,
un-reset → vendor cannot infer RAM; fix = `syn_ramstyle`, extra port under `` `ifndef ``, power-on init.
(venezia 출처: `evidence.md`)

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

**Exemplar (general pattern):** a header/comment 18-bit payload vs a `reg [16:0]` declaration → `data[17]=1'b1`
targets a non-existent bit, silently dropped; `localparam [W-1:0] MAX = SIZE-1` truncated for non-power-of-two
sizes. (venezia 출처: `evidence.md`)

**Prevention rules:**
- Bit indices must be within the declared range; enable index-out-of-bounds lint; keep header/comment widths in
  sync with declarations.
- Keep range/limit constants unsized and slice explicitly only at the point of comparison against a pointer.

---

## Review Signature Catalog — STATIC(S) + SIM-RISK(R)  [single source-of-truth · 프로젝트 무관]

> verilog-rtl-reviewer가 매 리뷰에 **전수 적용**하는 카탈로그(정본). 새 signature가 생기면 **여기에** 추가한다 —
> agent는 수정하지 않는다. reviewer는 이 표를 로드해 **모든 S를 must-catch**, **모든 R을 라우팅 + directed test
> 발행**한다. routing 정본: `bug-class-router.py`.
> ⚠️ **여기엔 프로젝트 특정 정보(commit 해시·모듈명)를 두지 않는다** — 일반지식이라 모든 프로젝트가 공유한다.
> 어느 commit/모듈에서 이 signature가 났는지(=구체 exemplar/흉터)는 **각 프로젝트의 지식시스템**(preflight:
> 그 repo의 `docs/solutions`·graphify)에서 recall한다.

### STATIC signatures (S) — 읽기 + `verilator --lint-only -Wall` + elaboration + (S12/S13) reachability로 확정. 하나라도 통과 = 리뷰 실패.
| # | 정적 위반 (diff signature, 일반 패턴) | Class | 탐지 |
|---|---|---|---|
| S1 | 새 `.v`가 filelist에 없음 → elaboration unresolved instance | T2 | filelist grep + elaborate |
| S2 | RHS 식별자가 선언된 port/reg/wire와 불일치 (i_ prefix 누락 → implicit net) | T7 | verilator IMPLICIT/UNDRIVEN + port-list 대조 |
| S3 | base char 없는 sized literal (`1'0`, `'<digit>`) | T7 | lint/compile error |
| S4 | if/case 분기 statement >1 인데 begin/end 없음 | T7 | 구조 읽기 + lint |
| S5 | 선언된 vector 범위 밖 bit index | T9 | 선언폭 대조, index-out-of-range lint |
| S6 | clock port가 enable-gating cell 구동인데 sink는 gate 닫혀도 동작 필요 | T3 | 드라이버를 PI/PLL/osc까지 trace, gating 조건 vs sink 요구 |
| S7 | async reset/set pin이 `always @(*)` 조합식 구동 | T3 | reset pin RHS가 reset-tree/레지스터인지 |
| S8 | inferred RAM dual write / `syn_preserve` 오용 / dynamic-index read | T8 | write-port 수·속성·index 형태 |
| S9 | 기능 mode/control port에 상수 literal tie | T2 | 포트가 register bit/top pin으로 trace |
| S10 | 새 registered output fan-out = 0 (dead feature) | T2 | downstream consumer ≥1 |
| S11 | writable register-map인데 read-back hardcoded-0 | T2 | write 경로 대비 read-back 경로 |
| **S12** ⭐ | enclosing state guard 하 도달불가 case 분기 (protocol-relational dead-code; reviewer가 owner) | T1 | reachability 추론 + **substate reset provenance**(async-reset만이면 carryover로 reachable → dead 단정 철회) |
| S13 | protocol-detected 신호(START/STOP/`*_detected`)에 조합 clear/override | T1 | detected-event 신호에 clear/override assign 검색 |

### SIM-RISK signatures (R) — 정적 단정 금지. flag + **route** + directed test. owner 없이 종결 금지("읽어보니 OK"는 결함).
라우팅 3 destination (`bug-class-router.py` codify): self-contained 로직/타이밍 → **Prover/formal**; cross-domain CDC timing → **directed sim**; protocol-relational → **directed sim 또는 STATIC reachability(S12)**.
| # | SIM 위험 (diff signature, 일반 패턴) | Class | route | directed test |
|---|---|---|---|---|
| R1 | read data가 `rd_en`과 같은 사이클 샘플 (단일클럭 sync-read) | T4 | self-contained → Prover | DT-A: single-entry read + holding reg 안정성 |
| R2 | 고정 `_d[N]` shift를 가변/CDC latency read-valid로 | T4 | cross-domain → sim; 단일클럭 고정지연이면 R1→Prover | DT-A 변형 |
| R3 | cross-domain active level timeout 없이 대기 / `count==0` deadlock | T5 | 로직(count==0) → Prover; CDC timing 잔여 → sim | DT-B: timer/count=0 로드 |
| R4 | circular pointer off-by-one / full-wrap lookahead | T6 | self-contained → Prover (+zero-ext 누락은 S-급 STATIC 병기) | DT-C: FIFO-full·single-entry·ptr==MAX |
| R5 | synchronized ack 전 FSM 전진 CDC race | T3/T5 | cross-domain → sim (multiclock formal=최난) | DT-D: ack 지연 주입 |
| R6 | prescaler/counter off-by-one (load 직후 미스킵) | T4 | self-contained → Prover | DT-E: load 후 첫 count skip |
| R7 | cross-packet parameter inheritance | T1 | protocol-relational → sim/S12 | DT-F: 연속 2패킷 mode 의존 |
| R8 | squash-vs-extension 연속 이벤트 의미 | T1 | protocol-relational → sim/S12 | DT-G: 동일타입 연속 squash/연장 |
| R9 | i2c repeated-START가 SCL tLOW race | T1 | protocol-relational → sim/S12 | DT-H: repeated-START를 tLOW 정렬 |

> 중복 회피: bit-width/latch/naming/2-proc FSM 일반 규칙, CDC 방식 선택, 래칭 보존은 `verilog-rtl` skill에 있다 —
> 이 카탈로그는 **AI 실패 signature 탐지·라우팅**(프로젝트 무관)만 담는다.
