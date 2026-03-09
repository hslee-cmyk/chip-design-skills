# Cycle Analysis Guide

## 개념

사이클 분석은 RTL 코드에서 **각 신호가 언제 유효한지** 추적하는 기법.

```
┌─────────────────────────────────────────────────────────────┐
│                 왜 사이클 분석이 중요한가?                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 파이프라인 설계 시 데이터 정렬 보장                     │
│  2. 레이턴시 계산 (입력 → 출력)                             │
│  3. valid/data 신호 동기화                                  │
│  4. 디버깅 시 값 추적                                       │
│  5. 타이밍 최적화 포인트 식별                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 표기법

### 기본 표기

```verilog
// [Cycle N]     - 사이클 N에 유효
// [Cycle N+1]   - 사이클 N+1에 유효 (레지스터 통과 후)
// [same]        - 같은 사이클 (조합 로직)
// [N → N+1]     - N에서 N+1로 전달 (레지스터)
```

### 예시

```verilog
input  wire [7:0] i_data;           // [Cycle 0] 외부 입력

wire [7:0] c_processed;             // [Cycle 0, same] 조합 처리
assign c_processed = i_data + 1;

reg [7:0] r_stage1;                 // [Cycle 1] 레지스터 출력
always_ff @(posedge i_clk) begin
    r_stage1 <= c_processed;        // [0 → 1]
end
```

## 조합 vs 순차 사이클

### 조합 로직 (Same Cycle)

```verilog
// 입력과 출력이 같은 사이클
//
//  i_a [N] ─────┐
//               ├──► c_sum [N, same]
//  i_b [N] ─────┘

wire [7:0] c_sum;
assign c_sum = i_a + i_b;  // [Cycle N, same cycle]
```

### 순차 로직 (Next Cycle)

```verilog
// 입력 사이클 + 1 = 출력 사이클
// 데이터 경로: 리셋 불필요

reg [7:0] r_data;
always_ff @(posedge i_clk) begin
    r_data <= i_data;  // [Cycle N → N+1]
