---
name: verilog-rtl
description: |
  Verilog/SystemVerilog RTL 설계 및 분석 skill. 다음 상황에서 사용:
  (1) RTL 코드 작성 - 신호 네이밍, always 블록 분리, FSM 설계
  (2) 사이클 분석 - 동일 사이클 처리 로직 식별, 타이밍 관계 분석
  (3) 합성 가능성 검토 - latch 방지, CDC 처리, 합성 문제 사전 식별
  (4) 코드 리뷰 및 버그 탐지 - race condition, 미정의 동작 검출
  (5) 모듈 통합 - top integration, 포트 연결, 파라미터 전달
  (6) Coverage 설계 - UVM 없이 SV만으로 covergroup, coverpoint, cross, bin, assertion coverage 구현
  (7) SV 검증 구문 - SVA assertion, covergroup, cross, 테스트벤치 SV 문법
  Verilog/SystemVerilog RTL 작업이라면 반드시 이 스킬을 사용.
  트리거: Verilog, SystemVerilog, RTL, always, FSM, 합성, synthesis, 모듈, 사이클, cycle, 타이밍, clock, reset,
    covergroup, coverpoint, cross, bins, cover property, assertion coverage, code coverage,
    toggle, FSM coverage, MC/DC, hole analysis, coverage closure (standalone RTL 환경),
    coverage 구현 (UVM 없이 SV만으로),
    bit-width, truncation, clog2, localparam, parameter width,
    Verilator, lint, lint-only
---

# Verilog RTL Design Skill

## 핵심 개념

Verilog RTL 설계의 두 가지 핵심:
1. **Always 블록 분리** - 로직을 목적별로 분리하여 가독성과 합성 품질 향상
2. **사이클 분석** - 같은 클럭 사이클에 처리되는 로직을 식별하여 타이밍 이해

RTL 설계 흐름: **요구사항**(무엇을) → **사이클 맵**(언제) → **Always 분할**(어떻게)

---

## 1. Design Rules

### 필수 규칙

| 규칙 | 설명 |
|------|------|
| **Asynchronous Reset** | Active low (`i_rst_n`), 비동기 리셋 기본 [→§1.Reset] |
| **No Latches** | 기본값 할당 또는 if/case 완전성으로 방지 [→§1,§7] |
| **CDC 방식 선택** | Slow→Fast: 2FF/Pulse Sync, Fast→Slow: Handshake [→§1.CDC] |
| **Blocking 규칙** | always_ff: `<=`, always_comb: `=` [→§2] |
| **단일 할당 원칙** | 동일 신호를 여러 always에서 할당 금지 [→§2] |
| **Bit-Width Safety** | sized 변수에 값 할당 시 max value < 2^W 검증 필수 [→§1.BitWidth] |

### Bit-Width Truncation 방지

**Bit-Width Safety 규칙:**
- localparam은 특별한 이유 없으면 unsized 사용 (32-bit default → 값 손실 없음)
- `[W-1:0] var = expr` 작성 시: max(expr) < 2^W 검증 필수 (파라미터 전 범위 대상)
- `$clog2(N) ≠ floor(log2(N))` — N이 2^k가 아니면 1 차이 → 비트 부족 버그
- 코드 생성/리뷰 시 모든 sized 변수에 대해 반복 검증

BAD/GOOD 예제, $clog2 vs custom log2 비교 테이블, 검증 체크리스트, 추가 위험 패턴: `references/synthesis-check.md` > Bit-Width Safety 참조

### Reset 패턴

#### ⚠️ Sensitivity List 규칙

리셋 사용 O → `@(posedge i_clk or negedge i_rst_n)`, 리셋 사용 X → `@(posedge i_clk)`

#### 리셋이 필요한 레지스터 (비동기 리셋)

```verilog
// 상태 레지스터, 제어 신호 등 - 리셋 필요
always_ff @(posedge i_clk or negedge i_rst_n) begin
    if (!i_rst_n) begin
        r_state <= S_IDLE;
        r_valid <= 1'b0;
    end else begin
        r_state <= c_next_state;
        r_valid <= i_valid;
    end
end
```

#### 리셋이 불필요한 레지스터 (리셋 없음)

