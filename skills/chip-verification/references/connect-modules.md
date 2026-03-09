# Connect Module Patterns

## 개요

Connect Module은 서로 다른 신호 도메인을 연결하는 브릿지 역할.

```
┌──────────┐     ┌────────────────┐     ┌──────────┐
│ Digital  │────►│ Connect Module │────►│ Analog   │
│ (logic)  │     │ (d2a, a2d)     │     │(electrical)
└──────────┘     └────────────────┘     └──────────┘
```

## Digital ↔ Electrical (Spectre 연결용)

### D2A (Digital to Analog)

```verilog
// d2a_1v8.vams - 1.8V 도메인
connectmodule d2a_1v8 (input logic d, output electrical a);
    parameter real v0  = 0.0;      // logic 0 전압
    parameter real v1  = 1.8;      // logic 1 전압
    parameter real tr  = 100p;     // rise time
    parameter real tf  = 100p;     // fall time
    
    analog begin
        V(a) <+ transition(d ? v1 : v0, 0, tr, tf);
    end
endmodule

// d2a_3v3.vams - 3.3V 도메인
connectmodule d2a_3v3 (input logic d, output electrical a);
    parameter real v0  = 0.0;
    parameter real v1  = 3.3;
    parameter real tr  = 200p;
    parameter real tf  = 200p;
    
    analog begin
        V(a) <+ transition(d ? v1 : v0, 0, tr, tf);
    end
endmodule
```

### A2D (Analog to Digital)

```verilog
// a2d_1v8.vams - 1.8V 도메인
connectmodule a2d_1v8 (input electrical a, output logic d);
    parameter real vth  = 0.9;     // threshold (VDD/2)
    parameter real vhys = 0.1;     // hysteresis
    
    real vth_hi, vth_lo;
    
    analog begin
        @(initial_step) begin
            vth_hi = vth + vhys/2;
            vth_lo = vth - vhys/2;
        end
    end
    
    // Schmitt trigger 동작
    assign d = (V(a) > vth_hi) ? 1'b1 :
               (V(a) < vth_lo) ? 1'b0 : d;
endmodule

// 간단한 버전 (hysteresis 없음)
connectmodule a2d_simple (input electrical a, output logic d);
    parameter real vth = 0.9;
    assign d = V(a) > vth;
endmodule
```

## Digital ↔ Wreal (행동 모델용)

### L2R (Logic to Real)

```verilog
// l2r.vams
connectmodule l2r (input logic l, output wreal r);
    parameter real v0 = 0.0;
    parameter real v1 = 1.8;
    
    assign r = l ? v1 : v0;
endmodule

// l2r with transition
connectmodule l2r_smooth (input logic l, output wreal r);
    parameter real v0 = 0.0;
    parameter real v1 = 1.8;
    parameter real tau = 1n;  // time constant
    
    real target;
    
    always @(l) target = l ? v1 : v0;
    
    // 1차 RC 응답 모델링
    analog begin
        r <+ laplace_nd(target, {1}, {1, tau});
    end
endmodule
```

### R2L (Real to Logic)

```verilog
// r2l.vams
connectmodule r2l (input wreal r, output logic l);
    parameter real vth = 0.9;
    
    assign l = (r > vth) ? 1'b1 : 1'b0;
endmodule

// r2l with hysteresis
connectmodule r2l_hys (input wreal r, output logic l);
    parameter real vth_hi = 1.0;
    parameter real vth_lo = 0.8;
    
    logic state;
    
    always @(r) begin
        if (r > vth_hi)      state = 1'b1;
        else if (r < vth_lo) state = 1'b0;
        // else hold
    end
    
    assign l = state;
endmodule
```

## 차동 신호 Connect Module

```verilog
// 차동 D2A
connectmodule d2a_diff (
    input  logic d,
    output electrical outp,
    output electrical outn
);
    parameter real vcm  = 0.9;    // common mode
    parameter real vdiff = 0.4;   // differential swing
    parameter real tr = 50p;
    parameter real tf = 50p;
    
    analog begin
        V(outp) <+ transition(d ? (vcm + vdiff/2) : (vcm - vdiff/2), 0, tr, tf);
        V(outn) <+ transition(d ? (vcm - vdiff/2) : (vcm + vdiff/2), 0, tr, tf);
    end
endmodule

// 차동 A2D
connectmodule a2d_diff (
    input  electrical inp,
    input  electrical inn,
    output logic d
);
    parameter real vth = 0.0;  // differential threshold
    
    assign d = V(inp, inn) > vth;
endmodule
```

## Bus Connect Module

```verilog
// 8-bit bus D2A
connectmodule d2a_bus8 (
    input  logic [7:0] d,
    output electrical [7:0] a
);
    parameter real v0 = 0.0;
    parameter real v1 = 1.8;
    parameter real tr = 100p;
    parameter real tf = 100p;
    
    genvar i;
    generate
        for (i = 0; i < 8; i = i + 1) begin : gen_d2a
            analog begin
                V(a[i]) <+ transition(d[i] ? v1 : v0, 0, tr, tf);
            end
        end
    endgenerate
endmodule
```

## Connect Rules (자동 삽입)

```verilog
// connectrules.vams
connectrules ams_rules;
    // 1.8V 도메인
    connect d2a_1v8 #(.v1(1.8)) a2d_1v8 #(.vth(0.9));
    
    // 3.3V 도메인 (포트 이름 패턴 매칭)
    connect d2a_3v3 #(.v1(3.3)) a2d_3v3 #(.vth(1.65)) 
        merged with (* portname == "*_3v3*" *);
    
    // wreal 연결
    connect l2r r2l;
endconnectrules
```

## 사용 예시

```verilog
// ams_top.vams
module ams_top;
    // Digital 신호
    logic clk, rst_n;
    logic [7:0] digital_data;
    
    // Electrical 신호 (Spectre 연결)
    electrical vref;
    electrical [7:0] analog_out;
    
    // Digital DUT
    my_digital_dut u_digital (
        .clk(clk),
        .data_out(digital_data)  // logic
    );
    
    // Connect module이 자동 삽입됨
    // digital_data (logic) → analog_in (electrical)
    
    // Spectre DAC
    dac_8bit u_dac (
        .din(digital_data),      // 자동으로 d2a 삽입
        .vref(vref),
        .aout(analog_out)
    );
endmodule
```
