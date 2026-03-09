# Analog Model Abstraction Levels

## 개요: 왜 모델 교체가 필요한가?

```
┌─────────────────────────────────────────────────────────────┐
│                     시뮬레이션 시간                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Behavioral (1분) ████                                      │
│  Wreal (10분)     ████████████████████████                  │
│  Spectre (1000분) ████████████████████████████████████████  │
│                                                             │
│  → 일일 회귀 1000개 테스트:                                  │
│    Behavioral: ~17시간 (하룻밤)                              │
│    Spectre: ~700일 (불가능)                                  │
└─────────────────────────────────────────────────────────────┘
```

## 동일한 포트, 다른 구현

### 공통 인터페이스 정의

```verilog
// analog_top_port.vh - 공통 포트 정의
// 모든 analog_top_xxx 모듈이 이 포트를 따름

// module analog_top (
    input  wire        clk,
    input  wire        rst_n,
    // ADC
    input  wire        adc_start,
    input  wire [1:0]  adc_ch_sel,
    output wire [11:0] adc_dout,
    output wire        adc_valid,
    // DAC
    input  wire [11:0] dac_din,
    input  wire        dac_load,
    // PLL
    input  wire        pll_en,
    output wire        pll_clk_out,
    output wire        pll_locked,
    // 외부 아날로그 핀 (테스트벤치에서 자극)
    input  wire        ana_in,      // 실제는 electrical/wreal
    output wire        ana_out
// );
```

## Level 1: Behavioral Model (가장 빠름)

**용도:** 기능 검증, 일일 회귀, CI/CD

```verilog
// analog_top_behav.sv
module analog_top_behav (
    `include "analog_top_port.vh"
);
    
    //------------------------------------------
    // ADC Behavioral Model
    //------------------------------------------
    // 타이밍: 즉시 (0 cycle latency로 단순화)
    // 정확도: 이상적 (노이즈, 비선형성 없음)
    
    reg [11:0] adc_result;
    reg        adc_done;
    
    // 간단한 변환: 0.0~1.8V → 0~4095
    // ana_in이 실제로는 0/1 디지털이지만
    // 테스트벤치에서 real 값으로 force 가능
    real ana_in_voltage;
    
    always @(posedge clk) begin
        if (adc_start) begin
            // 이상적 ADC: 즉시 변환
            adc_result <= (ana_in_voltage / 1.8) * 4095;
            adc_done <= 1;
        end else begin
            adc_done <= 0;
        end
    end
    
    assign adc_dout = adc_result;
    assign adc_valid = adc_done;
    
    //------------------------------------------
    // DAC Behavioral Model
    //------------------------------------------
    real dac_voltage;
    
    always @(posedge clk) begin
        if (dac_load) begin
            dac_voltage = (dac_din / 4095.0) * 1.8;
        end
    end
    
    // ana_out은 테스트벤치에서 이 값을 읽음
    assign ana_out = (dac_voltage > 0.9) ? 1'b1 : 1'b0;
    
    //------------------------------------------
    // PLL Behavioral Model
    //------------------------------------------
    // 즉시 lock, 이상적 클럭
    reg pll_clk_reg;
    
    always @(posedge clk) begin
        if (pll_en)
            pll_clk_reg <= ~pll_clk_reg;  // 2배 주파수
    end
    
    assign pll_clk_out = pll_clk_reg;
    assign pll_locked = pll_en;  // 즉시 lock
    
