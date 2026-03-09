# UVM RAL (Register Abstraction Layer) Guide

## 1. RAL 개요

### 계층 구조

```
uvm_reg_block (최상위 또는 중첩 블록)
├── uvm_reg_map (주소 맵, 다중 가능)
├── uvm_reg (레지스터)
│   └── uvm_reg_field (필드 — RAL의 최소 단위)
├── uvm_mem (메모리)
└── uvm_reg_block (하위 블록 — 계층 구성)
```

### 전체 흐름

```
[Register Model 정의] → [Adapter 구현] → [Testbench 연결]
    │                       │                  │
    ▼                       ▼                  ▼
  uvm_reg_block        reg2bus()          predictor 연결
  uvm_reg              bus2reg()          monitor.ap → predictor
  uvm_reg_field                           set_auto_predict(0)
    │
    ▼
  [lock_model() 호출] → [Stimulus/Check 사용]
                            │
                            ▼
                        read()/write()/mirror()/update()
```

---

## 2. Register Model 정의

### uvm_reg_field.configure() 파라미터

```systemverilog
class ctrl_reg extends uvm_reg;
    `uvm_object_utils(ctrl_reg)

    rand uvm_reg_field enable;
    rand uvm_reg_field mode;
    rand uvm_reg_field status;  // RO field — rand 불필요하지만 관례

    function new(string name = "ctrl_reg");
        super.new(name, 32, UVM_NO_COVERAGE);  // 32-bit, no built-in coverage
    endfunction

    virtual function void build();
        enable = uvm_reg_field::type_id::create("enable");
        mode   = uvm_reg_field::type_id::create("mode");
        status = uvm_reg_field::type_id::create("status");

        //              parent, size, lsb, access,  volatile, reset, has_reset, is_rand, individually_accessible
        enable.configure(this,  1,    0,   "RW",    0,        0,     1,         1,       0);
        mode.configure  (this,  2,    1,   "RW",    0,        0,     1,         1,       0);
        status.configure(this,  4,    8,   "RO",    1,        0,     1,         0,       0);
    endfunction
endclass
```

### Access Policy 종류

| Policy | 설명 |
|--------|------|
| `RW` | Read-Write |
| `RO` | Read-Only (write 무시) |
| `WO` | Write-Only (read 시 0) |
| `W1C` | Write-1-to-Clear |
| `RC` | Read-to-Clear |
| `WS` | Write-to-Set |
| `RS` | Read-to-Set |
| `W1S` | Write-1-to-Set |
| `W0C` | Write-0-to-Clear |

### Register Block 정의

```systemverilog
class my_reg_block extends uvm_reg_block;
    `uvm_object_utils(my_reg_block)

    rand ctrl_reg    ctrl;
    rand data_reg    data;
    uvm_reg_map      default_map;

    function new(string name = "my_reg_block");
        super.new(name, UVM_NO_COVERAGE);
    endfunction

    virtual function void build();
        ctrl = ctrl_reg::type_id::create("ctrl");
        ctrl.configure(this, null, "");
        ctrl.build();

        data = data_reg::type_id::create("data");
        data.configure(this, null, "");
        data.build();

        // Address map 생성
        default_map = create_map("default_map",
            'h0,    // base address
            4,      // bus width (bytes)
            UVM_LITTLE_ENDIAN
        );

        default_map.add_reg(ctrl, 'h00, "RW");
        default_map.add_reg(data, 'h04, "RW");

        lock_model();  // ★ 필수 — 모델 변경 금지
    endfunction
endclass
```

**`lock_model()` 필수**: build() 마지막에 호출하여 모델을 확정. 이후 레지스터/맵 추가 불가.

---

## 3. Complex Address Maps

### 다중 Address Map

하나의 register block에 여러 bus interface가 있을 때:

