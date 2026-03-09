//----------------------------------------------------------------------
// Coverage Monitor
//
// uvm_subscriber 기반 functional coverage collector.
// Agent의 monitor analysis port에 연결.
//
// TODO: covergroup을 프로토콜/검증항목에 맞게 수정
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_coverage_monitor extends uvm_subscriber #(myagent_seq_item);

`uvm_component_utils(myagent_coverage_monitor)

//------------------------------------------
// Cover Group(s)
//------------------------------------------
covergroup myagent_cov;
  OPCODE: coverpoint analysis_txn.we {
    bins write = {1};
    bins read  = {0};
  }
  // TODO: address range, data patterns 등 추가
endgroup

//------------------------------------------
// Data Members
//------------------------------------------
myagent_seq_item analysis_txn;

//------------------------------------------
// Methods
//------------------------------------------
function new(string name = "myagent_coverage_monitor", uvm_component parent = null);
  super.new(name, parent);
  myagent_cov = new();
endfunction

function void write(T t);
  analysis_txn = t;
  myagent_cov.sample();
endfunction

endclass
