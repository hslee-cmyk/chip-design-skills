---
template: design
version: 1.0
plan_version: 6.0
---

# gain-budget-gmid-sizing -- 41-gain-budget Design Document

> **Summary**: gain-budget-first 흐름을 설계한다(계획 N1.1, FR-1·FR-2·FR-4·FR-8, DEC-03·05·43·57·59·63·65·71·73·77·81). 다루는 내용은 다음과 같다.
> - connectivity에서 signal stage를 유도한다(SP1).
> - 블록 국소 소신호 모델로 stage gain을 정의하고, 매 평가 전회로 MNA gain과의 잔차를 기록한다.
> - 탐색 전에 LUT 상한으로 달성 가능성을 판정한다.
> - 층 0에서 블록별 gain bin마다 (전력, 면적) 비지배 점을 만들고, 조합 DP로 예산 조합 front와 `gain_budget_db`를 낸다.
> - 외층 SLSQP와 이어 붙인다.
> - 스펙에서 gm/ID·L·전류 출발 구간을 topology 무관하게 유도한다.
>
> **Date**: 2026-10-08 · **Status**: v1.0 초안 · 색인과 공통 표기는 [40-engine](gain-budget-gmid-sizing.40-engine.design.md)을 따른다(`E/`, 상태 어휘 OK/DEV/PART/MISS).

**as-built 요약**: 이 문서가 설계하는 항목은 거의 모두 MISS다.

| 있는 것 | 위치 |
|---|---|
| gain 상한 계산의 재료: LUT 곡선 표의 격자 최대 gm/gds | `CurveRow.gm_gds_max`, `E/lut/lut_types.py:384,396` |
| 전회로 MNA gain | `E/metrics/` |
| 외층 ε-제약 front | `E/search/` |
| 시작점 하나를 만드는 최소형 층 0 | `E/search/layer0_center.py` |

---

## 1. FR-1 -- signal stage 유도 SP1 (GB2, MOD3)

**목적**: connectivity만으로 여기 뷰마다 셀·구동 종류·stage·블록·극점 노드·루프를 유도한다. declared stage와 다르면 `review_needed`로 둔다(DEC-43·44). 규칙의 정본은 P N3.2의 1~9와 용어집('셀', '입력 노드 구동 종류', '블록 종류', '극점 노드 목록')이다. 이 절은 그 규칙을 **실행 순서와 알고리즘 선택**으로 고정한다(WP-21 코드 부류).

**출력**: S1v 필드 `views[]`. 각 뷰는 `{kind, excite, sense, ac_ground, signal_nets, forward_nets, cells{dev: CS|CG|CD|pass|diode_load|off}, drive_kind{net: voltage|current|value_dependent}, dist{net}, blocks[], pole_nodes[], loops[], cuts[]}`이다. 그 밖에 `rule_branch_coverage`, `review_needed[]`를 낸다.

**파일**(MOD3 `graph`, 한 파일에 한 계산 블록):

| 파일 | 내용 | 절 |
|---|---|---|
| `views.py` | 뷰 수집 | 1.1 |
| `ac_ground_view.py` | 뷰별 교류접지 | 1.2 |
| `signal_reach.py` | 도달성과 순방향 집합 | 1.3 |
| `cells.py` | 셀 분류 | 1.4 |
| `drive_kind.py` | 구동 종류 | 1.5 |
| `stage_bfs.py` | 0-1 BFS와 stage 번호 | 1.6 |
| `blocks.py`, `pole_nodes.py` | 블록 구성, 극점 노드 | 1.7 |
| `loops.py`, `loop_classify.py`, `loop_cuts.py`, `polarity.py` | 루프 | 1.8 |
| `buffer_bundles.py`, `output_direction.py`, `composite_blocks.py` | 버퍼 묶음, 출력 방향, 복합 블록 | 1.9 |
| `declared_compare.py`, `rule_coverage.py` | declared 대조, 규칙 분기 발동표 | 1.10 |
| `s1v_build.py` | 진입점 | -- |

### 1.1 뷰 수집 (P N3.2-2)

- **전달 뷰**: 선언된 metric의 `(ac_excite, sense)`마다 하나를 만든다.
- **기본 전달 뷰**: 선언이 없으면 `ports` role로 정한다. 두 입력 포트가 자기동형 궤도(40 §6)에서 서로 대응하면 기모드 여기 하나, 그렇지 않으면 입력마다 단일 여기를 둔다.
- **루프 뷰**: 1.8에서 (3)으로 분류된 루프마다 하나를 만든다.
- **전류 입력·트랜스임피던스 뷰**: `기록만` 분기이므로 DEC-59에 따라 정지한다.

as-built `E/authoring/spec_views.py:61,110`(`default_views`)는 metric 판정용 뷰다. S1v 뷰는 그것과 같은 `(excite, sense)` 키를 공유하고, 구조 정보를 따로 더한다.

### 1.2 뷰별 교류접지 (P N3.2-1)

**정적 집합**: as-built (1) 레일과 (2) gate 전용 넷이다(`E/graph/ac_ground_static.py`).

**(4) 바이어스 종속 넷 술어**: 넷 b가 다음을 모두 만족하면 그 뷰의 교류접지다.
- (0) b가 그 뷰에서 신호 넷이다.
- (i) b에서 신호가 gate로만 나간다.
- (ii) b를 구동하는 채널 단자가 모두 'b를 gate로 읽는 소자' 또는 '신호 경로 밖 gate 소자'의 것이다.
- (iii) 앞의 부류 소자 중 하나가 신호 노드 s에서 출발하는 사슬에 속하고, s는 b를 뺀 그래프에서도 신호 넷이다. 사슬은 source에서 drain 방향으로만 따라가며, 교류접지를 지나지 않고 b를 다시 지나지 않는다.
- 그 뷰의 여기가 s를 움직이지 않는다. 움직이는 뷰에서는 그 사슬의 폐경로를 루프 (3)으로 등록한다.

**구현**:
- 사슬은 b를 제거한 신호 그래프의 역방향 BFS로 찾는다. 뷰마다 한 번 계산하고 필드 캐시에 둔다.
- 이상 전압원 (3)은 현재 `source_kind_unsupported`로 정지한다. 발동 0이므로 DEC-76을 따른다.

