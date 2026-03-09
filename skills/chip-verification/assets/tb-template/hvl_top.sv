`timescale 1ns/1ps

//============================================
// HVL Top for AMS Verification
// 일반 UVM 환경 (디지털 인터페이스만 사용)
//============================================
module hvl_top;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    
    import chip_test_pkg::*;
    
    //------------------------------------------
    // Virtual Interface 전달
    //------------------------------------------
    initial begin
        // 디지털 인터페이스만 전달
        // 아날로그는 DUT 내부에서 처리됨
        uvm_config_db#(virtual chip_if.DRV)::set(
            null, "uvm_test_top.env.agent.drv", "vif", hdl_top.dut_if);
        uvm_config_db#(virtual chip_if.MON)::set(
            null, "uvm_test_top.env.agent.mon", "vif", hdl_top.dut_if);
        
        // 아날로그 모델 타입 전달 (테스트에서 참조 가능)
        `ifdef AMS_SPECTRE
        uvm_config_db#(string)::set(null, "*", "analog_model", "SPECTRE");
        `elsif AMS_WREAL
        uvm_config_db#(string)::set(null, "*", "analog_model", "WREAL");
        `else
        uvm_config_db#(string)::set(null, "*", "analog_model", "BEHAV");
        `endif
    end
    
    //------------------------------------------
    // UVM Test 실행
    //------------------------------------------
    initial begin
        run_test();
    end
    
    //------------------------------------------
    // 시뮬레이션 정보
    //------------------------------------------
    initial begin
        `uvm_info("HVL_TOP", "=== AMS Verification Environment ===", UVM_LOW)
        `ifdef AMS_SPECTRE
        `uvm_info("HVL_TOP", "Analog Model: SPECTRE (정밀)", UVM_LOW)
        `elsif AMS_WREAL
        `uvm_info("HVL_TOP", "Analog Model: WREAL (중간)", UVM_LOW)
        `else
        `uvm_info("HVL_TOP", "Analog Model: BEHAVIORAL (빠름)", UVM_LOW)
        `endif
    end
    
    //------------------------------------------
    // Timeout
    //------------------------------------------
    initial begin
        `ifdef AMS_SPECTRE
        #100ms;  // Spectre는 시간이 오래 걸림
        `else
        #10ms;
        `endif
        `uvm_fatal("HVL_TOP", "Simulation timeout!")
    end
    
endmodule
