//============================================
// Chip Top - Digital + Analog Integration
// 아날로그 모델 교체 가능
//============================================
module chip_top (
    input  wire        clk,
    input  wire        rst_n,
    // Digital data interface
    input  wire [11:0] din,
    output wire [11:0] dout,
    input  wire        valid_in,
    output wire        valid_out,
    output wire        ready,
    // ADC interface
    input  wire        adc_start,
    input  wire [1:0]  adc_ch_sel,
    output wire [11:0] adc_dout,
    output wire        adc_valid,
    // DAC interface
    input  wire [11:0] dac_din,
    input  wire        dac_load,
    // PLL interface
    input  wire        pll_en,
    output wire        pll_locked
);
    
    //------------------------------------------
    // Internal signals
    //------------------------------------------
    wire        pll_clk;
    wire [11:0] dsp_to_dac;
    wire [11:0] adc_to_dsp;
    wire        adc_data_valid;
    
    //------------------------------------------
    // Digital Core
    //------------------------------------------
    digital_core u_digital (
        .clk        (pll_clk),      // PLL 출력 사용
        .rst_n      (rst_n & pll_locked),
        .din        (din),
        .dout       (dout),
        .valid_in   (valid_in),
        .valid_out  (valid_out),
        .ready      (ready),
        // ADC data input
        .adc_data   (adc_to_dsp),
        .adc_valid  (adc_data_valid),
        // DAC data output
        .dac_data   (dsp_to_dac)
    );
    
    //------------------------------------------
    // Analog Top - 모델 선택
    //------------------------------------------
    `ifdef AMS_SPECTRE
        //--------------------------------------
        // Spectre Model (정밀, 느림)
        //--------------------------------------
        analog_top_spectre u_analog (
            .clk        (clk),
            .rst_n      (rst_n),
            .adc_start  (adc_start),
            .adc_ch_sel (adc_ch_sel),
            .adc_dout   (adc_to_dsp),
            .adc_valid  (adc_data_valid),
            .dac_din    (dsp_to_dac),
            .dac_load   (dac_load),
            .pll_en     (pll_en),
            .pll_clk_out(pll_clk),
            .pll_locked (pll_locked)
            // Spectre용 electrical 포트는 
            // 외부에서 직접 연결
        );
        
    `elsif AMS_WREAL
        //--------------------------------------
        // Wreal Model (중간 정확도, 중간 속도)
        //--------------------------------------
        analog_top_wreal u_analog (
            .clk        (clk),
            .rst_n      (rst_n),
            .adc_start  (adc_start),
            .adc_ch_sel (adc_ch_sel),
            .adc_dout   (adc_to_dsp),
            .adc_valid  (adc_data_valid),
            .dac_din    (dsp_to_dac),
            .dac_load   (dac_load),
            .pll_en     (pll_en),
            .pll_clk_out(pll_clk),
            .pll_locked (pll_locked)
        );
        
    `else  // AMS_BEHAV (기본)
        //--------------------------------------
        // Behavioral Model (빠름, 기능 검증용)
        //--------------------------------------
        analog_top_behav u_analog (
            .clk        (clk),
            .rst_n      (rst_n),
            .adc_start  (adc_start),
            .adc_ch_sel (adc_ch_sel),
            .adc_dout   (adc_to_dsp),
            .adc_valid  (adc_data_valid),
            .dac_din    (dsp_to_dac),
            .dac_load   (dac_load),
            .pll_en     (pll_en),
            .pll_clk_out(pll_clk),
            .pll_locked (pll_locked)
        );
        
    `endif
    
    // ADC 출력 연결
    assign adc_dout = adc_to_dsp;
    assign adc_valid = adc_data_valid;
    
endmodule
