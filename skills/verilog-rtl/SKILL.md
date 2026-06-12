---
name: verilog-rtl
description: |
  Verilog/SystemVerilog RTL 설계 및 분석 skill. 다음 상황에서 사용:
  (1) RTL 코드 작성 - 신호 네이밍, always 블록 분리, FSM 설계
  (2) 사이클 분석 - 동일 사이클 처리 로직 식별, 타이밍 관계 분석
  (3) 합성 가능성 검토 - latch 방지, CDC 처리, 합성 문제 사전 식별
  (4) 코드 리뷰 및 버그 탐지 - race condition, 미정의 동작 검출
  (5) 모듈 통합 - top integration, 포트 연결, 파라미터 전달
  (6) Coverage 설계 - UVM 없이 SV만으로 covergroup, coverpoint, cross, bin, assertion coverage 구현
  (7) SV 검증 구문 - SVA assertion, covergroup, cross, 테스트벤치 SV 문법
  (8) Module Analysis - RTL 수정 전 모듈 전체 분석서 작성, FSM 간 연계/타이밍/CDC 문서화
  (9) 파일 헤더 주석 - doxygen 스타일 헤더 신규 생성 및 수정 시 revision history 이력 관리
  Verilog/SystemVerilog RTL 작업이라면 반드시 이 스킬을 사용.
  트리거: Verilog, SystemVerilog, RTL, always, FSM, 합성, synthesis, clock, reset,
    covergroup, coverpoint, cross, bins, cover property, FSM coverage, MC/DC,
    bit-width, truncation, clog2, localparam, parameter width,
    Verilator, lint,
    module analysis, 모듈 분석, FSM 분석, signal analysis,
    file header, doxygen, @file, @brief, @history, 파일 헤더, 수정 이력,
    sync-read latency, FIFO read FSM, deadlock corner, circular pointer, wrap, gated clock,
    async reset provenance, integration audit, fan-out, register read-back, protocol fidelity, lint gate
---

# Verilog RTL Design Skill

## 핵심 개념

Verilog RTL 설계의 두 가지 핵심:
1. **Always 블록 분리** - 로직을 목적별로 분리하여 가독성과 합성 품질 향상
2. **사이클 분석** - 같은 클럭 사이클에 처리되는 로직을 식별하여 타이밍 이해

RTL 설계 흐름: **요구사항**(무엇을) → **사이클 맵**(언제) → **Always 분할**(어떻게)

---

## 1. Design Rules

### 필수 규칙

| 규칙 | 설명 |
|------|------|
| **Asynchronous Reset** | Active low (`i_rst_n`), 비동기 리셋 기본 [→§1.Reset] |
| **No Latches** | 기본값 할당 또는 if/case 완전성으로 방지 [→§1,§7] |
| **CDC 방식 선택** | Slow→Fast: 2FF/Pulse, Fast→Slow: Handshake 또는 2FF(장기유지 레벨) [→§1.CDC] |
| **Blocking 규칙** | always_ff: `<=`, always_comb: `=` [→§2] |
| **단일 할당 원칙** | 동일 신호를 여러 always에서 할당 금지 [→§2] |
| **Bit-Width Safety** | sized 변수에 값 할당 시 max value < 2^W 검증 필수 [→§1.BitWidth] |
| **H/W 리소스 최소화** | 인스턴스/FF/LUT 추가 전 기존 리소스 재사용 우선 검토 [→§1.Resource] |
| **Combinational Depth 최적화** | FSM state 내 조건 분기 깊이를 타이밍에 맞게 제한 [→§1.Timing] |
| **래칭 데이터 보존** | 래칭된 레지스터가 소비 전에 다른 경로에서 덮어써지지 않는지 검증 [→§1.DataLife] |
| **정의-구현 대조** | FSM state 구현 후 설계 정의와 1:1 대조하여 동작 불일치 검출 [→§1.DefImpl] |
| **원형 FIFO 포인터** | wrap 경계 modular 비교, occupancy counter 기반 점유 판정 [→§1.Pointer] |

### H/W Resource Minimization (Power & Area)

- 새 인스턴스(CDC, FIFO 등) 추가 전 **기존 인스턴스의 입력 교체**로 해결 가능한지 먼저 검토
- 용도가 변경된 인스턴스는 포트/와이어와 함께 교체, 사용처가 없어진 포트는 제거
- FSM state를 무조건 추가하지 않고, **기존 state 내 조건 분기**로 해결 가능한지 먼저 검토
- 기존 경로(레거시 등)는 state 추가 없이 유지하여 동작 변경 방지
- state 추가는 combinational depth가 과도해져 타이밍 위험이 있을 때만 수행

### Combinational Depth Optimization (Timing)

- 하나의 FSM state에서 크로스 FSM 신호 + CDC 신호 + FIFO 상태를 동시에 판단하는 것은 피함
- 조건이 깊어지면 다음 사이클로 분리 (별도 state)하되, **기존 타이밍 정렬을 깨뜨리지 않는지** 반드시 확인
- 클럭 게이트가 다른 FSM 간 신호 전달 시, 래칭 사이클 계산하여 정렬 유지 검증

### Latched Data Preservation (Data Lifecycle)

- 레지스터가 상태 A에서 래칭되고 상태 B에서 소비될 때, A→B 사이의 **모든 경로**에서 해당 레지스터를 덮어쓰지 않는지 검증
- 특히 Proactive/Speculative 경로에서 래칭 레지스터를 조건 없이 갱신하면 기존 pending 데이터가 유실됨
- **검증 방법**: 래칭 레지스터별로 `Write 상태 → Read 상태` 쌍을 나열하고, 중간 경로에 Write가 없는지 확인

### Definition-Implementation Cross-Check (정의-구현 대조)

- FSM state의 코드를 작성한 후, 해당 state의 **설계 정의(Plan/Design 문서)**를 다시 읽고 1:1 대조
- 정의에 없는 동작을 구현에 추가했으면 → 정의가 불완전한지, 아니면 구현이 과잉인지 판단
- H/W FSM의 각 state는 기본적으로 **하나의 명확한 역할**을 가져야 함. 단, 다음 경우 동일 state에서 구현 허용: (1) 리소스 최적화를 위해 역할이 유사한 로직 통합 (2) 타이밍 최적화를 위해 동일 사이클에 처리되어야 하는 로직 통합 (3) combinational depth 감소를 위한 state 공유
- state 공유/통합 시에도 설계 정의에 그 근거를 명시하고, 통합된 각 경로가 정의와 일치하는지 대조

### Bit-Width Truncation 방지

**Bit-Width Safety 규칙:**
- localparam은 특별한 이유 없으면 unsized 사용 (32-bit default → 값 손실 없음)
- `[W-1:0] var = expr` 작성 시: max(expr) < 2^W 검증 필수 (파라미터 전 범위 대상)
- `$clog2(N) ≠ floor(log2(N))` — N이 2^k가 아니면 1 차이 → 비트 부족 버그
- 코드 생성/리뷰 시 모든 sized 변수에 대해 반복 검증

BAD/GOOD 예제, $clog2 vs custom log2 비교 테이블, 검증 체크리스트, 추가 위험 패턴: `references/synthesis-check.md` > Bit-Width Safety 참조

### Reset 패턴

#### ⚠️ Sensitivity List 규칙

리셋 사용 O → `@(posedge i_clk or negedge i_rst_n)`, 리셋 사용 X → `@(posedge i_clk)`

#### 리셋이 필요한 레지스터 (비동기 리셋)

```verilog
// 상태 레지스터, 제어 신호 등 - 리셋 필요
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_state <= S_IDLE;
        r_valid <= 1'b0;
    end else begin
        r_state <= c_next_state;
        r_valid <= i_valid;
    end
end
```

#### 리셋이 불필요한 레지스터 (리셋 없음)

```verilog
// 데이터 경로, 파이프라인 데이터 등 - 리셋 불필요
always_ff @(posedge i_clk) begin
    r_data_d1 <= i_data;
    r_data_d2 <= r_data_d1;
end
```

동기 리셋: 글리치 민감한 환경/고속 설계 시 사용 — `@(posedge i_clk)` + `if (!i_rst_n)` 구조

### 리셋 필요 여부 판단

| 레지스터 타입 | 리셋 필요 | 이유 |
|--------------|----------|------|
| FSM 상태 | ✅ 필요 | 초기 상태 보장 |
| 제어 신호 (valid, ready) | ✅ 필요 | 잘못된 트랜잭션 방지 |
| 카운터 | ✅ 필요 | 초기값 보장 |
| 데이터 경로 | ❌ 불필요 | valid로 게이팅됨 |
| 파이프라인 데이터 | ❌ 불필요 | valid로 게이팅됨 |
| 지연 레지스터 | ❌ 불필요 | 단순 지연 용도 |

### CDC (Clock Domain Crossing)

#### CDC 방식 선택 테이블

| 조건 | 방식 | 설명 |
|------|------|------|
| 1-bit level, 소스 ≥ 2 dest cycles | **2FF Sync** | Slow→Fast 자연 충족, Fast→Slow 검증 필수 |
| 1-bit pulse, 소스 ≥ 2 dest cycles | **2FF + Edge Detect** | 펄스가 충분히 넓어 2FF 캡처 가능 |
| 1-bit pulse, 소스 < 2 dest cycles | **Pulse Sync** (Slow→Fast) 또는 **Handshake** (Fast→Slow) | 펄스 유실 위험 → toggle 변환 또는 Req/Ack |
| Multi-bit (순차적) | **Gray + 2FF** | 포인터, 카운터 |
| Multi-bit (스트림) | **Async FIFO** | 데이터 버퍼링 |

**핵심 판단 기준**: 소스 신호가 대상 클럭 **최소 2사이클** 유지되는가?
- **예** → 2FF 기반 (level: 2FF Sync, pulse: 2FF + Edge Detect)
- **아니오** → toggle 또는 핸드쉐이크 필요 (Pulse Sync / Handshake)
- Slow→Fast는 자연 충족 (1 src cycle ≥ 2 dest cycles). Fast→Slow는 주파수 비율로 검증 필수.

**펄스 + 동반 데이터**: 펄스를 CDC하면 동반 multi-bit 데이터는 펄스 기간 동안 안정이므로 별도 CDC 불필요 — 수신 측에서 동기화된 펄스 시점에 직접 샘플링. 상세: `references/cdc-patterns.md`

---

## 1.Pointer Circular-FIFO Pointer Comparison Semantics

**Taxonomy T6 (POINTER_HANDSHAKE).** LLM은 원형 FIFO 포인터를 단조 증가 선형 인덱스로 추론한다:
`wr>rd`가 항상 성립한다고 가정하고, `+1` offset을 native 포인터 폭에서 계산해(즉 `mod 2^W`로 wrap) lookahead를
판정하며, 점유량을 occupancy counter가 아닌 raw magnitude 비교로 도출한다. 가장 많은 lookahead 데이터가 존재하는
**wrap 경계(FIFO full, `wr==0`)**를 모델링하지 못한다.

