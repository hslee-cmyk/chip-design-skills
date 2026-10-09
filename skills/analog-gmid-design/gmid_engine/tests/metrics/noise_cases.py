"""[U8 2026-10-09] 잡음 metric test 공용 -- 손 회로 생성기와 독립 기대값 (metrics CONTRACT 10절, 설계 41 §7.1·7.3).

피검 함수로 기대값을 만들지 않는다. 기대값 출처:
* (a) 폐형식(이 파일 `closed_*`): 저항 분압기의 입력 환산 열잡음 4kT(Ra‖Rb)/H0², 1극 RC 의 꼬리까지 적분, 폐루프 1극 적분, 1/f corner (A/B)^(1/EF).
* (b) 이 파일의 독립 노드 해석(`ref_transfer`): tests/metrics conftest `ref_system`(전체 노드 어드미턴스를 직접 세워 고정 노드를 소거해 푼다)으로
  잡음원 주입 전류·직렬 전압원(전하 주입 q = C·e)의 출력 전달을 따로 푼다.
* (d) 볼츠만 상수 = scipy.constants(CODATA), 온도 = LUT 측정 온도(27 °C) -- 계약 10.1 'kT = k × (temp_c + zero_Celsius)'.

입력 조립(SsCircuit·MnaSystem·ParameterSet·NoiseSources·NoisePlan)은 공개 API 로 만든다 -- 그것은 피검 값이 아니라 피검 함수의 입력이다.
노드 번호는 정수, 넷·소자 이름은 `names` 인자로 바꿀 수 있다(이름 전단사 불변 test).
"""
from __future__ import annotations

import math

import numpy as np
from scipy import constants

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    MosSmallSignal,
    NoiseDecl,
    NoiseDevice,
    NoiseInput,
    NoiseSetup,
    Resistor,
    Sense,
    SmallSignalCircuit,
    build_mna,
    lut_parameters,
    noise_plan,
    noise_sources,
)
from gmid_engine.metrics.ss_types import SsCircuit

from .conftest import ref_system

TEMP_C = 27.0
KT = constants.k * (TEMP_C + constants.zero_Celsius)          # (d) CODATA k × LUT 측정 온도(K)
F_LO = 1.0                                                     # LUT 가 실측한 가장 낮은 잡음 주파수(lut CONTRACT 9.1 NOISE_F_PROBE = 1 Hz)
TWO_PI = 2.0 * math.pi


