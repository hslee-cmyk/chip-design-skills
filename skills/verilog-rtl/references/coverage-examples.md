# Coverage Examples

## 1. Bus Protocol Coverage — APB3 Example

### 1.1 Protocol Monitor Interface

APB3 프로토콜 모니터는 세 가지 카테고리의 coverage/assertion을 포함:

| 카테고리 | 목적 | 구현 방식 |
|---------|------|----------|
| Unknown Signal Detection | 신호 X/Z 검출 | Assertion (SIGNAL_VALID) |
| Timing Relationship | 프로토콜 타이밍 준수 | Assertion + Cover Property |
| Functional Coverage | 전송 유형/주소 분포 | Covergroup (Hybrid) |

### 1.2 Unknown Signal Assertions

```systemverilog
// X/Z 검출 — 모든 주요 신호에 적용
property SIGNAL_VALID(signal);
    @(posedge PCLK) disable iff (!PRESETn)
    !$isunknown(signal);
endproperty

assert property (SIGNAL_VALID(PSEL))    else $error("PSEL unknown");
assert property (SIGNAL_VALID(PENABLE)) else $error("PENABLE unknown");
assert property (SIGNAL_VALID(PWRITE))  else $error("PWRITE unknown");
assert property (SIGNAL_VALID(PADDR))   else $error("PADDR unknown");

// 조건부 — PSEL 활성 시에만 데이터 유효 검사
property CONTROL_SIGNAL_VALID(signal);
    @(posedge PCLK) disable iff (!PRESETn)
    |PSEL |-> !$isunknown(signal);
endproperty

assert property (CONTROL_SIGNAL_VALID(PWDATA)) else $error("PWDATA unknown during access");
```

### 1.3 Timing Relationship Assertions

```systemverilog
// PENABLE은 setup phase 후 한 사이클만 활성
property PENABLE_DEASSERTED;
    @(posedge PCLK) disable iff (!PRESETn)
    $fell(|PSEL) |-> !PENABLE;
endproperty
assert property (PENABLE_DEASSERTED);

// PSEL → PENABLE 한 사이클 후 활성
property PSEL_TO_PENABLE;
    @(posedge PCLK) disable iff (!PRESETn)
    $rose(|PSEL) |-> ##1 PENABLE;
endproperty
assert property (PSEL_TO_PENABLE);

// Transfer 완료 시퀀스
sequence END_OF_APB_TRANSFER;
    @(posedge PCLK) |PSEL && PENABLE && PREADY;
endsequence
```

### 1.4 Hybrid Coverage 패턴 (Transfer 완료 시 Sampling)

```systemverilog
// Slave별 covergroup array
covergroup cg_apb_access with function sample(
    bit [ADDR_WIDTH-1:0] addr,
    bit                  write,
    bit [2:0]            prot
);
    option.per_instance = 1;

    cp_addr: coverpoint addr {
        bins low_region  = {[0:32'h0FFF]};
        bins mid_region  = {[32'h1000:32'h7FFF]};
        bins high_region = {[32'h8000:32'hFFFF]};
    }

    cp_rw: coverpoint write {
        bins read  = {0};
        bins write = {1};
    }

    cp_prot: coverpoint prot {
        bins normal     = {3'b000};
        bins privileged = {3'b001};
    }

    cx_addr_rw: cross cp_addr, cp_rw;
    cx_addr_prot: cross cp_addr, cp_prot;
endgroup

// Slave별 인스턴스
cg_apb_access apb_cg[NUM_SLAVES];

initial begin
    foreach (apb_cg[i])
        apb_cg[i] = new($sformatf("slave_%0d", i));
end

// Transfer 완료 시 해당 slave만 sampling
cover property (END_OF_APB_TRANSFER) begin
    int slave_id = get_slave_id(PADDR);
    apb_cg[slave_id].sample(PADDR, PWRITE, PPROT);
end
```

**핵심**: Transfer 완료 assertion 성공 후에만 covergroup을 sampling → observation 기반 + check 통과 시에만 유효

---

