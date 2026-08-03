# -*- coding: utf-8 -*-
"""stage-1 (current-reuse telescopic, open-loop) CMRR -- ngspice AC 교차검증.

2026-08-03. `stage1_cmrr_sympy_derivation.py`가 sympy로 얻은 폐형식을 독립적으로
ngspice로 확인한다. 선례(`cmfb_cmrr_ngspice_crosscheck.py`)와 같은 방법:
실소자/PDK 모델을 쓰지 않고 **이상화 소신호 소자(VCCS + 저항)** 만으로 넷리스트를
조립해 DC 바이어싱 수렴 문제를 완전히 회피하고, 지정한 gm/gds가 그대로 반영되게 한다.

⚠️ 넷리스트는 **손으로 타이핑하지 않는다** -- `stick_diagram.load_topology()`가 돌려준
topology.json의 `.source/.drain/.gate`를 그대로 순회해 자동 생성한다
(프로젝트 원칙: topology.json이 유일한 토폴로지 소스).

소신호 소자 모델: I(drain->source) = gm*v(gate,source) + gds*v(drain,source)
  -> `G<name> <d> <s> <g> <s> gm` + `R<name> <d> <s> 1/gds`   (pmos/nmos 동일)

Adm = |v(Vop1)-v(Vom1)| (vip=+0.5, vim=-0.5),  Acm = |(v(Vop1)+v(Vom1))/2| (vip=vim=1)
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
AC_GROUND = {"vdd", "gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4", "Vcmfb"}
PAIR = {"M1b": "M1a", "M2b": "M2a", "M3b": "M3a", "M4b": "M4a"}

BASE = {"gm_M1a": 119e-6, "gds_M1a": 1 / 600e3, "gm_M2a": 130e-6, "gds_M2a": 1 / 700e3,
        "gm_M4a": 140e-6, "gds_M4a": 1 / 250e3, "gm_M3a": 150e-6, "gds_M3a": 1 / 300e3,
        "gm_M6": 0.0, "gds_M6": 0.5e-6, "gm_M7": 0.0, "gds_M7": 0.4e-6,
        "gm_M5": 0.0, "gds_M5": 1.0e-6}


def _devs():
    trs, _ = load_topology(TOPO_JSON)
    by = {t.name: t for t in trs}
    return [by[n] for n in STAGE1]


def _net(n, mode):
    """topology.json의 노드명 -> spice 노드명. AC ground는 전부 0."""
    if n in AC_GROUND:
        return "0"
    if n == "Vip":
        return "vip"
    if n == "Vim":
        return "vim"
    return n.lower()


def build(p, mode):
    L = [".title stage1 open-loop cmrr", ".options gmin=1e-18 abstol=1e-18"]
    L += (["Vip vip 0 AC 0.5", "Vim vim 0 AC -0.5"] if mode == "dm"
          else ["Vip vip 0 AC 1", "Vim vim 0 AC 1"])
    for t in _devs():
        canon = PAIR.get(t.name, t.name)
        gm, gds = p[f"gm_{canon}"], p[f"gds_{canon}"]
        d, s, g = _net(t.drain, mode), _net(t.source, mode), _net(t.gate, mode)
        if gm:
            L.append(f"G{t.name} {d} {s} {g} {s} {gm:.12g}")
        L.append(f"R{t.name} {d} {s} {1.0 / gds:.12g}")
    L += [".ac dec 1 1 1", ".print ac v(vom1) v(vop1) v(vx) v(vy)", ".end", ""]
    return "\n".join(L)


def run(p, mode):
    d = tempfile.mkdtemp()
    f = os.path.join(d, "s1.cir")
    with open(f, "w") as fh:
        fh.write(build(p, mode))
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


def closed_form(p):
    """2026-08-03 재유도 결과(sizing_recipe._cmrr_telescopic_class_ab와 동일 식)."""
    Kpp = p["gm_M2a"] / (p["gds_M1a"] * p["gds_M2a"])
    Knp = p["gm_M3a"] / (p["gds_M4a"] * p["gds_M3a"])
    adm = (p["gm_M1a"] + p["gm_M4a"]) * (Kpp * Knp / (Kpp + Knp))
    kp, kn = p["gm_M1a"] * Kpp, p["gm_M4a"] * Knp
    rx, ry = 1.0 / (p["gds_M6"] + p["gds_M7"]), 1.0 / p["gds_M5"]
    acm = (rx + ry) * kp * kn / (kn * ry + kp * rx)
    return adm, acm, 20 * math.log10(abs(adm / acm))


def old_closed_form(p):
    """폐기 대상: 캐스코드 부스팅에 **입력쌍** gm을 쓴 옛 식(커밋 b63e394까지)."""
    Kpp = p["gm_M1a"] / (p["gds_M1a"] * p["gds_M2a"])
    Knp = p["gm_M4a"] / (p["gds_M4a"] * p["gds_M3a"])
    adm = (p["gm_M1a"] + p["gm_M4a"]) * (Kpp * Knp / (Kpp + Knp))
    kp, kn = p["gm_M1a"] * Kpp, p["gm_M4a"] * Knp
    rx, ry = 1.0 / (p["gds_M6"] + p["gds_M7"]), 1.0 / p["gds_M5"]
    acm = (rx + ry) * kp * kn / (kn * ry + kp * rx)
    return adm, acm, 20 * math.log10(abs(adm / acm))


def report(p, tag):
    dm, cm = run(p, "dm"), run(p, "cm")
    adm = abs(dm["v(vop1)"] - dm["v(vom1)"])
    acm = abs((cm["v(vop1)"] + cm["v(vom1)"]) / 2.0)
    db = 20 * math.log10(adm / acm)
    _, _, db_new = closed_form(p)
    _, _, db_old = old_closed_form(p)
    print(f"[{tag}] SPICE Adm={adm:9.4g} Acm={acm:9.4g} CMRR={db:8.4f}dB | "
          f"new_cf={db_new:8.4f}({db_new - db:+.4f})  old_cf={db_old:8.4f}({db_old - db:+.4f})")
    return db, db_new, db_old


if __name__ == "__main__":
    print("== 앵커 1: Rx=Ry=1e6, 모든 gm=119uS (기존 self-test 앵커와 동일 조건) ==")
    a1 = dict(BASE)
    for k in ("gm_M2a", "gm_M4a", "gm_M3a"):
        a1[k] = 119e-6
    a1["gds_M1a"] = a1["gds_M2a"] = 1 / 600e3
    a1["gds_M4a"] = a1["gds_M3a"] = 1 / 250e3
    a1["gds_M6"] = a1["gds_M7"] = 0.5e-6
    a1["gds_M5"] = 1.0e-6
    report(a1, "anchor1")

    print("== 앵커 2: 같은 조건에서 Rx=1e8 (비대칭 tail) ==")
    a2 = dict(a1)
    a2["gds_M6"] = a2["gds_M7"] = 0.5e-8
    report(a2, "anchor2")

    print("== 앵커 3(신규): gm이 서로 다른 경우 -- 캐스코드 gm vs 입력 gm 차이가 드러난다 ==")
    report(dict(BASE), "anchor3")

    print("== 랜덤 스윕(각 파라미터 x[1/4, 4]) ==")
    random.seed(3)
    wn = wo = 0.0
    for i in range(20):
        p = dict(BASE)
        for k in p:
            if p[k]:
                p[k] *= math.exp(random.uniform(-math.log(4), math.log(4)))
        db, dn, do = report(p, f"rand{i}")
        wn, wo = max(wn, abs(dn - db)), max(wo, abs(do - db))
    print(f"WORST |new_cf - SPICE| = {wn:.4f} dB")
    print(f"WORST |old_cf - SPICE| = {wo:.4f} dB")
