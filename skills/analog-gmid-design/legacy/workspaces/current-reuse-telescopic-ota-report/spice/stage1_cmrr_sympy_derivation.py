# -*- coding: utf-8 -*-
"""stage-1 (current-reuse telescopic) CMRR closed form -- derivation FROM SCRATCH.

2026-08-03. Motivation: `sizing_recipe.py`의 self-test가
`assert M2a.drain == M3a.source` 에서 죽었다 -- 그 assert는 "PMOS 캐스코드의 드레인이
NMOS 캐스코드의 소스로 이어지는 하나의 직렬 텔레스코픽 기둥"이라는 **옛 위상 가정**이다.
확정된 topology.json은 그렇지 않다: M2a.drain == M3a.drain == Vom1 (드레인끼리 만난다).

이 스크립트는 논문 이미지를 다시 읽지 않는다. connectivity는 **오직**
`stick_diagram.load_topology()`로 topology.json에서 읽어 온 `Transistor` 객체의
`.source/.drain/.gate`만 쓴다(프로젝트 원칙: topology.json이 유일한 토폴로지 소스).

절차
  1. JSON에서 1단 소자 11개(M6,M7,M1a,M1b,M2a,M2b,M3a,M3b,M4a,M4b,M5)를 뽑는다.
  2. 그 connectivity로 **자동으로** 소신호 MNA를 세운다(손타이핑 netlist 없음).
     소자모델: I(drain->source) = gm*(vg-vs) + gds*(vd-vs)  (극성 무관 -- pmos/nmos 동일,
     nmos/pmos 부호는 이미 gm 정의에 흡수돼 있다).
  3. vdd/gnd/Vbias1..4/Vcmfb를 AC ground로 두고(open-loop: CMFB 루프 끊음),
     Vip/Vim을 독립 전압원으로 두고 sympy로 **정확해**를 푼다.
  4. DM(vip=+1/2, vim=-1/2)과 CM(vip=vim=1)의 정확해에서 Adm/Acm을 얻고,
     gm*ro>>1 leading order를 취해 폐형식을 얻는다.
  5. 폐형식 vs 정확해를 랜덤 스윕으로 수치 비교한다.

결론(스크립트 실행 결과가 증거):
  Kp' = gm(M2a)/(gds(M1a)*gds(M2a))        <- 캐스코드 소자의 gm (입력쌍 gm 아님!)
  Kn' = gm(M3a)/(gds(M4a)*gds(M3a))
  Kp  = gm(M1a)*Kp' ,  Kn = gm(M4a)*Kn'
  Rx  = 1/(gds(M6)+gds(M7)) ,  Ry = 1/gds(M5)
  Adm = (gm(M1a)+gm(M4a)) * (Kp' ∥ Kn')
  Acm = (Rx+Ry)*Kp*Kn / (Kn*Ry + Kp*Rx)
  CMRR = 20log10(Adm/Acm)
"""
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
# open-loop 해석: 전원/접지/바이어스 게이트/Vcmfb는 AC ground.
AC_GROUND = {"vdd", "gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4", "Vcmfb"}
# a/b 대칭쌍은 같은 기호를 공유한다(완전 대칭 가정 -- CMRR 1차 근사의 표준 전제).
PAIR = {"M1b": "M1a", "M2b": "M2a", "M3b": "M3a", "M4b": "M4a"}


def load_stage1():
    trs, meta = load_topology(TOPO_JSON)
    by_name = {t.name: t for t in trs}
    missing = [n for n in STAGE1 if n not in by_name]
    if missing:
        raise RuntimeError(f"topology.json에 없는 1단 소자: {missing}")
    return [by_name[n] for n in STAGE1], meta, by_name


