# sizing_recipe.py 함수 전수 감사 — 범위 5045 ~ 12570 (agent3)

- 대상: `skills/analog-gmid-design/assets/sizing_recipe.py` 모듈 최상위 함수/클래스 100개(inventory.json 기준) + `_evaluate` 블록 분해
- 계획서: `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` v4.43 (§7, §8.2/8.4, §10, §12)
- 운영 경로 정의: `workspaces/run_harness.py:440` → `optimize_full_circuit_budget` → `_build_theta_evaluator`/`_evaluate` (+ `run_harness.py:522` `diagnose_sizing_roles_gap`). run_harness SPECS: 파일럿만 `search_method="slsqp"`(`run_harness.py:325`), 나머지는 기본 `"grid"`(`:442`).
- 라이브러리 topology가 실제로 쓰는 metric/feed 타입(grep 실측): current_reuse = A/A_signed/B/C/metric_stage_budget/settling_split(`:1429`), metric smallsignal_ratio_db×2·smallsignal_gain_db·nulling_resistor_ohm 등; folded_cascode·nmcnr = cmrr_estimate/psrr_estimate(`circuit_family="diff_pair_tail"`만), const; two_stage = metric_stage_budget·smallsignal_gain_db. **`circuit_family="telescopic_class_ab*"`를 쓰는 topology는 0개.**
- 표기: ST = self-test 블록(12571~) 내 직접 참조 줄. "간접" = `optimize_full_circuit_budget` self-test(12653~, 24회 참조)를 통해서만 실행.
- 기록 방식: 그룹(≈10행) 단위로 append.

## 1. 함수별 판정표

