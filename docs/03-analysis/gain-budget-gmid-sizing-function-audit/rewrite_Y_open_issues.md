# 재작성용 -- §10.2~§10.5 미해결 항목 현재 상태 판정 (2026-09-14, HEAD 2555eec 기준)

판정 방법: 계획서 기록과 코드를 grep·읽기로 대조했다(코드는 실행하지 않음). 약어: SR=`skills/analog-gmid-design/assets/sizing_recipe.py`,
SD=`.../stick_diagram.py`, TJ=`.../library/current_reuse_telescopic_ota.topology.json`, P=계획서, H=이력 문서, A6=`agent6_plan_vs_code.md`,
RB=`review_B_design_7_5_7_9.md`, BR=`assets/tests/baseline/README.md`. 실행해야만 알 수 있는 수치(파일럿 통과 여부 등)는 "미확인"으로 적었다.

상태 집계(56행): **해소 17 / 폐기·대체 7 / 부분 해소 16 / 미해결 16 / 판단 불가 0**. 열린 이슈 32행, 닫힌 이슈 24행.

## (1) 열린 이슈 -- 미해결·부분 해소 (담당 Phase 순)

| ID | 한 줄 요지 | 기록된 상태 | **현재 상태** | 근거 | 담당 |
|---|---|---|---|---|---|
| A3 | 목적함수 `sum_current`가 직렬 스택 전류를 중복 계상(2.82배) | 부분 잔여(metric만 신설, objective 교체 안 함) | **부분 해소** -- `supply_current` metric은 있고 선언됨. objective는 여전히 `power_uA`(=`sum_current`) | SR:3016-3019, SR:4502; TJ:1990-1994(metric), TJ:2030-2032(`minimize: power_uA`); 커밋 cb7273c | Phase 4 · §13.3 #16 · D6 · G8(전력은 레일 전류) |
| A4 | 미러 ratio 쌍의 VDS 차이가 만드는 계통 전류비 오차 | 부분 잔여(상한 제약 없음) | **부분 해소** -- 기록과 달리 제약이 걸려 있음: `mirror_ratio_error_mV <= value_from_constraint: mismatch_sigma_mV`. 남은 것: 쌍 판정이 `names[0], names[1]`만 봐서 여러 소자 그룹에서 한 쌍만 검사. 파일럿 외 3개 회로 선언은 미확인 | TJ:2021-2026, TJ:2055-2060; SR:4578; 커밋 806c906 | Phase 4 · §12.6 #5 |
| B9 | vsb 오산출(PMOS kind 무시, 선언값과 경쟁) | ★수정 승인 대기 | **부분 해소** -- `reconcile_vsb_from_nodes()`가 헤드룸 뒤 vsb를 노드전압으로 다시 유도하고 `audit_vsb_consistency()` 게이트가 배선됨. 남은 것: 원인 코드 `other_entry.setdefault("vsb", ref_vds)`가 그대로 있어 헤드룸 중에는 틀린 vsb가 쓰이고, 그 vsb로 계산된 W/gds가 남는다(vsb/W 버전 혼재) | 정의 SR:3976, SR:4018 / 호출 SR:9207, SR:9441 / 원인 코드 잔존 SR:8134; 커밋 1285618 | Phase 4 · §12.6 #1 · Phase 6b(D1 노드전압 정본) · G7 |
| G5 | 폴딩 노드 역할 5종인데 서브롤은 4종 | 처리방향: 서브롤 확장 | **미해결** -- metric 키 `fold_leg_b`는 코드에 있음. 서브롤 열거 확장이나 역할 유도는 없음. §15는 열거를 늘리지 않고 유도하는 방향 | SR:3044-3054, SR:10154; RB:73; 이력의 역할 체계 변경 커밋 없음 | Phase 6a · G2 · J5 |
| G6 | stage 분할 규칙 부재, 5신호 분류기 전용 시 입력쌍이 cascode로 분류됨 | 처리방향 미결 | **부분 해소** -- 규칙은 설계로 확정(차동모드 뷰 + R2, 4회로 6개 선언과 소자 단위 100% 일치). 코드 구현은 0(`stage_index`/S1v 없음) | P:1396-1408(§15.3), P:1429(G2); `probe_stage_partition.result.md`; RB:74 | Phase 6a · G2 · J1~J9 · D5(ports) |
| A6 | ICMR·출력 swing·THD가 헤드룸 하한 목록에 없고 스키마 슬롯도 없음 | 슬롯 신설 여부 결정 필요 | **미해결** -- `output_swing`/`icmr` assets 전체 0건 | grep(assets 전체, 대소문자 무시) 0건; RB:58(D5 ports 선행) | Phase 6a(D5 ports) → 6b(G7 DC 해석), 공식 미배정 |
| A7 | 고정점 수렴 "20회 이내"에 논증 없음 → bisection 제안 | 구현 방식 결정 필요 | **부분 해소** -- diode 고정점은 bisection으로 구현(`solve_diode_connected_vds`). 일반 순환 블록의 수렴 판정·허용오차는 설계만 있음(C-c, D2) | A6:11; P:1018(D2); P:1434(G7) | Phase 6b · G7 · D2 |
| B7 | §7.5 프로토타입 이식 과대평가, 다중도달 불일치 미검사 | 없음(해소로 기록) | **부분 해소** -- 기록은 해소지만 핵심 검사가 없음: `propagate_node_voltages()`가 `conflicts`를 만들기만 하고 엔진 안에서 읽는 곳이 0 | SR:3954(반환만, `.conflicts` 읽는 곳 grep 0); A6:16; §12.6 #2 | Phase 4 · §12.6 #2 · Phase 6b(G7 봉인 게이트) |
| B8 | §7.5가 KCL을 검증하지 않음 | 없음(해소로 기록) | **부분 해소** -- `kcl_residual_uA` metric은 선언·계산됨. 상한 제약은 없고 `exclude_nets`로 저항 노드를 뺀 채임 | SR:4430; TJ:1995-2004; TJ:2033-2071(제약 목록에 없음) | Phase 6b · G7(봉인 게이트 KCL 잔차) |
| B13 | vds/gm_id/L 확정 출처 태그 규정 없음 | DoD 포함 여부 결정 필요 | **부분 해소** -- 태그는 일부 있음: `_vds_source`(SR:3566), `_gm_id_source`(SR:3873 diode, SR:9427 matching_pair), `_vsb_source`(SR:4013, 7858, 8010), `_L_source`. `_gm_id_source` 대입은 2곳뿐이라 다른 gm_id 결정 경로는 태그가 없음. DoD(§4.1)에도 없음 | 위 줄번호; P:328-354 | Phase 6b · §12.5.2 C-a(reader 기록) |
| B11 | C1~C10 방지 장치가 말뿐이었음 | 없음(해소로 기록) | **부분 해소** -- 강제 테스트 열로 표를 다시 쓰는 것은 끝남. 테스트 10개는 0개 구현(`def test_` 0) | P:297-308; A6:45; P:1162(T7) | §13.5 T7(Phase 6a~7c에 맞춰 진행) |
| B5 | DOF 진단이 VDS 미지수·KVL 방정식을 세지 않음(사고19를 못 막음) | DOF 축 추가 결정 필요 | **미해결** -- `diagnose_sizing_dof` 정의 0건 | grep 0; A6:23; P:1420(§15.4 §7.8 변형) | Phase 6c · G4 |
| B6 | DOF 진단이 부등식을 등식처럼 셈 | 등식만 대조 결정 필요 | **미해결** -- 위와 같이 함수 없음. 해소 방식은 §15.4에 설계만 있음 | grep 0; P:1420 | Phase 6c · G4 |
| B14 | 선언된 `value_amp`를 실제 전류로 써야 함 | ★엔진 미구현 | **부분 해소**(기록과 같음) -- 읽는 곳은 `_metric_kcl_residual`뿐. 사이징 경로(`seed_currents`)는 읽지 않음. 파일럿 Iref `value_amp=1.2e-06` 선언과 theta `r_biasgen`이 함께 남아 있음 | SR:4474-4485; `seed_currents` 대입 SR:5922/5939/5975(theta feed만); TJ:144, TJ:1563 | Phase 6c(G4 등식 수 계산) → 7b(G0 사람 선언 필드, §15.4) |
| B2 | CMRR/PSRR을 stage 국소로 못 봄 → T1/T2/T3 게이트 | 없음(해소로 기록) | **부분 해소** -- 분류 결정은 끝남. `check_global_gates()`·`make_stage_local_check()` 정의 0 | A6:21-22; P:1419(§15.4 §7.6 자동 분류) | Phase 7a · G8 |
| B21 | 선언된 gain 제약(`gain_stages_sum`, 6소자)이 미러 18소자를 못 봄(26.15dB 괴리) | ★결정 필요 | **미해결** -- 방향은 확정(판정은 전체회로 MNA, 할당은 부하 포함 블록). 코드 제약은 여전히 `gain_db`(`gain_stages_sum`) ≥ 54 | TJ:1883-1898, TJ:2034-2038; SR:3028-3037; P:1442-1446(§15.6) | Phase 7a · G8 · J6 · D6·D8 · R1 |
| A2 | `Area_i` 정의 없음, 최적화 면적과 레이아웃 면적이 다름, Cc 면적 누락 | 정의 결정 필요 | **미해결** -- `sum_area`는 여전히 `Σ W·L`만(수동소자 없음). 파일럿 제약에 area 없음 | SR:3022-3025; TJ:2033-2071; RB:33, RB:54 | Phase 7b · G6(면적 제약) -- 공식 미배정 |
| B3 | `resolve_stage_sizing()` 시그니처에 vds/vs 없음 | 시그니처 결정 | **미해결**(재명세 대상) -- 함수 정의 0. D1에서는 vds/vsb가 노드전압에서 파생되는 블록 입력으로 바뀜 | A6:13; RB:65 | Phase 7b · G6 |
| G1 | 단일단(`compensation: null`)이면 gm 출처가 사라짐 | null을 1급 케이스로 정의 필요 | **미해결** -- `folded_cascode`가 실제로 `compensation: null`. null일 때 gm 출처 규정은 계획(§15.5 G5 포함)에도 코드에도 없음 | `folded_cascode.topology.json:6`; P:1432 | Phase 7b · G5 |
| G2 | 3단 이상(NMCNR) 보상이 2단 하드코딩 | stage 수 종속으로 일반화 필요 | **부분 해소** -- 보상 레지스트리에는 3단 함수가 있음(`nmcnr_3stage_topology`, `ngcc_3stage_topology`). 스키마 초안의 `solves_for`/`stage_gm_ref` 2단 하드코딩은 이력 문서에 그대로 남음. `Rz=1/gm2`를 넣을 DOF 계수기는 미구현. nmcnr `passive_elements` 누락 | SR:1469-1476; H:411; P:1408; P:1460(J9) | Phase 7b · G5 · J9 |
| G4 | class-AB 정지전류가 KVL로 정해지는데 `ID_source`에 그 타입 없음 | `kvl_battery_loop`/`output_class` 신설 필요 | **부분 해소** -- 배터리 KVL 합 제약은 들어감(§10.7, `stack_kvl_vgs_limit`). `ID_source.type=kvl_battery_loop`·`output_class`·`driving_spec`은 0건 | SR:1835; H:2002-2031; grep `kvl_battery_loop`/`output_class` 0건(assets) | Phase 7b · G5/G6 · J3 |
| §10.5-C6 | `closed_loop_accuracy_db`·`stage_gm_ref`·`vdd_kvl`이 읽히지 않는 필드 | 잔여 | **미해결** -- 코드·JSON 0건. 이력 문서의 스키마 초안에만 있음. `sizing_spec.json`이 없어 소비 여부를 판정할 대상이 아직 없음 | grep assets 0건; H:294, H:411, H:417 | Phase 7b(`sizing_spec.json` 분리 시 재명세, §15.4) |
| §10.5-C7 | `slew_rate_v_per_us` vs `slew_rate_target` 명칭 불일치 | 잔여 | **미해결** -- 계획서 §3.1과 이력의 스키마가 여전히 다름. 코드 0건 | P:211; H:401, H:484; grep assets 0건 | Phase 7b |
| A9 | SPICE 교차검증 허용오차 미정 | 미리 정할 것 | **미해결** -- `cross_check_with_spice` 정의 0, 허용오차 기록 없음. §15.5 G9가 사전 계산하기로만 적음 | A6:17; P:1436 | Phase 7c · G9 |
| B12 | `for ... in set(...)` 결정론 규칙 없음 | P1에 규칙 + grep 테스트 추가 | **미해결** -- 규칙이 §3.2 P1에 없음, grep 테스트 없음. 잔존: SR:10302(1곳), SD:1580, 2638, 6665, 7790, 7826(5곳) | grep 결과; P:245-256 | Phase 7c · G9(순회 결정론) · §13.5 T7 C2(`test_order_shuffle_invariance`) |
| A5 | 온도·코너 메타데이터가 LUT에 없음 | 부분 잔여 | **부분 해소** -- 생성기가 `corner="tt"`, `temp_c=27.0`을 기록하고 읽는 함수도 있음. 그런데 **`lut_conditions_from_npz()`를 운영 경로에서 부르는 곳이 0**. 저장소 npz 재생성 여부는 미확인. 코너 스윕을 범위 밖이라고 §2.2에 적지 않음 | `sky130_lut_sweep.py:327-330`; SR:5355(def만, 호출 grep 0); A6:51; P:191-200 | 미배정(RB:57 제안: G0 S0 지문에 LUT 메타 해시) |
| G3 | gain-boosted cascode가 "VDS 예산이 유일한 자유도" 명제를 반증 | `boost_amp` 재귀 또는 범위 밖 선언 | **미해결** -- `boost_amp` 0건, §2.2 범위 밖 선언도 없음 | grep 0; P:191-200 | 미배정 |
| G7 | 비증폭 회로(밴드갭·비교기 등) 범위 밖 명시 없음 | §2.2에 절 신설 | **미해결** -- §2.2에 회로 부류 절 없음 | P:191-200 | 미배정(재작성 문서 작업) |
| G8 | 새 토폴로지 추가 비용(엔진 등록 3~4곳) 문서화 없음 | §8.3에 목록 명시 | **미해결** -- 이력 §8.3에도 목록 없음. §13.4가 §8.2를 대체했지만 이 목록은 없음 | H:1750-1776; P:1095-1119 | 미배정(§13.4 재작성) |
| §10.5-C3 | §2.2(파일럿 1개) vs §4.1 C7(4개 전수) 범위 충돌 | 잔여 | **부분 해소** -- §15.8 각 Phase DoD가 "4개 회로 측정"으로 사실상 정리했으나 §2.2 문구가 그대로 | P:193-194 vs P:352-354; P:1477 | 재작성 문서 작업 |
| §10.5-C5 | 신규 함수 목록을 3곳에서 관리(§2.1/§6.1/§7) | 잔여 | **부분 해소** -- 정본은 함수 레지스트리(§13.1)와 §13.2 규칙으로 정해짐. §6.1/§7은 이력으로 옮김. 그러나 §2.1 체크리스트가 계획서에 남아 낡음(예: `set_device_vds`가 `[ ]`인데 SR:3516에 구현됨) | P:120-180; P:1040, P:1067-1072; SR:3516 | 재작성 문서 작업 |
| §10.5-C9 | §7.10 측정 2 표의 빈 헤더 | 잔여 | **미해결** -- 첫 열 헤더가 여전히 비어 있음(`\| \| 0.15→0.35 \|...`) | P:499 | 재작성 문서 작업 |

