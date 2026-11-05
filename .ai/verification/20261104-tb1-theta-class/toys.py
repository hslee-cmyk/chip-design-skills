"""Targeted audit toys. usage: toys.py <skill root> <out>"""
import dataclasses, itertools, json, os, pathlib, sys, tempfile, traceback
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
from gmid_engine.search import open_run
from gmid_engine.graph import build_s1, build_s1v, GRAPH_KEY, S1V_KEY
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.sizing import DcInputs, build_kernel_context, dc_inputs_from_spec, dc_writer_plan, theta_class, ThetaClass
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.tests.sizing import conftest as C
from gmid_engine.lut import load_lut_set
from gmid_engine.tests.sizing.conftest import mos, two, topo

td = pathlib.Path(tempfile.mkdtemp(dir=os.path.dirname(OUT)))
m, c = C.write_toy_lut(td / "lut")
access = C.new_access(load_lut_set(str(m), str(c), C.TOY_SPEC))
SUP = dict(C.SUPPLIES)
out = open(OUT, "w", encoding="utf8")
cnt = [0]


def tmp():
    cnt[0] += 1
    p = td / ("t%d" % cnt[0]); p.mkdir(); return p


def W(tag, **kw):
    out.write(json.dumps({"tag": tag, **kw}, ensure_ascii=False, default=str) + "\n"); out.flush()


def build(doc, gbw=False, rout=False, settle=False, s1v=True, sup=None):
    sup = dict(sup or SUP)
    donors, counters = open_run(); run = dict(donors=donors, counters=counters)
    s1 = build_s1(C.load_doc(tmp(), doc), sup, **run)
    g = build_s1v(s1, None, count_budget=10 ** 6, stop_on_unsupported=False, **run) if s1v else s1
    inp = DcInputs(tuple(sorted(sup.items())), has_gbw_target=gbw, has_rout_limit=rout, has_settling=settle)
    return build_kernel_context(g, inp, access, **run)


def info(ctx):
    b = ctx.base
    return dict(tc={k: v.kind for k, v in b.column("device", "theta_class")},
                dep={k: (v.relation, v.partner) for k, v in b.column("device", "dc_coord") if v.role == "dependent"},
                colour=dict(b.column("device", "dc_colour")),
                orbits=dict(b.value("graph", GRAPH_KEY, "orbits").devices),
                gens=[[(e, i, s) for e, i, s in g] for g in b.value("graph", GRAPH_KEY, "current_symmetry").generators],
                views=[(v.id, v.excite, [(bb.kind, bb.stage, [n for n, r in bb.roles if r == "input"]) for bb in v.blocks]) for v in b.value("graph", S1V_KEY, "views") if v.kind == "transfer"] if b.field("graph", S1V_KEY, "views") is not None else None)


