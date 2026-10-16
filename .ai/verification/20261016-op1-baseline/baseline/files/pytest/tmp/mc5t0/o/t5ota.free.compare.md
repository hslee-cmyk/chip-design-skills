### t5ota -- 엔진 예측 vs SPICE (bias=free)
- 판정: **PASS** -- 선언 제약 전부 만족, 전도 MOS 전부 포화, 엔진 예측 전도 MOS 전부 SPICE 에서도 전도
- 기록용 비교(판정 무관): 허용오차 안 0, 밖 0, N/A 40
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": 0.05, "off_current_A": null}
- SPICE 포화 소자 4/4, 포화 아님: -
- C15 topology 연결 동일성: **unverified** -- topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 4, 'process_rule': 0, 'none': 0}
- C27 기록(판정 아님) 입력 inp: (2πf)²·L·C = 3.948e+09 @ 0.01 Hz
- C27 기록(판정 아님) 입력 inn: (2πf)²·L·C = 3.948e+09 @ 0.01 Hz (출력 DC 되먹임 경로)
- C10 PM 안정성 근거: PM 유효 (Bode 식 원값 87.82 deg) -- Nyquist 시계 방향 감은 수 N = 0, 폐루프 과도 stable, 개루프 RHP 극 0 (== (Nyquist: 과도 stable -> Z = 0)); .pz P = -(failed), Z = N + P = 0 -> 안정성 판정 **stable**(transient+nyquist)
- U6 offset Monte-Carlo: ok -- σ_in = 3.676 mV (표본 201, 목표 상대 표준오차 0.05, 평균 0.2481 mV, 시드 0)
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- 진단(free FAIL 원인): not_applicable -- free verdict PASS -- FAIL 일 때만 분류
- current source IT=2e-05 (test toy)
- capacitor CL=1e-12 (근거 미기재)
- free: DC 되먹임 out -> inn (V(out)_pred=0.899999, V(inn)_pred=0.895968)

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | 39.99 / 1.97e+07 / 87.82 / 1.995e+05 | | |
| (참고) PM 정의 beta_1: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / 87.82 | | |
| (참고) PM 교차 측정(폐루프 peaking 역산, 기록만) deg / peaking dB | | - / - | - | peaking 없음(Mp-1 = 0, 데이터 분해능 2e-08 이하) -- 2차 근사로 PM >= 65.53 deg |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 1 | 2 x 2 | -/10.05 | - | -/0.755 | -/0.411 | -/0.145 | 0.138 | +0.273 | sat | - | - |
| M2 | 1 | 2 x 2 | -/9.951 | - | -/0.751 | -/0.755 | -/0.145 | 0.135 | +0.620 | sat | - | - |
| M3 | 1 | 2 x 2 | -/10.05 | - | -/1.245 | -/1.245 | -/-0.000 | 0.250 | +0.995 | sat | - | - |
| M4 | 1 | 2 x 2 | -/9.951 | - | -/1.245 | -/0.900 | -/-0.000 | 0.250 | +0.650 | sat | - | - |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
| d1 | 0.5554 | 0.5554 | +0.0000 | N/A(tol 미설정) |
| inp | 0.9000 | 0.9000 | +0.0000 | N/A(테스트벤치가 고정) |
| tail | 0.1445 | 0.1445 | +0.0000 | N/A(tol 미설정) |
| out | 0.9000 | 0.9000 | +0.0000 | N/A(tol 미설정) |
| inn | 0.8960 | 0.8960 | +0.0000 | N/A(테스트벤치가 고정) |
| vdd | - | 1.8000 | - | N/A |
