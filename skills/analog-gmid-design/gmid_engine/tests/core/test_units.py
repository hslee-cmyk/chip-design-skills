"""metrics CONTRACT 0절 core 추가: units 상수 표 -- METRIC_UNITS 는 레지스트리 단위를 모두 담고, DOMAINS 는 dc·ss 를 담으며,
AMPLITUDE_DB_PER_DECADE 는 진폭 dB 계수 20(20·log10)."""
import math

from gmid_engine.core import AMPLITUDE_DB_PER_DECADE, DOMAINS, METRIC_UNITS


def test_metric_units_cover_registry_units():
    # metrics CONTRACT 3.15 표의 단위
    assert {"db", "hz", "deg", "ohm", "amp", "w", "m2"} <= set(METRIC_UNITS)
    assert len(set(METRIC_UNITS)) == len(METRIC_UNITS)


def test_domains_cover_dc_ss():
    assert {"dc", "ss"} <= set(DOMAINS)
    assert len(set(DOMAINS)) == len(DOMAINS)


def test_amplitude_db_per_decade():
    assert AMPLITUDE_DB_PER_DECADE == 20.0
    # 진폭비 10 = 20 dB
    assert AMPLITUDE_DB_PER_DECADE * math.log10(10.0) == 20.0
