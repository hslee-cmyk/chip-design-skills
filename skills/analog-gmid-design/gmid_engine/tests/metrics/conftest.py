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
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), Sense(m(2)))


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
                     Sense(m(2)))


def ex2_beta_res(nm=None):
    """예 2 β 계(저항): R(2,3,30k), R(3,0,10k), 1 V at 2, Sense(3) -> β = 0.25."""
    m = mapper(nm)
    ck = SmallSignalCircuit(resistors=(Resistor(m(2), m(3), 30e3), Resistor(m(3), m(0), 10e3)), ac_ground=(m(0),))
    return build_mna(ck, (Excitation("vfb", voltages=((m(2), 1.0),)),), Sense(m(3)))


def ex2c_beta_cap(nm=None, cf=1e-12, cs=3e-12):
    """예 2c: Cf(2,3), Cs(3,0), 1 V at 2, Sense(3) -> β = Cf/(Cf+Cs)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(capacitors=(Capacitor(m(2), m(3), cf), Capacitor(m(3), m(0), cs)), ac_ground=(m(0),))
    return build_mna(ck, (Excitation("vfb", voltages=((m(2), 1.0),)),), Sense(m(3)))


def ex2b_sf(gmb=2e-4, nm=None):
    """예 2b: source follower, d=9 교류접지, RL 10k, 1 V at 1, Sense(2)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(
        mos=(MosSmallSignal(m(9), m(1), m(2), m(0), 1e-3, gmb, 1e-5),),
        resistors=(Resistor(m(2), m(0), 1e4),),
        ac_ground=(m(0), m(9)),
    )
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), Sense(m(2)))


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
                     Sense(m(2)))


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
    return build_mna(ck, (Excitation("vin", voltages=((m(1), 1.0),)),), Sense(m(3)))


def ex6_ratio(nm=None):
    """예 6: Ra(1,2,1k), Rb(2,3,10k), 열 num(1 V at 1)·den(1 V at 3), Sense(2)."""
    m = mapper(nm)
    ck = SmallSignalCircuit(resistors=(Resistor(m(1), m(2), 1e3), Resistor(m(2), m(3), 1e4)), ac_ground=(m(0),))
    return build_mna(ck, (Excitation("num", voltages=((m(1), 1.0),)), Excitation("den", voltages=((m(3), 1.0),))),
                     Sense(m(2)))


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
