"""Z1 다제약 동시 닫기 + 손계산 정밀화(기생 C) 실측. 합성 toy만(library·held-out 미사용), 엔진 코드 미열람.

toy A = 5T OTA (z1_toy), 활성 제약 {GBW, A0}, 결정변수 {gmid1, I}.
toy B = 2단 Miller OTA (nfet 차동쌍 + pfet 거울 / pfet CS + nfet 싱크(M8 다이오드 거울), Cc + Rz 직렬),
        활성 제약 {GBW, PM, A0}, 결정변수 {gmid1, I1, I2}. Rz = 1/gm6(손계산, θ의 일부), Cc 고정.
손계산(기본 꼴, 기생 C 없음):
  A  : A0 = gm1/(gds2+gds4), GBW = gm1/(2π CL)
  B  : A0 = gm1/(gds2+gds4) · gm6/(gds6+gds7), GBW = gm1/(2π Cc), PM = 90° − atan(GBW/p2), p2 = gm6/(2π CL)
손계산(정밀화 꼴 'caps', toy A만): 소자 단독 bench(ngspice, W = 1 µm, m = 1)를 손계산 바이어스 점에서 한 번 재서
  단위 폭 정전용량(capbd, |cgd|, cgg)을 얻는다 = LUT에 C 열을 더한 것과 같은 정보(보간 없음 -- 최선 경우).
  C_out = CL + m1(capbd2+|cgd2|) + m3(capbd4+|cgd4|), GBW = gm1/(2π C_out).
닫기 방식(Δ = (점, metric)별 상대 문턱 이동, 목표 = 분해능/2):
  (a) metric별 독립 secant 동시 갱신  (b) Δ 벡터 Broyden(J0 = I: 손계산 metric = 목표라는 정의에서 나옴)
  (c) 한 번에 하나씩 순차(secant)
멈춤: 전부 [0, 분해능] = closed / 손계산 풀이 불가(E-0 실현 불가) = e0 / 실패 metric들의 oracle 진전 ≤ 분해능 = stall /
      반복 상한(실험 매개변수 15) = cap.
결과는 케이스마다 multi.jsonl에 append.
"""
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np
from scipy.optimize import brentq

import z1_toy as z

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "multi.jsonl")
VDD, VCM = z.VDD, z.VCM
INC = f""".include "{z.PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "{z.PDK}\\cells\\nfet_01v8\\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "{z.PDK}\\models\\parameters\\lod.spice"
.include "{z.PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__tt.pm3.spice"
.include "{z.PDK}\\cells\\pfet_01v8\\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"
.temp 27
.option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7
"""


class E0(Exception):
    pass


