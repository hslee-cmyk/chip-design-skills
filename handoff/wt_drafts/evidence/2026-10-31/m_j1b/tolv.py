# LUT leave-one-out tol_V 셀값(엔진 lut 모듈의 tol_v_table, 읽기 전용 호출 -- gmid_engine.lut 만 import, 규칙 선언(rule_decl) 경로는 부르지 않는다).
# 출력 tolv_cells.json: {kind: {w_um, L_um[], VDS[], id_equivalent_v[L][VDS], gm_id_inverse_v[L][VDS]}}
import sys, os, json, pathlib
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.core import BoundedLRU, read_pdk_decl
from gmid_engine.lut import LutMemo, LutSpec, load_lut_set, resolve_lut_location
from gmid_engine.lut import tol_v_table
HERE = pathlib.Path(__file__).parent
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")); CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
man = json.loads(pathlib.Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS); mins = {}
for e in man["slices"]:
    k = kinds[e["device"]]; mins[k] = min(e["w_um"] * 1e-6, mins.get(k, float("inf")))
dm = BoundedLRU(16)
pdk = read_pdk_decl(str(ENG / "assets/sky130_pdk_decl.json"), dm)
q = dict(pdk.quantities)
spec = LutSpec(float(man.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
memo = LutMemo(lut, point=1 << 16, curve=1 << 14, root=1 << 16)
print([ (e["device"], e["w_um"]) for e in man["slices"]][:40])
out = {}
import numpy as np, time
for kind in ("nmos", "pmos"):
    t0 = time.time()
    tb = tol_v_table(memo, kind, 1000)
    L = [float(x) for x in tb.L_anchors] if hasattr(tb, "L_anchors") else None
    vds = [float(x) for x in tb.vds_grid]
    eq = [[None if c.id_equivalent_v is None else float(c.id_equivalent_v) for c in row] for row in tb.cells]
    gi = [[None if c.gm_id_inverse_v is None else float(c.gm_id_inverse_v) for c in row] for row in tb.cells]
    out[kind] = dict(w_um=5.0, L_m=L, VDS=vds, id_equivalent_v=eq, gm_id_inverse_v=gi)
    print(kind, "done", round(time.time() - t0, 1), "s", len(eq), "x", len(vds), flush=True)
    flat = [v for r in eq for v in r if v is not None]
    print(" id_equivalent_v min/med/max", min(flat), float(np.median(flat)), max(flat))
(HERE / "tolv_cells.json").write_text(json.dumps(out), encoding="utf-8")
