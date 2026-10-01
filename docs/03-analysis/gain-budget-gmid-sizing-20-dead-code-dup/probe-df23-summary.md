# Phase 2B 실측 -- probe 전수(A)와 DF-23 전수(B)

> 읽기 전용 실측. 판단·결정 없음. 생성 스크립트: `scan_probes.py`, `code_lines.py`,
> `check_symbols.py`, `scan_df23.py`, `scan_df23b.py`, `build_outputs.py`, `make_summary.py`.
> 원자료: `probe_inventory.json`, `df23_inventory.json`, `code_hits.json`,
> `_probe_symbols.json`, `_df23_raw.json`, `_df23b_raw.json`.

## A. probe 전수 -- 42개

### A-0. 공통 사실(42/42 전부 동일)

| 항목 | 실측 |
|---|---|
| probe 파일 수 | 42 (`skills/analog-gmid-design/assets/tests/probe_*.py`, 전부 git 추적됨) |
| `if __name__ == "__main__"` 실행부 | **0 / 42** -- 전부 모듈 최상위(import 즉시 실행되는 스크립트) |
| pytest 형식(`def test_` 또는 `import pytest`) | **0 / 42** |
| 줄 수 | 최소 66(probe_metric_tiers) / 중앙값 137 / 최대 409(probe_mirror_design_space) |
| 엔진 심볼 정적 검사(참조하는 `sr.X`가 지금 엔진에 있는가) | 41 OK / **1 FAIL** |
| 하드코딩된 Windows 절대경로(`C:\Users\...`)를 쓰는 probe | 15 / 42 |

**산출물(`.result.txt` 등) 커밋 여부 -- A.4의 답: 커밋된 것은 0건이다.**
`.gitignore` 26~30행이 `tests/*.result.txt`, `*.sizing_cache.json`, `*.theta_star.json`,
`*.unwired_theta.json`, `*.window_dump.txt`를 전부 무시한다. 디스크에는 33개가 있지만
(`git status`가 보여주지도 않는다) **git 추적 대상은 하나도 없다**. `tests/` 안에서 추적되는
비-.py 파일은 `README.md`와 `canonical_theta_star.json`(픽스처) 둘뿐이다.

### A-1. 계획서 목록 대조(A.3)

| 목록 | 계획서 개수 | 실재 | 부재 |
|---|---|---|---|
| TS6 '승격 후보' | 7 | **7 전부 실재** | 0 |
| DF-21 '삭제' | 3 | **3 전부 실재** | 0 |
| 나머지(= TS6 'probes 이동' 잔여) | -- | 32 | -- |
| 운영 도구 `derive_achievable_bounds.py` (`tests/tools/`로 이동 대상) | 1 | `tests/derive_achievable_bounds.py`에 실재, `tests/tools/`는 **아직 없음** | -- |

참고: U-02는 "probe 삭제 11개"를 말하는데 DF-21은 3개만 이름을 댄다. 나머지 8개의 이름은
계획서에 없다(대조 불가).

### A-2. 승격 후보 7개

| probe | 줄 | 엔진 모듈 | 엔진 호출 수 | 확인된 엔진 로직 복제 | 심볼 검사 | 산출물(디스크) | 비고 |
|---|---:|---|---:|---:|---|---:|---|
| `probe_gm_id_monotonicity` | 393 | sizing_recipe | 2 | 3 | OK | 1 | - |
| `probe_physical_consistency` | 137 | sizing_recipe | 1 | 4 | OK | 0 | 절대경로 2, 스테일 필드 읽음 |
| `probe_parasitic_pm_all_circuits` | 151 | run_harness, sizing_recipe | 6 | 0 | OK | 1 | - |
| `probe_role_L_derivation` | 133 | run_harness, sizing_recipe | 8 | 0 | OK | 1 | - |
| `probe_lut_L_interpolation` | 179 | sizing_recipe | 2 | 0 | OK | 1 | - |
| `probe_revalidation_scope` | 95 | sizing_recipe | 2 | 0 | OK | 1 | - |
| `probe_prevention_wiring` | 94 | sizing_recipe, stick_diagram | 2 | 1 | OK | 0 | 절대경로 1 |

