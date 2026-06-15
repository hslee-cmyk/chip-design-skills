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

PCF `set_io` 명령에 `-io_std`와 `-pullup` 옵션을 직접 지정할 수 있음 (iCEcube2).

```
# set_io 문법: set_io <signal> <pin> [-io_std <std>] [-pullup <yes|no>]

# LVCMOS (기본 GPIO)
set_io i_rst_n          D5 -io_std SB_LVCMOS -pullup yes
set_io o_refClk         B4 -io_std SB_LVCMOS -pullup no

# LVDS 차동 입력 (P핀만, N핀은 자동 매핑)
set_io i_backTel_p      F5 -io_std SB_LVDS_INPUT -pullup no

# -io_std 생략 시: SB_LVCMOS 기본값 적용
# -pullup 생략 시: no (기본값)
set_io o_sdaOut         C6
```

#### -io_std 옵션 (iCE40 Ultra)

| io_std | 용도 |
|--------|------|
| `SB_LVCMOS` | 기본 GPIO (VCCIO에 따라 1.8V/2.5V/3.3V) |
| `SB_LVDS_INPUT` | LVDS 차동 입력 (비교기 기반, P핀만 할당) |

> iCE40 Ultra는 LVDS **출력** 미지원 — 입력 전용.

#### -pullup 옵션 (iCE40 Ultra)

| 옵션 | 의미 |
|------|------|
| `-pullup yes` | 내부 weak pull-up 활성화 |
| `-pullup no` | pull-up 비활성화 (기본값) |

**중요 제약:**
- iCE40 Ultra는 **pull-up만 지원** — pull-down 없음 (하드웨어 미지원)
- **Bank 3 핀은 PULLUP 무시됨** (bank 0/1/2에서만 동작)
- `SB_IO_OD` (open-drain) 핀은 내부 pull-up 없음 → 외부 저항 필요
- pull-up 저항값 (약, VCCIO 기준): 3.3V ≈ 25.7k~300kΩ, 2.5V ≈ 34.7k~312.5kΩ → 강한 pull 필요 시 외부 저항 사용

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
# iCE5LP4K-SWG36 패키지 (iCEcube2 생성)

# LVCMOS 핀 — 풀업 있는 입력 (리셋, I2C, 이어폰 감지)
set_io i_earpiece_det_n D6 -io_std SB_LVCMOS -pullup yes
set_io i_sdaIn          C1 -io_std SB_LVCMOS -pullup yes
set_io i_scl            B1 -io_std SB_LVCMOS -pullup yes
set_io i_rst_n          D5 -io_std SB_LVCMOS -pullup yes

# LVCMOS 핀 — 풀업 없는 일반 입출력
set_io i_pcmSync        E2 -io_std SB_LVCMOS -pullup no
set_io i_pcmIn          D2 -io_std SB_LVCMOS -pullup no
set_io i_deep_slp_en    F6 -io_std SB_LVCMOS -pullup no
set_io i_dyn_slp_en     E6 -io_std SB_LVCMOS -pullup no
set_io o_backTel_pwr_en F4 -io_std SB_LVCMOS -pullup no
set_io o_serial_tp_out  C2 -io_std SB_LVCMOS -pullup no
set_io o_askData        E3 -io_std SB_LVCMOS -pullup no
set_io o_refClk         B4 -io_std SB_LVCMOS -pullup no
set_io o_refClkInv      F3 -io_std SB_LVCMOS -pullup no

# LVDS 차동 입력 — P핀만 할당, N핀 자동 매핑
set_io i_backTel_p      F5 -io_std SB_LVDS_INPUT -pullup no

# io_std 미지정 (기본값 SB_LVCMOS 적용)
set_io o_sdaOut         C6
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

### iCE40 Ultra IO_STANDARD (iCE5LP4K)

iCE40 Ultra의 I/O 표준은 **PCF의 `-io_std`** 또는 **RTL의 SB_IO `IO_STANDARD` 파라미터** 둘 다로 설정 가능.
iCEcube2 사용 시 PCF 설정이 우선 적용됨.

| io_std / IO_STANDARD | 전압 | 용도 |
|----------------------|------|------|
| `SB_LVCMOS` | VCCIO 따름 (1.8V/2.5V/3.3V) | 기본 GPIO |
| `SB_LVDS_INPUT` | 차동 | LVDS 입력 (비교기 기반, P핀만) |

```
# PCF에서 설정 (권장 — iCEcube2)
set_io i_backTel_p  F5 -io_std SB_LVDS_INPUT -pullup no
set_io i_rst_n      D5 -io_std SB_LVCMOS     -pullup yes
```

```verilog
// RTL에서 직접 SB_IO 인스턴스화 시
SB_IO #(
    .PIN_TYPE(6'b0000_01),
    .IO_STANDARD("SB_LVDS_INPUT")  // LVDS 차동 입력
) u_lvds_in (
    .PACKAGE_PIN(i_lvds_p),
    .D_IN_0(lvds_data)
);

// Open-drain (I2C SDA) — SB_IO_OD 사용
SB_IO_OD #(
    .PIN_TYPE(6'b1010_01)  // 출력 + 입력
) u_i2c_sda (
    .PACKAGEPIN(io_i2c_sda),
    .DOUT0(sda_out),
    .DIN0(sda_in)
);
```

> **주의**: iCE40 Ultra는 LVDS **출력** 미지원 — `SB_LVDS_INPUT`은 입력 전용.

## PULLMODE 옵션

### PCF (iCEcube2 / iCE40 Ultra)

```
# set_io에서 -pullup 옵션으로 직접 설정
set_io i_rst_n   D5 -io_std SB_LVCMOS -pullup yes   # 풀업 활성화
set_io i_data    C3 -io_std SB_LVCMOS -pullup no    # 풀업 없음 (기본)
```

> **iCE40 Ultra pull 제약:**
> - **pull-up만 지원** — pull-down은 하드웨어 미지원
> - Bank 3 핀은 `-pullup yes`가 **무시됨** (bank 0/1/2만 동작)
> - `SB_IO_OD` (open-drain) 핀: 내부 pull-up 없음 → 외부 저항 필요
> - Pull-up 저항값: ~25.7k~300kΩ (3.3V), ~34.7k~312.5kΩ (2.5V) — weak pull

RTL에서 `SB_IO` 프리미티브를 직접 인스턴스화할 경우 `PULLUP` 파라미터로도 설정 가능:

```verilog
SB_IO #(
    .PIN_TYPE(6'b0000_01),
    .PULLUP(1'b1)           // 내부 풀업 활성화 (bank 0/1/2만)
) u_input_pullup (
    .PACKAGE_PIN(pin),
    .D_IN_0(pin_in)
);
```

### PDC (Radiant)

```tcl
ldc_set_port -iobuf {PULLMODE=UP} [get_ports pin]    # 풀업
ldc_set_port -iobuf {PULLMODE=DOWN} [get_ports pin]  # 풀다운
ldc_set_port -iobuf {PULLMODE=NONE} [get_ports pin]  # 없음
```

### LPF (Diamond)

```
IOBUF PORT "pin" PULLMODE=UP;
IOBUF PORT "pin" PULLMODE=DOWN;
```
