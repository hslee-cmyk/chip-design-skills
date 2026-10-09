"""CONTRACT 3.15: metric_registry -- 등록 11개([CM 2026-10-08] pm_cm_ss_deg 추가, S-20)(metric -> 결과 형식.필드, 단위, 영역, view_kind, objective_axis)."""
import pytest

from gmid_engine.core import MetricSignature
from gmid_engine.metrics import (
    AreaSearch,
    LoopAnalysis,
    NoiseAnalysis,
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
    # [CM 2026-10-08] 3.15 표 행 + S-20: 필드 LoopAnalysis.phase_margin_deg, deg, ss, cm_loop, axis None
    "pm_cm_ss_deg": (LoopAnalysis, "phase_margin_deg", "deg", "ss", "cm_loop", None),
    "ratio_ss_db": (ResponseRatio, "ratio_db", "db", "ss", "ratio", None),
    "rout_ss_ohm": (OutputResistance, "rout_ohm", "ohm", "ss", "output_port", None),
    "supply_current_dc": (SupplyCurrents, "supply_current_dc", "amp", "dc", None, "power"),
    "power_dc_w": (SupplyCurrents, "power_dc_w", "w", "dc", None, None),
    "area_search_m2": (AreaSearch, "area_search_m2", "m2", "geom", None, None),  # 3.15 영역 geom
    # [U8 2026-10-09] 계약 10절 '레지스트리 11개 -> 15개' + 41 §7.1 표(단위)·공통 규칙(ss, transfer, 목적 축 없음), 결과 형식 NoiseAnalysis
    "noise_th_in_v2hz": (NoiseAnalysis, "th_in_v2hz", "v2_per_hz", "ss", "transfer", None),
    "noise_fc_in_hz": (NoiseAnalysis, "fc_in_hz", "hz", "ss", "transfer", None),
    "noise_excess_th": (NoiseAnalysis, "excess_th", "ratio", "ss", "transfer", None),
    "noise_out_int_vrms": (NoiseAnalysis, "out_int_vrms", "v", "ss", "transfer", None),
}


def test_names_exactly_contract_table():
    # oracle (d): 계약 3.15 "등록 11개" 문장과 표(S-20) + 계약 10절 "레지스트리 11개 -> 15개"(잡음 4개) -- 개수는 이름에 넣지 않는다
    assert set(metric_registry()) == set(TABLE)
    assert len(metric_registry()) == 15


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
