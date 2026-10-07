"""core `MetricSignature(unit, domain, view_kind, objective_axis=None)` -- authoring SPEC_CONTRACT 4절."""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import METRIC_DOMAINS, OBJECTIVE_AXES, VIEW_KINDS, MetricSignature, fp_of, require_immutable


def test_vocabularies():
    assert set(METRIC_DOMAINS) == {"dc", "ss", "ls", "geom"}
    assert set(VIEW_KINDS) == {"none", "transfer", "ratio"}
    assert set(OBJECTIVE_AXES) == {"power", "area"}


@pytest.mark.parametrize("domain", ["dc", "ss", "ls", "geom"])
@pytest.mark.parametrize("view", ["none", "transfer", "ratio"])
@pytest.mark.parametrize("axis", [None, "power", "area"])
def test_valid(domain, view, axis):
    m = MetricSignature("dB", domain, view, axis)
    assert (m.unit, m.domain, m.view_kind, m.objective_axis) == ("dB", domain, view, axis)
    require_immutable(m)
    assert fp_of(m) == fp_of(MetricSignature("dB", domain, view, axis))


def test_default_axis_none():
    assert MetricSignature("Hz", "ss", "transfer").objective_axis is None


def test_frozen():
    m = MetricSignature("W", "dc", "none", "power")
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.unit = "mW"


@pytest.mark.parametrize("unit", ["", None, 3])
def test_bad_unit(unit):
    with pytest.raises(ValueError):
        MetricSignature(unit, "dc", "none")


@pytest.mark.parametrize("domain", ["DC", "ac", "", None])
def test_bad_domain(domain):
    with pytest.raises(ValueError):
        MetricSignature("V", domain, "none")


@pytest.mark.parametrize("view", ["port", "pending", "", None, "Transfer"])
def test_bad_view_kind(view):
    with pytest.raises(ValueError):
        MetricSignature("V", "dc", view)


@pytest.mark.parametrize("axis", ["energy", "", "Power"])
def test_bad_objective_axis(axis):
    with pytest.raises(ValueError):
        MetricSignature("W", "dc", "none", axis)


def test_equality_and_fp_by_content():
    a = MetricSignature("m2", "geom", "none", "area")
    b = MetricSignature("m2", "geom", "none", "area")
    c = MetricSignature("m2", "geom", "none", None)
    assert a == b and fp_of(a) == fp_of(b) and fp_of(a) != fp_of(c)
