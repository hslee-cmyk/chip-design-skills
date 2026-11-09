"""검증2: m4 seq의 슬라이스 키 의미 확인 -- slice_map (kind, key) -> w_m, L별 w_bin(첫 L bin)."""
import sys, os, json
sys.dont_write_bytecode = True
SKILL_S = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/integ-it12/skills/analog-gmid-design"
sys.path.insert(0, SKILL_S)
sys.path.append("C:/Users/HSLEE/AppData/Roaming/Python/Python314/site-packages")
from pathlib import Path
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location
SKILL = Path(SKILL_S)
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds_map = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds_map[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds_map[e["device"]], float("inf")))
GRID = float(man.get("manufacturing_grid_m", 5e-9))
dm = BoundedLRU(16); pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm); q = dict(pdk.quantities)
spec_l = LutSpec(GRID, tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
                 noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec_l, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
for (kd, key), sl in sorted(lut.slice_map.items(), key=lambda t: (t[0][0], t[1].w_m)):
    wb = sl.l_bins.w_bin if (sl.l_bins and sl.l_bins.bins) else None
    print(kd, key, sl.w_m, wb)
