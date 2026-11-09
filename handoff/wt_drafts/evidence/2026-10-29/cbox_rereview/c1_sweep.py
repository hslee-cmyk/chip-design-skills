"""C1. erfc_ota 결합 커패시터 값 sweep -- 첫 주기 대신호 SR(정류 표류 전, 원문 측정 조건 꼴 600 mV p-p 100 kHz 구형파,
단위이득 반전 beta 1/2 = flow_derivation S3/S6 bench 'inve' 그대로) 와 실측 결합비 alpha.
변형: both  = CBAT1_L/R = CBAT2 = C
      c1    = CBAT1_L/R = C, CBAT2 = 10 pF (X->M5/M6 게이트 결합만 변화)
      c2    = CBAT1_L/R = 10 pF, CBAT2 = C (n_m7d->M7/M8 게이트 결합만 변화)
alpha1 = (g5 상승 최대 - 정지)/(X 상승 최대 - 정지) (상승 edge), alpha1R = (g6 상승 최대 - 정지)/(Y 상승 최대 - 정지) (하강 edge),
alpha2 = (n_m8g 하강 - 정지)/(n_m7d 하강 - 정지) (상승 edge).
결과: c1_sweep.txt (케이스마다 append). 인자: 변형 이름들(없으면 셋 다)."""
import pathlib, sys
import numpy as np
FD = pathlib.Path(__file__).parent.parent / "flow_derivation"
sys.path.insert(0, str(FD))
from erfc_net import netlist, run, dev  # noqa: E402

HERE = pathlib.Path(__file__).parent
OUT = HERE / "c1_sweep.txt"
B = dict(vdd=1.8, vcp=0.7, vcn=0.7, vcm=0.6)
PER = 10e-6
AMP = 0.6
CS = [0.02e-12, 0.05e-12, 0.1e-12, 0.15e-12, 0.2e-12, 0.3e-12, 0.5e-12, 0.7e-12, 1e-12, 2e-12, 5e-12, 10e-12]
SR_SPEC = 19.32e6
CL = 70e-12


def sr_edge(t, o, e0):
    m = (t >= e0) & (t <= e0 + PER / 2 - 2e-9)
    tt, oo = t[m], o[m]
    v0 = np.interp(e0 - 2e-9, t, o)
    step = oo[-1] - v0
    fr = (oo - v0) / step
    i10 = np.argmax(fr >= 0.1); i90 = np.argmax(fr >= 0.9)
    return 0.8 * abs(step) / (tt[i90] - tt[i10]) / 1e6 if tt[i90] > tt[i10] else float("nan")


def case(var, c):
    c1, c2 = {"both": (c, c), "c1": (c, 10e-12), "c2": (10e-12, c)}[var]
    lo, hi = B["vcm"] - AMP / 2, B["vcm"] + AMP / 2
    stim = f"vsig vsig 0 pulse({lo} {hi} {PER/4} 1n 1n {PER/2 - 1e-9} {PER})"
    tag = f"c1_{var}_{c:.2e}"
    dat = str(HERE / f"{tag}.dat").replace("\\", "/")
    ids = [f"{dev(d)}[id]" for d in ("M8", "M6", "M3B", "M5")]
    deck = netlist(**B, cfg="inve", stim=stim, cbat=c1, cbat2=c2, mode="mos", extra="\n".join([
        ".control", "save all " + " ".join(f"@m.x{d.lower()}.msky130_fd_pr__{'pfet' if d == 'M8' else 'nfet'}_01v8[id]" for d in ("M8", "M6", "M3B", "M5")),
        f"tran 2n {PER + PER/4} 0 5n",
        f"wrdata {dat} v(out) v(x) v(y) v(n_m5g) v(n_m6g) v(n_m8g) v(n_m7d) v(n_m5s) v(n_m6s) v(n_m9d) v(n_m10d) " + " ".join(ids),
        ".endc", ".end"]))
    run(HERE / f"{tag}.cir", deck)
    d = np.loadtxt(dat)
    t = d[:, 0]
    col = lambda k: d[:, 2 * k + 1]
    o, x, y, g5, g6, g8, n7d, s5, s6, n9d, n10d, i8, i6, i3b, i5 = (col(k) for k in range(15))
    q = lambda w: np.interp(PER / 4 - 2e-9, t, w)
    fall_e, rise_e = PER / 4, PER / 4 + PER / 2
    wf = (t >= fall_e) & (t < rise_e)
    wr = (t >= rise_e)
    sr_f = sr_edge(t, o, fall_e); sr_r = sr_edge(t, o, rise_e)
    # 상승 edge(out 상승): X 상승 -> g5 상승, n_m7d 하강 -> n_m8g 하강
    dx = x[wr].max() - q(x); dg5 = g5[wr].max() - q(g5)
    d7 = n7d[wr].min() - q(n7d); dg8 = g8[wr].min() - q(g8)
    # 하강 edge(out 하강): Y 상승 -> g6 상승
    dy = y[wf].max() - q(y); dg6 = g6[wf].max() - q(g6)
    a1 = dg5 / dx if dx > 1e-6 else float("nan")
    a2 = dg8 / d7 if abs(d7) > 1e-6 else float("nan")
    a1r = dg6 / dy if dy > 1e-6 else float("nan")
    ipk_r = np.abs(i8[wr]).max(); ipk_f = np.abs(i6[wf]).max()
    s5min = s5[wr].min(); n9max = n9d[wr].max(); n10max = n10d[wr].max()
    with OUT.open("a", encoding="utf-8") as f:
        f.write(f"| {var} | {c*1e12:.3g} | {c1*1e12:.3g} | {c2*1e12:.3g} | {sr_f:.2f} | {sr_r:.2f} | {dx:.3f} | {dg5:.3f} | {a1:.3f} | "
                f"{d7:.3f} | {dg8:.3f} | {a2:.3f} | {dy:.3f} | {dg6:.3f} | {a1r:.3f} | {ipk_r*1e3:.3f} | {ipk_f*1e3:.3f} | "
                f"{s5min:.4f} | {n9max:.3f} | {n10max:.3f} | {'PASS' if sr_r * 1e6 >= SR_SPEC else 'FAIL'} |\n")
    pathlib.Path(dat).unlink()


if __name__ == "__main__":
    vars_ = sys.argv[1:] or ["both", "c1", "c2"]
    if not OUT.exists():
        OUT.write_text("# C1 sweep (sky130 tt, VDD 1.8, VCP 0.7, VCN 0.7, VCM 0.6, CL 70 pF, MOS pseudo-R, 첫 주기)\n"
                       f"# SR spec(driving_spec) 19.32 V/us -> I_req = CL*SR = {CL*SR_SPEC*1e3:.3f} mA\n"
                       "| var | C pF | CBAT1 pF | CBAT2 pF | SR fall | SR rise | dX | dg5 | alpha1 | dn7d | dg8 | alpha2 | dY | dg6 | alpha1R | |I_M8| pk mA | |I_M6| pk mA | n_m5s min | n_m9d max | n_m10d max | rise vs spec |\n"
                       "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n", encoding="utf-8")
    for v in vars_:
        for c in CS:
            case(v, c)
    print(OUT.read_text(encoding="utf-8"))
