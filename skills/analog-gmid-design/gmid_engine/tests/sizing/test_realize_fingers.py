"""FS-1 §1 -- `realize_fingers(w_theta, w_f_m, ratios)` 실현 정수화 (interface card 20261107-fs1 §1 R-1~R-8, R-E3, F-1, F-2, P-1~P-5, R-E5, R-T, R-V, R-K, R-E).

oracle 종류: (손) -- interface §1 정의 1~4를 그대로 쓴 곱집합 전수 함수 `hand_oracle` (이 파일 안 -- 피검 함수 아님)와
card 작성자 손값 표(`fs1_hand2_out.txt`, 정확 산술 `Fraction` 답과 같음)의 기대 `m` 리터럴. 기대 E1·E2 는 기대 `m` 에 §1 4의 식을
같은 부동소수 꼴로 적용해 `==` 비교(허용오차 상수 0). 피검 함수·엔진 함수로 기대값을 만들지 않는다. 모든 행 w_f_m = 1.0.
"""
import itertools
import math

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DeclaredRatio, RealizedCell, realize_fingers


# ---------------------------------------------------------------- 손 oracle (interface §1 정의 1~4)
def _options(x, ratios):
    """단위(unit)마다 (멤버 위치 tuple, 선택지 [m 벡터 조각 dict]) 목록. 정의 2."""
    units = []
    for rt in ratios:
        ks = [k for _, k in rt.outputs_with_k]
        if all(float(k) == int(k) and k >= 1 for k in ks):
            d = rt.reference
            cand = {max(1, math.floor(x[d])), max(1, math.ceil(x[d]))}
            for o, k in rt.outputs_with_k:
                cand |= {max(1, math.floor(x[o] / k)), max(1, math.ceil(x[o] / k))}
            members = (d,) + tuple(o for o, _ in rt.outputs_with_k)
            opts = []
            for md in sorted(cand):
                piece = {d: md}
                for o, k in rt.outputs_with_k:
                    piece[o] = int(k) * md
                opts.append(piece)
            units.append(opts)
        # 비정수 k 묶음: 멤버 모두 독립 단위 (아래 indep 에 그대로 든다)
    indep = [i for i in range(len(x)) if i not in {m for u in units for m in u[0]}]
    for i in indep:
        units.append([{i: max(1, math.floor(x[i]))}, {i: max(1, math.ceil(x[i]))}])
    return units


def hand_oracle(w_theta, w_f, ratios=()):
    x = [w / w_f for w in w_theta]
    units = _options(x, ratios)
    best = None
    for combo in itertools.product(*units):
        mv = {}
        for piece in combo:
            mv.update(piece)
        m = tuple(mv[i] for i in range(len(x)))
        r = [m[i] / x[i] for i in range(len(x))]
        e = [abs(m[i] - x[i]) / x[i] for i in range(len(x))]
        key = (max(r) / min(r) - 1, max(e), math.fsum(e), sum(m), tuple(m))
        if best is None or key < best:
            best = key
    return best          # (E1, E2, E3, E4, E5)


def hand_e1_e2(w_theta, w_f, m):
    x = [w / w_f for w in w_theta]
    r = [m[i] / x[i] for i in range(len(x))]
    e = [abs(m[i] - x[i]) / x[i] for i in range(len(x))]
    return max(r) / min(r) - 1, max(e)


# ---------------------------------------------------------------- 값 표 (interface §1 toy R/F/P)
D = DeclaredRatio
ROWS = [
    ("R-1", (10.4, 10.6), (), (10, 10), (0.019230769230769162, 0.05660377358490563)),
    ("R-2", (4.235, 5.0), (), (4, 5), (0.05875000000000008, 0.05548996458087374)),
    ("R-3", (1.4, 7.3), (D(0, ((1, 5.0),)),), (1, 5), (0.04285714285714293, 0.3150684931506849)),
    ("R-3b", (1.4, 7.3), (D(0, ((1, 2.5),)),), (2, 8), (0.3035714285714286, 0.42857142857142866)),
    ("R-4", (2.2, 4.3, 1.3, 4.1), (D(0, ((1, 2.0),)), D(2, ((3, 3.0),))), (3, 6, 2, 6),
     (0.1282051282051282, 0.5384615384615384)),
    ("R-5", (2.5,), (), (2,), (0.0, 0.2)),
    ("R-6", (0.4,), (), (1,), (0.0, 1.4999999999999998)),
    ("R-6b", (0.4, 0.7), (), (1, 1), (0.75, 1.4999999999999998)),
    ("R-7", (3.6,), (), (4,), (0.0, 0.11111111111111108)),
    ("R-8", (1.4, 2.6), (), (1, 2), (0.07692307692307687, 0.28571428571428564)),
    ("R-E3", (1.25, 1.75, 4.75), (), (1, 2, 5), (0.4285714285714284, 0.2)),
    ("F-1", (1.0, 46 / 3), (), (1, 15), None),
    ("F-2", (1.25, 1.75, 3.5, 3.5), (D(0, ((1, 3.0),)),), (1, 3, 3, 3), (1.1428571428571428, 0.7142857142857143)),
    ("P-1", (3.3, 3.7, 4.1), (), (4, 4, 5), (0.1280487804878052, 0.21951219512195133)),
    ("P-2", (1.2, 2.9, 5.5, 5.4), (D(0, ((1, 2.0),)),), (1, 2, 5, 5), (0.34259259259259234, 0.31034482758620685)),
    ("P-3", (6.6, 6.4, 2.1), (D(2, ((0, 3.0), (1, 3.0))),), (6, 6, 2), (0.04761904761904745, 0.09090909090909086)),
    ("P-4", (0.6, 1.6, 2.6), (), (1, 2, 3), (0.44444444444444464, 0.6666666666666667)),
    ("P-5", (7.49, 7.51), (), (7, 7), (0.0026702269692922, 0.06790945406125164)),
]
IDS = [r[0] for r in ROWS]


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_realize_value_rows(row):
    """R/F/P 값 행: 반환 m = card 손값 리터럴 = 손 oracle(K 전체 -- E5 포함) 답, E1·E2 = 손 꼴 `==` (R-E, R-E5 (c))."""
    _id, w, ratios, want_m, ref = row
    out = realize_fingers(w, 1.0, ratios)
    assert isinstance(out, RealizedCell)
    assert out.m == want_m                                                      # card 손값 (정확 산술 답과 같음)
    assert out.m == hand_oracle(w, 1.0, ratios)[4]                              # 곱집합 전수 K 사전식 최소 (E5 = m 자신)
    e1, e2 = hand_e1_e2(w, 1.0, want_m)
    assert out.ratio_err == e1 and out.member_err == e2                         # 같은 부동소수 꼴 `==`
    assert (e1, e2) == hand_oracle(w, 1.0, ratios)[:2]
    if ref is not None:                                                         # 참고 값 대조 (card 손값 표)
        assert e1 == pytest.approx(ref[0], rel=1e-9, abs=1e-15) and e2 == pytest.approx(ref[1], rel=1e-9, abs=1e-15)