| 함수(줄) | 책임 | 계획 대응 | 운영호출자 | 등급 | 이관 목적지 | self-test | 근거/비고 |
|---|---|---|---|---|---|---|---|
| `_load_telescopic_topology_cached`(5045) | current_reuse topology를 **하드코딩 경로**로 로드·캐시 | 계획 외(세션21) | 없음(체인 끝이 `_cmrr_telescopic_class_ab_cmfb`, 라이브러리 미사용) → self-test 전용 | D | 삭제 후보 | 간접 14994 | 경로 하드코딩 `:5054-5055`(일반화 원칙 위반). 기능은 `_load_full_topology_cached`(5379)와 DUP. `__dict__` 캐시 무효화 없음 `:5051` |
| `_telescopic_class_ab_open_loop_response`(5064) | 31소자 부분망 소신호 MNA로 (Vop1,Vom1) | 계획 외(세션21) | self-test 전용 | D | 삭제 후보 | 간접 14994 | `_full_circuit_response`(5543)가 전체회로로 일반화·대체(`:5588-5591` docstring 스스로 "대체"라 명시). DUP |
| `_hashable_key`(5104) | dict/list→정렬 tuple 정규화(캐시 키) | 계획 외 | 운영: `_nmcnr_predict`(3133, nmcnr_gain_db/pm_deg — nmcnr 라이브러리 사용) | R0 | gmid_sizing_engine(util) / circuit_state_graph S0 지문 재료 | 직접 없음 | 순수. 내용기반 키 생성기라 S0/S2 입력 해시에 그대로 재사용 가능(새로 만들면 중복) |
| `_telescopic_open_loop_device_names`(5115) | 31소자망 소자명 열거 | 계획 외 | self-test 전용 | D | 삭제 후보 | 간접 | 위 체인 전용 |
| `_telescopic_class_ab_open_loop_gains`(5130) | Adm/Acm/Ann/H 4여기 풀이 + ctx 캐시 | 계획 외(세션21/31) | self-test 전용 | D | 삭제 후보 | 14994, 15044-15045 | 캐시 키에 gm/gds 스냅샷 포함(`:5152-5153`, 내용기반 — 설계는 모범). 그러나 소비자 없음 |
| `_cmrr_telescopic_class_ab_cmfb`(5170) | telescopic CMFB CMRR(부분망+폐형식 G2/A_c) | §7.6 CMRR 결합(부분) | registry(`:5240`)만. 라이브러리 circuit_family에 없음 → self-test 전용 | D | 삭제 후보 | 14996 | 대체재 `_metric_smallsignal_ratio_db`(5586)가 current_reuse 정본. DUP |
| `_psrr_diff_pair_tail`(5244) | `gm_tail/gds_tail` 자리표시자 PSRR | §7.6(부분) | 운영: folded_cascode·nmcnr `psrr_estimate`(`circuit_family="diff_pair_tail"`) | R1 | gmid_sizing_engine | 없음 | docstring이 "order-of-magnitude 근사, 수천 배 차이 가능"(`:5245-5250`)이라 명시 → 제약으로 쓰이면 오판. `smallsignal_ratio_db`로 교체 검토 필요 |
| `_psrr_telescopic_class_ab`(5256) | telescopic 1단 open-loop PSRR 폐형식 | §7.6(부분) | registry(`:5350`)만, topology 0 / self-test 0 | D | 삭제 후보 | 없음 | `_cmrr_telescopic_class_ab`(4837)와 계산 복제를 docstring이 인정(`:5276-5278`). DUP |
| `_psrr_telescopic_class_ab_cmfb`(5312) | telescopic CMFB PSRR | §7.6(부분) | registry(`:5351`)만, topology 0 / self-test 0 | D | 삭제 후보 | 없음 | G2/A_c/T 블록 `:5334-5343` = `:5221-5233` 복제(DUP `_cmrr_telescopic_class_ab_cmfb`) |
| `lut_conditions_from_npz`(5355) | LUT npz의 corner/temp 기록 여부 반환 | §10.2 A5 | **호출자 0**(repo 전체 `*.py` grep 결과 정의 외 참조 없음) | D(배선 필요) | circuit_state_graph S0(LUT 생성메타 해시) | 없음 | §12.5.1 S0가 "LUT 내용+생성메타(corner/temp) 해시"를 요구 → 배선하면 R0. 지금은 만들고 안 쓴 상태(절대원칙 위반) |
| `_load_full_topology_cached`(5379) | topology 파싱+`load_topology` meta 보관, 경로별 캐시 | 계획 외(세션21), §11.4/§12 S1 후보 | 운영(28 호출자) | R1 | circuit_state_graph S1 | 13806, 13814 | 키가 **경로 문자열**, 파일 변경 무효화·상한 없음(`:5384-5385`) = §12.3-7/§12.5.2 C-d 위반. 키를 topology 내용해시로 교체 |
| `_topology_meta_cached`(5413) | 위 캐시의 meta 접근자 | 계획 외 | 운영(`_l_*_cached`) | R1 | circuit_state_graph S1 | 없음 | 동일 C-d 키 문제 |
| `_l_sharing_classes_cached`(5423) | L 동치류(층1) 경로별 캐시 | §10.9 층1 계획대로 | 운영(`_evaluate` 9456) | R1 | circuit_state_graph S1 | 간접 | 별도 `__dict__` 캐시, 경로 키(C-d). S1 "L 동치류 개념당 정의 하나"로 흡수 |
| `_l_class_owners_cached`(5435) | L 동치류 주인(층2) 캐시 | §10.9 층2 계획대로 | 운영(`_evaluate` 8967) | R1 | circuit_state_graph S1 | 간접 | 동일 |
| `_ideal_sources_cached`(5446) | ideal_sources 선언 접근자 | 계획 외(B8) | 운영(`_metric_kcl_residual`) | R1 | circuit_state_graph S1 | 없음 | 접근자 5종(5446/5452/5466/5472/5413) 동형 반복 → S1 단일 객체 속성으로 통합 |
| `_diode_set_cached`(5452) | gate==drain 소자 집합 | §7.3 B1 5단계 | 운영(`_hr_resolve_vertical_group` 7811, `set_device_vds` 등 10곳) | R1 | circuit_state_graph S1 | 없음 | §12.3-5 "diode 집합 16/1/20개 3정의" 중 connectivity 정의. S1 정본 후보로 승격 + C-d 키 교체 |
| `_device_roles_cached`(5466) | device_roles 접근자 | 계획 외(A8) | 운영 | R1 | circuit_state_graph S1 | 없음 | raw JSON의 device_roles(`:5407`) vs `_build_theta_evaluator`의 `meta["device_roles"]`(자동채움 포함 `:8524`) — **같은 이름 두 출처**(C-a) |
| `_matching_pairs_cached`(5472) | symmetry.matching_pairs 접근자(raw JSON) | 계획 외 | 운영(`_evaluate` 9455 등 12곳) | R1 | circuit_state_graph S1 | 13804 | `_evaluate`는 동시에 `meta["symmetry"]["matching_pairs"]`(`:8527`)를 따로 씀 → 두 출처(§12.3-5) |
| `_resolve_nulling_resistor_ohm`(5481) | Rz=1/gm(ref) 계산 + ctx 캐시 | §10.8(보상망) 부분 | 운영(current_reuse `nulling_resistor_ohm` metric, passive 저항 스탬프) | R1 | gmid_sizing_engine | 없음 | **스테일 캐시**: 키가 소자명뿐(`:5499-5504`). `revalidate_finger_override`가 `_dc_replace(ctx, sized=new_sized)`(`:11892`)로 새 ctx를 만들면 dataclasses.replace가 `_nulling_resistor_cache` dict를 **공유**(필드 `:3013`) → 옛 ctx로 먼저 계산(`:11923`)한 Rz가 새 ctx(gm 변경)에 재사용됨. C-b 위반. 키에 gm 값 포함 필요 |
| `_full_circuit_devices`(5508) | 전 MOSFET+저항을 MNA 스탬프 튜플로 변환 | 계획 외(세션21), §12.5.3 metric 블록 | 운영 | R0 | gmid_sizing_engine | 간접 | 순수 변환, 미사이징 소자는 KeyError(`:5527`). 캐시 없음(호출부 문제) |
| `_full_circuit_response`(5543) | 여기 1개로 전체회로 MNA 풀이 | 계획 외(세션21) | 운영(cmrr/psrr/gain_full) | R1 | gmid_sizing_engine + S2 memo | 15160 | 호출마다 스탬프 재조립+행렬 재분해(`:5563`,`:5574`). ratio metric 1개가 2회(`:5608`,`:5610`) → 같은 sized에 cmrr·psrr·gain_full로 동일 행렬 5회 분해. 행렬 1회 분해·RHS만 교체(S2 적재) |
| `_metric_smallsignal_ratio_db`(5586) | 두 여기의 응답비(dB) | §7.6 결합(일반형) | 운영(current_reuse cmrr/psrr) | R0 | gmid_sizing_engine | 직접 없음 | 순수. 성능은 5543에 위임 |
| `_metric_smallsignal_gain_db`(5615) | 전체회로 DM 이득(dB) | §7.9 gain metric 위임 | 운영(current_reuse, two_stage) | R0 | gmid_sizing_engine | 직접 없음 | 순수 |
| `_metric_cmrr_estimate`(5632) | circuit_family 2단 registry 조회 | §7.6 | 운영(folded, nmcnr) | R0 | gmid_sizing_engine | 없음 | 순수 디스패치. registry 3항목 중 살아있는 것은 `diff_pair_tail` 1개 |
| `_metric_psrr_estimate`(5644) | 동일(PSRR) | §7.6 | 운영(folded, nmcnr) | R0 | gmid_sizing_engine | 없음 | 위와 동일 |
| `unit_hint_from_metric_name`(5761) | 이름 접미사→단위 | §10(A12) | 운영(validate_metric_units) | R0 | topology_authoring | 직접 없음 | 순수 |
| `metric_unit_scale`(5770) | 선언 unit 환산계수(표에서만) | §10(A12) | 운영(compute_metric) | R0 | gmid_sizing_engine | 간접 | 순수, 표에 없으면 거부 |
| `validate_no_legacy_vs_key`(5790) | device_roles 옛 `vs` 키 거부 | §10.3 B9 | 운영(`_build_theta_evaluator` 8518) | R0 | topology_authoring | 간접 | 순수 게이트 |
| `validate_metric_units`(5813) | metric unit 선언 검증 | §10(A12) | 운영(8514) | R0 | topology_authoring | 간접 | 순수 게이트 |
| `compute_metric`(5842) | registry 계산기 호출×단위환산 | §7.9(metric 레지스트리) 계획대로 | 운영 핵심 | R0 | gmid_sizing_engine | 12684 외 31회 | 순수. 메모 없음 → 같은 metric을 `_refine...`(6468)·`_evaluate`(9468)·scorer(6370/6376)가 중복 계산(호출부 R2 사유) |
| `FeedHandler`(5882) | feed 핸들러+`touches` 레코드 | §7.3.2(registry) | 운영(registry) | R1 | gmid_sizing_engine | 없음 | **`touches` 필드는 어디서도 읽히지 않음**(grep `.touches` 0건) → 삭제하거나 §12.5.4 "구조적 쓰기 집합"으로 실제 사용 |
| `_feed_root_ratio`(5887) | A: theta×Σref ID를 root seed | §7.3.2 | 운영(4개 회로 전부) | R1 | gmid_sizing_engine | 13902 | `ctx.seed_currents` 원시 대입(`:5922`, C-a). 중첩 `_ref_id`가 `_feed_root_signed_sum`(`:5967-5971`)과 DUP |
| `_feed_root_const`(5925) | const: 절대전류 seed | §7.3.2(세션35) | 운영(folded, nmcnr) | R1 | gmid_sizing_engine | 없음 | C-a 원시 대입만 |
| `_feed_root_signed_sum`(5942) | A_signed: 부호합 seed | §7.3.2(세션6) | 운영(current_reuse 4, folded 2, nmcnr 5) | R1 | gmid_sizing_engine | 없음 | C-a, `_ref_id` DUP(5914). 음수 전류 검사는 하류(9247) |
| `_feed_diode_stack_target`(5978) | C: reference 복제×면적비 | §7.3.2 | 운영(current_reuse 2) | R1 | gmid_sizing_engine | 13909 | `ctx.sized[target] = entry` **통째 교체**(`:6036`)로 기존 필드(A엔진 ID 등) 소실 가능. ref의 gm_id/L을 그 시점 버전으로 복사(C-b) — 순서 검사기(6858)는 운영 미배선 |
| `_feed_gm_target_convention`(6039) | B: N·ωc·C → gm 역산 사이징 | §7.3.2, §10.8 E | 운영(current_reuse N_cmfb_bw) | R1 | gmid_sizing_engine | 13915 | `vsb=feed.get("vsb",0.0)`(`:6066`) 기준 W·gds → reconcile(9207) 후 vsb만 바뀌고 W/gds 미갱신(§12.6-1 계열). `gm_id_bounds` 리터럴 `(2.0,30.0)`(`:6083`) |
| `_feed_settling_split`(6099) | t_slew/t_lln 분배를 ctx.derived에 | §7.3.1 Level1 | 운영(current_reuse f_slew, topology `:1429`) | R1 | gmid_sizing_engine | 13926 | C-a 원시 대입, 기본 키명 리터럴(`:6116`) |
| `_metric_stage_budget_finalize`(6128) | (gm_id,ID,L,vds,vsb)→W/gm/gds 확정 기록 | §7.3.2 | 운영(feed 6786, scorer 6363) | R1 | gmid_sizing_engine | 간접 | **§12.6-1 원천 중 하나**: feed 기본 vsb 0.0 기준으로 W·gds 기록(`:6160-6162`), 입력 버전 미기록 → C-b 버전 필드 추가 |
| `_shared_current_groups_from_compensation`(6167) | shared_gm_id_groups → 소자명 frozenset | 계획 외(세션31) | 운영(8668), validate(6904) | R0 | circuit_state_graph S1 | 간접 | 순수, 3곳 공유 단일 정의 |
| `_evenly_subsample`(6181) | 이산 격자 균등 서브샘플 | 계획 외 | 운영(6287) | R0 | gmid_sizing_engine(util) | 없음 | 순수 |
| `_build_shared_current_joint_plan`(6198) | 공유전류 그룹 조인트 스캔 계획(정적) | 계획 외(세션31) | 운영(8669, 빌드 시 1회) | R0 | circuit_state_graph S1 / 유도 DAG | 간접 | 순수(thetas 선언만) |
| `_shared_current_root_grids`(6256) | 조인트 스캔 격자 생성 | 계획 외 | 운영(6411, 6476) | R1 | gmid_sizing_engine | 없음 | 격자 `[i*0.5 for i in range(4,61)]`(`:6283`)·상한 5000(`:6285`) 리터럴 — `:6632` 리터럴과 DUP. docstring은 `search_gm_id_for_role` 기본 격자 "재사용"이라 하나 실제로는 복사 |
| `_make_shared_current_scorer`(6291) | 후보 gm_id 조합 채점 클로저(ctx.sized 부수효과) | 계획 외 | 운영(6412, 6477) | R1 | gmid_sizing_engine(블록) | 간접 | `_metric_device_footprint` 제약마다 2회(`:6323-6324`), `except KeyError: continue`(`:6371`, "도달 안 함" 주석 = 근거 없는 skip), 후보마다 ctx 덮어씀(`:6363`) → 순수 점수화로 분리해야 S2 memo 가능 |
| `_run_shared_current_joint_scan`(6381) | 공유전류 그룹 K-D 전수 스캔 + 승자 재적용 | 계획 외(세션31) → §12.5.3 명시 대상 | 운영(`_feed_metric_stage_budget` 6794) | R2 | gmid_sizing_engine 블록 + circuit_state_graph S2 | 간접 | **warm 평가의 66%**(§12.3-6). 입력 동일해도 매 평가 최대 57²=3249조합×finalize×compute_metric 재실행. §12.5.3 키(그룹 L·vds·vsb·gm_total·고정 gm_id)로 S2 적재 |
| `_refine_shared_current_joint_scan_for_full_circuit_constraints`(6430) | 전역(ALL) 제약 위반 시 로컬 상위 top_n 재검사 | 계획 외(세션44) | 운영(`_evaluate` 9435) | R2 | gmid_sizing_engine 블록 + S2 | 간접 | `_all_global_satisfied`(`:6468`) 후 `_evaluate`가 전 metric 재계산(`:9468`) = **이중계산**(§12.4). 위반 시 1단계와 동일 전수 스캔 재실행(`:6479-6483` ≡ `:6415-6421`, DUP). top_n=20 리터럴 |
| `_feed_metric_stage_budget`(6496) | theta=L로 소자 L/gm_id/W 확정 + 조인트 스캔 트리거 | §7.3.2 부분(gain_db만 `:6574`) | 운영(current_reuse 3, two_stage 2) | R2 | gmid_sizing_engine(블록 분할) | 간접 | vds defer(`:6769-6785`) = "헤드룸이 나중에 채움" **실행순서 암묵계약**(§12.2, C-c/T2). joint-scan footprint를 feed 호출마다 재계산(`:6760-6767`). 순서 오류를 `ValueError`(`:6609`,`:6671`) → SLSQP 크래시 경로. 격자 리터럴 `:6632` DUP |
| `_feed_l_class`(6798) | l_class theta: 동치류 공통 L 기록 | §10.10 층3 계획대로 | 운영(파생 theta, 파일럿) | R1 | gmid_sizing_engine | 없음 | `_L_source` 출처 태그는 C-a 모범. setter 경유만 필요 |
| `apply_theta_feed`(6846) | feed 타입→핸들러 디스패치 | §7.3.2 계획대로 | 운영 | R0 | gmid_sizing_engine | 13904 외 | 순수 디스패치 |
| `validate_theta_declaration_order`(6858) | theta 선언순서=실행순서 계약 검사 | 계획 외(세션31) | **self-test 전용**, `_build_theta_evaluator` 미배선 | D(배선 필요) | topology_authoring | 15214~15266(6회) | 순서 오류 실사고 2회 기록(`:6864-6869`)인데 운영 게이트 없음. `l_class`/`vds_match_vgs_of` 의존 미검사. C-c 유도 DAG 도입 시 흡수 |
| `_constraint_tol`(6962) | 제약 판정 상대공차 1e-9 | §10.8 F 계획대로 | 운영(`_CONSTRAINT_OPS` 6973) | R0 | gmid_sizing_engine | 간접 | 순수 |
| `_lerp`(6980) | 선형보간 | 계획 외 | 운영(grid 분기 9753) | R0 | optimizer | 14020 | 순수 |
| `InfeasibleSizingError`(6984) | 물리 불가 격자점 예외 + sized_snapshot | §7.6/§12.5.2 C-c | 운영(25 호출자) | R1 | gmid_sizing_engine | 간접 | 메시지 문자열 + 스냅샷뿐 → 소비자가 **문자열 파싱**(`:11027`, `:9585`). §12.5.4 "구조화된 실패(분류·막은 소자·margin)" 필드 추가 필요 |
| `_HeadroomDependencyNotReady`(7011) | 헤드룸 worklist "나중에 재시도" 신호 | §7.3 | 운영(worklist 9188) | R2 | circuit_state_graph(C-c 고정점) | 간접 | 순환을 "진전 카운트"로 푸는 실행순서 우회(§12.3-8). C-c SCC 블록 반복으로 대체 |
| `resolve_stack_layout`(7025) | 레이아웃 1차 그룹 분할(override>declared vsid>candidates>legacy) | §8.4-4 **계획과 다름**(계획은 `stick_diagram.resolve_stack_layout`, 실제는 sizing_recipe) | 운영(8609) | R1 | sizing_layout_convergence(또는 stick_diagram) | 13135 외 5 | `load_topology()`가 내부에서 이미 `resolve_stack_layout`류 분석을 돈다고 기록(`:5393-5394`) → 빌드당 중복 실행. meta 결과 재사용 |
| `_metric_stage_budget_vds_by_device`(7137) | metric_stage_budget 고정 vds 사전 스캔 | §7.3 B1(tier) | 운영(comp 캐시 miss 8762) | R0 | gmid_sizing_engine | 간접 | 순수, `_feed_vds_fallback` 단일 폴백 공유 |
| `reserved_vds_for_other_stack_members`(7163) | vsid 컬럼의 타 멤버 예약 vds 합(재귀 확장) | 계획 외(세션30/43) | 운영(8776) | R0 | gmid_sizing_engine | 13271, 13317, 13351 | 순수, 모르면 None(보수). 결정론 정렬(`:7232`) |
| `make_replica_feasibility_check`(7253) | C replica target의 W 실현성 콜백 | 계획 외(세션30) | 운영(8817) | R1 | gmid_sizing_engine | 간접 | `search_gm_id_for_role(..., 0.0, ...)` vsb 0 고정(`:7293`) — 헤드룸 이후 vsb와 다른 버전으로 판정. 버전 인자화 |
| `make_matching_feasibility_check`(7300) | pelgrom/입력환산 오프셋 제약 콜백 | §10.14(2) 계획대로 | 운영(8818) | R0 | gmid_sizing_engine | 간접 | 충분조건 증명 docstring(`:7318-7328`), 순수. vsb 0은 compensation 자체 가정(`:8844`)과 일치 |
| `_HeadroomTopoEnv`(7396) | 헤드룸 토폴로지 레벨 상태 묶음 | §8.4-2 계획대로(추출) | 운영 | R1 | circuit_state_graph S1 | 간접 | S1 객체로 흡수(vparent union-find = "매칭 offset 그룹" 정의) |
| `_HeadroomEvalEnv`(7407) | 헤드룸 평가 레벨 상태 묶음 | §8.4-2 계획대로 | 운영 | R1 | circuit_state_graph S2 | 간접 | 평가마다 새로 조립되는 정적 구조(vertical_groups 등)가 담김 → 정적 부분은 S1로 이동 |
| `_hr_vfind`(7420) | offset 매칭 union-find find(경로압축) | §8.4-2 | 운영 | R0 | circuit_state_graph S1 | 간접 | 순수. 동형 union-find가 `search_stage_budget_L_warm_start._lc_find`(`:10828`)에 재구현(DUP) |
| `_hr_thin_singleton_ideal_source_check`(7428) | thin singleton 우회를 ideal_sources로 정당화 | §8.4-2 | 운영(8083) | R0 | circuit_state_graph S1(유도 사실+증거 net) | 간접 | 순수 구조 검증 — S1 `status/증거` 모델에 그대로 맞음 |
| `_hr_fold_group_check`(7461) | fold_group 우회를 connectivity로 정당화 | §8.4-2 | 운영(8104) | R1 | circuit_state_graph S1 | 간접 | 중첩 래퍼 `_thin_singleton_ideal_source_check`(`:7478`) 정의만 있고 미사용(추출 잔재) → 삭제 |
| `_hr_sum_ref_vds`(7515) | budget_reference_device vds 합 | §8.4-2 | 운영(7782, 7604) | R0 | gmid_sizing_engine | 간접 | 순수(C-c 신호만 사용) |
| `_hr_verify_group_kvl_sum`(7532) | vsid 그룹 KVL 합=vdd 게이트 | §8.4-2, §7.5 | 운영(7753/7775/8143) | R0 | gmid_sizing_engine(봉인 게이트 재료) | 간접 | 순수 게이트, 소자별 breakdown. fold_group/same_as 제외는 문서화된 계약 |
| `_hr_resolve_vertical_group`(7644) | vsid 그룹 1개 헤드룸 해석(pre-pass/sibling/same_as/적층 diode 연립/diode 창/singleton 우회/allocate/vsb 전파) | §7.3 + §8.4-2(추출) 부분 | 운영(worklist 9186) | R2 | circuit_state_graph C-c 순환 블록 | 간접 | 500줄. **광범위 except 2곳** `:7852`,`:8006`(§12.6-6과 동종, 목록 누락) → 노드전압 실패 시 폴백으로 조용히 진행. 쌍/미러멤버마다 `propagate_node_voltages` 재호출(`:7849`,`:8004`, §12.3-4 평가당 19회의 원천). vsb `setdefault(ref_vds)`(`:8134`, vsb 기록 9경로 중 하나). 미사용 중첩 래퍼 `_resolve_vertical_group`(`:7669`). §12.5.2 C-c 대상 순환(vds↔노드전압↔vsb↔diode창↔gm_id/W) 그 자체 |
| `spec_fingerprint`(8151) | 해상도 키 7개 문자열 지문 | §10.6/§12.3-7 | 운영(require_declared_spec_source 8232, resolve_constraint_references 8423, achievable_metric_bound 8310) | R2 | circuit_state_graph S0 | 직접 없음(간접 14395) | LUT·vdd·제약값·topology·엔진 제외(`:8146-8148`), repr 기반 → §12.5.1 S0(전 입력 내용해시+유도규칙 코드 해시)로 대체 |
| `require_declared_spec_source`(8172) | library 회로 spec 출처 선언 강제 게이트 | §10.6 계획대로 | 운영(8492) | R0 | gmid_sizing_engine 진입 게이트 | 14395, 14405, 14410 | 광범위 except 제거 이력(`:8205-8208`), 거부 확인됨 |
| `derived_bounds_path`(8249) | `<topology>.derived.json` 경로 | §10.14 | probe 전용(`tests/derive_achievable_bounds.py:112`, load_derived_bounds) | R0 | optimizer(S3 저장 경로) | 13296 | 순수. 단 엔진은 사이드카를 안 읽고 topology.json `_derived`를 씀(아래 D 사유) |
| `load_derived_bounds`(8261) | 사이드카 JSON 읽기 | §10.14 | **probe 전용**(`tests/derive_achievable_bounds.py:69`), 엔진 0 | D | optimizer S3(흡수) 또는 삭제 | 없음 | 유도값 저장 경로가 사이드카 vs topology.json `_derived`(`resolve_constraint_references` `:8423`) 두 갈래 — 엔진은 후자만 읽음 |
| `achievable_metric_bound`(8271) | 제약 하나를 목적함수로 바꿔 달성가능값 실측(multi-seed SLSQP) | §10.14(3)(4), §10.15 재사용 명시 | probe/tool 전용(`tests/derive_achievable_bounds.py`) | R1 | optimizer(S3 유도 임계값) | 없음 | `_ACHIEVABLE_BOUND_CACHE` 전역·무상한, 키가 약한 `spec_fingerprint`(`:8310`) → C-d. `except Exception`(`:8350`)은 notes 기록이라 조용하지 않음 |
| `resolve_constraint_references`(8370) | value_from_spec/constraint/achievable 참조 치환 | §10.13/§10.14 계획대로 | 운영(8521) | R1 | topology_authoring(선언 해석) | 13823, 13840 | 지문 불일치를 `_RESOLVE_STALE_NOTES`에 기록만 하고 값 계속 사용(`:8424-8432`) = **§12.6-8**. C-d(불일치=없음)는 픽스처/정본 구분 결정 필요 |
| `_build_theta_evaluator`(8479) | theta-무관 셋업 + `_evaluate` 클로저 반환 | §8.4-1/2(엔진 핵심), §12.5.3 분할 대상 | 운영(optimize_full_circuit_budget 9693, warm-start 4곳, diagnose 9576) | R2 | gmid_sizing_engine + circuit_state_graph S1 + 블록 DAG | 14089 외 7 | 셋업: **광범위 except `(KeyError, ValueError): pass`**(`:8511`, §12.6-6 — l_class theta 조용히 0개), `load_topology` 이중(`:8493` + `_load_full_topology_cached` 내부 `:5386`, §12.4), `_comp_cache` 무상한(`:8540`), 미사용 중첩 래퍼 4개(`:8646`,`:8649`,`:9144`,`:9147` — 정의만, 호출 0). `_evaluate` 분해는 §2 |
| `_base_stack_id`(9500) | row 접미사 제거 | 계획 외(세션32) | 운영 코드상 도달 가능하나 `floorplan_target` 쓰는 SPECS/self-test 없음 | R0 | sizing_layout_convergence | 없음 | 순수 정규식 |
| `_pick_split_target`(9507) | 지배적 splittable row 선택 | 계획 외(세션32) | 위와 동일(실행 0) | R1 | sizing_layout_convergence | 없음 | 순수이나 **테스트·운영 실행 0회** — self-test 추가 필요(없으면 D) |
| `_score_floorplan`(9528) | floorplan 목표 미달 스칼라 | 계획 외(세션32) | 위와 동일(실행 0) | R1 | sizing_layout_convergence | 없음 | 동일 |
| `diagnose_sizing_roles_gap`(9541) | theta 없는 회로 1회 평가 → gap 리포트 | 계획 외(세션35) | 운영(`run_harness.py:522` 실패 진단) | R1 | topology_authoring | 14317 외 8 | 예외 **메시지 부분문자열**로 분류(`:9585`,`:9604`) → 메시지 문구 변경 시 조용히 "other". 구조화 예외로 |
| `optimize_full_circuit_budget`(9624) | 단일 진입점: θ 탐색(grid/slsqp/block) + finger/euler/matching/row_split 레이아웃 | §8.2/§8.4(분할 대상), Executive Summary | 운영 최상위(`run_harness.py:440`) | R2 | sizing_layout_convergence(레이아웃·row_split) + optimizer(탐색 디스패치) | 12653 외 24 | θ*를 반환만, 저장 없음(§12.3-1). grid 분기 위반 포맷/실현성 판정이 SLSQP·warm-start와 4중 DUP(`:9773`,`:9785`, `:10906`, `:11570`, `:11619`). 에러문 "'grid' 또는 'slsqp'만 지원"(`:9797`)이 block 분기 존재와 불일치. 레이아웃 후 metric 재계산(`:9854`,`:9940`)도 S2 미사용 |
| `_metric_device_footprint`(10121) | metric 선언→읽는 소자 집합(or "ALL") | §10.14(2), §12.5.4 | 운영(scorer, feed, refine, dep-graph, L warm start) | R1 | circuit_state_graph S1 | 간접 | 순수이나 **결과 캐시 없음**(선언만 의존인데 scorer에서 후보 루프 밖 제약당 2회, feed 호출마다 재계산). "소자 참조" 정의가 `_collect_device_refs`(11826)와 둘(§12.3-5) |
| `_theta_feed_footprint`(10174) | feed 선언→roots/derived_writes/reads | 계획 외(세션29) | 운영(dep-graph 10316) | R0 | circuit_state_graph S1(쓰기 집합) | 없음 | 순수, 타입별 명시. §12.5.4 "구조적 쓰기 집합"의 정본 후보(제네릭 `_theta_device_map` 10933과 DUP 관계) |
| `derive_theta_dependency_graph`(10213) | theta를 dead/isolated/coupled/fixed/ambiguous로 분류(FD 5%) | 계획 외(세션29), §12.3-10 비판 대상 | 운영(presolve 11277) | R2 | optimizer | 없음(간접 13233) | **한 기준점 5% 섭동 분류로 차원 동결**(§12.3-10, §12.5.4 금지). 임계 `0.5dB`/`1%` 리터럴(`:10390-10392`). theta마다 같은 baseline을 `evaluate` 재호출(`:10355`, 루프 안 불변식) |
| `extract_linear_feasibility_constraints`(10419) | A_signed KCL 부호제약을 선형부등식으로 역산 | 계획 외(세션29) | 운영(presolve 11212) | R0 | optimizer | 없음 | reference 한 점에서 얼린 근사임을 status/reason으로 명시. `except ValueError`는 결과에 기록(`:10546`) |
| `_group_score_metric`(10581) | 조인트 스캔 점수 = metric 최소 | §10.12 | 운영(10816) | R0 | optimizer | 13848, 13873 | 순수 |
| `_group_score_interior`(10595) | 점수 = 최소 정규화 제약 여유 최대 | §10.12 되돌림1 | 운영(10855) | R0 | optimizer | 13858, 13868 | 순수, 분모=선언값(0이면 1.0) |
| `search_stage_budget_L_warm_start`(10637) | L theta 웜스타트(LUT 고속경로 + evaluate 조인트 스캔) | §10.10/§10.12, §11.5 | 운영(presolve 11249) | R2 | optimizer | 13233 | 매 후보 full `evaluate`(`:10903`), 실패 미캐시(`except: continue`), 위반합 공식 DUP. `window_around_reference`(`:10890-10896`)는 §12.4가 기각한 "지난 해±창" — 호출자는 block_coordinate(미사용)뿐. 중첩 `_lc_find` union-find DUP(`_hr_vfind`). LUT 고속경로의 gm_id/vds는 기본값 추정(`:10770-10771`) |
| `_theta_device_map`(10933) | feed dict 전체를 훑어 문자열 leaf 수집 | 계획 외(v4.35) | 운영(repair 11012) | DUP | (정본 `_theta_feed_footprint` 10174 / walker `_collect_device_refs` 11826) | 없음 | 소자명 아닌 문자열(type, metric 이름)도 수집 후 교집합으로 거름. 두 함수와 개념 중복 |
| `repair_infeasible_baseline`(10959) | 실패 메시지의 소자명을 따라 theta를 bounds/격자로 이동 | §10.7 B, §10.10 | 운영(presolve 11245, 11311) | R1 | optimizer | 없음(간접) | **`d in msg` 부분문자열 매칭**(`:11027`, §12.6-4: "M1"⊂"M11a"). `except Exception: return False, frozenset()`(`:11028`) 광범위·조용. L 후보 서브샘플 9 리터럴(`:11059`). 구조화 실패(InfeasibleSizingError 필드)로 교체 |
| `presolve_warm_start`(11130) | 투표+복구+L 스캔+의존그래프로 x0 조립 | 계획 외(세션29), §12.3-10 비판 대상 | 운영(_optimize_theta_slsqp 11439) | R2 | optimizer | 13233 | 결정론 x0 하나(§12.3-10), 사전평가·아카이브 없음. x0를 `evaluate` 최대 3회(`:11303`,`:11315` + slsqp `:11562`) 중복 평가 |
| `_optimize_theta_slsqp`(11342) | SLSQP multi-start(정규화, 페널티, 재검증) | 계획 외(세션29), §12.3-1/2 비판 대상 | 운영(파일럿 `search_method="slsqp"`) | R2 | optimizer | 13852 | **`_eval_cache`에 성공만 저장**(`:11497-11503`) → 예외 점 매번 재평가(§12.3-2: 811회 중 784 중복). 상수 페널티 1e6(`:11491`)로 경사 0. 호출 수명 캐시(§12.3-1), θ* 미기록. 빠른 수정(R1급): 실패도 캐시 |
| `_optimize_theta_slsqp_block_coordinate`(11640) | L 격자 ↔ SLSQP 블록 좌표 교대 | 계획 외(세션40) | **호출자 없음**: 디스패치 `:9707`만 존재, run_harness SPECS·self-test 0(grep) | D | 삭제 후보(또는 optimizer로 이관 후 실측) | 없음 | `window_around_reference` 경로의 유일한 사용자 → 함께 정리 |
| `_collect_device_refs`(11826) | 중첩 spec에서 알려진 소자명 수집 | §10.3 | 운영(revalidate 11944, 진단 키만) + probe(`tests/probe_revalidation_scope.py`) | DUP | (`_theta_device_map` 10933) | 없음 | 판정 로직에선 더 이상 안 씀(`:11894-11921` 사유) — 진단 필드 전용 |
| `revalidate_finger_override`(11848) | finger W 강제 후 gm_id 역산 + 전 metric 재검증 | §10.3(면적 제약 사고) | 운영(pair/matching growth) | R1 | sizing_layout_convergence | 12743 외 6 | 매 호출 old metric 전부 재계산(`:11923`, 입력 불변 → S2 재사용). `_dc_replace` 얕은 복사로 ctx 캐시 3종 공유(`:11892`) → `_nulling_resistor_cache` 스테일(5481 행 참고) |
| `apply_and_revalidate_pair_adjustment`(11948) | L3 후보를 L4로 순차 승인 | §8.4-5 | 운영(euler fixup) | R0 | sizing_layout_convergence | 12810 외 4 | 순수 오케스트레이션, ValueError는 rejected에 기록 |
| `_blocked_euler_rows`(12021) | audit 체크명 `"1. euler["` 접두사 파싱 | §8.4-4 | 운영 | R1 | sizing_layout_convergence | 12958, 12982, 13110 | 문자열 계약(`:12031`) → 체크 객체에 구조화 필드 |
| `_sync_finger_fixup`(12036) | overrides·ctx.sized 동기화 | §10.3 | 운영(12530) | R0 | sizing_layout_convergence | 없음(간접) | 순수. 동일 동기화 루프가 인라인 3곳에 재구현(`:9934-9938`,`:12230-12234`,`:12420-12424`) |
| `suggest_matching_finger_growth`(12066) | 3c용 min_fingers 성장 delta | 계획 외(세션16) | 운영 | R0 | sizing_layout_convergence | 13448 외 5 | 순수 |
| `apply_and_revalidate_matching_finger_growth`(12087) | 성장 후보 1개 L4 재검증 | 계획 외(세션16) | 운영 | R0 | sizing_layout_convergence | 13448, 13489, 13499 | 순수 |
| `_fixup_euler_blocked_rows`(12131) | repair 후 잔여 euler-blocked row 수리(성장→분할/컴포넌트 분리) | 계획 외(세션31) | 운영(`_finalize` 12337) | DUP | (`run_topology_pipeline_with_finger_fixup` 12436) | 없음(간접) | docstring 스스로 "정확히 같은 전략"(`:12143-12146`). rows 표현용·topology_path용 두 벌 |
| `run_matching_safety_with_finger_growth`(12261) | 3c 실패에 핑거성장/완화 루프 | §8.4-5(세션18) | 운영(`_evaluate_row_split` 9918) | R1 | sizing_layout_convergence | 13119 외 9 | 체크명 정규식 파싱(`:12365`), 루프 안 `import re`(`:12360`) |
| `run_topology_pipeline_with_finger_fixup`(12436) | euler-blocked row 핑거조정/그룹분할 루프 | §8.4-5 "이미 증명한 패턴" 계획대로 | 운영(9843) | R1 | sizing_layout_convergence | 12901 외 5 | `load_topology` 재호출(`:12502`) + 라운드마다 `run_topology_pipeline`이 경로로 재로드(`:12510`) → S1 재사용 |

