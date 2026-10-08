---
template: design
version: 1.1
plan_version: 6.0
---

# gain-budget-gmid-sizing -- 41-gain-budget Design Document

> **Summary**: gain-budget-first 흐름을 설계한다(계획 N1.1, FR-1·FR-2·FR-4·FR-8, DEC-03·05·43·57·59·63·65·71·73·77·81). 다루는 범위는 다섯 가지다.
> - connectivity에서 signal stage를 유도한다(SP1).
> - 블록 국소 소신호 모델로 stage gain을 정의하고, 평가마다 전회로 MNA와의 잔차를 기록한다.
> - LUT 격자 상한으로 탐색 전에 달성 가능성을 판정한다.
> - 층 0에서 블록 gain bin별 (전력, 면적) 비지배 점을 만들고, 조합 DP로 예산 조합 front와 `gain_budget_db`를 낸다. 이 결과를 외층 SLSQP와 잇는다.
> - 스펙에서 gm/ID·L·전류 출발 구간을 topology와 무관하게 유도한다.
>
> **Date**: 2026-10-08 · **Status**: v1.1 -- design-validator 지적 C1~C4·H1~H8·M1~M14·L1~L8 반영. 색인과 표기는 [40-engine](gain-budget-gmid-sizing.40-engine.design.md)을 따른다(`E/`, OK/DEV/PART/MISS). as-built 기준은 master `004b7d2`다.

**as-built 요약**: 이 문서의 설계 항목은 모두 MISS다. 쓸 수 있는 재료는 다음이 전부다.
- LUT 곡선 표의 격자 최대 gm/gds: `CurveRow.gm_gds_max`(`E/lut/lut_types.py:384,396`)
- LUT 곡선 검사: `curve_report`, `DcSlice.hermite_fc`(`E/lut/lut_set.py:124-173`)
- 전회로 MNA: `E/metrics/mna_build.py:47`, `mna_solve.py:42`
- pencil 극점: `E/metrics/pencil_roots.py`
- 외층 ε-제약 front: `E/search/eps_sweep.py`, `pareto.py`
- 최소형 층 0: `E/search/layer0_center.py`(시작점 하나만 만든다)

---

## 0. 계산 순서 DAG (S0당 한 번, 순환 없음)

P N3.1의 'GB0~GB4는 S0 지문마다 한 번'에 맞춘 순서다. 앞 단계는 뒤 단계 결과를 읽지 않는다.

```
[단계 A -- 봉인 평가 없이, S0당 1회]
 A1 GB0 load            : spec, topology, S0
 A2 GB1 build_s1        : S1
 A3 GB2 build_s1v       : S1v (뷰·셀·stage·블록·극점 노드·루프)        §1
 A4 GB3 coupling_vars   : y 목록, 기둥↔블록 매핑                        40 §3.3
 A5 GB4a curve_checks   : LUT 칸 분류(역산 허용/격자 전용/거부)          §4.1
 A6 GB4b block_bounds   : A_i,max 표(LUT 격자 전수, 인증 또는 미상)      §4.2
 A7 GB4c verdict        : Σ A_i,max 판정, 구조 DOF, 인증된 면적 하한     §4.3~4.5
 A8 start_intervals     : gm/ID·L·I 출발 구간(A3·A6을 읽는다)            §6
[단계 B -- 봉인 평가가 필요, S0당 1회, 평가 커널 컨텍스트 생성 뒤]
 B1 residual_probe      : 결합 잔차 분포 r̂ (표본 = dof_rank_sample_count) §2.4
 B2 dof_numeric         : 수치 rank (B1 표본 재사용)                     §4.5
 B3 layer0_budget       : 국소 front → 조합 DP → 조립(A6·A8·B1을 읽는다) §5
[단계 C -- 탐색]
 C1 find_front(외층 ε-제약) → MOD8 → 오라클                              40 §3.6, §3.9, §4
```

순환을 끊는 규칙은 넷이다.
- 단계 A는 봉인된 값을 읽지 않는다.
- A7 판정은 r̂를 쓰지 않는다. A7의 면적 하한도 A8 출발값을 쓰지 않는다(§4.4).
- A8이 읽는 A_i,max가 미상이면, 그 블록의 이득 L 하한만 비활성으로 둔다(§6.4).
- 단계 B의 결과는 단계 A로 되돌아가지 않는다.

**미측정 값의 처리 규칙(하나로 통일)**: 모델 오차, r̂, 분해능처럼 아직 재지 않은 값은 '보류'로 둔다. 보류 값을 쓰는 결정은 거부·정지를 하지 않는다. 그 값을 거친 산출물(front, 순서, bin)에는 '추정'을 표시한다(DEC-72·77).

---

## 1. FR-1 -- signal stage 유도 SP1 (GB2, MOD3)

**목적**: connectivity만으로 여기 뷰마다 셀, 구동 종류, stage, 블록, 극점 노드, 루프를 유도한다. declared와 다르면 `review_needed`로 올린다(DEC-43·44). 규칙 정본은 P N3.2 1~9와 용어집이다. 이 절은 그 규칙을 실행 순서와 알고리즘으로 정한다(WP-21 코드 부류).

**출력**: S1v의 필드 `views[]`이다. 각 뷰는 `{kind, excite, sense, ac_ground, signal_nets, forward_nets, cells{dev: CS|CG|CD|pass|diode_load|off}, drive_kind{net}, dist{net}, blocks[], pole_nodes[], loops[], cuts[]}`를 갖는다. 여기에 `rule_branch_coverage`와 `review_needed[]`가 붙는다.

**파일**(`E/graph/`, 계산 블록 하나 = 파일 하나):

