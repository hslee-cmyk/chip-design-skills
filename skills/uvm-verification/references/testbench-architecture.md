# UVM Testbench Architecture

## 1. Dual-Top Architecture

### hdl_top / hvl_top 분리

```
hdl_top (module)                    hvl_top (module)
├── DUT instance                    ├── import uvm_pkg::*;
├── Interface instances             ├── import test_pkg::*;
├── Clock/Reset generation          └── initial run_test();
└── Signal connections
```

```systemverilog
// hdl_top.sv — 합성 가능한 HDL 코드와 interface
module hdl_top;
    logic clk, rst_n;

    // Clock generation
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Reset
    initial begin
        rst_n = 0;
        #100 rst_n = 1;
    end

    // Interface
    my_interface my_if(.clk(clk), .rst_n(rst_n));

    // DUT
    my_dut dut(
        .clk   (my_if.clk),
        .rst_n (my_if.rst_n),
        .addr  (my_if.addr),
        .data  (my_if.data),
        .valid (my_if.valid),
        .ready (my_if.ready)
    );
endmodule

// hvl_top.sv — UVM 테스트벤치 시작점
module hvl_top;
    import uvm_pkg::*;
    import my_test_pkg::*;

    initial begin
        // config_db로 interface 전달
        uvm_config_db#(virtual my_interface)::set(null, "uvm_test_top.*", "vif",
                                                   hdl_top.my_if);
        run_test();
    end
endmodule
```

**와일드카드 import 주의**: `import uvm_pkg::*`는 허용되지만, 다수 패키지를 `*`로 import하면 이름 충돌 가능. 필요한 항목만 명시적 import 권장.

### config_db BFM 등록 패턴

BFM interface를 config_db에 등록하는 위치는 hdl_top과 hvl_top 양쪽 가능. **hdl_top 쪽 등록 권장** — BFM과 동일 모듈에서 상대 경로 사용 가능.

```systemverilog
// hdl_top에서 BFM 등록 (권장 — BFM과 지역화)
module hdl_top;
    // ... DUT, BFM 인스턴스 ...
    wb_m_bus_driver_bfm  wb_drv_bfm(wb_bus_if);
    wb_bus_monitor_bfm   wb_mon_bfm(wb_bus_if);

    initial begin
        // ★ hdl_top은 uvm_config_db만 명시적 import (합성 도메인 오염 방지)
        import uvm_pkg::uvm_config_db;
        uvm_config_db #(virtual wb_m_bus_driver_bfm)::set(null, "uvm_test_top", "WB_DRV_BFM", wb_drv_bfm);
        uvm_config_db #(virtual wb_bus_monitor_bfm)::set(null, "uvm_test_top", "WB_MON_BFM", wb_mon_bfm);
    end
endmodule
```

```systemverilog
// 대안: hvl_top에서 cross-domain 계층 경로로 등록
module hvl_top;
    import uvm_pkg::run_test;   // ★ 필요한 항목만 명시적 import
    import tests_pkg::*;

    initial begin
        import uvm_pkg::uvm_config_db;
        // ★ 전체 계층 경로로 hdl_top 내 BFM 참조
        uvm_config_db #(virtual wb_m_bus_driver_bfm)::set(null, "uvm_test_top", "WB_DRV_BFM",
                                                           top_hdl.wb_drv_bfm);
        run_test();
    end
endmodule
```

### `%m` String Formatter

다수 BFM 인스턴스가 있을 때 `%m`으로 고유한 config_db 키 자동 생성:

```systemverilog
// %m은 모듈 인스턴스의 전체 계층 경로로 치환 → 이름 충돌 방지
uvm_config_db #(virtual my_bfm)::set(null, "uvm_test_top",
    $sformatf("%m.bfm"), my_bfm_inst);
```

★ 같은 BFM 모듈이 여러 번 인스턴스화될 때, `%m`이 각 인스턴스를 고유하게 식별.

### Dual-Top 시뮬레이션 실행

```bash
# vsim: 두 top 모듈을 모두 지정
vsim -c top_hvl top_hdl +UVM_TESTNAME=my_test -do "run -all; exit"
```

