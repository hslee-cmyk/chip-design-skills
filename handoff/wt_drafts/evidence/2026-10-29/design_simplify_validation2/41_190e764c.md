---
template: design
version: 1.15.2
plan_version: 6.38.3
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
> **Date**: 2026-10-29 · **Status**: **design v1.15.2 -- 계획 v6.38.3(승인 O-170·O-172) 맞춤, 검증 대기**(40·42와 같은 판 -- 40 Status). 승인 질문 = §5.12.7. 판 이력(v1.15.2~v1.4) = design 이력 H41-16(`gain-budget-gmid-sizing.design.history.md`).
>
> 색인과 표기는 [40-engine](gain-budget-gmid-sizing.40-engine.design.md)을 따른다(`E/`, OK/DEV/PART/MISS). as-built 기준은 master `004b7d2`다.

**as-built 요약**: 이 문서의 설계 항목은 모두 MISS다. 쓸 수 있는 재료는 다음이 전부다.
- LUT 곡선 표의 격자 최대 gm/gds: `CurveRow.gm_gds_max`(`E/lut/lut_types.py`)
- LUT 곡선 검사: `curve_report`, `DcSlice.hermite_fc`(`E/lut/lut_set.py`)
- 전회로 MNA: `E/metrics/mna_build.py`, `mna_solve.py`
- pencil 극점: `E/metrics/pencil_roots.py`
- 외층 ε-제약 front: `E/search/eps_sweep.py`, `pareto.py`

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
 A8 start_intervals     : gm/ID·L·I 출발 구간, 7a KVL 고리 선택, 사다리(A3·A6, S0 쓰기 계획 `graph/kernel`, LUT를 읽는다) §6
 A9 block_bounds_l0     : 층 0 정의역 상한 A_i,max^L0(A6 국소 모델 + A8 S0 필드 `start.row`·`start.point`, 사용자 결정 L-12, '추정') §4.2
[단계 B -- 봉인 평가가 필요, S0당 1회, 평가 커널 컨텍스트 생성 뒤]
 B1 residual_probe      : 결합 잔차 분포 r̂ (표본 = dof_rank_sample_count) §2.4
 B2 dof_numeric         : 수치 rank (B1 표본 재사용)                     §4.5
 B3 layer0_budget       : 국소 front → 조합 DP → 조립(A6·A8·A9·B1을 읽는다) §5
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
- `(excite, sense)` 키는 as-built `E/authoring/spec_views.py`의 것을 그대로 쓴다.

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
4. **혼재**(한 소자의 drain과 다른 소자의 source가 만나는 노드)는 두 단계로 가른다(C-1, 사용자 결정 2026-10-12 "7절 권고대로", 보완 (가) 사용자 결정 2026-10-12 "1, 가로 해". 회로·소자 이름을 쓰지 않는 구조 규칙).
   - **(i) source 쪽 소자를 먼저 본다**: 그 소자의 drain이 교류 접지(레일)이고 gate가 그 뷰의 신호 노드(순방향 신호 경로 위 넷, §1.3)이면 source follower(CD)다. 그 노드는 **전압 구동**이다.
   - **(ii) 아니면(CG/cascode) drain 쪽 소자를 본다**(기존 C-1): drain 쪽 소자의 gate가 그 뷰의 신호 노드이면 **전류 구동**이다. 그 소자가 신호 전류를 그 노드로 밀어 넣기 때문이다. 그 gate가 신호 노드가 아니면(교류접지이거나 신호가 닿지 않는 바이어스 넷) 전압 구동이다. 그 소자는 그 뷰에서 고정 전류원이다.
   - **대체하는 규칙**: 옛 규칙 4 'drain 쪽 소자의 DC 역할로 가른다(바이어스 전류원 → 전압 구동, 신호 소자 → `review_needed`, 못 가르면 J 대기)'를 통째로 바꾼다. DC 역할은 뷰와 무관한 S1 사실이라 AC 신호 진입을 가르지 못했다. 바뀐 규칙은 뷰마다 신호 노드 집합(§1.3)과 교류 접지(§1.2)만 읽는다.
   - **예상 집합**(판정이 바뀌는 노드): `sf_pushpull_output_opamp` N910·N1112·N1516 → 전류 구동, `folded_cascode` Vg10 → 전류 구동(미러 출력 M10 → cascode M8, 옛 판정 오판). 유지: `sf_pushpull_output_opamp` N17·N20 = 전압 구동((i) follower M18·M19). 나머지 회로는 무동작이다. 40 §3.2-3 사실 표의 sf `drive_kind` override는 필요 없다.
   - **측정 의무**(구현 DoD): (1) 9 library 회로 발동표(뷰마다 혼재 노드, 옛 판정, 새 판정, 근거 `follower` | `cascode`). (2) `folded_cascode` 전후 비교 = 기록 + 판정 하나: Vg10이 전류 구동이 되고 M8이 stage 시작 셀이 아님(§1.6 규칙)이 유지됨을 확인한다(base에서도 M8은 시작 셀이 아니었다 -- stage 시작 셀 = M1, M2. ①-d 실측). 그 밖의 블록·stage·극점 노드 변화는 기록하고, Vg10 극점 노드 drive(voltage → current) 변화 밖이면 멈추고 보고한다. ①-d 실측: 변화는 Vg10 극점 노드 drive voltage → current 하나, 블록·stage는 9회로 불변. (3) 비교 키 = (회로, `view_key`, 노드). 예상 집합의 노드는 **그 노드가 혼재로 판정되는 모든 뷰에서** 판정이 바뀌어야 한다. 일부 뷰에서만 바뀌거나 예상 밖 (회로, 뷰, 노드)가 바뀌면(그 밖의 회로 무동작, WP-05) 구현을 멈추고 보고한다(§9 표 '혼재 노드 구동 종류' 행).
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
   - 낮음: source 단자나 diode가 붙은 노드. 출력 임피던스는 입력 신호를 0으로 놓고 보므로, gate가 교류접지이든 앞단이 구동하든(follower) source를 들여다보면 1/gm 차수다. pass 묶음 소자의 단자는 등급에 기여하지 않는다(pass 끝 노드는 반대편 종류를 상속, §1.6-5). Block.impedance와 극점 노드 등급은 이 한 규칙을 함께 쓴다(같은 뷰에서 등급이 둘이면 결함, U1 red test 1). 2026-10-08 정정: 옛 문구 "gate가 교류접지인 source 단자"는 follower 출력을 높음으로 만들어 물리와 어긋났다.
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
- (v1.15.2 개정 -- 계획 N6.35 E-33·card GV-1 범위 4, **원래 취지와 다름(계획 표지 -- U-24 '예외 확정' 변경)**) CM 루프도 다른 루프 뷰와 같은 규칙이다 -- 안정도 제약(`pm_cm_ss_deg`)이 미선언이면 GB2 출구 게이트가 탐색 전 정지(`undeclared_loop_constraint`, 사유·넷; 물리 결정자 = 되먹임 루프 안정도라는 같은 물리). 옛 'T_cm만 보고 + 경고 `cm_loop_unconstrained`'는 삭제(40 §5-3).
- 그 밖의 루프 뷰는 안정도 제약이 미선언이면 GB2 출구에서 `StructureUnresolvedError(undeclared_loop_constraint)`로 정지한다.
- '선언'은 spec 루프 뷰 선언(`ViewDecl` kind loop의 끊는 넷)이 안정도 제약 행에 쓰인 것이다. 단계 A 진입점이 그 끊는 넷 목록을 `build_s1v(declared_loop_cuts=...)`로 넘긴다(40 §3.2-3 파이프라인 수정. `[u1-sp1]` `pipeline/stage_a.py`는 넘기지 않아 선언해도 정지가 풀리지 않는다).

### 1.9 버퍼 묶음, 출력 방향, 복합 블록

- **R(u)**(DEC-63): CD 병렬 합류(②)에서는 §1.7의 ①보다 먼저 판정한다.
- **출력 방향**(DEC-65): β/σ/κ와 push-pull·class-A 구분은 MOD3에서 구조로 판정한다. 값은 40 §3.8-3(DC 동작 범위, as-built 모듈 `ls_fields`)이 낸다. β/σ/κ 분류가 남는지는 DE-1 착수 때 확인한다(계획 DE-1 소비자 표 -- `E/graph/output_direction.py`, 남지 않으면 출력 전용 선언 또는 삭제, 삭제는 승인). v1.15.0(계획 v6.38 DEC-104 R9·R13, U-115 닫힘 O-143 (5), O-144 J2): 구조 분류(class-A/AB)는 값 규칙을 가르지 않는다 -- 방향별 공급 능력 값은 늘 R9 LUT 극단 조회다. R10 공급 요구 하한(가정 붙은 필요조건 -- O-157 S4)의 적용 대상 판정만 S1v 구조 분류 β(모든 뷰) ∧ source 레일 넷을 card SB-1 블록이 READS한다(분류 필드 속성 아님 -- O-157 S4 J2)(β/σ/κ 기호와 별개 -- 기호 'β 셀'은 되먹임 계수와 겹쳐 쓰지 않는다).
- **feedforward 분리**(§1.12.2, J-A): 복합 블록 판정 전에 FF 묶음을 주경로 블록 구성에서 뺀다. FF 합류는 복합 블록으로 묶지 않는다.
- **복합 블록**(DEC-81): ②의 합류 노드가 전류 구동이거나 블록 출력노드면 묶는다. 묶은 결과 DAG는 사슬이어야 한다.
  - 묶음 크기 Π가 N_S를 넘으면 `unsupported_rule_branch`다. Π는 §4.2의 축 정의로 센 격자 곱이다. 계획 DEC-81은 'DEC-34 예산 식의 평가 수'를 쓴다. N_S로 두는 것은 L-10과 같은 이유(결정론, NFR-4)의 **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-65, 계획 DEC-81 정정)이다(§5.12.3 D5).
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

**상태**: MISS. 부분 대리물은 `E/authoring/_feedback_cuts.py`, `E/metrics/loop_cut.py`, `[ng-cmfb-pm] E/authoring/cm_partition.py`, `E/graph/matching_groups.py`다. SP1 본체는 `[u1-sp1]`(eae0292, 미병합)에 있다.

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
   - 주경로 최장 경로가 둘 이상이고 셀 집합이 다르면 `review_needed`(`main_path_ambiguous`)다. 이 판정은 FF 후보 묶음이 있는 뷰에서만 한다(as-built U1b 2026-10-09: 무조건 판정하면 push-pull 병렬 버퍼 가지(파일럿·pushpull·sf)에서 오발동한다. FF가 없으면 주경로를 고를 이유가 없다).
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
4. `name_order`: 남은 동률만 해당한다. `review_needed`(`l_owner_name_order`)로 올린다. **예외**(2026-10-09 오케스트레이터 결정): 동률 후보가 모두 같은 자기동형 궤도(U2 `automorphism_orbits`)에 들면 어느 쪽을 주인으로 골라도 구조상 같은 결과라 review를 올리지 않는다(정정 2026-10-09: nmcnr {M104, M105}는 단일 종단 미러 M108(diode)·M109(출력) 때문에 같은 궤도가 아니어서 이 예외에 들지 않는다 -- 독립 test·엔진 궤도 계산 확인).

**사실 `l_owner`가 이 순서를 덮어쓴다**(C-3, 사용자 결정 2026-10-12 "7절 권고대로"): `structure.json`에 그 동치류의 `l_owner` 사실(40 §3.2-3)이 있으면 1~4를 적용하지 않고 사실의 주인을 쓴다(override). 사실의 주인이 동치류 멤버가 아니면 `review_needed`(`structure_fact_mismatch`)다. 회로별 주인은 이 문서가 정하지 않는다. nmcnr {M104, M105}의 주인은 M105로 결정됐다(사용자 결정 2026-10-12 "C-3은 네 제안대로 해", 사실 파일로 적용, 40 §3.2-3).

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
| 1.12.1 → 루프 분류 | **실측(U1b, 2026-10-09)**: sf `composite_diode_internal` **3개**({N1,N5}, {N2,N7}, {N12,N13}). 옛 기대 9개는 U1 그래프의 `record_only` 수였고, 묶음 내부 혼재 넷(N56·N78·N1314)은 1.12.1-2로 혼재 판정을 하지 않아 사이클이 생기지 않는다. 파일럿 레플리카 쪽은 신호 사이클 0 | -- | 패킷 D.3 |
| 1.12.2 feedforward | **기대**: ngcc FF1 = {M6B, M6A, M7}(bias M5, 탭 ND, merge Vout, B_b = 1단), FF2 = {M14}(탭 V1, merge Vout, B_b = 2단). 주경로 V1 → V2 → Vout. 복합 블록 0 | **기대**: 나머지 8회로 0(sf M17·M20은 merge가 블록 출력노드가 아니라서 K8) | 패킷 A.2·A.4(경로 부호 다섯 개가 모두 같은 위상) |
| 1.12.3 보상 내부 루프 | **기대**: ngcc `loop:M8:V1`, nmcnr `loop:M201:NodeM2` → 루프 뷰 0, `undeclared_loop_constraint` 해소(두 회로 모두 `pm_ss_deg` 선언 있음) | 파일럿 CM 루프는 (b) 불만족으로 루프 뷰 유지 | 패킷 B.2·B.4 |
| 1.12.4 극성 | **기대**: 파일럿 CM 루프 뷰 = −1(DC 사이클 4개), Cc–Rz 우회 사이클 2개 = `ac_only`. ngcc ×2·nmcnr ×4 미정의는 1.12.3으로 사라진다 | -- | 패킷 F.1 |
| 1.12.5 L 주인 | **기대**: ngcc {M8, M14} → M8(`main_path_signal`), sf 3동치류 → M6·M8·M14(`current_source_member`) | -- | 패킷 F.3·F.4 |
| 1.12.6 교류접지 예외 | 파일럿 Vbias2, 뷰 `loop:M37a:Voc`. 패킷 C.4 scratch 실측: 정지·혼재 3건 해소 | -- | 패킷 C.4·C.5 |
| sf 전체 | **기대**: 이득 블록 {Y} 하나 + 버퍼 블록 {vout}. `composite_dag_not_chain`·`record_only`·혼재 8건 해소. 남는 혼재는 `drive_kind` 사실로 메우지 않는다(v1.8: §1.5-4 C-1 보완 (가)가 sf 혼재 넷을 구조로 가르고, 예상 집합과 다르면 구현을 멈추고 보고, 40 §3.2-3) | -- | 패킷 D.4. DC 역할만 바꾼 scratch 실측에서는 DAG 1·record_only 9·혼재 3이 남았다. 그 원인인 미러 인식은 1.12.1-2가 바꾼다 |

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
- 쓰임(40 §3.10.8 '결합 잔차의 쓰임', P N3.7):
  - (i) 진단 보고: 결과 JSON `diagnostics.residual_probe`.
  - (ii) 6c DoD 결합 잔차 표: 결과 JSON `residual_table[{block, metric, r_hat, r_spread, n_samples, seal_failures}]`.
  - (iii) 신뢰 한계: 잔차가 그 metric의 모델 오차 선언값(DEC-72)보다 크면, 그 블록 분해값을 할당 입력으로 쓸 때 `trust_limits[{block, metric, residual, model_error}]`를 함께 기록한다.
  - (iv) 층 0 조합 순서(§5.6).
  - 상한이 보장되지 않으므로 판정에는 쓰지 않는다(M2, DEC-74).

**상태**: MISS.

---

## 3. FR-3 연계

- 보상 `gm_req`(MNA 1-D 근)는 외층 판정에서 제약으로 쓴다(40 §3.5).
- 층 0 국소 고정점은 노드 C를 갱신하며 §6.5 매크로를 키워드 인자로 다시 풀어 블록 gm 요구와 보상 수동소자 시작값을 얻는다(§5.3.6).
- 조립점에서 `comp_approx_gap`을 기록한다(정의 §5.5).

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
- **v1.15.1 -- W-bin 슬라이스 포락(계획 v6.38.2 DEC-105 (2) 'W가 아직 없는 단계', card WB-1 범위 2)**: GB4는 전류가 정해지기 전이라 소자 W(따라서 W-bin 슬라이스)가 없다. 행마다 소자 파라미터를 그 kind의 도달 가능 슬라이스 전체(40 §3.7-A 8 `reachable_slices`)에서 읽고 **A_i,max 상계는 슬라이스별 gain의 최댓값**으로 둔다(상한이 실현 가능한 점을 자르지 않음 -- 상계 유지). found_db(하한 추정 -- 그 점에서 도달한 gain)는 격자 점마다 같은 포락의 **최솟값**(그 점이 어느 도달 가능 슬라이스로 실현돼도 도달하는 gain)으로 재고, 그 최댓값 점을 찾는다(계획 DEC-105 (2) '하한 양은 최솟값' 그대로; v1.15.1 '최댓값 행'은 계획과 달라 정정 -- gap §3-1. found_db는 g_i^(1) 분배 입력이라(§6.4-1) 그 변화는 card WB-1 변화표 원인 항목). 슬라이스 수만큼 행 평가가 늘어 격자 곱 Π에 슬라이스 축(그 kind 도달 가능 슬라이스 수)이 곱해진다 -- 예산 게이트 N_S 판정은 그 Π로 한다(새 상수 없음; 늘어난 Π로 미상이 늘면 card WB-1 변화표 원인 항목).

**예산 게이트**: 격자 곱 Π가 계수 예산 N_S(§0)를 넘으면(시간 무관, 결정론) 상한을 **'미상'**으로 두고 판정에 쓰지 않는다. 격자를 줄이지 않는 이유는, 줄인 격자의 최댓값은 상한이 아니기 때문이다. 이 처리는 P N3.7의 "LUT·구조만으로 상한을 계산할 수 없는 제약은 상한 미상"과 같다.

**분해능**: b_GB4,i = 최대 행과 그 격자 이웃 행들 사이 gain 차의 최댓값이다.

**GB5 재사용**: 보상 gm 요구로 다시 판정할 때는 이 표에서 gm 조건을 만족하는 행만 거른다. LUT 격자를 다시 돌지 않는다.

**버퍼 블록**: 같은 방법을 쓴다. 상한은 0 dB 이하다.

**층 0 정의역 상한 A_i,max^L0**(사용자 결정 2026-10-12 L-12 "GB4 블록 gain 상한 계산도 신호 소자 축만으로 축소", 재검증 Major-1 반영):
- **축 규칙**(§5.3.3 L-11의 자유 축과 같다):
  - 자유 축: S∪F 소자(§5.3.3)의 같은 VGS 묶음 VGS 축(= gm/ID 축), L 동치류 L 축 전부(L은 층 0에서 역산·LR5 격자로 움직인다, §5.3.5·§5.3.7), 전류·저항 축, 덮는 기둥의 W4 VDS 격자 축(VDS는 층 0에서 (c) 배분이 움직인다, §5.3.4. §4.2 표의 '기둥 VDS = W4 창 안의 LUT VDS 격자'와 같다).
  - 하나로 세기: matching 그룹(S1 `graph.matching_groups`의 derived `diff_pair`·`branch_symmetric`·`mirror`)과 자기동형 궤도로 묶인 소자의 VGS·VDS 축은 축 하나다(§4.2 '등식으로 묶인 것은 축 하나로 센다').
  - 고정: B 소자(§5.3.3)의 VGS 축과 모든 VS 축. 값은 S0 수준 필드 `start.row`(gm/ID·L)와 `start.point`(VDS, VSB)에서 읽는다(40 §2.4.8). VGS는 `vgs_for_gm_id`로 구하고 담는 LUT 격자 마디를 쓴다. 단계 B 기준점(봉인 평가)은 읽지 않는다(§0 DAG: A9는 단계 A).
- **계산**: §4.2와 같은 함수(격자 전수, 예산 게이트 N_S, 비단조 축 세분, 분해능 b)를 이 축에 적용한다. 단계 A9(A8 뒤)이고 결과는 S0 수준 필드다(40 §2.4.8 A9 행).
- **'추정' 표시**: 인증되어도 이 값은 B 소자를 출발값에 고정한 정의역 위의 최댓값이다. N3.7의 '봉인 가능 점을 모두 포함하는 상위집합 위의 상계'가 아니므로 늘 '추정'으로 표시한다(DEC-67).
- **쓰임**: 목표 bin 범위의 위 끝 후보로만 쓴다(§5.3.2: 위 끝 = max(A^L0 bin, 역산 실패 bin)). 첫 배분(§5.3.2, L-2)에는 쓰지 않는다. §4.3 exit 3과 §6.4-1 이득 L 하한은 축소 전 A_i,max만 읽는다(L-14).
- **실측(2026-10-12, as-built bd19cc6 코드 읽기 전용, `wt/_tmp_l0design/measure_v3.py`, 결과 `v3.jsonl`)**. N_S = 13,829,760(6회로 공통). 고정값은 as-built `start` 선택점(gm/ID·L)과 `CurveBook.points`(VDS, VSB, 40 §2.4.8에서 `start.point`가 된다)다.

| 회로 | 블록 | 축소 전 Π | A^L0 축 Π | 게이트 | A^L0 |
|---|---|---|---|---|---|
| common_gate_amplifier | vout | 1.9·10¹⁰ | 3.8·10⁷ | 초과 | 미상 |
| folded_cascode | out | 6.2·10⁵² | 7.8·10²⁹ | 초과 | 미상 |
| sf_pushpull_output_opamp | Y | 3.4·10⁸⁰ | 1.3·10⁴² | 초과 | 미상 |
| two_stage_ota | O1 / OUT | 1.7·10²² / 1.9·10⁹ | 3.0·10¹³ / 3.8·10⁷ | 초과 / 초과 | 미상 / 미상 |
| two_stage_ota_sf | O1 / OUT | 1.7·10²² / 1.9·10⁹ | 3.0·10¹³ / 3.8·10⁷ | 초과 / 초과 | 미상 / 미상 |

  - 재측정(실측(2026-10-12, as-built bd19cc6 코드 읽기 전용 + §6.7-1a 쓰기 계획 모사(같은 DC `input_tie` 엣지 제거), 'kvl 종속' 제외, `wt/_tmp_l0design/measure_v4.py`, 결과 `v4.jsonl`)): kvl 종속 VGS 축을 빼도 축 수가 같아 표 값이 그대로다.
  - 인증 수: 이득 블록 7개 중 **0개**. W4 VDS 축을 넣으면 가장 작은 블록(OUT, VGS 1 × VDS 2 × L 2)도 49²·18²·49 = 3.8·10⁷로 N_S를 넘는다. 그래서 지금 library에서 bin 위 끝은 모두 역산 실패 bin이 정한다(§5.3.2).
  - 직전 측정(VDS 고정, 단계 B 기준점 값)의 3개 인증과 그 값(48.8·54.5·52.8 dB)은 이 정의로 대체하며 쓰지 않는다. 그 값이 축소 전 `found_db`(61~68 dB)보다 낮았던 것이 '추정' 표시의 근거다.

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
- 변수: 노드전압, 소자 gm_id(P N3.7 이름. 새 엔진 좌표는 쓰기 소자 ln IDu(DEC-88)이고 강반전 분지에서 gm_id와 일대일이라 rank가 같다. 종속 소자 gm_id는 관계가 정해 변수가 아니다), L 동치류 L, θ 전류, DC 경로 저항.
- 등식: diode, `equal_vgs`, `stacked_vsb`, `kvl_branch`, KCL. (`budget_ref`는 없다: 옛 `budget_reference_device`의 예산 관계는 기둥 KVL과 노드 변수 하나로 이미 들어 있다, 계획 DEC-55·사용자 결정 2026-10-12 "다로 해")
- 방법: 변수와 등식의 이분 매칭으로 rank를 구한다.
- 판정: 매칭되지 않는 등식이 있으면 `overconstrained`이고 INFEASIBLE_TARGET이다. 남는 변수가 있으면 `underdetermined` 목록을 낸다.
- 부등식(포화 여유, 벌크 역바이어스, 헤드룸 창 등)은 rank에 넣지 않고 경고로만 낸다(P N3.7 "부등식은 경고"): `dof_inequality_warning[{kind, devices}]`.

**수치 rank**(단계 B2):
- B1 표본에서 등식 잔차의 FD Jacobian을 만든다. 스텝은 LUT 격자 간격이다.
- `numpy.linalg.matrix_rank`(기본 허용오차)로 rank를 구한다.
- **표본 수 증거 규칙**(P N3.7 "선언값이 모자란다는 증거(같은 회로에서 표본을 늘렸더니 rank가 달라짐)가 나오면 그 회로에서 올리고 근거를 남긴다"): 선언 표본 n개의 rank와 앞 ⌈n/2⌉개의 rank를 함께 잰다. 둘이 다르면 표본이 모자랄 수 있다는 증거로 `dof_sample_evidence{n, rank_half, rank_full}`를 기록하고 보고 맨 앞에 둔다. 선언값 `dof_rank_sample_count`는 spec 선언이므로 엔진이 바꾸지 않는다. 올리는 것은 그 회로 spec 선언의 개정이고, 출처에 이 기록 id를 남긴다.
- 범위 안이다: 40 §8 R3은 사용자 결정 2026-10-08 "Q1~Q11 모두 네 의견대로 진행해" Q1(R2~R6 복원)로 복원되었다. 구현 시점은 계획 N1.2의 DEC-76 원칙(발동 회로가 생길 때)을 따른다.

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
  - 입력 공통모드를 W4 자유 변수 y_icm으로 둔다. y_icm은 입력 포트인 W4 뿌리(회로마다 최대 하나 -- 둘 이상이면 탐색 전 정지, §4.7-1)의 y 성분이고 **y 키는 그 뿌리 넷 이름**이다(card IT-1, 계획 N6.5 범위 2·4; 옛 묶음 키 `input_common_mode`는 없어진다). 범위는 입력 창 [Vin,min, Vin,max] ∩ [rail_lo, rail_hi]이고 경계는 tol을 포함한다(포화 판정 여유 +tol_VDsat). **경계의 층별 정밀도**(사용자 결정 O-33 (3), card IT-2): 평가 커널에서는 그 해에서 잰 선형 감도 끝(손계산, '추정' 표기)이고, 끝 풀이(창 끝 x 고정 Newton)는 어느 층에도 두지 않는다(계획 v6.34 사용자 결정 O-109 C1 -- 정확값은 oracle `.dc`, §4.7-3). 이 y 범위는 θ 변수의 범위라 설계점 질문이고 θ 고정이다(DEC-103); 입력 포트의 ICMR 창은 봉인 뒤 측정 구성 판정 창(KCL 선형 감도 끝, §4.7-3b) 하나다.
  - `icm_margin_v`·`required_input_cm_v`·`icmr_v`는 입력 포트 창 필드를 읽기만 한다(§4.7-5, card IT-2 -- metric 쪽 자체 창 계산은 없다). 결과 JSON `required_input_cm_v{value, window}` 형식은 그대로다(IT-Q2, 사용자 결정 O-13 (2)).
  - '창 중앙값'을 숫자로 선언하지 않는다(EP-4).
  - agnd 0 V 관례는 이 정책의 회로에 적용하지 않는다.
- **선언 입력 DC 유지**: 입력 DC가 선언된 회로는 그 값을 쓰고, `icm_margin_v >= 0`을 제약으로 둔다(40 §9.2). 그 창도 입력 포트 창 필드에서 읽는다(§4.7-2 (c) -- 선언 포트는 F라 y 범위가 아니다).
  - 위 판정 규칙에 따라 창이 인증되었고 상한 밖이면 exit 3이다.
  - 출력 버퍼 창(follower 스택)은 선언 제약이 없어도 **탐색 전 실현가능성 보고**로 낸다. 이것은 기존 '보고만' 규칙과 같다. 이 보고는 단계 A 보고서에 별도 행 `buffer_window_report`로 출력한다.
- **짧은 L bin 경고**: 입력 창 상한이 인증된 상태에서, 그 창을 정하는 경로의 어느 kind가 **최단 L bin에서만** 양의 폭을 낼 때가 있다. 그때는 경고 `icmr_window_short_l_bin{kind, bin, upper_bound_by_bin}`를 낸다.
  - 이 경고는 탐색을 막지 않는다. 탐색 공간의 구조 정보로 보고에 싣는다.
  - 창이 모든 bin에서 비면 기존 판정 규칙(제약 있으면 exit 3)을 따른다.
  - 회로별 적용은 40 §9.2 표에 있다.

**파일**: `E/metrics/headroom_bound.py`(진입점 `achievability`가 부른다).

### 4.7 입력 포트 창 -- 정본 하나 (card IT-1·IT-2, 계획 N6.5·N6.6, v1.12)

**목적**: 입력 공통모드 창(J-E)을 계산하는 곳을 하나로 두고(DEC-83·FR-9, 원칙 감사 C1 '입력 CM 창 2곳'), metric은 그 필드를 읽기만 하게 한다. **v1.13.0 배치**(계획 v6.34 DEC-103 '계산 틀은 질문에 맞춘다'): θ 프레임 탐색 창 `node.dc_window`는 θ 변수인 W4 뿌리 y의 범위(설계점 질문, θ 고정 -- 노드 풀이 블록, W4 뿌리 항목만)이고, 입력 포트 창은 봉인 뒤 측정 구성 블록이 봉인점 KCL(`graph.ss_nodal`)로 잰 측정 구성 판정 창 `node.dc_window_cfg` 하나(섭동 질문, W·바이어스 고정)다; 커널·front·보고가 모두 그 칸을 읽고 정확값은 oracle `.dc`가 확정한다(기초 가정, O-108·O-109 C1). §4.6의 헤드룸 창 상한(`headroom_bound`, LUT 격자 최솟값 상한 = 탐색 전 달성가능성 경계)은 다른 개념이라 이 절의 대상이 아니다(계획 N6.6 소비자 표). **줄 인용 기준**(v1.12.10 재검증 R-1): 이 절의 엔진 `.py:줄` 인용은 master `52b9dd81` 기준이고, 다른 기준(integ-it12 `56080584`, IT-2b code `85847b49`, 4.7-0 표의 `9401e98f` 등)은 그 줄에 표시한다.

**4.7-V v1.15.2 대체 표**(계획 v6.38.3 DEC-106·N6.35 E-13·E-19·E-22·E-29, 계획 LA-1 후속 정정 표 v6.38.3 행 'design 41 4.7-2 항목 4·4.7-3 1·L12 (a)·A6 b → θ y 범위 = 순서 창 하나'; 이 절 4.7-1~4.7-7 가운데 아래 자리는 이 표가 정본이고 본문 해당 자리는 이 표를 가리킨다 -- 옛 문언 = design 이력 H41-02~H41-08, `gain-budget-gmid-sizing.design.history.md`):

| 옛 자리 | 대체 규칙 | 근거 |
|---|---|---|
| 4.7-1 2·4(입력 포트마다 W4 뿌리 후보, 입력 포트 W4 뿌리 둘 이상 = `input_port_multiple_roots` 정지)·4.7-1 test interface (d) | 입력 DC 미선언(`engine`·`pending`)이면 topology가 선언한 차동 입력쌍(role `differential_input_p`·`_n` 각 하나)의 두 포트를 Kruskal·성분 계산에서 **한 점(입력 점)**으로 묶는다(정점 묶음 -- 같은 DC 엣지·등식 없음). 그 점이 F에 닿으면 v_cm은 KVL 종속(y 성분 0), 아니면 W4 뿌리 하나·y 키 `(y, <role differential_input_p 포트 넷>)`(두 포트 writer 항목 relation `input_point`가 같은 키를 읽음). 묶은 뒤 (gate, source)·kind가 같아지는 쌍은 `parallel_vgs`. 그 밖 다중 입력 = 탐색 전 정지 `unsupported_rule_branch`(rule_branch **`input_cm_undefined`**, `ports`); `input_port_multiple_roots`·`BRANCH_INPUT_MULTIPLE_ROOTS` 삭제. 입력 DC 선언·단일 입력 회로 무동작. 상세 = 40 §3.11-4 | DEC-106 (1)~(7), card IT-1 범위 재작성 1~4(N6.5); 물리 결정자 = 측정 구성(한 차동쌍은 같은 원이 같은 공통모드로 구동 -- 두 포트 DC 차는 계통 offset이라는 계산 결과, DEC-23) |
| 4.7-2 `node.dc_window` 행('포화 판정 여유 창·선형 감도 끝')·값 형식의 `input_status` ∈ {measured, unsettled, unmeasured}·`tol_v`·4.7-3 1(뿌리 A6 되풀이·`_interior_solution`·`k_max`)·4·5·4.7-4 커널 쪽 `k_max` import·4.7-7 L12 (a)(`k_max` 주입 test·A6 b `unsettled` 단언) | **θ y 범위 = KVL 순서 창 하나**: `node.dc_window` = 순서 창(뿌리 넷에 채널이 닿는 전도 MOS마다 채널 전도 방향 전압(nmos V_DS, pmos V_SD) ≥ 0이 되는 y 구간 -- `kvl_window`, VDSAT·tol 없음), W4 뿌리마다(입력 점 뿌리 포함) 같은 규칙; 상태 칸 `input_status`·`tol_v`, 상수 `INPUT_STATUS_UNMEASURED`·`INPUT_STATUS_UNSETTLED`, 커널 입력 창 측정·`override` 되풀이·`_interior_solution`·`_dyadic_ys`의 커널 쓰임은 card WB-1 범위 3a 커밋에서 삭제. 입력 창(ICMR) 측정은 측정 구성 판정 창 `node.dc_window_cfg`(4.7-3b `icm_config`, W·바이어스 고정 KCL, fail-closed) 한 자리. 포화 밖 점은 봉인 7이 거부. 상세 = 40 §3.11-1 | N6.35 E-13, card WB-1 범위 3a; 두 창은 판정 여유(채널 전도 방향 전압 ≥ 0 대 ≥ VDSAT + tol)·범위(뿌리 인접 소자 대 사슬 전체)가 달라 다른 양(graph 규칙 3); 순서 창은 유효점의 상위집합(포화 '≥ VDSAT > 0' ⊂ '≥ 0', 채널 전도 방향 전압)이라 유효점 손실 0 -- 감사 A13 '맞음' |
| 4.7-3a R0 전도 행의 건너뜀 문턱 `\|rate\| ≤ float eps` | 행 단위별 문턱 = 그 행의 분해능(행 tol -- V/V 행은 전압 분해능, A/V 전도 행은 전류 분해능 -- 단위가 다른 양에 같은 문턱을 쓰지 않음) | N6.35 E-22, card IT-2(IT-2c) 범위 6 |
| (새) g = s 소자 | `graph.gvgs_summary.off_vgs0` 분류·`off_device_on_signal_path` 정지·`bias_fixed_net` 술어 -- 40 §3.11-5 | N6.35 E-19, IT-1 범위 재작성 5 |

**4.7-0 as-built 사실**(master `9401e98f`, 2026-10-20 이 design 작성 때 코드를 다시 읽음. `E` = `skills/analog-gmid-design/gmid_engine`):

| # | 사실 | 근거 |
|---|---|---|
| A1 | 쓰기 계획: 입력 DC 미선언이면 F 밖 입력 포트를 (구조 색, 이름) 이웃 쌍마다 '같은 DC' 엣지로 잇고(순위 최상위 `_TIE`·`_KIND_TIE`), 트리 엣지면 `input_tie`(W2)로 쓴다. 포트가 있는 성분의 뿌리 y 키 = `INPUT_GROUP_KEY`(`"input_common_mode"`) | `E/sizing/writer_plan.py:76-77, :104-105, :157-159, :213-214, :228-234` |
| A2 | `input_roots()` = relation `free_window`이고 y 키가 `INPUT_GROUP_KEY`인 W4 뿌리. `members`는 `input_tie` 사슬을 따라 뿌리에 묶인다. `dc_columns` READS에 `node.port_direction`이 없다 | `E/sizing/block_columns.py:179-184, :220-223, :82-86` |
| A3 | `saturation_rows` = 전도 MOS마다 (d, s, 부호, VDS − VDsat − tol_VDsat), 선형 선언 소자 제외, VDSAT 열·tol 미정이면 None | `E/sizing/block_columns.py` |
| A4 | `input_windows` = 뿌리마다 `saturation_window` 창 ∩ 순서 창(`kvl_window`, 레일 범위 포함) | `E/sizing/block_columns.py` |
| A5 | `saturation_window`는 `_sensitivities`(s_n = dV_n/dx 선형 연립, VDS·VSB 결합 포함)로 창을 잰 뒤 감도를 버리고 (lo, hi)만 낸다. 연립 특이·정의역 밖이면 None | `E/sizing/input_window.py:26-45, :48-66` |
| A6 | `_solve_input_window`: y = 1/2 풀이 → 창 측정 → 창을 y 범위(`override`)로 두고 다시 풀며 경계가 tol 안에서 같아질 때까지(상한 `k_max`) → `_refine_ends`(창 끝 x 고정 Newton) → 마지막 풀이. 갈래: (a) y = 1/2가 풀리지 않거나 창을 못 재면 `_interior_solution`이 이분 수준 y 열(`_dyadic_ys`, 시도 상한 `k_max`)에서 풀리고 창을 잴 수 있는 점을 찾고(θ 키는 호출자가 준 `key` -- as-built `(y, INPUT_GROUP_KEY)`), 못 찾으면 요청 y·순서 창으로 푼다(종래 사상) (b) `tolerance`가 미정(`SealViolationError`)이면 창을 한 번만 적용하고 되풀이 수렴 판정 없이 푼다 (c) 되풀이가 `k_max` 안에 tol 안으로 같아지지 않으면 마지막으로 잰 창을 그대로 쓴다(수렴 표시 없음) | `E/sizing/block_columns.py:691-735`(a `:713-717`·`:640-660`, b `:719-723`, c `:724-733`) |
| A7 | `_refine_ends`의 끝 값이 풀린 x인 경우는 (i) `inside and close` (ii) 풀이 직후 `again is None` 둘뿐이고, (iii) 첫 반복 풀이 실패 (iv) 둘째 반복 이후 풀이 실패 (v) `k_max` 소진에서는 끝 = 풀지 않은 x다. 끝 풀이 해(`values`)는 버린다. 끝이 무한대면(제약 없음) 손대지 않고 멈춘다(`:672` -- 순서 창이 레일 범위로 시작하므로(`kvl_window` `:201`) 입력 뿌리 창 끝은 실제로는 늘 유한) | `E/sizing/block_columns.py` |
| A8 | `dc_columns`는 relation `free_window`인 모든 넷에 `node.dc_window` = `Window(lo, hi, constraints)`(순서 창 ∩ `override`)를 쓴다 -- 입력 포트가 아닌 넷·뿌리 아닌 입력 포트·선언 입력 포트는 해당 없음 | `E/sizing/block_columns.py`, `E/sizing/s2_values.py`, `E/sizing/CONTRACT.md`(master `2e707d5d`에서 다시 잼, 옛 `:196`) |
| A9 | metric 쪽 둘째 창: `ls_swing`이 입력 포트마다 경로 합 [lo, hi]의 교집합을 재고 `v_icm = volts[inputs[0]]`(첫 포트)로 margin을 낸다. 호출 `metrics_aux._swing` | `E/metrics/ls_swing.py`, `E/metrics/metrics_aux.py:214, :236, :256-264` |
| A10 | **계획 소비자 표 밖 소비자**: `fd_jacobian._steps`가 `node.dc_window`를 그 넷 writer의 y 키로 색인해 y FD 스텝(창 폭)을 정한다 -- 창이 W4 뿌리에만 있다는 전제 | `E/search/fd_jacobian.py:52-55, :65-68` |

**4.7-1 card IT-1 -- 쓰기 계획 개정**(계획 N6.5 범위 1~5, 결정 B2·K-3·O-13 (1)(2)):

1. **같은 DC 엣지 없음**: 입력 DC 미선언이어도 G_vgs에 '같은 DC' 엣지를 넣지 않는다. 엣지 순위 `_TIE`·`_KIND_TIE`, `TieBreak(input_tie_order)` 기록, `input_tie` 쓰기와 어휘(`REL_TIE`·`PATH_TIE`·`TIE_INPUT_ORDER`·`INPUT_GROUP_KEY`와 그 공개 export)를 지운다. 같은 변경에서 지우는 소비 자리(master `2e707d5d`에서 잼): `E/sizing/scc_order.py` import `:21`·`:26`, `REL_TIE` 사슬 `:125`, `REL_TIE`·`INPUT_GROUP_KEY` 분기 `:137-140`, docstring `:7-8`; `E/sizing/CONTRACT.md` relation 어휘 `:232-233`, `TIE_INPUT_ORDER` `:238`, 쓰기 계획 문언 `:311`·`:318`·`:321`, 읽기 집합 `:351`, 식 `:420`, path_values `PATH_TIE` `:497`, 예시 `:635`, 입력 묶음 되풀이 문언 `:1014-1016`.
2. **뿌리와 y 키**: 뿌리 규칙은 그대로(F 없는 성분에 입력 포트가 있으면 그중 (구조 색, 이름) 최소, 같은 색 후보가 둘 이상이면 `TieBreak(w4_root)`). **y 키 = 뿌리 넷 이름**(입력 포트 뿌리도 다른 W4 뿌리와 같은 규칙). θ 성분 키는 `(y, <뿌리 넷>)`이고 결과 JSON 키 `y:input_common_mode`는 `y:<넷>`이 된다. 한 성분 안 뿌리가 아닌 입력 포트는 트리 경로(MOS VGS)로 쓰인다.
3. **종속**: 같은 DC 엣지로 생긴 종속은 0이다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이다(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b). 대칭이면 그 등식은 대칭 묶음과 중복이다. 불변식 '종속 수 = 순환수'는 같은 DC 엣지 없는 G_vgs(F 한 점) 기준이다.
4. **다중 입력**: 4.7-V 1행이 정본(DEC-106 입력 점, 그 밖 다중 입력 = 탐색 전 정지 `input_cm_undefined`; 옛 `input_port_multiple_roots` 문언 = design 이력 H41-02).
5. **노드 풀이 블록 쪽**(같은 card): `members` = 자기 자신(사슬 없음), `input_roots()` = relation `free_window`이고 넷이 입력 포트인 W4 뿌리(`dc_columns` READS에 `("node", "port_direction")`을 더한다). **G_vgs 밖 고립 입력 포트**(MOS gate·source에도 저항에도 닿지 않아 쓰기 계획이 W4 y 키 = 넷으로 쓰는 넷, `writer_plan.py:236-238`)도 입력 포트인 W4 뿌리로 센다 -- 4의 '둘 이상이면 정지'에 들어간다(그 넷도 사용 환경이 DC를 정하는 입력이고, 세지 않으면 y가 둘인 회로가 정지 없이 지나간다; 코퍼스 발동은 IT-0 M-I1이 기록). `_solve_input_window`의 θ 키 = `(y, <입력 뿌리 넷>)`(뿌리는 4로 최대 하나 -- 같은 키를 `_interior_solution`에 넘긴다), `REL_TIE` 분기(writer 식·야코비안·path value) 삭제. `achievability`의 `tie:<넷>` 등식 삭제.

**test interface(IT-1, test 작성 주체 -- 소스 없이)**: 진입점 `dc_writer_plan(snapshot, target_nets, input_dc_declared, order_hints=NO_ORDER_HINTS)`(서명 불변). 출력 필드 `node.dc_writer`(`NodeWrite(tier, relation, element, known, y_key, order)`), `device.dc_coord`(`DeviceCoord(role, relation, partner)` -- `E/sizing/s2_values.py`), `graph.dc_tie_breaks`(`TieBreak(decision, candidates, chosen)`; decision `input_tie_order`는 없어지고 `writer_edge`·`w4_root`·`current_pivot`이 남는다). 어휘: `NodeWrite.relation` ∈ {`rail`, `declared_target`, `input_dc`, `vgs_gate`, `vgs_source`, `resistor_drop`, `free_window`}(`input_tie` 없음), `DeviceCoord.role` ∈ {`writer`, `dependent`}, `DeviceCoord.relation` ∈ {`tree`, `parallel_vgs`, `cycle_vgs`, `fixed_vgs`}. 세 필드의 형식은 그대로이고 값 어휘·y 키만 바뀐다(계획 N6.5 완료 조건 4 (c) -- 40 §2.4.8 '쓰기 계획 필드(IT-1)' 행). 단언 (a) 입력 DC 미선언 차동 입력 toy: relation `input_tie` 0, 입력 포트 W4 뿌리의 y 키 = 그 넷 이름, 기대 종속 목록(같은 DC 엣지로 생긴 종속 0, 포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs` 포함)은 toy 연결에서 손으로 유도한다 (b) 종속 수 = 같은 DC 엣지 없는 G_vgs(F 한 점)의 순환 수(손계산) (c) 입력 DC 선언 toy의 쓰기 계획 = 손계산 오라클(base에서도 green -- 무동작 성질) (d) 두 입력 포트가 서로 다른 G_vgs 성분인 toy → `StructureUnresolvedError`, `detail["rule_branch"] == "input_port_multiple_roots"`(base는 정지하지 않아 red). 위치 = `E/tests/sizing/test_writer_plan.py` 안 새 test 함수(이름은 test 주체가 `git grep`으로 겹침 확인, F-IT4 -- 구조 규칙 H).

**4.7-2 card IT-2 -- 필드 셋**(이름 정본 = 계획 N6.6 범위 1·N6.8 DE-1 (a)·N3.3 S2 행. 정밀도·기준이 다르면 이름이 다르다):

| 필드 | 뜻 | writer | 층·호출 자리 | 읽는 쪽 | 이 design 판에서 |
|---|---|---|---|---|---|
| `node.dc_window` | **θ y 범위 = KVL 순서 창**(4.7-V 2행 -- θ 변수 W4 뿌리 y의 범위, 설계점 질문이라 θ 고정, DEC-103; 상태 칸 없음). **항목 = W4 뿌리만**(입력 점 뿌리 포함 -- O-109 D1·DEC-106) | `dc_columns`(노드 풀이 블록) | 평가 커널(모든 평가, FD 열 포함) | 커널 탐색 `fd_jacobian` y 스텝(W4 뿌리만, 4.7-6) -- 값 독자는 이것뿐이다(계획 N6.6 범위 1, O-58 S-1); `icm_config`는 이 필드를 읽지 않는다(D2) | IT-2b가 넓힌 범위('모든 입력 포트와 W4 뿌리')를 IT-2c가 W4 뿌리로 되돌린다: 뿌리 아닌 입력 포트·입력 DC 선언 포트·F 성분 미선언 포트 항목 삭제(D1, 4.7-3 2·3) |
| `node.dc_window_cfg` | **측정 구성 판정 창**(계획 N3.8 '창 필드'·'측정 구성 창 = 선형 감도 끝 하나', O-58 S-1·v6.34 O-109 C1): 측정 구성 ICMR(servo -- 단일·차동 출력; 단일 입력 '회로 그대로' -- v1.14.0 O-115)에서 +tol_VDsat로 잰 **KCL 선형 감도 끝**('추정' -- 봉인점 DC 야코비안 `graph.ss_nodal` + servo 행 δs = 0(Schur 1칸), 출력 꼴 무관; 경계 행 = 포화·`triode` 행 + 전도 행 R0 -- v1.14.1 O-118 2번, 4.7-3a 6; O-108). 값 꼴 = `node.dc_window`와 같은 `Window` 하나(아래 '값 형식'). **모든 측정 구성에서 쓰고 모든 측정 구성 포트의 끝을 담는 칸은 이 하나다**(같은 정의의 양 두 칸 금지 -- graph 규칙 3; v1.12.1 W1 철회 근거 그대로: θ 프레임 창과 측정 구성 축이 다른 양). 구성이 None(정의 불능)이면 쓰지 않고 소비자는 `graph.icm_config.undefined`를 metric 정의 불능으로 옮긴다(4.7-5 '측정 구성 정의 불능의 경로') | 새 블록 `icm_config`(4.7-3b) | 평가 커널, 봉인 뒤(`E/metrics/ss_evaluate.py:101` 뒤) | 커널 ICMR 선언 제약·커널 metric(`metrics_aux`, 아래 5)과 front·보고(그 점의 같은 값 -- 별도 블록 없음, O-109 C1); DE-1 뒤 선언 제약 판정 | IT-2c가 만든다(입력 포트마다; 상태는 이 블록이 스스로 정한다 -- `"measured"`·`"unmeasured"`(`"f_component_undeclared"` 삭제, O-118 3번), 커널 θ 프레임 상태를 이어받지 않음 -- v6.34 O-109 D2) |
| `node.dc_window_def` | **정의 창**: VDS ≥ VDSAT(tol 없음)·전도 끝(봉인 9 식, 훑기 점 값) | card DE-1 (a)의 블록 | 평가 커널 | DE-1 뒤 metric 값 | **예약 -- 이 card는 만들지 않는다**(DE-1 몫) |
| ~~`node.dc_window_def_refined`~~ | **삭제** -- 다듬은 창(끝 풀이로 다듬은 봉인 시점 창)과 기준 칸 `criterion`(X-IT12)을 두지 않는다(계획 v6.34 사용자 결정 O-109 C1 '선형 끝만, SPICE 확정' -- **원래 취지와 다름, 승인 O-109**; 정확값 = oracle `.dc`) | 없음(`dc_window_refine` 블록 없음 -- 4.7-4) | -- | -- | 만들지 않는다(엔진 소스 정의 0 -- 계획 완료 조건 (1)) |

**DE-1 전 한정**(계획 N6.6 범위 1·2): metric 값 = 커널·front·보고 모두 `node.dc_window_cfg`(측정 구성 판정 창 -- 모든 구성, '추정'; 계획 v6.34 N3.8 '측정 구성 창 = 선형 감도 끝 하나', 사용자 결정 O-109 C1 -- front 값을 따로 내는 블록 없음). DE-1 병합 뒤 metric 값은 `node.dc_window_def`, 선언 제약 판정은 `node.dc_window_cfg`(측정 구성 판정 창)를 읽고 그 제약 행은 다른 이름을 갖는다(DE-1 design 몫; 계획 N6.6 범위 1 'DE-1 병합 뒤에는 metric 값 = `node.dc_window_def`, 선언 제약 = 측정 구성 판정 창'·DE-1 (ii′) -- v1.12.1 gap G2 정정, 옛 '`node.dc_window`'는 O-58 전 문언 잔재).

**값 형식**:
- `node.dc_window` = `Window(lo, hi, constraints)`(상태 칸 없음 -- 4.7-V 2행; `constraints` = 순서 제약 수). **`node.dc_window_cfg`(4.7-3b)**는 같은 `Window` 꼴이고 상태는 `icm_config`가 스스로 정한다(커널 창의 상태를 이어받지 않는다 -- 계획 v6.34 사용자 결정 O-109 D2): `input_status` ∈ {`"measured"`(KCL 선형 감도 끝을 잼), `"unmeasured"`(자기 측정 실패 -- 행을 만들 수 없음(`region_rows` None)·감도 연립 특이(`kvl_sensitivity` None)·`saturation_window` None; 꼴 = `Window(None, None, 0, input_status="unmeasured")`)}(v1.14.1: 옛 셋째 상태 `"f_component_undeclared"` 삭제 -- F 성분 미선언 포트도 함께 구동해 창이 정의된다, 계획 v6.36 O-118 3번, 4.7-3 3); `"unsettled"`는 cfg에 없다(D2). cfg의 `constraints` = 0(순서 창이 없다), **`tol_v` = 봉인점 `device.dc_tol_v`(writer `dc_tolerances` -- 커널 `tolerance`와 같은 셀 `tol_v_cell`을 봉인점 VDS에서 이미 잰 graph 필드) 가운데 `device.dc_coord` MOS의 None 아닌 값의 최솟값**(v1.13.0 design 결정 -- 이어받던 커널 tol 대신 같은 정의의 봉인점 값을 READS로 읽는다, 재계산 0; 모두 None이면 `tol_v` = None이고 상태는 `"measured"` 그대로 -- 분해능 None 경로(4.7-5 785, 제약은 기존 `resolution_undefined` fail-closed)로 통일한다. **v1.13.0 둘째 커밋**: 첫 커밋의 'tol_V 모두 None → cfg `"unmeasured"`' 규칙은 철회 -- 그 점은 tol_V 미정 행이 undefined라서 봉인되지 않아(`sealed=None` -- 엔진에서 undefined는 fail(거부)과 다른 상태) 측정 구성 블록이 돌지 않는 죽은 갈래다(이 갈래에는 test를 두지 않는다 -- 셋째 커밋)(`E/sizing/seal_conduction.py:43-46`, `E/sizing/seal.py:13`, `E/metrics/ss_evaluate.py:83`). **축**(graph 규칙 3, gap G2): cfg `tol_v`(봉인점 소자 전부의 tol_V 최솟값)는 봉인 1의 노드 tol(Q-N3 -- 노드에 닿는 MOS tol_V 최솟값)과 다른 축이다(소자 전부 대 그 노드에 닿는 소자). **상태 우선순위**: cfg 상태가 둘뿐이라 겹침 없음(옛 definitional `"f_component_undeclared"` 삭제). **S-4 갈래 몫의 꼴**(4.7-3a 3 -- 계획 v6.34 N6.6 범위 1 '동작점 불일치 묶음' (가): 실을 창 항목 = cfg 항목인데 그 점은 봉인 거부라 측정 구성 블록이 돌지 않아 **cfg 항목의 불일치 상태는 대상 없음**, 상태 값·소자 열 칸·code를 둘지는 EO-1 design이 이 사실로 정한다): 두면 쓸 이름 = 불일치 상태 값 `"op_mismatch"`(상수 `INPUT_STATUS_OP_MISMATCH`), 소자 열 칸 `status_detail`(기본값 `()`), metric code `input_window_operating_point_mismatch`(상수 `CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH`); (S4-나)의 IT-2에는 없다(이 이름들은 4.7-7 D (d) 부재 검사의 검색 대상이고 code가 아니다). (옛 커널 상태 어휘·`tol_v` 문언 = design 이력 H41-04.)
- **삭제(계획 v6.34 사용자 결정 O-109 C1)**: `RefinedWindow`·`WindowEnd`·`CRITERION_*` 상수·끝 풀이 사유 `REASON_WINDOW_END_*`는 만들지 않는다(다듬은 창 없음 -- 위 표).
- 예시 리터럴(test 작성용): 커널 뿌리 `Window(0.31, 1.12, 2)`, cfg 포트 `Window(0.33, 1.18, 0, input_status="measured", tol_v=1.2e-4)`.
- **정확도 표기**(계획 N6.6 범위 1 '정확도(oracle 대조 오차)를 표기'): 커널 창은 손계산 '추정'이다. 그 정확도는 metric 쪽 `IcmWindow.model_error_ref`(4.7-5)에 적는다 -- 값 = card ME-1의 모델 오차 판정 기록 id, ME-1 전에는 None이고 보고에 '보류'(채울 card ME-1, 계획 N6.3 (i)·N6.19)로 적는다. 창 필드 자체에는 칸을 두지 않는다(모델 오차는 metric 단위 선언값, DEC-72).

**4.7-3 커널 창(IT-2 범위 1, O-33 (3))** -- `dc_columns`(노드 풀이 블록)가 같은 평가 안에서:
1. **뿌리**(입력 DC 미선언, 4.7-1로 최대 하나 -- 입력 점 포함): `node.dc_window` = KVL 순서 창(4.7-V 2행; 되풀이·`k_max`·`_interior_solution`·상태 칸 없음). metric은 측정 구성 판정 창 `node.dc_window_cfg`(4.7-3b)를 읽고 그 블록은 `node.dc_window`를 읽지 않는다(사용자 결정 O-109 D2 -- 설계점 질문의 결과가 섭동 질문 metric을 정의 불능으로 만들지 않는다, DEC-103). 포화 밖 점은 봉인 7이 거부한다. (옛 A6 되풀이·판정 tol·A6 b 도달 조건 = design 이력 H41-06.)
2. **뿌리 아닌 입력 포트 -- 커널 항목 없음**(계획 v6.34 사용자 결정 O-109 D1 -- **원래 취지와 다름, 승인 O-109**(O-16 (2) '노드 풀이 블록이 모든 입력 포트 창을 쓴다'); 근거: 그 항목은 값 소비자가 없고(커널 `node.dc_window` 값 독자 = `fd_jacobian` W4 뿌리 폭뿐) 섭동 성격의 양을 θ로 재는 것이다 -- DEC-103): IT-2b가 쓰던 뿌리 아닌 입력 포트 항목(뿌리 끝을 같은 해의 θ 감도로 옮긴 창)을 IT-2c 변경에서 지운다 -- `block_columns._windows`의 그 루프, 그것만 쓰던 `_Measured.slope`·`_Measured.values` 칸(감도·해 보관)과 `declared_inputs` 메서드(아래 3)도 같은 변경에서 지운다(죽은 코드 금지). 그 포트의 창은 측정 구성 판정 창(4.7-3b) 하나다. **끝 식 `saturation_window`**(창 끝 식(행 교집합)은 이 함수 하나에만 있다 -- 계획 N6.6 완료 조건 (2), 사용자 결정 O-61 P2): **`saturation_window(unknown, root, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None`**(v1.13.0 서명 -- 계획 v6.34 N6.6 범위 1 끝·검증 N-5: 쌍 roots `(행 넷, 고정 넷)` 갈래(θ 연립 follower 용)와 선언 포트 묶음 갈래(커널 선언 포트 항목 용)는 쓸 곳이 없어 IT-2c 변경에서 지운다; `roots` tuple → 넷 하나 `root`): `root` = x로 움직이는 넷 하나(그 행 s = 1 -- 커널 W4 입력 뿌리), `slope`(키워드 전용, {넷: dV/dx} 또는 None) = 주면 안의 감도 연립을 풀지 않고 그 감도로 끝만 낸다(측정 구성 -- 감도 정본 `kvl_sensitivity`, 4.7-3b (3)·(4); 그때 `unknown`·`root`·`values`·`gradient`는 읽지 않고(부르는 쪽은 None을 넘긴다) 반환 slope = 받은 값). 출발점 x₀ = 0 기준 **이동량** 창 [dlo, dhi](커널 뿌리 창은 호출자가 `values[뿌리] + [dlo, dhi]`로 만든다), slope = {넷: dV/dx}. **포트 창 규칙**(측정 구성 블록이 쓴다 -- 4.7-3b (4), 공개 `Circuit.port_window`, 4.7-4): 두 끝 전압 V_p + s_p·dlo, V_p + s_p·dhi의 [min, max] ∩ 레일(사용자 결정 O-49 P2 -- 감도 음수 포트는 아래 끝이 위 끝이 된다, 빈 창·음수 폭으로 내지 않는다); **s_p = 0이면 두 끝 = V_p**(이동량이 ±inf일 때 0·inf를 피함 -- v1.12.11 G6). 행 원소 꼴은 4.7-3a 1·4.7-7(v1.14.1: 일반 1차 행 `(terms, slack, kind)` -- 계획 v6.36 N3.8 '행 형태', 전도 행 R0 수용; 서명은 그대로). κ 경로 필드를 다시 계산하지 않고 별도 노드 풀이를 하지 않는다. s_p < 0 발동 회로는 card 0 M-I4가 기록한다(4.7-8a -- 측정 구성 판정 창 기준).
3. **입력 DC 선언 포트(F) -- 커널 항목 없음**(O-109 D1): 커널 θ 프레임 창에는 그 포트 항목을 두지 않는다(IT-2b의 선언 포트 묶음 항목·`_windows`의 그 갈래 삭제). 측정 구성 판정 창에서 그 포트는 KCL 계(`graph.ss_nodal` -- 고정 = ac 접지 ∪ 입력 넷)의 **구동 입력(고정 넷)**이고 아래 P3 묶음대로 x만큼 움직인다(계획 v6.34 N6.6 범위 1 '입력 DC 선언 포트(F)', 4.7-3b (4)). 근거: J-E '입력 DC는 사용 환경이 정하는 값이고 회로가 정하는 것은 창' -- 입력 포트의 창은 그 포트를 바깥에서 구동한다고 볼 때 선언 영역이 유지되는 구동 값 범위다(오라클에서 선언 입력 DC는 전압원). 아래 두 경우의 처리:
   - **F 성분에 속한 입력 DC 미선언 포트**(그 성분이 레일·W3에 닿아 포트가 W4 뿌리가 아니고 θ 쓰기 계획의 writer 사슬로 DC가 정해지는 입력 포트 -- 예: MOS gate 전용 입력 넷; library 발동은 IT-0 M-I1이 기록): **θ 프레임 창에서는 '정의 불능' 판단을 유지한다** -- 그 포트는 W4 뿌리가 아니라 D1 뒤 `node.dc_window`에 항목이 없다(as-built `E/sizing/block_columns.py:803-805`의 `f_component_undeclared` 항목은 D1의 뿌리 아닌 포트 항목 삭제로 함께 지워진다 -- 계획 v6.36 N3.8 'ICMR 측정 구성'). **측정 구성 판정 창에서는 함께 구동한다**(계획 v6.36 사용자 결정 O-118 3번 "(나) KCL 함께 구동 (권고)" -- **원래 취지와 다름(승인 O-118)**: v6.35.1·O-61 P4 (b) (가)의 KCL 쪽 '구동 제외·봉인점 고정·정의 불능'을 뒤집음; v1.14.0의 이 줄('판정·기록 자리', '측정 구성의 구동 입력이 아니다')과 4.7-3b (4)(ii)의 어긋남(검증 S-2·gap S-3)은 이 문언 하나로 맞춘다): 구동 = 모든 입력 포트(`graph.ss_nodal`의 입력 넷 그대로 -- 이득 계산과 같은 인수분해, 우변만 바뀜)이고 그 포트도 그 안에 든다. 근거(계획 인용): gate 전용 입력 넷에는 DC 전류가 들지 않아 회로가 그 넷의 DC를 정하지 않는다 -- 'writer'는 θ 틀이 입력쌍 전류를 θ로 고정해 생긴 장부상 방향이고 KCL 섭동 질문(DEC-103)에는 그 제약이 없다; 손계산 ICMR은 입력 게이트 전압을 자유 변수로 둔다. 그래서 측정 구성 블록은 이 판정을 하지 않고(`node.dc_writer` relation 판정·`Circuit.writer_head` 호출 0), cfg 항목 상태 `"f_component_undeclared"`·metric code `input_window_f_component_undeclared`·상수 `INPUT_STATUS_F_COMPONENT_UNDECLARED`·`writer_head`는 IT-2c에서 두지 않는다(생산자·소비자 0 -- 만들면 배선; 4.7-4). test = 4.7-7 L12 (b)(library toy -- heldout 회로는 근거로 쓰지 않음).
   - **고립 입력 포트**(G_vgs 밖 -- 게이트·소스·저항 어디에도 닿지 않아 쓰기 계획이 W4 y 키 = 그 넷으로 쓰는 포트): 계획 N6.5 4(사용자 결정 O-61 P4 (a))대로 '입력 포트인 W4 뿌리'로 센다 -- 둘 이상이면 4.7-1 4의 정지, 하나뿐이면 커널 창은 **위 1의 뿌리 창 절차 그대로**다(새 절차 없음; 그 넷에 닿는 소자가 없어 행이 그 넷의 감도를 쓰지 않으면 창 = 레일 교집합이 그 절차의 출력이다). 측정 구성 판정 창에서는 다른 입력 포트와 같이 KCL 계의 구동 입력이다(4.7-3b (4)). `domain.ties` y 묶음·뿌리별 포화 창은 구현하지 않는다(상태 '미구현(발동 0)', 계획 N6.5 완료 조건 7).

   **x 하나의 묶음**(사용자 결정 O-49 P3, 계획 X-IT11 -- 옛 '포트마다 따로 x' 해석 대체; v1.13.0 자리 = 측정 구성 판정 창 하나): **모든 입력 포트**(계획 IT-2c 착수 조건 (vii) -- servo는 입력 포트를 출력에 묶지 않아 O-53 A-2 갈래와 `tied_ports`가 소멸; F 성분 미선언 포트 포함 -- v1.14.1 O-118 3번; 4.7-3b (4))는 **모두 같은 x만큼 함께** 움직인다: KCL 구동 = 묶음의 모든 포트에 1(공통 x 하나, 선언 포트 사이 차 유지 -- 각 포트 전압 = 봉인점 값 + Δ, x₀ = 0 기준 이동량 Δ). 반환은 이동량 창 [dlo, dhi] 하나와 slope이고, **포트별 창**은 위 2의 포트 창 규칙으로 만든다(servo에서 s_p = 1 − e_p·(c·vx)/a_e라 포트마다 다를 수 있다 -- 끝 상태와 레일은 4.7-3b (4) (v); 옛 'x 구동 몫의 차 = 선언 차'는 그대로). 묶음 포트가 하나면 이 묶음은 그 포트 하나다. 커널 θ 프레임 창에는 이 묶음이 없다(D1).
4. **측정 실패**: 커널 입력 창 측정이 없으므로(4.7-V 2행) 커널 쪽 대상 없음. 측정 구성 판정 창의 자기 측정 실패는 4.7-3b가 `"unmeasured"`로 쓰고 metric 정의 불능(N3.14). DE-1 범위 2 '선형 감도 연립 특이 fail-closed'의 나머지(일반화된 끝점 블록의 결측 사유 기록 칸, 출력 창·방향 전류까지 같은 규칙)는 DE-1 몫이다.
5. (삭제 -- `node.dc_window`의 `tol_v` 칸 없음, 4.7-V 2행; metric 분해능은 측정 구성 판정 창의 `tol_v` -- 4.7-2·4.7-5; 옛 문언 = design 이력 H41-08.)

**4.7-3a 창 경계 행 = DC 범위 조건**(계획 N6.6 범위 1 '창 경계 조건', 완료 조건 (9); 사용자 결정 O-54·O-55 U1·V5; 정의 정본 = 계획 N3.8 '소자 조건 = DC 범위 조건' -- 여기서는 인용만): 커널 창(4.7-3)과 측정 구성 판정 창(4.7-3b)의 경계 행을 소자의 선언 영역(`intended_region`)별로 낸다 -- 행 셋은 하나(`region_rows`)이고 감도만 다르다(커널 = θ 고정 감도, 측정 구성 = KCL 감도; DEC-103). 새 기계는 두지 않는다.
1. **행 셋**(`saturation_rows`를 `region_rows`로 넓혔다(IT-2b, `block_columns._Circuit`); IT-2c가 공용 `_helpers_dc_solve.Circuit`으로 옮긴다 -- 4.7-4, 사용자 결정 O-110 U-101 (가′)) -- 반환 행 목록, **행 원소 꼴 = 일반 1차 행 `(terms, slack, kind)`**(계획 v6.36 N3.8 '행 형태': 전도 행이 여러 노드 감도의 가중합이라 넷 쌍 꼴을 넓힌다, 끝 식 정본 하나·새 창 함수 없음; `terms` = ((넷, 계수), ...), 행 기울기 = Σ 계수·s_넷; 아래 넷 쌍 꼴 `(a, b, sign, …)`은 `terms` = ((a, sign), (b, −sign))의 줄임이고 값·끝 불변; `saturation_window`의 끝 식은 `rate = Σ 계수·slope[넷]`, `slack + rate·Δ ≥ 0`, 영 기울기 건너뜀(`E/sizing/input_window.py:69`)과 서명은 그대로; 아래는 옛 넷 쌍 설명): `a`·`b` = 여유가 기대는 전압 차의 두 넷(행 기울기 = `sign`·(s_a − s_b)), `slack` = 그 해에서의 여유(≥ 0이 안쪽), `kind` ∈ {`"sat"`, `"triode"`, `"off"`}; 여유의 x 미분이 `sign`·(s_a − s_b)가 되도록 `sign`을 둔다 -- `saturation_window`의 끝 정의(`rate = sign·(s_a − s_b)`, `slack + rate·Δ ≥ 0`, `E/sizing/input_window.py:57-65`)가 그대로 맞는 부호): (가) 선언 없음(포화) = **`(d, s, 부호, VDS − VDsat − tol_VDsat, "sat")`**(지금 행 그대로, 부호 = 소자 극성 부호) (나) `triode` 선언 = **`(d, s, −부호, VDsat − VDS − tol_VDsat, "triode")`**(여유가 VDS↑에 줄어 기울기 부호가 포화 행과 반대; 판정 여유의 정의 자리 = 계획 N3.8 '소자 조건'의 `triode` 경계 판정 여유(사용자 결정 O-58 T-1 -- 인용만, 정의 사본 없음); `tol_VDsat` = (가) 행과 같은 정본 `sat_threshold` 값(headroom-chain HC-S, 계획 O-33 (8)) -- 훑기 점이면 그 점 자신의 VDS·VSB 셀, 새 상수·둘째 진입점 없음) (다) `off` 선언 = **`(g, s, −부호, V_on − VGS, "off")`**(첫 칸 = gate; 여유 V_on − VGS는 VGS↑에 줄어 기울기 = −부호·(s_g − s_s); 판정 여유 없음; V_on = 그 점에서 봉인 9 전도 정의(I_off ≤ ε·ID)를 처음 만족하는 VGS -- 아래 2). 선형화에서 VDsat·V_on은 그 해의 값으로 고정한다(행 기울기에 넣지 않는다 -- 지금 포화 행과 같은 손계산 '추정'). 지금 `saturation_rows`는 선언 소자를 빼기만 한다(`E/sizing/block_columns.py:223-224` -- 기준 커밋 integ-it12 `56080584`(IT-1 병합 뒤); 계획 N6.6 범위 1이 인용한 `:230-231`은 master `52b9dd81`(IT-1 전)의 같은 줄, 같은 사실) -- 그 제외를 이 행 셋으로 바꾼다.
2. **V_on의 출처**: card EO-1의 공용 전도 판정 함수(사용자 결정 O-55 U2·V5 -- 'off 유지 경계 = VGS 감도 + 봉인 9 전도 VGS(LUT)', 같은 함수가 LUT I_off로 판정)를 부른다. 이 design은 그 함수를 새로 만들지 않고 이름·서명은 EO-1 design을 인용한다. **S-4(사용자 결정 O-58 S-4·O-98 -- 계획 v6.33 N6.6 범위 1 '동작점 불일치 묶음'·'갈래'·완료 조건 (9), N6.20 범위 (4)·완료 조건 (8) (b)·(8) (e))**: (다) 행과 `off` toy, 그리고 **동작점 불일치 묶음**(아래 3 -- (가) 동작점(노드 풀이 블록의 마지막 풀이)에서 판정해 불일치 상태·소자 열을 입력 포트 창 항목에 싣는 것 -- v1.13.0, 계획 v6.34 셋째 커밋: 실을 항목 = 측정 구성 판정 창 항목이고 그 점은 봉인 거부라 **대상 없음**, 상태 값·소자 열 칸·code를 둘지는 EO-1 design이 정한다 (나) 같은 점 봉인 거부 (다) 그 창으로 부른 metric 함수의 정의 불능 code (라) 동작점 불일치 toy; 불일치 상태 값·소자 열 칸 포함)는 **IT-2·EO-1 가운데 늦게 병합되는 card**의 변경이다(O-56 (b)와 같은 규칙; 지금 spec 어휘는 `triode` 하나 `E/authoring/spec_regions.py`이라 `off` 어휘 없이 넣는 행은 죽은 코드; 공용 전도 판정 함수 없이 넣는 불일치 판정은 정본 없는 둘째 판정이거나 그 함수의 선행 사본 -- graph 단일 정본 규칙 1). 갈래 둘:
   - **(S4-가) IT-2가 늦게 병합**(EO-1 공용 함수와 `off` 어휘가 master에 있음): 이 card가 (다) 행을 `region_rows`에 넣는다. V_on = 공용 전도 판정 함수 **곁**에 두는 역함수(EO-1 모듈 안 공개 함수 -- 이름·서명은 EO-1 design 인용, 이 design은 정하지 않는다; 정의 = 그 점의 VDS·VSB에서 봉인 9 전도 정의를 처음 만족하는 VGS, LUT I_off 열 위 1변수 근 -- 계획 N3.3 (a) LUT memo 대상)를 부르는 자리 하나(`region_rows`)를 더한다; 근 풀이 종료 분해능 = 그 점의 tol_V 셀(계획 N3.8 '훑기 점의 I_off 평가 점' -- `tol_v_table(kind, w_key)`의 그 점 VDS 열, 새 상수 없음). 그 호출 자리 하나가 EO-1 완료 조건 (8) (b) '공용 함수 호출 = 봉인 7·9 + 그 행' 단언에 더해진다. 동작점 불일치 묶음(아래 3)도 이 card가 맡는다 -- 노드 풀이 블록의 판정 자리 = 공용 전도 판정 함수 호출 하나(같은 (8) (b) 단언에 더해짐); 상태 값·소자 열 칸을 둘지는 실을 cfg 항목이 대상 없다는 사실(위 (가))로 EO-1 design이 정한다(4.7-2 'S-4 갈래 몫의 꼴'). IT-2b 착수 때 갈래는 (S4-나)로 정해졌다(4.7-7 D). test = 4.7-7 D의 `off` 변형과 불일치 toy(이 card 판정, 계획 (9)가 N6.20 (8)(e)(i)~(iii)와 같은 단언을 짐).
   - **(S4-나) EO-1이 늦게 병합**: 이 card에는 (다) 행·V_on 호출·`off` toy와 동작점 불일치 묶음이 **없다**(불일치 상태 값·소자 열 칸·그 metric code는 정의도 없다). `region_rows`의 `kind` 값은 {`"sat"`, `"triode"`}뿐이고, 4.7-7 D가 계획 완료 조건 (9) (b)~(d) 꼴로 부재를 단언한다(행 `kind` 집합, 경계 행 계산의 정적 AST 검사, 불일치 정의 포함 0 -- 죽은 코드 없음의 증거; 옛 문언 '4.7-7 L7'(그런 항목 없음)·'`git grep` 호출 0'은 D와 계획 (9) (c)의 AST 측정으로 바꿈). (다) 행·`off` toy·동작점 불일치 묶음은 EO-1 design·test 몫이고 위 (S4-가)의 꼴(행 원소·V_on 자리·분해능·판정 호출 자리 하나·상태 칸 꼴)을 그대로 인용한다.
   - **갈래는 IT-2b 착수 때 한 번 정한다**(계획 v6.33 N6.6 범위 1 '갈래'): 오케스트레이터가 master의 EO-1 병합 여부로 정하고 IT-2 판정 card(IT-2b~IT-2d) 모두 같은 갈래이며 기록 = IT-2 card 재동결(design은 둘 다 정한다). (S4-나)로 정하면 **EO-1은 IT-1 + IT-2 통합 병합 뒤에 병합**한다(병합 순서 고정 -- `off` 경계 행도 같음, 계획 N6.1 EO-1 행). (다)에 tol을 더하지 않는다(상수 발명 금지).
3. **동작점 불일치**(O-53 B1·O-55 U1, 검증 M1 정정 -- 옛 '사유 없는 `unmeasured`' 대체; **위 2 S-4 갈래를 따른다** -- 사용자 결정 O-98, 이 3의 판정 점·판정 함수·기록·metric code·toy는 모두 동작점 불일치 묶음이라 (S4-가)면 이 card, (S4-나)면 card EO-1 몫이고 (S4-나)의 IT-2에는 아래 4 '(S4-나) 기간의 동작'만 있다): 선언된 `triode`·`off` 소자가 동작점에서 선언 영역과 어긋나면 창을 내지 않는다. 불일치 종류는 셋 -- 선언 `triode` 소자가 동작점에서 포화, 선언 `triode` 소자가 꺼짐, 선언 `off` 소자가 전도. 거부 자체는 봉인 게이트(계획 N3.6 표 7·9행, card EO-1 범위 4 (b))가 '선언 오류'로 낸다(노드 풀이 블록은 봉인 전이라 거부하지 않는다).
   - **판정 점 = 커널 마지막 풀이**((S4-가) 이 card / (S4-나) EO-1 몫 -- 4.7-3 1의 마지막 `override` 풀이 해 -- 그 해가 평가 스냅샷이 되어 봉인이 같은 점을 본다; 입력 DC 미선언 뿌리도 이 점이 동작점이다). 측정 구성 블록(4.7-3b)은 이 판정을 다시 하지 않는다(봉인 실패 점에서는 돌지 않는다).
   - **판정 함수·기준 = 봉인 7·9와 같은 것**((S4-가) 이 card / (S4-나) EO-1 몫 -- 블록의 판정 자리 = 공용 전도 판정 함수 호출 하나, 계획 N6.20 완료 조건 (8)(e)(ii)(라)): `off` = card EO-1의 공용 전도 판정 함수(O-55 U2 -- 봉인 9가 바로 부르는 함수), `triode` = 봉인 7의 triode 대조와 같은 함수·기준(여유 = 계획 N3.8 '소자 조건'의 `triode` 경계 판정 여유, 사용자 결정 O-58 T-1; 봉인 7 대조도 같은 기준 -- 계획 N3.6 표 7행, 맡는 card EO-1 N6.20 범위 (4) (b); tol_VDsat = `sat_threshold` 값). 이 블록은 행 여유 부호로 따로 판정하지 않는다(정본 하나 -- tol 띠의 소자를 블록과 봉인이 다르게 보는 일이 없게).
   - **기록**((S4-가) 이 card / (S4-나) EO-1 몫 -- 상태 값·소자 열 칸·metric code를 두면 그 card가 같은 변경에서 더한다): v1.13.0(계획 v6.34 셋째 커밋 N6.6 범위 1 (가)·재검증 S-1): 실을 창 항목 = 측정 구성 판정 창(`node.dc_window_cfg`) 항목(D1로 커널 θ 프레임 창에는 입력 포트 항목이 W4 뿌리뿐이고 metric이 읽는 포트 창은 cfg 하나)인데, 그 점은 같은 점 봉인 거부라 측정 구성 블록이 돌지 않으므로 **cfg 항목의 불일치 상태는 대상 없음**이다(4.7-3b '커널 상태 이어받기 없음' (다)와 같은 사실). 그 귀결로 그 창으로 부른 metric 함수의 불일치 code(`input_window_operating_point_mismatch`)도 운영 경로에서 불릴 자리가 없다(계획 작성자 도출) -- 상태 값·소자 열 칸·code를 둘지는 EO-1 design이 이 사실로 정하고(만들면 배선), 두지 않으면 불일치 toy는 같은 점 봉인 거부 단언만 진다(계획 같은 문단). 불일치 판정 결과(어긋난 소자)는 봉인 7·9의 거부 기록(선언 오류)에 남는다.
   - 선언 없는 소자의 비포화는 봉인 7·9 거부(그대로, O-55 U1 '설계 실패').
4. **훑기 도중 이탈 = 범위 끝**(O-54): 위 행 셋의 첫 영(0) 교차가 창 끝이다 -- 측정 거부가 아니다. 지금 `saturation_window`의 끝 정의(행마다 a·Δx + 여유 ≥ 0의 교집합)가 그대로 이 뜻이다. **(S4-나) 기간의 동작**(사용자 결정 O-100 수락 -- **원래 취지와 다름(작음, 발동 0)**, 계획 v6.33 N6.6 범위 1): 동작점에서 여유가 음수인 선언 `triode` 행(동작점에서 포화인 선언 소자)도 선언 없는 행과 같은 끝 식에 그대로 들어간다 -- 특별 처리 0(판정 함수가 없으므로 이 블록이 행 여유 부호로 따로 판정하지 않는다, 위 3). 그래서 그 창은 동작점 x₀를 포함하지 않거나 lo > hi일 수 있고, EO-1 병합까지 봉인이 그 점을 막지 않는다(봉인 7은 선언 소자를 빼기만 함). 코퍼스 13회로는 `intended_region`이 모두 미정(CI-18)이라 선언 소자 0개. **백로그 메모 B71**(gap §5): 선언 `triode` 소자가 동작점에서 **꺼짐**인 경우의 (S4-나) 동작(행 여유 식이 꺼진 소자에서 무엇을 내는지)은 정해져 있지 않다 -- 계획 몫(발동 0).
5. 측정 구성 판정 창(4.7-3b (4))도 같은 `region_rows`를 봉인점 노드 전압(`node.dc_v` ∪ `node.dc_rail_v`)에서 부른다(행 셋 정본 하나 -- 다듬은 창은 없다, v1.13.0). headroom-chain HC-S(`sat_threshold`)가 같은 자리를 고치므로 순서는 **IT-1·IT-2 → HC-S**(그대로), `device.dc_sat_v`의 `off` 갈래는 O-56 (b)로 HC-S·EO-1 몫이다(이 card 아님). **6. 전도 행 R0**(계획 v6.36 N3.8 '측정 구성 창 행 = 포화 행 + 전도 행 (R0)'·N6.6 범위 1 '측정 구성 창 전도 행', 사용자 결정 O-118 2번 -- 정의는 계획, 인용만; **원래 취지와 다름(승인 O-118)**: O-108 '일정 오차 감수'의 일정이 넓어짐 -- 약반전 소자는 1차 접선이 먼저 0에 닿아 차단을 앞당겨 잡음, ngcc 위 끝 −146 mV(servo)·−376 mV(L 구성), 판정은 안전 쪽, 개선은 백로그 I-H3): 측정 구성 판정 창(과 DE-1 뒤 정의 창)의 경계 행에만 더한다 -- 커널 θ 프레임 창 `node.dc_window`에는 없다(계획 '측정 구성 판정 창·정의 창의 경계 행'). **만드는 자리 = `E/metrics/icm_config.py` 비공개 함수 `_conduction_rows(circuit, ss_values, ops, floors)`**(`region_rows`와 다른 함수 -- 아래 '(9)과의 관계'): `device.dc_conduction_floor`(writer `dc_seal_conduction`, `E/sizing/seal_conduction.py`)에 값이 있는 MOS마다 행 하나 = `(terms, I0 − I_floor, "conduction")` -- I0 = 봉인점 `device.dc_op`의 `current`(선언 방향 ID, `DeviceOp.current` -- `E/sizing/s2_values.py`), I_floor = `device.dc_conduction_floor`, 극성 부호 σ = `Circuit.kind_sign`, gm·gds·gmb = `device.ss_dev`(`SsDevice`, `E/metrics/ss_types.py`); terms = ((g, σ·gm), (d, σ·gds), (b, σ·gmb), (s, −σ·(gm + gds + gmb))) -- 기울기 Σ 계수·s_넷 = σ·[gm·(s_g − s_s) + gds·(s_d − s_s) + gmb·(s_b − s_s)] = 계획의 k = gm·δVGS′ + gds·δVDS′ − gmb·δVSB′(같은 측정 구성 연립의 노드 감도 s -- 4.7-3b (2); 1차에서 KCL 전류 감도와 같은 값); 같은 넷이 두 단자에 걸리면 계수를 더한다. 그 행의 영 교차 = 선형 예측 I0 + k·Δ가 하한 I_floor에 닿는 점. **하한 고정 = '추정' 선형화**(계획 v6.36 둘째 커밋, 검증 N-4 인용): I_floor는 봉인점 값(I_off/ε)으로 고정한다 -- 포화 행이 VDsat을 봉인점 값으로 두는 것과 같은 선례; 훑기 점마다 I_off·ε을 재는 규칙(계획 N3.8 '훑기 점의 I_off 평가 점', O-36 (5)·O-46 (2))은 정의 쪽(oracle `.dc` 훑기) 규칙이라 충돌하지 않고 정확값은 oracle 전도 점검이 맡는다. I_floor가 None(tol_V 미정)인 소자는 행이 없다(그 점은 봉인 9 행 undefined로 봉인되지 않아 이 블록이 돌지 않으므로 실제로 생기지 않음 -- `seal_conduction.py`); ID ≤ 0 소자는 두 필드에 없어 행이 없다. 새 필드·상수 0, 소자당 곱셈 몇 번. **(9)과의 관계**(둘째 커밋 -- 계획 v6.37 정오 뒤 문언 전제, gap S-1): 계획 완료 조건 (9)(S4-나)(b)는 '`region_rows` 행 `kind` 집합 = {포화, `triode`}, 측정 구성 창 전체 행 `kind` 집합 = {포화, `triode`, 전도}', (c)(ii)는 '`_conduction_rows`는 `device.dc_conduction_floor`를 READS로 읽기만 허용(전도·문턱 계산 0)'으로 읽는다 -- 그래서 R0 행은 `region_rows`가 부르지 않는 별도 함수 `_conduction_rows`에 두고, (c)(i)·(iii)(VGS = 0 `op_point` 호출 0·EO-1 import 0)은 `_conduction_rows`에도 단언한다(4.7-7 L8 (h)); (9)의 취지(EO-1 공용 전도 판정 함수·`off` 행이 선행 사본으로 들어오지 않음)는 R0가 봉인 9 정본 값을 READS로만 읽어 깨지지 않는다. **영 기울기 건너뜀**: `saturation_window`의 `|rate| ≤ sys.float_info.epsilon` 건너뜀은 전도 행(기울기 단위 A/V)에도 그대로 적용된다 -- 단위가 다른 비교라는 사실만 기록한다(gm·gds ≫ eps라 판정 영향 없음, 새 문턱 없음).

**4.7-1a 출력 구조 분류 필드 `node.dc_output_structure` -- 폐지**(계획 v6.34 N3.8 '출력 구조 분류 -- 엔진 필드 없음', 사용자 결정 O-109 D4 -- **원래 취지와 다름, 승인 O-109**; 멈춤 S-OS1·S-OS2와 그 code는 O-109·O-115로 소멸): 측정 구성 감도(4.7-3b)와 출력 스윙(DE-1 (b), O-109 C3)이 두 출력 꼴에서 같은 KCL 계라 구조별 갈래가 없다. **IT-2c 변경에서 지우는 것**(재작성 범위): `E/sizing/writer_plan.py`의 WRITES `("node", "dc_output_structure")`·`_output_structure` 함수·그 호출과 그것만 쓰는 F′ 지역 값(`fixed_prime`)·머리 설명; `E/sizing/s2_values.py`의 `OUTPUT_HIGH_IMPEDANCE`·`OUTPUT_KVL_FIXED`와 `DC_WRITES` `DC_WRITER_PLAN_WRITER` 행의 그 원소; `E/sizing/CONTRACT.md`의 그 문단·소유표 행; `E/_module_map.py` 책임 문장의 그 구절; 그 필드를 단언하는 test(기대 갱신은 test 작성 주체 몫). 13회로 분류표(O-66 (1))는 회로 해석 기록이고 엔진 기준선이 아니다. 정지 회로 처리는 쓰기 계획의 기존 정지 그대로다. 옛 설계 기록(v1.12.2~v1.12.11 취소선 본문·줄 위치) = design 이력 H41-09.

**4.7-3b ICMR 측정 구성 = servo 하나(사용자 결정 O-115·O-116(U-105·U-106); 옛 O-50 G4·O-52·O-53 A-1·A-2 갈래 대체) -- 봉인 뒤 측정 구성 블록**(사용자 결정 O-58 S-1·S-2·O-59 (1), 계획 v6.35 N3.8 'ICMR 측정 구성 -- 정의 하나'·'ICMR 전달 뷰 = DEC-23 gain 전달 뷰 하나'·'차동 출력 -- 정의 본문'·'ICMR servo 감도 -- KCL'·'ICMR 좌표 -- 정의 자리 하나'·'판정 분해능의 정의 자리'·'측정 구성 창 = 선형 감도 끝 하나'·'창 필드', N6.6 범위 1·2, IT-2c 착수 조건 (vii), 완료 조건 (8)(a)~(g)·(10)(b)(c)(d)·(12); 정의 정본 = 계획 N3.8 -- 인용만, 정의 사본 없음. **v1.14.1**(계획 v6.35.1·v6.36, 사용자 결정 O-117·O-118·O-119): ICMR 전달 뷰 = S1v 기본 포트 뷰 READS(spec 로드 칸·`DcInputs` 칸·extras 삭제), 창 행 = 포화·`triode` 행 + 전도 행 R0, F 성분 미선언 포트도 함께 구동, 끝 상태 레일 자름(O-117), card RB-1(N6.25) 대상 없음(계획 N3.8 'IT-2 후속'). **v1.14.0**: 측정 구성 = servo(감지 s를 봉인점 `node.dc_v`에 묶고 여기 방향 e의 ε 하나로 보정, Schur 1칸 -- 단일·차동 출력 같은 연립)와 단일 입력 '회로 그대로' 둘뿐, 선언 되먹임은 읽지 않음; v1.13.0의 KCL 감도(O-108)·이어받기 없음(D2)·분류 없음(D4)·F 성분 판정(S-1)·E 항(O-107)·`Circuit` 접근(U-101 (가′))은 그대로. **원래 취지와 다름**(계획과 같은 문언): 옛 O-25 (2) '출력은 회로가 정하는 대로 따름'·O-50 G4 '선언 되먹임 구성, 없으면 단위 이득 follower'를 servo로 대체 -- 승인 O-115):
- **블록 `icm_config`**(새 `@compute_block`, writer 이름 `icm_config`(상수 `ICM_CONFIG_WRITER`), 파일 `E/metrics/icm_config.py`, 진입점 `icm_config_window`, test `E/tests/metrics/test_icm_config.py`(규칙 H)) = 계획 N3.8 '엔진 쪽 계산 자리'의 '봉인 뒤 블록 하나'. **자리**(W5): `E/metrics/ss_evaluate.py`(`ss_dev` 호출 -- 블록 정의 `E/metrics/ss_linearize.py`) 바로 뒤에 `ss_nodal` → `icm_config` 순으로 부른다(같은 `**keys` -- donors·counters). 호출 조건 = `metrics_aux` 호출 조건과 같음(`ss_evaluate.py` `if aux_requests or views` -- 그 조건 밖에서는 두 블록의 소비자가 돌지 않으므로 부르지 않는다). 등록 = `SS_WRITES`(`E/sizing/s2_values.py`)에 `(ICM_CONFIG_WRITER, (("node", "dc_window_cfg"), ("graph", "icm_config")))`. θ 프레임 창 `node.dc_window`(writer `dc_columns`, 소비자 `E/search/fd_jacobian.py`)는 바꾸지 않는다(O-58 S-1).
  - **READS** = 공용 `Circuit`(4.7-4)이 읽는 열(`node.dc_writer`·`node.dc_rail_v`·`node.port_direction`·`device.pins`·`device.kind`·`device.bulk`·`device.dc_L`·`device.dc_colour`·`device.dc_coord` -- 모두 `dc_columns` READS의 부분집합) + `("node", "dc_v")`(봉인점 노드 전압 -- `region_rows` 입력이자 servo 감지 기준값·`vcm0`; U-101 (가′)) + `("graph", "ss_nodal")` + `("device", "dc_tol_v")`(cfg `tol_v` -- 4.7-2) + **`("graph", "views")`**(S1v 뷰 목록 -- ICMR 전달 뷰, 아래) + **`("node", "port_role")`**(S1 -- 차동 출력 감지 부호 p/n) + **`("device", "ss_dev")`·`("device", "dc_op")`·`("device", "dc_conduction_floor")`**(전도 행 R0의 gm·gds·gmb·I0·하한 -- 4.7-3a 6). **뺀 것**: v1.14.0에서 DC 되먹임 판정만 읽던 S1 넷(`device.element_class`·`device.dc_nets`·`device.unsupported`·`node.is_rail`). **없는 것**: `("node", "dc_window")`(D2 -- 계획 완료 조건 (12)(d)), `("node", "dc_output_structure")`(D4). extras = **(LUT, 선형 선언 소자 frozenset)** 둘, 늘 이 둘. **ICMR 전달 뷰 입력**(계획 v6.36 N3.8 'ICMR 전달 뷰 = 기본 포트 뷰', 사용자 결정 O-118 6번 -- **원래 취지와 다름(승인 O-118)**: O-117의 '판정 gain 제약에서 고름'을 버림; v1.14.0의 `SizingSpecDoc.icmr_view`·`DcInputs.icm_view`·extras 셋째 원소는 **삭제**, gap G-1·S-1 해소): 기존 S1v writer `s1v_fields`(`E/graph/s1v_fields.py:249-297`)가 선언 뷰 유무와 무관하게 **기본 포트 뷰를 `("graph", "views")`에 늘 하나 둔다** -- `collect_views`(`E/graph/views.py:77-84`)의 `_declared(spec) or _default(model)`을 '선언 씨앗 다음에 기본 씨앗을 늘 붙이고 같은 (여기, 감지) 키는 `setdefault`로 먼저 온 씨앗 하나로 합침'으로 바꾼다(같은 writer의 출력 규칙 변경 -- 새 생산자·새 계산 아님; 선언 씨앗이 먼저라 같은 키에서는 출처 `spec_constraint_view`가 남아 `_constrained_keys`(`s1v_fields.py:117-123`)의 gain·pm 키 집합이 바뀌지 않는다). **식별(design 몫 -- 계획 '목록 안 순서와 식별 방법은 design') = 새 칸 `ViewSeed.default_port`·`ViewS1v.default_port`(bool, 기본 False)**: `collect_views`가 씨앗의 (여기, 감지) 키가 `_default(model)` 키 집합 안이면 True로 두고(같은 키로 합쳐진 선언 씨앗 포함), `analyze_view`가 그 값을 `ViewS1v`로 옮긴다; 목록 순서는 지금처럼 키 정렬 그대로; 순서·출처로 식별하지 않는 근거(둘째 커밋, 검증 S-2 -- 옛 근거 'GB4 첫 뷰가 12회로에서 바뀜'은 틀림: GB4는 첫 transfer 뷰를 고르고 12회로는 전달 뷰가 합쳐진 기본 뷰 하나뿐이라 순서와 무관하게 같다, `E/metrics/achievability.py:348`): `source`는 `_constrained_keys`(`E/graph/s1v_fields.py:117-123`)가 DECLARED 출처로 gain·pm 키를 모으는 칸이라 다시 쓸 수 없고, 순서에 뜻을 실으면 graph 규칙 3(같은 칸에 두 뜻 금지)에 어긋난다. `icm_config`는 `("graph", "views")`에서 `kind == "transfer"`이고 `default_port`가 True인 뷰를 고르고(재유도 0 -- 여기 가중·감지 넷은 그 뷰의 `excite`·`sense` 칸을 읽음), DE-1 (c)의 A_dc도 같은 뷰를 READS로 읽는다(a_e·A_dc 늘 같은 뷰 -- I-H2 합치기 무조건 성립, 4.7-9). **S1v 지문 영향**(계획 v6.36 'S1v 지문 영향' 인용 + 이 design의 식별 칸 몫 -- 보고 항목): (가) **뷰 추가 몫** = 선언 뷰가 있고 그 (여기, 감지)가 기본 뷰와 다른 회로에서만 뷰 하나가 더해진다 -- 계획 착수 실측 (d) grep 사실: 12회로는 제약 view 미선언(로더 기본 port 뷰라 같은 키로 합쳐짐) → 변화 0, current_reuse는 view 미선언 제약의 기본 port 씨앗이 같은 키로 합쳐져 변화 0(계획 v6.36 셋째 커밋 재검증 N-1 -- 착수 실측으로 확인) (나) **식별 칸 몫** = `ViewS1v`에 칸이 하나 늘어 13회로 모두 `("graph", "views")` 값 지문이 한 번 바뀐다(다른 칸 값 변화 0; READS 소비자 여섯 `E/graph/coupling_vars.py:170`·`E/metrics/metric_structure.py:30`·`E/metrics/achievability.py:334`·`E/search/start_intervals.py:238`·`E/search/noise_decl.py:33`·`E/search/iv_context.py:91`의 입력 버전도 한 번 바뀜 -- 그 소비자 값 변화 기대 0, 착수 실측 (d)가 회로별로 잼) -- 계획 문장('선언 뷰가 기본 뷰와 다른 회로에서만 바뀐다')은 뷰 추가 몫만 적었다(**계획 문장과 맞춰 볼 항목** -- 보고). 어차피 `views.py`·`s1v_fields.py`·`s1v_values.py` 바이트 변경으로 S1v 규칙 지문(`S1V_RULE_FILES`, `s1v_values.py:14`)과 블록 코드 해시가 13회로 모두 바뀐다. θ 성분·`fixed_values`·`resistor_values`·spec 되먹임 선언은 받지 않는다(O-115). `Circuit`에는 이름으로 넘긴다: `Circuit(projection, lut=…, linear=…)`(4.7-4 '이름 계약').
  - **WRITES** = `("node", "dc_window_cfg")`(**측정 구성 판정 창** -- 입력 포트마다, 값 꼴 = `node.dc_window`와 같은 `Window` 하나, +tol_VDsat, KCL 선형 감도 끝 '추정'; 모든 측정 구성(`"servo"`·`"as_is_single_input"`)에서 쓰고 구성 None이면 쓰지 않음; 상태·`tol_v` = 4.7-2 '값 형식'(이 블록이 스스로 정함, 이어받기 없음); 자기 측정 실패 꼴 = `Window(None, None, 0, input_status="unmeasured")`) · `("graph", "icm_config")`(값 `IcmConfig` -- frozen dataclass, `E/metrics/aux_types.py`, **칸 = `config`·`pivot_a_e`·`pivot_resolution`·`vcm0`·`vcm_lo`·`vcm_hi`·`undefined`**(계획 IT-2c 착수 조건 (vii)): `config` ∈ {`"servo"`, `"as_is_single_input"`} 또는 None(정의 불능; 이름 = design -- 소비 = `metrics_aux`의 None 갈래, 값 자체는 결과 JSON 표기); `pivot_a_e`: float 또는 None(servo 피벗 a_e = 여기 방향 e → 감지 s의 봉인점 DC 극한 전달(V/V, e 가중 = 그 뷰의 여기 가중 그대로) -- **모든 config에서 쓴다**(`"as_is_single_input"`은 여기 방향 = 그 입력, 계획 N3.8 '실행 조건'), 풀이 특이면 None; 옛 포트별 T_p 칸 `transfer` 대체); `pivot_resolution`: float 또는 None(= δA_num = δV_out / 레일 폭(V/V), 아래 '판정 분해능 정의 함수 하나'); **피벗 두 칸은 출력 전용**(엔진 소비자 0 -- 결과 JSON·변화표; card DE-1 (c)가 DEC-23 A_dc와 감지 자리·e 가중이 같으면 이 칸을 정본으로 합친다 -- 계획 N3.8 'a_e와 DEC-23 A_dc의 축'·N5.3 I-H2, 셋째 생산자 금지); `vcm0`·`vcm_lo`·`vcm_hi`: float 또는 None(V -- **V_cm 칸**, 계획 N3.8 'V_cm의 정본 자리'(U-106): V_cm = 입력 포트 전압의 평균, `vcm0` = 봉인점 값, `vcm_lo`·`vcm_hi` = 아래·위 끝 상태의 값; 계산 = 아래 계산 (6); 소비자 = `metrics_aux`의 세 metric(4.7-5) -- 포트 창에서 V_cm을 다시 계산하는 둘째 생산자 금지); `undefined`: tuple[`Undefined`]). **삭제**(계획 완료 조건 (8)(f) -- 만들면 배선): 칸 `inverting_port`·`tied_ports`·`transfer`, `config` 값 `"declared_feedback"`·`"follower_beta1"`. 출력 구조 분류 칸 없음(v1.13.0 D4). **옛 `kvl` 칸(포트별 선형 감도 끝)은 두지 않는다**(사용자 결정 O-61 P3 -- 같은 정의의 양 두 칸 금지, graph 단일 정본 규칙 3): 모든 측정 구성 포트의 끝은 `node.dc_window_cfg` 한 칸에만 있다(V_cm 칸은 포트 끝과 정의가 다른 양 -- 같은 끝 상태의 포트 평균이고 P2 [min, max] 정렬 뒤 포트 창에서 복원되지 않는다, 계획 N3.8 'V_cm의 정본 자리'). **정의 창 `node.dc_window_def`**: writer 자리 = 이 블록, 값은 card DE-1 (a)가 쓴다 -- IT-2는 쓰지 않는다(생산자만 있고 소비자 없는 칸을 만들지 않는다).
  - **소비자**(새 필드·칸마다 ≥ 1 또는 출력 전용 선언 -- 계획 N6.6 완료 조건 (5)): `node.dc_window_cfg` → `metrics_aux`(포트 정의 불능 판정·보고 `IcmPort` 열 -- 4.7-5; 커널 ICMR 선언 제약·front·보고는 그 metric 값을 읽음, O-109 C1); `graph.icm_config` → `metrics_aux`(V_cm 칸으로 세 metric, `config` None 갈래 `undefined` -- 4.7-5 M7 경로); 피벗 두 칸은 출력 전용(위). 옛 소비 `tied_ports` 포트 거르기·P3 묶음 빼기·보고 'β = 1 기본' 표기는 삭제(계획 IT-2c 착수 조건 (vii)).
  - **계산(한 연립 -- 계획 N3.8 'ICMR servo 감도 -- KCL')**: (1) **갈래**(정의 불능 = `config` None, `IcmConfig.undefined`에 code 하나, `node.dc_window_cfg` 쓰지 않음 -- 4.7-5 M7 경로; 모두 category `definitional`; 아래 순서로 처음 걸린 하나; 계획 v6.36 N3.8 'ICMR 전달 뷰 = 기본 포트 뷰'의 정의 불능 셋): ① `graph.ss_nodal`이 `Undefined`이면 그 code·detail 그대로(`passive_value_undeclared` -- 아래 `graph.ss_nodal`) ② 입력 포트(`node.port_direction == "input"`) 셋 이상 → **`icm_inputs_unsupported`**(detail `(("inputs", 포트 넷 tuple),)` -- 계획 '입력 포트가 셋 이상인 회로'(물리 규칙 미확인)의 정의 불능, 기존 어휘에 같은 뜻 없음 -- v1.14.0 검증 §3 수용; 13회로 0개) ③ **기본 포트 뷰를 만들 수 없음** -- 입력 포트 0개(`default_port` 뷰 0 -- 둘째 커밋, gap N-6 사실 정정: `collect_views`는 씨앗이 하나도 없을 때만 `view_required`를 기록한다(`E/graph/views.py:83-85`); 선언 뷰가 있고 입력이 0이면 기록 없이 `default_port` 뷰만 0이 된다 -- 이 갈래의 판정 결과는 같다) → 기존 어휘 **`view_required`**(`E/graph/views.py:84`·`E/graph/s1v_values.py:157` `F_VIEW_REQUIRED`와 같은 문자열, detail `(("default_views", 0),)`) ④ **기본 포트 뷰가 하나로 정해지지 않음** -- `default_port` 전달 뷰가 둘 이상(2입력인데 role이 차동쌍이 아니어서 `_default`가 입력마다 뷰를 냄) 또는 그 뷰의 감지가 출력 하나도 차동쌍도 아님(감지 넷 0, 또는 둘 이상인데 `node.port_role`이 `differential_output_p`·`_n` 한 쌍이 아님) → 같은 **`view_required`**(detail `(("default_views", 수),)` 또는 `(("sense", 넷 tuple),)` -- 고칠 자리가 같다: 포트 role 또는 topology 포트; 새 code 없음) ⑤ 입력 포트 하나 → `"as_is_single_input"`(아래 (5)) ⑥ (servo만) 레일 폭 0·레일 값 없음·연립 특이·\|a_e\|·레일 폭 ≤ δV_out → **`icm_servo_pivot_unresolved`**(옛 `icm_inverting_port_unresolved` 대체 이름, detail `(("rail_span", span),)`·`(("singular", True),)`·`(("a_e", a_e), ("resolution", δA_num))`; 계획 N3.8 '판정 분해능' 한 꼴). **v1.14.1 삭제**(생산 경로 0 -- 만들면 배선): `icm_view_ambiguous`(옛 '판정 gain 제약 뷰 둘 이상' -- v6.36이 gain 선언 뷰를 읽지 않아 대상 소멸), v1.14.0 ⑤ '여기 넷이 입력 밖 → `view_required`'(기본 뷰의 여기는 정의상 입력 포트 -- 계획 '대상이 사라진다'; 검증 N-1·gap S-2 해소), `icm_excite_common_mode`(e ∥ CM -- 기본 포트 뷰 servo는 차동쌍 가중 ±1/\|D\|라 가중 합이 0이어서 CM과 평행일 수 없다; 계획 v6.36 정의 불능 목록에는 'e가 CM 방향과 평행'이 남아 있으나 기본 뷰만 쓰면 도달 0 -- 보고 항목), 이 블록의 `no_input_port` 갈래(입력 0은 ③). 포트 role 이름·회로 이름은 결과를 정하지 않는다(기본 뷰 가중은 role에서 오지만 맞바꾸면 e → −e이고 부호가 ε에 흡수돼 끝 상태·metric이 같다 -- 계획 N3.8 '포트 role'; 차동 출력 감지 p/n을 맞바꾸면 c → −c라 δs = 0이 같다). **입력 두 개(차동쌍 기본 뷰) = `"servo"`**. (2) **servo 감도**(계획 N3.8 'ICMR servo 감도 -- KCL'·'차동 출력 -- 정의 본문', O-108·O-115): 봉인점 DC 야코비안 `graph.ss_nodal`(W·바이어스 전압 고정 KCL, 용량 개방, 고정 = ac 접지 ∪ 입력 넷)에서 입력 포트를 모두 같은 x로 움직이는 구동의 응답 vx와 여기 방향 e로 움직이는 구동의 응답 ve(같은 인수분해 위 `nodal_solve` 두 번)를 내고, 감지 c(그 기본 포트 뷰의 `sense` 넷 -- 단일 출력 = e_out, 차동 출력 = e_p − e_n, p/n = `node.port_role` `differential_output_p`/`_n`; 여기 e = 그 뷰의 `excite` 가중)의 행 δs = 0을 Schur 1칸으로 강제한다: 노드 감도 s_n = vx_n − ve_n·(c·vx / c·ve), servo 피벗 a_e = c·ve. 차동 출력은 차동 모드 V_op − V_on만 봉인점 차에 묶고 출력 공통모드는 회로의 CMFB가 정한다(행 없음) -- 단일 출력과 같은 1칸·같은 블록이라 구조별 갈래가 없다. 출력이 W3 목표 노드여도 같다(이 계에서 W3 목표 넷은 미지수). θ 감도(`writer_grad`·`_sensitivities`)는 부르지 않는다(L10 (d)); 출력 구조 분류 읽기 없음(D4). (3) **진입점** = 같은 파일의 공개 함수 **`kvl_sensitivity(nodal, drive, servo=None) -> tuple[dict[str, float], float | None, ndarray | None] | None`**(DE-1 design이 인용): `drive` = x로 함께 움직이는 입력 포트 넷 tuple(각 1), `servo` = None(보정 없음 -- `"as_is_single_input"`·DE-1 (b) 차동 훑기) | `(excite, sense, span)`(excite = ((넷, e 가중), ...), sense = ((넷, 부호), ...), span = 레일 폭(V)); 풀이 = vx = `nodal_solve(factor, size, {p: 1})`, servo면 ve = `nodal_solve(factor, size, {p: span·e_p})`(구동 = 레일 폭 -- 판정 분해능 정의의 구동과 같은 해, 아래 `_transfer_resolution`이 그 해를 그대로 씀, 풀이 추가 0), a_e = (c·ve) / span, s_n = vx_n − (ve_n / span)·(c·vx) / a_e. 반환 = (slope {넷: dV/dx}(`nodal.nodes` 이름으로; 구동 넷 = 1 − e_p·(c·vx)/a_e, 그 밖 고정 넷·`floating` 0), a_e(servo None이면 None), ve 전압 벡터(servo None이면 None)); 인수분해 특이(`nodal_solve` None)·a_e = 0이면 None(fail-closed -- 연립 특이; 0 아닌 작은 a_e는 ⑥의 판정 분해능이 거른다 -- 옛 백로그 B75 '닫음 분모 정확 0만'의 빈틈은 \|a_e\| 판정으로 닫힘). 새 인수분해·새 풀이기 없음(Schur 보완 1칸, 크기 고정 순풀이 아님 -- O-32). 옛 `closure` 인자(`("follower", u, out)`·`("node_kcl", u)`)와 닫힘 행 k = 2 일반화(RB-1)는 만들지 않는다(계획 N3.8 'IT-2 후속'). DE-1 (a) 정의 창·DE-1 (b) 출력 스윙은 이 연립을 기준·구동만 바꿔 재사용한다(스윙 = 차동 훑기·servo None, 사본 금지 -- 계획 O-58 S-2·O-109 C2·C3, 4.7-9). (4) **영역 경계 행과 창 끝 = `saturation_window` 호출**(사용자 결정 O-61 P2 -- 창 끝 함수 하나·부르는 자리 둘; 이 블록은 끝 식을 다시 쓰지 않는다): (i) 행 = `Circuit.region_rows(values)`(포화·`triode` 행 -- 4.7-3a 1, values = 봉인점 `node.dc_v` ∪ `node.dc_rail_v`) + `_conduction_rows(…)`(전도 행 R0 -- 4.7-3a 6, v1.14.1; 행 꼴 = 일반 1차 행 `(terms, slack, kind)`) (ii) 구동 = **P3 묶음 = 모든 입력 포트**(계획 IT-2c 착수 조건 (vii); servo는 입력 포트를 출력에 묶지 않는다, O-53 A-2 갈래 소멸; F 성분 미선언 포트 포함, 구동 = `graph.ss_nodal`의 입력 넷 그대로, O-118 3번) (iii) 감도 = `kvl_sensitivity(nodal, drive, servo)`의 slope (iv) 이동량 창 = `saturation_window(None, None, None, None, rows, slope=slope)` → (dlo, dhi) (v) **끝 상태 = 레일 안 입력**(계획 v6.35.1 N3.8 '레일 자름' -- 끝 상태에서 어느 입력 포트라도 레일 밖이면 그 상태는 범위 밖; **원래 취지와 다름(승인됨 O-117)**: O-49 P2·as-built '창 ∩ 레일'(포트별)을 끝 상태 단위로 바꿈 -- gap S-5 해소): [dlo, dhi]를 입력 포트마다 rail_min ≤ V_p0 + s_p·Δ ≤ rail_max(s_p ≠ 0인 포트)로 좁힌 [Δlo, Δhi] -- 레일 밖 입력 불허(40 §3.8-8 `icmr_v` 행의 기존 규칙)를 포트별 자름 대신 끝 상태에 걸어 포트 끝과 V_cm 끝이 같은 끝 상태에서 나오게 한다(계획 완료 조건 (8)(g)) (vi) 포트 창 = [Δlo, Δhi]에서 4.7-3 2 포트 창 규칙(P2 [min, max]; 레일 자름은 (v)로 이미 충족, s_p = 0이면 V_p -- `Circuit.port_window`)으로 입력 포트마다 (vii) **삭제**(F 성분 미선언 포트도 구동하고 그 항목은 다른 포트와 같다; O-118 3번, 4.7-3 3) (viii) (i)·(iii)·(iv) 가운데 하나라도 None이면 모든 입력 포트 항목을 `"unmeasured"`로 쓴다. 측정 구성 창은 모든 구성에서 이 선형 감도 끝 하나다(계획 N3.8 '측정 구성 창 = 선형 감도 끝 하나', O-109 C1). (5) **`"as_is_single_input"`**(계획 N3.8 '단일 입력 회로의 ICMR' -- 보정할 입력 자유도가 없음): 구동 = 그 입력 포트, `servo` = None(출력은 회로 자신의 DC 관계로 따름 -- (3)과 같은 정본); a_e 기록 = 같은 인수분해에서 구동 = 레일 폭·그 입력 하나의 `nodal_solve` 한 번(a_e = c·v / span, 그 해로 `_transfer_resolution`) -- 이 갈래는 피벗 판정을 하지 않는다(창이 a_e에 기대지 않음; 칸은 출력 전용 기록), 그 풀이가 특이·레일 폭 0이면 피벗 두 칸 None. (6) **V_cm 칸**(계획 N3.8 'ICMR 좌표 -- 정의 자리 하나'·'V_cm의 정본 자리', U-106): `vcm0` = Σ_p `node.dc_v`[p] / n(n = 입력 포트 수); 끝 상태 Δ에서 V_cm(Δ) = `vcm0` + s̄·Δ(s̄ = Σ_p s_p / n -- 같은 slope의 입력 포트 평균, 포트 창을 읽지 않음); `vcm_lo` = min(V_cm(Δlo), V_cm(Δhi)), `vcm_hi` = max(…)(s̄ < 0이면 아래 끝 상태가 위 V_cm -- P2와 같은 정렬을 끝 상태 쌍에 한 번); s̄ = 0이면 두 끝 = `vcm0`(0·inf 회피 -- 4.7-3 2 G6과 같은 규칙); 기본 뷰(e의 CM 성분 0)이면 s̄ = 1이라 V_cm = x0 + Δ끝. **한 포트라도 항목이 `"unmeasured"`이면 `vcm_lo`·`vcm_hi` = None**(계획 'V_cm 칸과 세 metric이 정의 불능' -- 사유는 그 포트 항목 상태로 metric에 실림, 4.7-5), `vcm0`는 봉인점 값이라 그대로. 포트 끝과 V_cm 끝은 같은 블록이 같은 연립에서 내는 두 칸이라 둘째 생산자가 아니다(완료 조건 (8)(g) 일치 단언).
  - **판정 분해능 정의 함수 하나**(v1.12.4·v1.13.0, v1.14.0 대상 = servo 피벗 a_e -- 계획 v6.35 N3.8 '판정 분해능의 정의 자리', 정의 정본 = 계획, 인용만; 사용자 결정 O-107(**원래 취지와 같음**)·O-71·O-68 (1)·O-67 (3); 근거 `wt/_drafts/evidence/2026-10-22/it2c_dvout_cancellation.md` §1·§3 (A)): 판정 = \|A\|·(V_rail,max − V_rail,min) ≤ δV_out이면 판정 불능, **엔진 δV_out = \|z_u\|ᵀ(\|r\| + E\|v\|)(V)**. **함수** = `_transfer_resolution(system, volt, sense) -> float | None`(δV_out, V) -- `E/metrics/icm_config.py` 안 비공개 함수 하나(IT-2에서 부르는 자리 = 이 블록의 a_e 판정·기록 하나). 계산(블록 안 지역 계산, 새 필드·생산자·상수 없음): (i) r = `coupling @ volt − inject[unknown]`(A) -- `nodal_factor`의 `coupling = g[unknown, :]`(`E/metrics/_helpers_nodal.py:43`), `nodal_solve`의 `rhs = inject[unknown] − coupling @ volt`(`:65`)·`volt[unknown] = x`(`:67`)라 = G_uu·x̂ − rhs (ii) z = `nodal_adjoint(system.factor, len(system.nodes), sense)`(`:73-82`; 단일 출력 = 출력 노드 단위 벡터, 차동 출력 = e_p − e_n의 수반 하나) (iii) **E 항** = `system.g_bound[unknown, :] @ |volt|`(E = `NodalSystem.g_bound` READS) (iv) δV_out = Σ \|z[unknown]\|·(\|r\| + E 항). `volt`·`z`가 None이면 None. 1차 상한(O(u²) 항·수반 z 계산 오차 제외). **구동** = 레일 폭: `volt` = `kvl_sensitivity`가 낸 ve(servo -- 구동 {p: span·e_p}) 또는 계산 (5)의 레일 폭 단일 입력 해 -- 전달 풀이와 분해능이 같은 해(풀이 추가 0); 판정 \|c·volt\| ≤ δV_out(⇔ \|a_e\| ≤ δA_num = δV_out / span). span = `node.dc_rail_v`(writer `dc_rails`, 이 블록 READS)의 레일 값 최대 − 최소(선언 `supplies_v` 정본 -- `E/sizing/dc_inputs.py:5`, DEC-60). **기록** = `IcmConfig.pivot_resolution` = δA_num(출력 전용). **fail-closed**: span = 0·레일 값 없음·특이 → servo는 `icm_servo_pivot_unresolved`(계산 (1) ⑥), `"as_is_single_input"`은 피벗 두 칸 None -- N3.14 적용. **자리 근거(실현 가능성)**: `_helpers_nodal.py`는 `_` 모듈이라 구조 규칙 A 보충 (3)(`E/tests/structure/README.md:39` -- 공개 함수마다 같은 하위 패키지 다른 파일 2개 이상이 import)을 받아, 호출 자리가 하나인 IT-2에서는 호출 자리 파일 안 비공개 함수로 두고, **card DE-1 (c)가 DEC-23 A_dc 갈래에서 둘째 호출 자리를 더할 때 같은 변경에서 `_helpers_nodal.py`의 공개 함수로 옮긴다**(이동이지 둘째 정의가 아님 -- 4.7-9 DE-1 인계 (8)). **착수 실측 기록**(계획 v6.35 N6.6 'IT-2c 착수 실측', 사용자 결정 O-71 -- 이 design이 다시 재지 않음): (a) `current_reuse_telescopic_ota` 봉인점의 a_e와 δA_num -- 미측정(층 0 시작점 없음, `it2c_circuit_access.md` §5; 그 회로의 gain 제약 view = `{"pending": "MOD5"}`라 ICMR은 기존 실행 전 정지(결정 대기)에 걸린다 -- 계획 재검증 N-a) (b) 진짜 A = 0인 대칭 사례 -- v1.13.0 기록(T_p 기준: 대칭 정확 0 toy 발동, 조립 상쇄 구멍 → O-107 식 정정, `it2c_dvout_cancellation.md` §2 -- 새 식은 toy 8000개·운영 8회로 14포트 모두 덮음); a_e 기준 재측정은 IT-2c 착수 때 (c) 오라클 vntol = 1e-7, reltol = 1e-4(`tools/spice_oracle/legacy_testbench.json:9`) -- 4.7-9 (d) **기본 포트 뷰 성립과 S1v 소비자 값**(계획 v6.36 착수 실측 (d) -- 옛 'ICMR 제약 4회로의 gain 전달 뷰 성립' 대체): 13회로 기본 포트 뷰가 하나로 정의됨(계획 근거 grep -- current_reuse도 정의, 다른 MOD5 표지로 실행 전 정지는 그대로)과, S1v가 기본 포트 뷰를 늘 두는 변경·식별 칸으로 바뀌는 S1v 소비자 값(GB4 첫 전달 뷰 등)을 회로별로 재고 변화표 원인 = v6.36으로 적는다(위 READS '(가)(나)'); 어긋나면 멈추고 보고 (e) **차동 출력 servo 착수 실측**(계획 N6.6) -- `current_reuse_telescopic_ota` 봉인점의 servo 연립 특이 여부·\|a_e\| 판정, 특이·판정 불능이면 멈추고 보고.
  - **정본 칸 -- 모든 측정 구성 포트**(v1.13.0 이름 '정본 칸 포트' -- 계획 v6.34 검증 N-13, 옛 '선형 감도 끝만 정의되는 구성의 정본 칸'·'KVL 고정 포트의 정본 칸'; 계획 N3.8 '측정 구성 창 = 선형 감도 끝 하나', 사용자 결정 O-61 P3·O-63 (4)를 O-109 C1이 모든 측정 구성으로 넓힘 -- **원래 취지와 다름, 승인 O-109**(O-21·O-25 (3)·O-33 (3) '수락 반복·front는 끝 풀이로 다듬음', O-49 P4·P6, O-61 P6, O-64 (2)); 취지 '정본 하나·재계산 0'은 그대로): servo·`as_is_single_input`의 (2)·(5) 연립은 이 블록이 평가마다 한 번 풀고, 그 끝은 `node.dc_window_cfg` **한 칸에만** 쓴다(`graph.icm_config`에 `kvl` 칸 없음 -- 같은 정의의 양 두 칸 금지; servo는 입력을 출력에 묶지 않아 모든 입력 포트가 같은 끝 상태의 항목이다). 커널·front·보고가 모두 그 칸('추정')을 읽는다(4.7-5). 끝 풀이로 다듬은 창(대신호 끝 풀이)과 그 블록·필드·기준 칸, front 전용 입력 CM metric 블록은 두지 않는다(4.7-4 -- 커널 입력 CM metric과 같은 입력·같은 정의라 둘째 생산자). 정확값은 oracle `.dc` 훑기(`.op` 스윕)가 확정하고(기초 가정·DEC-103), 엔진에 W·바이어스 고정 대신호 끝 풀이를 두지 않는다(O-32 순풀이 금지, O-108 무거운 계산 회피). 선형 감도 풀이가 정의되지 않으면(연립 특이 등) 그 끝은 결측 사유(`"unmeasured"`)와 함께 기록하고 그 끝을 읽는 metric은 정의 불능이다(fail-closed, 미검증 외삽 끝 금지 -- (4) (viii)). DE-1 뒤 정의 기준 값은 이 블록이 쓰는 `node.dc_window_def` 한 칸이다(card DE-1 design 몫 -- 재계산 0, 같은 연립을 기준만 바꿔 재사용).
  - **커널 상태 이어받기 없음**(계획 v6.34 N6.6 범위 1 '측정 구성 판정 창은 그 상태를 이어받지 않는다', 사용자 결정 O-109 D2 -- **원래 취지와 다름, 승인 O-109**(O-61 P5 '측정 구성 판정 창도 미수렴 상태를 이어받음'과 O-64 (2) 그 front 값 처리); 판정·기록 자리는 재검증 S-1): 이 블록은 `node.dc_window`를 READS로 읽지 않는다(계획 완료 조건 (12)(d)). (가) **커널 미수렴**: 봉인점이 봉인을 통과한 유효 동작점이면 KCL 측정 구성 창은 y 범위 수렴과 무관하게 정의된다 -- 설계점 질문(θ 변수 y 범위)의 미수렴이 섭동 질문 metric을 정의 불능으로 만들지 않는다(DEC-103). 그 상태는 θ 프레임 창 필드의 출력 전용 상태로만 남는다(4.7-3 1). (나) **F 성분 미선언 포트 -- 대상 없음**(O-118 3번: 그 포트도 함께 구동해 항목은 다른 포트와 같다, 4.7-3 3). (다) 동작점 불일치 점(S-4 갈래 몫 -- 4.7-3a 3)은 봉인 거부라 이 블록이 돌지 않는다 -- cfg 항목의 불일치 상태는 대상 없음((S4-나)의 IT-2에는 그 상태가 없고 그 점은 4.7-3a 4 '(S4-나) 기간의 동작'대로 봉인을 지날 수 있다 -- 그때 이 블록은 보통 점처럼 잰다). (라) **자기 측정 실패**: 4.7-2 '값 형식'의 `"unmeasured"`(행 None·감도 특이·`saturation_window` None; 봉인점 tol_V 미정은 그 행이 undefined라서 봉인되지 않아(`sealed=None`) 이 블록이 돌지 않으므로 대상 없음, test 없음 -- 둘째 커밋). (마) **우선순위**: 상태가 `"measured"`·`"unmeasured"` 둘뿐이라 대상 없음. 모든 구성(`as_is_single_input` 포함)에서 같다.
  - **S-3 선언 되먹임 DC 망 -- 폐지**(사용자 결정 O-115 -- ICMR은 선언 되먹임을 읽지 않는다, 계획 v6.35 N3.8 'ICMR 측정 구성' '선언 되먹임'): 측정 대상 = 봉인점 회로(topology 수동소자 포함) 그대로 = `graph.ss_nodal` 하나라, 선언 소자를 따로 세우는 망·`node_kcl` 닫음·`icm_config_feedback_cut` code·DC 되먹임 판정 갈래(`icm_config_feedback_no_dc`·`icm_config_feedback_element_unsupported`)를 두지 않는다; 13회로의 비지 않은 선언은 library `current_reuse_telescopic_ota` Cf1·Cf2(용량, DC 열림) 하나라 DC 망 변화 0. 옛 착수 실측 '루프 절단 적용'(옛 완료 조건 (10)(a))의 정적 가드는 card TN-1 완료 조건 (3)으로 옮겼다(계획 N6.26 -- 이 design은 인용만).
- **ss 층 필드 `graph.ss_nodal`**(사용자 결정 O-59 (1) -- 봉인점 컨덕턴스 계·인수분해 = ss 층 graph 필드 하나, writer 하나): 새 `@compute_block`, writer 이름 `ss_nodal`(상수 `SS_NODAL_WRITER`), 파일 `E/metrics/ss_nodal.py`, 진입점 `ss_nodal_system`, test `E/tests/metrics/test_ss_nodal.py`. READS = `("graph", "ss_circuit")`·`("device", "kind")`(결측 소자 저항 판정 -- 아래). **봉인점 소신호 회로 = ss 층 graph 필드 하나 `graph.ss_circuit`**(다섯째 커밋 -- 계획 v6.34.1 N3.3 S2 행·N3.8 '엔진 쪽 계산 자리'·N6.6 범위 1·완료 조건 (10)(c)(plan/v6341 `ec9f6db3`·`37d6b7e8`); 넷째 커밋의 공개 함수 `ss_circuit_of`를 대체 -- **원래 취지와 다름(범위 확대: 기존 조립 사본 둘 정리 + `graph.ss_circuit` 신설), 사용자 승인 대상**): 값 = `SsCircuit`(`E/metrics/ss_types.py:40`, frozen dataclass -- `fp_of` dataclass 규칙으로 지문화 가능, `E/core/fingerprint.py`), **writer 블록 하나** = 새 `@compute_block` 함수 **`ss_circuit_field`**(파일 `E/metrics/ss_circuit.py` -- metrics 층 1 그대로, writer 이름 **`ss_circuit`**(상수 `SS_CIRCUIT_WRITER`, `E/sizing/s2_values.py` `METRICS_AUX_WRITER` 옆 -- writer 이름 = 필드 이름 관례, `ss_nodal`과 같음), 등록 `SS_WRITES`에 `(SS_CIRCUIT_WRITER, (("graph", "ss_circuit"),))`; **이름 충돌 확인**(계획 재검증 N-2, integ-it12 `6afe4758` `git grep`): `ss_circuit_field`·`SS_CIRCUIT_WRITER`·필드 `("graph", "ss_circuit")` 0건; 문자열 `"ss_circuit"`은 2건이고 둘 다 기존 함수 이름이다(`E/metrics/__init__.py:337` 함수 export, `E/_module_map.py:773` 진입점 이름 -- v1.13.1 Q-4 정정, integ-it12 `ee9bcf5b` 재측정; 옛 문언 '0건'은 사실과 달랐다); writer 이름 `"ss_circuit"`은 이 두 문자열과 뜻이 다르고, 쓰는 곳 하나는 문자열 grep이 아니라 블록 WRITES와 권한표(`SS_WRITES` 행 하나 → `S2_WRITERS`의 `("graph", "ss_circuit")` writer 하나)로 잰다 -- 같은 이름의 기존 함수 `ss_circuit`(같은 파일, 순수 조립 함수, `metrics.__all__`·`test_ss_circuit.py:41`)과 모듈 `ss_circuit.py`는 그대로 두고 블록 함수 이름만 다르게 한다). 블록 READS = 회로 조립 열 `device.element_class`·`device.kind`·`device.pins`·`device.bulk`·`device.ss_dev`·`device.dc_colour`·`device.passive_value`·`node.ac_ground_class`·`node.dc_colour`·`node.port_direction`, 몸통 = 지금 조립과 같다(정준 순서 = `dc_colour`, 입력 노드 = `INPUT_DIRECTION` 포트, 수동소자 값 = `device.passive_value` 열 → 같은 파일의 `ss_circuit(...)` -- 식·순서 불변). **조립 사본 둘 삭제**(같은 IT-2c 변경): `E/metrics/ss_metrics.py:379-394`(`metrics_ss` 인라인)·`E/metrics/metrics_aux.py:92-105`(`_ss_of`) -- `metrics_ss`·`metrics_aux`·`ss_nodal`은 `graph.ss_circuit`을 READS로 읽는다(셋째 생산자 금지); `metrics_ss`가 쓰는 `ss_values`(`device.ss_dev` 열)·`metrics_aux`가 쓰는 `ss_values`·`device_orbit`(`device.dc_colour` 열)는 계산이 아니라 READS 열 읽기라 각 블록이 자기 READS로 읽는다. **호출 자리** = `ss_evaluate`에서 `ss_dev` 바로 뒤·`metrics_ss` 앞(조건 없음 -- `metrics_ss`가 늘 읽음); 지원 밖 원소 정지(`ss_circuit`의 `StructureUnresolvedError`)는 이 블록에서 난다(같은 예외·detail, 실패 블록 이름만 `metrics_ss` → `ss_circuit` -- 부분 스냅샷은 두 경우 모두 `ss_dev`까지라 같다). **스냅샷 파생**: 봉인 뒤 ss 층 블록이라 keep(base writer ∪ 봉인 4 호출 목록) 밖이고, child 파생 때 지워졌다가 같은 입력 버전이면 S3 색인((블록, 분할, 입력 버전)) graft로 돌아온다(4.7-3c -- 새 cache 없음). **구조 규칙 A**: 블록 `ss_circuit_field`가 같은 파일의 `ss_circuit`을 이름으로 참조하므로 `ss_circuit.py`의 독립 진입점은 블록 하나(`@compute_block` 등록 진입점), 모듈 지도 행 진입점 `ss_circuit` → `ss_circuit_field`. **결측 코드 정의 한 자리**(계획 재검증 N-4): `CODE_PASSIVE_MISSING = "passive_value_undeclared"`를 `E/metrics/ss_circuit.py`(결측 목록 `SsCircuit.missing`을 만드는 파일)에 하나 두고 `ss_metrics.py:71`·`metrics_aux.py:52`의 두 정의를 지워 `metrics_ss`·`metrics_aux`·`ss_nodal`·`icm_config`가 import한다(새 code 이름 없음). **fail-closed -- DC 전도 소자 결측만**(계획 v6.34.1 넷째 커밋, 재검증 S-1 -- `SsCircuit.missing`에는 값 없는 저항과 커패시터가 함께 든다(`E/metrics/ss_circuit.py:46-49`); 노달 계 G는 용량을 쓰지 않고 측정 구성 창은 DC 양 -- DC/AC 분리 DEC-67·DEC-103): **판정 술어 하나**(여섯째 커밋, 재검증 3 N-C·gap N-5): `E/metrics/ss_circuit.py`의 공개 함수 `is_dc_conducting_passive(kind) -> bool` = `kind in DC_CONDUCTING_PASSIVE_KINDS`(authoring 정본 상수 `("resistor",)`, `E/authoring/dc_edges.py:11` -- 새 kind 목록 없음); 같은 파일의 `ss_circuit`(저항·용량 가르기 -- 옛 `kind == LOOP_CUT_KINDS[0]` 대체, 같은 결과)과 `ss_nodal`이 이 술어 하나를 부른다(같은 파일의 `ss_circuit`이 이름으로 참조하므로 독립 진입점이 아니어서 구조 규칙 A에 맞음); `ss_nodal`은 `SsCircuit.missing`의 소자 가운데 `device.kind`(READS)가 이 술어를 만족하는 것을 고르고, 하나라도 있으면 노달 계를 세우지 않고 **`graph.ss_nodal` 값 = `Undefined("ss_nodal", CODE_PASSIVE_MISSING, "definitional", (("elements", 결측 저항 이름 정렬 tuple),))`**(detail 키 = 기존 `metrics_ss` 꼴 `("elements", …)` -- `ss_metrics.py:403`, gap N-4)(기존 `E/metrics/mna_types.py` `Undefined` -- 새 타입·칸 없음; 계획 재검증 N-5 '정의 불능이 graph 필드에 남는 꼴'), `icm_config`는 그 값을 읽어 `config` = None·`IcmConfig.undefined` = `(Undefined("icm_config", CODE_PASSIVE_MISSING, "definitional", 같은 detail),)`·`node.dc_window_cfg` 쓰지 않음(4.7-5 M7 경로로 세 metric 정의 불능, 선언 제약은 기존 unmeasured 경로); 용량만 결측이면 DC 판정 자리(`ss_nodal` 노달 계·`icm_config` 측정 구성)는 선다; IT-2c 시점에는 그 점의 metric을 `metrics_aux`·`metrics_ss`가 결측 전체로 막아(`E/metrics/metrics_aux.py:164-166` -- ICMR 세 metric(DC 양)도 `metrics_aux`가 냄) 모두 정의 불능이고, **card IT-2d에서 해소한다**(B77 -- 계획 v6.34.2 사용자 결정 O-111·O-112, 4.7-5 793; IT-1 + IT-2는 master 병합이 한 번이라 master에는 잔존이 나타나지 않는다; 옛 문언 'B77 범위 밖·원래 취지와 다름(작음)'은 계획 v6.34.2로 대체). 그래서 세 자리 이전(`offset_analysis` 등)이 `Undefined` 노달 값을 받는 일은 없고, 받으면 같은 code로 정의 불능(fail-closed). **G-10 계수**(계획 재검증 N-3): 커널 `size_and_seal` 정확 계수(같은 θ parent 재평가 DC 열세 블록 = reuse 12·graft 1, 4.7-3c 757)는 DC 단계라 **불변**이고, 커널 밖 ss 단계 같은 θ 재평가에서는 graft 블록이 `ss_circuit` 하나만큼 늘어난다(블록마다 (computes, grafts, reuses) = (0, 1, 0) -- 기존 test `test_ss_evaluate.py:723-724` 꼴, 4.7-7 L11 (c)). WRITES `("graph", "ss_nodal")`, 값 `NodalSystem`(새 frozen dataclass, `E/metrics/aux_types.py`: `nodes`(정준 순서 tuple -- 크기 = `len(nodes)`, 따로 칸 없음), `fixed`(frozenset[int] = ac 접지 ∪ 입력 넷), `g`(읽기 전용 ndarray), **`g_bound`**(읽기 전용 ndarray, `g`와 같은 모양, 단위 S -- 계획 v6.34 N3.8 '판정 분해능의 정의 자리'의 **E = 조립·잔차 평가 반올림 상한 행렬**, 사용자 결정 O-107; 칸 이름 = design 결정), `factor`(`nodal_factor` 튜플 -- `E/metrics/_helpers_nodal.py:36`)). **E의 계산 자리 = G를 조립하는 같은 루프 하나**(계획 'E는 G 값만의 함수가 아니라 스탬프에서 나오므로 정의 함수가 스탬프를 다시 돌리면 둘째 생산자'): `_helpers_nodal.conductance_matrix(circuit, size, *, bound=False)`에 키워드 `bound`를 더한다 -- `bound=True`이면 같은 스탬프 루프에서 항목 (i, j)마다 S_ij = Σ_s |ĝ_s,ij|, k_ij = 스탬프 항 수, C_ij = Σ_s γ_{c_s}·|ĝ_s,ij|를 함께 쌓고 루프 뒤 **E_ij = γ_{max(k_ij−1, 0)}·S_ij + C_ij + γ_{n+1}·|Ĝ_ij|**(n = `size`, γ_m = m·u/(1 − m·u), u = `sys.float_info.epsilon` / 2 = 2⁻⁵³ -- 상수는 u 하나, 개수는 실제 조립에서 셈)를 만들어 `(g, g_bound)`를 돌려준다; `bound=False`(기본)는 지금처럼 `g`만(기존 소비자 `block_model`·`ff_gm_ratio` 값 불변 -- 그들은 E 생산자가 아니다, 계획 v6.34 검증 N-4). 조립 루프는 이 함수 하나이고 `bound=True` 호출 자리는 `ss_nodal` 하나다(E를 만드는 둘째 자리 0 -- 계획 완료 조건 (10)(c)); `_helpers_nodal.py`의 새 공개 함수를 만들지 않으므로 구조 규칙 A 보충 (3)(공개 함수마다 2파일 사용)에 걸리지 않는다. **c_s(스탬프 값 하나를 계산하는 산술 연산 수)의 한 자리 = 스탬프 함수**: `StampSet`(`E/metrics/records.py:214`)에 칸 `g_ops: tuple = ()`(`g`와 같은 길이, 항목마다 c_s)를 더하고 `mos_stamps`가 `g_entries`와 나란한 연산 수(`total = gm + gmb + gds` 항목 (d, s)·(s, s) = 2, 나머지 = 0 -- 부호 반전은 정확)를, `two_terminal_stamps`가 저항 항목 넷 = 1(`1.0 / element.ohm`)을 같은 거르기(값 0 항목 빼기)로 함께 낸다; `len(g_ops) != len(g)`인 `StampSet`은 생성 때 거부한다(`StampSet.__post_init__` `ValueError` -- fail-closed; `g`가 빈 용량 스탬프는 `g_ops` 빈 값 그대로 -- 둘째 커밋). 스탬프 식이 바뀌면 개수도 바뀌어야 하므로 스탬프 식 변경을 잡는 test를 둔다(4.7-7 L10 (j)). 1차 상한이다(O(u²) 항 제외; Higham 인용 절·쪽 **미확인** -- 계획 N3.8과 같음). 호출 자리·조건 = 위 `icm_config` '자리'(W5 -- `ss_evaluate.py:101` 뒤, `icm_config` 앞), 등록 = `SS_WRITES`(`E/sizing/s2_values.py:173-179`)에 `(SS_NODAL_WRITER, (("graph", "ss_nodal"),))`.
  - **READS 지문**(계획 v6.21 재검증 Info): 블록 입력 버전 = `fp_of((name, code_hash, projection.fp))`(`E/core/compute_block.py`), projection 지문은 읽은 필드의 `FieldValue.value_fp`(= `fp_of(value)`, 쓰기 때 한 번 -- `E/core/field_value.py`)에서 온다. ndarray·LU 튜플은 `fp_of` 정준 직렬화 규칙 밖(`E/core/fingerprint.py` `TypeError`)이므로 `NodalSystem.__canonical__` = `(nodes, tuple(sorted(fixed)), g.shape, g.dtype.str, g.tobytes(), g_bound.dtype.str, g_bound.tobytes())`(I1 -- 바이트 해석을 정하는 dtype 포함; **`g_bound`는 지문에 든다** -- 같은 G라도 E가 다를 수 있어 빠지면 graph reuse가 다른 E를 같은 버전으로 본다, 계획 v6.34 N3.8 'E의 자리'·검증 S-3, graph 규칙 2)로 둔다 -- 인수분해(`lu`·`piv`·`coupling`·`floating`)는 (g, fixed)와 writer 코드 해시의 결정적 함수라 지문에 넣지 않는다(같은 (g, fixed) → 같은 인수분해, 결정성 비트 동일 -- 계획 완료 조건 (6)). 그래서 READS 하는 블록(`icm_config`·`metrics_aux`)의 입력 버전은 G·E·고정 집합이 바뀔 때만 바뀐다. 불변성(W4): `g`·`g_bound`와 `factor`의 모든 ndarray(`unknown`·`lu`·`piv`·`coupling`)는 `writeable=False`, `floating`은 tuple -- test 단언 L10 (f)(배열마다 `flags.writeable is False`, 제자리 쓰기 시도가 `ValueError`; **red 먼저** -- `writeable=False` 설정을 뺀 변형에서 단언이 실제로 FAIL함을 확인한 뒤 통과를 본다). `require_immutable`(`E/core/immutability.py`)이 이 값을 받는지도 같은 test가 쓰기 경로로 잰다.
  - **고정 집합 하나의 전제**: 세 자리의 `fixed` = `view_system`(`E/metrics/_helpers_view.py`)의 ac 접지 ∪ 입력 넷 ∪ 구동 쌍 넷. 착수 실측: library 9회로·toy에서 구동 쌍 넷 ⊆ ac 접지 ∪ 입력 넷(그러면 `fixed`가 뷰와 무관 -- 필드 하나). 아니면 **멈추고 보고**(뷰별 인수분해 여럿은 계획이 정하지 않았다).
  - **세 자리 이전(IT-2 범위, 같은 변경 -- 둘째·셋째 생산자 제거)**: `E/metrics/offset_analysis.py`·`E/metrics/offset_systematic.py`·`E/metrics/block_residual.py`의 `nodal_factor(conductance_matrix(ss.circuit, size), fixed)`를 `NodalSystem.factor` 읽기로 바꾸고(세 함수는 `metrics_aux` 블록 안에서 불린다 -- import 자리 `E/metrics/metrics_aux.py`), `metrics_aux` READS에 `("graph", "ss_nodal")`를 더한다. 전회로 조립 `conductance_matrix(ss.circuit` 자리 = `ss_nodal` 하나(완료 조건 (10) (c) `git grep`). `block_model.py:91, :112`·`ff_gm_ratio.py`의 조립은 블록 국소 부분회로·FF 회로(다른 계)라 대상 밖(I2 사실 확정: `block_model.py`·`:112` 인자 = `sub`, `ff_gm_ratio.py` 인자 = `ff_circuit`).
  - 재사용 = graph reuse·S3 graft(블록 호출 규약 `E/core/compute_block.py`)뿐, graph 밖 캐시·메모·값 사본 없음(NFR-2·DEC-83).
- **v1.14.1 결과 표기 칸과 정의 불능 code 목록**(계획 v6.36 IT-2c 착수 조건 (vii)): (1) `config` ∈ {`"servo"`, `"as_is_single_input"`} 또는 None; 보고 'β = 1 기본' 표기 삭제 (2) 정의 불능 code(4.7-5 `Undefined`, category `definitional`, 갈래 순서 = 4.7-3b 계산 (1)): `passive_value_undeclared`(기존 -- `graph.ss_nodal` 결측)·`icm_inputs_unsupported`(v1.14.0 이름, 소비자 유지)·`view_required`(기존 어휘 -- 기본 포트 뷰를 만들 수 없음·하나로 정해지지 않음)·`icm_servo_pivot_unresolved`(v1.14.0 이름 -- 옛 `icm_inverting_port_unresolved` 대체); 계획 v6.36 정의 불능 셋(입력 셋 이상·기본 뷰 하나로 안 정해짐·만들 수 없음)과 servo 피벗·특이·결측 (3) P3 묶음 = 모든 입력 포트(F 성분 미선언 포트 포함 -- 4.7-3 3). **삭제**(계획 완료 조건 (8)(f) -- 비test 엔진 소스 정의·참조 0): v1.14.0까지 `"declared_feedback"`·`"follower_beta1"`, 칸 `inverting_port`·`tied_ports`·`transfer`, `icm_inverting_port_none`·`icm_inverting_port_ambiguous`·`icm_inverting_port_unresolved`, `icm_config_differential_output_structure`·`icm_config_differential_output_undeclared`·`icm_config_feedback_no_dc`·`icm_config_feedback_element_unsupported`·`icm_config_feedback_outputs_split`·`icm_config_feedback_cut`, `_dc_feedback_reaches`와 그 판정용 S1 READS 넷; v1.14.1 `icm_view_ambiguous`·`icm_excite_common_mode`(도달 0 -- 4.7-3b 계산 (1)), `input_window_f_component_undeclared`·cfg 상태 `"f_component_undeclared"`·상수 `INPUT_STATUS_F_COMPONENT_UNDECLARED`·`Circuit.writer_head`(생산자·소비자 0 -- 4.7-3 3), `SizingSpecDoc.icmr_view`·`DcInputs.icm_view`·extras 셋째 원소(4.7-3b READS); 절단 넷 순수 함수 분리·`_input_side` 대체는 card TN-1(계획 N6.26)로 -- 인용만. (옛 목록은 git 이력.)
- 옛 멈춤 S-1~S-3(O-58 결정 전 문언, servo O-115로 대상 소멸) = design 이력 H41-10.

**4.7-3c graph 스냅샷 파생 규칙(IT-2 범위 4, 사용자 결정 O-59 (2) -- 원래 취지와 다름, 승인 O-59 (2); 정의 정본 = 계획 N3.3 '스냅샷 파생 규칙'·N3.6 표 4행 -- 인용만)**:
- **사실(master `b9af2d6f`, 2026-10-20 재측정)**: `run_kernel`은 parent가 있으면 `snapshot = parent.snapshot`에서 출발한다(`E/sizing/kernel_run.py:72-75` -- 그 앞 조건이 parent의 `PLAN_WRITERS` 버전 = base임을 확인). `_CONTEXT_WRITERS` = `S1_WRITERS` writer ∪ `PLAN_WRITERS`(`E/search/search_context.py:44`; `PLAN_WRITERS` 정의 `E/sizing/kernel_context.py:49`). `lift_s1`(`E/sizing/s2_lift.py:17-24`)은 S1 writer가 모두 돌았는지 확인하고 `source.widen(S2_WRITERS)`로 권한표만 넓힌다 -- 필드의 writer 귀속을 바꾸지 않는다(`FieldValue.writer`, `E/core/field_value.py:16`). 봉인 4 `seal_versions(snapshot, calls)`(`E/sizing/seal_versions.py:14-27`)는 `calls`의 블록만 본다.
- **파생 자리 하나**(keep 집합의 정의 -- 계획 N3.3 '스냅샷 파생 규칙', 사용자 결정 O-61 P1: 옛 문언 '`_CONTEXT_WRITERS`'를 대체, O-59 (2) 뜻 그대로·취지 변경 아님): `run_kernel`의 parent 분기를 `snapshot = parent.snapshot.derive_child(keep)`로 바꾼다. `keep` = **base writer**(그 평가의 커널 컨텍스트 스냅샷 `ctx.base`에 블록 버전이 있는 writer -- 정본 = `ctx.base.block_versions`의 키, `E/core/graph_snapshot.py:39`·`:46`; 그 매핑에서 읽는다, 사본 목록 없음) ∪ **봉인 4가 받는 호출 목록의 블록 이름**(v1.12.8 정오, 사용자 결정 O-94 (2) -- 계획 N3.3 '그 평가가 부르는 계산 블록'·N3.6 표 4행 '그 평가의 호출 블록'과 같은 집합; 옛 문언 '커널 호출 블록 이름(`steps`·`later`)'은 봉인 항목 블록을 빠뜨려 계획보다 좁았다): 커널 블록(`steps`·`later` 목록 -- `kernel_run.py:83-97`) ∪ 봉인 항목 블록 여덟(`dc_tolerances`·`dc_seal_node_conflict`·`dc_seal_vgs_match`·`dc_seal_kcl`·`dc_seal_bulk_reverse`·`dc_seal_saturation`·`dc_seal_kvl_branch`·`dc_seal_conduction` -- `E/sizing/seal.py` `seal_dc`의 항목 목록). 봉인 항목 블록의 구성원·순서는 `E/sizing/seal.py`의 모듈 상수 하나(블록 객체 tuple)가 정본이고 `seal_dc`의 호출 순서와 `run_kernel`의 keep이 모두 그 상수를 읽는다(이름 사본 목록 없음; extras는 `seal_dc` 안에서 블록 객체를 키로 하는 지역 매핑으로 찾는다 -- 순서는 상수, 키가 빠지거나 상수 밖 키가 있으면 예외(검증 R-1: 길이만 대조하면 순서 바뀜을 못 잡음); 실행 사이·평가 사이에 남지 않는 인자 구조라 cache가 아니다). keep 집합은 아래 집합 함수 `writers_in_scope`로 읽는다(계획 v6.32 N3.3 '집합의 정본 자리 = 함수 하나'). **실패 평가의 부분 스냅샷 파생**(card IT-2e, 정의 정본 = 계획 v6.32 N3.3 '실패 평가의 부분 스냅샷'·N3.6 표 4행·U-93, 사용자 결정 O-96, 근거 `wt/_drafts/evidence/2026-10-22/b69_partial_snapshot_analysis.md`; v1.12.8의 '원래 취지와 다름(작음)·백로그 B69'는 **계획 v6.32 N3.3·O-96으로 해소** -- 성격은 U-93 '그때까지 계산한'·N3.3 "'없음'이 '낡은 값'보다 안전"의 취지 회복): (사실, `integ-it12` `56080584` 재측정 -- v1.12.8 문언 'k+1 뒤 봉인 항목'은 좁았다) 블록 호출은 `block_version(이름) == 입력 버전`이면 reuse하므로(`E/core/compute_block.py:143`) 블록 k에서 실패했다는 것은 k의 입력 버전이 parent와 다르다는 뜻이고, parent에서 파생한 스냅샷의 부분 스냅샷(`_call_block` `E/sizing/kernel_run.py:56-62`, `seal_dc` 봉인 항목 `E/sizing/seal.py:66-70`)에는 **k..끝(실패 블록 자신과 그 뒤 커널 블록·봉인 항목 블록 -- 커널 블록에서 실패한 경우 포함)**의 parent 필드가 남는다; 봉인 보고서 블록 실패(`seal.py:74-78`)·봉인 위반(`:87`)은 커널 블록과 봉인 항목 블록을 모두 부른 뒤라 낡은 필드가 없고, ss 단계(`E/metrics/ss_evaluate.py:113-115`)는 시작 스냅샷 = 봉인 스냅샷이고 ss writer가 파생 keep 밖이라 이미 규칙을 충족한다(code 변경 없음 -- 계획 N3.3). **규칙**: 부분 스냅샷 = 실패 시점 스냅샷을 **base writer ∪ 그 평가에서 실패 전에 부른 블록**(reuse·graft·compute 어느 쪽이든 부른 블록; 계획 문언 '실패 전에 성공한 블록'과 같은 집합 -- 첫 실패에서 예외로 멈추므로 앞에서 부른 블록은 모두 성공한 블록)으로 줄인 것(`derive_child` -- 구조 공유, 새 필드·cache·값 사본·writer·블록 호출 없음, reuse·graft·compute 계수 변화 0); 실패한 블록 자신과 그 뒤 블록의 필드는 넣지 않는다; 봉인 위반에서는 `dc_seal_report`도 이미 부른 블록이라 남는다(방금 쓴 보고서를 지우지 않는다). 그래서 부분 스냅샷의 writer 집합과 지문은 (평가 키, 실패 지점)만으로 정해지고 parent와 무관하다; parent 없는 평가는 스냅샷 writer가 이미 이 집합 안이라 바뀌지 않는다(지문 불변). **집합 함수 하나**(이름·자리 = design, 계획 N3.3): `writers_in_scope(base, blocks) -> frozenset` -- 자리 `E/sizing/seal_versions.py`(봉인 4 coverage 술어가 있는 모듈; 모듈 지도 sizing 층 1이라 `seal.py`(층 3)·`kernel_run.py`(층 4)가 앞 층으로 import -- 순환·같은 층 import 없음; `seal_versions`가 부르므로 구조 규칙 A의 독립 진입점이 아니어서 모듈 지도 kind·진입점 `seal_versions` 그대로, 그 항목 책임 문장·계획 ID에 N3.3 부분 스냅샷 집합을 더한다). 서명: `base` = 커널 컨텍스트 스냅샷 `ctx.base`(base writer 정본 = 그 `block_versions` 키; None이면 `TypeError` -- `seal_versions`와 같은 형태), `blocks` = 블록 객체(`ComputeBlock`) iterable(이름은 함수 안에서 `.name`으로 읽는다 -- 부르는 자리는 블록 이름 집합을 만들지 않는다), 반환 = base writer ∪ {블록 이름}의 `frozenset`. 'base writer ∪ 블록 이름' 합집합식과 coverage 차집합 꼴의 정의 자리는 이 함수 하나, 그 밖 재구현 0(L11 (e) AST 검사). **AST 검사가 세는 것**(계획 N3.3 측정 정의 안의 구현 세부 -- 정의를 넓히지 않는다): 세는 연산 = 합집합·차집합 -- 이항 `|`·`-`, 누적 대입 `|=`·`-=`, set 메서드 `.union`·`.difference`·`.update`·`.difference_update`; 교집합(`&`·`.intersection`)은 서로소 단언 꼴이라 세지 않는다; 한 식 트리(위 연산의 사슬)의 피연산자에 base writer 집합(출처 = 스냅샷 `block_versions` -- 함수 안 대입을 거쳐도, `set(x)`·`frozenset(x)`·`tuple(x)`처럼 호출로 감싼 피연산자 안까지 들어가 추적; 재검증 N-R1)과 블록 이름 집합이 **함께** 나타날 때만 센다; '블록 이름 집합' = 블록 객체의 `.name`으로 만든 집합(comprehension 등), 문자열 상수의 set·frozenset·tuple(예: `{"dc_currents", …}` -- 옛 `_CONTEXT_WRITERS` 같은 이름 사본 꼴), 함수 매개변수로 받은 이름 집합, 또는 그것들을 담은 변수(재검증 S-R1 -- 계획 '블록 이름 집합'은 만드는 방식을 한정하지 않는다; 교집합 제외는 그대로). **검사기 양성 대조**(N-R1): 변경 전 head(IT-2a 반영 `integ-it12` `56080584`)에서 세면 인라인 식 두 곳(`kernel_run.py:86`·`seal_versions.py:36`) = 2가 나와야 한다(0이면 검사기 결함 -- red). 레지스트리 확인: `docs/03-analysis/gain-budget-gmid-sizing.function-registry.md` §2에 같은 개념 행 없음, 엔진 `def ` grep에 같은 집합을 내는 함수 없음(지금은 `kernel_run.py:86-87` keep식과 `seal_versions.py:32-36` coverage식 두 곳의 인라인 식) -- 새 함수를 두고 두 인라인 식을 같은 변경에서 지우며 레지스트리 §2에 행을 더한다(code 커밋 몫). **부르는 자리 셋**: (i) `run_kernel` 파생 keep -- `parent.snapshot.derive_child(writers_in_scope(base, 커널 블록(steps·later_blocks) + SEAL_ITEM_BLOCKS))`(옛 `set(base_writers) | {…} | …` 대체) (ii) 봉인 4 coverage -- 위반 writer = 스냅샷 필드 writer − `writers_in_scope(base, calls의 블록)`(차집합 꼴; 옛 `used - base_writers - called` 대체) (iii) 실패 부착 -- 줄인 스냅샷 `snapshot.derive_child(writers_in_scope(base, 앞 블록))`을 `attach_partial`에 넘긴다: `_call_block`(커널 블록 실패 -- 앞 블록 = 그 평가의 커널 호출 순서에서 실패 블록 앞부분), `seal_dc` 봉인 항목 블록 실패(앞 블록 = 그 시점 `calls`의 블록 = 커널 블록 ∪ 이미 성공한 봉인 항목; 실패 블록은 성공 뒤에만 `calls`에 더해지므로 빠진다 -- `seal.py:71`), 봉인 보고서 블록 실패(`calls`의 블록 전부 -- 커널 블록 ∪ `SEAL_ITEM_BLOCKS`), 봉인 위반(`calls`의 블록 + `dc_seal_report`). **앞 블록을 얻는 방법**: `_call_block`에 인자 `before`(그 평가에서 이미 부른 블록 객체 tuple)를 더하고 `run_kernel`의 두 루프가 호출 목록 앞부분 slice로 넘긴다(첫 루프 = `steps[:i]`의 블록, 둘째 루프 = `steps`의 블록 + `later_blocks[:j]` -- 루프 인덱스, 새 누적 변수·저장 없음); `seal_dc`는 이미 있는 지역 `calls`(봉인 4 인자로 쌓는 호출 목록)를 쓴다. 서로소 단언(base writer ∩ 호출 블록)과 parent 일치 검사(`kernel_run.py:73-74`)는 이 함수 밖이다(base writer를 따로 읽는 것은 합집합·차집합이 아니라 측정 대상 아님 -- 계획 N3.3). **재연 예외**(같은 실행 실패 색인 재연 -- 블록 호출의 `from_record`, `E/core/compute_block.py:150-156`)도 같은 부착 자리에서 줄여서 붙는다(재연 예외는 `partial` None으로 시작하고 `attach_partial` 첫 부착 유지 규칙 그대로 -- 계산했을 때와 같은 앞 블록·같은 부분 스냅샷). `attach_partial`(core)은 바꾸지 않는다(base를 모른다). **같은 변경에서 고치는 문서 자리**(바뀐 뒤 parent 경로에서 거짓이 되는 부분 스냅샷 문언, `56080584` 재확인): `E/search/CONTRACT.md:458`(`EvalResult.partial` 문언 'DC 블록 실패 = 그 블록에 들어간 스냅샷'), `E/search/search_values.py:163-164`(`EvalResult.partial` docstring), `E/sizing/CONTRACT.md:117-119`(`run_kernel`·`seal_dc` 부분 스냅샷 부착 문단), `E/sizing/kernel_run.py:10-11`(머리 설명), `E/sizing/seal.py:69` 주석 -- '줄인 스냅샷'으로 고친다. 착수 사실(부착 자리, 커널 블록 구성 = 평가 커널 steps·later 구성원, 집합식 자리, 줄 번호)은 IT-2d 병합 head에서 다시 잰다(계획 N6.6 범위 5 -- 이 항목의 줄 번호는 `56080584` 값). 범위 밖(백로그, 계획 N3.3): 봉인 아닌 점의 `passive_values`·`metrics_dc` 후보 실패 처리(`E/search/kernel.py:142-147`). **`dc_seal_report`는 keep에 넣지 않는다** -- 봉인 4·5의 결과를 입력으로 봉인 4 뒤에 불리므로 봉인 4의 호출 목록에 들 수 없고, parent의 보고서 필드를 남기면 봉인 4 coverage가 그 필드를 `foreign_writers`로 거부한다(남기려면 coverage가 아직 부르지 않은 블록의 낡은 필드를 허용해야 해서 검사가 약해진다). 그래서 그 필드는 child에서 지워지고 다시 불릴 때 같은 입력 버전이면 S3 graft로 돌아온다(재계산 0) -- 계획 문언 '부르는 계산 블록'을 '봉인 4가 받는 호출 목록'으로 읽은 것이고 더 지우는 쪽(fail-closed)이다(**원래 취지와 다름(작음), 승인 O-94 (2)**). 근거(계획 같은 문단): 옛 `_CONTEXT_WRITERS`(`S1_WRITERS` ∪ `PLAN_WRITERS`)에는 `ctx.base`가 담는 S1v·S0 탐색·metrics S0 writer가 없어 parent 없는 평가가 봉인 4에서 거부되고 child가 그 필드를 잃는다. `ctx.base`는 평가 θ를 읽지 않는 블록만으로 평가 전에 만들어지므로 그 필드는 모든 평가에 유효하다(전제 -- 아래 봉인 4 서로소 단언이 지킨다). 새 메서드 `GraphSnapshot.derive_child(keep_writers)`(`E/core/graph_snapshot.py`): writer ∈ `keep_writers`인 필드와 그 writer의 `block_version`만 남기고 나머지 writer의 필드·`block_version`을 지운 새 스냅샷(권한표·구조 공유 그대로; eager, '없음'이 '낡은 값'보다 안전 -- fail-closed). 봉인 뒤 블록(`ss_linearize`·`ss_circuit`·`ss_nodal`·`icm_config`·metric 블록)의 필드는 child에서 지워지고(v1.13.0: 커널 밖 writer `dc_window_refine`·`metrics_icm_front`는 없다 -- 4.7-4), 그 블록이 다시 불리면 같은 입력 버전의 값이 S3 색인 graft로 돌아온다(재계산 0, 새 캐시 없음 -- 계획 N3.3).
- **`_CONTEXT_WRITERS`는 옮기지 않는다**(사용자 결정 O-61 P1 -- 옛 초안의 '`CONTEXT_WRITERS` 정의 이동' 항목 삭제): `E/search/search_context.py:44`의 `_CONTEXT_WRITERS`는 평가 키 지문 `context_fp` 전용이고 이 규칙의 정본이 아니다(계획 N3.3). `run_kernel`은 search를 import하지 않는다 -- keep은 `ctx.base`(이미 `run_kernel`의 인자 `ctx`에 있음)에서 읽으므로 층 방향 문제가 없다.
- **parent 일치 검사 넓힘**(계획 N3.3·N6.6 범위 4): `kernel_run.py`의 검사 `any(parent.snapshot.block_version(w) != base.block_version(w) for w in PLAN_WRITERS)`를 **base writer 전부**(`base.block_versions`의 키)로 넓힌다 -- 같은 검사의 일반형, 어긋나면 지금처럼 `ValueError`(fail-closed). 그래서 `derive_child`가 남긴 base writer 필드는 늘 `ctx.base`와 같은 입력 버전이다.
- **봉인 4 단언 둘**(계획 N3.6 표 4행): `seal_versions(snapshot, calls, base)`(셋째 인자 = `ctx.base` 스냅샷 -- base writer는 그 `block_versions`에서 읽는다; 호출 자리 `seal_dc`는 `run_kernel`에서 `ctx.base`를 넘겨받는다 -- `seal_dc`의 `base`는 기본값 없는 필수 키워드(사용자 결정 O-94 (3): 기본값 None으로 (3)(4)를 건너뛰는 길은 봉인 4 우회 = 기준 약화; 선례 `donors`·`counters` 필수 키워드 B-T16; `seal_versions`도 base None을 받으면 건너뛰지 않고 `TypeError`로 거부하며(SEAL_FAIL이 아니라 호출 오류 -- 필수 키워드 누락과 같은 형태) `if base is not None` 건너뛰기 분기는 삭제, 계획 v6.31 N3.6 4행)) 끝에 (3) **coverage** '스냅샷의 모든 필드의 `FieldValue.writer` ∈ base writer ∪ {`calls`의 블록 이름}'(v1.12.9: 그 집합은 `writers_in_scope(base, calls의 블록)`에서 읽고 위반 writer = 필드 writer − 그 집합 -- 위 '실패 평가의 부분 스냅샷 파생', 계획 v6.32 N3.6 4행) -- 위반 writer는 detail `("foreign_writers", 정렬 tuple)` (4) **서로소** 'base writer ∩ {`calls`의 블록 이름} = ∅' -- 위반 이름은 detail `("base_call_overlap", 정렬 tuple)`을 더한다. 어느 하나라도 위반이면 status `SEAL_FAIL`(fail-closed). 기존 (1)(2) 검사는 그대로.
- **착수 실측**(계획 N6.6 범위 4): (i) search tests 가운데 ss 블록 `reuse` 계수를 단언하는 test(`git grep`) -- 기대가 `graft`로 바뀌므로 변화표에 적고 test 작성자가 새 기대로 쓴다; 같은 θ parent 재평가의 DC 열세 블록 outcome은 커널 4·봉인 항목 8 = `reuse`, `dc_seal_report` 1 = `graft`(옛 기대 reuse 13 -- `E/tests/sizing/test_size_and_seal.py` `test_same_theta_with_parent_zero_compute`·`test_passive_theta_only_change_zero_dc_compute` -- 함수 둘, parametrize 포함 항목 넷, computes 0 유지; v1.12.8, 사용자 결정 O-94 (2)) (ii) S3 색인에서 ss 블록 등록이 빠지는 경로(실패 경로 등) -- 있으면 그 경로에서 graft가 아니라 compute가 되므로 변화표에 적는다 (iii) parent 없는 평가 스냅샷(= `ctx.base`)의 writer 목록과 그 writer 모두가 평가 θ를 읽지 않음(탐색 경로 `E/search/search_context.py` `base = dc_ctx.base.widen(S0_WRITERS)` 뒤 S0 블록 포함 -- 계획 N6.6 범위 4; θ를 읽는 writer가 있으면 서로소 전제가 깨지므로 **멈추고 보고**) (iv) `lift_s1`(호출 `E/sizing/kernel_context.py`, 정의 `E/sizing/s2_lift.py`)이 writer 귀속을 바꾸지 않음(확인됨, 위 사실).

**4.7-4 공용 helper `Circuit`(card IT-2c, 사용자 결정 O-110 U-101 (가′)) -- 다듬은 창 블록 `dc_window_refine` 삭제**: 다듬은 창 블록 `dc_window_refine`(`E/sizing/window_refine.py`, 진입점 `refine_input_windows`, 상수 `DC_WINDOW_REFINE_WRITER`, `DC_WRITES` 행, 모듈 지도 행, test `test_window_refine.py`)은 **만들지 않는다**(계획 v6.34 N3.8 '측정 구성 창 = 선형 감도 끝 하나', 사용자 결정 O-109 C1 '선형 끝만, SPICE 확정' -- **원래 취지와 다름, 승인 O-109**(O-21·O-25 (3)·O-33 (3)·O-49 P1·P4~P6·O-61 P6·O-64 (2)); U-100 해소). 이 절에 남는 것은 측정 구성 블록(4.7-3b)이 행 셋을 쓰게 하는 접근 경로다(아래 760).
- **옮기는 것 = `_Circuit`의 행 부분 -- IT-2c**(사용자 결정 O-110 U-101 '(가′) IT-2c에서 Circuit 행 부분을 옮겨 공개 (권고)'; 계획 v6.34 N6.6 IT-2c 착수 조건 (vi)·N7.2 U-101; 근거 `wt/_drafts/evidence/2026-10-22/it2c_circuit_access.md` §2·§3·점검표, `it2c_spice_frame_v2.md` §4 3): 측정 구성 블록 `icm_config`(metrics 패키지)는 모든 구성에서 행 셋 `region_rows`와 끝 식 `saturation_window`(`slope=` 갈래)를 부르고(4.7-3b (4)), 포트 창에 `port_window`를 쓴다(v1.14.1: F 성분 판정 없음 -- `writer_head`는 소비자 0이라 옮기지 않고 IT-2c에서 삭제, 4.7-3 3) -- 그래서 IT-2c가 그 부분을 같은 패키지의 공용 helper 모듈 **`E/sizing/_helpers_dc_solve.py`**(이름은 계획 U-101 행 그대로; test `E/tests/sizing/test__helpers_dc_solve.py`, 규칙 H)의 공개 클래스 **`Circuit`**으로 옮기고, `sizing/__init__.py`의 `__all__`에 **`"Circuit"`·`"saturation_window"`·`"INPUT_STATUS_MEASURED"`·`"INPUT_STATUS_UNMEASURED"`·`"SS_CIRCUIT_WRITER"`·`"SS_NODAL_WRITER"`·`"ICM_CONFIG_WRITER"`**를 더한다(writer 상수 셋은 `E/sizing/s2_values.py`에 정의하고 metrics 블록이 `@compute_block`에 쓴다 -- 선례 `metrics_aux.py:24` `from gmid_engine.sizing import METRICS_AUX_WRITER`; 여섯째 커밋, 재검증 3 S-A)(규칙 C -- metrics(5) → sizing(4) 아래층 방향, 공개 이름만; 상태 상수 둘(`INPUT_STATUS_F_COMPONENT_UNDECLARED`는 생산자 0이라 상수째 삭제, `__all__` 일곱 이름)은 `icm_config`가 cfg `Window`에 쓰고 IT-2d `metrics_aux`가 code로 옮길 때 읽는다 -- 정본 상수 하나, 문자열 사본 금지; 둘째 커밋). **옮기는 범위와 계획의 관계**(여섯째 커밋, gap N-2): 계획 N6.6 IT-2c 착수 조건 (vi)은 '공용 helper로 옮길 대상은 행 셋을 세우는 데 필요한 부분(`region_rows`와 그 도우미)뿐 … 옮길 범위의 확정은 U-101 결정 뒤 design'이라 적었고, 이 design은 거기에 `port_window`(포트 창 규칙)·`canonical_writers`·`kind_sign`을 더한다 -- 계획이 design에 위임한 범위 안의 확정이라 **원래 취지와 다름 아님**. **`Circuit`의 범위**(봉인점 해 위 행 부분 -- 노드 풀이 기계 없음): 생성자 **`Circuit(projection, *, lut, linear)`**, 칸 = 투영 열(`node.dc_writer`·`node.dc_rail_v`·`node.port_direction`·`device.pins`·`device.kind`·`device.bulk`·`device.dc_L`·`device.dc_colour`·`device.dc_coord`)과 `lut`·`linear`·레일 lo/hi·입력 포트 집합, 메서드 = `mos_point`·`vds_vsb`·`region_rows`·`port_window`·`canonical_writers`와 정적 메서드 `kind_sign`(as-built 모듈 함수 `_kind_sign` -- 행 부호와 노드 풀이 부분이 함께 쓰므로 공개 정적 메서드로 옮겨 규칙 B(다른 파일의 `_` 이름 import 금지)를 지킨다). **`block_columns.py`에 남는 것**: 노드 풀이 부분은 `Circuit`을 상속한 비공개 클래스 `_Circuit(Circuit)`(생성자 `_Circuit(projection, *, theta_items, fixed_values, resistor_values, lut, linear)` -- θ·고정값·저항·`override`·`order_terms`·`tol_cells`·`kvl_window`·`window`·`input_windows`·`input_roots`·`start`·`writer_grad`·`newton_system`·`solve_self`·`update`·`drop`·`tolerance` 등)로 남고, 그것만 쓰는 비공개 도우미(`_vgs_of_coordinate`·`_vds_floor`·`_inward`)도 남는다. **이름 계약**(it2c_circuit_access.md 공백 3건 중 extras -- 옛 `_Circuit.__init__`의 `theta_items, fixed_values, resistor_values, lut, *rest = projection.extras`·`rest[0]` = 선형 선언은 블록마다 extras 꼴이 다르면 잘못 읽힌다): `Circuit`·`_Circuit`은 `projection.extras`를 읽지 않고 키워드 전용 인자로 받는다(기본값 없음); extras를 푸는 것은 각 블록의 몫이다 -- `dc_columns`는 자기 호출 계약(`kernel_run.py:97-98` -- 선형 선언이 비면 넷째 뒤 원소 없음) 그대로 풀어 `linear=frozenset(rest[0]) if rest else frozenset()`로 넘기고, `icm_config`는 자기 extras 셋(4.7-3b READS 문단)을 풀어 `Circuit(projection, lut=…, linear=…)`로 넘긴다. **구조 규칙 근거**(둘째 커밋): 규칙 A 보충 (3)의 검사기는 `_` 모듈의 공개 **함수**만 센다(`structure_checks.py:300-315` -- 클래스 미계수). 이 design은 **그 검사기 빈틈에 기대지 않는다** -- 근거는 규칙 A의 취지('공용 helper = 실사용자 둘 이상')를 실제로 충족한다는 사실이다: 실사용자 둘 = `block_columns._Circuit`(하위 클래스, 같은 패키지)·metrics `icm_config`(`sizing.__all__` 경유, 패키지 밖). 규칙 문언('같은 하위 패키지 2파일')과 다른 점은 이 두 사용자 구성에서 온다. **확인 기록**(셋째 커밋, 오케스트레이터 판단 (가)): 검사기는 `sizing/__init__.py` 재수출도 사용 파일로 세지만 그것은 실사용이 아니다; 취지 충족 근거는 실사용자 둘(`block_columns`·`icm_config`)이다; 검사기를 클래스·실사용 기준으로 고치는 일은 백로그 B76. **모듈 지도 층**: `_helpers_dc_solve`는 `_helpers_lut`·`scc_order`(층 1)를 import하므로 층 2이고, 그것을 import하는 `block_columns`는 지금 층 2에서 **층 3으로 올린다**('같은 층 import 금지' -- `_module_map.py` 머리; 이 층 규칙은 지금 구조 test가 강제하지 않음, 검증 확인). 규칙 B: `block_columns`는 `from ._helpers_dc_solve import Circuit`(`_helpers_*` 모듈 import 허용), `icm_config`는 `from gmid_engine.sizing import Circuit, saturation_window`. 모듈 지도(`E/_module_map.py`) helper 층 행과 `sizing/input_window.py` 행 서명 갱신도 IT-2c. '코드 이동이고 식 불변'은 옮기는 메서드에만 해당한다(`region_rows`(행 꼴만 일반 1차 행으로 -- 4.7-3a 1, v1.14.1)·`port_window`의 식 불변; 생성자 서명만 이름 계약으로 바뀜). **`_Circuit` test 직접 참조 0**(head grep -- 같은 근거 §2 (가) 표).
- **옮기지 않는 것 -- `solve`·`FAILURES` 이동 없음**(v1.13.0 재판단; 옛 'IT-2d가 `Circuit`·`solve`·`FAILURES`를 옮긴다'를 대체): 옛 이동 근거('`dc_columns`·`dc_window_refine` 둘이 노드 풀이 기계를 쓴다')는 다듬은 창 블록이 없어(C1) 성립하지 않는다 -- `_solve`·`_FAILURES`·`writer_grad`(θ 감도)·`_solve_input_window`·`_interior_solution`·`_dyadic_ys`·`_measure`·`_tolerance`는 커널(`dc_columns`) 하나만 쓰므로 `block_columns.py`에 비공개로 남는다(사용자 하나인 `_` 모듈 공개 함수는 규칙 A 보충 (3) 위반; `icm_config`는 KCL 감도라 θ 연립·노드 풀이를 쓰지 않는다 -- 계획 v6.34 U-101 행 'θ 감도(`writer_grad`)와 노드 풀이 기계(`solve`·`FAILURES`)는 `icm_config`·다른 블록이 나눠 쓸 일이 없어 이동 대상 밖'). 그래서 IT-2d에는 helper 이동이 없다(계획 재검증 N-7). 끝 풀이 함수는 어느 층에도 없다: as-built `_refine_ends`(+`_root_windows`)는 IT-2b에서 이미 지웠고(`6afe4758` 확인), 대체 함수도 만들지 않는다(O-109 C1). `_Measured.slope`·`_Measured.values`와 `declared_inputs`는 D1로 쓸 곳이 없어 IT-2c에서 지운다(4.7-3 2·3).
- 모듈 수준 이름(장애 주입 지점): `window_refine.py` 주입 지점은 없다(파일 없음 -- v1.13.0). 커널 `k_max` import·주입 지점은 커널 되풀이와 함께 범위 3a에서 삭제(4.7-V 2행).
1. **(삭제 -- v1.13.0, O-109 C1)** 다듬은 창의 출발 끝(출발 창 = `node.dc_window_cfg`, O-61 P6)은 대상이 없다 -- 출발 창이 곧 정본 칸이다(4.7-3b '정본 칸').
2. **(삭제 -- v1.13.0, O-109 C1)** 끝 풀이(창 끝 x 고정 Newton)·'쓰지 않는 포트' 갈래·(ii) 끝 포화 확인(O-49 P6)은 대상이 없다 -- 끝 풀이 함수는 어느 층에도 정의·호출 0(계획 완료 조건 (0)).
3. **(삭제 -- v1.13.0, O-109 C1)** 끝 풀이 실패 사유 `window_end_solve_failed`·`window_end_k_max_exhausted`·`window_end_saturation_unconfirmed`와 metric code `input_window_end_missing`은 만들지 않는다. 측정 구성 창의 fail-closed는 4.7-3b '정본 칸'(선형 감도 풀이가 정의되지 않으면 `"unmeasured"`, 대체값 없음).
4. 포트 창은 θ `_sensitivities` 기울기 외삽·넷별 뿌리 경로 κ로 내지 않는다 -- 측정 구성 포트 창은 KCL 감도 하나(4.7-3b), 재계산 0(계획 완료 조건 (4)).
5. **(삭제 -- v1.13.0, O-109 C1) 호출 자리와 배선**: 다듬은 창 실행 배선(`refine_front_windows`, 수락 반복 `accept`·`find_front` 배선, FD 열·커널 평가 제외 조건, perf 칸 `window_end_solves`, 층 0 front 후보 점 호출 자리 -- card LA-1 범위 12)은 만들지 않는다 -- `E/search/slsqp_outer.py`·`E/search/find_front.py` 변경 없음. front·보고 값(층 0 front 후보 점 포함) = 그 점 커널 평가 스냅샷의 `metrics_aux` 입력 CM 세 metric(= `node.dc_window_cfg`에서 낸 값, 추가 호출 0); 운반자 = `_point_record`의 `snapshot_ref`·`snapshot_fp`(EO-1의 oracle 입력 생산자·U16 보고서가 읽는 자리; run 레코드 형식 불변). 측정 구성 블록·`ss_nodal`의 재사용은 graph reuse·S3 graft뿐(4.7-3b, NFR-2·DEC-83 -- 새 캐시 없음); parent → child 파생 규칙(4.7-3c)은 그대로이고 봉인 뒤 블록 필드는 child에서 지워진다. 새 블록 `ss_nodal`·`icm_config`는 블록 계수(`perf.blocks`·`block_computes`, `RunCounters`)에 행이 생긴다(WP-10 비용 보고). 옛 줄별 문언 = design 이력 H41-12.
6. **(삭제 -- v1.13.0)** 다듬은 창 블록 READS 규칙(O-49 P1 `node.dc_v` 제외)은 대상이 없다(계획 v6.34 완료 조건 (7) -- 옛 (d) 없음). 측정 구성 블록은 반대로 `node.dc_v`를 READS로 읽는다(봉인점 행 셋 -- 4.7-3b READS, U-101 (가′)); `node.dc_window`를 읽지 않는 것은 측정 구성 블록의 단언이다(계획 완료 조건 (12)(d)).

**4.7-5 metric 읽기(IT-2 범위 2·3, IT-Q2 (다) 정의, X-IT8 -- 판정이 (나)든 (다)든 계산 경로 하나)**:
- **정의 함수 하나**: `icm_window_metrics(config, ports, input_dc) -> IcmWindow`(새 순수 함수, 파일 `E/metrics/icm_window.py`, test `E/tests/metrics/test_icm_window.py`; v1.14.0 서명 -- 계획 v6.35 N3.8 'ICMR 좌표 -- 정의 자리 하나'(U-106): 세 metric은 `config`(`IcmConfig`)의 V_cm 칸에서 내고, `ports`는 정의 불능 판정·보고 열에만 쓴다).
  - `config` = 같은 스냅샷의 `graph.icm_config` 값(`metrics_aux` READS -- 칸 참조, 사본 없음). `ports` = **입력 포트 모두**(계획 IT-2c 착수 조건 (vii) -- `tied_ports` 거르기 삭제, servo는 입력 포트를 출력에 묶지 않음; 옛 '측정 구성이 묶지 않은 입력 포트'(O-67 (2) DV-18)는 U-106으로 대체)의 `IcmPort(net, v, lo, hi, tol_v, missing)` tuple, 순서 = (구조 색 `node.dc_colour`, 이름). `IcmPort`(새 frozen dataclass, `E/metrics/aux_types.py`): `net: str`, `v: float`(그 포트 봉인점 전압 `node.dc_v`), `lo`·`hi`: float 또는 None(그 포트의 `node.dc_window_cfg` 끝 -- **보고 열 전용**, metric 산술에 쓰지 않음 -- 계획 완료 조건 (8)(g) AST), `tol_v`: float 또는 None, `missing`: `()` 또는 `((code, detail),)`(code = `input_window_unmeasured`(`input_window_f_component_undeclared` 삭제, O-118 3번); S-4 갈래 card가 두기로 하면 `input_window_operating_point_mismatch`(4.7-3a 3 -- (S4-나)의 IT-2에는 없음), detail = (키, 값) 정렬 tuple). 창 필드에서 만드는 규칙(`node.dc_window_cfg` 하나 -- 모든 구성, 커널·front·보고 같음): 항목 없음 또는 `"unmeasured"` → `input_window_unmeasured`. **포트별 margin과 포트 창 교집합은 계산하지 않는다**(계획 N3.8 'ICMR 좌표' -- servo에서 두 포트가 함께 움직여 V_cm 기준 값과 O(ε) 달라 같은 이름에 두 정의가 생김, graph 규칙 3).
  - `input_dc` = `"declared"` | `"pending"`. 예시: `config.vcm0` = 0.90, `config.vcm_lo` = 0.34, `config.vcm_hi` = 1.19, 두 포트 `missing` = () → `icm_margin_v` = min(0.90 − 0.34, 1.19 − 0.90) = 0.29, `icmr_v` = 1.19 − 0.34 = 0.85, `required_input_cm_v` = (0.90, 0.34, 1.19)(`"pending"`).
  - `icm_margin_v` = min(`vcm0` − `vcm_lo`, `vcm_hi` − `vcm0`)(계획 N3.8 'ICMR 좌표' -- V_cm0 = 봉인점 입력 포트 전압의 평균; 옛 포트별 margin 최솟값(O-67 (2) DV-18) 대체, U-106).
  - `required_input_cm_v` = 입력 DC 미선언이면 (`vcm0`, `vcm_lo`, `vcm_hi`), 선언이면 None -- 형식 (값, lo, hi) 불변(옛 '최솟값을 낸 포트의 것'(IT-Q2 (다)) 대체, U-106).
  - `icmr_v` = `vcm_hi` − `vcm_lo`(V_cm 끝 상태 차 -- 옛 as-built '포트 창 교집합 폭' 대체, U-106; 4.7-3b 계산 (6)의 min·max 정렬이라 음수 폭 없음). `window` = (`vcm_lo`, `vcm_hi`), `v_icm` = `vcm0`.
  - 분해능(새 상수 없음, 창 필드의 `tol_v`에서 -- 계획 N6.6 범위 2 '창 margin tol', servo 피벗 판정 분해능과 다른 양): cfg 항목의 `tol_v`는 모든 입력 포트가 같은 값(봉인점 `device.dc_tol_v` 최솟값 -- 4.7-2)이라 `margin_resolution` = 그 `tol_v`(`ports` 첫 항목에서 읽음), `icmr_resolution` = 아래 끝 `tol_v` + 위 끝 `tol_v` = 2·`tol_v`(as-built '구속 하한 누적 + 구속 상한 누적'과 같은 꼴). `tol_v`가 None이면 None.
  - **정의 불능**(N3.14, 세 metric 모두 값 None): (v1.14.1: 입력 포트 없음은 `icm_config`가 `view_required`로 먼저 낸다 -- 이 함수의 `no_input_port` 갈래는 도달 0이라 두지 않음) 어느 포트든 `missing`이 있으면 그 code(category `numeric` -- 단 `input_window_operating_point_mismatch`(선언과 동작점의 불일치로 창이 정의되지 않음, 4.7-3a 3 -- **S-4 갈래 몫**: (S4-가) 이 card, (S4-나) card EO-1이 정의·배선하고 (S4-나)의 IT-2 소스에는 정의 0 -- 사용자 결정 O-98)는 `definitional`; `input_window_f_component_undeclared` 삭제; detail에 `("port", net)`을 더함). **커널 ICMR 선언 제약**은 이 metric 값을 읽으므로 같은 `Undefined`(예: `input_window_unmeasured`)로 판정 불능이다(계획 N3.14 공통 실패 규약 -- 새 경로 없음; 커널 θ 프레임 미수렴은 여기에 들지 않는다 -- v6.34 O-109 D2). V_cm 칸(`vcm_lo`·`vcm_hi`)이 None인 점은 늘 한 포트 이상에 `missing`이 있는 점이라(4.7-3b 계산 (6)) 이 갈래가 원인을 낸다(새 code 없음). 기록 형식은 as-built `Undefined(quantity, code, category, detail)`(`E/metrics/mna_types.py:41-48`, category ∈ `UNDEFINED_CATEGORIES`)이고 세 metric 이름마다 한 원소. **원인이 여럿일 때**(v1.12.1 N3): 한 metric에 원소 하나 -- definitional code가 numeric code보다 앞서고, 같은 category 안에서는 `ports` 순서 첫 포트. **측정 구성 정의 불능의 경로**(v1.12.1 검증 M7): `icm_window_metrics`는 `config.config`가 None이면 `ports`를 보지 않고 `config.undefined`의 원소 u마다 `Undefined(q, u.code, u.category, u.detail)`를 q ∈ {`icmr_v`, `icm_margin_v`, `required_input_cm_v`}마다 만들어 `undefined`에 싣는다 -- q = `IcmWindow`·`SwingIcmr` 칸 이름 = metric 등록의 `entry.field`(`E/metrics/registry.py:61-62`)여야 한다: `metric_value`(`E/metrics/evaluate.py:14-27`)가 `u.quantity == entry.field`로 거르므로 다르면 원인이 `unrecorded_cause`로 바뀐다. `IcmConfig.undefined` 원소 자신의 quantity는 `"icm_config"`(구성 기록)이고, 이 사상은 metric 단위 원인 기록(결과 기록, graph 필드 아님)이라 값 사본이 아니다. 구성 None이 포트 `missing`보다 앞선다(포트를 만들지 않음). 예: `Undefined("icm_margin_v", "input_window_unmeasured", "numeric", (("port", "vin_p"),))`.
  - `IcmWindow`(새 frozen dataclass, `E/metrics/aux_types.py`) 칸 = `icmr_v`, `icm_margin_v`, `required_input_cm_v`, `window`, `v_icm`, `input_dc`, `icmr_resolution`, `margin_resolution`, `undefined`(tuple[`Undefined`]), `model_error_ref`(정확도 표기 -- card ME-1 판정 기록 id, ME-1 전 None = 보고에 '보류', 4.7-2). **`sources` 칸 없음**(옛 'front 값의 포트별 출처 필드 참조'는 front가 다른 칸을 읽을 일이 없어(모든 포트 = `node.dc_window_cfg`, O-109 C1) 소비자 없는 칸이 되므로 두지 않는다). **사본 칸 없음**(v1.12.1 검증 M6·gap I-2, graph 단일 정본 규칙 2·4): 옛 `criterion`·`config` 칸은 두지 않는다 -- 보고 'β = 1 기본' 표기는 v1.14.0에서 삭제(ICMR에 follower 구성 없음 -- 계획 IT-2c 착수 조건 (vii)), 기준 표기는 그 값을 낸 필드 정의에서 온다(DE-1 전 `node.dc_window_cfg` = '+tol 판정'(계획 N3.8 '창 필드'), DE-1 뒤 `node.dc_window_def` = '정의 기준' -- 새 상수 없음). 측정 구성 정의 불능의 metric 경로는 위 '측정 구성 정의 불능의 경로'.
  - **출력 전용 필드 선언**(계획 N6.6 완료 조건 (5), 사용자 원칙 'graph 계산값 소비' -- 새 필드마다 엔진 소비자 ≥ 1 또는 출력 전용 선언): 이 card에서 엔진 안 소비자가 없는 아래는 **출력 전용**이다 -- (1) `IcmConfig.pivot_a_e`·`pivot_resolution`(servo 피벗 기록 -- 결과 JSON·변화표; card DE-1 (c)가 A_dc 정본으로 합칠 때 소비자가 생김, 4.7-3b; 옛 `transfer` 대체) (2) 커널 θ 프레임 창 `node.dc_window`의 상태 칸 `input_status`·`tol_v`(값 독자 `fd_jacobian`은 `lo`·`hi`만 읽음; 상태는 card 0 발동률·변화표 -- 계획 완료 조건 (6), D2로 metric 소비자 없음) (3) `IcmWindow.model_error_ref`(card ME-1 전 늘 None, 보고 '보류'; ME-1이 생산·소비). 엔진 소비자가 있는 새 필드·칸: `node.dc_window_cfg`(`Window.input_status`·`tol_v` 포함) → `metrics_aux`(`IcmPort`), `graph.icm_config`(`config`·V_cm 칸·`undefined`) → `metrics_aux`, `graph.ss_nodal`(`g`·`factor`) → `icm_config`·`metrics_aux`(세 자리), `NodalSystem.g_bound` → `icm_config`의 `_transfer_resolution`(계획 완료 조건 (5) 'E의 소비자 = servo 피벗 판정 분해능 정의 함수 ≥ 1'). 옛 `graph.metrics_icm_front`·`RefinedWindow.criterion`·`IcmWindow.sources`·perf `window_end_solves`는 없다(C1). 출력 전용 선언은 EO-1·ME-1 병합 때 각 design이 소비자로 바꾼다.
- **커널(front·보고 같은 값)**: `metrics_aux`가 입력 포트의 `node.dc_window_cfg`·`graph.icm_config`·`node.dc_colour`(READS에 더함; `node.dc_window`는 읽지 않는다 -- 계획 N6.6 범위 1 '커널 탐색만', v1.12.1 W1 철회)를 읽어 **입력 포트 모두**로 `IcmPort` 열을 만들고(비공개 함수 `_icm_ports(projection)` -- 칸 옮기기만, lo·hi 산술 없음) `icm_window_metrics(graph.icm_config 값, ports, input_dc)`를 부른다(`tied_ports` 거르기 삭제, U-106). 창 출처 = 모든 구성에서 `node.dc_window_cfg`, 세 metric 값 출처 = `graph.icm_config` V_cm 칸, 구성 None이면 M7 경로. **AST 대상**(계획 완료 조건 (8)(g) '대상 함수 이름은 design'): `icm_window_metrics`와 `metrics_aux._icm_ports` -- 두 함수 소스에 `lo`·`hi` 속성을 피연산자로 쓰는 산술(`BinOp`, `sum`·`min`·`max`·`statistics.mean` 호출 인자) 0(포트 창에서 V_cm을 다시 내는 둘째 생산자 금지).
  - `ls_swing` 새 서명 = **`ls_swing(devices, rails, node_v, outputs, diff_outputs=False) -> SwingIcmr`**: 출력 스윙만 낸다(입력 창 계산 `:107-118`, 인자 `inputs`·`input_dc_v`, `no_input_port` 정지와 입력 넷의 `node_v_missing` 검사, 그 문언 삭제 -- 계획 N6.6 범위 3). 반환 `SwingIcmr`의 입력 칸은 기본값(`icmr_v`·`icm_margin_v` = None, `window` = `()`, `v_icm`·`required_input_cm_v` = None, `input_dc` = `""`, 두 분해능 None)이고 `undefined`에는 스윙 사유만 든다.
  - **합치는 규칙**: `metrics_aux`가 `dataclasses.replace(swing, icmr_v=iw.icmr_v, icm_margin_v=iw.icm_margin_v, window=iw.window, v_icm=iw.v_icm, required_input_cm_v=iw.required_input_cm_v, input_dc=iw.input_dc, icmr_resolution=iw.icmr_resolution, margin_resolution=iw.margin_resolution, undefined=swing.undefined + iw.undefined)`로 한 `SwingIcmr`을 만든다(`iw` = `IcmWindow`). 그래서 `SwingIcmr` 형식·결과 JSON·`swing_icmr` 보고 행 키·분해능 칸 이름(`RESOLUTION_FIELDS`, `metrics_aux.py`)은 그대로다(형식 불변, IT-Q2).
  - `bounds`(모든 넷의 경로 합 구간, `ls_fields` 입력)는 card DE-1 전까지 그대로다. 단서: as-built 넷 집합은 `set(inputs)`를 더했으나 입력 포트는 MOS gate라 소자 단자 넷에 이미 들고, 소자에 닿지 않는 입력 포트만 `bounds`에서 빠진다(그 넷은 `ls_fields`가 읽지 않는다).
  - 등록: `E/_module_map.py`의 `metrics/ls_swing.py` 행 서명 갱신, `metrics/icm_window.py` 행 추가. **B77 -- `metrics_aux` 결측 판정 영역 분리**(card IT-2d, 계획 v6.34.2 N3.8 'metric 결측 판정 -- 영역 규칙 하나'·N6.6 'IT-2d -- B77' (1)~(4), 사용자 결정 O-111·O-112·O-113 -- 정의는 계획, 인용만): (가) **relabel** -- `E/metrics/registry.py` `_ROWS` 영역 칸 `offset_in_sigma_mv`(`:56`)·`offset_excess`(`:57`)·`offset_sys_mv`(`:58`)·`mirror_ratio_sigma_pct`(`:59`)·`swing_out_v`·`icmr_v`·`icm_margin_v`(`:60-62`) → `"dc"`, `ff_gm_ratio`(`:63`) `"ss"` 그대로(integ-it12 `1fa7b1e5` 재측정 -- 계획 줄 번호와 같음; VB-1이 먼저 병합되어 `offset_sys_mv`가 이미 `dc`면 다시 바꾸지 않음); 같은 변경에서 `E/metrics/pending_metrics.py:15-18` 서술과 design 40 §3.8-8 영역 열 (나) **결측 판정 함수 하나** `_missing_gate(request, ss, nodal, registry) -> Undefined | None`(`metrics_aux.py` 비공개 -- 계획 완료 조건 (13)(c) AST 대상): `ss.missing`(`graph.ss_circuit` READS)이 비면 None; 아니면 영역 = `registry[request.metric].signature.domain`(정본 `MetricSignature.domain` 하나 -- 분류 표·metric 이름 목록 사본 0), 영역 `"dc"`이면 `graph.ss_nodal`(READS)이 `Undefined`일 때만 정의 불능(code가 `passive_value_undeclared`면 그 `Undefined`의 code·detail(결측 저항 `("elements", …)`), 다른 code면 그 code 그대로 -- 결측 code를 붙이지 않음, 계획 v6.34.2 재검증 N-b의 fail-closed 처리; 지금 `ss_nodal`의 `Undefined`는 결측 code뿐이라 발동 0), `NodalSystem`이면 None(계산 진행); 그 밖 영역(`ss`·`ls`·`geom`, 어휘 밖 값 포함)은 `passive_value_undeclared`(detail `("elements", ss.missing)` -- 지금 동작). 술어 `is_dc_conducting_passive` 호출 0(DC 결측 판정 생산자 = `ss_nodal` 하나). 옛 `:164-166` 요청 전체 실패 분기를 이 함수로 대체(요청마다 부르고, 실패한 요청은 계산 루프에서 빠짐); bundle detail `("missing_passives", ss.missing)`은 그대로. 용량만 결측인 점의 영역 `dc` metric은 결측 없는 회로와 같은 계산 경로(용량은 G·DC 망에 들지 않고 `ss_circuit`은 값 없는 수동소자를 스탬프하지 않음) (다) **보고**: 결측이 하나라도 있으면 전달 뷰 보고(`:224-239` 루프 -- `block_residual`·`nqs_ratio`·`ls_fields`·FF 보고; registry 행이 없어 영역 정본이 없음)는 내지 않고, metric별 보고(`offset_contrib`·`swing_icmr`·`mirror_ratio` -- `required_input_cm_v`는 `swing_icmr` 보고 칸)는 그 metric이 정의되면 낸다(**원래 취지와 다름(작음)**: O-112 '보고 항목은 결측 시 지금처럼 내지 않음'을 전달 뷰 보고로 해석, **확정 O-113**) (라) `metrics_ss`는 대상 없음(요청이 모두 영역 `ss` -- `ss_evaluate.py:95-96`; `ss_metrics.py:401-403` 그대로) (마) READS 추가 0(`graph.ss_nodal`·`graph.ss_circuit`은 IT-2c가 이미 더함), 새 code·필드·cache 0. **변경 종류**: 동작 변경(O-34 (1)) -- 변화표 원인 칸 둘(원인 'B77(O-111·O-112)' = 용량만 결측 점의 DC metric 정의 불능 → 정의됨, 원인 '`ls_swing` 삭제·cfg 배선(범위 2·3, O-109 C1)' = 정의된 점의 ICMR·스윙 값 출처 변경 -- 한 칸에 섞지 않음), `ff_gm_ratio`는 용량만 결측이어도 정의 불능(O-112 `ss` 유지 -- 변화표 칸에 사실로 적음), 코퍼스의 용량만 결측 봉인점 수는 착수 때 재고 변화표에 적음.
- **front·보고 -- 별도 블록 없음**(계획 v6.34 N3.8 '측정 구성 창 = 선형 감도 끝 하나'·N6.6 범위 2, 사용자 결정 O-109 C1 -- **원래 취지와 다름, 승인 O-109**): front 전용 입력 CM metric 블록 `metrics_icm_front`(`E/metrics/icm_front.py`·`icm_front`·`METRICS_ICM_FRONT_WRITER`·`graph.metrics_icm_front`·`SS_WRITES` 행·test `test_icm_front.py`)는 만들지 않는다 -- 커널 입력 CM metric과 같은 입력(`node.dc_window_cfg`)·같은 정의라 만들면 둘째 생산자다. front 점·층 0 front 후보 점의 보고 값(EO-1 oracle 입력 생산자·U16 보고서가 읽는다, DEC-98 oracle 대조 값)은 그 점 커널 평가 스냅샷(`_point_record`의 `snapshot_ref` -- run 레코드 키·형식 그대로)의 `metrics_aux` 세 metric이다(추가 호출 0). 정확값은 oracle `.dc` 훑기가 확정한다. **제약 판정은 커널 값**이다(DEC-74; 'front 판정' = oracle 대조·보고 값, 계획 N6.6 범위 1 A-N3). **IT-2d 범위**(계획 v6.34 N6.6 순서 'IT-2d 범위 = front·보고가 `node.dc_window_cfg` 값을 쓰는 배선과 옛 입력 창 계산(`ls_swing`) 삭제·`metrics_aux` 배선뿐'): `icm_window.py`(`icm_window_metrics`)·`aux_types.py`(`IcmPort`·`IcmWindow`)·`metrics_aux.py` 배선(위 '커널')·`ls_swing.py` 입력 창 삭제(새 서명)·그 CONTRACT·모듈 지도 행(4.7-6), V_cm 좌표(U-106 -- 위 정의 함수), **B77**(위 793 -- registry relabel·`_missing_gate`·보고 갈래; 계획 v6.34.2).
- **정의 불능 front 처리**(옛 '미수렴 front 처리'(O-64 (2))는 cfg가 미수렴을 이어받지 않아 **대상 없음**, 사용자 결정 O-109 D2; 새 경로·새 칸·새 상태 없음): 세 metric이 정의 불능인 점(`input_window_unmeasured`·구성 None code)에서 (가) **선언 제약이 걸린 값**(선언 `icmr_v`·`icm_margin_v` 제약): 그 제약 판정은 커널 값(DEC-74)이고 기존 `ss_constraint_rows`가 행 없이 `unmeasured`에 (metric, op, code)를 싣고(`E/search/ss_constraints.py` 머리 '값 None(Undefined)'), 그 점은 최종 `front`(봉인 + 모든 ss 제약 측정 -- `E/search/eps_sweep.py` `_CLASSES`)에서 빠져 `unmeasured_front` 안 비지배 재필터(`_filter` → `nondominated`)를 거친다. 원인 = 그 unmeasured code -- fail-closed. (나) **제약 없는 보고 값**: 그 점의 front 분류는 바뀌지 않고 `metrics_aux` 결과의 `undefined`에만 원인이 남는다(보고에서만 정의 불능). 두 갈래 모두 엔진 `ss_constraints` 기존 규칙과 같다. 커널 θ 프레임 창 미수렴은 이 경로에 들지 않는다(D2 -- 4.7-3b). **oracle 판정 입력**(계획 v6.37 DEC-98 (6)·N3.8 '선언 슬루의 엔진 표시', 확정 O-124): 같은 `unmeasured_front` 가운데 미측정 사유가 모두 `oracle_judged`('oracle 판정 대상' -- 엔진 metric이 없는 oracle 전용 제약, 지금은 슬루; 40 §3.8-3)인 점은 oracle front 판정 입력에 들어간다(40 §10.5; 새 칸 0). 위 (가)의 정의 불능 code가 하나라도 있는 점은 사유가 `oracle_judged`뿐이 아니므로 들지 않는다(fail-closed). oracle 판정 뒤 처리는 **계획 U-112 닫힘**(v6.38 사용자 결정 O-143 (4)·O-144 -- oracle 전용 제약 FAIL 점과 추종 검사 정의 불능 점(O-145)은 front에서 빼고 기록, 되먹임 없음; 배선 = card LA-1 front 판정 배선, O-44 (1))을 따른다(40 §10.5 (ii)).

**4.7-6 소비자 정리(계획 N6.6 소비자 표 + A10)**: `fd_jacobian._steps`의 y 스텝은 `node.dc_window` 항목을 그대로 읽는다 -- 그 필드 항목은 정의상 W4 뿌리뿐이라(D1·v1.15.2 E-13 순서 창) as-built의 `free_window` 필터는 무동작이고 같은 변경(card WB-1 범위 3a -- 그 줄이 FD 스텝 변화표 원인 항목과 같은 자리)에서 지운다(O-165·O-169: 유지 근거가 '지금 있다'뿐; 비교 = 유지(같은 정의를 두 자리에서 거름 -- 규칙 3 소지) / 삭제(정의 하나) -- 삭제 채택). `E/sizing/CONTRACT.md` 소유표 행 `node.dc_window`(IT-2b가 범위를 '모든 입력 포트와 W4 뿌리'로 넓힘)의 범위 = **'W4 뿌리 노드'로 되돌림**(계획 v6.34 N6.6 범위 1 '필드 소유표 행의 범위는 W4 뿌리 노드 그대로' -- D1)·형식 `Window`(칸 다섯), 그 소유표의 `node.dc_output_structure` 행 삭제(D4 -- 4.7-1a), 14.6절 문언(IT-2c). **새 행**(IT-2c): `graph.ss_nodal`(writer `ss_nodal`)·`graph.icm_config`·`node.dc_window_cfg`(writer `icm_config`) -- 해당 CONTRACT(`E/metrics/CONTRACT.md`). 그 밖 같은 변경에서 고치는 자리: IT-2c -- `E/sizing/s2_values.py` `SS_WRITES`(`ss_nodal`·`icm_config` 행 → `S2_WRITERS`)·`DC_WRITES`(D4 원소 삭제), `E/sizing/__init__.py` `__all__`(`Circuit`·`saturation_window`·`INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED`·`SS_CIRCUIT_WRITER`·`SS_NODAL_WRITER`·`ICM_CONFIG_WRITER` -- 4.7-4), `E/tests/metrics/test_ss_metrics.py:35-36`(블록 `metrics_ss`를 직접 부르는 픽스처 -- `graph.ss_circuit`을 먼저 써야 한다, 재검증 3 N-B; test 작성 주체 몫), **metrics CONTRACT 소유표 `graph.ss_nodal` 행**(값 타입 `NodalSystem | Undefined`, 읽는 쪽 처리: `icm_config` = `Undefined`면 구성 None·같은 code(4.7-3b), `metrics_aux` 세 자리 = 같은 code로 정의 불능(실제로는 `ss.missing` 선차단 -- B77) -- 재검증 3 N-A), `E/tests/sizing/test_s2_values.py`의 `SS_TABLE`·S2 = S1 + `DC_TABLE` + `SS_TABLE` 등식·`DC_TABLE` 행 수 기대(`SS_WRITES`에 `ss_nodal`·`icm_config` 행이 생기고 `DC_WRITES`에서 D4 원소가 빠짐 -- 기대 갱신은 test 작성 주체 몫, 옛 4.7-1a 719에서 옮김), `E/metrics/records.py` `StampSet.g_ops`·`stamp_mos.py`·`stamp_two_terminal.py`·`_helpers_nodal.py`(`conductance_matrix` `bound`), **`E/metrics/CONTRACT.md`의 `StampSet` 행**(생성자 계약 변경 -- 칸 `g_ops`, `__post_init__` 길이 불일치 `ValueError`; 셋째 커밋 R3), `E/_module_map.py`(새 파일 셋 `metrics/ss_nodal.py`·`metrics/icm_config.py`·`sizing/_helpers_dc_solve.py`, `saturation_window` 서명 행, `writer_plan.py` 책임 문장; **metrics 층**(셋째 커밋 R4, 지금 지도 기준 `_helpers_nodal` 층 2·`aux_types` 층 0·`metrics_aux` 층 5·`ss_evaluate` 층 7): `icm_config` = 층 3(`_helpers_nodal`(2)·`aux_types`(0) import, 다른 metrics 파일이 import하지 않음), `ss_nodal` = **층 3**(실제 import = `ss_circuit`(층 1, `CODE_PASSIVE_MISSING`)·`_helpers_nodal`(층 2, `conductance_matrix`·`nodal_factor`)·`aux_types`(층 0, `NodalSystem`)·`mna_types`(`Undefined`), 가장 높은 층 2 + 1; 회로는 import가 아니라 `graph.ss_circuit` READS; `icm_config`와 같은 층이나 서로 import하지 않음, 둘을 부르는 `ss_evaluate`(7)가 앞 층 쪽으로 import), `ss_circuit.py`(층 1 그대로 -- 블록 `ss_circuit_field`가 `core`·`sizing` 공개 이름만 더 import) 모듈 지도 행의 진입점 `ss_circuit` → `ss_circuit_field`(다섯째 커밋 -- 4.7-3b `graph.ss_nodal`), **metrics CONTRACT 12.0 표**(`:1226` 이하 -- `ss_circuit.py` 행 진입점 `ss_circuit_field`, 새 행 `ss_nodal.py`·`icm_config.py` 층 3)·**metrics CONTRACT 소유표에 `graph.ss_circuit`(writer `ss_circuit`) 행**, `s2_values.py` `SS_CIRCUIT_WRITER`·`SS_WRITES` 행(→ `S2_WRITERS`, `test_s2_values.py` `SS_TABLE` 기대 -- test 작성 주체 몫), `ss_evaluate.py`(`ss_dev` 뒤 `ss_circuit_field` 호출), `ss_metrics.py`·`metrics_aux.py`(인라인 조립·`_ss_of`·`CODE_PASSIVE_MISSING` 정의 삭제 → `graph.ss_circuit` READS·`ss_circuit.CODE_PASSIVE_MISSING` import, 동작 불변)); IT-2d -- `E/metrics/CONTRACT.md:1235`(`ls_swing` 서명 행), `:1286`(V_icm = 첫 포트·y_icm 문언), `:1334`(SP-2 대기 `icm_margin_v`), `E/metrics/aux_types.py:160-172`(`SwingIcmr` docstring의 V_icm 문언, `IcmPort`·`IcmWindow` 추가), `E/tests/metrics/test_aux_types.py:40`(`SwingIcmr(None, None, None)` -- 형식 불변이라 기대 그대로, 새 타입 test 추가는 test 주체), `E/_module_map.py`(`metrics/icm_window.py` 행·`ls_swing` 서명 행). `headroom_bound`의 창은 대상이 아니다. **v1.14.0 추가**: IT-2c -- `E/metrics/aux_types.py` `IcmConfig` 칸(`config`·`pivot_a_e`·`pivot_resolution`·`vcm0`·`vcm_lo`·`vcm_hi`·`undefined`), (v1.14.0의 `SizingSpecDoc.icmr_view`·`DcInputs.icm_view`·extras와 그 CONTRACT 행은 삭제) `E/graph/views.py`(`collect_views` 출력 규칙·씨앗 `default_port`)·`E/graph/s1v_values.py`(`ViewSeed`·`ViewS1v` 칸 `default_port`)·`E/graph/s1v_fields.py`·`analyze_view`(칸 옮김)·graph CONTRACT S1v `views` 행, `E/sizing/input_window.py`(`saturation_window` 행 꼴 = 일반 1차 행)·`block_columns.py`(`region_rows` 반환 꼴, `writer_head`·`_windows` F 성분 갈래 삭제)·`s2_values.py`(`INPUT_STATUS_F_COMPONENT_UNDECLARED` 삭제)·sizing CONTRACT(상태 어휘·`Window` 행), `icm_config.py` `_conduction_rows`, 함수 레지스트리 행(`kvl_sensitivity` servo 서명; `_dc_feedback_reaches` 개념 행·`feedback_cut_nets` 행은 이 card에서 만들지 않음 -- TN-1 몫); IT-2d -- `E/metrics/registry.py:56-62` 영역 칸, `E/metrics/pending_metrics.py:15-18`, metrics CONTRACT의 영역 서술, design 40 §3.8-8 영역 열; **영향 test**(계획 v6.34.2 '영역 값 영향 목록', integ-it12 `1fa7b1e5` 재측정 -- 줄 같음): `E/tests/metrics/test_registry.py:44-50`(단언 `:69`), `E/tests/authoring/conftest.py:105-111`(소비 `E/tests/metrics/test_pending_metrics.py:64`·`:131-135`, `E/tests/metrics/test_catalog.py:47-49`), `test_catalog.py:52-55`, `test_pending_metrics.py:76-79`·`:82-86`, `E/tests/integration/test_spec_library_load.py:552`(`U5_METRICS` -- 영역 단언 없음, 착수 때 실행으로 확인) -- 기대 갱신은 IT-2d test 작성 주체 몫(근거 O-112). **IT-2c 영향 test**(둘째 커밋, 검증 N-1 -- integ-it12 `3179cd78` 재측정): `E/tests/sizing/test_block_columns.py:1161-1168`(F 성분 포트 θ 창 항목 `f_component_undeclared` 단언 -- D1·O-118 3번으로 항목·상태가 없어짐), `E/tests/sizing/test_s2_values.py:227-228`(`Window(None, None, 0, input_status="f_component_undeclared")` 리터럴 -- 상태 값 삭제) -- 기대 갱신은 IT-2c test 작성 주체 몫. **재계수**: G-10 -- 새 블록·필드 0(블록 `ss_circuit`·`ss_nodal`·`icm_config` 그대로, `graph.icm_config` 칸만 바뀜)이라 ss 단계 같은 θ 재평가 계수(블록마다 (computes, grafts, reuses) = (0, 1, 0))와 `size_and_seal` reuse 12·graft 1 불변; 블록 수 불변(S1v writer `s1v_fields`도 출력 칸만 바뀜), `icm_config` READS 변화(S1 넷 넷 삭제, `graph.views`·`node.port_role`·`device.ss_dev`·`device.dc_op`·`device.dc_conduction_floor` 추가)와 extras 셋 → 둘로 그 블록 입력 버전이 한 번 바뀜, S1v 값 지문 변화(4.7-3b READS '(나)')로 S1v 소비자 블록 입력 버전도 한 번 바뀜(변화표). 모듈 지도 층 -- `icm_config` 층 3 그대로(import `_helpers_nodal`(2)·`aux_types`(0)·`ss_circuit`(1)·`mna_types`; 옛 authoring `feedback_cut_nets` import 없음), `icm_window` 층 1(`aux_types`·`mna_types`만), `metrics_aux` 층 5 그대로(`registry`는 이미 import -- `metrics_aux.py:38`). `sizing.__all__` -- v1.14.1 일곱 이름(`Circuit`·`saturation_window`·`INPUT_STATUS_MEASURED`·`INPUT_STATUS_UNMEASURED`·`SS_CIRCUIT_WRITER`·`SS_NODAL_WRITER`·`ICM_CONFIG_WRITER` -- `INPUT_STATUS_F_COMPONENT_UNDECLARED` 삭제, 새 공개 이름 0). 모듈 지도 층: `icm_config`는 `graph` 공개 이름(`VIEW_TRANSFER` 등 -- 선례 `metrics_aux.py:22`)만 더 import하고 metrics 층 3 그대로.

**4.7-7 test interface(IT-2, test 작성 주체 -- 소스 없이)**: 공개 진입점 `dc_columns`(서명 불변), `ss_nodal_system`·`icm_config_window`(블록, 4.7-3b), 순수 함수 `kvl_sensitivity(nodal, drive, servo=None)`(4.7-3b (3), v1.14.0)·`icm_window_metrics(config, ports, input_dc)`·`saturation_window`(v1.13.0 서명 `(unknown, root, values, gradient, rows, *, slope=None) -> (dlo, dhi, slope) | None` -- 4.7-3 2; `root` = 넷 하나, `slope`를 주면 감도 연립 없이 끝만, 쌍 roots·묶음 갈래 없음)·`conductance_matrix(circuit, size, *, bound=False)`(4.7-3b `graph.ss_nodal`)·`ls_swing`(새 서명)·`writers_in_scope(base, blocks) -> frozenset`(card IT-2e, `E/sizing/seal_versions.py` -- 4.7-3c, v1.12.9), 공개 클래스 `Circuit`(`gmid_engine.sizing` -- 4.7-4; `region_rows`·`port_window`(`writer_head` 삭제)), 타입 `Window`·`ViewS1v`(`default_port` 칸, v1.14.1)·`NodalSystem`(`g_bound` 칸)·`IcmConfig`·`IcmPort`·`IcmWindow`·`StampSet`(`g_ops` 칸). **없는 것**(O-109 C1): `refine_input_windows`·`icm_front`·`refine_front_windows`·`RefinedWindow`·`WindowEnd`. **`rows` 입력 꼴 변경**: as-built `saturation_window`는 4원소 행 `(d, s, sign, slack)`을 받았다(`E/sizing/input_window.py:57`); 새 꼴은 일반 1차 행 `(terms, slack, kind)`(4.7-3a 1 -- 포화·`triode` 행은 `terms` = ((a, sign), (b, −sign)), 전도 행 R0는 노드 가중합 -- 4.7-3a 6)이고 `saturation_window`는 `kind`를 창 계산에 쓰지 않는다(끝 정의는 행마다 `slack + sign·(s_a − s_b)·Δ ≥ 0`의 교집합 그대로). 필드·형식은 4.7-2, 사유 이름은 4.7-4 3·4.7-5. 단언(계획 N6.6 완료 조건 (0)~(6)을 측정할 수 있는 꼴):
- K1(계획 v6.34 완료 조건 (1)) 입력 DC 선언 toy: 입력 포트의 `node.dc_window_cfg` 항목이 있고 `input_status == "measured"`(base는 입력 창 없음 -- red), 커널 `node.dc_window` 항목은 입력 W4 뿌리뿐(뿌리 아닌 포트·선언 포트 항목이 있으면 red -- D1; 선언 회로는 입력 포트 항목 0). 미선언 2입력 toy: `node.dc_window` 입력 포트 항목 = 뿌리 하나, `node.dc_window_cfg` 두 포트 항목 모두 있음. 측정 구성 창을 잴 수 없는 toy(VDSAT 열 없는 LUT 축소 픽스처 등 -- `region_rows` None): cfg 항목 `input_status == "unmeasured"`, 세 metric 정의 불능 `input_window_unmeasured`.
- K2 커널 θ 프레임 뿌리 창 = 손계산 오라클(toy 연결의 θ 고정 선형 감도 손계산, '추정' 정확도 표기 -- 4.7-3 1).
- K3(계획 완료 조건 (0)·(1)) **다듬은 창·front 전용 블록 부재**: 비test 엔진 소스(`git grep`, 정의 기준)에 끝 풀이 함수(as-built `_refine_ends`·`_root_windows`) 정의 0·호출 0, `dc_window_def_refined`·`dc_window_refine`·`refine_input_windows`·`metrics_icm_front`·`icm_front`·`refine_front_windows`·`RefinedWindow`·`WindowEnd`·`window_end_solves` 정의 0; 엔진 소스에 S3 색인 밖 새 결과 캐시 없음(`git grep` -- `front_cache` 0).
- K4(계획 완료 조건 (1)·(5), D1·D4) **삭제 확인**: `block_columns._windows`가 W4 뿌리 아닌 넷에 항목을 쓰지 않음(뿌리 아닌 입력 포트·선언 포트·F 성분 미선언 포트 toy 셋 -- 있으면 red); 출력 구조 분류 필드(`dc_output_structure`)·그 writer 원소·`OUTPUT_HIGH_IMPEDANCE`·`OUTPUT_KVL_FIXED`·`icm_config_output_root_w3`·`saturation_window`의 쌍 roots 갈래(원소가 tuple인 roots 처리)·선언 포트 묶음 갈래의 정의·READS 0(비test 엔진 소스 `git grep`/AST).
- R2(옛 다듬은 창 red 변형 둘은 대상 없음, O-109 C1) **장애 주입 범위**: 내부 이름 monkeypatch는 커널 되풀이 소진 주입 `gmid_engine.sizing.block_columns.k_max`(상한 1 -- L12 (a), v1.12.10)와 L11 (e)의 블록 실패 주입(`ComputeBlock.__call__` 감쌈, 재연 선택 사례의 블록 인스턴스 `fn` 교체)뿐이다(`window_refine` 주입 지점 없음).
- M1(계획 완료 조건 (1)·(12)(c)) 커널 `icm_margin_v`·`icmr_v`·`required_input_cm_v` = `icm_window_metrics`(`graph.icm_config` V_cm 칸·`node.dc_window_cfg` 항목)와 같은 값(모든 구성 -- `as_is_single_input` toy 포함, v1.12.1 W1 철회), front·보고 값 = 같은 값(같은 스냅샷의 `metrics_aux` -- 다른 칸·블록에서 값을 내면 red, O-109 C1).
- W1 배선(IT-2d): 외층이 도는 toy 실행(`find_front`)에서 front 점마다 `snapshot_ref`가 가리키는 스냅샷의 `metrics_aux` 세 metric = 같은 스냅샷 `graph.icm_config`·`node.dc_window_cfg`로 부른 `icm_window_metrics` 값; front 기록 때 블록 `computes` 증분 0, `kernel_calls` 불변(추가 호출 0).
- M2 `git grep`(계획 v6.34 완료 조건 (2), 사용자 결정 O-61 P2): `ls_swing`에 입력 창 계산 0; 창 끝 식(행 교집합)을 가진 함수 = `input_window.saturation_window` 하나; 그 함수를 부르는 자리 = **둘** -- `dc_columns`(θ 프레임 창 `node.dc_window`, W4 뿌리 -- `block_columns._Circuit.input_windows`를 거쳐)·`icm_config`(`node.dc_window_cfg`, `slope=` 갈래로 직접 -- 4.7-3b (4)) -- 그 밖 호출·끝 식 재구현 0(`headroom_bound` 제외 -- LUT 격자 최솟값 상한, 다른 개념; 옛 '셋'의 다듬은 창 블록 삭제).
- M3(계획 완료 조건 (4)) 포트 창 재계산 0: 포트 창을 내는 자리 = `icm_config` 하나, 포트 창 계산이 θ `_sensitivities` 외삽·κ 경로 합·별도 노드 풀이·끝 풀이를 하지 않음(`git grep` + G-10 + WP-10 중복 인자 계측).
- P(계획 v6.34 완료 조건 (7), O-49): (a) 감도 음수 포트 toy -- 측정 구성 판정 창 포트 창 lo ≤ hi이고 = 두 끝 전압의 [min, max](손계산; base는 lo > hi -- red) (b) 입력 DC 둘 선언 toy(계획 v6.35.1 완료 조건 (7)(b) 사실 정정 그대로 -- 검증 S-3·gap N-2 해소): **일반 toy** -- 두 선언 포트를 같은 x로 함께 구동한 servo 창 끝 = servo 손계산 끝(포트별 따로 훑은 창이면 red); **대칭 toy**(입력 공통모드 → 감지 DC 전달이 0인 꼴 -- ε ≈ 0) -- 'x 구동 몫의 포트 차 = 선언 차'를 graph 출력(`node.dc_window_cfg` 포트 끝)만으로 관측, **전제 단언 둘**(어기면 그 사례 무효): (i) 손계산 \|vx_s\| ≤ 판정 분해능(포트 끝 차와 선언 차의 비교는 허용치 안) (ii) 같은 toy에서 포트별로 따로 훑은 창의 끝 차가 선언 차와 비교 허용치보다 크게 다름(포트별 훑기 red가 공허하지 않게); 구동 벡터를 test용 공개 칸으로 내지 않는다(엔진 소비자 없는 칸 -- 계획 같은 문장); `IcmWindow`에 `criterion`·`config`·`sources` 칸 없음(사본 칸 부재 단언 -- v1.12.1 M6); 옛 (c) (ii) 끝 toy·(d) 다듬은 창 블록 READS·(e) 기준 칸 단언은 대상이 없어 두지 않는다(사용자 결정 O-109 C1 -- **원래 취지와 다름**).
- D(계획 완료 조건 (9), O-54·O-58 S-4·O-98, 4.7-3a -- **S-4 갈래를 따른다**, v1.12.10): **(S4-나) IT-2b의 D = 계획 (9) (a)~(d)**: (a) `triode` 선언 소자가 동작점에서 triode이고(전제 단언) 훑기 중 포화로 가는 toy → 그 행의 영 교차 = 창 끝(커널 창·측정 구성 판정 창 모두 -- 측정 구성 판정 창은 IT-2c(KCL 감도), v1.13.0; 손계산 오라클: 행 `(d, s, −부호, VDsat − VDS − tol_VDsat)`의 영 교차; base는 선언 소자를 행에서 빼 놓침 -- red) (b) `region_rows` 행 `kind` 집합 = {`"sat"`, `"triode"`}(v1.14.1: 측정 구성 판정 창의 전도 행 `"conduction"`은 `region_rows`가 아닌 `icm_config._conduction_rows`가 만든다 -- 4.7-3a 6 '(9)과의 관계') (c) 행 여유는 `tol_VDsat` 정본 값과 그 해의 VDS·VDsat만 읽고(행 기울기는 writer 식 편미분) 경계 행 계산은 전도·문턱 계산을 하지 않음 -- 측정은 **정적 AST만**(docstring·주석 제외): `region_rows`와 그것이 부르는 IT-2 모듈 함수의 소스에 (i) VGS 인자가 상수 0인 `op_point` 호출 0 (ii) `device.dc_off_current`·`device.dc_conduction_floor` 읽기 0 (iii) EO-1 모듈 import 0(이름은 EO-1 design); 새 계수기·monkeypatch 없음 (d) 불일치 상태 값·소자 열 칸·그 metric code의 정의 포함 0 -- 측정 = (c)와 같은 꼴의 **정적 AST 검사**(비test 엔진 소스, docstring·주석 제외): 식별자(이름·속성·인자·키워드·dataclass 필드·대입 대상)와 문자열 상수에 `"op_mismatch"`·`status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH`(4.7-2 'S-4 갈래 몫의 꼴') 0(계획 (9)(d) '`git grep`'의 측정 꼴을 (c)와 하나로 정함; docstring에 '없다'는 설명은 셈하지 않음). **(S4-가)이면 D가 더 진다**(계획 (9) -- N6.20 (8)(e)(i)~(iii)와 같은 단언): `off` 선언 소자가 켜지는 toy → 창 끝 = V_on 행 영 교차; 동작점 불일치 toy 셋(선언 `triode`가 포화, 선언 `triode`가 꺼짐, 선언 `off`가 전도 -- 4.7-3a 3)마다 (나) 같은 점 봉인 거부(선언 오류) (라) 블록 판정 자리 = 공용 전도 판정 함수 호출 하나, 행 여유 부호 판정 0(`git grep`); (가)(다)(상태 값·소자 열·metric code 단언)는 실을 cfg 항목이 대상 없음이라(계획 v6.34 셋째 커밋 -- 4.7-3a 3) 그 칸·code를 두기로 정한 경우에만 그 design이 정한다; 그리고 (N6.20 (8)(e)(iii)) 검증자 변화표에 노드 풀이 블록(`dc_columns`) 출력의 불일치 상태 행 변화와 원인(library 9회로, 4.7-8 변화표 원인 칸). (S4-나)에서 이 묶음 단언은 card EO-1 완료 조건 (8)(e)가 진다. (triode 경계 판정 여유는 계획 N3.8 '소자 조건'(O-58 T-1) 인용, tol_VDsat = `sat_threshold` 값 -- 옛 815행, v1.14.0에서 L13 자리를 위해 옮김.)
- L8(계획 v6.36 완료 조건 (8)(a)~(h), 4.7-3b; 사용자 결정 O-115·O-108·O-107·U-106; 기대값은 모두 손계산 oracle -- 피검 함수로 만들지 않음): (a) **KCL servo 창 끝 단언**: 되먹임 미선언 차동 입력·단일 출력 고임피던스 toy(출력 = 드레인만 닿는 W4 노드) -- `node.dc_window_cfg`의 끝 (lo, hi)가 **손으로 조립한 KCL servo 끝**과 일치: oracle = test가 소자 스탬프로 봉인점 DC 야코비안을 직접 조립하고 입력 포트를 모두 같은 x로 움직이는 구동과 여기 방향 e 보정 ε을 두어 감지 행 δV_out = 0을 풀어 감도와 끝을 낸다(피검 `conductance_matrix`·`kvl_sensitivity`·`saturation_window`·`region_rows`를 부르지 않음); **test가 선언하는 것** = 고정 집합(toy 구성에서, `NodalSystem.fixed`를 읽지 않음)·e 가중(toy spec의 기본 포트 뷰 ±1/\|D\| -- 손으로); **엔진 입력으로 읽는 것** = `device.ss_dev`의 gm·gds·gmb, `node.dc_v`, `device.dc_op`의 VGS·VDS·VSB·L·w_key, `device.dc_tol_v`; **여유 행의 VDsat·tol_VDsat** = test가 LUT 원시 함수 `vdsat(memo, kind, w_key, L, vgs, vds, vsb)`·`tol_vdsat_table(memo, kind, w_key).at(L, vds)`를 그 dc_op 점에서 직접 부름(`DeviceOp`에 VDsat 칸 없음 -- `E/sizing/s2_values.py:389-404`); **비교 허용치** = test가 봉인점 `device.dc_tol_v`의 `dc_coord` MOS 값 최솟값을 손으로 낸 값(피검 cfg `tol_v`로 정하지 않음 -- 같은지는 따로 단언; 새 상수 없음); **보조 단언(권장)** = 공개 `kvl_sensitivity`의 노드 감도를 손 조립 감도와 따로 대조(같은 허용). **전제 단언**(공허 방지 -- 어기면 그 사례 무효): (i) 'servo 손계산 끝 ≠ follower 손계산 끝' -- 같은 toy에서 출력 = 반전 입력 = x인 follower 끝도 손으로 내 두 끝의 차 > 비교 허용(출력 쪽 소자가 follower 끝을 정하는 toy) (ii) 'servo 손계산 끝 ≠ θ 손계산 끝' -- θ 고정 연립 끝도 손계산(피검 함수 없이)해 차 > 비교 허용; `node.dc_window_cfg` 끝이 follower 또는 θ 손계산 끝과 같으면 red, base(측정 구성 없는 끝)도 red; 감지 노드의 servo 감도 = 0(수치 분해능 안 -- 출력이 묶였음; `kvl_sensitivity` slope의 출력 넷); `graph.icm_config.config == "servo"`; front·보고 `icm_margin_v` = `graph.icm_config` V_cm 칸으로 낸 값('추정' -- (12)(c)). SPICE `.dc` 접선 교차 확인은 oracle card 몫 (b) **차동 출력 toy 둘**(CMFB가 출력 공통모드를 정하는 차동 입력·차동 출력) -- 되먹임 선언 없음과 용량만 선언: 감지 V_op − V_on을 묶은 servo 창 끝이 손계산과 일치하고 두 toy의 창·V_cm 칸이 같음(선언 되먹임을 읽지 않음); 결과 어디에든 `icm_config_differential_output_structure`·`icm_config_differential_output_undeclared`가 나오면 red (c) **KVL 고정 출력 toy**(부하 저항이 출력과 레일을 잇는 차동 입력 단일 출력, O-52) -- servo 창 끝 = 봉인점 DC 방정식(부하 포함 KCL) 1차 감도 연립 + servo 행의 선형 감도 끝과 손계산 일치, '추정'(base는 측정 구성 없는 끝 -- red); 출력 꼴 무관(D4): 출력이 W3 목표 노드인 toy도 같은 KCL servo 끝(목표값을 x로 바꾼 θ 고정 끝이면 red), `IcmConfig`에 `output_structure` 칸 없음, `icm_config_output_root_w3`가 나오면 red (d) **선언 무시 toy** -- 저항 되먹임(R 출력–반전 입력)이 선언된 2입력 단일 출력 toy에서 `config == "servo"`이고 창이 같은 회로(선언 소자는 봉인점 회로의 소자로 남음 -- G에 듦)의 servo 손계산과 일치(선언 되먹임 구성(반전 입력 노드 KCL 닫음)으로 잰 창이면 red); 단일 입력 + 선언 toy → `config == "as_is_single_input"`(spec 검사가 이 꼴을 받는지 미확인 -- 받지 않으면 test 작성 주체가 멈추고 보고) (e) **δV_out 판정 불능 단언**(계획 (8)(e) -- O-107, v6.35 대상 = a_e): 조립 상쇄 toy(a_e가 한 G 항목에서 여러 스탬프 항이 상쇄해 설계상 0인 꼴 -- 근거 `it2c_dvout_cancellation.md` toy b3·b5·b7 꼴) → `config is None`, `icm_servo_pivot_unresolved`(사유 기록); 전제 단언 = 같은 toy에서 옛 식 \|z_u\|ᵀ\|r\|로는 '판정 가능'(미지수 하나 toy면 r̂ = 0); 기대값 근거 = 같은 float64 파라미터를 정확 산술(유리수 또는 고정밀)로 조립·풀이한 참값 오차 \|V̂ − V_exact\|가 새 δV_out 안(피검 함수로 기대값을 만들지 않음); E 칸 생산 자리 = `graph.ss_nodal` writer 조립 루프 하나(L10 (c)); **다른 정의 불능 갈래 toy**(4.7-3b 계산 (1), 계획 v6.36 정의 불능 셋) -- 입력 셋 → `icm_inputs_unsupported`, 입력 0 → `view_required`, 2입력인데 role이 차동쌍이 아님(기본 뷰 둘) → `view_required`, 출력 둘인데 차동쌍 role이 아님 → `view_required`(각 code 하나, `node.dc_window_cfg` 없음, 세 metric이 그 code로 정의 불능 -- M7); 포트 role 맞바꿈 toy에서 창·V_cm 칸 같음(계획 N3.8 '포트 role'); **선언 뷰 무시 toy**(O-118 6번) -- gain 제약 view가 기본 뷰와 다른 (여기, 감지)로 선언된 toy에서 창 = 기본 포트 뷰로 잰 servo 손계산(선언 뷰로 잰 창이면 red), S1v `("graph", "views")`에 `default_port` 뷰가 정확히 하나(선언 뷰와 함께) (f) **삭제 확인**(계획 (8)(f), 만들면 배선): 비test 엔진 소스(`git grep` + AST, 문자열·상수 이름 모두, docstring·주석 제외)에 `"declared_feedback"`·`"follower_beta1"`, `IcmConfig` 칸 `inverting_port`·`tied_ports`·`transfer`, `icm_inverting_port_none`·`icm_inverting_port_ambiguous`·`icm_inverting_port_unresolved`, `icm_config_differential_output_structure`·`icm_config_differential_output_undeclared`·`icm_config_feedback_no_dc`·`icm_config_feedback_element_unsupported`·`icm_config_feedback_outputs_split`·`icm_config_feedback_cut`, `_dc_feedback_reaches`, `icm_view_ambiguous`·`icm_excite_common_mode`·`input_window_f_component_undeclared`·`INPUT_STATUS_F_COMPONENT_UNDECLARED`·`writer_head`·`icmr_view`·`icm_view` 식별자의 정의·참조 0; `icm_config` READS에 `device.element_class`·`device.dc_nets`·`device.unsupported`·`node.is_rail` 없음(블록 READS 단언); `kvl_sensitivity`에 `closure` 인자 없음(서명 단언) (g) **V_cm 칸 일치 단언**(계획 (8)(g), U-106): (a)·(b) toy에서 `graph.icm_config`의 `vcm_lo`·`vcm_hi`가 같은 끝 상태의 입력 포트 전압 평균(test 손계산)과 일치, `vcm0` = 봉인점 입력 포트 전압 평균; 포트 감도가 모두 양수인 toy에서 `node.dc_window_cfg` 포트 끝(lo끼리·hi끼리)의 평균과도 일치; **감도 음수 포트 toy 하나**에서 P2 [min, max] 정렬 뒤에도 V_cm 칸이 손계산 끝 상태 평균과 일치(포트 창 lo·hi를 짝지어 평균한 값이면 red) -- **전제 단언 둘**(어기면 그 사례 무효): (i) 그 toy에서 한 포트의 감도가 실제로 음수(손 감도로; 공개 `kvl_sensitivity` slope도 같은 부호) (ii) 짝지은 평균(lo끼리·hi끼리)과 손계산 끝 상태 평균의 차 > 비교 허용치; `metrics_aux` READS에 `("graph", "icm_config")` 있음(블록 READS 단언); **AST**(계획 '대상 함수 이름은 design' -- 이 design이 정함, 4.7-5 789): `icm_window_metrics`(`E/metrics/icm_window.py`)와 `metrics_aux._icm_ports`의 소스에 `lo`·`hi` 속성을 피연산자로 쓰는 산술(`BinOp`, `sum`·`min`·`max`·`statistics.mean` 호출 인자) 0(포트 창에서 V_cm을 다시 내는 둘째 생산자 금지; red 변형 하나 -- 그 함수에 `(p.lo + q.lo) / 2`를 넣으면 검사 FAIL); 기본 뷰 toy에서 `vcm_lo`·`vcm_hi` = x0 + Δ끝(손계산); 레일이 끝 상태를 자르는 toy(한 포트가 먼저 레일에 닿음) -- 두 포트 끝과 V_cm 끝이 같은 끝 상태에서 나옴(4.7-3b 계산 (4) (v), 손계산). (h) **전도 행 단언**(계획 v6.36 완료 조건 (8)(h), 사용자 결정 O-118 2번): nmcnr형 이름 없는 toy(입력쌍 한쪽 전류가 꼬리 전류 − 다른 쪽 전류로 KCL이 정하는 '차' 전류이고 servo 훑기 중 그 소자 차단이 끝을 정하는 꼴) -- **전제 단언**(어기면 그 사례 무효): 손계산에서 차단 끝(전도 행 영 교차)이 모든 포화 행 끝보다 먼저(차단 끝 < 포화 끝); `node.dc_window_cfg` 끝 = 손계산 전도 행 끝(I0 + k·Δ = `device.dc_conduction_floor`) -- oracle = 손 기대: k는 (a)와 같은 손 조립 KCL servo 감도와 `device.ss_dev` gm·gds·gmb로, I0는 `device.dc_op.current`, 하한은 `device.dc_conduction_floor` 읽기(피검 `_conduction_rows`·`saturation_window`·`kvl_sensitivity`를 부르지 않음; 비교 허용 = (a)와 같은 규칙); 전도 행이 없어 포화 경계까지 간 끝이면 red; 약반전 꼬리 toy의 과보수(SPICE보다 좁음)는 단언하지 않고 기록만(백로그 I-H3); **AST 단언 둘**(둘째 커밋, gap S-1 -- 계획 완료 조건 (9)(S4-나)(c)의 (i)·(iii)을 `_conduction_rows`와 그것이 부르는 IT-2 모듈 함수에 적용, docstring·주석 제외): (i) VGS 인자가 상수 0인 `op_point` 호출 0 (iii) EO-1 모듈 import 0(이름은 EO-1 design); (ii) `device.dc_conduction_floor`는 READS 읽기만 허용; 행 `kind` 집합 -- `_conduction_rows` = {`"conduction"`}, `region_rows` = {`"sat"`, `"triode"`}(D (b)).
- L10(계획 v6.35 완료 조건 (10)(b)(c)(d) + design 항목 (f)~(l); 옛 (a)(e)(i)는 v1.14.0 삭제 표지): (a) **삭제**(계획 v6.35 완료 조건 (10): 동적 측정 (ii)·양성 대조는 전제(S-3 정의 불능 규칙) 소멸로 삭제, 정적 가드 (i)은 card TN-1 완료 조건 (3)으로 옮김 -- 계획 N6.26, 이 design은 인용만) (b) `git grep` writer 하나씩 -- `node.dc_window` = `dc_columns`, `node.dc_window_cfg` = `icm_config`(완료 조건 (2)와의 정합 -- 사용자 결정 O-61 P2: 창 끝 함수 `saturation_window` 하나·부르는 자리 둘, M2) (c) `conductance_matrix(ss.circuit` 자리 = `ss_nodal` 하나, 같은 입력 버전에서 `ss_nodal` `computes` 증분 0(G-10)·WP-10 중복 인자 0, `icm_config`·`metrics_aux` READS에 `("graph", "ss_nodal")`; **E(`NodalSystem.g_bound`) 생산 자리 하나**(계획 (10)(c) -- v6.34 O-107): `conductance_matrix(…, bound=True)` 호출 자리 = `ss_nodal` 하나, E를 만드는 둘째 자리 0(다른 회로·뷰의 G를 조립하는 기존 `conductance_matrix` 소비자 `block_model`·`ff_gm_ratio`는 `bound` 없이 불러 대상 밖; `git grep`·AST); **봉인점 소신호 회로 필드 `graph.ss_circuit`**(계획 v6.34.1 완료 조건 (10)(c), 다섯째 커밋): writer 1곳(`ss_circuit`), `metrics_ss`·`metrics_aux`·`ss_nodal` READS에 `("graph", "ss_circuit")` 단언, **비test 엔진 소스에서 `ss_circuit(` 호출 자리 = writer 블록 하나·`SsCircuit(` 생성 자리 = `ss_circuit` 함수 하나(`git grep`)**(정의 줄 `def ss_circuit(`은 빼고 호출만 센다 -- gap N-3)(`ss_metrics.py`·`metrics_aux.py`의 조립 사본 0), 같은 입력 버전 재계산 0(G-10 계수 -- L11 (c)); **결측 toy 둘**(계획 재검증 S-1): (ⅰ) 저항 결측 toy(값 없는 저항 하나) → `graph.ss_nodal` 값 = `Undefined("ss_nodal", "passive_value_undeclared", "definitional", (("elements", (그 저항,)),))`(노달 계 없음)·`icm_config` `config is None`·`IcmConfig.undefined` code = `passive_value_undeclared`·`node.dc_window_cfg` 항목 없음(세우면 red, 새 code 이름 0 -- `CODE_PASSIVE_MISSING` 정의 1곳 `ss_circuit.py`, `git grep`) (ⅱ) 용량만 결측 toy(값 없는 커패시터 하나, 저항 값 있음) → `graph.ss_nodal` 값이 `NodalSystem`이고 그 점의 `node.dc_window_cfg`가 있음(없거나 정의 불능이면 red); metric 결과는 단언하지 않는다(지금 `metrics_aux`·`metrics_ss`가 결측 전체를 막음 -- 백로그 B77, 계획 v6.34.1 다섯째 커밋) (ⅲ) 저항·용량 함께 결측 toy(재검증 3 N-C) → (ⅰ)과 같음(`Undefined` detail `("elements", (그 저항,))` -- 용량 이름은 들지 않음) (ⅳ) 술어 하나: `git grep` -- `def is_dc_conducting_passive` 1곳(`ss_circuit.py`), 부르는 자리 = `ss_circuit`·`ss_nodal`, `LOOP_CUT_KINDS[0]` 비교 0 (d) `kvl_sensitivity` 정의·호출 자리 하나(`git grep`) -- 측정 구성 감도 연립(KCL + servo 행)을 푸는 자리 하나(계획 (10)(d)), `icm_config`가 θ 감도(`writer_grad`·`_sensitivities`)를 부르는 자리 0(AST -- O-108), 모든 측정 구성 포트의 끝을 담는 칸 = `node.dc_window_cfg` 하나(`IcmConfig`에 `kvl` 칸 없음 -- 완료 조건 (5), O-61 P3·O-109 C1) (e) **삭제**(선언 되먹임 DC 망 대상 소멸, O-115; 선언 무시는 L8 (d)) (f) `NodalSystem`의 `g`·`g_bound`·`factor` 모든 ndarray `flags.writeable is False`·제자리 쓰기 `ValueError`(red 먼저 -- 4.7-3b W4); **지문**: `g`가 같고 `g_bound`만 다른 두 `NodalSystem`의 `fp_of` 값이 다름(같으면 red -- 계획 v6.34 N3.8 'E는 `__canonical__`에 든다') (g) `as_is_single_input` toy(단일 입력, 고임피던스 출력)에서 `node.dc_window_cfg` 항목 있음, 끝 = `graph.ss_nodal` 위 구동 = 입력 포트 감도(`kvl_sensitivity`, servo None)를 `slope`로 넘긴 `saturation_window` 끝(손계산), 커널·front metric = `icm_window_metrics(node.dc_window_cfg)`, `metrics_aux` READS에 `("node", "dc_window")` 없음(base는 cfg 없음 -- red; v1.12.1 W1 철회). (h) 구성 None toy -- 세 metric `undefined` 원소의 quantity가 칸 이름(`icmr_v`·`icm_margin_v`·`required_input_cm_v`)이고 `metric_value`가 `unrecorded_cause`를 내지 않음(M7). (i) **삭제**(DC 되먹임 판정·절단 넷 순수 함수 분리가 IT-2c에서 빠짐: 판정은 엔진 구현 없음(계획 N3.8 '선언 되먹임의 DC 되먹임 판정 -- 슬루 측정 구성 전용'), 순수 함수 분리·`_input_side` 대체·동작 동일성 test는 card TN-1(계획 N6.26 완료 조건 (1)(2)); 부재 단언은 L8 (f)) (j) **스탬프 연산 수 c_s**(계획 N3.8 'c_s는 스탬프 함수 옆 한 자리, 스탬프 식 변경을 잡는 test'): `mos_stamps`·`two_terminal_stamps` 결과의 공개 반환값으로 판정(둘째 커밋): 스탬프 함수마다 `g_ops` 길이 = 그 함수가 낸 `g` 값 수, 연산을 가진 항목의 연산 수 > 0(셋째 커밋 R1 -- 값 부호가 아니라 연산 수; (d, s) 항목처럼 g 값은 음수일 수 있다); 단언 둘로 나눈다(다섯째 커밋, design 재검증 recheck2 N-1 -- 셋째 커밋 S-R1의 식 변경 감지 취지 그대로): **(j-ⅰ) AST 계수 = 손 기대** -- test가 두 스탬프 함수 소스에서 **스탬프 값 식 안의 수치 이항 연산(`BinOp`)만** 센다(문자열 `%` 서식 등 문자열 피연산자 연산은 뺀다); 그 계수가 test가 스탬프 식을 손으로 센 기대(MOS 2 -- `gm + gmb + gds`, 저항 1 -- `1.0 / ohm`)와 다르면 red(식에 연산이 더해지면 FAIL); **(j-ⅱ) 항목별 `g_ops` = 손 기대** -- MOS (d, s)·(s, s) 항목 = 2, 나머지 0(부호 반전 정확), 저항 항목 넷 = 1; 다르면 red(식은 그대로 두고 `g_ops`만 틀리면 FAIL); **길이 불일치 거부** = `StampSet.__post_init__`가 `len(g_ops) != len(g)`이면 `ValueError`(예: `StampSet(g=((0, 0, 1.0),), g_ops=())`)(공개 생성자로 직접 단언 -- 내부 이름 주입 없음, R2 범위 밖 주입을 두지 않는다). (k) **E 손계산**: 작은 toy(스탬프 항 수가 항목마다 다른 꼴)에서 `g_bound` = 손으로 센 k_ij·S_ij·c_s로 낸 4.7-3b 식 값(u = 2⁻⁵³; 기대값은 피검 함수 없이 계산). (l) **회로 조립 정본 하나·동치**(넷째 커밋, 다섯째 커밋 개정 -- 4.7-3b `graph.ss_circuit`; 관측 대상 = design 재검증 recheck2 N-2): (l-ⅰ) **`graph.ss_circuit` 값을 손 회로와 직접 비교** -- test 작성자가 손으로 만든 작은 회로(소자·넷 이름과 `dc_colour`를 정함)의 정준 순서(노드 = (`dc_colour`, 이름) 순, 소자 = (`dc_colour`, 이름) 순, 입력 노드 = 입력 포트, ac 접지 = `ac_ground_class` 있는 넷)를 기대값으로 적고, 블록 `ss_circuit_field`가 쓴 `graph.ss_circuit`(`SsCircuit`)의 노드·소자·입력·접지 순서가 그와 같음(기대값을 피검 함수 출력으로 만들지 않는다) (l-ⅱ) **`metrics_ss`·`metrics_aux` 결과 = base 대비 비트 동일**(같은 입력의 `graph.metrics_ss`·`graph.metrics_aux` `FieldValue.value_fp` -- base `6afe4758` 대 head) (l-ⅲ) **READS 단언**(design 재검증 recheck2 N-3): `ss_circuit_field` READS ⊇ 조립 열 열(4.7-3b `graph.ss_nodal` 문단), `ss_nodal` READS ⊇ {`graph.ss_circuit`, `device.kind`}(결측 저항 판정), `metrics_ss` READS ⊇ {`graph.ss_circuit`, `device.ss_dev`}, `metrics_aux` READS ⊇ {`graph.ss_circuit`, `device.ss_dev`, `device.dc_colour`}; `git grep` -- `def _ss_of` 0, `ss_circuit_of` 0(넷째 커밋 이름 -- 만들지 않음). 죽은 갈래는 test를 두지 않는다(R5 -- 4.7-2).
- L11(완료 조건 (11), 4.7-3c, 사용자 결정 O-61 P1): (a) parent에 봉인 4 호출 목록·base writer 밖 writer 필드(예: 봉인 뒤 블록 `icm_config`의 `node.dc_window_cfg` -- v1.13.0, 옛 예 `dc_window_refine`은 O-109 C1로 없음)를 실은 픽스처 → child 스냅샷 커밋에 그 필드 없음; base writer 필드(S1·S1v·계획·S0 탐색·metrics S0 -- `ctx.base.block_versions`에 있는 writer)는 child에 남음(지우면 red); parent 없는 평가(스냅샷 = `ctx.base`)가 봉인 4를 통과함(keep을 옛 `_CONTEXT_WRITERS`로 구현하면 red); base writer 버전이 `ctx.base`와 다른 parent는 `ValueError`로 거부 (b) 봉인 4 위반 픽스처 둘 -- base writer ∪ 호출 블록 밖 writer 필드 → `SEAL_FAIL`·detail `foreign_writers`, base writer ∩ 호출 블록 ≠ ∅ → `SEAL_FAIL`·detail `base_call_overlap`(둘 다 통과면 red -- 게이트가 실제로 거부함을 먼저 확인) (c) 같은 θ ss 재평가 → ss 블록 outcome `graft`, `computes` 증분 0(다섯째 커밋: 새 블록 `ss_circuit` 포함 -- 블록마다 (computes, grafts, reuses) = (0, 1, 0); 커널 `size_and_seal` 계수 reuse 12·graft 1(757)은 DC 단계라 불변) (d) (사용자 결정 O-94 (2)) 같은 θ parent 재평가 → 봉인 항목 블록 여덟은 child에 남아 outcome `reuse`(keep을 커널 블록만으로 구현하면 `graft` -- red), `dc_seal_report`는 `graft`(keep에 넣으면 봉인 4 `foreign_writers` -- red), `computes` 증분 0; `seal_versions(snapshot, calls, None)`·`seal_dc(…, base=None)`·`seal_dc`에서 `base` 생략 → `TypeError`(건너뛰어 pass면 red -- 계획 v6.31 (11)(d)) (e) (계획 v6.32 완료 조건 (11)(e), 사용자 결정 O-96 -- card IT-2e, 4.7-3c '실패 평가의 부분 스냅샷 파생') parent가 있는 평가에서 블록 k(커널 블록(steps·later 구성원) 각각 -- 구성은 IT-2d 병합 head 실측 -- 와 봉인 항목 블록 각각 -- 구성 = `SEAL_ITEM_BLOCKS` 상수를 걷는다; 후보 실패 주입, 주입 자리는 바꾸지 않음)가 실패하면 부분 스냅샷(`EvalResult.partial`)의 `block_versions` 키 = base writer ∪ k 앞 블록, 필드 writer ⊆ base writer ∪ k 앞 블록이고 k와 그 뒤 블록이 없음(parent 값이 남으면 red). **사례 유효 조건 둘**(어기면 그 사례는 무효이고 통과로 세지 않음): (가) 주입한 θ에서 블록 k가 reuse되지도 graft되지도 않고 실제로 실패한다(parent reuse·같은 실행 S3 색인 graft 모두 아님 -- 부분 스냅샷이 없거나 k가 실패 블록이 아니면 그 사례는 무효). **(가)의 관측**(검증 S-4·gap G4): parent 경로 사례에서 블록 k에 들어간 스냅샷으로 잰 `k.input_version(snapshot, *extras)` ≠ parent 스냅샷의 `block_version(k.name)`(reuse 아님), 그 실행 색인의 `donors.find(k.name, "*", 그 입력 버전)`이 None(graft 아님), 그 실행 색인의 `donors.find_failure(k.name, "*", 그 입력 버전)`이 None(재연 아님 -- 계획 '실제로 실패'의 해석, 계획보다 엄격한 쪽이라 원래 취지와 다르지 않음; 재검증 S-R3: 옛 '`replays` 증분 0'은 `__call__`을 감싸는 주입에서 늘 0이라 아무것도 거르지 않아 바꿈) -- part `"*"`는 엔진 비공개 상수 `_PART`(`E/core/compute_block.py:99`)라 test는 리터럴 `"*"`로 쓴다(N-R2) (나) 대조 평가 = **새 `open_run()` 쌍으로 `build_kernel_context`한 별도 커널 컨텍스트에서 `size_and_seal`을 직접 호출**(parent 없이 같은 θ·같은 주입; 재검증 S-R2 -- 한 갈래) -- 계획 (나)('`size_and_seal` 직접 호출 또는 별도 커널 컨텍스트')보다 엄격하다: 평가 키 캐시와 블록 결과 색인(graft·재연)을 모두 parent 경로와 공유하지 않아 대조가 parent 경로에 기대지 않게 하기 위함; 대조 결과가 parent 경로 결과와 같은 캐시 객체가 아님을 확인한다. **재연 경로 선택 사례 1건**(S-R3 -- 4.7-3c '재연 예외도 같은 부착 자리에서 줄여서 붙는다'를 판정): 같은 커널 컨텍스트(같은 실행 쌍)에서 두 평가 모두 `size_and_seal(ctx, θ, parent=…)`을 직접 부른다 -- 먼저 parent 없이 블록 k를 실패시켜 실패를 색인에 기록하고, 이어 parent 경로 평가로 블록 k를 재연(`from_record`)시킨 뒤, 부분 스냅샷 축소(`block_versions` 키 = base writer ∪ k 앞 블록)와 fp가 계산 경로 사례와 같은지 본다(search `evaluate`로 부르지 않는다 -- 평가 키 캐시가 parent를 키에 넣지 않아 둘째 평가가 첫 결과 객체를 받아 사례가 공허하게 통과한다; 재검증 S-Q1). **이 사례의 유효 조건**: 블록 k의 `replays` 증분 = +1(재연임 -- 어기면 그 사례는 무효, N-Q1). 실패 주입 = 블록 인스턴스 `fn` 교체 또는 실제로 실패하는 θ(실패가 색인에 등록돼야 하므로 블록 계산 경로에서 나야 한다 -- `__call__`을 감싸는 주입으로는 재연이 생기지 않는다), 주입 예외는 `InfeasibleSizingError` 하위 클래스(결정적 도메인 실패만 색인에 등록됨 -- `E/core/compute_block.py:160`); 위 (가)의 '재연 아님' 조건은 이 사례에 적용하지 않는다. **판정 = 변성 관계**(기대값은 축소가 no-op인 parent 없는 경로에서 나온다): 부분 스냅샷 fp = 대조 평가의 부분 스냅샷 fp이고 S3 evals 실패 줄 `snapshot_fp`도 그 fp; 봉인 위반 + parent 한 건에서 부분 스냅샷에 `dc_seal_report` 필드가 남고(지우면 red) fp가 같은 조건 (가)(나)의 대조 평가와 같음. `writers_in_scope(None, …)` → `TypeError`(건너뛰어 집합을 내면 red -- gap G2·검증 N-2). **재구현 0(AST 검사, 측정 정의 = 계획 N3.3, 세는 연산 = 4.7-3c 'AST 검사가 세는 것')**: 한 식 트리(합집합·차집합 연산 사슬)의 피연산자에 base writer 집합(출처 = 스냅샷 `block_versions` -- 변수 대입을 거쳐도 추적)과 블록 이름 집합이 함께 나타나는 식(coverage 연쇄 꼴 `(used − base) − called` 포함)의 정의 자리 = `writers_in_scope` 하나, 그 함수를 부르는 자리 = 파생 keep(`run_kernel`)·봉인 4 coverage(`seal_versions`)·실패 부착(`_call_block`·`seal_dc`), 그 밖 0(서로소 단언·parent 일치 검사의 base writer 단독 읽기는 대상 아님); 검사가 실제로 거부함을 보이는 red 변형 둘(넣으면 검사 FAIL -- 계획 N3.3의 (가)(나)): 정의 자리 밖에 연쇄 꼴 `(필드 writer − base writer) − 호출 블록 이름`을 쓴 식, `block_versions`에서 얻은 base writer 집합을 변수에 담았다가 그 변수와 블록 이름 집합을 합집합하는 식. parent 없는 기존 부분 스냅샷 test(`E/tests/search/test_kernel.py` B-T19·B-T20) 불변, reuse·graft·compute 계수 변화 0(G-10). 바뀐 실패 줄 수는 감사가 base↔head 같은 입력 실행의 evals 실패 줄 `snapshot_fp` 차이로 변화표에서 센다; NFR-4 덤프(`tests/integration/nfr4_run_dump.py`가 evals 줄을 걷는다) 기준선을 바꿔야 하면 그 갱신은 작성자가 아닌 주체가 변화표 근거로 한다.
- L12(계획 v6.36 완료 조건 (12), 사용자 결정 O-61 P3~P5·O-109 C1·D2; (a)는 대상 소멸(4.7-V, O-61 P5 대상 소멸 -- 계획 E-13 표지), 그 자리 toy = 'y 범위 = 순서 창' toy(§9 v1.15.2 행)): (a) 커널 되풀이 `k_max` 소진 toy·tol 미정 toy(4.7-3 1 A6 b·c; **`k_max` 소진 toy에만 전제 단언: 그 점이 봉인을 통과함** -- 봉인되지 않으면 측정 구성 블록이 돌지 않아 아래 cfg 단언이 공허하므로 그 사례는 무효, 계획 재검증 N-5; tol 미정 toy는 봉인 통과가 불가능해 이 전제를 걸지 않고 커널 단언만 진다 -- 여섯째 커밋, gap N-1) -- 두 toy 모두 `node.dc_window` 뿌리 `input_status == "unsettled"`(사유 기록)이고 W4 y 범위로 그대로 쓰임(base는 수렴 표시 없이 마지막 창 값을 냄 -- red); **`k_max` 소진 toy에서 측정 구성 판정 창과 그 창을 읽는 세 metric·커널 ICMR 선언 제약은 미수렴 때문에 정의 불능이 되지 않음**(tol 미정 toy는 cfg 단언 **대상 없음** -- 그 점은 tol_V 미정 행이 undefined라서 봉인되지 않아(`sealed=None` -- fail과 다른 상태) 측정 구성 블록이 돌지 않는다, 죽은 갈래라 cfg test 없음; 커널 상태 `"unsettled"`·`tol_v is None`만 단언 -- 둘째 커밋, 계획 v6.34.1 (12)(a)와 같은 문언)(`node.dc_window_cfg` 항목 `input_status == "measured"`, 세 metric 값 있음 -- 이어받으면 red, v6.34 O-109 D2, **원래 취지와 다름**); **`k_max` 소진 toy의 주입 지점**(자연 toy는 창 끝의 y 의존이 2차라 수렴이 빨라 재현성 있게 만들기 어려움, R2 선례와 같은 수단): `gmid_engine.sizing.block_columns.k_max`(상한 1)만 허용(4.7-4 '모듈 수준 이름' 커널 쪽) -- 주입은 상한값만 바꾸고 검사 동작(소진 → `"unsettled"`)은 같으며, 전제 단언으로 `_solve_input_window`의 소진 분기 도달을 보인다; test 전제 단언 -- 요청 y ≠ 1/2, y = 1/2 풀이 성공(같은 이름을 읽는 `_interior_solution`에 들어가지 않음; 자기참조 bisection의 `SccLog.k_max` 칸도 같은 이름을 읽으므로(`_solve`가 `block_columns.py`에 남음 -- 4.7-4) 그 칸을 단언하지 않거나 자기참조 노드 없는 toy), 첫 회 창과 둘째 측정 창의 차 > tol(손계산); 기대 = 뿌리 `lo`·`hi` = 마지막으로 잰 창 ∩ 순서 창, V(뿌리) = lo + y(hi − lo); **tol 미정 toy**(A6 b) = 4.7-3 1 'A6 b 도달 조건'의 LUT 구성(VDSAT 열 출처 = 기준 LUT, 슬라이스 id_equivalent 셀 미정)과 비순환 쓰기 계획(`graph.dc_scc_order`로 전제 단언) -- 실패 예외의 `partial`로 읽지 않고 `dc_columns`까지 부른 스냅샷(test conftest `run_blocks(…, upto="columns")`)에서 본다; 선언 `icm_margin_v` 제약을 단 `k_max` 소진 toy(같은 주입)의 외층 실행에서 그 점이 미수렴 때문에 최종 `front`에서 빠지지 않음(옛 '미수렴 front 제외'는 대상 없음 -- 4.7-5) (b) **F 성분 입력 DC 미선언 포트 library toy**(계획 v6.36 완료 조건 (12)(b), O-118 3번 -- 입력 = MOS gate 전용 넷·source = gnd, `E/tests/sizing/test_block_columns.py` 꼴(회로 C -- 단일 입력이라 `config == "as_is_single_input"`)과 같은 연결의 2입력 변형(한 입력이 F 성분 포트, `config == "servo"`)): 그 포트를 함께 구동한 `node.dc_window_cfg` 창이 KCL 손계산과 일치(정의 불능·구동 제외·봉인점 고정이면 red; 2입력 변형에서 그 포트만 자기 x로 훑은 창이면 red), 커널 θ 프레임 창 `node.dc_window`에 그 포트 항목이 없음(있으면 red -- D1), cfg 상태·metric code에 `f_component_undeclared`가 나오면 red (c) **모든 측정 구성 toy** -- servo(단일 출력 고임피던스 L8 (a)·차동 출력 L8 (b)·KVL 고정 출력 L8 (c)·선언 무시 L8 (d), v1.14.0 O-115)·단일 입력 '회로 그대로'(사용자 결정 O-63 (4) -- L10 (g)와 같은 연결) -- 각 끝이 `node.dc_window_cfg`에만 있고(`IcmConfig`에 `kvl` 칸 없음) front·보고 `icm_margin_v` = `icm_window_metrics`(`graph.icm_config` V_cm 칸·그 포트의 `node.dc_window_cfg` 항목) 값('추정' 표기; front가 다른 칸·블록에서 값을 내면 red -- O-109 C1) (d) `icm_config` 블록 READS에 `("node", "dc_window")`가 없음(블록 READS 단언 -- 계획 (12)(d), O-109 D2) (e) **커널 y 끝점 기대**(사용자 결정 O-103, 4.7-8 (8)): 영향받는 기존 test 둘 = `test_off_mid_window_maps_y_and_ends_saturated`(y = 0·1)·`test_mid_window_ends_have_nonnegative_saturation_slack`. 내부 y(0 < y < 1)는 기존 단언 그대로(봉인 7 pass, 독립 여유 ≥ −1e-12 -- `test_input_window.py`(`it2b-test` `88335ef6`), master `52b9dd81` `:278`·`:288`); 끝점 y는 '봉인되거나(그러면 기존 단언 그대로), 봉인 7 거부이면서 \|slack\| ≤ tol_V' -- slack = 봉인 7 기록의 `slack_v`, tol_V = 그 점 뿌리 항목의 `node.dc_window.tol_v`(graph 필드; None이면 그 사례는 무효이고 통과로 세지 않음); 상한 tol_V는 사용자 결정 O-103 값(유도는 B70); **거부 끝점은 엔진 `slack_v`만으로 닫지 않는다**(작성자≠검증자) -- 같은 점에서 기존 test의 독립 oracle 여유(`_oracle_slacks`)도 \|여유\| ≤ `node.dc_window.tol_v`로 함께 단언한다(둘 다 성립해야 통과). 기대 갱신은 test 작성 주체 몫. (f) **판정 tol 매 해**(v1.12.11 E-3, 4.7-8 (9)): 해마다 tol이 다른 toy에서 뿌리 `node.dc_window` `tol_v` = 마지막으로 잰 해의 tol_V 셀 최솟값(기대값은 공개 표 API `gmid_engine.lut.tol_v_table(memo, kind, w_key).at(L, VDS, "id_equivalent")`로 그 해의 소자마다 구해 최솟값 -- 피검 함수를 부르지 않음); 전제 단언 = 첫 해 tol ≠ 마지막 해 tol(같으면 그 사례는 무효; 첫 해 tol 하나로 판정·기록하면 red). 기대 작성은 test 작성 주체 몫.
- L13(계획 v6.34.2 완료 조건 (13), card IT-2d B77 -- 4.7-5 793; 사용자 결정 O-111·O-112·O-113): (a) **용량만 결측 toy**(전제 단언: `SsCircuit.missing` ≠ ∅이고 결측 소자가 모두 `is_dc_conducting_passive` 거짓; mismatch 입력 등을 주어 결측 밖 정의 불능 사유가 없게 함) -- 영역 `dc` metric(`icmr_v`·`icm_margin_v`·`required_input_cm_v`(`swing_icmr` 보고 칸, 확정 O-113)·`swing_out_v`·`offset_in_sigma_mv`·`offset_excess`·`offset_sys_mv`·`mirror_ratio_sigma_pct`)이 `passive_value_undeclared` 없이 정의되고 대조 실행(같은 θ·같은 봉인점에서 그 커패시터 값만 선언)의 값과 비트 동일; 영역 `ss` metric(`ff_gm_ratio`·`metrics_ss` 요청)만 `passive_value_undeclared`; 전달 뷰 보고(`block_residual`·`nqs_ratio`·`ls_fields`·FF) 없음, `swing_icmr`·`offset_contrib`·`mirror_ratio` 보고는 그 metric이 정의되면 있음(base는 DC metric도 정의 불능 -- red) (b) **저항 결측 toy** -- 영역 `dc`·`ss` metric 모두 `passive_value_undeclared`(DC metric이 정의되면 red), DC metric detail = `graph.ss_nodal` `Undefined`의 `("elements", 결측 저항)` (c) **분류 사본 0**: AST 대상 = `metrics_aux._missing_gate`(와 그것이 부르는 함수) -- 그 안에 metric 이름 목록·집합·문자열 비교로 결측 판정을 가르는 식 0(영역은 `signature.domain`에서만; `metrics_aux`의 기존 metric 이름 계산 분기는 대상 밖); 술어 `is_dc_conducting_passive` 정의 1곳·호출 자리 = `ss_circuit`(스탬프 가르기)·`ss_nodal`(결측 판정) 둘, `metrics_aux` 호출 0(`git grep`); `metrics_aux` READS에 `graph.ss_nodal`·`graph.ss_circuit`(블록 READS 단언); registry 영역 칸을 metric 이름으로 단언 -- `offset_in_sigma_mv`·`offset_excess`·`offset_sys_mv`·`mirror_ratio_sigma_pct`·`swing_out_v`·`icmr_v`·`icm_margin_v` = `"dc"`, `ff_gm_ratio` = `"ss"`(base red는 base에서 `dc`가 아닌 행만 -- VB-1이 먼저 병합되었으면 `offset_sys_mv` 행은 red 대상에서 뺌) (d) **새 code 0**: 결측 정의 불능 code는 `passive_value_undeclared`뿐(비test 엔진 소스 `git grep` 새 code 상수 0).

**4.7-8 변경 종류·판정 다리**(계획 N6.3 (i)~(iv), O-34 (1)): IT-1·IT-2 모두 **동작 변경**(IT-1 = 입력 DC 미선언 회로의 쓰기 계획·θ y·결과, IT-2 = 입력 DC 선언 회로에 창이 생기고 metric 값의 출처가 바뀜. 무동작 입력 -- IT-1의 선언 2회로 쓰기 계획 -- 은 순수 리팩터링 필드별). 다리 넷: 정의 오라클 toy(4.7-1·4.7-7), 봉인 불변식, SPICE oracle 대조(**보류** -- 채울 card EO-1, 그 뒤 꺼짐 정의 판에 따라 OP-5), 검증자 변화표(9회로, IT-Q3 (가) -- IT-0 기록 대비). 결정성 비트 동일. 두 card는 각자 test·code 커밋을 갖고 **하나의 통합 병합**으로 들어간다(O-19 (2) -- IT-1만 병합된 기간 없음). 바뀌는 metric 동작(변화표 원인 칸에 쓴다): (1) 입력 창 출처가 경로 합 → 측정 구성 판정 창(봉인점 KCL 선형 감도 끝, v1.13.0), 세 metric 좌표가 포트 전압(as-built: 첫 포트 margin·포트 창 교집합 폭) → V_cm(U-106 -- v1.14.1 정정, gap S-4) (2) 측정 구성 창 측정 실패 점(`"unmeasured"`)의 세 metric이 정의 불능(as-built는 값을 냈다; F 성분 미선언 포트는 v1.14.1에서 정의됨 -- 아래 (7) (vi)) -- 커널 θ 프레임 되풀이 미수렴 점은 정의 불능이 되지 않는다(O-109 D2 -- v1.12.11 설계 대비 변화, 원인 칸 = O-109 D2) (3) **입력 포트가 없는 회로의 `swing_out_v`**: as-built `ls_swing`은 `no_input_port`면 세 metric 모두 정의 불능으로 냈다(`ls_swing.py:87-88`) -- 이제 스윙은 출력만 보고 풀리고, 입력 세 metric(ICMR)만 정의 불능이다(v1.14.1 code = `icm_config`의 `view_required` -- 입력 포트 0이면 기본 포트 뷰를 만들 수 없음; 옛 `no_input_port` 갈래는 도달 0이라 두지 않음). **기준선 둘**(v1.12.3 N-2): 검증자 변화표의 원인 칸은 as-built(IT-0 기록) 대비로 적는다. 아래 (4)~(7)·(10)·(11)은 as-built 대비 원인과, design 판 사이 차이(구현 전이라 변화표가 아니라 design 기록)를 함께 적는다. (4) **모든 측정 구성 포트의 front·보고 값 출처** = `node.dc_window_cfg`('추정' KCL 선형 감도 끝 -- 사용자 결정 O-63 (4)·v6.34 O-109 C1, 계획 완료 조건 (3)(i′)·(6)) -- as-built: `ls_swing` 경로 합 창; v1.12.11 설계: 다듬은 창(끝 풀이)이 있는 포트는 그 값, 원인 칸 = O-109 C1 (5) **고임피던스 follower 포트의 측정 구성 감도 θ 고정 연립 → KCL**(v6.34 사용자 결정 O-108, 계획 완료 조건 (3)(i)·(6)) -- 측정된 넷 `two_stage_ota`·`two_stage_ota_sf`·`folded_cascode`·`ngcc_3stage_ff`(층 0 시작점이 없어 미측정인 `sf_pushpull_output_opamp`은 착수 때 재측정)의 세 metric 커널 값; 설계 단계 실측 창 끝 차 2~69 mV(`it2c_circuit_access.md` 1.2), 원인 칸 = O-108 (6) **스냅샷 지문 변화**(계획 v6.34 셋째 커밋 완료 조건 (6), 재검증 N-6 -- O-34 분류): D1로 `node.dc_window` 값에서 뿌리 아닌 포트·선언 포트·F 성분 포트 항목이 빠져 `dc_columns` 출력 지문이 바뀌고, D4로 S0 필드 `node.dc_output_structure`가 없어져 base writer(쓰기 계획) 출력 지문이 바뀐다 -- 둘 다 지문 = 동작 변경, 원인 칸 = O-109 D1·D4 (옛 (6) '출력 구조 분류로 고르는 측정 구성 창 갈래'(O-64 (1))는 v1.13.0에서 대상 없음 -- 4.7-1a 기록) (7) **ICMR 측정 구성 → servo, 좌표 → V_cm**(사용자 결정 O-115·U-106(O-116), 계획 완료 조건 (3)(iii)·(6)): 2입력 회로의 세 metric 값(구성 follower·선언 되먹임 → servo -- 분석 실측 봉인점 기준 끝 차 수 mV~0.9 V, `icmr_definition_review.md` §4.2)과 좌표(포트 전압 → V_cm -- 입력 하나인 회로는 값 변화 0), 정의 불능 갈래 교체(반전 입력 셋·S-OS2·선언 되먹임 code → 4.7-3b 744), 원인 칸 = O-115·U-106; v1.13.0 설계의 멈춤 S-OS2 갈래는 소멸(as-built 대비로는 차동 출력 2입력 회로에도 servo 값이 생김); v1.14.1 추가(계획 v6.36 완료 조건 (3)(iv)~(vi)·(6), 원인 칸 = O-118): (iv) 전도 행 R0로 바뀌는 창 끝(nmcnr·ngcc 등 차단이 끝을 정하는 회로 -- 원인 O-118 2번) (v) 기본 포트 뷰를 S1v에 늘 두는 출력 규칙과 식별 칸 `default_port`로 바뀌는 S1v 값 지문·소비자 입력 버전(소비자 값 변화 기대 0 -- 착수 실측 (d), 원인 O-118 6번) (vi) F 성분 미선언 포트를 함께 구동해 정의되는 창(옛 정의 불능 -- 원인 O-118 3번); v1.14.0의 `DcInputs.icm_view` 지문 변화(검증 N-2: `context_fp`에 `DcInputs` 전체가 든다 -- `E/search/search_context.py:206`)는 그 칸을 지워 대상 없음; **U-104**(gap N-1 -- 계획 N7.2 U-104, 확정 O-116, 시점 'IT-2c 변화표 작성 전'): spec ICMR 값 출처 표기는 기존 `source.record`에 문구를 덧붙이는 data 커밋(사용자 승인 뒤, 후속 정정 표 'spec 출처 문언')이고, nmcnr `icmr_v >= 0.5`는 **사용자 지정 ICMR 최소 요구**다(계획 v6.37 U-104 (3), 사용자 결정 O-119 정정 1·2 -- 원문 값이 아니라 원문 follower 0.5 V 계단에서 사용자가 정한 servo `icmr_v`(계획 N3.8 '입력 범위 세 양' (1))의 최소치; servo ICMR과 **같은 양**, 출처 = 사용자 설정값, 값 0.5 유지): `source.record`에 덧붙일 표기 = '사용자 지정 ICMR 최소 요구(원문 follower 0.5 V 계단에서 사용자가 정함, 원문 값 아님) -- servo ICMR(gain-budget v6.37 N3.8 입력 범위 (1))과 같은 양'이다(옛 '다른 양 -- follower 계단 조건 → 증폭기 고유 입력 범위' 문언은 계획 v6.37로 대체 -- 같은 양이라 변화표 원인 칸의 '뜻 변화' 항목은 대상 없음; 이 design은 인용만) (8) **커널 W4 입력 뿌리 y 끝**(사용자 결정 O-103 -- O-102 대체; **원래 취지와 다름(작음)**): IT-2b부터 커널 y 범위 끝은 끝 풀이로 다듬은 끝이 아니라 A6 선형 끝이다(4.7-3 1, O-33 (3)). 창 끝은 봉인 7 여유가 0인 경계에 놓이므로 θ y = 0·1 끝점은 봉인 7이 거부할 수 있다 -- 끝을 다듬던 옛 경로도 부동소수점 오차급(−7.9e-12 V, 1e-11급)으로 거부했고 '모든 y 봉인'은 옛 경로에서도 보장되지 않았다(common_gate y = 1, head·base 모두 6점 중 5점 거부, slack −7.95e-12 V). IT-2b가 더하는 것은 선형 외삽의 곡률 오차(two_stage_ota_sf y = 0, 6/6점, −6.55e-6 V)와 common_gate y = 0(6/6점, −4.8e-13 ~ −3.6e-12 V; base는 둘 다 봉인)이다. **같은 범위의 사례 추가**(백로그 E-4 -- IT-2b 감사 판정 기록 `wt/integ-it12/.ai/verification/20261021-it2b-kernel-window.json` V9(판정 커밋 `5221c8b2`)): two_stage_ota y = 1 끝점 head 6/12점 봉인 7 거부(\|slack_v\| ≤ 4.32e-6 V, 그 점 뿌리 `tol_v` 약 6.3e-3 V -- \|slack\| ≤ tol_V라 O-103 범위(선형 곡률)); 같은 감사의 common_gate는 11/12점(\|slack_v\| ≤ 7.95e-12 V), two_stage_ota_sf는 6/12점(y = 0, ≤ 6.55e-6 V -- 위와 같음), folded_cascode·nmcnr 12/12점 봉인. 9회로 탐색(eval_budget 40)의 y 끝점 방문은 head 0회·base 1회(base의 common_gate y = 1, 봉인됨 -- SLSQP가 y 상자 경계에 실제로 닿는다는 관측)이고, 봉인 7 실패 수는 9회로 모두 head = base(거부율 변화 0); head 0회는 탐색 궤적이 달라진 결과(common_gate 커널 호출 34 대 43)이지 구조적 보장이 아니며, 큰 예산·경계 최적점의 발생률은 미측정이다. **함께 바뀌는 값**(비트 동일 아님): 뿌리 `lo`·`hi`(다듬지 않은 끝 -- 예 common_gate src 4 vin hi head 1.6957364591335347, base 1.6957364591379647)와 그것을 읽는 θ y → V 사상, `fd_jacobian` y 스텝 값 -- card '무동작 판정 입력'에서 뺀다. 끝을 커널에서 다시 푸는 안은 끝 풀이를 어느 층에도 두지 않는 규칙(O-33 (3)·v6.34 O-109 C1)에 어긋나 두지 않고, A6 한쪽 수렴도 해결이 아니다(두 추정 모두 내부 해의 선형 끝이라 곡률 오차가 남는다). 봉인 7 경계 비교를 수치 분해능으로 하는 일은 백로그 B70(봉인 규칙 변경 -- 계획 몫). 측정 근거(head `85847b49`·base `53d50aea`) 두 파일 `wt/_drafts/evidence/2026-10-22/o103_yend/` -- `yends_9circuits_analyst.jsonl`(판정 agent, 9회로 탐색·끝점 재평가), `yends.jsonl`(오케스트레이터, 2회로 봉인점 6개 y 0·1 직접 재현); 끝점 test 기대는 4.7-7 L12 (e). (9) (대상 소멸 -- 커널 A6 되풀이 삭제, 4.7-V 2행; 옛 항목 = design 이력 H41-20) (9′) **지원 밖 원소 정지의 실패 블록 이름**(여섯째 커밋, gap N-6): `ss_circuit`의 `StructureUnresolvedError`가 이제 writer 블록 `ss_circuit`에서 난다(예외·detail·부분 스냅샷 같음) -- 실패 줄의 블록 이름 `metrics_ss` → `ss_circuit`, 원인 칸 = 계획 v6.34.1 `graph.ss_circuit` 신설 (10) **servo 피벗 a_e의 resolution 칸 값**(E 항 포함 -- O-107; v6.35 대상 T_p → a_e, 계획 완료 조건 (3)(ii)·(6)): 판정 변화가 있으면 그 점을 원인과 함께(운영 판정 변화 0 기대 -- T_p 기준 근거 문서 운영 8회로 14포트 실측, a_e 기준은 IT-2c 착수 실측), 원인 칸 = O-107 (11) **커널 θ 프레임 창 미수렴 표시**(O-61 P5)는 동작 변경이고 card 0(IT-0)이 library 9회로에서 발동률(되풀이 미수렴·tol 미정 평가 수 / 평가 수)을 IT-2 착수 전에 재고 기록한다(계획 완료 조건 (6); 옛 'front가 빈 회로 수'는 이어받기 삭제로 대상 없음) (12) **B77**(card IT-2d, 계획 v6.34.2 O-111·O-112 -- 4.7-5 793): 용량만 결측 점의 영역 `dc` metric 정의 불능 → 정의됨, registry 영역 칸 표기 변경; 원인 칸은 'B77'과 '`ls_swing` 삭제·cfg 배선'으로 나눔(계획 검증 N-5). 순서: 선행 XRUN-F1 card B, 뒤에 headroom-chain HC-S(`sat_threshold`가 `region_rows`(옛 `saturation_rows`, IT-2c 뒤 `_helpers_dc_solve.Circuit`)를 고친다 -- **IT-1·IT-2 → HC-S**, headroom-chain v0.7.6), card DE-1, card ME-1(metric 코드를 바꾸는 card라 ME-1 모델 오차 측정은 IT-2 뒤, 계획 N6.19 선행). **(S4-나)이면 IT-1 + IT-2 → EO-1 → DE-1**(EO-1은 통합 병합 뒤 -- 4.7-3a 2 '갈래'; DE-1이 EO-1 뒤인 것은 오케스트레이터 기본안). **card IT-2e 변경 종류**(계획 v6.32 완료 조건 (11)(e), O-34): 지문(evals 실패 줄 `snapshot_fp` -- parent가 있는 커널 블록·봉인 항목 블록 단계 실패 줄) = 동작 변경, 지문 밖 결과 = 순수 리팩터링(필드별, NFR-4), 결정성 비트 동일; 동작 변경 칸의 SPICE 다리는 계획 N6.3 '대상 없음' (ii) -- 부분 스냅샷을 판정·재사용 입력으로 읽는 엔진 소비자 0의 `git grep` 증거를 판정 기록에 남긴다; 다리 = L11 (e) 변성 관계 test, 봉인 불변식(봉인 4 coverage가 같은 집합 함수), 검증자 변화표(바뀐 실패 줄 수).

**4.7-8a card 0 IT-0 결과 칸**(검증자가 채운다 -- 이 design 판에서는 '미측정'. 판정 기록 `.ai/verification/<IT-0 id>/`):

| 칸 | 내용 | 값 |
|---|---|---|
| M-I4 IT-Q2 판정 | 포트 쌍마다 \|V_p − V_q\| ≤ max(노드 tol_V) 여부 → (나)/(다) -- 계산 경로는 판정과 무관하게 하나(X-IT8) | 미측정 |
| s_p 부호 | 회로·입력 포트마다 측정 구성 판정 창의 dV_p/dx 부호(KCL 감도 -- 음수면 O-49 P2 [min, max] 규칙 발동; v1.13.0) | 미측정 |
| 커널 창 상태 발동 수 | (v1.15.2 대상 소멸 -- 4.7-V·계획 E-13: O-61 P5 커널 창 미수렴 표시 대상 소멸, 계획 표지) 회로마다 평가 중 커널 θ 프레임 창 `input_status` = `unmeasured`·`unsettled` 비율(계획 완료 조건 (6) -- 출력 전용 상태, metric 영향 없음 D2) | 미측정 |
| 다중 입력 뿌리·고립 입력 포트·F 성분 미선언 포트 | 4.7-1 4·5, 4.7-3 3 (나) 발동 회로 | 미측정 |
| front가 빈 회로 수 | **대상 없음**(미수렴 이어받기 삭제, 사용자 결정 O-109 D2; 계획 완료 조건 (6) '옛 front가 빈 회로 수 기록은 대상 없음') | -- |
| 차동 출력 servo·ICMR 전달 뷰 착수 실측 | 계획 v6.35 N6.6 IT-2c 착수 실측 (d)·'차동 출력 servo 착수 실측': ICMR 제약 4회로의 ICMR 전달 뷰 성립, `current_reuse_telescopic_ota` 봉인점의 servo 연립 특이 여부·\|a_e\| 판정(옛 '멈춤 S-OS2 발동' 칸은 S-OS2 폐지로 대상 없음, O-115) | 미측정 |

**4.7-9 범위 밖(card DE-1·FX-1 몫, 이 판에서 고치지 않음)과 보고 항목**:
- DE-1: 정의 창 `node.dc_window_def`(tol 없음·전도 끝 = 봉인 9 식, 훑기 점 I_off·ε)와 그 블록, 선언 제약 행의 다른 이름, ICMR 정의 = 계획 N3.8 'ICMR 측정 구성'(servo -- v6.35 O-115, 옛 O-25 (2) 대체)·일반형 O-33 (7)(전달 뷰 여기 방향 훑기), 선형 감도 연립 특이의 fail-closed(일반화된 끝점 블록의 결측 사유 기록 칸, 출력 창·방향 전류까지 같은 규칙), 출력 스윙(출력 꼴 무관, 출력 창 별도 필드), 계통 offset ΔV_out = −G⁻¹·ΔI, 방향별 공급 능력(정의 = 계획 DEC-65 v6.38(출력 포트를 선언 범위 끝 전압에 고정하고 입력을 끝까지 몬 DUT ⊕ 응용 망 DC 해의 순 전류, O-128 Q4), 엔진 계산 = DEC-104 R9(U-115 닫힘 O-143 (5) -- DE-1 착수 조건 (iii) 충족), 소비자 = DEC-104 R8 판정; 옛 소비자 피크 부하 전류 행·`load_peak_amp`는 O-143 (6)으로 삭제; as-built `ls_fields` β/σ/κ 고정 전류 가정은 DE-1 (d)가 R9로 고친다)와 엔진 슬루 몫 삭제(O-122 -- 40 §3.8-3), `ls_swing` 자체 제약계 삭제, 40 §3.8-3·§3.8-8 `swing_out_v`·`offset_sys_mv` 정의. **DE-1 인계(v1.12.2, v1.13.0 갱신 -- 계획 v6.34 N6.8 DE-1 (a)(b)·O-109 C2·C3, DEC-103)**: (1) **DE-1 (b) 출력 스윙 = KCL 선형 감도 끝, 출력 꼴 무관**(O-109 C3 -- **원래 취지와 다름, 승인 O-109**(O-43 D1 (a)를 고임피던스 출력으로 넓힘; 옛 '고임피던스 출력 = θ 고정 선형 감도 끝 + 다듬은 출력 창')): 계산 자리 = 이 card의 측정 구성 감도 연립 `kvl_sensitivity`(4.7-3b (3))를 구동만 차동 훑기·`servo` None으로 재사용(사본 금지 -- O-58 S-2), 다듬은 출력 창 없음(C1); 고임피던스/KVL 고정 구분·분류 필드 읽기 없음(D4 -- `node.dc_output_structure` 없음, 4.7-1a 기록; 13회로 출력 표(O-66 (1))는 회로 해석 기록이고 기준선이 아님) (1′) **DE-1 (a) 정의 창 = 같은 KCL 연립**(O-109 C2): 정의 창 `node.dc_window_def`는 이 블록이 같은 연립을 기준만 바꿔(tol 없음·전도 끝) 쓴다 -- θ 고정 끝점 손계산 블록 없음, 끝 풀이 없음 (2) DE-1 뒤 front·보고 값 출처 `node.dc_window_def`의 기준 표기는 그 필드 정의('정의 기준')에서 온다(`IcmWindow`에 `criterion`·`sources` 칸 없음) (3) 선언 제약 판정 = `node.dc_window_cfg`(4.7-2 'DE-1 전 한정', gap G2) (4) **미수렴 상태의 이어짐 -- 대상 없음**(O-109 D2): 정의 창도 커널 θ 프레임 상태를 이어받지 않는다 (5) **모든 측정 구성 포트**(O-63 (4)·O-109 C1)의 DE-1 뒤 정의 기준 값 = `icm_config`가 쓰는 `node.dc_window_def` 한 칸(계획 N3.8 -- 재계산 0) (6) **O-63 (1)**(DEC-23 'A_dc 정의 불능 갈래'가 'ΔW = 0 → 0'보다 먼저): IT-2는 A_dc·σ·V_id*를 계산하지 않는다(4.7-3b의 servo 피벗 a_e는 출력 전용 기록이고 그것으로 나누는 양이 없다 -- 감지 자리·e 가중이 DEC-23 A_dc와 같으면 DE-1 (c)가 `graph.icm_config` 피벗 칸을 정본으로 합치고(셋째 생산자 금지), 다르면 축을 적고 둘로 둔다 -- 계획 N3.8 'a_e와 DEC-23 A_dc의 축'; `icm_config`가 정의 불능이면 offset metric은 그 사유를 그대로 내고 DE-1 (c)는 offset 블록 READS에 `graph.icm_config`를 더한다 -- 계획 N3.8 '실행 조건'; a_e와 A_dc는 늘 같은 기본 포트 뷰(`ViewS1v.default_port`)라 I-H2 합치기가 무조건 성립(계획 v6.36 O-118 6번 'a_e와 DEC-23 A_dc의 축'), DEC-23 계산 일반형 (나′)(O-118 1번)·U-107(기준 도달 불가)·U-108(판정 자리)은 DE-1 (c) 몫이라 이 design은 인용만) -- 계통 offset(DE-1 (c))의 갈래 순서·판정 자리는 DE-1 design 몫이고 이 판은 설계하지 않는다 (7) **대상 없음**(S-OS2 폐지, card RB-1 대상 없음(계획 N3.8 'IT-2 후속'); 차동 출력 스윙은 DE-1 (b)가 같은 연립·servo None으로 잰다) (8) **판정 분해능 정의 함수의 이동**(v1.13.0 E 항): DE-1 (c)가 DEC-23 'A_dc 정의 불능 갈래'(O-63 (1) -- 갈래 먼저)에서 같은 정의를 쓸 때, `icm_config.py`의 비공개 `_transfer_resolution`(δV_out = \|z_u\|ᵀ(\|r\| + E\|v\|), E = `NodalSystem.g_bound` READS -- O-107)을 `E/metrics/_helpers_nodal.py`의 공개 함수로 옮기고 두 자리(a_e 판정·A_dc 판정)가 import한다(정의 하나 -- 둘째 정의 금지; 구조 규칙 A 보충 (3)이 그때 충족; DE-1 (c) A_dc 갈래는 같은 정의 자리를 인용해 따라온다 -- 계획 O-107 행). A_dc 생산자 둘(`offset_analysis.py:74`·`offset_systematic.py:50` -- O-71 백로그)의 정본 하나 정리도 DE-1 몫이다. 슬루 `.tran` 시작 동작점(N3.8 577, O-69 (1))·DEC-74 front 판정 기록(O-68 (3))은 IT-2 범위 밖이다.
- FX-1: §0 '단계 A는 봉인된 값을 읽지 않는다'의 출발 고정점 예외(X-FX1).
- O-49 P2 → 4.7-3 2 포트 창 규칙, P3 → 4.7-3 3 묶음(X-IT11) -- 둘 다 측정 구성 판정 창; P1·P4·P5·P6은 대상 소멸(O-109). 옛 D1~D6 경위 = design 이력 H41-13.
- (옛 멈춘 항목 S-1~S-4·T-1은 O-58·O-59로 설계됨 -- design 이력 H41-14.) **IT-2 착수 실측 멈춤 조건**(멈추고 보고): **IT-2c 착수 실측**(계획 v6.24 N6.6 순서, 사용자 결정 O-71 미확인 항목 -- 기록 뒤 착수, 결과가 계획 N3.8 정의와 어긋나면 멈추고 보고): (a) `current_reuse_telescopic_ota` 봉인점의 servo 피벗 a_e와 δA_num 값(v6.35 -- 옛 T_p) (b) 진짜 A = 0인 대칭 사례 하나(갈래 발동 확인) (c) 오라클이 선언한 실제 vntol·reltol(oracle N0 29행 입력) (d) 기본 포트 뷰 성립(13회로)과 S1v 기본 포트 뷰 늘 둠·식별 칸으로 바뀌는 S1v 소비자 값의 회로별 실측(v6.36 -- 옛 'ICMR 제약 4회로 gain 전달 뷰 성립' 대체; 어긋나면 멈추고 보고) (e) 차동 출력 servo 착수 실측(`current_reuse_telescopic_ota` 봉인점 servo 연립 특이·\|a_e\| 판정 -- 특이·판정 불능이면 멈추고 보고) -- (a)~(c) T_p 기준 **기록됨**(a_e 기준 (a)(b)와 (d)(e)는 IT-2c 착수 때)(`wt/_drafts/evidence/2026-10-22/it2c_circuit_access.md` §5: (a) 미측정(층 0 시작점 없음, 차동 출력이라 T_p 판정 전에 끝남), (b) 발동 + 조립 상쇄 구멍 → O-107 식 정정, (c) vntol 1e-7·reltol 1e-4; 4.7-3b '판정 분해능 정의 함수 하나'). **잴 수 없는 착수 실측의 처리**(v1.12.4 검증 nice-fix -- **design 선택, 사용자 확인 대상**): (a)는 지금 `current_reuse_telescopic_ota`에 층 0 출발점이 없어(`layer0_start` 출발점 없음 -- `_drafts/evidence/2026-10-21/dvout_feasibility.md` 5행) 잴 수 없다. 착수 실측을 잴 수 없으면 IT-0/IT-2c 판정 기록에 '미측정 + 사유'로 적고 IT-2c code 착수 전에 사용자에게 보고한다 -- 조용히 진행하지 않고, 다른 회로·다른 점의 대체 측정을 만들어 넣지 않는다; 판정 단위 = card 넷 IT-2a 스냅샷 파생(4.7-3c)·IT-2b 커널 창(4.7-3·4.7-3a; `_refine_ends` 삭제 포함 -- 병합됨 `6afe4758`)·**IT-2c 측정 구성**(v1.13.0 범위 -- 계획 v6.34 N6.6 순서: 봉인점 소신호 회로 필드 `graph.ss_circuit`(writer `ss_circuit` 하나) 신설과 `metrics_ss`·`metrics_aux` 조립 사본 삭제·`CODE_PASSIVE_MISSING` 한 자리·DC 전도 소자 결측 fail-closed(계획 v6.34.1 -- **원래 취지와 다름(범위 확대: 기존 조립 사본 둘 정리 + `graph.ss_circuit` 신설), 사용자 승인 대상**), 4.7-3b 전부(KCL 측정 구성 감도 `kvl_sensitivity`·`ss_nodal`과 E 칸 `g_bound`·`StampSet.g_ops`·`conductance_matrix(bound)`·세 자리 이전·`_transfer_resolution` E 항·F 성분 판정; v1.14.0 servo 측정 구성·`IcmConfig` 칸 개정·V_cm 칸 -- DC 되먹임 판정은 빠지고 절단 넷 순수 함수는 card TN-1; v1.14.1 S1v 기본 포트 뷰 늘 둠·`default_port` 칸(`views.py`·`s1v_values.py`·`s1v_fields.py`), 전도 행 R0(`_conduction_rows`·행 꼴 일반 1차 행), F 성분 포트 함께 구동(`writer_head`·`INPUT_STATUS_F_COMPONENT_UNDECLARED` 삭제), 끝 상태 레일 자름), 4.7-4 `Circuit` 행 부분 이동·`sizing.__all__` 공개(U-101 (가′)), 커널 `node.dc_window` W4 뿌리 축소(D1, 4.7-3 2·3), 출력 구조 분류 필드·writer 부분·S-OS1 삭제(D4, 4.7-1a), `saturation_window` 쌍 roots·묶음 갈래 삭제(4.7-3 2), 측정 구성 창 미수렴 이어받기 없음(D2))·**IT-2d front 배선**(v1.13.0 축소 -- 계획 v6.34 N6.6 순서 'IT-2d 범위 = front·보고가 `node.dc_window_cfg` 값을 쓰는 배선과 옛 입력 창 계산(`ls_swing`) 삭제·`metrics_aux` 배선뿐': 4.7-5 -- `icm_window.py`·`IcmPort`·`IcmWindow`·`metrics_aux` 배선·`ls_swing` 입력 창 삭제, V_cm 좌표(U-106), B77(계획 v6.34.2 -- registry relabel·`_missing_gate`·보고 갈래); 다듬은 창·front 전용 블록·helper 이동 없음 -- 4.7-4)(사용자 결정 O-69 (2) -- 같은 통합 브랜치, master 병합은 IT-1과 함께 한 번) + **card IT-2e 실패 평가의 부분 스냅샷 파생**(4.7-3c '실패 평가의 부분 스냅샷 파생'·L11 (e), 계획 v6.32 N6.6 범위 5·순서, 사용자 결정 O-96: IT-2d 뒤, IT-1 + IT-2 master 병합 전에 같은 통합 브랜치에서 test·code 커밋; 착수 조건 = 계획 v6.32 승인 → design 40 §2.4.7·이 4.7-3c 개정 → design↔계획 gap → IT-2d 병합 head에서 착수 사실 재측정); 구동 쌍 넷 ⊄ ac 접지 ∪ 입력 넷, 기본 포트 뷰 불성립·차동 출력 servo 특이(위 (d)(e)) -- v1.14.0: 옛 '루프 절단 적용'(S-3 폐지)·'커널 컨텍스트에 되먹임 선언 자리 없음'(extras에서 선언 되먹임 삭제)은 대상 없음(옛 '`require_immutable` 거부'는 L10 (f) test 단언으로, 옛 '`block_model`·`ff_gm_ratio` 인자'는 사실 확정으로 뺐다 -- W4·I2).
- **card EO-1 범위**(사용자 결정 O-55 U2·O-56 -- 이 design은 소비만 한다): 공용 전도 판정 함수 하나(봉인 7·9가 바로 부름), `search_domain`이 상자를 드는 kind 목록의 `off` 제외(`intended_region` 위 술어 하나), headroom-chain `device.dc_sat_v`의 `off` 갈래(HC-S·EO-1 중 늦게 병합되는 쪽). `off` 소자를 사이징·역산 경로에서 빼는 것(O-55 V5)도 EO-1 범위 4 (b)다. IT-2는 4.7-3a 2에서 그 함수를 부르기만 한다. **늦게 병합 몫**(사용자 결정 O-58 S-4·O-98, 계획 v6.33 N6.20 범위 (4)·완료 조건 (8)(e)): (S4-나)이면 `off` 경계 행과 **동작점 불일치 묶음**(4.7-3a 3 -- 노드 풀이 블록의 판정 호출 자리 하나, 같은 점 봉인 거부, 불일치 toy 셋; 불일치 상태 값·소자 열 칸·metric code `input_window_operating_point_mismatch`는 실을 cfg 항목이 대상 없다는 사실로 EO-1 design이 둘지 정한다)이 EO-1 범위이고, **EO-1은 IT-1 + IT-2 통합 병합 뒤에 병합**한다(갈래는 IT-2b 착수 때 한 번 -- 4.7-3a 2).
- **card DE-1 몫(O-50·O-54 관련)**: 정의 창의 tol 없는 경계(포화·triode·전도 끝 -- 같은 KCL 연립, O-109 C2), 훑기 점 I_off·ε, 출력 창 필드(옛 '기준 칸을 `"definition"`으로 바꾸기(O-49 P5)'는 기준 칸이 없어 대상 소멸 -- v1.13.0).
- 다른 계획·문서의 후속 정정 목록(helper 이동에 따른 경로·줄 번호 변경 -- 각 문서가 자기 개정에서 고침) = design 이력 H41-15.

**상태**: 4.1은 PART(분류는 있고 매핑이 없다). 4.2~4.6은 MISS. 4.7은 MISS(J-E 창은 as-built `input_window`·`_solve_input_window`가 PART -- A1~A10).

---

## 5. FR-4 -- 층 0 gain 예산 조합 front와 `gain_budget_db` (MOD6)

> **v1.6 계획 복귀 개정 (사용자 결정 2026-10-12 A1~A6, "L1~L13 모두 권고대로 해" 반영, 재검증 반영). L-14는 결정됐다(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지").** 사용자 결정 "A1~A6은 계획대로 되돌려"에 따라 v1.5의 이탈(§5.3 축 표의 'LUT gm/ID 격자점'·'LUT L 점' 후보 축, 'gain bin은 출력이다(N6)', (b) bin 안 L 다듬기, §5.10 as-built 1·2·11)을 폐기하고 계획 v6.3대로 다시 쓴다. 조항 대응은 §5.11, 계획이 정하지 않았거나 서로 어긋나는 점은 §5.12다. 범위 밖(A7 혼합 회로 버퍼 rout 국소 제약, A8 차동쌍 완화, A9 9회로 축소 격자 대조, A10, 결정 9의 §6 KVL 고리 개정)은 접점만 적는다(§5.10-3).

정본은 DEC-71 (1)~(8), DEC-73, DEC-77, DEC-03, DEC-92 (2), LR3·LR5·DEC-16·DEC-19다. **v1.15.0(계획 v6.38)**: 근본원칙 DEC-104(θ 기저·손계산 순서 -- 사용자 결정 O-127·O-128·O-141·O-142·O-143·O-144·O-146)가 이 절 전체의 상위 정본이다. 결정 순서는 계획 N1.1(v6.38 O-128 Q9) '요구 정의(소신호·정상상태·동적) → signal stage 유도 → 보상 → 전류 하한 → 신호 gm → gain 할당(S gm_id·L) ⇄ 고리 종속 파생(B·저항 강하·W4) → 전체회로 판정 → oracle 확정'이고, 충돌하면 DEC-104 (1) 우선순위 P0 물리 정합 > P1 fail-closed·상수 발명 금지·회로 이름/태그 금지 > P2 정의 하나·writer 하나 > P3 교과서 손계산 순서 > P4 손계산 속도 > P5 design 단순성 > P6 기존 결정 문언을 따른다. θ의 독립 성분은 S·F 셀의 ln IDu, L 동치류 L, 고리 종속이 아닌 y, θ 전류, 그리고 θ점 DC 전류가 0인 DC 경로 저항의 R 자체(spec 저항 상자 안 -- DEC-104 (4), O-157 S6)다 -- B 소자 ln IDu·값 미선언 DC 경로 저항의 강하 V_R·종속 W4는 고리 종속 성분이고 θ에 들지 않으며 DEC-104 R6 블록(§6.7-11)이 파생한다(계획 DEC-70 v6.38, M11).

**파일**(`E/search/`): `layer0_budget.py`, `gain_bins.py`, `local_candidates.py`, `local_front.py`, `combo_dp.py`, `assembly.py`, `budget_override.py`, `eval_budget.py`, 신규 `layer0_inverse.py`(§5.3.3~5.3.6), 신규 `l_targets.py`(§5.3.7).

### 5.1 활성 조건

**활성**: 다음 셋이 모두 맞을 때 층 0 gain 예산을 돌린다.
- gain 제약 `gain_ss_db >= G`가 있다.
- 그 전달 뷰에 이득 블록이 하나 이상 있다.
- `review_needed`가 없다.

**예산 대상**: 주경로 블록만이다(§1.12.2-4, J-A). feedforward 묶음은 bin·조합 DP·`gain_budget_db`에 항목이 없다. 조립점에서 FF 묶음 소자는 출발 구간(§6.5, r_ff = 1 관계)의 값을 쓰고, 그 기여는 §2 경로 기여로 계산해 조합 순서의 잔차에 넣는다.

**버퍼 블록의 국소 AC 제약**(DEC-71 (3) "그런 블록에는 선언된 출력 저항 상한(`rout_ss_ohm`)을 블록 국소 모델의 테브난 출력 저항에 건 것을 국소 AC 제약으로 대신 쓴다", 사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐" P-15 "이득 블록과 섞인 회로의 버퍼 블록에도 rout 국소 제약"):
- 이득 블록이 없는 회로(버퍼만): 층 0을 rout 모드로 돌린다. **as-built는 다르다**: integ/it12 `3179cd78` 층 0은 최소형 시작점(`E/search/layer0_center.py` -- θ 상자 중심에서 출발한 봉인 여유 max-min, 'feasibility centering')이고 버퍼 블록 rout 국소 제약(§5.12.5 E10)은 구현되지 않았다(B80 분석 `wt/_drafts/evidence/2026-10-24/b80_pushpull_front_zero.md` (a)(b); 계획 DEC-71 상태 칸 '미구현 -- card LA-1 F-LA1'; 옛 U15 전체판(§5.10-1 항목 8)은 master에 병합되지 않았다 -- 계획 F-LA6). card LA-1이 이 규칙을 구현한다(계획 DEC-71 (3), X-LA2).
- 이득 블록과 섞인 회로: gain 모드 층 0 안에서 버퍼 블록도 국소 문제를 푼다. 국소 AC 제약은 국소 Z_out ≤ `rout_ss_ohm`이다. 버퍼 블록은 gain 예산을 받지 않으므로 gain bin이 없고 면적 bin만으로 front를 만든다(DEC-71 (6) '이득 블록이 없어 gain bin이 정의되지 않는 블록'). DP 단계로 들어가는 방식은 §5.6이다.
- `rout_ss_ohm` 선언이 없는 버퍼 블록: DEC-71 (3) "그 선언도 없으면 그 블록은 '층 0 무동작'으로 보고"대로 그 블록만 무동작으로 보고하고, 그 블록 소자는 §6 출발값에 둔다. 섞인 회로에서는 그 블록만 무동작으로 보고하고 나머지 층 0은 돈다(PQ3 결정, 사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지").
- 실측 대상: sf_pushpull_output_opamp(vout 버퍼), two_stage_ota_sf(vout 버퍼). 둘 다 `rout_ss_ohm <= 1000` 선언이 있다.

**gain 제약도 rout 제약도 없는 경우**(H2):
- 문제: 국소 문제에 AC 제약이 없어 해가 최소 크기로 자명해진다.
- **처리**(사용자 결정 2026-10-08 Q5b. DEC-71 (3)의 '사이징 대상에서 뺀다' 대신 적용):
  - 층 0을 끄고 '층 0 무동작'으로 보고한다.
  - 시작점은 출발 구간(§6)에서 만든다.
  - 탐색 결과는 **'성능 판정 보류'**로 표시해 보고한다. 회로를 사이징에서 빼지 않는다.
  - 현재 해당 회로: common_gate_amplifier, folded_cascode(40 §9 Q5 표). 잡음 가드 `noise_excess_th` 행만 있는 경우도 gain 예산은 동작하지 않는다. (v1.15.0: 계획 v6.38 card LA-1 범위 14(사용자 결정 O-140 D1~D6·O-143 (1)(2))가 두 회로에 `gain_ss_db`·GBW·PM data(common_gate는 C_L 1 pF 측정 부하 `measurement_load: true` 표지·값·출처 -- topology CL 원소는 사용자가 추가, U-129 승인 O-166)를 LA-1 통합 병합 안에서 더하므로, 그 data 커밋 뒤에는 두 회로 모두 gain 모드다 -- 변화표 원인 칸은 'spec 추가'와 '층 0 전체판'으로 나눈다, O-143 (1).)

**보고 분류 출력 자리**(계획 v6.38 card LA-1 범위 9·완료 조건 6·7 -- B80 F-LA12, 검증 m3 '출력 자리는 design'; 새 분류 없음 -- 범위 6·7과 이 절이 이미 정한 표기를 결과에 싣는 자리):
- 필드 `graph/layer0: report_class` = 회로 하나의 층 0 분류 tuple(정렬) -- 원소 ∈ {`layer0_inactive`('층 0 무동작', 이 절 H2·PQ3 블록 단위면 원소 `("layer0_inactive", <블록 키>)`), `assembly_failed_path`('층 0 조립 실패 경로', LA-Q2), `performance_judgement_deferred`('성능 판정 보류', Q5b·U-56)}. 비면 `()`. writer = `layer0_budget` 블록 하나(활성 조건을 판정하는 자리, §5.1; 층 0이 돌지 않는 회로에서도 이 블록이 활성 판정만 하고 이 필드를 쓴다). 소비자 = 결과 JSON 보고(U16 -- 결과 JSON `layer0.report_class`와 notes 한 줄)·card LA-1 완료 조건 7 보고 분류 toy -- **출력 전용**(탐색·판정이 읽지 않음). 옛 notes `layer0_minimal`·`feasibility_only`(·`refinements_out_of_scope`)는 범위 8이 같은 변경에서 새 층 0 notes로 바꾼다(완료 조건 7: `git grep layer0_minimal`·'최소형' 0; 층 0 무동작 회로에서 바뀌어도 되는 것은 그 notes와 이 표지뿐 -- 완료 조건 5). `failed_eps` 정지 사유는 외층 정지 사유라 그대로 둔다.
- 이 보고는 결합 회로 한정이 아니라 모든 회로의 일반 보고다(계획 범위 9, 검증 m3). as-built는 front 0점을 분류 없이 낸다(WP-01 소지 -- 계획 F-LA12).

### 5.2 bin

- **gain bin 폭**: w_g = max(b_gain, `model_error_gain_ss_db`)이다.
  - b_gain은 `MetricResult.resolution`이다. 단계 B의 첫 봉인 평가에서 잰다. 잴 수 없으면 기준점 행에서 블록 국소 모델의 격자 분해능(§4.2 b와 같은 정의) 최댓값을 쓰고 출처를 `bins.b_gain_source`에 적는다.
  - 모델 오차가 미측정이면 b_gain만 쓰고 결과를 '추정'으로 표시한다(§0, DEC-72).
- **면적 bin 폭**: DEC-80 (ii)를 따른다.
- **bin은 목표다**(P DEC-71 (3) "블록 이득은 등이득 contour에 해당하는 **gain bin으로 고정**해 bin마다 따로 푼다"):
  - bin b = [b·w_g, (b+1)·w_g)이고 그 목표 T_b = b·w_g(아래 끝)다.
  - 국소 AC 제약은 P DEC-71 (3) "블록 국소 소신호 모델(N3.8) 이득 ≥ 그 블록 예산"이다. 그래서 점 p는 국소 gain(p) ≥ T_b이면 bin b를 **충족**한다. 한 점이 아래 bin 여럿을 함께 충족한다(§5.4).
  - 폐기: v1.5 'bin 번호는 floor(gain / w_g)로 평가된 후보에서 정한다(gain bin은 출력이다, N6)'.

### 5.3 블록 국소 문제와 역산 우선 후보 (DEC-71 (3)(4), LR3·LR5)

#### 5.3.1 국소 문제 (DEC-71 (3))

| 항목 | 내용 | 계획 인용 |
|---|---|---|
| 범위 | 블록 소자를 덮는 기둥 집합. 바이어스 기둥도 같은 절차(gain 제약 없음, 면적 bin만) | "범위 = 그 블록의 소자를 덮는 **기둥 집합**이다" / (2) 바이어스 기둥 |
| 입력 | 블록 예산(§5.3.2), 기둥별 레일 전압차, 블록 전류(KCL·선언·DEC-104 R8·R10 공급 요구 하한 -- §6.8), 소자 간 등식(매칭·공유 VGS·diode), 고정 입력(§5.3.10) | v6.38 DEC-71 (3) "블록 전류(KCL·선언·DEC-104 R8·R10 공급 요구 하한 -- ... 출력 노드의 그 방향 공급 셀이 모두 바이어스 구동 레일 source 셀일 때 ... (비대상 가지 순 주입 전류 ≤ 0 가정 붙은 필요조건 -- O-144 J1·O-146 K1·O-157 S4); 그 밖에는 엔진 슬루 하한·출발 목표를 두지 않음(O-157 S4·O-162 -- 옛 ''추정' 출발 목표로만' 삭제); 옛 '슬루 하한은 v6.37 O-122로 없음' -- 부분 복원, 원래 취지와 다름 승인 O-143)" |
| 결정 | S·F 소자 gm/ID(θ 좌표는 ln IDu, DEC-88), L 동치류 L(bin 선택 + bin 안 연속, LR3), θ 전류. B 소자 gm/ID·값 미선언 DC 경로 저항의 강하 V_R·종속 W4는 결정이 아니라 후보마다 DEC-104 R6 블록(§6.7-11)이 R5′로 파생한다(§5.3.4) | v6.38 DEC-71 (3) "결정 = S·F 소자 gm_id·L과 θ 전류다. B 소자 gm_id·값 미선언 DC 경로 저항의 강하 V_R·종속 W4는 후보마다 DEC-104 R6 블록이 R5′로 파생한다(... **원래 취지와 다름(승인 O-127·O-128·O-142)**: 옛 '소자별 gm_id·L·기둥 내부 노드전압(VDS 배분)'...)" |
| DC 제약 | 국소 봉인(§5.3.9)이 검사. 덮는 소자의 포화 부등식은 R-1′ 제약 그래프 S0 필드(TB-1, 40 §2.4.8)의 변과 writer_root 행으로 읽고 기둥 KVL만으로 대신하지 않는다 | v6.38 DEC-71 (3) "DC 제약 = 덮는 기둥마다 KVL(Σ VDS + 저항 강하 = 레일 전압차), 분기 노드 KCL, 포화 여유, diode VGS = VDS, 벌크 역바이어스 -- 덮는 소자의 포화 부등식은 R-1′ 제약 그래프(headroom-chain N3.1, S0 필드, 사본 금지)의 변과 writer_root 행이며 기둥 KVL만으로 대신하지 않는다" |
| AC 제약 | 국소 gain ≥ T_b. 출력 임피던스도 기록 | "이득 ≥ 그 블록 예산(출력 임피던스도 함께 기록)" |
| 목적 | (전력, 면적) 2목적, gain bin마다 따로 | "목적 = (전력, 면적) 2목적 ... gain bin으로 고정해 bin마다 따로 푼다" |

#### 5.3.2 블록 예산과 목표 bin 집합

- **첫 회차 예산**(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-2): g_i^(1) = G · found_db_i / Σ_j found_db_j (dB). found_db = 축소 전 GB4의 격자 일부 좌표 상승 최댓값(§4.2, 하한 추정). (gap A2: 두 양 분리) 뷰 전부 found_db가 있으면 1회차 예산은 g_i^(1) 필드(`graph/ach: gain_target_first`, §6.4-1)를 READS한다(재계산 0); found_db 없는 블록이 든 뷰는 g_i^(1)이 정의 불능이므로 그 뷰의 1회차 예산 = L-2 보완(층 0 기준점의 블록 분해 gain을 found_db 자리에 넣은 비례 -- 입력이 층 0 기준점이라 정의 축이 다른 양, '추정' DEC-67)이고 자리 = `graph/layer0: rounds`의 1회차 `budget` 칸(writer = 층 0 블록 하나, 계획 DEC-105 (1)·U-133 (A)). 첫 목표 bin = g_i^(1)를 담는 bin. A_i,max·A^L0 비례는 쓰지 않는다.
- **bin마다 푼다**: 블록 i가 푸는 bin 범위는 GB4 표와 역산 결과에서 정한다(새 상수 없음).
  - 위 끝 = max(A^L0 bin, 역산 실패 bin). A^L0 bin은 A_i,max^L0(§4.2, '추정')가 인증일 때 A_i,max^L0 + b_GB4,i를 담는 bin이고, 미상이면 없다. 역산 실패 bin은 (b) L 역산(§5.3.5)이 역산 대상 동치류 전부·모든 L bin에서 근을 못 찾는 첫 bin이다(그 bin과 그 위는 같은 고정값에서 도달 불가). 둘 중 큰 쪽까지 푼다. A^L0가 실제 상계가 아니므로 역산이 더 위에서도 근을 찾으면 그 bin을 버리지 않는다.
  - 아래 끝: 다른 블록의 축소 전 A_j,max(§4.2, exit 3과 같은 상계)가 모두 인증이면 G − b_gain − Σ_{j≠i}(A_j,max + b_GB4,j)를 담는 bin부터다(그 아래 bin을 쓰는 조합은 G에 닿지 않는다). '추정'인 A^L0로는 아래 끝을 자르지 않는다. 미상이 있으면 역산이 모든 대상에서 L 창 하한(§5.3.7)으로 눌려 직전 bin과 같은 후보만 낼 때 멈춘다.
  - 순서: 첫 목표 bin → 위로 → 아래로. 예산이 끊겨도 시작 배분 근방이 먼저 덮인다.
- **이후 회차**(사용자 결정 2026-10-12 L-3 "2회차 이후 = 고른 조합의 미해결 (bin, 고정 입력 지문)만 재풀이, 조합 front 불변이면 정지, 상한 K_max(DEC-70 반복 자리 추가 포함)"):
  - 회차 r ≥ 2의 입력: 예산 = 회차 r−1에서 조립이 고른 조합들의 `allocated`(§5.5·§5.6), 고정 입력 = 그 조립점 값(§5.3.10).
  - 다시 푸는 것: 고른 조합에 든 블록마다 (목표 bin, 고정 입력 지문) 쌍 중 `solved(블록 키, bin, 고정 입력 지문)`(40 §2.4.5)이 거짓인 것만 푼다. 참인 쌍은 다시 풀지 않는다.
  - 그 뒤 국소 front(§5.4) → 조합 DP(§5.6) → 조립(§5.5)을 다시 돈다.
  - 멈춤(계획 DEC-104 R5′ (4)(iii) ① 재검증 6 H-2, **원래 취지와 다름(계획 표지, 승인 O-162)**: 사용자 결정 L-3 종료 조건을 넓힘): 조합 front(조합 집합과 조합마다 (전력, 면적) 칸·`allocated`)가 직전 회차와 같고 **'이득 행 재개방' 표지가 선 미해결 칸이 0**이면 멈춘다. 표지(R6 출력 `graph/start: loop_dep`의 `reopen` 성분, §6.7-11)가 선 후보 칸은 다음 회차의 미해결 칸이다 -- 표지는 그 칸의 고정 입력 지문(입력 버전)에 들어가므로 `solved(블록 키, bin, 고정 입력 지문)`이 거짓이고 S3 graft가 옛 결과를 돌려주지 않는다(새 반복 자리 0 -- DEC-70 (d), 상한 = 아래 K_max).
  - 상한: N3.6 K_max 규칙이다. 변화량은 §5.3.6과 같은 지표를 고정 입력 소자에 적용한 것(VGS 변화, |Δln ID|/(gm/ID), |∂VGS/∂L|·|ΔL|)이고, 구간폭도 §5.3.6과 같다. q 규칙으로 도달 불가가 확정되거나 K_max에 닿으면 마지막 회차의 조합 front를 쓰고 `layer0_rounds_nonconvergent`를 기록한다(정지 아님).
  - **반복 자리**: 이 회차 반복은 DEC-70이 세는 반복 자리의 **넷째**다(사용자 승인 2026-10-12 L-3). 셋째(층 0 국소 고정점, §5.3.6)와 별개다. 계획 문언 정정은 §5.12.3 D3이다.
  - 회차 기록(회차 번호, 다시 푼 쌍, 조합 front 지문, 변화량)은 층 0 단계 필드다(40 §2.4.8 회차 기록 행).
- **L-2를 쓰는 이유**(실측, §5.12.4 표): 단계 B를 지나는 6회로의 이득 블록 7개가 축소 전 표에서 모두 미상이고(`grid_product_over_budget`), A^L0(§4.2)도 7개 모두 미상이다. 그래서 GB4 상한 비례 배분은 어느 gain 모드 회로에서도 정의되지 않는다.

#### 5.3.3 (a) gm/ID 역산과 소자 종류 (DEC-71 (4)(a), 사용자 결정 L-11)

P: "(a) 필요 gm에서 `gm_id = gm / ID` 역산". 사용자 결정 2026-10-12 L-11: "ID 미정 소자: 필요 gm 정의된 신호 소자만 gm/ID 자유변수(ID = gm/(gm/ID)), 부하·미러·바이어스는 §6 구간·미러비·KCL 로 정하고 격자 곱에서 제외(reference 방법론 §4.1·§6.4·§6.7)".

**L-11 개정**(계획 v6.38 DEC-104 'L-11 개정' -- 사용자 결정 O-128 Q2(M3), **원래 취지와 다름(승인 O-128)**): 부하·미러·바이어스(B)는 어느 층에서도 독립 변수가 아니다 -- 고리 종속이면 DEC-104 R5′·R6(§5.3.4·§6.7-11), 아니면 §6 가드 구간의 선택점·미러 비·KCL로 정하고 격자 곱에서 뺀다. 옛 B 행의 '외층 SLSQP가 다듬는다'는 삭제했다(외층 탐색 공간에서 B 축이 빠지는 front 영향은 미측정 -- 계획 문언 그대로, LA-1 변화표에 원인 항목으로 적는다).

**분류의 정본**(계획 DEC-104 R13·(3)(a), card TB-1): 아래 표의 종류는 S0 필드 `device: theta_class`(40 §2.4.8, writer = 분류 블록 `theta_class` 하나)의 값이다. 층 0은 이 표를 다시 계산하지 않고 그 필드를 READS한다(둘째 생산자 금지). 표의 구조 정의는 그 블록이 쓰는 정의의 서술이다. 층 0 실행 중 매크로 실패로 S가 F로 가는 갈래(아래 `no_gm_requirement`)는 필드 값을 바꾸지 않는 실행 기록이다(필드 = 선언·연결에서 정한 분류, 갈래 = 그 후보의 처리). 표의 '제외'가 R13의 X(쓰기 계획 종속)다.

**소자 종류**(구조 사실만 쓴다. 이름·상수 없음, IC4):

| 종류 | 구조 정의 | gm/ID | 전류 |
|---|---|---|---|
| 제외 | 쓰기 계획이 종속시킨 소자(`dc_coord.relation` = `cycle_vgs`·`fixed_vgs`, DEC-64 v2 고리 종속 멤버)와 같은 VGS 묶음 비뿌리(`parallel_vgs`) | 고리 등식·묶음 뿌리가 정한다(P DEC-64 "하나의 gm_id가 종속된다"). `kvl_dependent`·`parallel_member`로 기록만 | KCL |
| S: 필요 gm이 정의된 신호 소자 | gain 제약 전달 뷰의 주경로 이득 블록에서 S1v AC 역할이 `input`(시작 CS·CG, `Block.roles`)인 소자. 단 §6.5 매크로가 활성일 때만이다. 활성 조건은 §6.5와 같다: `gbw_target_hz`가 있으면 활성이고, `pm_target_deg`가 없으면 PM 하한 경로(`PM_FLOOR_DEG` = 45°, 기록 `pm_floor_pole_at_ugf`)로 푼다. 이 소자의 필요 gm이 매크로 블록 VCCS gm_i로 정의된다 | ID가 정해졌으면(`kcl`·`ideal_source_ref`) 역산 gm_id = gm_req/ID. ID가 θ 전류면 **자유 변수**(축)이고, 정의역은 §6 구간 [gm/ID_lo, gm/ID_hi] 안 LUT gm/ID 점이다 | 자유 변수면 ID = gm_req/(gm/ID)(방법론 §4.1 흐름 3, §6.4 "(gm/ID1, gm/ID2) 각 단을 제어", §6.7 Phase 1) |
| B: 부하·미러·바이어스, FF | S도 F도 아닌 소자: AC 역할 `load`·`mirror`·`diode_load`·`tail_source`, 어느 블록에도 들지 않는 소자(바이어스 기둥, DEC-71 (2)), 그리고 FF 묶음 셀(§1.12.2, 주경로 예산 밖, §5.1) | **축이 아니다**(어느 층에서도 독립 변수 아님 -- L-11 개정). 고리 종속이면 후보마다 DEC-104 R6 블록 값(§6.7-11, §5.3.4) -- 선언 범위 고리의 B는 R5′ (1) 나머지 경계(범위 끝 `sat_threshold` 등호; 이득 저하 정의가 있으면 포화·이득 공동 집합의 끝 -- R7 (가), O-157 S7·O-158 D-1), 행이 깨질 때만 R5′ (4)(ii) K-1. 그 밖 B(고리 밖·미선언 고리)는 고리 나머지 구간 ∩ R7 가드 필드 `device: start.guard`(소자별 구간 + 합 행 -- DEC-105 (5)) 안 기존 K-1 max-min이고 '열린 결정' 표지(U-124)를 단다(R7 (나)), FF 셀은 §6.5 G_ff = r_ff·gm_in 출발값 | 미러 비·KCL로 전파한다(placer, §5.10-3) |
| F: 그 밖 신호 소자 | 필요 gm이 정의되지 않은 신호 셀: AC 역할 `cascode`·`pass`·`follower`, 그리고 매크로가 비활성인 회로의 `input`. **버퍼 블록(rout 제약, §5.1)의 출력 follower**는 예외다: 그 블록 출력노드에 source가 닿는 follower 셀은 필요 gm이 rout 제약으로 정의되므로 S로 본다(§5.12.5 E10) | DEC-71 (4) 격자 폴백(`no_gm_requirement`). 정의역은 §6 구간 안 LUT gm/ID 점이다. rout S follower: 한 출력노드에 그런 follower가 여럿이면 **공통 배율 하나** s로 푼다: 그 follower들의 gm을 현재 값 비율 그대로 s배 한 국소 모델 Z_out(s) = `rout_ss_ohm`의 1-D 근(나머지 값 고정). 정준 순서로 하나씩 풀지 않는다 -- §5.3.6 매크로가 블록 gm을 공동으로 푸는 것과 같은 이유(순차 1-D는 앞 소자에 몫을 몰아 순서에 따라 답이 갈린다)이고, 비율을 유지하므로 이름 순서와 무관하다(결정론). 그 뒤는 S 규칙 | KCL. rout S follower는 ID = gm_req/(gm/ID) |

- **F와 R5′**(계획 DEC-104 R5′·U-117): F 밀도는 R5′ 재개방 좌표가 아니다(O-142). F가 둘 이상 든 고리(또는 F가 남는 깨진 행)의 처리는 **미결 U-117**(O-141 (7) -- card LA-1 design 착수 때 재측정 뒤 결정)이다. 그때까지 그런 행은 F 격자 폴백 축(위 F 행)에서 그 후보를 위반 기록과 함께 버린다(R11 -- 새 처리 규칙 없음).
- **θ 저항**(계획 DEC-104 (4)·DEC-70 v6.38 -- 사용자 결정 O-127 (iii)·O-128 Q2): DC 전류 경로에 있는 값 미선언 저항은 강하 V_R이 고리 종속 성분이고 R = V_R/I_R(I_R = `dc_current_basis`의 그 가지 전류)은 파생값이다. R은 사용자 선언 spec 저항 상자 안이어야 하고 -- 그 상자 = spec `search.theta_bounds.<원소>{min, max, source}`(as-built 로더 `SPEC_CONTRACT.md` '`theta_bounds`' 절; 사용자 결정 O-127 원문 'R 상자: 하네스 `resistance_bounds_ohm` [1e2, 1e5]를 None으로 → 사용자 선언 spec 상자') -- 측정·test 하네스의 실행 단위 재정의 `SearchSettings.resistance_bounds_ohm`이 아니다(판정 기준선 변경이라 그 상자를 처음 읽는 card(LA-1)의 검증 변화표와 함께, 하네스 쪽 None 전환은 test·검증 역할 몫). 밖이면 그 후보는 `resistor_out_of_box{element, R, box}`로 탈락 기록한다(§5.12.6). I_R이 구조적으로 0인 저항은 DC θ가 아니다(V_R 고리 좌표 없음 -- 계획 완료 조건 1 (x)). 잎 가지치기로 잘리지 않지만 θ점 DC 전류가 0인 DC 경로 저항(대칭 DC점의 CM 감지 저항 등)은 R = V_R/I_R이 0/0이라 V_R 기저를 쓰지 않고 R 자체를 θ 독립 성분(spec 저항 상자 안)으로 둔다(DEC-104 (4), O-157 S6 -- 'θ점 전류 0' 판정 = 그 저항 가지의 `dc_current_basis` 행이 θ 대칭 묶음(궤도·`domain.ties` -- 40 §6) 아래에서 θ 전류 계수가 정확히 상쇄되어 항등 0인지(유리수 정확 산술, 허용오차 상수 없음); 항등 0이 아니면 V_R 기저 그대로). **우연한 0 전류**(gap §2 (5) 보완): 항등 0이 아닌데 그 점의 I_R(θ)이 정확히 0이면 R = V_R/I_R이 정의되지 않으므로(V_R = 0이면 0/0, 아니면 ∞) 그 후보는 fail-closed 탈락 `resistor_current_zero{element}`(기록, 상자 중심 R 대체 없음); 0에 가까운 I_R은 R이 커져 기존 `resistor_out_of_box`로 탈락한다(허용오차 상수 없음 -- 물리 결정자: 전류 없는 저항의 강하는 KVL이 R을 정하지 못함). 값과 spec 상자가 둘 다 선언되지 않은 DC 경로 저항은 단계 A에서 정의 불능으로 멈춘다(하네스 상자 대신 쓰지 않음 -- O-151 N-5).
- S 소자의 역산(ID 기지)이 실패하면 그 소자만 격자 폴백한다. 사유는 `gm_id_out_of_interval`(§6 구간 또는 LUT 범위 밖)과 `lut_hermite_nonmonotone_cell`(§4.1 격자 전용 칸)이다.
- (v1.15.2 개정 -- 계획 N6.35 E-31·머리 '출발 정의 불능 공통 규칙') 매크로가 비활성(`macro_inactive`)이면 그 블록의 S 소자는 F로 간다(`no_gm_requirement`). 매크로 출발 불능 후보(§6.5-4 (i))는 쓰이지 않고(다음 후보) 목표 미달(PM 미달·P ≠ 0·미수렴 -- §6.5-4 (ii))은 gm_req가 정의돼 S 그대로다(옛 '`macro_root_missing`·`macro_nonconvergent`이면 F' 갈래 삭제 -- 같은 상황의 둘째 처리, O-169).
- VGS는 `lut.vgs_for_gm_id`(gm/ID 역산 지표 tol_V (i), N3.6)로 구한다.
- 폴백·자유 축의 열거 규칙은 §5.3.11이다.
- **축 하나로 세기**: matching 그룹(S1 `graph.matching_groups`의 derived `diff_pair`·`branch_symmetric`·`mirror`)이나 자기동형 궤도로 묶인 S·F 소자는 gm/ID 축 하나다(차동쌍 두 반쪽 = 축 하나). 같은 VGS 묶음(`parallel_vgs`)은 원래 한 축이다.
- **실측**(2026-10-12, §5.8 표): 9회로 블록 MOS 102개 중 ID가 KCL·선언으로 정해진 소자는 0개다. 그래서 S 소자는 모두 자유 변수 축이고, ID 기지 역산은 발동하지 않는다.

#### 5.3.4 (c) VDS·V_R 배분 (DEC-71 (4)(c), DEC-104 R5′·R6 -- v1.15.0 재작성)

P(v6.38 DEC-71 (4)(c)): "VDS·V_R 배분(v6.38 O-127·O-128 Q2·O-142, DEC-104 R5′·R6 -- **원래 취지와 다름(승인 O-128·O-142)**: 옛 '전 소자를 포화 여유 하한(VDsat, DF-25)으로 채운 뒤 남은 헤드룸을 배분'): (c-1) 후보의 θ와 (VDS, VSB)로 R-1′ 변 가중치를 넣어 W4·V_R의 실행 가능 구간을 낸다(V_R 구간 = spec 저항 상자 × I_R과의 교집합) (c-2) 모든 행 ≥ 0이면 종속 성분을 바꾸지 않고, 깨지면 R5′ (4) 순서로 다시 열어 K-1로 함께 고른다(max-min 대상: B = gm/ID 위치, W4·V_R = 행 여유) (c-3) 판정은 그 점의 쓰기 계획 정확 풀이로 하고, 남은 위반은 S 정의역 조건으로 자르거나 거르며, 그래도 남으면 `chain_violation`(fail-closed) (c-4) 삭제(v6.38.1 O-155 M-2 -- 원래 취지와 다름(승인 O-155): 종속 W4·V_R 선택 정본 = DEC-104 R5′ (2) 행 여유 max-min(K-1))" -- 그리고 (c-3) 인용에 '(R-1′ 행; 범위 끝 이득 행은 R5′ (4)(iii) 탐색 개방, 거부는 R8 -- O-159 E-3)'를 계획 문언 그대로 넣는다.

이 절의 계산은 모두 **DEC-104 R6 블록 하나**(§6.7-11, 출발 단계 §6.7 7a 블록 확장 -- 출발·층 0 공용)가 한다. 층 0은 후보마다 그 블록을 부르고, 결과(B ln IDu·V_R·종속 W4)를 다시 계산하지 않는다(P2). 고리·변·변 좌표 집합은 R-1′ 제약 그래프 S0 필드(TB-1, 정의 = headroom-chain N3.1·N3.4, 형식 = headroom-chain HC-D design)를 READS하고, 고리 처리 자리(출발 단계 / 층 0 후보)는 분류 필드 `device: theta_class`(R13)와 변 좌표 집합에서 S0에 한 번 정해진 값을 읽는다(DEC-104 (0) -- O-127 (i)(ii)는 O-128 Q2·O-142로 보정: 구성원이 모두 출발 단계에서 정해지는 고리는 출발 스냅샷에서 한 번(graph reuse), 층 0 결정 변수가 섞인 고리는 후보마다).

- **변수**(고리 종속 성분만): 덮는 기둥의 종속 W4 자유 노드전압, 값 미선언 DC 경로 저항의 강하 V_R, B 소자 ln IDu(R7 가드 안). W0~W3 writer 노드는 쓰기 계획이 값을 정하고, W1/W2 노드는 재배분하지 않는다(LR7). S·F 소자의 (ID, gm/ID, L)은 이 절의 입력이다(그 후보의 θ 독립 성분).
- **(c-1) 구간**: 후보의 θ 독립 성분과 그때의 (VDS, VSB)로 R-1′ 변 가중치 κ(채널 VDS 변 + Gs⁺ κ, 저항 변)를 넣고, W4·V_R의 실행 가능 구간을 낸다. V_R이 아직 미지수인 저항 변은 κ에 넣지 않고 차분 변 쌍(x_far − x_near ≥ V_R,lo, x_near − x_far ≥ −V_R,hi -- headroom-chain N3.1-1)으로 넣는다. V_R 구간 = spec 저항 상자(§5.3.3 'θ 저항') × I_R과의 교집합이다. writer_root 행(1변수 노드 근 존재, O-141 (6))도 고리 행이다.
- **(c-2) 바꾸지 않음 / 재개방**(R5′ (3)(4)): 모든 행(포화 행·writer_root 행)이 0 이상이면 종속 성분을 바꾸지 않는다 -- 값은 R5′ (1)(2)의 쓰기 순서(spec → S·θ 전류 → 쓰기 계획 등식(X, 미러 비) → 선언 범위가 있는 고리는 범위 끝에서 그 고리에 마지막으로 남는 전력 중립 좌표를 나머지 경계(범위 끝 `sat_threshold` 등호; 선언에 이득 저하 정의가 있으면 포화 행과 범위 끝 이득 저하 행을 함께 만족하는 그 좌표 집합의 끝 -- 포화 등호 쪽에서 가장 가까운 경계, O-158 D-1 (A′)·E-5)로; 선언 범위가 없는 W4·V_R은 모든 포화 행·writer_root 행을 함께 만족하는 창 안에서 그 좌표에 닿는 행 여유의 max-min(K-1 (ii) -- O-151 N-2; `mirror_vds` 목표 행은 넣지 않음, U-126 (가)))로 정한 값이다. 공동 집합이 비거나 봉인 스냅샷의 DE-1 (e) READS가 이득 행 깨짐을 보이면 정의역을 자르지 않고 '이득 행 재개방' 표지를 R6 출력 필드에 남긴다(아래 (iii)·§6.7-11). 행이 깨질 때만 비용 순으로 다시 연다: (i) W4·V_R → (ii) B 밀도(R7 가드 안) → (iii) S만 남으면 층 0 정의역 조건(R-1′ 행: 좌표 하나면 그 축 정의역 자르기, 여럿이면 층 0 후보 거르기; 범위 끝 이득 저하 행은 정의역을 자르지 않고 '이득 행 재개방' 표지 + 탐색 개방 -- 표지가 선 후보에 한해 L 역산 고정과 출발 구간 축소를 풀고 spec 상자(R)·LR3 bin(L, S 소자)·S gm/ID 범위(그 L bin LUT gm/ID 정의역 ∩ 최소 폭 하한) 안에서 층 0 후보 생성, 거부는 커널 뒤 R8 이득 행만 -- O-158 (A′)·O-159 E-3·O-160 F-3·O-162). K-1 (i) 위반 최소에는 깨진 R-1′ 행 위반 다음 순위로 `mirror_vds` 목표 행(DEC-105 (4))이, (ii)(B 선택)에는 가드 합 행(DEC-105 (5))이 함께 든다(합 행 위반이 R7 (가) 나머지 경계에서 생기면 StartConflict 기록만). 각 단계에서 열린 좌표를 K-1(위반 최소 → max-min → 합, §6.7-4)로 함께 고른다. **max-min 대상**: B는 gm/ID 위치, W4·V_R은 위치가 없어 깨진 행 여유다(R7). X(쓰기 계획 종속)는 등식 고리의 종속이고 재개방 좌표가 아니다(O-141 (3)). F는 재개방 좌표가 아니다(L-11, U-117).
- **(c-3) 판정**: 그 점의 쓰기 계획 정확 풀이(커널과 같은 쓰기 계획의 θ 고정 풀이, 새 풀이기 없음)로 한다. 선형화 값으로 판정하지 않는다(DEC-104 (0)). 이 판정은 R-1′ 관계식 거르기(LA-1 범위 11 → headroom-chain HC-1 함수, §5.3.9)와 **같은 함수 호출**이다(두 번 판정 0 -- v6.38 P9). 남은 위반은 S 정의역 조건으로 자르거나 거르고, 그래도 남으면 그 후보는 `local_infeasible{reason: "chain_violation"}`(fail-closed, N3.14)로 버린다.
- **(c-4) 삭제**(계획 v6.38.1 DEC-71 (4)(c) -- O-155 M-2, **원래 취지와 다름(승인 O-155)**): 남은 W4 여유를 `∂(gm/gds)/∂VDS` 순으로 배분하지 않는다 -- 종속 W4·V_R 선택 정본은 (c-2)의 R5′ (2) 행 여유 max-min(K-1) 하나다(이득은 L bin이 지키고 목적 축이 아님; DEC-71 (3) 동률 규칙(포화 여유 최대)과 같은 기준).
- **출력**: 종속 W4 자유 노드전압·V_R·B ln IDu -- 그 후보 θ 성분(층 0) 또는 출발 행(출발 단계)의 자리에 둔다(출력 자리 = R6 블록의 출력 필드 하나 -- 성분 B ln IDu·종속 W4·V_R·'재개방 표지'(R-1′ 정의역 자르기 / 이득 행 탐색 개방); 계획 DEC-104 (3)(c), O-151 DK1; `device: start.row`·`graph/start: rungs`는 θ 독립 성분만 담는다). 40 §3.7-5 'W4 초기값'은 이 W4 전압이고, 커널은 그 전압을 노드 전압 목표로 받아 y를 커널 DC 순환 블록 (a) 안에서 정한다(창 밖이면 정확 풀이 판정 -- 40 §3.7-5, 계획 DEC-71 (4)(c) '커널 입력', O-151 M3).
- 폐기: v1.5 as-built 2의 '(c) VDS 배분은 커널 DC 정본(W4 창·쓰기 계획)이 한다', v1.14.2까지의 '1단계 채움(전 소자 VDsat + tol 채움 뒤 H = ΔV_rail − Σ(하한) − Σ(저항 강하), `headroom_floor_unmet`)'(저항 강하를 주어진 값으로 빼고 고리가 정한 VDS를 자유로 봄 -- 계획 v6.38 DEC-71 (4)(c) 원래 취지와 다름 승인 O-128·O-142; 옛 문언은 git `4604d993` 41 §5.3.4).

#### 5.3.5 (b) L 역산 (DEC-71 (4)(b), LR3)

P: "(b) 목표 이득에서 필요한 gm/gds를 구해 bin마다 LUT 곡선(같은 bin 안 L 점 사이 선형 보간)에서 그 값을 내는 L을 역산하고 bin을 고른다(bin 경계를 넘는 L 보간 없음, LR3)".

- **대상**: 블록 안에서 확정할 수 있는 L 동치류 c(고정 입력 §5.3.10 제외).
- **식**(§5.12.1 E1): 다른 값(다른 동치류 L, gm/ID, VDS)을 현재 바퀴 값으로 두고 블록 국소 모델 gain(L_c) = T_b를 L_c에 대해 푼다. 이것이 '필요 gm/gds → L'의 일반형이다. 단일 소자 단에서는 방법론 §6.7 Phase 2 "Av_total 목표에서 역으로 필요한 VA(따라서 필요한 L)를 역산"과 같다.
- **bin마다**: L_c의 PDK 모델 bin(LR3 bin 지도) 중 feasible_L_window(§5.3.7) 안의 bin마다 따로 푼다. bin 안에서는 이웃 LUT L 점 사이 구간마다 끝값의 gain을 보고, T_b를 넘는 첫 구간을 bisection한다. 반복 상한은 N3.6 K_max이고 L 쪽 멈춤 폭은 PDK 제조 격자(DEC-80 (i)과 같은 선언)다. 결과는 gain ≥ T_b인 쪽 끝 L이다. bin 경계를 넘지 않고 LUT L 범위 밖으로 외삽하지 않는다.
- **bin 고르기**: 근이 있는 L bin마다 후보 하나씩을 낸다. 고르는 것은 국소 front(§5.4, (전력, 면적) 비지배)다(L-6).
- **실패 → 그 동치류만 격자 폴백**: `l_inverse_no_bracket`(창 안 어느 bin에서도 끝값이 T_b를 가르지 않음), `lut_axis_out_of_range`(DF-27). 폴백 격자는 그 동치류의 LR5 격자(§5.3.7)다.
- **국소 모델 평가**: L·VGS·VDS·VS는 격자 마디로 맞추지 않고 LUT 운영 보간(DEC-87, L은 bin 안 선형 LR3)으로 평가한다. 폐기: v1.5 as-built 1 '가장 가까운 LUT 격자 마디로 맞추고'.
- **탐색 개방 후보에는 역산을 다시 걸지 않는다**(계획 DEC-104 R5′ (4)(iii) ② 재검증 6 H-6, 승인 O-162): '이득 행 재개방' 표지가 선 칸에서 생성된 후보(§5.3.4 (c-2) 탐색 개방 -- R·L(S 소자)·S gm/ID)는 연 축 값을 고정 입력으로 받고 이 절의 L 역산을 다시 하지 않는다(역산은 개방이 푼 출발 구간 축소의 일부라 같은 후보에 다시 걸면 연 축이 닫힌다). toy = 계획 LA-1 완료 조건 9 (d) 탐색 개방 toy(§9 v1.15.2 행).
- 폐기: v1.5 '(b) bin 안 L 다듬기'. 역산이 T_b를 맞추는 최소 L을 직접 내므로 따로 두지 않는다.

#### 5.3.6 (d) 층 0 국소 고정점과 보상 시작점 (DEC-71 (4)(d), DEC-70 (c), DEC-92 (2))

P DEC-71 (4)(d): "기생 용량 반영은 부하 C를 갱신하며 도는 **층 0 국소 고정점**이다 -- ... 수렴 판정·반복 상한·NONCONVERGENT 판정은 DC 순환 블록(N3.6)과 같은 규칙을 쓰고 새 상수를 두지 않는다." P DEC-92 (2): "극점·영점 근사식은 층 0 시작점 생성기로만 쓰고 근사 대 MNA 차를 `comp_approx_gap`으로 기록한다(판정에 쓰지 않음)."

후보 하나의 **한 바퀴**(LUT 계산과 매크로 풀이만 한다. 커널은 부르지 않는다):
1. 극점 노드 용량 C_n은 국소 조각의 W·L에서 봉인 스냅샷 `ss.node_c_farad`와 같은 정의(같은 함수)로 계산한다. 부하 요소 값과 보상 수동소자 값을 더한다.
   - 이 값은 봉인 전 AC 값이라 **'추정'**이다(P DEC-67 "봉인 전에 내는 AC 값은 '상한' ... 또는 '추정'(시작점)으로 표기").
   - 접합 용량의 확산 기하는 레이아웃 전이므로 LUT 생성 규칙의 확산 기하 **규칙**(LUT 특성화 `DUT_LINE`의 ad/as/pd/ps 꼴)을 쓴다(P DEC-91 (2)). **v1.15.1 개정(계획 v6.38.2 DEC-105 (2) -- DEC-91 (2) 개정, card WB-1)**: 그 규칙을 총 폭 W 비례가 아니라 **손가락 폭 w_f와 손가락 수 m**(레이아웃 전 손가락 기하 -- 40 §3.7-A 3 `device: dc_finger`)으로 계산한다(EO-1 넷리스트 ad/as/pd/ps와 같은 값). 국소 조각(봉인 전)은 그 조각의 W에 선택 함수(40 §3.7-A 5)를 한 번 불러 (m, w_f)를 얻는다(출발값 축 -- 블록 안 값, 저장 0). 옛 `pre_layout_geometry(w_m, W/w_m)`(슬라이스 폭·비정수 m)는 card WB-1 범위 2b가 지운다.
   - 첫 바퀴는 §6.5 매크로의 노드 용량이다.
2. 블록 gm 요구와 보상 시작점은 아래 **층 0 매크로 호출**로 구한다.
3. (a) gm/ID 역산(§5.3.3) -- S·F만. B는 4의 R6 블록 값이다.
4. (c) VDS·V_R 배분(§5.3.4 -- DEC-104 R6 블록 호출: 종속 W4·V_R·B ln IDu).
5. (b) L 역산(§5.3.5).
6. W = ID · L / IDu(LUT)를 구하고, 이 값으로 다음 바퀴의 C_n을 만든다.

같은 바퀴 안의 LUT 조회(VGS, VDsat, ∂(gm/gds)/∂VDS)는 직전 바퀴 값을 입력으로 쓴다(첫 바퀴는 층 0 기준점 값). (b)와 (c)의 결합도 이 고정점 안에서 풀린다. 새 반복 자리는 만들지 않는다. 이 고정점은 DEC-70 (c)가 정한 세 번째 자리(층 0 국소 고정점) 안에 있다.

**층 0 매크로 호출**(DEC-92 (2), §5.12.1 E2):
- **서명**: as-built `macro_solve(ctx, model, gm_id, lengths, refine=True)`에 키워드 전용 인자 셋을 더한다.

```python
def macro_solve(ctx, model, gm_id, lengths, refine=True, *, node_c=None, gm_bounds=None, gain_targets=None) -> MacroResult
```
  - `node_c`: {극점 노드: C [F]}. 주어진 노드는 소자 기여 용량(전류 비례 cgg + cdd/cgd 항) 대신 이 값을 쓰고, 수동소자는 그대로 더한다.
  - `gm_bounds`: {블록 키: (lo, hi) [S]}. 주어진 블록의 ln gm 변수 상자를 이 범위와 as-built 상자의 교집합으로 좁힌다. 변수에서 빼거나 고정하지 않는다.
  - `gain_targets`: {블록 키: g [dB]}. 주어진 블록의 출력 컨덕턴스를 G_i = gm_i / 10^{g/20}로 둔다(§6.5 망 구성의 g_i 규칙). 주지 않은 블록은 as-built A_intr를 쓴다.
- **풀이**: as-built 그대로다. 공동 SLSQP와 '단마다 그 단을 주극점으로 하는 실행 가능한 출발점' 다중 출발을 쓰고, 목적은 전원 전류 합 최소다(§6.5 as-built).
  - 다른 블록 gm을 고정한 순차 1-D 풀이는 쓰지 않는다. §6.5 as-built 기록 "gm_1 을 고정한 채 gm_k 를 줄이면 이득이 1 아래로 떨어져 (i)이 풀리지 않고, gm_1 을 함께 다시 맞추면 gm_1 상자 상한 모서리로 간다"의 퇴화를 피한다.
- **층 0이 넘기는 값**(블록 i, 목표 bin b의 후보 바퀴):
  - `node_c` = 1단계의 C_n.
  - `gain_targets` = {i: T_b, j ≠ i: 블록 j의 현재 예산(첫 회차 g_j^(1), 이후 조합 `allocated`)}.
  - `gm_bounds` = {j ≠ i: 블록 j의 현재 국소 front 점들이 가진 gm_j의 최솟값~최댓값}. 블록 j를 아직 풀지 않았으면 넣지 않고 as-built 상자를 쓴다.
  - 블록 i의 gm은 as-built 상자 그대로 변수다. engine 보상 커패시터도 as-built처럼 변수다.
  - 결과의 보상 수동소자 값은 층 0 시작점의 보상 수동소자 θ다(DEC-92 (1) "θ 연속 성분(외층 SLSQP 변수)"의 시작값).
- **gm_req,i**: `MacroResult.gm`의 블록 i 값이다. 매크로가 비활성(`macro_inactive`)이면 블록 i 입력 셀은 (a) 폴백(`no_gm_requirement`)으로 가고 그 기록을 남긴다(매크로 출발 불능 후보는 쓰이지 않고 목표 미달은 gm_req가 정의돼 그대로; 옛 '`macro_root_missing`·`macro_nonconvergent`이면 폴백' 삭제 -- §5.3.3·§6.5-4).
- **기본 호출 불변**: 세 인자가 모두 None이면 as-built와 비트 동일이어야 한다.
  - 결정 9 초안(u13-kvl-start 7d516cc §6.7-4 B3 "§6.5 매크로 모델(`current_model` + `macro_solve`, 확정 풀이와 같은 설정)")이 기본 호출을 쓴다. 그래서 이 조건이 두 개정의 호환 조건이다.
  - test(`tests/search/test_macro_poles.py`): 이상 VCCS 2·3극점 픽스처와 library 9회로 중 매크로가 활성인 회로에서, 기본 호출 `MacroResult`의 `fp_of`가 as-built bd19cc6에서 잰 기준 지문과 같아야 한다. 기준 지문은 구현 전에 test 작성 주체가 잰다.
- **비용**: 매크로 풀이는 커널을 부르지 않으므로 평가 수에 들지 않는다. 시간은 T_used에 든다(§5.8). 매크로 결과는 그 후보 국소 스냅샷의 층 0 필드다(40 §2.4.8 매크로 결과 행, 입력 버전 = `node_c`, `gm_bounds`, `gain_targets`, gm_id, lengths). 같은 입력 버전이면 계산 블록 규칙(40 §2.4.4 호출 규칙 1·2)대로 재사용하거나 이식한다. graph 밖 memo를 두지 않는다. 매크로가 부르는 LUT 조회(A_intr, cgg·cdd)는 LUT memo다(40 §2.4.6).

**수렴·상한·NONCONVERGENT**(N3.6 그대로, 같은 함수 `sizing.k_max`와 q 판정):
- 변화량 |Δ_k| [V]는 다음 다섯 중 최댓값이다(v1.15.0: V_R 항 추가 -- 계획 v6.38 DEC-71 (4)(c) '수렴 지표에 V_R 변화(V, 같은 tol_V)를 더한다', P4).
  - 소자 VGS 변화.
  - W4 노드전압 변화.
  - 값 미선언 DC 경로 저항 강하 V_R 변화(같은 tol_V).
  - 소자 |Δln ID|/(gm/ID): ID 환산 지표 (ii)다. N3.6은 순환 블록 수렴에 이 지표를 쓴다.
  - 동치류 |∂VGS/∂L|·|ΔL|: 같은 ln IDu·VDS·VSB에서 L 변화를 VGS로 환산한 값이다(LUT bin 안 선형 보간의 L 방향 기울기, LR3). 이 항이 없으면 L만 움직이고 전압은 같은 바퀴를 수렴으로 잘못 센다(§5.12.1 E6).
- 수렴: |Δ_k| ≤ 그 칸들의 tol_V 최솟값.
- 상한: K_max = ceil(log2(구간폭/tol_V)). 구간폭은 바퀴 변수들의 창 폭 중 최댓값이고, 출처는 as-built 커널 순환 블록과 같다.
  - 노드 변수(W4): 노드 창 폭. `sizing.fixed_point.gauss_seidel`의 `width`이고, 호출부 `E/sizing/block_columns.py`가 `k_max(c.hi − c.lo, ...)`로 쓴다.
  - V_R: §5.3.4 (c-1) V_R 구간 폭(spec 저항 상자 × I_R).
  - VGS: 레일 폭. `block_columns.py`의 1변수 노드 규칙 "상한 k_max(레일 폭, tol)"과 같다.
  - L 환산 항: VGS와 같은 창에 든다.
- q 규칙으로 도달 불가가 확정되거나 K_max에 닿으면, 그 후보는 NONCONVERGENT 실패 레코드(N3.14)로 남기고 봉인하지 않는다.

**보상 근사 기록**은 조립점에서 한다(§5.5 `comp_approx_gap`).

#### 5.3.7 L 초기 목표·knee·동치류 격자 (LR5, DEC-16)

P LR5: "초기 L 목표(역할은 라벨이 아니라 S1 유도 사실이다, IC4): 미러(`equal_vgs` 멤버) = kind별 knee(`measure_L_knee`, 동치류 멤버의 탐색 gm_id 가능역으로 한정한 곡선에서 계산 ...), 바이어스 레플리카(J1 교류접지 예외 목록 소자) = `feasible_L_window` 하한, 캐스코드(전류 구동 CG 셀)·그 밖 신호 경로 셀 = knee 목표를 거부하고 theta 탐색이 정한다 ... 모두 `feasible_L_window`로 clamp한다." P DEC-16: "초기 L은 공정 knee에서 시작하고 실현가능 창으로 clamp한다".

**동치류 종류**(S1 사실, 라벨 없음): 동치류의 종류는 L 주인(LR1·DEC-17, §1.12.5)의 종류다.
- 미러: 주인이 `equal_vgs` 멤버이고 신호 셀이 아니다 → 초기 목표 = knee.
- 레플리카: 주인이 J1 술어(§1.2 (4) 바이어스 종속 넷)가 교류접지로 둔 넷을 구동하는 소자다 → 초기 목표 = window 하한.
- 신호: 주인이 신호 셀(CS·CG·CD, 캐스코드 포함)이다 → knee 목표를 거부하고 (b) 역산이 정한다. 첫 바퀴 값은 §6 출발 L이다.
- 그 밖: §6 출발 L(DEC-71 (3) "첫 회차는 ... 출발 구간 값").

**knee(새 엔진 정의)**. 원천은 history v4.49 §7.10 '측정 2'와 레지스트리 `measure_L_knee` "L 격자 전수 스캔으로 한계 Δ(gm/gds)/Δ(W·L) 최대 구간 상단 L"이다. 옛 코드는 참고만 한다.
- 소자 d, 고정 (gm/ID, VDS, VSB)에서 LUT L 점 L_1 < … < L_n(bin 경계 점 포함, LR3)마다 e_j = gm/gds, a_j = L_j²/IDu를 구한다. VGS는 `vgs_for_gm_id`로 구한다. W·L = ID·L²/IDu이므로 ID는 argmax에 영향이 없다.
- 한계효율 η_j = (e_{j+1} − e_j)/(a_{j+1} − a_j). a_{j+1} ≤ a_j인 구간(IDu 비단조, §7.10 반례)과 §4.1 격자 전용 칸은 건너뛰고 `knee_interval_skipped{reason}`로 기록한다.
- knee = η가 가장 큰 구간의 위 끝 L(LUT L 점 = 앵커). 동률은 작은 L이다.
- gm/ID 범위: 동치류 멤버의 §6 출발 구간 [gm/ID_lo, gm/ID_hi] 안의 LUT gm/ID 점(P "탐색 gm_id 가능역으로 한정", I-A15: 격자 전체 중앙값을 쓰지 않는다).
- VDS·VSB: S0 수준 필드 `start.point`의 그 소자 값이다(40 §2.4.8).
- 축약(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-4 "knee 축약 = 합집합 앵커(중복 제거, 늘어난 앵커 수 기록)"): 가능역의 gm/ID 점·멤버마다 잰 knee 앵커의 합집합(중복 제거)을 쓴다. 늘어난 앵커 수를 `knee_anchor_union{class, n_anchors}`로 기록한다.
- knee는 LUT와 숫자 인자(kind, w_key, gm/ID 점, VDS, VSB, LUT L 격자)만의 순수 함수다. 그래서 LUT memo `memo.call(knee_fn, ...)`에 둔다(40 §2.4.6 순수성 규칙).

**feasible_L_window(새 엔진 정의)**. 원천은 history §10.11 "선언된 `W_bounds`와 그 소자의 실제 ID로 그리는 'W 한계 안에 들어오는 L 구간'"이다.
- 소자 d: {L ∈ LUT L 범위 : W(L) = ID_d · L / IDu(gm/ID_d, L, VDS_d, VSB_d) ≥ W_min} ∩ {W(L) ≤ W 상한, 선언이 있을 때}. W_min은 PDK `core` 선언이다. 새 엔진에는 W 상한 선언이 없으므로 면적 예산이 있을 때만 §6.4-5의 W ≤ A_budget/L을 쓴다.
- history §10.11의 선언 `W_bounds`는 옛 spec 필드이고 새 spec에는 없다. 이 정의는 그것을 위 두 경계(PDK W_min, 면적 예산 W 상한)로 **대체**한다(§5.12.1 E5).
- diode 멤버는 VDS = VGS(gm/ID, L)로 계산한다(history §10.11 diode 분기).
- 동치류의 창 = 멤버 창의 교집합이다. ID·gm/ID·VDS는 현재 바퀴 값이다.
- 창이 비면 `l_window_empty`이고, 그 동치류가 든 후보는 국소 실현 불가다(LR5 확장 조건 'W 한계').

**동치류 격자**(P LR5 "동치류마다 초기 격자 = {knee 앵커와 인접 앵커} ∪ {`feasible_L_window` 하한 앵커}"):
- G_c = {knee 앵커, 그 위·아래 이웃 LUT L 점} ∪ {window 하한을 담는 LUT L 점}. window 밖 점은 뺀다.
- 역산 시작 후보: (b) 결과 L_inv를 감싸는 같은 bin의 두 LUT L 점을 G_c에 더한다(P LR5 "층 0의 이득→VA→L 역산 결과 ... 그 L을 감싸는 같은 bin의 LUT L 점을 이 격자의 시작 후보로만 쓰고, 격자를 대체하거나 줄이지 않는다").
- **넓히기**(P LR5 "블록이 실현 불가(W 한계, 블록 gain 상한 < 목표)이거나 한 칸 넓힌 격자에서 두 목적 축에서 비지배로 개선되는 점이 생기고 그 개선이 축마다 max(그 축의 분해능, 모델 오차) 이상이면 그 동치류 격자를 인접 앵커 한 칸씩 넓히고, 개선이 없거나 LR3·LR6 경계에 닿으면 멈춘다"):
  - 시도: G_c 양쪽 이웃 앵커 한 칸을 그 bin 국소 front에서 전력이 가장 작은 점의 나머지 값에 얹어 평가한다.
  - 개선 판정(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-8 "비지배 개선 + 개선된 축마다 개선량 >= max(분해능, 모델 오차), 모델 오차 미측정이면 분해능 + '추정'"): 넓힌 앵커의 점이 그 bin 국소 front에 비지배로 들어가고, 개선된 축마다 개선량이 max(그 축 분해능, 모델 오차) 이상이면 개선이다. 모델 오차가 미측정이면 분해능만 쓰고 '추정'으로 표시한다.
  - 멈춤: 개선 없음, LUT L 범위·bin 지도 끝(LR3), §6.4-4 속도 상한(LR6의 봉인 전 추정). **v1.15.1(계획 v6.38.2 DEC-105 (6) -- LR6 개정)**: matching은 L 하한을 만들지 않으므로(면적 조건은 §6.4-2의 gm/ID 하한) 옛 '§6.4-2 matching 하한' 멈춤 경계는 지운다.

#### 5.3.8 후보 집합 (DEC-71 (4) "역산은 후보를 만드는 수단이고 격자를 대체하지 않는다")

P: "LR5 동치류 격자와 내층 DP는 그대로이며 역산 결과는 그 격자의 시작 후보이고, 검증·폴백·미세조정은 격자가 한다."

블록 i, 목표 bin b의 후보:
1. **역산 후보**: 역산 대상 동치류 c마다, 나머지 동치류를 초기 목표(§5.3.7)에 두고 c를 (b) 역산한 점. 근이 있는 L bin마다 하나씩이다(§5.3.5). (a)·(c)·(d)는 §5.3.6 고정점이 함께 푼다.
2. **검증 후보**: 1의 L_inv를 감싸는 두 LUT L 점. 나머지 값은 그 역산 후보와 같다.
3. **자유·폴백 후보**: S 자유 축과 F 폴백 축의 gm/ID 격자(§5.3.3), (b)가 폴백한 동치류의 LR5 격자 G_c. B 소자는 축이 아니다 -- 고리 종속이면 후보마다 R6 블록 값(§5.3.4), 아니면 §6 가드 구간 선택점(§5.3.3 B 행). 열거는 §5.3.11이다.
4. **넓히기 후보**: §5.3.7 넓히기.

각 후보는 §5.3.6 고정점을 거친 뒤 국소 봉인 한 번(§5.3.9)으로 판정한다. 폐기: v1.5 §5.3 축 표('소자 그룹별 gm/ID = LUT gm/ID 격자점', 'L 동치류별 L = LUT L 점'을 모든 후보의 축으로 두는 곱).

#### 5.3.9 국소 봉인과 국소 결과 저장 (DEC-71 (5), 40 §2.4.4·§2.4.5·§2.4.8·§2.4.11)

신규 `E/sizing/size_and_seal_local.py`:

```python
def size_and_seal_local(ctx: KernelContext, theta_block: Mapping[str, float],
                        fixed: Mapping[str, float], columns: frozenset[str]) -> GraphSnapshot
```
- 계산 블록 ②~⑤를 `columns`에 속한 소자·노드에만 적용한다. 그 밖의 값은 `fixed`에서 읽는다. 블록은 분할 계산 블록이다(분할 key = 기둥 id 또는 `shared:<기둥>`, 40 §2.4.4).
- 봉인 1·2·6·7과 덮는 기둥의 독립 KVL·KCL만 검사한다. 독립 KVL 수 = 덮는 기둥 수 − 분기 노드 트리 차원 + R-1′ 그래프의 독립 순환(기둥 밖 게이트 경유 순환 포함 -- 계획 v6.38 DEC-71 (5), P5).
- **R-1′ 관계식 거르기**(계획 v6.38 LA-1 범위 11 → headroom-chain HC-1 범위로 이관, 사용자 결정 O-126·O-43 D2): 칸 대표 후보를 이 함수에 넣기 **전에** headroom-chain HC-1의 거르기 함수 하나로 거른다(한 좌표 부등식은 상자 자르기, 여러 좌표 관계식은 시험점 거르기). 이 호출은 §5.3.4 (c-3) 판정과 같은 함수 호출이다(두 번 판정 0). 거른 후보는 봉인하지 않고 거른 수·아낀 커널 호출 수를 그 자리를 배선한 card의 판정 기록에 낸다. **배선 card**: HC-1과 LA-1 가운데 나중에 병합되는 card가 세 자리(이 국소 봉인 후보·§5.5 조립점·§5.5 수리점)를 배선한다 -- LA-1이 먼저면 HC-1이 새 층 0 세 자리에 배선하고, HC-1이 먼저면 LA-1이 세 자리를 만들 때 HC-1 함수를 부른다(만들면 배선, 사본 금지; LA-1이 배선하면 계획 완료 조건 2 (c)).
- tol_I는 그 후보 자기 동작점의 `device.dc_gm` 필드 × tol_V다. 부모 스냅샷에 의존하지 않는다(40 §2.4.11, 사용자 결정 G-3').
- `theta_block`에는 §5.3.6 결과(ln IDu, L 동치류 L, W4 노드전압, θ 전류)가 들어간다.
- **반환값은 층 0 국소 층의 graph 스냅샷이다**(40 §2.4.1 층 0 국소 층).
  - 봉인 통과 여부와 실패 레코드는 그 스냅샷의 봉인 필드다.
  - 국소 전력·면적은 `graph/local: power_w, area_m2`, 국소 gain·rout 모드 Z_out은 국소 gain 필드다(40 §2.4.8 해당 행, writer = 국소 봉인 블록, 키 = 덮는 기둥 집합). 국소 AC는 봉인을 통과한 점에서만 계산한다.
  - graph 밖에 결과 사본(옛 `LocalSeal{gain_db, power_w, area_m2, snapshot_fragment}`)을 두지 않는다.
- **찾기**(40 §2.4.5 S3 메모리 색인):
  - `local(블록 키, 기둥, θ_block 지문, fixed 지문) -> 스냅샷 | None`: 같은 후보의 국소 스냅샷을 찾는다. 실행 안에서는 늘 보존되므로 스냅샷을 준다(40 §2.4.5 v1.11 -- 옛 '놓았으면 요약'은 대상 소멸). 찾으면 다시 봉인하지 않는다.
  - `solved(블록 키, bin, 고정 입력 지문) -> bool`: 그 (bin, 고정 입력 지문)을 이미 풀었는지. 회차 2 이상의 '미해결 쌍'(§5.3.2) 판정이 쓴다.
- **보존**(40 §2.4.5 v1.11 보존 규칙, 사용자 결정 X-2): 실행 수명이다. 국소 front 점의 국소 스냅샷(조립의 이식 원천, 회차 사이 재사용)과 조립점 스냅샷은 실행이 끝날 때까지 남는다. 옛 소유자 '층 0 단계(모든 회차)'·'외층 시작점 대기열'은 폐지(history).
- 폐기: v1.6 초안의 `sctx.local_seal_memo`(상한 있는 graph 밖 memo)와 `LocalSeal` 값 사본.

#### 5.3.10 고정 입력 (K1·K3·K8, 블록을 가로지르는 L 동치류)

P DEC-71 (3): "국소 확정 금지 소자 ... 의 gm_id·L은 국소 단계에서 **고정 입력**으로 쓴다 -- 첫 회차는 스펙에서 유도한 출발 구간 값(design 41 §6)이고 LR5 knee 앵커는 추가 후보로 넣으며(R29 수용, 사용자 2026-10-08), 이후 회차는 직전 조립점 값이며, 국소 AC 이득 계산의 부하 gds가 이 값에서 온다."
- 첫 회차: §6 출발값을 쓴다. **모든 고정 입력 동치류**에 knee 앵커(§5.3.7)와 LR5 종류 앵커(레플리카 종류면 window 하한 앵커)의 합집합을 **추가 후보**로 같은 bin에서 한 번씩 더 평가한다(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-9 "R29 를 좁히지 않음 -- 고정 입력 동치류 전부에 knee + LR5 종류 앵커(레플리카는 window 하한) 합집합"). 폐기: v1.5의 기록 `lr5_knee_anchor_unavailable`.
- 이후 회차: 직전 조립점 값.
- 고정 입력은 (a)·(b)의 역산 대상이 아니다.

#### 5.3.11 후보 열거와 종료

- 순서: 목표 bin 순서(§5.3.2) 안에서 역산 → 검증 → 자유·폴백 → 넓히기 순서다.
- 격자 곱 Π = Π_S(S 자유 축) × Π_F(F 폴백 축) × (L 폴백 동치류의 LR5 격자)를 쓴다. matching 그룹·궤도로 묶인 소자는 축 하나다(§5.3.3). B 소자·V_R·종속 W4는 축이 아니다(§5.3.3·§5.3.4, DEC-104 L-11 개정). 좌표 하나만 걸린 R-1′ 변(층 0 처리 변)의 S 정의역 자르기(R5′ (4)(iii) -- headroom-chain HC-1 '한 좌표 부등식은 상자 자르기')는 그 S 축의 격자 점 수를 줄인다 -- Π는 자른 뒤의 축 길이로 센다.
- **정지와 절단의 구분**(**결정**(사용자 결정 2026-10-12 "U-63은 (가)로", U-63), 사용자 결정 2026-10-12 P-1 "DEC-76 경로 열거 상한 초과 = 정지(unsupported_rule_branch), 좌표 훑기 축소 탐색 폐기"의 적용을 좁힌 것):
  - **정지**(`unsupported_rule_branch`, STRUCTURE_UNRESOLVED, 탐색 전)는 둘뿐이다. (a) DEC-71 (3) 경로 열거 수가 DEC-34 예산 상한을 넘을 때(DEC-76 안전망, 가지 단위 축소는 두지 않는다). (b) 후보 격자 곱 Π가 계수 예산 N_S(§0, L-10)를 넘을 때 -- `unsupported_rule_branch{rule: layer0_candidate_grid_over_budget, block, bin, Π, N_S}`. 둘 다 시간과 무관한 결정론 판정이고 단계 A·B 경계에서 한 번 한다.
  - **절단**(정지 아님): N_T,i(§5.8)는 평가 상한일 뿐이다. 후보는 축 index의 반분 단계 순(끝점 → 중점 → …)으로 평가하고, N_T,i나 블록 벽시계에 닿으면 멈춘다. 그때 `layer0_candidates_truncated{block, bin, Π, evaluated}`를 기록하고, 그 블록의 국소 front를 '추정'으로 표시한다(그 뒤 조합 front·`gain_budget_db`도 '추정').
  - 강결합 그룹 좌표 훑기(v1.6 초안)는 폐기한 채로 둔다.
  - 실측(§5.8 표): 후보 격자 곱 최대는 pushpull_follower_buffer vout Π_F = 52,675이고 N_S = 13,829,760보다 작다. 그래서 library 9회로 중 (b) 정지는 0이다. N_T,i에 따라 절단될 수 있는 블록은 pushpull vout 하나다(sf_pushpull vout은 35로 줄었다).
- 같은 θ는 다시 봉인하지 않는다. `local(...)`로 찾은 국소 스냅샷을 재사용한다(§5.3.9). 블록 몫 예산에는 적중도 한 번으로 센다.


### 5.4 블록 국소 front

- 블록마다 `{gain bin → (전력, 면적) 비지배 점}`을 만든다(DEC-71 (6)).
- bin b의 점 = 국소 봉인을 통과하고 국소 gain ≥ T_b인 점 전부다(§5.2). 그래서 높은 bin을 충족하는 점은 그보다 낮은 bin의 front에도 든다.
- **같은 점 접기**(P DEC-71 (6) "두 점의 블록 이득 차가 모델 오차 이하이고 면적 차가 면적 축 bin 폭 이하이며 전력 차가 목적값 분해능 이하이면 같은 점으로 접어 하나만 남긴다"): 칸에 넣기 전에 적용한다. 남기는 점은 칸 규칙과 같다. 모델 오차가 미측정이면 분해능만 쓰고 '추정'으로 표시한다(§0).
- (gain bin, 면적 bin) 칸 하나에는 전력이 가장 작은 점 하나만 남긴다. 전력이 같으면 포화 여유가 큰 점을 남긴다(P DEC-71 (3) "두 축 값이 같은 칸에 든 점끼리만 포화 여유 최솟값이 큰 점을 남긴다").
- 칸 수(gain bin 수 × 면적 bin 수)가 계수 예산 N_S를 넘으면 DEC-80 예산 게이트를 적용한다. bin 폭을 2배로 넓히고 그 배수를 기록한다. 더 넓혀도 칸 배치가 바뀔 수 없으면 멈추고 `resolution_gate_unmet`을 기록한다(as-built 유지).
- 바이어스 기둥(gain bin 없음)은 면적 bin만으로 센다(DEC-71 (6)).
- 목표 bin에 봉인을 통과한 점이 없으면 `local_infeasible{block, bin, reasons}`(N3.14)을 남긴다. 처리는 조립이 다른 조합을 고르는 것이다(DEC-71 (5)).

### 5.5 조립 (M6)

**미지수**: y(K1~K4)와 공유량이다. 공유량은 공유 노드 전압, 블록을 가로지르는 `equal_vgs`의 공통 VGS, 미러 비, `kvl_branch` 종속 gm/ID, 폴딩 노드 전류다.

**풀이**(사용자 결정 2026-10-12 #1, graph core **graft** 연산, 정의는 40 §2.4.4): 조합에 든 블록 국소 스냅샷들에서 입력 버전이 맞는 블록 필드를 조립 스냅샷으로 이식하고, 공유량 필드만 GB7 커널(writer plan 등식)로 다시 계산한 뒤 전역 봉인을 한다. 별도 솔버를 두지 않는다. 이식된 필드는 다시 계산하지 않는다(같은 입력 버전 재계산 0, 결정 (4) G-10).

**조립 = 확인**(계획 v6.38 DEC-71 (7)·DEC-73 -- P6): 등식(공유 노드 K4·공유 VGS K2·`stacked_vsb` K3·적층 헤드룸·`kvl_branch`)은 KVL·KCL 기저(`dc_current_basis` 가지 전류 기저와 기둥 KVL -- 커널과 같은 쓰기 계획의 θ 고정 풀이)로 **확인**한다. 고리 정합의 **구성**은 §5.3.4와 출발 단계의 DEC-104 R6 블록(§6.7-11)이 한다 -- 게이트·저항 κ를 지나는 사슬 헤드룸은 §5.3.4 VDS·V_R 배분이 정합으로 만든다(계획 LA-1 범위 2). 조립점은 커널 평가 **전에** R-1′ 관계식 거르기(§5.3.9와 같은 HC-1 함수)를 지난다.

**수리**(v1.15.0에서 바뀐 것만 -- 계획 v6.38 DEC-73 (3)·LA-1 범위 6, 사용자 결정 O-128 Q2(M9), **원래 취지와 다름(승인 O-128)**): 수리 후보 좌표는 θ의 독립 성분(S·F 밀도, θ 전류, L)뿐이다. 종속 성분(B 밀도·V_R·종속 W4)은 R6 블록이 다시 파생하고, 실패 writer가 종속 성분뿐이면 수리하지 않고 탈락 기록을 남긴다. 수리점(`_repair` 이분 시험점)도 커널 평가 전에 R-1′ 관계식 거르기를 지난다(LA-1 범위 11 세 자리). 층 0 무동작 회로·층 0 조립 실패 경로의 출발점 경로(빈 사다리 상자 중심 출발은 E-32로 삭제, 그 밖 출발점 생성기의 존치는 **계획 v6.38.4 대기(P4)**, §5.10-3; `_box_centre`·`_current_centre`·`_halton_probe`·사다리 칸 순회)도 θ의 독립 성분만 정하고 종속 성분은 R6 블록이 파생한다(상자 중심은 독립 성분에만 -- O-128 Q2, 근거 감사 W-3 대체). **이 판 범위 밖**: 계획 LA-1 범위 6의 수리 단계 전체(수리점 규칙 (A)~(C), `_repairable` 범위, `layer0_repair_dropped_dominates`)는 v1.14.2까지 41에 설계되지 않았다(LA-1 착수 조건 (1) 'design 41 §5 개정'의 몫 -- v6.38 이전부터 있던 design 공백, 42 D-LA1rep 행).

**공유 VGS 선택**(DEC-10):
- 그룹 g를 공유하는 블록 수를 m_g라 하면, 각 블록의 국소 값 m_g개를 후보로 커널을 m_g번 돌린다.
- 봉인을 통과한 후보 중 전회로 `gain_ss_db`가 가장 큰 것을 고른다. gain 차가 b_gain 이하면 전력이 작은 쪽을 고른다(U-14 기본안). 전회로 `gain_ss_db`를 잴 수 없으면 블록 분해 보고 `full_gain_db`를 쓰고 출처를 기록한다.
- **그룹이 여럿이면**(M6): 정준 순서로 한 그룹씩 고른다(좌표별). 앞 그룹에서 고른 값은 뒤 그룹을 평가할 때 고정한다. 커널 호출 수는 Π m_g가 아니라 Σ m_g다.

**기록**: 국소 값과 전역 값의 차(ΔVGS, Δ노드전압, Δgm_id, Δ블록 gain)를 남긴다.

**`comp_approx_gap`**(DEC-92 (2), §3). 조립에 성공한 점마다 다음을 기록하고 판정에는 쓰지 않는다.
- `approx`: 그 조합의 블록 점들이 쓴 §6.5 매크로 망이다(블록마다 자기 점의 gm_req,i와 자기 출력노드 C_n, 보상 수동소자는 조립된 θ의 값). 여기서 pencil 극점·영점 목록 [Hz], UGF [Hz], PM [deg]을 구한다.
- `mna`: 조립점 봉인 스냅샷에서 구한다. (G, C) 일반화 고유값의 극점·영점 목록 [Hz](DEC-92 (4)), `ugf_ss_hz`, `pm_ss_deg`.
- `gap`: ugf = mna − approx [Hz], pm = mna − approx [deg]. 두 쪽 모두 같은 정의의 스칼라라 짝이 정해진다.
- 극점·영점 목록은 두 쪽을 그대로 싣고, 원소별 차는 기록하지 않는다(L-7).
- 위치: 조립 스냅샷의 `comp_approx_gap` 필드다(40 §2.4.8 해당 행). `Layer0Budget.assemblies[k]`는 그 필드를 읽는 보기다. front 점 기록은 그 필드를 참조한다.
- 극점·영점 목록은 원본을 보존한다(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-7 "comp_approx_gap = UGF·PM 스칼라 차만 기록, 극점 목록 원본 보존").

**시도 상한**: 조립 커널 호출 수는 조합 front 크기와 N_T,0(§5.8)의 남은 몫 중 작은 쪽이다. 조립이 실패하면 다음 조합으로 간다. 성공한 조립점은 모두 외층 시작점으로 넘긴다(as-built 유지).

### 5.6 조합 DP와 front

- **상태**: (블록 k, 누적 gain bin, 누적 면적 bin)이다. 값은 그 상태의 최소 전력 경로다.
- **누적 gain**: 고른 이득 블록 점의 목표 T_b 합(= `allocated`)에 버퍼 블록 몫을 더한 값이다. 섞인 회로(P-15)에서는 버퍼 블록이 면적 bin만 가진 DP 단계이고, 그 몫은 고른 버퍼 점의 실제 국소 gain을 gain bin 아래 끝으로 내린 값(보수)이다. 버퍼 국소 문제가 무동작인 블록(rout 미선언)은 기준점 블록 분해 gain을 상수항으로 쓴다(옛 U15 as-built(§5.10-1 항목 4)와 같은 규칙 -- U15 전체판은 master에 병합되지 않았다, 계획 F-LA6; card LA-1이 구현). 점의 실제 국소 gain은 T_b 이상이므로 이 합은 보수적이다. 폐기: v1.5 as-built 7 '대표 경로의 정확한 gain 합'.
- **종료**: 누적 gain ≥ G − b_gain이다.
- **r̂의 쓰임**: 측정되어 있으면 '누적 gain + r̂'가 큰 순서로 조립에 넘긴다. 종료 조건에는 넣지 않는다.
- **출력**: 종료 상태 중 (전력, 면적) 비지배인 조합 front와, 조합마다 `gain_budget_db.allocated`를 낸다.
- **동률**(사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" D1 "DP 단계 동률 = 최소 포화 여유 비, 조립·봉인 뒤 조합 front 동률 = 계획대로 활성 제약 여유 합"):
  - DP 단계(조립 전): 전력, 블록 MOS 최소 포화 여유 비 (VDS − VDSAT)/VDSAT, 이름 정렬 순. 국소 단계에는 전회로 활성 제약 여유가 없다.
  - 조립·봉인 뒤 조합 front: 전력, 활성 제약 여유 합(DEC-71 (6)), 이름 정렬 순. 여유는 조립 스냅샷의 `graph/metrics: constraint_rows`(40 §2.4.8)에서 읽는다.
- **상태 수 상한**: 계수 예산 N_S(§0)다. DP는 커널을 부르지 않으므로 평가 예산과 섞지 않는다(N4). 넘으면 DEC-80 게이트를 쓴다(면적 폭 먼저, 면적 bin이 하나면 gain 폭). 더 넓힐 축이 없으면 `state_count_over_budget`으로 끝난다(as-built 유지).

### 5.7 출력과 override

**front 점마다 내는 값**: `gain_budget_db.allocated`, `gain_budget_db.realized`(최종 봉인 스냅샷의 블록 gain), 두 값의 차, `gain_residual_db`, `comp_approx_gap`(§5.5).

**`gain_budget_db_override: [{block: [<출력노드 넷 이름>...], value_db, source}]`**(블록 키는 §1.7-3의 정렬 배열):
- 그 블록의 목표 bin을 value_db를 담는 bin 하나로 고정한다. §5.3.2 범위 규칙 대신 이 bin만 푼다.
- 블록 키가 없으면 `SchemaRejectedError(override_block_unknown)`이다.
- A_i,max가 인증되어 있고 value_db > A_i,max + b_GB4,i이면 INFEASIBLE_TARGET이다.
- A_i,max가 미상이면 받아들인다. 그 bin에 봉인을 통과한 후보가 없으면 `local_infeasible`을 보고한다(H3).
- `override_source`를 기록한다.

### 5.8 평가 예산 N_T (DEC-34 식, 단계 B·C 전용, M10·N4)

P DEC-34: "실측 시간으로 계산한다(식: N3.5). 이 식은 **예산 상한 계산 용도**이고".

**정의**: 커널 평가 횟수 예산(상한).

N_T = floor((B − T_used − T_reserve) / t_eval)

| 기호 | 뜻 |
|---|---|
| B | `wall_clock_budget_s` |
| T_used | 지금까지 쓴 시간. §5.3.6 고정점의 LUT 계산 시간도 여기에 든다 |
| t_eval | warm 평가 시간의 중앙값. 첫 평가가 끝나기 전에는 정의되지 않는다. 국소 봉인 시간도 같은 목록에 넣는다 |
| T_reserve | 외층 최소 비용 = 끝점 2개 × (as-built `slsqp_outer` maxiter 식 Σ⌈log2(폭/h)⌉) × t_eval. 선언 E_B가 있으면 N_T = E_B − (커널 + 국소 평가 수) − T_reserve이고, T_reserve는 기준점 FD 스텝으로 센다 |

외층이 꺼지면(DEC-75 외층 스위치) T_reserve = 수리 몫(`_repair` 수리 단계의 평가 -- 계획 LA-1 후속 정정 v6.19 행)이다. 외층 예약분은 T_reserve로 **한 번만** 뺀다. N_T는 그렇게 뺀 뒤의 층 0 몫이므로, N_T에서 다시 빼지 않는다(N4).

**t_eval 첫 측정**(계획 LA-1 후속 정정 v6.19 행): 첫 국소 봉인 또는 첫 조립점 커널 평가에서 잰다(옛 'as-built `layer0_center` 시작점 하나를 먼저 평가' 삭제). 그 뒤로 평가할 때마다 중앙값을 갱신하고 N_T를 다시 계산한다.

**평가 1회**: 국소 봉인 1회 또는 커널 1회다. §5.3.6 고정점 바퀴는 커널을 부르지 않으므로 평가 수에 들지 않는다(시간은 T_used에 든다).

**블록 후보 수(이 개정이 바꾸는 것)**:
- 목표 bin 하나: n_{i,b} = Π_S × Π_F × N_L + 넓히기 후보 수. N_L = Σ_c (n_Lbin,c × 3) + Π_{c ∈ L 폴백} |G_c|(L 격자 쪽 후보).
  - Π_S = S 자유 축 격자 곱, Π_F = F 폴백 축 격자 곱이다(없으면 1). B는 축이 아니다.
  - c = 역산 대상 동치류, n_Lbin,c = 근이 있는 L bin 수, 3 = 역산 1 + 감싸는 LUT L 점 2(§5.3.8)다.
- 블록 전체: n_i = Σ_b n_{i,b}. 실제 평가는 N_T,i가 상한이고, 닿으면 절단·'추정'이다. 정지는 Π > N_S일 때뿐이다(§5.3.11).
- 목표 bin 범위가 미상(§5.3.2)이면 n_i는 평가 전에 알 수 없다. 이때는 n_i 대신 N_T를 쓴다.

**실측**(2026-10-12, as-built bd19cc6 읽기 전용, 스크립트 `wt/_tmp_l0design/measure_l0.py`·`measure_axes.py`, 결과 `results.jsonl`·`axes.jsonl`):
- **ID 출처**: 9회로 블록 MOS 102개 중 ID가 KCL·선언으로 정해진 소자는 0개이고, 블록 밖 MOS 40개 중에서는 2개다. 그래서 (a)의 'ID가 정해진 경우' 역산은 발동하지 않고, S 소자는 자유 변수 축이 된다(§5.3.3).

| 회로 | 블록 MOS | 입력 셀 | ID 고정 / θ 전류 | kvl 종속(`cycle_vgs`) | 블록 밖 MOS(고정 / θ) |
|---|---|---|---|---|---|
| common_gate_amplifier | 2 | 1 | 0 / 2 | 0 | 0 / 1 |
| current_reuse_telescopic_ota(단계 A 정지) | 25 | 8 | 0 / 25 | 6 | 1 / 25 |
| folded_cascode | 11 | 2 | 0 / 11 | 1 | 0 / 2 |
| ngcc_3stage_ff(review_needed) | 11 | 4 | 0 / 11 | 1 | 0 / 5 |
| nmcnr_amplifier(review_needed) | 15 | 4 | 0 / 15 | 1 | 0 / 0 |
| pushpull_follower_buffer | 4 | 0 | 0 / 4 | 1 | 0 / 2 |
| sf_pushpull_output_opamp | 19 | 2 | 0 / 19 | 2 | 1 / 2 |
| two_stage_ota | 7 | 3 | 0 / 7 | 1 | 0 / 0 |
| two_stage_ota_sf | 8 | 3 | 0 / 8 | 1 | 0 / 1 |

- **L-11 적용 뒤 격자 크기**(층 0이 도는 6회로). 실측(2026-10-12, as-built bd19cc6 코드 읽기 전용 + §6.7-1a 쓰기 계획 모사(같은 DC `input_tie` 엣지 제거), 'kvl 종속' 제외, `wt/_tmp_l0design/measure_v4.py`, 결과 `v4.jsonl`). as-built `_jobs` gm/ID 축을 §5.3.3 종류로 나누고, matching 그룹으로 묶인 축은 하나로 셌다. 축 크기 = §6 구간 안 LUT gm/ID 점 수. X = kvl 종속(쓰기 계획 `cycle_vgs`·`fixed_vgs`)이라 축에서 빠진 것. 출력 follower의 E10(S)은 축 수를 바꾸지 않아 F 열에 그대로 둔다.

| 회로(GBW 목표) | 블록(모드) | S 자유 축 → Π_S | F 폴백 축 → Π_F | B 축(제외) | X(kvl 종속) | L 동치류 | as-built Π |
|---|---|---|---|---|---|---|---|
| common_gate_amplifier(없음) | vout(gain) | 없음 → 1 | 35(input, 매크로 비활성) → 35 | 43 | 없음 | 2 | 4.9·10⁵ |
| folded_cascode(없음) | out(gain) | 없음 → 1 | 36(input 쌍), 44(cascode 쌍) → 1,584 | 25, 25 | 없음 | 7 | 2.4·10¹⁹ |
| folded_cascode | bias:6 | 1 | 1 | 35, 34 | 없음 | 0 | 1,190 |
| pushpull_follower_buffer(없음) | vout(rout, 버퍼만) | 1 | 35, 35, 43 → **52,675** | 없음 | 43(M3) | 4 | 2.4·10¹¹ |
| sf_pushpull_output_opamp(60 MHz, PM 하한 경로) | Y(gain) | 16(M1; M2는 kvl 종속) → 16 | 1 | 36, 42, 42, 15 | M2 | 9 | 5.0·10²³ |
| sf_pushpull_output_opamp | vout(버퍼, P-15) / bias:6 | 1 / 1 | 35 → 35 / 1 | 없음 / 13 | 42(M21) / 없음 | 2 / 0 | 4.8·10⁵ / 13 |
| two_stage_ota(7 MHz, PM 목표 없음) | O1 / OUT(gain) | 15 / 44 | 1 / 1 | 18 / 없음 | 없음 | 3 / 1 | 2.4·10⁷ / 792 |
| two_stage_ota_sf(7 MHz, PM 목표 없음) | O1 / OUT(gain) | 14 / 30 | 1 / 1 | 14 / 없음 | 없음 | 3 / 1 | 1.6·10⁷ / 540 |
| two_stage_ota_sf | vout(버퍼, P-15) | 1 | 36(follower) | 없음 | 없음 | 1 | 648 |

- **함의**: gain 제약이 있는 3회로의 블록은 bin 하나당 Π_S = 14~44에 N_L(동치류 1~9개 × 근 있는 L bin × 3)을 곱한 수준이라 전수가 가능하다. 모든 블록의 Π가 N_S보다 작아 P-1 (b) 정지는 0이다. pushpull vout(52,675)은 N_T,i에 따라 절단·'추정'이 될 수 있다. gain 제약이 없는 회로(cga, folded)는 매크로가 비활성이라 S가 비고 input·cascode가 F로 남지만, gain 모드 층 0 자체가 꺼진다(§5.1).
- 단계 A·B를 넘지 못하는 3회로(current_reuse_telescopic_ota 정지, ngcc·nmcnr review_needed)는 층 0이 돌지 않는다(§5.1).

**층 0 안 배분**(배분 규칙은 v1.5와 같다. 새 배분 상수 없음):
- 블록 몫: N_T,i = max(1, N_T × min(n_i, N_T) / Σ_j min(n_j, N_T)).
  - N_T,i는 평가 상한일 뿐이다. 닿으면 정지하지 않고 절단한다(`layer0_candidates_truncated` 기록, 블록 front '추정', §5.3.11). 정지는 경로 열거 예산 초과와 Π > N_S뿐이다(결정 -- 사용자 결정 2026-10-12 "U-63은 (가)로").
- 조립 몫: N_T,0 = N_T − Σ_i (블록 i가 실제로 쓴 평가 수).
- 벽시계: 층 0은 외층 몫(T_reserve · t_eval)을 남긴 시각까지 돈다. 블록마다 남은 시간을 남은 몫 비로 나눈 시각에서 끊는다.
- 국소 봉인 호출은 `counters["layer0_local_calls"]`로 따로 센다. `kernel_calls == 고유 키` 불변식은 유지된다.

**외층 ε 점 수**(40 §3.6-5): 층 0이 끝난 시점의 시간으로 같은 식을 다시 계산한다(T_reserve 없이).

**LUT memo 상한의 층 0 항**(결정 -- 사용자 결정 2026-10-12 "U-60은 (가)로", U-60 = (가), 40 §2.4.6과 같은 문장, 검토 M6 선택지 (가)):
- U_L0,r = Σ_i K_max,i · (U_pass,i,r + U_macro,i,r). 블록 i의 **첫 후보**에서 한 번 세고, N_T,i를 곱하지 않는다. 퇴출은 허용하고 `perf`에 보고한다. 퇴출된 키를 다시 계산하면 FAIL이다(U-60 (가)).
  - U_pass,i,r = 블록 i 첫 후보의 고정점 한 바퀴(§5.3.6)가 영역 r에서 센 서로 다른 LUT 키 수다.
  - U_macro,i,r = 같은 바퀴의 매크로 호출(§5.3.6)이 센 서로 다른 LUT 키 수다.
  - K_max,i = 그 바퀴의 N3.6 반복 상한(§5.3.6)이다. 첫 후보가 수렴 전에 멈춘 경우에도 상한 K_max를 곱한다.
- 층 0이 꺼진 회로는 0이다. 계수 방식은 40 §2.4.6이 정본이다.

**기록**: `perf`에 N_T, t_eval, 블록 n_i·몫·사용 수, 고정점 바퀴 수 합, NONCONVERGENT 수, 폴백 수(사유별), 소진 여부를 쓴다. 계수 예산 N_S는 §0의 정의를 따른다.

### 5.9 외층 인계 (M7)

- 외층 SLSQP는 조립점에서 시작한다. 블록 gain은 제약에 넣지 않는다(DEC-05·74).
- **외층 변수 = θ의 독립 성분**(계획 v6.38 DEC-73·DEC-70 M11 -- 사용자 결정 O-128 Q2, **원래 취지와 다름(승인 O-128)**: 옛 '정의역 변수 전체 + 칸이 구간인 L'): S·F ln IDu·θ 전류·L(칸이 구간인 것)·보상 수동소자 θ 연속 성분. 고리 종속 성분(B ln IDu·V_R·종속 W4)은 외층 변수가 아니고 점마다 DEC-104 R6 블록(§6.7-11)이 다시 파생한다. 외층 탐색 공간에서 B·W4·저항 축이 빠지는 척도·front 영향은 미측정 -- card LA-1 변화표의 원인 항목(계획 문언 그대로). as-built `E/search/slsqp_outer.py`은 정의역 변수 전체를 쓴다(gap, 42 행 70).
- **근방 반경**(40 §3.10.8 '근방 반경 확장 규칙'): 초기 r_j = max(|θ_j,local − θ_j,assembled|, h_j), h_j = 그 성분의 격자 분해능. 그 반경 안에 feasible이 없으면 반경을 2배로 넓힌다(DEC-80 예산 게이트와 같은 2배, 새 상수 아님). 멈춤: 반경이 전역 bounds에 닿거나, 확장에 쓴 평가 수가 DEC-34 예산 식의 남은 몫을 넘을 때. 층 0은 전역 bounds를 줄이지 않는다.
- **외층 봉인 스냅샷의 재개방 표지**(계획 DEC-104 R5′ (4)(iii) ③ 재검증 G-1 ③, **원래 취지와 다름(계획 표지, 승인 O-162)**): 외층(SLSQP) 봉인 스냅샷에서 R6이 '이득 행 재개방' 표지를 세워도 기록만 하고(`graph/start: loop_dep`의 `reopen` 칸 -- 층 0 스냅샷에서는 §5.3.2 고정 입력 지문이 읽는 소비 대상이고, **외층 스냅샷에서는 소비자 없음 -- 기록만**(계획 LA-1 완료 조건 9 (c) 측정 기록), v1.15.2 검증 m-4 표기 정정) 층 0을 다시 열지 않는다(외층은 L을 bin 안 연속 변수로 이미 다룬다 -- LR10). toy = 계획 LA-1 완료 조건 9 (d) 외층 표지 toy.
- ε 스윕의 첫 ε는 조합 점의 면적과 전력이다.
- r̂는 이미 평가한 받아들인 점에서 먼저 재고, 모자라면 Halton 시험을 표본 수 이하로 한다(`residual_probe(pool=, trials=)`). front 점의 `allocated`는 그 점의 풀이 사슬이 시작한 조립점의 조합에서 온다(`sweep_front` `roots`).

**불변식**: 층 0은 전역 bounds를 줄이지 않는다. 같은 입력이면 같은 조합 front다. 평가 계수는 `perf`에 남긴다.

**실패**(계획 LA-1 후속 정정 v6.19 행·LA-Q2(O-38 (1)) 둘 갈래): (i) 결합 오차(봉인 통과·전회로 제약 미달)는 외층을 켜는 정상 경로(대체 경로 아님) (ii) 봉인 실패로 조합 소진은 '층 0 점 없음'·'성능 판정 보류' 표기 대체 경로(DEC-73 (3)(b) 한 규칙) -- 그 경로의 출발점은 40 §3.11-2 칸 0 한 규칙이고 모든 후보가 출발 불능이면 출발 불능 보고(E-32); 그 경로의 출발점 생성기(`_box_centre`·`_current_centre`·`_halton_probe`·사다리 순회)의 존치·삭제는 **계획 v6.38.4 대기(P4)**. 옛 '§6 시작점 → `SearchFailedError`'는 이 둘로 대체.

**상태**: (기록 -- v1.14, U15: '`E/search/layer0_center.py`는 국소 기준점 생성, t_eval 첫 측정, 대체 시작점에만 쓰인다'; t_eval 첫 측정은 v1.15.2에서 §5.8로 바뀜, 남는 역할은 P4) v1.15.2 -- 빈 사다리의 상자 중심 출발(`layer0_center.py:654-656`)은 계획 N6.35 E-32로 삭제(출발 불능 보고·성능 판정 보류 -- 40 §3.6·§3.11-2); `layer0_center` 역할(계획 후속 정정 v6.19 행 '= `_repair` 수리')과 층 0 점 없음 경로의 출발점 생성기 존치는 **계획 v6.38.4 대기(P4)**.

### 5.10 as-built(U15) 대조와 구현 변경 목록

호출 경로(유지 -- 옛 U15 전체판 기준: U15 전체판은 master에 병합되지 않았고(계획 F-LA6) 엔진에 `layer0_budget`이 없다, card LA-1이 구현 -- §5.1 861과 같은 표지): `find_front` → `layer0_start`(기준점 = 국소 기준점·첫 t_eval·대체 시작점) → `layer0_budget` → 시작점(조립점 → §6 시작점 → S3 → x0, 없으면 `SearchFailedError`) → E_B 재유도(40 §3.6-5) → `sweep_front`.

**1. v1.5 §5.10 as-built 항목의 처리** = design 이력 H41-18(폐기·유지 판정 기록 -- 현행 규칙은 각 절).

**2. 구현 변경 목록**(U15 코드 기준. 파일은 `E/search/` 아래, 따로 적은 것 제외)

| 대상 | 유지 / 변경 |
|---|---|
| `gain_bins.py`(`BinGrid`, 게이트) | 유지. 'bin b 충족 = gain ≥ T_b' 판정 함수를 더한다 |
| `local_front.py` | 변경: 점이 충족하는 모든 bin에 넣는다(§5.4). 칸 규칙은 유지 |
| `combo_dp.py` | 변경: 누적 gain = T_b 합 + 상수항(§5.6). 상태·동률·게이트는 유지 |
| `assembly.py` | 변경: 조립 = graph graft(40 §2.4) + 공유량 필드 재계산 + 전역 봉인. `comp_approx_gap` 기록을 더한다(§5.5) |
| `budget_override.py` | 유지. override = 목표 bin 고정(§5.7) |
| `local_candidates.py` | 변경: 후보 = §5.3.8 집합, 축 = S 자유·F 폴백만(B·FF 제외, matching 그룹·궤도 = 축 하나, §5.3.3). 평가 루프(계수, 벽시계, 반분 순서)는 그대로 쓰고, 좌표 훑기는 지우고 P-1 규칙(Π > N_S 정지, N_T,i 절단 + `layer0_candidates_truncated`·'추정', §5.3.11)으로 바꾸며, `local_seal_memo` 대신 S3 메모리 색인 `local(...)`·`solved(...)`(40 §2.4.5)를 쓴다. `lr5_knee_anchor_unavailable` 삭제 |
| `layer0_budget.py` | 변경: 첫 배분 g_i^(1)(L-2 found_db 비례, §5.3.2), 목표 bin 범위·순서(§5.3.2), n_i 몫(§5.8). `REC_KNEE_UNAVAILABLE` 삭제. 일감(`_jobs`)·기둥·고정 입력·예산·DP 루프는 유지 |
| `_helpers_place.theta_from_choice` | 변경: θ = §5.3.6 결과(S·F ln IDu, 연속 L, θ 전류 -- 독립 성분) + R6 블록이 파생한 종속 성분(B ln IDu, V_R, 종속 W4 노드전압 -- §5.3.4, v1.15.0) |
| `_helpers_rows.model_row` + `E/metrics` U9 `row_gains` | 변경: 축 값을 격자 index로 맞추지 않고 동작점 연속값으로 평가한다(L은 bin 안 선형, 나머지는 DEC-87 운영 보간). A_i,max 표(§4.2)는 격자 그대로 둔다 |
| 신규 `layer0_inverse.py` | (a) gm/ID 역산(`lut.vgs_for_gm_id`, §4.1 분류), (c) VDS·V_R 배분 = R6 블록 호출(블록 본체는 §6.7-11 -- 이 파일은 부르기만 한다, v1.15.0), (b) L 역산, (d) 국소 고정점(`sizing.k_max`·q 판정 재사용), 노드 C(`ss.node_c_farad`와 같은 함수) |
| 신규 `l_targets.py` | knee, feasible_L_window, 동치류 종류(주인 기준), LR5 격자·넓히기 |
| `E/sizing/size_and_seal_local.py` | 변경: 반환 = 국소 graph 스냅샷. 국소 전력·면적·gain은 블록 범위 metric 필드다. tol_I = 자기 dc 단계 gm 필드 × tol_V(§5.3.9) |
| 신규 A9 블록 `block_bounds_l0`(§4.2) | 추가: 층 0 정의역 상한 A_i,max^L0(축 규칙 §4.2, 단계 A9, S0 필드 `start.row`·`start.point`를 읽음, '추정', 40 §2.4.8 A9 행). 축소 전 표와 exit 3은 그대로 둔다 |
| §6.5 매크로(`macro_poles.macro_solve`) | 변경: 키워드 전용 인자 `node_c`·`gm_bounds`·`gain_targets`를 추가한다(§5.3.6). 공동 SLSQP·다중 출발은 그대로 둔다. 기본 호출은 as-built와 비트 동일이고 test가 `fp_of`로 확인한다. 결정 9 §6.7-4 B3의 기본 호출과 호환된다 |
| 커널 θ(40 §3.7-5) | W4 자유 노드전압 θ를 층 0 값으로 받는지 확인하고, 받지 않으면 writer 계획의 W4 초기값 입력을 더한다 |

**3. 범위 밖 항목과의 접점**
- **결정 9(§6.7 KVL 고리 출발 제약, 사용자 결정 2026-10-12 "K-1~K-3도 권고대로", 같은 문서 §6.7)**:
  - **공동 선택(7a) 결과가 들어오는 자리**:
    - (i) 고리 종속 멤버(`cycle_vgs`·`fixed_vgs`)의 gm/ID는 층 0이 고르지 않는다. W2 쓰기 계획이 정한다(§5.3.3 `kvl_dependent`).
    - (ii) (v1.15.0 개정, 계획 DEC-104 R5′·R6) 7a가 위치를 옮긴 writer 묶음 가운데 **B 묶음은 층 0의 고정 입력(READS)**이다 -- 구성원이 모두 출발 단계에서 정해지는 고리는 출발 스냅샷의 R6 블록 값을 graph reuse로 읽고, 층 0 결정 변수가 섞인 고리는 후보마다 같은 R6 블록이 다시 파생한다(§5.3.4). S·F 묶음의 7a 선택점은 층 0 첫 회차의 출발값이다(블록 안 소자면 §5.3.6 첫 바퀴 값이자 §5.3.11 자유·폴백 열거에서 그 축의 첫 점, 고정 입력 소자면 §5.3.10 고정값). 옛 문언 '7a가 위치를 옮긴 writer 묶음의 선택점은 층 0 첫 회차의 출발값'(B 포함)은 L-11 개정으로 대체.
    - (iii) §6 구간은 (a) 역산과 폴백 격자의 정의역이다(§6.7 "구간은 그 역산의 정의역").
  - **placer**: 유지한다.
    - 역할은 θ 조립에서의 KCL·미러 전류 전파와 최소 폭 보정이다(§6 '같은 식').
    - 층 0이 정한 gm/ID·L·W4·θ 전류는 placer의 선택을 덮어쓴다. §6.7-6 "U15 `placer.place`(덮어쓴 묶음은 고정, 나머지만 변수)"와 같은 규칙이다.
    - placer는 층 0 안에서 7a를 다시 돌리지 않는다.
  - **`layer0_center._maxmin`·`_box_centre`**(gap 다름 2 자기모순 정리): **계획 v6.38.4 대기(P4)** -- 계획 LA-1 범위 6은 `_box_centre`(빈 사다리·출발 정의 불능 칸 대체로는 안 씀)·`_current_centre`·`_halton_probe`·사다리 순회를 '층 0 점 없음 경로의 출발점 생성으로만 존치'로 두고, E-32는 빈 사다리의 상자 중심 출발만 지운다. 이 design이 확정하는 것은 E-32 몫(빈 사다리 → 상자 중심 출발 없음, 출발 불능 보고)과 층 0 손계산 경로(활성 회로)에서 이 함수들을 부르지 않는다는 것뿐이고, 칸이 정하지 않은 성분의 상자 중심·전류 중심 출발의 물리적 필요·존치 여부는 계획 결과를 따른다(v1.15.2 둘째 커밋의 '`_box_centre`·`_current_centre` 출발 경로 삭제' 문장은 계획보다 앞서 정한 것이라 철회). 첫 t_eval = 첫 국소 봉인 또는 조립점 커널 평가(§5.8). 출발점 경로에서 정하는 것은 θ 독립 성분뿐이고 종속 성분은 R6 블록(§5.5 '수리'). 옛 문장 '§6.7-2의 저항 기하 중심은 `_box_centre`와 같은 값이다'는 삭제한다 -- §6.7-2는 값 미선언 저항을 상자 중심이 아니라 V_R 미지수(R-1′ 차분 변)로 다룬다(계획 DEC-104 (4), O-127 (iii)). `_maxmin` 소비자가 0이 되는지는 LA-1 착수 때 확인하고 0이면 삭제 후보로 적는다(삭제는 승인 뒤 -- 계획 LA-1 범위 6).
  - B1 "(a) 필요 gm -> gm/ID 역산, (c) VDS 배분(A1·A4 와 함께)"은 §5.3.3·§5.3.4와 같은 함수를 쓴다. §6.7-4 B3 매크로 재확인은 `macro_solve` 기본 호출이다(§5.3.6 불변 조건).
- **A7 → P-15(결정됨)**: 섞인 회로의 버퍼 블록에도 rout 국소 제약(§5.1, §5.6).
- **A8**: 차동쌍 완화. §5.3.3 입력 셀 gm_id 역산의 대상 집합이 바뀔 수 있다.
- **A9 → P-9(결정됨)**: N3.7 9회로 축소 격자 전수 대조는 §9 검증 항목이다. 층 0 결과를 바꾸지 않는다.
- **A10**: 접점 없음.

### 5.11 계획 조항 → 설계 절 대응표

| 계획 조항 | 요지 | 설계 절 |
|---|---|---|
| DEC-71 (3) 입력·첫 회차 배분 | GB4 비례 시작 배분(L-2: 축소 전 GB4 `found_db` 비례), 이후 조립 조합 | §5.3.1, §5.3.2 |
| DEC-71 (3) gain bin 고정 | bin마다 따로 푼다 | §5.2, §5.3.2 |
| DEC-71 (3) AC 제약 | 국소 gain ≥ 예산, 출력 임피던스 기록 | §5.2, §5.3.1, §5.4 |
| DEC-71 (3) 고정 입력 | 첫 회차 §6 + knee 추가 후보, 이후 조립점 | §5.3.10 |
| DEC-71 (4)(a) | gm_id = gm/ID 역산 | §5.3.3 |
| DEC-71 (4)(b), LR3 | 목표 gain → L 역산, bin 안 선형, bin 넘지 않음 | §5.3.5 |
| DEC-71 (4)(c) v6.38, DEC-104 R5′·R6, IC4, WP-03 | R-1′ 구간 (c-1) → 무변화/재개방 (c-2, W4·V_R = R5′ (2) 행 여유 max-min) → 정확 풀이 판정 (c-3) -- (c-4) 삭제(O-155 M-2) | §5.3.4, §6.7-11 |
| DEC-104 (0)·(1) | θ 기저·우선순위 P0~P6, 결정 순서(N1.1 v6.38) | §5 머리말, §6.1 |
| DEC-104 R3·R4 | 필요 gm = 매크로 블록 하나, S의 ID = max(gm_req/(gm/ID), R8 하한) | §5.3.3, §6.5, §6.8 |
| DEC-104 R7·(3)(b) | B 밀도 = (가) 선언 범위 고리는 R5′ (1) 나머지 경계(이득 저하 정의 시 공동 집합 끝), (나) 그 밖은 고리 나머지 ∩ 가드 안 K-1 max-min + '열린 결정'(U-124); 가드 필드(소자별 구간 + 합 행, card LA-1 범위 15 (d)) | §5.3.3, §6.7-11, 40 §2.4.8 `device: start.guard` |
| DEC-104 R8·R10 | 공급 요구 하한(정상상태 + 동적) | §6.8, §5.3.1 |
| DEC-104 R13·(3)(a) | S/B/F/X 분류 S0 필드(card TB-1) | §5.3.3, 40 §2.4.8 `device: theta_class` |
| DEC-104 (3)(d), headroom-chain N3.1·N3.4 | 고리와 변 좌표 집합 = R-1′ 제약 그래프 S0 필드 변 속성 | §5.3.4, §6.7-1·-3, 40 §2.4.8 R-1′ 행 |
| DEC-104 (4), DEC-70 v6.38 | V_R 결정·R 파생·spec 상자 | §5.3.3 'θ 저항', §5.3.4, §6.7-2 |
| DEC-73 (3) v6.38 | 수리 좌표 = 독립 성분만 | §5.5 '수리' |
| LA-1 범위 9 | 보고 분류 출력 자리 | §5.1 '보고 분류 출력 자리' |
| LA-1 범위 11(→ HC-1) | R-1′ 거르기 세 자리, 배선 card = 나중 병합 card | §5.3.9, §5.5 |
| LA-1 범위 13(B85) | 매크로 gm의 θ 전류 전파 | §6.5 '전류' |
| N3.8 '정착 측정 정의' 엔진 쓰임, U-118 | 대역폭 출발 목표 '추정'(필요조건 아님 -- O-157 S3) | §6.8-2 |
| DEC-71 (4)(d), DEC-70 (c), N3.6 | 기생 C 국소 고정점, 같은 수렴 규칙 | §5.3.6 |
| DEC-71 (4) 폴백 | 그 소자만 격자, 사유 기록 | §5.3.3, §5.3.5, §5.3.8 |
| DEC-71 (4) "역산은 후보 수단" | 격자가 검증·폴백·미세조정 | §5.3.8, §5.3.11 |
| DEC-71 (5) | 국소 봉인 | §5.3.9, §5.4 |
| DEC-71 (6), DEC-77, DEC-80 | bin별 비지배 점, 칸, 게이트, DP | §5.4, §5.6 |
| DEC-71 (7), DEC-10 | 조립, 공유 VGS | §5.5 |
| DEC-71 (8), DEC-73 | 전역 정합·외층 인계 | §5.9 |
| LR5, DEC-16, DEC-19, I-A15 | knee, window, 동치류 격자, 넓히기, 역산 시작 후보 | §5.3.7 |
| DEC-92 (2)(4), N3.7 보상 규칙 | 근사식 = 층 0 시작점, `comp_approx_gap` | §5.3.6, §5.5 |
| DEC-34, N3.5 | 예산 상한 식 | §5.8 |
| DEC-72 | gain bin 폭 = 모델 오차, 미측정 '추정' | §5.2, §5.3.7 |
| 40 §3.7-5 | W4 초기값 = 층 0 VDS·V_R 배분의 W4 전압(R-1′ 구간 안) → y | §5.3.4 |
| 사용자 결정 L-3·L-11·L-12 (2026-10-12) | 회차 반복, 소자 종류 S/B/F, 층 0 정의역 상한 | §5.3.2, §5.3.3, §4.2 |
| 40 §2.4 graph 저장(사용자 결정 #1·#2·G-3') | §2.4.4 graft, §2.4.5 색인·보존(`local`·`solved`, v1.11 블록 결과 색인·실행 수명 보존 -- 옛 소유자 '층 0 단계(모든 회차)'·'외층 시작점 대기열' 폐지), §2.4.6 LUT memo, §2.4.8 필드 소유(매크로 결과·국소 gain·Z_out·`comp_approx_gap`·A9·회차 기록), §2.4.11 tol_I | §5.3.2, §5.3.6, §5.3.9, §5.5, §5.8, §4.2 |
| DEC-64 v2 | 고리 종속 멤버 gm/ID는 등식이 정함 | §5.3.3, §5.10-3 |
| DEC-67, DEC-91 (2) | 봉인 전 C_n '추정', 레이아웃 전 확산 기하 | §5.3.6 |
| DEC-71 (6) 같은 점 접기 | 접은 뒤 칸에 넣음 | §5.4 |

### 5.12 결정 기록 -- 설계가 더한 정의, 사용자 결정, 계획과 다른 점

#### 5.12.1 설계가 더한 정의 (사용자 결정 L-13으로 승인)

사용자 결정 2026-10-12 "L1~L13 모두 권고대로 해" L-13 "design 추가 정의 E1~E9 승인(E4 위·아래 끝 규칙의 A^L0 사용 부분과 E9 축 규칙은 검증 Major-1 수정 후, E8 은 FF 처리 Major-2 수정 후)". E4·E8·E9는 그 수정을 반영한 아래 문안이다.

| # | 정의 | 절 | 근거 |
|---|---|---|---|
| E1 | (b) L 역산의 일반형: 블록 국소 gain(L_c) = T_b를 L 동치류 c마다 **하나씩** 푼다. 나머지 동치류는 §5.3.7 초기 목표에, gm/ID·VDS는 현재 바퀴 값에 둔다. 근이 있는 L bin마다 후보를 하나 낸다 | §5.3.5, §5.3.8 | DEC-71 (4)(b), 방법론 §6.7 Phase 2 |
| E2 | 층 0 매크로 호출: 키워드 전용 인자 `node_c`·`gm_bounds`·`gain_targets`, 공동 풀이 유지, 기본 호출 비트 동일 | §5.3.6 | DEC-92 (2), §6.5 as-built 퇴화 기록 |
| E3 | VDS 배분 한 걸음 = LUT VDS 격자 간격. 나머지는 지나는 모든 기둥의 여유를 지킬 때만 준다 | §5.3.4 | DEC-71 (4)(c) |
| E4 | 목표 bin 범위: 위 끝 = max(A^L0 bin('추정'), 역산 실패 bin), 아래 끝 = 축소 전 A_max 인증일 때의 유도 또는 창 하한 clamp 반복 | §5.3.2 | DEC-71 (3) "bin마다 따로 푼다" |
| E5 | feasible_L_window의 W 경계 = PDK W_min, 면적 예산 W ≤ A_budget/L(옛 `W_bounds` 대체) | §5.3.7 | history §10.11 |
| E6 | 국소 고정점 변화량에 L 환산 항 \|∂VGS/∂L\|·\|ΔL\| | §5.3.6 | N3.6 지표 규칙 |
| E7 | knee 동률은 작은 L이다. 동치류 종류는 L 주인의 종류다 | §5.3.7 | LR1·DEC-17 |
| E8 | L-11 소자 종류의 구조 정의: S = 주경로 이득 블록 AC 역할 `input`(매크로 활성 = GBW 목표 있음, PM 없으면 PM 하한 경로), B = `load`·`mirror`·`diode_load`·`tail_source`·블록 밖 소자·**FF 셀**(§6.5 출발값 고정 -- v1.15.0: 옛 '외층이 다듬음'은 L-11 개정(계획 DEC-104, O-128 Q2(M3))으로 삭제), F = `cascode`·`pass`·`follower`·매크로 비활성 회로의 `input`. matching 그룹·궤도로 묶인 S·F 소자는 축 하나. v1.15.0: 이 정의는 S0 필드 `device: theta_class`(TB-1, R13)의 값 정의이고, 매크로 활성에 '정착 선언 있음 + GBW 미선언'(선언 사실)을 더한다(계획 N3.8 '정착 측정 정의' 엔진 쓰임·R13 재검증 n8) | §5.3.3 | 사용자 결정 L-11, 재검증 Major-2·Minor-3·Minor-4, 계획 DEC-104 R13 |
| E9 | A^L0 축 규칙: (S∪F) gm/ID + L 전부 + 전류·저항 + 덮는 기둥 W4 VDS 격자, B VGS·VS는 S0 필드 `start.row`·`start.point`로 고정, 단계 A9, 늘 '추정' | §4.2 | 사용자 결정 L-12, 재검증 Major-1 |

#### 5.12.2 사용자 결정 기록 (L 번호 ↔ 이 문서 Q 번호)

| L | 옛 Q | 결정 원문(사용자 2026-10-12) | 설계 위치 |
|---|---|---|---|
| L-1 | Q1 | "계획 DEC-71 (4) "(I-A11)" 인용 오기 -> "N3.7 LUT 곡선 검사"로 계획 정정" | §5.3.3 폴백 사유, 계획 정정은 §5.12.3 D4 |
| L-2 | Q2 | "첫 회차 배분 = 축소 전 GB4 found_db 비례, 값 없는 블록만 기준점 블록 gain 보완, '추정' 표시(A^L0 비례는 쓰지 않음)" | §5.3.2 |
| L-3 | Q3 | (기승인) "2회차 이후 = 고른 조합의 미해결 (bin, 고정 입력 지문)만 재풀이, 조합 front 불변이면 정지, 상한 K_max(DEC-70 반복 자리 추가 포함)" | §5.3.2, D3 |
| L-4 | Q4 | "knee 축약 = 합집합 앵커(중복 제거, 늘어난 앵커 수 기록)" | §5.3.7 |
| L-5 | Q5 | "격자 폴백은 L-11 범위 밖(F 종류)에만, 정의역 §6 구간" | §5.3.3 |
| L-6 | Q6 | "L bin = 근이 있는 bin 마다 후보, 국소 front 가 고름" | §5.3.5 |
| L-7 | Q7 | "comp_approx_gap = UGF·PM 스칼라 차만 기록, 극점 목록 원본 보존(§6.5 옛 문장 정리)" | §5.5, §6.5 |
| L-8 | Q8 | "L 격자 넓히기 개선 = 비지배 개선 + 개선된 축마다 개선량 >= max(분해능, 모델 오차), 모델 오차 미측정이면 분해능 + '추정'" | §5.3.7 |
| L-9 | Q9 | "R29 를 좁히지 않음 -- 고정 입력 동치류 전부에 knee + LR5 종류 앵커(레플리카는 window 하한) 합집합" | §5.3.10 |
| L-10 | Q10 | "bin·DP 상태 상한 = 계수 예산 N_S 유지, 계획 DEC-71 (6)·DEC-80 문구 정정(NFR-4 결정론)" | §0, §5.4, §5.6, D2 |
| L-11 | -- | (기승인) "필요 gm 정의된 신호 소자만 gm/ID 자유변수(ID = gm/(gm/ID)), 부하·미러·바이어스는 §6 구간·미러비·KCL 로 정하고 격자 곱에서 제외" | §5.3.3 |
| L-12 | -- | (기승인) "GB4 블록 gain 상한 계산도 신호 소자 축만으로 축소 후 재측정" | §4.2 |
| L-13 | D1, E1~E9 | "design 추가 정의 E1~E9 승인 ..., D1 ... DP 단계 동률 = 최소 포화 여유 비, 조립·봉인 뒤 조합 front 동률 = 계획대로 활성 제약 여유 합; 계획 DEC-70 "세 곳뿐"·DEC-71 (4)(d) "세 번째" 정정(넷째 반복 자리)" | §5.12.1, §5.6, D1, D3 |
| L-14 | Q11 | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 축소 상한은 층 0 전용(첫 배분 제외, bin 위 끝 보조), exit 3·§6.4-1은 축소 전 표 | §4.2, §5.3.2(이미 반영) |

**L-14 결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"). 근거: 축소 상한은 상위집합의 상계가 아니고(§4.2 '추정'), 직전 측정에서 축소 값(54.5 dB)이 축소 전 격자 일부 값(67.7 dB)보다 낮았다. exit 3에 쓰면 gain 57 dB 회로를 잘못 멈출 수 있다.

#### 5.12.3 계획과 다른 점·계획 문언 정정

| # | 내용 | 계획 원문 | 설계 | 처리 |
|---|---|---|---|---|
| D1 | 조합 동률의 둘째 기준 | DEC-71 (6) "전력이 작은 쪽, 동률이면 활성 제약 여유 합이 큰 쪽" | DP 단계 = 최소 포화 여유 비, 조립·봉인 뒤 조합 front = 활성 제약 여유 합(§5.6) | L-13 결정. DP 단계만 계획과 다르다 |
| D2 | bin·DP 상태 게이트 예산 | DEC-71 (6)·DEC-80의 "DEC-34 예산 식에서 계산한 평가 수" | 계수 예산 N_S(§0) | L-10 결정. 계획 DEC-71 (6)·DEC-80 문언 정정 |
| D3 | 층 0 회차 반복 = DEC-70 넷째 반복 자리 | DEC-70 "반복은 (a) ... (b) ... (c) 층 0 국소 고정점 ... 세 곳뿐이다", DEC-71 (4)(d) "DEC-70이 세는 반복 자리에 (c) 층 0 국소 고정점을 세 번째로 추가" | (d) 층 0 회차 반복(§5.3.2)을 넷째로 더한다 | L-3·L-13 결정. 계획 DEC-70 "세 곳뿐" → "네 곳뿐", DEC-71 (4)(d) "세 번째"에 '(d) 회차 반복은 넷째' 추가 정정 |
| D5 | DEC-81 복합 블록 묶음 크기 상한 | DEC-81 "묶음 크기가 DEC-34 예산 식의 평가 수를 넘으면 `unsupported_rule_branch`" | 계수 예산 N_S(§1.9) | **결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-65, 계획 DEC-81 정정). L-10과 같은 이유(결정론) |
| D4 | 비단조 폴백 근거 인용 | DEC-71 (4) "LUT 비단조 구간(I-A11)" | N3.7 'LUT 곡선 검사'와 §4.1 | L-1 결정. 계획 인용 정정 |

#### 5.12.4 축소 전 A_i,max 인증 현황 (실측, L-2 근거)

(2026-10-12, as-built bd19cc6, 읽기 전용 스크립트 `wt/_tmp_l0design/measure_l0.py`, 결과 `results.jsonl`. A^L0는 §4.2 표)

| 회로 | 단계 A / B | gain 제약 | 이득 블록 | A_max 인증 / 미상 | 미상 사유(Π) | `found_db` |
|---|---|---|---|---|---|---|
| common_gate_amplifier | ok / ok | 없음 | 1 | 0 / 1 | `grid_product_over_budget`(1.9·10¹⁰) | 53.4 |
| folded_cascode | ok / ok | 없음 | 1 | 0 / 1 | 같음(6.2·10⁵²) | 119.3 |
| pushpull_follower_buffer | ok / ok | 없음 | 0(버퍼 1, 미상) | -- | -- | -- |
| sf_pushpull_output_opamp | ok / ok | 있음 | 1(+버퍼 1, 미상) | 0 / 1 | 같음(3.4·10⁸⁰) | 없음 |
| two_stage_ota | ok / ok | 있음 | 2 | 0 / 2 | 같음(1.7·10²², 1.9·10⁹) | 61.2, 67.7 |
| two_stage_ota_sf | ok / ok | 있음 | 2(+버퍼 1, 인증 −0.7 dB) | 0 / 2 | 같음 | 61.2, 67.7 |
| current_reuse_telescopic_ota | stopped / -- | 있음 | 3 | 단계 B 없음 | `unsupported_rule_branch`(cs_output_low_impedance, J-C) | -- |
| ngcc_3stage_ff | review_needed / -- | 없음 | 3 | 단계 B 없음 | -- | -- |
| nmcnr_amplifier | review_needed / -- | 없음 | 3 | 단계 B 없음 | -- | -- |

#### 5.12.5 P·K·C 결정 반영과 남은 질문 (2026-10-12)

**결정 반영**:

| 결정 | 원문 | 41 위치 |
|---|---|---|
| P-1 | "DEC-76 경로 열거 상한 초과 = 정지(unsupported_rule_branch), 좌표 훑기 축소 탐색 폐기" | §5.3.11, §5.8, §5.10, §9 |
| P-9 | "9회로 축소 격자 전수 대조 추가(N3.7, NFR-5)" | §9 |
| P-15 | "이득 블록과 섞인 회로의 버퍼 블록에도 rout 국소 제약(DEC-71 (3))" | §5.1, §5.3.3 F 행, §5.6, §5.8, §5.10 |
| K-1 | "KVL 고리 공동 선택 기준 승인 -- 위반 최소 -> 가장 낮은 위치 최대(max-min) -> 위치 합 최대, ..." | §6.7-4·10 |
| K-2 | "β·C_eff 근사 정의는 design 검증에서 지적이 없을 때 승인(지적이 있으면 다시 묻는다)" | §7.5, §6.7-10 |
| K-3 | "input_tie(U2 기본안 (a)) 폐기, 대칭 포트는 U2 자기동형 묶음(domain.ties)이 대신, 구현 순서는 결정 6(d/s 맞바꿈) 다음" | §6.7-1a·10 |
| C-2 | "(가) Cs1·Cs2 kT/C 선언하지 않음, 300 uV 는 OTA 소자 잡음 적분(폐루프 귀환 조건)으로 판정. 적분 대역은 논문에 명시 없음(spec 의 대역 정의 유지)" | §6.4-3, §7.1, §7.3, §7.5, §7.6, §9 |
| Q1(2026-10-08) R3 복원 | 40 §8 R3은 "Q1~Q11 모두 네 의견대로 진행해" Q1로 복원 | §4.5 |

**설계가 더한 정의(승인 대상)**:

| # | 정의 | 절 | 근거 |
|---|---|---|---|
| E10 | 버퍼 블록(rout 제약)에서 블록 출력노드에 source가 닿는 follower는 필요 gm이 rout 제약으로 정의되므로 S다. 한 출력노드의 여러 follower는 공통 배율 하나로 Z_out = `rout_ss_ohm`을 푼다(§5.3.3) | §5.3.3 | L-11 "필요 gm 정의된 신호 소자만 gm/ID 자유변수"를 rout 제약에 적용. P-15 |

**남은 질문**(계획이 정하지 않은 것):

| # | 쟁점 | 계획 원문 | 선택지 | 권고 |
|---|---|---|---|---|
| PQ1 | P-9 '축소 격자'의 정의 | N3.7 "전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색(다른 모델)과 대조한다"(무엇을 어떻게 줄이는지는 없음) | (i) A^L0와 같은 축(§4.2: S∪F gm/ID, L 앵커, W4 VDS, 전류·저항, B는 §6 값)을 축마다 반분 단계 순으로 줄여 Π ≤ N_S가 되게 함 (ii) θ 성분 전부를 축마다 같은 점 수로 균등 추출 (iii) 회로별 선언(spec `verification.reduced_grid`) | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): (i). B 고정 가정은 이 대조로 검증되지 않음을 보고에 기록한다. 층 0과 다른 모델(전회로 MNA)이고 같은 정의역이라 대조의 뜻이 분명하다. 다만 B 고정은 층 0과 같은 가정이라, 그 가정 자체는 이 대조로 검증되지 않는다 |
| PQ2 | P-1 정지 범위(검토 M1) | DEC-76 "만들지 않은 폴백이 필요한 입력이 실제로 오면 ... 탐색 전 정지" | (i) Π > N_T,i 정지(직전 판) (ii) 정지는 경로 열거 초과와 Π > N_S뿐, N_T,i는 절단 + '추정'(§5.3.11) | **결정**(사용자 결정 2026-10-12 "U-63은 (가)로", U-63): (ii). 재측정(kvl 종속 제외·`input_tie` 제거)으로 최대 Π = 52,675(pushpull vout) < N_S라 library 정지 0, 절단 가능 블록은 pushpull vout 하나 |
| PQ3 | 섞인 회로에서 rout 미선언 버퍼 | DEC-71 (3) "그 선언도 없으면 그 블록은 '층 0 무동작'으로 보고하고, 그 회로는 층 0 없이 출발 구간 시작점으로 탐색" | (i) 그 블록만 무동작, 나머지 층 0은 돈다(설계) (ii) 회로 전체 층 0 끔(문언) | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): (i). 그 블록만 층 0 무동작 + 보고. 문언은 버퍼만 있는 회로를 두고 쓴 것이고, 이득 블록 예산은 그대로 정의된다. 현재 library 해당 회로 0 |
| PQ4 | E10 승인 | -- | 승인 / 출력 follower도 F | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 승인. 한 출력노드에 follower가 둘 이상이면 공통 배율 하나로 Z_out = `rout_ss_ohm`을 푼다(E10, §5.3.3 -- §5.3.6 공동 풀이와 같은 변수 하나라 결정론) |
| PQ5 | §6.7 P1: KVL 등식을 단계 A8 출발 선택에도 거는 것 | DEC-71 (7)·N3.7 "조립 단계에서 푼다" | 유지(현 설계) / 조립에서만 | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 유지(출발 단계 A8에도 KVL 등식, 조립 처리는 그대로). 조립의 처리는 바꾸지 않고 출발점 실현 가능성만 높인다 |
| L-14 | 축소 상한 쓰임 | §5.12.2 | -- | **결정**(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지"): 축소 상한은 층 0 전용, exit 3·§6.4-1은 축소 전 표(설계 반영됨) |

#### 5.12.6 v1.15.0 -- 계획 v6.38이 design에 넘긴 이름·자리 (검증·승인 대상)

계획 v6.38이 '이름은 design'·'출력 자리는 design'으로 넘긴 것만 정한다. 새 규칙·상수·임계값은 없다(이름·자리·형식만).

| # | 정의 | 절 | 계획 근거 |
|---|---|---|---|
| E11 | S/B/F/X 분류 S0 필드 `device: theta_class` = `ThetaClass(kind ∈ {"S","B","F","X"})`, writer = 분류 블록 `theta_class`(`E/sizing/theta_class.py`, 쓰기 계획 다음 S0 블록) | §5.3.3, 40 §2.4.8 | DEC-104 R13·(3)(a), card TB-1 범위 1 |
| E12 | R7 matching·잡음 가드 필드 `device: start.guard` = B 소자별 `GuardInterval(gm_id_lo, gm_id_hi, sources)`, + 합 행(DEC-105 (5)), writer = `start_intervals` 블록(기존 §6.4-2a·§7.5 가드 계산을 옮기면서 DEC-105 (5) 규칙으로 고쳐 씀 -- 결함 이전 금지) | §6.7-11, 40 §2.4.8 | DEC-104 R7·(3)(b), DEC-105 (5), card LA-1 범위 15 (d)(U-132, 옛 TB-1 범위 3) |
| E13 | 층 0 보고 분류 `graph/layer0: report_class`(원소 `layer0_inactive`·`assembly_failed_path`·`performance_judgement_deferred`), writer `layer0_budget`, 출력 전용 | §5.1 | LA-1 범위 9·완료 조건 6·7 |
| E14 | 저항 상자 밖 탈락 기록 `resistor_out_of_box{element, R, box}`(층 0 후보 기록), 고리 위반 기록 = `local_infeasible{reason: "chain_violation"}`(층 0)·`StartConflict(quantity="kvl")`(출발, §6.6 기존 어휘) | §5.3.3, §5.3.4 | DEC-104 (0)·(4) |
| E15 | R6 블록 출력 필드 `graph/start: loop_dep` = `LoopDep(b_ln_idu, w4, v_r, reopen)`(정렬 tuple 칸 넷 -- 소자·넷·저항·행 키별; `reopen` 값 ∈ {`domain_cut`(R-1′ 정의역 자르기), `gain_reopen`(이득 행 탐색 개방)}), writer = R6 블록 `loop_dependents` 하나, 소비자 = 커널 평가 입력 조립(층 0 후보·출발 시작점 -- 참조로 읽어 점 좌표 조립, 사본 아님)·DC 블록 W4 목표(40 §3.7-A 4) | §6.7-11 | DEC-104 (3)(c), O-151 DK1 |
| E16 | 체계 오프셋 술어 인스턴스 S0 필드 `graph/start: mirror_vds_instances` = 정렬 tuple ((종류 ∈ {`P1s`, `P1c`}, 소자 키 넷 (d, o, g) 또는 (r, o, a, b), 노드 n), ...), writer = 구조 블록 `mirror_vds_instances` 하나(쓰기 계획 다음 S0 -- 연결·S1v만 읽음, topology 태그 READS 0), 신호 경로 판정 = 넷 술어 `bias_fixed_net`의 부정(S1v 순수 함수 하나 -- 'R10 모든 여기 뷰·되먹임 경로에서 신호 넷 아님', 자리 `E/graph/s1v_predicates.py`, 제작 = card IT-1 v6.38.3 범위 재작성 5(40 §3.11-5), 이 card와 SB-1은 부름 -- v1.15.2 정정, v1.15.1의 LA-1 제작 배정·옛 술어 이름은 삭제), 소비자 = R6 블록 `mirror_vds` 목표 행 | §6.7-4·§6.7-11 | DEC-105 (4), card LA-1 범위 15 (c) |
| E17 | 이득 L 하한 목표 필드 `graph/ach: gain_target_first`(writer `gain_target_first`, 소비자 = 출발 이득 L 하한·층 0 첫 회차) | §6.4-1 | DEC-105 (1), card LA-1 범위 15 (a) |

미정(근거 없음 -- 정하지 않음, 42 해당 행):
- (v1.15.1 닫힘) R6 블록 출력 자리 = 출력 필드 하나 `graph/start: loop_dep`(E15, §6.7-11 -- 계획 DEC-104 (3)(c), O-151 DK1).
- 정착 대역폭 출발 목표('추정' -- O-157 S3) 필드 이름·층과 β 읽는 점(U-118 -- LA-1 design에서 실측 뒤, §6.8-2).
- current_reuse 해결 선행(R7 가드 한 점 축소·입력 뿌리 W4 반대 방향 고리 -- 계획 LA-1 design 과제 (i), 시제품 `wt/_drafts/evidence/2026-10-26/r5r6_prototype.md` §수정판 B·J; 실측 뒤).
- (v1.15.1 닫힘) 매크로 gm의 θ 전류 전파에서 미지수 둘 이상이 남는 KCL 행 = R3 '전원 전류 최소' 변수(계획 DEC-104 R3·LA-1 범위 13 -- §6.5 '전류' 개정).
- (v1.15.1 닫힘) R10 셀 전류 = 봉인 해가 있는 스냅샷은 DE-1 R9 필드 READS, 없는 스냅샷은 블록 안 동작점 포락 하한, 구현 = card SB-1(§6.8-1 개정).

#### 5.12.7 v1.15.2 design 승인 질문 메모와 원래 취지와 다름 목록 (계획 v6.38.3 -- 40·41·42 공통; v1.15.1 판 처리는 아래 '옛 판 처리')

**승인 질문**(사용자 결정 O-171 -- 항목마다 물리 결정자·회로이론 근거·판정; 문턱 상수 없음):

| ID | 질문 | 기본안과 근거(물리·회로이론) | 판정 | 대안 |
|---|---|---|---|---|
| Q-DC1 | DC 블록 하나(40 §3.7-A)의 손계산 속도 손실을 받아들이나 | 받아들임 -- 계획 DEC-105 (2)가 블록 하나를 고정했다(물리 결정자: W = I·L/IDu라 DC 블록이 전류 열을 READS → θ 전류 FD 열마다 노드 풀이 재계산). 판단 재료 요지 = 40 §3.7-A 9(유도 손실 벽시계 0~4 %, Rʳ = ∅ 9/9라 노드 재풀이 0; 측정 원자료 evidence). 동작 변경: 봉인점의 `slice_cycle`·`finger_below_min` 점은 지금 봉인되지만 새 블록에서 봉인 실패가 된다(새로 거부되는 점 -- 계획 규칙 그대로, 바꿀지는 계획 v6.38.4 대기(P5·P8)). 손실이 크다고 판단되면 계획 개정 대상이지 design이 블록을 나누지 않는다 | 판단 재료 충분 -- 사용자 판단 | 계획 개정으로 블록 분할 재검토(R1-b) |
| Q-DC3 | 슬라이스별 tol 표 첫 구성 비용(LUT 적재 때 도달 가능 슬라이스 30개(nfet 18·pfet 12) × kind당 약 14~19 s CPU ≈ 7~10 분, 첫 실행 한 번 -- U-87 디스크 캐시 뒤 0)과 비기준 슬라이스의 L bin 중점 검증 부재 | 비용: 받아들임 -- 구성 시점을 LUT 적재로 고정해 블록 순수성 유지(40 §3.7-A 7; 물리 결정자 = tol은 LUT 보간 분해능이라 LUT 선언만의 함수). 검증 중점: 기준 폭 슬라이스에만 있는 사실을 card WB-1 착수 때 LUT 데이터로 재측정하고 비기준 슬라이스는 '중점 미검증' 표지를 보고에 남김(판정 불변) | 맞음(비용 수용은 사용자 몫) | 처음 쓰일 때 평가 안에서 구성(기각 -- 순수성·예산 얽힘), 비기준 슬라이스 중점 LUT 생성(oracle·LUT card 추가) |
| Q-PW1 | (계획 승인 질문으로 옮김) DUT 전력 정의 | **계획 v6.38.4 대기(P7)** -- 재료 = 40 §3.1-1 'DUT 전력' 참조 | -- | -- |

**고지(질문 아님)**: (1) W < W_min 점(m = 1에서 격자 반올림 w_f < W_min)은 `finger_below_min` 봉인 실패(40 §3.7-A 5 -- 계획 DEC-105 (2) 'w_f ≥ W_min'): 물리 결정자 = 제조 규칙(difftap.2) 밖 손가락은 PDK·LUT가 정의하지 않음(W_min 제약 행의 쓰임 = 40 §3.7-A 11; 바뀐 점 수는 card WB-1 변화표 원인 항목). (2) class-AB S: 'AC 구동 소자 포함' 안 기각, S = 연결 정의(손계산 꼴) -- 40 §3.5; 결합 용량 경로가 있으면 S 미정 fail-closed `zero_cancel_s_coupled` 초안, Cds 꼴 포함·최종 문언은 **계획 v6.38.4 대기(P2)**.

**옛 판 질문**: Q-DC2 → 고지 (1), Q-DC4·Q-GL1 → 삭제(O-166·O-170 승인으로 해당 없음). **원래 취지와 다름**(이 판이 새로 만든 것 -- 계획 승인 표지가 있는 항목은 계획 그대로 옮김이라 세지 않음): 없음. v1.15.1 목록·처리 경위 = `wt/_drafts/evidence/2026-10-29/design_v1152/simplify/moved_text.md` S8.

**계획 정정 후보 → 계획 v6.38.4에서 처리 중**(오케스트레이터 재판정 `wt/_drafts/evidence/2026-10-29/design_v1152_rejudge.md` §1 P1~P7, 그 뒤 P8 -- design의 해당 자리는 '계획 v6.38.4 대기' 표지만 두고 내용을 정하지 않음): (a) DEC-92 (3) '한계' 문언(P2) (b) card WB-1 완료 조건 (1) '입력 포트 W4 뿌리 꼴' 되먹임 toy -- 범위 3a(E-13) 뒤 입력 창 되먹임이 없어짐(40 §3.7-A 12) (c) 검증 C-1의 'R⁰ = ∅ 종속 소자 슬라이스 ≠ 기준 폭' toy 추가 (d) 병합 순서 의존 소유 문언('먼저 병합되는 card가 만든다' -- R9 조회 함수·`ORACLE_ONLY` 표·범위 끝 이득 함수, P6) (e) 판정 대상 집합의 저장 자리(술어 호출 여럿 대 `constraint_classes.judged`) (f) LA-1 범위 6 출발점 경로(`_box_centre`·`_current_centre`·`_halton_probe` -- gap 다름 2, P4) (g) design 입력 회차 수 문언(P5 -- 40 §3.7-A 9 측정 반영) (h) DUT 전력 정의(P7) (i) 손가락 슬라이스 선택 문언(DEC-105 (2) 'bin 안 w_f에 가장 가까운 슬라이스' -- 손가락 폭과 다른 폭의 슬라이스 값을 쓰면 bin 안 전류 밀도 비 0.54~1.74로 물리 정합이 깨짐; P8 결정 전까지 40 §3.7-A 5는 이 물리 부정합을 안은 계획 v6.38.3 문언 그대로 -- 출처 `wt/_drafts/evidence/2026-10-29/handcalc_principle_audit.md`:31·112, P8).

### 5.13 판정 경계 위에 일부러 놓는 점 (NFR-4 3안, v1.9.4)

사용자 결정 2026-10-15 "1안·3안 진행하고 ③ 기준 변경도 승인해"의 3안이다. 층 0 전류 중심에서 드러났고, 엔진 안의 같은 종류 자리(아래 표) 전부에 적용한다. 근거 요구: 계획 NFR-4(같은 입력 → 같은 산출물)와 40 §2.4.13 (2)의 '다른 실행 환경에서 이산 판단 정확 일치'.

**용어**: **경계 배치점** = 엔진이 판정 행 c ≥ 0(`ConstraintRow.c`, 분해능 단위)의 c = 0 위에 일부러 놓는 값. 풀이기가 활성 제약을 c ≈ 0으로 몰아 생긴 점은 경계 배치점이 아니다(아래 '남은 위험').

**문제**: 경계 배치점의 경계 좌표를 풀이기 수렴값에서 읽으면, 그 점의 c 부호는 풀이기 허용오차 안의 잡음이 정한다. 그 잡음은 BLAS 경로에 따라 다르다. 그래서 같은 입력에서 이산 판단이 뒤집힌다. 사례는 `E/search/layer0_center.py:238-246` 끌어올림이다(cfe2e31 실측: 주석 238-239, `lift = u` 240, 시도 루프 241-246, 반환 247 -- 옛 문장 '238-245'를 정정). 이 끌어올림은 Chebyshev 풀이(`:235`)의 목적값 u로 움직이는 θ 전류를 모두 e^u 배 해서 '가장 낮은 MOS 전류 = 기준 전류(`StartRung.current_ref`, 폭 W_min의 전류)'를 겨냥한다. pushpull_follower_buffer에서 시작점의 `w_min:M1` 행 c는 스레드 1에서 +1.13e-10, 스레드 8·18에서 −2.30e-6이다. 그래서 `hard_ok`(`:683`)의 `np.all(c >= 0)`이 뒤집힌다(같은 판정이 최선점 키 `:407`과 외층 `best` `E/search/slsqp_outer.py:230`에도 있다). 같은 결함은 스레드가 같아도 c를 0 아래로 놓을 수 있다: folded_cascode의 시작점 `w_min:M8` 행 c는 스레드 1에서 −4.68e-10이고 `hard_ok` = False다. 측정 조건은 아래 표 밑과 history에 있다.

**규칙**:
- **BP1 닫힌 식 배치**: 경계 배치점의 경계 좌표는 풀이기 수렴값에서 읽지 않는다. 그 행의 선언량(PDK·LUT·기준값)과 고정 순서 산술의 닫힌 식으로 계산하고, 판정 쪽으로 부동소수 여유 √ε(상대)만큼 안쪽에 놓는다. 풀이기 해는 '어느 행을 경계에 놓을지'를 고르는 데만 쓴다. √ε는 엔진이 같은 목적으로 이미 선언한 값이다(`E/search/start_intervals.py` `_REL`: 'W = W_min 이 정확히 경계라 반올림이 아래로 떨어지지 않게 하는 여유'). 새 상수가 아니다. **쓰는 방식(J-6, 오케스트레이터 기본안 -- 사용자 결정 아님)**: `_REL`은 비공개 이름이라 다른 파일에서 import할 수 없다(규칙 B). 그래서 `layer0_center`는 정의식 `math.sqrt(sys.float_info.epsilon)`을 그 자리에서 쓴다 -- 같은 정의식을 그 자리에서 쓰는 선례가 이미 있다(`E/search/macro_poles.py`, `E/search/iv_matching_l.py`). 근거: 값의 출처는 정의(부동소수 기계 엡실론)이고 상수를 짓는 것이 아니다. `_REL`을 공개 이름으로 바꾸거나 core에 정본을 두는 것은 `start_intervals.py`·다른 두 자리를 함께 고치는 별개 정리라 이 card 범위 밖이다(최소 변경). 여유가 필요한 까닭: 닫힌 식으로 놓아도 판정 값은 다른 산술 경로(커널 W = ID·L/exp(ln IDu) 대 기준 W_min·IDu/L)의 반올림 차만큼 0 근처에 남는다(측정: +9.53e-14 분해능 단위). √ε 여유를 두면 c ≈ √ε·W_min/grid다(측정: +1.25e-6 분해능 단위). 이 값은 반올림 수준보다 약 10^7배 크고, 활성 판정 경계(c ≤ 1, `E/search/constraints.py`)보다 훨씬 작다.
- **BP2 판정은 그대로**: 경계 배치점의 판정은 c ≥ 0 그대로다. 허용 띠(c ≥ −분해능)를 두지 않는다.
- **BP3 자기 판정식 확인**: 배치하는 함수가 판정식을 직접 가지는 자리는, 배치한 뒤 같은 식으로 확인한다. 통과하지 못하면 판정 허용오차만큼 안쪽으로 물러나 다시 확인한다.

**층 0 끌어올림의 식(BP1)**: 풀이기 해 x(θ 전류의 ln)에서 MOS 행 m(θ 전류를 하나라도 읽는 원뿔 행)마다 두 값을 잰다. A_m(x) = Σ(움직이는 θ 전류 항)/기준 전류_m이고 F_m = Σ(고정 전류 항)/기준 전류_m이다. 움직이는 전류를 e^s 배 하면 q_m(s) = A_m·e^s + F_m이다. 끌어올림 배수는 e^s = max_{m: A_m > 0} (1 + √ε − F_m)/A_m이다. 그 행은 q = 1 + √ε에 놓이고, 나머지 A_m > 0 행은 그 이상이다. u(풀이기 목적값)는 이 식에 쓰지 않는다. 원뿔이 깨지면(고정 전류·음의 계수) 올리지 않는 것과 변수 상자 클램프(`:244`)는 as-built 그대로다. **적용 조건(J-9, 오케스트레이터 기본안 -- 사용자 결정 아님)**: as-built 조건(`:240` -- 출발 사다리 칸이 있고 그 `StartRung.current_ref`가 비어 있지 않을 때만 끌어올린다)을 그대로 둔다. 근거: 끌어올림의 목적은 '모든 MOS 전류 ≥ 기준 전류 = 폭 W_min의 전류'다. 사다리 칸이 없으면 기준 전류는 kind 전류 상자의 기하 중심(`:190-193`)이라 W_min과 무관하고, q ≥ 1 + √ε는 경계 배치점이 아니다(BP1 대상 아님). 조건을 바꾸면 사다리 없는 회로의 시작점이 새로 바뀌어 3안 범위 밖 동작 변경이 된다. 측정 시제품은 F_m = 0인 경우만 구현했다(s = −min_m ln q_m(x) + ln(1 + √ε)). F_m ≠ 0인 행이 최소가 되는 경우는 착수 때 test로 덮는다.

**끌어올림 식의 가장자리**:
- A_m > 0인 행이 하나도 없다(모든 원뿔 행이 움직이는 전류에 대해 감소하거나 무관): 끌어올릴 행이 없다. s = 0(올리지 않음)이다. as-built의 '원뿔이 깨지면 올리지 않는다'와 같은 결과다.
- A_m > 0인 모든 행에서 1 + √ε − F_m ≤ 0(고정 전류만으로 이미 q ≥ 1 + √ε): 식의 최댓값이 0 이하라 ln이 정의되지 않는다. s = 0이다(이미 경계에서 여유가 있다).
- 식의 값이 s < 0(Chebyshev 해의 최소 행이 이미 1 + √ε보다 위 -- 끌어올림이 전류를 낮추게 됨): as-built `lift`는 u ≥ 0으로 올리기만 한다(`:232` u 상자 하한 0). **s = max(0, 식의 값)이다** -- as-built처럼 올리기만 한다(Q-N9 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-85).

**같은 종류 자리**(2026-10-15 grep `w_min_m`·`_REL`·`float_info.epsilon`·`bracket_root(`·클램프, tests 제외):

| 자리 | 경계에 놓는 것 | 판정 | 규칙 |
|---|---|---|---|
| `E/search/layer0_center.py:238-246` 끌어올림 | 가장 낮은 MOS 전류 = 기준 전류 | `:407`·`:683`, `E/search/slsqp_outer.py:230`의 c ≥ 0 | **BP1 위반 → 위 식으로 고친다** |
| `E/search/start_intervals.py` `current_ref` = max(scale, W_min·IDu/L) | 전류 미정 소자의 자리값을 W = W_min에 | 판정 아님(BP1 식의 입력) | BP1 준수(선언량 닫힌 식) |
| `E/search/start_intervals.py` `_width_floor_gm_id` | W = W_min·(1 + √ε)인 gm/ID | 같은 함수의 `excess ≤ 0`, 아니면 곡선 마디로 물러남 | BP1(√ε 여유)·BP3 준수 |
| `E/search/start_intervals.py` 면적 예산 경계 t | 실행 가능 판정의 경계 t | `feasible(solve(t − tol))` 재확인 | BP3 준수 |
| `E/search/iv_area.py` `w_min_gm_id` 상한 | W = W_min인 gm/ID(출발 구간 끝점) | 끝점 넘음 판정 `E/search/start_intervals.py`(√ε 상대 비교) | 구간 끝점(배치 아님) |
| `E/search/iv_matching_l.py` 입력쌍 L 하한 | σ_ΔVGS = σ_share인 L(출발 구간 하한) | 커널 판정 행의 경계가 아니다 | **해당 없음(2026-10-15 확인)**: 하한은 실제로 출발 L이 된다(측정 3 current_reuse M4a·M4b `l_chosen` = `l_lo` = 3.221e-6, `E/search/start_intervals.py` 하한 최댓값을 `_snap`이 그대로 고름). 그러나 σ_share = σ_target/√2는 입력 셀의 몫이고(`E/search/iv_matching_l.py`, `:123`), 커널 판정은 전회로 MNA `offset_in_sigma_mv`가 모든 소자 기여를 합해 한다(같은 파일 docstring '출발값 전용(EP-7)'). 그래서 이 L은 커널 판정 행의 c = 0 위가 아니다 |
| `E/search/iv_matching_l.py`, `E/search/iv_noise.py` W 클램프 max(…, W_min) | 모델 입력 W | 판정 없음(mismatch·잡음 모델 입력) | 해당 없음 |
| `E/search/layer0_center.py`, `_halton_probe` 상자 클램프 | θ를 변수 상자 끝에 | 상자는 정의역(판정 행 아님) | 해당 없음 |
| `E/search/macro_poles.py` 채택 판정 | (풀이기 해) | abs(ln abs(H)) ≤ √tol 등 허용 띠 | 배치 아님 -- 남은 위험 |
| `E/search/layer0_center.py`, `E/search/slsqp_outer.py` | (풀이기가 활성 제약을 c ≈ 0으로) | `:407`·`:683`·`:230`의 c ≥ 0 | 배치 아님 -- 남은 위험 |

**검토한 안과 측정**: 엔진 사본(`wt/_nfr4_design_scratch/repo`, master 34932a9 복제)만 고쳤다. 단계 A → B → `build_search_context` → `find_front`를 `OPENBLAS_NUM_THREADS` 1·8·18로 실행했다. 실행마다 별도 프로세스·빈 S0·빈 표 캐시를 썼다. '엔진 결정 차이' = 측정 3 이산 키에서 풀이기 호출 기록(`slsqp[…]`)과 경로 계수(nit·iterations·`n_history`·sweeps·평가 수·커널 호출 수)를 뺀 키의 차이다(40 §2.4.13 (3) D 부류). pushpull_follower_buffer:

| 안 | 내용 | 엔진 결정 차이 1 대 8 / 1 대 18 / 8 대 18 | `hard_ok` 1·8·18 | 시작점 `w_min:M1` c 1·8·18 | 판단 |
|---|---|---|---|---|---|
| 현행 | e^u 끌어올림 | 125 / 125 / 0 | T·F·F | +1.13e-10 · −2.30e-6 · −2.30e-6 | 결함 재현 |
| (a) 닫힌 식, 여유 없음 | e^s = 1 / min_m q_m(x) | 1 / 1 / 0 | T·T·T | +9.53e-14(세 스레드 같은 비트) | 경계 부호는 고쳐진다. 그러나 c가 반올림 수준이다. 남은 차이가 1건인 것은 우연이다(아래) |
| **(a2) 닫힌 식 + √ε 여유(BP1)** | e^s = (1 + √ε) / min_m q_m(x) | 125 / 125 / 0 | T·T·T | +1.25e-6(세 스레드 같은 비트) | **채택**: 경계 부호가 고쳐지고 반올림에 견딘다. 남은 125건은 경계 배치와 다른 원인이다(아래) |
| (b) 판정 허용 띠 | `:407`·`:683`·`:230`을 c ≥ −1 | 124 / 124 / 0 | T·T·T | 현행과 같음 | 기각: W < W_min 점을 경성 통과로 센다. 40 §10.5 'spec 제약 행 c ≥ 0'과 충돌한다. 경계 좌표의 잡음은 그대로다 |
| (c) 한 분해능 칸 안쪽 | e^(u + ln(1 + grid/W_min)), 목표 W = W_min + 격자 1칸 | 136 / 136 / 0 | T·T·T | 스레드 1의 최소 행 = `current_cone:M6` 1.0, 8·18 = `w_min:M1` 0.99999767 | 기각: 목표 c = +1이 활성 판정 경계(c ≤ 1)에 놓여 그 부호가 다시 잡음으로 정해진다. u의 잡음도 그대로 남는다 |

- **pushpull의 남은 차이는 경계 배치가 아니다.** (a2)에서 `hard_ok`와 시작점 c는 세 스레드가 같다. 그래도 외층 ε 풀이 `EP:s1`이 스레드 8·18에서 `L:M1` FD 열 실패로 그 변수를 고정한다(`frozen:L:M1`). 재시작이 2회에서 6회로 늘고, 평가 18번부터 다른 점을 잰다. 시작점의 경계 밖 성분은 스레드마다 다르다(`current/M4` 상대 5.6e-4, `current/M5` 4.8e-5 -- Chebyshev 풀이 `:235` 해의 잡음). 그 차이가 외층 풀이 경로를 가른다. 이 갈림은 이 규칙 범위 밖의 '남은 위험' (2)다(아래).
- (a)의 남은 1건은 `eval[35]`의 `failure.margin`이 정의되었는가다(스레드 1 = 2.08, 8·18 = None). 이 1건만 남은 것은 우연이다. (a)와 (a2)는 시작점이 √ε(상대 1.5e-8)만큼 다를 뿐인데 스레드 1에서 엔진 결정이 123건 다르다. 즉 pushpull의 외층 경로는 시작점의 그 정도 차이에도 갈린다.
- 측정 3의 인과 가설('시작점 c 부호가 달라 외층 첫 QP가 다르고, FD 열 실패로 L:M1이 고정된다')은 (a2)로 반증됐다. c 부호가 같아도 같은 갈림이 생긴다.
- (a2)를 9회로 1·8·18에 적용했다. 엔진 결정 차이는 pushpull 말고 0이다(현행도 같다). 경로 계수 차이는 남는다(current_reuse 7, nmcnr 8, sf_pushpull 8, two_stage_ota 7, two_stage_ota_sf 2). `hard_ok`는 9회로 모두 세 스레드가 같다.
- (a2)가 바꾸는 결과(스레드 1, 현행 대비 엔진 결정 차이)는 두 회로다. folded 1(`hard_ok` False → True, 시작점 c −4.68e-10 → +1.25e-6), common_gate 2(ε 풀이 `EA:s1` best seq 34 → 23, stop `converged` → `slsqp_8`)다. 나머지 7회로는 0이라고 적었으나 틀렸다(v1.11 정정, nfr4c2 판정 0305b8c A-5): √ε 여유가 경계에서 끌어올린 층 0 점 전부를 움직여 nmcnr_amplifier·pushpull_follower_buffer·sf_pushpull_output_opamp도 바뀐다(front·hard_ok·stop 불변, nmcnr `block_recomputes_same_input` 64 → 80). 사용자 결정 2026-10-16 N-5로 수용했다. 변화 0은 two_stage_ota·two_stage_ota_sf·current_reuse_telescopic_ota·ngcc_3stage_ff 4회로다. S0 수준 결과(`search_base.fp`·`context_fp`)는 비교할 수 있는 7회로에서 모두 같다(common_gate의 현행 측정에는 S0 기록이 없다). → 층 0·탐색 결과 기준선은 다시 잰다(40 §2.4.13 (7)).

**남은 위험**(이 규칙 범위 밖): 풀이기가 정한 값의 잡음은 BP1로 없앨 수 없다. 닫힌 식이 없기 때문이다. 두 갈래가 있다. (1) 풀이기가 활성 제약을 c ≈ 0으로 몬 점의 부호 판정. (2) 풀이기 해의 경계 밖 성분이 다음 풀이의 경로를 가르는 것(위 pushpull). 같은 실행 환경에서는 1안 고정(40 §2.4.13 (1))으로 비트 재현된다. 다른 환경에서 갈리면 40 §2.4.13 (2)의 이산 비교가 FAIL로 드러낸다. pushpull은 지금 엔진으로는 다른 환경 비교에서 FAIL할 것으로 본다. 스레드 1 대 8이 그 대리 측정이다. 처리(Q-N7 확정, 사용자 결정 2026-10-15 "기본안대로 진행해", U-83): 알려진 결함으로 기록하고(42 D-ND4) 이 card를 끝낸다. 원인(외층 FD 열 실패와 재시작 경로)은 후속 card NFR4-F1(40 §2.4.13 (8))로 조사한다. 2안은 다시 열지 않는다.

**as-built 변경**: `E/search/layer0_center.py:238-246`(위 식, 옛 `lift = u` 줄 240은 같은 변경에서 지운다. u는 `centre_u` 반환값으로만 남는다), 끌어올림 설명 문장 -- cfe2e31 실측으로 끌어올림 설명은 모듈 docstring 2번 항목(`:12-18`)에 **없고** 코드 주석 `:238-239`와 `E/search/CONTRACT.md:1063-1065`(U13.2 '전류 확정' 끝 문장 '해의 편차 u(ln)만큼 움직이는 θ 전류를 모두 올려')에 있다. 이 둘을 닫힌 식으로 고치고 docstring 2번 항목에 끌어올림 한 문장을 더한다(옛 문장 '모듈 docstring 2번 문단(끌어올림 설명)'을 정정). **test**(test 작성 주체, 소스 열람 없이 이 절만으로):
- `test_layer0_lift_closed_form`: toy 원뿔에서 끌어올린 뒤 최소 행 q가 1 + √ε와 같은지(부동소수 반올림 범위 안), 나머지 A_m > 0 행 q ≥ 1 + √ε인지 단언한다. F_m ≠ 0인 행이 최소인 toy를 포함한다. **반올림 범위(J-15, 오케스트레이터 기본안 -- 사용자 결정 아님)**: 상대 허용폭 γ_n = n·ε/(1 − n·ε)(표준 반올림 오차 상계, ε = `sys.float_info.epsilon`), n = test가 끌어올린 θ에서 q_m을 다시 계산하기까지 위 식이 거치는 부동소수 연산 수를 그 toy의 항 수로 센 값(s 계산: A_m·F_m 항마다 exp·곱·나눗셈과 합, 분자 1 + √ε − F_m, 나눗셈, ln / θᵢ = exp(xᵢ + s): 덧셈·exp / q_m 재계산: 항마다 곱·나눗셈과 합). 상수를 짓지 않는다 -- n은 식에서 세고 γ_n은 정의다. 셈 규칙(N-6): 덧셈·뺄셈·곱셈·나눗셈은 IEEE 754가 정확 반올림(상대 오차 ≤ ε/2)이고, `math.exp`·`math.log`는 정확 반올림이 보장되지 않으나 libm의 통상 오차 한도 1 ulp(상대 오차 ≤ ε)를 쓴다 -- 그래서 연산마다 상대 오차를 ε로 잡아 사칙연산·exp·ln을 **각 1회로** 센다(사칙연산은 그 절반이라 이 셈이 위쪽 상계다). `max`·`min`·클램프·비교는 반올림이 없어 세지 않는다. libm 1 ulp는 플랫폼 libm의 문서화된 한도이고 새 상수가 아니다. 이 한도를 넘는 libm이면 test가 실패로 드러낸다(넓히지 않는다). 단언: |min q − (1 + √ε)| ≤ γ_n·(1 + √ε).
- `test_layer0_lift_independent_of_solver_noise`: 같은 문제에서 풀이기 해 x만 허용오차 안에서 흔든 두 입력을 쓴다. 최소 행이 같으면 끌어올린 뒤 그 행의 `w_min` c가 둘 다 0보다 크다. **풀이기 해 주입(J-16, 오케스트레이터 기본안 -- 사용자 결정 아님. 선례: XRUN-F1 card A J-3·card 1 J-5의 모듈 속성 교체 계약)**: 모듈 속성 `gmid_engine.search.layer0_center.scipy_minimize`(as-built `from scipy.optimize import minimize as scipy_minimize`, 전류 중심 `:235`·최대-최소 `:374`가 모듈 전역 이름으로 부른다)를 교체 지점으로 고정한다 -- 이름·호출 방식(키워드 `jac`·`method`·`bounds`·`constraints`)·반환에서 `x`를 읽는 방식을 바꾸지 않는다. test는 `centre_start(sctx, rung)` 호출 동안만 이 속성을 진짜 풀이 결과의 x를 흔들어 돌려주는 감싸개로 바꾼다(`centre_start`는 전류 중심만 부르고 최대-최소는 부르지 않는다). 가장자리 test(아래 '끌어올림 식의 가장자리' 셋 -- R 빔, 분자 모두 ≤ 0, 식 값 < 0이면 s = 0)도 같은 지점으로 x를 정한다.
- `test_layer0_boundary_rows_positive_9circuits`(엔진 고정 상태, 스레드 수를 바꾸지 않음 -- 이 test에서는 스레드 비교를 하지 않는다. 고정 뒤에는 스레드 비교로 경계 배치 결함을 드러낼 수 없기 때문이다. 고정 자체가 듣는지는 40 §2.4.13 (7)의 `test_blas_thread_determinism`이 같은 환경 1차 검사로 계속 본다): 9회로 층 0 시작점에서 BP1로 경계에 놓인 행의 c가 0보다 크다. 그래서 `hard_ok`가 경계 배치 때문에 False가 되지 않는다. 현행 코드에서는 folded_cascode(`w_min:M8` c = −4.68e-10)에서 실패해야 한다(red 재현). 이 값은 34932a9 복제에서 잰 것이고 card 1(실행 사이 재사용 제거)·code_hash·library spec 병합 뒤인 card base cfe2e31에서는 재지 않았다(J-14): auditor가 test 동결 전에 cfe2e31에서 folded `w_min:M8` c < 0을 부호 단언으로 재현하고, 재현되지 않으면 멈추고 보고한다(다른 red 회로나 toy가 필요 -- 그때 이 절을 고친다). red는 import 오류가 아니라 비트·부호 단언이어야 한다. pushpull 탐색 결과의 다른 환경 일치는 이 card의 완료 조건이 아니다(남은 위험 (2), Q-N7 확정, 후속 card NFR4-F1).

---

## 6. 스펙에서 gm/ID·L·전류 출발 구간 (단계 A8)

**쓰임**: 출발값과 보고에만 쓴다(EP-7). 입력은 S1/S1v, spec, LUT 곡선, A6 상한표다.

**파일**: `E/search/start_intervals.py`, `iv_headroom.py`, `iv_speed.py`, `iv_gain_l.py`, `iv_matching_l.py`, `iv_noise.py`, `iv_area.py`, `iv_currents.py`, `macro_poles.py`, `dominant_node.py`.

**matching·헤드룸**(사용자 결정 2026-10-08 Q3·Q4; v1.15.1 개정 -- 계획 v6.38.2 DEC-105 (5)(6)): 절대 offset 제약이 있으면 입력 소자 면적 조건의 **gm/ID 하한**(§6.4-2 -- L 하한 아님), offset 구조 가드가 있거나 절대 offset·잡음 제약이 있으면 부하 gm/ID 상한(§6.4-2a -- R7 가드 필드, 합 행 포함), 스윙·ICMR 제약이 있으면 헤드룸 예산 분할(§6.2)을 계산한다.

**잡음 경로**: 범위 안이다(사용자 결정 2026-10-08, §7). 1/f 제약이 있으면 1/f L 하한(§6.4-3)을, 열잡음 제약이 있으면 열잡음 gm 하한(§7.5)을 계산한다.

**LUT 곡선 API(신규)**: `ft_curve`, `intrinsic_gain_curve`, `vdsat_curve`, `idu_curve`.

### 6.1 계산 순서 (순환 없음, M8)

궤도마다 대표 소자로 계산하고, L 동치류는 구간의 교집합을 쓴다. 순서는 다음과 같다.

0. 주극점 노드를 구조로 정한다(§6.3). 이 단계는 매크로 모델을 쓰지 않는다(N3).
1. 헤드룸 gm/ID 하한(§6.2).
2. 이득 L 하한(§6.4-1). [gm/ID_lo, LUT 최대] 구간에서 intrinsic gain이 가장 큰 gm/ID를 쓴다. 블록 목표 = found_db 비례 g_i^(1)(필드 READS -- §6.4-1, v1.15.1).
3. 속도 L 상한(§6.4-4). gm/ID_lo를 쓴다.
4. 잡음·면적 L 경계(§6.4-3, -5)와 면적 조건 gm/ID 하한(§6.4-2 -- v1.15.1: matching은 L 경계가 아니라 그 L에서의 입력 소자 gm/ID 하한, DEC-105 (6); 계산은 5의 L이 정해진 뒤). 이 단계에 필요한 전류는 1차 전류 추정(§6.5 1회차)에서 가져온다.
5. L 선택(§6.4-6).
6. 그 L에서 속도 gm/ID 상한(§6.3)과 면적 조건 gm/ID 하한(§6.4-2, v1.15.1).
7. gm/ID 선택(계획 DEC-104 R7·L-11 개정 -- M10 (b)): **S·F 출발값은 구간 안의 최댓값**이다. B는 고리 종속이면 7a(R6 블록)의 값이고, 고리 종속이 아니면 R7 (나) 현행 기준 -- R7 가드 필드 `device: start.guard`(소자별 구간 + 합 행)와 이 절 구간의 교집합 안에서 기존 K-1 max-min(§6.7-4; 구간 끝을 규칙으로 고르지 않음 -- 변수가 하나면 결과가 위 끝일 수 있다, O-151 N-2)으로 고르고 '열린 결정' 표지(U-124 -- LA-1 완료 조건 9 (c) 측정 뒤 결정)를 단다. 고리 종속 여부는 R-1′ 필드 변 좌표 집합과 분류 필드에서 읽는다(§6.7-11).
7a. **KVL 고리 공동 선택 = DEC-104 R6 블록**(§6.7, v1.6; v1.15.0 개정 -- 계획 DEC-104 R5′·R6·R7, O-127·O-142; K-1 (i)에 체계 오프셋 목표 행 `mirror_vds`와 R7 가드 합 행이 든다, DEC-105 (4)(5), §6.7-4): 7의 선택을 소자별 독립 최댓값으로 끝내지 않는다. R-1′ 제약 그래프 S0 필드(TB-1)의 변·writer_root 행과 쓰기 계획 v2 고리 등식(X)을 READS해, 출발 단계에서 처리하는 고리(구성원이 모두 출발 단계에서 정해지는 고리 -- 분류 필드·변 좌표 집합으로 S0에서 한 번 정한 자리)에 대해 R5′ (1)~(4)를 적용한다: 값은 R5′ (1)(2) 쓰기 순서(선언 범위 고리 = 나머지 경계, 이득 저하 정의 시 공동 집합 끝 -- R7 (가); 그 밖 W4·V_R = 행 여유 max-min)로 정하고, 모든 행이 0 이상이면 바꾸지 않고, 깨지면 W4·V_R → B 밀도(R7 가드 안, 합 행 포함) → S 정의역 조건(범위 끝 이득 행은 재개방 표지 + 탐색 개방) 순으로 다시 열어 K-1(§6.7-4 -- (i) 위반 최소에 `mirror_vds` 목표 행 포함, DEC-105 (4))로 함께 고른다. B의 max-min 대상 = gm/ID 위치, W4·V_R = 깨진 행 여유. 올린 점은 매크로·면적 실행 가능성을 다시 잰다(§6.7-4 B3). 해가 없으면 충돌 레코드(§6.6, `quantity="kvl"`). S·F의 선택점은 층 0 역산 우선(DEC-71 (4), §5)의 첫 회차 출발값이고 구간은 그 역산의 정의역이며, B·V_R·종속 W4는 층 0의 고정 입력(READS)이다(§5.10-3 (ii)).
8. 전류 확정(§6.5 2회차). 열잡음 gm 하한(§7.5)과 열잡음 C_eff 하한·1/f L 하한(§7.5, β·C_eff 입력)을 함께 적용한다. 블록 전류 하한 = DEC-104 R8·R10 공급 요구 하한(§6.8 -- 대상(측정 노드 그 방향 공급 셀이 모두 바이어스 구동 레일 source 셀)이면 가정 붙은 필요조건 하한, 그 밖은 하한·출발 목표 없음 -- O-157 S4·O-162; 구현 = card SB-1, LA-1 시점의 하한 행은 W_min뿐). S 소자 ID = max(gm_req/(gm/ID), R8 하한) -- R8 하한이 이기면 gm/ID 정의역 상한이 gm_req/I_min으로 잘린다(DEC-104 R4). 8 에서 전류가 바뀌어 최소 폭 보정(§6.5 as-built)이 gm/ID 를 올리면 7a 를 다시 잰다(상한 = 소자 수, 7a 가 바꾼 것이 없으면 끝).

9. **출발 사다리**(as-built 0868ff5 `search/start_intervals.py`·`start_values.StartRung`, 층 0 `layer0_start`가 소비):
   - **t**: 구간 안 위치다. 소자마다 gm/ID = gm/ID_lo + t·(gm/ID_hi − gm/ID_lo)이고, t = 0은 하한 끝, t = 1은 상한 끝이다(7의 선택은 t = 1에서 시작한다).
   - **steps** = ⌈log2(span / floor)⌉(span > 0일 때, 아니면 0). span = max_소자 (gm/ID_hi − gm/ID_lo), floor = 그 소자들 LUT 곡선의 gm/ID 최솟값이다. 구간 폭을 LUT gm/ID 최솟값 단위까지 반으로 가르는 횟수이고, t 탐색 분해능 2^−steps와 같다.
   - **칸 0(선택점)**: 실행 가능(면적 ≤ 예산, 매크로 근 있음)한 최대 t*. t = 1이 실행 가능하면 t* = 1이고, 아니면 [0, 1]에서 `bracket_root`(허용오차 2^−steps)로 경계를 찾아 그보다 한 칸 아래를 쓴다. 칸 0은 매크로 확정 풀이(전원 전류 최소화 포함)의 전류를 쓴다. 7a(KVL 고리 공동 선택)는 칸 0에 적용한다.
   - **칸 k = 1..steps**(t* > 0일 때): t_k = t*/2^k. 매크로는 전원 전류 최소화 없이 실행 가능한 출발점(`refine=False`)만 풀고, 7a를 칸마다 다시 적용한다(§6.7-6).
   - **칸의 내용**(`StartRung`): t, θ(구간이 값을 정한 성분만: ln IDu, θ 전류, 보상 커패시터, L 동치류 L), L 칸 index, 기준 전류(매크로가 전류를 정하지 못한 소자의 자리값).
   - **저장**: 칸 목록은 S0 수준 필드 `graph/start: rungs`(as-built `StartIntervals.ladder` 그대로, U17 ①-b), 선택점 둘레 출발 θ 생성기의 입력(선택 gm/ID·L·칸·t)은 `graph/start: placement`다(40 §2.4.8). `placement`는 U17 ②에서 U15 `placer`와 함께 만들고, as-built MOD8 `Placement`(`E/convergence/convergence_values.py`)와 다른 것이다(40 v1.9.1 D4, 근거: 소비자 위치). 층 0 `layer0_start`는 칸 0부터 차례로 커널에 확인해 처음 받아들일 상태인 칸을 기준점으로 쓴다(§5.9 상태).

**4의 전류를 정하는 방법**: 4는 전류 I가 필요하다. 그 값은 §6.5 매크로 모델을 **1회차**로 돌려 얻는다. 1회차에서는 gm/ID를 gm/ID_lo로 두고 L을 2의 하한으로 둔다. 확정 전류는 8에서 다시 계산한다. 4→8 사이에는 되먹임이 없으므로(8의 결과가 4로 돌아가지 않는다) 순환이 생기지 않는다.

### 6.2 gm/ID 하한 -- 헤드룸

**쓰임 한정**(계획 v6.38 후속 정정 표 '41 §6.2' -- 근거 `wt/_drafts/evidence/2026-10-26/handcalc_order_principle_audit.md` §7 M10 (b), DEC-104 R5′·R6): 이 절의 헤드룸 하한은 **고리 종속이 아닌 S·F 소자의 정의역 제약**으로만 쓴다. 고리 종속 성분(B ln IDu·V_R·종속 W4)은 이 하한으로 정하지 않고 R6 블록(§6.7-11)이 R-1′ 고리로 정한다. 아래 V_col의 'R 강하 0'(인증 전류 없음)은 V_R ≥ 0이라 가용 폭의 위쪽 경계 -- S·F 하한 gm/ID의 필요조건으로만 유효하다(감사 §2.5 '맞음(상한 인증으로서)').

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

1. **이득 하한**(v1.15.1 재작성 -- 계획 v6.38.2 DEC-105 (1)·card LA-1 범위 15 (a), 사용자 결정 2026-10-13 Q1-2 (ii)·L-2·O-164·O-165 (a)):
   - **블록 목표** = 층 0 첫 회차 예산과 같은 found_db 비례 g_i^(1) = G·found_db_i / Σ_j found_db_j(§5.3.2, 사용자 결정 L-2). 옛 'g_i = G·A_i,max / Σ A_max'와 'A_max가 미상이면 비활성'은 삭제한다 -- gain 제약이 선언된 회로에서는 A_max 인증과 무관하게 활성이고, gain 제약이 없으면 비활성 그대로다(H3 중 gain 제약 갈래만 남음).
   - **정본 필드**: g_i^(1)은 graph 필드 `graph/ach: gain_target_first` = 정렬 tuple ((블록 키, g_dB), ...)(writer = S0 블록 `gain_target_first`, 파일 `E/search/gain_target_first.py`; READS = `graph/ach` 블록 상한 행의 `found_db`·spec gain 목표 G; 단계 A, GB4 뒤·출발 구간 앞). 소비자 = 이 절(출발 구간 이득 L 하한)과 층 0 첫 회차(§5.3.2) -- 같은 양을 다시 계산하는 둘째 생산자 금지(graph 규칙 1·3; 지금 `layer0_budget`의 첫 배분 계산은 이 필드 READS로 바꾸고 옛 계산 삭제). **found_db가 없는 블록이 든 뷰**(gap A2: 단위 = 뷰): 그 뷰의 비례 정규화(Σ_j found_db_j)가 정의되지 않으므로 필드의 그 뷰 항목 = 정의 불능(사유 `found_db_missing{view, blocks}` -- 그 뷰의 블록 전부)이고 출발 이득 L 하한은 아래 '정의 불능'으로 간다. L-2 보완 규칙(층 0 기준점 블록 분해 gain)은 층 0 기준점(출발 구간 뒤)을 입력으로 하므로 출발 단계에서 부를 수 없다(층 역전) -- 층 0 첫 회차의 보완 예산은 정의 축이 다른 양(입력 = 층 0 기준점)이라 이 필드에 쓰지 않고 층 0 회차 기록(`graph/layer0: rounds` 1회차 예산)에만 남는다. (계획 v6.38.3 DEC-105 (1) 개정·U-133 기본안 (A) 승인 O-170과 같음, 옛 승인 질문 Q-GL1 삭제: 정의 불능의 단위 = found_db 없는 블록이 든 **이득 사슬 뷰의 블록 전부**(물리 결정자: g_i^(1)은 뷰 전체 도달 이득 추정 비로만 정의되는 몫 -- 아는 블록만으로 나누면 모르는 이득 블록의 몫을 얹어 L 하한을 부풀림); 영향 = 계획 실측 current_reuse·nmcnr·sf_pushpull(SF-1 범위 5 뒤 2회로); **원래 취지와 다름(U-133 -- 계획 표지)**: Q1-2 (ii) '활성'이 그 뷰의 출발 단계에서 정의 불능. 층 0 보완 예산의 필드 = `graph/layer0: rounds`의 1회차 `budget` 칸(writer = 층 0 블록 하나, 정의 축 = 입력이 층 0 기준점 -- g_i^(1)과 다른 양); 뷰 전부 found_db가 있으면 층 0은 g_i^(1) 필드를 READS(사본·재계산 0). found_db '기준점 미발견' 원인 조사 = card LA-1 범위 15 (h)).
   - **L 찾기**: 블록 국소 모델 gain ≥ g_i^(1)을 만족하는 최소 L을 찾는다. bin은 오름차순으로 훑고, bin 안에서는 bisection한다(같은 bin 안 보간 -- LR3).
   - **fail-closed**(DEC-105 (1) -- as-built 결함 `E/search/iv_gain_l.py`: 평가된 앵커가 없으면 가장 긴 앵커로 닫고 이득 0 dB를 가정한 margin): (i) 한 블록에서 평가되는 L 앵커가 하나도 없으면(표·값 미정의) 그 블록 이득 L 하한은 **정의 불능** -- 하한 값을 만들지 않고(어떤 앵커로도 닫지 않음) 사유와 margin `null`(N3.14)을 출발 기록(`graph/start: records`)·보고 표에 낸다. 원소 전류가 1회차 입력에 없으면 사유 = `gain_l_element_undetermined`('1회차 원소 미정' -- 자기 판정)이고 그 1회차 원소 키와 함께 기록한다(원인 추적은 원소 키로만 -- graph-consumption GC-5의 1회차 충돌 기록이 같은 원소 키를 가진다; 이 함수는 다른 card 기록을 읽지 않는다) (ii) 평가된 앵커가 있으나 목표에 못 미치면 `StartConflict(quantity="gain_l", margin = 목표 − 평가된 최선 이득)`, 하한 값 = **평가된 최선 앵커**(출발값 전용; as-built 마지막 평가 앵커 `previous[1]`에서 바뀌는 동작 변경 -- LR4 'L 증가가 늘 이득 증가는 아님', card LA-1 변화표 원인 항목). 거부는 커널 뒤 판정(gain 제약·DEC-104 R8 이득 행)만이다.
   - **W가 없는 단계**: 이 하한은 전류 확정 전이라 국소 모델 파라미터를 도달 가능 슬라이스 포락에서 읽는다(40 §3.7-A 8 -- 상한 양은 최댓값; gain ≥ 목표 판정은 그 포락 상한으로 한다 -- 실현 가능한 L을 자르지 않음, 출발값 전용).
   - **재작성 범위**(card LA-1 범위 15 (a) 단독 소유, O-165 (a)): `E/search/iv_gain_l.py` `gain_l_bounds` 함수 전체(목표·닫힘·최선 앵커·사유 분기 -- 원소 없음 경로 `:64-65`·`:117-119`, 닫힘 `:125-127`), `E/search/iv_context.py:49-51`의 인증 조건(A_max 인증 → 활성), `E/search/layer0_budget.py` 첫 배분 계산(필드 READS로), 새 `E/search/gain_target_first.py`. GC-5는 이 함수를 고치지 않는다(graph-consumption v0.14.3).
2. **matching 면적 조건 → 입력 소자 gm/ID 하한**(사용자 결정 2026-10-08 Q3 "q3,q4는 네 제안대로 해", 근거 `_drafts/engine/matching_swing_spec_proposal.md` §0·§2.3; **v1.15.1 개정 -- 계획 v6.38.2 DEC-105 (6), 사용자 결정 2026-10-14 Q-N2 B, LR6 개정; 옛 제목 'matching 하한'(L 하한)**): **절대 offset 제약**(`offset_in_sigma_mv <= 값`, 현재 파일럿 3.3 mV)이 있는 회로에서만 활성이다. 구조 가드(`offset_excess`, §6.4-2a)만 있는 회로는 부하 gm/ID 상한으로 간다. matching은 **L 하한을 만들지 않는다** -- 면적 조건은 (gm/ID, L) 결합 조건이고 L은 다른 경계(이득 역산·flicker·LR6 상한·LR3 bin)가 정한다(아래 '하한').
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
   - **하한**(v1.15.1 개정): 출발 단계의 입력 셀 몫 σ_share = σ_target/√2(입력 셀 분산 = 나머지 분산, §6.4-2a 가드와 §7.5 잡음과 같은 등분 원칙 -- 새 상수가 아니라 '부하 기여 ≤ 입력쌍 기여'의 경계). 입력 셀 소자 면적 하한 A_min(L, gm/ID) = A_eff(L, gm/ID)² / σ_share². L은 §6.4-6이 다른 경계로 정한 값이고, 그 L에서 W·L = I·L²/IDu(g, L) ≥ A_min(L, g), 곧 **IDu(g, L) ≤ I·L²/A_min(L, g)를 만족하는 최소 g**를 입력 소자 **gm/ID 하한**으로 건다(IDu는 gm/ID에 대해 단조 감소라 그 L의 LUT 곡선에서 bisection -- `idu_curve`, 새 상수 없음; 전류 I = §6.1-4의 1회차 전류, 8에서 확정 전류로 다시 잰다). 그 하한이 속도 상한(§6.3)을 넘으면 충돌 레코드(§6.6). 옛 'L ≥ √(A_min·IDu/I)'(matching L 하한)는 삭제한다(재작성 범위 = `E/search/iv_matching_l.py`의 L 하한 경로 -- card LA-1 범위 15 (e)·범위 1).
   - 판정은 이 하한이 아니라 봉인 스냅샷의 `offset_in_sigma_mv`(40 §3.8, MNA 전회로)가 한다(EP-7).
2a. **offset 구조 가드 → 부하 gm/ID 상한**(`offset_excess <= √2` 회로): 부하 소자 k의 입력 환산 분산 비 Σ_k (gm_k·σ_VGS,k)² / Σ_in (gm_in·σ_VGS,in)² ≤ 1이 되도록 부하 gm/ID를 상한으로 둔다. gm_k/gm_in은 §6.5 매크로 모델 전류 비로 쓴다(§7.5 잡음 가드와 같은 방법). §6.3 속도 상한·§7.5 잡음 상한과 교집합하고, 헤드룸 하한(§6.2)과 충돌하면 충돌 레코드로 남긴다.
   - **v1.15.1 -- R7 가드 필드 형식(계획 v6.38.2 DEC-105 (5)·DEC-104 (3)(b), 사용자 결정 2026-10-13 Q4-1·Q4-2·2026-10-14 Q-N2 D; 구현 = card LA-1 범위 15 (d), U-132 기본안 승인 O-166)**: 이 절과 §7.5의 가드는 R7 가드 필드 하나에 담긴다(§6.7-11) -- (a) B 소자별 gm/ID 가드 구간 (b) **합 행** Σ_부하 기여 ≤ 가드 비 · Σ_입력 기여(이 절의 Σ_k 조건 그 자체 -- 소자별 상한을 각각 고르면 합이 넘으므로 합 행을 R6·R7의 K-1 공동 선택이 함께 읽는다(§6.7-4); R7 (가) 선언 범위 고리 B가 나머지 경계로 정해져 합 행을 어기면 `StartConflict`로 기록만 -- 재개방 촉발 행은 R-1′ 행뿐, O-158 (A′) ②). (c) **가드 입력 전류 = 매크로·KCL이 정한 전류만**(자리값 금지 -- DEC-104 R3과 같은 규칙; 전류가 정해지지 않은 소자는 가드 계산에서 빼고 사유 기록), W가 W_min으로 잘린 점(`start.row` 최소 폭 보정 점)은 가드 계산에서 뺀다, gm/ID에 대한 분산 비 곡선의 볼록 껍질(hull)은 단조 구간 안에서만 만든다(Q4-1 잔여). (d) **절대 offset·잡음 제약 회로에도** 부하 가드 '부하 기여 ≤ 입력 기여'(§6.4-2 등분 전제 E² − 1 = 1, 새 상수 없음)를 건다(Q-N2 D -- 구조 가드 metric 회로만이 아님). 기존 가드 계산을 이 필드 writer로 옮기면서 (b)~(d)를 고친다(결함을 정본 필드로 옮기지 않음, 사본 금지).
2b. **LUT mismatch 감도 열**(U3): 생성기 `assets/sky130_lut_sweep.py`에 mismatch 모드를 더한다.
   - 방법(제안서 §0.3과 같음): pm3 카드 복사본에서 변수 k의 `*_slope_spectre`를 0 → 1(인스턴스 기하의 1σ)로 바꾼 섭동 곡선과 기준 곡선을 같은 include·DUT 줄로 돌리고, 기준 곡선의 칸 ID에서 두 곡선의 VGS 차를 DVGS_k로 둔다(W_ref·각 L·DC LUT 축 격자).
   - **저장**: 새 버전 파일 `..._mismatch_r1.npz`(sha256, 생성 메타: 모델 경로·sha, ngspice 버전, 온도, 섭동 변수 목록)에 둔다. **공유 `lut_data`의 기존 v2 r2 파일은 고치지 않는다.** `lut_v2_location.json`에 새 항목으로 더한다. 로더는 v2 칸과 같은 키로 합쳐 노출한다.
   - **tol**: 칸별 `tol_mismatch`를 LOO로 계산한다(DEC-87 방법, 디스크 캐시 대상 -- v1.10: 실행 사이 유지, U-87 원래 취지의 예외, 40 §2.4.12 Q9).
   - 감도 데이터가 없는데 offset 제약이 선언되면 `SchemaRejectedError(mismatch_lut_missing)`이다.
   - 한계 기록: 제안서 실측은 W 5 µm·|VDS| 0.9 V·VS 0 한 슬라이스였다. 생성기는 DC LUT 축(VDS·VS·W 슬라이스) 전체에서 잰다.
   - API(신규): `mismatch_dvgs(kind, w_key, L, VGS, VDS, VS) -> MismatchSens{dvgs: {param: V}, slope_ref: {param: value}}`.
3. **flicker 잡음 하한**(사용자 결정 2026-10-08, 파일럿 `noise_out_int_vrms` 제약에서 활성):
   - 출발 단계에서는 §7.5에 따라 (총 예산 − 스위치 kT/C 항)의 절반을 flicker 몫으로 보고, 이를 출력 적분 예산으로 둔다. 스위치 항은 `sampling_caps` 선언이 없으면 0이다(파일럿 = 0, C-2).
   - 입력 소자의 flicker 출력 적분은 Σ_in (K_k/(W_k·L_k))·∫ f^−EF_k·|폐루프 잡음 이득|² df이다. K는 §7.2의 A·W·L이고 W에 무관하다. 적분은 매크로 모델 폐루프 응답으로 계산한다.
   - 위 식에서 입력 소자 면적 하한 A_min = W·L이 나온다. W·L = I·L²/IDu에서 **L ≥ √(A_min·IDu/I)**이다(matching 하한과 같은 꼴).
4. **속도 상한**: f_T(gm/ID_lo, L) ≥ f_np에서 L의 최댓값.
5. **면적 상한**(결정 11):
   - L ≤ √(A_budget · IDu / I)
   - W ≤ A_budget / L
6. **선택**: L = max(1, 3의 하한)이다(2는 L 하한이 아니라 그 L에서의 gm/ID 하한, 2a는 gm/ID 상한이다; DEC-105 (6)·LR6 개정). LUT L 점이나 bin 안 값으로 맞춘다(LR3). 구간 끝이 다른 bin에 있으면 bin마다 후보를 하나씩 둔다.

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
- **영점 상쇄 저항**(계획 N6.35 E-15·DEC-92 (3)): 출발값 = 구조 규칙 1/Σ_{c∈S} gm_c(그 바퀴 셀 gm -- 40 §3.5)이고, 매크로 풀이(DEC-71 (4)(d))는 θ 스키마에 든 보상 수동소자 성분 일반을 함께 푼다(영점 R을 따로 지칭하지 않음 -- SF-1 범위 9와 순서 관계 0). θ 성분이 아닌 영점 R(SF-1 범위 9 병합 전 구조 규칙 고정)은 셀 전류 미정 단계에서 출발값 정의 불능 `zc_start_undefined{element}`를 기록하고 그 칸의 매크로 출발은 정의 불능(아래 4 (i) -- 사다리 다음 칸). 어느 경우도 망에서 빼지 않고(빼면 다른 회로) 상자 중점을 쓰지 않는다(as-built `zc_fallback` 상자 중점·커패시터 상자 미선언 '망에서 뺌' -- `E/search/macro_poles.py:131-135·137-157·180-182` 삭제; 상자 미선언은 단계 A 거부 DEC-105 (10) (d)). 비θ 갈래는 SF-1 범위 9가 병합되면 대상 0 -- 그 변경이 코드·toy·문언을 지우고, LA-1 착수 때 이미 0이면 만들지 않는다.

**풀이 순서와 실패 처리**:
1. 극점과 영점은 pencil 고유값으로 구한다(`pencil_roots`).
2. 한 바퀴는 다음 세 단계를 차례로 수행한다.
   - (i) gm_1: UGF = `gbw_target_hz`의 1-D 근(`bracket_root`). 이때 나머지 값은 현재 값으로 둔다.
   - (ii) k = 2..n 블록 순서로 gm_k: PM ≥ 목표인 최소값.
   - (iii) 보상 수동소자: 정준 순서로 PM ≥ 목표인 최소값.
3. 한 바퀴의 모든 값 변화가 각자의 1-D 근 허용오차 안에 들면 수렴이다. 상한은 K_max 바퀴이고, 닿으면 마지막 값을 쓰고 `macro_nonconvergent`를 기록한다(보고만, 정지 아님 -- v1.15.2: 목표 미달이라 기록 어휘 = `StartConflict(quantity="macro_target", reason="nonconvergent")`, 4 (ii)).
3a. **출발점 개방 RHP 극점 수 P = 0**(계획 v6.38.2 DEC-105 (3), 사용자 결정 2026-10-14 Q1-1·Q2-2 B; 구현 = card LA-1 범위 15 (b)): 매크로 출발점은 |H(jω_GBW)| = 1 근에 더해 그 점의 개방 루프 RHP 극점 수 P = 0(1의 pencil 극점 -- 새 계산 없음)을 요구한다. P > 0이면 그 출발점의 뒤 블록 gm을 **출발 gm 사다리**의 다음 칸으로 올린다. **사다리 정의**(이 절이 정본 -- 아래 '구현 반영' 다중 출발과 같은 사다리): 주극점으로 둔 단 j를 뺀 나머지 단 gm을 2^k배(k = 1, 2, …)로 올리고 단 j gm으로 UGF = GBW를 맞춘 점이 칸 k다(배수 2 = 사용자 결정 Q2-2 B 원문 '같은 2배 사다리로 더 올린다', 새 상수 아님); **사다리 끝** = 올린 gm이 그 단 gm 범위 상한(4의 변수 범위 -- 전류 상자 × gm/ID 구간)을 넘는 첫 칸. 끝 칸까지 근은 있으나 P ≠ 0이면 **목표 미달** -- 끝 칸의 정의된 값으로 출발하고 `StartConflict(quantity="macro_target", reason="rhp_open_loop")`을 그 후보에 기록한다(출발 불능 아님 -- v1.15.2, 계획 DEC-105 (3) v6.38.3·N6.35 머리 '출발 정의 불능 공통 규칙' (1); 판정은 봉인·MNA가 개루프 RHP 극점을 위반으로 셈 -- N3.6 안정 판정). 칸마다 원인이 섞이면(앞 칸 P ≠ 0, 끝 칸 근 없음) 근 있는 칸 가운데 가장 높은 칸의 정의된 값(목표 미달 기록), 근 있는 칸이 없으면 그 후보 매크로 출발 불능(4 (i)). 옛 `macro_rhp_start` 기록·'추정' 대체는 삭제. 매크로 망은 출력노드가 아닌 극점 노드(N9)를 포함한다(위 '망 구성' -- design 문언 그대로, 구현 몫). 재작성 범위 = `E/search/macro_poles.py:3-4`·`:316-328`(card LA-1 범위 15 (b)).
4. **근 없음과 목표 미달**(계획 N6.35 E-31·E-17·머리 '출발 정의 불능 공통 규칙', **원래 취지와 다름(계획 표지, 승인 표 #27·#31)**; 옛 '어떤 1-D 근이 괄호가 안 잡히면 현재 값 유지 + `macro_root_missing` 기록 + 모든 변수 근 없음이면 상자 기하 중심 '추정'' 대체 -- 세 층 어휘의 정본 = 40 §3.11-2):
   - (i) **정의 불능 = |H(jω)| = 1 근이 상자 안에 없음**(근 존재는 블록 순서 전부로 판정 -- as-built `refine=False`가 첫 블록 순서만 보는 경로(`macro_poles.py:332·337`) 삭제)과 **MNA 특이**(전달 정의 불능 -- E-17; as-built `at_target = (|H| 0.0, PM None)`(`:203-207`) 삭제)뿐이다 -- 그 칸은 `macro_rung_undefined{candidate, rung, reason ∈ {no_root, mna_singular}}`를 기록하고 사다리 다음 칸으로 간다; 모든 칸이 정의 불능이면 그 후보(출발 사다리 칸 t)만 **매크로 출발 불능**(`StartConflict(quantity="macro", reason="macro_start_unavailable")`, writer = 이 블록 -- card LA-1 범위 15 (g))이고 다음 후보로 간다; 모든 후보가 출발 불능(전류 충돌 포함)이면 그 S0 출발 불능(E-32 -- writer = graph-consumption GC-5).
   - (ii) **목표 미달**(근은 있으나 PM 미달·P ≠ 0·SLSQP 미수렴)은 정의된 값이라 그 값으로 출발하고 `StartConflict(quantity="macro_target", reason ∈ {pm_short, rhp_open_loop, nonconvergent})`만 후보마다 기록한다(아래 칸 `refine=False` 정제 생략 결과 포함 -- 기록이지 판정 아님; 미수렴 폴백 재풀이 없음 -- E-34).
   - (iii) 상자 미선언(as-built `capacitance_box_undeclared`·`resistance_box_undeclared`, `macro_poles.py:135·148`)은 단계 A 거부(DEC-105 (10) (d))라 매크로에 닿지 않는다. 어느 갈래도 상자 중심·풀리지 않은 출발점 그대로·첫 값으로 메우지 않는다(as-built `E/search/start_intervals.py:110-113` 삭제). 재작성 범위 = `macro_root_missing` 한 코드에 섞인 조건 넷(`E/search/macro_poles.py:135·148·363·369`) 분리·P 계산(1의 pencil 극점) -- card LA-1 범위 15 (g).
   - (옛 문언 -- 기록) 그 변수는 현재 값을 유지한다. `macro_root_missing{variable, condition}`을 기록하고 다음 변수로 넘어간다.
   - (옛 문언 -- 기록, v1.15.2 삭제) 모든 변수가 근 없이 끝나면 매크로 출발값을 버리고 상자 기하 중심을 쓴다. 이 값은 대체값이므로 **'추정'**으로 표기한다(계획 v6.38 후속 정정 표 '41 §6.5' -- 감사 `theta_basis_principle_audit.md` §2.5: gm·전류는 KVL 독립이라 θ 기저 위반은 아니고 대체값 표기만 필요). 상자 중심은 θ 독립 성분에만 쓴다(종속 성분은 R6 블록 -- O-128 Q2).

**특수 경우**: 단일 블록이고 Miller 루프가 없는 회로에서는 gm_1 = 2π·GBW·C_out이 나온다. U-12 기본안과 같은 값이지만, `compensation: null` 태그가 아니라 구조에서 나온다.

**전류**:
- I = gm / (gm/ID). S 소자는 I = max(gm_req/(gm/ID), R8·R10 하한)이다(DEC-104 R4, §6.8 -- v1.15.0).
- 나머지 소자는 미러 비와 KCL로 전파한다.
- 남는 θ 전류(계획 DEC-104 R3 -- O-151 U5·U6·O-157 S8): 한 KCL 행에 미지 θ 전류가 둘 이상 남으면 남는 자유도는 매크로 '전원 전류 최소'의 변수다(그 전류가 gm을 정하는 소자의 노드 극점이 매크로 망 안에 있을 때만 -- 망 = 이 절 N9 포함, 출발점 P = 0, DEC-105 (3)); 교류 요구가 닿지 않는 θ 전류(순수 바이어스 가지)와 망에 없는 극점에 닿는 θ 전류는 하한 행(W ≥ W_min 전류, R8·R10 -- LA-1 시점은 W_min뿐)의 최대에 두고 '극점 미포함'을 기록한다. 상자 기하 중심·기하 평균 자리값은 쓰지 않는다(as-built `start_intervals.py:121-128` 자리값은 card LA-1 범위 13이 지움 -- 재작성 범위; 매크로 근 없음은 위 4 (i) -- v1.15.2, 옛 '매크로 근 없음 때의 '추정' 대체는 그대로' 삭제). 출발값이 바뀌므로 LA-1 변화표 원인 항목.
- **매크로 목표 gm의 θ 전류 전파**(계획 v6.38 card LA-1 범위 13 -- 사용자 결정 O-140 D8, backlog B85, DEC-104 R3): 필요 gm은 매크로 블록 하나(`macro_solve` 결과 `graph/start: macro`)가 쓰고 θ 전류가 그것을 READS한다 -- 입력 소자 전류가 θ 전류의 차(또는 합)인 회로에서도, 그 소자 전류 I_in = gm_req/(gm/ID)를 `dc_current_basis`의 그 가지 행(θ 전류의 선형 결합)으로 θ 전류 쪽에 되돌린다(옛 '미지 항 하나 방정식부터 전파' 규칙이 θ 전류를 정하지 못해 GBW가 목표에 못 미친 결함 -- 계획 범위 13 근거 `wt/_drafts/evidence/2026-10-26/spec_candidates_folded_cg.md` §6, 원인 추정·코드 경로 미추적). 한 행에 미지 θ 전류가 둘 이상 남으면 R3 매크로의 '전원 전류 최소' 변수로 함께 정한다(계획 DEC-104 R3, O-151 U5·U6; 재작성 범위 = as-built `iv_currents.py:149-151`의 건너뜀 삭제 -- LA-1 범위 13; 완료 조건 9 toy '미지 θ 전류 둘 이상 KCL 행'). 완료 확인 = 계획 완료 조건 9 (a)·1 (i) 쪽 toy('입력 소자 전류가 θ 전류의 차인 회로에서 매크로 gm이 θ 전류로 전파됨').

**기록**: `comp_approx_gap` = UGF·PM 스칼라의 (조립점 MNA − 매크로) 차이고, 극점·영점 목록은 두 쪽 원본을 보존한다(§5.5, 사용자 결정 L-7).

**구현 반영(as-built, 단위 U13, 2026-10-09)**:
- **풀이는 순차 바퀴가 아니라 공동 풀이 + 다중 출발**이다. 위 '풀이 순서'(gm_1 UGF -> gm_k PM 최소 -> C PM 최소)는 퇴화한다: gm_1 을 고정한 채 gm_k 를 줄이면 이득이 1 아래로 떨어져 (i)이 풀리지 않고, gm_1 을 함께 다시 맞추면
  gm_1 상자 상한 모서리로 간다; UGF 에서 잰 PM 은 모든 gm 을 같이 줄여도 변하지 않아(척도 불변) '최소 gm' 이 하한으로 간다. 대신 같은 제약 -- |H(jω_GBW)| = 1, PM(ω_GBW) ≥ 목표, 주극점을 뺀 극점 ≥ ω_GBW·tan(PM)(§6.3) --
  아래 전원 전류 합 최소를 SLSQP 로 한 번에 푼다. 이 문제는 비볼록이다(주극점이 어느 단에 놓이는지가 국소 최소를 가른다; 3극점 C = 1·2·3 pF 에서 주극점을 1 pF 단에 둔 국소 최소는 전역 최소의 1.7 배).
  그래서 단마다 그 단을 주극점으로 하는 실행 가능한 출발점(나머지 단 gm 을 2 배씩 올리고 그 단 gm 으로 UGF = GBW)에서 다중 출발하고, 구조로 정한 주극점 노드(`dominant_node`, §6.3)의 단을 먼저 시도한다. 만족해 중 전류가 가장 작은 해를 쓴다.
  구조 주극점 노드의 극점을 강제로 가장 낮게 두지는 않는다(큰 커패시터 단이 구조 주극점이 아닌 회로에서 전류가 더 큰 해가 된다 -- 독립 test 의 2극점 닫힌 식 oracle 이 자유로운 단 선택의 최소를 기대한다).
- **출력노드 컨덕턴스의 A_i 순서**(v1.15.1 개정 -- 계획 v6.38.2 DEC-105 (1)): 이득 제약이 있고 블록 목표 g_i^(1)(§6.4-1 필드 `graph/ach: gain_target_first`)이 정의되면 그 값, 아니면 입력 소자의 LUT 진성 이득 A_intr. 옛 'A_i,max가 인증되면 g_i'는 삭제(목표 정의가 A_max 비례에서 found_db 비례로 바뀜). 위 설계의 중간 단계 'g_i 가 없으면 A_i,max' 는 쓰지 않았다
  -- 이득 제약이 없는 회로에서 인증 상한(최적 격자 점의 값)을 블록의 실제 이득으로 가정할 근거가 없다.
- **PM 목표가 없으면** 매크로는 경계 PM_FLOOR_DEG = atan(1) = 45°(비주극점이 UGF 에 놓임)를 PM 하한으로 풀이 안에서만 쓰고 `pm_floor_pole_at_ugf` 로 기록한다. §6.3 속도 gm/ID·L 상한은 설계대로 PM 목표가 없으면 비활성이고 사유 `pm_target_missing` 을 보고한다.
- §6.2: 출력 DC 가 선언되지 않은 창은 남는 여유를 위·아래 부분 기둥의 같은 몫으로 나누고, 최소 폭 W ≥ W_min 은 확정된 전류에서 gm/ID 를 올려 맞춘다(전류가 입력 소자를 따르는 미러 부하는 gm 고정 하한이 어긋난다). §6.4-1 은 U9 블록 국소 모델(`BlockModel`·`ParamTables`)로
  목표 g_i 를 맞추는 최소 L 을 앵커 오름차순으로 찾고, 같은 bin 안에서는 앵커 사이 gain(dB)을 L 에 선형으로 보간한다(파라미터 표가 앵커 격자라 bin 안 L 에서 모델을 다시 풀 수 없다).

### 6.6 충돌과 보고

**충돌 레코드** `StartConflict{device|group, quantity, bounds[{source, value}], gap}`를 남기는 경우:
- 하한 > 상한
- 전류 > 상자 상한
- A_est > 예산(보고만)
- KVL 고리 행(§6.7)이 소자 구간 안 어떤 조합으로도(매크로·면적 실행 가능성과 함께) 모두 0 이상이 되지 않음(`quantity = "kvl"`, `bounds` = 남은 위반 행 (행 종류, 소자, 값 V), `gap` = 가장 나쁜 행 값의 크기). 양 끝 후보 대신 위반이 가장 작은 조합을 넘긴다(§6.7-5).
- 열잡음 C_eff 하한 > 선언 커패시터 값(§7.5, `quantity = "capacitance"`).

충돌이 있어도 자르지 않는다. 양 끝 후보를 '충돌' 표시와 함께 층 0으로 넘긴다.

**보고 표**: `start_intervals[{device, gm_id_lo/hi/chosen, L_lo/hi/chosen, bin, I_start, sources, inactive_reasons, conflicts}]`

**불변식**: 같은 입력이면 같은 표다. 이름 전단사는 행 이름만 바꾼다.

**상태**(v1.15.1 정정 -- 계획 v6.38.2 후속 정정 표 'D41 상태 MISS 문장'): PART. 출발 구간 블록(`start_intervals` -- spec·S1v·LUT 곡선에서 구간·충돌 레코드를 내는 단계 A 블록)은 as-built에 있다(integ/it12 `d759838a` `E/search/start_intervals.py`). 옛 문장 'as-built는 spec과 무관한 LUT 포락선 상자 중점을 쓴다'는 출발 구간 도입 전 사실이라 지운다. 남은 gap = 이 판(v1.15.0·v1.15.1)의 개정 -- DEC-104 R3·R6·R7·R10, DEC-105 (1)(3)(4)(5)(6)(7) -- 이고 card LA-1·SB-1이 닫는다(42 D-SI-cur·D-R6·D-R10·D-GL 행).

### 6.7 KVL 고리 출발 제약 (사용자 결정 2026-10-12 "9번 권고대로", "B는 권고대로")

**원리(바꾸지 않는 것 -- v1.15.0: S·F에 한정, 계획 v6.38 후속 정정 표 '41 §6.7 원리', 감사 M10 (b))**: 입력단 gm 은 spec(§6.5 매크로 모델)에서 오고, **S·F 소자의** gm/ID 는 [헤드룸 하한 §6.2, 속도 상한 §6.3] 구간 안에서 고르며, 전류 = gm/(gm/ID)다. S·F에 대해서는 노드 전압을 먼저 배분하고 gm/ID 를 역산하지 않는다(reference `gm-id-methodology.md` §4.1·§6.4·§6.7, `sky130-worked-example.md` §6). B ln IDu·V_R·종속 W4는 고리 종속 성분이라 구간 최댓값으로 고르지 않고 R6 블록(아래 11)이 R-1′ 고리로 파생한다(DEC-104 (0)·R5′·R6) -- 그것도 노드 전압에서 gm/ID를 역산하지 않고, B gm/ID를 가드 구간 안에서 고르되 W4·V_R을 소거한 존재 조건(R-1′ 행)을 제약으로 쓴다. 이 절은 구간을 그대로 두고, **구조가 묶은 소자는 독립으로 고르지 않는다**는 등식·부등식만 더한다.

**층 0 과의 관계(계획 DEC-71 (3)(4), 사용자 결정 B1 "계획을 따른다"; v1.15.0 개정 -- 계획 v6.38 DEC-64·DEC-104 R6, 사용자 결정 O-127 '출발 단계(§6.7)가 B 밀도 고리 정합 책임'·O-142)**:
- §6 의 출력은 **구간(경계)**과 그 안의 출발 선택점이다. 계획 DEC-71 (4)의 역산 우선 -- (a) 필요 gm 에서 gm/ID = gm/ID 역산, (b) 목표 이득에서 L 역산, (c) VDS·V_R 배분(R-1′ 구간 → 무변화/재개방(W4·V_R = R5′ (2) 행 여유 max-min) → 정확 풀이 판정 -- §5.3.4) -- 은 **층 0(§5) 블록 국소 문제가 이 구간 안에서** 한다. §6 은 역산의 정의역(구간)과 첫 회차 고정 입력(DEC-71 (3) '첫 회차는 스펙에서 유도한 출발 구간 값')을 준다.
- **B 밀도 고리 정합은 출발 단계(이 절의 7a = R6 블록)가 한다**(O-127). VDS·V_R **값 배분**은 층 0의 몫이고(§5.3.4), 같은 R6 블록이 후보마다 부른다. 출발 단계와 층 0은 같은 R-1′ 그래프로 W4·V_R 구간을 계산해 그 안에서 고른다(DEC-64 v6.38, headroom-chain X-1 개정 -- R-1′ 쓰임이 판정에서 구성으로, **원래 취지와 다름(승인 O-127)**). 옛 문언 '이 절의 포화 행은 고리가 정한 VDS(W4 창이 아닌, 나무로 정해지는 VDS)만 검사한다'는 대체 -- W4·V_R 경유 B 고리도 소거식(R-1′ 차분 변)으로 검사한다.
- 층 0 쪽 받는 자리는 §5.10-3이다: 고리 종속 멤버(X)는 층 0이 고르지 않고(§5.3.3 `kvl_dependent`), B 묶음은 층 0의 고정 입력(READS)이며, S·F 묶음의 7a 선택점은 층 0 첫 회차의 고정 입력(§5.3.10) 또는 첫 바퀴 값(§5.3.6)이다. §6 구간은 (a) 역산·자유·폴백 축의 정의역이다.
- **단계**: 이 절 전체는 단계 A(A8 안의 7a)다. 봉인된 값을 읽지 않는다(§0). 결과는 S0 수준 필드다(아래 7).

**왜**: §6.1-7 은 소자마다 구간 최댓값을 따로 고른다. VGS 고리(DEC-64 v2)는 한 소자의 VGS 를 나머지 VGS 합·차로 정하고, VDS-1 고리는 한 소자의 VDS 를 VGS 합·차로 정한다. 따로 고른 최댓값(모두 약반전, VGS 최소)은 그 합·차를 무너뜨린다. 실측(as-built bd19cc6, 사다리 칸 0): 파일럿 M4a VDS = −0.03 V(VDS = VGS(M63) − VGS(M3a) 꼴), sf_pushpull M10 노드 근 없음, nmcnr M301 VDS ≈ 0(사다리 7칸 모두 실패, Halton 시험 점에서만 출발).

**1. 고리의 출처 -- 새 탐지기를 만들지 않는다**: 평가 커널의 쓰기 계획(`node.dc_writer` 나무 + `device.dc_coord`, GB7 `dc_writer_plan`, sizing CONTRACT 3절)을 읽는다. 쓰기 계획은 S1 G_vgs 고리(`graph.rel_kvl_branch`, DEC-64)를 레일·W3 선언 노드·입력 DC·저항 강하까지 넣어 컴파일한 것이고, 종속 소자는 DEC-95 (3) 우선순위로 이미 정해져 있다.
- 비나무 MOS 엣지 중 `cycle_vgs`·`fixed_vgs` = **고리 등식**(DEC-64 v2 `Σ±VGS = ΔV`): 그 소자의 VGS 는 나무 경로가 정한다. `parallel_vgs`(v0)는 같은 VGS 묶음(§6.1-6)이라 대상이 아니다.
- **v1(포트 차 고리)**(계획 DEC-64 v1, 사용자 결정 B2·O-13 (1)): 입력 포트끼리의 '같은 DC' 등식은 없다(아래 1a). 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이고(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b), 그 종속은 위 항목의 고리 등식과 같은 대상이다 -- 이 절의 행 생성 규칙은 바꾸지 않는다(계획 N6.5 '고치지 않는 것': §6.7 KVL 출발 제약은 U17 ② 몫이고 IT-1 뒤의 쓰기 계획을 읽는다). 대칭이면 그 등식은 대칭 묶음과 중복이다. (v1.12 정정: 옛 문장 'v1 고리는 이 절의 행을 만들지 않는다'는 O-13 (1)과 어긋나 고쳤다 -- 옛 문장은 계획 history H2 'IT-1·IT-2 design' 행.)
- drain·source 가 같은 나무 성분에 있는 diode 아닌 MOS = **VDS-1 부등식**(`gvgs_summary.vds_saturation` 과 같은 뜻): VDS = 나무 경로 합·차 ≥ VDSAT + tol_vdsat. **v1.15.0 개정(계획 v6.38 후속 정정 표 '41 §6.7-1', headroom-chain v0.7.9 N3.4 '구성 소비자' -- VDS-1 자기 행과 `graph/start: kvl_rows`는 R-1′ 필드 읽기로 대체)**: 이 절은 VDS-1 행을 스스로 만들지 않는다. 포화 행·writer_root 행·행마다의 의존 묶음은 R-1′ 제약 그래프 S0 필드(card TB-1이 만든다, 정의 = headroom-chain N3.1·N3.4, 형식 = headroom-chain HC-D design)의 변·writer_root 행과 변 속성(변 좌표 집합, headroom-chain N3.1-5)을 READS한다(같은 사실 하나 -- 둘째 생산자 금지, graph 규칙 1). VDS-1 길이 1 변은 그 그래프의 부분집합이다(headroom-chain N3.1-6). `gvgs_summary.vds_saturation`은 TB-1이 같은 변경에서 지운다(headroom-chain N3.4).

**1a. 커널 쪽 개정(DEC-64 v1 을 계획에 맞춤, 사용자 결정 B2·K-3·O-13, card IT-1 -- 계획 N6.5)**:
- 개정 전(as-built, master `9401e98f`): 입력 DC 미선언이면 F 밖 입력 포트를 이웃 쌍마다 '같은 DC' 엣지(`input_tie`)로 잇고 그 엣지가 Kruskal 순위 최상위라, 커널이 같은 DC 등식을 실제로 풀었다(§4.7-0 A1, 계획 X-IT1). 옛 문단 전문은 계획 history H2 'IT-1·IT-2 design' 행.
- 개정(정본 = §4.7-1 1~5; 이 항목의 '포트마다 W4 뿌리 후보'·'뿌리 둘 이상 정지'는 아래 v1.15.2 개정이 대체): 입력 DC 미선언이어도 '같은 DC' 엣지를 G_vgs 에 넣지 않는다. F 밖 입력 포트는 각자 성분의 W4 뿌리 후보로 남고(항목 5 의 뿌리 규칙 그대로), **y 키 = 뿌리 넷**(`INPUT_GROUP_KEY` 없음). 한 성분 안 뿌리가 아닌 입력 포트는 트리 경로(MOS VGS)로 쓰인다. 입력 포트인 W4 뿌리가 둘 이상이면 `unsupported_rule_branch`(rule_branch `input_port_multiple_roots`)로 탐색 전 정지한다(IT-Q1 (나), DEC-76).
- 결과(O-13 (1)): 같은 DC 엣지로 생긴 종속은 0이다. 포트 경로가 둘 이상인 v1 고리는 ΔV를 소거한 KVL 하나가 남아 그 고리 멤버 하나가 `cycle_vgs` 종속이다(파일럿 VGS1a − VGS1b = VGS4a − VGS4b, M1b). 대칭이면 그 등식은 대칭 묶음과 중복이다. 종속 수 = 순환수 불변식은 '같은 DC 엣지 없는 G_vgs(F 한 점)' 기준이다. `input_tie` relation·`TIE_INPUT_ORDER` 기록과 그 어휘는 IT-1이 같은 변경에서 지운다.
- **v1.15.2 개정 -- 차동 입력쌍 한 점(계획 DEC-106, card IT-1 범위 재작성 1~4, 사용자 결정 O-168; **원래 취지와 다름(O-168 -- 계획 표지)**: O-13 (1) (가)·K-3 전제 '대칭이면 묶음과 중복'이 단일 출력 회로에서 성립하지 않음)**: 위 '개정'의 'F 밖 입력 포트는 각자 성분의 W4 뿌리 후보'와 '입력 포트인 W4 뿌리가 둘 이상이면 `input_port_multiple_roots` 정지'는 대체된다 -- 규칙 정본 = §4.7-V 첫 행·40 §3.11-4(입력 점 한 점, y 키 하나, 그 밖 다중 입력 `input_cm_undefined` 정지). KVL 귀결(DEC-106 (3)): 두 포트를 지나는 고리는 ΔV = 0 KVL이고 종속 소자 하나를 만든다; 종속 수 = F 한 점·입력 점 한 점으로 묶은 G_vgs 순환수; 자기동형 궤도 묶음(DEC-97)은 그대로이고 종속 소자는 θ 성분이 없어 DOF를 두 번 빼지 않는다(IT-1 완료 조건 1 (f)). 아래 'K-3 축소'의 '서로 다른 성분 뿌리인 입력 포트 → 정지'는 대상 소멸. g = s 소자 한 규칙(E-19)은 40 §3.11-5.
- **K-3 축소(X-IT5, 원래 취지와 다름 -- 사용자 결정 O-13 (2) 승인)**: 옛 개정 문언의 '대칭 궤도가 같은 포트들의 y 는 U2 자기동형 묶음(`domain.ties`)이 하나의 변수로 묶는다'(서로 다른 성분 뿌리인 입력 포트의 경우)는 **미구현(발동 0)**이고 그 경우는 정지한다. 발동 회로가 library에 들어오면 그때 구현한다(계획 N6.5 범위 4).
- 영향 확인 대상(card 0 IT-0 M-I1~M-I7, 계획 N6.5 순서 0): 입력 DC 미선언 회로의 종속 소자 목록·W4 뿌리·y 키·θ y 수·층 0 시작점·봉인·결과 JSON 키·입력 포화 창(M-I4: 뿌리 아닌 포트와 뿌리의 전압 차, IT-Q2 판정)·DOF·순환수 = 종속 수(library 9회로). 입력 DC 가 선언된 회로는 입력 포트가 F(W2 `input_dc`)라 이 개정과 무관하다 -- 그때 두 포트를 지나는 고리는 v1 이 아니라 F 경유 v2 와 같은 처리(ΔV = 선언 차)다(계획 DEC-64 v1 'ΔV 는 입력 DC 선언이 있으면 그 차'). 무동작 확인 = library 선언 2회로 쓰기 계획 필드별 동일(M-I7, NFR-4).

**2. 노드 전위(출발 모델)**: 계획 순번대로 쓴다. 고정 = 레일·W3·입력 DC(절대값). MOS writer 는 커널과 같은 역산 `vgs_for_current_density`(ln IDu, L, VDS, VSB). 저항 = 선언값 × KCL 기저 전류(강하 기지). **값 미선언 DC 경로 저항**(v1.15.0 개정, 계획 DEC-104 (4)·O-127 (iii)·O-128 Q2, headroom-chain N3.1-1): 강하 V_R은 출발 단계에서 미지수다 -- 그 저항 변은 κ에 넣지 않고 R-1′ 차분 변 쌍(x_far − x_near ≥ V_R,lo, x_near − x_far ≥ −V_R,hi)으로 넣고, V_R 구간 = spec 저항 상자(`search.theta_bounds`, §5.3.3 'θ 저항') × I_R(`dc_current_basis` 그 가지 전류)이다. 출발 V_R 값은 R6 블록(11)이 R5′로 정하고 R = V_R/I_R은 파생값이다(매크로 AC가 쓰는 R도 이 파생값 -- 사본 아님, 같은 블록 출력을 READS). I_R ≡ 0인 저항은 DC θ가 아니다. θ점 DC 전류가 0인(가지치기로 잘리지 않는) DC 경로 저항은 R 자체를 θ 독립 성분(spec 저항 상자 안)으로 두고 V_R 미지수를 쓰지 않는다(O-157 S6, §5.3.3 'θ 저항'). 값·상자 둘 다 미선언이면 단계 A 정의 불능(O-151 N-5). 옛 문언 '저항 = 선언값 또는 θ 저항 상자 기하 중심 × KCL 기저 전류'와 순수 함수 `theta_box_centre`의 이 절 쓰임은 삭제한다(상자 중심 R은 근거 없는 자리값 -- 감사 `theta_basis_principle_audit.md` §2.5; `layer0_center._box_centre`는 무동작·조립 실패 출발점 경로에서 θ 독립 성분에만 남는다, §5.10-3 -- v1.15.2: 그 경로의 존치는 **계획 v6.38.4 대기(P4)**). W4 창 넷 = 그 넷을 뿌리로 한 **상대 전위**(같은 뿌리끼리의 차만 쓴다 -- y 와 무관). VDS·VSB 는 두 단자 전위가 같은 뿌리로 알려지면 그 차(VSB 는 절대 전위일 때만), 아니면 그 소자의 곡선 동작점(§6.1-6). 1변수 노드(diode gate·소스 추종 source)는 커널처럼 `bracket_root`(창 = 레일 범위, 상대면 아는 쪽 ± 레일 폭). drain 이 뒤 순번에서 쓰이는 writer 가 있으므로 전위 변화가 행 분해능 이하가 될 때까지 바퀴를 되풀이한다(상한 = 넷 수). 봉인 평가를 쓰지 않는다(§0 단계 A 규칙).

**3. 행**(값 ≥ 0 이 만족, 단위 V, 분해능 = 그 소자들의 LUT `tol_vdsat` 최솟값):
- `loop_lo`·`loop_hi`(v2 고리만): 종속 소자 m 의 고리 VGS_m 이 m 의 출발 구간 안 -- VGS_m − VGS(gm/ID_hi,m) ≥ 0, VGS(gm/ID_lo,m) − VGS_m ≥ 0(`vgs_for_gm_id`, 그 점 VDS·VSB). gm/ID_lo,m 은 구간 하한과 최소 폭 하한(§6.5 as-built) 중 큰 값. 종속 소자의 gm/ID 는 고르지 않고 등식이 정한다(DEC-64 '하나의 gm_id 가 종속된다').
- `saturation`: VDS − VDSAT − tol_vdsat ≥ 0(§6.2 와 같은 포화 규칙). VDSAT 는 gate 전위도 알면 그 VGS 점의 LUT 열, 아니면 출발 gm/ID 의 곡선 값. 선형 선언 소자는 제외(봉인 7 제외와 같다).
- `writer_root`: 1변수 노드의 창 안 근이 없거나 writer 역산이 정의되지 않음 -- 값 = −(끝점 |h| 최솟값, 없으면 레일 폭). 커널 `no_root_in_window` 와 같은 사실이다.
행마다 **의존 묶음**(행의 넷을 쓴 나무 경로의 writer 와 자기 소자의 같은 VGS 묶음 뿌리)을 S0 에서 구조로 한 번 정한다. **v1.15.0**: `saturation`·`writer_root` 행과 의존 묶음은 R-1′ 제약 그래프 S0 필드의 변·writer_root 행과 변 좌표 집합 속성을 READS한다(1의 개정 -- 이 절이 다시 만들지 않음). `loop_lo`·`loop_hi`는 쓰기 계획 v2 고리 등식(X)의 종속 소자 구간 행이라 쓰기 계획 필드(`device.dc_coord`)에서 읽는다(R-1′ 필드의 대상이 아님 -- X는 등식 고리의 종속이고 재개방 좌표가 아니다, O-141 (3)).

**4. 공동 선택(7a)** -- 결정론, 상한 있음:
- 선택점(§6.1-7, 최소 폭 보정 뒤)에서 모든 행이 0 이상이면 아무것도 바꾸지 않는다(대부분 회로가 이 경우여야 한다 -- 측정으로 확인).
- 아니면 변수 = 위반 행의 의존 묶음에 든 **writer VGS 묶음**들. 묶음 j 의 gm/ID 는 **자기 구간 [바닥_j, 상한_j] 어디로든** 움직일 수 있다(올림 허용, 사용자 결정 B3; 바닥 = max(구간 하한, 최소 폭 하한)). 정규화 위치 x_j = (g_j − 바닥_j)/(상한_j − 바닥_j) ∈ [0, 1], 출발 = 선택점 위치 x⁰_j. 제약 = 변수에 닿는 모든 행 ≥ 0. **v1.15.0 개정(계획 DEC-104 R5′ (4)·R7, O-142 -- 구조 순위표·동률 규칙 없음)**: 변수를 한꺼번에 열지 않고 비용 순으로 연다 -- (i) 깨진 행에 걸린 W4·V_R(위치가 없어 max-min 대상 = 깨진 행 여유) → (ii) B 묶음(구간 = 고리 나머지 구간 ∩ R7 가드 필드 `device: start.guard` 구간, max-min 대상 = gm/ID 위치; 교집합이 비면 fail-closed 충돌 기록) → (iii) S만 남으면 S 정의역 조건(R-1′ 행 -- 출발 단계에서는 그 S 묶음의 구간 자르기, 층 0이 같은 정의역을 읽는다; 범위 끝 이득 행은 자르지 않고 '이득 행 재개방' 표지만 R6 출력 필드에 남긴다 -- 탐색 개방은 층 0, O-159 E-3·O-160 F-3). K-1 (i)에는 깨진 R-1′ 행 위반 다음 순위로 `mirror_vds` 목표 행(DEC-105 (4)), (ii) B 단계에는 가드 합 행(DEC-105 (5))이 든다. 선언 범위 고리의 B는 재개방 전 기본값이 R5′ (1) 나머지 경계다(R7 (가)). 단계마다 열린 좌표를 아래 (i)~(iii) 기준(K-1)으로 함께 고르고, 그 단계에서 모든 행이 0 이상이 되면 멈춘다. F·X 묶음은 열지 않는다(L-11·O-141 (3)·U-117). 가드 구간은 정본 필드에서 읽고 헤드룸·속도 경계와 섞인 출발 구간을 대신 쓰지 않는다(한 점으로 줄어든 구간에서는 종속이 움직이지 못한다 -- 시제품 §수정판 B).
- 목적(기준 = gm/ID 큰 쪽, §6.1-7 과 같다): (i) 위반 최소화(min v, 행 + v ≥ 0, v ≥ 0)로 실행 가능 여부를 정하고, (ii) 가장 낮은 위치 min_j x_j 를 최대화(max-min), (iii) 그 값을 하한으로 고정하고 Σ x_j 최대화. 세 단계 모두 SLSQP, 변수 순서 = 구조 색 순(이름 전단사 불변), FD 스텝 = 사다리 분해능 2^−steps(§6.1-9 의 steps), maxiter = 변수 수 × steps(layer0 `_maxmin` 과 같은 규칙), ftol = 2^−steps. 결과 점에서 행을 다시 잰다(풀이 결과를 믿지 않는다).
- **매크로·면적 재확인(B3)**: 위치를 올린 묶음이 있으면 그 점에서 §6.5 매크로 모델(`current_model` + `macro_solve` **기본 호출** -- 키워드 인자 `node_c`·`gm_bounds`·`gain_targets` 없음, §5.3.6 '기본 호출 불변', 확정 풀이와 같은 설정)과 면적 추정(§6.4-5)을 다시 푼다 -- §6.1-7 의 실행 가능 판정과 같은 식(면적 ≤ 예산, 매크로 근 있음). 실행 불가면 올린 묶음들의 위치 상한을 선택점 위치 x⁰_j 쪽으로 반씩 좁혀(x 상한 = x⁰_j + (상한 − x⁰_j)/2^k) (i)~(iii)을 다시 푼다. k 는 0 부터 steps 까지(상한 steps + 1 회), k = steps 에서 올림이 사실상 없어진다. 매크로 결과가 바뀌면 전류가 바뀌므로 최소 폭 보정(§6.5 as-built)과 행 재측정을 거친다(§6.1-8 의 반복 상한 = 소자 수 안).
- 채택 점에서 종속 소자의 출발 gm/ID 는 고리가 정한 값으로 바꾼다(보고·면적 추정 일관).
- **v1.15.1 -- K-1 (i) 위반 최소에 드는 행 추가(계획 v6.38.2 DEC-105 (4)(5), card LA-1 범위 15 (c)(d))**: (가) **체계 오프셋 목표 행 `mirror_vds`** -- 술어 인스턴스 S0 필드(아래 11 '술어 인스턴스')의 인스턴스마다 목표 등식 VDS_o − VDS_d = 0(P1s; n의 KVL로 VGS_g = VGS_d와 같음) 또는 VGS_a = VGS_b(P1c)를 위반 최소 단계의 목표 행으로 넣는다 -- 순위는 깨진 R-1′ 행 위반 **다음**(R-1′ 위반을 먼저 줄이고 같은 위반 수준 안에서 이 행 위반을 줄인다). 이 행이 움직이는 좌표는 R6 종속 성분 가운데 B 밀도뿐이다(기본안 (가) -- U-126 승인 O-166: R5′ (2) W4·V_R 선택('K-1 (ii) max-min'만)에는 넣지 않고, S 좌표(gm/ID·L)는 바꾸지 않는다, X-LA8). R7 (가) 선언 범위 고리의 B는 나머지 경계로 정해져 이 행이 움직이지 않는다(남는 위반은 기록). 적용 = R7 (나) 그 밖 B 선택과 R5′ (4) 재개방의 K-1 (i). 해가 없으면 `StartConflict(quantity="mirror_vds", margin = 남은 |VDS_o − VDS_d|)` 기록(정지 아님, `graph/start: conflicts` 항목). 층 적용: 그 사슬(n을 지나는 VGS_g = VGS_d)의 구성원 좌표가 출발 단계에서 모두 정해지면 출발 스냅샷에서 한 번(graph reuse), 층 0 변수가 섞이면 층 0 후보 스냅샷마다 같은 R6 블록이 평가; 외층은 묶이지 않는다(EP-7). 판정은 계통 offset metric(DEC-23·O-53) (나) **R7 가드 합 행**(§6.4-2a v1.15.1 (b)) -- B 선택의 위반 최소 단계에서 소자별 가드 구간과 함께 읽는다.

**5. 해가 없으면(fail-closed)**: 위반 최소화 결과에서도 행 < 0 이 남거나, 4 의 좁힘을 다 써도 매크로·면적과 행을 함께 만족하는 점이 없으면 `StartConflict(quantity="kvl")`(§6.6)를 남은 행마다 남기고 위반 최소 조합(매크로·면적이 실행 가능한 쪽 우선)을 출발점으로 넘긴다. 다른 경계를 조용히 넓히거나 행을 빼지 않는다.

**6. 적용 위치(배선)**: `start_intervals` 블록의 선택점(사다리 칸 0)과 사다리 아래 칸 각각(칸의 t 위치가 출발, 구간 전체가 정의역). U15 `placer.place`는 덮어쓴 묶음을 고정하고 나머지만 바꾼다(§5.10-3). §6.1-7 의 t 괄호 탐색 안에서는 부르지 않는다(t 를 정한 뒤 한 번). 호출 경로: 단계 A `start_intervals`(7a 포함) -> S0 수준 필드 `start.row`·`start.point`·`graph/start` -> 단계 B `layer0_start` / `layer0_budget` -> `find_front`. 단계 B는 이 필드를 읽기만 한다.

**7. 인터페이스**(S0 수준 필드, 40 §2.4.2·§2.4.8. 묶음 객체 `StartContext`·`StartIntervals`는 없앤다, 40 §2.4.7):
- (v1.15.0 개정 -- 계획 v6.38 후속 정정 표 "`graph/start: kvl_model`·`kvl_rows`는 R-1′ 필드 READS로 대체(둘째 생산자 금지)") 옛 S0 수준 필드 `graph/start: kvl_model`(쓰기 계획·고정 전위·종속 소자·의존 묶음)과 `graph/start: kvl_rows`(선택점 행 표)는 **두지 않는다** -- R-1′ 제약 그래프 S0 필드(TB-1)와 같은 사실이라 둘째 생산자다. 고리·행·의존 묶음은 R-1′ 필드를, 고리 등식 종속은 쓰기 계획 필드(`node.dc_writer`·`device.dc_coord`)를 READS한다.
- 기록 `kvl_adjusted{groups, min_position}`·`kvl_macro_recheck{k}`·`kvl_unsatisfied{rows}`는 `graph/start: records`(KVL 기록은 U17 ②에서 더한다. U17 ①-b의 `records` = as-built 매크로 모델 기록 -- 40 v1.9.1 D3), 충돌은 `graph/start: conflicts`다. 채택된 S·F 소자 gm/ID·L(θ 독립 성분)은 `device: start.row`, (VDS, VSB)는 `device: start.point`다 -- `start.row`·`graph/start: rungs`에는 B 선택값·B ln IDu 칸을 두지 않는다(DEC-104 (3)(c), O-151 DK1). B 소자의 고리 종속 값(B ln IDu·종속 W4·V_R·재개방 표지)은 R6 블록 출력 필드(아래 11)이고, 커널에 넘기는 θ는 두 필드를 참조로 읽어 조립한 점 좌표다(값 사본 아님).
- `StartConflict.quantity` 어휘에 `"kvl"` 추가. 출처 어휘 `SRC_KVL_LOOP`·`SRC_KVL_SATURATION`.
- 새 파일 `E/search/iv_kvl.py`(행 평가 -- v1.15.0: 진입점 `kvl_model`(필드 writer)은 없앤다, R-1′ 필드 READS), `E/search/iv_kvl_choice.py`(진입점 `kvl_choice`, 4·5 -- v1.15.0: 이 진입점이 R6 블록 `loop_dependents`의 본체다, 아래 11).
- 재사용: 행 평가는 같은 x 벡터를 한 선택 호출 안에서만 묶는다. 이것은 호출 지역 변수이고 호출 밖으로 나가지 않는다(40 §2.4.10 G-8 허용, 상한 = 그 호출의 평가 상한 maxiter·(변수 수 + 2)). LUT 조회는 LUT memo `memo.call`(40 §2.4.6)이다.

**8. 비활성**: 레일 전위 미선언(`rail_potentials_undeclared`) -- 절대 전위 행 없음(상대 행은 남는다). 저항 전류·값이 없는 넷은 '정해지지 않음'으로 그 넷을 쓰는 행이 생기지 않고 사유 `kvl_node_undetermined{net}` 을 보고한다.

**9. 불변식**: 같은 입력이면 같은 행·같은 선택. 이름 전단사는 행 이름만 바꾼다. 위반이 없는 회로의 출발 θ 는 v1.5 와 비트 동일(1a 커널 개정이 바꾸는 입력 DC 미선언 회로는 개정된 쓰기 계획 기준으로 같은 말).

**10. 계획과의 관계**:
- (P1, 남음) 계획 DEC-71 (7)·N3.7 층 0 은 `kvl_branch` 등식을 **조립 단계**에서 푼다(정밀 경로는 내층 DP 의 W2 블록). 이 절은 같은 등식을 단계 A8 출발 선택에도 건다(사용자 결정 9). 조립의 처리는 바꾸지 않는다.
- (P2, 닫힘 -- B1) 역산 우선(DEC-71 (4)(a))은 층 0 의 몫이고 §6 은 그 정의역(구간)을 준다(위 '층 0 과의 관계').
- (P3, 닫힘 -- B1) VDS 배분(DEC-71 (4)(c))은 층 0 의 몫이고 이 절은 고리가 정한 VDS 만 검사한다.
- (P4, 닫힘 -- B2) DEC-64 v1 은 제약 없음(같은 DC 등식 없음, ΔV 소거 KVL은 남음 -- O-13 (1)). 커널 쓰기 계획을 1a 로 맞춘다(구현 = card IT-1, 계획 N6.5).
- (P5, 닫힘 -- K-1) 공동 선택 기준(위반 최소 -> max-min 위치 -> 위치 합 최대)과 매크로·면적 재확인의 좁힘 규칙(반씩, 상한 steps + 1 회)을 승인했다(사용자 결정 2026-10-12 "K-1~K-3도 권고대로" K-1 "KVL 고리 공동 선택 기준 승인 -- 위반 최소 -> 가장 낮은 위치 최대(max-min) -> 위치 합 최대, ... 그래도 없으면 StartConflict(kvl) 기록 + 위반 최소 조합 전달").
- (P6, 닫힘 -- B3) '낮춤만'·'매크로·면적 재확인 생략' 가정을 없앴다(4 의 재확인).
- (P7, 조건부 닫힘 -- K-2) §7.5 β·C_eff 정의는 "design 검증에서 지적이 없을 때 승인(지적이 있으면 다시 묻는다)"(K-2). design 검증 지적이 나오면 다시 묻는다.
- (P8, 닫힘 -- K-3) 1a 의 `input_tie` 폐기를 승인했다: "입력 DC 미선언 시 입력 포트를 같은 DC 로 묶던 input_tie(U2 기본안 (a)) 폐기, 대칭 포트는 U2 자기동형 묶음(domain.ties)이 대신, 구현 순서는 결정 6(d/s 맞바꿈) 다음"(K-3). U2 기본안 (a)를 대체한다. 구현 = card IT-1(계획 N6.5). '대칭 포트는 `domain.ties`가 대신'(서로 다른 성분 뿌리인 입력 포트)은 미구현(발동 0)·정지로 축소(X-IT5, 사용자 결정 O-13 (2) 승인, 1a).
- (P1, 닫힘) 위 첫 항목. PQ5 결정(사용자 결정 2026-10-12 "3은 권고대로"·"L14부터 PQ5까지")으로 닫혔다.
- (P9, v1.15.0) 계획 v6.38 DEC-104가 이 절의 원리·층 0 관계·1·2·3·4·7을 고쳤다(위 각 항목의 'v1.15.0' 표지). 원래 취지와 다름 승인 = O-127(R-1′ 쓰임 판정 → 구성, 출발 단계가 B 밀도 고리 정합)·O-128 Q2·O-142(R5′ 비용 순 재개방, writer = 7a 블록 하나).

**11. DEC-104 R6 블록 -- 고리 종속 값의 writer 하나**(계획 DEC-104 R6·R7·(3)(b)(c)(d), 사용자 결정 O-142 (5)·O-144 J3; 구현 card = LA-1(U17 ② §6.7과 같은 통합 병합), 읽는 필드를 만드는 card = TB-1):
- **정체**: 7a(4·5)의 `kvl_choice`를 R5′ (1)~(5)로 확장한 `@compute_block` 하나 -- writer 이름 `loop_dependents`(파일 `E/search/iv_kvl_choice.py`, 진입점 `kvl_choice`). 출발 단계 스냅샷과 층 0 후보 스냅샷에서 **같은 블록으로** 불린다. 구성원이 모두 출발 단계에서 정해지는 고리는 입력 버전이 같아 graph reuse로 한 번 계산된다(40 §2.4.4 호출 규칙 1·2). 따로 두면 B 출발 gm/ID writer가 둘이 되므로 출발·층 0 공용 하나다(O-142 (5)).
- **READS**: R-1′ 제약 그래프 S0 필드(고리·변·writer_root 행·변 좌표 집합 -- TB-1, 형식 = headroom-chain HC-D design), 분류 필드 `device: theta_class`(TB-1), R7 가드 필드 `device: start.guard`(소자별 구간 + 합 행 -- card LA-1 범위 15 (d), writer = 출발 단계 블록 하나), 체계 오프셋 술어 인스턴스 S0 필드(DEC-105 (4) -- card LA-1 범위 15 (c)), spec 출력 범위 키(card SF-1 범위 3 -- 없으면 선언 범위 갈래 비활성), DE-1 (e) 범위 끝 증분 DC 이득 칸(봉인 스냅샷에서 master에 있을 때만, 재개방 여부 판정에만 -- O-159 E-1·E-2; 없으면 같은 순수 함수를 블록 안 값으로 부름), 쓰기 계획 필드(`node.dc_writer`·`device.dc_coord`), `graph/kernel: search_domain`·spec `search.theta_bounds`(V_R 구간), `dc_current_basis`(I_R), 그 스냅샷의 S·F θ 독립 성분과 LUT memo(40 §2.4.6). 층 0 후보 스냅샷에서는 후보 θ(독립 성분)가 extras다.
- **값**: 고리 종속 성분(B ln IDu, V_R, 종속 W4)과 R5′ (4)(iii) '재개방 표지'(값 = R-1′ 정의역 자르기 / 이득 행 탐색 개방 -- 이득 값은 층 0 거르기 소비자가 거부에 쓰지 않음) -- R5′ (1)~(4)(위 4의 개정과 §5.3.4 (c-1)~(c-3)). 수리·외층·Halton·상자 중심 경로는 이 값을 바꾸지 않고 독립 성분만 움직이며, 종속 성분은 같은 블록이 다시 파생한다(R6).
- **출력 자리**(계획 DEC-104 (3)(c), O-151 DK1·O-162): R6 블록의 출력 필드 하나 `graph/start: loop_dep` = `LoopDep(b_ln_idu, w4, v_r, reopen)`(정렬 tuple 칸 넷 -- 소자·넷·저항·행 키별; 이름 = v1.15.1 확정) = (B ln IDu, 종속 W4, V_R, 재개방 표지). 출발 단계 스냅샷과 층 0 후보 스냅샷에서 같은 블록이 같은 필드에 쓰고(입력 버전이 같으면 graph reuse), 층 0 후보 스냅샷은 스냅샷 파생 규칙 5 하나로 정한다(검증 m-4: v1.15.1의 두 안을 한 규칙으로): 그 평가가 R6 블록(`loop_dependents`)을 부르므로 keep = base writer ∪ 부르는 블록에서 R6 writer는 부르는 블록 쪽이고, base(`ctx.base`)에는 R6 writer가 없어야 한다 -- 봉인 4 단언(base writer ∩ 부르는 블록 = ∅)이 이를 단언하고 어기면 fail-closed(O-155 m-10; 40 §2.4.4 규칙 5). `device: start.row`·`graph/start: rungs`는 θ 독립 성분만 담고(`start_intervals`가 writer 그대로), 커널 평가 입력 조립(층 0 후보·출발 시작점)이 두 필드를 참조로 읽어 점 좌표를 만든다(소비자 = card LA-1). 옛 '미정' 단락과 해소 후보 (가)(나)는 삭제(as-built writer 구조를 근거로 쓴 문단 -- DEC-104 (1′)).
- **술어 인스턴스**(계획 DEC-105 (4), card LA-1 범위 15 (c), U-132 기본안 승인 O-166): 체계 오프셋 술어 P1s(diode d / 미러 출력 o / n = o.drain에 diode 없음 / n에 gate가 닿는 g가 d와 같은 kind·같은 source)·P1c(미러 쌍 (r, o)의 drain을 각각 source로 쓰고 kind·gate가 같은 쌍 (a, b))의 인스턴스 가운데 **신호 경로 인스턴스**(n이 어느 여기 뷰 또는 되먹임 경로에서 신호 넷 -- 넷 술어의 부정, 바이어스 분배 쌍 제외 -- 기본 술어는 계획 오케스트레이터 원칙 기본안 그대로)를 S0 필드 `graph/start: mirror_vds_instances`(§5.12.6 E16)에 쓴다. 넷 술어는 `bias_fixed_net(views, net)`(S1v 순수 함수 하나, `E/graph/s1v_predicates.py` -- 제작 = card IT-1 v6.38.3 범위 재작성 5, 40 §3.11-5)이고 이 card(신호 경로 = 그 부정)와 card SB-1(R10 대상·C_lower '바이어스 고정 넷')이 부른다(사본 금지; v1.15.2 정정 -- v1.15.1의 옛 술어 이름·파일과 '이 card가 만들고 순서 LA-1 → SB-1'은 계획 v6.38.3 여덟째 커밋 배정과 달라 삭제, 기록 = git `ecd634d8` 판). 소비자 = 이 블록의 `mirror_vds` 목표 행(위 4 v1.15.1).
- **R7 가드 필드 writer**: 출발 단계 블록 하나(`start_intervals`) -- §6.4-2a 부하 gm/ID 상한·§7.5 잡음 가드 계산을 `device: start.guard`로 옮기면서 DEC-105 (5) 규칙으로 고친다(가드 입력 전류 = 매크로·KCL 전류만, W_min 클램프 점 제외, 단조 구간 안 hull, 절대 offset·잡음 제약 회로에도 '부하 기여 ≤ 입력 기여'; 결함을 정본 필드로 옮기지 않음, 사본 금지). 값 형식 = B 소자별 `GuardInterval(gm_id_lo, gm_id_hi, sources)` + 합 행(Σ 부하 기여 ≤ 가드 비 · Σ 입력 기여). 소비자 = 이 블록(R7·R6 K-1). 필드·writer·R6 READS는 모두 card LA-1 범위 15 (d)가 만든다(U-132 기본안 승인 O-166 -- 필드와 소비자가 같은 card라 병합 순서 규칙 없음; 옛 'TB-1 자리·O-149 통합 병합' 삭제).

**12. 정착 선언과 대역폭 출발 목표**: §6.8-2.

### 6.8 공급 요구 하한과 정착 출발 목표 (계획 DEC-104 R1·R8·R10, N3.8)

**6.8-1 공급 요구 하한(R8·R10 한 규칙)**(계획 DEC-104 R8·R10, DEC-71 (3) v6.38 -- 사용자 결정 O-143 (3)·O-144 J1·O-146 K1, **원래 취지와 다름(O-122·O-121 (가) 부분 복원, 승인 O-143·O-144)**):
- **쓰임**: 출발 단계(§6.1-8)와 층 0의 블록 전류 하한이다. 판정이 아니다 -- 슬루 판정은 oracle `.tran`만(40 §3.8-6·§4), 엔진 슬루 추정값·슬루 판정 행 없음(O-122의 판정 부분 유지).
- **대상**: 측정(출력) 노드의 그 방향 공급 셀이 **모두** '바이어스 구동 레일 source 셀'(S1v 구조 분류가 모든 뷰에서 β ∧ source가 레일 넷 -- 이미 있는 필드 둘(S1v 분류·`device.dc_role`)을 card SB-1 블록이 READS해 그 블록 안 순수 함수로 판정, 새 셀 속성 없음; O-144 J2·O-146 K1 (c)·O-157 S4 J2)인 경우만이다. 이 하한은 **가정 붙은 필요조건**이다((i)은 DC KCL이라 가정 없이 필요조건, (ii)는 비대상 가지의 순 주입 전류가 창 안에서 공급 방향을 돕지 않는다(≤ 0)는 가정 -- O-157 S4).
- **값**: (i) 정상상태 항 = 범위 끝 같은 점에서 그 셀들의 전류(같은 W·바이어스 LUT 조회 -- R9) 합 ≥ R_ss,d(응용 망 DC 해, 같은 출력 노드 KCL). (ii) 동적 항 = Σ I_cell(그 방향 셀 |VDS| 최대 끝에서 같은 W LUT 조회 -- R9) − min_창 I_load ≥ C_lower·SR_req -- 창 = spec `.tran` step의 20-80 %(이상 폐루프 출력 = step × 1/β의 20 %·80 % 수준 사이; spec step이 없는 회로만 그 구간을 덮는 레일 전 범위 -- O-157 S1 (4)), C_lower = 그 노드에 닿은 선언 수동 용량 가운데 다른 단자가 레일·바이어스 고정 넷인 것만(MOS 단자 용량·Miller Cc·되먹임 C 제외; '바이어스 고정 넷' = '모든 여기 뷰·되먹임 경로에서 신호 넷 아님' S1v 순수 함수 하나 `bias_fixed_net` -- card IT-1 v6.38.3 범위 재작성 5가 만들고 LA-1·SB-1이 부름, v1.15.2 정정). I_cell 값 = 봉인 DC 해가 있는 스냅샷에서는 DE-1 R9 필드 READS, 없는 스냅샷(출발 구간·층 0 커널 전)에서는 블록 안 **동작점 포락 하한**(대상 셀 VDS_op를 VDSAT 경계에 둔 조회 -- O-157 S4). SR 선언이 없는 방향은 (i)만 남는다. SR_req·창은 SF-1의 `.tran` 슬루 항목(40 §3.1-1), 범위 끝 V는 spec 절대 출력 범위 선언(`undeclared`이면 (i) 항을 두지 않고 범위 끝 양은 정의 불능 표시 -- O-154 Q1; (ii)는 범위 선언과 무관, SF-1 범위 3), R_ss,d의 응용 망 DC 해는 전류원 부하를 응용 망으로 표지하는 선언이 AP-1까지 fail-closed라 지금은 netlist 전류원 원소의 KCL 항뿐이다(N3.8 출력 구동 규칙 v6.38).
- **그 밖의 경우**(공급 셀에 신호 구동 셀이 섞임, 내부 노드)에는 엔진 슬루 하한·출발 목표를 두지 않는다(O-122 원형; O-157 S4 -- **원래 취지와 다름(승인 O-162)**: 옛 ''추정' 출발 목표로만' 삭제 -- 추정 오차 0.002~2×10⁴배, `wt/_drafts/evidence/2026-10-26/rereview_A_slew_la1order.md` §3).
- **writer·자리**(card SB-1): 출발 구간 블록 `start_intervals`(전류 상자 하한 갱신)와 층 0 블록 전류 하한 자리(DEC-71 (3) -- LA-1이 만든 자리에 SB-1이 배선) -- 저장 필드 0(노드 용량·θ 전류·LUT READS, DE-1이 지우는 `c_slew_farad` 같은 사본 없음). R4 정의역 자르기(하한이 이기면 gm/ID 정의역 상한 = gm_req/I_min)도 SB-1(O-155 m-11). 위반하면 기존 '전류 > 상자 상한' 충돌(§6.6).
- **거짓 거부 0 판정의 표본**(계획 card SB-1 완료 조건 (4) '표본 크기는 design이 정의 근거와 함께 정함', gap §3-5): 표본 = library 9회로 실행(선언 E_B)에서 R10 하한이 이긴 경우(그 하한 때문에 출발 구간·층 0 후보의 셀 전류가 올라간 경우 -- 완료 조건 (3) '하한이 이긴 횟수'와 같은 사건) **전부**(전수 -- 표본 크기 = 그 사건 수 자체, 상한은 선언 예산 E_B·N_T가 정함; 새 상수 0). 사건마다 하한이 없었을 때의 점(정의 -- gap D22: 하한 적용 전 출발 θ, 곧 그 θ 전류 성분만 하한 적용 전 값으로 두고 나머지 전류는 KCL 기저(`dc_current_basis`)로 전파한 점; 그 점이 KCL·전류 원뿔 밖이면 그 사건은 '대조 점 정의 불능'으로 기록하고 거짓 거부 셈에서 빼지 않고 따로 셈)을 oracle로 재(판정 = N3.8 슬루율·정상상태 정의), 그 제약을 통과하면 거짓 거부(하나라도 엔진 결함). 근거: R10은 필요조건이므로 반례 하나로 깨진다 -- 표본을 줄이면 반례를 놓칠 수 있어 전수가 정의상 최소 충분 표본이다. 사건이 0인 회로·방향은 '대상 0'으로 기록(판정 없음 -- 통과로 세지 않음).
- **셀 전류 출처**(계획 DEC-104 R10 '블록 안 값', O-151 DK2·O-157 S4·O-155 m-2; 구현 card = SB-1): 봉인 DC 해가 있는 스냅샷(층 0 반복의 커널 평가 뒤 포함)에서는 DE-1 R9 필드를 READS하고 함수를 다시 부르지 않는다. 봉인 DC 해가 없는 스냅샷(출발 구간 블록, 층 0 커널 전 국소 문제)에서는 출발 구간 블록과 층 0 블록이 각자 같은 R9 조회 순수 함수를 **동작점 포락 하한**으로 부른다(정의 축 = 동작점 미정, 봉인 값과 다른 양 -- graph 규칙 3). R9 조회 함수는 DE-1·SB-1 가운데 먼저 병합되는 card가 만든다(**계획 v6.38.4 대기(P6)**). SB-1 완료 조건 (4) 거짓 거부 0(표본 크기는 design이 정의 근거와 함께 정함).

**6.8-2 정착 선언의 대역폭 출발 목표('추정')**(계획 N3.8 '정착 측정 정의' 엔진 쓰임 -- 사용자 결정 O-139·O-142, U-118):
- 정착 선언 t_s·ε(SF-1 `.tran` `settle_s` 항목)가 있으면 ω_c,est = ln(1/ε)/t_s를 **'추정'**(단극·슬루 시간 0 근사의 **출발 목표** -- 필요조건 아님: PM이 큰 루프는 더 작은 ω_c로 정착한다; 경계·cut·판정에 쓰지 않음 -- O-157 S3)으로 내고 GBW_est = ω_c,est/(2π·β)다. 용도는 S 분류의 매크로 활성(R13)과 출발 목표뿐이고 판정이 아니다(판정 = oracle `.tran`).
- graph 필드 하나·writer 하나(spec `gbw_target_hz`에 사본으로 쓰지 않음). 그 필드를 만드는 card = LA-1. **필드 이름·층·β를 읽는 점 = 미정**(U-118 -- 계획 '미결 -- card LA-1 design에서 정하고 실측': 시제품에서 출발 W의 Cgg를 넣으면 β 0.086(GBW_est 318 MHz), 빼면 0.5(55 MHz) -- 층 0 W 뒤 고정점이 후보; 근거 `wt/_drafts/evidence/2026-10-26/r5r6_prototype.md` §수정판 B). 실측 전에는 정하지 않는다.
- S 분류(TB-1 필드)는 β·대역폭 값을 읽지 않고 '정착 선언 있음 + GBW 미선언'이라는 선언 사실로만 매크로 활성을 가른다(층 역전 없음 -- 재검증 n8).
- static settling error의 손계산 출발값 = 개루프 이득 A ≥ 1/(β·ε)(루프 이득 βA ≥ 1/ε, '추정'; β 정의와 읽는 점은 U-118 한 자리 -- 계획 metric 표 static settling error 행). 같은 물리량의 gain 선언은 두지 않는다(O-133). 쓰임은 출발 목표(§6.4-1 이득 하한의 목표)이며 β가 미정인 동안 이 출발값도 미정이다.

**6.8-3 LA-1 design 과제(계획 LA-1 착수 조건 'design 과제', 사용자 결정 O-142·O-139)**: (i) current_reuse 해결 선행 -- R7 가드 구간이 한 점으로 줄어 B 종속이 못 움직이는 문제와 입력 뿌리 W4 하나에 반대 방향 고리가 걸리는 문제(시제품 `r5r6_prototype.md` §수정판 B·J); current_reuse는 완료 조건 9에서 따로 보고 유지 (ii) β 읽는 점(U-118, 6.8-2). 둘 다 **미정 -- 실측 대기**(이 판은 정하지 않는다; LA-1 design 착수 실측 뒤 계획 결정으로 올린다). U-117(F 둘 이상 고리)도 같은 실측 뒤 결정이다(§5.3.3).

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
| current_reuse_telescopic_ota(파일럿) | `noise_out_int_vrms <= 450e-6`(V). 감지 = 차동 출력 v(Vop)−v(Vom)(view 미적음, 기본 포트 뷰), 대역 = 이 절의 적분 대역. 출처: `user_spec`(사용자 결정 2026-10-14 Q-S3, 근거 `_pilot_current_reuse/noise_basis.md` §4(c) C1: SPICE 438.5 µV @ 282 µW) |
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
- B(열잡음 평탄값)는 특성화 점 j마다 추정 B_j = (S_j − S_lo·r_j)/(1 − r_j)(r_j = (f_j/f_lo)^−EF)를 구하고, 아래 **두 조건을 모두 만족하는 가장 높은 주파수 점**의 B_j를 쓴다(사용자 결정 2026-10-12 "C-4는 (다)로" (1)).
  - (1) **피드스루**: (2π·f_j·|Cgd|/gm)² ≤ tol_point. Cgd와 gm은 같은 LUT 칸에서 읽으므로 새 상수가 없다.
  - (2) **평탄(plateau)**: j가 가장 낮은 이분 점이 아니면 |B_j − B_{j−1}| ≤ tol_point·|B_{j−1}| + (두 추정의 부동소수 반올림 허용분). 열잡음 평탄값은 주파수와 무관해야 하므로 이웃 점의 B 추정이 일치해야 한다.
  - tol_point = min(그 점의 ln S_vg(f_lo) 면 leave-one-out 오차, 그 셀 tol_a). LOO가 정의되지 않는 점(격자 가장자리)은 tol_a다. B의 주파수를 고르는 데 B의 tol을 쓰면 순환이라 flicker 면의 tol을 쓴다.
  - 근거(r1 실측 -- 피드스루 조건만 쓰면 긴 L·약반전 칸에서 B를 크게 낮게 읽음) = design 이력 H41-19. as-built `E/lut/noise_planes.py`가 이 규칙이다.
- 조건을 만족하는 점이 없으면 그 칸의 B는 '미상'(`no_feedthrough_free_point`)이다. 그 칸을 쓰는 잡음 metric의 resolution을 무한대로 두고 판정을 보류한다.

**칸별 적응 재측정**(사용자 결정 C-4 (2)(3), 구현 단위로 등록):
- 대상: 현 데이터로 B를 확정하지 못한 칸 -- 미상 칸, 피드스루·평탄 판정이 엇갈리는 칸, 계단형 칸.
- 방법: 칸마다 이웃 두 주파수 점 사이를 로그 이분해 새 점을 잰다(ngspice `.noise`, 생성기와 같은 DUT 줄). 위 두 조건을 만족하는 점이 생기면 그 칸은 멈춘다. 상한은 K_max(N3.6 식, 구간 = 로그 주파수 폭)다.
- 저장: 새 버전 noise 파일(`..._noise_r2.npz`, sha256·생성 메타). 기존 r1은 고치지 않는다.
- 시점: graph 재작성 ①~③(40 §11 U17) 다음, U16(9회로 E2E·오라클 대조) 전. 재측정 전 B 오차는 SPICE 오라클 잡음 대조가 잡는다(fail-closed).

**파생량**(읽는 쪽에서 계산하고 열로 저장하지 않는다):
- γ_eff = B·gm / (4kT)
- K = A·W·L(V²·m²): §6.4-3의 1/f L 하한에 쓴다.

**저장**:
- 추가 주파수 점은 **새 버전 파일** `..._noise_r1.npz`에 둔다. sha256과 생성 메타(모델 경로·sha, ngspice 버전, 온도, 코너, 주파수 점)를 함께 기록한다.
- 기존 v2 r2 파일은 고치지 않는다. `lut_v2_location.json`에 새 항목으로 더한다.
- 로더는 v2의 `SVG2_*`와 새 파일의 점을 합쳐 노출한다.
- 잡음 데이터가 없는데 잡음 제약이 선언되면 `SchemaRejectedError(noise_lut_missing)`이다.

**tol**: 칸별 `tol_noise`를 LOO로 계산한다(DEC-87 방법). 디스크 캐시 대상이다(v1.10: 실행 사이 유지, U-87 원래 취지의 예외, 40 §2.4.12 Q9).

**API**(신규): `noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams{A, B, ef, b_status}`. 옛 `SID_1F`는 단위가 잘못되어 있으므로 읽지 않는다.

### 7.3 metrics -- 봉인 스냅샷 잡음 해석 (MOD5)

**잡음원**:
- MOS: gate–source 사이에 게이트 환산 전압 잡음원을 하나 둔다. 값은 S_vg(f) = A/f^EF + B다. 이것을 드레인 전류 잡음 gm²·S_vg로 바꿔 drain–source에 스탬프하는데, 두 방식은 같은 양이다.
- 저항: 4kT/R.
- 값은 봉인 스냅샷 `ss`의 동작점에서 LUT로 읽고 W 배율을 적용한다.
- **포함 범위**(사용자 결정 Q11: CMFB·바이어스 포함): 회로의 모든 MOS와 저항이다. 스위치 kT/C 항은 spec이 `noise_testbench.sampling_caps[]`를 선언한 회로에만 더한다. **파일럿은 선언하지 않는다**(사용자 결정 2026-10-12 "C-2를 네가 확인해" C-2: 논문 Table I 300 µV는 Cadence 폐루프 테스트벤치(C1 = C2 = 500 fF 용량 귀환, CL = 1 pF)의 `.noise` 적분 출력 잡음이고, 기여 상위가 모두 OTA MOS이며 스위치가 없다 -- 판정 = OTA 소자 잡음 적분, 폐루프 귀환 조건).

**폐루프 모드**(`noise_out_int_vrms`, 파일럿):
- 선언된 되먹임 요소(feedback {Cf1, Cf2}, spec)로 루프를 닫는다. Cs는 입력 부하로 남긴다(CI-10 결정). 이 상태에서 출력 잡음 PSD를 구한다. 파일럿은 C-2대로 이 폐루프 조건의 OTA 소자 잡음 적분이 판정량이다.
- **스위치**(선언한 회로만, 현재 library 선언 0 -- 파일럿은 C-2로 선언하지 않음): 스위치 on-저항의 열잡음이 샘플링 커패시터에 남기는 값은 R과 무관하게 kT/C다. 그래서 spec 테스트벤치 선언 `noise_testbench.sampling_caps[]`(as-built 모양 `[{element, source}]` -- 요소는 topology 커패시터, 출력까지의 전달 이득은 엔진이 MNA로 계산하므로 선언하지 않는다)마다 kT/C_s × (그 커패시터에서 출력까지의 저주파 전달 이득)²를 출력 적분에 더한다.
- 이 항을 따로 기록해, 엔진(소자 잡음)과 오라클(스위치 포함 실제 SC 테스트벤치)의 구성 차이가 드러나게 한다.

**전달**: as-built MNA(같은 (G, C) 조립)의 adjoint를 쓴다.
- 출력 감지 노드에서 단위 전류를 주입해 adjoint 해를 한 번 구한다. 그러면 모든 잡음원의 전달 함수 Z_k(jω)를 한 번에 얻는다.
- ω마다 풀이 1회이며, 조립은 다시 하지 않는다(WP-23).

**입력 환산**: S_in(f) = Σ_k |Z_k|²·S_k(f) / |H(jω)|². H는 선언된 전달 뷰의 전달함수(gain metric과 같은 뷰)다.

**산출**:
- `noise_th_in_v2hz` = Σ_k |Z_k/H|²·gm_k²·B_k이다(열잡음 성분만).
- `noise_fc_in_hz`는 입력 환산 flicker 합 Σ|Z_k/H|²·gm_k²·A_k/f^EF_k가 열잡음 평탄값과 같아지는 f다. 1-D 근(`bracket_root`)으로 구한다.
- `noise_excess_th` = `noise_th_in_v2hz` / (input 셀 소자만의 같은 합)이다.
- `noise_out_int_vrms` = √(∫_{f_lo}^{f_hi} S_out df + 스위치 항)이다(스위치 항은 `sampling_caps` 선언이 없으면 0, 파일럿 = 0). 적분은 로그 격자 사다리꼴로 하고, 오차가 분해능 이하가 될 때까지 이분 세분한다(상한 K_max).
- 소자별 기여 표 `noise_contrib[{device|element, thermal, flicker, share}]`를 낸다.

**분해능**: metrics §9와 같은 방식이다. LUT 잡음 열의 tol_noise와 소신호 파라미터 tol이 adjoint 감도를 거쳐 전파된 값을 `MetricResult.resolution`으로 둔다.

**파일**: `E/metrics/noise_sources.py`, `E/metrics/noise_analysis.py`.

### 7.4 search -- 제약 행

다른 ss 제약과 같은 형식이다. 판정 단위는 c = (value − metric)/resolution이고, 풀이 척도는 40 §7.2를 따른다. 외층 전회로 판정 위치(DEC-74)도 그대로다.

### 7.5 출발 구간 -- 잡음

**`noise_excess_th ≤ 2` 가드**:
- 부하 소자 k의 열잡음 비는 (γ_k·gm_k)/(γ_in·gm_in)이다. 이 비의 합이 1 이하가 되도록 부하 gm/ID를 상한으로 둔다(강반전 쪽).
- 매크로 모델(§6.5)의 전류 비로 gm_k/gm_in = ((gm/ID)_k / (gm/ID)_in)·r_k이다. 여기에 LUT γ를 넣어 부하 gm/ID 상한을 역산하고, 그 결과를 §6.3 속도 상한과 교집합한다. **v1.15.1(계획 v6.38.2 DEC-105 (5))**: r_k의 전류는 매크로·KCL이 정한 전류만 쓴다(자리값 금지), W_min 클램프 점은 빼고, 합 행(Σ 비 ≤ 1)·hull 단조 구간·절대 잡음 제약 회로 적용은 §6.4-2a v1.15.1과 같다 -- 같은 R7 가드 필드 하나에 쓴다(§6.7-11).
- 헤드룸 하한(§6.2)과 충돌하면 충돌 레코드로 남긴다.

**파일럿 `noise_out_int_vrms`**:
- 폐루프 열잡음 적분은 매크로 근사로 v²_th ≈ N_in·γ_avg·kT/(β·C_eff)·(1 + 부하 비)이다(`noise_spec_proposal.md` §2.2와 같은 꼴, C_eff는 §6.5의 보상 소자).
  - **N_in의 구조 유도**(K-2 **결정**(사용자 결정 2026-10-12 "K-2 권고대로, GQ1/GQ3/GQ4, U-14,U-20,U-32,U-45 권고대로")): N_in = Σ_in γ_k·gm_k / (γ_avg·G_half). 합은 입력 셀 소자(S1v gain 제약 전달 뷰 첫 이득 블록에서 AC 역할 `input`인 MOS, `noise_excess_th`의 입력 소자와 같은 집합)에 대해서이고, G_half = gate가 한쪽 입력 포트에 닿는 입력 소자의 gm 합이다. γ_avg = 입력 소자 γ의 gm 가중 평균. 예: 차동쌍 2, current-reuse 2, 단일 입력 1. 유도(단일 출력): 입력 소자 k의 입력 환산 열잡음 4kTγ_k·gm_k / G_half²를 더하면 4kT·Σγ_k·gm_k / G_half²이고, 폐루프 잡음 대역 β·G_half/(4·C_eff)(1극)와 출력 환산 1/β²를 곱하면 N_in·γ_avg·kT/(β·C_eff)다. 옛 정의('입력 셀 소자 수')는 입력 소자들이 같은 gm·γ이고 한쪽 포트에 하나씩일 때의 특수형이다. 나머지 β·C_eff·kT/C·1/f 식은 검증 확인대로 승인됐다(같은 결정).
  - 출력 형태: 차동 출력(출력 포트 쌍 Vop − Vom)은 반쪽마다 C_eff·β가 같다는 가정에서 같은 식이다. 이 가정이 깨지는 회로(반쪽의 귀환 C가 다름)의 계수는 K-2 재확인 대상이다(**결정**(사용자 결정 2026-10-12 "GQ2, N1, N3, K2 권고대로")(U-70): N_in 구조 유도, 대칭 귀환 Cf1 = Cf2 식, 선언 귀환이 비대칭이면 그 계수를 '추정'으로 표시). gm이 소거되므로, 이 항은 보상 커패시터의 하한으로 작용한다. 하한 = 예산 중 열잡음 몫이 남도록 하는 최소 C_eff다.
- 예산은 나누지 않는다. 총 예산에서 kT/C 스위치 항(선언이 없으면 0, 파일럿 = 0, C-2)을 뺀 나머지를 열잡음과 flicker가 함께 쓴다.
- 출발 단계에서는 둘을 같은 몫으로 시작하고, 판정은 §7.3 전회로 계산이 한다.
- flicker 몫은 §6.4-3 1/f L 하한(입력 소자 W·L)으로 간다.

**1/f L 하한**: §6.4-3.

**β·C_eff 입력 배선(사용자 결정 2026-10-12 "K-1~K-3도 권고대로" K-2 "design 검증에서 지적이 없을 때 승인(지적이 있으면 다시 묻는다)", U13 열린 항목 `feedback_factor_beta_unavailable`·`c_eff_not_a_start_bound` 해소)**: (β, C_eff 노드, 샘플링 커패시터) 묶음은 S0 수준 필드 `graph/start: noise_inputs`다(writer = `start_intervals` 블록, S0당 1회, 40 §2.4.8). U17 ②에서 β·C_eff 계산과 함께 만든다(40 v1.9.1 D3, 근거: 소비자 위치). 새 상수 없음.
- **β**: spec `feedback.elements`(되먹임 소자) 각각의 입력 포트 쪽 단자 넷(authoring `_feedback_cuts`·metrics `noise_plan` 과 같은 절단 규칙)에서, β = ΣC_fb / (ΣC_fb + 그 넷에 닿는 다른 커패시터 값 합 + 그 넷에 gate 가 닿는 입력 소자의 cgg 추정 gm/(2π f_T)). 커패시터 값 = 선언값, engine θ 면 §6.5 매크로 출발값(`cap_values`), 둘 다 없으면 그 커패시터 값은 출발 정의 불능이고 β·C_eff 가드는 비활성(사유 `noise_feedback_cap_undefined` -- v1.15.2, 계획 N6.35 머리 원칙: 정의 불능 자리를 상자 중심으로 메우지 않음; 옛 'θ 상자 기하 중심(층 0 과 같은 값)' 삭제). 되먹임 소자가 커패시터가 아니거나 절단 넷이 정확히 하나가 아니면 비활성(`noise_feedback_cut_ambiguous`·`noise_feedback_element_unknown`, `noise_plan` 과 같은 사유 이름), `feedback` 이 결정 대기면 `noise_feedback_undeclared`. 입력쌍 차동 회로는 절단 넷마다 β 를 구하고 같지 않으면 작은 쪽(보수)을 쓰고, 그 계수를 '추정'으로 표시한다(비대칭 귀환, U-70 결정 "GQ2, N1, N3, K2 권고대로").
- **C_eff**: 구조 주극점 노드(§6.3 `dominant_node`)의 매크로 모델 노드 용량(§6.5 망 구성: 부하 + 소자 cgg 추정 + 보상 수동소자)에, 그 노드가 되먹임 소자의 출력 쪽 단자면 (1 − β)·ΣC_fb 를 더한 값. 주극점 노드가 정해지지 않으면 비활성(`dominant_node_undefined`).
- **열잡음 C_eff 하한**: v²_th,budget = (V_budget² − Σ_s kT/C_s·(C_s/ΣC_fb)²)/2(스위치 kT/C 항 -- 저주파 폐루프 전달 C_s/ΣC_fb, 남는 몫을 열잡음·flicker 가 같은 몫으로 시작, 위 '예산은 나누지 않는다'), 하한 C_eff,min = N_in·γ_avg·kT·(1 + 부하 비)/(β·v²_th,budget)(N_in은 위 구조 유도). γ_avg = 입력 소자 LUT γ_eff = B·gm/(4kT)(§7.2) 평균, 부하 비 = 위 가드와 같은 Σ(γ_k gm_k)/(γ_in gm_in)(출발점). kT 는 U8 `noise_integral` 과 같은 출처. 주극점 노드의 engine θ 커패시터가 있으면 그 출발값을 하한까지 올린다(값 경계 출처 `SRC_NOISE_THERMAL_C`); 모두 선언값이면 검사만 하고 모자라면 `StartConflict(quantity="capacitance")`. v²_th,budget ≤ 0 이면 `StartConflict`(스위치 항이 예산을 다 씀).
- **1/f L 하한(§6.4-3)**: 출력 flicker 몫 v²_fl,budget(같은 몫) ≥ Σ_in (K_k/(W_k·L_k))·(1/β)²·∫_{f_lo}^{f_cl} f^−EF_k df, f_lo = LUT 최저 잡음 주파수(U8 과 같다), f_cl = β·`gbw_target_hz`(폐루프 대역; 없으면 비활성 `gbw_target_missing`). 입력 소자는 같은 몫(대칭)으로 나눠 A_min = W·L, L ≥ √(A_min·IDu/I).
- 출발값 전용(EP-7), 판정은 §7.3 전회로 `noise_out_int_vrms`.

### 7.6 오라클 -- ngspice `.noise` 대조

- 오라클은 엔진을 import하지 않는다.
- **개루프 metric**(`noise_th_in_v2hz`, `noise_fc_in_hz`, `noise_excess_th`): 같은 free 모드 동작점 테스트벤치에서 `.noise v(sense) <입력원> dec ...`로 잰다. excess는 입력 소자별 기여(`.noise` 소자별 출력)로 계산한다.
- **폐루프 metric**(파일럿 `noise_out_int_vrms`, C-2): 논문 Table I과 같은 조건 -- 용량 귀환 폐루프(선언 feedback Cf1·Cf2, Cs 입력 부하, 부하 CL), CMFB·바이어스 포함, **스위치 없음** -- 의 `.noise` 출력 PSD를 적분한다. 적분 범위는 엔진과 같은 [f_lo, f_hi] 유도 규칙을 따른다(논문에 대역 명시 없음, spec의 대역 정의 유지. 오라클이 독립적으로 계산한다). 샘플링 kT/C는 재지 않는다(`sampling_caps` 선언 회로가 생기면 과도 기반으로 따로 잰다).
- **비교 허용오차**: 다른 metric과 같다. resolution과 `model_error_noise_*`(DEC-72)를 쓰고, 미측정이면 '판정 보류'다.
- **합격**: T5에 잡음 제약을 넣는다. `ORACLE_MEASURES`에 네 metric을 더한다.

### 7.7 상태

7.1~7.6 모두 MISS다. as-built 잡음 관련 코드는 `noise_1f_density`(옛 엔진)가 전부이고, 새 엔진에는 해당 코드가 없다.

---

## 8. 신규 공개 API

```python
def build_s1v(s1: S1, spec: SizingSpec, *, count_budget: int) -> S1v                                   # E/graph/s1v_build.py
def block_local_gain(snap: GraphSnapshot, s1v: S1v, view_key: str, block_key: tuple[str, ...]) -> BlockGain  # E/metrics/block_model.py
def achievability(s0: GraphSnapshot, lut: LutSet, spec: SizingSpec, pdk: PdkDecl, *, count_budget: int) -> GraphSnapshot  # graph/ach 필드를 쓴다(40 §2.4.8), raise InfeasibleTargetError
def start_intervals(s0: GraphSnapshot, lut: LutSet, spec: SizingSpec, pdk: PdkDecl) -> GraphSnapshot  # E/search/start_intervals.py, graph/start·device start.* 필드(40 §2.4.8)
def layer0_budget(ctx: SearchContext, s0: GraphSnapshot, *, count_budget: int) -> BudgetFront   # S0 수준 필드(graph/ach·graph/start·start.*·A9)를 읽는다(40 §2.4.2). 평가 예산·계수는 ctx 실행 계수, r̂는 S3 색인
def block_bounds_l0(s0: GraphSnapshot) -> GraphSnapshot                                           # 신규 A9(§4.2), graph/ach: block_bounds_l0 필드를 쓴다(40 §2.4.8)
# E/search/layer0_inverse.py (§5.3.3~5.3.6): 모듈 진입점 하나(파일당 진입점 하나 규칙)
def layer0_candidate(ctx: SearchContext, s0: GraphSnapshot, job: BlockJob, target_db: float, fixed_fp: str, choice: tuple) -> GraphSnapshot | FailureRecord  # (a)(c)(b)(d) 고정점 -> 국소 봉인 스냅샷
# E/search/l_targets.py (§5.3.7)
def l_targets(s0: GraphSnapshot, owner: str) -> LTargets   # {kind: mirror|replica|signal|other, knee_anchors, window, grid}, knee 는 LUT memo(40 §2.4.6)
def size_and_seal_local(ctx: KernelContext, theta_block, fixed, columns: frozenset[str]) -> GraphSnapshot  # E/sizing/size_and_seal_local.py (국소 스냅샷, 40 §2.4)
def macro_solve(ctx, model, gm_id, lengths, refine=True, *, node_c=None, gm_bounds=None, gain_targets=None) -> MacroResult  # E/search/macro_poles.py (§5.3.6)
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
| 층 0 역산(§5.3) | (a) 이름 없는 CS·캐스코드 toy 손계산(목표 gain → L, gm 요구 → gm/ID), 이상 소자 2단 VDS 배분 손계산, (b) 같은 bin 격자 전수 | `tests/search/test_layer0_inverse.py`, `test_l_targets.py` | 역산 L의 국소 gain ≥ T_b이고 한 제조 격자 아래 L은 < T_b. bin 경계 넘는 L 없음. 소자 종류(S 자유·B 제외·F 폴백·kvl 종속, §5.3.3)와 폴백 사유(`no_gm_requirement`·`l_inverse_no_bracket`·`lut_hermite_nonmonotone_cell`). 회차 2 이상 = 미해결 쌍만 재풀이·front 불변 정지(§5.3.2). 국소 결과 = 스냅샷, 조립 = graft(같은 입력 버전 재계산 0). 축소 상한(§4.2) ≠ exit 3 입력. VDS 배분 = 미분 큰 소자부터, 하한 위반 0. 고정점 수렴·NONCONVERGENT(비수축 픽스처). knee = 한계효율 최대 구간 위 끝(손계산 표), 면적 비단조 구간 건너뜀. 이름 전단사 불변 |
| 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 필요조건 성질 |
| 이득 L 하한 fail-closed·found_db 목표(§6.4-1 v1.15.1, card LA-1 toy 10 (a)) | (a) 손계산 toy | `tests/search/test_iv_gain_l.py`(이름은 test 주체 grep) | A_max 미인증 gain 선언 toy에서 활성(base 비활성 -- red), 평가 앵커 0 toy에서 하한 값 없음·margin null(base 가장 긴 앵커 -- red), 1회차 원소 없음 → `gain_l_element_undetermined`+원소 키, 미달 toy `StartConflict` margin = 목표 − 최선 이득·하한 = 최선 앵커, found_db 없는 블록 → `found_db_missing` |
| 매크로 P = 0(§6.5-3a, toy 10 (b)) | (a) RHP 극점 출발점 toy, 비출력 극점 노드 toy | `tests/search/test_macro_poles.py` | RHP 출발점은 사다리 다음 칸, 끝 칸까지 P ≠ 0이면 끝 칸 정의된 값으로 출발 + `StartConflict(macro_target, rhp_open_loop)`(옛 '`macro_rhp_start` 버림' 대체), 망에 N9 노드 포함 |
| 매크로 모델 | (a) 이상 VCCS 2·3극점, 캐스코드 노드 포함 | `tests/search/test_macro_poles.py` | UGF·PM 근, 근 없음 기록, 바퀴 수렴. **기본 호출 비트 동일**: 키워드 인자 셋이 None이면 `MacroResult`의 `fp_of`가 bd19cc6 기준 지문과 같다(이상 VCCS 픽스처 + library 매크로 활성 회로). 키워드 인자 호출은 `gm_bounds` 밖으로 나가지 않고 `gain_targets` 블록의 G_i = gm_i/10^{g/20} |
| **축소 격자 전수 대조**(P N3.7 검증, 사용자 결정 2026-10-12 "P-1~P-15까지 권고대로 고쳐" P-9 "9회로 축소 격자 전수 대조 추가(N3.7, NFR-5)") | (b) 다른 모델: 전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색(P N3.7 "사이징 대상 회로 전부에서 전체회로 MNA를 목적·제약으로 쓰는 축소 격자 전수탐색(다른 모델)과 대조한다") | `tests/integration/test_reduced_grid_crosscheck.py`(slow, 9회로) | 대조량 둘(DEC-77): (i) 축마다(전력·면적) 최적값 차, (ii) 같은 면적 상한 ε에서의 최소 전력 차(= front 점 대조). 각각 ≤ max(그 축의 격자 분해능(면적은 DEC-80), 모델 오차(DEC-72)), NFR-5와 같은 기준. 모델 오차 미측정이면 '판정 보류'. 단계 A·B에서 정지하는 회로(current_reuse·ngcc·nmcnr, P-1 정지 회로)는 그 정지를 기록하고 대조 대상에서 뺀 사실을 보고한다. 축소 격자의 정의는 계획에 없다(§5.12.5 PQ1) |
| 혼재 노드 구동 종류(§1.5-4, C-1 + 보완 (가)) | (a) 이름 없는 toy 셋(source 쪽 소자 drain 레일·gate 신호 노드 / drain 쪽 gate가 신호 노드 / 바이어스 넷), (d) 9회로 발동표 | `tests/graph/test_drive_kind.py`(toy), `tests/integration/test_drive_kind_mixed_9circuits.py` | toy: 첫째 전압 구동(근거 `follower`), 둘째 전류 구동(근거 `cascode`), 셋째 전압 구동. 9회로 발동표(옛/새/근거, 키 (회로, `view_key`, 노드)): 바뀐 키 = sf N910·N1112·N1516 + folded_cascode Vg10이 혼재로 판정되는 모든 뷰(모두 전류 구동)뿐, sf N17·N20 전압 구동 유지, 나머지 회로 무동작. folded_cascode: M8이 stage 시작 셀이 아님(base와 같이 유지, 시작 셀 = M1, M2)을 단언, 그 밖 블록·stage·극점 노드 변화는 기록(Vg10 극점 노드 drive voltage → current 밖이면 실패) |
| `l_owner` 사실(§1.12.5, C-3) | (a) toy 동치류 + 사실 | `tests/graph/test_l_classes.py` | 사실이 있으면 1~4 규칙과 무관하게 사실의 주인, 멤버가 아니면 `structure_fact_mismatch` |
| P-1 정지(§5.3.11 (a)(b)) | (a) 경로 열거 수가 예산 상한을 넘는 toy, Π > N_S toy(N_S 선언값 작게) | `tests/search/test_layer0_budget.py` | 둘 다 `unsupported_rule_branch`로 탐색 전 정지(결정론: 시간 설정을 바꿔도 같은 판정). 좌표 훑기 코드 경로 없음(구조 test) |
| P-1 절단(§5.3.11) | (a) N_S ≥ Π > N_T,i toy(N_T 선언 E_B 작게) | `tests/search/test_layer0_budget.py` | 정지하지 않고 반분 단계 순으로 N_T,i개 평가 후 `layer0_candidates_truncated{block, bin, Π, evaluated}` 기록, 그 블록 front·조합 front '추정' |
| §6.7 KVL 행 | (a) 이름 없는 toy: v2 고리(종속 소자 VGS 구간 밖·안), VDS-1 고리(포화 위반·만족), 1변수 노드 근 없음 | `tests/search/test_iv_kvl.py` | `loop_lo`·`loop_hi`·`saturation`·`writer_root` 행 값과 부호, 의존 묶음, 비활성 사유(`rail_potentials_undeclared`, `kvl_node_undetermined`) |
| §6.7 공동 선택 | (a) 위반 toy, 위반 없는 library 회로 | `tests/search/test_iv_kvl_choice.py` | 7a (i) 위반 최소 → (ii) max-min → (iii) 위치 합. 올린 묶음이 있으면 매크로·면적 재확인과 반씩 좁힘(상한 steps + 1). 해 없으면 `StartConflict(kvl)` + 위반 최소 조합(fail-closed). 위반 없는 회로의 출발 θ가 v1.5와 비트 동일. **v1.15.1(toy 10 (c)(d))**: P1s·P1c toy에서 R6 선택이 `mirror_vds` 위반을 줄임(깨진 R-1′ 행 위반이 먼저), 해 없음 → `StartConflict(mirror_vds)`, 바이어스 분배 쌍·S 좌표·외층 무동작, 부하 둘 이상 toy에서 합 행이 동시 상한 선택을 막음 |
| §6.7-1a 쓰기 계획(card IT-1, §4.7-1) | (a) 입력 DC 미선언 차동 입력 toy, 입력 DC 선언 toy, 두 입력 포트가 서로 다른 G_vgs 성분인 toy -- 기대 writer·종속 분류는 toy 연결에서 손으로 유도(손계산 오라클) | `tests/sizing/test_writer_plan.py` 안 새 test 함수(v1.12: 옛 경로 `test_writer_plan_no_input_tie.py`는 구조 규칙 H 위반이라 바꿈 -- 계획 F-IT4·X-IT3, 함수 이름은 test 주체가 `git grep`으로 겹침 확인) | **red 먼저**(검증자가 격리 복제본 base에서 실패 기록): relation `input_tie` 0, 같은 DC 엣지로 생긴 종속 0 + 종속 수 = 같은 DC 엣지 없는 G_vgs 순환 수(포트 경로가 둘 이상인 v1 고리의 ΔV 소거 `cycle_vgs`는 기대값에 포함), 입력 포트 W4 뿌리 y 키 = 뿌리 넷, 선언 toy 쓰기 계획 = 오라클(base에서도 green), 다중 입력 뿌리 toy = `unsupported_rule_branch`·`input_port_multiple_roots`(base는 정지하지 않음 -- red) -- **v1.15.2 대체**: 두 포트가 다른 성분인 차동 toy = 정지 없이 입력 점 한 점, 정의 불능 셋 = `input_cm_undefined`(§9 v1.15.2 IT-1 행·4.7-V) |
| §4.7 입력 포트 창(card IT-2, v1.13.0) | (a) 커널 θ 프레임 뿌리 창 손계산(θ 선형 감도), 측정 구성 판정 창 손조립 KCL 끝(L8 (a) -- follower·θ 손계산 끝과 다름을 전제 단언; v1.14.0 servo, V_cm 손계산 L8 (g), B77 L13), δV_out 정확 산술 참값(L8 (e)), E 손계산(L10 (k)) | `tests/sizing/test_block_columns.py`·`test_input_window.py`(커널 창·`saturation_window` 새 서명), `tests/sizing/test__helpers_dc_solve.py`(`Circuit` 행 부분), `tests/metrics/test_ss_nodal.py`·`test_icm_config.py`(측정 구성·E), `tests/metrics/test_stamp_mos.py`·`test_stamp_two_terminal.py`(`g_ops`), `tests/metrics/test_icm_window.py`(metric), `tests/metrics/test_ls_swing.py`(입력 칸 삭제 반영) | §4.7-7 K1~K4·R2·M1~M3·W1·P·D·L8·L10~L12. IT-2b가 `test_input_window.py`(IT-2b 반영 `6afe4758` `:396`)에서 '선언 입력 DC 포트의 커널 `node.dc_window` 항목 있음(measured)'으로 바꾼 기대는 D1로 다시 '커널 항목 없음'으로 바뀌고(test 작성 주체 몫), '창 있음'은 측정 구성 판정 창에서 단언한다(계획 v6.34 완료 조건 (1)). 다듬은 창·front 전용 test(`test_window_refine.py`·`test_icm_front.py`) 없음 |
| P-15 섞인 회로 버퍼(§5.1) | (a) 이름 없는 CS + follower toy(rout 선언·미선언) | `tests/search/test_layer0_budget.py` | 버퍼가 면적 bin DP 단계로 들어가고 국소 Z_out ≤ rout인 점만 남음. 미선언이면 그 블록만 무동작 기록, 상수항 사용 |
| 층 0 정의역 상한 A^L0(§4.2) | (a) 축소 축 2~3개 toy 전수 손계산 | `tests/graph/test_structure_tables.py`(S0 표에 `block_bounds_l0` 행·'추정' 표시·축 목록이 실림), `tests/metrics/test_block_bounds_l0.py` | 고정 축 값 = `start.row`·`start.point` 격자 마디, 단계 B 값을 읽지 않음, matching 그룹 축 하나, Π > N_S면 미상, exit 3이 이 값을 읽지 않음 |
| 계수 예산 결정론 | (a) 같은 S0 두 번 | `tests/search/test_count_budget.py` | N_S가 시간과 무관하다. 사이클·Π 결과가 실행 간 같다 |
| 비단조 축 처리 | (a) 비율에 대해 내부 최대가 있는 toy | `test_block_gain_bound.py` | 세분 후 인증, 실패 시 미상 |
| 잡음 LUT | (c) 단일 소자 ngspice `.noise` 칸 중앙 대조 | `tests/lut/test_noise_query.py` | 칸 중앙 오차 ≤ tol_noise |
| 잡음 해석 | (a) 저항 분압·CS 한 단 손계산(4kTR, 4kTγgm), (c) ngspice `.noise` | `tests/metrics/test_noise_analysis.py` | 입력 환산 밀도·적분이 resolution 안. `sampling_caps` 미선언(파일럿, C-2)이면 스위치 항 0 |
| 잡음 출발 구간 | (a) 손계산 | `tests/search/test_start_intervals.py` | 열잡음 gm 하한, 1/f L 하한 |
| mismatch 감도 LUT | (c) 단일 소자 ngspice 섭동(칸 중앙), (c) 소자 쌍 Monte Carlo | `tests/lut/test_mismatch_query.py` | 칸 중앙 오차 ≤ tol_mismatch. `vth0` 성분 = √2·slope 유도값(bin별 slope1 포함). MC σ와 A_eff 식이 MC 표본 분해능 안 |
| 면적 조건 gm/ID 하한·offset 가드(toy 10 (d)(e)) | (a) 손계산 | `tests/search/test_start_intervals.py` | 절대 offset 회로에서만 입력 소자 gm/ID 하한 활성(L 하한 없음 -- 같은 면적을 L 또는 gm/ID로 얻는 toy에서 L 하한 0, base는 L 하한 -- red), 가드 회로·절대 offset·잡음 회로는 부하 gm/ID 상한(합 행 포함, W_min 클램프 점 제외) |
| 헤드룸 달성가능성 | (a) 이름 없는 follower 스택·두 극성 입력 toy 손계산, (b) 소형 toy 격자 직접 전수 | `tests/metrics/test_headroom_bound.py` | 상한 ≥ 격자 직접 전수 최대 폭. 선언 제약이 인증 불가면 exit 3, 제약 없는 창은 보고만. 최단 L bin에서만 열리는 toy → `icmr_window_short_l_bin` 경고(정지 아님). SP-2 (c) 회로는 y_icm 범위 = 창 |
| 복합 diode(§1.12.1) | (a) 이름 없는 toy: 저항 자기바이어스 캐스코드 기준(MOS 2 + R), 레플리카(MOS 2, 전류원 고정), 단순 diode(무동작), 직렬 노드에 세 번째 전류 단자가 붙은 변형(무동작). (d) 9회로 | `tests/graph/test_composite_diode.py` | 발동 집합·기준/캐스코드 구분. 9회로 발동 = §1.13 실측 집합, 나머지 7회로 0. 같은 gs 묶음 나머지가 바이어스 전류원. 미러 입력 넷 확장. 묶음 내부 사이클은 `composite_diode_internal`, 루프 뷰 0. 이름 전단사 불변 |
| feedforward(§1.12.2) | (a) 이름 없는 3단 toy + 1단 우회 CS + 2단 우회 미러 가지, 우회 없는 병렬 합류 toy(무동작), 블록 내부 노드로 들어오는 바이어스 셀 toy(K8, 무동작). (b) 분해 합성값 A_decomp와 전회로 MNA 비교 | `tests/graph/test_feedforward_cells.py`, `tests/metrics/test_block_model.py` | FF 묶음·탭·merge·B_b. 주경로 블록 사슬. 복합 블록 0. A_decomp 잔차 ≤ 수치 분해능. `ff_ratio_candidates` 보고 |
| 보상 내부 루프(§1.12.3) | (a) 이름 없는 중첩 Miller 3단 toy(`pm_ss_deg` 선언 있음/없음), 순방향 밖 셀이 낀 되먹임 toy | `tests/graph/test_loop_roles.py` | 선언 있으면 루프 뷰 0. 없으면 `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`). 순방향 밖 셀 루프는 루프 뷰 유지 |
| 루프 극성·L 주인(§1.12.4·5) | (a) DC 사이클 + Cc 사이클 toy, 부호가 다른 DC 사이클 두 개 toy. 주경로 셀과 FF 셀이 같은 L 동치류인 toy | `tests/graph/test_loop_classify.py`, `tests/graph/test_l_classes.py` | 뷰 극성 = DC 사이클 극성. Cc 사이클 `ac_only`. 충돌이면 `loop_polarity_conflict`. 주인 = 주경로 stage 시작 셀(`main_path_signal`). name_order면 review |
| structure 사실 소비(40 §3.2-3) | (a) 사실 픽스처: confirm 일치/불일치/고아, override, stale(rule_hash 다름), 알 수 없는 concept | `tests/graph/test_structure_load.py`, `tests/pipeline/test_stage_a.py` | 일치 → ratified, 불일치 → `structure_fact_mismatch`, 고아 → `structure_fact_orphan`, stale → `structure_fact_stale`, 알 수 없는 concept → `SchemaRejectedError`(**거부 확인**). 단계 A가 spec 루프 선언의 끊는 넷을 `declared_loop_cuts`로 넘긴다(넘기지 않으면 실패하는 red test 먼저) |
| **v1.15.2 toy 자리**(gap §1.2·§4 -- 계획 완료 조건이 정본, 이 행들은 test 파일 자리만; 이름은 test 주체가 `git grep`으로 겹침 확인, 기대값은 손계산 -- 피검 함수로 만들지 않음) | -- | -- | -- |
| WB-1 (1) 손가락·bin(40 §3.7-A 5) | (a) 손계산: W ≤ w_hi → m = 1, W > w_hi → ⌈W/w_hi⌉, 슬라이스 없는 bin → m 증가, 첫 bin 두 슬라이스 → 가까운 쪽, w_f < W_min → `finger_below_min`, 덮개 없음 → `slice_missing`, W_min 왕복 반올림 점의 bin(D1), 경계 w_f·L | `tests/lut/test_finger_slice.py`, `tests/lut/test_helpers_bins.py` | base(kind당 기준 폭·1 ulp 비교) red, 넷리스트 `w`·`m`·`l` = 필드 격자 값 |
| WB-1 (1) DC 블록(40 §3.7-A 2) | (a) 계획 완료 조건 (1) 그대로 -- 종속 소자 슬라이스 되먹임 toy(입력 포트 W4 뿌리 꼴·writer 없는 SCC 허용오차 꼴 각 하나), 인위 순환 toy, 같은 θ 재평가 비트 동일·다른 계보 같은 점; toy 목록 정정은 **계획 v6.38.4 대기(P3)**(후보 = §5.12.7 정정 후보 (b)(c)) | `tests/sizing/test_block_dc.py` | 키 벡터 전체 재방문 수렴, 순환 → `slice_cycle`, 수렴 회차의 W·`w_key`·`dc_finger` 같은 슬라이스, `slice_rounds` = (회차, 노드 풀이) |
| WB-1 범위 3a(E-13 -- 40 §3.11-1) | (a) y 범위 = 순서 창 toy(뿌리 넷 전도 MOS의 채널 전도 방향 전압(nmos V_DS, pmos V_SD) ≥ 0 구간 손계산), `perf.solver_stops` 칸 toy(3a-0 -- 동작 불변) | `tests/sizing/test_block_columns.py`(3a는 DC 블록 앞 커밋), `tests/search/test_find_front.py` | `input_status`·`k_max` 되풀이 grep 0, 종료 사유 분류(정상·비정상·예산) |
| IT-1 범위 재작성(DEC-106 -- 40 §3.11-4, 41 §4.7-V) | (a) 계획 IT-1 v6.38.3 완료 조건 1 (a)~(f) 손계산(같은 y·`parallel_vgs`·순환수, 다른 성분 두 포트 한 점, F 닿음 → KVL 종속, 선언·단일 입력 무동작, 정의 불능 셋, 대칭 DOF·rank) | `tests/sizing/test_writer_plan.py` | base(포트별 뿌리·`input_port_multiple_roots`) red, `input_cm_undefined` |
| IT-1 범위 재작성 5(g = s -- 40 §3.11-5) | (a) 레일·비레일 g = s toy 같은 처리, 신호 경로 g = s toy 정지, `bias_fixed_net` 술어 toy(바이어스 분배 넷·되먹임 경로 넷) | `tests/graph/test_gvgs_cycles.py`, `tests/graph/test_s1v_predicates.py`, `tests/graph/test_s1v_fields.py` | `off_vgs0` 분류 한 자리, `off_device_on_signal_path`, 판정식 정의 자리 하나 |
| LA-1 9 (d) 회차·외층 표지(§5.3.2·§5.9) | (a) 표지가 선 칸이 다음 회차 미해결 칸으로 다시 풀림(S3 graft 옛 결과 없음)·종료(front 같음 ∧ 표지 미해결 0) 또는 K_max; 외층 봉인 스냅샷 표지 기록만·층 0 재개방 없음; 탐색 개방 후보 L 역산 없음(§5.3.5 H-6) | `tests/search/test_layer0_rounds.py`, `tests/search/test_slsqp_outer.py`, `tests/search/test_layer0_inverse.py` | 회차 수·재개방 여부 손계산과 같음 |
| LA-1 10 (b)·(g) 매크로 세 층(§6.5-3a·4, 40 §3.11-2) | (a) 근 없는 toy → `macro_rung_undefined`·다음 칸, 모든 칸 불능 → `macro_start_unavailable`, PM 미달 toy → 정의된 값 출발 + `macro_target`, 모든 칸 P ≠ 0 → 끝 칸 값, 혼합 원인 toy, MNA 특이 toy | `tests/search/test_macro_poles.py`, `tests/search/test_start_intervals.py` | 상자 중심·출발점 그대로 0(base red) |
| LA-1 10 (c) 술어·R6(§6.7-4·-11) | (a) diode·미러·캐스코드 미러 인스턴스 발동/비발동, 바이어스 분배 쌍 비발동, P1s·P1c R6 선택, 해 없음 StartConflict, 층 0 변수 섞인 고리 → 후보마다; (d) 9회로 발동 표(test 작성 주체 독립 재측정) | `tests/graph/test_offset_instances.py`, `tests/search/test_loop_dependents.py` | 깨진 R-1′ 행 위반이 먼저, S 좌표·외층 무동작 |
| LA-1 10 (d) 가드 합 행(§6.4-2a) | (a) 부하 둘 이상 toy에서 합 행이 동시 상한 선택을 막음; 변화표 행 = card LA-1 변화표 '가드 정정'(합 행 발동 회로·W 클램프 제외 수) | `tests/search/test_start_intervals.py` | O-34 동작 변경 기록 |
| LA-1 10 (f) CM 평형·기준(40 §5-6) | (a) 저항 감지 + 오차 쌍 toy(θ 전류 축 −1), 단일 출력 무동작, CM 기준 toy 넷(외부 미선언 → `cm_reference_undeclared`, 외부 선언 → F, 내부 생성 → KVL writer, 외부 + 출력 CM 둘 다 → `cm_reference_double_declared`), R1·R2 묶음 기록 | `tests/sizing/test_current_basis.py`, `tests/sizing/test_writer_plan.py` | `cm_reference_undetermined` grep 0 |
| RS-1 (1)~(3)(40 §3.8-9) | (a) 단일 소자 Δgm = LUT 기울기 × tol_V 닫힌 식, 약반전 점 새 Δp < 옛 Δp; (2) 9회로 분해능 표·판정 분류 변화표, (3) 최악 선형 대 RSS 기록 = card RS-1 판정 기록 | `tests/metrics/test_lut_parameters.py` | 열마다 Δp, 결합 최악 선형 |
| SF-1 범위 8~11(40 §3.1-1) | (a) `counted_rails` 거부 셋·보류 정지, `is_judged` 두 축·`unjudged`, DUT 전력 toy(계획 P7 결정 뒤 그 후보의 toy -- 후보별 기대 = 40 §3.1-1 (iv), **계획 v6.38.4 대기(P7)**), 선언 미러 비 toy 넷, 칸 삭제 선언 거부, θ 상자 (a)~(d) toy·`zero_cancel_box` 손계산 구간 | `tests/authoring/test_spec_judged.py`, `tests/authoring/test_spec_settings.py`, `tests/metrics/test_supply.py`, `tests/sizing/test_current_basis.py`, `tests/sizing/test_theta_schema.py` | base red 항목은 계획 SF-1 완료 조건 그대로 |
| SB-1 (4) 거짓 거부(§6.8-1) | (c) 하한이 이긴 사건 전수의 하한 전 점 oracle 판정 = card SB-1 판정 기록 | -- (판정 기록) | 거짓 거부 0 |
| LA-1 10 (g) 나머지(N6.35 E-07·E-14·E-15·E-24~E-26·E-34·E-35 -- gap D13) | (a) 미지수 2 KCL 행 toy → `kcl_row_underdetermined`(base 무기록 red), `tol_vdsat_max` 열 없는 toy → `tol_vdsat_table_missing`(base 0.0 red), 영점 R 두 갈래 손계산 toy(θ 성분 → 매크로 풀이 값, 비θ + 셀 전류 미정 → `zc_start_undefined`·망 유지); grep 0 = `T_refilter`·`E_refilter: 0`·`reserve_evals = 0`·`_e_total` N_T 0·'card C'·`compensation_fixed_fallback`·`constraint_rows` `_undefined` | `tests/search/test_iv_currents.py`, `tests/lut/test_derived_fns.py`, `tests/search/test_macro_poles.py`, grep = card LA-1 판정 기록 | 계획 N6.35 행 '완료 toy' 그대로 |
| WB-1 (1) E-18(gap D15) | (a) CDD 열 없는 toy → `lut_column_unavailable`(base cgd 대체 -- red) | `tests/search/test_iv_currents.py`, `tests/search/test_macro_poles.py` | cgd 대체 grep 0 |
| UB-1 범위 4(E-01·E-16 -- gap D29) | (a) 섭동 하나라도 None → `undeterminable`(base `ok` red), 영향 집합 빈 toy → `gate_empty` 기록, bin 안쪽 극값 toy → 세분 값 또는 미상(base 끝점 '인증' red) | `tests/metrics/test_sensitivity_gate.py`, `tests/search/test_gate_run.py`, `tests/metrics/test_block_gain_bound.py` | 판정 불능이면 분해 metric 미사용 |
| GV-1 범위 3·4(E-10·E-33 -- gap D29) | (a) 뷰마다 출발점이 다른 toy → `l_owner_view_ambiguous` 또는 전달 뷰 규칙 값(base 첫 뷰 red), CM 루프 + `pm_cm_ss_deg` 미선언 toy → `undeclared_loop_constraint` 정지(base 경고만 red) | `tests/graph/test_l_classes.py`, `tests/graph/test_s1v_fields.py` | `cm_loop_unconstrained` grep 0 |
| SF-1 범위 9 E-12(gap D29) | (a) 값 미정 수동소자 toy → 면적 정의 불능 `area_undefined`(base 면적 과소 red) | `tests/metrics/test_dc_metrics.py` | head 면적 0.0 대체 grep 0 |

**DoD 명령**(`$PY` = `C:\Python314\python.exe`):

```
$PY -m pytest skills/analog-gmid-design/gmid_engine/tests -q   # slow 포함 판정은 --run-slow
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
| §4.7 입력 포트 창(IT-1·IT-2, v1.13.0) | 3 | 0 | 1(4.7-1 쓰기 계획: 같은 DC 엣지를 커널이 푼다) | 1(4.7-3 커널 창: `input_window`·`_solve_input_window` as-built -- IT-2b 뒤 뿌리 아닌 포트 항목·출력 구조 분류가 있음, IT-2c가 지움) | 1(4.7-3b 측정 구성 블록·`ss_nodal`·E 칸, 4.7-4 `Circuit` 이동, 4.7-5 metric 읽기 -- 다듬은 창 블록 없음) |
| §5 층 0 | 9 | 0 | 0 | 0 | 9 |
| §6 출발 구간(v1.15.0: +6.7-11 R6 블록, +6.8 공급 요구 하한·정착 출발 목표; v1.15.1: +6.4-1 found_db 목표·fail-closed, +6.5-3a P = 0, +6.7-4 `mirror_vds`·합 행, +6.4-2 면적 gm/ID 하한) | 12 | 0 | 0 | 0 | 12 |
| §7 잡음 | 6 | 0 | 0 | 0 | 6 |
