# -*- coding: utf-8 -*-
"""engine2: adds fixed 2-cycle filter, s->d edge variants, rule 9(b)(c),
DEC-63 buffer bundles, DEC-64 G_vgs cycles, block/column mapping, GB2 stop ledger."""
import json, itertools, collections
from pathlib import Path
import networkx as nx
from engine import (Circuit, load_all, gb0_gate, build_views, ac_ground_base, signal_nets,
                    forward_path, bias_dependent_nets, classify_cells, drive_kinds,
                    stage_assign, dc_conduction_graph, branches_columns, bfs_dist, OUT)

CELLS = {"CS", "CG", "CD", "pass"}


# -------------------------------------------------- loop graph (2 variants)
def loop_graph(c, view, acg, dkv, variant, cells):
    removed = set(acg) | set(view["excite"])
    G = nx.DiGraph()
    for n in c.all_nets():
        if n not in removed: G.add_node(n)
    meta = collections.defaultdict(list)

    def add(u, v, name, kind):
        if u in G and v in G and u != v:
            G.add_edge(u, v); meta[(u, v)].append((name, kind))
    for m in c.devices:
        g, d, s = m["gate"], m["drain"], m["source"]
        add(g, d, m["name"], "g->d"); add(g, s, m["name"], "g->s")
        if variant == "A":
            cur = dkv.get(s, {}).get("kind") in ("current", "tap")
        else:  # B: plan N3.2-2 sentence -- any node entered by a signal cell's drain
            cur = any(m2["drain"] == s and cells.get(m2["name"], {}).get("cls") in CELLS
                      for m2 in c.devices)
        if cur: add(s, d, m["name"], "s->d")
    for p in c.passives:
        a, b = p["terminals"]
        add(a, b, p["name"], "passive"); add(b, a, p["name"], "passive")
    return G, meta


def enumerate_cycles(G, meta, c, cap=50000, bundles=()):
    pn = {p["name"] for p in c.passives}
    bpairs = {frozenset((a, b)) for a, b, _, _ in bundles}
    out = []
    for cyc in nx.simple_cycles(G):
        if len(cyc) < 2: continue
        if len(cyc) == 2:
            u, v = cyc
            # a genuine closed path needs one realization that is not the same 2-terminal
            # passive traversed both ways
            genuine = False
            for e1 in meta[(u, v)]:
                for e2 in meta[(v, u)]:
                    if e1[0] == e2[0]: continue           # same 2-terminal element round trip
                    if frozenset((e1[0], e2[0])) in bpairs: continue  # pass-bundle internal loop
                    genuine = True
            if not genuine: continue
        out.append(cyc)
        if len(out) >= cap: break
    return out


