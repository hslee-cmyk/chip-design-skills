"""레일 선언과 연결의 정합 -- 숨은 레일 DEC-60 (iii) + 선언 넷 존재 (설계 design_mod3_s1_graph 2.1 `hidden_rails.py`).

진입점: `check_hidden_rails(rails, devices, passives, sources) -> tuple[SchemaHit]`.

* `rail_not_connected` -- `supply_nets` 의 넷이 어느 단자(MOS d/g/s/선언 bulk, 수동소자·이상원 terminals)에도 없다
  (오타 방지).
* `hidden_rail` -- MOS 단자에는 없고 수동소자·이상원 단자에만 있는 넷이, 가지치기 전 DC 전도 엣지(`dc_edges.py`)로 어느
  레일에도 닿지 않는데 `supply_nets` 에 없다(공격 14 (b): 커패시터 단자만 붙은 교류 기준 넷을 선언에서 빼면 거부).
레일 판정은 선언 집합의 원소인가로만 한다(넷 이름을 보지 않는다).
"""
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .dc_edges import dc_edges_unpruned
from .topology_model import SchemaHit


def check_hidden_rails(rails, devices, passives, sources):
    mos_nets = mos_terminal_nets(devices)
    other_nets = two_terminal_nets(passives + sources)
    hits = []
    for net in sorted(rails.nets - mos_nets - other_nets):
        hits.append(SchemaHit("rail_not_connected", "supply_nets",
                              "레일 선언 넷 " + repr(net) + " 이 어느 단자에도 없다", (net,)))
    adjacency = {}
    for edge in dc_edges_unpruned(devices, passives, sources):
        a, b = edge.nets
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)
    reached = set(rails.nets)
    frontier = sorted(rails.nets)
    while frontier:
        net = frontier.pop()
        for other in sorted(adjacency.get(net, ())):
            if other not in reached:
                reached.add(other)
                frontier.append(other)
    for net in sorted(other_nets - mos_nets - reached):
        users = sorted(x.name for x in passives + sources if net in x.terminals)
        hits.append(SchemaHit("hidden_rail", net,
                              "넷 " + repr(net) + " 은 수동소자·이상원 단자에만 있고(" + ", ".join(users)
                              + ") DC 전도 엣지로 어느 레일에도 닿지 않는데 supply_nets 에 없다(DEC-60 (iii) 숨은 레일)",
                              (net,) + tuple(users)))
    return tuple(hits)
