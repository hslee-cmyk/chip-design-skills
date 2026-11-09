# 6a 구조 유도 준비 -- 새 엔진 기준(S1 그래프 우선)

- 작성 2026-10-07. 기준: clone `gmid-light` 브랜치 `phase3-light` cb0ef86(계획서 `docs/01-plan/features/gain-budget-gmid-sizing.plan.md` 1193행 -- 메인 master 6df4bd7과 바이트 동일).
- 실측: 격리 복제본 `/c/g458/repo`(cb0ef86)에서만. 원자료(스크립트·jsonl)는 이 문서 옆 `6a_prep_raw/`로 복사했다.
- **전제(오케스트레이터 지시 2026-10-07)**: 옛 엔진(`sizing_recipe.py`·`stick_diagram.py`)은 참고용이다. 계획서 아키텍처로 새 패키지를 짓고 그 첫 모듈이 S1 그래프다. 옛 함수 분류는 **이식 후보(검증된 로직, 옮길 때 계약 test 필요) / 참고만 / 버림**으로 쓴다. 새 엔진은 역할 태그를 처음부터 읽지 않는다.
- 회로 원리 해석은 하지 않았다. 해석이 필요한 칸은 **[J대상 Jn]**으로 표시했다.
- 착수 조건 확인: `6a-structure-stage` design 문서가 `docs/02-design/features/`에 **없다**(00-common·05·10·20·30만 있음). DEC-51(계획 N6.1 993행) 때문에 구현 card 전에 design 승인이 필요하다. 아래 1~6절은 그 design의 입력 초안이다.

---

## 1. S1 그래프 설계 (새 패키지 첫 모듈)

### 1.1 현황

- 통합 그래프 클래스가 없다. `stick_diagram.StackGraph`(SD 5198)는 Euler 레이아웃 전용이고, 구조 함수들은 `list[Transistor]`나 `by_name`을 각자 순회한다(아래 1.4 표의 함수 18개가 모두 그렇다).
- `Transistor`(SD 48)에는 bulk가 없고, 수동소자·이상원은 `meta`에 따로 있다. 그래서 `signal_path_nodes`(SR 3886)·`kcl_series_union`·`trace_*`가 수동소자를 보지 못한다.
- `load_topology`(SD 8569)는 로드할 때 역할 태그를 자동으로 채운다(`propose_vertical_stack_id_gap_fill`, `propose_device_roles_gap_fill`의 충돌 없는 제안 병합, SD 8668~8763). 실측: 스펙 미선언 5회로에서 태그가 **새로 생긴다**(ngcc 13, sf_pushpull 22, two_stage_ota_sf 9, common_gate 3, pushpull 2개 소자). **새 엔진은 이 로더를 쓰지 않는다.** 이 로더를 쓰면 태그 없는 유도라는 6a 전제가 로드 단계에서 깨진다(IC4, 계획 824행).

### 1.2 데이터 구조 (필드는 N3.3 364행 그대로)

목적지 = MOD3 `circuit_state_graph.py`(N3.10 528행). 새 패키지에서는 이 모듈을 첫 모듈로 두고, MOD2 `topology_authoring`(로드 게이트)만 아래 번호로 둔다.

```
S1Graph (frozen; 생성 후 불변)
  key: S1Key {topology_hash, rule_hash, supplies_v_hash}      # N3.3 364행 '키' 칸
  nodes: {name: Node}
    Node {name, terminals: tuple[(element, terminal)], is_rail: bool,   # is_rail = supply_nets(DEC-60), DC
          ac_ground_class: None | "rail" | "gate_only_undriven" | "ideal_vsrc"   # 뷰 무관 3분류(규칙 1 (1)~(3)), AC구조
          port_role: None | "input" | "output"}
          # 규칙 1 (4) 바이어스 종속 넷은 뷰 속성 -> S1이 아니라 S1v에 둔다(339행 '교류접지는 뷰 속성')
  devices: {name: Device}
    Device {name, kind, d, g, s, b,          # b = 선언 bulk 또는 DEC-61 기본 레일(nmos 최저/pmos 최고 전위)
            is_diode: bool,                   # g == d
            dc_role: "bias_current_source" | "diode_reference" | "signal" | "review_needed"}  # 용어집 87행
  passives: {name: Passive {name, kind, terminals}}      # topology 이름 그대로
  sources:  {name: Source {name, kind, terminals, value}}  # ideal_sources (이상원 = 가지 표시용, DEC-71(1))
  edges: tuple[RelEdge]
    RelEdge {type, domain, members, status, evidence{rule, nets}}
      type ∈ equal_vgs | vds_eq_vgs | same_as | budget_ref | stacked_vsb | matching_offset |
             matching_ratio | l_class | kcl_group | kvl_branch
      domain: dc = equal_vgs·vds_eq_vgs·budget_ref·stacked_vsb·matching_ratio·kcl_group·kvl_branch,
              geom = same_as·l_class, dc→ss = matching_offset          # 364행
      status ∈ declared | derived | proposed | review_needed | ratified  # 370~378행 전이표
  branches: tuple[Branch {id, ends:(node,node), devices_in_order, has_ideal_source}]
  columns:  tuple[Column {id, rail_lo, rail_hi, branch_order, status}]
  column_block_map: 비어 있음(S1v 확정 뒤 채운다 -- 364행 '매핑은 S1v 확정 뒤')
```

- status 전이(374~378행)는 `S1Graph`가 아니라 별도 함수 `transition(edge, to, by, approval_id)`로만 한다. 엔진이 쓸 수 있는 전이는 생성→declared/derived/proposed, derived/proposed→review_needed, ratified→review_needed(해시 변경)뿐이다. review_needed→ratified는 오케스트레이터가 `library/<name>.structure.json`(ratified 사실만, 364행 스키마)으로만 들여온다.
- 선언 필드(`device_roles.same_as_device`, `budget_reference_device`, `symmetry.matching_pairs`)는 **status=declared 관계 엣지로만** 싣는다. 유도 규칙의 입력으로 쓰지 않고, derived 결과와 대조할 때만 쓴다(DEC-44 238행, IC8 828행). `headroom_role`·`gm_id_role`·`L_role`·`vertical_stack_id`·`fold_group`·`sizing_roles.metrics.stages`는 **싣지 않는다**(`vertical_stack_id`만 J13 대조용 declared 표로 따로 읽는다, DEC-71 265행).

