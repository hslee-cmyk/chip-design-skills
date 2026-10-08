"""`_helpers_gmid_axis.axis_curve` (gm/ID 축 곡선 표 공용) -- CONTRACT 4.5 [r7]: 표의 마디 = 강반전 분지(VGS ≥ 곡선 정점 = gm/ID 최댓값
마디, nanargmax), 분지 안 NaN 마디 -> `lut_curve_undefined`, `monotone` = 분지 gm/ID 엄격 감소, `cell_ok` = 마디 사이 Hermite 칸.

공개 진입점(`idu_curve`·`ft_curve`)으로 본다(helper 직접 import 금지 -- CONTRACT 머리). 입력은 conftest `curve_lut` 합성 곡선(a)."""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import ft_curve, idu_curve

from .conftest import detail_of

VGS4 = (0.0, 0.5, 1.0, 1.5)


def test_branch_starts_at_peak_node(curve_lut):
    """gm/ID 마디 (4, 6, 5, 3): 정점 = 마디 1 -> 표 마디 = VGS 0.5, 1.0, 1.5 (마디 0 은 약반전 쪽이라 표 밖)."""
    ids = (1e-7, 1e-6, 1e-5, 5e-5)
    memo, g = curve_lut(VGS4, ids, (4.0, 6.0, 5.0, 3.0))
    c = idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(c.vgs) == (0.5, 1.0, 1.5)
    assert np.allclose(c.gm_id, [6.0, 5.0, 3.0], rtol=1e-12, atol=0)
    assert np.allclose(c.values, np.asarray(ids[1:]) * 1e-6 / 1e-6, rtol=1e-12, atol=0)
    assert c.monotone is True


def test_monotone_false_when_branch_gm_id_rises(curve_lut):
    """분지 gm/ID (8, 5, 6): 한 번 오른다 -> monotone False (소비자는 마디 전수, 설계 41 §4.1)."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-6, 1e-5, 1e-4), (8.0, 5.0, 6.0))
    c = idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert c.monotone is False
    assert len(c.vgs) == 3


def test_undefined_node_inside_branch(curve_lut):
    """분지 안 마디의 GM = 0(gm/ID 정의 안 됨) -> `lut_curve_undefined`(역산 함수와 같은 규칙)."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-6, 1e-5, 1e-4), (8.0, 5.0, 0.0))
    with pytest.raises(SealViolationError) as ei:
        idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_curve_undefined"


def test_cell_ok_follows_fc(curve_lut):
    """칸 단조 판정을 손으로: 마디 ID (1e-6, 1e-5, 1e-4)·gm/ID (8, 5, 3), h = 0.5, Δln ID = ln10 = 2.303.
    칸 0: b0 = 4, b2 = 2.5, b1 = 6.908 − 6.5 = 0.41 ≥ 0 -> 단조. 칸 1: b0 = 2.5, b2 = 1.5, b1 = 6.908 − 4 = 2.9 ≥ 0 -> 단조.
    gm/ID (8, 1, 3): 칸 0 b0 = 4, b2 = 0.5, b1 = 2.408 ≥ 0 단조; 칸 1 b0 = 0.5, b2 = 1.5, b1 = 4.9 ≥ 0 단조 -- 둘 다 True.
    gm/ID (20, 5, 3): 칸 0 b0 = 10, b2 = 2.5, b1 = −5.6, b1² = 31.3 ≤ 25 거짓 -> 위반."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-6, 1e-5, 1e-4), (8.0, 5.0, 3.0))
    assert tuple(bool(x) for x in idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0).cell_ok) == (True, True)
    memo, _ = curve_lut((0.0, 0.5, 1.0), (1e-6, 1e-5, 1e-4), (20.0, 5.0, 3.0))
    assert tuple(bool(x) for x in ft_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0).cell_ok) == (False, True)
