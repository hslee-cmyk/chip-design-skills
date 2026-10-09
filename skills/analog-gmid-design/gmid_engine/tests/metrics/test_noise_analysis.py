"""[U8 2026-10-09] `noise_analysis(field, setup, memo)` -- 입력 환산 열잡음 평탄값·1/f corner·excess (설계 41 §7.1·7.3, metrics CONTRACT 10.1~10.3).

oracle (기대값마다 아래 주석에 종류를 적는다):
* (a) 폐형식: 저항 분압기 th_in = 4kT(Ra‖Rb)/H0²(C 가 있어도 비가 주파수 무관), 단일 CS(cgd = 0)는 W = |Z/H|² = 1/gm² 이라 th_in = B,
  corner = (A/B)^(1/EF); 부하 MOS 의 잡음 전류는 입력 MOS 와 같은 출력 노드로 들어가 excess = 1 + gm2²B2/(gm1²B1).
* (b) 독립 노드 해석(noise_cases `Case.ref_*` -- conftest `ref_system`)과 scipy brentq: cgd 가 있어 W(f) 가 주파수에 따라 변하는 회로의 corner.
* (d) 계약 10.3 사유 어휘(`noise_fc_below_f_lo`·`noise_flicker_zero`·`noise_thermal_unknown`·`noise_input_cell_*`·`noise_f_lo_undefined`·
  `noise_transfer_view_missing`·`noise_device_missing`·`noise_lut_query_failed`).
피검 함수로 기대값을 만들지 않는다.
"""
import math

import pytest
from scipy.optimize import brentq

from gmid_engine.metrics import NoiseAnalysis, noise_analysis

from .noise_cases import F_LO, KT, TWO_PI, Case, closed_divider_th_in, codes, detail, dev, setup_of

RA, RB, C_OUT = 2e3, 2e3, 1e-9                 # CONTRACT 10.5 의 손 RC 와 같은 값(오라클 conftest RC)
GM, GDS, CL = 1e-4, 1e-6, 1e-12
A0, B0 = 1e-12, 1e-16                          # lut CONTRACT 9.6 toy 값


def divider(names=None):
    return Case(res=(("Ra", "in", "out", RA), ("Rb", "out", "gnd", RB)), cap=(("C", "out", "gnd", C_OUT),), names=names)


def cs(cgd=0.0, load=None):
    """M1 nmos (d=out, g=in, s=gnd), CL. load = (gm2, gds2) 이면 M2 (d=out, g=gnd, s=gnd) -- 게이트·소스가 모두 교류접지라 gm2 는 스탬프 효과가 없고
    잡음 전류만 out 에 들어간다."""
    mos = [("M1", "out", "in", "gnd", "gnd", GM, GDS, 0.0, cgd)]
    if load is not None:
        mos.append(("M2", "out", "gnd", "gnd", "gnd", load[0], load[1]))
    return Case(mos=tuple(mos), cap=(("CL", "out", "gnd", CL),))


# ---------------------------------------------------------------- noise_th_in_v2hz

def test_divider_th_in_is_4kt_rp_over_h0_squared():
    s = setup_of(divider())
    r = noise_analysis("th_in_v2hz", s, {})
    assert isinstance(r, NoiseAnalysis) and r.undefined == ()
    # oracle (a): 4kT(Ra‖Rb)/H0² -- C 가 있어도 출력 잡음과 H 가 같은 극을 가져 비는 주파수 무관(f_lo 에서 재도 같다)
    assert math.isclose(r.th_in_v2hz, closed_divider_th_in(RA, RB), rel_tol=1e-12)
    # 요청한 필드만 채운다(계약 10절 결과 형식)
    assert (r.fc_in_hz, r.excess_th, r.out_int_vrms) == (None, None, None)
    assert detail(r)["f_lo_hz"] == F_LO