### 1.3 생성 함수와 캐시

- `build_s1(topology: dict, supplies_v: dict | None, rule_hash: str) -> S1Graph`. 입력은 JSON dict이고 파일을 읽지 않는다. 파일 읽기와 GB0 로드 게이트(supply_nets 필수, 숨은 레일 (iii), ports, 3레일 supplies_v -- DEC-60 254행)는 MOD2 `load_and_gate(path)`가 먼저 한 번 하고 dict를 넘긴다. `linked_topology_files` 합치기 규칙은 옛 `load_topology`에서 이식한다.
- 캐시: 키 = S1Key(topology 정규화 JSON 해시 + 유도 규칙 코드 해시 + supplies_v 해시, 363~364행). 상한이 있는 dict 캐시(N3.5 LRU 규칙). S0 지문 계산 함수는 같은 모듈에 둔다(363행 '유도 규칙 코드 해시 = S1 유도 함수 호출 폐포의 ast.dump').
- 파생 질의(차수·단자 목록·gate-source 그룹·DC 전도 그래프)는 `S1Graph` 생성 때 한 번 인덱스로 만든다(`by_net_terminal`, `gs_groups`, `channel_adj`). 규칙 함수가 transistor 리스트를 다시 순회하지 않는다(재계산 금지 원칙).
- 질의 API(최소): `devices_at(net, terminal=None)`, `degree(net)`, `rails()`, `diodes()`, `gs_groups()`(같은 (kind, g, s)), `channel_edges()`, `dc_conduction_graph(prune_leaves: bool)`(DEC-71(1)·DEC-60(iii) -- 가지치기 전/후 둘 다), `gate_only_nets()`.

### 1.4 옛 함수 → S1 그래프 질의 매핑 (이식 후보 / 참고만 / 버림)

호출 수는 격리 복제본 grep(엔진 파일 기준, 주석·docstring 제외 근사).

| 옛 함수(파일:행) | 새 자리 | 분류 | 근거·옮길 때 필요한 계약 test |
|---|---|---|---|
| `is_diode_connected`(SR 3125) | `Device.is_diode` | 이식 후보 | 식 `g == d` 하나. test: 9회로 diode 수 = JSON 직접 집계(1.5 표) |
| `true_current_mirror_groups`(SR 2191) | `gs_groups()` + DC 역할 (2) 입력 | 이식 후보 | 키 (kind, gate, source), gate가 레일이면 제외, 레일은 `rails.nets`(B26-1 뒤 이름 리터럴 없음). 실측 1.6 표. test: 손계산 그룹 |
| `l_sharing_classes`(SR 2217) | `l_class` 엣지(derived) | 참고만(일부 이식) | union-find 중 (a) 미러 엣지만 유도 규칙이다. (b) `same_as_device`·(c) `matching_pairs`는 선언 입력이라 새 엔진에서는 declared 엣지 대조로 분리한다. 실측: 선언 포함/제외 결과가 다르다(파일럿 15류 vs 3류) |
| `l_class_owners`·`gain_stage_tails`(SR 2329·2273) | DEC-17 주인(212행) | 버림 | tail을 `headroom_role=="tail"`, stage를 `gain_stages_sum.stages`로 읽는다. 새 엔진은 DC 역할 tail + GB2 stage로 다시 정한다 |
| `vgs_alias_map`(SR 1637) | `equal_vgs` 엣지(DEC-64 v0) | 버림 | 전부 선언(`gm_id_match_vgs_of`)을 읽는다. 연결로 유도되는 같은 사실은 `gs_groups()`가 낸다 |
| `signal_path_nodes`(SR 3886) | 규칙 3 최소 고정점 도달성 | 참고만 | 엣지가 gate→drain·source→drain뿐이다. gate→source(CD)·수동소자 단자가 없어 follower 출력 회로에서 **빈 집합**(실측: pushpull, sf_pushpull, two_stage_ota_sf 0개). 규칙 3(344행)의 (a)(b)(c) 정의로 새로 쓴다 |
| `_kcl_and_matching_edges`(SD 3117)·`kcl_series_union`(SD 2997) | `kcl_group` 엣지 | 이식 후보(내부 2단자 넷 부분만) | 레일 아닌 넷이 채널 단자 2개뿐이면 같은 전류. 선언 `matching_pairs` 엣지 부분은 버린다. 수동소자를 세지 않는 한계를 계약 test에 넣는다(저항이 낀 넷) |
| `trace_vdd_to_gnd_branches`·`trace_gnd_to_vdd_branches`(SD 1183·1235) | 가지·기둥(DEC-71(1)) | 버림 | 시작점이 `"vdd"`/`"gnd"` 리터럴, 종료가 `_RAIL_NETS={"vdd","gnd","vss"}`(SD 2977). 실측: vss 레일 3회로(nmcnr·pushpull·sf_pushpull)에서 상향 가지 0개. 수동소자·이상원 무시. DC 전도 그래프의 단순 경로 열거로 새로 쓴다 |
| `find_structural_symmetry_candidates`(SD 2680) | 대칭 축약(345행), 기본 전달 뷰(341행) | 이식 후보 | 계획이 이 함수를 이름으로 지정한다. 실측 1.6 표(단일출력 미러 부하에서 unresolved 다수). test: 파일럿 16쌍 손확인 [J대상 J5·J12] |
| `find_matching_candidates`(SD 945) | 미러/차동쌍 후보(J12 대조) | 참고만 | 계획 1060행이 J12 대조 입력으로 그 출력을 인용한다. 새 엔진 규칙 입력은 아니다 |
| `find_differential_pair_candidates`·`_diff_pair_layer1_groups`(SD 1500·1607) | diffpair DC 역할·tail(DEC-17) | 참고만 | branch tree 경로는 `trace_*`(이름 리터럴)에 기댄다. layer1(같은 kind + 비레일 공통 source + 다른 gate, 정확히 2개)만 이식 가치 |
| `propagate_topology_forced_currents`(SD 2849) | 6b KCL 가지 전류(S2 dc) | 참고만 | 6a 범위 밖 |
| `propagate_node_voltages`(SR 3733) | 6b W 티어 | 참고만 | 기본 인자가 이름 리터럴 레일(레지스트리 §2) |
| `find_hub_merge_candidates`(SD 2635), netclass 계열(`find_idiom_matches` SD 1061, `_propose_*_roles` SD 1808~2194, `refine_differential_and_mirror_relations` SD 2314) | -- | 버림 | analog-grammar netclass 분류(INPUT/BIAS)와 역할 제안이다. 새 엔진에서는 ports + 교류접지 집합 + 도달성이 대체 |
| `propose_*_gap_fill`, `require_device_roles_reviewed`, `audit_vertical_stack_id_vs_kcl`(SD 3142~4763) | -- | 버림 | 태그를 만들거나 검사하는 도구다 |
| `load_topology`(SD 8569) | MOD2 `load_and_gate` + `build_s1` | 이식 후보(로드 부분만) | `rail_declaration`(SD 8541, B26-1), linked 파일 합치기, IC3 이름 유일성은 옮긴다. gap-fill 병합은 버린다 |

