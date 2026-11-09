"""§9 재측정: 손계산을 LUT v2 r2(C 열 포함, W_ref = 5 µm)로 다시 짠다. 합성 toy만, 엔진 코드 미열람.

LUT: lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz, 축 [L, VGS, VDS, VS], W_ref 5 µm,
  측정 소자 줄 'w=5u ad=2.5p as=2.5p pd=7u ps=7u'. C 열은 F_TEST = 100 MHz AC로 잰 값(부호 보존).
  손계산은 3축 선형 보간(L은 격자점). oracle 넷리스트도 같은 손가락 형상(w=5u, ad/pd 같음, m 실수)으로 둔다
  -- 손가락 형상 차(W′ 실현, Q-W1)를 이 비교에서 빼기 위함.
손계산 꼴 두 가지:
  'base' = 앞 절과 같은 꼴(C 없음): 5T GBW = gm1/(2π CL); Miller GBW = gm1/(2π Cc), PM = 90° − atan(GBW/p2), p2 = gm6/(2π CL)
  'C'    = LUT C 열을 넣은 소신호 마디 해석(닫힌 식 대신 마디 행렬을 주파수마다 푼다 -- 무거운 반복 없음):
     5T  : 출력 마디 C_out = CL + m1·CDD(M2) + m3·CDD(M4), 거울 마디 C_X = m3·(CGG3 + CDD3 − 2|CGD3|) + m3·CGG4 + m1·CDD1,
           H = gm1/(s C_out + g_out) · (1 + s/(2 p_m))/(1 + s/p_m), p_m = gm3/C_X  → |H| = 1 교차, 위상
     Miller: 마디 N1·NZ·OUT 3×3 어드미턴스(gm6 전압 제어, Rz, Cc + m6·|CGD6|, C1 = m1·CDD2 + m3·CDD4 + m6·(CGG6 − |CGD6|),
           C2 = CL + m6·(CDD6 − |CGD6|) + m7·CDD7) × 1단 거울 쌍 → |H| = 1 교차, PM
결과는 케이스마다 r2.jsonl에 append.
"""
import json
import math
import os
import re

import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.optimize import brentq, root

import z1_multi as M
import z1_toy as z

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "r2.jsonl")
LUT2 = r"C:/Users/HSLEE/Documents/Todoc/fpga/lut_data/sky130_lut_v2/sky130_nfet_pfet_lut_v2_r2.npz"
VDD, VCM = z.VDD, z.VCM
COLS = ("ID", "GM", "GDS", "CGG", "CGD", "CDD")
_d = np.load(LUT2)
_ax = (_d["VGS"], _d["VDS"], _d["VS"])
_f = {}


def q(dev, L, vgs, vds, vs):
    sfx = "_n" if dev == "nfet_01v8" else "_p"
    il = int(np.argmin(np.abs(_d["L"] - L)))
    assert abs(_d["L"][il] - L) < 1e-12
    key = (sfx, il)
    if key not in _f:
        _f[key] = {c: RegularGridInterpolator(_ax, _d[c + sfx][il]) for c in COLS}
    p = np.array([[vgs, vds, vs]])
    r = {c: float(_f[key][c](p)[0]) for c in COLS}
    r["CGD"] = abs(r["CGD"])
    return r


def gmid_solve(dev, L, g, vds_of, vs_of, lo, hi):
    f = lambda v: (lambda r: r["GM"] / r["ID"])(q(dev, L, v, vds_of(v), vs_of(v))) - g
    return brentq(f, lo, hi, xtol=1e-7)


def ugf_pm(Hf, w0):
    """|H(jw)| = 1 교차(첫 하강)와 그 점 위상. Hf(w) -> complex."""
    ws = np.geomspace(w0 * 1e-3, w0 * 1e3, 600)
    mags = np.array([abs(Hf(w)) for w in ws])
    i = int(np.argmax(mags < 1))
    if i == 0:
        raise M.E0("no unity crossing")
    wu = brentq(lambda w: abs(Hf(w)) - 1, ws[i - 1], ws[i])
    ph = math.degrees(np.angle(Hf(wu)))
    return wu / (2 * math.pi), 180 + ph if ph < 0 else ph


def geo(m):
    return f"w=5e-06 m={m:.9g} ad=2.5p as=2.5p pd=7u ps=7u"


