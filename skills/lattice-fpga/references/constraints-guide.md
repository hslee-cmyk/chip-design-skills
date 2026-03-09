# Lattice Constraints Guide

## PCF vs PDC vs LPF

| 항목 | PCF (iCEcube2) | PDC (Radiant) | LPF (Diamond) |
|------|----------------|---------------|---------------|
| 사용 툴 | iCEcube2 (또는 Yosys+nextpnr) | Radiant | Diamond |
| FPGA | iCE40 Ultra (iCE5LP) | Nexus, CrossLink-NX, iCE40 UltraPlus | ECP5, MachXO2/3 |
| 문법 | `set_io` 단순 문법 | SDC 기반 | 독자 문법 |
| 타이밍 | 별도 .sdc 파일 | 동일 .pdc 또는 별도 | FREQUENCY/BLOCK 문법 |

## PCF (iCEcube2) - Physical Constraints File

iCE40 Ultra 전용. `set_io` 명령으로 핀 할당.

### 핀 할당 기본

```
# pins.pcf - iCE40 Ultra (iCE5LP4K)

# 기본 문법: set_io signal_name PIN_LOC
set_io clk_i          B4
set_io rst_n_i         A5

# 버스 신호 (비트별 지정)
set_io data_o[0]       C5
set_io data_o[1]       D5
set_io data_o[2]       E5
set_io data_o[3]       F5

# LED 출력
set_io led_o           A1
```

### I/O 속성 지정

PCF에서는 `--warn-no-port` 옵션으로 미사용 핀 경고 제어 가능.
I/O 표준(IO_TYPE), 풀업/풀다운은 **RTL에서 SB_IO 프리미티브로 직접 설정**.

```
# PCF는 핀 위치만 지정
set_io i_backTel_p     E6

# I/O 표준 설정은 RTL에서:
# SB_IO #(.PIN_TYPE(6'b0000_01), .IO_STANDARD("SB_LVDS_INPUT"))
#       u_backTel (.PACKAGE_PIN(i_backTel_p), .D_IN_0(backTel_rx));
```

### 차동 입력 (LVDS)

iCE40 Ultra의 LVDS는 **P핀만 PCF에 할당**. N핀은 자동 매핑.

```
# LVDS 차동 입력 - P핀만 할당
set_io i_lvds_p        E6
# i_lvds_n (F6)은 자동 매핑 — PCF에 지정하지 않음

# RTL에서 SB_IO로 SB_LVDS_INPUT 표준 지정
```

### 전용 핀

```
# SPI 마스터 (하드 IP) - 전용 핀
set_io o_spi_sck       E1     # SPI_SCK 전용
set_io o_spi_ss        F2     # SPI_SS 전용
set_io o_spi_mosi      F1     # SPI_MOSI 전용
set_io i_spi_miso      E2     # SPI_MISO 전용

# I2C 마스터 (하드 IP) - 전용 핀
set_io io_i2c_scl      A3     # I2C_SCL 전용
set_io io_i2c_sda      B3     # I2C_SDA 전용
```

### 실제 프로젝트 예시 (venezia_test_fpga_top)

```
# venezia_test_fpga_top_swg36_io.pcf
# iCE5LP4K-SWG36 패키지

set_io o_cola_sdo       B2
set_io o_cola_sck       A2
set_io o_cola_ss        A3
set_io i_cola_sdi       B3
set_io io_i2c_sda       A4
set_io o_i2c_scl        B4
set_io o_mclk           A5
set_io o_pdm_data       B5
set_io i_pcm_data       E5
set_io i_pcm_sck        D5
set_io i_pcm_ws         E4
set_io i_backTel_p      E6
set_io o_backTel_pwr_en D6
set_io o_test_clk       C5
set_io o_test_out       D4
```

### 타이밍 제약 (.sdc)

iCEcube2는 타이밍 제약을 별도 `.sdc` 파일로 관리 (Synplify SDC 포맷).