**실측 기대**: 파일럿 2건, 나머지 8회로는 무동작이다(J1 확정).

### 1.3 신호 도달성과 순방향 집합 (P N3.2-3)

**최소 고정점**: 여기 포트 넷에서 시작해 아래 세 규칙을 더 늘지 않을 때까지 반복한다. 교류접지와 제거 넷은 넣지 않는다.
- (a) gate가 신호 넷인 소자의 drain·source 넷을 더한다.
- (b) source가 신호 넷인 소자의 drain 넷을 더한다.
- (c) 2단자 수동소자의 반대쪽 넷을 더한다.

**순방향 집합 F** = 이 그래프에서 여기 포트로부터 도달하고, 출력 포트로 역도달하는 넷이다. 셀 분류 전에 계산하므로 순환이 없다.

### 1.4 셀 분류 (P N3.2-3)

뷰마다 모든 MOS에 적용한다. 앞 규칙이 이기면 뒤 규칙은 보지 않는다.
1. gate = drain이면 `diode_load`다(셀이 아니고 그 노드의 1/gm 부하).
2. gate가 신호 넷인 경우:
   - drain이 교류접지면 CD, source가 교류접지면 CS다.
   - 둘 다 아니면, source가 순방향 위의 다른 신호 셀 입력 단자나 출력 포트에 닿는지 본다. 닿으면 `review_needed`(이중 출력), 닿지 않으면 CS(degeneration)다.
   - 상대 셀도 모호하면 그 쌍을 함께 `review_needed`로 둔다.
3. gate가 신호 경로 밖인 경우:
   - 역병렬 pass 묶음 조건(같은 두 노드, 반대 방향, 둘 다 gate가 신호 경로 밖)이면 pass다.
   - 그렇지 않고 source가 신호 넷이면 CG다.
   - 둘 다 아니면 `off`(그 뷰에서 신호를 싣지 않음)다.
   - 셋 이상이거나 방향이 섞인 묶음은 `review_needed`다.

**집계 규칙**: 대조표 셀 수는 출력 단자가 F에 드는 셀만 센다. 빠진 셀은 '순방향 밖 셀' 열에 이름으로 남긴다(DEC-59).

### 1.5 입력 노드 구동 종류 (용어집)

노드마다 신호 진입 단자와 진출 단자를 모아 판정한다.
1. 진입이 drain이면 전류, 진입이 source·입력 포트·앞 stage 출력이면 전압이다.
2. 진입이 저항만이면 반대쪽 노드에서 상속하고 '값 의존'을 붙인다. 상속이 순환하면 `review_needed`다.
3. 전류 진입과 '다음으로 넘김'이 겹치면 진출 단자로 가른다.
   - gate로만 나가면 전압이다.
   - 채널로만 나가면 전류다.
   - 둘 다면 gate 쪽 셀 출력이 F 위에 있을 때 전압이고, 아니면 tap(규칙 9 (a))이다.
4. 혼재(source 진입 + 다른 소자 drain)는 drain 쪽 소자의 DC 역할로 가른다.
   - 바이어스 전류원이면 전압(주입)이다.
   - 신호 소자면 `review_needed`다.
   - 구조로 못 가르는 그룹이면 그 그룹의 J를 기다린다.
5. pass 묶음을 지나 들어오면 반대편 노드의 구동 종류를 상속한다.

이 판정은 블록·stage를 입력으로 쓰지 않는다.

### 1.6 0-1 BFS와 stage 경계 (P N3.2-4, -5)

**엣지 비용**:
- gate→drain은 1이다. 단 gate가 diode 단자인 소자(미러)는 0이다.
- source→drain과 gate→source는 0이다. 단 source가 전압 구동인 CG는 1이다.
- 수동소자 엣지는 0이다. 이것이 6a 열린 항목 ⑬의 해법이다. 근거: 수동소자는 이득단을 열지 않고, (3-b) '앞/뒤'는 아래 블록 순서로 판정한다.

**stage 시작 셀**은 CS, 또는 source가 전압 구동인 CG이면서 입력 노드가 전압 구동인 것이다. 단 DC 역할이 바이어스 전류원인 셀은 stage를 시작하지 않는다(측면 주입 K8). 캐스코드(전류 구동 CG)는 같은 stage를 잇는다. CD는 버퍼 구간이다.

**적용 순서**(열린 항목 ⑧): 규칙 9 (c)의 diode 미러 갈래를 stage 시작보다 먼저 적용한다. 신호가 drain으로 들어오는 diode 노드를 gate로 읽는 소자의 출력이 F 위에 있으면, 그 diode 노드는 미러 입력이고 블록 내부 노드다. 그 노드를 gate로 읽는 셀은 stage를 시작하지 않는다. 근거: P N3.2-5 문헌 대조('diode 미러를 같은 단에 둔다')와 J2 기본안.

### 1.7 블록 구성·출력노드·임피던스 등급·극점 노드 (P N3.2-6, N3.7 입력 기준)

1. stage 시작 셀마다 블록 하나를 연다.
2. 그 셀의 출력 단자에서 캐스코드 사슬, 미러 연장(1.6), pass 묶음을 따라가며 노드를 더한다. 다음 stage 시작 셀의 입력 단자나 출력 포트에서 멈춘 노드가 출력노드다.
3. 병렬 합류는 판정 순서 ①②③(P N3.7)을 따른다.
   - ① 입력 기준(같은 입력, pass, 캐스코드, 미러 합류)이면 한 블록이다.
   - ② ①이 아니면 DEC-81 복합 블록 후보다(1.9).
   - ③ 둘 다 아니면 다입력 블록이며 `기록만` 정지다.
   - 3개 이상이 합류하면(열린 항목 ⑪) 입력 쌍마다 ①을 적용하고 union-find로 묶는다.
