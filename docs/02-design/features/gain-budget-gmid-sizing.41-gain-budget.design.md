---
template: design
version: 1.5
plan_version: 6.3
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
> **Date**: 2026-10-08 · **Status**: v1.5. 사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해."(J 공동분석, 근거 `_drafts/engine/J_joint_analysis_2026-10-08.md`)를 반영했다.
> - §1.12 구조 규칙 6개 추가: 복합 diode D1, feedforward 셀, 중첩 Miller 보상 내부 루프, 루프 극성 = DC 사이클 극성, L 주인 `main_path_signal`, 뷰 한정 교류접지 예외
> - §1.13 회로별 실측·기대 표 추가
> - §1.2·§1.4·§1.6·§1.8·§1.9·§2·§4.3·§4.6(입력 DC 정책 SP-2 (c)·짧은 L bin 경고)·§5.1·§6.5·§8·§9 갱신
>
> v1.4는 사용자 결정 2026-10-08 "q3,q4는 네 제안대로 해"(Q3 offset·미러비, Q4 스윙·ICMR)를 반영했다: §6.4-2 mismatch 모델을 유효 계수 A_eff(LUT 감도 열, bin별 slope)로 대체, §6.4-2a offset 구조 가드, §6.2 스윙·ICMR 예산 분할, §4.6 헤드룸 달성가능성 보고. 근거 `_drafts/engine/matching_swing_spec_proposal.md`. v1.3은 사용자 결정 2026-10-08 "Q1~Q11 모두 네 의견대로 진행해"를 반영했다(R29 knee 추가 후보, Q2 Pelgrom 출처, Q5b 판정 보류 탐색, Q11 잡음 값과 metric). v1.2의 변경은 다음 셋이다.
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
 A7 GB4c verdict        : Σ A_i,max 판정, 구조 DOF, 인증된 면적 하한,    §4.3~4.6
                          헤드룸 창 상한(스윙·ICMR·버퍼)
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

**뷰 한정 예외**(J-C): 위 판정 뒤 ratified `ac_ground_exception` 사실이 지정한 뷰에서만 그 넷을 교류접지로 둔다(§1.12.6).

### 1.3 도달성과 순방향 집합

최소 고정점으로 신호 넷을 모은다. 여기 포트에서 시작해 다음 세 규칙을 반복한다. 교류접지 넷과 제거된 넷은 넣지 않는다.
- (a) 신호 넷을 gate로 받는 소자의 drain·source를 넣는다.
- (b) 신호 넷을 source로 받는 소자의 drain을 넣는다.
- (c) 신호 넷에 붙은 2단자 수동소자의 반대쪽 단자를 넣는다.

**순방향 집합 F**는 이 그래프에서 여기 포트로부터 도달하고 출력 포트로 역도달하는 넷의 집합이다.

### 1.4 셀 분류

1. **gate = drain**이면 `diode_load`다. 복합 diode 묶음(§1.12.1)의 MOS 멤버도 `diode_load`다.
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

**diode 단자**: 위 표와 규칙 9 (c)의 'diode 단자'는 단순 diode와 복합 diode(§1.12.1) 소자의 gate 넷이다.

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

**분류**: (1.5) 바이어스 SCC → (1.6) 복합 diode 내부(§1.12.1) → (2) Miller → (3-a) → (3-b) → (4) 순서로 판정한다. 정의는 P N3.2-2를 따른다. (2)와 (3-b)를 함께 만족하면 두 분류를 모두 단다. (3-b)는 배타 조건 (가)·(나)를 적용하고, (나)는 복합 diode 묶음 밖의 루프에만 남는다. (2)·(3-b) 루프가 §1.12.3 조건을 만족하면 루프 뷰를 만들지 않는다(`compensation_internal`).

**끊는 점**: 루프 위에 gate 엣지가 있는 CS 셀의 gate다.
- 후보가 여럿이면 복귀 경로 다음 첫 gate를 고른다.
- 복귀 구간이 여럿이면, 이름 정렬로 첫 노드에서 시작한 사이클 표현의 가장 이른 구간을 쓴다.
- 후보가 없으면 `review_needed`다.

**극성**: §1.12.4(J-F). 사이클 극성은 커패시터를 지나지 않으면 셀 부호의 곱(CS −, 그 밖 +)이고, 지나면 `ac_only`(info)다. 루프 뷰 극성 = 그 뷰의 DC 사이클 극성이다.

**U-24 게이트와 CM 루프의 구조적 대응**(H5): 루프 뷰 ℓ의 사이클 노드 집합이 **선언된 차동 출력 포트쌍(role p/n)의 두 넷을 모두** 포함하면, ℓ을 '포트쌍 CM 루프 대응'으로 본다.
- 근거: 포트쌍에 같은 부호로 주입하면 두 출력 넷을 함께 지나는 모든 CM 되먹임 경로가 한 번에 열린다.
- 그 ℓ의 안정도 metric은 40 §5의 `pm_cm_ss_deg`다.
- U-24 정지 대신 사용자 결정(2026-10-08)을 따른다. 제약이 미선언이면 T_cm만 보고하고, T_cm(0) > 1이면 경고 `cm_loop_unconstrained`를 낸다.
- 그 밖의 루프 뷰는 안정도 제약이 미선언이면 GB2 출구에서 `StructureUnresolvedError(undeclared_loop_constraint)`로 정지한다.
- '선언'은 spec 루프 뷰 선언(`ViewDecl` kind loop의 끊는 넷)이 안정도 제약 행에 쓰인 것이다. 단계 A 진입점이 그 끊는 넷 목록을 `build_s1v(declared_loop_cuts=...)`로 넘긴다(40 §3.2-3 파이프라인 수정. `[u1-sp1]` `pipeline/stage_a.py`는 넘기지 않아 선언해도 정지가 풀리지 않는다).

### 1.9 버퍼 묶음, 출력 방향, 복합 블록

- **R(u)**(DEC-63): CD 병렬 합류(②)에서는 §1.7의 ①보다 먼저 판정한다.
- **출력 방향**(DEC-65): β/σ/κ와 push-pull·class-A 구분은 MOD3에서 구조로 판정한다. 값은 40 §3.8 `ls`가 낸다.
- **feedforward 분리**(§1.12.2, J-A): 복합 블록 판정 전에 FF 묶음을 주경로 블록 구성에서 뺀다. FF 합류는 복합 블록으로 묶지 않는다.
- **복합 블록**(DEC-81): ②의 합류 노드가 전류 구동이거나 블록 출력노드면 묶는다. 묶은 결과 DAG는 사슬이어야 한다.
  - 묶음 크기 Π가 N_S를 넘으면 `unsupported_rule_branch`다. Π는 §4.2의 축 정의로 센 격자 곱이다.
  - 경로별 기여는 §2에서 계산한다(⑭).

### 1.10 declared 대조와 발동표

- **declared 대조**: declared stage(`compensation.stage_devices`, `gain_stages_sum.stages`, `vertical_stack_id`)는 `declared` 엣지로만 싣고 유도 결과와 대조한다. 불일치면 `review_needed`다. 유도 입력으로는 쓰지 않는다(U-50).
- **발동표**(R7, 축소 유지 승인 2026-10-08): `rule_branch_coverage.json` 파일은 만들지 않는다. 대신 다음은 유지한다.
  - `기록만` 분기를 탈 때의 `unsupported_rule_branch` 정지(exit 2).
  - J ratify 전에 걸리는 `review_needed` 정지(DEC-59 안전망).
  - 분기 발동 사실을 S1v `review_needed[]`와 결과 JSON에 기록하는 일.

### 1.11 6a 열린 항목 결정

| 항목 | 결정 |
|---|---|
| ① | as-built `gvgs_cycles` |
| ② | R(u)를 먼저 판정 |
| ③ | 구조로 못 가르는 DC 역할 그룹은 잠정 신호 소자로 두고, 블록에 `review_needed`를 붙여 GB4 앞에서 정지. 2026-10-08 J: 복합 diode(§1.12.1)로 구조가 풀리는 그룹은 규칙으로 가르고, 남는 그룹만 ratified `dc_role` 사실(40 §3.2-3)로 정한다 |
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

**상태**: MISS. 부분 대리물은 `E/authoring/_feedback_cuts.py:11`, `E/metrics/loop_cut.py:60`, `[ng-cmfb-pm] E/authoring/cm_partition.py`, `E/graph/matching_groups.py:202`다. SP1 본체는 `[u1-sp1]`(eae0292, 미병합)에 있다.

### 1.12 J 공동분석 구조 규칙 (사용자 결정 2026-10-08 "j해석은 네의견에 모두 동의해.")

**근거**: `_drafts/engine/J_joint_analysis_2026-10-08.md`(SP1 9회로 실측, `[u1-sp1]` 7c757e8, `s1v_rule_fp` e6c195f2…1aef). 결정 전문은 `_drafts/user_decisions.md` 마지막 항목이다.

**이름 규칙**: 아래 1.12.1~1.12.5는 구조 규칙이다. 회로·소자·넷 이름을 쓰지 않는다(EP-1). 회로별 산출은 §1.13 실측 표와 40 §3.2-3 사실 표에만 적는다.

