---
template: design
version: 1.15.3
plan_version: 6.38.4
---

# gain-budget-gmid-sizing -- 42-gap-checklist (gap 분석 기준표)

> **Summary**: `bkit:gap-detector`가 설계 문서(40·41)와 구현을 대조할 때 쓰는 표다.
> - **design v1.15.3 -- 계획 v6.38.4(승인 O-173) 맞춤, 검증 대기**(2026-10-29, 40·41과 같은 판 -- 40 Status; 이 문서: D-WB1·D-WB2(슬라이스 고정 P8·P3)·D-START(칸 0 조립 P4)·D-JDG(P1)·D-PW(P7) 확정, D-RMIN 추가) · **v1.15.2 -- 계획 v6.38.3 맞춤**(40 Status; 이 문서: §2 DEC-106 행 추가, D-WB1 정정, D-G4 삭제(N/A -- E-34), D-IT1·D-GL·D-CM·D-TBX 문구, §3 새 14행 D-IN1·D-E13·D-START·D-GS·D-JDG·D-SPX·D-GATE·D-CML·D-LOWN·D-MR·D-PW·D-AREA·D-LA1G·D-CAB, §4 집계)
> - 옛 판 bullet(v1.15.1·v1.15.0) = design 이력 H42-01.
> - 한 행이 FR·NFR·DEC·설계 항목 하나다.
> - 열은 설계 절, 상태, 증거다. 증거는 `파일:행`, test 이름, 또는 재측정용 grep 패턴이다. 판 번호는 41에 맞춘다 -- v1.12.5는 41만 바꾼 판이라 이 문서는 v1.12.4에서 v1.12.6으로 건너뛰었다; v1.12.7 = 계획 v6.28(O-85·O-86) 맞춤, D-IT2 행; 둘째 커밋 = 사용자 O-87 (1)(차동 결합은 S-OS2 card 몫); 셋째 커밋 = 사용자 O-88(MOS 식별 = `device.element_class`); v1.13.0 = 계획 v6.34(사용자 O-106~O-110·DEC-103) 맞춤 -- D-ICM·D-IT2 행을 41 v1.13.0 §4.7에 맞춤(다듬은 창·`metrics_icm_front`·커널 미수렴 이어받기·출력 구조 분류·S-OS1 삭제, KCL 측정 구성 감도, E 칸; design 검증 `wt/_drafts/evidence/2026-10-22/design_v1130_validation.md` S-1), 재검증 90/100(`design_v1130_recheck.md`) 뒤; 계획 v6.34.1 `graph.ss_circuit`·용량만 결측 문언(재검증 3 S-B) 반영(41 v1.13.0과 같은 판); v1.14.0 = 계획 v6.35(사용자 O-114~O-116)·v6.34.2(O-111~O-113) 맞춤 -- D-ICM·D-IT2·D-J5 행을 41 v1.14.0 §4.7(servo 측정 구성, V_cm 좌표, B77)에 맞춤; v1.14.1 = 계획 v6.35.1(O-117)·v6.36(O-118·O-119) 맞춤 -- D-ICM·D-IT2(기본 포트 뷰·전도 행 R0·F 성분 포트 함께 구동·레일 자름)·D-J5(사실 정정), 검증 대기.
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
| NFR-2 같은 키 재계산 0, LUT memo 상한(v1.11: 같은 입력이면 계보 무관 재사용, 계수 범위 = 실행 전체 모든 (블록, 분할) -- 40 §2.4.14, D-XR1~D-XR5) | 40 §7.3 | PART | `E/core/compute_block.py:77`. f23aec8 사실 정정: `from_sweep` 정의 `E/lut/lut_memo.py:54`, 호출 `E/lut/sweep_memo.py:33`(옛 문구 '호출부 0'은 틀림). `from_sweep`은 v1.11 대상 소멸 → D-XR2 |
| NFR-3 IC1~IC11 강제 test | 40 §10.3 | MISS | 패키지별 test 폴더(R26 현행 체계 유지)에서 `rg "def test_ic"` 0 |
| NFR-4 결정론 | 전체 | PART | `E/core/determinism.py`. 구조 규칙 test `tests/structure/test_structure_rules.py`. v1.9.2 결함 기록(결정 8): OpenBLAS 스레드 수 의존(40 §11 U17 ② 선행) -- 상태는 다음 gap 분석에서 다시 잰다. v1.9.4(사용자 결정 2026-10-15): 설계 = 40 §2.4.13·41 §5.13, 설계 항목 D-ND1~D-ND5(D-ND5는 v1.10 대상 소멸, N/A). PART 근거: 엔진 안 BLAS 고정 없음(D-ND1), 경계 배치 결함(D-ND2), 알려진 다른 환경 결함(D-ND4) |
| NFR-5 스펙 맞춤, 여유 판정(v1.16.0 -- 최종 해의 oracle 여유 ∈ [0, 분해능], 닫기 = card CL-1, O-178) | 40 §3.6·§3.10.6 | PART | 분해능은 있다(`E/metrics/sensitivity.py:1-15`, `MetricResult.resolution`). oracle 닫기·예산 점이 없다; as-built c = 여유/max(분해능, e_m)(`E/search/ss_constraints.py`)는 재작성 범위(c = 여유/분해능) |
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
| 11 가장 오른쪽 근 | 41 §4.1, 40 §1 lut 행 | DEV | as-built `E/lut/vgs_root.py:17`(gm/ID → VGS 역산의 '가장 큰 VGS 해')는 사용자 결정 O-186 (A)로 규칙 철회 -- θ 역산 키 = ln IDu(`vgs_for_current_density`), gm/ID 역산 소비자 전수·삭제 = 계획 착수 실측 M-TH1c 재작성 범위(v1.16.0; 옛 상태 OK). **계획 DEC-11 행 문언('rightmost root', 구현됨)은 v6.38.5에서 개정되지 않음 -- 계획 개정 필요로 보고** |
| 12 diode 창의 VDsat 바닥 | 40 §3.7-6 | PART | W4 창 VDsat 항이 결정 대기다(`E/sizing/CONTRACT.md:750-757`) |
| 13 적층 diode | 40 §3.7-7 | PART | `stacked_vsb` 소비자가 연기됐다 |
| 14 diode vds 구간 변수 | 40 §3.7 | OK | `E/sizing/writer_plan.py` |
| 15·64 G_vgs KVL 루프 | 40 §3.2·§3.7-4 | PART | 탐지는 OK(`E/graph/gvgs_cycles.py:56`), 봉인 8도 OK. `structure.json` 로더는 있다(감사 DI2 N1 실측); 남은 MISS = 고리 종속 선택의 ratify 대조 READS(v1.16.0 concept `dependent_member` confirm -- 40 §3.2-3·§3.7-4, card TB-1)와 DEC-64 (v2) 종속 멤버 선택(B 멤버 순위·정준 위치 -- O-187·O-189) |
| 16 초기 L knee | 41 §6.4 | MISS | `rg "knee"` 0 |
| 17 L 동치류 주인 | 40 §3.2 | DEV | `E/graph/CONTRACT.md:220`(`l_class` proposed), `E/sizing/block_lengths.py:7` |
| 18 role 배수 없음 | -- | OK | 구조 규칙 E·I(`structure_checks.py`) |
| 19 warm start L | 41 §5 | PART | 층 0 흡수가 MISS다 |
| 20 `value_from_constraint` | 40 §3.1 | OK | `E/authoring/spec_refs.py` |
| 21 mismatch 5 mV 출처 | 40 §9 Q3, §9.2 | MISS | 사용자 결정 2026-10-08 Q3로 닫힘: 파일럿 5 mV → `offset_in_sigma_mv <= 3.3`(`user_spec`), two_stage·two_stage_sf 5 mV 폐기 → 가드. spec 미반영: `assets/library/current_reuse_telescopic_ota.sizing_spec.json:215`, `two_stage_ota.sizing_spec.json:71`, `two_stage_ota_sf.sizing_spec.json:62`에 옛 `mismatch_sigma_mv`가 남아 있다 |
| 22 bisection(기본 비활성) | 40 §3.10.8 | MISS | 기본 비활성이지만 켜기 경로(`optional_stages` → `achievable_metric_bound(mode="bisect")`)가 설계됐다(사용자 승인(2026-10-12 P), P-13 -- v1.15.2: `optional_stages` 칸은 계획 SF-1 범위 11로 삭제, 켜기 칸은 그 선택을 읽는 card가 읽기와 함께 만든다). `rg "achievable_metric_bound"` 0 |
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
| 58 블록 속성, 출력 구동 | 41 §1.7, 40 §3.8, §3.1-1 | MISS | 기대(계획 v6.38 DEC-58·DEC-65·DEC-104 R9, O-128 Q4·Q5·O-143 (5)(6)) = 방향별 공급 능력 `LsNode.i_charge_a`·`i_discharge_a`(정의 DEC-65 v6.38 범위 끝 순 전류, 계산 DEC-104 R9 -- U-115 닫힘; as-built β/σ/κ 고정 전류는 gap, DE-1 (d)), 소비자 = R8 판정; 피크 행 `ls:load_peak_amp>=`·`load_peak_amp`·`load_dc_amp`·`driving_spec` 섹션 **없음**(`git grep -e load_peak_amp -e load_dc_amp -e driving_spec -- skills/analog-gmid-design/gmid_engine` 비test 0건이 기대 -- SF-1·DE-1 뒤), 엔진 슬루 칸·행 0(O-122 -- `git grep -e c_slew_farad -e slew_charge_v_per_s -e slew_discharge_v_per_s -e 'slew_rate>=' -e _node_capacitance -- skills/analog-gmid-design/gmid_engine` 0건이 기대, test 포함 -- 계획 DE-1 완료 조건 (1)) |
| 59 발동표와 정지 | 41 §1.10 | PART | coverage 파일은 R7 축소 유지로 승인됨(2026-10-08). S1 지원 밖 정지는 있다(`E/graph/CONTRACT.md:352-362`). SP1 `기록만` 분기 정지는 FR-1과 함께 MISS |
| 60 레일 선언 | 40 §3.1 | OK | `E/authoring/rails.py`, `E/authoring/hidden_rails.py:16` |
| 61 벌크 기본값 | -- | OK | `E/graph/bulk_default.py` |
| 62 데이터만으로 토폴로지 추가 | 40 §1.2 | PART | 구조 규칙 E·I는 OK. 이름 전단사 metamorphic test가 없다(`tests/generality/` 6개는 일부만 다룸) |
| 63 R(u) | 41 §1.9 | MISS | `rg "buffer_bundle"` 0 |
| 65 β/σ/κ | 41 §1.9 | MISS | `rg "push_pull\|class_a"` 0 |
| 66 `rout_ss_ohm`과 잔차 | 41 §2.2 | PART | `E/metrics/rout.py`(MNA). 잔차 MISS |
| 68·69 명명과 옛 이름 거부 | 40 §3.1 | DEV | FR-9 |
| 70 AC→DC 제약과 θ 정의 | 40 §3.7, 41 §5 머리말 | PART | 미러 비 강제 MISS(`E/sizing/CONTRACT.md:276`). (옛 '슬루 제약' 항목 삭제 -- 슬루는 θ 제약이 아니다, 계획 v6.37 DEC-70·O-122.) v1.15.0(계획 v6.38 DEC-70 M11): θ 독립 성분 = S·F ln IDu·L·고리 종속 아닌 y·θ 전류, B ln IDu·V_R·종속 W4는 R6 블록 파생, 값 미선언 저항 R = V_R/I_R 파생 -- as-built θ 스키마(`E/sizing/theta_schema.py`)는 W4·값 미선언 저항 값을 θ 성분으로 센다(gap, card LA-1; 외층 SLSQP 변수 변경의 척도·front 영향 미측정) |
| 71 층 0 기둥 조립 | 41 §5 | PART | (1) 가지·기둥 OK(`E/graph/columns.py`). (2)~(8) MISS. v1.15.0: (3) 블록 전류 = KCL·선언·R8·R10 하한(41 §5.3.1·§6.8-1), (4)(c) VDS·V_R 배분 (c-1)~(c-3)(41 §5.3.4 -- (c-4) 삭제 O-155 M-2), (7) 조립 = 확인(41 §5.5) -- 모두 MISS |
| 72 대조 기록·oracle 닫기(v1.16.0 -- 계획 DEC-72 개정, 사용자 결정 O-178: 옛 '모델 오차 선언값' 폐지) | 40 §3.6·§3.8-6, D-CL1 | MISS | 대조 기록 칸·oracle 닫기 0(card CL-1). as-built 주석·이름 `model_error_`(`find_front.py:86`, `ss_constraints.py:14,24`)·`E/metrics/model_error.py`는 재작성 범위(지움) |
| 73 기본 경로 = 층 0 + 외층 | 41 §5.9 | PART | 층 0 예산 MISS |
| 74 외층 전회로 판정 | 40 §3.8 | PART | `E/search/search_context.py:84-105`(레지스트리 밖 metric은 notes에만 남는다) |
| 75 선언으로 켜는 기능 | -- | OK | `E/authoring/spec_settings.py:34` |
| 77 (전력, 면적) front | 40 §3.6 | PART | front는 OK(`E/search/find_front.py:72-120`). 예산 점 MISS |
| 78 전력 축 | 40 §3.8 | PART | Σ V·I는 결정 Q6(2026-10-08)과 일치한다(`E/search/objectives.py:9`). 기둥 대조 MISS. DEC-78 문구 정정 필요 |
| 79 면적 탐색 축·판정 축 | 40 §7.1, §3.9 | PART | `E/metrics/dc_metrics.py:18-19,80-83`. MIM은 `[ng-area-budget]`에만 있다. 판정 축의 수동소자와 재필터 MISS |
| 80 면적 눈금, bin | 41 §5.2, 40 §3.6 | PART | b_A = grid × W_min(`E/search/eps_sweep.py`). 면적 축 두 눈금 차(Q-EM1) 항 MISS(v1.16.0 -- 옛 '모델 오차 항', O-178) |
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
| 95 탐색 방법 묶음 | 40 §3.7, §3.9 | PART | ΔA_tie가 grid²다(`E/layout/floorplan.py:83`). DEC-95 (3)(v6.38.5 -- `kvl_branch`는 DEC-64 (v2) 종속 멤버 선택, 그 밖 비트리 관계는 ratified → diode → ② → 궤도 대표 → 정준 위치, O-187·O-189)은 일부만(① 구조 색·이름 키 -- `E/sizing/writer_plan.py:13-17`, card TB-1 재작성 범위; D-TB1d) |
| 96 nqs·mismatch 보고와 범위(잡음은 사용자 결정 2026-10-08로 범위 안, (2)는 Q3로 A_eff·offset metric) | 40 §3.8, 41 §6.4-2, §7 | MISS | `rg "nqs_ratio\|offset_in_sigma\|mirror_ratio_sigma"` 0. 잡음은 D-NZ1~6, 미스매치는 D-MM1·2, D-OF1~3, D-MR |
| 106 입력 공통모드 변수 하나(v1.15.2 신설 -- 계획 v6.38.3 DEC-106, 사용자 결정 O-168·O-170) | 40 §3.11-4·§10.7, 41 §4.7-V·§6.7-1a | MISS | 구현 card: IT-1 v6.38.3 범위 재작성(D-IN1), SF-1 U-128 data(4회로·current_reuse·common_gate `engine`, nmcnr `agnd`), CPG-1 bench 입력 DC |
| 105 C′ 앞단 결정 묶음(v1.15.1 신설 -- 계획 v6.38.2 DEC-105 (1)~(12), 사용자 결정 O-164·O-165·O-166) | 40 §3.7-A·§3.1-1·§3.8-9·§5-6·§10.5·§10.7, 41 §4.2·§6.4-1·-2·-2a·-6·§6.5-3a·§6.7-4 | MISS | 구현 card: WB-1(D-WB1~3), LA-1 범위 15(D-GL·D-MP0·D-MV·D-TB1c·D-AR·D-CMB), RS-1(D-RS1), SF-1 범위 8·9(D-CR·D-TBX), CPG-1(D-CPG); (11) 슬루 비차단 하한 = 대체됨(U-125, 변경 없음), (12) 재측정 = LA-1 완료 조건 9 (f)(40 §10.5-6) |
| 104 θ 기저·손계산 순서(v1.15.0 신설 -- 계획 v6.38, 사용자 결정 O-127·O-128·O-141·O-142·O-143·O-144·O-146) | 40 §1.2 EP-10·§2.4.8, 41 §5 머리말·§5.3.3·§5.3.4·§6.7-11·§6.8 | MISS | 구현: 필드 = card TB-1 범위 1·2(D-TB1a·b), R7 가드 필드·체계 오프셋 술어 인스턴스 필드 = card LA-1 범위 15 (d)·(c)(U-132 -- D-TB1c), R6 블록 = card LA-1(D-R6·D-R5p), R8·R10 공급 요구 하한 = card SB-1(D-R10). `rg "theta_class\|loop_dependents\|start\.guard"` 0이 지금 상태 |