### 1.5 그래프 자체 test (독립 기대값)

test 기대값은 test-author가 **topology JSON을 직접 집계해** 만든다(피검 `build_s1`을 부르지 않는다, N3.12). 집계 대상: 소자 수(nmos/pmos), 수동소자 수(R/C), 이상원 수, 넷 수(모든 단자 합집합), 넷별 차수(채널 3단자 + 수동 2단자 + 이상원 2단자), 레일 집합 = `supply_nets`, diode 수(`gate == drain`), gate 단자만 붙은 넷 목록.

아래는 **작성자 측 교차 확인 실측**이다(JSON 직접 집계, 엔진 코드 미사용). 정본 기대값이 아니며 test-author 결과와 대조하는 용도로만 쓴다(작성자≠검증자).

| 회로 | nmos/pmos | R/C | Isrc/Vsrc | 넷 | MOS 단자 | 수동 단자 | 원 단자 | bulk 선언 | 레일 | diode | 최대 차수(넷) | gate 전용 넷 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 2/1 | 0/0 | 0/0 | 7 | 9 | 0 | 0 | 0 | vdd, gnd | 0 | 2 (vout) | VNBias1, VNBias2, VPBias1 |
| current_reuse_telescopic_ota | 24/27 | 4/8 | 1/0 | 37 | 153 | 24 | 2 | 0 | vdd, gnd | 16 | 19 (gnd) | 없음 |
| folded_cascode | 6/7 | 0/0 | 1/0 | 14 | 39 | 0 | 2 | 0 | vdd, gnd | 4 (M7, M9, MN, MP) | 5 (vb1) | bias3, vin_n, vin_p |
| ngcc_3stage_ff | 9/7 | 0/3 | 0/0 | 13 | 48 | 6 | 0 | 0 | vdd, gnd | 3 (M3, M6A, M9) | 10 (gnd) | VBN, VBP, Vinn, Vinp |
| nmcnr_amplifier | 7/8 | 0/0 | 0/0 | 17 | 45 | 0 | 0 | 0 | vdd, vss | 2 (M108, M203) | 6 (vdd) | VB1~VB5, Vin_n, Vin_p |
| pushpull_follower_buffer | 3/3 | 0/1 | 0/0 | 9 | 18 | 2 | 0 | 0 | vdd, vss, agnd | 0 | 3 (vss) | VNB1, VPB1, vin |
| sf_pushpull_output_opamp | 11/11 | 3/2 | 1/0 | 23 | 66 | 10 | 2 | 0 | vdd, vss, agnd | 1 (M4) | 8 (vdd) | vin_n, vin_p |
| two_stage_ota | 4/3 | 0/0 | 0/0 | 9 | 21 | 0 | 0 | 0 | vdd, gnd | 1 (M3) | 4 (D3) | bias, vin_n, vin_p |
| two_stage_ota_sf | 6/3 | 0/2 | 0/0 | 10 | 27 | 4 | 0 | 0 | vdd, gnd | 1 (M3) | 4 (vdd) | bias, vin_n, vin_p |

관찰(판단 아님): 9회로 모두 `bulk` 선언 0 → DEC-61 기본 레일 규칙만 발동한다. `nmcnr`·`two_stage_ota`는 수동소자 0(J9 `passive_elements` 누락 후보, 계획 1057행). pushpull·sf_pushpull의 `agnd`는 레일 선언에 들어 있다(DEC-60 (iii) 9/9 통과 상태와 맞음).

그래프 test 추가 항목: (a) 같은 dict 두 번 → 같은 키·같은 객체(캐시) (b) 넷 하나 이름을 바꾸면 키가 바뀐다 (c) `supply_nets`에서 한 넷을 빼면 MOD2 게이트가 거부한다(공격 14 (b), DEC-60 254행) (d) 태그 필드(`device_roles` 전부)를 지운 JSON과 원본의 `build_s1` 결과에서 derived 부분이 같다(IC4의 S1 몫, 824행).

### 1.6 S2 `dc`가 S1 위에 올라가는 인터페이스 (6b GB7, 구현은 6b)

