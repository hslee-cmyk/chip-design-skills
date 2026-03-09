//----------------------------------------------------------------------
// Directed Write Sequence
//
// 특정 주소에 데이터 쓰기. addr, data를 설정하고 start() 호출.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_write_seq extends uvm_sequence #(myagent_seq_item);

`uvm_object_utils(myagent_write_seq)

//------------------------------------------
// Data Members
//------------------------------------------
rand logic [31:0] addr;
rand logic [31:0] data;

function new(string name = "myagent_write_seq");
  super.new(name);
endfunction

task body;
  myagent_seq_item req = myagent_seq_item::type_id::create("req");

  start_item(req);
  req.we   = 1;
  req.addr = addr;
  req.data = data;
  finish_item(req);
endtask

endclass
