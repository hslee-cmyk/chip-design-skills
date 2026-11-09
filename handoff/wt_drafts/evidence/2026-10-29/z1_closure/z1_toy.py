"""Z1(e_m 폐지 + oracle 닫기) 권고 전 실측 -- 합성 toy 5T OTA (sky130 tt, ngspice).

용도: 닫기 반복 수·진동/발산·반복당 oracle 비용·(c) e_m 가드 과설계량 비교.
엔진 코드를 읽거나 부르지 않는다. 손계산 = LUT 조회(sky130_lut_v2, W = 1 um 슬라이스, 3축 선형 보간)
+ 닫힌 식(θ 고정: 소자별 gm/ID, L, 꼬리 전류). 회로 = 합성 toy(library·held-out 회로 아님).

손계산 꼴 (as-designed toy 손계산, 엔진 식이 아님):
  M3(다이오드 pfet): gm/ID(VSG, VSD=VSG, VS=0) = gmid3 → VSG3, Vout = VDD - VSG3 (대칭 가정)
  M1(nfet 입력): gm/ID(VCM-VS, Vout-VS, VS) = gmid1 → VS (bulk = 0, gmbs 영향은 LUT VS 축이 반영)
  A0 = gm1/(gds2+gds4), GBW = gm1/(2π CL)  (LUT에 정전용량이 없어 기생 C 생략 -- 손계산 꼴 근사 (ii))
oracle: 같은 W(= 1 um × m, m 실수)·같은 바이어스로 ngspice .op + .ac. 측정 정의:
  A0 = |v(out)/v(id)| at 10 Hz, GBW = |H| = 1 교차 주파수, PM = 180 + ∠H(GBW).
결과는 케이스마다 results.jsonl에 append(원칙 30).
"""
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results.jsonl")
TMP = r"C:/Users/HSLEE/AppData/Local/Temp/claude/C--Users-HSLEE-Documents-Todoc-fpga-chip-design-skills/63c6146a-ab1d-4035-a169-bae810986922/scratchpad/z1"
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
LUT = r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_fd_pr__{dev}__tt__W1p0000um_dc.npz"
PDK = r"C:\pdk\sky130_fd_pr"
VDD, VCM = 1.8, 0.9

_lut = {}


def lut(dev, L):
    key = (dev, L)
    if key in _lut:
        return _lut[key]
    d = np.load(LUT.format(dev=dev))
    il = int(np.argmin(np.abs(d["L"] - L)))
    assert abs(d["L"][il] - L) < 1e-12, "L must be on LUT grid"
    ax = (d["VGS"], d["VDS"], d["VS"])
    f = {k: RegularGridInterpolator(ax, d[k][il], bounds_error=True) for k in ("ID", "GM", "GDS", "GMBS")}
    _lut[key] = f
    return f


def q(dev, L, vgs, vds, vs):
    f = lut(dev, L)
    p = np.array([[vgs, vds, vs]])
    return {k: float(f[k](p)[0]) for k in f}


def hand(th):
    """θ 고정 손계산. th: L1, L3, gmid1, gmid3, I, CL."""
    L1, L3, g1, g3, I, CL = (th[k] for k in ("L1", "L3", "gmid1", "gmid3", "I", "CL"))
    f3 = lambda v: (lambda r: r["GM"] / r["ID"])(q("pfet_01v8", L3, v, v, 0.0)) - g3
    vsg3 = brentq(f3, 0.15, 1.75, xtol=1e-7)
    r3 = q("pfet_01v8", L3, vsg3, vsg3, 0.0)
    # 측정 구성(oracle과 같은 정의): 출력 DC는 단위 되먹임 servo가 VCM에 둔다.
    vout = VCM
    vx = VDD - vsg3

    def f1(vs):
        r = q("nfet_01v8", L1, VCM - vs, vout - vs, vs)
        return r["GM"] / r["ID"] - g1
    vs1 = brentq(f1, 0.0, min(VCM, vx) - 0.05, xtol=1e-7)
    r2 = q("nfet_01v8", L1, VCM - vs1, vout - vs1, vs1)        # 출력 쪽 입력 소자
    r4 = q("pfet_01v8", L3, vsg3, VDD - vout, 0.0)              # 출력 쪽 거울 소자
    id1 = I / 2
    m1, m3 = id1 / r2["ID"], id1 / r3["ID"]
    gm1 = r2["GM"] * m1
    gds1, gds4 = r2["GDS"] * m1, r4["GDS"] * m3
    return {"vsg3": vsg3, "vout": vout, "vs1": vs1, "m1": m1, "m3": m3, "gm1": gm1,
            "A0": gm1 / (gds1 + gds4), "GBW": gm1 / (2 * math.pi * CL)}


