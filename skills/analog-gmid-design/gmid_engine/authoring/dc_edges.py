"""DC 전도 엣지 정의 -- 엔진에서 이 정의를 두는 유일한 곳 (DEC-70, 설계 design_mod3_s1_graph 2.1 `dc_edges.py`).

진입점: `dc_edges_unpruned(devices, passives, sources) -> tuple[DcEdge]` (원소 이름순).

DC 전도 엣지 = MOS 채널 drain–source(netlist 원소 전부; gate·bulk 는 엣지가 아님), kind 가 `DC_CONDUCTING_PASSIVE_KINDS`
인 수동소자(저항), 이상원 전부. 커패시터와 그 밖 수동 kind 는 엣지가 아니다. 잎 가지치기 **전** 목록이다 -- graph
`dc_conduction`(U2)이 이 정의를 import 해 가지치기를 한다(같은 개념의 두 번째 정의를 만들지 않는다).
"""
from .topology_model import DcEdge

DC_CONDUCTING_PASSIVE_KINDS = ("resistor",)


def dc_edges_unpruned(devices, passives, sources):
    edges = [DcEdge(x.name, x.kind, tuple(sorted((x.d, x.s)))) for x in devices]
    edges.extend(DcEdge(x.name, x.kind, tuple(sorted(x.terminals)))
                 for x in passives if x.kind in DC_CONDUCTING_PASSIVE_KINDS)
    edges.extend(DcEdge(x.name, x.kind, tuple(sorted(x.terminals))) for x in sources)
    return tuple(sorted(edges, key=lambda e: e.element))
