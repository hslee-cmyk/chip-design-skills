import sys, json
from fractions import Fraction
from pathlib import Path
SKILL = Path(sys.argv[1]); OUT = Path(sys.argv[2]); sys.path.insert(0, str(SKILL))
from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.core import MetricSignature
from gmid_engine.graph import build_s1, build_s1v, s1_symmetry, supplies_declaration, ELEMENT_SOURCE, s1v_findings
from gmid_engine.metrics import metric_catalog
from gmid_engine.search import open_run
from gmid_engine.sizing import dc_inputs_from_spec, DC_KEY
from gmid_engine.sizing.current_basis import dc_current_basis
from gmid_engine.sizing.s2_lift import lift_s1
from gmid_engine.sizing.w0_rails import dc_rails
from gmid_engine.sizing.symmetry_marks import symmetry_marks
from gmid_engine.sizing.s2_values import CURRENT_SOURCE

cat = dict(metric_catalog())
for n, sig in (("mismatch_sigma_mv", ("mv", "dc")), ("mirror_ratio_error_mv", ("mv", "dc")),
               ("area_layout_m2", ("m2", "geom", None, "area"))):
    cat.setdefault(n, MetricSignature(*sig))


def rank(vs):
    M = [list(v) for v in vs]; r = 0
    if not M:
        return 0
    for c in range(len(M[0])):
        p = next((i for i in range(r, len(M)) if M[i][c] != 0), None)
        if p is None:
            continue
        M[r], M[p] = M[p], M[r]
        for i in range(len(M)):
            if i != r and M[i][c] != 0:
                f = M[i][c] / M[r][c]
                M[i] = [a - f * b for a, b in zip(M[i], M[r])]
        r += 1
    return r


OUT.write_text("", encoding="utf-8")
for d in ("library", "heldout"):
    D = SKILL / "assets" / d
    for sp in sorted(D.glob("*.sizing_spec.json")):
        name = sp.name[:-len(".sizing_spec.json")]
        rec = {"set": d, "circuit": name}
        stxt = sp.read_text(encoding="utf-8")
        ttxt = (D / (name + ".topology.json")).read_text(encoding="utf-8")
        rec["pm_cm_in_spec"] = "pm_cm_ss_deg" in stxt
        rec["diff_out_role_in_topo"] = "differential_output_p" in ttxt
        try:
            td = load_topology(str(D / (name + ".topology.json")))
            spec = load_sizing_spec(str(sp), td, cat)
            inputs = dc_inputs_from_spec(spec)
            donors, counters = open_run()
            s1 = build_s1(td, dict(inputs.supplies_v), donors=donors, counters=counters)
            pins = dict(s1.column("device", "pins"))
            kinds = dict(s1.column("device", "kind"))
            classes = dict(s1.column("device", "element_class"))
            gs = []
            for n, p in pins.items():
                try:
                    pd = dict(p)
                except Exception:
                    continue
                if "g" in pd and "s" in pd and pd["g"] == pd["s"]:
                    gs.append(n)
            rec["g_eq_s"] = gs
            rails = frozenset(n for n, r in s1.column("node", "is_rail") if r)
            sup = supplies_declaration(dict(inputs.supplies_v), rails)
            vals = dict(inputs.element_values)
            srcs = tuple((n, vals.get(n)) for n in sorted(classes)
                         if classes[n] == ELEMENT_SOURCE and kinds[n] == CURRENT_SOURCE)
            b = lift_s1(s1)
            b = dc_rails(b, sup, donors=donors, counters=counters)
            b = s1_symmetry(b, sup, symmetry_marks(inputs), donors=donors, counters=counters)
            b = dc_current_basis(b, srcs, donors=donors, counters=counters)
            basis = b.value("graph", DC_KEY, "dc_current_basis")
            groups = s1.value("graph", "s1", "rel_matching_ratio")
            coords = list(basis.free) + [n for n, _ in basis.fixed]
            idx = {n: i for i, n in enumerate(coords)}
            rows = dict(basis.rows)

            def vec(n):
                v = [Fraction(0)] * len(coords)
                for t in rows.get(n, ()):
                    v[idx[t.source]] += Fraction(t.num, t.den)
                return v
            rec["n_free"] = len(basis.free)
            rec["groups"] = [[len(g.members), rank([vec(m) for m in g.members])] for g in groups]
            try:
                v = build_s1v(s1, spec, count_budget=10 ** 6, stop_on_unsupported=False, donors=donors, counters=counters)
                fs = s1v_findings(v)
                codes = set()
                for grp in fs:
                    for f in grp:
                        codes.add(getattr(f, "code", repr(f)))
                rec["s1v_codes"] = sorted(codes)
            except Exception as e:
                rec["s1v_err"] = type(e).__name__ + ": " + str(e)[:200]
        except Exception as e:
            rec["error"] = type(e).__name__ + ": " + str(e)[:300]
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
print("done")