- S2는 S1을 바꾸지 않는다. `S2DC`는 `S1Key`를 들고 S1의 노드·소자·가지 id를 키로 값을 단다(DEC-67 261행: 노드전압·전류 정본은 DC).
```
S2DC {s1_key, version: int,
      node_v: {node: NodeV{value, writer_tier ∈ W0..W4, writer_id, version}},   # 노드당 writer 하나(N3.4 382~397행)
      path_values: {node: [(path_id, value)]}, conflicts: [...],               # 366행 '경로별 값·충돌'
      branch_i: {branch_id: BranchI{value, source ∈ KCL|declared|theta, version}},   # 가지 전류 정본
      device_op: {device: {ID, gm_id, L, W, VGS, VDS, VSB}},  # VGS/VDS/VSB는 node_v의 읽기 전용 파생
      column_window: {column_id: {slack, ...}}}
```
- W 티어가 S1에서 읽는 것: W0 = `Node.is_rail` + `supplies_v`, W1 = `vds_eq_vgs`(diode)·`budget_ref` 엣지, W2 = `stacked_vsb`·`kvl_branch` 엣지 + CD 셀 source 노드(S1v), W3 = spec 선언, W4 = 기둥 내부 노드(`columns`).
- 봉인(N3.6)은 `S2DC.s1_key == 현재 S1Key`와 writer 유일성을 확인한다. `ss`·`ls`는 봉인 통과 `S2DC.version`을 입력 카운터로 기록한다(366행).

---

## 2. 6a 규칙 목록 (입력·출력·완료 판정)

행 번호 = 계획서 줄. 영역 표기는 DEC-67.

| # | 규칙 | 계획 행 | 입력 | 출력(S1/S1v) | 완료 판정 |
|---|---|---|---|---|---|
| R0 | GB0 로드 게이트: `supply_nets` 필수·숨은 레일 (iii)·3레일/음전위 `supplies_v`·ports·MG2 옛 키 거부 | 314, DEC-60 254, DEC-61 255 | topology JSON, spec | 거부 또는 검증된 dict | 9/9 통과·오거부 0, 공격 13·14 (a)(b) 거부 로그, IC11 3레일 케이스(1023행) |
| R1 | S0 지문 + S1 그래프 | 363~364 | 검증된 dict, LUT 메타, spec | S1Graph, S1Key | 1.5 test |
| R2 | 소자 DC 역할 (1)~(5) | 용어집 87, DEC-57 251 | S1(diode, gs_groups, 교류접지 3분류, 레일) | `Device.dc_role`(기준 없음 → review_needed) | ratified 대조표 일치. 지금 기대값 출처: 손계산 |
| R3 | 미러·`equal_vgs`(v0)·`kcl_group`·`l_class`(derived), diffpair·tail(DC), L 동치류 주인 | 315, DEC-17 212, DEC-64 258 | S1 | 관계 엣지(domain 포함) | 엣지 전부 domain 보유(1023행), declared 대조 불일치 → review_needed |
| R4 | G_vgs 사이클 분류 v0/v1/v2/VDS-1 | DEC-64 258, DEC-27 222, 용어집 88 | S1(gate-source 무향 엣지 + 레일 병합), ports | `kvl_branch` 엣지, v1 목록, VDS-1 수 | 기대(측정 기대, J12-c 대상): 파일럿 v2 4·v1 1, pushpull v2 1 {M1~M4}, sf_pushpull v2 1 {M18, M19, M21, M22}, 나머지 0. VDS-1 사이클 수는 '정확히 하나 포함'을 정본으로(356행 (vi)) |
| R5 | 가지·기둥(DC 전도 그래프, 레일 쌍별 노드-단순 경로) + `vertical_stack_id` 대조 | DEC-71 265 (1), J13 1070 | S1(채널·잎 가지치기 뒤 저항, 이상원 가지 표시) | branches, columns, review_needed | 파일럿 62 = 가지 32·비레일 분기 노드 9(정본, 265행), 나머지 3~9, 병렬 소자 합침 시 41 병기(열린 항목), 어느 쌍에도 안 드는 가지 보고 |
| R6 | 교류접지 집합 (1)~(3) + 여기 뷰 수집(전달 뷰 기본·metric 선언) | 339, 341 | S1, ports, metric 선언 | 뷰 목록, 뷰별 교류접지 | 스펙 미선언 회로는 기본 전달 뷰(341행). `find_structural_symmetry_candidates` 대응 확인 |
| R7 | 신호 경로 최소 고정점 도달성 + 순방향 경로 | 344 | 뷰, 교류접지 | 뷰별 신호 넷, 순방향 넷 집합 | 규칙 2 방향 그래프를 쓰지 않을 것(순환 금지, 344행) |
| R8 | 규칙 1 (4) 바이어스 종속 넷 술어(뷰별) + DC 바이어스 SCC | 339, J1 1049 | R7 결과 | 뷰별 추가 교류접지, 루프 뷰 등록 후보 | **J1 ratified**: 파일럿 2건, 나머지 8회로 무동작 -- 유일하게 ratified된 기대값 |
| R9 | 셀 분류 CS/CG/CD/pass/`diode(load)`, 역병렬 pass 묶음, 이중 출력 review, 3소자 이상 pass review | 344, 용어집 91, DEC-57 251 | R7·R8 | 뷰별 셀, CG/pass 판별 근거, 순방향 밖 셀 목록 | 측정 기대: 기존 4회로 CG 8(파일럿 M2a/M2b/M3a/M3b·folded 2·nmcnr 2), 파일럿 pass 묶음 2(M9a/M9b, M18a/M18b), common_gate 전압 구동 CG 1 [J12-i] (350·353·1023행) |
| R10 | 입력 노드 구동 종류(전압/전류/tap/값 의존, 우선순위·혼재·pass 상속) | 용어집 92, 91 | R9 | 뷰별 노드 구동 종류 | 신호 넷 중 구동 종류 미정의 0 [J12-b] |
| R11 | 엣지 비용 0-1 BFS(수동소자 비용 = 6a design 결정) | 348 | R9·R10 | 뷰별 거리 | 수동소자 엣지 비용 미정 -- **6a design이 정해야 R14 (3-b)·(4) 수가 정해진다**(1023행: 비용 0·1에서 파일럿 (4) 7 대 3) |
| R12 | stage 경계(구동 종류 하나), 바이어스 전류원 stage 시작 예외, 블록 구성(노드 배타), 출력노드, 임피던스 등급, 극점 노드 목록 | 349~354 | R9~R11, R2 | signal stage, 블록, 극점 노드 | 기존 4회로 input·cascode·tail = declared 100%(`probe_stage_partition.result.md`), 대칭 반쪽 공유 넷 처리는 design이 정함(354행 ⚠️) |
| R13 | 규칙 9 (a)(b)(c) + diode 미러 갈래 | 357 | R12, ports | `기록만` 분기 | 사이징 대상 회로 셀 review_needed 0(1023행) [J2] |
| R14 | 루프 뷰: 방향 신호 그래프, 단순 사이클 전수(2단자 수동 왕복 제외), (0)~(4)·(1.5)·(3-a)/(3-b)·배타 (가)(나), 끊는 점, 극성 | 342, 355 | R7~R12 | 루프 목록·분류·끊는 점·극성 | 기본 폐경로 수를 확정 정의로 **재측정**(옛 기대 36/18/1/0 대 측정 23/13/1/1, 342행). 사이징 대상 회로 `기록만` 발동 총합 0(1023행) [J11·J12-h·J7] |
| R15 | 버퍼 묶음 R(u) | DEC-63 257 | R9·R12 | 버퍼 블록 | 측정 기대(J12-a): pushpull {vin; A, B, vout; vout}, sf_pushpull {Y; N17, N20, vout; vout}, two_stage_ota_sf {OUT; vout; vout}, 기존 4회로 0 |
| R16 | 출력 방향 구조 분류 β/σ/κ | DEC-65 259 | R2, R9 | 출력 포트별 push-pull/class-A | 측정 기대(J12-e): two_stage_ota_sf vout class-A, two_stage_ota OUT class-A, 두 push-pull vout push-pull, 파일럿 Vop/Vom push-pull CS [J3] |
| R17 | 복합 블록 묶음(분기·합류) 판정 기록 | DEC-81 275 | R12 | 묶음 판정·경로별 기여(부호) | ngcc 발동 1·검증 발동 0 표기, 나머지 묶음 0 명시 [J12·J12-d]. 세부 규칙은 6c design |
| R18 | 기둥↔블록 매핑표·공유 소자·'블록마다 덮는 기둥 ≥ 1' | DEC-71 (2) 265, J13 | R5·R12 | 매핑표 | 9회로 블록마다 기둥 ≥ 1, 0이면 정지 |
| R19 | 규칙 분기 발동표(뷰별, 순방향 밖 셀 열) + status 전이 + `structure.json` 로드/해시 게이트 + shadow 대조 보고 | DEC-59 253, 370~380 | 전부 | `runs/<id>/rule_branch_coverage.json`, shadow 보고 | 매 실행 생성, IC7(827행) PASS. 정지 케이스는 6c(IC8 828행) |

