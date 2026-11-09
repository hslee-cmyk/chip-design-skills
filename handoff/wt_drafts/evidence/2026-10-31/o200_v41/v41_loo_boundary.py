# 검증 41 -- LOO tol_V 셀값(m_j1b/tolv_cells.json, Q-T0 미결 예시값)으로 잰 봉인 9 경계 VGS 분포 (감사 V2 '0.11~0.26 V' 대조). 결과 v41_loo_boundary.txt
import json, os, sys, pathlib
import numpy as np
sys.dont_write_bytecode = True
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.lut.data_location import resolve_lut_location
LOC = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
Z = np.load(LOC.cap_npz_path, allow_pickle=True); VG, VD = Z["VGS"], Z["VDS"]
TOLV = json.loads((pathlib.Path(__file__).parent.parent / "m_j1b/tolv_cells.json").read_text(encoding="utf-8"))
di = np.where(VD >= 0.3 - 1e-12)[0]
out = open(pathlib.Path(__file__).parent / "v41_loo_boundary.txt", "w", encoding="utf-8")
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID = np.moveaxis(Z["ID_" + k], 1, 3)[:, di]; GM = np.moveaxis(Z["GM_" + k], 1, 3)[:, di]
    loo = np.array([[np.nan if v is None else v for v in r] for r in TOLV[kind]["id_equivalent_v"]], float)[:, di][:, :, None, None]
    cond = (GM * loo >= ID[..., :1]) & (ID > 0)
    fi = np.where(cond.any(-1), np.argmax(cond, -1), -1)
    ok = np.isfinite(np.broadcast_to(loo, fi.shape + (1,))[..., 0]) & (fi >= 0)
    v = VG[np.maximum(fi, 0)][ok]
    s = f"{kind}: 경계 VGS 분위 [0,.1,.5,.9,1] = {[round(float(np.quantile(v, x)), 4) for x in (0, .1, .5, .9, 1)]}, 경계=마디0(옛 식이 VGS 0 을 전도로 봄) {int((fi[ok]==0).sum())}/{int(ok.sum())}, 경계 없음 {int((~cond.any(-1)).sum())}"
    print(s); out.write(s + "\n")
