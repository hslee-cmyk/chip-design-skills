# sizing_recipe.py 3022~5044 함수 전수 감사 (agent2)

- 대상: `skills/analog-gmid-design/assets/sizing_recipe.py` 모듈 최상위 함수·클래스 3022(`_metric_sum_area`) ~ 5042(`_mna_solve_smallsignal` 끝). 중첩 함수는 부모 행에 요약.
- 운영 경로 판정 근거: `workspaces/run_harness.py:303-345`가 4개 회로(two_stage_ota / current_reuse_telescopic_ota(파일럿) / folded_cascode / nmcnr_amplifier)를 모두 돌린다. metric은 `_build_theta_evaluator._evaluate` 끝(`:9468`)에서 `compute_metric`(`:5842`) -> `_METRICS_REGISTRY`(`:5656-5683`) 문자열 디스패치로 호출된다. 따라서 **topology.json `sizing_roles.metrics[*].type`에 선언된 타입만 운영 도달**이다(선언 전수표는 문서 끝 부록).
- self-test 범위는 `:12571~`. "간접"은 L5/L5c가 파일럿 topology로 `optimize_full_circuit_budget()`를 실제로 돌리는 경로(`:13105`, `:13370`)로만 실행된다는 뜻(이름으로 단언하는 테스트 없음).
- 등급: R0 그대로 재사용 / R1 재사용+국소 수정 / R2 재설계 대상 / D 미사용 / DUP 중복.

