//============================================
// Chip Interface
// 디지털 신호만 포함 (UVM에서 사용)
//============================================
interface chip_if (input logic clk, input logic rst_n);
    
    //------------------------------------------
    // Digital Data Interface
    //------------------------------------------
    logic [11:0] din;
    logic [11:0] dout;
    logic        valid_in;
    logic        valid_out;
    logic        ready;
    
    //------------------------------------------
    // ADC Control Interface
    //------------------------------------------
    logic        adc_start;
    logic [1:0]  adc_ch_sel;
    logic [11:0] adc_dout;
    logic        adc_valid;
    
    //------------------------------------------
    // DAC Control Interface
    //------------------------------------------
    logic [11:0] dac_din;
    logic        dac_load;
    
    //------------------------------------------
    // PLL Control Interface
    //------------------------------------------
    logic        pll_en;
    logic        pll_locked;
    
    //------------------------------------------
    // Clocking Blocks
    //------------------------------------------
    clocking drv_cb @(posedge clk);
        default input #1step output #1;
        output din, valid_in;
        output adc_start, adc_ch_sel;
        output dac_din, dac_load;
        output pll_en;
        input  dout, valid_out, ready;
        input  adc_dout, adc_valid;
        input  pll_locked;
    endclocking
    
    clocking mon_cb @(posedge clk);
        default input #1step;
        input din, dout, valid_in, valid_out, ready;
        input adc_start, adc_ch_sel, adc_dout, adc_valid;
        input dac_din, dac_load;
        input pll_en, pll_locked;
    endclocking
    
    //------------------------------------------
    // Modports
    //------------------------------------------
    modport DRV (clocking drv_cb, input rst_n);
    modport MON (clocking mon_cb, input rst_n);
    
    //------------------------------------------
    // Assertions (Protocol checks)
    //------------------------------------------
    // ADC: valid는 start 후 N 사이클 내에 발생해야 함
    property p_adc_response;
        @(posedge clk) disable iff (!rst_n)
        adc_start |-> ##[1:100] adc_valid;
    endproperty
    assert property (p_adc_response) 
        else $error("ADC response timeout");
    
    // PLL: lock은 enable 후 N 사이클 내에 발생해야 함
    property p_pll_lock;
        @(posedge clk) disable iff (!rst_n)
        $rose(pll_en) |-> ##[1:1000] pll_locked;
    endproperty
    assert property (p_pll_lock)
        else $error("PLL lock timeout");
    
endinterface