end
```

## 파이프라인 사이클 분석

### 3단 파이프라인 예시

```verilog
module three_stage_pipe (
    input  wire        i_clk,
    input  wire        i_rst_n,
    input  wire [15:0] i_a,          // [Cycle 0]
    input  wire [15:0] i_b,          // [Cycle 0]
    input  wire        i_valid,      // [Cycle 0]
    output wire [31:0] o_result,     // [Cycle 3]
    output wire        o_valid       // [Cycle 3]
);

    //========================================================
    // Stage 1: Multiply (partial)
    // Input: [Cycle 0], Output: [Cycle 1]
    //========================================================
    wire [31:0] c_mult_result;       // [Cycle 0, same]
    reg  [31:0] r_mult_result;       // [Cycle 1]
    reg         r_valid_s1;          // [Cycle 1]
    
    assign c_mult_result = i_a * i_b;  // 조합 곱셈
    
    // 데이터: 리셋 불필요
    always_ff @(posedge i_clk) begin
        r_mult_result <= c_mult_result;  // [0 → 1]
    end
    
    // Valid: 리셋 필요
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_valid_s1 <= 1'b0;
        end else begin
            r_valid_s1 <= i_valid;       // [0 → 1]
        end
    end
    
    //========================================================
    // Stage 2: Accumulate
    // Input: [Cycle 1], Output: [Cycle 2]
    //========================================================
    wire [31:0] c_accum_result;      // [Cycle 1, same]
    reg  [31:0] r_accum_result;      // [Cycle 2]
    reg         r_valid_s2;          // [Cycle 2]
    
    assign c_accum_result = r_mult_result + 32'd100;  // 조합 덧셈
    
    // 데이터: 리셋 불필요
    always_ff @(posedge i_clk) begin
        r_accum_result <= c_accum_result;  // [1 → 2]
    end
    
    // Valid: 리셋 필요
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_valid_s2 <= 1'b0;
        end else begin
            r_valid_s2 <= r_valid_s1;    // [1 → 2]
        end
    end
    
    //========================================================
    // Stage 3: Saturation
    // Input: [Cycle 2], Output: [Cycle 3]
    //========================================================
    wire [31:0] c_sat_result;        // [Cycle 2, same]
    reg  [31:0] r_sat_result;        // [Cycle 3]
    reg         r_valid_s3;          // [Cycle 3]
    
    // 포화 로직
    assign c_sat_result = (r_accum_result > 32'hFFFF) ? 
                          32'hFFFF : r_accum_result;
    
    // 데이터: 리셋 불필요
    always_ff @(posedge i_clk) begin
        r_sat_result <= c_sat_result;  // [2 → 3]
    end
    
    // Valid: 리셋 필요
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_valid_s3 <= 1'b0;
        end else begin
            r_valid_s3 <= r_valid_s2;    // [2 → 3]
        end
    end
    
    //========================================================
    // Output
    //========================================================
    assign o_result = r_sat_result;  // [Cycle 3]
    assign o_valid  = r_valid_s3;    // [Cycle 3]

endmodule
```

### 타이밍 다이어그램

```
Cycle         0       1       2       3       4
              │       │       │       │       │
i_a, i_b ─────┼───A───┼───B───┼───C───┼───D───┼
i_valid  ─────┼───1───┼───1───┼───1───┼───1───┼
              │       │       │       │       │
c_mult   ─────┼─A*A───┼─B*B───┼─C*C───┼─D*D───┼  [same]
              │       │       │       │       │
r_mult   ─────┼───────┼─A*A───┼─B*B───┼─C*C───┼  [+1]
r_valid_s1────┼───────┼───1───┼───1───┼───1───┼
              │       │       │       │       │
c_accum  ─────┼───────┼─+100──┼─+100──┼─+100──┼  [same]
              │       │       │       │       │
r_accum  ─────┼───────┼───────┼─A*A+──┼─B*B+──┼  [+1]
r_valid_s2────┼───────┼───────┼───1───┼───1───┼
              │       │       │       │       │
c_sat    ─────┼───────┼───────┼─sat───┼─sat───┼  [same]
              │       │       │       │       │
r_sat    ─────┼───────┼───────┼───────┼─ResA──┼  [+1]
r_valid_s3────┼───────┼───────┼───────┼───1───┼
              │       │       │       │       │
o_result ─────┼───────┼───────┼───────┼─ResA──┼  [Cycle 3]
o_valid  ─────┼───────┼───────┼───────┼───1───┼
```

## Valid 신호 정렬

### 핵심 원칙

**Data와 Valid는 항상 같은 사이클에 유효해야 함**

```verilog
// GOOD: data와 valid가 같이 이동 (별도 always)
always_ff @(posedge i_clk) begin
    r_data <= c_processed_data;    // [N → N+1] 데이터
end

always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_valid <= 1'b0;
    end else begin
        r_valid <= i_valid;        // [N → N+1] valid
    end
end

// BAD: valid가 다른 경로
always_ff @(posedge i_clk) begin
    r_data <= c_processed_data;    // [N → N+1]
end
assign o_valid = i_valid;          // [N] - 1 cycle 빠름!
```

### Valid 파이프라인

```verilog
// N-stage 파이프라인의 valid (리셋 필요)
reg [STAGES-1:0] r_valid_pipe;

always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_valid_pipe <= '0;
    end else begin
        r_valid_pipe <= {r_valid_pipe[STAGES-2:0], i_valid};
    end
end

assign o_valid = r_valid_pipe[STAGES-1];  // N cycle later
```

## 사이클 분석 절차

### 1단계: 입력 사이클 정의

```verilog
// 모든 입력을 Cycle 0으로 정의
input wire [7:0] i_data;   // [Cycle 0]
input wire       i_valid;  // [Cycle 0]
input wire       i_mode;   // [Cycle 0]
```

### 2단계: 조합 로직 추적 (same cycle)

```verilog
// 조합 로직은 입력과 같은 사이클
wire [7:0] c_modified = i_data ^ 8'hFF;     // [Cycle 0, same]
wire       c_enabled  = i_valid & i_mode;   // [Cycle 0, same]
```

### 3단계: 레지스터 추적 (+1 cycle)

```verilog
// 데이터 레지스터 (리셋 불필요)
reg [7:0] r_data_d1;   // [Cycle 1]
reg [7:0] r_data_d2;   // [Cycle 2]

always_ff @(posedge i_clk) begin
    r_data_d1 <= c_modified;  // [0 → 1]
    r_data_d2 <= r_data_d1;   // [1 → 2]
end
```

### 4단계: 출력 사이클 확인

```verilog
// 출력 경로 역추적
assign o_result = r_data_d2;  // [Cycle 2]
// 총 레이턴시: 2 cycles (Cycle 0 입력 → Cycle 2 출력)
```

## 사이클 분석 템플릿

```verilog
//============================================================
// Module: <module_name>
// Latency: <N> cycles (i_* → o_*)
//============================================================
// Cycle Map:
//   [Cycle 0] i_data, i_valid 입력
//   [Cycle 0] c_* 조합 처리
//   [Cycle 1] r_stage1_* 
//   [Cycle 2] r_stage2_*
//   [Cycle N] o_result, o_valid 출력
//============================================================
// Reset Policy:
//   - Data path: No reset (gated by valid)
//   - Control (valid, ready, state): Async reset
//============================================================
module <module_name> (
    input  wire        i_clk,
    input  wire        i_rst_n,
    input  wire [7:0]  i_data,      // [Cycle 0]
    input  wire        i_valid,     // [Cycle 0]
    output wire [7:0]  o_result,    // [Cycle N]
    output wire        o_valid      // [Cycle N]
);
    // ... implementation with cycle comments
endmodule
```

## 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | 모듈 헤더에 총 레이턴시 명시? |
| ☐ | 모든 레지스터에 사이클 번호 주석? |
| ☐ | 조합 로직에 [same] 표시? |
| ☐ | data/valid 사이클 정렬 확인? |
| ☐ | 파이프라인 단계 수 일치? |
| ☐ | 데이터 경로: 리셋 없음? |
| ☐ | 제어 신호: 리셋 있음? |
