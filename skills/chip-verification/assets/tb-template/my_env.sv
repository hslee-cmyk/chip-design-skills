`ifndef __MY_ENV_SV__
`define __MY_ENV_SV__

class my_env extends uvm_env;
    `uvm_component_utils(my_env)
    
    //------------------------------------------
    // Components
    //------------------------------------------
    my_in_agent     in_agent;    // Input side (active)
    my_out_agent    out_agent;   // Output side (passive or reactive)
    my_ref_model    ref_model;   // Reference model
    my_scoreboard   scbd;        // Comparator
    my_coverage     cov;         // Functional coverage
    
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
        
        // Agents
        in_agent  = my_in_agent::type_id::create("in_agent", this);
        out_agent = my_out_agent::type_id::create("out_agent", this);
        
        // Analysis components
        ref_model = my_ref_model::type_id::create("ref_model", this);
        scbd      = my_scoreboard::type_id::create("scbd", this);
        cov       = my_coverage::type_id::create("cov", this);
        
        // Agent configuration
        uvm_config_db#(uvm_active_passive_enum)::set(
            this, "in_agent", "is_active", UVM_ACTIVE);
        uvm_config_db#(uvm_active_passive_enum)::set(
            this, "out_agent", "is_active", UVM_PASSIVE);
    endfunction
    
    //------------------------------------------
    // Connect Phase
    //------------------------------------------
    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        // Input → Reference Model
        in_agent.ap.connect(ref_model.in_ap);
        
        // Input → Coverage
        in_agent.ap.connect(cov.in_ap);
        
        // Reference Model → Scoreboard (expected)
        ref_model.out_ap.connect(scbd.exp_ap);
        
        // Output Monitor → Scoreboard (actual)
        out_agent.ap.connect(scbd.act_ap);
        
        // Output → Coverage
        out_agent.ap.connect(cov.out_ap);
    endfunction
    
endclass

`endif
