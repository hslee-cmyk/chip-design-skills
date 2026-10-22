---
template: design
version: 1.13.0
plan_version: 6.34.1
---

# gain-budget-gmid-sizing -- 42-gap-checklist (gap 분석 기준표)

> **Summary**: `bkit:gap-detector`가 설계 문서(40·41)와 구현을 대조할 때 쓰는 표다.
> - 한 행이 FR·NFR·DEC·설계 항목 하나다.
> - 열은 설계 절, 상태, 증거다. 증거는 `파일:행`, test 이름, 또는 재측정용 grep 패턴이다. 판 번호는 41에 맞춘다 -- v1.12.5는 41만 바꾼 판이라 이 문서는 v1.12.4에서 v1.12.6으로 건너뛰었다(검증 R7); v1.12.7 = 계획 v6.28(O-85·O-86) 맞춤, D-IT2 행; 둘째 커밋 = 사용자 O-87 (1)(차동 결합은 S-OS2 card 몫); 셋째 커밋 = 사용자 O-88(MOS 식별 = `device.element_class`); v1.13.0 = 계획 v6.34(사용자 O-106~O-110·DEC-103) 맞춤 -- D-ICM·D-IT2 행을 41 v1.13.0 §4.7에 맞춤(다듬은 창·`metrics_icm_front`·커널 미수렴 이어받기·출력 구조 분류·S-OS1 삭제, KCL 측정 구성 감도, E 칸; design 검증 `wt/_drafts/evidence/2026-10-22/design_v1130_validation.md` S-1), 재검증 90/100(`design_v1130_recheck.md`) 뒤 승인 대기.
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
| NFR-2 같은 키 재계산 0, LUT memo 상한(v1.11: 같은 입력이면 계보 무관 재사용, 계수 범위 = 실행 전체 모든 (블록, 분할) -- 40 §2.4.14, D-XR1~D-XR5) | 40 §7.3 | PART | `E/core/compute_block.py:77`. f23aec8 사실 정정(v1.11): `from_sweep` 정의 `E/lut/lut_memo.py:54`, 호출 `E/lut/sweep_memo.py:33`(옛 문구 '호출부 0'은 틀림). `from_sweep`은 v1.11 대상 소멸 → D-XR2 |
| NFR-3 IC1~IC11 강제 test | 40 §10.3 | MISS | 패키지별 test 폴더(R26 현행 체계 유지)에서 `rg "def test_ic"` 0 |
| NFR-4 결정론 | 전체 | PART | `E/core/determinism.py`. 구조 규칙 test `tests/structure/test_structure_rules.py`. v1.9.2 결함 기록(결정 8): OpenBLAS 스레드 수 의존(40 §11 U17 ② 선행) -- 상태는 다음 gap 분석에서 다시 잰다. v1.9.4(사용자 결정 2026-10-15): 설계 = 40 §2.4.13·41 §5.13, 설계 항목 D-ND1~D-ND5(D-ND5는 v1.10 대상 소멸, N/A). PART 근거: 엔진 안 BLAS 고정 없음(D-ND1), 경계 배치 결함(D-ND2), 알려진 다른 환경 결함(D-ND4) |
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
| D-SYe | diff_pair review (나'): 두 멤버가 다른 궤도이고 (a) 출력 포트가 `differential_output_p/n` 쌍, (b) 그 쌍의 두 gate가 차동 입력 포트 p/n일 때만 `review_needed`(코드 `diff_pair_orbit_split`), 나머지는 crosstab 기록만. 9회로 review 0, 거부 test = 파일럿 넷 하나 비대칭 합성 회로 | 40 §6-5, §10.2 | MISS | `rg "orbit_matching_crosstab"` 0 |
| D-SYg | d/s 비트 동일 범위 (라)(사용자 결정 2026-10-13 "1은 권고"): topology d/s 표기 = 물리 방향 선언(사용자만 수정하는 정본). d/s 표기 맞바꿈에 대해 대칭 결과(궤도·정준 위치·`dc_colour`)는 비트 동일, 전류 부호는 표기 기준 방향 변환(뒤집은 소자 f = −1을 원소·상에 곱함) 뒤 동일. 사이징 결과(writer 계획·θ 스키마·ties·front)는 선언 방향. 틀린 선언 → 봉인 7 `no_root_in_window` 거부. test `tests/search/test_orbit_ties.py::test_ds_flip_symmetry_bit_identical`, 봉인 7 거부 `tests/sizing/test_block_columns.py`. `dc_colour` writer = graph 대칭 블록 `s1_symmetry` | 40 §6-8, §2.4.8, §10.2 | MISS | `rg "test_ds_flip_symmetry_bit_identical"` 0, `dc_colour` writer = `E/sizing/struct_colour.py:20` |
| D-SYf | 전류 기저 열 순서: 결정 취지 "대칭 궤도 원소를 자유 열로 먼저 남긴다" = 자유 열 선택에서 비자명 궤도 우선, 행사다리꼴이 앞 열을 pivot으로 잡으므로 열 정렬 키 = (궤도 비자명이 뒤, `dc_colour`, 이름)(앞에 두면 파일럿 27/40). `current_basis`가 `graph/s1: orbits` 읽음. (묶음 수, 탐색 θ 변수 수) = (`len(SearchDomain.ties)`, `len(SearchDomain.variables)`): 파일럿 29/38, 그중 전류 묶음 7(M1a~M1b, M19~M10), 나머지 8회로 = master `8e46548` as-built 값, 28/39(규칙 전, 전류 묶음 6)는 기록만 | 40 §6-3·§6-8 | MISS | `E/sizing/current_basis.py:8` 열 순서 = (`dc_colour`, 이름), orbit 읽기 0 |
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
| D-ICM | `icmr_v`(레일로 자른 창 폭, 빈 창 음수)와 `icm_margin_v`(선언 입력 DC와 창 경계 거리, SP-2 대기면 `input_dc_pending`), ICMR 제약 = 폭 + 포함. IT-2 설계(41 v1.13.0): 커널·front·보고 창 = 모두 `node.dc_window_cfg`(봉인점 KCL 선형 감도 끝 '추정', 모든 측정 구성 -- O-108·O-109 C1; 다듬은 창·front 전용 블록 없음, 정확값 oracle `.dc`), 정의 함수 `icm_window_metrics`(부르는 자리 `metrics_aux` 하나) | 40 §3.8-8, 41 §4.7-2·§4.7-3b·§4.7-5 | MISS | `rg "icmr_v\|icm_margin" E/` 0. ngcc spec은 `{metric: pending MOD5}`(`assets/library/ngcc_3stage_ff.sizing_spec.json:87`) |
| D-Q34 | §9.2 회로별 선언(파일럿 3.3 mV·스윙 2.4 V·icm_margin, 6회로 가드, ngcc `icmr_v >= 0.6`, nmcnr `icmr_v`·`swing_out_v >= 0.5`)과 옛 이름 거부(`mismatch_sigma_mv`, `mirror_ratio_error_mv`, `mismatch_sigma_v`) | 40 §9.2, §3.1 | MISS | `assets/library/*.sizing_spec.json`(옛 이름 3개 회로), `E/authoring/SPEC_CONTRACT.md:261` S2 |
| D-GB4f | 헤드룸 달성가능성: 출력·입력·버퍼 창 상한(LUT 격자 전수, 인증/미상), 선언 제약 인증 불가 → exit 3 `headroom_unattainable`, 제약 없는 창·입력 DC 대기는 보고, 유도 기록 | 41 §4.6 | MISS | `rg "headroom_bound\|headroom_unattainable" E/` 0 |
| D-SIg | 출발 구간 Q3·Q4: 스윙·ICMR·입력 DC 예산 분할(41 §6.2), A_eff matching L 하한(절대 offset 회로만, 41 §6.4-2) | 41 §6.2, §6.4-2 | MISS | `rg "start_intervals"` 0 |
| D-OR5 | 오라클 offset Monte-Carlo(표본 수 유도, `model_error_offset_in_sigma_mv`)와 스윙·ICMR `.dc` 스윕 | 40 §10.2 | MISS | `rg "mc_mm_switch\|offset_mc" tools/spice_oracle` 0 |
| D-J34 | J 공동분석 목록 추가: 입력 DC 값(nmcnr 0 V, SP-2), sf_pushpull M6↔M8·M5↔M7 matching, 4-팔로워 버퍼 헤드룸 | 40 §9 Q7, §9.3 | MISS | 해석은 2026-10-08 결정으로 닫혔다(40 §9.3 J-D·J-E). 구현 확인은 D-J1·D-J5·D-J7 행에서 한다 |
| D-J1 | 복합 diode D1: DC 가지 걷기 정의, 묶음·기준/캐스코드 구분, 소비 셋(DC 역할 규칙 1c, 미러 입력 확장·`diode_load`, 루프 (1.6) `composite_diode_internal`). 9회로 발동 = 41 §1.13 실측 집합, 나머지 7회로 무동작 | 41 §1.12.1, §1.13 | MISS | `rg "composite_diode" E/` 0. `[u1-sp1] E/graph/drive_kind.py` `_mirror_inputs`는 단순 diode만 본다 |
| D-J2 | feedforward 셀: 주경로(D_max·slack), FF 묶음·탭·merge·B_b, 블록 분해(FF 합류는 복합 블록 아님), gain 예산은 주경로만, 경로 기여·A_decomp 잔차, `ff_ratio_candidates`·`ff_gm_ratio`, Σ 판정 FF 상한, FF 출발값 | 41 §1.12.2, §2, §4.3, §5.1, §6.5, 40 §3.8-8 | MISS | `rg "feedforward\|ff_gm_ratio" E/` 0. `[u1-sp1]`은 ngcc Vout을 복합 블록 하나로 묶는다(`composite_block_pending_ratify`) |
| D-J3 | 중첩 Miller 보상 내부 루프: 조건 (a)(b), 루프 뷰 미생성, `pm_ss_deg` 미선언이면 `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`), 전체 PM 판정의 P = 0 확인 | 41 §1.12.3 | MISS | `rg "compensation_internal" E/` 0. `[u1-sp1]` ngcc·nmcnr에서 `undeclared_loop_constraint` 정지 |
| D-J4 | 루프 극성 = 뷰의 DC 사이클 극성, 커패시터 사이클 `ac_only`, `loop_polarity_conflict`. L 동치류 주인 규칙 `main_path_signal`, name_order는 review | 41 §1.12.4·5 | MISS | `[u1-sp1] E/graph/polarity.py`(커패시터 사이클 → 0 → review), `l_classes.py`(주인 순서 3단계) |
| D-IT1 | card IT-1: 입력 포트 '같은 DC' 엣지(`input_tie`) 폐기, 입력 포트 뿌리 y 키 = 넷, `input_port_multiple_roots` 정지 | 41 §4.7-1, 40 §11 IT 행 | MISS | 구현 전(계획 N6.5 완료 조건 1~7) |
| D-IT2 | card IT-2(41 v1.13.0, 계획 v6.34): 입력 CM 창 단일 정본 -- `node.dc_window`(θ 프레임, **W4 뿌리 항목만** -- O-109 D1)·`node.dc_window_cfg`(측정 구성 판정 창, `icm_config`, **모든 측정 구성의 KCL 선형 감도 끝 하나** -- `graph.ss_nodal` + 닫음 `kvl_sensitivity`, θ 연립 측정 구성 감도 0 -- O-108·O-109 C1; 상태 {measured, unmeasured, f_component_undeclared}, 커널 상태 이어받기 없음·READS에 `node.dc_window` 없음 -- O-109 D2; F 성분 미선언 판정 = `icm_config`가 `node.dc_writer`로 -- 재검증 S-1), `graph.ss_nodal`(세 자리 이전, E 칸 `g_bound` -- `conductance_matrix(…, bound=True)` 호출 자리 하나·`__canonical__` 포함, O-107; 저항 결측이면 값 = `Undefined`·`icm_config` `passive_value_undeclared`), `graph.ss_circuit`(계획 v6.34.1 -- writer `ss_circuit` 하나, `metrics_ss`·`metrics_aux`·`ss_nodal` READS, 조립 사본 둘 삭제, `ss_circuit(` 호출 자리 하나·`SsCircuit(` 생성 자리 하나; 원래 취지와 다름(범위 확대)), 스냅샷 파생 규칙(keep = `ctx.base` writer ∪ 호출 블록·parent 일치 검사 확장·봉인 4 coverage·서로소 단언 -- O-61 P1), 창 끝 함수 `saturation_window` 하나·**부르는 자리 둘**(`dc_columns`·`icm_config`; 서명 `root` 하나 -- 쌍 roots·묶음 갈래 삭제, O-61 P2·검증 N-5), 모든 측정 구성 포트 끝 = `node.dc_window_cfg` 한 칸(`IcmConfig` `kvl` 칸 없음, O-61 P3·O-109 C1), F 성분 미선언 포트 정의 불능·고립 포트 = 뿌리 창 절차(O-61 P4), 커널 미수렴 = θ 프레임 창의 출력 전용 상태(metric 정의 불능 아님 -- O-109 D2), W1 철회·`IcmWindow` 사본 칸(`criterion`·`config`·`sources`) 없음, **없는 것**(O-109 C1·D4): `node.dc_window_def_refined`·`dc_window_refine`·끝 풀이 함수·`metrics_icm_front`·`refine_front_windows`·`node.dc_output_structure`·S-OS1 code(남은 멈춤 S-OS2 -- fail-closed code, 41 §4.7-1a 726); `Circuit` 행 부분 공용 helper 이동·`sizing.__all__` 공개(U-101 (가′), 41 §4.7-4); 권한표 등록·깨지는 기존 test(`test_s2_values.py`)는 test 작성 주체 몫(41 §4.7-6); v1.12.4·v1.13.0: 판정 분해능 정의 함수 `_transfer_resolution`(δV_out = \|z_u\|ᵀ(\|r\| + E\|v\|) -- 계획 v6.34 N3.8 O-107, δA_num → `IcmConfig.transfer` resolution), 13회로 표 = 회로 해석 기록(병합 조건 대상 소멸 -- O-109 D4), S-OS2 일반형 후속 card(O-67 (5)·O-68 (2)), IT-2c 착수 실측 (a)~(c) 기록됨; v1.12.5·v1.12.6: 단일 출력 + 선언 되먹임의 DC 되먹임 판정(계획 v6.27 N3.8 경로 판정, `icm_config.py` 비공개 `_dc_feedback_reaches` 하나, READS S1 다섯) → `icm_config_feedback_no_dc`, 절단 넷 순수 함수 `feedback_cut_nets` 하나(`input_terminal_nets`·`_input_side` 0, 호출 넷), L10 (i); v1.12.7: 지원 밖 원소 = S1 `device.unsupported` READS → `icm_config_feedback_element_unsupported`, IT-2c 차동 출력 + 선언 = S-OS2 code(차동 결합·`icm_config_feedback_outputs_split`은 S-OS2 card 몫 -- O-87 (1)), MOS 식별 = S1 `device.element_class == ELEMENT_MOS` READS(셋째 커밋, O-88 -- 둘째 커밋의 pins gate 단자 추정 대체)·단자 이름 `MOS_TERMINAL_NAMES`·지원 kind 상수 참조 0·READS 일곱, 서명 `_dc_feedback_reaches(view, output, cut_nets)`, L10 (a) = 계획 v6.28 (10)(a)(함수 객체 참조 정적·`__code__` 동적·양성 대조)) | 41 §4.7-1a·§4.7-2~§4.7-7, 40 §2.4.8·§10·§11 IT 행 | MISS(IT-2a·IT-2b 병합 `6afe4758`, IT-2c·IT-2d 구현 전) | 계획 v6.34 N6.6 완료 조건 (0)~(12) |
| D-J5 | 입력 DC 정책: SP-2 (c) y_icm 창 범위, `required_input_cm_v`, sf `icm_margin_v >= 0` 제약, `buffer_window_report`, `icmr_window_short_l_bin` 경고 | 41 §4.6·§4.7-5(v1.12 IT-2 -- `required_input_cm_v`는 `icm_window_metrics`, 포트별 margin), 40 §3.8-8, §9.2 | MISS | `rg "required_input_cm\|short_l_bin" E/` 0. `assets/library/sf_pushpull_output_opamp.sizing_spec.json`에 `icm_margin_v` 제약 없음 |
| D-J6 | `structure.json` concept 어휘 7개(신규 5), override/confirm/고아/불일치 전이, `structure_rule_fp`, 단계 A의 사실 로드 순서·`build_s1(structure=)`·`declared_loop_cuts` 전달, 뷰 한정 `ac_ground_exception` 소비 | 40 §3.2-3, 41 §1.12.6 | MISS | `[u1-sp1] E/graph/structure_load.py`는 `drive_kind`만 소비한다. `[u1-sp1] E/pipeline/stage_a.py` `run_stage_a`는 `declared_loop_cuts`를 넘기지 않는다 |
| D-J7 | 회로별 사실 파일(`assets/library/<name>.structure.json`) 작성: U1b 병합 뒤, confirm 사실은 실측 일치 시만, rule_hash = 병합 코드의 `structure_rule_fp` | 40 §3.2-3 표 | MISS | 사실 파일 0개(작성 순서상 U1b 뒤) |
| D-J8 | 혼재 노드 구동 종류(C-1 + 보완 (가)): (i) source 쪽 소자 drain이 교류 접지·gate가 신호 노드면 follower → 전압 구동, (ii) 아니면 drain 쪽 gate가 신호 노드면 전류 구동. 9회로 발동표(옛/새/근거 `follower`\|`cascode`, 키 (회로, `view_key`, 노드), 혼재로 판정되는 모든 뷰에서 바뀜) = 바뀐 노드 sf N910·N1112·N1516 + folded_cascode Vg10(전류 구동), sf N17·N20 전압 구동 유지, 나머지 무동작. folded: M8 stage 시작 셀 아님 유지 판정(base도 시작 셀 = M1, M2) + 그 밖 변화 기록(허용 = Vg10 극점 노드 drive voltage → current 하나, 블록·stage 9회로 불변) | 41 §1.5-4 | MISS | as-built는 DC 역할로 가른다(`E/graph/drive_kind.py`) |
| D-J9 | `structure.json` concept `l_owner`(C-3, override). nmcnr 사실 = [M104, M105] → M105(사용자 결정 2026-10-12 "C-3은 네 제안대로 해") | 40 §3.2-3, 41 §1.12.5 | MISS | `rg "l_owner"` 사실 개념 0, nmcnr 사실 파일 없음 |
| D-J10 | 파일럿 `structure.json` `rule_hash`만 재기록(사실 불변, approval_id `user_decisions 2026-10-12 C-6 재확인`): ①-d 마지막 규칙 변경(C-1 보완 (가)·전류 기저 열 순서) 뒤 1회, 갱신 뒤 단계 A Vbias2 판정 불변 확인(달라지면 갱신하지 않고 재질의) | 40 §3.2-3 | MISS | 규칙 변경 미병합(master `8e46548`) |
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
| D-PF1 | **대상 소멸**(v1.11 → D-XR2: `from_sweep`·`sweep_memo`를 지우고 계수 상태 memo로 대체). 옛 항목: `LutMemo.from_sweep` 배선 | 40 §7.3, §2.4.6 | N/A | f23aec8 사실 정정: 정의 `E/lut/lut_memo.py:54`, 호출 `E/lut/sweep_memo.py:33`(옛 증거 '`lut_memo.py:34`, 호출부 0'은 틀림) |
| D-PF2 | tol_V 디스크 캐시와 정리(v1.10: 실행 사이 유지 -- U-87 결정, 원래 취지의 예외, 40 §2.4.12 Q9) | 40 §7.3 | PART(브랜치) | `[ng-tolv-cache] E/lut/table_cache.py:217,230-254` |
| D-GB7a | L 동치류의 L 공유 | 40 §3.2 | DEV | `E/graph/CONTRACT.md:220` |
| D-GB7b | 미러 비율 강제 | 40 §3.7 | MISS | `E/sizing/CONTRACT.md:276` |
| D-GB7c | DEC-95 (3) 전체 순서 | 40 §3.7 | PART | `E/sizing/writer_plan.py:13-17` |
| D-GB7d | W_request 고정 W | 40 §3.7 | MISS | `E/sizing/block_widths.py:9` |
| D-GB8a | `ls`(슬루·방향별 전류), 스윙·ICMR은 D-SW·D-ICM | 40 §3.8 | MISS | -- |
| D-GB8b | nqs 보고(미스매치 보고는 D-OF1·D-MR로 대체) | 40 §3.8 | MISS | -- |
| D-GB8c | `verified_by`, 모델 오차, `spice_unverifiable` | 40 §3.8 | MISS | -- |
| D-IC | IC1~IC11 계약 test(패키지별 폴더) | 40 §10.3 | MISS | `rg "def test_ic"` 0 |
| D-T | test 폴더 체계 | 40 §8 R26 | N/A | 축소 유지 승인(2026-10-08). 현행 체계를 쓴다 |
| D-GR1 | graph 밖 저장소는 셋뿐(LUT memo·S3 기록과 색인·실행 계수 -- v1.10 S0 직렬화 폐지) | 40 §2.4.1 | DEV | `E/search/search_context.py:58-67`(cache·computed_keys·cell_floors 등 -- master `b9af2d6f` 재측정, v1.12 단일 정본 감사 F4; `local_seal_memo`는 엔진 소스에 없음, `git grep -w` 0) |
| D-GR2 | S0 수준 층 필드화(S1v·결합 변수·GB4·출발 구간·metric 구조 입력). 레코드별 필드 = 40 §2.4.8(v1.9.1 D1~D4·D7~D9: `graph/s1v` `coverage`·`graph/ach` `block_bounds` 없음, `graph/start` `rungs` = as-built `ladder`, `noise_inputs`·`placement`는 U17 ②, `local_inputs` dict→tuple·memo 제외) | 40 §2.4.2·2.4.8 | MISS | bd19cc6 `sctx.s1v`·`sctx.ach`·`sctx.start` 객체, `E/search/start_values.py:186-235` `StartContext` |
| D-GR3 | 실행 사이 재사용 제거(v1.10, 사용자 결정 2026-10-15 "나로 해"): S0 수준 층 = 실행 수명, 디스크 스냅샷·S0 키·코덱·타입 등록부·U-68 정리·`run_stage_a` PDK 선언 경로 인자와 진입 sha 대조·`GMID_S0_SNAPSHOT_DIR`·S3 실행 사이 읽기(이전 front 점 시작점, 디스크 실패 기록) 삭제. 엔진 코드 지문은 결과 기록 출처 칸으로만, 블록 코드 해시는 실행 안 입력 버전으로 유지(checkout 무관 성질은 Q10). 옛 항목(S0 스냅샷 영속화, v1.9.1~v1.9.3 문구)은 history | 40 §2.4.3 | OK | [xrun 7e1b4be, 판정 029f9b7] 엔진 소스·CONTRACT에서 삭제 이름 20개 `rg -w` 0(`snapshot_codec`, `S0Slot`, `type_registry`, `disk_failures`, `_s3_thetas`, `load_evals`, `pdk_decl_path` 등), 9회로 새 프로세스 두 번 비트 동일·`.s0_snapshot` 생성 0, S3 미리 채움 = 빈 S3 |
| D-GR4 | 분할 계산 블록과 이식(graft). 분할 대상에 GB5 `passive_values`(읽는 레코드 = 영점 상쇄 셀 소자의 `dc_gm`, 전류 θ만 바뀐 자식의 재계산 해소, U17 ② 이월). v1.11: 분할 `*`의 이식·`Donors`(`find`·`register`)·필수 `donors`·`counters`는 XRUN-F1 B(D-XR3), 분할은 U17 ② | 40 §2.4.4 | MISS | `rg "def graft"` 0, `E/core/compute_block.py:73-90`(블록 이름 하나의 버전) |
| D-GR5 | S3 메모리 색인·스냅샷 보존(`sctx.cache`·`local_seal_memo` 대체, G-5). v1.11: 보존 = 실행 수명 동안 계산 원천 보존(보존 소유자·`retain`·`release` 폐지, 사용자 결정 X-2), 블록 결과 색인은 D-XR3 | 40 §2.4.5 | DEV | bd19cc6 `E/search/kernel.py:102-121`, `E/search/local_candidates.py:141-144` |
| D-GR6 | LUT memo 순수성(`call`)·S0당 인스턴스 하나·상한 B_r(층 0 항). v1.11: 첫 평가 버림 제거는 XRUN-F1 A로 앞당김(D-XR2) | 40 §2.4.6 | DEV | bd19cc6 `E/search/search_context.py:105-121`(두 번째 인스턴스, 첫 평가 버림), `E/lut/lut_memo.py:25-36,60-62` |
| D-GR7 | 수동소자 값 S2 필드(writer GB5, R = 1/Σgm 포함) | 40 §2.4.8 | MISS | bd19cc6 `E/metrics/passive_values.py:16`(함수), `E/search/kernel.py:146-150`(규칙 사본) |
| D-GR8 | tol_I = tol_V × `dc_gm`(자기 동작점, writer 1개, `ss_dev` 공용) | 40 §3.7-3, §2.4.11 | DEV | bd19cc6 `E/sizing/seal_tolerances.py:36-45`, `E/sizing/kernel_run.py:51-96` |
| D-GR9 | 값 사본 제거(`SsEvaluation`·`EvalResult`·`LayoutResult`), 레이아웃 = 설계점 필드. v1.11: `EvalResult` 스냅샷은 늘 있음(실패 = 부분 스냅샷, D-XR4) | 40 §2.4.7 | DEV | bd19cc6 `E/metrics/ss_types.py:79-88`, `E/search/search_values.py:146-162`, `E/layout/run.py:109` |
| D-GR10 | G-7 SearchContext = 참조 + S3 색인 + 실행 계수, `__slots__`·frozen | 40 §2.4.7 | DEV | bd19cc6 `E/search/search_context.py:51-89` |
| D-GR11 | G-8 강제 장치 4종(규칙 G 확장·설계 값 타입 위치·SC-a/SC-b lint·9회로 test). 허용 모듈(v1.10: `core/snapshot_codec.py`·`core/type_registry.py`는 목록에서 빠짐) | 40 §2.4.10 | PART | bd19cc6 규칙 G = 모듈 가변·데코레이터·global만(`E/tests/structure/structure_checks.py:880-920`) |
| D-GR12 | G-10 계수(블록·분할별 grafts 포함)와 9회로 test(v1.10: `perf.s0_snapshot`·두 번째 실행 test 폐지. v1.11: 범위 = 실행 전체 모든 (블록, 분할)·`perf.blocks`(D-XR5), 판정 6 대상 소멸, 9회로 test는 XRUN-F1 B가 판정 1·5로 먼저) | 40 §2.4.9 | PART | bd19cc6 `E/core/compute_block.py:30-38` `BlockStats`, `E/search/kernel.py:120-121` `recompute_same_key` |
| D-GR13 | 단계 B 층(r̂·수치 rank, 직렬화 제외(v1.10: S0 직렬화 폐지로 이 구분은 대상 소멸). ①-b는 필드 자리·제외 규칙만, 블록 배선은 소비자 층 0과 함께 U17 ② -- v1.9.1 D5), `ach.dof` = 구조 DOF만, KernelContext·SearchContext 선언 파생의 S0 수준 필드, `metrics_dc` `gate_area_m2`·`power_resolution_w`(제약 행 `constraint_rows`는 U17 ②로 이월, `unmeasured` 자리 40 §2.4.12 Q8 열림) | 40 §2.4.1·2.4.7·2.4.8 | DEV | bd19cc6 `E/search/objectives.py:31-45`, `E/sizing/s2_values.py:429-443` |
| D-GR14 | 층 0 필드(`graph/layer0: macro`·`comp_approx_gap`·`rounds`, `graph/local` 블록 범위 metric), 색인 `local`·`solved` | 40 §2.4.5·2.4.8, 41 §5.3.9·§5.3.11·§5.5 | MISS | `rg "comp_approx_gap"` 0(엔진 .py) |
| D-GR15 | 계수 소유 `RunCounters`(블록 무상태, `_evicted`·`events` 이동), LUT memo 퇴출 판정(U-60 결정 (가): 퇴출 뒤 재계산 0). v1.11: 블록 계수 부분과 블록 무상태화는 XRUN-F1 B(D-XR5), `_evicted`·`events` 이동은 U17 ②·③ | 40 §2.4.6·2.4.9 | DEV | bd19cc6 `E/core/compute_block.py:67-71`, `E/core/bounded_lru.py:38`, `E/lut/table_cache.py:199` |
| D-XR1 | ln 좌표 원값 보존 정본 `ThetaCoords`(`E/search/theta_coords.py`): 시작 좌표면 시작 θ 원값. 외층 `solve_eps`·층 0 `_maxmin`·감도 게이트가 같은 정본을 쓰고 사본(`_coord`·`to_theta` 세 개·`_layout` 원값 목록)은 지운다(사용자 결정 X-1 (1), XRUN-F1 A) | 40 §2.4.14 (2) | OK | `E/search/theta_coords.py`(ThetaCoords), 세 경로 `slsqp_outer.py`·`layer0_center.py`·`gate_run.py`, 사본 grep 0 -- 판정 기록 `.ai/verification/xrunf1a.json`(audit 9930c28, 병합본 1670330: suite 10118 passed/0 failed, 9회로 A-5 범위 밖 변화 0) |
| D-XR2 | 첫 평가 버림 제거: 탐색 memo는 계수 상태로 시작하고 실행의 첫 커널 평가(실제 평가) 뒤 상한 (n_θ + 1)·U_eval 고정, `build_search_context` 커널 평가 0, `sweep_memo.py`·`from_sweep` 삭제(사용자 결정 X-1 (2), XRUN-F1 A) | 40 §2.4.6 | OK | `E/lut/lut_memo.py`(counting·open_count·fix_bound·bound_state), `search_context.py` 커널 평가 0, `kernel.py` 배선, `sweep_memo.py` 삭제, `perf.lut_memo_bound` -- 판정 기록 `.ai/verification/xrunf1a.json`(audit 9930c28, 병합본 1670330: suite 10118 passed/0 failed, 9회로 A-5 범위 밖 변화 0) |
| D-XR3 | 블록 결과 색인: (블록, 분할, 입력 버전) → 그 값을 담은 스냅샷 참조, 계보 무관, 실행 수명, 상한 = 40 §2.4.9 증거 집합 식(등록 때 fail-closed는 card C 뒤, X-8), 결정적 도메인 실패 기록 등록·재연(X-9), fail-closed 다섯 가지(40 §2.4.5 fail-closed 칸 (1)~(4)·(6) -- (5) 상한 등록 검사는 card C. 옛 문구 '네 가지'는 (6)을 빠뜨린 오기, card B J-14), 모든 블록 호출이 `donors`·`counters` 필수이고 `run_stage_a`는 호출자가 만든 두 객체를 필수 키워드로 받는다(사용자 결정 X-1 (3)·X-7, offset-strategy PD-8(S-8), XRUN-F1 B). 실행 비공유는 구조 규칙으로: 두 객체는 `open_run()`으로만 만들고 구조 규칙 M이 생성 자리·실행 경계 넘김을 막으며, 색인 키에 실행 바깥 지문을 넣지 않고 디스크에 쓰지 않는다(사용자 결정 2026-10-16 "권고대로 구조로 막는 방향으로 진행해") | 40 §2.4.4·2.4.5 | MISS | (v1.11: Q12 → 사용자 결정 X-8 card C, 실패 기록 등록·재연 X-9) f23aec8 `E/core/compute_block.py:139`(같은 lineage `block_version` 하나만). `rg "class S3Index\|def graft\|class RunCounters"` 0 |
| D-XR4 | 실패 평가의 부분 스냅샷: 예외 `partial`·`attach_partial`, `EvalResult.partial`, S3 evals 실패 줄 `snapshot_fp`(사용자 결정 X-3, XRUN-F1 B) | 40 §2.4.7 | DEV | f23aec8 `E/search/kernel.py:119-122·129-135`(실패면 평가 스냅샷 없음), `E/sizing/seal.py:50-58`(보고서 쓴 뒤 예외) |
| D-XR5 | perf 재계산 계수 = 실행 전체 모든 (블록, 분할), 결과 JSON `perf.blocks`·`perf.block_totals`, 옛 `block_calls`·`block_reuses`·`block_computes`·`block_recomputes_same_input` 삭제(사용자 결정 X-5, XRUN-F1 B) | 40 §2.4.9 | DEV | f23aec8 `E/search/find_front.py:44-59·131-133`(sizing 블록 12개의 `find_front` 구간 차) |
| D-XR6 | 모든 커널 평가를 E_total에 넣음(E_B 선언·유도 모든 실행, X-15): 선언 E_B = 탐색 예산·E_total = E_B + N_T + R·게이트 예약 R = 2 × 정의역 변수 수(X-16·X-17, 게이트는 항상 돎), 유도 실행은 E_total = D·탐색 예산 = D − N_T − R, 묶음은 시작 전 상계 확인·부족이면 `FdBudgetShortfall`, `search_ceiling`·`search_stop` 한 자리(E_B 직접 읽는 예산 확인 전수 교체, E_B 유도도 `search_ceiling`으로, 확인 없던 단일 평가 -- 사다리 칸·주어진 시작점 -- 에 확인 추가, MOD8은 find_front 밖), 유도 적용 시점에 남는 탐색 예산이 없으면 fail-closed(`ValueError`), 그 뒤 넘침은 `RuntimeError`, 실행 끝 확인, 색인 상한 등록 때 fail-closed(사용자 결정 X-8, XRUN-F1 C) | 40 §2.4.14 (5) C, §2.4.12 Q12 | DEV | f23aec8 `E/search/fd_jacobian.py:86-111`(묶음 예산 검사 없음), `E/search/find_front.py:84`(게이트 예산 밖). 측정: E_B 40에서 커널 평가 43·49·64·66(history H4) |
| D-P2 | 소자별 폭 슬라이스(`LutAccess.w_keys` 소자 키, `w_key_of(lut, device)`), LY2 행별 finger 폭 | 40 §3.10.1 | DEV | bd19cc6 `LutAccess.w_keys` = kind 키, `convergence/place_layout` `layout_score` 최소 키 |
| D-P3 | LY5 nf → W → 완화, 종속 소자 W 고정 입력(봉인 2 판정) | 40 §3.10.2 | DEV | MOD8 gap (b)(종속 소자 W 고정 불가) |
| D-P6 | MOD8 열린 항목 닫음: 쌍 전류비 보장 규칙, `key_exclusion` 삭제, 면적 모델 오차 기록만, front 뒤 재측정 | 40 §3.10.3 | MISS | `rg "key_exclusion"` (convergence) |
| D-P7 | DEC-88 반전 수준 하한 = 연속 부등식 제약 행(bounds 조임 폐기) | 40 §3.10.4 | DEV | `search/CONTRACT.md:573`, `E/search/cell_floor.py` |
| D-P8 | DF 재발 금지 표(DF-01~37 → 계약 test → 단위) | 40 §10.3a | MISS | `rg "def test_df"` 0 |
| D-P10 | finger 피치 여유 PDK 유도(I-A12) | 40 §3.10.5 | MISS | 옛 `PROCESS_GEOMETRY["finger_pitch_overhead_m"]` = 0.0 |
| D-P11 | 최종 해 활성 제약 여유 판정·활성/비활성/보류 보고(NFR-5) | 40 §3.10.6 | MISS | front 표 `constraints[].state` 없음 |
| D-P12 | 규칙 분기 발동표 결과 JSON `rule_branches`(DEC-59) | 40 §3.10.7 | MISS | `rg "rule_branches"` 0 |
| D-P13 | 누락 항목 일괄: `dc_id_source`, tol_V 정의, 결합 잔차 쓰임(`residual_table`·`trust_limits`), LY8 3열, 근방 반경 확장, IC3·IC7·IC11, T1·T7·T8 형식, `layer0.ac_inactive`, bisection 켜기 경로, TS7 strict xfail | 40 §3.10.8 | MISS | 항목별 grep 0(`dc_id_source`, `trust_limits`, `metric_columns`, `ac_inactive`) |
| D-AP1 | A' 판정 기준(P DEC-98, 사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ①): 판정자 ngspice(MOD8 전 점은 T4-pre), 독립 대조군 AI 손분석(결정 원문 "코드 없음" -- 엔진 코드 미열람, LUT 조회·계산 보조 스크립트 허용; 회로마다 1회 고정 문서; 엔진 입력 아님; 작성 주체 ≠ 엔진 코드 작성 주체), 피검 엔진 시작점·front 점(P U-45). 판정 규칙(엔진만 실패 = 엔진 결함 대조표, AI만 실패 = 공동분석 기록·그 회로 완료, 둘 다 통과 = 전력(ngspice)·면적(엔진 면적 코드에 손분석 W/L/finger) 차, 둘 다 실패 = 판정 불능). U17 단계 ② 완료 조건: library 9회로 + held-out 회로에서 시작점 봉인 통과·spec 제약 행 c ≥ 0·ngspice(T4-pre·T5) 통과, front 점도 ngspice 통과, 엔진 실패 회로가 남으면 미완료(fail-closed), 9회로 도달률 회귀 지표. held-out 선정 P U-75(사용자 몫), 세부 P U-76 (1)~(9) 기본안 | 40 §10.5, §11 U17 ② | MISS | 저장소 안 손분석·A' 대조표 문서 0, held-out 회로 0(U-75 미정), `docs/03-analysis/aprime/` 0, T4-pre 오라클 입력(sizing W·비례 접합 기하) 0, `constraint_rows` 미구현(D-GR13) |
| D-ND1 | BLAS 스레드 고정·확인(fail-closed, 무상태 재확인 (a)~(e))과 결과 기록 칸 실행 환경 지문 `env_fp`(단계 A 보고서·S3 runs 줄)(사용자 결정 2026-10-15 1안, v1.10: S0 키 (iv)는 대상 소멸. 파일·이름·기록 자리는 40 §2.4.13 (1) J-1·J-2·J-4 오케스트레이터 기본안) | 40 §2.4.13 (1) | OK | `E/core/blas_env.py`(pin_blas_threads·blas_environment, 소유 BLAS 확인은 재확인 포함 -- N-6), `E/__init__.py:5-7`, 재확인 (a)~(e) `stage_a.py`·`search_context.py`·`find_front.py`·`layer0_center.py`·`slsqp_outer.py`, `env_fp` 단계 A 보고서·runs 줄 -- 판정 기록 `.ai/verification/nfr4c2.json`(audit a18c6b2, 병합본 ebd7b3c: suite 10089 passed/0 failed, A-4 36/36) |
| D-ND2 | 판정 경계 위 배치점 규칙 BP1~BP3, 층 0 끌어올림 닫힌 식(3안) | 41 §5.13 | OK | `E/search/layer0_center.py:243-265` 닫힌 식(√ε = math.sqrt(sys.float_info.epsilon)), `lift = u` 삭제. 범위 밖 기준선 변화 3회로는 사용자 결정 N-5로 수용 -- 판정 기록 `.ai/verification/nfr4c2.json`(audit a18c6b2, 병합본 ebd7b3c: suite 10089 passed/0 failed, A-4 36/36) |
| D-ND3 | NFR-4 검증 기준(③): 같은 환경·같은 코드 비트 동일, 다른 환경·수치 보존 리팩터링 필드별(D·C·K), 분해능 출처 표, test 기반 비교기(`E/tests/integration/nfr4_compare.py`)·실행 하네스(`nfr4_run_dump.py`)와 감사 사용, L-b 정지 사유 기록 | 40 §2.4.13 (2)~(5) | OK | `E/tests/integration/nfr4_compare.py`·`nfr4_run_dump.py`, L-b 정지 사유 `E/search/l_bin_search.py:35-40`·`eps_sweep.py:116-135`·notes `l_search` -- 판정 기록 `.ai/verification/nfr4c2.json`(audit a18c6b2, 병합본 ebd7b3c: suite 10089 passed/0 failed, A-4 36/36). 매크로 해 주입 진입은 후속 NFR4-F2 |
| D-ND4 | 알려진 잔여 결함: pushpull_follower_buffer의 다른 실행 환경 비교 이산 갈림(외층 ε 풀이 `EP:s1` FD 열 실패 `frozen:L:M1`·재시작 2 대 6, 시작점 경계 밖 성분의 풀이기 잡음). 3안으로 없어지지 않는다. 처리 = Q-N7 확정(사용자 결정 2026-10-15 "기본안대로 진행해"): 알려진 결함으로 남기고 원인은 후속 card NFR4-F1(40 §2.4.13 (8)) | 40 §2.4.13 (5)(b)·(8), 41 §5.13 '남은 위험' | DEV | 대리 측정(고정 전 스레드 1 대 8·18, 41 §5.13 (a2)): 엔진 결정 차이 125/125, `wt/_nfr4_design_scratch/all_variant_a2.json` -- 34932a9 복제 |
| D-ND5 | **대상 소멸**(v1.10, 사용자 결정 2026-10-15 "나로 해" -- S3 실행 사이 읽기 없음). 옛 항목: S3 실행 간 재사용의 실행 환경 지문(Q-N5, 사용자 결정 2026-10-15 "기본안대로 진행해"): `S3Archive(..., *, env_fp)`, 줄마다 `env_fp`, `load_evals`·`load_runs`가 `code_fp`·`env_fp` 둘 다 같은 줄만, 불일치 = miss, 빈 `env_fp` = `ValueError` | 40 §2.4.13 (8) Q-N5(대상 소멸) | N/A | `rg "env_fp" E/search/archive.py` 0 -- 34932a9. `E/search/archive.py:42`는 `(root, context_fp, code_fp)`만 받는다 |

