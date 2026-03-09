# Reveal Debugger Guide

Reveal은 Lattice의 내장 로직 분석기 (Xilinx ILA, Intel SignalTap 대응).

## 기본 개념

```
┌─────────────────────────────────────────────────────────────┐
│                         FPGA                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐      ┌─────────────────────────────┐  │
│  │   Your Design   │─────►│      Reveal Inserter        │  │
│  │                 │      │  ┌─────────────────────────┐│  │
│  │   신호 탭 ──────┼─────►│  │ Trace Buffer (BRAM)    ││  │
│  │                 │      │  └─────────────────────────┘│  │
│  └─────────────────┘      │  ┌─────────────────────────┐│  │
│                           │  │ Trigger Logic          ││  │
│                           │  └─────────────────────────┘│  │
│                           └──────────────┬──────────────┘  │
│                                          │                  │
│                                          ▼ JTAG             │
│                                     ┌─────────┐            │
│                                     │ PC/Tool │            │
│                                     └─────────┘            │
└─────────────────────────────────────────────────────────────┘
```

## Reveal 설정 (Radiant)

### 1. Reveal Inserter 프로젝트 생성

```
Radiant → Tools → Reveal Inserter
→ New Reveal Project (.rvl)
```

### 2. 신호 추가

```tcl
# reveal_setup.tcl

# Trace 신호 추가
add_trace_signal -name {fsm_state[2:0]} -width 3
add_trace_signal -name {data_valid} -width 1
add_trace_signal -name {data_out[31:0]} -width 32

# Trigger 신호 (트리거 조건용)
add_trigger_signal -name {error_flag} -width 1
add_trigger_signal -name {fsm_state[2:0]} -width 3
```

### 3. 트리거 조건

```
# GUI에서 또는 TCL로

# 단순 트리거: error_flag가 1일 때
set_trigger_condition -signal error_flag -value 1

# 복합 트리거: 특정 상태에서 에러
set_trigger_condition -expr {(fsm_state == 3'b101) && (error_flag == 1)}

# 시퀀스 트리거: A 발생 후 B 발생
set_trigger_sequence -step1 {start_pulse == 1} -step2 {done_pulse == 1}
```

### 4. 샘플 깊이 설정

```tcl
# Buffer 크기 (BRAM 사용량과 트레이드오프)
set_sample_depth 1024    # 1K 샘플
set_sample_depth 4096    # 4K 샘플
set_sample_depth 16384   # 16K 샘플

# Pre-trigger 비율 (트리거 전 데이터 비율)
set_pretrigger_depth 25%  # 25%는 트리거 전, 75%는 트리거 후
```

## RTL에서 Reveal 신호 지정

### 방법 1: Attribute 사용

```verilog
// Verilog
(* syn_keep = 1, mark_debug = "true" *)
reg [2:0] fsm_state;

(* syn_keep = 1, mark_debug = "true" *)
wire [31:0] debug_data;
```

```verilog
// SystemVerilog
(* mark_debug = "true" *)
logic [2:0] fsm_state;
```

### 방법 2: Reveal Inserter에서 직접 선택

```
1. Reveal Inserter 열기
2. Design Navigator에서 신호 찾기
3. 드래그 & 드롭으로 Trace/Trigger에 추가
```

## Reveal Analyzer 사용

### 연결 및 캡처

```
1. FPGA 보드 연결 (JTAG)
2. Radiant → Tools → Reveal Analyzer
3. .rvl 파일 열기
4. "Arm" 버튼 클릭
5. 트리거 대기 또는 "Force Trigger"
6. 파형 분석
```

### 파형 분석

```
┌─────────────────────────────────────────────────────────────┐
│  Reveal Analyzer                                            │
├─────────────────────────────────────────────────────────────┤
│                    ▼ Trigger Point                          │
│  clk        ─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─┬─               │
│  fsm_state  ─┤1├─┤1├─┤2├─┤3├─┤4├─┤5├─┤0├─┤              │
│  data_valid ───┘ └───────┐ └─────────────                  │
│  error_flag ─────────────┴─────────────                    │
│                                                             │
│  [Export VCD] [Export CSV] [Save Image]                    │
└─────────────────────────────────────────────────────────────┘
```

### VCD Export (시뮬레이터에서 비교)

```
File → Export → VCD Format
→ reveal_capture.vcd

# 시뮬레이션 파형과 비교 가능
```

## 디버깅 팁

### 1. 리소스 최적화

```verilog
// 넓은 버스 전체 대신 일부만 trace
(* mark_debug = "true" *)
wire [7:0] data_debug = data_full[7:0];  // 하위 8비트만
```

### 2. 여러 Reveal Core

```
// 다른 클럭 도메인별로 분리
Reveal Core 1: clk_100m 도메인 신호
Reveal Core 2: clk_200m 도메인 신호
```

### 3. 트리거 조합

```
# 복잡한 조건
Trigger = (state == ERROR) AND (counter > 100) AND (enable == 1)
```

## BRAM 사용량

| 샘플 깊이 | 신호 폭 32bit | 신호 폭 64bit |
|----------|--------------|--------------|
| 1K | 1 BRAM | 2 BRAM |
| 4K | 4 BRAM | 8 BRAM |
| 16K | 16 BRAM | 32 BRAM |

**팁:** 신호 수와 샘플 깊이 균형 조절