### A-3. DF-21 삭제 후보 3개 -- '실행 불가·무의미'의 실측 근거

| probe | 줄 | 실측된 상태 |
|---|---:|---|
| `probe_mirror_common_L_wiring` | 180 | **실행 불가.** 66·142행이 `sr._L_ROLE_MULTIPLIERS`를 읽는데 이 상수는 엔진에서 제거됐다(sizing_recipe.py 2568·2709 docstring이 "상수 대체/제거"라고 적고 있다). import 직후 `AttributeError`. 42개 중 심볼 결손은 이것 하나뿐 |
| `probe_node_voltage_audit` | 132 | **전제가 무효.** docstring이 "`audit_vsb_consistency()`는 엔진 경로에 호출부가 없다(2026-09-09 확인)"고 적고 있으나 지금은 `sizing_recipe.py:9481`에서 호출된다(세션46 배선). 즉 '미배선 진단'이라는 존재 이유가 사라졌다 |
| `probe_vs_semantics` | 88 | **무동작.** 51소자 전부를 `if not e or "vs" not in e: continue`로 거른다 -- 읽는 `current_reuse_telescopic_ota.instance.json`은 지금 `vsb`만 갖는다(`vs` 키 0개). 게다가 24·26행이 Windows 절대경로 2개를 박아 놓았고, 32-45행이 `propagate_node_voltages`를 손으로 다시 구현한다 |

### A-4. 엔진 로직 복제 -- 코드 줄을 직접 읽어 확인한 것만(A.2)

정규식 1차 후보는 `code_hits.json`에 전부 있고(주석·docstring 제외), 아래는 **본문 코드에서
실제로 같은 계산을 다시 구현한 것**만 추린 결과다. 정본 이름은 레지스트리 §2/§3에서 찾았다.