## 2. `_build_theta_evaluator._evaluate`(8673-9469) 블록 분해 (§12.5.3)

| 블록(줄) | 입력 | 출력(쓰기) | 부작용·결함 | §12 목적지 |
|---|---|---|---|---|
| B0 ctx 생성(8678-8681) | spec, device_roles, `known_sizing`, auto_mirror_ratios | 새 `SizingContext` | **매 평가 새 ctx**(§12.3-1). known_sizing 얕은 dict 복사 | S2 스냅샷 컨테이너 |
| B1 settling_split 선적용(8689-8695) | theta_values(f_slew) | `ctx.derived[t_slew/t_lln]` | 타입으로 골라 먼저 실행 = 순서 계약(Level1→2) | 유도 DAG 노드(보상 이전) |
| B2 보상(8707-8878) | comp_params(spec+derived), luts, VDS cap(`reserved_vds_for_other_stack_members`), extra_feasible 콜백 | stage 소자 gm/gm_id/L/W/ID/gds, **vsb=0.0**(`:8844`), `set_device_vds`; derived: exposed_params, `_shared_current_group`, `_metrics_specs`, `_constraints`, `_scb_joint_plan_by_devices` | `_comp_cache` 키=comp_params 튜플, 무상한(`:8540`,`:8742`). vsb 0 고정이 §12.6-1 W/gds 버전 혼재의 출발점. cap/extra_feasible은 miss 때만 계산(양호) | 보상 블록(S2 memo 이미 반쯤 존재) |
| B3 A엔진 1차(8888-8891) | ctx.sized ID, transistors_stackid, mirror_ratios | `setdefault("ID")` | setdefault → 재사용 모드에서 C-b "setdefault 건너뛰기 금지" 위반 소지 | 전류 블록 |
| B4 theta feed 루프(8893-8895) | theta_values, 선언 순서 | feed별 seed/sized/derived. `metric_stage_budget` 내부에서 **조인트 스캔(66%)** | 선언순서=실행순서(검사기 6858 운영 미배선). feed ValueError가 SLSQP 크래시 경로 | 전류/L 블록 + 조인트 스캔 S2 memo |
| B5 A엔진 2차(8903-8908) | sized ID + seed_currents | `setdefault("ID")` | B3과 동일 | 전류 블록 |
| B6 L_role 유도(8928-8951) | device_roles L_role, `_AUTHORITATIVE_L_SOURCES`(평가마다 set 리터럴 재생성 `:8928`) | L, `_L_source="L_role_derived"` | 근거 없으면 ValueError | L 유도 블록 |
| B7 L 동치류 층2(8967-9019) | `_l_class_owners_cached`, derive_class_L, knee_L_for_kind | L, `_L_source` | **`except (KeyError, ValueError): pass`**(`:9006`, §12.6-6) → 주인 knee 실패 시 조용히 기존 L 유지 | L 유도 블록 |
| B8 matching L 전파(9033-9059) | pairs_meta, `_L_source` | L | 순서 의존 전파(C-a), 불일치 ValueError | L 유도 블록(S1 L 동치류 단일 정의로 흡수) |
| B9 헤드룸 구조 구성(9061-9121) | device_roles | vertical_groups, group_ref_device, same_as_of, vds_match_of, referenced_devices | **θ 무관 정적 구조를 매 평가 재구성**(§12.4 `:9061-9121`) | S1(빌드 1회) |
| B10 헤드룸 worklist(9139-9196) | B9 구조, ctx.sized | vds(set_device_vds), sibling W/gm/gds, vsb setdefault | `_HeadroomDependencyNotReady` 진전카운트 고정점(C-c 우회), 교착 시 ValueError. 내부 광범위 except 2곳(7852, 8006) | **순환 블록 C-c**(vds↔노드전압↔vsb↔diode창↔gm_id/W) |
| B11 vsb 재조정(9201-9214) | ctx.sized vds, by_name, vdd | vsb만 | **W/gm/gds 미갱신**(§12.6-1), `report.conflicts` 미검사(`:9209`, §12.6-2) | C-c 순환 블록 내부 + 봉인 게이트 |
| B12 diode 자기일관 gm_id(9236) | L·vds·ID | diode gm_id/W, `_gm_id_source` | 순서: B13 이전이어야 함(주석 `:9232-9235`) | gm_id pass 블록 |
| B13 gm_id_role pass(9238-9286) | L, vds, vsb(entry 우선), ID | gm_id/gm/W/gds | ID≤0 → Infeasible, L/vds 없음 → ValueError | gm_id pass 블록 |
| B14 gm_id_match_vgs_of pass(9306-9351) | companion gm_id/L/vds | gm_id/gm/W/gds | 2-pass 고정, 체인 미지원 | gm_id pass 블록 |
| B15 matching gm_id 전파(9373-9427) | pairs_meta, `_gm_id_already_authoritative` | 대상 소자 전체 재계산 | 권위 판정 불가 시 ValueError | gm_id pass 블록 |
| B16 조인트 스캔 전역 보정(9434-9435) | `_scb_joint_plan_by_devices` | 그룹 gm_id/W 재적용 | 전역 metric 이중계산(6468 vs 9468), 위반 시 전수 스캔 재실행 | metric 블록 + 조인트 스캔 S2 |
| B17 vsb 게이트(9441-9448) | by_name, sized, vdd | — | **`ValueError`**(§12.6-3) → SLSQP/grid/warm-start는 `InfeasibleSizingError`만 잡으므로 탐색 전체 크래시 | 봉인 게이트(C-b) → 구조화 실패 |
| B18 L 동치류 게이트(9454-9467) | classes, sized L | — | **`ValueError`**(§12.6-3) 동일 | 봉인 게이트 |
| B19 metric 계산(9468) | metrics_specs 전부 | metrics_result | B16과 중복 metric, 매 평가 전부 재계산 | metric 블록(S2 적재) |

