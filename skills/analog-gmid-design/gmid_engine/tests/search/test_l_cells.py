"""CONTRACT 3.4 `l_cells(lut_access, kind)`: 레이아웃 전 슬라이스의 L 앵커와 bin 지도 -> 칸 ((lo, hi), ...) lo 오름.
빈 지도 -> 앵커마다 (a, a); 같은 anchor_bin 앵커들 -> (최소, 최대); anchor_bin None -> 자기 칸."""
import pytest

from gmid_engine.search import l_cells

from .conftest import R4_L, new_access


def expect_cells(anchors, anchor_bin):
    if not anchor_bin:
        return tuple((a, a) for a in anchors)
    groups, own = {}, []
    for a, b in zip(anchors, anchor_bin):
        if b is None:
            own.append((a, a))
        else:
            groups.setdefault(b, []).append(a)
    cells = own + [(min(v), max(v)) for v in groups.values()]
    return tuple(sorted(cells))


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_empty_bin_map_one_cell_per_anchor(lut_sealed, kind):
    assert l_cells(new_access(lut_sealed), kind) == tuple((a, a) for a in R4_L)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_real_lut_bins(real_lut_v2, kind):
    lut, _ = real_lut_v2
    acc = new_access(lut)
    sl = lut.slice_map[(kind, dict(acc.w_keys)[kind])]
    anchors = tuple(float(x) for x in sl.grids[0])
    exp = expect_cells(anchors, tuple(sl.l_bins.anchor_bin))
    got = l_cells(acc, kind)
    assert got == exp
    # 칸은 겹치지 않고 모든 앵커를 정확히 한 칸이 품는다.
    for a in anchors:
        assert sum(1 for lo, hi in got if lo <= a <= hi) == 1
    assert len(got) < len(anchors)          # 실 LUT 는 bin 이 앵커 여럿을 묶는다(lut 계약 r4 실측)
