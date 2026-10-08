"""tests/metrics 공용 -- metrics/CONTRACT.md 5절 예 회로 생성기, 폐형식 기대값, 독립 numpy MNA, 호출 계수기.

피검 함수로 기대값을 만들지 않는다. 기대값 출처는 셋뿐이다.
- CONTRACT 5절의 폐형식·손계산(이 파일 `closed_*`).
- 이 파일의 독립 MNA(`ref_solve`): 전체 노드 어드미턴스 Y(s) = G + sC 를 직접 세워 고정 노드를 소거해 푼다.
- scipy brentq 로 폐형식 |H(jω)| 교차를 따로 푼다.
노드는 전부 정수(이름 리터럴 없음). `nm` 인자(노드 치환 dict)로 같은 회로를 다른 번호로 만들 수 있다(I-7).
"""
from __future__ import annotations

import cmath
import math
import sys
from contextlib import contextmanager

import numpy as np
from scipy.optimize import brentq

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    MosSmallSignal,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    mos_stamps,
    two_terminal_stamps,
)

TWO_PI = 2.0 * math.pi


def rel_close(a, b, rtol=1e-9, atol=0.0):
    return abs(a - b) <= max(rtol * max(abs(a), abs(b)), atol)


def codes(undefined):
    """Undefined 묶음(tuple 또는 단일·None) -> code 집합."""
    if undefined is None:
        return set()
    if not isinstance(undefined, tuple):
        undefined = (undefined,)
    return {u.code for u in undefined}


# ---------------------------------------------------------------- 호출 계수기

@contextmanager
def count_calls(*funcs):
    """funcs 의 코드 객체가 호출된 횟수를 센다(sys.setprofile, 소스·모듈 경로를 몰라도 된다).
    yield 하는 dict: {func.__name__: 횟수}."""
    codes_ = {f.__code__: f.__name__ for f in funcs}
    counts = {name: 0 for name in codes_.values()}
    prev = sys.getprofile()

    def prof(frame, event, arg):
        if event == "call":
            name = codes_.get(frame.f_code)
            if name is not None:
                counts[name] += 1

    sys.setprofile(prof)
    try:
        yield counts
    finally:
        sys.setprofile(prev)


STAMP_FUNCS = (mos_stamps, two_terminal_stamps)


# ---------------------------------------------------------------- 노드 치환

def ident(n):
    return n


def mapper(nm):
    if nm is None:
        return ident
    return lambda n: nm[n]


# ---------------------------------------------------------------- 예 회로 (CONTRACT 5절)

def ex1_rc(nm=None):
    """예 1: R(1,2,1k), C(2,0,1n), 1 V at 1, Sense(2)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(resistors=(Resistor(m(1), m(2), 1e3),), capacitors=(Capacitor(m(2), m(0), 1e-9),),
                            ac_ground=(m(0),))
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), (Sense(m(2)),))


EX2_GM, EX2_GDS, EX2_CL = 1e-3, 1e-5, 1e-12


def ex2_amp(nm=None):
    """예 2 A 계: CS, 열 vin(1 V at 1)·iout(1 A at 2), Sense(2)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(
        mos=(MosSmallSignal(m(2), m(1), m(0), m(0), EX2_GM, 0.0, EX2_GDS),),
        capacitors=(Capacitor(m(2), m(0), EX2_CL),),
        ac_ground=(m(0),),
    )
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)), Excitation("iout", currents=((m(2), 1.0),))),
                     (Sense(m(2)),))


def ex2_beta_res(nm=None):
    """예 2 β 계(저항): R(2,3,30k), R(3,0,10k), 1 V at 2, Sense(3) -> β = 0.25."""
    m = mapper(nm)
    ck = SmallSignalCircuit(resistors=(Resistor(m(2), m(3), 30e3), Resistor(m(3), m(0), 10e3)), ac_ground=(m(0),))
    return build_mna(ck, (Excitation("vfb", voltages=((m(2), 1.0),)),), (Sense(m(3)),))


def ex2c_beta_cap(nm=None, cf=1e-12, cs=3e-12):
    """예 2c: Cf(2,3), Cs(3,0), 1 V at 2, Sense(3) -> β = Cf/(Cf+Cs)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(capacitors=(Capacitor(m(2), m(3), cf), Capacitor(m(3), m(0), cs)), ac_ground=(m(0),))
    return build_mna(ck, (Excitation("vfb", voltages=((m(2), 1.0),)),), (Sense(m(3)),))


def ex2b_sf(gmb=2e-4, nm=None):
    """예 2b: source follower, d=9 교류접지, RL 10k, 1 V at 1, Sense(2)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(
        mos=(MosSmallSignal(m(9), m(1), m(2), m(0), 1e-3, gmb, 1e-5),),
        resistors=(Resistor(m(2), m(0), 1e4),),
        ac_ground=(m(0), m(9)),
    )
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), (Sense(m(2)),))


EX2D = dict(gm=1e-3, gds=1e-5, cf=1e-12, cs=3e-12, cl=1e-12)


def ex2d_sc_loop(nm=None):
    """예 2d: gate(3) 가 용량으로만 이어진 폐루프 CS. 열 vin(1 V at 1)·iinj(1 A at 3), Sense(2)."""
    m = mapper(nm)
    p = EX2D
    ck = SmallSignalCircuit(
        mos=(MosSmallSignal(m(2), m(3), m(0), m(0), p["gm"], 0.0, p["gds"]),),
        capacitors=(Capacitor(m(2), m(3), p["cf"]), Capacitor(m(3), m(1), p["cs"]), Capacitor(m(2), m(0), p["cl"])),
        ac_ground=(m(0),),
    )
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)), Excitation("iinj", currents=((m(3), 1.0),))),
                     (Sense(m(2)),))


EX3 = dict(gm1=1e-4, g1=1e-6, gm2=1e-3, g2=1e-5, c1=0.1e-12, cl=1e-12, cc=0.5e-12)


def ex3_miller(nm=None, with_cc=True):
    """예 3: 2극 Miller. M1(d=2,g=1), M2(d=3,g=2), C1(2,0), CL(3,0), Cc(2,3), 1 V at 1, Sense(3)."""
    m = mapper(nm)
    p = EX3
    caps = [Capacitor(m(2), m(0), p["c1"]), Capacitor(m(3), m(0), p["cl"])]
    if with_cc:
        caps.append(Capacitor(m(2), m(3), p["cc"]))
    ck = SmallSignalCircuit(
        mos=(MosSmallSignal(m(2), m(1), m(0), m(0), p["gm1"], 0.0, p["g1"]),
             MosSmallSignal(m(3), m(2), m(0), m(0), p["gm2"], 0.0, p["g2"])),
        capacitors=tuple(caps),
        ac_ground=(m(0),),
    )
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), (Sense(m(3)),))


