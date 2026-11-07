"""CONTRACT 3.11 [r2] `fd_jacobian` -- 스텝 식, 부호 뒤집기·방향 순서, skip(고정 열), 양방향 실패 (None, h), FD parent = base(I-4).

기대 스텝은 conftest `expected_fd_steps`(base 스냅샷 입력 열 + toy LUT 격자로 3.11 식을 독립 계산).
"""
import math

import pytest

from gmid_engine.search import ACCEPTED_STATUSES, fd_jacobian
from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
from gmid_engine.sizing import dc_solve, dc_currents

from .conftest import block_row  # [XRUN-F1 card B C1]
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
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), ceiling=None)
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
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip, ceiling=None)
    assert out[i][1] > 0


def test_sign_flips_at_upper_bound(tmp_path, lut_sealed):
    """y = 0.87: x + h > 1 -> h = −h 부터(M2 는 L 1 µm·vgs 0.1 -> VDsat 0.155 V < VDS 0.234 V, 봉인 7 통과)."""
    th = theta_r4c(y=0.87, v2=0.1, l2=1e-6)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th, cells=(0, 0))
    assert base.status in ACCEPTED_STATUSES
    i = [v.component for v in vs].index(("y", "out"))
    he = expected_fd_steps(s, base)[i]
    skip = frozenset(j for j in range(len(vs)) if j != i)
    res, h = fd_jacobian(s, vs, x, base, (0, 0), f, (), skip=skip, ceiling=None)[i]
    assert res is not None
    assert h == pytest.approx(-he, rel=1e-12)


def test_skip_returns_base_without_evaluation(tmp_path, lut_sealed):
    th = theta_r4c(y=0.3)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    before = dict(s.counters)
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=frozenset(range(len(vs))), ceiling=None)
    assert all(r is base and h == 0.0 for r, h in out)
    assert dict(s.counters) == before


def test_current_column_recomputes_dc_solve_once(tmp_path, lut_sealed):
    """I-4 [WB-1 갱신]: FD parent = base -> current 열에서 dc_currents 1회, dc_solve 1회(노드 풀이와 W 가 한 블록이고 dc_current 를 읽는다 -- 옛 '노드 풀이 블록 재계산 0' 은
    블록 분할 소멸로 사라진 계약, G-10: 같은 입력 재계산은 0 이므로 각 블록 정확히 1회)."""
    th = theta_r4c(y=0.3)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    i = [v.component for v in vs].index(("current", "M2"))
    skip = frozenset(j for j in range(len(vs)) if j != i)
    # [XRUN-F1 card B C1·C6] 계수 = 그 탐색 컨텍스트 실행(sctx.dc.counters)의 행 computes(인덱스 4)
    c0, u0 = block_row(s.dc.counters, dc_solve.name)[4], block_row(s.dc.counters, dc_currents.name)[4]
    res, h = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip, ceiling=None)[i]
    assert res is not None and h != 0.0
    assert block_row(s.dc.counters, dc_solve.name)[4] == c0 + 1
    assert block_row(s.dc.counters, dc_currents.name)[4] == u0 + 1


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
    res, h = fd_jacobian(s, vs, x_of(vs, th), base, CELLS_P, to_theta_fn(vs, fixed_l(th)), (), skip=skip, ceiling=None)[i]
    assert res is None
    assert abs(h) == pytest.approx(he, rel=1e-12)
    assert dict(s.counters)["requests"] == before


@pytest.mark.parametrize("grid_um, grid_m", [("0.01", 1e-8), ("0.005", 5e-9)])
def test_l_step_is_one_manufacturing_grid(tmp_path, lut_sealed, grid_um, grid_m):
    """[r5·r8] L 열 스텝 = PDK 제조 격자 한 칸 `domain.grid_m`(앵커 간격 1 µm 가 아님). L 변수(칸 [1, 2] µm)를 넘겨
    아래 끝에서 +grid, 위 끝에서 −grid(x + h > hi 면 부호 뒤집기). 평가 성공·실패와 무관하게 돌려준 스텝 크기 = grid."""
    from gmid_engine.search import Variable

    from .conftest import write_pdk
    pdk = write_pdk(tmp_path / ("g" + grid_um.replace(".", "")), grid_um=grid_um)
    th = theta_r4c(y=0.3)
    case = build_case(tmp_path, circuit_c(), lut_sealed, pdk=pdk)
    s = case.sctx
    assert s.domain.grid_m == pytest.approx(grid_m, rel=1e-12)
    base = evaluate(s, tuple(sorted(th.items())), CELLS_C)
    assert base.status in ACCEPTED_STATUSES
    lv = (Variable(("L", "M1"), False, 1e-6, 2e-6),)
    fixed = {k: v for k, v in th.items() if k != ("L", "M1")}
    f = to_theta_fn(lv, fixed)
    for x0, sign in ((1e-6, 1.0), (2e-6, -1.0)):
        res, h = fd_jacobian(s, lv, (x0,), base, CELLS_C, f, (), ceiling=None)[0]
        assert h == pytest.approx(sign * grid_m, rel=1e-6), (x0, h)
        if res is not None:
            assert dict(res.theta)[("L", "M1")] == pytest.approx(x0 + h, rel=1e-15)


