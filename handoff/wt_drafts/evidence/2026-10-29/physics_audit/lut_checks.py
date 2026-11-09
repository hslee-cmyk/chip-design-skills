"""물리 점검 LUT 계산 (읽기 전용). sky130 LUT v2 기준 npz(W=5u, tt, 27C)만 읽는다.
결과는 같은 폴더 lut_checks.out.jsonl 에 케이스마다 append.
실행: C:/Python314/python.exe lut_checks.py [vth window voc swing intrinsic density curve]"""
import json, sys, os
import numpy as np
from scipy.interpolate import RegularGridInterpolator as RGI
from scipy.optimize import brentq

ROOT = os.environ.get("GMID_LUT_V2_ROOT", "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lut_checks.out.jsonl")
d = np.load(os.path.join(ROOT, "sky130_nfet_pfet_lut_v2_r2.npz"), allow_pickle=True)
Ls, VGS, VDS, VS = d["L"], d["VGS"], d["VDS"], d["VS"]
VDD = 1.8


def emit(case, **kw):
    rec = {"case": case, **kw}
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False))


_cache = {}


def f(col, t, L):
    key = (col, t, L)
    if key not in _cache:
        i = int(np.argmin(abs(Ls - L)))
        a = d[f"{col}_{t}"][i]
        if col == "ID":
            a = np.log(np.maximum(a, 1e-30))
        _cache[key] = RGI((VGS, VDS, VS), a, bounds_error=False, fill_value=None)
    return _cache[key]


def q(col, t, L, vgs, vds, vs):
    v = float(f(col, t, L)([[vgs, vds, vs]])[0])
    return float(np.exp(v)) if col == "ID" else v


def gmid(t, L, vgs, vds, vs):
    return q("GM", t, L, vgs, vds, vs) / q("ID", t, L, vgs, vds, vs)


def vgs_at_gmid(t, L, target, vds, vs):
    """VGS 오름차순으로 gm/ID가 target 아래로 내려가는 첫 점(강반전 쪽 가지)."""
    g = lambda v: gmid(t, L, v, vds, vs) - target
    grid = np.linspace(0.2, 1.8, 161)
    vals = [g(v) for v in grid]
    for a, b, fa, fb in zip(grid[:-1], grid[1:], vals[:-1], vals[1:]):
        if fa > 0 >= fb:
            return brentq(g, a, b)
    return None


def vgs_at_idu(t, L, idu, vds, vs):
    I = idu * 5.0
    return brentq(lambda v: np.log(q("ID", t, L, v, vds, vs)) - np.log(I), 0.05, 1.8)


def case_vth():
    for t in ("n", "p"):
        for L in (1.5e-7, 5e-7, 1e-6, 2e-6):
            emit("vth", kind=t, L_um=L * 1e6, vth_vs0=round(q("VTH", t, L, 0.9, 0.9, 0.0), 3),
                 vth_vs0p4=round(q("VTH", t, L, 0.9, 0.9, 0.4), 3))


def case_current_reuse_window():
    # 상보 입력쌍 창: lower = Vy + VGS_n(VS=Vy), Vy = VDSAT(M5); upper = Vx - VSG_p(VS=VDD-Vx), Vx = VDD - VDSAT(M6)
    for L in (5e-7, 1e-6, 2e-6):
        for gin in (10, 15, 20, 24):
            for gtail in (8, 12):
                vg5 = vgs_at_gmid("n", L, gtail, 0.3, 0.0)
                vg6 = vgs_at_gmid("p", L, gtail, 0.3, 0.0)
                if vg5 is None or vg6 is None:
                    continue
                vy = q("VDSAT", "n", L, vg5, 0.3, 0.0)
                vx = VDD - q("VDSAT", "p", L, vg6, 0.3, 0.0)
                vgn = vgs_at_gmid("n", L, gin, 0.4, vy)
                vsgp = vgs_at_gmid("p", L, gin, 0.4, VDD - vx)
                if vgn is None or vsgp is None:
                    emit("cr_window", L_um=L * 1e6, gmid_in=gin, gmid_tail=gtail, note="gm/ID 미도달")
                    continue
                lo, hi = vy + vgn, vx - vsgp
                emit("cr_window", L_um=L * 1e6, gmid_in=gin, gmid_tail=gtail, Vy_min=round(vy, 3), Vx_max=round(vx, 3),
                     VGS_n=round(vgn, 3), VSG_p=round(vsgp, 3), lo=round(lo, 3), hi=round(hi, 3),
                     center=round((lo + hi) / 2, 3), width=round(hi - lo, 3), has_0p9=bool(lo <= 0.9 <= hi),
                     margin_0p9_to_hi=round(hi - 0.9, 3))