def measure(text, tag):
    txt, dt = M.run_ng(text, tag)

    def g(name):
        mm = re.search(rf"^{name}\s*=\s*([-+0-9.eE]+)", txt, re.M)
        return float(mm.group(1)) if mm else None
    a0, ugf, ph = g("a0"), g("ugf"), g("ph")
    if a0 is None or ugf is None or ph is None:
        raise RuntimeError(f"oracle parse fail {tag}\n{txt[-1500:]}")
    pm = (180 + math.degrees(ph) + 180) % 360 - 180
    return {"GBW": ugf, "A0": a0, "PM": pm, "t_s": dt}


AC = """.control
set noaskquit
op
ac dec 200 1 20G
meas ac a0 find vm(out) at=1
meas ac ugf when vm(out)=1 fall=1
meas ac ph find vp(out) at=ugf
quit
.endc
.end
"""
STIM = f"""Vcm dcs_p 0 DC {VCM}
Ldc_p dcs_p vin_p 1e12
Cac_p vin_p acs_p 1
Vac_p acs_p 0 DC 0 AC 0.5
Lfb OUT vin_n 1e12
Cac_n vin_n acs_n 1
Vac_n acs_n 0 DC 0 AC -0.5
"""


class T5:
    """5T OTA. 측정 구성: 단위 되먹임 servo DC(출력 = VCM), 개루프 AC."""
    metrics = ("GBW", "A0")

    def __init__(self, base, spec, form):
        self.base, self.spec, self.form = base, spec, form

    def bias(self, th):
        L1, L3 = th["L1"], th["L3"]
        vsg3 = gmid_solve("pfet_01v8", L3, th["gmid3"], lambda v: v, lambda v: 0.0, 0.15, 1.75)
        vx = VDD - vsg3
        vs1 = brentq(lambda vs: (lambda r: r["GM"] / r["ID"])(q("nfet_01v8", L1, VCM - vs, VCM - vs, vs)) - th["gmid1"],
                     0.0, min(VCM, vx) - 0.05, xtol=1e-7)
        return {"vsg3": vsg3, "vx": vx, "vs1": vs1,
                "r1": q("nfet_01v8", L1, VCM - vs1, vx - vs1, vs1), "r2": q("nfet_01v8", L1, VCM - vs1, VCM - vs1, vs1),
                "r3": q("pfet_01v8", L3, vsg3, vsg3, 0.0), "r4": q("pfet_01v8", L3, vsg3, VDD - VCM, 0.0)}

    def hand(self, th):
        b = self.bias(th)
        id1 = th["I"] / 2
        m1, m3 = id1 / b["r2"]["ID"], id1 / b["r3"]["ID"]
        gm1 = b["r2"]["GM"] * m1
        gout = b["r2"]["GDS"] * m1 + b["r4"]["GDS"] * m3
        h = {"m1": m1, "m3": m3, "gm1": gm1, "A0": gm1 / gout, **{k: b[k] for k in ("vsg3", "vx", "vs1")}}
        if self.form == "base":
            h["GBW"] = gm1 / (2 * math.pi * th["CL"])
            return h
        r1, r2, r3, r4 = b["r1"], b["r2"], b["r3"], b["r4"]
        cout = th["CL"] + m1 * r2["CDD"] + m3 * r4["CDD"]
        cx = m3 * (r3["CGG"] + r3["CDD"] - 2 * r3["CGD"]) + m3 * r4["CGG"] + m1 * r1["CDD"]
        pmr = r3["GM"] * m3 / cx

        def H(w):
            s = 1j * w
            return gm1 / (s * cout + gout) * (1 + s / (2 * pmr)) / (1 + s / pmr)
        h["GBW"], h["PM"] = ugf_pm(H, gm1 / cout)
        return h

    def solve(self, tgt):
        def fa(g):
            return self.hand(dict(self.base, gmid1=g))["A0"] - tgt["A0"]
        grid = np.arange(10.5, 24.01, 0.5)
        vals = []
        for g in grid:
            try:
                vals.append(fa(g))
            except ValueError:
                vals.append(-np.inf)
        hi = float(grid[int(np.argmax(vals))])
        if max(vals) < 0 or fa(10.5) > 0:
            raise M.E0("A0 target outside gm/ID range")
        th = dict(self.base, gmid1=brentq(fa, 10.5, hi, xtol=1e-6))
        if self.form == "base":
            th["I"] = tgt["GBW"] * 2 * math.pi * th["CL"] * 2 / th["gmid1"]
            return th
        f = lambda I: self.hand(dict(th, I=I))["GBW"] - tgt["GBW"]
        if f(1e-2) < 0:
            raise M.E0("GBW target above hand self-loading asymptote")
        th["I"] = brentq(f, 1e-7, 1e-2, xtol=1e-12, rtol=1e-9)
        return th

    def oracle(self, th, tag):
        h = self.hand(dict(th))
        t = M.INC + f"""Vdd vdd 0 DC {VDD}
XM3 X X vdd vdd sky130_fd_pr__pfet_01v8 l={th['L3']:.6g} {geo(h['m3'])}
XM4 OUT X vdd vdd sky130_fd_pr__pfet_01v8 l={th['L3']:.6g} {geo(h['m3'])}
XM1 X vin_p CS 0 sky130_fd_pr__nfet_01v8 l={th['L1']:.6g} {geo(h['m1'])}
XM2 OUT vin_n CS 0 sky130_fd_pr__nfet_01v8 l={th['L1']:.6g} {geo(h['m1'])}
Itail CS 0 DC {th['I']:.9g}
CL OUT 0 {th['CL']:.6g}
{STIM}.nodeset v(OUT)={VCM} v(X)={h['vx']:.6g} v(CS)={h['vs1']:.6g}
""" + AC
        return measure(t, tag)


