"""`_helpers_product.product_at` (비공개) -- 인수 곱 T(ω) = Π Factor 를 새 ω 에서 실제로 풀어 곱한다.
공개 경로(find_crossing·analyze_loop 의 격자 밖 세분 풀이)로 확인한다: 격자 밖 교차값이 폐형식 인수 곱과 같아야 한다."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import Factor, analyze_loop, find_crossing, solve_responses

from .conftest import closed_single_pole, ex2_amp, ex2_beta_res, ex2c_beta_cap


def _t(factors):
    out = None
    for f in factors:
        col = np.asarray(f.response.values)[:, f.row, f.column]
        out = col if out is None else out * col
    return out


def test_three_factor_product_off_grid():
    a0, wp = closed_single_pole()
    ra, rb, rc = solve_responses((ex2_amp(), ex2_beta_res(), ex2c_beta_cap()))
    f = (Factor(ra, 0), Factor(rb, 0), Factor(rc, 0))
    t0 = abs(a0) * 0.25 * 0.25                     # 6.25
    c = find_crossing(f, np.asarray(ra.omegas), _t(f), 1.0, "ugf")
    assert c.undefined is None
    assert c.omega == pytest.approx(wp * math.sqrt(t0 * t0 - 1.0), rel=1e-10)
    # 교차점 값 = 폐형식 인수 곱
    exp = a0 * 0.25 * 0.25 / (1.0 + 1j * c.omega / wp)
    assert complex(c.value) == pytest.approx(exp, rel=1e-9)


def test_product_uses_requested_columns():
    # A 계 iout 열(ro/(1+sτ)) × β: T0 = 1e5·0.25
    a0, wp = closed_single_pole()
    ra, rb = solve_responses((ex2_amp(), ex2_beta_res()))
    la = analyze_loop((Factor(ra, 1), Factor(rb, 0)))
    assert la.dc_value == pytest.approx(1e5 * 0.25, rel=1e-12)
    t0 = 1e5 * 0.25
    assert la.ugf_hz == pytest.approx(wp * math.sqrt(t0 * t0 - 1.0) / (2 * math.pi), rel=1e-9)
