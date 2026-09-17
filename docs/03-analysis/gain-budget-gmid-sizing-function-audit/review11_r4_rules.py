# -*- coding: utf-8 -*-
"""Round-4 independent re-implementation of plan v5.18 SP1 / DEC-59 / DEC-60(iii) / DEC-71 rules.

Written from the plan text only (verifier code, NOT the orchestrator's review9/review10 scripts).
Appends every per-circuit result to r4_results.txt so a crash keeps partial output.
"""
import json, os, sys, io, itertools
from collections import defaultdict, deque

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "r4_results.txt")

CIRCUITS = ["common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode",
            "ngcc_3stage_ff", "nmcnr_amplifier", "pushpull_follower_buffer",
            "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]

EXISTING4 = ["current_reuse_telescopic_ota", "folded_cascode", "two_stage_ota", "nmcnr_amplifier"]


def emit(s=""):
    with io.open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s)


# ---------------------------------------------------------------- loading
class C:
    def __init__(self, name):
        d = json.load(io.open(os.path.join(LIB, name + ".topology.json"), encoding="utf-8"))
        self.name = name
        self.raw = d
        self.devs = [x for x in (d.get("netlist") or []) if not str(x.get("name", "")).startswith("_")]
        self.pas = [p for p in (d.get("passive_elements") or []) if p.get("terminals")]
        self.isrc = [s for s in (d.get("ideal_sources") or []) if s.get("terminals")]
        self.rails = set(d.get("supply_nets") or [])
        ports = d.get("ports") or {}
        self.ports = {k: v for k, v in ports.items() if not k.startswith("_")}
        self.inputs = sorted([k for k, v in self.ports.items()
                              if "input" in str(v.get("role", "")) or v.get("direction") == "input"])
        self.outputs = sorted([k for k, v in self.ports.items()
                               if "output" in str(v.get("role", "")) or v.get("direction") == "output"])
        self.kinds = sorted({x.get("kind") for x in self.devs})
        # net index
        self.gate_of = defaultdict(list)
        self.drain_of = defaultdict(list)
        self.source_of = defaultdict(list)
        for x in self.devs:
            self.gate_of[x["gate"]].append(x)
            self.drain_of[x["drain"]].append(x)
            self.source_of[x["source"]].append(x)
        self.pas_nets = set()
        for p in self.pas:
            self.pas_nets.update(p["terminals"])
        self.isrc_nets = set()
        for s in self.isrc:
            self.isrc_nets.update(s["terminals"])
        self.all_nets = set()
        for x in self.devs:
            self.all_nets.update([x["gate"], x["drain"], x["source"]])
        self.all_nets |= self.pas_nets | self.isrc_nets | set(self.ports)

    def dn(self, x):
        return x["name"]


# ---------------------------------------------------------------- rule 1
def base_acground(c):
    """N3.2-1 (1)(2)(3). (4) added later by fixpoint."""
    ag = set(c.rails)
    for n in sorted(c.gate_of):
        if n in c.rails:
            continue
        driven = bool(c.drain_of.get(n) or c.source_of.get(n))
        if driven:
            continue
        if n in c.pas_nets or n in c.isrc_nets or n in c.ports:
            continue
        ag.add(n)
    return ag


def signal_nets(c, excit, ag, removed=frozenset(), block_chan=frozenset()):
    """N3.2-3 minimal fixed point. block_chan = device names whose channel (s->d) edge is cut."""
    S = set(n for n in excit if n not in ag and n not in removed)
    ch = True
    while ch:
        ch = False
        for x in c.devs:
            if x["gate"] in S:
                for t in (x["drain"], x["source"]):
                    if t not in S and t not in ag and t not in removed:
                        S.add(t); ch = True
            if x["source"] in S and x["name"] not in block_chan:
                t = x["drain"]
                if t not in S and t not in ag and t not in removed:
                    S.add(t); ch = True
        for p in c.pas:
            a, b = p["terminals"][0], p["terminals"][1]
            for u, v in ((a, b), (b, a)):
                if u in S and v not in S and v not in ag and v not in removed:
                    S.add(v); ch = True
    return S


