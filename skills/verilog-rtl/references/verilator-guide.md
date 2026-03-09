# Verilator Lint 가이드

## 환경 설정

Verilator는 MSYS2를 통해 설치되어 있음:

```bash
# Verilator 버전 확인
C:/msys64/usr/bin/bash.exe -lc "verilator --version"

# Lint 실행
C:/msys64/usr/bin/bash.exe -lc "cd '<project_path>' && verilator --lint-only -Wall --top-module <top_module> -I<include_paths> <files>"

# 여러 파일 지정 예
C:/msys64/usr/bin/bash.exe -lc "cd 'C:/path/to/project' && verilator --lint-only -Wall --top-module my_top -Idb/design/d_rtl/mdl db/top/my_fpga_top.v"
```

## 주요 Warning 유형

| Warning | 심각도 | 설명 | 처리 방법 |
|---------|--------|------|-----------|
| IMPLICIT | 🔴 Critical | 미선언 신호 사용 | 반드시 수정 |
| PINMISSING | 🟠 Warning | 인스턴스 포트 미연결 | 가능하면 수정 |
| WIDTHTRUNC | 🟠 Warning | 비트폭 절삭 — 상위 비트 손실 | 가능하면 수정 |
| WIDTHEXPAND | 🟠 Warning | 비트폭 확장 — 부호 확장 주의 | 가능하면 수정 |
| PINCONNECTEMPTY | 🟡 Info | 빈 포트 연결 `()` (의도적일 수 있음) | 의도적이면 억제 |
| TIMESCALEMOD | 🟡 Info | timescale 불일치 | 의도적이면 억제 |
| EOFNEWLINE | 🟡 Info | 파일 끝 줄바꿈 누락 | 가능하면 수정 |
| UNUSED | 🟡 Info | 미사용 신호/변수 | 의도적이면 억제 |

**심각도 기준:**
- 🔴 Critical: 동작 불일치 또는 합성 오류 유발 → 반드시 수정
- 🟠 Warning: 의도치 않은 동작 가능성 → 원인 파악 후 수정 또는 억제
- 🟡 Info: 스타일/관행 문제 → 의도적이면 억제 가능

## Warning 억제 방법

### 특정 라인 억제

```verilog
/* verilator lint_off PINCONNECTEMPTY */
u_sub u_sub_inst (
    .o_unused_port  (),   // intentionally unconnected
    .o_data         (w_data)
);
/* verilator lint_on PINCONNECTEMPTY */
```

### 블록 억제

```verilog
/* verilator lint_off WIDTHTRUNC */
assign r_short = wide_signal;  // intentional truncation
/* verilator lint_on WIDTHTRUNC */
```

### 파일 전체 억제 (파일 상단)

```verilog
/* verilator lint_off UNUSED */
// 시뮬레이션 전용 파일 등에서 사용
```

## 자주 발생하는 상황

### WIDTHTRUNC: $clog2 비트 부족

```verilog
// BAD: FIFO_DEPTH=16이면 clog2(16)=4, 0~15는 저장 가능하지만
//      full 상태(count=16)를 저장하려면 비트 부족 → WIDTHTRUNC
logic [$clog2(FIFO_DEPTH)-1:0] r_count;

// GOOD: +1 비트로 안전하게
logic [$clog2(FIFO_DEPTH):0] r_count;    // 0~FIFO_DEPTH 저장 가능
```

자세한 Bit-Width Safety 규칙: `synthesis-check.md` > Bit-Width Safety 참조
