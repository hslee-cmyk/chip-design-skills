# -*- coding: utf-8 -*-
"""review9 2차 측정: 계획 N3.2-3/-5 셀 분류, 구동 종류, N3.2-2 루프 분류, 기둥(노드-단순).

측정 순서는 계획서가 정한 순서 그대로:
  (1) 교류접지 집합(N3.2-1) -> (2) 초집합 방향 그래프 도달성(N3.2-3)
  -> (3) 셀 분류(CS/CG/CD/pass, 이중출력 review) -> (4) 노드 구동 종류(용어집)
  -> (5) 루프 탐지 그래프(s->d는 source 노드가 전류 구동일 때만) -> (6) 폐경로 분류(0)~(4)
결과는 케이스마다 append (WP-11).
"""
import json, os, sys, itertools
sys.setrecursionlimit(50000)
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.dirname(os.path.abspath(__file__))
JSONL = os.path.join(OUT, "measure2_results.jsonl")

RAIL_NAMESET = {"vdd", "gnd", "vss", "vcc", "vee"}


def load(n):
    with open(os.path.join(LIB, n + ".topology.json"), encoding="utf-8") as f:
        return json.load(f)


def devs(d):
    return [x for x in (d.get("netlist") or []) if isinstance(x, dict) and x.get("name")]


def pas(d):
    return [x for x in (d.get("passive_elements") or []) if isinstance(x, dict)]


def isrc(d):
    return [x for x in (d.get("ideal_sources") or []) if isinstance(x, dict)]


def ports_of(d):
    p = d.get("ports")
    if not isinstance(p, dict):
        return {}
    return {k: v for k, v in p.items() if not k.startswith("_") and isinstance(v, dict)}


def isrc_t(q):
    t = q.get("terminals")
    if isinstance(t, list) and len(t) >= 2:
        return t[0], t[1]
    for a, b in (("from", "to"), ("plus", "minus"), ("net_from", "net_to")):
        if q.get(a) and q.get(b):
            return q[a], q[b]
    return None


def all_nets(d):
    s = set()
    for m in devs(d):
        for k in ("source", "drain", "gate"):
            if m.get(k):
                s.add(m[k])
    for p in pas(d):
        s.update(p.get("terminals") or [])
    for q in isrc(d):
        t = isrc_t(q)
        if t:
            s.update(t)
    return s


def rails_of(d):
    sn = d.get("supply_nets")
    if sn:
        return set(sn), "declared"
    return {n for n in all_nets(d) if n.lower() in RAIL_NAMESET}, "nameset"


def ac_ground(d, rails, portnets):
    driven = set()
    for m in devs(d):
        driven.add(m["source"]); driven.add(m["drain"])
    pn = set()
    for p in pas(d):
        pn.update(p.get("terminals") or [])
    isn = set()
    for q in isrc(d):
        t = isrc_t(q)
        if t:
            isn.update(t)
    g = set()
    for m in devs(d):
        gt = m["gate"]
        if gt in rails or gt in driven or gt in pn or gt in isn or gt in portnets:
            continue
        g.add(gt)
    return set(rails) | g


def superset_reach(d, acg, excite):
    adj = defaultdict(set)
    for m in devs(d):
        adj[m["gate"]].add(m["drain"])
        adj[m["gate"]].add(m["source"])
        adj[m["source"]].add(m["drain"])
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            adj[t[0]].add(t[1]); adj[t[1]].add(t[0])
    seen, st = set(), list(excite)
    while st:
        n = st.pop()
        if n in seen or n in acg:
            continue
        seen.add(n)
        for x in adj.get(n, ()):
            if x not in seen:
                st.append(x)
    return seen, adj


def bfs_dist(adj, acg, excite):
    """0-1 BFS 없이 단순 홉 거리(방향 도달 순서 판정용)."""
    dist = {}
    from collections import deque
    q = deque()
    for e in excite:
        dist[e] = 0
        q.append(e)
    while q:
        n = q.popleft()
        for x in adj.get(n, ()):
            if x in acg or x in dist:
                continue
            dist[x] = dist[n] + 1
            q.append(x)
    return dist


