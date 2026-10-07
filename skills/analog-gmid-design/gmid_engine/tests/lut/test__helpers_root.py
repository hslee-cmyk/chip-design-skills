"""`_helpers_root` (peak_index·strong_inversion_root) -- CONTRACT 3절 분지 규칙 [r5]: 칸 선택(정점 이상, 가장 오른쪽, 해 없음
실패)은 r4 와 같고 칸 안 근 = 그 칸 VGS Hermite 의 미분이 목표인 VGS, 칸 단조 위반이면 `lut_hermite_nonmonotone_cell`.
6절 [r5]: 옛 `_solve_vgs` 구간 A·B 복사는 패키지에서 빠졌다(옛 원본 구간 해시는 그대로, 패키지 어디에도 그 문장 창이 없다).

분지 규칙은 공개 `vgs_for_gm_id` 로 확인한다(격자점 (L, VDS, VS) 라 곡선 마디 = 격자값). 기대값은 손계산, conftest 의 독립
구현(`sir_ref`·`hermite_cell_root`·`fc_ok`), 옛 원본 문장 그대로 옮긴 `legacy_solve_vgs`(칸 index 비교만)에서 낸다.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import op_point, vgs_for_gm_id

from .conftest import (LEGACY_SR, anchored_block, ast_sha, branch_solve_vgs, detail_of, fc_ok, legacy_solve_vgs,
                       lut_package_window_hashes, sir_ref_b)

H_BLOCK_A = "0a86bafdeaddf5c9a83cfce762d1a47b01dd6051c285ded5e26b803a4d0fc729"
H_BLOCK_B = "29beb488b7222e495e3794d5685bd0d751289e08dc502368f9e7af3143c51680"


@pytest.mark.parametrize("first,last,expected,n", [
    ("d = g - gm_id", "idx = np.flatnonzero", H_BLOCK_A, 2),
    ("i = int(idx[-1])", "if x1 == x0", H_BLOCK_B, 5),
])
def test_legacy_block_copy_removed(first, last, expected, n):
    old = anchored_block(LEGACY_SR, "_solve_vgs", first, last)
    assert len(old) == n
    assert ast_sha(old) == expected, "옛 원본 구간 해시가 기록값과 다르다(해시 방법 확인용)"
    hits = lut_package_window_hashes(n).get(expected, [])
    assert hits == [], "옛 _solve_vgs 구간 복사가 패키지에 남아 있다: %r" % (hits,)


VGS6 = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
IDS6 = (1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4)
G6 = (5.0, 30.0, 12.0, 15.0, 8.0, 3.0)


def _q(memo, gm_id):
    return vgs_for_gm_id(memo, "nmos", 100, gm_id, 1e-6, 0.5, 0.0)


def _curve_ok(ids, g, vgs):
    y = np.log(np.asarray(ids, dtype=float))
    g = np.asarray(g, dtype=float)
    return tuple(bool(fc_ok(y[i], y[i + 1], g[i], g[i + 1], vgs[i + 1] - vgs[i])) for i in range(len(vgs) - 1))


def _ref(ids, g, vgs, target):
    """(상태, 근, 근 차 상한, 왕복 상한) -- 상한은 conftest 의 γ_n 유도(임의 상수 없음)."""
    return sir_ref_b(vgs, np.log(np.asarray(ids, dtype=float)), g, target, _curve_ok(ids, g, vgs), with_residual=True)


def _back(memo, v):
    return op_point(memo, "nmos", 100, 1e-6, v, 0.5, 0.0).gm_over_id


def _check_root(memo, ids, g, vgs, t):
    v = _q(memo, t)
    st, exp, rb, resb = _ref(ids, g, vgs, t)
    assert st == "ok" and abs(v - exp) <= rb, (t, v, exp, rb)
    assert abs(_back(memo, v) - t) <= resb, ("왕복: op_point gm/ID = 목표(같은 곡면)", t, _back(memo, v), resb)
    return v


def test_fixture_curve_cells_are_monotone():
    """전제: 아래 test 곡선(10배/0.2 V, gm/ID G6)의 칸은 모두 FC 단조 -- 칸 안 근이 있다."""
    assert _curve_ok(IDS6, G6, VGS6) == (True,) * 5


def test_rightmost_interval_inside_branch(curve_lut):
    # 정점 index 1(g=30). 목표 13 은 분지 안 [1,2]·[2,3]·[3,4] 세 칸이 품는다 -> 가장 오른쪽 [3,4]
    memo, g = curve_lut(VGS6, IDS6, G6)
    v = _check_root(memo, IDS6, g, VGS6, 13.0)
    assert 0.6 < v < 0.8
    # 칸 선택은 옛 2점 규칙과 같은 칸 -- 근은 다르다(Hermite 미분)
    assert branch_solve_vgs(g, VGS6, 13.0) != v and 0.6 < branch_solve_vgs(g, VGS6, 13.0) < 0.8
    # 목표 5: 정점 왼쪽 [0,1] 끝점도 닿지만 분지 [4,5] 가 품는다 -> 분지 해
    v5 = _check_root(memo, IDS6, g, VGS6, 5.0)
    assert 0.8 < v5 < 1.0


def test_peak_is_first_argmax(curve_lut):
    # 같은 최댓값 두 번(index 1, 2): 정점 = 첫 index 1 -> peak_vgs 0.2
    memo, g = curve_lut(VGS6, IDS6, (5.0, 30.0, 30.0, 15.0, 8.0, 3.0))
    with pytest.raises(SealViolationError) as ei:
        _q(memo, 40.0)
    det = detail_of(ei.value)
    assert det["peak_vgs"] == pytest.approx(0.2, abs=0)
    assert det["branch_gm_id_max"] == pytest.approx(float(g[1:].max()), rel=1e-12)


def test_leak_branch_only_target_fails(curve_lut):
    # 정점 왼쪽 g[0]=2 < 분지 최솟값 3: 목표 2.5 는 [0,1] 에서만 닿는다.
    memo, g = curve_lut(VGS6, IDS6, (2.0, 30.0, 12.0, 15.0, 8.0, 3.0))
    old = legacy_solve_vgs(g, VGS6, 2.5)
    assert old < 0.2, "옛 규칙은 누설 분지 해를 낸다(전제)"
    assert branch_solve_vgs(g, VGS6, 2.5) is None
    with pytest.raises(SealViolationError) as ei:
        _q(memo, 2.5)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_no_strong_inversion_root"
    assert det["gm_id"] == 2.5
    assert det["kind"] == "nmos" and det["w_key"] == 100
    assert det["peak_vgs"] == 0.2
    assert det["branch_gm_id_min"] == pytest.approx(float(g[1:].min()), rel=1e-12)
    assert det["branch_gm_id_max"] == pytest.approx(float(g[1:].max()), rel=1e-12)


def test_flat_interval_takes_upper_end_when_residual_zero(curve_lut):
    # [r5] 자료가 맞는 평탄 칸: gm/ID (30, 10, 10), ln ID 차 (10, 5) -> 칸 [1,2] 는 ln ID 가 기울기 10 직선(FC 단조).
    # 목표 = 10 -> 분지 가장 오른쪽 칸 [1,2], 위 끝 residual 정확히 0 -> 위 끝 VGS(3절)
    vgs = (0.0, 0.5, 1.0)
    ids = (1e-7, 1e-7 * math.exp(10.0), 1e-7 * math.exp(15.0))
    memo, g = curve_lut(vgs, ids, (30.0, 10.0, 10.0))
    assert _curve_ok(ids, g, vgs) == (True, True)
    # 목표 = 위 끝 마디 값: 칸 [1,2] 두 끝 편차 곱 ≤ 0, 위 끝 residual 0 -> 위 끝 VGS.
    # 엔진이 위 끝 residual 을 다항식 미분으로 계산하면 정확히 0 이 아닐 수 있다(보고 항목) -- 허용 = 유도 상한
    st, exp, rb, _ = _ref(ids, g, vgs, float(g[2]))
    assert st == "ok" and exp == 1.0
    assert abs(_q(memo, float(g[2])) - 1.0) <= rb


def test_flat_interval_inconsistent_data_rejected(curve_lut):
    """음성: 같은 평탄 gm/ID 인데 ln ID 차 0(기울기 10 과 모순) -> 칸 [1,2] FC 위반 -> lut_hermite_nonmonotone_cell."""
    vgs = (0.0, 0.5, 1.0)
    ids = (1e-7, 1e-6, 1e-6)
    memo, g = curve_lut(vgs, ids, (30.0, 10.0, 10.0))
    assert _curve_ok(ids, g, vgs) == (False, False)
    with pytest.raises(SealViolationError) as ei:
        _q(memo, float(g[1]))
    det = detail_of(ei.value)
    assert det["reason"] == "lut_hermite_nonmonotone_cell"
    assert det["axis"] == "VGS" and det["cell_lo"] == 0.5 and det["cell_hi"] == 1.0
    assert (det["gm_id"], det["L"], det["vds"], det["vsb"], det["kind"], det["w_key"]) == (
        float(g[1]), 1e-6, 0.5, 0.0, "nmos", 100)


def test_endpoint_exact_match_is_inside(curve_lut):
    memo, g = curve_lut(VGS6, IDS6, G6)
    # 분지 끝점 값과 정확히 같은 목표(편차 곱 0)도 칸에 든다 -> 위 끝 residual 0 이면 위 끝
    st, exp, rb, _ = _ref(IDS6, g, VGS6, float(g[-1]))
    assert st == "ok" and exp == 1.0
    assert abs(_q(memo, float(g[-1])) - 1.0) <= rb
    _check_root(memo, IDS6, g, VGS6, float(g[1]))


def test_cell_choice_matches_legacy_when_legacy_root_in_branch(curve_lut):
    # 6절 [r5]: 옛 결과가 분지 안이면 칸 index 는 같고, 칸 안 근은 Hermite 미분 근(독립 구현)과 같다
    memo, g = curve_lut(VGS6, IDS6, G6)
    p = int(np.argmax(g))
    n_cmp = n_diff = 0
    for t in np.linspace(3.05, 29.95, 41):
        t = float(t)
        old = legacy_solve_vgs(g, VGS6, t)
        if old < VGS6[p]:
            continue
        d = np.asarray(g) - t
        i_old = int(np.flatnonzero(d[:-1] * d[1:] <= 0.0)[-1])
        v = _check_root(memo, IDS6, g, VGS6, t)
        assert VGS6[i_old] <= v <= VGS6[i_old + 1], (t, i_old, v)
        n_cmp += 1
        n_diff += v != old
    assert n_cmp == 41 and n_diff >= 35
