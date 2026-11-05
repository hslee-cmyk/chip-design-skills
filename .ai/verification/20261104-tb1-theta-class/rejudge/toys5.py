"""S-widening stress on library and full-name rename of multi-view toy. usage: toys5.py <skill root> <out>"""
import dataclasses, json, os, pathlib, sys, tempfile, traceback
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
from gmid_engine.search import open_run
from gmid_engine.graph import build_s1, build_s1v, load_structure_facts, structure_rule_fp, S1V_KEY, GRAPH_KEY
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.sizing import DcInputs, build_kernel_context, dc_inputs_from_spec, dc_writer_plan, theta_class, ThetaClass
from gmid_engine.sizing.symmetry_marks import symmetry_marks
from gmid_engine.pipeline.stage_a import _net_names, _declared_loop_cuts
from gmid_engine.core import StructureUnresolvedError
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


def coords(snap):
    return {k: (v.role, v.relation, v.partner) for k, v in snap.column("device", "dc_coord")}


def replan(ctx, inp, table):
    snap = C.tamper(ctx.base, theta_class.name, "device", "theta_class", {k: ThetaClass(v) for k, v in table.items()})
    return dc_writer_plan(snap, tuple(sorted(x for x, _ in inp.node_targets)), inp.input_dc_v is not None, donors=ctx.donors, counters=ctx.counters)


LIB = pathlib.Path(ROOT) / "assets" / "library"
names = sorted(p.name[:-len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
tot = dict(circuits=0, stop=0, all_F_to_S_dep_changed=0, each_F_to_S_changed=0, each_F_to_S_cases=0, S_to_F_dep_changed=0, B_to_S_dep_changed=0, B_to_S_cases=0, n_dep_changed=0)
for name in names:
    try:
        topo_ = load_topology(str(LIB / (name + ".topology.json")))
        spec = load_sizing_spec(str(LIB / (name + ".sizing_spec.json")), topo_, C.spec_catalog())
        inp = dc_inputs_from_spec(spec)
        donors, counters = open_run(); run = dict(donors=donors, counters=counters)
        st = load_structure_facts(LIB / (name + ".structure.json"), topo_.connectivity_fp, structure_rule_fp(), _net_names(topo_))
        s1 = build_s1(topo_, dict(inp.supplies_v), structure=st, marks=symmetry_marks(inp), **run)
        s1 = build_s1v(s1, spec, count_budget=10 ** 6, structure=st, declared_loop_cuts=_declared_loop_cuts(spec), stop_on_unsupported=False, **run)
        ctx = build_kernel_context(s1, inp, access, **run)
    except StructureUnresolvedError as e:
        tot["stop"] += 1; W("lib", circuit=name, stop=dict(e.record.detail).get("rule_branch")); continue
    tot["circuits"] += 1
    tc = {k: v.kind for k, v in ctx.base.column("device", "theta_class")}
    co = coords(ctx.base)
    dep = lambda cc: {k for k, v in cc.items() if v[0] == "dependent"}
    # (a) all F -> S: union widening worst case (S/F only)
    cc = coords(replan(ctx, inp, {k: ("S" if v == "F" else v) for k, v in tc.items()}))
    ch = sorted(dep(cc) ^ dep(co))
    tot["all_F_to_S_dep_changed"] += bool(ch)
    tot["n_dep_changed"] += len(dep(cc)) != len(dep(co))
    # (b) one F -> S at a time
    each = []
    for d in [k for k, v in tc.items() if v == "F"]:
        tot["each_F_to_S_cases"] += 1
        c2 = coords(replan(ctx, inp, {**tc, d: "S"}))
        if dep(c2) != dep(co):
            tot["each_F_to_S_changed"] += 1; each.append((d, sorted(dep(c2) ^ dep(co))))
    # (c) what the concern is: B -> S (a load that is input in another view) -- what would change if B set shrank
    bs = []
    for d in [k for k, v in tc.items() if v == "B"]:
        tot["B_to_S_cases"] += 1
        c2 = coords(replan(ctx, inp, {**tc, d: "S"}))
        tot["n_dep_changed"] += len(dep(c2)) != len(dep(co))
        if dep(c2) != dep(co):
            tot["B_to_S_dep_changed"] += 1; bs.append((d, sorted(dep(c2) - dep(co)), sorted(dep(co) - dep(c2))))
    W("lib", circuit=name, all_F_to_S=ch, each=each, B_to_S=bs, n_F=sum(v == "F" for v in tc.values()), n_B=sum(v == "B" for v in tc.values()))
W("lib_total", **tot)


# full-name rename of multi-view toy (nets + elements)
def two_in(ia="ia", ib="ib"):
    return topo("aud_two", [mos("M1", "nmos", "out", ia, "gnd"), mos("M2", "nmos", "out", ib, "x"), mos("M3", "nmos", "x", "nb", "gnd"),
                            mos("M6", "nmos", "nb", "nb", "gnd"), mos("M4", "pmos", "out", "pb", "vdd"), mos("M7", "pmos", "pb", "pb", "vdd")],
                {ia: ("input", "single_ended_input"), ib: ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb"), two("I2", "current_source", "pb", "gnd")])


def build(doc, sup):
    donors, counters = open_run(); run = dict(donors=donors, counters=counters)
    s1 = build_s1(C.load_doc(tmp(), doc), dict(sup), **run)
    g = build_s1v(s1, None, count_budget=10 ** 6, stop_on_unsupported=False, **run)
    return build_kernel_context(g, DcInputs(tuple(sorted(sup.items())), 0.6, has_gbw_target=True), access, **run)


raw = two_in()
a = build(raw, SUP)
ta = {k: v.kind for k, v in a.base.column("device", "theta_class")}
da = {k for k, v in coords(a.base).items() if v[0] == "dependent"}
res = []
for seed in range(1, 11):
    d2, sn, se = C.rename(raw, seed)
    b = build(d2, {sn[k]: v for k, v in SUP.items()})
    tb = {k: v.kind for k, v in b.base.column("device", "theta_class")}
    db = {k for k, v in coords(b.base).items() if v[0] == "dependent"}
    res.append(({se[k]: v for k, v in ta.items()} == tb, {se[k] for k in da} == db))
W("T1_full_rename", base=ta, dep=sorted(da), tc_equal=sum(r[0] for r in res), dep_equal=sum(r[1] for r in res), n=len(res))
out.close()
