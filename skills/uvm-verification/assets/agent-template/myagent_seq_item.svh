//----------------------------------------------------------------------
// Sequence Item (TODO: 프로토콜에 맞게 필드/제약 수정)
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_seq_item extends uvm_sequence_item;

`uvm_object_utils(myagent_seq_item)

//------------------------------------------
// Data Members (Outputs rand, inputs non-rand)
//------------------------------------------
rand logic [31:0] addr;
rand logic [31:0] data;
rand logic        we;
rand int          delay;

bit error;  // response status

//------------------------------------------
// Constraints (TODO: 프로토콜에 맞게 수정)
//------------------------------------------
constraint c_addr_align {
  addr[1:0] == 0;
}

constraint c_delay {
  delay inside {[1:20]};
}

//------------------------------------------
// Methods
//------------------------------------------
function new(string name = "myagent_seq_item");
  super.new(name);
endfunction

function void do_copy(uvm_object rhs);
  myagent_seq_item rhs_;

  if (!$cast(rhs_, rhs))
    `uvm_fatal("do_copy", "cast of rhs object failed")
  super.do_copy(rhs);
  addr  = rhs_.addr;
  data  = rhs_.data;
  we    = rhs_.we;
  delay = rhs_.delay;
endfunction

function bit do_compare(uvm_object rhs, uvm_comparer comparer);
  myagent_seq_item rhs_;

  if (!$cast(rhs_, rhs)) return 0;
  return (super.do_compare(rhs, comparer) &&
          addr == rhs_.addr &&
          data == rhs_.data &&
          we   == rhs_.we);
  // delay is not relevant to comparison
endfunction

function string convert2string();
  return $sformatf("addr=0x%08h data=0x%08h %s delay=%0d",
                   addr, data, we ? "WR" : "RD", delay);
endfunction

function void do_print(uvm_printer printer);
  printer.m_string = convert2string();
endfunction

function void do_record(uvm_recorder recorder);
  super.do_record(recorder);
  `uvm_record_field("addr", addr)
  `uvm_record_field("data", data)
  `uvm_record_field("we", we)
  `uvm_record_field("delay", delay)
endfunction

endclass