def chan_component(c, start, blocked):
    """nodes reachable from `start` over channel-only edges (MOS d-s, resistors)."""
    seen = {start}
    q = deque([start])
    while q:
        n = q.popleft()
        for x in c.devs:
            if x["drain"] == n and x["source"] not in seen and x["source"] not in blocked:
                seen.add(x["source"]); q.append(x["source"])
            if x["source"] == n and x["drain"] not in seen and x["drain"] not in blocked:
                seen.add(x["drain"]); q.append(x["drain"])
        for p in c.pas:
            if p.get("kind") != "resistor":
                continue
            a, b = p["terminals"][0], p["terminals"][1]
            for u, v in ((a, b), (b, a)):
                if u == n and v not in seen and v not in blocked:
                    seen.add(v); q.append(v)
    return seen


BLOCK_RAILS_IN_CHAIN = True
CGPASS_MODE = "literal"   # "literal" | "bundle-only"   # reading B of rule 1 (4)(iii); see report


def bias_dependent_nets(c, excit, ag):
    """N3.2-1 (4) predicate (0)(i)(ii)(iii). Returns (set, evidence)."""
    S = signal_nets(c, excit, ag)
    found, ev = set(), []
    for b in sorted(S):
        if b in excit:
            continue
        # (0) already: b in S
        # (i) signal leaves b only by gate
        if not c.gate_of.get(b):
            continue
        if c.source_of.get(b):
            continue
        if b in c.pas_nets or b in c.isrc_nets:
            continue
        # (ii) every channel terminal driving b is (A) self-gate-read, or (B) gate outside signal path
        drivers = c.drain_of.get(b, [])
        if not drivers:
            continue
        clsA, ok = [], True
        for x in drivers:
            if x["gate"] == b:
                clsA.append(x)
            elif x["gate"] not in S:
                pass
            else:
                ok = False; break
        if not ok or not clsA:
            continue
        # (iii) one of clsA sits on a channel-only chain starting at a signal node that
        #       is still a signal node with b removed
        S_wo = signal_nets(c, excit, ag | {b})
        hit = None
        blocked = {b} | (set(ag) if BLOCK_RAILS_IN_CHAIN else set())
        for x in clsA:
            if x["source"] in blocked:      # reading C: the chain may not start on ac-ground
                continue
            comp = chan_component(c, x["source"], blocked)
            cand = sorted((comp & S) & S_wo)
            if cand:
                hit = (x["name"], cand[:4]); break
        if hit:
            found.add(b)
            ev.append((b, sorted(d["name"] for d in drivers), hit))
    return found, ev


def acground_fixpoint(c, excit):
    ag = base_acground(c)
    ev_all = []
    for _ in range(6):
        add, ev = bias_dependent_nets(c, excit, ag)
        new = add - ag
        if not new:
            break
        ag |= new
        ev_all += ev
    return ag, ev_all


# ---------------------------------------------------------------- views
def default_views(c):
    """N3.2-2 basic transfer view. Returns list of (label, excitation nets)."""
    if len(c.inputs) >= 2:
        return [("diff(nonreduced)", set(c.inputs))]
    if len(c.inputs) == 1:
        return [("single", set(c.inputs))]
    return []


# ---------------------------------------------------------------- rule 3 cells
def classify_cells(c, excit, ag):
    S = signal_nets(c, excit, ag)
    cells = {}
    notes = {}
    # antiparallel pass bundle candidates (rule 3 last clause)
    bundles = []
    bykey = defaultdict(list)
    for x in c.devs:
        if x["gate"] in S:
            continue
        bykey[frozenset((x["drain"], x["source"]))].append(x)
    for k, lst in bykey.items():
        if len(lst) == 2 and len(k) == 2:
            a, b = lst
            if a["drain"] == b["source"] and a["source"] == b["drain"]:
                bundles.append((a["name"], b["name"], tuple(sorted(k))))
        elif len(lst) >= 3 and len(k) == 2:
            notes[("multi", tuple(sorted(k)))] = [d["name"] for d in lst]
    bundled = set()
    for a, b, _ in bundles:
        bundled |= {a, b}

    # input-terminal set (determinable without full classification):
    #   gate in S  -> input terminal is the gate net
    #   gate not in S and source in S -> input terminal is the source net
    in_terms = defaultdict(set)
    for x in c.devs:
        if x["gate"] in S:
            in_terms[x["gate"]].add(x["name"])
        elif x["source"] in S:
            in_terms[x["source"]].add(x["name"])

    for x in c.devs:
        n = x["name"]
        if x["gate"] in S:
            if x["drain"] in ag:
                cells[n] = "CD"
            elif x["source"] in ag:
                cells[n] = "CS"
            else:
                sn = x["source"]
                touch = bool(in_terms.get(sn, set()) - {n}) or sn in c.outputs
                cells[n] = "REVIEW_CS_CD" if touch else "CS(degen)"
        else:
            # gate outside this view's signal path: CG / pass / load
            if x["source"] not in S:
                # no signal enters through the channel -> AC role 'load' (rule 3 load)
                cells[n] = "load" if x["drain"] in S else "offpath"
                continue
            if n in bundled:
                cells[n] = "pass(bundle)"
                continue
            if CGPASS_MODE == "bundle-only":
                cells[n] = "CG"          # counter-factual: only the antiparallel bundle makes 'pass'
                continue
            S_cut = signal_nets(c, excit, ag, block_chan={n})
            d_ok = x["drain"] in S_cut
            cells[n] = "pass" if d_ok else "CG"
    return S, cells, bundles, notes


