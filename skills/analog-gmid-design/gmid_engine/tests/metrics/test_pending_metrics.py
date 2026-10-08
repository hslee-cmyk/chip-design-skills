"""[U5 2026-10-08] 계산 대기 metric 서명(`metrics/pending_metrics.py`) -- 설계 40 §3.8-8(offset·미러비·스윙·ICMR 7개, 닫힌 어휘),
41 §7.1(잡음 4개, `domain: ss`·`view_kind: transfer`, 레지스트리 밖 잡음 이름은 `metric_unknown`), metrics CONTRACT 3.15.

oracle:
* (d) 설계 문장의 이름 11개와 단위·영역(tests/authoring conftest `u5_design_signatures` -- 그 docstring 에 표 출처).
* (d) 계약 3.15 문장: 카탈로그 = 레지스트리 11 + 계산 대기 11 = 22, 레지스트리는 11 그대로(계산 대기 이름은 `metric_value` KeyError),
  둘이 겹치면 ValueError.
* (a) 집합 관계(서로소·합집합)는 이 test 가 직접 계산한다.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import METRIC_UNITS, MetricSignature
from gmid_engine.metrics import metric_catalog, metric_registry

from authoring.conftest import u5_design_signatures

PENDING = u5_design_signatures()
DESIGN_Q34 = ("offset_in_sigma_mv", "offset_excess", "offset_sys_mv", "mirror_ratio_sigma_pct", "swing_out_v", "icmr_v",
              "icm_margin_v")                                    # 40 §3.8-8 표 행 순서
DESIGN_NOISE = ("noise_th_in_v2hz", "noise_fc_in_hz", "noise_excess_th", "noise_out_int_vrms")   # 41 §7.1 표 행 순서
REGISTRY_COUNT = 11                                               # metrics CONTRACT 3.15 / S-20


def test_design_names_are_exactly_the_pending_set():
    assert set(PENDING) == set(DESIGN_Q34) | set(DESIGN_NOISE)
    assert len(PENDING) == 11


def test_registry_unchanged_and_disjoint_from_pending():
    reg = metric_registry()
    assert len(reg) == REGISTRY_COUNT
    assert not set(reg) & set(PENDING)


def test_catalog_is_disjoint_union():
    cat = metric_catalog()
    reg = metric_registry()
    assert set(cat) == set(reg) | set(PENDING)
    assert len(cat) == len(reg) + len(PENDING)


@pytest.mark.parametrize("name", sorted(DESIGN_Q34 + DESIGN_NOISE))
def test_pending_signature_units_in_vocabulary(name):
    sig = metric_catalog()[name]
    assert isinstance(sig, MetricSignature)
    assert sig.unit in METRIC_UNITS
    assert sig.unit == PENDING[name].unit
    assert sig.domain == PENDING[name].domain
    assert sig.objective_axis is None                    # 설계: 판정·보고 metric, 목적 축 아님


@pytest.mark.parametrize("name", DESIGN_NOISE)
def test_noise_signatures_ss_transfer(name):
    """41 §7.1 공통 규칙: MOD5 레지스트리 서명 `domain: ss`, `view_kind: transfer`."""
    sig = metric_catalog()[name]
    assert (sig.domain, sig.view_kind) == ("ss", "transfer")


@pytest.mark.parametrize("name", ["swing_out_v", "icmr_v", "icm_margin_v"])
def test_large_signal_metrics_have_no_view(name):
    """40 §3.8-8 표: 스윙·ICMR 은 'ls'(뷰 없음) -- 뷰 칸이 없다."""
    sig = metric_catalog()[name]
    assert (sig.unit, sig.domain, sig.view_kind) == ("v", "ls", None)


@pytest.mark.parametrize("name", ["offset_in_sigma_mv", "offset_excess", "offset_sys_mv"])
def test_offset_metrics_transfer_view(name):
    """40 §3.8-8 표: offset 3개는 'ss / transfer'(gain 제약 전달 뷰) -- offset_sys_mv 의 'dc→ss' 는 최종 영역 ss 로 읽는다."""
    sig = metric_catalog()[name]
    assert (sig.domain, sig.view_kind) == ("ss", "transfer")


@pytest.mark.parametrize("name", sorted(DESIGN_Q34 + DESIGN_NOISE))
def test_pending_name_has_no_registry_value(name):
    """계산 대기 = 레지스트리에 결과 형식·필드가 없다(계약 3.15: metric_value 는 KeyError)."""
    from gmid_engine.metrics import metric_value
    with pytest.raises(KeyError):
        metric_value(name, object())


@pytest.mark.parametrize("name", ["noise_in_density_ss_v_rthz", "noise_in_integrated_ss_v", "noise_v_rthz",
                                  "mismatch_sigma_mv", "mirror_ratio_error_mv", "mismatch_sigma_v"])
def test_names_outside_closed_vocabulary_absent(name):
    """41 §7.1 '레지스트리 밖 잡음 이름은 metric_unknown' -- 40 §3.1 표의 옛 잡음 행 이름·옛 topology 이름과 옛 정합 이름은
    카탈로그에 없다(로더가 metric_unknown·legacy_name 으로 거부하는 근거)."""
    assert name not in metric_catalog()
    assert name not in metric_registry()


def test_catalog_read_only_includes_pending():
    cat = metric_catalog()
    with pytest.raises(TypeError):
        cat["offset_excess"] = MetricSignature("db", "ss")
    assert metric_catalog()["offset_excess"].unit == "ratio"
