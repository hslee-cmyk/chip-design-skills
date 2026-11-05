"""Targeted audit toys 2. usage: toys2.py <skill root> <out>"""
import json, os, pathlib, sys, tempfile, traceback
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
from gmid_engine.search import open_run
from gmid_engine.graph import build_s1, build_s1v, load_structure_facts, structure_rule_fp, GRAPH_KEY, S1V_KEY
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.sizing import DcInputs, build_kernel_context, dc_inputs_from_spec
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
cnt = [0]


def tmp():
    cnt[0] += 1
    p = td / ("t%d" % cnt[0]); p.mkdir(); return p


def W(tag, **kw):
    out.write(json.dumps({"tag": tag, **kw}, ensure_ascii=False, default=str) + "\n"); out.flush()


def build(doc, gbw=False, rout=False, settle=False, s1v=True, input_dc=None):
    donors, counters = open_run(); run = dict(donors=donors, counters=counters)
    s1 = build_s1(C.load_doc(tmp(), doc), dict(SUP), **run)
    g = build_s1v(s1, None, count_budget=10 ** 6, stop_on_unsupported=False, **run) if s1v else s1
    inp = DcInputs(tuple(sorted(SUP.items())), input_dc, has_gbw_target=gbw, has_rout_limit=rout, has_settling=settle)
    return build_kernel_context(g, inp, access, **run)


def info(ctx):
    b = ctx.base
    return dict(tc={k: v.kind for k, v in b.column("device", "theta_class")},
                dep={k: (v.relation, v.partner) for k, v in b.column("device", "dc_coord") if v.role == "dependent"},
                colour=dict(b.column("device", "dc_colour")),
                gens=[[(e, i, s) for e, i, s in g] for g in b.value("graph", GRAPH_KEY, "current_symmetry").generators],
                views=[(v.id, v.excite, [(bb.kind, bb.stage, [n for n, r in bb.roles if r == "input"]) for bb in v.blocks]) for v in b.value("graph", S1V_KEY, "views") if v.kind == "transfer"] if b.field("graph", S1V_KEY, "views") is not None else None)


