# 범용 gm/ID 엔진 로드맵 -- 계획서 N3 아키텍처로 새로 짓기 (설계 문서)

- 범위(사용자 확정 2026-10-07): library 9회로 전부 + 6a 구조 유도(역할 태그 없이 connectivity로) + (전력, 면적) 비지배 front + 9회로 ngspice 합격. 완성도 유지, 목표 약 1달(합리적 사유가 있으면 2달까지).
- 전제(사용자 확정 2026-10-07): **새 엔진을 계획서 N3 아키텍처(GB0~GB9 흐름, S0~S3 상태 층, MOD1~MOD10 모듈, DEC 규칙)로 새로 짓는다.** 옛 엔진(`assets/sizing_recipe.py` 12,013줄, `stick_diagram.py` 9,010줄)은 고치지 않고 (a) 검증된 부품의 출처 (b) 대조 기준선으로만 쓴다.
- 진행 절차: `_drafts/p3light/PROCEDURE.md`의 '남기는 것'(코드·test 작성 주체 분리, 깨진 test·약화 보고, 변경당 커밋 1, 매 변경 뒤 전체 pytest)을 새 엔진에도 쓴다. 옛 엔진 이동 증명(AST 해시)과 E-INST·E-LIB '옛 base와 같음' 규칙은 새 엔진에는 해당하지 않고, 대신 2.6절 대조 기록을 쓴다.
- 정본 인용: 계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(커밋 6df4bd7 행 번호, 이하 `P 행`). 정의·규칙은 계획서가 정본이고 이 문서는 범위에 맞춘 순서·축소 지점·완료 조건만 정한다. 축소 지점은 4절 결정 묶음에 기본안과 함께 있다.
- 규모 기호와 중앙 단가(h): mv 1.2 / S 1.7 / M 4.5 / L 11 / XL 22(`schedule_general_engine.md` 1절). 새로 짓는 단위는 정의가 계획서에 있으므로 L 단가를 쓰되, 계획서에 design 문서가 없는 단계는 설계 단위(D)를 따로 센다.
- 레인: **1** DC·사이징·탐색 커널(MOD1·MOD4·MOD6) / **2** 구조(MOD2·MOD3) / **P** 병렬(MOD5 metric 이식, SPICE 오라클, LUT 데이터, 스펙, 설계 문서, test 기반). 새 엔진은 처음부터 모듈이 나뉘어 있어 레인끼리 같은 파일을 고치지 않는다.

---

## 0. 구조와 순서

### 0.1 새 엔진의 위치

| 항목 | 기본안 |
|---|---|
| 패키지 | `skills/analog-gmid-design/gmid_engine/`(새 디렉터리, `__init__.py`). 파일 이름은 N3.10 표(P 515~535) 그대로: `gmid_lut.py`(MOD1), `topology_authoring.py`(MOD2), `circuit_state_graph.py`(MOD3), `gmid_sizing_engine.py`(MOD4), `circuit_metrics.py`(MOD5), `theta_search.py`(MOD6), MOD7은 옛 `stick_diagram.py`를 어댑터로 부름, `sizing_layout_convergence.py`(MOD8, 범위 밖 -- D4), `instance_report_builder.py`(MOD9), `gmid_design_pipeline.py`(MOD10). import는 번호가 작은 쪽으로만(P 517) |
| test | `skills/analog-gmid-design/gmid_engine/tests/`, N3.11 배치(P 537~): `unit/`, `integration/`, `contracts/`, `regression/`, `oracles/`. 옛 `assets/tests/`와 섞지 않는다 |
| SPICE 오라클 | `skills/analog-gmid-design/tools/spice_oracle/`(엔진 import 없음, 결과 JSON + topology.json만 읽음). 엔진 GB9(P 323)는 이 도구를 외부 단계로 부른다 |
| 작업 장소 | clone `gmid-light`에 master에서 새 브랜치(`engine-v2`). `phase3-light`는 멈춘다(D17) |
| 옛 엔진 | 동결. 새 엔진이 9회로 합격하면 옛 엔진·옛 test 퇴역을 별도 결정으로 올린다 |

### 0.2 단계 순서 (계획서 N3.1 흐름과 대조)

제안 순서 `S0/S1 그래프 → GB0~GB2 → GB7 → GB3/GB4 → GB5 → GB6 → GB8 → front → 9회로 SPICE`를 N3.1(P 310~335)과 대조해 아래처럼 고친다.

| 고친 점 | 근거 |
|---|---|
| **GB0 spec 로드가 맨 앞**(S0 지문이 spec 해시를 포함하고, 로드 게이트가 `supply_nets`·출처 없는 제약을 거부해야 S1이 선다) | N3.1 GB0 P 314, S0 P 363 |
| **GB8의 S2 `ss` 소신호와 MNA metric을 GB5·GB6 앞으로**: 평가 커널 순서가 GB7 → 봉인 → GB5 제약 판정 → GB8 metric이고, GB5는 봉인 스냅샷 `ss`(gm·gds·C)를 읽으며 GB6 외층은 GB8의 전력·면적·gain을 목적·제약으로 쓴다 | N3.1 실행 구조 P 325, N3.5 평가 커널 P 410 |
| **GB3(결합 블록 y)는 범위 밖**: y는 정밀 경로(내층 DP·중층 좌표강하)에서만 쓰이고 기본 경로는 층 0 + 외층 SLSQP | GB3 P 317, DEC-73 P 267 |
| **GB4는 축소**: 블록 gain 상한(AC 상한)과 LUT 곡선 검사로 탐색 전 INFEASIBLE_TARGET만. DOF·수치 rank는 범위 밖 | GB4 P 318, N3.14 P 734 |
| **GB6 층 0은 최소형**: 기둥 KVL 조립으로 DC 정합 시작점 하나를 만드는 데까지. 블록별 gain bin front는 U-33 실측 뒤 | DEC-71 P 265, U-33 P 1110 |
| **SPICE는 맨 끝이 아니라 처음부터 오라클로**: GB9의 SPICE 대조(7a)는 각 단계 완료 조건의 판정 장치다 | GB9 P 323, P 499 |

결과 순서: **GB0 + S0/S1 → GB1 → GB2(S1v) → GB7(S2 `dc`, 봉인) → GB8 핵심(S2 `ss`, MNA·전력·면적) → GB4 축소 → GB5 → GB6(층 0 최소 + 외층 ε-제약 front) → GB9 SPICE(오라클은 1주부터) → 9회로**. 평가 커널(MOD6)은 GB7 → 봉인 → GB5 → GB8을 후보마다 중첩 실행한다.

### 0.3 옛 엔진에서 가져올 부품

