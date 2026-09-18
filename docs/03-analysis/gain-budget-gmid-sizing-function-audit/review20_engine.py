# -*- coding: utf-8 -*-
"""fresh3 independent dry-run engine.  Written from plan text only (N0.4, N3.2, N3.7, DEC-59/60/63/64/70/71/76/81).
Does NOT import any repo code.  Every ambiguity is parameterised by an option dict `opt` so both readings
can be measured.  Results are appended per circuit to results_*.jsonl."""
import json, glob, os, sys, itertools, collections
import networkx as nx

LIB = r"C:\Users\HSLEE\Documents\Todoc\fpga\chip-design-skills\skills\analog-gmid-design\assets\library"
SP = os.path.dirname(os.path.abspath(__file__))


# ----------------------------------------------------------------------------- load
def load(path):
    d = json.load(open(path, encoding="utf-8"))
    devs = [dict(name=m["name"], kind=m["kind"], d=m["drain"], g=m["gate"], s=m["source"]) for m in d["netlist"]]
    pas = []
    for p in (d.get("passive_elements") or []):
        a, b = p["terminals"]
        pas.append(dict(name=p["name"], kind="R" if p["kind"] == "resistor" else "C", a=a, b=b,
                        value=p.get("value_ohm", p.get("value_farad"))))
    isrc = []
    vsrc = []
    for s in (d.get("ideal_sources") or []):
        a, b = s["terminals"]
        (isrc if s["kind"] == "current_source" else vsrc).append(dict(name=s["name"], a=a, b=b, value=s.get("value_amp")))
    ports = {k: v for k, v in (d.get("ports") or {}).items() if not k.startswith("_")}
    ins = sorted(k for k, v in ports.items() if v.get("direction") == "input")
    outs = sorted(k for k, v in ports.items() if v.get("direction") == "output")
    sr = d.get("sizing_roles")
    return dict(name=os.path.basename(path).replace(".topology.json", ""), raw=d, devs=devs, pas=pas, isrc=isrc,
                vsrc=vsrc, rails=list(d.get("supply_nets") or []), supply_nets_declared="supply_nets" in d,
                ports=ports, ins=ins, outs=outs, sizing_roles=sr)


def all_nets(c):
    n = set()
    for m in c["devs"]:
        n |= {m["d"], m["g"], m["s"]}
    for p in c["pas"] + c["isrc"] + c["vsrc"]:
        n |= {p["a"], p["b"]}
    return n


# ----------------------------------------------------------------------------- symmetry (own impl)
def symmetry_map(c):
    """seed: differential input pair (+ differential output pair), rails self.  Unique-candidate propagation."""
    ins = c["ins"]
    seed = {r: r for r in c["rails"]}
    roles = {v.get("role"): k for k, v in c["ports"].items()}
    ok_pair = False
    if "differential_input_p" in roles and "differential_input_n" in roles:
        p, n = roles["differential_input_p"], roles["differential_input_n"]
        seed[p] = n; seed[n] = p; ok_pair = True
    if "differential_output_p" in roles and "differential_output_n" in roles:
        p, n = roles["differential_output_p"], roles["differential_output_n"]
        seed[p] = n; seed[n] = p
    if not ok_pair:
        return None, {}
    net = dict(seed); dm = {}
    changed = True
    while changed:
        changed = False
        pend = []
        for t in c["devs"]:
            if t["name"] in dm: continue
            known = {a: net[t[a]] for a in ("s", "d", "g") if t[a] in net}
            if known: pend.append((t, known))
        pend.sort(key=lambda x: (-len(x[1]), x[0]["name"]))
        for t, known in pend:
            if t["name"] in dm: continue
            cand = [u for u in c["devs"] if u["kind"] == t["kind"] and u["name"] not in dm and all(u[a] == v for a, v in known.items())]
            if len(cand) != 1: continue
            u = cand[0]; dm[t["name"]] = u["name"]; dm[u["name"]] = t["name"]; changed = True
            for a in ("s", "d", "g"):
                if t[a] not in net:
                    net[t[a]] = u[a]; net.setdefault(u[a], t[a])
    # confirmed = the two input-port gate devices map to each other
    return net, dm


