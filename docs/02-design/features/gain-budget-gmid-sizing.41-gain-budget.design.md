---
template: design
version: 1.2
plan_version: 6.0
---

# gain-budget-gmid-sizing -- 41-gain-budget Design Document

> **Summary**: gain-budget-first 흐름을 설계한다(계획 N1.1, FR-1·FR-2·FR-4·FR-8, DEC-03·05·43·57·59·63·65·71·73·77·81). 다루는 범위는 여섯 가지다.
> - connectivity에서 signal stage를 유도한다(SP1).
> - 블록 국소 소신호 모델로 stage gain을 정의하고, 평가마다 전회로 MNA와의 잔차를 기록한다.
> - LUT 격자 상한으로 탐색 전에 달성 가능성을 판정한다.
> - 층 0에서 블록 gain bin별 (전력, 면적) 비지배 점을 만들고, 조합 DP로 예산 조합 front와 `gain_budget_db`를 낸다. 이 결과를 외층 SLSQP와 잇는다.
> - 스펙에서 gm/ID·L·전류 출발 구간을 topology와 무관하게 유도한다.
> - 잡음 경로를 만든다. spec 제약, LUT 잡음 데이터, MNA adjoint 잡음 해석, 오라클 `.noise` 대조를 포함한다.
>
> **Date**: 2026-10-08 · **Status**: v1.2. 이번 판의 변경은 셋이다.
> - 재검증 지적 N1~N9와 Low 항목 반영
> - 잡음 경로 추가(§7, 사용자 결정 2026-10-08)
> - v1.1에서 반영한 C1~C4·H1~H8·M1~M14·L1~L8 유지
>
> 색인과 표기는 [40-engine](gain-budget-gmid-sizing.40-engine.design.md)을 따른다(`E/`, OK/DEV/PART/MISS). as-built 기준은 master `004b7d2`다.

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

**예산은 두 종류이고 서로 섞지 않는다**(N1·N4):

- **계수 예산 N_S**(단계 A와 DP 상태 수에 씀)
  - 시간에 의존하지 않고 S0에서 계산한다. 같은 S0이면 결과가 늘 같다(결정론).
  - **기본값**: N_S = 이 회로에 쓰이는 kind들의 LUT 격자점 수 합 = Σ_kind |VGS|·|VDS|·|VS|·|L|·|W 슬라이스|. 근거는 "상한 계산 한 번이 LUT 전체를 한 번 훑는 양을 넘지 않는다"이다. LUT 파일에서 정해지므로 새 상수가 아니다.
  - **선언값**: spec human `structure_count_budget{value, source}`가 선언되면 기본값 대신 그 값을 쓴다. 이 값은 S0 지문에 들어간다.
  - **적용 대상**:
    - GB4 블록 격자 곱 Π(§4.2), 복합 블록 Π(§1.9): N_S를 넘으면 그 상한은 '미상'이다.
    - 사이클 열거(§1.8): N_S를 넘으면 정지한다.
    - 조합 DP 상태 수(§5.6): N_S를 넘으면 DEC-80 게이트로 bin 폭을 넓힌다.
- **시간 예산 N_T**(단계 B·C의 평가 커널 호출 수에 씀)
  - DEC-34 식으로 정한다(§5.8).
  - 단계 A는 커널을 부르지 않으므로 N_T를 쓰지 않는다.

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
   - 블록 키: 출력노드 넷 이름의 정렬된 배열이다. 단일 출력 블록은 원소 1개, 차동 블록은 원소 2개다. 구분자로 이은 문자열을 쓰지 않는 이유는 넷 이름에 어떤 문자가 들어 있어도 키가 모호해지지 않게 하기 위해서다. JSON에서는 배열로 쓴다.
   - 여기: 두 입력 넷에 ±½를 건다.
   - 출력: 두 출력노드 전압 차다.
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

