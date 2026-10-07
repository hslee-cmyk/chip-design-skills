# -*- coding: utf-8 -*-
"""stage-1 + Class-AB 출력전류원(battery) VDD 주입 경로까지 포함한 PSRR+ 폐형식 -- 세션21,
`.ai/context.md` 다음 세션 작업순서 1번(PSRR (C)단계). `stage1_psrr_sympy_derivation.py`
(세션20)의 정직한 한계 "2단 Class-AB 출력전류원(M8/M13/M17/M22, source=vdd)의 자체 VDD 주입
경로는 미포함"을 해소한다.

⚠️ **두 번 폐기된 접근**(둘 다 실측으로 확인 후 폐기, 상상 아님):
  (1) 31소자/18노드 통짜 MNA를 sympy linsolve로 한 번에 풀기 -- 수 분간 2.8GB+ 메모리,
      진행 없음(fraction-free Gaussian elimination의 중간식 크기 폭발).
  (2) battery-A 5노드만 먼저 정확해로 풀어 8노드에 얹는 "블록소거"도 -- 5노드 **정확해** 자체가
      이미 200항 넘는 단일 유리식이 됐고, 그걸 8노드 stage-1 KCL에 대입한 뒤 다시 정확해로
      풀려 하니 똑같이 3.3GB+로 폭주.
  **원인**: 이 프로젝트의 모든 폐형식은 애초에 gm·ro≫1 **leading order**만 필요한데, 위 두
  시도는 정확해부터 구하고 나중에 극한을 취하려 했다 -- leading order를 처음부터(각 서브
  회로 단계에서) 적용하면 매 단계가 작은(2~3노드) 시스템으로 남는다는 게 이번 세션의 핵심
  교훈(다음에 회로가 더 커지면 이 방식을 기본으로 삼을 것).

**세 번째 접근(채택, 아래 구현) -- 단계별 leading order**:
  1. M11a/M11b/M12(N11b 체인)과 M13/M14a/M14b(N14a14b 체인)는 Vg15/Vop1과 **완전히
     분리된 독립 서브회로**(넷리스트로 확인 -- 서로 다른 노드에만 닿는다)라 각각 2노드
     짜리 leading order만 따로 풀면 된다(사람 손 유도 + sympy로 재확인, 상상 아님).
  2. 그 결과(vN11b, vN14a14b -- 둘 다 vdd의 leading-order 선형함수)를 Vg15 KCL(M8/M9a/M9b,
     역시 leading order로 gds8/gds9a/gds9b는 O(eps)라 버림)에 대입해 vg15(vdd, vop1)를 얻는다.
  3. M9a/M9b가 Vop1에 주입하는 leading-order 전류를 vg15 결과로 계산 -> Vop1 KCL에 더한다.
  4. Vom1측(M17/M18a/M18b/M20a/M20b/M21/M19/M22/M23a/M24b)은 matching_pairs로 이미 확정된
     거울대칭이므로 같은 결과를 Vop1<->Vom1 치환만으로 재사용(재유도 없음).
  5. stage-1 8노드(세션20과 동일 크기)에 위 추가 전류를 얹어 Adm_full/Ann_full을 얻는다 --
     이 STEP은 세션20이 이미 빠르게 푼 크기 그대로라 다시 느려지지 않는다.
  6. **최종 확인은 ngspice AC**(이 프로젝트 전체의 검증 원칙 그대로) -- 이상화 VCCS+R
     넷리스트로 31소자 전체를 수치로 풀어(sympy 없이, 그래서 폭발 없음) leading-order
     폐형식과 대조한다(`stage2_battery_psrr_ngspice_crosscheck.py`, 별도 파일).
"""
import math
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

gm = lambda n: sp.Symbol(f"gm_{n}", positive=True)
gd = lambda n: sp.Symbol(f"gdsh_{n}", positive=True)   # 이미 leading-order 기호(eps 제거된 물리 gds)


def check_connectivity():
    trs, _ = load_topology(TOPO_JSON)
    d = {t.name: t for t in trs}
    for n in ["M11a", "M11b", "M12", "M13", "M14a", "M14b", "M8", "M9a", "M9b", "M10"]:
        t = d[n]
        assert t.source and t.drain and t.gate
    # 두 bias 체인이 Vg15/Vop1과 노드를 공유하지 않는 독립 서브회로임을 직접 확인(가정 아님).
    for n in ("M11a", "M11b", "M12", "M13", "M14a", "M14b"):
        t = d[n]
        assert "Vg15" not in (t.source, t.drain, t.gate), f"{n} touches Vg15 -- 가정 위반"
        assert "Vop1" not in (t.source, t.drain, t.gate), f"{n} touches Vop1 -- 가정 위반"
    assert d["M13"].drain == "N14a14b"
    print("STEP 0 -- connectivity 재확인: N11b/N14a14b 체인은 Vg15/Vop1과 노드를 공유하지 않음 (OK)")