| 함수(줄) | 책임 | 계획 대응 | 운영호출자 | 등급 | 이관 목적지 | self-test | 근거/비고 |
|---|---|---|---|---|---|---|---|
| `_metric_sum_area`(3022) | `devices`(없으면 ctx.sized 전체)의 W*L 합 | §7.9 v3.3 면적 제약(plan:681,1113) / 계획대로 | registry `sum_area` <- 파일럿·two_stage `area_um2` | R0 | gmid_sizing_engine.py | 12728,12731 | 순수 합산, 상태 없음 |
| `_metric_gain_stages_sum`(3028) | 스테이지별 Σgm/Σgds를 dB로 합산 | §7.2 gain-budget(plan:673,1023) / 계획대로 | registry `gain_stages_sum` <- 파일럿 `gain_db` | R0 | gmid_sizing_engine.py | 12729,13938 | 스테이지 독립 가정(부하효과 무시)은 폐형식 한계. 전체회로 값은 `smallsignal_gain_db`(5615)가 따로 잰다 -- 근사 수준이 달라 DUP로 보지 않음 |
| `_folded_cascode_rout`(3040) (+중첩 `ro`) | folded-cascode Rout_p/Rout_n/병렬 폐형식 | 계획 외(세션35, plan에 폐형식 명세 없음) | `_metric_folded_cascode_gain_db`/`_pm_deg` 전용 헬퍼 -> folded_cascode 운영 | DUP | gmid_sizing_engine.py | 없음 | 소비자 둘이 DUP라 종속. ro_fold 계산(3054)이 `_nmcnr_stage1_rout`(3126)와 같은 식 복제 |
| `_metric_folded_cascode_gain_db`(3061) | gm1·(Rout_p‖Rout_n) dB | 계획 외(세션35) | registry <- folded_cascode `gain_db` 제약 | DUP | gmid_sizing_engine.py | 없음 | 같은 개념을 회로무관 MNA `_metric_smallsignal_gain_db`(5615)가 계산(파일럿·two_stage는 이미 그쪽). docstring 3066-3068: sympy/SPICE 검증 안 됨. 운영 중이므로 삭제 전 JSON 타입 이전+4회로 측정 필요 |
| `_metric_folded_cascode_pm_deg`(3077) | 2-pole 근사 PM, C_fold=Cgg 합 | 계획 외(세션35) | registry <- folded_cascode `pm_deg` 제약 | DUP | gmid_sizing_engine.py | 없음 | `_metric_parasitic_pm_deg`(4329, L2 실제 주파수응답)와 같은 개념. 접합용량·Y-branch 극 무시(3084-3091) |
| `_nmcnr_stage1_rout`(3108) (+`ro`) | NMCNR stage1 비대칭 캐스코드 Rout | 계획 외(세션37) | `_nmcnr_predict` -> nmcnr 운영 | R0 | gmid_sizing_engine.py | 14783,14804 | 순수 계산. ro_fold 식은 3054와 중복(국소) |
| `_nmcnr_predict`(3133) (+`ro`) | 실사이징 gm/R로 `topology_library.nmcnr_predict_ac_response` 호출, ctx 캐시 | 계획 외(세션37) | `_metric_nmcnr_gain_db`/`_pm_deg` | R0 | gmid_sizing_engine.py | 14816 | 캐시 키 = spec 해시+footprint gm/gds 내용(3169-3170), 수명 ctx(평가 1회) -> C-d 부합. 대상 모델은 sympy+ngspice 검증 완료(3135-3136) |
| `_metric_nmcnr_gain_db`(3187) | `_nmcnr_predict()["dc_gain_db"]` | 계획 외 | registry <- nmcnr `gain_db` | R0 | gmid_sizing_engine.py | 14783 | 얇은 래퍼 |
| `_metric_nmcnr_pm_deg`(3194) | 첫 0dB 교차 PM, 교차 없음/notch면 ValueError | 계획 외 | registry <- nmcnr `pm_deg` | R0 | gmid_sizing_engine.py | 14783,14819 | 정의불가 상태를 명시 실패(3203-3209) |
| `_metric_flicker_plus_thermal_sum`(3213) | stages 소자 열+1/f 잡음 RSS(V/√Hz) | §7.2 metric(plan:680,686) / 부분 | registry <- 파일럿 `noise_v_rthz` | R1 | gmid_sizing_engine.py | 14710,14716 | `gamma=2/3`,`freq=1.0`,`temperature_K=300` 기본값을 조용히 주입(3221-3223) -- 상수 금지 원칙 위반. 선언 필수로 바꿀 것 |
| `estimate_mismatch_sigma`(3241) | Pelgrom σ=slope/√(WL) | §7.6(plan:1012) / 계획대로 | `_metric_pelgrom_mismatch`(3256), `make_matching_feasibility_check`(7362) | R0 | gmid_sizing_engine.py | 14684,14724 | 순수. 단위 µm 관례 명시 |
| `_metric_pelgrom_mismatch`(3250) | 쌍 σ를 RSS(mV) | §7.6(plan:600,647) / 계획대로 | JSON 직접 선언 0건, 그러나 `_metric_input_referred_offset`(4760) 경유 운영 | R0 | gmid_sizing_engine.py | 14511,14724 | 같은 쌍 RSS가 `make_matching_feasibility_check` 7361-7364에 **복붙**(상대 쪽을 이 함수 호출로 바꿀 것) |
| `DiodeSelfConsistencyError`(3261) | diode Vgs=Vds 해 없음 전용 예외(ValueError 하위) | §7.3 B1(plan:63) / 계획대로 | solve/set_device_vds/diode_vds_cached | R0 | gmid_sizing_engine.py | 이름 단언 없음(간접) | 예외 계층만 제공 |
| `_gm_id_already_authoritative`(3281) | `_L_source`/`_gm_id_source` 태그로 gm_id 덮어쓰기 금지 판정 | §7.3 B16(plan:3962) / 부분 | `_evaluate` 9242,9311,9390 | R2 | circuit_state_graph.py | 없음 | §12.5.2 C-a "필드×writer 티어 권한표"의 임시판. 권위가 두 문자열 필드로 갈라져 있고(3272-3275 주석 자인), `apply_diode_self_consistent_gm_id` 3804는 이 함수를 안 쓰고 `_L_source`만 본다 -> 판정 정의 2벌 |
| `is_diode_connected`(3287) | gate==drain(connectivity만) | §7.3 B1(plan:3951) / 계획대로 | `_diode_set_cached`(5462), `_metric_stack_headroom_slack`(3475) | R0 | circuit_state_graph.py | 없음(probe 10개) | §12.3-5 diode 정의 3벌(16/1/20) 중 정답 정의. `stick_diagram.py:3087 find_diode_stacks`가 DUP 쪽 -- S1 "개념당 정의 하나"의 기준으로 채택 |
| `solve_diode_connected_vds`(3297) (+`g`) | LUT 격자 브래킷+bisection으로 diode 자기일관 vds | §7.3 B1/§10.2 A7(plan:1251,1307) / 계획과 다름: §8.4의 `_solve_diode_connected_vgs_fixed_point()` 이름·대입반복 대신 bisection | set_device_vds 3557, diode_vds_cached 3386, apply_diode(오류문) 3852 | R0 | gmid_sizing_engine.py | 13062 | 순수, 수렴 실패 명시(3368). 캐시는 호출자 몫 |
| `diode_vds_cached`(3374) | solve_diode_connected_vds 메모(해 없음도 None 캐시) | §7.3 C10(plan:3952) / 부분 | `_metric_stack_headroom_slack` 3481 | R1 | gmid_sizing_engine.py | 없음 | 키에 `id(lut)`(3383) -- §12.3-7/C-d 위반(LUT 내용이 아니라 객체 id). 함수 속성 dict **상한 없음**. `set_device_vds` 3557은 이 캐시를 안 쓰고 원함수를 직접 호출 |
| `_metric_stack_headroom_slack`(3392) (+중첩 `find` union-find) | vertical_stack_id 그룹별 (예산 - Σdiode Vgs - Σ비diode vds) 최솟값, 측정불가 그룹 있으면 ValueError | §7.3 A8 재해석(plan:61,1121,1228) / 계획대로 | registry <- 파일럿 `stack_headroom_slack_v` | R1 | gmid_sizing_engine.py(값) + 그룹/union-find 구조는 circuit_state_graph.py(S1) | 없음(간접) | 매 평가마다 `groups`·offset union-find·budget_reference를 topology에서 재구성(3428-3449) -- 입력이 topology뿐인 정적 구조라 S1 캐시 대상(§12.4 "정적 스택 구조 매 평가 재구성"과 같은 부류). offset union은 `_hr_vfind`(7420) 계열과 개념 중복. `vertical_stack_id` 선언을 검증 없이 신뢰(3417) |
| `set_device_vds`(3516) | `ctx.sized[name]["vds"]` 단일 setter + diode 자기일관 검사 + `_vds_source` 출처 태그 | §7.3 B1/B13(plan:63,81,1251) / 계획대로 | 11곳(5455,6089,6096,6164,7694,7741,7772,8127,8851 등) | R1 | circuit_state_graph.py(S2 타입 setter) | 없음(간접) | §12.5.2 C-a가 "`set_device_vds` 일반화"로 명시한 원형. 국소 수정: (1) 3557이 캐시 없이 `solve_diode_connected_vds` 직접 호출(회당 LUT 100회+) (2) vds만 보호 -- vsb는 `reconcile_vsb_from_nodes` 4012가 원시 대입, gm_id/W는 여러 곳 dict 대입 -> 필드 전반으로 확장 필요 (3) 검사 불가 시 `+unchecked` 태그만 남기고 진행 |
| `diode_vds_window`(3570) | diode(+VGS 공유 미러 멤버)가 W_bounds 안에 드는 vds 구간 (lo,hi) | §7.3/§7.9 B22(plan:124,1266,1297) / 계획대로 | `_hr_resolve_vertical_group` 8014, `feasible_L_window` 2713/2750 | R1 | gmid_sizing_engine.py | 13401,14069,14344 | 캐시 키 `id(lut)`/`id(m[0])`(3617-3619) -> C-d 위반, 함수 속성 dict 상한 없음(§12.6-7 계열). `except (ValueError,KeyError): continue`(3630,3642)는 격자점 범위밖 스킵이라 정당 |
| `solve_stacked_diode_pair`(3659) | 적층 diode 2개 (v_up,v_lo) 격자 동시 스캔, 아래 vsb=vsb_up+v_up 결합 | §10.3 A8/B25(plan:2604,3966) / 계획대로(B25) | `_hr_resolve_vertical_group` 7859 | R2 | circuit_state_graph.py(C-c 순환 블록) | 없음(간접) | §12.3-8 순환 "vsb↔vds(적층 diode)"를 **2소자 한정 격자 스캔**으로 우회 -- C-c 명시적 고정점 블록으로 대체 대상. 캐시 없음(O(N²) LUT 조회, 매 평가). **결함**: `constrain_up=False`에서 LUT 조회 실패 시 `idu_up=1.0`(3707)으로 조용히 대체해 가짜 `W_up=L·ID`를 반환 -> 호출부 tie-break가 그 W로 균형비 계산(7908-7910 `s[2]`) |
| `apply_diode_self_consistent_gm_id`(3743) | diode gm_id를 자기 vds에서 역유도(gm_id_for_vgs)하고 gm/W/gds 마감, 불일치는 명시 실패 | §7.3 B16(plan:1260,2593) / 계획과 다름(계획 §0.2는 vds-먼저 방향, 구현은 역방향 -- docstring 3755-3760, 사용자 승인) | `_evaluate` 9236 | R1 | gmid_sizing_engine.py | 13055 | 국소: (1) `W_bounds` 기본값 `(1e-6,200e-6)` 주입(3791) -- 상수 기본값 (2) 3804가 `_gm_id_already_authoritative()` 대신 `_L_source`만 검사(정의 2벌) (3) §12.3-8 순환 "diode vds↔gm_id↔W"의 한 방향 -- C-c 블록 편입 시 재배치 |
| `NodeVoltageReport`(3887) | propagate 결과 dataclass(nodes/unresolved/conflicts/passes) | §7.5(plan:62) / 계획대로 | propagate_node_voltages | R0 | circuit_state_graph.py(S2 노드전압) | 없음 | 값 컨테이너. 버전/출처 필드 없음(S2 이관 시 추가) |
| `propagate_node_voltages`(3895) | 레일에서 vds로 전 노드 DC 전압 전파(sorted 결정론, 다중도달 conflicts 기록) | §7.5 `verify_node_voltage_consistency` 1단계 / 부분: conflicts를 Violation으로 올리지 않음, 계획의 "게이트 net Vgs 일치" 검사 없음, passive 무시 | reconcile 3999, audit 4026, `_hr_resolve_vertical_group` 7849·8004(루프 안, `except Exception`) | R1 | circuit_state_graph.py | 없음(probe_node_voltage_audit) | **§12.6-2 확인**: `conflicts`를 읽는 코드가 3891-3954 밖에 0건(grep; 11226은 무관 지역변수) -> 먼저 도달한 경로 값이 정본. 캐시 없음, 평가당 19회(§12.3-4). 7852·8007의 광범위 `except Exception: None`이 이 함수 실패를 조용히 fallback(`_vsb_source="pair_solve_fallback"/"mirror_window_fallback"`)으로 바꿈 |
| `derive_vsb_from_nodes`(3957) | 소스 노드전압 -> vsb(NMOS=V_s, PMOS=vdd-V_s), 모르면 None | §7.5 B9(plan:62,2603) / 계획대로 | reconcile 4006, audit 4033, 7847, 8002 | R0 | circuit_state_graph.py | 없음 | 순수. 벌크=레일 가정(3962-3964) 명시 |
| `reconcile_vsb_from_nodes`(3976) | 헤드룸 후 전 소자 vsb를 노드전압으로 덮어씀, undetermined 반환 | §10.3 B9(plan:2603,3798) / 부분 | `_evaluate` 9207 | R1 | circuit_state_graph.py(C-b) | 없음(간접) | **§12.6-1 확인**: vsb만 대입(4012), 옛 vsb 기준으로 이미 계산된 W/gm/gds는 갱신·무효화 안 함 -> 버전 혼재(7/51). `rep.conflicts` 무시. setter 우회(원시 대입). 국소 수정: changed 소자 재사이징 또는 봉인 게이트로 거부 |
| `audit_vsb_consistency`(4018) | 최종 vsb vs 노드전압 유도값 불일치 목록 | §10.3 B9 게이트(plan:2603,3964) / 부분 | `_evaluate` 9439(불일치 시 9443 ValueError) | R1 | circuit_state_graph.py(봉인 게이트) | 없음(간접) | reconcile(4001-4014)과 같은 루프를 다시 돌며 propagate 재계산(캐시 없음). **vsb만 비교** -> W/gds 버전 불일치는 통과(§12.3-3). 실패가 `ValueError`라 SLSQP 크래시 경로(§12.6-3, 9445) |
| `signal_path_nodes`(4043) (+`_reach`) | gate/source->drain 방향 그래프에서 excite∩sense 도달 내부노드 | §7.11 L1(plan:2309,2317) / 이후 L2로 대체 | **없음**(grep: `tests/probe_parasitic_pm_all_circuits.py`만) | D | (삭제 후보) | 없음 | 4354-4356 docstring이 L2에서 "원천적으로 필요 없어짐"이라 명시. §12.4가 소비자라 적은 것이 오류임을 재확인. 방향 규칙이 단일 DAG가 안 됨(§12.3-9) -> S1v 재활용 가치 낮음 |
| `node_pole_estimate`(4080) | 노드별 G/C 1차 pole 추정 | §7.11 L1(plan:2310,2850) / 이후 L2로 대체 | **없음**(probe만) | D | (삭제 후보) | 없음 | 4343-4346: L1 값(34.2도) 무효라고 자인. **§12.6-6 광범위 except 4138 확인**: `except (KeyError, ValueError): pass`로 Cgg 누락을 조용히 버림 -- 운영 미호출이라 영향은 probe 한정 |
| `_resolve_capacitor_farad`(4157) | passive 커패시터 값: value_farad > ctx.derived[key] > spec[key] > 오류 | §7.11 L2/§10.8(plan:2874) / 계획대로 | `_mna_stamp_capacitance` 4225 | R0 | gmid_sizing_engine.py | 없음(간접) | 0으로 때우지 않음(4186). derived 우선은 기존 관례. 출처 기록 없음(S2 이관 시 writer 표기 필요) |
| `_mna_stamp_capacitance`(4192) | 소자 Cgg(gate-source)+선언 커패시터 (a,b,C) 목록 | §7.11 L2(plan:2873) / 부분(Cgd·접합용량 없음, 명시) | `build_ac_network` 4259 | R1 | gmid_sizing_engine.py | 없음(간접) | **§12.6-6 광범위 except 4217 확인**: `except (KeyError, ValueError): continue`로 LUT 범위 밖 소자의 Cgg를 조용히 누락 -> cap_total 과소 -> PM 과대. 인자 `idx` 미사용(4259에서 None). 수정: 누락 목록 반환/실패 |
| `build_ac_network`(4230) | omega 무관 부분(소자 스탬프·용량·노드목록·고정노드)을 한 번 조립 | §7.11 L2 중복제거(plan:3135,3976) / 계획대로 | `_metric_parasitic_pm_deg` 4394, `full_circuit_response_at_omega` 4285(network 미전달 시) | R1 | gmid_sizing_engine.py(값은 S2 블록 memo) | 없음(간접) | 재사용 수명이 metric 한 번의 스윕뿐. 같은 평가에서 `_full_circuit_response`(5548)가 `_full_circuit_devices`를 smallsignal metric마다 **다시 조립**하고, 노드목록 루프(4252-4258)는 5552-5559와 동일 코드 -> ctx.sized 내용 해시 키로 평가 내 1회 조립 공유(§12.5.3) |
| `full_circuit_response_at_omega`(4267) (+중첩 `add`) | (G+jωC)v=b 복소 MNA 풀이 | §7.11 L2(plan:2873) / 계획과 다름: 계획은 고유값 pole 추출, 구현은 주파수 직접 풀이(근거 4274-4282) | `_metric_parasitic_pm_deg._h` 4397 | DUP | gmid_sizing_engine.py | 없음(간접) | 트랜지스터 스탬프 6줄(4305-4311)이 `_mna_solve_smallsignal`(4970) 5016-5022와 **동일**. ω=0이면 DC 해와 같음 -> 복소 solver 하나로 합칠 것. 이쪽엔 고립노드 진단(5029-5034)이 없음 |
| `_metric_parasitic_pm_deg`(4329) (+중첩 `_h`) | DC~ω_c 25점 로그스윕 위상 언랩 -> PM=180-누적지연 | §7.11 L2(plan:2311,2946) / 계획과 다름(위와 같음) | registry <- 파일럿 `parasitic_pm_deg` 제약 | R1 | gmid_sizing_engine.py | 13280,13300 | 국소: (1) `n_pts=25`, 시작 `ω_c·1e-4`(4407-4408)가 박힌 상수이고 "A0가 1e4를 넘지 않는 한 안전"(4405)이라는 가정에 의존 -- 상수 금지 원칙 (2) 4217 Cgg 누락을 그대로 물려받아 PM 과대 가능 (3) ω_c를 derived 우선으로 읽음(4384) -- 출처 기록 없음 |
| `_metric_kcl_residual`(4430) (+중첩 `add`) | 내부 노드 ΣI 잔차 최댓값(ideal_sources value_amp 반영, null이면 노드 제외) | §7.5 보강 B8/B14(plan:60,2585) / 계획대로(§7.5엔 KCL 검사 없음 -> 보강) | registry <- 파일럿 `kcl_residual_uA` | R1 | gmid_sizing_engine.py | 없음(probe_physical_consistency) | 계산 자체는 순수. 국소: 레일 이름을 인라인 튜플(4456)로 다시 정의 -- `_DEFAULT_RAIL_HI/LO`(3882-3883)와 정의 2벌. passive 전류 미계상(명시, 4448) |
| `_metric_supply_current`(4502) | PMOS source/NMOS drain이 supply 레일인 소자 ID 합(실제 공급전류) | §10 A3(plan:60,2563) / 부분 | registry <- 파일럿 `supply_current_uA`(보고용) | R1 | gmid_sizing_engine.py | 없음(probe_supply_current) | 레일 튜플 인라인(4524) 중복. **배선 문제**: docstring이 `sum_current`는 스택 중복계상으로 2.82배 틀린 전력이라고 규명(4506-4512)했지만, 4개 회로 objective는 전부 `minimize power_uA`=`sum_current`(JSON 부록). 같은 개념 정의 2벌 중 틀린 쪽이 목적함수 -- 교체는 엔진 동작 변경이라 사용자 승인 필요 |
| `_mirror_ratio_aggregate`(4540) | max/rss 집계, 알 수 없는 aggregate는 실패 | §10.13(plan:3409) / 계획대로 | 두 mirror metric | R0 | gmid_sizing_engine.py | 간접(13810-13811) | 순수. 빈 목록이면 0.0 반환(4546-4547) -- 쌍 0개가 "오차 0"과 구분 안 됨(stack_headroom_slack 3499-3507이 금지한 패턴과 같은 모양, 참고) |
| `_mirror_ratio_error_pairs`(4551) | ratio 쌍마다 (ΔVDS/V_A, 입력환산 V), ctx.derived 캐시 | §10.2 A4/§10.13(plan:3409,3893) / 부분 | 두 mirror metric | R1 | gmid_sizing_engine.py(값) + 쌍/미러군은 circuit_state_graph.py(S1) | 13819 | **§12.6-5 확인**: `a, b = names[0], names[1]`(4578) -- 3소자 이상 그룹은 첫 쌍만 검사. V_A·gm_id를 `a` 쪽만 씀(4585-4587). 선언 ratio 쌍 18개 중 11개는 connectivity상 미러 아님(§12.3-5) -> S1 미러군(`l_sharing_classes` 2385)에서 쌍 생성. 캐시는 `ctx.derived["_mirror_ratio_error_pairs"]`에 넣어 derived 네임스페이스에 사적 키 혼입(C-a 출처 없음) |
| `_metric_mirror_ratio_error_input_referred`(4597) | pairs의 V 성분 집계 | §10.13(plan:3263,3320) / 계획대로 | registry <- 파일럿 `mirror_ratio_error_mV` | R0 | gmid_sizing_engine.py | 13811 | 얇은 래퍼(결함은 `_mirror_ratio_error_pairs`에서 상속) |
| `_metric_mirror_ratio_error`(4617) | pairs의 % 성분 집계 | §10.2 A4(plan:60,72,1837) / 계획대로 | registry <- 파일럿 `mirror_ratio_error_pct` | R0 | gmid_sizing_engine.py | 13810 | 얇은 래퍼(결함 상속) |
| `input_referred_offset_pairs`(4644) | offset 쌍 중 전 소자 게이트가 ports input net인 쌍 | §10.14(plan:3491,3678) / 계획대로 | `_metric_input_referred_offset` 4751, `materialize_input_offset_pairs` 4715 | R1 | circuit_state_graph.py(S1 유도 사실) | 없음(간접) | 순수 구조 유도지만 `_load_full_topology_cached.__dict__["_cache"][path]` 사적 캐시에 직접 기록(4672,4691) -- 키가 경로 문자열(§12.3-7, C-d 위반: 파일 내용이 바뀌어도 적중). `ports` 선언은 파일럿·two_stage만 있음(grep: folded_cascode·nmcnr 0) |
| `materialize_input_offset_pairs`(4696) | 빌드 시 metric 선언 dict에 `_pairs`/`devices`를 제자리 기입 | §10.14(plan:3505) / 계획대로 | `_build_theta_evaluator` 8517 | R2 | circuit_state_graph.py(S1 유도 사실, status=derived) | 없음(간접) | 선언(사용자 입력)과 유도값을 같은 dict에 섞어 씀(4721-4722) -- C-a "declared/derived 구분·출처" 부재의 전형. 소비자 `_metric_device_footprint` 10137-10146, `make_matching_feasibility_check`가 선언을 읽는 척 유도값을 읽는다 |
| `_metric_input_referred_offset`(4724) | 입력 offset 쌍 σ를 gm 가중 RSS로 입력환산(V) | §10.14(plan:3484,3980) / 계획대로 | registry <- 파일럿·two_stage `mismatch_sigma_mV` 제약 | R1 | gmid_sizing_engine.py | 없음(간접) | 국소: (1) gm 없는 소자를 리스트 컴프리헨션으로 **조용히 제외**하고 남은 것만 평균(4762,4767) -- 전부 없을 때만 실패 (2) 쌍 kind를 `names[0]`만 봄(4758) (3) 빌드 시 materialize한 `spec["_pairs"]`를 안 쓰고 다시 조회 -> 쌍 출처 2곳 |
| `_metric_rail_referenced_voltage`(4772) | 소스가 레일이라는 전제로 게이트 DC 레벨 = rail∓VGS(LUT 역산) | 계획 외(세션6, plan에 이름 없음) | registry <- 파일럿 `vg15_level_v`/`vop1_level_v`, `_metric_battery_centering_deviation` | R1 | gmid_sizing_engine.py | 간접(13847) | 전제(source가 `rail`에 연결)를 검증하지 않음(4775-4776 자인) -- `_load_full_topology_cached`의 by_name으로 싸게 확인 가능. 선언 오류가 그럴듯한 전압으로 조용히 통과 |
| `_metric_battery_centering_deviation`(4793) | 두 출력게이트 레벨 합의 vdd 편차 | §10.7 class-AB(plan:601,683,2631) / 계획대로 | registry <- 파일럿 `classab_centering_dev_v` | R0 | gmid_sizing_engine.py | 13847 | 순수 조합(논문 절대값 미인용) |
| `_metric_nulling_resistor_ohm`(4819) | `_resolve_nulling_resistor_ohm` 보고 창구 | 계획 외(세션44, plan:601 언급만) | registry <- 파일럿 `rz1_ohm`/`rz2_ohm` | R0 | instance_report_builder.py(보고) 또는 gmid_sizing_engine.py | 없음 | 얇은 래퍼, ctx 캐시 공유 |
| `_cmrr_diff_pair_tail`(4828) | CMRR ≈ (ro_tail/2+1/gm)·gm 1차 근사 | 계획 외(배치 7-3i) | `_CMRR_ESTIMATOR_REGISTRY`(5238) <- folded_cascode·nmcnr `cmrr_db` | DUP | gmid_sizing_engine.py | 14739,14742 | 같은 개념을 회로무관 전체회로 MNA `_metric_smallsignal_ratio_db`(5586)가 계산(파일럿은 이미 전환, JSON 주석 1873). 운영 중이라 삭제 전 JSON 이전+측정 필요 |
| `_cmrr_telescopic_class_ab`(4837) | current-reuse 1단 open-loop CMRR 폐형식 | 계획 외(2026-07-31/08-03) | **없음**: 레지스트리(5239)에만 등록, `circuit_family: telescopic_class_ab`를 선언한 topology.json 0건 | D | (삭제 후보) | 14852,14996 | 파일럿이 `smallsignal_ratio_db`로 교체(JSON 1871,1873). 참조는 self-test와 `workspaces/.../spice/stage1_cmrr_*` 유도 스크립트뿐 |
| `_cmfb_amp_gain_diode_load`(4919) (+`g`) | CMFB 에러앰프 A_c 정확 폐형식 | 계획 외(배치 7-5c) | **없음**: 호출자 `_cmrr_telescopic_class_ab_cmfb` 5225/`_psrr_telescopic_class_ab_cmfb` 5338의 family를 선언한 JSON 0건 | D | (삭제 후보) | 15038 | self-test + `diagnose_cmrr_cmfb.py`(workspaces)에서만 참조 |
| `_mna_solve_smallsignal`(4970) (+`add`) | 실수 소신호 MNA를 LAPACK으로 풀고 고립노드 진단 | §7.6(plan에 이름 없음, 세션21) / 계획 외 | `_full_circuit_response` 5574 <- `smallsignal_gain_db`/`ratio_db`(파일럿 3개·two_stage 1개) | R1 | gmid_sizing_engine.py | 간접(15160 `_full_circuit_response`) | 국소: (1) 회로무관 solver인데 오류문에 `telescopic_class_ab`/`battery_vop1_side` 회로 전용 문구(5033,5039) -- 일반화 원칙 위반 (2) 스탬프가 4305-4311과 중복(DUP 상대) (3) 결과 캐시 없음 -- 같은 ctx에서 excite만 다른 풀이가 반복되므로 LU 분해 재사용 여지 |

