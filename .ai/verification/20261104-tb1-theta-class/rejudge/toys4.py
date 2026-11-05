"""Re-judge toys: union rule with gain constraint on part of views. usage: toys4.py <skill root> <out>"""
import json, os, pathlib, sys, tempfile, traceback, types
ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, ROOT)
from gmid_engine.search import open_run
from gmid_engine.graph import build_s1, build_s1v, GRAPH_KEY, S1V_KEY
from gmid_engine.sizing import DcInputs, build_kernel_context, dc_writer_plan, theta_class, ThetaClass
from gmid_engine.authoring.spec_model import ConstraintDecl, ViewDecl, ExciteSense, SenseDecl
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


def port_view(weights, sense):
    return ViewDecl(mode="port", weights=weights, sense=SenseDecl(sense, None, "single_ended"))


def transfer_view(excite, sense):
    return ViewDecl(mode="transfer", transfer=ExciteSense(excite, sense, None, "single_ended"))


def build(doc, cons, gbw=True, input_dc=None, rout=False, targets=()):
    donors, counters = open_run(); run = dict(donors=donors, counters=counters)
    s1 = build_s1(C.load_doc(tmp(), doc), dict(SUP), **run)
    spec = types.SimpleNamespace(judged_constraints=cons)
    g = build_s1v(s1, spec, count_budget=10 ** 6, stop_on_unsupported=False, **run)
    inp = DcInputs(tuple(sorted(SUP.items())), input_dc, targets, has_gbw_target=gbw, has_rout_limit=rout)
    return build_kernel_context(g, inp, access, **run), inp


def analyse(tag, doc, cons, gain_excite, **kw):
    ctx, inp = build(doc, cons, **kw)
    b = ctx.base
    views = [v for v in b.value("graph", S1V_KEY, "views") if v.kind == "transfer"]
    tc = {k: v.kind for k, v in b.column("device", "theta_class")}
    co = {k: (v.role, v.relation, v.partner) for k, v in b.column("device", "dc_coord")}
    gain_inputs = {n for v in views if tuple(v.excite) == tuple(gain_excite) for bb in v.blocks if bb.kind in ("gain", "composite") for n, r in bb.roles if r == "input"}
    roles = {n: sorted({(v.id, r) for v in views for bb in v.blocks for nn, r in bb.roles if nn == n}) for n in tc}
    narrow = {n: ("S" if n in gain_inputs else ("F" if tc[n] == "S" else tc[n])) for n in tc}
    # rout followers remain S in both
    snap = C.tamper(b, theta_class.name, "device", "theta_class", {n: ThetaClass(k) for n, k in narrow.items()})
    s2 = dc_writer_plan(snap, tuple(n for n, _ in inp.node_targets), inp.input_dc_v is not None, donors=ctx.donors, counters=ctx.counters)
    co2 = {k: (v.role, v.relation, v.partner) for k, v in s2.column("device", "dc_coord")}
    dep = sorted(k for k, v in co.items() if v[0] == "dependent")
    dep2 = sorted(k for k, v in co2.items() if v[0] == "dependent")
    W(tag, views=[(v.id, v.excite, v.sense) for v in views], wide=tc, narrow=narrow, widened=sorted(n for n in tc if tc[n] != narrow[n]),
      dep_wide={k: co[k][1:] for k in dep}, dep_narrow={k: co2[k][1:] for k in dep2}, dep_same=dep == dep2, n_dep=(len(dep), len(dep2)), roles=roles)


def tagged(fn, *a, **k):
    try:
        fn(*a, **k)
    except Exception:
        W(a[0], err=traceback.format_exc()[-900:])


GAIN = "gain_ss_db"


def con(metric, view):
    return ConstraintDecl(metric, ">=", 1.0, True, view, None)