4. 대칭 반쪽이 공유하는 넷(차동쌍 공통 소스 등, 열린 항목 ⑩): 같은 stage 번호의 두 반쪽 블록이 넷을 공유하면 **차동 블록 하나**로 합친다. 블록 노드 배타성은 합친 뒤에 검사한다. 축약 뷰에서는 반쪽 블록 하나다.
5. 출력노드 임피던스 등급:
   - 낮음 = gate가 교류접지인 source 단자, 또는 diode가 붙은 노드다.
   - 높음 = drain·gate·커패시터 단자뿐인 노드다.
   - 값 의존 = 낮음 단자 없이 저항이 붙은 노드다.
   - 규칙 9 (c)(이득 블록 출력이 낮음)는 블록 구성 뒤에, 출력노드가 F 위일 때만 판정한다.
6. 블록 속성: 종류(이득·버퍼·복합), input, cascode, load, tail, 노드 집합, 출력노드, stage 번호, 블록 키(출력노드 넷 이름).
7. 극점 노드 목록 = 그 뷰에서 교류접지가 아닌 모든 노드다. 속성은 소속 블록, 등급, 종류다.
8. 규칙 9 (a)(b)(c)는 `기록만`이며 DEC-59 정지다.

**DEC-59 정지를 세는 뷰**(열린 항목 ⑨): 비축약 뷰다. 축약은 계산 수단일 뿐이고, 축약과 비축약의 stage·셀이 같은지를 검사한다(규칙 8 (ii)).

### 1.8 루프 (P N3.2-2, -7)

**탐지**:
- 그래프: 교류접지와 여기 포트를 제거한 방향 그래프다. 엣지는 gate→drain, gate→source, '전류 진입이 있는 source'의 source→drain, 수동소자 엣지다.
- 열거: 단순 사이클 전수를 Johnson 알고리즘으로 구한다(정렬된 노드 순서).
- 제외: 2단자 수동소자 왕복, pass 묶음 내부 왕복, 자기 엣지는 사이클로 세지 않는다.

**분류**: 아래 순서로 처음 맞는 것을 쓴다.
1. (1.5) 바이어스 SCC: 전달 뷰의 순방향 노드를 하나도 지나지 않는다.
2. (2) Miller: 커패시터를 포함한 '수동소자만의 극대 구간'이 순방향 위 두 노드를 잇는다. (3-b)도 만족하면 두 분류를 함께 단다.
3. (3-a) 순방향 밖 능동 셀이 있다. 발동 0이므로 `review_needed`다.
4. (3-b) 복귀 경로에 능동 셀이 있고, 블록 순서상 뒤에서 앞 블록 입력으로 돌아온다. 복귀 경로 = 거리가 늘지 않는 엣지(동률 포함)로 이루어진 극대 연속 구간이다. 배타 조건이 둘 있다.
   - (가) 복귀 경로가 수동소자만이면 (4)다.
   - (나) 복귀 경로가 능동 셀 둘로만 닫히면 `기록만`이다. 사유: '수동소자 없는 2능동셀 루프'.
5. (4) 그 밖은 `기록만` 정지다.

**끊는 점**: 루프 위에 gate 엣지가 있는 CS 셀의 gate다. 후보가 여럿이면 복귀 경로 다음의 첫 gate로 하고, 복귀 구간이 둘 이상이면 노드 이름 정렬 첫 노드에서 시작하는 사이클 표현의 가장 이른 구간을 쓴다(NFR-4). 후보가 없으면 `review_needed`다.

**극성**: 셀 부호의 곱이다. CS는 −, CG·CD·pass·R은 +다. 커패시터만 지나 저주파 경로가 없으면 `review_needed`다.

**U-24 게이트**: 루프 뷰가 있는데 그 루프의 안정도 제약이 선언되지 않았으면 GB2 출구에서 `StructureUnresolvedError(undeclared_loop_constraint)`로 정지한다. CM 루프(40 §5)는 '차동 포트쌍이 있으면 T_cm 보고, 제약은 spec 선언 회로만'이라는 사용자 결정을 따르므로 이 게이트에서 뺀다. 이 예외는 사용자 결정이 근거다.

### 1.9 버퍼 묶음·출력 방향·복합 블록 (DEC-63·65·81)

- **R(u)**: 전압 구동 넷 u에서 CD 입력→출력 엣지만 따라가며 노드를 모은다. 합류 노드가 하나면 버퍼 블록이고, 둘 이상이면 `기록만`이다. CD 병렬 합류(열린 항목 ②)는 R(u)를 1.7의 ①보다 먼저 판정한다.
- **출력 방향**(구조): 출력 포트 노드에서 방향마다 공급 셀의 DC 역할을 본다(β·σ·κ). 두 방향 모두 σ면 push-pull, 한 방향만 σ면 class-A다. 값은 40 §3.8 `ls`가 낸다.
- **복합 블록**: 1.7의 ②에서 합류 노드가 '전류 구동이거나 블록 출력노드'인 병렬 경로 블록을 하나로 묶는다. 묶은 DAG가 사슬이어야 한다. 경로별 기여(부호 포함)는 41 §2가 계산한다. 묶음 크기 Π(셀 격자 수)가 예산 식(DEC-34)을 넘으면 `unsupported_rule_branch`다. 묶음 판정(구조)은 MOD3, 기여 계산은 MOD5에 둔다(열린 항목 ⑭).

### 1.10 declared 대조·규칙 분기 발동표

- **declared 대조**: topology의 declared stage(`compensation.stage_devices`, `gain_stages_sum.stages`, `vertical_stack_id`)를 `declared` 엣지로 읽어 유도 결과와 비교한다. 불일치는 `review_needed`다. 유도 입력으로는 쓰지 않는다(U-50).
- **발동표** `runs/<run_id>/rule_branch_coverage.json`: 행 = 뷰 × 분기. 열 = 발동 회로, 검증 발동 회로, `계산 규칙 있음/기록만`, 순방향 밖 셀. 검증 발동 = 발동 + ratified 대조표 일치 + `계산 규칙 있음`. 검증 발동 0인 분기를 타는 회로는 탐색 전에 `StructureUnresolvedError(unsupported_rule_branch)`(exit 2)로 정지한다.

### 1.11 6a 열린 항목의 알고리즘 결정