**열거 상한**: 계수 예산 N_S다(§0). 시간과 무관하다. 넘으면 `StructureUnresolvedError(unsupported_rule_branch, reason=cycle_enumeration_over_budget)`로 정지한다(M14).

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
  - 묶음 크기 Π가 N_S를 넘으면 `unsupported_rule_branch`다. Π는 §4.2의 축 정의로 센 격자 곱이다.
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
| y (K1~K4) | 따로 새 격자를 만들지 않고 해당 LUT 축 격자를 쓴다. K1(부하 소자가 다른 블록의 미러·L 동치류에 속함): 그 소자의 gm/ID·L 축에 이미 포함. K2(공유 VGS): 노드 창 안의 LUT VGS 격자. K3(`stacked_vsb`): LUT VS 격자. K4(공유 노드 전압): W4 창 안의 LUT VDS 격자 |
| 블록 안 저항값 | 컨덕턴스 G = 1/R 기준 격자. 후보 G는 그 저항이 닿는 노드에 붙은 소자들의 LUT 격자 gds·W/w_m 값(축 격자에서 나오는 값)과, spec θ 범위 양끝의 1/R이다. 근거: 국소 모델에서 저항은 같은 노드의 소자 컨덕턴스와 더해지거나 직렬로만 영향을 주므로, 영향이 달라지는 지점은 그 컨덕턴스들과 비교되는 크기다. θ 범위 밖 후보는 버린다 |
| 미러 비 θ | 범위 양끝 + 내부 세분(아래 '비단조 축 처리') |
| 전류 배율 | 블록에 저항이 있을 때만 둔다(저항이 있으면 gain이 전류에 대해 0차 동차가 아니다). 격자는 전류 상자 [I_off, I_max] 위의 LUT ID 격자를 w_m으로 환산한 것. 같은 비단조 축 처리를 적용한다 |

**비단조 축 처리**(미러 비, 전류 배율, 저항, N5): 최대 행에서 그 축을 따라 양쪽 이웃 행의 gain을 본다.
- **이웃이 둘 다 작다**: 그 축에서 내부 최대다. 이웃 사이 구간을 이분해 세분하고, 이웃 간 gain 차가 b_GB4 이하가 되면 멈춘다. 상한은 K_max다.
- **최대 행이 축 끝점이고 그 방향으로 단조다**: 그대로 인증한다.
- **세분해도 이웃 차가 b_GB4 아래로 내려가지 않는다**: '미상'으로 둔다.

**계산**:
- 행마다 봉인 없이 블록 국소 모델을 풀어 gain을 구한다.
- 행 조건 (gm, ID, L, VDS, R, 비)과 함께 S0 지문 필드에 저장한다(행 단위 memo).
- 소자 파라미터는 LUT memo에서 한 번만 조회한다.

**예산 게이트**: 격자 곱 Π가 계수 예산 N_S(§0)를 넘으면(시간 무관, 결정론) 상한을 **'미상'**으로 두고 판정에 쓰지 않는다. 격자를 줄이지 않는 이유는, 줄인 격자의 최댓값은 상한이 아니기 때문이다. 이 처리는 P N3.7의 "LUT·구조만으로 상한을 계산할 수 없는 제약은 상한 미상"과 같다.

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
| L 동치류별 L | §6 L 구간 안의 LUT L 점(bin 선택). bin 안 연속값은 (b) 다듬기 단계에서만 정한다 |
| VDS | 축이 아니다. 아래 (c)가 정한다 |
| 전류 | 저항이 없는 블록에서는 축이 아니다. 전류 = max(블록 gm 요구 / gm/ID(§6.5), 봉인 9 전도 하한). 저항이 있으면 §4.2처럼 전류 배율 축을 둔다 |

**gain bin은 출력이다**(N6): 후보는 bin 목표 없이 만든다. 평가한 gain이 그 후보가 속할 bin을 정한다.

**후보 하나의 처리**(역산 우선):
- (a) 전류와 gm/ID에서 ln IDu를 정한다.
- (c) VDS를 배분한다. 먼저 모든 소자를 VDSAT + tol_VDsat로 채우고, 남는 헤드룸은 ∂(gm/gds)/∂VDS가 큰 소자부터 준다.
- (d) 기생 용량 고정점을 푼다. 상한은 K_max이고, 넘으면 NONCONVERGENT 레코드를 남긴다.
- 국소 봉인과 국소 모델 gain을 평가해 bin을 정한다.

**(b) bin 안 L 다듬기**(차지된 칸에만): 국소 front(§5.4)의 각 칸 대표 점에서 L 동치류마다 bin 안 L을 줄여 면적을 낮춘다. 조건은 같은 gain bin 유지와 봉인 통과이고, LUT bin 안 선형 보간에서 bisection으로 푼다(상한 K_max). §4.1이 '격자 전용'으로 분류한 칸이면 다듬지 않는다.

**국소 봉인 인터페이스**(신규 `E/sizing/size_and_seal_local.py`):

```python
def size_and_seal_local(ctx: KernelContext, theta_block: Mapping[str, float],
                        fixed: Mapping[str, float], columns: frozenset[str]) -> LocalSeal
```
- 계산 블록 ②~⑤를 `columns`에 속한 소자·노드에만 적용한다. 그 밖의 값은 `fixed`에서 읽는다.
- 봉인 1·2·6·7과 덮는 기둥의 KVL·KCL만 검사한다.
- 반환값은 `LocalSeal{ok, failures[FailureRecord], snapshot_fragment, gain_db, power_w, area_m2}`이다.
- 필드 캐시 키는 (블록 키, θ_block, fixed 지문)이다.