## 요약

### 등급별 개수 (50개: 함수 48 + 클래스 2)

| 등급 | 개수 |
|---|---|
| R0 그대로 재사용 | 19 |
| R1 재사용+국소 수정 | 19 |
| R2 재설계 대상 | 3 |
| D 미사용 | 4 |
| DUP 중복 | 5 |

### R0 목록
`_metric_sum_area`, `_metric_gain_stages_sum`, `_nmcnr_stage1_rout`, `_nmcnr_predict`, `_metric_nmcnr_gain_db`, `_metric_nmcnr_pm_deg`, `estimate_mismatch_sigma`, `_metric_pelgrom_mismatch`, `DiodeSelfConsistencyError`, `is_diode_connected`, `solve_diode_connected_vds`, `NodeVoltageReport`, `derive_vsb_from_nodes`, `_resolve_capacitor_farad`, `_mirror_ratio_aggregate`, `_metric_mirror_ratio_error_input_referred`, `_metric_mirror_ratio_error`, `_metric_battery_centering_deviation`, `_metric_nulling_resistor_ohm`

### R2 목록
`_gm_id_already_authoritative`(C-a 권한표), `solve_stacked_diode_pair`(C-c 순환 블록), `materialize_input_offset_pairs`(S1 유도사실/출처)