GB2의 `undeclared_loop_constraint` 정지(316행)와 `unsupported_rule_branch` 정지(DEC-59)는 7b·6c 몫이고 6a는 기록만 한다.

---

## 3. 옛 엔진이 태그로 대신하던 판단 = 새 엔진 6a가 내야 할 출력 목록

새 엔진은 태그를 읽지 않는다. 아래 표는 옛 엔진의 태그 소비 지점(근거 위치)과, 그 판단을 대신할 6a 출력이다. 소비 지점 전수 원자료는 `6a_prep_raw/role_scan.txt`(AST로 함수 경계를 잡고 주석·docstring 줄을 뺀 근사)이고, 집계는 SR=sizing_recipe.py, SD=stick_diagram.py다.

| 옛 태그 | 옛 엔진 소비 지점(대표, 파일:행) | 옛 판단 | 대신할 6a 출력(규칙) | 6a로 다 못 내는 몫 |
|---|---|---|---|---|
| `headroom_role`(tail/cascode/mirror/diode_reference/voltage_divider…) SR 15줄·10함수 | `_min_need` 1742, `resolve_feed_vds` 1983, `gain_stage_tails` 2294, `_metric_stage_budget_vds_by_device` 6614, `reserved_vds_for_other_stack_members` 6700, `_hr_*` 6913·7097·7201·7250·7449, `search_stage_budget_L_warm_start` 10233 | VDS 배분 대상·순서, tail 판정 | `dc_role`(R2), `is_diode`, tail(DEC-17 DC 정의, R3), AC 셀(캐스코드 = 전류 구동 CG, R9·R10), 가지·기둥(R5) | VDS 배분 값 자체는 6b(W 티어)·7b(층 0 (4)(c)) |
| `gm_id_role` SR 13줄·5함수 | `_build_shared_current_joint_plan` 5691, `_feed_metric_stage_budget` 6052·6148, `make_replica_feasibility_check` 6737, `_evaluate` 8702·8735(→`search_gm_id_for_role`)·8795·8871 | 소자별 gm_id 탐색 범위 선택 | 셀 종류·stage 소속(R9·R12), DC 역할(R2), `equal_vgs`·`kvl_branch` 종속(R3·R4) | gm_id 값·범위는 GB6 θ(7b), LUT(MOD1) |
| `L_role` SR 15줄·6함수 | `derive_role_L` 2673~2677, `apply_diode_self_consistent_gm_id` 3663, `_hr_resolve_vertical_group` 7443, `_evaluate` 8398~8786, `l_class_owners` 2351 | L 고정배수/knee 선택 | L 동치류 + 주인(R3, DEC-17) | L 값은 N3.9 L 결정 규칙·GB6 |
| `vertical_stack_id` SR 29줄·12함수, SD 28줄 | `stack_kvl_vgs_limit` 1771, `allocate_stack_headroom` 1915, `_metric_stack_headroom_slack` 3285·3343, `_feed_diode_stack_target` 5472, `resolve_stack_layout` 6558~6587, `_hr_sum_ref_vds` 6983, `_evaluate` 8231·8540·8656·8723 | 같은 레일-레일 사슬(헤드룸 그룹) | 가지·기둥 + 레일 쌍(R5), 기둥 KVL 범위 | 레이아웃 행 묶음(`resolve_stack_layout`)은 레이아웃 소관(MOD7) |
| `fold_group` SR 24줄·4함수 | `_hr_fold_group_check` 6918~6968, `_hr_verify_group_kvl_sum` 7058, `_fold_group_check` 7120·8112, `_hr_resolve_vertical_group` 7519~7599 | 폴딩 노드 전류 합류 | 분기 노드(차수 ≥3)·공유 가지·기둥(R5), `kcl_group`(R3), 공유 소자(R18) [J8, 6b] | 전류 합류 등식은 6b·7b 조립 |
| `same_as_device` SR 6줄 | `l_sharing_classes` 2261, `_hr_*` 7224, `_evaluate` 8563·8657 | 병렬 동일 소자 | `same_as` 엣지(geom, **declared 유지** -- 사용자 connectivity 선언) | -- |
| `gm_id_match_vgs_of` SR 18줄·6함수 | `vgs_alias_map` 1649, `_feed_metric_stage_budget` 6051, `validate_theta_declaration_order` 6370, `_hr_*` 7433, `_evaluate` 8770~8871 | 공유 VGS(미러)·cross-kind VGS 매칭 | `equal_vgs`(v0 = 같은 (gate, source) 평행 엣지, R4), 미러 그룹(R3), `kvl_branch`(R4) | cross-kind VGS 매칭(파일럿 M15/M16)은 [J3-dc·J12-c] |
| `budget_reference_device` SR 8줄 | `stack_kvl_vgs_limit` 1778, `_metric_stack_headroom_slack` 3301, `reserved_…` 6676, `_hr_sum_ref_vds` 6982, `_evaluate` 8544·8657 | 기준 소자 VDS 공유 | `budget_ref` 엣지(declared) + 노드 공유 여부 | 노드를 공유하지 않는 4건은 [J8, 6b] |
| `shared_gm_id_groups`·`compensation.stage_devices` SR 6줄·15줄 | `optimize_multistage` 944·1121, `_shared_current_groups_from_compensation` 5625~5627, `_feed_metric_stage_budget` 6122, `_evaluate` 8171~8325 | 같은 전류 공유 묶음, stage 소자 | `kcl_group`·`equal_vgs`(R3), signal stage(R12) | 보상 수동소자 값은 GB5(7b) |
| `sizing_roles.metrics.stages`(`gain_stages_sum`) SR 8줄 | `gain_stage_tails` 2302, `_metric_gain_stages_sum` 2866, `_metric_device_footprint` 9597, `search_stage_budget_L_warm_start` 10225~10250 | stage 멤버십(RC1) | S1v signal stage·블록·극점 노드(R12) -- declared stage는 대조 입력으로만 | gain metric 통일은 7a |
| `symmetry.matching_pairs`/`current_forced` SR 43줄·SD 94줄 | `kcl_series_union` 2997, `_kcl_and_matching_edges` 3117, `resolve_stack_layout` 6481~6591, 레이아웃 함수 다수 | 매칭·강제 전류 | `matching_ratio`·`kcl_group`(declared 대조), 대칭 대응(R6) | 레이아웃 매칭은 MOD7 |
| netclass(INPUT/BIAS…, analog-grammar) SD 45줄·12함수 | `find_idiom_matches` 1072, `suggest_vertical_stack_composites` 1440, `_propose_headroom_roles` 2255~2307, `classify` 2398, `propose_device_roles_gap_fill` 4049 | 넷 분류 | ports + 교류접지 집합(R6·R8) + 도달성(R7) | -- |
| `device_roles` 전체(로더) | `load_topology` 8668~8763(gap-fill 자동 병합), `_device_roles_cached` SR 4903, `design_report.build_topology_device_table` 44·84 | 태그 자동 생성·보고 | 새 로더는 병합 안 함. 보고는 S1/S1v에서 | -- |

