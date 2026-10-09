"""`device_sigmas` -- 설계 41 §6.4-2 A_eff 모델(σ_VGS ∝ 1/√(W·L), LUT 감도 열 × bin slope), lut CONTRACT 10.4, metrics CONTRACT 10.9 (4)
(W 가 그 L 의 최대 bin 폭을 넘으면 finger n = ceil(W / w_top) 로 나눠 σ_finger/√n -- 레이아웃 전 가정).

oracle:
* (a) lut CONTRACT 10.4 손계산(tests/lut/test_mismatch_sigma 와 같은 toy): DVGS = (vth0 1, toxe 2, voff 2) mV, 기준 bin slope = 소자 bin slope
  -> W = L = 1 µm 에서 σ = √(1 + 4 + 4) mV = 3 mV.
* (a) 물리 불변식 Pelgrom 면적 법칙 σ ∝ 1/√(W·L): 같은 L·점에서 σ(W) = 3 mV·√(1 µm / W). W 가 bin 최대 폭(toy 10 µm)을 넘어도 같은 법칙이
  성립해야 한다(n 개 독립 병렬 finger 의 합 = 총 면적의 σ) -- finger 수 n 과 무관하다는 것을 W = 25·40 µm(n = 3·4)로 본다.
  오라클 넷리스트도 같은 면적 법칙이다(`tools/spice_oracle/oracle_offset_mc.py` 머리말: σ(ΔP) = slope/√(L·W·m), 인스턴스 w = finger_w·m = n).
* (a) 상수 DVGS 표의 LOO 보간 오차 = 0 -> σ 허용오차 0.
"""
from __future__ import annotations

import math
import types

import numpy as np
import pytest

from gmid_engine.core import PdkMismatchBlock, PdkMismatchModel, SealViolationError
from gmid_engine.metrics import MismatchSource, device_sigmas

from lut.conftest import TOY_SHAPE, MismatchToy, new_memo   # tests 루트 패키지 이름(test_pending_metrics 의 authoring.conftest 와 같은 방식)

DV = {"vth0": 1e-3, "toxe": 2e-3, "voff": 2e-3}
REF = {"vth0": 3e-3, "toxe": 2e-3, "voff": 1e-3}


def _model(wmax=10e-6, lmin=0.5e-6):
    rows = tuple((p, "toy_%s_slope" % p, REF[p], 1 + i) for i, p in enumerate(("toxe", "voff", "vth0")))
    return PdkMismatchModel("nmos", ("toxe", "voff", "vth0"), (PdkMismatchBlock("toy.1", lmin, 5e-6, 0.5e-6, wmax, rows, 10),),
                            "toy.pm3", "0" * 64, "toy.mm", "0" * 64)


@pytest.fixture(scope="module")
def lut(tmp_path_factory):
    t = MismatchToy(tmp_path_factory.mktemp("mm"), {p: np.full(TOY_SHAPE, v) for p, v in DV.items()}, slope_ref=REF)
    return types.SimpleNamespace(memo=new_memo(t.load()))


def _dev(label, W, L=1e-6):
    return (label, "nmos", 100, L, W, 0.5, 0.5, 0.0)


def test_reference_width_hand_value(lut):
    ((label, sigma, tol),) = device_sigmas(lut, MismatchSource((("nmos", _model()),), "0" * 64), (_dev("M1", 1e-6),))
    assert label == "M1"
    assert sigma == pytest.approx(3e-3, rel=1e-12)
    assert tol == pytest.approx(0.0, abs=1e-18)


@pytest.mark.parametrize("W", [4e-6, 10e-6, 25e-6, 40e-6])
def test_pelgrom_area_law_across_finger_split(lut, W):
    ((_l, sigma, _t),) = device_sigmas(lut, MismatchSource((("nmos", _model()),), "0" * 64), (_dev("M1", W),))
    assert sigma == pytest.approx(3e-3 * math.sqrt(1e-6 / W), rel=1e-12)


def test_rows_follow_device_order(lut):
    rows = device_sigmas(lut, MismatchSource((("nmos", _model()),), "0" * 64), (_dev("B", 4e-6), _dev("A", 1e-6)))
    assert [r[0] for r in rows] == ["B", "A"]


def test_missing_kind_or_table_gives_none(lut):
    assert device_sigmas(lut, MismatchSource((), "0" * 64), (_dev("M1", 1e-6),)) is None
    assert device_sigmas(lut, MismatchSource((("nmos", _model()),), "0" * 64), (("M1", "pmos", 100, 1e-6, 1e-6, 0.5, 0.5, 0.0),)) is None


def test_no_bin_for_length_still_fails(lut):
    """bin 이 L 로도 없으면 finger 환산 없이 원래 실패(lut_mismatch_no_block) -- 계약 10.9 (4)."""
    with pytest.raises(SealViolationError) as ei:
        device_sigmas(lut, MismatchSource((("nmos", _model(lmin=2e-6)),), "0" * 64), (_dev("M1", 1e-6),))
    assert dict(ei.value.record.detail)["reason"] == "lut_mismatch_no_block"