## 3. 요약

### 등급별 개수 (100개)
- **R0 35** / **R1 39** / **R2 12** / **D 11** / **DUP 3**

### R0 목록 (새로 만들면 중복이 되는 것)
`_hashable_key`, `_full_circuit_devices`, `_metric_smallsignal_ratio_db`, `_metric_smallsignal_gain_db`, `_metric_cmrr_estimate`, `_metric_psrr_estimate`, `unit_hint_from_metric_name`, `metric_unit_scale`, `validate_no_legacy_vs_key`, `validate_metric_units`, `compute_metric`, `_shared_current_groups_from_compensation`, `_evenly_subsample`, `_build_shared_current_joint_plan`, `apply_theta_feed`, `_constraint_tol`, `_lerp`, `_metric_stage_budget_vds_by_device`, `reserved_vds_for_other_stack_members`, `make_matching_feasibility_check`, `_hr_vfind`, `_hr_thin_singleton_ideal_source_check`, `_hr_sum_ref_vds`, `_hr_verify_group_kvl_sum`, `require_declared_spec_source`, `derived_bounds_path`, `_base_stack_id`, `_theta_feed_footprint`, `extract_linear_feasibility_constraints`, `_group_score_metric`, `_group_score_interior`, `apply_and_revalidate_pair_adjustment`, `_sync_finger_fixup`, `suggest_matching_finger_growth`, `apply_and_revalidate_matching_finger_growth`