> ⚠️ **§1.BitWidth와의 구분 (중복 아님) [→§1.BitWidth]**: `synthesis-check.md`의 `FIFO_MAX_PTR`/`PTR_WIDTH`
> 케이스는 **width-truncation**(예: `PTR_WIDTH=log2(7)=2`인데 `FIFO_SIZE-1=6`은 3비트 필요 → 선언 폭에서 silent
> 절단)이다. **이 §1.Pointer는 wrap-comparison**(올바른 폭이라도 modular 산술의 경계에서 틀리는 문제)을 다룬다.
> 같은 파일 `ext_fwd_fifo.v`에서 발생한 **서로 다른 두 버그 클래스**다. width는 [→§1.BitWidth]에서, wrap은 여기서 다룬다.

### 규칙

| # | 규칙 | 검출 | 근거 commit |
|---|------|------|-------------|
| R1 | 점유/lookahead 판정은 **occupancy counter**(`count>=N`, empty=`count==0`, full=`count==SIZE`)에서 도출한다. raw pointer magnitude 비교 금지. | **[STATIC]** smell (포인터 크기 직접 비교) | `737070b`,`3f979ac` |
| R2 | 비교 offset을 더하기 전에 포인터를 **1비트 zero-extend** (`{1'b0, ptr}+1`) — add가 `2^W`에서 wrap하지 않도록. | **[STATIC]** smell (offset add에 `{1'b0,..}` 부재) | `737070b` |
| R3 | **wr-wraps-to-0 / FIFO-full 경계**를 명시적으로 처리. wr은 write-then-increment(실제보다 +1), rd는 pre-increment 기준 → full이면 `wr==0`이므로 `(rd+1) <= (wr-1)`로 비교. | **[SIM]** (경계 테스트) | `06f19b0` |
| R4 | 단일 엔트리 lookahead는 **strict `<`** (`(rd+1) < wr`) — count==1에서 "다음 valid"가 거짓이어야 함. | **[SIM]** | `737070b` |
| R5 | FIFO write-enable은 **항상 `~full`과 AND**. full/almost-full은 flow-control 출력(sync request 등)으로 표면화. | **[STATIC]** (write-en에 `~full` 부재; status flag fan-out) | `3f979ac` |
| R6 | 같은 사이클 read+write는 **semaphore**로 중재 — 동시 r/w 시 occupancy 불변(`counter <= counter`). | **[SIM]** (정적 smell: 중재 부재) | `3f979ac` |

### BAD (AI) / GOOD (fixed)

```verilog
// ──────────── BAD: ext_fwd_fifo.v (AI) — R2/R3/R4 모두 위반 ────────────
if ((r_rd_ptr + 1) > r_wr_ptr) begin            // ⚠️ R2: native 폭 → ptr==MAX에서 +1이 mod 2^W wrap
    o_nxt_buf_out_valid <= 1'b0;                 // ⚠️ R4: 방향(>) 오류, R1: raw magnitude
end else begin
    o_nxt_buf_out_valid <= 1'b1;
    o_nxt_buf_out <= r_buf_mem[(r_rd_ptr + 1)];
end

// ──────────── GOOD step1: 737070b (zero-extend + strict <) ────────────
if (({1'b0, r_rd_ptr} + 1) < {1'b0, r_wr_ptr}) begin   // ✅ R2 zero-extend, R4 strict <
    o_nxt_buf_out_valid <= 1'b1;
    o_nxt_buf_out <= r_buf_mem[(r_rd_ptr + 1)];
end else begin
    o_nxt_buf_out_valid <= 1'b0;
end

// ──────────── GOOD step2: 06f19b0 (wr-wraps-to-0 / FIFO-full 경계) ────────────
// wr: write-then-increment (실제 index보다 1 많음). rd: 증가 전 기준. full ⇒ wr==0.
if (({1'b0, r_rd_ptr} + 1) <= ({1'b0, r_wr_ptr} - 1)) begin  // ✅ R3: (rd+1) <= (wr-1)
    o_nxt_buf_out_valid <= 1'b1;
    o_nxt_buf_out <= r_buf_mem[(r_rd_ptr + 1)];
end
```

```verilog
// ──────────── R5/R6: write guard + flow-control + semaphore (3f979ac) ────────────
// R5: ~full 없이 write-enable 금지
if (~w_fwd_fifo_full) c_fifoWrEn = 1; // ✅ fifo full이면 들어오는 data를 버림
// R5: full을 flow-control(sync request)로 표면화
else if (w_fwd_fifo_count[7:0] >= {1'b0,i_sync_req_fifo_num[6:0]} || w_fwd_fifo_full)
    r_syncReq <= 1;
// R6: 동시 read+write 시 occupancy 불변
if ((!o_buf_full && i_wr_en) && (!o_buf_empty && i_rd_en))
    o_fifo_counter <= o_fifo_counter;   // ✅ net change 0
```

### 필수 boundary tests

| 테스트 | 기대 | 검출 | commit |
|--------|------|------|--------|
| single entry (`count==1`) | nxt-valid = 0 (strict `<`) | **[SIM]** | `737070b` |
| `ptr == MAX` wrap | `+1`이 false-valid로 wrap되지 않음 (zero-extend) | **[SIM]** | `737070b` |
| wr-wraps-to-0 / FIFO full | nxt-valid가 `wr-1` 기준으로 정확 | **[SIM]** | `06f19b0` |
| full FIFO에 write | write-enable 억제, data drop, 데이터 손상 없음 | **[STATIC]**+**[SIM]** | `3f979ac` |
| 동시 read+write (full/empty 모두) | occupancy 불변 | **[SIM]** | `3f979ac` |

### 체크리스트

- [ ] **[STATIC]** empty/full/lookahead가 occupancy counter에서 나오는가 (raw pointer 비교 아님)? (R1)
- [ ] **[STATIC]** 비교 offset add 전에 `{1'b0, ptr}` zero-extend 했는가? (R2)
- [ ] **[SIM]** wr-wraps-to-0 / FIFO-full 경계가 `(rd+1) <= (wr-1)`로 처리되는가? (R3)
- [ ] **[SIM]** 단일 엔트리 lookahead가 strict `<`인가? (R4)
- [ ] **[STATIC]** 모든 write-enable이 `~full`과 AND되고, full이 flow-control로 표면화되는가? (R5)
- [ ] **[SIM]** 동시 r/w semaphore로 occupancy가 불변 유지되는가? (R6)
- [ ] **[STATIC]** 포인터 **폭**도 별도로 검증했는가? → width-truncation은 [→§1.BitWidth] (별개 클래스)

---

## 1.Protocol — Protocol / Spec Fidelity

**Taxonomy: T1 PROTOCOL_SPEC · "obey protocol state, don't invent or mutate it" · Detect: mixed**

> **원칙:** START/STOP detect, addressing-vs-legacy mode, param-vs-config inheritance 같은
> *프로토콜 상태 신호*는 외부 버스 이벤트의 **관찰값**이지, FSM을 강제하려고 LLM이 set하는 scratch
> flag가 아니다. 관찰하라, 합성하지 마라. 정의-구현 1:1 대조([→§1.DefImpl])의 프로토콜 특화 규칙.

### PF-1 — Observe, don't synthesize (관찰값을 clear/override 금지) — `5b61531`

⚠️ 이름이 *detected/valid*를 함의하는 신호(`*StartStopDet`, `*_detected`, 타 블록의 `*_valid`)에
clear/override를 걸지 말 것. FSM은 **관찰된 이벤트 자체**로만 전이한다. 또한 enclosing guard 때문에
도달 불가능한 case 분기는 **dead code로 flag**한다.

`ext_i2cSerialInterface.v`에서 AI는 (1) `CHK_ADR`의 `START_DET` 블록 안에 `STREAM_WRITE` 분기를
넣었으나 — `STREAM_WRITE`는 `NULL_DET`에서만 발생하므로 **구조적으로 도달 불가**, (2) 실제 SCL/SDA
edge를 반영하는 `c_clearStartStopDet=1`로 버스 상태를 **임의로 clear**했다. `5b61531`이 둘 다 원복.

```verilog
// AI (dead + state mutation):
`STREAM_WRITE: begin                       // ← START_DET 하에서는 도달 불가능 (dead)
    if (i_addressing_mode_en) begin c_streamRwState = `STREAM_DEV; c_fifo_access = 2'd0; end
    else c_loopState = `LOOP_IDLE;
end
...
if (i_addressing_mode_en) begin
    c_clearStartStopDet = 1'b1;            // ← 관찰된 버스 상태를 임의 clear
    c_streamRwState = `STREAM_REG;
end

// 5b61531 (fix): 도달불가 분기 주석처리 + clear 제거
// FIXME: 이게 왜 필요하지? STREAM_WRITE는 START_DET에서 실행될 수 없다.  ← human 진단
        //c_clearStartStopDet = 1'b1;
        c_streamRwState = `STREAM_REG;
```
**Detect:** dead 분기 + detected-state clear = **STATIC**(reachability 분석); 결과인 `0xFF` write 손상 = **SIM**.

### PF-2 — Mode-conditioned fields (모든 decode 분기가 mode bit를 switch) — `d5479c6`/`ee60097`

⚠️ 의미가 mode bit에 의존하는 byte는 **모든** decode 분기가 그 mode bit를 switch해야 한다.
**addressing mode에서는 device-select byte로부터 register address를 유도하지 말 것** — regAddr은
별도 STREAM_REG byte가 정한다. mode-independent 보호(device 불일치 시 IDLE 천이 등)는 양쪽 모두 유지.

AI는 device 분기에서 mode와 무관하게 `c_fifo_access`를 set하고 `c_regAddr = r_rxData >> 1`을
**device byte에서 무조건 유도**했다. `d5479c6`가 각 device 분기를 `if(i_addressing_mode_en)`로 감싸
legacy mode에서만 regAddr을 유도하도록 분리했고, `ee60097`이 D1(backtel) 분기를 두 mode 모두에서
올바로 처리하도록 보정했다.

```verilog
// AI: mode와 무관하게 device byte → regAddr (addressing mode에서 오염)
`I2C_ADDRESS_D1: begin
    c_fifo_access = 2'd1;
    if (r_rxData[0] == 1'b1) c_regAddr = r_rxData >> 1;   // ← device byte를 regAddr로 (잘못)
    else c_loopState = `LOOP_IDLE;
end

