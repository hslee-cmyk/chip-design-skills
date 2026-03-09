# RTL Port to Interface Mapping Guide

## 기본 매핑 규칙

### Step 1: RTL 포트 분석

```verilog
// RTL Module
module my_dut (
    input  wire        clk,
    input  wire        rst_n,
    // Input channel
    input  wire [31:0] in_data,
    input  wire        in_valid,
    output wire        in_ready,
    // Output channel  
    output wire [31:0] out_data,
    output wire        out_valid,
    input  wire        out_ready
);
```

### Step 2: Interface 생성

```systemverilog
interface my_dut_if (input logic clk, input logic rst_n);
    
    // Input channel signals
    logic [31:0] in_data;
    logic        in_valid;
    logic        in_ready;
    
    // Output channel signals
    logic [31:0] out_data;
    logic        out_valid;
    logic        out_ready;
    
    //------------------------------------------
    // Clocking Blocks (Driver/Monitor 관점)
    //------------------------------------------
    
    // Input Driver: DUT 입력을 구동
    clocking in_drv_cb @(posedge clk);
        default input #1step output #1;
        output in_data, in_valid;
        input  in_ready;
    endclocking
    
    // Input Monitor: DUT 입력을 관찰
    clocking in_mon_cb @(posedge clk);
        default input #1step;
        input in_data, in_valid, in_ready;
    endclocking
    
    // Output Driver: DUT 출력쪽 ready 구동
    clocking out_drv_cb @(posedge clk);
        default input #1step output #1;
        input  out_data, out_valid;
        output out_ready;
    endclocking
    
    // Output Monitor: DUT 출력을 관찰
    clocking out_mon_cb @(posedge clk);
        default input #1step;
        input out_data, out_valid, out_ready;
    endclocking
    
    //------------------------------------------
    // Modports
    //------------------------------------------
    modport IN_DRV  (clocking in_drv_cb,  input rst_n);
    modport IN_MON  (clocking in_mon_cb,  input rst_n);
    modport OUT_DRV (clocking out_drv_cb, input rst_n);
    modport OUT_MON (clocking out_mon_cb, input rst_n);
    
endinterface
```

### Step 3: DUT 연결 (hdl_top)

```systemverilog
module hdl_top;  // 듀얼탑 구조의 HDL 탑
    
    // Clock & Reset
    logic clk, rst_n;
    
    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 100MHz
    end
    
    // Interface instantiation
    my_dut_if dut_if(clk, rst_n);
    
    // DUT instantiation
    my_dut u_dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .in_data   (dut_if.in_data),
        .in_valid  (dut_if.in_valid),
        .in_ready  (dut_if.in_ready),
        .out_data  (dut_if.out_data),
        .out_valid (dut_if.out_valid),
        .out_ready (dut_if.out_ready)
    );
    
    // Note: 듀얼탑 구조에서 config_db::set은 hvl_top에 배치하는 것이 권장됨.
    // 아래는 hdl_top에서 직접 설정하는 간략화 예제.
    initial begin
        uvm_config_db#(virtual my_dut_if.IN_DRV)::set(
            null, "uvm_test_top.env.in_agent.drv", "vif", dut_if);
        uvm_config_db#(virtual my_dut_if.IN_MON)::set(
            null, "uvm_test_top.env.in_agent.mon", "vif", dut_if);
        uvm_config_db#(virtual my_dut_if.OUT_DRV)::set(
            null, "uvm_test_top.env.out_agent.drv", "vif", dut_if);
        uvm_config_db#(virtual my_dut_if.OUT_MON)::set(
            null, "uvm_test_top.env.out_agent.mon", "vif", dut_if);
    end

endmodule
```

## 복잡한 매핑 패턴

### 다중 인스턴스

```systemverilog
// 여러 채널이 있는 경우
my_dut_if ch_if[4](clk, rst_n);

for (genvar i = 0; i < 4; i++) begin : gen_dut
    my_dut u_dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .in_data (ch_if[i].in_data),
        // ...
    );
end

// Config DB도 배열로
initial begin
    for (int i = 0; i < 4; i++) begin
        uvm_config_db#(virtual my_dut_if)::set(
            null, $sformatf("uvm_test_top.env.agent[%0d]*", i), "vif", ch_if[i]);
    end
end
```

### 양방향 신호

```systemverilog
// Inout 포트 처리
interface bidir_if(input logic clk);
    wire [7:0] data;       // inout은 wire로
    logic      data_oe;    // output enable
    logic [7:0] data_out;  // 출력 데이터
    logic [7:0] data_in;   // 입력 데이터
    
    // Tristate 구현
    assign data = data_oe ? data_out : 8'bz;
    assign data_in = data;
endinterface
```

### 파라미터화된 Interface

```systemverilog
interface param_if #(
    parameter DATA_WIDTH = 32,
    parameter ADDR_WIDTH = 16
)(input logic clk, input logic rst_n);
    
    logic [DATA_WIDTH-1:0] data;
    logic [ADDR_WIDTH-1:0] addr;
    
endinterface

// 인스턴스화
param_if #(.DATA_WIDTH(64), .ADDR_WIDTH(20)) wide_if(clk, rst_n);
```

## Clocking Block 타이밍

```
        ┌───┐   ┌───┐   ┌───┐
clk  ───┘   └───┘   └───┘   └───
        
     ◄─#1step─►
input  ─────────X───────────────  (샘플링: posedge 직전)

            ◄─#1─►
output ──────────────X──────────  (구동: posedge 직후)
```

**#1step**: 같은 타임슬롯의 이전 region에서 샘플링 (race 방지)
**#1**: 1 time unit 후 구동 (delta 지연)
