---
template: design
version: 1.0
plan_version: 6.0
---

# gain-budget-gmid-sizing -- 42-gap-checklist (gap 분석 기준표)

> **Summary**: `bkit:gap-detector`가 설계(40·41)와 구현을 대조할 때 쓰는 표다. 한 행이 FR·NFR·DEC·설계 항목 하나다. 열은 설계 절, as-built 상태, 증거 위치다.
>
> **기준 시점**: master `f0f0fb8`(2026-10-08). 브랜치에만 있는 것은 `[브랜치]`로 표시하고, 병합 전에는 master 상태로 센다.
>
> **표기**:
> - 상태: OK / DEV / PART / MISS / N/A(원칙·폐기·비활성 기본값)
> - 경로: `E/` = `skills/analog-gmid-design/gmid_engine/`
>
> **재측정 방법**: 이 표의 '증거' 위치를 읽고, 설계 절의 알고리즘·불변식·실패 코드가 코드와 test에 있는지 확인한다. 상태를 바꿀 때는 그 근거(파일:행, test 이름)를 같은 행에 적는다.

## 1. 기능·비기능 요구

| ID | 설계 절 | 상태 | 증거 / 빠진 것 |
|---|---|---|---|
| FR-1 SP1 stage 유도 | 41 §1 | MISS | `E/graph/`에 셀·구동 종류·stage·루프 파일 없음 |
| FR-2 블록 gain 모델 + 매 평가 MNA 잔차 | 41 §2 | MISS | `metrics/CONTRACT.md:13-14` |
| FR-3 보상 먼저 | 40 §3.5, 41 §3 | PART | θ 연속 + MNA 판정 OK(`metrics/CONTRACT.md:555-567`). gm_req·comp_approx_gap·후보 유도 MISS |
| FR-4 `gain_budget_db` 출력, 층 0 조합 front | 41 §5 | MISS | 엔진 grep 0. `E/search/layer0_center.py`는 시작점 하나 |
| FR-5 노드전압 DC 정본, W0~W4, 영역 표기 | 40 §3.7 | OK | `E/sizing/writer_plan.py`, `seal.py:30` |
| FR-6 V/I 상시 검증(봉인 + SPICE) | 40 §3.7, §4 | PART | 봉인 OK. 파이프라인 SPICE 배선은 `[ng-bridge]`만 |
| FR-7 결과 재사용·실패 기록 | 40 §3.9 | PART | S3·실패 캐시 OK(`E/search/archive.py`, `eval_key.py`). 복원 타입 결함 |
| FR-8 탐색 전 달성 불가 | 41 §4 | MISS | `InfeasibleTargetError`는 KCL 충돌에만 쓰임(`E/sizing/current_basis.py:109`) |
| FR-9 명명 규칙·옛 이름 거부 | 40 §3.1 | DEV | `E/authoring/_spec_fields.py:28-33`(정본 이름 거부), topology `direction` 필수 |
| NFR-1 조용한 실패 불가 | 전체 | PART | 실패 규약 OK(`E/core/failure_errors.py`). 결함: 아카이브 문자열 복원 |
| NFR-2 재계산 0, LUT memo 상한 | 40 §7.3 | PART | 필드 캐시 OK. `LutMemo.from_sweep` 호출부 0 |
| NFR-3 IC1~IC11 강제 test | 40 §8 R26 | MISS | `E/tests/contracts/` 없음 |
| NFR-4 결정론 | 전체 | OK | 정렬 순회, `E/core/determinism.py` |
| NFR-5 스펙 맞춤·여유 바닥 | 40 §3.6 | PART | 분해능 OK(`E/metrics/sensitivity.py`). 모델 오차 미측정, 예산 점 MISS |
| NFR-6 기능별 파일 | 40 §1.2 EP-3 | OK | `E/tests/structure/structure_checks.py:312-1114` 규칙 A~I |

## 2. 결정 레지스터 (P N2.1, 폐기 DEC-37~42 제외)