## 2. Block-Level Coverage — UART Example

### 2.1 TX Channel Coverage

UART TX는 LCR(Line Control Register) 설정 조합이 핵심:

```systemverilog
covergroup cg_uart_tx with function sample(
    bit [1:0] word_length,  // 5,6,7,8 bit
    bit       stop_bits,    // 1 or 2
    bit       parity_en,
    bit       parity_type   // even/odd
);
    option.per_instance = 1;

    cp_word_len: coverpoint word_length {
        bins bits_5 = {2'b00};
        bins bits_6 = {2'b01};
        bins bits_7 = {2'b10};
        bins bits_8 = {2'b11};
    }

    cp_stop: coverpoint stop_bits {
        bins one_stop = {0};
        bins two_stop = {1};
    }

    cp_parity: coverpoint {parity_en, parity_type} {
        bins no_parity   = {2'b00, 2'b01};  // parity disabled
        bins even_parity = {2'b10};
        bins odd_parity  = {2'b11};
    }

    // 모든 설정 조합 Cross
    cx_tx_config: cross cp_word_len, cp_stop, cp_parity;
endgroup
```

### 2.2 RX Channel Coverage

```systemverilog
// Error-free: TX와 동일 구조
covergroup cg_uart_rx_normal with function sample(
    bit [1:0] word_length, bit stop_bits, bit parity_en, bit parity_type
);
    // TX와 동일한 coverpoint/cross 구조
    // ... (생략 — TX 패턴 재사용)
endgroup

// Error coverage: LSR(Line Status Register) 기반
covergroup cg_uart_rx_error with function sample(bit [4:0] lsr_status);
    cp_lsr: coverpoint lsr_status {
        bins overrun_err  = {5'b00010};
        bins parity_err   = {5'b00100};
        bins framing_err  = {5'b01000};
        bins break_int    = {5'b10000};
        bins multi_err    = {[5'b00110:5'b11110]};  // 복합 에러
        ignore_bins no_err = {5'b00000};
    }
endgroup
```

### 2.3 Interrupt Coverage

```systemverilog
// Interrupt Enable 조합 (IER의 4bit → 15개 non-zero 조합)
covergroup cg_int_enable with function sample(bit [3:0] ier);
    cp_ier: coverpoint ier {
        ignore_bins disabled = {4'b0000};  // 모두 비활성은 제외
        // 나머지 15개 조합 = auto bins 또는 명시적
    }
endgroup

// Interrupt Enable × Source Cross
covergroup cg_int_enable_src with function sample(bit [3:0] ier, bit [3:0] iir);
    cp_ier: coverpoint ier {
        ignore_bins disabled = {4'b0000};
    }

    cp_iir: coverpoint iir[3:1] {  // interrupt ID
        bins modem_status = {3'b000};
        bins tx_empty     = {3'b001};
        bins rx_data      = {3'b010};
        bins rx_line_stat = {3'b011};
        bins char_timeout = {3'b110};
    }

    cx_en_src: cross cp_ier, cp_iir {
        // 비활성 인터럽트 소스 제거
        ignore_bins rx_disabled = binsof(cp_ier) intersect {4'b???0} &&
                                  binsof(cp_iir.rx_data);
        ignore_bins tx_disabled = binsof(cp_ier) intersect {4'b??0?} &&
                                  binsof(cp_iir.tx_empty);
    }
endgroup

// Modem Interrupt × Loopback Cross
covergroup cg_modem_int with function sample(bit [3:0] msr, bit loopback);
    cp_msr: coverpoint msr {
        wildcard bins dcts = {4'b???1};
        wildcard bins ddsr = {4'b??1?};
        wildcard bins teri = {4'b?1??};
        wildcard bins ddcd = {4'b1???};
    }

    cp_loopback: coverpoint loopback {
        bins normal   = {0};
        bins loopback = {1};
    }

    cx_modem_loop: cross cp_msr, cp_loopback;
endgroup
```

### 2.4 Baud Rate Divisor Coverage