| 항목 | 결정 |
|---|---|
| ① VDS-1 계수 | as-built `gvgs_cycles`가 낸다(OK) |
| ② CD 병렬 합류 | R(u)가 먼저(1.9) |
| ③ 구조로 못 가르는 DC 역할 그룹 | 잠정 신호 소자로 셀·stage를 유도하되 그 블록에 `review_needed`를 달아 GB4 전에 정지한다 |
| ④ diode source로 들어오는 신호 | source 진입이므로 전압 구동이다. diode 자체는 `diode_load`라 stage를 시작하지 않는다 |
| ⑤ 보상 후보 혼입 | 40 §3.5 |
| ⑧ | 1.6 |
| ⑨ | 1.7 |
| ⑩ | 1.7-4 |
| ⑪ | 1.7-3 |
| ⑫ G_vgs 레일 병합 | as-built를 따른다 |
| ⑬ | 1.6 |
| ⑭ | 1.9 |
| ⑥ 대조표 수치 | 이 구현의 출력으로 갱신한다 |
| ⑮ | 사용자(J 신설, 40 §9 Q7) |

**불변식**:
- 같은 입력이면 같은 S1v다(정렬 순회).
- 이름을 전단사로 바꾸면 결과도 그 사상만큼만 바뀐다.
- 축약 뷰와 비축약 뷰의 stage·셀 결과가 같다(다르면 목록으로 보고).

**실패**: `StructureUnresolvedError`(`review_needed`, `unsupported_rule_branch`, `undeclared_loop_constraint`, `column_unassigned`).

**상태**: 1.1~1.10 전부 MISS. 부분 대리물: `E/authoring/_feedback_cuts.py:11`(선언 feedback 절단), `E/metrics/loop_cut.py:60`(수치 절단), `[ng-cmfb-pm] E/authoring/cm_partition.py`(CM 구동/소비), `E/graph/matching_groups.py:202`(`_loop_nets` SCC).

---

## 2. FR-2 -- 블록 gain 모델과 MNA 잔차 (GB8, MOD5)

### 2.1 정의

**블록 국소 소신호 모델**(P N3.8):
- 미지수: 블록 노드 집합.
- 입력 넷: 단위 전압으로 구동한다.
- 블록 밖 노드: 그 뷰의 교류접지이거나, 다음 블록 입력 넷 어드미턴스(다음 블록 국소 모델에서 계산한 cgd·cgs·cgb 스탬프, CD 입력은 부트스트랩 포함)로 고정한다.
- 스탬프: 소자 단자별 gm·gmb·gds·용량과 수동소자다. 값은 봉인 스냅샷 `ss`에서 읽는다.

**블록 gain**: `gain_block_ss_db = 20·log10|V(out)/V(in)|`(ω → 0 극한).

**출력 임피던스 Z_out**: 입력을 교류접지로 두고 출력노드에 단위 전류를 주입했을 때의 전압이다. CS 한 단이면 블록 gain = gm_in·Z_out이 되며, 이것은 일반식의 특수형이다(분기를 두지 않는다).

**복합 블록**: 묶음 전체를 한 모델로 스탬프한다. 경로 p의 기여 = 다른 경로 입력 소자의 gm을 0으로 둔 국소 해이며, 부호와 함께 기록한다.

**버퍼 블록**: 같은 모델로 gain ≤ 1과 Z_out을 낸다.

### 2.2 잔차

`gain_residual_db = gain_ss_db(전회로 MNA, gain 제약 전달 뷰) − Σ_i gain_block_ss_db(i)`이고, i는 그 뷰 사슬의 모든 블록이다. 봉인을 통과한 **모든 평가**에서 S2 `ss.block_gain{block_key: {gain_db, zout_ohm, contributions}}`와 `ss.gain_residual_db`를 쓰고, S3 evals 요약에 넣는다.

금지: 전체 MNA 해를 잘라 전압비를 곱하는 식의 정의(정의상 참)는 쓰지 않는다(P N3.8). 블록을 가로지르는 되먹임 수동소자가 있는 블록의 gain은 '분해값'으로만 표시한다.

`rout_ss_ohm`(DEC-66)도 같은 방식으로 Thevenin 잔차를 기록한다: `rout_residual = rout_ss_ohm − Z_out(마지막 블록)`.

### 2.3 계산 방법과 비용

- **조립**: 블록 노드 부분집합 위에서 as-built `build_mna`가 쓰는 스탬프 함수(`mos_stamps`, `stamp_two_terminal`)를 재사용해 부분 행렬 (G_b, C_b)를 조립한다.
- **풀이**: ω → 0 극한은 as-built `solve_dc_limit`과 같은 방법(전하 보존 극한)으로 푼다.
- **캐시**: 블록 키 + 봉인 `ss` 입력 버전 투영으로 필드 캐시한다. 블록 수가 작아(9회로에서 최대 수 개) 평가당 비용은 전회로 MNA의 일부다.

**파일**: `E/metrics/block_model.py`(조립·풀이), `E/metrics/block_residual.py`(잔차 필드).

**감도 게이트**: 40 §3.8-2.

**결합 잔차 측정**(P N3.7, 회로당 1회, 기본 활성): `dof_rank_sample_count`개의 준난수 θ 표본에서 봉인 통과 점의 잔차 분포를 잰다. 이 분포는 41 §5.5의 잔차 여유 r̂로 쓴다.

**상태**: MISS(`metrics/CONTRACT.md:13-14`).

---

## 3. FR-3 -- 보상 먼저 (연계)

GB5 규칙은 40 §3.5에 있다. gain 예산과의 연계는 두 가지다.
- (a) 보상이 요구하는 gm(`gm_req`, MNA 1-D 근)은 층 0 국소 문제의 하한 입력이다. 근사식 값(출발값)은 41 §6.3에서 온다.
- (b) 보상 수동소자 값은 θ 연속 성분이라, 층 0 국소 문제에서는 근사식 출발값으로 고정하고 외층이 다듬는다. 근사 대 MNA 차 `comp_approx_gap`은 조립점에서 기록한다.

---

## 4. FR-8 -- 탐색 전 달성 불가 판정 (GB4, MOD5)

**파일**: `E/metrics/achievability.py`(진입점), `block_gain_bound.py`, `dof_report.py`, `area_lower_bound.py`. 모두 S0당 한 번 실행하며 평가 커널 컨텍스트에 둔다.

### 4.1 블록 gain 상한 A_i,max (봉인 불필요, 보수적)

