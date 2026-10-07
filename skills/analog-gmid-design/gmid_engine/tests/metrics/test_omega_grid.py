"""CONTRACT 3.5: omega_grid -- 0.0 + 양의 유한 |극점|·|영점| 꺾임점 + 인접 꺾임점 기하 중점, 오름차순·중복 없음, 꺾임점 없으면 (0.0,)."""
import math

import pytest

from gmid_engine.metrics import Roots, omega_grid


def _close_seq(a, b, rtol=1e-12):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert x == pytest.approx(y, rel=rtol, abs=0.0)


def test_no_roots_gives_zero_only():
    assert tuple(omega_grid((Roots((), ((),)),))) == (0.0,)


def test_single_pole():
    g = omega_grid((Roots((complex(-1e6, 0),), ((),)),))
    _close_seq(g, (0.0, 1e6))
    assert g[0] == 0.0


def test_breakpoints_and_geometric_midpoints():
    r = Roots((complex(-1e3, 0), complex(-1e5, 0)), ((complex(2e4, 0),),))
    g = omega_grid((r,))
    _close_seq(g, (0.0, 1e3, math.sqrt(1e3 * 2e4), 2e4, math.sqrt(2e4 * 1e5), 1e5))


def test_union_over_systems_sorted_unique():
    r1 = Roots((complex(-1e6, 0),), ((),))
    r2 = Roots((complex(-1e4, 0), complex(-1e6, 0)), ((complex(-1e6, 0),),))
    g = omega_grid((r1, r2))
    _close_seq(g, (0.0, 1e4, math.sqrt(1e4 * 1e6), 1e6))
    assert list(g) == sorted(set(g))


def test_complex_pair_counted_once_by_magnitude():
    p = complex(-3e5, 4e5)                       # |p| = 5e5
    g = omega_grid((Roots((p, p.conjugate()), ((),)),))
    _close_seq(g, (0.0, 5e5))


def test_origin_root_excluded():
    g = omega_grid((Roots((complex(0, 0), complex(-1e6, 0)), ((complex(0, 0),),)),))
    _close_seq(g, (0.0, 1e6))


def test_ascending_strict():
    r = Roots((complex(-7e2, 0), complex(-3e8, 0), complex(-2e2, 0)), ((complex(5e4, 0), complex(-9e9, 0)),))
    g = list(omega_grid((r,)))
    assert all(a < b for a, b in zip(g, g[1:]))
    assert len(g) == 1 + 5 + 4
