"""CONTRACT 3.15: metric_registry -- 등록 11개([CM 2026-10-08] pm_cm_ss_deg 추가, S-20)(metric -> 결과 형식.필드, 단위, 영역, view_kind, objective_axis).
[U7 2026-10-09] + 계산 대기 표에서 옮긴 8행(CONTRACT 10.0 '레지스트리(`registry._ROWS`)에 옮긴 8행(서명은 `pending_metrics` 와 같다)'과
설계 40 §3.8-8 표(단위·domain/view_kind)) = 19개. 결과 형식·필드는 CONTRACT 10.0 문장 그대로 옮겨 적었다(oracle (d))."""
import pytest

from gmid_engine.core import MetricSignature
from gmid_engine.metrics import (
    AreaSearch,
    FfRatio,
    LoopAnalysis,
    MirrorRatio,
    OffsetAnalysis,
    OffsetSystematic,
    OutputResistance,
    RegisteredMetric,
    ResponseRatio,
    SupplyCurrents,
    SwingIcmr,
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
    # [U7] CONTRACT 10.0 옮긴 8행: 결과 형식.필드 = 10.0 문장, (단위, 영역, 뷰) = 설계 40 §3.8-8 표(mirror 뷰 없음 = cc91068 정정,
    # 스윙·ICMR 'ls', offset_sys 'dc→ss' 는 최종 영역 ss)
    "offset_in_sigma_mv": (OffsetAnalysis, "sigma_in_mv", "mv", "ss", "transfer", None),
    "offset_excess": (OffsetAnalysis, "excess", "ratio", "ss", "transfer", None),
    "offset_sys_mv": (OffsetSystematic, "sys_mv", "mv", "ss", "transfer", None),
    "mirror_ratio_sigma_pct": (MirrorRatio, "sigma_pct", "pct", "ss", None, None),
    "swing_out_v": (SwingIcmr, "swing_out_v", "v", "ls", None, None),
    "icmr_v": (SwingIcmr, "icmr_v", "v", "ls", None, None),
    "icm_margin_v": (SwingIcmr, "icm_margin_v", "v", "ls", None, None),
    "ff_gm_ratio": (FfRatio, "ratio", "ratio", "ss", "transfer", None),
}


def test_names_exactly_contract_table():
    # oracle (d): 계약 3.15 "등록 11개" 문장과 표(S-20) + [U7] CONTRACT 10.0 '옮긴 8행' -- 개수는 이름에 넣지 않는다
    assert set(metric_registry()) == set(TABLE)
    assert len(metric_registry()) == 11 + 8


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
