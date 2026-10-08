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
REGISTRY_NAMES = frozenset(EXPECTED)          # 위 11개 = 레지스트리(3.15 표)

# [U5 2026-10-08] 카탈로그 = 레지스트리 + 계산 대기 서명(설계 40 §3.8-8·41 §7.1 어휘). 기대 서명은 설계 문장에서 -- tests/authoring
# conftest `u5_design_signatures` 한 곳(oracle (d), 근거는 그 docstring). [2026-10-09] 설계 표가 mirror_ratio_sigma_pct view_kind 를
# '없음'으로 정정(master cc91068, 이의 D1)해 전 서명을 비교한다. [U5 후속] ff_gm_ratio 추가로 계산 대기 12 -> 카탈로그 23(metrics CONTRACT 3.15).
from authoring.conftest import u5_design_signatures  # noqa: E402

PENDING_EXPECTED = u5_design_signatures()
VIEW_KIND_UNASSERTED: set = set()


def _sig_key(name, sig):
    if name in VIEW_KIND_UNASSERTED:
        return (sig.unit, sig.domain, sig.objective_axis)
    return (sig.unit, sig.domain, sig.view_kind, sig.objective_axis)


def test_catalog_contents():
    cat = metric_catalog()
    assert isinstance(cat, collections.abc.Mapping)
    assert set(cat) == set(EXPECTED) | set(PENDING_EXPECTED)
    assert len(cat) == len(EXPECTED) + len(PENDING_EXPECTED) == 23
    for name, sig in EXPECTED.items():
        assert cat[name] == sig, name
    for name, sig in PENDING_EXPECTED.items():
        assert isinstance(cat[name], MetricSignature)
        assert _sig_key(name, cat[name]) == _sig_key(name, sig), name


def test_mirror_ratio_sigma_pct_unit_domain():
    """설계 40 §3.8-8: 단위 pct, 'dc→ss' -- 판정·보고 metric 이지 목적 축이 아니다."""
    s = metric_catalog()["mirror_ratio_sigma_pct"]
    assert (s.unit, s.domain, s.objective_axis) == ("pct", "ss", None)


def test_catalog_read_only():
    cat = metric_catalog()
    with pytest.raises(TypeError):
        cat["new_metric"] = MetricSignature("db", "ss")
    with pytest.raises(TypeError):
        cat["gain_ss_db"] = MetricSignature("hz", "ss")
    assert metric_catalog()["gain_ss_db"] == EXPECTED["gain_ss_db"]
