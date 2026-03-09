# Always Block Patterns

## 허용 사례: 통합형 (다중 출력 허용)

### 허용 사례 1: 단순 Capture (FSM State Register, Pipeline)

```verilog
// ✅ GOOD: 단순 capture는 다중 출력 허용
// 제어 구조가 완전히 동일 (리셋 + 단순 할당)
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_state       <= S_IDLE;
        r_data_valid  <= 1'b0;
        r_byte_count  <= '0;
    end else begin
        r_state       <= c_next_state;      // FSM state
        r_data_valid  <= c_next_valid;      // 동일 타이밍
        r_byte_count  <= c_next_byte_count; // 동일 타이밍
    end
end
```

### 허용 사례 2: 관련 카운터 그룹

```verilog
// ✅ GOOD: 구조적으로 유사한 카운터들
// 동일한 enable 조건, 동일한 리셋 구조
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_bit_cnt   <= '0;
        r_byte_cnt  <= '0;
        r_frame_cnt <= '0;
    end else if (i_enable) begin
        r_bit_cnt   <= c_next_bit_cnt;
        r_byte_cnt  <= c_next_byte_cnt;
        r_frame_cnt <= c_next_frame_cnt;
    end
end
```

### 허용 사례 3: 파이프라인 데이터 경로

```verilog
// ✅ GOOD: 파이프라인 단계별 데이터 (리셋 불필요)
// 모두 단순 지연, 동일 구조
always_ff @(posedge i_clk) begin
    r_data_d1 <= i_data;
    r_data_d2 <= r_data_d1;
    r_data_d3 <= r_data_d2;
end

// ✅ GOOD: 파이프라인 valid 신호들 (리셋 필요)
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_valid_d1 <= 1'b0;
        r_valid_d2 <= 1'b0;
        r_valid_d3 <= 1'b0;
    end else begin
        r_valid_d1 <= i_valid;
        r_valid_d2 <= r_valid_d1;
        r_valid_d3 <= r_valid_d2;
    end
end
```

### 허용 사례 4: 제어 구조가 약간 다르지만 단순한 경우

제어 구조가 완전히 동일하지 않더라도, **로직이 단순하고 가독성에 영향이 없다면** 허용:

```verilog
// ✅ GOOD: 제어 구조가 약간 다르지만 단순하여 허용
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_count <= '0;
        r_done  <= 1'b0;
    end else begin
        r_count <= r_count + 1'b1;           // 무조건 증가
        r_done  <= (r_count == MAX_COUNT);   // 단순 비교 (1줄)
    end
end

// ✅ GOOD: enable 조건만 약간 다른 경우
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_byte_cnt  <= '0;
        r_bit_cnt   <= '0;
    end else begin
        r_byte_cnt  <= i_byte_en ? r_byte_cnt + 1'b1 : r_byte_cnt;
        r_bit_cnt   <= i_bit_en  ? r_bit_cnt + 1'b1  : r_bit_cnt;
    end
end
```

---

## 분리 권장: 제어 구조가 복잡하게 다른 경우

제어 구조 차이가 크거나 복잡하여 **가독성이 저하되는 경우** 분리 권장:

```verilog
// ⚠️ 분리 권장: 제어 구조 차이가 커서 가독성 저하
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_count <= '0;
        r_done  <= 1'b0;
    end else begin
        r_count <= r_count + 1'b1;
        if (r_count == MAX_COUNT)        // 복잡한 조건 분기
            r_done <= 1'b1;
        else if (i_start)
            r_done <= 1'b0;
        else if (i_abort && r_state == S_RUN)
            r_done <= 1'b1;
    end
end

// ✅ BETTER: 분리하여 가독성 향상
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) r_count <= '0;
    else          r_count <= r_count + 1'b1;
end

always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n)                              r_done <= 1'b0;
    else if (r_count == MAX_COUNT)             r_done <= 1'b1;
    else if (i_start)                          r_done <= 1'b0;
    else if (i_abort && r_state == S_RUN)      r_done <= 1'b1;
end
```

상황별 가이드 테이블: SKILL.md §2 참조