def test_passive_theta_step_is_min_tol_gm_id(tmp_path, lut_sealed):
    """r6: DEC-92 θ(capacitance·ss_resistance, ln 좌표) 스텝 = 전 MOS dc_tol_v·gm_id 최솟값."""
    from .conftest import evaluate      # [FS-1 서명 맞춤] 손 wf 를 끼운 evaluate 래퍼
    from .conftest import CELLS_C, Z_ELEMENTS, circuit_z, col, snap_of, theta_z
    case = build_case(tmp_path, circuit_z(), lut_sealed, elements=Z_ELEMENTS, rbounds=(1e2, 1e6), cbounds=(1e-14, 1e-10))
    s = case.sctx
    th = theta_z(case.dc, y=0.3)
    base = evaluate(s, tuple(sorted(th.items())), CELLS_C)
    assert base.status in ACCEPTED_STATUSES
    snap = snap_of(base)
    ops, tol = col(snap, "device", "dc_op"), col(snap, "device", "dc_tol_v")
    hand = min(tol[m] * ops[m].gm_id for m in ops)
    vs = s.domain.variables
    f = to_theta_fn(vs, fixed_l(th))
    x = x_of(vs, th)
    for comp in (("capacitance", "Cz"), ("ss_resistance", "Rz")):
        i = [v.component for v in vs].index(comp)
        skip = frozenset(j for j in range(len(vs)) if j != i)
        res, h = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip, ceiling=None)[i]
        assert res is not None and res.status in ACCEPTED_STATUSES
        assert abs(h) == pytest.approx(hand, rel=1e-12)
        xi = list(x)
        xi[i] = x[i] + h
        assert dict(res.theta)[comp] == pytest.approx(f(xi)[comp], rel=1e-14)


def test_it2b_y_step_is_the_w4_root_window_width_only(tmp_path, lut_sealed):
    """[card IT-2b T-FD, design 41 4.7-6] `node.dc_window` 에 입력 포트 항목이 늘어도 y 스텝 색인·크기는 W4 뿌리 창 폭만으로 정해진다.
    oracle 대조: (식) 3.11 스텝 식 d/(hi − lo) (d = r4 VDS 격자 최소 간격 0.25 V, 손으로 읽은 LUT 격자) 에 회로 C 의 손계산 창을 넣는다:
    W4 뿌리 out 의 창 = 레일 [0, 1.8](폭 1.8). 입력 포트 in 은 M1 gate, source = gnd 라 F 성분 미선언 포트 -- IT-2b 뒤에는 그 항목이 `node.dc_window` 에
    들어오지만(lo·hi None) y 변수는 out 하나뿐이고 스텝은 0.25/1.8 그대로여야 한다. base·head 모두 통과(green 유지)."""
    th = theta_r4c(y=0.3)
    case, s, base, vs, x, f = _setup(tmp_path, lut_sealed, th)
    y_vars = [v.component for v in vs if v.component[0] == "y"]
    assert y_vars == [("y", "out")]                                       # 입력 포트 항목은 y 키를 만들지 않는다
    i = [v.component for v in vs].index(("y", "out"))
    skip = frozenset(j for j in range(len(vs)) if j != i)
    res, h = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip, ceiling=None)[i]
    assert res is not None and res.status in ACCEPTED_STATUSES
    assert abs(h) == pytest.approx(0.25 / 1.8, rel=1e-12)


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C4 (C-T5) -- 필수 키워드 `ceiling`, 상계 = 평가할 열 수 × 2, 남은 한도 = ceiling − kernel_calls.
# oracle: (손) 구성 -- 평가할 열 수 m = len(vs) − len(skip) (이 입력에서 스텝 0·None 열이 없음을 위 test_steps_and_results 가 보인다: 열마다 결과 1개,
# 커널 +1). 상계 = 2m. ceiling 은 kernel_calls + 상계(= 남은 한도 = 상계: 평상 실행)·그보다 1 작게(= 상계 − 1: 평가 0, needed = 상계,
# remaining = 상계 − 1)로 정한다. 피검 식을 다시 쓰지 않는다.
# =====================================================================================================================