결론: 옛 태그가 하던 판단 중 **구조 판단**은 R2·R3·R4·R5·R9·R12가 모두 낸다. 태그가 섞어서 하던 **값 결정**(VDS 배분, gm_id 범위, L 값)은 6a 출력이 아니라 6b·7b 입력이다. C8(구조→사이징 입력 배선)은 새 엔진에서는 '태그 대체'가 아니라 처음부터 GB6/GB7이 S1/S1v를 읽는 계약으로 쓴다.

---

## 4. 기존 실측 도구 (재사용 여부)

| 도구 | 위치 | 성격 | 새 엔진에서 |
|---|---|---|---|
| `probe_stage_partition.py`(669줄) + `.result.md`(648줄) | `docs/03-analysis/gain-budget-gmid-sizing-function-audit/` | R3(DM/R2) 실측, 기존 4회로 declared stage 100% 일치 | **R12 회귀 기대값의 원자료**(규칙 8 (i), 356행). 스크립트는 참고만 |
| `probe_cg_cascode_stage.result.md`, `probe_common_drain.result.md` | 같은 곳 | 캐스코드 stage·CD 실측 | R9·R15 대조 원자료 |
| review 독립 dry-run 엔진: `review17_engine(2).py`, `review18_engine(2).py`, `review20_engine.py`(562줄, "plan text only, repo 코드 import 없음", 모호점마다 옵션 dict)·`review20_driver.py`(변형 20개)·`review20_analysis.py` | 같은 곳 | 계획 문장만으로 쓴 SP1·루프·기둥·DEC-63/64 측정 엔진 | **참고만**(계획 검토용 throwaway). 단 모호점 목록(옵션 키: `pcost`, `bfs_mode`, `mirror_merge`, `reduced` 등)은 6a design의 '열린 항목' 체크리스트로 그대로 쓸 수 있다 |
| `review9_measure2_cells_loops.py`·`review11_measure_v518.py`·`review10_rerun_v518_rules.py`·`review9_j1_*`·`review9_orchestrator_column_recount.py` + 결과 `review9_measure2_results.jsonl`, `review10_rerun_v518_results.jsonl`, `review11_r4_results.txt`~`review16_r8_results.txt` | 같은 곳 | 회차별 실측(계획의 '원자료 history H4') | 기대값 출처 아님(ratify 전). 재측정 비교용. ⚠️ `review9_measure2`는 `RAIL_NAMESET` 이름 집합을 쓴다(B26-1 이전 판) |
| 이번 실측 `extract.py`·`extract.jsonl`·`role_scan.py`·`s1_direct.txt` | `6a_prep_raw/` | 5절·3절·1.5 원자료 | 일회성 |