**배선 원칙**: 각 규칙은 '소비' 항목에 적은 기존 계산 경로를 대체한다. 소비처가 없는 규칙은 두지 않는다.

#### 1.12.1 복합 diode (D1) -- DC 역할·미러 인식·루프 분류의 공통 입력

**정의**(S1, connectivity만 쓴다). MOS X의 gate 넷을 g, drain 넷을 d라 하고 'DC 가지 걷기'를 한다.
- 출발: w = d.
- 단계마다:
  - w = g이면 성공이다.
  - 아니면 w가 다음 두 조건을 모두 만족해야 한다. (i) 레일·포트·이상원 단자 넷이 아니다. (ii) w에 붙은 **DC 전류 단자**가 정확히 둘이다(직렬 노드). DC 전류 단자는 MOS 채널 단자(d·s)와 2단자 저항 단자다. gate와 커패시터 단자는 세지 않는다.
  - 두 조건을 만족하면 방금 들어온 단자가 아닌 쪽 단자의 원소를 지나 그 반대쪽 넷으로 간다.
  - 만족하지 않거나 이미 지난 넷에 다시 오면 실패다.
- 지난 원소가 하나 이상이고 성공하면 X는 **복합 diode 소자**다. gate = drain인 단순 diode(지난 원소 0)는 기존 규칙 1 그대로다.
- 걸음 수는 원소 수를 넘지 않으므로 따로 상한을 두지 않는다.

**묶음**: 복합 diode 소자 X와 그 걷기가 지난 원소(MOS·저항, 지나간 단순 diode 포함)가 한 묶음이다. 걷기가 원소를 공유하는 묶음은 합친다(union-find).

**묶음 안 역할**: 다른 복합 diode 소자의 걷기에 들지 않는 복합 diode 소자가 **기준**(`diode_reference_composite`)이다. 나머지 복합 diode 소자는 **캐스코드 기준 멤버**(`diode_reference_composite_cascode`)다. 지나간 단순 diode와 저항은 묶음 멤버로만 기록한다.

**소비**(배선 세 곳 -- 같은 묶음 레코드를 읽는다):
1. **DC 역할**(`E/graph/dc_roles.py` 규칙 1 확장, S1).
   - 복합 diode 소자는 diode 기준 역할이다(evidence rule `1c`, 하위 구분 composite / composite_cascode).
   - 그러면 규칙 2의 gs 묶음이 '기준이 있는 묶음'이 되어, 같은 gate·source 묶음의 나머지 멤버는 바이어스 전류원으로 갈린다. 이것이 J-U3-c '구조로 못 가르는 그룹'을 구조로 푸는 경로다.
   - L 동치류 주인 규칙 2(`current_source_member`)는 diode 기준을 읽으므로 이 기준을 그대로 고른다.
2. **미러 인식**(`E/graph/drive_kind.py` `_mirror_inputs`, 규칙 9 (c)·⑧, S1v).
   - '미러 입력 넷' 판정의 'diode 연결 단자'를 '단순 diode 또는 복합 diode 소자의 gate 넷'으로 넓힌다.
   - 그 넷을 gate로 읽는 다른 순방향 셀이 있으면 그 넷은 미러 입력(블록 내부 노드)이다. 그 셀은 stage를 시작하지 않고, 블록은 미러 출력 쪽으로 이어진다.
   - §1.6 엣지 비용의 'gate가 diode 단자면 0'도 같은 넓힌 정의를 쓴다.
   - 셀 분류(§1.4-1): 복합 diode 묶음의 MOS 멤버는 `diode_load`로 분류한다. 묶음 전체가 진입 넷에 걸린 diode 부하 하나(1/gm_eff)이기 때문이다. 묶음 내부 넷은 블록 내부 노드이고 구동 종류 혼재 판정(§1.5-4) 대상이 아니다.
3. **루프 분류**(`E/graph/loop_classify.py`, §1.8).
   - 분류 순서에 **(1.6) 복합 diode 내부 루프**를 (1.5) 바이어스 SCC 바로 뒤, (2) Miller 앞에 둔다.
   - 판정: 사이클의 모든 원소(엣지의 MOS·수동소자)가 한 복합 diode 묶음 안에 있으면, DC 국소 루프로 기록하고(`composite_diode_internal`, info) 루프 뷰를 만들지 않는다.
   - 이 규칙이 계획 N3.2-2 (3-b) 배타 조건 (나)('수동소자 없는 2능동셀 루프 → `기록만`')와 '국소 되먹임 조건 발동 0' 보류를 닫는다. (나)는 복합 diode 묶음 **밖**의 2능동셀 루프에만 남는다.

**바뀌지 않는 것**:
- 단순 diode 규칙 1과 J1 술어(§1.2)는 그대로다.
- 복합 diode 기준 가지에 흐르는 전류가 차동쌍 공통 source 넷에서 빠지는 것(레플리카 전류 분할)은 KCL이 이미 다룬다. GB7 꼬리 전류 예산에서 유효 꼬리 전류 = Σ 꼬리 공급 − Σ 레플리카 가지 전류다(새 코드 없음, U1b test로 확인).

#### 1.12.2 feedforward 셀 (J-A)

전달 뷰마다 블록 구성(§1.7) 뒤, 복합 블록(§1.9) 앞에서 판정한다.

1. **주경로**
   - G_f: 그 뷰 순방향 넷 F 위의 능동 셀 엣지만으로 만든 그래프다(§1.6 비용, 수동소자 엣지 제외). SCC는 응축한다.
   - D_max(n): 뷰 입력에서 n까지의 **최대** 비용, 즉 지나는 stage 시작 수의 최댓값이다. §1.6의 0-1 BFS(최소 비용)와 다른 양이다.
   - slack(e = u→v) = D_max(v) − D_max(u) − cost(e) ≥ 0.
   - **주경로 셀**: 뷰 입력에서 감지 출력까지 slack 0 엣지만으로 이어진 경로 위에 있는 셀이다.
   - **주경로 블록**: 그 셀들로 다시 구성한 블록이다(아래 3).
2. **feedforward 묶음**
   - FF 진입 엣지: 주경로가 아닌 신호 셀 c가 주경로 넷 m으로 들어오는 엣지이고 slack > 0인 것.
   - **합류 노드 조건**: m은 주경로 **블록 출력노드**여야 한다. 이 조건이 측면 주입(K8, 블록 내부 노드로 들어옴)과 feedforward를 가른다.
   - FF 묶음: c에서 출발해 주경로 넷에 닿을 때까지 거꾸로 따라간 비주경로 신호 셀 전부다. 닿은 주경로 넷이 **탭** u다.
   - 함께 묶는 것: 묶음 내부 넷에 drain이 붙은 바이어스 전류원(`ff_bias`)과 diode 부하(`ff_load`).
   - **우회 조건**: u에서 m까지 주경로가 지나는 블록 출력노드 중 FF 묶음이 지나지 않는 것이 하나 이상 있어야 한다. 그 첫 블록이 **처음 우회한 블록** B_b다. 우회 조건을 만족하지 않으면 FF가 아니고, 기존 규칙(§1.7 병렬 합류)대로 처리한다.
   - 주경로 최장 경로가 둘 이상이고 셀 집합이 다르면 `review_needed`(`main_path_ambiguous`)다.
3. **블록 분해**
   - FF 묶음의 셀을 빼고 §1.7을 다시 적용하면 주경로 블록 사슬이 된다.
   - m은 그 노드를 출력으로 갖는 주경로 블록에 둔다. FF 묶음은 그 블록의 **합류 입력**으로 붙인다.
   - FF 합류에는 복합 블록 조건(§1.9, DEC-81)을 적용하지 않는다. 경로 기여로 다룬다(아래 4).
   - 산출 필드: `feedforward_cells[{id, tap, merge, cells, bias_cells, load_cells, bypassed_blocks, sign}]`. sign은 경로 셀 부호의 곱이다.
4. **gain 귀속**
   - gain 예산(§5 bin·조합·`gain_budget_db`)은 주경로 블록에만 둔다. FF에는 예산 항목이 없다.
   - FF 기여는 §2 블록 국소 모델에서 **경로 기여**로 계산한다. merge 블록의 국소 해에 탭 전압을 추가 입력으로 넣는다.
   - 분해 합성값: A_decomp = Π_main A_i + Σ_ff A_in→tap · G_ff · Z_merge.
   - 잔차(§2.2)는 `gain_ss_db − 20·log10|A_decomp|`다.
   - `ss.ff_contrib{ff_id: {gain_db, sign}}`를 함께 쓴다.