// d5479c6 + ee60097 (fix): 모든 분기가 mode bit를 switch
`I2C_ADDRESS_D1: begin
    if (i_addressing_mode_en)        c_fifo_access = 2'd1;                 // addressing: routing만
    else if (r_rxData[0] == 1'b1)    c_regAddr = r_rxData >> 1;            // legacy만 regAddr 유도
    else                             c_loopState = `LOOP_IDLE;
end
```
**Detect: STATIC**(decode 분기에 mode switch 누락은 읽기로 검출) · 오염 symptom은 **SIM**.

### PF-3 — Inter-packet inheritance (이전 패킷 mode 상속) — `de8b9d0`

⚠️ 파라미터가 패킷 스트림에 걸쳐 상속될 때, 선택은 **현재 패킷 필드 AND 보존된 이전 패킷 mode** 둘
다에서 유도한다. *현재 패킷만으로* 계산하면 패킷 경계의 상속을 놓친다.

AI는 config target을 현재 패킷 bit만으로 판단했다(`c_target_is_config = w_fifoDataPacket[17]`).
`de8b9d0`이 직전 패킷의 param mode(`r_pcmParamMode`)를 AND하여 "마지막 param duration이 이어지는
config 패킷에 적용되도록" 했다.

```verilog
// AI: 현재 패킷 bit만 (이전 패킷 상속 누락)
c_target_is_config = w_fifoDataPacket[17];
// de8b9d0 (fix): 보존된 이전 패킷 mode AND 현재 패킷 bit
c_target_is_config = ~r_pcmParamMode & w_fifoDataPacket[17];
```
**Detect: SIM**(다중 패킷 시퀀스 필요) · "selection이 current packet만 참조" = **STATIC smell**.
래칭 수명/상속 관계는 [→§1.DataLife]와 함께 분석.

### PF-4 — Mirror existing analogous interface (write-strobe 재발명 금지) — `f451926`

⚠️ streaming/FIFO map 엔트리를 추가할 때 **기존 유사 인터페이스를 그대로 mirror**하고, 새 write-strobe
규약을 발명하지 말 것. `f451926`의 subject가 곧 규칙: *"fix duration fifo bug for i2c register map →
**same as backtel fifo**"*. Duration FIFO를 backtel FIFO와 동일한 access/strobe/read 구조로 통일했다.
(write/read 대칭 audit은 [→§6.1](d).)
**Detect: STATIC**(기존 인터페이스와 구조 대조).

[→§1.DefImpl] 정의-구현 대조의 일부 — PF-1..PF-4는 **프로토콜 상태 신호**에 특화된 대조 규칙이다.

---

## 1.ClockTrace — Clock-Source & Async-Reset Provenance

**Taxonomy: T3 CLOCK_RESET_CDC · gated-clock & async-reset provenance · Detect: STATIC(provenance)/SIM(symptom)**

> **원칙:** `*Clk`/`*RefClk`라는 *이름*은 free-running을 보장하지 않는다. clock/reset 포트를 연결하기
> **전에** driver를 primary input/PLL/reset-tree까지 추적하라. 이것은 CDC *방식* 선택([→§1.CDC])이나
> reset *정책*([→§1.Reset]) 이전 단계 — clock/reset *출처(provenance)*의 검증이다 (중복 아님, 확장).

### CT-1 — Clock provenance (gated CKO를 logic clock으로 쓰지 말 것) — `86a1796`

⚠️ 모든 clock 포트는 연결 전에 driver를 primary input 또는 PLL/oscillator까지 추적한다. clock
gate/ICG(`todoc_prim_icg`, suffix `_g`, `BUFGCE`)의 CKO는, 그 gate가 닫혀도 **돌아가야 하는** logic을
clocking하면 안 된다. receiver/decoder는 **free-running source clock**을 쓴다.

AI는 back-tel decoder를 `w_askRefClk`로 clocking했는데, 이는 forward-link clock-gating FSM이 enable을
주는 `todoc_prim_icg u_askRefClk_icg`의 **gated CKO**다. back-tel decode는 forward data가 멈출 때 —
즉 이 clock이 멈추는 바로 그 순간 — 돌아야 한다. `86a1796`이 ungated `i_refGenClk`로 교체.

```verilog
// AI: 이름만 보고 gated CKO 연결 → forward data pause 시 decode freeze
.i_refClk(w_askRefClk),   // ~=10MHz   ← CKO of todoc_prim_icg (forward-link gated)
// 86a1796 (fix): ungated free-running source
.i_refClk(i_refGenClk),   // ~=10MHz   ← 항상 동작
```
**Detect: STATIC**(driver를 gate까지 추적) · freeze symptom은 **SIM**.

### CT-2 — Async reset/set provenance (조합 신호로 async reset 구동 금지) — `9a3c520`

⚠️ async reset/set 입력은 **reset-tree 또는 REGISTERED 신호로만** 구동한다. 디코드된 clear는
`r_fifoClr <= c_fifoClr`처럼 **register한 뒤** `i_rst_n`에 묶는다. "논리적으로 올바른 level"과
"async reset로 쓸 만큼 glitch-free"는 다르다.

AI는 FIFO의 async reset 핀을 `always @(*)` 조합 출력 `c_fifoRstEn`으로 직접 구동했다. `9a3c520`이
이를 registered `r_fifoRstEn`/`r_fifoClr`로 바꿨다 (sync mode 비정상 종료 시 FIFO clear 기능).

```verilog
// AI: 조합 c_fifoRstEn 을 async reset 핀에 직접 (glitch 위험)
.i_rst_n(i_rst_n & ~c_fifoRstEn),
// 9a3c520 (fix): registered 신호로 교체
.i_rst_n(i_rst_n & (~r_fifoRstEn & ~r_fifoClr)),
//   r_fifoRstEn <= c_fifoRstEn;  (askState FF 블록)
//   r_fifoClr   <= c_fifoClr;    (fifoRd FSM 블록)
```
**Detect: STATIC** — async pin이 `always @(*)` 식에 묶였는지 읽기로 검출.

### CT-3 — Cross-mode enable/clear (모든 mode에서 동작하도록) — `9a3c520`

⚠️ 여러 mode를 가로지르는 블록은 **mode-enable/clear 입력**을 가져 모든 mode에서 정의된 동작을 한다.
`9a3c520`은 mode-exit(abrupt)에서 FIFO를 flush하는 `c_fifoClr` 경로를 FSM의 IDLE 천이마다 추가하여,
sync mode를 갑자기 빠져나가도 stale 데이터가 남지 않게 했다 (mode-gated buffer flush). FSM corner의
flush/abort 전이 일반 규칙은 별개 — 여기서는 *clear 입력의 provenance*가 핵심.
**Detect: STATIC**(mode-clear 입력 존재 여부) · stale-data symptom은 **SIM**.

[→§1.CDC] CDC 방식 선택 / [→§1.Reset] reset 정책 — CT-1..CT-3은 그 앞단의 **출처 추적**으로,
중복이 아니라 선행 검증 단계다.

---

## 2. Always 블록 분리 체계

### 블록 유형

| 블록 유형 | 용도 | 문법 | 합성 결과 | Prefix |
|----------|------|------|----------|--------|
| `always_ff` | 순차 로직 (레지스터) | `@(posedge i_clk)` | Flip-flop | `r_` |
| `always_comb` | 조합 로직 | `always_comb` | Combinational | `c_` |
| `always_latch` | 래치 (피해야 함) | `always_latch` | Latch | - |

### 분리 원칙

**최우선 기준: 가독성과 회로 동작 파악 용이성**

**필수:**
- 동일 신호를 여러 always에서 할당 금지
- always_ff에서는 `<=` (non-blocking)
- always_comb에서는 `=` (blocking)

**권장 (유연 적용):** 하나의 always → 하나의 출력, 순차/조합 로직 분리

### 핵심 철학: 가독성이 최우선

"제어구조 분리"나 "순차/조합 분리"는 가독성을 위한 **수단**이지 목적이 아님. 전체 회로의 동작을 한눈에 파악할 수 있는가? 관련 로직이 흩어져서 오히려 이해하기 어려워지지 않는가? — 분리가 가독성을 해친다면 합치는 것이 정답.

### 판단 기준

| 질문 | YES → | NO → |
|------|-------|------|
| 하나의 always로 작성 시 회로 동작이 한눈에 파악되는가? | 합쳐서 작성 | 분리 고려 |
| 분리하면 관련 로직이 흩어져서 이해하기 어려워지는가? | 합쳐서 작성 | 분리 고려 |
| 코드 리뷰어가 전체 동작을 쉽게 이해할 수 있는가? | 현재 방식 유지 | 개선 필요 |

### 상황별 가이드

| 상황 | 권장 스타일 | 이유 |
|------|-------------|------|
| 단순 로직, 신호 간 관계 밀접 | **통합형** | 전체 동작 한눈에 파악 |
| FSM capture, Pipeline | **통합형** | 단순 구조, 관련성 높음 |
| 관련 카운터 그룹 | **통합형** | 논리적 연관, 유사 구조 |
| 복잡한 조건 로직 | 분리형 권장 | 각 로직 독립적 이해 |
| 서로 다른 기능 블록 | **반드시 분리** | 모듈성, 재사용성 |

**선택 가이드:**
- 로직이 단순하고 신호 간 관계가 밀접 → **통합형** 선호
- 로직이 복잡하거나 독립적으로 변경될 가능성 → **분리형** 선호

허용 사례(통합형 1-4) 및 분리 권장 코드 예제: `references/always-block-patterns.md` 참조

---

## 3. 사이클 분석 (Cycle Analysis)

### 개념

사이클 분석은 **각 신호가 어느 클럭 에지에서 값이 결정되는지** 추적하는 것.
- 조합 로직: 같은 사이클 내에서 즉시 반영
- 순차 로직: 다음 클럭 에지에서 반영 (1 cycle delay)

### 사이클 표기법

코드 작성/분석 시 주석으로 사이클 명시: `[Cycle N]`, `[Cycle N+1]`, `[same]`

전체 파이프라인 예시, 타이밍 다이어그램, 표기법 상세: `references/cycle-analysis.md` 참조

### 사이클 분석 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | 각 레지스터의 유효 사이클이 명시되었는가? [→§3] |
| ☐ | 조합 로직이 같은 사이클임을 표시했는가? [→§3] |
| ☐ | 파이프라인 단계별 지연이 일치하는가? [→§3] |
| ☐ | valid/data 신호의 사이클이 정렬되었는가? [→§3] |

---

## 3.1 Synchronous-Read Latency & Read-Data Handshake [→§3]

**Taxonomy T4 (TIMING_CYCLE).** LLM은 FIFO/RAM을 "`pop()`이 지금 값을 돌려주고 그대로 유지되는 소프트웨어 큐"로
모델링한다. **synchronous-read 1-cycle 레지스터드 출력 지연**과, **read pointer가 전진하는 순간 출력이 바뀐다**는
사실을 내부 표상에 갖고 있지 않다. 그래서 `rd_en`과 같은 사이클에 read data를 샘플링하거나, "read는 N cycle 걸린다"를
data-valid/ack 핸드쉐이크가 아니라 고정 상수(`_d[N]`)로 인코딩한다.

이 절은 §3 사이클 분석의 *메모리 read 전용* 확장이다. §3은 "각 신호가 어느 에지에서 결정되는가"를 다루고,
여기서는 그중 **registered-read 출력**이라는 특정 위험 패턴의 규칙을 고정한다.

### 규칙

| # | 규칙 | 검출 | 근거 commit |
|---|------|------|-------------|
| R1 | synchronous-read 메모리/FIFO에서 `rd_en`을 어서트한 **같은 state**에서 그 read data를 절대 샘플링하지 않는다. | **[SIM]** (정적 smell: `rd_en=1`과 동일 분기에서 출력 비트 테스트) | `05a53c5`,`daad643` |
| R2 | read를 **issue/check 두 단계로 분리** — 발행 state 다음에 *registered-read wait state* 를 두고, 등록된 enable(`r_*RdEn`)이 관측된 뒤에 데이터를 판별한다. | **[SIM]** | `daad643`,`f77e3c9` |
| R3 | 여러 사이클에 걸쳐 소비되는 read data는 **holding register**에 래칭하여 read pointer 전진과 무관하게 안정 유지 [→§1.DataLife]. | **[SIM]** | `05a53c5` |
| R4 | `rd_en`은 **single-cycle pulse** — 등록된 enable이 관측되면 즉시 deassert하여 double-pop 방지. | **[STATIC]** smell (`rd_en` default가 `r_rd_en` 홀드면 위험) | `f77e3c9`,`daad643` |
| R5 | cross-block / CDC read는 **소스가 내는 synchronized data-valid/ack**로 게이팅한다. 고정 `_d[N]` shift로 지연을 추정하지 않는다. 클럭 도메인을 넘으면 ack를 CDC 동기화 [→§1.CDC]. | **[SIM]** (STATIC smell: cross-domain read-valid로 쓰인 fixed `_d[N]`는 reject-on-sight, 그러나 latency 정합은 sim) | `090d3dd` |

### BAD (AI) / GOOD (fixed)

```verilog
// ──────────── BAD: ext_askEncoder.v (AI) ────────────
// rd_en과 같은 state에서 FIFO 출력을 판별 + 멀티사이클 mux가 live 출력을 직접 읽음
`TRF_READY: begin
    // ... (선행 if 분기 생략 — 발췌) ...
    else if (~w_fwd_fifo_empty) begin
        c_fifoRdEn = 1;                          // assert read
        if (w_fifoDataPacket[18]) begin          // ⚠️ R1: rd_en과 동일 사이클에 샘플 — 출력 아직 무효
            ...
        end
    end
end
case (r_tokenIndex)                              // token mux: tokenIndex 1..8 (여러 cell cycle 소비)
    'd1: c_triBitData = w_fifoDataPacket[17:15]; // ⚠️ R3: rd_ptr 전진 시 값이 바뀜 → 토큰 손상
    'd2: c_triBitData = w_fifoDataPacket[14:12];
    ...

// ──────────── GOOD: daad643 (issue/check split) + 05a53c5 (holding latch) ────────────
// R1/R2: 발행(IDLE) → registered-read wait(DATA) → 판별(CHK)
`FIFO_RD_IDLE: begin                              // 1
    if (~w_fwd_fifo_empty && ~r_onTransfer) begin
        c_fifoRdEn   = 1;                         // ✅ R4: 한 사이클만 펄스
        c_fifoRdState = `FIFO_RD_DATA;
    end
end
`FIFO_RD_DATA: begin                              // 2  ── registered-read wait state
    if (r_fifoRdEn) c_fifoRdState = `FIFO_RD_CHK; // ✅ R2: 등록 enable 관측 후 전진
end
`FIFO_RD_CHK: begin                               // 4  ── 이제 FIFO 출력 유효
    if (w_fifoDataPacket[18]) c_fifoRdState = `FIFO_RD_SQSH;  // ✅ R1
    else                      c_fifoRdState = `FIFO_RD_XFR;
