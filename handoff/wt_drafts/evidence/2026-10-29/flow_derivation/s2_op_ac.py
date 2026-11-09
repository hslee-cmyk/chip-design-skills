"""S2. 바이어스점 .op 상세 + 개루프 AC: f_HP(= 1/(2 pi R_ps C_BAT)) 를 바꿔 doublet·DC 이득·GBW·PM 측정.
bench: sky130 tt, VDD 1.8, VCP 0.7, VCN 0.7, VCM 0.6 (S1 에서 M19~M21 밖 전 MOS 포화 여유 >= 0.13 V).
결과: s2_op_ac.txt (케이스마다 append)."""
import math, pathlib, sys
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from erfc_net import netlist, run, dev, ALL

HERE = pathlib.Path(__file__).parent
OUT = HERE / "s2_op_ac.txt"
B = dict(vdd=1.8, vcp=0.7, vcn=0.7, vcm=0.6)
CB = 1e-12


def log(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")
    print(s)


OUT.write_text("# S2 op + open-loop AC (sky130 tt, VDD 1.8, VCP 0.7, VCN 0.7, VCM 0.6, CL 70 pF)\n", encoding="utf-8")

# --- op 상세
prints = ["print v(x) v(y) v(z) v(n_m5g) v(n_m6g) v(n_m8g) v(n_m7d) v(n_m5s) v(n_m6s) v(n_m9d) v(n_m10d) v(out) v(a) v(b) i(vvdd)"]
for d in ALL:
    prints.append(f"print {dev(d)}[id] {dev(d)}[vgs] {dev(d)}[vds] {dev(d)}[vdsat] {dev(d)}[gm] {dev(d)}[gds] {dev(d)}[cgg]")
v, _ = run(HERE / "s2_op.cir", netlist(**B, cbat=CB, extra="\n".join([".control", "op"] + prints + [".endc", ".end"])))
log("## op (mode=mos, Table 1 M19~M21)")
for k in ["v(x)", "v(y)", "v(z)", "v(n_m5g)", "v(n_m6g)", "v(n_m8g)", "v(n_m7d)", "v(n_m5s)", "v(n_m6s)", "v(n_m9d)", "v(n_m10d)", "v(out)", "v(a)", "v(b)", "i(vvdd)"]:
    log(f"  {k} = {v.get(k)}")
log("| dev | id | vgs | vds | vdsat | gm | gds | cgg | gm/id |")
log("|---|---|---|---|---|---|---|---|---|")
for d in ALL:
    g = lambda p: v.get(f"{dev(d)}[{p}]")
    idd = g("id")
    log(f"| {d} | {idd:.3e} | {g('vgs'):.4f} | {g('vds'):.4f} | {g('vdsat'):.4f} | {g('gm'):.3e} | {g('gds'):.3e} | {g('cgg'):.3e} | {abs(g('gm')/idd) if idd else 0:.1f} |")
OPV = v


def ac_case(tag, **kw):
    deck = netlist(**B, cfg="ol", extra="\n".join([".control", "ac dec 40 1e-4 1e9",
                                                     "wrdata " + str(HERE / f"s2_ac_{tag}.dat").replace("\\", "/") + " vdb(out) vp(out) vdb(n_m5g) vdb(x)",
                                                     ".endc", ".end"]), **kw)
    run(HERE / f"s2_ac_{tag}.cir", deck)
    d = np.loadtxt(HERE / f"s2_ac_{tag}.dat")
    f = d[:, 0]; mag = d[:, 1]; ph = np.unwrap(d[:, 3]) * 180 / math.pi
    gdc = mag[0]
    i = np.where(mag < 0)[0][0]
    fu = f[i - 1] * (f[i] / f[i - 1]) ** (mag[i - 1] / (mag[i - 1] - mag[i]))
    phu = np.interp(math.log10(fu), np.log10(f), ph)
    pm = 180 - abs(phu - ph[0])   # 저주파 위상 기준 (vp 는 radian)
    # 1 kHz~10 kHz 구간 |A|*f (단일극 영역 이득-대역 곱)로 doublet 앞뒤 비교
    gbw_lo = lambda fx: 10 ** (np.interp(math.log10(fx), np.log10(f), mag) / 20) * fx
    np.save(HERE / f"s2_ac_{tag}.npy", d)
    return gdc, fu, pm, f, mag, ph


log("\n## open-loop AC")
log("| case | R_ps Ohm | C_BAT F | f_HP 계산 Hz | DC gain dB | f_u Hz | PM deg | |A|*f @0.1 f_u (Hz) | |A|*f @1e-3 f_u |")
log("|---|---|---|---|---|---|---|---|---|")
cases = [("const", dict(cbat=1e-18, mode="res", r_ps=1.0), "고정 게이트(Fig.5a, R 1 Ohm, CBAT->0)"), ("selfboot", dict(cbat=1e-18, mode="res", r_ps=1e9), "CBAT->0, R 1 GOhm(게이트 자기 Cgs 결합)")]
for fhp in (1e0, 1e2, 1e4, 1e5, 3e5, 1e6, 3e6, 1e7):
    cases.append((f"res_f{fhp:.0e}", dict(cbat=CB, mode="res", r_ps=1 / (2 * math.pi * fhp * CB)), ""))
cases.append(("mos", dict(cbat=CB, mode="mos"), "Table 1 M19~M21"))
for cb in (0.1e-12, 10e-12):
    for fx in (1e2, 1e5):
        cases.append((f"res_f{fx:.0e}_C{cb:.0e}", dict(cbat=cb, mode="res", r_ps=1 / (2 * math.pi * fx * cb)), ""))
for tag, kw, note in cases:
    gdc, fu, pm, f, mag, ph = ac_case(tag, **kw)
    af = lambda fx: 10 ** (np.interp(math.log10(fx), np.log10(f), mag) / 20) * fx
    fhp = 1 / (2 * math.pi * kw["r_ps"] * kw["cbat"]) if kw.get("mode") == "res" else float("nan")
    log(f"| {tag} {note} | {kw.get('r_ps', 'mos')} | {kw['cbat']} | {fhp:.3g} | {gdc:.3f} | {fu:.4g} | {pm:.2f} | {af(fu / 10):.4g} | {af(fu / 1e3):.4g} |")