| 파일 | 내용 |
|---|---|
| `views.py` | 뷰 수집 |
| `ac_ground_view.py` | 뷰별 교류접지 |
| `signal_reach.py` | 도달성·순방향 집합 |
| `cells.py` | 셀 분류 |
| `drive_kind.py` | 입력 노드 구동 종류 |
| `stage_bfs.py` | 0-1 BFS, stage 경계 |
| `blocks.py` | 블록 구성 |
| `pole_nodes.py` | 극점 노드 목록 |
| `loops.py`, `loop_classify.py`, `loop_cuts.py`, `polarity.py` | 루프 탐지·분류·끊는 점·극성 |
| `buffer_bundles.py`, `output_direction.py`, `composite_blocks.py` | 버퍼 묶음, 출력 방향, 복합 블록 |
| `declared_compare.py`, `rule_coverage.py` | declared 대조, 규칙 분기 발동표 |
| `s1v_build.py` | 진입점 |

### 1.1 뷰 수집

- **전달 뷰**: 선언된 metric의 `(ac_excite, sense)`마다 하나씩 만든다.
- **기본 전달 뷰**: metric 선언이 없으면 `ports` role에서 만든다. 두 입력 포트가 자기동형 궤도(40 §6)에서 서로 대응하면 기모드 여기 하나, 아니면 입력마다 단일 여기 하나다.
- **루프 뷰**: §1.8의 (3) 루프마다 하나씩 만든다.
- 전류 입력·트랜스임피던스 뷰는 DEC-59에 따라 정지한다.
- `(excite, sense)` 키는 as-built `E/authoring/spec_views.py:61,110`의 것을 그대로 쓴다.

### 1.2 뷰별 교류접지

정적 집합 (1) 레일과 (2) gate 전용 넷은 as-built가 이미 계산한다(`E/graph/ac_ground_static.py`).

**(4) 바이어스 종속 넷 술어**(P N3.2-1 (0)~(iii)): 넷 b에 대해 다음을 확인한다.
- 사슬 찾기: b를 제거한 신호 그래프에서 source→drain 역방향 BFS로 사슬을 찾는다. 교류접지와 b는 지나지 않는다.
- 판정: 그 뷰의 여기가 사슬의 출발 신호 노드를 움직이지 않으면 b는 교류접지다.
- 움직이는 경우: b는 교류접지가 아니고, 그 사슬이 만드는 폐경로를 (3) 루프로 등록한다.

이상 전압원 (3)은 as-built처럼 정지한다(발동 0, DEC-76). 실측 기대는 파일럿 2건, 나머지 8회로 무동작이다(J1).

### 1.3 도달성과 순방향 집합

최소 고정점으로 신호 넷을 모은다. 여기 포트에서 시작해 다음 세 규칙을 반복한다. 교류접지 넷과 제거된 넷은 넣지 않는다.
- (a) 신호 넷을 gate로 받는 소자의 drain·source를 넣는다.
- (b) 신호 넷을 source로 받는 소자의 drain을 넣는다.
- (c) 신호 넷에 붙은 2단자 수동소자의 반대쪽 단자를 넣는다.

**순방향 집합 F**는 이 그래프에서 여기 포트로부터 도달하고 출력 포트로 역도달하는 넷의 집합이다.

### 1.4 셀 분류

1. **gate = drain**이면 `diode_load`다.
2. **gate가 신호 넷**인 경우:
   - drain이 교류접지면 CD, source가 교류접지면 CS다.
   - 둘 다 아니면 source가 F 위의 다른 신호 셀 입력이나 출력 포트에 닿는지 본다. 닿으면 `review_needed`, 아니면 CS(degeneration)다.
   - 상대 셀도 모호하면 그 쌍을 함께 `review_needed`로 올린다.
3. **gate가 신호 경로 밖**인 경우:
   - 역병렬 pass 묶음 조건을 만족하면 pass다.
   - 아니고 source가 신호 넷이면 CG다.
   - 그 밖은 `off`다.
   - 소자가 셋 이상이거나 방향이 섞인 묶음은 `review_needed`다.

대조표 셀 수는 출력이 F에 드는 셀만 센다. 빠진 셀은 '순방향 밖 셀' 열에 적는다.

### 1.5 입력 노드 구동 종류

1. 신호가 drain으로 들어오면 전류 구동이다. source, 입력 포트, 앞 stage 출력으로 들어오면 전압 구동이다.
2. 저항으로만 들어오면 반대쪽 노드의 종류를 상속하고 '값 의존'으로 표시한다. 상속이 순환하면 `review_needed`다.
3. 전류 진입 노드는 신호가 나가는 쪽으로 가른다.
   - gate로만 나가면 전압 구동이다.
   - 채널로만 나가면 전류 구동이다.
   - 둘 다면 gate 쪽 셀의 출력이 F 위에 있을 때 전압 구동(stage 경계)이다. 그렇지 않으면 그 노드는 **tap**이다. tap은 채널 쪽만 순방향을 잇는 노드다. 구동 종류는 '전류 구동'으로 기록하고, gate로 갈라진 셀은 규칙 9 (a)(`기록만`, DEC-59 정지)로 둔다.
4. **혼재**(source 진입과 다른 소자 drain이 한 노드에 있음)는 drain 쪽 소자의 DC 역할로 가른다.
   - 바이어스 전류원이면 전압 구동이다.
   - 신호 소자면 `review_needed`다.
   - 구조로 못 가르는 그룹이면 J 판정을 기다린다.
5. pass 묶음을 지난 노드는 반대편 노드의 종류를 상속한다.

### 1.6 0-1 BFS와 stage 경계

**엣지 비용**:

| 엣지 | 비용 | 비고 |
|---|---|---|
| gate→drain | 1 | gate가 diode 단자면 0 |
| source→drain, gate→source | 0 | source가 전압 구동인 CG의 source→drain은 1 |
| 수동소자 | 0 | 열린 항목 ⑬ |

**stage 시작 셀**: 입력이 전압 구동인 CS, 그리고 source가 전압 구동인 CG다. 단 DC 역할이 바이어스 전류원인 셀은 stage를 시작하지 않는다(K8).

**적용 순서**(⑧): 규칙 9 (c)의 diode 미러 갈래를 stage 시작보다 먼저 적용한다. 미러 입력 노드는 블록 내부 노드이므로, 그 노드를 gate로 읽는 셀은 stage를 시작하지 않는다. 근거는 P N3.2-5와 J2 기본안이다.

### 1.7 블록, 출력노드, 임피던스 등급, 극점 노드

