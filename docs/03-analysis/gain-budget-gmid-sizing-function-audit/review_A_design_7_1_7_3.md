# 검토 A -- 원설계 재평가: 이력 §1.4 / §6 / §7.1 / §7.2 / §7.3 (gain-budget-first 관점)

- 기준: HEAD 5578aa3(2026-09-14), 읽기 전용. 약어 H=`docs/01-plan/features/gain-budget-gmid-sizing.history.md`, P=`docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, SR=`skills/analog-gmid-design/assets/sizing_recipe.py`, SD=`.../stick_diagram.py`, REG=`docs/03-analysis/gain-budget-gmid-sizing.function-registry.md`, A6=`docs/03-analysis/gain-budget-gmid-sizing-function-audit/agent6_plan_vs_code.md`, CTX=`.ai/context.md`, TOPO=`assets/library/<회로>.topology.json`.
- "여전히 필요?" 값: **유지**(형태 그대로 필요) / **변형**(형태를 바꿔 필요) / **폐기**(불필요).
- 이 문서에서 직접 실측한 것(추측 아님): 4개 topology의 `device_roles`/`sizing_roles`/`compensation` 필드 집계, netlist 노드 공유 여부(`vds_match_vgs_of` 3건, `same_as_device` 4건, `budget_reference_device` 9건), `_evaluate` 안 호출 순서(SR 줄번호), 스키마 이름 grep.

## 0. 실측 사실 (이 문서의 근거)

### 0.1 `_evaluate` 실제 순서 (SR)
`apply_theta_feed`(8694) -> `optimize_multistage` 보상(8820) -> `apply_theta_feed` feeds(8895) -> **L**: `derive_role_L`(8943)/`derive_class_L`(8987) -> **VDS**: 헤드룸 worklist `_hr_resolve_vertical_group`(9151) -> vsb `reconcile_vsb_from_nodes`(9207) -> **gm_id**: `apply_diode_self_consistent_gm_id`(9236) -> `gm_id_role` 루프(9238-9286) -> `gm_id_match_vgs_of` 2-pass(9306-9351) -> 매칭쌍 gm_id 전파 B17(9353-9427) -> 조인트스캔 보정(9434) -> `audit_vsb_consistency` 게이트(9441) -> `audit_l_sharing_consistency`(9454) -> `compute_metric`(9468).
=> 실제 순서는 **L -> VDS -> gm_id**(SR:3537-3540 docstring도 명시). §1.4/§7.3이 전제한 "gm_id 확정 후 VDS"와 **반대**다.

### 0.2 4개 topology의 현 선언 필드 (python 집계)
| 필드 | current_reuse(파일럿) | folded_cascode | nmcnr | two_stage |
|---|---|---|---|---|
| `device_roles` 수 | 54 | 13 | 15 | 9 |
| `headroom_role` | 43 (tail4/mirror14/cascode18/floating_current_source4/diode_reference1/voltage_divider2) | 13 (diode_reference2/mirror6/cascode5) | 15 (mirror11/cascode4) | 7 (cascode4/tail2/mirror1) |
| `gm_id_role` | 36 (전부 matching) | 13 (matching10/gain3) | 12 (matching6/gain2/load4) | 3 (matching3) |
| `L_role` | 51 (bias_replica7/mirror44) | 13 mirror | 13 mirror | 3 (bias_replica1/mirror2) |
| `vertical_stack_id` | 51 | 13 | 15 | 4 |
| `vsb` | 44 | 13 | 15 | 7 |
| `gm_id_match_vgs_of` | 15 | - | 1 (M204->M203) | - |
| `vds_match_vgs_of` | 1 (M10->M16) | - | 2 (M109->M201, M204->M301) | - |
| `same_as_device` | 4 | - | - | - |
| `budget_reference_device` | 8 | - | - | 1 (M4->M5) |
| `fold_group` | - | 11 | 9 | - |
| theta feed 타입 | metric_stage_budget3 / C2 / B1 / A11 / A_signed4 (+`f_slew`=settling_split) | const1/A2/A_signed2 | const1/A5/A_signed5 | A1/metric_stage_budget2 |
| gain metric 타입 | `gain_stages_sum` stages=[[M1a,M4a,M2a,M3a],[M15,M16]] (+`gain_full_circuit_db`=smallsignal_gain_db, 제약 없음) | `folded_cascode_gain_db`(gm1_device/fold_leg_a/b/cascode_p/n/mirror_n) | `nmcnr_gain_db`(gm1..3_device, stage1_* 등) | `smallsignal_gain_db` |
| objective | power_uA | power_uA | power_uA | power_uA |
| `compensation` 키 | function/parameters[t_lln,PM_target_deg,Cf,Cs,C_Ltot]/stage_devices[[M1a,M1b],[M4a,M4b],[M15,M25],[M16,M26]]/shared_gm_id_groups/vds_kvl_groups | **null** | function/parameters[GBW,CL,PM_target_deg,kg]/stage_devices[[M102,M103],[M201],[M301]] | function/parameters[GBW,CL,Z,NDP]/stage_devices[[M1,M2],[M6]] |
| `ports` | Vip/Vim in, Vop/Vom out | 없음 | 없음 | vin_p/vin_n in (출력 없음) |

### 0.3 netlist 노드 공유 검산 (python)
- `vds_match_vgs_of` 3건 **전부** "참조 소자의 gate 넷 = 이 소자의 drain 넷, 두 source가 같은 레일": M10(drain Vop1, src gnd)->M16(gate Vop1, src gnd) / M109(drain NodeM2, src vdd)->M201(gate NodeM2, src vdd) / M204(drain NodeS2, src vss)->M301(gate NodeS2, src vss). => **노드전압이 정본이면(D1) 항등식**이다.
- `same_as_device`: M2b/M2a, M3b/M3a = 차동 좌우 대칭쌍. M7(drain Vx, gate **Vcmfb**, vdd)/M6(drain Vx, gate **Vbias1**, vdd) = 게이트가 다른 병렬 소자. M36b(drain=gate N36b)/M36a(drain=gate Vcmfb) = 서로 다른 노드의 diode. => 뒤 둘은 connectivity로 동일성이 나오지 않는다(설계 의도).
- `budget_reference_device`: 노드 공유 5건(M9a/M10 Vop1, M9b/M8 Vg15, M18a/M19 Vom1, M18b/M17 Vg25, M60/M66 Vbias4) / **비공유 4건**(M61 drain Vbias3 -> M5 drain Vy, M68 Vbias2 -> M6 Vx, M38 Ncmfb_tail -> M36a Vcmfb, two_stage M4 O1 -> M5 CS). P:741(B24 (가)) "소스가 레일인데 vsb!=0" 4소자 **M38/M60/M61/M68이 전부 이 필드 보유자**다.
- two_stage `headroom_role=="tail"` 2개 중 M7은 drain=OUT(출력단 전류 싱크)이다 -- 입력쌍 tail이 아닌 소자에 tail 라벨.

### 0.4 스키마 이름 grep (assets 전체, py+json)
`closed_loop_accuracy_db`/`driving_spec`/`ID_source`/`gm_id_policy`/`bias_devices`(코드)/`gain_budget_db`/`gm_id_for_gm_gds_ratio`/`resolve_stage_sizing`/`structural_declarations`/`feedback_loops`/`output_class`/`kvl_battery_loop` = **0건**. `shared_current_groups`는 `_shared_current_groups_from_compensation` SR:6167(호출 6904, 8668) 형태로만 존재.

---

## 1. 설계 요소 표

| 절 | 설계 요소 | 의도 | 여전히 필요? | 구현 상태 | 이후 발견과 충돌 | graph로 개선 | 근거 |
|---|---|---|---|---|---|---|---|
| §1.4-① | Phase 1(DC 완전 정합) -> Phase 2(남은 자유도로 AC 타겟), "VDS를 gm_id 확정 이후에만 푼다" | DC bias망을 먼저 정합시키고 gain은 그 위에서 맞춘다(사고21) | **변형** -- "Phase 순서"가 아니라 D1 노드전압 정본 + 명시적 순환 블록으로 | 다른 형태: 실제 순서 L->VDS->gm_id(§0.1), Phase 분리 함수 없음 | H:1376-1386 §7.9가 스스로 "VDS 예산<->gain 순환"을 기록. B16: 헤드룸 시점 diode gm_id 0/16 -> 순서 유지+역방향 구속(P:731). P:938 §12.3-8 순환 10종을 실행순서로 우회 | S2 노드전압(D1) + 유도 DAG의 SCC(C-c, P:976)가 "Phase 1"을 순서가 아니라 고정점 블록으로 대체. gm_id_i 자유축(P:410-419)은 SCC 밖 외부 변수 | H:196-203, P:1017, SR:3537-3540, SR:9151/9236 |
| §1.4-② | `vds_match_vgs_of`/`gm_id_match_vgs_of` primitive 재사용 | 참조 소자 VGS를 이 소자 VDS/gm_id로 강제 | **변형** -- `vds_match_vgs_of`는 D1에서 항등식(§0.3, 선언 불필요). `gm_id_match_vgs_of`는 same-kind 미러=유도, cross-kind(M15/M16류)=선언 | 구현: pre-pass SR:7680-7694, 2-pass SR:9306-9351, `vgs_alias_map` SR:1804. 체인 미지원(SR:9303) | B19'(P:735): 선언 기준 11소자 vs connectivity 18소자, 6소자(M5/M6/M7/M38/M66/M68) 누락 -> 사용자 확정 18 강제. B22(P:739): 미러 강제 후 diode 창이 그룹 전원 W 결정. `l_sharing_classes`는 이 필드를 edge로 안 씀(SR:2397-2399, cross-kind 혼재) | S1 `equal_vgs` 엣지를 `(kind,gate,source)`에서 유도(이미 `true_current_mirror_groups` SR:2358) -> 선언 누락 구조적 불가, 체인은 위상 순서로 자동. `vds_eq_vgs`는 노드 동일성이라 S2에서 저절로 성립 | H:201-203, §0.3 |
| §1.4-③ | `_resolve_vertical_group` fixed-point worklist + `_HeadroomDependencyNotReady` | 서로 다른 멤버로 맞물린 그룹을 풀 수 있는 것부터 반복 | **변형** -- C-c "순환은 명시적 고정점(수렴판정·상한·잔차)"으로 | 구현: `_hr_resolve_vertical_group` SR:7644(약 500줄), worklist SR:9127-9196 | P:922 "실행 순서라는 암묵 계약" T2 약 35건. REG:407 광범위 except SR:7852/:8006, 쌍마다 `propagate_node_voltages` 재호출(평가당 19회, P:934). §10.2 A7 수렴 논증 없음(P:705) | 유도 DAG SCC가 순환 블록을 구조적으로 찾음(P:976) -> "진전했나" 휴리스틱 제거. **안 되는 것**: 블록 내부 해법(허용오차 D2, P:1018)은 graph가 주지 않는다 | H:204-210 |
| §1.4-④ | `resolve_feed_vds` 우선순위 체인 확장 | (§7.3 행으로 통합, 개수에서 제외) | -- | -- | -- | -- | H:208-210 |
| §1.4-⑤ | 결합 소자쌍 조인트 스캔(§13.1/§13.2, M15/M16 71.14->75.80dB), 가칭 `shared_current_groups` | 단일소자 role 최적이 결합 최적점을 놓치는 것 방지 | **변형** -- 결합을 선언이 아니라 S1 관계 엣지 연결성분으로 식별 | 다른 형태: `_shared_current_groups_from_compensation` SR:6167(`compensation.shared_gm_id_groups` 선언에서 읽음), 조인트 스캔 `_scb_joint_plan`(보정 SR:9434) | P:936 조인트 스캔이 warm 평가의 66%인데 입력이 100% 같아도 재실행. §11.6 Case A(H:2978): stage_devices·shared_gm_id_groups **손 선언** | S2 블록 memo 키 "(그룹 L·vds·vsb·gm_total·고정 gm_id)"(P:983)로 재실행 제거. 결합 그룹은 S1 엣지(equal_vgs·stacked_vsb·same_as·matching·L class) union | H:216-221, §0.4 |
| §1.4-⑥ | cascode(`gain`: gm/gds 최대) vs 비캐스코드 load(`load`: gds 최소) 목적함수 구분(§13.7) | 서로 다른 물리량을 같은 기준으로 최적화하지 않기 | **유지** -- 단 "누가 cascode/load인가"는 선언이 아니라 유도 | 구현: `search_gm_id_for_role` role="gain" SR:2279-2284 / "load" SR:2285-2296. 선언은 nmcnr load4, fc gain3, **파일럿은 36개 전부 matching**(§0.2) -- 파일럿 cascode는 `L_cascode` metric_stage_budget theta가 담당 | A11(P:710): gm/gds가 gm_id에 비단조(VDS 0.6~1.2V에서 정점 18~20.5). 격자 전수 argmax라 선택 자체는 유효하지만 역산(§7.2 step3)은 깨짐. B19'/B22: 부하가 미러면 gm_id가 공유 VGS에 종속 | S1v `role_in_stage`로 "gm이 ro에 곱해지는 위치(소스=신호노드, 게이트 AC 접지)" vs "출력노드 병렬 컨덕턴스" 판정 -> C4(P:302, role만 바꿔도 vds 0.2/0.3/0.6) 제거 | H:222-226 |
| §6.1(가) | `resolve_feed_vds()`에 티어①(gate==drain -> 고정점) 추가 | 순서 의존 없이 diode에 물리값 | **폐기**(원형) -- 개념은 C-a writer 권한표로 흡수 | 구현 후 대체: v4.3(5c23a8b)에서 `set_device_vds` SR:3516 단일 setter로 전환 | B1 실측: `resolve_feed_vds`는 51소자 중 4개만, diode 0개(H:1083-1094) = 사고19 재현 | S2 필드×writer 티어표(P:974)가 "어느 함수 안 티어"라는 자리 문제를 없앤다 | H:241, A6 행37 |
| §6.1(가) | `allocate_stack_headroom()`/`HeadroomPolicy`: 균등분배 -> `headroom_fn(entry,ctx)` + dA/dVDS 가중 배분 | 물리 근거 없는 균등분배를 gain 기여도 배분으로 | **변형** -- D1에서 배분 대상은 "소자 vds"가 아니라 **자유 내부 노드전압**. 가중 기준(gain 기여)은 gain-budget-first에 필수 | **미구현**: 균등분배 그대로 SR:2062-2065, diode 구간 소자는 `lo` SR:2049-2051(docstring이 잠정이라고 자인 SR:2032-2034), `headroom_fn` 없음(`cascode_fn` SR:2002). 합 검증 `assert` SR:2084(-O에서 사라짐, REG:280) | B22(P:739): `lo` 선택이 미러 그룹 전원 W를 결정(최악 66.7배). B25: 적층 쌍은 W 균형 tie-break(SR:7893-7910). R4b "L보다 VDS 먼저"(P:449) | S1 KVL branch 방정식 + S2 노드전압 벡터 -> `∂gain/∂V(node)`를 전체회로 MNA(S2 memo)에서 수치미분해 배분. 스택 경계는 `kcl_series_union` SD:3167로 유도 | H:242, H:1704-1717 |
| §6.1(가) | `search_gm_id_for_role()` -> `search_gm_id_and_L_for_role()`(L축 내부화) | 같은 `_idu_scan` 중복 실행 제거 | **폐기** -- L은 소자 단위가 아니라 동치류 단위로 이미 외부화됨 | 구현 후 대체: `derive_role_L` SR:2772 / `derive_class_L` SR:2865 / `feasible_L_window` SR:2694 / `synthesize_l_class_thetas` SR:2612 (A6 행32) | §10.9 사용자 확정 "gain stage의 tail이 L의 주인"(H:2266-2268), 층3 공동 sweep(H:2350-2355) | S1 L 동치류(`l_sharing_classes` SR:2385) + owner(S1v stage/tail) -> L 축이 류 단위로 결정 | H:243 |
| §6.1(가) | `_L_ROLE_MULTIPLIERS`(2.5×/1.2×) -> `measure_L_knee()` | 공정 의존 knee를 상수로 박지 않기 | **유지** | 구현됨: `measure_L_knee` SR:2305, v4.39(dae3c5a) 상수 완전 제거 | v4.39 착지가 v4.38보다 나빴다(H:2544). knee는 gm_id에 민감해 격자 중앙값 사용(H:2323-2327). 캐시 `_KNEE_L_CACHE` 키 `id(lut)`(P:1082 #13) | knee 결과를 S2(키: LUT 내용해시·kind·격자)로 적재 -> C-d 위반 해소. 값 자체는 LUT 계층이라 graph가 개선하지 않음 | H:244 |
| §6.1(가) | `optimize_multistage()`/`topology_fn` 방향 반전(확정 gm -> Cc/Rz) | gain 주도 | **변형** -- v4.0에서 인과가 다시 뒤집힘: compensation이 `(Cc,Rz,gm_1..N)`을 한 번에, `gm_id_i`가 유일 자유축(P:410-419) | **미구현**: 여전히 topology_fn->gm, 비수렴 시 `converged=False` 그대로 반환(REG:396). §10.8은 Cc 유도만 착지(A6 행15) | G1 folded_cascode `compensation: null`(§0.2, P:751), G2 NMCNR 3단 하드코딩(P:752) | Cc<->Cgg2 순환(P:938)을 C-c 블록으로. `stage_gm_ref`는 S1v `stage_index`로 유도 | H:245, P:397-423 |
| §6.1(나) | "그대로 사용" 목록(LUT 계층, `size_transistor`, worklist, match primitive, 사후 metric 등) | 물리·수치 계층 보존 | **유지**(판단) -- 단 "보존 의무 아님"(H:255) 조항이 실제로 발동됨 | 대부분 R0(REG §3). 발동 사례: `_solve_vgs` rightmost root(B20, 57abfdd), L 보간 배열별 로그/선형(B15), worklist는 R2(REG:407) | B20: PMOS 비단조로 W 2.36배 조용히 틀림(P:736). B15: PMOS gm/ID 56,646까지 비물리(P:730) | LUT 계층은 graph로 개선되지 않는다. 캐시 키만 C-d(LUT 내용 해시) | H:247-256 |
| §6.1(다) | `verify_node_voltage_consistency()` | 전체 netlist KVL/KCL·게이트 VGS 정합 상시 게이트(§3.1-6 최우선) | **변형** -- D1에서는 "사후 검증"이 아니라 **S2 봉인 게이트**(노드전압 conflicts=거부, 버전 불일치=거부) | 부분: `propagate_node_voltages` SR:3895 / `derive_vsb_from_nodes` SR:3957 / `audit_vsb_consistency` SR:4018(배선 SR:9441) / `_metric_kcl_residual` SR:4430. **conflicts를 엔진이 안 읽음**(P:998 #2), 게이트-내부net VGS 검사 없음(A6 행16) | B7: 다중도달 4건 243.5mV(P:722). §12.6 #1 vsb/W 버전 혼재 7소자(P:997) | S2 노드전압이 정본이면 "경로별 값 충돌"은 쓰기 시점 거부로 바뀐다(C-b/C-c, P:975-976) | H:259, P:228-239 |
| §6.1(다) | `solve_allocation_dp()` (stage별 gm_id 배분, v4.2) | gain 배분을 엔진이 결정론으로 유도(§7.4 원칙3) | **유지** -- gain-budget-first의 핵심 산출기 | **미구현**(def 0, 프로브 `tests/probe_allocation_solvers.py`만, A6 행26) | A11 -> KKT 탐욕 폐기, DP 9/9(H:1630-1636). 분리성 전제 "stage의 (전력·면적·gain)이 자기 gm_id에만 의존"(H:1613)은 B21(부하 gds가 stage 밖 미러)·B19'(tail 미러 공유 VGS)로 **파일럿에서 거짓** | stage 표 계산 시 S1로 "그 stage 출력노드에 붙은 모든 소자"를 stage 멤버에 포함 -> 분리성이 성립하는 범위를 구조로 판정. 미러로 stage 간 결합되면 DP 변수를 그 연결성분 단위로 | H:1618-1624 |
| §6.1(다) | `diagnose_sizing_dof()` | 목표 수 대비 자유도 사전 진단(C6) | **변형** -- 세는 축을 S1 방정식(KVL branch·KCL 그룹·equal_vgs)과 S2 미지수(자유 노드전압·root 전류·gm_id_i)로 | **미구현**(def 0, A6 행23) | B5: VDS 미지수·KVL 방정식 안 셈(P:720), B6: 부등식을 등식처럼(P:721) | S1이 방정식 목록을 "개념당 정의 하나"로 가지면 랭크 계산이 가능해진다(현재는 세는 대상 자체가 흩어짐) | H:260 |
| §6.1(다) | `cross_check_with_spice()` | 독립 solver 교차검증 | **유지** | **미구현**(def 0, `build_transient_netlist.py` 없음, A6 행17) | A9 허용오차 미정(P:707) | graph 무관(단 S2 노드전압 스냅샷이 비교 대상 한 곳이 된다) | H:260 |
| §6.1(다) | 유령 3함수 `allocate_headroom_budget`/`measure_stage_gain_ceiling`/`redistribute_headroom_by_gain_gradient` | §7.9 Phase 1/2/3 | **폐기**(이름) -- 기능은 위 `allocate_stack_headroom` 변형행과 DP로 흡수 | 미구현 + 본문 정의 없음(P:763-764, A6 행35) | §10.5 정합성 지적 | -- | H:261-262 |
| §6.2 | `run_harness.py`의 신/구 경로 분기 | 신규 `sizing_spec` 유무로 분기 | **변형** -- 단일 진입점 `run_gmid_design_pipeline()`(P:1111) | 미구현. 진입점 `optimize_full_circuit_budget` SR:9624(RH:440) | §13.3 #18 실패해도 exit 0(P:1087) | graph 무관 | H:268-271 |
| §6.3 | 검증 4단계(self-test/회귀/diode 고정점/SPICE) | 재사이징 검증 | **변형** -- pytest + 계약 test(C-a~C-d 거부 케이스), stdout baseline 퇴역 | 부분: baseline 로그 2개(A6 행49), `def test_` 0건(A6 행45) | §13.3 #17 baseline이 FAIL을 고정(P:1086) | 계약 test가 graph 계약(봉인·지문·순서셔플)을 직접 검사 | H:273-276, P:1121-1165 |
| §7.1 | `schema_version`/`topology_ref` | spec<->topology 참조 | **변형** -- S0 지문(topology 정규화 해시)으로 참조 무결성 | 미구현(`*.sizing_spec.json` 0개, A6 행40) | §12.6 #8 spec_fingerprint 불일치를 노트만 남김(P:1004), 해상도 키 7개뿐(P:937) | S0가 topology+LUT+spec+유도규칙 해시로 대체(P:960) | H:284-285 |
| §7.1 | `global_spec.vdd` | 레일 전압 | **유지**(선언) | 구현: `spec["vdd"]`(SR:9201) | -- | 무관(S1 레일 노드 값) | H:288 |
| §7.1 | `global_spec.objective {"minimize":"power_uA"}` | 목적함수 전력 하나(v3.3) | **유지**(선언) -- 정의는 D6 | 구현: 4회로 `sizing_roles.objective`=power_uA(§0.2), type `sum_current` | A3/§13.3 #16: 스택 직렬 중복계상 2.82배, branch별 가중이 다름(P:701, P:1085), D6 착수조건(P:1196). A12 이름은 µA인데 A 반환(P:709) | S1 레일 노드 KCL(레일 유입전류 = `_metric_supply_current` SR:4502 정의)로 전력 정의가 구조에서 나온다 -- 무엇을 최소화할지는 여전히 사용자 | H:293 |
| §7.1 | `global_spec.closed_loop_accuracy_db` | 폐루프 정확도 | **폐기** -- 미소비 필드(P:768) | 미구현 0건(§0.4) | -- | -- | H:294 |
| §7.1 | `global_spec.constraints[]`(gain/area/cmrr/psrr/mismatch/noise) | 스펙 부등식 | **유지**(선언) | 구현: `sizing_roles.constraints` 파일럿 7개(gain_db>=54, mismatch_sigma_mV<=5.0, cmrr/psrr>=60, mirror_ratio_error_mV<=None, classab_centering<=0.15, parasitic_pm_deg>=None), fc/nmcnr 4, two_stage 2. None 값은 `resolve_constraint_references` SR:8370 | `mismatch_sigma_mV`=5.0 근거 없음(48f3a1d, §10.14), area_um2 제약이 4회로 모두 없음(§0.2, A12), noise 제약 선언 없음(원설계 예시엔 있음) | 값은 graph가 주지 않는다. 달성가능 임계값(§10.14/§10.15)은 S3 아카이브 몫 | H:297-308 |
| §7.1 | `metrics{}` 정의 블록(타입 선택) | 제약 이름이 무엇을 재는지 선언(v4.0 복원) | **변형** -- "무엇을 잴지(타입·excite/sense)"만 선언, 소자 역할 인자는 유도 | 다른 위치에 구현: `sizing_roles.metrics` 파일럿 19 / fc 5 / nmcnr 5 / two_stage 4, `_METRICS_REGISTRY` 경유 `compute_metric` SR:5842 | B18 재검증이 전역 metric 누락(P:733), G5 folded_cascode 역할키 5종(P:755), G8 새 토폴로지 = 레지스트리 3~4곳 등록(P:758) | S1v(excite=ports input, sense=ports output) + 전체회로 MNA면 `gm1_device/fold_leg_a/b/cascode_p/n/mirror_n/stages/tail_device/circuit_family` 인자가 필요 없다(REG:53-55 정본이 전부 smallsignal 계열) | H:317-334 |
| §7.1 | `metrics.gain_db.type="gain_stages_sum"` + `stages` | 파일럿 gain 식 | **변형** -- stage 멤버를 유도하고, 식은 "출력노드 컨덕턴스 합"을 보는 것으로 | 구현: `_metric_gain_stages_sum` SR:3028-3037(stage 목록 소자만 Σgm/Σgds), 파일럿 stages=[[M1a,M4a,M2a,M3a],[M15,M16]] | **B21**(P:738): 미러 18소자 6480조합에서 `gain_db` Δ=0, `gain_full_circuit_db` 63.67~89.82dB(26.15dB). M19.drain=Vom1, M10.drain=Vop1 = stage1 출력노드인데 stages에 없음. 미결(CTX:14328) | §2.2 참고 -- S1에서 stage 출력노드의 terminal 전부를 모으면 M10/M19가 자동 포함 | H:318-323, SR:5615-5621 |
| §7.1 | `metrics.cmrr/psrr.circuit_family`·`tail_device` | 폐형식 CMRR 선택 | **폐기** -- 전체회로 소신호 비(`smallsignal_ratio_db`)가 정본 | 파일럿은 이미 `smallsignal_ratio_db`(excite/sense), fc/nmcnr는 `cmrr_estimate` family/tail_device(§0.2) | REG:55 CMRR 정본 `_metric_smallsignal_ratio_db`, REG:501 `_cmrr_telescopic_class_ab_cmfb` 삭제 후보 | excite/sense는 S1v 공통모드·전원 여기 뷰(P:962)에서 나온다 | H:325-327 |
| §7.1 | `metrics.mismatch_sigma_mV.pairs` | offset 쌍 | **변형** -- stage_index로 입력환산 | 다른 형태: `input_referred_offset`(pairs 인자 없음) + `materialize_input_offset_pairs` SR:4696 | §11.6 Case B(직렬 단 오프셋 /A_1 미지원)·Case C(CMFB 쌍 metric 없음)(H:2976-2984) | S1v `stage_index` + 앞단 이득(S2 MNA) -> Case B 해결(H:2986-2988) | H:328 |
| §7.1 | `metrics.input_noise.devices` | 입력 소자 noise | **변형**(유도) | 구현: 파일럿 `noise_v_rthz` stages=[[M1a,M4a]] 손 선언, 제약 없음 | v4.0 주석 "있는 기능을 떨어뜨림"(H:335-339) | 입력소자 = excite 넷을 gate로 갖는 소자(`gain_stage_tails` 입력단 판정 SR:2476-2480과 같은 규칙) | H:329 |
| §7.1 | `structural_declarations.kcl`(A/A_signed) | KCL 전류 관계(부호 포함) | **변형** -- 방정식은 S1 KCL 그룹에서 유도, 남는 것은 "어느 전류가 root(자유/스펙)인가" | 스키마 블록 미구현(A6 행43). 기능은 theta feeds(파일럿 A11/A_signed4, fc A2/A_signed2, nmcnr A5/A_signed5, two_stage A1) + `propagate_topology_forced_currents` SD:3019 | §7.9 v3.2: 미러비 `k_i`는 파생값(탐색 축 아님)(H:1465-1468) vs 현 theta `r_*`/`kcl_*` 자유변수. B14 `value_amp` 소비는 kcl_residual뿐(A6 행52) | S1 KCL 그룹 + `matching{ratio}` 엣지 -> A/A_signed feed의 구조 부분이 사라지고 root 선택만 남음 | H:344-346, H:451-458 |
| §7.1 | `structural_declarations.diode_stack`(C) | diode 스택이 만들 기준전압 | **변형** -- diode 판정은 connectivity, 기준전압은 D1 노드전압 목표로 | 다른 형태: theta C feed 2개(예 `K_replica` target M9a reference M15), `_feed_diode_stack_target` SR:5978 | B25(P:742): 적층 diode는 vsb로 결합(`vsb_lo=vsb_up+v_up` SR:3722-3730) -> 독립 스택 선언으로 표현 불가 | S1 `stacked_vsb` 엣지 + S2 노드전압(`target_net`만 선언) | H:348-350 |
| §7.1 | `couplings.vds_match_vgs_of` | 참조 VGS = 이 소자 VDS | **폐기** -- 3건 전부 노드 공유(§0.3), D1에서 항등식 | 구현: SR:7680-7694 | -- | S2 노드전압에서 저절로 성립 | H:354 |
| §7.1 | `couplings.gm_id_match_vgs_of` | 참조 VGS로 gm_id 역산 | **변형** -- same-kind 미러는 유도, cross-kind만 선언 | 구현: SR:9306-9351, 파일럿 15 / nmcnr 1(§0.2) | B19'(P:735) 선언 11 vs connectivity 18, 사용자 확정 (가)(나) | S1 `equal_vgs`(`true_current_mirror_groups` SR:2358) | H:355 |
| §7.1 | `per_device.vs` | 소자별 vs 선언 | **폐기** -- 노드전압에서 유도 | 선언 잔존: `device_roles.vsb` 44/13/15/7(§0.2). 유도 `reconcile_vsb_from_nodes` SR:3976(배선 SR:9207) | B9/B24: 51소자 중 26개 불일치(P:741). vsb만 고치고 W/gds 미갱신 7소자(P:997) | S2 노드전압 -> vsb 파생 + C-b 버전(W가 옛 vsb 버전이면 봉인 거부) | H:360 |
| §7.1 | `per_device.budget_reference_device` | 스택 예산 기준 소자 | **변형** -- 노드 공유 5건은 D1 항등식, **비공유 4건은 공동분석** | 구현: `_hr_sum_ref_vds` SR:7515 | §0.3: 비공유 M61/M68/M38(+공유 M60) = B24 (가) vsb 오류 4소자 전원(P:741). 원인 `setdefault("vsb", ref_vds)`(SR:3981, P:724) | 공유분은 S2 노드전압으로 사라진다. 비공유분은 노드 관계가 아니라 "다른 스택 참조"라 graph가 의미를 모른다 -> `review_needed`(C8) | H:361 |
| §7.1 | `per_device.same_as_device` | 물리적으로 동일한 파트너 | **유지**(선언) -- 일부만 유도 | 구현: SR:7756-7773, `l_sharing_classes` edge(b) SR:2392-2393 | §0.3: M2a/M2b·M3a/M3b는 대칭쌍(S1 `matching{offset}`으로 유도 가능), M7/M6(게이트 다름)·M36b/M36a(다른 노드)는 설계 의도. M7=M6은 미러 L 사슬(H:2288-2289) | S1 `same_as` 엣지로 1회 정의(현재 헤드룸·L·gm_id 경로가 각자 읽음) | H:362 |
| §7.1 | `feedback_loops[]`(CMFB: sense/amp/tail + targets) | CMFB·gain-boost 루프를 stage/bias와 구분 | **변형** -- 루프 소자·경로·극성은 S1v, targets만 선언 | 미구현 0건(§0.4). 대체: theta B `N_cmfb_bw`(target M37a, **`L`=3.5e-7·`W`=5e-6 리터럴**, gm_id_bounds [2,26]) / `N_cmfb_bw_mirror`(TOPO 실측) | P:939: CMFB는 저항·커패시터로 닫혀 방향 규칙만으로 DAG가 안 됨. B19' pmos:Vcmfb 그룹은 gain 폭 0.0dB(P:735) -> 다른 기준 필요. 리터럴 L/W는 상수 금지 원칙 위반 | S1v 공통모드 여기 뷰의 SCC + 피드백 엣지 극성 -> 루프 멤버 자동. targets(loop_gain/PM/BW)는 graph가 못 준다 | H:370-377 |
| §7.1 | `stages[]` 분할 자체(`id`) | stage 경계 | **변형** -- S1v `stage_index` 유도, 손 선언은 대조용 | 미구현. 대체 선언이 **3곳에서 서로 다름**: 파일럿 `compensation.stage_devices`=[[M1a,M1b],[M4a,M4b],[M15,M25],[M16,M26]] vs `gain_db.stages`=[[M1a,M4a,M2a,M3a],[M15,M16]] vs noise [[M1a,M4a]](§0.2) | G6 stage 분할 규칙 없음(P:756). P:935 "stage 선언과 유도 불일치". §11.6 공통원인(H:2986) | S1v 차동 여기 뷰의 SCC 응축 DAG에서 게이트 구동 경계 = stage. D5 ports 선언 선행(P:1021) | H:379-405 |
| §7.1 | `stages[].devices.input` | gm 소자 | **변형**(유도) | 부분: `gain_stage_tails`가 excite 넷을 gate로 갖는 stage를 찾음(SR:2476-2480) | §11.6 Case A current-reuse 병렬 입력(M1a/M1b ∥ M4a/M4b) gm 손 분할(H:2978) | input_k = stage k 입력노드(=stage k-1 출력노드 또는 excite)를 gate로 갖는 소자 | H:383 |
| §7.1 | `stages[].devices.cascode` | gm이 ro에 곱해지는 소자 | **변형**(유도) | 미구현(스키마). 현 라벨 `headroom_role=cascode` 18(파일럿)에 diode가 섞임: diode 16개 role이 cascode 11/mirror 3/diode_reference 1/voltage_divider 2(H:1100-1101) | C4 FAIL(P:302). G6: 5신호 전용 시 입력쌍이 cascode로 분류(P:756) | S1v: 소스=신호노드·게이트=AC 접지 노드·드레인=출력노드 방향인 소자 | H:384 |
| §7.1 | `stages[].devices.load` | ro 자체로 기여하는 부하 | **변형**(유도) -- **미러 부하 포함이 필수** | 미구현(원설계 파일럿 예시가 `load: []`, H:385) | **B21**: M10/M19(부하)가 stage에 없어 26dB 괴리. 원설계 예시 `load:[]` 자체가 B21과 같은 누락 | S1: stage 출력노드에 drain이 붙은 비입력·비캐스코드 소자 전부 | H:385 |
| §7.1 | `stages[].devices.tail` | ID를 KCL로 정하고 CMRR/PSRR 좌우 | **변형**(유도) -- tail은 L의 주인(§10.9) | 부분: `gain_stage_tails` SR:2434(stage 소자의 source 넷을 drain으로 갖는 tail). **후보 집합은 `headroom_role=="tail"` 선언에 의존**(SR:2454-2455), gain_stages_sum 없는 3회로는 {}(H:2304-2305) | §10.9 사용자 확정 "최초 input 단 tail이 실제 주인"(H:2266). B19' tail M5/M6가 bias 미러와 묶임(사용자 확정). §0.3 two_stage M7(출력단 싱크)에 tail 라벨 | S1v: 입력쌍 공통 source 노드를 drain으로 갖는 소자(선언 불필요) | H:386-388 |
| §7.1 | `stages[].ID_source {kcl, ideal_source_ref}` | stage 전류 출처 | **변형** -- S1 KCL + `value_amp`(B14) + class-AB KVL 배터리(G4) | 다른 형태: A엔진 `propagate_topology_forced_currents` SD:3019 + theta seed | G4 class-AB 정지전류는 VGS 합(KVL)이 정함(P:754). v4.0 인과 `ID_i=gm_i/gm_id_i`(P:416)와 "KCL로 이미 확정" 전제가 충돌 | S1 KCL 그룹이 root 전류 집합을 결정, KVL 배터리 루프는 S1 엣지 | H:389, H:397 |
| §7.1 | `stages[].gain_budget_db_override` | 논문 재현 등 배분 강제 예외 | **유지**(선언, 기본 null) | 미구현 0건(§0.4) | v3.1 출력 격하(H:430-435) | 무관 | H:390-392 |
| §7.1 | `stages[].driving_spec`(CL/slew/settling) | 출력단 구동 요구 | **유지**(선언) | 다른 형태: theta `f_slew` feed `settling_split`(TOPO), `compensation.parameters`의 `C_Ltot`/`CL` | G4 `ID_final=max(KCL,SR×CL)`은 class-A 규칙(P:754). 명칭 흔들림 slew_rate_v_per_us vs slew_rate_target(P:769) | 무관(값). 적용 대상(출력 stage)은 S1v | H:399-403 |
| §7.1 | `compensation.{function,targets,solves_for,stage_gm_ref,gm_convention}` | 보상 방정식 선택·목표·해 변수 | **변형** -- function/targets는 선언, solves_for는 레지스트리 메타데이터, stage_gm_ref는 유도 | 다른 형태: `{function, parameters, stage_devices, shared_gm_id_groups, vds_kvl_groups}`(§0.2). parameters에 스펙 목표(PM_target_deg/GBW/CL)·설계 노브(kg/Z/NDP/t_lln)·소자값(Cf/Cs/C_Ltot)이 섞임. `targets`/`solves_for`/`stage_gm_ref`/`gm_convention` 키 0건 | G1 null(fc), G2 3단(P:751-752). `stage_gm_ref` 미소비(P:768) | stage_devices·stage_gm_ref는 S1v. Cf/Cs와 `passive_elements`의 대응은 **이번에 확인하지 않음** | H:407-412 |
| §7.1 | (현행) `compensation.shared_gm_id_groups`/`vds_kvl_groups` | current-reuse gm 공유 / KVL 쌍 | **변형** -- vds_kvl_groups는 D1 KVL로 유도, shared_gm_id_groups는 **공동분석**(회로 해석) | 구현: `_shared_current_groups_from_compensation` SR:6167 | §11.6 Case A 손 선언(H:2978) | KVL은 S1 branch 방정식. gm 합산 여부는 해석 | §0.2 |
| §7.1 | `headroom.policy="post_gm_id_self_consistent"` | gm_id 확정 후 자기일관 헤드룸 | **변형** -- D1 + C-c | 미구현(정책 키 없음). 실제 순서 반대(§0.1) | B16(P:731) | S2 노드전압 블록 | H:415 |
| §7.1 | `headroom.vertical_stacks[]`(+`vdd_kvl`) | KVL 컬럼 | **변형**(유도) | 다른 형태: `device_roles.vertical_stack_id` 51/13/15/4(§0.2). 유도·제안기 이미 있음: `kcl_series_union` SD:3167, `audit_vertical_stack_id_vs_kcl` SD:3322, `propose_vertical_stack_id_gap_fill` SD:3418 | 사고19 underdetermined(B5, P:720). `vdd_kvl` 미소비(P:768). two_stage 9소자 중 4개만 선언 | S1 KVL branch 방정식(`status=derived/proposed`) -- 손 선언 불필요 | H:416-418 |
| §7.1 | `bias_devices[]`(role / ID_source ideal_source_ref / `gm_id_policy`) | bias-gen 소자만 strong inversion 최소화 | **변형** -- bias 소자 식별은 유도, 정책은 **미러 동치류 단위**로 | 미구현 0건(§0.4). 현행 `gm_id_role=matching` 36(파일럿) | **B19'(나) 사용자 확정**: 공유 VGS는 gain 기준(tail M5/M6가 bias 미러와 묶임, P:735) -> "bias 소자는 min gm_id" 정책이 gain 경로와 충돌. pmos:Vcmfb는 gain 폭 0dB라 별도 기준 | S1 `equal_vgs` 연결성분에 gain-stage tail이 있으면 성분 전체가 gain 기준, 없으면 bias 정책(`l_class_owners`와 같은 판정 SR:2490-2515) | H:421-425 |
| §7.1 | `device_roles.headroom_role`/`gm_id_role` 폐기 | role 라벨 대신 connectivity | **유지**(방향 옳음) | **미구현**: 4회로 모두 존속(§0.2) | C4 FAIL(P:302), B1 diode 라벨 1/16(H:1100-1104). 예외: `voltage_divider`(M39/M40 의도적 균등, SR:1996-2000)·`floating_current_source`(배터리 전압이 설계량, SR:7785-7789)는 **예산 의도** | 대부분 S1/S1v 유도. 두 예외는 노드전압 목표 선언으로 재표현(공동분석) | H:436-439 |
| §7.1 | theta 처분표(자유변수 폐기 / A·A_signed·C·metric_stage_budget·servo B·gm_target_convention 존속) | 구조 선언 소실 방지(v4.0) | **변형** -- 존속 구조선언 대부분이 S1 유도 대상, 남는 자유변수는 L 동치류·root 전류·gm_id_i | 미구현: 파일럿 theta 22개 그대로(§0.2) | §10.10-10.11: L theta를 동치류에서 **파생**(`synthesize_l_class_thetas` SR:2612) -> "gm_id_i가 유일한 자유축"(H:453)과 불일치(현 자유변수는 L+전류비). 세션33 자동채움 회귀(권위 소스 4종) | S1이 KCL/KVL/equal_vgs/stage를 유도하면 feed 타입 A/A_signed/C/metric_stage_budget의 **구조 부분**이 사라지고 값 부분만 S3 탐색 변수로 남는다 | H:440-462 |
| §7.2 | 입력 `stage.gain_budget_db` | stage별 gain 목표에서 사이징 시작 | **폐기**(입력으로서) -- DP 출력 | 미구현 0건(§0.4) | v3.1 출력 격하(H:1433-1436), 원칙3(P:424-428) | DP stage 표를 S2에 적재 | H:467 |
| §7.2 | 입력 `ID(KCL로 이미 확정)` | 전류 고정 전제 | **변형** -- v4.0 인과: gm_i는 compensation, `ID_i=gm_i/gm_id_i` 파생(P:414-416) | 현행: ID는 A엔진+theta가 먼저 정함(SR:9244-9246 "A엔진이 전류를 못 정했다") | §7.9 v3.2 k_i는 파생값(H:1465-1468). 파일럿 비율 5.34는 활성 제약의 결과(H:1689-1691) | S1 KCL: gm_id_i 선택 -> root 전류 -> 미러비 역산 경로를 구조로 | H:467 |
| §7.2 | step1 cascode: L 후보 스캔으로 gm/gds 최대 -> (L_cas, gm_id_cas) | cascode 부스트 확정 | **변형** -- L은 동치류/owner가 정하고 gm/gds 최대는 gm_id만. cascode vds는 노드전압 차 | 다른 형태: 파일럿은 `L_cascode` theta(metric_stage_budget, gain_db 직접, M2a/M2b/M3a/M3b)(TOPO), role="gain" 경로 SR:2279 | 원칙1 "input+cascode 동시 결정"(P:395)과 step1 독립 결정이 모순. A11 비단조. R1/R2 매칭 L 강제(P:445-446) | cascode 식별 S1v. 게이트 bias 노드·소스 노드 전압이 S2 정본이라 vds_cas = V(drain)-V(source)가 스택 전체와 한 번에 정합 | H:469-471 |
| §7.2 | step1' load: gds 최소 | 부하 ro 최대 | **유지** -- 단 미러 부하는 공유 VGS에 종속 | 구현 role="load" SR:2285-2296(nmcnr 4소자) | B19'/B22: 미러 부하(M10/M19)는 `gm_id_match_vgs_of` 종속(SR:9306)이라 독립 gds 최소화 불가 | S1 equal_vgs 성분 단위로 목적함수(성분에 gain-stage 부하가 있으면 gain 기준) | H:472-477 |
| §7.2 | step2 input 목표 intrinsic gain = 10^(budget/20) / (cascode+load ro 부스트) | 목표에서 input gm/gds 역산 | **변형(필수)** -- 식이 "단일 소자 intrinsic × 부스트"라 출력노드 병렬 로딩을 못 봄 | 미구현 | §7.9 ① 부하 로딩 미반영 단당 −6dB(H:1534-1538), ② V_A의 gm_id 의존 최대 −5.5dB(H:1539-1553). **B21 26.15dB**(P:738). §7.9와 §7.2가 서로 다른 gain 모델(H:1537-1538) | **§2.2**: A_k = gm_in,k / G_out,k, G_out,k = stage k 출력노드에 붙은 모든 소자의 출력 컨덕턴스 합(미러 부하 gds 포함) -> S1 terminal 목록 + S2 gm/gds | H:478-479 |
| §7.2 | step3 `gm_id_for_gm_gds_ratio()` LUT 이분 역산 | 목표 gm/gds의 gm_id 직접 역산 | **폐기** -- 비단조 함수의 이분 역산은 틀린 근을 낸다 | 미구현 def 0(§0.4) | A11(H:1575-1605) 정점 위 지배 영역. 같은 파일의 이분 역산 단조성 미검사 결함(P:1079 #10), B20 rightmost root 선례(P:736) | graph 무관(LUT 계층). v4.0 인과에서 gm_i가 고정이면 역산 대상이 gm/gds가 아니라 G_out -> 격자 전수(DP)로 | H:480-481 |
| §7.2 | step4 `size_transistor()` W | W 확정 | **유지** | 구현 SR:115(R0), 같은 식 인라인 복제 4곳(REG:38, REG:445) | B20 W 조용히 틀림(해소 57abfdd). B22 미러는 `id_density_at_vgs` SR:609 경로(VGS에서 직접). §12.6 #1 vsb/W 버전 혼재 | S2 W 필드 `{writer, input_version(L,vds,vsb,gm_id)}` -> C-b 봉인 게이트 | H:482 |
| §7.2 | output stage `ID_final=max(KCL ID, SR×CL)` | 슬루 요구로 ID 상향 | **변형** -- class-A/AB 구분 필요 | 다른 형태: `f_slew` settling_split feed(TOPO) | G4(P:754), §10.7 class-AB 배터리 KVL(H:2004-2046) | S1 KVL 배터리 루프 엣지로 AB 판정을 **제안**(확정은 선언 `output_class` 권장, G4) | H:484-486 |
| §7.2 | 캐스코드/load 없는 단순 stage는 부스트=1 | 특수 케이스 흡수 | **유지** | 미구현(알고리즘 전체 미구현) | -- | G_out 정식화에서 자동 성립 | H:489-490 |
| §7.2 | 순차(1->1'->2->3) 정당성: "목적함수가 자기 소자만의 함수", 결합은 stage 경계 밖 예외 | 순차 알고리즘의 전역최적 논증 | **변형** -- 전제가 파일럿에서 반증됨 | 미구현(docstring 명시 대상 `resolve_stage_sizing` 없음) | B19'(tail 미러 공유 VGS가 input stage gain에 직결, 사용자 원문 P:735), B25(적층 diode vsb 결합), §10.9(L 동치류), B17(매칭쌍 gm_id, P:732) -> "stage 내부에는 결합이 없는 게 일반적"(H:500-501)이 거짓 | S1 관계 엣지 union의 연결성분 = 결합 블록. 블록이 한 소자면 순차, 여러 소자면 조인트 -- 선택이 선언이 아니라 구조에서 나온다 | H:492-503 |
| §7.3 v2.0 | `resolve_feed_vds(name, declared_vds, ctx)` 체인 재사용(①ctx.sized ②declared ③role 폴백) | 소자 vds 결정 우선순위 단일화(사고24) | **폐기** | 구현 잔존 SR:2138-2151(theta feed 2곳 경유) | REG:398 "누가 언제 썼는지 확인 없이 재사용" = C-a 부재. B1 4/51 | S2 writer 권한표 | H:511-513 |
| §7.3 v3.0 | 티어① `gate==drain` -> diode 고정점을 `resolve_feed_vds` 최우선에 | 호출 순서와 무관하게 diode에 물리값 | **폐기**(자리) | 구현 후 대체(v4.3, 5c23a8b) | B1(H:1080-1098) | 자리 문제 자체가 C-a로 사라진다 | H:525-527 |
| §7.3 v3.0 | 티어② `ctx.sized` 기존 vds 존중 | 다른 메커니즘이 먼저 확정한 값 존중 | **폐기** -- 이것이 곧 "먼저 쓴 쪽이 이김" | 구현 SR:2147-2149 | C2(P:300) `test_order_shuffle_invariance` 미실행 | C-a: 필드×writer 티어 권한표 + setter가 권한 없는 덮어쓰기를 거부 | H:528 |
| §7.3 v3.0 | 티어③ declared_vds(spec 명시값) | 사람이 준 값 | **변형** -- D1에서 선언 대상은 소자 vds가 아니라 **노드전압 목표**(예: 출력 CM, 배터리 전압) | 구현 `_feed_vds_fallback` SR:2131-2132 | B24: 소자 단위 선언(vsb 0.0)이 노드 불일치 26건을 만듦(P:741) | S2 노드전압 writer 중 `declared` 티어 | H:529 |
| §7.3 v3.0 | 티어④ role 폴백(KVL/KCL 그룹 비소속이 확인된 소자에만, C1) | 최후 폴백 | **폐기** | 구현 `_feed_vds_fallback` SR:2133-2135, 상수 0.6/0.2 SR:2104/2116 | §13.3 #20 근거 없는 폴백 상수(P:1089). C4 role만 바꿔도 vds 0.2/0.3/0.6(P:302). 부분 대체 `lut_vdsat_headroom`(SR:7796) | D1에서 모든 소자는 두 노드 사이라 "KVL 무관 소자"가 존재하지 않는다 -> 폴백 대상이 구조적으로 공집합. 하한은 LUT vdsat 유도 | H:530-531 |
| §7.3 | `_solve_diode_connected_vgs_fixed_point(gm_id, L, vs, lut)` | Vgs=Vds 고정점 | **변형** -- 방향이 vds->gm_id로 뒤집힘(B16). gm_id가 먼저 정해지는 경우에만 bisection | 이름 바꿔 구현 `solve_diode_connected_vds` SR:3297(bisection, A7) + `apply_diode_self_consistent_gm_id` SR:3743(역방향) | C1 당시 16/16 tol 초과(P:299). B16 헤드룸 시점 gm_id 0/16(P:731). REG:58 새로 만들지 말 것 | D1: diode 노드 V(gate=drain)가 곧 vgs=vds -> "V(node)->gm_id->W" 한 방향 관계식. gain-budget-first에서 bias diode gm_id를 정책으로 정하면 반대 방향 bisection | H:540-545 |
| §7.3 | 호출 시점 "§7.2가 diode gm_id 확정 직후 ctx.sized에 기입" | 헤드룸 루프가 그 값을 존중 | **폐기** -- 시점 전제가 거짓 | 실제: L->VDS->gm_id(§0.1), diode gm_id는 SR:9236에서 vds로부터 | B16(P:731) | 시점 개념 자체를 C-c 블록 반복으로 대체 | H:546-550 |
| §7.3 | diode끼리 맞물리면 worklist에 pre-pass 끼워넣기(새 알고리즘 발명 금지) | 사고22 교훈 | **변형** -- 실제로는 새 2변수 연립이 필요했다 | 구현 후 대체: `solve_stacked_diode_pair` SR:3659(격자 2변수) + `_hr_resolve_vertical_group` 쌍 처리 SR:7802-7960 | A8 "연립 불필요"(v4.13) -> **B25 번복**(P:742): `vsb_lo=vsb_up+v_up` 누적, 쌍 합 상한, 정확 합, 위쪽 비-diode, 위쪽 소스 비레일. `idu_up=1.0` 대입 결함(P:1080 #11) | S1 `stacked_vsb` 엣지 사슬 -> SCC 블록(2소자 한정 아님, N 적층). vsb가 S2 노드전압에서 파생되므로 "누적식"은 노드전압 차로 저절로 성립 | H:551-555 |
| §7.3 v4.3 | `set_device_vds(ctx,name,value,source)` 단일 setter + `_vds_source` + 원시대입 grep 테스트 | 7개 기입점 수렴, C2/C9 | **변형** -- D1에서 setter 대상은 **노드전압**, 소자 vds는 파생(P:1017) | 구현 SR:3516(원시 대입 SR:3565 한 곳). grep 테스트 미구현(A6 행27) | vsb는 setter 우회 원시대입 SR:4012, W/gm/gds 미갱신(REG:296, P:997). diode 검사가 캐시 없이 매 호출 bisection(REG:292) | C-a 타입 setter 일반화(P:974) + C-b 입력버전 | H:1149-1156 |
| §7.3 v4.3 | pre-pass 자기참조 확장(diode = `vds_match_vgs_of[m]=m`) | diode를 기존 primitive 특수 케이스로 | **변형** | 다른 형태: `diode_vds_window` 구간 제약(SR:3570) + allocate `lo`(SR:2049) + `apply_diode_self_consistent_gm_id`(SR:9236) | B16: 자기참조 고정점은 헤드룸 시점에 gm_id가 없어 불가 -> 구간 제약 변수로 전환(P:731) | D1에서 자기참조는 동일 노드 -> 항등, 남는 것은 노드전압 bounds | H:1134-1143 |
| §7.3 v4.17/B22 | `diode_vds_window(lut,kind,L,ID,vsb,W_bounds,mirror_members)` 구간 | diode vds 선택 = W 선택, 미러 전원의 W 한계 | **변형** -- 구간 = 그 노드를 gate/drain으로 공유하는 모든 소자의 W_bounds 교집합(노드 변수 bounds) | 구현 SR:3570-3656. mirror_members는 `gm_id_match_vgs_of` **선언 옵트인**(SR:3599-3600), 캐시 키 `id(lut)`(SR:3617, REG:293) | B22 최악 66.7배(P:739), B23 선행조건 B9(P:740) | S1 equal_vgs 연결성분에서 mirror_members 자동(선언 누락 불가). 노드 bounds를 S2에 적재·memo | SR:3593-3614, P:739 |

---

## 2. 질문별 답

### 2.1 §7.1 스키마 필드: graph에서 유도 가능 vs 사람이 선언해야

분류 기준: **유도** = S1(connectivity·타입 관계 엣지)/S1v(여기 모드 뷰)/S2(노드전압)에서 계산된다. **선언** = 사용자 spec(목표치·objective·ports·전류원 값)이라 graph가 줄 수 없다. **공동분석** = 회로 해석이 걸려 있어 Claude 단독 판단 금지(MEMORY "회로위상 해석은 항상 공동분석", P:1198 D8) -- graph는 `proposed`/`review_needed`까지만 만든다.

#### (A) 원설계 §7.1 필드

| 필드 | 분류 | 근거 |
|---|---|---|
| `stages[]` 분할 | 유도(S1v `stage_index`) -- 전제: `ports` 선언(D5) | G6(P:756), 선언 3곳 불일치(§0.2) |
| `stages[].devices.input` | 유도 | excite(또는 앞 stage 출력) 넷을 gate로 갖는 소자 |
| `stages[].devices.cascode` | 유도 | S1v 위치 규칙. 라벨은 diode를 11개 섞음(H:1100) |
| `stages[].devices.load` | 유도 | stage 출력노드에 drain이 붙은 나머지 소자(B21 원인 해소) |
| `stages[].devices.tail` | 유도 | 입력쌍 공통 source 노드를 drain으로 갖는 소자. "tail이 L의 주인"은 사용자 확정 **규칙**(H:2266) |
| `stages[].ID_source` | 유도(KCL 그룹) + 선언(`ideal_sources.value_amp`, B14) | P:729 |
| `stages[].driving_spec` | 선언 | 스펙 |
| `stages[].gain_budget_db_override` | 선언(예외) | H:430-435 |
| `bias_devices[]` 목록 | 유도 | 신호 여기 뷰에서 AC 접지 노드만 구동하는 소자 |
| `bias_devices[].gm_id_policy` | 선언(전역 규칙 1회) -- 단 미러 성분에 gain tail이 있으면 gain 기준(B19'(나) 사용자 확정) | P:735 |
| `compensation.function` | 선언(회로 부류; S1v 패턴 매칭은 제안까지) | G2(P:752) |
| `compensation.targets`(GBW/PM/CL) | 선언 | 스펙 |
| `compensation.solves_for` | 선언 아님 -- 레지스트리(코드) 메타데이터 | G2 "topology_fn 메타데이터로 이동"(P:752) |
| `compensation.stage_gm_ref` | 유도 | S1v stage_index |
| `compensation.gm_convention` | 선언 | B타입 feed 규약(H:458) |
| `headroom.policy` | 폐기(엔진 계약 C-c) | P:976 |
| `headroom.vertical_stacks`/`vdd_kvl` | 유도(S1 KVL branch) | `kcl_series_union` SD:3167 등 제안기 존재 |
| `structural_declarations.kcl` | 방정식 유도 / root 전류 선택·값은 선언 또는 탐색 | H:1465-1468 |
| `structural_declarations.diode_stack` | diode 판정 유도 / `target_net` 전압 목표는 선언 | B25 |
| `couplings.vds_match_vgs_of` | 유도(항등식) | §0.3 3건 검산 |
| `couplings.gm_id_match_vgs_of` | same-kind 유도 / cross-kind 선언 | B19', SR:2397-2399 |
| `per_device.vs` | 유도(노드전압) | B9/B24 |
| `per_device.budget_reference_device` | 노드 공유 5건 유도 / **비공유 4건 공동분석** | §0.3 |
| `per_device.same_as_device` | 대칭쌍 유도 / M7=M6·M36b=M36a 선언 | §0.3 |
| `feedback_loops[]` | 멤버·극성 유도(S1v SCC) / `targets` 선언 | P:939 |
| `metrics{}` | 타입·excite/sense 선언(ports) / 소자 역할 인자 유도 | REG:53-55 |
| `global_spec.*` | 선언 | 스펙 |

#### (B) 4개 topology.json의 **현재 필드** 분류(§0.2 실측)

| 현 필드 | 보유 회로(개수) | 분류 | 비고 |
|---|---|---|---|
| `device_roles.headroom_role` | 4회로(43/13/15/7) | **유도**(diode/mirror/tail/cascode) + **공동분석**(`voltage_divider` 2, `floating_current_source` 4 -- 예산 의도, SR:1996-2000/7785-7789) | 두 예외는 노드전압 목표 선언으로 재표현 |
| `device_roles.gm_id_role` | 4회로(36/13/12/3) | **유도**(역할 분류) -- 선택 정책은 DP·equal_vgs 성분 규칙이 대체 | 파일럿 36개 전부 matching이라 §13.7 구분이 파일럿에서 안 쓰임 |
| `device_roles.L_role` | 4회로(51/13/13/3) | **유도**(동치류+owner+knee) + **공동분석**(`bias_replica` 의도: `derive_class_L`의 `prefer_knee`가 여전히 L_role에서 옴, SR:2880) | H:2358-2360 |
| `device_roles.vertical_stack_id` | 4회로(51/13/15/4) | **유도** | 제안기 SD:3418 |
| `device_roles.vsb` | 4회로(44/13/15/7) | **유도**(노드전압) -- 선언 폐기 | B9 |
| `device_roles.gm_id_match_vgs_of` | 파일럿 15, nmcnr 1 | **유도**(same-kind 게이트·소스 공유 미러: 파일럿은 B19'가 실측 P:734, nmcnr M204/M203은 SR:9291-9292 주석 "gate=NodeC, source=vss 동일") | cross-kind가 생기면 그것만 선언 |
| `device_roles.vds_match_vgs_of` | 파일럿 1, nmcnr 2 | **유도**(D1 항등) | §0.3 |
| `device_roles.same_as_device` | 파일럿 4 | M2b/M3b **유도**, M7/M36b **선언** | §0.3 |
| `device_roles.budget_reference_device` | 파일럿 8, two_stage 1 | 5건 **유도**, 4건 **공동분석** | §0.3 |
| `device_roles.fold_group` | fc 11, nmcnr 9 | **공동분석** | MEMORY "fold_group 오판 반복(세션42)" |
| `sizing_roles.theta[].feeds` A/A_signed | 4회로 | KCL 구조 **유도** / root 전류·bounds는 탐색 변수 | |
| theta feed C | 파일럿 2 | diode **유도** / 목표 전압 **선언** | |
| theta feed B(servo `N_cmfb_bw`) | 파일럿 1 | 루프 멤버 **유도** / 대역폭 배수 **선언**, feed 안 `L`/`W` 리터럴은 **유도돼야 할 값**(상수 금지) | TOPO 실측 |
| theta feed metric_stage_budget | 파일럿 3, two_stage 2 | stage 멤버 **유도** / 어느 metric에 묶는지 **선언** | |
| theta feed settling_split / const | 파일럿 1 / fc·nmcnr 1 | **선언** | |
| theta `bounds` | 4회로 | **유도**(이미 선언된 제약에서: L 상한 parasitic_pm_deg, 하한 mismatch, CTX:14321-14323) | |
| `sizing_roles.metrics` | 4회로(19/5/5/4) | 타입 **선언** / 역할 인자(`stages`, `gm1_device`, `fold_leg_*`, `cascode_*`, `mirror_n`, `tail_device`, `circuit_family`, `high_device/low_device`) **유도** | |
| `sizing_roles.objective`, `constraints` | 4회로 | **선언** | D6 |
| `compensation.function` | 3회로(fc null) | **선언** | |
| `compensation.parameters` | 3회로 | 스펙 목표(PM_target_deg/GBW/CL) **선언** / 설계 노브(kg/Z/NDP/t_lln) **선언 또는 탐색(DOF)** / Cf·Cs·C_Ltot **확인 안 함** | |
| `compensation.stage_devices` | 3회로 | **유도**(S1v) | 파일럿은 gain stages와 불일치 |
| `compensation.shared_gm_id_groups` | 파일럿 | **공동분석** | §11.6 Case A |
| `compensation.vds_kvl_groups` | 파일럿 | **유도**(KVL) | |
| `symmetry.matching_pairs` | 4회로 | 후보 **유도**(offset=대칭쌍, ratio=미러) / 매칭 요구·sensitivity **선언**(`proposed`로 제시) | |
| `ports` | 파일럿·two_stage | **선언**(D5: Claude 제안 -> 사용자 확인, P:1021). fc/nmcnr 미선언, two_stage 출력 미선언 | |
| `ideal_sources.value_amp` | 파일럿 1.2µA / fc null | **선언** | B14 |
| `netlist`, `passive_elements` | 4회로 | 사용자 전용 connectivity(유일 소스) | MEMORY "topology.json이 유일한 토폴로지 소스" |

### 2.2 §7.2 "stage 1개 기준" 알고리즘과 이후 사실의 충돌 -- 출력노드 임피던스를 graph에서 모으면

**원 알고리즘의 모델**(H:466-482): `A_stage = (input gm/gds) × (cascode+load 부스트)` -> 목표 A에서 input의 gm/gds를 역산 -> LUT 이분으로 gm_id -> W.

**충돌 5가지**

1. **A11 비단조**(P:710, H:1580-1586): VDS 0.6/0.9/1.2/1.5V에서 gm/gds 최대가 gm_id 20.5/20.0/18.0/18.0에 있고 그 위로는 감소 구간. step3 이분 역산(`gm_id_for_gm_gds_ratio`)은 해가 둘이거나 정점 위 지배 영역을 고른다 -> step3 폐기, 격자 전수 DP(v4.2, H:1607-1636).
2. **B21 부하 누락**(P:738): `_metric_gain_stages_sum`은 stage 목록 소자의 Σgm/Σgds만 쓴다(SR:3033-3036). 파일럿 stage1 출력노드 Vop1/Vom1에 drain이 붙은 미러 부하 M10/M19가 목록에 없어 미러 6480조합에서 `gain_db` Δ=0.0000인데 `gain_full_circuit_db`는 26.15dB 벌어진다. §7.2 step2의 "부스트" 모델도 같은 결함이다 -- 원설계 파일럿 예시가 `load: []`(H:385).
3. **v4.0 인과 역전**(P:410-419): gm_i는 compensation이 정한다. 그러면 `A_k = gm_k·R_out,k`에서 조정 변수는 input gm/gds가 아니라 **R_out,k(=1/G_out,k)**다. step2가 역산할 대상이 틀렸다.
4. **§7.9와 §7.2가 서로 다른 gain 모델**(H:1537-1538): 병렬 로딩 단당 −6dB, V_A의 gm_id 의존 −5.5dB(H:1543-1553).
5. **"stage 내부는 결합이 없다" 전제 반증**: B19' tail 미러 공유 VGS가 input stage gain을 결정(사용자 확정, P:735). 부하 M10/M19은 NMOS Vbias4 미러 성분에 속하고 tail M5와 같은 L 동치류(M68류, H:2288)다 -- stage1의 G_out이 bias 미러·tail L과 결합돼 있다.

**출력노드 임피던스(부하 gds 합)를 graph에서 모으면 달라지는 것**

- **모으는 법**: S1 넷 노드마다 `terminals`(소자, 단자) 목록이 있다(§11.2가 "함수마다 재구성"이라 적은 필드, H:2918). stage k의 출력노드 = S1v 차동 여기 뷰에서 stage k의 sense 노드(파일럿 stage1 = Vop1/Vom1, stage2 = Vop/Vom). `G_out(node) = Σ_{drain∈node} y_out(d)`. 소스가 AC 접지(레일·bias)인 소자는 `gds_d`, 소스가 내부 신호노드인 소자(캐스코드)는 소스쪽 컨덕턴스로 축소된 값(문헌 표준 소신호식 -- **이 저장소에서 실측한 식은 아니다**). 정확한 값은 이미 있는 전체회로 MNA(`build_ac_network` SR:4230 / `_full_circuit_response` SR:5543)가 준다. graph가 새로 주는 것은 **"그 노드에 누가 붙었나"의 정본 목록과 무효화 키**다.
- **(i) B21이 구조적으로 사라진다**: M10/M19가 Vop1/Vom1 terminal 목록에 자동으로 들어간다. P:738 선택지 ②("stages에 부하 추가 -- 누가 부하인지 판정 규칙 필요 = G6")의 판정 규칙이 곧 "출력노드에 drain이 붙은 소자"다.
- **(ii) DP 분리성이 성립하는 범위를 구조로 판정**: G_out,k에 들어간 소자가 다른 stage나 bias 미러의 equal_vgs/L 동치류 성분에 속하면 stage k와 그 성분은 결합이다 -> DP 변수를 연결성분 단위로 묶는다(H:1613 분리성 전제의 적용 가능 범위를 선언이 아니라 그래프가 말한다).
- **(iii) 역산 대상이 바뀐다**: gm_k 고정(compensation) -> 필요한 `G_out,k = gm_k / A_k` -> 출력노드 이웃 소자들의 (L, gm_id, 노드전압) 조합으로 만족 -> 격자 전수(비단조와 무관).
- **(iv) 괴리를 원인별로 분리 측정**: "노드별 G_out으로 만든 stage 곱" vs 전체 MNA를 metric으로 나란히 두면, 26dB가 stage 멤버 누락 때문인지 stage 간 로딩 때문인지 갈라 볼 수 있다(P:738 선택지 ③ "괴리를 metric으로 감시"의 구체형).
- **(v) 재계산**: 노드 G_out은 이웃 소자 버전이 바뀔 때만 무효화(S2 입력 해시). FD 한 스텝에서 실제로 바뀐 소자 6.7/51(P:936).
- **graph로 안 되는 것**: (a) CMFB·Miller Cc로 닫힌 노드의 "DC 이득"은 여기 모드 선택이 필요하다(S1v가 모드를 나눠 주지만 어느 모드가 스펙인지는 선언). (b) class-AB 출력단 M15∥M16처럼 두 소자 gm이 합쳐지는지(`shared_gm_id_groups`)는 노드에 둘 다 붙었다는 사실만으로 결정되지 않는다(공동분석, §11.6 Case A). (c) LUT 비단조(A11/B20)는 graph 계층 밖이다.

### 2.3 §7.3 우선순위 체인을 D1(노드전압 정본) 아래에서 다시 세우기

**원칙**: 정본은 노드전압 `V(n)` 하나다(P:1017). 소자의 `vds/vgs/vsb`는 kind 부호를 붙인 노드전압 차로 **파생**된다(`propagate_node_voltages`의 부호 규약 SR:3912, `derive_vsb_from_nodes` SR:3963-3964). 따라서 "소자 vds를 누가 정하나"라는 체인은 **"노드전압을 누가 쓰나"(writer 티어) + 노드 변수 병합 + 순환 블록 + 자유 노드 배분**으로 바뀐다.

**재정식화한 writer 티어(C-a 권한표 초안)**

| 티어 | 내용 | writer | 원 체인에서 온 것 |
|---|---|---|---|
| **T0 레일** | vdd/gnd/vss 노드 값 | S1 + `global_spec.vdd` | -- |
| **T1 구조 항등(변수 병합)** | 같은 전압이어야 하는 노드·단자를 **하나의 변수로 합친다**: diode(gate==drain), `vds_match_vgs_of` 3건, `budget_reference_device` 노드공유 5건, `vds_kvl_groups` | S1(쓰기가 아니라 union) | 원 티어①(diode 최우선)이 "우선순위"가 아니라 **변수 동일성**이 된다 |
| **T2 물리 종속 블록** | 노드전압 <-> gm_id <-> W 관계식: diode/미러 노드(`diode_vds_window` 구간), 적층 vsb 결합(노드전압 차라 자동), 스택 KVL VGS 상한(`stack_kvl_vgs_limit` SR:1835) | 순환 블록 solver 하나(C-c: 수렴판정·상한·잔차, 비수렴 `InfeasibleSizingError`) | v4.3 pre-pass 자기참조, B16 역방향, B25 쌍 연립 |
| **T3 선언 노드전압 목표** | 출력 CM, Vcmfb 목표, class-AB 배터리 전압(`floating_current_source` 의도), VDD/2 분압(`voltage_divider` 의도) -- **공동분석 확정 후** | spec | 원 티어③ declared_vds(소자 단위 선언은 금지) |
| **T4 자유 노드전압** | 남은 내부 노드 = §7.9 "VDS 예산 배분"의 진짜 변수. bounds = 이웃 소자 포화 하한(LUT vdsat, `lut_vdsat_headroom` SR:7796) ∩ T2 구간 | 배분기(gain 기여 가중 / DP / SLSQP) | 원 티어④ role 폴백과 `allocate_stack_headroom` 균등분배를 **대체** |
| (삭제) | 원 티어② "ctx.sized에 먼저 쓴 값 존중" | -- | 권한표로 대체: 낮은 티어는 높은 티어가 쓴 노드를 못 덮고, 같은 티어 두 writer가 한 노드에 다른 값을 쓰면 **conflict = 봉인 거부**(현재 conflicts는 계산만 하고 버림, P:998) |

**setter 계약**
- `set_node_voltage(node, V, tier, input_version)` 하나만 쓰기 경로. `set_device_vds`(SR:3516)는 **읽기 전용 파생 접근자**로 격하(P:1017 "노드전압 writer의 파생").
- grep 게이트 대상 확장: `["vds"] =` + `["vsb"] =` 원시 대입(현재 vsb는 SR:4012에서 setter를 우회).
- C-b: W/gm/gds 필드는 `(L, gm_id, V(d), V(g), V(s))` 버전을 기록 -> 노드전압이 바뀌면 파생 필드가 무효. `reconcile_vsb_from_nodes`처럼 "사후 덮어쓰기"가 구조적으로 불가능해져 7소자 버전 혼재(P:997)가 사라진다.
- 순서 독립: 결과가 티어와 SCC 고정점에만 의존 -> `test_order_shuffle_invariance`(C2, P:300)가 성립하는 조건.

**원 체인·현행 코드 -> 새 위치 대응**

| 원 체인 / 현행 | D1 재정식화 | 현재 위치 |
|---|---|---|
| 티어① gate==drain -> 고정점 | T1 병합(V(g)=V(d)) + T2 방정식 V<->gm_id<->W | `is_diode_connected` SR:3287, `apply_diode_self_consistent_gm_id` SR:3743, `diode_vds_window` SR:3570 |
| 티어② ctx.sized 존중 | 삭제 -> 권한표 + conflict 거부 | SR:2147-2149 |
| 티어③ declared_vds | T3 선언 노드전압 | SR:2131-2132 |
| 티어④ role 폴백 | 소멸(T4 + LUT 포화 하한) | SR:2133-2135, 상수 SR:2104/2116 |
| `vds_match_vgs_of` pre-pass | T1 병합 | SR:7680-7694 |
| `same_as_device` vds 복사 | 같은 노드면 T1, 아니면 선언된 동일성 제약(T2 방정식) | SR:7756-7773 |
| `budget_reference_device` + `_hr_sum_ref_vds` | 공유 5건 T1 / 비공유 4건 **공동분석** 후 T3 또는 삭제 | SR:7515, §0.3 |
| `allocate_stack_headroom` 균등분배 | T4 배분기 | SR:2062-2065 |
| `solve_stacked_diode_pair` | T2 블록(vsb 누적은 노드차로 자동, N 적층) | SR:3659 |
| `reconcile_vsb_from_nodes` 사후 덮어쓰기 | 소멸(vsb는 항상 파생) | SR:3976, 호출 9207 |
| `audit_vsb_consistency` 게이트 | 봉인 게이트로 일반화(vsb뿐 아니라 W/gds 버전·노드 conflict) | SR:4018, 호출 9441 |

**D1으로도 안 풀리는 것(정직한 한계)**
1. KVL만으로 노드전압이 유일하게 정해지지 않는다 -- 자유 노드 수가 곧 DOF이고, 배분 기준은 gain-budget 목적(DP/가중)에서 와야 한다(graph가 주지 않음).
2. `propagate_node_voltages`는 `passive_elements`의 저항 강하를 읽지 않는다(SR:3917) -- 노드전압 정본화에는 KCL 전류×R 항이 필요하다.
3. 다중 DC 동작점은 복원하지 않는다(SR:3919).
4. 블록 수렴 허용오차는 D2(P:1018)대로 LUT 격자에서 계산해야 하며 계산법이 아직 없다.
5. 비공유 `budget_reference_device` 4건과 `voltage_divider`/`floating_current_source` 의도는 회로 해석이라 공동분석이 선행돼야 T3/T1 중 어디로 갈지 정해진다.

---

## 3. 집계 (§1 표의 행 기준, §1.4-④ 통합행 제외)

| 절 | 행 | 유지 | 변형 | 폐기 |
|---|---|---|---|---|
| §1.4 | 5 | 1 | 4 | 0 |
| §6 | 13 | 4 | 6 | 3 |
| §7.1 | 33 | 7 | 22 | 4 |
| §7.2 | 10 | 3 | 5 | 2 |
| §7.3 | 11 | 0 | 6 | 5 |
| **합계** | **72** | **15** | **43** | **14** |

## 4. 가장 중요한 충돌 top 8

1. **순서가 반대다**: 원설계는 "gm_id 확정 후 VDS"(H:199-200, H:546), 코드는 L->VDS->gm_id(SR:3537-3540, 9151->9236). B16(헤드룸 시점 diode gm_id 0/16, P:731)이 이 순서를 강제했다.
2. **B21 -- gain 제약이 부하를 못 본다**: `gain_stages_sum`이 stage 목록 소자만 합산해 미러 부하 M10/M19를 놓치고 전체회로와 26.15dB 괴리(P:738). §7.2 step2 부스트 모델과 §7.1 예시 `load: []`가 같은 결함.
3. **A11 -- gm/gds가 gm_id에 비단조**(P:710): §7.2 step3 이분 역산 폐기, DP로 대체(H:1607-1636).
4. **v4.0 인과 역전**(P:410-419): gm_i는 compensation이 고정하고 gain_budget_db는 출력(H:1433), ID는 파생 -- §7.2의 두 입력 전제가 모두 뒤집혔다.
5. **B19' -- 미러 18소자 강제 + 공유 VGS는 gain 기준**(P:735): bias_devices/gm_id_policy 분리와 "stage 내부 비결합" 순차 논증(H:492-503)이 파일럿에서 성립하지 않는다.
6. **B25 -- 적층 diode는 vsb로 결합**(`vsb_lo=vsb_up+v_up`, SR:3722-3730, P:742): A8 "연립 불필요" 번복. diode 단독 고정점(§7.3)은 불충분.
7. **B9/B24 -- vsb 26/51 불일치**(P:741): `per_device.vs` 선언 폐기. `reconcile_vsb_from_nodes`가 vsb만 고쳐 W/gds 버전 혼재 7소자(P:997). 오류 4소자(M38/M60/M61/M68)가 전부 `budget_reference_device` 보유자(§0.3).
8. **B1 + §10.9**: `resolve_feed_vds` 티어는 4/51·diode 0개만 지나감(H:1083-1094) -> 체인 자리 폐기. "gain stage의 tail이 L의 주인"(H:2266)이라 cascode 단독 L 결정(§7.2 step1)도 불가.

## 5. graph 기반 재설계 핵심 포인트

1. **stage = S1v `stage_index`**(ports 선언 D5 선행). stage 멤버 = 입력 + 출력노드 terminal 전부(부하 포함) -- 3곳에 흩어진 손 선언(§0.2)은 대조용으로만.
2. **stage gain = gm_in / G_out(출력노드)**: G_out은 S1 terminal 목록 + S2 gds, 전체회로 MNA와 괴리를 metric으로 감시.
3. **결합 블록 = S1 관계 엣지(equal_vgs·stacked_vsb·same_as·matching·L class)의 연결성분** -> DP 변수 단위와 순차/조인트 선택을 구조가 정한다.
4. **DC = 노드전압 정본 + writer 티어 T0~T4**, 소자 vds/vsb는 파생, conflict·버전 불일치는 봉인 거부.
5. **순환은 SCC 블록**(diode V<->gm_id<->W, 적층 diode, 미러 공유 VGS<->레퍼런스, Cc<->Cgg2) -- 실행 순서 계약 제거.
6. **선언 최소화**: 목표·objective·ports·`value_amp`·cross-kind 매칭·노드전압 목표만 선언. `fold_group`·`shared_gm_id_groups`·비공유 `budget_reference_device`·`voltage_divider`/`floating_current_source` 의도는 공동분석.
7. **graph가 못 하는 것**: 자유 노드전압의 배분 기준, 저항 강하(passive), 다중 동작점, 루프 targets, LUT 비단조.