| probe | 줄 | 다시 구현한 개념 | 레지스트리 정본 | §2 행 |
|---|---|---|---|---|
| `probe_diode_min_vgs` | 93-104 | union-find 동치류 | `sizing_recipe.l_sharing_classes` | §2 'union-find' |
| `probe_diode_vds_window` | 72-76 | W = L*ID/IDu 인라인(공개 API로 IDu는 얻음) | `sizing_recipe.size_transistor` | §2 'W 계산' |
| `probe_gm_id_monotonicity` | 246-251 | gm_id->VGS 역보간(np.interp, 피크 이후 구간) | `SemiEmpiricalGmIdLUT.gm_id_for_vgs / _solve_vgs` | §3 R0 gm_id_for_vgs |
| `probe_gm_id_monotonicity` | 254-256 | IDu 재구현(LUT private 직접 호출) | `SemiEmpiricalGmIdLUT.id_density_at_vgs` | §3 R0 |
| `probe_gm_id_monotonicity` | 308-315 | W = L*ID/IDu 인라인 | `sizing_recipe.size_transistor` | §2 'W 계산' |
| `probe_mirror_common_L` | 97-99 | IDu 재구현 -- LUT private(_query/_log_ID/_w_ref_effective) 직접 호출 | `SemiEmpiricalGmIdLUT.id_density_at_vgs` | §3 R0 |
| `probe_mirror_common_L` | 93 | (참고) 소자·넷 이름 리터럴 REF={'nmos:Vbias4':'M66', 'pmos:Vbias1':'M18_bg', 'pmos:Vcmfb':'M36a'} | `-` | DF-23 유형(probe 쪽) |
| `probe_mirror_common_L_wiring` | 83-99 | union-find로 VGS/L 동치류 묶기 | `sizing_recipe.l_sharing_classes (+ vgs_alias_map)` | §2 '전류미러 그룹' / §2 'union-find' / §3 R0 l_sharing_classes |
| `probe_mirror_common_L_wiring` | 112-121 | theta feeds(metric_stage_budget)에서 소자->theta 역맵 | `sizing_recipe._theta_feed_footprint / _theta_device_map` | §2 'theta가 건드리는 소자' |
| `probe_mirror_design_space` | 164 | (gate, source, kind) 키로 미러군 묶기 | `sizing_recipe.true_current_mirror_groups` | §2 '전류미러 그룹' |
| `probe_mirror_design_space` | 170 | diode 판정 gate==drain | `sizing_recipe.is_diode_connected` | §2 'diode 판정' |
| `probe_mirror_design_space` | 220-253 | W_i = L*ID_i/IDu 인라인 | `sizing_recipe.size_transistor` | §2 'W 계산' |
| `probe_mirror_gain_ranking` | 158 | (gate, source, kind) 키로 미러군 묶기 | `sizing_recipe.true_current_mirror_groups` | §2 '전류미러 그룹' |
| `probe_mirror_gain_ranking` | 164 | diode 판정 gate==drain | `sizing_recipe.is_diode_connected` | §2 'diode 판정' |
| `probe_mirror_gain_ranking` | 194-201 | W_i = L*ID_i/IDu 인라인 | `sizing_recipe.size_transistor` | §2 'W 계산' |
| `probe_mirror_infeasibility` | 87-89 | IDu 재구현(LUT private 직접 호출) | `SemiEmpiricalGmIdLUT.id_density_at_vgs` | §3 R0 |
| `probe_mirror_infeasibility` | 115-116, 163-164 | W = L*ID/IDu 인라인 | `sizing_recipe.size_transistor` | §2 'W 계산' |
| `probe_mirror_wiring_readiness` | 96 | (gate, source, kind) 키로 미러군 묶기 | `sizing_recipe.true_current_mirror_groups` | §2 '전류미러 그룹' |
| `probe_mirror_wiring_readiness` | 102 | diode 판정 gate==drain | `sizing_recipe.is_diode_connected` | §2 'diode 판정' |
| `probe_node_voltage_audit` | 86 | 레일 넷 집합 재선언 RAILS={'vdd','vss','gnd','0'} | `sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO` | §2 '레일 넷 집합' |
| `probe_physical_consistency` | 48-70 | DC 노드전압 전파(순회 순서 2종 + 다중도달 불일치 수집) | `sizing_recipe.propagate_node_voltages(NodeVoltageReport.conflicts)` | §2 '노드 DC 전압' |
| `probe_physical_consistency` | 93-105 | 노드별 KCL 잔차(ID 부호 주입 합) | `sizing_recipe._metric_kcl_residual` | §2 'KCL 엣지' |
| `probe_physical_consistency` | 126 | source가 레일인지로 vsb=0 판정 | `sizing_recipe.derive_vsb_from_nodes` | §3 R0 |
| `probe_physical_consistency` | 40 | 레일 넷 집합 재선언 | `sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO` | §2 '레일 넷 집합' |
| `probe_prevention_wiring` | 46 | diode 판정 gate==drain | `sizing_recipe.is_diode_connected` | §2 'diode 판정' |
| `probe_ratio_pair_analysis` | 145-148 | 게이트·소스 공유 여부 인라인 판정(미러 성립 조건) | `sizing_recipe.true_current_mirror_groups` | §2 '전류미러 그룹' |
| `probe_stack_headroom_feasibility` | 63-74 | union-find 동치류(스택 그룹) | `sizing_recipe.l_sharing_classes / _hr_resolve_vertical_group` | §2 'union-find' / §2 '스택 KVL 합' |
| `probe_stacked_diode_options` | 79-80 | IDu 재구현(LUT private 직접 호출) | `SemiEmpiricalGmIdLUT.id_density_at_vgs` | §3 R0 |
| `probe_stacked_diode_options` | 89-90 | W = L*ID/IDu 인라인 | `sizing_recipe.size_transistor` | §2 'W 계산' |
| `probe_supply_current` | 55-66, 92-96 | 레일 직결 소자의 공급전류 합(+RAILS_HI/LO 재선언) | `sizing_recipe._metric_supply_current(4540) / _DEFAULT_RAIL_*` | §3 R0 _metric_sum_current / §2 '레일 넷 집합' |
| `probe_vds_assignment_paths` | 129 | diode 판정 gate==drain | `sizing_recipe.is_diode_connected` | §2 'diode 판정' |
| `probe_vs_semantics` | 32-45 | DC 노드전압 전파(이름 정렬 순회 + vds 누적) | `sizing_recipe.propagate_node_voltages` | §2 '노드 DC 전압' |
| `probe_vs_semantics` | 59 | vsb 유도(NMOS=V_s, PMOS=vdd-V_s) | `sizing_recipe.derive_vsb_from_nodes` | §3 R0 |
| `probe_vs_semantics` | 24 | 레일 넷 집합 재선언 RAIL_HI/RAIL_LO | `sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO(3893-3894)` | §2 '레일 넷 집합' |

