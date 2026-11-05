"""사용: dump_s0_rows.py <skill 루트> <out.json> <회로>. start.row·edge_costs·reference_vds 를 쓴다(판정자 측정, 엔진 쓰기 없음)."""
import dataclasses, json, os, sys, tempfile
from pathlib import Path
from types import SimpleNamespace

skill = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2])
circuit = sys.argv[3]
sys.path[:0] = [str(skill), str(skill / "gmid_engine" / "tests"), str(skill / "gmid_engine" / "tests" / "integration")]
import test_s0_layer_9circuits as t  # noqa: E402

from gmid_engine.core import BoundedLRU, read_pdk_decl  # noqa: E402
from gmid_engine.lut import LutMemo, LutSpec, derived, load_lut_set, resolve_lut_location  # noqa: E402
import gmid_engine.lut as L  # noqa: E402

assert str(skill).lower().replace("\\", "/") in str(Path(t.__file__).resolve()).lower().replace("\\", "/")
loc = resolve_lut_location(str(skill / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(t.DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(skill / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), t.DEVICE_KINDS, t.CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
env = SimpleNamespace(lut=lut, pdk=pdk, rule=read_pdk_decl(str(skill / "assets" / "sky130_lut_rule_decl.json"), dm),
                      root=Path(tempfile.mkdtemp(prefix="d_", dir=str(out.parent))), runs={})
res = {"file": str(Path(L.__file__).resolve()), "circuit": circuit}
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
res["luts"] = {}
for (kind, w_key), sl in lut.slice_map.items():
    row = {"slice_has_VDSAT": "VDSAT" in sl.columns, "w_m": sl.w_m}
    cap = lut.cap_map.get(kind)
    row["cap_w_key_same"] = None if cap is None else cap.w_key == w_key
    row["cap_has_VDSAT"] = None if cap is None else "VDSAT" in cap.columns
    if cap is not None:
        row["cap_grid_eq_slice"] = [len(a) == len(b) and all(float(x) == float(y) for x, y in zip(a, b)) for a, b in zip(cap.grids, sl.grids)]
    ec = derived(memo, "edge_costs", kind, w_key)
    row["edge"] = {"vds_min_v": ec.vds_min_v, "vgs_min_v": ec.vgs_min_v, "by_bin": ec.vgs_min_by_bin if hasattr(ec, "vgs_min_by_bin") else None}
    row["ref_vds"] = {str(float(a)): derived(memo, "reference_vds", kind, w_key, float(a)) for a in sl.grids[0][:4]}
    res["luts"]["%s/%s" % (kind, w_key)] = row
run = t._chain(env, circuit, "first")
res["status"] = run.status
if run.base is not None:
    base = run.base
    rows = {}
    for dev in sorted(t._baseline(circuit)["start"]["row_fp"]):
        f = base.field("device", dev, "start.row")
        rows[dev] = {"fp": None if f is None else f.value_fp, "baseline_fp": t._baseline(circuit)["start"]["row_fp"][dev], "value": repr(None if f is None else f.value),
                     "point": repr(base.field("device", dev, "start.point").value)}
    res["rows"] = rows
    res["graph_start"] = {}
    for k in ("rungs", "conflicts", "inactive", "macro", "records", "area_est_m2", "area_fraction", "uncovered"):
        fv = base.field("graph", "start", k)
        res["graph_start"][k] = {"fp": None if fv is None else fv.value_fp}
    res["inactive"] = repr(base.field("graph", "start", "inactive").value)
    res["conflicts"] = repr(base.field("graph", "start", "conflicts").value)
out.write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
print("done", out)