# Q: two inputs, gain only on ia view; ib view default
def two_in(ia="ia", ib="ib"):
    return topo("aud_two", [mos("M1", "nmos", "out", ia, "gnd"), mos("M2", "nmos", "out", ib, "x"), mos("M3", "nmos", "x", "nb", "gnd"),
                            mos("M6", "nmos", "nb", "nb", "gnd"), mos("M4", "pmos", "out", "pb", "vdd"), mos("M7", "pmos", "pb", "pb", "vdd")],
                {ia: ("input", "single_ended_input"), ib: ("input", "single_ended_input"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb"), two("I2", "current_source", "pb", "gnd")])


tagged(analyse, "Q_two_in_gain_ia", two_in(), (con(GAIN, port_view((("ia", 1.0),), "out")),), (("ia", 1.0),), input_dc=0.6)
tagged(analyse, "Q_two_in_gain_ib", two_in(), (con(GAIN, port_view((("ib", 1.0),), "out")),), (("ib", 1.0),), input_dc=0.6)


# P: 5T OTA + PSRR-like transfer view excited from rail
def ota5():
    return topo("aud_ota", [mos("M1", "nmos", "x", "inp", "t"), mos("M2", "nmos", "out", "inn", "t"), mos("M5", "nmos", "t", "nb", "gnd"),
                            mos("M6", "nmos", "nb", "nb", "gnd"), mos("M3", "pmos", "x", "x", "vdd"), mos("M4", "pmos", "out", "x", "vdd")],
                {"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"), "out": ("output", "single_ended_output")},
                sources=[two("I1", "current_source", "vdd", "nb")])


DIFF = (("inn", -0.5), ("inp", 0.5))
tagged(analyse, "P_ota_psrr_vdd", ota5(), (con(GAIN, port_view(DIFF, "out")), con("psrr_ss_db", transfer_view((("vdd", 1.0),), "out"))), DIFF)
tagged(analyse, "P_ota_cm_view", ota5(), (con(GAIN, port_view(DIFF, "out")), con("cmrr_ss_db", transfer_view((("inn", 0.5), ("inp", 0.5)), "out"))), DIFF)


# R: loop with non-B input in the extra view, parallel pair sharing gate where only one is `input`-role in the non-gain view (selection-sensitive)
def rtoy(ia="ia", ib="ib"):
    return topo("aud_r", [mos("A", "nmos", "o1", ib, "gnd"), mos("A2", "nmos", "o2", ib, "gnd"), mos("Pa", "pmos", "o1", "pb", "vdd"), mos("Pb", "pmos", "o2", "pb", "vdd"),
                          mos("G", "nmos", "o3", ia, "gnd"), mos("Pc", "pmos", "o3", "pb", "vdd"), mos("D", "pmos", "pb", "pb", "vdd"), mos("Q", "nmos", "o2", "vb", "gnd"), mos("Qb", "nmos", "vb", "vb", "gnd")],
                {ia: ("input", "single_ended_input"), ib: ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y"), "o3": ("output", "y")},
                sources=[two("I1", "current_source", "pb", "gnd"), two("I2", "current_source", "vdd", "vb")])


tagged(analyse, "R_parallel", rtoy(), (con(GAIN, port_view((("ia", 1.0),), "o3")),), (("ia", 1.0),), input_dc=0.6)


# S: same-gate parallel pair with one in a follower/buffer path (role differs) under declared non-gain view; no input DC so input net floats
def stoy():
    return topo("aud_s", [mos("M1", "nmos", "o1", "ib", "s1"), mos("M1p", "nmos", "o2", "ib", "s1"), mos("Mt", "nmos", "s1", "vb", "gnd"), mos("Qb", "nmos", "vb", "vb", "gnd"),
                          mos("P1", "pmos", "o1", "pb", "vdd"), mos("P2", "pmos", "o2", "pb", "vdd"), mos("D", "pmos", "pb", "pb", "vdd"),
                          mos("G", "nmos", "o3", "ia", "s1"), mos("P3", "pmos", "o3", "pb", "vdd")],
                {"ia": ("input", "single_ended_input"), "ib": ("input", "single_ended_input"), "o1": ("output", "y"), "o2": ("output", "y"), "o3": ("output", "y")},
                sources=[two("I1", "current_source", "pb", "gnd"), two("I2", "current_source", "vdd", "vb")])


tagged(analyse, "S_shared_tail", stoy(), (con(GAIN, port_view((("ia", 1.0),), "o3")),), (("ia", 1.0),), input_dc=0.6)
out.close()
