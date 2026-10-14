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
| composite_diode.py [U1b] | 1 | `composite_diodes` | 복합 diode(DC 가지 걷기) 묶음·기준·캐스코드 기준(10.6) |
| feedforward_cells.py [U1b] | 1 | `feedforward_cells` | 주경로(D_max·slack)·feedforward 묶음(10.6) |
| loop_roles.py [U1b] | 1 | `loop_roles` | 루프 역할(루프 뷰 \| 중첩 Miller 내부 \| 복합 diode 내부 \| 바이어스 SCC, 10.6) |
| canonical_form.py [r11] | 1 | `canonical_form` | 완전 정준 라벨링·자기동형 생성자(4.7) |
| automorphism_orbits.py [r11] | 1 | `automorphism_orbits` | 생성자 -> 정점 궤도(4.7) |
| orbit_matching_crosstab.py [U17-1d] | 1 | `orbit_matching_crosstab` | MOS 궤도 ↔ matching 레코드 대조 표(4.8) |
| s1_symmetry.py [U17-1d] | 4 | `s1_symmetry`(`@compute_block`) | 대칭 블록: 구조 색·`graph/s1: orbits`·`current_symmetry`·d/s 자기 맞바꿈 정지(4.8) |
| s1_build.py | 5 | `build_s1` | 공개 진입점(빌드 순서·재사용) |

U2~U4 블록 10개는 서로 import 하지 않는다(값은 graph 필드로만 전달). 어느 것도 `device.bulk`·supplies 를 읽지 않는다.

## 1. `build_s1(doc, supplies_v=None, previous=None, column_limit=None, *, structure=None, marks=NO_MARKS) -> S1Graph`

- `marks` [U17-1d] = `SymmetryMarks`(사람 선언 표시 -- 입력 DC·원소 값·engine·선형 영역·노드 목표, 단계 A 는 `sizing.symmetry_marks(dc_inputs_from_spec(spec))`).
  `SymmetryMarks` 가 아니면 `TypeError`. 지문은 `S1Key.marks_fp`. 마지막 블록 `s1_symmetry(·, supplies, marks)`(4.8)가 이 표시를 읽는다.

- `structure` [U1b] = `load_structure_facts` 결과 또는 None. S1 이 소비하는 ratified 사실만(`dc_role` -> `s1_dc_roles` 규칙 4, `matching_pair` -> `s1_matching_groups` 레코드 추가)
  뽑아 두 블록의 extras 로 넘기고 그 지문을 `S1Key.facts_fp` 에 넣는다(사실이 다르면 S1 이 다르다). `drive_kind`·`ac_ground_exception`·`loop_role`·`feedforward_cell`·`stage_members` 는 S1v 쪽.

- 인자 검사: `doc` 이 `TopologyDoc` 아님 -> `TypeError`. `previous` 가 S1Graph 가 아니거나 권한표가 `S1_WRITERS` 와 다름 ->
  `TypeError`. `column_limit` 가 None 도 0 이상 int 도 아님(bool 포함) -> `TypeError`.
- 순서(고정): `supplies_declaration(supplies_v, doc.rails)` -> `s1_key(doc, supplies)` -> 재사용 판정 -> `s1_structure(base,
  doc.devices, doc.passives, doc.sources, 정렬 레일 tuple, doc.ports)` -> `s1_bulk(·, supplies)` -> `s1_dc_conduction` ->
  `s1_gs_groups` -> `s1_branches` -> `s1_dc_roles(·, dc 사실)` -> `s1_rel_vgs` -> `s1_rel_matching` -> `s1_matching_groups(·, matching_pair 사실)` -> `s1_gvgs` ->
  `s1_columns(·, column_limit)`
  -> `s1_rel_kcl` -> `s1_symmetry(·, supplies, marks)` -> `S1Graph(key, snapshot)`. `base` = `previous.snapshot`(있으면) 또는 `GraphSnapshot.empty(S1_WRITERS)`.
- 재사용 판정: `previous.key == key` 이고 (`column_limit` 가 None 이거나 `previous` 의 기둥 수 ≤ `column_limit`)이면
  `previous` 를 **그대로**(`is`) 반환, 블록 호출 0. 기둥 수가 상한을 넘으면 반환하지 않고 블록을 부른다 -- `s1_columns` 만
  입력(extras)이 바뀌어 다시 돌고 정지한다(1.1).
- 재사용(확정 사항 1·2·5):
  - 같은 doc·supplies_v·column_limit 로 `previous` 를 넘기면 같은 객체, 모든 블록 계수 변화 0.
  - supplies_v 만 바꿔 `previous` 를 넘기면 `s1_bulk` 와 `s1_symmetry`(레일 전위 표시·bulk 를 읽는다) 만 compute, 나머지 11 블록은 reuse(입력 버전 같음). node 레코드는
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

## 3. `s1_key(doc, supplies, facts=(), marks=NO_MARKS) -> S1Key(topology_fp, rule_fp, supplies_v_fp, facts_fp, marks_fp)`

- [U17-1d] `facts_fp` = `build_s1` 이 뽑은 S1 사실 tuple(`dc_role`·`matching_pair`)의 지문(둘 다 비면 `NO_FACTS_FP`), `marks_fp` = `fp_of(marks)`(`NO_MARKS` 면 `NO_MARKS_FP`) --
  40 §3.2-3 파이프라인 3, §6-8. `S1_RULE_FILES` 에 `canonical_form.py`·`automorphism_orbits.py`·`s1_symmetry.py` 가 든다.

- `topology_fp == doc.connectivity_fp`.
- `rule_fp` = `fp_of`(((basename, 파일 바이트(CRLF -> LF 정규화) sha256), ...) basename 정렬) over `S1_RULE_FILES`
  = (ac_ground_static, branches, bulk_default, columns, composite_diode [U1b], dc_conduction, dc_roles, gs_groups, gvgs_cycles,
  matching_groups, rel_kcl, rel_matching, rel_vgs, s1_build, s1_index, s1_structure, s1_values, supplies).py -- S1 필드 값을
  정하는 graph 파일 18개
  (s1_key.py·s1_model.py 제외). 같은 소스면 프로세스·`PYTHONHASHSEED` 와 무관하게 같다.