def test_divider_contrib_shares():
    """소자별 기여: Ra 의 출력 잡음 = (4kT/Ra)·Rp²/|1+jωRpC|², 입력 환산 = 4kT·Rp²/(Ra·H0²) -> 몫 Rp/Ra. oracle (a)."""
    ra, rb = 1e3, 3e3
    case = Case(res=(("Ra", "in", "out", ra), ("Rb", "out", "gnd", rb)), cap=(("C", "out", "gnd", C_OUT),))
    r = noise_analysis("th_in_v2hz", setup_of(case), {})
    rp = ra * rb / (ra + rb)
    h0 = rb / (ra + rb)
    got = {name: dict(kv) for name, kv in r.contrib}
    assert set(got) == {"Ra", "Rb"}
    assert math.isclose(got["Ra"]["share"], rp / ra, rel_tol=1e-12)
    assert math.isclose(got["Rb"]["share"], rp / rb, rel_tol=1e-12)
    assert math.isclose(got["Ra"]["thermal"], 4 * KT * rp ** 2 / (ra * h0 ** 2), rel_tol=1e-12)
    assert got["Ra"]["flicker"] == 0.0 and got["Rb"]["flicker"] == 0.0          # 저항은 flicker 없음(계약 10.1)


def test_cs_th_in_is_gate_referred_b_and_resolution_is_tol_share():
    """단일 CS, cgd = 0: W = 1/gm² 라 th_in = gm²B/gm² = B (gds·CL 무관). oracle (a).
    분해능(계약 10.2): q = B 는 gm·gds 에 의존하지 않아 파라미터 몫 0, 허용오차 몫 = tol_thermal·q."""
    s = setup_of(cs(), (dev("M1", a=A0, b=B0, tol_thermal=0.05, tol_flicker=0.1),), rel_tol=0.02)
    r = noise_analysis("th_in_v2hz", s, {})
    assert math.isclose(r.th_in_v2hz, B0, rel_tol=1e-12)
    assert r.resolution == pytest.approx(0.05 * B0, rel=1e-9, abs=1e-30)


def test_th_in_resolution_undetermined_when_lut_tol_missing():
    """계약 10.2: 어느 한 불확실성이 미정(ParameterSet.undetermined)이면 분해능 None -- 값은 낸다. oracle (d)."""
    s = setup_of(cs(), (dev("M1", a=A0, b=B0, tol_thermal=0.05, tol_flicker=0.1),), rel_tol=None)
    r = noise_analysis("th_in_v2hz", s, {})
    assert math.isclose(r.th_in_v2hz, B0, rel_tol=1e-12)
    assert r.resolution is None


# ---------------------------------------------------------------- noise_fc_in_hz

@pytest.mark.parametrize("ef", [1.0, 0.84])
def test_cs_corner_is_a_over_b_root(ef):
    """구성한 S_vg = A/f^EF + B, 단일 CS(cgd = 0 -> W 상수): corner f_c = (A/B)^(1/EF). oracle (a)."""
    s = setup_of(cs(), (dev("M1", a=A0, b=B0, ef=ef),))
    r = noise_analysis("fc_in_hz", s, {})
    assert r.undefined == ()
    assert math.isclose(r.fc_in_hz, (A0 / B0) ** (1.0 / ef), rel_tol=1e-9)


def test_corner_two_devices_different_ef():
    """입력 nmos(EF 0.84) + 부하 pmos 자리(EF 1.0): W 가 둘 다 1/gm1² 이라 Q_fl(f) = (gm1²A1/f^0.84 + gm2²A2/f)/gm1²,
    Q_th = (gm1²B1 + gm2²B2)/gm1². 근은 brentq 로 따로 푼다. oracle (a)+(b)."""
    gm2 = 5e-5
    a1, b1, a2, b2 = 2e-12, 1e-16, 4e-11, 3e-16
    s = setup_of(cs(load=(gm2, 1e-6)), (dev("M1", a=a1, b=b1, ef=0.84), dev("M2", a=a2, b=b2, ef=1.0)))
    r = noise_analysis("fc_in_hz", s, {})
    q_th = GM ** 2 * b1 + gm2 ** 2 * b2

    def g(x):
        f = math.exp(x)
        return math.log(GM ** 2 * a1 / f ** 0.84 + gm2 ** 2 * a2 / f) - math.log(q_th)

    expect = math.exp(brentq(g, 0.0, 60.0, xtol=1e-14, rtol=1e-15))
    assert math.isclose(r.fc_in_hz, expect, rel_tol=1e-8)