def case_cr_window_density():
    """입력쌍 전류 밀도(A/um, 두 쌍 같은 전류 -- current reuse)로 창을 다시 잼. 꼬리 VDS = VDSAT(gm/ID 12)."""
    for L in (5e-7, 1e-6):
        vg5 = vgs_at_gmid("n", L, 12, 0.3, 0.0)
        vg6 = vgs_at_gmid("p", L, 12, 0.3, 0.0)
        vy = q("VDSAT", "n", L, vg5, 0.3, 0.0)
        vx = VDD - q("VDSAT", "p", L, vg6, 0.3, 0.0)
        for idu in (1e-9, 1e-8, 3e-8, 1e-7, 3e-7, 1e-6):
            vgn = vgs_at_idu("n", L, idu, 0.4, vy)
            vsgp = vgs_at_idu("p", L, idu, 0.4, VDD - vx)
            lo, hi = vy + vgn, vx - vsgp
            emit("cr_window_density", L_um=L * 1e6, IDu_A_per_um=idu, Vy=round(vy, 3), Vx=round(vx, 3),
                 VGS_n=round(vgn, 3), gmid_n=round(gmid("n", L, vgn, 0.4, vy), 1),
                 VSG_p=round(vsgp, 3), gmid_p=round(gmid("p", L, vsgp, 0.4, VDD - vx), 1),
                 fT_p_MHz=round(q("GM", "p", L, vsgp, 0.4, VDD - vx) / (2 * np.pi * abs(q("CGG", "p", L, vsgp, 0.4, VDD - vx))) / 1e6, 2),
                 lo=round(lo, 3), hi=round(hi, 3), center=round((lo + hi) / 2, 3), width=round(hi - lo, 3),
                 has_0p9=bool(lo <= 0.9 <= hi))


def case_pmos_gmid_curve():
    for L in (5e-7, 1e-6):
        for v in np.arange(0.5, 1.31, 0.05):
            emit("gmid_curve", L_um=L * 1e6, VGS=round(float(v), 3),
                 gmid_p=round(gmid("p", L, v, 0.6, 0.0), 2), IDu_p=q("ID", "p", L, v, 0.6, 0.0) / 5.0,
                 gmid_n=round(gmid("n", L, v, 0.6, 0.0), 2), IDu_n=q("ID", "n", L, v, 0.6, 0.0) / 5.0)


def case_voc_des():
    # M39: pmos source vdd, gate=drain=V -> VSG=VSD=VDD-V, 몸체-소스 0
    # M40: pmos source V, gate=drain=gnd -> VSG=VSD=V, 몸체 vdd -> VS = VDD-V
    for L in (5e-7, 1e-6, 2e-6):
        for ratio in (0.25, 0.5, 1.0, 2.0, 4.0, 10.0, 30.0):  # W40/W39
            g = lambda V: np.log(q("ID", "p", L, VDD - V, VDD - V, 0.0)) - np.log(ratio * q("ID", "p", L, V, V, VDD - V))
            try:
                V = brentq(g, 0.3, 1.5)
                emit("voc_des", L_um=L * 1e6, W40_over_W39=ratio, Voc_des=round(V, 4),
                     I_per_5um_A=q("ID", "p", L, VDD - V, VDD - V, 0.0),
                     gmid_M39=round(gmid("p", L, VDD - V, VDD - V, 0.0), 2),
                     gmid_M40=round(gmid("p", L, V, V, VDD - V), 2))
            except ValueError:
                emit("voc_des", L_um=L * 1e6, W40_over_W39=ratio, note="근 없음 [0.3,1.5]")


def case_output_swing_cr():
    # 출력단 M15(pmos vdd) / M16(nmos gnd): 스윙 [VDSAT16, VDD-VSDSAT15]
    for L in (5e-7, 1e-6):
        for g in (8, 12, 16):
            vgn = vgs_at_gmid("n", L, g, 0.9, 0.0)
            vgp = vgs_at_gmid("p", L, g, 0.9, 0.0)
            if vgn is None or vgp is None:
                continue
            a = q("VDSAT", "n", L, vgn, 0.9, 0.0)
            b = q("VDSAT", "p", L, vgp, 0.9, 0.0)
            emit("cr_out_swing", L_um=L * 1e6, gmid=g, lo=round(a, 3), hi=round(VDD - b, 3), center=round((a + VDD - b) / 2, 3))


def case_intrinsic():
    for t in ("n", "p"):
        for L in (5e-7, 1e-6, 2e-6):
            for g in (10, 15, 20):
                for vds in (0.3, 0.6):
                    v = vgs_at_gmid(t, L, g, vds, 0.0)
                    if v is None:
                        continue
                    gm = q("GM", t, L, v, vds, 0.0)
                    gds = q("GDS", t, L, v, vds, 0.0)
                    cgg = abs(q("CGG", t, L, v, vds, 0.0))
                    cdd = abs(q("CDD", t, L, v, vds, 0.0))
                    emit("intrinsic", kind=t, L_um=L * 1e6, gmid=g, VDS=vds, VGS=round(v, 3), gm_gds=round(gm / gds, 1),
                         gain_db=round(20 * np.log10(gm / gds), 1), fT_MHz=round(gm / (2 * np.pi * cgg) / 1e6, 1),
                         IDu_A_per_um=q("ID", t, L, v, vds, 0.0) / 5.0, cgg_per_gm=cgg / gm, cdd_per_gm=cdd / gm)


CASES = {"vth": case_vth, "window": case_current_reuse_window, "density": case_cr_window_density,
         "curve": case_pmos_gmid_curve, "voc": case_voc_des, "swing": case_output_swing_cr, "intrinsic": case_intrinsic}

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(CASES)):
        CASES[name]()
