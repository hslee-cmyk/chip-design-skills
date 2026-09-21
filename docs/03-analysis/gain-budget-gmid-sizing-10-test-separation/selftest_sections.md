# self-test 섹션 계수 (commit 89d257c3c332158697389c9b10195b210f2ae03b)

## sizing_recipe.py -- 블록 12571~15269 (2699줄), sys.argv 사용 False

섹션 77(머리 P 포함) / 범주 P 1 · D(표지만) 5 · A(assert·raise 판정) 68 · B(print 판정만) 1 · C(판정 없음) 2 / C 중 뒤 섹션이 의존 2 / assert 220 / raise AssertionError 20 / 거부 try 20 / print PASS·FAIL 토큰 113 / 앞 섹션 의존 섹션 52 / `lut` 읽는 섹션 27
모듈 이름 읽음 56개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 12572-12599 | (머리) | 0 | 0 | 0 | 0 |  | 9 |
| S1 | major | B | 12601-12613 | # toy LUT(E.K.V. 해석식 합성 데이터) 기반 실행 예시 — 숫자는 데모용, 실제 공정값 아님 | 0 | 0 | 0 | 1 | S0 | 27 |
| S2 | major | C | 12614-12634 | # find_optimal_sizing() 데모 — gain 제약에서 전력/면적 각각 최소인 점 자동 탐색 | 0 | 0 | 0 | 0 | S0, S1 | 2 |
| S3 | major | A | 12635-12659 | # _COMPENSATION_REGISTRY allowlist 거부 -- 실제 harness 경로(_evaluate()) 자체 | 1 | 1 | 1 | 0 |  | 25 |
| S4 | major | A | 12660-12681 | # 배치 7-1(analog-topology-json-library.do.md) — optimize_multistage() 실 | 1 | 0 | 0 | 1 | S3 | 0 |
| S5 | major | D | 12682-12686 | # 배치 7-3 B/C/F 엔진(analog-topology-json-library.do.md §7.3.2, 2026-07-3 | 0 | 0 | 0 | 0 |  | 0 |
| S6 | sub | A | 12687-12702 | [B엔진 solve_id_for_target_gm() -- 순방향으로 만든 gm_target을 역산해 gm_id 복원] | 2 | 0 | 0 | 1 | S1 | 0 |
| S7 | sub | A | 12703-12721 | [C엔진 solve_diode_stack_current() -- 순방향으로 만든 VGS합을 역산해 전류 복원] | 1 | 0 | 0 | 1 | S1 | 0 |
| S8 | sub | A | 12722-12742 | [F엔진 compute_metric()/_METRICS_REGISTRY -- sum_current/sum_area/gain_s | 3 | 1 | 1 | 1 |  | 0 |
| S9 | sub | A | 12743-12809 | [L4 revalidate_finger_override() -- finger 반올림으로 W가 강제로 바뀌어도 ID는 | 8 | 0 | 0 | 3 | S1 | 0 |
| S10 | sub | A | 12810-12900 | [L4b apply_and_revalidate_pair_adjustment() -- suggest_pair_finger_adj | 9 | 0 | 0 | 3 | S1 | 1 |
| S11 | sub | A | 12901-13031 | [L4c run_topology_pipeline_with_finger_fixup() -- 세션12 M3a 그룹(11소자) 실제 | 17 | 0 | 0 | 3 | S0, S1, S2, S3, S10 | 4 |
| S12 | sub | A | 13032-13134 | [L5 optimize_full_circuit_budget() 실배선 -- run_topology_pipeline_with_f | 5 | 0 | 0 | 1 | S1, S3, S11 | 2 |
| S13 | sub | A | 13135-13191 | [L5b resolve_stack_layout() -- declared vertical_stack_id를 audit_verti | 4 | 0 | 0 | 3 | S11, S12 | 4 |
| S14 | sub | A | 13192-13447 | [L5c 헤드룸 singleton 정책(다음 세션 최우선①, 2026-08-11 세션28) -- M5/M61, | 7 | 0 | 0 | 5 | S3, S11, S12, S13 | 2 |
| S15 | sub | A | 13448-13561 | [L4d suggest_matching_finger_growth()/apply_and_revalidate_matching_fi | 11 | 0 | 0 | 5 | S1, S3, S13, S14 | 3 |
| S16 | sub | A | 13562-13613 | [L4e run_matching_safety_with_finger_growth() -- 세션17 설계안 3번. gm/ID 예산 | 7 | 0 | 0 | 4 | S1, S15 | 1 |
| S17 | major | D | 13614-13617 | # 배치 7-3b/e/f(analog-topology-json-library.do.md, 2026-07-31) -- | 0 | 0 | 0 | 0 |  | 0 |
| S18 | sub | A | 13618-13632 | [7-3b allocate_stack_headroom() -- resize.py 6개 소자 스택, vdd=1.8V] | 2 | 0 | 0 | 1 |  | 1 |
| S19 | sub | A | 13634-13645 | [gm_id가 있으면 2/gm_id+margin으로 캐스코드 헤드룸이 자동 연동되는지(§7-3e (b))] | 2 | 0 | 0 | 1 | S13, S18 | 0 |
| S20 | sub | A | 13646-13673 | [2026-08-11(세션28) HeadroomPolicy.thin_roles -- 'diode_reference'도 casc | 3 | 0 | 0 | 2 |  | 0 |
| S21 | sub | A | 13674-13697 | [7-3e search_gm_id_for_role() -- role별 선택 방향(matching=최소, gain=gm/gds  | 3 | 0 | 0 | 1 | S1, S2 | 3 |
| S22 | sub | A | 13699-13711 | [2026-08-19 세션37 연속 신설 -- 'load' role: gm/gds가 아니라 ro(=1/gds) 자체를 | 1 | 0 | 0 | 1 | S1, S21 | 0 |
| S23 | sub | A | 13713-13721 | [W_bounds 안에 후보가 하나도 없으면 즉시 ValueError] | 0 | 1 | 1 | 1 | S1, S21 | 0 |
| S24 | sub | A | 13722-13797 | [7-3f 대체(2026-09-10, 사용자 지시 "bias_replica 상수도 없애") -- | 7 | 1 | 1 | 6 | S1, S14, S21 | 1 |
| S25 | sub | A | 13798-13820 | [계통 미러비 오차를 **선언된 랜덤 예산과 같은 단위**로 재기(2026-09-10) -- | 3 | 0 | 0 | 2 |  | 0 |
| S26 | sub | A | 13822-13845 | [value_from_constraint -- 임계값을 다른 제약에서 그대로 참조(숫자 복제 금지)] | 1 | 1 | 1 | 2 | S16 | 0 |
| S27 | sub | A | 13846-13878 | [웜스타트 조인트 스캔 점수(2026-09-10, l_class 포함) -- 그룹마다 기준이 다르다] | 3 | 2 | 2 | 4 |  | 0 |
| S28 | sub | A | 13879-13897 | [7-4b 확장 estimate_area_budget() -- 콜드스타트 블렌딩 vs 실측 자기참조] | 2 | 0 | 0 | 0 |  | 0 |
| S29 | major | D | 13898-13901 | # 배치 7-3d(analog-topology-json-library.do.md §7.3.2 D, 2026-07-31) -- | 0 | 0 | 0 | 0 |  | 0 |
| S30 | sub | A | 13902-13907 | [feed 'A' (_feed_root_ratio) -- theta*reference 전류합을 root의 seed로] | 1 | 0 | 0 | 1 |  | 0 |
| S31 | sub | A | 13909-13913 | [feed 'C' (_feed_diode_stack_target) -- theta*reference W를 target W로] | 1 | 0 | 0 | 1 |  | 0 |
| S32 | sub | A | 13915-13924 | [feed 'B' (_feed_gm_target_convention) -- N*omega_c*C_cmfb를 gm_target으 | 1 | 0 | 0 | 1 | S1 | 0 |
| S33 | sub | A | 13926-13930 | [feed 'settling_split' (_feed_settling_split) -- theta*total을 derived로 | 1 | 0 | 0 | 1 |  | 0 |
| S34 | sub | A | 13932-13939 | [feed 'metric_stage_budget' -- theta(L)로 지정 devices의 L/W/gm/gds 재계산] | 1 | 0 | 0 | 1 | S1 | 0 |
| S35 | sub | A | 13941-13948 | [등록 안 된 feed 타입은 즉시 ValueError] | 0 | 1 | 1 | 1 |  | 0 |
| S36 | sub | A | 13949-13985 | [optimize_full_circuit_budget() -- sizing_roles/device_roles 둘 다 없는 회로 | 2 | 0 | 0 | 1 | S1, S3 | 7 |
| S37 | sub | A | 13986-14039 | [optimize_full_circuit_budget() -- 합성 sizing_roles로 그리드서치가 실제 최적값을 찾는지 | 5 | 0 | 0 | 1 | S1, S3 | 1 |
| S38 | sub | A | 14040-14112 | [device_roles.gm_id_match_vgs_of -- 2026-08-19 세션38 신설, gm_id_role 루프의 | 3 | 0 | 0 | 1 | S1, S3, S24 | 3 |
| S39 | sub | A | 14114-14129 | [gm_id_match_vgs_of가 아직 sizing 안 된(존재하지 않는) 소자를 참조하면 ValueError] | 1 | 1 | 1 | 1 | S3, S38 | 0 |
| S40 | sub | A | 14130-14189 | [device_roles.vds_match_vgs_of -- 2026-08-19 세션38 연속 신설, 헤드룸 루프가 다른 컬럼 | 3 | 0 | 0 | 1 | S0, S1, S3 | 1 |
| S41 | sub | A | 14191-14205 | [vds_match_vgs_of가 순환 참조하면 ValueError] | 1 | 1 | 1 | 1 | S3, S40 | 0 |
| S42 | sub | A | 14206-14276 | [fixed-point worklist -- 2026-08-19 세션39 신설, _ref_depth() 단일재귀 정렬을 대체. | 4 | 0 | 0 | 1 | S0, S1, S3 | 1 |
| S43 | sub | A | 14278-14316 | [두 그룹의 budget_reference_device가 서로를 직접 가리키면(pre-pass로도 못 뚫리는 진짜 순환) 여전 | 1 | 1 | 1 | 1 | S0, S1, S3, S42 | 0 |
| S44 | sub | C | 14317-14326 | [diagnose_sizing_roles_gap() -- device_role/symmetry의 propose_device_r | 0 | 0 | 0 | 0 |  | 1 |
| S45 | sub | A | 14328-14367 | [1. 정상 케이스 -- known_sizing으로 전류/L/VDS가 다 채워지면 status=ok] | 5 | 0 | 0 | 3 | S0, S3, S13, S38, S44 | 1 |
| S46 | sub | A | 14369-14377 | [4. 실제 라이브러리 파일 folded_cascode -- 세션35 안에서 이 gap 자체를 해소했다(Ibg를 KCL 유도+ | 1 | 0 | 0 | 1 | S3, S36 | 0 |
| S47 | sub | A | 14379-14394 | [5/6. 실제 라이브러리 파일 nmcnr_amplifier -- 원래(세션35) PM_target_deg=46 (논문 실측치 | 1 | 0 | 0 | 1 | S3, S36 | 0 |
| S48 | sub | A | 14395-14418 | [require_declared_spec_source() -- 라이브러리 회로를 **출처 없는 spec**으로 | 1 | 1 | 1 | 4 | S3, S36 | 0 |
| S49 | sub | A | 14420-14426 | [7. sizing_roles.theta가 이미 선언된 회로는 status=has_theta로 조기 반환] | 1 | 0 | 0 | 1 | S3, S36 | 0 |
| S50 | sub | A | 14427-14442 | [제약을 만족하는 격자점이 하나도 없으면 즉시 ValueError] | 0 | 1 | 1 | 1 | S3, S37 | 0 |
| S51 | sub | A | 14443-14582 | [optimize_full_circuit_budget() -- 실제 회로(two_stage_ota, 7개 소자) 전체를 | 4 | 0 | 0 | 1 | S1, S3, S15, S36, S38, S45 | 2 |
| S52 | sub | A | 14583-14634 | [matching_pairs L 강제 일치 -- compensation(spec 기반) vs device_roles.L_rol | 2 | 0 | 0 | 1 | S0, S1, S3, S51 | 2 |
| S53 | sub | A | 14636-14661 | [matching_pairs L 강제 일치 -- 양쪽 다 L_role(휴리스틱)인데 값이 다르면(스펙 근거로 우선순위를 가릴  | 0 | 1 | 1 | 1 | S0, S1, S3, S52 | 0 |
| S54 | sub | A | 14662-14682 | [재현성: 같은 spec으로 다시 호출하면 완전히 같은 sizing] | 2 | 1 | 1 | 2 | S51 | 0 |
| S55 | major | D | 14683-14686 | # 배치 7-3g/h/i(analog-topology-json-library.do.md, 2026-07-31) -- | 0 | 0 | 0 | 0 |  | 0 |
| S56 | sub | A | 14687-14692 | [7-3g noise_1f_density() -- SID_1F 없는 LUT는 즉시 ValueError(데이터 없음을 숨기지 않 | 0 | 1 | 1 | 1 | S1 | 0 |
| S57 | sub | A | 14694-14708 | [SID_1F 있는 합성 LUT -- W_ref/W_target 스케일링 + 1/freq 반영 확인] | 1 | 0 | 0 | 1 | S1 | 1 |
| S58 | sub | A | 14710-14723 | [_metric_flicker_plus_thermal_sum() -- 열+1/f 합산이 손계산과 일치] | 1 | 0 | 0 | 1 | S57 | 0 |
| S59 | sub | A | 14724-14738 | [7-3h estimate_mismatch_sigma()/pelgrom_mismatch metric -- sky130 실측 v | 2 | 0 | 0 | 1 |  | 0 |
| S60 | sub | A | 14739-14749 | [7-3i cmrr_estimate/psrr_estimate metric -- diff_pair_tail family 계산 확 | 2 | 0 | 0 | 1 |  | 1 |
| S61 | sub | A | 14751-14759 | [등록 안 된 circuit_family는 즉시 ValueError] | 0 | 1 | 1 | 1 | S60 | 0 |
| S62 | sub | A | 14760-14781 | [세션37: nmcnr_gain_db/nmcnr_pm_deg -- nmcnr_amplifier.topology.json 실제 | 7 | 0 | 0 | 1 | S3, S15, S36 | 1 |
| S63 | sub | A | 14783-14817 | [_nmcnr_stage1_rout()/_metric_nmcnr_gain_db/_metric_nmcnr_pm_deg -- 손계 | 3 | 0 | 0 | 1 |  | 1 |
| S64 | sub | A | 14819-14830 | [_metric_nmcnr_pm_deg -- 0dB 교차가 아예 없으면(gm1이 극단적으로 작아 DC이득이 이미 0dB 미만) | 0 | 1 | 1 | 1 | S63 | 0 |
| S65 | sub | A | 14831-14889 | [cmrr_estimate -- telescopic_class_ab family: metric_spec의 소자 역할 배정이 | 16 | 0 | 0 | 1 | S3, S11, S36, S62 | 1 |
| S66 | sub | A | 14890-14938 | [cmrr_estimate -- telescopic_class_ab family(2026-08-03 확정 topology.js | 3 | 0 | 0 | 3 |  | 0 |
| S67 | sub | A | 14939-14991 | [cmrr_estimate -- telescopic_class_ab_cmfb family(2026-08-03 신규 유도, CM | 12 | 0 | 0 | 1 | S65 | 1 |
| S68 | sub | A | 14992-15071 | [cmrr/psrr_estimate -- telescopic_class_ab_cmfb family(2026-08-07 세션21 | 6 | 1 | 1 | 4 | S67 | 1 |
| S69 | sub | A | 15072-15092 | [psrr_estimate -- telescopic_class_ab_cmfb family, 같은 31소자망 -- Ann_ope | 1 | 1 | 1 | 3 | S68 | 0 |
| S70 | sub | A | 15093-15165 | [smallsignal_ratio_db/smallsignal_gain_db -- topology-무관 일반화(세션21 2차)] | 7 | 0 | 0 | 4 |  | 0 |
| S71 | major | A | 15166-15213 | # current_reuse_telescopic_topology() 등록 재확인(2026-07-31, 원문 Eq.2-6 재도출 | 9 | 0 | 0 | 0 | S1, S52 | 1 |
| S72 | major | D | 15214-15216 | # validate_theta_declaration_order() -- theta 배열 '선언 순서=실행 순서' 계약 | 0 | 0 | 0 | 0 |  | 0 |
| S73 | sub | A | 15218-15240 | [합성 fixture -- gm_id_match_vgs_of/C타입 reference가 선언 순서를 위반하면 잡아내는지] | 2 | 0 | 0 | 2 | S71 | 0 |
| S74 | sub | A | 15242-15248 | [올바른 순서(reference가 앞에 옴)면 위반 0건인지] | 1 | 0 | 0 | 1 |  | 0 |
| S75 | sub | A | 15250-15256 | [compensation.stage_devices는 처음부터 생산됨으로 취급되는지] | 1 | 0 | 0 | 1 |  | 0 |
| S76 | sub | A | 15258-15269 | [실제 library topology.json 4개 전부 위반 0건인지(reorder 이후 회귀 확인)] | 1 | 0 | 0 | 1 | S3 | 0 |

## stick_diagram.py -- 블록 8992~12936 (3945줄), sys.argv 사용 False

섹션 174(머리 P 포함) / 범주 P 1 · D(표지만) 10 · A(assert·raise 판정) 114 · B(print 판정만) 21 · C(판정 없음) 28 / C 중 뒤 섹션이 의존 13 / assert 346 / raise AssertionError 10 / 거부 try 9 / print PASS·FAIL 토큰 232 / 앞 섹션 의존 섹션 120 / `lut` 읽는 섹션 0
모듈 이름 읽음 92개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 8993-8995 | (머리) | 0 | 0 | 0 | 0 |  | 0 |
| S1 | major | C | 8997-9007 | === Test 1a: pptx slide 2의 원본 연결 그래프 (finger 1개씩, node 1-2-3-4 체인) === | 0 | 0 | 0 | 0 |  | 0 |
| S2 | major | C | 9008-9018 | === Test 1b: 실제 finger 수(M1=4, M2=2, M3=4)를 반영하면 모든 노드가 짝수차수 → 닫힌 회로 = | 0 | 0 | 0 | 0 |  | 0 |
| S3 | major | C | 9019-9033 | === Test 2: 홀수차수 노드 4개인 예(한붓그리기 불가능 + 조정 후보 확인) === | 0 | 0 | 0 | 0 |  | 0 |
| S4 | major | C | 9034-9046 | === Test 3: 극성이 다르면 자동으로 별도 stack으로 분리되는지 확인 === | 0 | 0 | 0 | 0 |  | 0 |
| S5 | major | C | 9047-9060 | === Test 4: Folded Cascode(PDF p.34~p.38) 실제 넷리스트 — pptx 원본 정답과 대조 === | 0 | 0 | 0 | 0 |  | 0 |
| S6 | major | C | 9061-9071 | === Test 5: PDF p.14 'Axis of Symmetries' — folded cascode top 행의 실제 대 | 0 | 0 | 0 | 0 |  | 0 |
| S7 | major | D | 9072-9072 | === Test 5.5: mirror_symmetric_trail() — 세션11 L3(D), 실제 회로 2개로 교차검증 == | 0 | 0 | 0 | 0 |  | 0 |
| S8 | sub | C | 9073-9084 | [사례1: folded_cascode top row — MP(self-pair,2f)/M3-M4(3f)/M5-M6(6f)] | 0 | 0 | 0 | 0 |  | 2 |
| S9 | sub | C | 9086-9102 | [사례2: current_reuse_telescopic_ota 그룹 M8 — M8/M17, M9a/M18a(둘 다 1:1, s | 0 | 0 | 0 | 0 |  | 0 |
| S10 | sub | C | 9104-9111 | [사례3(음성 대조): build_stick_diagram()에 matching_pairs를 안 주면 기존 동작과 완전히 동일 | 0 | 0 | 0 | 0 | S8 | 0 |
| S11 | major | C | 9112-9130 | === Test 5.6: suggest_pair_finger_adjustments() + mirror_symmetric_tra | 0 | 0 | 0 | 0 |  | 4 |
| S12 | sub | C | 9132-9134 | [1. 조정 전: build_graph()+check_euler_condition() 그대로면 홀수차수 6개(다중 trail  | 0 | 0 | 0 | 0 | S11 | 0 |
| S13 | sub | C | 9136-9144 | [2. suggest_pair_finger_adjustments() — 매칭쌍 단위 제안 1순위가 M9b/M18b 동시 +1인 | 0 | 0 | 0 | 0 | S8, S11 | 1 |
| S14 | sub | C | 9146-9154 | [3. 조정 후: mirror_symmetric_trail()이 대표 조합 탐색 + 홀수 self-pair 다리로 11소자 전 | 0 | 0 | 0 | 0 | S11, S13 | 1 |
| S15 | sub | C | 9156-9160 | [4(회귀 대조). 조정 없이 원본 그대로면 여전히 None(폴백)이어야 함 -- 다리만으로는 안 풀림] | 0 | 0 | 0 | 0 | S11 | 0 |
| S16 | major | C | 9161-9176 | === Test 6: matching 그룹 자동 탐지 — folded cascode 넷리스트에서 전류거울/차동쌍 추출 === | 0 | 0 | 0 | 0 | S14 | 2 |
| S17 | major | C | 9177-9183 | === Test 7: unit cell 사이징 후보 탐색 — nominal W 근방에서 정수배 후보 생성 === | 0 | 0 | 0 | 0 |  | 1 |
| S18 | major | C | 9184-9190 | === Test 8: 2-Stage OTA(PDF p.28~p.33) 실제 넷리스트 — 3개 stack 전부 닫힌 회로 확인  | 0 | 0 | 0 | 0 |  | 0 |
| S19 | major | C | 9191-9202 | === Test 9: 홀수 개수 매칭쌍의 교차 대칭 배치 — folded cascode M9/M10(각 3개) 실제 사례 == | 0 | 0 | 0 | 0 |  | 0 |
| S20 | major | C | 9203-9215 | === Test 10: §8 box-shape 탐색 — Intrinsic Gain Stage 예제(N=15um 1소자 vs P | 0 | 0 | 0 | 0 |  | 0 |
| S21 | major | B | 9216-9252 | === Test 11: §2.7 2D common-centroid 표 기반 경로 — M2/M2b(전류거울, 4:4) === | 0 | 0 | 0 | 3 |  | 0 |
| S22 | major | A | 9253-9273 | === Test 12: common_centroid_layout() 회전 경로 — 홀수 개수(M1/M2 차동쌍 9:9)도 | 1 | 0 | 0 | 0 |  | 2 |
| S23 | major | A | 9274-9306 | === Test 12.5: common_centroid_layout() — 대칭(1:1)에서 표/회전 두 경로가 | 2 | 0 | 0 | 1 | S22 | 2 |
| S24 | major | A | 9307-9392 | === Test 12.6: interdigitate_layout() — common_centroid_layout()와 동급으로 | 6 | 0 | 0 | 0 | S22, S23 | 0 |
| S25 | major | A | 9393-9489 | === Test 12.7: common_centroid_layout() — N=3 이상 hub-leaf common-centr | 9 | 0 | 0 | 5 | S17, S23 | 4 |
| S26 | major | C | 9490-9496 | === Test 12.8: common_centroid_layout() 일반화 — 소자 개수가 다르거나 n_rows를 | 0 | 0 | 0 | 0 |  | 3 |
| S27 | sub | A | 9497-9506 | [개수가 다름(A=6,B=4,C=2), n_rows 미지정 -> 기본 n_rows=N=3, 탐색 경로로 감] | 2 | 0 | 0 | 0 | S25, S26 | 1 |
| S28 | sub | A | 9508-9519 | [n_rows=4 (N=3보다 많음, 더 잘게 쪼갬) -- 슬라이싱만으론 모든 phase가 오일러 조건을 | 2 | 0 | 0 | 0 | S26, S27 | 1 |
| S29 | sub | A | 9521-9525 | [n_rows=2 (N=3보다 적음, 회전을 다 못 채움) -- 잔차가 0이 아닐 수 있음을 확인] | 1 | 0 | 0 | 0 | S26, S28 | 1 |
| S30 | sub | A | 9527-9537 | [균등 개수(N=3, 전부 8) + n_rows=3(=N) 명시 -- target_rows==N+개수 균등이면 | 1 | 0 | 0 | 0 |  | 0 |
| S31 | sub | A | 9539-9556 | [버그 재현+수정 확인: N=2, n_rows=2(=N) 명시 -- 사용자 지적으로 발견됨] | 1 | 0 | 0 | 0 |  | 0 |
| S32 | major | A | 9557-9585 | === Test 12.9: n_rows==N 전수 스윕(N=2~6, count 다양) — dispatch 버그 수정 후 | 2 | 0 | 0 | 0 | S25 | 1 |
| S33 | sub | A | 9586-9598 | [발견된 2차 버그: N=4,count=20처럼 '최대한 균등'([5,5,5,5], 전부 홀수)이 오일러 | 1 | 0 | 0 | 0 | S29 | 1 |
| S34 | sub | B | 9600-9611 | [소자별 개수(count)가 소자 수(N)보다 작으면(예: N=4, 각 2개씩) 명확한 ValueError인지 | 0 | 0 | 0 | 1 | S33 | 1 |
| S35 | major | D | 9612-9615 | === Test 12.9b: 회전 경로에 crossover 폴백 통합 (사용자 요청, 2026-07-28 3차) === | 0 | 0 | 0 | 0 |  | 0 |
| S36 | sub | A | 9616-9643 | [Test 12.9에서 '진짜 불가능'으로 확인됐던 10개 조합 전부 재확인 -- 이제는 | 4 | 0 | 0 | 0 | S32 | 3 |
| S37 | sub | A | 9645-9655 | [이미 0-crossover로 성공하던 케이스(N=2,count=4)는 전혀 안 바뀌었는지 회귀 확인] | 1 | 0 | 0 | 0 | S36 | 0 |
| S38 | major | A | 9656-9710 | === Test 12.10: n_rows != N(N보다 크거나 작은 경우) 전수 스윕 — 사용자 요구 === | 2 | 0 | 0 | 0 | S36 | 2 |
| S39 | sub | A | 9712-9722 | [발견된 잔차 지표 결함: 길이 1인 행을 건너뛰면 그 행에만 있는 소자가 완전히 | 1 | 0 | 0 | 0 |  | 0 |
| S40 | sub | A | 9724-9738 | [발견된 더 근본적 한계: 소자 하나가 통째로 자기 행에만 격리되면(다른 소자와 단 | 1 | 0 | 0 | 0 | S38 | 1 |
| S41 | sub | A | 9739-9745 | [증명된 최적 경로(rotation_exact)는 항상 isolated_pairs=0인지 확인] | 1 | 0 | 0 | 0 | S40 | 0 |
| S42 | major | A | 9746-9779 | === Test 12.11: INTERDIGITATION_PATTERNS 표 전체 — interdigitate_layout() | 2 | 0 | 0 | 0 | S25 | 0 |
| S43 | major | D | 9780-9782 | === Test 12.12: find_min_crossover_layout() — 최소 crossover 배치 신설 === | 0 | 0 | 0 | 0 |  | 0 |
| S44 | sub | A | 9783-9790 | [이미 가능한 경우(0 crossover) — 우선순위대로 단일 연속 diffusion부터 확인] | 1 | 0 | 0 | 0 | S36 | 1 |
| S45 | sub | A | 9792-9800 | [ABC 3소자 1개씩(4개 홀수차수 노드, m=2) -> crossover=1이어야 함] | 2 | 0 | 0 | 0 | S34, S44 | 2 |
| S46 | sub | A | 9802-9808 | [6소자 1개씩(6개 홀수차수 노드, m=3) -> crossover=2, 소자 6개 보존] | 2 | 0 | 0 | 0 | S45 | 3 |
| S47 | sub | A | 9810-9815 | [각 segment 내부가 실제로 유효한 hub-leaf walk인지 1차 원리로 재확인] | 1 | 0 | 0 | 0 | S46 | 1 |
| S48 | sub | A | 9817-9823 | [ABCD 표 패턴(4소자 1개씩)이 실제로 crossover=1로 해결되는지 -- 사용자가 | 1 | 0 | 0 | 0 | S46, S47 | 1 |
| S49 | sub | B | 9825-9840 | [대조군 -- 입력 검증] | 0 | 0 | 0 | 2 |  | 0 |
| S50 | major | D | 9841-9843 | === Test 12.13: find_min_crossover_layout() matching_pairs 확장(세션15) — | 0 | 0 | 0 | 0 |  | 0 |
| S51 | sub | A | 9844-9908 | [실전: current_reuse_telescopic_ota.topology.json M6 그룹(8소자) — 핑거조정 | 6 | 0 | 0 | 1 | S16, S38, S48 | 6 |
| S52 | sub | A | 9910-9918 | [node_map 역산 단위 확인 -- M2a/M2b가 서로 공유 끝이 없어도 Vom1<->Vop1이 | 3 | 0 | 0 | 1 | S51 | 0 |
| S53 | sub | A | 9920-9930 | [폴백 발동 확인 -- matching_pairs가 텅 비어 전부 orphan이면(자기대응 노드가 | 2 | 0 | 0 | 1 | S51 | 0 |
| S54 | sub | A | 9932-9937 | [회귀 -- matching_pairs=None(기존 호출부 경로, 하위호환)이면 hub-leaf 사전조건과 | 2 | 0 | 0 | 1 | S45, S46 | 0 |
| S55 | sub | A | 9939-9981 | [세션17 offset 우선순위 가중치 -- _count_matching_pair_splits()의 | 7 | 0 | 0 | 3 |  | 0 |
| S56 | sub | A | 9983-9995 | [M6 실제 회로 회귀 -- pair_sensitivity를 줘도 이미 달성한 (0,0)이 안 깨지는지] | 2 | 0 | 0 | 1 | S51 | 0 |
| S57 | major | B | 9996-10054 | === Test 13: check_box_shape() 게이트 — SPICE 전에 반드시 통과해야 하는 §8 체크포인트 === | 0 | 0 | 0 | 10 |  | 1 |
| S58 | major | B | 10055-10106 | === Test 14: stage 경계를 넘는 stack 병합 — Maloberti p.29 'Layout Oriented D | 0 | 0 | 0 | 3 | S51 | 4 |
| S59 | major | C | 10107-10134 | === Test 15: search_shared_finger_w() — 가로 배치(Case B) 탐색, Example 3로 정 | 0 | 0 | 0 | 0 | S25 | 0 |
| S60 | major | B | 10135-10168 | === Test 16: run_full_circuit_audit() — 4단계 harness가 실제로 잡아내는지 확인 === | 0 | 0 | 0 | 13 |  | 1 |
| S61 | major | B | 10169-10231 | === Test 17: pack_floorplan() — 실제 Xie&Chen 51-소자 회로 전체 블록으로 검증 === | 0 | 0 | 0 | 2 | S57, S58 | 5 |
| S62 | major | B | 10232-10267 | === Test 18: find_diffusion_safe_split_points() — 실제 S1_TAILP 시퀀스로 검증  | 0 | 0 | 0 | 5 | S61 | 1 |
| S63 | major | B | 10268-10299 | === Test 19: pack_floorplan_grouped() — 기능 그룹이 실제로 흩어지지 않는지 확인 === | 0 | 0 | 0 | 2 | S61, S62 | 3 |
| S64 | major | B | 10300-10330 | === Test 20: net_weights — 신호선 근접 배치, 실제 vbias1 연결로 검증 === | 0 | 0 | 0 | 3 | S61, S63 | 4 |
| S65 | major | B | 10331-10362 | === Test 21: sub_kind — 같은 diffusion(폴러리티)별로 나눠 배치하면 더 compact한지 실측 == | 0 | 0 | 0 | 1 | S51, S61, S63, S64 | 1 |
| S66 | major | C | 10363-10372 | === Test 21.5: check_symmetry_dispositions() — 매칭 후보를 조용히 빼먹는 것 차단 === | 0 | 0 | 0 | 0 |  | 2 |
| S67 | sub | A | 10376-10381 | [MA/MB(진짜 diff_pair)를 matching_pairs에 빼먹은 상황] | 1 | 0 | 0 | 1 | S66 | 1 |
| S68 | sub | A | 10383-10386 | [MA/MB를 matching_pairs에 정상 기록하면 PASS] | 1 | 0 | 0 | 1 | S66 | 0 |
| S69 | sub | A | 10388-10397 | [net 이름 대소문자 불일치(사고9와 동일 패턴)를 잡아내는지 -- Vbias1 vs vbias1] | 1 | 0 | 0 | 1 |  | 0 |
| S70 | sub | A | 10399-10413 | [실전: current_reuse_telescopic_ota.topology.json 전체 재검증] | 1 | 0 | 0 | 0 |  | 2 |
| S71 | sub | A | 10414-10456 | [linked_topology_files -- 회로가 여러 파일로 쪼개져도 항상 전체를 합쳐서 보는지] | 2 | 0 | 0 | 1 | S58, S70 | 2 |
| S72 | major | B | 10457-10476 | === Test 22: audit_row_split() — Euler/box-shape만으론 못 잡는 matching 회귀 실 | 0 | 0 | 0 | 1 |  | 1 |
| S73 | sub | B | 10477-10504 | [회귀 재현] M3 row0 통째로/M4 row1 통째로: overall={} | 0 | 0 | 0 | 4 | S72 | 1 |
| S74 | sub | B | 10505-10510 | [common_centroid_layout로 재구성] overall={} | 0 | 0 | 0 | 3 | S73 | 0 |
| S75 | sub | B | 10511-10534 | [kind-aware 재판정 -- two_stage_ota_example() top(M3/M4=2f+2f) + M6(8f)]  | 0 | 0 | 0 | 3 |  | 0 |
| S76 | sub | B | 10535-10552 | [대조군 -- 진짜 차동쌍이 common-centroid를 실패하면 이번엔 진짜로 FAIL해야 한다] | 0 | 0 | 0 | 4 |  | 0 |
| S77 | major | C | 10553-10565 | === Test 23: branch_symmetric kind — M5/M6, M7/M8 (공유 노드 없는 캐스코드 대칭쌍)  | 0 | 0 | 0 | 0 |  | 2 |
| S78 | sub | B | 10567-10589 | [1차: M5/M6 통째로 한 컬럼씩(solo)] -- 전수 탐색으로 interdigitation(3b)이 그래프상 | 0 | 0 | 0 | 4 | S77 | 0 |
| S79 | sub | B | 10590-10616 | [사용자 재지적: "differential pair처럼 stack 분리+finger 조절로 common-centroid를 | 0 | 0 | 0 | 3 | S77 | 2 |
| S80 | sub | B | 10617-10632 | [대조군 -- 진짜 finger 수가 안 맞는 branch_symmetric 쌍은 여전히 FAIL해야 한다] | 0 | 0 | 0 | 4 |  | 1 |
| S81 | major | C | 10633-10648 | === Test 24: check_walk_sequence() — 제안된 순서가 실제로 이어지는지 독립 검산 === | 0 | 0 | 0 | 0 | S79 | 1 |
| S82 | sub | C | 10649-10653 | [finger 개수 자체가 안 맞는 경우도 잡아내는지 확인] | 0 | 0 | 0 | 0 | S79 | 0 |
| S83 | major | B | 10654-10676 | === Test 25: check_stick_diagram_coverage() — sizing은 됐는데 layout이 통째로  | 0 | 0 | 0 | 1 |  | 1 |
| S84 | sub | B | 10677-10685 | [대조: 전부 커버되면 OK로 통과하는지 확인] | 0 | 0 | 0 | 1 | S83 | 0 |
| S85 | major | C | 10686-10697 | === Test 26: topology library JSON 오케스트레이션 레이어 (load_topology/run_topo | 0 | 0 | 0 | 0 |  | 8 |
| S86 | sub | A | 10698-10724 | [folded_cascode: n_fingers/finger_w/w/stack_id 산출물만 folded_cascode_exa | 1 | 0 | 0 | 1 | S71, S85 | 14 |
| S87 | sub | C | 10725-10743 | [two_stage_ota: 동일 회귀 + compensation 함수 실제 연결 확인] | 0 | 0 | 0 | 0 | S85, S86 | 2 |
| S88 | sub | A | 10744-10763 | [save_instance_json(): pipeline_result를 손대지 않고 그대로 파일에 옮기는지] | 1 | 0 | 0 | 1 | S85, S86, S87 | 0 |
| S89 | major | A | 10764-10780 | === Test 26.5: run_topology_pipeline() -- sizing_overrides에서 소자 하나를 | 0 | 1 | 1 | 1 | S85, S86, S87 | 1 |
| S90 | major | A | 10781-10804 | === Test 26.55: run_topology_pipeline() -- check_finger_width_compatib | 1 | 1 | 1 | 2 | S85, S86 | 0 |
| S91 | major | D | 10805-10810 | === Test 26.6: run_topology_pipeline() -- cell_groups 인자 (배치 7-2/2026- | 0 | 0 | 0 | 0 |  | 0 |
| S92 | sub | A | 10811-10817 | [(a) cell_groups/spine_groups 둘 다 None -- 기존 단일-Verdict 동작 그대로] | 2 | 0 | 0 | 1 | S86 | 0 |
| S93 | sub | A | 10818-10829 | [(b) cell_groups 생략, floorplan_hints.spine_groups만 제공 -- fallback으로 그대 | 2 | 0 | 0 | 1 | S85, S86 | 1 |
| S94 | sub | A | 10830-10845 | [(c) cell_groups를 명시하면 spine_groups와 달라도 cell_groups가 우선(오버라이드)] | 2 | 0 | 0 | 1 | S85, S86, S93 | 0 |
| S95 | major | D | 10846-10849 | === Test 27: propagate_topology_forced_currents() / find_diode_stacks( | 0 | 0 | 0 | 0 |  | 0 |
| S96 | sub | A | 10850-10858 | [A엔진 (a) 직렬 스택 전파 -- folded_cascode 'bot' 스택 한 소자만 seed] | 2 | 0 | 0 | 1 | S64, S86, S89 | 1 |
| S97 | sub | A | 10859-10864 | [A엔진 (b) 미러비 전파 -- ref(M9)->mirror(MN) 1:1 미러 가정] | 1 | 0 | 0 | 1 | S86 | 0 |
| S98 | sub | A | 10865-10872 | [A엔진 (c) 같은 직렬 스택에 서로 다른 seed 전류가 섞이면 즉시 ValueError] | 0 | 1 | 1 | 1 | S86 | 0 |
| S99 | sub | A | 10873-10884 | [C엔진 find_diode_stacks() (a) folded_cascode -- M11/MN이 실제로 self-diode임 | 2 | 0 | 0 | 1 | S86 | 1 |
| S100 | sub | A | 10885-10907 | [C엔진 find_diode_stacks() (b) 실제 회로(current_reuse_telescopic_ota.topolo | 3 | 0 | 0 | 1 | S85, S96, S99 | 3 |
| S101 | major | D | 10908-10910 | === Test 28: select_layout_tool()/repair_matching_safety() (배치 7-4/7-4 | 0 | 0 | 0 | 0 |  | 0 |
| S102 | sub | A | 10911-10924 | [select_layout_tool() -- 2026-08-05(세션10) L1 하드컷: 축B/축C 조합별 도구 선택 | 4 | 1 | 1 | 1 |  | 0 |
| S103 | sub | A | 10925-10965 | [repair_matching_safety() -- known-incidents.md 사고3 재현: folded_cascode | 2 | 1 | 0 | 2 | S80, S86, S100 | 4 |
| S104 | sub | A | 10966-10984 | [repair_matching_safety() -- 공유 hub가 없는 pair(같은 파일에서 발견한 진짜 | 2 | 0 | 0 | 2 | S103 | 3 |
| S105 | sub | A | 10985-11017 | [repair_matching_safety() -- 세션16 branch 복합 매칭: current_reuse_telescop | 5 | 0 | 0 | 2 | S61, S63, S100, S103 | 3 |
| S106 | sub | A | 11019-11026 | [_branch_composite_pair() -- branch 구조가 없는(2단자 net으로 안 이어진) 단독 소자 | 1 | 0 | 0 | 1 | S104 | 0 |
| S107 | sub | A | 11027-11068 | [세션17 _composite_collapse_for_crossover()/find_min_crossover_layout_wi | 8 | 0 | 0 | 2 | S51, S105 | 2 |
| S108 | sub | A | 11070-11081 | [회귀 -- branch 구조 없는 그룹(위 rowA/rowB 픽스처)은 _composite_collapse_for_ | 2 | 0 | 0 | 1 | S104, S107 | 1 |
| S109 | sub | A | 11082-11109 | [repair_matching_safety() -- 세션17 relaxed_pairs: 최후수단 인접배치 완화가 | 3 | 0 | 0 | 3 | S103, S104, S105 | 1 |
| S110 | major | D | 11110-11115 | === Test 29: derive_stack_groups()/assign_finger_geometry() (배치 7-6, 2 | 0 | 0 | 0 | 0 |  | 0 |
| S111 | sub | A | 11116-11155 | [geometry_colocation_union() -- 2026-08-05(세션10) L1/L2 하드컷: derive_sta | 5 | 0 | 0 | 1 | S64, S86, S103, S105, S108 | 5 |
| S112 | sub | A | 11156-11161 | [geometry_colocation_union() -- 재현성: 같은 입력 다시 넣으면 완전히 같은 그룹] | 1 | 0 | 0 | 1 | S86, S111 | 0 |
| S113 | sub | A | 11162-11201 | [assign_finger_geometry() -- 위 그룹 + 합성 sizing_results(가상 gm/ID 결과, | 6 | 0 | 0 | 1 | S111 | 1 |
| S114 | major | D | 11202-11206 | === Test 30: analog-grammar 연동(Tier 1) — find_idiom_matches()/find_mat | 0 | 0 | 0 | 0 |  | 0 |
| S115 | sub | A | 11207-11213 | [0. analog-grammar 사용 가능 확인 -- 없으면 이 Test 전체가 무의미하니 먼저 확인] | 1 | 0 | 0 | 1 |  | 0 |
| S116 | sub | A | 11214-11220 | [1. 하위호환 -- idiom_matches=None(기본값)이면 Test 6과 완전히 동일한 net-only 동작] | 2 | 0 | 0 | 1 | S16 | 0 |
| S117 | sub | A | 11221-11244 | [2. M57/M58 오탐 재현 -- 세션18 실사고 connectivity(2026-07-29 disposed -> 2026 | 3 | 0 | 0 | 0 | S58, S107, S111 | 1 |
| S118 | sub | A | 11245-11263 | [3. M11/MN 오탐 재현 -- folded_cascode_example(), 둘 다 self-diode(role=DIOD | 3 | 0 | 0 | 0 | S117 | 1 |
| S119 | sub | A | 11264-11281 | [4. 캐스코드 대칭쌍(M2a/M2b류) 복합소자 상속 -- folded_cascode의 M1/M2(확정 diff_pair) | 4 | 0 | 0 | 1 | S118 | 2 |
| S120 | sub | A | 11282-11303 | [5. 어댑터 자체 폴백 -- gate가 전혀 없는(레거시) Transistor 목록을 주면 | 3 | 0 | 0 | 2 |  | 0 |
| S121 | major | C | 11304-11311 | === Test 31: run_full_circuit_audit_from_topology() -- topology.json 하 | 0 | 0 | 0 | 0 |  | 3 |
| S122 | sub | A | 11312-11328 | [1. 실제 회로(51개 소자)로 자동 구성 -- ok=True, 세 체크 전부 자동 데이터로 통과하는지] | 4 | 0 | 0 | 1 | S81, S109, S121 | 3 |
| S123 | sub | A | 11329-11344 | [2. dispositions 변환 -- symmetry.dispositions(list)와 개수가 일치하고, 형식이 (cat | 2 | 0 | 0 | 1 | S70, S122 | 1 |
| S124 | sub | A | 11345-11354 | [3. 구조화 필드가 없는 회로(folded_cascode) -- ValueError로 명확히 실패하는지, | 1 | 1 | 1 | 1 | S121 | 0 |
| S125 | sub | A | 11355-11388 | [4. 구조화가 netlist 전수를 못 커버하면(소자 하나가 어느 블록에도 없음) ValueError -- | 1 | 1 | 1 | 2 | S121 | 0 |
| S126 | major | A | 11389-11433 | === Test 32: trace_vdd_to_gnd_branches() -- 세션23 실측(4가지 vertical_stack | 6 | 0 | 0 | 5 | S65 | 1 |
| S127 | major | A | 11434-11465 | === Test 33: suggest_vertical_stack_composites() -- branch tracing(Tes | 8 | 0 | 0 | 2 |  | 0 |
| S128 | major | A | 11466-11515 | === Test 35: trace_gnd_to_vdd_branches()/find_differential_and_mirror_ | 6 | 0 | 0 | 3 | S71, S126 | 10 |
| S129 | major | A | 11516-11541 | === Test 36: find_verified_differential_and_mirror_relations() -- 진짜 b | 6 | 0 | 0 | 2 | S60, S128 | 1 |
| S130 | major | A | 11542-11562 | === Test 37: find_differential_pair_candidates() -- inputs= 선언 없이 순수 | 4 | 0 | 0 | 2 | S122, S128 | 1 |
| S131 | major | A | 11563-11619 | === Test 38: refine_differential_and_mirror_relations() -- input 승격 | 11 | 0 | 0 | 4 | S129, S130 | 1 |
| S132 | major | A | 11620-11652 | === Test 39: find_verified_differential_and_mirror_relations() -- 세 번째 | 6 | 0 | 0 | 2 | S128, S131 | 1 |
| S133 | major | A | 11653-11683 | === Test 40: refine_differential_and_mirror_relations()의 | 9 | 0 | 0 | 2 | S119, S128 | 1 |
| S134 | major | A | 11684-11715 | === Test 41: _propose_vertical_stack_ids()의 fan-in 모호성 탐지 -- | 5 | 0 | 0 | 3 |  | 0 |
| S135 | major | A | 11716-11739 | === Test 42: fan-in 후보 중 differential-pair branch 소속 여부로 재판정 -- | 4 | 0 | 0 | 2 | S128 | 0 |
| S136 | major | A | 11740-11766 | === Test 43: refine_differential_and_mirror_relations()의 | 4 | 0 | 0 | 2 | S111, S128, S133 | 2 |
| S137 | major | A | 11767-11787 | === Test 44: suggest_vertical_stack_composites()가 idioms.Match.ports를 | 2 | 0 | 0 | 2 | S128 | 1 |
| S138 | major | A | 11788-11847 | === Test 45: refine_differential_and_mirror_relations()의 | 3 | 0 | 0 | 4 | S128, S136 | 1 |
| S139 | major | A | 11848-11883 | === Test 46: find_verified_differential_and_mirror_relations()의 | 3 | 0 | 0 | 3 | S128 | 0 |
| S140 | major | A | 11884-11936 | === Test 47: audit_vertical_stack_id_vs_kcl() -- declared vertical_sta | 6 | 0 | 0 | 4 | S64, S111, S122, S128 | 3 |
| S141 | major | A | 11937-11987 | === Test 48: merge_layout_groups_by_matching_pairs() -- vertical_stack | 7 | 0 | 0 | 2 | S100, S113, S138, S140 | 3 |
| S142 | sub | A | 11988-12002 | [current_forced=False까지 전부 넘기면(세션9/10 dx 악화 반례 재현 의도) | 1 | 0 | 0 | 0 | S141 | 2 |
| S143 | sub | A | 12003-12021 | [current_forced=False라도 실제로 물리적으로 이어진(오일러 실현 가능한) 쌍이면 | 1 | 0 | 0 | 1 | S140 | 1 |
| S144 | major | A | 12022-12090 | === Test 49: audit_vertical_stack_id_euler_feasibility() -- declared | 10 | 0 | 0 | 3 | S140, S142, S143 | 18 |
| S145 | sub | A | 12091-12114 | [합성 fixture -- 완전히 무관한(공유 net 없는) 두 소자를 한 declared 그룹으로 | 2 | 0 | 0 | 2 |  | 0 |
| S146 | major | A | 12115-12140 | === Test 50: find_euler_repair_options() -- unresolved_row를 resolved로 | 3 | 0 | 0 | 2 | S141, S144 | 1 |
| S147 | sub | A | 12141-12163 | [합성 fixture -- 같은 행 안에서는 절대 안 풀리는(서로 완전히 끊긴) blocked 그룹을 | 2 | 0 | 0 | 2 | S137 | 0 |
| S148 | major | A | 12164-12204 | === Test 51: derive_horizontal_stack_groups() -- vertical_stack_id 그룹( | 5 | 0 | 0 | 3 | S141, S142, S144, S146 | 2 |
| S149 | sub | A | 12205-12220 | [합성 fixture -- 매칭 파트너가 없는 순수 mixed-kind vsid 하나가 kind로만 | 2 | 0 | 0 | 1 |  | 0 |
| S150 | major | D | 12221-12224 | === Test 52: propose_vertical_stack_id_gap_fill() -- audit_vertical_st | 0 | 0 | 0 | 0 |  | 0 |
| S151 | sub | A | 12225-12246 | [합성 fixture -- internal_series gap은 채우고 declared_matching_pair gap은 | 3 | 0 | 0 | 1 |  | 0 |
| S152 | sub | A | 12247-12263 | [합성 fixture -- 같은 소자가 서로 다른 edge에서 서로 다른 vsid를 물려받게 | 2 | 0 | 0 | 1 |  | 0 |
| S153 | sub | A | 12264-12295 | [실제 회로 -- two_stage_ota.topology.json 원본(device_roles에 M1/M2/M6 | 3 | 0 | 0 | 1 | S123, S144, S148 | 1 |
| S154 | sub | A | 12296-12326 | [load_topology() 배선 -- 위 제안이 실제로 harness 최상위 진입점에서 | 4 | 0 | 0 | 3 | S144, S153 | 1 |
| S155 | major | A | 12327-12368 | === Test 53: propose_device_roles_gap_fill() -- netlist(+load_topology | 5 | 0 | 0 | 3 | S58, S144, S154 | 2 |
| S156 | sub | A | 12369-12389 | [compensation_stage_devices를 넘겨도 M1a/M4a/M15/M25 등 8개 소자에 gm_id_role이 | 3 | 0 | 0 | 1 | S132, S136, S155 | 2 |
| S157 | sub | A | 12390-12467 | [실제로 M1(compensation.stage_devices 소속)에 gm_id_role을 채운 topology.json으로 | 3 | 1 | 1 | 3 | S144 | 0 |
| S158 | major | A | 12468-12498 | === Test 54: propose_device_roles_gap_fill() -- 층위1 폴백(비대칭/폴딩 구조라 | 3 | 0 | 0 | 3 | S67, S144, S155 | 2 |
| S159 | major | A | 12499-12547 | === Test 55: apply_device_roles_gap_fill() -- 실제 파일 읽기/병합/쓰기 왕복 + | 5 | 0 | 0 | 3 | S144, S158 | 3 |
| S160 | major | A | 12548-12606 | === Test 56: propose_device_roles_gap_fill()/apply_device_roles_gap_fi | 6 | 0 | 0 | 3 | S144, S148, S158, S159 | 2 |
| S161 | major | A | 12607-12639 | === Test 57: find_authoritative_sizing_devices()/find_unreviewed_devic | 5 | 0 | 0 | 2 | S144 | 1 |
| S162 | sub | A | 12640-12677 | [합성 fixture -- 일반 소자(authoritative 아님)의 gm_id_role/L_role이 파일에 | 3 | 1 | 1 | 3 | S144, S159, S161 | 0 |
| S163 | major | A | 12678-12724 | === Test 58: find_unreviewed_matching_pairs() -- matching_pairs도 revie | 4 | 1 | 1 | 2 | S144, S159 | 1 |
| S164 | sub | A | 12725-12736 | [differential(offset) 출처는 review 없이도 메모리에 자동 병합되는지 -- M1/M2 | 1 | 0 | 0 | 2 | S163 | 0 |
| S165 | major | A | 12737-12751 | === Test 60: audit_theta_root_direction() -- sizing_roles.theta의 'A'/' | 1 | 0 | 0 | 1 | S144 | 1 |
| S166 | sub | A | 12753-12771 | [세션 초반 실제로 저질렀던 버그(M106을 root로 두고 M108을 그 반대로 참조) 재현 -- 잡히는지] | 2 | 0 | 0 | 1 | S160, S165 | 1 |
| S167 | sub | A | 12773-12787 | [current_reuse_telescopic_ota의 kcl_tail_M38(root=M38 tail, reference=M | 1 | 0 | 0 | 1 | S144 | 0 |
| S168 | sub | A | 12789-12804 | [나머지 실제 library 회로(folded_cascode/two_stage_ota)도 findings 0건인지 -- 이미  | 2 | 0 | 0 | 2 | S144 | 0 |
| S169 | major | A | 12805-12829 | === Test 61: propose_theta_kcl_gap_fill() -- 전류(ID) KCL 구조를 connectivi | 4 | 0 | 0 | 1 | S144, S156, S166 | 1 |
| S170 | sub | A | 12831-12856 | [compensation_stage_devices=[M102,M103,M201,M301]을 주면 위 한계가 풀리는지 -- 20 | 6 | 0 | 0 | 1 | S156, S169 | 2 |
| S171 | sub | A | 12858-12870 | [folded_cascode -- 규칙 2.7(gate mirror, MP->M3/M4)가 실제로 필요한지 재확인 -- 처음엔 | 2 | 0 | 0 | 1 | S144, S170 | 2 |
| S172 | sub | A | 12872-12888 | [서로 다른 자유 root 그룹(MP측/M9-M10측)이 같은 KCL 노드로 수렴하면 placeholder 값 충돌(0/음수) | 2 | 0 | 0 | 2 | S160, S171 | 0 |
| S173 | major | A | 12889-12936 | === Test 62: apply_theta_kcl_gap_fill() -- propose_theta_kcl_gap_fill( | 5 | 0 | 0 | 2 | S119, S144, S170, S171 | 0 |

## design_report.py -- 블록 319~382 (64줄), sys.argv 사용 False

섹션 5(머리 P 포함) / 범주 P 1 · D(표지만) 0 · A(assert·raise 판정) 4 · B(print 판정만) 0 · C(판정 없음) 0 / C 중 뒤 섹션이 의존 0 / assert 13 / raise AssertionError 0 / 거부 try 0 / print PASS·FAIL 토큰 5 / 앞 섹션 의존 섹션 3 / `lut` 읽는 섹션 0
모듈 이름 읽음 4개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 320-331 | (머리) | 0 | 0 | 0 | 0 |  | 3 |
| S1 | major | A | 333-344 | === Test 1: build_topology_device_table() -- 51개 소자가 matching_pairs로 그 | 3 | 0 | 0 | 1 | S0 | 1 |
| S2 | major | A | 345-354 | === Test 2: assemble_report_data() -- instance.json 없이도(사이징 전) 안 죽는지 = | 4 | 0 | 0 | 1 | S0, S1 | 0 |
| S3 | major | A | 355-375 | === Test 3: assemble_report_data() -- 실제(과거, partial scope) instance.j | 5 | 0 | 0 | 1 | S0 | 0 |
| S4 | major | A | 376-382 | === Test 4: 빈 report({}) -- 아무 섹션도 없어도 크래시 없이 최소 HTML만 생성 === | 1 | 0 | 0 | 2 |  | 0 |

## topology_library.py -- 블록 528~694 (167줄), sys.argv 사용 False

섹션 16(머리 P 포함) / 범주 P 1 · D(표지만) 0 · A(assert·raise 판정) 10 · B(print 판정만) 0 · C(판정 없음) 5 / C 중 뒤 섹션이 의존 2 / assert 17 / raise AssertionError 0 / 거부 try 0 / print PASS·FAIL 토큰 4 / 앞 섹션 의존 섹션 7 / `lut` 읽는 섹션 0
모듈 이름 읽음 8개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 529-533 | (머리) | 0 | 0 | 0 | 0 |  | 0 |
| S1 | major | C | 535-538 | # Miller 2단 OTA (GBW=20MHz, CL=3pF, Z=10, NDP=4) — prev_cggs=None(초기 반 | 0 | 0 | 0 | 0 |  | 0 |
| S2 | major | A | 540-550 | # NMCNR 3단 (GBW=5MHz, CL=10pF, PM_target=70deg, kg=0.5) | 2 | 0 | 0 | 0 |  | 1 |
| S3 | major | C | 552-561 | # nmcnr_predict_ac_response() 스모크 테스트 — sky130-worked-example.md §12.3 | 0 | 0 | 0 | 0 | S2 | 0 |
| S4 | major | A | 563-602 | # nmcnr_predict_ac_response() 독립 재유도 회귀 검증(2026-08-19 세션37 연속) — | 2 | 0 | 0 | 1 |  | 0 |
| S5 | major | C | 604-606 | # nmcnr_check_dominant_pole_approximation() -- Eq10/11의 '우세극' 전제 자체를 | 0 | 0 | 0 | 0 |  | 2 |
| S6 | sub | A | 607-615 | [nmcnr_amplifier 실제 스펙: GBW=816kHz/CL=1e-10F/PM_target=70도/kg=0.5] | 1 | 0 | 0 | 1 | S5 | 0 |
| S7 | sub | A | 617-629 | [GBW/CL/kg 불변성 -- gbw_ratio/pm_diff가 PM_target_deg에만 의존하고 GBW/CL/kg와는 | 2 | 0 | 0 | 1 | S5 | 0 |
| S8 | sub | A | 631-642 | [PM_target_deg만 바꿔가며 valid=True가 되는 지점 탐색 -- 물리적으로 타당한 60~90도 | 2 | 0 | 0 | 1 |  | 0 |
| S9 | major | C | 644-650 | # NGCC 3단 (Lee et al. Table 4 예제: k=4, GB=10MHz, CL=10pF, alpha=0.3) — | 0 | 0 | 0 | 0 |  | 0 |
| S10 | major | C | 651-654 | # current-reuse telescopic OTA(Xie & Chen 원문 Eq.2-6, 2026-07-31 -- 원문  | 0 | 0 | 0 | 0 |  | 2 |
| S11 | sub | A | 656-659 | [Eq.6 ratio=tan(PM_target) -- 원문 수치 예제(PM=70도->2.8)와 검산] | 1 | 0 | 0 | 0 |  | 0 |
| S12 | sub | A | 661-668 | [Eq.4/5 cold-start(prev_cggs=None) -- Cgg1=0 가정, beta=0.5 정확히, gmp=gmn | 2 | 0 | 0 | 0 | S10 | 3 |
| S13 | sub | A | 670-678 | [Eq.4 -- Cgg1_total(M1a+M4a 합)을 명시적으로 주면 beta/gmp/gmn이 그만큼 변함] | 2 | 0 | 0 | 0 | S10, S12 | 2 |
| S14 | sub | A | 680-685 | [세션30 -- gm2가 gmp2/gmn2로 분리되고 항상 gmp2=gmn2=gm2/2(50:50 기본값)임을 확인] | 2 | 0 | 0 | 0 | S12, S13 | 0 |
| S15 | sub | A | 687-694 | [Eq.6 -- Cgg2(prev_cggs[2]+prev_cggs[3])를 키우면 gm2(=gmp2+gmn2)도 커짐(단조성) | 1 | 0 | 0 | 0 | S12, S13 | 0 |

## audit_current_forced.py -- 블록 153~180 (28줄), sys.argv 사용 True

섹션 2(머리 P 포함) / 범주 P 1 · D(표지만) 0 · A(assert·raise 판정) 0 · B(print 판정만) 0 · C(판정 없음) 1 / C 중 뒤 섹션이 의존 0 / assert 0 / raise AssertionError 0 / 거부 try 0 / print PASS·FAIL 토큰 0 / 앞 섹션 의존 섹션 1 / `lut` 읽는 섹션 0
모듈 이름 읽음 4개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 154-166 | (머리) | 0 | 0 | 0 | 0 |  | 1 |
| S1 | major | C | 168-180 | # current_forced audit -- matching_pairs 축A 선언과 sizing_roles.theta 양방향 | 0 | 0 | 0 | 0 | S0 | 0 |

## sky130_lut_sweep.py -- 블록 313~337 (25줄), sys.argv 사용 False

섹션 3(머리 P 포함) / 범주 P 1 · D(표지만) 0 · A(assert·raise 판정) 0 · B(print 판정만) 0 · C(판정 없음) 2 / C 중 뒤 섹션이 의존 1 / assert 0 / raise AssertionError 0 / 거부 try 0 / print PASS·FAIL 토큰 0 / 앞 섹션 의존 섹션 2 / `lut` 읽는 섹션 0
모듈 이름 읽음 10개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 314-315 | (머리) | 0 | 0 | 0 | 0 |  | 2 |
| S1 | major | C | 317-318 | === NMOS (nfet_01v8) === | 0 | 0 | 0 | 0 | S0 | 1 |
| S2 | major | C | 320-337 | === PMOS (pfet_01v8) === | 0 | 0 | 0 | 0 | S0, S1 | 0 |

## topology_to_markdown.py -- 블록 187~205 (19줄), sys.argv 사용 True

섹션 1(머리 P 포함) / 범주 P 1 · D(표지만) 0 · A(assert·raise 판정) 0 · B(print 판정만) 0 · C(판정 없음) 0 / C 중 뒤 섹션이 의존 0 / assert 0 / raise AssertionError 0 / 거부 try 0 / print PASS·FAIL 토큰 0 / 앞 섹션 의존 섹션 0 / `lut` 읽는 섹션 0
모듈 이름 읽음 4개, 미해결 이름 []

| S | 종류 | 범주 | 줄 | 표지 | assert | raise AE | 거부 try | PASS/FAIL print | 앞 섹션 의존 | 뒤 섹션이 의존 |
|---|---|---|---|---|---|---|---|---|---|---|
| S0 | prelude | P | 188-205 | (머리) | 0 | 0 | 0 | 0 |  | 0 |

