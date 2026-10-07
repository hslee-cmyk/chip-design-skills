"""`_helpers_root` (peak_index·strong_inversion_root) -- CONTRACT 3절 분지 규칙과 6절 구간 A·B 복사 해시.

분지 규칙은 공개 `vgs_for_gm_id` 로 확인한다(격자점 (L, VDS, VS) 라 곡선 = 격자 gm/ID 그대로). 기대값은 손계산과
conftest 의 독립 구현(`branch_solve_vgs`, 옛 `legacy_solve_vgs`)에서 낸다.
"""
import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import vgs_for_gm_id

from .conftest import (LEGACY_SR, LUT_SRC, anchored_block, ast_sha, branch_solve_vgs, detail_of,
                       legacy_solve_vgs, rel_close)

H_BLOCK_A = "0a86bafdeaddf5c9a83cfce762d1a47b01dd6051c285ded5e26b803a4d0fc729"
H_BLOCK_B = "29beb488b7222e495e3794d5685bd0d751289e08dc502368f9e7af3143c51680"


@pytest.mark.parametrize("first,last,expected,n", [
    ("d = g - gm_id", "idx = np.flatnonzero", H_BLOCK_A, 2),
    ("i = int(idx[-1])", "if x1 == x0", H_BLOCK_B, 5),
])
def test_copy_block_ast_hash(first, last, expected, n):
    old = anchored_block(LEGACY_SR, "_solve_vgs", first, last)
    new = anchored_block(LUT_SRC / "_helpers_root.py", "strong_inversion_root", first, last)
    assert len(old) == n and len(new) == n
    assert ast_sha(old) == expected, "옛 구간 해시가 계약 표와 다르다(해시 방법 확인용)"
    assert ast_sha(new) == expected


VGS6 = (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)
IDS6 = (1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4)


def _q(memo, gm_id):
    return vgs_for_gm_id(memo, "nmos", 100, gm_id, 1e-6, 0.5, 0.0)


def test_rightmost_interval_inside_branch(curve_lut):
    # 정점 index 1(g=30). 목표 13 은 분지 안 [1,2]·[2,3]·[3,4] 세 구간이 품는다 -> 가장 오른쪽 [3,4]
    memo, g = curve_lut(VGS6, IDS6, (5.0, 30.0, 12.0, 15.0, 8.0, 3.0))
    v = _q(memo, 13.0)
    hand = 0.8 + (0.6 - 0.8) / (15.0 - 8.0) * (13.0 - 8.0)      # 0.657142857...
    assert rel_close(v, hand, 1e-9)
    assert v == branch_solve_vgs(g, VGS6, 13.0)
    # 목표 5: 정점 왼쪽 [0,1] 끝점도 닿지만 분지 [4,5] 가 품는다 -> 분지 해
    assert rel_close(_q(memo, 5.0), 0.8 + (5.0 - 8.0) / (3.0 - 8.0) * 0.2, 1e-9)


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


def test_flat_interval_takes_larger_vgs_end(curve_lut):
    # ID·GM 이 같은 두 점 -> 격자 gm/ID 가 비트 단위로 같다(평탄 구간). 목표 = 그 값 -> 가장 큰 VGS 쪽 끝점
    vgs = (0.0, 0.5, 1.0)
    memo, g = curve_lut(vgs, (1e-7, 1e-6, 1e-6), (30.0, 10.0, 10.0))
    assert g[1] == g[2]
    assert _q(memo, float(g[1])) == 1.0


def test_endpoint_exact_match_is_inside(curve_lut):
    memo, g = curve_lut(VGS6, IDS6, (5.0, 30.0, 12.0, 15.0, 8.0, 3.0))
    # 분지 끝점 값과 정확히 같은 목표(편차 곱 0)도 구간에 든다
    assert _q(memo, float(g[-1])) == pytest.approx(1.0, abs=1e-12)
    assert _q(memo, float(g[1])) == branch_solve_vgs(g, VGS6, float(g[1]))


def test_matches_legacy_bitwise_when_legacy_root_in_branch(curve_lut):
    # 3절: 옛 결과가 분지 안이면 새 결과가 비트 단위로 같다
    memo, g = curve_lut(VGS6, IDS6, (5.0, 30.0, 12.0, 15.0, 8.0, 3.0))
    p = int(np.argmax(g))
    n_cmp = 0
    for t in np.linspace(3.05, 29.95, 41):
        old = legacy_solve_vgs(g, VGS6, float(t))
        if old >= VGS6[p]:
            assert _q(memo, float(t)) == old, t
            n_cmp += 1
    assert n_cmp == 41
