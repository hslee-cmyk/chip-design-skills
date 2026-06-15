# SVA (SystemVerilog Assertions) 패턴 가이드

## 절차적 Formal vs SVA 선택 기준

```
단일 사이클 조건 / Verilog 설계     → 절차적 (always @(posedge clk) assert(...))
멀티사이클 시퀀스 / SystemVerilog    → SVA concurrent assertion
표준 준수 / 툴 이식성 필요           → SVA
```

---

## Immediate vs Concurrent Assertion

```systemverilog
// Immediate: 실행 시점의 값만 검사 (시뮬레이션 전용)
always @(posedge clk)
    assert (count < MAX);  // 이 순간만 검사

// Concurrent: 클럭 기준, 시간 관계 표현 가능 (formal + sim)
assert property (@(posedge clk) count < MAX);
```

---

## disable iff — Reset 처리

```systemverilog
// reset 활성 구간은 assertion 비활성화
assert property (
    @(posedge clk) disable iff (!rst_n)
    property_expression
);

// 절차적 동치
always @(posedge clk) begin
    if (rst_n)  // rst_n=1 일 때만 검사
        assert(property_expression);
end
```

---

## Temporal Operators 상세

### `##N` — 사이클 지연

```systemverilog
// req 후 정확히 2사이클 뒤 ack
assert property (@(posedge clk) disable iff (!rst_n)
    req |-> ##2 ack);

// req 후 1~4사이클 내 ack
assert property (@(posedge clk) disable iff (!rst_n)
    req |-> ##[1:4] ack);

// req 후 즉시부터 4사이클 내 ack
assert property (@(posedge clk) disable iff (!rst_n)
    req |-> ##[0:4] ack);
```

### `|->` vs `|=>` — Implication

```systemverilog
// |-> overlapping: 선행조건 사이클 = 결론 사이클
assert property (@(posedge clk)
    valid |-> !error);        // valid인 사이클에 error 없어야

// |=> non-overlapping: 선행조건 다음 사이클에 결론
assert property (@(posedge clk)
    start |=> processing);    // start 다음 사이클에 processing
```

### `always` / `s_eventually`

```systemverilog
// 항상 성립
assert property (@(posedge clk) disable iff (!rst_n)
    always (state inside {IDLE, WORKING, DONE}));

// 언젠가 성립 (cover와 유사)
assert property (@(posedge clk) disable iff (!rst_n)
    start |-> s_eventually done);
```

---

## sequence 블록

```systemverilog
// 재사용 가능한 시간 패턴 정의
sequence s_req_ack;
    req ##[1:3] ack;
endsequence

sequence s_valid_data (sig);
    valid && (sig != 0);
endsequence

// property에서 사용
property p_req_always_acked;
    @(posedge clk) disable iff (!rst_n)
    req |-> s_req_ack;
endproperty

assert property (p_req_always_acked);
```

---

## property 블록

```systemverilog
// FSM 상태 유효성
property p_valid_state;
    @(posedge clk) disable iff (!rst_n)
    state inside {IDLE, FETCH, EXEC, WRITE};
endproperty

// 출력 인과관계
property p_output_causality;
    @(posedge clk) disable iff (!rst_n)
    out_valid |-> $past(in_valid, 2);  // 2사이클 전 in_valid
endproperty

// FIFO no-underflow
property p_no_underflow;
    @(posedge clk) disable iff (!rst_n)
    (rd_en && empty) == 0;
endproperty

assert property (p_valid_state);
assert property (p_output_causality);
assert property (p_no_underflow);
```

---

## sby에서 SVA 사용

### .sby 설정

```ini
[options]
mode bmc
depth 25

[engines]
smtbmc z3

[script]
read -sv module.sv          # -sv 플래그 (SystemVerilog)
hierarchy -top module
prep -top module

[files]
src/module.sv
```

### SystemVerilog 파일 구조

```systemverilog
module top (
    input  logic clk,
    input  logic rst_n,
    input  logic in_valid,
    output logic out_valid
);
    // ... RTL 구현 ...

`ifdef FORMAL
    // SVA concurrent assertions
    assert property (@(posedge clk) disable iff (!rst_n)
        in_valid |=> out_valid);

    assume property (@(posedge clk) disable iff (!rst_n)
        $stable(in_valid) || !in_valid);

    cover property (@(posedge clk)
        in_valid ##1 out_valid);
`endif

endmodule
```

---

## $past() 와 SVA 비교

| 목적 | 절차적 `$past()` | SVA |
|------|-----------------|-----|
| 이전 사이클 값 | `$past(sig)` | `sig` (with `\|=>`) |
| 2사이클 전 | `$past(sig, 2)` | `sig ##2 condition` |
| 원인→결과 | `if (f_past_valid && out) assert($past(in))` | `in \|=> out` |

---

## Yosys SVA 지원 범위 (v0.56~v0.64)

| 기능 | 지원 |
|------|------|
| `assert/assume/cover property` | ✅ |
| `##N`, `##[m:n]` | ✅ |
| `\|->`, `\|=>` | ✅ |
| `disable iff` | ✅ |
| `sequence`/`property` 블록 | ✅ (기본) |
| `always`, `s_eventually` | 부분적 |
| 중첩 sequence/복잡한 반복 | ⚠️ 일부 미지원 |
| PSL assertions | ❌ |
