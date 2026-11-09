"""손계산용 LUT 읽기 도우미 -- 엔진 코드를 쓰지 않고 npz 원 파일을 numpy로 직접 읽는다.

규칙(손계산 선택):
- L은 LUT 격자점만 쓴다(bin 경계를 넘는 L 보간 금지 -- 계획 L은 같은 bin 안에서만 보간).
- VGS·VDS·VS는 격자 사이 다선형 보간.
- DC 열(ID·GM·GDS·VTH·VDSAT)은 손가락 폭 w_s 슬라이스 파일에서(DEC-105 (2)),
  용량 열(CGG·CGD·CGS·CDD·CSS)은 기준 폭(w_ref) 표에서 읽어 W/w_ref로 비례(같은 결정).
- 크기는 절댓값(LUT 부호 규약: pfet은 크기로 저장).
"""
import glob, os, re
import numpy as np

ROOT = "C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/"
_DEV = {"nmos": "nfet", "pmos": "pfet"}
_slices = {}
_cap = None


def slice_widths(kind):
    pat = os.path.join(ROOT, "sky130_fd_pr__%s_01v8__tt__W*um_dc.npz" % _DEV[kind])
    out = []
    for f in glob.glob(pat):
        m = re.search(r"__W(\d+)p(\d+)um_dc", f)
        out.append(float(m.group(1) + "." + m.group(2)) * 1e-6)
    return sorted(out)


def _slice(kind, w):
    key = (kind, round(w * 1e9))
    if key not in _slices:
        um = "%.4f" % (w * 1e6)
        a, b = um.split(".")
        f = os.path.join(ROOT, "sky130_fd_pr__%s_01v8__tt__W%sp%sum_dc.npz" % (_DEV[kind], a, b))
        d = np.load(f, allow_pickle=True)
        _slices[key] = {k: d[k] for k in ("L", "VGS", "VDS", "VS", "ID", "GM", "GDS", "VTH", "VDSAT", "GMBS")}
        _slices[key]["W"] = float(d["W"])
    return _slices[key]


def cap_table():
    global _cap
    if _cap is None:
        d = np.load(os.path.join(ROOT, "sky130_nfet_pfet_lut_v2_r2.npz"), allow_pickle=True)
        _cap = {k: d[k] for k in d.files if k not in ("meta_json",)}
    return _cap


def _interp3(arr_l, vgs_ax, vds_ax, vs_ax, vgs, vds, vs):
    """arr_l: [VGS, VDS, VS] 배열에서 다선형 보간."""
    def idx(ax, x):
        x = min(max(x, ax[0]), ax[-1])
        i = int(np.searchsorted(ax, x) - 1)
        i = min(max(i, 0), len(ax) - 2)
        t = (x - ax[i]) / (ax[i + 1] - ax[i])
        return i, t
    i, ti = idx(vgs_ax, vgs)
    j, tj = idx(vds_ax, vds)
    k, tk = idx(vs_ax, vs)
    acc = 0.0
    for di, wi in ((0, 1 - ti), (1, ti)):
        for dj, wj in ((0, 1 - tj), (1, tj)):
            for dk, wk in ((0, 1 - tk), (1, tk)):
                acc += wi * wj * wk * arr_l[i + di, j + dj, k + dk]
    return float(acc)


def l_index(ax, L):
    i = int(np.argmin(np.abs(ax - L)))
    if abs(ax[i] - L) > 1e-12:
        raise ValueError("L %.3g 는 LUT 격자점이 아님 (bin 넘는 보간 금지)" % L)
    return i


def dc(kind, w_s, L, vgs, vds, vs):
    """손가락 폭 w_s 슬라이스에서 손가락 하나의 DC 값과 폭 정규화 IDu."""
    s = _slice(kind, w_s)
    il = l_index(s["L"], L)
    r = {}
    for q in ("ID", "GM", "GDS", "VTH", "VDSAT", "GMBS"):
        r[q] = _interp3(s[q][il], s["VGS"], s["VDS"], s["VS"], vgs, vds, vs)
    r["IDu"] = r["ID"] / s["W"]
    r["gmid"] = r["GM"] / r["ID"] if r["ID"] > 0 else float("nan")
    return r


def caps(kind, L, vgs, vds, vs, W):
    """기준 폭 표의 용량을 W/w_ref로 비례."""
    c = cap_table()
    suf = "_n" if kind == "nmos" else "_p"
    il = l_index(c["L"], L)
    scale = W / float(c["w_ref_m"])
    r = {}
    for q in ("CGG", "CGD", "CGS", "CGB", "CDD", "CSS"):
        r[q] = abs(_interp3(c[q + suf][il], c["VGS"], c["VDS"], c["VS"], vgs, vds, vs)) * scale
    return r


def vgs_for_gmid(kind, w_s, L, gmid_target, vds, vs):
    """같은 (L, VDS, VS)에서 gm/ID = 목표가 되는 VGS(이분법, gm/ID는 VGS에 단조 감소인 구간)."""
    s = _slice(kind, w_s)
    lo, hi = 0.05, 1.8
    f = lambda v: dc(kind, w_s, L, v, vds, vs)["gmid"] - gmid_target
    # 강반전 쪽(hi)에서 gm/ID 작음 -> f<0, 약반전 쪽(lo)에서 큼 -> f>0
    flo, fhi = f(lo), f(hi)
    if not (flo > 0 > fhi):
        raise ValueError("gm/ID %.2f 가 범위 밖 (lo %.2f hi %.2f)" % (gmid_target, flo + gmid_target, fhi + gmid_target))
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if f(m) > 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)


def vgs_for_idu(kind, w_s, L, idu_target, vds, vs):
    """같은 (L, VDS, VS)에서 IDu = 목표가 되는 VGS(ID는 VGS에 단조 증가)."""
    lo, hi = 0.0, 1.8
    g = lambda v: dc(kind, w_s, L, v, vds, vs)["IDu"] - idu_target
    for _ in range(60):
        m = 0.5 * (lo + hi)
        if g(m) < 0:
            lo = m
        else:
            hi = m
    return 0.5 * (lo + hi)
