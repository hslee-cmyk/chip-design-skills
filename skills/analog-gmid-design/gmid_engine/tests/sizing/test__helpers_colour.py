"""helper `_helpers_colour.refine_colours` -- CONTRACT 3.0 [r2] 정제 + 3.0b [r11](struct_colour 의 1-WL 색과 struct_canon 의 정준 라벨링이 같은 정제를 쓴다).

helper 는 비공개라 공개 결과로 확인한다(oracle (b): conftest `wl_colours`·test_struct_canon `wl_classes` 의 독립 1-WL 구현):
- 1-WL 색이 정점마다 유일한 회로에서 `dc_colour` = 독립 1-WL 색(정준 위치가 순서를 바꿀 여지가 없다) -- 정제 결과 그대로.
- 정제는 처음 색 순서를 보존한다: 처음 색이 다른 정점 사이 순서가 결과 색에서도 같다(서명 첫 성분 = 옛 색) -- 공개 `dc_colour` 에서
  1-WL 색 순서 보존으로 본다(test_struct_colour `check_colour_contract` 와 같은 성질의 helper 쪽 근거).
- 정준 라벨링의 궤도는 정제가 가르는 색 클래스를 넘지 않는다(정제는 자기동형 불변).
"""
import pytest

from gmid_engine.sizing import canonical_labeling

from .conftest import NINE, library_ctx, wl_colours
from .test_struct_canon import HAND, orbit_partition, random_graph, wl_classes


@pytest.mark.parametrize("name", NINE)
def test_unique_wl_circuits_colour_equals_refinement(name, toy_access):
    base = library_ctx(name, toy_access)[5].base
    wn, we = wl_colours(base)
    nc, ec = dict(base.column("node", "dc_colour")), dict(base.column("device", "dc_colour"))
    allw = list(wn.values()) + list(we.values())
    unique = len(set(allw)) == len(allw)
    assert (not unique) or (nc, ec) == (wn, we)                 # 1-WL 유일 -> 값이 정제 결과 그대로
    bad = [(k1, k2) for k1, w1 in wn.items() for k2, w2 in wn.items() if w1 < w2 and not nc[k1] < nc[k2]]
    assert bad == []                                            # 동률이 남아도 1-WL 순서는 보존


def test_both_branches_exercised(toy_access):
    """위 test 의 두 분기(1-WL 유일 -> 같음, 동률 -> 순서 보존)가 9회로에서 모두 실제로 지난다(공허한 test 아님)."""
    uniq = 0
    for name in NINE:
        wn, we = wl_colours(library_ctx(name, toy_access)[5].base)
        allw = list(wn.values()) + list(we.values())
        uniq += len(set(allw)) == len(allw)
    assert 0 < uniq < len(NINE)


@pytest.mark.parametrize("seed", range(15))
def test_orbits_never_cross_refined_classes(seed):
    col, nb = random_graph(500 + seed, n=8, labels=("x", "y"), colours=2)
    _, orb = canonical_labeling(col, nb)
    wl = wl_classes(col, nb)
    for g in orbit_partition(orb):
        assert len({wl[v] for v in g}) == 1


@pytest.mark.parametrize("name", sorted(HAND))
def test_refinement_order_preserving_on_hand_graphs(name):
    """처음 색이 다른 정점은 같은 궤도가 아니다(정제가 처음 색 순서를 보존 -- 서명 첫 성분)."""
    col, nb = HAND[name]
    col2 = {v: (1 if i % 3 == 0 else 0) for i, v in enumerate(sorted(col))}
    _, orb = canonical_labeling(col2, nb)
    for g in orbit_partition(orb):
        assert len({col2[v] for v in g}) == 1
