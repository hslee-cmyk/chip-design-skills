---
template: design
version: 1.8
plan_version: 6.7
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
| FR-9 명명 규칙, 옛 이름 거부 | 40 §3.1 | DEV | 정본 이름 거부는 U5에서 고쳐졌다(bd19cc6 `_spec_fields.py:28`). 남은 것: topology가 `direction`을 필수로 받는다(`E/authoring/ports.py:22,57-59`). 설계 = role 유도·`direction` 거부·옛 이름 표 ∩ 정본 = ∅ test(사용자 승인(2026-10-12 P), P-4) |
| NFR-1 조용한 실패 불가 | 전체 | PART | `E/core/failure_errors.py:20-60`. 아카이브 문자열 복원 결함 |
| NFR-2 같은 키 재계산 0, LUT memo 상한 | 40 §7.3 | PART | `E/core/compute_block.py:77`. `rg "from_sweep\("` 호출부 0(`E/lut/lut_memo.py:34`) |
| NFR-3 IC1~IC11 강제 test | 40 §10.3 | MISS | 패키지별 test 폴더(R26 현행 체계 유지)에서 `rg "def test_ic"` 0 |
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
| 12 diode 창의 VDsat 바닥 | 40 §3.7-6 | PART | W4 창 VDsat 항이 결정 대기다(`E/sizing/CONTRACT.md:750-757`) |
| 13 적층 diode | 40 §3.7-7 | PART | `stacked_vsb` 소비자가 연기됐다 |
| 14 diode vds 구간 변수 | 40 §3.7 | OK | `E/sizing/writer_plan.py` |
| 15·64 G_vgs KVL 루프 | 40 §3.2 | PART | 탐지는 OK(`E/graph/gvgs_cycles.py:56`), 봉인 8도 OK. ratified 선택(J12-c·f)을 읽는 곳이 없다(`structure.json` 로더 MISS) |
| 16 초기 L knee | 41 §6.4 | MISS | `rg "knee"` 0 |
| 17 L 동치류 주인 | 40 §3.2 | DEV | `E/graph/CONTRACT.md:220`(`l_class` proposed), `E/sizing/block_lengths.py:7` |
| 18 role 배수 없음 | -- | OK | 구조 규칙 E·I(`structure_checks.py`) |
| 19 warm start L | 41 §5 | PART | 층 0 흡수가 MISS다 |
| 20 `value_from_constraint` | 40 §3.1 | OK | `E/authoring/spec_refs.py` |
| 21 mismatch 5 mV 출처 | 40 §9 Q3, §9.2 | MISS | 사용자 결정 2026-10-08 Q3로 닫힘: 파일럿 5 mV → `offset_in_sigma_mv <= 3.3`(`user_spec`), two_stage·two_stage_sf 5 mV 폐기 → 가드. spec 미반영: `assets/library/current_reuse_telescopic_ota.sizing_spec.json:215`, `two_stage_ota.sizing_spec.json:71`, `two_stage_ota_sf.sizing_spec.json:62`에 옛 `mismatch_sigma_mv`가 남아 있다 |
| 22 bisection(기본 비활성) | 40 §3.10.8 | MISS | 기본 비활성이지만 켜기 경로(`optional_stages` → `achievable_metric_bound(mode="bisect")`)가 설계됐다(사용자 승인(2026-10-12 P), P-13). `rg "achievable_metric_bound"` 0 |
| 23 입력환산 오프셋 | 40 §3.8-8 | MISS | Q3(2026-10-08)로 정의 대체: 입력쌍 gm 가중 RSS → 모든 MOS의 MNA 전달(`offset_in_sigma_mv`). `rg "offset_in_sigma\|input_referred_offset"` 0 |
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
| 47·49·51·76·85·86 | -- | N/A | 원칙 |
| 67 DC/AC 영역 원칙(영역 표기, `ss`·`ls`는 봉인 통과 점에서만, 봉인 전 AC 값은 상한·추정 표기) | 40 §3.7, 41 §0, EP-7 | PART | 관계 엣지 `domain`(`E/graph/s1_values.py:298`)과 `MetricSignature.domain`(`E/core/metric_signature.py`)은 있다. 모든 규칙·필드·게이트의 영역 표기를 검사하는 장치와 봉인 전 AC 값의 상한·추정 표기는 확인되지 않았다(2026-10-08 사용자 질문으로 원칙 묶음에서 분리) |
| 48 물리 정합 상시 게이트 | 40 §3.7 | OK | `E/sizing/seal.py:30`(봉인 1~9) |
| 50 gain 54 재도출 | 40 §9 Q5 | N/A | U-19 착수 조건 |
| 52 vsb | -- | OK | `E/sizing/seal_bulk_reverse.py` |
| 53 metric 서명 | 40 §5 | OK | `E/core/metric_signature.py:26`. `cm_loop`는 `[ng-cmfb-pm]`에서 계획 갱신 필요 |
| 54 SLSQP, ε-제약, 시작점 출처 | 40 §3.6 | PART | `E/search/slsqp_outer.py:99-225`, `E/search/eps_sweep.py`, `E/search/start_intervals`는 MISS. `n_starts` MISS(`E/search/CONTRACT.md:591`) |
| 55 `budget_reference_device` → 기둥 흡수, `budget_ref` 엣지 없음(태그 키는 읽지 않는다, U-50. 비공유 옛 선언 4건은 J8 엔진 유도. 사용자 결정 2026-10-12 "다로 해") | 40 §3.2·§3.7-8 | N/A | 구현 측정만(40 §3.7-8): 대상 = 노드 공유 옛 선언 5건(파일럿 M9a→M10, M9b→M8, M18a→M19, M18b→M17, M60→M66), 나머지 8회로 대상 0건 보고, 비공유 4건 J8 제외. 각 대상에서 (a) 노드 n writer 정확히 1개(티어·블록), (b) X·Y 같은 S1 기둥 id, (c) \|B_X − ((V_top − V_bot) − \|VDS(Y)\|)\| ≤ tol_V(N3.6). 엣지 없음은 as-built와 같다(`E/graph/CONTRACT.md:226`, 문구 정정은 아래 후속 항목) |
| 56 L5c 픽스처 | -- | N/A | 옛 엔진 전용(P N2.1 '새 엔진에는 해당하지 않는다') |
| 57 전압 이득 stage | 41 §1.6 | MISS | FR-1 |
| 58 블록 속성, 출력 구동 | 41 §1.7, 40 §3.8 | MISS | `rg "c_slew_farad\|i_out_max"` 0 |
| 59 발동표와 정지 | 41 §1.10 | PART | coverage 파일은 R7 축소 유지로 승인됨(2026-10-08). S1 지원 밖 정지는 있다(`E/graph/CONTRACT.md:352-362`). SP1 `기록만` 분기 정지는 FR-1과 함께 MISS |
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
| 78 전력 축 | 40 §3.8 | PART | Σ V·I는 결정 Q6(2026-10-08)과 일치한다(`E/search/objectives.py:9`). 기둥 대조 MISS. DEC-78 문구 정정 필요 |
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
| 96 nqs·mismatch 보고와 범위(잡음은 사용자 결정 2026-10-08로 범위 안, (2)는 Q3로 A_eff·offset metric) | 40 §3.8, 41 §6.4-2, §7 | MISS | `rg "nqs_ratio\|offset_in_sigma\|mirror_ratio_sigma"` 0. 잡음은 D-NZ1~6, 미스매치는 D-MM1·2, D-OF1~3, D-MR |

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
| D-L0c | 국소 후보 생성(역산 우선 (a)~(d), 후보 집합) | 41 §5.3.1~5.3.6, §5.3.8~5.3.11 | MISS | U15 as-built는 축 곱 후보(41 v1.5 이탈, v1.6에서 폐기) |
| D-L0c2 | L 초기 목표·knee·feasible_L_window·동치류 격자(LR5) | 41 §5.3.7 | MISS | -- |
| D-L0d | 국소 front | 41 §5.4 | MISS | -- |
| D-L0e | 조립(DEC-10 포함) | 41 §5.5 | MISS | -- |
| D-L0f | 조합 DP | 41 §5.6 | MISS | -- |
| D-L0g | 출력, override | 41 §5.7 | MISS | -- |
| D-L0h | 평가 예산 `EvalBudget` | 41 §5.8 | MISS | -- |
| D-L0i | 외층 인계, 근방 반경 | 41 §5.9 | MISS | -- |
| D-P1 | 층 0 정지 = DEC-71 (3) 경로 열거 예산 초과와 후보 격자 Π > N_S 둘뿐, N_T,i는 평가 상한(닿으면 절단 + `layer0_candidates_truncated` + 블록 front '추정'), 좌표 훑기 폐기(P-1, U-63 (가)) | 41 §5.3.11 | DEV | U15 as-built `local_candidates.py`가 Π > 몫이면 강결합 그룹 좌표 훑기를 한다 |
| D-P9 | 9회로 축소 격자 전수 대조(전회로 MNA, 축별 최적값 차·같은 ε front 점 차 ≤ max(분해능, 모델 오차))(P-9, N3.7·NFR-5) | 41 §9 | MISS | 축소 격자 정의는 41 §5.12.5 PQ1 |
| D-P15 | 이득 블록과 섞인 회로의 버퍼 블록 rout 국소 제약·면적 bin DP 단계(P-15, DEC-71 (3)) | 41 §5.1·§5.6 | DEV | U15 as-built는 섞인 회로의 버퍼를 기준점 gain 상수항으로만 넣는다 |
| D-FV1 | 이식 투영 = 값 기반 정준 사상, `fixed`는 extras로만(국소 → 조립 이식) | 40 §2.4.4 | MISS | `rg "def graft"` 0 |
| D-FV2 | d/s 자기 맞바꿈 → `unsupported_rule_branch`(`ds_self_swap_zero_current`), toy test | 40 §6-8 | MISS | `rg "ds_self_swap_zero_current"` 0 |
| D-FV3 | DEC-12 diode 창 VDSAT 바닥·명시 실패, DEC-13 적층 diode 2변수 공동 풀이 | 40 §3.7-6·7 | PART | `E/sizing/CONTRACT.md:750-757`(W4 창 VDsat 대기) |
| D-FV4 | 단위 보고 `broken_tests`·`criteria_weakened`, `--profile`, DEC-51 공유 블록 전후 대조 도구 | 40 §3.10.8, §10.4 | MISS | `rg "criteria_weakened\|--profile"` 0 |
| D-FV5 | 정밀 경로 선언 정지(U-66 결정), 복합 블록 상한 N_S(U-65 결정) | 40 §3.10.8·3.10.11 | MISS | `rg "precise_path_not_implemented"` 0 |
| D-FV6 | U-23·U-33 측정 도구 `tools/compare_paths.py` | 40 §3.10.10 | MISS | 파일 없음 |
| D-FV7 | U-67(사용자 결정 2026-10-12 "U-67은 (나)로"): L 혼합 interdigitation 행 대칭 검사(`interdigitation_not_mirror_symmetric`), `ly.lod` finger별 sa·sb·sd → 오라클 넷리스트, WPE·PSE 제외 | 40 §3.9, §3.10.8, §4 | MISS | `rg "ly.lod\|interdigitation_not_mirror"` 0 |
| D-K1 | 41 §6.7 KVL 고리 출발 제약: K-1 공동 선택 순서(위반 최소 → max-min → 위치 합 최대), 실행 불가 시 올린 묶음 상한 반분 재풀이(최대 steps+1), `StartConflict(kvl)`, PQ5(출발 단계 A8에도 등식), K-3 `input_tie` 폐기 | 41 §6.7 | MISS | `rg "kvl_choice"` 0 |
| D-K2 | 41 §7.5 β·C_eff 입력 배선(feedback 절단, C_eff 노드), 비대칭 귀환 계수 '추정'(U-70), N_in = Σγ_k·gm_k/(γ_avg·G_half)(K-2 결정) | 41 §7.5 | MISS | U13 열린 항목 `feedback_factor_beta_unavailable` |
| D-C4 | 잡음 B 평탄(plateau) 규칙(피드스루 + 이웃 점 일치), 칸별 적응 재측정 구현 단위(미상·엇갈림·계단형 칸, 로그 이분, 상한 K_max, noise r2) -- 시점 = graph 재작성 ①~③ 뒤, U16 전(C-4) | 41 §7.2 | PART | plateau는 as-built `noise_planes.py`와 일치, 재측정 단위 없음 |
| D-D1 | d/s 맞바꿈 궤도를 넘는(KCL 유도) 전류 묶음 상자 = 구성원 상자 교집합, 비면 거부 `tied_current_box_empty`(U-61 D-1). 같은 궤도 안 불일치는 `tied_orbit_bounds_differ` | 40 §6-8 | MISS | as-built `search_domain`은 `tied_orbit_bounds_differ`로 거부 |
| D-G1 | IC11 픽스처: 거부 = 합성 음전위 레일·pushpull(supply_nets 삭제), 동등 = two_stage_ota 2레일·pushpull 3레일 | 40 §3.10.8, §10.3 | MISS | `rg "def test_rail_origin_shift_invariance"` 0 |
| D-G2 | 문자열 값 안 옛 이름 test, `human.objective` 형식·`duplicate_axis_budget`, spec `origin` 규칙(U-04 결정) | 40 §3.1 | MISS | -- |
| D-G3 | LY1 쌍 전류비 규칙(U-71 결정, 사용자 결정 2026-10-12 "U-71승인") | 40 §3.10.3 | MISS | -- |
| D-G4 | 보상 단 폴백(U-51 결정): SLSQP maxiter 미수렴 시작점만 보상 단 GB5 고정 재풀이, `compensation_fixed_fallback` 기록·'추정', 9회로 빈도 보고 | 40 §3.6 | MISS | `rg "compensation_fixed_fallback"` 0 |
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
| D-SYb | 궤도 θ 묶기와 해제, `orbit_matching_crosstab`, diff_pair 궤도 검사(review 조건은 D-SYe) | 40 §6 | PART(브랜치) | `[ng-layer0-canon]` `E/search/orbit_ties.py`, `tie_expand.py`, `human.search.untie_orbits`. 대조 표는 MISS |
| D-SYc | 수동소자를 방향 없이 다루는 라벨링과 부호 있는 전류 묶기(사용자 결정 2026-10-08 'b') | 40 §6-7 | DEV | 브랜치 실측에서 9회로 모두 묶기가 비활성이다(수동소자를 방향 있는 것으로 다룸) |
| D-SYd | folded_cascode·two_stage_ota front 회귀 추적 | 40 §6-6 | MISS | `tests/integration`에 없음 |
| D-SYe | diff_pair review (나'): 두 멤버가 다른 궤도이고 (a) 출력 포트가 `differential_output_p/n` 쌍, (b) 그 쌍의 두 gate가 차동 입력 포트 p/n일 때만 `review_needed`, 나머지는 crosstab 기록만. 9회로 review 0, 거부 test = 파일럿 넷 하나 비대칭 합성 회로 | 40 §6-5, §10.2 | MISS | `rg "orbit_matching_crosstab"` 0 |
| D-SYf | 전류 기저 열 순서 키 = (궤도 비자명 먼저, `dc_colour`, 이름), `current_basis`가 `graph/s1: orbits` 읽음. 파일럿 묶음/변수 29/38(M1a~M1b, M19~M10), 나머지 8회로 무동작 | 40 §6-3·§6-8 | MISS | `E/sizing/current_basis.py:8` 열 순서 = (`dc_colour`, 이름), orbit 읽기 0 |
| D-NS | 시간과 무관한 계수 예산 N_S, `structure_count_budget` | 41 §0 | MISS | `rg "count_budget"` 0 |
| D-NM | 비단조 축 세분(미러 비·전류 배율·저항), 저항 컨덕턴스 격자 | 41 §4.2 | MISS | -- |
| D-LS | `size_and_seal_local` 국소 봉인 인터페이스 | 41 §5.3 | MISS | `rg "size_and_seal_local"` 0 |
| D-DN | 주극점 노드를 구조로 판정 | 41 §6.3 | MISS | -- |
| D-NZ1 | 잡음 metric 어휘(`noise_th_in_v2hz`, `noise_fc_in_hz`, `noise_excess_th`, `noise_out_int_vrms`), 단위, 회로별 선언(Q11), `noise_testbench` | 41 §7.1 | MISS | `E/core/units.py`에 없음 |
| D-NZ2 | LUT 잡음: v2 `SVG2_*` + 저주파 점 r1 새 파일, A/B/EF 분해, `noise_params`, 생성기 `.noise` 모드 | 41 §7.2 | MISS | `rg "noise_params"` 0. 옛 `SID_1F`는 읽지 않는다 |
| D-PG | Pelgrom slope를 PDK mismatch 파일에서 읽고(bin별 slope 이름, pfet L < 0.5 µm `vth0_slope1` 7.356e-3 보정) ngspice 소자 쌍 MC로 단위 확인 | 41 §6.4-2 | MISS | `E/core/pdk_decl.py`에 없음. `rg "vth0_slope" E/`는 spec 옛 키 거부 표 한 줄뿐(`E/authoring/_spec_fields.py:39`) |
| D-MM1 | 유효 mismatch 계수 A_eff(전 `*_slope_spectre` 변수 RSS, toxe→Vth·약반전 voff 포함, 같은 ID에서의 ΔVGS), 옛 vth0·β 두 항 식 대체 | 41 §6.4-2 | MISS | `rg "A_eff\|mismatch_dvgs" E/` 0 |
| D-MM2 | LUT mismatch 감도 열 DVGS_k: 생성기 mismatch 모드, 새 버전 파일 `..._mismatch_r1.npz`(공유 데이터 무변경), `lut_v2_location.json` 새 항목, `tol_mismatch` LOO, `mismatch_lut_missing` 거부 | 41 §6.4-2b | MISS | `assets/sky130_lut_sweep.py:227`은 mismatch 파일을 include만 한다. 섭동 모드·감도 열 없음 |
| D-OF1 | `offset_in_sigma_mv`: 모든 MOS 게이트 오차원 → MNA adjoint 출력 전달 → 입력 환산, `offset_contrib` 표(matching 레코드는 해석용) | 40 §3.8-8 | MISS | `rg "offset_in_sigma" E/` 0 |
| D-OF2 | `offset_excess` 구조 가드(`<= √2`, 입력 셀 = S1v 첫 이득 블록 input 셀)와 출발 단계 부하 gm/ID 상한 | 40 §3.8-8, 41 §6.4-2a | MISS | `rg "offset_excess" E/` 0 |
| D-OF3 | `offset_sys_mv`(차동 = Vop − Vom, 단일 = 선언 기준, 없으면 `reference_undeclared`), 상한 = `value_from_constraint: offset_in_sigma_mv` | 40 §3.8-8 | MISS | `rg "offset_sys" E/` 0 |
| D-MR | `mirror_ratio_sigma_pct` 보고(mirror 계열 matching 그룹마다), 단위 `pct` | 40 §3.8-8 | MISS | `E/core/units.py:13`에 `pct` 없음 |
| D-SW | `swing_out_v`: 포화 기준(VDS ≥ VDSAT + tol_vdsat), 대칭 p-p, 차동 = 출력별 반폭 최솟값 × 4, 구간 레코드 | 40 §3.8-8 | MISS | `rg "swing_out" E/` 0 |
| D-ICM | `icmr_v`(레일로 자른 창 폭, 빈 창 음수)와 `icm_margin_v`(선언 입력 DC와 창 경계 거리, SP-2 대기면 `input_dc_pending`), ICMR 제약 = 폭 + 포함 | 40 §3.8-8 | MISS | `rg "icmr_v\|icm_margin" E/` 0. ngcc spec은 `{metric: pending MOD5}`(`assets/library/ngcc_3stage_ff.sizing_spec.json:87`) |
| D-Q34 | §9.2 회로별 선언(파일럿 3.3 mV·스윙 2.4 V·icm_margin, 6회로 가드, ngcc `icmr_v >= 0.6`, nmcnr `icmr_v`·`swing_out_v >= 0.5`)과 옛 이름 거부(`mismatch_sigma_mv`, `mirror_ratio_error_mv`, `mismatch_sigma_v`) | 40 §9.2, §3.1 | MISS | `assets/library/*.sizing_spec.json`(옛 이름 3개 회로), `E/authoring/SPEC_CONTRACT.md:261` S2 |
| D-GB4f | 헤드룸 달성가능성: 출력·입력·버퍼 창 상한(LUT 격자 전수, 인증/미상), 선언 제약 인증 불가 → exit 3 `headroom_unattainable`, 제약 없는 창·입력 DC 대기는 보고, 유도 기록 | 41 §4.6 | MISS | `rg "headroom_bound\|headroom_unattainable" E/` 0 |
| D-SIg | 출발 구간 Q3·Q4: 스윙·ICMR·입력 DC 예산 분할(41 §6.2), A_eff matching L 하한(절대 offset 회로만, 41 §6.4-2) | 41 §6.2, §6.4-2 | MISS | `rg "start_intervals"` 0 |
| D-OR5 | 오라클 offset Monte-Carlo(표본 수 유도, `model_error_offset_in_sigma_mv`)와 스윙·ICMR `.dc` 스윕 | 40 §10.2 | MISS | `rg "mc_mm_switch\|offset_mc" tools/spice_oracle` 0 |
| D-J34 | J 공동분석 목록 추가: 입력 DC 값(nmcnr 0 V, SP-2), sf_pushpull M6↔M8·M5↔M7 matching, 4-팔로워 버퍼 헤드룸 | 40 §9 Q7, §9.3 | MISS | 해석은 2026-10-08 결정으로 닫혔다(40 §9.3 J-D·J-E). 구현 확인은 D-J1·D-J5·D-J7 행에서 한다 |
| D-J1 | 복합 diode D1: DC 가지 걷기 정의, 묶음·기준/캐스코드 구분, 소비 셋(DC 역할 규칙 1c, 미러 입력 확장·`diode_load`, 루프 (1.6) `composite_diode_internal`). 9회로 발동 = 41 §1.13 실측 집합, 나머지 7회로 무동작 | 41 §1.12.1, §1.13 | MISS | `rg "composite_diode" E/` 0. `[u1-sp1] E/graph/drive_kind.py` `_mirror_inputs`는 단순 diode만 본다 |
| D-J2 | feedforward 셀: 주경로(D_max·slack), FF 묶음·탭·merge·B_b, 블록 분해(FF 합류는 복합 블록 아님), gain 예산은 주경로만, 경로 기여·A_decomp 잔차, `ff_ratio_candidates`·`ff_gm_ratio`, Σ 판정 FF 상한, FF 출발값 | 41 §1.12.2, §2, §4.3, §5.1, §6.5, 40 §3.8-8 | MISS | `rg "feedforward\|ff_gm_ratio" E/` 0. `[u1-sp1]`은 ngcc Vout을 복합 블록 하나로 묶는다(`composite_block_pending_ratify`) |
| D-J3 | 중첩 Miller 보상 내부 루프: 조건 (a)(b), 루프 뷰 미생성, `pm_ss_deg` 미선언이면 `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`), 전체 PM 판정의 P = 0 확인 | 41 §1.12.3 | MISS | `rg "compensation_internal" E/` 0. `[u1-sp1]` ngcc·nmcnr에서 `undeclared_loop_constraint` 정지 |
| D-J4 | 루프 극성 = 뷰의 DC 사이클 극성, 커패시터 사이클 `ac_only`, `loop_polarity_conflict`. L 동치류 주인 규칙 `main_path_signal`, name_order는 review | 41 §1.12.4·5 | MISS | `[u1-sp1] E/graph/polarity.py`(커패시터 사이클 → 0 → review), `l_classes.py`(주인 순서 3단계) |
| D-J5 | 입력 DC 정책: SP-2 (c) y_icm 창 범위, `required_input_cm_v`, sf `icm_margin_v >= 0` 제약, `buffer_window_report`, `icmr_window_short_l_bin` 경고 | 41 §4.6, 40 §3.8-8, §9.2 | MISS | `rg "required_input_cm\|short_l_bin" E/` 0. `assets/library/sf_pushpull_output_opamp.sizing_spec.json`에 `icm_margin_v` 제약 없음 |
| D-J6 | `structure.json` concept 어휘 7개(신규 5), override/confirm/고아/불일치 전이, `structure_rule_fp`, 단계 A의 사실 로드 순서·`build_s1(structure=)`·`declared_loop_cuts` 전달, 뷰 한정 `ac_ground_exception` 소비 | 40 §3.2-3, 41 §1.12.6 | MISS | `[u1-sp1] E/graph/structure_load.py`는 `drive_kind`만 소비한다. `[u1-sp1] E/pipeline/stage_a.py` `run_stage_a`는 `declared_loop_cuts`를 넘기지 않는다 |
| D-J7 | 회로별 사실 파일(`assets/library/<name>.structure.json`) 작성: U1b 병합 뒤, confirm 사실은 실측 일치 시만, rule_hash = 병합 코드의 `structure_rule_fp` | 40 §3.2-3 표 | MISS | 사실 파일 0개(작성 순서상 U1b 뒤) |
| D-J8 | 혼재 노드 구동 종류(C-1 + 보완 (가)): (i) source 쪽 소자 drain이 교류 접지·gate가 신호 노드면 follower → 전압 구동, (ii) 아니면 drain 쪽 gate가 신호 노드면 전류 구동. 9회로 발동표(옛/새/근거 `follower`\|`cascode`) = 바뀐 노드 sf N910·N1112·N1516 + folded_cascode Vg10(전류 구동), sf N17·N20 전압 구동 유지, 나머지 무동작. folded 블록·stage·극점 노드 전후 비교 | 41 §1.5-4 | MISS | as-built는 DC 역할로 가른다(`E/graph/drive_kind.py`) |
| D-J10 | 파일럿 `structure.json` `rule_hash`만 재기록(사실 불변, approval_id `user_decisions 2026-10-12 C-6 재확인`): ①-d 마지막 규칙 변경(C-1 보완 (가)·전류 기저 열 순서) 뒤 1회, 갱신 뒤 단계 A Vbias2 판정 불변 확인(달라지면 갱신하지 않고 재질의) | 40 §3.2-3 | MISS | 규칙 변경 미병합(master `8e46548`) |
| D-J9 | `structure.json` concept `l_owner`(C-3, override). nmcnr 사실 = [M104, M105] → M105(사용자 결정 2026-10-12 "C-3은 네 제안대로 해") | 40 §3.2-3, 41 §1.12.5 | MISS | `rg "l_owner"` 사실 개념 0, nmcnr 사실 파일 없음 |
| D-RA | 저항 면적: poly 시트·최소 폭·머리를 PDK 선언에 두고 Ω당 면적 계산 | 40 §7.1 | MISS | `rg "poly_res_sheet"` 0 |
| D-Q5 | Q5 승격(two_stage GBW 제약, ngcc ICMR)과 Q5b 판정 보류 표시 | 40 §9 | MISS | `assets/library/*.sizing_spec.json` |
| D-NZ3 | adjoint 잡음 해석, 소자별 기여, 분해능 | 41 §7.3 | MISS | `rg -i "noise" E/metrics` 0 |
| D-NZ4 | 잡음 제약 행 | 41 §7.4 | MISS | -- |
| D-NZ5 | 열잡음 C_eff 하한(41 §7.5 v1.6), 1/f L 하한 | 41 §7.5, §6.4-3 | MISS | -- |
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
| D-LY5 | 레이아웃 파생 값(`review_needed`·`devices`·`coverage`·`w_requests`·`w_invariant_ok`·`revalidation`) = 반환값 함수 `layout_outputs(snapshot)`(graph 필드 아님). **U16 완료 조건**: U16 결과 JSON이 설계점마다 한 번 호출하도록 배선. U16 전 프로덕션 호출처 0(test만) 사용자 승인(사용자 결정 2026-10-12 "4번 권고대로") | 40 §2.4.8, §11 U16 | MISS | `rg "def layout_outputs"` 0 |
| D-M8 | MOD8 수렴과 재필터 | 40 §3.9 | PART | `E/convergence/converge.py`(U14 구현·`E/convergence/CONTRACT.md`). 호출자(U16 `run_gmid_design_pipeline`)가 아직 없어 파이프라인 배선은 U16 몫 |
| D-M9 | MOD9 결과 JSON | 40 §3.9 | MISS | `E/report/__init__.py` |
| D-M10 | `run_gmid_design_pipeline` | 40 §3.9 | MISS | `E/pipeline/__init__.py`. 일부가 `[ng-bridge]`에 있다 |
| D-PF1 | `LutMemo.from_sweep` 배선 | 40 §7.3 | PART | `E/lut/lut_memo.py:34`, 호출부 0 |
| D-PF2 | tol_V 디스크 캐시와 정리 | 40 §7.3 | PART(브랜치) | `[ng-tolv-cache] E/lut/table_cache.py:217,230-254` |
| D-GB7a | L 동치류의 L 공유 | 40 §3.2 | DEV | `E/graph/CONTRACT.md:220` |
| D-GB7b | 미러 비율 강제 | 40 §3.7 | MISS | `E/sizing/CONTRACT.md:276` |
| D-GB7c | DEC-95 (3) 전체 순서 | 40 §3.7 | PART | `E/sizing/writer_plan.py:13-17` |
| D-GB7d | W_request 고정 W | 40 §3.7 | MISS | `E/sizing/block_widths.py:9` |
| D-GB8a | `ls`(슬루·방향별 전류), 스윙·ICMR은 D-SW·D-ICM | 40 §3.8 | MISS | -- |
| D-GB8b | nqs 보고(미스매치 보고는 D-OF1·D-MR로 대체) | 40 §3.8 | MISS | -- |
| D-GB8c | `verified_by`, 모델 오차, `spice_unverifiable` | 40 §3.8 | MISS | -- |
| D-IC | IC1~IC11 계약 test(패키지별 폴더) | 40 §10.3 | MISS | `rg "def test_ic"` 0 |
| D-T | test 폴더 체계 | 40 §8 R26 | N/A | 축소 유지 승인(2026-10-08). 현행 체계를 쓴다 |
| D-GR1 | graph 밖 저장소는 넷뿐(LUT memo·S3 기록과 색인·실행 계수·S0 수준 스냅샷 직렬화) | 40 §2.4.1 | DEV | bd19cc6 `E/search/search_context.py:65-89`(cache·cell_floors·local_seal_memo 등) |
| D-GR2 | S0 수준 층 필드화(S1v·결합 변수·GB4·출발 구간·metric 구조 입력) | 40 §2.4.2·2.4.8 | MISS | bd19cc6 `sctx.s1v`·`sctx.ach`·`sctx.start` 객체, `E/search/start_values.py:186-235` `StartContext` |
| D-GR3 | S0 수준 스냅샷 디스크 영속화(키·타입 있는 코덱·원자적 쓰기·검증), 단계 A 보고서 `s0_snapshot` 키(hit\|miss\|corrupt), `run_stage_a` PDK 선언 필수 인자, U-68 재현 판정 = 입력 파일 원본 sha + 엔진 코드 지문 | 40 §2.4.3 | MISS | `rg "snapshot_codec"` 0 |
| D-GR4 | 분할 계산 블록과 이식(graft) | 40 §2.4.4 | MISS | `rg "def graft"` 0, `E/core/compute_block.py:73-90`(블록 이름 하나의 버전) |
| D-GR5 | S3 메모리 색인·스냅샷 보존(`sctx.cache`·`local_seal_memo` 대체, G-5) | 40 §2.4.5 | DEV | bd19cc6 `E/search/kernel.py:102-121`, `E/search/local_candidates.py:141-144` |
| D-GR6 | LUT memo 순수성(`call`)·S0당 인스턴스 하나·상한 B_r(층 0 항) | 40 §2.4.6 | DEV | bd19cc6 `E/search/search_context.py:105-121`(두 번째 인스턴스, 첫 평가 버림), `E/lut/lut_memo.py:25-36,60-62` |
| D-GR7 | 수동소자 값 S2 필드(writer GB5, R = 1/Σgm 포함) | 40 §2.4.8 | MISS | bd19cc6 `E/metrics/passive_values.py:16`(함수), `E/search/kernel.py:146-150`(규칙 사본) |
| D-GR8 | tol_I = tol_V × `dc_gm`(자기 동작점, writer 1개, `ss_dev` 공용) | 40 §3.7-3, §2.4.11 | DEV | bd19cc6 `E/sizing/seal_tolerances.py:36-45`, `E/sizing/kernel_run.py:51-96` |
| D-GR9 | 값 사본 제거(`SsEvaluation`·`EvalResult`·`LayoutResult`), 레이아웃 = 설계점 필드 | 40 §2.4.7 | DEV | bd19cc6 `E/metrics/ss_types.py:79-88`, `E/search/search_values.py:146-162`, `E/layout/run.py:109` |
| D-GR10 | G-7 SearchContext = 참조 + S3 색인 + 실행 계수, `__slots__`·frozen | 40 §2.4.7 | DEV | bd19cc6 `E/search/search_context.py:51-89` |
| D-GR11 | G-8 강제 장치 4종(규칙 G 확장·설계 값 타입 위치·SC-a/SC-b lint·9회로 test) | 40 §2.4.10 | PART | bd19cc6 규칙 G = 모듈 가변·데코레이터·global만(`E/tests/structure/structure_checks.py:880-920`) |
| D-GR12 | G-10 계수(블록·분할별 grafts 포함, `perf.s0_snapshot` 포함)와 9회로·두 번째 실행 test(`test_g10_second_run_s0_zero`는 U17 단계 ②) | 40 §2.4.9 | PART | bd19cc6 `E/core/compute_block.py:30-38` `BlockStats`, `E/search/kernel.py:120-121` `recompute_same_key` |
| D-GR13 | 단계 B 층(r̂·수치 rank, 직렬화 제외), `ach.dof` = 구조 DOF만, KernelContext·SearchContext 선언 파생의 S0 수준 필드, `metrics_dc` `gate_area_m2`·`power_resolution_w`(제약 행 `constraint_rows`는 U17 ②로 이월, `unmeasured` 자리 40 §2.4.12 Q8 열림) | 40 §2.4.1·2.4.7·2.4.8 | DEV | bd19cc6 `E/search/objectives.py:31-45`, `E/sizing/s2_values.py:429-443` |
| D-GR14 | 층 0 필드(`graph/layer0: macro`·`comp_approx_gap`·`rounds`, `graph/local` 블록 범위 metric), 색인 `local`·`solved` | 40 §2.4.5·2.4.8, 41 §5.3.9·§5.3.11·§5.5 | MISS | `rg "comp_approx_gap"` 0(엔진 .py) |
| D-GR15 | 계수 소유 `RunCounters`(블록 무상태, `_evicted`·`events` 이동), LUT memo 퇴출 판정(U-60 결정 (가): 퇴출 뒤 재계산 0) | 40 §2.4.6·2.4.9 | DEV | bd19cc6 `E/core/compute_block.py:67-71`, `E/core/bounded_lru.py:38`, `E/lut/table_cache.py:199` |
| D-P2 | 소자별 폭 슬라이스(`LutAccess.w_keys` 소자 키, `w_key_of(lut, device)`), LY2 행별 finger 폭 | 40 §3.10.1 | DEV | bd19cc6 `LutAccess.w_keys` = kind 키, `convergence/place_layout` `layout_score` 최소 키 |
| D-P3 | LY5 nf → W → 완화, 종속 소자 W 고정 입력(봉인 2 판정) | 40 §3.10.2 | DEV | MOD8 gap (b)(종속 소자 W 고정 불가) |
| D-P6 | MOD8 열린 항목 닫음: 쌍 전류비 보장 규칙, `key_exclusion` 삭제, 면적 모델 오차 기록만, front 뒤 재측정 | 40 §3.10.3 | MISS | `rg "key_exclusion"` (convergence) |
| D-P7 | DEC-88 반전 수준 하한 = 연속 부등식 제약 행(bounds 조임 폐기) | 40 §3.10.4 | DEV | `search/CONTRACT.md:573`, `E/search/cell_floor.py` |
| D-P8 | DF 재발 금지 표(DF-01~37 → 계약 test → 단위) | 40 §10.3a | MISS | `rg "def test_df"` 0 |
| D-P10 | finger 피치 여유 PDK 유도(I-A12) | 40 §3.10.5 | MISS | 옛 `PROCESS_GEOMETRY["finger_pitch_overhead_m"]` = 0.0 |
| D-P11 | 최종 해 활성 제약 여유 판정·활성/비활성/보류 보고(NFR-5) | 40 §3.10.6 | MISS | front 표 `constraints[].state` 없음 |
| D-P12 | 규칙 분기 발동표 결과 JSON `rule_branches`(DEC-59) | 40 §3.10.7 | MISS | `rg "rule_branches"` 0 |
| D-P13 | 누락 항목 일괄: `dc_id_source`, tol_V 정의, 결합 잔차 쓰임(`residual_table`·`trust_limits`), LY8 3열, 근방 반경 확장, IC3·IC7·IC11, T1·T7·T8 형식, `layer0.ac_inactive`, bisection 켜기 경로, TS7 strict xfail | 40 §3.10.8 | MISS | 항목별 grep 0(`dc_id_source`, `trust_limits`, `metric_columns`, `ac_inactive`) |

