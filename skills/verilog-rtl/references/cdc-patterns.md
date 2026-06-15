# CDC (Clock Domain Crossing) Patterns

## CDC 방식 선택 가이드

### ⚠️ 핵심 원칙

```
┌─────────────────────────────────────────────────────────────┐
│  "소스 신호가 대상 클럭 2사이클 이상 유지되는가?"           │
│  이 질문이 CDC 방식을 결정한다.                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  소스 ≥ 2 dest cycles → 2FF 기반 (Sync / Edge Detect)     │
│  소스 < 2 dest cycles → Toggle 또는 Handshake 필요        │
│                                                             │
│  Slow→Fast: 1 src cycle ≥ 2 dest cycles → 자연 충족       │
│  Fast→Slow: 주파수 비율로 검증 필수                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 왜 소스 < 2 dest cycles일 때 2FF가 안 되는가?

```
Fast Clock  ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─
             │ │ │ │ │ │ │ │ │ │ │ │
Signal      ─┴─┴─┼─┴─┴─┼─┴─┴─┴─┴─┴─┴─
                 ↑     ↑
                 │     └─ 신호 끝
                 └─ 신호 시작 (1-2 fast cycles)

Slow Clock  ────────┬───────────┬───────────
                    ↑           ↑
                    │           └─ 두 번째 샘플링 (이미 사라짐!)
                    └─ 첫 번째 샘플링 (신호 없음)

