//----------------------------------------------------------------------
// Agent Package
//
// 1 class = 1 file 원칙. 의존성 순서대로 include.
// BFM interface (.sv)는 package에 포함하지 않음 — hdl_top에서 별도 컴파일.
//
// Source: Verification Academy - UVM Cookbook / Subsystem TB Example
//----------------------------------------------------------------------

// Questa recording macro
`define uvm_record_field(NAME,VALUE) \
   $add_attribute(recorder.get_handle(),VALUE,NAME);

package myagent_agent_pkg;

import uvm_pkg::*;
`include "uvm_macros.svh"

// Sequence Item & Config (순서 중요: 의존성 먼저)
`include "myagent_seq_item.svh"
`include "myagent_agent_config.svh"

// Components
`include "myagent_driver.svh"
`include "myagent_coverage_monitor.svh"
`include "myagent_monitor.svh"
typedef uvm_sequencer #(myagent_seq_item) myagent_sequencer;
`include "myagent_agent.svh"

// Register Adapter
`include "myagent_reg_adapter.svh"

// Utility Sequences
`include "myagent_seq.svh"
`include "myagent_read_seq.svh"
`include "myagent_write_seq.svh"

endpackage