def classify_loops(c, view, acg, S, FWD, cells, cycles, dist, meta):
    pmap = {p["name"]: p for p in c.passives}
    out = []
    for cyc in cycles:
        L = len(cyc)
        edges = [(cyc[i], cyc[(i + 1) % L]) for i in range(L)]
        elems = [meta[e] for e in edges]
        seg_pass = [all(n in pmap for n, k in es) for es in elems]
        devs = sorted({n for es in elems for n, k in es if n not in pmap})
        rec = {"cycle": cyc, "elements": [[f"{n}:{k}" for n, k in es] for es in elems],
               "devices": devs}
        if not (set(cyc) & FWD):
            rec["class"] = "(1.5) bias SCC"; out.append(rec); continue

        def runs_of(mask):
            r, used = [], set()
            if all(mask): return [list(range(L))]
            for i in range(L):
                if not mask[i] or i in used: continue
                run = [i]; used.add(i)
                j = (i + 1) % L
                while mask[j] and j not in used:
                    run.append(j); used.add(j); j = (j + 1) % L
                k = (i - 1) % L
                while mask[k] and k not in used:
                    run.insert(0, k); used.add(k); k = (k - 1) % L
                r.append(run)
            return r
        miller = False
        for run in runs_of(seg_pass):
            has_cap = any(any(pmap[n].get("kind") == "capacitor" for n, kk in elems[i]) for i in run)
            a, b = cyc[run[0]], cyc[(run[-1] + 1) % L]
            if has_cap and a in FWD and b in FWD:
                miller = True; break
        rec["miller"] = miller
        back = []
        for (u, v) in edges:
            du, dv = dist.get(u), dist.get(v)
            back.append(False if du is None or dv is None else dv <= du)
        rruns = runs_of(back)
        rec["return_runs"] = [[f"{cyc[i]}->{cyc[(i+1)%L]}" for i in run] for run in rruns]
        three_b, notes = False, []
        for run in rruns:
            ra = {n for i in run for n, k in elems[i] if n not in pmap and cells.get(n, {}).get("cls") in CELLS}
            rp = {n for i in run for n, k in elems[i] if n in pmap}
            if not ra: notes.append("(가) 복귀 수동소자만"); continue
            if not rp and len(ra) == 2: notes.append("(나) 수동소자 없는 2능동셀"); continue
            three_b = True
        rec["return_note"] = notes
        rec["3a_candidates"] = sorted(d for d in devs if cells.get(d, {}).get("cls") in CELLS
                                      and cells[d].get("out") is not None and cells[d]["out"] not in FWD)
        k = []
        if miller: k.append("(2)")
        if three_b: k.append("(3-b)")
        if not k:
            k.append("기록만(나)" if any("(나)" in x for x in notes) else "(4)")
        rec["class"] = "+".join(k)
        if "(3-b)" in rec["class"]:
            rec["break_candidates"] = sorted({c.dev[d]["gate"] for d in devs
                                              if cells.get(d, {}).get("cls") == "CS"})
            if not rec["break_candidates"]:
                rec["break_candidates_empty"] = True
        out.append(rec)
    return out


# -------------------------------------------------- blocks / rule 9(c)
def impedance_grade(c, node, acg):
    low = []
    for m in c.devices:
        if m["source"] == node and m["gate"] in acg: low.append((m["name"], "source,gate=acgnd"))
        if m["gate"] == m["drain"] == node: low.append((m["name"], "diode d+g"))
    if low: return "낮음", low
    if any(p.get("kind") == "resistor" and node in p["terminals"] for p in c.passives):
        return "값 의존", []
    return "높음", []


def build_blocks(c, view, acg, S, FWD, cells, dkv, stages):
    blocks = []
    for nm, kind, innode in stages["stage_starts"]:
        node = cells[nm]["out"]
        members = [nm]
        guard = 0
        while guard < 50:
            guard += 1
            nxt = None
            for m2 in c.devices:
                if cells[m2["name"]]["cls"] == "CG" and m2["source"] == node \
                        and dkv.get(node, {}).get("kind") in ("current", "tap"):
                    nxt = m2; break
            if not nxt: break
            members.append(nxt["name"]); node = nxt["drain"]
        grade, ev = impedance_grade(c, node, acg)
        # rule 9(c) with the diode-mirror carve-out
        rule9c = None
        if node in FWD and grade == "낮음":
            diode_here = [m for m in c.devices if m["gate"] == m["drain"] == node]
            mirror_out = [m for m in c.devices if m["gate"] == node and m["gate"] != m["drain"]
                          and cells[m["name"]].get("out") in FWD]
            if diode_here and mirror_out:
                rule9c = None  # mirror input: block continues toward mirror output device
            else:
                rule9c = f"9(c) 발동: 출력노드 {node} 임피던스 등급 낮음 ({ev})"
        blocks.append({"start": nm, "kind": kind, "input_node": innode, "members": members,
                       "output_node": node, "impedance": grade, "impedance_evidence": ev,
                       "rule9c": rule9c})
    return blocks