end

// R3: 멀티사이클 소비 데이터는 holding register에 래칭 (05a53c5)
always @(posedge i_cellClk or negedge i_rst_n)
    if (~i_rst_n)        r_fifoDataPacket <= 0;
    else if (r_fifoRdEn) r_fifoDataPacket <= w_fifoDataPacket;  // ✅ 안정 유지
case (r_tokenIndex)
    'd1: c_triBitData = r_fifoDataPacket[17:15]; // ✅ token 사이클 내내 안정
    ...
```

```verilog
// ──────────── R5: 고정 _d[N] 대신 per-source data-valid ack (090d3dd) ────────────
// BAD (AI): 3-deep shift register로 read latency를 "3"으로 가정
reg [2:0] r_data_rd_en_d;
r_data_rd_en_d <= {r_data_rd_en_d[1:0], r_data_rd_en};
`DATA_LOAD: if (r_data_rd_en_d[2]) c_txData = i_dataIn; // ⚠️ 소스별 실제 지연을 무시

// GOOD: 소스가 내는 ack로 게이팅, 도메인 넘는 LUT는 CDC 동기화
`DATA_LOAD: if (i_data_rd_ack) c_txData = i_dataIn;     // ✅ 실제 소스 ack
//   register read : c_data_rd_ack = i_data_rd_en;            (on-chip, same-cycle)
//   FIFO read     : c_data_rd_ack = r_fifo_rd_pass;
//   LUT (cellClk) : c_data_rd_ack = i_dur_seq_rd_ack_cdc;    via ext_if_cdc (cellClk→i2cClk)
```

> ⚠️ `090d3dd`에서 LUT(Duration sequence) read는 `i2cClk`이 아니라 `cellClk` 도메인에서 응답한다. 그래서
> ack(`o_dur_seq_rd_ack_cdc`)를 `ext_if_cdc`로 CDC 동기화한 뒤 사용한다 — 고정 `_d[N]`로는 이 가변·교차도메인
> 지연을 절대 맞출 수 없다(R5).

### 체크리스트

- [ ] **[SIM]** `rd_en` 어서트와 동일 state에서 그 read data를 샘플링하지 않는가? [→§3] (R1)
- [ ] **[SIM]** synchronous-read에 registered-read wait state(issue/check 분리)가 존재하는가? (R2)
- [ ] **[SIM]** 멀티사이클 소비 데이터를 holding register에 래칭했는가? [→§1.DataLife] (R3)
- [ ] **[STATIC]** `rd_en`이 single-cycle pulse인가 (default 0, 발행 state에서만 1)? (R4)
- [ ] **[SIM]** cross-block/CDC read가 fixed `_d[N]`이 아닌 synchronized data-valid/ack로 게이팅되는가 (fixed `_d[N]`은 STATIC smell)? [→§1.CDC] (R5)

---

## 4. Signal Naming Convention

### Prefix 규칙

| Prefix | 용도 | 사이클 특성 | 예시 |
|--------|------|------------|------|
| `i_` | 입력 포트 | Cycle N (외부 결정) | `i_data`, `i_valid` |
| `i_` | **클럭/리셋** | 입력 신호 | `i_clk`, `i_rst_n` |
| `o_` | 출력 포트 | Cycle N+k (내부 결정) | `o_result`, `o_ready` |
| `w_` | 와이어 (내부 연결) | 연결용 | `w_adder_out` |
| `r_` | 레지스터 (순차) | **Cycle N+1** | `r_state`, `r_counter` |
| `c_` | 조합 로직 출력 | **Same cycle** | `c_next_state`, `c_sum` |

### ⚠️ Clock/Reset 네이밍

클럭과 리셋도 입력 신호이므로 `i_` prefix: `i_clk`, `i_rst_n`

### Boundary Scan Chain (BSC) 네이밍

`_a` (BSC 입력) / `_z` (BSC 출력) postfix — BSC 모듈 포트에서만 사용. 상세: `references/naming-examples.md`

### 모듈 코드 구조 (영역 분리)

모듈 파일은 다음 3영역을 순서대로 배치:
1. **포트 선언** — `module`, `input`/`output`/`inout` 포트
2. **내부 선언** — `reg`, `wire`, `localparam`, `parameter` (로직 없음)
3. **Body** — `assign`, `always`, 인스턴스 등 실제 로직

**기존 코드 수정 시 배치 규칙**:
- 추가 신호는 **관련 기존 신호 근처**에 선언 (파일 끝에 무분별하게 추가하지 않음)
- Body 내 로직은 **관련 기존 로직 영역**에 추가 (독립 블록이면 해당 기능 근처에 배치)
- 선언 순서는 **Body에서 사용되는 순서**와 대응 — 리뷰어가 선언→사용을 순차적으로 추적 가능
- 목표: 코드 리뷰어가 관련 신호와 로직을 **직관적으로 찾을 수 있는 구조**

---

## 5. Module/Parameter Naming

### 규칙

| 항목 | 스타일 | 예시 |
|------|--------|------|
| **Module** | lowercase_with_underscores | `uart_rx`, `adc_controller` |
| **Parameter** | UPPER_CASE | `DATA_WIDTH`, `FIFO_DEPTH` |
| **Instance** | u_<module_name> | `u_uart_rx`, `u_fifo` |

### 예시

```verilog
module fifo_buffer #(
    parameter DATA_WIDTH = 8,        // UPPER_CASE
    parameter FIFO_DEPTH = 16,
    parameter ALMOST_FULL_THRESH = 12
)(
    input  wire                  i_clk,
    input  wire                  i_rst_n,
    input  wire [DATA_WIDTH-1:0] i_wdata,
    output wire [DATA_WIDTH-1:0] o_rdata
);
```

---

## 6. Top Integration Wire Naming

### 규칙

**형식**: `w_<source_instance>_<output_port_name>`

- 보내는 쪽 인스턴스명 + 출력 포트명 **전체** 포함
- 포트명의 `o_` prefix도 그대로 유지
- **예외**: Top 출력으로 직결되는 신호는 `o_` 포트명 그대로 연결

상세 예시: `references/naming-examples.md` Top Integration 섹션 참조

### 네이밍 예시

| 인스턴스 | 출력 포트 | 와이어 이름 |
|---------|----------|------------|
| u_proc | o_result | `w_u_proc_o_result` |
| u_proc | o_done | `w_u_proc_o_done` |
| u_fifo | o_rdata | `w_u_fifo_o_rdata` |
| u_uart | o_tx_data | `w_u_uart_o_tx_data` |

---

## 6.1 Feature Integration Completeness (End-to-End Signal Audit)

**Taxonomy: T2 PORT_INTEGRATION · "declared somewhere ≠ wired end-to-end & bidirectional"**

> **원칙:** 신호를 *선언/사용*했다는 것은 *모든 계층·빌드 매니페스트·read+write 양방향*에 연결되었다는
> 뜻이 아니다. LLM은 producer와 consumer를 별도 하위작업으로 그럴듯하게 만들고 **루프를 닫지 않는다**.
> 구현 직후 아래 audit를 **반드시** 수행한다. 와이어 네이밍 규칙 자체는 [→§6] 참조 — 여기서는 *연결
> 완결성*을 검증한다.

### Audit 규칙

| # | 규칙 | Detect | Taxonomy / Commit |
|---|------|--------|-------------------|
| (a) | 신규 `.v` 파일은 빌드 filelist에 **실제 경로**로 등록되고 elaboration이 unresolved instance 0개로 통과 | **STATIC** | T2 · `759af25`,`b26d292` |
| (b) | 신규 registered output은 **≥1 consumer**(grep로 확인). fan-out 0 = dead feature | **STATIC** | T2 · `dcfa6d2`,`a3be708` |
| (c) | 신규 mode input은 **실제 datapath 신호를 바꿔야** 함. 기능 포트에 상수(`1'b0`/`1'b1`) = red flag | **STATIC** | T2 · `f785a05`,`d1bd162` |
| (d) | register/FIFO/LUT 대칭성: write **AND** read 경로 + 유사 기존 FIFO와 **동일한 CDC req→ack** + 정의된 non-zero read-back | **STATIC** | T2 · `f451926`,`090d3dd`,`1851ac0` |
| (e) | host가 polling하는 status flag는 datapath consumer뿐 아니라 **register-map status 그룹 경로**를 가짐 | **STATIC** | T2 · `768ff83` |
| (f) | 신규 addressing/offset/제어 pin은 **모든 계층(top→main→leaf)**에 threading | **STATIC** | T2 · `a3be708` |
| (g) | open-drain pad: disable 시 **release level을 구동**하여 pad가 float. OD 출력을 data 신호에 직접 묶지 말 것 | **STATIC** | T2 · `0ff1f49` |

### (a) Filelist + elaboration — `759af25`/`b26d292`

새 모듈 `ext_fwd_fifo.v`가 `d_filelist.f`에 없어 빌드가 깨졌고(`759af25`), 추가 후에도 **잘못된 폴더
경로**(`d_top/mdl/` ← 실제는 `d_enc/mdl/`)로 등록되어 다시 수정(`b26d292`)했다.

```diff
# 759af25 — 누락된 파일 추가
+$PROJ_ROOT/design/digi/d_top/mdl/ext_fwd_fifo.v
# b26d292 — 실제 경로로 정정 (선언만으로는 부족, elaboration이 찾을 수 있어야 함)
-$PROJ_ROOT/design/digi/d_top/mdl/ext_fwd_fifo.v
+$PROJ_ROOT/design/digi/d_enc/mdl/ext_fwd_fifo.v
```
⚠️ 새 `.v`를 작성하면 **즉시** filelist 등록 + elaboration 확인. "파일을 만들었다 ≠ 빌드가 본다."

### (b) Zero fan-out = dead feature — `dcfa6d2`/`a3be708`

AI는 `ext_backTelInterface.v`에 `r_timer_active` 타이머를 만들었지만, 정작 활성화 출력
`o_backtel_dec_en`은 **레거시 조건 그대로** 두어 새 타이머를 **0번** 참조했다 → 기능 전체가 dead.
`dcfa6d2`가 출력 식에 타이머를 실제로 wiring했다.

```verilog
// AI (dead): 새 r_timer_active는 어디서도 소비되지 않음
assign o_backtel_dec_en = r_pwr_en_hs & r_nop_backtel_cdc[1] & r_forward_transfer_n_cdc[1];

