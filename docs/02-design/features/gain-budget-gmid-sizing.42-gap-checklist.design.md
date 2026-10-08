---
template: design
version: 1.2
plan_version: 6.0
---

# gain-budget-gmid-sizing -- 42-gap-checklist (gap 분석 기준표)

> **Summary**: `bkit:gap-detector`가 설계 문서(40·41)와 구현을 대조할 때 쓰는 표다.
> - 한 행이 FR·NFR·DEC·설계 항목 하나다.
> - 열은 설계 절, 상태, 증거다. 증거는 `파일:행`, test 이름, 또는 재측정용 grep 패턴이다.
>
> **기준 시점**: master `004b7d2`(2026-10-08 재측정. f0f0fb8 이후 바뀐 것은 ng-perf-sizing 병합분뿐이다).
> - `[브랜치]` 표시: 그 브랜치에만 있는 구현이다.
> - 병합 전에는 master 상태로 세고, 브랜치에만 OK인 항목은 PART로 센다.
>
> **표기**:
> - 상태: OK / DEV / PART / MISS / N/A(원칙·폐기·옛 엔진 전용·비활성 기본값)
> - `E/` = `skills/analog-gmid-design/gmid_engine/`
> - grep 패턴은 `rg -n "<패턴>" E/`(tests 제외) 형식이다. 결과가 0이면 MISS를 유지한다. 걸린 줄이 주석·docstring·notes 문자열뿐이어도 구현 0으로 본다. 004b7d2에서 잰 그런 예는 다음과 같다.
>   - `comp_approx_gap`: `E/search/find_front.py:48`
>   - `knee`: `find_front.py:12,45,47`, `layer0_center.py:7`
>   - `model_error_`: `find_front.py:86`, `ss_constraints.py:14,24`
>   - `structure.json`: `E/graph/dc_roles.py:17`

## 1. 기능·비기능 요구

| ID | 설계 절 | 상태 | 증거 |
|---|---|---|---|
| FR-1 SP1 stage 유도 | 41 §1 | MISS | `rg "def build_s1v\|drive_kind\|stage_bfs"` 0 |
| FR-2 블록 gain 모델과 MNA 잔차 | 41 §2 | MISS | `rg "gain_residual_db\|block_local_gain"` 0. `E/metrics/CONTRACT.md:13-14` |
| FR-3 보상 먼저 | 40 §3.5, 41 §3 | PART | θ 연속 성분 + MNA 판정은 있다(`E/metrics/CONTRACT.md:555-567`). `rg "gm_req\|comp_approx_gap"` 0 |
| FR-4 `gain_budget_db` 출력과 층 0 조합 front | 41 §5 | MISS | `rg "gain_budget_db"` 0(엔진 .py). `E/search/layer0_center.py:1-37`은 시작점 하나만 낸다 |
| FR-5 노드전압 DC 정본, W0~W4 | 40 §3.7 | OK | `E/sizing/writer_plan.py:117-225`, `E/sizing/seal.py:30`, test `tests/sizing/test_writer_plan.py` |
| FR-6 V/I 상시 검증(봉인 + SPICE) | 40 §3.7, §4 | PART | 봉인은 OK. 파이프라인 SPICE 연결은 `[ng-bridge]` `pipeline/front_oracle`뿐이다 |
| FR-7 결과 재사용, 실패 기록 | 40 §3.9 | PART | `E/search/archive.py:53,56,81`, `E/search/eval_key.py:13-22`. 결함: 복원 시 float가 문자열로 돌아온다(`layer0_center._repairable` TypeError) |
| FR-8 탐색 전 달성 불가 판정 | 41 §4 | MISS | `InfeasibleTargetError` 사용처가 `E/sizing/current_basis.py:109` 하나다(KCL 충돌) |
| FR-9 명명 규칙, 옛 이름 거부 | 40 §3.1 | DEV | `E/authoring/_spec_fields.py:28-33`가 정본 이름 `input_dc_net`·`topology_hash`·`derived`를 거부한다. topology가 `direction`을 필수로 받는다(`authoring/CONTRACT.md:151-152`) |
| NFR-1 조용한 실패 불가 | 전체 | PART | `E/core/failure_errors.py:20-60`. 아카이브 문자열 복원 결함 |
| NFR-2 같은 키 재계산 0, LUT memo 상한 | 40 §7.3 | PART | `E/core/compute_block.py:77`. `rg "from_sweep\("` 호출부 0(`E/lut/lut_memo.py:34`) |
| NFR-3 IC1~IC11 강제 test | 40 §10.3 | MISS | `E/tests/contracts/` 디렉터리 없음 |
| NFR-4 결정론 | 전체 | OK | `E/core/determinism.py`. 구조 규칙 test `tests/structure/test_structure_rules.py` |
| NFR-5 스펙 맞춤, 여유 바닥 | 40 §3.6 | PART | 분해능은 있다(`E/metrics/sensitivity.py:1-15`, `MetricResult.resolution`). 모델 오차와 예산 점이 없다 |
| NFR-6 기능별 파일 | 40 §1.2 EP-3 | OK | `E/tests/structure/structure_checks.py:312-1114`(규칙 A~I) |