def report_connectivity(devs):
    print("=" * 78)
    print("STEP 1 -- load_topology()가 실제로 돌려준 1단 connectivity (손타이핑 아님)")
    print("=" * 78)
    print("%-6s %-6s %-10s %-10s %-10s" % ("name", "kind", "source", "drain", "gate"))
    for t in devs:
        print("%-6s %-6s %-10s %-10s %-10s" % (t.name, t.kind, t.source, t.drain, t.gate))
    d = {t.name: t for t in devs}
    print()
    print(f"  M2a.drain = {d['M2a'].drain!r}   M3a.drain = {d['M3a'].drain!r}"
          f"   M3a.source = {d['M3a'].source!r}")
    print(f"  -> 옛 가정 (M2a.drain == M3a.source): "
          f"{d['M2a'].drain == d['M3a'].source}  <-- 이게 틀렸던 가정")
    print(f"  -> 실제        (M2a.drain == M3a.drain): "
          f"{d['M2a'].drain == d['M3a'].drain}  (= {d['M2a'].drain!r})")
    print(f"  PMOS 직렬 캐스코드 (M1a.drain == M2a.source): "
          f"{d['M1a'].drain == d['M2a'].source} (= {d['M2a'].source!r})")
    print(f"  NMOS 직렬 캐스코드 (M4a.drain == M3a.source): "
          f"{d['M4a'].drain == d['M3a'].source} (= {d['M3a'].source!r})")
    print(f"  PMOS tail Vx (M6.drain==M7.drain==M1a.source): "
          f"{d['M6'].drain == d['M7'].drain == d['M1a'].source} (= {d['M1a'].source!r})")
    print(f"  NMOS tail Vy (M5.drain==M4a.source): "
          f"{d['M5'].drain == d['M4a'].source} (= {d['M4a'].source!r})")
    print()


def build_mna(devs, vip, vim):
    """JSON connectivity만으로 소신호 MNA를 자동 조립 -> (sol, nodes, syms)."""
    sym = {}          # (devname_canonical, 'gm'|'gds') -> Symbol
    def g(name, key):
        canon = PAIR.get(name, name)
        k = (canon, key)
        if k not in sym:
            sym[k] = sp.Symbol(f"{key}_{canon}", positive=True)
        return sym[k]

    # 미지 노드 = AC ground도 아니고 입력도 아닌 모든 노드
    nodes = []
    for t in devs:
        for n in (t.source, t.drain, t.gate):
            if n not in AC_GROUND and n not in ("Vip", "Vim") and n not in nodes:
                nodes.append(n)
    v = {n: sp.Symbol(f"v_{n}") for n in nodes}

    def pot(n):
        if n in AC_GROUND:
            return sp.Integer(0)
        if n == "Vip":
            return vip
        if n == "Vim":
            return vim
        return v[n]

    kcl = {n: sp.Integer(0) for n in nodes}
    for t in devs:
        vd, vs, vg = pot(t.drain), pot(t.source), pot(t.gate)
        i_ds = g(t.name, "gm") * (vg - vs) + g(t.name, "gds") * (vd - vs)
        if t.drain in kcl:
            kcl[t.drain] += i_ds          # drain 노드에서 소자로 빠져나가는 전류
        if t.source in kcl:
            kcl[t.source] -= i_ds         # source 노드로 소자에서 들어오는 전류
    sol = sp.solve([sp.Eq(kcl[n], 0) for n in nodes], [v[n] for n in nodes], dict=True)
    if len(sol) != 1:
        raise RuntimeError(f"MNA 해가 유일하지 않다: {len(sol)}")
    return sol[0], v, sym