---

## 5. 9회로 현재 함수 실측 (격리 복제본, cb0ef86)

함수는 옛 엔진 그대로 불렀다(로더는 `load_topology` -- gap-fill이 섞인다. 선언 영향이 있는 칸은 표시). 해석은 하지 않았다.

| 회로 | 레일 / 포트(in→out) | diode | 진짜 미러 그룹(`true_current_mirror_groups`) | 차동쌍 후보 | 연결만 L류 / 선언 포함 L류 | 구조 대칭(mirror, 포트 seed) 쌍·자기·미해결 | `signal_path_nodes` | `kcl_series_union`(연결만, 2개 이상 묶음) | 상향/하향 가지(`trace_*`, 이름 리터럴) |
|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | vdd,gnd / vin→vout | 0 | 0 | 0 | 0 / 0 | 0·3·0 | ∅ | {M1,M2,M3} | 1/1 |
| current_reuse_telescopic_ota | vdd,gnd / Vip,Vim→Vop,Vom | 16 | 3: {M10,M12,M19,M21,M38,M5,M66,M68}, {M13,M17,M18_bg,M22,M6,M60,M61,M8}, {M36a,M7} | M1a/M1b(Vx), M4a/M4b(Vy), M37a/M37b(Ncmfb_tail) | 3 / 15 | 16·19·0 (low_conf M1a/M1b, M4a/M4b) | N1a2a, N1b2b, N3a4a, N3b4b, Vg15, Vg25, Vom1, Vop1 | 16묶음 | 하향 30(gnd·non_transistor) / 상향 29 |
| folded_cascode | vdd,gnd / vin_p,vin_n→out | 4 | {M10,M9}, {M11,MN}, {M3,M4,MP} | M1/M2(tail) | 3 / 6 | 2·8·1(M5), 충돌 1 | Vg7, X, Y | {M5,M9,M7}, {M6,M10,M8} | 3/6 |
| ngcc_3stage_ff | vdd,gnd / Vinp,Vinn→Vout | 3 | {M0,M12,M5}, {M10,M9}, {M14,M8}, {M3,M4,M6B}, {M6A,M7} | M1/M2(TAIL) | 5 / 6 | 1·5·9 | ND, NP, NX, V1, V2 | {M1,M3}, {M2,M4}, {M8,M9}, {M10,M11} | 9/9 |
| nmcnr_amplifier | vdd,vss / Vin_p,Vin_n→Vout | 2 | {M104,M105}, {M108,M109}, {M203,M204} | M102/M103(NodeTail) | 3 / 5 | 3·6·3 | NodeC, NodeF1, NodeF2, NodeM1, NodeM2, NodeS2 | 5묶음 | 하향 7(non_transistor) / **상향 0** |
| pushpull_follower_buffer | vdd,vss,agnd / vin→vout | 0 | 0 | 0 | 0 / 0 | 0·6·0 | **∅** | {M5,M3}, {M4,M6}, {M1,M2} | 하향 3(non_transistor) / **상향 0** |
| sf_pushpull_output_opamp | vdd,vss,agnd / vin_p,vin_n→vout | 1 (M4) | {M11,M8}, {M14,M16,M20}, {M17,M6,M9}, {M3,M4} | M1/M2(TAIL) | 4 / 5 | 1·12·8 | **∅** | 8묶음 | 하향 7(non_transistor) / **상향 0** |
| two_stage_ota | vdd,gnd / vin_p,vin_n→OUT | 1 (M3) | {M3,M4}, {M5,M7} | M1/M2(CS) | 2 / 3 | 1·3·2 | D3, O1 | {M3,M1}, {M4,M2}, {M6,M7} | 3/3 |
| two_stage_ota_sf | vdd,gnd / vin_p,vin_n→vout | 1 (M3) | {M3,M4}, {M5,M7,M9} | M1/M2(CS) | 2 / 3 | 1·4·3 | **∅** | {M1,M3}, {M2,M4}, {M6,M7}, {M8,M9} | 4/4 |

현재 함수로 **얻을 수 없는** 것(새로 써야 함): 교류접지 집합·바이어스 종속 넷, 셀 분류·구동 종류·stage·블록·극점 노드, 루프 탐지·분류, G_vgs 사이클, 레일 쌍별 기둥(이름 리터럴 없이), DC 역할, 버퍼 묶음, 출력 방향 분류, 발동표.

관찰(결함 후보, 판단 아님):
1. `signal_path_nodes`가 follower 출력 회로 3개에서 빈 집합이다(gate→source 엣지 없음). 이 함수가 PM 계산(`node_pole_estimate` 계열)의 노드 필터로 쓰이던 자리라면 그 회로의 극점 노드가 비게 된다 -- 옛 엔진 결함으로만 기록(새 엔진은 R7·R12).
2. `trace_*`는 vss 레일 3회로에서 상향 가지 0, 하향은 전부 `non_transistor` 종료(B26-2 이후 남은 이름 리터럴 `_RAIL_NETS`·`"vdd"`·`"gnd"`).
3. L 동치류는 선언(`same_as_device`, `matching_pairs`)을 넣으면 크게 달라진다(파일럿 3 → 15류). 차이는 전부 선언 엣지 몫이다 → 새 엔진에서 derived/declared 분리 근거.
4. 구조 대칭: 단일출력 미러 부하 회로(ngcc·sf_pushpull·two_stage_ota(_sf)·nmcnr)는 미해결이 많다 [J대상 J5]. folded_cascode는 M5 미해결·충돌 1 [J대상 J5·J9].
5. 파일럿 매칭 후보에 `('pmos','Vbias2')` {M2a,M2b,M58,M57}·`('nmos','Vbias3')` {M3a,M3b,M64,M63}이 나온다 -- 캐스코드 게이트 바이어스 넷이 diode가 구동하는 넷이다 [J대상 J1 -- 이미 ratified 2건과 같은 넷인지는 6a에서 대조].

