### trhp_posfb -- 엔진 예측 vs SPICE (bias=free)
- 판정: **FAIL** -- 폐루프 불안정(Z = 2, 과도 unstable, 근거 transient+nyquist)
- 기록용 비교(판정 무관): 허용오차 안 0, 밖 0, N/A 32
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": 0.05, "off_current_A": null}
- SPICE 포화 소자 3/3, 포화 아님: -
- C15 topology 연결 동일성: **unverified** -- topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 3, 'process_rule': 0, 'none': 0}
- C27 기록(판정 아님) 입력 nin: (2πf)²·L·C = 3.948e+09 @ 0.01 Hz
- C10 PM 안정성 근거: PM 정의 불가 open_loop_rhp_poles (Bode 식 원값 283.8 deg) -- Nyquist 시계 방향 감은 수 N = 0, 폐루프 과도 unstable, 개루프 RHP 극 2 (== (.pz)); .pz P = 2(ok), Z = N + P = 2 -> 안정성 판정 **unstable**(transient+nyquist)
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- 진단(free FAIL 원인): unknown -- forced 결과 없음 또는 막힘 -- 분류 불가(--bias free forced 로 함께 실행)
- resistor R1=51764.70588 (근거 미기재)
- resistor R2=129400 (근거 미기재)
- resistor Rb=10000000 (근거 미기재)
- capacitor Cc=1e-12 (근거 미기재)

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | 33.87 / 4139 / - / 84.14 | | |
| (참고) PM 정의 beta_1: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / - | | |
| (참고) PM 교차 측정(폐루프 peaking 역산, 기록만) deg / peaking dB | | - / - | - | 정의 불가(open_loop_rhp_poles) -- 개루프 RHP 극·불안정 폐루프에서는 peaking 역산이 위상여유가 아니다(원값 None) |
| 제약 pmc: pm_deg >= 60 | | - | | N/A(정의 불가: open_loop_rhp_poles) |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 0.5 | 2 x 1 | -/4.25 | - | -/0.700 | -/0.700 | -/-0.000 | 0.095 | +0.605 | sat | - | - |
| M2 | 0.5 | 2 x 2 | -/8.498 | - | -/0.700 | -/0.700 | -/-0.000 | 0.095 | +0.606 | sat | - | - |
| M3 | 0.5 | 2 x 4 | -/17 | - | -/0.700 | -/0.700 | -/-0.000 | 0.095 | +0.605 | sat | - | - |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
| n1 | - | 0.7000 | - | N/A |
| nin | 0.7000 | 0.7000 | +0.0000 | N/A(테스트벤치가 고정) |
| n2 | - | 0.7004 | - | N/A |
| n3 | - | 0.7000 | - | N/A |
| vdd | - | 1.8000 | - | N/A |
| vb | - | 0.7000 | - | N/A |
