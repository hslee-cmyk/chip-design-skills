"""의도 영역 `human.intended_region` (gate `intended_region`) -- SPEC_CONTRACT 2절 intended_region_device 행.
영역 어휘(`REGIONS`)는 계약에 값이 적혀 있지 않아 '어휘 밖 영역 -> type' 과 '소자 밖 -> intended_region_device 포함'만 판정한다."""
from __future__ import annotations

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}


def test_empty_is_explicit_declaration(sc):
    assert sc.load().intended_region == ()


def test_pending(sc):
    sc.human["intended_region"] = {"pending": "CI-18"}
    assert sc.load().intended_region.decision == "CI-18"


def test_device_outside_topology(sc):
    sc.human["intended_region"] = {"Qzz": {"region": "zz_not_a_region", "source": dict(US)}}
    d = sc.reject()
    assert "intended_region_device" in sc.rules(d)
    assert d["rejected_gates"] == ("intended_region",)


@pytest.mark.parametrize("name", ["Rfb", "Ibs"])
def test_element_is_not_a_device(sc, name):
    sc.human["intended_region"] = {name: {"region": "zz_not_a_region", "source": dict(US)}}
    d = sc.reject()
    assert "intended_region_device" in sc.rules(d)


def test_region_vocab(sc):
    sc.human["intended_region"] = {"Q1": {"region": "zz_not_a_region", "source": dict(US)}}
    sc.reject_only("type", "intended_region")


@pytest.mark.parametrize("raw", [[], "saturation", 3])
def test_section_type(sc, raw):
    sc.human["intended_region"] = raw
    d = sc.reject()
    assert "type" in sc.rules(d) and d["rejected_gates"] == ("intended_region",)