class Case:
    """손 소신호 회로 한 개. mos: (이름, d, g, s, b, gm, gds[, cgs, cgd]) 넷 이름, res·cap: (이름, a, b, 값), ground: 교류접지 넷,
    inp: 입력 포트 넷, out: 감지 넷. names: 넷·소자 이름 치환 dict(없는 이름은 그대로). 노드 번호 = 넷 이름 정렬 순서가 아니라 `order`(정수
    배정 순서 -- 치환 test 가 번호도 바꿀 수 있게)."""

    def __init__(self, mos=(), res=(), cap=(), ground=("gnd",), inp="in", out="out", names=None, order=None):
        nm = dict(names or {})
        self.nm = lambda x: nm.get(x, x)
        nets = set(ground) | {inp, out}
        for t in mos:
            nets |= set(t[1:5])
        for t in tuple(res) + tuple(cap):
            nets |= {t[1], t[2]}
        nets = sorted(nets) if order is None else list(order)
        self.nets = tuple(self.nm(n) for n in nets)
        self.ix = {n: i for i, n in enumerate(nets)}
        self.mos, self.res, self.cap = tuple(mos), tuple(res), tuple(cap)
        self.ground, self.inp, self.out = tuple(ground), inp, out

    def node(self, net):
        return self.ix[net]

    def circuit(self, ac_ground=()):
        ix = self.ix
        mos = []
        for t in self.mos:
            name, d, g, s, b, gm, gds = t[:7]
            cgs, cgd = (t[7], t[8]) if len(t) > 7 else (0.0, 0.0)
            mos.append(MosSmallSignal(ix[d], ix[g], ix[s], ix[b], gm, 0.0, gds, cgs, cgd, 0.0, 0.0, 0.0, label=self.nm(name)))
        return SmallSignalCircuit(
            mos=tuple(mos),
            resistors=tuple(Resistor(ix[a], ix[b], v, label=self.nm(n)) for n, a, b, v in self.res),
            capacitors=tuple(Capacitor(ix[a], ix[b], v, label=self.nm(n)) for n, a, b, v in self.cap),
            ac_ground=tuple(ix[g] for g in ac_ground))

    def ss(self):
        return SsCircuit(self.nets, self.circuit(), tuple(self.nm(r[0]) for r in self.res),
                         tuple(self.nm(c[0]) for c in self.cap), tuple(self.nm(g) for g in self.ground),
                         (self.nm(self.inp),))

    def system(self, mode="view"):
        """mode view = 입력 1 V 구동 열 하나 + 감지 out(전달 뷰 / 개루프 출력 잡음 계), closed = 입력 자유(열 없음)."""
        ix = self.ix
        circ = self.circuit(ac_ground=tuple(self.ground))
        if mode == "closed":
            # 열은 쓰지 않는다(폐루프 출력 잡음은 전달 뷰 열이 없다) -- build_mna 가 열 하나 이상을 요구해 감지 넷 전류 열을 둔다
            return build_mna(circ, (Excitation("probe", currents=((ix[self.out], 1.0),)),), (Sense(ix[self.out]),))
        return build_mna(circ, (Excitation("view", voltages=((ix[self.inp], 1.0),)),), (Sense(ix[self.out]),))

    # ---- 독립 기준(b): conftest ref_system
    def _ref_mos(self):
        ix = self.ix
        out = []
        for t in self.mos:
            _n, d, g, s, b, gm, gds = t[:7]
            cgs, cgd = (t[7], t[8]) if len(t) > 7 else (0.0, 0.0)
            out.append((ix[d], ix[g], ix[s], ix[b], gm, 0.0, gds, cgs, cgd, 0.0, 0.0, 0.0))
        return tuple(out)

    def ref(self, column, omega, closed=False, mos=None):
        ix = self.ix
        res = tuple((ix[a], ix[b], v) for _n, a, b, v in self.res)
        cap = tuple((ix[a], ix[b], v) for _n, a, b, v in self.cap)
        ground = tuple(ix[g] for g in self.ground)
        volts = dict(column.get("v", {}))
        if not closed:
            volts.setdefault(ix[self.inp], 0.0)                 # 입력 고정(전달 뷰·개루프 출력 잡음): 구동이 없으면 0 V
        column = {"v": volts, "i": dict(column.get("i", {})), "q": dict(column.get("q", {}))}
        return complex(ref_system(self._ref_mos() if mos is None else mos, res, cap, ground,
                                  (column,), ((ix[self.out], None),), omega)[0, 0])

    def ref_h(self, omega):
        """전달 뷰 H = v(out)/v(in)(입력 1 V)."""
        return self.ref({"v": {self.ix[self.inp]: 1.0}}, omega)

    def ref_z(self, a, b, omega, closed=False):
        """단위 잡음 전류(b 에서 a 로 소자를 흐름 = 노드 a 로 주입 +1, 노드 b 에서 −1)의 출력 전달. 입력 고정(closed 면 자유)."""
        ix = self.ix
        i = {}
        i[ix[a]] = i.get(ix[a], 0.0) + 1.0
        i[ix[b]] = i.get(ix[b], 0.0) - 1.0
        for g in self.ground:
            i.pop(ix[g], None)
        if not closed:
            i.pop(ix[self.inp], None)
        return self.ref({"i": i}, omega, closed=closed)

    def ref_series_cap(self, cap_name, omega, closed=True):
        """커패시터에 직렬로 놓인 단위 전압원 e 의 출력 전달 = 노턴 등가 전하 C·e 를 두 단자에(a 에 +, b 에 −) 주입."""
        ix = self.ix
        n, a, b, c = next(t for t in self.cap if t[0] == cap_name)
        q = {ix[a]: c, ix[b]: -c}
        for g in self.ground:
            q.pop(ix[g], None)
        return self.ref({"q": q}, omega, closed=closed)


def noise_input(devices, decl=None, f_lo=F_LO, kt=KT):
    return NoiseInput(NoiseDecl() if decl is None else decl, tuple(devices), f_lo, kt)


