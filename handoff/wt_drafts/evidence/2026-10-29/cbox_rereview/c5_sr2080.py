"""C5. 계획 O-122 의 oracle SR 정의(20-80 % 기울기)로 상승·하강 SR 재측정 -- c1_sweep(10-90 %)과 경계 C 비교.
bench 는 c1_sweep 과 같음(600 mV p-p 구형파, 원문 측정 조건; oracle '전 폭 계단' 크기는 SF-1 몫이라 여기서는 원문 크기).
결과: c5_sr2080.txt (케이스마다 append)."""
import pathlib, sys
import numpy as np
FD = pathlib.Path(__file__).parent.parent / "flow_derivation"
sys.path.insert(0, str(FD))
from erfc_net import netlist, run  # noqa: E402

HERE = pathlib.Path(__file__).parent
OUT = HERE / "c5_sr2080.txt"
B = dict(vdd=1.8, vcp=0.7, vcn=0.7, vcm=0.6)
PER, AMP = 10e-6, 0.6


def sr(t, o, e0, a, b):
    m = (t >= e0) & (t <= e0 + PER / 2 - 2e-9)
    tt, oo = t[m], o[m]
    v0 = np.interp(e0 - 2e-9, t, o); step = oo[-1] - v0; fr = (oo - v0) / step
    ta = tt[np.argmax(fr >= a)]; tb = tt[np.argmax(fr >= b)]
    return (b - a) * abs(step) / (tb - ta) / 1e6


def case(var, c):
    c1, c2 = {"both": (c, c), "c1": (c, 10e-12), "c2": (10e-12, c)}[var]
    lo, hi = B["vcm"] - AMP / 2, B["vcm"] + AMP / 2
    stim = f"vsig vsig 0 pulse({lo} {hi} {PER/4} 1n 1n {PER/2 - 1e-9} {PER})"
    tag = f"c5_{var}_{c:.2e}"
    dat = str(HERE / f"{tag}.dat").replace("\\", "/")
    deck = netlist(**B, cfg="inve", stim=stim, cbat=c1, cbat2=c2, mode="mos", extra="\n".join([
        ".control", f"tran 1n {PER + PER/4} 0 2n", f"wrdata {dat} v(out)", ".endc", ".end"]))
    run(HERE / f"{tag}.cir", deck)
    d = np.loadtxt(dat); pathlib.Path(dat).unlink()
    t, o = d[:, 0], d[:, 1]
    fe, re_ = PER / 4, PER / 4 + PER / 2
    v = [sr(t, o, fe, .2, .8), sr(t, o, re_, .2, .8), sr(t, o, fe, .1, .9), sr(t, o, re_, .1, .9)]
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"| {var} | {c*1e12:.3g} | " + " | ".join(f"{x:.2f}" for x in v) +
                f" | {'PASS' if min(v[0], v[1]) >= 19.32 else 'FAIL'} |\n")


if __name__ == "__main__":
    OUT.write_text("# C5 SR 20-80 % (O-122 정의) 대 10-90 %, spec 19.32 V/us, 판정 = 방향별 min(20-80 %)\n"
                   "| var | C pF | fall 20-80 | rise 20-80 | fall 10-90 | rise 10-90 | 판정 |\n|---|---|---|---|---|---|---|\n",
                   encoding="utf-8")
    for var in ("both", "c1", "c2"):
        for c in (0.1e-12, 0.2e-12, 0.3e-12, 0.5e-12, 0.7e-12, 1e-12, 1.5e-12, 2e-12, 3e-12, 5e-12, 10e-12):
            case(var, c)
    print(OUT.read_text(encoding="utf-8"))
