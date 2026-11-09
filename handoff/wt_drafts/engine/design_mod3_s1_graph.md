# MOD2 topology 로더 + MOD3 첫 범위(S1 그래프 구축·질의 API) -- 짧은 design

- 작성 2026-10-07. 문서만 작성했다(코드·저장소 수정 없음). 사용자 원칙 E7: MOD별 짧은 design으로 쓰고, 사용자 승인은 회로 해석 항목(6절)만 받는다.
- 입력: `NEW_ENGINE_DESIGN_REQUIREMENTS.md`(이하 REQ, 맨 끝 '확정 사항'을 가장 앞에 둔다), `6a_structure_prep.md`(이하 S6a), `_drafts/user_decisions.md` 2026-10-07, 계획서 P = `docs/01-plan/features/gain-budget-gmid-sizing.plan.md`(N3.2·N3.3·DEC-57~65·70·71·76·81, 용어집 87·100·101행), C00 = `00-common` §5·§6·§7.
- core 계약: `gmid_engine/core/CONTRACT.md`는 아직 없다(ng-core worktree에 `gmid_engine/` 없음, 2026-10-07 확인). 그래서 아래 **[가정 core]** 표시는 모두 REQ 1.1·3.1·확정 사항 1~5의 core 기술로 가정한 것이다. CONTRACT.md가 나오면 그 칸만 맞춘다.
- 표기: **[결정]** = 원칙에서 이 문서가 고른 기본안이다(회로 해석이 아니어서 사용자 승인을 받지 않는다). **[추측]** = 근거 없이 추론한 것이다.

---

## 1. 범위

| 넣는 것 | 넣지 않는 것(다음 단계, 4절) |
|---|---|
| MOD2: topology 파일 읽기, 스키마, `supply_nets`·`ports`·`passive_elements`·`ideal_sources` 선언 게이트, 이름 유일성(IC3), 숨은 레일 (iii)(DEC-60), 위반을 모두 모아 한 번에 거부 | 회로 spec 로드(`supplies_v` 부호·3레일 검사 DEC-60 (i)), MG 옛 이름 표(LEGACY_NAMES 행) |
| MOD3: S1 데이터 모델 전체(필드 정의), S1 생성(노드·소자·수동소자·이상원·뷰 무관 교류접지 (1)(2)·`is_diode`·bulk 기본 규칙), S1 키, 생성 때 한 번 만드는 인덱스, 질의 API | 관계 엣지 유도·declared 대조(U3), DC 역할(U4), 가지·기둥(U2), G_vgs(U5), 뷰부터 뒤(U6~U15) -- 필드는 1절 모델에 있으되 값은 비어 있다 |

**옛 로더와의 차이(S6a 1.1)**: 옛 `load_topology`(SD 8525)는 로드할 때 `propose_vertical_stack_id_gap_fill`·`propose_device_roles_gap_fill`로 역할 태그를 채운다. 새 로더는 태그 키(`device_roles`, `symmetry`, `sizing_roles`, `compensation`)를 **허용하되 읽지 않는다**(스키마의 '무시 키' 목록). 태그를 채우는 경로가 없어서 '태그 없는 유도'(IC4, P 824)가 로드 단계에서 깨지지 않는다.

## 2. 파일 목록 (규칙 A~D)

규칙 A = 파일마다 독립 진입점 하나, B = 비공개 helper는 그 파일에서만 쓴다, C = 캐시되는 계산 블록 하나에 파일 하나, D = test 파일이 원본과 1:1이다(user_decisions 2026-10-07 확정). `층`은 패키지 안의 import 순서이고, 같은 층끼리는 import하지 않는다.

### 2.1 `gmid_engine/authoring/` (MOD2)