- `supplies_v_fp` = `fp_of(supplies)`, supplies None 이면 `NO_SUPPLIES_FP`(`"none"`). 전위 하나라도 다르면 다르다.
- `column_limit` 는 키에 들어가지 않는다(열린 결정 O1 기본안 -- 예산은 S1 키 밖).
- `facts_fp` [U1b] = S1 이 소비하는 ratified 사실(`dc_role`·`matching_pair`)의 `fp_of`, 사실이 없으면 `NO_FACTS_FP`(`"none"`). `s1_key(doc, supplies)` 는 이 값을 `NO_FACTS_FP` 로 두고 `build_s1` 이 덮어쓴다.
- `S1Key` 는 frozen dataclass(`==` 는 네 값 비교).

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
| (1c) [U1b] | 복합 diode 소자(`composite_diodes`, 10.6) | diode_reference | derived | ("1c", (gate, source), 묶음 멤버, (`diode_reference_composite`(기준) \| `diode_reference_composite_cascode`,)) |
| (5) | 나머지 | signal | derived | ("5", (gate, source), (), ()) |
| (4) [U1b] | ratified `dc_role` 사실(5) 뒤에 적용: 유도 status 가 review_needed(J-U3-c 그룹)면 override | 사실 값(복합 값은 diode_reference) | **ratified** | ("4", 유도 nets, 유도 group, (approval_id, 값)) |
| (4) [U1b] | 그 밖 소자: 사실 값 == 유도 값(복합은 기준·캐스코드 구분 포함) -> confirm | 유도 role 그대로 | **ratified** | 유도 evidence, basis + (approval_id,) |
| (4) [U1b] | 사실 값 != 유도 값 | 유도 role 그대로 | **review_needed** | 유도 evidence, basis + (`structure_fact_mismatch`, 유도 값) |

(1c) 는 (2) 보다 먼저 돈다 -- 같은 gate·source 묶음에 복합 diode 소자가 있으면 '기준이 있는 묶음'이라 나머지 멤버가 bias_current_source(rule 2)로 갈린다. `dc_role` 사실의 소자가 없으면(고아)
S1 에는 기록이 없고 `build_s1v` 가 `structure_fact_orphan` 을 올린다. `s1_dc_roles` 는 reads 에 `node.port_direction` 를 더한다(복합 diode 걷기가 포트 넷에서 멈춘다).

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
[U1b] extras = ratified `matching_pair` 사실 ((멤버 이름 tuple, approval_id, 근거 넷), ...) -- override: 같은 멤버의 `branch_symmetric` 그룹이 이미 유도돼 있으면 그 레코드를 status `ratified`
(evidence.basis = (approval_id,))로 바꾸고, 없으면 레코드를 더한다. 멤버가 소자 이름이 아닌 사실은 S1 에 기록하지 않고(`build_s1v` 가 `structure_fact_orphan`). extras 없이 부르면 사실 0.

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

**[r11] matching 그룹과 자기동형 궤도의 관계 (측정 2026-10-08, sizing CONTRACT 3.0b `dc_struct_colour` 의 dc_orbit)**: matching 그룹(레이아웃 짝짓기 -- 같은 kind·같은 source
등 부분 구조 조건)과 자기동형 궤도(회로 그래프 전체의 연결·kind·레일 전위·선언을 보존하는 전단사)는 **서로 다른 개념이고 포함 관계가 없다**. 9개 라이브러리 회로 +
합성 회로에서 확인: (1) 궤도가 둘 이상 원소인 회로는 `current_reuse_telescopic_ota` 하나(완전 차동, 2단자 수동소자를 무향으로 다루므로 R1(Vom→Voc)·R2(Voc→Vop)처럼 끝을 뒤집어 그려도 대칭이 선다 -- 22개 궤도 + 수동소자 쌍. 궤도: M10/M19, M17/M8, M1a/M1b, M2a/M2b, M3a/M3b, M4a/M4b,
R1/R2, Cc1/Cc2, CL1/CL2, 전반부-후반부 쌍 M11a/M20a … 등). 나머지 회로는 단일 출력이라 diff_pair 두 원소도 서로 다른 궤도(예 folded_cascode M1/M2: 드레인이 서로 다른
부하에 연결)이고 mirror/branch_symmetric 그룹도 궤도가 아니다. (2) 궤도 ⊆ 한 matching 그룹이 아닌 경우: current_reuse 의 M11a/M20a·M12/M21 … (차동 두 반쪽 사이의 대응,
matching 그룹은 한 가지 안의 짝만 본다)와 수동소자 쌍 R1/R2·Cc1/Cc2·CL1/CL2(matching 은 MOS 만). (3) matching 그룹이 한 궤도가 아닌 경우: 비율 mirror
(M38/M5/M66 -- 3 궤도, M18_bg/M6 …)와 current_reuse 의 diff_pair M37a/M37b(궤도 2: CMFB 쌍이라 입력 연결이 비대칭). 결론: θ 묶음은 궤도만 따른다(matching 그룹을
묶음 근거로 쓰지 않는다 -- 비율 mirror·비대칭 diff_pair 를 잘못 묶을 위험). 불일치는 결함이 아니라 개념 차이이며 matching 쪽 판정은 이 변경이 바꾸지 않는다.

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

### 4.7 [r11] 정준형 `canonical_form(source, element_marks=(), node_marks=()) -> Canonical` · `automorphism_orbits(canon) -> {정점: 궤도 id}` (설계 40 §6, 사용자 결정 2026-10-08)
- `source` = `.column(kind, field)` 를 가진 것(S1Graph, sizing 계산 블록 Projection). 읽는 열: `device.{element_class, kind, is_diode, pins, bulk}`, `node.{is_rail, port_direction}`. θ 무관.
- 그래프: 정점 = 넷 `("n", 넷)` ∪ 원소 `("e", 원소)`. 엣지 = 원소-넷 연결에 단자 라벨: MOS `c`(drain·source 같은 채널 라벨, U17-1d)·`g`·`b`(bulk 넷이 정해졌으면), 이상원 `t0`·`t1`(전류 방향), 그 밖 2단자(저항·커패시터)는 **방향 없는 `t`**
  (단자 순서를 색에 넣지 않는다). 처음 색: 원소 = (종류, element_class, kind, is_diode, 선언 표시), 노드 = (종류, is_rail, port_direction, 선언 표시). 선언 표시 형식은 sizing 3.0b.
