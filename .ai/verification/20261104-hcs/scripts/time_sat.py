"""실제 LUT: sat_threshold 와 vdsat 호출당 시간, 그리고 슬라이스 전수 사실(열 출처, 격자 입구 예외). 무거운 탐색 없음."""
import json, os, sys, time
from pathlib import Path
skill = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(skill), str(skill / "gmid_engine" / "tests"), str(skill / "gmid_engine" / "tests" / "integration")]
import test_s0_layer_9circuits as t  # noqa
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location, sat_threshold, sat_threshold_grid, vdsat, derived, tol_vdsat_table
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
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path, noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
n_ok = n_none = n_raise = 0
for (kind, w_key) in lut.slice_map:
    try:
        g = sat_threshold_grid(memo, kind, w_key)
        n_ok += g is not None
        n_none += g is None
    except Exception as exc:
        n_raise += 1
        print("raise", kind, w_key, exc)
print("grid entrance ok/none/raise", n_ok, n_none, n_raise, "of", len(lut.slice_map))
kind, w_key = "nmos", 1000
sl = lut.slice_map[(kind, w_key)]
L = float(sl.grids[0][10])
pts = [(0.3 + 0.0007 * i, 0.5 + 0.0003 * i, 0.0 + 0.0001 * i) for i in range(2000)]
tol_vdsat_table(memo, kind, w_key)
t0 = time.perf_counter()
for p in pts:
    vdsat(memo, kind, w_key, L, *p)
t1 = time.perf_counter()
for p in pts:
    sat_threshold(memo, kind, w_key, L, *p)
t2 = time.perf_counter()
for p in pts:
    vdsat(memo, kind, w_key, L, *p)
t3 = time.perf_counter()
print("per call us: vdsat first %.1f, sat_threshold (vdsat cached) %.1f, vdsat cached %.1f" % ((t1 - t0) / len(pts) * 1e6, (t2 - t1) / len(pts) * 1e6, (t3 - t2) / len(pts) * 1e6))
print(sat_threshold(memo, kind, w_key, L, *pts[0]))