1. **블록 열기**: 시작 셀마다 블록을 연다. 캐스코드 사슬, 미러 연장, pass 묶음을 따라가 다음 시작 셀 입력이나 출력 포트에 닿은 노드가 출력노드다.
2. **병렬 합류**: P N3.7의 ①②③ 순서로 판정한다. 세 갈래 이상이면 입력 쌍마다 ①을 적용하고 union-find로 묶는다(⑪).
3. **차동 블록**(⑩·M5): 같은 stage 번호의 반쪽 블록 둘이 넷을 공유하면 하나로 합친다.
   - 블록 키: 두 출력노드 넷 이름을 정렬해 `|`로 잇는다.
   - 여기: 두 입력 넷에 ±½를 건다.
   - 출력: 두 출력노드 전압 차다.
   - 단일 출력 블록의 키는 출력노드 넷 이름이다.
   - 노드 배타성은 합친 뒤에 검사한다.
4. **임피던스 등급**:
   - 낮음: gate가 교류접지인 source 단자나 diode가 붙은 노드.
   - 높음: drain, gate, 커패시터 단자만 붙은 노드.
   - 값 의존: 낮음 단자 없이 저항이 붙은 노드.
   - 규칙 9 (c)는 블록 구성 뒤, 출력노드가 F 위에 있을 때만 본다.
5. **극점 노드 목록**: 교류접지가 아닌 모든 노드다. 노드마다 소속 블록, 등급, 종류를 붙인다.
6. **DEC-59 정지 집계**: 비축약 뷰에서 센다(⑨). 축약 뷰와 비축약 뷰의 결과가 같아야 한다.

### 1.8 루프

**탐지**: P N3.2-2 방향 그래프에서 단순 사이클을 전수 열거한다(Johnson, 정렬된 노드 순서). 세지 않는 것은 수동소자 왕복, pass 묶음 내부 왕복, 자기 엣지다.

**열거 상한**: 단계 A 예산 N_A(§5.8)다. 넘으면 `StructureUnresolvedError(unsupported_rule_branch, reason=cycle_enumeration_over_budget)`로 정지한다(M14).

**분류**: (1.5) 바이어스 SCC → (2) Miller → (3-a) → (3-b) → (4) 순서로 판정한다. 정의는 P N3.2-2를 따른다. (2)와 (3-b)를 함께 만족하면 두 분류를 모두 단다. (3-b)는 배타 조건 (가)·(나)를 적용한다.

**끊는 점**: 루프 위에 gate 엣지가 있는 CS 셀의 gate다.
- 후보가 여럿이면 복귀 경로 다음 첫 gate를 고른다.
- 복귀 구간이 여럿이면, 이름 정렬로 첫 노드에서 시작한 사이클 표현의 가장 이른 구간을 쓴다.
- 후보가 없으면 `review_needed`다.

**극성**: 셀 부호의 곱이다(CS −, 그 밖 +). 커패시터만 지나는 경로는 `review_needed`다.

**U-24 게이트와 CM 루프의 구조적 대응**(H5): 루프 뷰 ℓ의 사이클 노드 집합이 **선언된 차동 출력 포트쌍(role p/n)의 두 넷을 모두** 포함하면, ℓ을 '포트쌍 CM 루프 대응'으로 본다.
- 근거: 포트쌍에 같은 부호로 주입하면 두 출력 넷을 함께 지나는 모든 CM 되먹임 경로가 한 번에 열린다.
- 그 ℓ의 안정도 metric은 40 §5의 `pm_cm_ss_deg`다.
- U-24 정지 대신 사용자 결정(2026-10-08)을 따른다. 제약이 미선언이면 T_cm만 보고하고, T_cm(0) > 1이면 경고 `cm_loop_unconstrained`를 낸다.
- 그 밖의 루프 뷰는 안정도 제약이 미선언이면 GB2 출구에서 `StructureUnresolvedError(undeclared_loop_constraint)`로 정지한다.

### 1.9 버퍼 묶음, 출력 방향, 복합 블록

- **R(u)**(DEC-63): CD 병렬 합류(②)에서는 §1.7의 ①보다 먼저 판정한다.
- **출력 방향**(DEC-65): β/σ/κ와 push-pull·class-A 구분은 MOD3에서 구조로 판정한다. 값은 40 §3.8 `ls`가 낸다.
- **복합 블록**(DEC-81): ②의 합류 노드가 전류 구동이거나 블록 출력노드면 묶는다. 묶은 결과 DAG는 사슬이어야 한다.
  - 묶음 크기 Π가 N_A를 넘으면 `unsupported_rule_branch`다.
  - 경로별 기여는 §2에서 계산한다(⑭).

### 1.10 declared 대조와 발동표

- **declared 대조**: declared stage(`compensation.stage_devices`, `gain_stages_sum.stages`, `vertical_stack_id`)는 `declared` 엣지로만 싣고 유도 결과와 대조한다. 불일치면 `review_needed`다. 유도 입력으로는 쓰지 않는다(U-50).
- **발동표**: `runs/<run_id>/rule_branch_coverage.json`이다.
  - 행: 뷰 × 분기.
  - 열: 발동 회로, 검증 발동 회로, 속성, 순방향 밖 셀.
  - 검증 발동이 0인 분기를 타면 탐색 전에 exit 2로 정지한다.

### 1.11 6a 열린 항목 결정

| 항목 | 결정 |
|---|---|
| ① | as-built `gvgs_cycles` |
| ② | R(u)를 먼저 판정 |
| ③ | 구조로 못 가르는 DC 역할 그룹은 잠정 신호 소자로 두고, 블록에 `review_needed`를 붙여 GB4 앞에서 정지 |
| ④ | diode source 진입은 전압 구동으로 보고, diode 자체는 `diode_load` |
| ⑤ | 40 §3.5 |
| ⑧ | §1.6 |
| ⑨·⑩·⑪ | §1.7 |
| ⑫ | as-built |
| ⑬ | §1.6 |
| ⑭ | §1.9 |
| ⑥ | 구현 출력으로 갱신 |
| ⑮ | 사용자(40 §9 Q7) |

