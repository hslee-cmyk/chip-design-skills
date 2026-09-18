# -*- coding: utf-8 -*-
"""fresh3 part 2: rule 9, DEC-63, K8, rule 2 loops (0-1 BFS), DEC-64 G_vgs, DEC-71 columns, DEC-60 GB0.
Appends one JSON line per (variant, circuit) to results2_<tag>.jsonl."""
import json, os, sys, itertools, collections, random
import networkx as nx
import engine as E

SP = E.SP


def blocks_merged(ctx):
    blk = ctx["blk"]; segs = blk["segs"]; uf = blk["uf"]
    B = collections.defaultdict(lambda: dict(members=set(), ins=set(), outs=set(), nodes=set(), segs=[]))
    for s, sg in segs.items():
        r = uf[s]
        B[r]["members"] |= set(sg["members"]); B[r]["ins"] |= set(sg["ins"]); B[r]["outs"] |= set(sg["outs"])
        B[r]["nodes"] |= set(sg["nodes"]); B[r]["segs"].append(s)
    dev = {m["name"]: m for m in ctx["c"]["devs"]}
    for r, b in B.items():
        # outs: an out that is also an input of the same block is internal
        b["outs"] = {o for o in b["outs"]}
        for mn in b["members"]:
            m = dev[mn]
            for t in (m["d"], m["s"], m["g"]):
                if t in ctx["R"] and t not in ctx["acg"]: b["nodes"].add(t)
    return dict(B)


def impedance(ctx, n):
    c, acg = ctx["c"], ctx["acg"]
    low = [m["name"] for m in c["devs"] if (m["s"] == n and m["g"] in acg) or (m["g"] == m["d"] == n)]
    if low: return "low", low
    if any(n in (p["a"], p["b"]) and p["kind"] == "R" for p in c["pas"]): return "value_dep", []
    return "high", []


def rule9(ctx, B, opt):
    c, cell, F, kind = ctx["c"], ctx["cell"], ctx["F"], ctx["kind"]
    a = list(ctx["blk"]["rule9a"])
    a_fwd = [x for x in a if cell[x]["out"] in F]
    bports = [x for x in c["ports"].values() if x.get("kind") == "current" or x.get("signal") == "current"]
    cc = []
    for r, b in B.items():
        starters = [s for s in b["segs"] if cell[s]["type"] in ("CS", "CSCD_review")]
        if not starters: continue
        for o in b["outs"]:
            if o not in F: continue
            g, why = impedance(ctx, o)
            if g == "low": cc.append(dict(block=r, out=o, low_terms=why))
    # alternative reading (layer error): every forward CS drain as output-node candidate, no block
    cc_alt = []
    for m in c["devs"]:
        if cell[m["name"]]["type"] == "CS" and m["d"] in F:
            g, why = impedance(ctx, m["d"])
            if g == "low":
                # diode-mirror exception
                readers = [u for u in c["devs"] if u["g"] == m["d"] and u["g"] != u["d"] and cell[u["name"]].get("out") in F]
                if any(u["g"] == u["d"] for u in c["devs"] if u["d"] == m["d"]) and readers: continue
                cc_alt.append((m["name"], m["d"], why))
    return dict(a=a, a_forward=a_fwd, b=len(bports), c=cc, c_alt_noblock=cc_alt)


def dec63(ctx, B):
    c, cell, kind, F = ctx["c"], ctx["cell"], ctx["kind"], ctx["F"]
    us = set(x for x in ctx["excite"]) | {o for b in B.values() for o in b["outs"]}
    us = {u for u in us if kind.get(u) == "V" or u in ctx["excite"]}
    out = []
    cds = [m for m in c["devs"] if cell[m["name"]]["type"] == "CD"]
    for u in sorted(us):
        Rset = set(); fr = [u]
        while fr:
            x = fr.pop()
            for m in cds:
                if m["g"] == x and m["s"] not in Rset:
                    Rset.add(m["s"]); fr.append(m["s"])
        if not Rset: continue
        term = [n for n in Rset if not any(m["g"] == n for m in cds)]
        out.append(dict(u=u, R=sorted(Rset), terminal=sorted(term), kind="buffer" if len(term) == 1 else "multi_output_record_only"))
    return out


