# gmid_engine.graph 동작 계약 (MOD3 S1, test 작성용)

- 대상: `gmid_engine/graph/` 공개 API(`gmid_engine.graph.__all__`). test 는 `from gmid_engine.graph import ...`,
  `from gmid_engine.authoring import ...`, `from gmid_engine.core import ...` 만 쓴다(파일 모듈 직접 import·`_` 이름 금지).
  배치는 규칙 D: `gmid_engine/tests/graph/test_<파일>.py`, 9회로 교차는 `tests/integration/`.
- 근거: `_drafts/engine/design_mod3_s1_graph.md` 2.2·3·4·5·6절, `NEW_ENGINE_DESIGN_REQUIREMENTS.md` 끝 '확정 사항'(최우선),
  `user_decisions.md` 2026-10-07(1번 supplies_v, 6번 bulk 기본 규칙), core `CONTRACT.md` 5·6절, authoring `CONTRACT.md`.
- 입력: `authoring.load_topology(path)` 결과 `TopologyDoc` + 인자 `supplies_v`. 엔진은 topology 의 `_` 키
  (`_declared_target_spec` 등)를 읽지 않는다 -- test 픽스처가 필요하면 test 쪽에서 꺼내 인자로 넘긴다.
- 기대값은 test 쪽이 topology JSON 을 직접 집계해 만든다(피검 함수로 기대값을 만들지 않는다). 아래 6절 숫자는
  작성자 측 교차 확인용(JSON 직접 집계와 엔진 실행이 일치함을 2026-10-07 확인)이다.

---

## 0. 파일과 진입점 (규칙 A~G, `_module_map` graph 층)

| 파일 | 층 | 독립 진입점 | 책임 |
|---|---|---|---|
| s1_values.py | 0 | (데이터 선언 모듈) `S1Key`·`BulkResult`·`FieldNotComputed` + 어휘·`S1_WRITERS` | 값 형식·어휘·필드 권한표 |
| supplies.py | 0 | `supplies_declaration` | supplies_v 검사·정규화 |
| ac_ground_static.py | 1 | `static_ac_ground` | 교류접지 (1)(2) |
| bulk_default.py | 1 | `s1_bulk`(`@compute_block`) | device.bulk |
| s1_index.py | 1 | `terminal_index` | 넷별 단자 인덱스 |
| s1_key.py | 1 | `s1_key` | S1 지문 |
| s1_model.py | 1 | `S1Graph` | S1 스냅샷·질의 |
| s1_structure.py | 2 | `s1_structure`(`@compute_block`) | node·device 구조 필드 |
| s1_build.py | 3 | `build_s1` | 공개 진입점(빌드 순서·재사용) |

## 1. `build_s1(doc, supplies_v=None, previous=None) -> S1Graph`

- 순서: `supplies_declaration(supplies_v, doc.rails)` -> `s1_key(doc, supplies)` -> (`previous.key == key` 이면
  `previous` 를 **그대로**(`is`) 반환, 블록 호출 0) -> `s1_structure(base, doc.devices, doc.passives, doc.sources,
  정렬 레일 tuple, doc.ports)` -> `s1_bulk(snapshot, supplies)` -> `S1Graph(key, snapshot)`.
  `base` = `previous.snapshot`(있으면) 또는 `GraphSnapshot.empty(S1_WRITERS)`.
- 재사용(확정 사항 1·2·5):
  - 같은 doc·supplies_v 로 `previous` 를 넘기면 같은 객체, 두 블록 계수 변화 0.
  - supplies_v 만 바꿔 `previous` 를 넘기면 `s1_structure` 는 reuse(입력 버전 같음), `s1_bulk` 만 compute.
    node 레코드는 모두 이전 스냅샷과 같은 객체(`snapshot.record("node", k) is ...`), device 레코드는 bulk 필드가
    바뀌므로 새 객체.
  - `previous` 없이 같은 doc 으로 두 번 부르면 두 번 계산하고 `s1_structure.stats().recomputes_same_input` 이 1 오른다
    (정상 파이프라인 기대값 0 -- 호출자가 이전 S1 을 넘겨야 한다. graph 밖 memo 는 두지 않는다).
  - 연결 투영이 같으면(`_` 주석만 바뀐 파일, 태그 키 삭제, netlist 순서 섞기) 키가 같다(`connectivity_fp` 동일).
