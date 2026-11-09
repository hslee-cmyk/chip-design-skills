# gm/ID 사이징 엔진 현재 능력 실측 (2026-10-07)

- 기준: HEAD 6df4bd7 의 `git archive` 격리 복사본 `/c/g448/src` (저장소 무변경)
- Python: C:\Python314\python.exe 3.14, numpy 2.4.6 / scipy 1.18.0 (사용자 site-packages)
- 주의(환경): MSYS `timeout` 명령으로 python을 감싸면 user site-packages가 안 잡혀 `No module named numpy` -- Python `subprocess.run(timeout=590)` 드라이버로 대체했다.

## 1. library 회로 목록과 스펙 위치

엔진 주석상 "4개 회로"(sizing_recipe.py:5017-5018 docstring): `current_reuse_telescopic_ota` / `folded_cascode` / `nmcnr_amplifier` / `two_stage_ota`.

| 회로 | topology.json | 엔진 실행 spec(공정·탐색 파라미터) | 성능 제약(topology.json `sizing_roles.constraints`) |
|---|---|---|---|
| two_stage_ota | skills/analog-gmid-design/assets/library/two_stage_ota.topology.json (소자 7, theta 3) | workspaces/run_harness.py `_spec_two_stage_ota()` (GBW 7MHz, CL 3pF, vdd 1.8) | gain_db>=57, mismatch_sigma_mV<=5.0(근거 없음 표기) |
| current_reuse_telescopic_ota | .../library/current_reuse_telescopic_ota.topology.json (소자 51, theta 22) | run_harness.py `_spec_current_reuse_telescopic_ota()` (slsqp n_starts=3,maxiter=25) | gain_db>=54, mismatch<=5.0, cmrr_estimate_db>=60, psrr_estimate_db>=60, mirror_ratio_error_mV<=(mismatch), classab_centering_dev_v<=0.15, parasitic_pm_deg>=PM_target_deg(70) |
| folded_cascode | .../library/folded_cascode.topology.json (소자 13, theta 5) | run_harness.py `_spec_folded_cascode()` (grid 400) | **[] 비어 있음** -- `_constraints_status`: 2026-09-17 U-35 "자기 결과 역산값이라 삭제, 7a SPICE 대조에서 다시 읽는다, 그때까지 사이징 판정 보류" |
| nmcnr_amplifier | .../library/nmcnr_amplifier.topology.json (소자 15, theta 11) | run_harness.py `_spec_nmcnr_amplifier()` (GBW 816kHz, CL 100pF, PM 70) | **[] 비어 있음** (folded_cascode와 같은 U-35 사유) |

- objective는 4개 모두 `{"minimize": "power_uA"}`.
- GBW·PM은 two_stage/nmcnr에서 spec 입력(보상 설계 입력)이지 constraint 판정 항목이 아니다. current_reuse만 `parasitic_pm_deg` 제약이 있다.
- 그 밖 library 파일(엔진 4회로 밖): common_gate_amplifier, ngcc_3stage_ff, pushpull_follower_buffer, sf_pushpull_output_opamp, two_stage_ota_sf, _TEMPLATE.
- spec 정본 진입점: `workspaces/run_harness.py` `SPECS`/`canonical_spec()`/`run()`.

## 2. 전체회로 진입점 실행 결과 (`workspaces/run_harness.py <key>` = `optimize_full_circuit_budget()` + 레이아웃 파이프라인, 4개 병렬 실행)

진입점: `skills/analog-gmid-design/assets/sizing_recipe.py:9074 optimize_full_circuit_budget(topology_path, spec, grid_points_per_theta, search_method, slsqp_kwargs, stop_after_sizing)`. 호출 설정은 run_harness.py `SPECS`(floorplan_target 자동 추가).

### 2.1 two_stage_ota -- 실패 (11.3s)
첫 theta 평가에서 즉시 ValueError(sizing_recipe.py:7079 `_hr_verify_group_kvl_sum`):
```
ValueError: 'stage1_out' 그룹의 VDS 합(2.37965V)이 vdd(1.8V)와 불일치(diff=+0.579654V) -- KVL(직렬 branch 전압강하 합=vdd)이 깨졌다. 소자별 값: M4=0.9172, M2=0.9, refs(M5=0.5625). 이 그룹의 소자들이 서로 다른 경로(compensation/metric_stage_budget/gm_target_convention/headroom_role)로 각자 독립적으로 vds를 받으면 이런 불일치가 생길 수 있다 -- topology.json의 device_roles/theta feeds를 확인할 것
```
호출 경로: optimize_full_circuit_budget:9217 -> _evaluate:8636 `_resolve_vertical_group` -> 7197 -> 7105 -> 7079. W/L 출력 없음. (HEAD에 남아 있는 workspaces/two-stage-ota-report/two_stage_ota.instance.json 은 과거 실행 산출물)