| 부품 | 옛 위치 | 새 위치 | 방법 | 근거·조건 |
|---|---|---|---|---|
| LUT 인터페이스·다선형 보간·VGS 역산·조회 캐시·조건 메타 | `sizing_recipe.py` 52 `GmIdLUT`, `_multilinear_interp*`, `_solve_vgs`, `lut_conditions_from_npz` | MOD1 | **그대로 복사 + 계약 test**(npz 격자점 직접 조회 오라클, LOO 보간 오차) | 엔진 ID = LUT ID 자기일관성 실측(engine_current_capability 4.3절). 추가: `w_ref_m` 메타, VS 축 밖 조회 거부(DF-27 P 939), gmb(∂ID/∂VSB, P 490) |
| 레일 선언 접근자 `RailDeclaration`·`rail_declaration` | gmid-light `stick_diagram.py` 8535·8541(B26-1) | MOD2 | **그대로 복사 + 그 test 이식**(`test_b26_rail_accessor.py`) | B26-1 판정 1179 passed, 9회로 `nets = supply_nets` 실측 |
| tol_V(LOO 보간 오차) 계산 | `tests/probes/probe_interp_scheme_loo.py` | MOD1 | 복사 후 함수화 + test | P 439 |
| 소신호 MNA(행렬 조립·주파수 응답) | `build_ac_network` 4067, `full_circuit_response_at_omega` 4104, `_full_circuit_response` 4970 | MOD5 | **복사 + 입력을 S2 `ss`로 바꾸는 어댑터 + 오라클**(VCCS 등가회로 ngspice 대조, 옛 `stage3_full_circuit_ngspice_crosscheck.py` 방식) | gmb 스탬프 추가(P 490) |
| metric 식: 공급 전류, ΣW·L, 미스매치 σ, Rz = 1/gm | `_metric_supply_current` 4339, `_metric_sum_area` 2854, `estimate_mismatch_sigma`, `_resolve_nulling_resistor_ohm` | MOD5 | 식만 복사 + 손계산 test. 레일은 선언에서(이름 집합 기본값 금지) | DEC-78 P 272, DEC-79 P 273 |
| L 결정 규칙 식(knee 측정) | `measure_L_knee`, `derive_role_L` | MOD4 | **참고 + 식 단위 복사**(역할 이름 입력을 S1 `dc_role`로) | N3.9 P 501 |
| 구조 판정(diode, 미러 그룹, KCL·매칭 엣지, L 공유류) | `is_diode_connected` 3119, `true_current_mirror_groups` 2191, `_kcl_and_matching_edges`, `l_sharing_classes` | MOD3 | **참고만**(S1 그래프 위에서 다시 씀). 옛 함수 출력은 4회로 shadow 대조 기준 | 옛 구조 질의가 소자 리스트를 각자 순회(sizing 24곳, stick 83곳) -- 통합 그래프 없음 |
| 노드전압 전파·헤드룸 배정 | `propagate_node_voltages` 3727, `_hr_*`, `allocate_stack_headroom` | -- | **쓰지 않음**(대조용 출력만) | 사후 복원 방식이 DC 비정합의 원인(spice_harness_report 4단계 3, nmcnr_diag 3.1) |
| 보상 함수(회로별) | `topology_library.py` | -- | **참고만**. GB5 일반 규칙(DEC-70)의 test 기대값 대조 | DEC-70 P 264 |
| SLSQP 래퍼·multi-start | `_optimize_theta_slsqp` 10792 | MOD6 | 참고만(구조: scipy SLSQP, 시작점 여러 개) | probe_area_pareto 실측(지배당한 국소해 존재) |
| 레이아웃(finger 배정·floorplan·stick) | `stick_diagram.py` R0 함수, `assign_finger_geometry` 6017 | MOD7 | **그대로 import(어댑터로 새 결과 → 옛 sizing dict)**, 수정 없음. 합격 시험 밖, 보고용 | D4 |
| instance.json·HTML 보고 | `save_instance_json` 8959, `design_report.py` | MOD9 | 참고 + 새 결과 JSON 스키마(1.1 출력). 옛 instance.json은 어댑터로 계속 생성 | DEC-77 front 저장 |
| LUT 생성 도구 | `sky130_lut_sweep.py` | 도구 유지 | 그대로 + U-27 확장 | U-27 P 1104 |
| SPICE 하네스 시제품 | `_drafts/engine/spice_harness/` | `tools/spice_oracle/` | 이관(엔진 import 없음) | 0.1 |
| 스펙 값 | `workspaces/run_harness.py` `SPECS` | 회로별 spec JSON(출처 필드) | 값만 옮김, 출처 표기 | U-35 P 1112 |

### 0.4 test 체계

| 층 | 내용 | 옛 자산 재사용 |
|---|---|---|
| contracts | IC1~IC11(P 821~831), SC-a~SC-e(P 404) | **정의 재사용, 코드 새로**: 계약 문장은 엔진과 무관하나 옛 test 파일은 옛 함수 이름을 부른다. 새 API로 다시 쓰고 해당 단계 완료 시 활성 |
| oracles | (i) LUT npz 격자 직접 조회 (ii) 손계산 toy 회로(이름 없는 2~4소자) (iii) SPICE 오라클(`tools/spice_oracle`, free 모드 = 판정, forced 모드 = 진단) (iv) VCCS 등가회로 ngspice(MNA) | 옛 엔진 출력은 오라클이 아니다(대조 기록만) |
| unit | 모듈별(MOD1~MOD10) | LUT·레일 접근자 test만 이식 |
| integration | 파일럿 E2E, 레이아웃 어댑터 | -- |
| regression | 9회로 E2E(T9), 규칙 분기 발동표(DEC-59) | -- |

test 작성 주체는 코드 작성 주체와 분리하고(PROCEDURE 1), 기대값은 오라클에서만 만든다(피검 함수로 기대값을 만들지 않는다).

### 0.5 계획서 Phase와의 관계

| Phase | 새 엔진에서 |
|---|---|
| 3(옛 엔진 모듈 분할, M1~M10·F1·F2) | **기본안에서 뺌**: 새 엔진이 처음부터 MOD1~MOD10으로 지어지므로 옛 코드 이동은 결과에 남지 않는다. 이미 끝난 B26-1은 부품으로 가져간다 |
| 4(DF 수정) | 옛 결함 DF-01~37(P 907~949)은 고치지 않고 **재발 금지 목록**으로 각 설계 단위의 완료 조건에 넣는다(예: DF-16 → 전력 축은 공급 전류, DF-01·02 → DC 정본이 구조적으로 막음) |
| 5(실패 캐시) | 평가 커널 단위에 최소형(실패 기록 + 지문 키)만 |
| 6a·6b·7a·7b | 이 로드맵의 본체(축소 지점은 0.2·4절) |
| 6c·7c | GB4 축소와 SPICE 오라클만 |
| 옛 엔진 국소 패치(nmcnr 수정안 A, two_stage stage1_out) | **기본안에서 뺌**: 옛 헤드룸 경로(`_hr_*`)를 새 엔진은 쓰지 않는다. 진단 결과(nmcnr_diag 2~3절)는 GB1 기둥·GB7 W2 블록의 test 픽스처로 쓴다 |

---

## 1. 합격 시험 정의

### 1.1 입력과 출력

| 구분 | 내용 | 근거 |
|---|---|---|
| 입력 | topology.json의 connectivity·`ports`·`supply_nets`·`supplies_v`·`passive_elements`·`ideal_sources`, 회로 스펙(제약 값과 출처, 목적 축, 예산), gm/ID LUT(sky130 tt 27 C) | P 141, GB0 P 314, U-25 P 1102, U-26 P 1103 |
| 읽지 않는 것(역할 태그) | `device_roles`, `vertical_stack_id`, `fold_group`, `headroom_role`, `shared_gm_id_groups`, `budget_reference_device`, 손선언 theta·stage 구성. 새 엔진 로더는 이 키를 읽지 않는다(목록은 D13) | 6a 완료 P 1023, IC4 P 824 |
| 출력(결과 JSON) | 소자 W·L·finger(`w=finger_w`, `m=n_fingers`)·ID·VGS·VDS·VSB, 노드전압 전부(S2 `dc`), 이상원 값, 수동소자 값(보상 C·Rz 유도값), metric, front 표(점마다 θ*, 전력, 면적, 활성 제약 여유)와 예산 점, 실패 레코드와 exit code(N3.14) | P 499, N3.14 P 734, DEC-77 P 271 |
| W 정본 | 엔진 평가 안에서 W = n_fingers × W_ref(D2)로 정해진 값 하나. 레이아웃 어댑터는 W를 바꾸지 않는다 | lut_coverage_study 6절 |

### 1.2 판정 항목 (회로마다)

