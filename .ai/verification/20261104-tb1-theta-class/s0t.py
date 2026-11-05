"""S0 table on product path (no LUT eval, no ngspice). usage: s0t.py <skill root> <outfile>"""
import json, sys, os, tempfile, pathlib, traceback
ROOT = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, ROOT)
from gmid_engine.search import open_run
from gmid_engine.graph import build_s1, build_s1v, load_structure_facts, structure_rule_fp, S1V_KEY, GRAPH_KEY
from gmid_engine.authoring import load_topology, load_sizing_spec
from gmid_engine.sizing import dc_inputs_from_spec, build_kernel_context
from gmid_engine.sizing.symmetry_marks import symmetry_marks
from gmid_engine.core import StructureUnresolvedError
from gmid_engine.pipeline.stage_a import _net_names, _declared_loop_cuts
from gmid_engine.tests.sizing import conftest as C
from gmid_engine.lut import load_lut_set

td = pathlib.Path(tempfile.mkdtemp(dir=os.path.dirname(OUT)))
m, c = C.write_toy_lut(td / "lut")
access = C.new_access(load_lut_set(str(m), str(c), C.TOY_SPEC))
LIB = pathlib.Path(ROOT) / "assets" / "library"
names = sorted(p.name[:-len(".topology.json")] for p in LIB.glob("*.topology.json") if not p.name.startswith("_"))
out = open(OUT, "w", encoding="utf8")


def row(d):
    out.write(json.dumps(d, ensure_ascii=False, default=str) + "\n"); out.flush()


for name in names:
    r = {"circuit": name}
    try:
        topo = load_topology(str(LIB / (name + ".topology.json")))
        spec = load_sizing_spec(str(LIB / (name + ".sizing_spec.json")), topo, C.spec_catalog())
        inp = dc_inputs_from_spec(spec)
        donors, counters = open_run(); run = dict(donors=donors, counters=counters)
        sp = LIB / (name + ".structure.json")
        st = load_structure_facts(sp, topo.connectivity_fp, structure_rule_fp(), _net_names(topo))
        r["facts"] = len(st.facts)
        s1 = build_s1(topo, dict(inp.supplies_v), structure=st, marks=symmetry_marks(inp), **run)
        s1 = build_s1v(s1, spec, count_budget=10 ** 6, structure=st, declared_loop_cuts=_declared_loop_cuts(spec), stop_on_unsupported=False, **run)
        views = s1.value("graph", S1V_KEY, "views")
        tv = [v for v in views if v.kind == "transfer"]
        r["n_transfer"] = len(tv)
        r["has"] = dict(gbw=getattr(inp,"has_gbw_target",None), rout=getattr(inp,"has_rout_limit",None), settle=getattr(inp,"has_settling",None))
        r["views"] = [(v.id, v.excite, v.sense, [(b.kind, [n for n, ro in b.roles if ro == "input"]) for b in v.blocks]) for v in tv]
        r["gain_constraints"] = [(x.metric, None if x.view is None else str(x.view)[:200]) for x in spec.judged_constraints if x.metric == "gain_ss_db"]
        ctx = build_kernel_context(s1, inp, access, **run)
        b = ctx.base
        try:
            tc = {k: v.kind for k, v in b.column("device", "theta_class")}
        except Exception:
            tc = {k: "?" for k, c0 in b.column("device", "element_class") if c0 == "mos"}
        co = dict(b.column("device", "dc_coord"))
        r["theta"] = {k: sorted(n for n, v in tc.items() if v == k) for k in "SFB"}
        rel = {}
        for n, cc in sorted(co.items()):
            if cc.role == "dependent":
                rel.setdefault(cc.relation, []).append((n, cc.partner) if cc.partner else n)
        r["dependent"] = rel
        pins = {k: dict(v) for k, v in b.column("device", "pins")}
        cls = dict(b.column("device", "element_class"))
        writes = dict(b.column("node", "dc_writer"))
        fixed = {n for n, w in writes.items() if w.relation in ("rail", "target", "input_dc", "node_target")}
        r["fixed"] = sorted(fixed)
        r["relations"] = sorted({w.relation for w in writes.values()})
        al = {}
        for n, w in writes.items():
            if w.relation == "input_point" and w.known:
                al[n] = w.known; al.setdefault(w.known, w.known)

        def V2(n):
            n = "F" if n in fixed else n
            return al.get(n, n)
        tree = []
        for n, cc in co.items():
            if cc.role == "writer":
                tree.append((n, pins[n]["g"], pins[n]["s"]))
        writers = {w.element for w in writes.values()}
        for n, k in cls.items():
            if k == "passive" and n in writers:
                ts = list(pins[n].values()); tree.append((n, ts[0], ts[1]))
        adj = {}
        for n, a, b2 in tree:
            adj.setdefault(V2(a), []).append((V2(b2), n)); adj.setdefault(V2(b2), []).append((V2(a), n))
        loops = []
        twin_of = {t: cc2.partner for t, cc2 in co.items() if cc2.relation == "parallel_vgs"}
        for n, cc in sorted(co.items()):
            if cc.role == "dependent" and cc.relation == "cycle_vgs":
                a, bb = V2(pins[n]["g"]), V2(pins[n]["s"])
                prev = {a: None}; q = [a]
                for u in q:
                    for v, e in adj.get(u, ()):
                        if v not in prev:
                            prev[v] = (u, e); q.append(v)
                mem = []; h = bb
                while prev.get(h) is not None:
                    mem.append(prev[h][1]); h = prev[h][0]
                ms = [x for x in mem if x in tc]
                loops.append({"dep": n, "dep_class": tc[n], "members": {x: tc[x] for x in ms}, "reached": bb in prev,
                              "members_with_twins": {x: [t for t, p in twin_of.items() if p == x] for x in ms if any(p == x for p in twin_of.values())},
                              "B_rule_ok": tc[n] == "B" or not any(tc[x] == "B" for x in ms)})
        r["loops"] = loops
        sg = b.value("graph", GRAPH_KEY, "current_symmetry")
        dep = {n for n, cc in co.items() if cc.role == "dependent" and cc.relation == "cycle_vgs"}
        viol = []
        for g in sg.generators:
            mp = {e: i for e, i, _ in g}
            img = {mp.get(x, x) for x in dep}
            if img != dep:
                viol.append(sorted(img ^ dep))
        r["cycle_dep_not_closed_under_generator"] = viol
        r["ok"] = True
    except StructureUnresolvedError as e:
        r["stop"] = str(getattr(e, "record", e))[:400]
    except Exception:
        r["error"] = traceback.format_exc()[-1500:]
    row(r)
