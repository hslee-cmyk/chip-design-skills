# -*- coding: utf-8 -*-
"""m_gc8a: library 13 circuits, W4-root-touching MOS vs conduction axes (static, connectivity + spec only).
Definitions read from plan v6.38.5 (9a9b1ed4): see m_gc8a_conduction_axis.md section 'Definitions'.
Writes one jsonl line per circuit (append) to m_gc8a/results.jsonl. Read-only on the repo.
"""
import json, glob, os, sys, itertools
from fractions import Fraction

LIB = r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library"
OUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-30/m_gc8a/results.jsonl"


def load(n):
    t = json.load(open(f"{LIB}/{n}.topology.json", encoding="utf8"))
    s = json.load(open(f"{LIB}/{n}.sizing_spec.json", encoding="utf8"))
    return t, s


def rref_nullspace(rows, ncols):
    """exact nullspace of matrix (list of dict col->Fraction)"""
    M = [[Fraction(0)] * ncols for _ in rows]
    for i, r in enumerate(rows):
        for c, v in r.items():
            M[i][c] = Fraction(v)
    piv = []
    r = 0
    for c in range(ncols):
        p = None
        for i in range(r, len(M)):
            if M[i][c] != 0:
                p = i
                break
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        inv = 1 / M[r][c]
        M[r] = [x * inv for x in M[r]]
        for i in range(len(M)):
            if i != r and M[i][c] != 0:
                f = M[i][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        piv.append(c)
        r += 1
        if r == len(M):
            break
    free = [c for c in range(ncols) if c not in piv]
    basis = []
    for fcol in free:
        v = [Fraction(0)] * ncols
        v[fcol] = Fraction(1)
        for ri, pc in enumerate(piv):
            v[pc] = -M[ri][fcol]
        basis.append(v)
    return basis


def analyse(name):
    t, s = load(name)
    h = s["human"]
    mos = t["netlist"]
    rails = set(t["supply_nets"])
    bias = set(t.get("bias_inputs") or [])
    ports = {k: v for k, v in t["ports"].items() if not k.startswith("_")}
    in_ports = [k for k, v in ports.items() if v.get("direction") == "input"]
    pe = t.get("passive_elements", []) or []
    res = [p for p in pe if p["kind"] == "resistor"]
    isrc = [p for p in (t.get("ideal_sources") or []) if p["kind"] == "current_source"]
    other_src = [p for p in (t.get("ideal_sources") or []) if p["kind"] != "current_source"]

    idc = h.get("input_dc")
    input_declared = isinstance(idc, dict) and ("value_v" in idc or "net" in idc or "value" in idc)
    ir = h.get("intended_region")
    ir_declared = isinstance(ir, dict) and "pending" not in ir
    nvt = h.get("node_voltage_targets_v")
    nvt_declared = isinstance(nvt, dict) and "pending" not in nvt
    region = {}
    if ir_declared:
        for k, v in ir.items():
            region[k] = v if isinstance(v, str) else (v.get("region") if isinstance(v, dict) else str(v))
    nvt_nets = set(nvt.keys()) if nvt_declared else set()

    ZERO_MOS = set()
    rec = dict(circuit=name, n_mos=len(mos), input_declared=input_declared, intended_region_declared=ir_declared,
               region_decl=region, node_targets_declared=nvt_declared, in_ports=in_ports,
               bias_inputs=sorted(bias), other_ideal_sources=[p["name"] for p in other_src])

    # ---- Gs+ construction (HC N0.1 / DEC-106) ; variants on bias_inputs membership in F
    def gsplus(bias_in_F, dr1=False):
        F = set(rails) | set(nvt_nets)
        if bias_in_F:
            F |= bias
        if dr1:
            fixed = set(F) | (set(in_ports) if input_declared else set())
            ch = True
            while ch:
                ch = False
                for d in mos:
                    if d['name'] in ZERO_MOS:
                        a, b = d['drain'], d['source']
                        if a in fixed and b not in fixed:
                            fixed.add(b); F.add(b); ch = True
                        elif b in fixed and a not in fixed:
                            fixed.add(a); F.add(a); ch = True
        if input_declared:
            F |= set(in_ports)
        # input points
        merged = {}
        diff_p = [k for k in in_ports if ports[k].get("role") == "differential_input_p"]
        diff_n = [k for k in in_ports if ports[k].get("role") == "differential_input_n"]
        input_points = []
        if not input_declared:
            if len(diff_p) == 1 and len(diff_n) == 1:
                merged[diff_n[0]] = diff_p[0]
                input_points = [diff_p[0]] + [k for k in in_ports if k not in (diff_p[0], diff_n[0])]
            else:
                input_points = list(in_ports)
        ptn = lambda n: "F" if n in F else merged.get(n, n)
        edges = []
        for d in mos:
            edges.append((ptn(d["gate"]), ptn(d["source"]), "vgs:" + d["name"]))
        for r in res:
            a, b = r["terminals"]
            edges.append((ptn(a), ptn(b), "res:" + r["name"]))
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        nodes_in_gs = set(["F"])
        for a, b, _ in edges:
            nodes_in_gs |= {a, b}
            parent.setdefault(a, a); parent.setdefault(b, b)
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        comps = {}
        for n in nodes_in_gs:
            comps.setdefault(find(n), set()).add(n)
        floating = [c for c in comps.values() if "F" not in c]
        # map merged ports back: members
        def expand(c):
            out = set()
            for n in c:
                out.add(n)
                for k, v in merged.items():
                    if v == n:
                        out.add(k)
            return out
        roots_min, roots_any, comp_info = set(), set(), []
        for c in floating:
            ips = sorted(n for n in c if n in input_points)
            if ips:
                root = ips[0]
                multi_inp = len(ips) > 1
            else:
                root = min(c)
                multi_inp = False
            roots_min.add(root)
            ex = expand(c)
            roots_any |= ex
            comp_info.append(dict(nets=sorted(ex), root=root, has_input_point=bool(ips), multi_input_points=multi_inp))
        # isolated (drain-only) nets: appear as drain of a MOS, not in Gs+ nodes, not F, not rail
        allnets = set()
        for d in mos:
            allnets |= {d["drain"], d["gate"], d["source"]}
        iso = sorted(n for n in allnets if ptn(n) != "F" and ptn(n) not in nodes_in_gs)
        # nodes_in_gs holds mapped names; merged names map to rep present
        return dict(F=F, roots_min=roots_min, roots_any=roots_any, comps=comp_info, isolated=iso)


    def touch(rootset):
        return sorted(d["name"] for d in mos if d["drain"] in rootset or d["source"] in rootset)

    # ---- KCL identity-zero channel set
    driven = set(rails) | bias | set(in_ports) | set(nvt_nets)
    el = []  # (kind,name,a,b)
    for d in mos:
        el.append(("mos", d["name"], d["drain"], d["source"]))
    for r in res:
        el.append(("res", r["name"], r["terminals"][0], r["terminals"][1]))
    srcs = [(p["name"], p["terminals"][0], p["terminals"][1]) for p in isrc]
    nets = sorted({n for e in el for n in e[2:]} | {n for s_ in srcs for n in s_[1:]})
    kcl_nets = [n for n in nets if n not in driven]
    ncol = len(el) + len(srcs)
    rows = []
    for n in kcl_nets:
        row = {}
        for j, (k, nm, a, b) in enumerate(el):
            v = (1 if a == n else 0) - (1 if b == n else 0)  # current a->b leaves a, enters b
            if v:
                row[j] = row.get(j, 0) + v
        for j, (nm, a, b) in enumerate(srcs):
            v = (1 if a == n else 0) - (1 if b == n else 0)
            if v:
                row[len(el) + j] = row.get(len(el) + j, 0) + v
        rows.append(row)
    ns = rref_nullspace(rows, ncol)
    zero1 = sorted(el[j][1] for j in range(len(el)) if all(v[j] == 0 for v in ns))
    zero1_mos = sorted(x for x in zero1 if any(x == d["name"] for d in mos))
    # sufficient condition (chains): non-driven net whose only DC element is this channel
    alive = set(range(len(el)))
    z2 = set()
    changed = True
    while changed:
        changed = False
        for j in sorted(alive):
            k, nm, a, b = el[j]
            for n in (a, b):
                if n in driven:
                    continue
                cnt = [i for i in alive if n in el[i][2:]] + [("s", i) for i, s_ in enumerate(srcs) if n in s_[1:]]
                if cnt == [j]:
                    z2.add(nm); alive.discard(j); changed = True
                    break
    z2_mos = sorted(x for x in z2 if any(x == d["name"] for d in mos))
    rec["kcl_zero_mos_nullspace"] = zero1_mos
    rec["kcl_zero_mos_sufficient_chain"] = z2_mos
    rec["kcl_zero_res"] = [x for x in zero1 if x not in zero1_mos]
    rec["nullspace_dim"] = len(ns)

    ZERO_MOS.update(zero1_mos)
    # ---- LP: is MOS current sign (declared direction) forced by KCL alone?  (cone feasibility, free resistor sign)
    import numpy as np
    from scipy.optimize import linprog
    A = np.zeros((len(kcl_nets), ncol))
    for i_, row in enumerate(rows):
        for j, v in row.items():
            A[i_, j] = v
    sign = []
    for (k, nm, a, b) in el:
        if k == 'mos':
            kd = [d for d in mos if d['name'] == nm][0]['kind']
            sign.append(-1.0 if kd == 'pmos' else 1.0)
        else:
            sign.append(0.0)
    sign += [1.0] * len(srcs)
    def lp(i_force_nonpos):
        # vars: x(ncol), t ; maximize t
        n = ncol + 1
        c = np.zeros(n); c[-1] = -1.0
        Aub, bub = [], []
        for j in range(ncol):
            if sign[j] == 0.0 or (j < len(el) and el[j][1] in zero1_mos):
                continue
            row = np.zeros(n)
            if j == i_force_nonpos:
                row[j] = sign[j]  # sign*x <= 0
                Aub.append(row); bub.append(0.0)
            else:
                row[j] = -sign[j]; row[-1] = 1.0   # sign*x >= t
                Aub.append(row); bub.append(0.0)
        Aeq = np.hstack([A, np.zeros((A.shape[0], 1))]) if A.shape[0] else None
        beq = np.zeros(A.shape[0]) if A.shape[0] else None
        bounds = [(None, None)] * ncol + [(0, 1)]
        r_ = linprog(c, A_ub=np.array(Aub), b_ub=np.array(bub), A_eq=Aeq, b_eq=beq, bounds=bounds, method='highs')
        return (r_.status == 0) and (-r_.fun > 1e-7)
    sign_class = {}
    all_pos = lp(-1)
    for j, (k, nm, a, b) in enumerate(el):
        if k != 'mos' or nm in zero1_mos:
            continue
        if not all_pos:
            sign_class[nm] = 'cone_infeasible'
            continue
        nonpos_ok = lp(j)
        sign_class[nm] = 'theta_dependent' if nonpos_ok else 'always_conducting'
    rec['kcl_cone_all_declared_direction_positive_feasible'] = bool(all_pos)
    rec['kcl_sign_class'] = sign_class
    G = {"biasFree": gsplus(False), "biasF": gsplus(True),
         "biasFree+DR1F": gsplus(False, True), "biasF+DR1F": gsplus(True, True)}
    # ---- per-variant results
    off = sorted(k for k, v in region.items() if v == "off")
    tri = sorted(k for k, v in region.items() if v == "triode")
    rec["off_declared"] = off
    rec["triode_declared"] = tri
    rec["variants"] = {}
    for vname, g in G.items():
        v = {}
        v["floating_components"] = g["comps"]
        v["isolated_drain_only_nets"] = g["isolated"]
        v["roots_min"] = sorted(g["roots_min"])
        for key, rs in [("I1_root_min", g["roots_min"]), ("I1x_any_net_of_floating", g["roots_any"]),
                        ("I2_root_min_plus_isolated", set(g["roots_min"]) | set(g["isolated"])),
                        ("I2x_any_plus_isolated", set(g["roots_any"]) | set(g["isolated"]))]:
            T = touch(rs)
            v[key] = dict(touching=T,
                          n=len(T),
                          a_off=[x for x in T if x in off],
                          b_kcl_zero=[x for x in T if x in zero1_mos],
                          c_triode=[x for x in T if x in tri],
                          conduct_structural=[x for x in T if x not in zero1_mos],
                          conduct_theta_known=[x for x in T if x not in zero1_mos and x not in off],
                          theta_dependent=[x for x in T if sign_class.get(x) == 'theta_dependent'])
        rec["variants"][vname] = v
    return rec


if __name__ == "__main__":
    names = sorted(os.path.basename(f).split(".")[0] for f in glob.glob(LIB + "/*.topology.json"))
    names = [n for n in names if not n.startswith("_")]
    if os.path.exists(OUT):
        os.remove(OUT)
    for n in names:
        r = analyse(n)
        with open(OUT, "a", encoding="utf8") as f:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(n, "done", file=sys.stderr)
