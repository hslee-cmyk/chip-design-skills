# topology 정정 대기열 (사용자 '한꺼번에 반영' 지시 때 일괄 반영 + connectivity 표 재출력)

| # | 회로 | 정정 | 출처 | 상태 |
|---|---|---|---|---|
| Q1 | folded_cascode | M1·M2 kind: pmos -> **nmos** (source tail, drain X/Y, gate vin_n/vin_p 는 그대로) | 사용자 2026-10-07 "3번의 m1/m2는 pmos가 아니라 nmos야." (UD-17a 해소) | 반영(4e421ca) |
| Q2 | library 9회로 | 옛 키 이름(nfet/pfet, value_amp 등) -> 새 이름, connectivity 불변 | 사용자 2026-10-07 결정 7 기본안 | 검토 완료 -- 변경 없음(4e421ca: 남은 옛 키 전부 보류, 목록은 반영 보고) |
| Q3 | nmcnr_amplifier | passive_elements 추가: Cm1(NodeM2-NodeCM), Cm2(NodeS2-NodeCM), Rm(NodeCM-Vout), CL(Vout-vss, 100 pF) -- NodeCM 새 넷, Cm1·Cm2·Rm 값은 엔진 계산 | 사용자 2026-10-07 "1번은 맞아" | 반영(4e421ca, 최종 Q3''' 기준) |
| Q4 | two_stage_ota | passive_elements 추가: Cc 와 Rz 직렬, O1-OUT 사이(중간 새 넷 1개), 값은 엔진 계산 | 사용자 2026-10-07 "cc와 Rz가 직렬로 O1-OUT사이에 있어" | 반영(4e421ca, Q4' 기준) |
| Q5 | folded_cascode | passive_elements 추가: CL(out-gnd, 1 pF) | 사용자 2026-10-07 "CL 1pF를 넣어줘" | 반영(4e421ca) |
| Q4' | two_stage_ota | Q4 확정: O1 - Rz - N_cc_rz - Cc - OUT (Rz 수동 저항, 값은 엔진 계산) + CL(OUT-gnd, 3 pF) | 사용자 2026-10-07 "가로 하고, 수동소자로 해. 3pF으로 확정해." | 반영(4e421ca) |
| Q3' | nmcnr_amplifier | Q3 확정 + RL(Vout-vss, 25 kΩ) 부하 저항 추가 | 사용자 2026-10-07 "nmcnr은 25kOhm부하저항 넣어." | 반영(4e421ca, Q3''' 로 복원) |
| Q3'' | nmcnr_amplifier | Q3' 철회: 25 kΩ 부하 저항 넣지 않음 -- 최종 = Q3(Cm1, Cm2, Rm, CL 100 pF)만 | 사용자 2026-10-07 "그럼 25k저항은 빼." | 철회됨(Q3''' 가 대체, 4e421ca) |
| Q3''' | nmcnr_amplifier | Q3'' 철회, Q3' 복원: library nmcnr 에 RL(Vout-vss, 25 kΩ) 포함 -- 최종 = Cm1, Cm2, Rm, CL 100 pF, RL 25 kΩ (논문 측정 조건 100 pF ∥ 25 kΩ, 레일로 DC 전류를 흘리는 저항 분기의 검증 발동 회로) | 사용자 2026-10-07 "25kOhm을 넣어." | 반영(4e421ca) |
| Q6 | common_gate, folded_cascode, ngcc, nmcnr, pushpull, two_stage_ota, two_stage_ota_sf | gate 전용 외부 바이어스 넷 선언 추가(`bias_inputs`, connectivity 불변): common_gate {VNBias1, VNBias2, VPBias1}, folded {bias3}, ngcc {VBP, VBN}, nmcnr {VB1~VB5}, pushpull {VPB1, VNB1}, two_stage·two_stage_sf {bias} -- 넷 이름은 반영 때 topology에서 재실측 | 사용자 2026-10-07 "B는 추천대로 해."(SYNTHESIS Q9 (i)) | **반영됨 2026-10-08 (브랜치 ng-q6-bias, 미병합)**: library 7회로 `bias_inputs` 선언(재실측 일치), authoring `bias_inputs.py` 게이트(gate_only_undeclared/bias_input_not_gate_only), 오라클 C15 bias_voltages 대조 배선, CONTRACT 9절 |
| Q7 | library 9회로 | 선택 키 `source_manifest{figure, device_count, passive_count}` 추가(값은 사용자가 도면 기준으로 선언, 로더가 netlist 수와 대조) | 같은 지시(Q9 (iii)) | **반영됨 2026-10-08 (사용자 "Q7도 모두 맞아", 브랜치 ng-q6-bias, 미병합)**: 9회로 `source_manifest` 추가, authoring `source_manifest.py` 개수 대조(source_manifest_mismatch), CONTRACT 10절 |
| Q8 | nmcnr_amplifier | 전원을 pushpull 형태로: supplies_v {vdd 0.9, vss -0.9} -> **{vdd 1.8, vss 0.0, agnd 0.9}**, supply_nets [vdd, vss] -> **[vdd, vss, agnd]**. 부하 CL(100 pF)·RL(25 kOhm) 끝을 vss -> **agnd** 로(pushpull·sf 의 CL 이 agnd 에 붙는 것과 같은 형태). MOS source/bulk 의 vss 연결은 그대로(vss 가 0 V 가 됨). sizing_spec human.supplies_v 와 topology _declared_target_spec.supplies_v 도 같이 고침. input_dc(SP-2 대기)는 agnd 기준으로 다시 정해야 함 | 사용자 2026-10-12 "nmcnr은 1.8, 0으로 고치고 agnd로 0.9로 하는 pushpull 형태로 고쳐" | **대기**("한꺼번에 반영" 지시 때) |
