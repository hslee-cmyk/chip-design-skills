# MOD3 구조 유도 U2~U5 -- 짧은 design (6a 1차분)

- 작성 2026-10-07. 문서만 썼다(코드 없음, 저장소 읽기만). 실측 스크립트·원자료는 세션 scratchpad(`m.py`, `m_out.txt`~`m4_out.txt`)에만 있고 저장소에는 없다.
- 입력 정본: `wt/ng-graph` 브랜치 `ng-graph`(97e401e) `gmid_engine/graph/CONTRACT.md`(이하 GC). 그 밖: `6a_structure_prep.md`(S6a, R0~R19), `design_mod3_s1_graph.md`(DS1), `design_gb7_dc_canonical.md`(GB7), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항', `_drafts/user_decisions.md` 2026-10-07, 계획 P = `ng-graph/docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(DEC-64 263행, DEC-70 269행, DEC-71 270행, 용어집 91~93행, N3.2 351행, N3.3 373행, J 1118~1139행).
- **[2026-10-07 개정 -- reference 검토 Q8·Q10 추천안 확정, 사용자 "B는 추천대로 해."]** 계획 worktree `plan-rev4` 커밋 `defdc24`: matching 분류 규칙(DEC-93 (1), J14 신설 = 옛 J-U4 회로별 ratify), 종속 소자 구조 우선순위(DEC-95 (3)). 아래 [개정] 표시.
- 표기: **[결정]** 회로 해석이 아닌 설계 기본안(원칙에서 고름). **[J]** 사용자 공동분석 필요(6절). **[JSON]** topology JSON 직접 집계 기대값, **[손]** 손계산, **[계획]** 계획서 측정 기대값, **[정정 후 재측정]** 대기열 Q1~Q5 반영 뒤 바뀔 수 있는 값.

## 0. 범위·번호 대응·대원칙

| 이 문서 | 내용 | S6a 단위 | GC 4.3 예약 필드 |
|---|---|---|---|
| U2 | DC 전도 그래프(잎 가지치기)·병렬 합침 segment·가지·기둥 | U2 (R5) | (`graph`,`branches`)·(`graph`,`columns`) |
| U3 | 소자 DC 역할(dc_role) | U4 (R2) | (`device`,`dc_role`) |
| U4 | 관계 엣지(equal_vgs·vds_eq_vgs·kcl_group·matching_ratio·matching_offset·l_class·kvl_branch)와 G_vgs 사이클(DEC-64) | U3·U5 (R3·R4) | (`edge`,`relation`) -> 4.0에서 바꾼다 |
| U5 | 교류접지(뷰별)·기본 전달 뷰 수집·신호 도달성(최소 고정점)·순방향 넷·바이어스 종속 넷 -- 셀 분류(R9) 입력 준비 | U6·U7 (R6~R8) | 없음(S1v) |

**대원칙(사용자 2026-10-07, 오케스트레이터 전달)**: topology 에 종속된 엔진을 만들지 않는다.
1. 모든 규칙은 connectivity(S1 필드)·선언(ports·supply_nets·passive/ideal 선언·이후 spec metric 선언)·LUT 에서만 판정한다. 회로·소자·넷 이름, `topology_name`, 옛 `compensation.function`·`device_roles`·`symmetry` 같은 회로별 키를 읽지 않는다(TopologyDoc 에 애초에 없다). 이름은 **결정론적 순서 tie-break** 로만 쓰고, 그 경우 판정 결과의 **개수·불변량은 이름과 무관**해야 한다(5.3 metamorphic test 로 강제).
2. library 9회로에 없는 구조가 오면 특수 처리 없이 core `StructureUnresolvedError`(reason `unsupported_rule_branch`, `rule_branch` = 아래 각 절의 이름, exit 2)로 **탐색 전 정지**한다(DEC-59·DEC-76). 정지 분기는 모두 test 에서 '실제로 거부한다'를 먼저 확인한다.
3. 반복 계산 금지: 각 계산 블록은 core `@compute_block` 하나(규칙 C)이고 결과는 graph 필드다(필드가 곧 캐시). 입력 투영이 같으면 reuse. `supplies_v` 만 바뀌면 U2~U4 블록은 하나도 다시 돌지 않는다(어느 블록도 `device.bulk`·supplies 를 읽지 않는다 -- 4.0 표).

### 0.1 선행 변경(1단계 S1 계약 개정 2건, 회로 해석 아님 [결정])

- **C1 `device.dc_nets`**: `s1_structure` 가 authoring `dc_edges_unpruned`(DEC-70 유일 정의)를 불러 원소마다 DC 엣지 넷 쌍(정렬 2-tuple, 엣지가 아니면 None)을 쓴다. U2 가 이 필드만 읽어서 DC 엣지 정의가 둘로 갈라지지 않는다. 블록 투영으로 doc 을 다시 받지 않는다.
- **C2 예약 필드 교체**: GC 4.3 `RESERVED_FIELDS` 네 행을 4.0 표의 필드로 바꾼다. `S1_WRITERS` 가 바뀌므로 새 lineage 다(GC 8절이 예고한 것). GC 9절에 '설계와 다르게 정한 점'으로 적는다.

---

