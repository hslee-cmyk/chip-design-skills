# Synthesis Checklist

## Latch 방지

### ⚠️ 핵심 원칙: 기본값 할당 = Latch 완전 방지

```
┌─────────────────────────────────────────────────────────────┐
│         Latch 생성 여부 판단 기준                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Latch 없음: always 블록 시작에서 모든 출력에 기본값    │
│     → 이후 if/case에서 else/default 없어도 OK!             │
│     → 기본값이 유지되므로 latch 불필요                     │
│                                                             │
│  ❌ Latch 생성: 기본값 없이 조건부 할당만 있는 경우        │
│     → 일부 조건에서 값이 정의되지 않아 latch 생성          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Latch가 생성되지 않는 패턴 (올바른 코드)

```verilog
//============================================================
// GOOD 1: 블록 시작에서 기본값 할당 (권장 패턴)
// → else 없어도 latch 생성 안 됨!
//============================================================
always_comb begin
    c_data = '0;           // ← 기본값 먼저 할당
    c_valid = 1'b0;        // ← 모든 출력에 기본값

    if (sel) begin
        c_data = i_a;      // 조건 충족 시 덮어쓰기
    end
    // else 불필요 - 기본값 '0이 유지됨
end

//============================================================
// GOOD 2: FSM 조합 로직 (기본값 + case)
// → default case 없어도 latch 생성 안 됨! (기본값이 있으므로)
//============================================================
always_comb begin
    // 블록 시작에서 모든 출력에 기본값 할당
    c_next_state = r_state;  // ← 기본값: 상태 유지
    o_busy = 1'b0;           // ← 기본값
    o_done = 1'b0;           // ← 기본값

    case (r_state)
        S_IDLE: begin
            if (i_start) c_next_state = S_RUN;
        end
        S_RUN: begin
            o_busy = 1'b1;
            if (i_complete) c_next_state = S_DONE;
        end
        S_DONE: begin
            o_done = 1'b1;
            c_next_state = S_IDLE;
        end
        // default 생략 가능 - 기본값(r_state 유지)이 이미 있음
    endcase
end

//============================================================
// GOOD 3: default case만 사용
//============================================================
always_comb begin
    case (sel)
        2'b00:   c_data = i_a;
        2'b01:   c_data = i_b;
        default: c_data = '0;  // 모든 나머지 경우 처리
    endcase
end
```

### Latch가 생성되는 패턴 (문제 코드)

```verilog
// BAD: 기본값 없음 + else 없음 → Latch 생성!
always_comb begin
    if (sel)
        c_data = i_a;
    // else 없고 기본값도 없음 → sel=0일 때 c_data 미정의!
end

// BAD: 기본값 없음 + default 없음 → Latch 생성!
always_comb begin
    case (sel)
        2'b00: c_data = i_a;
        2'b01: c_data = i_b;
        // 2'b10, 2'b11일 때 c_data 미정의!
    endcase
end
```

### 🔍 코드 분석 시 주의사항

```
┌─────────────────────────────────────────────────────────────┐
│  코드 분석 시 Latch 판단 순서                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. always_comb 블록 시작 부분 확인                        │
│  2. 모든 출력 신호에 기본값이 할당되어 있는가?             │
│     → YES: Latch 없음 (if/case 완전성 불필요)              │
│     → NO:  if/case 완전성 확인 필요                        │
│                                                             │
│  ⚠️ 기본값 할당 패턴을 보고 latch 문제로 잘못 보고 금지!   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Blocking vs Non-blocking

### 규칙

| 블록 | 할당 | 이유 |
|------|------|------|
| `always_ff` | `<=` (Non-blocking) | 레지스터 동작 |
| `always_comb` | `=` (Blocking) | 조합 로직 |

```verilog
// Sequential: Non-blocking
always_ff @(posedge i_clk or negedge i_rst_n) begin
    r_data <= i_data;        // <=
    r_valid <= i_valid;      // <=
end

// Combinational: Blocking
always_comb begin
    c_sum = i_a + i_b;       // =
    c_carry = (c_sum > 255); // = (순서 의존)
end
```

## 클럭 게이팅 금지

```verilog
// BAD: 조합 로직으로 클럭 생성
wire w_gated_clk = i_clk & enable;  // 글리치 발생!

always_ff @(posedge w_gated_clk) begin
    r_data <= i_data;
end

// GOOD: Enable 사용
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (enable)
        r_data <= i_data;
end
```

## 리셋 정책

### 리셋 필요 여부에 따른 sensitivity list

```verilog
// 리셋 필요 (제어 신호: state, valid, ready, count 등)
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_state <= S_IDLE;
        r_valid <= 1'b0;
        r_count <= '0;
    end else begin
        // ...
    end
end

// 리셋 불필요 (데이터 경로: valid로 게이팅됨)
always_ff @(posedge i_clk) begin
    r_data <= i_data;
end
```

### 리셋 필요 여부 판단

| 레지스터 타입 | 리셋 | sensitivity list |
|--------------|------|------------------|
| FSM 상태 | ✅ | `@(posedge i_clk or negedge i_rst_n)` |
| valid/ready | ✅ | `@(posedge i_clk or negedge i_rst_n)` |
| 카운터 | ✅ | `@(posedge i_clk or negedge i_rst_n)` |
| 데이터 경로 | ❌ | `@(posedge i_clk)` |
| 파이프라인 데이터 | ❌ | `@(posedge i_clk)` |

