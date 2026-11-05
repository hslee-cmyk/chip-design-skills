"""G_vgs 사이클 -- kvl_branch(v2)·port_diff(v1)·VDS-1 포화 부등식 (설계 design_mod3_structure_u2_u5 3.2, DEC-64, 용어집 92행).

진입점: `s1_gvgs` -- core `@compute_block`(writer `S1_GVGS_WRITER`, reads `GVGS_READS`,
writes `graph.rel_kvl_branch`·`graph.gvgs_summary`).

    snapshot = s1_gvgs(snapshot)

* G = MOS 마다 (gate, source) 무향 엣지, 모든 레일을 고정 노드 F 하나로 병합. gate·source 가 둘 다 레일인 소자는 VGS 가
  레일 차로 고정 -> `fixed_vgs` 에 기록. gate 넷 == source 넷(g == s, 레일이든 아니든)은 정지하지 않고 `gate_source_same` 에 적는다(자기 고리 -- G 엣지가 아니라 순환수 불변;
  레일 g = s 는 `fixed_vgs` 에도 든다, O-210 RR-6). 평행 엣지는 v0(= equal_vgs, `rel_vgs` 가 이미 기록)이라 이름순 첫 소자 하나만
  남긴 단순 그래프 Gs 를 쓴다.
* 개수(기저와 무관): P = 입력 포트 넷, c(H) = |E| − |V| + 성분 수. v2_port0 = c(Gs − P), v2_port1 = Σ_p [c(Gs − (P − {p}))
  − c(Gs − P)], v1 = c(Gs) − v2_port0 − v2_port1, cyclomatic = c(Gs).
* 멤버(어느 소자 gm_id 가 종속되는지는 GB7 `writer_plan` 몫 -- 여기서는 사이클만): 숲을 단계별로 키운다 -- (0) Gs − P 의
  엣지, (p) 포트 p 마다 (0)의 숲 사본에 p 에만 닿는 엣지, (끝) (0)의 숲에 각 (p) 단계 트리 엣지와 둘 이상 포트에 닿는 엣지.
  단계 안 엣지 순서 = 끝점 이름순(F 가 먼저). 비트리 엣지마다 기본 사이클 1개(그 엣지 + 숲 경로). (0)·(p) 사이클 =
  `rel_kvl_branch`(RelEdge kvl_branch, evidence.rule v2_rail = F 경유 / v2_zero), (끝) 사이클 = `gvgs_summary.port_diff`
  (제약 없음, 대조만). 사이클 멤버 합집합 = Gs 의 비다리 엣지(기저와 무관한 불변량). 단계별 비트리 엣지 수가 곧 위 개수다.
* VDS-1: diode 아닌 MOS 중 drain·source(레일 병합 후)가 서로 다르고 Gs 의 같은 성분에 있는 소자마다 사이클 1개(그 VDS
  엣지 + Gs 최단 경로, 이웃 이름순) = 포화 하한 부등식 `gvgs_summary.vds_saturation`. members = (그 소자,) + 경로 소자
  (drain 쪽부터) -- 경로가 그 소자 자신의 VGS 엣지를 지나면 같은 이름이 두 번 나온다(VDS·VGS 두 엣지). VDS 엣지 2개 이상 사이클은 기둥 창(W4)
  이라 기록하지 않는다.
* 모든 G_vgs 기록은 evidence.basis = (J12-c,) -- 판독(v1 제외·v2 대응·VDS-1 목록)은 공동분석 기본안(계획 DEC-64 그대로).
"""
from gmid_engine.authoring import INPUT_DIRECTION
from gmid_engine.core import compute_block, sorted_items

from .s1_values import (
    CYCLE_V2_RAIL,
    CYCLE_V2_ZERO,
    DOMAIN_DC,
    ELEMENT_MOS,
    GRAPH_KEY,
    GVGS_READS,
    GVGS_WRITES,
    J_GVGS_READING,
    MOS_DRAIN,
    MOS_GATE,
    MOS_SOURCE,
    REL_KVL_BRANCH,
    REL_PORT_DIFF,
    REL_VDS_SATURATION,
    S1_GVGS_WRITER,
    STATUS_DERIVED,
    Evidence,
    GvgsSummary,
    RelEdge,
)

_FIXED = (0, "")                                       # 레일 병합 고정 노드 F(넷 노드 (1, 넷)보다 앞에 정렬)


