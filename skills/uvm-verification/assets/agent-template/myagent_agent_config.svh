//----------------------------------------------------------------------
// Agent Configuration
//
// BFM 핸들, active/passive, has_coverage 등을 포함하는 config object.
// Test의 build_phase에서 생성하여 config_db로 전달.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_agent_config extends uvm_object;

`uvm_object_utils(myagent_agent_config)

// BFM Virtual Interfaces
virtual myagent_monitor_bfm mon_bfm;
virtual myagent_driver_bfm  drv_bfm;

//------------------------------------------
// Data Members
//------------------------------------------
uvm_active_passive_enum active = UVM_ACTIVE;
bit has_functional_coverage = 0;
bit has_scoreboard = 0;

// TODO: 프로토콜별 설정 추가 (예: address map, select lines 등)

//------------------------------------------
// Methods
//------------------------------------------
function new(string name = "myagent_agent_config");
  super.new(name);
endfunction

// Static convenience method
static function myagent_agent_config get_config(uvm_component c);
  myagent_agent_config t;
  if (!uvm_config_db #(myagent_agent_config)::get(c, "", "myagent_agent_config", t))
    `uvm_fatal("CONFIG_LOAD",
      $sformatf("Cannot get() configuration myagent_agent_config from uvm_config_db. Have you set() it?"))
  return t;
endfunction

endclass