**정의**(P N3.7): A_i,max = 블록 i 국소 모델 gain의 최댓값이다. 범위는 gm_id 격자 × LUT L 점과 bin 안 연속 L × W4 창 VDS × y 가능역이다.

**계산**(전수 대신 인증된 완화):
1. **소자별 극값 표**(LUT, S0당 1회): (kind, L 점, VDS) 칸마다 gm/ID 최대값, gds/ID 최소값, gmb/ID 범위를 구한다. 근거는 `CurveRow.gm_gds_max`와 곡선 표다. bin 안 L 내부 극값이 양끝 L 점 값을 넘는지 확인해 넘으면 포함한다(P N3.7).
2. **완화 점**: 블록의 각 소자 k에 'gain을 키우는 방향의 극값'을 준다.
   - 신호 경로의 gm(입력·캐스코드·CD)은 최대 gm/ID × 전류다.
   - 출력노드 gds 기여 소자는 최소 gds/ID × 전류다.
   - 전류는 블록 KCL 비(전류 기저·미러 비)로 묶어 공통 배율 하나로 정규화한다. 블록 gain은 전류 배율에 대해 0차 동차이므로 배율은 소거된다.
3. **인증**: 그 점에서 블록 국소 모델 gain의 adjoint 감도 ∂A/∂p(as-built `response_sensitivity`와 같은 방식)의 부호가 가정한 방향과 맞는지 확인한다(gm 쪽 ≥ 0, gds 쪽 ≤ 0).
   - 맞으면 A_i,max를 '인증됨'으로 둔다.
   - 맞지 않는 파라미터가 있으면 그 블록 상한을 '상한 미상'으로 두고 판정에 쓰지 않는다.
4. **행 기록**: 블록마다 상한과 그 상한을 낸 (gm/ID, L, VDS) 조건을 기록한다. GB5 `gm_req`로 다시 거를 때는 이 표의 행을 필터로 쓰고, LUT 격자를 다시 돌지 않는다.
5. **버퍼 블록**의 상한은 ≤ 0 dB다(같은 계산).

### 4.2 판정

gain 제약 전달 뷰의 블록 사슬(복합 블록으로 묶은 뒤)에서 Σ_i A_i,max(dB) + r̂_max < G_target − b_gain이면 `InfeasibleTargetError(INFEASIBLE_TARGET)`(exit 3)로 탐색 전에 정지한다.
- b_gain = gain metric 분해능이다.
- r̂_max = 결합 잔차 측정의 최댓값이다. 측정 전에는 0을 쓰지 않고 판정을 보류해 보고만 한다.

블록 중 하나라도 '상한 미상'이면 판정하지 않고 보고만 한다. 결과는 표 `achievability{blocks[{key, A_max_db, certified, condition}], sum_db, target_db, verdict}`로 남긴다.

### 4.3 면적 하한 (결정 11 확장)

면적 예산이 선언되면 A_lb = Σ_k I_k,min·L_k,min²/IDu_k,max를 계산한다.
- I_k,min은 41 §6.3의 gm 요구에서 나오는 최소 전류다. 요구가 없는 소자는 I_off다.
- L_k,min은 출발 구간 하한이다.
- IDu_k,max는 LUT 최대 전류밀도다.
- 수동소자 면적 하한을 더한다(값 θ 하한 / MIM 밀도). 측정 부하는 뺀다.

A_lb > 예산 + b_A이면 INFEASIBLE_TARGET(사유 `area_budget_below_lower_bound`)이다.

### 4.4 DOF

**구조 rank**:
- 변수: W0·W1·W3가 쓰지 않는 노드전압, writer ln IDu, L 동치류 L, θ 전류 변수, DC 경로 미선언 저항.
- 등식: diode, `equal_vgs`, `budget_ref`, `stacked_vsb`, `kvl_branch`, KCL.
- 둘로 이분 그래프 최대 매칭을 만들어 구조 rank를 구한다. 등식이 변수보다 많아 매칭되지 않으면 `overconstrained` → INFEASIBLE_TARGET이다. 남는 변수는 `underdetermined` 목록이다.

**수치 rank**:
- 표본 수 = `dof_rank_sample_count`(spec 선언, 출처 필수)다.
- θ 표본마다 봉인을 통과한 점에서 등식 잔차의 Jacobian을 FD로 구한다. 스텝 = 그 변수의 LUT 격자 간격이다.
- `numpy.linalg.matrix_rank` 기본 허용오차로 rank를 잰다.

**출력**: `DofReport{status: ok|underdetermined|overconstrained, structural_rank, numeric_ranks[], competing_pairs}`.

**상태**: 4.1~4.4 전부 MISS. 4.4 수치 rank는 40 §8 R3(사용자 결정)에 따른다. 구조 rank는 비용이 작아 기본으로 둔다.

---

## 5. FR-4 -- 층 0 gain 예산 조합 front와 `gain_budget_db` (GB6, MOD6)

**정본 규칙**: DEC-71 (1)~(8), DEC-73, DEC-77, DEC-03. **파일**(MOD6 `search`):

| 파일 | 내용 | 절 |
|---|---|---|
| `layer0_budget.py` | 진입점 | -- |
| `gain_bins.py` | 활성 조건·bin 정의 | 5.1 |
| `local_problem.py` | 블록 국소 문제 | 5.2 |
| `local_front.py` | 블록별 국소 front | 5.3 |
| `combo_dp.py` | 조합 DP | 5.5 |
| `assembly.py` | 조립 | 5.4 |
| `budget_override.py` | override | 5.6 |

### 5.1 활성 조건과 bin

**활성 조건**: gain 제약 metric(`gain_ss_db >= G`)이 선언됐고, 그 전달 뷰의 이득 블록이 1개 이상이며, `review_needed`가 없어야 한다. 아니면 아래처럼 처리한다.
- 이득 블록이 없고 버퍼 블록만 있으면 `rout_ss_ohm` 제약을 국소 AC 제약으로 쓴다. 그것도 없으면 '층 0 AC 무동작'으로 보고하고 출발 구간(§6)만으로 시작점을 만든다(DEC-71 (3)).
- gain 제약이 없으면 gain bin 없이 블록마다 (전력, 면적) 비지배 점만 만든다.

