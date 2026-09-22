# 함수 재사용 레지스트리 -- gain-budget-gmid-sizing

> 작성 2026-09-14, 기준 커밋 78b58c6. 계획서 §13(v4.44)의 부속 문서.
> **목적: 이미 있는 것을 다시 만드는 실수를 막는다.** 줄 번호는 코드가 바뀌면 틀어지므로 **이름으로 grep**한다.
> 원자료(함수별 전체 판정표): `docs/03-analysis/gain-budget-gmid-sizing-function-audit/agent1~6*.md`

## 0. 사용 규칙 (강제)

새 함수를 쓰기 전에 **반드시** 이 순서로 확인한다.

1. 이 문서에서 책임(개념)을 검색한다 -- 이름이 달라도 같은 계산일 수 있다(§2 정본표).
2. `grep -n "def <후보이름>"` + **호출부 grep**(정의만 보고 판단하지 않는다 -- 호출자 0이면 D).
3. 등급에 따라:
   * **R0** -- 그대로 호출한다. 같은 식을 인라인으로 다시 쓰지 않는다(`size_transistor` 식이 4곳에 인라인 복제된 사례).
   * **R1** -- 그 함수를 고친다. 새 함수를 만들지 않는다.
   * **R2** -- §12 구조로 대체 예정. 새 호출부를 늘리지 않는다.
   * **D** -- 호출하기 전에 배선/삭제 결정(사용자 승인)부터.
   * **DUP** -- §2 정본만 쓴다.
4. 새 함수를 추가하거나 대체했으면 **같은 커밋에서** 이 문서를 갱신하고, 대체된 옛 함수를 **삭제**한다(삭제 안 해서 다음 grep에 후보가 둘 나오는 것이 재작성 실수의 3번째 원인).

## 1. 집계

| 파일 | R0 | R1 | R2 | D | DUP | 비고 |
|---|---|---|---|---|---|---|
| sizing_recipe.py | 84 | 77 | 19 | 27 | 11 | 표 행 기준(여러 함수를 한 행에 묶은 경우 1) |
| stick_diagram.py | 81 | 16 | 12 | 19 | 7 | 표 행 기준(여러 함수를 한 행에 묶은 경우 1) |
| 기타 모듈 | 21 | 16 | 1 | 2 | 1 | 표 행 기준(여러 함수를 한 행에 묶은 경우 1) |

감사자 요약 기준(행 묶음 전 개수): sizing_recipe.py R0 84 / R1 77 / R2 19 / D 27 / DUP 11 (218), stick_diagram.py R0 101 / R1 16 / R2 12 / D 20 / DUP 7 (158).

## 2. 개념별 정본 (DUP 해소 기준)

같은 개념을 여러 함수가 계산한다. **정본 하나만 쓰고 나머지는 정본을 호출하도록 바꾸거나 삭제한다.**
★ 표시는 회로 해석이 걸려 있어 **사용자와 공동분석 후 확정**한다(정의가 달라 결과가 다르다).

| 개념 | 정본(제안) | 중복 | 상태 |
|---|---|---|---|
| W 계산 `W=L*ID/IDu` | `size_transistor` / LUT `_sizing_bundle` | `find_optimal_sizing`, `feasible_gm_ids`, `search_gm_id_for_role`, `feasible_L_window`에 인라인 4곳 | 식 동일 -- 행동 보존 통합 가능 |
| diode 판정 | `is_diode_connected` | `stick_diagram.find_diode_stacks`(운영 0), SD 인라인 `gate==drain` 3곳, netclass role 기반 | ★ `find_diode_stacks`는 이웃 diode까지 포함(16/1/20 불일치의 원인) |
| 전류미러 그룹 | `true_current_mirror_groups`(connectivity, 키 kind·gate·source) | `stick_diagram.find_matching_candidates`(키 kind·gate 또는 kind·bias·rail), `_mirror_ratio_error_pairs`(선언 기반, 첫 쌍만), probe 3곳 복제 | ★ B19'에서 11 vs 18소자로 결론이 뒤집힌 원인 |
| diffpair / tail | (미정) | `find_differential_pair_candidates`, `_diff_pair_layer1_groups`, `_propose_gm_id_roles`(SD, connectivity) vs `gain_stage_tails`, `input_referred_offset_pairs`(SR, 선언) | ★ S1 유도 정본을 정해야 함 |
| 노드 DC 전압 | `propagate_node_voltages`(평가당 1회로) | 한 평가 안 4곳 재호출, `_hr_sum_ref_vds`·헤드룸 vsb 전파가 다른 순회로 같은 값, probe 2곳 | §12 D1 결정에 종속 |
| KCL 엣지 | `stick_diagram._kcl_and_matching_edges` | `kcl_series_union`이 같은 엣지를 따로 구현, `_metric_kcl_residual` | 행동 보존 통합 가능 |
| 스택 KVL 합 | `_hr_verify_group_kvl_sum` | `solve_diode_stack_current`(운영 0), 3곳 재계산 | |
| 레일 넷 집합 | (상수 하나로) | SD `_RAIL_NETS` 소문자만 vs SR 대소문자 2곳 | 불일치 -- 결함 후보 |
| topology 로딩 | `_load_full_topology_cached` | `load_topology` 직접 호출(SR 4845/5056/8493, SD `run_topology_pipeline`, fixup), `json.load`(SR 8315) | 캐시 키를 내용 해시로(C-d) |
| theta가 건드리는 소자 | `_theta_feed_footprint` | `_theta_device_map`, `_collect_device_refs` | |
| euler 행 수정 전략 | `run_topology_pipeline_with_finger_fixup` | `_fixup_euler_blocked_rows`(docstring이 "정확히 같은 전략") | |
| 위반량 합 | (함수 하나로) | 4곳 인라인 | |
| union-find | (유틸 하나로) | `design_report` + SR 2곳 + SD 2곳 | |
| 다선형 보간 | `_multilinear_interp` | `_multilinear_interp_point_multi` 복붙 | |
| 이분 역산 뼈대 | (하나로, **단조성 검사 포함**) | `_invert_gm_id_for_current`, `solve_id_for_target_gm` | 단조성 미검사 결함 동반 |
| gain metric | `_metric_smallsignal_gain_db` | `_metric_folded_cascode_gain_db` | folded_cascode가 사용 중 -- 4회로 재측정 후 |
| PM metric | `_metric_parasitic_pm_deg` | `_metric_folded_cascode_pm_deg` | 〃 |
| CMRR | `_metric_smallsignal_ratio_db` | `_cmrr_diff_pair_tail` | 〃 |
| MNA 소자 스탬프 | `build_ac_network` | `full_circuit_response_at_omega`, `_mna_solve_smallsignal` | |
| HTML 리포트 | `design_report.render_html_report` | 계획 §8.5 "신규" `render_design_report_html()` | **새로 만들지 않는다** |
| diode 고정점 | `solve_diode_connected_vds` | 계획 §7.3/§8.4의 `_solve_diode_connected_vgs_fixed_point` | 이름만 다름 -- **새로 만들지 않는다** |
| L grid 스냅 | `quantize_L` | SD `_quantize_to_grid`(의도적 사본) | 모듈 경계 결정 후 |

## 3. R0 -- 수정 없이 그대로 재사용 (새로 만들면 중복)

