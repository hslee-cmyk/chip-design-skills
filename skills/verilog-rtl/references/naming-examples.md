# Signal Naming Examples

## 완전한 모듈 예시

```verilog
//============================================================
// Module: uart_tx
// Description: UART Transmitter with FIFO
//============================================================
module uart_tx #(
    parameter DATA_WIDTH   = 8,          // UPPER_CASE
    parameter FIFO_DEPTH   = 16,
    parameter BAUD_DIV     = 434         // 115200 @ 50MHz
)(
    input  wire                    i_clk,
    input  wire                    i_rst_n,
    
    // Data Interface
    input  wire [DATA_WIDTH-1:0]   i_tx_data,    // i_ 입력
    input  wire                    i_tx_valid,
    output wire                    o_tx_ready,   // o_ 출력
    
    // UART Interface
    output wire                    o_uart_tx,
    
    // Status
    output wire                    o_fifo_full,
    output wire                    o_fifo_empty
);

    //--------------------------------------------------------
    // Internal Signals
    //--------------------------------------------------------
    // 레지스터 (r_)
    reg [DATA_WIDTH-1:0]  r_shift_reg;
    reg [3:0]             r_bit_cnt;
    reg [15:0]            r_baud_cnt;
    reg [2:0]             r_state;
    
    // 조합 출력 (c_)
    wire [2:0]            c_next_state;
    wire                  c_baud_tick;
    wire                  c_tx_done;
    
    // 내부 와이어 (w_)
    wire [DATA_WIDTH-1:0] w_u_tx_fifo_o_rdata;   // w_<inst>_<port>
    wire                  w_fifo_rd_en;           // 제어 와이어 (인스턴스 출력 아님)
    wire                  w_u_tx_fifo_o_empty;    // w_<inst>_<port>
    
    //--------------------------------------------------------
    // Submodule Instance
    //--------------------------------------------------------
    fifo_sync #(
        .DATA_WIDTH (DATA_WIDTH),
        .DEPTH      (FIFO_DEPTH)
    ) u_tx_fifo (
        .i_clk      (i_clk),
        .i_rst_n    (i_rst_n),
        .i_wdata    (i_tx_data),
        .i_wr_en    (i_tx_valid & o_tx_ready),
        .i_rd_en    (w_fifo_rd_en),
        .o_rdata    (w_u_tx_fifo_o_rdata),  // w_<inst>_<port>
        .o_full     (o_fifo_full),          // Top 출력 직결
        .o_empty    (w_u_tx_fifo_o_empty)
    );
    
    //--------------------------------------------------------
    // Baud Rate Generator
    //--------------------------------------------------------
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_baud_cnt <= '0;
        end else if (r_baud_cnt == BAUD_DIV - 1) begin
            r_baud_cnt <= '0;
        end else begin
            r_baud_cnt <= r_baud_cnt + 1'b1;
        end
    end
    
    assign c_baud_tick = (r_baud_cnt == BAUD_DIV - 1);
    
    //--------------------------------------------------------
    // FSM (2-process)
    //--------------------------------------------------------
    localparam [2:0]
        S_IDLE  = 3'b001,
        S_START = 3'b010,
        S_DATA  = 3'b100;
    
    // Process 1: State Register
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_state <= S_IDLE;
        end else begin
            r_state <= c_next_state;
        end
    end
    
    // Process 2: Next State + Output (Mealy)
    always_comb begin
        c_next_state = r_state;
        // ... FSM logic
    end
    
    //--------------------------------------------------------
    // Output Assignment
    //--------------------------------------------------------
    assign o_tx_ready  = !o_fifo_full;
    assign o_fifo_empty = w_u_tx_fifo_o_empty;
    
endmodule
```

## Top Integration 예시

