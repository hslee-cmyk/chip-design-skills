"""`idu_curve` -- CONTRACT 4.5 [r7] (값 = IDu = ID·L/w_m, A), 계획 DEC-88(쓰기 소자 좌표 ln IDu), 설계 41 §6.4-5(면적 상한 W·L = I·L²/IDu).

oracle: (a) r5 toy: IDu = ID(w_m)·L/w_m, L = 2e-6 장은 ID 가 1/2 이고 L 이 2배 -> L = 1e-6 과 같은 IDu; 폭 무관;
(c) 실데이터 마디 = ID·L/W(npz 직접); 분지 gm/ID 엄격 감소 여부(`monotone`) = numpy 로 같은 판정."""
import math

import numpy as np
import pytest

from gmid_engine.lut import idu_curve


def _idu(v, d=0.5, s=0.0):
    return 1e-7 * math.exp(20 * v - 6 * v * v + 0.1 * d) * 0.5 ** (s / 0.5)


@pytest.mark.parametrize("w_key,L", [(100, 1e-6), (200, 1e-6), (100, 2e-6), (200, 3e-6)])
def test_toy_closed_form(toy_memo, w_key, L):
    c = idu_curve(toy_memo, "nmos", w_key, L, 0.5, 0.0)
    assert c.quantity == "idu_a" and c.L == L
    assert np.allclose(c.values, [_idu(v) for v in (0.0, 0.5, 1.0)], rtol=1e-12, atol=0)


@pytest.mark.lut_realdata
def test_real_nodes_and_monotone_flag(real_memo, raw_slice):
    """(c) 마디 IDu = ID·L/W. monotone = 분지(정점부터) 마디 gm/ID 가 엄격 감소(독립 numpy 판정)와 같다.
    pmos 는 중반전에서 gm/ID 가 한 번 오르는 곡선이 많다는 계약 실측(4.5)을 같은 판정으로 센다(정보 -- 개수 비교 없음)."""
    rng = np.random.default_rng(20261008)
    for kind in ("nmos", "pmos"):
        z = raw_slice(kind, 1000)
        W = float(z["W"])
        for _ in range(25):
            i, k, s = int(rng.integers(len(z["L"]))), int(rng.integers(4, len(z["VDS"]))), int(rng.integers(len(z["VS"])))
            L = float(z["L"][i])
            c = idu_curve(real_memo, kind, 1000, L, float(z["VDS"][k]), float(z["VS"][s]))
            j = np.searchsorted(z["VGS"], np.asarray(c.vgs))
            assert np.allclose(np.asarray(c.values), z["ID"][i, j, k, s] * L / W, rtol=1e-12, atol=0)
            g = z["GM"][i, :, k, s] / z["ID"][i, :, k, s]
            br = g[int(np.argmax(g)):]
            assert c.monotone == bool(np.all(np.diff(br) < 0)), (kind, i, k, s)