```systemverilog
virtual function void build();
    // APB map
    apb_map = create_map("apb_map", 'h0, 4, UVM_LITTLE_ENDIAN);
    apb_map.add_reg(ctrl, 'h00, "RW");
    apb_map.add_reg(data, 'h04, "RW");

    // AHB map (다른 주소 할당 가능)
    ahb_map = create_map("ahb_map", 'h0, 4, UVM_LITTLE_ENDIAN);
    ahb_map.add_reg(ctrl, 'h100, "RW");
    ahb_map.add_reg(data, 'h104, "RW");

    lock_model();
endfunction
```

### add_submap()

```systemverilog
// 상위 블록에서 하위 블록의 map을 특정 base address에 배치
soc_map.add_submap(uart_block.default_map, 'h4000_0000);
soc_map.add_submap(spi_block.default_map,  'h4001_0000);
```

### Dynamic Address Map (런타임 재구성)

Security 모드, 호스트 전환 등으로 런타임에 맵을 변경해야 할 때:

```systemverilog
// 레지스터/메모리 숨기기 (security 모드)
function void enter_secure_mode();
    unlock_model();
    AHB_map.unregister(secret_reg);      // 맵에서 제거
    AHB_map.unregister(secret_mem);
    lock_model();
endfunction

// 복원
function void exit_secure_mode();
    unlock_model();
    AHB_map.add_reg(secret_reg, 'h0010, "RW");
    AHB_map.add_mem(secret_mem, 'h1_0000, "RW");
    lock_model();
endfunction

// 맵 전체 교체 (호스트 전환)
function void remap_for_host_B();
    unlock_model();
    unregister(AHB_map);                 // 맵 자체 제거
    AHB_map = null;
    AHB_map = create_map("AHB_map", 'h0, 4, UVM_LITTLE_ENDIAN, 1);
    AHB_map.add_reg(ctrl, 'h2000_0000, "RW");  // 새 주소
    // ... 나머지 레지스터/메모리 등록
    lock_model();
endfunction
```

> **주의**: `unlock_model()` 후 반드시 `lock_model()`으로 마감. Predictor/adapter 재연결 필요 시 connect_phase 로직도 갱신.

---

## 4. Register Adapter

Adapter는 RAL의 generic 트랜잭션(`uvm_reg_bus_op`)을 프로토콜-specific 트랜잭션으로 변환.

### APB Adapter 예제

```systemverilog
class apb_reg_adapter extends uvm_reg_adapter;
    `uvm_object_utils(apb_reg_adapter)

    function new(string name = "apb_reg_adapter");
        super.new(name);

        // ★ 중요 설정
        supports_byte_enable = 0;   // APB는 byte enable 미지원
        provides_responses   = 0;   // driver가 별도 response 미전송
    endfunction

    virtual function uvm_sequence_item reg2bus(const ref uvm_reg_bus_op rw);
        apb_transaction tr = apb_transaction::type_id::create("tr");
        tr.addr  = rw.addr;
        tr.data  = rw.data;
        tr.write = (rw.kind == UVM_WRITE);
        return tr;
    endfunction

    virtual function void bus2reg(uvm_sequence_item bus_item, ref uvm_reg_bus_op rw);
        apb_transaction tr;
        if (!$cast(tr, bus_item))
            `uvm_fatal("CAST", "Failed to cast bus_item to apb_transaction")
        rw.addr   = tr.addr;
        rw.data   = tr.data;
        rw.kind   = tr.write ? UVM_WRITE : UVM_READ;
        rw.status = UVM_IS_OK;
    endfunction
endclass
```

### Adapter 설정 플래그

| 플래그 | 설명 |
|--------|------|
| `supports_byte_enable` | 프로토콜이 byte enable을 지원하면 1 |
| `provides_responses` | driver가 별도 response item을 전송하면 1 |

---

## 5. Testbench Integration

### Explicit Prediction (권장)