def step1_n11b_chain():
    """M11a(diode,S=vdd)-M11b(diode)-M12(sink,S=gnd,G=Vbias4=0) -> N11b.
    2노드(N11a11b,N11b) leading order 선형계 -- diode gm 유지, 전부 gds는 O(eps)라 버림
    (M12만 예외: N11b의 유일한 대지 경로라 gds12를 남겨야 유한해가 나온다)."""
    vN11a11b, vN11b, vdd = sp.symbols("vN11a11b vN11b vdd")
    # M11a: S=vdd,D=G=N11a11b -> i = gm11a*(vN11a11b-vdd) [diode, gds 버림]
    i11a = gm("M11a") * (vN11a11b - vdd)
    # M11b: S=N11a11b,D=G=N11b -> i = gm11b*(vN11b-vN11a11b)
    i11b = gm("M11b") * (vN11b - vN11a11b)
    # M12: S=gnd,D=N11b,G=0(Vbias4) -> i = gds12*vN11b (gm12항은 vg-vs=0-0=0)
    i12 = gd("M12") * vN11b
    kcl_a = i11a - i11b     # N11a11b: M11a drain(+), M11b source(-)
    kcl_b = i11b + i12      # N11b: M11b drain(+), M12 drain(+)
    sol = sp.solve([sp.Eq(kcl_a, 0), sp.Eq(kcl_b, 0)], [vN11a11b, vN11b], dict=True)[0]
    vN11b_expr = sp.simplify(sol[vN11b])
    print(f"  vN11b(leading, gds12 유지) = {vN11b_expr}")
    # gds12 -> 0 극한(진짜 leading order, M12조차 완전 이상적이면 vN11b=vdd 정확히)
    vN11b_lead0 = sp.limit(vN11b_expr, gd("M12"), 0)
    print(f"  gds12->0 극한: vN11b = {vN11b_lead0}   (기대: vdd, 손유도와 일치 확인용)")
    return vN11b_expr, vdd


def step2_n14a14b_chain():
    """M13(S=vdd,D=N14a14b,G=Vbias1=0, 전류원)-M14a(diode)-M14b(diode,S=gnd) -> N14a14b.
    2노드(N14a14b,N14a_14b), M13은 gds13도 O(eps)라 버리고 gm13 주입만 남긴다(직접 손유도와
    동일 -- sympy로 재확인)."""
    vN14a14b, vN14a_14b, vdd = sp.symbols("vN14a14b vN14a_14b vdd")
    i13 = gm("M13") * (0 - vdd)                                  # 전류원 주입만(gds13 버림)
    i14a = gm("M14a") * (vN14a14b - vN14a_14b)                   # diode
    i14b = gm("M14b") * (vN14a_14b - 0)                          # diode
    kcl_top = i13 + i14a           # N14a14b: M13 drain(+), M14a drain(+)
    kcl_mid = -i14a + i14b         # N14a_14b: M14a source(-), M14b drain(+)
    sol = sp.solve([sp.Eq(kcl_top, 0), sp.Eq(kcl_mid, 0)], [vN14a14b, vN14a_14b], dict=True)[0]
    vN14a14b_expr = sp.simplify(sol[vN14a14b])
    print(f"  vN14a14b(leading) = {vN14a14b_expr}")
    return vN14a14b_expr, vdd


def step3_vg15(vN11b_expr, vN14a14b_expr, vdd):
    """Vg15 KCL(M8 주입 + M9a/M9b, 전부 leading order: gds8/gds9a/gds9b는 O(eps)라 버림) --
    vop1은 외부 심볼로 남겨(Vop1은 stage-1 8노드에서 함께 풀린다)."""
    vg15, vop1 = sp.symbols("vg15 vop1")
    i8 = gm("M8") * (0 - vdd)                                     # 전류원 주입만
    i9a = gm("M9a") * (vN11b_expr - vg15)                         # M9a: S=Vg15,D=Vop1,G=N11b
    i9b = gm("M9b") * (vN14a14b_expr - vop1)                      # M9b: S=Vop1,D=Vg15,G=N14a14b
    kcl_vg15 = i8 - i9a + i9b     # M8 drain(+), M9a source(-), M9b drain(+)
    vg15_expr = sp.solve(sp.Eq(kcl_vg15, 0), vg15)[0]
    vg15_expr = sp.simplify(vg15_expr)
    print(f"  vg15(leading, vop1 외부심볼) = {vg15_expr}")
    return vg15_expr, vop1, vdd, i9a.subs(vg15, vg15_expr), i9b