## 멀티드라이버 금지

```verilog
// BAD: 같은 신호를 여러 블록에서 할당
always_ff @(posedge i_clk) begin
    r_data <= i_a;
end

always_ff @(posedge i_clk) begin
    r_data <= i_b;  // ERROR: Multi-driver!
end

// GOOD: 하나의 블록에서만 할당
always_ff @(posedge i_clk) begin
    if (sel)
        r_data <= i_a;
    else
        r_data <= i_b;
end
```

## Initial 블록 (FPGA vs ASIC)

```verilog
// FPGA: 동작함
// ASIC: 무시됨 (합성 불가)
initial begin
    r_counter = 0;  // FPGA에서만!
end

// 권장: 리셋으로 초기화 (둘 다 동작)
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n)
        r_counter <= '0;
    else
        r_counter <= r_counter + 1'b1;
end
```

## 합성 전 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | 기본값 할당 (권장) 또는 모든 if에 else 있는가? |
| ☐ | 기본값 할당 (권장) 또는 모든 case에 default 있는가? |
| ☐ | always_ff에서 `<=` 사용? |
| ☐ | always_comb에서 `=` 사용? |
| ☐ | 조합 로직으로 클럭 생성 없는가? |
| ☐ | 같은 신호 여러 블록 할당 없는가? |
| ☐ | 리셋 정책 적절한가? (제어=리셋 있음, 데이터=리셋 없음) |
| ☐ | CDC: Slow→Fast=2FF/Pulse Sync, Fast→Slow=Handshake 적용? |
| ☐ | initial 블록 대신 리셋 사용? |
| ☐ | Bit-Width: sized 변수 max value < 2^W? localparam unsized 권장? |
| ☐ | Bit-Width: $clog2 사용? (custom log2는 N≠2^k일 때 1 부족) |

## Bit-Width Safety

### 핵심 원칙

localparam/parameter에 값을 할당할 때 **explicit bit-width가 값을 잘라내지 않는지** 반드시 검증.

### 위험 패턴: Parameter 파생 Bit-Width

```verilog
// ★ 실제 버그 사례: FIFO pointer width truncation
parameter FIFO_SIZE    = 7;
parameter PTR_WIDTH    = log2(FIFO_SIZE);  // custom log2 → 2 (floor)

// BAD: explicit bit-width [PTR_WIDTH-1:0] = [1:0] = 2비트
// FIFO_SIZE-1 = 6 → 3비트 필요 → truncation!
localparam [PTR_WIDTH-1:0] MAX_PTR = FIFO_SIZE - 1;  // 6→2 (silent truncation!)

// GOOD: unsized — 32-bit default, 값 보존
localparam MAX_PTR = FIFO_SIZE - 1;  // 6 유지
```

### $clog2 vs custom log2

```verilog
// $clog2: ceiling log2 (SystemVerilog 표준) — 포인터 폭에 적합
parameter PTR_W = $clog2(FIFO_SIZE);  // $clog2(7)=3, $clog2(8)=3

// custom log2 함수: 대부분 floor 반환 — 2^k 아닐 때 1 부족!
// log2(7)=2 (WRONG for addressing 0-6)
// log2(8)=3 (OK for power of 2)
```

| 함수 | N=7 | N=8 | N=9 | N=16 |
|------|-----|-----|-----|------|
| `$clog2(N)` | **3** | 3 | **4** | 4 |
| `floor(log2(N))` | **2** | 3 | **3** | 4 |

### 검증 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | localparam에 explicit bit-width가 필요한가? → 불필요하면 unsized |
| ☐ | `[W-1:0] var = expr` : max(expr) < 2^W 인가? (파라미터 전 범위) |
| ☐ | W가 log2 계열 함수에서 파생되었나? → $clog2 사용 확인 |
| ☐ | 파라미터가 2의 거듭제곱이 아닌 값을 가질 수 있나? → 경계값 테스트 |
| ☐ | pointer width로 FIFO/Memory 전체를 인덱싱할 수 있나? |

### 추가 위험 패턴

```verilog
// BAD: 카운터 비트폭 부족
parameter MAX_COUNT = 100;
reg [6:0] r_count;  // [6:0] max=127 → 100은 OK
// BUT: MAX_COUNT가 200으로 변경되면? → 200>127, truncation!

// GOOD: 파라미터에서 폭 자동 계산
reg [$clog2(MAX_COUNT+1)-1:0] r_count;  // 항상 충분한 폭

// BAD: 비트 연산에서 implicit truncation
wire [7:0] w_sum = i_a + i_b;  // 8-bit + 8-bit = 9-bit → MSB 손실!

// GOOD: 캐리 비트 포함
wire [8:0] w_sum = i_a + i_b;  // 9-bit → 값 보존
```

## 경고 메시지 확인

합성 후 다음 경고 확인:

```
WARNING: Latch inferred for signal 'xxx'
WARNING: Multi-driven net 'xxx'
WARNING: Unconnected port 'xxx'
WARNING: Width mismatch in assignment
```
