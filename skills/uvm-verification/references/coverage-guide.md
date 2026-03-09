# UVM Coverage Integration Guide

## 1. UVM Coverage Subscriber

`uvm_subscriber #(T)` 확장으로 analysis port에서 트랜잭션을 받아 sampling.

### Single Covergroup

```systemverilog
class my_coverage extends uvm_subscriber #(my_transaction);
    `uvm_component_utils(my_coverage)

    my_transaction tr;

    covergroup cg_transaction with function sample(
        bit [31:0] addr, bit [31:0] data, bit write
    );
        option.per_instance = 1;
        option.name = "txn_cg";

        cp_addr: coverpoint addr {
            bins low   = {[0:32'h0FFF]};
            bins mid   = {[32'h1000:32'h7FFF]};
            bins high  = {[32'h8000:32'hFFFF]};
        }

        cp_write: coverpoint write {
            bins read  = {0};
            bins write = {1};
        }

        cx_addr_write: cross cp_addr, cp_write;
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_transaction = new();
    endfunction

    // ★ write()에서 sampling
    function void write(my_transaction t);
        cg_transaction.sample(t.addr, t.data, t.write);
    endfunction

    function void report_phase(uvm_phase phase);
        `uvm_info("COV", $sformatf("Coverage: %.2f%%",
                  cg_transaction.get_coverage()), UVM_LOW)
    endfunction
endclass
```

### 다중 Covergroup + 조건부 Sampling

하나의 subscriber에서 여러 covergroup 운용 시:
- 각 covergroup을 constructor에서 `new()`
- `write()` 내에서 **조건별 분기**로 선택적 sampling:
  - 에러 유형별: `if (t.has_error) cg_error.sample(t.err_code);`
  - Check 통과 확인: `if (t.status == PASS) cg_normal.sample(...);`
  - 모드별 분기: `case (t.mode) ... endcase`

★ Check 통과 시에만 sampling — 오동작 시 sampling은 무의미 (verilog-rtl > coverage-methodology §6)
★ Covergroup 문법 상세 → verilog-rtl > covergroup-patterns.md

---

## 2. Register Model 연동 Coverage

### External Monitor 권장 (★)

Register coverage 구현 시 **외부 coverage monitor** (uvm_subscriber 확장) 권장:

| 방식 | 설명 | 권장 여부 |
|------|------|----------|
| Reg model 내부 covergroup | include_coverage → build 시 자동 생성 | narrow field에만 유용. 넓은 field는 overhead만 증가 |
| **External coverage monitor** | uvm_subscriber에서 reg model 핸들로 sampling | **권장** — 분리 개발, 제어 용이, 비-register 변수와 cross 가능 |

★ Covergroup wrapper를 `uvm_object`로 감싸면 **factory override로 대체 coverage model 교체** 가능
★ 지연 생성(deferred construction)으로 조건부 coverage 활성화 유연

Register model의 mirrored value를 활용하여 DUT 설정 기반 coverage 수집.

```systemverilog
class reg_context_coverage extends uvm_subscriber #(data_transaction);
    `uvm_component_utils(reg_context_coverage)

    my_reg_block reg_model;

    covergroup cg_data_with_config with function sample(
        bit [7:0] result, bit [1:0] mode, bit enable
    );
        cp_result: coverpoint result {
            bins low  = {[0:63]};
            bins mid  = {[64:191]};
            bins high = {[192:255]};
        }
        cp_mode: coverpoint mode;
        cp_enable: coverpoint enable;
        cx_result_mode: cross cp_result, cp_mode {
            ignore_bins disabled = binsof(cp_enable) intersect {0};
        };
    endgroup

    function new(string name, uvm_component parent);
        super.new(name, parent);
        cg_data_with_config = new();
    endfunction

    function void write(data_transaction t);
        // ★ Register model에서 현재 설정 획득
        bit [1:0] current_mode = reg_model.ctrl.mode.get_mirrored_value();
        bit       current_en   = reg_model.ctrl.enable.get_mirrored_value();

        cg_data_with_config.sample(t.result, current_mode, current_en);
    endfunction
endclass
```

### Register Access Coverage

★ Register access covergroup 문법 (bins/cross/ignore_bins) → verilog-rtl > covergroup-patterns.md §3

---

## 3. Coverage Component Naming

```systemverilog
// ★ UVM 계층 경로를 covergroup 이름에 반영
cg_transaction = new();
cg_transaction.option.name = get_full_name();
// 또는: cg = new($sformatf("%s.cg", get_full_name()));
```

★ `option.per_instance = 1` 등 SV option 상세 → verilog-rtl > covergroup-patterns.md §4

---

## 4. Analysis Path 기반 Coverage

UVM TLM 구조에서 coverage sampling 경로:

```
DUT → Monitor → Analysis Port → Coverage Subscriber
                              → Scoreboard
```

### Scoreboard Check 통과 후 Sampling

```systemverilog
class checked_coverage extends uvm_component;
    `uvm_component_utils(checked_coverage)

    uvm_analysis_imp #(checked_transaction, checked_coverage) ap;

    covergroup cg_verified with function sample(bit [31:0] addr, bit [31:0] data);
        // ... coverpoints
    endgroup

    function void write(checked_transaction t);
        // ★ Scoreboard가 검증 완료 표시한 트랜잭션만 sampling
        if (t.check_passed)
            cg_verified.sample(t.addr, t.data);
    endfunction
endclass
```

---

## 5. UVM Register Coverage

### Built-in Coverage Types

| Type | 설명 |
|------|------|
| `UVM_CVR_REG_BITS` | 각 RW 필드 비트의 0/1 toggle |
| `UVM_CVR_ADDR_MAP` | address map을 통한 접근 여부 |
| `UVM_CVR_FIELD_VALS` | 필드 값 coverage |
| `UVM_CVR_ALL` | 위 모든 coverage |

### 활성화

```systemverilog
// ★ build() 전에 호출
uvm_reg::include_coverage("*", UVM_CVR_ALL);

// Register block build 후
reg_model.build();
void'(reg_model.set_coverage(UVM_CVR_ALL));
```

### sample() / sample_values()

```systemverilog
// 자동 sampling — read()/write() 시 자동 호출
// 수동 sampling
reg_model.ctrl.sample();         // address/access 기반
reg_model.ctrl.sample_values();  // 필드 값 기반
```

### Register Block Coverage 제어 흐름

Reg block 내부에 covergroup을 통합할 때의 **완전한 제어 흐름**:

| Method | 용도 | 호출 시점 |
|--------|------|----------|
| `uvm_reg::include_coverage()` | resource DB에 coverage 타입 등록 (static) | **Test build_phase — reg_model.build() 전** |
| `build_coverage()` | resource DB에서 m_has_cover 설정 | Constructor (super.new 인자) |
| `has_coverage()` | 해당 coverage 타입이 빌드되었는지 확인 | build(), sample() |
| `add_coverage()` | m_has_cover에 coverage 타입 추가 | build() |
| `set_coverage()` | sampling 활성화 (m_cover_on 설정) | build() (covergroup 생성 후) |
| `get_coverage()` | sampling 활성 여부 확인 | sample(), sample_values() |

```systemverilog
// ★ Reg block constructor: build_coverage로 coverage 타입 등록
function new(string name = "my_reg_block");
    super.new(name, build_coverage(UVM_CVR_ADDR_MAP));
endfunction

// ★ build(): has_coverage 체크 → 생성 → set_coverage
virtual function void build();
    if (has_coverage(UVM_CVR_ADDR_MAP)) begin
        access_cg = reg_access_wrapper::type_id::create("access_cg");
        set_coverage(UVM_CVR_ADDR_MAP);  // sampling 활성화
    end
    // ... register 생성, map 설정 ...
endfunction

// ★ sample(): get_coverage 체크 → 실제 sampling
function void sample(uvm_reg_addr_t offset, bit is_read, uvm_reg_map map);
    if (get_coverage(UVM_CVR_ADDR_MAP))
        access_cg.sample(offset, is_read);
endfunction
```

★ `set_coverage()`는 `has_coverage()`가 true인 타입만 활성화 가능 — build 없이 sampling 불가

---

## 6. Env Integration

### has_functional_coverage 플래그로 조건부 생성

```systemverilog
class my_env extends uvm_env;
    env_config    cfg;
    my_agent      agent;
    my_coverage   cov;  // coverage subscriber

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        agent = my_agent::type_id::create("agent", this);

        // ★ 조건부 생성
        if (cfg.has_coverage)
            cov = my_coverage::type_id::create("cov", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // ★ monitor.ap → coverage subscriber 연결
        if (cfg.has_coverage)
            agent.mon.ap.connect(cov.analysis_export);
    endfunction
endclass
```

---

## Cross-Skill 참조

- SV covergroup 문법, bin 설계, cross 기법 → **verilog-rtl** > `covergroup-patterns.md`
- Coverage 이론, testplan, closure 프로세스 → **verilog-rtl** > `coverage-methodology.md`
- 실전 예제 (APB3, UART, Datapath) → **verilog-rtl** > `coverage-examples.md`