# ----------------------------------------------------------------------------- AC ground base
def base_acg(c):
    nets = all_nets(c)
    gate_only = set()
    chan = {m[x] for m in c["devs"] for x in ("d", "s")}
    pas_t = {p[x] for p in c["pas"] for x in ("a", "b")}
    src_t = {p[x] for p in c["isrc"] + c["vsrc"] for x in ("a", "b")}
    for n in nets:
        if n in chan or n in pas_t or n in src_t or n in c["ports"]:
            continue
        gate_only.add(n)
    vs = {p[x] for p in c["vsrc"] for x in ("a", "b")}
    return set(c["rails"]) | gate_only | vs, gate_only


def reach(c, acg, excite):
    R = set(n for n in excite if n not in acg)
    changed = True
    while changed:
        changed = False
        for m in c["devs"]:
            new = []
            if m["g"] in R: new += [m["d"], m["s"]]
            if m["s"] in R: new += [m["d"]]
            for n in new:
                if n not in acg and n not in R: R.add(n); changed = True
        for p in c["pas"]:
            for x, y in ((p["a"], p["b"]), (p["b"], p["a"])):
                if x in R and y not in acg and y not in R: R.add(y); changed = True
    return R


def reach_graph_edges(c, R):
    E = []
    for m in c["devs"]:
        if m["g"] in R:
            for t in (m["d"], m["s"]):
                if t in R and t != m["g"]: E.append((m["g"], t))
        if m["s"] in R and m["d"] in R: E.append((m["s"], m["d"]))
    for p in c["pas"]:
        if p["a"] in R and p["b"] in R: E += [(p["a"], p["b"]), (p["b"], p["a"])]
    return E


def forward_set(c, R, outs):
    G = nx.DiGraph(); G.add_nodes_from(R); G.add_edges_from(reach_graph_edges(c, R))
    F = set()
    for o in outs:
        if o in G: F |= nx.ancestors(G, o) | {o}
    return F & R


# ----------------------------------------------------------------------------- rule 1 (4)
def bias_dependent_nets(c, acg0, excite, net_sym, opt):
    R0 = reach(c, acg0, excite)
    out = []
    for b in sorted(R0):
        if b in excite: continue
        # (i) signal leaves b only through gate: no MOS has source==b (s->d propagation) ; passive at b -> fail (strict)
        if any(m["s"] == b for m in c["devs"]): continue
        if any(b in (p["a"], p["b"]) for p in c["pas"]): continue
        # (ii) drivers
        drivers = [m for m in c["devs"] if m["d"] == b or m["s"] == b]
        self_cls, bias_cls, bad = [], [], []
        for m in drivers:
            if m["g"] == b: self_cls.append(m)
            elif m["g"] not in R0: bias_cls.append(m)
            else: bad.append(m)
        if bad or not self_cls: continue
        # (iii) chain from a self-class device, drain->source backward, not through acg, not revisiting b
        acg_b = acg0 | {b}
        Rb = reach(c, acg_b, excite)
        start = None
        for m in self_cls:
            # walk: from device m (channel at b) go to its other channel terminal, then devices whose drain is that net ...
            frontier = [m["s"] if m["d"] == b else m["d"]]
            seen = set()
            while frontier and start is None:
                n = frontier.pop(0)
                if n in seen or n == b or n in acg0: continue
                seen.add(n)
                if n in Rb:
                    start = (m["name"], n); break
                for u in c["devs"]:
                    if u["d"] == n and u["s"] not in seen: frontier.append(u["s"])
            if start: break
        if not start: continue
        moves = True
        if net_sym is not None and net_sym.get(start[1]) == start[1]:
            moves = False
        out.append(dict(net=b, chain_dev=start[0], start_node=start[1], moves_in_view=moves))
    return out