def forward_nets(c, excit, ag, S):
    """forward path = reachable from excitation AND reverse-reachable to an output port."""
    adj = defaultdict(set)
    for x in c.devs:
        if x["gate"] in S:
            for t in (x["drain"], x["source"]):
                if t in S:
                    adj[x["gate"]].add(t)
        if x["source"] in S and x["drain"] in S:
            adj[x["source"]].add(x["drain"])
    for p in c.pas:
        a, b = p["terminals"][0], p["terminals"][1]
        if a in S and b in S:
            adj[a].add(b); adj[b].add(a)
    radj = defaultdict(set)
    for u, vs in adj.items():
        for v in vs:
            radj[v].add(u)
    out = set(n for n in c.outputs if n in S)
    seen = set(out); q = deque(out)
    while q:
        n = q.popleft()
        for u in radj.get(n, ()):
            if u not in seen:
                seen.add(u); q.append(u)
    return S & seen, adj


def cell_out_net(x, kind):
    if kind.startswith("CS") or kind == "CG":
        return x["drain"]
    if kind == "CD":
        return x["source"]
    return None


# ---------------------------------------------------------------- driving type
def driving_types(c, excit, ag, S, cells):
    """glossary '입력 노드 구동 종류' incl. priority rule."""
    res = {}
    for n in sorted(S):
        # signal enters via the DRAIN of a SIGNAL cell (loads/off-path devices are not entries)
        cur_in = [x["name"] for x in c.drain_of.get(n, [])
                  if cells.get(x["name"], "offpath") in
                  ("CS", "CS(degen)", "CG", "pass", "pass(bundle)", "REVIEW_CS_CD")]
        volt_in = []
        if n in excit:
            volt_in.append("port")
        for x in c.source_of.get(n, []):
            if cells.get(x["name"]) == "CD":
                volt_in.append(x["name"])
        res_in = [p["name"] for p in c.pas
                  if p.get("kind") == "resistor" and n in p["terminals"]]
        out_gate = [x["name"] for x in c.gate_of.get(n, []) if cells.get(x["name"], "").startswith(("CS", "CD"))]
        out_chan = [x["name"] for x in c.source_of.get(n, []) if cells.get(x["name"]) in ("CG", "pass", "pass(bundle)")]
        if cur_in and (out_gate or out_chan):
            if out_gate and not out_chan:
                t = "voltage(priority:gate-only)"
            elif out_chan and not out_gate:
                t = "current(priority:chan-only)"
            else:
                t = "TAP->rule9(a)"
        elif cur_in:
            t = "current"
        elif volt_in:
            t = "voltage"
        elif res_in:
            t = "value-dep(inherit)"
        else:
            t = "undetermined"
        res[n] = dict(t=t, cur_in=cur_in, volt_in=volt_in, res_in=res_in,
                      out_gate=out_gate, out_chan=out_chan)
    return res


