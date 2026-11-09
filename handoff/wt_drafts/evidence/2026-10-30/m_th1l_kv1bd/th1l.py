# M-TH1L: 레이아웃 폭 슬라이스로 옮길 때 보존량 두 안 비교.
#   (L1) (ID, gm/ID, L) 보존: 슬라이스 s 에서 g_s(VGS') = g0 인 VGS'(가장 큰 해 = 현행 규칙; 근 수도 셈) -> ΔVGS, 봉인(포화) 깨짐, 다근
#   (L2) (ID, VGS, L) 보존: g_s(VGS0) -> Δgm/gm (ID 보존이므로 Δ(gm/ID)/g0), 고유이득 gm/gds 변화, 봉인 깨짐
# 설계 기준점 = r2 주 LUT(W_ref 5 um, lut_v2_location.json cap_npz) 위 동작점. 슬라이스 = lut_data/sky130_lut_v2/*_dc.npz 32개(manifest).
# 대표 소자: (a) kv1 oracle rep_orig_rail_rail 의 8소자(current_reuse class-AB 반쪽, 고리 P·N 잔차까지)
#            (b) 원문 current_reuse pfet 26개(orig_ops, 원문 판독 IDu·L·VSB·VSD -> sky130 r2 위 VGS0 역산)
# 고리 잔차(L1): 고리 P: VSG11a + VSG11b - VSG15 - VSG9a 의 ΔVGS 합, N: VGS14a + VGS14b - VGS16 - VGS9b. 모든 소자가 같은 슬라이스 / 소자별 최악 둘.
# I_Q 환산: d ln I_Q / dδ = 5.8~6.3 /V (classab_battery all_out.jsonl sens) -- 인용(앞 실측), 판정 근거는 잔차 V 자체.
# 결과 append: th1l.jsonl
import json, math, pathlib, re, glob
import numpy as np
from scipy.interpolate import RegularGridInterpolator