| # | 항목 | 판정 문장 | 근거 |
|---|---|---|---|
| T1 | 엔진 완주 | `run_gmid_design_pipeline(spec)`이 exit 0, 결과 JSON에 1.1 출력 전부 | MOD10 P 530, N3.14 |
| T2 | 역할 태그 없음 | 로더가 1.1의 역할 태그 키를 읽지 않음(키를 넣은 입력과 지운 입력의 결과 JSON 해시 같음). 기존 4회로는 유도 input·cascode·tail 멤버십이 옛 선언과 같음(다르면 `review_needed`로 U2 ratify) | P 1023, IC4 P 824 |
| T3 | DC 봉인 | 최종 해가 봉인 항목 1~8(P 428~435)을 tol_V·tol_I 안에서 통과 | N3.6 P 422~442 |
| T4 | SPICE DC(free 모드) | 회로가 스스로 DC 해를 찾는 테스트벤치에서 ID > 0 인 모든 MOS 포화(VDS − VDsat ≥ 0). 엔진 S2 `dc`와의 노드전압·소자 ID 차는 합격 조건이 아니고 T8로 기록만, 경고는 forced 모드에서만(사용자 확정 2026-10-07 8번, 계획 N3.6) | P 434·442·499 |
| T5 | SPICE 성능 | 선언된 성능 제약 전부를 SPICE 측정값이 만족(gain, GBW, PM, Rout, 공급 전류). 비교 metric 정의 **결정 대기 D15** | U-25, U-35, DEC-66 P 260 |
| T6 | front | 전력(공급 전류, DEC-78)·면적(탐색 축, DEC-79 (a)) 비지배 front: 끝점 2 + ε점(시간 예산 안) + 비지배 필터(표 안에 서로 지배하는 점 0), 예산 선언 시 예산 점. 면적 판정 축 **결정 대기 D4**, 예산 **결정 대기 D7** | DEC-77~80 P 271~274, N3.7 P 472 |
| T7 | SPICE를 돌리는 front 점 | **결정 대기 D5**(기본안: 양 끝점 + 예산 점), 그 점마다 T4·T5 | -- |
| T8 | 모델 오차 기록 | 회로·metric·노드·소자별 abs(엔진 − SPICE) 저장, 임계 아님 | DEC-72 P 266 |
| T9 | 회귀 | 9회로 E2E test가 새 test 체계 전체 실행에 포함, green | IC7 P 827 |

### 1.3 9회로 표

| 회로 | 레일 | 스펙 상태 | 새 엔진에서 필요한 단계 | 판정 범위 |
|---|---|---|---|---|
| current_reuse_telescopic_ota (파일럿) | vdd/gnd | gain ≥ 54, PM ≥ 70 외 5건. GBW 미선언 | GB7 순환 블록(CMFB·bias SCC), 완전차동 테스트벤치, Iref 정본(D14) | T1~T9 |
| two_stage_ota | vdd/gnd | gain ≥ 57(U-19 P 1096 재도출 대상). GBW 7 MHz·CL 3 pF는 보상 목표 | GB1 기둥(옛 stage1_out KVL 실패 I-C11 P 981을 픽스처로), CL 연결(U-31 P 1108) | T1~T9, GBW·PM 제약 값 **결정 대기 D1** |
| folded_cascode | vdd/gnd | 제약 0건(U-35 `pending_7a`), CL 1 pF | 폴딩 기둥(옛 엔진 노드가 레일 밖 -0.85 V였던 것을 픽스처로) | 제약 값 **결정 대기 D1**, 그 전에는 T1~T4·T6·T8 |
| nmcnr_amplifier | vdd 0.9 / vss −0.9 | 제약 0건(U-35), 보상 목표 GBW 816 kHz·CL 100 pF·PM 70 | 분할 레일(DEC-60 P 254), 기둥 diode 창(nmcnr_diag 2절 수치를 픽스처로), 자유 θ 적음 → front 퇴화 | 제약 값 **결정 대기 D1** |
| common_gate_amplifier | vdd/gnd | 스펙 없음 | CG 셀(J12-i P 1069) | 스펙 **결정 대기 D1**, 그 전에는 T1~T4·T6·T8 |
| ngcc_3stage_ff | vdd/gnd | gain 미선언(U-34 P 1111), Cm1·Cm2·CL 확정 | 복합 블록(DEC-81 P 275), NGCC 보상(DEC-70) | gain **결정 대기 D1** |
| pushpull_follower_buffer | vdd/vss/agnd | Rout ≤ 1 kΩ, CL 1 pF, 최소 전력(U-25) | 3레일, 버퍼 묶음(DEC-63 P 257), 출력 방향(DEC-65 P 259), `kvl_branch`(DEC-64 P 258), CD source W2 | T1~T9 |
| sf_pushpull_output_opamp | vdd/vss/agnd | Av ≥ 65 dB, GB ≥ 60 MHz, Rout ≤ 1 kΩ, CL 1 pF(U-25) | 위 버퍼 요구 + K8 측면 주입(J12-d P 1064), Cc–agnd 보상 | T1~T9 |
| two_stage_ota_sf | vdd/gnd | two_stage 상속 + CL 3 pF@vout, Rout ≤ 1 kΩ(U-25) | CD source W2, follower 블록(J12-g P 1067) | T1~T9 |

회로 합격 = 판정 범위의 T 전부. 범위 합격 = 9회로 합격 + T9.

---

## 2. 작업 단위

공통 완료 조건(문장에서 생략): 새 test 체계 전체 0 failed, 약화 0(있으면 보고서 나열), 옛 엔진 대비 차이는 2.6 대조 기록에 남김.

### 2.1 설계 단위 (레인 P, 단 D0·D1은 임계 경로)

계획서 N9.1(P 1149~1170)의 design 문서 중 6a~7c가 없다. 구현 전에 **인터페이스 명세 수준**(데이터 스키마, 함수 시그니처, 실패 클래스, 단위별 오라클, N9.1 '반드시 담을 것' 중 이 범위 몫)만 쓴다.

| ID | 산출물 | 계획서 근거 | 선행 | 규모 | 완료 조건 |
|---|---|---|---|---|---|
| D0 | 공통 인터페이스: 패키지 골격, MOD1~MOD10 공개 API 시그니처, S0·S1·S1v·S2(`dc`/`ss`/`ls`)·S3 필드 스키마, 결과 JSON 스키마, 실패 클래스(N3.14), 옛 DF 재발 금지 목록 | N3.3 P 359~380, N3.10, N3.14, `00-common` | U1 | L, 11 | 파일럿을 예로 든 스키마 JSON 예시가 있고, 모든 단위가 이 문서의 이름만으로 test를 쓸 수 있음 |
| D1 | `6a-structure-stage` 명세(GB0~GB2: S1 엣지 `domain`·status, 셀 우선순위, SP1, 루프 분류, 기둥 유도, DC 역할, DEC-63/65/81, 발동표, 열린 항목 ①~⑮ 기본안) | N9.1 P 1162 | D0 | L, 11 | 열린 항목 15개 각각 기본안·근거, 단위 N2~N9 오라클 목록 |
| D2 | `6b-node-voltage-seal` 명세(S2 `dc`, W0~W4 권한표, 계산 블록 입출력과 유도 DAG, 순환 블록 고정점, 봉인 1~8, tol_V·tol_I·K_max) | N9.1 `6b`, N3.4~N3.6 P 382~442 | D0 | L, 11 | 권한표(필드 × 티어), toy 픽스처 손계산 기대값 |
| D3 | `7a-gain-metric` 명세(S2 `ss`, MNA·gmb, `gain_ss_db`, GBW, PM 루프 정의, `rout_ss_ohm`, 전력·면적 축, GB4 축소, SPICE 오라클 인터페이스·모델 오차) | N9.1 `7a`, N3.8 P 486~499 | D0 | M, 9 | metric마다 정의·단위·오라클 |
| D4 | `7b-compensation-allocation` 명세(GB5 규칙: 단일단 U-12, Miller, NGCC, Cc–agnd, class-AB / GB6: 층 0 최소, 외층 SLSQP, ε-제약 두 방향, 비지배 필터, 예산 점) | N9.1 `7b`, N3.7 P 444~485, DEC-70 | D2, D3 | L, 11 | 보상 규칙 9회로 적용표, ε 격자 규칙(시간 예산에서 유도) |
| D5 | 회로 스펙 파일 형식(N3.15 축소: constraints·source·보상 목표·supplies_v·예산) | N3.15 P 753 | D0 | S, 1.7 | 9회로 spec JSON 예시 |
| **설계 합** | | | | **약 55 h** | |

