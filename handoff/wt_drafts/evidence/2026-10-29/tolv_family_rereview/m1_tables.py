"""tol_V 계열 재검토 측정 1: 현 엔진 LUT(읽기만)의 tol_V·tol_VDsat 셀값, gm/ID별 eps=tol_V*gm/ID, Pelgrom sigma, W 격자 하한.
결과를 케이스마다 m1_tables.txt 에 append."""
import json
import math
import os
import sys
from pathlib import Path

SKILL = Path(r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\integ-it12\skills\analog-gmid-design")
sys.path.insert(0, str(SKILL))
OUT = Path(__file__).with_name("m1_tables.txt")
OUT.write_text("", encoding="utf-8")


def w(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s, flush=True)


from gmid_engine.core import BoundedLRU, read_pdk_decl  # noqa: E402
from gmid_engine.lut import (LutMemo, LutSpec, load_lut_set, mismatch_sigma_vgs, op_point,  # noqa: E402
                             resolve_lut_location, tol_v_table, tol_vdsat_table, vdsat, vgs_for_gm_id)

DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))
CAP = (("nmos", "_n"), ("pmos", "_p"))
loc = resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)
man = json.loads(Path(loc.manifest_path).read_text(encoding="utf-8"))
kinds = dict(DEVICE_KINDS)
mins = {}
for e in man["slices"]:
    mins[kinds[e["device"]]] = min(e["w_um"] * 1e-6, mins.get(kinds[e["device"]], float("inf")))
pdk = read_pdk_decl(str(SKILL / "assets" / "sky130_pdk_decl.json"), BoundedLRU(16))
q = dict(pdk.quantities)
grid = float(man.get("manufacturing_grid_m", 5e-9))
spec = LutSpec(grid, tuple(sorted(mins.items())), DEVICE_KINDS, CAP,
               noise_ef=(("nmos", q["noise_ef_nmos"].value_m), ("pmos", q["noise_ef_pmos"].value_m)))
lut = load_lut_set(loc.manifest_path, loc.cap_npz_path, spec, pdk_root=loc.pdk_root, verify_midpoints=loc.midpoints_path,
                   noise_npz=loc.noise_path, mismatch_npz=loc.mismatch_path)
memo = LutMemo(lut, point=20000, curve=2000, root=2000)
from gmid_engine.sizing import pre_layout_lut_access  # noqa: E402
wk = dict(pre_layout_lut_access(memo).w_keys)
NAN = float("nan")
w("grid=%s w_keys=%s" % (grid, wk))
for kind in ("nmos", "pmos"):
    fws = sorted(set(e["w_um"] for e in man["slices"] if kinds[e["device"]] == kind))
    w("[%s] W grid lower bound grid/(2 fw): %s" % (kind, ", ".join("fw %gum->%.1e" % (fw, grid / (2 * fw * 1e-6)) for fw in fws)))
    t = tol_v_table(memo, kind, wk[kind])
    tv = tol_vdsat_table(memo, kind, wk[kind])
    try:
        mm = pdk.mismatch_model(kind)
    except Exception as ex:  # noqa: BLE001
        mm = None
        w("mismatch model missing %r" % (ex,))
    w("[%s] L anchors(um)=%s" % (kind, [round(x * 1e6, 3) for x in t.L_anchors]))
    w("kind L_um VDS | tolV_ideq_mV tolV_inv_mV tolVDsat_mV | gmid VGS VDsat_mV eps%% sigVGS(W10um)_mV pair_sig_dI/I%% eps/pair_sig")
    for L in t.L_anchors:
        for vds in (0.2, 0.9):
            try:
                a = t.at(L, vds, "id_equivalent")
                b = t.at(L, vds, "gm_id_inverse")
                c = tv.at(L, vds)
            except Exception as ex:  # noqa: BLE001
                w(("%s %.3f %s ERR %r" % (kind, L * 1e6, vds, ex))[:200])
                continue
            for g in (8.0, 15.0, 22.0):
                try:
                    vgs = vgs_for_gm_id(memo, kind, wk[kind], g, L, vds, 0.0)
                    vgs = vgs[0] if isinstance(vgs, tuple) else vgs
                    op = op_point(memo, kind, wk[kind], L, vgs, vds, 0.0)
                    vd = vdsat(memo, kind, wk[kind], L, vgs, vds, 0.0)
                    sig = None
                    if mm is not None:
                        s = mismatch_sigma_vgs(memo, mm, kind, wk[kind], L, vgs, vds, 0.0, 10e-6)
                        sig = s.sigma_v
                    eps = (a if a is not None else NAN) * op.gm_over_id
                    ps = None if sig is None else math.sqrt(2) * sig * op.gm_over_id
                    w("%s %7.3f %.2f | %7.3f %7.3f %7.3f | %5.1f %.3f %6.1f %6.2f %s %s %s" % (
                        kind, L * 1e6, vds, 1e3 * (a if a is not None else NAN), 1e3 * (b if b is not None else NAN),
                        1e3 * (c if c is not None else NAN), op.gm_over_id, vgs, 1e3 * vd, 100 * eps,
                        "-" if sig is None else "%.3f" % (1e3 * sig), "-" if ps is None else "%.3f" % (100 * ps),
                        "-" if ps is None else "%.1f" % (eps / ps)))
                except Exception as ex:  # noqa: BLE001
                    w("%s %.3f %s g%s ERR %s %s" % (kind, L * 1e6, vds, g, type(ex).__name__, str(ex)[:150]))