5. **비율 제약 후보**(sizing 제약, 출처 기록)
   - FF 묶음마다 r_ff = G_ff / gm_in(B_b)를 정의한다.
   - G_ff: B_b 입력 넷 전압에서 merge 노드 단락 전류까지의 FF 경로 트랜스컨덕턴스. FF 안의 미러 비를 포함한다.
   - gm_in(B_b): B_b input 셀의 gm이다.
   - 관계 r_ff = 1이 영점 상쇄 조건 후보다. 출처: You, Embabi, Sánchez-Sinencio, IEEE JSSC 32(12), 1997; Leung & Mok, IEEE TCAS-I 48(9), 2001.
   - S1v는 `ff_ratio_candidates[{ff, bypassed_block, relation, source}]`를 내고, 단계 A 보고(`stage_a_report`)가 이를 출력한다.
   - metric `ff_gm_ratio`(단위 ratio, 40 §3.8-8 어휘에 추가)는 front 점마다 보고한다.
   - 제약 행은 spec이 값과 `source`를 선언할 때만 활성이다. 값은 사용자 몫이다.
   - 출발 구간(§6.5)은 FF 셀 전류 출발값을 r_ff = 1 관계에서 낸다. 이것은 출발값일 뿐이다(EP-7).
6. **달성가능성**(§4.2·§4.3)
   - A_i,max는 주경로 블록만 계산한다.
   - Σ 판정의 상한 = 20·log10(Π A_i,max + Σ_ff A_ff,max)이다. A_ff,max = (입력→탭 상한) × (FF 경로 격자 상한)이다.
   - 성분 하나라도 미상이면 상한은 미상이다(§4.2 규칙).

#### 1.12.3 중첩 Miller 내부 루프 = 보상 루프 (J-B)

**대상**: §1.8 (3) 판정으로 생기는 루프 뷰 후보 ℓ(끊는 점 c, 출처 전달 뷰 T).

**구조 조건**: 다음 (a)(b)를 모두 만족하면 ℓ은 `compensation_internal`이다.
- (a) ℓ의 모든 사이클이 (2) Miller 조건을 만족한다. 즉 사이클마다 커패시터를 포함한 수동소자만의 극대 구간이 있고, 그 구간이 T의 순방향 넷 둘을 잇는다.
- (b) ℓ의 사이클 위 능동 셀이 모두 T의 순방향 셀이다. 즉 루프가 개루프 증폭기 **내부**에 있다.

**처리**:
- 루프 뷰를 만들지 않는다. GB5가 보상 루프로 받는다.
- 안정도는 T의 전체 루프 제약 `pm_ss_deg`가 덮는다. 그 판정에는 개루프 RHP 극점 수 P = 0이 포함된다(결정 A 탐색 규칙, 오라클은 40 §4 Q10의 Nyquist Z = N + P와 `.pz`).
- T에 `pm_ss_deg` 제약이 선언되지 않았으면 기존 정지 `undeclared_loop_constraint`를 유지하고 사유 `compensation_internal_needs_overall_pm`을 붙인다.
- (3-b) 판정 자체는 바꾸지 않는다. 수동소자 엣지를 뺀 거리로 (3-b)를 다시 정하는 안(B3)은 9회로 실측에서 다른 회로를 깨므로 기각했다.

**조건 (b)가 막는 것**: 순방향 밖 능동 셀(예: 공통 모드 감지·주입 셀)이 낀 되먹임 루프는 (b)를 만족하지 않는다. 그런 루프는 루프 뷰로 남는다(40 §5).

#### 1.12.4 루프 극성 (J-F)

§1.8 '극성' 문단과 P N3.2-7의 '커패시터만 거쳐 저주파 경로가 없으면 `review_needed`'를 아래로 대체한다.
- **사이클 극성**
  - 커패시터를 지나지 않는 사이클(저항은 지나도 된다): 셀 부호의 곱(CS −1, 그 밖 +1, 저항 +1)이다. 이것이 **DC 사이클 극성**이다.
  - 커패시터를 지나는 사이클: 극성 `ac_only`로 기록한다(info `loop_polarity_ac_only`). 그 사이클의 수동소자는 GB5 보상 후보 목록에 올린다.
- **루프 뷰 극성** = 그 뷰에 속한 DC 사이클들의 극성이다.
  - 모두 같으면 그 값이다.
  - 서로 다르면 `review_needed`(`loop_polarity_conflict`)다.
  - DC 사이클이 하나도 없으면 `loop_polarity_undefined`(review_needed)를 유지한다. 1.12.3 뒤에는 발동 기대가 0이다.

#### 1.12.5 L 동치류 주인 (J-F)

DEC-17 순서(`E/graph/l_classes.py`)의 3번째에 규칙 하나를 넣는다.
1. tail
2. `current_source_member`: diode 기준(1.12.1의 복합 diode 포함)
3. **신규 `main_path_signal`**: 멤버 중 gain 제약 전달 뷰(없으면 첫 전달 뷰)의 **주경로 stage 시작 셀**(1.12.2)인 것. FF 묶음 멤버보다 우선한다. 여럿이면 가장 앞 stage 것이다.
   - 근거: FF 셀은 주경로 전류를 복사하는 쪽이다. 따라서 주경로 소자가 L 기준이 되는 것이 회로 원리에 맞다.
4. `name_order`: 남은 동률만 해당한다. `review_needed`(`l_owner_name_order`)로 올린다.

#### 1.12.6 뷰 한정 교류접지 예외 (J-C)

§1.2 (4) 술어 결과 위에, ratified 사실 `ac_ground_exception{subject: 넷, value: 뷰 id}`가 있으면 **그 뷰에서만** 그 넷을 교류접지로 둔다(40 §3.2-3 override).
- 다른 뷰(CM 전달 뷰·전원 뷰 등)에서는 J1 판정이 그대로다.
- 구조 규칙이 아니라 회로 해석 사실이다. 근거: 레플리카가 전류원에 고정되어 신호 전류를 싣지 않으므로 1차 근사로 접지다. 잔여 효과는 오라클 CM 루프 측정이 잰다.
- 이 사실이 필요한지는 1.12.1을 적용한 뒤 실측으로 확인한다. 1.12.1은 레플리카 가지의 DC 역할과 루프 분류만 바꾸고, 루프 뷰에서 레플리카 구동 gate 넷이 움직이는 것은 바꾸지 않는다. 그래서 분석 패킷 C.4 기준으로는 그 뷰의 `cs_output_low_impedance` 정지가 이 사실 없이 남는다.

### 1.13 J 규칙 실측·기대 표 (규칙 아님 -- 회로 이름은 이 표와 40 §3.2-3에만)

'실측'은 분석 패킷의 9회로 측정값(`[u1-sp1]` 7c757e8)이다. '기대'는 패킷의 손유도와 부분 실측에서 나온 값이다. 기대값은 test 기준값이 아니다(EP-5). U1b가 9회로로 재고, 다르면 42 행에 차이를 보고한다(EP-8).

| 규칙 | 발동 회로·대상 | 무동작 | 근거 |
|---|---|---|---|
| 1.12.1 복합 diode | **실측**: sf_pushpull M5·M6·M7·M8·M13·M14(묶음 {M6, M5, R1a}, {M8, M7, R1b}, {M14, M13, R1c}, 기준 M6·M8·M14), 파일럿 M58·M63(묶음 {M58, M57}, {M63, M64}) | **실측**: 나머지 7회로 0 | 패킷 C.3·D.3 |
| 1.12.1 → DC 역할 | **기대**: sf M9·M17·M11·M16·M20 = 바이어스 전류원(미러 출력, AC는 K8). sf J-U3-c 3그룹 해소. ngcc {M8, M14}는 남는다(기준 없는 그룹 → 40 §3.2-3 `dc_role` 사실) | -- | 패킷 D.4·D.6, F.3 |
| 1.12.1 → 루프 분류 | **기대**: sf `record_only` 9개 → `composite_diode_internal`, 파일럿 레플리카 루프 → 같음 | -- | 패킷 D.3 |
| 1.12.2 feedforward | **기대**: ngcc FF1 = {M6B, M6A, M7}(bias M5, 탭 ND, merge Vout, B_b = 1단), FF2 = {M14}(탭 V1, merge Vout, B_b = 2단). 주경로 V1 → V2 → Vout. 복합 블록 0 | **기대**: 나머지 8회로 0(sf M17·M20은 merge가 블록 출력노드가 아니라서 K8) | 패킷 A.2·A.4(경로 부호 다섯 개가 모두 같은 위상) |
| 1.12.3 보상 내부 루프 | **기대**: ngcc `loop:M8:V1`, nmcnr `loop:M201:NodeM2` → 루프 뷰 0, `undeclared_loop_constraint` 해소(두 회로 모두 `pm_ss_deg` 선언 있음) | 파일럿 CM 루프는 (b) 불만족으로 루프 뷰 유지 | 패킷 B.2·B.4 |
| 1.12.4 극성 | **기대**: 파일럿 CM 루프 뷰 = −1(DC 사이클 4개), Cc–Rz 우회 사이클 2개 = `ac_only`. ngcc ×2·nmcnr ×4 미정의는 1.12.3으로 사라진다 | -- | 패킷 F.1 |
| 1.12.5 L 주인 | **기대**: ngcc {M8, M14} → M8(`main_path_signal`), sf 3동치류 → M6·M8·M14(`current_source_member`) | -- | 패킷 F.3·F.4 |
| 1.12.6 교류접지 예외 | 파일럿 Vbias2, 뷰 `loop:M37a:Voc`. 패킷 C.4 scratch 실측: 정지·혼재 3건 해소 | -- | 패킷 C.4·C.5 |
| sf 전체 | **기대**: 이득 블록 {Y} 하나 + 버퍼 블록 {vout}. `composite_dag_not_chain`·`record_only`·혼재 8건 해소. 남는 혼재가 있으면 그 넷만 `drive_kind` 사실(40 §3.2-3) | -- | 패킷 D.4. DC 역할만 바꾼 scratch 실측에서는 DAG 1·record_only 9·혼재 3이 남았다. 그 원인인 미러 인식은 1.12.1-2가 바꾼다 |

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
- feedforward 기여(§1.12.2-4): merge 블록 국소 해에 FF 묶음을 합류 입력으로 넣고, 탭 전압을 그 입력으로 준 해다. 주경로 블록 gain에는 넣지 않는다.

