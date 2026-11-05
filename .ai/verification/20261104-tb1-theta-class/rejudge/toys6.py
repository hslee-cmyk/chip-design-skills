"""Same physical point under two dependent selections (values), and main_path vs input role. usage: toys6.py <skill root> <out>"""
import json, os, pathlib, sys, tempfile, traceback
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
from gmid_engine.search import open_run
from gmid_engine.graph import build_s1, build_s1v, S1V_KEY
from gmid_engine.sizing import DcInputs, build_kernel_context, KERNEL_KEY
from gmid_engine.sizing.kernel_run import run_kernel
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.sizing import dc_inputs_from_spec
from gmid_engine.tests.sizing import conftest as C
from gmid_engine.lut import load_lut_set
from gmid_engine.tests.sizing.conftest import mos, two, topo

td = pathlib.Path(tempfile.mkdtemp(dir=os.path.dirname(OUT)))
m, c = C.write_toy_lut(td / "lut")
access = C.new_access(load_lut_set(str(m), str(c), C.TOY_SPEC))
SUP = dict(C.SUPPLIES)
out = open(OUT, "w", encoding="utf8")
n = [0]


def tmp():
    n[0] += 1
    p = td / ("t%d" % n[0]); p.mkdir(); return p


def W(tag, **kw):
    out.write(json.dumps({"tag": tag, **kw}, ensure_ascii=False, default=str) + "\n"); out.flush()


def ctx_of(doc, s1v, gbw=False):
    donors, counters = open_run(); run = dict(donors=donors, counters=counters)
    s1 = build_s1(C.load_doc(tmp(), doc), dict(SUP), **run)
    g = build_s1v(s1, None, count_budget=10 ** 6, stop_on_unsupported=False, **run) if s1v else s1
    return build_kernel_context(g, DcInputs(tuple(sorted(SUP.items())), element_values=(("I1", 2e-5),), has_gbw_target=gbw), access, **run)


def inv():
    return topo("aud_inv", [mos("Mn", "nmos", "out", "x", "gnd"), mos("Mp", "pmos", "out", "x", "vdd")],
                {"x": ("input", "single_ended_input"), "out": ("output", "single_ended_output")})


def evaluate(ctx, theta):
    ev = run_kernel(ctx, theta, None, (), False)
    snap = getattr(ev, "snapshot", ev)
    return ev, snap


def report(snap):
    op = dict(snap.column("device", "dc_op"))
    vals = {k: {f: getattr(v, f, None) for f in ("vgs", "vds", "vsb", "id")} for k, v in op.items()}
    nodes = dict(snap.column("node", "dc_v")) if snap.field("node", "gnd", "dc_v") is not None else {}
    return vals, nodes


try:
    a = ctx_of(inv(), False)
    b = ctx_of(inv(), True)
    for tag, cx in (("A_all_B", a), ("B_with_views", b)):
        sc = cx.base.value("graph", KERNEL_KEY, "theta_schema")
        W("schema", which=tag, comps=sc.components, tc={k: v.kind for k, v in cx.base.column("device", "theta_class")},
          dep={k: v.relation for k, v in cx.base.column("device", "dc_coord") if v.role == "dependent"})
    sa = a.base.value("graph", KERNEL_KEY, "theta_schema")
    th = {}
    for k in sa.components:
        kind = k[0]
        if kind == "L":
            th[k] = 1e-6
        elif kind == "current":
            th[k] = 1e-5
        elif kind == "y":
            th[k] = 0.5
        elif kind == "ln_idu":
            mk = dict(a.base.column("device", "kind"))[k[1]]
            th[k] = C.Oracle.ln_idu(mk, 0.75, 0.9, 0.0)
    eva, sna = evaluate(a, th)
    va, na = report(sna)
    W("eval_A", theta=str(th), op=va, nodes=na)
    sb = b.base.value("graph", KERNEL_KEY, "theta_schema")
    thb = {}
    for k in sb.components:
        if k[0] == "ln_idu":
            mk = dict(b.base.column("device", "kind"))[k[1]]
            o = va[k[1]]
            sg = 1.0
            thb[k] = C.Oracle.ln_idu(mk, abs(o["vgs"]), abs(o["vds"]), abs(o["vsb"] or 0.0))
        else:
            thb[k] = th.get(k, 1e-6 if k[0] == "L" else 1e-5 if k[0] == "current" else 0.5)
    evb, snb = evaluate(b, thb)
    vb, nb = report(snb)
    W("eval_B", theta=str(thb), op=vb, nodes=nb)
    W("compare", dV={k: abs(na[k] - nb[k]) for k in na if k in nb and isinstance(na[k], float)},
      dop={d: {f: (None if va[d][f] is None or vb[d][f] is None else abs(va[d][f] - vb[d][f])) for f in va[d]} for d in va})
except Exception:
    W("eval_err", err=traceback.format_exc()[-1500:])


# main_path vs input role over all library + multi-view toys
LIB = pathlib.Path(ROOT) / "assets" / "library"
names = sorted(p.name[:-len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
bad = {}
for name in names:
    td0 = load_topology(str(LIB / (name + ".topology.json")))
    spec = load_sizing_spec(str(LIB / (name + ".sizing_spec.json")), td0, C.spec_catalog())
    inp = dc_inputs_from_spec(spec)
    donors, counters = open_run(); run = dict(donors=donors, counters=counters)
    s1 = build_s1(td0, dict(inp.supplies_v), **run)
    g = build_s1v(s1, spec, count_budget=10 ** 6, stop_on_unsupported=False, **run)
    views = [v for v in g.value("graph", S1V_KEY, "views") if v.kind == "transfer"]
    for v in views:
        i = {x for bb in v.blocks if bb.kind in ("gain", "composite") for x, r in bb.roles if r == "input"}
        if i - set(v.main_path):
            bad.setdefault(name, []).append((v.id, sorted(i - set(v.main_path))))
W("input_not_in_main_path", circuits=len(names), hits=bad)
out.close()