### 2.2 레인 2 -- 구조 (MOD2·MOD3)

| ID | 내용 | 계획서 근거 | 선행 | 규모 | 완료 조건 |
|---|---|---|---|---|---|
| N1 | GB0: topology·spec 로더와 로드 게이트(`supply_nets` 필수, 출처 없는 제약 거부, 역할 태그 키 무시), `rail_declaration` 이식 | GB0 P 314, B26-1, U-35 | D0, D5 | M + S, 6.2 | 9회로 로드, 게이트마다 거부 test, T2의 해시 동일 test |
| N2 | S0 지문 + S1 그래프: 노드{terminals, is_rail, ac_ground_class, port_role}, 소자{d, g, s, b(DEC-61), is_diode}, 수동소자, 관계 엣지{type, domain, members, status, evidence} | N3.3 P 363~364, DEC-60·61 | N1, D1 | L, 11 | 9회로 S1 생성, 지문이 입력 변경에 따라 바뀜(SC-d), 구조 질의는 모두 그래프 질의 |
| N3 | GB1 DC 쪽: 소자 DC 역할(tail·미러·diode 부하·바이어스·캐스코드 바이어스), 미러 그룹, diffpair, L 동치류, 교류접지 집합 | GB1 P 315, P 1162(①③⑫) | N2 | L, 11 | 9회로 DC 역할 표, 4회로 tail·cascode·input 멤버십이 옛 선언과 같음 |
| N4 | GB1 기둥: DC 전도 그래프, 레일·분기 노드, 가지·기둥 열거, 기둥↔블록 매핑, G_vgs 사이클(DEC-64) | DEC-71 P 265, J13 P 1070, DEC-64 P 258 | N3 | L, 11 | 9회로 기둥 표, 4회로 `vertical_stack_id`와 대조표, push-pull 2회로 `kvl_branch` 등식 탐지 |
| N5 | GB2: 셀 분류 CS/CG/CD/pass/diode, 구동 종류, SP1 stage 분할(0-1 BFS), 출력노드·극점 노드, S1v | GB2 P 316, SP1 N3.2 P 337 | N3 | L×2, 22 | 9회로 stage 표, 4회로 stage 수 옛 선언과 같음 |
| N6 | 루프 탐지·(0)~(4) 분류·끊는 점, 피드백 극성 | J11 P 1059, P 342 | N5 | L, 11 | 9회로 루프 표 |
| N7 | 버퍼 묶음·출력 방향·복합 블록 | DEC-63·65·81 P 257·259·275, J12-a·e P 1061·1065 | N5, N6 | M + M + L, 20 | J12-a·e 기대값과 같음, ngcc feedforward가 복합 블록 하나 |
| N8 | 규칙 분기 발동표 + `review_needed`·`unsupported_rule_branch` 정지 | DEC-59 P 253, N3.14 | N3~N7 | S + M, 6.2 | 지원하지 않는 분기에서 STRUCTURE_UNRESOLVED로 정지하는 test |
| N9 | `structure.json`·J 대조표 출력(U2 입력) | J2~J13 P 1050~1070 | N3~N7 | M, 4.5 | 9회로 대조표 |
| **레인 2 합** | | | | **약 103 h** | |

### 2.3 레인 1 -- DC·사이징·탐색 (MOD1·MOD4·MOD6)

| ID | 내용 | 계획서 근거 | 선행 | 규모 | 완료 조건 |
|---|---|---|---|---|---|
| K1 | MOD1: LUT 이식 + `w_ref_m` + VS 축 밖 거부 + gmb + tol_V(LOO) | MOD1 P 521, DF-27 P 939, P 490 | D0 | M, 6 | 격자점 오라클 비트 동일, 축 밖 조회 거부 test |
| K2 | **GB7 DC 정본**: S2 `dc`, writer 티어 W0~W4(레일·diode·W2 물리 종속·W3 목표·W4 자유), 순환 블록 고정점(SC-c), 봉인 1~8, SC-a(단일 writer)·SC-b(버전) | DEC-31 P 226, DEC-67 P 261, GB7 P 321, N3.4~N3.6 | K1, N4, D2 | XL + L, 33 (P 60) | toy 픽스처 손계산 노드전압 재현, 같은 노드 두 writer를 봉인이 거부, 4회로에서 공유 게이트 넷 전압 하나·KCL 잔차 ≤ tol_I, 원시 대입 grep 0 |
| K3 | 소자 사이징: gm_id·L(N3.9 규칙, `dc_role` 입력)·W = n × W_ref(D2), 협폭 슬라이스(D3) | N3.9 P 501, DEC-12 P 207 | K2 | L + M, 15.5 | W가 W_ref 정수배(협폭은 슬라이스 격자 폭), 단일 소자 SPICE 오라클 ID 오차가 W_ref finger에서 LUT 보간 오차 안 |
| K4 | 평가 커널 조립(② 전류 → ③ L → ④ 기둥·순환 → ⑤ W → 봉인 → ① GB5 판정 → ⑥ metric), 실패 레코드·exit code, 실패 캐시 최소형, MOD9 결과 JSON, MOD10 진입점 | N3.5 P 410, N3.14, MOD9·10 | K3, M1 | L + M, 15.5 | 파일럿 1점 평가가 결과 JSON을 내고, 봉인 실패 후보가 margin과 함께 기록되고 탐색이 계속됨 |
| K5 | 9회로 확장 DC: 분할 레일·3레일(agnd), IC11, CD source W2, `kvl_branch` 정지전류, K8 측면 주입 | DEC-60 P 254, IC11 P 831, W2 P 390, DEC-64, J12-d | K2, N4 | M×4, 18 | nmcnr ±0.9 V와 0/1.8 V 실행이 원점 이동 동등, push-pull 등식 잔차 ≤ 멤버 수 × tol_V |
| K6 | GB4 축소: 블록 gain AC 상한·LUT 곡선 검사 → INFEASIBLE_TARGET | GB4 P 318 | N5, M1 | M, 4.5 | 불가능한 gain 스펙 픽스처에서 탐색 전 정지(exit 3) |
| K7 | GB5 보상 규칙(θ 제약, 봉인 스냅샷 `ss`로 판정) | DEC-70 P 264, U-12 P 1089, J3·J7 | K4, N5, N6, D4 | L + M, 15.5 | 9회로 보상 소자 값이 결과 JSON에 있고, 옛 회로별 함수와 4회로 대조 기록 |
| K8 | GB6: 층 0 최소(기둥 KVL 조립 시작점) + 외층 SLSQP multi-start + ε-제약 두 방향 + 비지배 필터 + 실패 ε 기록 + 예산 점 | DEC-71 P 265, DEC-54 P 248, DEC-77 P 271, N3.7 P 472, U-13 P 1090 | K4, M1, D4 | L×2, 22 | 파일럿 front 표에 서로 지배하는 점 0, 시작점이 봉인 통과, 예산 선언 회로에서 예산 점 1개 |
| **레인 1 합** | | | | **약 130 h** | |

