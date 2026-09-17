# -*- coding: utf-8 -*-
"""review9 사고실험용 순수 구조 측정기.

계획서 v5.17의 GB0~GB6 규칙 중 **topology.json connectivity만으로 셀 수 있는 것**만 센다.
사이징·LUT·탐색은 하지 않는다. 결과는 케이스마다 out.jsonl / out.txt 에 append (WP-11).
"""
import json, os, sys, glob, itertools
sys.setrecursionlimit(20000)
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.dirname(os.path.abspath(__file__))
JSONL = os.path.join(OUT, "measure_results.jsonl")
TXT = os.path.join(OUT, "measure_results.txt")

RAIL_NAMESET = {"vdd", "gnd", "vss", "vcc", "vee"}  # 전환기 이름집합 해석(DEC-60, 소문자 비교)
SIZING_SPEC_CIRCUITS = {"two_stage_ota", "current_reuse_telescopic_ota",
                        "folded_cascode", "nmcnr_amplifier"}  # run_harness.SPECS 실측


def load(name):
    with open(os.path.join(LIB, name + ".topology.json"), encoding="utf-8") as f:
        return json.load(f)


def devices(d):
    return [x for x in (d.get("netlist") or []) if isinstance(x, dict) and x.get("name")]


def passives(d):
    return [x for x in (d.get("passive_elements") or []) if isinstance(x, dict)]


def isources(d):
    return [x for x in (d.get("ideal_sources") or []) if isinstance(x, dict)]


def all_nets(d):
    s = set()
    for m in devices(d):
        for k in ("source", "drain", "gate", "bulk"):
            if m.get(k):
                s.add(m[k])
    for p in passives(d):
        for t in (p.get("terminals") or []):
            s.add(t)
    for q in isources(d):
        for t in (q.get("terminals") or []):
            s.add(t)
        for k in ("from", "to", "plus", "minus", "net_from", "net_to"):
            if q.get(k):
                s.add(q[k])
    return s


def ports_of(d):
    p = d.get("ports")
    if not isinstance(p, dict):
        return {}
    return {k: v for k, v in p.items() if not k.startswith("_") and isinstance(v, dict)}


def rails_of(d):
    """(rails, source) -- 선언이 있으면 선언, 없으면 전환기 이름집합 해석."""
    sn = d.get("supply_nets")
    if sn:
        return set(sn), "declared"
    nets = all_nets(d)
    return {n for n in nets if n.lower() in RAIL_NAMESET}, "nameset"


def isrc_terminals(q):
    ts = q.get("terminals")
    if isinstance(ts, list) and len(ts) >= 2:
        return ts[0], ts[1]
    for a, b in (("from", "to"), ("plus", "minus"), ("net_from", "net_to"),
                 ("source_net", "drain_net"), ("net_p", "net_n")):
        if q.get(a) and q.get(b):
            return q[a], q[b]
    return None


# ---------------------------------------------------------------- DC 전도 그래프
def dc_edges(d, rails, ports):
    """DEC-70/DEC-71: MOS 채널(d-s), 저항, 이상원. 게이트·커패시터 제외.
    잎 가지치기: 레일·포트가 아닌 노드 중 DC 엣지가 저항 하나뿐이면 반복 제거."""
    edges = []  # (u, v, kind, name)
    for m in devices(d):
        edges.append((m["source"], m["drain"], "mos", m["name"]))
    for p in passives(d):
        if (p.get("kind") or "").lower().startswith("res"):
            t = p.get("terminals") or []
            if len(t) >= 2:
                edges.append((t[0], t[1], "res", p.get("name")))
    for q in isources(d):
        t = isrc_terminals(q)
        if t:
            edges.append((t[0], t[1], "isrc", q.get("name")))
    keep = list(range(len(edges)))
    changed = True
    while changed:
        changed = False
        deg = defaultdict(list)
        for i in keep:
            u, v, k, n = edges[i]
            deg[u].append(i)
            deg[v].append(i)
        for node, ids in list(deg.items()):
            if node in rails or node in ports:
                continue
            if len(ids) == 1 and edges[ids[0]][2] == "res":
                keep.remove(ids[0])
                changed = True
                break
    return [edges[i] for i in keep]


