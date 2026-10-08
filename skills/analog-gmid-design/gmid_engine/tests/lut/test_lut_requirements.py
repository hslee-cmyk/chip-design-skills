"""`require_lut_data` -- CONTRACT 9.5·10.5 [r7], 설계 41 §7.2 '잡음 데이터가 없는데 잡음 제약이 선언되면 SchemaRejectedError(noise_lut_missing)',
§6.4-2b '감도 데이터가 없는데 offset 제약이 선언되면 SchemaRejectedError(mismatch_lut_missing)'.

oracle (d) 설계 선언 그대로의 거부 사유. 입력 = toy(잡음·mismatch 파일 유무를 이 파일이 정함)."""
import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError
from gmid_engine.lut import require_lut_data

from .conftest import TOY_SHAPE, MismatchToy, NoiseToy, detail_of


def _reason(lut, kinds, **kw):
    with pytest.raises(SchemaRejectedError) as ei:
        require_lut_data(lut, kinds, **kw)
    return detail_of(ei.value)


def test_noise_missing(toy):
    d = _reason(toy, ("nmos",), noise=True)
    assert d["reason"] == "noise_lut_missing" and tuple(d["kinds"]) == ("nmos",)


def test_mismatch_missing(toy):
    d = _reason(toy, ("nmos",), mismatch=True)
    assert d["reason"] == "mismatch_lut_missing" and tuple(d["kinds"]) == ("nmos",)


def test_both_missing_noise_first(toy):
    assert _reason(toy, ("nmos",), noise=True, mismatch=True)["reason"] == "noise_lut_missing"


def test_missing_kinds_sorted(toy):
    d = _reason(toy, ("pmos", "nmos"), noise=True)
    assert tuple(d["kinds"]) == ("nmos", "pmos")


def test_nothing_required_passes(toy):
    assert require_lut_data(toy, ("nmos", "pmos")) is None


def test_present_data_passes(tmp_path):
    n = NoiseToy(tmp_path / "n", np.full(TOY_SHAPE, 1e-12), np.full(TOY_SHAPE, 1e-16))
    lut = n.load()
    assert require_lut_data(lut, ("nmos",), noise=True) is None
    d = _reason(lut, ("nmos",), noise=True, mismatch=True)
    assert d["reason"] == "mismatch_lut_missing"
    m = MismatchToy(tmp_path / "m", {"vth0": np.full(TOY_SHAPE, 1e-3)})
    assert require_lut_data(m.load(), ("nmos",), mismatch=True) is None