### DUP 쌍 (등급 DUP 5개 + 다른 등급 행 안의 국소 중복)
1. `_metric_folded_cascode_gain_db`(3061) <-> `_metric_smallsignal_gain_db`(5615)
2. `_metric_folded_cascode_pm_deg`(3077) <-> `_metric_parasitic_pm_deg`(4329)
3. `_folded_cascode_rout`(3054 ro_fold) <-> `_nmcnr_stage1_rout`(3126)
4. `full_circuit_response_at_omega`(4305-4311 스탬프) <-> `_mna_solve_smallsignal`(5016-5022); `build_ac_network` 노드목록(4252-4258) <-> `_full_circuit_response`(5552-5559)
5. `_cmrr_diff_pair_tail`(4828) <-> `_metric_smallsignal_ratio_db`(5586)
6. (국소) `_metric_pelgrom_mismatch` RSS(3256-3258) <-> `make_matching_feasibility_check`(7361-7364)
7. (국소) `reconcile_vsb_from_nodes`(4001-4014) <-> `audit_vsb_consistency`(4028-4038) -- 같은 루프·propagate 2회
8. (국소, 개념) `_metric_sum_current`(3016, 범위 밖) <-> `_metric_supply_current`(4502) -- 전력 정의 2벌, 목적함수는 틀린 쪽
9. (국소) `is_diode_connected`(3287) <-> `stick_diagram.py:3087 find_diode_stacks`
10. (국소) `_gm_id_already_authoritative`(3281) <-> `apply_diode_self_consistent_gm_id` 3804 인라인 판정
11. (국소) `diode_vds_cached`(3374) <-> `set_device_vds` 3557 무캐시 직접호출
12. (국소) `_DEFAULT_RAIL_HI/LO`(3882) <-> 4456, 4524 인라인 튜플
13. (국소) 빌드 시 `spec["_pairs"]`(4721) <-> `_metric_input_referred_offset`의 재조회(4751)

