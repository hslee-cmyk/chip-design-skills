# gmid_engine.graph 동작 계약 (MOD3 S1 + U2~U4 구조 유도, test 작성용)

- 대상: `gmid_engine/graph/` 공개 API(`gmid_engine.graph.__all__`). test 는 `from gmid_engine.graph import ...`,
  `from gmid_engine.authoring import ...`, `from gmid_engine.core import ...` 만 쓴다(파일 모듈 직접 import·`_` 이름 금지).
  배치는 규칙 D: `gmid_engine/tests/graph/test_<파일>.py`, 9회로 교차는 `tests/integration/`.
- 근거: `_drafts/engine/design_mod3_s1_graph.md` 2.2·3·4·5·6절, `_drafts/engine/design_mod3_structure_u2_u5.md`(이하 DU)
  0.1·1~3·5·6·7절(U2~U4, U5 는 범위 밖), `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항'(최우선),
  `user_decisions.md` 2026-10-07(1번 supplies_v, 6번 bulk 기본 규칙, 10번 병렬 합쳐 세기), core `CONTRACT.md` 5·6절,
  authoring `CONTRACT.md`, 계획 DEC-57·64·70·71, N3.3(status 전이표), 용어집 91~92행,
  `_drafts/engine/reference_review/SYNTHESIS.md` Q8 (i)(iii)(사용자 승인 2026-10-07 "B는 추천대로 해" -- 4.5a).
- 입력: `authoring.load_topology(path)` 결과 `TopologyDoc` + 인자 `supplies_v`(+ `column_limit`). 엔진은 topology 의 `_` 키
  (`_declared_target_spec` 등)를 읽지 않는다 -- test 픽스처가 필요하면 test 쪽에서 꺼내 인자로 넘긴다.
- 대원칙(DU 0절): 규칙은 connectivity(S1 필드)·선언(포트·레일·수동/이상원 선언)만으로 판정한다. 회로·소자·넷 이름은
  **결정론적 순서 tie-break** 로만 쓰고 개수·불변량은 이름과 무관하다. library 에 없는 구조는 특수 처리 없이
  `StructureUnresolvedError`(reason `unsupported_rule_branch`)로 정지한다. 계산 블록 1 = 파일 1, 결과는 graph 필드(필드가 곧
  캐시), `supplies_v` 만 바뀌면 U2~U4 블록 재계산 0.
- 기대값은 test 쪽이 topology JSON 을 직접 집계해 만든다(피검 함수로 기대값을 만들지 않는다). 아래 7절 숫자는
  작성자 측 교차 확인용(이 커밋 코드로 실제 실행한 값, 2026-10-07)이다.

---

## 0. 파일과 진입점 (규칙 A~G, `_module_map` graph 층)

| 파일 | 층 | 독립 진입점 | 책임 |
|---|---|---|---|
| s1_values.py | 0 | (데이터 선언 모듈) 값 형식·어휘·`S1_WRITERS` | 값 형식·어휘·필드 권한표 |
| supplies.py | 0 | `supplies_declaration` | supplies_v 검사·정규화 |
| ac_ground_static.py | 1 | `static_ac_ground` | 교류접지 (1)(2) |
| bulk_default.py | 1 | `s1_bulk`(`@compute_block`) | device.bulk |
| s1_index.py | 1 | `terminal_index` | 넷별 단자 인덱스 |
| s1_key.py | 1 | `s1_key` | S1 지문 |
| s1_model.py | 1 | `S1Graph` | S1 스냅샷·질의 |
| s1_structure.py | 2 | `s1_structure`(`@compute_block`) | node·device 구조 필드(+ C1 `dc_nets`) |
| dc_conduction.py | 2 | `s1_dc_conduction`(`@compute_block`) | U2 DC 전도: 정지 검사·잎 가지치기·병렬 합침 segment |
| gs_groups.py | 2 | `s1_gs_groups`(`@compute_block`) | U3 같은 (kind, gate, source) 묶음 |
| branches.py | 3 | `s1_branches`(`@compute_block`) | U2 분기 노드·가지 |
| dc_roles.py | 3 | `s1_dc_roles`(`@compute_block`) | U3 소자 DC 역할 |
| rel_vgs.py | 3 | `s1_rel_vgs`(`@compute_block`) | U4 equal_vgs·vds_eq_vgs |
| rel_matching.py | 3 | `s1_rel_matching`(`@compute_block`) | U4 matching_ratio·l_class |
| gvgs_cycles.py | 3 | `s1_gvgs`(`@compute_block`) | U4 G_vgs 순환수·kvl_branch·v1·VDS-1 |
| columns.py | 4 | `s1_columns`(`@compute_block`) | U2 기둥·쌍 요약·orphan·열거 상한 |
| matching_groups.py | 4 | `s1_matching_groups`(`@compute_block`) | U4 matching_offset(바이어스 형제 제외)·레이아웃 matching 그룹·제외 기록(4.5a) |
| rel_kcl.py | 4 | `s1_rel_kcl`(`@compute_block`) | U4 kcl_group |
| s1_build.py | 5 | `build_s1` | 공개 진입점(빌드 순서·재사용) |

U2~U4 블록 10개는 서로 import 하지 않는다(값은 graph 필드로만 전달). 어느 것도 `device.bulk`·supplies 를 읽지 않는다.

## 1. `build_s1(doc, supplies_v=None, previous=None, column_limit=None) -> S1Graph`

- 인자 검사: `doc` 이 `TopologyDoc` 아님 -> `TypeError`. `previous` 가 S1Graph 가 아니거나 권한표가 `S1_WRITERS` 와 다름 ->
  `TypeError`. `column_limit` 가 None 도 0 이상 int 도 아님(bool 포함) -> `TypeError`.
- 순서(고정): `supplies_declaration(supplies_v, doc.rails)` -> `s1_key(doc, supplies)` -> 재사용 판정 -> `s1_structure(base,
  doc.devices, doc.passives, doc.sources, 정렬 레일 tuple, doc.ports)` -> `s1_bulk(·, supplies)` -> `s1_dc_conduction` ->
  `s1_gs_groups` -> `s1_branches` -> `s1_dc_roles` -> `s1_rel_vgs` -> `s1_rel_matching` -> `s1_matching_groups` -> `s1_gvgs` ->
  `s1_columns(·, column_limit)`
  -> `s1_rel_kcl` -> `S1Graph(key, snapshot)`. `base` = `previous.snapshot`(있으면) 또는 `GraphSnapshot.empty(S1_WRITERS)`.
- 재사용 판정: `previous.key == key` 이고 (`column_limit` 가 None 이거나 `previous` 의 기둥 수 ≤ `column_limit`)이면
  `previous` 를 **그대로**(`is`) 반환, 블록 호출 0. 기둥 수가 상한을 넘으면 반환하지 않고 블록을 부른다 -- `s1_columns` 만
  입력(extras)이 바뀌어 다시 돌고 정지한다(1.1).
- 재사용(확정 사항 1·2·5):
  - 같은 doc·supplies_v·column_limit 로 `previous` 를 넘기면 같은 객체, 모든 블록 계수 변화 0.
  - supplies_v 만 바꿔 `previous` 를 넘기면 `s1_bulk` 만 compute, 나머지 11 블록은 reuse(입력 버전 같음). node 레코드는
    모두 이전 스냅샷과 같은 객체, device 레코드는 bulk 필드가 바뀌는 MOS 만 새 객체.
  - `column_limit` 만 바꾸면(키 같음, 이전 기둥 수가 새 상한 초과) `s1_columns` 만 compute.
  - `previous` 없이 같은 doc 으로 두 번 부르면 두 번 계산하고 각 블록 `stats().recomputes_same_input` 이 1 오른다
    (정상 파이프라인 기대값 0 -- 호출자가 이전 S1 을 넘겨야 한다. graph 밖 memo 는 두지 않는다).
  - 연결 투영이 같으면(`_` 주석만 바뀐 파일, 태그 키 삭제, netlist 순서 섞기) 키가 같다(`connectivity_fp` 동일).
- 실패:
  - supplies_v 위반 -> `SchemaRejectedError`(2절).
  - bulk 기본 규칙 정지·U2~U4 정지 -> `StructureUnresolvedError`(4.6절). 정지는 예외라 캐시되지 않는다.

## 2. `supplies_declaration(supplies_v, rails) -> tuple | None`

- None -> None. 그 밖 -> 넷 이름순 `((넷, float), ...)`(int 는 float 로).
- 거부 = core `SchemaRejectedError`, `record.detail`: `gate == "supplies_v"`, `where == "supplies_v"`, `hits` = authoring
  `SchemaHit` tuple(위반 전부, 개수로 자르지 않음). hit 순서: 입력 넷 이름순으로 `supplies_unknown_net`·`supplies_value`,
  그 뒤 레일 이름순 `supplies_missing_rail`.

| rule | where | elements | 조건 |
|---|---|---|---|
| `supplies_type` | `supplies_v` | () | Mapping 아님(이 hit 하나) |
| `supplies_unknown_net` | `supplies_v.<넷>` | (넷,) | 키가 비문자열이거나 레일 선언(`doc.rails`) 밖 -- `_comment` 같은 `_` 키도 여기 걸린다 |
| `supplies_value` | `supplies_v.<넷>` | (넷,) | 값이 bool, 비실수, NaN·Inf |
| `supplies_missing_rail` | `supplies_v.<넷>` | (넷,) | 레일 선언 넷의 전위 없음 |

## 3. `s1_key(doc, supplies) -> S1Key(topology_fp, rule_fp, supplies_v_fp)`

- `topology_fp == doc.connectivity_fp`.
- `rule_fp` = `fp_of`(((basename, 파일 바이트(CRLF -> LF 정규화) sha256), ...) basename 정렬) over `S1_RULE_FILES`
  = (ac_ground_static, branches, bulk_default, columns, dc_conduction, dc_roles, gs_groups, gvgs_cycles,
  matching_groups, rel_kcl, rel_matching, rel_vgs, s1_build, s1_index, s1_structure, s1_values, supplies).py -- S1 필드 값을
  정하는 graph 파일 17개
  (s1_key.py·s1_model.py 제외). 같은 소스면 프로세스·`PYTHONHASHSEED` 와 무관하게 같다.
- `supplies_v_fp` = `fp_of(supplies)`, supplies None 이면 `NO_SUPPLIES_FP`(`"none"`). 전위 하나라도 다르면 다르다.
- `column_limit` 는 키에 들어가지 않는다(열린 결정 O1 기본안 -- 예산은 S1 키 밖).
- `S1Key` 는 frozen dataclass(`==` 는 세 값 비교).

## 4. 필드 정의 (core GraphSnapshot, 권한표 `S1_WRITERS`)

레코드 key: node = 넷 이름, device = 원소 이름(MOS·수동소자·이상원 한 이름 공간, IC3), graph = `GRAPH_KEY`(`"s1"`) 하나.
값은 모두 불변. 각 필드의 `snapshot.field(kind, key, field)` 는 core `FieldValue`(writer·input_version·write_count)다.
writer 이름 = 블록 이름(`S1_*_WRITER` 상수). 권한표 = 아래 4.1~4.5 의 writes 전부(C2: 옛 예약 4행 `dc_role`·`relation`·
`branches`·`columns` 는 없어지고 `RESERVED_FIELDS` 도 없다 -- `edge` kind 필드는 쓰지 않는다).

공통 값 형식(s1_values, 모두 frozen dataclass):
- `Evidence(rule, nets=(), group=(), basis=())` -- `basis` = 판정이 기댄 J 항목 ID(DU 6절 기본안: `J13-a`·`J13-b`·`J13-c`·
  `J13-d`·`J-U3-a`·`J-U3-c`·`J-U4-a`·`J-U4-b`·`J12-c`, Q8 신설 `J-U4-c`(`J_BRANCH_SYMMETRIC`)·`J-U4-d`(`J_MATCH_CLASS`),
  상수 `J_*`). J 에 기대지 않은 판정은 `()`.
- status 어휘(계획 N3.3 전이표, 엔진 규칙만으로 정함): `STATUS_DERIVED`(`"derived"`), `STATUS_PROPOSED`(`"proposed"`),
  `STATUS_REVIEW_NEEDED`(`"review_needed"`). declared 대조(태그·`vertical_stack_id`)는 S1 밖 U14 몫이라 S1 에 `declared` 는 없다.

### 4.1 writer `s1_structure` (reads 없음, extras = 연결 투영)

node 레코드 = 단자 넷(MOS d/g/s, 2단자 terminals) ∪ 선언 bulk 넷 ∪ 레일. 모든 node 에 아래 5필드가 있다.

| 필드 | 값 |
|---|---|
| `terminals` | ((원소, 단자), ...) 정렬. 단자 ∈ `MOS_TERMINAL_NAMES`(`d`,`g`,`s`) ∪ authoring `TWO_TERMINAL_NAMES`(`t0`,`t1`). bulk 미포함(bulk 만 있는 넷은 `()`) |
| `is_rail` | 넷 ∈ `doc.rails` |
| `port_direction` / `port_role` | 포트면 direction(`input`/`output`)·role, 아니면 None |
| `ac_ground_class` | `AC_GROUND_RAIL`(`"rail"`) = 레일 선언 넷 -- **단자 유무와 무관**(bulk 만 붙은 레일도 rail). `AC_GROUND_GATE_ONLY`(`"gate_only_undriven"`) = 레일 아님·입력 포트 아님·단자가 전부 `g`. 그 밖(레일이 아닌 단자 없는 넷 포함) None |

device 레코드 = 모든 원소.

| 필드 | 대상 | 값 |
|---|---|---|
| `element_class` | 전부 | `ELEMENT_MOS`(`"mos"`) / `ELEMENT_PASSIVE`(`"passive"`) / `ELEMENT_SOURCE`(`"ideal_source"`) |
| `kind` | 전부 | 선언 kind 그대로 |
| `pins` | 전부 | MOS `(("d", drain), ("g", gate), ("s", source))`, 2단자 `(("t0", 첫 넷), ("t1", 둘째 넷))`(문서 순서) |
| `dc_nets` (C1) | 전부 | authoring `dc_edges_unpruned` 의 그 원소 DC 엣지 넷 쌍(정렬 2-tuple) -- MOS 전부(d, s), 저항, 이상원 전부. 커패시터·그 밖 수동 kind 는 None(필드는 있고 값이 None) |
| `bulk_declared` | MOS | 선언 bulk 넷 또는 None |
| `is_diode` | MOS | gate == drain |
| `value_key` / `value` | 2단자 | authoring 투영 그대로(미선언 None) |
| `unsupported` | 지원 kind 밖 원소만 | 분기 이름: MOS kind ∉ {nmos, pmos} -> `mos_kind_unsupported`, 수동 kind ∉ {capacitor, resistor} -> `passive_kind_unsupported`, 이상원 kind ∉ {current_source} -> `source_kind_unsupported`(이상 전압원 포함). 기록은 여기서, 정지는 소비자 `s1_dc_conduction`(4.6) |

### 4.2 writer `s1_bulk` (reads `device.{bulk_declared, element_class, kind, pins}`, `node.is_rail`, extras `(supplies,)`)

MOS 레코드마다 `bulk` = `BulkResult(net, origin, reason)`:

| 우선순위 | 조건 | 값 |
|---|---|---|
| 1 | `bulk_declared` 있음 | `(그 넷, "declared", None)` |
| 2 | kind ∉ {nmos, pmos} | `(None, "undetermined", "unsupported_kind")` |
| 3 | supplies None | `(None, "undetermined", "needs_supplies_v")` |
| 4 | 그 밖 | `(최저 전위 레일, "default_rule", None)`(nmos) / `(최고 전위 레일, "default_rule", None)`(pmos) -- 레일 이름이 아니라 supplies 전위 값으로 고른다. 원점 이동 불변(±0.9 와 0/1.8 이 같은 넷을 고른다) |

정지 검사(4번 규칙을 쓸 소자가 하나라도 있고 supplies 가 있을 때만): `bulk_rail_potential_tie`(최저 또는 최고 전위 레일이
둘 이상, detail `rails`·`potential`), `bulk_multi_domain`(채널 레일 집합 ⊄ {최저, 최고}, detail `channel_rails`·`bulk_rails`·
`outside_rails`, devices = 바깥 레일에 d/s 가 닿는 소자). 커패시터·저항만 붙은 레일(교류 기준 `agnd` 등)은 채널 레일이
아니라 걸리지 않는다. 9회로 실측은 7.2.

### 4.3 U2 -- DC 전도·가지·기둥 (DU 1절, DEC-70·DEC-71 (1))

**`s1_dc_conduction`** (reads `device.{dc_nets, element_class, kind, unsupported}`, `node.{is_rail, port_direction}`;
writes `graph.dc_pruned`, `graph.dc_segments`)
1. 정지 검사: `device.unsupported` 가 있는 원소가 하나라도 있으면 정지(`rule_branch` = 이름순 첫 원소의 분기 이름,
   devices = 같은 분기 이름의 원소 전부, `nets` = ()) -- 지원 밖 MOS·이상원은 DC 엣지이고 지원 밖 수동 kind 는 DC 를
   통하는지 정의가 없다. 그다음 `dc_nets` 양 끝이 같은 원소 -> `dc_self_loop`(devices = 그 원소들, `nets` = 그 넷).
2. 잎 가지치기(DEC-70, J13-b 기본안 = 열거 전): 레일·포트가 아닌 넷 중 DC 엣지가 **수동소자(저항) 하나뿐**인 넷과 그
   저항을 지운다. 라운드마다 그 라운드 시작 시점의 잎 넷을 이름순으로 처리, 반복. 커패시터는 엣지가 아니라 차수에 들지
   않고, gate 단자도 들지 않는다. 포트·레일에 붙은 잎 저항은 남는다. MOS·이상원 잎은 지우지 않는다.
   `dc_pruned` = ((원소, 라운드), ...) (라운드, 원소) 순, 라운드는 1부터.
3. 병렬 합침(사용자 확정 10, J13-a 기본안 = 종류 무관): 남은 엣지를 같은 무향 넷 쌍끼리 묶어 `Segment(nets, elements)`
   (nets 정렬 2-tuple, elements 이름순). `dc_segments` = nets 순 tuple.

**`s1_branches`** (reads `graph.dc_segments`, `device.element_class`, `node.is_rail`; writes `graph.branches`, `node.dc_branch_node`)
- 분기 노드 = 레일이 아니고 segment 차수 ≥ 3 인 넷. `node.dc_branch_node` = 모든 node 레코드에 bool.
- 닻 = 레일 ∪ 분기 노드 ∪ segment 차수 1 넷. 가지 = 닻 사이 극대 직렬 segment 사슬. 닻을 이름순, 각 닻의 segment 를
  (반대 넷, 원소 tuple) 순으로 훑어 아직 안 쓴 segment 에서 사슬을 뻗는다.
- `Branch(id, ends, segments, has_ideal_source)`: id = 생성 순번(0부터 int), ends = (출발 닻, 도착 닻)(걷는 순서, 정렬 아님),
  segments = 걷는 순서, `has_ideal_source` = 이상원 원소 포함(J13-d: 그 전압 강하는 기둥 KVL 자유 변수 -- GB7 몫).
- 쓰이지 않은 segment 가 남으면(닻 없는 고리) `dc_isolated_loop` 정지(devices = 남은 원소, `nets` = 그 넷).

**`s1_columns`** (reads `graph.branches`, `node.is_rail`, extras `(column_limit,)`; writes `graph.columns`, `graph.column_pairs`,
`graph.column_orphans`)
- 레일 쌍 (r1, r2), r1 < r2 이름순, **모든 쌍**(J13-c 기본안)마다 가지 그래프(노드 = 가지 끝 넷, 엣지 = 가지; 양 끝이 같은
  가지 제외)에서 r1 -> r2 노드-단순 경로를 DFS 로 열거(내부 노드는 레일 아님, 이웃 순서 = (반대 넷, 가지 id)).
- `Column(id, rails, branch_order, parallel_expansion, status, evidence)`: id = 전체 순번, rails = (r1, r2), branch_order = 경로의
  가지 id(r1 쪽부터), `parallel_expansion` = 경로 위 모든 segment 원소 수의 곱(병렬 소자를 따로 셀 때 그 기둥이 갈라지는
  수 -- 회로의 '따로 센' 기둥 수 = 이 값의 합), status `derived`, evidence `Evidence("rail_pair_simple_path", (r1, r2), (),
  (J13-a, J13-b, J13-c[, J13-d 경로에 이상원 가지가 있으면]))`.
- `column_pairs` = ((r1, r2, 기둥 수), ...) -- 0 인 쌍도 기록(정지 아님).
- `column_orphans` = 어느 기둥에도 들지 않는 가지 `ColumnOrphan(branch, "review_needed")` tuple(정지 아님).
- 하단/상단 레일 구분은 전위가 필요해 S1 에 두지 않는다(GB7 `rail_v` 소비자 몫).
- 열거 누적 수가 `column_limit` 를 넘는 순간 `column_enumeration_over_budget` 정지(detail `limit`, `rails` = 넘은 쌍). None 이면 상한 없음.

### 4.4 U3 -- 같은 VGS 묶음·DC 역할 (DU 2절, 용어집 91행, DEC-57)

**`s1_gs_groups`** (reads `device.{element_class, kind, pins}`; writes `graph.gs_groups`)
- `GsGroup(kind, gate, source, members)` = 같은 (kind, gate 넷, source 넷)인 MOS 2개 이상(레일 gate 포함 원자료), (kind, gate,
  source) 순, members 이름순. U3 역할 (2)와 U4 `equal_vgs`·`matching_ratio`·`l_class` 가 이 필드 하나를 읽는다.

**`s1_dc_roles`** (reads `device.{element_class, is_diode, kind, pins}`, `node.{ac_ground_class, is_rail}`, `graph.gs_groups`;
writes `device.dc_role`) -- MOS 레코드에만 `DcRole(role, status, evidence)`(수동소자·이상원 레코드에는 필드 없음).
- 지원 밖 MOS kind 가 있으면 `mos_kind_unsupported` 정지(devices = 그 소자). `build_s1` 경로에서는 4.3 정지가 먼저 걸린다.
- '모든 뷰에서 교류접지' G = `ac_ground_class` ∈ {rail, gate_only_undriven}(J-U3-a 기본안 -- 바이어스 종속 넷 미포함).

| 순서 | 조건 | role | status | evidence(rule, nets, group, basis) |
|---|---|---|---|---|
| (1) | `is_diode` | diode_reference | derived | ("1", (gate, source), (), ()) |
| (2) | gs 묶음에 diode 멤버가 있음 -> diode 아닌 멤버 | bias_current_source | derived | ("2", (gate, source), 멤버, ()) |
| (2) | 묶음 gate ∈ G(diode 멤버 없음) -> 멤버 전부 | bias_current_source | derived | ("2", (gate, source), 멤버, (J-U3-a,)) |
| (2) | 위 둘 다 아님 -> 멤버 전부 | signal | **review_needed** | ("2", (gate, source), 멤버, (J-U3-c,)) |
| (3) | 남은 소자, gate ∈ G 이고 source 가 레일 | bias_current_source | derived | ("3", (gate, source), (), (J-U3-a,)) |
| (4) | ratified `structure.json` 상속 | -- | -- | ratified 사실 0(로더 없음) -> 발동 0, 구현 안 함(J-U3-b) |
| (5) | 나머지 | signal | derived | ("5", (gate, source), (), ()) |

### 4.5 U4 -- 관계 엣지·G_vgs (DU 3절, 계획 N3.3·DEC-64)

관계 엣지는 유형별 graph 필드에 `RelEdge(type, domain, members, status, evidence)` tuple 로 둔다(writer = 유형별 블록).
domain 어휘 `DOMAIN_DC`(`"dc"`)·`DOMAIN_DC_TO_SS`(`"dc_to_ss"`)·`DOMAIN_GEOM`(`"geom"`). `same_as`·`budget_ref`(선언 전용)와
`stacked_vsb`(소비자 GB7 W2 단계)는 만들지 않는다.

| 필드 (writer) | type | domain | 대상 / members | status | evidence |
|---|---|---|---|---|---|
| `rel_equal_vgs` (`s1_rel_vgs`) | equal_vgs | dc | gs 묶음마다 / 멤버 | derived | rule equal_vgs, nets (gate, source) |
| `rel_vds_eq_vgs` (`s1_rel_vgs`) | vds_eq_vgs | dc | diode 마다 / (소자,) | derived | nets (drain, source) |
| `rel_kcl_group` (`s1_rel_kcl`) | kcl_group | dc | segment 2개 이상인 가지마다 / segment 원소 tuple 들(걷는 순서) | derived | nets = 가지 ends, basis (J13-a,) |
| `rel_matching_ratio` (`s1_rel_matching`) | matching_ratio | dc | gate 가 **비레일**인 gs 묶음(미러)마다 / 멤버 | derived | nets (gate, source) |
| `rel_l_class` (`s1_rel_matching`) | l_class | geom | 같은 묶음마다 / 멤버 | **proposed** | basis (J-U4-a,) |
| `rel_matching_offset` (**`s1_matching_groups`**, 4.5a) | matching_offset | dc_to_ss | 같은 (kind, **비레일** source) MOS 묶음 중 gate 넷이 2개 이상으로 갈리는 것에서 **바이어스 형제를 뺀 뒤** gate 넷이 아직 2개 이상인 것 / 남은 멤버 이름순 | 남은 멤버 정확히 2 -> derived, 3 이상 -> review_needed | rule matching_offset, nets (source,) + 남은 멤버 gate 넷 정렬, group (), basis (J-U4-b,) |
| `rel_kvl_branch` (`s1_gvgs`) | kvl_branch | dc | G_vgs v2 사이클마다 / 사이클 대표 소자 이름순 | derived | rule `v2_rail`(F 경유) 또는 `v2_zero`, nets = 사이클의 비레일 넷 정렬, basis (J12-c,) |

`rel_matching_ratio`·`rel_l_class` 는 DC 전류비·L 동치류 관계라 4.5a 의 레이아웃 분류(bias_distribution·feedback_shared)와
무관하게 묶음 전체를 담는다(이번 변경으로 바뀌지 않음). `s1_rel_matching` reads = `graph.gs_groups`, `node.is_rail` 뿐.

**`s1_gvgs`** (reads `device.{element_class, is_diode, kind, pins}`, `node.{is_rail, port_direction}`; writes `graph.rel_kvl_branch`,
`graph.gvgs_summary`):
- G = MOS 마다 (gate, source) 무향 엣지, 모든 레일 = 고정 노드 F 하나. gate·source 둘 다 레일 -> `fixed_vgs` 에만.
  같은 비레일 넷(g == s) -> `gvgs_self_edge` 정지(devices = 그 소자, `nets` = 그 넷). 평행 엣지는 이름순 첫 소자 하나만 남긴
  단순 그래프 Gs(v0 = equal_vgs).
- 개수(기저·이름과 무관): P = 입력 포트 넷. c(H) = |E| − |V| + 성분 수. `v2_port0` = c(Gs − P), `v2_port1` =
  Σ_p [c(Gs − (P − {p})) − c(Gs − P)], `v1` = c(Gs) − v2_port0 − v2_port1, `cyclomatic` = c(Gs).
- 멤버: 단계별 숲(0: Gs − P 엣지 / p: 포트 p 마다 0단계 숲 사본에 p 에만 닿는 엣지 / 끝: 0단계 숲에 각 p 단계 트리 엣지와
  포트 2개 이상에 닿는 엣지). 단계 안 엣지 순서 = 끝점 이름순(F 먼저). 비트리 엣지마다 기본 사이클 1개(그 엣지 + 숲 경로).
  0·p 단계 사이클 = `rel_kvl_branch`, 끝 단계 = `gvgs_summary.port_diff`. 단계별 비트리 엣지 수 = 위 개수(구성상 같음).
  **불변량**: kvl_branch ∪ port_diff 멤버 합집합 = Gs 의 비다리(non-bridge) 엣지 대표 소자 집합.
- VDS-1: diode 아닌 MOS 중 drain·source(레일 병합 후)가 다르고 Gs 의 같은 성분에 있는 소자마다 사이클 1개(그 VDS 엣지 +
  Gs 최단 경로, 이웃 이름순). members = (그 소자,) + 경로 소자(drain 쪽부터) -- 경로가 그 소자 자신의 VGS 엣지를 지나면 같은
  이름이 두 번 나온다.
- `gvgs_summary` = `GvgsSummary(cyclomatic, v2_port0, v2_port1, v1, fixed_vgs, port_diff, vds_saturation)`; `port_diff` =
  `RelEdge("port_diff", dc, 멤버, derived, basis (J12-c,))`(제약 없음, 대조만), `vds_saturation` = `RelEdge("vds_saturation", dc,
  members, derived, basis (J12-c,))`(포화 하한 부등식).

### 4.5a 레이아웃 matching 분류 -- `s1_matching_groups` (SYNTHESIS Q8 (i)(iii), 사용자 승인 2026-10-07)

**`s1_matching_groups`** (reads `graph.{branches, gs_groups}`, `device.{dc_nets, dc_role, element_class, is_diode, kind, pins}`,
`node.{ac_ground_class, is_rail, port_direction}`; writes `graph.rel_matching_offset`, `graph.matching_groups`,
`graph.matching_dispositions`). 정지 분기 없음(기록만). 9회로 결과는 회로 해석이라 사용자 J-U4 대조표
(`_drafts/engine/J_U4_matching_table.md`)로 확인받는다 -- 그 전까지 아래 수치는 기대값이 아니라 작성자 실행값이다.

**구조 정의**(모두 기존 S1 필드만으로 정한다. 소자·넷 이름은 결정론적 순서에만 쓴다):

| 용어 | 정의 |
|---|---|
| G | `node.ac_ground_class` 가 None 이 아닌 넷(레일 ∪ gate 전용 비입력 넷, 4.1) |
| 입력 포트 넷 | `node.port_direction == "input"` |
| 가지 넷 nets(b) | `graph.branches` 의 가지 b 의 `ends` ∪ 모든 segment `nets` |
| 소자의 가지 | 그 소자를 segment 원소로 갖는 가지(MOS 는 가지치기 대상이 아니라 정확히 하나) |
| 블록 | 가지 그래프에서 **레일이 아닌** 가지 끝 넷을 공유하는 가지끼리 이은 연결 성분(= DC 전도 그래프에서 레일 넷을 지웠을 때의 연결 성분). 소자의 블록 = 그 소자 가지의 블록. 블록 넷 = 그 가지들의 nets 합집합 |
| 바이어스 블록 | 최대 고정점: 모든 블록에서 시작해, (a) 블록 넷에 입력 포트 넷이 있거나 (b) 블록 안 diode 아닌 MOS 중 gate 가 G ∪ (현재 바이어스 블록들의 넷)에 없는 것이 있는 블록을 빼기를 변화가 없을 때까지 반복한 나머지. 뜻: 레일은 교류접지라 블록 사이 DC 신호 통로는 gate 뿐이고, 블록 안 전류를 정하는 gate 가 모두 바이어스이면 그 블록 넷은 전부 바이어스다(자기 바이어스 고리 -- 서로 gate 를 대는 블록끼리 -- 도 남는다) |
| 바이어스 넷 B | 바이어스 블록들의 넷 합집합 |
| 영향 그래프 | 방향 그래프. 노드 = G 밖 넷. MOS 마다 g→d, g→s, s→d, `dc_nets` 가 있는 수동소자(저항)마다 양방향. 커패시터·이상원은 엣지 없음. 끝점이 같거나 한쪽이 G 인 엣지는 넣지 않는다 |
| 루프 신호 넷 L | 영향 그래프의 강연결 성분 C 중 (1) 넷 2개 이상 (2) 양 끝이 C 안인 MOS 엣지가 있고 (3) 어느 가지 하나의 nets 에도 C 전체가 들지 않는 것들의 넷 합집합. (3)은 diode 겹침(diode 위에 gate 를 같은 넷에 둔 소자를 쌓은 self-cascode 등)처럼 한 가지 안에서 닫히는 국소 고리를 뺀다. 커패시터를 빼므로 보상 커패시터(Miller 등)로만 닫히는 고리는 L 이 아니다 |
| 바이어스 형제 | 차동쌍 후보 묶음 멤버 중 다음 하나에 해당(검사 순서 = 기록 rule): `dc_role.role` ∈ {diode_reference, bias_current_source} -> `bias_sibling_dc_role` / gate ∈ G -> `bias_sibling_ground_gate` / gate 가 **자기 가지** nets 안 -> `bias_sibling_own_branch_gate`(그 가지 전류가 자기 gate 를 정하는 바이어스 다리) |
| 소비 소자 | gate 비레일 gs 묶음에 diode 멤버가 있을 때, diode 멤버가 하나도 없는 블록에 있는 diode 아닌 멤버 |
| 꼬리 넷 | status derived 인 `rel_matching_offset` RelEdge 의 공통 source 넷(`evidence.nets[0]`) |
| diode 넷 | `is_diode` MOS 의 gate(= drain) 넷 |
| 대응 넷 사상 | 무향 넷 짝 {a ↔ b}. seed = derived 이고 멤버가 정확히 2인 `rel_matching_offset` 의 두 멤버 drain 넷. 확장: 가지마다 걷는 넷 열(`ends[0]` 에서 segment 순서대로 반대 넷을 이은 열)과 그 반대 방향 열을 만들고, segment 서명 열(segment 마다 원소 (element_class, kind) 정렬 tuple)이 같은 두 열(같은 가지의 정·역방향 쌍 제외)에서 자리마다 (가) 같은 넷이면 끝 자리만 허용 (나) 다르면 둘 다 레일이 아니고 충돌 넷이 아니며, 이미 짝이 있는 넷이면 그 짝이 맞은편이어야 한다 -- 모든 자리가 이를 만족하고 이미 짝인 자리가 하나 이상이면 서로 다른 자리 넷끼리 짝을 더한다. 변화가 없을 때까지 반복. 짝을 더할 때 한쪽이 이미 다른 넷과 짝이면 관련 넷 전부를 충돌 넷으로 두고 최종 사상에서 뺀다. 레일은 짝이 되지 않는다 |

**차동쌍 후보** `rel_matching_offset`(4.5 표 행): 같은 (kind, 비레일 source) MOS 묶음(멤버 이름순) 중 gate 넷이 2개 이상인 것마다
바이어스 형제를 빼고, 남은 멤버 gate 넷이 2개 이상이면 RelEdge 하나. 뺀 소자는 남은 멤버로 RelEdge 를 만들었든 아니든
소자마다 `bias_sibling` 기록 하나(아래 표). 묶음 순서 = (kind, source) 순.

**`graph.matching_groups`** = `MatchingGroup(kind, members, status, evidence)` tuple, 순서 = (1) gate 비레일 gs 묶음 순서대로
각 묶음의 mirror 그룹들(한 묶음 안에서는 diode_block 다음 consumer_block) (2) `rel_matching_offset` 순서대로 diff_pair (3) branch_symmetric 찾은 순서.

| kind | 만드는 조건 | members | status | evidence (rule, nets, group, basis) |
|---|---|---|---|---|
| mirror | gate 비레일 gs 묶음에 소비 소자가 없음(diode 멤버 없음 포함) | 묶음 멤버 전부 | derived | (`mirror_whole`, (gate, source), diode 멤버, ()) |
| mirror | 소비 소자가 있고 gate ∉ B, gate ∉ L | 묶음 멤버 전부 | derived | (`mirror_signal_cross_block`, (gate, source), diode 멤버, (J-U4-d,)) |
| mirror | 소비 소자가 있고 gate ∈ B 또는 L, 소비 소자 아닌 멤버(diode 쪽)가 2개 이상 | 그 멤버 | derived | (`mirror_diode_block`, (gate, source), diode 멤버, (J-U4-d,)) |
| mirror | 같은 경우, 같은 블록에 모인 소비 소자가 2개 이상인 블록(블록마다, 아래 '소비 소자 세분') 중 drain 이 대응 넷 짝 (a, b) 인 소비 소자 둘(각 drain 에 열린 소비 소자가 정확히 하나) | 그 둘 | derived | (`mirror_consumer_symmetric`, (gate, source, a, b) -- a < b, diode 멤버, (J-U4-d,)) |
| mirror | gate ∈ B 또는 L 인 묶음에서 꼬리 소비 소자가 하나 이상(블록 크기 무관, 묶음 전체에서 모음) | diode 멤버 + 꼬리 소비 소자, 이름순 | derived | (`mirror_tail_ratio`, (gate, source), diode 멤버, (J-U4-d,)) -- 꼬리는 disposition 에서 빠진다 |
| mirror | 같은 블록 세분 뒤 남은 소비 소자가 2개 이상(블록마다) | 그 소자 | derived | (`mirror_consumer_block`, (gate, source), diode 멤버, (J-U4-d,)) -- 블록별 그룹 순서 = members 순 |
| diff_pair | `rel_matching_offset` RelEdge 마다 | 그 members | 그 status | (`diff_pair`, 그 evidence.nets, (), (J-U4-b,)) |
| branch_symmetric | 아래 stack 전파 | 위 소자들 | derived | (`branch_symmetric`, (gate,) + source 넷 정렬, seed 그룹 members, (J-U4-c,)) |

**소비 소자 세분**(사용자 ratify 2026-10-08 J14 1번·판단 7·M7 결정): bias_distribution 묶음(gate ∈ B)과 feedback_shared 묶음
(gate ∉ B, gate ∈ L) 모두에서 소비 소자 중 drain ∈ 꼬리 넷인 것은 블록에 혼자여도 **꼬리**(`mirror_tail_ratio`, disposition 에서
빠짐 -- 루프 신호 gate 로 구동되는 CMFB 꼬리도 diode 와 비율 미러). 이어서 같은 블록에 소비 소자가 2개 이상인 블록에서만, 꼬리가 아닌 소비
소자를 (2) drain ∈ diode 넷 -> **diode 공급**(그룹 없음, disposition 에만 남음) (3) 나머지 = 열린 소자로 나눈다. 열린 소자 중 drain 이
대응 넷 짝인 둘(그 두 drain 에 열린 소자가 하나씩)은 `mirror_consumer_symmetric`. 그 블록에 꼬리·diode 공급·대칭쌍이 하나도 없으면
옛 규칙 그대로 블록 전체가 `mirror_consumer_block`, 하나라도 있으면 남은 열린 소자가 2개 이상일 때만 `mirror_consumer_block`.
한 gs 묶음 안 그룹 순서: diode_block, (블록마다 symmetric 들 -> consumer_block), 끝에 tail_ratio.

**branch_symmetric stack 전파**(Q8 (i)): 대기열 = 위 (1)(2) 그룹 중 status derived. 대기열의 그룹 S 마다, S 의 멤버 m 의 drain 이
레일이 아니면 kind 가 m 과 같고 source == m 의 drain 이며 S 멤버가 아닌 MOS 를 모두 '위 소자'로 모아 gate 넷별로 나눈다.
gate 넷 하나의 위 소자들의 source 넷이 2개 이상이고 그 멤버 집합이 이미 있는 그룹(어느 kind 든)과 같지 않으면 새
branch_symmetric 그룹(gate 넷 순)을 만들고 대기열 끝에 넣는다(고정점까지 -- 쌓인 캐스코드가 다시 seed). diode 인 위 소자도
넣는다(캐스코드 미러 diode 쪽). kind 가 다른 drain-drain 접합(PMOS/NMOS 경계)은 같은 kind 조건으로 걸러진다.

**`graph.matching_dispositions`** = `MatchingDisposition(kind, members, status, evidence)` tuple, 순서 = bias_sibling 전부(차동쌍
후보 묶음 순, 묶음 안 멤버 순) 다음 gs 묶음 순서대로 bias_distribution·feedback_shared. status 는 모두 **proposed**(J-U4 확인 전).

| kind | 조건 | members | evidence (rule, nets, group, basis) |
|---|---|---|---|
| bias_sibling | 차동쌍 후보 묶음에서 뺀 바이어스 형제(소자마다 하나) | (그 소자,) | (위 형제 rule 셋 중 하나, (source, 그 소자 gate), 남은 멤버, (J-U4-b, J-U4-d)) |
| bias_distribution | gate 비레일 gs 묶음에 소비 소자가 있고 gate ∈ B | 그 묶음의 소비 소자 중 꼬리(`mirror_tail_ratio` 멤버) 를 뺀 전부(비면 기록 없음) | (`bias_distribution`, (gate, source), diode 멤버, (J-U4-d,)) |
| feedback_shared | 같은 경우 gate ∉ B 이고 gate ∈ L | 같음 | (`feedback_shared`, (gate, source), diode 멤버, (J-U4-d,)) |

판정 순서는 B 먼저, 그다음 L. 한 소자가 disposition(diode 기준 관계 제외)과 `mirror_consumer_block` 그룹(같은 블록 소비 소자끼리의
관계)에 함께 나올 수 있다 -- 둘은 다른 관계다.

**레이아웃 전달 정책**(G4-20 기본안, 소비자 MOD7 몫): 레이아웃 matching 에는 `matching_groups` 중 status derived(와 이후
ratified)만 쓰고, review_needed 그룹·`matching_dispositions` 는 matching 없이 배치하며 근거와 함께 결과에 남긴다.

**9회로 실측**(작성자 실행값, 2026-10-07 -- J-U4 대조표 확인 전):

| 회로 | mirror | diff_pair | branch_symmetric | bias_distribution | feedback_shared | bias_sibling |
|---|---|---|---|---|---|---|
| common_gate_amplifier | 0 | 0 | 0 | 0 | 0 | 0 |
| current_reuse_telescopic_ota | 5 ({M10, M19}·{M17, M8} consumer_symmetric, {M38, M5, M66}·{M18_bg, M6}·{M36a, M7} tail_ratio -- **ratified 2026-10-08 J14 1번·판단 7**) | 3 ({M37a, M37b}, {M4a, M4b}, {M1a, M1b}) | 2 ({M3a, M3b}, {M2a, M2b}) | 2 (Vbias4: M10, M12, M19, M21, M68 / Vbias1: M13, M17, M22, M60, M61, M8) | 0 (Vcmfb 묶음의 유일한 소비 소자 M7 이 꼬리 -> tail_ratio) | 2 (M63, M58 -- own_branch_gate) |
| folded_cascode | 3 ({M10, M9} whole, {M3, M4} consumer_symmetric, {M11, MN} tail_ratio -- 판단 7) | 1 | 2 ({M7, M8}, {M5, M6}) | 1 (vb1: M3, M4) | 0 | 0 |
| ngcc_3stage_ff | 5 (ND {M3, M4, M6B}·NX {M6A, M7}·NP {M10, M9} signal_cross_block, {M14, M8}·{M0, M12, M5} whole -- {M14, M8} 은 **ratified 2026-10-08 J14**(NGCC gm14 = gm8 비율 matching)) | 1 | 0 | 0 | 0 | 0 |
| nmcnr_amplifier | 3 ({M203, M204} signal_cross_block, {M104, M105}·{M108, M109} whole) | 1 | 1 ({M106, M107}) | 0 | 0 | 0 |
| pushpull_follower_buffer | 0 | 0 | 0 | 0 | 0 | 0 |
| sf_pushpull_output_opamp | 4 ({M14, M16, M20}·{M17, M6, M9}·{M11, M8} whole, {M3, M4} tail_ratio -- 판단 7) | 1 | 3 ({M13, M15}, {M10, M5}, {M12, M7}) | 0 | 0 | 0 |
| two_stage_ota | 2 (whole) | 1 | 0 | 0 | 0 | 0 |
| two_stage_ota_sf | 2 (whole) | 1 | 0 | 0 | 0 | 0 |

B(레일 제외): current_reuse {N11a11b, N11b, N14a14b, N14a_14b, N20a20b, N20b, N23a24b, N24b23a, Vbias1, Vbias4, Voc_des},
folded {vb1, vb2}, sf {NB}, 나머지 6회로 ∅. L: current_reuse 만 비어 있지 않음(CMFB·출력단·주 블록을 잇는 성분 하나 --
Vcmfb·Vx·Vom1·Vop1·Vom·Vop·Voc·Vbias2 등 16넷), 나머지 8회로 ∅. matching_offset 은 파일럿이 {M1a, M1b}·{M4a, M4b}·{M37a, M37b}
모두 derived(옛 규칙의 3멤버 review_needed 2건이 M58·M63 제외로 2멤버), 나머지 6회로는 옛 규칙과 같다.
대응 넷 사상(작성자 실행값): current_reuse {N1a2a↔N1b2b, N3a4a↔N3b4b, Vom1↔Vop1, Vg15↔Vg25, Vcmfb↔N36b}, folded {X↔Y, Vg9↔Vg10,
Vg7↔out}, ngcc {ND↔V1}, nmcnr {NodeF1↔NodeF2, NodeM1↔NodeM2}, sf {N1↔N2, N5↔N7, N56↔N78}, two_stage·two_stage_sf {D3↔O1},
common_gate·pushpull ∅. 세분 발동: 파일럿 Vbias4·Vbias1 묶음, folded vb1(멤버 같고 rule 만 consumer_symmetric)·vb2(꼬리 M11),
sf NB(꼬리 M3), 파일럿 Vcmfb(꼬리 M7, feedback_shared 묶음). 나머지 6회로 불변. 그 결과 9회로에서 feedback_shared 기록은 0건이다
(L 은 파일럿에만 있고, 그 묶음의 소비 소자가 꼬리뿐). feedback_shared 는 꼬리가 아닌 소비 소자가 루프 신호 gate 를 읽을 때만 남는다.

**일반성**(작성자 측 측정, `tests/generality/topogen` 합성 회로): syn_cs_load·syn_diffpair5·syn_follower 는 diode 기준 바이어스
블록 -> 다른 블록 전류원이라 bias_distribution 1건씩, branch_symmetric·feedback_shared·bias_sibling 0(그 구조 없음, 무동작).
손 변형: diffpair5 꼬리에 M58/M57형 바이어스 다리 추가 -> diff_pair 유지 + bias_sibling 1, 같은 gate 로 쌓인 diode 쌍은
branch_symmetric 0; NMOS 캐스코드 2단 -> branch_symmetric 2. 이름 치환 3벌·순서 섞기 3벌·극성 뒤집기에서 분류가 치환표를
따라감(42/42), 단 복제는 모든 kind 수가 정확히 2배. 소비 블록 세분(2026-10-08)은 위 합성·손 변형 6종에서 결과 불변(무동작); 세분이 걸리는
합성 변형 syn_dp_split(NMOS 차동쌍 + diode 바이어스 블록에서 받는 PMOS 부하 Pa/Pb·NMOS 꼬리 Ye·싱크 Na/Nb) -> {Pa, Pb}·{Na, Nb}
consumer_symmetric, {Nr, Ye} tail_ratio, 변형 불변량 49/49. 판단 7(혼자인 꼬리) 뒤: syn_diffpair5 와 그 손 변형 3종의 꼬리 Ye 가
bias_distribution -> {Ye, Yf} tail_ratio(그 구조 = 바이어스 diode 를 쓰는 차동쌍 꼬리가 있음), 차동쌍이 없는 syn_cs_load·syn_follower 는
불변, 변형 불변량 49/49.

### 4.6 정지 분기 (모두 core `StructureUnresolvedError`, exit 2, `detail["reason"] == "unsupported_rule_branch"`)

| `rule_branch` | 블록 | 조건 | `record.devices` / detail |
|---|---|---|---|
| `bulk_rail_potential_tie`, `bulk_multi_domain` | s1_bulk | 4.2 | 4.2 |
| `mos_kind_unsupported`, `passive_kind_unsupported`, `source_kind_unsupported` | s1_dc_conduction | 지원 밖 원소 존재(이름순 첫 원소의 분기) | 그 분기의 원소 / `nets` () |
| `dc_self_loop` | s1_dc_conduction | DC 엣지 양 끝 같은 넷 | 그 원소 / `nets` |
| `dc_isolated_loop` | s1_branches | 닻 없는 고리 segment 잔존 | 그 원소 / `nets` |
| `column_enumeration_over_budget` | s1_columns | 기둥 누적 수 > column_limit | () / `limit`, `rails` |
| `mos_kind_unsupported` | s1_dc_roles | 지원 밖 MOS kind(블록 단독 호출 시) | 그 소자 |
| `gvgs_self_edge` | s1_gvgs | MOS gate == source(비레일) | 그 소자 / `nets` |

review_needed 는 정지가 아니라 기록이다(DcRole 묶음·matching_offset 3개 이상·column_orphans). `s1_matching_groups` 는 정지 분기가
없다(분류 못 하는 경우는 mirror 그대로 또는 disposition 기록).

## 5. `S1Graph(key, snapshot)` 질의

- `key`: S1Key, `snapshot`: core GraphSnapshot(`writers == S1_WRITERS`). frozen.
- `column(kind, field)` -> `snapshot.column(kind, field)` 와 같은 key 정렬 tuple `((key, value), ...)`.
- `value(kind, key, field)` -> 값. 그 레코드·필드가 없으면 `KeyError`. graph 필드는 `value("graph", GRAPH_KEY, field)`.
- 공통 실패: (kind, field) 가 `S1_WRITERS` 에 없음 -> `KeyError`. 있으나 그 writer 의 `snapshot.block_version(writer)`
  가 None -> `FieldNotComputed`(`LookupError` 하위; 빈 tuple 을 돌려주지 않는다). `build_s1` 결과에서는 모든 권한표 필드의
  writer 가 돌았다(블록을 직접 일부만 부른 스냅샷에서만 `FieldNotComputed`).
- 결정론: 같은 doc·supplies_v 면 `snapshot.fp` 가 프로세스·`PYTHONHASHSEED`·netlist 순서와 무관하게 같다.

## 6. 부품 함수

- `terminal_index(devices, passives, sources)` -> 넷 이름순 `((넷, ((원소, 단자), ...)), ...)`. bulk 미포함.
- `static_ac_ground(index, rails, input_nets)` -> index 넷 순서 그대로 `((넷, 분류|None), ...)`(4.1 규칙).
- 계산 블록(core `ComputeBlock`, `stats()`·`reset_stats()`): `s1_structure(snapshot, devices, passives, sources, rails, ports)`,
  `s1_bulk(snapshot, supplies)`, `s1_dc_conduction(snapshot)`, `s1_gs_groups(snapshot)`, `s1_branches(snapshot)`,
  `s1_dc_roles(snapshot)`, `s1_rel_vgs(snapshot)`, `s1_rel_matching(snapshot)`, `s1_matching_groups(snapshot)`, `s1_gvgs(snapshot)`,
  `s1_columns(snapshot, column_limit)`, `s1_rel_kcl(snapshot)`. 직접 부를 때 extras 는 불변이어야 한다(core 6.2). 선행 블록 필드가
  없으면 projection 의 graph 값 조회가 `KeyError`.

## 7. 9회로 실측 (2026-10-07, 이 커밋 코드 + library 정정본 b9c7042, 9회로 모두 load 통과)

supplies_v: two_stage_ota·two_stage_ota_sf·current_reuse·folded·common_gate = 사용자 확정 `{vdd: 1.8, gnd: 0}`;
ngcc·nmcnr·pushpull·sf = topology `_declared_target_spec.supplies_v`(`_comment` 제외; nmcnr vdd 0.9/vss −0.9, pushpull·sf
vdd 1.8/vss 0/agnd 0.9). column_limit None. 9회로 모두 `unsupported` 열 `()`, 정지 0(오정지 0).

### 7.1 S1 기본 필드

| 회로 | node | 레일 | MOS(n/p) | 수동 | 이상원 | is_diode 참 | gate_only_undriven | 포트 in/out | bulk(default_rule) |
|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 7 | gnd, vdd | 3 (2/1) | 0 | 0 | 0 | VNBias1, VNBias2, VPBias1 | 1/1 | gnd 2, vdd 1 |
| current_reuse_telescopic_ota | 37 | gnd, vdd | 51 (24/27) | 12 | 1 | 16 (M11a, M11b, M14a, M14b, M18_bg, M20a, M20b, M23a, M24b, M36a, M36b, M39, M40, M57, M64, M66) | 없음 | 2/2 | gnd 24, vdd 27 |
| folded_cascode | 14 | gnd, vdd | 13 (8/5) | 1 | 1 | 4 (M7, M9, MN, MP) | bias3 | 2/1 | gnd 8, vdd 5 |
| ngcc_3stage_ff | 13 | gnd, vdd | 16 (9/7) | 3 | 0 | 3 (M3, M6A, M9) | VBN, VBP | 2/1 | gnd 9, vdd 7 |
| nmcnr_amplifier | 18 | vdd, vss | 15 (7/8) | 5 | 0 | 2 (M108, M203) | VB1~VB5 | 2/1 | vss 7, vdd 8 |
| pushpull_follower_buffer | 9 | agnd, vdd, vss | 6 (3/3) | 1 | 0 | 0 | VNB1, VPB1 | 1/1 | vss 3, vdd 3 (agnd 0) |
| sf_pushpull_output_opamp | 23 | agnd, vdd, vss | 22 (11/11) | 5 | 1 | 1 (M4) | 없음 | 2/1 | vss 11, vdd 11 (agnd 0) |
| two_stage_ota | 10 | gnd, vdd | 7 (4/3) | 3 | 0 | 1 (M3) | bias | 2/1 | gnd 4, vdd 3 |
| two_stage_ota_sf | 10 | gnd, vdd | 9 (6/3) | 2 | 0 | 1 (M3) | bias | 2/1 | gnd 6, vdd 3 |

two_stage_ota_sf 는 supplies_v 를 넘기지 않으면 bulk 9개 모두 undetermined(needs_supplies_v).
(옛 7.2 '3회로 거부·`passive_elements: []` 변형 참고값'은 topology 정정 b9c7042 로 사실이 아니게 되어 지웠다.)

### 7.2 다중 도메인 판정 실측

| 회로 | 레일(전위) | 채널 레일 | {최저, 최고} | 판정 |
|---|---|---|---|---|
| 2레일 7회로 | vdd/gnd(1.8/0) 또는 vdd/vss(0.9/−0.9) | 두 레일 | 같은 두 레일 | 통과 |
| pushpull_follower_buffer | vdd 1.8, vss 0, agnd 0.9 | vdd, vss (agnd 는 CL 단자만) | vss, vdd | 통과 |
| sf_pushpull_output_opamp | vdd 1.8, vss 0, agnd 0.9 | vdd, vss (agnd 는 CL·Cc 단자만) | vss, vdd | 통과 |

정지가 실제로 걸리는 증거(메모리 변형): pushpull 에서 nmos 하나의 source 를 agnd 로 -> `bulk_multi_domain`(outside agnd);
sf 에 레일 vddx(1.5) 추가 + pmos source 하나 이동 -> outside vddx; vddx 3.3 -> outside vdd; pushpull supplies agnd 0 ->
`bulk_rail_potential_tie`(agnd, vss).

### 7.3 U2 DC 전도·가지·기둥

'합침' = 엔진 필드(정본), '따로' = 병렬 원소를 따로 센 병기값. 기둥 따로 = Σ `parallel_expansion`(엔진 값). 분기 노드·가지의
'따로' 값은 엔진 필드가 아니라 작성자 측 독립 스크립트(병렬 segment 를 원소별 엣지로 풀어 같은 정의로 센 값)다.

| 회로 | dc_pruned (라운드) | segment | 병렬 segment | 분기 노드 합침/따로 | 가지 합침/따로 | 기둥 합침/따로 | column_pairs | orphan | 이상원 가지 |
|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | -- | 3 | -- | 0 / 0 | 1 / 1 | 1 / 1 | gnd–vdd 1 | 0 | 0 |
| current_reuse_telescopic_ota | Rz1 (1), Rz2 (1) | 51 | M9a∥M9b, M18a∥M18b, M6∥M7 | **7 / 9** | **27 / 32** | **41 / 62** | gnd–vdd 41 | 0 | 1 |
| folded_cascode | -- | 14 | -- | 3 / 3 | 8 / 8 | 7 / 7 | gnd–vdd 7 | 0 | 1 |
| ngcc_3stage_ff | -- | 13 | M6A∥M6B, M13∥M14∥M7 | 1 / 3 | 7 / 12 | 6 / 9 | gnd–vdd 6 | 0 | 0 |
| nmcnr_amplifier | Rm (1) | 15 | M301∥RL (J13-a 종류 무관 합침) | 3 / 4 | 10 / 12 | **9 / 10** | vdd–vss 9 | 0 | 0 |
| pushpull_follower_buffer | -- | 6 | -- | 0 / 0 | 3 / 3 | 3 / 3 | agnd–vdd 0, agnd–vss 0, vdd–vss 3 | 0 | 0 |
| sf_pushpull_output_opamp | -- | 26 | -- | 1 / 1 | 9 / 9 | 8 / 8 | agnd–vdd 0, agnd–vss 0, vdd–vss 8 | 0 | 1 |
| two_stage_ota | Rz (1) | 7 | -- | 1 / 1 | 4 / 4 | 3 / 3 | gnd–vdd 3 | 0 | 0 |
| two_stage_ota_sf | -- | 9 | -- | 1 / 1 | 5 / 5 | 4 / 4 | gnd–vdd 4 | 0 | 0 |

파일럿 41/62 = 계획 DEC-71 (3), 나머지 3~9 와 일치. 불변식(9회로 확인): 기둥마다 연속 가지가 넷을 공유하고 내부 노드가
레일이 아니며 r1 에서 시작해 r2 에서 끝난다.

### 7.4 U3 같은 VGS 묶음·DC 역할

| 회로 | gs_groups | diode | bias | signal | review_needed 묶음(멤버 signal) |
|---|---|---|---|---|---|
| common_gate_amplifier | 0 | 0 | 2 | 1 | -- |
| current_reuse_telescopic_ota | 3 | 16 | 15 | 20 | -- |
| folded_cascode | 3 | 4 | 4 | 5 | -- |
| ngcc_3stage_ff | 5 | 3 | 8 | 5 | {M14, M8} |
| nmcnr_amplifier | 3 | 2 | 7 | 6 | -- |
| pushpull_follower_buffer | 0 | 0 | 2 | 4 | -- |
| sf_pushpull_output_opamp | 4 | 1 | 1 | 20 | {M11, M8}, {M14, M16, M20}, {M17, M6, M9} |
| two_stage_ota | 2 | 1 | 3 | 3 | -- |
| two_stage_ota_sf | 2 | 1 | 4 | 4 | -- |
| **합계** | 22 | **28** | **46** | **68** | **4 묶음, 멤버 10** (계획 용어집 91행 실측과 정확히 일치) |

### 7.5 U4 관계 엣지·G_vgs

| 회로 | equal_vgs | vds_eq_vgs | kcl_group | matching_ratio = l_class | matching_offset | G_vgs cyclomatic (v2 포트0 / 포트1 / v1) | fixed_vgs | VDS-1 |
|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 0 | 0 | 1 | 0 | -- | 0 (0/0/0) | 0 | 0 |
| current_reuse_telescopic_ota | 3 | 16 | 18 | 3 | {M37a, M37b}, {M4a, M4b}, {M1a, M1b} 모두 derived (M63·M58 = bias_sibling, 4.5a) | **5 (4/0/1)** | 0 | **22** |
| folded_cascode | 3 | 4 | 3 | 3 | {M1, M2} derived | 0 | 0 | 1 (M10) |
| ngcc_3stage_ff | 5 | 3 | 6 | 5 | {M1, M2} derived | 0 | 0 | 6 |
| nmcnr_amplifier | 3 | 2 | 5 | 3 | {M102, M103} derived | 0 | 0 | 4 |
| pushpull_follower_buffer | 0 | 0 | 3 | 0 | -- | **1 (0/1/0)** | 0 | 0 |
| sf_pushpull_output_opamp | 4 | 1 | 8 | 4 | {M1, M2} derived | **1 (1/0/0)** | 0 | 0 |
| two_stage_ota | 2 | 1 | 3 | 2 | {M1, M2} derived | 0 | 0 | 1 (M4) |
| two_stage_ota_sf | 2 | 1 | 4 | 2 | {M1, M2} derived | 0 | 0 | 1 (M4) |

사이클 멤버(작성자 측 실행값): current_reuse kvl_branch 4개 모두 `v2_rail` -- {M11a, M11b, M15, M9a}, {M14a, M14b, M16, M9b},
{M18a, M20a, M20b, M25}, {M18b, M23a, M24b, M26}; port_diff {M1a, M1b, M4a, M4b}. pushpull kvl_branch {M1, M2, M3, M4}
`v2_zero`(입력 포트 하나를 지나는 v2). sf kvl_branch {M18, M19, M21, M22} `v2_zero`. 9회로 모두 kvl_branch ∪ port_diff
멤버 합집합 = Gs 비다리 엣지(불변량 확인). 대표 소자 선택은 이름 tie-break 이라 test 는 개수와 이 불변량으로 비교한다.
VDS-1 22/1/6/4/0/0/1/1 = DU 3.4 표(J12-c 재측정)와 일치. matching_offset 은 S6a '차동쌍 후보'와 대조 보고 대상(기대값 아님).
옛 규칙(바이어스 형제 미제외)의 파일럿 값은 {M4a, M4b, M63}·{M1a, M1b, M58} review_needed 였다(2026-10-07 Q8 (iii) 로 변경).

### 7.6 재사용·결정론·정지 (작성자 측 실행 확인)

- 9회로 모두: supplies_v 를 바꿔(+0.5 V 원점 이동) `previous` 를 넘기면 compute 는 `s1_bulk` 1회뿐(U2~U4 블록 9개 reuse),
  같은 인자로 한 번 더 부르면 `is` 같은 객체. netlist 순서를 섞은 파일은 `snapshot.fp` 동일. `PYTHONHASHSEED` 1~5 에서
  회로마다 `snapshot.fp` 하나.
- 정지 실제 발동(two_stage_ota 메모리 변형): 인덕터 추가 -> `passive_kind_unsupported`(Lx); 이상 전압원 -> `source_kind_unsupported`;
  MOS kind njfet -> `mos_kind_unsupported`; MOS d == s -> `dc_self_loop`; 새 넷 la·lb·lc 위 MOS 3개 고리(la→lb→lc→la, gate 는
  첫 netlist 소자의 gate 넷) -> `dc_isolated_loop`(저항만의 고리는 authoring `hidden_rail` 로 먼저 거부된다); `column_limit=1` ->
  `column_enumeration_over_budget`(3 은 통과); gate == source(비레일 tail 넷) MOS 추가 -> `gvgs_self_edge`; `column_limit` 없이
  만든 S1 을 previous 로 `column_limit=1` -> 반환하지 않고 정지, `column_limit=3` -> 같은 객체.

## 8. 다음 단계 (이번 단계에서 만들지 않음 -- 호출자가 생길 때 그 단계에서 만든다)

- U5(DU 4절): 대칭 대응·뷰·뷰별 교류접지·신호 도달성·바이어스 종속 넷(S1v). core `GraphRecord.key` 는 str 만 받으므로
  (O2 확인 결과) `vnode` 의 (view_id, net) key 는 정준 문자열 인코딩 helper 가 필요하다 -- U5 에서 정한다.
- `S1Graph.relations(type=None)` 질의(DU 3.0) -- 소비자 GB7 `writer_plan` 이 생길 때.
- DC 역할 (4) 상속 -- ratified `structure.json` 로더가 생길 때. declared 대조(U14).
- S1 스냅샷 디스크 캐시(확정 6 E3, 키 = `S1Key`), 회로 spec 로더(supplies_v 출처, DEC-60 (i))와 `S0` 전체 지문.

## 9. 설계와 다르게 정한 점

design_mod3_s1_graph 대비:
1. **S1 저장 = core GraphSnapshot**(사용자 지시): 설계 3절의 `S1Graph` 필드 묶음 대신 node·device(·graph) 레코드 필드, 필드
   메타는 core `FieldValue`. 수동소자·이상원도 device 레코드(`element_class` 로 구분, IC3).
2. **계산 블록 분리**(규칙 C): supplies_v 만 바뀌면 bulk 만 다시 계산한다. `bulk_default.py` 진입점은 블록 `s1_bulk`.
3. **`supplies.py` 신설**: supplies_v 검사를 한 곳에 둔다.
4. **인덱스 축소**: `terminal_index` 는 넷별 단자만. `gs_groups` 는 U3 에서 질의가 아니라 graph 필드(`s1_gs_groups`)로 실현.
5. **`unsupported`**: 원소별 필드, 정지는 소비자(`s1_dc_conduction`).
6. **다중 도메인·전위 동률 정지**(사용자 확정 6번).
7. **`rule_fp`**: graph 파일 바이트 sha256(`S1_RULE_FILES`).
8. **authoring `__all__` 에 `INPUT_DIRECTION` 추가**.

design_mod3_structure_u2_u5(DU) 대비:
9. **C2 `RESERVED_FIELDS` 삭제**: 예약 4행을 실제 writer 필드로 바꾸면서 상수 자체를 없앴다(남은 예약 없음, 빈 상수를 두지 않음).
10. **지원 밖 원소 정지 범위**: DU 1.2 는 'DC 엣지가 되는 것'만 정지라 했으나, 지원 밖 수동 kind 는 `dc_edges_unpruned` 가
    엣지로 넣지 않아(저항만 엣지) DC 여부를 판정할 근거가 없다 -> `unsupported` 원소는 분류 무관 모두 정지. `rule_branch` 는
    S1 이 기록한 분기 이름(`mos_kind_unsupported`·`passive_kind_unsupported`·`source_kind_unsupported`) 그대로.
11. **reads 차이**: `s1_branches` 가 `device.element_class` 를 더 읽는다(`has_ideal_source`). `s1_gs_groups` 는 `unsupported` 를,
    `s1_rel_vgs` 는 `node.is_rail` 을 읽지 않는다(쓰지 않음).
12. **`graph.column_pairs` 신설**: DU 1.3 '쌍별 0 을 graph.columns 의 쌍 요약에' -> 필드 하나에 값 형식 둘을 섞지 않고 별도 필드.
13. **값 형식 보강**: `Evidence.basis`(J ID), `Column.evidence`, `ColumnOrphan`, `GsGroup`, `GvgsSummary`. v1·VDS-1 사이클은
    `gvgs_summary` 안 RelEdge(type `port_diff`·`vds_saturation`).
14. **G_vgs 멤버 단계 순서**: DU 3.2 'F 뿌리 BFS, 이웃 이름순' 대신 단계 안 엣지를 끝점 이름순으로 넣는다(같은 결정론, 단순).
    포트 p 단계는 0단계 숲의 **사본**에서 키워(포트끼리 독립) 포트 둘 이상을 지나는 사이클이 v1 로 간다 -- 개수 공식과 구성상 일치.
15. **O1**: `column_limit` 는 build_s1 인자, S1Key 밖. previous 재사용 경로에서도 상한을 지키도록 '이전 기둥 수 ≤ 상한'일 때만
    previous 를 그대로 돌려준다.
16. **O2**: core 레코드 key 는 str 만(tuple 불가) -- U2~U4 는 graph 레코드 key `"s1"` 하나라 영향 없음, U5 로 넘긴다(8절).
17. **matching_offset 정의 구체화**: 같은 (kind, 비레일 source) 묶음에서 gate 넷이 2개 이상으로 갈릴 때만(gate 가 모두 같으면
    gs 묶음). ~~파일럿 입력쌍 M1a/M1b 는 같은 source 의 M58 때문에 3멤버 review_needed~~ -> 18번으로 바뀜.
18. **Q8 (i)(iii) 레이아웃 matching 분류(2026-10-07, 4.5a)**: (a) `rel_matching_offset` writer 를 `s1_rel_matching` 에서 새 블록
    `s1_matching_groups` 로 옮겼다 -- 바이어스 형제 제외가 가지·DC 역할을 읽어 블록 입력이 달라서(규칙 C, writer 1). (b) 설계
    문서의 'MOD3 블록(stage·bias)'·'loops.py 루프'는 아직 없는 모듈이라, 블록 = 레일을 지운 DC 성분, 바이어스 넷 = 바이어스 블록
    최대 고정점, 루프 신호 = 영향 그래프의 비국소 강연결 성분(커패시터 제외)으로 기존 S1 필드에서 정의했다. (c) 바이어스·루프
    판정은 diode 가 있는 gs 묶음의 '소비 소자'에만 건다(diode 없는 묶음은 mirror 그대로) -- 승인 문언 'diode 와 다른 블록의
    소비 소자'와 DRS (c)(d) 의 'diode 가 만든 노드를 읽는 관계'를 따른 것. (d) 같은 블록에 모인 소비 소자끼리는 mirror
    (`mirror_consumer_block`)로 남겼다 -- 빼면 folded M3/M4 같은 대칭 전류원과 그 위 캐스코드쌍 seed 가 사라진다(J-U4 확인 대상).
    -> 2026-10-08 사용자 ratify(J14 1번)로 '소비 블록 세분'(꼬리 -> diode 와 비율 미러, diode 넷 drain -> bias_distribution 만,
    drain 대응 짝 -> 대칭쌍)을 더했다. 판단 7(2026-10-08 ratify): 꼬리는 블록에 혼자여도 tail_ratio. 단 feedback_shared 묶음의
    꼬리(파일럿 M7, Vcmfb)도 2026-10-08 사용자 결정("꼬리 비율 미러 {M36a, M7}로 분류")으로 같은 꼬리 규칙(gate ∈ L 묶음 포함). 대응 넷은 U5 `graph.symmetry` 가 없어 derived 차동쌍 drain seed 의 가지 서명 전파로 정의했다.
    (e) branch_symmetric seed 에 mirror 도 넣었다(folded M7/M8·nmcnr M106/M107·sf 3쌍은 mirror 위에 쌓임). (f) 차동쌍 후보의
    '신호 넷 gate(입력 포트 또는 graph.symmetry 대응) 정확히 2' 조건(G5-03)은 U5 가 없어 넣지 않았다 -- 바이어스 형제 제외만.

---

## 10. SP1 -- `build_s1v` (U1, 설계 41 §0 단계 A3·§1, 40 §3.2, 계획 N3.2·DEC-43·57·63·65·81)

test 작성자용 계약. 이 절의 숫자·기대값은 **없다**(기대값은 toy 손계산·ratified 대조표·불변량으로 만든다). 아래 불변량이 test 대상이다.

### 10.1 공개 API (`gmid_engine.graph.__all__`)

| 이름 | 설명 |
|---|---|
| `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None, stop_on_unsupported=True) -> S1v` | 진입점. `s1` = `build_s1` 결과, `spec` = `SizingSpecDoc` 또는 None(기본 전달 뷰만). `count_budget` = 계수 예산 N_S(1 이상 int, bool 거부 `TypeError`) |
| `S1v`, `ViewS1v`, `ViewSeed`, `Block`, `CompositeBlock`, `Loop`, `LClass`, `Finding`, `StructureFact`, `CellInfo`, `DriveInfo`, `PoleNode`, `PassBundle`, `OutputDirection` | frozen dataclass(`fp_of` 가능). 필드 뜻과 어휘(`Block.kind`·AC 역할·`DriveInfo.basis`·`LClass.owner_rule`·`OutputDirection.topology`·`unreduced_diff` 형식)는 `s1v_values.py` docstring 이 정본이고 10.5 에 요약한다 |
| `load_structure_facts(path, topology_fp, rule_fp) -> StructureFacts` | `structure.json` ratified 사실 로더(파일 없음 = 사실 0, 형식 위반 = `SchemaRejectedError` gate `structure_json`, 해시 불일치 = 사실 미적용 + `structure_fact_stale` review_needed) |
| `structure_tables(s1v) -> dict` | JSON 으로 쓸 수 있는 구조 표(뷰·셀·구동 종류·블록·극점 노드·루프·L 동치류·기록) |
| `s1v_rule_fp() -> str` | S1v 규칙 코드 지문(`S1V_RULE_FILES` 바이트). `structure.json` 의 `rule_hash` 와 재사용 키가 쓴다 |

### 10.2 동작

* 순서: `collect_views` -> 전달 뷰마다 `analyze_view` -> 전달 뷰의 (3) 루프가 만든 루프 뷰(끊는 점 (소자, gate 넷)마다 하나) -> 루프 뷰 판정 -> `l_equivalence_classes` ->
  `declared_compare`. 뷰 id: 전달 `transfer:<순번>`(여기·관측 정렬 순), 루프 `loop:<소자>:<gate 넷>`.
* **뷰 수집**: spec 제약의 `ViewDecl`(port·loop = 가중+관측, transfer, ratio = 분자·분모)마다 하나, (여기, 관측) 중복은 하나. 선언이 없으면 기본 뷰: 입력 포트 role 이
  차동 p·n 한 쌍이면 가중 ±1/2 기모드 여기 하나, 아니면 입력 포트마다 단일 여기. 관측 = 출력 포트 전부. mode `sense`·`none`·`pending` 은 구조 뷰를 만들지 않는다.
* **교류접지**: 레일 ∪ gate 전용 미구동 넷(S1) ∪ 이 뷰에서 여기하지 않는 입력 포트 ∪ (4) 바이어스 종속 넷(술어 (0)(i)(ii)(iii), `ac_ground_view.py` docstring). 기모드
  여기에서 회로 자기동형(`virtual_ground`, 맞짝 전파)이 있으면 자기대응 넷(`ViewS1v.virtual_ground`)은 **축약 뷰의 접지**다 -- 셀·구동 종류·블록·극점 노드·출력 방향은 축약
  뷰 기준, 루프·끊는 점은 비축약 뷰 기준(공통모드 되먹임이 가상접지를 지난다). 두 뷰에서 셀 판독이 다른 소자는 `unreduced_diff`.
* **셀**: gate==drain -> `diode_load`. gate∈S: drain 접지 -> `cd`, source 접지 -> `cs`, 둘 다 아니면 source 가 순방향 위 신호 셀 입력·출력 포트에 닿을 때 `cell_ambiguous`
  (기록만), 아니면 `cs`(degeneration). gate∉S: 같은 두 노드 사이 반대 방향 둘 -> pass 묶음(셋 이상 방향 섞임 `pass_group_unsupported`), 아니고 source∈S -> `cg`, 그 밖 `off`.
  셀 이름은 소문자 `cs`/`cg`/`cd`/`pass`/`diode_load`/`off`(규칙 E: 대문자 `CS` 는 library 넷 이름과 같아 쓸 수 없다). `CellInfo.forward` = 출력 단자가 순방향 집합 위.
* **구동 종류**: 진입(여기 포트 / CS drain·source / CD source / CG drain / diode source·drain)에서 규칙 1(drain 진입만 = 전류 후보)·3(gate 로만 나가면 전압, 채널로만 전류, 둘 다 gate 쪽
  순방향이면 전압(stage 경계), 아니면 tap)·4(혼재 = drain 쪽 DC 역할로: 바이어스 전류원이면 전압, 신호 소자면 `mixed_drive_signal_drain`, 못 가르는 그룹이면 잠정 전압 +
  `mixed_drive_unresolved_group`)·2·5(저항·pass 로만 들어오면 이웃 종류 상속, 저항은 `value_dependent`). ratified `drive_kind` 사실은 해당 넷을 고정(근거 `ratified_fact`).
* **stage**: `dist`(수동소자 엣지 포함 0-1 BFS, 복귀 경로 판정용)와 `stage_dist`(수동소자 제외, stage 번호용). 시작 셀 = 순방향 CS(gate 전압 구동, 미러 입력 아님, DC 역할이
  바이어스 전류원 아님) / source 가 전압 구동인 CG. 블록 stage = 시작 셀 입력 넷 `stage_dist` + 1.
* **임피던스 등급**(41 §1.7-4, 2026-10-08 정정): `node_impedance` 표 하나를 블록 출력노드(`Block.impedance`, 이득·버퍼 블록 모두)와 극점 노드가 함께 읽는다. 낮음 = MOS source 단자(gate 가 교류접지이든 구동되든 무관 -- follower 출력 포함)나 diode 단자가 붙은 노드, 값 의존 = 낮음 없이 저항이 붙은 노드, 높음 = 그 밖. pass 묶음 소자의 단자는 등급에 기여하지 않는다(통로).
* **블록**: 소유 고정점(시작 셀 -> 캐스코드·미러 연장·pass·diode). 같은 stage 블록이 넷(공통 소스·출력)을 공유하면 합친다(차동 블록). 출력노드가 같은 블록 pass 묶음의 한 끝이면 반대 끝으로 따라간다(41 §1.7-1: pass 로 끝나면 pass 출력 단자 노드 = 포트). 키 = 출력노드 이름 정렬 tuple. 서로 다른 stage 가
  합류 노드를 공유하면 복합 블록 후보. 출력노드 임피던스가 낮으면 `cs_output_low_impedance`(기록만). 버퍼 블록 = CD 묶음 R(u)(싱크 하나). 이득 블록과 버퍼 블록이 합류 노드가 아닌 넷을 공유하면 `block_node_overlap`(review_needed, 불변량 4).
* **루프**: 방향 신호 그래프(gate->drain/source, CG 또는 전류 진입 source->drain, 수동소자·pass 양방향)의 단순 사이클 전수, 시작 = 사이클 최소 노드. 수동소자만의 사이클 제외.
  개수·걸음 수가 `count_budget` 초과 -> `cycle_enumeration_over_budget`(기록만). 분류 (1.5) `bias_scc` / (2) `miller` / (3) `loop_view`((3-a)·(3-b)) / (4) `record_only`.
  끊는 점 = 복귀 구간 다음 첫 CS gate 후보 중 뷰 안 루프에서 가장 많이 나타나는 것(이름 전단사 불변). 극성 = CS gate->drain 반전 곱, 커패시터 경유 0.
  포트쌍 CM 루프 대응(R31): 루프 뷰의 루프 노드가 차동 출력 포트쌍 두 넷을 모두 포함하면 `cm_pair`, 기록은 `cm_loop_unconstrained`(info). 그 밖의 루프 뷰는
  `declared_loop_cuts` 에 gate 넷이 없으면 `undeclared_loop_constraint`(기록만).
* **L 동치류**: `S1v.l_classes` = S1 `rel_l_class` 마다 주인(DEC-17: tail -> 첫 전달 뷰 최전단 stage tail -> diode 기준 -> 이름 순)과 규칙 이름. 멤버 DC 역할 미확정이면 status
  review_needed. S1 의 `rel_l_class` 필드는 proposed 그대로다(소비자는 S1v 를 읽는다).
* **declared 대조**: `declared` = ((출처, (소자 이름 tuple, ...)), ...) 를 첫 전달 뷰 블록과 대조해 불일치를 `declared_stage_mismatch`(review_needed). 유도의 입력이 아니다(U-50).
* **기록과 정지**: `Finding.severity` ∈ review_needed / unsupported_rule_branch / info. `S1v.unsupported`(기록만)가 하나라도 있고 `stop_on_unsupported` 이면
  `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, `rule_branch` = 첫 분기, `branches`, `findings`). `False` 는 진단 모드(기록을 돌려받음). review_needed 는 정지가
  아니라 `S1v.review_needed` 로 GB4 앞 정지 대상.