**고정 입력**(K1·K3·K8, 블록을 가로지르는 L 동치류): 첫 회차에는 §6 출발값을 쓰고, 이후 회차에는 직전 조립점 값을 쓴다. DEC-71 (3)의 'LR5 knee 앵커'와 다르므로 40 §8 R29에 올렸다.

**후보 수 상한과 종료**:
- 블록 후보 수 Π가 블록 몫 평가 예산 N_T,i(§5.8)를 넘으면 강결합 그룹 단위 좌표 훑기로 바꾼다. 강결합 그룹은 같은 직렬 전류 경로를 공유하는 셀이다(P N3.7).
- **한 바퀴**의 정의: 그룹을 정준 순서(40 §6)로 하나씩 고른다. 고른 그룹의 후보 점을 모두 평가하고, 나머지 그룹은 '현재 국소 front에서 전력이 가장 작은 점'의 값으로 고정한다. 모든 그룹을 한 번씩 거치면 한 바퀴다. 첫 바퀴의 고정값은 §6 출발값이다.
- 한 바퀴를 돌아도 국소 front의 (gain bin, 면적 bin) 칸 집합과 칸별 전력 값이 바뀌지 않으면 종료한다. 칸은 유한하고 칸별 값은 줄어들기만 하므로 반드시 끝난다.
- N_T,i에 닿아도 종료하고 '예산 소진'을 기록한다.

### 5.4 블록 국소 front

- 블록마다 `{gain bin → (전력, 면적) 비지배 점}`을 만든다.
- (gain bin, 면적 bin) 칸 하나에는 전력이 가장 작은 점 하나만 남긴다. 전력이 같으면 포화 여유가 큰 점을 남긴다.
- 칸 수(gain bin 수 × 면적 bin 수)가 계수 예산 N_S를 넘으면 DEC-80 예산 게이트를 적용한다. bin 폭을 2배로 넓히고 그 배수를 기록한다.

### 5.5 조립 (M6)

**미지수**: y(K1~K4)와 공유량이다. 공유량은 공유 노드 전압, 블록을 가로지르는 `equal_vgs`의 공통 VGS, 미러 비, `kvl_branch` 종속 gm/ID, 폴딩 노드 전류다.

**풀이**: 별도 솔버를 두지 않는다. 블록 점의 θ와 출발값을 합친 θ로 as-built GB7 커널(`size_and_seal`)을 돌린다. 이 등식들은 writer plan의 등식으로 풀린다.

**공유 VGS 선택**(DEC-10):
- 그룹 g를 공유하는 블록 수를 m_g라 하면, 각 블록의 국소 값 m_g개를 후보로 커널을 m_g번 돌린다.
- 봉인을 통과한 후보 중 전회로 `gain_ss_db`가 가장 큰 것을 고른다. gain 차가 b_gain 이하면 전력이 작은 쪽을 고른다(U-14 기본안).
- **그룹이 여럿이면**(M6): 정준 순서로 한 그룹씩 고른다(좌표별). 앞 그룹에서 고른 값은 뒤 그룹을 평가할 때 고정한다. 커널 호출 수는 Π m_g가 아니라 Σ m_g다.

**기록**: 국소 값과 전역 값의 차(ΔVGS, Δ노드전압, Δgm_id, Δ블록 gain)를 남긴다.

**시도 상한**: 조립 커널 호출 수는 조합 front 크기와 N_T,0(§5.8)의 남은 몫 중 작은 쪽이다. 조립이 실패하면 다음 조합으로 간다.

### 5.6 조합 DP와 front

- **상태**: (블록 k, 누적 gain bin, 누적 면적 bin)이다. 값은 그 상태의 최소 전력 경로다.
- **종료**: 누적 gain ≥ G − b_gain이다.
- **r̂의 쓰임**: 측정되어 있으면 '누적 gain + r̂'가 큰 순서로 조립에 넘긴다. 종료 조건에는 넣지 않는다.
- **출력**: 종료 상태 중 (전력, 면적) 비지배인 조합 front와, 조합마다 `gain_budget_db.allocated`를 낸다.
- **동률**: 전력, 활성 여유 합, 이름 정렬 순으로 가른다.
- **상태 수 상한**: 계수 예산 N_S(§0)다. DP는 커널을 부르지 않으므로 평가 예산과 섞지 않는다(N4). 넘으면 DEC-80 게이트를 쓴다.

### 5.7 출력과 override

**front 점마다 내는 값**: `gain_budget_db.allocated`, `gain_budget_db.realized`(최종 봉인 스냅샷의 블록 gain), 두 값의 차, `gain_residual_db`.

