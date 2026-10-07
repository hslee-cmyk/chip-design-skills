# -*- coding: utf-8 -*-
"""세션21 -- 병렬 컨덕턴스 가설(Adm은 근접, Acm/Ann은 완전히 틀림, 부호까지 다름 -- 수치로
확인)이 깨졌으므로, 손유도 지름길을 더 시도하지 않고 solve_stage1_plus_M10()의 **정확해**를
그대로(추가 근사 없이) 꺼내 크기를 확인한다. 관리 가능한 크기면 그대로 폐형식으로 채택."""
import os
import sys

import sympy as sp

_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.abspath(os.path.join(
    _HERE, "..", "..", "..", "skills", "analog-gmid-design", "assets"))
sys.path.insert(0, _ASSETS)
from stick_diagram import load_topology  # noqa: E402

TOPO_JSON = os.path.join(_ASSETS, "library", "current_reuse_telescopic_ota.topology.json")
STAGE1 = ["M6", "M7", "M1a", "M1b", "M2a", "M2b", "M3a", "M3b", "M4a", "M4b", "M5"]
AC_GROUND = {"gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4", "Vcmfb"}
PAIR = {"M1b": "M1a", "M2b": "M2a", "M3b": "M3a", "M4b": "M4a"}


def solve_stage1_plus_M10(inject_M8=True):
    trs, _ = load_topology(TOPO_JSON)
    by_name = {t.name: t for t in trs}
    stage1_devs = [by_name[n] for n in STAGE1]
    sym = {}
    def g(name, key):
        canon = PAIR.get(name, name)
        k = (canon, key)
        if k not in sym:
            sym[k] = sp.Symbol(f"{key}_{canon}", positive=True)
        return sym[k]
    nodes = []
    for t in stage1_devs:
        for n in (t.source, t.drain, t.gate):
            if n not in AC_GROUND and n not in ("Vip", "Vim", "vdd") and n not in nodes:
                nodes.append(n)
    v = {n: sp.Symbol(f"v_{n}") for n in nodes}
    vip, vim, vdd = sp.symbols("vip vim vdd")
    def pot(n):
        if n in AC_GROUND:
            return sp.Integer(0)
        if n == "Vip":
            return vip
        if n == "Vim":
            return vim
        if n == "vdd":
            return vdd
        return v[n]
    kcl = {n: sp.Integer(0) for n in nodes}
    for t in stage1_devs:
        vd, vs, vgate = pot(t.drain), pot(t.source), pot(t.gate)
        i_ds = g(t.name, "gm") * (vgate - vs) + g(t.name, "gds") * (vd - vs)
        if t.drain in kcl:
            kcl[t.drain] += i_ds
        if t.source in kcl:
            kcl[t.source] -= i_ds
    gdsM10 = sp.Symbol("gds_M10", positive=True)
    gmM8 = sp.Symbol("gm_M8", positive=True)
    kcl["Vop1"] += gdsM10 * v["Vop1"]
    kcl["Vom1"] += gdsM10 * v["Vom1"]
    if inject_M8:
        kcl["Vop1"] += -gmM8 * vdd
        kcl["Vom1"] += -gmM8 * vdd
    sol = sp.solve([sp.Eq(kcl[n], 0) for n in nodes], [v[n] for n in nodes], dict=True)
    assert len(sol) == 1
    sol = sol[0]
    return sol[v["Vop1"]], sol[v["Vom1"]], vip, vim, vdd, sym


def main():
    vop1, vom1, vip, vim, vdd, sym = solve_stage1_plus_M10(inject_M8=False)
    dm = {vip: sp.Rational(1, 2), vim: sp.Rational(-1, 2), vdd: 0}
    cm = {vip: 1, vim: 1, vdd: 0}
    Adm_new = sp.together((vop1 - vom1).subs(dm))
    Acm_new = sp.together(((vop1 + vom1) / 2).subs(cm))
    Adm_n, Adm_d = sp.fraction(Adm_new)
    Acm_n, Acm_d = sp.fraction(Acm_new)
    print(f"Adm_new: numer {sp.count_ops(Adm_n)}항 / denom {sp.count_ops(Adm_d)}항")
    print(f"Acm_new: numer {sp.count_ops(Acm_n)}항 / denom {sp.count_ops(Acm_d)}항")

    vop1b, vom1b, vipb, vimb, vddb, symb = solve_stage1_plus_M10(inject_M8=True)
    ripple = {vipb: 0, vimb: 0, vddb: 1}
    Ann_new = sp.together(((vop1b + vom1b) / 2).subs(ripple))
    Ann_n, Ann_d = sp.fraction(Ann_new)
    print(f"Ann_new: numer {sp.count_ops(Ann_n)}항 / denom {sp.count_ops(Ann_d)}항")

    print()
    print("Adm_new =", Adm_new)
    print()
    print("Acm_new =", Acm_new)
    print()
    print("Ann_new =", Ann_new)


if __name__ == "__main__":
    main()