### 10.3 불변량 (test 대상)

1. 같은 입력이면 `fp_of(structure_tables(s1v))` 가 같다(프로세스·`PYTHONHASHSEED`·netlist 순서 무관). 같은 키 `previous` 는 `is` 같은 객체.
2. 원소·넷 이름을 전단사로 바꾸면 모든 구조 필드(접지·셀·구동 종류·시작 셀·블록 키·역할·루프 노드 집합·분류·끊는 점·극점 노드·출력 방향)가 그 사상으로만 바뀐다. 예외(이름이 마지막
   tie-break 인 곳): L 동치류에 tail·diode 기준이 없을 때의 주인(DEC-17 '이름 정렬 첫 멤버'), 전달 뷰 순번(여기 이름 정렬 순서).
3. 접지 집합은 정적 집합의 초집합이고 여기 넷·감지 넷은 접지가 아니다. 순방향 넷 ⊆ 신호 넷. 모든 MOS 에 셀이 정확히 하나 있다.
4. 블록의 소유 넷(입력 경계 넷 제외)은 서로 겹치지 않는다(겹침은 복합 블록 합류 또는 `block_node_overlap`). 블록 키는 출력노드 정렬 tuple 이고 단일 출력 블록은 원소 1개.
5. stage 시작 셀은 순방향이고 바이어스 전류원 DC 역할이 아니며 CD 가 아니다. 미러 입력 노드를 gate 로 읽는 셀은 시작하지 않는다.
6. 극점 노드 = 뷰의 접지가 아닌 모든 넷(중복 없음). 버퍼 출력노드 포함.
7. 루프: 사이클은 단순(노드 반복 없음), 첫 노드가 사이클 최소 노드, 수동소자 하나·pass 묶음 하나로 되돌아오는 왕복 없음. `bias_scc` 는 순방향 노드를 하나도 지나지 않는다.
   `loop_view` 루프의 끊는 점은 그 루프 위 CS 셀의 gate 엣지다.