---

## 6. 구현 순서 제안 (작은 단위, 각 단위의 test 기대값 출처)

모든 단위의 기대값은 test-author가 만든다. 출처 표기: **[JSON]** = topology JSON 직접 집계(독립), **[손]** = 손계산(작은 픽스처 또는 회로 일부), **[ratified]** = 승인 기록, **[계획 측정 기대]** = 계획에 적힌 실측값(ratify 전이라 회귀 기대가 아니라 대조 보고 대상).

| 단위 | 내용 | 규칙 | test 기대값 출처 | 선행 |
|---|---|---|---|---|
| U0 | 새 패키지 골격 + MOD2 `load_and_gate`(rail_declaration·linked·IC3 이식, gap-fill 없음) + `build_s1` + S0 지문·캐시 | R0 일부, R1 | [JSON] 1.5 표 전 열, 캐시 동일성, 태그 삭제 불변 | 6a design 승인 |
| U1 | GB0 게이트 확장: 숨은 레일 (iii)(잎 가지치기 **전** DC 전도 그래프), 3레일 `supplies_v`, MG2 옛 키 | R0 | [손] 공격 14 (a)(b) 픽스처(라이브러리 JSON에서 agnd 뺀 변형), 9/9 통과 | U0 |
| U2 | DC 전도 그래프(가지치기 전/후) + 가지·기둥(레일 쌍별 노드-단순 경로) + `vertical_stack_id` 대조 | R5 | [계획 측정 기대] 파일럿 62/32/9(265행 정본, 독립 재현 3회), [손] two_stage_ota·common_gate 기둥 전수 | U0 |
| U3 | `gs_groups`·diode·`kcl_group`(내부 2단자 넷)·`l_class`(미러만) derived 엣지 + declared 엣지 적재·대조 | R3 | [손] two_stage_ota·two_stage_ota_sf·ngcc(계획 1060행이 인용한 매칭 후보 목록과 대조) | U0 |
| U4 | DC 역할 (1)~(5) | R2 | [손] common_gate(전압 구동 CG 신호 소자 0이 되지 않아야 함, 87행 (3) 근거), two_stage_ota, ngcc(기준 없는 그룹 → review_needed) | U3, R6의 '모든 뷰에서 교류접지'가 필요하면 U6 뒤로 |
| U5 | G_vgs 사이클 v0/v1/v2/VDS-1 | R4 | [계획 측정 기대] DEC-64 행, [손] pushpull {M1~M4} 한 사이클 | U3 |
| U6 | 교류접지 3분류 + 기본 전달 뷰 + 대칭 대응(이식) + 최소 고정점 도달성·순방향 경로 | R6·R7 | [손] common_gate·pushpull·two_stage_ota(신호 넷 집합) | U0 |
| U7 | 바이어스 종속 넷 술어(뷰별) + DC 바이어스 SCC | R8 | **[ratified] J1**: 파일럿 2건·8회로 무동작 | U6 |
| U8 | 셀 분류·pass 묶음·이중 출력·순방향 밖 셀 | R9 | [계획 측정 기대] CG 8·pass 묶음 2, [손] two_stage_ota·common_gate 셀 판독(손계산) | U7 |
| U9 | 구동 종류 + 0-1 BFS(수동소자 비용은 design 결정값) | R10·R11 | [손] two_stage_ota·two_stage_ota_sf | U8, design 결정 |
| U10 | stage·블록·출력노드·임피던스 등급·극점 노드 + 규칙 9 + declared 대조 | R12·R13 | [계획 측정 기대] 기존 4회로 declared 100%(`probe_stage_partition.result.md`), [손] two_stage_ota_sf(M8 follower로 gain stage 수 ≠ 극점 단 수, DEC-57 251행) | U9 |
| U11 | 버퍼 묶음 + 출력 방향 구조 분류 | R15·R16 | [계획 측정 기대] DEC-63·DEC-65 행 | U10, U4 |
| U12 | 루프 뷰: 사이클 전수·분류·끊는 점·극성 | R14 | 재측정(옛 기대 36/18/1/0은 정의 확정 전 값이라 기대값으로 쓰지 않는다, 342행), [손] two_stage_ota_sf Cc 루프 1개 (2) | U10 |
| U13 | 복합 블록 묶음 기록(ngcc) + 기둥↔블록 매핑·덮는 기둥 ≥1 | R17·R18 | [계획 측정 기대] ngcc M7·M13·M14 → Vout 합류(1060행 connectivity 사실), 9회로 덮는 기둥 ≥1 | U2, U10 |
| U14 | 발동표(뷰별) + status 전이 + `structure.json` 로드/해시 게이트 + shadow 보고 + IC7 | R19 | [손] 전이표 374~378행 각 행 1케이스, IC7 regression | U1~U13 |
| U15 | J 대조표 생성(회로별, 판정 순서 J1 → J2·J5·J13 → J11 → J3-ac·J4·J10 → J12-a~i → J6·J7, 1045행) | -- | 사용자 ratify | U14 |

병렬 가능: U2·U3·U6은 U0 뒤 서로 독립. U5는 U3 뒤, U7~U12는 직렬.

### 착수 전 결정 필요(6a design 몫, 계획이 열어 둔 것)

1. 수동소자 엣지 비용(348행) -- R14 (3-b)/(4) 수를 가른다(1023행 감도 7 대 3).
2. 대칭 반쪽 공유 넷·형제 블록과 블록 노드 배타성(354행 ⚠️).
3. 병렬 소자를 기둥 경로 하나로 셀지(62 대 41, 265행).
4. 블록 구성 방식(미러 입력에서 멈춤/연장)에 따른 규칙 9 (c) 0 대 2회로(357행).
5. 새 패키지 이름·위치와 N3.10 MOD 번호의 관계(30-module-split design은 옛 파일을 옮기는 계획이다 -- '새로 짓는다' 전제와 Phase 3 이동 계획의 관계를 정해야 한다. 사용자 결정 대상).