```systemverilog
class my_env extends uvm_env;
    my_reg_block       reg_model;
    apb_reg_adapter    adapter;
    uvm_reg_predictor #(apb_transaction) predictor;
    my_agent           agent;

    virtual function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        reg_model = my_reg_block::type_id::create("reg_model");
        reg_model.build();

        adapter   = apb_reg_adapter::type_id::create("adapter");
        predictor = uvm_reg_predictor#(apb_transaction)::type_id::create("predictor", this);
        agent     = my_agent::type_id::create("agent", this);
    endfunction

    virtual function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // ★ Explicit prediction 설정
        reg_model.default_map.set_auto_predict(0);

        // Sequencer 연결 (RAL이 sequence를 실행할 sequencer)
        reg_model.default_map.set_sequencer(agent.seqr, adapter);

        // Predictor 연결
        predictor.map     = reg_model.default_map;
        predictor.adapter = adapter;
        agent.mon.ap.connect(predictor.bus_in);  // monitor → predictor
    endfunction
endclass
```

### Three Prediction Modes

| Mode | set_auto_predict() | 특징 |
|------|-------------------|------|
| **Auto** | 1 | write()/read() 호출 즉시 mirror 업데이트. 간단하지만 실제 bus 동작 미반영 |
| **Explicit** (권장) | 0 | monitor가 bus 트랜잭션을 관찰 → predictor가 mirror 업데이트 |
| **Passive** | 0 | Agent가 passive (sequencer 없음). monitor만으로 prediction |

**Explicit 권장 이유**: 실제 bus에 전달된 트랜잭션을 기반으로 prediction → 프로토콜 에러, 중재 실패 등 감지 가능

---

## 6. Quirky Registers

### W1C (Write-1-to-Clear)

```systemverilog
// W1C 필드: write 1로 해당 비트 클리어
status.configure(this, 4, 0, "W1C", 1, 4'hF, 1, 0, 0);

// 사용: 특정 비트만 클리어
reg_model.status_reg.write(status, .value(4'b0010));  // bit 1만 클리어
```

### RC (Read-to-Clear)

```systemverilog
// RC 필드: read 시 자동 클리어
int_status.configure(this, 8, 0, "RC", 1, 0, 1, 0, 0);
```

### Counter Register

카운터처럼 HW가 독립적으로 값을 변경하는 레지스터:
- `volatile = 1` 설정
- mirror와 실제 값이 다를 수 있음
- `read()` 후 mirror 갱신으로 현재 값 확인

### Aliased Register

동일 레지스터가 다른 주소/조건에서 다른 동작:
- DLAB 비트에 따라 같은 주소가 다른 레지스터로 매핑 (UART LCR 예)

### FIFO Register

```systemverilog
// FIFO 레지스터: 같은 주소에 반복 접근 시 다른 데이터
// uvm_mem로 모델링하거나 custom register 구현
```

### uvm_mem (Memory Model)

메모리 영역 모델링. 레지스터와 달리 상태를 저장하지 않음 (DUT HW 메모리가 실제 저장).

```systemverilog
// 정의 및 등록
my_mem = uvm_mem::type_id::create("my_mem");
my_mem.configure(this, 1024, 32);  // 1024 entries × 32-bit
default_map.add_mem(my_mem, 'h1000);
```

#### 접근 메서드

```systemverilog
uvm_status_e   status;
uvm_reg_data_t data;
uvm_reg_data_t burst_data[];

// ★ 주소는 offset (메모리 영역 내 상대 주소), 절대 주소 아님 → 재사용 용이
my_mem.write(status, 'h100, 32'hDEAD_BEEF, .parent(this));
my_mem.read(status, 'h100, data, .parent(this));

// burst — 연속 주소에 배열 데이터 읽기/쓰기
burst_data = new[8];
foreach (burst_data[i]) burst_data[i] = i * 16;
my_mem.burst_write(status, 'h200, burst_data, .parent(this));

burst_data = new[4];
my_mem.burst_read(status, 'h200, burst_data, .parent(this));

// 다중 map 사용 시 map 지정
my_mem.read(status, 'h100, data, .parent(this), .map(ahb_2_map));
```

> **주의**: burst는 내부적으로 single transfer로 분해됨. 프로토콜 고유 burst 검증은 bus agent 시퀀스 직접 사용.

