# UVM Debug Guide

## 로그 레벨 제어

### Verbosity 레벨
```
UVM_NONE   = 0    // 항상 출력
UVM_LOW    = 100  // 핵심 정보
UVM_MEDIUM = 200  // 일반 정보
UVM_HIGH   = 300  // 상세 정보
UVM_FULL   = 400  // 매우 상세
UVM_DEBUG  = 500  // 디버그용
```

### 런타임 설정
```bash
# 전체 verbosity
+UVM_VERBOSITY=UVM_HIGH

# 특정 컴포넌트만
+uvm_set_verbosity=uvm_test_top.env.agent.drv,_ALL_,UVM_DEBUG,time,0
```

### 코드에서 설정
```systemverilog
// 특정 컴포넌트
env.agent.drv.set_report_verbosity_level(UVM_DEBUG);

// 계층 전체
uvm_top.set_report_verbosity_level_hier(UVM_HIGH);
```

## 메시지 매크로 사용

```systemverilog
`uvm_info("TAG", "Normal message", UVM_MEDIUM)
`uvm_warning("TAG", "Warning message")
`uvm_error("TAG", "Error message")
`uvm_fatal("TAG", "Fatal - simulation stops")

// 조건부 출력
`uvm_info_context("TAG", "msg", UVM_LOW, component_handle)
```

## Report Catcher

메시지를 가로채서 severity 변경, 필터링, 수정 가능.

### 기본 패턴

```systemverilog
class my_report_catcher extends uvm_report_catcher;
    `uvm_object_utils(my_report_catcher)

    function new(string name = "my_report_catcher");
        super.new(name);
    endfunction

    function action_e catch();
        // 특정 메시지를 ERROR → WARNING으로 변경
        if (get_severity() == UVM_ERROR && get_id() == "EXPECTED_ERR") begin
            set_severity(UVM_WARNING);
            return THROW;  // 변경된 severity로 출력
        end

        // 특정 메시지 완전 억제
        if (get_id() == "NOISY_MSG")
            return CAUGHT;  // 출력하지 않음

        return THROW;  // 기본: 그대로 출력
    endfunction
endclass
```

### 등록

```systemverilog
// Per-component 등록
my_report_catcher catcher = new("catcher");
uvm_report_cb::add(env.agent.drv, catcher);

// Global 등록 (모든 컴포넌트)
uvm_report_cb::add(null, catcher);
```

### 활용 사례

| 용도 | catch() 구현 |
|------|-------------|
| 알려진 에러 억제 | `get_id()` 매칭 → `CAUGHT` |
| ERROR → WARNING 변경 | `set_severity()` → `THROW` |
| 메시지 카운트 | 내부 카운터 증가 → `THROW` |
| 메시지 내용 변경 | `set_message()` → `THROW` |

## Phase 디버깅

### Objection 추적

```bash
+UVM_OBJECTION_TRACE
+UVM_PHASE_TRACE
```

### Phase 시작/종료 확인
```systemverilog
function void phase_started(uvm_phase phase);
    `uvm_info("PHASE", $sformatf("Starting %s", phase.get_name()), UVM_LOW)
endfunction

function void phase_ended(uvm_phase phase);
    `uvm_info("PHASE", $sformatf("Ended %s", phase.get_name()), UVM_LOW)
endfunction
```

### Objection 규칙

```
★ Objection은 test 또는 virtual sequence에서만 raise/drop
★ Driver, Monitor, Scoreboard에서 objection 금지
★ phase_ready_to_end()로 drain time 처리
```

### phase_ready_to_end 패턴

```systemverilog
function void phase_ready_to_end(uvm_phase phase);
    if (phase.get_name() == "run") begin
        phase.raise_objection(this, "Drain time");
        fork begin
            #1000;  // drain time
            phase.drop_objection(this, "Drain complete");
        end join_none
    end
endfunction
```

## TLM 디버깅

### 포트 연결 확인
```systemverilog
function void end_of_elaboration_phase(uvm_phase phase);
    // 토폴로지 출력
    uvm_top.print_topology();

    // 특정 포트 연결 확인
    if (!drv.seq_item_port.is_connected())
        `uvm_fatal("CONN", "seq_item_port not connected")
endfunction
```

### 트랜잭션 추적
```systemverilog
// Monitor에서 모든 트랜잭션 로깅
function void write(my_transaction tr);
    `uvm_info("MON", tr.convert2string(), UVM_HIGH)
endfunction
```

## Factory 디버깅

### 등록 확인
```systemverilog
function void start_of_simulation_phase(uvm_phase phase);
    factory.print();
endfunction
```

### Override 확인
```bash
+UVM_DUMP_CMDLINE_ARGS
```

## Config DB 디버깅

### 모든 설정 출력
```systemverilog
uvm_config_db#(virtual my_if)::dump();
```

### Get 실패 추적
```systemverilog
if (!uvm_config_db#(virtual my_if)::get(this, "", "vif", vif)) begin
    `uvm_info("CFG", "Available configs:", UVM_LOW)
    uvm_config_db#(virtual my_if)::dump();
    `uvm_fatal("NOVIF", "Virtual interface not set")
end
```

### Config DB 경로 주의

```systemverilog
// ★ "uvm_test_top" 사용 — null 대신 명시적 경로 권장
uvm_config_db#(env_config)::set(null, "uvm_test_top.env", "env_cfg", cfg);

// ★ 와일드카드 사용 시 주의 — 의도하지 않은 컴포넌트에 전달될 수 있음
// BAD: 너무 넓은 범위
uvm_config_db#(virtual my_if)::set(null, "*", "vif", vif);
// GOOD: 정확한 경로
uvm_config_db#(virtual my_if)::set(null, "uvm_test_top.env.agent*", "vif", vif);
```

