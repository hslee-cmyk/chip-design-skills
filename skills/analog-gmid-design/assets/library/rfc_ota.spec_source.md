# rfc_ota (held-out A, 판독 이름 A_rfc) -- spec 원문 표 추출

> 저장소 등록 메모(2026-10-13): 아래 본문은 판독본 `wt/_heldout/A_rfc/A_rfc.spec_source.md` 를 그대로 옮긴 것이다(제목만 바꿈, 본문 4행
> '사이징 spec은 만들지 않았다'는 추출 당시 상태). 사이징 spec 은 `rfc_ota.sizing_spec.json` 이고, 사용자 결정(user_decisions.md 2026-10-13
> "held-out A는 나", "A, B 모두 권고대로 해", "A도 넣어.")에 따라 원문 값에서 아래만 옮겼다(값 조정 없음, 공정 UMC 180 nm -> 엔진 PDK sky130):
>
> | spec 자리 | 값 | 원문 |
> |---|---|---|
> | 제약 `gain_ss_db >=` | 57.91 | p.56 Table 17 Recycling 열 |
> | 제약 `gbw_ss_hz >=` | 133.2e6 | p.56 Table 17 Recycling 열 |
> | 제약 `pm_ss_deg >=` | 62.77 | p.56 Table 17 Recycling 열 |
> | 결정 대기 `pending_constraints` `supply_current_dc` (U-75) | (457.2e-6 A, 판정 안 함) | p.56 Table 17 Bias Current. p.54 'only the amplifier current is considered' -- 엔진 `supply_current_dc` 는 레일 전류 합이라 바이어스 회로(A-7 (가)로 topology 에 포함)까지 센다. 정의 불일치로 판정 제약에서 뺐다 |
> | `driving_spec.slew_rate_v_per_s` | 18.95e6 | p.49 Table 13 (SR+ 19.16 / SR- -18.95 중 작은 크기) |
> | `supplies_v` | vdd 1.8, gnd 0 | p.11 명세 1 |
> | `element_values.CL` (measurement_load) | 2.75e-12 F | p.35, p.37 Fig.11 |
> | `element_values.RB` | 1412 Ω | p.34 Fig.9 |
> | `input_dc` | 결정 대기 U-75 | 원문 미기재 |
>
> 보고만(spec 에 넣지 않음): 대역폭, 정착 시간·오버슈트, 입력 환산 잡음, offset, PSRR, CMRR, ICMR, HD2·HD3 -- 아래 §3 표.

출처: P. J. I. Matibag, *Design and test of a CMOS folded cascode OTA with current recycling*, UPC 석사논문, 2024 (`wt/_heldout/upc_rfc.pdf`).
공정: UMC 180 nm (p.9 초록). 이 문서는 원문 값을 옮겨 적은 것이며, 사이징 spec(`*.sizing_spec.json`)은 만들지 않았다. 어떤 값을 제약으로 쓸지는 사용자가 정한다.

## 1. 요구사항·명세 (p.11 §1.3)

| 항목 | 값 | 단위 | 조건·비고 | 쪽 |
|---|---|---|---|---|
| GBW (RFC) | 150 | MHz | 요구사항 1 | p.11 |
| 부하 용량 CL | 2.25 | pF | 요구사항 2 (p.16 사이징 식 (7)에도 2.25 pF) | p.11, p.16 |
| 전류 소모 | 기존 FC와 비슷하게 | -- | 요구사항 3 (공정한 비교 조건, 숫자 없음) | p.11 |
| 공급 전압 | 1.8 | V | 명세 1 | p.11 |
| testbench | 두 증폭기에 같은 것 | -- | 명세 2 | p.11 |
| 바이어스 회로 | 두 증폭기에 같은 것 | -- | 명세 3 (p.34 Fig.9) | p.11 |

## 2. 설계 과정에서 바뀐 조건 (p.35)

| 항목 | 값 | 비고 | 쪽 |
|---|---|---|---|
| 1차 반복 PM (RFC) | 57.33° | 60° 미만이라 불안정으로 판정 | p.35 Table 4 |
| 부하 용량 변경 | 2.25 pF -> **2.75 pF** (500 fF 추가) | PM 확보용. 이 때문에 GBW 150 MHz 목표는 달성 불가라고 원문에 적혀 있다 | p.35 본문, p.37 Fig.11 |
| 과구동 전압 목표 | 약 150 mV | 사이징 기준 | p.35 |
| PM 안정 기준 | 60° | 원문이 정한 안정 판정 임계값 | p.35 |

## 3. 결과 표 -- RFC 열만 (Table 17 = pre-layout, Table 30 = post-layout)