#### 메모리 테스트 시퀀스 패턴

```systemverilog
class mem_test_seq extends reg_base_seq;
    task body();
        uvm_reg_addr_t addrs[10];
        uvm_reg_data_t written[10];

        super.body();
        // Write loop
        for (int i = 0; i < 10; i++) begin
            addrs[i] = $urandom_range(0, rm.my_mem.get_size() - 1);
            written[i] = $urandom();
            rm.my_mem.write(status, addrs[i], written[i], .parent(this));
        end
        // Read-back loop
        for (int i = 0; i < 10; i++) begin
            rm.my_mem.read(status, addrs[i], data, .parent(this));
            if (data != written[i])
                `uvm_error("MEM_TEST", $sformatf("Mismatch @%0h: exp=%0h act=%0h",
                           addrs[i], written[i], data))
        end
    endtask
endclass
```

---

## 7. Built-in Register Sequences

### 주요 시퀀스

| Sequence | 목적 |
|----------|------|
| `uvm_reg_hw_reset_seq` | 리셋 후 모든 레지스터가 리셋 값과 일치하는지 확인 |
| `uvm_reg_bit_bash_seq` | RW 필드에 walking-1/0 패턴 write/read-back |
| `uvm_reg_access_seq` | 모든 레지스터에 frontdoor/backdoor 접근 테스트 |
| `uvm_mem_walk_seq` | 메모리 walking pattern 테스트 |

### 사용법

```systemverilog
task run_phase(uvm_phase phase);
    uvm_reg_hw_reset_seq reset_seq;
    uvm_reg_bit_bash_seq bash_seq;

    phase.raise_objection(this);

    // Reset value 확인
    reset_seq = uvm_reg_hw_reset_seq::type_id::create("reset_seq");
    reset_seq.model = reg_model;
    reset_seq.start(env.agent.seqr);

    // Bit bash 테스트
    bash_seq = uvm_reg_bit_bash_seq::type_id::create("bash_seq");
    bash_seq.model = reg_model;
    bash_seq.start(env.agent.seqr);

    phase.drop_objection(this);
endtask
```

### Opt-out (특정 레지스터 제외)

```systemverilog
// 특정 레지스터를 built-in sequence에서 제외
uvm_resource_db#(bit)::set({"REG::", reg_model.status_reg.get_full_name()},
                           "NO_REG_BIT_BASH_TEST", 1);
uvm_resource_db#(bit)::set({"REG::", reg_model.fifo_reg.get_full_name()},
                           "NO_REG_ACCESS_TEST", 1);
