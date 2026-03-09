//----------------------------------------------------------------------
// Agent
//
// Config object에 따라 active/passive 및 coverage monitor를 조건부 빌드.
// Analysis port는 monitor의 ap를 passthrough.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_agent extends uvm_component;

`uvm_component_utils(myagent_agent)

//------------------------------------------
// Data Members
//------------------------------------------
myagent_agent_config m_cfg;

//------------------------------------------
// Component Members
//------------------------------------------
uvm_analysis_port #(myagent_seq_item) ap;
myagent_monitor            m_monitor;
myagent_sequencer          m_sequencer;
myagent_driver             m_driver;
myagent_coverage_monitor   m_fcov_monitor;

//------------------------------------------
// Methods
//------------------------------------------
function new(string name = "myagent_agent", uvm_component parent = null);
  super.new(name, parent);
endfunction

function void build_phase(uvm_phase phase);
  super.build_phase(phase);
  m_cfg = myagent_agent_config::get_config(this);
  // Monitor is always present
  m_monitor = myagent_monitor::type_id::create("m_monitor", this);
  // Only build driver and sequencer if active
  if (m_cfg.active == UVM_ACTIVE) begin
    m_driver    = myagent_driver::type_id::create("m_driver", this);
    m_sequencer = myagent_sequencer::type_id::create("m_sequencer", this);
  end
  if (m_cfg.has_functional_coverage) begin
    m_fcov_monitor = myagent_coverage_monitor::type_id::create("m_fcov_monitor", this);
  end
endfunction

function void connect_phase(uvm_phase phase);
  super.connect_phase(phase);
  ap = m_monitor.ap;
  if (m_cfg.active == UVM_ACTIVE) begin
    m_driver.seq_item_port.connect(m_sequencer.seq_item_export);
  end
  if (m_cfg.has_functional_coverage) begin
    m_monitor.ap.connect(m_fcov_monitor.analysis_export);
  end
endfunction

endclass