def branches_and_columns(d, rails, ports):
    E = dc_edges(d, rails, ports)
    deg = defaultdict(int)
    adj = defaultdict(list)
    for i, (u, v, k, n) in enumerate(E):
        deg[u] += 1
        deg[v] += 1
        adj[u].append((v, i))
        adj[v].append((u, i))
    branch_nodes = sorted([n for n, c in deg.items() if c >= 3])
    terminals = set(branch_nodes) | set(rails)
    # 가지: terminal 노드에서 출발해 차수 2 노드를 지나 다음 terminal 까지
    used = set()
    branches = []  # dict(ends=(a,b), edges=[i], devs=[names])
    for t in sorted(terminals):
        for (nb, ei) in adj[t]:
            if ei in used:
                continue
            path = [ei]
            used.add(ei)
            prev, cur = t, nb
            while cur not in terminals:
                nxt = [(x, j) for (x, j) in adj[cur] if j not in used]
                if len(nxt) != 1:
                    break
                x, j = nxt[0]
                used.add(j)
                path.append(j)
                prev, cur = cur, x
            branches.append({"ends": tuple(sorted([t, cur])),
                             "edges": path,
                             "elems": [E[i][3] for i in path],
                             "kinds": [E[i][2] for i in path]})
    # 고립 루프(terminal 없는 사이클) 잔여 엣지
    leftovers = [i for i in range(len(E)) if i not in used]
    # 기둥: 레일 쌍마다 가지 그래프 위 단순 경로
    badj = defaultdict(list)
    for bi, b in enumerate(branches):
        a, c = b["ends"]
        badj[a].append((c, bi))
        if a != c:
            badj[c].append((a, bi))
    rails_l = sorted(rails)
    columns = []
    for r1, r2 in itertools.combinations(rails_l, 2):
        stack = [(r1, [], set())]
        cnt = 0
        while stack and cnt < 200000:
            node, pathb, seen = stack.pop()
            cnt += 1
            if node == r2 and pathb:
                columns.append({"rails": (r1, r2), "branches": list(pathb)})
                continue
            for (nb, bi) in badj[node]:
                if bi in seen:
                    continue
                if nb in rails and nb != r2:
                    continue  # 레일을 중간에 지나지 않는다
                stack.append((nb, pathb + [bi], seen | {bi}))
    covered_branches = set()
    for c in columns:
        covered_branches.update(c["branches"])
    uncovered = [bi for bi in range(len(branches)) if bi not in covered_branches]
    # 소자 -> 덮는 기둥 수
    dev_cols = defaultdict(set)
    for ci, c in enumerate(columns):
        for bi in c["branches"]:
            for e in branches[bi]["elems"]:
                dev_cols[e].add(ci)
    mos_names = [m["name"] for m in devices(d)]
    uncovered_mos = [m for m in mos_names if not dev_cols.get(m)]
    return {
        "dc_edges": len(E),
        "branch_nodes": branch_nodes,
        "n_branch_nodes": len(branch_nodes),
        "n_branches": len(branches),
        "branches": [{"ends": list(b["ends"]), "elems": b["elems"]} for b in branches],
        "n_columns": len(columns),
        "columns": [{"rails": list(c["rails"]), "elems":
                     [e for bi in c["branches"] for e in branches[bi]["elems"]]} for c in columns],
        "uncovered_branches": [branches[bi]["elems"] for bi in uncovered],
        "leftover_cycle_edges": [E[i][3] for i in leftovers],
        "mos_not_in_any_column": uncovered_mos,
    }


# ---------------------------------------------------------------- AC 구조
def ac_ground(d, rails):
    """레일 + gate에만 붙고 구동되지 않는 넷 + 이상 전압원 단자."""
    driven = set()
    for m in devices(d):
        driven.add(m["source"])
        driven.add(m["drain"])
    passive_nets = set()
    for p in passives(d):
        for t in (p.get("terminals") or []):
            passive_nets.add(t)
    isrc_nets = set()
    for q in isources(d):
        t = isrc_terminals(q)
        if t:
            isrc_nets.update(t)
    pnames = set(ports_of(d).keys())
    gate_only = set()
    for m in devices(d):
        g = m["gate"]
        if g in rails:
            continue
        if g in driven or g in passive_nets or g in isrc_nets or g in pnames:
            continue
        gate_only.add(g)
    return set(rails) | gate_only


