"""CONTRACT 3.8 [r3] `constraint_rows(snapshot, lut_access, w_min_m, grid_m) -> (rows, undefined)`.

MOS 마다(dc_op 열 순서) w_min:<m> c = (W − W_min)/g (늘), tol = dc_tol_v 가 None·≤0 이면 undefined(그 MOS 나머지 행 없음),
seal6_bulk:<m> c = (min(vsb, vds + vsb) + tol)/tol, writer 면 inversion_floor:<m> c = (ln_idu − r_peak)·gm_id/tol,
active = c ≤ 1. r_peak 는 toy LUT 닫힌 식(gm/ID = B − C·VGS 최대 = VGS 격자 0 마디): ln I0 + LAM·vds + VS 항(vsb).
"""
import pytest

from gmid_engine.search import ConstraintRow, constraint_rows
from gmid_engine.sizing import S2_WRITERS
from fs1_wf import size_and_seal      # [FS-1 서명 맞춤] 손 wf 를 끼운 래퍼

from .conftest import GRID, expected_rows, W_MIN, build_case, circuit_c, col, theta_r4c


def _assert_rows(got, exp):
    rows, undef = got
    assert all(isinstance(r, ConstraintRow) for r in rows)
    assert [r.name for r in rows] == [n for n, _ in exp[0]]
    for r, (_, c) in zip(rows, exp[0]):
        assert r.c == pytest.approx(c, rel=1e-9, abs=1e-12)
        assert r.active == (r.c <= 1)
    assert tuple(undef) == tuple(exp[1])


@pytest.fixture
def sealed_c(tmp_path, lut_sealed):
    case = build_case(tmp_path, circuit_c(), lut_sealed)
    ev = size_and_seal(case.dc, theta_r4c(y=0.55, v1=0.65, v2=0.75))
    return case, ev.snapshot


def test_rows_match_hand_calc(sealed_c):
    case, snap = sealed_c
    got = constraint_rows(snap, case.acc, W_MIN, GRID)
    _assert_rows(got, expected_rows(snap, W_MIN, GRID))
    assert got[1] == ()


def test_w_below_w_min_gives_negative_active_row(sealed_c):
    case, snap = sealed_c
    big = 1.0                                 # 1 m: 모든 소자 W < W_min
    rows, _ = constraint_rows(snap, case.acc, big, GRID)
    wm = [r for r in rows if r.name.startswith("w_min:")]
    assert len(wm) == 2 and all(r.c < 0 and r.active for r in wm)
    _assert_rows((rows, ()), expected_rows(snap, big, GRID))


@pytest.mark.parametrize("bad", [None, 0.0, -1e-3])
def test_undefined_tolerance_keeps_only_w_min(sealed_c, bad):
    case, snap = sealed_c
    w = S2_WRITERS.writer_of("device", "dc_tol_v")
    tol = col(snap, "device", "dc_tol_v")
    tol["M1"] = bad
    snap2 = snap.write(w, "tampered", {("device", "dc_tol_v"): tol})
    rows, undef = constraint_rows(snap2, case.acc, W_MIN, GRID)
    assert tuple(undef) == ("M1",)
    assert [r.name for r in rows if r.name.endswith(":M1")] == ["w_min:M1"]
    _assert_rows((rows, undef), expected_rows(snap2, W_MIN, GRID))


def test_bulk_forward_bias_is_negative(sealed_c):
    """seal6: vsb 를 tol 보다 큰 음수로 만들면 c < 0(정의역 밖 쪽)."""
    case, snap = sealed_c
    ops = col(snap, "device", "dc_op")
    tol = col(snap, "device", "dc_tol_v")
    import dataclasses
    ops["M1"] = dataclasses.replace(ops["M1"], vsb=-3 * tol["M1"])
    snap2 = snap.write(S2_WRITERS.writer_of("device", "dc_op"), "tampered", {("device", "dc_op"): ops})
    rows, _ = constraint_rows(snap2, case.acc, W_MIN, GRID)
    r = {x.name: x for x in rows}["seal6_bulk:M1"]
    assert r.c == pytest.approx((-3 * tol["M1"] + tol["M1"]) / tol["M1"], rel=1e-12) and r.active