- 실패:
  - `doc` 이 `TopologyDoc` 아님 -> `TypeError`. `previous` 가 S1Graph 가 아니거나 권한표가 `S1_WRITERS` 와 다름 -> `TypeError`.
  - supplies_v 위반 -> `SchemaRejectedError`(2절).
  - bulk 기본 규칙 정지 -> `StructureUnresolvedError`(4절).

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
  = (ac_ground_static, bulk_default, s1_build, s1_index, s1_structure, s1_values, supplies).py. 같은 소스면 프로세스·
  `PYTHONHASHSEED` 와 무관하게 같다.
- `supplies_v_fp` = `fp_of(supplies)`, supplies None 이면 `NO_SUPPLIES_FP`(`"none"`). 전위 하나라도 다르면 다르다.
- `S1Key` 는 frozen dataclass(`==` 는 세 값 비교).

## 4. 필드 정의 (core GraphSnapshot, 권한표 `S1_WRITERS`)

레코드 key: node = 넷 이름, device = 원소 이름(MOS·수동소자·이상원 한 이름 공간, IC3). 값은 모두 불변.
각 필드의 `snapshot.field(kind, key, field)` 는 core `FieldValue`(writer·input_version·write_count)다.

### 4.1 writer `S1_STRUCTURE_WRITER` = `"s1_structure"` (`s1_structure` 블록, reads 없음)

node 레코드 = 단자 넷(MOS d/g/s, 2단자 terminals) ∪ 선언 bulk 넷 ∪ 레일. 모든 node 에 아래 5필드가 있다.

| 필드 | 값 |
|---|---|
| `terminals` | ((원소, 단자), ...) 정렬. 단자 ∈ `MOS_TERMINAL_NAMES`(`d`,`g`,`s`) ∪ authoring `TWO_TERMINAL_NAMES`(`t0`,`t1`). bulk 미포함(bulk 만 있는 넷은 `()`) |
| `is_rail` | 넷 ∈ `doc.rails` |
| `port_direction` / `port_role` | 포트면 direction(`input`/`output`)·role, 아니면 None |
| `ac_ground_class` | `AC_GROUND_RAIL`(`"rail"`) = 레일. `AC_GROUND_GATE_ONLY`(`"gate_only_undriven"`) = 레일 아님·입력 포트 아님·단자가 전부 `g`. 그 밖(단자 없는 넷 포함) None |

device 레코드 = 모든 원소.

| 필드 | 대상 | 값 |
|---|---|---|
| `element_class` | 전부 | `ELEMENT_MOS`(`"mos"`) / `ELEMENT_PASSIVE`(`"passive"`) / `ELEMENT_SOURCE`(`"ideal_source"`) |
| `kind` | 전부 | 선언 kind 그대로 |
| `pins` | 전부 | MOS `(("d", drain), ("g", gate), ("s", source))`, 2단자 `(("t0", 첫 넷), ("t1", 둘째 넷))`(문서 순서) |
| `bulk_declared` | MOS | 선언 bulk 넷 또는 None |
| `is_diode` | MOS | gate == drain |
| `value_key` / `value` | 2단자 | authoring 투영 그대로(미선언 None) |
| `unsupported` | 지원 kind 밖 원소만 | 분기 이름: MOS kind ∉ {nmos, pmos} -> `mos_kind_unsupported`, 수동 kind ∉ {capacitor, resistor} -> `passive_kind_unsupported`, 이상원 kind ∉ {current_source} -> `source_kind_unsupported`(이상 전압원 포함 -- 교류접지 (3) 미구현, DEC-76 안전망). 기록만 하고 정지하지 않는다(정지는 그 원소를 쓰는 소비자 몫, C00 §7.1) |

### 4.2 writer `S1_BULK_WRITER` = `"s1_bulk"` (`s1_bulk` 블록, reads `device.{bulk_declared, element_class, kind, pins}`, `node.is_rail`, extras `(supplies,)`)