def buffer_bundles(c, view, acg, S, FWD, cells, dkv, block_outs=()):
    """DEC-63 R(u)."""
    res = []
    us = set()
    for nm, info in cells.items():
        if info["cls"] != "CD": continue
        us.add(c.dev[nm]["gate"])
    # u must be an input port or a gain-block output node -> approximate: voltage-driven net
    for u in sorted(us):
        if u not in view["excite"] and u not in set(block_outs): continue
        R, frontier, chain = set(), [u], []
        while frontier:
            n = frontier.pop()
            for m in c.devices:
                if cells[m["name"]]["cls"] == "CD" and m["gate"] == n:
                    s = m["source"]
                    chain.append(m["name"])
                    if s not in R:
                        R.add(s); frontier.append(s)
        if not R: continue
        merge = sorted(n for n in R if not any(cells[m["name"]]["cls"] == "CD" and m["gate"] == n
                                               for m in c.devices))
        res.append({"u": u, "R": sorted(R), "cells": sorted(set(chain)),
                    "merge_nodes": merge,
                    "verdict": "버퍼 블록" if len(merge) == 1 else "기록만(다출력 버퍼)"})
    return res


# -------------------------------------------------- DEC-64 G_vgs
def gvgs_cycles(c, with_vds):
    rails = set(c.supply_nets or [])
    def nd(n): return "RAIL" if n in rails else n
    G = nx.MultiGraph()
    for m in c.devices:
        G.add_edge(nd(m["gate"]), nd(m["source"]), key="gs:" + m["name"], et="gs", dev=m["name"])
    if with_vds:
        for m in c.devices:
            G.add_edge(nd(m["drain"]), nd(m["source"]), key="ds:" + m["name"], et="ds", dev=m["name"])
    in_ports = {nd(p) for p, v in c.ports.items()
                if v.get("direction") == "input" or "input" in str(v.get("role", ""))}
    # spanning forest + fundamental cycles
    T = nx.Graph()
    T.add_nodes_from(G.nodes())
    tree_keys = set()
    for u, v, k in G.edges(keys=True):
        if u == v: continue
        if not nx.has_path(T, u, v) if (u in T and v in T) else True:
            pass
    # build spanning forest explicitly
    uf = {n: n for n in G.nodes()}
    def find(x):
        while uf[x] != x: uf[x] = uf[uf[x]]; x = uf[x]
        return x
    for u, v, k in sorted(G.edges(keys=True), key=lambda e: e[2]):
        if u == v: continue
        ru, rv = find(u), find(v)
        if ru != rv:
            uf[ru] = rv; tree_keys.add(k); T.add_edge(u, v, key=k)
    out = []
    for u, v, k, data in sorted(G.edges(keys=True, data=True), key=lambda e: e[2]):
        if k in tree_keys: continue
        if u == v:
            out.append({"nontree": k, "type": "self-loop", "class": "(0) 자기 엣지"}); continue
        try:
            path = nx.shortest_path(T, u, v)
        except Exception:
            out.append({"nontree": k, "class": "확인 못 함(경로 없음)"}); continue
        # collect edge keys along path
        pk = []
        for a, b in zip(path, path[1:]):
            kk = list(T[a][b].keys())[0] if hasattr(T[a][b], "keys") else None
            pk.append(kk)
        cyc_keys = [k] + [x for x in pk if x]
        nodes = set(path)
        n_ds = sum(1 for x in cyc_keys if str(x).startswith("ds:"))
        # v0: parallel edge (same node pair already in tree between u,v)
        if len(path) == 2:
            cl = "(v0) equal_vgs"
        elif len(nodes & in_ports) >= 2:
            cl = "(v1) 포트 차 루프"
        elif with_vds and n_ds == 1:
            cl = "(VDS-1)"
        else:
            cl = "(v2) kvl_branch"
        out.append({"nontree": k, "cycle_nodes": sorted(nodes), "edges": cyc_keys,
                    "n_ds": n_ds, "class": cl,
                    "devices": sorted({str(x).split(":")[1] for x in cyc_keys if ":" in str(x)})})
    return out