### 2.2 current_reuse_telescopic_ota -- 완주 (146.2s, SLSQP 3 start, 자유변수 8개)
- SLSQP: start1 success(iters=2, 7.1s), start2·3 `Positive directional derivative for linesearch` 실패(각 ~57s).
- 51소자 전부 W/L/ID/vds/vsb/gm_id/gm/gds 출력, instance.json·report.html 저장.
- metrics(theta*): power_uA=231.17, area_um2=806.9, gain_db(gain_stages_sum)=61.56, gain_full_circuit_db(MNA)=67.08, cmrr_estimate_db=72.55, psrr_estimate_db=72.49, mismatch_sigma_mV=1.09, mirror_ratio_error_mV=3.19, classab_centering_dev_v=0.1477, parasitic_pm_deg=75.02, supply_current_uA=82.02, kcl_residual_uA=4.19, mirror_ratio_error_pct=7.13, stack_headroom_slack_v=0.0.
- 선언 제약 7건 전부 만족(gain>=54, mismatch<=5, cmrr>=60, psrr>=60, mirror_ratio_error_mV<=5, classab<=0.15, parasitic_pm>=70).
- floorplan_ok=True(aspect 1.138, density 0.998), run_full_circuit_audit.ok=True, coverage.ok=True.
- **audit_ok=False**: box-shape 행폭비 10.13>1.5, 필수 kind common-centroid FAIL 다수(M4a/M4b, M3a/M3b, M11b/M20b, M14a/M23a, M9a/M18a, M9b/M18b, M37a/M37b 등) -- 레이아웃 매칭 단계 미해결.
- 관찰: power_uA(모든 소자 ID 단순합 231uA)와 supply_current_uA(82uA)가 2.8배 다르다 -- 목적함수 power_uA는 공급전류가 아니다(3절). gain 두 추정이 5.5dB 차이. kcl_residual 4.19uA(0 아님). theta* 다수가 하한(0.02)에 붙음.

### 2.3 folded_cascode -- 완주 (20.2s, grid 400)
- 13소자 W/L 출력, instance.json 저장(report.html은 `_netlist_sections_structured` 없음으로 생략).
- theta_star: Ibg=5e-07(탐색 하한), metrics: power_uA=9.5, gain_db=41.06, pm_deg=87.2, cmrr_db=23.6, psrr_db=29.0.
- **constraints=[] 이라 '제약 없는 전력 최소화' -> Ibg가 하한으로 가는 자명해**(topology.json `_constraints_status`가 "사이징 판정 보류"로 스스로 표기). 성능 판정에 쓸 수 없음.
- audit_ok=False(box-shape 2.50>1.5, common-centroid M5/M6·M7/M8 FAIL), floorplan_ok=False(aspect 3.278).

### 2.4 nmcnr_amplifier -- 실패 (11.5s)
grid 탐색에서 평가한 조합 1개가 물리적 infeasible로 건너뛰어져 해 없음(sizing_recipe.py:9239):
```
ValueError: 모든 theta 격자점이 infeasible -- bounds/constraints를 확인하세요. 마지막 평가 조합의 theta=None, metrics=None, 위반된 제약=[]. 물리적으로 불가능해 건너뛴 조합 1개(마지막 사유: 'stage2_diode_ref' 그룹(예산 1.5V, 미해결 ['M203']): 스택 예산 1.5V 중 0.525V를 배정할 곳이 없다 -- 이 그룹은 구간 제약 소자(diode)뿐인데 전부 상한까지 올려도 예산을 못 채운다. 구간: [M203∈[0.6375,0.975]]. 이 컬럼에 선언되지 않은 소자/수동소자가 있거나 vertical_stack_id 선언이 실제 직렬 경로와 다르다는 뜻이다, theta={'Ibg_tail': 1e-05, 'r_split_M102_M103': 0.5, 'r_fold_M108_M109': 0.5, 'kcl_M104': 1.0, ...})
```
(theta 11개가 전부 고정값이라 격자점이 1개뿐.) 해당 run_harness docstring(세션36/37)의 "15소자 완주, pm 76.74도" 서술은 현재 HEAD에서 재현되지 않는다.