개념별 집계(복제 건수):

| 정본 | 복제한 probe 수 |
|---|---:|
| `sizing_recipe.size_transistor` | 6 |
| `sizing_recipe.is_diode_connected` | 5 |
| `SemiEmpiricalGmIdLUT.id_density_at_vgs` | 4 |
| `sizing_recipe.true_current_mirror_groups` | 4 |
| `sizing_recipe._DEFAULT_RAIL_HI/_DEFAULT_RAIL_LO` | 3 |
| `sizing_recipe.l_sharing_classes` | 2 |
| `sizing_recipe.propagate_node_voltages` | 2 |
| `sizing_recipe.derive_vsb_from_nodes` | 2 |
| `SemiEmpiricalGmIdLUT.gm_id_for_vgs / _solve_vgs` | 1 |
| `-` | 1 |
| `sizing_recipe._theta_feed_footprint / _theta_device_map` | 1 |
| `sizing_recipe._metric_kcl_residual` | 1 |
| `sizing_recipe.l_sharing_classes / _hr_resolve_vertical_group` | 1 |
| `sizing_recipe._metric_supply_current` | 1 |

정본을 **호출하는** 것이라 복제로 세지 않은 것(참고): `probe_interp_scheme_loo`·
`probe_lut_L_interpolation`(`_multilinear_interp` 정본 호출), `probe_gmid_gain_landscape`
(`size_transistor` 호출 후 IDu 역산).

### A-5. 세 후보군 집계(A.1 요약)

| 후보군 | probe 수 | 엔진 로직 복제가 있는 probe | 복제 건수 합 | 절대경로 박힌 probe | 산출물 디스크에 있음 |
|---|---:|---:|---:|---:|---:|
| 승격(TS6) | 7 | 3 | 8 | 2 | 5 |
| 삭제(DF-21) | 3 | 3 | 6 | 1 | 2 |
| 이동(나머지) | 32 | 12 | 20 | 12 | 20 |
| **합** | 42 | 18 | 34 | 15 | 27 |

### A-6. 눈에 띄는 것

* 승격 후보 `probe_physical_consistency`는 (a) 엔진 정본을 거의 안 쓰고(엔진 호출 1건)
  `propagate_node_voltages`·`_metric_kcl_residual`·`derive_vsb_from_nodes`·레일 집합을
  전부 손으로 다시 구현하며, (b) Windows 절대경로로 세션18 산출물 `*.instance.json`을 읽고,
  (c) 그 파일에 이제 없는 `vs` 필드를 `.get("vs", 0.0)`으로 읽어 **B9 절 전체가 항상
  '전 소자 vs=0'으로 나온다**(무동작).
* 승격 후보 `probe_gm_id_monotonicity`(393줄, 최대)는 `gm_id_for_vgs` 역보간을 np.interp로
  다시 짜는데, 그 probe의 목적 자체가 "엔진 역보간이 비단조 구간에서 틀리는가"라서
  대조군 성격이다 -- 복제로 볼지 판단이 갈릴 수 있다(design에서 결정).