## 4. 상태 집계

기준은 master이고, 브랜치에만 OK인 항목은 PART로 센다.

| 구분 | 행 수 | OK | DEV | PART | MISS | N/A |
|---|---|---|---|---|---|---|
| FR·NFR | 15 | 3 | 1 | 6 | 5 | 0 |
| DEC | 82 | 24 | 6 | 29 | 17 | 6 |
| 설계 항목 | 155 | 0 | 23 | 16 | 115 | 1 |
| **합계** | 252 | 27 | 30 | 51 | 137 | 7 |

v1.8(2026-10-13, 사용자 결정 2026-10-12 "나'로 진행해"·"1, 가로 해"·"2번 승인."·"3번 권고대로"·"4번 권고대로"): 설계 항목 4행 추가(D-J10, D-SYe, D-SYf, D-LY5, 모두 MISS -- master `8e46548`에서 잼), D-J8·D-D1·D-SYb·D-GR3·D-GR12·D-GR13 문구 갱신(상태 불변).

v1.7(2026-10-12, 사용자 결정 "다로 해"): DEC 행 55 = `budget_reference_device`의 역할을 S1 기둥이 흡수하고 `budget_ref` 엣지는 만들지 않는다(N/A 유지, 구현 단위 측정만). 직전 안("가로 해" 구조 유도, MISS)은 대체했다.