def append(rec):
    with open(OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run_ng(text, tag):
    os.makedirs(z.TMP, exist_ok=True)
    p = os.path.join(z.TMP, f"{tag}.cir")
    with open(p, "w") as fo:
        fo.write(text)
    t0 = time.perf_counter()
    r = subprocess.run([z.NG, "-b", p], capture_output=True, text=True, timeout=300)
    return r.stdout + r.stderr, time.perf_counter() - t0


# ---------- 단위 폭 정전용량 bench (손계산 정밀화 꼴의 입력) ----------
_bench = {}


def bench(dev, L, vgs, vds, vs):
    key = (dev, L, round(vgs, 5), round(vds, 5), round(vs, 5))
    if key in _bench:
        return _bench[key]
    if dev == "nfet_01v8":
        vb, vS = 0.0, vs
        vg, vd = vS + vgs, vS + vds
    else:
        vb, vS = VDD, VDD - vs
        vg, vd = vS - vgs, vS - vds
    t = INC + f"""Vd d 0 {vd}
Vg g 0 {vg}
Vs s 0 {vS}
Vb b 0 {vb}
XM1 d g s b sky130_fd_pr__{dev} l={L:.6g} w=1e-06 ad=0.5p as=0.5p pd=3u ps=3u
.control
op
show m.xm1.msky130_fd_pr__{dev} : cgg cgd capbd
quit
.endc
.end
"""
    txt, _ = run_ng(t, f"bench_{abs(hash(key))}")
    c = {k: abs(float(re.search(rf"^\s*{k}\s+([-+0-9.eE]+)", txt, re.M).group(1))) for k in ("cgg", "cgd", "capbd")}
    _bench[key] = c
    return c


# ---------- toy A: 5T OTA ----------
class ToyA:
    metrics = ("GBW", "A0")

    def __init__(self, base, spec, caps=False):
        self.base, self.spec, self.caps = base, spec, caps

    def hand(self, th):
        h = z.hand(th)
        if self.caps:
            c2 = bench("nfet_01v8", th["L1"], VCM - h["vs1"], VCM - h["vs1"], h["vs1"])
            c4 = bench("pfet_01v8", th["L3"], h["vsg3"], VDD - VCM, 0.0)
            cout = th["CL"] + h["m1"] * (c2["capbd"] + c2["cgd"]) + h["m3"] * (c4["capbd"] + c4["cgd"])
            if self.caps == "out":
                h["GBW"] = h["gm1"] / (2 * math.pi * cout)
            else:  # "out+mirror": 거울 마디 극-영점 쌍(p_m, 2p_m)까지 넣고 |H| = 1 교차를 푼다
                vx = VDD - h["vsg3"]
                c1 = bench("nfet_01v8", th["L1"], VCM - h["vs1"], vx - h["vs1"], h["vs1"])
                c3 = bench("pfet_01v8", th["L3"], h["vsg3"], h["vsg3"], 0.0)
                r3 = z.q("pfet_01v8", th["L3"], h["vsg3"], h["vsg3"], 0.0)
                cx = h["m3"] * (2 * c3["cgg"] + c3["capbd"]) + h["m1"] * (c1["capbd"] + c1["cgd"])
                pm = r3["GM"] * h["m3"] / cx
                wu0 = h["gm1"] / cout

                def mag(w):
                    return wu0 / w * abs(complex(1, w / (2 * pm))) / abs(complex(1, w / pm)) - 1
                h["GBW"] = brentq(mag, wu0 * 1e-3, wu0 * 10) / (2 * math.pi)
        return h

    def solve(self, tgt):
        th = z.solve_a0(self.base, tgt["A0"])                       # A0 는 I 와 무관(θ 고정)
        if not self.caps:
            return z.solve_gbw(th, tgt["GBW"])
        f = lambda I: self.hand(dict(th, I=I))["GBW"] - tgt["GBW"]
        lo, hi = 1e-7, 1e-2
        if f(hi) < 0:
            raise E0("GBW target above hand self-loading asymptote")
        th["I"] = brentq(f, lo, hi, xtol=1e-12, rtol=1e-9)
        return th

    def oracle(self, th, tag):
        o = z.oracle(th, z.hand(th), tag)
        return {"GBW": o["GBW"], "A0": o["A0"], "PM": o["PM_deg"], "t_s": o["t_s"]}


# ---------- toy B: 2단 Miller ----------
class ToyB:
    metrics = ("GBW", "PM", "A0")

    def __init__(self, base, spec):
        self.base, self.spec = base, spec

    def hand(self, th):
        L1, L3, L6, L7 = th["L1"], th["L3"], th["L6"], th["L7"]
        g1, g3, g6, g7 = th["gmid1"], th["gmid3"], th["gmid6"], th["gmid7"]
        I1, I2, Cc, CL = th["I1"], th["I2"], th["Cc"], th["CL"]
        f6 = lambda v: (lambda r: r["GM"] / r["ID"])(z.q("pfet_01v8", L6, v, VDD - VCM, 0.0)) - g6
        vsg6 = brentq(f6, 0.15, 1.75, xtol=1e-7)
        r6 = z.q("pfet_01v8", L6, vsg6, VDD - VCM, 0.0)
        v1 = VDD - vsg6                                            # 1단 출력 DC
        f3 = lambda v: (lambda r: r["GM"] / r["ID"])(z.q("pfet_01v8", L3, v, v, 0.0)) - g3
        vsg3 = brentq(f3, 0.15, 1.75, xtol=1e-7)
        r3 = z.q("pfet_01v8", L3, vsg3, vsg3, 0.0)
        r4 = z.q("pfet_01v8", L3, vsg3, VDD - v1, 0.0)
        vx = VDD - vsg3

        def f1(vs):
            r = z.q("nfet_01v8", L1, VCM - vs, v1 - vs, vs)
            return r["GM"] / r["ID"] - g1
        vs1 = brentq(f1, 0.0, min(VCM, vx, v1) - 0.05, xtol=1e-7)
        r2 = z.q("nfet_01v8", L1, VCM - vs1, v1 - vs1, vs1)
        f8 = lambda v: (lambda r: r["GM"] / r["ID"])(z.q("nfet_01v8", L7, v, v, 0.0)) - g7
        vgs8 = brentq(f8, 0.15, 1.75, xtol=1e-7)
        r8 = z.q("nfet_01v8", L7, vgs8, vgs8, 0.0)
        r7 = z.q("nfet_01v8", L7, vgs8, VCM, 0.0)
        m1, m3 = (I1 / 2) / r2["ID"], (I1 / 2) / r3["ID"]
        m6, m7 = I2 / r6["ID"], I2 / r8["ID"]
        gm1, gm6 = r2["GM"] * m1, r6["GM"] * m6
        A0 = gm1 / (r2["GDS"] * m1 + r4["GDS"] * m3) * gm6 / (r6["GDS"] * m6 + r7["GDS"] * m7)
        gbw = gm1 / (2 * math.pi * Cc)
        p2 = gm6 / (2 * math.pi * CL)
        return {"A0": A0, "GBW": gbw, "PM": 90 - math.degrees(math.atan(gbw / p2)), "gm1": gm1, "gm6": gm6,
                "m1": m1, "m3": m3, "m6": m6, "m7": m7, "v1": v1, "vs1": vs1, "vx": vx, "vgs8": vgs8}

    def solve(self, tgt):
        b = self.base

        def fa(g):
            return self.hand(dict(b, gmid1=g))["A0"] - tgt["A0"]
        grid = np.arange(10.5, 24.01, 0.5)
        vals = []
        for g in grid:
            try:
                vals.append(fa(g))
            except ValueError:
                vals.append(-np.inf)
        hi = float(grid[int(np.argmax(vals))])
        if max(vals) < 0 or fa(10.5) > 0:
            raise E0("A0 target outside gm/ID range")
        g1 = brentq(fa, 10.5, hi, xtol=1e-6)
        th = dict(b, gmid1=g1)
        th["I1"] = tgt["GBW"] * 2 * math.pi * b["Cc"] * 2 / g1        # GBW = gmid1·I1/2/(2π Cc)
        if tgt["PM"] >= 90:
            raise E0("PM target >= 90")
        p2 = tgt["GBW"] / math.tan(math.radians(90 - tgt["PM"]))
        th["I2"] = 2 * math.pi * b["CL"] * p2 / b["gmid6"]           # gm6 = gmid6·I2
        th["Rz"] = 1 / (b["gmid6"] * th["I2"])
        return th

    def oracle(self, th, tag):
        h = self.hand(th)

        def geo(m):
            return f"w=1e-06 m={m:.9g} ad=0.5p as=0.5p pd=3u ps=3u"
        t = INC + f"""Vdd vdd 0 DC {VDD}
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
Vcm dcs_p 0 DC {VCM}
Ldc_p dcs_p vin_p 1e12
Cac_p vin_p acs_p 1
Vac_p acs_p 0 DC 0 AC 0.5
Lfb OUT vin_n 1e12
Cac_n vin_n acs_n 1
Vac_n acs_n 0 DC 0 AC -0.5
.nodeset v(OUT)={VCM} v(N1)={h['v1']:.6g} v(X)={h['vx']:.6g} v(CS)={h['vs1']:.6g} v(NB)={h['vgs8']:.6g}
.control
set noaskquit
op
print v(out) v(n1)
ac dec 200 1 20G
meas ac a0 find vm(out) at=1
meas ac ugf when vm(out)=1 fall=1
meas ac ph find vp(out) at=ugf
quit
.endc
.end
"""
        txt, dt = run_ng(t, tag)

        def g(name):
            m = re.search(rf"^{name}\s*=\s*([-+0-9.eE]+)", txt, re.M)
            return float(m.group(1)) if m else None
        a0, ugf, ph = g("a0"), g("ugf"), g("ph")
        if a0 is None or ugf is None or ph is None:
            raise RuntimeError(f"oracle parse fail {tag}\n{txt[-1500:]}")
        pm = 180 + math.degrees(ph)
        pm = (pm + 180) % 360 - 180
        return {"GBW": ugf, "A0": a0, "PM": pm, "t_s": dt}


# ---------- 다제약 닫기 ----------
def close_multi(toy, case, method, res_rel, kmax=15):
    ms = toy.metrics
    spec = toy.spec
    n = len(ms)
    D = np.zeros(n)                       # 상대 Δ (spec 단위)
    J = np.eye(n)
    hist = []
    seq_i = 0
    prevD = prevF = None
    status = "cap"
    for k in range(kmax):
        tgt = {m: spec[m] * (1 + D[i]) for i, m in enumerate(ms)}
        try:
            th = toy.solve(tgt)
        except (E0, ValueError) as e:
            status = "e0"
            hist.append({"k": k, "D": D.tolist(), "e0": str(e)[:120]})
            break
        o = toy.oracle(th, f"{case}_{method}_{k}")
        s = np.array([(o[m] - spec[m]) / spec[m] for m in ms])
        F = s - res_rel / 2
        hist.append({"k": k, "D": D.tolist(), "s": s.tolist(), "oracle": {m: o[m] for m in ms},
                     "theta": {x: th[x] for x in ("gmid1", "I", "I1", "I2") if x in th}, "PM_oracle": o.get("PM"),
                     "t_s": o["t_s"]})
        if np.all((s >= 0) & (s <= res_rel)):
            status = "closed"
            break
        if k >= 1:
            # 진전 판정 대상 = 직전 걸음에서 Δ를 실제로 옮긴 metric 중 실패한 것. 순차 (c)에서 안 옮긴 metric을
            # '진전 없음'으로 세면 거짓 정지가 난다(첫 실행 run_multi.out.txt의 (c) stall 6건).
            moved = np.array(hist[-1]["D"]) != np.array(hist[-2]["D"])
            fail = (s < 0) & moved
            ps = np.array(hist[-2]["s"])
            if fail.any() and np.all(np.abs(s[fail] - ps[fail]) <= res_rel):
                status = "stall"
                break
        if method == "a":
            newD = D - F
            if prevD is not None:
                for i in range(n):
                    dd, dF = D[i] - prevD[i], F[i] - prevF[i]
                    if dd != 0 and dF != 0:
                        newD[i] = D[i] - F[i] * dd / dF
        elif method == "b":
            if prevD is not None:
                dD, dF = D - prevD, F - prevF
                if dD @ dD > 0:
                    J = J + np.outer(dF - J @ dD, dD) / (dD @ dD)
            newD = D - np.linalg.solve(J, F)
        else:  # c: 순차
            while 0 <= s[seq_i] <= res_rel:
                seq_i = (seq_i + 1) % n
            i = seq_i
            newD = D.copy()
            dd = (D[i] - prevD[i]) if prevD is not None else 0.0
            dF = (F[i] - prevF[i]) if prevF is not None else 0.0
            newD[i] = D[i] - (F[i] * dd / dF if dd != 0 and dF != 0 else F[i])
        prevD, prevF = D.copy(), F.copy()
        D = newD
    rec = {"kind": "multi", "case": case, "method": method, "res_rel": res_rel, "metrics": list(ms),
           "spec": spec, "status": status, "oracle_runs": sum(1 for h in hist if "s" in h), "hist": hist}
    append(rec)
    print(case, method, res_rel, status, rec["oracle_runs"],
          [[round(x * 100, 2) for x in h["s"]] for h in hist if "s" in h])
    return rec
