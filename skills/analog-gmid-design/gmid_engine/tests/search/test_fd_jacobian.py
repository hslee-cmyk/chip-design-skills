"""CONTRACT 3.11 [r2] `fd_jacobian` -- 스텝 식, 부호 뒤집기·방향 순서, skip(고정 열), 양방향 실패 (None, h), FD parent = base(I-4).

기대 스텝은 conftest `expected_fd_steps`(base 스냅샷 입력 열 + toy LUT 격자로 3.11 식을 독립 계산).
"""
import math

import pytest

from gmid_engine.search import ACCEPTED_STATUSES, evaluate, fd_jacobian
from gmid_engine.sizing import dc_columns, dc_currents

from .conftest import (
    CELLS_C,
    CELLS_P,
    build_case,
    circuit_c,
    circuit_p,
    expected_fd_steps,
    fixed_l,
    theta_p,
    theta_r4c,
    to_theta_fn,
    x_of,
)


def _setup(tmp_path, lut, th, topo=None, cells=CELLS_C, **kw):
    case = build_case(tmp_path, topo or circuit_c(), lut, **kw)
    s = case.sctx
    base = evaluate(s, tuple(sorted(th.items())), cells)
    vs = s.domain.variables
    return case, s, base, vs, x_of(vs, th), to_theta_fn(vs, fixed_l(th))


def test_steps_and_results(tmp_path, lut_sealed):
    th = theta_r4c(y=0.3)            # y + h 가 봉인 7 을 지키는 쪽(VDS(M2) 여유)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    exp = expected_fd_steps(s, base)
    k0 = dict(s.counters)["kernel_calls"]
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, ())
    assert len(out) == len(vs)
    for v, (res, h), he in zip(vs, out, exp):
        assert res is not None and res.status in ACCEPTED_STATUSES, v
        assert abs(h) == pytest.approx(he, rel=1e-12), v
        xi = list(x)
        i = vs.index(v)
        xi[i] = x[i] + h
        want = f(xi)[v.component]
        assert dict(res.theta)[v.component] == pytest.approx(want, rel=1e-14), v
        # 다른 성분은 그대로
        for u in vs:
            if u is not v:
                assert dict(res.theta)[u.component] == pytest.approx(dict(base.theta)[u.component], rel=1e-14)
    assert dict(s.counters)["kernel_calls"] == k0 + len(vs)


def test_positive_direction_first_when_inside(tmp_path, lut_sealed):
    th = theta_r4c(y=0.3)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    i = [v.component for v in vs].index(("y", "out"))
    skip = frozenset(j for j in range(len(vs)) if j != i)
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip)
    assert out[i][1] > 0


def test_sign_flips_at_upper_bound(tmp_path, lut_sealed):
    """y = 0.87: x + h > 1 -> h = −h 부터(M2 는 L 1 µm·vgs 0.1 -> VDsat 0.155 V < VDS 0.234 V, 봉인 7 통과)."""
    th = theta_r4c(y=0.87, v2=0.1, l2=1e-6)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th, cells=(0, 0))
    assert base.status in ACCEPTED_STATUSES
    i = [v.component for v in vs].index(("y", "out"))
    he = expected_fd_steps(s, base)[i]
    skip = frozenset(j for j in range(len(vs)) if j != i)
    res, h = fd_jacobian(s, vs, x, base, (0, 0), f, (), skip=skip)[i]
    assert res is not None
    assert h == pytest.approx(-he, rel=1e-12)


def test_skip_returns_base_without_evaluation(tmp_path, lut_sealed):
    th = theta_r4c(y=0.3)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    before = dict(s.counters)
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=frozenset(range(len(vs))))
    assert all(r is base and h == 0.0 for r, h in out)
    assert dict(s.counters) == before


def test_current_column_reuses_columns_block(tmp_path, lut_sealed):
    """I-4: FD parent = base -> current 열에서 sizing dc_columns computes 0 (DC 저항 없음), dc_currents 1."""
    th = theta_r4c(y=0.3)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    i = [v.component for v in vs].index(("current", "M2"))
    skip = frozenset(j for j in range(len(vs)) if j != i)
    c0, u0 = dc_columns.stats().computes, dc_currents.stats().computes
    res, h = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip)[i]
    assert res is not None and h != 0.0
    assert dc_columns.stats().computes == c0
    assert dc_currents.stats().computes == u0 + 1


def test_both_directions_out_of_bounds_gives_none(tmp_path, lut_sealed):
    """θ 저항 상자가 스텝보다 좁으면 h·−h 모두 bounds 밖 -> (None, h), 평가 없음."""
    r = 9e4
    rb = (r * (1 - 1e-9), r * (1 + 1e-9))
    case = build_case(tmp_path, circuit_p(), lut_sealed, elements=(("R1", "resistor", None),), rbounds=rb)
    s = case.sctx
    th = theta_p(case.dc, r=r)
    base = evaluate(s, tuple(sorted(th.items())), CELLS_P)
    assert base.status in ACCEPTED_STATUSES
    vs = s.domain.variables
    i = [v.component for v in vs].index(("resistance", "R1"))
    he = expected_fd_steps(s, base)[i]
    assert he > 2 * (math.log(rb[1]) - math.log(rb[0]))           # 손 확인: 스텝이 상자보다 크다
    skip = frozenset(j for j in range(len(vs)) if j != i)
    before = dict(s.counters)["requests"]
    res, h = fd_jacobian(s, vs, x_of(vs, th), base, CELLS_P, to_theta_fn(vs, fixed_l(th)), (), skip=skip)[i]
    assert res is None
    assert abs(h) == pytest.approx(he, rel=1e-12)
    assert dict(s.counters)["requests"] == before
