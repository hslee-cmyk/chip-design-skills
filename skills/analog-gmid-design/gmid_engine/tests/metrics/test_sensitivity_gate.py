"""`sensitivity_gate` -- 설계 40 §3.8-2: 분해 metric 이 읽지 않는 소자를 건드리는 섭동에서 '분해 값 변화 ≤ ε 인데 MNA 값 변화 > ε' 이면 오류,
ε = ‖A·x − b‖₂/‖b‖₂ × 그 metric 의 x 감도(이득 dB 의 상대 변화 감도 = 20/ln 10), 체크리스트 D-SG, 계약 10.0.

oracle (a): ε 를 손으로 -- 잔차 1e-12 -> ε = 1e-12·20/ln 10 = 8.686e-12 dB. 잔차 0 이면 부동소수 해상도(2.22e-16) 바닥 -> 1.93e-15 dB.
"""
from __future__ import annotations

import math
import sys

import pytest

from gmid_engine.metrics import GateResult, sensitivity_gate

K = 20.0 / math.log(10.0)


def test_error_when_mna_moves_but_decomposition_does_not():
    base = (60.0, 60.0, 1e-12)
    runs = (("current:I1", 60.0, 60.5, 1e-12),          # 분해 그대로, MNA 0.5 dB -> 오류
            ("L:M9", 60.3, 60.3, 1e-12),                # 둘 다 움직임 -> 정상
            ("ln_idu:M2", 60.0, 60.0, 1e-12))           # 둘 다 그대로 -> 정상
    got = sensitivity_gate(base, runs)
    assert isinstance(got, GateResult)
    assert got.ok is False and got.errors == ("current:I1",)
    eps = 1e-12 * K
    assert got.epsilon == pytest.approx(eps, rel=1e-12)
    checks = {c[0]: c for c in got.checks}
    assert checks["current:I1"][1:] == (0.0, pytest.approx(0.5), pytest.approx(eps, rel=1e-12), True)
    assert checks["L:M9"][4] is False and checks["ln_idu:M2"][4] is False


def test_epsilon_uses_larger_residual_and_float_floor():
    got = sensitivity_gate((60.0, 60.0, 0.0), (("a", 60.0, 60.0, 0.0),))
    assert got.epsilon == pytest.approx(sys.float_info.epsilon * K, rel=1e-12)
    got = sensitivity_gate((60.0, 60.0, 1e-13), (("a", 60.0, 60.0, 3e-11),))
    assert got.epsilon == pytest.approx(3e-11 * K, rel=1e-12)


def test_change_within_epsilon_is_not_error():
    eps = 1e-10 * K
    got = sensitivity_gate((40.0, 40.0, 1e-10), (("a", 40.0, 40.0 + 0.5 * eps, 1e-10),))
    assert got.ok is True and got.errors == ()


def test_undefined_values_unchecked_not_error():
    got = sensitivity_gate((40.0, 40.0, 1e-12), (("a", None, 41.0, 1e-12), ("b", 40.0, 41.0, None)))
    assert got.ok is True and got.errors == ()
    assert [c[4] for c in got.checks] == [None, None]
    assert got.epsilon is None
    assert sensitivity_gate((None, 40.0, 1e-12), (("a", 40.0, 41.0, 1e-12),)).ok is True


def test_no_runs():
    assert sensitivity_gate((40.0, 40.0, 1e-12), ()) == GateResult(True, (), (), None)