---

## 2. DUT Connection 패턴 3종

### 2.1 Signal Container (시뮬레이션 전용)

Interface가 DUT 포트 신호를 직접 묶는 방식.

```systemverilog
interface my_interface(input logic clk, rst_n);
    logic [31:0] addr;
    logic [31:0] data;
    logic        valid;
    logic        ready;
    logic        write;

    // Clocking block (driver용)
    clocking drv_cb @(posedge clk);
        output addr, data, valid, write;
        input  ready;
    endclocking

    // Clocking block (monitor용)
    clocking mon_cb @(posedge clk);
        input addr, data, valid, ready, write;
    endclocking
endinterface
```

- 장점: 단순, 빠른 구현
- 단점: Emulation 불가, 신호 추가 시 interface 수정 필요

### 2.2 BFM-Method (권장, Emulation-Ready)

Interface 내에 task/function으로 프로토콜 동작을 캡슐화.

```systemverilog
interface my_bfm_interface(input logic clk, rst_n);
    logic [31:0] addr, wdata, rdata;
    logic        valid, ready, write;

    // Driver BFM task
    task drive_write(input bit [31:0] a, input bit [31:0] d);
        @(posedge clk);
        addr  <= a;
        wdata <= d;
        write <= 1;
        valid <= 1;
        @(posedge clk);
        while (!ready) @(posedge clk);
        valid <= 0;
    endtask

    task drive_read(input bit [31:0] a, output bit [31:0] d);
        @(posedge clk);
        addr  <= a;
        write <= 0;
        valid <= 1;
        @(posedge clk);
        while (!ready) @(posedge clk);
        d = rdata;
        valid <= 0;
    endtask

    // Monitor BFM: 트랜잭션 감지
    task wait_for_transfer(output bit [31:0] a, output bit [31:0] d, output bit w);
        @(posedge clk);
        while (!(valid && ready)) @(posedge clk);
        a = addr;
        d = write ? wdata : rdata;
        w = write;
    endtask
endinterface
```

- 장점: pin-level 동작 캡슐화, Emulation-ready
- 단점: interface가 커질 수 있음

### 2.3 Abstract-Concrete Class (파라미터 불필요)

파라미터화된 DUT에 대해 abstract class로 인터페이스 정의:

```systemverilog
// Abstract class — 파라미터 독립
virtual class my_driver_bfm;
    pure virtual task drive(input bit [31:0] addr, input bit [31:0] data);
    pure virtual task read(input bit [31:0] addr, output bit [31:0] data);
endclass

// Concrete class — 파라미터화된 구현
class my_driver_bfm_impl #(int WIDTH = 32) extends my_driver_bfm;
    virtual my_param_if #(WIDTH) vif;
    // ... 구현
endclass
```

- 장점: UVM 컴포넌트가 파라미터에 의존하지 않음
- 단점: 구현 복잡도 증가

---

## 3. Parameter Handling

### tb_params_pkg + Namespace Class

```systemverilog
package tb_params_pkg;
    class tb_params;
        static int DATA_WIDTH = 32;
        static int ADDR_WIDTH = 16;
        static int NUM_SLAVES = 4;
    endclass
endpackage
```

### Max-width Sequence Item

파라미터에 의존하지 않는 sequence item 설계:

```systemverilog
class my_transaction extends uvm_sequence_item;
    `uvm_object_utils(my_transaction)

    // 최대 폭으로 선언 — 실제 폭은 runtime에 결정
    rand bit [63:0] addr;  // max width
    rand bit [63:0] data;  // max width

    int actual_addr_width = 32;  // config에서 설정
    int actual_data_width = 32;

    constraint c_width {
        addr < (1 << actual_addr_width);
        data < (1 << actual_data_width);
    }
endclass
```

---

## 4. Block-Level Testbench

```
uvm_test
└── block_env
    ├── agent (active)
    │   ├── sequencer
    │   ├── driver
    │   └── monitor
    ├── scoreboard
    ├── coverage (uvm_subscriber)
    └── reg_model (optional)
