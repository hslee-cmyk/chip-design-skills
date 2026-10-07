"""CONTRACT 3.15: metric_registry -- 등록 10개(metric -> 결과 형식.필드, 단위, 영역, view_kind, objective_axis)."""
import pytest

from gmid_engine.core import MetricSignature
from gmid_engine.metrics import (
    AreaSearch,
    LoopAnalysis,
    OutputResistance,
    RegisteredMetric,
    ResponseRatio,
    SupplyCurrents,
    metric_registry,
)

# 계약 표 그대로
TABLE = {
    "gain_ss_db": (LoopAnalysis, "gain_db", "db", "ss", "transfer", None),
    "ugf_ss_hz": (LoopAnalysis, "ugf_hz", "hz", "ss", "transfer", None),
    "gbw_ss_hz": (LoopAnalysis, "gbw_hz", "hz", "ss", "transfer", None),
    "parasitic_pm_ss_deg": (LoopAnalysis, "phase_margin_deg", "deg", "ss", "transfer", None),
    "pm_ss_deg": (LoopAnalysis, "phase_margin_deg", "deg", "ss", "loop", None),
    "ratio_ss_db": (ResponseRatio, "ratio_db", "db", "ss", "ratio", None),
    "rout_ss_ohm": (OutputResistance, "rout_ohm", "ohm", "ss", "output_port", None),
    "supply_current_dc": (SupplyCurrents, "supply_current_dc", "amp", "dc", None, "power"),
    "power_dc_w": (SupplyCurrents, "power_dc_w", "w", "dc", None, None),
    "area_search_m2": (AreaSearch, "area_search_m2", "m2", "dc", None, None),
}


def test_exactly_ten_names():
    assert set(metric_registry()) == set(TABLE)
    assert len(metric_registry()) == 10


@pytest.mark.parametrize("name", sorted(TABLE))
def test_entry(name):
    src, field, unit, domain, view, axis = TABLE[name]
    e = metric_registry()[name]
    assert isinstance(e, RegisteredMetric)
    assert e.source_type is src
    assert e.field == field
    assert isinstance(e.signature, MetricSignature)
    assert (e.signature.unit, e.signature.domain, e.signature.view_kind, e.signature.objective_axis) == \
        (unit, domain, view, axis)


def test_unknown_name_key_error():
    with pytest.raises(KeyError):
        metric_registry()["gain_db"]
