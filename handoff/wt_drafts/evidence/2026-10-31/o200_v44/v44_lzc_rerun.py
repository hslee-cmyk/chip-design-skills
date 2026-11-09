# O-200 v4 (Major E) -- 후보 (가) '선형 예측 영 교차'의 물리 뜻을 LUT 로 잰다.
# 소자 전류를 봉인점에서 VGS 1차로 늘이면 ID + gm·ΔVGS = 0 의 영 교차는 ΔVGS = -1/(gm/ID) 다.
# 그 VGS 에서 실제 LUT 전류가 봉인점 전류의 몇 배인지(ID(VGS - 1/(gm/ID)) / ID(VGS))를 반전 수준별로 잰다 -- 1 에 가까우면 '차단' 이 아니다.
# 반전 수준 = VGS - |VTH| (BSIM VTH 열): WI < -0.1 V, MI [-0.1, 0.1], SI > 0.1 V (구간 이름은 보고용 표지이고 판정 문턱으로 쓰지 않음).
# 입력: LUT r2 (resolve_lut_location, sha 대조), VDS >= 0.3 V, 격자 원값, ln ID 는 VGS 마디 사이 선형 보간(보고용 근사).
# 결과: m_linear_zero_cross.txt (kind·반전 구간마다 append)
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
di = np.where(VD >= 0.3 - 1e-12)[0]
out = open(HERE / "v44_lzc_rerun.txt", "w", encoding="utf-8")
out.write(f"cap_npz = {loc.cap_npz_path}\nquantiles [0, .1, .5, .9, 1]\n")


def q(a):
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    return None if a.size == 0 else [round(float(np.quantile(a, p)), 4) for p in (0, .1, .5, .9, 1)]


for k, kind in (("n", "nmos"), ("p", "pmos")):
    ID = np.moveaxis(Z["ID_" + k], 1, 3)[:, di].reshape(-1, len(VG))
    GM = np.moveaxis(Z["GM_" + k], 1, 3)[:, di].reshape(-1, len(VG))
    VTH = np.abs(np.moveaxis(Z["VTH_" + k], 1, 3)[:, di].reshape(-1, len(VG)))
    valid = (ID > 0) & (GM > 0)
    lnI = np.where(valid, np.log(np.where(ID > 0, ID, 1.0)), np.nan)
    g = np.where(valid, GM / np.where(ID > 0, ID, 1.0), np.nan)
    dv = 1.0 / g
    vt = VG[None, :] - dv
    inside = vt >= VG[0]
    ratio = np.full(ID.shape, np.nan)
    for r in range(ID.shape[0]):
        ok = valid[r]
        if ok.sum() < 2:
            continue
        xs, ys = VG[ok], lnI[r, ok]
        m = ok & inside[r]
        ratio[r, m] = np.exp(np.interp(vt[r, m], xs, ys) - lnI[r, m])
    vov = VG[None, :] - VTH
    for name, sel in (("WI vov<-0.1", vov < -0.1), ("MI -0.1..0.1", (vov >= -0.1) & (vov <= 0.1)), ("SI vov>0.1", vov > 0.1)):
        s = sel & valid
        si = s & inside
        line = dict(kind=kind, region=name, nodes=int(s.sum()), dVGS_mV=q(1e3 * dv[s]), outside_domain_frac=round(float((s & ~inside).sum() / max(1, s.sum())), 4),
                    ID_at_zero_cross_over_ID=q(ratio[si]))
        out.write(json.dumps(line, ensure_ascii=False) + "\n"); out.flush()
        print(line)
