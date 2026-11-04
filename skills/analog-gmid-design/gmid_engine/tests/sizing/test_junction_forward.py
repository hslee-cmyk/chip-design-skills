"""`junction_forward(vds, vsb) = max(0, -vsb, -(vds + vsb))` -- interface card 20261104-eo1r4-sf1l §2 '봉인 6'.

oracle (식): 식은 card §2 에 적힌 것이고, 값은 이 파일에서 vds·vsb 조합마다 손으로 셈했다(2진 분수 -- 정확 비교).
부호 양쪽 쓰는 두 소비자(nmos·pmos 노드 전압 -> vds·vsb 환산)는 ss 층 test(T-O3b)에서 건다.
"""
import pytest

from gmid_engine.sizing import junction_forward

from .call_sites import calls_of

# (vds, vsb, 손계산 값): 항 -vsb, -(vds+vsb)
CASES = [
    (0.5, 0.25, 0.0),        # 둘 다 역방향: -0.25, -0.75 -> 0
    (0.5, -0.25, 0.25),      # source-bulk 순방향: -vsb = 0.25, -(0.25) = -0.25
    (-0.5, 0.25, 0.25),      # drain-bulk 순방향: -vsb = -0.25, -(vds+vsb) = 0.25
    (0.25, -0.5, 0.5),       # 둘 다 순방향: 0.5 와 0.25 중 큰 쪽
    (0.0, 0.0, 0.0),         # 경계 0 V 정확히: 순방향 아님
    (-0.25, 0.25, 0.0),      # vdb = 0 정확히 (vsb > 0): -vsb = -0.25, -(0) = 0 -> 0
]


@pytest.mark.parametrize("vds,vsb,expected", CASES)
def test_junction_forward_hand_values(vds, vsb, expected):
    assert junction_forward(vds, vsb) == expected


def test_junction_forward_boundary_both_sides():
    """경계 0 V 의 양쪽: vsb = 0 에서 vds 만 바꿔도 vdb 가 음수가 되는 순간부터 양수, vsb = -0 아래도 양수."""
    import math
    tiny = math.ulp(0.0)
    assert junction_forward(0.5, 0.0) == 0.0
    assert junction_forward(0.5, -tiny) == tiny
    assert junction_forward(-tiny, 0.0) == tiny
    assert junction_forward(0.0, 0.0) == 0.0
    assert junction_forward(0.25, tiny) == 0.0


def test_junction_forward_call_sites_are_exactly_two():
    """호출 자리 = 봉인 6(dc_seal_bulk_reverse)과 ss_off_op 둘 -- 같은 식을 다른 곳에서 다시 계산하지 않는다(G-10)."""
    sites = calls_of("junction_forward")
    assert {fn for _f, fn in sites} == {"dc_seal_bulk_reverse", "ss_off_op"}, sorted(sites)
    assert len(sites) == 2
