"""C3. 결합 C 하한의 물리 결정자 분리: (a) 전하 분배 alpha = C/(C + C_g) 만인가, (b) 슬루 동안 pseudo-R 역방향 전도
(게이트가 VCN/VCP 를 넘으면 M19~M21 소스·드레인이 바뀌어 지수 전도 -- flow_derivation 2절)로 게이트가 처지는 것인가.
같은 bench(c1_sweep 'both')에서 M19~M21 을 (mos) Table 1 MOS 그대로 / (ideal) 선형 R 1e15 Ohm(누설 0 근사) 로 바꿔
상승 edge 의 10 %·90 % 시점 결합 효율 a(t) = (g5(t) - g5_q)/(X(t) - X_q), b(t) = (g8(t) - g8_q)/(n7d(t) - n7d_q) 과 SR 을 잰다.
결과: c3_droop.txt (케이스마다 append)."""
import pathlib, sys
import numpy as np
FD = pathlib.Path(__file__).parent.parent / "flow_derivation"
sys.path.insert(0, str(FD))
from erfc_net import netlist, run  # noqa: E402

HERE = pathlib.Path(__file__).parent
OUT = HERE / "c3_droop.txt"
B = dict(vdd=1.8, vcp=0.7, vcn=0.7, vcm=0.6)
PER, AMP = 10e-6, 0.6


def case(mode, c):
    lo, hi = B["vcm"] - AMP / 2, B["vcm"] + AMP / 2
    stim = f"vsig vsig 0 pulse({lo} {hi} {PER/4} 1n 1n {PER/2 - 1e-9} {PER})"
    tag = f"c3_{mode}_{c:.2e}"
    dat = str(HERE / f"{tag}.dat").replace("\\", "/")
    kw = dict(mode="mos") if mode == "mos" else dict(mode="res", r_ps=1e15)
    deck = netlist(**B, cfg="inve", stim=stim, cbat=c, extra="\n".join([
        ".control", f"tran 2n {PER + PER/4} 0 5n",
        f"wrdata {dat} v(out) v(x) v(n_m5g) v(n_m7d) v(n_m8g)", ".endc", ".end"]), **kw)
    run(HERE / f"{tag}.cir", deck)
    d = np.loadtxt(dat); pathlib.Path(dat).unlink()
    t = d[:, 0]; o, x, g5, n7, g8 = (d[:, 2 * k + 1] for k in range(5))
    q = lambda w: np.interp(PER / 4 - 2e-9, t, w)
    out = []
    for e0 in (PER / 4 + PER / 2,):          # 상승 edge
        m = (t >= e0) & (t <= e0 + PER / 2 - 2e-9)
        tt = t[m]; oo = o[m]
        v0 = np.interp(e0 - 2e-9, t, o); step = oo[-1] - v0; fr = (oo - v0) / step
        t10 = tt[np.argmax(fr >= 0.1)]; t90 = tt[np.argmax(fr >= 0.9)]
        sr = 0.8 * abs(step) / (t90 - t10) / 1e6
        a = lambda tx: (np.interp(tx, t, g5) - q(g5)) / (np.interp(tx, t, x) - q(x))
        b = lambda tx: (np.interp(tx, t, g8) - q(g8)) / (np.interp(tx, t, n7) - q(n7))
        out = [sr, (t90 - t10) * 1e9, a(t10), a(t90), b(t10), b(t90), np.interp(t90, t, g5), np.interp(t90, t, g8)]
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"| {mode} | {c*1e12:.3g} | " + " | ".join(f"{v:.3f}" for v in out) + " |\n")


if __name__ == "__main__":
    OUT.write_text("# C3 상승 edge: SR 과 10 %/90 % 시점 결합 효율 (mos = Table 1 pseudo-R, ideal = 선형 R 1e15 Ohm)\n"
                   "| mode | C pF | SR rise V/us | t10-90 ns | a(t10) CBAT1 | a(t90) CBAT1 | b(t10) CBAT2 | b(t90) CBAT2 | g5(t90) V | g8(t90) V |\n"
                   "|---|---|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
    for mode in ("mos", "ideal"):
        for c in (0.05e-12, 0.1e-12, 0.2e-12, 0.3e-12, 1e-12, 10e-12):
            case(mode, c)
    print(OUT.read_text(encoding="utf-8"))