MOS 레코드마다 `bulk` = `BulkResult(net, origin, reason)`:

| 우선순위 | 조건 | 값 |
|---|---|---|
| 1 | `bulk_declared` 있음 | `(그 넷, "declared", None)` |
| 2 | kind ∉ {nmos, pmos} | `(None, "undetermined", "unsupported_kind")` |
| 3 | supplies None | `(None, "undetermined", "needs_supplies_v")` |
| 4 | 그 밖 | `(최저 전위 레일, "default_rule", None)`(nmos) / `(최고 전위 레일, "default_rule", None)`(pmos) -- 레일 이름이 아니라 supplies 전위 값으로 고른다. 원점 이동 불변(±0.9 와 0/1.8 이 같은 넷을 고른다) |

정지 검사(4번 규칙을 쓸 소자가 하나라도 있고 supplies 가 있을 때만, 결과는 core `StructureUnresolvedError`, exit 2,
`detail["reason"] == "unsupported_rule_branch"`):

| `rule_branch` | 조건 | detail / devices |
|---|---|---|
| `bulk_rail_potential_tie` | 최저 또는 최고 전위를 가진 레일이 둘 이상(레일 0 포함) | `rails`(동률 넷 정렬), `potential` |
| `bulk_multi_domain` | 채널 레일 집합 ⊄ {최저 전위 레일, 최고 전위 레일}. 채널 레일 = nmos·pmos 의 d 또는 s 가 닿는 레일 선언 넷 | `channel_rails`(정렬), `bulk_rails`(최저, 최고), `outside_rails`(정렬); `record.devices` = 바깥 레일에 d/s 가 닿는 소자 |

다중 도메인 판정의 뜻: 단일 도메인 회로의 MOS 채널은 최저·최고 전위 레일에만 닿는다. 중간 전위 레일이나 최저·최고가
아닌 레일(예: 서로 다른 고전위 레일 둘에 pmos source)에 채널이 닿으면 bulk 를 하나의 극값 레일로 묶는 것이 회로 사실과
다를 수 있어 조용히 묶지 않는다. 커패시터·저항만 붙은 레일(교류 기준 `agnd` 등)은 채널 레일이 아니라 걸리지 않는다.
9회로 실측은 7절.

### 4.3 예약 필드 (`RESERVED_FIELDS`, 다음 단계 writer -- 이번 단계 값 없음)

| (kind, field) | writer | 다음 단계 |
|---|---|---|
| (`device`, `dc_role`) | `dc_roles` | U4 DC 역할 |
| (`edge`, `relation`) | `relations` | U3 관계 엣지·declared 대조 |
| (`graph`, `branches`) | `dc_conduction` | U2 가지(segments 는 병렬 소자를 한 segment 에 담는 중립 표현 -- 41 대 62 셈은 사용자 결정 대기) |
| (`graph`, `columns`) | `columns` | U2 기둥 |

## 5. `S1Graph(key, snapshot)` 질의

- `key`: S1Key, `snapshot`: core GraphSnapshot(`writers == S1_WRITERS`). frozen.
- `column(kind, field)` -> `snapshot.column(kind, field)` 와 같은 key 정렬 tuple `((key, value), ...)`.
- `value(kind, key, field)` -> 값. 그 레코드·필드가 없으면 `KeyError`.
- 공통 실패: (kind, field) 가 `S1_WRITERS` 에 없음 -> `KeyError`. 있으나 그 writer 의 `snapshot.block_version(writer)`
  가 None -> `FieldNotComputed`(`LookupError` 하위; 빈 tuple 을 돌려주지 않는다). 이번 단계 S1 에서 4.3 네 필드는
  항상 `FieldNotComputed`.
- 결정론: 같은 doc·supplies_v 면 `snapshot.fp` 가 프로세스·`PYTHONHASHSEED`·netlist 순서와 무관하게 같다.

## 6. 부품 함수