### 2.4 레인 P -- metric·SPICE·LUT·스펙·test 기반

| ID | 내용 | 계획서 근거 | 선행 | 규모 | 완료 조건 |
|---|---|---|---|---|---|
| M1 | MOD5 GB8 핵심: S2 `ss`, MNA 이식 + gmb 스탬프, `gain_ss_db`, GBW(\|H\|=1), PM(측정 크로스오버, 루프 정의 D15), 공급 전류(DEC-78), 면적 탐색 축 + 수동소자(DEC-79 (a), U-36), Rz, 미스매치 σ | GB8 P 322, N3.8 P 486, DEC-78·79 | K1, D3 | L + M, 15.5 | VCCS 등가회로 ngspice 오라클과 gain·위상 일치, metric마다 손계산 test |
| M2 | `rout_ss_ohm` | DEC-66 P 260 | M1 | M, 4.5 | 버퍼 toy에서 손계산과 일치 |
| P1 | SPICE 오라클 이관(`tools/spice_oracle`): 넷리스트(`w=finger_w m=n`), free·forced 모드, 개루프 DC 안정화, CMFB, `.op` 영역, `.ac` gain·GBW·PM(D15)·Rout, tol 파일, 비교표, 모델 오차 파일 | P 499, U-11 P 1088, DEC-72 | -- | M + L + S, 17 | 옛 엔진 파일럿 결과로 시제품과 같은 표 재현, 엔진 import 0 |
| P2 | 회로군 적응: 완전차동, 3레일, 버퍼 | U-25 | P1 | M×3, 13.5 | 각 군 1회로 free 모드 실행 |
| P3 | LUT: `w_ref_m` 메타, U-27 재생성(VS 0~1.8, CGS·CGB·SID_1F, 기계 약 22 h 백그라운드), 협폭 DC 슬라이스(D3, 약 30 분) | U-27 P 1104, DF-28 P 940 | U1 | M, 4.5 | 옛 격자점 값 같음, 메타 기록 |
| P4 | 회로 스펙 9개(출처 포함) | U-25, U-35, D5 | D1(결정), D5 | S×9, 15 | constraints에 출처 없는 값 0 |
| P5 | test 기반: conftest(real_lut·toy_lut·library), contracts IC1~IC11·SC-a~e 새 API로 재작성(xfail로 선언, 해당 단위에서 활성), 오라클 (i)(ii)(iv) | N3.11, N4.1 | D0 | L + M, 15.5 | 계약 test 수집, xfail 사유에 담당 단위 |
| P6 | 옛 엔진 대조 기준선 고정: 파일럿·folded 결과와 SPICE 오라클 결과 저장 | -- | P1 | S, 1.7 | 대조 파일 |
| P7 | 9회로 E2E 회귀(T9) | IC7 P 827 | Z1~Z9 | M, 4.5 | 전체 실행에 포함, green |
| **레인 P 합(설계 제외)** | | | | **약 92 h** | |

### 2.5 closure

| ID | 내용 | 규모 | 완료 조건 |
|---|---|---|---|
| Z1~Z9 | 회로별: SPICE 불합격 → 원인 → 해당 단위 수정 반복 | 회로당 8 h (3~20), 합 72 | 그 회로 1.3 판정 범위 통과 |

### 2.6 대조 기록(옛 엔진 대비)

새 엔진 단위가 끝날 때마다 4회로(옛 엔진이 다루는 범위)에서 옛 출력과의 차를 표로 남긴다: 구조 멤버십(N3·N5), 노드전압(K2, 옛 `propagate_node_voltages`), metric(M1). 차는 판정이 아니라 설명 대상이고, 판정은 오라클(손계산·SPICE)만 한다.

### 2.7 합계와 임계 경로 (중앙, h)

| 묶음 | h |
|---|---|
| 설계 D0~D5 | 55 |
| 레인 2 N1~N9 | 103 |
| 레인 1 K1~K8 | 130 |
| 레인 P M1·M2·P1~P7 | 92 |
| closure | 72 |
| **합** | **452** |

임계 경로: D0 11 → D1 11 → N1 6.2 → N2 11 → N3 11 → N4 11 → K2 33 → K3 15.5 → K4 15.5 → K7 15.5 → K8 22 → closure 뒤쪽 3/4 54 → P7 4.5 ≈ **222 h**. 처리 용량 한계(총 452 h ÷ 유효 동시성 1.7) ≈ **266 h**가 더 크므로 소요 작업 시간은 약 266 h다.

옛 엔진 수리 계획(이전 산정 약 393 h)과의 차: 빠지는 것 -- Phase 3 이동 13.2, 옛 DF 국소 수정 약 12, 국소 패치(nmcnr A·two_stage) 10.7, 손 태그 대체 배선(옛 S12) 22, finger 배정 뒤 재사이징 11 ≈ −69 h / 더해지는 것 -- 설계 문서 55, 커널·구조 새로 짓기(이식 대신) 약 +50, test 기반 15.5, LUT·레일 이식 test 약 +6 ≈ +127 h. 순 +59 h.

---

## 3. 주차별 순서

사용자 몫은 세 번: **U1(1주 1~2일, 4절 결정 전부 + D0 인터페이스 승인)**, **U2(3주 끝, 구조 공동분석 한 번)**, **U3(6주, 결과 검토)**.

| 주 | 레인 1 | 레인 2 | 레인 P | 사용자 몫 | 주 끝 상태(측정) |
|---|---|---|---|---|---|
| 1 | K1 | D0 → D1(설계 담당 겸함), N1 착수 | P1, P3(재생성 백그라운드), P5, P6, D5 | **U1** | 패키지 골격, LUT 이식 green, SPICE 오라클이 옛 파일럿 결과로 동작 |
| 2 | D2, K2 착수(toy 픽스처) | N2, N3 | D3, M1, P4 | -- | 9회로 S1 그래프·DC 역할 표 |
| 3 | K2 계속 | N4, N5, N9 | M1 끝, D4, P2(완전차동) | **U2**: 9회로 J 대조표·J12-a~i·열린 항목 ①~⑮, nmcnr Q1~Q3, connectivity 확인(D12) | 9회로 기둥·stage 표, 4회로 노드전압 정본 toy 재현 |
| 4 | K2 끝, K3, K4 → **Z1 파일럿** | N6, N8 | P2(3레일·버퍼), M2 | -- | **1달 점검 = 마일스톤 1**: 새 엔진 파일럿 SPICE 합격(5절), 9회로 구조 ratify 완료 |
| 5 | K7, K8, K6, Z2~Z4(two_stage·folded·nmcnr) | N7 | P4 마무리 | -- | 기존 4회로 합격 + front 표 |
| 6 | K5, Z5~Z9 | 구조 수정(closure 요청분) | P7 | **U3**: 9회로 합격표, 예산 미선언 회로의 front 점 선택 | 범위 합격 |

달력 해석: 소요 266 h = 활동일 25.3일. 활동일 비율 0.8이면 약 32일 + 응답 대기 약 3.5일 ≈ **35일(5주)**, 0.55면 약 46일 + 3.5일 ≈ **50일(7주)**. 위 표는 비율 약 0.65 기준 6주이고, 0.55면 7주차가 closure 꼬리(Z7~Z9)로 붙는다.

---

## 4. 사용자 결정 묶음 (U1에서 한 번에)