# ----------------------------------------------------------------------------- DC roles
def dc_roles(c, acg_all_views, opt):
    role = {}
    grp_review = []
    for m in c["devs"]:
        if m["g"] == m["d"]: role[m["name"]] = "diode"
    groups = collections.defaultdict(list)
    for m in c["devs"]:
        groups[(m["g"], m["s"])].append(m)
    for (g, s), mem in groups.items():
        if len(mem) < 2: continue
        has_diode = any(x["g"] == x["d"] for x in mem)
        if has_diode or g in acg_all_views:
            for x in mem:
                if x["name"] not in role: role[x["name"]] = "bias"
        else:
            names = [x["name"] for x in mem if x["name"] not in role]
            if names:
                grp_review.append(dict(gate=g, source=s, members=names))
                for n in names: role[n] = opt.get("unresolved_as", "unresolved")
    for m in c["devs"]:
        if m["name"] in role: continue
        if m["g"] in acg_all_views and m["s"] in c["rails"]:
            role[m["name"]] = "bias"
    # (4) inheritance: equal_vgs / matching_ratio / kcl_group -- look for these keys in device_roles
    inh = []
    dr = c["raw"].get("device_roles") or {}
    for dev, v in (dr.items() if isinstance(dr, dict) else []):
        if isinstance(v, dict) and any(k in v for k in ("equal_vgs", "matching_ratio", "kcl_group")):
            inh.append(dev)
    if opt.get("inherit_from_matching_pairs"):
        for mp in (c["raw"].get("symmetry") or {}).get("matching_pairs") or []:
            names = mp.get("names") or []
            rs = {role.get(n) for n in names if role.get(n) in ("bias",)}
            if rs and mp.get("current_forced"):
                for n in names:
                    if n not in role or role[n] not in ("diode",):
                        if role.get(n) != "bias": inh.append(n)
                        role[n] = "bias"
    for m in c["devs"]:
        if m["name"] not in role: role[m["name"]] = "signal"
    return role, grp_review, inh


# ----------------------------------------------------------------------------- cells
def classify_cells(c, R, acg, F, excite):
    cell = {}
    names = {m["name"]: m for m in c["devs"]}
    # pass bundles
    bundles = []
    used = set()
    for a, b in itertools.combinations(c["devs"], 2):
        if a["g"] in R or b["g"] in R: continue
        if a["g"] == a["d"] or b["g"] == b["d"]: continue
        if {a["d"], a["s"]} == {b["d"], b["s"]} and a["d"] == b["s"] and a["d"] != a["s"]:
            if a["d"] in R or a["s"] in R:
                bundles.append((a["name"], b["name"], tuple(sorted((a["d"], a["s"])))))
                used |= {a["name"], b["name"]}
    # >=3 devices between same node pair with gates outside -> review
    pair_cnt = collections.defaultdict(list)
    for m in c["devs"]:
        if m["g"] not in R and m["g"] != m["d"] and (m["d"] in R or m["s"] in R):
            pair_cnt[tuple(sorted((m["d"], m["s"])))].append(m["name"])
    pass3 = [v for v in pair_cnt.values() if len(v) >= 3]
    for m in c["devs"]:
        n = m["name"]
        if m["g"] == m["d"]:
            cell[n] = dict(type="diode", inp=None, out=m["d"]); continue
        if m["g"] in R:
            if m["d"] in acg: cell[n] = dict(type="CD", inp=m["g"], out=m["s"])
            elif m["s"] in acg: cell[n] = dict(type="CS", inp=m["g"], out=m["d"])
            else: cell[n] = dict(type="CS", inp=m["g"], out=m["d"], degen=True)
            continue
        if n in used:
            cell[n] = dict(type="pass", inp=None, out=None); continue
        if m["s"] in R:
            cell[n] = dict(type="CG", inp=m["s"], out=m["d"]); continue
        if m["d"] in R:
            cell[n] = dict(type="load", inp=None, out=None); continue
        cell[n] = dict(type="off", inp=None, out=None)
    # dual-output check for degenerated CS (forward restriction, ambiguous->ambiguous stops)
    def fwd_out(x):
        t = cell[x]
        if t["type"] == "pass":
            return any(bn for bn in bundles if x in bn[:2] and (bn[2][0] in F or bn[2][1] in F))
        return t.get("out") in F
    dual = []
    for m in c["devs"]:
        t = cell[m["name"]]
        if t["type"] == "CS" and t.get("degen"):
            s = m["s"]
            touch = []
            for u in c["devs"]:
                if u["name"] == m["name"]: continue
                tu = cell[u["name"]]
                if tu["type"] in ("CS", "CD") and u["g"] == s and fwd_out(u["name"]): touch.append(u["name"])
                if tu["type"] == "CG" and u["s"] == s and fwd_out(u["name"]): touch.append(u["name"])
            if s in c["outs"]: touch.append("<out_port>")
            if touch:
                dual.append((m["name"], touch))
    for n, t in dual:
        cell[n]["type"] = "CSCD_review"; cell[n]["touch"] = t
    return cell, bundles, pass3