| 파일(층) | 진입점 하나 | 책임 / 근거 |
|---|---|---|
| `json_read.py`(0) | `load_json_checked(path, where) -> dict` | UTF-8·BOM 없음·중복 키 거부·유한 수(C00 §6.2 로더 규칙). 엔진의 `json.load`는 이 파일에만 둔다. 옛 이름 거부 훅은 빈 표로 연결해 두고, 행은 MG 단계에서 더한다 |
| `topology_schema.py`(0) | `check_topology_schema(doc) -> tuple[Hit]` | 최상위 키 화이트리스트: 필수 {`schema_version`, `topology_name`, `netlist`, `supply_nets`, `ports`, `passive_elements`}, 선택 {`ideal_sources`, `linked_topology_files`, `source`}, **무시** {`device_roles`, `symmetry`, `sizing_roles`, `compensation`}, `_` 접두 키는 주석이라 무시한다. 그 밖의 키는 거부. netlist 원소 키는 {`name`, `kind`, `drain`, `gate`, `source`, `bulk`?} + `_`만 받는다(`n_fingers`·`w` 같은 사이징 산출물은 거부). `schema_version == "2.0"`만 받는다(9/9 실측) |
| `linked_files.py`(0) | `check_linked_files(doc) -> tuple[Hit]` | `linked_topology_files`가 비어 있지 않으면 거부한다. **[결정] DEC-76**: library 9회로 실측은 `[]` 6개·키 없음 3개라 발동이 0이다. 그래서 옛 합치기 로직은 이식하지 않고, 이 입력이 오면 `unsupported_rule_branch`와 같은 뜻으로 거부한다. 옛 합치기는 진입 파일의 `passive_elements`만 IC3에 넘겼다(SD `load_topology` 안 IC3 호출) -- 이식하는 시점에 이 결함을 함께 고친다 |
| `name_uniqueness.py`(0) | `check_name_uniqueness(doc) -> tuple[Hit]` | IC3 이식(SD `check_topology_name_uniqueness`). 옛 함수와 달리 **이상원 이름도 포함한다**: 소자·수동·이상원 중복, 대소문자만 다른 이름 |
| `rails.py`(1) | `rail_declaration(doc) -> RailDeclaration` | B26-1 이식(gmid-light cb0ef86 SD 8541: 키 없음·list 아님·빈 문자열·중복은 거부, `[]`는 받음) + **새 게이트**: 선언한 넷이 어느 단자에도 없으면 거부(오타 방지). `ValueError` 대신 core `SchemaRejectedError`를 쓴다 |
| `ports.py`(1) | `port_declaration(doc) -> PortDeclaration` | `ports` 필수. `_` 아닌 원소마다 `direction ∈ {input, output}`·`role` 문자열·넷이 단자에 있음·넷이 레일 아님. 입력과 출력이 각각 1개 이상이어야 한다(기본 전달 뷰 P 341, U-08) |
| `passives.py`(1) | `passive_declaration(doc) -> tuple[PassiveDecl]` | `passive_elements` 키 필수(`[]`는 명시 선언으로 받음, 6.1). 원소마다 이름·`kind`·단자 2개(문자열, 서로 다름)·값 필드(`value_ohm`/`value_farad`, `null`이면 미선언). `resistor`·`capacitor` 밖의 kind는 거부하지 않고 S1이 `기록만`으로 남긴다(DEC-59) |
| `ideal_sources.py`(1) | `source_declaration(doc) -> tuple[SourceDecl]` | 선택 키. 단자 2개, `value_amp`/`value_volt`. kind는 기록만 하고 판정은 S1이 한다 |
| `dc_edges.py`(2) | `dc_edges_unpruned(doc) -> tuple[DcEdge]` | **DC 전도 엣지를 정의하는 유일한 곳**(DEC-70: MOS 채널 d–s, 저항, 이상원. gate·커패시터는 엣지가 아님). 잎 가지치기 **전** 목록이다. MOD3 `dc_conduction.py`(U2)가 이 정의를 import해서 가지치기를 하므로 정의가 둘로 갈라지지 않는다(H 12.3 #5 같은 개념 여러 정의의 재발 방지) |
| `hidden_rails.py`(3) | `check_hidden_rails(doc, rails) -> tuple[Hit]` | DEC-60 (iii): MOS 단자에 없고 수동·이상원 단자에만 있으며, 가지치기 전 DC 엣지로 어느 레일에도 닿지 않는 넷이 `supply_nets`에 없으면 거부한다(공격 14 (b)) |
| `topology_model.py`(0) | `TopologyDoc`(frozen) | 검증을 통과한 투영: {name, devices, passives, sources, rails, ports, `connectivity_fp`, `file_sha256`}. 태그는 들어가지 않는다. **[가정 core]** 타입 정의 파일의 규칙 A 판정은 뿌리 타입 하나(필드 주석으로 참조되는 하위 타입은 셈에서 뺀다) |
| `topology_load.py`(4) | `load_topology(path) -> TopologyDoc` | 위 검사를 **모두** 돌려 걸린 곳을 전부 모은 뒤 한 번에 `SchemaRejectedError(detail={"gate", "hits"[...]})`를 낸다(C00 §6.2: 개수로 자르지 않는다). 통과하면 `TopologyDoc`를 만든다. 결과는 파일 sha256 키로 실행 안에서 재사용한다 **[가정 core: graph 밖 memo는 LUT 하나뿐(확정 4)이라, 로드 결과도 S0 입력 객체로 들고 다니고 별도 캐시는 두지 않는다]** |

### 2.2 `gmid_engine/graph/` (MOD3, 이번 범위)

| 파일(층) | 진입점 하나 | 책임 / 근거 |
|---|---|---|
| `s1_model.py`(0) | `S1Graph`(frozen, 질의 메서드 포함) | 3절 데이터 전부 + 4절 질의 API(메서드는 인덱스 필드만 읽는다). 아직 채우지 않은 필드는 `unset`이고, 그런 필드를 질의하면 `FieldNotComputed`를 낸다(조용한 빈 값 금지, WP-02) |
| `s1_key.py`(0) | `s1_key(doc, supplies_v) -> S1Key` | 5.1 |
| `bulk_default.py`(0) | `bulk_net(kind, declared, rails, supplies_v) -> BulkResult` | DEC-61: 선언한 `bulk`가 있으면 그것, 없으면 nmos = `supplies_v`에서 가장 낮은 전위의 레일, pmos = 가장 높은 전위의 레일. `supplies_v`가 없으면 `undetermined(needs_supplies_v)`를 낸다. **[결정]** 레일 이름으로 대신 정하지 않는다(DEC-60) |
| `ac_ground_static.py`(0) | `static_ac_ground(terms, rails, ports) -> Mapping[net, cls]` | 교류접지 중 뷰와 무관한 분류(N3.2-1): (1) `rail` (2) `gate_only_undriven` = 단자가 전부 gate이고, 입력 포트가 아니며, 수동·이상원 단자가 없다. (3) 이상 **전압원** 단자는 library 발동이 0이라 구현하지 않고 `unsupported` 기록만 남긴다(DEC-76 안전망). (4) 바이어스 종속 넷은 뷰 속성이라 U7 몫이다 |
| `s1_index.py`(0) | `build_index(devices, passives, sources) -> S1Index` | 생성 때 한 번 만드는 인덱스: `by_net_terminal`, `gs_groups`(같은 (kind, gate, source), 2개 이상), `channel_adj`, `gate_only`. 규칙 함수가 소자 리스트를 다시 돌지 않게 한다(S6a 1.3, 대원칙 '같은 값 반복 계산 금지') |
| `s1_build.py`(1) | `build_s1(doc, supplies_v=None) -> S1Graph` | 5.2. 계산 블록이고(규칙 C), 키는 `S1Key`다 |

test 파일: `gmid_engine/tests/authoring/test_<file>.py`, `tests/graph/test_<file>.py`가 원본 파일과 1:1이다(규칙 D). 교차 test는 `tests/integration/test_s1_library9.py`에 둔다(6절).

## 3. 데이터 (S1, P 364 필드 그대로)

```
S1Graph(frozen)            # [가정 core] Fingerprinted 기반, fp 생성 시 1회
  key: S1Key{topology_fp, rule_fp, supplies_v_fp}
  nodes: FrozenMap[name -> Node]
    Node{name, terminals: tuple[(element, term)],  # term ∈ d|g|s (MOS), t0|t1 (수동·이상원). bulk는 넣지 않음(아래)
         is_rail: bool (dc),  ac_ground_class: None|"rail"|"gate_only_undriven" (ac_struct, 뷰 무관 부분만),
         port_role: None|"input"|"output"}
  devices: FrozenMap[name -> Device]
    Device{name, kind ∈ {nmos,pmos}, d, g, s, b: BulkResult{net|None, origin ∈ declared|default_rule|undetermined},
           is_diode: bool (g == d),  dc_role: unset   # U4가 쓴다
  passives: FrozenMap[name -> Passive{name, kind, terminals:(t0,t1), value|None}]
  sources:  FrozenMap[name -> Source{name, kind, terminals:(t0,t1), value|None}]
  edges:    unset   # tuple[RelEdge{type, domain, members, status, evidence{rule, nets}}], U3·U5가 쓴다
  branches: unset   # tuple[Branch{id, ends, segments: tuple[tuple[device,...]], has_ideal_source}], U2
  columns:  unset   # tuple[Column{id, rail_lo, rail_hi, branch_order, status}], U2
  unsupported: tuple[UnsupportedRecord{rule_branch, element, evidence}]   # 기록만 분기(DEC-59)
  index: S1Index
  stamps: FrozenMap[field -> FieldStamp{writer, writer_code_fp, input_fp}]   # 확정 1: 필드마다 writer 1·입력 버전
```

- **bulk를 단자 인덱스에 넣지 않는 이유 [결정]**: S6a 1.5 교차표의 차수 정의가 '채널 3단자 + 수동 2 + 이상원 2'이다. bulk를 넣으면 레일 차수가 소자 수만큼 늘어나서, 가지 분할에 쓰는 '분기 노드 = DC 엣지 차수 3 이상'과 섞인다. bulk 사용처는 `Device.b`와 질의 `bulk_users(net)`로 따로 둔다.
- **branch의 `segments`**: 병렬 소자를 한 segment 안의 여러 소자로 담는다. 이 표현은 '따로 세기 62 / 합쳐 세기 41'(P 1162 ⑦) 어느 쪽으로도 셀 수 있게 중립으로 둔다. 어느 쪽으로 셀지는 U2가 정한다(4절).
- **kind 밖 소자**: nmos·pmos 밖의 MOS kind, resistor·capacitor 밖의 수동 kind, `voltage_source`는 S1에 원소로 넣는다. 다만 그 원소가 엣지·분류에 쓰이지 않는다는 사실을 `unsupported`에 소자 이름과 함께 남긴다(DEC-61 끝, DEC-59). 이 정지(`unsupported_rule_branch`)는 MOD3가 아니라 소비자(MOD4 이상)가 낸다(C00 §7.1 raise 위치 규칙).
- **domain**: `is_rail`·`b`·`is_diode`·`dc_role` = dc, `ac_ground_class`·`port_role` = ac_struct(C00 §5 `DOMAINS`). 엣지 `domain`의 값 집합 검사(CC-6)는 엣지를 처음 쓰는 U3에서 한다.
- **status**: 이번 범위는 엣지를 만들지 않으므로 status 전이(P 374~378)는 U14에서 한다. 선언 태그(`same_as_device`, `budget_reference_device`, `matching_pairs`, `vertical_stack_id`)를 `declared` 엣지·대조표로 읽는 일은 U3·U2가 MOD2 `declared_facts.py`(그때 신설)로 한다. 이번 범위의 `TopologyDoc`·S1 키에는 태그가 들어가지 않는다.

## 4. 질의 API (`S1Graph` 메서드, 반환은 모두 정렬된 tuple -- NFR-4)

| 메서드 | 반환 | 근거·소비자 |
|---|---|---|
| `nets()` / `node(net)` | 넷 이름 / `Node` | 전부 |
| `terminals(net, kinds=None)` | `(element, term)` 목록. `kinds`로 d/g/s/t0/t1을 거른다 | 옛 `by_name` 순회 대체(R 49행) |
| `degree(net)` | 채널 3단자 + 수동 2 + 이상원 2 단자 수 | 교차표, U2 분기 노드 |
| `rails()` / `is_rail(net)` | `supply_nets` | DEC-60, W0 |
| `ports(direction=None)` | (net, direction, role) | R6·R7·DEC-64 v1 |
| `devices(kind=None)` / `device(name)` | 소자 | 전부 |
| `diodes()` | `is_diode` 소자 | R2 (1), W1 |
| `gs_groups()` | 같은 (kind, gate, source)인 2개 이상 묶음. 레일 gate 묶음을 거르지 않은 원자료다 | R2 (2), R3 미러·`equal_vgs` v0 |
| `channel_edges()` | (device, d, s) | U2 DC 전도, U5 |
| `gate_only_nets()` | 단자가 전부 gate인 넷(입력 포트 포함, 원자료) | R6 (2), 교차표 |
| `ac_ground_static()` | 넷 -> `rail`·`gate_only_undriven` | R6 |
| `bulk_of(device)` / `bulk_users(net)` | `BulkResult` / 그 넷을 bulk로 쓰는 소자 | W2 `stacked_vsb`, 6b |
| `passives(kind=None)` / `sources(kind=None)` | 원소 | U2·R11·R14 |
| `unsupported()` | 기록만 분기 목록 | R19 발동표 |
| `field_stamp(field)` | `FieldStamp` | 확정 5 test(입력 버전 같은데 재계산하면 FAIL) |

## 5. 생성

### 5.1 S1 키 (S0 지문의 S1 부분, P 363~364)

- `topology_fp` = `TopologyDoc.connectivity_fp`. 대상은 정규화한 **투영**의 바이트다: 소자(이름순: name, kind, d, g, s, 선언 bulk), 수동·이상원(이름순: name, kind, terminals, value), `supply_nets`(정렬), ports(넷순: net, direction, role). `_` 주석 키·태그 키·원소 순서는 지문에 들어가지 않는다. **[결정]** 근거는 NFR-2 '키 = 그 계산이 실제로 읽는 상태의 지문'이다. 주석만 바꾸면 S1이 다시 유도되지 않고, 태그를 지워도 키가 같다(IC4). 파일 sha256은 출처 기록으로만 따로 든다.
- `rule_fp` = S1 필드 writer 파일들(`s1_build`·`s1_index`·`bulk_default`·`ac_ground_static`와, 다음 단계에서 쓰는 writer들)의 코드 지문을 정렬해 합친 해시다. 필드마다 `writer_code_fp`도 함께 기록하므로, writer 하나가 바뀌면 그 필드만 다시 계산된다(확정 1 '필드가 곧 캐시'). **[가정 core]** 코드 지문 함수는 core `fingerprint.py`가 제공한다(REQ N3.3 행: 패키지 소스 해시 [제안]).
- `supplies_v_fp` = `supplies_v{넷: 전압}`의 정규화 해시. 없으면 `"none"`이다. ratified -> review_needed 전이(P 378)의 입력이다.

### 5.2 `build_s1(doc, supplies_v=None)`

1. 인덱스 1회(`s1_index`) -> 2. 노드(`terminals`, `is_rail`, `port_role`) -> 3. `static_ac_ground` -> 4. 소자(`is_diode`, `bulk_net`) -> 5. kind 밖 원소를 `unsupported`에 기록 -> 6. 필드 stamp. 입력은 `TopologyDoc`(파일을 다시 읽지 않는다)와 `supplies_v`다. **`supplies_v`는 이번 범위에서 인자로만 받는다**: 새 회로 spec 로더는 아직 없고, topology의 `_declared_target_spec`은 `_` 주석 키라 읽지 않는다 **[결정]**.
- 스냅샷: 결과는 불변이다. 다음 단계의 writer(U2~U5)는 `snapshot.with_fields(...)`로 **바뀐 필드만 새로 만들고 나머지는 이전 스냅샷과 공유하는** 새 스냅샷을 낸다(확정 2). **[가정 core]** `with_fields`·`FieldStamp`·같은 writer 두 번이면 FAIL·같은 입력 버전 재계산이면 FAIL은 core가 강제한다(확정 5).
- 재사용: 같은 `S1Key`의 S1 스냅샷은 디스크에 둔다(확정 6 E3: S1 스냅샷 지문 키). 실행 안에서는 같은 키로 `build_s1`을 다시 계산하는 횟수가 0이어야 한다(test 6.3 (c)).

## 6. test 계획

기대값은 test 작성 주체가 **topology JSON을 직접 집계해** 만든다. 피검 함수 `load_topology`·`build_s1`을 불러 기대값을 만들지 않는다(가벼운 절차 '남기는 것' 1). 아래 수치는 작성자 측 교차 확인용이고 정본이 아니다.

### 6.1 9회로 교차표 (S6a 1.5 + 이번 범위 열, JSON 직접 집계 2026-10-07)

| 회로 | 넷 | 레일 | `passive_elements` | gs 묶음 ≥2 | `gate_only_undriven`(교류접지 (2)) | source가 레일 아닌 MOS | `supplies_v`(`_declared_target_spec`) |
|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 7 | vdd, gnd | `[]` | 0 | VNBias1, VNBias2, VPBias1 | 1/3 | 없음 |
| current_reuse_telescopic_ota | 37 | vdd, gnd | 12개 | 3 | 없음 | 23/51 | 없음 |
| folded_cascode | 14 | vdd, gnd | **키 없음** | 3 | bias3 | 6/13 | 없음 |
| ngcc_3stage_ff | 13 | vdd, gnd | 3개 | 5 | VBN, VBP | 2/16 | 있음 |
| nmcnr_amplifier | 17 | vdd, vss | **키 없음** | 3 | VB1~VB5 | 4/15 | 있음(±0.9) |
| pushpull_follower_buffer | 9 | vdd, vss, agnd | 1개 | 0 | VNB1, VPB1 | 4/6 | 있음(3레일) |
| sf_pushpull_output_opamp | 23 | vdd, vss, agnd | 5개 | 4 | 없음 | 12/22 | 있음(3레일) |
| two_stage_ota | 9 | vdd, gnd | **키 없음** | 2 | bias | 2/7 | 없음 |
| two_stage_ota_sf | 10 | vdd, gnd | 2개 | 2 | bias | 3/9 | 없음 |

나머지 열(nmos/pmos·R/C·이상원 수·단자 수·diode·최대 차수)은 S6a 1.5 표를 그대로 쓴다. 숨은 레일 (iii) 후보(레일 선언 전 기준): pushpull·sf의 `agnd`(커패시터 단자만 있음), current_reuse의 `N_cc_rz1`·`N_cc_rz2`(Rz로 DC 연결되어 후보 아님). 현재 9/9가 통과한다.

### 6.2 단위 test (파일별, 규칙 D)

| test 파일 | 핵심 케이스 |
|---|---|
| `test_json_read` | BOM, 중복 키, NaN/Inf 거부. AST: `json_read.py` 밖에 `json.load` 0 |
| `test_topology_schema` | 미지 최상위 키·netlist 원소의 `n_fingers` 거부, `_` 키·무시 키 통과, `schema_version` 다르면 거부 |
| `test_linked_files` | `[]`·키 없음 통과, 원소 1개면 거부(DEC-76 안전망) |
| `test_name_uniqueness` | 소자 중복, 소자-수동 겹침, 소자-이상원 겹침(옛 함수가 못 잡던 경우), 대소문자만 다른 이름 |
| `test_rails` | B26-1 4종 거부 + 선언 넷이 단자에 없으면 거부, `[]`는 받음 |
| `test_ports` | 키 없음, direction 값 밖, 넷이 없거나 레일, 입력 0 또는 출력 0 -> 거부 |
| `test_passives` | 키 없음 거부, 단자 개수·같은 단자 거부, `inductor` kind는 통과(S1 기록 대상) |
| `test_dc_edges` | 손계산 픽스처: 커패시터·gate는 엣지가 아님, 저항·이상원·채널은 엣지 |
| `test_hidden_rails` | **공격 14 (b)**: pushpull·sf에서 `supply_nets`에서 `agnd`만 뺀 변형은 거부. **오거부 0**: current_reuse 원본은 통과(N_cc_rz). (a) 미선언은 `test_rails`가 잡는다 |
| `test_topology_load` | 위반 두 종류를 넣은 픽스처가 **예외 한 번**에 hits 둘을 낸다. 9회로 원본은 6.4 승인 결과를 반영한 뒤 통과한다 |
| `test_s1_key` | (a) 같은 doc -> 같은 키 (b) 넷 이름 하나를 바꾸면 키가 바뀐다 (c) `_comment`만 바꾸면 키가 같다 (d) `device_roles`를 통째로 지워도 키가 같다(IC4) (e) netlist 순서를 섞고 `PYTHONHASHSEED` 1~5로 돌려도 키가 같다(IC2) |
| `test_bulk_default` | 3레일 `supplies_v`(vdd 1.8, vss 0, agnd 0.9): nmos -> vss, pmos -> vdd. 원점 이동 불변(nmcnr ±0.9 vs 0/1.8, IC11). 선언 bulk 우선. `supplies_v`가 없으면 undetermined |
| `test_ac_ground_static` | 입력 포트인 gate 전용 넷은 (2)가 아님(folded vin_p). 수동 단자가 붙은 넷은 (2)가 아님. 전압원 픽스처는 `unsupported` |
| `test_s1_index` | `gs_groups`·`channel_adj` 손계산(two_stage_ota) |
| `test_s1_build` | 6.3 |

### 6.3 통합 (`tests/integration/test_s1_library9.py`)

(a) 9회로마다 S1 값과 JSON 직접 집계가 6.1 표 + S6a 1.5 표 전 열에서 같다. (b) S1 질의가 정렬된 tuple을 낸다. (c) 같은 doc으로 `build_s1`을 두 번 부르면 계산은 1회이고 같은 객체를 돌려준다(core 카운터 `recompute_same_key == 0`) [가정 core]. (d) 아직 쓰지 않은 필드(`edges`·`branches`·`columns`·`dc_role`)를 질의하면 `FieldNotComputed`가 나고 빈 tuple은 나오지 않는다. (e) 엔진 소스의 문자열 상수와 9회로 넷·소자 이름의 교집합이 0이다(`test_no_name_literals`, REQ 1.4 -- structure 묶음에서 이미 돌면 그것을 쓴다).

## 7. 6a 규칙 R0~R19 배치

| 규칙 | 이번 범위 | 다음 단계 |
|---|---|---|
| R0 GB0 로드 게이트 | `supply_nets` 필수·숨은 레일 (iii)·ports·passive·IC3·스키마 | spec 쪽: 3레일·음전위 `supplies_v`, spec 넷 키 = `supply_nets`(DEC-60 (i)), MG 옛 키 행 -- spec 로더 단계 |
| R1 S0 + S1 | S1 키, S1 노드·소자·수동·이상원·인덱스, bulk 기본 규칙, 뷰 무관 교류접지 (1)(2) | 전체 S0(LUT·spec·metric 코드 해시)는 MOD1·spec 로더 뒤 `s0.py` |
| R2 DC 역할 | 입력(`diodes`, `gs_groups`)만 | U4 `dc_roles.py` |
| R3 관계 엣지·declared 대조 | -- | U3 `relations.py` + MOD2 `declared_facts.py` |
| R4 G_vgs | -- | U5 |
| R5 가지·기둥 | DC 엣지 정의(`dc_edges.py`)만 | U2 `dc_conduction.py`·`columns.py`. ⑦(62 대 41)은 코드 결정이다(P 1162 부류 '코드'). 기본안 [결정]: 정본은 따로 세기 62(DEC-71 (3)), 합쳐 세기 41은 병기한다. J13(레일 쌍)은 U2 design에서 다룬다 |
| R6 교류접지·뷰 | (1)(2)만 | (4)·뷰 수집·대칭 축약 U6·U7 |
| R7~R19 | -- | U6~U14(S6a 6절 순서 그대로) |

## 8. 사용자 승인이 필요한 항목 (회로 해석·connectivity 사실만, S1 단계에 걸리는 것)

S6a '착수 전 결정' 1~4는 이번 범위에 걸리지 않는다. 1(수동소자 엣지 비용)은 R11, 2(대칭 반쪽)는 R12, 4(블록 구성)는 R13 몫이다. 3(병렬 소자)은 데이터 표현을 중립으로 둬서 U2로 넘겼다(7절). J 항목 중 S1에 걸리는 것은 아래 둘뿐이다. J1은 이미 확정됐고 U7이 쓴다. J13·J2·J5 등은 U2 이후에 쓴다.

### 8.1 [J9] `passive_elements` 선언 누락 3회로 -- MOD2 passive 게이트가 지금 거부한다

| 회로 | 키 | topology 안 근거(connectivity는 사용자 소관이라 엔진이 옮기지 않는다) | S1에 미치는 영향 |
|---|---|---|---|
| nmcnr_amplifier | 없음 | `_compensation_network_comment`: Cm1(NodeM2->NodeCM), Cm2(NodeS2->NodeCM), Rm(NodeCM->Vout), CL(Vout->vss), "only ONE null resistor"(2026-07-31 사용자 정정). NodeCM은 netlist에 없는 넷이다 | 보상 루프(R14)·교류접지·DC 잎 가지치기(Rm)가 통째로 빠진다 |
| two_stage_ota | 없음 | `compensation.function = miller_ota_topology`, 매개변수 GBW·CL·Z·NDP, 주석 "표준 2단 Miller OTA". 수동소자 넷 이름은 적혀 있지 않다 | Miller 루프(J12-g와 같은 형태)가 S1에 없다 |
| folded_cascode | 없음 | `_compensation_status = not_applicable`, compensation null | 출력 부하 CL 유무가 결정되지 않는다 |

- **기본안 (a)**: 게이트는 키가 없으면 거부한다(`[]`는 '없음'을 명시한 선언으로 받는다). 사용자가 세 파일에 선언을 쓴다. 후보는 다음과 같다. nmcnr은 위 주석의 4개 소자를 그대로 옮긴다. two_stage_ota는 Cc(O1–OUT)와 CL(OUT–gnd)이다 **[추측: two_stage_ota_sf의 같은 이름 넷 선언과 Miller 표준형에서 유추했으므로 도면 확인이 필요하다]**. folded는 도면에 보상·부하 소자가 없으면 `[]`이다. 근거: 키가 없는 것을 `[]`로 읽으면 '수동소자 없음'이라는 회로 사실을 엔진이 지어내는 셈이고, 그러면 교류접지 (2)·루프 분류가 아무 경고 없이 달라진다(WP-02).
- (b) 대안: 키가 없으면 통과시키되 S1에 `passives_declared=False`를 기록하고, R6·R14 소비자가 `review_needed`로 정지한다. 이 경우 9회로 중 3회로가 6a 대조를 늦게 받는다.
- 계획 J9는 passive를 7b 소비로 적었지만, S1 게이트가 지금 걸리므로 승인 시점이 당겨진다.

### 8.2 [DEC-61 사실 확인] bulk 선언 0개 -> 모든 소자에 기본 레일 규칙 적용

| 회로 | bulk 선언 | source가 레일이 아닌 MOS(기본 규칙이면 vsb ≠ 0) |
|---|---|---|
| pushpull_follower_buffer | 0 | M1, M2, M3, M4(follower) |
| sf_pushpull_output_opamp | 0 | M1, M2, M5, M7, M10, M12, M13, M15, M18, M19, M21, M22 |
| two_stage_ota_sf | 0 | M1, M2, M8(follower) |
| current_reuse_telescopic_ota | 0 | 23개(M1a/M1b·M4a/M4b 입력쌍, 캐스코드, M57/M58/M63/M64 등) |
| folded / nmcnr / ngcc / two_stage_ota / common_gate | 0 | 6 / 4 / 2 / 2 / 1개 |

- **기본안**: 선언을 추가하지 않는다. 그러면 위 소자는 모두 nmos -> 최저 전위 레일, pmos -> 최고 전위 레일에 bulk가 붙는다(3레일 회로는 agnd에 붙지 않는다). J12의 "two_stage_ota_sf M1/M2 body effect" 서술과 일치한다.
- 사용자 확인 사항: 도면에서 bulk를 source 등 다른 넷에 묶은 소자(특히 follower M8·M1~M4·M18~M22)가 있으면 그 소자에 `bulk` 필드를 쓴다. bulk는 connectivity라 사용자만 쓴다(DEC-61, WP-07).
- 이 결과는 S1 `Device.b`와 6b W2 `stacked_vsb`·`ss` gmb의 입력이다. 5회로(`supplies_v` 없음)는 spec 선언 전까지 `b = undetermined`로 남는다.

## 9. core 계약에 기대는 가정 (CONTRACT.md가 나오면 맞출 칸)

`Fingerprinted`·코드 지문 함수, `SchemaRejectedError`·`FailureRecord`의 위치(REQ C4: core 층 0), 불변 스냅샷의 `with_fields`와 `FieldStamp{writer, writer_code_fp, input_fp}`, writer 유일성·같은 입력 버전 재계산 FAIL 강제, `FrozenMap` 정렬 순회, S1 스냅샷 디스크 캐시(E3), 규칙 A 판정에서 타입 정의 파일을 세는 방식.