## 1. U2 -- DC 전도 그래프·가지·기둥 (DEC-70·DEC-71 (1), J13)

### 1.1 파일 (규칙 A~D: 파일 1 = 진입점 1 = 계산 블록 1, test 1:1)

| 파일(층) | 진입점 = 블록(writer) | reads | writes |
|---|---|---|---|
| `dc_conduction.py`(2) | `s1_dc_conduction` | `device.{dc_nets, element_class, kind, unsupported}`, `node.{is_rail, port_direction}` | `graph.dc_pruned`, `graph.dc_segments` |
| `branches.py`(3) | `s1_branches` | `graph.dc_segments`, `node.is_rail` | `graph.branches`, `node.dc_branch_node` |
| `columns.py`(4) | `s1_columns` | `graph.branches`, `node.is_rail`, extras `(column_limit,)` | `graph.columns`, `graph.column_orphans` |

값 형식(`s1_values.py` 에 frozen dataclass로 추가): `Segment(nets: (a, b), elements: tuple)` / `Branch(id, ends: (a, b), segments: tuple[Segment], has_ideal_source: bool)` / `Column(id, rails: (r1, r2), branch_order: tuple[id], parallel_expansion: int, status)`.

### 1.2 알고리즘 (결정론, 한 번씩만 계산)

1. **엣지**: `dc_nets` 가 None 아닌 원소. 정지 검사 먼저: `unsupported` 가 붙은 원소 중 DC 엣지가 되는 것(지원 밖 MOS kind, 지원 밖 수동 kind -- 인덕터는 DC 를 통한다, 이상 전압원) -> `unsupported_rule_branch`(`rule_branch` = 그 원소의 unsupported 분기 이름, devices = 해당 원소). 양 끝이 같은 넷인 엣지(MOS d == s, 저항 양단 같은 넷) -> `dc_self_loop` 정지(9회로 발동 0).
2. **잎 가지치기**(DEC-70): 레일·포트가 아닌 넷 중 DC 엣지가 **저항 하나뿐**인 넷과 그 저항을 제거, 더 없을 때까지 반복. 라운드마다 넷 이름순 처리, 결과 `dc_pruned = ((원소, 라운드), ...)`. 넷별 차수는 처음 한 번 세고 제거할 때 이웃 차수만 줄인다(큐 방식, 전체 재계산 없음).
3. **병렬 합침**(사용자 확정 10: 합쳐 세기 정본): 같은 무향 넷 쌍의 엣지를 한 `Segment` 로 묶는다(원소 이름순). 종류가 다른 병렬(MOS ∥ 저항)도 합친다 [J13-a].
4. **분기 노드**: segment 그래프에서 레일이 아니고 segment 차수 ≥ 3 인 넷. **가지** = 닻(레일 ∪ 분기 노드 ∪ 차수 1 넷) 사이의 극대 직렬 segment 사슬. 닻을 이름순, 각 닻의 segment 를 (반대 넷, 원소) 순으로 훑어 아직 안 쓴 segment 에서 사슬을 뻗는다. 닻이 없는 고리(레일·분기 없는 순환 사슬) -> `dc_isolated_loop` 정지(발동 0). `has_ideal_source` = 이상원 원소 포함.
5. **기둥**: 레일 쌍 (r1 < r2, 이름순, 모든 nC2 쌍)마다 가지 그래프에서 r1 -> r2 **노드-단순 경로**(내부 노드는 레일 아님)를 DFS 로 열거(이웃 = (반대 넷, 가지 id) 순). `parallel_expansion` = 경로 위 segment 원소 수의 곱(따로 세기 병기값 = Σ). 하단/상단 구분은 전위(supplies)가 필요하므로 S1 에 두지 않고 GB7 `rail_v` 소비자가 정한다 [결정 -- supplies 변경이 기둥 재계산을 부르지 않게].
6. **어느 쌍에도 안 드는 가지** -> `column_orphans`(status `review_needed`, 정지 아님 -- DEC-71 (1)).
7. **열거 상한**: 열거 수가 `column_limit` 를 넘으면 `column_enumeration_over_budget` 정지(DEC-71 (3) 폴백 미구현이라 정지). 상한 값의 출처는 7절 열린 결정 O1.

### 1.3 실패 규약

| 상황 | 결과 |
|---|---|
| DC 엣지가 되는 지원 밖 원소, `dc_self_loop`, `dc_isolated_loop`, `column_enumeration_over_budget` | `StructureUnresolvedError`(reason `unsupported_rule_branch`, detail `rule_branch`·`devices`·`nets`) |
| 레일 쌍에 기둥 0(3레일 회로의 agnd 쌍) | 정지 아님. `Column` 없음 + 쌍별 0 을 `graph.columns` 의 쌍 요약에 기록 [J13-c] |
| orphan 가지 | `column_orphans` 기록(정지 아님) |

### 1.4 test 계획

단위(`tests/graph/test_dc_conduction.py`·`test_branches.py`·`test_columns.py`): [손] 소형 픽스처 -- 저항 사슬 잎(2라운드 제거), 포트에 붙은 잎 저항은 남음, 커패시터는 엣지 아님, 병렬 MOS 2개 -> segment 1, 분기 노드 차수 경계(2/3), 이상원 가지 `has_ideal_source`, 각 정지 분기(인덕터·전압원·d==s·고리·상한 1)가 **실제로 정지**.

