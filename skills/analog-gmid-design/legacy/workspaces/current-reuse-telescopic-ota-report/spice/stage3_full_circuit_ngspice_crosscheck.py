# -*- coding: utf-8 -*-
"""세션21 2차(topology-무관 일반화) -- 51소자 전체(1단+2단+CMFB+bias-gen 전부) + R1/R2/Rz1/Rz2
(1GΩ, Cc1/Cc2는 DC/mid-band 개방회로라 제외)를 ngspice AC로 독립 검증한다. connectivity는
`load_topology()`로 topology.json에서 그대로 읽는다(손타이핑 없음) -- `sizing_recipe.py`의
`_metric_smallsignal_ratio_db()`(순수 Python Gaussian elimination)와 완전히 다른 솔버로
같은 회로를 풀어 대조."""
import math
import os
import re
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.abspath(os.path.join(
    _HERE, "..", "..", "..", "skills", "analog-gmid-design", "assets"))
sys.path.insert(0, _ASSETS)
from stick_diagram import load_topology  # noqa: E402

NG = r"C:\ngspice\Spice64\bin\ngspice_con.exe"
TOPO_JSON = os.path.join(_ASSETS, "library", "current_reuse_telescopic_ota.topology.json")

# self-test(sizing_recipe.py, 세션21 2차)와 완전히 동일한 파라미터.
GM = {"M1a": 119e-6, "M1b": 119e-6, "M2a": 130e-6, "M2b": 130e-6,
      "M4a": 140e-6, "M4b": 140e-6, "M3a": 150e-6, "M3b": 150e-6,
      "M6": 0.0, "M7": 90e-6, "M5": 0.0,
      "M8": 40e-6, "M17": 40e-6, "M9a": 50e-6, "M9b": 50e-6, "M18a": 50e-6, "M18b": 50e-6,
      "M11a": 30e-6, "M11b": 30e-6, "M20a": 30e-6, "M20b": 30e-6,
      "M12": 0.0, "M21": 0.0, "M10": 0.0, "M19": 0.0,
      "M13": 40e-6, "M22": 40e-6, "M14a": 30e-6, "M14b": 30e-6, "M23a": 30e-6, "M24b": 30e-6,
      "M15": 3.0e-3, "M16": 3.0e-3, "M25": 3.0e-3, "M26": 3.0e-3,
      "M37a": 100e-6, "M37b": 105e-6, "M36a": 80e-6, "M36b": 84e-6, "M38": 0.0,
      "M18_bg": 40e-6, "M60": 40e-6, "M61": 40e-6, "M64": 30e-6, "M63": 30e-6,
      "M58": 30e-6, "M57": 30e-6, "M66": 0.0, "M68": 0.0, "M39": 40e-6, "M40": 40e-6}
GDS = {"M1a": 1/600e3, "M1b": 1/600e3, "M2a": 1/700e3, "M2b": 1/700e3,
       "M4a": 1/250e3, "M4b": 1/250e3, "M3a": 1/300e3, "M3b": 1/300e3,
       "M6": 0.5e-6, "M7": 0.4e-6, "M5": 1.0e-6,
       "M8": 0.3e-6, "M17": 0.3e-6, "M9a": 0.4e-6, "M9b": 0.4e-6, "M18a": 0.4e-6, "M18b": 0.4e-6,
       "M11a": 0.5e-6, "M11b": 0.5e-6, "M20a": 0.5e-6, "M20b": 0.5e-6,
       "M12": 0.6e-6, "M21": 0.6e-6, "M10": 0.6e-6, "M19": 0.6e-6,
       "M13": 0.3e-6, "M22": 0.3e-6, "M14a": 0.5e-6, "M14b": 0.5e-6, "M23a": 0.5e-6, "M24b": 0.5e-6,
       "M15": 8e-6, "M16": 9e-6, "M25": 8e-6, "M26": 9e-6,
       "M37a": 1.0e-6, "M37b": 1.1e-6, "M36a": 0.8e-6, "M36b": 0.9e-6, "M38": 1.2e-6,
       "M18_bg": 0.3e-6, "M60": 0.3e-6, "M61": 0.3e-6, "M64": 0.5e-6, "M63": 0.5e-6,
       "M58": 0.5e-6, "M57": 0.5e-6, "M66": 0.6e-6, "M68": 0.6e-6, "M39": 0.3e-6, "M40": 0.3e-6}