def main():
    check_connectivity()
    print()
    print("=" * 78)
    print("STEP 1 -- N11b replica-bias 체인(M11a/M11b/M12) leading order")
    print("=" * 78)
    vN11b_expr, vdd = step1_n11b_chain()

    print()
    print("=" * 78)
    print("STEP 2 -- N14a14b 체인(M13/M14a/M14b) leading order")
    print("=" * 78)
    vN14a14b_expr, _ = step2_n14a14b_chain()

    print()
    print("=" * 78)
    print("STEP 3 -- Vg15 KCL(M8/M9a/M9b), Vop1은 외부 심볼")
    print("=" * 78)
    vg15, vop1_sym = sp.symbols("vg15 vop1")
    i8 = gm("M8") * (0 - vdd)
    i9a_expr = gm("M9a") * (vN11b_expr - vg15)
    i9b_expr = gm("M9b") * (vN14a14b_expr - vop1_sym)
    kcl_vg15 = sp.Eq(i8 - i9a_expr + i9b_expr, 0)
    vg15_sol = sp.solve(kcl_vg15, vg15)[0]
    vg15_sol = sp.simplify(vg15_sol)
    print(f"  vg15 = {vg15_sol}")

    print()
    print("=" * 78)
    print("STEP 4 -- Vop1에 주입되는 battery-A net 전류(M9a+M9b+M10, leading order)")
    print("=" * 78)
    i9a_at_vop1 = gm("M9a") * (vN11b_expr - vg15_sol)   # M9a: D=Vop1 -> kcl[Vop1]+=i9a
    i9b_at_vop1 = gm("M9b") * (vN14a14b_expr - vop1_sym)  # M9b: S=Vop1 -> kcl[Vop1]-=i9b
    i10_at_vop1 = gd("M10") * vop1_sym                   # M10: D=Vop1,S=gnd,G=0 -> gds10*vop1(O(eps))
    i_into_vop1 = sp.simplify(i9a_at_vop1 - i9b_at_vop1 + i10_at_vop1)
    i_into_vop1 = sp.expand(i_into_vop1)
    coeff_vop1 = sp.diff(i_into_vop1, vop1_sym)
    coeff_vdd = sp.diff(i_into_vop1, vdd)
    print(f"  I_into_Vop1 = ({sp.simplify(coeff_vop1)}) * vop1 + ({sp.simplify(coeff_vdd)}) * vdd")

    print()
    print("=" * 78)
    print("STEP 5 -- stage-1 8노드에 battery-A(Vop1)/battery-B(Vom1, 거울대칭) 전류를 얹어 재계산")
    print("=" * 78)
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
    vip, vim = sp.symbols("vip vim")

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

    i_batteryA_vop1 = i_into_vop1.subs(vop1_sym, v["Vop1"])
    i_batteryB_vom1 = i_into_vop1.subs(vop1_sym, v["Vom1"], simultaneous=True)  # 거울대칭 재사용
    kcl["Vop1"] += i_batteryA_vop1
    kcl["Vom1"] += i_batteryB_vom1

    sol = sp.solve([sp.Eq(kcl[n], 0) for n in nodes], [v[n] for n in nodes], dict=True)
    assert len(sol) == 1, f"해가 유일하지 않다: {len(sol)}"
    sol = sol[0]
    vom1_full, vop1_full = sol[v["Vom1"]], sol[v["Vop1"]]

    dm = {vip: sp.Rational(1, 2), vim: sp.Rational(-1, 2), vdd: 0}
    ripple = {vip: 0, vim: 0, vdd: 1}
    Adm_full = sp.simplify((vop1_full - vom1_full).subs(dm))
    Ann_full = sp.simplify(((vop1_full + vom1_full) / 2).subs(ripple))
    print(f"  Adm_full = {sp.factor(Adm_full)}")
    print()
    print(f"  Ann_full = {sp.factor(Ann_full)}")

    print()
    print("=" * 78)
    print("STEP 6 -- Adm_full/Ann_full의 leading order (gdsh_M10도 O(eps)로 취급 --")
    print("  M10은 stage-1 소자와 마찬가지로 캐스코드 아닌 단순 sink이므로 같은 스케일)")
    print("=" * 78)
    eps = sp.Symbol("eps", positive=True)
    gds_syms = [sym[(c, "gds")] for c in {"M1a", "M2a", "M3a", "M4a", "M5", "M6", "M7"}]
    gdsh_m10 = sp.Symbol("gdsh_M10", positive=True)
    S = {s: eps * sp.Symbol(f"hat_{s}", positive=True) for s in gds_syms}
    S[gdsh_m10] = eps * sp.Symbol("hat_gdsh_M10", positive=True)

    Adm_e = sp.together(Adm_full.subs(S))
    Ann_e = sp.together(Ann_full.subs(S))
    Adm_lead = Ann_lead = None
    for k in range(-2, 4):
        val = sp.limit(Adm_e * eps**k, eps, 0)
        if val not in (0, sp.oo, -sp.oo, sp.zoo):
            print(f"  Adm_full ~ (1/eps^{-k}) * {sp.factor(val)}")
            Adm_lead = val
            break
    for k in range(-2, 4):
        val = sp.limit(Ann_e * eps**k, eps, 0)
        if val not in (0, sp.oo, -sp.oo, sp.zoo):
            print(f"  Ann_full ~ (1/eps^{-k}) * {sp.factor(val)}")
            Ann_lead = val
            break

    print()
    print("=" * 78)
    print("STEP 7 -- 수치 검증: leading-order 폐형식 vs 세션20 stage1-only 근사, PSRR(dB) 차이")
    print("=" * 78)
    import math
    import random

    # 세션20 stage1-only 폐형식(그대로 재사용, 물리 스케일 gds_* 그대로 사용).
    def stage1_only(p):
        Kpp = p["gm_M2a"] / (p["gds_M1a"] * p["gds_M2a"])
        Knp = p["gm_M3a"] / (p["gds_M4a"] * p["gds_M3a"])
        adm = (p["gm_M1a"] + p["gm_M4a"]) * (Kpp * Knp / (Kpp + Knp))
        kp, kn = p["gm_M1a"] * Kpp, p["gm_M4a"] * Knp
        rx, ry = 1.0 / (p["gds_M6"] + p["gds_M7"]), 1.0 / p["gds_M5"]
        acm = (rx + ry) * kp * kn / (kn * ry + kp * rx)
        ann = (p["gm_M6"] + p["gm_M7"]) * (rx * ry / (rx + ry)) * acm
        return adm, ann

    all_syms = sorted(set(Adm_full.free_symbols) | set(Ann_full.free_symbols), key=str)
    f_adm_full = sp.lambdify(all_syms, Adm_full, "math")
    f_ann_full = sp.lambdify(all_syms, Ann_full, "math")
    lead_syms_adm = sorted(Adm_lead.free_symbols, key=str) if Adm_lead is not None else []
    lead_syms_ann = sorted(Ann_lead.free_symbols, key=str) if Ann_lead is not None else []
    f_adm_lead = sp.lambdify(lead_syms_adm, Adm_lead, "math") if Adm_lead is not None else None
    f_ann_lead = sp.lambdify(lead_syms_ann, Ann_lead, "math") if Ann_lead is not None else None

    BASE = {"gm_M1a": 119e-6, "gds_M1a": 1 / 600e3, "gm_M2a": 130e-6, "gds_M2a": 1 / 700e3,
            "gm_M4a": 140e-6, "gds_M4a": 1 / 250e3, "gm_M3a": 150e-6, "gds_M3a": 1 / 300e3,
            "gm_M6": 60e-6, "gds_M6": 0.5e-6, "gm_M7": 25e-6, "gds_M7": 0.4e-6,
            "gm_M5": 0.0, "gds_M5": 1.0e-6, "gm_M8": 40e-6, "gdsh_M10": 0.6e-6}

    random.seed(21)
    worst = 0.0
    for i in range(15):
        p = dict(BASE)
        for k in p:
            if p[k]:
                p[k] *= math.exp(random.uniform(-math.log(4), math.log(4)))
        p["hat_gdsh_M10"] = p["gdsh_M10"]   # leading-order 기호 별칭(같은 물리값)
        args_full = [p[str(s)] for s in all_syms]
        adm_x, ann_x = f_adm_full(*args_full), f_ann_full(*args_full)
        db_x = 20 * math.log10(abs(adm_x / ann_x))

        args_lead_adm = [p[str(s)] for s in lead_syms_adm]
        args_lead_ann = [p[str(s)] for s in lead_syms_ann]
        adm_l = f_adm_lead(*args_lead_adm) if f_adm_lead else None
        ann_l = f_ann_lead(*args_lead_ann) if f_ann_lead else None
        db_l = 20 * math.log10(abs(adm_l / ann_l)) if (adm_l and ann_l) else float("nan")

        adm_s1, ann_s1 = stage1_only(p)
        db_s1 = 20 * math.log10(abs(adm_s1 / ann_s1))

        print(f"  rand{i:<2d} exact(31dev)={db_x:8.4f}dB  lead(31dev)={db_l:8.4f}dB"
              f"({db_l-db_x:+.4f})  stage1-only(세션20)={db_s1:8.4f}dB({db_s1-db_x:+.4f})")
        worst = max(worst, abs(db_l - db_x))
    print(f"  WORST |lead - exact(31소자)| = {worst:.4f} dB")
    print(f"  (stage1-only과의 차이가 크게 나오면 battery 경로가 실제로 PSRR을 지배한다는 뜻)")


if __name__ == "__main__":
    main()
