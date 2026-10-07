# -*- coding: utf-8 -*-
"""Idealised small-signal (VCCS+R only) netlist of the FULL corrected circuit:
stage-1 current-reuse telescopic (2 branches) + Monticelli class-AB stage-2
(ideal floating battery: Vg15==Vg16==stage-1 out) + corrected Fig.5 CMFB.
Runs ngspice AC and reports Adm / Acm / CMRR, to cross-check the closed form."""
import math
import os
import re
import subprocess
import tempfile

NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"


def mos(name, d, s, g, gm, gds):
    """small-signal MOSFET: current d->s = gm*v(g,s) + gds*v(d,s). Polarity-agnostic."""
    out = []
    if gm:
        out.append(f"G{name} {d} {s} {g} {s} {gm:.12g}")
    out.append(f"R{name} {d} {s} {1.0/gds:.12g}")
    return out


def build(p, mode):
    """mode: 'dm' or 'cm'."""
    L = [".title cmfb cmrr", ".options gmin=1e-18 abstol=1e-18"]
    if mode == "dm":
        L += ["Vip vip 0 AC 0.5", "Vim vim 0 AC -0.5"]
    else:
        L += ["Vip vip 0 AC 1", "Vim vim 0 AC 1"]

    # ---- stage 1 (shared tails vx / vy) --------------------------------------
    L += mos("6", "vx", "0", "0", 0.0, p["gds6"])
    L += mos("7", "vx", "0", "vcmfb", p["gm7"], p["gds7"])
    L += mos("5", "vy", "0", "0", 0.0, p["gds5"])
    for br, gin in (("a", "vip"), ("b", "vim")):
        o = f"vo1{br}"
        L += mos(f"1{br}", f"n1{br}", "vx", gin, p["gm1"], p["gds1"])
        L += mos(f"2{br}", o, f"n1{br}", "0", p["gm2"], p["gds2"])
        L += mos(f"3{br}", o, f"n3{br}", "0", p["gm3"], p["gds3"])
        L += mos(f"4{br}", f"n3{br}", "vy", gin, p["gm4"], p["gds4"])

    # ---- stage 2: class-AB, ideal Monticelli battery -> vg15 == vg16 == vo1 --
    # cross-coupled: Vom driven by vo1b, Vop driven by vo1a  (paper Fig.1)
    for out, drv in (("vom", "vo1b"), ("vop", "vo1a")):
        L += mos(f"15{out}", out, "0", drv, p["gm15"], p["gds15"])
        L += mos(f"16{out}", out, "0", drv, p["gm16"], p["gds16"])

    # ---- CMFB (corrected Fig.5) ---------------------------------------------
    L += [f"R1cm vom voc {p['Rcm']:.12g}", f"R2cm voc vop {p['Rcm']:.12g}"]
    L += mos("36a", "vcmfb", "0", "vcmfb", p["gm36a"], p["gds36a"])   # pmos diode
    L += mos("36b", "n36b", "0", "n36b", p["gm36b"], p["gds36b"])     # pmos diode
    L += mos("37a", "vcmfb", "ntail", "voc", p["gm37a"], p["gds37a"])
    L += mos("37b", "n36b", "ntail", "vocdes", p["gm37b"], p["gds37b"])
    L += mos("38", "ntail", "0", "0", 0.0, p["gds38"])
    L += mos("39", "vocdes", "0", "vocdes", p["gm39"], p["gds39"])    # pmos diode
    L += mos("40", "0", "vocdes", "0", p["gm40"], p["gds40"])         # pmos, src=vocdes
    L += [".ac dec 1 1 1", ".print ac v(vom) v(vop) v(vcmfb) v(vo1a) v(vo1b) v(vocdes)",
          ".end", ""]
    return "\n".join(L)


def run(p, mode):
    d = tempfile.mkdtemp()
    f = os.path.join(d, "n.cir")
    open(f, "w").write(build(p, mode))
    r = subprocess.run([NG, "-b", f], capture_output=True, text=True, timeout=120)
    txt = r.stdout + r.stderr
    vals = {}
    for line in txt.splitlines():
        m = re.match(r"\s*0\s+1\.0+e\+00\s+(.*)", line)
        if m:
            pass
    # ngspice prints one column block per variable; parse "index frequency value"
    cur = None
    for line in txt.splitlines():
        m = re.match(r"\s*Index\s+frequency\s+(\S+)", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r"\s*0\s+1\.0+e\+00\s+([-\d.eE+]+)", line)
        if m and cur:
            vals[cur] = float(m.group(1))
            cur = None
    if not vals:
        raise RuntimeError("ngspice parse failed:\n" + txt[-3000:])
    return vals