def k8(ctx, B, opt):
    c, cell, role = ctx["c"], ctx["cell"], ctx["role"]
    gain_outs = {o for b in B.values() for o in b["outs"]}
    cds = [m for m in c["devs"] if cell[m["name"]]["type"] == "CD"]
    hits = []
    for m in c["devs"]:
        r = role[m["name"]]
        rb = (r == "bias") or (r == "unresolved" and opt.get("k8_unresolved_as_bias"))
        if not rb or cell[m["name"]]["type"] not in ("CS", "CSCD_review"): continue
        k = m["d"]
        for cd in cds:
            if cd["s"] != k: continue
            # gate of m reachable from cd input via CD edges?
            seen = {cd["g"]}; fr = [cd["g"]]
            while fr:
                x = fr.pop()
                for u in cds:
                    if u["g"] == x and u["s"] not in seen: seen.add(u["s"]); fr.append(u["s"])
            if m["g"] in seen: continue
            if k in gain_outs: continue
            hits.append(dict(dev=m["name"], k=k, cd=cd["name"]))
    return hits


# ----------------------------------------------------------------------------- rule 2
def loop_graph(ctx, include_ports=False):
    c, cell, acg, R = ctx["c"], ctx["cell"], ctx["acg"], ctx["R"]
    excite = set(ctx["excite"])
    nets = E.all_nets(c)
    nodes = {n for n in nets if n not in acg and (include_ports or n not in excite)}
    cur_entry = {m["d"] for m in c["devs"] if cell[m["name"]]["type"] in ("CS", "CG", "CSCD_review")}
    bundle_of = {}
    for b in ctx["bundles"]:
        bundle_of[b[0]] = b; bundle_of[b[1]] = b
    G = nx.MultiDiGraph(); G.add_nodes_from(nodes)
    for m in c["devs"]:
        n = m["name"]
        if m["g"] != m["d"] and m["g"] in nodes and m["d"] in nodes: G.add_edge(m["g"], m["d"], lab=("gd", n))
        if m["g"] != m["s"] and m["g"] in nodes and m["s"] in nodes: G.add_edge(m["g"], m["s"], lab=("gs", n))
        if n in bundle_of: continue
        if m["s"] in nodes and m["d"] in nodes and m["s"] in cur_entry:
            G.add_edge(m["s"], m["d"], lab=("sd", n))
    for b in ctx["bundles"]:
        x, y = b[2]
        if x in nodes and y in nodes:
            G.add_edge(x, y, lab=("B", b[0] + "/" + b[1])); G.add_edge(y, x, lab=("B", b[0] + "/" + b[1]))
    for p in c["pas"]:
        if p["a"] in nodes and p["b"] in nodes:
            G.add_edge(p["a"], p["b"], lab=("P" + p["kind"], p["name"])); G.add_edge(p["b"], p["a"], lab=("P" + p["kind"], p["name"]))
    return G


def bfs01(ctx, Gl, pcost, opt):
    c, cell, kind = ctx["c"], ctx["cell"], ctx["kind"]
    excite = [e for e in ctx["excite"] if e not in ctx["acg"]]
    if opt.get("bfs_mode", "rule4") == "rule4":
        G = nx.MultiDiGraph(); G.add_nodes_from(Gl.nodes)
        for u, v, d in Gl.edges(data=True):
            if d["lab"][0] in ("gd", "gs", "B") or d["lab"][0].startswith("P"): G.add_edge(u, v, lab=d["lab"])
    else:
        G = nx.MultiDiGraph(Gl)
    # add ports and their outgoing edges, plus CG s->d for all CG cells
    for m in c["devs"]:
        n = m["name"]
        for p in excite:
            if m["g"] == p:
                for t in (m["d"], m["s"]):
                    if t in G and t != p: G.add_edge(p, t, lab=("gd" if t == m["d"] else "gs", n))
        if cell[n]["type"] == "CG" and m["d"] in set(G.nodes) | set(excite) and (m["s"] in G or m["s"] in excite):
            if not G.has_edge(m["s"], m["d"]) or all(d["lab"] != ("sd", n) for d in G.get_edge_data(m["s"], m["d"]).values()):
                G.add_edge(m["s"], m["d"], lab=("sd", n))
    for pz in (c["pas"] if opt.get("bfs_port_passive", True) else []):
        for p in excite:
            for x, y in ((pz["a"], pz["b"]), (pz["b"], pz["a"])):
                if x == p and y in G: G.add_edge(p, y, lab=("P" + pz["kind"], pz["name"]))
    diode_nodes = {m["d"] for m in c["devs"] if m["g"] == m["d"]}
    dev = {m["name"]: m for m in c["devs"]}
    def cost(u, v, lab):
        t, n = lab
        if t == "gd": return 0 if u in diode_nodes else 1
        if t == "gs": return 0
        if t == "sd":
            return 1 if (cell[n]["type"] == "CG" and kind.get(dev[n]["s"]) == "V") else 0
        if t.startswith("P"): return pcost
        return 0
    import collections as C
    dist = {p: 0 for p in excite}
    dq = C.deque(excite)
    while dq:
        u = dq.popleft()
        for _, v, d in G.out_edges(u, data=True):
            w = cost(u, v, d["lab"])
            nd = dist[u] + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                if w == 0: dq.appendleft(v)
                else: dq.append(v)
    return dist, cost, G


