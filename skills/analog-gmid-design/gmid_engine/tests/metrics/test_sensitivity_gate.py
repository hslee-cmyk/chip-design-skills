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
    """[UB-1 E-01 뜻 교체, fail-open -> fail-closed] 값이 없는 섭동·기준은 '통과'가 아니라 undeterminable(ok False).
    oracle (a): C-10 우선순위 -- 오류 없고 None 섭동 있음 -> undeterminable/perturbation_unmeasured, unmeasured = 그 이름;
    base 에 None -> undeterminable/base_undefined, unmeasured = 전 이름."""
    got = sensitivity_gate((40.0, 40.0, 1e-12), (("a", None, 41.0, 1e-12),))
    assert got.ok is False and got.errors == ()
    assert got.verdict == "undeterminable" and got.reason == "perturbation_unmeasured"
    assert got.unmeasured == ("a",)
    assert [c[4] for c in got.checks] == [None]
    # 칸 하나만 None 이어도(분해 dB·전회로 dB·잔차 중 어느 하나) None 섭동(C-10 문언)
    both = sensitivity_gate((40.0, 40.0, 1e-12), (("a", None, 41.0, 1e-12), ("b", 40.0, 41.0, None)))
    assert both.ok is False and both.verdict == "undeterminable" and both.reason == "perturbation_unmeasured"
    assert both.unmeasured == ("a", "b") and [c[4] for c in both.checks] == [None, None]
    only_b = sensitivity_gate((40.0, 40.0, 1e-12), (("b", 40.0, 41.0, None),))
    assert only_b.verdict == "undeterminable" and only_b.unmeasured == ("b",)
    base_none = sensitivity_gate((None, 40.0, 1e-12), (("a", 40.0, 41.0, 1e-12), ("b", 40.0, 40.0, 1e-12)))
    assert base_none.ok is False and base_none.verdict == "undeterminable" and base_none.reason == "base_undefined"
    assert base_none.unmeasured == ("a", "b")
    assert sensitivity_gate((40.0, None, 1e-12), (("a", 40.0, 41.0, 1e-12),)).reason == "base_undefined"
    assert sensitivity_gate((40.0, 40.0, None), (("a", 40.0, 41.0, 1e-12),)).reason == "base_undefined"


def test_no_runs():
    """[UB-1 E-01 뜻 교체] 섭동이 없으면 통과가 아니다: gate_empty/no_perturbation(ok False). runs 빈 것이 base None 보다 먼저."""
    got = sensitivity_gate((40.0, 40.0, 1e-12), ())
    assert got.ok is False and got.verdict == "gate_empty" and got.reason == "no_perturbation"
    assert got.errors == () and got.unmeasured == ()
    assert sensitivity_gate((None, None, None), ()).reason == "no_perturbation"


def test_ub1_verdict_priority_error_beats_unmeasured():
    """T-6 (a): 오류 >= 1 이면 verdict error(reason None), None 섭동은 unmeasured 에 남는다."""
    base = (60.0, 60.0, 1e-12)
    got = sensitivity_gate(base, (("current:I1", 60.0, 60.5, 1e-12), ("b", None, 61.0, 1e-12)))
    assert got.ok is False and got.verdict == "error" and got.reason is None
    assert got.errors == ("current:I1",) and got.unmeasured == ("b",)


def test_ub1_verdict_ok_branch():
    """T-6 (a): 모두 측정되고 오류 없으면 ok(reason None, unmeasured 빈) -- ok 칸 == (verdict == "ok")."""
    got = sensitivity_gate((60.0, 60.0, 1e-12), (("a", 60.0, 60.0, 1e-12), ("b", 60.3, 60.3, 1e-12)))
    assert got.verdict == "ok" and got.reason is None and got.unmeasured == () and got.errors == ()
    assert got.ok is True
    assert got.epsilon == pytest.approx(1e-12 * K, rel=1e-12)