## 3. 설계 항목 (40·41에서 새로 정한 것)

| ID | 항목 | 설계 절 | 상태 | 증거 |
|---|---|---|---|---|
| D-GB0a | spec 필드 `gain_budget_db_override`·~~`driving_spec`~~(v1.15.0: card SF-1이 지움 -- D-SF1a)·`symmetry_untie` | 40 §3.1 | MISS | `E/authoring/SPEC_CONTRACT.md:226` |
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
| D-P9 | 사이징 대상 회로 전부(library 13 -- O-181) 축소 격자 전수 대조(전회로 MNA, 축별 최적값 차·같은 ε front 점 차 ≤ 그 축의 분해능(면적은 DEC-80) -- v1.16.0, 모델 오차 항은 O-178로 소멸)(P-9, N3.7·NFR-5) | 41 §9 | MISS | 축소 격자 정의는 41 §5.12.5 PQ1 |
| D-P15 | 이득 블록과 섞인 회로의 버퍼 블록 rout 국소 제약·면적 bin DP 단계(P-15, DEC-71 (3)) | 41 §5.1·§5.6 | DEV | U15 as-built는 섞인 회로의 버퍼를 기준점 gain 상수항으로만 넣는다 |
| D-FV1 | 이식 투영 = 값 기반 정준 사상, `fixed`는 extras로만(국소 → 조립 이식) | 40 §2.4.4 | MISS | `rg "def graft"` 0 |
| D-FV2 | d/s 자기 맞바꿈 → `unsupported_rule_branch`(`ds_self_swap_zero_current`), toy test | 40 §6-8 | MISS | `rg "ds_self_swap_zero_current"` 0 |
| D-FV3 | DEC-12 diode 창 VDSAT 바닥·명시 실패, DEC-13 적층 diode 2변수 공동 풀이 | 40 §3.7-6·7 | PART | `E/sizing/CONTRACT.md:750-757`(W4 창 VDsat 대기) |
| D-FV4 | 단위 보고 `broken_tests`·`criteria_weakened`, `--profile`, DEC-51 공유 블록 전후 대조 도구 | 40 §3.10.8, §10.4 | MISS | `rg "criteria_weakened\|--profile"` 0 |
| D-FV5 | 정밀 경로 선언 정지(U-66 결정), 복합 블록 상한 N_S(U-65 결정) | 40 §3.10.8·3.10.11 | MISS | `rg "precise_path_not_implemented"` 0 |
| D-FV6 | U-23·U-33 측정 도구 `tools/compare_paths.py` | 40 §3.10.10 | MISS | 파일 없음 |
| D-FV7 | U-67(사용자 결정 2026-10-12 "U-67은 (나)로"): L 혼합 interdigitation 행 대칭 검사(`interdigitation_not_mirror_symmetric`), `ly.lod` finger별 sa·sb·sd → 오라클 넷리스트, WPE·PSE 제외 | 40 §3.9, §3.10.8, §4 | MISS | `rg "ly.lod\|interdigitation_not_mirror"` 0 |
| D-K1 | 41 §6.7 KVL 고리 출발 제약: K-1 공동 선택 순서(위반 최소 → max-min → 위치 합 최대), 실행 불가 시 올린 묶음 상한 반분 재풀이(최대 steps+1), `StartConflict(kvl)`, PQ5(출발 단계 A8에도 등식), K-3 `input_tie` 폐기. v1.15.0(계획 v6.38 DEC-104 R5′·R7, O-142): 비용 순 재개방(W4·V_R → B(R7 가드 안) → S 정의역), max-min 대상(B = gm/ID 위치, W4·V_R = 행 여유), 행·의존 묶음 = R-1′ 필드 READS(`graph/start: kvl_model`·`kvl_rows` 없음), 원리는 S·F 한정 | 41 §6.7 | MISS | `rg "kvl_choice"` 0. v1.15.0 기대: `rg "kvl_model\|kvl_rows"` 0 |
| D-K2 | 41 §7.5 β·C_eff 입력 배선(feedback 절단, C_eff 노드), 비대칭 귀환 계수 '추정'(U-70), N_in = Σγ_k·gm_k/(γ_avg·G_half)(K-2 결정) | 41 §7.5 | MISS | U13 열린 항목 `feedback_factor_beta_unavailable` |
| D-C4 | 잡음 B 평탄(plateau) 규칙(피드스루 + 이웃 점 일치), 칸별 적응 재측정 구현 단위(미상·엇갈림·계단형 칸, 로그 이분, 상한 K_max, noise r2) -- 시점 = graph 재작성 ①~③ 뒤, U16 전(C-4) | 41 §7.2 | PART | plateau는 as-built `noise_planes.py`와 일치, 재측정 단위 없음 |
| D-D1 | d/s 맞바꿈 궤도를 넘는(KCL 유도) 전류 묶음 상자 = 구성원 상자 교집합, 비면 거부 `tied_current_box_empty`(U-61 D-1). 같은 궤도 안 불일치는 `tied_orbit_bounds_differ` | 40 §6-8 | MISS | as-built `search_domain`은 `tied_orbit_bounds_differ`로 거부 |
| D-G1 | IC11 픽스처: 거부 = 합성 음전위 레일·pushpull(supply_nets 삭제), 동등 = two_stage_ota 2레일·pushpull 3레일 | 40 §3.10.8, §10.3 | MISS | `rg "def test_rail_origin_shift_invariance"` 0 |
| D-G2 | 문자열 값 안 옛 이름 test, `human.objective` 형식·`duplicate_axis_budget`, spec `origin` 규칙(U-04 결정) | 40 §3.1 | MISS | -- |
| D-G3 | LY1 쌍 전류비 규칙(U-71 결정, 사용자 결정 2026-10-12 "U-71승인") | 40 §3.10.3 | MISS | -- |
| D-G4 | ~~보상 단 폴백(U-51 결정): SLSQP maxiter 미수렴 시작점만 보상 단 GB5 고정 재풀이, `compensation_fixed_fallback` 기록·'추정', 9회로 빈도 보고~~ -- **삭제**(계획 N6.35 E-34, O-169: 미수렴 = 목표 미달 = 정의된 출발값, 둘째 경로) | 40 §3.6 | N/A(삭제) | `rg "compensation_fixed_fallback"` 0 유지 = card LA-1 범위 15 (g) |
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
| D-SYf | 전류 기저 열 순서: 결정 취지 "대칭 궤도 원소를 자유 열로 먼저 남긴다" = 자유 열 선택에서 비자명 궤도 우선, 행사다리꼴이 앞 열을 pivot으로 잡으므로 열 정렬 키 = (궤도 비자명이 뒤, `dc_colour`, DEC-97 정준 위치)(v1.16.0 -- O-189, 옛 마지막 키 '이름'; `dc_colour`가 정점마다 유일이라 마지막 키는 정의상 공허)(앞에 두면 파일럿 27/40). `current_basis`가 `graph/s1: orbits` 읽음. (묶음 수, 탐색 θ 변수 수) = (`len(SearchDomain.ties)`, `len(SearchDomain.variables)`): 파일럿 29/38, 그중 전류 묶음 7(M1a~M1b, M19~M10), 나머지 8회로 = master `8e46548` as-built 값, 28/39(규칙 전, 전류 묶음 6)는 기록만 | 40 §6-3·§6-8 | MISS | `E/sizing/current_basis.py:8` 열 순서 = (`dc_colour`, 이름), orbit 읽기 0 |
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
| D-ICM | `icmr_v`·`icm_margin_v`·`required_input_cm_v` = **V_cm 좌표**(입력 포트 전압 평균 -- 계획 v6.35 N3.8 'ICMR 좌표', U-106: `icmr_v` = V_cm 끝 차, `icm_margin_v` = min(V_cm0 − 아래, 위 − V_cm0), `required_input_cm_v` = (V_cm0, 아래, 위)), SP-2 대기면 `input_dc_pending`, ICMR 제약 = 폭 + 포함. IT-2 설계(41 v1.14.0): 측정 구성 = servo(O-115 -- 감지를 봉인점에 묶고 여기 방향 e 보정, 단일 입력 = 회로 그대로; ICMR 전달 뷰 = S1v 기본 포트 뷰(O-118 6번), 창 행 = 포화·`triode` + 전도 행 R0(O-118 2번), F 성분 미선언 포트도 함께 구동(O-118 3번), 끝 상태 레일 자름(O-117)), 값 출처 = `graph.icm_config` V_cm 칸(writer `icm_config`), 포트 창 = `node.dc_window_cfg`(봉인점 KCL 선형 감도 끝 '추정' -- O-108·O-109 C1; 정확값 oracle `.dc` servo), 정의 함수 `icm_window_metrics(config, ports, input_dc)`(부르는 자리 `metrics_aux` 하나, 포트 창 산술 0 -- AST), 영역 칸 `dc`(IT-2d relabel -- O-112) | 40 §3.8-8, 41 §4.7-2·§4.7-3b·§4.7-5 | MISS | `rg "icmr_v\|icm_margin" E/` 0. ngcc spec은 `{metric: pending MOD5}`(`assets/library/ngcc_3stage_ff.sizing_spec.json:87`) |
| D-Q34 | §9.2 회로별 선언(파일럿 3.3 mV·스윙 2.4 V·icm_margin, 6회로 가드, ngcc `icmr_v >= 0.6`, nmcnr `icmr_v`·`swing_out_v >= 0.5`)과 옛 이름 거부(`mismatch_sigma_mv`, `mirror_ratio_error_mv`, `mismatch_sigma_v`) | 40 §9.2, §3.1 | MISS | `assets/library/*.sizing_spec.json`(옛 이름 3개 회로), `E/authoring/SPEC_CONTRACT.md:261` S2 |
| D-GB4f | 헤드룸 달성가능성: 출력·입력·버퍼 창 상한(LUT 격자 전수, 인증/미상), 선언 제약 인증 불가 → exit 3 `headroom_unattainable`, 제약 없는 창·입력 DC 대기는 보고, 유도 기록 | 41 §4.6 | MISS | `rg "headroom_bound\|headroom_unattainable" E/` 0 |
| D-SIg | 출발 구간 Q3·Q4: 스윙·ICMR·입력 DC 예산 분할(41 §6.2), A_eff matching L 하한(절대 offset 회로만, 41 §6.4-2) | 41 §6.2, §6.4-2 | MISS | `rg "start_intervals"` 0 |
| D-OR5 | 오라클 offset Monte-Carlo(표본 수 유도, 엔진 차 = 대조 기록 -- v1.16.0, 옛 `model_error_offset_in_sigma_mv`, O-178)와 스윙·ICMR `.dc` 스윕 | 40 §10.2 | MISS | `rg "mc_mm_switch\|offset_mc" tools/spice_oracle` 0 |
| D-J34 | J 공동분석 목록 추가: 입력 DC 값(nmcnr 0 V, SP-2), sf_pushpull M6↔M8·M5↔M7 matching, 4-팔로워 버퍼 헤드룸 | 40 §9 Q7, §9.3 | MISS | 해석은 2026-10-08 결정으로 닫혔다(40 §9.3 J-D·J-E). 구현 확인은 D-J1·D-J5·D-J7 행에서 한다 |
| D-J1 | 복합 diode D1: DC 가지 걷기 정의, 묶음·기준/캐스코드 구분, 소비 셋(DC 역할 규칙 1c, 미러 입력 확장·`diode_load`, 루프 (1.6) `composite_diode_internal`). 9회로 발동 = 41 §1.13 실측 집합, 나머지 7회로 무동작 | 41 §1.12.1, §1.13 | MISS | `rg "composite_diode" E/` 0. `[u1-sp1] E/graph/drive_kind.py` `_mirror_inputs`는 단순 diode만 본다 |
| D-J2 | feedforward 셀: 주경로(D_max·slack), FF 묶음·탭·merge·B_b, 블록 분해(FF 합류는 복합 블록 아님), gain 예산은 주경로만, 경로 기여·A_decomp 잔차, `ff_ratio_candidates`·`ff_gm_ratio`, Σ 판정 FF 상한, FF 출발값 | 41 §1.12.2, §2, §4.3, §5.1, §6.5, 40 §3.8-8 | MISS | `rg "feedforward\|ff_gm_ratio" E/` 0. `[u1-sp1]`은 ngcc Vout을 복합 블록 하나로 묶는다(`composite_block_pending_ratify`) |
| D-J3 | 중첩 Miller 보상 내부 루프: 조건 (a)(b), 루프 뷰 미생성, `pm_ss_deg` 미선언이면 `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`), 전체 PM 판정의 P = 0 확인 | 41 §1.12.3 | MISS | `rg "compensation_internal" E/` 0. `[u1-sp1]` ngcc·nmcnr에서 `undeclared_loop_constraint` 정지 |
| D-J4 | 루프 극성 = 뷰의 DC 사이클 극성, 커패시터 사이클 `ac_only`, `loop_polarity_conflict`. L 동치류 주인 규칙 `main_path_signal`, name_order는 review | 41 §1.12.4·5 | MISS | `[u1-sp1] E/graph/polarity.py`(커패시터 사이클 → 0 → review), `l_classes.py`(주인 순서 3단계) |
| D-IT1 | card IT-1: 입력 포트 '같은 DC' 엣지(`input_tie`) 폐기, 입력 포트 뿌리 y 키 = 넷, ~~`input_port_multiple_roots` 정지~~(DEC-106 입력 점 한 점으로 대체, D-IN1) | 41 §4.7-1, 40 §11 IT 행 | MISS | 구현 전(계획 N6.5 완료 조건 1~7) |
| D-IT2 | card IT-2(41 v1.14.0, 계획 v6.35·v6.34.2): 입력 CM 창 단일 정본 -- `node.dc_window`(θ 프레임, **W4 뿌리 항목만** -- O-109 D1)·`node.dc_window_cfg`(측정 구성 판정 창, `icm_config`, **모든 측정 구성의 KCL 선형 감도 끝 하나**; 상태 {measured, unmeasured}, 커널 상태 이어받기 없음·READS에 `node.dc_window` 없음 -- O-109 D2; F 성분 미선언 판정 없음 -- v1.14.1 O-118 3번), **ICMR 측정 구성 = servo 하나**(사용자 결정 O-115·U-105 -- `graph.ss_nodal` 위 vx·ve 두 풀이와 감지 행 δs = 0 Schur 1칸 `kvl_sensitivity(nodal, drive, servo)`, 단일·차동 출력 같은 연립, 단일 입력 = `as_is_single_input`; ICMR 전달 뷰 = 기본 포트 뷰(O-118 6번) -- S1v writer가 기본 포트 뷰를 늘 두고 `ViewS1v.default_port`로 식별, `icm_config` READS `graph.views`; `IcmConfig(config, pivot_a_e, pivot_resolution, vcm0, vcm_lo, vcm_hi, undefined)`, 피벗 칸 출력 전용, V_cm 칸 소비자 `metrics_aux`(U-106); 정의 불능 code = `passive_value_undeclared`·`icm_inputs_unsupported`·`view_required`·`icm_servo_pivot_unresolved`; 끝 상태 = 레일 안 입력으로 자름(O-117); 경계 행 = `region_rows`(포화·`triode`) + `_conduction_rows`(전도 행 R0, O-118 2번, 행 꼴 일반 1차 행); F 성분 미선언 포트도 구동(O-118 3번 -- cfg 상태·code·상수·`writer_head` 삭제)), **삭제 확인**(계획 (8)(f)): `inverting_port`·`tied_ports`·`transfer`·`declared_feedback`·`follower_beta1`·반전 입력 식별 code 셋·S-OS2 code·`icm_config_differential_output_undeclared`·`icm_config_feedback_*`·`icm_config_feedback_cut`·`_dc_feedback_reaches`와 S1 READS 넷, `icm_view_ambiguous`·`icm_excite_common_mode`·`input_window_f_component_undeclared`·`SizingSpecDoc.icmr_view`·`DcInputs.icm_view` 0(절단 넷 순수 함수·`_input_side` 대체는 card TN-1 -- 계획 N6.26), `graph.ss_nodal`(세 자리 이전, E 칸 `g_bound` -- `conductance_matrix(…, bound=True)` 호출 자리 하나·`__canonical__` 포함, O-107; 저항 결측이면 값 = `Undefined`(detail `("elements", …)`)·`icm_config` `passive_value_undeclared`), `graph.ss_circuit`(writer `ss_circuit` 하나, 조립 사본 둘 삭제; 원래 취지와 다름(범위 확대)), **B77**(card IT-2d, 계획 v6.34.2 O-111~O-113 -- registry 영역 칸 relabel `dc`(`ff_gm_ratio` `ss` 유지), `metrics_aux._missing_gate` = 영역 `MetricSignature.domain`에서만·`dc`는 `graph.ss_nodal` Undefined일 때만 정의 불능, 결측 시 전달 뷰 보고만 막음, 영향 test 다섯 파일), 스냅샷 파생 규칙(keep = `ctx.base` writer ∪ 호출 블록·parent 일치 검사 확장·봉인 4 coverage·서로소 단언 -- O-61 P1), 창 끝 함수 `saturation_window` 하나·**부르는 자리 둘**(`dc_columns`·`icm_config`; 서명 `root` 하나 -- O-61 P2·검증 N-5), 모든 측정 구성 포트 끝 = `node.dc_window_cfg` 한 칸(`IcmConfig` `kvl` 칸 없음, O-61 P3·O-109 C1), F 성분 미선언 포트 = θ 창 항목 없음·cfg는 함께 구동(O-118 3번), 고립 포트 = 뿌리 창 절차(O-61 P4), 커널 미수렴 = θ 프레임 창의 출력 전용 상태(O-109 D2), `IcmWindow` 사본 칸(`criterion`·`config`·`sources`) 없음, **없는 것**(O-109 C1·D4): `node.dc_window_def_refined`·`dc_window_refine`·끝 풀이 함수·`metrics_icm_front`·`refine_front_windows`·`node.dc_output_structure`·S-OS1 code; `Circuit` 행 부분 공용 helper 이동·`sizing.__all__` 공개(U-101 (가′), 일곱 이름 -- v1.14.1); 판정 분해능 정의 함수 `_transfer_resolution`(δV_out = \|z_u\|ᵀ(\|r\| + E\|v\|) -- O-107, 대상 = servo 피벗 a_e → `IcmConfig.pivot_resolution`), IT-2c 착수 실측 (a)~(e)(41 §4.7-3b) | 41 §4.7-1a·§4.7-2~§4.7-7, 40 §2.4.8·§3.8-8·§10·§11 IT 행 | MISS(IT-2a·IT-2b 병합 `6afe4758`, IT-2c·IT-2d 구현 전) | 계획 v6.36 N6.6 완료 조건 (0)~(13) |
| D-J5 | 입력 DC 정책: SP-2 (c) y_icm 창 범위, `required_input_cm_v`, sf `icm_margin_v >= 0` 제약, `buffer_window_report`, `icmr_window_short_l_bin` 경고 | 41 §4.6·§4.7-5(v1.12 IT-2 -- `required_input_cm_v`는 `icm_window_metrics`, v1.14.0 V_cm 좌표 -- U-106), 40 §3.8-8, §9.2 | MISS | `rg "required_input_cm\|short_l_bin" E/` 0. `assets/library/sf_pushpull_output_opamp.sizing_spec.json:141-148`에 `icm_margin_v >= 0` 제약 있음(v1.14.1 사실 정정 -- gap N-5, integ-it12 `3179cd78` 재측정) |
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
| D-GB7c | 종속 멤버 선택(DEC-64 (v2)·DEC-95 (3) v6.38.5 -- v1.16.0 정정, 옛 'DEC-95 (3) 전체 순서') -- 행 정본 = D-TB1d | 40 §3.7-4 | MISS | as-built `E/sizing/writer_plan.py:13-17`(① 구조 색·이름 키·OrderHints)는 card TB-1 재작성 범위(옛 상태 PART) |
| D-GB7d | W_request 고정 W | 40 §3.7 | MISS | `E/sizing/block_widths.py:9` |
| D-GB8a | DC 동작 범위 방향별 공급 능력(v1.15.0: 정의 DEC-65 v6.38 범위 끝 순 전류, 계산 DEC-104 R9 -- U-115 닫힘, 소비자 R8 판정; as-built `ls_fields`, 엔진 슬루 칸 0(O-122)), 스윙·ICMR은 D-SW·D-ICM | 40 §3.8 | MISS | -- |
| D-GB8b | nqs 보고(미스매치 보고는 D-OF1·D-MR로 대체) | 40 §3.8 | MISS | -- |
| D-GB8c | `verified_by`(엔진 metric ↔ oracle measure 대응만 -- `model_error_ref`·`max_error` 칸 없음, O-178; 레지스트리 밖 oracle 전용 항목 `_ORACLE_ONLY` 포함 -- 40 §3.8-6, card VB-1), `spice_unverifiable` | 40 §3.8 | MISS | -- |
| D-GB8d | ~~`load_dc_amp` 선언 = 출력 포트 KCL의 이상 전류원 항~~ -- **v1.15.0: 키 삭제**(계획 v6.38 DEC-58·SF-1 범위 2, 사용자 결정 O-128 Q5 -- DC 부하 = netlist 전류원 원소, 선언하면 로더 거부(fail-closed)). 기대 = `git grep load_dc_amp -- skills/analog-gmid-design/gmid_engine` 0건(SF-1 뒤, test 포함 -- test 역할이 고침) | 40 §3.8-3 (다), §3.1-1 | MISS | 엔진 비test 소비자 0(`git grep load_dc_amp -- skills/analog-gmid-design/gmid_engine` 비test 결과 = `authoring/spec_driving.py`·`spec_model.py` 읽기와 `search/ls_constraints.py:5` 머리말뿐 -- integ/it12 `3179cd78`) |
| D-IC | IC1~IC11 계약 test(패키지별 폴더) | 40 §10.3 | MISS | `rg "def test_ic"` 0 |
| D-T | test 폴더 체계 | 40 §8 R26 | N/A | 축소 유지 승인(2026-10-08). 현행 체계를 쓴다 |
| D-GR1 | graph 밖 저장소는 셋뿐(LUT memo·S3 기록과 색인·실행 계수 -- v1.10 S0 직렬화 폐지) | 40 §2.4.1 | DEV | `E/search/search_context.py:58-67`(cache·computed_keys·cell_floors 등 -- master `b9af2d6f` 재측정, v1.12 단일 정본 감사 F4; `local_seal_memo`는 엔진 소스에 없음, `git grep -w` 0) |
| D-GR2 | S0 수준 층 필드화(S1v·결합 변수·GB4·출발 구간·metric 구조 입력). 레코드별 필드 = 40 §2.4.8(v1.9.1 D1~D4·D7~D9: `graph/s1v` `coverage`·`graph/ach` `block_bounds` 없음, `graph/start` `rungs` = as-built `ladder`, `noise_inputs`·`placement`는 U17 ②, `local_inputs` dict→tuple·memo 제외) | 40 §2.4.2·2.4.8 | MISS | bd19cc6 `sctx.s1v`·`sctx.ach`·`sctx.start` 객체, `E/search/start_values.py:186-235` `StartContext` |
| D-GR3 | 실행 사이 재사용 제거(사용자 결정 2026-10-15 "나로 해"): S0 수준 층 = 실행 수명, 디스크 스냅샷·S0 키·코덱·타입 등록부·U-68 정리·`run_stage_a` PDK 선언 경로 인자와 진입 sha 대조·`GMID_S0_SNAPSHOT_DIR`·S3 실행 사이 읽기(이전 front 점 시작점, 디스크 실패 기록) 삭제. 엔진 코드 지문은 결과 기록 출처 칸으로만, 블록 코드 해시는 실행 안 입력 버전으로 유지(checkout 무관 성질은 Q10). 옛 항목(S0 스냅샷 영속화, v1.9.1~v1.9.3 문구)은 history | 40 §2.4.3 | OK | [xrun 7e1b4be, 판정 029f9b7] 엔진 소스·CONTRACT에서 삭제 이름 20개 `rg -w` 0(`snapshot_codec`, `S0Slot`, `type_registry`, `disk_failures`, `_s3_thetas`, `load_evals`, `pdk_decl_path` 등), 9회로 새 프로세스 두 번 비트 동일·`.s0_snapshot` 생성 0, S3 미리 채움 = 빈 S3 |
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
| D-P2 | 소자별 폭 슬라이스(`LutAccess.w_keys` 소자 키, `w_key_of(lut, device)`), LY2 행별 finger 폭 -- **v1.15.1 운반 꼴 개정**: 소자 슬라이스는 DC 블록 안 값(`LutAccess.w_keys` 삭제, 기본값 = W-bin 슬라이스) -- D-WB1~3이 닫음 | 40 §3.10.1·§3.7-A | DEV | bd19cc6 `LutAccess.w_keys` = kind 키, `convergence/place_layout` `layout_score` 최소 키 |
| D-P3 | LY5 nf → W → 완화, 종속 소자 W 고정 입력(봉인 2 판정) | 40 §3.10.2 | DEV | MOD8 gap (b)(종속 소자 W 고정 불가) |
| D-P6 | MOD8 열린 항목 닫음: 쌍 전류비 보장 규칙, `key_exclusion` 삭제, 면적 축 두 눈금 차(Q-EM1 -- 옛 '면적 모델 오차', O-178) 기록만, front 뒤 재측정 | 40 §3.10.3 | MISS | `rg "key_exclusion"` (convergence) |
| D-P7 | DEC-88 반전 수준 하한 = 연속 부등식 제약 행(bounds 조임 폐기) | 40 §3.10.4 | DEV | `search/CONTRACT.md:573`, `E/search/cell_floor.py` |
| D-P8 | DF 재발 금지 표(DF-01~37 → 계약 test → 단위) | 40 §10.3a | MISS | `rg "def test_df"` 0 |
| D-P10 | finger 피치 여유 PDK 유도(I-A12) | 40 §3.10.5 | MISS | 옛 `PROCESS_GEOMETRY["finger_pitch_overhead_m"]` = 0.0 |
| D-P11 | 최종 해 활성 제약 여유 판정·활성/비활성/보류 보고(NFR-5) | 40 §3.10.6 | MISS | front 표 `constraints[].state` 없음 |
| D-P12 | 규칙 분기 발동표 결과 JSON `rule_branches`(DEC-59) | 40 §3.10.7 | MISS | `rg "rule_branches"` 0 |
| D-P13 | 누락 항목 일괄: `dc_id_source`, tol_V 정의, 결합 잔차 쓰임(`residual_table`·`trust_limits`), LY8 3열, 근방 반경 확장, IC3·IC7·IC11, T1·T7·T8 형식, `layer0.ac_inactive`, bisection 켜기 경로, TS7 strict xfail | 40 §3.10.8 | MISS | 항목별 grep 0(`dc_id_source`, `trust_limits`, `metric_columns`, `ac_inactive`) |
| D-AP1 | A' 판정 기준(P DEC-98, 사용자 결정 2026-10-13 "1은 권고, 2도 권고, 3도 권고대로" (3)과 "①, ②, ③ 권고대로 진행해" ①): 판정자 ngspice(MOD8 전 점은 T4-pre), 독립 대조군 AI 손분석(결정 원문 "코드 없음" -- 엔진 코드 미열람, LUT 조회·계산 보조 스크립트 허용; 회로마다 1회 고정 문서; 엔진 입력 아님; 작성 주체 ≠ 엔진 코드 작성 주체), 피검 엔진 시작점·front 점(P U-45). 판정 규칙(엔진만 실패 = 엔진 결함 대조표, AI만 실패 = 공동분석 기록·그 회로 완료, 둘 다 통과 = 전력(ngspice)·면적(엔진 면적 코드에 손분석 W/L/finger) 차, 둘 다 실패 = 판정 불능). U17 단계 ② 완료 조건(v1.16.0 -- O-175·O-178·O-181): library 회로 전부(13) + held-out 회로(지금 0개 -- 새 held-out 제공 전 일반성 판정 정지)에서 시작점 봉인 통과·spec 제약 행 c ≥ 0·ngspice(T4-pre·T5) 판정(불합격 = 대조 기록, 엔진 결함은 E-0·정의 동일성 위반만), front 점은 oracle 닫기 뒤 ngspice 통과, 엔진 실패 회로가 남으면 미완료(fail-closed), library 도달률 회귀 지표. held-out 선정·제작 P U-75(사용자 몫, 관측 보고만), 세부 P U-76 (1)~(9) 기본안. oracle 전용 제약(P DEC-98 (6), 확정 O-124): `unmeasured_front` 중 미측정 사유가 `oracle_judged`뿐인 점도 oracle 판정 입력, 그 불합격 = `oracle_only_fail`(엔진 결함 아님); v1.15.0: U-112 닫힘(O-143 (4)·O-144·O-145) -- FAIL 점·추종 정의 불능 점 front 제외·기록, 되먹임 없음, 합격 점 = FAIL 제외의 여집합으로 최종 front 후보 + 비지배 재필터(design 읽기 -- 검증 확인 대상), 슬루 선언 held-out 회로 완료는 그 front로 판정 | 40 §10.5, §11 U17 ② | MISS | 저장소 안 손분석·A' 대조표 문서 0, held-out 회로 0(U-75 미정), `docs/03-analysis/aprime/` 0, T4-pre 오라클 입력(sizing W·비례 접합 기하) 0, `constraint_rows` 미구현(D-GR13) |
| D-ND1 | BLAS 스레드 고정·확인(fail-closed, 무상태 재확인 (a)~(e))과 결과 기록 칸 실행 환경 지문 `env_fp`(단계 A 보고서·S3 runs 줄)(사용자 결정 2026-10-15 1안, v1.10: S0 키 (iv)는 대상 소멸. 파일·이름·기록 자리는 40 §2.4.13 (1) J-1·J-2·J-4 오케스트레이터 기본안) | 40 §2.4.13 (1) | OK | `E/core/blas_env.py`(pin_blas_threads·blas_environment, 소유 BLAS 확인은 재확인 포함 -- N-6), `E/__init__.py:5-7`, 재확인 (a)~(e) `stage_a.py`·`search_context.py`·`find_front.py`·`layer0_center.py`·`slsqp_outer.py`, `env_fp` 단계 A 보고서·runs 줄 -- 판정 기록 `.ai/verification/nfr4c2.json`(audit a18c6b2, 병합본 ebd7b3c: suite 10089 passed/0 failed, A-4 36/36) |
| D-ND2 | 판정 경계 위 배치점 규칙 BP1~BP3, 층 0 끌어올림 닫힌 식(3안) | 41 §5.13 | OK | `E/search/layer0_center.py:243-265` 닫힌 식(√ε = math.sqrt(sys.float_info.epsilon)), `lift = u` 삭제. 범위 밖 기준선 변화 3회로는 사용자 결정 N-5로 수용 -- 판정 기록 `.ai/verification/nfr4c2.json`(audit a18c6b2, 병합본 ebd7b3c: suite 10089 passed/0 failed, A-4 36/36) |
| D-ND3 | NFR-4 검증 기준(③): 같은 환경·같은 코드 비트 동일, 다른 환경·수치 보존 리팩터링 필드별(D·C·K), 분해능 출처 표, test 기반 비교기(`E/tests/integration/nfr4_compare.py`)·실행 하네스(`nfr4_run_dump.py`)와 감사 사용, L-b 정지 사유 기록 | 40 §2.4.13 (2)~(5) | OK | `E/tests/integration/nfr4_compare.py`·`nfr4_run_dump.py`, L-b 정지 사유 `E/search/l_bin_search.py:35-40`·`eps_sweep.py:116-135`·notes `l_search` -- 판정 기록 `.ai/verification/nfr4c2.json`(audit a18c6b2, 병합본 ebd7b3c: suite 10089 passed/0 failed, A-4 36/36). 매크로 해 주입 진입은 후속 NFR4-F2 |
| D-ND4 | 알려진 잔여 결함: pushpull_follower_buffer의 다른 실행 환경 비교 이산 갈림(외층 ε 풀이 `EP:s1` FD 열 실패 `frozen:L:M1`·재시작 2 대 6, 시작점 경계 밖 성분의 풀이기 잡음). 3안으로 없어지지 않는다. 처리 = Q-N7 확정(사용자 결정 2026-10-15 "기본안대로 진행해"): 알려진 결함으로 남기고 원인은 후속 card NFR4-F1(40 §2.4.13 (8)) | 40 §2.4.13 (5)(b)·(8), 41 §5.13 '남은 위험' | DEV | 대리 측정(고정 전 스레드 1 대 8·18, 41 §5.13 (a2)): 엔진 결정 차이 125/125, `wt/_nfr4_design_scratch/all_variant_a2.json` -- 34932a9 복제 |
| D-ND5 | **대상 소멸**(사용자 결정 2026-10-15 "나로 해" -- S3 실행 사이 읽기 없음). 옛 항목: S3 실행 간 재사용의 실행 환경 지문(Q-N5, 사용자 결정 2026-10-15 "기본안대로 진행해"): `S3Archive(..., *, env_fp)`, 줄마다 `env_fp`, `load_evals`·`load_runs`가 `code_fp`·`env_fp` 둘 다 같은 줄만, 불일치 = miss, 빈 `env_fp` = `ValueError` | 40 §2.4.13 (8) Q-N5(대상 소멸) | N/A | `rg "env_fp" E/search/archive.py` 0 -- 34932a9. `E/search/archive.py:42`는 `(root, context_fp, code_fp)`만 받는다 |
| D-TB1a | (card TB-1 범위 1 -- 단독 병합, O-187·O-190) S/B/F 분류 S0 필드 `device: theta_class` = `ThetaClass(kind ∈ {"S","B","F"})`(v1.16.0 -- X 칸 삭제, O-187), writer = `theta_class` 블록 하나(`E/sizing/theta_class.py`, **쓰기 계획 앞**), 입력 = S1v `Block.roles`·spec 선언 사실·L 동치류(`device.dc_coord` 읽지 않음, topology 태그 READS 0) -- '바이어스 구동 레일 source 셀' 속성 없음(O-157 S4 J2; 대상 판정은 card SB-1) | 40 §2.4.8, 41 §5.3.3·§5.12.6 E11 | MISS | `rg "theta_class"` 0. 확인(계획 TB-1 완료 조건 (1)(3)): writer 하나·READS 단언, 분류 toy(선언·연결만 읽음, 태그 READS 0 -- 속성 대조는 SB-1 대상 판정 toy). 첫 소비자 = 같은 card의 쓰기 계획 종속 멤버 선택(D-TB1d)이라 TB-1 단독 병합(계획 표 #5; 옛 '병합 때 엔진 소비자 0(O-146 K2)·HC-1·LA-1과 같은 통합 병합(O-149)' 대체) |
| D-TB1b | (card **HC-1** -- R-1′ 묶음, 사용자 결정 O-190; 옛 'card TB-1 범위 2') R-1′ 제약 그래프 S0 필드·넷별 뿌리 경로 필드·Gs⁺ VGS 변 필드(이름·형식 = headroom-chain HC-D design -- **미작성**), F_exist·J_point·방향 규칙 P(서명 = HC-D design 한 자리), writer = R-1′ 블록 하나, 같은 변경에서 `gvgs_summary.vds_saturation` 삭제·소비자 재배선, `current_symmetry` 결과 필드 HC-1 한 길; HC-1 + GC-8 통합 병합(O-191) | 40 §2.4.8, 41 §6.7-1·-3·§6.7-11 | MISS | 착수 조건 = headroom-chain HC-1 행(GC-D design 승인·GC-1 선행 -- O-191). 옛 'TB-1 착수 조건 HC-D design 승인'은 O-192로 삭제. 확인 = headroom-chain HC-1 완료 조건(R-1′ 정의 toy·`vds_saturation` 삭제 비교(base 집합 ⊆ 새 길이 1 집합)·순수 리팩터링 필드별 비교) |
| D-TB1d | (card TB-1 -- 쓰기 계획 종속 멤버 선택 배선, v1.16.0 신설 -- 사용자 결정 O-187·O-189) `kvl_branch` 고리: B 멤버 있으면 B 종속(diode → 대칭 궤도 대표 → 소스 사슬 하류 → DEC-97 정준 위치), 없으면 ① diode 독립 → ② 뒤 stage 독립 → 정준 위치; 고리 밖 비트리 관계 이름 키 → 정준 위치; ratify 대조 = `structure.json` concept `dependent_member`(고리 = confirm·다르면 정지, 고리 밖 = override); 옛 OrderHints·이름 키 삭제; R6 값 대상 = writer 역할 B만(종속 B ln IDu = 커널 고리 등식) | 40 §3.7-4·§3.2-3, 41 §5.3.3·§6.7-11 | MISS | as-built `E/sizing/writer_plan.py`(① 구조 색·이름·`order_hints`). 확인 = 계획 TB-1 완료 조건(이름 전단사 metamorphic -- 고리 안팎, 고리 밖 base red toy 확보는 test 주체·TB-1 design 몫 -- 계획 검증 33 D-4); 착수 실측 M-KV1c(r2r 고리 포함 여부) |
| D-TB1c | (card LA-1 범위 15 (d) -- U-132 승인 O-166, 옛 TB-1 범위 3) R7 가드 필드 `device: start.guard` = 소자별 `GuardRow(g_lo, g_hi, ln_idu_set, sources)`(v1.16.0 -- ln IDu 축 위 순방향 제약 행, 계획 DEC-104 (3)(b), O-186; 옛 `GuardInterval(gm_id_lo, gm_id_hi, sources)`) + 합 행(DEC-105 (5)), writer = 출발 단계 블록 `start_intervals`(41 §6.4-2a·§7.5 가드 계산을 옮기며 DEC-105 (5) 규칙으로 고침), R6 READS 같은 card; 확인 = LA-1 완료 조건 10 (d)(합 행 toy·변화표) | 40 §2.4.8, 41 §6.7-11·§5.12.6 E12 | MISS | `rg "start\.guard\|GuardInterval"` 0 |
| D-R6 | (card LA-1) DEC-104 R6 블록 `loop_dependents`(`iv_kvl_choice.kvl_choice` 확장 `@compute_block`, 출발·층 0 공용, R5′ (1)~(4)) -- 출력 = R6 블록 출력 필드 하나(B ln IDu·종속 W4·V_R·재개방 표지 -- DEC-104 (3)(c), O-151 DK1), `start.row`·`rungs`는 θ 독립 성분만 | 41 §6.7-11 | MISS | `rg "loop_dependents"` 0. 확인 = LA-1 완료 조건 1 (ix)·9 (c)(d) |
| D-R5p | (card LA-1 범위 1·2·6) VDS·V_R 배분 (c-1)~(c-4)(R-1′ 구간·무변화/재개방·정확 풀이 판정 = HC-1 거르기와 같은 함수 호출; (c-4) 삭제 -- W4·V_R = R5′ (2) 행 여유 max-min), V_R 수렴 지표, 조립 = 확인, 수리 좌표 = θ 독립 성분만, `resistor_out_of_box`, `chain_violation`, 저항 상자 = spec `search.theta_bounds` | 41 §5.3.3·§5.3.4·§5.3.6·§5.5 | MISS | 계획 LA-1 완료 조건 1 toy (vii)~(x). as-built `E/search/layer0_center.py` 최소형 |
| D-R10 | (card SB-1) DEC-104 R8·R10 공급 요구 하한(대상 = 출력 노드 공급 셀이 모두 바이어스 구동 레일 source 셀 -- S1v β ∧ source 레일 넷 READS, 가정 붙은 필요조건; 정상상태 항(범위 선언 시)·동적 항 C_lower·SR(창 = spec step 20-80 %, step 없으면 레일 전 범위); 셀 전류 = 봉인 스냅샷 DE-1 R9 READS / 그 밖 블록 안 동작점 포락 하한; 자리 = 출발 구간 블록 + 층 0 블록 전류 하한; 그 밖 하한·출발 목표 없음; R4 정의역 자르기) | 41 §6.8-1, §5.3.1 | MISS | 확인 = SB-1 완료 조건 (1)~(4)(거짓 거부 0) |
| D-L0rpt | (card LA-1 범위 9) 보고 분류 `graph/layer0: report_class`(`layer0_inactive`·`assembly_failed_path`·`performance_judgement_deferred`), writer `layer0_budget`, 출력 전용 -- 결과 JSON `layer0.report_class`·notes | 41 §5.1, 40 §2.4.8 | MISS | 계획 LA-1 완료 조건 7 보고 분류 toy(base는 분류 없이 front 0점 -- red) |
| D-L0filt | (LA-1 범위 11 → HC-1) R-1′ 관계식 거르기 세 자리(국소 봉인 후보·조립점·수리점) -- 함수 = HC-1의 J_point, 세 자리 배선 = LA-1(순서 HC-1 → LA-1, 계획 표 #16 -- O-190; 옛 '나중 병합 card'), 거른 수·아낀 커널 호출 수 보고 | 41 §5.3.9·§5.5 | MISS | -- |
| D-L0B85 | (LA-1 범위 13, B85) 매크로 목표 gm의 θ 전류 전파(`dc_current_basis` 행으로 되돌림) -- 미지 θ 전류 둘 이상 행 = R3 '전원 전류 최소' 변수(O-151 U5·U6), 극점 미포함이면 하한 행 최대 + 기록 | 41 §6.5 '전류' | MISS | 계획 완료 조건 9 (a)·1 (i) toy |
| D-SI-cur | (card LA-1 범위 13) 남는 θ 전류 출발값 = R3 -- '전원 전류 최소' 변수(극점이 매크로 망 안일 때) 또는 하한 행 최대 + '극점 미포함' 기록; 상자 기하 중심·기하 평균 자리값 삭제(as-built `start_intervals.py:120-128` = 재작성 범위) | 41 §6.5 | MISS | LA-1 완료 조건 9 toy |
| D-SF1a | (card SF-1 범위 1·6) oracle 전용 `.tran` 항목: 이름표 `E/core/oracle_only.py` `ORACLE_ONLY_METRICS`(`slew_rate_v_per_s`·`slew_rise_v_per_s`·`slew_fall_v_per_s`·`settle_s`·`settle_static_error_pct`), 항목 형식 `{metric, op, value, direction?, tran?{config, epsilon_pct?}, source}` + 회로당 `.tran` step 한 자리(SR·정착 공용 -- O-157 S1), `SizingSpecDoc.oracle_tran`(`TranDecl`)·`tran_fp`, `judged_constraints` 밖, 단일 키·방향 키 동시 선언 거부 | 40 §3.1-1 | MISS | as-built: registry 밖 metric `metric_unknown`, `.tran` 영역 없음(`library_sr_from_sources.md` §4). 완료 조건 (1) toy |
| D-SF1b | (card SF-1 범위 2·4·6 (c)) 삭제 키 거부: `human.driving_spec`·`load_peak_amp`·`load_dc_amp`·`compensation_targets.settling`(`linear_s`·`settling_order`), 전류원 부하 표지 AP-1까지 거부 | 40 §3.1·§3.1-1 | MISS | 완료 조건 (1) red(base는 받아들임) |
| D-SF1c | (card SF-1 범위 3) 출력 절대 범위 `human.output_range_v`(필수 키 -- 범위 또는 `undeclared` 표지 + source, 누락 거부; 차동 = Vod + CM, 노드 범위는 S0 spec 블록 유도; 판정 꼴 칸 이득 저하·기준점), `undeclared` = 요구 행 없음·범위 끝 양 정의 불능 표시 -- 행동 소비자 = DE-1 (d)·SB-1·LA-1 R6, 병합 = 첫 소비자 LA-1과 같은 통합 병합(교체 커밋 -- 계획 표 #3, O-183; 옛 'DE-1·SB-1 가운데 먼저') | 40 §3.1-1 | MISS | -- |
| D-SF1d | (card SF-1 범위 5·7) library spec data(nmcnr SR 0.36/0.31 V/µs·`settle_s` 3.03/3.04 µs·ε 0.1 %·step 0.4 → 0.9 V, ngcc SR 상승 6.3 V/µs·`settle_s` 120 ns·ε 1 %·step 0.14 → 0.54 V, current_reuse `settle_s`·static error·`gain_ss_db ≥ 54` 삭제·`linear_s` 삭제, 6회로 SR 미선언; 출력 범위 = current_reuse Vod [−1.2, 1.2] V + CM 0.9 V + 3 dB 판정 꼴, 나머지 8회로 `undeclared`; `swing_out_v` 제약 3개 삭제(교체 커밋 -- 첫 소비자 통합 병합), nmcnr `icmr_v ≥ 0.5` 유지), heldout erfc·rfc 형식 이관(근거 사용 아님), oracle 스키마 이름 맞춤 | 40 §3.1-1 | MISS | 완료 조건 (2) data·source 칸 대조 |
| D-TRK | 슬루 추종 판정(기준 = 이상 폐루프 목표 step × 1/β, (가)~(다) 20 %·\|Δx\| 띠·0.8·Δx 통과·끝 시각 t_step + \|Δx\|/SR_req -- O-157 S3) + 과도 측정 유효성 조건(계단 ⊆ follower 사용 범위 -- O-157 S1 (3)), 이탈 = SR 정의 불능 → front 제외·기록 | 40 §4-9 | MISS | 구현 = oracle OP-10 |
| D-SET | 정착 측정 `settle_s`(ε 띠, 실제 최종값 = 같은 구성 DC 해)·`settle_static_error_pct`, `tran.config = "application"`은 AP-1까지 판정 대기, measure 이름·구현 = oracle card | 40 §4-10·§3.8-6 | MISS | -- |
| D-STL | (card LA-1) 정착 선언 대역폭 출발 목표 '추정'(필요조건 아님 -- O-157 S3; GBW_est = ω_c,est/(2π·β)) 필드 -- **이름·층·β 읽는 점 미정**(U-118 -- LA-1 design 실측 뒤), S 분류는 선언 사실만 | 41 §6.8-2 | MISS(미정) | -- |
| D-CMP1 | (card CMP-1) 평가 절차: library 회로 전부, (A) 예산 = (C)가 oracle로 판정한 설계점 수(O-157 S8), 독립 agent·감사 판정, 기록 `docs/03-analysis/cmp1/CMP-1.eval.json`·`CMP-1.md`, 게이트 아님 | 40 §10.6 | MISS | 선행 = LA-1 병합 |
| D-LA1rep | (v1.15.0에서 발견한 기존 design 공백) 계획 LA-1 범위 6 수리 단계 전체(수리점 규칙 (A)~(C), `_repairable` 범위, `layer0_repair_dropped_dominates`)가 41에 설계되지 않음 -- v1.15.0은 v6.38에서 바뀐 부분(수리 좌표·R-1′ 거르기)만 적음 | 41 §5.5 '수리' | MISS(design 공백) | LA-1 착수 조건 (1) 'design 41 §5 개정' 몫 |
| D-WB1 | (card WB-1 범위 3; v1.15.2 정정) DC 블록 `dc_solve`(노드 풀이 + W·`dc_op` + `dc_finger` 쓰기, writer 하나), 쓰기 소자 무반복, 종속 소자 노드 재풀이 = Rʳ ≠ ∅일 때만(블록 안 local)·순환 = `slice_cycle` fail-closed, 손가락 선택 = 슬라이스 고정 열거(W_min ≤ w_s ≤ w_hi, 잔차 최소·동률 큰 w_s -- 계획 O-173 Q-P8 (A)) + Rʳ ≠ ∅만 키 벡터 재방문 + W′·바이어스 고정 KCL 재풀이·재봉인(재풀이 점 W 값은 멈춘 자리 -- 40 §3.7-A 2-5), 되먹임 읽기 = SCC 수렴 허용오차 소자(정의)뿐(입력 창 되풀이·시도 상한은 범위 3a 삭제), `dc_finger` 레이아웃 뒤 빈 열, 실현 기하 = 참조 `RealizedGeometry(layout_ref, w_request)`, 슬라이스별 tol 표 = LUT 적재 때, 평가 = θ 순수 함수(평가 캐시 키에 슬라이스 성분 없음), `dc_scc_log.slice_rounds` 출력 전용, W4 목표 READS(LA-1 배선) | 40 §3.7-A 1·2·4 | MISS | as-built 노드 풀이·W 두 블록(integ/it12 `d759838a` `E/sizing/kernel_run.py:84`), kind당 슬라이스(`E/sizing/pre_layout_widths.py:14-22`) |
| D-WB2 | (card WB-1 범위 0·1·2·2a) 선택 함수 `lut.finger_slice`·`slice_of_finger`·`reachable_slices`(손가락 규칙 = 슬라이스 고정 -- 후보 W_min ≤ w_s ≤ w_hi, 잔차 최소·동률 큰 w_s, 후보 0 = `slice_missing` 실현 불능; 계획 v6.38.4 P8), bin 소속 = 격자 정수 비교 + bin 경계 선언 방향(결함 D1), 필드 `device: dc_finger` = `FingerGeom(m, w_f_m)`(소비자 EO-1 넷리스트·범위 2b·DE-1 판정 W), 읽는 열(DC = 소자 키, 용량·잡음·mismatch = 기준 폭 표 키), W 없는 단계 포락 | 40 §3.7-A 3·5·8, 41 §4.2·§5.3.6-1 | MISS | as-built 1 ulp 경계 비교 `E/lut/_helpers_bins.py:6-14`, 판정 도구 관례 `round(W/5 µm)` `wt/_cmp_pilot/judge/eng2spice.py:3` |
| D-WB3 | (card WB-1 범위 2b·3) kind 키 운반 삭제와 소비자 전환: `LutAccess.w_keys`·`pre_layout_lut_access`·`w_key_of(lut, kind)`·`kernel_keys`·`place_layout` kind 키 좁히기·`key_exclusion`(그룹 단위 재작성)·`dc_drop_current` 필드 삭제, 소비자 = 소자 키 / 기준 폭 표 키 / 포락으로 가름, 손가락 옛 생산자 셋(`device_sigma`·`iv_matching_l`·`ss_linearize:68`) 삭제, memo B_r 재측정, 슬라이스별 tol 표 | 40 §3.7-A 6·7·10, §3.10.1 v1.15.1 | DEV | as-built kind 키 운반 26파일(`git grep "w_keys\|w_key_of"`, `d759838a`), D-P2 |
| D-GL | (card LA-1 범위 15 (a)) 이득 L 하한 목표 = found_db 비례 필드 `graph/ach: gain_target_first`(writer `gain_target_first`, 소비자 = 출발 이득 L 하한·층 0 첫 회차), 'A_max 미상 → 비활성' 삭제, 평가 앵커 0 = 정의 불능(margin null, `gain_l_element_undetermined`+원소 키), 미달 = `StartConflict(gain_l)`·최선 앵커, found_db 없는 블록이 든 뷰 = `found_db_missing`(U-133 (A) 승인 O-170, 계획과 같음; 옛 Q-GL1 삭제) | 41 §6.4-1·§6.5 A_i 순서·§5.3.2 | DEV | as-built A_max 인증 조건 `E/search/iv_context.py:49-51`, 가장 긴 앵커 닫힘 `E/search/iv_gain_l.py:125-127` |
| D-MP0 | (card LA-1 범위 15 (b); E-31) 매크로 출발점 P = 0, 출발 gm 2배 사다리(끝 = gm 범위 상한), 끝 칸까지 P ≠ 0 = 정의된 값 출발 + `StartConflict(macro_target, rhp_open_loop)`(옛 `macro_rhp_start` 버림 대체), 망 N9 노드 | 41 §6.5-3a | MISS | as-built `E/search/macro_poles.py:316-328` 다중 출발(P 검사 없음) |
| D-MV | (card LA-1 범위 15 (c)) 체계 오프셋 술어 인스턴스 S0 필드(P1s·P1c, 신호 경로 = R10 넷 술어의 부정 -- 술어 = `bias_fixed_net` 부정, 제작 = card IT-1 v6.38.3 범위 재작성 5, LA-1·SB-1이 부름 -- v1.15.2 정정)와 `mirror_vds` 목표 행(K-1 (i), R-1′ 위반 다음, B 밀도만, `StartConflict(mirror_vds)`) | 41 §6.7-4·§6.7-11 | MISS | -- |
| D-AR | (card LA-1 범위 1·15 (e)) 면적 조건 → 입력 소자 ln IDu 상한 순방향 제약 행(IDu ≤ I·L²/A_min(L, ln IDu) -- v1.16.0, 계획 DEC-105 (6)·O-186; 옛 'gm/ID 하한, 최소 g'), matching L 하한 삭제(LR6 개정) | 41 §6.4-2·-6, §5.3.7 멈춤 | DEV | as-built matching L 하한 `E/search/iv_matching_l.py` |
| D-CMB | (v1.15.1 D-CM → v1.15.2 ID 변경(옛 D-CM 행(§3)과 중복 해소), card LA-1 범위 15 (f); DEC-105 (7) v6.38.3·N6.35 E-11, 판별 밖 = `cm_reference_unclassified`) CM 되먹임 DC 평형 등식(오차 쌍 전류 같음 → `dc_current_basis`, 출력 CM = 기준 넷 DC → 쓰기 계획 고정 노드), CM 기준 = 내부 생성이면 KVL writer·외부면 선언 필수(`cm_reference_undeclared`)·선언 자리 하나(`cm_reference_double_declared`), 생략 예외 `cm_reference_undetermined` 삭제, 단일 출력 무동작 | 40 §5-6 | MISS | -- |
| D-RS1 | (card RS-1) 열별 Δp = \|∂ln p/∂VGS\|·tol_V·\|p\|(공통 ε_d 삭제), 최악 선형 유지, metrics CONTRACT 9.1 개정(기준 변경) | 40 §3.8-9 | DEV | as-built ε_d 공통 `E/metrics/ss_linearize.py` `lut_rel_tol`, `E/metrics/lut_parameters.py` |
| D-CR | (card SF-1 범위 8) `human.counted_rails` 선언·로더 거부 셋·`supply_current_dc` + 미선언 = 보류 정지, 전력 축·oracle 레일 집합 같은 선언 | 40 §3.1-1 | PART | as-built 엔진 extras `counted_rails`(`E/metrics/dc_metrics.py:4·:95`) 있음, spec 로더 키·보류 정지 없음 |
| D-TBX | (card SF-1 범위 9; DEC-105 (10) v6.38.3) θ 상자 출처 규칙 (a) 커패시터 공통 선언 `assets/theta_box_common.json`(값 = 2026-10-08 '10번') (b) 영점 상쇄 저항 = θ·상자 [1/max Σgm, 1/min Σgm](`zero_cancel_box`, U-134 (가)) (c) DC 경로 저항 = 회로별 선언 (d) 출처 없음 거부; 회로별 커패시터 사본 9개 삭제, 실행 설정 재정의 삭제 | 40 §3.1-1 | MISS | as-built 회로별 `human.search.theta_bounds` 사본(library 커패시터 9항목 -- v1.15.2 정정) |
| D-IN1 | (card IT-1 범위 재작성 1~4 -- DEC-106) 입력 DC 미선언 차동 입력쌍 = G_vgs 한 점(입력 점), y 키 `(y, <role p 포트 넷>)` 하나·relation `input_point`, F 닿으면 KVL 종속, 그 밖 다중 입력 = `input_cm_undefined` 정지, `input_port_multiple_roots`·`BRANCH_INPUT_MULTIPLE_ROOTS` 삭제 | 40 §3.11-4, 41 §4.7-V·§6.7-1a | MISS | as-built 포트별 뿌리·`input_tie`(integ/it12 `E/sizing/writer_plan.py`) |
| D-E13 | (card WB-1 범위 3a-0·3a -- N6.35 E-13) θ y 범위 = KVL 순서 창 하나(`node.dc_window` 상태 칸 없음), 입력 창 = `dc_window_cfg` 한 자리, 결과 JSON `perf.solver_stops`(출력 전용) | 40 §3.11-1·3.11-3, 41 §4.7-V | MISS | as-built `E/sizing/block_columns.py:736-780`(되풀이·`_interior_solution`·`unmeasured`/`unsettled`) |
| D-START | (card LA-1 범위 15 (g)·graph-consumption GC-5 -- N6.35 머리·E-31·E-32·E-17·E-08) 출발 정의 불능 세 층(`macro_rung_undefined`·`macro_start_unavailable`·`start_unavailable`), 목표 미달 = 정의된 출발값 + `StartConflict(macro_target)`, 칸 0 한 규칙, 상자 중심 출발·`use_macro` 해제 경로 없음, 층 0 점 없음 경로 출발점 = 칸 0 조립 한 규칙(`_box_centre`·`_current_centre`·`centre_start`·`_halton_probe`·`_maxmin`·`layer0_start` 삭제, `_repair` 수리 단계로 -- 계획 v6.38.4 P4), θ점 DC 전류 0 저항 출발값 = P4-R | 40 §3.11-2·§3.6, 41 §6.5-3a·4·§5.9 | MISS | as-built `macro_root_missing` 한 코드(`E/search/macro_poles.py:135·148·363·369`), `_box_centre`(`E/search/layer0_center.py:654-656`) |
| D-GS | (card IT-1 범위 재작성 5 -- N6.35 E-19) g = s 한 규칙: `graph.gvgs_summary.off_vgs0` 분류(S1), 신호 경로 꺼짐 소자 = `off_device_on_signal_path` 정지(S1v GB2 출구), 술어 `bias_fixed_net`(S1v 순수 함수 -- LA-1 (c)·SB-1이 부름) | 40 §3.11-5 | MISS | as-built 비레일 `gvgs_self_edge` 정지·레일 `fixed_vgs` 비대칭(`E/graph/gvgs_cycles.py`) |
| D-JDG | (card SF-1 범위 8 -- N6.35 E-02·E-03) 판정 대상 두 축(출처·metric) = S0 칸 `constraint_classes.judged_targets`(writer 제약 분류 블록, 소비자 READS, S-10 거부 = 그 블록 안 -- 계획 v6.38.4 P1), 옛 칸 `judged` → `objective_axis`, 결과 상태 `unjudged`, `ConstraintDecl.judged` 삭제, CPG-1 셈 규칙 | 40 §3.1-1·§10.7 | MISS | as-built `E/authoring/spec_constraints.py:264-268`·`spec_refs.py:86-90` |
| D-SPX | (card SF-1 범위 11 -- N6.35 E-04) spec 칸 삭제: `search_method`·`optional_stages`·`spice_check`(규칙 칸 여섯)·`front_refilter`(규칙 칸 셋), 선언 = 모르는 키 거부 | 40 §3.1-1·§3.10.8 | MISS | as-built `E/authoring/spec_settings.py:35-39·104-106` |
| D-GATE | (card UB-1 범위 4 -- N6.35 E-01·E-16) 감도 게이트 verdict `undeterminable`·`gate_empty` 기록, bin 안 극값 세분 전 상한 = 미상 | 40 §3.8-2·§3.11-6, 41 §4.2 | MISS | as-built `E/metrics/sensitivity_gate.py:16·30-33`, `E/metrics/block_gain_model.py:20-23` |
| D-CML | (card GV-1 범위 4 -- N6.35 E-33) CM 루프 안정도 제약 미선언 = `undeclared_loop_constraint` 정지, `cm_loop_unconstrained` 경로 삭제 | 40 §5-3, 41 §1.8 | MISS | as-built `E/graph/s1v_fields.py:92`, `E/metrics/ss_metrics.py:76·273` |
| D-LOWN | (card GV-1 범위 3 -- N6.35 E-10) L 주인 = S1v 전달 뷰에서, 뷰가 둘 이상·출발점 다름·전달 뷰 없음 = `l_owner_view_ambiguous` 정의 불능, 첫 뷰 대체 삭제 | 40 §3.11-7 | MISS | as-built `l_classes._main_path_starts` 첫 뷰 |
| D-MRD | (card SF-1 범위 10 -- ID: 기존 D-MR(`mirror_ratio_sigma_pct`)과 중복 해소) 선언 미러 비 `human.mirror_ratios`만 `dc_current_basis` 강제 행, 정지 `mirror_ratio_not_mirror`·`mirror_ratio_symmetry_conflict`, ρ θ 종류 없음 | 40 §3.1-1·§3.7-2 | MISS | as-built `E/sizing/current_basis.py:12`('강제하지 않는다') |
| D-PW | (card SF-1 범위 8 정의 항목 -- O-172 A18) DUT 전력 `power_dc_w` = Σ 셈 레일 V·I, V_0 = 넷리스트 0 V, 측정 부하 가감 없음(계획 DEC-78 v6.38.4 P7, 승인 O-173 C5 -- 40 §3.1-1; oracle OP-11 = 레일 전압원 전류 − 측정 부하 원소 전류) | 40 §3.1-1 | MISS | as-built `E/metrics/supply.py`(레일 전체 전류) |
| D-RMIN | (card SF-1 범위 9 -- 계획 v6.38.4 D18·D19) 저항 소신호 = 이상 R + 양 끝 C_par/2(l = R/r_l, 소신호 MNA만, 필드 `device: passive_parasitic`), 실현 범위 R ≥ R_min(종류) = 종류 선택 후보 조건(실현 종류 0이면 `resistor_kind_unrealizable`), 선언 칸 `r_min_ohm` | 40 §3.1-1 | MISS | as-built 종류 선택 `E/core/pdk_decl.py`(Ω당 면적 최소, R_min 없음) |
| D-U12 | (40 §3.5 상태표에서 옮김) 단일단 gm_1 규칙(U-12, 계획상 확정 대기) | 40 §3.5 | MISS | -- |
| D-PMCM | (40 §4 상태표에서 옮김) `pm_cm_ss_deg` oracle 측정 -- `[ng-cmfb-pm]`에 있고 `[ng-bridge]` `ORACLE_MEASURES`에는 없음 | 40 §4 | PART | `[ng-cmfb-pm]` |
| D-FCOP | (40 §3.4 상태표에서 옮김) LUT 곡선 FC 위반 칸에서 `op_point`가 사유 기록 없이 선형으로 넘어감(분류는 있고 해법 매핑 없음) | 40 §3.4 | PART | `E/lut/lut_set.py`, `E/lut/curve_check.py` |
| D-AREA | (card SF-1 범위 9 -- N6.35 E-12) 값 미정 수동소자가 있으면 면적 정의 불능 `area_undefined`, head 면적 미선언 0.0 대체 삭제 | 40 §3.11-8 | MISS | as-built `E/metrics/dc_metrics.py:115-118`, `E/layout/passives.py:21` |
| D-LA1G | (card LA-1 범위 15 (g) -- N6.35 E-07·E-14·E-15·E-24·E-25·E-26·E-34·E-35) `kcl_row_underdetermined`·`tol_vdsat_table_missing`·`zc_start_undefined` 기록, 0 자리값(`E_refilter`·`reserve_evals`·N_T) 삭제, U-51 폴백 문언 삭제, `constraint_rows` `undefined` 반환 삭제 | 40 §3.11-6·§3.6, 41 §6.5 | MISS | 행별 as-built 자리 = 계획 N6.35 |
| D-CAB | (계획 DEC-92 (3) '한계' design 판정) S = 연결 정의(규칙 변경 0, 출발값 R_S = 1/Σgm), 'AC 구동 소자 포함' 안 기각(근거 = evidence 실측), A–G 결합 용량 경로 = S 미정 fail-closed 초안(P2) | 40 §3.5 | N/A(규칙 변경 없음 -- 판정 기록) | 실측 `wt/_drafts/evidence/2026-10-29/design_v1152/class_ab_s/` |
| D-CPG | (card CPG-1) C′ 경로 완료 판정 bench(10항목, 선언 모드·EO-1 기하, 엔진 `dc_finger` 그대로, 기준선 재측정) | 40 §10.7 | MISS | 선행 = DEC-105 card 전부 병합 |
| D-TH1 | (v1.16.0 -- 사용자 결정 O-186 (A), card LA-1·LI-1·WB-1) θ 독립 좌표·역산 키 = ln IDu: gm/ID 역산(`vgs_for_gm_id`·'가장 큰 VGS 해'·gm/ID 축 곡선) 소비 0, gm/ID = `device.dc_op` 순방향 조회 칸(writer 하나), S 소자 ID = max(gm_req/g(ln IDu), R8), gm/ID 경계 = 순방향 제약 행(해 집합 = ln IDu 구간 여럿), 출발 구간·사다리·가드·tol_V 지표 = ln IDu 축 | 41 §4.1·§4.2·§4.5·§5.3·§6·§7.5, 40 §1·§3.10 | MISS | as-built gm/ID 역산 소비자 전수 = 계획 착수 실측 M-TH1c(LA-1·LI-1·WB-1 첫 design 착수 전), 해 집합 여럿 여부 = M-TH1a. 확인 toy = 41 §9 면적 조건 행(pfet 중간 반전 두 구간) |
| D-L2 | (v1.16.0 -- 사용자 결정 O-186 (L2), card LI-1·MOD7) 레이아웃 보존량 = (ID, VGS, L), 실현 W = ID/J_slice(VGS) 순방향, 슬라이스 간 gm 이동은 DEC-89 (2) 레이아웃 뒤 재평가 | 40 §2.4.8 `ly_point`·`ly_slices`·`ly_attrs` 행, §3.10.2 | MISS | as-built `ConservedPoint.gm_id` 칸·`slice_density` gm/ID 역산. 착수 조건 = M-TH1L+·M-TH1g(MOD7·MOD8 design 전) |
| D-NM1 | (v1.16.0 -- 사용자 결정 O-189) 이름 tie-break 여덟 자리의 마지막 키 = DEC-97 정준 위치: DEC-70·DEC-97 (2) 열 키(40 §6-3), DEC-71 (6) front 타이(41 §5.4), N3 루프 뷰 사이클 시작점(41 §1.8), DEC-17 L 주인(41 §1.12.5 `l_owner_position_order`), DEC-95 (3) 고리 밖(40 §3.7-4 (b)), 일곱째 R-1′ 변 순서(HC-D design), 여덟째 W4 뿌리(41 §4.7 -- 정의상 공허) | 40 §3.7-4·§6-3, 41 §1.8·§1.12.5·§4.7·§5.4 | MISS | as-built 이름 키(`writer_plan.py`·`current_basis.py:8`·`l_classes.py`·`block_columns.py:189`). 착수 실측 M-NM1 남은 실측(DEC-17·루프 물리 키 -- 6a design 착수 조건) |
| D-CL1 | (v1.16.0 -- 계획 DEC-72 (3)·card CL-1, 사용자 결정 O-178·O-182 Q-CL1) oracle 닫기: 정의 동일성 관문 → 활성 제약 oracle 여유 [0, 분해능] 밖이면 (점, metric)별 Δ secant(metric별 독립 동시 갱신), 멈춤 = oracle 진전 ≤ 분해능 / E-0 실현 불가 / 선언 반복 상한; 대조 기록 = oracle 판정 기록 칸(record_id 참조), 엔진 `model_error` 필드·`model_error_ref`·ME-1 삭제 | 40 §3.6·§3.8-6·§10 검증 기준, 41 §4.7-2 | MISS | as-built `E/metrics/model_error.py`·`ss_constraints.py` e_m 분모(재작성 범위). 완료 조건 = 계획 CL-1(library 13 닫기 반복·oracle 실행 수·t_oracle·σ_in 닫기 비용 실측) |
| D-GL1 | (v1.16.0 -- card GL-1, 사용자 결정 O-182 Q-GL1 (가1)·O-183 #10) G 확장 lint·설계 값 타입 위치 검사·공유 호출 감사 도구, GL-1 병합 전 엔진 card 병합 금지, 기존 위반 기준선 래칫 | 40 §2.4.10 | MISS | `tests/structure/structure_checks.py` G-8·값 타입 위치 검사 0건(계획 N6.37 사실) |
| D-V9 | (계획 V9 -- matching 멤버 (W/L, ln IDu) 일치, O-186) 짝 비교의 두 멤버 ln IDu 허용오차 합침 규칙·동작점이 VGS 노드 위일 때 쓰는 칸·옛 기준(gm/ID 격자 간격)과의 비교 방법(약화 금지 근거) | -- | MISS(design 공백) | 계획이 'design 몫'으로 넘겼으나 40·41·42에 V9(계약 test 6b) 자리가 없다 -- v1.16.0은 정하지 않고 6b 계약 test design 몫으로 표지(계획 검증 30 m29-1·n30-2) |

## 4. 상태 집계

기준은 master이고, 브랜치에만 OK인 항목은 PART로 센다.

| 구분 | 행 수 | OK | DEV | PART | MISS | N/A |
|---|---|---|---|---|---|---|
| FR·NFR | 15 | 2 | 1 | 7 | 5 | 0 |
| DEC | 85 | 23 | 7 | 29 | 20 | 6 |
| 설계 항목 | 223 | 6 | 30 | 18 | 164 | 5 |
| **합계** | 323 | 31 | 38 | 54 | 189 | 11 |

v1.16.0(2026-10-31, 계획 v6.38.5 맞춤 -- 사용자 결정 O-193): DEC 행 11 OK → DEV(O-186 규칙 철회 -- DEC OK 23·DEV 7); 설계 항목 7행 추가(D-TB1d·D-TH1·D-L2·D-NM1·D-CL1·D-GL1·D-V9, 모두 MISS), D-GB7c PART → MISS(행 정본 = D-TB1d) -- 설계 항목 223(PART 18·MISS 164)·합계 323(OK 31·DEV 38·PART 54·MISS 189); 나머지는 행 문구 정정(상태 불변). DEC 표 행 수 85: OK 23·DEV 7·PART 29·MISS 20·N/A 6.

v1.15.3(2026-10-29, 계획 v6.38.4 맞춤 -- 사용자 결정 O-173, 검증 대기): 설계 항목 4행 추가(D-RMIN MISS, 검증 2 m-C로 40 상태표에서 옮긴 D-U12 MISS·D-PMCM PART·D-FCOP PART) -- 설계 항목 216(PART 19·MISS 156)·합계 316(PART 55·MISS 181); 나머지는 행 문구 확정(D-WB1·D-WB2·D-START·D-JDG·D-PW, 상태 불변).

판별 이력(v1.15.2 집계 정정 ~ v1.7) = design 이력 H42-02.

**후속 항목**(코드 쪽, 이 문서 개정에서 고치지 않음): `E/graph/CONTRACT.md:226`의 "`same_as`·`budget_ref`(선언 전용)" 문구 중 `budget_ref`를 '만들지 않는다 -- 기둥이 흡수(DEC-55, 사용자 결정 2026-10-12 "다로 해")'로 고친다. 다음 graph 계약 개정 단위에서 처리한다.

판별 이력(v1.6 ~ v1.4) = design 이력 H42-03.

센 방법:
- D-SIa~f는 6행으로 센다.
- DEC 표에서 '37~42', '47·49·51·76·85·86'은 각각 1행이다.