```verilog
// 데이터 경로, 파이프라인 데이터 등 - 리셋 불필요
always_ff @(posedge i_clk) begin
    r_data_d1 <= i_data;
    r_data_d2 <= r_data_d1;
end
```

동기 리셋: 글리치 민감한 환경/고속 설계 시 사용 — `@(posedge i_clk)` + `if (!i_rst_n)` 구조

### 리셋 필요 여부 판단

| 레지스터 타입 | 리셋 필요 | 이유 |
|--------------|----------|------|
| FSM 상태 | ✅ 필요 | 초기 상태 보장 |
| 제어 신호 (valid, ready) | ✅ 필요 | 잘못된 트랜잭션 방지 |
| 카운터 | ✅ 필요 | 초기값 보장 |
| 데이터 경로 | ❌ 불필요 | valid로 게이팅됨 |
| 파이프라인 데이터 | ❌ 불필요 | valid로 게이팅됨 |
| 지연 레지스터 | ❌ 불필요 | 단순 지연 용도 |

### CDC (Clock Domain Crossing)

#### CDC 방식 선택 테이블

| 조건 | 방식 | 설명 |
|------|------|------|
| Slow→Fast, 1-bit level | **2FF Sync** | 단순, 2 cycle 지연 |
| Slow→Fast, 1-bit pulse | **Pulse Sync** | 펄스 확장 후 2FF |
| Fast→Slow, 1-bit | **Handshake** | Req/Ack로 확인 |
| Multi-bit (순차적) | **Gray + 2FF** | 포인터, 카운터 |
| Multi-bit (스트림) | **Async FIFO** | 데이터 버퍼링 |

CDC 방식 선택 가이드 및 상세 구현: `references/cdc-patterns.md` 참조

---

## 2. Always 블록 분리 체계

### 블록 유형

| 블록 유형 | 용도 | 문법 | 합성 결과 | Prefix |
|----------|------|------|----------|--------|
| `always_ff` | 순차 로직 (레지스터) | `@(posedge i_clk)` | Flip-flop | `r_` |
| `always_comb` | 조합 로직 | `always_comb` | Combinational | `c_` |
| `always_latch` | 래치 (피해야 함) | `always_latch` | Latch | - |

### 분리 원칙

**최우선 기준: 가독성과 회로 동작 파악 용이성**

**필수:**
- 동일 신호를 여러 always에서 할당 금지
- always_ff에서는 `<=` (non-blocking)
- always_comb에서는 `=` (blocking)

**권장 (유연 적용):** 하나의 always → 하나의 출력, 순차/조합 로직 분리

### 핵심 철학: 가독성이 최우선

"제어구조 분리"나 "순차/조합 분리"는 가독성을 위한 **수단**이지 목적이 아님. 전체 회로의 동작을 한눈에 파악할 수 있는가? 관련 로직이 흩어져서 오히려 이해하기 어려워지지 않는가? — 분리가 가독성을 해친다면 합치는 것이 정답.

### 판단 기준

| 질문 | YES → | NO → |
|------|-------|------|
| 하나의 always로 작성 시 회로 동작이 한눈에 파악되는가? | 합쳐서 작성 | 분리 고려 |
| 분리하면 관련 로직이 흩어져서 이해하기 어려워지는가? | 합쳐서 작성 | 분리 고려 |
| 코드 리뷰어가 전체 동작을 쉽게 이해할 수 있는가? | 현재 방식 유지 | 개선 필요 |

### 상황별 가이드

| 상황 | 권장 스타일 | 이유 |
|------|-------------|------|
| 단순 로직, 신호 간 관계 밀접 | **통합형** | 전체 동작 한눈에 파악 |
| FSM capture, Pipeline | **통합형** | 단순 구조, 관련성 높음 |
| 관련 카운터 그룹 | **통합형** | 논리적 연관, 유사 구조 |
| 복잡한 조건 로직 | 분리형 권장 | 각 로직 독립적 이해 |
| 서로 다른 기능 블록 | **반드시 분리** | 모듈성, 재사용성 |

**선택 가이드:**
- 로직이 단순하고 신호 간 관계가 밀접 → **통합형** 선호
- 로직이 복잡하거나 독립적으로 변경될 가능성 → **분리형** 선호

허용 사례(통합형 1-4) 및 분리 권장 코드 예제: `references/always-block-patterns.md` 참조

---