**gain bin**:
- 블록 i의 bin은 [A_i,min, A_i,max] 구간을 폭 w_g로 나눈 것이다. A_i,min은 블록이 봉인을 통과하는 최소 gain이며, 국소 문제 결과로 갱신한다.
- 폭 w_g = max(gain 분해능 b_gain, gain 모델 오차 `model_error_gain_ss_db`)(DEC-72)다.
- 모델 오차가 측정되기 전에는 b_gain만으로 bin을 나누고, front를 '추정'으로 표시한다(DEC-72·77).

**면적 bin** 폭 = max(레이아웃 격자 분해능, 면적 축 모델 오차)(DEC-80).

**예산 게이트**: 점 수 상한(gain bin 수 × 면적 bin 수, 그리고 DP 상태 수)이 DEC-34 평가 예산을 넘으면 bin 폭을 2배씩 넓히고 배수·사유를 기록한다.

### 5.2 블록 국소 문제

**범위**: 블록 i의 소자를 덮는 기둥 집합이다(S1 기둥 ∩ 매핑표). 어느 블록에도 속하지 않는 바이어스 기둥은 '바이어스 기둥 국소 문제'로 따로 푼다. 다른 블록에 gds로 기여하는 소자는 그 블록의 고정 입력이다.

**결정 변수**: 블록 소자의 ln IDu(또는 gm/ID), L 동치류 L, 기둥 내부 노드전압(VDS 배분).

**고정 입력**: 국소 확정 금지 소자(K1·K3·K8과 블록을 가로지르는 L 동치류)의 값이다. 첫 회차는 출발 구간 값(§6), 이후 회차는 직전 조립점 값이다.

**DC 제약**: 덮는 기둥의 KVL, 분기 노드 KCL, 포화 여유(VDS ≥ VDSAT + tol_VDsat), diode, 벌크 역바이어스.

**AC 제약**: 블록 국소 모델 gain ≥ bin 하한이다. 버퍼 블록이면 Z_out ≤ 선언 `rout_ss_ohm`이다.

**목적**: 블록 소자의 (전류 × 레일 전압차 합, Σ W·L + 블록 수동소자 면적)이다.

**푸는 방식**(역산 우선, DEC-71 (4)):
- (a) 필요 gm(보상 `gm_req` 근사 또는 bin gain에서)과 전류 후보로 gm/ID를 역산한다.
- (b) bin gain에서 필요한 gm/gds로 L을 bin 안에서 역산한다. bin 선택은 이산이고 bin 안 L은 연속이다(LR3).
- (c) VDS를 배분한다. 모든 소자를 VDSAT + tol_VDsat 하한으로 채운 뒤, 남는 헤드룸을 LUT ∂(gm/gds)/∂VDS가 큰 소자부터 준다.
- (d) 기생 용량 반영 고정점을 돈다. 수렴 판정과 상한은 P N3.6 K_max다.
- 역산이 불가하거나 비단조이면 그 소자만 LR5 격자로 폴백하고 사유를 기록한다.
- 초기점은 as-built `layer0_center`의 상자 중심과 전류 Chebyshev 중심을 블록 변수에 제한해 쓴다.

**국소 봉인**: 봉인 항목 1·2·6·7과 기둥 KVL·KCL이다. 실패는 `local_infeasible` 레코드(margin 정규화, N3.14)로 남긴다.

### 5.3 블록별 국소 front

블록마다 `{gain bin → (전력, 면적) 비지배 점들}`을 만든다. 한 (gain bin, 면적 bin) 칸에는 전력이 최소인 점 하나만 남기고, 같은 칸 동률은 포화 여유 최솟값이 큰 점을 남긴다. 점마다 θ_block, VDS 배분, 국소 gain, Z_out, 고정 입력 지문을 보관한다.

### 5.4 조립

조합 하나(블록마다 점 하나)를 받아 θ를 합친다. 조립 등식(공유 노드, 공유 VGS(K2, 선택 기준은 DEC-10 gain), 미러 비, `kvl_branch`, 폴딩 노드 KCL)을 풀어 y 초기값을 정한다. 그다음 평가 커널을 1회 돌려 국소 값과 전역 값의 차(ΔVGS, Δ노드전압, Δgm_id, Δ블록 gain)를 기록한다.

봉인에 실패하면 다음 조합으로 넘어간다. 그것이 예산 재배분이다.

### 5.5 조합 DP와 예산 조합 front

**상태**: (블록 순서 k, 누적 gain bin, 누적 면적 bin). 값 = 그 상태에 도달하는 비지배 (전력) 최소 경로 집합이다.

**전이**: 블록 k+1의 국소 front 점 하나를 고른다. 누적 gain = Σ 블록 gain_db, 누적 면적 = Σ 면적이다.

**종료 조건**: 누적 gain + r̂ ≥ G − b_gain이다.
- r̂ = 결합 잔차 측정(§2.3)의 중앙값이다.
- 측정 전에는 r̂ = 0으로 두고 그 front를 '추정'으로 표시한다.
- 잔차의 산포는 조립 단계의 실제 MNA 판정이 흡수한다. 판정은 언제나 전회로이므로 r̂는 후보 순서만 바꾼다.

**출력**: 종료 상태 전체에서 (전력, 면적) 비지배인 조합 front다. 각 조합의 `gain_budget_db = {block_key: bin 중심 gain_db}`다. 한 점을 골라야 할 때의 동률 규칙은 전력 → 활성 제약 여유 합 → 블록·점 이름 정렬(NFR-4)이다.

**조립 순회**: front 조합을 전력 순으로 조립(5.4)한다. 성공한 조합이 시작점 목록 맨 앞에 온다.

### 5.6 `gain_budget_db` 출력과 override

**front 점마다 두 값을 기록한다.**
- `gain_budget_db.allocated`: 층 0이 배분한 값.
- `gain_budget_db.realized`: 최종 봉인 스냅샷의 블록 gain(§2).
- 두 값의 차와 `gain_residual_db`를 함께 front 표와 결과 JSON에 낸다.