def test_corner_with_frequency_dependent_weight():
    """cgd > 0: H = −(gm − jωcgd)/Y, Z = 1/Y 라 W(f) = 1/|gm − jωcgd|² 가 corner 근처에서 변한다. 기준은 독립 노드 해석(conftest ref_system)으로
    W(f) = |Z/H|² 를 풀고 Q_fl(f) = W(f)·gm²A/f = Q_th = W(f_lo)·gm²B 를 brentq 로 푼다(계약 10.1: Q_th 는 f_lo 값). oracle (b)."""
    cgd = 1e-12                                    # ωcgd = gm 인 f = gm/(2πcgd) ≈ 1.6e7 Hz
    a, b = 1e-9, 1e-16                             # W 가 상수라면 corner 1e7 Hz -- 그 근처에서 W 가 줄어든다
    case = cs(cgd=cgd)
    s = setup_of(case, (dev("M1", a=a, b=b),))
    r = noise_analysis("fc_in_hz", s, {})

    def w(f):
        om = TWO_PI * f
        return abs(case.ref_z("out", "gnd", om)) ** 2 / abs(case.ref_h(om)) ** 2

    q_th = w(F_LO) * GM ** 2 * b
    expect = math.exp(brentq(lambda x: math.log(w(math.exp(x)) * GM ** 2 * a / math.exp(x)) - math.log(q_th),
                             math.log(1e5), math.log(1e9), xtol=1e-13, rtol=1e-14))
    assert not math.isclose(expect, a / b, rel_tol=1e-3)     # 구성 확인: W 변화가 corner 를 실제로 옮긴다
    assert math.isclose(r.fc_in_hz, expect, rel_tol=1e-7)


@pytest.mark.parametrize("ef", [1.0, 0.84])
def test_corner_resolution_closed_form(ef):
    """계약 10.2 corner 분해능: δ ln f = (Σ|∂g/∂p|Δp + 허용오차 몫)/|∂ln Q_fl/∂ln f|. 단일 CS(cgd = 0)는 W·S 의 gm 의존이 상쇄돼 파라미터 몫 0,
    허용오차 몫 = tol_flicker + tol_thermal(성분 하나라 몫 1), 기울기 = EF -> 분해능 = f_c·(tol_fl + tol_th)/EF. oracle (a)."""
    t_fl, t_th = 0.1, 0.05
    s = setup_of(cs(), (dev("M1", a=A0, b=B0, ef=ef, tol_flicker=t_fl, tol_thermal=t_th),), rel_tol=0.02)
    r = noise_analysis("fc_in_hz", s, {})
    f_c = (A0 / B0) ** (1.0 / ef)
    assert r.resolution == pytest.approx(f_c * (t_fl + t_th) / ef, rel=1e-6)


def test_excess_resolution_closed_form():
    """계약 10.2 excess 분해능 = excess × (Σ|∂ln(Q_th/Q_in)/∂p|Δp + Σ_k tol_k·|th_k/Q_th − [k∈입력]·th_k/Q_in|). Δp = 0(rel_tol 0) 이면
    파라미터 몫 0, excess = 2 인 두 소자(몫 1/2 씩)는 허용오차 몫 = (t1 + t2)/2. oracle (a)."""
    gm2, t1, t2 = 5e-5, 0.04, 0.2
    b2 = GM ** 2 * B0 / gm2 ** 2
    s = setup_of(cs(load=(gm2, 1e-6)), (dev("M1", a=A0, b=B0, tol_thermal=t1, tol_flicker=0.0),
                                        dev("M2", a=0.0, b=b2, tol_thermal=t2, tol_flicker=0.0)),
                 input_devices=("M1",), rel_tol=0.0)
    r = noise_analysis("excess_th", s, {})
    assert r.excess_th == pytest.approx(2.0, rel=1e-12)
    assert r.resolution == pytest.approx(2.0 * (t1 + t2) / 2, rel=1e-9)


