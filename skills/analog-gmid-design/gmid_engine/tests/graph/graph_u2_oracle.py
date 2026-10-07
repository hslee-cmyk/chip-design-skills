"""U2~U4 test 쪽 독립 oracle -- topology JSON(dict)만 읽고 계약 `graph/CONTRACT.md` 4.3~4.5 문장을 그대로 다시 구현한다.

엔진(gmid_engine.graph)을 import 하지 않는다(값 형식 비교는 test 가 엔진 dataclass 를 plain tuple 로 풀어 한다).
여기서 만드는 값은 모두 plain tuple/dict:

- DC 엣지(authoring CONTRACT 3.10): MOS (drain, source), kind == resistor 인 수동소자, 이상원 전부. 커패시터 등은 엣지 아님.
- 잎 가지치기(4.3-2): 레일·포트가 아닌 넷 중 DC 엣지가 저항 하나뿐인 넷 + 그 저항. 라운드 시작 시점 잎을 이름순 처리, 반복.
- 병렬 합침(4.3-3): 같은 무향 넷 쌍 엣지 -> segment (nets 정렬, elements 이름순), nets 순.
  `merge=False` 는 병렬 원소를 따로 센 병기값(7.3 '따로')용: segment = 원소 하나.
- 가지(s1_branches), 기둥(s1_columns: 레일 쌍 모든 조합, 노드-단순 경로 DFS, 이웃 순서 (반대 넷, 가지 id)).
- gs 묶음, DC 역할 표, 관계 엣지, G_vgs 개수(c(H) = |E| - |V| + 성분 수), 비다리 엣지, VDS-1 대상.
"""
from __future__ import annotations

import itertools
from collections import defaultdict

MOS_KINDS = ("nmos", "pmos")
F = "\x00F"          # G_vgs 고정 노드(모든 레일) -- 어떤 넷 이름보다 앞에 정렬


class StopExpected(Exception):
    def __init__(self, branch, devices=(), **detail):
        super().__init__(branch)
        self.branch = branch
        self.devices = tuple(devices)
        self.detail = detail


def _cyclomatic(edges):
    """edges: iterable of (a, b) a != b. c = |E| - |V| + 성분 수 (V = 엣지가 닿는 노드)."""
    edges = list(edges)
    parent = {}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        parent.setdefault(a, a)
        parent.setdefault(b, b)
    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    comps = len({find(x) for x in parent})
    return len(edges) - len(parent) + comps


