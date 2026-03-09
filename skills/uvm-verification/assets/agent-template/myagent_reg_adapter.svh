//----------------------------------------------------------------------
// Register Adapter
//
// UVM Register Model과 bus agent 사이의 변환.
// reg2bus: register operation → sequence item
// bus2reg: sequence item → register operation
//
// TODO: 프로토콜에 맞게 필드 매핑 수정
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
class myagent_reg_adapter extends uvm_reg_adapter;

`uvm_object_utils(myagent_reg_adapter)

function new(string name = "myagent_reg_adapter");
  super.new(name);
  // Does the protocol support byte enables?
  supports_byte_enable = 0;
  // Does the driver provide separate response items via put()?
  provides_responses = 0;
endfunction

virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
  myagent_seq_item item = myagent_seq_item::type_id::create("item");

  item.we   = (rw.kind == UVM_READ) ? 1'b0 : 1'b1;
  item.addr = rw.addr;
  item.data = rw.data;
  item.delay = 1;
  return item;
endfunction

virtual function void bus2reg(uvm_sequence_item bus_item,
                              ref uvm_reg_bus_op rw);
  myagent_seq_item item;
  if (!$cast(item, bus_item)) begin
    `uvm_fatal("NOT_BUS_TYPE", "Provided bus_item is not the correct type")
    return;
  end
  rw.kind   = (item.we) ? UVM_WRITE : UVM_READ;
  rw.addr   = item.addr;
  rw.data   = item.data;
  rw.status = UVM_IS_OK;
endfunction

endclass