def classify(d, rails, acg, excite, outports):
    reach, adj = superset_reach(d, acg, excite)
    dist = bfs_dist(adj, acg, excite)
    gates = {m["gate"] for m in devs(d)}
    cells = {}
    why = {}
    for m in devs(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        gsig = (g in reach)
        if gsig:
            if dr in acg:
                c = "CD"
            elif s in acg:
                c = "CS"
            else:
                # N3.2-3: source 노드가 다른 신호 셀의 입력 단자나 출력 포트에 닿으면
                # CD/CS 이중 출력 review_needed, 아니면 CS(degeneration)
                touches = (s in gates and s in reach) or (s in outports)
                c = "CS_CD_review" if touches else "CS(degen)"
        else:
            ssig, dsig = (s in reach), (dr in reach)
            if ssig and dsig:
                ds, dd = dist.get(s, 10**9), dist.get(dr, 10**9)
                c = "CG" if ds < dd else ("pass?" if ds == dd else "pass(rev)")
            elif ssig or dsig:
                c = "load/bias"
            else:
                c = "off_path"
        cells[m["name"]] = c
        why[m["name"]] = {"gate_sig": gsig, "s": s, "d": dr,
                          "ds": dist.get(s), "dd": dist.get(dr)}
    # 역병렬 pass 묶음 조건(N3.2-3): 같은 두 노드 사이 반대 방향 + 둘 다 gate 비신호
    pairs = defaultdict(list)
    for m in devs(d):
        if cells[m["name"]] in ("CG", "pass?", "pass(rev)"):
            pairs[tuple(sorted([m["source"], m["drain"]]))].append(m)
    bundles = []
    for k, ms in pairs.items():
        if len(ms) == 2 and ms[0]["source"] == ms[1]["drain"] and ms[0]["drain"] == ms[1]["source"]:
            bundles.append([ms[0]["name"], ms[1]["name"]])
            for mm in ms:
                cells[mm["name"]] = "pass(bundle)"
        elif len(ms) >= 3:
            for mm in ms:
                cells[mm["name"]] = "review(>=3 same pair)"
    return cells, why, reach, dist, bundles


def drive_types(d, acg, cells, reach, portnets, inports, outports):
    """용어집 '입력 노드 구동 종류'. 노드별로 신호 진입 단자 종류를 모은다."""
    res = {}
    for n in sorted(reach | set(inports)):
        if n in acg:
            continue
        kinds = []
        for m in devs(d):
            c = cells.get(m["name"], "")
            sigcell = c.startswith("CS") or c in ("CD", "CG") or c.startswith("pass")
            if not sigcell:
                continue
            if m["drain"] == n:
                kinds.append(("current", m["name"] + ".d"))
            if m["source"] == n and c == "CD":
                kinds.append(("voltage", m["name"] + ".s"))
        if n in inports:
            kinds.append(("voltage", "input_port"))
        for p in pas(d):
            t = p.get("terminals") or []
            if n in t and (p.get("kind") or "").lower().startswith("res"):
                kinds.append(("value_dep", p.get("name")))
        ks = {k for k, _ in kinds}
        if not ks:
            res[n] = "none"
        elif ks == {"current"}:
            res[n] = "current"
        elif "voltage" in ks and "current" in ks:
            res[n] = "voltage(mixed: 혼재 우선)"
        elif "voltage" in ks:
            res[n] = "voltage"
        elif ks == {"value_dep"}:
            res[n] = "value_dep"
        else:
            res[n] = "/".join(sorted(ks))
    return res


def loop_graph(d, acg, excite, cells, drives):
    removed = set(acg) | set(excite)
    adj = defaultdict(set)
    elab = defaultdict(set)  # (u,v) -> {('mos',name)|('pas',name)}
    for m in devs(d):
        g, s, dr = m["gate"], m["source"], m["drain"]
        for (a, b) in ((g, dr), (g, s)):
            if a in removed or b in removed or a == b:
                continue
            adj[a].add(b); elab[(a, b)].add(("mos", m["name"]))
        if drives.get(s) == "current":
            if s not in removed and dr not in removed and s != dr:
                adj[s].add(dr); elab[(s, dr)].add(("mos", m["name"]))
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2 and t[0] not in removed and t[1] not in removed and t[0] != t[1]:
            adj[t[0]].add(t[1]); adj[t[1]].add(t[0])
            elab[(t[0], t[1])].add(("pas", p.get("name")))
            elab[(t[1], t[0])].add(("pas", p.get("name")))
    return adj, elab


def simple_cycles(adj, cap=400000):
    nodes = set(adj.keys())
    for v in adj.values():
        nodes |= v
    nodes = sorted(nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    out = []
    budget = [cap]

    def dfs(start, node, path, onp):
        if budget[0] <= 0:
            return
        for nxt in sorted(adj.get(node, ())):
            budget[0] -= 1
            if budget[0] <= 0:
                return
            if nxt == start and len(path) >= 2:
                out.append(list(path))
            elif nxt not in onp and idx.get(nxt, -1) > idx[start]:
                path.append(nxt); onp.add(nxt)
                dfs(start, nxt, path, onp)
                path.pop(); onp.discard(nxt)

    for s in nodes:
        dfs(s, s, [s], {s})
    return out, budget[0] <= 0, len(nodes)


def forward_devices(d, acg, excite, outports):
    """전달 뷰 순방향 경로에 있는 능동 셀(근사): 여기에서 도달 + 출력 포트로 도달."""
    fwd = defaultdict(set)
    for m in devs(d):
        fwd[m["gate"]].add(m["drain"]); fwd[m["gate"]].add(m["source"])
        fwd[m["source"]].add(m["drain"])
    for p in pas(d):
        t = p.get("terminals") or []
        if len(t) >= 2:
            fwd[t[0]].add(t[1]); fwd[t[1]].add(t[0])
    def reach_from(seed):
        seen, st = set(), list(seed)
        while st:
            n = st.pop()
            if n in seen or n in acg:
                continue
            seen.add(n)
            st.extend(fwd.get(n, ()))
        return seen
    rev = defaultdict(set)
    for a, bs in fwd.items():
        for b in bs:
            rev[b].add(a)
    def reach_rev(seed):
        seen, st = set(), list(seed)
        while st:
            n = st.pop()
            if n in seen or n in acg:
                continue
            seen.add(n)
            st.extend(rev.get(n, ()))
        return seen
    R = reach_from(excite)
    B = reach_rev(outports)
    on = set()
    for m in devs(d):
        ins = [m["gate"], m["source"]]
        outs = [m["drain"], m["source"]]
        if any(i in R for i in ins) and any(o in B for o in outs):
            on.add(m["name"])
    return on


def classify_cycles(cycles, elab, d, fwddev, acg, sigpath_nodes):
    capnames = {p["name"] for p in pas(d) if (p.get("kind") or "").lower().startswith("cap")}
    resnames = {p["name"] for p in pas(d) if (p.get("kind") or "").lower().startswith("res")}
    out = {"c2_miller": 0, "c2_localfb": 0, "c3_loopview": 0, "c4_record_only": 0}
    detail = {"c3": [], "c4": []}
    for cyc in cycles:
        labs = []
        for i in range(len(cyc)):
            a, b = cyc[i], cyc[(i + 1) % len(cyc)]
            labs.append(sorted(elab.get((a, b), {("?", "?")})))
        flat = [x for L in labs for x in L]
        mos = {n for (k, n) in flat if k == "mos"}
        ps = {n for (k, n) in flat if k == "pas"}
        has_cap = bool(ps & capnames)
        has_res = bool(ps & resnames)
        if has_cap and mos and mos <= fwddev:
            out["c2_miller"] += 1
        elif len(mos) == 1 and has_res and not (set(cyc) & sigpath_nodes):
            out["c2_localfb"] += 1
        elif mos - fwddev:
            out["c3_loopview"] += 1
            detail["c3"].append({"nodes": cyc, "mos": sorted(mos), "pas": sorted(ps)})
        else:
            out["c4_record_only"] += 1
            detail["c4"].append({"nodes": cyc, "mos": sorted(mos), "pas": sorted(ps)})
    return out, detail


# ------------------------------------------------------- 기둥(노드-단순 경로)
def dc_edges(d, rails, portnets):
    E = []
    for m in devs(d):
        E.append((m["source"], m["drain"], "mos", m["name"]))
    for p in pas(d):
        if (p.get("kind") or "").lower().startswith("res"):
            t = p.get("terminals") or []
            if len(t) >= 2:
                E.append((t[0], t[1], "res", p["name"]))
    for q in isrc(d):
        t = isrc_t(q)
        if t:
            E.append((t[0], t[1], "isrc", q.get("name")))
    keep = list(range(len(E)))
    ch = True
    while ch:
        ch = False
        deg = defaultdict(list)
        for i in keep:
            deg[E[i][0]].append(i); deg[E[i][1]].append(i)
        for node, ids in list(deg.items()):
            if node in rails or node in portnets:
                continue
            if len(ids) == 1 and E[ids[0]][2] == "res":
                keep.remove(ids[0]); ch = True; break
    return [E[i] for i in keep]


def columns(d, rails, portnets):
    E = dc_edges(d, rails, portnets)
    deg = defaultdict(int); adj = defaultdict(list)
    for i, (u, v, k, n) in enumerate(E):
        deg[u] += 1; deg[v] += 1
        adj[u].append((v, i)); adj[v].append((u, i))
    bn = sorted([n for n, c in deg.items() if c >= 3])
    term = set(bn) | set(rails)
    used = set(); branches = []
    for t in sorted(term):
        for (nb, ei) in adj[t]:
            if ei in used:
                continue
            path = [ei]; used.add(ei); cur = nb
            while cur not in term:
                nxt = [(x, j) for (x, j) in adj[cur] if j not in used]
                if len(nxt) != 1:
                    break
                x, j = nxt[0]; used.add(j); path.append(j); cur = x
            branches.append({"ends": tuple(sorted([t, cur])), "elems": [E[i][3] for i in path]})
    badj = defaultdict(list)
    for bi, b in enumerate(branches):
        a, c = b["ends"]
        badj[a].append((c, bi))
        if a != c:
            badj[c].append((a, bi))
    cols = []
    for r1, r2 in itertools.combinations(sorted(rails), 2):
        st = [(r1, [], {r1})]
        while st:
            node, pb, vis = st.pop()
            if node == r2 and pb:
                cols.append(list(pb)); continue
            for (nb, bi) in badj[node]:
                if bi in pb or nb in vis:
                    continue
                st.append((nb, pb + [bi], vis | {nb}))
    cov = set()
    for c in cols:
        cov.update(c)
    devcol = defaultdict(set)
    for ci, c in enumerate(cols):
        for bi in c:
            for e in branches[bi]["elems"]:
                devcol[e].add(ci)
    return {"n_branches": len(branches),
            "branch_nodes_nonrail": [x for x in bn if x not in rails],
            "n_branch_nodes_nonrail": len([x for x in bn if x not in rails]),
            "n_columns_node_simple": len(cols),
            "uncovered_branches": [branches[bi]["elems"] for bi in range(len(branches)) if bi not in cov],
            "mos_not_in_any_column": [m["name"] for m in devs(d) if not devcol.get(m["name"])]}


def run(name):
    d = load(name)
    ports = ports_of(d)
    portnets = set(ports.keys())
    rails, rsrc = rails_of(d)
    inports = [k for k, v in ports.items()
               if "input" in (v.get("role") or "") or v.get("direction") == "input"]
    outports = [k for k, v in ports.items()
                if "output" in (v.get("role") or "") or v.get("direction") == "output"]
    acg = ac_ground(d, rails, portnets)
    rec = {"circuit": name, "rails": sorted(rails), "rail_source": rsrc,
           "acg": sorted(acg), "in": inports, "out": outports,
           "columns": columns(d, rails, portnets)}
    if not (inports and outports):
        rec["view"] = "불가(U-08)"
        with open(JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec
    cells, why, reach, dist, bundles = classify(d, rails, acg, inports, set(outports))
    drives = drive_types(d, acg, cells, reach, portnets, inports, outports)
    tally = defaultdict(int)
    for v in cells.values():
        tally[v] += 1
    adj, elab = loop_graph(d, acg, inports, cells, drives)
    cyc, trunc, nn = simple_cycles(adj)
    fwd = forward_devices(d, acg, inports, outports)
    sig_nodes = {n for n in reach if n not in acg}
    cl, det = classify_cycles(cyc, elab, d, fwd, acg, sig_nodes)
    rec.update({"view": "가능", "cells": cells, "cell_tally": dict(sorted(tally.items())),
                "pass_bundles": bundles, "drives": drives,
                "n_simple_cycles": len(cyc), "cycles_truncated": trunc,
                "cycle_class": cl, "cycle_detail_c4": det["c4"][:10],
                "cycle_detail_c3": det["c3"][:10],
                "forward_devices": sorted(fwd),
                "gate_nets_reachable": {m["name"]: (m["gate"] in reach) for m in devs(d)}})
    with open(JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


if __name__ == "__main__":
    if os.path.exists(JSONL):
        os.remove(JSONL)
    for n in ["current_reuse_telescopic_ota", "folded_cascode", "nmcnr_amplifier",
              "two_stage_ota", "two_stage_ota_sf", "pushpull_follower_buffer",
              "sf_pushpull_output_opamp", "ngcc_3stage_ff"]:
        try:
            r = run(n)
            print(n, r.get("view"), r.get("cell_tally"), r.get("n_simple_cycles"),
                  r.get("cycle_class"), r["columns"]["n_columns_node_simple"])
        except Exception as e:
            import traceback
            traceback.print_exc()
            with open(JSONL, "a", encoding="utf-8") as f:
                f.write(json.dumps({"circuit": n, "error": repr(e)}, ensure_ascii=False) + "\n")
