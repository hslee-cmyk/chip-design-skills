"""`icm_window_metrics` -- card IT-2d T-IW: 세 metric(`icm_margin_v`·`icmr_v`·`required_input_cm_v`)은 `graph.icm_config`의 V_cm 칸에서
낸다. 입력 포트 창 `lo`·`hi`는 보고 열 전용이라 산술에 쓰지 않는다. 순수 함수.

oracle: (식) interface 'IT-2d 세 metric 정의(손 판정 기준)' 문장 -- margin = min(vcm0 − vcm_lo, vcm_hi − vcm0), icmr = vcm_hi − vcm_lo,
required = pending 이면 (vcm0, vcm_lo, vcm_hi) 아니면 None, 분해능 = 첫 포트 tol_v / 2·tol_v. 기대값은 아래 손 산수로 적었고 피검 함수로
만들지 않는다. 정의 불능 code·category 는 interface 문장 그대로(oracle (d)).
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.metrics import Undefined
from gmid_engine.metrics.aux_types import IcmConfig, IcmPort, IcmWindow
from gmid_engine.metrics.icm_window import icm_window_metrics

THREE = {"icm_margin_v", "icmr_v", "required_input_cm_v"}


def cfg(vcm0=0.90, lo=0.34, hi=1.19, config="as_is_single_input", undefined=()):
    return IcmConfig(config, None, None, vcm0, lo, hi, undefined)


def port(net="in", v=0.9, lo=0.0, hi=1.8, tol=0.01, missing=()):
    return IcmPort(net, v, lo, hi, tol, missing)


def test_it2d_icm_window_interface_fields_exact():
    """interface: IcmPort(net, v, lo, hi, tol_v, missing), IcmWindow 아홉 칸(model_error_ref·sources·criterion·config 칸 없음), 둘 다 frozen."""
    assert [f.name for f in dataclasses.fields(IcmPort)] == ["net", "v", "lo", "hi", "tol_v", "missing"]
    names = [f.name for f in dataclasses.fields(IcmWindow)]
    assert names == ["icmr_v", "icm_margin_v", "required_input_cm_v", "window", "v_icm", "input_dc", "icmr_resolution",
                     "margin_resolution", "undefined"]
    assert IcmPort.__dataclass_params__.frozen and IcmWindow.__dataclass_params__.frozen


def test_it2d_icm_window_hand_example_pending():
    """interface 예: vcm0 0.90, vcm_lo 0.34, vcm_hi 1.19 -> margin = min(0.90 − 0.34, 1.19 − 0.90) = min(0.56, 0.29) = 0.29,
    icmr = 1.19 − 0.34 = 0.85, input_dc pending 이면 required = (0.90, 0.34, 1.19). window = (0.34, 1.19), v_icm = 0.90.
    분해능: margin = 첫 포트 tol 0.01, icmr = 2·0.01 = 0.02."""
    got = icm_window_metrics(cfg(), (port(tol=0.01),), "pending")
    assert isinstance(got, IcmWindow) and got.undefined == ()
    assert got.icm_margin_v == pytest.approx(0.29, abs=1e-12)
    assert got.icmr_v == pytest.approx(0.85, abs=1e-12)
    assert got.required_input_cm_v == (0.90, 0.34, 1.19)
    assert got.window == (0.34, 1.19) and got.v_icm == 0.90 and got.input_dc == "pending"
    assert got.margin_resolution == pytest.approx(0.01, abs=1e-15)
    assert got.icmr_resolution == pytest.approx(0.02, abs=1e-15)


def test_it2d_icm_window_declared_has_no_required():
    """입력 DC 선언이면 required_input_cm_v None, 나머지 값은 같다."""
    got = icm_window_metrics(cfg(), (port(),), "declared")
    assert got.required_input_cm_v is None and got.input_dc == "declared"
    assert got.icm_margin_v == pytest.approx(0.29, abs=1e-12)
    assert got.icmr_v == pytest.approx(0.85, abs=1e-12)


def test_it2d_icm_window_margin_negative_when_outside_window():
    """V_cm 이 창 밖이면 margin 음수 그대로: vcm0 1.30, 창 [0.34, 1.19] -> min(1.30 − 0.34, 1.19 − 1.30) = −0.11. icmr 는 0.85 그대로."""
    got = icm_window_metrics(cfg(vcm0=1.30), (port(),), "declared")
    assert got.icm_margin_v == pytest.approx(-0.11, abs=1e-12)
    assert got.icmr_v == pytest.approx(0.85, abs=1e-12)


def test_it2d_icm_window_resolution_from_first_port_and_none():
    """margin_resolution = 첫 포트 tol_v(둘째 포트 값 아님), icmr_resolution = 2·tol_v. tol_v None 이면 둘 다 None."""
    two = (port("a", tol=0.01), port("b", tol=0.05))
    got = icm_window_metrics(cfg(), two, "declared")
    assert got.margin_resolution == pytest.approx(0.01, abs=1e-15)
    assert got.icmr_resolution == pytest.approx(0.02, abs=1e-15)
    none = icm_window_metrics(cfg(), (port(tol=None),), "declared")
    assert none.margin_resolution is None and none.icmr_resolution is None
    assert none.icm_margin_v == pytest.approx(0.29, abs=1e-12)                    # 값은 tol 과 무관


@pytest.mark.parametrize("lo, hi", [(0.0, 1.8), (0.5, 0.6), (1.7, 0.2), (-5.0, 9.0)])
def test_it2d_icm_window_ignores_port_lo_hi(lo, hi):
    """포트 `lo`·`hi`는 보고 열 전용: 어떤 값(역전된 창, 레일 밖 포함)이어도 세 metric 은 V_cm 칸에서 정한 위 값 그대로.
    (음수 감도 포트의 정렬 뒤 열이 달라져도 값이 변하지 않는다는 불변식.)"""
    got = icm_window_metrics(cfg(), (port("a", lo=lo, hi=hi), port("b", lo=hi, hi=lo)), "pending")
    assert got.icm_margin_v == pytest.approx(0.29, abs=1e-12)
    assert got.icmr_v == pytest.approx(0.85, abs=1e-12)
    assert got.required_input_cm_v == (0.90, 0.34, 1.19)


def test_it2d_icm_window_unmeasured_port_is_numeric_undefined():
    """어느 포트든 missing 이 있으면: 세 metric 값 None, metric 이름마다 Undefined 한 원소, code input_window_unmeasured,
    category numeric, detail 에 ("port", net)."""
    got = icm_window_metrics(cfg(), (port("a"), port("bz", missing=("window",))), "pending")
    assert (got.icmr_v, got.icm_margin_v, got.required_input_cm_v) == (None, None, None)
    assert len(got.undefined) == 3 and {u.quantity for u in got.undefined} == THREE
    for u in got.undefined:
        assert isinstance(u, Undefined)
        assert (u.code, u.category) == ("input_window_unmeasured", "numeric")
        assert ("port", "bz") in u.detail


def test_it2d_icm_window_config_none_copies_config_code():
    """구성 None: icm_config.undefined 의 code 를 그대로 옮긴다(category definitional), 세 metric 값 None, metric 이름마다 하나."""
    src = Undefined("icm_config", "icm_inputs_unsupported", "definitional", (("inputs", ("a", "b", "c")),))
    got = icm_window_metrics(IcmConfig(None, None, None, None, None, None, (src,)), (port(),), "pending")
    assert (got.icmr_v, got.icm_margin_v, got.required_input_cm_v) == (None, None, None)
    assert len(got.undefined) == 3 and {u.quantity for u in got.undefined} == THREE
    assert {(u.code, u.category) for u in got.undefined} == {("icm_inputs_unsupported", "definitional")}


def test_it2d_icm_window_pure_and_deterministic():
    """순수 함수: 같은 입력 -> 같은 결과(동등), 입력 레코드는 frozen 이라 바뀌지 않는다."""
    c, ps = cfg(), (port(),)
    assert icm_window_metrics(c, ps, "pending") == icm_window_metrics(c, ps, "pending")
    assert c == cfg() and ps == (port(),)