# -------------------------------------------------- main
def main():
    circuits = load_all()
    res = {}
    for c in circuits:
        rec = {"circuit": c.name, "n_devices": len(c.devices)}
        rec["gb0"] = gb0_gate(c)
        views = build_views(c)
        rec["views"] = []
        for view in views:
            acg0 = ac_ground_base(c, view)
            S0 = signal_nets(c, view, acg0)
            F0 = forward_path(c, view, acg0, S0)
            bd = bias_dependent_nets(c, view, acg0, S0, F0)
            acg = set(acg0) | {x["net"] for x in bd}
            S = signal_nets(c, view, acg)
            F = forward_path(c, view, acg, S)
            cells, bundles, triples = classify_cells(c, view, acg, S, F)
            dkraw, dkv = drive_kinds(c, view, acg, S, F, cells)
            st = stage_assign(c, view, cells, dkv)
            blocks = build_blocks(c, view, acg, S, F, cells, dkv, st)
            bufs = buffer_bundles(c, view, acg, S, F, cells, dkv,
                                  [b["output_node"] for b in blocks])
            counts = collections.Counter(v["cls"] for v in cells.values())
            fwd = collections.Counter(v["cls"] for v in cells.values() if v.get("out") in F)
            nodes_nodrive = sorted(n for n, v in dkv.items() if v["kind"] in ("none", "review_needed"))
            nodes_review = sorted(n for n, v in dkv.items() if v.get("flag"))
            loops = {}
            for variant in ("A", "B"):
                G, meta = loop_graph(c, view, acg, dkv, variant, cells)
                cyc = enumerate_cycles(G, meta, c, bundles=bundles)
                for pc in (0, 1):
                    dist = bfs_dist(c, view, acg, cells, dkv, pc)
                    cl = classify_loops(c, view, acg, S, F, cells, cyc, dist, meta)
                    loops[f"{variant}_pc{pc}"] = {"n_cycles": len(cyc),
                                                  "counts": dict(collections.Counter(x["class"] for x in cl)),
                                                  "detail": cl}
            vrec = {"view": view["name"], "excite": sorted(view["excite"]), "sense": sorted(view["sense"]),
                    "acg0": sorted(acg0), "bias_dep": bd, "acg": sorted(acg),
                    "signal_nets": sorted(S), "forward_path": sorted(F),
                    "cells": cells, "counts": dict(counts), "counts_forward": dict(fwd),
                    "pass_bundles": bundles, "triple_warn": triples,
                    "drive_kinds": dkv, "drive_raw": dkraw,
                    "nodes_without_drive": nodes_nodrive,
                    "nodes_mixed_review": nodes_review,
                    "stages": st, "blocks": blocks, "buffer_bundles": bufs,
                    "loops": loops}
            rec["views"].append(vrec)
        rec["dec71"] = branches_columns(c)
        # column <-> block mapping
        d71 = rec["dec71"]
        bdev = {}
        for i, br in enumerate(d71["branches"]):
            for e in br["edges"]:
                if str(e).startswith("dev:"): bdev.setdefault(str(e)[4:], []).append(i)
        colbr = [set(col["branches"]) for col in d71["columns"]]
        for vr in rec["views"]:
            for b in vr["blocks"]:
                need = set()
                for dv in b["members"]: need |= set(bdev.get(dv, []))
                cols = [i for i, cb in enumerate(colbr) if cb & need]
                b["covering_columns"] = cols
                b["n_covering_columns"] = len(cols)
            vr["blocks_without_column"] = [b["start"] for b in vr["blocks"] if b["n_covering_columns"] == 0]
        # rule 9(b): current-input port feeding a CG
        cur_ports = [p for p, v in c.ports.items() if str(v.get("kind", "")).lower() == "current"
                     or str(v.get("signal", "")).lower() == "current"]
        rec["rule9b_current_input_ports"] = cur_ports
        rec["gvgs_gs_only"] = gvgs_cycles(c, False)
        rec["gvgs_with_vds"] = gvgs_cycles(c, True)
        res[c.name] = rec
        with open(OUT / "engine2.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    json.dump(res, open(OUT / "all2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("done", len(res))


if __name__ == "__main__":
    main()
