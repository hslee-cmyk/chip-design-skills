"""`ss_types` (데이터 선언 모듈: SsDevice·SsCircuit·MetricRequest·MetricBundle·SsEvaluation) -- metrics CONTRACT 7.1
(+ 7.0 권한표: S2_WRITERS 에 ss·metric 필드 3개, sizing CONTRACT 2절 끝 표).
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import fp_of, require_immutable
from gmid_engine.metrics import (
    MetricBundle,
    MetricRequest,
    MetricResult,
    SmallSignalCircuit,
    SsCircuit,
    SsDevice,
    SsEvaluation,
    metrics_dc,
    metrics_ss,
    ss_dev,
)
from gmid_engine.sizing import (
    METRICS_DC_WRITER,
    METRICS_KEY,
    METRICS_SS_WRITER,
    S2_WRITERS,
    SS_DEV_WRITER,
    SS_WRITES,
)


def _fields(cls):
    return [f.name for f in dataclasses.fields(cls)]


def test_field_names_and_order():
    """7.1 생성자 순서 그대로([9절] 13번째 `lut_rel_tol`, 기본값 None)."""
    assert _fields(SsDevice) == ["gm", "gmb", "gds", "cgg", "cgs", "cgd", "cgb", "cdb", "csb", "cap_model", "gmb_model",
                                 "junction_model", "lut_rel_tol"]
    assert _dev().lut_rel_tol is None                       # 12칸 생성자 호출도 받는다(7.1)
    assert dataclasses.replace(_dev(), lut_rel_tol=0.02).lut_rel_tol == 0.02
    assert _fields(SsCircuit) == ["nodes", "circuit", "resistors", "capacitors", "ground_nets", "input_nets", "missing"]
    assert _fields(MetricRequest) == ["metric", "view"]
    # [CM 2026-10-08] 7.4 "결과 묶음에 reports·warnings 가 있다", S-26·S-27 (7.1 bea18e0: 필드 순서 entries, approximations, detail, reports, warnings)
    assert _fields(MetricBundle) == ["entries", "approximations", "detail", "reports", "warnings"]
    assert _fields(SsEvaluation) == ["snapshot", "ss", "dc", "lineage"]


def test_defaults():
    c = SsCircuit(("gnd",), SmallSignalCircuit((), (), (), ()), (), (), ("gnd",), ())
    assert c.missing == ()
    assert MetricRequest("power_dc_w").view is None
    b = MetricBundle(())
    assert b.approximations == () and b.detail == () and b.reports == () and b.warnings == ()
    assert SsEvaluation(None, None, None).lineage is None


def _dev():
    # 접합 표시 = 7.2 JUNCTION_LUT_RULE 값(옛 "pending_pdk_junction_params" 는 삭제됨), cdb·csb 는 PDK 접합 식 값 크기
    return SsDevice(1e-3, 2e-4, 1e-5, 1e-15, 6e-16, 2e-16, -2.03e-16, 1.6e-14, 2.3e-14, "lut_cgs_cgb", "lut_gmbs_column",
                    "pdk_bsim4_lut_rule_diffusion")


@pytest.mark.parametrize("make", [
    _dev,
    lambda: MetricRequest("gain_ss_db", None),
    lambda: MetricBundle(((MetricRequest("power_dc_w"), MetricResult("power_dc_w", 1e-6, ())),), (("cap", "x"),),
                         (("systems", 1),)),
], ids=["SsDevice", "MetricRequest", "MetricBundle"])
def test_frozen_and_immutable(make):
    """frozen -- 필드 값은 S2 스냅샷에 들어가므로 core 불변 값 규칙(require_immutable)·fp_of 를 통과해야 한다."""
    v = make()
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(v, _fields(type(v))[0], None)
    require_immutable(v)
    assert fp_of(v) == fp_of(make())


def test_fp_follows_values():
    a = _dev()
    b = dataclasses.replace(a, cgb=2.03e-16)          # 부호만 다름
    assert fp_of(a) != fp_of(b)
    assert fp_of(a) != fp_of(dataclasses.replace(a, csb=2.4e-14))          # 접합 용량도 지문에 든다


def test_junction_model_constant():
    """7.2: SsDevice.junction_model 값 상수 JUNCTION_LUT_RULE = "pdk_bsim4_lut_rule_diffusion"."""
    from gmid_engine.metrics import JUNCTION_LUT_RULE
    assert JUNCTION_LUT_RULE == "pdk_bsim4_lut_rule_diffusion" == _dev().junction_model


def test_s2_writer_table_has_ss_fields():
    """권한표 S2_WRITERS: ss·metric 필드 3개가 dc 필드 뒤에 더 있다, writer = metrics 계산 블록 이름."""
    assert SS_WRITES == (("ss_dev", (("device", "ss_dev"),)), ("metrics_ss", (("graph", "metrics_ss"),)),
                         ("metrics_dc", (("graph", "metrics_dc"),)))
    assert S2_WRITERS.writer_of("device", "ss_dev") == SS_DEV_WRITER == ss_dev.name
    assert S2_WRITERS.writer_of("graph", "metrics_ss") == METRICS_SS_WRITER == metrics_ss.name
    assert S2_WRITERS.writer_of("graph", "metrics_dc") == METRICS_DC_WRITER == metrics_dc.name
    assert METRICS_KEY == "metrics"
    for writer, fields in SS_WRITES:
        blk = {b.name: b for b in (ss_dev, metrics_ss, metrics_dc)}[writer]
        assert tuple(blk.writes) == fields
    # 필드마다 writer 하나 -- 세 writer 가 쓰는 필드는 정확히 그 3개
    owned = {kf for kf, w in S2_WRITERS.entries if w in (SS_DEV_WRITER, METRICS_SS_WRITER, METRICS_DC_WRITER)}
    assert owned == {("device", "ss_dev"), ("graph", "metrics_ss"), ("graph", "metrics_dc")}


def test_s2_writer_table_rejects_other_writer():
    """권한표가 실제로 거부한다: 다른 writer 가 ss_dev 열을 쓰면 WriterPermissionError(core 5.6)."""
    from gmid_engine.core import GraphSnapshot, WriterPermissionError
    snap = GraphSnapshot.empty(S2_WRITERS)
    with pytest.raises(WriterPermissionError):
        snap.write(METRICS_SS_WRITER, "v", {("device", "ss_dev"): {"M1": _dev()}})
    ok = snap.write(SS_DEV_WRITER, "v", {("device", "ss_dev"): {"M1": _dev()}})
    assert ok.value("device", "M1", "ss_dev") == _dev() or fp_of(ok.value("device", "M1", "ss_dev")) == fp_of(_dev())
