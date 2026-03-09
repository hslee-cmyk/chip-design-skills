# UVM Sequence Patterns

## Basic Sequence

```systemverilog
class my_basic_sequence extends uvm_sequence #(my_transaction);
    `uvm_object_utils(my_basic_sequence)

    rand int num_items;
    constraint c_num { num_items inside {[5:20]}; }

    function new(string name = "my_basic_sequence");
        super.new(name);
    endfunction

    task body();
        repeat (num_items) begin
            req = my_transaction::type_id::create("req");
            start_item(req);
            if (!req.randomize())
                `uvm_fatal("RAND", "Randomization failed")
            finish_item(req);
        end
    endtask
endclass
```

## Constrained Sequence

```systemverilog
class my_write_sequence extends uvm_sequence #(my_transaction);
    `uvm_object_utils(my_write_sequence)

    rand bit [31:0] target_addr;

    function new(string name = "my_write_sequence");
        super.new(name);
    endfunction

    task body();
        req = my_transaction::type_id::create("req");
        start_item(req);
        if (!req.randomize() with { addr == target_addr; write == 1; })
            `uvm_fatal("RAND", "Randomization failed")
        finish_item(req);
    endtask
endclass
```

## Sequence with Response

```systemverilog
class my_read_sequence extends uvm_sequence #(my_transaction);
    `uvm_object_utils(my_read_sequence)

    bit [31:0] read_data;

    task body();
        req = my_transaction::type_id::create("req");
        start_item(req);
        if (!req.randomize() with { write == 0; })
            `uvm_fatal("RAND", "Randomization failed")
        finish_item(req);
        get_response(rsp);  // driver가 item_done(rsp) 호출 필요
        read_data = rsp.data;
    endtask
endclass
```

## Layered Sequence (Nested)

```systemverilog
class my_burst_sequence extends uvm_sequence #(my_transaction);
    `uvm_object_utils(my_burst_sequence)

    rand int burst_len;
    constraint c_len { burst_len inside {[4:16]}; }

    task body();
        my_write_sequence wr_seq;
        my_read_sequence  rd_seq;

        // Write burst
        repeat (burst_len) begin
            wr_seq = my_write_sequence::type_id::create("wr_seq");
            wr_seq.start(m_sequencer);
        end

        // Read back
        repeat (burst_len) begin
            rd_seq = my_read_sequence::type_id::create("rd_seq");
            rd_seq.start(m_sequencer);
        end
    endtask
endclass
```

## Virtual Sequence (Multi-Agent)

```systemverilog
// ★ 권장: Virtual Sequencer 없이 standalone + null sequencer
class my_virtual_sequence extends uvm_sequence;
    `uvm_object_utils(my_virtual_sequence)

    // Sequencer 핸들 — config 또는 init_vseq()로 설정
    uvm_sequencer #(master_transaction) master_seqr;
    uvm_sequencer #(slave_transaction)  slave_seqr;

    function new(string name = "my_virtual_sequence");
        super.new(name);
    endfunction

    task body();
        my_write_sequence master_seq;
        my_resp_sequence  slave_seq;

        fork
            begin  // Master agent
                master_seq = my_write_sequence::type_id::create("master_seq");
                master_seq.start(master_seqr);
            end
            begin  // Slave agent
                slave_seq = my_resp_sequence::type_id::create("slave_seq");
                slave_seq.start(slave_seqr);
            end
        join
    endtask
endclass
```

### init_vseq() 패턴

```systemverilog
// Test에서 virtual sequence의 sequencer 핸들을 설정
class my_test extends uvm_test;
    task run_phase(uvm_phase phase);
        my_virtual_sequence vseq;

        phase.raise_objection(this);

        vseq = my_virtual_sequence::type_id::create("vseq");
        init_vseq(vseq);
        vseq.start(null);  // null sequencer — virtual sequence는 sequencer 불필요

        phase.drop_objection(this);
    endtask

    function void init_vseq(my_virtual_sequence vseq);
        vseq.master_seqr = env.master_agent.seqr;
        vseq.slave_seqr  = env.slave_agent.seqr;
    endfunction
endclass
```

**Virtual Sequencer 비권장**: `uvm_declare_p_sequencer` + virtual sequencer 대신 위 패턴 사용. Virtual sequencer는 불필요한 컴포넌트 계층 추가.

