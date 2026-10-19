### tfb_cs_rfeedback -- 엔진 예측 vs SPICE (bias=free)
- 판정: **BLOCKED** -- 막힘이 있어 합격 판정을 하지 않는다
- 기록용 비교(판정 무관): 허용오차 안 0, 밖 0, N/A 11
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": 0.05, "off_current_A": null}
- SPICE 포화 소자 0/1, 포화 아님: M1
- C15 topology 연결 동일성: **unverified** -- topology 미지정(입력 topology.path 도 --topology 도 없음) -- 연결 동일성 미검증
- C23 전도 확인: SPICE 에서 꺼짐 -, 판정 못 함 {'M1': 'N/A(예측 없음)'}
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 1, 'process_rule': 0, 'none': 0}
- PM 루프: None, feedback_passives ['Rf', 'Cin', 'Cx'] (규칙 미기재), 절단 넷 None, 가중 None
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- 진단(free FAIL 원인): not_applicable -- free verdict BLOCKED -- FAIL 일 때만 분류
- 막힘: feedback_passives 의 Cx 은 두 단자 ['nin', 'nin'] 가 모두 입력 포트 넷이다 -- 절단 단자가 하나로 정해지지 않는다(엔진 feedback_cut_ambiguous 와 같은 조건)
- resistor RL=100000 (근거 미기재)
- capacitor CL=1e-11 (근거 미기재)
- resistor Rf=1000000 (근거 미기재)
- capacitor Cin=1e-11 (근거 미기재)
- capacitor Cx=1e-12 (근거 미기재)

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | - / - / - / - | | |
| (참고) PM 정의 None: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / - | | |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 0.5 | 2 x 2 | -/- | - | -/- | -/- | -/- | - | - | None | - | - |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
| nout | - | - | - | N/A |
| nin | 0.7000 | - | - | N/A(테스트벤치가 고정) |
| vdd | - | - | - | N/A |
