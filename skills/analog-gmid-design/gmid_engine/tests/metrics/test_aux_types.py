"""`aux_types` -- 계약 10.0·10.1: U7 결과·구조 입력 레코드는 frozen dataclass, 값은 tuple·float·str(graph 필드 값 = 불변·지문 가능),
`MismatchSource` 의 지문 `__canonical__` = (sha256, kind 목록)(모델 본문을 직렬화하지 않는다), `from_decl(pdk_decl)`.

oracle (a) 구성: 레코드를 손으로 만들어 동등·해시·불변을 본다.
"""
from __future__ import annotations

import dataclasses
import types

import pytest

from gmid_engine.metrics import (BlockGain, BlockResidual, BlockStruct, CoupledResidual, FfContribution, FfRatio, FfStruct, GateResult,
                                 LsFields, LsNode, MetricStructure, MirrorRatio, MismatchSource, NqsRatio, OffsetAnalysis,
                                 OffsetContribution, OffsetSystematic, SatDevice, SwingIcmr, ViewStruct)

ALL = (BlockGain, BlockResidual, BlockStruct, CoupledResidual, FfContribution, FfRatio, FfStruct, GateResult, LsFields, LsNode,
       MetricStructure, MirrorRatio, MismatchSource, NqsRatio, OffsetAnalysis, OffsetContribution, OffsetSystematic, SatDevice,
       SwingIcmr, ViewStruct)


@pytest.mark.parametrize("cls", ALL, ids=lambda c: c.__name__)
def test_frozen_dataclass(cls):
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen


def test_records_hashable_and_immutable():
    b = BlockStruct(("out",), "gain", 1, ("in",), ("out",), ("in", "out"), ("M1",))
    v = ViewStruct("t", (("in", 1.0),), ("out",), (b,))
    ms = MetricStructure((v,))
    assert hash(ms) == hash(MetricStructure((ViewStruct("t", (("in", 1.0),), ("out",), (b,)),)))
    with pytest.raises(dataclasses.FrozenInstanceError):
        b.stage = 2


def test_defaults_are_empty_or_none():
    assert OffsetAnalysis(None, None, None).undefined == () and OffsetAnalysis(None, None, None).contrib == ()
    s = SwingIcmr(None, None, None)
    assert (s.out_ranges, s.window, s.bounds, s.input_dc, s.required_input_cm_v) == ((), (), (), "", None)
    assert SatDevice("M", 1, "d", "g", "s", 0.5, 0.2).linear is False


def test_mismatch_source_canonical_and_from_decl():
    models = (("nmos", object()), ("pmos", object()))
    src = MismatchSource(models, "ab" * 32)
    assert src.__canonical__() == ("ab" * 32, ("nmos", "pmos"))
    decl = types.SimpleNamespace(mismatch_models=list(models), decl_sha256="cd" * 32)
    got = MismatchSource.from_decl(decl)
    assert got.models == models and got.sha256 == "cd" * 32