# ---------------------------------------------------------------- rule 9 record-only branches
def record_only_branches(c, excit, ag, S, cells, dtypes, bundles, notes):
    hits = defaultdict(list)
    # (a) CS whose gate sits on a current-driven (TAP) node
    for x in c.devs:
        k = cells.get(x["name"], "")
        if k.startswith("CS"):
            g = dtypes.get(x["gate"])
            if g and g["t"] == "TAP->rule9(a)":
                hits["9a_CS_on_tap"].append(x["name"])
    # (b) CG fed by a current-input port  -- ports declare voltage by default => 0
    # (c) CS-started block whose output node impedance class is low
    for x in c.devs:
        k = cells.get(x["name"], "")
        if k.startswith("CS"):
            dn = x["drain"]
            low = any(y["source"] == dn and y["gate"] in ag for y in c.devs) or \
                  any(y["drain"] == dn and y["gate"] == dn for y in c.devs)
            if low:
                hits["9c_CS_low_Z_out"].append(x["name"] + "@" + dn)
    for k, v in cells.items():
        if v == "REVIEW_CS_CD":
            hits["cell_CS_CD_dual"].append(k)
    for key, v in notes.items():
        if key[0] == "multi":
            hits["ge3_devices_same_nodepair"].append(str(key[1]) + ":" + ",".join(v))
    if any(k not in ("nmos", "pmos") for k in c.kinds):
        hits["non_mos_kind"].append(",".join(c.kinds))
    return hits


# ---------------------------------------------------------------- loops (rule 2)
def loop_graph(c, excit, ag, S, cells, dtypes, bundles):
    """directed signal graph for loop detection; excitation nets and ac-ground removed."""
    removed = set(ag) | set(excit)
    nodes = set(n for n in c.all_nets if n not in removed)
    edges = defaultdict(set)     # u -> {(v, tag)}
    for x in c.devs:
        g, d, s = x["gate"], x["drain"], x["source"]
        if g in nodes:
            for t in (d, s):
                if t in nodes:
                    edges[g].add((t, "act:" + x["name"]))
        # source->drain only when source node is a current-driven node
        if s in nodes and d in nodes:
            dt = dtypes.get(s, {}).get("t", "")
            if dt.startswith("current") or dt == "TAP->rule9(a)":
                edges[s].add((d, "act:" + x["name"]))
    # pass bundle: one merged 2-terminal signal path, traversable once each direction
    for a, b, k in bundles:
        u, v = k
        if u in nodes and v in nodes:
            edges[u].add((v, "bundle:" + a + "/" + b))
            edges[v].add((u, "bundle:" + a + "/" + b))
    for p in c.pas:
        a, b = p["terminals"][0], p["terminals"][1]
        if a in nodes and b in nodes:
            edges[a].add((b, "pas:" + p["name"]))
            edges[b].add((a, "pas:" + p["name"]))
    return nodes, edges


def simple_cycles(nodes, edges, cap=200000):
    """all simple cycles (node-simple), each reported once by smallest-start canonical form.
    Round-trip over the SAME 2-terminal passive / same bundle is excluded (N3.2-2)."""
    order = {n: i for i, n in enumerate(sorted(nodes))}
    out = []
    cnt = [0]

    def dfs(start, u, path, ptags, onpath):
        for (v, tag) in sorted(edges.get(u, ())):
            if order[v] < order[start]:
                continue
            if v == start:
                if len(path) == 2 and ptags and ptags[-1] == tag:
                    continue  # 2-node round trip over same element
                out.append((list(path), list(ptags) + [tag]))
                cnt[0] += 1
                if cnt[0] > cap:
                    return True
                continue
            if v in onpath:
                continue
            if ptags and ptags[-1] == tag and len(path) >= 1:
                # immediate back-and-forth over the same element
                continue
            path.append(v); ptags.append(tag); onpath.add(v)
            stop = dfs(start, v, path, ptags, onpath)
            path.pop(); ptags.pop(); onpath.discard(v)
            if stop:
                return True
        return False

    for s in sorted(nodes, key=lambda n: order[n]):
        if dfs(s, s, [s], [], {s}):
            break
    return out