* IDu 재구현 4건(`probe_mirror_common_L`·`probe_mirror_infeasibility`·
  `probe_stacked_diode_options`·`probe_gm_id_monotonicity`)은 전부 같은 두 줄
  `math.exp(lut._query(lut._log_ID, ...)) * L / lut._w_ref_effective(L)` 복붙이고,
  **LUT의 private 멤버를 직접 건드린다**. 정본은 `SemiEmpiricalGmIdLUT.id_density_at_vgs`.
* 미러군을 `(gate, source, kind)` 키로 묶는 코드가 3개 probe에 그대로 복붙돼 있다
  (`probe_mirror_design_space:164`, `probe_mirror_gain_ranking:158`,
  `probe_mirror_wiring_readiness:96`) -- 레지스트리 §2가 이미 "probe 3곳 복제"라고
  적어 둔 바로 그것이다(정본 `true_current_mirror_groups`).
* `probe_mirror_common_L:93`은 `REF = {"nmos:Vbias4": "M66", "pmos:Vbias1": "M18_bg",
  "pmos:Vcmfb": "M36a"}`로 **소자·넷 이름을 박아 놓았다** -- DF-23과 같은 유형이 probe
  쪽에도 있다는 뜻(DF-23의 점검 범위는 엔진 소스라 목록에는 넣지 않았다).

---

## B. DF-23 전수 -- 엔진 소스의 소자·넷·회로 이름과 topology 경로 리터럴
이 절의 수는 1e2e243 측정 기록이다. 현재 목록은 `df23_inventory.json`(`measured_at`, 항목마다 `phase`).

### B-0. 방법

추측하지 않고 **근거 어휘를 먼저 만들었다**: `library/*.topology.json` 9개에서 소자 이름
102개와 넷 이름 101개, 회로 이름 10개를 실제로 읽어 vocabulary로 쓰고,
엔진 소스의 문자열 리터럴과 exact-match했다(스캔 1). 이것만으로는 `folded_cascode_gain_db`
같은 **파생 이름**을 놓치므로, 회로 이름 줄기(telescopic/folded_cascode/nmcnr/two_stage/
ngcc/miller/pushpull/current_reuse/class_ab/common_gate) substring 스캔을 덧붙였다(스캔 2).
역할은 AST 부모 노드로 판정했다(dict 키 / 비교 / 구독 / 호출·키워드 인자 / 상수 테이블 =
"동작을 정함", docstring·f-string·문자열 결합·주석 = "메시지뿐").

### B-1. 총계 -- '동작을 정함' 대 '메시지뿐'

| 파일 | 동작을 정함 | 메시지뿐 | 합 |
|---|---:|---:|---:|
| `skills/analog-gmid-design/assets/audit_current_forced.py` | 1 | 4 | 5 |
| `skills/analog-gmid-design/assets/design_report.py` | 0 | 2 | 2 |
| `skills/analog-gmid-design/assets/sizing_recipe.py` | 117 | 148 | 265 |
| `skills/analog-gmid-design/assets/sky130_lut_sweep.py` | 0 | 2 | 2 |
| `skills/analog-gmid-design/assets/stick_diagram.py` | 94 | 102 | 196 |
| `skills/analog-gmid-design/assets/topology_library.py` | 11 | 46 | 57 |
| `skills/analog-gmid-design/assets/topology_to_markdown.py` | 1 | 1 | 2 |
| `workspaces/run_harness.py` | 42 | 19 | 61 |
| **합** | **266** | **324** | **590** |

`design_report.py`·`sky130_lut_sweep.py`에는 **동작을 정하는 리터럴이 0건**이다
(메시지·docstring뿐). `audit_current_forced.py`(172 `glob("*.topology.json")`)와
`topology_to_markdown.py`(200 `f"{topo_name}.topology.md"`)는 각 1건이고 둘 다 파일 이름
규약 리터럴이다.

### B-2. '동작을 정함' 266건의 분포(계획서 DF 대조)