## Sequence Library

```systemverilog
class my_sequence_library extends uvm_sequence_library #(my_transaction);
    `uvm_object_utils(my_sequence_library)
    `uvm_sequence_library_utils(my_sequence_library)

    function new(string name = "my_sequence_library");
        super.new(name);
        init_sequence_library();
    endfunction

    function void init_sequence_library();
        add_typewide_sequence(my_write_sequence::get_type());
        add_typewide_sequence(my_read_sequence::get_type());
        add_typewide_sequence(my_burst_sequence::get_type());
    endfunction
endclass
```

## Reactive Sequence (Slave)

```systemverilog
class slave_response_sequence extends uvm_sequence #(slave_transaction);
    `uvm_object_utils(slave_response_sequence)

    task body();
        forever begin
            req = slave_transaction::type_id::create("req");
            start_item(req);
            if (!req.randomize() with {
                resp_data == req.addr + 32'h100;
                resp_valid == 1;
            }) `uvm_fatal("RAND", "Randomization failed")
            finish_item(req);
        end
    endtask
endclass
```

## Sequence Start 패턴

```systemverilog
// Test에서 시퀀스 실행
task run_phase(uvm_phase phase);
    my_sequence seq;

    phase.raise_objection(this);

    // 방법 1: 기본 실행
    seq = my_sequence::type_id::create("seq");
    seq.start(env.agent.seqr);

    // 방법 2: 인자 전달
    seq.randomize() with { num_items == 100; };
    seq.start(env.agent.seqr);

    // 방법 3: 병렬 실행
    fork
        seq1.start(env.agent1.seqr);
        seq2.start(env.agent2.seqr);
    join

    phase.drop_objection(this);
endtask
```

---

## Driver-Sequence Use Models

### Unidirectional (기본)

```systemverilog
// Driver: get → drive → done
task run_phase(uvm_phase phase);
    forever begin
        seq_item_port.get_next_item(req);
        drive_to_bfm(req);           // BFM을 통해 DUT에 drive
        seq_item_port.item_done();    // 완료 알림
    end
endtask
```

### Bidirectional (응답 포함)

```systemverilog
// Driver: req에 response를 기록하고 finish_item() 후 sequence가 읽음
task run_phase(uvm_phase phase);
    forever begin
        seq_item_port.get_next_item(req);
        drive_to_bfm(req);
        // ★ req 자체에 response 기록
        req.resp_data = vif.rdata;
        req.resp_status = vif.status;
        seq_item_port.item_done();
    end
endtask

// Sequence: finish_item() 후 req에서 response 읽기
task body();
    req = my_transaction::type_id::create("req");
    start_item(req);
    req.randomize();
    finish_item(req);
    // ★ finish_item() 반환 후 req에 response가 기록되어 있음
    read_data = req.resp_data;
endtask
```

### Pipelined (다중 Outstanding)

```systemverilog
// Driver: response handler 사용
class pipelined_driver extends uvm_driver #(my_transaction);
    function new(string name, uvm_component parent);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        // ★ Pipelined: response handler 활성화
        seq_item_port.set_response_handler(this);
    endfunction

    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get_next_item(req);
            // Address phase — 즉시 다음 item 요청 가능
            drive_address_phase(req);
            seq_item_port.item_done();
        end
    endtask

    // Data phase — 별도 process에서 response 수집
    task drive_address_phase(my_transaction tr);
        fork
            begin
                wait_data_phase(tr);
                // response를 sequence에 전달
                seq_item_port.put_response(tr);
            end
        join_none
    endtask
endclass
```

---

## Late Randomization

```systemverilog
// ★ start_item() 후 randomize → finish_item()
// Sequencer 중재(arbitration) 이후에 randomize하므로 최신 상태 반영 가능
task body();
    req = my_transaction::type_id::create("req");
    start_item(req);  // sequencer 중재 대기
    // ★ 여기서 randomize — 중재 이후이므로 현재 상태 기반 constraint 가능
    if (!req.randomize() with { addr == local::target_addr; })
        `uvm_fatal("RAND", "Randomization failed")
    finish_item(req);  // driver에게 전달