def bfs01_dist(c, excit, ag, S, cells, dtypes, pas_cost=1):
    """rule 4: 0-1 BFS from view input. gate->drain 1, s->d(cascode)/gate->source 0,
    gate net = diode node -> gate->drain 0; voltage-driven CG s->d = 1."""
    diode_nets = set()
    for x in c.devs:
        if x["gate"] == x["drain"]:
            diode_nets.add(x["gate"])
    adj = defaultdict(list)
    for x in c.devs:
        g, d, s = x["gate"], x["drain"], x["source"]
        k = cells.get(x["name"], "offpath")
        if k == "offpath":
            continue
        if k.startswith("CS") or k == "CD" or k == "REVIEW_CS_CD":
            adj[g].append((d, 0 if g in diode_nets else 1))
            adj[g].append((s, 0))
        if k in ("CG", "pass", "pass(bundle)"):
            dt = dtypes.get(s, {}).get("t", "")
            cost = 1 if dt.startswith("voltage") else 0
            adj[s].append((d, cost))
            if k.startswith("pass"):
                adj[d].append((s, cost))
    for p in c.pas:
        a, b = p["terminals"][0], p["terminals"][1]
        adj[a].append((b, pas_cost)); adj[b].append((a, pas_cost))
    dist = {}
    dq = deque()
    for n in sorted(excit):
        dist[n] = 0; dq.append(n)
    while dq:
        u = dq.popleft()
        for v, w in adj.get(u, ()):
            nd = dist[u] + w
            if v not in dist or nd < dist[v]:
                dist[v] = nd
                (dq.appendleft if w == 0 else dq.append)(v)
    return dist


def classify_loops(c, excit, ag, S, cells, dtypes, bundles, fwd, pas_cost=1):
    nodes, edges = loop_graph(c, excit, ag, S, cells, dtypes, bundles)
    cyc = simple_cycles(nodes, edges)
    dist = bfs01_dist(c, excit, ag, S, cells, dtypes, pas_cost=pas_cost)
    res = defaultdict(list)
    for path, tags in cyc:
        # (1.5) bias SCC : no node of the transfer-view signal path
        if not any(n in S for n in path):
            res["1.5_bias_scc"].append((path, tags)); continue
        # return path (rule 7): edges whose BFS distance does not decrease
        rev = []
        L = len(path)
        for i, tag in enumerate(tags):
            u = path[i]; v = path[(i + 1) % L]
            du, dv = dist.get(u), dist.get(v)
            if du is None or dv is None:
                rev.append((i, tag, "unknown")); continue
            if dv <= du:
                rev.append((i, tag, "rev"))
        revtags = [t for (_, t, m) in rev if m == "rev"]
        act_rev = [t for t in revtags if t.startswith("act:") or t.startswith("bundle:")]
        pas_rev = [t for t in revtags if t.startswith("pas:")]
        has_cap_rev = any(t.startswith("pas:") and _is_cap(c, t[4:]) for t in revtags)
        # (2) Miller: return path passives only, containing a capacitor, back to fwd node
        if revtags and not act_rev and has_cap_rev:
            res["2_miller"].append((path, tags)); continue
        # (3-a) contains an active cell not on any transfer-view forward path
        act_names = [t.split(":", 1)[1] for t in tags if t.startswith("act:")]
        offfwd = [a for a in act_names
                  if cell_out_net(_dev(c, a), cells.get(a, "")) not in fwd]
        if offfwd:
            res["3a"].append((path, tags)); continue
        # (3-b) return path has >=1 active cell ; exclusions
        if act_rev:
            if not pas_rev and len(set(a.split(":", 1)[1] for a in act_rev)) == 2:
                res["record_2active_no_passive"].append((path, tags)); continue
            res["3b"].append((path, tags)); continue
        if revtags and not act_rev:
            res["4"].append((path, tags)); continue
        res["4"].append((path, tags))
    return res, len(cyc)


def _dev(c, name):
    for x in c.devs:
        if x["name"] == name:
            return x
    return {"drain": None, "source": None}


def _is_cap(c, pname):
    for p in c.pas:
        if p["name"] == pname:
            return p.get("kind") == "capacitor"
    return False


