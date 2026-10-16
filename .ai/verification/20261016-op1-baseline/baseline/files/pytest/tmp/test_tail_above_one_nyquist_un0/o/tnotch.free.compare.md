### tnotch -- 엔진 예측 vs SPICE (bias=free)
- 판정: **INCOMPLETE** -- SPICE 로 값을 못 얻은 제약 ['pmc']
- 기록용 비교(판정 무관): 허용오차 안 0, 밖 0, N/A 14
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": 0.05, "off_current_A": null}
- SPICE 포화 소자 1/1, 포화 아님: -
- C15 topology 연결 동일성: **unverified** -- topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 1, 'process_rule': 0, 'none': 0}
- C27 기록(판정 아님) 입력 nin: (2πf)²·L·C = 3.948e+09 @ 0.01 Hz
- C10 PM 안정성 근거: PM 정의 불가 nyquist_count_unavailable (Bode 식 원값 93.16 deg) -- Nyquist 시계 방향 감은 수 N = -(|L(f_last=1e+10 Hz)| = 2.942 >= 1 -- 스윕 위 꼬리가 -1 을 감을 수 있어 감은 수를 셀 수 없다(fstop_hz 부족)), 폐루프 과도 stable, 개루프 RHP 극 -; .pz P = -(failed), Z = N + P = - -> 안정성 판정 **stable**(transient)
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- 진단(free FAIL 원인): not_applicable -- free verdict INCOMPLETE -- FAIL 일 때만 분류
- resistor RL=129409.146 (근거 미기재)
- resistor Rt1=10000000 (근거 미기재)
- resistor Rt2=10000000 (근거 미기재)
- capacitor Ctm=3.2e-12 (근거 미기재)
- capacitor Ct1=1.6e-12 (근거 미기재)
- capacitor Ct2=1.6e-12 (근거 미기재)
- resistor Rts=5000000 (근거 미기재)

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | 23.93 / 8723 / - / 2371 | | |
| (참고) PM 정의 beta_1: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / - | | |
| (참고) PM 교차 측정(폐루프 peaking 역산, 기록만) deg / peaking dB | | - / 0.027 | - | 정의 불가(nyquist_count_unavailable) -- 개루프 RHP 극·불안정 폐루프에서는 peaking 역산이 위상여유가 아니다(원값 63.99752952367732) |
| 제약 pmc: pm_deg >= 10 | | - | | N/A(정의 불가: nyquist_count_unavailable) |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 0.5 | 2 x 2 | -/8.5 | - | -/0.700 | -/0.700 | -/-0.000 | 0.095 | +0.605 | sat | - | - |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
| n1 | - | 0.7000 | - | N/A |
| nin | 0.7000 | 0.7000 | +0.0000 | N/A(테스트벤치가 고정) |
| vdd | - | 1.8000 | - | N/A |
| nm | - | 0.7000 | - | N/A |
| no | - | 0.7000 | - | N/A |
| nc | - | 0.0000 | - | N/A |