### 2.2 잔차

평가마다 다음을 S2 `ss`와 S3 evals 요약에 쓴다.
- `gain_residual_db = gain_ss_db(전회로) − Σ 블록 gain`. feedforward 묶음이 있는 뷰는 `gain_ss_db − 20·log10|A_decomp|`이고, A_decomp는 §1.12.2-4의 분해 합성값이다. 이때 `ss.ff_contrib`도 함께 쓴다
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

**파일**: `E/metrics/achievability.py`(진입점), `curve_checks.py`, `block_gain_bound.py`, `dof_report.py`, `area_lower_bound.py`, `headroom_bound.py`(§4.6).

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

**feedforward가 있는 뷰**(§1.12.2-6): 블록은 주경로 블록만이다. 비교식은 dB 합 대신 20·log10(Π A_i,max + Σ_ff A_ff,max) + b_GB4 < G_target이다. 이때 b_GB4는 주경로 블록 b의 합이다. FF 상한이 하나라도 미상이면 판정하지 않는다. FF 경로는 주경로와 같은 위상으로 더해질 때 이득을 키우므로 이 합이 상한이다.

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

### 4.6 헤드룸 달성가능성 (사용자 결정 2026-10-08 Q4 (6), 탐색 전 보고)

**왜 필요한가**: sky130 1.8 V에서는 pfet |VT|가 L bin에 따라 크게 뛴다(gm/ID 15에서 VSG 0.68 / 0.81 / 1.02 V at L 0.15 / 0.18 / 0.5 µm, 제안서 §0.4). 그래서 '게이트-소스로 쌓이는' 경로(입력 두 극성 공유 gate, follower 스택, PMOS 입력쌍)는 L bin 선택이 곧 DC 성립 여부다. 이 사실을 탐색이 수백 번 실패한 뒤가 아니라 탐색 전에, 유도와 함께 보고한다.

**대상(구조로 정한다, 이름 없음)**: S1의 레일-레일 경로 중 VGS 엣지를 하나 이상 지나는 DC 경로 전부. 각 경로에 대해 아래 세 창을 계산한다.
- 출력 창: 출력 노드에 닿는 경로들로 [V_lo, V_hi]의 최대 폭(`swing_out_v`의 상한).
- 입력 창: 입력 셀 gate에서 레일까지의 경로들로 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi]의 최대 폭(`icmr_v`의 상한). 레일 밖 입력은 허용하지 않는다(사용자 결정 Q4 (4)).
- 버퍼 창: 버퍼 묶음(§1.9) 입력 노드가 DC로 성립하는 구간의 최대 폭.

**상한 계산(인증)**: 경로 폭 = ΔV_rail − Σ_VGS엣지 |VGS|_min − Σ_VDS엣지 (VDSAT_min + tol_VDsat). |VGS|_min·VDSAT_min은 그 소자 kind의 LUT 격자 전수(gm/ID, L bin, VS 축은 bulk 기본 규칙이 정하는 VSB 범위)에서의 최솟값이다. 서로 다른 소자를 독립으로 최소화하므로 실제 폭의 **상한**이다. 등식(`equal_vgs`, L 동치류)으로 묶인 소자는 한 축으로 센다(§4.2와 같은 규칙). 격자 곱이 N_S를 넘으면 '미상'이다.

**판정**(§4.3과 같은 규칙):
- 선언 제약(`swing_out_v >=`, `icmr_v >=`, `icm_margin_v >= 0`)의 대상 창이 **모두 인증**되었고 상한 + 분해능 < 목표면 `InfeasibleTargetError`(exit 3, 사유 `headroom_unattainable{metric, window, upper_bound, target, derivation}`)이다.
- 선언 제약이 없는 창(포화 전용 -- SPICE 합격 조건 '모든 MOS 포화'에만 걸리는 버퍼 창 등)과, 입력 DC가 SP-2 대기라 `icm_margin_v`를 판정할 수 없는 경우는 **보고만** 하고 정지하지 않는다.
- 산출 `headroom_achievability[{path, window_kind, upper_bound_v, binding_devices, best_row{gm_id, L_bin, VSB}, status: certified|unknown, verdict}]`. 각 행에 유도(경로 엣지 목록과 엣지별 최솟값의 출처 LUT 칸)를 함께 적는다.

**알려진 사례**(제안서 §2.4·§7·§8·§9 추정 -- W 5 µm 한 슬라이스·bulk = 레일 가정이다. **test 기대값이 아니다**, 기대값은 오라클 DC 스윕과 test 작성 주체가 만든다):

| 회로 | 경로 | 제안서 추정 |
|---|---|---|
| current_reuse(파일럿) 입력단 | 두 극성 입력이 같은 gate: VDSAT5 + VGS4 ≤ Vin ≤ VDD − VSDsat6 − VSG1 | 창이 pfet 최단 bin(L 0.15 µm)·nmos 약반전에서만 열린다(+0.14 V), L 0.18 −0.02 V, L 0.5 −0.15 V |
| nmcnr_amplifier 입력 | Vin,max = vdd − VSDsat101 − VSG102 | L ≥ 0.5 µm에서 −0.26 ~ −0.48 V → 입력 DC 0 V(agnd 관례, SP-2 대기)는 창 밖 |
| sf_pushpull_output_opamp 출력 버퍼 | Y ∈ [VGS19 + VDSAT20, VDD − VSDsat17 − VSG18] | L 0.15 +0.11 V, L 0.18 −0.12 V, L 0.5 −0.32 V. 선언 입력 DC 0.9 V도 Vin,min 0.83–0.99 V에 걸린다 |
| pushpull_follower_buffer | vin 창 = [VDSAT6 + VGS4, VDD − VSDsat5 − VSG3] | 위와 같은 식·같은 수치. Rout ≤ 1 kΩ 선언과 충돌 가능 |

**후속 처리**: bulk 기본 규칙(NMOS = 최저 레일, PMOS = 최고 레일)은 유지한다(사용자 결정 Q4 (6)). 입력 DC와 버퍼 구성은 아래 J-E 결정으로 닫혔다.

**입력 DC 정책(J-E, 사용자 결정 2026-10-08)**: 입력 DC는 회로가 아니라 사용 환경이 정하는 값이다. 회로가 정하는 것은 창이다.
- **SP-2 (c) 창 안 자유 변수**: 입력 DC가 `pending: SP-2`인 회로는 값을 지어내지 않는다.
  - 입력 공통모드를 W4 자유 변수 y_icm으로 둔다. 범위는 입력 창 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi]이고, 경계는 봉인 시점 값이며 tol을 포함한다.
  - `icm_margin_v`는 해의 y_icm에서 계산한다. 결과 JSON에 `required_input_cm_v{value, window}`를 보고한다.
  - '창 중앙값'을 숫자로 선언하지 않는다(EP-4).
  - agnd 0 V 관례는 이 정책의 회로에 적용하지 않는다.
- **선언 입력 DC 유지**: 입력 DC가 선언된 회로는 그 값을 쓰고, `icm_margin_v >= 0`을 제약으로 둔다(40 §9.2).
  - 위 판정 규칙에 따라 창이 인증되었고 상한 밖이면 exit 3이다.
  - 출력 버퍼 창(follower 스택)은 선언 제약이 없어도 **탐색 전 실현가능성 보고**로 낸다. 이것은 기존 '보고만' 규칙과 같다. 이 보고는 단계 A 보고서에 별도 행 `buffer_window_report`로 출력한다.
- **짧은 L bin 경고**: 입력 창 상한이 인증된 상태에서, 그 창을 정하는 경로의 어느 kind가 **최단 L bin에서만** 양의 폭을 낼 때가 있다. 그때는 경고 `icmr_window_short_l_bin{kind, bin, upper_bound_by_bin}`를 낸다.
  - 이 경고는 탐색을 막지 않는다. 탐색 공간의 구조 정보로 보고에 싣는다.
  - 창이 모든 bin에서 비면 기존 판정 규칙(제약 있으면 exit 3)을 따른다.
  - 회로별 적용은 40 §9.2 표에 있다.

**파일**: `E/metrics/headroom_bound.py`(진입점 `achievability`가 부른다).

**상태**: 4.1은 PART(분류는 있고 매핑이 없다). 4.2~4.6은 MISS.

---

## 5. FR-4 -- 층 0 gain 예산 조합 front와 `gain_budget_db` (MOD6)

