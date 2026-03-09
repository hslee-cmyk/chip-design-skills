//----------------------------------------------------------------------
// Signal Interface (Signal Container)
//
// DUT와 BFM 사이의 신호 연결용.
// BFM이 이 interface의 신호를 통해 DUT와 통신.
//
// TODO: DUT 포트에 맞게 신호 수정
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------
interface myagent_if (
  input PCLK,
  input PRESETn
);

logic [31:0] addr;
logic [31:0] wdata;
logic [31:0] rdata;
logic        we;
logic        valid;
logic        ready;

//------------------------------------------
// Assertions (Optional)
//------------------------------------------
property p_valid_stable;
  @(posedge PCLK) disable iff (!PRESETn)
  valid |-> ##[1:100] ready;
endproperty

CHK_VALID: assert property (p_valid_stable);

endinterface