- `terminal_index(devices, passives, sources)` -> 넷 이름순 `((넷, ((원소, 단자), ...)), ...)`. bulk 미포함.
- `static_ac_ground(index, rails, input_nets)` -> index 넷 순서 그대로 `((넷, 분류|None), ...)`(4.1 규칙).
- `s1_structure(snapshot, devices, passives, sources, rails, ports)` / `s1_bulk(snapshot, supplies)` -- core
  `ComputeBlock`(`stats()`·`reset_stats()`). 직접 부를 때 extras 는 불변이어야 한다(core 6.2).

## 7. 9회로 실측 (2026-10-07, 이 커밋 코드 + library 원본, JSON 직접 집계와 일치)

supplies_v: two_stage_ota·current_reuse·folded·common_gate = 사용자 확정 `{vdd: 1.8, gnd: 0}`; ngcc·nmcnr·pushpull·sf =
topology `_declared_target_spec.supplies_v`(`_comment` 제외); two_stage_ota_sf = 없음(None).

### 7.1 지금 만들 수 있는 6회로 (기대 집계값)

| 회로 | node 수 | 레일 | MOS(n/p) | 수동 | 이상원 | is_diode 참 | gate_only_undriven | 포트 in/out | bulk |
|---|---|---|---|---|---|---|---|---|---|
| common_gate_amplifier | 7 | gnd, vdd | 3 (2/1) | 0 | 0 | 0 | VNBias1, VNBias2, VPBias1 | 1/1 | default gnd 2, vdd 1 |
| current_reuse_telescopic_ota | 37 | gnd, vdd | 51 (24/27) | 12 | 1 | 16 (M11a, M11b, M14a, M14b, M18_bg, M20a, M20b, M23a, M24b, M36a, M36b, M39, M40, M57, M64, M66) | 없음 | 2/2 | default gnd 24, vdd 27 |
| ngcc_3stage_ff | 13 | gnd, vdd | 16 (9/7) | 3 | 0 | 3 (M3, M6A, M9) | VBN, VBP | 2/1 | default gnd 9, vdd 7 |
| pushpull_follower_buffer | 9 | agnd, vdd, vss | 6 (3/3) | 1 | 0 | 0 | VNB1, VPB1 | 1/1 | default vss 3, vdd 3 (agnd 0) |
| sf_pushpull_output_opamp | 23 | agnd, vdd, vss | 22 (11/11) | 5 | 1 | 1 (M4) | 없음 | 2/1 | default vss 11, vdd 11 (agnd 0) |
| two_stage_ota_sf | 10 | gnd, vdd | 9 (6/3) | 2 | 0 | 1 (M3) | bias | 2/1 | undetermined(needs_supplies_v) 9 |

6회로 모두 `unsupported` 열 `()`, 4.3 필드 `FieldNotComputed`, `build_s1(doc, sv, previous=s1) is s1`.

### 7.2 authoring 이 거부하는 3회로 (CI-12 대기 -- 기대값 test 는 결정 뒤)

folded_cascode·nmcnr_amplifier·two_stage_ota 는 `load_topology` 가 `passives / missing_key` 로 거부한다(authoring 계약 4절).
참고로 메모리 안 `passive_elements: []` 변형으로 돌린 값: folded node 14, MOS 13 (6/7), 이상원 1, diode 4 (M7, M9, MN, MP),
gate_only bias3, bulk gnd 6·vdd 7 / nmcnr node 17, MOS 15 (7/8), diode 2 (M108, M203), gate_only VB1~VB5, bulk vss 7·vdd 8 /
two_stage_ota node 9, MOS 7 (4/3), diode 1 (M3), gate_only bias, bulk gnd 4·vdd 3. nmcnr 는 주석의 Cm1·Cm2·Rm·CL 이
선언되면 값이 바뀐다(`[]` 는 회로 사실이 아님).

### 7.3 다중 도메인 판정 실측