| DEC | 설계 절 | 상태 | 증거 / 빠진 것 |
|---|---|---|---|
| 01 gain-budget-first | 41 | MISS | FR-1·2·4·8 |
| 02 보상 먼저(제약 방향) | 40 §3.5 | PART | gm_req MISS |
| 03 `gain_budget_db` 출력·override | 41 §5.6 | MISS | `SPEC_CONTRACT.md:226-228` |
| 04 소자별 독립 변수(관계로 묶인 것 제외) | 40 §3.2 | PART | 소자별 OK, L 동치류 묶기 없음 |
| 05 전회로 MNA 판정 + 잔차 | 41 §2 | PART | MNA OK, 잔차 MISS |
| 06 θ = 자유 탐색 변수만 | 40 §3.7 | OK | `E/sizing/theta_schema.py` |
| 08 `value_dc_amp` 고정 | 40 §3.7 | OK | `E/sizing/current_basis.py` |
| 09 미러 `equal_vgs` | 40 §3.2 | OK | `E/graph/rel_vgs.py` |
| 10 공유 VGS gain 기준 선택 | 41 §5.4 | MISS | -- |
| 11 역보간 가장 오른쪽 근 | -- | OK | `E/lut/vgs_root.py:17` |
| 12 diode 창 VDsat 바닥 | 40 §3.7 | PART | W4 창 VDsat 항 결정 대기(`sizing/CONTRACT.md:750-757`) |
| 13 적층 diode | 40 §3.7 | PART | `stacked_vsb` 소비자 연기 |
| 14 diode vds 구간 변수 | 40 §3.7 | OK | `E/sizing/writer_plan.py` |
| 15·64 G_vgs KVL 루프 | 40 §3.2 | OK | `E/graph/gvgs_cycles.py:56`, 봉인 8 |
| 16 초기 L knee | 41 §6.4 | MISS | knee grep 0 |
| 17 L 동치류 주인 | 40 §3.2 | DEV | `l_class` proposed(`graph/CONTRACT.md:220`) |
| 18 role 배수 없음 | -- | OK | 구조 test E·I |
| 19 warm start L 동치류 | 41 §5 | PART | 층 0 흡수 MISS |
| 20 `value_from_constraint` | 40 §3.1 | OK | `E/authoring/spec_refs.py` |
| 21 mismatch 5 mV 출처 | 40 §9 Q3 | N/A | 착수 조건 U-17 |
| 22 bisection(기본 비활성) | -- | N/A | 비활성 |
| 23 입력환산 오프셋 | 40 §3.8 | MISS | -- |
| 24 보상 소자 값 엔진 결정 | 40 §3.5 | OK | θ 연속 성분 |
| 25 `parasitic_pm_ss_deg` | 40 §3.8 | OK | `metrics/CONTRACT.md:235` |
| 26 spec 파일 정본 | 40 §3.1 | OK | `E/authoring/spec_load.py` |
| 27 VDS-1 + VDsat | 40 §3.7 | OK | `E/lut/vdsat_query.py:20`, 봉인 7 |
| 28 이름 없는 복구 | -- | OK | `layer0_center` 수리(이름 없음) |
| 29 뷰별 0-1 BFS 방향 | 41 §1.6 | MISS | -- |
| 30 결과 재사용 | 40 §3.9 | PART | 아카이브 타입 결함 |
| 31 노드전압 DC 정본 | 40 §3.7 | OK | -- |
| 32 허용오차·반복 상한 | 40 §3.7 | DEV | tol_I가 격자 최대 gm(`seal_tolerances.py`) |
| 34 샘플 수 식(기본 비활성) | 40 §3.6 | PART | 식 MISS, 샘플 비활성 |
| 35 ports | -- | OK | 9/9 선언 |
| 36 pytest | -- | OK | `E/tests/` |
| 43 SP1 | 41 §1 | MISS | -- |
| 44 회로 해석 공동분석 | 41 §1.10 | N/A | 원칙 |
| 45 할당 층 명세 | 41 §5, 40 §3.6 | PART | 외층만 |
| 46 패키지 구조 | -- | OK | `E/_module_map.py` |
| 47·49·51·67·76·85·86 | -- | N/A | 원칙 |
| 48 물리 정합 상시 게이트 | 40 §3.7 | OK | 봉인 1~9 |
| 50 gain 54 재도출 | 40 §9 Q5 | N/A | 착수 조건 U-19 |
| 52 vsb | -- | OK | 봉인 6 |
| 53 metric 서명 어휘 | 40 §5 | OK | `E/core/metric_signature.py:26`(`cm_loop` 추가는 `[ng-cmfb-pm]`, 계획 갱신 필요) |
| 55 `budget_reference_device` | -- | N/A | 태그 키라 유도 입력이 아님(U-50) |
| 57 전압 이득 stage | 41 §1.6 | MISS | -- |
| 58 블록 속성·출력 구동 | 41 §1.7, 40 §3.8 | MISS | `ls` 없음 |
| 59 규칙 분기 발동표·정지 | 41 §1.10 | MISS | S1 지원 밖 정지만 있음(`graph/CONTRACT.md:352-362`) |
| 60 레일 선언 | 40 §3.1 | OK | `E/authoring/rails.py`, `hidden_rails.py` |
| 61 벌크 기본 규칙 | -- | OK | `E/graph/bulk_default.py`, 봉인 6 |
| 62 데이터만으로 토폴로지 추가 | 40 §1.2 EP-1 | OK | 구조 test E·I |
| 63 버퍼 묶음 R(u) | 41 §1.9 | MISS | -- |
| 65 출력 방향 β/σ/κ | 41 §1.9, 40 §3.8 | MISS | -- |
| 66 `rout_ss_ohm` + 잔차 | 41 §2.2 | PART | 잔차 MISS |
| 68·69 명명·옛 이름 거부 | 40 §3.1 | DEV | FR-9 |
| 70 AC→DC 제약, θ 정의 | 40 §3.7 | PART | 미러 비 강제·슬루 제약 MISS |
| 71 층 0 기둥 조립 | 41 §5 | PART | 가지·기둥 OK(`E/graph/columns.py`). (2)~(8) MISS |
| 72 모델 오차 선언값 | 40 §3.8 | MISS | `metrics/CONTRACT.md:424` |
| 73 기본 경로 = 층 0 + 외층 | 41 §5.7 | PART | 층 0 예산 MISS |
| 74 외층 전회로 판정 | 40 §3.8 | PART | 레지스트리 밖 metric은 notes만(`E/search/search_context.py:84-105`) |
| 75 선언으로 켜는 기능 | -- | OK | `E/authoring/spec_settings.py:34` |
| 77 (전력, 면적) front | 40 §3.6 | PART | front OK, 예산 점 MISS |
| 78 전력 축 정의 | 40 §3.8 | DEV | Σ V·I(`E/search/objectives.py:9`), 기둥 대조 없음 |
| 79 면적 탐색·판정 축 | 40 §7.1, §3.9 | PART | 판정 축 수동소자·재필터 MISS. MIM은 `[ng-area-budget]` |
| 80 면적 눈금·bin | 41 §5.1 | PART | b_A = grid × W_min만 |
| 81 복합 블록 | 41 §1.9 | MISS | -- |
| 82 새 엔진 | -- | OK | `E/` |
| 83 단일 정본 graph | -- | OK | `E/core/graph_snapshot.py` |
| 84 레이아웃 규칙 | 40 §3.9 | PART | MOD8 MISS |
| 87 Hermite 보간 | 40 §8 R25 | DEV | VS 선형, FC 위반 칸 선형 폴백 |
| 88 ln IDu 좌표 | 40 §3.6, §8 R25 | DEV | `vgs_for_current_density` 없음, bounds 조임 |
| 89 레이아웃 뒤 재검증 | 40 §3.9 | PART | LY7 `pending_wiring` |
| 90 SPICE 합격 정의 | 40 §4 | PART | `spice_unverifiable` MISS |
| 91 접합 용량 | 40 §3.9 | PART | layout `ly.diffusion` MISS |
| 92 GB5 방법 | 40 §3.5 | PART | gm_req·gap MISS |
| 93 matching 분류·레이아웃 | 40 §3.2 | PART | 신호 gate 2 조건 빠짐 |
| 94 MOD2 입력 게이트 | 40 §3.1 | DEV | 최상위 `bias_inputs`(사용자 승인) |
| 95 탐색 방법 묶음 | 40 §3.7, §3.9 | PART | ΔA_tie grid², DEC-95 (3) 일부 |
| 96 nqs·mismatch·보고 | 40 §3.8 | MISS | `metrics/CONTRACT.md:14` |

