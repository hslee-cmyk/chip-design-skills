# -*- coding: utf-8 -*-
"""세션21 -- M10/M19 로딩을 "기존 캐스코드 R_out과 병렬 컨덕턴스로 정확히 합산"하는 폐형식이
STEP5(stage2_battery_psrr_sympy_derivation.py)의 exact Adm_full/Ann_full과 대수적으로 같은지
검증한다. ⚠️ 첫 시도(sp.simplify/sp.factor로 기호적 항등식 증명)는 오래 걸려(6분+, CPU바운드,
메모리는 안 커짐 -- 이전 두 번의 "메모리 폭발"과는 다른 종류의 정체) 죽이고 **수치 대조**로
전환(랜덤 스윕 diff -> 0 근접이면 사실상 항등식 확인, 이 프로젝트의 다른 폐형식들도 전부 이
방식으로 검증돼 왔다 -- 손타이핑/상상 아님, 실측 확인 원칙 그대로)."""
import math
import os
import random
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


def gm(n):
    return sp.Symbol(f"gm_{n}", positive=True)


def gds(n):
    return sp.Symbol(f"gds_{n}", positive=True)


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


BASE = {"gm_M1a": 119e-6, "gds_M1a": 1 / 600e3, "gm_M2a": 130e-6, "gds_M2a": 1 / 700e3,
        "gm_M4a": 140e-6, "gds_M4a": 1 / 250e3, "gm_M3a": 150e-6, "gds_M3a": 1 / 300e3,
        "gm_M6": 60e-6, "gds_M6": 0.5e-6, "gm_M7": 25e-6, "gds_M7": 0.4e-6,
        "gm_M5": 0.0, "gds_M5": 1.0e-6, "gm_M8": 40e-6, "gds_M10": 0.6e-6}


def rand_sweep(f_exact, f_conj, syms_exact, syms_conj, n=20, seed=21, tag=""):
    random.seed(seed)
    worst = 0.0
    for i in range(n):
        p = dict(BASE)
        for k in p:
            if p[k]:
                p[k] *= math.exp(random.uniform(-math.log(4), math.log(4)))
        x = f_exact(*[p[str(s)] for s in syms_exact])
        c = f_conj(*[p[str(s)] for s in syms_conj])
        rel = abs(c - x) / (abs(x) + 1e-30)
        worst = max(worst, rel)
        if i < 5:
            print(f"    [{tag}] rand{i}: exact={x:.6g}  conj={c:.6g}  rel_err={rel:.3e}")
    print(f"  [{tag}] WORST relative error over {n}점 = {worst:.3e}"
          f"  ({'가설 확인(사실상 0)' if worst < 1e-6 else '가설 불일치'})")
    return worst


def main():
    print("=" * 78)
    print("A) M10만 부하로 추가(주입 없음) -- Adm_new, Acm_new exact vs 가설")
    print("=" * 78)
    vop1, vom1, vip, vim, vdd, sym = solve_stage1_plus_M10(inject_M8=False)
    dm = {vip: sp.Rational(1, 2), vim: sp.Rational(-1, 2), vdd: 0}
    cm = {vip: 1, vim: 1, vdd: 0}
    Adm_new = (vop1 - vom1).subs(dm)
    Acm_new = ((vop1 + vom1) / 2).subs(cm)

    Kp_prime = gm("M2a") / (gds("M1a") * gds("M2a"))
    Kn_prime = gm("M3a") / (gds("M4a") * gds("M3a"))
    gdsM10 = sp.Symbol("gds_M10", positive=True)
    R_out_old = Kp_prime * Kn_prime / (Kp_prime + Kn_prime)
    R_out_new = 1 / (1 / R_out_old + gdsM10)
    Adm_conj = (gm("M1a") + gm("M4a")) * R_out_new

    Kp = gm("M1a") * Kp_prime
    Kn = gm("M4a") * Kn_prime
    Rx = 1 / (gds("M6") + gds("M7"))
    Ry = 1 / gds("M5")
    Acm_open = (Rx + Ry) * Kn * Kp / (Kn * Ry + Kp * Rx)
    Gm_cm = Acm_open / R_out_old
    Acm_conj = Gm_cm * R_out_new

    syms_exact_adm = sorted(Adm_new.free_symbols, key=str)
    syms_conj_adm = sorted(Adm_conj.free_symbols, key=str)
    f_adm_x = sp.lambdify(syms_exact_adm, Adm_new, "math")
    f_adm_c = sp.lambdify(syms_conj_adm, Adm_conj, "math")
    rand_sweep(f_adm_x, f_adm_c, syms_exact_adm, syms_conj_adm, tag="Adm")

    syms_exact_acm = sorted(Acm_new.free_symbols, key=str)
    syms_conj_acm = sorted(Acm_conj.free_symbols, key=str)
    f_acm_x = sp.lambdify(syms_exact_acm, Acm_new, "math")
    f_acm_c = sp.lambdify(syms_conj_acm, Acm_conj, "math")
    rand_sweep(f_acm_x, f_acm_c, syms_exact_acm, syms_conj_acm, tag="Acm")

    print()
    print("=" * 78)
    print("B) M10 부하 + M8 주입(-gm8*vdd) 둘 다 -- Ann_new exact vs 가설")
    print("=" * 78)
    vop1b, vom1b, vipb, vimb, vddb, symb = solve_stage1_plus_M10(inject_M8=True)
    ripple = {vipb: 0, vimb: 0, vddb: 1}
    Ann_new = ((vop1b + vom1b) / 2).subs(ripple)

    gm8 = sp.Symbol("gm_M8", positive=True)
    gm6, gm7 = sp.Symbol("gm_M6", positive=True), sp.Symbol("gm_M7", positive=True)
    Ann_open_old = (gm6 + gm7) * (Rx * Ry / (Rx + Ry)) * Acm_open
    Gm_ann = Ann_open_old / R_out_old
    Ann_conj = Gm_ann * R_out_new + gm8 * R_out_new

    syms_exact_ann = sorted(Ann_new.free_symbols, key=str)
    syms_conj_ann = sorted(Ann_conj.free_symbols, key=str)
    f_ann_x = sp.lambdify(syms_exact_ann, Ann_new, "math")
    f_ann_c = sp.lambdify(syms_conj_ann, Ann_conj, "math")
    rand_sweep(f_ann_x, f_ann_c, syms_exact_ann, syms_conj_ann, tag="Ann")


if __name__ == "__main__":
    main()
