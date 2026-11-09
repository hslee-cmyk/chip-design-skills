import json, os, sys, traceback
from pathlib import Path
exec(open(sys.argv[3], encoding="utf-8").read().split("def main():")[0])
from gmid_engine.lut import LutMemo
OUT = Path(sys.argv[2])
env = make_env(OUT.parent / "runs")
names = sorted(p.name[:-len(".sizing_spec.json")] for p in T.LIBRARY.glob("*.sizing_spec.json"))
for circuit in names:
    row = {"circuit": circuit}
    try:
        donors, counters = open_run()
        out = env.root / circuit
        a = run_stage_a(T.LIBRARY / (circuit + ".topology.json"), T.LIBRARY / (circuit + ".sizing_spec.json"), env.lut,
                        output_dir=out, donors=donors, counters=counters)
        env.memo = LutMemo(env.lut, point=1 << 14, curve=1 << 12, root=1 << 14)
        b = run_stage_b(a, env.memo, env.pdk, output_dir=out, diagnostic=True, settings=T._settings())
        env.rule = read_pdk_decl(str(T.SKILL / "assets" / "sky130_lut_rule_decl.json"), BoundedLRU(4))
        sctx = T._search_context(env, a, b)
        row["rungs_len"] = len(sctx.rungs) if sctx.rungs is not None else None
        r = find_field(sctx.dc.base, "macro")
        m = r[2].value if r else None
        recs = getattr(m, "records", ()) if m is not None else ()
        row["macro_records"] = [str(c[0]) for c in recs]
        row["macro_root_missing"] = sum(1 for c in recs if str(c[0]) == "macro_root_missing")
        rc = find_field(sctx.dc.base, "conflicts")
        row["start_conflicts"] = len(rc[2].value) if rc and rc[2].value is not None else None
    except Exception:
        row["error"] = traceback.format_exc()[-800:]
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=repr) + "\n")