| 회로 | 레일(전위) | 채널 레일 | {최저, 최고} | 판정 |
|---|---|---|---|---|
| 2레일 7회로 | vdd/gnd(1.8/0) 또는 vdd/vss(0.9/-0.9) | 두 레일 | 같은 두 레일 | 통과(two_stage_ota_sf 는 supplies 없음이라 검사 미적용, 채널 레일 2개) |
| pushpull_follower_buffer | vdd 1.8, vss 0, agnd 0.9 | vdd, vss (agnd 는 CL 단자만) | vss, vdd | 통과 |
| sf_pushpull_output_opamp | vdd 1.8, vss 0, agnd 0.9 | vdd, vss (agnd 는 CL·Cc 단자만) | vss, vdd | 통과 |

9/9 통과(오정지 0). 정지가 실제로 걸리는 증거(메모리 변형): pushpull 에서 nmos 하나의 source 를 agnd 로 -> `bulk_multi_domain`
(outside agnd, devices (M6,)); sf 에 레일 vddx(1.5) 를 더하고 pmos source 하나를 옮김 -> outside vddx; 같은 변형에 vddx 3.3 ->
outside vdd(최고가 vddx 로 바뀜, vdd 에 d/s 가 닿는 소자 6개); pushpull supplies agnd 0 -> `bulk_rail_potential_tie`(agnd, vss).

## 8. 다음 단계 (이번 단계에서 만들지 않음 -- 호출자가 생길 때 그 단계에서 만든다)

- 질의: `degree(net)`, `gs_groups()`(같은 (kind, gate, source) 2개 이상), `channel_edges()`, `bulk_users(net)`,
  `diodes()`, kind 별 원소 목록 -- U2~U5 규칙 함수가 생길 때 인덱스 필드와 함께.
- S1 스냅샷 디스크 캐시(확정 6 E3, 키 = `S1Key`).
- 회로 spec 로더(supplies_v 출처, DEC-60 (i) 3레일·음전위 검사)와 `S0` 전체 지문.
- 4.3 예약 필드의 writer 블록(U2·U3·U4). 권한표를 늘리면 `S1_WRITERS` 가 바뀌어 새 lineage 가 된다.

## 9. 설계(design_mod3_s1_graph)와 다르게 정한 점

1. **S1 저장 = core GraphSnapshot**(사용자 지시): 설계 3절의 `S1Graph` 필드 묶음(nodes·devices·passives·sources FrozenMap,
   stamps) 대신 node·device 레코드 필드로 두고, 필드 메타(writer·입력 버전)는 core `FieldValue` 가 맡는다. 수동소자·이상원도
   device 레코드(`element_class` 로 구분, 이름 공간 하나 -- IC3).
2. **계산 블록 2개**(규칙 C): `s1_structure`(구조)·`s1_bulk`(bulk). supplies_v 만 바뀌면 bulk 만 다시 계산한다. 그래서
   `bulk_default.py` 진입점은 설계의 `bulk_net(...)` 함수가 아니라 블록 `s1_bulk` 다.
3. **`supplies.py` 신설**: supplies_v 검사(키 = 레일 선언, 유한 실수)를 한 곳에 둔다.
4. **인덱스 축소**: `terminal_index` 는 넷별 단자만 만든다(`node.terminals` 와 교류접지 (2)가 실제로 쓴다).
   `gs_groups`·`channel_adj` 와 4절 질의 대부분은 소비자가 없어 8절로 미뤘다(만들고 안 쓰는 함수 금지).
5. **`unsupported`**: 설계의 그래프 수준 목록 대신 원소별 필드(`device.unsupported`) -- writer 하나로 쓰고 열로 질의한다.
6. **다중 도메인·전위 동률 정지**(사용자 확정 6번): 설계에 없던 분기. `StructureUnresolvedError`(N3.14 STRUCTURE_UNRESOLVED,
   reason `unsupported_rule_branch`)를 graph 가 바로 낸다 -- 조용히 묶는 대신 bulk 결정 시점에 정지.
7. **`rule_fp`**: graph 파일 바이트 sha256(`S1_RULE_FILES`). 블록 입력 버전(core code_hash = 블록 함수 바이트코드)과 별개로
   S1 키 수준에서 helper 코드 변경까지 덮는다.
8. **authoring `__all__` 에 `INPUT_DIRECTION` 추가**: 교류접지 (2)의 '입력 포트 아님' 판정이 같은 어휘를 다시 정의하지 않게 했다.
