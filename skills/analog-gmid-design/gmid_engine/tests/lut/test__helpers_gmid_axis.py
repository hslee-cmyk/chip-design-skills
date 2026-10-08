"""`_helpers_gmid_axis.axis_curve` (gm/ID 축 곡선 표 공용) -- CONTRACT 4.5 [r7]: 표의 마디 = 강반전 분지(VGS ≥ 곡선 정점 = gm/ID 최댓값
마디, nanargmax), 분지 안 NaN 마디 -> `lut_curve_undefined`, `monotone` = 분지 gm/ID 엄격 감소, `cell_ok` = 마디 사이 Hermite 칸.

공개 진입점(`idu_curve`·`ft_curve`)으로 본다(helper 직접 import 금지 -- CONTRACT 머리). 입력은 conftest `curve_lut` 합성 곡선(a)."""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import ft_curve, idu_curve

from .conftest import chord_ids, chord_outside_fraction, detail_of

# [r7 2026-10-09 단위 검사 복원(lut CONTRACT 1.4)] 합성 곡선의 마디 ID 는 기울기 자료(gm/ID)와 평균값 정리로 맞게 만든다 --
# conftest `chord_ids`(칸마다 ln ID 현 기울기 = 두 끝 gm/ID 의 볼록 결합, oracle (a) 구성). 옛 곡선(10 배/칸 등 gm/ID 와 무관한 ID)은
# 칸 과반이 1.4 위반이라 로드가 거부된다.
VGS4 = (0.0, 0.5, 1.0, 1.5)


def test_branch_starts_at_peak_node(curve_lut):
    """gm/ID 마디 (4, 6, 5, 3): 정점 = 마디 1 -> 표 마디 = VGS 0.5, 1.0, 1.5 (마디 0 은 약반전 쪽이라 표 밖)."""
    ids = chord_ids(VGS4, (4.0, 6.0, 5.0, 3.0), 1e-7)
    assert chord_outside_fraction(VGS4, ids, (4.0, 6.0, 5.0, 3.0)) == (0, 3)          # 전제: 1.4 일관
    memo, g = curve_lut(VGS4, ids, (4.0, 6.0, 5.0, 3.0))
    c = idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(c.vgs) == (0.5, 1.0, 1.5)
    assert np.allclose(c.gm_id, [6.0, 5.0, 3.0], rtol=1e-12, atol=0)
    assert np.allclose(c.values, np.asarray(ids[1:]) * 1e-6 / 1e-6, rtol=1e-12, atol=0)
    assert c.monotone is True


def test_monotone_false_when_branch_gm_id_rises(curve_lut):
    """분지 gm/ID (8, 5, 6): 한 번 오른다 -> monotone False (소비자는 마디 전수, 설계 41 §4.1)."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), chord_ids((0.0, 0.5, 1.0), (8.0, 5.0, 6.0), 1e-6), (8.0, 5.0, 6.0))
    c = idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert c.monotone is False
    assert len(c.vgs) == 3


def test_undefined_node_inside_branch(curve_lut):
    """분지 안 마디의 GM = 0(gm/ID 정의 안 됨) -> `lut_curve_undefined`(역산 함수와 같은 규칙)."""
    memo, _ = curve_lut((0.0, 0.5, 1.0), chord_ids((0.0, 0.5, 1.0), (8.0, 5.0, 0.0), 1e-6), (8.0, 5.0, 0.0))
    with pytest.raises(SealViolationError) as ei:
        idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_curve_undefined"


def test_cell_ok_follows_fc(curve_lut):
    """칸 단조 판정을 손으로(CONTRACT 1.4 식, h = 0.5). 두 곡선 모두 칸마다 현 기울기가 두 끝 gm/ID 사이(1.4 단위 검사 일관).
    gm/ID (8, 5, 3)·Δln ID (3, 2)(현 6 ∈ [5, 8], 4 ∈ [3, 5]): 칸 0 b0 = 4, b2 = 2.5, b1 = 9 − 6.5 = 2.5 ≥ 0 -> 단조;
      칸 1 b0 = 2.5, b2 = 1.5, b1 = 6 − 4 = 2 ≥ 0 -> 단조.
    gm/ID (20, 4, 3)·Δln ID (2.25, 1.75)(현 4.5 ∈ [4, 20], 3.5 ∈ [3, 4]): 칸 0 b0 = 10, b2 = 2, b1 = 6.75 − 12 = −5.25,
      b1² = 27.6 > 20 -> 위반; 칸 1 b0 = 2, b2 = 1.5, b1 = 5.25 − 3.5 = 1.75 ≥ 0 -> 단조.
    (현이 두 끝 사이인데 FC 위반이려면 끝 기울기 비가 커야 한다 -- 옛 (20, 5, 3)·Δln ID ln10 은 현 4.6 이 [5, 20] 밖이었다.)"""
    vgs = (0.0, 0.5, 1.0)
    ids = (1e-6, 1e-6 * math.exp(3.0), 1e-6 * math.exp(5.0))
    assert chord_outside_fraction(vgs, ids, (8.0, 5.0, 3.0)) == (0, 2)
    memo, _ = curve_lut(vgs, ids, (8.0, 5.0, 3.0))
    assert tuple(bool(x) for x in idu_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0).cell_ok) == (True, True)
    ids = (1e-6, 1e-6 * math.exp(2.25), 1e-6 * math.exp(4.0))
    assert chord_outside_fraction(vgs, ids, (20.0, 4.0, 3.0)) == (0, 2)
    memo, _ = curve_lut(vgs, ids, (20.0, 4.0, 3.0))
    assert tuple(bool(x) for x in ft_curve(memo, "nmos", 100, 1e-6, 0.5, 0.0).cell_ok) == (False, True)
