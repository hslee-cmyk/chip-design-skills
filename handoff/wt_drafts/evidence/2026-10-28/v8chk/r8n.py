"""독립 검증 8: E-31·E-32 발동 재현(엔진 import만). 회로마다 append."""
import json, os, sys, traceback
from pathlib import Path
ENG = Path(sys.argv[1]); OUT = Path(sys.argv[2])
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
sys.path.insert(0, str(ENG)); sys.path.insert(0, str(ENG / "gmid_engine" / "tests" / "integration"))
import types
pt = types.ModuleType("pytest")
pt.fixture = lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
class _M:
    def __getattr__(self, n): return lambda *a, **k: (a[0] if a and callable(a[0]) else (lambda f: f))
pt.mark = _M(); sys.modules.setdefault("pytest", pt)
import test_s0_layer_9circuits as T
from types import SimpleNamespace
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.pipeline import run_stage_a, run_stage_b
from gmid_engine.search import open_run
loc = resolve_lut_location(str(T.SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(T.DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
pdk = read_pdk_decl(str(T.SKILL / "assets" / "sky130_pdk_decl.json"), BoundedLRU(16)); q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), T.DEVICE_KINDS, T.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
env = SimpleNamespace(lut=lut, pdk=pdk, root=OUT.parent / "runs")
def field(snap, name):
    for k in snap.kinds():
        for key in snap.keys(k):
            r = snap.record(k, key)
            if name in r.field_names(): return r.get(name).value
    return "ABSENT"
for c in ["nmcnr_amplifier"]:
    row = {"circuit": c}
    try:
        donors, counters = open_run()
        a = run_stage_a(T.LIBRARY / (c + ".topology.json"), T.LIBRARY / (c + ".sizing_spec.json"), lut, output_dir=env.root / c, donors=donors, counters=counters)
        env.memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
        b = run_stage_b(a, env.memo, pdk, output_dir=env.root / c, diagnostic=True, settings=T._settings())
        env.rule = read_pdk_decl(str(T.SKILL / "assets" / "sky130_lut_rule_decl.json"), BoundedLRU(4))
        sctx = T._search_context(env, a, b)
        row["sctx_rungs"] = None if sctx.rungs is None else len(sctx.rungs)
        base = sctx.dc.base
        rungs = field(base, "rungs"); row["field_rungs"] = rungs if rungs == "ABSENT" else len(rungs)
        m = field(base, "macro")
        recs = getattr(m, "records", ()) if m not in (None, "ABSENT") else ()
        row["macro_records"] = [[str(code), [list(map(str, d)) for d in det]] for code, det in recs]
        row["start_records"] = repr(field(base, "records"))[:600]
        cf = field(base, "conflicts"); row["conflicts"] = [repr(x)[:240] for x in (cf or ())]
        row["inactive"] = repr(field(base, "inactive"))[:300]
        row["uncovered"] = repr(field(base, "uncovered"))[:300]
    except Exception:
        row["error"] = traceback.format_exc()[-900:]
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=repr) + "\n")