8. 정지 규칙: `기록만` 코드(`cell_ambiguous`·`pass_group_unsupported`·`gate_on_current_node`·`cs_output_low_impedance`·`buffer_multi_output`·`composite_dag_not_chain`·
   `composite_over_budget`·`loop_record_only`·`cycle_enumeration_over_budget`·`undeclared_loop_constraint`)가 있으면 `build_s1v` 가 기본 모드에서 정지한다.

### 10.4 설계와 다르게 정한 점 / 위임한 점

* `structure_count_budget(lut, kinds)` 는 합이 1 미만(kinds 가 비었거나 LUT 슬라이스 없음)이면 `ValueError` -- N_S 는 1 이상 int 여야 하므로 정의역 밖이다. `run_stage_a` 는 이를 잡아 `count_budget_undefined`(StructureUnresolvedError, exit 2)로 보고서에 쓴다.
* **U1b 로 미룬 것**: `structure.json` 의 `schema_version` 값 검사·알 수 없는 개념 거부(어휘는 U1b), `drive_kind` 사실 값 범위(voltage|current) 검사, 판정 규칙 J1~ 구현.
* S1v 저장은 core `GraphSnapshot` 이 아니라 frozen dataclass 트리(`S1v`)이고 재사용은 키(`S1v.key`) 일치로 한다.
* 입력 포트 role 문자열(`differential_input_p/n`, `differential_output_p/n`)과 spec 뷰 mode 문자열은 `s1v_values.py` 에 같은 값으로 복제했다(authoring 이 `__all__` 로 내보내지 않는다 -- U5 요청).
* declared stage 의 생산자(topology 의 `compensation.stage_devices` 등 태그 읽기)는 엔진 안에 없다(태그 키는 규칙 I·IC4 로 읽기 금지). `declared` 인자로만 받는다.
* 복합 블록은 묶음 경계를 J12 ratify 전 `composite_block_pending_ratify`(review_needed)로 남기고 격자 곱 Π 는 LUT 축이 필요해 U9 몫이다(`CompositeBlock.cells` = 밑).
* `virtual_ground` 는 U2 정준 라벨링·궤도가 들어오면 그 궤도로 대체한다.