**`gain_budget_db_override: [{block: [<출력노드 넷 이름>...], value_db, source}]`**(블록 키는 §1.7-3의 정렬 배열):
- 그 블록의 bin을 value_db로 고정한다.
- 블록 키가 없으면 `SchemaRejectedError(override_block_unknown)`이다.
- A_i,max가 인증되어 있고 value_db > A_i,max + b_GB4,i이면 INFEASIBLE_TARGET이다.
- A_i,max가 미상이면 받아들인다. 그 bin에 봉인을 통과한 후보가 없으면 `local_infeasible`을 보고한다(H3).
- `override_source`를 기록한다.

### 5.8 평가 예산 N_T (DEC-34 식, 단계 B·C 전용, M10·N4)

**정의**: 커널 평가 횟수 예산.

N_T = floor((B − T_used − T_reserve) / t_eval)

| 기호 | 뜻 |
|---|---|
| B | `wall_clock_budget_s` |
| T_used | 지금까지 쓴 시간 |
| t_eval | warm 평가 시간의 중앙값. 첫 평가가 끝나기 전에는 정의되지 않는다 |
| T_reserve | 외층 최소 비용 = 끝점 2개 × (as-built `slsqp_outer` maxiter 식 Σ⌈log2(폭/h)⌉) × t_eval |

외층 예약분은 T_reserve로 **한 번만** 뺀다. N_T는 그렇게 뺀 뒤의 층 0 몫이므로, N_T에서 다시 빼지 않는다(N4).

**t_eval 첫 측정**: as-built `layer0_center` 시작점 하나를 먼저 평가해 잰다. 그 뒤로 평가할 때마다 중앙값을 갱신하고 N_T를 다시 계산한다.

**층 0 안 배분**:
- 블록 몫: N_T,i = N_T × (블록 i 후보 수 / Σ 후보 수).
- 조립 몫 N_T,0 = N_T − Σ_i (블록 i가 실제로 쓴 평가 수).

**외층 ε 점 수**(40 §3.6-5): 층 0이 끝난 시점의 시간으로 같은 식을 다시 계산한다(T_reserve 없이).

**기록**: `perf`에 N_T, t_eval, 배분, 소진 여부를 쓴다. 계수 예산 N_S는 §0의 정의를 따른다.

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

**파일**: `E/search/start_intervals.py`, `iv_headroom.py`, `iv_speed.py`, `iv_gain_l.py`, `iv_matching_l.py`, `iv_noise.py`, `iv_area.py`, `iv_currents.py`, `macro_poles.py`, `dominant_node.py`.

**잡음 경로**: 범위 안이다(사용자 결정 2026-10-08, §7). 1/f 제약이 있으면 1/f L 하한(§6.4-3)을, 열잡음 제약이 있으면 열잡음 gm 하한(§7.5)을 계산한다.

**LUT 곡선 API(신규)**: `ft_curve`, `intrinsic_gain_curve`, `vdsat_curve`, `idu_curve`.

### 6.1 계산 순서 (순환 없음, M8)

궤도마다 대표 소자로 계산하고, L 동치류는 구간의 교집합을 쓴다. 순서는 다음과 같다.

0. 주극점 노드를 구조로 정한다(§6.3). 이 단계는 매크로 모델을 쓰지 않는다(N3).
1. 헤드룸 gm/ID 하한(§6.2).
2. 이득 L 하한(§6.4-1). [gm/ID_lo, LUT 최대] 구간에서 intrinsic gain이 가장 큰 gm/ID를 쓴다.
3. 속도 L 상한(§6.4-4). gm/ID_lo를 쓴다.
4. matching·잡음·면적 L 경계(§6.4-2, -3, -5). 이 단계에 필요한 전류는 1차 전류 추정(§6.5 1회차)에서 가져온다.
5. L 선택(§6.4-6).
6. 그 L에서 속도 gm/ID 상한(§6.3).
7. gm/ID 선택: 구간 안의 최댓값.
8. 전류 확정(§6.5 2회차). 열잡음 gm 하한(§7.5)을 함께 적용한다.

**4의 전류를 정하는 방법**: 4는 전류 I가 필요하다. 그 값은 §6.5 매크로 모델을 **1회차**로 돌려 얻는다. 1회차에서는 gm/ID를 gm/ID_lo로 두고 L을 2의 하한으로 둔다. 확정 전류는 8에서 다시 계산한다. 4→8 사이에는 되먹임이 없으므로(8의 결과가 4로 돌아가지 않는다) 순환이 생기지 않는다.

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
- **주극점 노드(구조로 결정, N3)**: gain 제약 전달 뷰에서 정한다.
  - Miller (2) 루프가 있으면, 그 수동소자 구간이 잇는 두 노드 중 앞 노드(BFS 거리가 작은 쪽)가 주극점 노드다. Miller 증배가 걸리는 노드이기 때문이다. 루프가 여럿이면 블록 순서상 가장 앞 블록의 출력노드인 것을 쓴다.
  - Miller 루프가 없으면 출력 포트 노드가 주극점 노드다. 부하가 걸리는 노드다.
  - 등급이 '높음'이 아닌 노드는 주극점 노드 후보에서 뺀다.
