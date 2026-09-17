# -*- coding: utf-8 -*-
"""Independent re-measurement of plan v5.18 rule claims (generality audit round 4).

Writes results by appending one JSON line per (circuit, case) to results.jsonl
and a human-readable line to results.txt, so a crash mid-run keeps partial data.
"""
import json
import os
import sys
import itertools
from pathlib import Path

LIB = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library")
OUT = Path(__file__).resolve().parent
JSONL = OUT / "results.jsonl"
TXT = OUT / "results.txt"


def emit(circuit, case, value, note=""):
    rec = {"circuit": circuit, "case": case, "value": value, "note": note}
    with open(JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
    with open(TXT, "a", encoding="utf-8") as f:
        f.write("%-32s %-40s %s  %s\n" % (circuit, case, value, note))
        f.flush()


class Ckt:
    def __init__(self, path):
        d = json.load(open(path, encoding="utf-8"))
        self.name = d.get("topology_name") or path.stem.replace(".topology", "")
        self.d = d
        self.devs = [x for x in d.get("netlist", []) if x.get("kind") in ("nmos", "pmos", "nfet", "pfet")]
        self.other_devs = [x for x in d.get("netlist", []) if x.get("kind") not in ("nmos", "pmos", "nfet", "pfet")]
        self.passives = d.get("passive_elements", []) or []
        self.isrc = d.get("ideal_sources", []) or []
        self.rails = set(d.get("supply_nets") or [])
        ports = d.get("ports") or {}
        self.ports = {k: v for k, v in ports.items() if not k.startswith("_")}
        self.in_ports = [k for k, v in self.ports.items() if "input" in (v.get("role") or "")]
        self.out_ports = [k for k, v in self.ports.items() if "output" in (v.get("role") or "")]
        # net -> list of (dev, terminal)
        self.term = {}
        for m in self.devs:
            for t in ("drain", "gate", "source"):
                self.term.setdefault(m[t], []).append((m["name"], t))
        self.byname = {m["name"]: m for m in self.devs}
        self.pass_terms = {}
        for p in self.passives:
            for n in p.get("terminals", []):
                self.pass_terms.setdefault(n, []).append(p["name"])
        self.isrc_terms = {}
        for s in self.isrc:
            for n in s.get("terminals", []):
                self.isrc_terms.setdefault(n, []).append(s["name"])

    def all_nets(self):
        s = set(self.term)
        s |= set(self.pass_terms)
        s |= set(self.isrc_terms)
        return s

    # ---------- DC conduction graph (DEC-70 / DEC-71 edge kinds) ----------
    def dc_edges(self, pruned=True):
        """edges: (u, v, label). MOS channel, resistors, ideal sources.
        Gate and capacitors are not edges."""
        E = []
        for m in self.devs:
            E.append((m["source"], m["drain"], "ch:" + m["name"]))
        for p in self.passives:
            if p.get("kind") == "resistor":
                t = p["terminals"]
                E.append((t[0], t[1], "r:" + p["name"]))
        for s in self.isrc:
            t = s["terminals"]
            E.append((t[0], t[1], "i:" + s["name"]))
        if not pruned:
            return E
        # leaf pruning (DEC-70): repeatedly remove non-rail non-port nodes whose
        # only DC edge is a single resistor, together with that resistor.
        keep = set(range(len(E)))
        changed = True
        protect = self.rails | set(self.ports)
        while changed:
            changed = False
            deg = {}
            for i in sorted(keep):
                u, v, lab = E[i]
                deg.setdefault(u, []).append(i)
                deg.setdefault(v, []).append(i)
            for n, idxs in sorted(deg.items()):
                if n in protect:
                    continue
                if len(idxs) == 1 and E[idxs[0]][2].startswith("r:"):
                    keep.discard(idxs[0])
                    changed = True
                    break
        return [E[i] for i in sorted(keep)]

    def pruned_resistors(self):
        full = set(l for _, _, l in self.dc_edges(pruned=False) if l.startswith("r:"))
        kept = set(l for _, _, l in self.dc_edges(pruned=True) if l.startswith("r:"))
        return sorted(full - kept)

    # ---------- DEC-60 (iii) hidden rail candidates ----------
    def hidden_rail_candidates(self):
        mos_nets = set(self.term)
        cand = []
        E = self.dc_edges(pruned=False)
        adj = {}
        for u, v, _ in E:
            adj.setdefault(u, set()).add(v)
            adj.setdefault(v, set()).add(u)
        for n in sorted(self.all_nets()):
            if n in mos_nets:
                continue
            # BFS from n over DC conduction graph (pre-pruning), look for a rail
            seen, stack, found = {n}, [n], False
            while stack:
                x = stack.pop()
                if x in self.rails:
                    found = True
                    break
                for y in sorted(adj.get(x, ())):
                    if y not in seen:
                        seen.add(y)
                        stack.append(y)
            if not found:
                cand.append(n)
        return cand

    # ---------- branch / column (DEC-71) ----------
    def branches_columns(self):
        E = self.dc_edges(pruned=True)
        deg = {}
        for u, v, _ in E:
            deg[u] = deg.get(u, 0) + 1
            deg[v] = deg.get(v, 0) + 1
        branch_nodes = sorted(n for n, dd in deg.items() if dd >= 3)
        term_nodes = set(branch_nodes) | set(self.rails)
        # build adjacency of edges
        adj = {}
        for i, (u, v, lab) in enumerate(E):
            adj.setdefault(u, []).append((v, i))
            adj.setdefault(v, []).append((u, i))
        used = set()
        branches = []
        for i, (u, v, lab) in enumerate(E):
            if i in used:
                continue
            # extend maximal serial chain through non-terminal nodes
            chain = [i]
            used.add(i)
            ends = []
            for start, other in ((u, v), (v, u)):
                cur, prev_edge, prev_node = start, i, other
                while cur not in term_nodes and len(adj.get(cur, [])) == 2:
                    nxt = [(w, j) for (w, j) in adj[cur] if j != prev_edge]
                    if not nxt:
                        break
                    w, j = nxt[0]
                    if j in used:
                        break
                    used.add(j)
                    chain.append(j)
                    prev_edge, prev_node, cur = j, cur, w
                ends.append(cur)
            branches.append({"ends": tuple(sorted(ends)), "edges": sorted(chain)})
        # columns: node-simple paths between two distinct rail nets over branch graph
        badj = {}
        for bi, b in enumerate(branches):
            a, c = b["ends"]
            badj.setdefault(a, []).append((c, bi))
            if a != c:
                badj.setdefault(c, []).append((a, bi))
        rails = sorted(self.rails)
        cols = []
        for r1, r2 in itertools.combinations(rails, 2):
            # enumerate node-simple paths r1 -> r2
            def dfs(node, visited, path):
                if node == r2 and path:
                    cols.append((r1, r2, tuple(path)))
                    return
                for (w, bi) in sorted(badj.get(node, []), key=lambda x: x[1]):
                    if bi in path:
                        continue
                    if w in visited:
                        continue
                    dfs(w, visited | {w}, path + (bi,))
            dfs(r1, {r1}, ())
        in_col = set()
        for _, _, p in cols:
            in_col |= set(p)
        orphan = [bi for bi in range(len(branches)) if bi not in in_col]
        nonrail_branch_nodes = [n for n in branch_nodes if n not in self.rails]
        return branches, cols, branch_nodes, nonrail_branch_nodes, orphan

    # ---------- AC structure ----------
    def base_ac_ground(self):
        """(1) rails (2) gate-only, not driven, not port/passive/ideal terminal"""
        ag = set(self.rails)
        for n in sorted(self.all_nets()):
            if n in ag:
                continue
            if n in self.ports:
                continue
            if n in self.pass_terms or n in self.isrc_terms:
                continue
            terms = self.term.get(n, [])
            if terms and all(t == "gate" for _, t in terms):
                ag.add(n)
        return ag

    def signal_nets(self, excite, ac_ground):
        sig = set(e for e in excite if e not in ac_ground)
        changed = True
        while changed:
            changed = False
            for m in self.devs:
                if m["gate"] in sig:
                    for t in ("drain", "source"):
                        n = m[t]
                        if n not in sig and n not in ac_ground:
                            sig.add(n)
                            changed = True
                if m["source"] in sig:
                    n = m["drain"]
                    if n not in sig and n not in ac_ground:
                        sig.add(n)
                        changed = True
            for p in self.passives:
                t = p.get("terminals", [])
                if len(t) == 2:
                    for a, b in ((t[0], t[1]), (t[1], t[0])):
                        if a in sig and b not in sig and b not in ac_ground:
                            sig.add(b)
                            changed = True
        return sig

    def bias_dependent_nets(self, excite, ac_ground, with_cond0=True):
        """Rule 1 (4) predicate."""
        sig = self.signal_nets(excite, ac_ground)
        hits = []
        for b in sorted(self.all_nets()):
            if b in ac_ground:
                continue
            if with_cond0 and b not in sig:
                continue
            terms = self.term.get(b, [])
            if not terms:
                continue
            # (i) signal leaves b only via gate
            # signal leaves b via a channel terminal if b is source of a device
            # whose drain gets signal from b (s->d), i.e. b acts as a driving
            # channel terminal.  Approximate: b must not be the source of any
            # device that is on the signal path, and must not be drain feeding on.
            leaves_channel = False
            for (dn, t) in terms:
                if t == "source":
                    # s->d edge carries signal out of b
                    leaves_channel = True
                if t == "drain":
                    # d->s is not a signal edge in the plan's edge set
                    pass
            if leaves_channel:
                continue
            if not any(t == "gate" for _, t in terms):
                continue
            # (ii) every channel terminal driving b is either from a device that
            # reads b as gate, or from a device whose gate is outside signal path
            drivers = [(dn, t) for (dn, t) in terms if t in ("drain", "source")]
            if not drivers:
                continue
            self_gate = []
            ok = True
            for (dn, t) in drivers:
                m = self.byname[dn]
                if m["gate"] == b:
                    self_gate.append(dn)
                elif m["gate"] not in sig:
                    pass
                else:
                    ok = False
                    break
            if not ok or not self_gate:
                continue
            # (iii) one of the self-gate devices lies on a channel-only chain
            # starting from a signal node that stays a signal node without b
            sig_wo_b = self.signal_nets([e for e in excite], ac_ground | {b})
            found = False
            for dn in self_gate:
                m = self.byname[dn]
                # walk channel-only from this device
                seen = set()
                stack = [m["source"], m["drain"]]
                while stack:
                    n = stack.pop()
                    if n in seen:
                        continue
                    seen.add(n)
                    if n != b and n in sig and n in sig_wo_b:
                        found = True
                        break
                    for (dn2, t2) in self.term.get(n, []):
                        if t2 in ("drain", "source"):
                            m2 = self.byname[dn2]
                            for nn in (m2["source"], m2["drain"]):
                                if nn not in seen:
                                    stack.append(nn)
                if found:
                    break
            if found:
                hits.append(b)
        return hits

    def cell_classes(self, excite, ac_ground):
        """Rule 3 cell classification, incl. the CG/pass discriminator."""
        sig = self.signal_nets(excite, ac_ground)
        res = {}
        for m in self.devs:
            g, d, s = m["gate"], m["drain"], m["source"]
            if g in sig:
                if d in ac_ground:
                    res[m["name"]] = "CD"
                elif s in ac_ground:
                    res[m["name"]] = "CS"
                else:
                    res[m["name"]] = "CS/CD?"
                continue
            # gate outside signal path -> CG or pass
            if d not in sig and s not in sig:
                res[m["name"]] = "off_path"
                continue
            # remove this device's channel edge and recompute reachability
            saved = self.devs
            self.devs = [x for x in saved if x["name"] != m["name"]]
            try:
                sig2 = self.signal_nets(excite, ac_ground)
            finally:
                self.devs = saved
            if d not in sig2:
                res[m["name"]] = "CG"
            elif s in sig2 and d in sig2:
                res[m["name"]] = "pass"
            else:
                res[m["name"]] = "CG"
        return res, sig

    def antiparallel_pass_pairs(self, ac_ground, sig):
        pairs = []
        seen = set()
        for a, b in itertools.combinations(self.devs, 2):
            if a["gate"] in sig or b["gate"] in sig:
                continue
            if a["source"] == b["drain"] and a["drain"] == b["source"]:
                key = tuple(sorted([a["name"], b["name"]]))
                if key not in seen:
                    seen.add(key)
                    pairs.append(key)
        return pairs

    def forward_cells(self, excite, ac_ground, cells, sig):
        """forward path = reachable from excite AND back-reachable from output port"""
        # back reachability over the same directed signal edges
        radj = {}
        def add(u, v):
            radj.setdefault(v, set()).add(u)
        for m in self.devs:
            if m["gate"] in sig:
                add(m["gate"], m["drain"])
                add(m["gate"], m["source"])
            if m["source"] in sig:
                add(m["source"], m["drain"])
        for p in self.passives:
            t = p.get("terminals", [])
            if len(t) == 2:
                add(t[0], t[1])
                add(t[1], t[0])
        back = set(n for n in self.out_ports if n in sig)
        stack = list(back)
        while stack:
            x = stack.pop()
            for y in sorted(radj.get(x, ())):
                if y not in back:
                    back.add(y)
                    stack.append(y)
        fwd = {}
        for name, c in cells.items():
            m = self.byname[name]
            out_term = {"CS": m["drain"], "CG": m["drain"], "CD": m["source"]}.get(c)
            if out_term is None:
                continue
            if out_term in sig and out_term in back:
                fwd[name] = c
        return fwd


def default_excite(c):
    if c.in_ports:
        return list(c.in_ports)
    return []


def main():
    for p in (JSONL, TXT):
        if p.exists():
            p.unlink()
    files = sorted(LIB.glob("*.topology.json"))
    for f in files:
        if f.name.startswith("_TEMPLATE"):
            continue
        c = Ckt(f)
        emit(c.name, "n_devices", len(c.devs))
        emit(c.name, "supply_nets", sorted(c.rails))
        emit(c.name, "ports_in/out", [c.in_ports, c.out_ports])
        # DEC-60 (iii)
        hr = c.hidden_rail_candidates()
        emit(c.name, "DEC60(iii) hidden_rail_candidates", hr,
             "declared? " + str([n in c.rails for n in hr]))
        # DEC-70 leaf pruning
        emit(c.name, "DEC70 pruned_resistors", c.pruned_resistors())
        # DEC-71
        br, cols, bn, nrbn, orphan = c.branches_columns()
        emit(c.name, "DEC71 n_branches", len(br))
        emit(c.name, "DEC71 n_branch_nodes(all/nonrail)", [len(bn), len(nrbn)])
        emit(c.name, "DEC71 n_columns", len(cols))
        emit(c.name, "DEC71 orphan_branches", len(orphan))
        # AC structure
        ag0 = c.base_ac_ground()
        emit(c.name, "acgnd(1)(2)", sorted(ag0))
        ex = default_excite(c)
        if not ex:
            emit(c.name, "AC", "SKIP", "no input ports")
            continue
        bd_with = c.bias_dependent_nets(ex, ag0, with_cond0=True)
        bd_without = c.bias_dependent_nets(ex, ag0, with_cond0=False)
        emit(c.name, "rule1(4) bias_dependent_nets (with cond0)", bd_with)
        emit(c.name, "rule1(4) bias_dependent_nets (no cond0)", bd_without)
        ag = ag0 | set(bd_with)
        cells, sig = c.cell_classes(ex, ag)
        counts = {}
        for v in cells.values():
            counts[v] = counts.get(v, 0) + 1
        emit(c.name, "cells(all, acgnd incl rule1(4))", counts)
        emit(c.name, "CG list", sorted(k for k, v in cells.items() if v == "CG"))
        emit(c.name, "pass list", sorted(k for k, v in cells.items() if v == "pass"))
        ap = c.antiparallel_pass_pairs(ag, sig)
        emit(c.name, "antiparallel pass pairs", ap)
        fwd = c.forward_cells(ex, ag, cells, sig)
        fcounts = {}
        for v in fwd.values():
            fcounts[v] = fcounts.get(v, 0) + 1
        emit(c.name, "cells(forward only)", fcounts)
        emit(c.name, "CG list (forward)", sorted(k for k, v in fwd.items() if v == "CG"))
        # without rule1(4)
        cells0, sig0 = c.cell_classes(ex, ag0)
        fwd0 = c.forward_cells(ex, ag0, cells0, sig0)
        f0 = {}
        for v in fwd0.values():
            f0[v] = f0.get(v, 0) + 1
        emit(c.name, "cells(forward, no rule1(4))", f0)


if __name__ == "__main__":
    main()
    print("done")
