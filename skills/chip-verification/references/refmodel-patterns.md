# Reference Model Patterns

## Reference Model 역할

```
                    ┌─────────────┐
  Input ──────────► │  DUT (RTL)  │ ──────► Actual Output
    │               └─────────────┘              │
    │                                            │
    │               ┌─────────────┐              ▼
    └─────────────► │  Ref Model  │ ──────► Expected ──► Compare
                    └─────────────┘           Output      (Scoreboard)
```

## 기본 Reference Model 구조

```systemverilog
class my_ref_model extends uvm_component;
    `uvm_component_utils(my_ref_model)
    
    // TLM ports
    uvm_analysis_imp #(input_transaction, my_ref_model) in_ap;
    uvm_analysis_port #(output_transaction) out_ap;
    
    // 내부 상태 (RTL 파이프라인 모델링)
    input_transaction pipeline[$];
    int pipeline_depth;
    
    function new(string name, uvm_component parent);
        super.new(name, parent);
        pipeline_depth = 2;  // RTL 사이클 분석에서 결정
    endfunction
    
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        in_ap  = new("in_ap", this);
        out_ap = new("out_ap", this);
    endfunction
    
    // 입력 수신 시 예측 수행
    function void write(input_transaction tr);
        output_transaction exp;
        
        // 파이프라인에 추가
        pipeline.push_back(tr);
        
        // 파이프라인이 차면 출력 예측
        if (pipeline.size() >= pipeline_depth) begin
            exp = predict(pipeline.pop_front());
            out_ap.write(exp);
        end
    endfunction
    
    // 예측 함수 (RTL 동작 모델링)
    function output_transaction predict(input_transaction in);
        output_transaction out = output_transaction::type_id::create("out");
        // RTL 로직을 추상화하여 구현
        out.data   = transform(in.data);
        out.status = SUCCESS;
        return out;
    endfunction
    
endclass
```

## 사이클 정확 Reference Model

RTL 사이클 분석 결과를 직접 반영:

```systemverilog
class cycle_accurate_ref_model extends uvm_component;
    `uvm_component_utils(cycle_accurate_ref_model)
    
    // 사이클별 상태 (RTL always 블록 매핑)
    typedef struct {
        logic [31:0] data;
        logic        valid;
        int          cycle;
    } pipeline_entry_t;
    
    pipeline_entry_t stage1, stage2;  // RTL 레지스터 대응
    int current_cycle;
    
    // RTL always_ff @(posedge clk) 대응
    function void clock_cycle();
        current_cycle++;
        
        // [Cycle N+2] stage2 출력
        if (stage2.valid) begin
            output_transaction out;
            out = output_transaction::type_id::create("out");
            out.data = stage2.data;
            out.cycle = stage2.cycle + 2;  // latency = 2
            out_ap.write(out);
        end
        
        // [Cycle N+1] stage1 → stage2 전파
        stage2 = stage1;
        
        // [Cycle N] 입력 → stage1 (write()에서 처리)
        stage1.valid = 0;
    endfunction
    
    function void write(input_transaction tr);
        // [Cycle N] 입력 캡처
        stage1.data  = tr.data;
        stage1.valid = 1;
        stage1.cycle = current_cycle;
    endfunction
    
endclass
```

## FSM Reference Model

RTL FSM을 그대로 모델링:

```systemverilog
class fsm_ref_model extends uvm_component;
    
    // RTL FSM 상태 (verilog-rtl의 FSM과 동일)
    typedef enum {IDLE, FETCH, DECODE, EXECUTE, WRITEBACK} state_t;
    state_t current_state, next_state;
    
    // RTL FSM 대응 (상태 + 전이/출력 분리)

    // State Register (clock_cycle에서 호출)
    function void update_state();
        current_state = next_state;
    endfunction
    
    // Process 2: Next State Logic (입력 변화 시 호출)
    function void compute_next_state(input_transaction tr);
        case (current_state)
            IDLE:      if (tr.start) next_state = FETCH;
            FETCH:     next_state = DECODE;
            DECODE:    next_state = EXECUTE;
            EXECUTE:   next_state = WRITEBACK;
            WRITEBACK: next_state = IDLE;
            default:   next_state = IDLE;
        endcase
    endfunction
    
    // Process 3: Output Logic
    function output_transaction compute_output();
        output_transaction out;
        out = output_transaction::type_id::create("out");
        out.busy   = (current_state != IDLE);
        out.done   = (current_state == WRITEBACK);
        out.result = (current_state == WRITEBACK) ? computed_result : '0;
        return out;
    endfunction
    
endclass
```

## Transaction-Level vs Cycle-Level

### Transaction-Level (추상화)
```systemverilog
// 타이밍 무시, 기능만 검증
function void write(input_transaction in);
    output_transaction out;
    out.result = function_model(in);
    out_ap.write(out);  // 즉시 출력
endfunction
```
**용도:** 빠른 시뮬레이션, 기능 검증

### Cycle-Level (정밀)
```systemverilog
// RTL 사이클과 동기화
task run_phase(uvm_phase phase);
    forever begin
        @(posedge vif.clk);
        clock_cycle();  // 매 사이클 상태 업데이트
    end
endtask
```
**용도:** 타이밍 검증, 파이프라인 검증

## Scoreboard 연결

```systemverilog
class my_scoreboard extends uvm_scoreboard;
    
    // 두 analysis port: DUT 출력 vs Ref Model 출력
    uvm_analysis_imp_dut #(output_transaction, my_scoreboard) dut_ap;
    uvm_analysis_imp_ref #(output_transaction, my_scoreboard) ref_ap;
    
    output_transaction dut_queue[$];
    output_transaction ref_queue[$];
    
    function void write_dut(output_transaction tr);
        if (ref_queue.size() > 0)
            compare(tr, ref_queue.pop_front());
        else
            dut_queue.push_back(tr);
    endfunction
    
    function void write_ref(output_transaction tr);
        if (dut_queue.size() > 0)
            compare(dut_queue.pop_front(), tr);
        else
            ref_queue.push_back(tr);
    endfunction
    
    function void compare(output_transaction dut, output_transaction ref);
        if (!dut.compare(ref))
            `uvm_error("SCBD", $sformatf("Mismatch!\nDUT: %s\nREF: %s",
                       dut.convert2string(), ref.convert2string()))
    endfunction
    
endclass
```
