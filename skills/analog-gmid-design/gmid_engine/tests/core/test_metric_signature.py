"""metrics CONTRACT 0절 core 추가: MetricSignature(unit, domain, view_kind=None, objective_axis=None) -- unit ∈ METRIC_UNITS,
domain ∈ DOMAINS 아니면 ValueError."""
import pytest

from gmid_engine.core import DOMAINS, METRIC_UNITS, MetricSignature


def test_defaults():
    s = MetricSignature("db", "ss")
    assert (s.unit, s.domain, s.view_kind, s.objective_axis) == ("db", "ss", None, None)


def test_all_units_and_domains_accepted():
    for u in METRIC_UNITS:
        for d in DOMAINS:
            assert MetricSignature(u, d).unit == u


def test_value_equality():
    assert MetricSignature("hz", "ss", "transfer") == MetricSignature("hz", "ss", "transfer", None)
    assert MetricSignature("hz", "ss", "transfer") != MetricSignature("hz", "ss", "loop")


@pytest.mark.parametrize("unit", ["dB", "Hz", "volt", "", "rad"])
def test_bad_unit_value_error(unit):
    with pytest.raises(ValueError):
        MetricSignature(unit, "ss")


@pytest.mark.parametrize("domain", ["ac", "SS", "", "time"])
def test_bad_domain_value_error(domain):
    with pytest.raises(ValueError):
        MetricSignature("db", domain)