**불변식**: 같은 입력이면 같은 S1v다. 이름을 전단사로 바꾸면 결과는 그 사상으로만 바뀐다. 축약 뷰와 비축약 뷰의 결과가 같다.

**실패**: `StructureUnresolvedError`.

**상태**: MISS. 부분 대리물은 `E/authoring/_feedback_cuts.py:11`, `E/metrics/loop_cut.py:60`, `[ng-cmfb-pm] E/authoring/cm_partition.py`, `E/graph/matching_groups.py:202`다.

---

## 2. FR-2 -- 블록 gain 모델과 MNA 잔차 (MOD5)

### 2.1 정의

**블록 국소 모델**(P N3.8):
- 미지수는 블록 노드 집합이다.
- 입력 넷에 단위 전압을 건다. 차동 블록은 ±½다(§1.7-3).
- 블록 밖 노드는 교류접지로 두거나, 다음 블록의 입력 어드미턴스로 고정한다.
- 스탬프 값은 봉인 스냅샷의 `ss`에서 가져온다.

**산출량**:
- 블록 gain = 20·log10|V(out)/V(in)| (ω → 0).
- Z_out = 입력을 교류접지로 두고 출력에 단위 전류를 넣었을 때의 출력 전압.
- 복합 블록의 경로별 기여 = 다른 경로 입력 소자의 gm을 0으로 둔 국소 해(부호 포함).

### 2.2 잔차

평가마다 다음을 S2 `ss`와 S3 evals 요약에 쓴다.
- `gain_residual_db = gain_ss_db(전회로) − Σ 블록 gain`
- `ss.block_gain{key: {gain_db, zout_ohm, contributions}}`
- `ss.rout_residual_ohm`(DEC-66)

블록을 가로지르는 되먹임 수동소자가 있으면 그 블록 gain은 '분해값'으로만 표시한다.

### 2.3 구현

- 블록 노드 부분집합에서 as-built 스탬프 함수(`mos_stamps`, `stamp_two_terminal`)로 (G_b, C_b)를 조립한다.
- ω → 0 극한은 `solve_dc_limit` 방식으로 푼다.
- 필드 캐시 키는 블록 키와 `ss` 입력 버전이다.
- 파일은 `E/metrics/block_model.py`, `block_residual.py`다.

### 2.4 결합 잔차 측정 (단계 B1)

- 표본: `dof_rank_sample_count`개의 준난수 θ다.
- 계산: 표본마다 평가 커널을 돌리고, 봉인을 통과한 점에서 잔차를 잰다.
- 산출: r̂ = 중앙값, r̂_spread = 최대 − 최소.
- 쓰임: 층 0 조합 순서에만 쓴다(§5.6). 상한이 보장되지 않으므로 판정에는 쓰지 않는다(M2).

**상태**: MISS.

---

## 3. FR-3 연계

- 보상 `gm_req`(MNA 1-D 근)는 외층 판정에서 제약으로 쓴다(40 §3.5).
- 층 0에서는 §6.5 매크로 출발값으로 보상 수동소자 값을 고정한다.
- 조립점에서 `comp_approx_gap`을 기록한다.

---

## 4. FR-8 -- 탐색 전 달성 불가 판정 (GB4, MOD5)

**파일**: `E/metrics/achievability.py`(진입점), `curve_checks.py`, `block_gain_bound.py`, `dof_report.py`, `area_lower_bound.py`.

### 4.1 LUT 곡선 검사에서 해법으로 (P N3.7)

as-built `curve_report`와 `hermite_fc`의 칸 분류를 소비해, 칸마다 해법을 정한다.

| 칸 분류 | 해법 |
|---|---|
| 단조 | 역산 허용(`vgs_for_gm_id`, `vgs_for_current_density`) |
| 비단조 또는 Fritsch–Carlson 위반 | 그 칸은 격자 전수만 쓴다. 역산은 `lut_hermite_nonmonotone_cell`로 실패시킨다. 순방향 조회는 선형 폴백을 허용하되 사유를 기록한다(DEC-87) |
| 단위 불일치 | 로드 거부(`SchemaRejectedError`) |

산출은 `CurveCheck{kind, w_key, L, VDS, cell, method}`다. §5.3의 역산이 이것을 읽는다.

### 4.2 블록 gain 상한 A_i,max (P N3.7 격자 전수, C2)

**정의**: A_i,max = 블록 i 국소 모델 gain의 최댓값이다. 최댓값은 블록 결정 축의 격자 곱 전체에서 찾는다.

**축**: 등식으로 묶인 것(궤도, L 동치류, `equal_vgs`)은 축 하나로 센다.

| 축 | 격자 |
|---|---|
| 소자 그룹별 gm/ID | LUT gm/ID 격자 |
| L 동치류별 L | LUT L 점, 그리고 bin 안 L 구간의 내부 극값. 내부 극값이 양끝을 넘으면 그 점을 추가한다 |
| 기둥 VDS | W4 창 안의 LUT VDS 격자 |
| y | K1~K4 이산 격자 |
| 블록 안 저항값 | spec θ 범위의 양끝과, LUT 격자 간격으로 만든 로그 격자 |
| 미러 비 θ | 범위 양끝 |
| 전류 배율 | 블록에 저항이 있을 때만 둔다. 저항이 있으면 gain이 전류에 대해 0차 동차가 아니기 때문이다. 격자는 전류 상자 [I_off, I_max] 위에서 LUT ID 격자를 w_m으로 환산한 것이다 |

**계산**:
- 행마다 봉인 없이 블록 국소 모델을 풀어 gain을 구한다.
- 행 조건 (gm, ID, L, VDS, R, 비)과 함께 S0 지문 필드에 저장한다(행 단위 memo).
- 소자 파라미터는 LUT memo에서 한 번만 조회한다.

**예산 게이트**: 격자 곱 Π가 단계 A 예산 N_A(§5.8)를 넘으면 상한을 **'미상'**으로 두고 판정에 쓰지 않는다. 격자를 줄이지 않는 이유는, 줄인 격자의 최댓값은 상한이 아니기 때문이다. 이 처리는 P N3.7의 "LUT·구조만으로 상한을 계산할 수 없는 제약은 상한 미상"과 같다.