def test_realize_mirror_ratio_vs_member_rounding_distinct():
    """가르는 것: R-1 은 멤버별 반올림 (10, 11) 이 아님, R-2 는 전류 비 목표 (5, 5) 가 아님, R-3 은 m_d=2 → (2, 10) 이 아님."""
    assert realize_fingers((10.4, 10.6), 1.0, ()).m != (10, 11)
    assert realize_fingers((4.235, 5.0), 1.0, ()).m != (5, 5)
    assert realize_fingers((1.4, 7.3), 1.0, (D(0, ((1, 5.0),)),)).m != (2, 10)
    assert realize_fingers((1.4, 7.3), 1.0, (D(0, ((1, 5.0),)),)).m == (1, 5)    # 양성 대조


@pytest.mark.parametrize("row", ROWS, ids=IDS)
def test_realize_deterministic_and_shape(row):
    """R-E5 (a) 같은 입력 두 호출 `==` (b) m 길이 = 입력 길이, 원소 int ≥ 1."""
    _id, w, ratios, _m, _ref = row
    a, b = realize_fingers(w, 1.0, ratios), realize_fingers(w, 1.0, ratios)
    assert a == b
    assert len(a.m) == len(w)
    assert all(type(v) is int and v >= 1 for v in a.m)


def test_realize_f1_comparison_form_fixed():
    """F-1 (E1 비교 꼴 고정): 최적 단위가 창에서 빠지면 (1, 15) 가 아니게 된다. 손 oracle 답 (1, 15) 와 같아야 한다."""
    w = (1.0, 46 / 3)
    assert hand_oracle(w, 1.0)[4] == (1, 15)
    assert realize_fingers(w, 1.0, ()).m == (1, 15)


def test_realize_f2_error_form_fixed():
    """F-2 (오차 꼴 고정): `e = abs(r - 1)` 꼴이면 1 ulp 차로 (1, 3, 3, 4) -- 정확 산술 답은 (1, 3, 3, 3)."""
    out = realize_fingers((1.25, 1.75, 3.5, 3.5), 1.0, (D(0, ((1, 3.0),)),))
    assert out.m == (1, 3, 3, 3) and out.m != (1, 3, 3, 4)


# ---------------------------------------------------------------- R-T 분류된 실패
@pytest.mark.parametrize("w_theta,w_f", [((1.0, 0.0), 1.0), ((1.0, float("nan")), 1.0), ((1.0, -2.0), 1.0),
                                         ((1.0, float("inf")), 1.0), ((1.0, 2.0), 0.0)])
def test_realize_tie_unresolved(w_theta, w_f):
    assert realize_fingers((1.0, 2.0), 1.0, ()).m == (1, 2)                     # 양성 대조: 정상 입력은 통과
    with pytest.raises(SealViolationError) as ei:
        realize_fingers(w_theta, w_f, ())
    d = dict(ei.value.record.detail)
    assert d["reason"] == "realize_tie_unresolved"
    assert "w_theta" in d and "w_f_m" in d


# ---------------------------------------------------------------- R-V, R-K 계약 위반 (ValueError)
def test_realize_ratios_position_out_of_range():
    with pytest.raises(ValueError):
        realize_fingers((1.4, 7.3), 1.0, (D(0, ((5, 2.0),)),))


def test_realize_member_in_two_groups():
    with pytest.raises(ValueError):
        realize_fingers((1.4, 7.3, 2.0), 1.0, (D(0, ((1, 2.0),)), D(1, ((2, 2.0),))))


def test_realize_reference_is_own_output():
    with pytest.raises(ValueError):
        realize_fingers((1.4, 7.3), 1.0, (D(0, ((0, 2.0),)),))


@pytest.mark.parametrize("k", [float("inf"), float("nan"), 0.0, -2.0])
def test_realize_declared_k_invalid(k):
    assert realize_fingers((1.4, 7.3), 1.0, (D(0, ((1, 5.0),)),)).m == (1, 5)   # 양성 대조
    with pytest.raises(ValueError) as ei:
        realize_fingers((1.4, 7.3), 1.0, (D(0, ((1, k),)),))
    assert "declared_ratio_invalid" in str(ei.value)