endtask
```

**Late randomization 장점**: sequencer에서 중재가 완료된 후에 randomize하므로, 다른 sequence의 영향이나 DUT 상태 변화를 constraint에 반영 가능.

---

## Sequence Arbitration (6종)

Sequencer에서 여러 sequence가 동시에 실행될 때 중재 방식:

| Mode | 설명 |
|------|------|
| `SEQ_ARB_FIFO` (기본) | 선착순 (FIFO) |
| `SEQ_ARB_WEIGHTED` | priority에 비례한 가중 랜덤 |
| `SEQ_ARB_RANDOM` | 완전 랜덤 |
| `SEQ_ARB_STRICT_FIFO` | priority 높은 것 먼저, 같으면 FIFO |
| `SEQ_ARB_STRICT_RANDOM` | priority 높은 것 먼저, 같으면 랜덤 |
| `SEQ_ARB_USER` | 사용자 정의 (user_priority_arbitration 오버라이드) |

```systemverilog
// Sequencer 중재 모드 설정
env.agent.seqr.set_arbitration(SEQ_ARB_STRICT_FIFO);

// Sequence 우선순위 설정
high_prio_seq.start(seqr, null, 100);  // priority = 100 (높음)
low_prio_seq.start(seqr, null, 1);     // priority = 1 (낮음)
```

---

## Lock / Grab

### Lock — 배타적 접근 (현재 대기열 소진 후)

```systemverilog
task body();
    // ★ lock: 현재 큐의 기존 item 처리 후 배타 접근
    lock(m_sequencer);

    // 이 사이에는 다른 sequence가 개입 불가
    repeat (10) begin
        req = my_transaction::type_id::create("req");
        start_item(req);
        req.randomize();
        finish_item(req);
    end

    unlock(m_sequencer);
endtask
```

### Grab — 즉시 배타적 접근

```systemverilog
task body();
    // ★ grab: 현재 item 완료 즉시 배타 접근 (큐 무시)
    grab(m_sequencer);

    // 긴급 처리
    req = my_transaction::type_id::create("req");
    start_item(req);
    req.randomize();
    finish_item(req);

    ungrab(m_sequencer);
endtask
```

**Deadlock 주의**: lock/grab 중인 sequence 내에서 다른 sequence를 start하면 deadlock 가능. Lock 범위를 최소화할 것.

---

## Interrupt Sequence (3종)

### Grab 방식

```systemverilog
class interrupt_sequence extends uvm_sequence #(my_transaction);
    task body();
        // 인터럽트 감지 시 grab으로 즉시 선점
        wait (vif.irq);
        grab(m_sequencer);

        // 인터럽트 핸들링
        req = my_transaction::type_id::create("req");
        start_item(req);
        req.randomize() with { cmd == INT_ACK; };
        finish_item(req);

        ungrab(m_sequencer);
    endtask
endclass
```

### Priority 방식

```systemverilog
// 높은 priority로 시작 — STRICT 중재 모드에서 우선 처리
task run_phase(uvm_phase phase);
    fork
        normal_seq.start(seqr, null, 50);   // 일반 priority
        int_seq.start(seqr, null, 200);     // 높은 priority → 우선 처리
    join
endtask
```

### HW-Triggered 방식

```systemverilog
class hw_int_sequence extends uvm_sequence #(my_transaction);
    task body();
        forever begin
            // HW 인터럽트 대기
            wait (cfg.vif.irq);

            // 인터럽트 처리 시퀀스
            grab(m_sequencer);
            handle_interrupt();
            ungrab(m_sequencer);
        end
    endtask
endclass
```

---

## Sequence Layering (Translator)

상위 레벨 시퀀스를 하위 프로토콜 트랜잭션으로 변환:

```systemverilog
// 상위: AXI burst 트랜잭션
class axi_burst_item extends uvm_sequence_item;
    rand bit [31:0] start_addr;
    rand int        burst_len;
    rand bit [31:0] data[];
endclass

