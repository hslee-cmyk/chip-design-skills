"""WB-1 B-7 (interface card 20261104-wb1 §1): 격자 정수 비교 -- `widths` 의 W_min 판정과 `l_position` 의 앵커 비교.

oracle (손): 값을 round(값/격자) 정수로 바꿔 비교한다. g = 1e-8 이면 1e-6·(1 ± 32·eps) 는 모두 정수 100.
- widths: `w_key >= round(w_min/grid)`. W_min = 1e-6·(1 + 32·eps) 이면 round = 100 이라 키 100 이 든다(옛 w_key·grid >= w_min 은 1e-6 < W_min 이라 빠진다 = red).
- l_position: round(L/g) 가 앵커 정수와 같으면 그 앵커 (i, i, l_grid[i]), 앵커가 아닌 같은 bin 이면 (k−1, k, L).
`widths` 와 `l_position` 이 읽는 칸만 가진 손 stub 으로 부른다(test_finger_slice 와 같은 방식: 실제 LUT 가 아니라 입력 구성).
test_midpoint_checks·test_mismatch_sigma 의 W_min 왕복 점 소속은 관찰 경로(공개 함수 + 합성 중점·mismatch 파일 형식)가 card 에 없어 쓰지 않았다(보고).
`_on_or_inside` ulp 조건 grep 0 은 tests/structure/test_wb1_source.py.
"""
from types import SimpleNamespace

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import LBin, LBinMap, widths
from gmid_engine.lut._helpers_anchor import l_position

EPS = 2.0 ** -52
G = 1e-8


def lut_stub(w_min, keys=(99, 100, 101)):
    return SimpleNamespace(spec=SimpleNamespace(manufacturing_grid_m=G, min_finger_w_m=(("nmos", w_min),)),
                           slice_map={("nmos", k): SimpleNamespace() for k in keys})


@pytest.mark.parametrize("w_min", [1e-6, 1e-6 * (1 + 32 * EPS), 1e-6 * (1 - 32 * EPS)])
def test_bin_widths_w_min_round_trip_point_keeps_key_100(w_min):
    assert widths(lut_stub(w_min), "nmos") == (100, 101)          # 99 는 정수 100 미만


def test_bin_widths_threshold_is_integer_not_float_product():
    # 손: W_min = 1.01e-6 -> 정수 101 이라 키 100 은 빠지고 101 만 든다 (양성 대조: 경계 판정이 실제로 일어난다)
    assert widths(lut_stub(1.01e-6), "nmos") == (101,)


L_GRID = (1e-6, 2e-6, 3e-6)
BINS = LBinMap(model_files=(), w_bin=(1e-6, 5e-6), bins=(LBin("b", 5e-7, 3.5e-6),), anchor_bin=(0, 0, 0))


@pytest.mark.parametrize("L, want", [
    (2e-6 * (1 + 32 * EPS), (1, 1, 2e-6)),            # 32 eps 어긋나도 정수 200 = 앵커 1 (base: 1 ulp 밖이라 앵커가 아니다)
    (1e-6 * (1 - 32 * EPS), (0, 0, 1e-6)),
    (3e-6 * (1 + 32 * EPS), (2, 2, 3e-6)),
    (1.5e-6, (0, 1, 1.5e-6)),                          # 앵커가 아닌 같은 bin: (k−1, k, L)
    (2.5e-6, (1, 2, 2.5e-6)),
])
def test_bin_l_position_anchor_compare_on_grid_integers(L, want):
    got = l_position(L_GRID, BINS, L, G, "lower")
    assert tuple(got) == want
    assert got[2] == want[2]                              # 앵커면 앵커 값, 아니면 조회 L 그대로


def test_bin_l_position_non_anchor_with_empty_bin_map_is_rejected():
    empty = LBinMap((), None, (), ())
    with pytest.raises(SealViolationError) as ei:
        l_position(L_GRID, empty, 1.5e-6, G, "lower")
    assert dict(ei.value.record.detail)["reason"] == "lut_l_not_anchor"
    # 양성 대조: 같은 빈 지도에서 앵커(32 eps 어긋남)는 통과
    assert tuple(l_position(L_GRID, empty, 2e-6 * (1 + 32 * EPS), G, "lower")) == (1, 1, 2e-6)