- [U17-1d] 그래프: MOS 의 drain·source 엣지는 같은 채널 라벨 `c`(d/s 맞바꿈 허용, gate `g`·bulk `b` 는 그대로).
- `Canonical(wl, position, generators)`: `wl` = 선언 표시를 넣은 **같은 그래프**의 1-WL 색(정수, D-2), `position` = 정준 위치 0..n−1(정점마다 다름), `generators` = 자기동형 생성자 tuple(각각 움직인 정점만 `((정점, 상), ...)`).
  정준 라벨링 = individualization-refinement(nauty 식): 평형 분할의 가장 앞선 비단일 칸의 정점을 하나씩 개별화·정제, 잎의 증명서 cert 최소가 정준, 같은 cert 의 두 잎 사이 위치 대응이 자기동형
  (최저 공통 선조 마디로 가지치기). 이름은 탐색 순서에만 쓰이고 증명서·군은 이름과 무관하다.
- `automorphism_orbits`: 생성자들이 만드는 군 아래 정점 동치류. 궤도 id = 구성원의 정준 위치 최솟값(같은 궤도 ⇔ 같은 값). 생성자가 없으면 정점마다 자기 위치.
- 불변식(test 가 확인할 성질): (a) 이름 전단사·원소 순서 섞기에 `automorphism_orbits` 가 불변; (b) 생성자는 모두 자기동형(이웃 다중집합·처음 색 보존, 단자 라벨 보존);
  (c) 손 그래프 기지 군(링 n 개 한 궤도, 경로, C6⊔2×C3 에서 1-WL 색 같아도 궤도 2, 큐브, Petersen) 및 소규모 전수 순열 대조; (d) 단일 종단 OTA 차동쌍 두 멤버는 서로 다른 궤도,
  완전 차동 쌍은 같은 궤도; (e) 저항 terminals 순서를 뒤집어도 궤도 분할 동일; (f) 선언 표시가 다른 두 원소는 다른 궤도; (g) 결정론; (h) 궤도 ⊆ `wl` 클래스.

### 4.8 [U17-1d] 대칭 블록 `s1_symmetry`·`orbit_matching_crosstab` (설계 40 §6-5·7·8, §2.4.1 '대칭 탐색', §2.4.8, 사용자 결정 2026-10-12 "6. 가"·D-1~D-3)

- reads `device.{bulk, element_class, is_diode, kind, pins}`, `node.{is_rail, port_direction}`, `graph.dc_pruned`; extras `(supplies, marks)`.
  writes `device.dc_colour`·`node.dc_colour`(int), `graph.orbits`(`Orbits(devices, nodes)`), `graph.current_symmetry`(`CurrentSigns(generators)`).
- **그래프 하나**(D-2): 선언 표시(노드 = 레일 전위 `rail_v`(supplies)·노드 목표 `target_v`·입력 포트 `input_dc_v`, 원소 = `marks.elements`)를 넣은 색 그래프 하나에서
  `canonical_form` 이 `wl`·정준 위치·생성자를 모두 정한다. 그 그래프에서 MOS 의 d·s 엣지는 같은 라벨 `c`(4.7 갱신). 같은 S1 에서 이 블록 밖 어디서도 정준형을 다시 계산하지
  않는다(L 동치류 `name_order` 예외·search 묶음·sizing 순서가 모두 이 필드를 읽는다).
- `dc_colour` = (`wl`, 정준 위치) 정렬 순위(정점마다 유일). `orbits` = 궤도 id(구성원 정준 위치 최솟값). `current_symmetry.generators[i]` = 생성자 i 아래 움직이거나 방향을 뒤집는
  원소의 (원소, 상, 부호) 이름순: 부호 −1 = MOS drain 이 상 MOS drain 으로 가지 않음, 방향 없는 2단자 수동소자 첫 단자 넷이 상의 첫 단자 넷으로 가지 않음; 이상원 +1.
- 정지: 군의 원소가 전도 MOS(가지치기 안 된 MOS) 하나를 자기 자신으로 보내며 d/s 를 맞바꾸면 `StructureUnresolvedError`(reason `unsupported_rule_branch`,
  rule_branch `ds_self_swap_zero_current`, devices, detail generators). (원소, ±방향) 쌍 궤도의 union-find 로 군 전체에서 판정.
- 소비자: `l_equivalence_classes`(궤도), sizing `build_kernel_context`(같은 블록을 `symmetry_marks(inputs)` 로 재호출 -- 같은 표시면 재사용), search `current_symmetry`·`orbit_ties`·
  `canonical_order`·`search_domain`(궤도·부호), metrics `achievability`(궤도).
