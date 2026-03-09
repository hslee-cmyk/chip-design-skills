`ifndef __MY_SCOREBOARD_SV__
`define __MY_SCOREBOARD_SV__

// Analysis port implementations
`uvm_analysis_imp_decl(_exp)
`uvm_analysis_imp_decl(_act)

class my_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(my_scoreboard)
    
    //------------------------------------------
    // TLM Ports
    //------------------------------------------
    uvm_analysis_imp_exp #(out_transaction, my_scoreboard) exp_ap;  // Expected (from ref model)
    uvm_analysis_imp_act #(out_transaction, my_scoreboard) act_ap;  // Actual (from DUT)
    
    //------------------------------------------
    // Queues for comparison
    //------------------------------------------
    out_transaction exp_queue[$];
    out_transaction act_queue[$];
    
    //------------------------------------------
    // Statistics
    //------------------------------------------
    int match_count;
    int mismatch_count;
    int total_compared;
    
    // 옵션: 순서 검증
    bit check_order = 1;
    int max_queue_depth = 100;
    
    //------------------------------------------
    // Constructor
    //------------------------------------------
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction
    
    //------------------------------------------
    // Build Phase
    //------------------------------------------
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        exp_ap = new("exp_ap", this);
        act_ap = new("act_ap", this);
    endfunction
    
    //------------------------------------------
    // Expected 수신 (Reference Model에서)
    //------------------------------------------
    function void write_exp(out_transaction tr);
        out_transaction tr_copy;
        $cast(tr_copy, tr.clone());
        
        `uvm_info("SCBD", $sformatf("[EXP] %s", tr.convert2string()), UVM_HIGH)
        
        // 대기 중인 actual이 있으면 바로 비교
        if (act_queue.size() > 0) begin
            compare(exp_queue.pop_front(), act_queue.pop_front());
        end else begin
            exp_queue.push_back(tr_copy);
            check_queue_overflow();
        end
    endfunction
    
    //------------------------------------------
    // Actual 수신 (DUT Monitor에서)
    //------------------------------------------
    function void write_act(out_transaction tr);
        out_transaction tr_copy;
        $cast(tr_copy, tr.clone());
        
        `uvm_info("SCBD", $sformatf("[ACT] %s", tr.convert2string()), UVM_HIGH)
        
        // 대기 중인 expected가 있으면 바로 비교
        if (exp_queue.size() > 0) begin
            compare(exp_queue.pop_front(), tr_copy);
        end else begin
            act_queue.push_back(tr_copy);
            check_queue_overflow();
        end
    endfunction
    
    //------------------------------------------
    // 비교
    //------------------------------------------
    function void compare(out_transaction exp, out_transaction act);
        total_compared++;
        
        if (exp.compare(act)) begin
            match_count++;
            `uvm_info("SCBD", $sformatf("[MATCH #%0d] %s", 
                      total_compared, act.convert2string()), UVM_MEDIUM)
        end else begin
            mismatch_count++;
            `uvm_error("SCBD", $sformatf(
                "[MISMATCH #%0d]\n  Expected: %s\n  Actual:   %s",
                total_compared, exp.convert2string(), act.convert2string()))
            
            // 상세 필드 비교 (디버깅용)
            print_field_diff(exp, act);
        end
    endfunction
    
    //------------------------------------------
    // 필드별 차이 출력
    //------------------------------------------
    function void print_field_diff(out_transaction exp, out_transaction act);
        `uvm_info("SCBD", "=== Field Comparison ===", UVM_LOW)
        
        if (exp.result != act.result)
            `uvm_info("SCBD", $sformatf("  result: exp=0x%08h act=0x%08h", 
                      exp.result, act.result), UVM_LOW)
        
        if (exp.status != act.status)
            `uvm_info("SCBD", $sformatf("  status: exp=%s act=%s",
                      exp.status.name(), act.status.name()), UVM_LOW)
        
        // TODO: 다른 필드들 추가
        
        `uvm_info("SCBD", "========================", UVM_LOW)
    endfunction
    
    //------------------------------------------
    // 큐 오버플로우 체크
    //------------------------------------------
    function void check_queue_overflow();
        if (exp_queue.size() > max_queue_depth)
            `uvm_warning("SCBD", $sformatf(
                "Expected queue overflow: %0d items (no matching actual)",
                exp_queue.size()))
        
        if (act_queue.size() > max_queue_depth)
            `uvm_warning("SCBD", $sformatf(
                "Actual queue overflow: %0d items (no matching expected)",
                act_queue.size()))
    endfunction
    
    //------------------------------------------
    // Check Phase
    //------------------------------------------
    function void check_phase(uvm_phase phase);
        super.check_phase(phase);
        
        // 남은 항목 확인
        if (exp_queue.size() > 0)
            `uvm_error("SCBD", $sformatf(
                "%0d expected transactions never received from DUT",
                exp_queue.size()))
        
        if (act_queue.size() > 0)
            `uvm_error("SCBD", $sformatf(
                "%0d actual transactions with no expected match",
                act_queue.size()))
    endfunction
    
    //------------------------------------------
    // Report Phase
    //------------------------------------------
    function void report_phase(uvm_phase phase);
        string result_str;
        
        `uvm_info("SCBD", "========== Scoreboard Summary ==========", UVM_LOW)
        `uvm_info("SCBD", $sformatf("  Total Compared: %0d", total_compared), UVM_LOW)
        `uvm_info("SCBD", $sformatf("  Matches:        %0d", match_count), UVM_LOW)
        `uvm_info("SCBD", $sformatf("  Mismatches:     %0d", mismatch_count), UVM_LOW)
        
        if (mismatch_count == 0 && exp_queue.size() == 0 && act_queue.size() == 0)
            result_str = "PASSED";
        else
            result_str = "FAILED";
        
        `uvm_info("SCBD", $sformatf("  Result:         %s", result_str), UVM_LOW)
        `uvm_info("SCBD", "=========================================", UVM_LOW)
    endfunction
    
endclass

`endif