## 4. 상태 집계

기준은 master이고, 브랜치에만 OK인 항목은 PART로 센다.

| 구분 | 행 수 | OK | DEV | PART | MISS | N/A |
|---|---|---|---|---|---|---|
| FR·NFR | 15 | 2 | 1 | 7 | 5 | 0 |
| DEC | 82 | 24 | 6 | 29 | 17 | 6 |
| 설계 항목 | 168 | 6 | 27 | 15 | 117 | 3 |
| **합계** | 265 | 32 | 34 | 51 | 139 | 9 |

v1.11.3(2026-10-16, XRUN-F1 card A 병합 직전, 판정 9930c28): D-XR1·D-XR2 DEV → OK. 집계: 설계 항목 OK 4 → 6, DEV 29 → 27(합계 OK 30 → 32, DEV 36 → 34).

v1.11.2(2026-10-16, NFR-4 card 2 병합 직전, 판정 a18c6b2·사용자 결정 N-5·N-6): D-ND1 MISS → OK, D-ND2 DEV → OK, D-ND3 MISS → OK. NFR-4 행은 D-ND4(알려진 잔여 결함) 때문에 PART 유지. 집계: 설계 항목 OK 1 → 4, DEV 30 → 29, MISS 119 → 117(합계 OK 27 → 30, DEV 37 → 36, MISS 141 → 139).