def ex6_ratio(nm=None):
    """예 6: Ra(1,2,1k), Rb(2,3,10k), 열 num(1 V at 1)·den(1 V at 3), Sense(2)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(resistors=(Resistor(m(1), m(2), 1e3), Resistor(m(2), m(3), 1e4)), ac_ground=(m(0),))
    return build_mna(ck, (Excitation("num", voltages=((m(1), 1.0),)), Excitation("den", voltages=((m(3), 1.0),))),
                     (Sense(m(2)),))


RENUMBER = {0: 17, 1: 4, 2: 30, 3: 8, 9: 2}   # 0 이 교류접지가 아닌 번호로 가도 된다


# ---------------------------------------------------------------- 폐형식 (CONTRACT 5절)

def closed_single_pole():
    ro = 1.0 / EX2_GDS
    a0 = -EX2_GM * ro
    wp = 1.0 / (ro * EX2_CL)
    return a0, wp


def closed_single_pole_loop(beta):
    """T = A·β, 단일 극. 반환 (gain_db, ugf_hz, gbw_hz, pm_deg)."""
    a0, wp = closed_single_pole()
    t0 = abs(a0 * beta)
    ugf = wp * math.sqrt(t0 * t0 - 1.0) / TWO_PI
    gbw = t0 * wp / TWO_PI
    pm = 180.0 - math.degrees(math.atan(math.sqrt(t0 * t0 - 1.0)))
    return 20.0 * math.log10(t0), ugf, gbw, pm


def closed_miller():
    p = EX3
    r1, r2 = 1.0 / p["g1"], 1.0 / p["g2"]
    c1, cl, cc = p["c1"], p["cl"], p["cc"]
    k = p["gm1"] * p["gm2"] * r1 * r2
    a1 = r1 * (c1 + cc) + r2 * (cl + cc) + p["gm2"] * r1 * r2 * cc
    a2 = r1 * r2 * (c1 * cl + c1 * cc + cl * cc)
    z = p["gm2"] / cc
    disc = math.sqrt(a1 * a1 - 4.0 * a2)
    p1 = (a1 - disc) / (2.0 * a2)       # 작은 |극점| (실수 음극점의 크기)
    p2 = (a1 + disc) / (2.0 * a2)

    def h(w):
        s = 1j * w
        return k * (1.0 - s / z) / (1.0 + a1 * s + a2 * s * s)

    def lag(w):  # T(0) 대비 지연(rad): 두 LHP 극 + RHP 영점
        return math.atan(w / p1) + math.atan(w / p2) + math.atan(w / z)

    wu = brentq(lambda w: abs(h(w)) - 1.0, 1.0, 1e12, xtol=1e-12, rtol=1e-15, maxiter=500)
    w3 = brentq(lambda w: abs(h(w)) - k / math.sqrt(2.0), 1.0, 1e12, xtol=1e-12, rtol=1e-15, maxiter=500)
    return dict(k=k, a1=a1, a2=a2, z=z, p1=p1, p2=p2, h=h, ugf_hz=wu / TWO_PI, gbw_hz=k * w3 / TWO_PI,
                pm_deg=180.0 - math.degrees(lag(wu)), gain_db=20.0 * math.log10(k))


def closed_sc_loop_dc():
    p = EX2D
    a0 = -p["gm"] / p["gds"]
    return a0 * p["cs"] / ((p["cf"] + p["cs"]) - a0 * p["cf"])


# ---------------------------------------------------------------- 독립 MNA

def ref_solve(mos=(), res=(), cap=(), ac_ground=(0,), volts=None, amps=None, sense=(None, None), omega=1.0):
    """독립 MNA. mos: (d,g,s,b,gm,gmb,gds,cgs,cgd,cgb,cdb,csb) tuple 들, res/cap: (a,b,값).
    volts {노드: V}, amps {노드: 주입 A}. 반환 v(pos) − v(neg) (복소)."""
    volts = dict(volts or {})
    amps = dict(amps or {})
    nodes = set(ac_ground) | set(volts) | set(amps) | {n for n in sense if n is not None}
    for t in res + cap:
        nodes |= {t[0], t[1]}
    for t in mos:
        nodes |= set(t[:4])
    nodes = sorted(nodes)
    idx = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    s = 1j * omega
    Y = np.zeros((n, n), dtype=complex)

    def two(a, b, y):
        ia, ib = idx[a], idx[b]
        Y[ia, ia] += y
        Y[ib, ib] += y
        Y[ia, ib] -= y
        Y[ib, ia] -= y

    for a, b, r in res:
        two(a, b, 1.0 / r)
    for a, b, c in cap:
        two(a, b, s * c)
    for d, g, so, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb in mos:
        # I(d->s) = gm(vg-vs) + gmb(vb-vs) + gds(vd-vs): drain 에서 나감, source 로 들어옴
        for row, sign in ((d, 1.0), (so, -1.0)):
            r = idx[row]
            Y[r, idx[g]] += sign * gm
            Y[r, idx[b]] += sign * gmb
            Y[r, idx[d]] += sign * gds
            Y[r, idx[so]] -= sign * (gm + gmb + gds)
        for a, bb, c in ((g, so, cgs), (g, d, cgd), (g, b, cgb), (d, b, cdb), (so, b, csb)):
            if c:
                two(a, bb, s * c)
    fixed = set(ac_ground) | set(volts)
    unk = [x for x in nodes if x not in fixed]
    xf = np.array([volts.get(x, 0.0) for x in nodes if x in fixed], dtype=complex)
    fi = [idx[x] for x in nodes if x in fixed]
    ui = [idx[x] for x in unk]
    rhs = np.array([amps.get(x, 0.0) for x in unk], dtype=complex) - Y[np.ix_(ui, fi)] @ xf
    xu = np.linalg.solve(Y[np.ix_(ui, ui)], rhs)
    full = {}
    for x, v in zip([x for x in nodes if x in fixed], xf):
        full[x] = v
    for x, v in zip(unk, xu):
        full[x] = v
    pos, neg = sense
    return full[pos] - (full[neg] if neg is not None else 0.0)


def mos_t(d, g, s, b, gm, gmb, gds, cgs=0.0, cgd=0.0, cgb=0.0, cdb=0.0, csb=0.0):
    return (d, g, s, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb)


def phase(z):
    return cmath.phase(z)


# ---------------------------------------------------------------- 7a: 루프 절단·Middlebrook 독립 구현 (CONTRACT 3.16·3.17·예 7)

def ref_middlebrook(mos=(), res=(), cap=(), ac_ground=(0,), cuts=(), weights=(1.0,), omega=1.0):
    """독립 Middlebrook 이중 주입(오라클 넷리스트와 같은 배치). 절단 회로를 test 쪽에서 직접 만들고(3.16: 같은 원래 노드
    -> 같은 x, x = 원래 최대 노드 + 1 부터 n 오름차순) 쌍마다 프로브 전압원 `Vlb n x`(MNA 가지 전류 = n -> x)와 전류원
    `Ilb 0 n`(n 으로 주입)을 넣는다.
      - 전압 실험: Vlb_k = w_k, Ilb = 0 -> Tv = −wᵀV_x / wᵀV_n
      - 전류 실험: Vlb = 0, Ilb_k = w_k -> I_k = i(Vlb_k), Ti = wᵀI / wᵀ(w − I)
      - T = (Tv·Ti − 1)/(Tv + Ti + 2)
    mos: (d, g, s, b, gm, gmb, gds), res/cap: (a, b, 값), cuts: ((kind, index, terminal), ...). ω > 0 전용.
    반환 dict(T, Tv, Ti, pairs)."""
    res = [list(r) for r in res]
    cap = [list(c) for c in cap]
    nodes = set(ac_ground)
    for e in res + cap:
        nodes |= {e[0], e[1]}
    for m in mos:
        nodes |= set(m[:4])
    moved = []
    for kind, idx, term in cuts:
        el = (res if kind == "resistor" else cap)[idx]
        moved.append((el, 0 if term == "a" else 1))
    orig = sorted({el[t] for el, t in moved})
    top = max(nodes)
    xs = {n: top + 1 + i for i, n in enumerate(orig)}
    for el, t in moved:
        el[t] = xs[el[t]]
    pairs = tuple((n, xs[n]) for n in orig)
    allnodes = sorted(nodes | set(xs.values()))
    unk = [n for n in allnodes if n not in set(ac_ground)]
    ix = {n: i for i, n in enumerate(unk)}
    nu, k = len(unk), len(pairs)
    s = 1j * omega
    a = np.zeros((nu + k, nu + k), dtype=complex)

    def two(p, q, y):
        for r_, c_, sg in ((p, p, 1.0), (q, q, 1.0), (p, q, -1.0), (q, p, -1.0)):
            if r_ in ix and c_ in ix:
                a[ix[r_], ix[c_]] += sg * y

    for p, q, r in res:
        two(p, q, 1.0 / r)
    for p, q, c in cap:
        two(p, q, s * c)
    for d, g, so, b, gm, gmb, gds in mos:
        for row, sg in ((d, 1.0), (so, -1.0)):
            if row not in ix:
                continue
            for col, v in ((g, gm), (b, gmb), (d, gds), (so, -(gm + gmb + gds))):
                if col in ix:
                    a[ix[row], ix[col]] += sg * v
    for j, (n, x) in enumerate(pairs):
        a[ix[n], nu + j] += 1.0          # 가지 전류 n -> x 가 n 에서 나간다
        a[ix[x], nu + j] -= 1.0
        a[nu + j, ix[n]] += 1.0          # v(n) − v(x) = Vlb
        a[nu + j, ix[x]] -= 1.0
    w = np.asarray(weights, dtype=float)
    rhs = np.zeros(nu + k, dtype=complex)
    rhs[nu:] = w
    sol = np.linalg.solve(a, rhs)
    vn = np.array([sol[ix[n]] for n, _ in pairs])
    vx = np.array([sol[ix[x]] for _, x in pairs])
    tv = -(w @ vx) / (w @ vn)
    rhs = np.zeros(nu + k, dtype=complex)
    for j, (n, _) in enumerate(pairs):
        rhs[ix[n]] += w[j]
    sol = np.linalg.solve(a, rhs)
    i_ = sol[nu:]
    ti = (w @ i_) / (w @ (w - i_))
    return dict(T=(tv * ti - 1.0) / (tv + ti + 2.0), Tv=tv, Ti=ti, pairs=pairs)


EX7 = dict(gm=1e-3, gds=1e-5, cl=1e-12, cf=1e-12, cs=3e-12, rs=1e5, rx=5e4)
EX7_CUT = (("capacitor", 1, "b"),)          # 예 7: Cf(capacitors index 1) 의 b 단자(노드 3 = 입력 포트)
EX7B_CUTS = (("capacitor", 1, "b"), ("capacitor", 4, "b"))


def ex7_parts(cs_resistor=False):
    """예 7 원소(test tuple): MOS(d=2,g=3), caps [CL(2,0), Cf(2,3), Cs(3,0)] -- Cf = capacitors index 1.
    cs_resistor=True 면 예 7c: Cs 대신 Resistor(3, 0, 1e5). 반환 (mos, res, cap)."""
    p = EX7
    mos = ((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),)
    if cs_resistor:
        return mos, ((3, 0, p["rs"]),), ((2, 0, p["cl"]), (2, 3, p["cf"]))
    return mos, (), ((2, 0, p["cl"]), (2, 3, p["cf"]), (3, 0, p["cs"]))


def ex7b_parts():
    """예 7b: 예 7 반회로 두 벌(a: 2·3, b: 12·13), Cf index 1·4, 출력 사이 Resistor(2, 12, 5e4)."""
    p = EX7
    mos = ((2, 3, 0, 0, p["gm"], 0.0, p["gds"]), (12, 13, 0, 0, p["gm"], 0.0, p["gds"]))
    cap = ((2, 0, p["cl"]), (2, 3, p["cf"]), (3, 0, p["cs"]), (12, 0, p["cl"]), (12, 13, p["cf"]), (13, 0, p["cs"]))
    return mos, ((2, 12, p["rx"]),), cap


def circuit_of(mos, res, cap, ac_ground=(0,), nm=None):
    """test tuple -> SmallSignalCircuit(노드 치환 nm 선택)."""
    m = mapper(nm)
    return SmallSignalCircuit(
        mos=tuple(MosSmallSignal(m(d), m(g), m(s), m(b), gm, gmb, gds) for d, g, s, b, gm, gmb, gds in mos),
        resistors=tuple(Resistor(m(a), m(b), v) for a, b, v in res),
        capacitors=tuple(Capacitor(m(a), m(b), v) for a, b, v in cap),
        ac_ground=tuple(m(n) for n in ac_ground),
    )


def closed_ex7():
    """예 7 폐형식 되돌림 비 T(s) = gm·Cf/(Cf+Cs) / (gds + s(CL + Cf·Cs/(Cf+Cs))). 반환 dict(t, t0, wp, ugf_hz, pm_deg, gain_db)."""
    p = EX7
    k = p["cf"] / (p["cf"] + p["cs"])
    ceq = p["cl"] + p["cf"] * p["cs"] / (p["cf"] + p["cs"])
    t0 = p["gm"] * k / p["gds"]
    wp = p["gds"] / ceq

    def t(w):
        return p["gm"] * k / (p["gds"] + 1j * w * ceq)

    return dict(t=t, t0=t0, wp=wp, ugf_hz=wp * math.sqrt(t0 * t0 - 1.0) / TWO_PI, gain_db=20.0 * math.log10(t0),
                pm_deg=180.0 - math.degrees(math.atan(math.sqrt(t0 * t0 - 1.0))))


def closed_ex7b(mode):
    """예 7b 반회로 폐형식: DM 출력 부하 gds + 2/Rx, CM 은 Rx 무전류(예 7 과 같음). 반환 dict(t0, wp, ugf_hz, pm_deg)."""
    p = EX7
    k = p["cf"] / (p["cf"] + p["cs"])
    ceq = p["cl"] + p["cf"] * p["cs"] / (p["cf"] + p["cs"])
    g = p["gds"] + (2.0 / p["rx"] if mode == "dm" else 0.0)
    t0 = p["gm"] * k / g
    wp = g / ceq
    return dict(t0=t0, wp=wp, ugf_hz=wp * math.sqrt(t0 * t0 - 1.0) / TWO_PI,
                pm_deg=180.0 - math.degrees(math.atan(math.sqrt(t0 * t0 - 1.0))))


# =====================================================================================================================
# 7절 (2단계 ss_linearize 배선) 공용 -- CONTRACT 7절·sizing CONTRACT 2절·lut CONTRACT r6·authoring SPEC_CONTRACT 만 근거.
# metrics 의 새 소스(ss_*.py·dc_metrics.py)는 열람하지 않았다. 입력은 공개 API(authoring 로더·graph build_s1·sizing lift_s1·
# GraphSnapshot.write)로 만들고, 기대값은 이 파일의 toy LUT 해석식·numpy 다중선형 보간·폐형식으로만 만든다.
# =====================================================================================================================

import json as _json
import hashlib as _hashlib
from pathlib import Path as _Path

SS_SRC = {"kind": "user_spec", "record": "ss test fixture", "decided": "2026-10-08"}
_PLAN = lambda pid: {"kind": "plan_rule", "plan_id": pid}          # noqa: E731
HAND = "hand_model"                                                  # 손 SsDevice 의 모형 표시(엔진 어휘 밖 -- 그대로 실려야 한다)


def topo_doc(name, mos=(), passives=(), sources=(), ports=None, rails=("gnd",)):
    """topology JSON dict. mos: (이름, kind, d, g, s, bulk), passives·sources: (이름, kind, a, b)."""
    ports = ports or {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}
    d = {"schema_version": "2.0", "topology_name": name,
         "netlist": [{"name": n, "kind": k, "drain": dd, "gate": g, "source": s, "bulk": b} for n, k, dd, g, s, b in mos],
         "supply_nets": list(rails),
         "ports": {k: {"direction": v[0], "role": v[1]} for k, v in ports.items()},
         "passive_elements": [{"name": n, "kind": k, "terminals": [a, b]} for n, k, a, b in passives]}
    if sources:
        d["ideal_sources"] = [{"name": n, "kind": k, "terminals": [a, b]} for n, k, a, b in sources]
    return d


def _value_key(kind):
    return {"capacitor": "value_farad", "resistor": "value_ohm", "current_source": "value_dc_amp",
            "voltage_source": "value_dc_v"}[kind]


def spec_json(td, supplies, elements, feedback=(), constraints=(), input_dc_v=None):
    """사이징 spec JSON dict(SPEC_CONTRACT 1절 형식). elements: (이름, kind, 값 | None(engine)).
    constraints: (metric, op, value, view | None) -- view 는 JSON 모양(None 이면 키 없음 = 유도 뷰)."""
    ev = {}
    for n, k, v in elements:
        ev[n] = {"engine": True, "source": SS_SRC} if v is None else {_value_key(k): v, "source": SS_SRC}
    cons = []
    for metric, op, value, view in constraints:
        c = {"metric": metric, "op": op, "value": value, "source": SS_SRC}
        if view is not None:
            c["view"] = view
        cons.append(c)
    indc = {"engine": True, "source": SS_SRC} if input_dc_v is None else {"value_v": input_dc_v, "source": SS_SRC}
    return {"meta": {"schema_version": "5", "circuit": td.name, "topology_fp": td.connectivity_fp, "origin": "fixture"},
            "human": {
                "supplies_v": {"values": dict(supplies), "source": SS_SRC},
                "input_dc": indc,
                "element_values": ev,
                "feedback": {"elements": list(feedback), "source": SS_SRC},
                "constraints": cons,
                "node_voltage_targets_v": {},
                "intended_region": {},
                "objective": {"budgets": {}},
                "search": {
                    "wall_clock_budget_s": {"value": 300, "source": _PLAN("DEC-34")},
                    "front_budget_s": {"value": 60, "source": _PLAN("DEC-34")},
                    "search_method": {"value": "default", "source": _PLAN("DEC-73")},
                    "optional_stages": {"value": {}, "source": _PLAN("DEC-75")},
                    "dof_rank_sample_count": {"value": 10, "source": _PLAN("N3.7")}},
                "spice_check": {k: {"rule": r, "source": SS_SRC} for k, r in (
                    ("acceptance_rule", "free_spec_and_all_saturated"), ("saturation_rule", "vds_ge_vdsat"),
                    ("node_compare_rule", "record_only"), ("device_compare_rule", "record_only"),
                    ("forced_warn_rule", "forced_device_diff_gt_lut_tolerance"), ("front_points_rule", "all_front_points"))},
                "front_refilter": {k: {"rule": r, "source": SS_SRC} for k, r in (
                    ("axis_rule", "layout_floorplan_outline"), ("tie_rule", "manufacturing_grid_cell_area"),
                    ("cycle_cap_rule", "k_max_n3_6"))}}}


def load_case(tmp_path, topo, supplies, elements=(), feedback=(), constraints=(), input_dc_v=None):
    """topology·spec 를 tmp 에 쓰고 authoring 로더로 읽는다(입력 생성용 공개 API). 반환 (TopologyDoc, SizingSpecDoc)."""
    from gmid_engine.authoring import load_sizing_spec, load_topology
    tmp_path = _Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    tp = tmp_path / (topo["topology_name"] + ".topology.json")
    tp.write_text(_json.dumps(topo, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    sp = tmp_path / (topo["topology_name"] + ".sizing_spec.json")
    sp.write_text(_json.dumps(spec_json(td, supplies, elements, feedback, constraints, input_dc_v), indent=1),
                  encoding="utf-8")
    from gmid_engine.metrics import metric_catalog
    return td, load_sizing_spec(str(sp), td, metric_catalog())


def topo_only(tmp_path, topo):
    from gmid_engine.authoring import load_topology
    tmp_path = _Path(tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    tp = tmp_path / (topo["topology_name"] + ".topology.json")
    tp.write_text(_json.dumps(topo, indent=1), encoding="utf-8")
    return load_topology(str(tp))


def s2_of(td, supplies):
    """S1 -> S2 스냅샷(sizing lift_s1, 권한표 S2_WRITERS)."""
    from gmid_engine.graph import build_s1
    from gmid_engine.sizing import lift_s1
    return lift_s1(build_s1(td, dict(supplies)))


def hand_ss(gm, gds, gmb=0.0, cgs=0.0, cgd=0.0, cgb=0.0, cdb=0.0, csb=0.0, cgg=0.0):
    from gmid_engine.metrics import SsDevice
    return SsDevice(gm, gmb, gds, cgg, cgs, cgd, cgb, cdb, csb, HAND, HAND, HAND)


def with_ss(snap, ss_map, version="hand_ss"):
    """손 S2: device.ss_dev 열을 권한표 writer(SS_DEV_WRITER = writer_of(device, ss_dev))로 쓴다."""
    from gmid_engine.sizing import S2_WRITERS
    w = S2_WRITERS.writer_of("device", "ss_dev")
    return snap.write(w, version, {("device", "ss_dev"): dict(ss_map)})


def hand_write(snap, kind, field, col, version="hand"):
    """손 S2 열 쓰기 -- writer = 권한표 writer_of(kind, field)."""
    from gmid_engine.sizing import S2_WRITERS
    return snap.write(S2_WRITERS.writer_of(kind, field), version, {(kind, field): dict(col)})


def requests_of(spec, metrics=None):
    """spec 제약 -> MetricRequest(metric, view) (문서 순서, metrics 로 거르기)."""
    from gmid_engine.metrics import MetricRequest
    return tuple(MetricRequest(c.metric, c.view) for c in spec.constraints
                 if c.metric is not None and (metrics is None or c.metric in metrics))


def bundle_map(bundle):
    """MetricBundle -> {metric: MetricResult} (같은 metric 두 번이면 마지막)."""
    return {req.metric: res for req, res in bundle.entries}


# ---------------------------------------------------------------- 예 7 을 topology 로 (S-1·S-2·S-3·S-4·S-5·S-8)

EX7_NAMES = {"out": "out", "in": "in", "gnd": "gnd"}


def ex7_topology(names=None, cs_resistor=False):
    """예 7: M1 nmos (d=out, g=in, s=gnd, b=gnd), CL(out, gnd), Cf(out, in), Cs(in, gnd). 입력 포트 = in, 출력 = out.
    names: 넷 이름 전단사(S-8). cs_resistor: 예 7c(Cs 대신 저항 Rs)."""
    n = dict(EX7_NAMES if names is None else names)
    o, i, g = n["out"], n["in"], n["gnd"]
    pas = [("CL", "capacitor", o, g), ("Cf", "capacitor", o, i)]
    pas.append(("Rs", "resistor", i, g) if cs_resistor else ("Cs", "capacitor", i, g))
    return topo_doc("ex7_" + "_".join(sorted(n.values())) + ("_r" if cs_resistor else ""),
                    mos=[("M1", "nmos", o, i, g, g)], passives=pas,
                    ports={i: ("input", "single_ended_input"), o: ("output", "single_ended_output")}, rails=(g,))


def ex7_passives(cs_resistor=False, drop=()):
    p = EX7
    vals = [("CL", p["cl"]), ("Cf", p["cf"]), ("Rs", p["rs"]) if cs_resistor else ("Cs", p["cs"])]
    return tuple(sorted((k, v) for k, v in vals if k not in drop))


def ex7_ss():
    return {"M1": hand_ss(EX7["gm"], EX7["gds"])}


def ex7_case(tmp_path, constraints, feedback=("Cf",), names=None, cs_resistor=False, ss=None):
    """(TopologyDoc, spec, 손 S2 스냅샷). 원소 값은 spec 에 쓰지만 metrics_ss 에는 passive_values 인자로 넘긴다(7.4)."""
    n = dict(EX7_NAMES if names is None else names)
    topo = ex7_topology(n, cs_resistor)
    kinds = {e["name"]: e["kind"] for e in topo["passive_elements"]}
    els = tuple((k, kinds[k], v) for k, v in ex7_passives(cs_resistor))
    td, spec = load_case(tmp_path, topo, {n["gnd"]: 0.0}, els, feedback, constraints, input_dc_v=0.0)
    return td, spec, with_ss(s2_of(td, {n["gnd"]: 0.0}), ex7_ss() if ss is None else ss)


def ex7_port_closed():
    """예 7 소자의 포트 전달 뷰(입력 in 1 V 구동, 관측 out): H(s) = −(gm − sCf)/(gds + s(CL + Cf)) -- Cs 는 고정 넷 사이.
    반환 dict(h, gain_db, ugf_hz, pm_deg, gbw_hz) -- 교차는 brentq(폐형식 |H|), 위상 지연 = atan(ωCf/gm) + atan(ω(CL+Cf)/gds)."""
    p = EX7
    cp = p["cl"] + p["cf"]

    def h(w):
        return -(p["gm"] - 1j * w * p["cf"]) / (p["gds"] + 1j * w * cp)

    a0 = p["gm"] / p["gds"]
    wu = brentq(lambda w: abs(h(w)) - 1.0, 1.0, 1e12, xtol=1e-6, rtol=1e-15)
    w3 = brentq(lambda w: abs(h(w)) - a0 / math.sqrt(2.0), 1.0, 1e12, xtol=1e-9, rtol=1e-15)
    lag = math.atan(wu * p["cf"] / p["gm"]) + math.atan(wu * cp / p["gds"])
    return dict(h=h, gain_db=20.0 * math.log10(a0), ugf_hz=wu / TWO_PI, pm_deg=180.0 - math.degrees(lag),
                gbw_hz=a0 * w3 / TWO_PI)


# ---------------------------------------------------------------- toy LUT r6 (GMBS·CGS·CGB 열 선택)

LUT_GRID = 1e-8
LUT_WM = 1e-6                      # 슬라이스 폭 -> w_key 100
LUT_WKEY = 100
LUT_L = (1e-6, 2e-6)
LUT_VGS = tuple(round(0.1 * i, 10) for i in range(19))
LUT_VDS = tuple(round(0.3 * i, 10) for i in range(7))
LUT_VS = (-0.45, 0.0, 0.45, 0.9, 1.35, 1.8)
LUT_I0 = {"nmos": 1e-11, "pmos": 5e-12}
LUT_B, LUT_C, LUT_LAM, LUT_A = 20.0, 8.0, 0.1, 2.0
LUT_KSCALE = {"nmos": 1.0, "pmos": 1.5}         # 용량 kind 배율(두 kind 값이 섞이면 드러나게)
GMBS_COEF = {"slice": (0.2, -0.05), "cap": (0.3, -0.04)}   # GMBS/ID = c0 + c1·VS (열 출처마다 다르게)
LUT_SPEC_ARGS = (LUT_GRID, (("nmos", 1e-6), ("pmos", 1e-6)), (("toyn", "nmos"), ("toyp", "pmos")),
                 (("nmos", "_n"), ("pmos", "_p")))
LUT_WKEYS = (("nmos", LUT_WKEY), ("pmos", LUT_WKEY))


def _mesh(L, VGS, VDS, VS):
    return (np.asarray(L)[:, None, None, None], np.asarray(VGS)[None, :, None, None],
            np.asarray(VDS)[None, None, :, None], np.asarray(VS)[None, None, None, :])


def lut_id(kind, L, VGS, VDS, VS, w=LUT_WM):
    Lg, G, D, S = _mesh(L, VGS, VDS, VS)
    return (w / Lg) * LUT_I0[kind] * np.exp(LUT_B * G - 0.5 * LUT_C * G * G + LUT_LAM * D - LUT_A * S * S)


def lut_cap_cols(kind, L, VGS, VDS, VS):
    """기준 LUT 용량 열(모든 축 1차 -> 선형 보간이 정확). CGB 는 음수(부호 보존 확인용), CGS 도 VS 가 크면 작아진다."""
    Lg, G, D, S = _mesh(L, VGS, VDS, VS)
    k = LUT_KSCALE[kind]
    one = np.ones(np.broadcast_shapes(Lg.shape, G.shape, D.shape, S.shape))
    return {
        "CGG": k * (1e-15 * (Lg / 1e-6) + 1e-16 * G) * one,
        "CGD": k * (2e-16 + 1e-17 * D) * one,
        "CGS": k * (6e-16 + 2e-16 * G - 1e-17 * S) * one,
        "CGB": k * (-5e-17 + 1e-17 * G - 2e-17 * D) * one,
    }


def lut_cap_closed(kind, L, vgs, vds, vsb):
    """lut_cap_cols 의 점 값(폭 w_ref 기준)."""
    k = LUT_KSCALE[kind]
    return {"CGG": k * (1e-15 * (L / 1e-6) + 1e-16 * vgs), "CGD": k * (2e-16 + 1e-17 * vds),
            "CGS": k * (6e-16 + 2e-16 * vgs - 1e-17 * vsb), "CGB": k * (-5e-17 + 1e-17 * vgs - 2e-17 * vds)}


def _sha_of(path):
    return _hashlib.sha256(_Path(path).read_bytes()).hexdigest()


def write_lut_v2(root, slice_gmbs=True, cap_cgs_cgb=True, cap_gmbs=False, cap_vs=LUT_VS, temp_c=27.0):
    """toy LUT(npz 직접 작성). slice_gmbs: 슬라이스 GMBS 열. cap_cgs_cgb: 기준 LUT CGS·CGB 열. cap_gmbs: 기준 LUT GMBS·ID 열.
    cap_vs: 기준 LUT VS 축(슬라이스와 달라도 됨, lut 1.4). temp_c: 측정 온도(슬라이스·기준 LUT 같은 값, None 이면 기록 안 함)."""
    root = _Path(root)
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for kind, dev in (("nmos", "toyn"), ("pmos", "toyp")):
        ID = lut_id(kind, LUT_L, LUT_VGS, LUT_VDS, LUT_VS)
        G = np.asarray(LUT_VGS)[None, :, None, None]
        S = np.asarray(LUT_VS)[None, None, None, :]
        a = {"W": np.float64(LUT_WM), "L": np.asarray(LUT_L), "VGS": np.asarray(LUT_VGS), "VDS": np.asarray(LUT_VDS),
             "VS": np.asarray(LUT_VS), "ID": ID, "GM": ID * (LUT_B - LUT_C * G), "GDS": ID * LUT_LAM,
             "VTH": np.full(ID.shape, 0.4), "meta_json": np.str_('{"model_files_sha256": {}}'),
             "corner": np.str_("tt")}
        if temp_c is not None:
            a["temp_c"] = np.float64(temp_c)
        if slice_gmbs:
            c0, c1 = GMBS_COEF["slice"]
            a["GMBS"] = ID * (c0 + c1 * S)
        p = root / ("toy_%s.npz" % kind)
        np.savez(p, **a)
        entries.append({"device": dev, "file": p.name, "sha256": _sha_of(p)})
    (root / "manifest.json").write_text(_json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    cap = {"L": np.asarray(LUT_L), "VGS": np.asarray(LUT_VGS), "VDS": np.asarray(LUT_VDS), "VS": np.asarray(cap_vs),
           "w_ref_m": np.float64(LUT_WM), "corner": np.str_("tt")}
    if temp_c is not None:
        cap["temp_c"] = np.float64(temp_c)
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        cols = lut_cap_cols(kind, LUT_L, LUT_VGS, LUT_VDS, cap_vs)
        cap["CGG" + suf] = cols["CGG"]
        cap["CGD" + suf] = cols["CGD"]
        if cap_cgs_cgb:
            cap["CGS" + suf] = cols["CGS"]
            cap["CGB" + suf] = cols["CGB"]
        if cap_gmbs:
            idc = lut_id(kind, LUT_L, LUT_VGS, LUT_VDS, cap_vs)
            c0, c1 = GMBS_COEF["cap"]
            cap["ID" + suf] = idc
            cap["GMBS" + suf] = idc * (c0 + c1 * np.asarray(cap_vs)[None, None, None, :])
    np.savez(root / "cap.npz", **cap)
    return root / "manifest.json", root / "cap.npz"


def load_lut_v2(root, **kw):
    from gmid_engine.lut import LutSpec, load_lut_set
    m, c = write_lut_v2(root, **kw)
    return load_lut_set(str(m), str(c), LutSpec(*LUT_SPEC_ARGS))


def lut_access(lut, n=4096):
    from gmid_engine.lut import LutMemo
    from gmid_engine.sizing import LutAccess
    return LutAccess(LutMemo(lut, point=n, curve=n, root=n), LUT_WKEYS)


def _cell(grid, x):
    """lut 4.2 칸 규칙(독립 구현): i = min(max(bisect_right − 1, 0), n − 2), t = (x − g_i)/(g_{i+1} − g_i)."""
    import bisect as _b
    g = list(grid)
    i = min(max(_b.bisect_right(g, x) - 1, 0), len(g) - 2)
    return i, (x - g[i]) / (g[i + 1] - g[i])


def multilinear(grids, arr, point):
    """4축 다중선형 보간(독립 numpy). L 이 격자점이면 그 장만 쓴다."""
    cells = [_cell(g, x) for g, x in zip(grids, point)]
    tot = 0.0
    for corner in range(16):
        w = 1.0
        idx = []
        for ax, (i, t) in enumerate(cells):
            hi = (corner >> ax) & 1
            wt = t if hi else 1.0 - t
            if wt == 0.0:
                w = 0.0
                break
            w *= wt
            idx.append(i + hi)
        if w:
            tot += w * float(arr[tuple(idx)])
    return tot


def lut_vs_term(vsb):
    """ln ID 의 VS 항 = 격자 위 −A·VS² 의 구간 선형(VS 축 선형 보간)."""
    i, t = _cell(LUT_VS, vsb)
    y0, y1 = -LUT_A * LUT_VS[i] ** 2, -LUT_A * LUT_VS[i + 1] ** 2
    return y0 + t * (y1 - y0)


def lut_ln_idu(kind, vgs, vds, vsb):
    """IDu = ID·L/w_m 의 로그(L 무관). VGS 2차·VDS 1차는 저장 기울기 Hermite 가 정확히 재현한다(lut 4.2)."""
    return math.log(LUT_I0[kind]) + LUT_B * vgs - 0.5 * LUT_C * vgs * vgs + LUT_LAM * vds + lut_vs_term(vsb)


def oracle_ss(op, gmb_source="slice", cap_model="lut_cgs_cgb"):
    """7.2 식의 독립 계산(npz 해석식 + numpy 보간). op = DeviceOp(손 값). 반환 dict.
    gmb_source: "slice"/"cap" = GMBS 열(GMBS/ID 선형 보간 × ID(점)), "secant" = r5 VS 칸 할선."""
    grids = (LUT_L, LUT_VGS, LUT_VDS, LUT_VS)
    pt = (op.L, op.vgs, op.vds, op.vsb)
    gds_arr = np.log(lut_id(op.kind, *grids) * LUT_LAM)
    gds = math.exp(multilinear(grids, gds_arr, pt)) / LUT_WM * op.W
    id_pt = math.exp(lut_ln_idu(op.kind, op.vgs, op.vds, op.vsb)) * LUT_WM / op.L
    if gmb_source == "secant":
        k, _ = _cell(LUT_VS, op.vsb)
        slope = (-LUT_A * LUT_VS[k + 1] ** 2 + LUT_A * LUT_VS[k] ** 2) / (LUT_VS[k + 1] - LUT_VS[k])
        gmb_w = -id_pt * slope
    else:
        c0, c1 = GMBS_COEF[gmb_source]
        gmb_w = id_pt * (c0 + c1 * op.vsb)
    caps = lut_cap_closed(op.kind, op.L, op.vgs, op.vds, op.vsb)
    sc = op.W / LUT_WM
    cgg, cgd = caps["CGG"] * sc, caps["CGD"] * sc
    if cap_model == "lut_cgs_cgb":
        cgs, cgb = caps["CGS"] * sc, caps["CGB"] * sc
    else:
        cgs, cgb = cgg - cgd, 0.0
    # 접합 용량 cdb·csb 는 LUT 가 아니라 PDK 선언에서 온다(DEC-91) -- oracle_junction 이 따로 계산한다.
    return dict(gm=op.gm_id * op.current, gds=gds, gmb=gmb_w * op.W / LUT_WM, cgg=cgg, cgd=cgd, cgs=cgs, cgb=cgb)


def device_op(kind, L, vgs, vds, vsb, W, current=1e-5, gm_id=12.0):
    """손 DeviceOp(ss_dev 가 읽는 칸만 의미가 있다 -- ln_idu·idu_forward 는 해석식 값으로 채운다)."""
    from gmid_engine.sizing import DeviceOp
    ln = lut_ln_idu(kind, vgs, vds, vsb)
    return DeviceOp(kind, current, ln, gm_id, L, W, vgs, vds, vsb, LUT_WKEY, math.exp(ln))


# ---------------------------------------------------------------- 접합 용량 독립 기준 식 (CONTRACT 8.2) + toy 선언

JUNCTION_FIELDS = ("cjs", "cjd", "cjsws", "cjswd", "cjswgs", "cjswgd", "mjs", "mjd", "mjsws", "mjswd", "mjswgs", "mjswgd",
                   "pbs", "pbd", "pbsws", "pbswd", "pbswgs", "pbswgd", "tcj", "tcjsw", "tcjswg", "tpb", "tpbsw", "tpbswg",
                   "tnom", "permod", "dwj")


def _ref_junction_side(p, fw, area, perim, v, temp_c, s):
    """한 쪽(s = "s" source / "d" drain)의 finger 하나 용량 -- 8.2-2..5 (피검 함수와 독립 구현)."""
    dT = temp_c - p["tnom"]
    wc = fw - 2 * p["dwj"]
    p_eff = perim - wc if p["permod"] == 1 else perim
    total = 0.0
    for c, tc, mj, pb, tp, g in (
        (p["cj" + s], p["tcj"], p["mj" + s], p["pb" + s], p["tpb"], area),
        (p["cjsw" + s], p["tcjsw"], p["mjsw" + s], p["pbsw" + s], p["tpbsw"], p_eff),
        (p["cjswg" + s], p["tcjswg"], p["mjswg" + s], p["pbswg" + s], p["tpbswg"], wc),
    ):
        c0 = c * max(0.0, 1.0 + tc * dT) * g
        pbt = pb - tp * dT
        assert pbt > 0 and wc > 0
        if v > 0:
            total += c0 * (1.0 + v / pbt) ** (-mj) if c0 > 0 else 0.0
        else:
            total += c0 * (1.0 - mj * v / pbt)
    return total


def ref_caps(p, geo, v_db, v_sb, temp_c):
    """8.2 독립 기준 식. p = {필드: 값}, geo = (finger_w, ad, as, pd, ps, m) -> (cdb, csb)."""
    fw, ad, as_, pd, ps, m = geo
    return (m * _ref_junction_side(p, fw, ad, pd, v_db, temp_c, "d"),
            m * _ref_junction_side(p, fw, as_, ps, v_sb, temp_c, "s"))


# toy 모델 카드 접합 파라미터(kind 마다·drain/source 쪽마다 다른 값 -- 섞이면 드러나게). 값은 단위 글자 없는 repr 로 카드에
# 쓰므로(units_m {"": 1.0}) 선언 값 = 이 float 그대로.
TOY_JUNCTION = {
    "nmos": dict(cjs=1.1e-3, cjd=0.9e-3, cjsws=1.2e-10, cjswd=0.8e-10, cjswgs=2.5e-10, cjswgd=1.5e-10,
                 mjs=0.45, mjd=0.35, mjsws=0.2, mjswd=0.3, mjswgs=0.7, mjswgd=0.6,
                 pbs=0.8, pbd=0.7, pbsws=0.9, pbswd=0.6, pbswgs=1.1, pbswgd=1.2,
                 tcj=1e-3, tcjsw=2e-4, tcjswg=3e-4, tpb=1e-3, tpbsw=2e-3, tpbswg=5e-4,
                 tnom=25.0, permod=1.0, dwj=2e-8),
    "pmos": dict(cjs=0.7e-3, cjd=0.6e-3, cjsws=1.0e-10, cjswd=0.9e-10, cjswgs=2.2e-10, cjswgd=2.0e-10,
                 mjs=0.35, mjd=0.4, mjsws=0.3, mjswd=0.25, mjswgs=0.9, mjswgd=0.8,
                 pbs=0.66, pbd=0.75, pbsws=0.74, pbswd=0.7, pbswgs=1.4, pbswgd=1.3,
                 tcj=1.2e-3, tcjsw=3.7e-4, tcjswg=0.0, tpb=2e-3, tpbsw=1.2e-3, tpbswg=0.0,
                 tnom=30.0, permod=1.0, dwj=1e-8),
}
# toy LUT 생성 규칙 DUT 줄(ad ≠ as, pd ≠ ps -- 쪽이 바뀌면 드러나게). SI 값 그대로(단위 글자 없음).
TOY_RULE_LINE = "xdut d g s b dev l=1e-6 w=4e-6 ad=2e-12 as=1.2e-12 pd=9e-6 ps=7e-6"


def toy_rule_values(rule_line=TOY_RULE_LINE):
    """규칙 DUT 줄에서 4개 양을 식(ad / w, as / w, pd − w, ps − w) 그대로 따로 계산."""
    kv = dict(t.split("=") for t in rule_line.split() if "=" in t)
    w, ad, as_, pd, ps = (float(kv[k]) for k in ("w", "ad", "as", "pd", "ps"))
    return dict(ad_per_w=ad / w, as_per_w=as_ / w, pd_extra=pd - w, ps_extra=ps - w)


def _write_sha(path, data):
    path.write_bytes(data)
    return _hashlib.sha256(data).hexdigest()


def toy_junction_decls(root, params=None, rule_line=TOY_RULE_LINE, kinds=("nmos", "pmos")):
    """toy PDK 선언(kind 마다 모델 카드 원본 하나, 27개 양 `junction_<kind>_<필드>`) + toy LUT 규칙 선언(core 9.1 형식).
    반환 (pdk 선언 경로, 규칙 선언 경로)."""
    root = _Path(root)
    (root / "m").mkdir(parents=True, exist_ok=True)
    params = TOY_JUNCTION if params is None else params
    sources, quantities = {}, {}
    for kind in kinds:
        body = "\n".join("+ %s = %r" % (f, float(params[kind][f])) for f in JUNCTION_FIELDS)
        text = ("* toy %s card\n.model tj_%s.0 %s level = 54 vth0 = 0.3\n%s\n.model tj_%s.1 %s level = 54 vth0 = 0.4\n%s\n"
                % (kind, kind, kind, body, kind, kind, body))
        sha = _write_sha(root / "m" / ("%s.spice" % kind), text.encode("utf-8"))
        sources["card_" + kind] = {"path": "m/%s.spice" % kind, "sha256": sha, "format": "spice_model_card",
                                   "encoding": "utf-8", "model_pattern": r"tj_%s\.[0-9]+" % kind, "units_m": {"": 1.0}}
        for f in JUNCTION_FIELDS:
            quantities["junction_%s_%s" % (kind, f)] = {"source": "card_" + kind, "expression": f, "basis": "toy"}
    pdk = {"schema": "gmid_pdk_decl/1", "pdk": "toyjw", "pdk_root": root.as_posix(), "sources": sources,
           "quantities": quantities}
    gsha = _write_sha(root / "gen.py", ('DUT_LINE = "%s"\n' % rule_line).encode("utf-8"))
    rule = {"schema": "gmid_pdk_decl/1", "pdk": "toyjw", "pdk_root": "unused",
            "sources": {"gen": {"path": "gen.py", "base": "decl_dir", "newline": "lf", "sha256": gsha,
                                "format": "spice_instance_line", "encoding": "utf-8",
                                "line_pattern": r'^DUT_LINE\s*=\s*"([^"]*)"', "units_m": {"": 1.0}}},
            "quantities": {"lut_diffusion_ad_per_w_m": {"source": "gen", "expression": "ad / w", "basis": "t"},
                           "lut_diffusion_as_per_w_m": {"source": "gen", "expression": "as / w", "basis": "t"},
                           "lut_diffusion_pd_extra_m": {"source": "gen", "expression": "pd - w", "basis": "t"},
                           "lut_diffusion_ps_extra_m": {"source": "gen", "expression": "ps - w", "basis": "t"}}}
    pp, rp = root / "pdk.json", root / "rule.json"
    pp.write_bytes(_json.dumps(pdk).encode("utf-8"))
    rp.write_bytes(_json.dumps(rule).encode("utf-8"))
    return str(pp), str(rp)


def read_decls(pdk_path, rule_path):
    from gmid_engine.core import BoundedLRU, read_pdk_decl
    memo = BoundedLRU(8)
    return read_pdk_decl(pdk_path, memo), read_pdk_decl(rule_path, memo)


def toy_junction(root, lut, **kw):
    """8.5 소비자 호출 그대로: JunctionSource.from_decls(PDK 선언, 규칙 선언, LUT 세트)."""
    from gmid_engine.metrics import JunctionSource
    return JunctionSource.from_decls(*read_decls(*toy_junction_decls(root, **kw)), lut)


def oracle_junction(op, params=None, temp_c=27.0, rule=None, w_m=LUT_WM):
    """7.2 접합 항의 독립 계산: 기하 = LUT 규칙(finger_w = w_m, m = W / w_m), v_db = vds + vsb, v_sb = vsb."""
    p = (TOY_JUNCTION if params is None else params)[op.kind]
    r = toy_rule_values() if rule is None else rule
    geo = (w_m, r["ad_per_w"] * w_m, r["as_per_w"] * w_m, w_m + r["pd_extra"], w_m + r["ps_extra"], op.W / w_m)
    return ref_caps(p, geo, op.vds + op.vsb, op.vsb, temp_c)


# 독립 기준 식과 엔진의 차이 허용: 둘 다 같은 식을 연산 순서만 다르게 푼다 -- 쪽마다 항 3개 x (곱·합·나눗셈·거듭제곱)
# 약 10회 반올림, 최종 m 곱·합 포함 약 40회 x eps(2.2e-16) = 9e-15. 거듭제곱 지수 곱의 오차 증폭(|mj| ≤ 1)을 넣어 10 배 여유.
JUNCTION_RTOL = 40 * 2.220446049250313e-16 * 10


# =====================================================================================================================
# 9절 (metric 분해능) 공용 -- CONTRACT 9절만 근거. metrics 의 새 소스(lut_parameters·sensitivity·resolution·_helpers_dc)와
# 바뀐 소스는 열람하지 않았다. 기대값 = 9.5 폐형식(test 쪽 재계산) + 아래 독립 MNA 의 중심 차분(파라미터마다 다시 세워 푼다).
# =====================================================================================================================

EPS = float(np.finfo(float).eps)
LUT_P = ("gm", "gmb", "gds", "cgs", "cgd", "cgb")      # 9.1 LUT_PARAMETERS (계약 문자열의 test 쪽 사본)
MOS_IX = {"gm": 4, "gmb": 5, "gds": 6, "cgs": 7, "cgd": 8, "cgb": 9, "cdb": 10, "csb": 11}   # mos_t tuple 위치
DB_PER_NEPER = 20.0 / math.log(10.0)                     # 9.3 D = 20·log10(e)
FD_H = 1e-6                                              # R-2 의 상대 차분 폭
FD_RTOL = 1e-6                                           # R-2 의 허용 상대 차


def circuit12(mos, res=(), cap=(), ac_ground=(0,), nm=None):
    """mos_t 12-tuple(용량 포함) -> SmallSignalCircuit(노드 치환 nm 선택)."""
    m = mapper(nm)
    return SmallSignalCircuit(
        mos=tuple(MosSmallSignal(m(t[0]), m(t[1]), m(t[2]), m(t[3]), *t[4:]) for t in mos),
        resistors=tuple(Resistor(m(a), m(b), v) for a, b, v in res),
        capacitors=tuple(Capacitor(m(a), m(b), v) for a, b, v in cap),
        ac_ground=tuple(m(n) for n in ac_ground),
    )


def columns_of(excitations):
    """Excitation 레코드 -> 독립 풀이용 열 dict(입력 레코드 읽기만)."""
    return tuple({"v": dict(e.voltages), "i": dict(e.currents), "q": dict(e.charges)} for e in excitations)


def senses_of(senses):
    return tuple((s.pos, s.neg) for s in senses)


def ref_system(mos=(), res=(), cap=(), ac_ground=(0,), columns=(), senses=(), omega=1.0):
    """독립 MNA(여러 열·여러 관측). mos: mos_t 12-tuple, res/cap: (a, b, 값 -- 음수 용량 허용), columns: ({"v","i","q"}, ...),
    senses: ((pos, neg | None), ...). 반환 (r, m) 복소 배열.
    - 고정 노드 = ac_ground ∪ 모든 열의 전압 구동 노드(열에 없는 구동 노드는 0 V -- CONTRACT 1절).
    - ω > 0: (G + jωC)x = I + jω·Q.
    - ω = 0: 전하 보존 극한(3.3) -- 전체 G 행이 0 인 미지수 노드 행은 C 행·x = Q, 나머지는 G 행·x = I. 그 노드에 I ≠ 0 인 열은 NaN.
    풀기 전 행마다 최대 크기로 나눈다(해 불변 -- 용량 전용 행과 컨덕턴스 행의 크기 차를 없앤다)."""
    nodes = set(ac_ground)
    for col in columns:
        nodes |= set(col["v"]) | set(col["i"]) | set(col["q"])
    for p, n in senses:
        nodes |= {p} | ({n} if n is not None else set())
    for t in tuple(res) + tuple(cap):
        nodes |= {t[0], t[1]}
    for t in mos:
        nodes |= set(t[:4])
    nodes = sorted(nodes)
    ix = {n: i for i, n in enumerate(nodes)}
    N = len(nodes)
    G = np.zeros((N, N))
    C = np.zeros((N, N))

    def two(M, a, b, y):
        M[ix[a], ix[a]] += y
        M[ix[b], ix[b]] += y
        M[ix[a], ix[b]] -= y
        M[ix[b], ix[a]] -= y

    for a, b, r in res:
        two(G, a, b, 1.0 / r)
    for a, b, c in cap:
        two(C, a, b, c)
    for d, g, so, b, gm, gmb, gds, cgs, cgd, cgb, cdb, csb in mos:
        for row, sg in ((d, 1.0), (so, -1.0)):
            r_ = ix[row]
            G[r_, ix[g]] += sg * gm
            G[r_, ix[b]] += sg * gmb
            G[r_, ix[d]] += sg * gds
            G[r_, ix[so]] -= sg * (gm + gmb + gds)
        for a, bb, c in ((g, so, cgs), (g, d, cgd), (g, b, cgb), (d, b, cdb), (so, b, csb)):
            if c:
                two(C, a, bb, c)
    fixed = set(ac_ground)
    for col in columns:
        fixed |= set(col["v"])
    fi = [ix[n] for n in nodes if n in fixed]
    unk = [n for n in nodes if n not in fixed]
    ui = [ix[n] for n in unk]
    charge = [n for n in unk if not np.any(G[ix[n], :])]
    out = np.zeros((len(senses), len(columns)), dtype=complex)
    for j, col in enumerate(columns):
        xf = np.array([col["v"].get(n, 0.0) for n in nodes if n in fixed], dtype=complex)
        if omega > 0.0:
            Y = G + 1j * omega * C
            A = Y[np.ix_(ui, ui)]
            rhs = np.array([col["i"].get(n, 0.0) + 1j * omega * col["q"].get(n, 0.0) for n in unk]) - Y[np.ix_(ui, fi)] @ xf
        else:
            if any(col["i"].get(n, 0.0) != 0.0 for n in charge):
                out[:, j] = np.nan
                continue
            A = np.zeros((len(ui), len(ui)), dtype=complex)
            rhs = np.zeros(len(ui), dtype=complex)
            for k, n in enumerate(unk):
                M, src = (C, col["q"]) if n in charge else (G, col["i"])
                A[k] = M[ix[n], ui]
                rhs[k] = src.get(n, 0.0) - M[ix[n], fi] @ xf
        scale = np.max(np.abs(A), axis=1)
        x = np.linalg.solve(A / scale[:, None], rhs / scale)
        full = {n: v for n, v in zip([n for n in nodes if n in fixed], xf)}
        full.update(zip(unk, x))
        for r, (p, n) in enumerate(senses):
            out[r, j] = full[p] - (full[n] if n is not None else 0.0)
    return out


def perturbed(mos, k, name, factor):
    """mos_t tuple 들 중 k 번째 MOS 의 파라미터 name 만 factor 배."""
    out = [list(t) for t in mos]
    out[k][MOS_IX[name]] *= factor
    return tuple(tuple(t) for t in out)


def central_diff(mos, k, name, fn, h=FD_H):
    """∂fn/∂p ≈ (fn(p(1+h)) − fn(p(1−h)))/(p+ − p−) -- 실제 부동소수 폭으로 나눈다."""
    p = mos[k][MOS_IX[name]]
    pp, pm = p * (1.0 + h), p * (1.0 - h)
    return (fn(perturbed(mos, k, name, 1.0 + h)) - fn(perturbed(mos, k, name, 1.0 - h))) / (pp - pm)


def lut_params_of(mos):
    """9.1: (MOS 순번, 이름) -- 값 ≠ 0 인 LUT 파라미터만, (MOS 순번, LUT_P 순서)."""
    return tuple((k, nm) for k, t in enumerate(mos) for nm in LUT_P if t[MOS_IX[nm]] != 0.0)


# ---------------------------------------------------------------- 9절 변형 회로 (음의 용량·Miller·gmb)

# 예 3 Miller + source 축퇴(Rs: gmb 가 의미 있게) + 두 MOS 의 cgs·cgd·음의 cgb·접합(cdb·csb -- LUT 파라미터 아님)
MILLER_V_MOS = (
    mos_t(2, 1, 4, 0, 1e-4, 2e-5, 1e-6, cgs=20e-15, cgd=5e-15, cgb=-3e-15, cdb=2e-15, csb=1e-15),
    mos_t(3, 2, 0, 0, 1e-3, 1e-4, 1e-5, cgs=50e-15, cgd=10e-15, cgb=-5e-15, cdb=4e-15, csb=0.0),
)
MILLER_V_RES = ((4, 0, 1e3),)
MILLER_V_CAP = ((2, 0, 0.1e-12), (3, 0, 1e-12), (2, 3, 0.5e-12))
MILLER_V_COLS = ({"v": {1: 1.0}, "i": {}, "q": {}},)
MILLER_V_SENSE = ((3, None),)


def miller_v_system(mos=MILLER_V_MOS, nm=None):
    m = mapper(nm)
    ck = circuit12(mos, MILLER_V_RES, MILLER_V_CAP, (0,), nm)
    return ck, build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), (Sense(m(3)),))


# 예 7 + gmb·cgs·cgd·음의 cgb·cdb(절단 전 원래 회로, Cf = capacitors index 1)
EX7V_MOS = (mos_t(2, 3, 0, 0, 1e-3, 1e-4, 1e-5, cgs=0.3e-12, cgd=0.2e-12, cgb=-0.1e-12, cdb=0.05e-12),)
EX7V_CAP = ((2, 0, 1e-12), (2, 3, 1e-12), (3, 0, 3e-12))
EX7_MOS12 = (mos_t(2, 3, 0, 0, 1e-3, 0.0, 1e-5),)
EX7_CAP = ((2, 0, 1e-12), (2, 3, 1e-12), (3, 0, 3e-12))


# =====================================================================================================================
# 예 8·8a·8b -- PM 전제(CONTRACT 3.10 'PM 전제', 2절 `loop_open_rhp_poles`, I-17). 교차 결합 쌍(M2·M3)이 개루프 T 에 우반면 극점을
# 만든다. 기대값은 아래 폐형식(노드 방정식을 손으로 소거한 2차식의 근)뿐이고, 폐형식 자체는 test 에서 독립 MNA(`ref_solve`)·독립
# Middlebrook(`ref_middlebrook`)과 대조한다. 엔진 소스(loop_analysis.py)는 열람하지 않았다.
# =====================================================================================================================

EX8 = dict(gm=1e-3, gds=1e-5, c=1e-12, gx2=1.2e-9, gx2_8b=5.2e-9)


def ex8_parts(gx2=EX8["gx2"]):
    """예 8 test tuple: M1(d=2, g=1), 교차 결합 M2(d=2, g=5, gm=gx)·M3(d=5, g=2, gm=gx), C(2,0)·C(5,0), gx = √gx2."""
    p = EX8
    gx = math.sqrt(gx2)
    mos = ((2, 1, 0, 0, p["gm"], 0.0, p["gds"]), (2, 5, 0, 0, gx, 0.0, p["gds"]), (5, 2, 0, 0, gx, 0.0, p["gds"]))
    return mos, (), ((2, 0, p["c"]), (5, 0, p["c"]))


def ex8_system(nm=None, gx2=EX8["gx2"]):
    """예 8 계: 열 1 V at 1, Sense(2). 반환 (SmallSignalCircuit, MnaSystem)."""
    m = mapper(nm)
    ck = circuit_of(*ex8_parts(gx2), nm=nm)
    return ck, build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), (Sense(m(2)),))


def ex8a_parts(gx2=EX8["gx2"]):
    """예 8a(gx2 1.2e-9)·8b(gx2 5.2e-9): 예 7 회로(Cf = capacitors index 1 유지) + 노드 2 에 예 8 의 교차 결합 쌍·노드 5 용량."""
    p = EX8
    gx = math.sqrt(gx2)
    mos, res, cap = ex7_parts()
    mos = mos + ((2, 5, 0, 0, gx, 0.0, p["gds"]), (5, 2, 0, 0, gx, 0.0, p["gds"]))
    return mos, res, cap + ((5, 0, p["c"]),)


def quad_roots(a, b, c):
    """a s² + b s + c = 0 의 두 실근(판별식 > 0 전제), 상쇄 없는 공식, 오름차순."""
    disc = b * b - 4.0 * a * c
    assert disc > 0.0
    q = -0.5 * (b + math.copysign(math.sqrt(disc), b))
    return tuple(sorted((q / a, c / q)))


def closed_real_rational(t0, zeros, poles):
    """T(s) = t0·Π(1 − s/z)/Π(1 − s/p) (모든 근 실수, 0 아님). 위상(T(0) 기준) = Σ_p atan(ω/p) − Σ_z atan(ω/z) -- 각 항이
    (−π/2, π/2) 라 언랩이 필요 없다. |T(0)| > 1 이면 |T| = 1 교차를 brentq 로(조밀 로그 격자에서 부호 바뀜이 한 번임을 확인).
    반환 dict(t, phase, ugf_w, ugf_hz, lag_rad, old_pm_deg)."""

    def t(w):
        s = 1j * w
        v = complex(t0)
        for z in zeros:
            v *= 1.0 - s / z
        for p in poles:
            v /= 1.0 - s / p
        return v

    def ph(w):
        return sum(math.atan(w / p) for p in poles) - sum(math.atan(w / z) for z in zeros)

    out = dict(t=t, phase=ph, ugf_w=None, ugf_hz=None, lag_rad=None, old_pm_deg=None)
    if abs(t0) > 1.0:
        grid = np.logspace(0, 13, 4001)
        f = np.array([abs(t(w)) - 1.0 for w in grid])
        assert int(np.count_nonzero(np.diff(np.sign(f)))) == 1     # 교차 하나(첫 교차 = 유일 교차)
        wu = brentq(lambda w: abs(t(w)) - 1.0, 1.0, 1e13, xtol=1e-9, rtol=4 * EPS, maxiter=500)
        lag = -ph(wu)
        out.update(ugf_w=wu, ugf_hz=wu / TWO_PI, lag_rad=lag, old_pm_deg=180.0 - math.degrees(lag))
    return out


def closed_ex8(gx2=EX8["gx2"]):
    """예 8 폐형식(β = 1 포트 Factor = 전달 H): 노드 2 (g2 + sC)v2 + gx·v5 = −gm·v1(g2 = 2gds), 노드 5 gx·v2 + (g5 + sC)v5 = 0
    (g5 = gds) -> H = −gm(g5 + sC)/((g2 + sC)(g5 + sC) − gx²). 극점 = 분모 근, 영점 −g5/C, T0 = gm·g5/(gx² − g2·g5).
    폐루프 1 + T = 0 근 = C²s² + (C(g2 + g5) − gm·C)s + (g2·g5 − gx² − gm·g5) 의 근."""
    p = EX8
    g2, g5, c = 2.0 * p["gds"], p["gds"], p["c"]
    poles = quad_roots(c * c, c * (g2 + g5), g2 * g5 - gx2)
    t0 = p["gm"] * g5 / (gx2 - g2 * g5)
    d = closed_real_rational(t0, (-g5 / c,), poles)
    d.update(t0=t0, poles=poles, zero=-g5 / c,
             closed_loop=quad_roots(c * c, c * (g2 + g5) - p["gm"] * c, g2 * g5 - gx2 - p["gm"] * g5))
    return d


def closed_ex8a(gx2=EX8["gx2"]):
    """예 8a·8b 의 되돌림 비(gm 제어원, 절단 노드 3 = gate + Cs 용량 전용): 노드 3 은 v2·β(β = Cf/(Cf + Cs)), 노드 2 유효 어드미턴스
    g2 + s·Ceff − gx²/(g5 + sC5)(Ceff = CL + Cf·Cs/(Cf + Cs)) -> T = gm·β(g5 + sC5)/((g2 + sCeff)(g5 + sC5) − gx²).
    (예 7 의 T = gm·β/(gds + sCeff) 에 교차 결합 항만 더한 것 -- test 에서 독립 Middlebrook 과 대조한다.)
    폐루프(1 + T = 0) 근 = Ceff·C5 s² + ((g2 + gm·β)C5 + g5·Ceff)s + ((g2 + gm·β)g5 − gx²) 의 근."""
    p, q = EX8, EX7
    beta = q["cf"] / (q["cf"] + q["cs"])
    ceff = q["cl"] + q["cf"] * q["cs"] / (q["cf"] + q["cs"])
    g2, g5, c5, gmb = 2.0 * p["gds"], p["gds"], p["c"], q["gm"] * beta
    poles = quad_roots(ceff * c5, g2 * c5 + g5 * ceff, g2 * g5 - gx2)
    t0 = gmb * g5 / (g2 * g5 - gx2)
    d = closed_real_rational(t0, (-g5 / c5,), poles)
    d.update(t0=t0, poles=poles, zero=-g5 / c5,
             closed_loop=quad_roots(ceff * c5, (g2 + gmb) * c5 + g5 * ceff, (g2 + gmb) * g5 - gx2))
    return d


def probe_of(parts, cuts, weights=(1.0,), nm=None, extra=()):
    """parts=(mos,res,cap) -> (절단 계 응답, ProbeFactor, extra 응답들). 절단 계 + extra 계를 한 번의 solve_responses 로."""
    from gmid_engine.metrics import LoopCut, cut_circuit, probe_factor, solve_responses
    cut = cut_circuit(circuit_of(*parts, nm=nm), tuple(LoopCut(k, i, t) for k, i, t in cuts))
    rs = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),) + tuple(extra))
    return rs[0], probe_factor(rs[0], cut.pairs, weights), rs[1:]


def check_rhp_detail(u):
    """3.10 'detail 형식(정확히)': 저장 순서 (("rhp_pole_count", n), ("rhp_poles", ((re, im), ...))), rhp_poles = Python float 쌍의
    tuple(complex 아님), 실부 > 0, 중복 없음, (|s|, 실부, 허부) 오름차순, rhp_pole_count = int = len. 반환 rhp_poles."""
    assert tuple(k for k, _ in u.detail) == ("rhp_pole_count", "rhp_poles")
    (_, n), (_, roots) = u.detail
    assert type(roots) is tuple
    for p in roots:
        assert type(p) is tuple and len(p) == 2, p
        assert type(p[0]) is float and type(p[1]) is float, p
        assert math.isfinite(p[0]) and math.isfinite(p[1]) and p[0] > 0.0, p
    assert type(n) is int and n == len(roots)
    assert len(set(roots)) == len(roots)
    keys = [(math.hypot(re, im), re, im) for re, im in roots]
    assert keys == sorted(keys)
    return roots


# 켤레 우반면 쌍 예(test 쪽 구성, 3.10 '켤레 복소쌍은 두 원소'): 반전 3단 고리(노드 2→3→4→2, 각 gm·gds·C) + 입력 M0(d=2, g=1, gds 0).
# 노드마다 (g + sC)v_k + gm·v_{k−1} = 0 -> (g + sC)³ + gm³ = 0 -> s = (−g − gm·c)/C, c ∈ {1, e^{±j2π/3}}.
RING = dict(gm=1e-4, gds=1e-5, c=1e-12)


def ring_system():
    p = RING
    mos = ((2, 1, 0, 0, 1e-3, 0.0, 0.0), (3, 2, 0, 0, p["gm"], 0.0, p["gds"]), (4, 3, 0, 0, p["gm"], 0.0, p["gds"]),
           (2, 4, 0, 0, p["gm"], 0.0, p["gds"]))
    ck = circuit_of(mos, (), ((2, 0, p["c"]), (3, 0, p["c"]), (4, 0, p["c"])))
    return ck, build_mna(ck, (Excitation("vin", voltages=((1, 1.0),)),), (Sense(2),))


def closed_ring_poles():
    """반환 (실극점, (re, im) 켤레 쌍 -- 허부 음·양 순)."""
    p = RING
    re = (-p["gds"] + 0.5 * p["gm"]) / p["c"]
    im = p["gm"] * math.sqrt(3.0) / 2.0 / p["c"]
    return (-p["gds"] - p["gm"]) / p["c"], ((re, -im), (re, im))


def pm_undefined(la_or_result):
    """LoopAnalysis·MetricResult 의 undefined 중 quantity == "phase_margin_deg" 인 것(순서 유지)."""
    return tuple(u for u in (la_or_result.undefined or ()) if u.quantity == "phase_margin_deg")


# =====================================================================================================================
# [CM 2026-10-08] 예 7d·7e -- 섞인 절단(n 용량 전용 gate, x 전도), 공통 모드 루프 모양 (CONTRACT 5절 예 7d·7e, 3.17, I-18~I-20)
# 기대값 = 아래 폐형식(되돌림 비, test 작성자 손유도 -- 엔진 출력 아님):
#   gate 쪽 노드(Cg 만, 열림)를 시험 전압 1 로 두면 drain 노드 KCL: (gds + sCL)·v_d + sCg/(1 + sRCg)·v_d = −gm,
#   gate 로 돌아오는 전압 v_g = v_d/(1 + sRCg) -> T(s) = gm / ((gds + sCL)(1 + sRCg) + sCg)
#   = gm / (gds + s(CL + Cg + gds·R·Cg) + s²·CL·R·Cg). 예 7e 는 공통 모드(v2 = v12)에서 감지 노드가 두 R 병렬(R/2)·두 Cg
#   병렬(2Cg)이라 v20 = v/(1 + sRCg), 반회로마다 같은 식 -> 같은 T(s).
# =====================================================================================================================

EX7D = dict(gm=1e-3, gds=1e-5, cg=1e-12, cl=1e-12, rf=1e5)
EX7D_CUT = (("resistor", 0, "b"),)                       # Rf(2, 3) 의 b 단자(노드 3 = gate 쪽) -> x = 4
EX7E_CUTS = (("resistor", 0, "b"), ("resistor", 1, "a"))   # R(2, 20)·R(20, 12) 의 노드 20 쪽 단자 -> 같은 x = 21


def ex7d_circuit(nm=None):
    """예 7d: MosSmallSignal(d=2, g=3, s=0, b=0, gm, 0, gds, cgs=Cg), Resistor(2, 3, Rf), Capacitor(2, 0, CL), ac_ground (0,)."""
    m = mapper(nm)
    p = EX7D
    return SmallSignalCircuit(
        mos=(MosSmallSignal(m(2), m(3), m(0), m(0), p["gm"], 0.0, p["gds"], cgs=p["cg"]),),
        resistors=(Resistor(m(2), m(3), p["rf"]),),
        capacitors=(Capacitor(m(2), m(0), p["cl"]),),
        ac_ground=(m(0),))


def ex7e_circuit(nm=None):
    """예 7e: 두 반회로 MOS(d=2, g=20)·MOS(d=12, g=20) (각 cgs = Cg), Resistor(2, 20)·Resistor(20, 12), Capacitor(2, 0)·
    Capacitor(12, 0), ac_ground (0,)."""
    m = mapper(nm)
    p = EX7D
    return SmallSignalCircuit(
        mos=(MosSmallSignal(m(2), m(20), m(0), m(0), p["gm"], 0.0, p["gds"], cgs=p["cg"]),
             MosSmallSignal(m(12), m(20), m(0), m(0), p["gm"], 0.0, p["gds"], cgs=p["cg"])),
        resistors=(Resistor(m(2), m(20), p["rf"]), Resistor(m(20), m(12), p["rf"])),
        capacitors=(Capacitor(m(2), m(0), p["cl"]), Capacitor(m(12), m(0), p["cl"])),
        ac_ground=(m(0),))


def ex7d_ref_parts():
    """독립 Middlebrook(ref_middlebrook, MOS 7칸 -- 용량 없음)용 예 7d: gate–source(접지) 용량 cgs 를 같은 노드 쌍의 명시 C 로."""
    p = EX7D
    return (((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), ((2, 3, p["rf"]),), ((2, 0, p["cl"]), (3, 0, p["cg"])))


def ex7e_ref_parts():
    p = EX7D
    return (((2, 20, 0, 0, p["gm"], 0.0, p["gds"]), (12, 20, 0, 0, p["gm"], 0.0, p["gds"])),
            ((2, 20, p["rf"]), (20, 12, p["rf"])),
            ((2, 0, p["cl"]), (12, 0, p["cl"]), (20, 0, p["cg"]), (20, 0, p["cg"])))


def closed_ex7d(p=None):
    """예 7d·7e 폐형식. 반환 dict(t(ω), t0, a=(a0, a1, a2) 분모 계수, poles(실수 2개, 오름차순), ugf_hz, pm_deg, gain_db).
    UGF: |a0 − a2ω² + j·a1ω| = gm -> u = ω² 의 2차식 a2²u² + (a1² − 2a0a2)u + (a0² − gm²) = 0 의 양근.
    PM = 180° + arg T(jω_u) = 180° − arg(분모)."""
    p = dict(EX7D if p is None else p)
    gm = p["gm"]
    a0 = p["gds"]
    a1 = p["cl"] + p["cg"] + p["gds"] * p["rf"] * p["cg"]
    a2 = p["cl"] * p["rf"] * p["cg"]

    def t(w):
        s = 1j * w
        return gm / ((p["gds"] + s * p["cl"]) * (1.0 + s * p["rf"] * p["cg"]) + s * p["cg"])

    A, B, C = a2 * a2, a1 * a1 - 2.0 * a0 * a2, a0 * a0 - gm * gm
    u = (-B + math.sqrt(B * B - 4.0 * A * C)) / (2.0 * A)
    wu = math.sqrt(u)
    pm = 180.0 - math.degrees(math.atan2(a1 * wu, a0 - a2 * u))
    disc = math.sqrt(a1 * a1 - 4.0 * a2 * a0)
    poles = sorted(((-a1 - disc) / (2.0 * a2), (-a1 + disc) / (2.0 * a2)))
    return dict(t=t, t0=gm / a0, a=(a0, a1, a2), poles=tuple(poles), ugf_hz=wu / TWO_PI, pm_deg=pm,
                gain_db=20.0 * math.log10(gm / a0), wu=wu)


def closed_ex7c():
    """예 7c 폐형식(계약 5절 예 7c, 손유도로 재확인): Cf 를 x 로 뗀 뒤 gm 시험 전압 1 -> drain 노드 임피던스
    Z2 = 1/(gds + sCL + sCf/(1 + sCfRs)), gate 로 돌아오는 전압 = v_d·sRsCf/(1 + sRsCf) -> T = gm·Z2·sRsCf/(1 + sRsCf).
    T(0) = 0(분자에 s), 대역 통과."""
    p = EX7

    def t(w):
        s = 1j * w
        z2 = 1.0 / (p["gds"] + s * p["cl"] + s * p["cf"] / (1.0 + s * p["cf"] * p["rs"]))
        return p["gm"] * z2 * s * p["rs"] * p["cf"] / (1.0 + s * p["rs"] * p["cf"])

    return dict(t=t, t0=0.0)


def probe_cut(circuit, cuts, weights=(1.0,), extra=()):
    """SmallSignalCircuit -> (CutCircuit, 절단 계, ProbeFactor, extra 응답). 절단 계 + extra 계를 한 번의 solve_responses 로."""
    from gmid_engine.metrics import LoopCut, cut_circuit, probe_factor, solve_responses
    cut = cut_circuit(circuit, tuple(LoopCut(k, i, t) for k, i, t in cuts))
    sysm = build_mna(cut.circuit, cut.excitations, cut.senses)
    rs = solve_responses((sysm,) + tuple(extra))
    return cut, sysm, probe_factor(rs[0], cut.pairs, weights), rs[1:]


def i20_cases():
    """I-20 기준선 대상(이름 -> (SmallSignalCircuit, cuts, weights)). 기준선 파일 fixtures/i20_probe_samples_base.json 은 이
    함수를 변경 전 엔진(merge-base 3a38275, 섞인 절단 T(0) 도입 직전)에서 돌려 만들었다(oracle (c) 기준선 -- 아래 파일 머리 참조).
    섞이지 않은 절단(ex7 용량 전용, ex7b DM·CM, resistive 전도 전용)과 섞인 절단(ex7c, ex7d, ex7e)."""
    p = EX7
    resistive = (((2, 3, 0, 0, p["gm"], 0.0, p["gds"]),), ((2, 3, 3e4), (3, 0, 1e4)), ((2, 0, p["cl"]),))
    return {
        "ex7": (circuit_of(*ex7_parts()), EX7_CUT, (1.0,)),
        "ex7b_dm": (circuit_of(*ex7b_parts()), EX7B_CUTS, (0.5, -0.5)),
        "ex7b_cm": (circuit_of(*ex7b_parts()), EX7B_CUTS, (0.5, 0.5)),
        "resistive": (circuit_of(*resistive), (("resistor", 0, "b"),), (1.0,)),
        "ex7c": (circuit_of(*ex7_parts(cs_resistor=True)), EX7_CUT, (1.0,)),
        "ex7d": (ex7d_circuit(), EX7D_CUT, (1.0,)),
        "ex7e": (ex7e_circuit(), EX7E_CUTS, (1.0,)),
    }


I20_MIXED = ("ex7c", "ex7d", "ex7e")        # 섞인 절단(n 과 x 중 하나만 용량 전용) -- ω = 0 한 점이 NaN -> 값


# =====================================================================================================================
# [CM 0e487b3] 출력 포트 CM 주입(metrics CONTRACT 7.11, S-21~S-28) -- 합성 CMFB 변형 회로(test 작성자 설계)와 독립 기준.
# 코어: 입력쌍 M1 (op, ip, gnd)·M2 (om, im, gnd), PMOS 부하 M3 (op, c, vdd)·M4 (om, c, vdd), CL1·CL2. CM 제어 넷 c 를 만드는 CMFB
# 변형만 바꾼다. 기대값 출처:
#   (a) 변형마다 손유도 T_cm(0) (아래 CM_VARIANTS 의 "t0" -- 식은 각 항목 주석), 출력 노드 KCL: Go·v = −gmp·v_c (Go = gds1 + gdsp,
#       CM 에서 평균망 전류 0), v_c = A·v -> T_cm(0) = gmp·A/Go.
#   (b) 독립 Middlebrook(ref_cm_output): 이 파일이 직접 세운 노드 어드미턴스(MOS 3.1 식·용량 5개)에 7.11 절단 규칙(출력 넷에 d 또는 s 가
#       정확히 한쪽만 물린 MOS 의 그 단자 -> x)을 test 가 따로 적용하고 두 출력에 (1/2, 1/2) 이중 주입. PM 은 |T| = 1 교차(brentq)와
#       저주파부터 언랩한 위상으로 test 가 계산.
# 소자 이름·넷 이름은 test 가 지은 것이고(library 이름과 겹치지 않음), 엔진에는 topology/spec JSON 으로만 들어간다.
# =====================================================================================================================

CM_SUPPLIES = {"gnd": 0.0, "vdd": 1.8}
CM_PORTS = {"ip": ("input", "differential_input_p"), "im": ("input", "differential_input_n"),
            "op": ("output", "differential_output_p"), "om": ("output", "differential_output_n")}
CM_GDS1, CM_GDSP, CM_CL, CM_CG, CM_R = 1e-6, 1e-6, 1e-12, 0.2e-12, 1e6
CM_GO = CM_GDS1 + CM_GDSP


def _core(gmp):
    """(mos, passives): mos = (이름, kind, d, g, s, b, gm, gds, cgs), passives = (이름, kind, a, b, 값)."""
    mos = [("M1", "nmos", "op", "ip", "gnd", "gnd", 1e-4, CM_GDS1, 0.0),
           ("M2", "nmos", "om", "im", "gnd", "gnd", 1e-4, CM_GDS1, 0.0),
           ("M3", "pmos", "op", "c", "vdd", "vdd", gmp, CM_GDSP, CM_CG),
           ("M4", "pmos", "om", "c", "vdd", "vdd", gmp, CM_GDSP, CM_CG)]
    pas = [("CL1", "capacitor", "op", "gnd", CM_CL), ("CL2", "capacitor", "om", "gnd", CM_CL)]
    return mos, pas


def cm_variant(name):
    """반환 dict(mos, passives, sources((이름, kind, a, b, 값)), bias_inputs, t0(손유도), outputs)."""
    src, bias = [], []
    if name in ("direct", "ref_rc", "low_gain"):
        # V0: 저항 평균 R1(op, c)·R2(c, om) 이 바로 PMOS gate(c) -- 예 7e 의 PMOS 판. A = 1 -> T0 = gmp/Go.
        gmp = {"direct": 1e-4, "ref_rc": 1e-4, "low_gain": 1e-6}[name]
        mos, pas = _core(gmp)
        pas += [("R1", "resistor", "op", "c", CM_R), ("R2", "resistor", "c", "om", CM_R)]
        t0 = gmp / CM_GO
        if name == "ref_rc":
            # 감지 넷 기준 Rref(c, gnd)·Cref(c, gnd): CM 에서 평균망에 DC 전류가 흐른다. 반환비(gmp 제어 전압 v_c 를 1 로 떼고):
            # 감지 넷 KCL 2(v_c − v)/R + v_c/Rref = 0 -> v_c = k·v, k = 2Rref/(2Rref + R); 출력 KCL (Go + (1 − k)/R)·v = −gmp
            # -> T0 = gmp·k/(Go + (1 − k)/R) = 1e-4·(2/3)/(2e-6 + 1/3e-6) = 200/7.
            rref = 1e6
            pas += [("Rref", "resistor", "c", "gnd", rref), ("Cref", "capacitor", "c", "gnd", 0.1e-12)]
            kk = 2.0 * rref / (2.0 * rref + CM_R)
            t0 = gmp * kk / (CM_GO + (1.0 - kk) / CM_R)
    elif name == "err_amp":
        # V1: 저항 평균 s -> CS Me1(e, s, gnd)+Re1(vdd, e) -> CS Me2(c, e, gnd)+Re2(vdd, c) (반전 2, gds 0) -> PMOS 부하(반전 1).
        # A = gme1·Re1·gme2·Re2 = 100 -> T0 = gmp·A/Go = 2e-7·100/2e-6 = 10. 평균 저항 1e4(감지 넷 극점을 높게 -- 3극 루프가
        # 안정하도록; CM 에서 평균망 전류 0 이라 T0 와 무관).
        gmp = 2e-7
        mos, pas = _core(gmp)
        mos += [("Me1", "nmos", "e", "s", "gnd", "gnd", 1e-4, 0.0, CM_CG), ("Me2", "nmos", "c", "e", "gnd", "gnd", 1e-4, 0.0, 0.0)]
        pas += [("R1", "resistor", "op", "s", 1e4), ("R2", "resistor", "s", "om", 1e4),
                ("Re1", "resistor", "vdd", "e", 1e5), ("Re2", "resistor", "vdd", "c", 1e5)]
        t0 = gmp * 100.0 / CM_GO
    elif name == "sf_buffer":
        # V2: 소스 팔로어 Ms1(vdd, op, bp)·Ms2(vdd, om, bm)(gds 0, gmb 0, 이상 전류원 바이어스 -> 이득 gms/gms = 1) -> 저항 평균 c ->
        # PMOS gate. T0 = gmp/Go.
        gmp = 1e-4
        mos, pas = _core(gmp)
        mos += [("Ms1", "nmos", "vdd", "op", "bp", "bp", 1e-4, 0.0, 0.0), ("Ms2", "nmos", "vdd", "om", "bm", "bm", 1e-4, 0.0, 0.0)]
        pas += [("R1", "resistor", "bp", "c", CM_R), ("R2", "resistor", "c", "bm", CM_R)]
        src += [("Ib1", "current_source", "bp", "gnd", 1e-6), ("Ib2", "current_source", "bm", "gnd", 1e-6)]
        t0 = gmp / CM_GO
    elif name == "dda":
        # V3: DDA -- 쌍 A: Ma(e, op, ta)·Mb(f, vref, ta), 쌍 B: Mc(e, om, tb)·Md(f, vref, tb), 꼬리 이상 전류원(교류 개방), 쌍 gds 0.
        # CM v: v_ta = v_tb = v/2 -> e 에서 빠지는 전류 gm·v -> v_e = −gm·Re·v; Mx(c, e, gnd)+Rc: v_c = gm·gmx·Re·Rc·v.
        # T0 = gmp·gm·gmx·Re·Rc/Go = 2e-6·1e-4·1e-4·1e5·1e5/2e-6 = 100.
        gmp = 2e-6
        mos, pas = _core(gmp)
        mos += [("Ma", "nmos", "e", "op", "ta", "gnd", 1e-4, 0.0, 0.0), ("Mb", "nmos", "f", "vref", "ta", "gnd", 1e-4, 0.0, 0.0),
                ("Mc", "nmos", "e", "om", "tb", "gnd", 1e-4, 0.0, 0.0), ("Md", "nmos", "f", "vref", "tb", "gnd", 1e-4, 0.0, 0.0),
                ("Mx", "nmos", "c", "e", "gnd", "gnd", 1e-4, 0.0, 0.0)]
        pas += [("Re", "resistor", "vdd", "e", 1e5), ("Rf", "resistor", "vdd", "f", 1e5), ("Rc", "resistor", "vdd", "c", 1e5)]
        src += [("It1", "current_source", "ta", "gnd", 1e-6), ("It2", "current_source", "tb", "gnd", 1e-6)]
        bias = ["vref"]
        t0 = gmp * 1e-4 * 1e-4 * 1e5 * 1e5 / CM_GO
    elif name == "triode":
        # V4: 평균 저항 R1·R2 를 triode MOS 로(gate = vdd 레일, Vds ≈ 0 이라 gm = 0, gds = 1/R): 전기적으로 "direct" 와 같은 회로
        # (물리 CM 루프 이득 = gmp/Go = 50). 7.11 규칙상 Mt 의 channel 단자가 출력에 물려 구동자(x)로 옮겨진다.
        gmp = 1e-4
        mos, pas = _core(gmp)
        mos += [("Mt1", "nmos", "op", "vdd", "c", "gnd", 0.0, 1.0 / CM_R, 0.0),
                ("Mt2", "nmos", "om", "vdd", "c", "gnd", 0.0, 1.0 / CM_R, 0.0)]
        t0 = gmp / CM_GO          # 물리 루프 이득(정의 밖 참고값) -- 엔진 정의로는 0(7.11 변형 4)
    else:
        raise KeyError(name)
    return dict(mos=mos, passives=pas, sources=src, bias_inputs=bias, t0=t0)


def cm_topology(name, variant, names=None):
    nm = (lambda n: n) if names is None else (lambda n: names.get(n, n))
    v = cm_variant(variant)
    d = topo_doc(name, mos=[(nm(a), k, nm(dd), nm(g), nm(s), nm(b)) for a, k, dd, g, s, b, *_ in v["mos"]],
                 passives=[(nm(a), k, nm(x), nm(y)) for a, k, x, y, _ in v["passives"]],
                 sources=[(nm(a), k, nm(x), nm(y)) for a, k, x, y, _ in v["sources"]],
                 ports={nm(k): p for k, p in CM_PORTS.items()}, rails=(nm("gnd"), nm("vdd")))
    if v["bias_inputs"]:
        d["bias_inputs"] = [nm(n) for n in v["bias_inputs"]]
    return d, v


def cm_case(tmp_path, variant, constraints, names=None, ss_scale=None):
    """(TopologyDoc, spec, 손 S2 스냅샷, passive_values, variant dict). 원소 값은 spec 에도 쓰고 passive_values 로도 넘긴다(7.4)."""
    nm = (lambda n: n) if names is None else (lambda n: names.get(n, n))
    topo, v = cm_topology("cmv_%s%s" % (variant, "" if names is None else "_r"), variant, names)
    kinds = {e["name"]: e["kind"] for e in topo["passive_elements"] + topo.get("ideal_sources", [])}
    els = tuple((nm(a), kinds[nm(a)], val) for a, _, _, _, val in v["passives"] + v["sources"])
    sup = {nm(k): x for k, x in CM_SUPPLIES.items()}
    td, spec = load_case(tmp_path, topo, sup, els, (), constraints, input_dc_v=0.9)
    ss = {nm(a): hand_ss(gm, gds, cgs=cg) for a, _, _, _, _, _, gm, gds, cg in v["mos"]}
    snap = with_ss(s2_of(td, sup), ss)
    pv = tuple(sorted((nm(a), val) for a, _, _, _, val in v["passives"]))
    return td, spec, snap, pv, v


def ref_cm_output(variant, omega):
    """(b) 독립 Middlebrook: 출력 op·om 에서 7.11 절단(출력 넷에 d 또는 s 가 정확히 한쪽만 물린 MOS 의 그 단자 -> x_넷), 가중 (½, ½),
    교류접지 = 레일 ∪ 입력 포트 ∪ gate 전용 넷(bias_inputs). 이상 전류원 = 개방. 반환 T(jω)."""
    v = cm_variant(variant)
    fixed = {"gnd", "vdd", "ip", "im"} | set(v["bias_inputs"])
    outs = ("om", "op")
    mos = [list(m) for m in v["mos"]]
    for m in mos:
        for o in outs:
            hit = [i for i in (2, 4) if m[i] == o]
            if len(hit) == 1 and m[2] != m[4]:
                m[hit[0]] = "x_" + o
    nets = set()
    for m in mos:
        nets |= set(m[2:6])
    for p in v["passives"]:
        nets |= {p[2], p[3]}
    nets |= {"x_om", "x_op"}
    unk = sorted(n for n in nets if n not in fixed)
    ix = {n: i for i, n in enumerate(unk)}
    nu, k = len(unk), 2
    s = 1j * omega
    a = np.zeros((nu + k, nu + k), dtype=complex)

    def two(p, q, y):
        for r_, c_, sg in ((p, p, 1.0), (q, q, 1.0), (p, q, -1.0), (q, p, -1.0)):
            if r_ in ix and c_ in ix:
                a[ix[r_], ix[c_]] += sg * y

    for _, kind, x, y, val in v["passives"]:
        two(x, y, 1.0 / val if kind == "resistor" else s * val)
    for _, _, d, g, so, b, gm, gds, cgs in mos:
        for row, sg in ((d, 1.0), (so, -1.0)):
            if row in ix:
                for col, val in ((g, gm), (d, gds), (so, -(gm + gds))):
                    if col in ix:
                        a[ix[row], ix[col]] += sg * val
        two(g, so, s * cgs)
    pairs = [(o, "x_" + o) for o in outs]
    for j, (n, x) in enumerate(pairs):
        a[ix[n], nu + j] += 1.0
        a[ix[x], nu + j] -= 1.0
        a[nu + j, ix[n]] += 1.0
        a[nu + j, ix[x]] -= 1.0
    w = np.array([0.5, 0.5])
    rhs = np.zeros(nu + k, dtype=complex)
    rhs[nu:] = w
    sol = np.linalg.solve(a, rhs)
    vn = np.array([sol[ix[n]] for n, _ in pairs])
    vx = np.array([sol[ix[x]] for _, x in pairs])
    tv = -(w @ vx) / (w @ vn)
    rhs = np.zeros(nu + k, dtype=complex)
    for j, (n, _) in enumerate(pairs):
        rhs[ix[n]] += w[j]
    sol = np.linalg.solve(a, rhs)
    i_ = sol[nu:]
    ti = (w @ i_) / (w @ (w - i_))
    return (tv * ti - 1.0) / (tv + ti + 2.0)


def ref_pm(tfun, w_lo=1.0, w_hi=1e13, n=4000):
    """|T| = 1 첫 하강 교차(brentq, log ω)와 w_lo 부터 언랩한 위상 -> (ugf_hz, pm_deg). 교차 없으면 (None, None)."""
    ws = np.geomspace(w_lo, w_hi, n)
    ts = np.array([tfun(w) for w in ws])
    mag = np.abs(ts)
    ph = np.unwrap(np.angle(ts))
    for i in range(n - 1):
        if mag[i] >= 1.0 > mag[i + 1]:
            lw = brentq(lambda lw_: abs(tfun(math.exp(lw_))) - 1.0, math.log(ws[i]), math.log(ws[i + 1]), xtol=1e-14, rtol=1e-15)
            wu = math.exp(lw)
            p = cmath.phase(tfun(wu))
            p += 2.0 * math.pi * round((ph[i] - p) / (2.0 * math.pi))     # 같은 가지로
            assert abs(ph[0]) < 1e-3, ph[0]                                # T(0) 은 양의 실수(음되먹임) -- 위상 기준 0
            return wu / TWO_PI, 180.0 + math.degrees(p)
    return None, None
