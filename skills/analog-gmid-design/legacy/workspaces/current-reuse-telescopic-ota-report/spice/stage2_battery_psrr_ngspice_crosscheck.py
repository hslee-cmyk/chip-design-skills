# -*- coding: utf-8 -*-
"""세션21 -- 31소자(1단11 + 양쪽 Monticelli battery 10+10) 소신호망의 독립 ngspice AC
교차검증. `sizing_recipe.py`의 `_telescopic_class_ab_open_loop_gains()`(순수 Python
Gaussian elimination)와는 완전히 다른 솔버(ngspice)로 같은 이상화 회로(VCCS+R, 실소자
없이 지정 gm/gds만)를 풀어 Adm_open/Acm_open/Ann_open/H를 대조한다 -- "내가 짠 solver
자체가 맞는가"를 검증하는 게 목적이라, connectivity는 손타이핑하지 않고 `load_topology()`로
topology.json에서 그대로 읽는다(stage1_cmrr_ngspice_crosscheck.py와 동일 방법론)."""
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

STAGE1 = ["M6", "M7", "M1a", "M1b", "M2a", "M2b", "M3a", "M3b", "M4a", "M4b", "M5"]
BATTERY_A = ["M8", "M9a", "M9b", "M11a", "M11b", "M12", "M10", "M13", "M14a", "M14b"]
BATTERY_B = ["M17", "M18a", "M18b", "M20a", "M20b", "M21", "M19", "M22", "M23a", "M24b"]
ALL_DEVS = STAGE1 + BATTERY_A + BATTERY_B
AC_GROUND = {"gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4"}

# self-test(sizing_recipe.py, 세션21 신규 CMRR/PSRR 앵커)와 완전히 동일한 파라미터.
GM = {"M1a": 119e-6, "M1b": 119e-6, "M2a": 130e-6, "M2b": 130e-6,
      "M4a": 140e-6, "M4b": 140e-6, "M3a": 150e-6, "M3b": 150e-6,
      "M6": 0.0, "M7": 90e-6, "M5": 0.0,
      "M8": 40e-6, "M17": 40e-6, "M9a": 50e-6, "M9b": 50e-6, "M18a": 50e-6, "M18b": 50e-6,
      "M11a": 30e-6, "M11b": 30e-6, "M20a": 30e-6, "M20b": 30e-6,
      "M12": 0.0, "M21": 0.0, "M10": 0.0, "M19": 0.0,
      "M13": 40e-6, "M22": 40e-6, "M14a": 30e-6, "M14b": 30e-6, "M23a": 30e-6, "M24b": 30e-6}
GDS = {"M1a": 1 / 600e3, "M1b": 1 / 600e3, "M2a": 1 / 700e3, "M2b": 1 / 700e3,
       "M4a": 1 / 250e3, "M4b": 1 / 250e3, "M3a": 1 / 300e3, "M3b": 1 / 300e3,
       "M6": 0.5e-6, "M7": 0.4e-6, "M5": 1.0e-6,
       "M8": 0.3e-6, "M17": 0.3e-6, "M9a": 0.4e-6, "M9b": 0.4e-6, "M18a": 0.4e-6, "M18b": 0.4e-6,
       "M11a": 0.5e-6, "M11b": 0.5e-6, "M20a": 0.5e-6, "M20b": 0.5e-6,
       "M12": 0.6e-6, "M21": 0.6e-6, "M10": 0.6e-6, "M19": 0.6e-6,
       "M13": 0.3e-6, "M22": 0.3e-6, "M14a": 0.5e-6, "M14b": 0.5e-6, "M23a": 0.5e-6, "M24b": 0.5e-6}


def _devs():
    trs, _ = load_topology(TOPO_JSON)
    by = {t.name: t for t in trs}
    return [by[n] for n in ALL_DEVS]


def _net(n):
    if n in AC_GROUND or n == "gnd":
        return "0"
    if n == "Vip":
        return "vip"
    if n == "Vim":
        return "vim"
    if n == "vdd":
        return "vddac"
    if n == "Vcmfb":
        return "vcmfbac"
    return n.lower()


def build(vip_ac, vim_ac, vdd_ac, vcmfb_ac):
    L = [".title telescopic_class_ab 31-device open-loop crosscheck",
         ".options gmin=1e-18 abstol=1e-18",
         f"Vip vip 0 AC {vip_ac}", f"Vim vim 0 AC {vim_ac}",
         f"Vdd vddac 0 AC {vdd_ac}", f"Vcmfb vcmfbac 0 AC {vcmfb_ac}"]
    for t in _devs():
        gm, gds = GM[t.name], GDS[t.name]
        d, s, g = _net(t.drain), _net(t.source), _net(t.gate)
        if gm:
            L.append(f"G{t.name} {d} {s} {g} {s} {gm:.12g}")
        L.append(f"R{t.name} {d} {s} {1.0 / gds:.12g}")
    L += [".ac dec 1 1 1", ".print ac v(vop1) v(vom1)", ".end", ""]
    return "\n".join(L)


def run(vip_ac, vim_ac, vdd_ac, vcmfb_ac):
    d = tempfile.mkdtemp()
    f = os.path.join(d, "s2.cir")
    with open(f, "w") as fh:
        fh.write(build(vip_ac, vim_ac, vdd_ac, vcmfb_ac))
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
    print("Adm_open (vip=0.5, vim=-0.5, vdd=0, vcmfb=0)")
    print("=" * 78)
    r = run(0.5, -0.5, 0, 0)
    adm_sp = r["v(vop1)"] - r["v(vom1)"]
    print(f"  ngspice: Adm_open = {adm_sp:.6g}")
    print(f"  python(sizing_recipe._telescopic_class_ab_open_loop_gains): 253.729 (self-test 참고값)")
    print(f"  rel err = {abs(adm_sp/253.72885995944682 - 1):.4%}")

    print()
    print("Acm_open (vip=vim=1, vdd=0, vcmfb=0)")
    r = run(1, 1, 0, 0)
    acm_sp = (r["v(vop1)"] + r["v(vom1)"]) / 2
    print(f"  ngspice: Acm_open = {acm_sp:.6g}")
    print(f"  python: -1.031040580245931")
    print(f"  rel err = {abs(acm_sp/-1.031040580245931 - 1):.4%}")

    print()
    print("Ann_open (vip=vim=0, vdd=1, vcmfb=0)")
    r = run(0, 0, 1, 0)
    ann_sp = (r["v(vop1)"] + r["v(vom1)"]) / 2
    print(f"  ngspice: Ann_open = {ann_sp:.6g}")
    print(f"  python: 95.50419613227969")
    print(f"  rel err = {abs(ann_sp/95.50419613227969 - 1):.4%}")

    print()
    print("H (vip=vim=0, vdd=0, vcmfb=1)")
    r = run(0, 0, 0, 1)
    h_sp = (r["v(vop1)"] + r["v(vom1)"]) / 2
    print(f"  ngspice: H = {h_sp:.6g}")
    print(f"  python: -49.88910382619901")
    print(f"  rel err = {abs(h_sp/-49.88910382619901 - 1):.4%}")


if __name__ == "__main__":
    main()
