# FSM Design Patterns

## ⚠️ 중요: 작성/분석 규칙

```
┌─────────────────────────────────────────────────────────────┐
│  📝 작성 시: 항상 2-process 패턴만 사용                     │
│  🔍 분석 시: 모든 FSM 패턴 인식 (1/2/3-process)            │
└─────────────────────────────────────────────────────────────┘
```

## 2-Process vs 3-Process 비교

| 스타일 | 구조 | 용도 |
|--------|------|------|
| **2-process** | state_reg + (next_state + output) | ✅ 작성 시 사용 |
| **3-process** | state_reg + next_state + output | 🔍 분석용 |

---

## 2-Process FSM Template (✅ 작성 시 사용)

### 기본 구조

```verilog
module fsm_example (
    input  wire       i_clk,
    input  wire       i_rst_n,
    input  wire       i_start,
    input  wire       i_done,
    output reg        o_busy,
    output reg        o_complete
);

    //--------------------------------------------------------
    // State Encoding
    //--------------------------------------------------------
    // One-hot (8 states 미만)
    localparam [3:0]
        S_IDLE    = 4'b0001,
        S_SETUP   = 4'b0010,
        S_PROCESS = 4'b0100,
        S_DONE    = 4'b1000;
    
    reg [3:0] r_state;
    reg [3:0] c_next_state;
    
    //--------------------------------------------------------
    // Process 1: State Register
    //--------------------------------------------------------
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_state <= S_IDLE;
        end else begin
            r_state <= c_next_state;
        end
    end
    
    //--------------------------------------------------------
    // Process 2: Next State + Output (Mealy)
    //--------------------------------------------------------
    always_comb begin
        //====================================================
        // ✅ 기본값 할당 = Latch 완전 방지
        // - 블록 시작에서 모든 출력에 기본값 할당
        // - 이후 if/case에서 else/default 없어도 latch 없음!
        //====================================================
        c_next_state = r_state;   // 기본값: 상태 유지
        o_busy = 1'b0;            // 기본값: 비활성
        o_complete = 1'b0;        // 기본값: 비활성

        case (r_state)
            S_IDLE: begin
                if (i_start) begin
                    c_next_state = S_SETUP;
                end
                // else 불필요 - 기본값(r_state)이 유지됨
            end

            S_SETUP: begin
                o_busy = 1'b1;
                c_next_state = S_PROCESS;
            end

            S_PROCESS: begin
                o_busy = 1'b1;
                if (i_done) begin
                    c_next_state = S_DONE;
                end
            end

            S_DONE: begin
                o_complete = 1'b1;
                c_next_state = S_IDLE;
            end

            default: begin
                c_next_state = S_IDLE;  // 선택적 - 안전을 위해
            end
        endcase
    end

endmodule
```

---

## 3-Process FSM Template (🔍 분석용 - 작성 시 사용 금지)

기존 코드 분석 시 참고용. 새 코드 작성 시에는 반드시 2-process 사용:

```verilog
module fsm_3process (
    input  wire       i_clk,
    input  wire       i_rst_n,
    input  wire       i_start,
    input  wire       i_done,
    output reg        o_busy,
    output reg        o_complete
);

    localparam [2:0]
        S_IDLE    = 3'b001,
        S_PROCESS = 3'b010,
        S_DONE    = 3'b100;
    
    reg [2:0] r_state;
    reg [2:0] c_next_state;

    //--------------------------------------------------------
    // Process 1: State Register (순차)
    //--------------------------------------------------------
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_state <= S_IDLE;
        end else begin
            r_state <= c_next_state;
        end
    end
    
    //--------------------------------------------------------
    // Process 2: Next State Logic (조합)
    //--------------------------------------------------------
    always_comb begin
        c_next_state = r_state;  // default: hold
        
        case (r_state)
            S_IDLE: begin
                if (i_start) c_next_state = S_PROCESS;
            end
            S_PROCESS: begin
                if (i_done) c_next_state = S_DONE;
            end
            S_DONE: begin
                c_next_state = S_IDLE;
            end
            default: c_next_state = S_IDLE;
        endcase
    end
    
    //--------------------------------------------------------
    // Process 3: Output Logic (조합 또는 순차)
    //--------------------------------------------------------
    // Mealy 출력 (조합) - 입력에 즉시 반응
    always_comb begin
        o_busy     = (r_state == S_PROCESS);
        o_complete = (r_state == S_DONE);
    end

endmodule
```

### Moore 출력 (순차)

상태에만 의존하고 1 cycle 지연이 허용될 때:

```verilog
// Process 3: Output Logic (순차 - Moore)
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        o_busy     <= 1'b0;
        o_complete <= 1'b0;
    end else begin
        o_busy     <= (c_next_state == S_PROCESS);
        o_complete <= (c_next_state == S_DONE);
    end
end
```

---

## State Encoding

### One-hot (< 8 states) - 권장