def enumerate_cycles(G):
    D = nx.DiGraph(); D.add_nodes_from(G.nodes)
    for u, v in G.edges(): D.add_edge(u, v)
    node_cycles = []
    for cyc in nx.simple_cycles(D):
        # rotate to name-sorted first node
        i = cyc.index(min(cyc)); cyc = cyc[i:] + cyc[:i]
        hops = [(cyc[k], cyc[(k + 1) % len(cyc)]) for k in range(len(cyc))]
        labs = [[d["lab"] for d in G.get_edge_data(u, v).values()] for u, v in hops]
        # edge-level expansions
        exps = []
        for combo in itertools.product(*labs):
            if len(cyc) == 2 and combo[0] == combo[1] or (len(cyc) == 2 and combo[0][1] == combo[1][1] and combo[0][0][0] in "PB" and combo[1][0][0] in "PB"):
                continue
            exps.append(combo)
        if not exps: continue
        node_cycles.append(dict(nodes=cyc, hops=hops, exps=exps))
    return node_cycles


def classify_cycle(ctx, cyc, combo, dist, B, opt):
    c, cell, R, F = ctx["c"], ctx["cell"], ctx["R"], ctx["F"]
    nodes, hops = cyc["nodes"], cyc["hops"]
    tags = []
    sig_set = F if opt.get("bias_scc_by_forward") else R
    if not any(n in sig_set for n in nodes):
        return ["1.5"], {}
    L = len(hops)
    passive = [combo[k][0].startswith("P") for k in range(L)]
    # (2) maximal passive-only runs containing a capacitor with both endpoints forward
    is2 = False
    if all(passive):
        is2 = any(combo[k][0] == "PC" for k in range(L))
    else:
        k0 = next(k for k in range(L) if not passive[k])
        k = k0 + 1
        while k < k0 + 1 + L:
            if passive[k % L]:
                j = k
                while passive[j % L]: j += 1
                run = [(k2 % L) for k2 in range(k, j)]
                a = hops[run[0]][0]; z = hops[run[-1]][1]
                if any(combo[r][0] == "PC" for r in run) and a in F and z in F: is2 = True
                k = j
            else:
                k += 1
    if is2: tags.append("2")
    # active devices used
    devs_used = sorted({combo[k][1] for k in range(L) if combo[k][0] in ("gd", "gs", "sd")})
    bund_used = sorted({combo[k][1] for k in range(L) if combo[k][0] == "B"})
    cells_ = [d for d in devs_used if cell[d]["type"] in ("CS", "CG", "CD", "CSCD_review")]
    # (3-a)
    def off(d):
        t = cell[d]
        return t.get("out") not in F
    if opt.get("r3a_any_device"):
        is3a = any(off(d) if cell[d]["type"] in ("CS", "CG", "CD", "CSCD_review") else True for d in devs_used)
    else:
        is3a = any(off(d) for d in cells_)
    # return runs: hop reverse if dist[v] <= dist[u]
    def dd(n): return dist.get(n, 10 ** 6)
    rev = [dd(hops[k][1]) <= dd(hops[k][0]) for k in range(L)]
    runs = []
    if all(rev): runs = [list(range(L))]
    elif any(rev):
        k0 = next(k for k in range(L) if not rev[k])
        k = k0 + 1
        while k < k0 + 1 + L:
            if rev[k % L]:
                j = k
                while rev[j % L]: j += 1
                runs.append([(k2 % L) for k2 in range(k, j)]); k = j
            else: k += 1
    has_passive = any(passive)
    n_active = len(devs_used) + len(bund_used)
    two_active = (not has_passive) and len(devs_used) == 2 and not bund_used
    # block orders
    border = {}
    for r, b in B.items():
        border[r] = min((dd(o) for o in b["outs"]), default=10 ** 6)
    def later_ok(a, bi, strict):
        oi = border[bi]
        cand = [border[bj] for bj in B if (border[bj] > oi if strict else border[bj] >= oi)]
        return any(dd(a) >= x for x in cand)
    is3b = {}
    for key in ("strict_in_strictorder", "strict_in_loose_order", "node_in_strictorder", "node_in_loose_order"):
        ok = False
        for run in runs:
            act = [r for r in run if combo[r][0] in ("gd", "gs", "sd", "B")]
            if not act: continue
            a = hops[run[0]][0]; z = hops[run[-1]][1]
            for bi, b in B.items():
                zin = (z in b["ins"]) if key.startswith("strict_in") else (z in b["nodes"])
                if zin and later_ok(a, bi, key.endswith("strictorder")):
                    ok = True
        is3b[key] = ok
    all_ret_passive = runs and all(all(combo[r][0].startswith("P") for r in run) for run in runs)
    info = dict(devs=devs_used, bundles=bund_used, runs=[[hops[r] for r in run] for run in runs], is3a=is3a,
                is3b=is3b, two_active=two_active, all_ret_passive=bool(all_ret_passive), has_passive=has_passive)
    return tags, info