| # | 결정 | 기본안 | 근거 |
|---|---|---|---|
| D1 | 회로별 스펙 값: common_gate 전부, ngcc gain, folded·nmcnr gain/GBW/PM, two_stage GBW·PM을 제약으로 올릴지, U-19 gain 재도출 | 사용자가 준 값만 제약(`user_spec`). 값이 없는 metric은 '보고만', 그 회로는 영역·선언 스펙만 판정. 실행 spec의 보상 목표(GBW·PM·CL)는 출처 확인 뒤 제약으로 | 스펙은 사용자 몫, U-35 P 1112는 자기 결과 역산값을 삭제 |
| D2 | finger 폭 = LUT W_ref, W = n × W_ref | 채택. W_ref는 LUT 메타 `w_ref_m` | 단일소자 ID 오차 중앙값 19.5 % → 3.2 %, 미러 비 오차 0(lut_coverage_study 표 B·6절) |
| D3 | U-27에 DC 전용 협폭 슬라이스 | 채택: PDK bin 폭 0.42·0.55·0.64·0.84·1.0·1.26·1.68·2.0·3.0 µm, ID·GM·GDS만, 보간 금지 | 협폭 오차 +60~106 %, 비용 약 30 분, 용량 W 비례 ±9 % |
| D4 | 면적 판정 축을 탐색 축(ΣW·L + 선언 수동소자)으로 축소, MOD8 수렴 루프 범위 밖 | **해소(사용자 확정 12번 (나))**: 탐색은 ΣW·L, front 는 floorplan 외곽 면적(판정 축)으로 재필터, 동률 = 격자 한 칸, MOD8 W_request 루프는 범위 안 | DEC-79 P 273(정본은 레이아웃 축) |
| D5 | SPICE를 돌리는 front 점 | 양 끝점 + 예산 점 | ngspice 1회 초 단위, 끝점이 활성 제약 경계 |
| D6 | SPICE 오차 처리 | **확정(사용자 2026-10-07 8번)**: 합격 = free 모드 스펙 만족 + 포화 여유 0. 노드전압·소자 ID/gm/gds·성능 차는 기록만(노드전압은 합격 비교 대상이 아님), 성능 차는 모델 오차로 제약 여유에 반영, 경고는 forced 모드에서 소자 차 > LUT 계산 허용오차일 때만 | DEC-72 P 266, NFR-5 P 185, P 442 |
| D7 | 면적 예산(U-13) | 미선언 → front 제시 후 정지, U3에서 점 선택 | DEC-77 P 271 |
| D8 | 수동소자 면적 단위(U-36) 출처 | sky130 MIM·저항 단위 면적을 PDK 문서에서 읽어 출처와 함께 선언, 사용자가 출처 승인. 미선언 회로 front `review_needed` | U-36 P 1113 |
| D9 | front 시간 예산 | 풀이 1회 300 s(DEC-34), front 점 수 = front 예산 / 실측 1회 시간. front 예산 값은 사용자(300 s면 끝점 2개뿐) | DEC-34 P 228 |
| D10 | 보상 단 gm/ID를 결정변수로 | 새 엔진은 처음부터 소자별 gm_id를 θ로 둘 수 있으나(DEC-04 P 200) 탐색 차원이 커진다. 기본: 보상 단 포함 θ로 두고 SLSQP 시간이 D9 예산을 넘으면 보상 단만 GB5 규칙값으로 고정 | DEC-04, D9 |
| D11 | 옛 엔진 결과와의 차이 처리 | 기준선 변경 승인(DEC-40) 대상이 아니라 2.6 대조 기록. 옛 기준선은 옛 엔진에 묶여 동결 | 전제(옛 엔진 = 참고) |
| D12 | connectivity 확인: CL을 two_stage·folded·nmcnr 출력에, J9 passive 누락분 | spec 값(3 pF / 1 pF / 100 pF)으로 출력–레일에 추가 | U-31 P 1108, J9 P 1057 |
| D13 | 역할 태그 범위(로더가 읽지 않는 키) | 1.1 목록. spec·constraints·ports·supply_nets·passive 값·ideal source 값은 입력 | P 1023 |
| D14 | 이상 전류원 정본(파일럿 Iref topology 1.2 µA 대 옛 엔진 0.1993 µA) | 선언값이 있으면 정본(엔진이 소비), null이면 엔진이 정해 출력 | DEC-08 P 203, I-B14 P 971 |
| D15 | 비교 metric 정의: gain(단 합 대 전회로 MNA), PM 루프(β=1 대 Cf/Cs β) | gain = 전회로 MNA. PM = 선언된 되먹임 수동소자가 있으면 그 β 루프, 없으면 β=1. 엔진·오라클 같은 정의. 파일럿 β 해석은 U2 | I-B21 P 972. 옛 파일럿 강제 바이어스 SPICE: 단 합 대비 6.6 dB, MNA 대비 12.1 dB 차 |
| D16 | 새 엔진 위치·이름 | 0.1 표(`skills/analog-gmid-design/gmid_engine/`, 파일명 N3.10, test는 패키지 아래, 오라클은 `tools/spice_oracle/`) | N3.10 P 515 |
| D17 | 옛 엔진 작업 중단: Phase 3 가벼운 절차(M1~M10·F1·F2) 멈춤, 옛 test 동결, 퇴역은 9회로 합격 뒤 별도 결정 | 그렇게 한다 | 옛 코드 이동은 새 엔진 결과에 남지 않음 |
| D18 | GB6 층 0을 최소형(시작점 조립)으로, 블록별 gain bin front·GB3·정밀 경로는 범위 밖 | 그렇게 한다. U-33 실측은 9회로 합격 뒤 | U-33 P 1110, DEC-73 P 267 |

공동분석(U2 한 번): J2~J13(P 1050~1070), J12-a~i, 6a 열린 항목 ①~⑮(P 1162), nmcnr Q1~Q3(M203 역할, M201 VDS 종속, M204 포화 요구).

결정 개수: **18개(D1~D18)**, 공동분석 묶음 1개.

---

## 5. 첫 마일스톤: 새 엔진 파일럿 SPICE 합격 (4주 끝)

파일럿 = current_reuse_telescopic_ota(51소자, 완전차동, CMFB, 수동소자 12개).

옛 엔진 대조 사실(새 엔진이 넘어야 할 것, spice_harness_report 3.1): 옛 엔진은 제약 7/7 만족으로 판정하지만 free 모드에서 출력이 레일에 붙는다. 노드를 강제해야 gain 54.98 dB·PM 79.25°가 나오고 KCL 잔차 Vy 198 µA, 공유 게이트 넷 요구 전압 차 최대 0.89 V, layout W(29/51 소자 > 5 % 차)로는 PM 18°.

필요한 단위:

| 순 | 단위 | 파일럿에서 보장하는 것 |
|---|---|---|
| 1 | D0, D5, P4(파일럿), U1의 D2·D6·D14·D15 | 입력·출력 형식, Iref 값, 비교 정의 |
| 2 | K1, P3 메타 | LUT 조회와 W_ref |
| 3 | D1, N1~N4 | S1 그래프, DC 역할, 기둥(손 태그 없이) |
| 4 | D2, K2 | 노드전압 정본, 공유 게이트 넷 전압 하나, KCL ≤ tol_I, CMFB·bias 순환 블록 수렴 |
| 5 | K3 | W = n × W_ref 하나(레이아웃이 바꾸지 않음) |
| 6 | D3, M1 | MNA gain·GBW·PM(D15 정의), 공급 전류, 면적 |
| 7 | K4 + K8 끝점 2개(층 0 시작점 + SLSQP, 전력 최소·면적 최소) | 결과 JSON, front 양 끝 |
| 8 | P1, P5 | free 모드 오라클, 계약 test |
| 9 | Z1 | 불합격 원인 반복 |

GB5 일반 규칙(K7)은 마일스톤에 필요 없다: 파일럿 보상 소자는 선언값(Cc·CL·Cf·Cs)과 Rz = 1/gm 규칙이고 PM은 M1 metric 제약으로 판정한다.