**후속 항목**(코드 쪽, 이 문서 개정에서 고치지 않음): `E/graph/CONTRACT.md:226`의 "`same_as`·`budget_ref`(선언 전용)" 문구 중 `budget_ref`를 '만들지 않는다 -- 기둥이 흡수(DEC-55, 사용자 결정 2026-10-12 "다로 해")'로 고친다. 다음 graph 계약 개정 단위에서 처리한다.

v1.6 최종검증(2026-10-12): 설계 항목 6행 추가(D-FV1~D-FV6, PART 1·MISS 5). 계획 N7 U-60~U-70은 모두 2026-10-12에 결정됐다(U-67 결정 뒤 D-FV7 추가, 설계 항목 MISS 1행). gap 재분석으로 U-71~U-74를 올렸고, U-72~U-74는 같은 날 결정됐다("K-2 권고대로, GQ1/GQ3/GQ4, ..."). U-71도 같은 날 결정됐다("U-71승인"). U-51도 결정됐다("U-51은 (나)로"). U-04도 결정됐다("U-04 권고대로"). 계획 N7에 남은 사용자 결정·확정 대기는 없다(D-G1~D-G3 추가).

v1.6 P(2026-10-12, 사용자 승인(2026-10-12 P)): 설계 항목 9행 추가(D-P2·3·6·7·8·10·11·12·13, DEV 4·MISS 5), DEC-22 N/A → MISS(켜기 경로 설계). P-1·P-9·P-15의 행은 41 개정 몫이고 D-P1·D-P9·D-P15로 더했다.