endmodule
```

### Behavioral 모델 특징

| 항목 | 구현 |
|------|------|
| ADC 변환 시간 | 0~1 cycle |
| DAC settling | 즉시 |
| PLL lock 시간 | 즉시 |
| 노이즈 | 없음 |
| 비선형성 | 없음 |
| 전원 변동 영향 | 없음 |

## Level 2: Wreal Model (중간)

**용도:** 타이밍 검증, 주간 회귀

```verilog
// analog_top_wreal.sv
module analog_top_wreal (
    `include "analog_top_port.vh"
);
    
    //------------------------------------------
    // ADC Wreal Model
    //------------------------------------------
    // 타이밍: 실제 변환 시간 모델링
    // 정확도: 기본적인 비선형성 포함
    
    parameter real ADC_VREF = 1.8;
    parameter int  ADC_CONV_CYCLES = 12;  // 실제 변환 시간
    parameter real ADC_INL = 1.0;         // LSB
    parameter real ADC_OFFSET = 0.001;    // V
    
    wreal ana_in_w;  // wreal 타입 사용
    assign ana_in_w = ana_in ? 1.8 : 0.0;  // 또는 외부에서 drive
    
    reg [11:0] adc_result;
    reg        adc_done;
    int        conv_cnt;
    
    typedef enum {ADC_IDLE, ADC_CONV} adc_state_t;
    adc_state_t adc_state;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            adc_state <= ADC_IDLE;
            adc_done <= 0;
        end else begin
            case (adc_state)
                ADC_IDLE: begin
                    adc_done <= 0;
                    if (adc_start) begin
                        conv_cnt <= 0;
                        adc_state <= ADC_CONV;
                    end
                end
                
                ADC_CONV: begin
                    conv_cnt <= conv_cnt + 1;
                    if (conv_cnt >= ADC_CONV_CYCLES - 1) begin
                        // 비선형성 포함 변환
                        real vin_corrected;
                        int code;
                        vin_corrected = ana_in_w - ADC_OFFSET;
                        code = int'((vin_corrected / ADC_VREF) * 4096);
                        // INL 에러 추가
                        code = code + $urandom_range(-int'(ADC_INL), int'(ADC_INL));
                        // Saturation
                        if (code < 0) code = 0;
                        if (code > 4095) code = 4095;
                        adc_result <= code;
                        adc_done <= 1;
                        adc_state <= ADC_IDLE;
                    end
                end
            endcase
        end
    end
    
    assign adc_dout = adc_result;
    assign adc_valid = adc_done;
    
    //------------------------------------------
    // DAC Wreal Model
    //------------------------------------------
    parameter real DAC_SETTLING_NS = 100;  // settling time
    parameter real DAC_GLITCH_NS = 5;      // glitch duration
    
    wreal dac_out_w;
    real dac_target;
    real dac_current;
    
    always @(posedge clk) begin
        if (dac_load) begin
            dac_target = (dac_din / 4095.0) * 1.8;
        end
    end
    
    // Settling 동작 모델링
    always begin
        #1ns;
        // 1차 지수 응답
        dac_current = dac_current + (dac_target - dac_current) * 0.05;
    end
    
    assign dac_out_w = dac_current;
    assign ana_out = (dac_out_w > 0.9) ? 1'b1 : 1'b0;
    
    //------------------------------------------
    // PLL Wreal Model
    //------------------------------------------
    parameter real PLL_LOCK_CYCLES = 100;  // lock 시간
    parameter real PLL_JITTER_PS = 10;      // jitter RMS
    
    reg pll_clk_reg;
    reg pll_locked_reg;
    int lock_cnt;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            lock_cnt <= 0;
            pll_locked_reg <= 0;
        end else if (pll_en) begin
            if (lock_cnt < PLL_LOCK_CYCLES)
                lock_cnt <= lock_cnt + 1;
            else
                pll_locked_reg <= 1;
        end else begin
            lock_cnt <= 0;
            pll_locked_reg <= 0;
        end
    end
    
    // Jitter 포함 클럭 생성
    real jitter;
    always begin
        if (pll_locked_reg) begin
            jitter = $dist_normal($urandom, 0, PLL_JITTER_PS) * 1ps;
            #(2.5ns + jitter);  // 200MHz 예시
            pll_clk_reg = ~pll_clk_reg;
        end else begin
            #5ns;
            pll_clk_reg = 0;
        end
    end
    
    assign pll_clk_out = pll_clk_reg;
    assign pll_locked = pll_locked_reg;
    
endmodule
```

## Level 3: Spectre Model (가장 정밀)

**용도:** 테잎아웃 전 최종 검증, 아날로그 특성 검증

```verilog
// analog_top_spectre.vams
`include "disciplines.vams"

module analog_top_spectre (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        adc_start,
    input  wire [1:0]  adc_ch_sel,
    output wire [11:0] adc_dout,
    output wire        adc_valid,
    input  wire [11:0] dac_din,
    input  wire        dac_load,
    input  wire        pll_en,
    output wire        pll_clk_out,
    output wire        pll_locked,
    // Spectre 연결용 electrical
    input  electrical  ana_in_e,
    output electrical  ana_out_e
);
    
    // 내부 electrical 노드
    electrical vdd, vss, vref;
    electrical adc_vin, dac_vout;
    
    //------------------------------------------
    // Power supplies (Spectre)
    //------------------------------------------
    vsource #(.type("dc"), .dc(1.8)) V_VDD (vdd, vss);
    vsource #(.type("dc"), .dc(0.9)) V_VREF (vref, vss);
    
    //------------------------------------------
    // ADC (Spectre subcircuit)
    //------------------------------------------
    adc_12bit_spectre u_adc (
        .VDD(vdd),
        .VSS(vss),
        .VREF(vref),
        .VIN(ana_in_e),
        .CLK(clk),          // connect module 자동 삽입
        .START(adc_start),
        .DOUT(adc_dout),
        .VALID(adc_valid)
    );
    
    //------------------------------------------
    // DAC (Spectre subcircuit)
    //------------------------------------------
    dac_12bit_spectre u_dac (
        .VDD(vdd),
        .VSS(vss),
        .VREF(vref),
        .DIN(dac_din),
        .LOAD(dac_load),
        .CLK(clk),
        .VOUT(ana_out_e)
    );
    
    //------------------------------------------
    // PLL (Spectre subcircuit)
    //------------------------------------------
    pll_spectre u_pll (
        .VDD(vdd),
        .VSS(vss),
        .REFCLK(clk),
        .EN(pll_en),
        .OUTCLK(pll_clk_out),
        .LOCKED(pll_locked)
    );
    
endmodule
```

## 모델 선택 Makefile

```makefile
# 기본: Behavioral (빠른 시뮬레이션)
ANALOG_MODEL ?= BEHAV

# 컴파일 플래그
ifeq ($(ANALOG_MODEL), SPECTRE)
    AMS_FLAGS := +define+AMS_SPECTRE -ams
    SIM_TOOL := xmsim -ams
else ifeq ($(ANALOG_MODEL), WREAL)
    AMS_FLAGS := +define+AMS_WREAL
    SIM_TOOL := xmsim
else
    AMS_FLAGS := +define+AMS_BEHAV
    SIM_TOOL := xmsim
endif

# 타겟
sim_behav:
	$(MAKE) sim ANALOG_MODEL=BEHAV

sim_wreal:
	$(MAKE) sim ANALOG_MODEL=WREAL

sim_spectre:
	$(MAKE) sim ANALOG_MODEL=SPECTRE

# 회귀 전략
regress_daily: sim_behav      # 매일: Behavioral
regress_weekly: sim_wreal     # 주간: Wreal
regress_tapeout: sim_spectre  # 테잎아웃: Spectre (선별 테스트)
```

## 모델 정확도 비교

| 특성 | Behavioral | Wreal | Spectre |
|------|------------|-------|---------|
| 변환 정확도 | 이상적 | ±1 LSB | 실제 |
| 타이밍 | 없음/1cycle | 근사 | 정확 |
| 노이즈 | 없음 | 모델링 가능 | 정확 |
| 전원 변동 | 없음 | 단순 | 정확 |
| 온도 영향 | 없음 | 파라미터 | 정확 |
| 시뮬 속도 | 1x | 10-100x 느림 | 1000x 느림 |