## (2) 닫힌 이슈 -- 해소·폐기 (이력 문서로 옮길 대상)

| ID | 한 줄 요지 | 판정 | 근거 |
|---|---|---|---|
| A1 | KKT λ항 부호 오류 | 폐기(KKT 자체를 폐기하고 DP → §15.5 G6 3층 할당으로 대체) | RB:34, RB:53; P:1433 |
| A8 | 적층 diode 연립 solver 불필요(재해석) | 폐기·대체 → B25 `solve_stacked_diode_pair` | SR:3659, 호출 SR:7859; RB:60. 참고: `stack_headroom_slack_v`는 여전히 제약이 아니고 주석의 "7개 스택 음수"는 B25 이전 기록(현재값 미확인) TJ:2005-2009 |
| A10 | v3.3 근거 실측치가 물리적으로 불가능하다는 의혹 | 폐기(기각, 선형비/dB 오독) | P:708; 커밋 cbce11e |
| A11 | gm/gds가 gm_id에 단조가 아님 | 해소(문서: KKT·해석해 철회, DP로 교체). DP 코드는 미구현이며 G6 몫(Phase 7b) | P:710; RB:63; 커밋 cbce11e |
| A12 | metric 이름과 단위 불일치(µA 이름에 A 값) | 해소 -- 단위 레지스트리 + 로드 시 거부, 선언에 `unit` 강제 | SR:5813-5839, 배선 SR:8514, SR:5852-5854; TJ:1877/1881; 커밋 28e696d |
| B1 | diode 티어가 실제 버그 경로를 안 지남 → 단일 setter | 해소 -- `set_device_vds()`, 원시 대입은 SR:3565 한 곳. (원시 대입 grep 강제 테스트는 미구현 → §13.5 T7 C9) | SR:3516-3566; A6:27; 커밋 f2a897a, 5c23a8b |
| B4 | 실행시간 예산 항목 없음 | 해소 -- DoD에 wall-clock ≤ 5분(현재 평가 1회 72.9ms) | P:349-351; 커밋 199b5c9 |
| B10 | §7.10이 사고4 경계(`select_L_by_role` cascode/signal 거부)를 건드림 | 해소 -- `select_L_by_role`/`_L_ROLE_MULTIPLIERS`는 사용자 지시로 삭제, cascode/signal 가드는 `derive_role_L()`로 옮김 | SR:2777-2780, SR:13772; 커밋 dae3c5a |
| B15 | LUT L 보간이 PMOS gm/ID를 비물리 값으로 만듦 | 해소 -- 배열별 보간(①) + L 앵커 7→12(③). npz 내용은 실행 없이 확인 못 함 | 커밋 35908e8, a19e687 |
| B16 | 헤드룸 시점에 diode gm_id가 없음 | 해소 -- `apply_diode_self_consistent_gm_id()` 신설·배선 | SR:3743, 호출 SR:9236; 커밋 35908e8 |
| B17 | 매칭 쌍에 L만 전파되고 gm_id는 안 됨 | 해소 -- gm_id 전파(`_gm_id_source: matching_pair:*`) | SR:9427; 커밋 ae505c9 |
| B18 | 레이아웃 재검증이 전역 metric을 건너뜀 | 해소 -- 전부 재계산으로 전환 | SR:11900-11944; 커밋 d32811b |
| B19 | 미러 3그룹 VGS가 물리적으로 불가능하게 벌어짐(11소자) | 폐기·대체 → B19'(대상 18소자, 결론 번복) | P:734-735; 커밋 4ff315a |
| B19' | 18소자 미러 강제, 공유 VGS는 gain 기준 | 해소 -- `gm_id_match_vgs_of` 15선언 배선 | TJ:1027~1314(15곳); 커밋 a412f40 |
| B20 | `_solve_vgs()`가 비단조 PMOS LUT에서 branch를 넘나듦 | 해소 -- 가장 큰 VGS 해(rightmost root) + 범위 밖이면 명시적 실패 | SR:522-607; 커밋 57abfdd. 관련 잔여: 다른 역산 함수의 단조성 미검사는 §13.3 #10 |
| B20 보강 | "정점 오른쪽"이 아니라 "가장 큰 VGS 해"로 정식화 | 해소(①′ 채택, 기록의 "승인 필요"는 낡음) | SR:545-556, SR:581-592; 커밋 57abfdd |
| B22 | `diode_vds_window()`가 diode 자신의 W만 봄 | 해소 -- `mirror_members`로 VGS 공유 소자 전원을 봄 | SR:3570-3571, SR:3639; 호출 SR:8018; 커밋 d64175b |
| B23 | B19'·B22 전에 B9가 먼저 | 해소 -- 순서 이행(B9+B25 → B19' 배선 착지) | 커밋 1285618 → a412f40 |
| B24 | B9를 고치면 M11b(W=6342µm)가 성립 안 함, 회로 판단 필요 | 해소 -- B25 적층 diode 연립으로 풀림(기록의 "혼자 진행 안 함"은 낡음). L5c 픽스처 잔여는 `r_cmfb_vocdes`를 하한 0.02에 고정해 처리 | SR:9207, SR:9441; BR:60-81; 커밋 1285618, 0c00de9 |
| B25 | 적층 diode는 vsb로 결합(`vsb_lo = vsb_up + v_up`) | 해소 -- 연립 solver + 헤드룸 배선 + `L_role: bias_replica`. 잔여 결함(LUT 실패 시 `idu_up=1.0`)은 §13.3 #11로 따로 추적 | SR:3659-3712(#11은 SR:3707), 호출 SR:7859; 커밋 1cdb46b, 1285618 |
| §10.5-C1 | 유령 함수 3개(`allocate_headroom_budget` 등) | 폐기·대체 -- 계획서 본문에서 빠져 이력에만 있음(def 0). 기능은 §15.5 G4/G6로 대체 | H:260; grep assets 0건; A6:35 |
| §10.5-C2 | 삭제 선언한 `gain_allocation`/`gain_allocation_check` 잔존 | 해소(계획서 기준) -- 계획서 0건, 이력(H:1339, H:1772)에만 있음 | grep P 0건 |
| §10.5-C4 | §7.9 3-Phase 순서와 §8.4 harness 순서 불일치 | 폐기·대체 -- 두 절 모두 이력으로 옮김. §15.5 G0~G9 + §15.8이 대체 | P:1423-1436, P:1464-1477 |
| §10.5-C8 | `battery_centering_deviation` vs `classab_centering_dev_v` 명칭 흔들림 | 폐기 -- 흔들림이 아니라 metric 타입명과 인스턴스명 구분으로 일관되게 쓰임 | TJ:1978-1983 |

