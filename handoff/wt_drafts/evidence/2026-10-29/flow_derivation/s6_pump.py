"""S6. 대신호 반복(600 mV p-p 100 kHz 구형파, 원문 SR 측정 조건 꼴)에서 부유 전지 게이트 DC 표류(정류, pumping).
선형 R(대칭) 대 MOS pseudo-resistor(비대칭 I-V)를 비교. 주기마다 edge 직전 게이트·n_m5s 값, 반주기 끝 정착 오차, 10-90 % SR.
인자: tag(mos|res_f1e3|...) NPER.  결과: s6_pump.txt (케이스마다 append)."""
import math, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from erfc_net import netlist, run

HERE = pathlib.Path(__file__).parent
OUT = HERE / "s6_pump.txt"
B = dict(vdd=1.8, vcp=0.7, vcn=0.7, vcm=0.6)
PER = 10e-6
tag = sys.argv[1]
NPER = int(sys.argv[2])
cb = float(sys.argv[3]) if len(sys.argv) > 3 else 1e-12
if tag == "mos":
    kw = dict(cbat=cb, mode="mos")
else:
    fhp = float(tag.split("_f")[1])
    kw = dict(cbat=cb, mode="res", r_ps=1 / (2 * math.pi * fhp * cb))
amp = 0.6
lo, hi = B["vcm"] - amp / 2, B["vcm"] + amp / 2
stim = f"vsig vsig 0 pulse({lo} {hi} {PER/4} 1n 1n {PER/2 - 1e-9} {PER})"
dat = str(HERE / f"s6_{tag}_C{cb:.0e}_{NPER}.dat").replace("\\", "/")
deck = netlist(**B, cfg="inve", stim=stim, extra="\n".join([
    ".control", f"tran 5n {NPER*PER + PER/4} 0 10n",
    f"wrdata {dat} v(out) v(n_m5g) v(n_m6g) v(n_m8g) v(n_m5s) v(n_m6s)",
    ".endc", ".end"]), **kw)
run(HERE / f"s6_{tag}_C{cb:.0e}_{NPER}.cir", deck)
d = np.loadtxt(dat)
t = d[:, 0]; o = d[:, 1]; g5 = d[:, 3]; g6 = d[:, 5]; g8 = d[:, 7]; s5 = d[:, 9]; s6 = d[:, 11]
with OUT.open("a", encoding="utf-8") as f:
    f.write(f"\n## {tag} C_BAT {cb} ({NPER} periods)\n| period | g5 pre-rise | g6 pre-rise | g8 pre-rise | n_m5s pre | n_m6s pre | fall-edge SR V/us | rise-edge SR V/us | err @ end of half (rise edge, % of step) |\n|---|---|---|---|---|---|---|---|---|\n")
    for k in range(NPER):
        te = k * PER + PER / 4
        pre = lambda w: np.interp(te - 2e-9, t, w)
        srs = []
        for e0 in (te, te + PER / 2):
            m = (t >= e0) & (t <= e0 + PER / 2 - 2e-9)
            tt, oo = t[m], o[m]
            v0 = np.interp(e0 - 2e-9, t, o); step = oo[-1] - v0
            fr = (oo - v0) / step
            i10 = np.argmax(fr >= 0.1); i90 = np.argmax(fr >= 0.9)
            srs.append(0.8 * abs(step) / (tt[i90] - tt[i10]) / 1e6 if tt[i90] > tt[i10] else float("nan"))
        # 반주기 끝 오차: 이상 목표 = 2 vcm - vsig
        e0 = te; tend = e0 + PER / 2 - 2e-9
        ideal = 2 * B["vcm"] - hi
        err = (np.interp(tend, t, o) - ideal) / amp * 100
        if k < 5 or k % max(1, NPER // 12) == 0 or k == NPER - 1:
            f.write(f"| {k} | {pre(g5):.4f} | {pre(g6):.4f} | {pre(g8):.4f} | {pre(s5):.4f} | {pre(s6):.4f} | {srs[0]:.2f} | {srs[1]:.2f} | {err:+.3f} |\n")
print(open(OUT, encoding="utf-8").read()[-3000:])
