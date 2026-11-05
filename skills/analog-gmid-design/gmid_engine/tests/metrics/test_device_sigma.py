"""`device_sigmas` -- 설계 41 §6.4-2 A_eff 모델(σ_VGS ∝ 1/√(W·L), LUT 감도 열 × bin slope), lut CONTRACT 10.4, metrics CONTRACT 10.9 (4)
(WB-1 D-3: slope bin 은 손가락 폭 w_f 로 고르고 면적 항은 총 폭 W 로 센다 -- σ = √(Σ(DVGS_k·slope_k(bin(w_f, L))/slope_k(bin_ref))²)·√(W_ref/W)).
소자 행 = (label, kind, w_key, L, W, vgs, vds, vsb, w_f).

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
                            "0" * 64, "0" * 64)  # [U17 ①-b 3차, 결정 7] 경로 칸 없음: (model_sha256, slope_sha256)


@pytest.fixture(scope="module")
def lut(tmp_path_factory):
    t = MismatchToy(tmp_path_factory.mktemp("mm"), {p: np.full(TOY_SHAPE, v) for p, v in DV.items()}, slope_ref=REF)
    return types.SimpleNamespace(memo=new_memo(t.load()))


def _dev(label, W, L=1e-6, w_f=1e-6):
    """w_f = 손가락 폭(기본 1 µm = 기준 폭, 총 폭 W = m·w_f). 옛 finger 환산 대신 W 가 면적 항으로만 든다."""
    return (label, "nmos", 100, L, W, 0.5, 0.5, 0.0, w_f)


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
    assert device_sigmas(lut, MismatchSource((("nmos", _model()),), "0" * 64), (("M1", "pmos", 100, 1e-6, 1e-6, 0.5, 0.5, 0.0, 1e-6),)) is None


def test_no_bin_for_length_still_fails(lut):
    """bin 이 L 로도 없으면 finger 환산 없이 원래 실패(lut_mismatch_no_block) -- 계약 10.9 (4)."""
    with pytest.raises(SealViolationError) as ei:
        device_sigmas(lut, MismatchSource((("nmos", _model(lmin=2e-6)),), "0" * 64), (_dev("M1", 1e-6),))
    assert dict(ei.value.record.detail)["reason"] == "lut_mismatch_no_block"


def _two_bin_model():
    """card §5 D-3 합성 mismatch 모델: W bin (1e-6, 3e-6) slope = 기준 slope 의 1배, (3e-6, 7e-6) slope = 2배. L 범위는 둘 다 (0.5e-6, 5e-6)."""
    def rows(scale):
        return tuple((p, "toy_%s_slope" % p, REF[p] * scale, 1 + i) for i, p in enumerate(("toxe", "voff", "vth0")))
    return PdkMismatchModel("nmos", ("toxe", "voff", "vth0"),
                            (PdkMismatchBlock("toy.1", 0.5e-6, 5e-6, 1e-6, 3e-6, rows(1.0), 10),
                             PdkMismatchBlock("toy.2", 0.5e-6, 5e-6, 3e-6, 7e-6, rows(2.0), 20)), "0" * 64, "0" * 64)


def test_slope_bin_follows_finger_width_and_area_term_follows_total_width(lut):
    """oracle (a): 기준 bin(W_ref = 1 µm) slope = 소자 bin slope 이면 σ = 3 mV(DV 1·2·2 mV), 2배 slope bin 이면 6 mV. 면적 항 √(W_ref/W): W = 8 µm -> 1/√8.
    w_f = 2 µm(bin 1배), W = 8 µm -> σ = 3 mV/√8. w_f = 5 µm(bin 2배), W = 8 µm -> 6 mV/√8. 총 폭 8 µm 로 bin 을 고르면 어느 bin 에도 없다(최대 7 µm) -> 실패였다."""
    src = MismatchSource((("nmos", _two_bin_model()),), "0" * 64)
    ((_l, s1, _t1),) = device_sigmas(lut, src, (_dev("A", 8e-6, w_f=2e-6),))
    ((_l, s2, _t2),) = device_sigmas(lut, src, (_dev("B", 8e-6, w_f=5e-6),))
    assert s1 == pytest.approx(3e-3 / math.sqrt(8.0), rel=1e-12)
    assert s2 == pytest.approx(6e-3 / math.sqrt(8.0), rel=1e-12)
    assert s2 == pytest.approx(2.0 * s1, rel=1e-12)                            # 같은 총 폭, bin 만 다르다 -- 판별력
    with pytest.raises(SealViolationError) as ei:                            # 총 폭으로 bin 을 고르는 옛 규칙이면 성립하지 않는 입력
        device_sigmas(lut, src, (_dev("C", 8e-6, w_f=8e-6),))
    assert dict(ei.value.record.detail)["reason"] == "lut_mismatch_no_block"