def test_corner_below_f_lo_reason():
    """f_lo 에서 이미 Q_fl < Q_th(A < B·f_lo^EF) -> `noise_fc_below_f_lo`(값 없음). oracle (a) 구성 + (d) 계약 10.1·10.3."""
    s = setup_of(cs(), (dev("M1", a=0.5 * B0 * F_LO, b=B0),))
    r = noise_analysis("fc_in_hz", s, {})
    assert r.fc_in_hz is None
    assert codes(r) == ("noise_fc_below_f_lo",)


def test_corner_flicker_zero_reason():
    """flicker 합 0(저항만, 또는 A = 0) -> `noise_flicker_zero`. oracle (d) 계약 10.1."""
    assert codes(noise_analysis("fc_in_hz", setup_of(divider()), {})) == ("noise_flicker_zero",)
    assert codes(noise_analysis("fc_in_hz", setup_of(cs(), (dev("M1", a=0.0, b=B0),)), {})) == ("noise_flicker_zero",)


# ---------------------------------------------------------------- noise_excess_th

def test_excess_input_cell_only_is_one():
    """입력 셀 소자만 잡음을 내면(부하 a = b = 0) excess = 1. oracle (a)."""
    s = setup_of(cs(load=(5e-5, 1e-6)), (dev("M1", a=A0, b=B0), dev("M2", a=0.0, b=0.0)), input_devices=("M1",))
    r = noise_analysis("excess_th", s, {})
    assert r.undefined == ()
    assert r.excess_th == pytest.approx(1.0, rel=1e-12)
    assert detail(r)["input_cell"] == ("M1",)


def test_excess_equal_load_noise_is_two():
    """부하 잡음 전류 gm2²B2 = gm1²B1 -> excess = 1 + gm2²B2/(gm1²B1) = 2 (41 §7.1 가드 경계 '부하 잡음 ≤ 입력 잡음'). oracle (a)."""
    gm2 = 5e-5
    b2 = GM ** 2 * B0 / gm2 ** 2
    s = setup_of(cs(load=(gm2, 1e-6)), (dev("M1", a=A0, b=B0), dev("M2", a=0.0, b=b2)), input_devices=("M1",))
    assert noise_analysis("excess_th", s, {}).excess_th == pytest.approx(2.0, rel=1e-12)


def test_excess_counts_resistor_noise():
    """입력 셀 밖의 저항도 분자에 든다(41 §7.3 포함 범위: 모든 MOS 와 저항). 출력 저항 RL(out-gnd): 잡음 전류 4kT/RL 이 같은 노드로 ->
    excess = 1 + (4kT/RL)/(gm²B). oracle (a)."""
    rl = 1e5
    case = Case(mos=(("M1", "out", "in", "gnd", "gnd", GM, GDS),), res=(("RL", "out", "gnd", rl),), cap=(("CL", "out", "gnd", CL),))
    s = setup_of(case, (dev("M1", a=A0, b=B0),), input_devices=("M1",))
    assert noise_analysis("excess_th", s, {}).excess_th == pytest.approx(1.0 + (4 * KT / rl) / (GM ** 2 * B0), rel=1e-12)


@pytest.mark.parametrize("inputs, code", [(None, "noise_input_cell_undefined"), ((), "noise_input_cell_undefined"),
                                          (("Mx",), "noise_input_cell_not_in_circuit")])
def test_excess_input_cell_reasons(inputs, code):
    """입력 셀 미정·회로에 없음 -> 정의 불가(조용히 통과하지 않는다). oracle (d) 계약 10.3·search 11절."""
    s = setup_of(cs(), (dev("M1", a=A0, b=B0),), input_devices=inputs)
    r = noise_analysis("excess_th", s, {})
    assert r.excess_th is None and codes(r) == (code,)


