//----------------------------------------------------------------------
// Driver BFM
//
// Pin-level 프로토콜 동작을 캡슐화하는 interface.
// hdl_top에서 인스턴스화하여 DUT 신호에 연결.
// Emulation-ready: 모든 pin-level 코드가 이 BFM에 집중.
//
// TODO: 포트/프로토콜에 맞게 수정
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
interface myagent_driver_bfm (
  input        clk,
  input        rst_n,

  output logic [31:0] addr,
  output logic [31:0] wdata,
  input  logic [31:0] rdata,
  output logic        we,
  output logic        valid,
  input  logic        ready
);

`include "uvm_macros.svh"
import uvm_pkg::*;
import myagent_agent_pkg::*;

//------------------------------------------
// Methods
//------------------------------------------

task wait_for_reset();
  @(posedge rst_n);
endtask

function void clear_sigs();
  valid <= 0;
  addr  <= 0;
  wdata <= 0;
  we    <= 0;
endfunction

// TODO: 프로토콜에 맞게 drive 로직 수정
task drive(myagent_seq_item req);
  repeat (req.delay)
    @(posedge clk);
  addr  <= req.addr;
  wdata <= req.data;
  we    <= req.we;
  valid <= 1;
  @(posedge clk);
  while (!ready)
    @(posedge clk);
  if (!req.we)
    req.data = rdata;
  valid <= 0;
endtask

endinterface