### 10.5 어휘 요약과 library 9회로 정지 코드 (2026-10-08 U1 수정 뒤 실측)

* `Block.kind` ∈ {gain, buffer, composite}. AC 역할 ∈ {input, cascode, mirror, diode_load, pass, follower, tail, load}(계획 N3.2-6 의 input·cascode·follower·pass·load·tail 에
  mirror·diode_load 를 load 의 세분으로 더함. 옛 이름 `tail_source` 는 `tail` 로 바꿨다).
* `LClass.owner_rule` ∈ {tail_owner, tail_first_gain_stage, current_source_member, name_order}. `OutputDirection.topology` ∈ {push_pull, class_a, none}(none = 어느 방향도 σ 셀 없음).
  `DriveInfo.basis` 13종은 `s1v_values.py` `BASIS_*`. `ViewS1v.unreduced_diff` = ((소자, (축약 kind, forward), (비축약 kind, forward)), ...). `S1v.key` 는 7원소(마지막 = declared_loop_cuts 지문).
  `S1v.views` 순서 = 전달 뷰(순번 순) 다음 루프 뷰(끊는 점 정렬 순).

| 회로 | status / exit | 정지 코드(`unsupported_rule_branch`) | review_needed 코드 |
|---|---|---|---|
| two_stage_ota, two_stage_ota_sf, folded_cascode, common_gate_amplifier, pushpull_follower_buffer | ok / 0 | 없음 | 없음 |
| current_reuse_telescopic_ota | stopped / 2 | `cs_output_low_impedance` -- 루프 뷰 `loop:M37a:Voc` 의 N1a2a, N1b2b, Vx(출력노드가 다른 소자의 source) | loop_polarity_undefined, mixed_drive_signal_drain |
| ngcc_3stage_ff | stopped / 2 | `undeclared_loop_constraint` -- 루프 뷰 `loop:M8:V1`(차동 출력 포트쌍 없음, 안정도 제약 미선언) | composite_block_pending_ratify, loop_polarity_undefined |
| nmcnr_amplifier | stopped / 2 | `undeclared_loop_constraint` -- 루프 뷰 `loop:M201:NodeM2` | loop_polarity_undefined |
| sf_pushpull_output_opamp | stopped / 2 | `loop_record_only`(transfer:0 복합 diode 루프 9건), `composite_dag_not_chain`(N1112,N12 / N1516,N910,Y), `cs_output_low_impedance`(N1112, N1314, N1516, N17, N20, N56, N78, N910 -- 정정된 §1.7-4 로 새로 생김) | block_node_overlap(N17, N20: 버퍼 사슬 중간 노드와 부하 블록), composite_block_pending_ratify, mixed_drive_unresolved_group |

정지 4회로의 정지 사유는 J 규칙(U1b)이 닿기 전까지 의도된 `기록만` 정지다.