정본은 DEC-71 (1)~(8), DEC-73, DEC-77, DEC-03이다.

**파일**(`E/search/`): `layer0_budget.py`, `gain_bins.py`, `local_candidates.py`, `local_front.py`, `combo_dp.py`, `assembly.py`, `budget_override.py`, `eval_budget.py`.

### 5.1 활성 조건

**활성**: 다음 셋이 모두 맞을 때 층 0 gain 예산을 돌린다.
- gain 제약 `gain_ss_db >= G`가 있다.
- 그 전달 뷰에 이득 블록이 하나 이상 있다.
- `review_needed`가 없다.

**예산 대상**: 주경로 블록만이다(§1.12.2-4, J-A). feedforward 묶음은 bin·조합 DP·`gain_budget_db`에 항목이 없다. 조립점에서 FF 묶음 소자는 출발 구간(§6.5, r_ff = 1 관계)의 값을 쓰고, 그 기여는 §2 경로 기여로 계산해 조합 순서의 잔차에 넣는다.

**이득 블록 없이 버퍼 블록만 있는 경우**: 선언된 `rout_ss_ohm`을 국소 AC 제약으로 쓴다(DEC-71 (3)).

**gain 제약도 rout 제약도 없는 경우**(H2):
- 문제: 국소 문제에 AC 제약이 없어 해가 최소 크기로 자명해진다.
- **처리**(사용자 결정 2026-10-08 Q5b. DEC-71 (3)의 '사이징 대상에서 뺀다' 대신 적용):
  - 층 0을 끄고 '층 0 무동작'으로 보고한다.
  - 시작점은 출발 구간(§6)에서 만든다.
  - 탐색 결과는 **'성능 판정 보류'**로 표시해 보고한다. 회로를 사이징에서 빼지 않는다.
  - 현재 해당 회로: common_gate_amplifier, folded_cascode(40 §9 Q5 표). 잡음 가드 `noise_excess_th` 행만 있는 경우도 gain 예산은 동작하지 않는다.

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

**고정 입력**(K1·K3·K8, 블록을 가로지르는 L 동치류):
- 첫 회차에는 §6 출발값을 쓴다. LR5 knee 앵커는 **추가 후보**로 L 축에 넣는다.
- 이후 회차에는 직전 조립점 값을 쓴다.
- 근거: 사용자 결정 2026-10-08 Q1, R29 수용.

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

**matching·헤드룸**(사용자 결정 2026-10-08 Q3·Q4): 절대 offset 제약이 있으면 matching L 하한(§6.4-2), offset 구조 가드가 있으면 부하 gm/ID 상한(§6.4-2a), 스윙·ICMR 제약이 있으면 헤드룸 예산 분할(§6.2)을 계산한다.

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

**스윙·입력 범위 제약에서 V_lo·V_hi 정하기**(사용자 결정 2026-10-08 Q4, 정의는 40 §3.8-3):
- `swing_out_v >= s`: 출력 노드마다 요구 반폭 h = s/2(단일 출력) 또는 s/4(차동 출력, 출력마다). 출력 DC V_o가 spec에 선언되어 있으면 V_hi = V_o + h, V_lo = V_o − h. 선언이 없으면 위·아래 예산 합 = ΔV_rail − 2h로 두고, 둘의 나눔은 위·아래 부분 기둥의 최소 요구(Σ(VDSAT_j,min + tol_VDsat,j))에 대한 남는 여유의 최솟값이 가장 크도록 정한다(계산값, 상수 없음).
- `icmr_v >= w`: 입력 경로 기둥(입력 셀 gate에서 레일까지의 VGS·VDS 엣지 경로)의 가용 폭을 ΔV_rail − w로 두고 같은 식으로 역산한다.
- `icm_margin_v >= 0`이고 입력 DC V_icm이 선언된 회로: 입력 경로의 위쪽 예산 = V_rail,hi − V_icm, 아래쪽 예산 = V_icm − V_rail,lo.
- 경계의 여유는 사용자 SPICE 포화 규칙 VDS ≥ VDSAT에 LUT `tol_vdsat`를 더한 것뿐이다. 3σ 같은 통계 관례는 쓰지 않는다(사용자 결정 Q4 (4)).
- 이 구간이 비면(필요 폭 > 가용 폭) 41 §4.6 헤드룸 달성가능성 보고와 같은 사실이다. 출발 구간은 충돌 레코드로 남기고 자르지 않는다(§6.6).

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
2. **matching 하한**(사용자 결정 2026-10-08 Q3 "q3,q4는 네 제안대로 해", 근거 `_drafts/engine/matching_swing_spec_proposal.md` §0·§2.3): **절대 offset 제약**(`offset_in_sigma_mv <= 값`, 현재 파일럿 3.3 mV)이 있는 회로에서만 활성이다. 구조 가드(`offset_excess`, §6.4-2a)만 있는 회로는 L 하한이 아니라 부하 gm/ID 상한으로 간다.
   - **mismatch 모델(옛 식 대체)**: 옛 식 A_min = (A_VT² + A_β²/(gm/ID)²)/σ² 는 `vth0` 한 항과 β 한 항만 본다. ngspice 감도 실측(제안서 §0.3)에서 `toxe`는 β보다 Vth로 더 크게 들어가고(BSIM4 k1ox 경로, n 2.2–4.1·p 2.3–6.5 mV·µm로 `vth0` 항과 같은 크기), nfet 약반전에서는 `voff` 항이 `vth0` 항을 넘는다. 옛 식은 nfet을 1.2–2.4배, pfet을 1.05–1.4배 과소평가한다. 그래서 **유효 계수 A_eff**로 바꾼다.
     - 단일 소자 게이트 환산 σ: σ_VGS(W, L, 점) = √(Σ_k (DVGS_k(L, 점) · slope_k(bin(W, L)) / slope_k(bin_ref))²) · √(W_ref·L_ref) / √(W·L).
     - k는 mismatch 블록의 `*_slope_spectre` 변수 **전수**다(`vth0`, `toxe`, `voff`, `nfactor` 등 카드가 쓰는 것, lint·wint는 slope 0이라 0 기여). 같은 ID에서의 ΔVGS로 정의하므로 β 경로(1/(gm/ID)에 비례)와 Vth 경로가 한 열에 함께 들어간다.
     - 쌍: σ_ΔVGS,pair = √2·σ_VGS(두 소자 독립). A_eff(L, gm/ID) = σ_ΔVGS,pair·√(W·L)이고 읽는 쪽에서 계산한다(열로 저장하지 않는다).
     - DVGS_k는 §6.4-2b의 LUT 감도 열에서 읽는다(상수 표를 박지 않는다).
   - **slope 출처**(사용자 결정 2026-10-08 Q2, 이번 Q3로 bin 규칙 보강): PDK `C:/pdk/sky130_fd_pr/cells/{nfet,pfet}_01v8/sky130_fd_pr__*_01v8__mismatch.corner.spice`를 파싱한다.
     - 모델 카드는 파라미터를 `p = p0 + p_slope·(slope_spectre)/√(l·w·mult)` 꼴로 흔든다(`toxe`는 toxe0을 곱한 상대값).
     - **bin마다 쓰는 slope 이름이 다르다.** 모델 카드(`*__tt.pm3.spice`) `.model` 블록마다 lmin/lmax/wmin/wmax와 그 블록이 쓰는 slope 이름(`vth0_slope` / `vth0_slope1`, `toxe_slope` / `toxe_slope1` 등)을 읽어 LBinMap과 같은 bin 지도에 붙인다. 예(제안서 §0.1 전수 집계): pfet L < 0.5 µm 36 bin은 `vth0_slope1` = 7.356e-3(L ≥ 0.5 µm의 5.856e-3 대비 +26 %), nfet L 4–8 µm·좁은 W 4 bin도 `vth0_slope1`. 옛 `legacy/sizing_recipe.py:3073`은 pfet에 5.856e-3 하나만 썼다(결함, 대조 기준선으로만 기록).
     - 참고 유도값(vth0 항만, 대조용): A_VT = √2·`vth0_slope` = nfet 4.75, pfet 8.28(L ≥ 0.5) / 10.40(L < 0.5) mV·µm. A_β = √2·`toxe_slope` = nfet 0.487, pfet 0.628 / 0.911 %·µm. LUT 감도 열의 `vth0` 성분은 이 값과 같아야 한다(U3 test (c)).
   - **단위 확인**: `models/all.spice` `.option scale=1.0u`라 l·w는 µm²다. 구현 첫 커밋에서 ngspice 소자 쌍 Monte Carlo(mismatch 블록 변수를 소자마다 gauss로, 오라클 측·엔진 비의존)로 σ(ΔVGS at 같은 ID)를 재고 A_eff 식과 비교한다. 그 비교를 test로 고정하고, 확인한 단위와 출처(파일 sha256·행)를 `core` PDK 선언에 기록한다.
   - **하한**: 출발 단계의 입력 셀 몫 σ_share = σ_target/√2(입력 셀 분산 = 나머지 분산, §6.4-2a 가드와 §7.5 잡음과 같은 등분 원칙 -- 새 상수가 아니라 '부하 기여 ≤ 입력쌍 기여'의 경계). 입력 셀 소자 면적 하한 A_min(L, gm/ID) = A_eff(L, gm/ID)² / σ_share², **L ≥ √(A_min·IDu/I)**. A_eff가 L에 의존하므로 §6.4-1처럼 bin을 오름차순으로 훑고 bin 안에서 bisection한다.
   - 판정은 이 하한이 아니라 봉인 스냅샷의 `offset_in_sigma_mv`(40 §3.8, MNA 전회로)가 한다(EP-7).