def two_in(ia, ib):
    return topo("aud_two", [mos("M1", "nmos", "out", ia, "gnd"), mos("M2", "nmos", "out", ib, "x"), mos("M3", "nmos", "x", "nb", "gnd"),
                            mos("M6", "nmos", "nb", "nb", "gnd"), mos("M4", "pmos", "out", "pb", "vdd"), mos("M7", "pmos", "pb", "pb", "vdd")],
                {ia: ("input", "single_ended_input"), ib: ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb"), two("I2", "current_source", "pb", "gnd")])


for label, (ia, ib) in (("a_first", ("ia", "ib")), ("b_first", ("zz", "aa"))):
    try:
        i = info(build(two_in(ia, ib), gbw=True, input_dc=0.6))
        W("T1_multiview_name", label=label, inputs=(ia, ib), tc=i["tc"], dep=i["dep"], views=i["views"])
    except Exception:
        W("T1_multiview_name", label=label, err=traceback.format_exc()[-700:])


# dependents through S-vs-F difference: parallel group whose two members both are inputs of different views: same gate? use common input ia for M1 and a parallel M1p whose S-ness differs by view
def two_in_par(ia, ib):
    return topo("aud_two_p", [mos("M1", "nmos", "o1", ia, "gnd"), mos("M1b", "nmos", "o2", ib, "gnd"),
                              mos("B1", "pmos", "o1", "pb", "vdd"), mos("B2", "pmos", "o2", "pb", "vdd"), mos("B3", "pmos", "o2", ib, "vdd"), mos("B4", "pmos", "o1", ia, "vdd"),
                              mos("M7", "pmos", "pb", "pb", "vdd")],
                {ia: ("input", "single_ended_input"), ib: ("input", "single_ended_input"), "o1": ("output", "single_ended_output"), "o2": ("output", "single_ended_output")},
                sources=[two("I2", "current_source", "pb", "gnd")])


for label, (ia, ib) in (("a_first", ("ia", "ib")), ("b_first", ("zz", "aa"))):
    try:
        i = info(build(two_in_par(ia, ib), gbw=True, input_dc=0.6))
        W("T1b", label=label, tc=i["tc"], dep=i["dep"], views=i["views"], colour=i["colour"])
    except Exception:
        W("T1b", label=label, err=traceback.format_exc()[-700:])


def symloops(a1="A1", a2="A2", b1="B1", b2="B2"):
    return topo("aud_pairs", [mos(a1, "nmos", "n1a", "n2a", "gnd"), mos(a2, "nmos", "n1b", "n2b", "gnd"),
                              mos(b1, "nmos", "o1", "n2a", "n1a"), mos(b2, "nmos", "o2", "n2b", "n1b"),
                              mos("C1", "nmos", "n2a", "n1a", "gnd"), mos("C2", "nmos", "n2b", "n1b", "gnd"),
                              mos("P1", "pmos", "o1", "pb", "vdd"), mos("P2", "pmos", "o2", "pb", "vdd"), mos("T", "nmos", "gnd", "ip", "gnd")],
                {"ip": ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y")},
                sources=[two("I1", "current_source", "vdd", "n1a"), two("I2", "current_source", "vdd", "n1b"), two("I3", "current_source", "vdd", "n2a"), two("I4", "current_source", "vdd", "n2b")], bias=["pb"])


for k, nm in enumerate((("A1", "A2", "B1", "B2"), ("Z", "A", "Q", "R"), ("B", "Y", "C", "D"))):
    try:
        i = info(build(symloops(*nm), s1v=False))
        W("T6_symloops", names=nm, dep=i["dep"], colour=i["colour"], gens=i["gens"])
    except Exception:
        W("T6_symloops", names=nm, err=traceback.format_exc()[-500:])

# library: unrestricted vs loop-restricted downstream flag on loop B members, and main_path membership of S, rel_kvl_branch vs plan cycles
LIB = pathlib.Path(ROOT) / "assets" / "library"
names = sorted(p.name[:-len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
for name in names:
    r = {}
    try:
        topo_ = load_topology(str(LIB / (name + ".topology.json")))
        spec = load_sizing_spec(str(LIB / (name + ".sizing_spec.json")), topo_, C.spec_catalog())
        inp = dc_inputs_from_spec(spec)
        donors, counters = open_run(); run = dict(donors=donors, counters=counters)
        st = load_structure_facts(LIB / (name + ".structure.json"), topo_.connectivity_fp, structure_rule_fp(), _net_names(topo_))
        s1 = build_s1(topo_, dict(inp.supplies_v), structure=st, marks=symmetry_marks(inp), **run)
        s1 = build_s1v(s1, spec, count_budget=10 ** 6, structure=st, declared_loop_cuts=_declared_loop_cuts(spec), stop_on_unsupported=False, **run)
        ctx = build_kernel_context(s1, inp, access, **run)
        b = ctx.base
        tc = {k: v.kind for k, v in b.column("device", "theta_class")}
        views = [v for v in b.value("graph", S1V_KEY, "views") if v.kind == "transfer"]
        S = {k for k, v in tc.items() if v == "S"}
        mains = set(views[0].main_path) if views else set()
        inputs = {n for v in views[:1] for bb in v.blocks for n, ro in bb.roles if ro == "input"}
        r["S_input_not_in_main_path"] = sorted((S & inputs) - mains)
        kvl = b.value("graph", GRAPH_KEY, "rel_kvl_branch")
        r["rel_kvl_branch"] = sorted(sorted(e.members) for e in kvl)
        r["port_diff"] = sorted(sorted(e.members) for e in b.value("graph", GRAPH_KEY, "gvgs_summary").port_diff)
        r["facts"] = [(f.concept, f.subject) for f in st.facts]
        r["stale_findings"] = [f.rule for f in st.findings] if hasattr(st, "findings") else None
        r["applied"] = b.value("graph", S1V_KEY, "applied_facts")
        W("lib", circuit=name, **r)
    except StructureUnresolvedError as e:
        W("lib", circuit=name, stop=dict(e.record.detail).get("rule_branch"))
    except Exception:
        W("lib", circuit=name, err=traceback.format_exc()[-500:])
out.close()