**분해능**: b_GB4,i = 최대 행과 그 격자 이웃 행들 사이 gain 차의 최댓값이다.

**GB5 재사용**: 보상 gm 요구로 다시 판정할 때는 이 표에서 gm 조건을 만족하는 행만 거른다. LUT 격자를 다시 돌지 않는다.

**버퍼 블록**: 같은 방법을 쓴다. 상한은 0 dB 이하다.

### 4.3 gain 판정

다음 두 조건이 모두 맞으면 `InfeasibleTargetError`(exit 3)로 정지한다.
- 모든 블록 상한이 인증되었다.
- Σ_i (A_i,max + b_GB4,i) < G_target이다.

r̂와 모델 오차는 쓰지 않는다. 블록 하나라도 상한이 미상이면 판정하지 않고 보고만 한다.

산출은 `achievability{blocks[{key, A_max_db, b_db, status: certified|unknown, row_condition}], sum_db, target_db, verdict}`다.

### 4.4 면적 하한 (결정 11, 인증된 하한만, C1)

A_lb = Σ_k I_k,cert · L_min,k² / IDu_max,k + Σ_c C_c,min / ρ_MIM

| 항 | 뜻 |
|---|---|
| I_k,cert | 선언된 이상 전류원(`value_dc_amp`)과 KCL로 값이 고정된 가지 전류. 그 밖의 소자는 0 |
| L_min,k | LUT 최소 L 점(PDK 최소 L 이상) |
| IDu_max,k | LUT 최대 전류밀도 |
| C_c,min | 값이 선언되지 않은 보상 커패시터의 spec θ 하한, 선언값이 있으면 그 값. 측정 부하는 뺀다 |
| ρ_MIM | PDK 선언 `mim_cap_density_f_per_m2` |

- A_lb > A_budget + b_A이면 INFEASIBLE_TARGET(`area_budget_below_lower_bound`)로 정지한다.
- 출발값으로 계산한 면적 추정 A_est는 보고만 한다.

### 4.5 DOF

**구조 rank**(단계 A):
- 변수: 노드전압, writer ln IDu, L 동치류 L, θ 전류, DC 경로 저항.
- 등식: diode, `equal_vgs`, `budget_ref`, `stacked_vsb`, `kvl_branch`, KCL.
- 방법: 변수와 등식의 이분 매칭으로 rank를 구한다.
- 판정: 매칭되지 않는 등식이 있으면 `overconstrained`이고 INFEASIBLE_TARGET이다. 남는 변수가 있으면 `underdetermined` 목록을 낸다.

**수치 rank**(단계 B2):
- B1 표본에서 등식 잔차의 FD Jacobian을 만든다. 스텝은 LUT 격자 간격이다.
- `numpy.linalg.matrix_rank`로 rank를 구한다.
- 이 항목을 범위에 넣을지는 40 §8 R3(사용자)이 정한다.

산출은 `DofReport{status, structural_rank, numeric_ranks[], competing_pairs}`다.

**상태**: 4.1은 PART(분류는 있고 매핑이 없다). 4.2~4.5는 MISS.

---

## 5. FR-4 -- 층 0 gain 예산 조합 front와 `gain_budget_db` (MOD6)

정본은 DEC-71 (1)~(8), DEC-73, DEC-77, DEC-03이다.

**파일**(`E/search/`): `layer0_budget.py`, `gain_bins.py`, `local_candidates.py`, `local_front.py`, `combo_dp.py`, `assembly.py`, `budget_override.py`, `eval_budget.py`.

### 5.1 활성 조건

**활성**: 다음 셋이 모두 맞을 때 층 0 gain 예산을 돌린다.
- gain 제약 `gain_ss_db >= G`가 있다.
- 그 전달 뷰에 이득 블록이 하나 이상 있다.
- `review_needed`가 없다.

**이득 블록 없이 버퍼 블록만 있는 경우**: 선언된 `rout_ss_ohm`을 국소 AC 제약으로 쓴다(DEC-71 (3)).

**gain 제약도 rout 제약도 없는 경우**(H2):
- 문제: 국소 문제에 AC 제약이 없어 해가 최소 크기로 자명해진다.
- 계획 충돌: DEC-71 (3)은 이런 회로를 '층 0 무동작'으로 보고하고 **사이징 대상에서 뺀다**고 정한다. 이는 DEC-85(9회로 전부 합격)와 충돌한다. 사용자 질문으로 올린다(40 §9 Q5b).
- 결정 전 처리: 층 0을 끄고 '층 0 무동작'으로 보고한다. 시작점은 출발 구간(§6)에서 만들고, 결과는 '성능 판정 보류'로 보고한다.

### 5.2 bin

- **gain bin 폭**: w_g = max(b_gain, `model_error_gain_ss_db`)이다.
  - b_gain은 `MetricResult.resolution`이다. 단계 B의 첫 봉인 평가에서 잰다.
  - 모델 오차가 미측정이면 b_gain만 쓰고 결과를 '추정'으로 표시한다.
- **면적 bin 폭**: DEC-80 (ii)를 따른다.
- **bin 번호**: floor(gain / w_g)로 평가된 후보에서 정한다. 따라서 A_i,min을 미리 가정하지 않고(C3), A_i,max가 미상이어도 bin을 만들 수 있다(H3).

### 5.3 블록 국소 후보 생성 (C3)

**범위**: 블록 소자를 덮는 기둥 집합이다. 바이어스 기둥도 같은 절차를 따른다.

**축과 후보**:

| 축 | 후보 |
|---|---|
| 소자 그룹별 gm/ID | §6 출발 구간 안의 LUT gm/ID 격자점. 구간이 충돌이면 양 끝점 |
| L 동치류별 L | §6 L 구간 안의 LUT L 점(bin 선택). bin 안 값은 아래 (b)의 역산이 정한다 |
| VDS | 축이 아니다. 아래 (c)가 정한다 |
| 전류 | 저항이 없는 블록에서는 축이 아니다. 전류 = max(블록 gm 요구 / gm/ID(§6.5), 봉인 9 전도 하한). 저항이 있으면 §4.2처럼 전류 배율 축을 둔다 |

