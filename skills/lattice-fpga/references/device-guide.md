# Lattice Device Guide (iCE40, MachXO2, XP2)

## 디바이스 비교

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          디바이스 비교                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  iCE40 Ultra    iCE40UP        MachXO2           LatticeXP2             │
│  ─────────      ─────────      ─────────         ─────────              │
│  초저전력       초저전력       Instant-on        고밀도+Flash           │
│  ~71µA stby     ~75µW          ~20mW             ~100mW                 │
│  3.5K LUT       5.3K LUT       6.9K LUT          40K LUT                │
│  iCEcube2       Radiant        Diamond           Diamond                │
│                                                                          │
│  용도:          용도:          용도:             용도:                  │
│  - 모바일       - 웨어러블     - 전원 시퀀싱     - 복잡 로직           │
│  - 센서관리     - IoT 센서     - 시스템 관리     - DSP 처리            │
│  - IrDA/LED     - 저전력 AI    - 브릿지/변환     - 비휘발 저장         │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## iCE40 Ultra (iCE5LP) — iCEcube2

### 리소스

| 디바이스 | LUT | EBR Blocks | EBR Bits | DSP (MAC16) | PLL | I2C/SPI | Osc |
|----------|-----|-----------|----------|-------------|-----|---------|-----|
| iCE5LP1K | 1,100 | 16 | 64Kb | 2 | 1 | 1/1 | HF+LF |
| iCE5LP2K | 2,048 | 20 | 80Kb | 4 | 1 | 2/2 | HF+LF |
| iCE5LP4K | 3,520 | 20 | 80Kb | 4 | 1 | 2/2 | HF+LF |

### 패키지

| 패키지 | 볼/핀 수 | Pitch | 크기 | User I/O |
|--------|---------|-------|------|----------|
| SWG36 | 36-ball WLCSP | 0.35mm | 2.078 x 2.078 mm | 26 |
| CM36 | 36-ball ucfBGA | 0.40mm | 2.5 x 2.5 mm | 26 |
| SG48 | 48-pin QFN | 0.50mm | 7.0 x 7.0 mm | 39 |

### 특징
- **초저전력**: 40nm LP 공정, 대기 ~71µA typ
- **NVCM**: 비휘발성 설정 메모리 내장 (외부 Flash 불필요)
- **온칩 오실레이터**: HFOSC 48MHz (÷2/4/8), LFOSC 10kHz
- **하드 IP**: I2C, SPI 컨트롤러 내장
- **LED 드라이버**: 3x 24mA RGB LED sink + 1x 500mA IR LED sink
- **DSP**: 16x16 MAC, 8x8 독립 연산 가능
- **EBR**: 4Kb 블록, 256x16/512x8/1024x4/2048x2 설정
- **I/O Bank**: 3개 (Bank 0 상단, Bank 1/2 하단), 각각 독립 VCCIO
- **Embedded PWM IP**: iCE5LP1K/2K에 내장 (4K는 미포함)

### I/O 표준 및 차동 입력

| 표준 | 입력 | 출력 | VCCIO |
|------|------|------|-------|
| LVCMOS 3.3V | O | O | 3.3V |
| LVCMOS 2.5V | O | O | 2.5V |
| LVCMOS 1.8V | O | O | 1.8V |
| LVCMOS 1.2V | O | - | 1.2V |
| SB_LVDS_INPUT | O (차동비교기) | - | Bank 의존 |

- 차동 출력은 LVCMOS 2개 + 외부 저항 네트워크로 구성 (TN1253 참조)
- Pull-up: per-pin 개별 설정 가능

### iCEcube2 프로젝트 구조 및 워크플로우

```
icecube2_proj/
├── source/           # RTL 소스
├── constraint/       # .pcf 핀 제약
├── synthesis/        # Synplify Pro 결과
├── placer/           # Place 결과
├── router/           # Route 결과
└── bitmap/           # 비트스트림 (.bin)
```

```
iCEcube2 워크플로우:
1. New Project → Device: iCE5LP4K, Package: SWG36/CM36/SG48
2. Add RTL sources (Verilog)
3. Add .pcf constraint file
4. Synplify Pro (합성) → Netlist
5. Place & Route
6. Generate Bitmap → .bin
7. Program via Diamond Programmer 또는 iceprog (FTDI)
```

### PCF 예시 (iCEcube2)

```
# iCE5LP4K-SWG36 핀 할당
set_io i_rst_n B1
set_io i_scl D2
set_io i_sdaIn F6
set_io o_sdaOut A2
set_io i_pcmIn F5
set_io i_pcmSync E3
set_io i_backTel_p E6
set_io o_askData B4
set_io o_refClk B2
set_io o_refClkInv F4
set_io o_backTel_pwr_en E5
set_io i_deep_slp_en F3
set_io i_dyn_slp_en D5
set_io i_earpiece_det_n E2
set_io o_serial_tp_out D6
```

