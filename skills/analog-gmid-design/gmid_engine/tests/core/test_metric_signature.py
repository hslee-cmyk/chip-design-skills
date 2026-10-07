"""core CONTRACT 0절 metric_signature.py 행 + SPEC_CONTRACT 4절 + metrics CONTRACT 0절 core 추가:
MetricSignature(unit, domain, view_kind=None, objective_axis=None) -- frozen, unit ∈ METRIC_UNITS(db, hz, deg, ohm, mv, amp, w, m2),
domain ∈ DOMAINS(dc, ss, ls, geom), view_kind ∈ {None} ∪ VIEW_KINDS(transfer, loop, output_port, ratio; 문자열 "none" 은 어휘 밖),
objective_axis ∈ {None} ∪ OBJECTIVE_AXES(power, area). 밖이면 ValueError.
MetricSignature 통일(사용자 승인 2026-10-07): domain 어휘는 DOMAINS 하나(METRIC_DOMAINS 삭제)."""
import pytest

import gmid_engine.core as core
from gmid_engine.core import DOMAINS, METRIC_UNITS, OBJECTIVE_AXES, VIEW_KINDS, MetricSignature

# 계약 문장 그대로의 어휘
WANT_UNITS = {"db", "hz", "deg", "ohm", "mv", "amp", "w", "m2"}
WANT_DOMAINS = {"dc", "ss", "ls", "geom"}
WANT_VIEW_KINDS = {"transfer", "loop", "output_port", "ratio"}
WANT_AXES = {"power", "area"}


def test_defaults():
    s = MetricSignature("db", "ss")
    assert (s.unit, s.domain, s.view_kind, s.objective_axis) == ("db", "ss", None, None)


def test_vocabularies_exact():
    assert set(METRIC_UNITS) == WANT_UNITS
    assert set(DOMAINS) == WANT_DOMAINS
    assert set(VIEW_KINDS) == WANT_VIEW_KINDS
    assert set(OBJECTIVE_AXES) == WANT_AXES


def test_all_units_and_domains_accepted():
    for u in METRIC_UNITS:
        for d in DOMAINS:
            assert MetricSignature(u, d).unit == u


def test_mv_unit_valid():
    """mv 는 통일 때 METRIC_UNITS 에 추가된 단위(mismatch_sigma_mv 등)."""
    s = MetricSignature("mv", "dc")
    assert (s.unit, s.domain) == ("mv", "dc")


def test_metric_domains_not_exported():
    """domain 어휘는 DOMAINS 한 곳 -- METRIC_DOMAINS 는 core 공개 API 에 없다."""
    assert "METRIC_DOMAINS" not in core.__all__
    assert not hasattr(core, "METRIC_DOMAINS")


def test_value_equality():
    assert MetricSignature("hz", "ss", "transfer") == MetricSignature("hz", "ss", "transfer", None)
    assert MetricSignature("hz", "ss", "transfer") != MetricSignature("hz", "ss", "loop")


def test_frozen():
    s = MetricSignature("db", "ss", "transfer")
    with pytest.raises(AttributeError):
        s.unit = "hz"


@pytest.mark.parametrize("unit", ["dB", "Hz", "mV", "W", "A", "volt", "", "rad"])
def test_bad_unit_value_error(unit):
    """옛 대문자 단위(dB·Hz·mV·W·A)는 METRIC_UNITS 밖."""
    with pytest.raises(ValueError):
        MetricSignature(unit, "ss")


@pytest.mark.parametrize("domain", ["ac", "SS", "", "time", "GEOM"])
def test_bad_domain_value_error(domain):
    with pytest.raises(ValueError):
        MetricSignature("db", domain)


@pytest.mark.parametrize("view_kind", [None, "transfer", "loop", "output_port", "ratio"])
def test_view_kind_accepted(view_kind):
    assert MetricSignature("deg", "ss", view_kind).view_kind == view_kind


@pytest.mark.parametrize("view_kind", ["none", "None", "", "port", "TRANSFER", "pending"])
def test_bad_view_kind_value_error(view_kind):
    """문자열 "none" 은 어휘 밖(뷰 없음은 None)."""
    with pytest.raises(ValueError):
        MetricSignature("deg", "ss", view_kind)


@pytest.mark.parametrize("axis", [None, "power", "area"])
def test_objective_axis_accepted(axis):
    assert MetricSignature("amp", "dc", None, axis).objective_axis == axis


@pytest.mark.parametrize("axis", ["none", "Power", "", "noise", "geom"])
def test_bad_objective_axis_value_error(axis):
    with pytest.raises(ValueError):
        MetricSignature("amp", "dc", None, axis)