### 2.5 요약
| 회로 | 완주 | 시간 | 제약 만족 | audit_ok | 비고 |
|---|---|---|---|---|---|
| two_stage_ota | X | 11.3s | - | - | stage1_out KVL 불일치 ValueError |
| current_reuse_telescopic_ota | O | 146.2s | 7/7 | False | 레이아웃 매칭 FAIL |
| folded_cascode | O(자명해) | 20.2s | 제약 0건 | False | 판정 보류 회로 |
| nmcnr_amplifier | X | 11.5s | - | - | stage2_diode_ref 헤드룸 infeasible |

## 3. 전력·면적이 목적함수/결과에 있는가

- 목적함수: 4개 회로 모두 topology.json `sizing_roles.objective = {"minimize": "power_uA"}` 단일 스칼라. 다목적(전력+면적 가중/Pareto) 없음.
  - grid: sizing_recipe.py:9227 `obj_val = metrics_result[objective["minimize"]] ...`
  - slsqp: sizing_recipe.py:10654, 10939-10940 (`objective["minimize"]` 하나만 읽음)
- `power_uA` = `sum_current` = sizing_recipe.py:2848 `_metric_sum_current` -- **모든 소자 ID 단순합**(전압·레일 미반영, 직렬 스택 중복 계상). 엔진 자신이 sizing_recipe.py:4339-4349 `_metric_supply_current` docstring에서 "sum_current로는 안 된다, 파일럿 2.82배 중복"이라고 적어 두었고, 이번 실측도 231.17uA vs supply_current 82.02uA(2.82배). **올바른 metric은 있는데 목적함수에 배선되지 않음**(current_reuse만 supply_current를 결과 metric으로 계산, 나머지 3회로는 선언조차 없음). 계획서 docs/01-plan/features/gain-budget-gmid-sizing.plan.md:495 가 "7a에서 DEC-78 정의로 교체"로 미룸.
- 면적: sizing_recipe.py:2854 `_metric_sum_area` = Σ W·L(핑거 오버헤드·수동소자(Cc 등)·배선 없음). `area_um2`는 two_stage_ota·current_reuse에만 결과 metric으로 선언, **목적·제약 어디에도 안 쓰임**(4개 회로 constraints에 area 없음). 레이아웃 판정 면적(stick_diagram floorplan)은 별도로 계산되나 최적화 루프 밖. 계획서 plan.md:496(DEC-79/80)에 "목적 축 2"로만 설계.
- 스테이지 수준: `optimize_multistage()`(sizing_recipe.py:941, objective 설명 837행) 는 stage별 "power"(ID 최소) 또는 "area"(W 최소)를 고를 수 있으나 run_harness spec은 전부 `stage_objective: "power"`.
- 결론: "전력·면적 최소화 해"는 현재 **전력(그것도 중복계상 ID합) 단일 목적**만 있고, 면적은 보고용 숫자.

## 4. ngspice 연동 현황