def final_class(tags, info, key):
    if tags == ["1.5"]: return "1.5"
    out = []
    if "2" in tags: out.append("2")
    if info["two_active"]:
        return "+".join(out + ["nah_2active"]) if out else "nah_2active"
    if info["is3a"]:
        out.append("3a")
    elif info["is3b"][key] and not info["all_ret_passive"]:
        out.append("3b")
    if not out: out.append("4")
    return "+".join(out)


def breakpoints(ctx, cyc, combo, info):
    cell = ctx["cell"]
    L = len(cyc["hops"])
    cand = []
    for k in range(L):
        t, n = combo[k]
        if t in ("gd", "gs") and cell[n]["type"] in ("CS", "CSCD_review"):
            cand.append((k, n, cyc["hops"][k][0]))
    return cand


# ----------------------------------------------------------------------------- DEC-64 G_vgs
def gvgs(c, trees=("bfs", "dfs", "rand1", "rand2", "rand3")):
    rails = set(c["rails"])
    ins = set(c["ins"])
    def mp(n): return "RAIL" if n in rails else n
    G = nx.MultiGraph()
    for m in c["devs"]:
        G.add_edge(mp(m["g"]), mp(m["s"]), key=m["name"], g=m["g"], s=m["s"])
    E_ = G.number_of_edges(); V = G.number_of_nodes(); Cc = nx.number_connected_components(G)
    nbasis = E_ - V + Cc
    res = {"n_basis": nbasis, "selfloops": [k for u, v, k in G.edges(keys=True) if u == v]}
    for tr in trees:
        # spanning forest
        H = nx.Graph(); H.add_nodes_from(G.nodes)
        order = sorted(G.nodes)
        if tr.startswith("rand"):
            rng = random.Random(int(tr[-1])); order = order[:]; rng.shuffle(order)
        tree_edges = set(); seen = set()
        for root in (["RAIL"] if "RAIL" in G else []) + order:
            if root in seen: continue
            seen.add(root); fr = [root]
            while fr:
                u = fr.pop(0) if tr in ("bfs",) or tr.startswith("rand") else fr.pop()
                nbrs = sorted({(v, k) for _, v, k in G.edges(u, keys=True)})
                if tr.startswith("rand"): rng.shuffle(nbrs)
                for v, k in nbrs:
                    if v not in seen:
                        seen.add(v); tree_edges.add(k); H.add_edge(u, v, key=k); fr.append(v)
        cls = collections.Counter(); detail = []
        for u, v, k, d in G.edges(keys=True, data=True):
            if k in tree_edges: continue
            if u == v:
                path = [u]; pedges = []
            else:
                path = nx.shortest_path(H, u, v); pedges = [H[path[i]][path[i + 1]]["key"] for i in range(len(path) - 1)]
            members = [k] + pedges
            dev = {m["name"]: m for m in c["devs"]}
            if len(members) == 2 and (dev[members[0]]["g"], dev[members[0]]["s"]) == (dev[members[1]]["g"], dev[members[1]]["s"]):
                typ = "v0"
            else:
                nets_on = set(path)
                if len(nets_on & ins) >= 2: typ = "v1"
                else: typ = "v2_rail" if "RAIL" in nets_on else "v2"
            cls[typ] += 1; detail.append((typ, sorted(members)))
        res[tr] = dict(counts=dict(cls), v1v2=[d for d in detail if d[0] != "v0"])
    return res