## 3. 사이클 분석 (Cycle Analysis)

### 개념

사이클 분석은 **각 신호가 어느 클럭 에지에서 값이 결정되는지** 추적하는 것.
- 조합 로직: 같은 사이클 내에서 즉시 반영
- 순차 로직: 다음 클럭 에지에서 반영 (1 cycle delay)

### 사이클 표기법

코드 작성/분석 시 주석으로 사이클 명시: `[Cycle N]`, `[Cycle N+1]`, `[same]`

전체 파이프라인 예시, 타이밍 다이어그램, 표기법 상세: `references/cycle-analysis.md` 참조

### 사이클 분석 체크리스트

| 체크 | 항목 |
|------|------|
| ☐ | 각 레지스터의 유효 사이클이 명시되었는가? [→§3] |
| ☐ | 조합 로직이 같은 사이클임을 표시했는가? [→§3] |
| ☐ | 파이프라인 단계별 지연이 일치하는가? [→§3] |
| ☐ | valid/data 신호의 사이클이 정렬되었는가? [→§3] |

---

## 4. Signal Naming Convention

### Prefix 규칙

| Prefix | 용도 | 사이클 특성 | 예시 |
|--------|------|------------|------|
| `i_` | 입력 포트 | Cycle N (외부 결정) | `i_data`, `i_valid` |
| `i_` | **클럭/리셋** | 입력 신호 | `i_clk`, `i_rst_n` |
| `o_` | 출력 포트 | Cycle N+k (내부 결정) | `o_result`, `o_ready` |
| `w_` | 와이어 (내부 연결) | 연결용 | `w_adder_out` |
| `r_` | 레지스터 (순차) | **Cycle N+1** | `r_state`, `r_counter` |
| `c_` | 조합 로직 출력 | **Same cycle** | `c_next_state`, `c_sum` |

### ⚠️ Clock/Reset 네이밍

**클럭과 리셋도 입력 신호이므로 `i_` prefix 사용:**

```verilog
module my_module (
    input  wire        i_clk,       // 클럭: i_ prefix
    input  wire        i_rst_n,     // 리셋: i_ prefix (active low)
    input  wire [7:0]  i_data,
    output wire [7:0]  o_result
);
```

### Boundary Scan Chain (BSC) 네이밍

**JTAG Boundary Scan Chain 블록의 통과 신호에는 `_a`/`_z` postfix 사용:**

| Postfix | 용도 | 설명 |
|---------|------|------|
| `_a` | BSC 입력 | Boundary Scan Chain으로 들어오는 신호 |
| `_z` | BSC 출력 | Boundary Scan Chain에서 나가는 신호 |

**주의**: `_a`/`_z`는 BSC 모듈 포트에서만 사용. 신호 방향(i_/o_)은 원래 의미 유지.

상세 예시: `references/naming-examples.md` BSC 섹션 참조

---

## 5. Module/Parameter Naming

### 규칙

| 항목 | 스타일 | 예시 |
|------|--------|------|
| **Module** | lowercase_with_underscores | `uart_rx`, `adc_controller` |
| **Parameter** | UPPER_CASE | `DATA_WIDTH`, `FIFO_DEPTH` |
| **Instance** | u_<module_name> | `u_uart_rx`, `u_fifo` |

### 예시

```verilog
module fifo_buffer #(
    parameter DATA_WIDTH = 8,        // UPPER_CASE
    parameter FIFO_DEPTH = 16,
    parameter ALMOST_FULL_THRESH = 12
)(
    input  wire                  i_clk,
    input  wire                  i_rst_n,
    input  wire [DATA_WIDTH-1:0] i_wdata,
    output wire [DATA_WIDTH-1:0] o_rdata
);
```

---

## 6. Top Integration Wire Naming

### 규칙

**형식**: `w_<source_instance>_<output_port_name>`

- 보내는 쪽 인스턴스명 + 출력 포트명 **전체** 포함
- 포트명의 `o_` prefix도 그대로 유지
- **예외**: Top 출력으로 직결되는 신호는 `o_` 포트명 그대로 연결

상세 예시: `references/naming-examples.md` Top Integration 섹션 참조

### 네이밍 예시