2a. **offset 구조 가드 → 부하 gm/ID 상한**(`offset_excess <= √2` 회로): 부하 소자 k의 입력 환산 분산 비 Σ_k (gm_k·σ_VGS,k)² / Σ_in (gm_in·σ_VGS,in)² ≤ 1이 되도록 부하 gm/ID를 상한으로 둔다. gm_k/gm_in은 §6.5 매크로 모델 전류 비로 쓴다(§7.5 잡음 가드와 같은 방법). §6.3 속도 상한·§7.5 잡음 상한과 교집합하고, 헤드룸 하한(§6.2)과 충돌하면 충돌 레코드로 남긴다.
2b. **LUT mismatch 감도 열**(U3): 생성기 `assets/sky130_lut_sweep.py`에 mismatch 모드를 더한다.
   - 방법(제안서 §0.3과 같음): pm3 카드 복사본에서 변수 k의 `*_slope_spectre`를 0 → 1(인스턴스 기하의 1σ)로 바꾼 섭동 곡선과 기준 곡선을 같은 include·DUT 줄로 돌리고, 기준 곡선의 칸 ID에서 두 곡선의 VGS 차를 DVGS_k로 둔다(W_ref·각 L·DC LUT 축 격자).
   - **저장**: 새 버전 파일 `..._mismatch_r1.npz`(sha256, 생성 메타: 모델 경로·sha, ngspice 버전, 온도, 섭동 변수 목록)에 둔다. **공유 `lut_data`의 기존 v2 r2 파일은 고치지 않는다.** `lut_v2_location.json`에 새 항목으로 더한다. 로더는 v2 칸과 같은 키로 합쳐 노출한다.
   - **tol**: 칸별 `tol_mismatch`를 LOO로 계산한다(DEC-87 방법, 디스크 캐시 대상).
   - 감도 데이터가 없는데 offset 제약이 선언되면 `SchemaRejectedError(mismatch_lut_missing)`이다.
   - 한계 기록: 제안서 실측은 W 5 µm·|VDS| 0.9 V·VS 0 한 슬라이스였다. 생성기는 DC LUT 축(VDS·VS·W 슬라이스) 전체에서 잰다.
   - API(신규): `mismatch_dvgs(kind, w_key, L, VGS, VDS, VS) -> MismatchSens{dvgs: {param: V}, slope_ref: {param: value}}`.
3. **flicker 잡음 하한**(사용자 결정 2026-10-08, 파일럿 `noise_out_int_vrms` 제약에서 활성):
   - 출발 단계에서는 §7.5에 따라 (총 예산 − 스위치 kT/C 항)의 절반을 flicker 몫으로 보고, 이를 출력 적분 예산으로 둔다.
   - 입력 소자의 flicker 출력 적분은 Σ_in (K_k/(W_k·L_k))·∫ f^−EF_k·|폐루프 잡음 이득|² df이다. K는 §7.2의 A·W·L이고 W에 무관하다. 적분은 매크로 모델 폐루프 응답으로 계산한다.
   - 위 식에서 입력 소자 면적 하한 A_min = W·L이 나온다. W·L = I·L²/IDu에서 **L ≥ √(A_min·IDu/I)**이다(matching 하한과 같은 꼴).
4. **속도 상한**: f_T(gm/ID_lo, L) ≥ f_np에서 L의 최댓값.
5. **면적 상한**(결정 11):
   - L ≤ √(A_budget · IDu / I)
   - W ≤ A_budget / L
6. **선택**: L = max(1, 2, 3의 하한)이다(2a는 L이 아니라 gm/ID 상한이다). LUT L 점이나 bin 안 값으로 맞춘다(LR3). 구간 끝이 다른 bin에 있으면 bin마다 후보를 하나씩 둔다.

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
- **feedforward·복합 블록**: 경로마다 VCCS를 하나씩 둔다. feedforward 묶음(§1.12.2)의 VCCS 값은 G_ff = r_ff · gm_in(B_b)이고, r_ff = 1(영점 상쇄 조건 후보)이다. 그 묶음 소자의 전류 출발값은 이 G_ff와 FF 경로 미러 비로 전파한다. 이것은 출발값이며, 판정은 외층이 한다(EP-7).

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

잡음 경로를 범위 안에 넣는다. 회로별 값은 사용자 결정 2026-10-08 Q11을 따른다(§7.1). 이 결정에 따라 P N1.2의 잡음 항목과 DEC-96 (3)의 '잡음·왜곡 미검증'은 잡음에 한해 바뀐다(계획서 DEC-96 정정 필요, 사용자 지시). 설계는 topology와 무관하다. 잡음원은 소자마다 붙고, 출력까지의 전달은 MNA adjoint로 계산하며, 회로별 식은 두지 않는다.

### 7.1 spec -- 잡음 제약 metric (닫힌 어휘)

metric 이름은 주파수를 숫자로 고르지 않도록 '평탄값'과 'corner'로 정의한다(근거: `_drafts/engine/noise_spec_proposal.md` §1).

| metric | 정의 | 단위 | 쓰임 |
|---|---|---|---|
| `noise_th_in_v2hz` | 입력 환산 **열잡음 평탄값**. 소자별 열잡음 성분을 전달 뷰의 MNA로 입력에 환산해 더한 값 | V²/Hz | 보고(모든 회로) |
| `noise_fc_in_hz` | 입력 환산 **1/f corner**. 입력 환산 flicker 성분이 열잡음 평탄값과 같아지는 주파수 | Hz | 보고(모든 회로) |
| `noise_excess_th` | `noise_th_in_v2hz` ÷ 입력 소자만의 열잡음 하한(같은 LUT γ). 입력 소자는 S1v에서 gain 제약 전달 뷰의 첫 이득 블록 input 셀로 구조적으로 정한다 | 무차원 | 구조 가드 제약 |
| `noise_out_int_vrms` | **폐루프** 출력 적분 잡음(rms). 선언된 되먹임 β로 루프를 닫은 테스트벤치(§7.3 폐루프 모드)에서 [f_lo, f_hi]를 적분한다 | V | 파일럿 제약 |

**회로별 선언**(사용자 결정 2026-10-08 Q11):

| 회로 | 잡음 선언 |
|---|---|
| current_reuse_telescopic_ota(파일럿) | `noise_out_int_vrms <= 300e-6`. 출처: `user_spec`(논문 Xie & Chen Table I 값 채택, 사용자 결정) |
| two_stage_ota, two_stage_ota_sf, folded_cascode, ngcc_3stage_ff, nmcnr_amplifier, sf_pushpull_output_opamp, common_gate_amplifier | `noise_excess_th <= 2`(가드: 부하 잡음 ≤ 입력 잡음, `user_spec`). 그리고 `noise_th_in_v2hz`·`noise_fc_in_hz` 보고 |
| pushpull_follower_buffer | 제약 없음, 보고만(이득 ~1 버퍼라 잡음 스펙이 의미가 없음) |

**파일럿 적분 범위**:
- 하한 f_lo = LUT가 실측한 가장 낮은 잡음 주파수 점이다(외삽하지 않는다. 현재 1 Hz).
- 상한 f_hi는 유도한다. 폐루프 최고 극점보다 위에서 로그 격자로 올라가며, 꼬리 상계 PSD(f)·f(1극 이상 감쇠에서 성립)가 분해능²(이 metric의 resolution²) 이하가 되는 첫 주파수에서 멈춘다. 상한은 K_max번 두 배 확장이다.

**공통 규칙**:
- 제약 형식은 `{metric, op: "<=", value, source}`이다. `source`는 필수다.
- MOD5 레지스트리에 `MetricSignature`로 등록한다(`domain: ss`, `view_kind: transfer`).
- 단위 어휘 `v2_per_hz`, `hz`(기존), `ratio`, `v`를 `core/units`에 넣는다.
- 레지스트리 밖의 잡음 이름은 `metric_unknown`으로 거부한다.
- 옛 topology `sizing_roles.metrics.noise_v_rthz`(주파수가 없어 판정할 수 없음)는 새 로더가 읽지 않는다.
- 왜곡은 여전히 범위 밖이다.

### 7.2 LUT -- 소자 잡음 데이터 (PDK BSIM4 잡음 모델에서 특성화)