// Translator sequence: burst → 개별 transfer로 분해
class burst_to_transfer_seq extends uvm_sequence #(axi_transfer_item);
    `uvm_object_utils(burst_to_transfer_seq)

    uvm_sequencer #(axi_burst_item) upper_seqr;

    task body();
        axi_burst_item burst;
        forever begin
            upper_seqr.get_next_item(burst);

            // Burst를 개별 transfer로 변환
            for (int i = 0; i < burst.burst_len; i++) begin
                req = axi_transfer_item::type_id::create("req");
                start_item(req);
                req.addr = burst.start_addr + i * 4;
                req.data = burst.data[i];
                req.last = (i == burst.burst_len - 1);
                finish_item(req);
            end

            upper_seqr.item_done();
        end
    endtask
endclass
```

---

## Hierarchical Sequence Organization

```
API Sequence (최상위)
├── configure_dut_seq      — DUT 설정
├── traffic_seq            — 데이터 전송
│   ├── write_burst_seq    — Worker
│   └── read_burst_seq     — Worker
└── check_status_seq       — 상태 확인

Virtual Sequence
├── master_traffic_seq     — Master agent
├── slave_response_seq     — Slave agent
└── monitor_interrupt_seq  — Interrupt 감시
```

### API → Worker → Virtual Sequence 계층

```systemverilog
// API Sequence — 최상위, 테스트 시나리오 정의
class test_scenario_seq extends uvm_sequence;
    task body();
        configure_dut_seq cfg_seq;
        traffic_seq       traf_seq;

        // 1단계: DUT 설정
        cfg_seq = configure_dut_seq::type_id::create("cfg_seq");
        cfg_seq.start(m_sequencer);

        // 2단계: 트래픽 생성
        traf_seq = traffic_seq::type_id::create("traf_seq");
        traf_seq.start(m_sequencer);
    endtask
endclass

// Worker Sequence — 구체적 동작 수행
class write_burst_seq extends uvm_sequence #(my_transaction);
    rand int burst_len;
    rand bit [31:0] base_addr;

    task body();
        repeat (burst_len) begin
            req = my_transaction::type_id::create("req");
            start_item(req);
            req.randomize() with { addr == base_addr; write == 1; };
            finish_item(req);
            base_addr += 4;
        end
    endtask
endclass
```

---

## Sequence Configuration

Sequence body() 내에서 config_db를 통해 리소스(config object, register model 등)에 접근하는 패턴.

### config_db 접근 3가지 방식

```systemverilog
// 방법 1: m_sequencer 핸들 (가장 일반적)
// scope = sequencer 경로 (e.g. "uvm_test_top.env.agent.sequencer")
if (!uvm_config_db #(my_config)::get(m_sequencer, "", "my_config", m_cfg))
    `uvm_error("BODY", "config_db lookup failed")