# ---------------------------------------------------------------- DEC-60 (iii)
def hidden_rail_check(c):
    """DC conduction graph BEFORE leaf pruning: MOS channel, resistors, ideal sources.
    Nets that never appear as a transistor terminal, appear only at passive/ideal-source
    terminals, and are not DC-connected to any rail net => rail candidates."""
    adj = defaultdict(set)
    for x in c.devs:
        adj[x["drain"]].add(x["source"]); adj[x["source"]].add(x["drain"])
    for p in c.pas:
        if p.get("kind") in ("resistor", "inductor"):
            a, b = p["terminals"][0], p["terminals"][1]
            adj[a].add(b); adj[b].add(a)
    for s in c.isrc:
        a, b = s["terminals"][0], s["terminals"][1]
        adj[a].add(b); adj[b].add(a)
    tnets = set()
    for x in c.devs:
        tnets.update([x["gate"], x["drain"], x["source"]])
    seen = set(c.rails); q = deque(c.rails)
    while q:
        n = q.popleft()
        for m in adj.get(n, ()):
            if m not in seen:
                seen.add(m); q.append(m)
    cands = []
    for n in sorted(c.all_nets):
        if n in tnets or n in c.rails:
            continue
        if n in seen:
            continue
        cands.append(n)
    missing = [n for n in cands if n not in c.rails]
    return cands, missing


# ---------------------------------------------------------------- DEC-71 columns
def dc_graph(c, prune=True):
    edges = []   # (u, v, label)
    for x in c.devs:
        edges.append((x["drain"], x["source"], "M:" + x["name"]))
    for p in c.pas:
        if p.get("kind") == "resistor":
            edges.append((p["terminals"][0], p["terminals"][1], "R:" + p["name"]))
    for s in c.isrc:
        edges.append((s["terminals"][0], s["terminals"][1], "I:" + s["name"]))
    if prune:
        changed = True
        while changed:
            changed = False
            deg = defaultdict(list)
            for i, (u, v, l) in enumerate(edges):
                deg[u].append(i); deg[v].append(i)
            for n, idxs in list(deg.items()):
                if n in c.rails or n in c.ports:
                    continue
                if len(idxs) == 1 and edges[idxs[0]][2].startswith("R:"):
                    edges.pop(idxs[0]); changed = True; break
    return edges


def branches_and_columns(c, cap=400000):
    edges = dc_graph(c, prune=True)
    deg = defaultdict(int)
    inc = defaultdict(list)
    for i, (u, v, l) in enumerate(edges):
        deg[u] += 1; deg[v] += 1
        inc[u].append(i); inc[v].append(i)
    branch_nodes = set(c.rails) | {n for n in deg if deg[n] >= 3}
    # branches = maximal series chains between branch nodes
    used = set()
    branches = []
    for n in sorted(branch_nodes):
        for i in inc[n]:
            if i in used:
                continue
            u, v, l = edges[i]
            cur = v if u == n else u
            chain = [i]; used.add(i); prev = n
            while cur not in branch_nodes and deg[cur] == 2:
                nxt = [j for j in inc[cur] if j not in used]
                if not nxt:
                    break
                j = nxt[0]; used.add(j); chain.append(j)
                a, b, _ = edges[j]
                nxtnode = b if a == cur else a
                prev, cur = cur, nxtnode
            branches.append((n, cur, chain))
    # node-simple paths between distinct rail nets over the branch graph
    badj = defaultdict(list)
    for bi, (a, b, ch) in enumerate(branches):
        badj[a].append((b, bi)); badj[b].append((a, bi))
    rails = sorted(c.rails)
    cols = []
    stop = [False]

    def walk(cur, target, visited, path):
        if stop[0]:
            return
        for (nxt, bi) in badj.get(cur, ()):
            if bi in path:
                continue
            if nxt == target:
                cols.append(path + [bi])
                if len(cols) > cap:
                    stop[0] = True
                    return
                continue
            if nxt in visited:
                continue
            walk(nxt, target, visited | {nxt}, path + [bi])

    for i in range(len(rails)):
        for j in range(i + 1, len(rails)):
            walk(rails[i], rails[j], {rails[i]}, [])
    nonrail_branch_nodes = sorted(n for n in deg if deg[n] >= 3 and n not in c.rails)
    return branches, cols, nonrail_branch_nodes