### 하드 IP 프리미티브

```verilog
// 1. 내부 오실레이터 (48MHz ÷2 = 24MHz)
SB_HFOSC #(.CLKHF_DIV("0b01")) u_osc (
    .CLKHFEN(1'b1),      // enable (100us power-up 후)
    .CLKHFPU(1'b1),      // power up
    .CLKHF(rootClk)      // 24MHz 출력
);

// 2. SB_IO - LVDS 차동 입력 (SB_LVDS_INPUT)
SB_IO #(
    .PIN_TYPE(6'b000001),           // No output, Direct input
    .IO_STANDARD("SB_LVDS_INPUT")
) u_diff_in (
    .PACKAGE_PIN(diff_p),           // P-side 핀 (N-side 자동 예약)
    .D_IN_0(diff_result),           // 차동 비교 결과
    .LATCH_INPUT_VALUE(1'b0),
    .CLOCK_ENABLE(1'b0),
    .INPUT_CLK(1'b0),
    .OUTPUT_CLK(1'b0),
    .OUTPUT_ENABLE(1'b0),
    .D_OUT_0(1'b0),
    .D_OUT_1(1'b1),
    .D_IN_1()
);

// 3. SB_IO_OD - Open-Drain 출력 (I2C SDA 등)
SB_IO_OD #(
    .PIN_TYPE(6'b101001),           // Tristate output, Direct input
    .NEG_TRIGGER(1'b0)
) u_od_out (
    .PACKAGEPIN(sda_pin),
    .OUTPUTENABLE(~sda_out),        // 0→Hi-Z(pull-up), 1→Low 구동
    .DOUT0(1'b0),
    .DOUT1(1'b1),
    .LATCHINPUTVALUE(1'b0),
    .CLOCKENABLE(1'b0),
    .INPUTCLK(1'b0),
    .OUTPUTCLK(1'b0),
    .DIN0(),
    .DIN1()
);

// 4. SB_IO PIN_TYPE 참조 (6비트)
//    [5:2] 출력: 0000=None, 0110=Output, 1010=Tristate,
//                0100=DDR, 0101=Registered, 1001=Reg+Enable
//    [1:0] 입력: 01=Direct, 00=Registered/DDR, 11=Latch, 10=Reg+Latch
```

### iCEcube2 알려진 이슈

```
⚠ VHDL netlister 버그 (iCEcube2 v2020.12.27943):
  - Top I/O에 multi-bit 버스 사용 시 VHDL netlister가 [n]_wire 형식으로
    변환하여 OA database에서 bus syntax error 발생
  - 해결: Top I/O를 single-bit 이름으로 선언 (bus index 미사용)

⚠ SG48 패키지에서 DRIVE_STRENGTH 속성 미지원

⚠ VPP_2V5_TO_1P8V synthesis 속성으로 전압 레벨 설정 가능:
  /* synthesis VPP_2V5_TO_1P8V = 1 */
```

### 오픈소스 툴체인 (대안)

```bash
# Yosys + nextpnr-ice40 + icestorm
yosys -p "synth_ice40 -device u -abc2 -top top_module -json top.json" src.v
nextpnr-ice40 --u4k --package sg48 --pre-pack prepack_swg36.py \
    --json top.json --pcf-allow-unconstrained --asc top.asc
icepack top.asc top.bin
iceprog top.bin  # FTDI 기반 프로그래밍
```

> **참고**: nextpnr에서 iCE5LP4K는 `--u4k` 디바이스 사용. SWG36 패키지는 chipdb 미지원이므로
> `--package sg48` + `--pre-pack` Python으로 IO 배치.
> 상세 제약 사항은 `tcl-scripts.md > 오픈소스 빌드 플로우` 참조.

---

## iCE40 UltraPlus

### 리소스

| 디바이스 | LUT | EBR | SPRAM | DSP | PLL | I2C/SPI |
|----------|-----|-----|-------|-----|-----|---------|
| iCE40UP5K | 5,280 | 120Kb | 1Mb | 8 | 1 | 2/2 |
| iCE40UP3K | 2,800 | 80Kb | 1Mb | 8 | 1 | 2/2 |

### 특징
- **초저전력**: 대기 ~75µW, 동작 ~1-10mW
- **SPRAM**: 1Mbit 싱글포트 RAM (대용량 버퍼)
- **하드 IP**: I2C, SPI 블록 내장
- **RGB LED 드라이버**: PWM LED 제어

