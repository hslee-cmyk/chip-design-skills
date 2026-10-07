"""CONTRACT 3.9: phase_lag -- T(0) 대비 누적 지연(rad, 지연 양수). 칸마다 arg(T_k/T_{k−1}), |Δφ| ≥ π/2 면 중점을 풀어 세분
(π 를 넘는 지연도 언랩)."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import Factor, phase_lag, solve_responses

from .conftest import closed_miller, closed_single_pole, ex1_rc, ex2_amp, ex2_beta_res, ex3_miller


def _t(factors):
    out = None
    for f in factors:
        col = np.asarray(f.response.values)[:, f.row, f.column]
        out = col if out is None else out * col
    return out


def test_rc_lag_at_corner_and_beyond():
    (r,) = solve_responses((ex1_rc(),))
    f = (Factor(r, 0),)
    om, v = np.asarray(r.omegas), _t(f)
    for w in (1e6, math.sqrt(3.0) * 1e6, 1e8):
        lag, und = phase_lag(f, om, v, w, 1.0 / (1.0 + 1j * w * 1e-6), "lag")
        assert und is None
        assert lag == pytest.approx(math.atan(w * 1e-6), rel=1e-12)


def test_miller_lag_beyond_pi_unwrapped():
    ref = closed_miller()
    (r,) = solve_responses((ex3_miller(),))
    f = (Factor(r, 0),)
    om, v = np.asarray(r.omegas), _t(f)
    for w in (ref["ugf_hz"] * 2 * math.pi, 1e9, 1e11):
        exp = math.atan(w / ref["p1"]) + math.atan(w / ref["p2"]) + math.atan(w / ref["z"])
        lag, und = phase_lag(f, om, v, w, ref["h"](w), "lag")
        assert und is None
        assert lag == pytest.approx(exp, rel=1e-9)
    assert exp > math.pi                              # 1e11 에서 π 를 넘는다


def test_inverting_dc_reference_two_factor():
    # T(0) = −25(반전): 기준이 T(0) 이므로 지연은 단일 극 atan(ω/ωp) 만
    a0, wp = closed_single_pole()
    ra, rb = solve_responses((ex2_amp(), ex2_beta_res()))
    f = (Factor(ra, 0), Factor(rb, 0))
    om, v = np.asarray(ra.omegas), _t(f)
    w = 3e8
    t_end = a0 * 0.25 / (1.0 + 1j * w / wp)
    lag, und = phase_lag(f, om, v, w, t_end, "lag")
    assert und is None
    assert lag == pytest.approx(math.atan(w / wp), rel=1e-12)
