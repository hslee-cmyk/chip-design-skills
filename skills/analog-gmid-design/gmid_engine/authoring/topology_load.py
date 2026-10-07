"""topology 로더 -- 모든 로드 게이트를 돌려 위반을 전부 모은 뒤 한 번에 거부 (설계 design_mod3_s1_graph 2.1 `topology_load.py`, C00 §6.2).

진입점: `load_topology(path) -> TopologyDoc`.

순서: `load_json_checked`(JSON 수준 위반이면 그 `SchemaRejectedError` 를 그대로 낸다 -- 문서가 없으니 다음 게이트가 없다)
-> `check_topology_schema` -> `check_linked_files` -> 선언 접근자 `device_declaration`·`rail_declaration`·
`passive_declaration`·`source_declaration` -> `check_name_uniqueness` -> `port_declaration` -> `check_hidden_rails`.
접근자가 낸 `SchemaRejectedError` 는 그 hits 를 모으고 계속한다. 어떤 검사의 입력 선언이 거부됐으면 그 검사는
돌릴 수 없으므로 `not_evaluated` 에 이름을 남긴다(조용히 건너뛰지 않는다 -- 문서는 이미 거부된다):
`name_uniqueness`·`hidden_rails` 는 통째로, `port_declaration` 은 형식 검사는 그대로 하고 `ports.port_net_unknown`
(원소 선언 거부 시)·`ports.port_on_rail`(레일 선언 거부 시)만.

위반이 하나라도 있으면 `SchemaRejectedError` 한 번(개수로 자르지 않는다): detail =
{"gate": "topology_load", "where": 경로, "hits": SchemaHit tuple(게이트 순서), "rejected_gates": 위반을 낸 게이트 이름
정렬 tuple, "not_evaluated": 돌리지 못한 게이트 이름 tuple}.
통과하면 `TopologyDoc`(불변, `connectivity_fp`·`file_sha256`). 태그 키는 읽지 않는다. 결과를 캐시하지 않는다
(graph 밖 memo 는 LUT 하나뿐 -- 확정 사항 4; 로드 결과는 호출자가 S0 입력 객체로 들고 다닌다).
"""
from gmid_engine.core import SchemaRejectedError

from ._rejection import reject
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .devices import device_declaration
from .hidden_rails import check_hidden_rails
from .ideal_sources import source_declaration
from .json_read import load_json_checked
from .linked_files import check_linked_files
from .name_uniqueness import check_name_uniqueness
from .passives import passive_declaration
from .ports import port_declaration
from .rails import rail_declaration
from .topology_model import TopologyDoc
from .topology_schema import check_topology_schema

_GATE = "topology_load"


def load_topology(path):
    where = str(path)
    doc = load_json_checked(path, where)
    hits = []
    rejected = set()

    def run_check(gate, check, *args):
        found = check(*args)
        if found:
            rejected.add(gate)
            hits.extend(found)

    def run_accessor(gate, accessor, *args):
        try:
            return accessor(*args)
        except SchemaRejectedError as exc:
            rejected.add(gate)
            hits.extend(dict(exc.record.detail)["hits"])
            return None

    run_check("topology_schema", check_topology_schema, doc.data)
    if not isinstance(doc.data, dict):
        reject(_GATE, where, hits, rejected_gates=tuple(sorted(rejected)), not_evaluated=("all_declarations",))
    data = doc.data
    run_check("linked_files", check_linked_files, data)
    devices = run_accessor("devices", device_declaration, data)
    rails = run_accessor("rails", rail_declaration, data)
    passives = run_accessor("passives", passive_declaration, data)
    sources = run_accessor("ideal_sources", source_declaration, data)
    not_evaluated = []
    elements_ok = devices is not None and passives is not None and sources is not None
    if elements_ok:
        run_check("name_uniqueness", check_name_uniqueness, devices, passives, sources)
    else:
        not_evaluated.append("name_uniqueness")
    known_nets = None
    if elements_ok:
        known_nets = mos_terminal_nets(devices) | two_terminal_nets(passives + sources)
    else:
        not_evaluated.append("ports.port_net_unknown")
    if rails is None:
        not_evaluated.append("ports.port_on_rail")
    ports = run_accessor("ports", port_declaration, data, rails, known_nets)
    if elements_ok and rails is not None:
        run_check("hidden_rails", check_hidden_rails, rails, devices, passives, sources)
    else:
        not_evaluated.append("hidden_rails")
    if hits or not_evaluated:
        reject(_GATE, where, hits, rejected_gates=tuple(sorted(rejected)), not_evaluated=tuple(not_evaluated))
    return TopologyDoc.from_declarations(data["topology_name"], devices, passives, sources, rails.nets, ports,
                                         doc.sha256)