```verilog
// 장점: 빠른 디코딩, 글리치 감소
// 단점: 플립플롭 많이 사용

localparam [4:0]
    S_IDLE  = 5'b00001,
    S_READ  = 5'b00010,
    S_CALC  = 5'b00100,
    S_WRITE = 5'b01000,
    S_DONE  = 5'b10000;

// State 체크가 단순함
assign c_is_idle = r_state[0];
assign c_is_read = r_state[1];
```

### Binary (≥ 8 states)

```verilog
// 장점: 면적 효율
// 단점: 디코딩 로직 복잡

localparam [3:0]
    S_IDLE    = 4'd0,
    S_INIT    = 4'd1,
    S_READ    = 4'd2,
    S_CALC1   = 4'd3,
    S_CALC2   = 4'd4,
    S_CALC3   = 4'd5,
    S_WRITE   = 4'd6,
    S_VERIFY  = 4'd7,
    S_DONE    = 4'd8,
    S_ERROR   = 4'd9;
```

## 타이밍 크리티컬 출력

### 문제: Mealy 출력 지연

```
         ┌─────────────────────────────────────┐
Clock    │  입력 → 조합로직 → 출력             │
         │         긴 경로 = 타이밍 위반 가능  │
         └─────────────────────────────────────┘
```

### 해결: 출력 레지스터링

```verilog
module fsm_registered_output (
    input  wire i_clk,
    input  wire i_rst_n,
    input  wire i_trigger,
    output wire o_result       // 타이밍 크리티컬
);

    localparam [1:0]
        S_IDLE = 2'b01,
        S_WORK = 2'b10;
    
    reg [1:0] r_state;
    reg [1:0] c_next_state;
    
    // 조합 출력 (내부)
    reg c_result;
    
    // 레지스터된 출력
    reg r_result_reg;
    
    // State register
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) r_state <= S_IDLE;
        else        r_state <= c_next_state;
    end
    
    // Next state + combinational output
    always_comb begin
        c_next_state = r_state;
        c_result = 1'b0;
        
        case (r_state)
            S_IDLE: begin
                if (i_trigger) c_next_state = S_WORK;
            end
            S_WORK: begin
                c_result = 1'b1;  // 조합 출력
                c_next_state = S_IDLE;
            end
            default: c_next_state = S_IDLE;
        endcase
    end
    
    // Output register (1 cycle delay)
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) r_result_reg <= 1'b0;
        else        r_result_reg <= c_result;
    end
    
    assign o_result = r_result_reg;

endmodule
```

## Counter 포함 FSM

```verilog
module fsm_with_counter (
    input  wire       i_clk,
    input  wire       i_rst_n,
    input  wire       i_start,
    input  wire [7:0] i_count,
    output reg        o_busy,
    output reg        o_done
);

    localparam [1:0]
        S_IDLE  = 2'b01,
        S_COUNT = 2'b10;
    
    reg [1:0] r_state;
    reg [1:0] c_next_state;
    reg [7:0] r_counter;
    reg [7:0] r_target;
    
    // State register
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) r_state <= S_IDLE;
        else        r_state <= c_next_state;
    end
    
    // Counter & target register
    always_ff @(posedge i_clk or negedge i_rst_n) begin
        if (!i_rst_n) begin
            r_counter <= '0;
            r_target  <= '0;
        end else begin
            case (r_state)
                S_IDLE: begin
                    if (i_start) begin
                        r_counter <= '0;
                        r_target  <= i_count;
                    end
                end
                S_COUNT: begin
                    r_counter <= r_counter + 1'b1;
                end
            endcase
        end
    end
    
    // Next state + output
    always_comb begin
        c_next_state = r_state;
        o_busy = 1'b0;
        o_done = 1'b0;
        
        case (r_state)
            S_IDLE: begin
                if (i_start) c_next_state = S_COUNT;
            end
            S_COUNT: begin
                o_busy = 1'b1;
                if (r_counter == r_target - 1) begin
                    c_next_state = S_IDLE;
                    o_done = 1'b1;
                end
            end
            default: c_next_state = S_IDLE;
        endcase
    end

endmodule
```

## FSM 사이클 다이어그램

```
Cycle       N       N+1     N+2
            │       │       │
r_state ────┼─IDLE──┼─RUN───┼─DONE──
            │       │       │
i_start ────┼───1───┤       │
            │       │       │
c_next  ────┼─RUN───┤       │  [same cycle]
            │       │       │
o_busy  ────┼───0───┼───1───┼───0───  [same cycle as state]
```

## FSM 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | 2-process 스타일인가? |
| ☐ | Mealy machine 기본인가? |
| ☐ | Default 값 설정 (latch 방지) |
| ☐ | default case 있는가? |
| ☐ | One-hot (< 8 states) / Binary (≥ 8)? |
| ☐ | 타이밍 크리티컬 출력 레지스터링? |
| ☐ | 리셋 시 초기 상태 설정? |