v1.11(2026-10-15, XRUN-F1 design, 사용자 결정 2026-10-15 "권고대로 진행해" X-1~X-5): 설계 항목 5행 추가(D-XR1·D-XR2·D-XR4·D-XR5 DEV -- 옛 구조가 as-built에 있음, D-XR3 MISS), D-GR4·5·6·9·12·15와 NFR-2 행 문구(상태 불변). D-PF1 대상 소멸(PART → N/A, → D-XR2)과 NFR-2·D-PF1 증거의 `from_sweep` 사실 정정. 집계(v1.10.1 증감을 함께 반영): 설계 항목 162 → 167, OK 0 → 1, DEV 26 → 29(v1.10.1 −1, 이번 +4), PART 16 → 15, MISS 118 → 119, N/A 2 → 3. 합계 OK 27, DEV 36, PART 51, MISS 141, N/A 9. 이어서 사용자 결정 X-8로 D-XR6(DEV) 추가: 설계 항목 168·DEV 30, 합계 265·DEV 37.

v1.10.1(2026-10-15, card 1 xrun 구현 7e1b4be·판정 029f9b7 뒤, 사용자 결정 J-8 "권고대로 진행해"): D-GR3 DEV → OK(병합 직전 갱신, 증거는 판정 기록). 집계: 설계 항목 DEV 26 → 25, OK 0 → 1(합계 DEV 33 → 32, OK 26 → 27). 이 증감은 v1.11 표에 함께 반영했다(위 v1.11 줄).

