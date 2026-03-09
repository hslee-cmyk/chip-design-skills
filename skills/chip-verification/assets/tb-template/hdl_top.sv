`timescale 1ns/1ps

//============================================
// HDL Top for AMS Verification
// 아날로그 모델 교체 가능한 구조
//============================================
module hdl_top;
    
    //------------------------------------------
    // Parameters
    //------------------------------------------
    parameter CLK_PERIOD = 10;  // 100MHz
    parameter RST_CYCLES = 10;
    
    //------------------------------------------
    // Clock & Reset
    //------------------------------------------
    logic clk;
    logic rst_n;
    
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    initial begin
        rst_n = 0;
        repeat (RST_CYCLES) @(posedge clk);
        rst_n = 1;
    end
    
    //------------------------------------------
    // Interface (디지털 신호만!)
    //------------------------------------------
    chip_if dut_if(clk, rst_n);
    
    //------------------------------------------
    // Chip Top (Digital + Analog)
    // analog_top이 내부에 인스턴스됨
    //------------------------------------------
    chip_top u_chip (
        .clk        (clk),
        .rst_n      (rst_n),
        // Digital interface
        .din        (dut_if.din),
        .dout       (dut_if.dout),
        .valid_in   (dut_if.valid_in),
        .valid_out  (dut_if.valid_out),
        .ready      (dut_if.ready),
        // ADC control
        .adc_start  (dut_if.adc_start),
        .adc_ch_sel (dut_if.adc_ch_sel),
        .adc_dout   (dut_if.adc_dout),
        .adc_valid  (dut_if.adc_valid),
        // DAC control
        .dac_din    (dut_if.dac_din),
        .dac_load   (dut_if.dac_load),
        // PLL status
        .pll_en     (dut_if.pll_en),
        .pll_locked (dut_if.pll_locked)
    );
    
    //------------------------------------------
    // Analog Stimulus (테스트벤치 레벨)
    // Behavioral/Wreal 모델에서 사용
    //------------------------------------------
    `ifndef AMS_SPECTRE
    // Spectre가 아닐 때만 TB에서 아날로그 자극 제공
    real ana_stim_voltage;
    
    initial begin
        ana_stim_voltage = 0.0;
    end
    
    // chip 내부 analog_top에 force (모델에 따라)
    // Behavioral 모델은 internal real 변수를 가짐
    `ifdef AMS_BEHAV
    // Force to behavioral model's internal variable
    // (모델 구현에 따라 조정 필요)
    `endif
    `endif
    
    //------------------------------------------
    // Waveform Dump
    //------------------------------------------
    initial begin
        if ($test$plusargs("DUMP_WAVES")) begin
            `ifdef AMS_SPECTRE
            // Spectre: SHM 사용
            $shm_open("waves.shm");
            $shm_probe(hdl_top, "AS");  // Analog + Digital
            `else
            // Digital only: VCD
            $dumpfile("waves.vcd");
            $dumpvars(0, hdl_top);
            `endif
        end
    end
    
endmodule
