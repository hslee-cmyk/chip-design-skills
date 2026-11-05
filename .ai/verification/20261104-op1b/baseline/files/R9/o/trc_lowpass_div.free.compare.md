### trc_lowpass_div -- 엔진 예측 vs SPICE (bias=free)
- 판정: **INCOMPLETE** -- sat_margin_V 미설정 -- 포화 조건 판정 불가; 전도 확인(C23)을 판정 못 한 소자 {'MD': 'N/A(예측 없음)'}
- 기록용 비교(판정 무관): 허용오차 안 0, 밖 0, N/A 13
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": null, "off_current_A": null}
- 포화 판정: sat_margin_V 미설정(포화 여유 값만 보고)
- C15 topology 연결 동일성: **unverified** -- topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증
- C23 전도 확인: SPICE 에서 꺼짐 -, 판정 못 함 {'MD': 'N/A(예측 없음)'}
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 1, 'process_rule': 0, 'none': 0}
- C27 기록(판정 아님) 입력 rin: (2πf)²·L·C = 3.948e+09 @ 0.01 Hz
- C10 PM 안정성 근거: PM 검사 대상 아님 (Bode 식 원값 - deg) -- Nyquist 시계 방향 감은 수 N = -, 폐루프 과도 None, 개루프 RHP 극 -; .pz P = -(None), Z = N + P = - -> 안정성 판정 **None**(None)
- U6 .noise 개루프: ok -- 열잡음 입력환산 6.63e-17 V²/Hz (f = 10 Hz), flicker 코너 - Hz(below_f_lo), excess -
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- 진단(free FAIL 원인): not_applicable -- free verdict INCOMPLETE -- FAIL 일 때만 분류
- resistor Ra=2000 (근거 미기재)
- resistor Rb=2000 (근거 미기재)
- capacitor C1=1e-09 (근거 미기재)
- resistor R1=3000 (근거 미기재)
- resistor R2=1000 (근거 미기재)
- resistor Rd=100000 (근거 미기재)

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | -6.021 / - / - / 1.679e+05 | | |
| (참고) PM 정의 beta_1: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / - | | |
| (참고) PM 교차 측정(폐루프 peaking 역산, 기록만) deg / peaking dB | | 65.48 / 3.055e-05 | - |  |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| MD | 1 | 1 x 1 | -/9.275 | - | -/0.872 | -/0.872 | -/-0.000 | 0.247 | +0.626 | None | - | - |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
| ndio | - | 0.8725 | - | N/A |
| rin | 0.6000 | 0.6000 | +0.0000 | N/A(테스트벤치가 고정) |
| rout | - | 0.3000 | - | N/A |
| vdd | - | 1.8000 | - | N/A |
| dmid | - | 0.4500 | - | N/A |