- **대상 노드**: 극점 노드에서 주극점 노드를 뺀 나머지 전부다.
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
3. **flicker 잡음 하한**(사용자 결정 2026-10-08: 잡음 경로 구현). 1/f 영역 잡음 제약(§7.1)이 선언된 회로에서만 활성이다.
   - 입력 환산 1/f 밀도 예산 S_target(f₁)를 정한다. 출발 단계에서는 신호 경로 소자 수로 균등 분배한다. 정확한 판정은 §7.3이 한다.
   - 소자마다 1/f 기여 S_k(f₁) = KF_eff,k(L, gm/ID, VDS) / (W·L·f₁) × (gm_k/gm_in)²를 쓴다. KF_eff는 §7.2 LUT 열이다.
   - 위 식을 풀면 W·L ≥ A_min,k = KF_eff·(gm_k/gm_in)² / (f₁·S_target,k)가 된다. W·L = I·L²/IDu를 대입하면 **L ≥ √(A_min,k·IDu/I)**다(matching 하한과 같은 꼴).
4. **속도 상한**: f_T(gm/ID_lo, L) ≥ f_np에서 L의 최댓값.
5. **면적 상한**(결정 11):
   - L ≤ √(A_budget · IDu / I)
   - W ≤ A_budget / L
6. **선택**: L = max(1, 2, 3의 하한)이다. LUT L 점이나 bin 안 값으로 맞춘다(LR3). 구간 끝이 다른 bin에 있으면 bin마다 후보를 하나씩 둔다.

### 6.5 전류 출발값 -- S1v 매크로 모델 (H4)

DEC-92 (2)의 근사를 회로별 식이 아닌 일반 매크로 모델로 둔다.

**망 구성**:
- **노드**: gain 제약 전달 뷰의 극점 노드.
- **이득 블록 출력노드 컨덕턴스**: 블록마다 VCCS gm_i를 둔다. 출력노드 컨덕턴스는 G_i = gm_i / 10^{g_i/20}이다.
  - g_i가 없으면 A_i,max를 쓴다.
  - 둘 다 없으면 G_i = gm_i / A_intr,i로 둔다. A_intr,i는 블록 입력 소자의 LUT gm/gds(출발 gm/ID, L)이다. 캐스코드가 없다고 가정한 값이므로 보수적이다.
- **출력노드가 아닌 극점 노드**(캐스코드 source 노드 등, N9): 낮은 등급 단자를 주는 소자 c의 gm_c + gmb_c를 컨덕턴스로 둔다.
  - 이 값은 블록 gm에 비례하게 표현한다: gm_c = gm_i · ((gm/ID)_c / (gm/ID)_in) · r_c.
  - r_c는 KCL·미러 비로 정해진 전류 비다. 같은 가지에 있으면 1이다.
  - gmb/gm 비는 LUT에서 읽는다.
  - 높은 등급 노드는 붙은 drain 단자들의 gds 합을 쓴다. 이것도 같은 방식으로 gm_i에 비례한다.
- **노드 용량**: 부하 + 소자 cgg 추정(gm/(2π f_T)) + 보상 수동소자.
- **feedforward·복합 블록**: 경로마다 VCCS를 하나씩 둔다.

**보상 수동소자 값 규칙(하나만 쓴다, N9)**:
- 선언값이 있으면 그 값을 쓴다.
- 선언값이 없으면 **PM ≥ `pm_target_deg`를 만족하는 최소값**을 쓴다.
- θ 범위의 기하 중점은 1-D 근 찾기의 **첫 구간 분할점**으로만 쓴다.

**풀이 순서와 실패 처리**:
1. 극점과 영점은 pencil 고유값으로 구한다(`pencil_roots`).
2. 한 바퀴는 다음 세 단계를 차례로 수행한다.
   - (i) gm_1: UGF = `gbw_target_hz`의 1-D 근(`bracket_root`). 이때 나머지 값은 현재 값으로 둔다.
   - (ii) k = 2..n 블록 순서로 gm_k: PM ≥ 목표인 최소값.
   - (iii) 보상 수동소자: 정준 순서로 PM ≥ 목표인 최소값.
