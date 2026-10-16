### tcs_nmos_rload -- 엔진 예측 vs SPICE (bias=iso)
- 판정: **INCOMPLETE** -- iso 는 진단 모드 -- 합격 판정은 free 모드에서만 한다
- 기록용 비교(판정 무관): 허용오차 안 0, 밖 0, N/A 18
- 모델 코너/온도(LUT npz 메타): tt, 27.0 C
- 판정 설정: {"tolerances": {}, "sat_margin_V": null, "off_current_A": null}
- 포화 판정: sat_margin_V 미설정(포화 여유 값만 보고)
- C15 topology 연결 동일성: **not_applicable** -- iso 는 회로 연결이 없는 단독 소자 넷리스트 -- C15 대상 아님
- C23 전도 확인: SPICE 에서 꺼짐 -, 판정 못 함 {'M1': 'N/A(off_current_A 없음)', 'MP1': 'N/A(off_current_A 없음)'}
- C22 접합 용량(확산 기하): 포함 True -- 출처 {'device': 0, 'process_rule': 2, 'none': 0}
- C25 슬루·정착: not_measured -- β 루프 .tran 정의(입력 계단 크기·여기 넷, 정착 오차 대역, 슬루 측정 구간)가 엔진·spec 계약에 없다 (gmid_engine/authoring/SPEC_CONTRACT.md, design_spec_format F11: settling 은 {total_s, linear_s} 뿐 오차 대역 없음, driving_spec.slew_rate_* 는 MOD5 레지스트리 미정) -- 추측으로 정하지 않음(Q5 (ii) (B), 2026-10-07)
- iso(단독 소자, K3): **INCOMPLETE** -- 허용오차 안 0, 밖 [], 판정 못 함 {'M1': 'tol_ID_rel 없음', 'MP1': 'tol_ID_rel 없음'}

| 성능 | 예측 | SPICE | 차이 | 판정 |
|---|---|---|---|---|
| (참고) dc_gain_db / UGF Hz / PM deg / f-3dB Hz | | - / - / - / - | | |
| (참고) PM 정의 None: 루프 이득 기준점 dB / 루프 UGF Hz / 개루프 A 의 PM deg | | - / - / - | | |

| 소자 | L um | finger_w um x m | ID 예측/SPICE uA | ID차 | VGS 예측/SPICE | VDS 예측/SPICE | VSB 예측/SPICE | VDSAT | 포화여유 | 영역 | gm차 | gds차 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 0.5 | 2 x 2 | 8.698/8.698 | +0.0% | 0.700/0.700 | 0.900/0.900 | 0.000/-0.000 | 0.095 | +0.805 | None | - | - |
| MP1 | 0.5 | 2 x 3 | 16.48/16.48 | -0.0% | 1.200/1.200 | 1.340/1.340 | 0.300/0.300 | 0.197 | +1.143 | None | - | - |

| 넷 | 예측 V | SPICE V | 차 | 판정 |
|---|---|---|---|---|