→ 신호가 dest clock 2 edge 사이보다 짧으면 유실!
```

### CDC 방식 선택 테이블

| 신호 타입 | 소스 폭 vs dest 2 cycles | 방식 | 지연 |
|----------|-------------------------|------|------|
| 1-bit level | ≥ 2 dest cycles | **2FF Sync** | 2 dest cycles |
| 1-bit pulse | ≥ 2 dest cycles | **2FF + Edge Detect** | 2-3 dest cycles |
| 1-bit pulse | < 2 dest cycles (Slow→Fast) | **Pulse Sync** (toggle) | 3-4 dest cycles |
| 1-bit pulse | < 2 dest cycles (Fast→Slow) | **Handshake** | 가변 (Ack 대기) |
| Multi-bit pointer | — | **Gray + 2FF** | 2 dest cycles |
| Multi-bit data stream | — | **Async FIFO** | FIFO depth |

> **Slow→Fast에서 pulse < 2 dest cycles가 발생하는 경우는 드물다**
> (1 src cycle이 자연적으로 여러 dest cycles). 하지만 주파수가 근접한
> 경우(예: 8MHz→10MHz)는 검증 필요.

### 펄스 + 동반 Multi-bit 데이터

펄스가 CDC를 통과하면, 동반 데이터는 별도 CDC 없이 직접 샘플링 가능:
- 소스 측에서 펄스와 동시에 레지스터에 래칭된 데이터
- 데이터는 다음 펄스까지 안정 (최소 1 src cycle = 여러 dest cycles)
- 수신 측에서 동기화된 펄스 시점에 데이터를 읽으면 안전

---

## 1. 2FF Synchronizer (Slow → Fast 전용)

### 사용 조건

- 송신 클럭 < 수신 클럭 (f_src < f_dest)
- 신호가 최소 2 dest cycles 동안 유지됨

### 구현

```verilog
module sync_2ff (
    input  wire i_clk_dest,
    input  wire i_rst_n,
    input  wire i_async,      // From slow domain
    output wire o_sync        // To fast domain
);

    reg r_sync_ff1;
    reg r_sync_ff2;
    
    always_ff @(posedge i_clk_dest or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_sync_ff1 <= 1'b0;
            r_sync_ff2 <= 1'b0;
        end else begin
            r_sync_ff1 <= i_async;
            r_sync_ff2 <= r_sync_ff1;
        end
    end
    
    assign o_sync = r_sync_ff2;

endmodule
```

### 타이밍

```
Slow Clk  ──────┬───────────────┬───────────────
               ↑               ↑
i_async   ─────┴───────────────┴───────────────
                    (여러 fast cycles 동안 유지)

Fast Clk  ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─
           │ │ │ │ │ │ │ │ │ │ │ │
r_sync_ff1 ───┬─────────────────────  (1 cycle 후)
r_sync_ff2 ─────┬───────────────────  (2 cycles 후)
                ↑
                └─ 안정적으로 샘플링됨
```

---

## 1.5 2FF + Edge Detect (Pulse, 소스 ≥ 2 dest cycles)

### 사용 조건

- 소스 펄스가 **dest 클럭 2사이클 이상** 유지 (Slow→Fast에서 자연 충족)
- Toggle 변환 없이 2FF로 직접 캡처 가능

### 구현

```verilog
// 소스 펄스가 충분히 넓을 때 (예: 2MHz→10MHz, 1 src cycle = 5 dest cycles)
reg [1:0] r_pulse_cdc;

always_ff @(posedge i_clk_dest or negedge i_rst_n) begin
    if (!i_rst_n)
        r_pulse_cdc <= 2'b0;
    else
        r_pulse_cdc <= {r_pulse_cdc[0], i_pulse};
end

wire w_pulse_sync = r_pulse_cdc[0] & ~r_pulse_cdc[1];  // rising edge detect
```

> **2FF + Edge Detect vs Pulse Sync 판단**: 소스 펄스 1 cycle이 dest 2 cycles 이상이면
> 2FF + Edge Detect로 충분. 미만이면 §2 Pulse Sync (toggle 방식) 사용.

---

## 2. Pulse Synchronizer (Pulse, 소스 < 2 dest cycles)

### 사용 조건

- 소스 펄스가 dest 클럭 **2사이클 미만** (2FF 캡처 불가 → toggle로 레벨 변환)
- 주로 주파수가 근접한 경우 (예: 8MHz→10MHz)

### 구현

```verilog
module pulse_sync (
    input  wire i_clk_src,
    input  wire i_clk_dest,
    input  wire i_rst_n,
    input  wire i_pulse,      // 1-cycle pulse in src domain
    output wire o_pulse       // 1-cycle pulse in dest domain
);

    // Source: Toggle on pulse
    reg r_toggle;
    
    always_ff @(posedge i_clk_src or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_toggle <= 1'b0;
        end else if (i_pulse) begin
            r_toggle <= ~r_toggle;
        end
    end
    
    // Destination: 2FF sync + edge detect
    reg r_sync_ff1;
    reg r_sync_ff2;
    reg r_sync_ff3;
    
    always_ff @(posedge i_clk_dest or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_sync_ff1 <= 1'b0;
            r_sync_ff2 <= 1'b0;
            r_sync_ff3 <= 1'b0;
        end else begin
            r_sync_ff1 <= r_toggle;
            r_sync_ff2 <= r_sync_ff1;
            r_sync_ff3 <= r_sync_ff2;
        end
    end
    
    // Edge detect = pulse
    assign o_pulse = r_sync_ff2 ^ r_sync_ff3;

endmodule
```

---

## 3. Handshake Synchronizer (Pulse, 소스 < 2 dest cycles, Fast→Slow)

### ⚠️ Fast→Slow 펄스에서 소스 < 2 dest cycles이면 반드시 이 방식 사용

### 동작 원리

```
┌─────────────────────────────────────────────────────────────┐
│  Handshake Protocol                                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Source: req 토글                                        │
│  2. Dest: req 동기화 후 처리                               │
│  3. Dest → Source: ack 반환 (2FF OK, Slow→Fast)            │
│  4. Source: ack 확인 후 다음 전송 가능                     │
│                                                             │
│  → 신호 유실 없이 안전하게 전달                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 구현

```verilog
module handshake_sync (
    // Source domain (Fast)
    input  wire       i_clk_src,
    input  wire       i_rst_src_n,
    input  wire       i_send,        // Send request
    input  wire [7:0] i_data,        // Data to send
    output wire       o_busy,        // Cannot accept new data
    
    // Destination domain (Slow)
    input  wire       i_clk_dest,
    input  wire       i_rst_dest_n,
    output wire       o_valid,       // Data valid pulse
    output wire [7:0] o_data         // Received data
);

    //========================================================
    // Source Domain (Fast)
    //========================================================
    reg       r_req;
    reg [7:0] r_data_hold;
    
    // Ack synchronizer (Slow → Fast, 2FF OK)
    reg r_ack_sync1, r_ack_sync2;
    
    always_ff @(posedge i_clk_src or negedge i_rst_src_n) begin
        if (!i_rst_src_n) begin
            r_ack_sync1 <= 1'b0;
            r_ack_sync2 <= 1'b0;
        end else begin
            r_ack_sync1 <= r_ack;       // From dest domain
            r_ack_sync2 <= r_ack_sync1;
        end
    end
    
    // Request generation
    always_ff @(posedge i_clk_src or negedge i_rst_src_n) begin
        if (!i_rst_src_n) begin
            r_req <= 1'b0;
            r_data_hold <= '0;
        end else if (i_send && !o_busy) begin
            r_req <= ~r_req;            // Toggle request
            r_data_hold <= i_data;      // Capture data
        end
    end
    
    assign o_busy = (r_req != r_ack_sync2);  // Busy until ack matches
    
    //========================================================
    // Destination Domain (Slow)
    //========================================================
    reg r_ack;
    
    // Request synchronizer (Fast → Slow, need extra stage)
    reg r_req_sync1, r_req_sync2, r_req_sync3;
    
    always_ff @(posedge i_clk_dest or negedge i_rst_dest_n) begin
        if (!i_rst_dest_n) begin
            r_req_sync1 <= 1'b0;
            r_req_sync2 <= 1'b0;
            r_req_sync3 <= 1'b0;
        end else begin
            r_req_sync1 <= r_req;
            r_req_sync2 <= r_req_sync1;
            r_req_sync3 <= r_req_sync2;
        end
    end
    
    // Detect req toggle = new data
    wire w_req_pulse = r_req_sync2 ^ r_req_sync3;
    
    // Generate ack
    always_ff @(posedge i_clk_dest or negedge i_rst_dest_n) begin
        if (!i_rst_dest_n) begin
            r_ack <= 1'b0;
        end else begin
            r_ack <= r_req_sync2;  // Echo back synced request
        end
    end
    
    // Output
    assign o_valid = w_req_pulse;
    assign o_data = r_data_hold;  // Data is stable during handshake

endmodule
```

### 타이밍 다이어그램

```
Fast Clk  ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─
           │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │
i_send    ───┬─┴─────────────────────────────────────
r_req     ───┴───────────────────────────────────────  (toggle)
o_busy    ───┬───────────────────────────────┬───────  (wait for ack)
             │                               │
Slow Clk  ───────┬───────────┬───────────┬───────────
                 │           │           │
r_req_sync2 ─────────────────┬───────────────────────  (synced)
r_ack     ───────────────────────────────┬───────────  (echo)
                                         │
r_ack_sync2 ─────────────────────────────────────┬───  (back to src)
                                                 │
o_busy    ───────────────────────────────────────┴───  (released)
```

---

## 4. Gray Code Synchronizer (Multi-bit Pointer)

### 사용 조건

- 포인터, 카운터 등 순차적으로 변하는 값
- 한 번에 1비트만 변함 (Gray code 특성)

### 구현

```verilog
module gray_sync #(
    parameter WIDTH = 4
)(
    input  wire             i_clk_dest,
    input  wire             i_rst_n,
    input  wire [WIDTH-1:0] i_gray,       // Gray coded input
    output wire [WIDTH-1:0] o_gray_sync   // Synced gray code
);

    reg [WIDTH-1:0] r_sync_ff1;
    reg [WIDTH-1:0] r_sync_ff2;
    
    always_ff @(posedge i_clk_dest or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_sync_ff1 <= '0;
            r_sync_ff2 <= '0;
        end else begin
            r_sync_ff1 <= i_gray;
            r_sync_ff2 <= r_sync_ff1;
        end
    end
    
    assign o_gray_sync = r_sync_ff2;

endmodule

// Binary ↔ Gray 변환
function [WIDTH-1:0] bin2gray(input [WIDTH-1:0] bin);
    bin2gray = bin ^ (bin >> 1);
endfunction

function [WIDTH-1:0] gray2bin(input [WIDTH-1:0] gray);
    integer i;
    begin
        gray2bin[WIDTH-1] = gray[WIDTH-1];
        for (i = WIDTH-2; i >= 0; i = i - 1)
            gray2bin[i] = gray2bin[i+1] ^ gray[i];
    end
endfunction
```

---

## 5. Async FIFO (Multi-bit Data Stream)

### 사용 조건

- 연속적인 데이터 스트림
- 양방향 클럭 속도 차이 흡수

### 핵심 구조

```
┌─────────────────────────────────────────────────────────────┐
│                     Async FIFO                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Write Domain          Memory           Read Domain         │
│  ─────────────         ──────           ───────────         │
│  i_clk_wr         ┌──────────────┐      i_clk_rd           │
│                   │              │                          │
│  wr_ptr ─────────→│   Dual-Port  │←───────── rd_ptr        │
│  (Gray) ─────────→│     RAM      │←───────── (Gray)        │
│                   │              │                          │
│          Gray Sync│              │Gray Sync                 │
│  rd_ptr_sync ←────┘              └────→ wr_ptr_sync        │
│                                                             │
│  Full = (wr_gray == {~rd_sync[MSB:MSB-1], rd_sync[rest]})  │
│  Empty = (rd_gray == wr_sync)                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 구현 (핵심 부분)

```verilog
module async_fifo #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 4
)(
    // Write side
    input  wire                  i_clk_wr,
    input  wire                  i_rst_wr_n,
    input  wire [DATA_WIDTH-1:0] i_wdata,
    input  wire                  i_wr_en,
    output wire                  o_full,
    
    // Read side
    input  wire                  i_clk_rd,
    input  wire                  i_rst_rd_n,
    output wire [DATA_WIDTH-1:0] o_rdata,
    input  wire                  i_rd_en,
    output wire                  o_empty
);

    // Memory
    reg [DATA_WIDTH-1:0] r_mem [0:(1<<ADDR_WIDTH)-1];
    
    // Write pointer (binary & gray)
    reg [ADDR_WIDTH:0] r_wr_ptr_bin;
    wire [ADDR_WIDTH:0] w_wr_ptr_gray = r_wr_ptr_bin ^ (r_wr_ptr_bin >> 1);
    
    // Read pointer (binary & gray)
    reg [ADDR_WIDTH:0] r_rd_ptr_bin;
    wire [ADDR_WIDTH:0] w_rd_ptr_gray = r_rd_ptr_bin ^ (r_rd_ptr_bin >> 1);
    
    // Synchronized pointers
    reg [ADDR_WIDTH:0] r_wr_ptr_gray_sync1, r_wr_ptr_gray_sync2;
    reg [ADDR_WIDTH:0] r_rd_ptr_gray_sync1, r_rd_ptr_gray_sync2;
    
    //--------------------------------------------------------
    // Write Domain
    //--------------------------------------------------------
    always_ff @(posedge i_clk_wr or negedge i_rst_wr_n) begin
        if (!i_rst_wr_n) begin
            r_wr_ptr_bin <= '0;
        end else if (i_wr_en && !o_full) begin
            r_wr_ptr_bin <= r_wr_ptr_bin + 1'b1;
        end
    end
    
    // Memory write (no reset)
    always_ff @(posedge i_clk_wr) begin
        if (i_wr_en && !o_full) begin
            r_mem[r_wr_ptr_bin[ADDR_WIDTH-1:0]] <= i_wdata;
        end
    end
    
    // Sync rd_ptr to wr domain
    always_ff @(posedge i_clk_wr or negedge i_rst_wr_n) begin
        if (!i_rst_wr_n) begin
            r_rd_ptr_gray_sync1 <= '0;
            r_rd_ptr_gray_sync2 <= '0;
        end else begin
            r_rd_ptr_gray_sync1 <= w_rd_ptr_gray;
            r_rd_ptr_gray_sync2 <= r_rd_ptr_gray_sync1;
        end
    end
    
    // Full: MSB 2 bits inverted, rest same
    assign o_full = (w_wr_ptr_gray == {~r_rd_ptr_gray_sync2[ADDR_WIDTH:ADDR_WIDTH-1],
                                        r_rd_ptr_gray_sync2[ADDR_WIDTH-2:0]});
    
    //--------------------------------------------------------
    // Read Domain
    //--------------------------------------------------------
    always_ff @(posedge i_clk_rd or negedge i_rst_rd_n) begin
        if (!i_rst_rd_n) begin
            r_rd_ptr_bin <= '0;
        end else if (i_rd_en && !o_empty) begin
            r_rd_ptr_bin <= r_rd_ptr_bin + 1'b1;
        end
    end
    
    // Memory read (no reset)
    assign o_rdata = r_mem[r_rd_ptr_bin[ADDR_WIDTH-1:0]];
    
    // Sync wr_ptr to rd domain
    always_ff @(posedge i_clk_rd or negedge i_rst_rd_n) begin
        if (!i_rst_rd_n) begin
            r_wr_ptr_gray_sync1 <= '0;
            r_wr_ptr_gray_sync2 <= '0;
        end else begin
            r_wr_ptr_gray_sync1 <= w_wr_ptr_gray;
            r_wr_ptr_gray_sync2 <= r_wr_ptr_gray_sync1;
        end
    end
    
    // Empty: pointers equal
    assign o_empty = (w_rd_ptr_gray == r_wr_ptr_gray_sync2);

endmodule
```

---

## CDC 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | 소스 신호 폭이 dest 클럭 2사이클 이상 유지되는가? (핵심 판단 기준) |
| ☐ | Level 신호: 소스 ≥ 2 dest cycles → 2FF Sync? |
| ☐ | Pulse 신호: 소스 ≥ 2 dest cycles → 2FF + Edge Detect? |
| ☐ | Pulse 신호: 소스 < 2 dest cycles → Pulse Sync (toggle) 또는 Handshake? |
| ☐ | 펄스 + 동반 데이터: 데이터 별도 CDC 없이 펄스 시점에 샘플링? |
| ☐ | Multi-bit 순차적: Gray code + 2FF (포인터, 카운터)? |
| ☐ | Multi-bit 스트림: Async FIFO? |
| ☐ | 메타스테빌리티 제약 설정? |
| ☐ | CDC 경로 SDC 제약? |
