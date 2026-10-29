# B_erfc spec 출처 표 (spec 파일 아님 -- 원문 수치 기록만)

출처: Wu 외, Sensors 25(8):2523, 2025. 모든 값은 **post-layout 시뮬레이션**(실측 아님, p.16 Table 4 "Sim.").
쪽 번호는 PDF 쪽(p.N of 18).

## 1. 동작 조건

| 항목 | 값 | 출처 |
|---|---|---|
| 공정 | 0.18 µm CMOS | p.12 4절 첫 문단, Abstract |
| VDD | 1.8 V | p.8 Fig.6 우상단 표, p.12 |
| VCP / VCN | 1.1 V / 0.7 V | p.8 Fig.6 우상단 표 |
| IB / IC | 2 µA / 0.2 µA | p.8 Fig.6 우상단 표, p.12("bias current IB is 2 µA") |
| 정지 전류(supply current) | 10.4 µA | p.12, p.15 Table 2 |
| CL | 70 pF | p.12, p.15 Table 2 |
| 입력 공통모드 | 800 mV | p.13(open-loop 응답 조건 "common-mode input voltage of 800 mV") |
| 동작 영역 | M15/M16 포화, M19~M21 deep triode, 나머지 subthreshold | p.7 3.2절 |
| 면적 | 107 × 83 µm² | p.12 |

## 2. 성능 (TT, p.15 Table 2 "Proposed ERFC OTA" 열)

| 항목 | 값 | 비고 |
|---|---|---|
| DC gain | 84.18 dB | |
| GBW | 1.37 MHz | |
| Phase margin | 67.05° | Table 3 TT 열은 66.86°(⚠️ 표 간 차이) |
| 평균 slew rate | 19.32 V/µs | 600 mV p-p 계단, 단위이득 반전 구성(p.14). Table 3 TT 열 19.175(⚠️) |
| 1% 정착 시간 | 0.473 µs | 10 mV p-p 100 kHz 구형파, 단위이득 반전 구성(p.13~14). Table 3 TT STav 471.95 ns |
| 입력 잡음 @1 MHz | 31.86 nV/√Hz | p.13: @0.1 Hz 26.61 µV/√Hz |
| FoM_S | 9.22 MHz·pF/µA | |
| FoM_L | 130.04 (V/µs)·pF/µA | |
| offset | 3.3 mV | p.16 Table 4 (⚠️ p.15 Monte Carlo 평균 0.036 mV, σ 1.094 mV와 의미가 다름) |

## 3. PVT (p.15 Table 3)

| 항목 | FF | SS | SF | FS | TT | VDD −10% | VDD +10% | −40 °C | +125 °C |
|---|---|---|---|---|---|---|---|---|---|
| GBW (MHz) | 1.71 | 1.10 | 1.41 | 1.33 | 1.37 | 1.14 | 1.63 | 1.22 | 1.47 |
| PM (°) | 63.29 | 69.03 | 65.95 | 67.45 | 66.86 | 72.32 | 60.95 | 70.42 | 57.87 |
| Gain (dB) | 83.87 | 84.02 | 84.87 | 83.55 | 84.18 | 82.56 | 85.7 | 84.45 | 82.48 |
| SRav (V/µs) | 18.74 | 18.015 | 17.81 | 19.79 | 19.175 | 18.42 | 19.435 | 15.68 | 18.005 |
| STav (ns) | 391.3 | 539.3 | 468.25 | 479.5 | 471.95 | 359.65 | 429.2 | 388.15 | 626.85 |

⚠️ STav 행은 원문 XML 추출에 빠져 있고 PDF 렌더(`img/page15.png`)에서만 읽었다.

## 4. Monte Carlo (200점, p.15~16 본문·Fig.13)

| 항목 | 평균 | 표준편차 |
|---|---|---|
| GBW | 1.376 MHz | 0.18 MHz |
| DC gain | 84.15 dB | 1.133 dB |
| PM | 66.77° | **4.203°** (PDF). ⚠️ XML 원문은 34.20° -- XML 오류로 판단, PDF 값 채택 권고 |
| offset | 0.036 mV | 1.094 mV |

## 5. 입력·출력 범위 (식만, 수치 없음)

- 입력 범위 p.9 식 (8): VDD − VSG11 − VSG13 − VSD11,sat − VSG15 ≤ Vin ≤ VDD − VSG11 − VSD13,sat
- 출력 범위 p.9 식 (9): VDS4B,sat + VDS6,sat ≤ Vout ≤ VDD − VSD10,sat − VSD8,sat
- 소신호 p.9 식 (10): gm,ERFC = 2(gm1B·gm4B·RY + gm2A)

## 6. 비교 기준 (같은 논문의 일반 RFC, p.15 Table 2) -- 참고
8 µA, 70 pF, GBW 0.23 MHz, 68.37 dB, PM 89.15°, SR 0.16 V/µs, 2.945 µs, 37.77 nV/√Hz.

## 7. 사용자 확정 (2026-10-13)

- ⚠️12 (가): PDF 값 채택. PM sigma 4.203도(p.15 본문, p.16 Fig.13c 범례). TT 기준값은 Table 2·Table 4의 PM 67.05도, SR 19.32 V/us. Table 3 TT 열(66.86도, 19.175)은 참고.
- Monte Carlo offset 평균: 본문 0.036 mV, p.16 Fig.13d 범례 -0.036 mV(부호 차이, 원문 그대로 기록).
- B-5: CBAT1_L, CBAT1_R, CBAT2 값은 원문 없음 -> 엔진 계산(spec element_values engine:true).