```systemverilog
covergroup cg_baud_divisor with function sample(bit [15:0] divisor);
    cp_divisor: coverpoint divisor {
        // Powers of 2
        bins pow2[] = {1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024};
        // 경계값
        bins min_val = {16'h0001};  // 최소 (0은 invalid)
        bins max_val = {16'hFFFF};  // 최대
        // 표준 baud rate 해당 divisor (50MHz 클럭 기준 예시)
        bins baud_9600   = {16'd326};
        bins baud_115200 = {16'd27};
    }
endgroup
```

### 2.5 Register Access Coverage

```systemverilog
covergroup cg_reg_access with function sample(bit [2:0] addr, bit write);
    cp_addr: coverpoint addr {
        bins RBR_THR = {3'h0};  // Read: RBR, Write: THR
        bins IER     = {3'h1};
        bins IIR_FCR = {3'h2};  // Read: IIR, Write: FCR
        bins LCR     = {3'h3};
        bins MCR     = {3'h4};
        bins LSR     = {3'h5};
        bins MSR     = {3'h6};
        bins SCR     = {3'h7};
    }

    cp_rw: coverpoint write {
        bins read  = {0};
        bins write = {1};
    }

    cx_reg_rw: cross cp_addr, cp_rw {
        // Read-only 레지스터에 write 제외
        ignore_bins no_write_iir = binsof(cp_addr.IIR_FCR) && binsof(cp_rw.read);
        ignore_bins no_read_fcr  = binsof(cp_addr.IIR_FCR) && binsof(cp_rw.write);
        ignore_bins no_write_lsr = binsof(cp_addr.LSR) && binsof(cp_rw.write);
        ignore_bins no_write_msr = binsof(cp_addr.MSR) && binsof(cp_rw.write);
    }
endgroup
```

---

## 3. Datapath Coverage — BiQuad IIR Filter

### 3.1 Covergroup Wrapper Pattern

Covergroup을 class wrapper로 감싸 모듈화 및 재사용 가능:

```systemverilog
class biquad_coverage;

    // 모드별 별도 covergroup
    covergroup cg_lowpass with function sample(bit [15:0] coeff, bit [7:0] freq_bin);
        cp_coeff: coverpoint coeff {
            bins low_gain  = {[0:16'h3FFF]};
            bins mid_gain  = {[16'h4000:16'hBFFF]};
            bins high_gain = {[16'hC000:16'hFFFF]};
        }
        cp_freq: coverpoint freq_bin {
            bins dc       = {0};
            bins low_freq = {[1:31]};
            bins mid_freq = {[32:95]};
            bins hi_freq  = {[96:127]};
        }
        cx_coeff_freq: cross cp_coeff, cp_freq;
    endgroup

    covergroup cg_highpass with function sample(bit [15:0] coeff, bit [7:0] freq_bin);
        // 유사 구조 (high-pass 특성 bin)
        cp_coeff: coverpoint coeff;
        cp_freq:  coverpoint freq_bin;
        cx_coeff_freq: cross cp_coeff, cp_freq;
    endgroup

    covergroup cg_bandpass with function sample(bit [15:0] coeff, bit [7:0] freq_bin);
        cp_coeff: coverpoint coeff;
        cp_freq:  coverpoint freq_bin;
        cx_coeff_freq: cross cp_coeff, cp_freq;
    endgroup

    function new(string name = "biquad_coverage");
        cg_lowpass  = new();
        cg_highpass = new();
        cg_bandpass = new();
    endfunction
endclass
```

### 3.2 Co-efficient × Frequency Cross

```systemverilog
// Coefficient 값을 인자로 받아 모드별 sampling
function void sample_coverage(bit [15:0] coeff_a1, bit [15:0] coeff_b0, bit [1:0] mode);
    // Concatenated coefficient → 의미 있는 범위로 추상화
    bit [15:0] coeff_combined = {coeff_a1[15:8], coeff_b0[15:8]};
    bit [7:0]  freq_bin = determine_freq_bin(coeff_a1, coeff_b0);

    case (mode)
        2'b00: cg_lowpass.sample(coeff_combined, freq_bin);
        2'b01: cg_highpass.sample(coeff_combined, freq_bin);
        2'b10: cg_bandpass.sample(coeff_combined, freq_bin);
    endcase
endfunction
```