| 인스턴스 | 출력 포트 | 와이어 이름 |
|---------|----------|------------|
| u_proc | o_result | `w_u_proc_o_result` |
| u_proc | o_done | `w_u_proc_o_done` |
| u_fifo | o_rdata | `w_u_fifo_o_rdata` |
| u_uart | o_tx_data | `w_u_uart_o_tx_data` |

---

## 7. FSM Implementation

### 기본 규칙

| 항목 | 규칙 |
|------|------|
| **스타일** | 2-process (작성 시) |
| **타입** | Mealy machine 기본 |
| **인코딩** | One-hot (< 8 states), Binary (≥ 8 states) |
| **타이밍 크리티컬** | 출력 레지스터링 추가 |

### FSM 작성/분석 규칙

- **작성 시**: 항상 2-process 패턴만 사용 (일관성, 코드 리뷰 용이, 합성 예측 가능)
- **분석 시**: 모든 FSM 패턴 인식 (1/2/3-process, 다양한 코딩 스타일)

### 타이밍 크리티컬: 출력 레지스터링

Mealy 출력이 타이밍 크리티컬하면 `r_result_reg <= c_result;` 로 1 cycle 추가.

전체 FSM 템플릿, 2/3-process 패턴, 출력 레지스터링: `references/fsm-patterns.md` 참조
FSM 사이클 다이어그램: `references/fsm-patterns.md` 참조

---

## 8. Verification 연계

### SVA Assertion

```verilog
// 프로토콜 체크
assert property (@(posedge i_clk) disable iff (!i_rst_n)
    i_valid |-> ##[1:10] o_ready
) else $error("Ready timeout!");

// FIFO overflow 방지
assert property (@(posedge i_clk) disable iff (!i_rst_n)
    (r_count == FIFO_DEPTH) |-> !i_write
) else $error("FIFO overflow!");
```

### Coverage 분류

| 분류 | 생성 방식 | 소스 |
|------|----------|------|
| Code Coverage | 자동 (implicit) | RTL 구현 |
| Functional Coverage | 수동 (explicit) | 스펙/요구사항 |
| Assertion Coverage | 수동 (explicit) | 프로토콜/타이밍 |

### Coverage 핵심 원칙

1. Coverage는 observation 기반 — stimulus가 아닌 DUT 출력/상태 관찰
2. Coverage는 check 통과 시에만 유효 — 오동작 시 sampling 무의미
3. 100% code coverage ≠ 100% 기능 검증 (역도 마찬가지) — 상호 보완 필수
4. Bin은 명시적 설계 — auto-bin 지양, 분석 가능한 레이블 부여
5. Cross coverage에서 불가능 조합은 ignore_bins로 제거

### Coverage 워크플로우

1. **스펙 분석** → 기능 요구사항 추출, 디자인 유형 파악
2. **Testplan 작성** → spec→요구사항→coverage element 매핑
3. **Coverage 모델 구현** → covergroup/assertion 코딩
4. **시뮬레이션 실행** → coverage 수집
5. **Hole Analysis** → 미달 항목 원인 분석 (stimulus 부족 / 버그 / unreachable)
6. **Coverage Closure** → stimulus 조정, exclusion, regression 최적화, 반복

### Coverage 목표

| 항목 | 목표 |
|------|------|
| Code Coverage | 95% |
| Functional Coverage | 90% |

Covergroup 예제 및 문법 상세: `references/covergroup-patterns.md` 참조
Coverage 이론, testplan, closure 프로세스: `references/coverage-methodology.md` 참조
실전 예제 (APB3, UART, Datapath, SoC): `references/coverage-examples.md` 참조

---

## 9. 코드 생성 워크플로우

RTL 코드 작성 시 다음 5단계를 따른다:

1. **요구사항 분석** — 입출력 정의, 타이밍 요구사항 파악
2. **사이클 맵 작성** — 어떤 처리가 몇 사이클에 발생하는지 명시
3. **블록 분할** — always 블록별 책임 할당
4. **코드 작성** — 사이클 주석과 함께 작성
   - **4.5 Bit-Width 검증** [→§1.BitWidth] — 모든 sized 변수: max(value) < 2^W 확인, localparam/parameter 파생 관계 교차 검증
5. **합성 체크** — `references/synthesis-check.md` 참조

---

## 10. 코드 리뷰 체크리스트