# ---- T1 multi-view: two single-ended inputs of different structure; rename only the input nets (order flips)
def two_in(ia, ib):
    return topo("aud_two", [mos("M1", "nmos", "out", ia, "gnd"), mos("M2", "nmos", "out", ib, "x"), mos("M3", "nmos", "x", "nb", "gnd"),
                            mos("M6", "nmos", "nb", "nb", "gnd"), mos("M4", "pmos", "out", "pb", "vdd"), mos("M7", "pmos", "pb", "pb", "vdd")],
                {ia: ("input", "single_ended_input"), ib: ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb"), two("I2", "current_source", "pb", "gnd")])


for label, (ia, ib) in (("a_first", ("ia", "ib")), ("b_first", ("zz", "aa"))):
    try:
        i = info(build(two_in(ia, ib), gbw=True))
        W("T1_multiview_name", label=label, inputs=(ia, ib), tc=i["tc"], dep=i["dep"], views=i["views"], colour=i["colour"])
    except Exception:
        W("T1_multiview_name", label=label, err=traceback.format_exc()[-800:])


# ---- T1b also dependents change? a loop whose non-B ranking depends on S vs F in parallel: M1 and M1p parallel on ia, M2 and M2p parallel on ib
def two_in_par(ia, ib):
    d = two_in(ia, ib)
    d["netlist"] += [mos("M1p", "nmos", "out2", ia, "gnd"), mos("M5", "pmos", "out2", "pb", "vdd")]
    d["ports"]["out2"] = {"direction": "output", "role": "single_ended_output"}
    return d


for label, (ia, ib) in (("a_first", ("ia", "ib")), ("b_first", ("zz", "aa"))):
    try:
        i = info(build(two_in_par(ia, ib), gbw=True))
        W("T1b_multiview_dep", label=label, inputs=(ia, ib), tc=i["tc"], dep=i["dep"], n_views=len(i["views"]))
    except Exception:
        W("T1b_multiview_dep", label=label, err=traceback.format_exc()[-800:])


# ---- T2 pinned B rep in loop with non-B: inverter loop Mn (B, parallel pair Mn,Mn2) + Mp (F)
def inv_par():
    return topo("aud_invp", [mos("Mn", "nmos", "out", "x", "gnd"), mos("Mn2", "nmos", "o2", "x", "gnd"), mos("Mp", "pmos", "out", "x", "vdd"),
                             mos("Pl", "pmos", "o2", "pb", "vdd")],
                {"x": ("input", "single_ended_input"), "out": ("output", "y"), "o2": ("output", "y")}, bias=["pb"])


ctx = build(inv_par(), s1v=False)
snap = C.tamper(ctx.base, theta_class.name, "device", "theta_class", {"Mn": ThetaClass("B"), "Mn2": ThetaClass("B"), "Mp": ThetaClass("F"), "Pl": ThetaClass("B")})
s = dc_writer_plan(snap, (), False, donors=ctx.donors, counters=ctx.counters)
W("T2_pinned_B_rep", dep={k: (v.relation, v.partner) for k, v in s.column("device", "dc_coord") if v.role == "dependent"},
  note="loop {Mn(B, parallel rep), Mp(F)}: card (a) literally = B dependent")


# ---- T3 downstream restricted to loop members? triangle A(F) B C both B, C.source = rail; D off-loop MOS whose gate = C's? make B2 source net gated by off-loop device
def tri_off():
    # loop A(n1,gnd) diode? use: A nmos(o0,n3,gnd)  B nmos(o1,n2,n1) C nmos(o2,n2,n3) E nmos(n1,n3?..)
    return topo("aud_tri_off", [mos("A", "nmos", "n1", "n1", "gnd"), mos("B", "nmos", "o1", "n2", "n1"), mos("C", "nmos", "o2", "n2", "n4"),
                                mos("G", "nmos", "n4", "n4x", "gnd"), mos("H", "nmos", "o3", "n4", "gnd"), mos("Q", "nmos", "n4x", "n4x", "gnd"),
                                mos("P1", "pmos", "o1", "pb1", "vdd"), mos("P2", "pmos", "o2", "pb2", "vdd"), mos("P3", "pmos", "o3", "pb3", "vdd")],
                {"n2": ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y"), "o3": ("output", "y")},
                sources=[two("I1", "current_source", "vdd", "n1"), two("I2", "current_source", "vdd", "n4x")], bias=["pb1", "pb2", "pb3"])


try:
    ctx = build(tri_off(), s1v=False)
    W("T3_info", dep={k: v for k, v in info(ctx)["dep"].items()}, colour=info(ctx)["colour"])
except Exception:
    W("T3_info", err=traceback.format_exc()[-600:])


# ---- T5 brute-force automorphism of _sym4: enumerate device+net perms preserving kind/pins
def automorphisms(doc):
    devs = doc["netlist"]
    nets = sorted({e[k] for e in devs for k in ("drain", "gate", "source")})
    fixed = set(doc["supply_nets"])
    free = [n for n in nets if n not in fixed]
    autos = []
    rows = {(e["kind"], e["drain"], e["gate"], e["source"]): e["name"] for e in devs}
    role = {k: (v["direction"], v["role"]) for k, v in doc["ports"].items()}
    bias = set(doc.get("bias_inputs") or [])
    for p in itertools.permutations(free):
        mp = dict(zip(free, p))
        if any(role.get(a) != role.get(b) or ((a in bias) != (b in bias)) for a, b in mp.items()):
            continue
        ok = {}
        good = True
        for e in devs:
            key = (e["kind"], mp.get(e["drain"], e["drain"]), mp.get(e["gate"], e["gate"]), mp.get(e["source"], e["source"]))
            if key not in rows:
                good = False; break
            ok[e["name"]] = rows[key]
        if good:
            autos.append(ok)
    return autos


def sym4(a="MA", b="MB", cc="MC", d="MD"):
    return topo("tb1_sym", [mos(a, "nmos", "oa", "pb", "gnd"), mos(b, "nmos", "ob", "pb", "gnd"), mos(cc, "pmos", "oa", "pc", "vdd"), mos(d, "pmos", "ob", "pc", "vdd")],
                {"pb": ("input", "x"), "oa": ("output", "y"), "ob": ("output", "y")}, bias=["pc"])


autos = automorphisms(sym4())
W("T5_sym4_aut_bruteforce", n=len(autos), autos=autos)
i1 = info(build(sym4(), s1v=False)); i2 = info(build(sym4("Z1", "A1"), s1v=False))
W("T5_sym4_dep", original=i1["dep"], renamed=i2["dep"], colour1=i1["colour"], colour2=i2["colour"])
# strict equivariance impossibility: every automorphism moving pair members -- dep set must be fixed by every automorphism for a strict rule
dep1 = set(i1["dep"])
W("T5_strict_impossible", dep=sorted(dep1), images=[sorted(a.get(x, x) for x in dep1) for a in autos],
  any_selection_invariant=[sel for sel in itertools.product(("MA", "MB"), ("MC", "MD")) if all({a.get(x, x) for x in sel} == set(sel) for a in autos)])

# ---- T5b non-automorphic twin: same as sym4 but oa/ob distinguished by different load (no automorphism) -> selection must be strictly sigma-equivariant


def sym4_broken(a="MA", b="MB", cc="MC", d="MD", ob="ob"):
    return topo("aud_sym_broken", [mos(a, "nmos", "oa", "pb", "gnd"), mos(b, "nmos", ob, "pb", "gnd"), mos(cc, "pmos", "oa", "pc", "vdd"), mos(d, "pmos", ob, "pc", "vdd"),
                                   mos("X", "nmos", ob, "pc2", "gnd")],
                {"pb": ("input", "x"), "oa": ("output", "y"), ob: ("output", "y")}, bias=["pc", "pc2"])


for lab, names in (("orig", ("MA", "MB", "MC", "MD")), ("ren", ("Z1", "A1", "MC", "MD")), ("ren2", ("Q", "B", "ZC", "AD"))):
    i = info(build(sym4_broken(*names), s1v=False))
    W("T5b_nonautomorphic", lab=lab, names=names, dep=i["dep"], orbits=i["orbits"])

# ---- T6 symmetric loop pair closure: two independent mirrored loops, try rename variety
def symloops(s=("A1", "A2", "B1", "B2")):
    a1, a2, b1, b2 = s
    return topo("aud_pairs", [mos(a1, "nmos", "n1a", "n2a", "gnd"), mos(a2, "nmos", "n1b", "n2b", "gnd"),
                              mos(b1, "nmos", "o1", "n2a", "n1a"), mos(b2, "nmos", "o2", "n2b", "n1b"),
                              mos("C1", "nmos", "n2a", "n1a", "gnd"), mos("C2", "nmos", "n2b", "n1b", "gnd"),
                              mos("P1", "pmos", "o1", "pb", "vdd"), mos("P2", "pmos", "o2", "pb", "vdd")],
                {"o1": ("output", "y"), "o2": ("output", "y")},
                sources=[two("I1", "current_source", "vdd", "n1a"), two("I2", "current_source", "vdd", "n1b"), two("I3", "current_source", "vdd", "n2a"), two("I4", "current_source", "vdd", "n2b")], bias=["pb"])


try:
    i = info(build(symloops(), s1v=False))
    W("T6_symloops", dep=i["dep"], colour=i["colour"], gens=i["gens"])
except Exception:
    W("T6_symloops", err=traceback.format_exc()[-700:])

# ---- T7 library rename through S1v default view (macro from spec flags): dep/theta by colour correspondence and isomorphism
LIB = pathlib.Path(ROOT) / "assets" / "library"
import json as J
names = sorted(p.name[:-len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
tot = dict(cases=0, stop=0, dep_equal=0, tc_equal=0, iso_ok=0, keyset_same=0)
for name in names:
    raw = J.loads((LIB / (name + ".topology.json")).read_text(encoding="utf8"))
    td0 = load_topology(str(LIB / (name + ".topology.json")))
    spec = load_sizing_spec(str(LIB / (name + ".sizing_spec.json")), td0, C.spec_catalog())
    inp = dc_inputs_from_spec(spec)
    def run_case(doc, inputs):
        donors, counters = open_run(); run = dict(donors=donors, counters=counters)
        s1 = build_s1(C.load_doc(tmp(), doc), dict(inputs.supplies_v), **run)
        g = build_s1v(s1, None, count_budget=10 ** 6, stop_on_unsupported=False, **run)
        return build_kernel_context(g, inputs, access, **run)
    try:
        base_ctx = run_case(raw, inp)
    except StructureUnresolvedError as e:
        tot["stop"] += 1; W("T7", circuit=name, stop=dict(e.record.detail).get("rule_branch")); continue
    ba = info(base_ctx)
    for seed in (1, 2, 3):
        d2, sn, se = C.rename(raw, seed)
        i2 = dataclasses.replace(C.rename_inputs(inp, sn, se), has_gbw_target=inp.has_gbw_target, has_rout_limit=inp.has_rout_limit, has_settling=inp.has_settling)
        cb = run_case(d2, i2)
        bb = info(cb)
        tot["cases"] += 1
        e2 = {v: k for k, v in bb["colour"].items()}
        em = {k: e2[v] for k, v in ba["colour"].items()}
        n1 = dict(base_ctx.base.column("node", "dc_colour")); n2 = dict(cb.base.column("node", "dc_colour")); n2i = {v: k for k, v in n2.items()}
        nm = {k: n2i[v] for k, v in n1.items()}
        p1 = {k: dict(v) for k, v in base_ctx.base.column("device", "pins")}; p2 = {k: dict(v) for k, v in cb.base.column("device", "pins")}
        iso = True
        for k, pp in p1.items():
            q = p2[em[k]]
            if set(pp) >= {"g"}:
                iso &= nm[pp["g"]] == q["g"] and {nm[pp["d"]], nm[pp["s"]]} == {q["d"], q["s"]}
            else:
                iso &= sorted(nm[x] for x in pp.values()) == sorted(q.values())
        dep_eq = {(em[k], v[0]) for k, v in ba["dep"].items()} == {(k, v[0]) for k, v in bb["dep"].items()}
        tc_eq = {em[k]: v for k, v in ba["tc"].items()} == bb["tc"]
        tot["dep_equal"] += dep_eq; tot["tc_equal"] += tc_eq; tot["iso_ok"] += iso
        if not (dep_eq and tc_eq and iso):
            W("T7_diff", circuit=name, seed=seed, dep_eq=dep_eq, tc_eq=tc_eq, iso=iso)
    W("T7", circuit=name, ok=True)
W("T7_total", **tot)
out.close()