R_DEFAULT = 1.0e9


def _devs_and_passive():
    trs, _ = load_topology(TOPO_JSON)
    by = {t.name: t for t in trs}
    import json
    with open(TOPO_JSON, encoding="utf-8") as fh:
        raw = json.load(fh)
    return [by[n] for n in GM], raw.get("passive_elements") or []


def _net(n):
    if n == "gnd":
        return "0"
    if n == "Vip":
        return "vip"
    if n == "Vim":
        return "vim"
    if n == "vdd":
        return "vddac"
    return n.lower()


def build(vip_ac, vim_ac, vdd_ac):
    devs, passive = _devs_and_passive()
    L = [".title full-circuit (51 devices + R1/R2/Rz1/Rz2) open-loop crosscheck",
         ".options gmin=1e-18 abstol=1e-18",
         f"Vip vip 0 AC {vip_ac}", f"Vim vim 0 AC {vim_ac}", f"Vdd vddac 0 AC {vdd_ac}"]
    for t in devs:
        gm, gds = GM[t.name], GDS[t.name]
        d, s, g = _net(t.drain), _net(t.source), _net(t.gate)
        if gm:
            L.append(f"G{t.name} {d} {s} {g} {s} {gm:.12g}")
        L.append(f"R{t.name} {d} {s} {1.0/gds:.12g}")
    for p in passive:
        if p.get("kind") != "resistor":
            continue
        r_ohm = p.get("value_ohm") or R_DEFAULT
        a, b = p["terminals"]
        L.append(f"R{p['name']} {_net(a)} {_net(b)} {r_ohm:.12g}")
    L += [".ac dec 1 1 1", ".print ac v(vop) v(vom) v(vbias1)", ".end", ""]
    return "\n".join(L)


def run(vip_ac, vim_ac, vdd_ac):
    d = tempfile.mkdtemp()
    f = os.path.join(d, "s3.cir")
    with open(f, "w") as fh:
        fh.write(build(vip_ac, vim_ac, vdd_ac))
    r = subprocess.run([NG, "-b", f], capture_output=True, text=True, timeout=120)
    txt = r.stdout + r.stderr
    vals, cur = {}, None
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


def main():
    print("=" * 78)
    print("Adm (Vip=0.5, Vim=-0.5, vdd=0)")
    r = run(0.5, -0.5, 0)
    adm = r["v(vop)"] - r["v(vom)"]
    gain_db = 20 * math.log10(abs(adm))
    print(f"  ngspice: Vop={r['v(vop)']:.6g} Vom={r['v(vom)']:.6g} Adm={adm:.6g} gain={gain_db:.4f}dB")
    print(f"  python:  Vop=44641.61972837285 Vom=-44641.61972837283 gain=99.01539878703716dB")

    print()
    print("Acm (Vip=Vim=1, vdd=0)")
    r = run(1, 1, 0)
    acm = (r["v(vop)"] + r["v(vom)"]) / 2
    print(f"  ngspice: Acm = {acm:.6g}")

    print()
    print("Ann (vdd=1, Vip=Vim=0)")
    r = run(0, 0, 1)
    ann = (r["v(vop)"] + r["v(vom)"]) / 2
    print(f"  ngspice: Ann = {ann:.6g}  (python Vop=0.47371222323057693 Vom=0.47371222323989126)")
    print(f"  ngspice: Vbias1(vdd=1) = {r['v(vbias1)']:.6g}  (python: 1.0 -- bias-gen이 vdd를 그대로 따라감)")

    print()
    print("CMRR/PSRR 최종 dB 대조")
    r_dm = run(0.5, -0.5, 0)
    adm2 = r_dm["v(vop)"] - r_dm["v(vom)"]
    r_cm = run(1, 1, 0)
    acm2 = (r_cm["v(vop)"] + r_cm["v(vom)"]) / 2
    r_vdd = run(0, 0, 1)
    ann2 = (r_vdd["v(vop)"] + r_vdd["v(vom)"]) / 2
    cmrr_sp = 20 * math.log10(abs(adm2 / acm2))
    psrr_sp = 20 * math.log10(abs(adm2 / ann2))
    print(f"  ngspice CMRR = {cmrr_sp:.4f}dB   (python: 125.76715845307814)")
    print(f"  ngspice PSRR = {psrr_sp:.4f}dB   (python: 105.50510696686493)")


if __name__ == "__main__":
    main()