### R2 목록
`_run_shared_current_joint_scan`, `_refine_shared_current_joint_scan_for_full_circuit_constraints`, `_feed_metric_stage_budget`, `_HeadroomDependencyNotReady`, `_hr_resolve_vertical_group`, `spec_fingerprint`, `_build_theta_evaluator`(+`_evaluate`), `optimize_full_circuit_budget`, `derive_theta_dependency_graph`, `search_stage_budget_L_warm_start`, `presolve_warm_start`, `_optimize_theta_slsqp`

### DUP 쌍
- `_theta_device_map`(10933) ↔ `_collect_device_refs`(11826) ↔ `_theta_feed_footprint`(10174)
- `_fixup_euler_blocked_rows`(12131) ↔ `run_topology_pipeline_with_finger_fixup`(12436)
- (D 겸) `_telescopic_class_ab_open_loop_response`(5064) ↔ `_full_circuit_response`(5543); `_cmrr_/_psrr_telescopic_class_ab_cmfb`(5170/5312) ↔ `_metric_smallsignal_ratio_db`(5586); `_psrr_telescopic_class_ab`(5256) ↔ `_cmrr_telescopic_class_ab`(4837); `_load_telescopic_topology_cached`(5045) ↔ `_load_full_topology_cached`(5379)
- (행 내부) `_feed_root_ratio._ref_id` ↔ `_feed_root_signed_sum._ref_id`; `_hr_vfind` ↔ `search_stage_budget_L_warm_start._lc_find`; 격자 리터럴 `:6283` ↔ `:6632`; 위반량 합 공식 `:9785`/`:10906`/`:11570`/`:11619`; 전수 스캔 루프 `:6415` ↔ `:6479`; finger 동기화 루프 `_sync_finger_fixup` ↔ `:9934`/`:12230`/`:12420`