| 계획서 매핑 | 건수 | 대표 위치 |
|---|---:|---|
| 신규(계획 DF-29~34 목록 밖) | 148 | 아래 B-3 참조 |
| DF-29 | 40 | sizing_recipe.py 5061~5370: `_load_telescopic_topology_cached`(5071 파일 경로), `_TELESCOPIC_FIXED_BASE`(5077 `gnd`/`Vbias1`~`Vbias4`), `_telescopic_class_ab_open_loop_response`(5109·5115 `Vip`/`Vim`/`vdd`/`Vcmfb`, 5117 `Vop1`/`Vom1`), `_cmrr/_psrr_telescopic_class_ab[_cmfb]` |
| DF-34 | 18 | run_harness.py 71·131·211·248 `_spec_*()` 정의 + 309~347 `SPECS`의 회로 이름 키·`topology_file` 경로·`spec_fn`(계획서는 305~350) |
| DF-30(회로별 metric 함수) | 17 | sizing_recipe.py 3051~3220 `_folded_cascode_rout`·`_metric_folded_cascode_*`·`_nmcnr_stage1_rout`·`_nmcnr_predict`·`_metric_nmcnr_*` |
| DF-33 | 12 | run_harness.py 123·124·127 `stack_groups_override`/`row_split`의 소자 이름 `M1`~`M7` |
| DF-31(회로별 보상 함수) | 11 | topology_library.py 33·62·121·137·257·339·373 회로별 보상/예측 함수 정의 |
| DF-30(신규 위치) | 7 | sizing_recipe.py 5725~5728 `_METRIC_UNITS`의 같은 회로 이름 키 4개 + 10193·10196·10200 `if mtype == "folded_cascode_gain_db"` 류 분기 3곳 |
| DF-31 | 6 | sizing_recipe.py 1469~1480 `_COMPENSATION_REGISTRY` import + 회로 이름 키 4개(계획서는 1464~1471) |
| DF-30 | 4 | sizing_recipe.py 5676~5679 `_METRICS_REGISTRY`의 회로 이름 키 4개(계획서는 5656~5663이라고 적음 -- 줄 밀림) |
| DF-29(신규 위치) | 2 | sizing_recipe.py 4853~5060: `_cmrr_telescopic_class_ab` 본체와 `telescopic_class_ab` 오류 메시지 -- 계획서 DF-29가 이름을 댄 세 함수 밖 |
| DF-32 | 1 | sizing_recipe.py 2460 `r.get("headroom_role") == "tail"`(계획서는 2442·2455) |

계획서 DF-29~DF-34가 지목한 위치는 **전부 실재했다**(줄 번호는 DF-30·31·32·34에서
4~20줄씩 밀려 있으나 계획서가 "...행 참고"라고 적은 대로 함수 이름으로 찾으면 일치).

### B-3. 계획서 목록 밖에서 새로 나온 것

| 분류 | 건수 | 내용 |
|---|---:|---|
| 레일 넷 이름 리터럴(vdd/gnd/vss) | 63 | `'vdd'` 49회·`'gnd'` 25회·`'vss'` 4회가 코드에 박혀 동작을 정한다. 선언은 topology.json `supply_nets`에 있는데 코드가 안 본다. 같은 집합이 최소 **3곳에 따로 선언**돼 있다: sizing_recipe `_DEFAULT_RAIL_HI/_LO`(3893-3894), sizing_recipe `_build_theta_evaluator`(8592), stick_diagram(3167). 레지스트리 §2 '레일 넷 집합'이 "SD 소문자만 vs SR 대소문자 2곳 -- 불일치, 결함 후보"라고 이미 적은 것 |
| 픽스처 넷리스트(stick_diagram 6928-7010, 운영 호출부 0) | 61 | `folded_cascode_example()`(6928~)과 `two_stage_ota_example()`(6970~)이 소자 이름 13개·넷 이름 다수를 `Transistor(...)` 인자로 박아 엔진 모듈 안에 **테스트 픽스처를 들고 있다**. 운영 호출부는 0이고 `tests/unit/test_selftest_stick_diagram.py`만 쓴다(TS1/TS3 이동 대상과 겹침) |
| 기타 넷/소자 이름 리터럴 | 9 | sizing_recipe 4265·5580 `build_ac_network`/`_full_circuit_response`의 기준 노드 `'gnd'`, 4829~4832 `_metric_battery_centering_deviation`의 `'vdd'`/`'gnd'` 등 |
| 어휘 충돌(역할 라벨/spec 키 -- 넷·소자 이름 아님) | 9 | `'tail'`·`'bias'`는 folded_cascode/two_stage_ota에 같은 이름의 넷이 실제로 있어 어휘에 걸렸지만, 걸린 자리는 전부 **역할 라벨**이다(`headroom_role == "tail"`=DF-32, `m.ports["tail"]`, `min_vds_by_role`의 `"tail"`=DF-20). `'CL'`·`'Cc'`는 spec 키. DF-23 목록에서 제외하고 해당 DF로 돌려보낼 것 |
| 파일 이름 규약 리터럴(.topology.json 등) | 6 | sizing_recipe 8252·8264(`require_declared_spec_source`), run_harness 428·429(`.topology.json`->`.instance.json`), audit_current_forced 172, topology_to_markdown 200. 회로 이름은 아니지만 '파일 경로가 코드에 박힘'이라 DF-23 범위 |

