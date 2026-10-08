"""`_helpers_grids` (`npz_grids`·`npz_condition_mismatch` -- lut_set·noise_set·mismatch_set 공용) -- CONTRACT 0절 [r7]·9.1·10.1.

공개 진입점(`load_lut_set(noise_npz=, mismatch_npz=)`)의 거부로 본다(helper 직접 import 금지). 규칙(계약 1.4 불변식과 같은 뜻):
축은 float 단위로 같아야 하고(1 ulp 차이도 다름), 측정 조건(corner·temp_c)이 기록돼 있으면 기준 LUT 와 같아야 한다.
oracle (a): 한 원소만 바꾼 toy 입력."""
import math

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError

from .conftest import TOY_SHAPE, TOY_VDS, MismatchToy, NoiseToy, detail_of


def _noise(tmp_path, **kw):
    return NoiseToy(tmp_path / "n", np.full(TOY_SHAPE, 1e-12), np.full(TOY_SHAPE, 1e-16), **kw)


def _mm(tmp_path, **kw):
    return MismatchToy(tmp_path / "m", {"vth0": np.full(TOY_SHAPE, 1e-3)}, **kw)


def _one_ulp_vds(a):
    v = np.asarray(TOY_VDS, dtype=float).copy()
    v[-1] = math.nextafter(v[-1], 2.0)
    a["VDS"] = v


@pytest.mark.parametrize("make,reason", [(_noise, "lut_noise_axes_mismatch"), (_mm, "lut_mismatch_axes_mismatch")])
def test_one_ulp_axis_difference_rejected(tmp_path, make, reason):
    key = "noise_mutate" if make is _noise else "mm_mutate"
    t = make(tmp_path, **{key: _one_ulp_vds})
    with pytest.raises(SchemaRejectedError) as ei:
        t.load()
    assert detail_of(ei.value)["reason"] == reason


@pytest.mark.parametrize("make", [_noise, _mm])
@pytest.mark.parametrize("cond", [("corner", np.str_("ss")), ("temp_c", np.float64(27.000001))])
def test_condition_difference_rejected(tmp_path, make, cond):
    key = "noise_mutate" if make is _noise else "mm_mutate"
    t = make(tmp_path, **{key: lambda a: a.update({cond[0]: cond[1]})})
    with pytest.raises(SchemaRejectedError) as ei:
        t.load()
    assert detail_of(ei.value)["reason"] == "lut_conditions_mismatch"


@pytest.mark.parametrize("make", [_noise, _mm])
def test_identical_axes_and_conditions_load(tmp_path, make):
    lut = make(tmp_path).load()
    assert ("nmos" in lut.noise) or ("nmos" in lut.mismatch)