```

단일 DUT, 단일/소수 인터페이스. 가장 기본적인 구조.

---

## 5. Integration-Level Testbench (Vertical Reuse)

### 5.1 구조 개요

```
uvm_test (pss_test_base)
└── soc_env (pss_env)
    ├── block_env_A (spi_env — block 재사용)
    │   ├── apb_agent (PASSIVE — 브릿지 후단 관측)
    │   ├── spi_agent, scoreboard, coverage
    │   └── reg_predictor (block reg_block 참조)
    ├── block_env_B (gpio_env — block 재사용)
    │   ├── apb_agent (PASSIVE)
    │   ├── gpio_agents, scoreboard, coverage
    │   └── reg_predictor
    ├── ahb_agent (ACTIVE — 최상위 버스 구동)
    └── reg_predictor (subsystem reg_block, AHB monitor 연결)
```

- Block env를 그대로 인스턴스화하여 재사용
- SoC-level 추가 검증 컴포넌트 추가
- Virtual sequence로 다중 agent 조율

### 5.2 Config 중첩 전파 (Russian Doll 확장)

Subsystem config가 block-level config를 포함. Test에서 전체를 생성하여 nesting.

```systemverilog
class pss_env_config extends uvm_object;
    `uvm_object_utils(pss_env_config)

    // Sub-env configs (block-level 재사용)
    spi_env_config  m_spi_env_cfg;
    gpio_env_config m_gpio_env_cfg;
    // Subsystem-level agent config
    ahb_agent_config m_ahb_agent_cfg;
    // Subsystem register model
    pss_reg_block pss_rb;
    // Interrupt utility (공유)
    intr_util ICPIT;
    // ...
endclass
```

```systemverilog
// Test의 build_phase에서:
// 1. Sub-env config 생성 및 block reg_block 참조 전달
m_spi_env_cfg = spi_env_config::type_id::create("m_spi_env_cfg");
m_spi_env_cfg.spi_rb = pss_rb.spi_rb;  // ★ subsystem reg_block의 sub-block 참조

// 2. Sub-env 내부 agent config 생성 및 nesting
m_spi_apb_agent_cfg = apb_agent_config::type_id::create("m_spi_apb_agent_cfg");
m_spi_apb_agent_cfg.active = UVM_PASSIVE;  // ★ Active→Passive 전환
m_spi_env_cfg.m_apb_agent_cfg = m_spi_apb_agent_cfg;

// 3. Subsystem config에 nesting
m_env_cfg.m_spi_env_cfg = m_spi_env_cfg;
```

### 5.3 Active→Passive 전환

Block level에서 ACTIVE였던 버스 agent를 subsystem에서 PASSIVE로 전환.
이유: 버스 브릿지(AHB→APB)가 DUT 내부에 존재하여 직접 구동 불필요.

```
Block-Level:   test → APB agent (ACTIVE) → DUT
Subsystem:     test → AHB agent (ACTIVE) → AHB-APB Bridge (DUT 내부)
                       APB agent (PASSIVE, monitor only) ← bind/prober로 관측
```

```
★ Block-level env 코드를 수정하지 않고, config만 변경하여 agent 모드를 전환
★ 이것이 "vertical reuse"의 핵심: env 코드 수정 없이 config로 행동 변경
```

### 5.4 Register Model 합성 (add_submap)

Subsystem reg_block이 block-level reg_block을 `add_submap()`으로 포함.