### PDC 예시 (Radiant)

```tcl
# iCE40UP5K-SG48 핀 할당

# 클럭 (12MHz 일반적)
ldc_set_location -site {35} [get_ports clk_12m_i]
ldc_set_port -iobuf {IO_TYPE=LVCMOS33} [get_ports clk_12m_i]

# SPI 하드 IP (고정 핀)
ldc_set_location -site {15} [get_ports spi_sck_o]
ldc_set_location -site {17} [get_ports spi_mosi_o]
ldc_set_location -site {14} [get_ports spi_miso_i]
ldc_set_location -site {16} [get_ports spi_cs_n_o]

# I2C 하드 IP (고정 핀)
ldc_set_location -site {31} [get_ports i2c_sda_io]
ldc_set_location -site {32} [get_ports i2c_scl_o]
ldc_set_port -iobuf {IO_TYPE=LVCMOS33 PULLMODE=UP} [get_ports i2c_*]

# RGB LED 드라이버
ldc_set_location -site {39} [get_ports led_r_o]
ldc_set_location -site {40} [get_ports led_g_o]
ldc_set_location -site {41} [get_ports led_b_o]
```

### 저전력 설계 팁

```verilog
// 1. SPRAM 활용 (EBR보다 저전력)
SB_SPRAM256KA u_spram (
    .ADDRESS    (addr[13:0]),
    .DATAIN     (wdata),
    .DATAOUT    (rdata),
    .MASKWREN   (4'b1111),
    .WREN       (we),
    .CHIPSELECT (1'b1),
    .CLOCK      (clk),
    .STANDBY    (standby),      // 대기모드
    .SLEEP      (sleep),        // 슬립모드 (더 저전력)
    .POWEROFF   (poweroff)      // 파워오프
);

// 2. PLL 저전력 모드
// Radiant IP에서 Low Power 옵션 선택

// 3. 미사용 IO 설정
// Pulldown으로 설정하여 플로팅 방지
```

---

## MachXO2

### 리소스

| 디바이스 | LUT | EBR | UFM | PLL | 특징 |
|----------|-----|-----|-----|-----|------|
| LCMXO2-256 | 256 | 0 | 2Kb | 0 | 초소형 |
| LCMXO2-1200 | 1,280 | 64Kb | 2Kb | 1 | |
| LCMXO2-4000 | 4,320 | 92Kb | 2Kb | 2 | |
| LCMXO2-7000 | 6,864 | 240Kb | 2Kb | 2 | 최대 |

### 특징
- **Instant-on**: 전원 인가 즉시 동작 (<1ms)
- **UFM**: User Flash Memory (설정/데이터 저장)
- **TransFR**: 동작 중 재구성 가능
- **Dual-boot**: 두 이미지 간 전환

### LPF 예시 (Diamond)

```
# MachXO2-7000 핀 할당 (TQFP144)

# 클럭
LOCATE COMP "clk_i" SITE "P3";
IOBUF PORT "clk_i" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk_i" 50 MHz;

# 리셋
LOCATE COMP "rst_n_i" SITE "P4";
IOBUF PORT "rst_n_i" IO_TYPE=LVCMOS33 PULLMODE=UP;

# SPI
LOCATE COMP "spi_sck_o" SITE "P5";
LOCATE COMP "spi_mosi_o" SITE "P6";
LOCATE COMP "spi_miso_i" SITE "P7";
LOCATE COMP "spi_cs_n_o" SITE "P8";
IOBUF PORT "spi_*" IO_TYPE=LVCMOS33;

# I2C
LOCATE COMP "i2c_scl_io" SITE "P9";
LOCATE COMP "i2c_sda_io" SITE "P10";
IOBUF PORT "i2c_*" IO_TYPE=LVCMOS33 PULLMODE=UP OPENDRAIN=ON;

# GPIO
LOCATE COMP "gpio_io[0]" SITE "P11";
LOCATE COMP "gpio_io[1]" SITE "P12";
LOCATE COMP "gpio_io[2]" SITE "P13";
LOCATE COMP "gpio_io[3]" SITE "P14";
IOBUF PORT "gpio_io[*]" IO_TYPE=LVCMOS33;
```

### UFM 사용 (User Flash Memory)

```verilog
// MachXO2 UFM 인스턴스
UFM u_ufm (
    .CLK        (clk),
    .FLASH_CSBI (flash_cs_n),
    .FLASH_SCK  (flash_sck),
    .FLASH_SI   (flash_si),
    .FLASH_SO   (flash_so)
);

// UFM 컨트롤러로 설정값 저장/로드
// - 캘리브레이션 데이터
// - 사용자 설정
// - 시리얼 넘버
```

