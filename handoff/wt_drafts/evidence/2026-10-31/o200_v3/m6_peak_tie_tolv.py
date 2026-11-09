# O-200 v3 m6 -- Q-O200-4 (다) 대안 '정점과 VGS 축 분해능(device.dc_tol_v = tol_V id_equivalent 셀) 안에서 구별 불가한 점 중 가장 낮은 ln IDu'
# 가 pfet 내부 정점(argmax > 0, 물리 의미 없는 미세 차)을 VGS 0 마디로 되돌리는가를 잰다.
# 판정: 정점 마디 VGS - VGS(마디 0) <= tol_V(그 곡선 (L, VDS) LOO 셀) 이면 '구별 불가'(동률) -> (다) 결과 = 마디 0.
# 입력: LUT r2 (u13_real.real_env 의 resolve_lut_location 경로 = sha 대조), tol_V 셀 = m_j1b/tolv_cells.json(엔진 lut tol_v_table, w 5 um 슬라이스).
# 결과: m6_peak_tie_tolv.txt
import os, sys, json, pathlib
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"; sys.dont_write_bytecode = True
import numpy as np
ENG = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design")
sys.path.insert(0, str(ENG))
from gmid_engine.lut import resolve_lut_location
HERE = pathlib.Path(__file__).parent
loc = resolve_lut_location(str(ENG / "assets/lut_v2_location.json"), os.environ)
Z = np.load(loc.cap_npz_path, allow_pickle=True)
VG, VD = Z["VGS"], Z["VDS"]
T = json.loads((HERE.parent / "m_j1b/tolv_cells.json").read_text(encoding="utf-8"))
out = open(HERE / "m6_peak_tie_tolv.txt", "w", encoding="utf-8")
out.write(f"cap_npz = {loc.cap_npz_path}\n")
di = np.where(VD >= 0.3 - 1e-12)[0]
for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID = np.moveaxis(Z["ID_" + k], 1, 3)[:, di]; GM = np.moveaxis(Z["GM_" + k], 1, 3)[:, di]
    valid = (ID > 0) & (GM > 0)
    g = np.where(valid, GM / np.where(ID > 0, ID, 1), -np.inf)
    am = np.argmax(g, axis=-1)
    loo = np.array([[np.nan if v is None else v for v in r] for r in T[kind]["id_equivalent_v"]], float)[:, di][:, :, None]
    loo = np.broadcast_to(loo, am.shape)
    inner = am > 0
    dv = VG[am] - VG[0]
    tie = inner & (dv <= loo)
    out.write(f"{kind}: curves {am.size}, interior peaks {int(inner.sum())}, of which within tol_V of node0 (tie -> node0) {int(tie.sum())}, "
              f"not tie (stays at noise peak) {int((inner & ~tie & np.isfinite(loo)).sum())}, loo undefined {int((inner & ~np.isfinite(loo)).sum())}; "
              f"interior peak dVGS min/med/max = {dv[inner].min() if inner.any() else None}/{np.median(dv[inner]) if inner.any() else None}/{dv[inner].max() if inner.any() else None} V; "
              f"LOO tol_V on interior-peak curves min/med/max = {np.nanmin(loo[inner]) if inner.any() else None}/{np.nanmedian(loo[inner]) if inner.any() else None}/{np.nanmax(loo[inner]) if inner.any() else None} V\n")
out.close()
print(open(HERE / "m6_peak_tie_tolv.txt", encoding="utf-8").read())