## (3) 새로 발견한 불일치 (재작성 시 반영)

1. **A6 감사가 `_gm_id_source` 규정이 없다고 적었는데**(A6:53) 코드에는 태그가 있다(SR:3274-3284 권위 출처 판정, SR:3873, SR:9427). 정확한 사실은 "대입처가 2곳뿐"이다.
2. **커밋 82dd5f5 제목은 "B14 해소"인데**, 계획서 B14는 "엔진 미구현"이고 코드도 사이징 경로에서 `value_amp`를 읽지 않는다(SR:4485만).
3. **A4 기록("상한 제약 안 걸었다")이 낡았다** -- 806c906에서 `mirror_ratio_error_mV` 제약이 걸렸다(TJ:2055-2060). 대신 §12.6 #5(SR:4578 `names[0], names[1]`) 때문에 이 제약이 그룹 대부분을 못 본다.
4. **B7·B8·B2·B11은 기록상 "없음(해소)"인데** 구현 요소가 비어 있다: conflicts를 읽는 곳 0(SR:3954), KCL 제약 없음, `check_global_gates` 없음, C 테스트 0.
5. **B9는 "해소"로 보이지만 원인 코드 SR:8134 `setdefault("vsb", ref_vds)`가 남아 있다** -- 나중에 reconcile이 덮어쓸 뿐이라 §12.6 #1(vsb/W 버전 혼재)의 발생원이다. 계획서 B9 행과 §12.6 #1이 서로를 참조하지 않는다.
6. **`lut_conditions_from_npz()`는 운영 경로에서 부르는 곳이 0**(def SR:5355만) -- A5 기록은 이 함수를 해법처럼 서술한다(★절대원칙: 만들고 배선 안 함).
7. **B25 행의 "잔여: L5c 픽스처"는 처리됐다**(BR:81, 하한 0.02 고정). 계획서 본문은 갱신되지 않았다.
8. TJ:2008 `stack_headroom_slack_v` 주석("7개 스택 음수, 제약으로 걸면 즉시 infeasible")은 B25 이전 실측이다. 지금 값은 실행해야 알 수 있고(미확인), 제약으로 걸지 않은 채 남아 있다 -- A8 폐기 뒤 담당이 없다.
9. §2.1 체크리스트(P:120-180)가 구현 여부와 맞지 않는다(`set_device_vds` `[ ]`인데 SR:3516에 구현).
10. §10.5 본문의 줄 참조 "L794/L1150"은 이력 분리(v4.47) 뒤 무효다.
11. §10.2 표 형식: A12가 A11보다 앞에 있고, A11 행은 셀 수가 헤더(4열)보다 적다(P:709-710).
12. B20 수정은 `_solve_vgs`에만 들어갔다. 같은 비단조 문제를 가진 이분 역산(`solve_id_for_target_gm`, `_invert_gm_id_for_current`)은 §13.3 #10으로 따로 열려 있는데, B20 행에는 그 연결이 없다.