// 방법 2: get_full_name() — sequence 이름 포함
// scope = sequencer 경로 + sequence 이름 → per-sequence 설정 가능
if (!uvm_config_db #(my_config)::get(null, get_full_name(), "my_config", m_cfg))
    `uvm_error("BODY", "config_db lookup failed")

// 방법 3: 임의 scope — 컴포넌트 계층과 무관한 논리적 도메인
if (!uvm_config_db #(my_config)::get(null, "MY_DOMAIN::", "my_config", m_cfg))
    `uvm_error("BODY", "config_db lookup failed")
```

### Per-Sequence 설정

방법 2를 사용하면 sequence 이름별로 다른 config 할당 가능:

```systemverilog
// env build_phase에서 — 이름 기반 config 분기
uvm_config_db #(my_config)::set(this, "agent*", "my_config", normal_cfg);
uvm_config_db #(my_config)::set(this, "agent.sequencer.error*", "my_config", error_cfg);

// test run_phase에서 — 이름이 다른 sequence 생성
normal_seq = my_seq::type_id::create("normal_seq");  // → normal_cfg
error_seq  = my_seq::type_id::create("error_seq");   // → error_cfg
```

### Register Base Sequence 패턴

Register 시퀀스의 공통 base class에서 RM 핸들을 설정하고 파생 class에서 재사용:

```systemverilog
class reg_base_seq extends uvm_sequence #(uvm_sequence_item);
    my_env_config m_cfg;
    my_reg_block  rm;

    task body();
        if (!uvm_config_db #(my_env_config)::get(null, get_full_name(), "env_config", m_cfg))
            `uvm_error("BODY", "env_config lookup failed")
        rm = m_cfg.reg_model;  // config object에서 RM 핸들 획득
    endtask
endclass

class init_seq extends reg_base_seq;
    task body();
        super.body();  // ★ 반드시 호출 — RM 핸들 설정
        rm.ctrl_reg.write(status, 32'h0, .parent(this));
    endtask
endclass
```

---

## Stimulus Generation Patterns

### Sequence Persistence

rand 필드는 start_item/finish_item 반복 간 **이전 randomize 값을 유지**한다.

```systemverilog
class mem_copy_seq extends uvm_sequence #(bus_transaction);
    `uvm_object_utils(mem_copy_seq)

    task body();
        req = bus_transaction::type_id::create("req");
        repeat (16) begin
            start_item(req);
            // ★ req.addr는 이전 반복의 randomize 결과가 남아있음
            // 새로운 randomize() 호출로 기존 값 기반 constraint 가능
            if (!req.randomize() with { addr == local::req.addr + 4; write == 1; })
                `uvm_fatal("RAND", "Randomization failed")
            finish_item(req);
            // addr 값이 4씩 증가하는 contiguous 패턴
        end
    endtask
endclass
```

**주의**: `create()`로 **새 item을 생성하면** persistence 없음. 기존 item을 **재사용**할 때만 유효.

### Sequence Polymorphism (seq_item Factory Override)

base seq_item을 derived seq_item으로 factory override하여, 동일 sequence가 다른 타입의 stimulus를 생성.

```systemverilog
// Base transaction
class base_transaction extends uvm_sequence_item;
    `uvm_object_utils(base_transaction)
    rand bit [31:0] addr;
    rand bit [31:0] data;
endclass

// Error injection transaction
class error_transaction extends base_transaction;
    `uvm_object_utils(error_transaction)
    rand bit inject_parity_error;
    constraint c_err { inject_parity_error == 1; }
endclass

// Test에서 factory override
class error_test extends my_base_test;
    function void build_phase(uvm_phase phase);
        // ★ 기존 sequence 코드 변경 없이 error transaction 생성
        base_transaction::type_id::set_type_override(error_transaction::get_type());
        super.build_phase(phase);
    endfunction
endclass
```

### Sequence Overriding (Sequence Factory Override)

sequence 자체를 factory override하여 test별 시나리오 변경.

```systemverilog
// Type override — 전체 교체
write_seq::type_id::set_type_override(burst_write_seq::get_type());

// Instance override — 특정 인스턴스만 교체
write_seq::type_id::set_inst_override(
    burst_write_seq::get_type(),
    "env.agent.seqr.write_seq"  // ★ 경로 지정
);

// ★ uvm_object에서 create 시 3번째 인자 contxt 필수
// sequence 내부에서:
sub_seq = write_seq::type_id::create("sub_seq", , get_full_name());
//                                               ↑ contxt — instance override 매칭에 필요
```

---

## get/put vs get_next_item/item_done 비교

| 항목 | get_next_item/item_done | get/put |
|------|------------------------|---------|
| Blocking | get_next_item() blocks | get() blocks |
| Response | item_done(rsp) 또는 req 필드 수정 | put(rsp) — 명시적 |
| 장점 | 표준, 널리 사용, 간단 | 명시적 response path |
| 단점 | response path 불명확 | sequencer rsp_port 필요 |
| 권장 | **기본 권장** | bidirectional/pipelined 특수 경우 |

### Bidirectional get/put

```systemverilog
class bidir_driver extends uvm_driver #(my_transaction);
    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get(req);       // blocking — request 수신
            drive_to_bfm(req);

            // ★ 필수: rsp에 req의 ID 정보 복사 — response routing에 필요
            rsp = my_transaction::type_id::create("rsp");
            rsp.copy(req);                // 또는 BFM에서 clone()
            rsp.set_id_info(req);         // ★ 필수 — sequence에게 올바른 response 전달
            rsp.resp_data = vif.rdata;

            seq_item_port.put(rsp);       // 명시적 response 전달
        end
    endtask
endclass
```

### Pipelined get/put

다중 outstanding 트랜잭션을 위한 get/put 기반 패턴. Response 처리 3가지 방식:

```systemverilog
class pipelined_get_put_driver extends uvm_driver #(my_transaction);
    task run_phase(uvm_phase phase);
        forever begin
            seq_item_port.get(req);
            fork
                begin
                    automatic my_transaction r = req;
                    drive_and_respond(r);
                end
            join_none
        end
    endtask

    task drive_and_respond(my_transaction tr);
        my_transaction rsp;
        drive_to_bfm(tr);
        rsp = my_transaction::type_id::create("rsp");
        rsp.set_id_info(tr);  // ★ 필수
        rsp.resp_data = vif.rdata;

        // 방식 1: put_response() — function (not task), async callback
        seq_item_port.put_response(rsp);

        // 방식 2: use_response_handler(1) — response handler 패턴
        // build_phase에서 seq_item_port.set_response_handler(this) 설정 필요

        // 방식 3: pipeline queue — in-flight tracking (driver 내부 queue 관리)
    endtask
endclass
```

---

## Interrupt — Parallel Processing

event 기반 병렬 HW 블록 제어 패턴.

```systemverilog
// interrupt_util class: event-based notification
class interrupt_util extends uvm_object;
    `uvm_object_utils(interrupt_util)
    event interrupt_detected;
    bit   active;

    function new(string name = "interrupt_util");
        super.new(name);
    endfunction
endclass

// Config object에 interrupt utility 배열 보유
class my_config extends uvm_object;
    interrupt_util intr_utils[4];  // 블록별 interrupt utility

    function new(string name = "my_config");
        super.new(name);
        foreach (intr_utils[i])
            intr_utils[i] = interrupt_util::type_id::create($sformatf("intr_%0d", i));
    endfunction
endclass

// 병렬 HW 블록 시작/정지 제어
class parallel_ctrl_sequence extends uvm_sequence #(my_transaction);
    my_config cfg;

    task body();
        // grab()으로 선점 후 블록별 제어
        forever begin
            @(cfg.intr_utils[0].interrupt_detected);
            grab(m_sequencer);
            // interrupt 처리: 해당 블록 정지 → 처리 → 재시작
            req = my_transaction::type_id::create("req");
            start_item(req);
            req.randomize() with { cmd == BLOCK_STOP; block_id == 0; };
            finish_item(req);
            ungrab(m_sequencer);
        end
    endtask
endclass
```

**BFM-proxy pattern**: config object가 동기화 hub 역할 — BFM이 interrupt 감지 → config의 interrupt_util event trigger → sequence가 반응.

---

## Anti-patterns

### fork/join_any + disable fork

```systemverilog
// ★ ANTI-PATTERN: disable fork로 sequence 중단
task body();
    fork
        seq1.start(seqr);
        seq2.start(seqr);
    join_any
    disable fork;  // ★ 위험 — 다른 fork도 함께 중단될 수 있음
endtask

// GOOD: 각 sequence에 완료 조건 내장
task body();
    fork
        seq1.start(seqr);  // 내부에서 자체 종료
        seq2.start(seqr);  // 내부에서 자체 종료
    join
endtask
```

### sequence.kill() / sequencer.stop_sequences()

```systemverilog
// ★ ANTI-PATTERN: 강제 종료
seq.kill();                    // sequence 강제 종료 — 정리 코드 미실행
seqr.stop_sequences();        // 모든 sequence 강제 종료

// GOOD: 정상 종료 메커니즘
class my_sequence extends uvm_sequence #(my_transaction);
    bit stop_requested;

    task body();
        while (!stop_requested) begin
            req = my_transaction::type_id::create("req");
            start_item(req);
            req.randomize();
            finish_item(req);
        end
    endtask
endclass
```

### get()/put() — Alternative Pattern

```systemverilog
// ★ ALTERNATIVE PATTERN: bidirectional/pipelined 프로토콜에서 유효
// 기본 권장: get_next_item/item_done
// get/put 적합: 명시적 response path가 필요한 경우
seq_item_port.get(req);   // blocking — get_next_item과 동일하게 block
// ... drive ...
seq_item_port.put(rsp);   // 명시적 response 전달

// 기본 권장 (대부분의 경우):
seq_item_port.get_next_item(req);
// ...
seq_item_port.item_done();
```

**get/put 사용 시점**: 위 "get/put vs get_next_item/item_done 비교" 섹션 참조