### 4.1 있는 것
- ngspice: `C:\ngspice\Spice64\bin\ngspice_con.exe` (ngspice.exe 와 함께) -- 단일소자 .op 실행 확인(정상).
- PDK 모델: `C:\pdk\sky130_fd_pr\` (sparse-checkout: cells/nfet_01v8, cells/pfet_01v8, models/; 사용 corner `__tt.pm3.spice` + `__mismatch.corner.spice`, pfet은 `models/parameters/lod.spice` 추가). 저장소 밖.
- LUT 생성기: `skills/analog-gmid-design/assets/sky130_lut_sweep.py` (NGSPICE_EXE/PDK_ROOT 상수 하드코딩, 체크포인트 `assets/ac_sweep_checkpoints/*.npz` 120개 = nfet/pfet × L12 × VS5).
- 검증 절차 문서: `skills/analog-gmid-design/references/spice-verification-workflow.md`(소자 단위 분해 바이어스, LUT<->SPICE 교차검증 절차).
- 워크스페이스 일회성 스크립트(엔진 미배선, current_reuse 전용): `workspaces/current-reuse-telescopic-ota-report/spice/`
  - `gen_single_device.py` + `sd_*.cir` 9개: 옛 `vgs_table.json` 기반 단일소자 .op, **body를 0V로 고정(vsb 무시)**.
  - `stage3_full_circuit_ngspice_crosscheck.py` 등: 트랜지스터가 아니라 **gm/gds 고정값 VCCS 소신호 등가회로**로 엔진 MNA를 교차검증(하드코딩 GM/GDS 표) -- 트랜지스터 레벨 아님.
- `assets/_sweep.cir`: 이상 VCCS 소신호 파라미터 스윕 1개.

### 4.2 없는 것
- **엔진 출력 -> 트랜지스터 레벨 전체회로 SPICE 넷리스트 생성기 없음.** 계획서 plan.md:499 `write_spice_netlist(S1,S2,models)`/`run_ngspice_op_ac(path)` 는 설계만 있고 코드 없음(`grep "def write_spice_netlist"` 0건). 첫 실행 Phase가 7a로 잡혀 있고 현재 Phase는 3(모듈 분할 중).
- 엔진 결과에 **바이어스 전압이 없다**: instance.json `sizing`은 소자별 ID/L/W/vds/vsb/gm_id/gm/gds만 담는다. 노드전압(`propagate_node_voltages()` sizing_recipe.py:3727)·VGS(`vgs_for_gm_id` 625행)는 내부에서만 계산되고 반환/저장 안 됨. 구동되지 않는 바이어스 게이트 넷(예: folded_cascode `bias3`)의 전압, 입력 공통모드, 이상 전류원 값(folded `Ibg` value_amp=null, theta로만 결정), 수동소자 값(current_reuse R1/R2 `value_ohm: null`)이 넷리스트로 나올 형태가 아니다.
- 테스트벤치(AC 소스, 부하 CL, 폐루프/CMFB DC 수렴 조건, GBW/PM 측정 .meas) 생성기 없음.

### 4.3 지금 가능한 것 실측 -- 엔진 출력의 단일소자 .op 대조 (격리 복사본에서 임시 스크립트로)
방법: 이번 실행의 instance.json에서 소자마다 (W,L,vds,vsb,gm_id) -> LUT `vgs_for_gm_id`로 VGS 역산 -> ngspice로 Vg/Vd/Vb 고정 단일소자 .op -> ID/gm 비교. `ID_lut`(LUT가 그 VGS에서 주는 ID)도 같이 계산해 엔진-LUT 자기일관성과 LUT-SPICE 오차를 분리.

| 회로 / 핑거 실현 방식 | N | |오차 ID| 중앙값 | vsb가 LUT VS 범위(0~0.8V) 안 | 범위 안 중앙값 | 범위 안 <=10% |
|---|---|---|---|---|---|
| current_reuse / 단일 W(>90um만 5um 분할) | 51 | 12.3% | 47 | 11.3% | 21/47 |
| current_reuse / 엔진 finger_w·n_fingers 그대로 | 51 | 19.8% | 47 | 19.5% | 8/47 |
| current_reuse / 전부 ~5um 핑거(LUT W_ref와 같게) | 51 | 3.3% | 47 | 3.2% | 34/47 |
| folded_cascode / 단일 W | 13 | 33.4% | 9 | 14.3% | 3/9 |
| folded_cascode / 엔진 finger | 13 | 30.5% | 9 | 27.6% | 0/9 |
| folded_cascode / ~5um 핑거 | 13 | 15.2% | 9 | 1.7% | 5/9 |

해석(근거: 표 열 `ID_eng` 대 `ID_lut` 가 거의 모든 소자에서 같음):
1. 엔진은 자기 LUT와는 일관된다(ID_eng = ID_lut). 오차는 LUT<->실소자 차이에서 온다.
2. **LUT가 W_ref=5um 한 폭에서만 특성화돼 ID∝W 스케일링을 가정**한다(run_harness.py `_W_REF = 5e-6`). 핑거 폭을 5um 근처로 맞추면 중앙값 ~3%, 엔진이 고른 finger_w(1~40um)로 실현하면 ~20%로 나빠진다 -- sky130 폭 bin/협폭 효과. 엔진의 핑거 배정과 LUT 특성 폭이 서로 묶여 있지 않다.
3. **협폭 소자**(W<~2um: folded M3/M4 1.02um +106%, current_reuse M58 1.69um +60%, folded M10 1.12um -15%)는 5um 핑거 방식으로도 못 맞춘다.
4. **vsb가 LUT VS 축(0~0.8V) 밖**인 소자: folded M1/M2(vsb=1.6), M5(1.8), M7(-0.65, 순방향 body), current_reuse M2a/M2b(0.923), M9a/M18a(0.825) -- 외삽 구간이라 -50~-98%. folded의 vsb=1.8/-0.65는 물리적으로도 의심(노드전압 전파 결과 확인 필요).
5. 이 대조는 소자별 경계전압을 엔진 값으로 **강제**한 것이라 전체회로 .op(노드전압 자기일관성·KCL)는 검증하지 않는다.
(원자료: 격리 복사본 /c/g448/out/sd_*.txt -- 작업 후 삭제, 주요 값은 위 표에 옮김)

## 5. LUT 출처와 위치
- 파일: `skills/analog-gmid-design/assets/sky130_nfet_pfet_lut_sample.npz` (저장소에 커밋됨). run_harness.py:`LUTFILE`이 이 파일을 쓴다.
- PDK: SkyWater **sky130** `sky130_fd_pr__nfet_01v8` / `sky130_fd_pr__pfet_01v8`, corner `tt`(npz `corner='tt'`), 27C(`temp_c=27.0`), ngspice-46으로 `sky130_lut_sweep.py` 생성.
- 축: L 12점(0.15,0.2,0.25,0.3,0.35,0.425,0.5,0.7,1.0,1.5,2.5,4.0 um), VGS 49점(0~1.8V), VDS 49점(0~1.8V), **VS 5점(0~0.8V)**, 측정 폭 W=5um 단일. 필드 ID/GM/GDS/CGG/CGD/SID_1F(n,p).
- 회귀 기준: `assets/sky130_regression_reference.json` (optimize_multistage 케이스만, `tests/tools/regression_runner.py`).
- 다른 공정 LUT 없음(gf180 등 없음). corner(ff/ss)·온도 스윕 LUT 없음.

## 6. test 스위트 (격리 복사본, `--gmid-phase=3`)
- 수집: `python -P -m pytest -c tools/gates/pytest_gate.ini --rootdir=. --confcutdir=. skills/analog-gmid-design/assets/tests --gmid-phase=3 --collect-only -q` -> **1129 tests collected in 4.41s** (contracts 849, unit 242, tooling 38). `--gmid-phase` 없으면 UsageError(conftest.py:76).
- 전체 실행: **125.7s, 1112 passed / 15 xfailed / 2 failed**. 실패 2건(`contracts/test_ts6_probe_relocate.py::test_base_blob_reader_reads_the_base_tree`, `::test_moved_tool_matches_base_except_path_lines`)은 `git archive` 복사본에 .git이 없어 `git show 939f926:...`가 실패한 환경 원인(코드 결함 아님). 최근 판정 기록상 기준: 1114 passed·15 xfailed.
- 4개 회로 전체회로 실행을 끝까지 돌려 성능 스펙을 판정하는 test는 수집 목록에 없음(integration/·regression/ 디렉터리 "아직 없음", tests/README.md).

(6절 보충) `optimize_full_circuit_budget` 를 부르는 test는 모두 임시 topology(`_test_only.topology.json`, `_test_L_reconcile.topology.json`, tmp_path 생성)와 toy_lut를 쓴다(unit/test_selftest_sizing_recipe.py:199·481, contracts/test_b26pre_existing_paths.py:102·162). library 4회로를 실 LUT로 끝까지 돌리는 test는 없다 -- 그래서 2절의 two_stage_ota·nmcnr 실패가 test 스위트 green(1112 passed)과 공존한다.

## 7. 합격 시험까지 빠진 것 (근거 포함)

합격 시험 = topology.json + 스펙 + LUT -> 모든 소자 W/L·바이어스 + 전력·면적 최소화 해 -> 4개 회로 ngspice 실행 -> 영역(포화)·gain·GBW·PM 스펙 만족, 예측-SPICE 오차 허용 범위.

| # | 빠진 것 | 근거 |
|---|---|---|
| 1 | **4개 중 2개 회로가 해를 못 낸다** | 2.1 two_stage_ota: stage1_out KVL 합 2.38V≠1.8V ValueError(sizing_recipe.py:7079). 2.4 nmcnr: stage2_diode_ref 헤드룸 infeasible(9239), 자유 theta 0개 |
| 2 | **2개 회로는 성능 제약이 아예 없다** | folded_cascode·nmcnr_amplifier `sizing_roles.constraints=[]`(U-35, "7a SPICE 대조에서 다시 읽는다"). folded 실행 결과 Ibg=하한 자명해 |
| 3 | **GBW·PM이 제약으로 판정되지 않는다**(current_reuse의 parasitic_pm_deg 하나뿐) | 1절 표: two_stage/nmcnr의 GBW·PM은 spec 입력값, constraints에 없음. folded/nmcnr pm_deg는 metric만 있음 |
| 4 | **전력 목적이 틀린 metric** | objective=power_uA=sum_current(2848행) -- 실측 2.82배 중복계상. 올바른 `_metric_supply_current`(4339행)는 있으나 목적에 미배선, 3회로는 선언조차 없음. 전원 전압 곱(전력 W)도 없음 |
| 5 | **면적 최소화 없음** | sum_area(2854행)는 보고용, objective/constraints 0회 사용. 다목적(전력+면적) 구조 없음(9227/10654/10939행 단일 metric). 수동소자(Cc, CL, R) 면적 미포함 |
| 6 | **바이어스 출력 없음** | 결과는 소자별 ID/W/L/vds/vsb/gm_id만. 노드전압·VGS·바이어스 게이트 전압·이상 전류원 값이 반환/저장되지 않음(propagate_node_voltages 3727행은 내부용). folded `Ibg` value_amp=null, current_reuse R1/R2 value_ohm=null |
| 7 | **트랜지스터 레벨 넷리스트·테스트벤치 생성기 없음** | plan.md:499 `write_spice_netlist`/`run_ngspice_op_ac` 미구현(정의 0건), 첫 실행 Phase 7a(현재 Phase 3). workspace 스크립트는 VCCS 등가회로·단일소자뿐 |
| 8 | **예측-SPICE 오차 허용치 미정·미측정** | DEC-72 "7a에서 잰 abs(모델-SPICE)가 선언값" -- 아직 값 없음. N3.8 허용오차(tol_V 등) 숫자 미측정 |
| 9 | **LUT 폭 스케일링 오차 ~20%** | 4.3절: 엔진 finger_w로 실현 시 단일소자 ID 오차 중앙값 19.5%(current_reuse), 5um 핑거로 맞추면 3.2%. LUT는 W=5um 단일 특성화(run_harness `_W_REF=5e-6`). 협폭(<2um) +60~106% |
| 10 | **vsb가 LUT 범위 밖** | LUT VS 축 0~0.8V. 엔진 산출 vsb 0.825~1.8V, -0.65V 소자 다수(folded M1/M2/M5/M7, current_reuse M2a/M2b/M9a/M18a) -> 외삽, SPICE 대비 -50~-98%. VS 축 확장 LUT 재생성 또는 vsb 상한 제약 필요 |
| 11 | **포화 영역 판정이 SPICE 기준으로 없음** | 엔진의 min_vds_by_role(0.2~0.3V) 고정 하한만 있고 vdsat 대비 여유를 SPICE .op로 확인하는 경로 없음. 4.3 대조에서 vds=0.2V 소자 오차가 큼(folded M3/M10, current_reuse M2a) |
| 12 | **레이아웃 매칭 audit 미통과** | current_reuse·folded 모두 audit_ok=False(필수 common-centroid FAIL, box-shape 10.13/2.50>1.5) -- 합격 범위에 레이아웃이 포함되면 미해결 |
| 13 | **전체회로 DC 자기일관성 지표가 0이 아님** | current_reuse kcl_residual_uA=4.19, mirror_ratio_error_pct=7.13, 두 gain 추정 5.5dB 차(61.56 vs 67.08) -- SPICE 대조 전에 엔진 내부에서도 수렴 기준 불명 |
| 14 | **회로별 E2E 회귀 test 없음** | 6절 보충: library 4회로 실 LUT E2E test 0건, tests/integration·regression 디렉터리 없음 |
| 15 | corner·온도·다른 PDK 없음 | LUT는 sky130 tt/27C 한 벌. 합격 시험이 tt만이면 무관 |

현재 상태 한 줄: **실 LUT로 끝까지 W/L을 내고 선언 제약을 다 만족하는 회로는 current_reuse_telescopic_ota 1개(146s)**이고, 그마저 전력 목적이 중복계상 metric이며 바이어스 전압·SPICE 넷리스트 출력이 없어 ngspice 합격 판정 단계로 넘어갈 수 없다.