**후보 하나의 처리**(역산 우선):
- (a) 전류와 gm/ID에서 ln IDu를 정한다.
- (b) bin이 요구하는 gm/gds를 만족하는 bin 안 L을 bisection으로 찾는다. 반복 상한은 K_max다. §4.1에서 격자 전용으로 분류된 칸이면 L 점만 쓴다.
- (c) VDS를 배분한다. 모든 소자를 VDSAT + tol_VDsat로 먼저 채우고, 남는 헤드룸은 ∂(gm/gds)/∂VDS가 큰 소자부터 준다.
- (d) 기생 용량 고정점을 푼다. 상한은 K_max이고, 넘으면 NONCONVERGENT 레코드를 남긴다.

**국소 봉인**: 봉인 1·2·6·7과 기둥 KVL·KCL을 검사한다. as-built 평가 커널을 블록 변수에만 적용하고, 나머지 변수는 고정 입력으로 둔다.

**고정 입력**(K1·K3·K8, 블록을 가로지르는 L 동치류): 첫 회차에는 §6 출발값을 쓰고, 이후 회차에는 직전 조립점 값을 쓴다. DEC-71 (3)의 'LR5 knee 앵커'와 다르므로 40 §8 R29에 올렸다.

**후보 수 상한과 종료**:
- 블록 후보 수 Π가 블록 몫 예산 N_B,i(§5.8)를 넘으면 강결합 그룹 단위 좌표 훑기로 바꾼다. 강결합 그룹은 같은 직렬 전류 경로를 공유하는 셀이다(P N3.7).
- 한 바퀴 동안 국소 front가 바뀌지 않으면 종료한다.
- N_B,i에 도달해도 종료하고 '예산 소진'을 기록한다.

### 5.4 블록 국소 front

- 블록마다 `{gain bin → (전력, 면적) 비지배 점}`을 만든다.
- (gain bin, 면적 bin) 칸 하나에는 전력이 가장 작은 점 하나만 남긴다. 전력이 같으면 포화 여유가 큰 점을 남긴다.
- 점 수가 상한을 넘으면 DEC-80 예산 게이트대로 bin 폭을 2배로 넓히고 배수를 기록한다.

### 5.5 조립 (M6)

**미지수**: y(K1~K4)와 공유량이다. 공유량은 공유 노드 전압, 블록을 가로지르는 `equal_vgs`의 공통 VGS, 미러 비, `kvl_branch` 종속 gm/ID, 폴딩 노드 전류다.

**풀이**: 별도 솔버를 두지 않는다. 블록 점의 θ와 출발값을 합친 θ로 as-built GB7 커널(`size_and_seal`)을 돌린다. 이 등식들은 writer plan의 등식으로 풀린다.

**공유 VGS 선택**(DEC-10):
- 그룹을 공유하는 블록 수를 m이라 하면, 각 블록의 국소 값 m개를 후보로 커널을 m번 돌린다.
- 봉인을 통과한 후보 중 전회로 `gain_ss_db`가 가장 큰 것을 고른다.
- gain 차가 b_gain 이하면 전력이 작은 쪽을 고른다(U-14 기본안).

**기록**: 국소 값과 전역 값의 차(ΔVGS, Δ노드전압, Δgm_id, Δ블록 gain)를 남긴다.

**시도 상한**: 조합 front 크기와 N_B,0 중 작은 쪽이다. 조립이 실패하면 다음 조합으로 간다.

### 5.6 조합 DP와 front

- **상태**: (블록 k, 누적 gain bin, 누적 면적 bin)이다. 값은 그 상태의 최소 전력 경로다.
- **종료**: 누적 gain ≥ G − b_gain이다.
- **r̂의 쓰임**: 측정되어 있으면 '누적 gain + r̂'가 큰 순서로 조립에 넘긴다. 종료 조건에는 넣지 않는다.
- **출력**: 종료 상태 중 (전력, 면적) 비지배인 조합 front와, 조합마다 `gain_budget_db.allocated`를 낸다.
- **동률**: 전력, 활성 여유 합, 이름 정렬 순으로 가른다.
- **상태 수 상한**: N_B,0이다.

### 5.7 출력과 override

**front 점마다 내는 값**: `gain_budget_db.allocated`, `gain_budget_db.realized`(최종 봉인 스냅샷의 블록 gain), 두 값의 차, `gain_residual_db`.

**`gain_budget_db_override{block_key: {value_db, source}}`**:
- 그 블록의 bin을 value_db로 고정한다.
- 블록 키가 없으면 `SchemaRejectedError(override_block_unknown)`이다.
- A_i,max가 인증되어 있고 value_db > A_i,max + b_GB4,i이면 INFEASIBLE_TARGET이다.
- A_i,max가 미상이면 받아들인다. 그 bin에 봉인을 통과한 후보가 없으면 `local_infeasible`을 보고한다(H3).
- `override_source`를 기록한다.

### 5.8 평가 예산 (DEC-34 식, M10)

**식**: N = floor((B − T_fixed) / t_eval)

| 기호 | 뜻 |
|---|---|
| B | `wall_clock_budget_s` |
| t_eval | 그 실행에서 잰 warm 평가 시간의 중앙값. 첫 평가가 끝나기 전에는 정의되지 않는다 |
| T_fixed | 이미 쓴 시간 + 외층 예약 시간 |
| 외층 예약 시간 | 끝점 2개 × as-built `slsqp_outer` maxiter 식 Σ⌈log2(폭/h)⌉ × t_eval |

**t_eval 첫 측정**: as-built `layer0_center` 시작점 하나를 먼저 평가해서 잰다. 이후 평가마다 중앙값을 갱신한다.

**예산 나누기**:
- **단계 A 예산 N_A**: 단위 비용을 단계 A 첫 국소 모델 행들의 실측 중앙값으로 두고 같은 식을 쓴다.
- **층 0 예산**: N_B,0 = N − 외층 예약 평가 수다.
- **블록 몫**: N_B,i = N_B,0 × (블록 i 후보 수 / Σ 후보 수)다.