---

## LatticeXP2

### 리소스

| 디바이스 | LUT | EBR | DSP | PLL | FlashBAK |
|----------|-----|-----|-----|-----|----------|
| LFXP2-5E | 5,000 | 166Kb | 12 | 2 | 5Mb |
| LFXP2-8E | 8,000 | 221Kb | 16 | 2 | 8Mb |
| LFXP2-17E | 17,000 | 276Kb | 20 | 4 | 17Mb |
| LFXP2-30E | 30,000 | 387Kb | 28 | 4 | 30Mb |
| LFXP2-40E | 40,000 | 498Kb | 36 | 4 | 40Mb |

### 특징
- **FlashBAK**: 비휘발성 메모리 (전원 꺼져도 유지)
- **sysDSP**: 18x18 곱셈기 블록
- **sysMEM EBR**: 듀얼포트 RAM
- **고밀도**: 최대 40K LUT

### LPF 예시 (Diamond)

```
# LatticeXP2-17E 핀 할당 (PQFP208)

# 클럭
LOCATE COMP "clk_i" SITE "P88";
IOBUF PORT "clk_i" IO_TYPE=LVCMOS33;
FREQUENCY PORT "clk_i" 100 MHz;

# 차동 클럭 (고속 인터페이스)
LOCATE COMP "clk_p_i" SITE "P91";
LOCATE COMP "clk_n_i" SITE "P92";
IOBUF PORT "clk_p_i" IO_TYPE=LVDS25;

# 외부 메모리 인터페이스
LOCATE COMP "mem_addr_o[0]" SITE "P100";
# ... (나머지 주소/데이터 핀)
IOBUF PORT "mem_*" IO_TYPE=LVCMOS25 DRIVE=8;

# DSP 입력
LOCATE COMP "dsp_a_i[0]" SITE "P120";
LOCATE COMP "dsp_b_i[0]" SITE "P130";
```

### FlashBAK 사용

```verilog
// XP2 FlashBAK - 비휘발성 저장
// 동작 중 Flash에 쓰기 가능

// 1. EBR을 FlashBAK 모드로 설정 (Diamond IP)
// 2. TransFR 명령으로 EBR ↔ Flash 전송

// UFM 컨트롤러
XP2_UFM u_flashbak (
    .CLK        (clk),
    .ADDR       (flash_addr),
    .DATA_IN    (flash_wdata),
    .DATA_OUT   (flash_rdata),
    .WE         (flash_we),
    .RE         (flash_re),
    .BUSY       (flash_busy)
);

// 용도:
// - 설정값 영구 저장
// - 펌웨어 업데이트
// - 로그 데이터 저장
```

### DSP 블록 사용

```verilog
// XP2 sysDSP 인스턴스 (18x18 MAC)
MULT18X18D u_dsp (
    .A          (a_in[17:0]),
    .B          (b_in[17:0]),
    .P          (product[35:0]),
    .CLK        (clk),
    .CEA        (1'b1),
    .CEB        (1'b1),
    .CEP        (1'b1),
    .RSTA       (rst),
    .RSTB       (rst),
    .RSTP       (rst)
);

// 또는 추론 (Diamond가 자동 매핑)
always @(posedge clk) begin
    product <= a * b;  // DSP 블록으로 추론
end
```

---

## 디바이스 선택 가이드

```
┌─────────────────────────────────────────────────────────────┐
│                   용도별 선택                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  초저전력, 배터리 ────────────────────► iCE40 UltraPlus    │
│                                                             │
│  빠른 부팅, 시스템 관리 ──────────────► MachXO2            │
│                                                             │
│  복잡 로직, DSP, 비휘발 저장 ─────────► LatticeXP2         │
│                                                             │
│  고속 인터페이스 (SERDES) ────────────► ECP5 (필요시)      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

조합 예시:
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   MachXO2    │───►│    XP2       │───►│  메인 SoC    │
│ (전원 시퀀싱)│    │ (전처리/DSP) │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 공통 주의사항

### 1. 전압 레벨
```
iCE40UP: 1.2V 코어, 1.8V~3.3V IO
MachXO2: 1.2V 코어, 1.2V~3.3V IO  
XP2:     1.2V 코어, 1.2V~3.3V IO

IO Bank별로 전압 분리 가능
```

### 2. 프로그래밍 인터페이스
```
iCE40:  SPI (외부 Flash 또는 NVCM)
MachXO2: JTAG, I2C, SPI (내장 Flash)
XP2:    JTAG, SPI (내장 Flash)
```

### 3. 온도 범위
```
Commercial: 0°C ~ 85°C
Industrial: -40°C ~ 100°C
```