HERE = pathlib.Path(__file__).parent
OUT = HERE / "th1l.jsonl"
ROOT = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2")
LOC = json.loads(pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/lut_v2_location.json").read_text(encoding="utf-8"))
KV = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/wt/_drafts/evidence/2026-10-30/m_kv1_name_tiebreak")
FINE = None


class Table:
    def __init__(self, ID, GM, GDS, VDSAT, L, VG, VD, VS, W):
        self.ID, self.GM, self.GDS, self.VDSAT, self.L, self.VG, self.VD, self.VS, self.W = ID, GM, GDS, VDSAT, L, VG, VD, VS, W
        self._c = {}

    def interp(self, L):
        if L not in self._c:
            li = int(np.argmin(np.abs(self.L - L)))
            assert abs(self.L[li] - L) < 1e-12
            idv = np.maximum(self.ID[li], 1e-30)
            ax = (self.VG, self.VD, self.VS)
            self._c[L] = (RegularGridInterpolator(ax, np.log(idv), method="cubic"),
                          RegularGridInterpolator(ax, self.GM[li] / idv, method="cubic"),
                          RegularGridInterpolator(ax, self.GDS[li] / idv, method="cubic"),
                          RegularGridInterpolator(ax, self.VDSAT[li], method="linear"))
        return self._c[L]

    def q(self, L, vgs, vds, vsb):
        lid, g, gd, vs = self.interp(L)
        p = [[vgs, vds, vsb]]
        return dict(J=float(np.exp(lid(p)[0])) / self.W, g=float(g(p)[0]), gds_id=float(gd(p)[0]), vdsat=float(vs(p)[0]))

    def curve(self, L, vds, vsb, diode):
        lid, g, _, _ = self.interp(L)
        vd = FINE if diode else np.full_like(FINE, vds)
        pts = np.column_stack([FINE, vd, np.full_like(FINE, vsb)])
        return g(pts), lid(pts)


def load_main():
    z = np.load(pathlib.Path(LOC["root"]["default"]) / LOC["files"]["cap_npz"]["path"], allow_pickle=True)
    out = {}
    for k in ("n", "p"):
        out[k] = Table(z["ID_" + k], z["GM_" + k], z["GDS_" + k], z["VDSAT_" + k], z["L"], z["VGS"], z["VDS"], z["VS"], float(z["w_ref_m"]))
    return out


def load_slices():
    out = {"n": [], "p": []}
    for f in sorted(ROOT.glob("*_dc.npz")):
        k = "n" if "nfet" in f.name else "p"
        z = np.load(f, allow_pickle=True)
        out[k].append(Table(z["ID"], z["GM"], z["GDS"], z["VDSAT"], z["L"], z["VGS"], z["VDS"], z["VS"], float(z["W"])))
    return out


def vgs_from_J(T, L, J, vds, vsb, diode):
    g, lid = T.curve(L, vds, vsb, diode)
    t = math.log(J * T.W)
    if not (lid[0] <= t <= lid[-1]):
        return None
    return float(np.interp(t, lid, FINE))


def roots_of_g(T, L, g0, vds, vsb, diode):
    g, _ = T.curve(L, vds, vsb, diode)
    p = int(np.argmax(g))
    v, gb = FINE[p:], g[p:]
    d = gb - g0
    idx = np.where(d[:-1] * d[1:] <= 0)[0]
    return [float(v[i] + (v[i + 1] - v[i]) * d[i] / (d[i] - d[i + 1])) if d[i] != d[i + 1] else float(v[i]) for i in idx]


def per_device(name, kind, L, vgs0, vds, vsb, diode, main, slices):
    ref = main[kind].q(L, vgs0, vgs0 if diode else vds, vsb)
    g0 = ref["g"]
    rows = []
    for T in slices[kind]:
        if not np.any(np.abs(T.L - L) < 1e-12):
            continue
        # L1
        rts = roots_of_g(T, L, g0, vds, vsb, diode)
        if rts:
            v1 = max(rts)
            near = min(rts, key=lambda r: abs(r - vgs0))
            q1 = T.q(L, v1, v1 if diode else vds, vsb)
            sat1 = diode or vds >= q1["vdsat"]
        else:
            v1 = near = None; q1 = None; sat1 = None
        # L2
        q2 = T.q(L, vgs0, vgs0 if diode else vds, vsb)
        sat2 = diode or vds >= q2["vdsat"]
        rows.append(dict(W_slice_um=T.W * 1e6, L1=dict(n_roots=len(rts), vgs=v1, dvgs=None if v1 is None else v1 - vgs0,
                                                     dvgs_nearest=None if near is None else near - vgs0, sat=sat1,
                                                     J_ratio=None if q1 is None else q1["J"] / ref["J"]),
                         L2=dict(dg_rel=q2["g"] / g0 - 1, gain_rel=(q2["g"] / q2["gds_id"]) / (g0 / ref["gds_id"]) - 1, sat=sat2,
                                 J_ratio=q2["J"] / ref["J"])))
    return dict(dev=name, kind=kind, L=L, vgs0=vgs0, vds=vds, vsb=vsb, diode=diode, g0=g0, slices=rows)


def main_run():
    global FINE
    main = load_main()
    FINE = np.linspace(main["n"].VG[1], main["n"].VG[-1], 3001)
    slices = load_slices()
    if OUT.exists():
        OUT.unlink()
    # (a) kv1 rep_orig_rail_rail
    rec = None
    for line in (KV / "results.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("case") == "spice" and r.get("outer") == "rep" and r.get("point") == "orig" and r["depP"] == "rail" and r["depN"] == "rail":
            rec = r
    run = KV.parent / "m_kv1_name_tiebreak"
    dv = {}
    tag = "rep_orig_rail_rail"
    runs = pathlib.Path(r"C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/kv1/runs")
    for ln in (runs / tag / "op_dev.txt").read_text(errors="replace").splitlines():
        m = re.match(r"\s*@m\.x(m\w+)\.msky130_fd_pr__[np]fet_01v8\[(\w+)\]\s*=\s*([-+0-9.eE]+)", ln)
        if m:
            dv[f"{m.group(1)}.{m.group(2)}"] = float(m.group(3))
    nodes = dict(rec["spice_nodes"]); nodes["vdd"] = 1.8; nodes["0"] = 0.0
    SRC = dict(M15="vdd", M16="0", M9a="vg15", M9b="vop1", M11a="vdd", M11b="n11a11b", M14b="0", M14a="n14a_14b")
    devres = {}
    for d, (kind, w, l) in rec["sizes"].items():
        L = round(l, 3) * 1e-6
        vgs, vds = abs(dv[f"{d.lower()}.vgs"]), abs(dv[f"{d.lower()}.vds"])
        vs = nodes[SRC[d]]
        vsb = (1.8 - vs) if kind == "p" else vs
        diode = d in ("M11a", "M11b", "M14a", "M14b")
        res = per_device(d, kind, L, vgs, vds, vsb, diode, main, slices)
        res["set"] = "kv1_rep"
        devres[d] = res
        append(res)
    # 고리 잔차(L1, 같은 슬라이스 -- 슬라이스 W 별, 네 소자가 모두 그 W 슬라이스를 가질 때)
    for loop, plus, minus in (("P", ("M11a", "M11b"), ("M15", "M9a")), ("N", ("M14a", "M14b"), ("M16", "M9b"))):
        ws = set.intersection(*[set(round(s["W_slice_um"], 4) for s in devres[d]["slices"]) for d in plus + minus])
        same = []
        for W in sorted(ws):
            dd = {}
            for d in plus + minus:
                s = [x for x in devres[d]["slices"] if round(x["W_slice_um"], 4) == W][0]
                dd[d] = s["L1"]["dvgs"]
            if any(v is None for v in dd.values()):
                continue
            same.append(dict(W=W, res=sum(dd[d] for d in plus) - sum(dd[d] for d in minus)))
        # 소자별 독립 슬라이스: 잔차 범위 = Σ 범위
        lo = sum(min(x["L1"]["dvgs"] for x in devres[d]["slices"] if x["L1"]["dvgs"] is not None) for d in plus) - \
             sum(max(x["L1"]["dvgs"] for x in devres[d]["slices"] if x["L1"]["dvgs"] is not None) for d in minus)
        hi = sum(max(x["L1"]["dvgs"] for x in devres[d]["slices"] if x["L1"]["dvgs"] is not None) for d in plus) - \
             sum(min(x["L1"]["dvgs"] for x in devres[d]["slices"] if x["L1"]["dvgs"] is not None) for d in minus)
        append(dict(case="loop_residual_L1", loop=loop, same_slice=same, indep_range=[lo, hi]))
    # (b) 원문 current_reuse pfet
    for line in (KV / "orig_ops" / "current_reuse_telescopic_ota.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if not (r.get("W_um") and r.get("L_um") and r.get("I_A")):
            continue
        Lg = main["p"].L * 1e6
        up = Lg[Lg >= r["L_um"] - 1e-9]
        L = float((up[0] if len(up) else Lg[-1]) * 1e-6)
        vsb = r.get("VSB_V")
        if vsb is None:
            vsb = 0.0 if r.get("source_is_rail") else None
        if vsb is None or not (0 <= vsb <= 1.8):
            continue
        diode = bool(r.get("is_diode"))
        vds = abs(r["VSD_V"]) if r.get("VSD_V") is not None else None
        if vds is None and not diode:
            continue
        J = abs(r["I_A"]) / (r["W_um"] * 1e-6 * (r.get("m") or 1))
        vgs0 = vgs_from_J(main["p"], L, J, vds, vsb, diode)
        if vgs0 is None:
            continue
        res = per_device(r["dev"], "p", L, vgs0, vgs0 if diode else vds, vsb, diode, main, slices)
        res["set"] = "orig_current_reuse"
        append(res)


def append(o):
    with open(OUT, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(o, default=float) + "\n")


if __name__ == "__main__":
    main_run()