통합 9회로 [JSON] (2026-10-07 원본 + 메모리 정정본, 작성자 측 교차 확인값 -- test-author 는 JSON 에서 다시 센다):

| 회로 | 잘린 저항 | 분기 노드(합침 / 따로) | 가지(합침 / 따로) | 기둥 합침(정본) / 따로(병기) | 병렬 segment |
|---|---|---|---|---|---|
| current_reuse(파일럿) | Rz1, Rz2 | 7 / **9** | 27 / **32** | **41** / **62** [계획 DEC-71 (3) 일치] | M18a∥M18b, M6∥M7, M9a∥M9b |
| common_gate | -- | 0 / 0 | 1 / 1 | 1 / 1 | -- |
| folded_cascode | -- | 3 / 3 | 8 / 8 | 7 / 7 | -- |
| ngcc_3stage_ff | -- | 1 / 3 | 7 / 12 | 6 / 9 | M7∥M13∥M14, M6A∥M6B |
| nmcnr_amplifier | -- | 3 / 3 | 10 / 10 | 9 / 9 | -- |
| pushpull_follower_buffer | -- | 0 / 0 | 3 / 3 | 3 / 3 (vss-vdd만, agnd 쌍 0) | -- |
| sf_pushpull_output_opamp | -- | 1 / 1 | 9 / 9 | 8 / 8 (vss-vdd만, agnd 쌍 0) | -- |
| two_stage_ota | -- | 1 / 1 | 4 / 4 | 3 / 3 | -- |
| two_stage_ota_sf | -- | 1 / 1 | 5 / 5 | 4 / 4 | -- |

