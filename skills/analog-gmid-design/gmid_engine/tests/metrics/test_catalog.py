"""CONTRACT 3.15: metric_catalog() = {이름: MetricSignature} 읽기 전용 -- 레지스트리 서명과 같다."""
import collections.abc

import pytest

from gmid_engine.core import MetricSignature
from gmid_engine.metrics import metric_catalog

EXPECTED = {
    "gain_ss_db": MetricSignature("db", "ss", "transfer", None),
    "ugf_ss_hz": MetricSignature("hz", "ss", "transfer", None),
    "gbw_ss_hz": MetricSignature("hz", "ss", "transfer", None),
    "parasitic_pm_ss_deg": MetricSignature("deg", "ss", "transfer", None),
    "pm_ss_deg": MetricSignature("deg", "ss", "loop", None),
    # [CM 2026-10-08] 3.15 표 행 + S-20(공통 모드 CMFB 루프 PM, 계약 7.11)
    "pm_cm_ss_deg": MetricSignature("deg", "ss", "cm_loop", None),
    "ratio_ss_db": MetricSignature("db", "ss", "ratio", None),
    "rout_ss_ohm": MetricSignature("ohm", "ss", "output_port", None),
    "supply_current_dc": MetricSignature("amp", "dc", None, "power"),
    "power_dc_w": MetricSignature("w", "dc", None, None),
    "area_search_m2": MetricSignature("m2", "geom", None, None),  # 3.15 영역 geom
}


def test_catalog_contents():
    cat = metric_catalog()
    assert isinstance(cat, collections.abc.Mapping)
    assert dict(cat) == EXPECTED


def test_catalog_read_only():
    cat = metric_catalog()
    with pytest.raises(TypeError):
        cat["new_metric"] = MetricSignature("db", "ss")
    with pytest.raises(TypeError):
        cat["gain_ss_db"] = MetricSignature("hz", "ss")
    assert metric_catalog()["gain_ss_db"] == EXPECTED["gain_ss_db"]
