//----------------------------------------------------------------------
// Monitor
//
// Proxy 패턴: BFM이 트랜잭션을 감지하면 proxy.notify_transaction() 호출.
// Monitor 자체는 analysis port에 write만 수행.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_monitor extends uvm_component;

`uvm_component_utils(myagent_monitor)

virtual myagent_monitor_bfm m_bfm;

//------------------------------------------
// Data Members
//------------------------------------------
myagent_agent_config m_cfg;

//------------------------------------------
// Component Members
//------------------------------------------
uvm_analysis_port #(myagent_seq_item) ap;

//------------------------------------------
// Methods
//------------------------------------------
function new(string name = "myagent_monitor", uvm_component parent = null);
  super.new(name, parent);
endfunction

function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  m_cfg = myagent_agent_config::get_config(this);
  m_bfm = m_cfg.mon_bfm;
  m_bfm.proxy = this;
  ap = new("ap", this);
endfunction

task run_phase(uvm_phase phase);
  m_bfm.run();
endtask

// Proxy callback — BFM에서 호출
function void notify_transaction(myagent_seq_item item);
  ap.write(item);
endfunction

endclass