v1.6(2026-10-12, v1.6 graph 정본 개정 (사용자 결정 2026-10-12), 사용자 승인(2026-10-12 "design 승인")): 설계 항목 15행 추가(D-GR1~D-GR15, 40 §2.4·§11 U17. D-GR13~15는 design-validator 반영). 상태는 `u15-layer0-tests` bd19cc6에서 쟀다(DEV 8, PART 2, MISS 5). 다른 행의 기준 시점(master `004b7d2`)은 바꾸지 않았다.

v1.5(2026-10-08, 사용자 결정 "j해석은 네의견에 모두 동의해."): 설계 항목 7행 추가(D-J1~D-J7, 모두 MISS, 구현 단위 U1b와 40 §11 'J 추가 범위'). D-J34 문구 갱신(해석 닫힘).

v1.4(2026-10-08, 사용자 결정 Q3·Q4): 설계 항목 13행 추가(D-MM1·2, D-OF1~3, D-MR, D-SW, D-ICM, D-Q34, D-GB4f, D-SIg, D-OR5, D-J34, 모두 MISS), DEC-21을 N/A에서 MISS로(결정으로 닫혔고 spec 미반영), D-PG·D-GB8a·b·DEC-23·96 문구 갱신.

센 방법:
- D-SIa~f는 6행으로 센다.
- DEC 표에서 '37~42', '47·49·51·76·85·86'은 각각 1행이다.