### sizing_recipe.py (84)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `GmIdLUT` | LUT 추상 인터페이스(`gm_id_to_id_density`/`gm_gds_ratio`는 NotImplemented) | gmid_sizing_engine.py | 순수 인터페이스 |
| `SizingResult` | 사이징 결과 dataclass(gm, gm_id, ID, W, gain) | gmid_sizing_engine.py |  |
| `QuasiStaticVerdict` | 준정적 판정 결과 | gmid_sizing_engine.py |  |
| `check_quasi_static` | fT ≤ margin·f_nqs | gmid_sizing_engine.py | margin 기본 0.1은 호출부 `quasi_static_margin` 기본값으로 노출됨 |
| `_multilinear_interp` | N차원 다중선형보간(순수 파이썬 bisect) | gmid_sizing_engine.py | 경계는 clamp(외삽 안 함) |
| `SemiEmpiricalGmIdLUT._w_ref_effective` | 기준폭(W_ref 또는 L) | gmid_sizing_engine.py | `find_optimal_sizing`이 private 메서드를 직접 호출(944) -- 캡슐화 문제만 |
| `SemiEmpiricalGmIdLUT._query_multi` | 여러 배열 동시 보간 래퍼 | gmid_sizing_engine.py | 상위 `_solve_vgs` 캐시 뒤라 자체 캐시 불필요 |
| `SemiEmpiricalGmIdLUT._sizing_bundle` | find_optimal_sizing 핫루프용 (IDu, gm/gds, cgg_raw) 일괄 | gmid_sizing_engine.py | 개별 메서드와 동일식(465-469) |
| `SemiEmpiricalGmIdLUT.id_density_at_vgs` | VGS에서 직접 IDu(B22) | gmid_sizing_engine.py |  |
| `SemiEmpiricalGmIdLUT.gm_id_to_id_density` | gm_id→IDu(W/L=1 기준) | gmid_sizing_engine.py |  |
| `SemiEmpiricalGmIdLUT.cgg_absolute` | W_target으로 스케일한 절대 Cgg | gmid_sizing_engine.py | 호출부 `_size_all:1358`이 vsb=0.0 하드코딩(optimize_multistage 비고) |
| `SemiEmpiricalGmIdLUT.gm_gds_ratio` | 로그공간 gm/gds(B15) | gmid_sizing_engine.py |  |
| `SemiEmpiricalGmIdLUT.vgs_for_gm_id` | `_solve_vgs` 공개 래퍼 | gmid_sizing_engine.py | 의도된 공개 별칭 |
| `SemiEmpiricalGmIdLUT.gm_id_for_vgs` | VGS→gm_id 역보간(VGS 오름차순 np.interp) | gmid_sizing_engine.py | 범위 밖이면 명시적 ValueError(700-703) |
| `SemiEmpiricalGmIdLUT.noise_1f_density` | 1/f 게이트환산 잡음, SID_1F 없으면 ValueError | gmid_sizing_engine.py | 현재 LUT에 SID_1F 없음(713-716) -- metric을 선언하면 명시적으로 실패 |
| `dense_candidates` | 실측 격자 범위 안 n개 후보(앵커 우선, 촘촘하면 서브샘플) | optimizer(탐색 격자 생성) | 서브샘플 인덱스식(790)이 `_grid_points_in_range:844`와 동일(소규모 코드 중복) |
| `quantize_L` | L을 grid_step 배수로 스냅(nearest/floor/ceil) | optimizer |  |
| `_grid_points_in_range` | [lo,hi] 안 grid_step 배수 나열/서브샘플 | optimizer | n=1 ZeroDivision 수정 기록(836-843) |
| `layout_grid_L_candidates` | LUT 범위 안 레이아웃 그리드 L 후보 | optimizer | docstring이 대체 대상이라 부르는 `dense_L_candidates()`(851)는 존재하지 않음(문서 부정확) |
| `_COMPENSATION_REGISTRY` | topology.json `compensation.function` 문자열 allowlist 디스패치 | gmid_sizing_engine.py | `from topology_library import ...`(1464)가 모듈 중간 import |
| `_LUT_VDSAT_ROLES` | LUT에서 VDsat을 유도할 role 집합("floating_current_source") | gmid_sizing_engine.py | role 문자열 상수(데이터) |
| `feasible_gm_ids` | (L,ID,vds,vsb)에서 W_bounds 안에 드는 gm_id 목록 | gmid_sizing_engine.py | 단일 술어로 추출됨. 단 `search_gm_id_for_role:2233-2235`는 이 함수를 안 쓰고 같은 필터를 인라인으로 반복(아래 DUP 기록) |
| `vgs_alias_map` | `gm_id_match_vgs_of`(device_roles + theta feeds) → `{소자: 레퍼런스}` VGS 동치 | circuit_state_graph.py(S1 typed edge) | 순수 선언 파싱 |
| `_vgs_root` | alias 체인 뿌리(순환 안전) | circuit_state_graph.py |  |
| `HeadroomPolicy` | 헤드룸 배정 정책 객체(cascode_fn, thin_roles) | gmid_sizing_engine.py | 컨테이너 자체는 결함 없음. 계획상 ctx 접근 시그니처 확장은 남음 |
| `measure_L_knee` | L 격자 전수 스캔으로 한계 Δ(gm/gds)/Δ(W·L) 최대 구간 상단 L | gmid_sizing_engine.py | **부분**: 시그니처가 명세와 다름(kind 인자 없음, vsb 추가, float가 아니라 dict 반환 2353-2355). 기능·비단조 skip 보고는 명세 취지대로. §7.10의 짝 함수 `L_bounds_from_ft_and_matching()`은 이 범위에 없음(아래 요약 참고) |
| `l_sharing_classes` | 미러군 + same_as_device + matching_pairs를 union-find로 L 동치류 | circuit_state_graph.py(S1 L 동치류) | 순수 구조 유도. 캐시 키는 호출 래퍼 쪽 경로 문자열(§12.3-7, 래퍼 책임) |
| `l_class_owners` | 동치류별 주인(input tail > 다른 gain tail > 없음), needs_joint_sweep | circuit_state_graph.py | 결정론적 정렬(2507-2509) |
| `audit_l_sharing_consistency` | 동치류 안에서 L이 갈린 류 보고(`_L_source` 포함) | circuit_state_graph.py(S2 봉인 게이트, C-b) | 함수 자체는 순수. **호출부**가 결과를 `ValueError`로 올림(9462) = **§12.6-3**(SLSQP가 그 점에 들어가면 탐색 전체 크래시). `_L_source` 필드는 C-a 출처의 초기 형태 |
| `_metric_sum_current` | devices(없으면 전체)의 ID 합 | gmid_sizing_engine.py(metric) | ID 없는 소자는 KeyError(명시적) |
| `_metric_sum_area` | `devices`(없으면 ctx.sized 전체)의 W*L 합 | gmid_sizing_engine.py | 순수 합산, 상태 없음 |
| `_metric_gain_stages_sum` | 스테이지별 Σgm/Σgds를 dB로 합산 | gmid_sizing_engine.py | 스테이지 독립 가정(부하효과 무시)은 폐형식 한계. 전체회로 값은 `smallsignal_gain_db`(5615)가 따로 잰다 -- 근사 수준이 달라 DUP로 보지 않음 |
| `_nmcnr_stage1_rout` | NMCNR stage1 비대칭 캐스코드 Rout | gmid_sizing_engine.py | 순수 계산. ro_fold 식은 3054와 중복(국소) |
| `_nmcnr_predict` | 실사이징 gm/R로 `topology_library.nmcnr_predict_ac_response` 호출, ctx 캐시 | gmid_sizing_engine.py | 캐시 키 = spec 해시+footprint gm/gds 내용(3169-3170), 수명 ctx(평가 1회) -> C-d 부합. 대상 모델은 sympy+ngspice 검증 완료(3135-3136) |
| `_metric_nmcnr_gain_db` | `_nmcnr_predict()["dc_gain_db"]` | gmid_sizing_engine.py | 얇은 래퍼 |
| `_metric_nmcnr_pm_deg` | 첫 0dB 교차 PM, 교차 없음/notch면 ValueError | gmid_sizing_engine.py | 정의불가 상태를 명시 실패(3203-3209) |
| `estimate_mismatch_sigma` | Pelgrom σ=slope/√(WL) | gmid_sizing_engine.py | 순수. 단위 µm 관례 명시 |
| `_metric_pelgrom_mismatch` | 쌍 σ를 RSS(mV) | gmid_sizing_engine.py | 같은 쌍 RSS가 `make_matching_feasibility_check` 7361-7364에 **복붙**(상대 쪽을 이 함수 호출로 바꿀 것) |
| `DiodeSelfConsistencyError` | diode Vgs=Vds 해 없음 전용 예외(ValueError 하위) | gmid_sizing_engine.py | 예외 계층만 제공 |
| `is_diode_connected` | gate==drain(connectivity만) | circuit_state_graph.py | §12.3-5 diode 정의 3벌(16/1/20) 중 정답 정의. `stick_diagram.py:3087 find_diode_stacks`가 DUP 쪽 -- S1 "개념당 정의 하나"의 기준으로 채택 |
| `solve_diode_connected_vds` | LUT 격자 브래킷+bisection으로 diode 자기일관 vds | gmid_sizing_engine.py | 순수, 수렴 실패 명시(3368). 캐시는 호출자 몫 |
| `NodeVoltageReport` | propagate 결과 dataclass(nodes/unresolved/conflicts/passes) | circuit_state_graph.py(S2 노드전압) | 값 컨테이너. 버전/출처 필드 없음(S2 이관 시 추가) |
| `derive_vsb_from_nodes` | 소스 노드전압 -> vsb(NMOS=V_s, PMOS=vdd-V_s), 모르면 None | circuit_state_graph.py | 순수. 벌크=레일 가정(3962-3964) 명시 |
| `_resolve_capacitor_farad` | passive 커패시터 값: value_farad > ctx.derived[key] > spec[key] > 오류 | gmid_sizing_engine.py | 0으로 때우지 않음(4186). derived 우선은 기존 관례. 출처 기록 없음(S2 이관 시 writer 표기 필요) |
| `_mirror_ratio_aggregate` | max/rss 집계, 알 수 없는 aggregate는 실패 | gmid_sizing_engine.py | 순수. 빈 목록이면 0.0 반환(4546-4547) -- 쌍 0개가 "오차 0"과 구분 안 됨(stack_headroom_slack 3499-3507이 금지한 패턴과 같은 모양, 참고) |
| `_metric_mirror_ratio_error_input_referred` | pairs의 V 성분 집계 | gmid_sizing_engine.py | 얇은 래퍼(결함은 `_mirror_ratio_error_pairs`에서 상속) |
| `_metric_mirror_ratio_error` | pairs의 % 성분 집계 | gmid_sizing_engine.py | 얇은 래퍼(결함 상속) |
| `_metric_battery_centering_deviation` | 두 출력게이트 레벨 합의 vdd 편차 | gmid_sizing_engine.py | 순수 조합(논문 절대값 미인용) |
| `_metric_nulling_resistor_ohm` | `_resolve_nulling_resistor_ohm` 보고 창구 | instance_report_builder.py(보고) 또는 gmid_s… | 얇은 래퍼, ctx 캐시 공유 |
| `_hashable_key` | dict/list→정렬 tuple 정규화(캐시 키) | gmid_sizing_engine(util) / circuit_state… | 순수. 내용기반 키 생성기라 S0/S2 입력 해시에 그대로 재사용 가능(새로 만들면 중복) |
| `_full_circuit_devices` | 전 MOSFET+저항을 MNA 스탬프 튜플로 변환 | gmid_sizing_engine | 순수 변환, 미사이징 소자는 KeyError(`:5527`). 캐시 없음(호출부 문제) |
| `_metric_smallsignal_ratio_db` | 두 여기의 응답비(dB) | gmid_sizing_engine | 순수. 성능은 5543에 위임 |
| `_metric_smallsignal_gain_db` | 전체회로 DM 이득(dB) | gmid_sizing_engine | 순수 |
| `_metric_cmrr_estimate` | circuit_family 2단 registry 조회 | gmid_sizing_engine | 순수 디스패치. registry 3항목 중 살아있는 것은 `diff_pair_tail` 1개 |
| `_metric_psrr_estimate` | 동일(PSRR) | gmid_sizing_engine | 위와 동일 |
| `unit_hint_from_metric_name` | 이름 접미사→단위 | topology_authoring | 순수 |
| `metric_unit_scale` | 선언 unit 환산계수(표에서만) | gmid_sizing_engine | 순수, 표에 없으면 거부 |
| `validate_no_legacy_vs_key` | device_roles 옛 `vs` 키 거부 | topology_authoring | 순수 게이트 |
| `validate_metric_units` | metric unit 선언 검증 | topology_authoring | 순수 게이트 |
| `compute_metric` | registry 계산기 호출×단위환산 | gmid_sizing_engine | 순수. 메모 없음 → 같은 metric을 `_refine...`(6468)·`_evaluate`(9468)·scorer(6370/6376)가 중복 계산(호출부 R2 사유) |
| `_shared_current_groups_from_compensation` | shared_gm_id_groups → 소자명 frozenset | circuit_state_graph S1 | 순수, 3곳 공유 단일 정의 |
| `_evenly_subsample` | 이산 격자 균등 서브샘플 | gmid_sizing_engine(util) | 순수 |
| `_build_shared_current_joint_plan` | 공유전류 그룹 조인트 스캔 계획(정적) | circuit_state_graph S1 / 유도 DAG | 순수(thetas 선언만) |
| `apply_theta_feed` | feed 타입→핸들러 디스패치 | gmid_sizing_engine | 순수 디스패치 |
| `_constraint_tol` | 제약 판정 상대공차 1e-9 | gmid_sizing_engine | 순수 |
| `_lerp` | 선형보간 | optimizer | 순수 |
| `_metric_stage_budget_vds_by_device` | metric_stage_budget 고정 vds 사전 스캔 | gmid_sizing_engine | 순수, `_feed_vds_fallback` 단일 폴백 공유 |
| `reserved_vds_for_other_stack_members` | vsid 컬럼의 타 멤버 예약 vds 합(재귀 확장) | gmid_sizing_engine | 순수, 모르면 None(보수). 결정론 정렬(`:7232`) |
| `make_matching_feasibility_check` | pelgrom/입력환산 오프셋 제약 콜백 | gmid_sizing_engine | 충분조건 증명 docstring(`:7318-7328`), 순수. vsb 0은 compensation 자체 가정(`:8844`)과 일치 |
| `_hr_vfind` | offset 매칭 union-find find(경로압축) | circuit_state_graph S1 | 순수. 동형 union-find가 `search_stage_budget_L_warm_start._lc_find`(`:10828`)에 재구현(DUP) |
| `_hr_thin_singleton_ideal_source_check` | thin singleton 우회를 ideal_sources로 정당화 | circuit_state_graph S1(유도 사실+증거 net) | 순수 구조 검증 — S1 `status/증거` 모델에 그대로 맞음 |
| `_hr_sum_ref_vds` | budget_reference_device vds 합 | gmid_sizing_engine | 순수(C-c 신호만 사용) |
| `_hr_verify_group_kvl_sum` | vsid 그룹 KVL 합=vdd 게이트 | gmid_sizing_engine(봉인 게이트 재료) | 순수 게이트, 소자별 breakdown. fold_group/same_as 제외는 문서화된 계약 |
| `require_declared_spec_source` | library 회로 spec 출처 선언 강제 게이트 | gmid_sizing_engine 진입 게이트 | 광범위 except 제거 이력(`:8205-8208`), 거부 확인됨 |
| `derived_bounds_path` | `<topology>.derived.json` 경로 | optimizer(S3 저장 경로) | 순수. 단 엔진은 사이드카를 안 읽고 topology.json `_derived`를 씀(아래 D 사유) |
| `_base_stack_id` | row 접미사 제거 | sizing_layout_convergence | 순수 정규식 |
| `_theta_feed_footprint` | feed 선언→roots/derived_writes/reads | circuit_state_graph S1(쓰기 집합) | 순수, 타입별 명시. §12.5.4 "구조적 쓰기 집합"의 정본 후보(제네릭 `_theta_device_map` 10933과 DUP 관계) |
| `extract_linear_feasibility_constraints` | A_signed KCL 부호제약을 선형부등식으로 역산 | optimizer | reference 한 점에서 얼린 근사임을 status/reason으로 명시. `except ValueError`는 결과에 기록(`:10546`) |
| `_group_score_metric` | 조인트 스캔 점수 = metric 최소 | optimizer | 순수 |
| `_group_score_interior` | 점수 = 최소 정규화 제약 여유 최대 | optimizer | 순수, 분모=선언값(0이면 1.0) |
| `apply_and_revalidate_pair_adjustment` | L3 후보를 L4로 순차 승인 | sizing_layout_convergence | 순수 오케스트레이션, ValueError는 rejected에 기록 |
| `_sync_finger_fixup` | overrides·ctx.sized 동기화 | sizing_layout_convergence | 순수. 동일 동기화 루프가 인라인 3곳에 재구현(`:9934-9938`,`:12230-12234`,`:12420-12424`) |
| `suggest_matching_finger_growth` | 3c용 min_fingers 성장 delta | sizing_layout_convergence | 순수 |
| `apply_and_revalidate_matching_finger_growth` | 성장 후보 1개 L4 재검증 | sizing_layout_convergence | 순수 |