# ----------------------------------------------------------------------------- DEC-71 columns
def dc_graph(c, prune=True):
    rails = set(c["rails"]); ports = set(c["ports"])
    G = nx.MultiGraph()
    for m in c["devs"]:
        if m["d"] != m["s"]: G.add_edge(m["d"], m["s"], key=m["name"], t="M")
    for p in c["pas"]:
        if p["kind"] == "R": G.add_edge(p["a"], p["b"], key=p["name"], t="R")
    for s in c["isrc"] + c["vsrc"]:
        G.add_edge(s["a"], s["b"], key=s["name"], t="I")
    pruned = []
    if prune:
        ch = True
        while ch:
            ch = False
            for n in list(G.nodes):
                if n in rails or n in ports: continue
                if G.degree(n) == 1:
                    (u, v, k, d), = list(G.edges(n, keys=True, data=True))
                    if d["t"] == "R":
                        G.remove_edge(u, v, key=k); G.remove_node(n); pruned.append(k); ch = True
                elif G.degree(n) == 0:
                    G.remove_node(n)
    return G, pruned


def columns(c, max_paths=200000):
    rails = [r for r in c["rails"]]
    G, pruned = dc_graph(c, True)
    bnodes = sorted(n for n in G.nodes if n not in rails and G.degree(n) >= 3)
    # branches: maximal chains between endpoints (rail / branch node / degree!=2 node)
    endp = set(rails) | set(bnodes) | {n for n in G.nodes if G.degree(n) != 2}
    used = set(); branches = []
    for u, v, k in G.edges(keys=True):
        if k in used: continue
        # grow chain both directions
        chain = [k]; used.add(k); ends = []
        for start, nxt in ((u, v), (v, u)):
            cur, prev_k = nxt, k
            path_nodes = []
            while cur not in endp:
                es = [(a, b, kk) for a, b, kk in G.edges(cur, keys=True) if kk != prev_k]
                if len(es) != 1: break
                a, b, kk = es[0]
                if kk in used: break
                used.add(kk); chain.append(kk); prev_k = kk
                cur = b if a == cur else a
            ends.append(cur)
        branches.append(dict(devs=sorted(chain), ends=sorted(ends)))
    # columns: node-simple paths rail->rail through non-rail nodes
    res = {}
    rail_set = set(r for r in rails if r in G)
    D = nx.Graph()
    for u, v in G.edges(): D.add_edge(u, v)
    col_dev_sets = []
    for ra, rb in itertools.combinations(sorted(rail_set), 2):
        H = D.subgraph([n for n in D.nodes if n not in rail_set or n in (ra, rb)])
        cnt_nodes = 0; cnt_edges = 0
        if ra in H and rb in H:
            for p in nx.all_simple_paths(H, ra, rb):
                if any(x in rail_set for x in p[1:-1]): continue
                cnt_nodes += 1
                mult = 1; devset = []
                for i in range(len(p) - 1):
                    ks = list(G.get_edge_data(p[i], p[i + 1]).keys())
                    mult *= len(ks); devset.append(ks)
                cnt_edges += mult
                col_dev_sets.append(set(itertools.chain.from_iterable(devset)))
                if cnt_nodes > max_paths: break
        res[f"{ra}-{rb}"] = dict(node_simple=cnt_nodes, edge_expanded=cnt_edges)
    covered = set().union(*col_dev_sets) if col_dev_sets else set()
    uncovered_branches = [b for b in branches if not (set(b["devs"]) & covered)]
    return dict(branch_nodes=bnodes, n_branch_nodes=len(bnodes), branches=branches, n_branches=len(branches),
                pruned=pruned, columns=res, covered=covered, uncovered_branches=uncovered_branches,
                col_dev_sets=col_dev_sets)