**모델 사실**(`noise_spec_proposal.md` §0, sky130 모델 카드를 bin 전수로 확인한 값):
- `fnoimod = 1`(unified flicker: NOIA/NOIB/NOIC, EF). 그래서 KF·AF는 쓰지 않는다(카드 값 kf = 0).
- `tnoimod = 1`(holistic thermal). γ는 모델 파라미터가 아니라 바이어스 함수다.
- `ef`: nfet 0.84, pfet 1.0.
- 따라서 γ·K를 상수로 가정하지 않는다. **LUT에서 칸마다 읽는다.**
- EF는 상수를 박지 않고 PDK 모델 카드에서 파싱해 `core` PDK 선언(출처: 파일·sha256·행)에 둔다.

**이미 있는 열**: LUT v2 r2(`lut_v2_location.json`이 sha256으로 고정)에 `SVG2_1HZ`, `SVG2_HF`가 있다. 게이트 환산 V²/Hz이고 각각 1 Hz, 100 MHz 값이다.

**추가 특성화**(사용자 결정 Q11: 저주파 점 추가):
- 100 MHz 점은 fT가 충분하지 않은 칸(긴 L, 약반전)에서 Cgd 피드스루 때문에 게이트 환산값이 작게 나온다. 그래서 중간 주파수 점을 더 잰다.
- 점 위치를 상수로 박지 않는다. 기존 두 점 사이를 로그로 이분해 점을 추가한다. 각 칸에서 아래 '열잡음 평탄값 B 추정' 조건을 만족하는 점이 하나 이상 생길 때까지 반복하고, 상한은 K_max다.
- 측정은 ngspice `.noise`로 한다. 단일 소자 DUT 줄과 include는 생성기와 같다.
- 축 격자는 DC LUT의 (L, VGS, VDS, VS)와 W 슬라이스를 그대로 쓴다.

**분해 규칙**: S_vg(f) = A/f^EF + B로 둔다.
- A = S_vg(1 Hz) − B.
- B(열잡음 평탄값)는 특성화 점 중 피드스루 오차 (ω·Cgd/gm)²가 그 칸의 tol 이하인 **가장 높은 주파수 점**에서 A/f^EF를 빼서 구한다. Cgd와 gm은 같은 LUT 칸에서 읽으므로 새 상수가 없다.
- 조건을 만족하는 점이 없으면 그 칸의 B는 '미상'이다. 그 칸을 쓰는 잡음 metric의 resolution을 무한대로 두고 판정을 보류한다.

**파생량**(읽는 쪽에서 계산하고 열로 저장하지 않는다):
- γ_eff = B·gm / (4kT)
- K = A·W·L(V²·m²): §6.4-3의 1/f L 하한에 쓴다.

**저장**:
- 추가 주파수 점은 **새 버전 파일** `..._noise_r1.npz`에 둔다. sha256과 생성 메타(모델 경로·sha, ngspice 버전, 온도, 코너, 주파수 점)를 함께 기록한다.
- 기존 v2 r2 파일은 고치지 않는다. `lut_v2_location.json`에 새 항목으로 더한다.
- 로더는 v2의 `SVG2_*`와 새 파일의 점을 합쳐 노출한다.
- 잡음 데이터가 없는데 잡음 제약이 선언되면 `SchemaRejectedError(noise_lut_missing)`이다.

**tol**: 칸별 `tol_noise`를 LOO로 계산한다(DEC-87 방법). 디스크 캐시 대상이다.

**API**(신규): `noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams{A, B, ef, b_status}`. 옛 `SID_1F`는 단위가 잘못되어 있으므로 읽지 않는다.

### 7.3 metrics -- 봉인 스냅샷 잡음 해석 (MOD5)

**잡음원**:
- MOS: gate–source 사이에 게이트 환산 전압 잡음원을 하나 둔다. 값은 S_vg(f) = A/f^EF + B다. 이것을 드레인 전류 잡음 gm²·S_vg로 바꿔 drain–source에 스탬프하는데, 두 방식은 같은 양이다.
- 저항: 4kT/R.
- 값은 봉인 스냅샷 `ss`의 동작점에서 LUT로 읽고 W 배율을 적용한다.
- **포함 범위**(사용자 결정 Q11: CMFB·바이어스·스위치 포함): 회로의 모든 MOS와 저항이다. 파일럿 폐루프 모드에는 아래 스위치 kT/C 항을 더한다.

**폐루프 모드**(`noise_out_int_vrms`, 파일럿):
- 선언된 되먹임 요소(feedback {Cf1, Cf2}, spec)로 루프를 닫는다. Cs는 입력 부하로 남긴다(CI-10 결정). 이 상태에서 증폭 위상의 출력 잡음 PSD를 구한다.
- **스위치**: 스위치 on-저항의 열잡음이 샘플링 커패시터에 남기는 값은 R과 무관하게 kT/C다. 그래서 spec 테스트벤치 선언 `noise_testbench.sampling_caps[]`(요소 이름과 출력 전달 이득 출처)마다 kT/C_s × (그 커패시터에서 출력까지의 저주파 전달 이득)²를 출력 적분에 더한다.
- 이 항을 따로 기록해, 엔진(소자 잡음)과 오라클(스위치 포함 실제 SC 테스트벤치)의 구성 차이가 드러나게 한다.

**전달**: as-built MNA(같은 (G, C) 조립)의 adjoint를 쓴다.
- 출력 감지 노드에서 단위 전류를 주입해 adjoint 해를 한 번 구한다. 그러면 모든 잡음원의 전달 함수 Z_k(jω)를 한 번에 얻는다.
- ω마다 풀이 1회이며, 조립은 다시 하지 않는다(WP-23).

**입력 환산**: S_in(f) = Σ_k |Z_k|²·S_k(f) / |H(jω)|². H는 선언된 전달 뷰의 전달함수(gain metric과 같은 뷰)다.

**산출**:
- `noise_th_in_v2hz` = Σ_k |Z_k/H|²·gm_k²·B_k이다(열잡음 성분만).
- `noise_fc_in_hz`는 입력 환산 flicker 합 Σ|Z_k/H|²·gm_k²·A_k/f^EF_k가 열잡음 평탄값과 같아지는 f다. 1-D 근(`bracket_root`)으로 구한다.
- `noise_excess_th` = `noise_th_in_v2hz` / (input 셀 소자만의 같은 합)이다.
- `noise_out_int_vrms` = √(∫_{f_lo}^{f_hi} S_out df + 스위치 항)이다. 적분은 로그 격자 사다리꼴로 하고, 오차가 분해능 이하가 될 때까지 이분 세분한다(상한 K_max).
- 소자별 기여 표 `noise_contrib[{device|element, thermal, flicker, share}]`를 낸다.

**분해능**: metrics §9와 같은 방식이다. LUT 잡음 열의 tol_noise와 소신호 파라미터 tol이 adjoint 감도를 거쳐 전파된 값을 `MetricResult.resolution`으로 둔다.

**파일**: `E/metrics/noise_sources.py`, `E/metrics/noise_analysis.py`.

### 7.4 search -- 제약 행

다른 ss 제약과 같은 형식이다. 판정 단위는 c = (value − metric)/resolution이고, 풀이 척도는 40 §7.2를 따른다. 외층 전회로 판정 위치(DEC-74)도 그대로다.

### 7.5 출발 구간 -- 잡음

**`noise_excess_th ≤ 2` 가드**:
- 부하 소자 k의 열잡음 비는 (γ_k·gm_k)/(γ_in·gm_in)이다. 이 비의 합이 1 이하가 되도록 부하 gm/ID를 상한으로 둔다(강반전 쪽).
- 매크로 모델(§6.5)의 전류 비로 gm_k/gm_in = ((gm/ID)_k / (gm/ID)_in)·r_k이다. 여기에 LUT γ를 넣어 부하 gm/ID 상한을 역산하고, 그 결과를 §6.3 속도 상한과 교집합한다.
- 헤드룸 하한(§6.2)과 충돌하면 충돌 레코드로 남긴다.

**파일럿 `noise_out_int_vrms`**:
- 폐루프 열잡음 적분은 매크로 근사로 v²_th ≈ 2·γ_avg·kT/(β·C_eff)·(1 + 부하 비)이다(`noise_spec_proposal.md` §2.2와 같은 꼴, C_eff는 §6.5의 보상 소자). gm이 소거되므로, 이 항은 보상 커패시터의 하한으로 작용한다. 하한 = 예산 중 열잡음 몫이 남도록 하는 최소 C_eff다.
- 예산은 나누지 않는다. 총 예산에서 kT/C 스위치 항을 뺀 나머지를 열잡음과 flicker가 함께 쓴다.
- 출발 단계에서는 둘을 같은 몫으로 시작하고, 판정은 §7.3 전회로 계산이 한다.
- flicker 몫은 §6.4-3 1/f L 하한(입력 소자 W·L)으로 간다.

**1/f L 하한**: §6.4-3.

### 7.6 오라클 -- ngspice `.noise` 대조