# ---------------------------------------------------------------- run
def run(name):
    c = C(name)
    emit("=" * 90)
    emit("CIRCUIT %s  devs=%d pas=%d isrc=%d rails=%s in=%s out=%s kinds=%s"
         % (name, len(c.devs), len(c.pas), len(c.isrc), sorted(c.rails), c.inputs, c.outputs, c.kinds))
    views = default_views(c)
    if not views:
        emit("  !! no default transfer view (no input port)")
        return
    hr_c, hr_m = hidden_rail_check(c)
    emit("  DEC-60(iii) hidden-rail candidates=%s  not-in-supply_nets(=REJECT)=%s" % (hr_c, hr_m))
    br, cols, bn = branches_and_columns(c)
    emit("  DEC-71: branches=%d  non-rail branch-nodes=%d  columns(node-simple)=%d"
         % (len(br), len(bn), len(cols)))
    for label, excit in views:
        ag, ev = acground_fixpoint(c, excit)
        S, cells, bundles, notes = classify_cells(c, excit, ag)
        fwd, adj = forward_nets(c, excit, ag, S)
        dt = driving_types(c, excit, ag, S, cells)
        emit("  VIEW %s excit=%s" % (label, sorted(excit)))
        emit("    acground(|%d|)=%s" % (len(ag), sorted(ag)))
        emit("    rule1(4) bias-dependent nets = %s" % ([e[0] for e in ev] or "none"))
        for e in ev:
            emit("       evid %s driven_by=%s chain_dev=%s start_signal_nodes=%s" % (e[0], e[1], e[2][0], e[2][1]))
        emit("    signal nets(%d)=%s" % (len(S), sorted(S)))
        emit("    forward nets(%d)=%s" % (len(fwd), sorted(fwd)))
        byk = defaultdict(list)
        for n, k in sorted(cells.items()):
            byk[k].append(n)
        for k in sorted(byk):
            emit("    cells %-14s (%2d) %s" % (k, len(byk[k]), byk[k]))
        # forward-restricted counts
        fw_cells = defaultdict(list)
        for n, k in sorted(cells.items()):
            if k == "offpath":
                continue
            o = cell_out_net(_dev(c, n), k)
            if k.startswith("pass"):
                x = _dev(c, n)
                inf = (x["drain"] in fwd) or (x["source"] in fwd)
            else:
                inf = o in fwd
            if inf:
                fw_cells[k].append(n)
        emit("    FORWARD-restricted: " + "  ".join("%s=%d%s" % (k, len(v), v) for k, v in sorted(fw_cells.items())))
        emit("    pass bundles = %s" % (bundles or "none"))
        # stages
        starts = [n for n, k in cells.items() if k.startswith("CS")] + \
                 [n for n, k in cells.items() if k == "CG" and dt.get(_dev(c, n)["source"], {}).get("t", "").startswith("voltage")]
        emit("    stage-start cells (rule5) = %s" % sorted(starts))
        vcg = [n for n, k in cells.items() if k == "CG" and dt.get(_dev(c, n)["source"], {}).get("t", "").startswith("voltage")]
        emit("    voltage-driven CG (branch) = %s" % sorted(vcg))
        ro = record_only_branches(c, excit, ag, S, cells, dt, bundles, notes)
        emit("    RECORD-ONLY branch hits = %s" % (dict(ro) or "none"))
        for pc in (0, 1):
            loops, tot = classify_loops(c, excit, ag, S, cells, dt, bundles, fwd, pas_cost=pc)
            summ = {k: len(v) for k, v in sorted(loops.items())}
            emit("    LOOPS (pas_cost=%d) total simple cycles=%d -> %s" % (pc, tot, summ))
            if loops.get("4"):
                for p, t in loops["4"][:6]:
                    emit("       (4): %s | %s" % (p, t))
            if loops.get("record_2active_no_passive"):
                for p, t in loops["record_2active_no_passive"][:4]:
                    emit("       rec2act: %s | %s" % (p, t))
        # driving types of interest
        emit("    driving types (signal nets): " +
             "; ".join("%s=%s" % (n, dt[n]["t"]) for n in sorted(S)))
        taps = [n for n in S if dt[n]["t"] == "TAP->rule9(a)"]
        emit("    TAP nodes (rule9a trigger) = %s" % taps)


if __name__ == "__main__":
    if os.path.exists(OUT):
        os.remove(OUT)
    sys.stdout.reconfigure(encoding="utf-8")
    sys.setrecursionlimit(20000)
    for n in CIRCUITS:
        try:
            run(n)
        except Exception as e:
            import traceback
            emit("  !! EXCEPTION in %s: %r" % (n, e))
            emit(traceback.format_exc())
    emit("DONE")
