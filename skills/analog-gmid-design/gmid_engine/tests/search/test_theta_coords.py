"""[XRUN-F1 card A] `ThetaCoords` -- interface card xrunf1a C1(공개면: `start(variables, theta)`, `to_theta(x)`, 읽기 전용 `x0`).

계약(C1): 시작 좌표 x0ᵢ = math.log(θᵢ)(log 변수) 또는 θᵢ(그 밖), 자르지 않는다. `to_theta(x)`: v = float(x[i]) 가 x0ᵢ 와 정확히 같으면 θᵢ 원값,
아니면 log 변수는 math.exp(v), 그 밖은 v. 변수 밖 성분은 theta 값 그대로, 반환은 호출마다 새 dict(키 = theta 의 키 전부). clip 같은 다른
인자는 TypeError(X-14).

oracle: (Py) 기대 좌표·값은 이 파일이 Python `math` 로 따로 만든다(x0 = math.log(θ), 바뀐 성분 = math.exp(x0 + δ)). (식) 원값 보존 규칙은
C1 문장. 비트 비교는 float.hex. 피검 함수 출력으로 기대값을 만들지 않는다. 엔진 소스는 열람하지 않았다(interface card 만).

θ 값은 math.exp(math.log(θ)) != θ 인 것을 골랐다(1e-5·9e4 -- 각 test 가 그 전제를 먼저 단언해 원값 보존 단언이 공허하지 않게 한다).
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from gmid_engine.search import ThetaCoords, Variable

# 손으로 정한 변수 셋: log 둘(전류·저항), 선형 하나(ln_idu), 변수 밖 성분 하나(L).
I1 = ("current", "I1")
R1 = ("resistance", "R1")
U1 = ("ln_idu", "M1")
L1 = ("L", "M1")
THETA = {I1: 1e-5, R1: 9e4, U1: -3.1, L1: 1e-6}
# bounds 는 ln 좌표(log 변수)·값(선형)으로 -- 이 셋은 시작 좌표를 모두 안에 둔다(ln 1e-5 ≈ −11.5, ln 9e4 ≈ 11.4).
VARS_IN = (Variable(I1, True, -20.0, 0.0), Variable(R1, True, 6.0, 12.0), Variable(U1, False, -30.0, -1.0))
# 시작 좌표가 bounds 밖인 셋(A-T3): 전류 [0, 10](ln 1e-5 < 0), ln_idu [0, 1](−3.1 < 0)
VARS_OUT = (Variable(I1, True, 0.0, 10.0), Variable(R1, True, 6.0, 12.0), Variable(U1, False, 0.0, 1.0))


def _hex(theta):
    return {k: float(v).hex() for k, v in dict(theta).items()}


def _x0_expected(variables, theta):
    """(Py) C1 시작 좌표: log 변수 math.log(θ), 그 밖 θ -- 자르지 않음."""
    return tuple(math.log(theta[v.component]) if v.log else theta[v.component] for v in variables)


def test_theta_coords_premise_round_trip_breaks():
    """전제(공허 방지): 고른 log 변수 θ 는 math.exp(math.log(θ)) 왕복이 원값을 잃는다(원값 보존 단언이 의미 있다)."""
    for comp in (I1, R1):
        assert math.exp(math.log(THETA[comp])) != THETA[comp], comp


@pytest.mark.parametrize("as_type", ["tuple", "list", "ndarray"])
def test_theta_coords_start_point_bits_preserved(as_type):
    """A-T1: to_theta(x0) 가 θ 와 성분마다 비트 동일(변수 밖 성분 L 포함), x0 = test 가 math.log 로 만든 좌표와 비트 동일."""
    coords = ThetaCoords.start(VARS_IN, dict(THETA))
    want_x0 = _x0_expected(VARS_IN, THETA)                                  # (Py)
    assert tuple(float(v).hex() for v in coords.x0) == tuple(float(v).hex() for v in want_x0)
    x = {"tuple": tuple(want_x0), "list": list(want_x0), "ndarray": np.asarray(want_x0, dtype=float)}[as_type]
    got = coords.to_theta(x)
    assert set(got) == set(THETA)                                           # 키 = theta 의 키 전부
    assert _hex(got) == _hex(THETA)                                         # (식) 시작 좌표 -> 원값(비트)


def test_theta_coords_returns_new_dict_each_call():
    """C1: 반환은 호출마다 새 dict -- 한 반환을 고쳐도 다음 반환·theta 원본은 그대로."""
    theta = dict(THETA)
    coords = ThetaCoords.start(VARS_IN, theta)
    a = coords.to_theta(coords.x0)
    b = coords.to_theta(coords.x0)
    assert a is not b
    a[I1] = 123.0
    assert _hex(coords.to_theta(coords.x0)) == _hex(THETA)
    assert _hex(theta) == _hex(THETA)


@pytest.mark.parametrize("i", [0, 1, 2], ids=["log_current", "log_resistance", "linear_ln_idu"])
def test_theta_coords_one_coordinate_moved(i):
    """A-T2: 좌표 하나만 x0ᵢ + δ 로 바꾼 x -- 그 성분 = math.exp(x0ᵢ + δ)(log) 또는 x0ᵢ + δ(선형), 나머지 변수·변수 밖 성분은 θ 비트 그대로.
    δ = 0.25(2진 정확값, bounds 안에 머무는 크기 -- 구성 입력)."""
    delta = 0.25
    coords = ThetaCoords.start(VARS_IN, dict(THETA))
    x0 = _x0_expected(VARS_IN, THETA)
    x = list(x0)
    x[i] = x0[i] + delta
    assert x[i] != x0[i]                                                    # 전제: 정말 다른 좌표
    got = coords.to_theta(x)
    v = VARS_IN[i]
    want = math.exp(x0[i] + delta) if v.log else x0[i] + delta              # (Py)+(식)
    assert float(got[v.component]).hex() == float(want).hex()
    rest = {k: val for k, val in _hex(got).items() if k != v.component}
    assert rest == {k: val for k, val in _hex(THETA).items() if k != v.component}


def test_theta_coords_start_not_clipped_outside_bounds():
    """A-T3: 시작 θ 가 변수 bounds 밖이어도 x0 은 잘리지 않는다 -- x0 = math.log(θ)/θ 그대로, to_theta(x0) = θ 원값(비트).
    test 가 math.log 로 만든 x0 을 그대로 넘겨도 원값."""
    coords = ThetaCoords.start(VARS_OUT, dict(THETA))
    want_x0 = _x0_expected(VARS_OUT, THETA)
    # 전제: 두 성분의 시작 좌표가 정말 bounds 밖(자르면 달라진다)
    outside = [v for v, x in zip(VARS_OUT, want_x0) if not (v.lo <= x <= v.hi)]
    assert [v.component for v in outside] == [I1, U1]
    assert tuple(float(v).hex() for v in coords.x0) == tuple(float(v).hex() for v in want_x0)
    assert _hex(coords.to_theta(coords.x0)) == _hex(THETA)
    assert _hex(coords.to_theta(tuple(want_x0))) == _hex(THETA)


@pytest.mark.parametrize("kw", [{"clip": True}, {"clip": False}])
def test_theta_coords_start_rejects_clip_keyword(kw):
    """A-T4: X-14 -- start 는 (variables, theta) 뿐, clip 인자는 TypeError. 대조군: 같은 인자에서 clip 만 빼면 만들어진다."""
    with pytest.raises(TypeError):
        ThetaCoords.start(VARS_IN, dict(THETA), **kw)
    assert ThetaCoords.start(VARS_IN, dict(THETA)) is not None