완료 조건: (a) T1·T2·T3 통과 (b) free 모드에서 ID > 0 소자 전부 포화(엔진 S2 `dc`와의 노드전압 차는 기록만, 사용자 확정 8번) (c) SPICE로 재는 선언 제약(gain, PM, 공급 전류) 만족 (d) front 양 끝점 각각 (b)(c) (e) 모델 오차 파일 (f) Z1 반복 수 기록(6절 재추정 입력) (g) 2.6 대조 기록(옛 엔진 대비 노드전압·metric 차).

---

## 6. 위험과 1달을 넘길 합리적 사유

### 6.1 위험

| # | 위험 | 신호(측정) | 대응 |
|---|---|---|---|
| R1 | 새 코드가 옛 결함 클래스를 다시 만듦 | D0 재발 금지 목록 항목별 test | 목록 항목마다 계약 test를 단위 완료 조건에 |
| R2 | 설계 문서가 구현 중 바뀜(인터페이스 흔들림) | D0 이후 시그니처 변경 수 | 바뀌면 D 문서와 test를 같은 커밋에서 갱신, 2회 넘으면 U에 보고 |
| R3 | GB7 순환 블록(CMFB·bias SCC) 비수렴 | 파일럿 NONCONVERGENT 발생 | K_max·초기값(층 0 시작점) 조정, 남으면 회로 해석 문제로 U2 |
| R4 | closure 반복 수가 많음 | Z1 반복 수 | 회로당 8 h를 실측으로 교체 |
| R5 | L 단위 실측 단가 > 추정 | N2·N3·K2 실측 h | 2주 끝 재추정 |
| R6 | 비지배 front가 국소해로 지배점 포함 | 필터가 버린 점 비율 | 시작점 수를 D9 예산 안에서 늘림 |
| R7 | ratify 왕복 | U2 뒤 미결 수 | 남은 항목만 문서로 질의 |
| R8 | LUT 재생성 기계 시간 | P3 진행률 | 백그라운드, 결과 전에는 VS 축 밖 거부 |

### 6.2 1달을 넘길 합리적 사유 후보 (수치)

| 사유 | 수치 근거 | 일정 영향(중앙) |
|---|---|---|
| A. 새로 짓는 비용: 설계 문서 6~7c 부재 | 계획서 N9.1 문서 중 6a·6b·6c·7a·7b·7c design 없음, 인터페이스 명세 55 h | 총 +55 h(그중 D0·D1 22 h는 임계 경로) |
| B. DC 정본이 핵심 필수 | 옛 파일럿 free 모드 미동작, 강제 시 KCL 잔차 198 µA, 게이트 넷 요구 전압 차 0.89 V, 옛 folded 노드 충돌 1.6 V, 옛 nmcnr KCL 잔차 1779 µA·vsb 1.3 V | K2 33 h(비관 60 h), 임계 경로 위 |
| C. 합계 | 옛 엔진 수리안 393 h 대비 새 엔진 452 h(+59 h). 처리 용량 한계 266 h | 비율 0.8: 35일, 0.55: 50일 |
| D. closure 회로당 20 h(비관) | Z1 반복 수 > 3 | +108 h → 약 9~10주 |
| E. U2 ratify 두 번 이상 왕복 | 미결 항목 수 | 왕복당 +2~3일 |
| F. 활동일 비율 0.55 유지 | 실측 0.53~0.57 | 0.8 대비 +15일 |

판단 규칙: 4주 끝 마일스톤 1이 통과하면 범위 합격은 5주(0.8)~7주(0.55) 안이다. 통과하지 못하면 Z1 반복 수와 K2 실측 h로 다시 계산하고, 8주를 넘으면 범위 축소안(ngcc·sf를 구조 유도까지만, front 끝점 + 예산 점만)을 U에 올린다.


## 정정 (2026-10-07, 사용자 지시 반영) -- W·레이아웃 규칙

앞 절의 'W는 엔진이 n x W_ref로 정한 값 하나, 레이아웃은 W를 바꾸지 못함' 규칙을 철회하고 다음으로 바꾼다.

1. sizing이 gm/ID·L·ID를 정하고 총 W를 유도한다(references/gm-id-methodology.md §2.2 식 1.18). 레이아웃은 총 W를 유지한다(finger 양자화 허용 범위 안).
2. 레이아웃은 matching을 고려해 stack별 finger_w·nf·행 구성을 고른다(stick-diagram-euler-layout.md §2.7, §8.1~8.2). matching 패턴 규칙(사용자 지정): **differential pair = common-centroid 필수**, 그 밖의 matching 그룹(미러 등) = common-centroid 또는 interdigitation 중 선택(box·면적·Euler 실현성으로 결정). matched 소자는 같은 unit geometry 반복(§2.7). 차동쌍·미러 판정은 6a 구조 유도 출력(태그 아님).
3. 고른 finger_w가 LUT 기준폭과 다르면 그 폭의 DC LUT 슬라이스(PDK 특성화 폭)로 재확인, 독립 바이어스 소자는 VGS 재보정(§8.3). diode 연결 소자는 보정 불필요.
4. 총 W를 크게 바꿔야만 box가 나오면 레이아웃이 조용히 바꾸지 않고 sizing으로 되돌린다(MOD8 수렴 루프). 옛 엔진의 총 W 10~35배 변경은 이 규칙 위반 결함 -- 원인(같은 stack finger_w 통일로 작은 소자 올림 추정)은 새 엔진 설계 전 실측.
5. 결정 묶음: 'finger 폭 W_ref 고정' 삭제, 'finger_w별 DC LUT 슬라이스 생성' 추가.

6. (사용자 지시 2026-10-07) matching 패턴 계산은 옛 엔진 stick_diagram.py의 기존 함수를 그대로 쓴다(새로 만들지 않음): `interdigitate_layout(transistors, base, repeat)`(stick_diagram.py:164, 문헌 표 `INTERDIGITATION_PATTERNS` :94 우선, 표에 안 맞으면 검증된 탐색·최소 crossover 폴백)과 `common_centroid_layout(transistors, n_rows, max_candidates)`(:379, `COMMON_CENTROID_PATTERNS` :110 표 경로 + N-way 회전 exact + 탐색). 차동쌍 -> common_centroid_layout, 그 밖 matching 그룹 -> 두 함수 결과를 box·면적·residual로 비교해 선택. 비정수 비율(예 1:4)도 표 패턴(AABA, AABAA, ABA 등)과 탐색 경로가 처리하므로 별도 규칙을 만들지 않는다. 새 엔진은 이 함수들을 import로 재사용(레지스트리 정본 행 160·165). 확인 항목: COMMON_CENTROID_PATTERNS 주석에 '이미지에서 옮긴 표라 실사용 전 원문 재확인 권장'이 있다 -- 사용 전 원문 대조 1회.

7. (사용자 지시 2026-10-07) 레이아웃 규칙(layout_pipeline_analysis.md §4 (c)) 반영: 차동쌍은 common-centroid 우선. 시도 순서 = (i) 같은 총 W에서 finger_w를 줄여 nf 조정 (ii) W_request로 sizing 재평가 루프를 거친 W 조정. 둘 다 불가능할 때만 interdigitation 완화 허용 -- 완화는 결과에 시도 기록(시도한 nf·W·실패 사유)과 함께 명시 기록(조용한 완화 금지). 나머지 (c) 규칙(총 W 보존 불변식, W 변경은 sizing 요청, 패턴 선택을 행 구성 단계로, 행별 finger_w, 수리 루프 전 쌍 판정)은 사용자 응답 대기.

8. (사용자 지시 2026-10-07) 총 W 보존 허용오차는 상수 없이 계산: 소자별 상한 |dW/W| <= tol_V x (gm/ID) (tol_V = 계획 N3.6 LUT leave-one-out VGS 보간 오차 최댓값; tol_I = tol_V x gm 과 같은 식), 실현 하한 = MANUFACTURINGGRID / (2 x finger_w). 격자는 PDK tech 파일 C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef 의 MANUFACTURINGGRID 를 파싱(코드에 숫자 금지; PDK 경로는 LUT 생성과 같은 PDK 루트 선언에서). 하한 > 상한이면 레이아웃은 다른 finger_w·nf를 고르고, 안 되면 W_request.


