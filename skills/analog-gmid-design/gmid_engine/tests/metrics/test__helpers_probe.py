"""`_helpers_probe.probe_value` (비공개) -- Middlebrook T 한 점 평가·사후 오차(`probe_loop`·`_helpers_product` 공용).
공개 경로로 확인한다: find_crossing 은 격자 밖 점(이분 중점·상단 괄호)을 `product_at` -> `probe_value` 로 실제로 풀고,
그 교차 ω·교차값이 폐형식 T 와 같아야 한다(CONTRACT 3.8·3.17 '격자 밖 한 점 -> (복소값, 사후 오차, 사유)').
기대값: conftest 폐형식(`closed_ex7`·`closed_ex7b`)."""
import math

import numpy as np
import pytest

from gmid_engine.metrics import Factor, LoopCut, build_mna, cut_circuit, find_crossing, probe_factor, solve_responses

from .conftest import EX7_CUT, EX7B_CUTS, circuit_of, closed_ex7, closed_ex7b, codes, ex2_beta_res, ex7_parts, ex7b_parts


def _pf(parts, cuts, weights, extra=()):
    cut = cut_circuit(circuit_of(*parts), tuple(LoopCut(*c) for c in cuts))
    rs = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),) + tuple(extra))
    return probe_factor(rs[0], cut.pairs, weights), rs[1:]


def _cross(factors, level, values):
    om = np.asarray(factors[0].response.omegas)
    return find_crossing(factors, om, values, level, "q")


@pytest.mark.parametrize("level", [1.0, 3.0, 12.5, 0.01, 1e-3])
def test_off_grid_crossing_value_is_closed_form_t(level):
    """|T| = level 교차: 격자 안(1·3·12.5)과 격자 끝 밖(0.01·1e-3 -- 상단 괄호를 T 극점·영점으로 유도) 모두
    교차 ω = ω_p·√((T0/level)² − 1), 교차값 = 폐형식 T(jω)."""
    ref = closed_ex7()
    pf, _ = _pf(ex7_parts(), EX7_CUT, (1.0,))
    c = _cross((pf,), level, np.asarray(pf.samples))
    assert c.undefined is None
    exp_w = ref["wp"] * math.sqrt((ref["t0"] / level) ** 2 - 1.0)
    assert c.omega == pytest.approx(exp_w, rel=1e-11)
    assert complex(c.value) == pytest.approx(ref["t"](c.omega), rel=1e-11)
    assert abs(abs(complex(c.value)) - level) <= 1e-11 * level


def test_mixed_probe_and_factor_product_off_grid():
    """3.8: Factor 와 ProbeFactor 를 섞어 묶는다 -- T = T_ex7 × β(0.25, 저항 분압 계), T0 = 6.25."""
    ref = closed_ex7()
    pf, (rb,) = _pf(ex7_parts(), EX7_CUT, (1.0,), extra=(ex2_beta_res(),))
    fb = Factor(rb, 0)
    vals = np.asarray(pf.samples) * np.asarray(rb.values)[:, 0, 0]
    c = _cross((pf, fb), 1.0, vals)
    t0 = 0.25 * ref["t0"]
    assert c.undefined is None
    assert c.omega == pytest.approx(ref["wp"] * math.sqrt(t0 * t0 - 1.0), rel=1e-11)
    assert complex(c.value) == pytest.approx(0.25 * ref["t"](c.omega), rel=1e-11)


@pytest.mark.parametrize("mode,weights", [("dm", (0.5, -0.5)), ("cm", (0.5, 0.5))])
def test_two_cut_off_grid_crossing(mode, weights):
    ref = closed_ex7b(mode)
    pf, _ = _pf(ex7b_parts(), EX7B_CUTS, weights)
    for level in (1.0, 0.5):
        c = _cross((pf,), level, np.asarray(pf.samples))
        assert c.undefined is None
        assert c.omega == pytest.approx(ref["wp"] * math.sqrt((ref["t0"] / level) ** 2 - 1.0), rel=1e-11)


def test_posterior_error_reported_nonnegative_and_small():
    """사후 오차(Z 원소 오차의 1차 전파)는 정지 판정에 쓰인다 -- 교차 결과의 resolution 은 유한·비음·|T| 대비 작다."""
    pf, _ = _pf(ex7_parts(), EX7_CUT, (1.0,))
    c = _cross((pf,), 1.0, np.asarray(pf.samples))
    assert c.resolution is not None and math.isfinite(c.resolution) and c.resolution >= 0.0
    assert c.resolution <= 1e-9


def test_mixed_cut_dc_nan_is_crossing_undefined():
    """예 7c: T(0) NaN(loop_cut_mixed_charge) -> 교차는 정의 불가 값(예외 없음). find_crossing 단독에 NaN 표본을 주었을 때의
    사유 code 는 3.8 이 정하지 않는다(사유 전파는 3.10 analyze_loop 몫 -- test_probe_loop 예 7c 가 확인)."""
    pf, _ = _pf(ex7_parts(cs_resistor=True), EX7_CUT, (1.0,))
    c = _cross((pf,), 1.0, np.asarray(pf.samples))
    assert c.omega is None and c.value is None
    assert codes(c.undefined)