## 2. 결정 레지스터 (P N2.1)

폐기된 DEC-37~42는 N/A 한 행으로 묶었다.

| DEC | 설계 절 | 상태 | 증거 |
|---|---|---|---|
| 01 gain-budget-first | 41 | MISS | FR-1·2·4·8 |
| 02 보상 먼저(제약 방향) | 40 §3.5 | PART | `rg "gm_req"` 0 |
| 03 `gain_budget_db` 출력과 override | 41 §5.7 | MISS | `E/authoring/SPEC_CONTRACT.md:226-228`(로더가 `unknown_key`로 거부) |
| 04 소자별 독립 변수 | 40 §3.2 | PART | `E/sizing/theta_schema.py:6`. L 동치류 묶기와 궤도 묶기가 없다 |
| 05 전회로 MNA 판정과 잔차 | 41 §2 | PART | MNA는 OK(`E/metrics/mna_build.py:47`). 잔차 MISS |
| 06 θ = 자유 변수만 | 40 §3.7 | OK | `E/sizing/theta_schema.py:1-30` |
| 08 `value_dc_amp` 고정 | 40 §3.7 | OK | `E/sizing/current_basis.py:77,109` |
| 09 `equal_vgs` | 40 §3.2 | OK | `E/graph/rel_vgs.py`, `E/graph/gs_groups.py` |
| 10 공유 VGS를 gain 기준으로 선택 | 41 §5.5 | MISS | `rg "shared_vgs\|DEC-10"` 0 |
| 11 가장 오른쪽 근 | -- | OK | `E/lut/vgs_root.py:17` |
| 12 diode 창의 VDsat 바닥 | 40 §3.7 | PART | W4 창 VDsat 항이 결정 대기다(`E/sizing/CONTRACT.md:750-757`) |
| 13 적층 diode | 40 §3.7 | PART | `stacked_vsb` 소비자가 연기됐다 |
| 14 diode vds 구간 변수 | 40 §3.7 | OK | `E/sizing/writer_plan.py` |
| 15·64 G_vgs KVL 루프 | 40 §3.2 | PART | 탐지는 OK(`E/graph/gvgs_cycles.py:56`), 봉인 8도 OK. ratified 선택(J12-c·f)을 읽는 곳이 없다(`structure.json` 로더 MISS) |
| 16 초기 L knee | 41 §6.4 | MISS | `rg "knee"` 0 |
| 17 L 동치류 주인 | 40 §3.2 | DEV | `E/graph/CONTRACT.md:220`(`l_class` proposed), `E/sizing/block_lengths.py:7` |
| 18 role 배수 없음 | -- | OK | 구조 규칙 E·I(`structure_checks.py`) |
| 19 warm start L | 41 §5 | PART | 층 0 흡수가 MISS다 |
| 20 `value_from_constraint` | 40 §3.1 | OK | `E/authoring/spec_refs.py` |
| 21 mismatch 5 mV 출처 | 40 §9 Q3 | N/A | U-17 착수 조건 |
| 22 bisection(기본 비활성) | -- | N/A | 비활성 |
| 23 입력환산 오프셋 | 40 §3.8 | MISS | `rg "input_referred_offset"` 0 |
| 24 보상 소자 값을 엔진이 결정 | 40 §3.5 | OK | θ `capacitance`, `ss_resistance`(`E/metrics/CONTRACT.md:555-567`) |
| 25 `parasitic_pm_ss_deg` | 40 §3.8 | OK | `E/metrics/CONTRACT.md:235` |
| 26 spec 파일이 정본 | 40 §3.1 | OK | `E/authoring/spec_load.py` |
| 27 VDS-1과 VDsat | 40 §3.7 | OK | `E/lut/vdsat_query.py:20`, `E/sizing/seal_saturation.py` |
| 28 이름 없는 복구 | -- | OK | `E/search/layer0_center.py`(이름 없음) |
| 29 뷰별 0-1 BFS | 41 §1.6 | MISS | `rg "stage_bfs\|0-1 BFS"` 0 |
| 30 결과 재사용 | 40 §3.9 | PART | 아카이브 타입 결함 |
| 31 노드전압이 DC 정본 | 40 §3.7 | OK | `E/sizing/writer_plan.py` |
| 32 허용오차, 반복 상한 | 40 §3.7 | DEV | tol_I가 늘 격자 최대 gm이다(`E/sizing/seal_tolerances.py`) |
| 34 샘플 수 식 | 41 §5.8 | MISS | `rg "EvalBudget\|wall_clock_budget_s.*t_eval"` 0. 샘플 자체는 비활성 |
| 35 ports | -- | OK | 9/9 선언(`assets/library/*.topology.json`) |
| 36 pytest | -- | OK | `E/tests/` |
| 37~42 | -- | N/A | 폐기(DEC-86) |
| 43 SP1 | 41 §1 | MISS | FR-1 |
| 44 회로 해석은 공동분석 | 41 §1.10 | N/A | 원칙 |
| 45 할당 층 | 41 §5, 40 §3.6 | PART | 외층만 있다 |
| 46 패키지 구조 | -- | OK | `E/_module_map.py` |
| 47·49·51·67·76·85·86 | -- | N/A | 원칙 |
| 48 물리 정합 상시 게이트 | 40 §3.7 | OK | `E/sizing/seal.py:30`(봉인 1~9) |
| 50 gain 54 재도출 | 40 §9 Q5 | N/A | U-19 착수 조건 |
| 52 vsb | -- | OK | `E/sizing/seal_bulk_reverse.py` |
| 53 metric 서명 | 40 §5 | OK | `E/core/metric_signature.py:26`. `cm_loop`는 `[ng-cmfb-pm]`에서 계획 갱신 필요 |
| 54 SLSQP, ε-제약, 시작점 출처 | 40 §3.6 | PART | `E/search/slsqp_outer.py:99-225`, `E/search/eps_sweep.py`, `E/search/start_intervals`는 MISS. `n_starts` MISS(`E/search/CONTRACT.md:591`) |
| 55 `budget_reference_device` | -- | N/A | 태그 키(U-50) |
| 56 L5c 픽스처 | -- | N/A | 옛 엔진 전용(P N2.1 '새 엔진에는 해당하지 않는다') |
| 57 전압 이득 stage | 41 §1.6 | MISS | FR-1 |
| 58 블록 속성, 출력 구동 | 41 §1.7, 40 §3.8 | MISS | `rg "c_slew_farad\|i_out_max"` 0 |
| 59 발동표와 정지 | 41 §1.10 | MISS | `rg "rule_branch_coverage"` 0 |
| 60 레일 선언 | 40 §3.1 | OK | `E/authoring/rails.py`, `E/authoring/hidden_rails.py:16` |
| 61 벌크 기본값 | -- | OK | `E/graph/bulk_default.py` |
| 62 데이터만으로 토폴로지 추가 | 40 §1.2 | PART | 구조 규칙 E·I는 OK. 이름 전단사 metamorphic test가 없다(`tests/generality/` 6개는 일부만 다룸) |
| 63 R(u) | 41 §1.9 | MISS | `rg "buffer_bundle"` 0 |
| 65 β/σ/κ | 41 §1.9 | MISS | `rg "push_pull\|class_a"` 0 |
| 66 `rout_ss_ohm`과 잔차 | 41 §2.2 | PART | `E/metrics/rout.py`(MNA). 잔차 MISS |
| 68·69 명명과 옛 이름 거부 | 40 §3.1 | DEV | FR-9 |
| 70 AC→DC 제약과 θ 정의 | 40 §3.7 | PART | 미러 비 강제 MISS(`E/sizing/CONTRACT.md:276`). 슬루 제약 MISS |
| 71 층 0 기둥 조립 | 41 §5 | PART | (1) 가지·기둥 OK(`E/graph/columns.py`). (2)~(8) MISS |
| 72 모델 오차 선언값 | 40 §3.8 | MISS | `rg "model_error_"` 0(엔진 .py) |
| 73 기본 경로 = 층 0 + 외층 | 41 §5.9 | PART | 층 0 예산 MISS |
| 74 외층 전회로 판정 | 40 §3.8 | PART | `E/search/search_context.py:84-105`(레지스트리 밖 metric은 notes에만 남는다) |
| 75 선언으로 켜는 기능 | -- | OK | `E/authoring/spec_settings.py:34` |
| 77 (전력, 면적) front | 40 §3.6 | PART | front는 OK(`E/search/find_front.py:72-120`). 예산 점 MISS |
| 78 전력 축 | 40 §3.8 | DEV | `E/search/objectives.py:9`(Σ V·I). 기둥 대조 MISS |
| 79 면적 탐색 축·판정 축 | 40 §7.1, §3.9 | PART | `E/metrics/dc_metrics.py:18-19,80-83`. MIM은 `[ng-area-budget]`에만 있다. 판정 축의 수동소자와 재필터 MISS |
| 80 면적 눈금, bin | 41 §5.2, 40 §3.6 | PART | b_A = grid × W_min(`E/search/eps_sweep.py`). 모델 오차 항 MISS |
| 81 복합 블록 | 41 §1.9 | MISS | `rg "composite"` 0 |
| 82 새 엔진 | -- | OK | `E/` |
| 83 단일 정본 graph | -- | OK | `E/core/graph_snapshot.py:34,148-200` |
| 84 레이아웃 규칙 | 40 §3.9 | PART | MOD8 MISS(`E/convergence/__init__.py`) |
| 87 Hermite | 40 §8 R25 | DEV | VS 축이 선형이다(`E/lut/CONTRACT.md` 4.2). FC 위반 칸이 선형 폴백(`E/lut/lut_set.py:124-173`) |
| 88 ln IDu 좌표 | 40 §3.6, §8 R25 | DEV | `rg "def vgs_for_current_density"` 0. bounds를 조인다(`E/search/CONTRACT.md:573`) |
| 89 레이아웃 뒤 재검증 | 40 §3.9 | PART | `E/layout/run.py:151`(`pending_wiring`) |
| 90 SPICE 합격 정의 | 40 §4 | PART | `rg "spice_unverifiable"` 0 |
| 91 접합 용량 | 40 §3.9 | PART | 엔진 쪽 OK(`E/metrics/junction_cap.py`). `ly.diffusion` MISS(`E/layout/_ly_fields.py:22-40`) |
| 92 GB5 방법 | 40 §3.5 | PART | `gm_req`·gap MISS |
| 93 matching 분류 | 40 §3.2 | PART | `E/graph/matching_groups.py:78`. 신호 gate 2개 조건이 빠졌다(`E/graph/CONTRACT.md:538`) |
| 94 MOD2 입력 게이트 | 40 §3.1 | DEV | `E/authoring/bias_inputs.py:20`(최상위 키, 사용자 승인. 계획 문구 갱신 필요) |
| 95 탐색 방법 묶음 | 40 §3.7, §3.9 | PART | ΔA_tie가 grid²다(`E/layout/floorplan.py:83`). DEC-95 (3)은 일부만(`E/sizing/writer_plan.py:13-17`) |
| 96 nqs·mismatch 보고와 범위(잡음은 사용자 결정 2026-10-08로 범위 안) | 40 §3.8, 41 §7 | MISS | `rg "nqs_ratio\|mismatch_sigma_v"` 0. 잡음은 D-NZ1~6 |