def setup_of(case, devices=(), decl=None, *, mode="open", input_devices=None, rel_tol=None, poles=(), f_lo=F_LO,
             column="auto", kt=KT):
    """NoiseSetup 조립. mode = open(입력 고정, 전달 뷰 열 0) | closed(입력 자유, 열 없음). rel_tol: MOS 마다 같은 LUT 상대 불확실성(None = 미정)."""
    decl = NoiseDecl(feedback=()) if decl is None else decl
    ss = case.ss()
    system = case.system("closed" if mode == "closed" else "view")
    col = (None if mode == "closed" else 0) if column == "auto" else column
    params = lut_parameters(ss.circuit, tuple(rel_tol for _ in ss.circuit.mos))
    noise = noise_input(devices, decl, f_lo, kt)
    sources = noise_sources(ss, noise, params)
    return NoiseSetup(system, 0, col, sources, params, noise, noise_plan(ss, decl), ss, input_devices, tuple(poles), mode)


def dev(name, a=0.0, b=0.0, ef=1.0, tol_flicker=None, tol_thermal=None, failure=None, b_status=None):
    return NoiseDevice(name, a=a, b=b, ef=ef, b_status=("known" if b is not None else "no_feedthrough_free_point")
                       if b_status is None else b_status, tol_flicker=tol_flicker, tol_thermal=tol_thermal, failure=failure)


def codes(result):
    return tuple(u.code for u in result.undefined)


def detail(result):
    return dict(result.detail)


# ---------------------------------------------------------------- 폐형식 (a)

def closed_divider_th_in(ra, rb, kt=KT):
    """저항 분압기(in -Ra- out -Rb- gnd, out 에 C 가 있어도 같음): 출력 잡음 4kT·Re Z_out, H = H0/(1 + jωRpC) 이라 비가 주파수 무관 = 4kT·Rp/H0²."""
    rp = ra * rb / (ra + rb)
    h0 = rb / (ra + rb)
    return 4.0 * kt * rp / h0 ** 2


def closed_one_pole_integral(s0, fp, f_lo):
    """∫_{f_lo}^∞ s0/(1 + (f/fp)²) df = s0·fp·(π/2 − atan(f_lo/fp))."""
    return s0 * fp * (math.pi / 2.0 - math.atan(f_lo / fp))


def closed_one_pole_flicker_integral(k, fp, f_lo):
    """∫_{f_lo}^∞ (k/f)/(1 + (f/fp)²) df = (k/2)·ln(1 + (fp/f_lo)²)  (EF = 1)."""
    return 0.5 * k * math.log1p((fp / f_lo) ** 2)


def ref_poles(case, closed=False):
    """독립 극점: 미지수 노드 블록의 (G, C) 일반화 고유값 -s = G/C (전체 노드 어드미턴스를 직접 세움, conftest ref_system 과 같은 스탬프 규칙)."""
    from scipy.linalg import eigvals
    ix = case.ix
    n = len(case.nets)
    G = np.zeros((n, n))
    C = np.zeros((n, n))

    def two(M, a, b, y):
        M[a, a] += y
        M[b, b] += y
        M[a, b] -= y
        M[b, a] -= y

    for _n, a, b, v in case.res:
        two(G, ix[a], ix[b], 1.0 / v)
    for _n, a, b, v in case.cap:
        two(C, ix[a], ix[b], v)
    for t in case.mos:
        _nm, d, g, s, b, gm, gds = t[:7]
        cgs, cgd = (t[7], t[8]) if len(t) > 7 else (0.0, 0.0)
        for row, sg in ((ix[d], 1.0), (ix[s], -1.0)):
            G[row, ix[g]] += sg * gm
            G[row, ix[d]] += sg * gds
            G[row, ix[s]] -= sg * (gm + gds)
        if cgs:
            two(C, ix[g], ix[s], cgs)
        if cgd:
            two(C, ix[g], ix[d], cgd)
    fixed = {ix[g] for g in case.ground} | (set() if closed else {ix[case.inp]})
    unk = [i for i in range(n) if i not in fixed]
    lam = eigvals(-G[np.ix_(unk, unk)], C[np.ix_(unk, unk)])
    return tuple(complex(v) for v in lam if np.isfinite(v))
