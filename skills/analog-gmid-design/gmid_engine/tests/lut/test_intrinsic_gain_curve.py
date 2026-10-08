"""`intrinsic_gain_curve` -- CONTRACT 4.5 [r7] (값 = gm/gds, 무차원), 설계 41 §6.4-1(이득 하한 L)·§4(GB4 곡선 검사).

oracle: (a) r5 toy: GDS = 0.1·ID -> gm/gds = (gm/ID)/0.1 = 10·(20 − 12v) = (200, 140, 80) (폭·VDS·VS 무관);
(c) 실데이터: 마디 값 = 슬라이스 GM/GDS(npz 직접)."""
import numpy as np
import pytest

from gmid_engine.lut import intrinsic_gain_curve


@pytest.mark.parametrize("w_key,vds,vsb", [(100, 0.5, 0.0), (200, 0.8, 0.3), (100, 1.0, 0.5)])
def test_toy_closed_form(toy_memo, w_key, vds, vsb):
    c = intrinsic_gain_curve(toy_memo, "nmos", w_key, 1e-6, vds, vsb)
    assert c.quantity == "intrinsic_gain"
    assert np.allclose(c.values, [200.0, 140.0, 80.0], rtol=1e-12, atol=0)
    assert np.allclose(c.gm_id, [20.0, 14.0, 8.0], rtol=1e-12, atol=0)
    assert c.monotone is True


def test_r4_toy_cell_class(r4toy_memo):
    """r4 toy(CONTRACT 7.2): VGS 칸 [0, 0.5] FC 위반 -> cell_ok (False, True).
    [RED 예상 -- 결함 보고] 마디 값은 '그 마디에서 LUT 가 말하는 양'(CONTRACT 4.5)이고 격자점에서 gm/ID 는 저장값 그대로(4.2 '결과',
    계획 DEC-87 '기울기 = 저장 GM/ID')라 gm/gds = 저장 GM/GDS = 10·(20, 10, 4). 마디 0 의 오른쪽 칸이 FC 위반이면 엔진 op_point 가
    격자점에서도 그 칸의 할선 기울기(ln10/0.5 = 4.605)를 gm/ID 로 내 표의 gm_id(20)와 값(46.05)이 서로 다른 gm/ID 를 쓴다."""
    c = intrinsic_gain_curve(r4toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    assert tuple(bool(x) for x in c.cell_ok) == (False, True)
    assert np.allclose(c.gm_id, [20.0, 10.0, 4.0], rtol=1e-12, atol=0)
    assert np.allclose(c.values, [200.0, 100.0, 40.0], rtol=1e-12, atol=0)


@pytest.mark.lut_realdata
def test_real_nodes_equal_gm_over_gds(real_memo, raw_slice):
    rng = np.random.default_rng(7)
    for kind in ("nmos", "pmos"):
        z = raw_slice(kind, 1000)
        for _ in range(10):
            i, k, s = int(rng.integers(len(z["L"]))), int(rng.integers(4, len(z["VDS"]))), int(rng.integers(len(z["VS"])))
            c = intrinsic_gain_curve(real_memo, kind, 1000, float(z["L"][i]), float(z["VDS"][k]), float(z["VS"][s]))
            j = np.searchsorted(z["VGS"], np.asarray(c.vgs))
            exp = z["GM"][i, j, k, s] / z["GDS"][i, j, k, s]
            assert np.allclose(np.asarray(c.values), exp, rtol=1e-12, atol=0)