```tcl
# timing.sdc

# 내부 오실레이터 클럭 (SB_HFOSC)
# CLKHF_DIV="0b10" → 48MHz/4 = 12MHz
create_clock -name clk_hfosc -period 83.33 [get_ports clk_hfosc]

# 외부 클럭 입력
create_clock -name clk_ext -period 100.0 [get_ports clk_i]

# 비동기 리셋
set_false_path -from [get_ports rst_n_i]

# 클럭 도메인 크로싱
set_clock_groups -asynchronous \
    -group [get_clocks clk_hfosc] \
    -group [get_clocks clk_ext]
```

## PDC (Radiant) - Physical Design Constraints

### 핀 할당

```tcl
# pins.pdc

# 클럭 입력
ldc_set_location -site {A5} [get_ports clk_i]
ldc_set_port -iobuf {IO_TYPE=LVCMOS33} [get_ports clk_i]

# 리셋 (풀업)
ldc_set_location -site {B6} [get_ports rst_n_i]
ldc_set_port -iobuf {IO_TYPE=LVCMOS33 PULLMODE=UP} [get_ports rst_n_i]

# 데이터 버스
ldc_set_location -site {C7} [get_ports {data_io[0]}]
ldc_set_location -site {C8} [get_ports {data_io[1]}]
ldc_set_location -site {D7} [get_ports {data_io[2]}]
ldc_set_location -site {D8} [get_ports {data_io[3]}]
ldc_set_port -iobuf {IO_TYPE=LVCMOS33} [get_ports {data_io[*]}]

# LED 출력 (드라이브 강도)
ldc_set_location -site {E10} [get_ports led_o]
ldc_set_port -iobuf {IO_TYPE=LVCMOS33 DRIVE=8} [get_ports led_o]

# 차동 신호 (LVDS)
ldc_set_location -site {F1} [get_ports lvds_p_i]
ldc_set_location -site {F2} [get_ports lvds_n_i]
ldc_set_port -iobuf {IO_TYPE=LVDS} [get_ports lvds_p_i]
```

### 타이밍 제약

```tcl
# timing.pdc

# 기본 클럭 정의
create_clock -name clk_sys -period 10.0 [get_ports clk_i]

# PLL 출력 클럭 (generate된 클럭)
create_generated_clock -name clk_pll \
    -source [get_ports clk_i] \
    -multiply_by 4 \
    [get_pins u_pll/CLKOP]

# 입력 지연
set_input_delay -clock clk_sys -max 2.0 [get_ports {data_i[*]}]
set_input_delay -clock clk_sys -min 0.5 [get_ports {data_i[*]}]

# 출력 지연
set_output_delay -clock clk_sys -max 2.0 [get_ports {data_o[*]}]
set_output_delay -clock clk_sys -min 0.5 [get_ports {data_o[*]}]

# False path (비동기 신호)
set_false_path -from [get_ports rst_n_i]

# 클럭 그룹 (CDC)
set_clock_groups -asynchronous \
    -group [get_clocks clk_sys] \
    -group [get_clocks clk_ext]
```

## LPF (Diamond) - Logical Preference File

### 핀 할당

```
# pins.lpf

# 클럭
LOCATE COMP "clk_i" SITE "P3";
IOBUF PORT "clk_i" IO_TYPE=LVCMOS33;

# 리셋
LOCATE COMP "rst_n_i" SITE "T2";
IOBUF PORT "rst_n_i" IO_TYPE=LVCMOS33 PULLMODE=UP;

# 버스
LOCATE COMP "data_io[0]" SITE "R1";
LOCATE COMP "data_io[1]" SITE "R2";
LOCATE COMP "data_io[2]" SITE "T1";
LOCATE COMP "data_io[3]" SITE "U1";
IOBUF PORT "data_io[0]" IO_TYPE=LVCMOS33;
IOBUF PORT "data_io[1]" IO_TYPE=LVCMOS33;
IOBUF PORT "data_io[2]" IO_TYPE=LVCMOS33;
IOBUF PORT "data_io[3]" IO_TYPE=LVCMOS33;

# 차동
LOCATE COMP "lvds_p" SITE "A4";
LOCATE COMP "lvds_n" SITE "A5";
IOBUF PORT "lvds_p" IO_TYPE=LVDS25;
```