N, t_eval, 배분, 소진 여부를 `perf`에 기록한다.

### 5.9 외층 인계 (M7)

- 외층 SLSQP는 조립점에서 시작한다. 블록 gain은 제약에 넣지 않는다(DEC-05·74).
- **근방 반경**: r_j = max(|θ_j,local − θ_j,assembled|, 격자 간격_j)다. 그 반경 안에 feasible이 없으면 곧바로 전역 bounds로 넓힌다.
- ε 스윕의 첫 ε는 조합 점의 면적과 전력이다.

**불변식**: 층 0은 전역 bounds를 줄이지 않는다. 같은 입력이면 같은 조합 front다. 평가 계수는 `perf`에 남긴다.

**실패**: 모든 조합의 조립이 실패하면 §6 시작점으로 넘어간다. 그것도 실패하면 `SearchFailedError`다.

**상태**: MISS. `E/search/layer0_center.py`는 새 흐름으로 대체되며, 국소 초기점 생성과 t_eval 첫 측정에만 남긴다.

---

## 6. 스펙에서 gm/ID·L·전류 출발 구간 (단계 A8)

**쓰임**: 출발값과 보고에만 쓴다(EP-7). 입력은 S1/S1v, spec, LUT 곡선, A6 상한표다.

**파일**: `E/search/start_intervals.py`, `iv_headroom.py`, `iv_speed.py`, `iv_gain_l.py`, `iv_matching_l.py`, `iv_area.py`, `iv_currents.py`, `macro_poles.py`.

**잡음 경로**: 설계 문장만 두고 파일은 만들지 않는다. 발동하는 회로가 없어 미구현이다(DEC-76, M9).

**LUT 곡선 API(신규)**: `ft_curve`, `intrinsic_gain_curve`, `vdsat_curve`, `idu_curve`.

### 6.1 계산 순서 (순환 없음, M8)

궤도마다 대표 소자로 계산하고, L 동치류는 구간의 교집합을 쓴다. 순서는 다음과 같다.

1. 헤드룸 gm/ID 하한(§6.2).
2. 이득 L 하한(§6.4-1). [gm/ID_lo, LUT 최대] 구간에서 intrinsic gain이 가장 큰 gm/ID를 쓴다.
3. 속도 L 상한(§6.4-4). gm/ID_lo를 쓴다.
4. matching·면적 L 경계(§6.4-2, -5).
5. L 선택(§6.4-6).
6. 그 L에서 속도 gm/ID 상한(§6.3).
7. gm/ID 선택: 구간 안의 최댓값.
8. 전류(§6.5).

### 6.2 gm/ID 하한 -- 헤드룸

**기둥별 가용 폭**:

V_col = ΔV_rail − Σ VGS_min(diode) − Σ R·I_cert

- VGS_min은 LUT 최대 gm/ID에서의 VGS다.
- 인증 전류 I_cert가 없으면 R 강하는 0이다.

**스윙 구간 분할**: 스윙 [V_lo, V_hi] 제약이 있는 노드 n에서 기둥을 나눈다.
- 위쪽 예산 = V_rail,hi − V_hi.
- 아래쪽 예산 = V_lo − V_rail,lo.

**하한**: 다음 식을 `vdsat_curve`로 역산한 값이 gm/ID_k,lo다. 여러 기둥에 걸친 소자는 그중 최댓값을 쓴다.

VDSAT_k(gm/ID) ≤ V_part − Σ_{j≠k}(VDSAT_j,min + tol_VDsat,j)

VDSAT_j,min은 LUT 최대 gm/ID에서의 VDSAT를 L 점 전체에서 최소로 한 값이다.

### 6.3 gm/ID 상한 -- 속도

- **전제**: `gbw_target_hz`와 `pm_target_deg`가 있어야 한다. 없으면 비활성이다.
- **비주극점 조건**: f_np ≥ GBW / tan(90° − PM)(2극점 근사).
- **대상 노드**: 극점 노드 중 주극점 노드를 뺀 노드다. 주극점 노드는 §6.5 매크로 모델에서 가장 낮은 극점의 고유벡터 성분이 가장 큰 노드다.
- **조건**: 그 노드에 낮은 등급 단자를 주는 소자는 f_T(gm/ID, L) ≥ f_np를 만족해야 한다.
- **산출**: `ft_curve`를 역산해 gm/ID_k,hi를 얻는다.

### 6.4 L 구간

1. **이득 하한**:
   - 블록 목표 g_i = G·A_i,max / Σ A_max로 둔다.
   - 블록 국소 모델 gain ≥ g_i를 만족하는 최소 L을 찾는다. bin은 오름차순으로 훑고, bin 안에서는 bisection한다.
   - A_max가 미상이거나 gain 제약이 없으면 비활성이다(H3).
2. **matching 하한**(Q2·Q3 선행):
   - A_min = (A_VT² + A_β²/(gm/ID)²) / σ_target²
   - L ≥ √(A_min · IDu / I)
   - 계수가 없으면 비활성('계수 미확보')이다.
3. **잡음 하한**: S·w_ref/W ≤ S_target이고 W = I·L/IDu다. 미구현(발동 없음).
4. **속도 상한**: f_T(gm/ID_lo, L) ≥ f_np에서 L의 최댓값.
5. **면적 상한**(결정 11):
   - L ≤ √(A_budget · IDu / I)
   - W ≤ A_budget / L
6. **선택**: L = max(1, 2의 하한)이다. LUT L 점이나 bin 안 값으로 맞춘다(LR3). 구간 끝이 다른 bin에 있으면 bin마다 후보를 하나씩 둔다.

### 6.5 전류 출발값 -- S1v 매크로 모델 (H4)

DEC-92 (2)의 근사를 회로별 식이 아닌 일반 매크로 모델로 둔다.

**망 구성**:
- 노드: 극점 노드.
- 이득 블록마다 VCCS gm_i를 두고, 출력 컨덕턴스 G_i = gm_i / 10^{g_i/20}로 둔다. g_i가 없으면 A_i,max를 쓴다.
- 노드 용량: 부하 + 소자 cgg 추정(gm / (2π f_T)) + 보상 수동소자.
- 보상 수동소자 값: 선언값이 있으면 그것, 없으면 θ 범위의 기하 중점.
- feedforward·복합 블록은 경로별 VCCS로 둔다.

