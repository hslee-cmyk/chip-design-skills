# UVM Component Templates

## Transaction (Sequence Item)

```systemverilog
class my_transaction extends uvm_sequence_item;
    `uvm_object_utils(my_transaction)

    // ★ Request fields: rand, Response fields: NOT rand
    rand bit [31:0] addr;
    rand bit [31:0] data;
    rand bit        write;

    // Response fields (driver가 채움)
    bit [31:0] resp_data;
    bit [1:0]  resp_status;

    // Constraints
    constraint c_addr_align { addr[1:0] == 2'b00; }
    constraint c_valid_range { addr inside {[32'h0000:32'hFFFF]}; }

    function new(string name = "my_transaction");
        super.new(name);
    endfunction

    // ★ 필수: do_copy, do_compare, convert2string (uvm_field_* 대체)
    function void do_copy(uvm_object rhs);
        my_transaction rhs_;
        super.do_copy(rhs);
        $cast(rhs_, rhs);
        this.addr  = rhs_.addr;
        this.data  = rhs_.data;
        this.write = rhs_.write;
    endfunction

    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        my_transaction rhs_;
        if (!$cast(rhs_, rhs)) return 0;
        return (super.do_compare(rhs, comparer) &&
                this.addr  == rhs_.addr &&
                this.data  == rhs_.data &&
                this.write == rhs_.write);
    endfunction

    function string convert2string();
        return $sformatf("addr=0x%08h data=0x%08h %s",
                         addr, data, write ? "WR" : "RD");
    endfunction
endclass
```

### Transaction Methods 규칙

| 메서드 | 용도 | 비고 |
|--------|------|------|
| `do_copy()` | 깊은 복사 | `$cast` + 필드별 복사 |
| `do_compare()` | 비교 | `$cast` 실패 시 return 0 |
| `convert2string()` | 문자열 표현 | 디버깅/로그에 사용 |

**uvm_field_* 금지**: 성능 저하, 예측 불가능한 동작. 위 메서드를 직접 구현.

## Driver

```systemverilog
class my_driver extends uvm_driver #(my_transaction);
    `uvm_component_utils(my_driver)

    virtual my_interface vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual my_interface)::get(this, "", "vif", vif))
            `uvm_fatal("NOVIF", "Virtual interface not found")
    endfunction

    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            drive_transaction(req);
            seq_item_port.item_done();
        end
    endtask

    task drive_transaction(my_transaction tr);
        @(posedge vif.clk);
        vif.addr  <= tr.addr;
        vif.data  <= tr.data;
        vif.valid <= 1'b1;
        @(posedge vif.clk);
        while (!vif.ready) @(posedge vif.clk);
        vif.valid <= 1'b0;
    endtask
endclass
```

## Monitor

```systemverilog
class my_monitor extends uvm_monitor;
    `uvm_component_utils(my_monitor)

    virtual my_interface vif;
    uvm_analysis_port #(my_transaction) ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
        if (!uvm_config_db#(virtual my_interface)::get(this, "", "vif", vif))
            `uvm_fatal("NOVIF", "Virtual interface not found")
    endfunction

    task run_phase(uvm_phase phase);
        forever begin
            my_transaction tr;
            collect_transaction(tr);
            ap.write(tr);
        end
    endtask

    task collect_transaction(output my_transaction tr);
        tr = my_transaction::type_id::create("tr");
        @(posedge vif.clk);
        while (!(vif.valid && vif.ready)) @(posedge vif.clk);
        tr.addr  = vif.addr;
        tr.data  = vif.data;
        tr.write = vif.write;
    endtask
endclass
```

### Copy-on-Write 정책

Monitor에서 `ap.write(tr)` 호출 시 **핸들만 broadcast** 된다 (객체 복사 아님).
동일 객체를 다음 iteration에서 수정하면 subscriber가 참조하는 데이터도 변경되므로 주의.

**방법 1: 매 iteration마다 새 객체 생성 (권장)**
```systemverilog
task run_phase(uvm_phase phase);
    forever begin
        my_transaction tr = my_transaction::type_id::create("tr");
        collect_transaction(tr);
        ap.write(tr);  // 매번 새 객체 → 안전
    end
endtask
```

**방법 2: clone() 후 broadcast**
```systemverilog
task run_phase(uvm_phase phase);
    my_transaction tr = my_transaction::type_id::create("tr");
    forever begin
        collect_transaction(tr);
        $cast(tr_clone, tr.clone());
        ap.write(tr_clone);  // 원본 재사용, clone broadcast
    end
endtask
```

★ 위 Monitor 예제는 이미 방법 1을 사용 중 (`collect_transaction` 내부에서 create).
  하지만 명시적 경고 없이는 실수하기 쉬운 패턴.

## Agent

```systemverilog
class my_agent extends uvm_agent;
    `uvm_component_utils(my_agent)

    my_driver    drv;
    my_monitor   mon;
    uvm_sequencer #(my_transaction) seqr;

    uvm_analysis_port #(my_transaction) ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        mon = my_monitor::type_id::create("mon", this);
        if (get_is_active() == UVM_ACTIVE) begin
            drv  = my_driver::type_id::create("drv", this);
            seqr = uvm_sequencer#(my_transaction)::type_id::create("seqr", this);
        end
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        ap = mon.ap;  // passthrough
        if (get_is_active() == UVM_ACTIVE) begin
            drv.seq_item_port.connect(seqr.seq_item_export);
        end
    endfunction
endclass
```

## Config Object

```systemverilog
class env_config extends uvm_object;
    `uvm_object_utils(env_config)

    // 조건부 빌드 플래그
    bit has_scoreboard       = 1;
    bit has_coverage         = 1;
    bit has_reg_model        = 0;

    // 중첩 agent config
    agent_config m_agent_cfg;

    // rand 지원 (테스트에서 randomize 가능)
    rand int num_transactions;
    constraint c_txn { num_transactions inside {[100:1000]}; }

    function new(string name = "env_config");
        super.new(name);
        m_agent_cfg = agent_config::type_id::create("m_agent_cfg");
    endfunction

    function void do_copy(uvm_object rhs);
        env_config rhs_;
        super.do_copy(rhs);
        $cast(rhs_, rhs);
        this.has_scoreboard = rhs_.has_scoreboard;
        this.has_coverage   = rhs_.has_coverage;
        this.has_reg_model  = rhs_.has_reg_model;
        this.m_agent_cfg.copy(rhs_.m_agent_cfg);
    endfunction
endclass

class agent_config extends uvm_object;
    `uvm_object_utils(agent_config)

    uvm_active_passive_enum is_active = UVM_ACTIVE;
    virtual my_interface     vif;

    function new(string name = "agent_config");
        super.new(name);
    endfunction
endclass
```

## Scoreboard Patterns

### In-Order (Queue-based)

```systemverilog
class my_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(my_scoreboard)

    uvm_analysis_imp #(my_transaction, my_scoreboard) ap;

    my_transaction expected_queue[$];
    int match_count, mismatch_count;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap = new("ap", this);
    endfunction

    function void write(my_transaction tr);
        my_transaction exp;
        if (expected_queue.size() == 0) begin
            `uvm_error("SCBD", "Unexpected transaction received")
            return;
        end
        exp = expected_queue.pop_front();
        if (tr.compare(exp)) begin
            match_count++;
            `uvm_info("SCBD", $sformatf("MATCH: %s", tr.convert2string()), UVM_MEDIUM)
        end else begin
            mismatch_count++;
            `uvm_error("SCBD", $sformatf("MISMATCH:\n  EXP: %s\n  GOT: %s",
                       exp.convert2string(), tr.convert2string()))
        end
    endfunction

    function void report_phase(uvm_phase phase);
        `uvm_info("SCBD", $sformatf("Matches: %0d, Mismatches: %0d",
                  match_count, mismatch_count), UVM_LOW)
    endfunction
endclass
```

### In-Order (FIFO-based)

```systemverilog
class fifo_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(fifo_scoreboard)

    // ★ 두 analysis port를 FIFO로 분리
    uvm_tlm_analysis_fifo #(my_transaction) expected_fifo;
    uvm_tlm_analysis_fifo #(my_transaction) actual_fifo;

    uvm_analysis_export #(my_transaction) expected_export;
    uvm_analysis_export #(my_transaction) actual_export;

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        expected_fifo   = new("expected_fifo", this);
        actual_fifo     = new("actual_fifo", this);
        expected_export = new("expected_export", this);
        actual_export   = new("actual_export", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        expected_export.connect(expected_fifo.analysis_export);
        actual_export.connect(actual_fifo.analysis_export);
    endfunction

    task run_phase(uvm_phase phase);
        my_transaction expected_tr, actual_tr;
        forever begin
            expected_fifo.get(expected_tr);
            actual_fifo.get(actual_tr);
            if (!actual_tr.compare(expected_tr))
                `uvm_error("SCBD", "Mismatch detected")
        end
    endtask
endclass
```

### Out-of-Order

```systemverilog
class ooo_scoreboard extends uvm_scoreboard;
    `uvm_component_utils(ooo_scoreboard)

    // ★ Associative array — ID 기반 매칭
    my_transaction expected_aa[bit [31:0]];  // key = transaction ID

    function void add_expected(my_transaction tr);
        expected_aa[tr.id] = tr;
    endfunction

    function void write_actual(my_transaction tr);
        if (expected_aa.exists(tr.id)) begin
            if (!tr.compare(expected_aa[tr.id]))
                `uvm_error("SCBD", "Out-of-order mismatch")
            expected_aa.delete(tr.id);
        end else begin
            `uvm_error("SCBD", $sformatf("No expected transaction for ID=%0d", tr.id))
        end
    endfunction

    function void check_phase(uvm_phase phase);
        if (expected_aa.size() > 0)
            `uvm_error("SCBD", $sformatf("%0d unmatched expected transactions",
                       expected_aa.size()))
    endfunction
endclass
```

## Predictor

```systemverilog
// ★ Separate Prediction from Evaluation
class my_predictor extends uvm_subscriber #(my_transaction);
    `uvm_component_utils(my_predictor)

    uvm_analysis_port #(my_transaction) predicted_ap;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        predicted_ap = new("predicted_ap", this);
    endfunction

    // ★ 입력 트랜잭션 기반으로 예측 결과 생성
    function void write(my_transaction t);
        my_transaction predicted;
        predicted = my_transaction::type_id::create("predicted");
        predicted.copy(t);

        // 예측 로직 (reference model)
        predicted.data = calculate_expected(t.addr, t.data, t.write);

        predicted_ap.write(predicted);  // scoreboard로 전달
    endfunction
endclass
```

## Metric Analyzer

```systemverilog
class metric_analyzer extends uvm_component;
    `uvm_component_utils(metric_analyzer)

    int total_transactions;
    int error_count;
    real throughput;
    real latency_sum;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    // ★ extract_phase → check_phase → report_phase 순서
    function void extract_phase(uvm_phase phase);
        // 시뮬레이션 데이터에서 메트릭 추출
        throughput = real'(total_transactions) / ($time / 1ns);
    endfunction

    function void check_phase(uvm_phase phase);
        // 메트릭 기준 검증
        if (throughput < 0.8)
            `uvm_error("METRIC", $sformatf("Throughput %.2f below threshold 0.8", throughput))
        if (error_count > 0)
            `uvm_error("METRIC", $sformatf("%0d errors detected", error_count))
    endfunction

    function void report_phase(uvm_phase phase);
        `uvm_info("METRIC", $sformatf(
            "Transactions: %0d, Errors: %0d, Throughput: %.2f, Avg Latency: %.1f ns",
            total_transactions, error_count, throughput,
            total_transactions > 0 ? latency_sum / total_transactions : 0.0
        ), UVM_LOW)
    endfunction
endclass
```

## Environment

```systemverilog
class my_env extends uvm_env;
    `uvm_component_utils(my_env)

    env_config    cfg;
    my_agent      agent;
    my_predictor  pred;
    my_scoreboard scbd;
    my_coverage   cov;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db#(env_config)::get(this, "", "env_cfg", cfg))
            `uvm_fatal("NOCFG", "env_config not found")

        agent = my_agent::type_id::create("agent", this);
        pred  = my_predictor::type_id::create("pred", this);

        if (cfg.has_scoreboard)
            scbd = my_scoreboard::type_id::create("scbd", this);
        if (cfg.has_coverage)
            cov = my_coverage::type_id::create("cov", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // ★ Analysis Pipeline: monitor → predictor → scoreboard
        agent.ap.connect(pred.analysis_export);

        if (cfg.has_scoreboard)
            pred.predicted_ap.connect(scbd.ap);
        if (cfg.has_coverage)
            agent.ap.connect(cov.analysis_export);
    endfunction
endclass
```

### Analysis Pipeline

```
Monitor → Analysis Port ─┬─→ Predictor → Predicted AP → Scoreboard
                         └─→ Coverage Subscriber
```

### Post-Run Phases 순서

```
extract_phase()  → 시뮬레이션 데이터 수집/변환
check_phase()    → 최종 검증 (미처리 큐, 메트릭 기준)
report_phase()   → 결과 출력
```

## Test

```systemverilog
class my_base_test extends uvm_test;
    `uvm_component_utils(my_base_test)

    my_env     env;
    env_config cfg;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        cfg = env_config::type_id::create("cfg");
        cfg.randomize();
        uvm_config_db#(env_config)::set(this, "env", "env_cfg", cfg);
        env = my_env::type_id::create("env", this);
    endfunction

    function void end_of_elaboration_phase(uvm_phase phase);
        uvm_top.print_topology();
    endfunction
endclass

class my_sanity_test extends my_base_test;
    `uvm_component_utils(my_sanity_test)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        my_basic_sequence seq;
        phase.raise_objection(this);
        seq = my_basic_sequence::type_id::create("seq");
        seq.start(env.agent.seqr);
        phase.drop_objection(this);
    endtask
endclass
```

## Reactive Slave Agent

### 단일 Seq Item

기존 Reactive Sequence 참조 (sequence-patterns.md > Reactive Sequence). Slave driver가 protocol에 따라 응답:

```systemverilog
class slave_driver extends uvm_driver #(slave_transaction);
    `uvm_component_utils(slave_driver)
    virtual slave_interface vif;

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            // ★ Protocol 응답: request에 맞는 response 생성
            drive_response(req);
            seq_item_port.item_done();
        end
    endtask
endclass
```

### 다중 Seq Item (Multi-Phase Protocol)

Phase별 다른 sequence_item을 사용하는 프로토콜:

```systemverilog
// ★ Sequencer: base class 파라미터화로 다양한 item 타입 수용
uvm_sequencer #(uvm_sequence_item) slave_seqr;

// Multi-phase slave driver
class multi_phase_slave_driver extends uvm_driver #(uvm_sequence_item);
    `uvm_component_utils(multi_phase_slave_driver)

    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    task run_phase(uvm_phase phase);
        uvm_sequence_item item;
        config_response_item cfg_rsp;
        data_response_item   data_rsp;

        forever begin
            // ★ Config phase
            seq_item_port.get_next_item(item);
            if (!$cast(cfg_rsp, item))
                `uvm_fatal("CAST", "Expected config_response_item")
            drive_config_response(cfg_rsp);
            seq_item_port.item_done();

            // ★ Data phase
            seq_item_port.get_next_item(item);
            if (!$cast(data_rsp, item))
                `uvm_fatal("CAST", "Expected data_response_item")
            drive_data_response(data_rsp);
            seq_item_port.item_done();
        end
    endtask
endclass
```

**주의**: strict phase alternation contract 준수 — config/data phase 순서가 어긋나면 `$cast` 실패로 즉시 감지.

## Wait-for-Signal Pattern

Agent 없이 특정 신호를 대기하는 lightweight 패턴. 3-layer delegation 구조:

```
Sequence → Config Object → BFM Interface
```

```systemverilog
// BFM interface — automatic 키워드 필수
interface signal_bfm;
    logic [7:0] status;

    // ★ automatic: 병렬 호출 시 독립 stack
    task automatic wait_for_status(input logic [7:0] expected);
        while (status !== expected) @(posedge clk);
    endtask
endinterface

// Config object — BFM 핸들 보유
class signal_config extends uvm_object;
    `uvm_object_utils(signal_config)
    virtual signal_bfm bfm;

    task wait_for_signal(logic [7:0] expected);
        bfm.wait_for_status(expected);
    endtask

    function new(string name = "signal_config");
        super.new(name);
    endfunction
endclass

// Sequence에서 사용
class wait_status_seq extends uvm_sequence;
    `uvm_object_utils(wait_status_seq)
    signal_config cfg;

    task body();
        // ★ config_db: sequence에서는 get(null, get_full_name(), ...) 패턴
        if (!uvm_config_db#(signal_config)::get(null, get_full_name(), "sig_cfg", cfg))
            `uvm_fatal("NOCFG", "signal_config not found")
        cfg.wait_for_signal(8'hFF);
    endtask

    function new(string name = "wait_status_seq");
        super.new(name);
    endfunction
endclass
```