def main():
    devs, meta, by_name = load_stage1()
    report_connectivity(devs)

    print("=" * 78)
    print("STEP 2 -- JSON connectivity에서 자동 조립한 MNA를 sympy로 정확히 푼다")
    print("=" * 78)
    vip, vim = sp.symbols("vip vim")
    sol, v, sym = build_mna(devs, vip, vim)
    vom1, vop1 = sol[v["Vom1"]], sol[v["Vop1"]]

    dm = {vip: sp.Rational(1, 2), vim: sp.Rational(-1, 2)}
    cm = {vip: 1, vim: 1}
    Adm_exact = sp.simplify((vop1 - vom1).subs(dm))     # v(Vop1)-v(Vom1) per 1V diff
    Acm_exact = sp.simplify(((vop1 + vom1) / 2).subs(cm))
    print("  Adm_exact, Acm_exact 정확해 확보(기호식은 길어서 생략, 아래 수치검증으로 확인).")
    print(f"  Adm_exact 항 수 = {sp.count_ops(Adm_exact)},  "
          f"Acm_exact 항 수 = {sp.count_ops(Acm_exact)}")

    print()
    print("=" * 78)
    print("STEP 3 -- gm*ro >> 1 leading order (기호적으로 확인)")
    print("=" * 78)
    # gds_* = eps * gdsn_* 로 두고 eps->0 극한을 취한다(= 모든 ro를 1/eps배).
    eps = sp.Symbol("eps", positive=True)
    S = {}
    hat = {}
    for (dev, key), s in sym.items():
        if key == "gds":
            hat[(dev, key)] = sp.Symbol(f"gdsh_{dev}", positive=True)
            S[s] = eps * hat[(dev, key)]
    gd = lambda d: hat[(d, "gds")]
    gm = lambda d: sym[(d, "gm")]

    # Adm: eps->0에서 유한(캐스코드라 Rout~1/eps^2, Gm 유한 -> Adm ~ 1/eps^2)
    Adm_e = sp.simplify(Adm_exact.subs(S))
    Acm_e = sp.simplify(Acm_exact.subs(S))
    # Adm, Acm 모두 eps->0에서 O(1/eps^2) (캐스코드 Rout~1/eps^2, CM은 (Rx+Ry)~1/eps
    # 곱하기 Kp*Kn/(KnRy+KpRx)~1/eps -- 둘이 같은 차수라 CMRR 자체는 O(1)이다).
    Adm_lead = sp.simplify(sp.limit(Adm_e * eps**2, eps, 0))
    Acm_lead = sp.simplify(sp.limit(Acm_e * eps**2, eps, 0))
    print("  Adm ~ (1/eps^2) *", sp.factor(Adm_lead))
    print("  Acm ~ (1/eps^2) *", sp.factor(Acm_lead))

    # 제안 폐형식
    Kp_prime = gm("M2a") / (gd("M1a") * gd("M2a"))
    Kn_prime = gm("M3a") / (gd("M4a") * gd("M3a"))
    Kp = gm("M1a") * Kp_prime
    Kn = gm("M4a") * Kn_prime
    Rx = 1 / (gd("M6") + gd("M7"))
    Ry = 1 / gd("M5")
    Adm_cf = (gm("M1a") + gm("M4a")) * (Kp_prime * Kn_prime / (Kp_prime + Kn_prime))
    Acm_cf = (Rx + Ry) * Kp * Kn / (Kn * Ry + Kp * Rx)
    print()
    print("  제안 폐형식 Adm_cf - leading(Adm) =",
          sp.simplify(sp.together(Adm_cf - Adm_lead)))
    # Acm은 부호가 음수로 나온다(CM 이득은 반전) -- 크기 비교를 위해 부호를 맞춘다.
    print("  제안 폐형식 Acm_cf + leading(Acm) =",
          sp.simplify(sp.together(Acm_cf + Acm_lead)))
    print("  (둘 다 0이면 폐형식 == leading order, 기호적으로 동일. Acm은 부호만 반대)")

    print()
    print("=" * 78)
    print("STEP 4 -- 정확해 vs 폐형식 수치 비교(랜덤 스윕 30점, 물리적으로 그럴듯한 범위)")
    print("=" * 78)
    f_exact_dm = sp.lambdify(sorted(sym.values(), key=str), Adm_exact, "math")
    f_exact_cm = sp.lambdify(sorted(sym.values(), key=str), Acm_exact, "math")
    order = [str(s) for s in sorted(sym.values(), key=str)]
    BASE = {"gm_M1a": 119e-6, "gds_M1a": 1 / 600e3, "gm_M2a": 130e-6, "gds_M2a": 1 / 700e3,
            "gm_M4a": 140e-6, "gds_M4a": 1 / 250e3, "gm_M3a": 150e-6, "gds_M3a": 1 / 300e3,
            "gm_M6": 0.0, "gds_M6": 0.5e-6, "gm_M7": 0.0, "gds_M7": 0.4e-6,
            "gm_M5": 0.0, "gds_M5": 1.0e-6}

    def closed_form(p):
        Kpp = p["gm_M2a"] / (p["gds_M1a"] * p["gds_M2a"])
        Knp = p["gm_M3a"] / (p["gds_M4a"] * p["gds_M3a"])
        adm = (p["gm_M1a"] + p["gm_M4a"]) * (Kpp * Knp / (Kpp + Knp))
        kp, kn = p["gm_M1a"] * Kpp, p["gm_M4a"] * Knp
        rx = 1.0 / (p["gds_M6"] + p["gds_M7"])
        ry = 1.0 / p["gds_M5"]
        acm = (rx + ry) * kp * kn / (kn * ry + kp * rx)
        return adm, acm

    def old_closed_form(p):
        """폐기 대상: 캐스코드 부스팅에 **입력쌍** gm을 쓴 옛 식(_cmrr_telescopic_class_ab)."""
        Kpp = p["gm_M1a"] / (p["gds_M1a"] * p["gds_M2a"])
        Knp = p["gm_M4a"] / (p["gds_M4a"] * p["gds_M3a"])
        adm = (p["gm_M1a"] + p["gm_M4a"]) * (Kpp * Knp / (Kpp + Knp))
        kp, kn = p["gm_M1a"] * Kpp, p["gm_M4a"] * Knp
        rx = 1.0 / (p["gds_M6"] + p["gds_M7"])
        ry = 1.0 / p["gds_M5"]
        acm = (rx + ry) * kp * kn / (kn * ry + kp * rx)
        return adm, acm

    random.seed(11)
    worst_new = worst_old = 0.0
    rows = []
    for i in range(30):
        p = dict(BASE)
        for k in p:
            if p[k]:
                p[k] *= math.exp(random.uniform(-math.log(4), math.log(4)))
        args = [p[n] for n in order]
        adm_x, acm_x = f_exact_dm(*args), f_exact_cm(*args)
        db_x = 20 * math.log10(abs(adm_x / acm_x))
        adm_c, acm_c = closed_form(p)
        db_c = 20 * math.log10(abs(adm_c / acm_c))
        adm_o, acm_o = old_closed_form(p)
        db_o = 20 * math.log10(abs(adm_o / acm_o))
        worst_new = max(worst_new, abs(db_c - db_x))
        worst_old = max(worst_old, abs(db_o - db_x))
        rows.append((i, db_x, db_c, db_o))
    for i, dx, dc, do in rows[:8]:
        print(f"  rand{i:<2d} exact={dx:8.4f}dB  new_cf={dc:8.4f}({dc-dx:+.4f})"
              f"  old_cf(input-gm)={do:8.4f}({do-dx:+.4f})")
    print(f"  ... ({len(rows)}점)")
    print(f"  WORST |new_cf - exact| = {worst_new:.4f} dB")
    print(f"  WORST |old_cf - exact| = {worst_old:.4f} dB   <- 캐스코드 gm을 잘못 쓴 옛 식")
    print()
    print("  주: Adm/Acm 비에서 Kp'/Kn' 스케일이 부분적으로 상쇄돼 CMRR(dB) 차이는 작지만,")
    print("      Adm(=DC 이득) 자체는 gm(M2a)/gm(M1a) 비만큼 통째로 틀린다:")
    p = dict(BASE)
    print(f"      base 사이징에서 Adm_exact={f_exact_dm(*[p[n] for n in order]):.4g}, "
          f"new_cf={closed_form(p)[0]:.4g}, old_cf={old_closed_form(p)[0]:.4g}")


if __name__ == "__main__":
    main()
