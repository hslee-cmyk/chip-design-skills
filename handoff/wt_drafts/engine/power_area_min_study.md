# 전력·면적 최소화 최소 구현 경로 조사 (2026-10-07, 읽기 전용)

- 기준: 메인 저장소 HEAD `6df4bd7` (수정·git 변경 없음). 행 번호는 이 커밋 기준.
- P = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`, SR = `skills/analog-gmid-design/assets/sizing_recipe.py`, H = `workspaces/run_harness.py`.
- 선행 초안과 겹치는 부분은 다시 재지 않고 인용만 한다: `_drafts/engine_mvp_scope.md` 165~182행(7b front 축소안), `_drafts/engine_current_capability.md` 64~72행(목적함수 실측).

## 1. 계획서 정본 (정확한 행)

| 위치 | 요지(원문 핵심 구절) |
|---|---|
| P 141 N1.1 (f) | "최적화 축은 **전력과 면적 둘**이고 성능 스펙은 제약이다. 산출은 스칼라 최적해 하나가 아니라 그 두 축의 비지배 front이며, 예산이 선언되면 front 안의 한 점을 함께 낸다(DEC-77)." |
| P 248 DEC-54 | "SLSQP가 푸는 것은 **ε-제약으로 스칼라화한 문제 하나**다(한 축을 상한으로 고정하고 다른 축을 최소화한다. 가중합은 쓰지 않는다 -- 볼록성 가정이 없다)." 상태: 부분(multi-start만) |
| P 271 DEC-77 | 성능 스펙은 전부 제약, 최적화는 (전력, 면적) 2목적. "두 축을 가중합 같은 **단일 스칼라 목적으로 합치지 않는다**". 산출 = 비지배 front, 예산 선언 시 front 점 하나 추가, "예산 선언이 없으면 front를 제시하고 정지한다 -- 자동으로 한 점을 고르지 않는다". 두 축 정의가 확정·구현되기 전의 front는 '추정'이며 판정에 쓰지 않는다. 상태: 미구현 |
| P 272 DEC-78 | 전력 축 = "레일에서 들어오는 공급 전류의 합"(DC 정지 전류, `_metric_supply_current` 계열). `sum_current`는 직렬 기둥 중복 계상으로 "front의 순서를 바꾸므로" 목적 축 금지(DF-16, U-10). 기둥 계산과의 차를 기록, metric 이름 후보 `supply_current_dc_ua`/`power_dc_w`. 상태: 미구현(7a에서 교체) |
| P 273 DEC-79 | 면적 (a) 탐색 축 = Σ(W·L) + **선언된** 수동소자 면적(미선언이면 0, 매 실행 보고) (b) 판정·보고 축 = 레이아웃 면적(MOD7 stick_diagram, MOD8 수렴 루프). "보상·부하 수동소자가 있는 회로에서 수동소자 면적 선언이 없으면 그 회로의 front는 ... `review_needed`". "**비지배 판정의 정본은 판정 축이다**". 정본 단위 m². 상태: 미구현(7a 정의·7b 소비) |
| P 274 DEC-80 | 눈금 둘: (i) 레이아웃 격자 분해능(PDK 선언에서 식으로 계산, 용도는 표기·bin 하한뿐) (ii) bin 폭 = max(격자 분해능, 면적 축 모델 오차 = 탐색 축 대 판정 축 실측 차). "(i)만으로 bin을 나누면 안 된다"(0.0021 µm² 대 1041 µm²). 예산 게이트: bin 수가 평가 예산(DEC-34)을 넘으면 bin 폭 2배씩 확대·기록, '해상도 굵음(배수 n)' 표시. 모델 오차 미측정이면 면적 축 판정 '보류'. 상태: 미구현(Phase 4 PDK → 7a 측정 → 7b 소비) |
| P 472 N3.7 외층 | "**2목적의 스칼라화는 ε-제약이다**": front 점마다 "면적을 상한으로 고정하고 전력을 최소화한 뒤 상한을 면적 축 bin 폭(DEC-80 (ii)) 한 칸씩 밀어 다시 푼다". "**반대 방향도 같은 규칙으로 돈다**"(전력 상한, 면적 최소화). "어느 ε에서 나온 해든 다른 해에 지배당하면 버린다. 예산이 선언되면 그 예산을 ε으로 고정한 한 번의 풀이가 최종 해다" |
| P 267 DEC-73 / P 320 GB6 | 기본 경로 = 층 0 기둥 조립 presolve(블록마다 gain bin별 (전력, 면적) 비지배 점) + 외층 SLSQP. 상태: 미구현 |
| P 1008 N6.1 7a | "두 목적 축의 눈금 확정·구현 -- 전력 정의(DEC-78) 교체, 면적 탐색 축·판정 축(DEC-79)과 면적 축 두 눈금 식(DEC-80)" + SPICE 대조(U-11)·모델 오차(DEC-72) |
| P 1009 N6.1 7b | "(전력, 면적) 비지배 front 산출·보고와 외층 ε-제약 스윕(두 방향), 예산 선언 시 front 안 한 점 선택(U-13), MOD8 수렴 루프(LR9)와 면적 탐색 축 대 판정 축 차 기록". 착수 조건: "두 목적 축의 눈금이 7a에서 확정·구현돼 있을 것" |
| P 1026 N6.2 7a 완료 | 전력 축 DEC-78로 계산 + `sum_current` 대비 전후 비교표("동작 변경이므로 ... DEC-40 승인"), 탐색 축·판정 축 같은 실행 기록·차 보고, 두 눈금 판정 기록 |
| P 1027 N6.2 7b 완료 | wall-clock ≤ `wall_clock_budget_s`(파일럿 300 s. "U-13에서 면적 예산을 선언하지 않으면 파일럿 판정은 front 제시·정지와 사용자가 고른 점의 재실행으로") |
| P 1087 U-10 | 확정: DEC-78. 7b 착수 조건 |
| P 1090 U-13 | "파일럿 **면적 예산을 선언할지**와 그 값" -- 7b 착수 조건 |
| P 1113 U-36 | 수동소자 면적 모델(단위 면적/F·/Ω)의 PDK 출처. 선언 전 보상·부하 수동소자 회로 front는 `review_needed` |
| P 158 범위 밖 | 잡음은 목적 축 아님(제약으로만, 2026-09-17 확정) |
| design 문서 | **7a·7b design은 아직 없다.** `docs/02-design/`에 `7a-gain-metric`·`7b-compensation-allocation` 파일 없음(실측 ls). 계획 N9.1 목록에만 있다: P 1165(7a: 전력 정의 반영·비교표, 면적 두 축·차, 두 눈금 식), P 1166(7b: "ε-제약 스윕 절차(두 방향·스윕 폭 = DEC-80·목적값 분해능, 지배 점 제거), (전력, 면적) front 산출·보고 형식, ... 면적 예산 선언 시 한 점 선택(U-13)") |

방법론 근거: `references/gm-id-methodology.md` 412~419·440행(§6.4 "스펙 vs attribute 이분법 ... Attribute: 전력, 면적", "면적 contour를 밀어 접점 → 주어진 전류의 최소 면적. 여러 전류 반복 → 전력-최소면적 관계").

## 2. 현재 코드가 실제로 최적화하는 것

### 2.1 목적함수 경로 (단일 스칼라)
- 목적 선언: 4회로 topology.json 모두 `sizing_roles.objective = {"minimize": "power_uA"}`, `power_uA` = type `sum_current`(실측, 아래 표).
- grid: SR 9222~9230(최종 9245) -- 제약 전부 만족한 점 중 `metrics_result[objective["minimize"]]` 최소 하나만 `best`로 남기고 나머지 실현 가능 점은 버린다.
- slsqp: SR 10792 `_optimize_theta_slsqp` -- 10939~10940 `objective_metric` 하나, 10955 `_objective_fn`, 10963 `_make_constraint_fn`(제약은 `ev["constraints"]` 그대로), 10980 `scipy_constraints`. 결과도 하나(11080~11087).
- slsqp_block_coordinate(SR 11090)도 같은 objective를 읽는다.
- presolve: SR 10580 `presolve_warm_start` -- 10654 `minimize = "minimize" in objective`, `_better_bound`가 objective 감도 부호로 isolated θ를 한쪽 끝으로 고정. 9727~9833 `derive_theta_dependency_graph`가 objective·constraints 이름으로 θ를 coupled/isolated/dead 분류.
- **L θ는 objective를 보지 않는다**: SR 10087 `search_stage_budget_L_warm_start`는 `metric_stage_budget` θ를 "걸린 제약 방향"으로 고른다(gain `>=`면 gm/gds가 큰 쪽 극값). 그리고 SR 10895~10898에서 이 θ들(`warm["stage_budget_L"]`)은 SLSQP 자유변수에서 **빠진다**. 즉 면적의 주 손잡이인 L이 "이득 최대 쪽"으로 고정된 채 SLSQP가 돈다.
- 소자 gm_id도 objective를 보지 않는다: SR 1987 `search_gm_id_for_role`이 역할 규칙(matching = gm_id 최소, gain = gm/gds 최대, balanced = 최소 W, moderate = 중앙, load = gds 최소)으로 고른다.
- 보상 단: SR 8163~8277 `optimize_multistage(objective=stage_objective, w_max=stage_w_max)`. H 119·174·298에서 3회로 모두 `stage_objective: "power"`, `stage_w_max` = 500e-6 / 200e-6 / 500e-6. 즉 보상 단 소자는 "W ≤ stage_w_max 안에서 ID 최소"이며, **면적 결과는 사람이 박은 W 상한 상수가 사실상 정한다**(암묵적 단별 ε-제약).

### 2.2 전력·면적 계산 함수
| 함수 | 위치 | 내용 | 상태 |
|---|---|---|---|
| `_metric_sum_current` | SR 2848 | 소자 ID 단순 합 (현 목적 `power_uA`) | DEC-78이 금지한 정의. 파일럿 231.17 µA 대 공급 전류 82.02 µA(2.82배, capability 초안 2.2) |
| `_metric_supply_current` | SR 4339 | PMOS source 또는 NMOS drain이 레일인 소자의 ID 합 | DEC-78 계열. 레일 = metric spec `supply_nets` 또는 이름 집합 기본값 `("vdd","VDD")`(SR 4361) -- B26-2(극성, 사용자 결정 D1 대기) 사이트(`docs/02-design/specs/20260930-b26-rail-accessor-set.spec.md` 67행). docstring이 스스로 ideal source 전류·레일 저항 전류 미계상, gnd 유출과 3.1% 불일치를 적는다. 파일럿만 metric 선언(`supply_current_uA`), 나머지 3회로 미선언 |
| `_metric_sum_area` | SR 2854 | Σ W·L(m²) | DEC-79 (a)의 트랜지스터 항. 수동소자 항 없음. `area_um2` 선언은 two_stage·파일럿뿐, 목적·제약 어디에도 없음 |
| 레이아웃 면적 | `stick_diagram.py` 8114~8125 `FloorplanResult`(bbox_width·bbox_height·packing_density) | DEC-79 (b) 판정 축 재료. `optimize_full_circuit_budget` 레이아웃 단계(SR 9450 `rebuild_floorplan`)에서 θ* 한 점에만 계산 | 최적화 루프 밖 |
| `_METRIC_UNITS` | SR 5132~ | sum_current A, sum_area m², supply_current A | 단위 정본 있음 |

### 2.3 회로별 결정변수 (실측, topology.json `sizing_roles.theta`)
| 회로 | 자유 θ(bounds lo≠hi) | 수동소자 선언 | 현 실행 상태(capability 초안 2.5) |
|---|---|---|---|
| two_stage_ota | 2 (`L_mirror_M3`, `L_mirror_M5`, metric_stage_budget) | 없음(Cm은 보상 함수가 계산만) | 첫 평가 KVL ValueError |
| current_reuse_telescopic_ota(파일럿) | 22개 중 SLSQP 자유 8 | R·Cc·CL·Cf·Cs 12개 | 완주 146 s, 제약 7/7 |
| folded_cascode | 1 (`Ibg`) | 없음 | 완주, 제약 0건이라 자명해 |
| nmcnr_amplifier | **0** (11개 전부 고정) | 없음(Cm 계산만) | 헤드룸 infeasible |

**함의(추측 아님, 위 실측에서 바로 나옴)**: 외층 θ 공간에서 (전력, 면적) front를 만들어도 nmcnr은 점 1개, folded는 Ibg 하나(전력·면적이 같은 방향으로 커지므로 front가 사실상 한 점일 가능성이 큼 -- 이 부분은 **추측**), two_stage는 L 두 개뿐이다. §6.4가 말하는 절충(단별 gm/ID)은 지금 `stage_objective`/`stage_w_max`와 역할 규칙 안에 숨어 있어 외층이 움직일 수 없다. 이것을 결정변수로 올리는 것이 DEC-04(P 200, "소자마다 독립 결정변수", 미구현)다.

### 2.4 기존 실측 자료 (재사용 가능)
- `skills/analog-gmid-design/assets/tests/probes/probe_area_pareto.py`(120행) + `tests/probe_area_pareto.result.txt`: 파일럿에 `area_um2 <= cap` 제약을 임시 사본에 넣고 SLSQP(1 start, maxiter 40) -- **이미 ε-제약 스윕의 한 방향 프로토타입**이다. 결과: 제약없음 936 µm²·257.98 µA(180 s), cap 1000/900/800 성공(36~111 s, 800에서 230.38 µA), 700 이하 전부 실패.
- 그 표에서 **제약 없는 해(257.98)가 cap 800 해(230.38)에 지배당한다** -- SLSQP 국소해 문제의 실례. ε 스윕에 비지배 필터가 꼭 필요하다는 증거(계획 N3.7 "지배당하면 버린다"와 일치). 단, `power_uA`(sum_current) 기준의 옛 실행이라 수치 자체는 DEC-78 축으로 다시 재야 한다.

## 3. 최소 구현 안 비교

공통 선행(세 안 모두 필요): (1) 목적을 DEC-78 축으로 -- 4회로 `sizing_roles`에 `supply_current` metric 선언 + objective 교체(메타데이터, connectivity 아님) (2) `area_um2`(sum_area)를 4회로 모두 선언 (3) `_metric_supply_current` 레일을 선언에서 받기(B26-1 `meta["rails"]` 재사용, 극성은 B26-2 D1) (4) 기준선 변경 DEC-40 승인. 규모: 코드 10~30행 + JSON 4개(추측 범위).

| | (a) 단일 목적 + 면적 예산 제약 | (b) 가중합 | (c) ε-제약 스윕 → (전력, 면적) 비지배 front (계획서, 축소판) |
|---|---|---|---|
| 내용 | min supply_current, 사용자 선언 시 `area_um2 <= 예산`을 제약으로 추가. 예산 없으면 면적은 보고만 | min (P/P0 + w·A/A0) 한 번 | 끝점 2개(min P, min A) + 사이 ε점 N개(면적 상한 고정 → 전력 최소) + 비지배 필터 + 예산 점(선언 시) |
| 바뀌는 곳 | 공통 선행만 + H 결과 출력(예산 점 기록) | SR 새 metric type 1개(`_METRICS_REGISTRY` 5084) 또는 `_objective_fn`(10955)·grid 9227 수정 | ① `_optimize_theta_slsqp`(10792)에 objective/constraints 덮어쓰기 인자(ev 얕은 복사로 가능, 10881) ② grid 분기(9221~9230) 실현 가능 점 전부 보관 → 비지배 필터(추가 평가 0) ③ 새 `sweep_power_area_front()`(끝점·ε 격자·실패 ε 기록·비지배 필터·예산 점) ④ `search_stage_budget_L_warm_start`(10087)·자유변수 필터(10895~10898): 면적 방향일 때 L θ를 objective 인지로 고르거나 자유변수로 풀기 ⑤ ε 점 사이 평가 캐시 공유(현 `_eval_cache`는 호출마다 지역, 10947) ⑥ 면적 탐색 축에 선언 수동소자 면적 항(U-36) ⑦ H front 표·JSON 출력 ⑧ ε 하나 실패(ValueError)를 그 점의 infeasible로 기록(DF-03 최소판) |
| 대략 줄 수(추측) | 코드 20~40 + JSON 4 | 40~70 + 정규화 상수 2·가중치 1 | 250~350(① 15, ② 25, ③ 120, ④ 40, ⑤ 20, ⑥ 30, ⑦ 40, ⑧ 10) |
| 기간(추측) | 0.5~1일 | 1일 | 3~5일(test 포함) |
| SLSQP 구조 재사용 | 그대로 | `_objective_fn` 한 줄 교체 | 그대로 감싸서 여러 번 호출. 제약 1개 추가가 전부라 SLSQP 내부 수정 거의 없음. probe가 이미 이 방식으로 돌았음 |
| 계획서 DEC와의 차 | front 없음(DEC-77·N1.1 (f) 위반). 예산 선언 시 "그 예산을 ε으로 고정한 한 번의 풀이"(N3.7 끝 문장·U-13)와는 같음 → **(c)의 예산 점 경로만 떼어 낸 부분집합** | DEC-77·DEC-54·N3.7이 **명시적으로 금지**. P0·A0·w는 근거 없는 상수(메모리 '상수를 임의로 만들지 마라' 위반). 비볼록 front 구간을 못 찾음 | 계획서와 같은 절차. 차이: 판정 축 = 탐색 축(DEC-79 (b) 레이아웃 면적·MOD8 미룸), 스윕 간격 = 시간 예산에서 유도(DEC-80 (ii) 모델 오차 미측정 동안. DEC-80의 예산 게이트 방식과 같은 성질), 층 0 presolve(DEC-71/73) 없이 현 presolve + multi-start |
| 면적이 실제로 줄어드는가 | 예산이 활성일 때만. 외층 θ가 적은 3회로는 예산이 통과/실패 판정만 될 가능성(2.3 함의) | 같은 결정변수 한계 | 같은 한계(2.3). 파일럿·two_stage는 의미 있는 front, nmcnr·folded는 퇴화(추측) |
| SPICE 합격 시험과의 관계 | 해 1점 → SPICE 1회 | 해 1점 | front 점 수만큼 SPICE 가능(ngspice .op/.ac는 초 단위라 비용 문제 아님). 어느 점을 합격 대상으로 할지 결정 필요 |

### SPICE 합격 시험과의 공통 관계 (세 안 공통)
1. **전력 축은 SPICE로 직접 검증된다**: DEC-78 공급 전류 = SPICE `.op`의 레일 전압원 전류. 이것이 전력 metric의 `verified_by`(P 498)가 되고, `_metric_supply_current`가 빼먹는 ideal source 전류(SR 4357 docstring (2))와 KCL 잔차(파일럿 4.19 µA)가 그대로 모델 오차로 드러난다.
2. **면적 탐색 축(Σ W·L)은 넷리스트와 같은 W·L이라 SPICE가 검증할 것이 없다.** 레이아웃 면적(DEC-79 (b))도 SPICE 밖이다. 면적 축의 '모델 오차'(DEC-80 (ii))는 SPICE가 아니라 레이아웃 단계에서 나온다.
3. **최소화는 해를 활성 제약 경계로 민다** → 모델 오차만큼 SPICE에서 떨어질 수 있다(일반 성질, 이 엔진에서의 크기는 **추측**). 계획서의 대응은 NFR-5(P 185, 여유 = max(격자 분해능, 모델 오차))·DEC-72다. 따라서 순서가 필요하다: SPICE 대조 1점으로 모델 오차 측정 → 그 오차만큼 제약을 조인 상태로 front/예산 점 계산 → 선택 점 SPICE 합격 판정. 최소화를 넣으면 SPICE 대조(7a U-11)가 **최소화보다 먼저** 돌아야 한다는 뜻이다.

## 4. 추천안

**(c) 축소판을 단계로 쪼개 (a)를 첫 단계로 둔다.** (a)는 (c)의 예산 점 경로와 공통 선행을 그대로 쓰는 부분집합이라 버리는 작업이 없다.

| 단계 | 내용 | 규모(추측) | 산출 |
|---|---|---|---|
| S1 | 공통 선행: DEC-78 전력 목적(supply_current, 4회로) + area_um2 선언 + 레일 선언 소비 + `sum_current` 대비 전후 비교표(P 1026) | 20~40행 + JSON 4 | 올바른 '전력 최소화' 해 |
| S2 | 끝점 2개: min P(현 경로) / min A(objective 교체 + L θ 면적 인지 ④) + grid 회로는 실현 가능 점 전부 보관 → 비지배 필터(추가 평가 0) | 90~120행 | front 양 끝 + grid 회로 front |
| S3 | 사이 ε 점: 면적 상한을 끝점 사이에서 N개, N = `wall_clock_budget_s` / 실측 1회 풀이 시간(새 상수 없음, DEC-80 예산 게이트와 같은 원리, '해상도 굵음' 표기) + 비지배 필터 + 실패 ε 기록 + 평가 캐시 공유 | 120~150행 | 파일럿·two_stage front |
| S4 | 예산 점(U-13 선언 시 ε 고정 1회) + front 표/JSON 출력 | 40~60행 | 합격 시험 대상 점 |

근거:
- DEC-77·DEC-54·N3.7·N1.1 (f)가 정본이고 가중합은 명시 금지 → (b)는 제외.
- ε-제약은 기존 SLSQP에 제약 1개를 더하는 것이 전부라 구조 재사용률이 가장 높고, probe가 이미 같은 방식으로 돌아 실현성이 실측돼 있다.
- grid 회로(two_stage·folded·nmcnr)는 이미 전 격자를 평가하므로 front가 추가 평가 없이 나온다(NFR-2와 일치).
- 단계마다 엔진이 바로 쓰는 결과가 나온다(배선 원칙): S1만으로도 현 목적의 결함(DF-16)이 없어진다.

추천안의 알려진 한계(사실):
- 결정변수 한계(2.3): nmcnr(자유 θ 0)·folded(1)에서는 front가 퇴화한다. 보상 단의 전력-면적 절충은 `stage_w_max` 상수(H 120·175·299)가 정한다.
- 면적 판정 축(레이아웃) 비지배 재필터·MOD8 루프는 빠진다.
- 파일럿 1회 풀이 ≈146 s(3 start) / probe 36~180 s(1 start) → 300 s 예산이면 끝점 2개 정도뿐이다(실측 기반 계산, 사이 점은 예산을 늘리거나 ε 사이 warm start 재사용이 있어야 함 -- 재사용 효과는 **추측**).

## 5. 사용자 결정 항목

| # | 결정 | 기본안(원칙에서) | 왜 사용자 몫인가 |
|---|---|---|---|
| D1 | 면적 예산(U-13)을 회로별로 선언할지·값 | 미선언 → front 제시 후 정지(DEC-77). 합격 시험이 '해 하나'를 요구하면 선언 필요 | 스펙 값은 사용자만 정한다 |
| D2 | 비지배 판정 축을 탐색 축(Σ W·L + 선언 수동소자)으로 축소 | 축소(레이아웃 판정 축·MOD8은 뒤로) | DEC-79 "정본은 판정 축" 변경 |
| D3 | 수동소자 면적 단위(U-36: sky130 MIM 커패시터 단위 면적/F, 저항 단위 면적/Ω) 출처 | 미선언이면 수동소자 회로(파일럿) front = `review_needed` | PDK 출처 선언 |
| D4 | front 계산 시간 예산 `wall_clock_budget_s`(DEC-34 파일럿 300 s)를 front 전체에 쓸지, 늘릴지 | 300 s 유지 시 파일럿은 끝점 2개 | 시간 예산은 사람 선언(DEC-34) |
| D5 | 결정변수 범위: 퇴화 front(nmcnr·folded)를 받아들일지, 보상 단 gm_id(지금은 `stage_objective`·`stage_w_max` 상수)를 θ로 올릴지(DEC-04 일부, 추가 100~200행 추측) | 1개월 목표면 받아들이고 한계로 보고 | 범위·일정 결정 |
| D6 | 합격 시험에서 SPICE를 요구할 front 점(전 점 / 양 끝 + 예산 점 / 예산 점만) | 양 끝 + 예산 점 | 합격 정의 |
| D7 | 순서: SPICE 모델 오차 측정을 최소화보다 먼저 두고 제약을 그만큼 조이는 것(NFR-5·DEC-72) | 그렇게 한다 | 7a·7b 순서와 합격 절차에 걸림 |
| D8 | 전력 표기: 전류(A, DEC-78) 유지 vs 전력(W = V·I). 단일 공급이면 순서가 같다 | 전류 유지, 보고에 W 병기 | metric 이름(DEC-68) |
| D9 | 4회로 objective·기준선이 바뀌는 동작 변경 승인(DEC-40, P 1026) | 승인 요청 | 기준선 변경은 승인 사항 |
| D10 | `_metric_supply_current` 레일 극성(B26-2 D1)과의 순서 | S1에서 레일 넷은 선언 소비, 극성 판정(PMOS source/NMOS drain)은 현 규칙 유지 | 이미 대기 중인 D1과 연결 |