## 3. 설계 항목 (40·41에서 새로 정한 것)

| ID | 항목 | 설계 절 | 상태 | 증거 |
|---|---|---|---|---|
| D-GB0a | spec 신규 필드 `gain_budget_db_override`·`driving_spec`·`symmetry_untie` | 40 §3.1 | MISS | `SPEC_CONTRACT.md:226` |
| D-GB0b | `cm_sense_elements`, `measurement_load` | 40 §3.1 | OK(브랜치) | `[ng-cmfb-pm]`, `[ng-area-budget]` |
| D-GB1a | `structure.json` 로더·status 전이 | 40 §3.2 | MISS | -- |
| D-GB2a~j | SP1 1.1~1.10 | 41 §1 | MISS(1.2 정적만 PART) | `E/graph/ac_ground_static.py` |
| D-GB2k | U-24 `undeclared_loop_constraint` 게이트(CM 루프 예외) | 41 §1.8 | MISS | -- |
| D-GB3 | 결합 변수·기둥↔블록 매핑 | 40 §3.3 | MISS | -- |
| D-GB4a | 블록 gain 상한(인증된 완화) | 41 §4.1 | MISS | 재료 `CurveRow.gm_gds_max` |
| D-GB4b | INFEASIBLE_TARGET 판정 | 41 §4.2 | MISS | -- |
| D-GB4c | 면적 하한 판정 | 41 §4.3 | MISS | -- |
| D-GB4d | 구조·수치 DOF | 41 §4.4 | MISS | -- |
| D-BM | 블록 국소 모델·잔차·결합 잔차 측정 | 41 §2 | MISS | -- |
| D-SG | 감도 게이트 | 40 §3.8 | MISS | `E/metrics/sensitivity.py`는 다른 양 |
| D-L0a~g | 층 0 bin·국소 문제·국소 front·조립·DP·출력·인계 | 41 §5 | MISS | `E/search/layer0_center.py`(대체 대상) |
| D-SIa~f | 출발 구간 6.1~6.6 | 41 §6 | MISS | -- |
| D-LUTc | LUT 곡선 `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve` | 40 §2.3 | MISS | 조합으로만 가능 |
| D-OR1 | C10 지속 진동 = unstable(limit_cycle), FAIL | 40 §4 | DEV | 계약 L42-54, test `test_oracle_c10_stability.py:710` |
| D-OR2 | RHP → 오라클 FAIL | 40 §4 | DEV | `[ng-cmfb-pm]` README |
| D-CM | CM 루프 1·2·3·5 | 40 §5 | OK(브랜치) | `[ng-cmfb-pm]` |
| D-CM4 | 분해능 없음 → 판정 보류(1 dB 대체 제거) | 40 §5 | DEV | `[ng-cmfb-pm] E/search/ss_constraints.py` |
| D-SYa | 완전 정준 라벨링 | 40 §6 | MISS | 1-WL만(`E/sizing/struct_colour.py`) |
| D-SYb | 궤도 θ 묶기 + 해제 | 40 §6 | MISS | -- |
| D-AR1 | 면적 예산 제약·MIM·측정 부하 제외·S-3b | 40 §7.1 | OK(브랜치) | `[ng-area-budget]` 538eeab |
| D-AR2 | 예산을 지키는 출발점·W 타당성 | 40 §7.1 | MISS | -- |
| D-AR3 | 4회로 front 손실 원인 보고 | 40 §7.1 | MISS | -- |
| D-SC | SLSQP 판정 단위 / 풀이 단위 척도화 | 40 §7.2 | DEV | `[ng-area-budget]` 상수 곱 |
| D-BP | 예산 점 풀이 | 40 §3.6 | MISS | `search/CONTRACT.md:537` |
| D-ST | `n_starts`, L-c 분지 | 40 §3.6 | PART | `E/search/eps_sweep.py:4` |
| D-AC | 타입 있는 S3·실패 캐시 레코드 | 40 §3.9 | DEV | `layer0_center._repairable` TypeError |
| D-LY1 | ΔA_tie 식 | 40 §3.9 | DEV | `E/layout/floorplan.py:83` |
| D-LY2 | LY5 즉시 완화 제거 | 40 §3.9 | DEV | `layout/CONTRACT.md:217` |
| D-LY3 | `ly.diffusion` | 40 §3.9 | MISS | `E/layout/_ly_fields.py` |
| D-LY4 | 판정 축 면적에 수동소자 | 40 §3.9 | MISS | `E/layout/floorplan.py` |
| D-M8 | MOD8 수렴·재필터 | 40 §3.9 | MISS | `E/convergence/__init__.py` |
| D-M9 | MOD9 결과 JSON | 40 §3.9 | MISS | `E/report/__init__.py` |
| D-M10 | `run_gmid_design_pipeline` | 40 §3.9 | MISS | `E/pipeline/__init__.py`, `[ng-bridge]` 일부 |
| D-PF1 | `LutMemo.from_sweep` 배선 | 40 §7.3 | PART | 호출부 0 |
| D-PF2 | tol_V 디스크 캐시·정리 | 40 §7.3 | PART(브랜치) | `[ng-tolv-cache]`(`__all__`·test 없음) |
| D-GB7a | L 동치류 L 공유 | 40 §3.2 | DEV | -- |
| D-GB7b | 미러 비율 강제 | 40 §3.7 | MISS | -- |
| D-GB7c | DEC-95 (3) 전체 순서 | 40 §3.7 | PART | -- |
| D-GB7d | W_request 고정 W | 40 §3.7 | MISS | `E/sizing/block_widths.py:9` |
| D-GB8a | `ls`·스윙·ICMR | 40 §3.8 | MISS | -- |
| D-GB8b | nqs·mismatch 보고 | 40 §3.8 | MISS | Pelgrom 계수 선행 |
| D-GB8c | `verified_by`·모델 오차·`spice_unverifiable` | 40 §3.8 | MISS | -- |
| D-T | test 폴더 contracts·regression·oracles·perf | 40 §8 R26 | MISS | `E/tests/` |

## 4. 상태 집계 (master 기준, 브랜치 전용 OK는 PART로 셈)

| 구분 | 행 수 | OK | DEV | PART | MISS | N/A |
|---|---|---|---|---|---|---|
| FR·NFR | 15 | 3 | 1 | 6 | 5 | 0 |
| DEC | 78 | 26 | 7 | 24 | 15 | 6 |
| 설계 항목 | 65 | 0 | 8 | 8 | 49 | 0 |
| **합계** | 158 | 29 | 16 | 38 | 69 | 6 |

설계 항목 열에서 D-GB2a~j는 10행(그중 1.2만 PART), D-L0a~g는 7행, D-SIa~f는 6행으로 센다. 브랜치에만 OK인 D-GB0b, D-CM, D-AR1, D-PF2는 PART로 센다.
