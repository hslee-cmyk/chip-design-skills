//----------------------------------------------------------------------
// Directed Read Sequence
//
// 특정 주소에서 읽기. addr를 설정하고 start() 호출.
// 읽은 데이터는 data 필드에 반환.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_read_seq extends uvm_sequence #(myagent_seq_item);

`uvm_object_utils(myagent_read_seq)

//------------------------------------------
// Data Members
//------------------------------------------
rand logic [31:0] addr;
logic [31:0] data;  // output: read data

function new(string name = "myagent_read_seq");
  super.new(name);
endfunction

task body;
  myagent_seq_item req = myagent_seq_item::type_id::create("req");

  start_item(req);
  req.we   = 0;
  req.addr = addr;
  finish_item(req);
  // Capture read data from response
  data = req.data;
endtask

endclass