### D 목록
- `signal_path_nodes`(4043), `node_pole_estimate`(4080): §7.11 L1, L2로 대체돼 운영 호출 0(probe 1개만). **삭제 후보**(배선할 곳이 없음 -- L2 docstring 4354-4356이 불필요하다고 명시).
- `_cmrr_telescopic_class_ab`(4837), `_cmfb_amp_gain_diode_load`(4919): 레지스트리엔 등록돼 있으나 해당 `circuit_family`를 선언한 topology.json 0건(파일럿이 `smallsignal_ratio_db`로 전환). **삭제 후보**(범위 밖 `_cmrr/_psrr_telescopic_class_ab_cmfb` 5170/5312, `_telescopic_class_ab_open_loop_response` 5064도 함께 도달 불가일 가능성 -- 해당 범위 감사자 확인 필요).

### 지시된 확인 항목 결과
- `reconcile_vsb_from_nodes`: vsb만 대입(4012), W/gm/gds 미갱신 -- **확인**(§12.6-1).
- `propagate_node_voltages` conflicts: 엔진에서 읽는 곳 0건 -- **확인**(§12.6-2). 추가로 7852·8007 `except Exception`이 호출 실패를 fallback으로 삼킴.
- `signal_path_nodes`/`node_pole_estimate`: 엔진 미호출 -- **확인**(D).
- `build_ac_network`: 운영 경로(파일럿 parasitic_pm_deg). 평가 간/metric 간 재사용 없음 -> R1.
- `_mirror_ratio_error_pairs` `names[0:2]`: **확인**(4578, §12.6-5).
- 광범위 except 4138(`node_pole_estimate`, 미운영)·4217(`_mna_stamp_capacitance`, 운영): **둘 다 확인**(§12.6-6).
- 신규 발견: `solve_stacked_diode_pair` 3707 `idu_up=1.0` 조용한 대체 -> 가짜 W_up이 7908 tie-break에 쓰임. `_metric_input_referred_offset` 4762 gm 없는 소자 조용한 제외. 캐시 키 `id(lut)`·상한 없음 2곳(3383, 3617). 상수 기본값 주입 3곳(3221-3223 잡음, 3791 W_bounds, 4407-4408 PM 스윕).

## 부록: topology.json 선언 metric type (운영 도달 판정 근거)

| 회로 | 선언 type |
|---|---|
| current_reuse_telescopic_ota(파일럿) | sum_current(objective), sum_area, gain_stages_sum, flicker_plus_thermal_sum, input_referred_offset, smallsignal_ratio_db×2, smallsignal_gain_db, rail_referenced_voltage×2, nulling_resistor_ohm×2, battery_centering_deviation, mirror_ratio_error, supply_current, kcl_residual, stack_headroom_slack, parasitic_pm_deg, mirror_ratio_error_input_referred |
| two_stage_ota | sum_current(objective), sum_area, smallsignal_gain_db, input_referred_offset |
| folded_cascode | sum_current(objective), folded_cascode_gain_db, folded_cascode_pm_deg, cmrr_estimate/psrr_estimate(diff_pair_tail) |
| nmcnr_amplifier | sum_current(objective), nmcnr_gain_db, nmcnr_pm_deg, cmrr_estimate/psrr_estimate(diff_pair_tail) |
