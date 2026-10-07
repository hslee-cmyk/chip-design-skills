# -*- coding: utf-8 -*-
"""stage-1 (current-reuse telescopic, open-loop) PSRR -- ngspice AC 교차검증.

2026-08-07(세션20 후속). `stage1_psrr_sympy_derivation.py`가 sympy로 얻은 폐형식
(Ann_open = (gm(M6)+gm(M7))*(Rx||Ry)*Acm_open, 즉 PSRR_open = CMRR_open -
20*log10((gm6+gm7)*(Rx||Ry)))을 `stage1_cmrr_ngspice_crosscheck.py`와 동일 방법
(이상화 소신호 VCCS+저항, 손타이핑 넷리스트 없음)으로 독립 검증한다.

CMRR 스크립트와의 유일한 차이: `mode="psrr"`에서는 Vip=Vim=0(신호 AC ground)이고
**vdd를 AC ground에서 빼서 독립 전압원(AC 1V)으로 둔다** -- 순수 전원->출력 전달만 본다.
"""
import math
import os
import random
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
# psrr 모드: gnd/바이어스/Vcmfb는 여전히 AC ground(open-loop 가정). vdd는 여기 없음 --
# 독립 전압원으로 별도 취급(cmrr 스크립트는 반대로 vdd가 AC ground였다).
AC_GROUND_PSRR = {"gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4", "Vcmfb"}
PAIR = {"M1b": "M1a", "M2b": "M2a", "M3b": "M3a", "M4b": "M4a"}

BASE = {"gm_M1a": 119e-6, "gds_M1a": 1 / 600e3, "gm_M2a": 130e-6, "gds_M2a": 1 / 700e3,
        "gm_M4a": 140e-6, "gds_M4a": 1 / 250e3, "gm_M3a": 150e-6, "gds_M3a": 1 / 300e3,
        "gm_M6": 60e-6, "gds_M6": 0.5e-6, "gm_M7": 25e-6, "gds_M7": 0.4e-6,
        "gm_M5": 0.0, "gds_M5": 1.0e-6}


def _devs():
    trs, _ = load_topology(TOPO_JSON)
    by = {t.name: t for t in trs}
    return [by[n] for n in STAGE1]


def _net(n):
    if n in AC_GROUND_PSRR:
        return "0"
    if n == "Vip":
        return "vip"
    if n == "Vim":
        return "vim"
    if n == "vdd":
        return "vddac"
    return n.lower()


def build(p):
    L = [".title stage1 open-loop psrr", ".options gmin=1e-18 abstol=1e-18",
         "Vip vip 0 AC 0", "Vim vim 0 AC 0", "Vdd vddac 0 AC 1"]
    for t in _devs():
        canon = PAIR.get(t.name, t.name)
        gm, gds = p[f"gm_{canon}"], p[f"gds_{canon}"]
        d, s, g = _net(t.drain), _net(t.source), _net(t.gate)
        if gm:
            L.append(f"G{t.name} {d} {s} {g} {s} {gm:.12g}")
        L.append(f"R{t.name} {d} {s} {1.0 / gds:.12g}")
    L += [".ac dec 1 1 1", ".print ac v(vom1) v(vop1) v(vx) v(vy)", ".end", ""]
    return "\n".join(L)


def run(p):
    d = tempfile.mkdtemp()
    f = os.path.join(d, "s1psrr.cir")
    with open(f, "w") as fh:
        fh.write(build(p))
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


def adm_closed_form(p):
    """Adm은 CMRR 유도와 완전히 동일 -- 재도출 없이 그대로 재사용."""
    Kpp = p["gm_M2a"] / (p["gds_M1a"] * p["gds_M2a"])
    Knp = p["gm_M3a"] / (p["gds_M4a"] * p["gds_M3a"])
    return (p["gm_M1a"] + p["gm_M4a"]) * (Kpp * Knp / (Kpp + Knp))


def acm_closed_form(p):
    Kpp = p["gm_M2a"] / (p["gds_M1a"] * p["gds_M2a"])
    Knp = p["gm_M3a"] / (p["gds_M4a"] * p["gds_M3a"])
    kp, kn = p["gm_M1a"] * Kpp, p["gm_M4a"] * Knp
    rx, ry = 1.0 / (p["gds_M6"] + p["gds_M7"]), 1.0 / p["gds_M5"]
    return (rx + ry) * kp * kn / (kn * ry + kp * rx)


def psrr_closed_form(p):
    """2026-08-07 유도(stage1_psrr_sympy_derivation.py) -- Ann_open = (gm6+gm7)*(Rx||Ry)*Acm_open."""
    rx, ry = 1.0 / (p["gds_M6"] + p["gds_M7"]), 1.0 / p["gds_M5"]
    acm = acm_closed_form(p)
    adm = adm_closed_form(p)
    ann = (p["gm_M6"] + p["gm_M7"]) * (rx * ry / (rx + ry)) * acm
    return adm, ann, 20 * math.log10(abs(adm / ann))


def report(p, tag):
    r = run(p)
    adm_sp = abs(0.0)  # DM 응답은 이 psrr 모드에선 안 나온다(vip=vim=0) -- Adm은 폐형식만 대조
    ann_sp = abs((r["v(vop1)"] + r["v(vom1)"]) / 2.0)
    adm_cf, ann_cf, db_cf = psrr_closed_form(p)
    db_sp = 20 * math.log10(abs(adm_cf / ann_sp))   # Adm은 CMRR 스크립트에서 이미 SPICE 검증됨
    print(f"[{tag}] SPICE Ann={ann_sp:10.4g}  cf_Ann={ann_cf:10.4g} "
          f"(ratio={ann_sp/ann_cf:.4f})  PSRR(SPICE-Ann,cf-Adm)={db_sp:8.4f}dB  "
          f"cf={db_cf:8.4f}dB  (err={db_cf - db_sp:+.4f}dB)")
    return db_sp, db_cf


if __name__ == "__main__":
    print("== 앵커 1 (CMRR 스크립트 anchor1과 동일 사이징) ==")
    a1 = dict(BASE)
    for k in ("gm_M2a", "gm_M4a", "gm_M3a"):
        a1[k] = 119e-6
    a1["gds_M1a"] = a1["gds_M2a"] = 1 / 600e3
    a1["gds_M4a"] = a1["gds_M3a"] = 1 / 250e3
    a1["gds_M6"] = a1["gds_M7"] = 0.5e-6
    a1["gds_M5"] = 1.0e-6
    report(a1, "anchor1")

    print("== 앵커 2 (Rx 비대칭, CMRR anchor2와 동일) ==")
    a2 = dict(a1)
    a2["gds_M6"] = a2["gds_M7"] = 0.5e-8
    report(a2, "anchor2")

    print("== 랜덤 스윕(각 파라미터 x[1/4, 4]) ==")
    random.seed(3)
    worst = 0.0
    for i in range(20):
        p = dict(BASE)
        for k in p:
            if p[k]:
                p[k] *= math.exp(random.uniform(-math.log(4), math.log(4)))
        db_sp, db_cf = report(p, f"rand{i}")
        worst = max(worst, abs(db_cf - db_sp))
    print(f"WORST |cf - SPICE| = {worst:.4f} dB")
