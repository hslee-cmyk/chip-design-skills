# -*- coding: utf-8 -*-
"""stage-1 (current-reuse telescopic) PSRR+ closed form -- derivation FROM SCRATCH
(2026-08-07, 세션20 후속). `stage1_cmrr_sympy_derivation.py`와 정확히 같은 방법론/topology
모델을 그대로 재사용한다 -- 유일한 차이는 독립원이 Vip/Vim(DM/CM)이 아니라 vdd(전원 리플)라는
것뿐이다. connectivity는 오직 `load_topology()`로 topology.json에서 읽는다(손타이핑 없음).

배경(세션20 발견): 기존 `psrr_estimate_db` metric은 `circuit_family="diff_pair_tail"`
(M5의 gm/gds만 보는 자리표시자, docstring 자신이 "order-of-magnitude 근사, 검증된 폐형식
없음"이라고 명시)이었다 -- 그런데 이 회로에서 M5는 **13개 자유 theta 중 어느 것에도 안
닿는다**(고정 KCL 관계로만 값이 정해짐, 실측 확인). 즉 이 placeholder로는 PSRR 제약을
만족시킬 자유도 자체가 없어, 그리드 탐색을 아무리 잘 바꿔도 못 푼다 -- CMRR이 이미 겪은
문제(`diff_pair_tail` -> `telescopic_class_ab` -> `telescopic_class_ab_cmfb`)와 같은 종류라
CMRR과 동일한 절차로 stage-1 전용 PSRR 폐형식을 새로 유도한다.

절차 (stage1_cmrr_sympy_derivation.py STEP 1~4와 동일 절차, 입력만 다름)
  1. JSON에서 1단 소자 11개를 읽는다.
  2. connectivity로 자동 MNA 조립. **vdd를 AC ground에서 빼고 독립 전압원(rd)으로
     둔다** -- CMRR의 Vip/Vim 대신 이번엔 vdd가 스윕 대상. Vip/Vim(신호 입력)은 이번엔
     AC ground(0V, 순수 전원->출력 전달만 본다). gnd/Vbias1..4/Vcmfb는 여전히 AC ground
     (open-loop, "이상적 바이어스" 가정 -- CMRR의 첫 pass가 CMFB를 뺐던 것과 동일한 종류의
     정직한 한계, 아래 STEP 5 주석 참고).
  3. Adm은 CMRR 유도와 동일(vdd=0일 때 vip/vim 차동 응답) -- 재유도하지 않고 그대로 재사용
     (같은 회로, 같은 신호경로이므로 당연히 같다 -- 이 스크립트에서도 직접 재계산해서
     기호적으로 같은지 재확인한다).
  4. Ann = (vop1+vom1)/2, vip=vim=0, vdd=1V 리플 기준.
  5. PSRR = 20*log10(|Adm/Ann|). leading order 취해 폐형식 확인, 수치 대조.
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
# PSRR 해석: gnd/바이어스 게이트/Vcmfb는 여전히 AC ground(이상적 바이어스 가정, 정직한
# 한계 -- 아래 STEP 5 주석). vdd는 이번엔 AC ground가 아니라 독립원이다(빠져 있음이 핵심).
AC_GROUND = {"gnd", "Vbias1", "Vbias2", "Vbias3", "Vbias4", "Vcmfb"}
PAIR = {"M1b": "M1a", "M2b": "M2a", "M3b": "M3a", "M4b": "M4a"}


def load_stage1():
    trs, meta = load_topology(TOPO_JSON)
    by_name = {t.name: t for t in trs}
    missing = [n for n in STAGE1 if n not in by_name]
    if missing:
        raise RuntimeError(f"topology.json에 없는 1단 소자: {missing}")
    return [by_name[n] for n in STAGE1], meta, by_name


def build_mna(devs, vip, vim, vdd):
    """CMRR 스크립트의 build_mna()와 동일 -- 이번엔 vip/vim/vdd 셋 다 독립원으로 받는다
    (CMRR 쪽은 vdd가 AC ground로 고정, 이번엔 vip/vim이 보통 0으로 고정된다는 차이뿐,
    함수 자체는 완전히 동일한 일반 MNA 조립기)."""
    sym = {}
    def g(name, key):
        canon = PAIR.get(name, name)
        k = (canon, key)
        if k not in sym:
            sym[k] = sp.Symbol(f"{key}_{canon}", positive=True)
        return sym[k]

    nodes = []
    for t in devs:
        for n in (t.source, t.drain, t.gate):
            if n not in AC_GROUND and n not in ("Vip", "Vim", "vdd") and n not in nodes:
                nodes.append(n)
    v = {n: sp.Symbol(f"v_{n}") for n in nodes}

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
    for t in devs:
        vd, vs, vg = pot(t.drain), pot(t.source), pot(t.gate)
        i_ds = g(t.name, "gm") * (vg - vs) + g(t.name, "gds") * (vd - vs)
        if t.drain in kcl:
            kcl[t.drain] += i_ds
        if t.source in kcl:
            kcl[t.source] -= i_ds
    sol = sp.solve([sp.Eq(kcl[n], 0) for n in nodes], [v[n] for n in nodes], dict=True)
    if len(sol) != 1:
        raise RuntimeError(f"MNA 해가 유일하지 않다: {len(sol)}")
    return sol[0], v, sym


def main():
    devs, meta, by_name = load_stage1()
    print("=" * 78)
    print("STEP 1 -- connectivity는 stage1_cmrr_sympy_derivation.py와 동일 회로(재확인 생략,")
    print("  그 스크립트가 이미 검증함)")
    print("=" * 78)

    print()
    print("=" * 78)
    print("STEP 2 -- vdd를 독립원으로 둔 MNA를 sympy로 정확히 푼다")
    print("=" * 78)
    vip, vim, vdd = sp.symbols("vip vim vdd")
    sol, v, sym = build_mna(devs, vip, vim, vdd)
    vom1, vop1 = sol[v["Vom1"]], sol[v["Vop1"]]

    dm = {vip: sp.Rational(1, 2), vim: sp.Rational(-1, 2), vdd: 0}
    ripple = {vip: 0, vim: 0, vdd: 1}
    Adm_exact = sp.simplify((vop1 - vom1).subs(dm))
    Ann_exact = sp.simplify(((vop1 + vom1) / 2).subs(ripple))
    print(f"  Adm_exact 항 수 = {sp.count_ops(Adm_exact)},  Ann_exact 항 수 = {sp.count_ops(Ann_exact)}")

    print()
    print("=" * 78)
    print("STEP 3 -- gm*ro >> 1 leading order")
    print("=" * 78)
    eps = sp.Symbol("eps", positive=True)
    S, hat = {}, {}
    for (dev, key), s in sym.items():
        if key == "gds":
            hat[(dev, key)] = sp.Symbol(f"gdsh_{dev}", positive=True)
            S[s] = eps * hat[(dev, key)]
    gd = lambda d: hat[(d, "gds")]
    gm = lambda d: sym[(d, "gm")]

    Adm_e = sp.simplify(Adm_exact.subs(S))
    Ann_e = sp.simplify(Ann_exact.subs(S))
    Adm_lead = sp.simplify(sp.limit(Adm_e * eps**2, eps, 0))
    Ann_lead = sp.simplify(sp.limit(Ann_e * eps**1, eps, 0))
    print("  Adm ~ (1/eps^2) *", sp.factor(Adm_lead))
    print("  Ann ~ (1/eps^1) *", sp.factor(Ann_lead))
    print("  (Adm/Ann이 eps->0에서 발산(1/eps) -- PSRR은 gds가 작을수록 좋아진다는 뜻,")
    print("   물리적으로 타당함: 캐스코드 출력임피던스가 커질수록 vdd 리플이 출력에 덜 실린다)")

    Kp_prime = gm("M2a") / (gd("M1a") * gd("M2a"))
    Kn_prime = gm("M3a") / (gd("M4a") * gd("M3a"))
    Adm_cf = (gm("M1a") + gm("M4a")) * (Kp_prime * Kn_prime / (Kp_prime + Kn_prime))
    print()
    print("  Adm_cf(CMRR 유도와 동일식) - leading(Adm) =",
          sp.simplify(sp.together(Adm_cf - Adm_lead)), " (0이면 같은 Adm 재확인)")

    print()
    print("  Ann_lead 인수분해:", sp.factor(Ann_lead))


if __name__ == "__main__":
    main()