- 오라클은 엔진을 import하지 않는다.
- **개루프 metric**(`noise_th_in_v2hz`, `noise_fc_in_hz`, `noise_excess_th`): 같은 free 모드 동작점 테스트벤치에서 `.noise v(sense) <입력원> dec ...`로 잰다. excess는 입력 소자별 기여(`.noise` 소자별 출력)로 계산한다.
- **폐루프 metric**(파일럿 `noise_out_int_vrms`): 스위치·CMFB·바이어스를 모두 넣은 실제 SC 테스트벤치를 증폭 위상으로 두고 `.noise`로 출력 PSD를 얻는다. 적분 범위는 엔진과 같은 [f_lo, f_hi] 유도 규칙을 따른다(오라클이 독립적으로 계산한다). 샘플링 kT/C는 과도 기반으로 따로 잰다.
- **비교 허용오차**: 다른 metric과 같다. resolution과 `model_error_noise_*`(DEC-72)를 쓰고, 미측정이면 '판정 보류'다.
- **합격**: T5에 잡음 제약을 넣는다. `ORACLE_MEASURES`에 네 metric을 더한다.

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
def mismatch_dvgs(kind, w_key, L, VGS, VDS, VS) -> MismatchSens                                          # E/lut/mismatch_query.py  (§6.4-2b)
def headroom_bound(s1: S1, s1v: S1v, lut: LutSet, spec: SizingSpec, pdk: PdkDecl, *, count_budget: int) -> HeadroomAchievability  # E/metrics/headroom_bound.py (§4.6)
# J 공동분석(§1.12) -- 단위 U1b
def composite_diodes(projection) -> tuple[CompositeDiode, ...]                                        # E/graph/composite_diode.py  {members, reference, cascode_members, walk[]}
def feedforward_cells(model, view, blocks, cells, stage) -> FeedforwardResult                          # E/graph/feedforward_cells.py {main_path, cells[FeedforwardCell], ratio_candidates, findings}
def loop_roles(view_loops, transfer_views, declared_pm_views) -> tuple[LoopRole, ...]                  # E/graph/loop_roles.py  {loop_id, role: loop_view|compensation_internal|composite_diode_internal|bias_scc}
```

`build_s1v`의 as-built 서명(`[u1-sp1]`)은 `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None, stop_on_unsupported=True)`이다. U1b는 서명을 바꾸지 않는다. 단계 A가 `declared_loop_cuts`와 `structure`를 실제로 넘기도록 호출부를 고친다(40 §3.2-3).

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
| DOF(IC6) | (a) 사고19 픽스처 | `tests/metrics/test_ic6_dof.py` | over/under 판정 |
| 층 0 | (a) 2블록 toy에서 전수 조합과 비교 | `tests/search/test_combo_dp.py`, `test_layer0_budget.py` | DP front = 전수 front. `gain_budget_db` 출력. override 반영 |
| 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 필요조건 성질 |
| 매크로 모델 | (a) 이상 VCCS 2·3극점, 캐스코드 노드 포함 | `tests/search/test_macro_poles.py` | UGF·PM 근, 근 없음 기록, 바퀴 수렴 |
| 계수 예산 결정론 | (a) 같은 S0 두 번 | `tests/search/test_count_budget.py` | N_S가 시간과 무관하다. 사이클·Π 결과가 실행 간 같다 |
| 비단조 축 처리 | (a) 비율에 대해 내부 최대가 있는 toy | `test_block_gain_bound.py` | 세분 후 인증, 실패 시 미상 |
| 잡음 LUT | (c) 단일 소자 ngspice `.noise` 칸 중앙 대조 | `tests/lut/test_noise_query.py` | 칸 중앙 오차 ≤ tol_noise |
| 잡음 해석 | (a) 저항 분압·CS 한 단 손계산(4kTR, 4kTγgm), (c) ngspice `.noise` | `tests/metrics/test_noise_analysis.py` | 입력 환산 밀도·적분이 resolution 안 |
| 잡음 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 열잡음 gm 하한, 1/f L 하한 |
| mismatch 감도 LUT | (c) 단일 소자 ngspice 섭동(칸 중앙), (c) 소자 쌍 Monte Carlo | `tests/lut/test_mismatch_query.py` | 칸 중앙 오차 ≤ tol_mismatch. `vth0` 성분 = √2·slope 유도값(bin별 slope1 포함). MC σ와 A_eff 식이 MC 표본 분해능 안 |
| matching L 하한·offset 가드 | (a) 손계산 | `tests/search/test_start_intervals.py` | 절대 offset 회로에서만 L 하한 활성, 가드 회로는 부하 gm/ID 상한 |
| 헤드룸 달성가능성 | (a) 이름 없는 follower 스택·두 극성 입력 toy 손계산, (b) 소형 toy 격자 직접 전수 | `tests/metrics/test_headroom_bound.py` | 상한 ≥ 격자 직접 전수 최대 폭. 선언 제약이 인증 불가면 exit 3, 제약 없는 창은 보고만. 최단 L bin에서만 열리는 toy → `icmr_window_short_l_bin` 경고(정지 아님). SP-2 (c) 회로는 y_icm 범위 = 창 |
| 복합 diode(§1.12.1) | (a) 이름 없는 toy: 저항 자기바이어스 캐스코드 기준(MOS 2 + R), 레플리카(MOS 2, 전류원 고정), 단순 diode(무동작), 직렬 노드에 세 번째 전류 단자가 붙은 변형(무동작). (d) 9회로 | `tests/graph/test_composite_diode.py` | 발동 집합·기준/캐스코드 구분. 9회로 발동 = §1.13 실측 집합, 나머지 7회로 0. 같은 gs 묶음 나머지가 바이어스 전류원. 미러 입력 넷 확장. 묶음 내부 사이클은 `composite_diode_internal`, 루프 뷰 0. 이름 전단사 불변 |
| feedforward(§1.12.2) | (a) 이름 없는 3단 toy + 1단 우회 CS + 2단 우회 미러 가지, 우회 없는 병렬 합류 toy(무동작), 블록 내부 노드로 들어오는 바이어스 셀 toy(K8, 무동작). (b) 분해 합성값 A_decomp와 전회로 MNA 비교 | `tests/graph/test_feedforward_cells.py`, `tests/metrics/test_block_model.py` | FF 묶음·탭·merge·B_b. 주경로 블록 사슬. 복합 블록 0. A_decomp 잔차 ≤ 수치 분해능. `ff_ratio_candidates` 보고 |
| 보상 내부 루프(§1.12.3) | (a) 이름 없는 중첩 Miller 3단 toy(`pm_ss_deg` 선언 있음/없음), 순방향 밖 셀이 낀 되먹임 toy | `tests/graph/test_loop_roles.py` | 선언 있으면 루프 뷰 0. 없으면 `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`). 순방향 밖 셀 루프는 루프 뷰 유지 |
| 루프 극성·L 주인(§1.12.4·5) | (a) DC 사이클 + Cc 사이클 toy, 부호가 다른 DC 사이클 두 개 toy. 주경로 셀과 FF 셀이 같은 L 동치류인 toy | `tests/graph/test_loop_classify.py`, `tests/graph/test_l_classes.py` | 뷰 극성 = DC 사이클 극성. Cc 사이클 `ac_only`. 충돌이면 `loop_polarity_conflict`. 주인 = 주경로 stage 시작 셀(`main_path_signal`). name_order면 review |
| structure 사실 소비(40 §3.2-3) | (a) 사실 픽스처: confirm 일치/불일치/고아, override, stale(rule_hash 다름), 알 수 없는 concept | `tests/graph/test_structure_load.py`, `tests/pipeline/test_stage_a.py` | 일치 → ratified, 불일치 → `structure_fact_mismatch`, 고아 → `structure_fact_orphan`, stale → `structure_fact_stale`, 알 수 없는 concept → `SchemaRejectedError`(**거부 확인**). 단계 A가 spec 루프 선언의 끊는 넷을 `declared_loop_cuts`로 넘긴다(넘기지 않으면 실패하는 red test 먼저) |

**DoD 명령**(`$PY` = `C:\Python314\python.exe`):

```
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q -m "not slow"
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_structure_tables.py -q  # 9회로 S1v·A_max·Π·인증 비율 표
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests/integration/test_layer0_pilot.py -q      # front 점마다 allocated·realized·잔차
```

`test_structure_tables.py`는 `runs/<run_id>/structure_tables/`에 다음을 쓰고, 9회로 전부 표가 있는지 단언한다(N7).
- 9회로 S1v 표와 분기 발동 기록. 전용 coverage 파일은 만들지 않는다(R7).
- 블록별 GB4 표(블록 키, 격자 곱 Π, N_S, 인증/미상, A_max, b_GB4)
- 회로별 인증 비율(인증 블록 수 / 블록 수)

---

## 10. 상태 요약

| 절 | 항목 | OK | DEV | PART | MISS |
|---|---|---|---|---|---|
| §1 SP1 | 10 | 0 | 0 | 1(1.2 정적 교류접지) | 9 |
| §1.12 J 규칙 | 6 | 0 | 0 | 0 | 6 |
| §2 블록 모델·잔차 | 3 | 0 | 0 | 0 | 3 |
| §4 GB4 | 6 | 0 | 0 | 1(4.1 곡선 분류) | 5 |
| §5 층 0 | 9 | 0 | 0 | 0 | 9 |
| §6 출발 구간 | 6 | 0 | 0 | 0 | 6 |
| §7 잡음 | 6 | 0 | 0 | 0 | 6 |