조건: VDD 1.8 V, CL 2.75 pF(p.37 Fig.11). 개방 루프 AC 측정은 1 GΩ 귀환 저항과 10 mF 커패시터로 DC 동작점만 잡는다(p.36). 이득·GBW·PM은 1 Hz~100 MHz AC 해석. SR·정착 시간은 1 V 펄스(p.50). 잡음은 1 Hz~100 MHz 적분(p.54). 바이어스 전류는 증폭기 전류만 셈(p.54 "only the amplifier current is considered"). 입력 공통모드 DC 레벨은 원문에서 찾지 못함.

| 파라미터 | Pre-layout (Table 17, p.56) | Post-layout (Table 30, p.81) | 단위 | 비고 |
|---|---|---|---|---|
| 바이어스 전류 | 457.2 | 463.7 | µA | 증폭기만 |
| DC 이득 | 57.91 | 58.78 | dB | Table 5 p.37 / Table 18 p.70 |
| 대역폭(-3 dB) | 173.2 | 155.1 | kHz | Table 6 p.38 |
| GBW | 133.2 | 132.6 | MHz | Table 7 p.39 (CL 2.75 pF) |
| 위상 여유 | 62.77 | 62.59 | ° | Table 8 p.40 |
| SR+ | 19.16 | 19.16 | V/µs | Table 13 p.49 |
| SR- | -18.95 | -18.94 | V/µs | Table 13 p.49 |
| 오프셋 전압 | -319 | -114.3 | µV | Table 9 p.41 |
| PSRR+ @10 Hz | 56.79 | 59.54 | dB | Table 11 p.46 |
| PSRR- @10 Hz | 76.65 | 77.42 | dB | Table 11 p.46 |
| CMRR @10 Hz | 69.72 | 87.89 | dB | Table 10 p.42 |
| CMRR @100 MHz | 37.06 | 40.16 | dB | Table 10 p.42 |
| ICMR | [0.3; 1.74] | [0.3; 1.74] | V | Table 12 p.47 |
| 정착 시간(90%) | 41.95 | 41.98 | ns | Table 14 p.50 |
| 오버슈트 | 0.12 | 0.10 | % | Table 14 p.50 |
| 입력 환산 잡음(1 Hz~100 MHz) | 87.45 | 87.45 | µVrms | Table 16 p.54 |
| HD2 | 55.04 | 55.03 | dB | Table 15 p.52 |
| HD3 | 59.85 | 59.84 | dB | Table 15 p.52 |

참고(비교 대상 기존 FC, Table 17): 457.4 µA, 48.46 dB, GBW 63.66 MHz, PM 82.49°.

## 4. 치수 (p.27 Table 2; p.28 Fig.6 / p.34 Fig.9에도 표기)

| 소자 | W (µm) | L (µm) | 쪽 |
|---|---|---|---|
| M0 | 161.57 | 0.54 | p.27 |
| M1a, M1b, M2a, M2b | 40.39 | 0.54 | p.27 |
| M3a, M4a | 27.24 | 0.54 | p.27 (K = 3, p.22·p.26) |
| M3b, M4b | 9.09 | 0.54 | p.27 |
| M5, M6 | 18.17 | 0.54 | p.27 |
| M7, M8 | 80.78 | 0.54 | p.27 |
| M9, M10 | 53.85 | 0.36 | p.27 |
| M11, M12 | 9.09 | 0.54 | p.27 |
| Q9, Q7, Q11 | 40.4 | 0.54 | p.34 Fig.9 |
| Q8, Q6, Q10 | 40.4 | 0.66 | p.34 Fig.9 |
| Q1, Q4, Q3, Q12, Q15, Q16, Q17 | 9.09 | 0.54 | p.34 Fig.9 |
| Q2 | 36.32 | 0.54 | p.34 Fig.9 |
| Q5 | 2.28 | 0.54 | p.34 Fig.9 |
| Q13 | 6 | 0.66 | p.34 Fig.9 |
| Q14 | 10.1 (단위 표기 없음) | 0.66 | p.34 Fig.9 |
| Q18 | 0.24 | 0.36 | p.34 Fig.9 |
| R_B | 1412 Ω | -- | p.34 Fig.9 (p.33: 처음 353 Ω, 소자 1/4 축소에 맞춰 4배) |

## 5. spec 선택 시 주의

- 원문 요구 GBW 150 MHz는 CL 2.25 pF 기준이고, 최종 결과(133.2 MHz)는 CL 2.75 pF 기준이다. 두 쌍을 섞으면 안 된다.
- 원문 결과는 UMC 180 nm 값이다. sky130으로 옮기면 그대로 달성된다는 보장은 없다.