// dcfa6d2 (fix): sync-xfr 모드에서 타이머를 실제 datapath로 연결
assign o_backtel_dec_en = r_pwr_en_hs & r_forward_transfer_n_cdc[1]
                        & (r_sync_xfr_en_hs ? r_timer_active : r_nop_backtel_cdc[1]);
// a3be708: 추가로 BT_LOGIC_CTRL_EN bit를 AND  → (r_timer_active & r_bt_logic_ctrl_en_hs)
```
✅ 검증: `grep -rn "<new_output_signal>"` → producer 외 consumer가 ≥1개인지 확인. 0이면 미통합.

### (c) 기능 포트의 상수 = red flag — `f785a05`/`d1bd162`

AI는 squash 모드를 지원한다며 `.i_btnop_sqsh_mode(1'b1)`를 **하드코딩**해 모드 포트를 상수에 묶었다
(`f785a05`). `d1bd162`가 이를 실제 PCM 레지스터 bit(`r_btnop_sqsh_mode <= i_reg_data[5]`)에서 나온
`w_btnop_sqsh_mode`로 교체하고 top→slave→register→enc/dec 전 계층에 threading했다.

```verilog
// f785a05 (red flag): 기능 모드 포트에 상수 → 호스트가 제어 불가, datapath 고정
.i_btnop_sqsh_mode(1'b1),
// d1bd162 (fix): 레지스터 bit로 trace → 0x09[5]에서 디코드된 실제 신호
.i_btnop_sqsh_mode(w_btnop_sqsh_mode),  // ← ext_pcmRegister: r_btnop_sqsh_mode <= i_reg_data[5]
```
⚠️ 기능 control/mode 포트에 묶인 모든 리터럴은 register bit 또는 top pin으로 **추적 가능해야** 한다.
clock-gate disable 같은 **물리적 상수**만 예외 ([→§1.ClockTrace] CT-3와 구분).

### (d) write/read 대칭 + read-back — `f451926`/`090d3dd`/`1851ac0`

Duration LUT는 처음에 write 경로만 있어 i2c read-back이 0을 반환했다. `f451926`가 backtel FIFO와
**동일한 구조로** read MUX를 추가했고, `090d3dd`가 누락된 CDC **read-ack**(`o_data_rd_ack`,
`i_dur_seq_rd_ack_cdc`)를 기존 FIFO와 동일한 req→ack로 맞췄으며, `1851ac0`가 RW 엔트리의
**read-back을 0이 아닌 실제 값**으로 정의했다.

```verilog
// 090d3dd — 유사 기존 FIFO와 동일한 read-ack 핸드쉐이크를 mirror (write-only로 짓지 말 것)
output o_data_rd_ack;                 input i_dur_seq_rd_ack_cdc;
assign o_data_rd_ack = r_data_rd_ack; // registered ack, i2cClk 도메인

// 1851ac0 — 쓰기 가능 엔트리는 정의된 non-zero read-back을 반환
//   AI: WO처럼 0 반환                          fix: 실제 RW 값 reflect
-'hE: r_rdDataReg[14] <= 8'h00;  // DUR_PUSH: WO → 0
+'hE: r_rdDataReg[14] <= {3'b0, r_dur_dir_addr[4:0]};  // DUR_CH_SET: RW read-back
+'hF: r_rdDataReg[15] <= r_config_dur[7:0];            // CONFIG_DUR: RW read-back
```
✅ I2C-accessible FIFO/LUT/register는 (1) write 경로, (2) read 경로, (3) 유사 기존 FIFO와 **동일한**
CDC req→ack, (4) spec상 write-only가 아니면 non-zero read-back — 4개 모두 존재해야 통합 완료.

### (e) status flag → register-map 경로 — `768ff83`

`w_timer_active`(BTNOP 타이머 active flag)는 datapath consumer만 있고 호스트가 polling할
register-map 경로가 없었다. `768ff83`가 top→i2cSlave→i2cRegisterInterface로 threading하여
status 그룹(`0x09`)에 매핑했다.

```verilog
// d_main:  .i_btnop_tmr_active(w_timer_active),   // top→leaf threading
// i2cRegisterInterface: status 그룹 bit에 매핑
'h9: r_rdDataReg[9] <= {1'b0, i_btnop_tmr_active, i_btnop_sqsh_mode, i_dur_fifo_ptr_reset,
                        i_fwd_fifo_clr, i_sync_req_clr_en, i_sync_interrupt_en, i_i2c_stop};
```
⚠️ 호스트가 읽어야 하는 모든 status flag는 datapath 소비처 외에 **register-map status 그룹**에도
경로가 있어야 한다.

### (f) pin threading top→main→leaf — `a3be708`

`BT_LOGIC_CTRL_EN`은 encoder(`o_bt_logic_ctrl_en`)에서 생성→ `ext_d_main`이 `w_bt_logic_ctrl_en`
와이어로 받아→ decoder(`.i_bt_logic_ctrl_en`)로 전달하고, top 출력 식까지 반영했다. **모든** 계층을
한 commit에서 닫는 것이 핵심.

```verilog
// a3be708 — encoder out → main wire → decoder in → top output, 한 번에 전 계층
wire w_bt_logic_ctrl_en;                                   // main 선언
.o_bt_logic_ctrl_en(w_bt_logic_ctrl_en),  // encoder
.i_bt_logic_ctrl_en(w_bt_logic_ctrl_en),  // decoder
assign o_backTel_pwr_en = w_backTel_pwr_en & (w_sync_xfr_en ? w_bt_logic_ctrl_en : 1'b1); // top
```

### (g) open-drain disable 시 float — `0ff1f49`

`o_stim_trig`를 open-drain pad로 만들면서, disable(`w_stim_trig_en==0`) 시 pad가 float하도록
**release level(`1'b1`)을 구동**해야 한다. OD 출력을 data 신호에 직접 묶으면 pad가 항상 구동된다.

```verilog
// 0ff1f49 — disable면 1'b1 (release) → OD pad floating, 아니면 data
assign o_stim_trig = (w_earpiece_pwr_ctrl_en == 1'b1) ? ((i_earpiece_det_n==0) ? 1'b1 : 1'b0)
                   : (w_stim_trig_en == 1'b0) ? 1'b1 : w_stim_trig;
```
(OD pad의 vendor 프리미티브 `SB_IO_OD` 사용 상세 → `lattice-fpga` skill.)

### 📋 Copy-paste Integration Audit Checklist

```text
# 신규 기능 구현 직후 — 모든 항목 PASS 전에는 기능 review로 넘어가지 않는다. (cd db/design)
[ ] (a) FILELIST   : 새 .v 마다  grep -n "<file>.v" d_filelist.f  → 실제 경로로 1줄 존재
                     elaboration(빌드/Verilator)에서 unresolved instance 0개
[ ] (b) FAN-OUT    : 새 registered output 마다  grep -rn "<o_signal>" .  → producer 외 consumer ≥1
                     (consumer 0 = dead feature → 출력 식에 신호를 실제로 연결)
[ ] (c) NO-CONST   : 모든 인스턴스의 .i_<mode>(...) 에 1'b0/1'b1 리터럴이 묶인 기능 포트 없음
                     (있으면 register bit / top pin 으로 trace)
[ ] (d) RW-SYM     : I2C/host-accessible FIFO·LUT·register 마다
                       - write 경로 존재 ?   - read MUX 경로 존재 ?
                       - 유사 기존 FIFO와 동일한 CDC req→ack 존재 ?
                       - RW 엔트리 read-back 이 0 아닌 실제 값 ? (WO면 spec에 명시)
[ ] (e) STATUS-MAP : host-polled flag 마다 register-map status 그룹(r_rdDataReg[...])에 매핑됨
[ ] (f) THREADING  : 새 pin 마다  top 선언 → main wire → leaf 포트  전 계층 연결 (grep로 각 계층 확인)
[ ] (g) OD-FLOAT   : open-drain 출력은 disable 시 release level 구동(float), data 직접 묶음 없음
```
[→§6] Top Integration Wire Naming (와이어 *이름* 규칙). 본 §6.1은 *연결 완결성*을 검증.

---

## 7. FSM Implementation

### 기본 규칙

| 항목 | 규칙 |
|------|------|
| **스타일** | 2-process (작성 시) |
| **타입** | Mealy machine 기본 |
| **인코딩** | One-hot (< 8 states), Binary (≥ 8 states) |
| **타이밍 크리티컬** | 출력 레지스터링 추가 |

### FSM 작성/분석 규칙

- **작성 시**: 항상 2-process 패턴만 사용 (일관성, 코드 리뷰 용이, 합성 예측 가능)
- **분석 시**: 모든 FSM 패턴 인식 (1/2/3-process, 다양한 코딩 스타일)

### 타이밍 크리티컬: 출력 레지스터링

Mealy 출력이 타이밍 크리티컬하면 `r_result_reg <= c_result;` 로 1 cycle 추가.

전체 FSM 템플릿, 2/3-process 패턴, 출력 레지스터링: `references/fsm-patterns.md` 참조
FSM 사이클 다이어그램: `references/fsm-patterns.md` 참조

---

## 7.1 FSM Corner Enumeration & Deadlock Avoidance [→§7]

**Taxonomy T5 (FSM_CORNER_DEADLOCK).** LLM은 nominal happy-path 흐름 중심으로 FSM을 짜고, **이 설계 고유의
`state × async-event` 행렬**을 열거하지 않는다. 누락되는 셀: 시퀀스 도중 패킷 도착, 모드-disable/abort flush,
FIFO empty/full, illegal one-hot state, 그리고 퇴화 입력 `count==0` load. "done까지 대기" 분기를 추가할 때도
done이 slow-domain 동기화기가 관측하기 전에 도착하는 퇴화 케이스를 추론하지 못해 **deadlock**을 만든다.

§7은 2-process/Mealy/인코딩 등 *구조* 규칙을 다룬다. 이 절은 그 위에 **corner 열거 의무**와 **deadlock 회피**를
고정한다.

### 규칙

| # | 규칙 | 검출 | 근거 commit |
|---|------|------|-------------|
| R1 | FSM 작성 전 **state × async-event 매트릭스**를 만들고 모든 셀에 명시적 정의 전이를 둔다(아래 템플릿). | **[STATIC]** (매트릭스 누락 셀 = 미정의 동작) | methodology gate (대표 누락 셀: `2ebd51f` zero-load, `9a3c520` abort-flush) |
| R2 | **zero-duration load**(`count==0`)는 한 틱만 active 처리 — `active <= 1'b1`(값 0/1 모두 1 cycle active). | **[SIM]** (directed test `val=0`) | `2ebd51f` |
| R3 | counter 만료 비교는 `==`(`count==1`)이 아니라 **`<=`** 경계 비교 — min/zero load도 정확히 1 expiry edge. | **[STATIC]** smell (단말 카운트 `==`는 리뷰 flag) + **[SIM]** | `2ebd51f` |
| R4 | cross-domain active level을 기다리는 state는 그 level이 **dest ≥2 cycle 유지** 보장되거나 **timeout/abort**가 있어야 한다. 동기화 전 전이 금지. | **[SIM]** (정적 smell: 무-timeout 교차도메인 대기) | `b353ad3`,`2ebd51f` |
| R5 | 타이머 동작 중 도착한 패킷은 `r_xfr_pending`류 **defer 부킹**으로 기억했다가 만료 후 처리 [→§1.DataLife]. | **[SIM]** | `0e5a566`,`20e59ca` |
| R6 | 모드-gated 버퍼는 mode-exit/abort마다 **flush(clear) 경로**를 갖는다. flush 신호는 **레지스터링 후** FIFO async reset에 인가(combinational 직결 금지) [→§1.Reset]. | **[STATIC]** (async reset 소스 provenance) + **[SIM]** (flush 커버리지) | `9a3c520` |

### state × async-event 매트릭스 (template)

행=FSM state, 열=async-event. 각 셀에 **정의된 전이/출력**을 채운다. 빈 셀은 곧 미정의 동작(T5 버그).

| State \ Event | new packet (mid-seq) | mode-disable/abort | FIFO empty | FIFO full | illegal/default | zero/min load |
|---|---|---|---|---|---|---|
| `<S_load>`  | `<...>` | `<flush→IDLE>` | `<...>` | `<...>` | `<flush→IDLE>` | **one-tick active (R2)** |
| `<S_wait>`  | `<defer (R5)>` | `<→IDLE>` | `<...>` | `<...>` | `<flush→IDLE>` | **`<=` expiry (R3)** |
| `<default>` | — | — | — | — | **`<c_fifoClr=1;→IDLE>`** | — |

**채워진 실제 예시 — `ext_askEncoder.v` FIFO Read FSM (commit 근거 표기):**

| State \ Event | new packet (mid-seq) | mode-disable/abort (`~i_sync_xfr_en`) | FIFO empty | FIFO full | illegal/default | zero/min load |
|---|---|---|---|---|---|---|
| `FIFO_RD_IDLE` | pop→DATA; `r_xfr_pending`→XFR `20e59ca` | stay IDLE | stay IDLE | — | →IDLE+flush | — |
| `FIFO_RD_DATA` | `r_fifoRdEn`→CHK (R2) | (CHK/SQSH에서 처리) | — | — | →IDLE+flush | — |
| `FIFO_RD_CHK` | PARAM+timer→WAIT, set `c_xfr_pending` `0e5a566`/`20e59ca` | — | — | — | →IDLE+flush | — |
| `FIFO_RD_SQSH` | nxt BTNOP→re-pop | else→IDLE+`c_fifoClr` `9a3c520` | →TMR | — | →IDLE+flush | — |
| `FIFO_RD_TMR` | nxt PARAM→WAIT | else→IDLE+`c_fifoClr` `9a3c520` | →RDY | — | →IDLE+flush | btnop timer=0 → one-tick active `2ebd51f` |
| `FIFO_RD_RDY` | new wr→re-pop | else→IDLE+`c_fifoClr` `9a3c520` | timer expire→IDLE | — | →IDLE+flush | — |
| `FIFO_RD_WAIT` | — | →IDLE | — | — | →IDLE+flush | timer expire (`<=`) `2ebd51f` |
| `default` | — | — | — | — | `c_fifoClr=1;`→IDLE `9a3c520` | — |

### BAD (AI) / GOOD (fixed)

```verilog
// ──────────── BAD: ext_backTelInterface.v (AI) — R2/R3 deadlock ────────────
r_timer_active <= (i_btnop_timer_val != 8'd0); // ⚠️ R2: val==0 → active 절대 어서트 안 됨
...
if (r_timer_count == 8'd1) begin               // ⚠️ R3: exact-match expiry
    r_timer_count  <= 8'd0;
    r_timer_active <= 1'b0;
end
// 결과: val==0이면 slow-cellClk 2-FF 동기화기 w_timer_active_cdc가 high를 못 봄 → read FSM 영구 대기

// ──────────── GOOD: 2ebd51f ────────────
r_timer_active <= 1'b1;                         // ✅ R2: 0/1 모두 1 cycle active
...
if (r_timer_count <= 8'd1) begin                // ✅ R3: <= 경계 비교 (timer 0도 포함)
    r_timer_count  <= 8'd0;
    r_timer_active <= 1'b0;
end
```

```verilog
// ──────────── R4: 교차도메인 active 관측 후 전이 (b353ad3) ────────────
// BAD: BTNOP 처리 후 무조건 전이
c_btnop_exec_pulse = 1;
c_transferState = `TRF_READY;                   // ⚠️ w_timer_active_cdc 아직 low일 수 있음
// GOOD: 동기화된 active level 관측 후에만 전이
c_btnop_exec_pulse = 1;
if (w_timer_active_cdc) begin                   // ✅ dest 도메인에서 active 확인
    c_transferState = `TRF_READY;
end

// ──────────── R5: defer 부킹 (0e5a566 + 20e59ca) ────────────
else if (w_timer_active_cdc) begin              // PARAM이 timer 동작 중 도착
    c_xfr_pending = 1;                          // ✅ 보류 기록
    c_fifoRdState = `FIFO_RD_WAIT;
end
...
`FIFO_RD_IDLE: begin
    if (r_xfr_pending) begin                    // ✅ 만료 후 보류분 처리
        c_xfr_pending = 0;
        c_fifoRdState = `FIFO_RD_XFR;
    end
    else if (~w_fwd_fifo_empty && ~r_onTransfer) ...

// ──────────── R6: mode-exit flush, 레지스터링 후 async reset 인가 (9a3c520) ────────────
else begin                                      // abort/fallback
    c_fifoClr = 1;                              // ✅ flush 경로
    c_fifoRdState = `FIFO_RD_IDLE;
end
// r_fifoClr <= c_fifoClr; (레지스터링) 후:
.i_rst_n(i_rst_n & (~r_fifoRstEn & ~r_fifoClr)) // ✅ 등록된 flush를 reset에 — combinational 직결 아님
```

### 필수 directed tests

| 테스트 | 기대 | 검출 | commit |
|--------|------|------|--------|
| timer/count load = 0 | 정확히 1 expiry edge, FSM 비-hang | **[SIM]** | `2ebd51f` |
| timer 동작 중 PARAM 패킷 도착 | `xfr_pending`으로 보류 → 만료 후 전송 | **[SIM]** | `0e5a566`,`20e59ca` |
| 모든 `FIFO_RD_*`에서 `i_sync_xfr_en` 1→0 | FIFO flush 후 IDLE 복귀, 잔여 데이터 없음 | **[SIM]** | `9a3c520` |
| 교차도메인 timer-active 미관측 | `w_timer_active_cdc` 대기, premature 전이 없음 | **[SIM]** | `b353ad3` |
| illegal one-hot state 주입 | default 분기 flush + IDLE 복구 | **[SIM]** | `9a3c520` |

> ⚠️ R4의 "dest ≥2 cycle 유지"는 §1.CDC의 2FF 캡처 조건과 동일 판정 기준이다 — 교차도메인 대기 state는
> 사실상 1-bit level CDC이므로 [→§1.CDC] 테이블로 유지 사이클을 검증한다. 여기서는 *FSM이 그 level을 영원히
> 기다릴 수 있는가*(timeout 부재)를 추가로 본다.

---

## 8. Verification 연계

### SVA Assertion

RTL 동작을 사이클 정확도로 검증하는 SystemVerilog 구문:

```verilog
// 프로토콜 체크: valid 후 N 사이클 내 ready 응답
assert property (@(posedge i_clk) disable iff (!i_rst_n)
    i_valid |-> ##[1:10] o_ready
) else $error("Ready timeout!");
```

복합 시퀀스, cover property, 시스템 SVA 패턴: `references/covergroup-patterns.md` 참조

### Coverage

| 분류 | 생성 방식 | 목표 |
|------|----------|------|
| Code Coverage | 자동 (implicit) | 95% |
| Functional Coverage | 수동 (explicit) | 90% |
| Assertion Coverage | 수동 (explicit) | — |

Coverage 워크플로우: `references/coverage-methodology.md`, 문법 패턴: `references/covergroup-patterns.md` 참조
실전 예제 (APB3, UART, Datapath, SoC): `references/coverage-examples.md` 참조

---

## 9. 코드 생성 워크플로우

RTL 코드 작성/수정 시 다음 단계를 따른다:

0. **모듈 분석서 확인** [→§12] — `.ai/analysis/{module}.analysis.md` 존재 여부 확인. 없으면 먼저 작성. 기존 수정이면 분석서의 FSM/신호/타이밍 정보를 참조하여 영향 범위 파악.
   - **0.5 파일 헤더 확인** [→§13] — 파일 상단 doxygen 헤더 존재 확인. 없으면 생성. 수정 시 `[revision history]`에 변경 항목 1줄 추가.
1. **요구사항 분석** — 입출력 정의, 타이밍 요구사항 파악
2. **사이클 맵 작성** — 어떤 처리가 몇 사이클에 발생하는지 명시
3. **블록 분할** — always 블록별 책임 할당
4. **코드 작성** — 사이클 주석과 함께 작성
   - **4.5 Bit-Width 검증** [→§1.BitWidth] — 모든 sized 변수: max(value) < 2^W 확인, localparam/parameter 파생 관계 교차 검증
5. **합성 체크** — `references/synthesis-check.md` 참조
6. **분석서 갱신** [→§12] — 변경된 FSM/신호/전이를 분석서에 반영

---

## 10. 코드 리뷰 체크리스트

코드 리뷰 시 `references/review-checklist.md` 참조. 핵심 항목:

### 합성 관련
- [ ] Latch 유발 코드 없음 (기본값 할당 또는 if/case 완전성) [→§1,§7]
- [ ] 리셋 정책: 제어 신호=리셋 있음, 데이터 경로=리셋 없음 [→§1.Reset]
- [ ] CDC: Slow→Fast=2FF/Pulse, Fast→Slow=Handshake 또는 2FF(장기유지) [→§1.CDC]
- [ ] Blocking/Non-blocking 할당 적절성 [→§2]
- [ ] Bit-Width Safety: sized 변수의 max value < 2^W, localparam unsized 권장 [→§1.BitWidth]

### 타이밍 관련
- [ ] 사이클 타이밍 정확성 [→§3]
- [ ] data/valid 정렬 (리셋 정책에 맞게 분리) [→§3,§1.Reset]
- [ ] 타이밍 크리티컬 경로 레지스터링 [→§7]

### 코딩 스타일
- [ ] 네이밍 규칙 준수 (i_, o_, w_, r_, c_, Top wire, BSC) [→§4,§5,§6]
- [ ] 모듈 구조: 포트→선언→Body 영역 분리, 추가 신호는 관련 신호 근처 배치 [→§4]
- [ ] always 블록: 필수 규칙 준수 + 유연성 원칙 (가독성 최우선) [→§2]
- [ ] 사이클 주석 명시 [→§3]
- [ ] 파일 헤더 주석: doxygen 스타일 헤더 존재, 수정 시 `[revision history]` 항목 추가 [→§13]

### 기능 관련
- [ ] 리셋 시 초기값 정확 [→§1.Reset]
- [ ] 에지 케이스 처리 (오버플로우, 언더플로우)
- [ ] FSM: 2-process, Mealy 기본, One-hot(<8)/Binary(≥8) [→§7]
- [ ] 리소스 최소화: 기존 인스턴스 재사용 검토, 불필요 포트 제거 [→§1.Resource]
- [ ] Combinational depth: FSM state 내 조건 깊이 적정, 타이밍 정렬 유지 [→§1.Timing]
- [ ] 래칭 보존: pending 레지스터가 중간 경로에서 덮어써지지 않는지 확인 [→§1.DataLife]
- [ ] 정의-구현 대조: 각 FSM state가 설계 정의와 1:1 일치하는지 확인 [→§1.DefImpl]
- [ ] 동기 read 타이밍: rd_en과 동일 사이클 샘플 금지, holding latch, ack 기반 cross-block read [→§3.1]
- [ ] FSM corner: state×async-event 매트릭스 전 셀 정의, zero-load/abort-flush/교차도메인 timeout [→§7.1]
- [ ] 원형 FIFO: zero-extend wrap 비교, ~full write guard, 동시 r/w semaphore [→§1.Pointer]
- [ ] 통합 완결성: filelist 등재, output fan-out≥1, register write/read 대칭, 기능 포트 상수 금지 [→§6.1]
- [ ] 프로토콜 충실도: detected 신호 clear 금지, mode-conditioned 분기, 패킷 상속 [→§1.Protocol]
- [ ] clock/reset provenance: gated CKO 금지, async reset는 registered 신호로 [→§1.ClockTrace]
- [ ] lint gate 통과(default_nettype none), FPGA RAM 1-write-port/ramstyle/case-MUX [→§11.1]

---

## 11. Verilator Lint

정적 분석 도구. OSS CAD Suite에 포함 (verilator 5.047):

```bash
export PATH="/c/oss-cad-suite/oss-cad-suite/bin:/c/oss-cad-suite/oss-cad-suite/lib:$PATH"
verilator --lint-only -Wall --top-module <top> <files>
```

주요 Warning 유형, 억제 방법: `references/verilator-guide.md` 참조

---

## 11.1 Mandatory Lint Gate & FPGA RAM Inference

**Taxonomy: T7 STRUCTURE_STYLE / T8 FPGA_RAM · Detect: STATIC**

> **원칙:** Lint는 "있으면 좋은 도구"가 아니라 **기능 review 이전의 GATE**다 ([→§11]을 도구에서
> 게이트로 승격). 모든 파일은 `` `default_nettype none ``으로 compile + lint를 통과해야 하며, 아래
> 항목은 **build-blocking error**로 취급한다. 이 게이트를 통과하지 못한 코드는 기능 검토 대상이 아니다.

### Lint Gate (T7) — build-blocking 항목 — `72b2219`

`72b2219`("fix syntax error")의 AI 코드는 `` `default_nettype none `` compile이면 **전부 거부**됐을
것들이다. lint 게이트가 없어서 shipped 됐다.

| 항목 | AI (reject) | Fix | 근거 |
|------|-------------|-----|------|
| implicit net (prefix 누락) | `o_fifo_btnop = sync_xfr_en && ...` | `i_sync_xfr_en && ...` | undriven net → BTNOP flag stuck 0 |
| base 없는 sized literal | `{i_pcmPayload[16:0], 1'0}` | `... 1'b0}` | `` '<digit> `` 불법 |
| empty if-branch | `if(r_fifo_btnop_cdc[1]) else if(...)` | `if(r_fifo_btnop_cdc[1]); else if(...)` | then-branch 비어 dangling |
| begin/end 없는 multi-stmt | `if(cond)` 아래 2문장 무괄호 | `if(cond) begin ... end` | 두번째 문장 무조건 실행 |

```verilog
// 72b2219 — implicit undriven net: 포트는 i_sync_xfr_en 인데 prefix 빠뜨림
-assign o_fifo_btnop = sync_xfr_en && r_nopBackTel;
+assign o_fifo_btnop = i_sync_xfr_en && r_nopBackTel;

// 72b2219 — base 없는 literal + begin/end 누락 동시 수정
-if (r_fifo_btnop_cdc[1])
-    c_rawDataPacket[17:0] = {i_pcmPayload[16:0],1'0};
+if (r_fifo_btnop_cdc[1]) begin
+    c_rawDataPacket[17:0] = {i_pcmPayload[16:0],1'b0};
+end
```

추가 build-blocking 항목 (모두 **STATIC**, [→§11] 게이트로 enforce):
- **implicit net / undeclared id** (i_/o_/w_ prefix drop) — `72b2219` · RHS id를 선언된 port/reg/wire와 prefix-exact 대조 [→§4]
- **out-of-range bit index** — `f451926` · 선언 범위 밖 bit 접근 (아래 §11.1 RAM 예와 동일 commit, T9 연계 [→§1.BitWidth])
- **width mismatch / 미정의 동작** — sized 변수 max value < 2^W [→§1.BitWidth]

```verilog
// f451926 — 선언은 reg [16:0] r_pktData,c_pktData (bit 0..16) 인데 bit[17] 접근 → 무성 drop
//   header 주석엔 o_pcm_payload[17:0] with BTNOP flag[17] (18-bit 의도) — 선언과 불일치 (T9)
-c_pktData[17] = 1'b1; // BTNOP flag   ← [16:0]에 존재하지 않는 bit, lint가 잡아야 함
```
⚠️ **GATE 절차:** [→§11]의 `verilator --lint-only -Wall` 호출을 그대로 쓰되, **게이트 델타**만 더한다 —
`--default-net none`(implicit net을 강제 오류화) + `--default-language 1800-2017`, 그리고 warning을
통과시키지 않도록 `-Wno-fatal` 사용 금지. 이 게이트를 통과한 뒤에만 기능 review로 진행한다.
implicit-net/undeclared-id/out-of-range index warning은 **error로 취급**. (§11의 "lint 도구"를
"통과 필수 gate"로 승격하는 것이 이 절의 유일한 추가분 — 호출 자체는 §11에서 재사용.)

### FPGA RAM Inference (T8) — RTL-side — `c69a048`/`1851ac0`/`f451926`

> vendor 매크로/attribute 상세는 `lattice-fpga` skill에 위임. 여기서는 **RTL-side 추론 규칙**만.

| 규칙 | Detect | Commit |
|------|--------|--------|
| FPGA RAM array는 **write port 정확히 1개** | **STATIC** | `c69a048` |
| 올바른 `syn_ramstyle` (≠ `syn_preserve`) | **STATIC** | `c69a048` |
| read는 **명시적 case-MUX** (Synplify에서 dynamic index 금지) | **STATIC** | `f451926` |
| read가 write보다 먼저 일어날 수 있으면 init/reset | **STATIC** | `1851ac0` |
| 비합성 extra port는 `` `ifndef ``로 guard | **STATIC** | `c69a048` |

`r_dur_lut[0:31]`은 (1) 한 always 블록에 **write port 2개**, (2) `syn_preserve=1`(틀린 attribute),
(3) **dynamic-index read**, (4) un-reset이라 XO2가 RAM 추론에 실패했다.

```verilog
// c69a048 — ramstyle 교정 + 두번째 write port를 `ifndef XO2 로 guard (1-write-port 보장)
-reg [7:0] r_dur_lut [0:31] /* synthesis syn_preserve = 1 */;
+reg [7:0] r_dur_lut [0:31] /* synthesis syn_ramstyle="distributed" */;
         r_dur_lut[r_dur_fifo_wr_ptr] <= i_dur_seq_wr_data;   // write port #1 (유지)
+`ifndef XO2
         if (w_dur_dir_wr_cdc_p) r_dur_lut[i_dur_dir_addr] <= r_phaseDuration; // write #2 → guard
+`endif

// f451926 — dynamic index read를 명시적 case-MUX로 (Synplify/Lattice 안전)
5'd17: c_dur_lut_rd = r_dur_lut[17];   // …32-way case MUX, dynamic r_dur_lut[idx] 금지

// 1851ac0 — read가 write보다 선행 가능 → power-on init loop
for (i=0;i<32;i=i+1) r_dur_lut[i] <= 8'h00;
```
✅ RAM array 작성 시: write port 1개 → 올바른 ramstyle → case-MUX read → init/reset → extra port
`` `ifndef `` guard. synthesis RAM-inference report로 확인. (out-of-range `r_dur_lut[17]` 류 index는
[→§1.BitWidth] / T9와 교차 검증.)

[→§11] Verilator Lint — 본 §11.1은 그 lint를 **mandatory gate**로 승격하고 FPGA RAM 추론 규칙을 추가.

---

## 12. Module Analysis (수정 전 필수 분석)

### 원칙

> **RTL 수정 전에 대상 모듈의 전체 분석서가 반드시 존재해야 한다.**
> H/W는 모듈 내 모든 신호가 상호 연계되어 있어 snippet 분석으로는 불충분하다.

**워크플로우**: 모듈 식별 → `.ai/analysis/{module}.analysis.md` 확인(없으면 작성) → 참조 → 수정 후 갱신
### 분석서 필수 포함 항목

**파일 경로**: `.ai/analysis/{module_name}.analysis.md`

#### A. 모듈 개요
- 모듈 역할, 클럭/리셋 포트, 전체 입출력 포트 목록
- 동작 클럭 도메인 (클럭별 **정확한 주파수**, 용도). 주파수를 코드에서 유추할 수 없으면 **반드시 사용자에게 확인** — CDC 방향(Fast→Slow/Slow→Fast) 판단의 기초

#### B. Always 블록 맵
- 모듈 내 모든 always 블록 목록 (line 범위, 클럭, 게이트 조건)
- 각 블록이 담당하는 레지스터/신호 목록

#### C. FSM 전체 상태 전이도
- 각 FSM별:
  - **상태 목록** (define, one-hot/binary 인코딩)
  - **클럭 게이트 조건** (매 사이클 동작 vs 조건부 enable)
  - **전체 전이 테이블**: `현재상태 × 조건 → 다음상태 + 출력`
  - 각 상태에서 설정하는 **모든** 조합 출력 (c_ 신호) 나열

#### D. 신호 의존성 맵
- 모듈 내 주요 신호별:
  - **Producer**: 어느 always/FSM/상태에서 생성
  - **Consumer**: 어느 always/FSM/상태에서 사용
  - **타이밍**: 조합(same cycle) vs 레지스터(next cycle)
- **FSM 간 크로스 신호**: 생성 FSM → 소비 FSM, 클럭 게이트 차이, 유효 사이클
- **래칭 수명** [→§1.DataLife]: Write 상태 → Read 상태 쌍, 중간 경로의 덮어쓰기 위험

#### E. FSM 간 핸드쉐이크 타이밍
- FSM 간 신호가 전달되는 사이클 정확 다이어그램
- 클럭 게이트가 다른 경우 실제 래칭 사이클 명시
- 타이밍 제약: "이 신호는 반드시 X 사이클에 설정되어야 함" 등

#### F. CDC 경로
- 클럭 도메인 경계를 넘는 신호, 동기화 방식, 지연 사이클
- 2FF 사용 시: 소스 신호 유지 구간이 대상 2사이클 이상인지 주파수 비율로 검증. 보장 불가 시 주석 명시 + 사용자 확인

#### G. 수정 시 주의사항
- 건드리면 안 되는 타이밍 정렬 관계
- 기존 설계의 암묵적 가정 (코드 주석에 없는 것들)
- 과거 버그 수정 이력에서 파생된 제약

### 분석서 작성 규칙

1. **전체 읽기 필수**: 모듈 파일을 처음부터 끝까지 전부 읽는다. 부분 grep 금지.
2. **모든 always/FSM 식별**: 순차/조합 블록, define/case 양쪽 교차 확인.
3. **크로스 FSM 신호 추적**: 생성 FSM → 소비 FSM, 클럭 게이트 차이, 유효 사이클.
4. **사이클 다이어그램**: 복잡한 핸드쉐이크는 `[Cycle N]`, `[Cycle N+1]` 표기로 명시.

### 분석서 갱신 규칙

- RTL 수정 후, 변경된 FSM 상태/신호/전이만 업데이트. 추가 시 전이 테이블/크로스 신호 맵 반영. 삭제 시 분석서에서도 제거.

### 분석 깊이 기준

| 모듈 복잡도 | 분석 수준 | 예시 |
|------------|----------|------|
| 단순 (FSM 0~1개, <200줄) | A+B+D | 레지스터 뱅크, 단순 인터페이스 |
| 중간 (FSM 1~2개, 200~500줄) | A+B+C+D+F | 인코더, 디코더, FIFO 래퍼 |
| 복잡 (FSM 3개+, >500줄, 크로스FSM 신호) | **A~G 전체** | pcmInterface, askEncoder 등 |

---

## 13. File Header Comment (파일 헤더 주석)

### 원칙

RTL 파일 작성/수정 시 파일 상단에 doxygen 스타일 헤더 주석을 유지한다.

- **신규 파일 생성 시**: 헤더 전체 생성. `[revision history]`에 `initial version` 항목 추가.
- **기존 파일 수정 시 (헤더 있음)**: `[revision history]`에 변경 항목 1줄 추가, `@date`·`@version` minor 갱신.
- **기존 파일 수정 시 (헤더 없음)**: 헤더 생성 후 revision history에 현재 변경 내용 추가.

### 헤더 템플릿

```verilog
/* Copyright YYYY. TODOC, Inc. All Rights Reserved. Proprietary and confidential. */
/** @file {filename}.v
 * @brief {1줄 모듈 역할 설명}.
 * @details [Notes] - {설계 의도, 주요 제약, 알려진 한계}
 *
 * [revision history]
 *   - initial version (by {author}), {Month Year}
 *
 * @author {Name} <{email}>
 * @date {Month, Year}
 * @version 1.0
 */
```

### 각 필드 작성 규칙

| 필드 | 규칙 |
|------|------|
| `@file` | 파일명 + 확장자 (`ext_foo.v`) |
| `@brief` | 모듈 역할 1줄 요약. **반드시 `.`으로 끝냄** (JAVADOC_AUTOBRIEF 기준) |
| `@details` 본문 | `[Notes]`, `[Algorithm]`, `[FSM 설명]` 등 **내용에 맞는 섹션명** 자유 사용 |
| `[revision history]` | 항목 형식: `- {feature}: {변경 내용 요약} (by {author}), {Month Year}` |
| `@author` | 이름 + 이메일. 복수 작성자는 `, ` 구분. 알 수 없으면 `[Author]` |
| `@date` | **최신 수정** 월/연도 (`Mar, 2026`). 최초 작성일 아님 |
| `@version` | X.Y 형식. 수정 시 minor(Y) 증가. 기능 추가·대규모 변경 시 major(X) 증가 |
| Copyright block | 프로젝트 정책이 있으면 추가. 없으면 생략 가능 |

### revision history 업데이트 패턴

수정 항목이 특정 feature와 연계될 때:
```
 [revision history]
   - initial version (by jonghyeok park), Nov 2021
   - release version (by hoseung lee), June 2022
   - sync-xfr-extension: BTNOP 10us timer engine, i_btnop_exec_pulse input
     (by hoseung lee & claude), Mar 2026
```

일반 버그픽스나 소규모 수정:
```
   - fix I2C repeated START race condition in SCL edge detection (by hoseung lee), Mar 2026
```

### 주의사항

- `@details` 본문 섹션명은 통일 불필요 — 해당 모듈의 설계 구조를 가장 잘 설명하는 이름 사용
- `[revision history]`는 **필수** — 다른 섹션은 내용 없으면 생략 가능
- `*//* for doxygen, JAVADOC_AUTOBRIEF set to YES...` 마무리 주석은 doxygen 처리 시 reminder용 — 선택적 추가

---

## 참조 파일

- `references/naming-examples.md` - 네이밍 상세 예시
- `references/fsm-patterns.md` - FSM 설계 패턴 상세
- `references/cdc-patterns.md` - CDC 처리 패턴
- `references/synthesis-check.md` - 합성 체크리스트
- `references/cycle-analysis.md` - 사이클 분석 상세
- `references/review-checklist.md` - 코드 리뷰 체크리스트
- `references/always-block-patterns.md` - Always 블록 허용/분리 사례 코드
- `references/covergroup-patterns.md` - SV covergroup/assertion 문법 패턴
- `references/coverage-methodology.md` - Coverage 이론, testplan, closure
- `references/coverage-examples.md` - Coverage 실전 예제
- `references/verilator-guide.md` - Verilator Lint 환경, Warning 유형, 억제 방법
- `.ai/analysis/*.analysis.md` - 프로젝트별 모듈 분석서 (§12에서 생성)

## Cross-Skill 참조

- FPGA 합성, iCEcube2/Radiant 구현, 비트스트림 → `lattice-fpga` skill
- UVM 테스트벤치, agent/env 설계, RAL → `uvm-verification` skill
- Verilog-A 아날로그 모델, Mixed-signal 인터페이스 → `verilog-a` skill
- RTL-TB 인터페이스, 듀얼탑, Reference Model, Scoreboard → `chip-verification` skill
