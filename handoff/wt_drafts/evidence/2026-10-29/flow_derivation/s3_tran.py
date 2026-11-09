"""S3. 폐루프 계단(원문 p.13~14 조건 꼴): 단위이득 반전(beta 1/2), 100 kHz 50 % 구형파,
(i) 10 mV p-p 소신호 -> 1 % 정착 시간·느린 꼬리, (ii) 600 mV p-p 대신호 -> 평균 SR·게이트 전압(전지) 처짐·정착.
f_HP 를 R_ps(선형 저항) 로 바꾸고, 고정 게이트(CBAT->0)·Table 1 MOS pseudo-resistor 와 비교.
결과: s3_tran.txt (케이스마다 append), 파형 s3_<tag>_<amp>.npy"""
import math, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from erfc_net import netlist, run

HERE = pathlib.Path(__file__).parent
OUT = HERE / "s3_tran.txt"
B = dict(vdd=1.8, vcp=0.7, vcn=0.7, vcm=0.6)
CB = 1e-12
PER = 10e-6
NPER = int(sys.argv[1]) if len(sys.argv) > 1 else 3


def log(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s, flush=True)


def sim(tag, amp, **kw):
    lo, hi = B["vcm"] - amp / 2, B["vcm"] + amp / 2
    stim = f"vsig vsig 0 pulse({lo} {hi} {PER/4} 1n 1n {PER/2 - 1e-9} {PER})"
    dat = str(HERE / f"s3_{tag}_{int(amp*1000)}mV.dat").replace("\\", "/")
    deck = netlist(**B, cfg="inve", stim=stim, extra="\n".join([
        ".control", f"tran 2n {NPER*PER + PER/4} 0 5n",
        f"wrdata {dat} v(out) v(vsig) v(n_m5g) v(n_m6g) v(n_m8g) v(x) v(y) v(n_m5s) v(n_m6s) v(n_m7d) v(z)",
        ".endc", ".end"]), **kw)
    run(HERE / f"s3_{tag}_{int(amp*1000)}mV.cir", deck)
    d = np.loadtxt(dat)
    cols = ["t", "out", "vsig", "n_m5g", "n_m6g", "n_m8g", "x", "y", "n_m5s", "n_m6s", "n_m7d", "z"]
    w = {c: d[:, 0 if i == 0 else 2 * i - 1] for i, c in enumerate(cols)}
    np.save(HERE / f"s3_{tag}_{int(amp*1000)}mV.npy", d)
    return w


def edges_metrics(w, amp):
    """마지막 주기의 상승·하강 두 edge 각각: 1 % 정착 시간, 평균 SR(10-90 %), 반주기 끝 값, 꼬리(edge 뒤 2 us·4 us 오차)."""
    t, o = w["t"], w["out"]
    res = []
    last = (NPER - 1) * PER + PER / 4
    for k, te in enumerate((last, last + PER / 2)):
        tend = te + PER / 2 - 2e-9
        m = (t >= te) & (t <= tend)
        tt, oo = t[m], o[m]
        vf = oo[-1]
        v0 = np.interp(te - 1e-9, t, o)
        step = vf - v0
        err = np.abs(oo - vf)
        bad = np.where(err > 0.01 * abs(step))[0]
        ts = tt[bad[-1]] - te if len(bad) else 0.0
        # SR: 10 % -> 90 %
        frac = (oo - v0) / step
        i10 = np.argmax(frac >= 0.1); i90 = np.argmax(frac >= 0.9)
        sr = 0.8 * abs(step) / (tt[i90] - tt[i10]) if tt[i90] > tt[i10] else float("nan")
        e2 = (np.interp(te + 2e-6, t, o) - vf) / step
        e1 = (np.interp(te + 1e-6, t, o) - vf) / step
        g = {n: (np.interp(te - 1e-9, t, w[n]), np.max(w[n][m]), np.min(w[n][m]), w[n][m][-1]) for n in ("n_m5g", "n_m6g", "n_m8g", "x", "y", "n_m5s", "n_m6s")}
        res.append(dict(edge="rise" if k == 0 else "fall", step=step, ts=ts, sr=sr, e1=e1, e2=e2, g=g))
    return res


if __name__ == "__main__":
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    if which == "all":
        OUT.write_text(f"# S3 closed-loop step (unity-gain inverting, beta 1/2, 100 kHz square, {NPER} periods, metrics on last period)\n", encoding="utf-8")
    cases = [("const", dict(cbat=1e-18, mode="res", r_ps=1.0))]   # 게이트를 VCN 에 1 Ohm 로 고정(Fig.5a)
    for fhp in (1e1, 1e3, 1e4, 1e5, 1e6):
        cases.append((f"res_f{fhp:.0e}", dict(cbat=CB, mode="res", r_ps=1 / (2 * math.pi * fhp * CB))))
    cases.append(("mos", dict(cbat=CB, mode="mos")))
    for amp in (0.01, 0.6):
        log(f"\n## amp {amp*1000:.0f} mV p-p")
        log("| case | edge | step V | 1% ts ns | SR V/us (10-90) | err@+1us | err@+2us | gate5 pre/max/min/end | gate8 pre/max/min/end | x pre/max/min | n_m5s pre/min |")
        log("|---|---|---|---|---|---|---|---|---|---|---|")
        for tag, kw in cases:
            w = sim(tag, amp, **kw)
            for r in edges_metrics(w, amp):
                g = r["g"]
                f4 = lambda q: "/".join(f"{x:.3f}" for x in q)
                log(f"| {tag} | {r['edge']} | {r['step']:+.4f} | {r['ts']*1e9:.0f} | {r['sr']/1e6:.2f} | {r['e1']:+.2e} | {r['e2']:+.2e} | "
                    f"{f4(g['n_m5g'])} | {f4(g['n_m8g'])} | {f4(g['x'][:3])} | {g['n_m5s'][0]:.3f}/{g['n_m5s'][2]:.3f} |")
