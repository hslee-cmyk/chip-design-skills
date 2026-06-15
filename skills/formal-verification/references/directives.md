# Formal Directives 상세 가이드

## assert — 속성 위반 탐지

```verilog
// 기본 패턴
always @(posedge clk) begin
    assert(property_expression);
end

// $past() 사용 — 이전 사이클 값 참조
always @(posedge clk) begin
    if (f_past_valid && out_valid)
        assert($past(in_valid));  // 이전 사이클 in_valid=1 이어야 함
end

// 복잡한 조건
always @(posedge clk) begin
    if (f_past_valid && r_state == DONE)
        assert($past(r_state) == WORKING || $past(r_state) == DONE);
end
```

**주의**: `assert` 추가 → illegal state 포함 → state space **증가** → 분석 시간 증가

## assume — 입력 제약

```verilog
// 유효한 입력 범위 제약
always @(posedge clk) begin
    assume(i_data < 16'd1000);
end

// 핸드셰이크 프로토콜 모델링
always @(posedge clk) begin
    if (!i_ready)
        assume(!i_valid);  // ready=0이면 valid도 0
end

// 환경 제약: 리셋 해제 후 최소 2사이클 대기
always @(posedge clk) begin
    if (f_past_valid && !$past(i_rst_n))
        assume(!i_valid);
end
```

**경고**: `assume(a==1 && a==0)` → UNSAT → Vacuous Pass (모든 assert가 trivially 통과)

## cover — 도달 가능성 검증

```verilog
// 특정 상태 도달 가능성
always @(posedge clk) begin
    cover(f_past_valid && r_state == DONE);
end

// 복합 조건
always @(posedge clk) begin
    cover(f_past_valid && out_valid && o_data == 8'hFF);
end
```

**결과 해석**:
- `PASS` → 해당 상태에 도달하는 시퀀스 존재 (`trace.vcd`에서 확인)
- `UNREACHABLE` → depth 부족 or 실제 도달 불가

## restrict — assert 무관 입력 제약

`assume`과 동일하게 동작하지만, SMT solver가 `restrict`로 표시된 제약은 COI(Cone of Influence) 계산에서 assert에 영향을 주지 않는다고 처리.

```verilog
// assert와 무관한 디버그 신호 제약
always @(posedge clk) begin
    restrict(i_debug_mode == 0);  // 디버그 모드 off 고정
end
```

## f_past_valid 패턴

```verilog
`ifdef FORMAL
    reg f_past_valid;
    initial f_past_valid = 0;
    always @(posedge clk) f_past_valid <= 1;

    // 첫 사이클($past 미정의) 보호
    always @(posedge clk) begin
        if (f_past_valid) begin
            // $past() 안전하게 사용 가능
        end
    end
`endif
```

## 다중 클럭 도메인에서 f_past_valid

각 클럭 도메인마다 별도 `f_past_valid` 필요:

```verilog
`ifdef FORMAL
    reg f_past_valid_clk1, f_past_valid_clk2;
    initial {f_past_valid_clk1, f_past_valid_clk2} = 2'b0;
    always @(posedge clk1) f_past_valid_clk1 <= 1;
    always @(posedge clk2) f_past_valid_clk2 <= 1;
`endif
```

## Directive 선택 플로우

```
속성 검증?  → assert
입력 범위?  → assume (COI 내) / restrict (COI 외)
도달 확인?  → cover
```
