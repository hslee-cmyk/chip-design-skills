"""엔진 LUT 조회 직접 확인 (읽기 전용 import). 봉인점 (vgs, vds, vsb) 에서 op_point·vdsat, ln_idu 역산 vgs."""
import json, math, os, sys
from pathlib import Path
SKILL = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_it2c\src\skills\analog-gmid-design")
sys.path.insert(0, str(SKILL))
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.lut.point_query import op_point
from gmid_engine.lut.vdsat_query import vdsat
from gmid_engine.lut.vgs_current_density import vgs_for_current_density
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
memo = LutMemo(lut, point=1000, curve=1000, root=1000)
out = {}
for k, sl in lut.slice_map.items():
    if k[1] == 1000:
        print("slice", k, "w_m", sl.w_m, "grids", [len(g) for g in sl.grids], "VS", list(sl.grids[3]), "cols", sorted(sl.columns))
for name in sys.argv[1:]:
    eng = json.loads(Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\evidence\2026-10-22\it2c_spice_frame\engine\%s.engine.json" % name).read_text(encoding="utf-8"))
    for m, op in eng["device_cols"]["dc_op"].items():
        k, wk = op["kind"], op["w_key"]
        p = op_point(memo, k, wk, op["L"], op["vgs"], op["vds"], op["vsb"])
        vs = vdsat(memo, k, wk, op["L"], op["vgs"], op["vds"], op["vsb"])
        vg = vgs_for_current_density(memo, k, wk, op["ln_idu"], op["L"], op["vds"], op["vsb"])
        idu = op["current"] * op["L"] / op["W"]
        rec = {"idu_fwd_engine_query": p.IDu, "idu_from_IW": idu, "idu_forward_field": op.get("idu_forward"), "ln_idu": op["ln_idu"],
               "exp_ln_idu": math.exp(op["ln_idu"]), "gm_id_q": p.gm_over_id, "gm_id_field": op["gm_id"], "vdsat_q": vs, "vgs_root": vg, "vgs_field": op["vgs"],
               "gds_q_per_w": p.gds_per_w, "w_m": lut.slice_map[(k, wk)].w_m, "ID_slice_A": p.IDu * lut.slice_map[(k, wk)].w_m / op["L"], "fallbacks": list(p.fallbacks)}
        out.setdefault(name, {})[m] = rec
        print(name, m, json.dumps({a: (round(b, 6) if isinstance(b, float) and abs(b) > 1e-3 else b) for a, b in rec.items()}))
Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_scratch_b74\out\engq.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