# ----------------------------------------------------------------------------- drive kinds
def drive_kinds(c, R, acg, F, cell, bundles, role, excite, opt):
    dev = {m["name"]: m for m in c["devs"]}
    info = {}
    for n in sorted(R):
        if n in acg: continue
        e = collections.defaultdict(list)
        if n in excite: e["port"].append(n)
        for m in c["devs"]:
            t = cell[m["name"]]["type"]
            if m["d"] == n and t in ("CS", "CG", "CSCD_review"): e["cur"].append(m["name"])
            if m["s"] == n and m["g"] in R and t in ("CS", "CD", "CSCD_review"): e["volt"].append(m["name"])
            if m["s"] == n and t == "diode" and m["g"] in R: e["diode_src"].append(m["name"])
            if m["d"] == n and t in ("load", "off"): e["load_drain"].append(m["name"])
        for p in c["pas"]:
            for x, y in ((p["a"], p["b"]), (p["b"], p["a"])):
                if x == n and y in R:
                    e["R" if p["kind"] == "R" else "C"].append((p["name"], y))
        for b in bundles:
            if n in b[2]:
                other = b[2][1] if b[2][0] == n else b[2][0]
                if other in R: e["pass"].append((b[0] + "/" + b[1], other))
        gate_exit = [m["name"] for m in c["devs"] if m["g"] == n and cell[m["name"]]["type"] in ("CS", "CD", "CSCD_review")]
        chan_exit = [m["name"] for m in c["devs"] if m["s"] == n and cell[m["name"]]["type"] == "CG"]
        info[n] = dict(entries=dict(e), gate_exit=gate_exit, chan_exit=chan_exit)
    kind = {}
    attr = collections.defaultdict(list)
    for n, I in info.items():
        e = I["entries"]
        if "port" in e:
            kind[n] = "V"; continue
        if "volt" in e:
            others = [x for x in (e.get("cur", []) + e.get("load_drain", [])) if x not in e["volt"]]
            # mixed rule applies to drains of "other devices" (any MOS drain at n)
            others = [m["name"] for m in c["devs"] if m["d"] == n and m["name"] not in e["volt"]]
            if not others:
                kind[n] = "V"
            else:
                rs = {x: role[x] for x in others}
                if all(r == "bias" for r in rs.values()): kind[n] = "V"
                elif any(r == "signal" for r in rs.values()): kind[n] = "REVIEW_conflict"
                elif any(r == "unresolved" for r in rs.values()): kind[n] = "REVIEW_J"
                else: kind[n] = "UNDEF_mixed_role:" + ",".join(f"{k}={v}" for k, v in rs.items())
                attr[n].append(("mixed", rs))
            if "R" in e: attr[n].append("value_dependent")
            continue
        if "cur" in e:
            g, ch = I["gate_exit"], I["chan_exit"]
            if g and not ch: kind[n] = "V"
            elif ch and not g: kind[n] = "I"
            elif g and ch:
                gf = any(cell[x]["out"] in F for x in g)
                cf = any(cell[x]["out"] in F for x in ch)
                if gf: kind[n] = "V"
                elif cf: kind[n] = "TAP"
                else: kind[n] = "UNDEF_neither_forward"
            else:
                kind[n] = "I"
            if "R" in e: attr[n].append("value_dependent")
            continue
        if "diode_src" in e:
            kind[n] = "UNDEF_diode_source"; continue
        if "R" in e or "pass" in e or "C" in e:
            kind[n] = None; continue
        kind[n] = "UNDEF_no_entry"
    # inheritance through resistor-only / pass-only / capacitor-only
    for _ in range(50):
        ch = False
        for n, I in info.items():
            if kind.get(n) is not None: continue
            e = I["entries"]
            srcs = [y for (_, y) in e.get("pass", [])] + [y for (_, y) in e.get("R", [])]
            ks = {kind.get(y) for y in srcs if kind.get(y) is not None}
            if ks:
                k0 = sorted(ks)[0] if len(ks) == 1 else "REVIEW_inherit_conflict"
                if k0 == "I" and opt.get("priority_after_inherit", True):
                    g, chx = I["gate_exit"], I["chan_exit"]
                    if g and not chx: k0 = "V"
                    elif g and chx:
                        gf = any(cell[x]["out"] in F for x in g); cf = any(cell[x]["out"] in F for x in chx)
                        k0 = "V" if gf else ("TAP" if cf else "UNDEF_neither_forward")
                kind[n] = k0
                if e.get("R"): attr[n].append("value_dependent")
                attr[n].append("inherited")
                ch = True
        if not ch: break
    for n, I in info.items():
        if kind.get(n) is None:
            e = I["entries"]
            if e.get("C") and not e.get("R") and not e.get("pass"): kind[n] = "UNDEF_capacitor_only"
            else: kind[n] = "REVIEW_inherit_cycle"
    return kind, attr, info


