//----------------------------------------------------------------------
// Driver
//
// BFM에 트랜잭션을 위임하여 프로토콜 핀을 구동.
// pin-level 동작은 myagent_driver_bfm.sv에 구현.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_driver extends uvm_driver #(myagent_seq_item, myagent_seq_item);

`uvm_component_utils(myagent_driver)

virtual myagent_driver_bfm m_bfm;

//------------------------------------------
// Data Members
//------------------------------------------
myagent_agent_config m_cfg;

//------------------------------------------
// Methods
//------------------------------------------
function new(string name = "myagent_driver", uvm_component parent = null);
  super.new(name, parent);
endfunction

function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  m_cfg = myagent_agent_config::get_config(this);
  m_bfm = m_cfg.drv_bfm;
endfunction

task run_phase(uvm_phase phase);
  myagent_seq_item req;

  m_bfm.wait_for_reset();
  forever begin
    m_bfm.clear_sigs();
    seq_item_port.get_next_item(req);
    m_bfm.drive(req);
    seq_item_port.item_done();
  end
endtask

endclass