### 타이밍 제약

```
# timing.lpf

# 클럭 주기
FREQUENCY PORT "clk_i" 100 MHz;

# PLL 출력
FREQUENCY NET "clk_pll" 400 MHz;

# 입출력 타이밍
INPUT_SETUP PORT "data_i[*]" 2.0 ns HOLD 0.5 ns CLKPORT "clk_i";
OUTPUT PORT "data_o[*]" 2.0 ns CLKPORT "clk_i";

# 비동기 경로 무시
BLOCK PATH FROM PORT "rst_n_i";
```

## IO_TYPE 옵션

### Radiant/Diamond IO_TYPE

| IO_TYPE | 전압 | 용도 |
|---------|------|------|
| LVCMOS33 | 3.3V | 일반 GPIO |
| LVCMOS25 | 2.5V | 일반 GPIO |
| LVCMOS18 | 1.8V | 저전압 GPIO |
| LVCMOS12 | 1.2V | 저전압 GPIO |
| LVDS | 차동 | 고속 인터페이스 |
| LVDS25 | 2.5V 차동 | LVDS |
| SSTL15 | DDR3 | 메모리 인터페이스 |
| HSUL12 | 1.2V 고속 | 고속 단방향 |

### iCE40 Ultra IO_STANDARD (SB_IO 파라미터)

iCE40 Ultra는 PCF가 아닌 **RTL의 SB_IO 프리미티브 파라미터**로 I/O 표준 설정.

| IO_STANDARD | 전압 | 용도 |
|-------------|------|------|
| SB_LVCMOS | 1.8V~3.3V (VCCIO 따름) | 기본 GPIO |
| SB_LVDS_INPUT | 차동 | LVDS 입력 (비교기 기반) |

```verilog
// iCE40 Ultra: SB_IO로 I/O 표준 설정
SB_IO #(
    .PIN_TYPE(6'b0000_01),        // 단순 입력
    .IO_STANDARD("SB_LVDS_INPUT") // LVDS 차동 입력
) u_lvds_in (
    .PACKAGE_PIN(i_lvds_p),
    .D_IN_0(lvds_data)
);

// Open-drain (I2C SDA)
SB_IO_OD #(
    .PIN_TYPE(6'b1010_01)  // 출력 + 입력
) u_i2c_sda (
    .PACKAGEPIN(io_i2c_sda),
    .DOUT0(sda_out),
    .DIN0(sda_in)
);
```

> **주의**: iCE40 Ultra는 true LVDS **출력**을 지원하지 않음. LVDS 입력만 SB_LVDS_INPUT으로 가능.

## PULLMODE 옵션

```tcl
# PDC (Radiant)
ldc_set_port -iobuf {PULLMODE=UP} [get_ports pin]    # 풀업
ldc_set_port -iobuf {PULLMODE=DOWN} [get_ports pin]  # 풀다운
ldc_set_port -iobuf {PULLMODE=NONE} [get_ports pin]  # 없음
```

```
# LPF (Diamond)
IOBUF PORT "pin" PULLMODE=UP;
```

```verilog
// PCF (iCEcube2) - 풀업/풀다운은 SB_IO 인스턴스에서 설정
// PULLUP 파라미터: "NO" (기본), "YES"
SB_IO #(
    .PIN_TYPE(6'b0000_01),
    .PULLUP(1'b1)           // 내부 풀업 활성화
) u_input_pullup (
    .PACKAGE_PIN(pin),
    .D_IN_0(pin_in)
);
```