def signal_reach(d, rails, acg, excite_nets):
    """초집합 방향 그래프(모든 g->d, g->s, s->d, d->s? 계획은 s->d만) 도달성.
    계획 N3.2-3: '신호 경로 도달성은 source->drain 엣지를 모두 넣은 초집합 방향 그래프로
    한 번 계산' -> g->d, g->s, s->d + 수동소자 무향."""
    adj = defaultdict(set)
    for m in devices(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        adj[g].add(dr)
        adj[g].add(s)
        adj[s].add(dr)
    for p in passives(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            adj[t[0]].add(t[1])
            adj[t[1]].add(t[0])
    seen = set()
    stack = [n for n in excite_nets]
    while stack:
        n = stack.pop()
        if n in seen or n in acg:
            continue
        seen.add(n)
        for x in adj.get(n, ()):
            if x not in seen:
                stack.append(x)
    return seen


def classify_cells(d, rails, acg, excite_nets):
    reach = signal_reach(d, rails, acg, excite_nets)
    out = {}
    for m in devices(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        gate_sig = (g in reach) and (g not in acg)
        s_sig = (s in reach) and (s not in acg)
        d_sig = (dr in reach) and (dr not in acg)
        if gate_sig:
            if dr in acg:
                cell = "CD"
            elif s in acg:
                cell = "CS"
            else:
                cell = "CS_or_CD_review"  # N3.2-3 이중 출력 -> review_needed(기록만)
        else:
            if s_sig and d_sig:
                cell = "CG_or_pass"       # 방향 도달 순서/역병렬 묶음 필요
            elif s_sig or d_sig:
                cell = "load/bias"        # 신호 경로 셀 아님(부하)
            else:
                cell = "off_path"         # 뷰의 신호 경로 밖
        out[m["name"]] = cell
    return out, reach


def signal_loops(d, rails, acg, excite_nets, port_nets, cap=200000):
    """N3.2-2 루프 탐지 그래프: 교류접지 + 여기 포트 제거, 방향 엣지
    (g->d, g->s, s->d) + 수동소자 무향. 기본 폐경로(단순 사이클) 전수."""
    removed = set(acg) | set(excite_nets)
    adj = defaultdict(set)
    for m in devices(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        for (a, b) in ((g, dr), (g, s), (s, dr)):
            if a in removed or b in removed or a == b:
                continue
            adj[a].add(b)
    for p in passives(d):
        t = p.get("terminals") or []
        if len(t) >= 2 and t[0] not in removed and t[1] not in removed and t[0] != t[1]:
            adj[t[0]].add(t[1])
            adj[t[1]].add(t[0])
    allnodes = set(adj.keys())
    for v in adj.values():
        allnodes |= v
    nodes = sorted(allnodes)
    idx = {n: i for i, n in enumerate(nodes)}
    cycles = []
    budget = [cap]

    def dfs(start, node, path, onpath):
        if budget[0] <= 0:
            return
        for nxt in sorted(adj[node]):
            budget[0] -= 1
            if budget[0] <= 0:
                return
            if nxt == start and len(path) >= 2:
                cycles.append(list(path))
            elif nxt not in onpath and idx[nxt] > idx[start]:
                path.append(nxt)
                onpath.add(nxt)
                dfs(start, nxt, path, onpath)
                path.pop()
                onpath.discard(nxt)

    for s in nodes:
        dfs(s, s, [s], {s})
    return {"n_simple_cycles": len(cycles), "truncated": budget[0] <= 0,
            "sample": cycles[:8], "n_nodes": len(nodes)}


def gvgs_cycles(d, rails, ports):
    """DEC-64: MOS gate-source 무향 엣지 + 레일 병합 고정 노드. 기본 사이클 분류."""
    def canon(n):
        return "__RAIL__" if n in rails else n
    edges = [(canon(m["gate"]), canon(m["source"]), m["name"]) for m in devices(d)]
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    tree, nontree = [], []
    for (a, b, nm) in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            nontree.append((a, b, nm))
        else:
            parent[ra] = rb
            tree.append((a, b, nm))
    # 기본 사이클 = 비트리 엣지 수
    adj = defaultdict(list)
    for (a, b, nm) in tree:
        adj[a].append((b, nm))
        adj[b].append((a, nm))

    def tree_path(a, b):
        seen = {a: None}
        stack = [a]
        while stack:
            u = stack.pop()
            if u == b:
                break
            for (v, nm) in adj[u]:
                if v not in seen:
                    seen[v] = (u, nm)
                    stack.append(v)
        if b not in seen:
            return None
        path, cur = [], b
        while seen[cur] is not None:
            u, nm = seen[cur]
            path.append((cur, u, nm))
            cur = u
        return path

    in_ports = {k for k, v in ports.items()
                if "input" in (v.get("role") or "") or (v.get("direction") == "input")}
    cls = {"v0_equal_vgs": [], "v1_port_diff": [], "v2_kvl_branch": [], "unresolved": []}
    for (a, b, nm) in nontree:
        tp = tree_path(a, b)
        if tp is None:
            cls["unresolved"].append([nm])
            continue
        members = [nm] + [x[2] for x in tp]
        nodes = {a, b} | {x[0] for x in tp} | {x[1] for x in tp}
        if len(members) == 2 and a in ({x[0] for x in tp} | {x[1] for x in tp}):
            pass
        # v0: 같은 (gate, source) 평행 엣지
        parallel = any((a == x and b == y) or (a == y and b == x)
                       for (x, y, _n) in tree if True)
        touched_in_ports = nodes & in_ports
        if len(members) == 2 and parallel:
            cls["v0_equal_vgs"].append(members)
        elif len(touched_in_ports) >= 2:
            cls["v1_port_diff"].append(members)
        else:
            cls["v2_kvl_branch"].append(members)
    return {k: v for k, v in cls.items()}, len(nontree)


def vds1_cycles(d, rails):
    """DEC-64 VDS-1: G_vgs 그래프에 drain-source 엣지를 1개 추가해서 닫히는 사이클 수
    (근사: gate-source 무향 그래프 + 각 MOS의 d-s 엣지 하나를 넣어 만들어지는 기본 사이클)."""
    def canon(n):
        return "__RAIL__" if n in rails else n
    base = [(canon(m["gate"]), canon(m["source"])) for m in devices(d)]
    cnt = 0
    hits = []
    for m in devices(d):
        # union-find on base + this ds edge; ds edge closes a cycle iff its two ends already connected
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for (a, b) in base:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        a, b = canon(m["drain"]), canon(m["source"])
        if find(a) == find(b):
            cnt += 1
            hits.append(m["name"])
    return cnt, hits


def analyze(name):
    d = load(name)
    devs = devices(d)
    ports = ports_of(d)
    rails, rail_src = rails_of(d)
    nets = all_nets(d)
    in_ports = [k for k, v in ports.items()
                if "input" in (v.get("role") or "") or v.get("direction") == "input"]
    out_ports = [k for k, v in ports.items()
                 if "output" in (v.get("role") or "") or v.get("direction") == "output"]
    kinds = sorted({(m.get("kind") or "?").lower() for m in devs})

    rec = {
        "circuit": name,
        "n_devices": len(devs),
        "kinds": kinds,
        "n_passive": len(passives(d)),
        "n_ideal_sources": len(isources(d)),
        "n_nets": len(nets),
        "supply_nets_declared": bool(d.get("supply_nets")),
        "rails": sorted(rails),
        "rail_source": rail_src,
        "n_rails": len(rails),
        "ports_declared": bool(ports),
        "in_ports": in_ports,
        "out_ports": out_ports,
        "default_transfer_view_possible": bool(in_ports and out_ports),
        "sizing_spec_declared": name in SIZING_SPEC_CIRCUITS,
        "compensation": ("null" if d.get("compensation") is None else "set"),
        "compensation_status": d.get("_compensation_status"),
        "passive_area_declared": any(("area" in k) for p in passives(d) for k in p.keys()),
        "objective_declared": bool((d.get("sizing_roles") or {}).get("objective")
                                   if isinstance(d.get("sizing_roles"), dict) else False),
    }

    # GB0 로드 게이트 판정
    if rec["supply_nets_declared"]:
        rec["gb0_gate"] = "pass(declared)"
    else:
        if len(rails) == 2:
            rec["gb0_gate"] = "pass(nameset, MG1까지 한시)"
        else:
            rec["gb0_gate"] = f"REJECT(nameset 레일 {len(rails)}개 != 2)"

    # 기둥 유도
    try:
        rec["columns"] = branches_and_columns(d, rails, set(ports.keys()))
    except Exception as e:
        rec["columns"] = {"error": repr(e)}

    # AC 구조(기본 전달 뷰)
    acg = ac_ground(d, rails)
    rec["ac_ground"] = sorted(acg)
    if rec["default_transfer_view_possible"]:
        cells, reach = classify_cells(d, rails, acg, in_ports)
        tally = defaultdict(int)
        for v in cells.values():
            tally[v] += 1
        rec["cells"] = cells
        rec["cell_tally"] = dict(sorted(tally.items()))
        rec["cells_undefined"] = sorted([k for k, v in cells.items()
                                         if v in ("CS_or_CD_review", "CG_or_pass", "off_path")])
        rec["loops"] = signal_loops(d, rails, acg, in_ports, set(ports.keys()))
    else:
        rec["cells"] = None
        rec["cell_tally"] = None
        rec["cells_undefined"] = None
        rec["loops"] = None
        rec["ac_blocked_reason"] = "ports 미선언 또는 출력 포트 미선언 -> 기본 전달 뷰 불가(U-08)"

    gv, nnt = gvgs_cycles(d, rails, ports)
    rec["gvgs"] = {k: len(v) for k, v in gv.items()}
    rec["gvgs_detail"] = gv
    rec["gvgs_n_fundamental"] = nnt
    v1n, v1h = vds1_cycles(d, rails)
    rec["vds1_count"] = v1n
    rec["vds1_devices"] = v1h
    return rec


def main():
    if os.path.exists(JSONL):
        os.remove(JSONL)
    if os.path.exists(TXT):
        os.remove(TXT)
    names = ["current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier",
             "two_stage_ota", "two_stage_ota_sf", "pushpull_follower_buffer",
             "sf_pushpull_output_opamp", "ngcc_3stage_ff"]
    for n in names:
        try:
            rec = analyze(n)
        except Exception as e:
            import traceback
            rec = {"circuit": n, "error": repr(e), "tb": traceback.format_exc()}
        with open(JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        with open(TXT, "a", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"[{rec.get('circuit')}]\n")
            for k, v in rec.items():
                if k in ("cells", "gvgs_detail", "columns"):
                    continue
                f.write(f"  {k}: {json.dumps(v, ensure_ascii=False)}\n")
            c = rec.get("columns") or {}
            if isinstance(c, dict) and "n_columns" in c:
                f.write(f"  columns.n_branches={c['n_branches']} n_branch_nodes={c['n_branch_nodes']} "
                        f"n_columns={c['n_columns']} dc_edges={c['dc_edges']}\n")
                f.write(f"  columns.branch_nodes={c['branch_nodes']}\n")
                f.write(f"  columns.uncovered_branches={json.dumps(c['uncovered_branches'], ensure_ascii=False)}\n")
                f.write(f"  columns.mos_not_in_any_column={c['mos_not_in_any_column']}\n")
                f.write(f"  columns.leftover_cycle_edges={c['leftover_cycle_edges']}\n")
            if rec.get("cells"):
                f.write(f"  cells: {json.dumps(rec['cells'], ensure_ascii=False)}\n")
            if rec.get("gvgs_detail"):
                f.write(f"  gvgs_detail: {json.dumps(rec['gvgs_detail'], ensure_ascii=False)}\n")
        print("done", n)


if __name__ == "__main__":
    main()
