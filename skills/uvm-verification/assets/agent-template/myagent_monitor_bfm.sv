//----------------------------------------------------------------------
// Monitor BFM
//
// 프로토콜 이벤트를 감지하여 proxy(monitor)에 트랜잭션을 전달.
// hdl_top에서 인스턴스화하여 DUT 신호에 연결.
//
// TODO: 포트/프로토콜에 맞게 수정
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
interface myagent_monitor_bfm (
  input        clk,
  input        rst_n,

  input logic [31:0] addr,
  input logic [31:0] wdata,
  input logic [31:0] rdata,
  input logic        we,
  input logic        valid,
  input logic        ready
);

import myagent_agent_pkg::*;

//------------------------------------------
// Data Members
//------------------------------------------
myagent_monitor proxy;

//------------------------------------------
// Methods
//------------------------------------------

// TODO: 프로토콜에 맞게 감지 로직 수정
task run();
  myagent_seq_item item;
  myagent_seq_item cloned_item;

  item = myagent_seq_item::type_id::create("item");

  forever begin
    @(posedge clk);
    if (valid && ready) begin
      item.addr = addr;
      item.we   = we;
      item.data = we ? wdata : rdata;
      // Clone and publish
      $cast(cloned_item, item.clone());
      proxy.notify_transaction(cloned_item);
    end
  end
endtask

endinterface