def netlist(th, h, path):
    L1, L3, I, CL = th["L1"], th["L3"], th["I"], th["CL"]

    def geo(m):
        return f"w=1e-06 m={m:.9g} ad=0.5p as=0.5p pd=3u ps=3u"
    s = f"""* z1 toy 5T OTA
.include "{PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "{PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "{PDK}\\models\\parameters\\lod.spice"
.include "{PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__tt.pm3.spice"
.include "{PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"
.temp 27
.option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7
Vdd vdd 0 DC {VDD}
XM3 X X vdd vdd sky130_fd_pr__pfet_01v8 l={L3:.6g} {geo(h['m3'])}
XM4 OUT X vdd vdd sky130_fd_pr__pfet_01v8 l={L3:.6g} {geo(h['m3'])}
XM1 X vin_p CS 0 sky130_fd_pr__nfet_01v8 l={L1:.6g} {geo(h['m1'])}
XM2 OUT vin_n CS 0 sky130_fd_pr__nfet_01v8 l={L1:.6g} {geo(h['m1'])}
Itail CS 0 DC {I:.9g}
CL OUT 0 {CL:.6g}
Vcm dcs_p 0 DC {VCM}
Ldc_p dcs_p vin_p 1e12
Cac_p vin_p acs_p 1
Vac_p acs_p 0 DC 0 AC 0.5
Lfb OUT vin_n 1e12
Cac_n vin_n acs_n 1
Vac_n acs_n 0 DC 0 AC -0.5
.nodeset v(OUT)={h['vout']:.6g} v(X)={h['vout']:.6g} v(CS)={h['vs1']:.6g}
.control
set noaskquit
op
print v(out) v(cs)
ac dec 200 10 20G
meas ac a0 find vm(out) at=10
meas ac ugf when vm(out)=1 fall=1
meas ac ph find vp(out) at=ugf
quit
.endc
.end
"""
    with open(path, "w") as fo:
        fo.write(s)


def oracle(th, h, tag):
    os.makedirs(TMP, exist_ok=True)
    p = os.path.join(TMP, f"{tag}.cir")
    netlist(th, h, p)
    t0 = time.perf_counter()
    r = subprocess.run([NG, "-b", p], capture_output=True, text=True, timeout=300)
    dt = time.perf_counter() - t0
    txt = r.stdout + r.stderr

    def g(name):
        m = re.search(rf"^{name}\s*=\s*([-+0-9.eE]+)", txt, re.M)
        return float(m.group(1)) if m else None
    vo = re.search(r"v\(out\)\s*=\s*([-+0-9.eE]+)", txt)
    a0, ugf, ph = g("a0"), g("ugf"), g("ph")
    if a0 is None or ugf is None:
        raise RuntimeError(f"oracle parse fail {tag}\n{txt[-2000:]}")
    pm = 180 + math.degrees(ph) if ph is not None else None
    return {"A0": a0, "GBW": ugf, "PM_deg": pm, "vout": float(vo.group(1)) if vo else None, "t_s": dt}


