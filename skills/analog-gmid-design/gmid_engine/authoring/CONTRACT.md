# gmid_engine.authoring 동작 계약 (MOD2, test 작성용)

- 대상: `gmid_engine/authoring/` 공개 API(`gmid_engine.authoring.__all__`). test 는 `from gmid_engine.authoring import ...`
  와 `from gmid_engine.core import ...` 만 쓴다(파일 모듈 직접 import·`_` 이름 사용 금지). test 배치는 규칙 D:
  `gmid_engine/tests/authoring/test_<파일>.py`(공용 helper `_rejection.py`·`_terminal_nets.py`·`_two_terminal.py` 는
  `test__<이름>.py`), 9회로 교차는 `tests/integration/`.
- 근거: `_drafts/engine/design_mod3_s1_graph.md` 2.1·6절, `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항',
  core `CONTRACT.md`(4절 실패 규약), C00 §6.2(위반을 모두 모아 한 번에), DEC-59·60·61·70·76, IC3·IC4, J9.
- 범위: 이 문서는 MOD2 topology 로드. **회로 사이징 spec 로드(`load_sizing_spec`, `supplies_v` 등)는 `SPEC_CONTRACT.md`**
  (2026-10-07 추가 -- 공개 진입점, 엔진 안 호출자는 아직 없음: MOD10 이 부를 예정). bulk 기본 규칙(CI-14)·S1 graph 는
  다음 단계(graph/)다.
- **태그 키는 읽지 않는다**: `device_roles`·`symmetry`·`sizing_roles`·`compensation` 은 허용하되 어느 함수도 값을 읽지
  않고, 결과(`TopologyDoc`)·지문에 들어가지 않는다. 태그를 채우는 경로는 없다(IC4).
- **회로 파일(topology.json)은 이 단계에서 고치지 않았다**(connectivity 는 사용자만).

---

## 0. 실패 형식 (모든 거부 공통)

- 예외: core `SchemaRejectedError`(exit code 7, `exit_code_for`). `ValueError` 를 내지 않는다(옛 `rail_declaration` 과 다름).
- `exc.record.detail`(키 정렬 (키, 값) tuple -- `dict(...)` 로 읽는다):
  - `gate`: 거부를 낸 함수 단위 이름 -- `json_read`, `devices`, `rails`, `passives`, `ideal_sources`, `ports`,
    `topology_load`.
  - `where`: 문서 위치(접근자는 최상위 키 이름, `json_read`·`topology_load` 는 `path` 문자열).
  - `hits`: `SchemaHit` tuple -- **걸린 곳 전부**(개수로 자르지 않는다). 순서는 게이트 순서, 게이트 안에서는 문서 순서.
    예외: `check_name_uniqueness`·`check_hidden_rails` 는 원소 사이 관계 검사라 문서 순서가 정의되지 않으므로 이름순
    (`name_duplicate` 는 이름, `name_case_collision`·`net_case_collision` 은 casefold 키(원소 위반 다음 넷 위반),
    `rail_not_connected`·`hidden_rail` 은 넷 이름 정렬, 결정론)이 정본이다.
  - `topology_load` 만 추가: `rejected_gates`(위반을 낸 게이트 이름 정렬 tuple), `not_evaluated`(입력 선언이 거부돼 돌리지
    못한 검사 이름 tuple, 0절 표).
- `SchemaHit(rule, where, message, elements=())` frozen dataclass. `elements` 는 관련 원소·넷 이름의 **정렬·중복 제거**
  tuple(입력 순서 무관). `rule` 값은 아래 표의 위반 키 그대로다(test 는 `rule`·`where`·`elements` 로 판정하고
  `message` 문구는 판정하지 않는다).
- `record.devices` 는 비어 있다(관련 이름은 hit 의 `elements`).

| `not_evaluated` 이름 | 조건 |
|---|---|
| `all_declarations` | 최상위 값이 객체가 아님(이 경우 다른 검사 없음) |
| `name_uniqueness` | devices·passives·ideal_sources 중 하나라도 거부 |
| `ports.port_net_unknown` | 위와 같음(단자 넷 집합을 만들 수 없음). 포트 형식 검사는 그대로 한다 |
| `ports.port_on_rail` | rails 거부 |
| `hidden_rails` | 원소 셋 또는 rails 중 하나라도 거부 |

## 1. `load_topology(path) -> TopologyDoc`

- 순서: `load_json_checked` -> `check_topology_schema` -> `check_linked_files` -> `device_declaration` ->
  `rail_declaration` -> `passive_declaration` -> `source_declaration` -> `check_name_uniqueness` ->
  `port_declaration` -> `check_hidden_rails`.
- JSON 수준 위반(`json_read`)은 그 예외를 그대로 낸다(gate `json_read`, 문서가 없으니 다음 게이트 없음).
- 그 밖 위반은 전부 모아 `SchemaRejectedError` **한 번**(gate `topology_load`). 접근자 예외는 잡아서 hits 를 합친다.
  예: 미지 최상위 키 + netlist 원소 `n_fingers` + supply_nets 중복 + 포트 direction·role 위반 -> 예외 1개, hits 5개,
  `rejected_gates == ("devices", "ports", "rails", "topology_schema")`.
- 통과하면 `TopologyDoc`. 같은 경로를 두 번 부르면 두 번 읽는다(캐시 없음 -- graph 밖 memo 는 LUT 하나뿐, 확정 사항 4).
- 파일 열기 OS 오류(`FileNotFoundError` 등)는 그대로 전파(스키마 문제가 아님).

## 2. `TopologyDoc` (frozen dataclass, `require_immutable` 통과, `fp_of` 가능)

- 필드: `name`(topology_name), `devices`(DeviceDecl, 이름순), `passives`(PassiveDecl, 이름순), `sources`(SourceDecl,
  이름순), `rails`(frozenset), `ports`(PortDecl, 넷순), `connectivity_fp`(64자 hex), `file_sha256`(파일 바이트 sha256).
- `TopologyDoc.from_declarations(name, devices, passives, sources, rails, ports, file_sha256)` 이 정렬하고
  `connectivity_fp` 를 계산한다. 생성자에 가변 값을 넣으면 `TypeError`.
- `connectivity_fp` = `fp_of`(plain tuple 투영: 소자 (name, kind, d, g, s, bulk), 수동·이상원 (name, kind, terminals,
  value_key, value), 정렬 레일, 포트 (net, direction, role)). 불변식:
  - `_` 주석 키를 바꾸거나 더해도 같다. 태그 키 4개를 통째로 지워도 같다(IC4). netlist·passive 원소 순서를 섞어도 같다(IC2).
  - 넷 이름 하나, kind 하나, 포트 role 하나, 레일 집합, 수동소자 값 하나라도 바뀌면 다르다.
  - `file_sha256` 은 지문에 들어가지 않는다(출처 기록).
- 원소 형식: `DeviceDecl(name, kind, d, g, s, bulk=None)`, `PassiveDecl`/`SourceDecl(name, kind, terminals, value_key=None,
  value=None)`(terminals = 문서의 두 넷 순서 그대로, `TWO_TERMINAL_NAMES == ("t0", "t1")` 순), `PortDecl(net, direction,
  role)`, `RailDeclaration(nets: frozenset)`, `DcEdge(element, element_kind, nets)`(nets 정렬 2-tuple).

## 3. 위반 종류별 거부 조건 (공개 함수마다)

### 3.1 `load_json_checked(path, where) -> CheckedJson(data, sha256)` -- gate `json_read`
| rule | 조건 |
|---|---|
| `bom` | 파일이 UTF-8 BOM 으로 시작 |
| `not_utf8` | UTF-8 해독 실패 |
| `duplicate_key` | 같은 객체 안 같은 키 2번 이상(중첩 어디든, 등장마다 하나) |
| `non_finite` | `NaN`·`Infinity`·`-Infinity` 상수, float 범위 밖 수(`1e999`) -- 등장마다 하나 |
| `json_syntax` | 문법 오류(앞서 모인 hits 와 함께 낸다) |
엔진에서 `json` 파싱은 이 파일에만 있다.

### 3.2 `check_topology_schema(doc) -> tuple[SchemaHit]` (빈 tuple = 통과)
| rule | 조건 |
|---|---|
| `top_not_object` | 최상위 값이 객체 아님(이 hit 하나만 내고 끝) |
| `missing_key` | `schema_version`·`topology_name` 없음 |
| `unknown_key` | `_` 접두가 아니고 받는 키 밖. 받는 키 = {schema_version, topology_name, netlist, supply_nets, ports, passive_elements, ideal_sources, linked_topology_files, source} + `IGNORED_TAG_KEYS` |
| `schema_version` | 값 ≠ `SCHEMA_VERSION`(`"2.0"`) |
| `topology_name` | 비어 있지 않은 문자열 아님 |
| `source_type` | `source` 가 문자열·null 아님 |
netlist·supply_nets·ports·passive_elements 의 **존재**는 각 접근자가 `missing_key` 로 낸다(중복 보고 없음).

### 3.3 `check_linked_files(doc)`
| rule | 조건 |
|---|---|
| `linked_files_type` | `linked_topology_files` 가 list 아님 |
| `linked_files_unsupported` | 원소가 1개 이상(DEC-76 안전망 -- 여러 파일 합치기 미지원, 진입 파일만 읽지 않고 거부) |
키 없음·`[]` 통과.

### 3.4 `device_declaration(doc) -> tuple[DeviceDecl]` -- gate `devices`
| rule | 조건 |
|---|---|
| `top_not_object` | doc 이 객체 아님 |
| `missing_key` / `netlist_type` | `netlist` 없음 / list 아님(이 경우 그 hit 하나) |
| `element_type` | 원소가 객체 아님 |
| `element_unknown_key` | 원소 키가 {name, kind, drain, gate, source, bulk} + `_` 밖(`n_fingers`·`w` 등 사이징 산출물) |
| `element_field` | name·kind·drain·gate·source 가 빠졌거나 빈/비문자열, `bulk` 가 있는데 빈/비문자열 |
kind 값은 제한 없음(nmos·pmos 밖은 graph 가 기록만). 원소 이름 중복은 여기서 보지 않는다(3.8).

### 3.5 `rail_declaration(doc) -> RailDeclaration` -- gate `rails` (B26-1 이식)
| rule | 조건 |
|---|---|
| `top_not_object` | doc 이 객체 아님 |
| `missing_key` | `supply_nets` 없음 |
| `supply_nets_type` | list 아님 |
| `supply_net_value` | 원소가 빈 문자열·비문자열(원소마다) |
| `supply_net_duplicate` | 같은 원소 2번 이상(넷마다 한 번) |
`[]` 는 받는다(`nets == frozenset()`). 넷 이름으로 레일을 정하지 않는다.

### 3.6 `passive_declaration(doc) -> tuple[PassiveDecl]` -- gate `passives`
| rule | 조건 |
|---|---|
| `top_not_object` | doc 이 객체 아님 |
| `missing_key` | `passive_elements` 키 없음 -- **CI-12 기본안(사용자 결정 대기)**: 키 없음을 `[]` 로 읽지 않는다. `[]` 는 받는다 |
| `passive_elements_type` | list 아님 |
| `element_type` | 원소가 객체 아님 |
| `element_unknown_key` | 원소 키가 {name, kind, terminals, value_ohm, value_farad, value_from_spec, nulling_reference_device} + `_` 밖 |
| `element_field` | name·kind 가 빈/비문자열 |
| `terminals` | list 아님, 원소 수 ≠ 2(`len(TWO_TERMINAL_NAMES)`), 넷이 빈/비문자열, 두 넷이 같음 |
| `element_value` | 값 필드 2개 이상, 값이 null·유한 수 아님(bool 포함) |
`value_from_spec`·`nulling_reference_device` 는 허용하되 읽지 않는다(투영에 없음). kind 는 제한 없음(`inductor` 통과).

### 3.7 `source_declaration(doc) -> tuple[SourceDecl]` -- gate `ideal_sources`
키 없으면 `()`. 원소 규칙은 3.6 과 같고(`ideal_sources_type` 포함), 받는 키 = {name, kind, terminals, value_amp, value_volt,
implementable} + `_`, 값 필드 = value_amp·value_volt, `implementable` 은 읽지 않는다. kind 제한 없음(`voltage_source` 통과).

### 3.8 `check_name_uniqueness(devices, passives, sources, supply_nets=(), port_nets=())` (IC3, 이상원 포함 + 넷 대소문자, 7절)
| rule | 조건 |
|---|---|
| `name_duplicate` | 세 종류를 합친 이름 공간에서 같은 이름 2번 이상(소자끼리·소자-수동·소자-이상원·수동끼리 모두), 이름마다 하나 |
| `name_case_collision` | casefold 가 같고 글자는 다른 이름 묶음마다 하나(`elements` = 그 이름들) |
| `net_case_collision` | 넷 이름 집합(MOS d/g/s/선언 bulk ∪ 2단자 terminals ∪ `supply_nets` ∪ `port_nets`)에서 casefold 가 같고 글자는 다른 묶음마다 하나(`elements`·`where` = 그 넷 이름들). 원소 이름과 넷 이름은 다른 공간(서로 비교 안 함). 자동 통일·레일 별칭 예외 없음 |

### 3.9 `port_declaration(doc, rails, known_nets) -> tuple[PortDecl]` -- gate `ports`
| rule | 조건 |
|---|---|
| `top_not_object` | doc 이 객체 아님 |
| `missing_key` / `ports_type` | `ports` 없음 / 객체 아님 |
| `port_entry_type` | 포트 선언이 객체 아님 |
| `port_unknown_key` | 선언 키가 {direction, role} + `_` 밖 |
| `port_direction` | direction ∉ {input, output} |
| `port_role` | role 이 빈/비문자열 |
| `port_net_unknown` | 넷 ∉ `known_nets`(`known_nets is None` 이면 이 검사 안 함) |
| `port_on_rail` | 넷 ∈ `rails.nets`(`rails is None` 이면 이 검사 안 함) |
| `no_input_port` / `no_output_port` | 위반 없는 input / output 포트가 0개 |
`_` 접두 키는 포트가 아니다.

### 3.10 `dc_edges_unpruned(devices, passives, sources) -> tuple[DcEdge]` (DEC-70 유일 정의, 원소 이름순)
- 엣지 = 모든 netlist 원소의 (drain, source), kind ∈ `DC_CONDUCTING_PASSIVE_KINDS`(= `("resistor",)`)인 수동소자,
  모든 이상원. gate·bulk·커패시터·그 밖 수동 kind 는 엣지가 아님. 거부 없음.

### 3.11 `check_hidden_rails(rails, devices, passives, sources)` (DEC-60 (iii) + 선언 넷 존재)
| rule | 조건 |
|---|---|
| `rail_not_connected` | supply_nets 넷이 어느 단자(MOS d/g/s/선언 bulk, 2단자 terminals)에도 없음 |
| `hidden_rail` | MOS 단자에 없고 2단자 원소 단자에만 있는 넷이, 3.10 엣지로 어느 레일에도 닿지 않는데 레일 선언에 없음. `elements` = 넷 + 그 넷을 쓰는 2단자 원소 |
레일 판정은 선언 원소인가로만 한다(공격 14 (b): pushpull·sf 에서 supply_nets 의 `agnd` 만 빼면 `hidden_rail`).

## 4. 9회로 로드 결과 (실제 실행, 2026-10-07, 이 커밋의 코드 + library 원본)

| 회로 | 결과 | 사유 |
|---|---|---|
| common_gate_amplifier | 통과 | 소자 3, 수동 0(`[]`), 레일 2, 포트 in 1/out 1 |
| current_reuse_telescopic_ota | 통과 | 소자 51, 수동 12, 이상원 1, 포트 in 2/out 2. `N_cc_rz1/2` 는 Rz 로 DC 연결돼 숨은 레일 아님 |
| folded_cascode | **거부** | `passives / missing_key`(passive_elements 키 없음) -- CI-12. not_evaluated: name_uniqueness, ports.port_net_unknown, hidden_rails |
| ngcc_3stage_ff | 통과 | 소자 16, 수동 3 |
| nmcnr_amplifier | **거부** | `passives / missing_key` -- CI-12. not_evaluated 같음 |
| pushpull_follower_buffer | 통과 | 소자 6, 수동 1, 레일 3(agnd 선언) |
| sf_pushpull_output_opamp | 통과 | 소자 22, 수동 5, 이상원 1, 레일 3 |
| two_stage_ota | **거부** | `passives / missing_key` -- CI-12. not_evaluated 같음 |
| two_stage_ota_sf | 통과 | 소자 9, 수동 2 |

- 거부 3회로는 **CI-12 하나만** 걸린다: 메모리 안에서 `passive_elements: []` 로 바꾼 변형은 3개 모두 나머지 게이트를
  통과했다(파일은 고치지 않음). 단 nmcnr 은 topology 주석에 Cm1·Cm2·Rm·CL 이 적혀 있어 `[]` 가 회로 사실과 다르다 --
  사용자가 실제 선언을 써야 한다(design 8.1).
- 공격 14 (b) 확인: pushpull·sf 에서 `agnd` 만 뺀 변형 -> `hidden_rail @agnd`(pushpull elements (CL, agnd),
  sf (CL, Cc, agnd)). current_reuse 원본은 통과(오거부 0).
- 지문 확인: two_stage_ota_sf 에서 태그 키 4개 삭제 + `_note` 변경 + netlist 섞기 -> `connectivity_fp` 같음.

## 5. 설계(design 2.1)와 다르게 정한 점

1. **`devices.py` 신설**: netlist 원소 키·형식 검사와 `DeviceDecl` 생성을 맡는다(design 은 `topology_schema` 에 원소 키
   검사를 뒀다). 원소를 한 번만 돌고, 다른 선언과 같은 접근자 형식이 된다.
2. **공용 helper 3개**: `_rejection.py`(reject·require_object), `_two_terminal.py`(수동·이상원 공통 원소 규칙),
   `_terminal_nets.py`(단자 넷 집합 -- hidden_rails·topology_load). 각 공개 함수는 2개 이상 파일이 쓴다.
3. **선언 넷 존재 검사(`rail_not_connected`)는 `hidden_rails.py`**: 단자 정보가 필요해 `rail_declaration` 은 B26-1
   계약 그대로(선언만) 두었다.
4. **`dc_edges_unpruned` 인자**: raw doc 대신 검증된 선언 tuple(devices, passives, sources) -- 파싱을 두 번 하지 않는다.
5. **`port_declaration` 인자**: `(doc, rails, known_nets)`. 단독 호출 시 None 을 주면 그 두 검사를 하지 않는다.
6. **옛 이름 거부 훅(빈 표)은 만들지 않았다**: 쓰는 곳이 없는 빈 훅이라(만들면 배선 원칙) MG 단계에서 행과 함께 만든다.
7. 층(`_module_map.LAYERS` authoring): 0 = topology_model·_terminal_nets, 1 = _rejection·_two_terminal·dc_edges·
   linked_files·name_uniqueness·topology_schema, 2 = devices·hidden_rails·ideal_sources·json_read·passives·ports·rails,
   3 = topology_load.

## 6. 사용자 결정 대기 항목과의 관계

- **CI-12**: 기본안(키 없으면 거부)대로 구현 -> 위 3회로 거부. 결정이 (b)(통과 + review_needed)로 바뀌면
  `passive_declaration` 의 `missing_key` 분기만 바뀐다.
- **SP-1(supplies_v)·CI-14(bulk 기본 규칙)**: MOD2 범위 밖. `DeviceDecl.bulk` 는 선언값만 담고(9회로 모두 None),
  기본 규칙 적용은 graph(`bulk_default.py`)가 `supplies_v` 와 함께 한다.

## 7. [신규] 넷 이름 대소문자 충돌 `net_case_collision` (2026-10-07, 브랜치 ng-authoring2)

- 근거: `_drafts/engine/reference_review/SYNTHESIS.md` T15 (2)·3절 'MOD2 입력 게이트 -- 지금 가능', G4-09, G5-10
  (사고 '4·24차 넷 이름 대소문자 충돌'), FSM 155행 '0번 net 이름 대소문자 스캔 -- 자동 소문자 통일 없이 사람이 원본을 고친다'.
  전에는 원소 이름만 casefold 검사(3.8)해서 엔진은 받고 오라클 C4 가 막았다.
- 위치: 규칙 A(파일당 진입점 1개) 때문에 새 파일을 만들지 않고 `check_name_uniqueness` 에 규칙을 더했다. 추가 인자
  `supply_nets`·`port_nets` 는 기본값 `()` 라 기존 3인자 호출은 그대로다(원소 이름 검사 + 단자 넷 검사).
- `load_topology`: `supply_nets` 원본 list 의 비어 있지 않은 문자열 원소와 `ports` 원본 객체의 `_` 아닌 키를 넘긴다.
  rails·ports 선언이 다른 게이트에서 거부돼도 이 문자열은 쓸 수 있으므로 넷 검사는 돈다(새 `not_evaluated` 이름 없음).
  원소 선언 하나라도 거부되면 기존대로 `name_uniqueness` 전체가 `not_evaluated`(넷 검사 포함). 위반은 gate
  `name_uniqueness` 로 다른 위반과 함께 한 번에 거부한다(0절 형식 그대로).
- 다른 규칙과 겹침: 포트 키만 대소문자가 다르면 `port_net_unknown` 도, 레일 선언만 다르면 `rail_not_connected` 도 같이
  난다(둘 다 낸다 -- 원인 진단은 `net_case_collision` 이 준다).
- 실측(2026-10-07, 이 커밋 코드 + library 원본, `/c/g486` 임시 스크립트):
  - 9회로 `load_topology` **전부 통과**(오거부 0): common_gate 3/0/0, current_reuse 51/12/1, folded 13/1/1, ngcc 16/3/0,
    nmcnr 15/5/0, pushpull 6/1/0, sf_pushpull 22/5/1, two_stage 7/3/0, two_stage_sf 9/2/0 (소자/수동/이상원).
    (4절 표의 CI-12 거부 3회로는 topology 정정 b9c7042 뒤 통과 -- integration test 머리말과 같음.)
  - 거부 확인: current_reuse M2b drain `Vop1`→`vop1` -> hits `[net_case_collision ('Vop1','vop1')]` 하나,
    rejected_gates `("name_uniqueness",)`. two_stage_ota_sf `supply_nets` 에 기존 레일의 대소문자 변형 추가 ->
    `net_case_collision` + `rail_not_connected`. M1 gate `vin_n`→`VIN_N`(포트 키는 그대로) -> `net_case_collision`
    + `port_net_unknown`.
- test: 이 단계는 test 파일을 쓰지 않았다(작성자≠검증자). 필요한 test: 단자끼리·단자-레일·단자-포트 충돌 각 1,
  원소 이름-넷 이름 같은 casefold 는 통과, 3인자 호출 회귀, 9회로 오거부 0, rails·ports 거부 시에도 넷 검사가 도는지.

## 8. [신규] `authoring_anomalies` -- 구현하지 않음(정의 불명확, 보고)

SYNTHESIS T15 (1)은 '비차단 `authoring_anomalies`(dangling 넷, 대칭 미해결)'라고만 적는다. 구현하지 않은 이유:
1. **dangling 정의가 문서마다 다르다.** G4-08 = '채널 단자가 1개뿐이고 다른 단자가 없는 넷', TEC 104행 = 'net 참조
   카운트 1'. 레일·포트를 빼는지는 어느 쪽도 적지 않았다. 9회로 실측(2026-10-07):
   - G4-08 정의 그대로: common_gate `{gnd, vdd}`(레일 -- 소자 3개 회로라 레일 단자가 1개씩), 나머지 8회로 0.
     레일·포트를 빼면 9회로 전부 0.
   - TEC 정의(참조 1): common_gate {VNBias1, VNBias2, VPBias1, gnd, vdd}, folded·sf·two_stage·two_stage_sf {vin_n, vin_p},
     ngcc {VBN, Vinn, Vinp}, nmcnr {VB1, VB4, VB5, Vin_n, Vin_p}, pushpull {VNB1, VPB1, agnd} -- 입력 포트·gate 전용
     바이어스가 대부분이라 `bias_inputs`(Q9 (i), 사용자 결정 대기)와 겹친다.
   어느 정의·어떤 제외를 정본으로 할지 정해야 한다.
2. **'대칭 미해결'은 MOD2 에서 계산할 수 없다.** G4-19 의 대칭 미해결 목록은 `graph.symmetry` 출력이다. authoring(층 2)은
   graph(층 3)를 import 할 수 없고 태그 키도 읽지 않는다(IC4). 이 항목은 graph 또는 MOD9 `report/topology_review.py` 몫이다.
3. **소비자가 없다.** 비차단 보고를 받아 출력할 MOD9 `topology_review` 가 아직 없어(SYNTHESIS: MOD9 design 은 Q11 (iv) 뒤)
   지금 만들면 배선되지 않는 결과가 된다.
- 결정 필요: (a) dangling 정의(G4-08 채널 1개 / TEC 참조 1), (b) 레일·포트 제외 여부, (c) 결과를 어디에 담을지
  (`TopologyDoc` 필드 / 별도 함수) -- (c)는 MOD9 설계와 함께. `bias_inputs` 게이트는 9절에서 구현했다(2026-10-08).


## 9. [신규] `bias_inputs` -- gate 전용 외부 바이어스 넷 선언과 게이트 (2026-10-08, 브랜치 ng-q6-bias, 정정 대기열 Q6)

- 근거: 사용자 2026-10-07 "B는 추천대로 해."(SYNTHESIS Q9 (i)), 2026-10-08 "Q6는 반영해".
- 선택 최상위 키 `bias_inputs`: 넷 이름 문자열 list. connectivity 불변 선언이라 `connectivity_fp` 에 넣지 않는다.
  `TopologyDoc.bias_inputs`(정렬 tuple, 기본 `()`)로 노출. 코드: `bias_inputs.py`(`bias_input_declaration`), 이름 하드코딩 없음.
- gate 전용 넷 = MOS gate 에만 나타나고 drain/source/선언 bulk·수동소자·이상원 terminals·레일·포트 어디에도 없는 넷.
- 거부(gate `bias_inputs`): `gate_only_undeclared`(gate 전용인데 미선언), `bias_input_not_gate_only`(선언했는데 gate 전용 아님 --
  레일·포트·drain/source/bulk/2단자 단자, gate 에도 없는 넷 포함), `bias_inputs_type`, `bias_input_entry`, `bias_input_duplicate`.
  소자·수동·이상원·레일·포트 선언이 모두 통과했을 때만 돈다. 거부된 문서에서는 건너뛰며 `not_evaluated` 이름은 늘리지 않는다
  (기존 test 가 그 집합을 정확히 고정한다).
- 라이브러리 선언(재실측 = 제안 목록과 일치): common_gate {VNBias1, VNBias2, VPBias1}, folded {bias3}, ngcc {VBN, VBP},
  nmcnr {VB1..VB5}, pushpull {VNB1, VPB1}, two_stage {bias}, two_stage_sf {bias}. current_reuse·sf_pushpull 은 내부 바이어스라 선언 없음(통과).
- 소비처: SPICE 오라클 C15 (`tools/spice_oracle/oracle_netlist.py::topology_identity`)가 입력 `bias_voltages` 넷 집합 == topology `bias_inputs` 를 대조한다.

## 10. [신규] `source_manifest` -- 출처 개수 대조 (2026-10-08, 브랜치 ng-q6-bias, 정정 대기열 Q7)

- 근거: 사용자 2026-10-08 "Q7도 모두 맞아"(SYNTHESIS Q9 (iii)). 선택 최상위 키 `source_manifest{figure, device_count, passive_count}`,
  코드 `source_manifest.py::check_source_manifest`(`connectivity_fp` 불변, 키 없으면 검사 안 함).
- 대조: device_count == netlist MOS 수, passive_count == `passive_elements` 수(이상원 제외). 위반 gate `source_manifest`:
  `source_manifest_mismatch`(선언·실제 개수 둘 다 메시지에), `source_manifest_type`·`_key`·`_figure`·`_count`(형식).
  소자·수동 선언이 거부된 문서에서는 이 검사를 건너뛴다(`not_evaluated` 이름은 늘리지 않는다).
- 9회로 값(사용자 확인): common_gate 3/0, current_reuse 51/12, folded 13/1, ngcc 16/3, nmcnr 15/5, pushpull 6/1, sf_pushpull 22/5,
  two_stage 7/3, two_stage_sf 9/2 -- 9회로 전부 로드 통과(실제 개수와 일치).