@compute_block(S1_GVGS_WRITER, reads=GVGS_READS, writes=GVGS_WRITES)
def s1_gvgs(projection):
    rails = frozenset(net for net, flag in projection.column("node", "is_rail") if flag)
    ports = tuple((1, net) for net, direction in projection.column("node", "port_direction")
                  if direction == INPUT_DIRECTION)
    pins = {name: dict(p) for name, p in projection.column("device", "pins")}
    is_diode = dict(projection.column("device", "is_diode"))
    mos = tuple(name for name, cls in projection.column("device", "element_class") if cls == ELEMENT_MOS)

    def node(net):
        return _FIXED if net in rails else (1, net)

    fixed = []
    same = []                                          # gate 넷 == source 넷 -- 레일이든 아니든 정지 없이 기록(쓰기 계획이 읽는다)
    simple = {}                                        # (u, v) 정렬 -> 대표 소자(이름순 첫)
    for name in mos:
        g, s = node(pins[name][MOS_GATE]), node(pins[name][MOS_SOURCE])
        if pins[name][MOS_GATE] == pins[name][MOS_SOURCE]:
            same.append(name)
        if g == s:
            if g == _FIXED:
                fixed.append(name)
            continue
        simple.setdefault(tuple(sorted((g, s))), name)
    edges = sorted_items(simple)
    port_set = frozenset(ports)
    stage0 = tuple(e for e in edges if not port_set.intersection(e[0]))
    base = _Forest()
    v2 = list(base.grow(stage0))
    tree_by_port = []
    for p in sorted(ports):
        forest = base.copy()
        only_p = tuple(e for e in edges if p in e[0] and not (port_set - {p}).intersection(e[0]))
        v2.extend(forest.grow(only_p))
        tree_by_port.append(forest.tree_added)
    v2_port1 = len(v2) - len(base.cycles_seen)
    final = base.copy()
    v1 = list(final.grow(tuple(e for added in tree_by_port for e in added)))
    v1.extend(final.grow(tuple(e for e in edges if len(port_set.intersection(e[0])) > 1)))
    kvl = tuple(RelEdge(REL_KVL_BRANCH, DOMAIN_DC, members, STATUS_DERIVED,
                        Evidence(CYCLE_V2_RAIL if _FIXED in nodes else CYCLE_V2_ZERO, _nets(nodes), (),
                                 (J_GVGS_READING,)))
                for members, nodes in v2)
    port_diff = tuple(RelEdge(REL_PORT_DIFF, DOMAIN_DC, members, STATUS_DERIVED,
                              Evidence(REL_PORT_DIFF, _nets(nodes), (), (J_GVGS_READING,)))
                      for members, nodes in v1)
    whole = _Forest()                                  # Gs 전체(최단 경로용, 숲이 아님)
    for (u, v), name in edges:
        whole.adjacency.setdefault(u, []).append((v, name))
        whole.adjacency.setdefault(v, []).append((u, name))
    vds = []
    for name in mos:
        d, s = node(pins[name][MOS_DRAIN]), node(pins[name][MOS_SOURCE])
        if is_diode[name] or d == s:
            continue
        path = whole.path(d, s)
        if path is not None:
            members, nodes = path
            vds.append(RelEdge(REL_VDS_SATURATION, DOMAIN_DC, (name,) + members, STATUS_DERIVED,
                               Evidence(REL_VDS_SATURATION, _nets(nodes), (), (J_GVGS_READING,))))
    summary = GvgsSummary(len(v2) + len(v1), len(base.cycles_seen), v2_port1, len(v1), tuple(fixed), port_diff,
                          tuple(vds), tuple(sorted(same)))
    return {("graph", "rel_kvl_branch"): {GRAPH_KEY: kvl}, ("graph", "gvgs_summary"): {GRAPH_KEY: summary}}


def _nets(nodes):
    return sorted_items({net for kind, net in nodes if kind})


class _Forest:
    """신장 숲(인접 + 소자). `grow(edges)` 는 엣지를 순서대로 넣으며 비트리 엣지마다 (멤버, 노드) 사이클을 돌려준다."""

    def __init__(self, adjacency=None, cycles_seen=()):
        self.adjacency = {k: list(v) for k, v in (adjacency or {}).items()}
        self.cycles_seen = tuple(cycles_seen)
        self.tree_added = ()

    def copy(self):
        return _Forest(self.adjacency, self.cycles_seen)

    def grow(self, edges):
        cycles = []
        added = []
        for (u, v), name in edges:
            path = self.path(u, v)
            if path is None:
                self.adjacency.setdefault(u, []).append((v, name))
                self.adjacency.setdefault(v, []).append((u, name))
                added.append(((u, v), name))
            else:
                members, nodes = path
                cycles.append((tuple(sorted((name,) + members)), nodes))
        self.tree_added = tuple(added)
        self.cycles_seen = self.cycles_seen + tuple(cycles)
        return tuple(cycles)

    def path(self, start, goal):
        """숲(또는 그래프) 안 start -> goal 최단 경로의 (소자 tuple, 노드 tuple) start 쪽부터, 없으면 None. 이웃은 이름순."""
        if start not in self.adjacency or goal not in self.adjacency:
            return None
        previous = {start: None}
        queue = [start]
        for here in queue:
            if here == goal:
                break
            for other, name in sorted(self.adjacency[here]):
                if other not in previous:
                    previous[other] = (here, name)
                    queue.append(other)
        if goal not in previous:
            return None
        members, nodes, here = [], [goal], goal
        while previous[here] is not None:
            here, name = previous[here]
            members.append(name)
            nodes.append(here)
        return tuple(reversed(members)), tuple(reversed(nodes))