```systemverilog
class pss_reg_block extends uvm_reg_block;
    `uvm_object_utils(pss_reg_block)

    rand spi_reg_block  spi_rb;
    rand gpio_reg_block gpio_rb;
    uvm_reg_map pss_map;

    virtual function void build();
        // Sub-block 생성 및 configure
        spi_rb = spi_reg_block::type_id::create("spi_rb");
        spi_rb.configure(this);  // ★ parent = this
        spi_rb.build();

        gpio_rb = gpio_reg_block::type_id::create("gpio_rb");
        gpio_rb.configure(this);
        gpio_rb.build();

        // Subsystem map에 sub-block map 추가 (주소 오프셋)
        pss_map = create_map("pss_map", 'h0, 4, UVM_LITTLE_ENDIAN, 1);
        default_map = pss_map;
        pss_map.add_submap(spi_rb.spi_reg_block_map, 'h0);     // SPI: 0x000
        pss_map.add_submap(gpio_rb.gpio_reg_block_map, 'h0100); // GPIO: 0x100

        lock_model();
    endfunction
endclass
```

### 5.5 get_parent() 가드 패턴

Block-level env의 connect_phase에서 `get_parent() == null` 검사로 최상위 여부 판별.

```systemverilog
function void block_env::connect_phase(uvm_phase phase);
    // ★ reg_block이 최상위일 때만 sequencer/predictor 연결
    if (m_cfg.block_rb.get_parent() == null) begin
        m_cfg.block_rb.block_map.set_sequencer(m_agent.m_sequencer, m_adapter);
        // predictor 설정...
        m_cfg.block_rb.block_map.set_auto_predict(0);
        m_agent.ap.connect(m_predictor.bus_in);
    end
    // ★ subsystem에서는 get_parent() != null → 상위 env가 predictor 설정
endfunction
```

```
★ 이 패턴 덕분에 block env 코드를 한 줄도 수정하지 않고 subsystem에 재사용 가능
★ Subsystem env에서는 AHB agent 기반으로 별도 predictor를 설정
```

### 5.6 Bind + Prober 패턴

DUT 내부 버스(APB)를 관측하기 위해 SystemVerilog `bind`로 prober 모듈을 삽입.

```systemverilog
// binder.sv — DUT 내부에 prober 바인딩
module binder();
    bind pss  // ★ DUT 모듈 이름
    apb_prober probe (
        .PCLK(HCLK),
        .PRESETn(HRESETn),
        .PADDR(PADDR),
        .SPI_PRDATA(SPI_PRDATA),
        .GPIO_PRDATA(GPIO_PRDATA),
        .PWDATA(PWDATA),
        .PSEL(PSEL),
        .PENABLE(PENABLE),
        .PWRITE(PWRITE),
        .SPI_PREADY(SPI_PREADY),
        .GPIO_PREADY(GPIO_PREADY)
    );
endmodule

// apb_prober.sv — PSEL 기반 MUX로 신호 합성
module apb_prober(input PCLK, PRESETn, ...);
    // PRDATA: PSEL에 따라 해당 slave의 PRDATA 선택
    assign APB.PRDATA = ({32{PSEL[0]}} & SPI_PRDATA) |
                        ({32{PSEL[1]}} & GPIO_PRDATA);
    // PREADY: 동일하게 MUX
    assign APB.PREADY = (PSEL[0] & SPI_PREADY) |
                        (PSEL[1] & GPIO_PREADY);
endmodule
```

```
★ Prober는 DUT 내부 신호를 BFM interface에 연결하여 passive monitor가 관측 가능하게 함
★ Block-level에서는 직접 연결, Subsystem에서는 bind+prober로 연결 — env 코드 변경 없음
```

### 5.7 Sequencer 핸들 전파

Test에서 중첩 env 내부의 sequencer 핸들을 virtual sequence에 전달.

```systemverilog
// Test
function void assign_sequencers(pss_test_seq_base seq_);
    seq_.ahb = m_env.m_ahb_agent.m_sequencer;
    // ★ 중첩 env 내부 sequencer에 직접 접근
    seq_.spi = m_env.m_spi_env.m_spi_agent.m_sequencer;
    seq_.gpi = m_env.m_gpio_env.m_GPI_agent.m_sequencer;
    seq_.m_cfg = m_env_cfg;
endfunction

// Virtual Sequence Base
class pss_test_seq_base extends uvm_sequence #(uvm_sequence_item);
    ahb_sequencer  ahb;
    spi_sequencer  spi;
    gpio_sequencer gpi;
    pss_env_config m_cfg;
    // ...
endclass
```

### 5.8 Interrupt Utility 공유

Interrupt utility 객체를 subsystem config과 sub-env config에 공유하여 다수 블록의 인터럽트를 통합 관리.

```systemverilog
// Test의 build_phase:
ICPIT = intr_util::type_id::create("ICPIT");
ICPIT.set_bfm(temp_intr_bfm);  // BFM 바인딩
m_env_cfg.ICPIT = ICPIT;
m_spi_env_cfg.INTR = ICPIT;    // ★ sub-env에도 동일 객체 공유

// Virtual Sequence에서 인터럽트 대기:
m_cfg.wait_for_interrupt();     // → ICPIT.wait_for_interrupt()
```

---

## 6. "Russian Doll" Config 패턴

### Config Object 중첩

```systemverilog
class agent_config extends uvm_object;
    `uvm_object_utils(agent_config)

    uvm_active_passive_enum is_active = UVM_ACTIVE;
    virtual my_interface     vif;

    function new(string name = "agent_config");
        super.new(name);
    endfunction
endclass

class env_config extends uvm_object;
    `uvm_object_utils(env_config)

    // 조건부 빌드 플래그
    bit has_scoreboard  = 1;
    bit has_coverage    = 1;
    bit has_reg_model   = 0;

    // 중첩된 agent config
    agent_config m_agent_cfg;

    // rand 지원 (테스트에서 randomize 가능)
    rand int num_transactions;
    constraint c_txn { num_transactions inside {[100:1000]}; }

    function new(string name = "env_config");
        super.new(name);
        m_agent_cfg = agent_config::type_id::create("m_agent_cfg");
    endfunction
endclass
```

### has_* 플래그로 조건부 빌드

```systemverilog
class my_env extends uvm_env;
    env_config   cfg;
    my_agent     agent;
    my_scoreboard scbd;
    my_coverage   cov;

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        if (!uvm_config_db#(env_config)::get(this, "", "env_cfg", cfg))
            `uvm_fatal("NOCFG", "env_config not found")

        agent = my_agent::type_id::create("agent", this);

        // 조건부 생성
        if (cfg.has_scoreboard)
            scbd = my_scoreboard::type_id::create("scbd", this);
        if (cfg.has_coverage)
            cov = my_coverage::type_id::create("cov", this);
    endfunction
endclass
```

### Config DB 권장 패턴

```systemverilog
// ★ 1 set/get per config object (개별 필드가 아닌 config object 단위)
// GOOD: config object 전체를 한번에 set
uvm_config_db#(env_config)::set(this, "env", "env_cfg", m_env_cfg);

// BAD: 개별 필드를 각각 set
// uvm_config_db#(bit)::set(this, "env", "has_scoreboard", 1);
// uvm_config_db#(bit)::set(this, "env", "has_coverage", 1);

// ★ 경로: "uvm_test_top" 사용 (null 대신)
uvm_config_db#(env_config)::set(null, "uvm_test_top.env", "env_cfg", m_env_cfg);
```

### Config DB 우선순위 규칙

| 상황 | 우선순위 |
|------|----------|
| Build phase 중 다른 계층에서 set() | **상위 계층**이 하위 계층보다 우선 |
| 동일 context에서 여러 번 set() | **나중** set()이 이전 set()보다 우선 |
| Build phase 이후 set() | **나중** set()이 이전 set()보다 우선 |

★ Scope 형성: `{cntxt.get_full_name(), ".", inst_name}`
★ 디버깅 시 `+UVM_CONFIG_DB_TRACE`로 set/get 추적 가능

### create() 네이밍 규칙

Factory create() 시 name 인자는 로컬 핸들 이름과 일치시킨다:

```systemverilog
// GOOD: 핸들 이름 = create name 일치
m_env   = my_env::type_id::create("m_env", this);
m_agent = my_agent::type_id::create("m_agent", this);

// BAD: 이름 불일치 (토폴로지 출력 시 혼란)
m_env   = my_env::type_id::create("env_inst", this);
```

★ `print_topology()` 출력에서 인스턴스 이름이 핸들 이름과 일치하여 디버깅 용이.

### Virtual Interface 전달 원칙

Driver/Monitor는 config_db에서 **직접** VIF를 가져오지 않고, **config object를 통해서만** 받는다:

```systemverilog
// GOOD: config object에서 VIF 획득 (권장)
function void my_driver::build_phase(uvm_phase phase);
    if (!uvm_config_db#(agent_config)::get(this, "", "agent_cfg", m_cfg))
        `uvm_fatal("NOCFG", "agent_config not found")
    vif = m_cfg.vif;  // ★ config object의 vif 필드 사용
endfunction

// BAD: Driver에서 직접 config_db get (재사용성 저하)
// uvm_config_db#(virtual my_if)::get(this, "", "vif", vif)
```

★ Test → config_db → config object → sub-component 순서로 VIF가 전파됨.
★ Config object 경유 시 Test에서 VIF 할당을 완전히 제어 가능.

---

## 7. Factory Override

### Type Override

```systemverilog
// test에서 — 전체 타입 교체
function void build_phase(uvm_phase phase);
    super.build_phase(phase);

    // my_driver 대신 error_driver 사용
    set_type_override_by_type(my_driver::get_type(), error_driver::get_type());

    // my_transaction 대신 error_transaction 사용
    set_type_override_by_type(my_transaction::get_type(), error_transaction::get_type());
endfunction
```

### Instance Override

```systemverilog
// 특정 인스턴스만 교체
set_inst_override_by_type(
    "env.agent.drv",           // 대상 인스턴스 경로
    my_driver::get_type(),     // 원래 타입
    slow_driver::get_type()    // 교체 타입
);
```

### 커맨드라인 Override

```bash
+uvm_set_type_override=my_driver,error_driver
+uvm_set_inst_override=my_driver,slow_driver,uvm_test_top.env.agent.drv
```

---

## 8. End of Test / Objection

### 기본 패턴

```systemverilog
// ★ Objection은 test 또는 virtual sequence에서만 raise/drop
class my_test extends uvm_test;
    task run_phase(uvm_phase phase);
        my_virtual_sequence vseq;

        phase.raise_objection(this, "Starting test");

        vseq = my_virtual_sequence::type_id::create("vseq");
        vseq.start(null);  // null sequencer (virtual sequence)

        phase.drop_objection(this, "Test complete");
    endtask
endclass
```

### phase_ready_to_end 패턴

```systemverilog
// Drain time — objection drop 후 추가 대기
class my_env extends uvm_env;
    function void phase_ready_to_end(uvm_phase phase);
        if (phase.get_name() == "run") begin
            phase.raise_objection(this, "Drain time");
            fork begin
                #1000;  // drain time
                phase.drop_objection(this, "Drain complete");
            end join_none
        end
    endfunction
endclass
```

### Anti-patterns

| Anti-pattern | 문제 |
|-------------|------|
| Driver/Monitor에서 objection | 종료 시점 제어 어려움, 무한 loop 위험 |
| Objection callback 사용 | 복잡한 의존성, 디버깅 어려움 |
| 여러 컴포넌트에서 raise/drop | 누락/불일치로 hang 발생 |

---

## 9. Macro 권고 테이블

| Macro | 권고 | 이유 |
|-------|------|------|
| `uvm_component_utils` | **항상 사용** | Factory 등록 필수 |
| `uvm_object_utils` | **항상 사용** | Factory 등록 필수 |
| `uvm_field_*` | **금지** | 성능 저하, 디버깅 어려움, 예측 불가능한 동작 |
| `uvm_do_*` | **금지** | 흐름 제어 숨김, Late randomization 불가, 디버깅 어려움 |
| `uvm_info/warning/error/fatal` | **항상 사용** | 표준 메시지 출력 |
| `uvm_declare_p_sequencer` | **사용 가능** | Virtual sequence에서 필요 시 (대안: config 방식) |

### uvm_field_* 대체

```systemverilog
// BAD: uvm_field_* 매크로
`uvm_field_int(addr, UVM_ALL_ON)
`uvm_field_int(data, UVM_ALL_ON)

// GOOD: 직접 구현
function void do_copy(uvm_object rhs);
    my_transaction rhs_;
    super.do_copy(rhs);
    $cast(rhs_, rhs);
    this.addr = rhs_.addr;
    this.data = rhs_.data;
endfunction

function bit do_compare(uvm_object rhs, uvm_comparer comparer);
    my_transaction rhs_;
    if (!$cast(rhs_, rhs)) return 0;
    return (super.do_compare(rhs, comparer) &&
            this.addr == rhs_.addr &&
            this.data == rhs_.data);
endfunction

function string convert2string();
    return $sformatf("addr=0x%08h data=0x%08h", addr, data);
endfunction
```

### uvm_do_* 대체

```systemverilog
// BAD: uvm_do 매크로
`uvm_do_with(req, { addr == target_addr; })

// GOOD: 수동 제어 (Late Randomization)
req = my_transaction::type_id::create("req");
start_item(req);
if (!req.randomize() with { addr == target_addr; })
    `uvm_fatal("RAND", "Randomization failed")
finish_item(req);
```

---

## 10. Package Organization

### Package 계층

```
agent_pkg        — transaction, sequence, driver, monitor, agent, agent_config
  ↓ (import)
env_pkg          — env, env_config, scoreboard, predictor, coverage subscriber
  ↓ (import)
test_base_pkg    — base_test, virtual sequences
  ↓ (import)
test_pkg         — 개별 test classes
```

### 구성 규칙

```
★ 1 class = 1 file (재사용성, 가독성)
★ 각 파일은 정확히 1개의 package에만 `include
★ $unit scope에 코드 금지 — 반드시 package 안에서 정의
★ package 내 `include 순서: base class → derived class (의존성 순서)
```

### Package 작성 패턴

```systemverilog
package my_agent_pkg;
    import uvm_pkg::*;
    `include "uvm_macros.svh"

    // 의존성 순서대로 include
    `include "my_transaction.svh"
    `include "my_sequence.svh"
    `include "my_driver.svh"
    `include "my_monitor.svh"
    `include "my_agent_config.svh"
    `include "my_agent.svh"
endpackage
```

### import vs `include

| 항목 | `include | import |
|------|----------|--------|
| 동작 | 텍스트 삽입 (전처리) | 이름 접근 허용 (컴파일) |
| 사용 | package 내부에서 .svh 파일 포함 | 다른 package의 타입 참조 |
| 주의 | 같은 파일을 2개 package에 include 금지 | `import pkg::*`는 사용한 이름만 가져옴 |

```systemverilog
// ★ 같은 파일을 두 package에 include하면 별개의 타입이 됨 — 컴파일 에러 유발
// BAD:
package pkg_a; `include "my_tr.svh" endpackage
package pkg_b; `include "my_tr.svh" endpackage  // my_tr는 pkg_a::my_tr과 다른 타입!

// GOOD: 한 곳에서 include, 다른 곳에서 import
package pkg_a; `include "my_tr.svh" endpackage
package pkg_b; import pkg_a::my_tr;  endpackage
```

### 디렉토리 구조 (권장)

```
project/
├── rtl/                    # DUT 소스
├── tb/
│   ├── my_agent/
│   │   ├── my_agent_pkg.sv
│   │   ├── my_transaction.svh
│   │   ├── my_sequence.svh
│   │   ├── my_driver.svh
│   │   ├── my_monitor.svh
│   │   ├── my_agent_config.svh
│   │   └── my_agent.svh
│   ├── env/
│   │   ├── my_env_pkg.sv
│   │   ├── my_env.svh
│   │   ├── my_env_config.svh
│   │   └── my_scoreboard.svh
│   ├── tests/
│   │   ├── my_test_pkg.sv
│   │   └── my_test.svh
│   └── top/
│       ├── hdl_top.sv
│       └── hvl_top.sv
└── sim/
    └── Makefile
```

### Parameterized UVC

파라미터화된 agent를 재사용할 때, package가 파라미터를 가질 수 없으므로 대안 사용:

```systemverilog
// 방법 1: tb_params_pkg (§3 참조)
// 방법 2: Max-width + runtime config (§3 참조)
// 방법 3: `define로 package 생성 (비권장 — 이름 충돌 위험)
```
