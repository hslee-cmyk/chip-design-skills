//----------------------------------------------------------------------
// Base Random Sequence
//
// start_item/finish_item 패턴 사용 (uvm_do 금지).
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_seq extends uvm_sequence #(myagent_seq_item);

`uvm_object_utils(myagent_seq)

function new(string name = "myagent_seq");
  super.new(name);
endfunction

task body;
  myagent_seq_item req;

  req = myagent_seq_item::type_id::create("req");
  start_item(req);
  if (!req.randomize())
    `uvm_fatal("RAND", "Randomization failed")
  finish_item(req);
endtask

endclass