**[정정 후 재측정]**: nmcnr(Q3''' Rm 잘림, RL∥M301 합침) -> 분기 3 / 4, 가지 10 / 12, 기둥 9 / 10. two_stage_ota(Q4' Rz 잘림) 수치 불변. folded(Q1 극성, Q5 CL) 불변. orphan 가지 9/9 모두 0. "나머지 회로 3~9"(DEC-71 (3))와 일치.

추가: (a) `supplies_v` 만 바꾼 `build_s1(previous=...)` 에서 세 블록 compute 0 (b) 넷 이름순·netlist 순서 섞기·`PYTHONHASHSEED` 1~5 에서 `graph.fp` 동일 (c) 기둥 경로마다 연속 가지가 넷을 공유하고 내부 노드가 레일이 아님(불변식).

---

## 2. U3 -- 소자 DC 역할 (용어집 91행 (1)~(5), DEC-57)

### 2.1 파일

| 파일(층) | 블록 | reads | writes |
|---|---|---|---|
| `gs_groups.py`(2) | `s1_gs_groups` | `device.{element_class, kind, pins, unsupported}` | `graph.gs_groups` |
| `dc_roles.py`(3) | `s1_dc_roles` | `device.{element_class, kind, pins, is_diode}`, `node.{is_rail, ac_ground_class}`, `graph.gs_groups` | `device.dc_role` |

`gs_groups` = 같은 (kind, gate 넷, source 넷)인 MOS 2개 이상 묶음 전부(레일 gate 포함 원자료). U3 (2)와 U4 `equal_vgs` 가 **같은 필드 하나**를 읽는다(개념당 정의 하나 -- GC 8절 `gs_groups()` 질의를 필드로 실현).
`DcRole(role ∈ {diode_reference, bias_current_source, signal}, status ∈ {derived, review_needed}, evidence{rule ∈ {"1","2","3","5"}, nets, group})`.

### 2.2 알고리즘

1. MOS 만 대상(수동·이상원은 레코드에 dc_role 없음 -- 질의 시 `KeyError` 가 아니라 필드 부재). 지원 밖 MOS kind 가 있으면 `mos_kind_unsupported` 정지(GC 4.1 '소비자가 정지'의 소비자가 여기다).
2. (1) `is_diode` -> diode_reference.
3. (2) `gs_groups` 각 묶음: diode 멤버가 있거나 gate 넷이 **모든 뷰에서 교류접지**이면 diode 아닌 멤버 = bias_current_source. 기준이 없으면 멤버 전부 `signal` + status `review_needed`(evidence.group).
4. (3) 남은 소자 중 gate 넷이 모든 뷰에서 교류접지이고 source 넷이 레일이면 bias_current_source.
5. (4) 상속: ratified `structure.json` 의 `equal_vgs`·`matching_ratio`·`kcl_group` 사실만 쓴다. 지금 ratified 사실 0 -> 발동 0. derived 엣지로는 상속하지 않는다 [J-U3-b].
6. (5) 나머지 signal.
- **'모든 뷰에서 교류접지'** = `node.ac_ground_class` 가 `rail` 또는 `gate_only_undriven`(뷰 무관 (1)(2); (3) 전압원은 U2 에서 이미 정지). 바이어스 종속 넷 (4)는 뷰마다 다시 판정되므로 '모든 뷰' 술어에 넣지 않는다 [J-U3-a]. 이렇게 두면 U3 가 U5(뷰)보다 먼저 돌 수 있어 순환이 없다.

### 2.3 실패 규약: `mos_kind_unsupported` 정지만. 기준 없는 묶음은 정지가 아니라 `review_needed` 기록(용어집 그대로).

### 2.4 test 계획

[손] 픽스처: 5T OTA(diode 미러 -> 부하 bias, tail gate 가 gate 전용 넷 -> bias(3)), 전압 구동 CG(gate 바이어스 넷·source 가 신호 넷 -> signal 유지: (3)의 source 조건이 없으면 0 이 되는 회귀 방지), 기준 없는 묶음(두 소자가 신호 넷 gate 공유) -> review_needed, gate 와 source 가 둘 다 레일인 소자.

통합 [JSON] -- 위 2.2 로 9회로를 직접 센 값이 **계획 용어집 91행 실측(diode 28·bias 46·signal 68·못 가르는 묶음 4·그 멤버 10)과 정확히 일치**(원본·정정본 같음):

| 회로 | diode | bias | signal | review_needed 묶음 |
|---|---|---|---|---|
| common_gate | 0 | 2 | 1 | -- |
| current_reuse | 16 | 15 | 20 | -- |
| folded_cascode | 4 | 4 | 5 | -- |
| ngcc_3stage_ff | 3 | 8 | 5 | {M8, M14} |
| nmcnr_amplifier | 2 | 7 | 6 | -- |
| pushpull_follower_buffer | 0 | 2 | 4 | -- |
| sf_pushpull_output_opamp | 1 | 1 | 20 | {M14, M16, M20}, {M6, M9, M17}, {M8, M11} |
| two_stage_ota | 1 | 3 | 3 | -- |
| two_stage_ota_sf | 1 | 4 | 4 | -- |

`gs_groups` 수 [JSON]: 0 / 3 / 3 / 5 / 3 / 0 / 4 / 2 / 2 (위 순서, DS1 6.1 표와 일치). [정정 후 재측정] folded Q1(M1·M2 nmos)은 묶음·역할 불변(입력 gate), 확인만.

---

## 3. U4 -- 관계 엣지와 G_vgs 사이클 (N3.3 엣지 스키마, DEC-64, DEC-17)

### 3.0 엣지 저장 [결정]

GC 예약 (`edge`,`relation`) 단일 writer 대신 **유형별 graph 필드**(writer = 유형별 블록)로 둔다: `graph.rel_<type>` = `RelEdge(type, domain, members, status, evidence{rule, nets})` tuple. 이유: 규칙 C(블록 1 = 파일 1)와 writer 1 을 지키면서 유형마다 독립 reuse. `S1Graph.relations(type=None)` 질의는 이 필드들을 읽기만 한다(소비자: GB7 `writer_plan`). status 는 엔진 규칙만으로 `derived`/`proposed`/`review_needed`. **declared 대조(태그·`vertical_stack_id`)는 S1 밖** U14 대조 블록(선언 사실 지문을 자기 키에 넣음)이 한다 -- S1 키에 태그가 들어가면 IC4(태그 삭제 불변, DS1 test_s1_key (d))가 깨지기 때문.

### 3.1 파일

| 파일(층) | 블록 | reads | writes | domain |
|---|---|---|---|---|
| `rel_vgs.py`(3) | `s1_rel_vgs` | `graph.gs_groups`, `device.{is_diode, pins}`, `node.is_rail` | `graph.rel_equal_vgs`, `graph.rel_vds_eq_vgs` | dc |
| `rel_kcl.py`(4) | `s1_rel_kcl` | `graph.branches` | `graph.rel_kcl_group` | dc |
| `rel_matching.py`(3) | `s1_rel_matching` | `graph.gs_groups`, `device.{kind, pins, element_class}`, `node.is_rail` | `graph.rel_matching_ratio`, `graph.rel_matching_offset`, `graph.rel_l_class` | dc / dc→ss / geom |
| `gvgs_cycles.py`(3) | `s1_gvgs` | `device.{element_class, kind, pins, is_diode}`, `node.{is_rail, port_direction}` | `graph.rel_kvl_branch`, `graph.gvgs_summary` | dc |

`same_as`·`budget_ref` 는 선언 전용 유형이라 U4 가 유도하지 않는다(U14 declared). `stacked_vsb` 는 소비자(GB7 W2) 블록이 생길 때 그 단계에서 만든다(만들면 배선 원칙).

### 3.2 알고리즘

- **equal_vgs**: `gs_groups` 묶음마다 하나(members 이름순, evidence.nets = (gate, source)). **vds_eq_vgs**: diode 마다 하나.
- **kcl_group**: 가지마다 segment 가 2개 이상이면 하나(members = segment 들, 같은 segment 안 병렬 원소는 전류를 나누므로 segment 단위). 옛 `kcl_series_union` 이 못 보던 저항·이상원·gate/커패시터만 더 붙은 넷도 가지 정의가 이미 처리한다.
- **matching_ratio**: gate 가 레일이 아닌 `gs_groups` 묶음(= 진짜 미러; 비율 값은 θ/W 몫). **l_class**: 같은 묶음 -> geom 엣지 status `proposed` [J-U4-a]. **matching_offset**(차동쌍 후보): 같은 kind, 같은 **비레일** source 넷, gate 가 서로 다른 MOS 가 정확히 2개면 `derived`, 3개 이상이면 그 묶음 `review_needed` [J-U4-b].
- **G_vgs**(DEC-64, 용어집 92행): 무향 그래프 G = MOS 마다 (gate, source) 엣지, 모든 레일을 고정 노드 F 하나로 병합. 양 끝이 같아진 엣지 -- 둘 다 레일이면 VGS 가 레일 차로 고정된 소자로 `gvgs_summary.fixed_vgs` 에만 기록, 같은 비레일 넷(g == s)이면 `gvgs_self_edge` 정지(발동 0). 평행 엣지는 v0(= equal_vgs, 이미 기록)이고 대표 하나만 남긴 단순 그래프 Gs 에서:
  - **개수는 기저와 무관한 순환수(cyclomatic number)로 센다**: P = 입력 포트 넷 집합. c(H) = |E| − |V| + 성분 수. v2_0 = c(Gs − P), v2_1 = Σ_p∈P [c(Gs − (P − {p})) − c(Gs − P)], v1 = c(Gs) − v2_0 − v2_1. 이름·순서와 무관(5.3 이 강제).
  - **멤버**(어느 소자 gm_id 가 종속되는지는 GB7 `writer_plan` 몫이고 U4 는 사이클만 기록): Gs − P, 각 p 추가, 전체 순서로 숲을 키우며(F 뿌리 BFS, 이웃 이름순) 새로 생긴 비트리 엣지마다 기본 사이클 1개. 사이클마다 `kvl_branch`(v2, evidence.rule `v2_rail` = F 경유 ΔV = 레일 차 / `v2_zero`) 또는 v1 기록(`port_diff`, 제약 없음, 대조만). 사이클 멤버 합집합 = Gs 의 비다리(non-bridge) 엣지 -- 기저와 무관한 불변량이라 test 가 이것으로 검사한다.
  - **VDS-1**: diode 아닌 MOS 중 drain·source(레일 병합 후)가 서로 다르고 G 의 같은 성분에 있는 소자마다 사이클 1개(그 VDS 엣지 + G 의 경로) = 부등식(포화 하한) 기록. 2개 이상 VDS 엣지 사이클은 기둥 창(W4)이라 기록하지 않는다.

### 3.3 실패 규약: `gvgs_self_edge` 정지. 다른 경우는 기록만(status `review_needed` 포함).

### 3.4 test 계획

[손] 픽스처: 2소자 미러(equal_vgs 1, matching_ratio 1, l_class 1), 레일 gate 전류원 묶음(equal_vgs 는 있음, matching_ratio 없음), 차동쌍 2 vs 공통 source 3소자(review_needed), 직렬 3소자 가지(kcl_group 1, 병렬 segment 포함), class-AB 형 4소자 루프(v2 1), 입력 포트 둘을 지나는 루프(v1 1), 정지 픽스처(g == s).

통합 [계획 DEC-64 측정 기대 = 이번 JSON 직접 계산과 일치]:

| 회로 | G_vgs 순환수 | v2(포트 0 / 포트 1) | v1 | VDS-1 [재측정, J12-c] |
|---|---|---|---|---|
| current_reuse | 5 | 4 / 0 | 1 | 22 |
| pushpull_follower_buffer | 1 | 0 / 1 (입력 포트 vin 하나 -> v2, 계획 예와 같음) | 0 | 0 |
| sf_pushpull_output_opamp | 1 | 1 / 0 | 0 | 0 |
| common_gate·folded·ngcc·nmcnr·two_stage·two_stage_sf | 0 | 0 | 0 | 0 / 1(M10) / 6 / 4 / 1(M4) / 1(M4) |

v2 멤버 [계획]: pushpull {M1, M2, M3, M4}, sf {M18, M19, M21, M22}(멤버 합집합 = 비다리 엣지로 검사). equal_vgs·vds_eq_vgs 수 = gs_groups 수·diode 수([JSON] 2.4 표). matching_offset 은 S6a 5절 '차동쌍 후보' 열(옛 함수 출력)과 **대조 보고만**(기대값 아님). [정정 후 재측정] 정정 5건은 gate-source 연결을 바꾸지 않아 G_vgs 수치 불변(메모리 정정본으로 확인), kcl_group 은 nmcnr 가지 변화를 따라 바뀐다.

---

## 4. U5 -- 교류접지·여기 뷰·셀 분류 준비 (N3.2-1·2·3, 용어집 93행, J1)

### 4.0 S1v 와 필드 권한표

S1v 스냅샷 = S1 스냅샷에 뷰 kind 를 더한 구조 공유 스냅샷(`S1V_WRITERS` = `S1_WRITERS` + 아래), 진입점 `build_s1v(s1, view_decls=None, previous=None)`(`s1v_build.py`, 공개). 키 = (S1Key, view_decls 지문). 지금은 metric 선언 로더가 없어 `view_decls=None` -> 기본 전달 뷰만.

U2~U4 전체 writer 추가표(C2): `s1_dc_conduction`, `s1_branches`, `s1_columns`, `s1_gs_groups`, `s1_dc_roles`, `s1_rel_vgs`, `s1_rel_kcl`, `s1_rel_matching`, `s1_gvgs` -- 어느 것도 `device.bulk`·supplies 를 읽지 않는다. 호출 순서는 `s1_build.py` 가 고정: structure -> bulk -> dc_conduction -> gs_groups -> branches -> dc_roles -> rel_vgs -> rel_matching -> gvgs -> columns -> rel_kcl.

### 4.1 파일

| 파일(층) | 블록 | reads | writes |
|---|---|---|---|
| `symmetry_map.py`(3) | `s1_symmetry` | `device.{kind, pins, element_class}`, `node.{is_rail, port_direction, port_role}` | `graph.symmetry`(넷·소자 대응, 자기대응, 미해결 목록) -- 옛 `find_structural_symmetry_candidates`(SD 2680) 이식, 이름 리터럴 제거·결정론 계약 test 동반 |
| `views.py`(4) | `s1v_views` | `node.{port_direction}`, `graph.symmetry`, extras `(view_decls,)` | `view.{excite, sense, mode}` |
| `view_ac_ground.py`(5) | `s1v_ac_ground` | `view.*`, `node.{ac_ground_class, port_direction}` | `vnode.ac_ground_base` |
| `signal_reach.py`(6) | `s1v_reach` | `vnode.ac_ground_base`, `device.pins`, `device.element_class` | `vnode.signal_r0`(1차 도달성) |
| `bias_dependent.py`(7) | `s1v_bias_dep` | `vnode.{ac_ground_base, signal_r0}`, `device.pins`, `view.*` | `vnode.bias_dependent`, `graph.bias_scc`(DC, 뷰 무관 등록) |
| `forward_path.py`(8) | `s1v_forward` | `vnode.{ac_ground_base, bias_dependent}`, `device.pins`, `view.*` | `vnode.{signal, forward, ac_ground}`(최종) |

### 4.2 알고리즘

1. **기본 전달 뷰**(N3.2-2): 입력 포트 2개가 `graph.symmetry` 에서 서로 대응이면 기모드 여기 1개, 아니면 입력 포트마다 단일 여기 1개. 감지 = 출력 포트 전부. 전류 입력·트랜스임피던스 뷰는 `transfer_view_current_excite` 정지(기록만 분기 DEC-59를 엔진에서는 정지로, 발동 0). 루프 뷰는 R14 단계(이번 범위 밖).
2. **뷰 교류접지 기초** = 정적 (1)(2) ∪ 그 뷰에서 여기되지 않는 입력 포트(N3.2-2 '선언된 여기원 밖 독립원은 교류접지').
3. **최소 고정점 도달성 R0**: 여기 넷에서 시작해 (a) 신호 넷을 gate 로 받는 MOS 의 d·s (b) 신호 넷을 source 로 받는 MOS 의 d (c) 신호 넷에 붙은 수동소자 반대 단자를 더한다. 교류접지·여기 제거 넷은 넣지 않는다. 작업 큐(각 넷 한 번 방문), 반복 재계산 없음.
4. **바이어스 종속 넷**(N3.2-1 (4) (0)(i)(ii)(iii), 사슬 = source -> drain 방향, 교류접지·b 비통과): 후보 판정은 R0 위에서 한 번, (iii)의 'b 를 뺀 그래프에서도 신호 넷'은 후보마다 b 를 뺀 도달성을 한 번 더(후보 수만큼, 9회로 후보 총 2). 출발 신호 노드가 그 뷰의 여기로 움직이지 않으면(대칭 축약 자기대응 넷) 그 뷰의 교류접지. DC 바이어스 SCC 는 뷰와 무관하게 `graph.bias_scc` 에 등록(GB7 순환 블록 입력).
5. **최종**: 교류접지 = 기초 ∪ 그 뷰의 바이어스 종속 넷, 그 위에서 도달성 한 번 더 -> `signal`, 순방향 = 여기에서 도달 ∩ 출력 포트로 역도달(같은 최소 고정점 그래프, 규칙 2 방향 그래프 사용 금지).
6. **셀 분류 준비**(R9 는 다음 단계): R9 가 읽을 입력은 위 `vnode.{signal, forward, ac_ground}` + U3 `dc_role` + `device.is_diode` 가 전부다. 이번 단계는 셀을 쓰지 않는다.

### 4.3 실패 규약: `transfer_view_current_excite`, 이상 전압원(U2 에서 이미 정지), 대칭 대응 충돌(`symmetry_conflict` -- 한 넷이 두 넷에 대응, 9회로 중 folded 1건 실측(S6a 5절) -> 정지가 아니라 `graph.symmetry` 의 미해결로 기록하고 그 뷰는 단일 여기로 떨어진다 [J5]).

### 4.4 test 계획

[ratified J1] 바이어스 종속 넷: 파일럿 2건, 나머지 8회로 0 -- 유일한 ratified 기대값. [손] common_gate·pushpull·two_stage_ota 신호 넷 집합(follower 회로에서 빈 집합이 아님 -- 옛 `signal_path_nodes` 결함 회귀 방지, S6a 5절 관찰 1). [손] 입력 포트인 gate 전용 넷은 정적 교류접지 아님. [계획] 기본 전달 뷰: 차동 입력 7회로 중 대칭 대응이 확인되는 회로 = 기모드 1뷰, 단일 입력 2회로(common_gate·pushpull) = 단일 여기 1뷰 -- 회로별 대응 확인 여부는 [J5] 재측정. [정정 후 재측정] nmcnr·two_stage(수동소자 추가 -> (c) 엣지 추가로 신호 넷 증가), folded(CL).

---

## 5. 공통 test (구조·일반성)

### 5.1 재사용·결정론 (확정 사항 5)
- 같은 doc·supplies 로 `previous` 넘김 -> 같은 객체, 전 블록 compute 0. supplies 만 변경 -> `s1_bulk` 만 compute, U2~U4 블록 reuse(stats). `previous` 없이 두 번 -> `recomputes_same_input` 증가(정상 파이프라인 기대 0).
- 블록 결과는 setter(`@compute_block` writes)로만, writer 둘이면 FAIL(core 강제), 모듈 dict·lru_cache lint 0.
- 엔진 소스 문자열 상수 ∩ 9회로 넷·소자 이름 = ∅(`test_no_name_literals`), `topology_name`·`compensation` 문자열이 graph 패키지에 없음(AST).

### 5.2 정지 분기 실재 확인
1.3·2.3·3.3·4.3 의 정지 분기마다 '실제로 정지(예외·rule_branch·devices)' 픽스처 1개 이상, 9회로 원본은 정지 0(오정지 0).

### 5.3 library 밖 합성 topology -- metamorphic test (`tests/integration/test_structure_metamorphic.py`)

기반 픽스처(손으로 작성, 이름은 무의미 기호 `x1`, `n3` 등): T1 5T OTA, T2 telescopic 캐스코드(이상 전류원 tail), T3 class-AB 출력 루프(4소자 G_vgs v2), T4 저항 자기바이어스 + Miller RC(잎 가지치기·v2 없음), T5 3레일(중간 레일에 커패시터만). 각 기반의 기대값은 [손](가지·기둥·역할·순환수).

| 변형 | 판정(기대 관계) |
|---|---|
| 이름 바꾸기(넷·원소 전단사, 시드 고정 여러 개) | 모든 개수(분기 노드·가지·기둥·병기값·역할별 수·review 묶음 수·v0/v1/v2/VDS-1·신호 넷 수) 동일, 이름 사상 아래 집합 동일. 이름 tie-break 로 고른 대표(사이클 멤버 등)는 불변량(비다리 엣지 합집합)으로만 비교 |
| netlist·passive 순서 섞기, `PYTHONHASHSEED` 1~5 | 스냅샷 `fp` 동일 |
| n/p 극성 + 레일 뒤집기(nmos↔pmos, 최저↔최고 레일 교환, supplies 부호 반전) | U2~U4 개수·역할 동일, bulk 는 뒤집힌 레일로(GC 4.2 원점 이동 불변 test 와 함께) |
| 단 복제(같은 레일을 공유하는 서로소 사본 2개) | 가지·기둥·역할·gs 묶음·순환수 = 정확히 2배(레일 공유는 가지를 합치지 않음), 분기 노드 2배 |
| 직렬 연결(사본1 출력 포트 넷 = 사본2 입력 gate 넷, 사본2 입력 포트 선언 제거) | DC 구조(가지·기둥) = 합(gate 는 DC 엣지 아님), 역할 = 합(연결 넷이 drain 을 가져 정적 교류접지 아님 -- 사전 손확인), G_vgs 순환수 = 합, v1 은 사본2 몫이 v2 로 이동(입력 포트 감소) -- 손계산으로 이동 수 기대 |
| 미지원 구조 주입(인덕터, 전압원, 4번째 MOS kind, g == s, 기둥 상한 초과) | 해당 `rule_branch` 로 정지(특수 처리 없음) |

판정 결과는 케이스마다 파일에 append(중간 실패에도 보존). 이 test 가 9회로에 없는 구조에서 **무동작 또는 정지**만 일어남을 측정한다(일반성 증거).

---

## 6. 사용자 공동분석(J) 항목 -- 근거와 기본안

| # | 항목(영역) | 근거(실측) | 기본안 |
|---|---|---|---|
| J13-a | (DC) 병렬 합침 범위: 종류가 다른 병렬(MOS ∥ 저항)도 한 segment 인가 | 정정 후 nmcnr RL(Vout–vss) ∥ M301 -> 따로 10 / 합침 9 | 같은 넷 쌍이면 종류 무관 합침(KVL 같음, 전류는 KCL 분배) |
| J13-b | (DC) 잎 가지치기를 열거 전에 하는 순서와 회로별 결과 | 잘림: 파일럿 Rz1·Rz2, 정정 후 two_stage Rz·nmcnr Rm. 파일럿 R1/R2 는 남음(θ) | DEC-70 그대로(열거 전 가지치기) |
| J13-c | (DC) 3레일 회로에서 어느 레일 쌍을 DC 경로로 보나 | pushpull·sf: agnd 쌍 기둥 0, vss–vdd 만 | 모든 쌍 열거, 0 인 쌍은 기록만(정지 아님) |
| J13-d | (DC) 이상 전류원 가지의 전압 강하 = 기둥 KVL 자유 변수(W4) | 파일럿 Iref, folded·sf IBias 가지 | 자유 변수(GB7 U8 와 같은 안) |
| J13-e | (DC) 기둥 정본 41 vs 손선언 `vertical_stack_id` 대조 | 파일럿 41/62, 가지 27/32, 분기 7/9 | 대조는 U14 shadow 보고(S1 status 는 규칙만) |
| J-U3-a | (DC 역할) '모든 뷰에서 교류접지' = 뷰 무관 (1)(2)만 | 이 정의로 9회로 28/46/68·묶음 4·멤버 10 이 계획 실측과 정확히 일치 | 그대로. (4) 바이어스 종속 넷은 넣지 않음 |
| J-U3-b | (DC 역할) (4) 상속을 derived `kcl_group` 으로 할지 | derived kcl_group 으로 상속하면 바이어스 전류원과 직렬인 캐스코드(CG 신호 소자)가 바이어스가 됨 | ratified 사실만(지금 발동 0) |
| J-U3-c | (DC 역할) 구조로 못 가르는 묶음 4개 | ngcc {M8, M14}, sf {M14, M16, M20}·{M6, M9, M17}·{M8, M11} | review_needed + 잠정 signal. J12-d 가 다루지 않는 묶음은 6a 신설 J 로 회로별 ratify |
| J-U4-a | (geom) 미러 묶음 = L 동치류(proposed) | 옛 L류: 연결만 3 vs 선언 포함 15(파일럿) | gate 비레일 gs 묶음만 l_class proposed, 선언분은 U14 대조 |
| J-U4-b | (dc→ss) 차동쌍 후보 규칙(같은 kind·공통 비레일 source·다른 gate 정확히 2) | 파일럿 후보에 CMFB 쌍(M37a/M37b) 포함, J4(M7 tail/CMFB) 관련 | derived, 3개 이상 공통 source 는 review_needed. **[개정 2026-10-07 Q8 (i)(iii), 계획 DEC-93 (1)·J14]** 바이어스 형제(gate가 모든 뷰 교류접지이거나 DC 역할이 바이어스 전류원·diode 구동)를 먼저 빼고 남은 신호 gate 멤버가 정확히 둘(둘 다 diode 아님)이면 derived -- DC 역할·뷰를 matching보다 먼저 계산. role 어휘 {diff_pair, mirror, branch_symmetric(확정 쌍 위 같은 kind 채널 stack 전파), bias_distribution, feedback_shared} + evidence + status, 레이아웃엔 앞 셋의 derived·ratified만. 9회로 결과는 계획 J14로 ratify |
| J12-c | (DC) G_vgs 판독: v1(파일럿 {M1a, M1b, M4a, M4b}) 제약 제외, v2 4 의 J3 루프 대응, **VDS-1 실측 22/1/6/4/0/0/1/1** 이 전부 의도한 포화 부등식인지 | 3.4 표(이번 재측정, 계획 '정확히 하나 포함' 정의) | 계획 DEC-64 그대로, VDS-1 목록을 회로별 대조표로 |
| J12-f | (DC) kvl_branch 종속 멤버 선택 | U4 는 사이클만 기록, 선택은 GB7 | ~~DEC-64 기본(ratified 없으면 이름 정렬 첫 멤버) -- 이름 tie-break 이므로 metamorphic test 는 개수만 비교~~ **[개정 2026-10-07 Q10 (v), 계획 DEC-64·DEC-95 (3)]** ratified 없으면 diode → GB5 gm 요구·뒤 stage 소자 독립 유지 → 대칭 궤도 대표 → 이름. metamorphic test는 '이름 전단사 후 front 정규화 해시(이름 사상 적용) 동일'까지 본다 |
| J5 | (AC구조) 대칭 미해결·충돌 시 기본 전달 뷰 | S6a 5절: 단일출력 미러 부하 회로 미해결 다수, folded 충돌 1 | 충돌·미해결이 입력 포트 대응을 막으면 입력마다 단일 여기 뷰 |
| J1 | (AC구조) 바이어스 종속 넷 | ratified(파일럿 2, 나머지 0) | 추가 질문 없음 |

## 7. 열린 설계 결정 (회로 해석 아님 -- 오케스트레이터 확정 대상)

- O1 **기둥 열거 상한 출처**: DEC-34 는 실측 시간 기반 예산(spec `wall_clock_budget_s`)이라 S1(spec 무관 키)에 넣으면 결정론·키가 흔들린다. 기본안: `column_limit` 를 `build_s1` 인자로 받고 S1Key 에 넣지 않으며, 초과 시 정지(정지 결과는 캐시하지 않음). 9회로 최대 62(따로)라 발동 0.
- O2 core `GraphSnapshot` 레코드 key 가 tuple 을 받는지(`vnode` key = (view_id, net)) -- 안 되면 정준 문자열 인코딩 helper 를 core 에 둔다.
- O3 `symmetry_map.py` 이식 범위(옛 SD 2680 의 seed·충돌 규칙)는 이식 card 에서 옛 함수 출력과 9회로 대조로 정한다.