def test_excess_input_cell_noise_zero_reason():
    s = setup_of(cs(load=(5e-5, 1e-6)), (dev("M1", a=0.0, b=0.0), dev("M2", a=0.0, b=B0)), input_devices=("M1",))
    assert codes(noise_analysis("excess_th", s, {})) == ("noise_input_cell_noise_zero",)


# ---------------------------------------------------------------- 정의 불가 사유 (계약 10.3)

@pytest.mark.parametrize("field", ["th_in_v2hz", "fc_in_hz", "excess_th"])
def test_thermal_unknown_withholds_value(field):
    """LUT B 미상 -> 값 없음 + `noise_thermal_unknown`(소자 이름) -- 오케스트레이터 결정: 설계의 '분해능 무한대·판정 보류'의 fail-closed 등가. oracle (d)."""
    s = setup_of(cs(), (dev("M1", a=A0, b=None),), input_devices=("M1",))
    r = noise_analysis(field, s, {})
    assert getattr(r, field) is None
    assert codes(r) == ("noise_thermal_unknown",)
    assert dict(r.undefined[0].detail)["devices"] == ("M1",)


@pytest.mark.parametrize("devices, code", [((), "noise_device_missing"),
                                           ((dev("M1", failure="lut_l_out_of_range"),), "noise_lut_query_failed")])
def test_device_problems_reported(devices, code):
    r = noise_analysis("th_in_v2hz", setup_of(cs(), devices), {})
    assert r.th_in_v2hz is None and code in codes(r)


def test_f_lo_undefined_and_view_missing():
    r = noise_analysis("th_in_v2hz", setup_of(cs(), (dev("M1", a=A0, b=B0),), f_lo=None), {})
    assert codes(r) == ("noise_f_lo_undefined",)
    r = noise_analysis("th_in_v2hz", setup_of(cs(), (dev("M1", a=A0, b=B0),), column=None), {})
    assert codes(r) == ("noise_transfer_view_missing",)


def test_memo_shares_reference_between_metrics():
    """세 metric 이 같은 memo 를 쓰면 같은 값(계약 10.4 '같은 계 키·같은 열'). 공유한 memo 와 새 memo 의 결과가 같다. oracle (a): th_in = B."""
    s = setup_of(cs(), (dev("M1", a=A0, b=B0),), input_devices=("M1",))
    memo = {}
    first = noise_analysis("th_in_v2hz", s, memo)
    noise_analysis("fc_in_hz", s, memo)
    again = noise_analysis("th_in_v2hz", s, memo)
    assert first.th_in_v2hz == again.th_in_v2hz == noise_analysis("th_in_v2hz", s, {}).th_in_v2hz
    assert math.isclose(first.th_in_v2hz, B0, rel_tol=1e-12)


def test_name_bijection_invariance():
    """넷·소자 이름 전단사와 노드 번호 순서를 바꿔도 값이 같다(이름이 아니라 구조로 정해진다). 기준 = 원래 이름 회로의 폐형식. oracle (a)."""
    names = {"in": "zz_in", "out": "aa_out", "gnd": "mm_gnd", "Ra": "R9", "Rb": "R0", "C": "Cq"}
    base = Case(res=(("Ra", "in", "out", RA), ("Rb", "out", "gnd", RB)), cap=(("C", "out", "gnd", C_OUT),))
    moved = Case(res=(("Ra", "in", "out", RA), ("Rb", "out", "gnd", RB)), cap=(("C", "out", "gnd", C_OUT),), names=names,
                 order=("out", "gnd", "in"))
    a = noise_analysis("th_in_v2hz", setup_of(base), {})
    b = noise_analysis("th_in_v2hz", setup_of(moved), {})
    assert math.isclose(a.th_in_v2hz, closed_divider_th_in(RA, RB), rel_tol=1e-12)
    assert math.isclose(b.th_in_v2hz, a.th_in_v2hz, rel_tol=1e-12)
    assert {names[n]: dict(kv)["share"] for n, kv in a.contrib} == pytest.approx({n: dict(kv)["share"] for n, kv in b.contrib},
                                                                                 rel=1e-12)
