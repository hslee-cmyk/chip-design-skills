"""ngcc_3stage_ff ICMR servo 측정(ngspice) -- 손 사이징 시험점(spec 값 아님, 엔진 봉인점 부재로 대용).

측정 구성 = 계획 N3.8 'ICMR 측정 구성'(servo): 두 입력 포트를 Vcm 으로 함께 훑고, 출력은 기준값 Vref 에 DC 로 묶는다.
  e = A_s·(Vref − Vout), Vinp = Vcm + e/2, Vinn = Vcm − e/2 (A_s = 1, 음되먹임 -- Vinp → Vout 비반전).
점별 증분 DC 이득(O-211 기준 양) = ∂Vout/∂Vid 를 같은 DC 해의 .tf 로: de/dVref = A_s/(1 + A_s·A) → A = (A_s/(de/dVref) − 1)/A_s.
소자 영역: 점마다 |VDS| − |VDSAT| (ngspice @m[vds]·[vdsat], O-204 경계 = VDS = VDSAT), ID 부호.
usage: python icmr_servo_spice.py <case_name> <vref> [vcm_lo vcm_hi step] [--L 5e-7]
결과: icmr_<case>.csv (덮어씀), icmr_servo.log 에 케이스 요약 append.
"""
import argparse
import math
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
NG = r"C:/ngspice/Spice64/bin/ngspice_con.exe"
INC = r"""
.include "C:\pdk\sky130_fd_pr\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "C:\pdk\sky130_fd_pr\cells\nfet_01v8\sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "C:\pdk\sky130_fd_pr\models\parameters\lod.spice"
.include "C:\pdk\sky130_fd_pr\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__tt.pm3.spice"
.include "C:\pdk\sky130_fd_pr\cells\pfet_01v8\sky130_fd_pr__pfet_01v8__mismatch.corner.spice"
"""
# 손 사이징 시험점 (W um) -- 유도는 ngcc_3stage_ff.md §3.2 표(char_gmid.log 전류밀도 표에서 계산)
SIZES = {
    # name: (kind, d, g, s, W_um)
    "M0": ("p", "TAIL", "VBP", "vdd", 6.9),
    "M1": ("p", "ND", "Vinn", "TAIL", 15.1),
    "M2": ("p", "V1", "Vinp", "TAIL", 15.1),
    "M3": ("n", "ND", "ND", "0", 0.86),
    "M4": ("n", "V1", "ND", "0", 0.86),
    "M5": ("p", "NX", "VBP", "vdd", 6.9),
    "M6A": ("n", "NX", "NX", "0", 0.86),
    "M6B": ("n", "NX", "ND", "0", 0.86),
    "M7": ("n", "Vout", "NX", "0", 1.72),
    "M8": ("n", "NP", "V1", "0", 2.93),
    "M9": ("p", "NP", "NP", "vdd", 7.6),
    "M10": ("p", "V2", "NP", "vdd", 7.6),
    "M11": ("n", "V2", "VBN", "0", 1.9),
    "M12": ("p", "Vout", "VBP", "vdd", 116.6),
    "M13": ("n", "Vout", "V2", "0", 39.4),
    "M14": ("n", "Vout", "V1", "0", 2.93),
}
VBP, VBN = 0.725, 0.815


def dev(name):
    k = SIZES[name][0]
    return "@m.x%s.msky130_fd_pr__%sfet_01v8" % (name.lower(), k)


def netlist(vcm, vref, L):
    lines = ["* ngcc servo icmr point", INC, ".temp 27", ".option gmin=1e-15 reltol=1e-6 abstol=1e-15 vntol=1e-9 itl1=1000",
             "Vdd vdd 0 DC 1.8", "Vbp VBP 0 DC %g" % VBP, "Vbn VBN 0 DC %g" % VBN,
             "Vref vref 0 DC %g" % vref, "Vcm vcm 0 DC %g" % vcm,
             "Ee e 0 vref Vout 1",
             "Ep Vinp vcm e 0 0.5", "En Vinn vcm e 0 -0.5"]
    for n, (k, d, g, s, w) in SIZES.items():
        b = "vdd" if k == "p" else "0"
        w = w * L / 5e-7                      # W/L 유지 배율(L 바꿀 때 같은 전류밀도 근사)
        m = max(1, math.ceil(w / 10.0))          # 병렬 소자(m)로 모델 bin 폭 범위 안에 둠
        lines.append("X%s %s %s %s %s sky130_fd_pr__%sfet_01v8 l=%g w=%g m=%d" % (n, d, g, s, b, k, L, w / m * 1e-6, m))
    lines += ["CL Vout 0 10p", "Cm1 V1 Vout 1.68p", "Cm2 V2 Vout 1.32p"]
    sv = " ".join("%s[%s]" % (dev(n), p) for n in SIZES for p in ("vds", "vdsat", "id", "vgs"))
    lines += [".control", "set noaskquit", "option numdgt=12", "save all " + sv, "op",
              "print v(Vout) v(e) v(TAIL) v(ND) v(V1) v(V2) v(NX) v(NP)"]
    for n in SIZES:
        lines.append("print %s[vds] %s[vdsat] %s[id] %s[vgs]" % ((dev(n),) * 4))
    lines += ["tf v(e) vref", "print all", "quit", ".endc", ".end"]
    return "\n".join(lines) + "\n"