## 3. 설계 항목 (40·41에서 새로 정한 것)

| ID | 항목 | 설계 절 | 상태 | 증거 |
|---|---|---|---|---|
| D-GB0a | spec 필드 `gain_budget_db_override`·`driving_spec`·`symmetry_untie` | 40 §3.1 | MISS | `E/authoring/SPEC_CONTRACT.md:226` |
| D-GB0b | `cm_sense_elements`, `measurement_load` | 40 §3.1 | PART(브랜치) | `[ng-cmfb-pm]`, `[ng-area-budget]` |
| D-GB1a | `structure.json` 로더와 status 전이 | 40 §3.2 | MISS | `rg "structure.json"` 0(엔진 .py) |
| D-GB2a | 뷰 수집 | 41 §1.1 | MISS | `rg "def build_s1v"` 0 |
| D-GB2b | 뷰별 교류접지 | 41 §1.2 | PART | 정적 부분만 있다(`E/graph/ac_ground_static.py`) |
| D-GB2c | 도달성, 순방향 | 41 §1.3 | MISS | `rg "forward_nets"` 0 |
| D-GB2d | 셀 분류 | 41 §1.4 | MISS | `rg "diode_load"` 0 |
| D-GB2e | 구동 종류(tap 포함) | 41 §1.5 | MISS | `rg "drive_kind"` 0 |
| D-GB2f | 0-1 BFS, stage | 41 §1.6 | MISS | -- |
| D-GB2g | 블록, 차동 블록 키, 극점 노드 | 41 §1.7 | MISS | `rg "pole_nodes"` 0 |
| D-GB2h | 루프, 끊는 점, 극성, 열거 상한, U-24·CM 대응 | 41 §1.8 | MISS | `rg "undeclared_loop_constraint\|cycle_enumeration_over_budget"` 0 |
| D-GB2i | R(u), 출력 방향, 복합 블록 | 41 §1.9 | MISS | -- |
| D-GB2j | declared 대조, 발동표 | 41 §1.10 | MISS | -- |
| D-GB3 | 결합 변수, 기둥↔블록 매핑 | 40 §3.3 | MISS | `rg "column_block_map"` 0 |
| D-GB4a | LUT 곡선 검사 → 해법 매핑 | 41 §4.1 | PART | `E/lut/lut_set.py:124-173`, `E/lut/curve_check.py:37`(분류만 있음) |
| D-GB4b | 블록 gain 상한(격자 전수, 미상) | 41 §4.2 | MISS | 재료 `CurveRow.gm_gds_max`(`E/lut/lut_types.py:384`) |
| D-GB4c | Σ 판정 | 41 §4.3 | MISS | -- |
| D-GB4d | 인증된 면적 하한 | 41 §4.4 | MISS | -- |
| D-GB4e | 구조·수치 DOF | 41 §4.5 | MISS | `rg "DofReport"` 0 |
| D-BM | 블록 국소 모델, 잔차, 결합 잔차 측정 | 41 §2 | MISS | -- |
| D-SG | 감도 게이트 | 40 §3.8 | MISS | `E/metrics/sensitivity.py`는 다른 양을 다룬다 |
| D-L0a | 활성 조건 | 41 §5.1 | MISS | -- |
| D-L0b | bin | 41 §5.2 | MISS | -- |
| D-L0c | 국소 후보 생성 | 41 §5.3 | MISS | -- |
| D-L0d | 국소 front | 41 §5.4 | MISS | -- |
| D-L0e | 조립(DEC-10 포함) | 41 §5.5 | MISS | -- |
| D-L0f | 조합 DP | 41 §5.6 | MISS | -- |
| D-L0g | 출력, override | 41 §5.7 | MISS | -- |
| D-L0h | 평가 예산 `EvalBudget` | 41 §5.8 | MISS | -- |
| D-L0i | 외층 인계, 근방 반경 | 41 §5.9 | MISS | -- |
| D-SIa~f | 출발 구간 6.1~6.6(1/f L 하한 `iv_noise.py` 포함, 잡음은 범위 안) | 41 §6 | MISS | `rg "start_intervals"` 0 |
| D-LUTc | LUT 곡선 `ft_curve` 등 | 40 §2.3 | MISS | `rg "def ft_curve"` 0 |
| D-OR1 | C10 한계 사이클 = unstable FAIL | 40 §4 | DEV | `[ng-oracle-early]` 계약 L42-54, `tools/spice_oracle/tests/test_oracle_c10_stability.py:710` |
| D-OR2 | 개루프 RHP: Nyquist Z와 과도로 판정(Z 구현 전에는 과도만) | 40 §4-5·7 | DEV | `tools/spice_oracle/README.md:516` |
| D-OR3 | `.pz` P 계수, 1+L 위상 펼침 N, 표본 세분 | 40 §4-6 | MISS | `rg "\.pz" tools/spice_oracle` 0 |
| D-OR4 | 한계 사이클의 안정 fixture 불변 확인, 고Q 표시 | 40 §4-2 | MISS | -- |
| D-CM | CM 루프 1·2·3·5 | 40 §5 | PART(브랜치) | `[ng-cmfb-pm]` |
| D-CM4 | 결정 A는 척도와 무관하게 위반, 1 dB 대체 제거 | 40 §5 | DEV | `[ng-cmfb-pm] E/search/ss_constraints.py` `_cm_level_violation` |
| D-CMR | CM 감지 저항 최소 R(사용자 결정 R1·R2 (b)) | 40 §3.5 | MISS | -- |
| D-SYa | 완전 정준 라벨링 | 40 §6 | PART(브랜치) | `[ng-layer0-canon]` 49283c6 `E/sizing/struct_canon.py`. master에는 1-WL만 있다(`E/sizing/struct_colour.py:1-15`). 위치를 `graph`로 옮겨야 한다 |
| D-SYb | 궤도 θ 묶기와 해제, `orbit_matching_crosstab`, diff_pair 궤도 검사 | 40 §6 | PART(브랜치) | `[ng-layer0-canon]` `E/search/orbit_ties.py`, `tie_expand.py`, `human.search.untie_orbits`. 대조 표는 MISS |
| D-SYc | 수동소자를 방향 없이 다루는 라벨링과 부호 있는 전류 묶기 | 40 §6-7 | DEV | 브랜치 실측에서 9회로 모두 묶기가 비활성이다. 사용자 결정 Q12 대기 |
| D-SYd | folded_cascode·two_stage_ota front 회귀 추적 | 40 §6-6 | MISS | `tests/regression` 없음 |
| D-NS | 시간과 무관한 계수 예산 N_S, `structure_count_budget` | 41 §0 | MISS | `rg "count_budget"` 0 |
| D-NM | 비단조 축 세분(미러 비·전류 배율·저항), 저항 컨덕턴스 격자 | 41 §4.2 | MISS | -- |
| D-LS | `size_and_seal_local` 국소 봉인 인터페이스 | 41 §5.3 | MISS | `rg "size_and_seal_local"` 0 |
| D-DN | 주극점 노드를 구조로 판정 | 41 §6.3 | MISS | -- |
| D-NZ1 | 잡음 spec 제약 어휘(`noise_in_density_ss_v_rthz`, `noise_in_integrated_ss_v`), 단위 `v_rthz`·`v` | 41 §7.1 | MISS | `E/core/units.py`에 없음 |
| D-NZ2 | LUT 잡음 열(`SID_TH`, `SID_FL1`, `FL_EXP`)의 새 버전 파일, 생성기 `.noise` 모드, `noise_params` | 41 §7.2 | MISS | `rg "noise_params"` 0. 옛 `SID_1F`는 읽지 않는다 |
| D-NZ3 | adjoint 잡음 해석, 소자별 기여, 분해능 | 41 §7.3 | MISS | `rg -i "noise" E/metrics` 0 |
| D-NZ4 | 잡음 제약 행 | 41 §7.4 | MISS | -- |
| D-NZ5 | 열잡음 gm 하한, 1/f L 하한 | 41 §7.5, §6.4-3 | MISS | -- |
| D-NZ6 | 오라클 `.noise` 대조 | 41 §7.6 | MISS | `rg "\.noise" tools/spice_oracle` 0 |
| D-AR1 | 면적 예산 행, MIM, 측정 부하 제외, S-3b 닫힘 | 40 §7.1 | PART(브랜치) | `[ng-area-budget]` 538eeab `E/search/area_decl.py` |
| D-AR2 | 예산을 지키는 출발점, W 타당성 | 40 §7.1 | MISS | -- |
| D-AR3 | front가 없는 회로의 원인 보고 | 40 §7.1 | MISS | -- |
| D-SC | 판정 단위와 풀이 단위의 척도화 | 40 §7.2 | DEV | `[ng-area-budget] E/search/slsqp_outer.py`(상수 곱) |
| D-BP | 예산 점 풀이 | 40 §3.6 | MISS | `E/search/CONTRACT.md:537` |
| D-ST | `n_starts`, L-c 분지 | 40 §3.6 | PART | `E/search/eps_sweep.py:4` |
| D-EPS | ε 간격 = DEC-80 bin 폭과 점 예산 | 40 §3.6 | PART | `E/search/eps_sweep.py:1-14` |
| D-AC | 타입 있는 S3·실패 캐시 레코드 | 40 §3.9 | DEV | `layer0_center._repairable` TypeError |
| D-LY1 | ΔA_tie 식 | 40 §3.9 | DEV | `E/layout/floorplan.py:83` |
| D-LY2 | LY5 즉시 완화 제거 | 40 §3.9 | DEV | `E/layout/CONTRACT.md:217,306-311` |
| D-LY3 | `ly.diffusion` | 40 §3.9 | MISS | `E/layout/_ly_fields.py:22-40` |
| D-LY4 | 판정 축 면적에 수동소자 포함 | 40 §3.9 | MISS | `E/layout/floorplan.py:30-84` |
| D-M8 | MOD8 수렴과 재필터 | 40 §3.9 | MISS | `E/convergence/__init__.py` |
| D-M9 | MOD9 결과 JSON | 40 §3.9 | MISS | `E/report/__init__.py` |
| D-M10 | `run_gmid_design_pipeline` | 40 §3.9 | MISS | `E/pipeline/__init__.py`. 일부가 `[ng-bridge]`에 있다 |
| D-PF1 | `LutMemo.from_sweep` 배선 | 40 §7.3 | PART | `E/lut/lut_memo.py:34`, 호출부 0 |
| D-PF2 | tol_V 디스크 캐시와 정리 | 40 §7.3 | PART(브랜치) | `[ng-tolv-cache] E/lut/table_cache.py:217,230-254` |
| D-GB7a | L 동치류의 L 공유 | 40 §3.2 | DEV | `E/graph/CONTRACT.md:220` |
| D-GB7b | 미러 비율 강제 | 40 §3.7 | MISS | `E/sizing/CONTRACT.md:276` |
| D-GB7c | DEC-95 (3) 전체 순서 | 40 §3.7 | PART | `E/sizing/writer_plan.py:13-17` |
| D-GB7d | W_request 고정 W | 40 §3.7 | MISS | `E/sizing/block_widths.py:9` |
| D-GB8a | `ls`, 스윙, ICMR | 40 §3.8 | MISS | -- |
| D-GB8b | nqs, mismatch 보고 | 40 §3.8 | MISS | Pelgrom 계수가 선행되어야 한다 |
| D-GB8c | `verified_by`, 모델 오차, `spice_unverifiable` | 40 §3.8 | MISS | -- |
| D-IC | IC1~IC11 계약 test | 40 §10.3 | MISS | `E/tests/contracts/` 없음 |
| D-T | test 폴더 regression, oracles, perf | 40 §8 R26 | MISS | `E/tests/` |

## 4. 상태 집계

기준은 master이고, 브랜치에만 OK인 항목은 PART로 센다.

| 구분 | 행 수 | OK | DEV | PART | MISS | N/A |
|---|---|---|---|---|---|---|
| FR·NFR | 15 | 3 | 1 | 6 | 5 | 0 |
| DEC | 81 | 24 | 7 | 26 | 16 | 8 |
| 설계 항목 | 84 | 0 | 9 | 12 | 63 | 0 |
| **합계** | 180 | 27 | 17 | 44 | 84 | 8 |

센 방법:
- D-SIa~f는 6행으로 센다.
- DEC 표에서 '37~42', '47·49·51·67·76·85·86'은 각각 1행이다.
