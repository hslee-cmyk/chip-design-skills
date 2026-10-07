"""CONTRACT 0절·2절·3.6: 결과 레코드 -- Undefined(quantity, code, category, detail), MetricResult, SystemResponse.dc = values[0].real."""
import numpy as np

from gmid_engine.metrics import (
    Factor,
    MetricResult,
    Roots,
    SystemResponse,
    Undefined,
    solve_responses,
)

from .conftest import ex1_rc


def test_undefined_fields():
    u = Undefined("ugf_hz", "dc_not_above_level", "definitional", (("dc_magnitude", 1.0),))
    assert (u.quantity, u.code, u.category, u.detail) == ("ugf_hz", "dc_not_above_level", "definitional",
                                                        (("dc_magnitude", 1.0),))
    assert Undefined("q", "singular_mna", "numeric").detail == ()


def test_metric_result_fields():
    r = MetricResult("gain_ss_db", 40.0)
    assert (r.name, r.value, r.undefined) == ("gain_ss_db", 40.0, ())
    u = Undefined("ugf_hz", "dc_not_above_level", "definitional")
    r2 = MetricResult("ugf_ss_hz", None, (u,))
    assert r2.value is None and r2.undefined == (u,)


def test_system_response_dc_is_real_part_of_first_row():
    sysm = ex1_rc()
    vals = np.array([[2.0 + 0.0j], [0.5 - 0.5j]])
    r = SystemResponse(sysm, Roots((), ((),)), np.array([0.0, 1e6]), vals)
    assert np.array_equal(np.asarray(r.dc), np.array([2.0]))


def test_system_response_dc_from_solve():
    (r,) = solve_responses((ex1_rc(),))
    assert np.array_equal(np.asarray(r.dc), np.asarray(r.values)[0].real)


def test_factor_holds_response_and_column():
    (r,) = solve_responses((ex1_rc(),))
    f = Factor(r, 0)
    assert f.response is r and f.column == 0