### stick_diagram.py (81)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `_try_interdigitation_table_match` | 문헌 interdigitation 표 경로 | stick_diagram | 순수 |
| `interdigitate_layout` | hub-leaf 1행 interdigitation 배치 | stick_diagram | 결정론 |
| `build_mirror_symmetric_pattern` | 좌반부로 대칭 finger 패턴 생성 | stick_diagram |  |
| `_hubleaf_sequence_node_path` | finger 순서의 hub-leaf 경로 산출 | stick_diagram |  |
| `_common_centroid_from_pattern_table` | 표 기반 2D common-centroid | stick_diagram |  |
| `_try_pattern_table_match` | N=2 표 경로 분기 | stick_diagram |  |
| `common_centroid_layout` | N소자 common-centroid 배치(표/회전/탐색) | stick_diagram |  |
| `_fix_block_parity` | 블록 크기 홀짝 보정 | stick_diagram |  |
| `_common_centroid_nway_exact` | 회전대칭 최적 경로 | stick_diagram |  |
| `_proportional_round_robin` | 비율 유지 섞기 | stick_diagram |  |
| `_slice_into_rows` | 순환 시퀀스 행 분할 | stick_diagram |  |
| `_row_feasible` | 행 오일러 실현성 | stick_diagram |  |
| `_repair_row_parity` | 행 배분 오일러 보정 | stick_diagram |  |
| `_build_rows_from_shares` | 배분을 실제 finger 행으로(hierholzer) | stick_diagram |  |
| `_build_rows_from_shares_with_crossover` | crossover 허용판 | stick_diagram |  |
| `_common_centroid_residual` | 행 안 centroid 잔차 | stick_diagram |  |
| `_count_isolated_pairs` | 같은 행에 없는 소자쌍 수 | stick_diagram |  |
| `_common_centroid_nway_search` | 휴리스틱 탐색 경로 | stick_diagram |  |
| `_sorted_setmap` | set 맵 결정론적 렌더링 | stick_diagram | baseline README "결정론 전제" |
| `_scan_case_collisions` | net 이름 대소문자 충돌 | topology_authoring(검증) |  |
| `_to_analog_grammar_devs` | Transistor를 analog-grammar dict로 변환 | topology_authoring |  |
| `find_stack_edges` | `netclass.stack_edges` 래퍼 | topology_authoring |  |
| `SymmetryDispositionsVerdict` | 결과 레코드 | topology_authoring |  |
| `find_hub_merge_candidates` | 같은 hub 공유 행 병합 후보 | stick_diagram |  |
| `StructuralSymmetryVerdict` | 결과 레코드 | topology_authoring |  |
| `split_into_stacks` | stack_id 또는 (kind,finger_w)로 행 후보 분할 | stick_diagram |  |
| `shares_diffusion_node` | S/D 공유(게이트 제외) 판정 | stick_diagram |  |
| `_verified_euler_fix` | 그룹 오일러 검사+finger 조정 재검증 | stick_diagram |  |
| `merge_layout_groups_by_matching_pairs` | 매칭쌍으로 레이아웃 그룹 재병합 | stick_diagram | SR:5873 import 정리 대상 |
| `derive_horizontal_stack_groups` | vsid 그룹을 kind 분할+매칭 재병합 | stick_diagram |  |
| `FingerWidthIssue` | 결과 레코드 | stick_diagram |  |
| `check_finger_width_compatibility` | W가 finger_w 정수배인지 | stick_diagram |  |
| `StackGraph` | stack multigraph | stick_diagram | 계획 §11.1 표 마지막 행 |
| `build_graph` | Transistor 리스트를 finger multigraph로 | stick_diagram |  |
| `_degrees` | 차수/연결성 | stick_diagram |  |
| `EulerVerdict` | 오일러 3조건 판정 | stick_diagram |  |
| `hierholzer` | 오일러 경로 순회 | stick_diagram |  |
| `_mirror_node_map_from_pairs` | 매칭쌍에서 net 거울 대응 | stick_diagram |  |
| `_pair_odd_nodes_by_mirror` | 홀수차수 노드 거울 우선 짝짓기 | stick_diagram |  |
| `_build_crossover_segments` | 가상 edge로 segment 분할 | stick_diagram |  |
| `_count_matching_pair_splits` | segment 간 매칭쌍 분리 수 | stick_diagram |  |
| `_is_perfect_crossover_score` | 점수 0 판정 | stick_diagram |  |
| `_enumerate_perfect_matchings` | 완전짝짓기 열거 | stick_diagram | (2m-1)!! 폭발 상한 확인 필요 |
| `_select_crossover_pairing` | 최적 crossover 짝 선택 | stick_diagram |  |
| `find_min_crossover_layout` | 최소 crossover hub-leaf 배치 | stick_diagram |  |
| `AdjustmentSuggestion` | 단일 소자 finger ±1 제안 | stick_diagram |  |
| `PairAdjustmentSuggestion` | 쌍 finger 조정 제안 | stick_diagram |  |
| `UnitCellCandidate` | nominal W 근방 unit cell 후보 | stick_diagram |  |
| `BoxLayoutCandidate` | stack별 finger_w 탐색(Case A) | stick_diagram |  |
| `assign_finger_geometry` | 사이징 W를 finger/width로 배분 | stick_diagram |  |
| `apply_explicit_row_split` | 명시 row_split 균등 분할 | stick_diagram | self-test 등장 0회 |
| `pitch` | finger 1개 폭 근사 | stick_diagram |  |
| `RowGeometry` | 행 폭/높이 계산 | stick_diagram |  |
| `BoxShapeVerdict` | box-shape 게이트 | stick_diagram | SR:5875 import 정리 대상 |
| `StickResult` | stack 결과 | stick_diagram |  |
| `WalkVerdict` | 제안 순서 연속성 독립 검산 | stick_diagram |  |
| `mirror_symmetric_trail` | 매칭 인지 대칭 trail 선택 | stick_diagram |  |
| `build_stick_diagram` | stack별 오일러 결과 생성 진입점 | stick_diagram |  |
| `AuditCheck` | 감사 결과 레코드 | stick_diagram(직렬화는 instance_report_build… | `design_report.py:32`가 `_audit_result_json` 사용 |
| `CoverageVerdict` | 사이징 소자 전부 행에 배치됐는지 | stick_diagram |  |
| `INSTANCE_TOP_FIELDS`/`INSTANCE_SIZING_FIELDS` | instance.json 저장 필드 목록 단일 정의(IC3) | stick_diagram |  |
| `CompletenessVerdict`/`check_instance_completeness` | instance.json 저장 완전성 재검증(IC3, `save_instance_json` 배선) | stick_diagram |  |
| `NameCollisionVerdict`/`check_topology_name_uniqueness` | 소자/수동소자 이름 전역 유일성 재검증(IC3, `load_topology` 배선) | stick_diagram |  |
| `select_layout_tool` | 민감도/공유노드로 도구 선택 | stick_diagram |  |
| `audit_row_split` | 행 분할 후 euler/box/matching 고정 순서 감사 | stick_diagram |  |
| `_layout_result_to_rows` | 도구 반환값을 rows로 | stick_diagram |  |
| `_two_device_branch_outer` | 2소자 branch 바깥 단자 | stick_diagram |  |
| `_branch_composite_pair` | 거울 branch를 합성 소자쌍으로 | stick_diagram |  |
| `_composite_collapse_for_crossover` | crossover 전 branch 합성 | stick_diagram | `_sensitivity_of` 중첩이 `audit_row_split`, `_count_matching_pair_splits`에도 각각 있음(본문 동일성 미확인) |
| `find_min_crossover_layout_with_branch_composite` | branch 인지형 최소 crossover 래퍼 | stick_diagram |  |
| `repair_matching_safety` | 매칭 실패 행 재배치 반복 | stick_diagram | 같은 역할 이름의 중첩 헬퍼 4곳 중 하나(본문 동일성은 미확인) |
| `FloorplanBlock` | floorplan 레코드 | stick_diagram |  |
| `_block_center` | 배선 비용 | stick_diagram |  |
| `skyline_pack` | bottom-left skyline packing | stick_diagram |  |
| `_sweep_widths` | 폭 스윕/정사각 폭/높이 맞춤 | stick_diagram |  |
| `find_diffusion_safe_split_points` | 행 분할 후보 평가 | stick_diagram |  |
| `pack_floorplan` | spine+mirror pair packing | stick_diagram |  |
| `block_from_rows` | rows를 블록으로 | stick_diagram |  |
| `rebuild_floorplan` | rows만으로 floorplan 재조립 | stick_diagram |  |
| `_pack_by_subkind` | 기능 그룹 단위 packing | stick_diagram |  |
| `run_full_circuit_audit_from_topology` | topology.json만으로 full audit 자동 구성 | instance_report_builder |  |
| `_box_shape_json` | BoxShapeVerdict 직렬화 | instance_report_builder |  |
| `_audit_result_json` | AuditResult 직렬화 | instance_report_builder |  |
| `save_instance_json` | instance.json 작성 | instance_report_builder |  |

### 기타 모듈 (21)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `miller_ota_topology` | Miller 2단 보상식 -> `topology_fn(prev_cggs)->[gm1,gm2]` 팩토리 | `gmid_sizing_engine.py`(보상식 레지스트리) | `gmid_sizing_engine.py`(보상식 레지스트리) |
| `  └ topology_fn` | prev_cggs 고정점 반복용 gm | 〃 | 〃 |
| `  └ topology_fn` | 상수 gm 반환 | 〃 | 〃 |
| `nmcnr_compensation_elements` | Eq8/9 Cm1/Rm/Cm2 | 〃 | 〃 |
| `nmcnr_predict_ac_response` | 4-노드 KCL 정확 전달함수 -> crossings/notch/dc_gain | 〃 | 〃 |
| `  └ _H` | H(jw) | 〃 | 〃 |
| `  └ topology_fn` | 상수 반환 | 〃 | 〃 |
| `_kv_table` | dict 리스트 -> HTML 표 | 〃 | 〃 |
| `  └ _section` | 섹션 번호 | 〃 | 〃 |
| `save_html_report` | 파일 쓰기 | 〃 | 〃 |
| `_as_set` | 문자열/리스트 -> set | `topology_authoring.py` | `topology_authoring.py` |
| `_gen_netlist` | ngspice .control 루프 넷리스트(op+Y11/Y12+noise) | LUT 생성 도구 유지 | LUT 생성 도구 유지 |
| `_parse_output` | 'P' 마커 파싱 -> 6배열 | 〃 | 〃 |
| `_ltag` | L값 기반 체크포인트 태그 | 〃 | 〃 |
| `_cleanup_temp` | 임시파일 재시도 삭제 | 〃 | 〃 |
| `run_device` | 4D 배열 조립 | 〃 | 〃 |
| `_flag_dangling_nets` | S/D 단자 1개 net | `topology_authoring.py` | `topology_authoring.py` |
| `_flag_gate_only_nets` | gate-only net | 〃 | 〃 |
| `_net_table` | net -> (device, terminal) 역색인 | 〃 | 〃 |
| `render_markdown` | topology.md(사람 검토용 net 표) | 〃 | 〃 |
| `canonical_spec` | 정본 spec | `gmid_design_pipeline.py` | `gmid_design_pipeline.py` |

## 4. R1 -- 재사용하되 국소 수정 (새 함수를 만들지 말고 이것을 고친다)

### sizing_recipe.py (77)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `_QUERY_CACHE_MAX` | 4D 배열 적재, shape 검증, log(ID/GM/GDS) 사전계산(B15), 캐시 dict 5종 생성 | gmid_sizing_engine.py(+ S0 LUT 지문은 circu… | (1) `_gm_id_curve_cache`(389)·`_solve_vgs_cache`(396)·`_idu_scan_cache`(410)는 **상한 없음**, `_query_cache`만 상한(§12.6-7 계열). (2) LUT **내용 지문 없음** -- 외부 캐시가 `id(lut)`로 키잉(2593… |
| `SemiEmpiricalGmIdLUT._query` | 4축 보간 1점 + 메모 | gmid_sizing_engine.py | **§12.6-7이 지목한 줄(:434)**: 상한 도달 시 LRU가 아니라 **캐싱 중단**, 보고 없음. 키 `id(array)`는 인스턴스 속성 배열이라 안전(425-427) |
| `SemiEmpiricalGmIdLUT._idu_scan` | gm_id 격자 전체 (gm_id,IDu) 스캔 캐시 | gmid_sizing_engine.py | 캐시 **상한 없음**(496). gm_id별 ValueError를 필터로 삼키는 것은 문서화된 의도(479-482) |
| `SemiEmpiricalGmIdLUT._gm_id_curve` | (L,vds,vsb)의 VGS 격자 곡선 (ID, gm/ID) 캐시 | gmid_sizing_engine.py | 캐시 **상한 없음**(519). probe_gm_id_monotonicity.py도 직접 사용 |
| `SemiEmpiricalGmIdLUT._solve_vgs` | 목표 gm/ID의 rightmost-root VGS(B20), 범위 밖이면 ValueError | gmid_sizing_engine.py | 로직은 R0급(명시적 실패, 단조 곡선에서 비트 동일 587-606). 캐시 **상한 없음**(606)만 수정 |
| `find_optimal_sizing` | (L,VDS,gm_id) 3중 격자 전수 스윕 + 제약 + power_tolerance 재선정 | gmid_sizing_engine.py | (1) 매 호출 `all_candidates` 전량을 리스트로 만들어 반환하지만 엔진 호출부 4곳이 전부 `_`로 **버린다**(1164,1208,1219,1239) = §12.2 G1 "계산 결과 버림" + 메모리 낭비. `return_all` 옵트인으로. (2) `vsb` 인자가 있으나 `optimi… |
| `solve_id_for_target_gm` | W 고정 소자에서 gm=gm_target인 ID를 gm_id 이분탐색 | gmid_sizing_engine.py | 이분법이 **gm(gm_id) 단조감소를 검사 없이 가정**(1608-1610, 1629-1632). 같은 파일 `_solve_vgs` docstring(536-538)이 PMOS gm/ID(VGS) 비단조 75.3%를 실측으로 기록 -- rightmost-root 이후에도 gm(gm_id)가 단조인지는… |
| `_invert_gm_id_for_current` | 주어진 전류를 만드는 gm_id 이분탐색 | gmid_sizing_engine.py | `solve_id_for_target_gm`과 같은 결함(단조 가정 1641-1643, 무검사) + 이분법 뼈대 복붙(1647-1663 vs 1617-1633) -- 공통 `_bisect_monotone(f, lo, hi, target)` 헬퍼로 합칠 것 |
| `_default_cascode_headroom` | thin role VDS = 2/gm_id + margin, 없으면 min_vds | gmid_sizing_engine.py | `margin` 기본 **0.05 리터럴**(1731) -- 근거 없는 상수(C1). `2/gm_id` 근사 자체는 방법론 2.7 인용(1761-1763) |
| `lut_vdsat_headroom` | 포화 최소 VDS = 2/max(실현가능 gm_id) | gmid_sizing_engine.py | (1) **`except Exception: feas = []`**(1797) -- 광범위 except가 LUT 오류를 "후보 없음"으로 바꿔 더 느슨한 max(grid) 하한으로 조용히 진행(§12.6-6과 같은 부류). (2) 기본 gm_id 격자 `[i*0.5 for i in range(4,61)]… |
| `allocate_stack_headroom` | 직렬 스택 VDS 배정: thin role/구간(diode) 하한 선배정 → 나머지 균등분배, 부족/잉여는 InfeasibleSizingError, 합=vdd assert | gmid_sizing_engine.py | **계획과 다름**: 균등분배가 그대로다(2062-2065). diode 구간 소자에 `lo`를 주는 선택은 잠정이라고 자인(2032-2034). 합 검증이 `assert`(2084)라 `python -O`에서 사라짐 -> 명시적 raise로. 실패를 조용히 맞추지 않는 점은 좋음(2054-2082) |
| `_feed_vds_fallback` | declared vds → min_vds_by_role[role] → 폴백 상수 | gmid_sizing_engine.py | 순수함수이나 최종 폴백이 상수 0.6/0.2(2134-2135) -- role에 min_vds 선언이 없으면 `lut_vdsat_headroom`처럼 LUT에서 유도하거나 거부해야 함 |
| `search_gm_id_for_role` | W_bounds(+vgs_max) 실현가능 gm_id 스캔 후 role별(matching/balanced/moderate/gain/load) 선택 | gmid_sizing_engine.py | (1) **계획과 다름**: L축 내부화 미구현(L은 여전히 고정 인자). (2) W 필터 인라인(2233-2235)이 `feasible_gm_ids`(1755-1756)와 중복. (3) 기본 격자·W_bounds 리터럴(2155,2229). (4) 실패는 InfeasibleSizingError로 명시(… |
| `gain_stage_tails` | tail 선언 + gain metric `stages` + drain=stage source 연결로 stage tail, excite net으로 input stage | circuit_state_graph.py(S1v 여기 뷰 `stage_i… | (1) `gain_stages_sum` metric이 여럿이면 **마지막 것이 덮어씀**(2463-2464). (2) gain metric 판정이 타입 문자열에 `"gain"`이 들어 있는지로 결정(2467). §12.7-5 "S1v 여기 뷰 + stage_index -- 손 선언과 대조" 대상 |
| `_KNEE_L_CACHE` | kind별 knee L = gm_id 격자 전체 measure_L_knee 중앙값(vds는 격자 중앙), 격자 미선언이면 ValueError | gmid_sizing_engine.py(값은 S2/S3 유도 임계값) | 모듈 전역 캐시 키가 **`id(lut)`**(2593)이고 **상한 없음**(2608) -- §12.3-7 / C-d. LUT 지문으로 키잉할 것. 호출부 `_evaluate:9006`은 `except (KeyError, ValueError): pass`(§12.6-6 지목 줄) |
| `synthesize_l_class_thetas` | 주인 있는 동치류마다 `L_class__<root>` theta 파생(선언 L theta가 건드린 류 제외, 상한=선언 L theta 상한의 min) | circuit_state_graph.py(S1 파생) + optimize… | (1) 상한을 **다른 선언 theta의 상한 min에서 빌려온다**(2662) -- 근거가 "실측 실패 회피"(2656-2661). (2) **호출부**가 `except (KeyError, ValueError): pass`(8511)로 감싸 **L_class theta가 조용히 0개**가 될 수 있음 … |
| `_FEASIBLE_L_WINDOW_CACHE` | 자기 ID로 W_bounds 안에 드는 L 구간 양 끝(diode면 diode 창/고정 vds 판정) | gmid_sizing_engine.py | **§12.6-7 지목 줄(:2758)**: 상한 도달 시 캐싱 중단, 보고 없음. 키에 **`id(lut)`**(2736) = §12.3-7 지목. 구간이 연속이 아닐 수 있음을 자인(2725-2728, 양 끝만 반환). diode 경로의 `diode_vds_window`는 3570(범위 밖) |
| `_L_ROLE_TARGETS` | L_role(mirror/bias_replica) 소자 L = clamp(knee 또는 창 하한, 창) | gmid_sizing_engine.py | (1) diode 판정이 `_diode_set_cached`(5452) -- §12.3-5 "diode 집합 16/1/20개" 중 한 정의. (2) `vds_is_fixed=bool(e.get("vds"))`(2859)라 vds=0.0이면 미고정 취급. (3) 창이 비었거나 ID 없으면 **knee를 그… |
| `derive_class_L` | 주인 없는 동치류 공통 L = clamp(멤버 knee 중앙값 또는 교집합 하한, 창 교집합) | gmid_sizing_engine.py | `derive_role_L`과 같은 diode 정의·W_bounds 리터럴(2904-2909). None이면 호출부가 `continue`(8988)로 소자별 L을 그대로 두고, 갈림은 마지막 게이트가 ValueError로 잡음(9462, §12.6-3). knee 중앙값을 kind 구분 없이 섞음(291… |
| `_metric_flicker_plus_thermal_sum` | stages 소자 열+1/f 잡음 RSS(V/√Hz) | gmid_sizing_engine.py | `gamma=2/3`,`freq=1.0`,`temperature_K=300` 기본값을 조용히 주입(3221-3223) -- 상수 금지 원칙 위반. 선언 필수로 바꿀 것 |
| `diode_vds_cached` | solve_diode_connected_vds 메모(해 없음도 None 캐시) | gmid_sizing_engine.py | 키에 `id(lut)`(3383) -- §12.3-7/C-d 위반(LUT 내용이 아니라 객체 id). 함수 속성 dict **상한 없음**. `set_device_vds` 3557은 이 캐시를 안 쓰고 원함수를 직접 호출 |
| `_metric_stack_headroom_slack` | vertical_stack_id 그룹별 (예산 - Σdiode Vgs - Σ비diode vds) 최솟값, 측정불가 그룹 있으면 ValueError | gmid_sizing_engine.py(값) + 그룹/union-find… | 매 평가마다 `groups`·offset union-find·budget_reference를 topology에서 재구성(3428-3449) -- 입력이 topology뿐인 정적 구조라 S1 캐시 대상(§12.4 "정적 스택 구조 매 평가 재구성"과 같은 부류). offset union은 `_hr_vfin… |
| `set_device_vds` | `ctx.sized[name]["vds"]` 단일 setter + diode 자기일관 검사 + `_vds_source` 출처 태그 | circuit_state_graph.py(S2 타입 setter) | §12.5.2 C-a가 "`set_device_vds` 일반화"로 명시한 원형. 국소 수정: (1) 3557이 캐시 없이 `solve_diode_connected_vds` 직접 호출(회당 LUT 100회+) (2) vds만 보호 -- vsb는 `reconcile_vsb_from_nodes` 4012가 원… |
| `diode_vds_window` | diode(+VGS 공유 미러 멤버)가 W_bounds 안에 드는 vds 구간 (lo,hi) | gmid_sizing_engine.py | 캐시 키 `id(lut)`/`id(m[0])`(3617-3619) -> C-d 위반, 함수 속성 dict 상한 없음(§12.6-7 계열). `except (ValueError,KeyError): continue`(3630,3642)는 격자점 범위밖 스킵이라 정당 |
| `apply_diode_self_consistent_gm_id` | diode gm_id를 자기 vds에서 역유도(gm_id_for_vgs)하고 gm/W/gds 마감, 불일치는 명시 실패 | gmid_sizing_engine.py | 국소: (1) `W_bounds` 기본값 `(1e-6,200e-6)` 주입(3791) -- 상수 기본값 (2) 3804가 `_gm_id_already_authoritative()` 대신 `_L_source`만 검사(정의 2벌) (3) §12.3-8 순환 "diode vds↔gm_id↔W"의 한 방향 --… |
| `propagate_node_voltages` | 레일에서 vds로 전 노드 DC 전압 전파(sorted 결정론, 다중도달 conflicts 기록) | circuit_state_graph.py | **§12.6-2 확인**: `conflicts`를 읽는 코드가 3891-3954 밖에 0건(grep; 11226은 무관 지역변수) -> 먼저 도달한 경로 값이 정본. 캐시 없음, 평가당 19회(§12.3-4). 7852·8007의 광범위 `except Exception: None`이 이 함수 실패를 조… |
| `reconcile_vsb_from_nodes` | 헤드룸 후 전 소자 vsb를 노드전압으로 덮어씀, undetermined 반환 | circuit_state_graph.py(C-b) | **§12.6-1 확인**: vsb만 대입(4012), 옛 vsb 기준으로 이미 계산된 W/gm/gds는 갱신·무효화 안 함 -> 버전 혼재(7/51). `rep.conflicts` 무시. setter 우회(원시 대입). 국소 수정: changed 소자 재사이징 또는 봉인 게이트로 거부 |
| `audit_vsb_consistency` | 최종 vsb vs 노드전압 유도값 불일치 목록 | circuit_state_graph.py(봉인 게이트) | reconcile(4001-4014)과 같은 루프를 다시 돌며 propagate 재계산(캐시 없음). **vsb만 비교** -> W/gds 버전 불일치는 통과(§12.3-3). 실패가 `ValueError`라 SLSQP 크래시 경로(§12.6-3, 9445) |
| `_mna_stamp_capacitance` | 소자 Cgg(gate-source)+선언 커패시터 (a,b,C) 목록 | gmid_sizing_engine.py | **§12.6-6 광범위 except 4217 확인**: `except (KeyError, ValueError): continue`로 LUT 범위 밖 소자의 Cgg를 조용히 누락 -> cap_total 과소 -> PM 과대. 인자 `idx` 미사용(4259에서 None). 수정: 누락 목록 반환/실패 |
| `build_ac_network` | omega 무관 부분(소자 스탬프·용량·노드목록·고정노드)을 한 번 조립 | gmid_sizing_engine.py(값은 S2 블록 memo) | 재사용 수명이 metric 한 번의 스윕뿐. 같은 평가에서 `_full_circuit_response`(5548)가 `_full_circuit_devices`를 smallsignal metric마다 **다시 조립**하고, 노드목록 루프(4252-4258)는 5552-5559와 동일 코드 -> ctx.si… |
| `_metric_parasitic_pm_deg` | DC~ω_c 25점 로그스윕 위상 언랩 -> PM=180-누적지연 | gmid_sizing_engine.py | 국소: (1) `n_pts=25`, 시작 `ω_c·1e-4`(4407-4408)가 박힌 상수이고 "A0가 1e4를 넘지 않는 한 안전"(4405)이라는 가정에 의존 -- 상수 금지 원칙 (2) 4217 Cgg 누락을 그대로 물려받아 PM 과대 가능 (3) ω_c를 derived 우선으로 읽음(4384) … |
| `_metric_kcl_residual` | 내부 노드 ΣI 잔차 최댓값(ideal_sources value_amp 반영, null이면 노드 제외) | gmid_sizing_engine.py | 계산 자체는 순수. 국소: 레일 이름을 인라인 튜플(4456)로 다시 정의 -- `_DEFAULT_RAIL_HI/LO`(3882-3883)와 정의 2벌. passive 전류 미계상(명시, 4448) |
| `_metric_supply_current` | PMOS source/NMOS drain이 supply 레일인 소자 ID 합(실제 공급전류) | gmid_sizing_engine.py | 레일 튜플 인라인(4524) 중복. **배선 문제**: docstring이 `sum_current`는 스택 중복계상으로 2.82배 틀린 전력이라고 규명(4506-4512)했지만, 4개 회로 objective는 전부 `minimize power_uA`=`sum_current`(JSON 부록). 같은 개념 … |
| `_mirror_ratio_error_pairs` | ratio 쌍마다 (ΔVDS/V_A, 입력환산 V), ctx.derived 캐시 | gmid_sizing_engine.py(값) + 쌍/미러군은 circui… | **§12.6-5 확인**: `a, b = names[0], names[1]`(4578) -- 3소자 이상 그룹은 첫 쌍만 검사. V_A·gm_id를 `a` 쪽만 씀(4585-4587). 선언 ratio 쌍 18개 중 11개는 connectivity상 미러 아님(§12.3-5) -> S1 미러군(`l_s… |
| `input_referred_offset_pairs` | offset 쌍 중 전 소자 게이트가 ports input net인 쌍 | circuit_state_graph.py(S1 유도 사실) | 순수 구조 유도지만 `_load_full_topology_cached.__dict__["_cache"][path]` 사적 캐시에 직접 기록(4672,4691) -- 키가 경로 문자열(§12.3-7, C-d 위반: 파일 내용이 바뀌어도 적중). `ports` 선언은 파일럿·two_stage만 있음(grep… |
| `_metric_input_referred_offset` | 입력 offset 쌍 σ를 gm 가중 RSS로 입력환산(V) | gmid_sizing_engine.py | 국소: (1) gm 없는 소자를 리스트 컴프리헨션으로 **조용히 제외**하고 남은 것만 평균(4762,4767) -- 전부 없을 때만 실패 (2) 쌍 kind를 `names[0]`만 봄(4758) (3) 빌드 시 materialize한 `spec["_pairs"]`를 안 쓰고 다시 조회 -> 쌍 출처 2… |
| `_metric_rail_referenced_voltage` | 소스가 레일이라는 전제로 게이트 DC 레벨 = rail∓VGS(LUT 역산) | gmid_sizing_engine.py | 전제(source가 `rail`에 연결)를 검증하지 않음(4775-4776 자인) -- `_load_full_topology_cached`의 by_name으로 싸게 확인 가능. 선언 오류가 그럴듯한 전압으로 조용히 통과 |
| `_mna_solve_smallsignal` | 실수 소신호 MNA를 LAPACK으로 풀고 고립노드 진단 | gmid_sizing_engine.py | 국소: (1) 회로무관 solver인데 오류문에 `telescopic_class_ab`/`battery_vop1_side` 회로 전용 문구(5033,5039) -- 일반화 원칙 위반 (2) 스탬프가 4305-4311과 중복(DUP 상대) (3) 결과 캐시 없음 -- 같은 ctx에서 excite만 다른 풀… |
| `_psrr_diff_pair_tail` | `gm_tail/gds_tail` 자리표시자 PSRR | gmid_sizing_engine | docstring이 "order-of-magnitude 근사, 수천 배 차이 가능"(`:5245-5250`)이라 명시 → 제약으로 쓰이면 오판. `smallsignal_ratio_db`로 교체 검토 필요 |
| `_load_full_topology_cached` | topology 파싱+`load_topology` meta 보관, 경로별 캐시 | circuit_state_graph S1 | 키가 **경로 문자열**, 파일 변경 무효화·상한 없음(`:5384-5385`) = §12.3-7/§12.5.2 C-d 위반. 키를 topology 내용해시로 교체 |
| `_topology_meta_cached` | 위 캐시의 meta 접근자 | circuit_state_graph S1 | 동일 C-d 키 문제 |
| `_l_sharing_classes_cached` | L 동치류(층1) 경로별 캐시 | circuit_state_graph S1 | 별도 `__dict__` 캐시, 경로 키(C-d). S1 "L 동치류 개념당 정의 하나"로 흡수 |
| `_l_class_owners_cached` | L 동치류 주인(층2) 캐시 | circuit_state_graph S1 | 동일 |
| `_ideal_sources_cached` | ideal_sources 선언 접근자 | circuit_state_graph S1 | 접근자 5종(5446/5452/5466/5472/5413) 동형 반복 → S1 단일 객체 속성으로 통합 |
| `_diode_set_cached` | gate==drain 소자 집합 | circuit_state_graph S1 | §12.3-5 "diode 집합 16/1/20개 3정의" 중 connectivity 정의. S1 정본 후보로 승격 + C-d 키 교체 |
| `_device_roles_cached` | device_roles 접근자 | circuit_state_graph S1 | raw JSON의 device_roles(`:5407`) vs `_build_theta_evaluator`의 `meta["device_roles"]`(자동채움 포함 `:8524`) — **같은 이름 두 출처**(C-a) |
| `_matching_pairs_cached` | symmetry.matching_pairs 접근자(raw JSON) | circuit_state_graph S1 | `_evaluate`는 동시에 `meta["symmetry"]["matching_pairs"]`(`:8527`)를 따로 씀 → 두 출처(§12.3-5) |
| `_resolve_nulling_resistor_ohm` | Rz=1/gm(ref) 계산 + ctx 캐시 | gmid_sizing_engine | **스테일 캐시**: 키가 소자명뿐(`:5499-5504`). `revalidate_finger_override`가 `_dc_replace(ctx, sized=new_sized)`(`:11892`)로 새 ctx를 만들면 dataclasses.replace가 `_nulling_resistor_cache` … |
| `_full_circuit_response` | 여기 1개로 전체회로 MNA 풀이 | gmid_sizing_engine + S2 memo | 호출마다 스탬프 재조립+행렬 재분해(`:5563`,`:5574`). ratio metric 1개가 2회(`:5608`,`:5610`) → 같은 sized에 cmrr·psrr·gain_full로 동일 행렬 5회 분해. 행렬 1회 분해·RHS만 교체(S2 적재) |
| `FeedHandler` | feed 핸들러+`touches` 레코드 | gmid_sizing_engine | **`touches` 필드는 어디서도 읽히지 않음**(grep `.touches` 0건) → 삭제하거나 §12.5.4 "구조적 쓰기 집합"으로 실제 사용 |
| `_feed_root_ratio` | A: theta×Σref ID를 root seed | gmid_sizing_engine | `ctx.seed_currents` 원시 대입(`:5922`, C-a). 중첩 `_ref_id`가 `_feed_root_signed_sum`(`:5967-5971`)과 DUP |
| `_feed_root_const` | const: 절대전류 seed | gmid_sizing_engine | C-a 원시 대입만 |
| `_feed_root_signed_sum` | A_signed: 부호합 seed | gmid_sizing_engine | C-a, `_ref_id` DUP(5914). 음수 전류 검사는 하류(9247) |
| `_feed_diode_stack_target` | C: reference 복제×면적비 | gmid_sizing_engine | `ctx.sized[target] = entry` **통째 교체**(`:6036`)로 기존 필드(A엔진 ID 등) 소실 가능. ref의 gm_id/L을 그 시점 버전으로 복사(C-b) — 순서 검사기(6858)는 운영 미배선 |
| `_feed_gm_target_convention` | B: N·ωc·C → gm 역산 사이징 | gmid_sizing_engine | `vsb=feed.get("vsb",0.0)`(`:6066`) 기준 W·gds → reconcile(9207) 후 vsb만 바뀌고 W/gds 미갱신(§12.6-1 계열). `gm_id_bounds` 리터럴 `(2.0,30.0)`(`:6083`) |
| `_feed_settling_split` | t_slew/t_lln 분배를 ctx.derived에 | gmid_sizing_engine | C-a 원시 대입, 기본 키명 리터럴(`:6116`) |
| `_metric_stage_budget_finalize` | (gm_id,ID,L,vds,vsb)→W/gm/gds 확정 기록 | gmid_sizing_engine | **§12.6-1 원천 중 하나**: feed 기본 vsb 0.0 기준으로 W·gds 기록(`:6160-6162`), 입력 버전 미기록 → C-b 버전 필드 추가 |
| `_shared_current_root_grids` | 조인트 스캔 격자 생성 | gmid_sizing_engine | 격자 `[i*0.5 for i in range(4,61)]`(`:6283`)·상한 5000(`:6285`) 리터럴 — `:6632` 리터럴과 DUP. docstring은 `search_gm_id_for_role` 기본 격자 "재사용"이라 하나 실제로는 복사 |
| `_make_shared_current_scorer` | 후보 gm_id 조합 채점 클로저(ctx.sized 부수효과) | gmid_sizing_engine(블록) | `_metric_device_footprint` 제약마다 2회(`:6323-6324`), `except KeyError: continue`(`:6371`, "도달 안 함" 주석 = 근거 없는 skip), 후보마다 ctx 덮어씀(`:6363`) → 순수 점수화로 분리해야 S2 memo 가능 |
| `_feed_l_class` | l_class theta: 동치류 공통 L 기록 | gmid_sizing_engine | `_L_source` 출처 태그는 C-a 모범. setter 경유만 필요 |
| `InfeasibleSizingError` | 물리 불가 격자점 예외 + sized_snapshot | gmid_sizing_engine | 메시지 문자열 + 스냅샷뿐 → 소비자가 **문자열 파싱**(`:11027`, `:9585`). §12.5.4 "구조화된 실패(분류·막은 소자·margin)" 필드 추가 필요 |
| `resolve_stack_layout` | 레이아웃 1차 그룹 분할(override>declared vsid>candidates>legacy) | sizing_layout_convergence(또는 stick_diagr… | `load_topology()`가 내부에서 이미 `resolve_stack_layout`류 분석을 돈다고 기록(`:5393-5394`) → 빌드당 중복 실행. meta 결과 재사용 |
| `make_replica_feasibility_check` | C replica target의 W 실현성 콜백 | gmid_sizing_engine | `search_gm_id_for_role(..., 0.0, ...)` vsb 0 고정(`:7293`) — 헤드룸 이후 vsb와 다른 버전으로 판정. 버전 인자화 |
| `_HeadroomTopoEnv` | 헤드룸 토폴로지 레벨 상태 묶음 | circuit_state_graph S1 | S1 객체로 흡수(vparent union-find = "매칭 offset 그룹" 정의) |
| `_HeadroomEvalEnv` | 헤드룸 평가 레벨 상태 묶음 | circuit_state_graph S2 | 평가마다 새로 조립되는 정적 구조(vertical_groups 등)가 담김 → 정적 부분은 S1로 이동 |
| `_hr_fold_group_check` | fold_group 우회를 connectivity로 정당화 | circuit_state_graph S1 | 중첩 래퍼 `_thin_singleton_ideal_source_check`(`:7478`) 정의만 있고 미사용(추출 잔재) → 삭제 |
| `achievable_metric_bound` | 제약 하나를 목적함수로 바꿔 달성가능값 실측(multi-seed SLSQP) | optimizer(S3 유도 임계값) | `_ACHIEVABLE_BOUND_CACHE` 전역·무상한, 키가 약한 `spec_fingerprint`(`:8310`) → C-d. `except Exception`(`:8350`)은 notes 기록이라 조용하지 않음 |
| `resolve_constraint_references` | value_from_spec/constraint/achievable 참조 치환 | topology_authoring(선언 해석) | 지문 불일치를 `_RESOLVE_STALE_NOTES`에 기록만 하고 값 계속 사용(`:8424-8432`) = **§12.6-8**. C-d(불일치=없음)는 픽스처/정본 구분 결정 필요 |
| `_pick_split_target` | 지배적 splittable row 선택 | sizing_layout_convergence | 순수이나 **테스트·운영 실행 0회** — self-test 추가 필요(없으면 D) |
| `_score_floorplan` | floorplan 목표 미달 스칼라 | sizing_layout_convergence | 동일 |
| `diagnose_sizing_roles_gap` | theta 없는 회로 1회 평가 → gap 리포트 | topology_authoring | 예외 **메시지 부분문자열**로 분류(`:9585`,`:9604`) → 메시지 문구 변경 시 조용히 "other". 구조화 예외로 |
| `_metric_device_footprint` | metric 선언→읽는 소자 집합(or "ALL") | circuit_state_graph S1 | 순수이나 **결과 캐시 없음**(선언만 의존인데 scorer에서 후보 루프 밖 제약당 2회, feed 호출마다 재계산). "소자 참조" 정의가 `_collect_device_refs`(11826)와 둘(§12.3-5) |
| `repair_infeasible_baseline` | 실패 메시지의 소자명을 따라 theta를 bounds/격자로 이동 | optimizer | **`d in msg` 부분문자열 매칭**(`:11027`, §12.6-4: "M1"⊂"M11a"). `except Exception: return False, frozenset()`(`:11028`) 광범위·조용. L 후보 서브샘플 9 리터럴(`:11059`). 구조화 실패(InfeasibleSizin… |
| `revalidate_finger_override` | finger W 강제 후 gm_id 역산 + 전 metric 재검증 | sizing_layout_convergence | 매 호출 old metric 전부 재계산(`:11923`, 입력 불변 → S2 재사용). `_dc_replace` 얕은 복사로 ctx 캐시 3종 공유(`:11892`) → `_nulling_resistor_cache` 스테일(5481 행 참고) |
| `_blocked_euler_rows` | audit 체크명 `"1. euler["` 접두사 파싱 | sizing_layout_convergence | 문자열 계약(`:12031`) → 체크 객체에 구조화 필드 |
| `run_matching_safety_with_finger_growth` | 3c 실패에 핑거성장/완화 루프 | sizing_layout_convergence | 체크명 정규식 파싱(`:12365`), 루프 안 `import re`(`:12360`) |
| `run_topology_pipeline_with_finger_fixup` | euler-blocked row 핑거조정/그룹분할 루프 | sizing_layout_convergence | `load_topology` 재호출(`:12502`) + 라운드마다 `run_topology_pipeline`이 경로로 재로드(`:12510`) → S1 재사용 |

### stick_diagram.py (16)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `Transistor` | connectivity+finger 필드를 담는 소자 레코드 | stick_diagram 유지(S1은 별도 엣지 타입) | R1(레이아웃 필드 stack_id/n_fingers가 connectivity와 한 레코드) |
| `_import_analog_grammar` | analog-grammar sys.path 주입+import | topology_authoring | R1(sys.path 부작용을 패키지 import로) |
| `find_stacked_matching_candidates` | 매칭쌍 위 적층쌍 재귀 상속 | circuit_state_graph | R1(S1 stacked 관계로 흡수) |
| `_propose_L_roles` | L_role(mirror/bias_replica) 제안 | topology_authoring | R1(docstring/라벨 의미 갱신) |
| `check_symmetry_dispositions` | 후보 대비 disposition 누락 게이트 | topology_authoring |  |
| `find_structural_symmetry_candidates` | seed net 대응 고정점 전파(automorphism) | circuit_state_graph(대칭 관계 유도) | docstring SD:2858-2860: `propagate_topology_forced_currents`와 같은 전파 스타일 |
| `geometry_colocation_union` | matching base+적층 상속 geometry 그룹 | stick_diagram |  |
| `audit_vertical_stack_id_vs_kcl` | 선언 vsid vs KCL 그룹 대조표 | topology_authoring(→S1 검증) |  |
| `find_authoritative_sizing_devices` | role 없이도 안전한 소자 집합 | topology_authoring | R1(정의 이중화 해소) |
| `find_unreviewed_device_roles` | 자동채움 중 review 필요 필드 | circuit_state_graph(status) |  |
| `find_unreviewed_matching_pairs` | review 필요 매칭쌍 | circuit_state_graph(status) |  |
| `require_device_roles_reviewed` | 미검토 자동채움이면 사이징 거부 | circuit_state_graph(status 게이트) |  |
| `run_full_circuit_audit` | devices dict 기반 전체회로 4단계 감사 | stick_diagram 또는 instance_report_builder | R1(입력 `devices` 튜플 dict가 topology와 별도 정본 -> S1에서 읽게) |
| `_failing_required_pairs` | AuditCheck name 문자열에서 실패 쌍 파싱 | stick_diagram | R1(구조화 필드 부재로 정규식 파싱) |
| `_kcl_branch_map` | kcl_series_union을 소자별 branch로 펼침 | stick_diagram | R1(S1 KCL 관계 사용으로) |
| `run_topology_pipeline` | load->override->finger 검사->stack->euler->box->audit->floorplan->coverage | stick_diagram | R1(`load_topology` 재호출 SD:8781 -> 로드 결과 주입) |

### 기타 모듈 (16)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `nmcnr_3stage_topology` | NMCNR Eq6~11 + `topology_fn.dominant_pole_check` 부착 | 〃 | R1 -- 팩토리마다 4000점 스윕 진단 즉시 계산(`:117`), lru_cache(`:248`)로만 완화 |
| `nmcnr_check_dominant_pole_approximation` | Eq10/11 우세극 근사 성립 여부 | 〃 | R1 -- valid 문턱(0.5~2.0배, 15도)을 docstring이 "임의값"이라 명시(`:306-308`) -- "상수 임의 금지" 원칙 위반 소지 |
| `ngcc_3stage_topology` | NGCC Eq8.a/8.b, `mu_ratio` 기본 3.9775(논문 역산 `:356`) | 〃 | R1 -- 논문 역산 기본값 |
| `current_reuse_telescopic_topology` | Xie&Chen Eq2-6, β/Cc 고정점, `exposed_params`/`stage_fT_targets` | 〃 | R1 -- 클로저 속성 `exposed_params`를 호출마다 갱신(`:496`) = 숨은 가변 상태, §12.5.2 C-a(단일 writer·출처)와 충돌 |
| `  └ topology_fn` | [gmp,gmn,gmp2,gmn2] + Cc 유도(`:492`) | 〃 | 〃 |
| `build_topology_device_table` | topology.json -> matching_pairs union-find 소자 표 | `instance_report_builder.py` | R1 (인라인 union-find) |
| `assemble_report_data` | topology+instance.json+audit+narrative -> REPORT dict | 〃 | R1 -- 경로로 instance.json 재로드, 지문(§12.5.2 C-d) 없음 |
| `render_html_report` | REPORT -> self-contained HTML(순수) | `instance_report_builder.render_design_r… | R1 -- 계획이 "신규"라 적은 함수가 이름만 다르게 이미 존재. §8.5가 요구한 헤드룸 검증/gain 배분 대조표/CMRR·PSRR·mismatch 요약 섹션은 없음(sizing은 instance.json 필드 덤프 `:228-232`) |
| `_theta_evidence_for_pair` | 쌍이 theta feed A/A_signed root 또는 C target/reference로 강제되는지 | 〃 | R1 -- A/A_signed/C만 인정. 엔진 feed는 B/settling_split/metric_stage_budget/`gm_id_match_vgs_of` 등 추가 존재(self-test `sizing_recipe.py:13902-13940`, `vgs_alias_map:1804`) -> 근거 누… |
| `audit_topology` | current_forced 양방향 대조 | 〃 | 〃 |
| `_run_combo` | 1조합 실행+체크포인트 | 〃 | R1 -- 미사용 인자 `iL`; 체크포인트 키가 파일명(L값·VS 인덱스)뿐, PDK/모델/격자(VGS·VDS 49점) 변경 시 스테일 재사용(§12.5.2 C-d 부재) |
| `_spec_two_stage_ota` | 정본 spec dict | `topology_authoring.py`(-> json) | R1 -- 코드 dict. §8.3은 `sizing_spec.json`을 `library/`에 저장 요구 |
| `_spec_current_reuse_telescopic_ota` | 〃 | 〃 | R1 + 죽은 값 `Cc`(`:191`, A-1 참고) |
| `_spec_folded_cascode` | 〃 | 〃 | 〃 |
| `_spec_nmcnr_amplifier` | 〃 | 〃 | 〃 |
| `SPECS` | key -> topology/spec_fn/search 설정 | 〃 | 〃 |

## 5. R2 -- §12 구조로 대체 예정 (새 호출부를 늘리지 않는다)

### sizing_recipe.py (19)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `optimize_multistage` | topology_fn(prev_cggs)→gms 고정점 반복 + 스테이지/공유 gm_id 그룹/VDS-KVL 그룹 사이징 + 한계순환 평균 | gmid_sizing_engine.py(순환 루프는 §12.5.2 C-c… | (1) **계획과 다름**: gm 방향 반전이 미구현(1009-1012, 여전히 topology_fn→gm). (2) **C-c 위반**: cgg↔gm 순환을 암묵 반복으로 풀고, 비수렴이면 `converged=False` 결과를 **그대로 반환**(1393), 한계순환이면 주기 평균으로 대체값을 만든다… |
| `stack_kvl_vgs_limit` | VGS(name)이 다른 소자 VDS로 소비될 때 스택 KVL로 VGS 상한 = const/k 유도 | circuit_state_graph.py(S1 엣지 `vds_eq_vgs… | (1) 결과가 **호출 시점에 `ctx.sized`에 무엇이 이미 채워졌는지에 달린다**: 참조/멤버 vds 미확정이면 그 소비자를 건너뛰고(1957-1960, 1973), 전부 건너뛰면 `None`=제약 없음 -> §12.2 "실행 순서 암묵 계약"(T2) 그 자체. (2) vds↔VGS 순환(§12.… |
| `resolve_feed_vds` | theta feed의 소자 vds: ctx.sized 선점값 → `_feed_vds_fallback` | circuit_state_graph.py(S2 값 저장소의 출처·버전 조… | `ctx.sized[name]["vds"]`가 있으면 **누가 언제 썼는지 확인 없이** 재사용(2147-2149). 계획이 지목한 "먼저 쓴 쪽이 이김" 구조가 코드에 그대로 남음 = §12.5.2 **C-a(단일 writer·출처)** 부재. writer 티어 권한표로 대체해야 함 |
| `SizingContext` | 평가 1회용 공유 상태(sized/spec/derived/seed_currents/mirror_ratios/topology_path/kind_of + 평가 내 캐시 3종) | circuit_state_graph.py(S2 값 저장소: 필드마다 `{… | §12.2 근본원인 "값의 상태 모델 부재"가 이 클래스다: `sized`는 원시 dict라 필드마다 정체/출처/버전/수명이 없고(2988), 쓰기가 전부 원시 대입(예 `_evaluate:8950-8951, 9018-9019`) -> **C-a/C-b 위반**. 평가마다 새 ctx라(§12.3-1 `:… |
| `_gm_id_already_authoritative` | `_L_source`/`_gm_id_source` 태그로 gm_id 덮어쓰기 금지 판정 | circuit_state_graph.py | §12.5.2 C-a "필드×writer 티어 권한표"의 임시판. 권위가 두 문자열 필드로 갈라져 있고(3272-3275 주석 자인), `apply_diode_self_consistent_gm_id` 3804는 이 함수를 안 쓰고 `_L_source`만 본다 -> 판정 정의 2벌 |
| `solve_stacked_diode_pair` | 적층 diode 2개 (v_up,v_lo) 격자 동시 스캔, 아래 vsb=vsb_up+v_up 결합 | circuit_state_graph.py(C-c 순환 블록) | §12.3-8 순환 "vsb↔vds(적층 diode)"를 **2소자 한정 격자 스캔**으로 우회 -- C-c 명시적 고정점 블록으로 대체 대상. 캐시 없음(O(N²) LUT 조회, 매 평가). **결함**: `constrain_up=False`에서 LUT 조회 실패 시 `idu_up=1.0`(3707)으… |
| `materialize_input_offset_pairs` | 빌드 시 metric 선언 dict에 `_pairs`/`devices`를 제자리 기입 | circuit_state_graph.py(S1 유도 사실, status=… | 선언(사용자 입력)과 유도값을 같은 dict에 섞어 씀(4721-4722) -- C-a "declared/derived 구분·출처" 부재의 전형. 소비자 `_metric_device_footprint` 10137-10146, `make_matching_feasibility_check`가 선언을 읽는 척 … |
| `_run_shared_current_joint_scan` | 공유전류 그룹 K-D 전수 스캔 + 승자 재적용 | gmid_sizing_engine 블록 + circuit_state_gr… | **warm 평가의 66%**(§12.3-6). 입력 동일해도 매 평가 최대 57²=3249조합×finalize×compute_metric 재실행. §12.5.3 키(그룹 L·vds·vsb·gm_total·고정 gm_id)로 S2 적재 |
| `_refine_shared_current_joint_scan_for_full_circuit_constraints` | 전역(ALL) 제약 위반 시 로컬 상위 top_n 재검사 | gmid_sizing_engine 블록 + S2 | `_all_global_satisfied`(`:6468`) 후 `_evaluate`가 전 metric 재계산(`:9468`) = **이중계산**(§12.4). 위반 시 1단계와 동일 전수 스캔 재실행(`:6479-6483` ≡ `:6415-6421`, DUP). top_n=20 리터럴 |
| `_feed_metric_stage_budget` | theta=L로 소자 L/gm_id/W 확정 + 조인트 스캔 트리거 | gmid_sizing_engine(블록 분할) | vds defer(`:6769-6785`) = "헤드룸이 나중에 채움" **실행순서 암묵계약**(§12.2, C-c/T2). joint-scan footprint를 feed 호출마다 재계산(`:6760-6767`). 순서 오류를 `ValueError`(`:6609`,`:6671`) → SLSQP 크래시 … |
| `_HeadroomDependencyNotReady` | 헤드룸 worklist "나중에 재시도" 신호 | circuit_state_graph(C-c 고정점) | 순환을 "진전 카운트"로 푸는 실행순서 우회(§12.3-8). C-c SCC 블록 반복으로 대체 |
| `_hr_resolve_vertical_group` | vsid 그룹 1개 헤드룸 해석(pre-pass/sibling/same_as/적층 diode 연립/diode 창/singleton 우회/allocate/vsb 전파) | circuit_state_graph C-c 순환 블록 | 500줄. **광범위 except 2곳** `:7852`,`:8006`(§12.6-6과 동종, 목록 누락) → 노드전압 실패 시 폴백으로 조용히 진행. 쌍/미러멤버마다 `propagate_node_voltages` 재호출(`:7849`,`:8004`, §12.3-4 평가당 19회의 원천). vsb `se… |
| `spec_fingerprint` | 해상도 키 7개 문자열 지문 | circuit_state_graph S0 | LUT·vdd·제약값·topology·엔진 제외(`:8146-8148`), repr 기반 → §12.5.1 S0(전 입력 내용해시+유도규칙 코드 해시)로 대체 |
| `_build_theta_evaluator` | theta-무관 셋업 + `_evaluate` 클로저 반환 | gmid_sizing_engine + circuit_state_graph… | 셋업: **광범위 except `(KeyError, ValueError): pass`**(`:8511`, §12.6-6 — l_class theta 조용히 0개), `load_topology` 이중(`:8493` + `_load_full_topology_cached` 내부 `:5386`, §12.4), … |
| `optimize_full_circuit_budget` | 단일 진입점: θ 탐색(grid/slsqp/block) + finger/euler/matching/row_split 레이아웃 | sizing_layout_convergence(레이아웃·row_split… | θ*를 반환만, 저장 없음(§12.3-1). grid 분기 위반 포맷/실현성 판정이 SLSQP·warm-start와 4중 DUP(`:9773`,`:9785`, `:10906`, `:11570`, `:11619`). 에러문 "'grid' 또는 'slsqp'만 지원"(`:9797`)이 block 분기 존재와… |
| `derive_theta_dependency_graph` | theta를 dead/isolated/coupled/fixed/ambiguous로 분류(FD 5%) | optimizer | **한 기준점 5% 섭동 분류로 차원 동결**(§12.3-10, §12.5.4 금지). 임계 `0.5dB`/`1%` 리터럴(`:10390-10392`). theta마다 같은 baseline을 `evaluate` 재호출(`:10355`, 루프 안 불변식) |
| `search_stage_budget_L_warm_start` | L theta 웜스타트(LUT 고속경로 + evaluate 조인트 스캔) | optimizer | 매 후보 full `evaluate`(`:10903`), 실패 미캐시(`except: continue`), 위반합 공식 DUP. `window_around_reference`(`:10890-10896`)는 §12.4가 기각한 "지난 해±창" — 호출자는 block_coordinate(미사용)뿐. 중첩 `… |
| `presolve_warm_start` | 투표+복구+L 스캔+의존그래프로 x0 조립 | optimizer | 결정론 x0 하나(§12.3-10), 사전평가·아카이브 없음. x0를 `evaluate` 최대 3회(`:11303`,`:11315` + slsqp `:11562`) 중복 평가 |
| `_optimize_theta_slsqp` | SLSQP multi-start(정규화, 페널티, 재검증) | optimizer | **`_eval_cache`에 성공만 저장**(`:11497-11503`) → 예외 점 매번 재평가(§12.3-2: 811회 중 784 중복). 상수 페널티 1e6(`:11491`)로 경사 0. 호출 수명 캐시(§12.3-1), θ* 미기록. 빠른 수정(R1급): 실패도 캐시 |

### stick_diagram.py (12)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `trace_vdd_to_gnd_branches` | kind별 전류방향 고정 branch 골격(하향) | circuit_state_graph(S1 방향 엣지/뷰) | 전류방향 규약 3곳: SD:1216-1224, `_kcl_terminal_sign` SD:3580, SR `_metric_kcl_residual` SR:4469-4472 |
| `trace_gnd_to_vdd_branches` | 상향 branch 골격 | circuit_state_graph | 위와 쌍 |
| `suggest_vertical_stack_composites` | branch+idiom으로 vsid composite 제안 | topology_authoring |  |
| `find_verified_differential_and_mirror_relations` | branch 구조 일치쌍 안의 diff/mirror 관계 | topology_authoring |  |
| `_propose_vertical_stack_ids` | vsid 후보 이름 생성 | topology_authoring |  |
| `_propose_gm_id_roles` | gm_id_role(balanced/matching) 제안 | topology_authoring | tail 판정(shared_source를 drain으로, SD:2238-2242)이 SR `gain_stage_tails`와 개념 중복 |
| `_propose_headroom_roles` | headroom_role 제안(37/37 규칙) | topology_authoring | diode 판단이 netclass role 기반(SD:2484) -> SR `is_diode_connected`(gate==drain, SR:3294)와 다른 정의 |
| `refine_differential_and_mirror_relations` | diffpair gate net 자동 승격 고정점 반복 | topology_authoring | `load_topology` 호출마다 재실행(아래 `propose_device_roles_gap_fill` 비고) |
| `propagate_topology_forced_currents` | stack_id+미러비 전류 고정점 전파(A엔진) | circuit_state_graph(엣지) + 엔진(값) | 전류 동일 관계를 레이아웃 필드 `stack_id`에서 읽음 SD:3044-3048(본문 시작부) |
| `propose_vertical_stack_id_gap_fill` | union 그룹 내 vsid 상속 제안 | topology_authoring |  |
| `propose_device_roles_gap_fill` | matching_pairs/device_roles 3단 소스 제안 | topology_authoring | 706줄. `load_topology`마다 analog-grammar 전체 재실행. SR 캐시(SR:5386,5414)가 있으나 `run_topology_pipeline` SD:8781, `_build_theta_evaluator` SR:8493, fixup SR:12502는 캐시 없이 재호출(C10 재… |
| `load_topology` | JSON+linked 파일 병합 로드 **+ vsid/device_roles/matching 자동채움** | 파싱: circuit_state_graph S0/S1 로더 / 자동채움:… | R2(파싱 R0 + 구조 유도 분리) |

### 기타 모듈 (1)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `run` | optimize_full_circuit_budget -> audit -> instance.json -> report.html | `gmid_design_pipeline.run_gmid_design_pi… | R2 -- 3단계 분리 없음, θ* print만(`:461`, §12.3 표 1행 지적), `except Exception`(`:507`)으로 실패도 exit 0 |

## 6. DUP -- §2 정본으로 통합

### sizing_recipe.py (11)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `size_transistor` | ID=gm/gm_id, W=L·ID/IDu | gmid_sizing_engine.py | 같은 식 `W=L·ID/IDu`를 엔진이 인라인으로 다시 씀: `find_optimal_sizing:941`, `feasible_gm_ids:1756`, `search_gm_id_for_role:2234`, `feasible_L_window:2746`. 계획은 "재사용"이라 했지만 엔진은 이 함수를 안 … |
| `_multilinear_interp_point_multi` | 단일 좌표에서 여러 배열을 한 번에 보간 | gmid_sizing_engine.py | 축별 bisect/frac/corner-weight 코드가 `_multilinear_interp`(217-246)와 복붙. 공통 `(idx_lo, frac)` 헬퍼 하나로 합칠 것 |
| `true_current_mirror_groups` | 같은 (kind, gate net, source net) 소자 그룹(게이트가 레일이면 제외) | circuit_state_graph.py(S1 "개념당 정의 하나"의 미… | 같은 개념이 다른 정의로 또 있다: `stick_diagram.find_matching_candidates`(972, 1005-1006 `(kind, gate, source)` current_mirror 그룹핑), `_mirror_ratio_error_pairs`(4551, connectivity가 아니… |
| `_folded_cascode_rout` | folded-cascode Rout_p/Rout_n/병렬 폐형식 | gmid_sizing_engine.py | 소비자 둘이 DUP라 종속. ro_fold 계산(3054)이 `_nmcnr_stage1_rout`(3126)와 같은 식 복제 |
| `_metric_folded_cascode_gain_db` | gm1·(Rout_p‖Rout_n) dB | gmid_sizing_engine.py | 같은 개념을 회로무관 MNA `_metric_smallsignal_gain_db`(5615)가 계산(파일럿·two_stage는 이미 그쪽). docstring 3066-3068: sympy/SPICE 검증 안 됨. 운영 중이므로 삭제 전 JSON 타입 이전+4회로 측정 필요 |
| `_metric_folded_cascode_pm_deg` | 2-pole 근사 PM, C_fold=Cgg 합 | gmid_sizing_engine.py | `_metric_parasitic_pm_deg`(4329, L2 실제 주파수응답)와 같은 개념. 접합용량·Y-branch 극 무시(3084-3091) |
| `full_circuit_response_at_omega` | (G+jωC)v=b 복소 MNA 풀이 | gmid_sizing_engine.py | 트랜지스터 스탬프 6줄(4305-4311)이 `_mna_solve_smallsignal`(4970) 5016-5022와 **동일**. ω=0이면 DC 해와 같음 -> 복소 solver 하나로 합칠 것. 이쪽엔 고립노드 진단(5029-5034)이 없음 |
| `_cmrr_diff_pair_tail` | CMRR ≈ (ro_tail/2+1/gm)·gm 1차 근사 | gmid_sizing_engine.py | 같은 개념을 회로무관 전체회로 MNA `_metric_smallsignal_ratio_db`(5586)가 계산(파일럿은 이미 전환, JSON 주석 1873). 운영 중이라 삭제 전 JSON 이전+측정 필요 |
| `_theta_device_map` | feed dict 전체를 훑어 문자열 leaf 수집 | (정본 `_theta_feed_footprint` 10174 / walk… | 소자명 아닌 문자열(type, metric 이름)도 수집 후 교집합으로 거름. 두 함수와 개념 중복 |
| `_collect_device_refs` | 중첩 spec에서 알려진 소자명 수집 | (`_theta_device_map` 10933) | 판정 로직에선 더 이상 안 씀(`:11894-11921` 사유) — 진단 필드 전용 |
| `_fixup_euler_blocked_rows` | repair 후 잔여 euler-blocked row 수리(성장→분할/컴포넌트 분리) | (`run_topology_pipeline_with_finger_fixu… | docstring 스스로 "정확히 같은 전략"(`:12143-12146`). rows 표현용·topology_path용 두 벌 |

### stick_diagram.py (7)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `find_matching_candidates` | mirror/diff_pair 후보 탐지(net-only 또는 idiom 경로) | circuit_state_graph(S1 matching 엣지 정의 1개… | mirror 정의 3개: net-only (kind,gate) SD:1024-1031 / idiom (kind,bias,rail) SD:1041 / SR `true_current_mirror_groups` (kind,gate,source)+레일게이트 제외 SR:2358-2382. diff_pair는 `_… |
| `find_differential_pair_candidates` | inputs 선언 없이 diffpair 후보(shared_source) | circuit_state_graph | diffpair/tail 정의 다중: 여기 / `find_matching_candidates` diff_pair SD:1033-1046 / SR `gain_stage_tails`(stage source net을 drain으로 갖는 tail) SR:2434-2470 / SR `input_referred_o… |
| `_diff_pair_layer1_groups` | net-only diff_pair 판정 재사용 | circuit_state_graph | docstring SD:1787-1789가 `find_matching_candidates` diff_pair와 같은 판정이라 명시 |
| `kcl_series_union` | 2단자 내부넷+matching_pairs union-find KCL 그룹 | circuit_state_graph | 같은 edge를 `_kcl_and_matching_edges`(SD:3298, docstring "단일 정의로 분리")가 재구성하지만 이 함수 본문 SD:3188-3212는 그것을 쓰지 않고 독자 구현 |
| `_kcl_and_matching_edges` | KCL/matching edge 목록(원인 보존) | circuit_state_graph | 상대: `kcl_series_union` |
| `_kcl_terminal_sign` | PMOS/NMOS 단자 KCL 부호 | circuit_state_graph | 운영 0(D). SR `_metric_kcl_residual` SR:4469-4472이 같은 규약 독자 구현 |
| `_quantize_to_grid` | 길이 grid 스냅 | stick_diagram(공용 유틸로 추출 가능) | SR `quantize_L` SR:799-815와 동일 공식; docstring SD:6059-6063이 순환 import 회피용 의도적 사본이라 명시 |

### 기타 모듈 (1)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `  └ _find` | union-find | 공통 유틸 | DUP 성격 -- union-find가 `sizing_recipe.py:3427`, `:10819`, `stick_diagram.py:3170`, `:5092`에도 각자 구현 |

## 7. D -- 운영 경로 호출 0 (배선/삭제 결정 필요)

### sizing_recipe.py (27)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `GmIdLUT.junction_cap` | Jespers jctCap 1차 근사 CJD(원문 예시 unit-cap 기본값 CJ=1e-15 등) | gmid_sizing_engine.py(배선 시) 또는 삭제 | 기본값이 원문 예시 상수(77, 80-81). 운영에 배선하려면 PDK 값에서 읽어야 함. 삭제/배선은 사용자 판단 필요 |
| `gm_from_fT` | gm=2π·fT·C | gmid_sizing_engine.py | 1줄 순수함수, 데모·단일소자 경로용. 삭제 이득 없음 |
| `converge_with_parasitics` | 기생 CJD 반복 수렴(발산하면 ValueError) | gmid_sizing_engine.py 또는 tests 데모 | 발산 판정 `20*C_external`(143) 매직넘버. 운영 경로에서 기생 반영은 `optimize_multistage`의 cgg 반복이 대신 함. 배선 또는 삭제는 사용자 승인 필요 |
| `slew_rate` | ID/C | 삭제 후보 | 완전 dead. slew metric이 필요하면 `_METRICS_REGISTRY`에 metric으로 넣을 것 |
| `SemiEmpiricalGmIdLUT.fT` | fT=gm/(2πCgg) | 삭제 후보(또는 준정적 검증에 배선) | `find_optimal_sizing`의 준정적 검증은 `check_quasi_static`+cgg로 따로 계산하므로 이 메서드는 안 쓰임 |
| `_invq_newton` | EKV q 뉴턴 역산 | tests/ 픽스처(삭제 아님) | toy 전용 |
| `build_toy_lut` | EKV 합성 4D LUT | tests/ 픽스처(§8.8 test 분리 시 이관) | VA=5V/um, Cox 5e-15 등 toy 상수(1428,1432) -- 픽스처로만 쓸 것 |
| `RegressionVerdict` | 회귀 판정 dataclass | tests/(회귀 러너와 함께 이관, 삭제 아님) |  |
| `_run_optimize_multistage_case` | reference JSON case로 optimize_multistage 실행 / engine 문자열 디스패치 | tests/ | 엔진 등록은 optimize_multistage 하나뿐(1524) |
| `run_regression_case` | 공정별 골든 JSON 로드 → 실행 → 상대오차 대조 | tests/(골든 회귀는 가치 있음 -- 이관) | `W_ref=5e-6` 하드코딩(1561,1563) -- LUT npz 메타에서 읽어야 함(C-d/S0 지문 대상). `except (ValueError, KeyError)`를 실패 verdict로 바꾸는 건 테스트 러너라 허용 |
| `solve_diode_stack_current` | 직렬 diode 스택 VGS합=target이 되는 전류 로그축 이분탐색 | 삭제 후보 | 적층 diode 문제의 운영 해법은 `solve_stacked_diode_pair`(3659, B25, 호출 7859)로 대체됨. 개념 중복 -- 삭제는 사용자 승인 필요 |
| `estimate_area_budget` | n_fingers × pitch로 A_1D, packing_density 표본이 있으면 A_1D/density, 없으면 콜드스타트 블렌딩 | sizing_layout_convergence.py(배선 시) | **공식 결함**: 콜드스타트 `(1-α)·A_1D + α·(A_1D/α)` = `(2-α)·A_1D`(2954-2955) -- α가 서로 상쇄돼 블렌딩이 아니다(α=0.65면 1.35·A_1D). self-test(13882-13884)가 **같은 식을 다시 써서** 비교하므로 잡지 못함(동어반복 테스… |
| `signal_path_nodes` | gate/source->drain 방향 그래프에서 excite∩sense 도달 내부노드 | (삭제 후보) | 4354-4356 docstring이 L2에서 "원천적으로 필요 없어짐"이라 명시. §12.4가 소비자라 적은 것이 오류임을 재확인. 방향 규칙이 단일 DAG가 안 됨(§12.3-9) -> S1v 재활용 가치 낮음 |
| `node_pole_estimate` | 노드별 G/C 1차 pole 추정 | (삭제 후보) | 4343-4346: L1 값(34.2도) 무효라고 자인. **§12.6-6 광범위 except 4138 확인**: `except (KeyError, ValueError): pass`로 Cgg 누락을 조용히 버림 -- 운영 미호출이라 영향은 probe 한정 |
| `_cmrr_telescopic_class_ab` | current-reuse 1단 open-loop CMRR 폐형식 | (삭제 후보) | 파일럿이 `smallsignal_ratio_db`로 교체(JSON 1871,1873). 참조는 self-test와 `workspaces/.../spice/stage1_cmrr_*` 유도 스크립트뿐 |
| `_cmfb_amp_gain_diode_load` | CMFB 에러앰프 A_c 정확 폐형식 | (삭제 후보) | self-test + `diagnose_cmrr_cmfb.py`(workspaces)에서만 참조 |
| `_load_telescopic_topology_cached` | current_reuse topology를 **하드코딩 경로**로 로드·캐시 | 삭제 후보 | 경로 하드코딩 `:5054-5055`(일반화 원칙 위반). 기능은 `_load_full_topology_cached`(5379)와 DUP. `__dict__` 캐시 무효화 없음 `:5051` |
| `_telescopic_class_ab_open_loop_response` | 31소자 부분망 소신호 MNA로 (Vop1,Vom1) | 삭제 후보 | `_full_circuit_response`(5543)가 전체회로로 일반화·대체(`:5588-5591` docstring 스스로 "대체"라 명시). DUP |
| `_telescopic_open_loop_device_names` | 31소자망 소자명 열거 | 삭제 후보 | 위 체인 전용 |
| `_telescopic_class_ab_open_loop_gains` | Adm/Acm/Ann/H 4여기 풀이 + ctx 캐시 | 삭제 후보 | 캐시 키에 gm/gds 스냅샷 포함(`:5152-5153`, 내용기반 — 설계는 모범). 그러나 소비자 없음 |
| `_cmrr_telescopic_class_ab_cmfb` | telescopic CMFB CMRR(부분망+폐형식 G2/A_c) | 삭제 후보 | 대체재 `_metric_smallsignal_ratio_db`(5586)가 current_reuse 정본. DUP |
| `_psrr_telescopic_class_ab` | telescopic 1단 open-loop PSRR 폐형식 | 삭제 후보 | `_cmrr_telescopic_class_ab`(4837)와 계산 복제를 docstring이 인정(`:5276-5278`). DUP |
| `_psrr_telescopic_class_ab_cmfb` | telescopic CMFB PSRR | 삭제 후보 | G2/A_c/T 블록 `:5334-5343` = `:5221-5233` 복제(DUP `_cmrr_telescopic_class_ab_cmfb`) |
| `lut_conditions_from_npz` | LUT npz의 corner/temp 기록 여부 반환 | circuit_state_graph S0(LUT 생성메타 해시) | D(배선 필요) |
| `validate_theta_declaration_order` | theta 선언순서=실행순서 계약 검사 | topology_authoring | D(배선 필요) |
| `load_derived_bounds` | 사이드카 JSON 읽기 | optimizer S3(흡수) 또는 삭제 | 유도값 저장 경로가 사이드카 vs topology.json `_derived`(`resolve_constraint_references` `:8423`) 두 갈래 — 엔진은 후자만 읽음 |
| `_optimize_theta_slsqp_block_coordinate` | L 격자 ↔ SLSQP 블록 좌표 교대 | 삭제 후보(또는 optimizer로 이관 후 실측) | `window_around_reference` 경로의 유일한 사용자 → 함께 정리 |

### stick_diagram.py (19)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `MirrorSymmetryVerdict` | 대칭 판정 결과 | stick_diagram(삭제 후보) | `check_mirror_symmetry` 전용 |
| `check_mirror_symmetry` | finger 순서 좌우 대칭 판정 | stick_diagram 유지 또는 test util | 운영 호출 0 |
| `find_interleaved_symmetric_splits` | 홀수 finger 쌍 교차 대칭 분할 해 | test util | SD 밖 grep 0건 |
| `find_idiom_matches` | analog-grammar Stage1~3 원본 Match | topology_authoring |  |
| `find_differential_and_mirror_forks` | 양방향 fork 분류 | 삭제 후보 | `find_verified_...` docstring SD:1802-1815가 이 접근의 한계와 대체를 기술 |
| `suggest_headroom_stack_groups` | composite를 헤드룸 그룹으로 제안 | 삭제 후보 | AST 호출자 0, 저장소 grep 0 |
| `MultiLeafHubParityVerdict` | 결과 레코드 | test util |  |
| `check_multi_leaf_hub_parity` | hub-leaf 오일러 가능성 공식 스크리닝 | test util |  |
| `DiodeStackMember` | 결과 레코드 | - |  |
| `DiodeStack` | 결과 레코드 | - |  |
| `find_diode_stacks` | 스택 내 gate가 (자기/이웃) drain인 소자 | circuit_state_graph(diode 정의 1개로 통합) | **DUP**: 계획 §12.3 표 5행 "diode 집합 16/1/20". 정의 4곳: 여기(이웃-diode, stack_id 필요 SD:3100-3112) / SR `is_diode_connected` SR:3294 / SR `_diode_set_cached` SR:5452 / SD 층위1 `t.ga… |
| `audit_theta_root_direction` | theta A feed의 캐스코드 방향 역전 탐지 | topology_authoring(배선 여부 승인 필요) |  |
| `propose_theta_kcl_gap_fill` | theta 전류 구조 제안(고정점 규칙) | topology_authoring(배선 승인 필요) | 346줄, 운영 호출 0 |
| `apply_theta_kcl_gap_fill` | 위 제안을 topology.json에 기록 | topology_authoring | 파일 쓰기 도구 |
| `apply_device_roles_gap_fill` | 제안을 topology.json에 영구 기록 | topology_authoring |  |
| `audit_vertical_stack_id_euler_feasibility` | 선언 vsid 그룹의 오일러 실현성 | stick_diagram(배선 여부 승인 필요) |  |
| `find_euler_repair_options` | unresolved_row 복구 선택지 진단 | stick_diagram(배선 승인 필요) | 운영 0 |
| `SharedFingerWCandidate` | 공통 finger_w 탐색(Case B) | stick_diagram 유지 또는 삭제 |  |
| `render_stick_diagram` | PDF 형식 텍스트 출력 | test fixture/유틸 |  |

### 기타 모듈 (2)

| 함수 | 책임 | 이관 목적지 | 비고 |
|---|---|---|---|
| `render_report` | 텍스트 리포트 + has_violation | §8.3 게이트 배선 후보 | D(파이프라인 미배선) |
| `derived_spec` | override + `_spec_source` 기록, why 필수 | 〃 | D(만들고 미배선) |