class U2Oracle:
    def __init__(self, raw: dict, merge: bool = True, column_limit=None):
        self.raw = raw
        self.mos = {e["name"]: e for e in raw["netlist"]}
        self.passives = {e["name"]: e for e in (raw.get("passive_elements") or [])}
        self.sources = {e["name"]: e for e in (raw.get("ideal_sources") or [])}
        self.rails = frozenset(raw["supply_nets"])
        self.ports = {k: v for k, v in raw["ports"].items() if not k.startswith("_")}
        self.input_ports = frozenset(k for k, v in self.ports.items() if v["direction"] == "input")
        self.merge = merge
        self.column_limit = column_limit
        self._dc()
        self._branches()
        self._columns()
        self._u3()
        self._u4()
        self._gvgs()

    # ------------------------------------------------------------ U2
    def dc_nets_of(self, name):
        if name in self.mos:
            e = self.mos[name]
            return tuple(sorted((e["drain"], e["source"])))
        if name in self.passives:
            e = self.passives[name]
            return tuple(sorted(e["terminals"])) if e["kind"] == "resistor" else None
        return tuple(sorted(self.sources[name]["terminals"]))

    def _dc(self):
        # 정지 검사 1: 지원 밖 원소 / 자기 고리
        unsup = {}
        for n, e in self.mos.items():
            if e["kind"] not in MOS_KINDS:
                unsup[n] = "mos_kind_unsupported"
        for n, e in self.passives.items():
            if e["kind"] not in ("capacitor", "resistor"):
                unsup[n] = "passive_kind_unsupported"
        for n, e in self.sources.items():
            if e["kind"] != "current_source":
                unsup[n] = "source_kind_unsupported"
        self.unsupported = unsup
        if unsup:
            first = unsup[min(unsup)]
            raise StopExpected(first, sorted(n for n, b in unsup.items() if b == first), nets=())
        edges = {}
        for n in list(self.mos) + list(self.passives) + list(self.sources):
            p = self.dc_nets_of(n)
            if p is not None:
                edges[n] = p
        loops = sorted(n for n, (a, b) in edges.items() if a == b)
        if loops:
            raise StopExpected("dc_self_loop", loops, nets=tuple(sorted({edges[n][0] for n in loops})))
        # 잎 가지치기
        remaining = dict(edges)
        pruned = []
        rnd = 0
        while True:
            rnd += 1
            inc = defaultdict(list)
            for n, (a, b) in remaining.items():
                inc[a].append(n)
                inc[b].append(n)
            leaves = sorted(net for net, es in inc.items()
                            if net not in self.rails and net not in self.ports and len(es) == 1
                            and es[0] in self.passives)
            if not leaves:
                break
            removed = []
            for net in leaves:
                el = inc[net][0]
                if el in remaining:
                    del remaining[el]
                    removed.append(el)
            pruned += [(el, rnd) for el in sorted(removed)]
        self.dc_pruned = tuple(pruned)
        self.edges = remaining
        groups = defaultdict(list)
        for n, pair in remaining.items():
            groups[pair if self.merge else pair + (n,)].append(n)
        self.segments = tuple(sorted(((k[0], k[1]), tuple(sorted(v))) for k, v in groups.items()))

    def _branches(self):
        seg = list(self.segments)
        at = defaultdict(list)
        for i, (nets, _) in enumerate(seg):
            at[nets[0]].append(i)
            at[nets[1]].append(i)
        deg = {net: len(v) for net, v in at.items()}
        self.branch_nodes = frozenset(n for n, d in deg.items() if n not in self.rails and d >= 3)
        anchors = set(self.rails) | self.branch_nodes | {n for n, d in deg.items() if d == 1}

        def other(i, net):
            a, b = seg[i][0]
            return b if a == net else a

        used = set()
        branches = []
        for a in sorted(anchors):
            for i in sorted(at.get(a, ()), key=lambda i: (other(i, a), seg[i][1])):
                if i in used:
                    continue
                chain = [i]
                used.add(i)
                cur = other(i, a)
                while cur not in anchors:
                    nxt = [j for j in at[cur] if j not in used]
                    assert len(nxt) == 1, (cur, nxt)
                    j = nxt[0]
                    used.add(j)
                    chain.append(j)
                    cur = other(j, cur)
                els = [el for j in chain for el in seg[j][1]]
                branches.append((len(branches), (a, cur), tuple(seg[j] for j in chain),
                                 any(el in self.sources for el in els)))
        left = [i for i in range(len(seg)) if i not in used]
        if left:
            raise StopExpected("dc_isolated_loop", sorted(el for i in left for el in seg[i][1]),
                               nets=tuple(sorted({n for i in left for n in seg[i][0]})))
        self.branches = tuple(branches)

    def _columns(self):
        adj = defaultdict(list)
        for bid, (a, b), _segs, _src in self.branches:
            if a == b:
                continue
            adj[a].append((b, bid))
            adj[b].append((a, bid))
        for k in adj:
            adj[k].sort()
        cols, pairs = [], []
        total = 0
        for r1, r2 in itertools.combinations(sorted(self.rails), 2):
            found = []

            def dfs(node, visited, path):
                nonlocal total
                for nb, bid in adj.get(node, ()):
                    if nb == r2:
                        found.append(tuple(path + [bid]))
                        total += 1
                        if self.column_limit is not None and total > self.column_limit:
                            raise StopExpected("column_enumeration_over_budget", (), limit=self.column_limit,
                                               rails=(r1, r2))
                        continue
                    if nb in self.rails or nb in visited:
                        continue
                    dfs(nb, visited | {nb}, path + [bid])

            dfs(r1, {r1}, [])
            pairs.append((r1, r2, len(found)))
            for path in found:
                expansion = 1
                src = False
                for bid in path:
                    for _nets, els in self.branches[bid][2]:
                        expansion *= len(els)
                    src = src or self.branches[bid][3]
                basis = ("J13-a", "J13-b", "J13-c") + (("J13-d",) if src else ())
                cols.append((len(cols), (r1, r2), path, expansion, "derived",
                             ("rail_pair_simple_path", (r1, r2), (), basis)))
        self.columns = tuple(cols)
        self.column_pairs = tuple(pairs)
        in_col = {bid for c in cols for bid in c[2]}
        self.column_orphans = tuple((b[0], "review_needed") for b in self.branches if b[0] not in in_col)

    # ------------------------------------------------------------ U3
    def _u3(self):
        groups = defaultdict(list)
        for n, e in self.mos.items():
            groups[(e["kind"], e["gate"], e["source"])].append(n)
        self.gs_groups = tuple((k[0], k[1], k[2], tuple(sorted(v)))
                               for k, v in sorted(groups.items()) if len(v) >= 2)
        # 교류접지 G (4.4: ac_ground_class in {rail, gate_only_undriven})
        term = defaultdict(list)
        for n, e in self.mos.items():
            term[e["drain"]].append("d")
            term[e["gate"]].append("g")
            term[e["source"]].append("s")
        for e in list(self.passives.values()) + list(self.sources.values()):
            for t in e["terminals"]:
                term[t].append("t")
        gate_only = {net for net, ts in term.items()
                     if net not in self.rails and net not in self.input_ports and ts and all(x == "g" for x in ts)}
        self.ground = frozenset(self.rails) | gate_only
        roles = {}
        diode = {n for n, e in self.mos.items() if e["gate"] == e["drain"]}
        self.diodes = tuple(sorted(diode))
        for n in diode:
            e = self.mos[n]
            roles[n] = ("diode_reference", "derived", ("1", (e["gate"], e["source"]), (), ()))
        for kind, g, s, members in self.gs_groups:
            if any(m in diode for m in members):
                for m in members:
                    if m not in diode:
                        roles[m] = ("bias_current_source", "derived", ("2", (g, s), members, ()))
            elif g in self.ground:
                for m in members:
                    roles[m] = ("bias_current_source", "derived", ("2", (g, s), members, ("J-U3-a",)))
            else:
                for m in members:
                    roles[m] = ("signal", "review_needed", ("2", (g, s), members, ("J-U3-c",)))
        for n, e in self.mos.items():
            if n in roles:
                continue
            if e["gate"] in self.ground and e["source"] in self.rails:
                roles[n] = ("bias_current_source", "derived", ("3", (e["gate"], e["source"]), (), ("J-U3-a",)))
            else:
                roles[n] = ("signal", "derived", ("5", (e["gate"], e["source"]), (), ()))
        self.dc_roles = roles

    # ------------------------------------------------------------ U4
    def _u4(self):
        self.equal_vgs = tuple(("equal_vgs", "dc", m, "derived", (g, s)) for _k, g, s, m in self.gs_groups)
        self.vds_eq_vgs = tuple(("vds_eq_vgs", "dc", (n,), "derived", (self.mos[n]["drain"], self.mos[n]["source"]))
                                for n in self.diodes)
        self.kcl_group = tuple(("kcl_group", "dc", tuple(els for _n, els in segs), "derived", ends, ("J13-a",))
                               for _bid, ends, segs, _src in self.branches if len(segs) >= 2)
        mirrors = [(g, s, m) for _k, g, s, m in self.gs_groups if g not in self.rails]
        self.matching_ratio = tuple(("matching_ratio", "dc", m, "derived", (g, s)) for g, s, m in mirrors)
        self.l_class = tuple(("l_class", "geom", m, "proposed", ("J-U4-a",)) for _g, _s, m in mirrors)
        by_ks = defaultdict(list)
        for n, e in self.mos.items():
            if e["source"] not in self.rails:
                by_ks[(e["kind"], e["source"])].append(n)
        off = []
        for (_kind, s), members in sorted(by_ks.items()):
            gates = sorted({self.mos[m]["gate"] for m in members})
            if len(gates) >= 2:
                members = tuple(sorted(members))
                off.append(("matching_offset", "dc_to_ss", members,
                            "derived" if len(members) == 2 else "review_needed", (s,) + tuple(gates), ("J-U4-b",)))
        self.matching_offset = tuple(off)

    def _node(self, net):
        return F if net in self.rails else net

    def _gvgs(self):
        fixed = []
        rep = {}               # frozenset(끝점) -> 대표 소자(이름순 첫)
        for n in sorted(self.mos):
            e = self.mos[n]
            g, s = self._node(e["gate"]), self._node(e["source"])
            if g == F and s == F:
                fixed.append(n)
                continue
            if g == s:
                raise StopExpected("gvgs_self_edge", (n,), nets=(e["gate"],))
            rep.setdefault(frozenset((g, s)), n)
        self.fixed_vgs = tuple(fixed)
        self.gs_edges = {n: tuple(k) for k, n in rep.items()}           # 대표 소자 -> 끝점 2개
        E = list(rep)
        P = set(self.input_ports)

        def c(edge_keys):
            return _cyclomatic(tuple(k) for k in edge_keys)

        def minus(nodes):
            return [k for k in E if not (k & nodes)]

        self.cyclomatic = c(E)
        self.v2_port0 = c(minus(P))
        self.v2_port1 = sum(c(minus(P - {p})) - self.v2_port0 for p in sorted(P))
        self.v1 = self.cyclomatic - self.v2_port0 - self.v2_port1
        self.non_bridge = frozenset(rep[k] for k in E if c([x for x in E if x != k]) == self.cyclomatic - 1)
        # 성분·최단 거리(VDS-1)
        adj = defaultdict(set)
        for k in E:
            a, b = tuple(k)
            adj[a].add(b)
            adj[b].add(a)
        self.gs_adj = adj

        def dist(a, b):
            if a not in adj or b not in adj:
                return None
            seen = {a: 0}
            frontier = [a]
            while frontier:
                nxt = []
                for x in frontier:
                    for y in adj[x]:
                        if y not in seen:
                            seen[y] = seen[x] + 1
                            nxt.append(y)
                frontier = nxt
            return seen.get(b)

        self.gs_dist = dist
        vds = {}
        for n, e in self.mos.items():
            if n in self.diodes:
                continue
            d, s = self._node(e["drain"]), self._node(e["source"])
            if d == s:
                continue
            k = dist(d, s)
            if k is not None:
                vds[n] = k
        self.vds1 = vds          # 소자 -> Gs 최단 경로 엣지 수