# ----------------------------------------------------------------------------- blocks (rule 5/6, N3.7)
def build_blocks(c, R, acg, F, cell, bundles, role, kind, opt):
    dev = {m["name"]: m for m in c["devs"]}
    unres_as = opt.get("rule5_unresolved_as", "signal")
    def effective_bias(n):
        r = role[n]
        if r == "unresolved": return unres_as == "bias"
        return r == "bias"
    starts, rule9a, buf_cd, casc, vcg = [], [], [], [], []
    undefined_start = []
    for m in c["devs"]:
        t = cell[m["name"]]
        if t["type"] in ("CS", "CSCD_review"):
            k = kind.get(m["g"])
            if k == "V":
                if effective_bias(m["name"]): pass
                else: starts.append(m["name"])
            elif k in ("I", "TAP"):
                rule9a.append(m["name"])
            else:
                undefined_start.append((m["name"], k))
        elif t["type"] == "CG":
            k = kind.get(m["s"])
            if k == "V":
                if not effective_bias(m["name"]): starts.append(m["name"]); vcg.append(m["name"])
            elif k == "I": casc.append(m["name"])
            else: undefined_start.append((m["name"], k))
        elif t["type"] == "CD":
            buf_cd.append(m["name"])
    diode_at = collections.defaultdict(list)
    for m in c["devs"]:
        if m["g"] == m["d"]: diode_at[m["d"]].append(m["name"])
    # segments
    segs = {}
    for s0 in starts:
        mem = [s0]; nodes = {dev[s0]["g"] if cell[s0]["type"] != "CG" else dev[s0]["s"]}
        ins = set(nodes)
        outs = set(); frontier = [cell[s0]["out"]]; seen = set()
        mirror_used = []
        while frontier:
            o = frontier.pop(0)
            if o in seen: continue
            seen.add(o); nodes.add(o)
            nxt = False
            for m in c["devs"]:
                if cell[m["name"]]["type"] == "CG" and m["s"] == o and kind.get(o) == "I" and m["name"] not in starts:
                    mem.append(m["name"]); frontier.append(m["d"]); nxt = True
            if o in diode_at:
                readers = [m for m in c["devs"] if m["g"] == o and m["g"] != m["d"] and cell[m["name"]]["type"] in ("CS", "CSCD_review") and cell[m["name"]]["out"] in F]
                if readers:
                    mem += diode_at[o]
                    for r in readers:
                        if r["name"] not in starts or opt.get("mirror_absorbs_starters"):
                            mem.append(r["name"]); frontier.append(cell[r["name"]]["out"]); nxt = True
                            mirror_used.append((o, r["name"]))
            if not nxt: outs.add(o)
        segs[s0] = dict(members=mem, ins=ins, outs=outs, nodes=nodes, mirror=mirror_used)
    # a starter absorbed by another segment's mirror continuation is not its own segment
    if opt.get("mirror_absorbs_starters"):
        absorbed = {rd for s0, sg in segs.items() for (_, rd) in sg["mirror"] if rd != s0}
        for a in absorbed:
            if a in segs: del segs[a]
        starts = [x for x in starts if x not in absorbed]
    # merge by shared output node
    out_to = collections.defaultdict(list)
    for s0, sg in segs.items():
        for o in sg["outs"]: out_to[o].append(s0)
    uf = {s: s for s in segs}
    def find(x):
        while uf[x] != x: uf[x] = uf[uf[x]]; x = uf[x]
        return x
    merges = []
    for o, ss in out_to.items():
        if len(ss) < 2: continue
        # step 1: input-based rule.  inputs connected if same net, or via pass bundle, or segment reaches o through mirror whose diode lies in another merging segment
        def in_nets(s):
            x = set(segs[s]["ins"])
            for b in bundles:
                if b[2][0] in x or b[2][1] in x: x |= set(b[2])
            return x
        def via_mirror(s):
            return any(cell[rd]["out"] == o and dn in segs[s]["nodes"] for (dn, rd) in segs[s]["mirror"])
        mode = opt.get("mirror_merge", "Y")
        if mode == "none":
            core, mir = list(ss), []
        elif mode == "Y":
            core = [x for x in ss if not via_mirror(x)]
            mir = [x for x in ss if via_mirror(x)]
        else:
            core, mir = list(ss), []
        linked = nx.Graph(); linked.add_nodes_from(core)
        for a, b in itertools.combinations(core, 2):
            if in_nets(a) & in_nets(b): linked.add_edge(a, b)
            if mode == "X" and (via_mirror(a) or via_mirror(b)): linked.add_edge(a, b)
        comps = list(nx.connected_components(linked)) if core else [set()]
        if mode == "Y" and mir:
            comps = [set(x) for x in comps] if core else [set()]
            if len(comps) == 1: comps = [comps[0] | set(mir)]
            else: comps.append(set(mir))
        if len(comps) == 1:
            merges.append(dict(node=o, kind="step1_one_block", segs=ss))
            for s in ss[1:]: uf[find(s)] = find(ss[0])
        else:
            merges.append(dict(node=o, kind="residual", segs=ss, comps=[sorted(x) for x in comps]))
    return dict(starts=starts, rule9a=rule9a, buf_cd=buf_cd, cascode=casc, vcg=vcg, undefined_start=undefined_start,
                segs=segs, merges=merges, uf={s: find(s) for s in segs})