def analytic(p):
    Kp_prime = p["gm2"] / (p["gds1"] * p["gds2"])
    Kn_prime = p["gm3"] / (p["gds4"] * p["gds3"])
    Adm1 = (p["gm1"] + p["gm4"]) * (Kp_prime * Kn_prime / (Kp_prime + Kn_prime))
    Kp, Kn = p["gm1"] * Kp_prime, p["gm4"] * Kn_prime
    Rx = 1.0 / (p["gds6"] + p["gds7"])
    Ry = 1.0 / p["gds5"]
    Acm1 = (Rx + Ry) * Kn * Kp / (Kn * Ry + Kp * Rx)
    H = -p["gm7"] * (Rx * Kp) * (Ry * Kn) / (Rx * Kp + Ry * Kn)
    a = p["gm36a"] + p["gds36a"]
    b = p["gm36b"] + p["gds36b"]
    A1 = a * (p["gm37a"] + p["gds37a"]) / (a + p["gds37a"])
    A0 = a * p["gm37a"] / (a + p["gds37a"])
    B1 = b * (p["gm37b"] + p["gds37b"]) / (b + p["gds37b"])
    vt = A0 / (A1 + B1 + p["gds38"])
    Ac = ((p["gm37a"] + p["gds37a"]) * vt - p["gm37a"]) / (a + p["gds37a"])
    G2 = -(p["gm15"] + p["gm16"]) / (p["gds15"] + p["gds16"])
    T = -H * Ac * G2
    return dict(Adm1=Adm1, Acm1=Acm1, H=H, Ac=Ac, G2=G2, T=T,
                cmrr_db=20 * math.log10(abs(Adm1 / Acm1) * abs(1 + T)))


BASE = dict(gm1=119e-6, gds1=1/600e3, gm2=130e-6, gds2=1/700e3,
            gm4=140e-6, gds4=1/250e3, gm3=150e-6, gds3=1/300e3,
            gds6=0.5e-6, gm7=90e-6, gds7=0.4e-6, gds5=1.0e-6,
            gm15=3.0e-3, gds15=8e-6, gm16=3.0e-3, gds16=9e-6,
            gm36a=80e-6, gds36a=0.8e-6, gm36b=84e-6, gds36b=0.9e-6,
            gm37a=100e-6, gds37a=1.0e-6, gm37b=105e-6, gds37b=1.1e-6,
            gm39=85e-6, gds39=0.7e-6, gm40=88e-6, gds40=0.6e-6,
            gds38=1.2e-6, Rcm=1e9)


def report(p, tag):
    dm = run(p, "dm")
    cm = run(p, "cm")
    adm = abs(dm["v(vom)"] - dm["v(vop)"])
    acm = abs((cm["v(vom)"] + cm["v(vop)"]) / 2.0)
    spice_db = 20 * math.log10(adm / acm)
    an = analytic(p)
    print(f"[{tag}] SPICE: Adm={adm:.6g} Acm={acm:.6g} CMRR={spice_db:.4f} dB "
          f"| v(vocdes)_cm={cm['v(vocdes)']:.3g}")
    print(f"        analytic CMRR={an['cmrr_db']:.4f} dB  (delta {an['cmrr_db']-spice_db:+.4f} dB)"
          f"  A_c={an['Ac']:.4f} G2={an['G2']:.4g} T={an['T']:.4g}")
    return spice_db, an


if __name__ == "__main__":
    import random
    report(dict(BASE), "anchor1")
    p2 = dict(BASE); p2["gds5"] = 1.0e-6 * 0.05; p2["gm7"] = 90e-6 * 4
    report(p2, "anchor2")
    random.seed(7)
    worst = 0.0
    for i in range(25):
        p = dict(BASE)
        for k in p:
            if k != "Rcm":
                p[k] *= math.exp(random.uniform(-math.log(4), math.log(4)))
        s, a = report(p, f"rand{i}")
        worst = max(worst, abs(a["cmrr_db"] - s))
    print("WORST |analytic-spice| =", round(worst, 4), "dB")
