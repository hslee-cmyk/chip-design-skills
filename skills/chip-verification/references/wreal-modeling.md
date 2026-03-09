# Wreal Modeling Guide

## Wreal이란?

**Wreal (Wire Real)**: 실수 값을 전달하는 와이어 타입. 
아날로그 신호를 이벤트 기반으로 모델링하여 시뮬레이션 속도 향상.

```
┌─────────────────────────────────────────────────────────┐
│          Simulation Speed vs Accuracy                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Fast    ──────────────────────────────────►  Slow     │
│                                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ Digital │  │  Wreal  │  │ Verilog │  │ Spectre │   │
│  │ (logic) │  │ (real)  │  │  -AMS   │  │ (SPICE) │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
│                                                         │
│  Low     ──────────────────────────────────►  High     │
│                        Accuracy                         │
└─────────────────────────────────────────────────────────┘
```

## Wreal 기본 사용

### 선언

```verilog
// SystemVerilog에서
wreal vout;           // 단일 wreal
wreal [7:0] bus_v;    // wreal 버스 (각 비트가 real)

// 또는 real 타입 사용
real vout_real;
```

### 할당

```verilog
// Continuous assignment
assign vout = (sel) ? 1.8 : 0.0;

// Procedural assignment
always @(posedge clk) begin
    vout <= computed_voltage;
end
```

## Wreal ADC 모델

```verilog
// adc_wreal.sv - 8-bit ADC 행동 모델
module adc_wreal #(
    parameter int BITS = 8,
    parameter real VREF = 1.8,
    parameter real OFFSET = 0.0,
    parameter real INL_MAX = 0.5,  // LSB
    parameter real DNL_MAX = 0.5   // LSB
)(
    input  logic clk,
    input  logic start,
    input  wreal vin,           // 아날로그 입력 (wreal)
    output logic [BITS-1:0] dout,
    output logic valid
);
    
    real lsb;
    real vin_corrected;
    int code;
    
    // Conversion delay (cycles)
    parameter int CONV_CYCLES = 10;
    int cycle_count;
    
    initial begin
        lsb = VREF / (2**BITS);
    end
    
    typedef enum {IDLE, CONVERTING, DONE} state_t;
    state_t state;
    
    always_ff @(posedge clk) begin
        case (state)
            IDLE: begin
                valid <= 0;
                if (start) begin
                    vin_corrected = vin - OFFSET;
                    cycle_count <= 0;
                    state <= CONVERTING;
                end
            end
            
            CONVERTING: begin
                cycle_count <= cycle_count + 1;
                if (cycle_count >= CONV_CYCLES - 1) begin
                    // 이상적 변환 + 비선형성
                    code = int'(vin_corrected / lsb);
                    code = code + $urandom_range(0, int'(INL_MAX));  // INL 모델링
                    
                    // Saturation
                    if (code < 0) code = 0;
                    if (code > 2**BITS - 1) code = 2**BITS - 1;
                    
                    dout <= code[BITS-1:0];
                    state <= DONE;
                end
            end
            
            DONE: begin
                valid <= 1;
                state <= IDLE;
            end
        endcase
    end
endmodule
```

## Wreal DAC 모델

```verilog
// dac_wreal.sv - 8-bit DAC 행동 모델
module dac_wreal #(
    parameter int BITS = 8,
    parameter real VREF = 1.8,
    parameter real OFFSET = 0.0,
    parameter real SETTLING_TIME = 1e-9  // 1ns
)(
    input  logic clk,
    input  logic [BITS-1:0] din,
    output wreal vout
);
    
    real lsb;
    real target_v;
    real current_v;
    
    initial begin
        lsb = VREF / (2**BITS);
        current_v = 0.0;
    end
    
    // 이상적 DAC 출력 계산
    always @(din) begin
        target_v = din * lsb + OFFSET;
    end
    
    // Settling 모델링 (1차 지수 응답)
    always begin
        #(SETTLING_TIME / 10);
        current_v = current_v + (target_v - current_v) * 0.3;
    end
    
    assign vout = current_v;
    
endmodule
```

## Wreal PLL 모델