3. 한 바퀴의 모든 값 변화가 각자의 1-D 근 허용오차 안에 들면 수렴이다. 상한은 K_max 바퀴이고, 닿으면 마지막 값을 쓰고 `macro_nonconvergent`를 기록한다(보고만, 정지 아님).
4. 어떤 1-D 근이 그 변수의 범위(전류 상자 × gm/ID, θ 범위)에서 괄호가 잡히지 않으면 다음과 같이 처리한다.
   - 그 변수는 현재 값을 유지한다.
   - `macro_root_missing{variable, condition}`을 기록하고 다음 변수로 넘어간다.
   - 모든 변수가 근 없이 끝나면 매크로 출발값을 버리고 상자 기하 중심을 쓴다.

**특수 경우**: 단일 블록이고 Miller 루프가 없는 회로에서는 gm_1 = 2π·GBW·C_out이 나온다. U-12 기본안과 같은 값이지만, `compensation: null` 태그가 아니라 구조에서 나온다.

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

## 7. 잡음 경로 (사용자 결정 2026-10-08: "노이즈 spec을 추가해서 코드를 만들어야지.")

잡음 경로를 범위 안에 넣는다. 이 결정으로 P N1.2의 '잡음은 제약 metric으로 먼저 들어온다' 항목과 DEC-96 (3)의 '잡음·왜곡 미검증'은 잡음에 한해 바뀐다(계획서 정정 필요). 설계는 topology와 무관하다. 잡음원은 소자마다 붙고, 출력까지의 전달은 MNA adjoint로 계산하며, 회로별 식은 두지 않는다.

### 7.1 spec -- 잡음 제약 metric (닫힌 어휘)

| metric | 뜻 | 단위 | 선언 인자 |
|---|---|---|---|
| `noise_in_density_ss_v_rthz` | 입력 환산 잡음 전압 밀도, 지정 주파수 한 점 | V/√Hz | `freq_hz`, 전달 뷰(`ac_excite`, `sense`) |
| `noise_in_integrated_ss_v` | 입력 환산 적분 잡음 전압(RMS), 지정 대역 | V | `band_hz: [f_lo, f_hi]`, 전달 뷰 |

- 열잡음 영역 제약과 1/f 영역 제약은 둘 다 `noise_in_density_ss_v_rthz`를 쓰고 `freq_hz`로 구분한다. 이름을 따로 만들지 않는다(DEC-68: 개념 하나에 이름 하나).
- 제약 형식은 다른 제약과 같다: `{metric, op: "<=", value, source}`. `source`는 필수이고 `user_spec`이다.
- 회로별 값은 사용자가 정한다(40 §9 Q11). 값을 지어내지 않는다.
- 이 metric은 MOD5 레지스트리에 `MetricSignature{unit, domain: ss, view_kind: transfer, objective_axis: None}`로 등록한다. 단위 어휘에 `v_rthz`와 `v`를 추가한다(`core/units`).
- 레지스트리 밖의 잡음 이름은 `metric_unknown`으로 거부한다(as-built 규칙 그대로).
- 왜곡은 여전히 범위 밖이다.

### 7.2 LUT -- 소자 잡음 데이터 (PDK BSIM4 잡음 모델에서 특성화)

**열**(DC 슬라이스와 같은 축 (kind, w_key, L, VGS, VDS, VS)):

| 열 | 뜻 | 단위 |
|---|---|---|
| `SID_TH` | 열잡음 드레인 전류 PSD 계수 = S_id,thermal / gm | A²/Hz/S |
| `SID_FL1` | 1 Hz에서의 1/f 드레인 전류 PSD × f | A² |
| `FL_EXP` | 1/f 기울기 지수 af_eff. 두 주파수 측정에서 계산한다 | 무차원 |

**파생량**(읽는 쪽에서 계산하며 열로 저장하지 않는다):
- 열잡음 γ_eff = SID_TH / (4kT).
- 입력 환산 1/f 계수 KF_eff = SID_FL1·W·L / gm²(§6.4-3에서 사용).

**스윕**:
- ngspice `.noise` 해석을 쓴다. 단일 소자를 DC 바이어스한 뒤 drain 전류 잡음을 출력으로 하고, 출력 잡음 PSD를 읽는다.
- 축 격자는 기존 DC LUT와 같은 (L, VGS, VDS, VS) 격자이고, 폭은 DC 슬라이스 키와 같다.
- 주파수 두 점: f_th(1/f 성분이 열잡음보다 충분히 작은 높은 주파수)와 f_fl(1/f 우세 낮은 주파수). 두 값 모두 상수로 박지 않는다.
  - 각 소자 칸에서 1/f와 열잡음의 교차 주파수 f_c를 먼저 잰다(예비 스윕은 `.noise` dec 스윕).
  - f_th = 스윕 상단, f_fl = 스윕 하단으로 정한다. 스윕 범위는 PDK 모델 유효 범위와 LUT 생성 메타에 기록한다.