v1.10(2026-10-15, 사용자 결정 2026-10-15 "나로 해", 실행 사이 재사용 제거): D-GR3을 제거 항목으로 다시 씀(MISS → DEV, 옛 구조가 as-built에 있음), D-ND5 대상 소멸(MISS → N/A), D-GR1·D-GR11·D-GR12·D-ND1·D-ND3·D-PF2 문구. 집계: 설계 항목 DEV 25 → 26, MISS 120 → 118, N/A 1 → 2.

v1.9.4(2026-10-15, 사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해"): 설계 항목 3행 추가(D-ND1 MISS, D-ND2 DEV, D-ND3 MISS -- 34932a9에서 잰, 40 §2.4.3·§2.4.13, 41 §5.13), NFR-4 증거 칸에 설계 절·행 추가(상태 불변). 집계: 설계 항목 157 → 160(DEV +1, MISS +2). 같은 v1.9.4에 사용자 결정 2026-10-15 "기본안대로 진행해"(Q-N1~Q-N10): D-ND3·D-ND4 문구를 결정으로, D-ND5(Q-N5 S3 실행 환경 지문, MISS) 추가. 집계: 설계 항목 161 → 162(MISS +1). 같은 v1.9.4에 독립 검증 지적 B-2 반영: D-ND4(알려진 잔여 결함, DEV) 추가, NFR-4 상태 OK → PART(근거 D-ND1·2·4). 집계: FR·NFR OK 3 → 2·PART 6 → 7, 설계 항목 160 → 161(DEV +1).

40 v1.9.3 as-built 문서 정정 동기화(2026-10-14, 4차 판정 `wt/_audit_u17_1b_r4/audit_report.md` 988eef4·code_hash 판정 `wt/_audit_codehash/audit_report.md` ecda471의 경미 지적): D-GR3의 'N-1 반영 예정' 시점 문장을 구현 7eb4865로. 상태 칸(MISS, 증거 `rg "snapshot_codec"` 0)은 두 판정 모두 기준 시점 004b7d2 '상태 불변' 원칙의 옛 칸으로 일치 판정했으므로 바꾸지 않는다(재측정은 다음 기준 시점 갱신 때, 상태 불변, 행 수 불변, 이 문서 버전 번호 불변).

40 v1.9.3 동기화(2026-10-14, 3차 판정 N-2, 사용자 결정 2026-10-14 "U-68은 권고대로 복구해"·"(가) 경로 인자 필수"·`decl=` "그대로 둠"): D-GR3 문구에 U-68 두 선언 파일 경로 인자·경로↔sha 일치 거부 추가(상태 불변, 행 수 불변, 이 문서 버전 번호 불변).

v1.9.2(2026-10-14, 사용자 결정 2026-10-14 "3~9 모두 권고대로" 4·6·7·8): D-GR3 문구를 40 v1.9.2 §2.4.3에 맞춤, NFR-4 증거 칸에 결함 기록(상태 불변, 행 수 불변).

v1.9.1(2026-10-13, 오케스트레이터 기본안 2026-10-13 U17 ①-b D1~D10, 사용자 결정 아님): D-GR2·D-GR3·D-GR13 문구를 40 v1.9.1 §2.4.3·§2.4.8에 맞춤(상태 불변, 행 수 불변).

v1.9(2026-10-13, 사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ①): 설계 항목 1행 추가(D-AP1 A' 판정 기준, MISS -- master `3151392`에서 잰, 40 §10.5). 다른 행 불변.

v1.8.2(2026-10-13, 사용자 결정 2026-10-13 "1은 권고" d/s 비트 동일 범위 (라)와 U17 ①-a·①-c·①-d 실측 정정): 설계 항목 1행 추가(D-SYg, MISS -- master `980d147`에서 잰), D-GR3(U-68 프로세스당 첫 실제 쓰기 1회·`GMID_S0_SNAPSHOT_DIR`)·D-GR4(분할 대상 GB5 `passive_values`, ② 이월)·D-GR11(허용 모듈 `core/snapshot_codec.py`) 문구 갱신(상태 불변).

v1.8.1(2026-10-13, U17 ①-d·①-e 실측에 문구를 맞춘 정정, 사용자 결정 변경 아님): D-SYf (묶음 수, 변수 수) 정의 = `len(SearchDomain.ties)`·`len(SearchDomain.variables)`(파일럿 29/38, 전류 묶음 7)와 열 정렬 방향(비자명 궤도 원소를 뒤로 = 자유 열 우선), D-SYe 기록 코드 `diff_pair_orbit_split`, D-J8 folded M8 "해제" → "시작 셀 아님 유지". 상태·집계 불변.

v1.8(2026-10-13, 사용자 결정 2026-10-12 "나'로 진행해"·"1, 가로 해"·"2번 승인."·"3번 권고대로"·"4번 권고대로"): 설계 항목 4행 추가(D-J10, D-SYe, D-SYf, D-LY5, 모두 MISS -- master `8e46548`에서 잰), D-J8·D-D1·D-SYb·D-GR3·D-GR12·D-GR13 문구 갱신(상태 불변).

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
