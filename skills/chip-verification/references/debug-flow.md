# Debug Flow: Simulation Failure to RTL Bug

## 디버그 워크플로우

```
Simulation Fail
      │
      ▼
┌─────────────────┐
│ 1. 에러 메시지  │ → 어떤 검증 요소가 실패?
│    분석         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. 트랜잭션    │ → 실패 시점의 입출력 데이터
│    추적         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. 사이클      │ → RTL 내부 신호 파형 분석
│    분석         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. RTL 코드    │ → 원인이 되는 always 블록 식별
│    추적         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 5. 버그 수정   │ → RTL 수정 후 회귀 테스트
│    & 검증      │
└─────────────────┘
```

## Step 1: 에러 메시지 분석

### Scoreboard Mismatch
```
UVM_ERROR @ 1250ns: SCBD [MISMATCH]
  Expected: data=0x00001234 valid=1
  Actual:   data=0x00005678 valid=1
```
**분석:**
- 데이터 값이 다름 → 연산 로직 또는 데이터 경로 문제
- valid 타이밍은 맞음 → 제어 로직은 정상

### Timeout
```
UVM_FATAL @ 10000ns: DRV [TIMEOUT] 
  Waited 1000 cycles for ready
```
**분석:**
- Handshake 실패 → FSM이 stuck 상태일 가능성
- Backpressure 처리 문제

### Assertion Failure
```
Error: Assertion p_valid_stable failed @ 500ns
  valid deasserted before ready
```
**분석:**
- 프로토콜 위반 → 해당 신호 구동 로직 확인

## Step 2: 트랜잭션 추적

### 실패 트랜잭션 식별
```systemverilog
// Scoreboard에서 실패 정보 저장
function void compare(...);
    if (!match) begin
        $display("=== FAIL TRANSACTION ===");
        $display("Input:  %s", input_tr.convert2string());
        $display("Output: %s", actual.convert2string());
        $display("Expected: %s", expected.convert2string());
        $display("Cycle: %0d", $time / CLK_PERIOD);
        $display("========================");
    end
endfunction
```

### 패턴 분석
```
질문:
- 특정 입력 값에서만 실패?
- 특정 시퀀스(연속 트랜잭션)에서만 실패?
- 랜덤하게 실패? (타이밍 문제 가능성)
```

## Step 3: 사이클 분석

### 파형 덤프 활성화
```tcl
# VCS
fsdbDumpvars 0 tb_top +all

# Xcelium  
database -open waves -into waves.shm
probe -create tb_top -depth all -all
```

### 핵심 신호 추적
```
클럭 도메인별:
1. 입력 인터페이스 신호 (valid, ready, data)
2. 파이프라인 레지스터 (stage1_*, stage2_*)
3. FSM 상태 (current_state, next_state)
4. 출력 인터페이스 신호

RTL 사이클 분석과 대조:
[Cycle 100] input captured     → 파형에서 확인
[Cycle 101] stage1 processing  → 파형에서 확인
[Cycle 102] output expected    → 실제 출력과 비교
```

### 비교 분석 템플릿
```
Signal        | Expected | Actual | Match
--------------|----------|--------|------
stage1_data   | 0x1234   | 0x1234 | ✓
stage1_valid  | 1        | 1      | ✓
stage2_data   | 0x1235   | 0x5678 | ✗ ← 문제 발생 지점
stage2_valid  | 1        | 1      | ✓
```

## Step 4: RTL 코드 추적

### Always 블록 식별
```verilog
// 문제 신호: stage2_data
// 해당 신호를 할당하는 always 블록 찾기

always_ff @(posedge clk) begin
    if (!rst_n)
        stage2_data <= '0;
    else if (stage2_enable)
        stage2_data <= stage1_data + 1;  // ← 여기가 문제?
end
```

### 입력 조건 확인
```verilog
// stage2_enable이 왜 그 값인지 추적
always_comb begin
    stage2_enable = stage1_valid & ~stall;  // stall 조건 확인
end
```

### 일반적인 버그 패턴

| 증상 | 가능한 원인 |
|------|------------|
| 데이터 1사이클 늦음 | 레지스터 추가됨, 조합→순차 변경 |
| 데이터 1사이클 빠름 | 레지스터 제거됨, 순차→조합 변경 |
| 간헐적 데이터 오류 | CDC 문제, 메타스테이빌리티 |
| 특정 값에서 오류 | 오버플로우, 경계 조건 |
| FSM 멈춤 | 상태 전이 조건 불완전 |

## Step 5: 버그 수정 & 검증

### 수정 전 체크리스트
- [ ] 버그 원인 명확히 이해
- [ ] 수정이 다른 기능에 영향 없는지 확인
- [ ] 수정된 사이클 타이밍 문서화

### 회귀 테스트
```bash
# 실패한 테스트 먼저
make test TEST=failed_test SEED=<original_seed>

# 전체 회귀
make regress
```

### 디버그 로그 추가 (임시)
```verilog
// synthesis translate_off
always @(posedge clk) begin
    if (stage2_enable)
        $display("[%0t] stage2: in=%h out=%h", $time, stage1_data, stage2_data);
end
// synthesis translate_on
```

## 디버그 효율화 팁

### 1. 재현 가능한 실패
```bash
# 시드 고정
+UVM_TESTNAME=my_test +seed=12345
```

### 2. 범위 좁히기
```systemverilog
// 특정 조건에서만 덤프
initial begin
    if ($test$plusargs("DEBUG_MODE")) begin
        #100us;  // 문제 시점 근처부터
        $fsdbDumpon;
    end
end
```

### 3. Assertion 추가
```verilog
// 문제 조건 감시
assert property (@(posedge clk) 
    stage1_valid |-> ##2 stage2_valid
) else $error("Pipeline stall detected");
```
