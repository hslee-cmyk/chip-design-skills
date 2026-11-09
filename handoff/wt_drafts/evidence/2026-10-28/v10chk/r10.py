"""독립 검증 10: E-31 후보 단위 재현. _placed 호출마다 (t, refine, macro_failed, 기록 조건). 엔진 import만, 회로마다 append."""
import json, os, sys, traceback, types
from pathlib import Path
ENG = Path(sys.argv[1]); OUT = Path(sys.argv[2])
sys.path.insert(0, str(ENG)); sys.path.insert(0, str(ENG / "gmid_engine" / "tests" / "integration"))
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
SI = sys.modules.get("gmid_engine.search.start_intervals") or __import__("gmid_engine.search.start_intervals", fromlist=["x"])
LOG = []
_orig = SI._placed
def _wrap(ctx, g, L, refine=True):
    st = _orig(ctx, g, L, refine)
    f = sys._getframe(1); t = f.f_locals.get("x") if f.f_code.co_name == "solve" else None
    caller = sys._getframe(2).f_code.co_name if f.f_code.co_name == "solve" else f.f_code.co_name
    conds = []
    for c, d in getattr(st.macro, "records", ()):
        dd = dict(d) if not isinstance(d, dict) else d
        conds.append((str(c), dd.get("condition")))
    LOG.append({"t": t, "caller": caller, "refine": bool(refine), "macro_failed": bool(st.macro_failed), "area": st.area, "recs": conds})
    return st
SI._placed = _wrap
circs = sys.argv[3].split(",")
for c in circs:
    row = {"circuit": c}; LOG.clear()
    try:
        donors, counters = open_run()
        a = run_stage_a(T.LIBRARY / (c + ".topology.json"), T.LIBRARY / (c + ".sizing_spec.json"), lut, output_dir=env.root / c, donors=donors, counters=counters)
        env.memo = LutMemo(lut, point=1 << 14, curve=1 << 12, root=1 << 14)
        b = run_stage_b(a, env.memo, pdk, output_dir=env.root / c, diagnostic=True, settings=T._settings())
        env.rule = read_pdk_decl(str(T.SKILL / "assets" / "sky130_lut_rule_decl.json"), BoundedLRU(4))
        sctx = T._search_context(env, a, b)
        row["rung_t"] = None if sctx.rungs is None else [r.t for r in sctx.rungs]
    except Exception:
        row["error"] = traceback.format_exc()[-900:]
    row["calls"] = list(LOG)
    with OUT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=repr) + "\n")
