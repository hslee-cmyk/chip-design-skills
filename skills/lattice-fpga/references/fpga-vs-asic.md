# FPGA vs ASIC Considerations

RTL을 FPGA와 ASIC(UVM 시뮬레이션) 양쪽에서 사용할 때 주의사항.

## 합성 차이점

| 항목 | FPGA | ASIC |
|------|------|------|
| 메모리 | BRAM (Block RAM) | SRAM 컴파일러 |
| 곱셈기 | DSP 블록 | 합성된 로직 |
| 클럭 | PLL (하드 IP) | PLL (셀 기반) |
| 리셋 | 전역 GSR 있음 | 명시적 리셋 필요 |
| IO | 고정 IO 셀 | 다양한 IO 라이브러리 |

## 공통 RTL 작성 가이드

### 1. 메모리 추론

```verilog
// GOOD: FPGA BRAM & ASIC SRAM 모두 추론 가능
reg [31:0] mem [0:1023];

always @(posedge clk) begin
    if (we)
        mem[addr] <= wdata;
    rdata <= mem[addr];  // 동기 읽기 (BRAM 추론)
end
```

```verilog
// BAD: 비동기 읽기 - FPGA에서 분산 RAM 사용
always @(posedge clk) begin
    if (we)
        mem[addr] <= wdata;
end
assign rdata = mem[addr];  // 비동기 읽기
```

### 2. 리셋 처리

```verilog
// FPGA: GSR (Global Set/Reset) 활용 가능하지만
// ASIC: 명시적 리셋 필요

// GOOD: 둘 다 호환
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        state <= IDLE;
    else
        state <= next_state;
end
```

### 3. 클럭 게이팅

```verilog
// BAD: FPGA에서 글리치 발생 가능
wire gated_clk = clk & enable;

// GOOD: 레지스터 enable 사용
always @(posedge clk) begin
    if (enable)
        data_reg <= data_in;
end

// ASIC에서는 ICG 셀 사용, FPGA에서는 CE 사용
```

### 4. 초기화

```verilog
// FPGA: initial 블록 지원
// ASIC: initial 블록 무시됨 (합성 불가)

// FPGA 전용 초기화
initial begin
    counter = 0;  // FPGA에서만 동작
end

// 공통: 리셋으로 초기화
always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        counter <= 0;  // FPGA & ASIC 모두 동작
    else
        counter <= counter + 1;
end
```

### 5. DSP 추론

```verilog
// GOOD: FPGA DSP 블록 & ASIC 곱셈기 추론
always @(posedge clk) begin
    product <= a * b;           // 곱셈
    mac <= mac + (a * b);       // MAC
end

// 파이프라인 추가 시 더 효율적
always @(posedge clk) begin
    a_reg <= a;
    b_reg <= b;
    product <= a_reg * b_reg;   // 입력 레지스터
    product_reg <= product;     // 출력 레지스터
end
```

## Lattice 특화 고려사항

### 합성 시 모듈 Flatten 규칙

클럭 생성/분주 모듈은 명시적으로 계층 유지가 지정되지 않는 한 합성 시 flatten하여 최적화한다.

**Flatten 대상 (기본)**:
- 클럭 분주/게이팅 모듈 (예: `ext_clk`)
- 리셋 동기화 모듈 (예: `ext_rst_sync`)
- 단순 클럭 로직 모듈

**계층 유지 대상 (예외)** — 아래 경우에만 `syn_hier = "hard"` 또는 동등 속성 부여:
- 하드 IP 인스턴스를 포함하는 모듈 (SB_HFOSC, PLL 등)
- Reveal 디버그 대상 모듈
- 사용자가 명시적으로 계층 유지를 지정한 모듈

**Synplify Pro 설정**:
```tcl
# 기본: 전체 flatten (클럭 모듈 포함)
set_option -hdl_param -set flatten 1

# 예외: 특정 모듈 계층 유지
# RTL에서 속성 부여:
# (* syn_hier = "hard" *) module my_preserved_module (...);
```

**Yosys 설정**:
```tcl
# 기본: flatten 후 합성
synth_ice40 -flatten -top <top_module>

# 또는 명시적으로
flatten
synth_ice40 -top <top_module>

# 예외: 특정 모듈 유지
# RTL에서 속성 부여:
# (* keep_hierarchy = "yes" *) module my_preserved_module (...);
```

> **SDC 영향**: 클럭 모듈이 flatten되면 `get_nets u_ext_d_top.u_ext_clk.w_signal` 같은
> 계층적 넷 경로가 변경될 수 있다. 합성 후 넷리스트에서 실제 넷 이름을 확인하고
> SDC를 갱신해야 한다.

### PLL 사용

```verilog
// Lattice PLL 인스턴스 (FPGA 전용)
`ifdef FPGA_LATTICE
    pll_core u_pll (
        .CLKI   (clk_in),
        .CLKOP  (clk_100m),
        .CLKOS  (clk_200m),
        .LOCK   (pll_locked)
    );
`else
    // ASIC: behavioral PLL 또는 외부 클럭
    assign clk_100m = clk_in;
    assign pll_locked = 1'b1;
`endif
```

### IO 버퍼

```verilog
// Lattice IO primitive (FPGA 전용)
`ifdef FPGA_LATTICE
    BB u_bidir (
        .I    (data_out),
        .O    (data_in),
        .B    (data_io),
        .T    (~data_oe)
    );
`else
    // ASIC: 직접 연결 또는 behavioral
    assign data_io = data_oe ? data_out : 1'bz;
    assign data_in = data_io;
`endif
```

## 조건부 컴파일

```verilog
// 프로젝트 공통 define 파일
// project_defines.vh

`ifdef SYNTHESIS
    `ifdef FPGA_TARGET
        `define FPGA_LATTICE
    `else
        `define ASIC_TARGET
    `endif
`else
    `define SIMULATION
`endif
```

```verilog
// RTL에서 사용
`include "project_defines.vh"

module my_design (...);
    
    `ifdef FPGA_LATTICE
        // FPGA 전용 코드
    `elsif ASIC_TARGET
        // ASIC 전용 코드
    `else
        // 시뮬레이션 전용 코드
    `endif
    
endmodule
```

## 검증 전략

```
┌─────────────────────────────────────────────────────────────┐
│                    검증 흐름                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. RTL 시뮬레이션 (UVM)  ─── 공통 RTL ───                 │
│         │                         │                         │
│         ▼                         ▼                         │
│  2a. FPGA 합성 (Radiant)   2b. ASIC 합성 (DC)             │
│         │                         │                         │
│         ▼                         ▼                         │
│  3a. FPGA 검증 (Reveal)    3b. 게이트 시뮬레이션           │
│         │                         │                         │
│         ▼                         ▼                         │
│  4a. 하드웨어 테스트       4b. 테잎아웃                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

* 1단계에서 대부분의 버그 발견
* FPGA는 빠른 프로토타입, 하드웨어 검증
* ASIC은 정밀 타이밍 검증
```
