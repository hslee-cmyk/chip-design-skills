"""[U5 2026-10-08] 계산 대기 metric 서명(`metrics/pending_metrics.py`) -- 설계 40 §3.8-8(offset·미러비·스윙·ICMR 7개, 닫힌 어휘),
41 §7.1(잡음 4개, `domain: ss`·`view_kind: transfer`, 레지스트리 밖 잡음 이름은 `metric_unknown`), metrics CONTRACT 3.15.

oracle:
* (d) 설계 문장의 이름 12개와 단위·영역(tests/authoring conftest `u5_design_signatures` -- 그 docstring 에 표 출처).
  [U5 후속 2026-10-09] `ff_gm_ratio`(40 §3.8-8 표 행, §11 'J 추가 범위' U5 행 '어휘', 값은 U7 행) 추가.
* (d) 계약 3.15 문장: 카탈로그 = 레지스트리 11 + 계산 대기 12 = 23, 레지스트리는 11 그대로(계산 대기 이름은 `metric_value` KeyError),
  둘이 겹치면 ValueError. [U8 2026-10-09] 계약 10절: 잡음 4개가 레지스트리로 이동 -- 레지스트리 15 + 계산 대기 8 = 23.
* (a) 집합 관계(서로소·합집합)는 이 test 가 직접 계산한다.
* [U7 2026-10-09] (d) metrics CONTRACT 10.0: 계산 대기 8행(offset 3·mirror·스윙 3·ff_gm_ratio)을 서명 그대로 레지스트리로 옮겼다 --
  `PENDING_METRIC_ROWS` 에는 잡음 4행만 남는다(U8). 카탈로그(23 = 설계 이름 12 + 레지스트리 원래 11)는 그대로이고, 나뉨이
  레지스트리 19 + 계산 대기 4 로 바뀐다. 서명 test(단위·영역·뷰)는 카탈로그에 대해 그대로 둔다(옮겨도 서명 동일).
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
DESIGN_FF = ("ff_gm_ratio",)                                      # 40 §3.8-8 표 마지막 행 + §11 J 추가 범위 U5 행
BASE_COUNT = 11                                                  # metrics CONTRACT 3.15 / S-20 (U7·U8 이전 레지스트리)
MOVED_U7 = DESIGN_Q34 + DESIGN_FF                                 # [U7] CONTRACT 10.0 '레지스트리에 옮긴 8행'
REGISTRY_COUNT = BASE_COUNT + len(MOVED_U7) + len(DESIGN_NOISE)   # [U7+U8 통합] 11 + 8 + 4 = 23
STILL_PENDING = ()                                                # [U7+U8 통합] 계산 대기 이름 없음(잡음 4 = U8, 나머지 8 = U7 이 모두 레지스트리로 이동)
PENDING_COUNT = len(STILL_PENDING)


def test_design_names_are_exactly_the_pending_set():
    assert set(PENDING) == set(DESIGN_Q34) | set(DESIGN_NOISE) | set(DESIGN_FF)
    assert len(PENDING) == 12


def test_registry_holds_moved_rows_and_disjoint_from_still_pending():
    """[U7] 레지스트리 = 원래 11 + 옮긴 8, 남은 계산 대기(잡음 4)와 서로소."""
    reg = metric_registry()
    assert len(reg) == REGISTRY_COUNT
    assert len(STILL_PENDING) == PENDING_COUNT
    assert not set(reg) & set(STILL_PENDING)
    assert set(MOVED_U7) <= set(reg)
    assert set(DESIGN_NOISE) <= set(reg)                 # 계약 10절: 잡음 4개는 레지스트리에 있다


def test_catalog_is_disjoint_union():
    cat = metric_catalog()
    reg = metric_registry()
    assert set(cat) == set(reg) | set(PENDING)           # 설계 이름 12개(잡음 포함)는 모두 카탈로그에 있다
    assert not set(reg) & set(STILL_PENDING)
    assert len(cat) == len(reg) + len(STILL_PENDING) == REGISTRY_COUNT + PENDING_COUNT == 23


@pytest.mark.parametrize("name", sorted(DESIGN_Q34 + DESIGN_NOISE + DESIGN_FF))
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


def test_empty_pending_table_catalog_equals_registry():
    """[U7+U8 통합 2026-10-09] 옛 `test_pending_name_has_no_registry_value`(계산 대기 이름마다 metric_value KeyError)를 대체한다 --
    계산 대기 이름이 하나도 없어 parametrize 가 비어 늘 skip 되던 헐거운 test 였다. 현재 계약(metrics CONTRACT 10.0·11절,
    3.15 '카탈로그 = 레지스트리 + 계산 대기'): 계산 대기 표가 빈 표이면 카탈로그 = 레지스트리(이름 집합과 서명이 같다).
    oracle (d) 계약 문장 + (a) 집합 비교는 이 test 가 직접 한다."""
    cat = metric_catalog()
    reg = metric_registry()
    assert set(cat) == set(reg)
    assert len(cat) == REGISTRY_COUNT == 23
    for name in reg:
        assert cat[name] == reg[name].signature, name


def test_name_outside_catalog_has_no_registry_value():
    """빈 계산 대기 표에서도 카탈로그 밖 이름은 metric_value 가 KeyError(계약 3.15 '레지스트리 밖 이름은 KeyError'). oracle (d).
    이름은 구성으로 정한 미지 이름(a) -- 카탈로그에 없음을 먼저 단정한다."""
    from gmid_engine.metrics import metric_value
    name = "noise_no_such_metric_v2hz"
    assert name not in metric_catalog()
    with pytest.raises(KeyError):
        metric_value(name, object())


NOISE_FIELD = {"noise_th_in_v2hz": "th_in_v2hz", "noise_fc_in_hz": "fc_in_hz", "noise_excess_th": "excess_th",
               "noise_out_int_vrms": "out_int_vrms"}                 # 계약 10절 'NoiseAnalysis 필드 ... metric_value 가 그대로 읽는다'


@pytest.mark.parametrize("name", DESIGN_NOISE)
def test_noise_name_reads_noise_analysis(name):
    """[U8] 잡음 metric 은 레지스트리 항목 -- 결과 형식 NoiseAnalysis 의 필드를 읽고, 다른 형식은 TypeError(배선 결함, evaluate 계약).
    oracle (a): 구성으로 정한 값 0.125 를 그 필드에만 넣으면 그 값이 읽힌다."""
    from gmid_engine.metrics import NoiseAnalysis, metric_value
    with pytest.raises(TypeError):
        metric_value(name, object())
    got = metric_value(name, NoiseAnalysis(**{NOISE_FIELD[name]: 0.125}))
    assert got.value == 0.125
    empty = metric_value(name, NoiseAnalysis())
    assert empty.value is None and empty.undefined


@pytest.mark.parametrize("name", sorted(MOVED_U7))
def test_moved_name_signature_unchanged_in_registry(name):
    """[U7] CONTRACT 10.0 '서명은 pending_metrics 와 같다': 레지스트리 서명 = 설계 표 서명(u5_design_signatures) 그대로."""
    sig = metric_registry()[name].signature
    want = PENDING[name]
    assert (sig.unit, sig.domain, sig.view_kind, sig.objective_axis) == (want.unit, want.domain, want.view_kind, want.objective_axis)


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


def test_ff_gm_ratio_signature():
    """[U5 후속] 40 §3.8-8 표 `ff_gm_ratio` 행: 단위 ratio, 'ss / transfer'(41 §1.12.2-5 r_ff = G_ff / gm_in), 보고·선언 시 제약
    -- 목적 축 아님. oracle (d) 설계 표."""
    sig = metric_catalog()["ff_gm_ratio"]
    assert (sig.unit, sig.domain, sig.view_kind, sig.objective_axis) == ("ratio", "ss", "transfer", None)
    assert "ff_gm_ratio" in metric_registry()            # [U7] 계산이 들어왔다(§11 J 추가 범위 U7 행, CONTRACT 10.0)


def test_mirror_ratio_sigma_pct_has_no_view():
    """[2026-10-09 master cc91068] 40 §3.8-8 표 정정: mirror_ratio_sigma_pct 'dc→ss / 없음'(뷰 불필요). oracle (d)."""
    sig = metric_catalog()["mirror_ratio_sigma_pct"]
    assert (sig.unit, sig.domain, sig.view_kind) == ("pct", "ss", None)
