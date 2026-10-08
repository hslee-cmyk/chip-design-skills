"""`vdsat_curve` -- CONTRACT 4.5 [r7] (값 = VDSAT 열, V), 설계 41 §6.2(헤드룸 gm/ID 하한)·계획 DEC-88(VDsat = LUT VDSAT 열).

oracle: (a) toy 기준 LUT 에 VDSAT_n = 0.1 + 0.2·VGS 를 더함(CONTRACT 7.1 r6 행) -> 마디 (0.1, 0.2, 0.3);
VDSAT 열이 없으면 `lut_column_unavailable`(2/(gm/ID) 로 대신하지 않는다 -- DEC-88); (c) 실데이터 마디 = 슬라이스 VDSAT(npz 직접)."""
import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import vdsat_curve

from .conftest import detail_of, new_memo, toy_cap_arrays, toy_id


def test_column_missing_rejected(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        vdsat_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_column_unavailable" and d["column"] == "VDSAT"


def test_toy_vdsat_column(toy_build):
    cap = toy_cap_arrays()
    cap["ID_n"] = toy_id(1.0)
    cap["VDSAT_n"] = np.broadcast_to(0.1 + 0.2 * np.asarray([0.0, 0.5, 1.0])[None, :, None, None], (3, 3, 2, 2)).copy()
    m = new_memo(toy_build("vd", cap=cap).load())
    c = vdsat_curve(m, "nmos", 100, 1e-6, 0.75, 0.25)
    assert c.quantity == "vdsat_v"
    assert np.allclose(c.values, [0.1, 0.2, 0.3], rtol=0, atol=1e-15)
    with pytest.raises(SealViolationError) as ei:                  # 다른 폭의 열로 대신하지 않는다(4.3)
        vdsat_curve(m, "nmos", 200, 1e-6, 0.75, 0.25)
    assert detail_of(ei.value)["reason"] == "lut_column_unavailable"


@pytest.mark.lut_realdata
def test_real_nodes_equal_slice_vdsat(real_memo, raw_slice):
    rng = np.random.default_rng(11)
    for kind in ("nmos", "pmos"):
        for w_key in (1000, 84 if kind == "pmos" else 72):
            z = raw_slice(kind, w_key)
            for _ in range(6):
                i, k, s = int(rng.integers(len(z["L"]))), int(rng.integers(4, len(z["VDS"]))), int(rng.integers(len(z["VS"])))
                c = vdsat_curve(real_memo, kind, w_key, float(z["L"][i]), float(z["VDS"][k]), float(z["VS"][s]))
                j = np.searchsorted(z["VGS"], np.asarray(c.vgs))
                assert np.array_equal(np.asarray(c.values), z["VDSAT"][i, j, k, s])