def hidden_rails(c, supply_override=None):
    rails = set(supply_override if supply_override is not None else c["rails"])
    G, _ = dc_graph(c, prune=False)
    mos_nets = {m[x] for m in c["devs"] for x in ("d", "g", "s")}
    other = {p[x] for p in c["pas"] + c["isrc"] + c["vsrc"] for x in ("a", "b")}
    cand = []
    for n in sorted(other - mos_nets):
        if n in rails: continue
        conn = False
        if n in G:
            comp = nx.node_connected_component(G, n)
            conn = bool(comp & rails)
        if not conn: cand.append(n)
    return cand


# ----------------------------------------------------------------------------- driver
def analyse(c, opt):
    r1, ctx = E.run(c, opt)
    out = dict(circuit=c["name"], opt=opt)
    B = blocks_merged(ctx)
    out["blocks_merged"] = {k: dict(members=sorted(v["members"]), ins=sorted(v["ins"]), outs=sorted(v["outs"]), nodes=sorted(v["nodes"])) for k, v in B.items()}
    # block node-set overlap (rule 6 exclusivity)
    ov = []
    ks = list(B)
    for a, b in itertools.combinations(ks, 2):
        inter = (B[a]["nodes"] & B[b]["nodes"]) - (B[a]["outs"] & B[b]["ins"]) - (B[b]["outs"] & B[a]["ins"])
        if inter: ov.append((a, b, sorted(inter)))
    out["block_overlap"] = ov
    out["rule9"] = rule9(ctx, B, opt)
    out["dec63"] = dec63(ctx, B)
    out["k8"] = k8(ctx, B, opt)
    # residual merges -> (a) composite or multi-input
    res_m = [m for m in r1["merges"] if m["kind"] == "residual"]
    out["residual_merges"] = []
    for m in res_m:
        o = m["node"]; k = ctx["kind"].get(o)
        a_lit = k == "I" or True  # merge node is a block output by construction
        out["residual_merges"].append(dict(node=o, drive=k, segs=m["segs"], comps=m.get("comps")))
    Gl = loop_graph(ctx)
    pc = opt.get("pcost", 0)
    dist, cost, Gb = bfs01(ctx, Gl, pc, opt)
    out["dist"] = dist
    cycles = enumerate_cycles(Gl)
    key = opt.get("r3b_key", "node_in_loose_order")
    agg = collections.Counter(); agg_edge = collections.Counter(); lst = []
    bp_zero = []
    for cy in cycles:
        klass_set = []
        for combo in cy["exps"]:
            tags, info = classify_cycle(ctx, cy, combo, dist, B, opt)
            fc = final_class(tags, info, key) if tags != ["1.5"] else "1.5"
            klass_set.append(fc)
            agg_edge[fc] += 1
            if "3a" in fc or "3b" in fc:
                bp = breakpoints(ctx, cy, combo, info)
                if not bp: bp_zero.append((cy["nodes"], combo))
        # node-cycle class = the set (if expansions disagree, report)
        k = "|".join(sorted(set(klass_set)))
        agg[k] += 1
        lst.append(dict(nodes=cy["nodes"], klass=k, n_exp=len(cy["exps"]),
                        info={kk: vv for kk, vv in (classify_cycle(ctx, cy, cy["exps"][0], dist, B, opt)[1] or {}).items() if kk in ("devs", "is3b", "two_active", "is3a")}))
    out["n_cycles_node"] = len(cycles); out["n_cycles_edge"] = sum(len(x["exps"]) for x in cycles)
    out["cycle_class_node"] = dict(agg); out["cycle_class_edge"] = dict(agg_edge)
    out["cycles"] = lst; out["bp_zero"] = [str(x) for x in bp_zero]
    # old definition: include 2-terminal passive round trips
    D = nx.DiGraph(); D.add_edges_from((u, v) for u, v in Gl.edges()); D.add_nodes_from(Gl.nodes)
    out["n_cycles_incl_roundtrip"] = sum(1 for _ in nx.simple_cycles(D))
    return out, r1, ctx, B


if __name__ == "__main__":
    tag = sys.argv[1]; opt = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    fn = os.path.join(SP, f"results2_{tag}.jsonl"); open(fn, "w").close()
    for c in E.circuits():
        o, r1, ctx, B = analyse(c, opt)
        with open(fn, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(part1=r1, part2=o), ensure_ascii=False, default=str) + "\n")
        print(c["name"], o["n_cycles_node"], o["cycle_class_node"])