**`gain_budget_db_override{block_key: {value_db, source}}`**(spec, 출처 필수):
- override가 있는 블록은 bin을 그 값을 포함하는 bin 하나로 고정한다.
- 조합 DP는 나머지 블록만 고른다.
- 블록 키가 S1v에 없으면 `SchemaRejectedError(override_block_unknown)`다.
- 고정 bin이 A_i,max보다 크면 INFEASIBLE_TARGET이다.
- 결과에 `override_source`를 기록한다.

### 5.7 외층과의 인계

**외층 SLSQP**(40 §3.6):
- 조립된 조합점에서 시작한다.
- 그 조합의 블록 gain을 **제약으로 걸지 않는다**. 판정은 전회로 `gain_ss_db` 하나다(DEC-05·74). 층 0 예산은 출발점과 보고값이다(EP-7).
- 근방 격자 반경 초기값은 격자 분해능과 DEC-34 예산에서 계산하고, feasible이 없으면 2배로 넓힌다.
- ε-제약 스윕은 front 조합의 각 점의 면적을 첫 ε로 쓴다.

**불변식**:
- 층 0이 전역 bounds를 줄이지 않는다.
- 같은 입력이면 같은 조합 front가 나온다.
- 층 0 국소 평가와 조립 평가의 계수가 `perf`에 남는다.

**실패**:
- 모든 조합의 조립이 실패하면 출발 구간 시작점(§6)으로 넘어가고 사유를 기록한다.
- 그것도 없으면 `SearchFailedError`다.

**상태**: 5.1~5.7 전부 MISS. 대체 중인 as-built: `E/search/layer0_center.py`(spec 무관 feasibility 중심 시작점 하나).

---

## 6. 스펙에서 gm/ID·L·전류 출발 구간 유도 (topology 무관)

**목적**: 스펙과 LUT에서 소자마다 gm/ID 구간, L 구간, 전류 출발값을 계산한다. 결과는 층 0 국소 문제의 초기값, 추가 시작점 후보, 보고 표로만 쓴다. 판정에는 쓰지 않는다(EP-7). 모든 식의 입력은 S1/S1v 구조 사실, spec 선언값, LUT 곡선이고, 회로 이름을 쓰지 않는다.

**파일**: `E/search/start_intervals.py`(진입점). 하위 계산 블록은 `iv_headroom.py`, `iv_speed.py`, `iv_gain_l.py`, `iv_matching_l.py`, `iv_noise_l.py`, `iv_area.py`, `iv_currents.py`다. LUT 곡선은 `lut`의 신규 `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`를 쓴다. 이 곡선들은 (kind, L, VDS, VSB)마다 gm/ID 축 배열을 S0당 한 번 만들어 LUT memo에 둔다.

### 6.1 소자 집합과 순서

대상은 S1 소자 전부다. 대칭 궤도(40 §6)의 대표만 계산하고 궤도 전체에 복사한다. L 동치류는 구간의 교집합을 쓴다.

### 6.2 gm/ID 하한 -- 헤드룸

**기둥**(S1, 레일 쌍 사이 단순 경로)마다:
- 가용 폭 V_col = ΔV_rail − Σ(기둥 안 비포화 강하)로 정의한다. 비포화 강하는 diode VGS(같은 gm/ID 출발값에서 LUT VGS)와 DC 경로 저항 강하다.
- 출력 스윙 스펙(`swing`·ICMR 제약)이 선언됐고 기둥이 그 노드를 지나면 그 스윙 폭을 더 뺀다.

**포화 소자 k**: 필요조건은 Σ_j (VDSAT_j + tol_VDsat,j) ≤ V_col이다. 소자 k의 하한은 다음과 같다.
- VDSAT_k(gm/ID_k) ≤ V_col − Σ_{j≠k}(VDSAT_j,min + tol_VDsat,j)
- VDSAT_j,min은 LUT의 가장 큰 gm/ID(약반전 끝)에서의 VDSAT다.
- 이 식을 `vdsat_curve`로 역산해 gm/ID_k,lo를 얻는다. VDSAT는 gm/ID에 대해 감소하므로 하한이 된다.
- 소자가 여러 기둥에 있으면 하한들의 최댓값을 쓴다.

이 식은 배분 상수를 쓰지 않는 **필요조건**이다(다른 소자가 모두 최소 VDSAT일 때도 성립해야 한다).

### 6.3 gm/ID 상한 -- 속도, 그리고 전류 출발값

**전제**: spec에 `gbw_target_hz`와 `pm_target_deg`가 있다. 없으면 이 절은 비활성으로 보고한다.

**비주극점 요구**: 2극점 근사에서 PM = 90° − atan(GBW/f_p2)이므로 f_p2 ≥ GBW / tan(90° − PM)이다.

**fT 요구**: S1v 극점 노드 목록에서 주극점 노드(보상 커패시터가 걸린 노드나 출력노드 중 gain 제약 전달 뷰에서 Miller (2) 루프의 끝)를 뺀 '낮음' 등급 노드의 소자를 본다. 그 노드의 극점 주파수는 gm/(2π·C_node) ≤ gm/(2π·cgg) = f_T이므로 필요조건은 f_T(gm/ID, L) ≥ f_p2다.

**gm/ID 상한**: f_T는 gm/ID에 대해 감소하므로 `ft_curve` 역산으로 gm/ID_k,hi(L)를 얻는다. 이 상한은 L에 의존하므로 6.4의 L 구간과 함께 2차원 구간으로 기록한다.

**다극점 회로**: 모든 비주극점에 같은 조건을 쓴다. 이 조건은 출발 구간용이고 판정이 아니다. 영점·feedforward가 있는 회로에서는 필요조건이 아닐 수 있어서 결과에 '속도 상한 = 2극점 근사' 표시를 붙인다.

**선택**: 구간 [gm/ID_lo, gm/ID_hi] 안의 **최대 gm/ID**를 쓴다. 이것이 같은 gm에서 전류를 최소로 한다.