def append(rec):
    with open(OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------- 엔진 쪽 풀이(손계산 역산) ----------
def solve_gbw(th, target):
    """GBW 활성: gm/ID 고정, I 를 닫힌 식으로 역산 (GBW = gmid1·I/2 /(2π CL))."""
    t = dict(th)
    t["I"] = target * 2 * math.pi * th["CL"] * 2 / th["gmid1"]
    return t


def solve_a0(th, target):
    """A0 활성: I 고정, gmid1 을 손계산 A0(gmid1) = target 으로 역산(단조)."""
    def f(g):
        t = dict(th)
        t["gmid1"] = g
        return hand(t)["A0"] - target
    lo = 10.5
    grid = np.arange(lo, 24.01, 0.5)
    hi = float(grid[int(np.argmax([f(g) for g in grid]))])  # 단조 가지(최대 A0 앞)만 쓴다
    if f(lo) > 0 or f(hi) < 0:
        raise RuntimeError("A0 target outside gmid1 range")
    t = dict(th)
    t["gmid1"] = brentq(f, lo, hi, xtol=1e-6)
    return t


SOLVERS = {"GBW": solve_gbw, "A0": solve_a0}
XVAR = {"GBW": "I", "A0": "gmid1"}


def closure(case, th0, metric, spec, res_rel, aim, kmax=12):
    """Z1 닫기. aim='zero': Δ ← Δ - s°; aim='mid': Δ ← Δ - (s° - res/2).
    합격 = 0 <= s° <= res. 정지 = 합격 / Δ 재방문 / kmax."""
    res = res_rel * spec
    delta, hist, seen = 0.0, [], []
    for k in range(kmax):
        th = SOLVERS[metric](th0, spec + delta)
        h = hand(th)
        o = oracle(th, h, f"{case}_{metric}_{aim}_{k}")
        s = o[metric] - spec
        hist.append({"k": k, "delta": delta, "x": th[XVAR[metric]], "I": th["I"], "gmid1": th["gmid1"],
                     "hand": h[metric], "oracle": o[metric], "s_rel": s / spec, "PM_deg": o["PM_deg"],
                     "t_s": o["t_s"]})
        if 0 <= s <= res:
            return {"status": "closed", "oracle_runs": k + 1, "hist": hist}
        F = s if aim == "zero" else s - res / 2
        if aim == "secant" and k >= 1 and F != hist[-2]["F"]:
            d_prev, F_prev = hist[-2]["delta"], hist[-2]["F"]
            nd = delta - F * (delta - d_prev) / (F - F_prev)
        else:
            nd = delta - F
        hist[-1]["F"] = F
        if any(abs(nd - d0) <= 1e-9 * spec for d0 in seen):
            return {"status": "revisit", "oracle_runs": k + 1, "hist": hist}
        seen.append(delta)
        delta = nd
    return {"status": "kmax", "oracle_runs": kmax, "hist": hist}


def run_closure(case, th0, metric, spec, res_rel, aim):
    r = closure(case, th0, metric, spec, res_rel, aim)
    rec = {"kind": "closure", "case": case, "metric": metric, "spec": spec, "res_rel": res_rel, "aim": aim,
           "theta0": th0, **r}
    append(rec)
    print(case, metric, aim, res_rel, r["status"], r["oracle_runs"],
          [round(x["s_rel"] * 100, 3) for x in r["hist"]])
    return rec


def run_curve(case, th0, metric, xs):
    """d(x) 곡선: 닫기 수렴 인자 κ = d'(x)/m_hand'(x) 추정용."""
    pts = []
    for i, x in enumerate(xs):
        t = dict(th0)
        t[XVAR[metric]] = x
        h = hand(t)
        o = oracle(t, h, f"{case}_curve_{metric}_{i}")
        pts.append({"x": x, "hand": h[metric], "oracle": o[metric], "d_rel": (h[metric] - o[metric]) / o[metric],
                    "PM_deg": o["PM_deg"], "t_s": o["t_s"], "vout_hand": h["vout"], "vout_sp": o["vout"]})
    m_h = np.array([p["hand"] for p in pts])
    d = np.array([p["hand"] - p["oracle"] for p in pts])
    kappa = (np.diff(d) / np.diff(m_h)).tolist()
    rec = {"kind": "curve", "case": case, "metric": metric, "theta0": th0, "pts": pts, "kappa": kappa}
    append(rec)
    print(case, metric, "d_rel%", [round(p["d_rel"] * 100, 2) for p in pts], "kappa", [round(k, 3) for k in kappa])
    return rec


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "smoke":
        th = {"L1": 5e-7, "L3": 5e-7, "gmid1": 12.0, "gmid3": 10.0, "I": 50e-6, "CL": 1e-12}
        h = hand(th)
        o = oracle(th, h, "smoke")
        print(h)
        print(o)