- 생성기는 `assets/sky130_lut_sweep.py`에 `.noise` 모드로 추가한다(U-27 (f) 공유 생성기).

**출처와 저장**:
- **새 버전 파일**로 쓴다. 이름은 `..._noise_r1.npz`이고 sha256, 생성 메타(모델 파일 경로·sha, ngspice 버전, 온도, 코너, 주파수 점)를 함께 둔다.
- 기존 공유 LUT 파일은 고치지 않는다. `lut_v2_location.json`에 새 항목으로 추가한다.
- 로더 `load_lut_set`은 잡음 파일이 있을 때만 잡음 열을 노출한다. 없는데 잡음 제약이 선언되면 `SchemaRejectedError(noise_lut_missing)`이다.
- tol은 다른 열과 같은 leave-one-out 방식으로 셀별 `tol_noise`를 계산한다(DEC-87 방법). 디스크 캐시 대상에 넣는다.

**LUT 조회 API**(신규): `noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams{sid_th, sid_fl1, fl_exp}`. as-built `CapTable.columns`의 옛 `SID_1F` 열은 단위가 틀렸으므로 읽지 않는다.

### 7.3 metrics -- 봉인 스냅샷 잡음 해석 (MOD5)

**잡음원**: 소자마다 drain–source 사이 전류 잡음원 하나를 둔다.
- S_id(f) = sid_th·gm + sid_fl1/f^{fl_exp}.
- 저항은 4kT/R을 둔다.
- 값은 봉인 스냅샷 `ss`의 동작점에서 LUT로 읽고, W 배율을 적용한다.

**전달**: as-built MNA(같은 (G, C) 조립)의 adjoint를 쓴다.
- 출력 감지 노드에서 단위 전류를 주입해 adjoint 해를 한 번 구한다. 그러면 모든 잡음원의 전달 함수 Z_k(jω)를 한 번에 얻는다.
- ω마다 풀이 1회이며, 조립은 다시 하지 않는다(WP-23).

**입력 환산**: S_in(f) = Σ_k |Z_k|²·S_k(f) / |H(jω)|². H는 선언된 전달 뷰의 전달함수(gain metric과 같은 뷰)다.

**산출**:
- `noise_in_density_ss_v_rthz` = √S_in(freq_hz).
- `noise_in_integrated_ss_v` = √∫S_in df. 적분은 대역 안 로그 격자의 사다리꼴 적분이다. 격자 간격은 오차가 분해능 이하가 될 때까지 이분 세분한다(상한 K_max).
- 소자별 기여 표 `noise_contrib[{device|element, share}]`.

**분해능**: metrics §9와 같은 방식이다. LUT 잡음 열의 tol_noise와 소신호 파라미터 tol이 adjoint 감도를 거쳐 전파된 값을 `MetricResult.resolution`으로 둔다.

**파일**: `E/metrics/noise_sources.py`, `E/metrics/noise_analysis.py`.

### 7.4 search -- 제약 행

다른 ss 제약과 같은 형식이다. 판정 단위는 c = (value − metric)/resolution이고, 풀이 척도는 40 §7.2를 따른다. 외층 전회로 판정 위치(DEC-74)도 그대로다.

### 7.5 출발 구간 -- 열잡음 gm 하한

열잡음 밀도 제약이 선언되면 입력 소자 gm 하한을 둔다.
- S_in,th ≈ Σ_k sid_th,k·gm_k / gm_in² ≤ S_target이다.
- 입력 소자만 고려하면 gm_in ≥ (Σ_input sid_th) / S_target이다. 매크로 모델(§6.5)의 비를 써서 나머지 소자의 gm/gm_in을 넣으면 gm_in ≥ (Σ_k sid_th,k·(gm_k/gm_in)) / S_target이 된다.
- §6.5에서 구한 gm_1이 이 하한보다 작으면 하한으로 올린다. 그다음 전류를 다시 전파한다.
- 1/f 하한은 §6.4-3이다.

### 7.6 오라클 -- ngspice `.noise` 대조

- 오라클은 엔진을 import하지 않는다.
- 같은 테스트벤치(free 모드 동작점)에서 `.noise v(sense) <입력원> dec ...`로 입력 환산 밀도와 대역 적분을 잰다. 엔진과 같은 정의다(같은 감지 노드, 같은 여기원).
- 비교 허용오차는 다른 metric과 같다. 엔진 metric의 resolution과 `model_error_noise_*`(DEC-72)로 판정하고, 모델 오차가 미측정이면 '판정 보류'다.
- 합격 T5에 잡음 제약을 넣는다(사용자 결정으로 범위 안이 되었으므로).
- 오라클 측정 항목 `ORACLE_MEASURES`에 두 metric을 더한다.