★ UVM register model 연동 시 `reg_model.*.get_mirrored_value()`로 coefficient 획득 → uvm-verification > coverage-guide.md §2

---

## 4. SoC Coverage Strategy

### 4.1 Use Model Flow (DITL — Day-In-The-Life)

SoC coverage는 실제 사용 시나리오 기반:

```
Phase 1: Setup/Config
  → Boot sequence coverage
  → Register initialization 조합
  → Clock/Power domain 설정

Phase 2: Traffic
  → 정상 데이터 전송 패턴
  → 다중 마스터 동시 접근
  → DMA 전송 시나리오

Phase 3: Unexpected Events
  → 인터럽트 도중 전송
  → 에러 주입 및 복구
  → 전원 모드 전환 중 이벤트
```

### 4.2 Block Reuse

```
Block-level testplan:
├── UART coverage (cg_uart_tx, cg_uart_rx, cg_int, cg_reg)
├── SPI coverage
└── I2C coverage

SoC-level testplan:
├── import: UART coverage (block reuse)
│   └── exclusion: standalone-only bins
├── import: SPI coverage
├── SoC-specific coverage
│   ├── cg_multi_master (DMA × CPU 동시 접근)
│   ├── cg_interrupt_nesting (중첩 인터럽트)
│   └── cg_power_mode (저전력 모드 전이)
└── Use-model coverage (DITL)
```

### 4.3 SoC Coverage Covergroup 예시

```systemverilog
// 다중 마스터 접근 Coverage
covergroup cg_multi_master with function sample(
    bit [1:0] master_id,
    bit [3:0] slave_id,
    bit       write
);
    cp_master: coverpoint master_id {
        bins cpu  = {0};
        bins dma  = {1};
        bins dbg  = {2};
    }

    cp_slave: coverpoint slave_id {
        bins sram  = {0};
        bins flash = {1};
        bins uart  = {2};
        bins spi   = {3};
    }

    cp_rw: coverpoint write {
        bins read  = {0};
        bins write = {1};
    }

    cx_master_slave: cross cp_master, cp_slave, cp_rw {
        // Debug port는 flash write 불가
        ignore_bins no_dbg_flash_wr = binsof(cp_master.dbg) &&
                                       binsof(cp_slave.flash) &&
                                       binsof(cp_rw.write);
    }
endgroup
```

---

## 5. Requirements Writing Guidelines

### 한 행에 하나의 요구사항

```
| Tag    | Description                                         | Type       |
|--------|-----------------------------------------------------|------------|
| UART-001 | TX: 5/6/7/8 bit word length 각각 전송 성공        | Covergroup |
| UART-002 | TX: 1/2 stop bit 각각 전송 성공                    | Covergroup |
| UART-003 | TX: word_length × stop_bits × parity 전체 조합     | Cross      |
| UART-004 | RX: 수신 데이터 정합성 (no error)                   | Assertion  |
| UART-005 | RX: overrun/parity/framing error 각각 발생 및 감지   | Covergroup |
```

### 3관점 기술

각 요구사항을 **Generation / Checking / Coverage** 관점에서 기술:

| 관점 | UART-003 예시 |
|------|-------------|
| **Generation** | LCR 레지스터에 word_length/stop/parity 설정 후 TX 데이터 전송 |
| **Checking** | RX 측 수신 데이터가 TX 데이터와 일치하는지 scoreboard 비교 |
| **Coverage** | cx_tx_config cross에서 모든 조합 bin hit 확인 |

### 고유 태그

- 알파벳+숫자 조합: `UART-001`, `APB-T-003`, `SOC-INT-012`
- 계층 구조 반영: `BLOCK.FEATURE.NUMBER`
- Traceable: testplan → coverage element → 시뮬레이션 결과 추적 가능