**전류 출발값**:
- 입력 소자: gm_in = 2π·GBW·C_eff다. 단일단이면 C_eff = 부하 + 출력노드 자기용량, Miller면 C_eff = 보상 커패시터의 출발값이다.
- 보상 커패시터 출발값: DEC-92 (2) 근사식을 출발값으로만 쓴다. 비주극점 조건 gm_2 ≥ 2π·f_p2·C_L과 함께 쓰고, `comp_approx_gap`을 기록한다.
- 출력단 소자: gm_2 = 2π·f_p2·C_L이다.
- 전류: I = gm / (gm/ID)다.
- 나머지 소자: 미러 비(matching 레코드)와 전류 기저(KCL)로 전파한다. θ 전류 변수 중 남는 것은 상자 기하 중심을 쓴다.
- 이 전류가 4.3의 I_k,min이다.

### 6.4 L 구간

**하한 -- 이득**: 블록 i의 gain 목표 g_i를 정한다. 층 0 bin이 있으면 그 bin, 없으면 첫 회차 시작 배분 g_i = G·A_i,max/Σ A_max(DEC-71 (3))다. 블록 국소 모델에서 블록 소자를 6.3의 gm/ID 출발값과 후보 L로 두고 gain ≥ g_i를 만족하는 가장 작은 L을 찾는다.
- bin 선택은 LUT L 점을 오름차순으로 훑는다.
- bin 안 연속 L은 선형 보간 위에서 bisection으로 찾는다. 상한은 K_max다.
- L 동치류마다 하나씩 찾는다. 출력노드 gds 기여 동치류부터 시작하고, 나머지 동치류는 knee 앵커(LR5)로 고정한다.

**하한 -- matching**(DEC-96 (2), Q2·Q3 선행):
- 오프셋 스펙 σ_os,target 또는 미러비 오차 스펙이 선언된 matching 그룹이 대상이다.
- 소자 쌍의 필요 면적: σ(ΔVth)² = A_VT²/(W·L), 전류 비 오차는 σ(ΔI/I)² = (gm/ID·σ_VT)² + A_β²/(W·L)이다. 입력 환산은 DEC-23 gm 가중 RSS다. 필요 면적 A_min = (A_VT² + A_β²/(gm/ID)²)/σ_target²(쌍 1개 기여 기준)다.
- W·L = I·L²/IDu이므로 **L ≥ √(A_min·IDu/I)**다.
- A_VT·A_β는 PDK 선언에서 읽는다. **선행 조건**: 현재 선언이 없다. 로컬에는 `C:/pdk/sky130_fd_pr/cells/{nfet,pfet}_01v8/*__mismatch.corner.spice`(`vth0_slope`, `toxe_slope` 등)가 있으나, A_VT·A_β로 바꾸는 유도와 단위 확인이 되지 않았다(40 §8 R17, §9 Q2). 그 전에는 이 하한이 비활성이고 보고에 '계수 미확보'를 적는다.

**하한 -- flicker 잡음**:
- 입력 환산 잡음 스펙 S_target(f)가 선언된 경우에만 활성이다.
- LUT 잡음 열 `SVG2_1HZ`(W 정규화)를 쓴다. 이것이 정본이고 K_F 식은 쓰지 않는다(P N1.2).
- 필요조건은 S(gm/ID, L)·w_ref/W ≤ S_target이고, W = I·L/IDu를 넣어 L 하한을 역산한다.
- 9회로에 잡음 스펙이 없고(사용자 2026-10-07) LUT 조회 함수도 없으므로 경로는 설계만 두고 비활성이다.

**상한 -- 속도**: 6.3의 f_T(gm/ID, L) ≥ f_p2를 L에 대해 역산한다. f_T는 L에 대해 감소하므로 L ≤ L_fT,max다.

**상한 -- 면적**(결정 11): 면적 예산 A_budget이 있으면, 한 소자만으로도 예산을 넘지 않아야 하므로 필요조건 W·L = I·L²/IDu ≤ A_budget에서 **L ≤ √(A_budget·IDu/I)**다. 같은 식으로 W ≤ A_budget/L을 상자 제약으로 쓴다(40 §7.1).

**bin 규칙**: 구간 끝이 다른 bin에 있으면 bin마다 후보 하나를 만든다. bin 경계를 넘는 보간은 하지 않는다(LR3).

**선택**: 이득 하한과 matching 하한의 최댓값을 L 출발값으로 쓴다(전력·면적 최소 쪽).

### 6.5 충돌

다음 경우에 충돌 레코드 `StartConflict{device|class, quantity, bounds[{source, value}], gap}`를 남긴다.
- 어느 구간이든 하한 > 상한(gap > 해당 분해능)
- 6.3 전류가 상자 상한(I_max)을 넘음
- 4.3 면적 하한이 예산을 넘음

조용히 한쪽으로 자르지 않는다(EP-8). 충돌한 구간은 양 끝점 각각으로 후보를 만들어 층 0에 넘기고, 후보에 '충돌'을 표시한다.

### 6.6 소비와 보고

- 층 0 국소 문제의 초기점과 고정 입력 첫 회차 값(5.2)
- 외층 시작점 목록의 추가 후보(조립점 다음)
- 결과 JSON 표 `start_intervals[{device, kind, gm_id_lo/hi/chosen, L_lo/hi/chosen, bin, I_start, bounds_sources, conflicts}]`

계산은 S0당 한 번이다(평가 커널 컨텍스트 필드).

**불변식**:
- 같은 입력이면 같은 표가 나온다.
- 이름을 전단사로 바꾸면 행 이름만 바뀐다.
- 비활성 경로(잡음, 계수 없는 matching, 속도 스펙 없음)는 '비활성: 사유'로 표에 나온다.

**상태**: 6.1~6.6 전부 MISS. as-built 출발값은 spec 무관이다(`E/search/search_domain.py:35-56`, `layer0_center.py:105-172`: LUT 포락선 상자 중점).

---

## 7. 상태 요약

| 절 | 항목 수 | OK | DEV | PART | MISS |
|---|---|---|---|---|---|
| §1 SP1 | 10 | 0 | 0 | 1(1.2 정적 교류접지) | 9 |
| §2 블록 모델·잔차 | 3 | 0 | 0 | 0 | 3 |
| §4 GB4 | 4 | 0 | 0 | 0 | 4 |
| §5 층 0 gain 예산 | 7 | 0 | 0 | 1(5.2 초기점 재료) | 6 |
| §6 출발 구간 | 6 | 0 | 0 | 0 | 6 |
