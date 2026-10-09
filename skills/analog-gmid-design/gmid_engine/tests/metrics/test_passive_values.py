"""`metrics.passive_values(snapshot, ctx, theta)` -- 수동소자 값 정본 (metrics CONTRACT 7.6, DEC-92, 설계 40 §11 U14 '공개 passive_values').

oracle (a)·(d): 가짜 스냅샷·ctx·θ(피검이 읽는 속성만)에 손으로 둔 세 출처 -- spec 선언 값, θ 저항·커패시터·ss 저항, 영점 상쇄 구조 규칙 저항.
영점 상쇄 저항 값은 회로 해석(Miller 영점을 지우는 직렬 저항 = 1/(그 단의 gm 합))에서 손으로: gm 1 mS + 3 mS -> 250 Ω.
실경로(two_stage_ota Rz = 1/gm(M6))는 tests/convergence/test_converge.py 에서 본다(같은 값이 판정 축 면적 입력으로 간다).
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

import gmid_engine.metrics as metrics
from gmid_engine.metrics import passive_values


class Snap:
    def __init__(self, classes, gm):
        self.classes, self.gm = classes, gm

    def column(self, table, field):
        if (table, field) == ("device", "element_class"):
            return tuple(sorted(self.classes.items()))
        if (table, field) == ("device", "ss_dev"):
            return tuple(sorted((m, SimpleNamespace(gm=g)) for m, g in self.gm.items()))
        raise KeyError((table, field))


def ctx(values, zero_cancel=()):
    return SimpleNamespace(inputs=SimpleNamespace(element_values=tuple(values)),
                           schema=SimpleNamespace(zero_cancel=tuple(zero_cancel)))


def zc(resistor, cells, reason=None):
    return SimpleNamespace(resistor=resistor, cells=tuple(cells), reason=reason)


def theta(pairs):
    return SimpleNamespace(values=tuple(pairs))


CLASSES = {"M1": "mos", "M2": "mos", "R1": "passive", "C1": "passive", "Rs": "passive", "CL": "passive", "Cx": "passive",
           "Rz": "passive", "Rq": "passive", "V1": "ideal_source"}
GM = {"M1": 1e-3, "M2": 3e-3}


def test_public():
    assert "passive_values" in metrics.__all__


def test_three_sources_merged_sorted():
    c = ctx((("CL", 3e-12), ("Cx", None), ("V1", 0.9)), (zc("Rz", ("M1", "M2")), zc("Rq", ("M1",), reason="pending")))
    th = theta(((("resistance", "R1"), 1e3), (("capacitance", "C1"), 2e-12), (("ss_resistance", "Rs"), 5e4),
                (("ln_idu", "M1"), -14.0), (("current", "M2"), 1e-5)))
    out = passive_values(Snap(CLASSES, GM), c, th)
    assert [n for n, _v in out] == ["C1", "CL", "R1", "Rs", "Rz"]     # 이름순, 값 없는 Cx·reason 있는 Rq·비수동 V1 제외
    got = dict(out)
    assert (got["C1"], got["CL"], got["R1"], got["Rs"]) == (2e-12, 3e-12, 1e3, 5e4)
    assert got["Rz"] == pytest.approx(250.0, rel=1e-15)                  # 1 / (1 mS + 3 mS)
    assert all(isinstance(v, float) for v in got.values())


def test_theta_name_not_a_passive_is_rejected():
    with pytest.raises(ValueError):
        passive_values(Snap(CLASSES, GM), ctx(()), theta(((("resistance", "M1"), 1e3),)))


def test_same_passive_from_two_sources_is_rejected():
    with pytest.raises(ValueError):
        passive_values(Snap(CLASSES, GM), ctx((("C1", 1e-12),)), theta(((("capacitance", "C1"), 2e-12),)))
    with pytest.raises(ValueError):
        passive_values(Snap(CLASSES, GM), ctx((), (zc("R1", ("M1",)),)), theta(((("resistance", "R1"), 1e3),)))


def test_structural_resistor_must_be_passive():
    with pytest.raises(ValueError):
        passive_values(Snap(CLASSES, GM), ctx((), (zc("V1", ("M1",)),)), theta(()))


def test_no_sources_gives_empty():
    assert passive_values(Snap({"M1": "mos"}, {"M1": 1e-3}), ctx(()), theta(())) == ()