### 7.7 상태

7.1~7.6 모두 MISS다. as-built 잡음 관련 코드는 `noise_1f_density`(옛 엔진)가 전부이고, 새 엔진에는 해당 코드가 없다.

---

## 8. 신규 공개 API

```python
def build_s1v(s1: S1, spec: SizingSpec, *, count_budget: int) -> S1v                                   # E/graph/s1v_build.py
def block_local_gain(snap: GraphSnapshot, s1v: S1v, view_key: str, block_key: tuple[str, ...]) -> BlockGain  # E/metrics/block_model.py
def achievability(s1: S1, s1v: S1v, lut: LutSet, spec: SizingSpec, pdk: PdkDecl, *, count_budget: int) -> Achievability  # raise InfeasibleTargetError
def start_intervals(s1: S1, s1v: S1v, ach: Achievability, lut: LutSet, spec: SizingSpec, pdk: PdkDecl) -> StartIntervals  # E/search/start_intervals.py
def layer0_budget(ctx: SearchContext, ach: Achievability, iv: StartIntervals, residual: ResidualProbe | None, *, count_budget: int, eval_budget: EvalBudget) -> BudgetFront
def size_and_seal_local(ctx: KernelContext, theta_block, fixed, columns: frozenset[str]) -> LocalSeal    # E/sizing/size_and_seal_local.py
def count_budget(lut: LutSet, kinds: frozenset[str], spec: SizingSpec) -> int                           # E/search/count_budget.py  (N_S, §0)
class EvalBudget:                                                                                       # E/search/eval_budget.py  (N_T, §5.8)
    def remaining(self) -> int: ...
def noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams                                            # E/lut/noise_query.py
def noise_analysis(snap: GraphSnapshot, view_key: str, spec_item) -> NoiseResult                         # E/metrics/noise_analysis.py
```

---

## 9. 검증 -- 오라클, test, DoD 명령

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
| 매크로 모델 | (a) 이상 VCCS 2·3극점, 캐스코드 노드 포함 | `tests/search/test_macro_poles.py` | UGF·PM 근, 근 없음 기록, 바퀴 수렴 |
| 계수 예산 결정론 | (a) 같은 S0 두 번 | `tests/search/test_count_budget.py` | N_S가 시간과 무관하다. 사이클·Π 결과가 실행 간 같다 |
| 비단조 축 처리 | (a) 비율에 대해 내부 최대가 있는 toy | `test_block_gain_bound.py` | 세분 후 인증, 실패 시 미상 |
| 잡음 LUT | (c) 단일 소자 ngspice `.noise` 칸 중앙 대조 | `tests/lut/test_noise_query.py` | 칸 중앙 오차 ≤ tol_noise |
| 잡음 해석 | (a) 저항 분압·CS 한 단 손계산(4kTR, 4kTγgm), (c) ngspice `.noise` | `tests/metrics/test_noise_analysis.py` | 입력 환산 밀도·적분이 resolution 안 |
| 잡음 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 열잡음 gm 하한, 1/f L 하한 |

**DoD 명령**(`$PY` = `C:\Python314\python.exe`):

```
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -m "not slow"
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/regression/test_structure_tables.py -q   # 9회로 S1v·발동표·A_max 표
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_layer0_pilot.py -q      # front 점마다 allocated·realized·잔차
```

`test_structure_tables.py`는 `runs/<run_id>/structure_tables/`에 다음을 쓰고, 9회로 전부 표가 있는지 단언한다(N7).
- 9회로 S1v 표와 규칙 분기 발동표
- 블록별 GB4 표(블록 키, 격자 곱 Π, N_S, 인증/미상, A_max, b_GB4)
- 회로별 인증 비율(인증 블록 수 / 블록 수)

---

## 10. 상태 요약

| 절 | 항목 | OK | DEV | PART | MISS |
|---|---|---|---|---|---|
| §1 SP1 | 10 | 0 | 0 | 1(1.2 정적 교류접지) | 9 |
| §2 블록 모델·잔차 | 3 | 0 | 0 | 0 | 3 |
| §4 GB4 | 5 | 0 | 0 | 1(4.1 곡선 분류) | 4 |
| §5 층 0 | 9 | 0 | 0 | 0 | 9 |
| §6 출발 구간 | 6 | 0 | 0 | 0 | 6 |
| §7 잡음 | 6 | 0 | 0 | 0 | 6 |