### B-4. '메시지뿐' 324건

대부분 docstring·주석·오류 메시지에서 회로 이름을 **사례로** 드는 것이다
(`sizing_recipe.py` 148건, `stick_diagram.py` 102건, `topology_library.py` 46건).
동작에 영향이 없으므로 DF-23의 교체 대상이 아니다. 전체 목록은
`df23_inventory.json`의 `role == "메시지뿐"` 항목.

### B-5. 눈에 띄는 것

* **소자 이름 리터럴이 운영 코드에 있는 곳은 `run_harness.py` 123·124·127(DF-33)뿐이다.**
  나머지 소자 이름 30건 중 27건은 `stick_diagram.py`의 self-test 픽스처 두 함수 안에 있다.
  계획서 DF-23이 적은 "엔진 운영부의 소자 이름 문자열 리터럴은 0건"은 이번 실측에서도 맞다
  (run_harness를 엔진 운영부로 치면 3줄).
* **가장 많은 것은 레일 넷 이름 리터럴 78건**(`vdd` 49·`gnd` 25·`vss` 4)이고, 그중
  63건은 DF-29~34 어디에도 등록돼 있지 않다(나머지 15건은 DF-29 등에 딸려 있다).
  `supply_nets`가 topology.json에 선언돼 있는데 코드가 `"vdd"`/`"gnd"`를 직접 쓴다.
  `nmcnr_amplifier`·`pushpull_follower_buffer`·`sf_pushpull_output_opamp`는 `vss`를 쓰고
  `agnd`도 있는데, `_metric_supply_current`(4540)는 `'vdd'`만 본다.
* DF-30의 사정권이 계획서 기록보다 넓다: `_METRICS_REGISTRY`(4키) 말고도
  `_METRIC_UNITS`(같은 4키)와 `metric_devices` 계열의 `if mtype == ...` 분기 3곳이 더 있다.
  DF-30을 "위반 4곳"으로 세면 실제 교체 지점은 그보다 많다.
* DF-29의 사정권도 넓다: 계획서가 세 metric 함수만 댔지만, 그 셋이 공유하는
  `_telescopic_open_loop_device_names`(5131)·`_telescopic_class_ab_open_loop_gains`(5146)와
  `_CMRR_REGISTRY`(5255-5256)·`_PSRR_REGISTRY`(5366-5367)의 `telescopic_class_ab*` 키까지
  같이 움직여야 한다.
* `_load_telescopic_topology_cached`의 docstring은 "connectivity는 오직 이 JSON에서만
  읽는다(하드타이핑 없음, topology.json이 유일한 토폴로지 소스)"라고 적고 있는데, **그 JSON
  경로 자체가 5071행에 박혀 있다**. 선언을 지킨다는 주장과 실제가 갈리는 자리다.