## 백로그 (2026-10-07 오케스트레이터 기록, 에이전트 보고에서)
- lut 로더: 모델 파일 경로를 slice meta 절대 경로 `pdk_root`에서 읽음 -> 다른 기계에서 로드 거부. 경로 덮어쓰기 인자 필요.
- lut: bin 블록이 없는 PDK(비-binned 모델)는 빈 bin 지도 -> L 보간 전부 거부. 모델 L 범위 전체를 bin 1개로 취급해야 일반성 원칙에 맞음.
- lut: 폭 슬라이스 W = bin wmin 이 ngspice에서는 아래 W bin(wmax 끝점)으로 계산됨 -> E5·LY2 '특성화 폭 = 그 bin' 전제 재정리.
- lut: 새 열 GMBS·VTH·VDSAT·CDD·CSS·SVG2_* 로더 미소비, 용량 열 부호 보존(CGB 음수 가능) -- log/abs 가정 점검. lut_v2 재생성 뒤.
- lut: tol_V `l_bin_checks`(2점 bin 외부 L 오차) 실제 호출부 미배선 -- lut_v2 검증 중점 데이터로 배선.
- layout: 실 LUT 첫 실행 490 s(슬라이스 20장 tol_v_table) -- 비용 점검(캐시는 memo 재사용 시만).
- layout: graph `row_groups`(stage별 행 그룹), core `pdk_decl`(LayoutPdk 길이·rule_ids) 생산자 없음.
- oracle: legacy_adapter가 off_current_A 미출력 -> 옛 기준선 free verdict 최선 INCOMPLETE. 파일럿 CMRR·PSRR 뷰 pending(MOD5).
- spec: pm_ss_deg(loop)·rout_ss_ohm(output_port) 선언 뷰는 7a design 전까지 pending -- 마일스톤 1 PM 판정 전에 루프 뷰 정의 필요.
- graph CONTRACT 4.5a 문언 보강(test 작성자 지적): gate 넷 정렬이 집합인지 목록인지, '소비 소자' 블록 판정의 diode 범위, '이미 있는 그룹'에 review_needed 포함 여부, 가지치기된 저항 엣지 포함 여부. J14 ratify 때 함께.
- [다음, Hermite 병합 직후] LUT v2(_drafts/engine/lut_v2, 18 L x VS 10, 532 MB) 를 엔진 기본 LUT 로 배선: 옛 12점 세트 대체(배선 원칙), 로더 새 열(GMBS/VTH/VDSAT/CGS/CGB/CDD/CSS/SVG2_*) 소비, tol_V l_bin_checks 를 검증 중점 npz 로 배선, 데이터 저장 위치(저장소 밖 고정 경로 + manifest sha) 결정, 엔진 test 기본 경로 교체.
- [MOD10 배선] 새 엔진 -> 오라클 입력 생산자: rout_ss_ohm -> rout_ohm(C26), feedback_passives_basis=spec_feedback_elements(C12), off_current_A(C23), diffusion(C22), CMRR/PSRR ratio 뷰(C24). layout run_layout 호출(LayoutPdk.from_decl). 이것 없이는 C22~C27 이 옛 어댑터로만 돈다.
- [계획서 반영 대기] MOD6 S-18: 탐색 제약 W >= W_min(PDK difftap.2, c=(W-W_min)/grid), 면적 분해능 b_A = grid x W_min, b_P = sum|V_rail| x max(tol_V x 동작점 gm) (봉인 3 은 gm_bound 유지). seal 7: W4 창 VDsat 항은 넣지 않음(봉인 7 판정으로 충분, SCC 확대 회피). Q7: 소신호 용량은 부호 있는 유한 실수(BSIM4 단자 용량 정의, 오라클과 같음). gm/ID Richardson 차수 3(계획의 Hermite 4 문구 정정). lut 계획 545행 _multilinear 잔존 문구.
- [MOD7 확인] ly.diffusion pd/ps 둘레 규약: BSIM4 perMod=1 에서 pd/ps 는 gate 변 포함 둘레(>= finger_w) 여야 측벽 항이 음수가 안 됨. layout 이 내는 값이 이 규약인지 확인·계약 명시(접합 용량 junction_cap.py 소비자).
- [병합 주의] ng-mod6 와 ng-junction 이 둘 다 assets/sky130_pdk_decl.json 수정(min_finger_w_m / junction 54개) -- 병합 시 둘 다 유지.
- [결정 2026-10-08 오케스트레이터] S-19 ss metric 분해능 정본 = LUT 조회 오차(tol_V)가 소신호 값(gm, gds, gmb, 용량)을 거쳐 metric 으로 전파된 양(1차 감도, MNA 수치오차보다 큰 쪽과 max). metrics 에 MetricResult.resolution 칸 + 감도 계산(같은 LU 재사용) 신설 필요 -- junction 배선 test 병합 뒤 착수.
- [계약 정리] sizing 4.4 ZC_RESISTOR_END 는 로더(hidden_rail)가 먼저 거부해 도달 불가 -> 방어 분기로 명시. S-13 gain 불변은 비트 동일 아님(ss_resistance 변경 시 1 ulp) -> 수치 동일로 문구 정정.


## 세션 중단 인계 (2026-10-08, 사용자 지시 "멈추고 다음 세션에서")
master = d672985 (ng-layout-ratify + tests 병합 완료; 병합 뒤 전체 suite 는 중단돼 미실행 -> 다음 세션 첫 작업으로 재실행).
사용자 결정 5·6·7·9 기록됨(wt/_drafts/user_decisions.md). 남은 결정: 11(면적 예산) -- 사용자가 "더 구체적으로" 요청, 근거 실측(엔진 면적 식·9회로 소자/커패시터·MIM 밀도·W 254 m 사례) 후 회로별 제안 표로 다시 제시.
중단된 작업(모두 kill, worktree 보존 -- 미커밋 변경은 그대로 남음):
- wt/ng-bridge (5 commits ahead, dirty 7): 파이프라인 이름 불일치 수정 중 -> 완료 후 ng-bridge-tests(dd511d5)와 병합.
- wt/ng-search-cond (1 ahead, dirty 13): 전도 하한 + 소자별 theta_bounds spec + R/C 범위 spec 반영 + 9회로 재실행.
- wt/ng-core-perf (dirty 5): fp_of -> value_fp, writer-table API (결정 1 승인).
- wt/ng-match-split (dirty 4): 파일럿 4소자 분리(결정 2) + ngcc {M8,M14} ratio(결정 3) + J-U4 표.
- wt/ng-oracle-singular-tests (dirty 1, untracked 1): loop_probe_singular 독립 test.
- wt/ng-mod6 (untracked 1): 확인 필요.
- 미착수(agent 중단, worktree 변경 없음): CI-10 파일럿 feedback {Cf1,Cf2} 구조 규칙 배선(결정 5), CMFB 루프 PM >= 60 deg(결정 6, 7a 확장 + 오라클 CM 측정), LUT 검증 중점 L (0.165,0.85,1.75,3.25) 재생성(결정 7). 빈 worktree: .claude/worktrees/agent-{a90dfb25,a9e32bbb,afc7da00}* -> 정리 가능.
- 결정 9: 코드 변경 불필요(sizing CONTRACT 4.4 규칙이 이미 drain/gate 양방향).
대기열: topology 정정 Q6/Q7(bias_inputs, source_manifest) -- 사용자 "한꺼번에 반영" 지시 대기.
