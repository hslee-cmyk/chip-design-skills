"""[U8 2026-10-09] `metrics/noise_types` -- 잡음 값 형식 dataclass (metrics CONTRACT 10절 머리·10.0 표).

oracle (d) 계약 문장: NoiseAnalysis 필드 `th_in_v2hz`·`fc_in_hz`·`excess_th`·`out_int_vrms`(요청한 하나만 채움) + `undefined`·`resolution`·`contrib`·`detail`,
NoiseDecl 기본 = 되먹임 결정 대기(None)·샘플링 커패시터 없음·입력 셀 없음, 지문 가능한 불변 입력(frozen·hash 가능).
"""
import dataclasses

import pytest

from gmid_engine.metrics import (
    NoiseAnalysis,
    NoiseDecl,
    NoiseDevice,
    NoiseInput,
    NoisePlan,
    NoiseSetup,
    NoiseSources,
    NoiseTransfer,
)


def _fields(cls):
    return [f.name for f in dataclasses.fields(cls)]


def test_noise_analysis_fields_and_defaults():
    assert _fields(NoiseAnalysis) == ["th_in_v2hz", "fc_in_hz", "excess_th", "out_int_vrms", "undefined", "resolution",
                                      "contrib", "detail"]
    a = NoiseAnalysis()
    assert (a.th_in_v2hz, a.fc_in_hz, a.excess_th, a.out_int_vrms, a.resolution) == (None,) * 5
    assert a.undefined == () and a.contrib == () and a.detail == ()


def test_noise_decl_defaults_and_hashable():
    d = NoiseDecl()
    assert d.feedback is None and d.sampling_caps == () and d.input_cells == ()
    same = NoiseDecl(feedback=("Cf",), sampling_caps=("Cs",), input_cells=((("in",), ("out",), ("M1",)),))
    assert hash(same) == hash(NoiseDecl(feedback=("Cf",), sampling_caps=("Cs",), input_cells=((("in",), ("out",), ("M1",)),)))
    with pytest.raises(dataclasses.FrozenInstanceError):
        same.feedback = ()


@pytest.mark.parametrize("cls", [NoiseDecl, NoiseDevice, NoiseInput, NoiseSources, NoisePlan, NoiseTransfer, NoiseSetup,
                                 NoiseAnalysis])
def test_all_frozen(cls):
    assert cls.__dataclass_params__.frozen


def test_noise_device_unknown_b_is_none():
    d = NoiseDevice("M1", a=1e-12, b=None, ef=0.84, b_status="no_feedthrough_free_point")
    assert d.b is None and d.failure is None and d.tol_flicker is None and d.tol_thermal is None


def test_noise_input_fields():
    assert _fields(NoiseInput) == ["decl", "devices", "f_lo", "kt"]
