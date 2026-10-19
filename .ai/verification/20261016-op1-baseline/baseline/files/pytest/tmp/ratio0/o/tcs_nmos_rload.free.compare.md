### tcs_nmos_rload -- 엔진 예측 vs SPICE (bias=free)
- 판정: **PASS** -- 선언 제약 전부 만족, 전도 MOS 전부 포화, 엔진 예측 전도 MOS 전부 SPICE 에서도 전도
- 기록용 비교(판정 무관): 허용오차 안 2, 밖 0, N/A 26
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": 0.05, "off_current_A": null}
- SPICE 포화 소자 2/2, 포화 아님: -
- C15 topology 연결 동일성: **unverified** -- topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 2, 'process_rule': 0, 'none': 0}
- C24 ratio_db @ 0.01 Hz: 22.98 dB (|H_num| 12.88, |H_den| 0.9143)
- C24 ratio_db @ 0.01 Hz: 29 dB (|H_num| 25.76, |H_den| 0.9143)
- C24 ratio_db @ 0.01 Hz: 22.34 dB (|H_num| 11.97, |H_den| 0.9143)
- C24 ratio_db @ 0.01 Hz: 20.37 dB (|H_num| 12.88, |H_den| 1.234)
- C24 ratio_db @ 0.01 Hz: 4.291 dB (|H_num| 1.506, |H_den| 0.9187)
- C27 기록(판정 아님) 입력 nin: (2πf)²·L·C = 3.948e+09 @ 0.01 Hz
- C10 PM 안정성 근거: PM 유효 (Bode 식 원값 94.22 deg) -- Nyquist 시계 방향 감은 수 N = 0, 폐루프 과도 stable, 개루프 RHP 극 0 (== (Nyquist: 과도 stable -> Z = 0)); .pz P = 0(ok), Z = N + P = 0 -> 안정성 판정 **stable**(transient+nyquist)
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- 진단(free FAIL 원인): not_applicable -- free verdict PASS -- FAIL 일 때만 분류
- resistor RL=100000 (test)
- capacitor CL=1e-12 (근거 미기재)
- resistor RP=10000 (근거 미기재)
- 게이트 전용 넷 pb = 0.3 V (bias_voltages 선언)

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| ratio_db (psrr_vdd_se) | 0 | 22.98 | +23 | N/A(tol 미설정) |
| ratio_db (neg_amp_multi) | 0 | 29 | +29 | N/A(tol 미설정) |
| ratio_db (sum_two_nets) | 0 | 22.34 | +22.3 | N/A(tol 미설정) |
| ratio_db (diff_sense) | 0 | 20.37 | +20.4 | N/A(tol 미설정) |
| ratio_db (gate_bias_vsp) | 0 | 4.291 | +4.29 | N/A(tol 미설정) |
| ratio_db (psrr_dup) | 0 | 22.98 | +23 | N/A(tol 미설정) |
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | 22.2 / 2.232e+07 / 94.22 / 1.778e+06 | | |
| (참고) PM 정의 beta_1: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / 94.22 | | |
| (참고) PM 교차 측정(폐루프 peaking 역산, 기록만) deg / peaking dB | | - / - | - | peaking 없음(Mp-1 = 2.88e-10, 데이터 분해능 2e-08 이하) -- 2차 근사로 PM >= 65.53 deg |
| 제약 psrr_c: ratio_db >= 0 | | 22.98 | | PASS |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 0.5 | 2 x 2 | 8.724/8.724 | +0.0% | 0.700/0.700 | 0.928/0.928 | -0.000/-0.000 | 0.095 | +0.832 | sat | +0.0% | +0.0% |
| MP1 | 0.5 | 2 x 3 | 16.47/16.47 | +0.0% | 1.200/1.200 | 1.335/1.335 | 0.300/0.300 | 0.197 | +1.139 | sat | -0.0% | -0.0% |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
| nout | 0.9276 | 0.9276 | +0.0000 | N/A(tol 미설정) |
| nin | 0.7000 | 0.7000 | +0.0000 | N/A(테스트벤치가 고정) |
| pout | 0.1647 | 0.1647 | +0.0000 | N/A(tol 미설정) |
| pb | - | 0.3000 | - | N/A(테스트벤치가 고정) |
| vsp | - | 1.5000 | - | N/A |
| vdd | - | 1.8000 | - | N/A |
