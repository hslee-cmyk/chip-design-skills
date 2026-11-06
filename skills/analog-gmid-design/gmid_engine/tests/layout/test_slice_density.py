"""CONTRACT 4.2 `slice_density(memo, device, keys) -> tuple[SliceDensity]` (Q4 (i)(iv)) -- toy 손계산, 제외 사유, memo 캐시.

보존량 (ID, gm/ID, L) 에서 슬라이스마다 J = op.IDu / L, W_need = ID_A / J, tol = id_equivalent 셀. [r5] toy(lut 계약 7.1)는
gm/ID 14 -> vgs 0.5(격자점), J0 = I1 / 1e-6 = 0.1·e^8.55 A/m(두 키 같음), ID_A = c x I1 -> W_need = c x 1e-6, tol_V = 0 수준.
r4 toy(lut 7.2)는 VGS 칸 [0, 0.5] 이 FC 위반이라 모든 슬라이스가 `lut_hermite_nonmonotone_cell` 로 빠진다.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import SliceDensity
from gmid_engine.layout.slice_density import slice_density

from .conftest import I1, J0, TOY_VGS_ROOT, build_toy_lut, dev, new_memo


def _stats(memo):
    return {r: (s.hits, s.misses) for r, s in memo.stats()}


@pytest.mark.parametrize("ID", [2e-6, 0.75e-6, 12e-6])
def test_toy_hand_values(toy_memo, ID):
    out = slice_density(toy_memo, dev("X", "s", "d", ID), (100, 200))
    assert isinstance(out, tuple) and len(out) == 2
    for sd, key in zip(out, (100, 200)):
        assert isinstance(sd, SliceDensity)
        assert sd.finger_w_key == key
        assert sd.finger_w_m == pytest.approx(key * 1e-8, rel=1e-12)
        assert sd.vgs_V == pytest.approx(TOY_VGS_ROOT, abs=1e-12)        # 20 − 12v = 14 -> 0.5
        assert sd.J_A_per_m == pytest.approx(J0, rel=1e-12)               # 0.1·e^8.55 = 516.675443 A/m
        assert J0 == pytest.approx(516.675443, rel=1e-9) and I1 == pytest.approx(5.16675443e-4, rel=1e-9)
        assert sd.W_need_m == pytest.approx(ID, rel=1e-12)                # ID_A = c x I1 -> W_need = c x 1e-6
        assert sd.W_need_m == pytest.approx(ID * J0 / sd.J_A_per_m, rel=1e-12)  # W_need = ID_A / J
        assert isinstance(sd.tol_v_V, float)
        assert abs(sd.tol_v_V) <= 1e-12                                   # id_equivalent 셀 = 0 수준(실측 1e-18~1e-16)
        assert sd.reason == ""


def test_w_need_is_from_preserved_quantities_not_reference_W(toy_memo):
    # W_m(참고 W)는 보존량이 아니다: W_m 만 바꿔도 W_need 는 그대로 ID/J
    a = slice_density(toy_memo, dev("X", "s", "d", 0.75e-6, W=4e-6), (100, 200))
    b = slice_density(toy_memo, dev("X", "s", "d", 0.75e-6, W=9e-6), (100, 200))
    assert [x.W_need_m for x in a] == [x.W_need_m for x in b]
    assert all(x.W_need_m == pytest.approx(0.75e-6, rel=1e-9) for x in a)


def test_r4_toy_rejected_by_hermite_fc(tmp_path):
    # 4.2 [r5]: r4 toy(lut 7.2) 는 역산 칸이 Fritsch–Carlson 위반 -> 모든 슬라이스 제외(사유 그대로)
    memo = new_memo(build_toy_lut(tmp_path / "r4", variant="r4"))
    out = slice_density(memo, dev("X", "s", "d", 2e-6), (100, 200))
    assert [(s.finger_w_key, s.reason) for s in out] == [(100, "lut_hermite_nonmonotone_cell"),
                                                         (200, "lut_hermite_nonmonotone_cell")]
    assert all((s.vgs_V, s.J_A_per_m, s.W_need_m, s.tol_v_V) == (None,) * 4 for s in out)


def test_keys_order_kept(toy_memo):
    out = slice_density(toy_memo, dev("X", "s", "d", 2e-6), (200, 100))
    assert [s.finger_w_key for s in out] == [200, 100]


@pytest.mark.parametrize("kw, reason", [
    ({"gm_id": 25.0}, "lut_no_strong_inversion_root"),     # 계약 손계산: 정점 20 위
    ({"L": 1.5e-6}, "lut_l_bin_unbracketed"),               # 앵커 1e-6·2e-6 사이 -- [WB-1 §4] 합성 bin 지도: 앵커 1개 bin 안 비앵커 점 (card 목록 lut_l_not_anchor -> lut_l_bin_unbracketed)
    ({"L": 4e-6}, "lut_axis_out_of_range"),
    ({"vsb": 0.6}, "lut_axis_out_of_range"),
])
def test_seal_violation_becomes_excluded_slice(toy_memo, kw, reason):
    out = slice_density(toy_memo, dev("X", "s", "d", 2e-6, **kw), (100, 200))
    assert len(out) == 2
    for sd, key in zip(out, (100, 200)):
        assert sd.finger_w_key == key
        assert sd.finger_w_m == pytest.approx(key * 1e-8, rel=1e-12)
        assert (sd.vgs_V, sd.J_A_per_m, sd.W_need_m, sd.tol_v_V) == (None, None, None, None)
        assert sd.reason == reason


def test_other_exceptions_propagate(toy_memo):
    # 슬라이스 없는 폭 키는 lut 계약상 KeyError(계약 위반) -- SliceDensity 로 삼키지 않는다
    with pytest.raises(KeyError):
        slice_density(toy_memo, dev("X", "s", "d", 2e-6), (150,))


def test_second_identical_call_is_memo_hit(toy_lut):
    memo = new_memo(toy_lut)
    d = dev("X", "s", "d", 2e-6)
    first = slice_density(memo, d, (100, 200))
    s1 = _stats(memo)
    second = slice_density(memo, dev("Y", "s2", "d2", 2e-6), (100, 200))   # 이름·넷만 다름 = 같은 조회 인자
    s2 = _stats(memo)
    assert first == second
    for region in s1:
        assert s2[region][1] == s1[region][1], "두 번째 조회에서 %s 영역 miss 증가 -- memo 재계산" % region
    assert sum(s2[r][0] for r in s2) > sum(s1[r][0] for r in s1)
