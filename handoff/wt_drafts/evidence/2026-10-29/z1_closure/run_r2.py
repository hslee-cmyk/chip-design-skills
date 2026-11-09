"""§9 구동: LUT r2(C 열) 손계산으로 Z1 닫기((a) 독립 secant 동시) + (c) e_m 가드 비교. 결과 r2.jsonl append.
e_m(DEC-72 꼴) = (회로, metric)마다 첫 풀이(Δ = 0) front 점들의 |손계산 − oracle|/spec 최대값(방향 무시).
가드 = 손계산 목표 spec·(1 + e_m) (metric마다). 가드 점을 oracle로 재서 합격·여유·전력을 Z1 닫힌 점과 비교.
"""
import json
import os
from collections import defaultdict

import z1_multi as M
import z1_r2 as R

M.OUT = R.OUT
RES = 0.01


class T5G(R.T5):
    """GBW 단독(gm/ID 고정) -- §1·§3과 같은 단일 제약 비교."""
    metrics = ("GBW",)

    def solve(self, tgt):
        th = dict(self.base)
        if self.form == "base":
            th["I"] = tgt["GBW"] * 2 * 3.141592653589793 * th["CL"] * 2 / th["gmid1"]
            return th
        from scipy.optimize import brentq
        f = lambda I: self.hand(dict(th, I=I))["GBW"] - tgt["GBW"]
        if f(1e-2) < 0:
            raise M.E0("GBW target above hand self-loading asymptote")
        th["I"] = brentq(f, 1e-7, 1e-2, xtol=1e-12, rtol=1e-9)
        return th


def power(th):
    return th.get("I", 0) + th.get("I1", 0) + th.get("I2", 0)


def guard(toy, circ, em, z1rec, tag):
    tgt = {m: toy.spec[m] * (1 + em[m]) for m in toy.metrics}
    rec = {"kind": "guard", "circuit": circ, "case": tag, "form": toy.form, "e_m_rel": em}
    try:
        th = toy.solve(tgt)
        o = toy.oracle(th, f"r2guard_{tag}")
        s = {m: (o[m] - toy.spec[m]) / toy.spec[m] for m in toy.metrics}
        rec.update({"status": "ok", "s_rel": s, "pass": all(v >= 0 for v in s.values()),
                    "over_res": [m for m in toy.metrics if s[m] > RES], "P_guard": power(th)})
    except (M.E0, ValueError) as e:
        rec.update({"status": "e0", "msg": str(e)[:100]})
    hs = [h for h in z1rec["hist"] if "s" in h]
    rec.update({"z1_status": z1rec["status"], "z1_runs": len(hs), "P_z1": power(hs[-1]["theta"]) if z1rec["status"] == "closed" else None})
    if rec.get("P_guard") and rec["P_z1"]:
        rec["P_guard_vs_z1_rel"] = rec["P_guard"] / rec["P_z1"] - 1
    with open(R.OUT, "a", encoding="utf-8") as fo:
        fo.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print("  guard", tag, rec.get("status"), {k: round(v * 100, 2) for k, v in rec.get("s_rel", {}).items()},
          "pass", rec.get("pass"), "P g/z1", round(rec.get("P_guard_vs_z1_rel", float("nan")) * 100, 1))


def run_group(circ, toys):
    z1 = {}
    for tag, toy in toys:
        z1[tag] = M.close_multi(toy, f"r2_{toy.form}_{tag}", "a", RES)
    em = defaultdict(float)
    for tag, toy in toys:
        h0 = z1[tag]["hist"][0]
        if "s" not in h0:
            continue
        th0 = h0["theta"]
        hand0 = {m: toy.spec[m] for m in toy.metrics}      # Δ = 0 풀이에서 손계산 = spec
        for m in toy.metrics:
            em[m] = max(em[m], abs(hand0[m] - h0["oracle"][m]) / toy.spec[m])
    for tag, toy in toys:
        guard(toy, circ, dict(em), z1[tag], f"{toy.form}_{tag}")


if __name__ == "__main__":
    for form in ("base", "C"):
        for cl, gbw in ((1e-12, 50e6), (1e-13, 300e6), (3e-14, 600e6)):
            toys = []
            for g in (10.0, 14.0, 20.0):
                base = {"L1": 5e-7, "L3": 5e-7, "gmid1": g, "gmid3": 10.0, "I": 50e-6, "CL": cl}
                toys.append((f"gbw_cl{cl:.0e}_g{g:g}", T5G(base, {"GBW": gbw}, form)))
            run_group(f"5T_GBW_cl{cl:.0e}", toys)
        for cl, gbw in ((1e-12, 50e6), (1e-13, 300e6), (3e-14, 600e6)):
            toys = []
            for g in (12.0, 18.0):
                base = {"L1": 5e-7, "L3": 5e-7, "gmid1": g, "gmid3": 10.0, "I": 50e-6, "CL": cl}
                a0 = round(R.T5(base, {}, "base").hand(base)["A0"], 2)
                toys.append((f"multi_cl{cl:.0e}_g{g:g}", R.T5(base, {"GBW": gbw, "A0": a0}, form)))
            run_group(f"5T_multi_cl{cl:.0e}", toys)
        bb = {"L1": 5e-7, "L3": 5e-7, "L6": 5e-7, "L7": 5e-7, "gmid1": 14.0, "gmid3": 10.0, "gmid6": 10.0,
              "gmid7": 10.0, "I1": 10e-6, "I2": 30e-6}
        for cl, cc, cases in ((1e-12, 3e-13, ((30e6, 60.0),)), (2e-13, 6e-14, ((100e6, 60.0), (80e6, 60.0), (80e6, 70.0)))):
            base = dict(bb, CL=cl, Cc=cc)
            a0 = round(R.TB(base, {}, "base").hand(dict(base, Rz=1 / (10 * 30e-6)))["A0"], 1)
            toys = [(f"miller_cl{cl:.0e}_gbw{g/1e6:g}M_pm{p:g}", R.TB(base, {"GBW": g, "PM": p, "A0": a0}, form))
                    for g, p in cases]
            run_group(f"Miller_cl{cl:.0e}", toys)