- `orbit_matching_crosstab(s1) -> OrbitMatchingCrosstab(orbits, records)`: MOS 궤도마다 걸친 matching 레코드, 레코드마다 걸친 MOS 궤도(40 §6-5). 단계 A 보고서 키
  `orbit_matching_crosstab`. `findings` = `diff_pair_orbit_split`(review_needed, 40 §6-5 (나') v1.8): `diff_pair` 두 멤버가 다른 궤도이고 (a) 출력 포트 role 에
  `differential_output_p`·`_n` 이 둘 다 있으며 (b) 두 멤버 gate 넷의 포트 role 이 `differential_input_p`·`_n` 일 때만. 그 밖은 표에 기록만. 단계 A 가 review 목록에 올린다.
- [U17-1d] 혼재 노드 구동 종류(`drive_kinds`, 41 §1.5-4 C-1 + 보완 (가)): (i) source 쪽 소자 drain 이 그 뷰 교류 접지이고 gate 가 순방향 신호 넷이면 전압(근거 `follower`),
  (ii) 아니면 drain 쪽 소자 gate 가 순방향 신호 넷이면 전류(근거 `cascode`), 그 밖 전압(`mixed_bias_drain`). 옛 DC 역할 판정과 기록 `mixed_drive_signal_drain`·`mixed_drive_unresolved_group` 삭제.

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
ngcc·nmcnr·pushpull·sf = topology `_declared_target_spec.supplies_v`(`_comment` 제외; nmcnr·pushpull·sf
vdd 1.8/vss 0/agnd 0.9 -- nmcnr 은 2026-10-12 사용자 정정 Q8 로 옛 vdd 0.9/vss −0.9 에서 바뀌고 CL·RL 끝이 vss -> agnd, 아래 nmcnr 행은 Q8 뒤 손 재측정). column_limit None. 9회로 모두 `unsupported` 열 `()`, 정지 0(오정지 0).

### 7.1 S1 기본 필드

| 회로 | node | 레일 | MOS(n/p) | 수동 | 이상원 | is_diode 참 | gate_only_undriven | 포트 in/out | bulk(default_rule) |
|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 7 | gnd, vdd | 3 (2/1) | 0 | 0 | 0 | VNBias1, VNBias2, VPBias1 | 1/1 | gnd 2, vdd 1 |
| current_reuse_telescopic_ota | 37 | gnd, vdd | 51 (24/27) | 12 | 1 | 16 (M11a, M11b, M14a, M14b, M18_bg, M20a, M20b, M23a, M24b, M36a, M36b, M39, M40, M57, M64, M66) | 없음 | 2/2 | gnd 24, vdd 27 |
| folded_cascode | 14 | gnd, vdd | 13 (8/5) | 1 | 1 | 4 (M7, M9, MN, MP) | bias3 | 2/1 | gnd 8, vdd 5 |
| ngcc_3stage_ff | 13 | gnd, vdd | 16 (9/7) | 3 | 0 | 3 (M3, M6A, M9) | VBN, VBP | 2/1 | gnd 9, vdd 7 |
| nmcnr_amplifier | 19 | agnd, vdd, vss | 15 (7/8) | 5 | 0 | 2 (M108, M203) | VB1~VB5 | 2/1 | vss 7, vdd 8 (agnd 0) |
| pushpull_follower_buffer | 9 | agnd, vdd, vss | 6 (3/3) | 1 | 0 | 0 | VNB1, VPB1 | 1/1 | vss 3, vdd 3 (agnd 0) |
| sf_pushpull_output_opamp | 23 | agnd, vdd, vss | 22 (11/11) | 5 | 1 | 1 (M4) | 없음 | 2/1 | vss 11, vdd 11 (agnd 0) |
| two_stage_ota | 10 | gnd, vdd | 7 (4/3) | 3 | 0 | 1 (M3) | bias | 2/1 | gnd 4, vdd 3 |
| two_stage_ota_sf | 10 | gnd, vdd | 9 (6/3) | 2 | 0 | 1 (M3) | bias | 2/1 | gnd 6, vdd 3 |

two_stage_ota_sf 는 supplies_v 를 넘기지 않으면 bulk 9개 모두 undetermined(needs_supplies_v).
(옛 7.2 '3회로 거부·`passive_elements: []` 변형 참고값'은 topology 정정 b9c7042 로 사실이 아니게 되어 지웠다.)

### 7.2 다중 도메인 판정 실측

| 회로 | 레일(전위) | 채널 레일 | {최저, 최고} | 판정 |
|---|---|---|---|---|
| 2레일 6회로 | vdd/gnd(1.8/0) | 두 레일 | 같은 두 레일 | 통과 |
| nmcnr_amplifier (Q8 뒤) | vdd 1.8, vss 0, agnd 0.9 | vdd, vss (agnd 는 CL·RL 단자만) | vss, vdd | 통과 |
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
| nmcnr_amplifier | Rm (1) | 16 | -- (Q8 뒤 RL 은 Vout–agnd 라 M301 과 갈림; 옛 M301∥RL 15 segment) | 4 / 4 | 12 / 12 | **11 / 11** | agnd–vdd 1, agnd–vss 1, vdd–vss 9 | 0 | 0 |
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
| nmcnr_amplifier | 3 | 2 | 4 (Q8 전 5: vss–Vout–vdd 가지가 Vout 분기로 갈림) | 3 | {M102, M103} derived | 0 | 0 | 4 |
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

[U17 ①-b] (설계 40 §2.4.2·§2.4.8 v1.9.1 D1) S1v 는 묶음 객체가 아니라 S0 수준 graph 필드다: 레코드 `("graph", S1V_KEY="s1v")` 의 `views`(ViewS1v tuple -- 블록·복합 블록·극점 노드·루프·끊는 점은
뷰 안 칸), `l_classes`, `findings`(뷰 밖 기록), `declared`(((출처, stage 묶음 수), ...)), `applied_facts`((개념, 대상) tuple). writer = 계산 블록 `s1v_fields`(writer 이름 `build_s1v`,
reads = S1 필드 전부 `S1_READS`, extras = (spec 판정 제약, N_S, declared, 사실, stale 기록, 선언 루프 끊는 넷)) -- 입력 버전이 같으면 재사용(옛 `previous`·`S1v.key` 재사용은 없앴다).
권한표 `S1V_WRITERS` = `S1_WRITERS` + S1v 필드 + 결합 필드(11절). `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), stop_on_unsupported=True) -> S1Graph`
(같은 S1 키, 스냅샷 권한표를 `S1V_WRITERS` 로 넓혀 블록을 부른 것; `s1` 은 권한표가 S1_WRITERS 를 덮는 S1Graph -- S0 수준 스냅샷 위의 것 포함). 기록 묶음은
`s1v_findings(source) -> (all_findings, review_needed, unsupported)`(옛 `S1v.all_findings`·`review_needed`·`unsupported` 속성), 구조 표는 `structure_tables(source)`(필드를 읽는다 -- 옛 `key` 칸 없음,
`facts_applied` -> `applied_facts`). `build_s1(previous=)` 는 권한표가 S1_WRITERS 를 **덮는** 스냅샷을 받는다(S0 수준 스냅샷 포함). 표는 이 단락과 같은 현재 서명이다.

| 이름 | 설명 |
|---|---|
| `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), stop_on_unsupported=True) -> S1Graph` | 진입점. `s1` = `build_s1` 결과(권한표가 `S1_WRITERS` 를 덮는 S1Graph), `spec` = `SizingSpecDoc` 또는 None(기본 전달 뷰만). `count_budget` = 계수 예산 N_S(1 이상 int, bool 거부 `TypeError`). 결과는 S1v 필드를 쓴 같은 S1 키의 S1Graph(`previous` 인자·`S1v` 묶음 객체는 없다) |
| `ViewS1v`, `ViewSeed`, `Block`, `CompositeBlock`, `Loop`, `LClass`, `Finding`, `StructureFact`, `CellInfo`, `DriveInfo`, `PoleNode`, `PassBundle`, `OutputDirection` | frozen dataclass(`fp_of` 가능). 필드 뜻과 어휘(`Block.kind`·AC 역할·`DriveInfo.basis`·`LClass.owner_rule`·`OutputDirection.topology`·`unreduced_diff` 형식)는 `s1v_values.py` docstring 이 정본이고 10.5 에 요약한다 |
| `load_structure_facts(path, topology_fp, rule_fp, net_names=()) -> StructureFacts` | `structure.json` ratified 사실 로더(파일 없음 = 사실 0, 형식 위반 = `SchemaRejectedError` gate `structure_json`, 해시 불일치 = 사실 미적용 + `structure_fact_stale` review_needed). [U1b] `schema_version`·concept 어휘·값 범위·`->` 모호 거부는 10.6 |
| `structure_tables(source) -> dict` | `source`(S1v 필드를 가진 S1Graph)의 필드를 읽어 만든 JSON 으로 쓸 수 있는 구조 표(뷰·셀·구동 종류·블록·극점 노드·루프·L 동치류·기록) |
| `s1v_rule_fp() -> str` | S1v 규칙 코드 지문(`S1V_RULE_FILES` 바이트). `structure_rule_fp()` 가 부른다(재사용은 블록 입력 버전이 정한다 -- 옛 `build_s1v` 재사용 키는 없다) |
| `structure_rule_fp() -> str` [U1b] | `s1v_rule_fp()` + S1 쪽 소비 파일(`STRUCTURE_RULE_EXTRA_FILES` = composite_diode·dc_roles·gs_groups·matching_groups) 지문. `structure.json` 의 `rule_hash` |
| `composite_diodes(projection)`, `feedforward_cells(model, view, blocks, cells, stage)`, `loop_roles(view_loops, transfer_views, declared_pm_views)` [U1b] | J 구조 규칙(10.6). 모두 단계 A 경로(`build_s1` -> `s1_dc_roles`, `analyze_view`)에서 불린다 |
| `LoopRole`, `FeedforwardCell`, `FfRatioCandidate`, `CompositeDiode`, `FeedforwardResult` [U1b] | frozen dataclass |

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
  끊는 점 = 복귀 구간 다음 첫 CS gate 후보 중 뷰 안 루프에서 가장 많이 나타나는 것(이름 전단사 불변). 극성 = CS gate->drain 반전 곱, 커패시터 경유 0(`ac_only`, [U1b] 10.6).
  포트쌍 CM 루프 대응(R31): 루프 뷰의 루프 노드가 차동 출력 포트쌍 두 넷을 모두 포함하면 `cm_pair`, 기록은 `cm_loop_unconstrained`(info). 그 밖의 루프 뷰는
  `declared_loop_cuts` 에 gate 넷이 없으면 `undeclared_loop_constraint`(기록만).
  **선언 끊는 넷 = 엔진 루프 뷰의 끊는 gate 넷**(U1b-jrules 결정): spec 루프 뷰 선언의 `cuts` 는 입력 포트가 아니라 엔진 루프 뷰 `cuts[*][1]`(단계 A 보고서 `views[]` 에 나오는 끊는 gate 넷)를 가리켜야 한다.
  단계 A(`pipeline.stage_a`)는 spec `feedback` 소자에서 유도된 β 루프 선언(`ViewDecl.beta == declared`; 입력 포트 절단)을 `declared_loop_cuts` 와 이 대조에서 제외한다(내부 루프 뷰가 아니다). 나머지 `declared_loop_cuts` 를 엔진 루프 뷰 끊는 넷 집합과 대조해 어느 뷰에도 맞지 않은 선언 넷마다 `loop_cut_unmatched`(review_needed, 뷰 "", subject = 그 넷)를 보고서 `review_needed` 에 올린다(`build_s1v` 결과 S1Graph 의 `graph/s1v` 필드 `findings` 에는 넣지 않는다) -- 맞지 않는 선언이 조용히 무동작이 되지 않게 한다.
* **L 동치류**: `graph/s1v` 필드 `l_classes`(레코드 `("graph", S1V_KEY)`) = S1 `rel_l_class` 마다 주인(DEC-17: tail -> 첫 전달 뷰 최전단 stage tail -> diode 기준(복합 diode 포함) -> [U1b] `main_path_signal` -> 이름 순)과 규칙 이름. 멤버 DC 역할 미확정이면 status
  review_needed. S1 의 `rel_l_class` 필드는 proposed 그대로다(소비자는 S1v 를 읽는다).
* **declared 대조**: `declared` = ((출처, (소자 이름 tuple, ...)), ...) 를 첫 전달 뷰 블록과 대조해 불일치를 `declared_stage_mismatch`(review_needed). 유도의 입력이 아니다(U-50).
* **기록과 정지**: `Finding.severity` ∈ review_needed / unsupported_rule_branch / info. `s1v_findings(source)` 의 `unsupported`(기록만)가 하나라도 있고 `stop_on_unsupported` 이면
  `StructureUnresolvedError`(detail reason `unsupported_rule_branch`, `rule_branch` = 첫 분기, `branches`, `findings`). `False` 는 진단 모드(기록을 돌려받음). review_needed 는 정지가
  아니라 `s1v_findings(source)` 의 `review_needed` 로 GB4 앞 정지 대상.

### 10.3 불변량 (test 대상)

1. 같은 입력이면 `fp_of(structure_tables(s1v))` 가 같다(프로세스·`PYTHONHASHSEED`·netlist 순서 무관).  (`build_s1v` 에는 `previous` 인자가 없다 -- 재사용은 계산 블록 입력 버전 일치로 판정하고, 같은 입력의 두 번째 호출은 블록 호출 0 이다.)
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
* **U1b 로 미룬 것 -> 닫힘**: `schema_version` 값 검사·알 수 없는 개념 거부·`drive_kind` 값 범위·J 판정 규칙은 U1b 가 구현했다(10.6).
* [U17 ①-b 대체] S1v 저장은 core `GraphSnapshot` 의 S0 수준 필드(`graph/s1v`)이고 재사용은 계산 블록 `s1v_fields` 의 입력 버전 일치로 한다(설계 40 §2.4.2, v1.9.1 D1).
* 입력 포트 role 문자열(`differential_input_p/n`, `differential_output_p/n`)과 spec 뷰 mode 문자열은 `s1v_values.py` 에 같은 값으로 복제했다(authoring 이 `__all__` 로 내보내지 않는다 -- U5 요청).
* declared stage 의 생산자(topology 의 `compensation.stage_devices` 등 태그 읽기)는 엔진 안에 없다(태그 키는 규칙 I·IC4 로 읽기 금지). `declared` 인자로만 받는다.
* 복합 블록은 묶음 경계를 J12 ratify 전 `composite_block_pending_ratify`(review_needed)로 남기고 격자 곱 Π 는 LUT 축이 필요해 U9 몫이다(`CompositeBlock.cells` = 밑). [U1b] feedforward 합류는 복합 블록이 아니다(10.6).
* `virtual_ground` 는 U2 정준 라벨링·궤도가 들어오면 그 궤도로 대체한다.

### 10.5 어휘 요약과 library 9회로 정지 코드 (2026-10-08 U1 수정 뒤 실측)

* `Block.kind` ∈ {gain, buffer, composite}. AC 역할 ∈ {input, cascode, mirror, diode_load, pass, follower, tail_source, load}(계획 N3.2-6 의 input·cascode·follower·pass·load·tail 에
  mirror·diode_load 를 load 의 세분으로 더함. 계획의 `tail` 은 값 `tail_source` 로 쓴다 -- 문자열 `tail` 은 library 넷 이름과 같아 구조 규칙 E 가 코드 리터럴로 거부한다).
* [U1b-jrules] 블록 구성: 복합 diode 묶음 내부 gate 넷(미러 입력)을 읽는 셀은 묶음 진입 넷을 소유한 블록의 멤버로 이어지고(`blocks._owner_of`), 그 미러 출력 넷이 낮은 임피던스(다른 셀이 구동하는 팔로워 출력 등)이면 측면 주입(K8)이라 이어지지 않는다. 다른 stage 블록이 겹친 넷을 한 블록 멤버가 입력으로 읽으면 내부 노드 측면 주입이라 읽는 블록에 합친다(`_absorb_side_injections`). FF 합류 노드는 주경로 셀을 멤버로 가진 블록의 출력노드만이다. L 주인 `name_order` 동률이 한 자기동형 궤도(`automorphism_orbits`, S1 구조만)이면 review 를 올리지 않는다(status derived).
* `LClass.owner_rule` ∈ {tail_owner, tail_first_gain_stage, current_source_member, main_path_signal [U1b], name_order}. `OutputDirection.topology` ∈ {push_pull, class_a, none}(none = 어느 방향도 σ 셀 없음).
  `DriveInfo.basis` 13종은 `s1v_values.py` `BASIS_*`. `ViewS1v.unreduced_diff` = ((소자, (축약 kind, forward), (비축약 kind, forward)), ...). [U17 ①-b] 재사용 키 칸은 없다(옛 `S1v.key` 7원소 삭제): 재사용은 계산 블록 `s1v_fields`
  의 입력 버전(`fp_of((이름, code_hash, 투영 지문))`, 투영 지문 = S1 읽기 열 + extras -- extras 마지막 = `declared_loop_cuts`)이 같을 때다(`core/compute_block.py`·`core/projection.py`).
  `graph/s1v` 필드 `views`(레코드 `("graph", S1V_KEY)`) 순서 = 전달 뷰(순번 순) 다음 루프 뷰(끊는 점 (소자, gate 넷) 정렬 순)(`s1v_fields.py`).

| 회로 | status / exit | 정지 코드(`unsupported_rule_branch`) | review_needed 코드 |
|---|---|---|---|
| two_stage_ota, two_stage_ota_sf, folded_cascode, common_gate_amplifier, pushpull_follower_buffer | ok / 0 | 없음 | 없음 |
| current_reuse_telescopic_ota | stopped / 2 | `cs_output_low_impedance` -- 루프 뷰 `loop:M37a:Voc` 의 N1a2a, N1b2b | drive_inherit_cycle(Vbias2), mixed_drive_signal_drain(M1a/N1a2a, M1b/N1b2b) -- 뷰 한정 `ac_ground_exception`(Vbias2) 사실이 닫는다 (U1b 뒤) |
| ngcc_3stage_ff [U1b] | stopped / 2 (spec 에 `pm_ss_deg` 가 있으면 ok / 0) | `undeclared_loop_constraint`(사유 `compensation_internal_needs_overall_pm`: 전체 `pm_ss_deg` 미선언) | 없음 (feedforward 2묶음, 루프 뷰 0, 복합 블록 0) |
| nmcnr_amplifier [U1b] | stopped / 2 (spec 에 `pm_ss_deg` 가 있으면 review_needed / 2) | `undeclared_loop_constraint`(같은 사유) | `l_owner_name_order`({M104, M105} -- 대칭 쌍이라 규칙으로 못 가르는 동률) |
| sf_pushpull_output_opamp [U1b] | ok / 0 | 없음 (복합 diode 6소자 -> 이득 블록 {Y} + 버퍼 블록 {vout}, 루프 3개 `composite_diode_internal`) | 없음 |

정지 회로의 정지 사유는 사실(`structure.json`)이나 spec 선언이 닿기 전까지 의도된 `기록만` 정지다(U1 시점의 sf 정지 `loop_record_only`·`composite_dag_not_chain` 등은 10.6 으로 닫혔다).

### 10.6 [U1b] J 공동분석 구조 규칙과 structure.json 사실 소비 (설계 41 §1.12·§1.13, 40 §3.2-3, 사용자 결정 2026-10-08)

* **[U17-1d] concept `l_owner`**(C-3, 사용자 결정 2026-10-12 "7절 권고대로"): subject = L 동치류 멤버 이름 정렬 JSON 배열(둘 이상), value = 주인 소자 이름(로드 검사는 형식만).
  `build_s1v` 가 `l_equivalence_classes(..., owner_facts)` 로 넘기고 멤버가 엔진 유도 동치류와 같고 주인이 멤버면 주인 = 사실(`owner_rule` `ratified_fact`, status ratified -- 41 §1.12.5
  규칙 1~4 를 덮음, `applied_facts` 에 남김). 멤버가 겹치는 동치류가 있으나 다르거나 주인이 멤버가 아니면 `structure_fact_mismatch`, 겹치는 동치류가 없으면 `structure_fact_orphan`.
  소비자(sizing `l_ties`, metrics `achievability`)는 derived·ratified 동치류를 L 공유로 쓴다. `name_order` 동률 예외의 궤도는 S1 필드 `graph/s1: orbits`(4.8, 정준형 재계산 없음).

모든 규칙은 connectivity 만 읽는다(회로·소자·넷 이름 없음). 사실 파일은 이 단위가 쓰지 않는다(코드 병합 뒤 `structure_rule_fp()` 로 쓴다).

| 규칙 | 파일 / 호출 | 산출 | 소비처 |
|---|---|---|---|
| 복합 diode D1 (§1.12.1) | `composite_diode.composite_diodes(projection)` <- `s1_dc_roles` | `CompositeDiode(members, reference, cascode_members, walk)` | `device.dc_role` rule `1c`(evidence.group = 묶음, basis[0] = `diode_reference_composite` 또는 `diode_reference_composite_cascode`); `net_model`: `diode_nodes`(복합 gate 넷 포함)·`composite_mos`·`composite_bundles`·`composite_internal`; `cells`(묶음 MOS = `diode_load`); `drive_kind`(미러 입력·묶음 내부 넷은 구동 판정 제외); `stage_bfs`(diode 단자 비용 0); `blocks`(묶음 MOS = `diode_load` 멤버, 소유 넷은 늘리지 않음); `loop_classify`(1.6) |
| feedforward (§1.12.2) | `feedforward_cells.feedforward_cells(model, view, blocks, cells, stage)` <- `analyze_view`(전달 뷰만, 이득 블록 구성 뒤) | `FeedforwardResult(main_path, cells[FeedforwardCell], ratio_candidates[FfRatioCandidate], findings)`. 비용 정의의 단일 출처 = `StageResult.edges` | 묶음이 있으면 `analyze_view` 가 그 소자(cells + bias_cells + load_cells)를 뺀 모형(`_without`)에서 셀 이하를 다시 구한다(주경로 블록 사슬, 복합 블록 0). `ViewS1v.main_path`·`feedforward`·`ff_ratio_candidates`. `main_path_ambiguous`(review_needed)는 feedforward 후보가 있을 때만, 입력마다 센다 |
| 중첩 Miller 내부 (§1.12.3) | `loop_roles.loop_roles(view_loops, transfer_views, declared_pm_views)` <- `analyze_view`(전달 뷰) | `LoopRole(loop_id, role, view, reason)`, role ∈ `LOOP_ROLES`. `compensation_internal` 의 reason = `overall_pm_declared` 또는 `compensation_internal_needs_overall_pm` | 해당 사이클 classes 의 `loop_view` 를 `compensation_internal` 로 바꾸고 끊는 점을 루프 뷰 후보에서 뺀다. 전체 `pm_ss_deg` 미선언이면 기존 `undeclared_loop_constraint`(기록만)를 그 reason 으로 전달 뷰에 유지. `ViewS1v.loop_roles`(뷰마다 칸 -- `graph/s1v` 에 뷰 밖 모음 필드는 없다, 사실 대조는 모든 뷰의 `loop_roles` 를 모아 쓴다 `s1v_fields.py`) |
| 루프 극성 (§1.12.4) | `polarity.loop_polarity`, `view_analysis._loops`(루프 뷰 후보별 DC 극성 모음), `s1v_fields._polarity` | `Loop.ac_only`(커패시터 경유, 극성 0), `ViewS1v.polarity`(루프 뷰: DC 사이클 극성; 갈리면 0 + `loop_polarity_conflict`, DC 사이클이 없으면 0 + `loop_polarity_undefined`), info `loop_polarity_ac_only`, `ViewS1v.compensation_candidates` | 극성 기록은 루프 뷰에만 붙는다 |
| L 주인 `main_path_signal` (§1.12.5) | `l_classes.l_equivalence_classes(s1, model, views, gain_views)` | `LClass.owner_rule == "main_path_signal"`. `name_order` 는 status review_needed + `l_owner_name_order` | gain 제약(`gain_ss_db`) 전달 뷰(없으면 첫 전달 뷰)의 stage 시작 셀(feedforward 묶음 제외) |
| 뷰 한정 교류접지 (§1.12.6) | `ac_ground_view.view_ac_ground(..., exceptions)` <- `analyze_view(exceptions=)` | `AcGround.exceptions` -> `ViewS1v.ac_ground_exceptions` | `ac_ground_exception` 사실(대상 넷, 값 뷰 id)이 가리킨 뷰에서만 |

**structure.json 사실 소비**(40 §3.2-3): concept 7개 -- `drive_kind`(override) · `stage_members`(declared 대조) · `dc_role`(override: 유도 status 가 review_needed 인 소자, 그 밖은 confirm) · `loop_role`(confirm) ·
`feedforward_cell`(confirm; 값 `ff|ff_bias|ff_load:<탭>-><merge>`, 대상 = 소자) · `ac_ground_exception`(override, 그 뷰만) · `matching_pair`(대상 = 이름 둘 이상의 정렬 JSON 배열, 값 `branch_symmetric`, override:
같은 멤버의 `branch_symmetric` 그룹을 status ratified 로 올리거나 레코드를 더한다). `dc_role`·`matching_pair` 는 `build_s1(structure=)` 가 S1 안에서 적용하고(`S1Key.facts_fp`), 나머지는 `build_s1v` 가 쓴다.
대조(`s1v_fields._fact_findings`): 적용·일치 -> `graph/s1v` 필드 `applied_facts` 의 (concept, subject); 유도 값과 다름 -> `structure_fact_mismatch`(review_needed, detail = concept·subject·derived·ratified);
대상이 없음(소자·넷·루프·뷰·feedforward 소자를 엔진이 만들지 않음) -> `structure_fact_orphan`(review_needed). `drive_kind` 는 넷이 topology 에 없을 때만 orphan.
confirm 이 일치한 유도 레코드는 status 를 올린다: `dc_role` -> `DcRole.status == "ratified"`(+ evidence.basis 에 approval_id), `loop_role` -> `LoopRole.status/approval_id`, `feedforward_cell` -> 묶음의 모든 소자에
일치하는 사실이 있을 때 `FeedforwardCell.status/approval_id`(`s1v_fields._ratify_derived`). 구조로 못 가르는 DC 역할 그룹(J-U3-c)은 사실이 없으면 `dc_role_unresolved_group`(review_needed, 그룹 단위)을 올린다.

**로더 거부**(`SchemaRejectedError`, gate `structure_json`, hit rule): `structure_schema_version`(값이 `STRUCTURE_SCHEMA_VERSION` = `"1"` 이 아님), `structure_concept_unknown`(닫힌 어휘 `CONCEPTS` 밖),
`structure_value_range`(concept 별 값·대상 어휘 위반), `structure_value_ambiguous`(`feedforward_cell` 사실이 있는데 `net_names` 중 `->` 를 품은 넷이 있음) + 기존 키·status·evidence 위반. stale 판정은 `structure_rule_fp()`.

**단계 A**(pipeline CONTRACT 1): `load_structure_facts(path, doc.connectivity_fp, structure_rule_fp(), net_names)` -> `build_s1(structure=)` -> `build_s1v(structure=, declared_loop_cuts=)`.

**불변량 [U1b]**: (a) 복합 diode 소자의 gate 넷은 `diode_nodes` 에 있고 묶음의 MOS 멤버 셀은 항상 `diode_load`. (b) feedforward 묶음 소자는 `ViewS1v.blocks` 의 어느 역할에도 없고 `cells` 에는 있다.
(c) `compensation_internal` 루프의 끊는 점은 `ViewS1v.cuts` 에 없고 루프 뷰가 생기지 않는다. (d) `Loop.ac_only` 이면 `polarity == 0`. (e) 사실이 없을 때 library 9회로의 D1 발동 = sf {M5, M6, M7, M8, M13, M14},
파일럿 {M58, M63}, 나머지 0; feedforward = ngcc 2묶음, 나머지 0.

---

## 11. GB3 -- 결합 변수 y와 기둥↔블록 매핑표 (U10, 설계 40 §3.3, 41 §0 단계 A4, 계획 DEC-71 (2)(7))

파일: `coupling_values.py`(값 형식·어휘), `column_block_map.py`(진입 `column_block_map(s1, views) -> (rows, bias_columns)`), `coupling_vars.py`(계산 블록 `coupling_vars`,
writer `coupling_vars`: reads = S1 필드 전부 + `graph/s1v: views·l_classes`, writes S0 수준 필드 `("graph", COUPLING_KEY="coupling")`: `vars`·`column_block_map`(행 tuple)·`bias_columns`
-- [U17 ①-b] 설계 40 §2.4.8 v1.9.1 D8, 묶음 `Coupling`·`ColumnBlockMap` 없음). 호출자: `pipeline.run_stage_a` A4(필드를 읽어 보고서 `coupling` 키). 소비자: U15 층 0 조립(41 §5.5).
`column_unassigned` 정지는 블록에서 전파된다(필드를 쓰지 않는다).

### 11.1 값 형식
* `BlockRef(view, key)` -- 뷰 id 와 블록 키(출력노드 이름 정렬 tuple). 같은 키의 블록도 뷰가 다르면 다른 블록. 정렬 가능(frozen order).
  **의사 블록(바이어스 기둥)**: 어느 블록에도 속하지 않는 소자만으로 된 기둥(`bias_columns`)은 K1·K2·K4 판정에서 블록 하나로 센다. 표현 = `BlockRef(view, ("bias:<기둥 id>",))` (`coupling_values.BIAS_PREFIX`) --
  판정이 뷰 단위라 의사 블록은 모든 뷰에 기둥마다 하나씩 놓이고, 바이어스 기둥 소자는 모든 뷰에서 그 키를 갖는다. `repr` 에 `bias:<기둥 id>` 가 든다. 기둥 id 는 열거 순서에 따르므로
  이름 전단사 불변은 '기둥 소자 집합'으로 대응시켜 본다(레코드의 members·nets 는 이름만으로 정해져 영향 없음). 매핑표 행의 `block` 은 계속 None(`bias_column`).
* `ColumnBlockRow(column, block, device, shared, basis)` -- `column` = S1 기둥 id 또는 None(어느 기둥에도 안 든 블록 멤버, 예: 커패시터), `block` = BlockRef 또는 None(바이어스 기둥),
  `basis` ∈ `block_member | column_mate | bias_column`. 필드 `column_block_map` = 행 tuple -- (column(None 먼저), block, device) 순, 필드 `bias_columns` = 바이어스 기둥 id 정렬 tuple.
* `CouplingVar(kind, members, blocks, domain, init_rule, nets)` -- 40 §3.3 레코드에 `nets` 를 더했다. 필드 `vars` -- (kind, members, nets, domain) 순, 같은 키 중복 없음.

### 11.2 매핑표 규칙(DEC-71 (2))
* 소자 범위 = 어느 DC 가지(`graph.branches`)에 든 원소. 커패시터·DEC-70 가지치기로 빠진 저항은 DC 전류가 없어 KVL 이 없으므로 대상 밖(블록 멤버면 column=None 행).
* 소자가 어느 뷰에서든 블록 멤버면 그 기둥마다 블록 멤버 행(뷰별 블록마다 한 행). 어느 뷰에도 블록이 없는 소자가 든 기둥에 블록 소자가 있으면 그 기둥에 있는 블록들에 귀속(`column_mate`, shared=True).
  기둥의 소자가 모두 블록 밖이면 바이어스 기둥(`bias_columns`, 행 block=None).
* `shared` = 둘 이상 기둥에 걸침 | 한 뷰에서 둘 이상 블록 멤버 | 기둥 이웃으로 귀속.
* **불변식**: 가지에 들었는데 어느 블록에도 어느 기둥에도 안 든 소자(기둥 열거에서 빠진 orphan 가지의 소자) -> `StructureUnresolvedError`, `detail["reason"] == "column_unassigned"`, `devices` = 그 소자들.

### 11.3 결합 종류와 판정 (모두 '한 뷰 안에서 소자들의 블록 키 합집합 != 교집합'을 블록 경계 횡단으로 본다; 블록이 있는 소자가 그 뷰에 둘 이상 있어야 한다)
| kind | 만드는 조건 | members | nets | domain | init_rule |
|---|---|---|---|---|---|
| K1 | S1 mirror matching 그룹 또는 S1v L 동치류가 블록을 가로지르고 멤버 중 부하 역할(load·mirror·diode_load·tail_source)이 횡단 블록에 있음 -- 실제 블록·의사 블록에 똑같이 적용(오케스트레이터 결정 2026-10-09: 다른 블록·바이어스 의사 블록에서 전류를 정하는 tail 로 미러하는 것도 K1) | 류 멤버 | () | dc(mirror)·geom(L 동치류) | class_owner_value |
| K2 | S1 `equal_vgs` 엣지가 블록을 가로지름 | 엣지 멤버 | 엣지 evidence 넷 | dc | common_vgs_candidates |
| K3 | 비레일 넷에 MOS e 의 drain 과 MOS d 의 source 가 만나고 둘의 블록이 다름(`stacked_vsb`) | (e, d) | (그 넷,) | dc | stack_node_kvl |
| K4 | 한 가지를 지나는 모든 기둥의 소자가 블록을 가로지름 | 가지의 소자 | 가지 양 끝 | dc | shared_node_kvl_kcl |
| K7 | MOS(동작점이 있는 소자)가 둘 이상 뷰의 블록 멤버. 커패시터·저항은 값이 뷰마다 같아 제외 | (소자,) | () | dc | view_shared_split |
| K8 | DC 역할 바이어스 전류원 + 셀 CS(gate 가 신호 넷) + drain 노드에 신호 CD 의 source + c 의 gate 가 그 CD 입력에서 CD 엣지로 안 닿음 + drain 노드가 이득 블록 출력 아님 | (c, CD 셀들) | (drain 노드,) | dc | side_injection_current |
`blocks` = 횡단이 일어난 뷰들의 횡단 블록(K7·K8 은 소자의 모든 블록). 바이어스 기둥 소자와 블록 소자 사이의 미러·`equal_vgs`(예: 기준 diode)도 의사 블록 횡단으로 K1·K2 가 된다(blocks 에 의사 블록이 든다).