## 시뮬레이터별 디버깅

### VCS
```bash
# 파형 덤프
+fsdb+all
-debug_access+all

# UVM 디버깅
+UVM_TR_RECORD
+UVM_LOG_RECORD
```

### Xcelium
```bash
# 파형 덤프
-access +rwc
-input probe.tcl

# UVM 디버깅
-uvmhome CDNS-1.2
-uvm_set_config_int "*,recording_detail,UVM_FULL"
```

### QuestaSim
```bash
# 파형 덤프
-voptargs=+acc

# UVM 디버깅
+UVM_SET_CONFIG_INT=*,recording_detail,1
```

## 일반적인 문제 해결

### 1. Timeout / Hang
```
원인: objection 미해제, 무한 루프
확인:
  - +UVM_OBJECTION_TRACE
  - 각 raise/drop 쌍 확인
  - forever 루프 내 @(event) 확인
  - ★ Objection은 test/vseq에서만 raise/drop하면 추적 용이
```

### 2. Virtual Interface Null
```
원인: config_db set/get 경로 불일치
확인:
  - uvm_config_db::dump() 출력
  - hierarchical path 정확히 일치하는지
  - build_phase 순서 (top-down)
  - ★ "uvm_test_top" vs "*" 확인
```

### 3. Sequence Not Starting
```
원인: sequencer 미연결, objection 누락
확인:
  - seq.start() 전에 raise_objection
  - driver.seq_item_port.is_connected()
```

### 4. Scoreboard Mismatch
```
원인: 타이밍 불일치, 예측 모델 오류
확인:
  - Monitor 샘플링 시점
  - Reference model 로직
  - Transaction 비교 함수 (do_compare)
  - ★ Predictor 분리 패턴으로 디버깅 용이
```

### 5. Coverage Hole
```
원인: 제약 부족, 시나리오 누락
확인:
  - Constraint 분포 확인
  - Cross coverage 분석
  - Sequence 다양성
  - ★ verilog-rtl > coverage-methodology.md 참조 (hole analysis 프로세스)
```

### 6. Factory Override 미적용
```
원인: override 시점 오류, 타입 불일치
확인:
  - factory.print() 확인
  - override는 create() 전에 설정
  - 대상 클래스에 `uvm_*_utils 등록 확인
```

## 유용한 디버그 코드

```systemverilog
// 사이클 카운터
int cycle_count;
always @(posedge clk) cycle_count++;

// 트랜잭션 ID 추적
class my_transaction extends uvm_sequence_item;
    static int id_counter;
    int tr_id;

    function new(string name = "");
        super.new(name);
        tr_id = id_counter++;
    endfunction
endclass

// 조건부 중단점
if (cycle_count > 1000 && state == ERROR)
    $stop;  // 시뮬레이터 중단
```

## Command-Line Plusargs 참조

### 기본 설정 (1회)

| Plusarg | 설명 | 예시 |
|---------|------|------|
| `+UVM_TESTNAME=<class>` | 실행할 test class | `+UVM_TESTNAME=sanity_test` |
| `+UVM_VERBOSITY=<level>` | 전체 verbosity | `+UVM_VERBOSITY=UVM_HIGH` |
| `+UVM_TIMEOUT=<ns>,<YES/NO>` | 글로벌 타임아웃 | `+UVM_TIMEOUT=1000000,NO` |
| `+UVM_MAX_QUIT_COUNT=<N>,<YES/NO>` | error N개 후 종료 | `+UVM_MAX_QUIT_COUNT=5,NO` |

### 디버그 트레이스

```bash
+UVM_PHASE_TRACE           # phase 실행 추적
+UVM_OBJECTION_TRACE       # objection raise/drop 추적
+UVM_CONFIG_DB_TRACE       # config_db set/get 추적
+UVM_RESOURCE_DB_TRACE     # resource_db 접근 추적
```

### 런타임 오버라이드 (다중 사용 가능)

```bash
# 특정 컴포넌트의 verbosity 변경
+uvm_set_verbosity=uvm_test_top.env.agent.*,_ALL_,UVM_DEBUG,time,0

# message severity 변경 (ERROR → WARNING)
+uvm_set_severity=uvm_test_top.env.*,BAD_CRC,UVM_ERROR,UVM_WARNING

# message action 변경 (ERROR 무시)
+uvm_set_action=uvm_test_top.env.*,_ALL_,UVM_ERROR,UVM_NO_ACTION

# factory override (커맨드라인에서)
+uvm_set_type_override=base_test,extended_test
+uvm_set_inst_override=base_seq,error_seq,uvm_test_top.env.agent.sequencer.*

# config_db에 int/string 설정
+uvm_set_config_int=uvm_test_top.env,num_loops,100
+uvm_set_config_string=uvm_test_top,test_mode,stress
```

### 사용자 정의 Plusarg

```systemverilog
uvm_cmdline_processor clp = uvm_cmdline_processor::get_inst();

// 단일 값 (예: +MY_ITER=500)
string val;
if (clp.get_arg_value("+MY_ITER=", val))
    num_iter = val.atoi();

// 다중 값 (예: +MY_CFG=a +MY_CFG=b)
string vals[$];
clp.get_arg_values("+MY_CFG=", vals);
```

> **주의**: 사용자 plusarg에 `uvm_` / `UVM_` 접두어 사용 금지 (UVM 예약).