import importlib  # noqa: E402
from gmid_engine.core import InfeasibleSizingError  # noqa: E402

_FD_MOD = importlib.import_module("gmid_engine.search.fd_jacobian")


def _fd_case(tmp_path, lut_sealed):
    th = theta_r4c(y=0.3)
    return _setup(tmp_path, lut_sealed, th)


def test_fd_shortfall_remaining_equals_bound_runs_normally(tmp_path, lut_sealed):
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    k0 = dict(s.counters)["kernel_calls"]
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), ceiling=k0 + 2 * len(vs))      # 남은 한도 = 상계
    assert len(out) == len(vs)
    assert all(res is not None for res, _h in out)
    assert dict(s.counters)["kernel_calls"] == k0 + len(vs)


def test_fd_shortfall_remaining_one_below_bound_no_evaluation(tmp_path, lut_sealed):
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    k0 = dict(s.counters)["kernel_calls"]
    bound = 2 * len(vs)
    with pytest.raises(_FD_MOD.FdBudgetShortfall) as ei:
        fd_jacobian(s, vs, x, base, CELLS_C, f, (), ceiling=k0 + bound - 1)          # 남은 한도 = 상계 − 1
    assert ei.value.needed == bound and ei.value.remaining == bound - 1
    assert dict(s.counters)["kernel_calls"] == k0                                    # 평가 호출 0
    assert not isinstance(ei.value, InfeasibleSizingError)


def test_fd_shortfall_remaining_uses_current_kernel_calls(tmp_path, lut_sealed):
    # oracle (손): 남은 한도 = ceiling − kernel_calls -- kernel_calls 를 5 올려도 ceiling 이 같이 5 오르면 같은 판정.
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    s.counters["kernel_calls"] += 5
    k0 = dict(s.counters)["kernel_calls"]
    bound = 2 * len(vs)
    with pytest.raises(_FD_MOD.FdBudgetShortfall) as ei:
        fd_jacobian(s, vs, x, base, CELLS_C, f, (), ceiling=k0 + bound - 1)
    assert (ei.value.needed, ei.value.remaining) == (bound, bound - 1)


def test_fd_shortfall_skipped_columns_leave_the_bound(tmp_path, lut_sealed):
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    skip = frozenset({0, 2})
    k0 = dict(s.counters)["kernel_calls"]
    bound = 2 * (len(vs) - len(skip))                                                # 평가할 열에서 skip 을 뺀다
    with pytest.raises(_FD_MOD.FdBudgetShortfall) as ei:
        fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip, ceiling=k0 + bound - 1)
    assert (ei.value.needed, ei.value.remaining) == (bound, bound - 1)
    assert dict(s.counters)["kernel_calls"] == k0
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=skip, ceiling=k0 + bound)  # 남은 한도 = 상계: 통과
    assert len(out) == len(vs) and dict(s.counters)["kernel_calls"] == k0 + len(vs) - len(skip)


def test_fd_shortfall_all_columns_skipped_needs_nothing(tmp_path, lut_sealed):
    # oracle (손): 평가할 열 0 -> 상계 0 -> 남은 한도 0 이면 평상 실행(평가 0).
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    k0 = dict(s.counters)["kernel_calls"]
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), skip=frozenset(range(len(vs))), ceiling=k0)
    assert len(out) == len(vs) and dict(s.counters)["kernel_calls"] == k0


def test_fd_shortfall_ceiling_none_means_no_check(tmp_path, lut_sealed):
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    k0 = dict(s.counters)["kernel_calls"]
    out = fd_jacobian(s, vs, x, base, CELLS_C, f, (), ceiling=None)
    assert len(out) == len(vs) and dict(s.counters)["kernel_calls"] == k0 + len(vs)


def test_fd_shortfall_ceiling_is_required(tmp_path, lut_sealed):
    case, s, base, vs, x, f = _fd_case(tmp_path, lut_sealed)
    with pytest.raises(TypeError):
        fd_jacobian(s, vs, x, base, CELLS_C, f, ())
    with pytest.raises(TypeError):
        fd_jacobian(s, vs, x, base, CELLS_C, f, (), frozenset())                     # 위치로는 받지 않는다(키워드 전용)