```verilog
module system_top (
    input  wire        i_clk,
    input  wire        i_rst_n,
    
    // External Interface
    input  wire [7:0]  i_rx_data,
    input  wire        i_rx_valid,
    output wire        o_tx_uart,
    output wire        o_led
);

    //--------------------------------------------------------
    // Internal Wires: w_<instance>_<port_name>
    // 포트명 전체 포함 (o_ prefix 유지)
    //--------------------------------------------------------
    // From u_proc
    wire [7:0]  w_u_proc_o_data;
    wire        w_u_proc_o_valid;
    wire        w_u_proc_o_ready;
    
    // From u_uart
    wire        w_u_uart_o_tx_ready;
    wire        w_u_uart_o_busy;
    
    // From u_ctrl
    wire        w_u_ctrl_o_enable;
    wire [1:0]  w_u_ctrl_o_mode;
    
    //--------------------------------------------------------
    // Instances
    //--------------------------------------------------------
    data_processor u_proc (
        .i_clk      (i_clk),
        .i_rst_n    (i_rst_n),
        .i_data     (i_rx_data),
        .i_valid    (i_rx_valid),
        .i_enable   (w_u_ctrl_o_enable),      // From u_ctrl
        .o_data     (w_u_proc_o_data),        // w_<inst>_<port>
        .o_valid    (w_u_proc_o_valid),
        .o_ready    (w_u_proc_o_ready)
    );
    
    uart_tx u_uart (
        .i_clk      (i_clk),
        .i_rst_n    (i_rst_n),
        .i_tx_data  (w_u_proc_o_data),        // From u_proc
        .i_tx_valid (w_u_proc_o_valid),
        .o_tx_ready (w_u_uart_o_tx_ready),
        .o_uart_tx  (o_tx_uart),              // Top 출력 직결
        .o_busy     (w_u_uart_o_busy)
    );
    
    system_ctrl u_ctrl (
        .i_clk      (i_clk),
        .i_rst_n    (i_rst_n),
        .i_busy     (w_u_uart_o_busy),        // From u_uart
        .o_enable   (w_u_ctrl_o_enable),
        .o_mode     (w_u_ctrl_o_mode),
        .o_led      (o_led)                   // Top 출력 직결
    );

endmodule
```

## BSC (Boundary Scan Chain) 네이밍 예시

```verilog
//============================================================
// BSC 통과 신호: _a (BSC 입력), _z (BSC 출력)
// 신호 방향(i_/o_)은 원래 신호의 의미를 유지 (BSC 관점 아님)
//============================================================
module bsc_wrapper (
    // BSC 통과 신호
    input  wire        i_rst_a,           // 외부에서 BSC로 입력
    output wire        i_rst_z,           // BSC에서 내부로 출력

    input  wire [11:0] i_adc_out_a,       // ADC → BSC 입력
    output wire [11:0] i_adc_out_z,       // BSC → 내부 로직 출력

    input  wire        o_stim_en_a,       // 내부 로직 → BSC 입력
    output wire        o_stim_en_z,       // BSC → 외부 패드 출력

    // JTAG 제어 신호 (일반 네이밍)
    input  wire        i_tck,
    input  wire        i_trstn,
    output wire        o_tdo
);

    //--------------------------------------------------------
    // Signal Flow:
    //   External  ──(_a)──▶ [BSC Cell] ──(_z)──▶  Internal
    //   Internal  ──(_a)──▶ [BSC Cell] ──(_z)──▶  External
    //
    //   Normal mode: _z = _a (bypass)
    //   Test mode:   _z = scan chain value
    //--------------------------------------------------------

endmodule
```

## 신호 이름 체크리스트

| 체크 | 규칙 |
|------|------|
| ☐ | 입력 포트가 `i_`로 시작하는가? |
| ☐ | 출력 포트가 `o_`로 시작하는가? |
| ☐ | 레지스터가 `r_`로 시작하는가? |
| ☐ | 조합 출력이 `c_`로 시작하는가? |
| ☐ | 내부 와이어가 `w_`로 시작하는가? |
| ☐ | Top integration 와이어가 `w_<inst>_<port>` 형식인가? |
| ☐ | 클럭/리셋이 `i_clk`, `i_rst_n` 인가? (입력이므로 `i_` prefix) |
| ☐ | BSC 통과 신호가 `_a`(BSC 입력), `_z`(BSC 출력) postfix인가? |
| ☐ | 파라미터가 UPPER_CASE인가? |
| ☐ | 모듈이 lowercase_with_underscores인가? |
| ☐ | 인스턴스가 `u_`로 시작하는가? |