# ----------------------------------------------------------------------------- run one circuit
def run(c, opt):
    res = dict(circuit=c["name"], opt=opt)
    acg_base, gate_only = base_acg(c)
    net_sym, dev_sym = symmetry_map(c)
    diff = net_sym is not None
    excite = list(c["ins"])
    res["view"] = "odd-mode(nonreduced)" if diff and len(excite) == 2 else "single"
    acg0 = set(acg_base)
    bdn = bias_dependent_nets(c, acg0, excite, net_sym if diff else None, opt)
    res["rule1_4"] = bdn
    acg = set(acg0) | ({x["net"] for x in bdn if not x["moves_in_view"]} if not opt.get("no_rule14") else set())
    if opt.get("reduced") and diff:
        vg = {n for n, m in net_sym.items() if m == n and n not in c["rails"]}
        res["virtual_ground"] = sorted(vg)
        acg |= vg
    if opt.get("iterate_rule1_4"):
        for _ in range(5):
            more = bias_dependent_nets(c, acg, excite, net_sym if diff else None, opt)
            new = {x["net"] for x in more if not x["moves_in_view"]} - acg
            if not new: break
            acg |= new; res.setdefault("rule1_4_iter_extra", []).extend(sorted(new))
    R = reach(c, acg, excite)
    F = forward_set(c, R, c["outs"])
    res["acg"] = sorted(acg); res["signal_nets"] = sorted(R); res["forward"] = sorted(F)
    # DC roles.  'all views AC ground': variant A base only; variant B base + rule1(4) nets not moving in *any* view
    acg_all = set(acg_base)
    if opt.get("dcrole_include_rule14"):
        acg_all |= {x["net"] for x in bdn if not x["moves_in_view"]}
    role, grp, inh = dc_roles(c, acg_all, opt)
    res["dc_role_counts"] = dict(collections.Counter(role.values()))
    res["dc_unresolved_groups"] = grp
    res["dc_role"] = role
    res["dc_inherit"] = inh
    cell, bundles, pass3 = classify_cells(c, R, acg, F, excite)
    res["cells"] = {k: v["type"] for k, v in cell.items()}
    res["bundles"] = bundles; res["pass3"] = pass3
    cnt_all = collections.Counter(v["type"] for v in cell.values())
    fwd_cells = {}
    for k, v in cell.items():
        if v["type"] == "pass":
            isf = any(k in b[:2] and (b[2][0] in F or b[2][1] in F) for b in bundles)
        elif v["type"] in ("diode",):
            isf = v["out"] in F
        else:
            isf = v.get("out") in F
        fwd_cells[k] = isf
    res["cell_count_all"] = dict(cnt_all)
    res["cell_count_forward"] = dict(collections.Counter(v["type"] for k, v in cell.items() if fwd_cells[k]))
    res["cells_offforward"] = sorted(k for k, v in cell.items() if not fwd_cells[k] and v["type"] in ("CS", "CG", "CD", "pass", "CSCD_review"))
    kind, attr, info = drive_kinds(c, R, acg, F, cell, bundles, role, excite, opt)
    res["drive_kind"] = kind
    res["drive_attr"] = {k: [str(a) for a in v] for k, v in attr.items()}
    res["mixed_nodes"] = sorted(k for k, v in attr.items() if any(isinstance(a, tuple) and a[0] == "mixed" for a in v))
    blk = build_blocks(c, R, acg, F, cell, bundles, role, kind, opt)
    res["blocks"] = {k: dict(members=v["members"], ins=sorted(v["ins"]), outs=sorted(v["outs"])) for k, v in blk["segs"].items()}
    res["block_union"] = blk["uf"]
    res["merges"] = blk["merges"]
    for k in ("starts", "rule9a", "buf_cd", "cascode", "vcg", "undefined_start"):
        res[k] = blk[k]
    return res, dict(c=c, acg=acg, R=R, F=F, cell=cell, bundles=bundles, role=role, kind=kind, blk=blk, excite=excite, net_sym=net_sym, acg_base=acg_base)


def circuits():
    out = []
    for f in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
        if "_TEMPLATE" in f: continue
        out.append(load(f))
    return out


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "base"
    opt = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    fn = os.path.join(SP, f"results_{tag}.jsonl")
    open(fn, "w").close()
    for c in circuits():
        r, _ = run(c, opt)
        with open(fn, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        print(c["name"], "ok")