### D 목록
- 삭제 후보(라이브러리 0 사용, self-test만): `_load_telescopic_topology_cached`, `_telescopic_class_ab_open_loop_response`, `_telescopic_open_loop_device_names`, `_telescopic_class_ab_open_loop_gains`, `_cmrr_telescopic_class_ab_cmfb`, `_psrr_telescopic_class_ab`, `_psrr_telescopic_class_ab_cmfb`, `_optimize_theta_slsqp_block_coordinate`, `load_derived_bounds`(probe 전용)
- 배선 필요: `lut_conditions_from_npz`(호출자 0 → S0 LUT 메타), `validate_theta_declaration_order`(self-test만 → 빌드 게이트)

### 계획서(§12.6)에 없던 추가 발견
1. `_resolve_nulling_resistor_ohm` 캐시 스테일: `dataclasses.replace`가 ctx 캐시 dict를 공유(`:3013`, `:11892`)하고 키가 소자명뿐(`:5499`).
2. `_hr_resolve_vertical_group` 광범위 `except Exception` 2곳(`:7852`, `:8006`) — §12.6-6 목록에서 빠짐.
3. `repair_infeasible_baseline._probe`의 `except Exception`(`:11028`)도 조용히 삼킴.
4. `FeedHandler.touches` 미사용 필드, 미사용 중첩 래퍼 6개(`:7478`, `:7669`, `:8646`, `:8649`, `:9144`, `:9147`).
5. `optimize_full_circuit_budget`의 `floorplan_target` 재시도 경로(`_pick_split_target`/`_score_floorplan`)는 SPECS·self-test 실행 0회.
6. `resolve_stack_layout` 위치가 §8.4(`stick_diagram`)와 다름.
