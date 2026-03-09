# Spectre Integration Guide

## Spectre 모듈 인스턴스화

### 기본 구조

```verilog
// ams_top.vams
`include "disciplines.vams"

module ams_top;
    
    // Electrical 노드 선언
    electrical vdd, vss, vref;
    electrical [7:0] adc_in;
    electrical clk_ana;
    
    // Digital 신호
    logic clk, rst_n;
    logic [7:0] digital_out;
    
    //------------------------------------------
    // Power Supply (Spectre)
    //------------------------------------------
    vsource #(.type("dc"), .dc(1.8)) V_VDD (vdd, vss);
    vsource #(.type("dc"), .dc(0.9)) V_VREF (vref, vss);
    
    //------------------------------------------
    // Spectre Analog Block
    //------------------------------------------
    adc_8bit_spectre u_adc (
        .VDD    (vdd),
        .VSS    (vss),
        .VREF   (vref),
        .VIN    (adc_in),
        .CLK    (clk_ana),      // electrical clock
        .DOUT   (digital_out)   // connect module 자동 삽입
    );
    
    //------------------------------------------
    // Digital Block
    //------------------------------------------
    my_digital_dut u_digital (
        .clk    (clk),
        .rst_n  (rst_n),
        .din    (digital_out)
    );
    
endmodule
```

### Spectre 넷리스트 연결

```
// spectre_blocks.scs

// ADC subcircuit
subckt adc_8bit_spectre (VDD VSS VREF VIN<7:0> CLK DOUT<7:0>)
    // Spectre netlist here
    ...
ends adc_8bit_spectre

// DAC subcircuit
subckt dac_8bit_spectre (VDD VSS VREF DIN<7:0> VOUT)
    ...
ends dac_8bit_spectre
```

## Discipline 선언

```verilog
// disciplines.vams (표준)
`include "constants.vams"

discipline electrical;
    potential Voltage;
    flow Current;
endiscipline

discipline logic;
    domain discrete;
endiscipline

// wreal discipline
discipline wreal;
    domain discrete;
    potential Voltage;
endiscipline
```

## 복잡한 Mixed-Signal 구조

### ADC + Digital Processing + DAC

```verilog
// mixed_signal_top.vams
`include "disciplines.vams"

module mixed_signal_top;
    
    // Power
    electrical vdd_ana, vdd_dig, vss;
    
    // Analog I/O
    electrical ana_in;
    electrical ana_out;
    
    // Internal nodes
    electrical adc_out_ana;
    logic [11:0] adc_dout;
    logic [11:0] dac_din;
    logic clk_100m, clk_1g;
    
    //------------------------------------------
    // Analog Frontend (Spectre)
    //------------------------------------------
    // Anti-aliasing filter
    lpf_2nd_order #(.fc(10e6)) u_aaf (
        .VIN(ana_in),
        .VOUT(adc_in_filtered),
        .VDD(vdd_ana),
        .VSS(vss)
    );
    
    // 12-bit ADC
    adc_12bit u_adc (
        .VDD    (vdd_ana),
        .VSS    (vss),
        .VIN    (adc_in_filtered),
        .CLK    (clk_100m),
        .DOUT   (adc_dout)
    );
    
    //------------------------------------------
    // Digital Processing (Verilog)
    //------------------------------------------
    digital_filter u_dsp (
        .clk    (clk_100m),
        .rst_n  (rst_n),
        .din    (adc_dout),
        .dout   (dac_din)
    );
    
    //------------------------------------------
    // Analog Backend (Spectre)
    //------------------------------------------
    // 12-bit DAC
    dac_12bit u_dac (
        .VDD    (vdd_ana),
        .VSS    (vss),
        .DIN    (dac_din),
        .CLK    (clk_100m),
        .VOUT   (dac_out_raw)
    );
    
    // Reconstruction filter
    lpf_2nd_order #(.fc(10e6)) u_recon (
        .VIN(dac_out_raw),
        .VOUT(ana_out),
        .VDD(vdd_ana),
        .VSS(vss)
    );
    
    //------------------------------------------
    // PLL (Spectre or Wreal)
    //------------------------------------------
    pll_spectre u_pll (
        .REFCLK (clk_ext),
        .VDD    (vdd_ana),
        .VSS    (vss),
        .OUTCLK (clk_1g),
        .LOCKED (pll_locked)
    );
    
endmodule
```

## Spectre 제어 파일

### AMS Control File (.scs)

```
// ams_control.scs

simulator lang=spectre

// Global 옵션
global 0 vdd!

// 시뮬레이션 설정
amssettings {
    // 아날로그 solver 정확도
    reltol=1e-4
    vabstol=1e-6
    iabstol=1e-12
    
    // 혼합 모드 설정
    amscoupling=on
    vlogammsel=automatic
}

// Transient 분석
tran tran stop=100u errpreset=conservative

// 옵션
options {
    reltol=1e-3
    vabstol=1e-6
    iabstol=1e-12
    temp=27
    scalem=1
}

// 라이브러리 포함
include "/path/to/spectre_models.scs" section=tt
include "/path/to/analog_blocks.scs"
```

### Xcelium-AMS 명령줄

```bash
# Compile
xmvlog -ams -sv tb_files.sv
xmvlog -ams ams_top.vams
xmelab -ams -timescale 1ns/1ps \
    -discipline_resolution \
    -analogcontrol ams_control.scs \
    tb_top

# Run
xmsim tb_top \
    +UVM_TESTNAME=my_test \
    -input xmsim_cmds.tcl
```

### VCS-AMS 명령줄

```bash
# Compile and elaborate
vcs -full64 -sverilog -ams \
    +vcs+lic+wait \
    -ams_discipline electrical \
    -ams_controlfile ams_control.scs \
    tb_files.sv ams_top.vams \
    -top tb_top

# Run
./simv +UVM_TESTNAME=my_test
```

## Spectre 파라미터 전달

```verilog
// 파라미터화된 Spectre 인스턴스
module ams_top;
    parameter real VDD_VAL = 1.8;
    parameter real TEMP = 27;
    
    // Spectre 인스턴스에 파라미터 전달
    adc_8bit #(
        .vdd_nom(VDD_VAL),
        .temp(TEMP)
    ) u_adc (
        .VDD(vdd),
        // ...
    );
endmodule
```

## Mixed-Signal 디버깅

### 아날로그 파형 저장

```verilog
// ams_top.vams
initial begin
    // Spectre 노드 probe
    $shm_open("waves.shm");
    $shm_probe(vdd, vss, ana_in, ana_out, "AS");  // Analog + Digital
end
```

### Xcelium-AMS 파형

```tcl
# xmsim_cmds.tcl
database -open waves -shm -into waves.shm
probe -create ams_top -depth all -all -shm -waveform

run
exit
```

## 주의사항

### 타이밍 동기화
```verilog
// 디지털 클럭을 아날로그로 전달 시 주의
// Connect module이 지연을 추가할 수 있음

// 방법 1: 명시적 지연 보상
logic clk_delayed;
assign #(CONNECT_DELAY) clk_delayed = clk;

// 방법 2: 아날로그 클럭 생성
vsource #(.type("pulse"), .val0(0), .val1(1.8), 
          .period(10n), .rise(100p), .fall(100p)) 
    V_CLK (clk_ana, vss);
```

### 수렴 문제
```
// Spectre 수렴 실패 시:
// 1. reltol 완화: reltol=1e-3
// 2. gmin stepping: gmin=1e-12 → 1e-15
// 3. 초기 조건 설정: ic vnode=0.9
// 4. 시간 스텝 제한: maxstep=1n
```