```

---

## 8. Register Stimulus API

### 핵심 메서드

```systemverilog
// Write — 값 쓰기 (bus를 통해)
reg_model.ctrl.write(status, .value(32'h0000_0001));

// Read — 값 읽기 (bus를 통해)
reg_model.ctrl.read(status, .value(read_data));

// Mirror — 실제 HW 값과 mirror 비교
reg_model.ctrl.mirror(status, .check(UVM_CHECK));  // 불일치 시 에러

// Update — desired 값을 HW에 반영
reg_model.ctrl.enable.set(1);  // desired 값 설정
reg_model.ctrl.mode.set(2'b10);
reg_model.ctrl.update(status);  // bus를 통해 write

// Desired/Mirror 값 접근 (bus 접근 없음)
reg_model.ctrl.set(32'h0000_0005);           // desired 값 설정
value = reg_model.ctrl.get();                 // desired 값 읽기
value = reg_model.ctrl.get_mirrored_value();  // mirror 값 읽기
```

### set() → update() 패턴

```systemverilog
// 여러 필드를 한번에 설정하고 한번의 bus write로 반영
reg_model.ctrl.enable.set(1);
reg_model.ctrl.mode.set(2'b11);
reg_model.ctrl.update(status);  // desired와 mirror 차이가 있는 필드만 write
```

---

## 9. Backdoor Access

Bus를 거치지 않고 HDL 시뮬레이션 계층을 통해 직접 접근.

```systemverilog
// Peek — HDL 경로에서 직접 읽기 (bus 미사용)
reg_model.ctrl.peek(status, .value(peek_data));

// Poke — HDL 경로에서 직접 쓰기 (bus 미사용)
reg_model.ctrl.poke(status, .value(32'hDEAD_BEEF));
```

### HDL Path 설정

```systemverilog
// Register 정의 시 HDL path 설정
ctrl.configure(this, null, "dut.u_ctrl.ctrl_reg");

// 또는 block 레벨에서
add_hdl_path("dut.u_block");
ctrl.add_hdl_path_slice("ctrl_reg", 0, 32);
```

**용도**: 초기화, 에러 주입, 빠른 상태 설정 (bus 사이클 절약)

---

## 10. Register Scoreboarding

### Mirror 기반 검증

```systemverilog
// 방법 1: mirror()로 즉시 비교
reg_model.ctrl.mirror(status, .check(UVM_CHECK));  // 불일치 시 uvm_error

// 방법 2: get_mirrored_value()로 수동 비교
expected = reg_model.ctrl.get_mirrored_value();
actual   = observed_transaction.data;
if (expected !== actual)
    `uvm_error("REG_SB", $sformatf("Mismatch: exp=0x%0h, act=0x%0h", expected, actual))

// 방법 3: predict()로 mirror 직접 갱신 (HW 자동 변경 반영)
reg_model.status_reg.predict(new_hw_value);
```

### Scoreboard에서 Register Model 활용

```systemverilog
function void check_transaction(my_transaction tr);
    // Register model의 mirror 값으로 예측값 계산
    bit [1:0] mode = reg_model.ctrl.mode.get_mirrored_value();
    bit       enable = reg_model.ctrl.enable.get_mirrored_value();

    if (enable) begin
        expected_data = calculate_expected(tr.input_data, mode);
        if (tr.output_data !== expected_data)
            `uvm_error("SB", "Output mismatch based on register config")
    end
endfunction
```

---

## 11. Register Coverage

### Built-in Coverage Types

| Type | 설명 |
|------|------|
| `UVM_CVR_REG_BITS` | 각 RW 필드 비트의 0/1 toggle coverage |
| `UVM_CVR_ADDR_MAP` | 각 레지스터가 address map을 통해 접근되었는지 |
| `UVM_CVR_FIELD_VALS` | 필드 값 coverage (자동 bin) |
| `UVM_CVR_ALL` | 위 모든 coverage |

### Coverage 활성화

```systemverilog
// ★ build() 전에 호출해야 함
uvm_reg::include_coverage("*", UVM_CVR_ALL);

// 또는 특정 레지스터만
uvm_reg::include_coverage("*ctrl*", UVM_CVR_REG_BITS | UVM_CVR_ADDR_MAP);

// Register block build() 후 활성화
reg_model.build();
void'(reg_model.set_coverage(UVM_CVR_ALL));
```

### Custom Register Coverage

Built-in coverage가 부족할 경우 custom coverage subscriber 작성:

```systemverilog
class reg_coverage extends uvm_subscriber #(apb_transaction);
    `uvm_component_utils(reg_coverage)

    my_reg_block reg_model;

    covergroup cg_reg_access with function sample(bit [7:0] addr, bit write);
        cp_addr: coverpoint addr {
            bins ctrl = {'h00};
            bins data = {'h04};
            bins stat = {'h08};
        }
        cp_rw: coverpoint write;
        cx_reg_rw: cross cp_addr, cp_rw {
            ignore_bins no_write_stat = binsof(cp_addr.stat) && binsof(cp_rw) intersect {1};
        };
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_reg_access = new();
    endfunction

    function void write(apb_transaction t);
        cg_reg_access.sample(t.addr[7:0], t.write);
    endfunction
endclass
```

→ SV covergroup 문법, bin 설계 기법은 **verilog-rtl** > `covergroup-patterns.md` 참조