class TB:
    """2단 Miller. 측정 구성 같음."""
    metrics = ("GBW", "PM", "A0")

    def __init__(self, base, spec, form):
        self.base, self.spec, self.form = base, spec, form

    def bias(self, th):
        L1, L3, L6, L7 = th["L1"], th["L3"], th["L6"], th["L7"]
        vsg6 = gmid_solve("pfet_01v8", L6, th["gmid6"], lambda v: VDD - VCM, lambda v: 0.0, 0.15, 1.75)
        v1 = VDD - vsg6
        vsg3 = gmid_solve("pfet_01v8", L3, th["gmid3"], lambda v: v, lambda v: 0.0, 0.15, 1.75)
        vx = VDD - vsg3
        vs1 = brentq(lambda vs: (lambda r: r["GM"] / r["ID"])(q("nfet_01v8", L1, VCM - vs, v1 - vs, vs)) - th["gmid1"],
                     0.0, min(VCM, vx, v1) - 0.05, xtol=1e-7)
        vgs8 = gmid_solve("nfet_01v8", L7, th["gmid7"], lambda v: v, lambda v: 0.0, 0.15, 1.75)
        return {"v1": v1, "vx": vx, "vs1": vs1, "vgs8": vgs8,
                "r1": q("nfet_01v8", L1, VCM - vs1, vx - vs1, vs1), "r2": q("nfet_01v8", L1, VCM - vs1, v1 - vs1, vs1),
                "r3": q("pfet_01v8", L3, vsg3, vsg3, 0.0), "r4": q("pfet_01v8", L3, vsg3, VDD - v1, 0.0),
                "r6": q("pfet_01v8", L6, vsg6, VDD - VCM, 0.0), "r8": q("nfet_01v8", L7, vgs8, vgs8, 0.0),
                "r7": q("nfet_01v8", L7, vgs8, VCM, 0.0)}

    def hand(self, th):
        b = self.bias(th)
        r1, r2, r3, r4, r6, r7, r8 = (b[k] for k in ("r1", "r2", "r3", "r4", "r6", "r7", "r8"))
        m1, m3 = (th["I1"] / 2) / r2["ID"], (th["I1"] / 2) / r3["ID"]
        m6, m7 = th["I2"] / r6["ID"], th["I2"] / r8["ID"]
        gm1, gm6 = r2["GM"] * m1, r6["GM"] * m6
        g1 = r2["GDS"] * m1 + r4["GDS"] * m3
        g2 = r6["GDS"] * m6 + r7["GDS"] * m7
        h = {"m1": m1, "m3": m3, "m6": m6, "m7": m7, "gm1": gm1, "gm6": gm6, "A0": gm1 / g1 * gm6 / g2,
             **{k: b[k] for k in ("v1", "vx", "vs1", "vgs8")}}
        if self.form == "base":
            gbw = gm1 / (2 * math.pi * th["Cc"])
            h["GBW"], h["PM"] = gbw, 90 - math.degrees(math.atan(gbw / (gm6 / (2 * math.pi * th["CL"]))))
            return h
        cgd6 = m6 * r6["CGD"]
        cc = th["Cc"] + cgd6
        c1 = m1 * r2["CDD"] + m3 * r4["CDD"] + m6 * r6["CGG"] - cgd6
        c2 = th["CL"] + m6 * r6["CDD"] + m7 * r7["CDD"] - cgd6
        cx = m3 * (r3["CGG"] + r3["CDD"] - 2 * r3["CGD"]) + m3 * r4["CGG"] + m1 * r1["CDD"]
        pmr = r3["GM"] * m3 / cx
        gz = 1 / th["Rz"]

        def H(w):
            s = 1j * w
            Y = np.array([[g1 + s * c1 + gz, -gz, 0],
                          [-gz, gz + s * cc, -s * cc],
                          [gm6, -s * cc, g2 + s * c2 + s * cc]], dtype=complex)
            v = np.linalg.solve(Y, np.array([gm1, 0, 0], dtype=complex))
            # 1단 출력 전류 방향: 입력 vin_p ↑ → N1 ↓ → OUT ↑ (비반전), gm6 항 부호가 그 반전을 담는다
            return -v[2] * (1 + s / (2 * pmr)) / (1 + s / pmr)
        h["GBW"], h["PM"] = ugf_pm(H, gm1 / th["Cc"])
        return h

    def solve(self, tgt):
        b = self.base

        def fa(g):
            return self.hand(dict(b, gmid1=g, I1=b["I1"], I2=b["I2"], Rz=1 / (b["gmid6"] * b["I2"])))["A0"] - tgt["A0"]
        grid = np.arange(10.5, 24.01, 0.5)
        vals = []
        for g in grid:
            try:
                vals.append(fa(g))
            except (ValueError, M.E0):
                vals.append(-np.inf)
        hi = float(grid[int(np.argmax(vals))])
        if max(vals) < 0 or fa(10.5) > 0:
            raise M.E0("A0 target outside gm/ID range")
        g1 = brentq(fa, 10.5, hi, xtol=1e-6)
        th = dict(b, gmid1=g1)
        if tgt["PM"] >= 90:
            raise M.E0("PM target >= 90")
        I1 = tgt["GBW"] * 2 * math.pi * b["Cc"] * 2 / g1
        I2 = 2 * math.pi * b["CL"] * tgt["GBW"] / math.tan(math.radians(90 - tgt["PM"])) / b["gmid6"]
        if self.form == "base":
            return dict(th, I1=I1, I2=I2, Rz=1 / (b["gmid6"] * I2))

        def F(x):
            i1, i2 = math.exp(x[0]), math.exp(x[1])
            try:
                h = self.hand(dict(th, I1=i1, I2=i2, Rz=1 / (b["gmid6"] * i2)))
            except (M.E0, ValueError):
                return [10.0, 10.0]
            return [h["GBW"] / tgt["GBW"] - 1, (h["PM"] - tgt["PM"]) / tgt["PM"]]
        sol = root(F, [math.log(I1), math.log(I2)], method="hybr")
        if not sol.success or max(abs(v) for v in F(sol.x)) > 1e-6:
            raise M.E0("hand (GBW, PM) target not reachable: " + str(sol.message)[:60])
        i1, i2 = math.exp(sol.x[0]), math.exp(sol.x[1])
        if i1 > 1e-2 or i2 > 1e-2:
            raise M.E0("hand solution current above 10 mA")
        return dict(th, I1=i1, I2=i2, Rz=1 / (b["gmid6"] * i2))

    def oracle(self, th, tag):
        h = self.hand(dict(th))
        t = M.INC + f"""Vdd vdd 0 DC {VDD}
XM3 X X vdd vdd sky130_fd_pr__pfet_01v8 l={th['L3']:.6g} {geo(h['m3'])}
XM4 N1 X vdd vdd sky130_fd_pr__pfet_01v8 l={th['L3']:.6g} {geo(h['m3'])}
XM1 X vin_n CS 0 sky130_fd_pr__nfet_01v8 l={th['L1']:.6g} {geo(h['m1'])}
XM2 N1 vin_p CS 0 sky130_fd_pr__nfet_01v8 l={th['L1']:.6g} {geo(h['m1'])}
Itail CS 0 DC {th['I1']:.9g}
XM6 OUT N1 vdd vdd sky130_fd_pr__pfet_01v8 l={th['L6']:.6g} {geo(h['m6'])}
XM7 OUT NB 0 0 sky130_fd_pr__nfet_01v8 l={th['L7']:.6g} {geo(h['m7'])}
XM8 NB NB 0 0 sky130_fd_pr__nfet_01v8 l={th['L7']:.6g} {geo(h['m7'])}
Iref vdd NB DC {th['I2']:.9g}
Rz N1 NZ {th['Rz']:.9g}
Cc NZ OUT {th['Cc']:.6g}
CL OUT 0 {th['CL']:.6g}
{STIM}.nodeset v(OUT)={VCM} v(N1)={h['v1']:.6g} v(X)={h['vx']:.6g} v(CS)={h['vs1']:.6g} v(NB)={h['vgs8']:.6g}
""" + AC
        return measure(t, tag)