NUM = r"([-+]?\d+\.?\d*(?:[eE][-+]?\d+)?)"


def parse(out):
    vals = {}
    for m in re.finditer(r"^\s*([@\w\.\[\]\(\)\-:]+)\s*=\s*" + NUM + r"\s*$", out, re.M):
        vals[m.group(1).lower()] = float(m.group(2))
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("case")
    ap.add_argument("vref", type=float)
    ap.add_argument("lo", type=float, nargs="?", default=0.0)
    ap.add_argument("hi", type=float, nargs="?", default=1.8)
    ap.add_argument("step", type=float, nargs="?", default=0.02)
    ap.add_argument("--L", type=float, default=5e-7)
    a = ap.parse_args()
    work = HERE / ("icmr_%s_runs" % a.case)
    work.mkdir(exist_ok=True)
    rows = []
    n = int(round((a.hi - a.lo) / a.step))
    for i in range(n + 1):
        vcm = round(a.lo + i * a.step, 6)
        p = work / ("p%04d.cir" % i)
        p.write_text(netlist(vcm, a.vref, a.L), encoding="utf-8")
        r = subprocess.run([NG, "-b", str(p)], capture_output=True, text=True, cwd=str(work))
        v = parse(r.stdout)
        tfk = [k for k in v if k.startswith("transfer_function") or "transfer" in k]
        row = {"vcm": vcm, "ok": int("v(vout)" in v and bool(tfk))}
        if row["ok"]:
            de = v[tfk[0]]
            row["vout"] = v["v(vout)"]
            row["e"] = v["v(e)"]
            row["A"] = (1.0 / de - 1.0) if de != 0 else float("inf")
            row["A_db"] = 20 * math.log10(abs(row["A"])) if row["A"] not in (0, float("inf")) else float("nan")
            worst, wname = float("inf"), ""
            for nm in SIZES:
                d = dev(nm).lower()
                vds, vdsat, idv = abs(v.get(d + "[vds]", float("nan"))), abs(v.get(d + "[vdsat]", float("nan"))), v.get(d + "[id]", float("nan"))
                mg = vds - vdsat
                row["sat_" + nm] = mg
                row["id_" + nm] = idv
                if mg < worst:
                    worst, wname = mg, nm
            row["worst_sat"], row["worst_dev"] = worst, wname
            for k in ("tail", "nd", "v1", "v2", "nx", "np"):
                row[k] = v.get("v(%s)" % k, float("nan"))
        rows.append(row)
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    csv = HERE / ("icmr_%s.csv" % a.case)
    with open(csv, "w", encoding="utf-8") as f:
        f.write(",".join(keys) + "\n")
        for r in rows:
            f.write(",".join(str(r.get(k, "")) for k in keys) + "\n")
    ok = [r for r in rows if r["ok"]]
    summ = ["=== case %s vref=%g L=%g sweep %g..%g step %g ok=%d/%d" % (a.case, a.vref, a.L, a.lo, a.hi, a.step, len(ok), len(rows))]
    for r in ok:
        summ.append("vcm=%.3f vout=%.5f A_db=%.2f worst_sat=%+.4f(%s) tail=%.3f v1=%.3f nd=%.3f id_M0=%.3e id_M6A=%.3e" % (
            r["vcm"], r["vout"], r["A_db"], r["worst_sat"], r["worst_dev"], r["tail"], r["v1"], r["nd"], r["id_M0"], r["id_M6A"]))
    with open(HERE / "icmr_servo.log", "ab") as f:
        f.write(("\n".join(summ) + "\n").encode("utf-8"))
    print("\n".join(summ))


if __name__ == "__main__":
    main()