```verilog
// pll_wreal.sv - PLL 행동 모델
module pll_wreal #(
    parameter real FREF = 100e6,        // Reference frequency
    parameter int  MULT = 10,           // Multiplier
    parameter real LOCK_TIME = 10e-6,   // Lock time
    parameter real JITTER_RMS = 1e-12   // Jitter (RMS)
)(
    input  logic ref_clk,
    input  logic enable,
    output logic out_clk,
    output logic locked
);
    
    real fout;
    real period;
    real jitter;
    time lock_counter;
    
    initial begin
        fout = FREF * MULT;
        period = 1.0 / fout;
        out_clk = 0;
        locked = 0;
    end
    
    // Lock 검출
    always @(posedge ref_clk) begin
        if (enable) begin
            if (lock_counter < LOCK_TIME * FREF)
                lock_counter <= lock_counter + 1;
            else
                locked <= 1;
        end else begin
            lock_counter <= 0;
            locked <= 0;
        end
    end
    
    // 출력 클럭 생성 (with jitter)
    always begin
        if (enable && locked) begin
            jitter = $dist_normal($urandom, 0, JITTER_RMS * 1e12) * 1ps;
            #((period/2) * 1s + jitter);
            out_clk = ~out_clk;
        end else begin
            #(period/2 * 1s);
            out_clk = 0;
        end
    end
    
endmodule
```

## Wreal LDO 모델

```verilog
// ldo_wreal.sv - LDO 행동 모델
module ldo_wreal #(
    parameter real VOUT_NOM = 1.8,
    parameter real VIN_MIN = 2.0,
    parameter real DROPOUT = 0.2,
    parameter real LOAD_REG = 0.01,     // 1% load regulation
    parameter real LINE_REG = 0.01,     // 1% line regulation
    parameter real PSRR_DB = 60         // dB at DC
)(
    input  wreal vin,
    input  wreal iload,      // 부하 전류
    output wreal vout
);
    
    real vout_ideal;
    real vout_actual;
    real psrr_linear;
    real vin_ripple;
    
    initial begin
        psrr_linear = 10 ** (-PSRR_DB / 20);
    end
    
    always @(vin or iload) begin
        // Dropout 체크
        if (vin < VOUT_NOM + DROPOUT) begin
            vout_ideal = vin - DROPOUT;
        end else begin
            vout_ideal = VOUT_NOM;
        end
        
        // Load regulation
        vout_actual = vout_ideal * (1.0 - LOAD_REG * iload);
        
        // Line regulation
        vout_actual = vout_actual * (1.0 + LINE_REG * (vin - VIN_MIN));
        
        // PSRR (입력 리플 감쇠)
        vin_ripple = vin - 3.3;  // AC 성분 추정
        vout_actual = vout_actual + vin_ripple * psrr_linear;
    end
    
    assign vout = vout_actual;
    
endmodule
```

## UVM에서 Wreal 사용

### Wreal Interface

```systemverilog
// analog_stim_if.sv
interface analog_stim_if;
    wreal voltage;
    wreal current;
    real  frequency;
    
    // Stimulus generation tasks
    task set_dc(real v);
        voltage = v;
    endtask
    
    task set_sine(real amp, real freq, real offset);
        real t;
        frequency = freq;
        forever begin
            t = $realtime * 1e-9;  // ns to s
            voltage = offset + amp * $sin(2.0 * 3.14159 * freq * t);
            #1ns;
        end
    endtask
    
    task set_ramp(real v_start, real v_end, real duration);
        real step;
        int num_steps;
        num_steps = int'(duration / 1e-9);  // 1ns step
        step = (v_end - v_start) / num_steps;
        voltage = v_start;
        repeat (num_steps) begin
            #1ns;
            voltage = voltage + step;
        end
    endtask
endinterface
```

### Analog Stimulus Agent

```systemverilog
// analog_stim_driver.sv
class analog_stim_driver extends uvm_driver #(analog_transaction);
    `uvm_component_utils(analog_stim_driver)
    
    virtual analog_stim_if vif;
    
    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            drive_stimulus(req);
            seq_item_port.item_done();
        end
    endtask
    
    task drive_stimulus(analog_transaction tr);
        case (tr.stim_type)
            DC:   vif.set_dc(tr.dc_value);
            SINE: fork vif.set_sine(tr.amplitude, tr.freq, tr.offset); join_none
            RAMP: vif.set_ramp(tr.start_v, tr.end_v, tr.duration);
        endcase
    endtask
endclass
```

## Wreal vs Electrical 선택 기준

| 기준 | Wreal | Electrical (Spectre) |
|------|-------|---------------------|
| 시뮬레이션 속도 | 빠름 (10-100x) | 느림 |
| 정확도 | 행동 수준 | 트랜지스터 수준 |
| 노이즈 모델링 | 제한적 | 정확 |
| 비선형성 | 수동 모델링 | 자동 |
| 용도 | 시스템 검증, 빠른 회귀 | 상세 특성 검증 |