코드 리뷰 시 `references/review-checklist.md` 참조. 핵심 항목:

### 합성 관련
- [ ] Latch 유발 코드 없음 (기본값 할당 또는 if/case 완전성) [→§1,§7]
- [ ] 리셋 정책: 제어 신호=리셋 있음, 데이터 경로=리셋 없음 [→§1.Reset]
- [ ] CDC: Slow→Fast=2FF/Pulse Sync, Fast→Slow=Handshake [→§1.CDC]
- [ ] Blocking/Non-blocking 할당 적절성 [→§2]
- [ ] Bit-Width Safety: sized 변수의 max value < 2^W, localparam unsized 권장 [→§1.BitWidth]

### 타이밍 관련
- [ ] 사이클 타이밍 정확성 [→§3]
- [ ] data/valid 정렬 (리셋 정책에 맞게 분리) [→§3,§1.Reset]
- [ ] 타이밍 크리티컬 경로 레지스터링 [→§7]

### 코딩 스타일
- [ ] 네이밍 규칙 준수 (i_, o_, w_, r_, c_, Top wire, BSC) [→§4,§5,§6]
- [ ] always 블록: 필수 규칙 준수 + 유연성 원칙 (가독성 최우선) [→§2]
- [ ] 사이클 주석 명시 [→§3]

### 기능 관련
- [ ] 리셋 시 초기값 정확 [→§1.Reset]
- [ ] 에지 케이스 처리 (오버플로우, 언더플로우)
- [ ] FSM: 2-process, Mealy 기본, One-hot(<8)/Binary(≥8) [→§7]

---

## 11. Verilator Lint

### 환경 설정

Verilator는 MSYS2를 통해 설치되어 있음:

```bash
# MSYS2 bash를 통해 Verilator 실행
C:/msys64/usr/bin/bash.exe -lc "verilator --version"

# Lint 실행
C:/msys64/usr/bin/bash.exe -lc "cd '<project_path>' && verilator --lint-only -Wall --top-module <top_module> -I<include_paths> <files>"
```

### 주요 Warning 유형

| Warning | 심각도 | 설명 |
|---------|--------|------|
| IMPLICIT | 🔴 Critical | 미선언 신호 사용 |
| PINMISSING | 🟠 Warning | 인스턴스 포트 미연결 |
| WIDTHTRUNC | 🟠 Warning | 비트폭 절삭 |
| WIDTHEXPAND | 🟠 Warning | 비트폭 확장 |
| PINCONNECTEMPTY | 🟡 Info | 빈 포트 연결 (의도적일 수 있음) |
| TIMESCALEMOD | 🟡 Info | timescale 불일치 |
| EOFNEWLINE | 🟡 Info | 파일 끝 줄바꿈 누락 |

### Warning 억제

```verilog
// 특정 라인 억제
/* verilator lint_off PINCONNECTEMPTY */
.o_unused_port  (),
/* verilator lint_on PINCONNECTEMPTY */

// 파일 전체 억제
/* verilator lint_off UNUSED */
```

---

## 참조 파일

- `references/naming-examples.md` - 네이밍 상세 예시
- `references/fsm-patterns.md` - FSM 설계 패턴 상세
- `references/cdc-patterns.md` - CDC 처리 패턴
- `references/synthesis-check.md` - 합성 체크리스트
- `references/cycle-analysis.md` - 사이클 분석 상세
- `references/review-checklist.md` - 코드 리뷰 체크리스트
- `references/always-block-patterns.md` - Always 블록 허용/분리 사례 코드
- `references/covergroup-patterns.md` - SV covergroup/assertion 문법 패턴
- `references/coverage-methodology.md` - Coverage 이론, testplan, closure
- `references/coverage-examples.md` - Coverage 실전 예제
- `references/consistency-map.md` - 원칙별 반영 위치 맵 (수정 시 영향 범위 확인용)

## Cross-Skill 참조

- FPGA 합성, iCEcube2/Radiant 구현, 비트스트림 → `lattice-fpga` skill
- UVM 테스트벤치, agent/env 설계, RAL → `uvm-verification` skill
- Verilog-A 아날로그 모델, Mixed-signal 인터페이스 → `verilog-a` skill
- RTL-TB 인터페이스, 듀얼탑, Reference Model, Scoreboard → `chip-verification` skill