**풀이**:
- 극점과 영점은 pencil 고유값으로 구한다(`pencil_roots`).
- gm_1은 UGF = `gbw_target_hz` 조건에서 1-D 근으로 구한다(`bracket_root`).
- 뒤 블록 gm_k와 보상 값은 PM ≥ `pm_target_deg`를 만족하는 최소값을 같은 방법으로 구한다.
- 근이 없으면 중점을 그대로 두고 '근 없음'을 기록한다.
- 단일 블록이고 Miller 루프가 없는 회로에서는 gm_1 = 2π·GBW·C_out이 된다. U-12 기본안과 같은 값이지만, 태그(`compensation: null`)가 아니라 구조로 정해진다.

**전류**:
- I = gm / (gm/ID).
- 나머지 소자는 미러 비와 KCL로 전파한다.
- 남는 θ 전류는 상자 기하 중심이다.

**기록**: `comp_approx_gap` = 매크로 극점과 조립점 MNA 극점의 차.

### 6.6 충돌과 보고

**충돌 레코드** `StartConflict{device|group, quantity, bounds[{source, value}], gap}`를 남기는 경우:
- 하한 > 상한
- 전류 > 상자 상한
- A_est > 예산(보고만)

충돌이 있어도 자르지 않는다. 양 끝 후보를 '충돌' 표시와 함께 층 0으로 넘긴다.

**보고 표**: `start_intervals[{device, gm_id_lo/hi/chosen, L_lo/hi/chosen, bin, I_start, sources, inactive_reasons, conflicts}]`

**불변식**: 같은 입력이면 같은 표다. 이름 전단사는 행 이름만 바꾼다.

**상태**: MISS. as-built는 spec과 무관한 LUT 포락선 상자 중점을 쓴다(`E/search/search_domain.py:35-56`, `layer0_center.py:105-172`).

---

## 7. 신규 공개 API

```python
def build_s1v(s1: S1, spec: SizingSpec, *, budget: EvalBudget) -> S1v                                  # E/graph/s1v_build.py
def block_local_gain(snap: GraphSnapshot, s1v: S1v, view_key: str, block_key: str) -> BlockGain       # E/metrics/block_model.py
def achievability(s1: S1, s1v: S1v, lut: LutSet, spec: SizingSpec, pdk: PdkDecl, *, budget: EvalBudget) -> Achievability  # raise InfeasibleTargetError
def start_intervals(s1: S1, s1v: S1v, ach: Achievability, lut: LutSet, spec: SizingSpec, pdk: PdkDecl) -> StartIntervals  # E/search/start_intervals.py
def layer0_budget(ctx: SearchContext, ach: Achievability, iv: StartIntervals, residual: ResidualProbe | None, *, budget: EvalBudget) -> BudgetFront
class EvalBudget:                                                                                      # E/search/eval_budget.py
    def remaining(self) -> int: ...      # N = floor((B - T_fixed) / t_eval), 온라인 갱신
```

---

## 8. 검증 -- 오라클, test, DoD 명령

오라클 종류(P N0.4): (a) 손계산·불변식, (b) 다른 방법의 참조구현, (c) SPICE, (d) 사용자 선언.

| 항목 | 오라클 | test(신규) | 핵심 단언 |
|---|---|---|---|
| SP1 | (a) 이름 없는 2~4소자 toy, (d) ratified 대조표 | `tests/graph/test_cells.py`, `test_drive_kind.py`, `test_stage_bfs.py`, `test_blocks.py` | 5T: 차동 블록 1, 미러 입력은 내부 노드. 2단: 블록 2. 캐스코드는 같은 stage. 이름 전단사 불변 |
| 루프 | (a) toy, (d) J11 | `test_loops.py`, `test_loop_classify.py` | Miller = (2). CMFB = 포트쌍 대응. 열거 상한 초과 시 정지 |
| 블록 gain·잔차 | (a) CS·캐스코드 손계산, (b) 단일 블록 회로에서 MNA와 비교 | `tests/metrics/test_block_model.py` | 단일 블록 잔차 ≤ 수치 분해능 |
| GB4 | (b) 작은 toy에서 격자 직접 전수, (a) 불가능한 gain 픽스처 | `test_block_gain_bound.py`, `test_achievability.py` | exit 3. 상한 미상이면 판정 없음. 저항이 있으면 전류 축 포함 |
| 면적 하한 | (a) | `test_area_lower_bound.py` | 인증되지 않은 전류 = 0 |
| DOF(IC6) | (a) 사고19 픽스처 | `tests/contracts/test_ic6_dof.py` | over/under 판정 |
| 층 0 | (a) 2블록 toy에서 전수 조합과 비교 | `tests/search/test_combo_dp.py`, `test_layer0_budget.py` | DP front = 전수 front. `gain_budget_db` 출력. override 반영 |
| 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 필요조건 성질 |
| 매크로 모델 | (a) 이상 VCCS 2·3극점 | `tests/search/test_macro_poles.py` | UGF·PM 근 |

**DoD 명령**(`$PY` = `C:\Python314\python.exe`):

```
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -m "not slow"
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/regression/test_structure_tables.py -q   # 9회로 S1v·발동표·A_max 표
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_layer0_pilot.py -q      # front 점마다 allocated·realized·잔차
```

---

## 9. 상태 요약

| 절 | 항목 | OK | DEV | PART | MISS |
|---|---|---|---|---|---|
| §1 SP1 | 10 | 0 | 0 | 1(1.2 정적 교류접지) | 9 |
| §2 블록 모델·잔차 | 3 | 0 | 0 | 0 | 3 |
| §4 GB4 | 5 | 0 | 0 | 1(4.1 곡선 분류) | 4 |
| §5 층 0 | 9 | 0 | 0 | 0 | 9 |
| §6 출발 구간 | 6 | 0 | 0 | 0 | 6 |
