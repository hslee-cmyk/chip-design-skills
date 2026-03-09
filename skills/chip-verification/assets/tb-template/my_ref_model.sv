`ifndef __MY_REF_MODEL_SV__
`define __MY_REF_MODEL_SV__

class my_ref_model extends uvm_component;
    `uvm_component_utils(my_ref_model)
    
    //------------------------------------------
    // TLM Ports
    //------------------------------------------
    uvm_analysis_imp #(in_transaction, my_ref_model) in_ap;
    uvm_analysis_port #(out_transaction) out_ap;
    
    //------------------------------------------
    // Internal State (RTL 파이프라인 모델링)
    //------------------------------------------
    
    // 파이프라인 깊이 (RTL 사이클 분석에서 결정)
    // verilog-rtl skill 사이클 분석 결과 반영
    localparam int PIPELINE_DEPTH = 2;  // TODO: RTL에 맞게 수정
    
    // 파이프라인 큐
    in_transaction pipeline_queue[$];
    
    // 옵션: 사이클 정확 모델링용
    virtual my_dut_if vif;
    bit cycle_accurate_mode = 0;
    
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
        in_ap  = new("in_ap", this);
        out_ap = new("out_ap", this);
        
        // 사이클 정확 모드 설정 (옵션)
        if (uvm_config_db#(virtual my_dut_if)::get(this, "", "dut_vif", vif))
            cycle_accurate_mode = 1;
    endfunction
    
    //------------------------------------------
    // Run Phase (사이클 정확 모드)
    //------------------------------------------
    task run_phase(uvm_phase phase);
        if (cycle_accurate_mode) begin
            forever begin
                @(posedge vif.clk);
                process_cycle();
            end
        end
    endtask
    
    //------------------------------------------
    // 입력 수신 (Analysis Port)
    //------------------------------------------
    function void write(in_transaction tr);
        in_transaction tr_copy;
        
        // Deep copy
        $cast(tr_copy, tr.clone());
        
        `uvm_info("REF", $sformatf("Received: %s", tr.convert2string()), UVM_HIGH)
        
        if (cycle_accurate_mode) begin
            // 사이클 정확 모드: 큐에 추가만
            pipeline_queue.push_back(tr_copy);
        end else begin
            // 트랜잭션 레벨 모드: 즉시 예측
            pipeline_queue.push_back(tr_copy);
            check_and_output();
        end
    endfunction
    
    //------------------------------------------
    // 사이클 처리 (사이클 정확 모드)
    //------------------------------------------
    function void process_cycle();
        // 파이프라인 진행
        // RTL의 always_ff 블록과 대응
        
        if (pipeline_queue.size() >= PIPELINE_DEPTH) begin
            out_transaction out_tr;
            in_transaction in_tr;
            
            in_tr = pipeline_queue.pop_front();
            out_tr = predict(in_tr);
            out_ap.write(out_tr);
            
            `uvm_info("REF", $sformatf("Output: %s", out_tr.convert2string()), UVM_HIGH)
        end
    endfunction
    
    //------------------------------------------
    // 출력 확인 (트랜잭션 레벨 모드)
    //------------------------------------------
    function void check_and_output();
        if (pipeline_queue.size() >= PIPELINE_DEPTH) begin
            out_transaction out_tr;
            in_transaction in_tr;
            
            in_tr = pipeline_queue.pop_front();
            out_tr = predict(in_tr);
            out_ap.write(out_tr);
            
            `uvm_info("REF", $sformatf("Output: %s", out_tr.convert2string()), UVM_HIGH)
        end
    endfunction
    
    //------------------------------------------
    // 예측 함수 (TODO: RTL 로직에 맞게 구현)
    //------------------------------------------
    function out_transaction predict(in_transaction in_tr);
        out_transaction out_tr;
        out_tr = out_transaction::type_id::create("out_tr");
        
        // ===================================
        // RTL 동작을 여기서 모델링
        // verilog-rtl skill의 always_comb 로직 참조
        // ===================================
        
        // 예시: 단순 덧셈
        out_tr.result = in_tr.data + 1;
        out_tr.status = (in_tr.valid) ? SUCCESS : ERROR;
        
        // 예시: 조건부 처리
        if (in_tr.opcode == OP_ADD)
            out_tr.result = in_tr.operand_a + in_tr.operand_b;
        else if (in_tr.opcode == OP_SUB)
            out_tr.result = in_tr.operand_a - in_tr.operand_b;
        
        return out_tr;
    endfunction
    
    //------------------------------------------
    // Report Phase
    //------------------------------------------
    function void report_phase(uvm_phase phase);
        if (pipeline_queue.size() > 0)
            `uvm_warning("REF", $sformatf("%0d transactions still in pipeline", 
                         pipeline_queue.size()))
    endfunction
    
endclass

`endif
