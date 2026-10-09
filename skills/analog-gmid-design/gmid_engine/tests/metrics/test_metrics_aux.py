"""`metrics_aux` 계산 블록과 `ss_evaluate` 배선 -- metrics CONTRACT 10.0·10.7, 설계 40 §3.8(판정 위치 = 외층 전회로 계산 한 곳, DEC-74),
41 §2.2(평가마다 `gain_residual_db`·`ss.block_gain` 기록).

회로·DC 점: `test_ss_evaluate` 와 같은 CS + 저항 부하(toy LUT r6, 실제 sizing 경로 size_and_seal). toy LUT 에는 VDSAT 열·mismatch 감도 표가 없다.

oracle:
* (d) 계약 10.7·설계 40 §3.8-8 문장: AUX 결과 형식 metric 은 metrics_aux 가 계산해 `SsEvaluation.ss` 에 합쳐진다, 입력이 없으면 정의 불가 사유
  (mismatch 없음 `mismatch_source_missing`, LUT mismatch 표 없음 `mismatch_lut_missing`, 포화 열 없음 `sat_unavailable`(DEC-88 근사 안 함),
  단일 출력 기준 미선언 `reference_undeclared`, 구조 입력 없음 `structure_unavailable`). 구조가 있으면 전달 뷰마다 `block_residual`·`nqs_ratio` 보고.
* (a) 단일 블록(CS) 분해 잔차 0, 전회로 이득 = 폐형식 20·log10(gm/(gds + 1/R))(test_ss_evaluate 의 `_expected` 와 같은 독립 npz 해석식).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import PdkMismatchBlock, PdkMismatchModel
from gmid_engine.metrics import (REPORT_BLOCK_RESIDUAL, MetricBundle, MismatchSource, ss_evaluate)
from gmid_engine.sizing import METRICS_KEY, SealedSnapshot

from . import u7_hand as H
from .conftest import codes
from .test_ss_evaluate import _expected, build, theta

AUX = (("offset_in_sigma_mv", "<=", 3.0, None), ("offset_sys_mv", "<=", 3.0, None), ("swing_out_v", ">=", 0.1, None),
       ("ff_gm_ratio", ">=", 1.0, None))
BASE = (("gain_ss_db", ">=", 10.0, None),)


def _struct():
    return H.vstruct("transfer:0", {"in": 1.0}, ("out",), (H.block(("out",), ("in",), ("out",), ("in", "out"), input_cells=("M1",)),),
                     (), ("M1",), ("M1",))


@pytest.fixture(scope="module")
def case(tmp_path_factory):
    spec, ctx, ev, js = build(tmp_path_factory.mktemp("aux"), cons=BASE + AUX)
    return spec, ctx, SealedSnapshot(ev.snapshot, ev.report), js


def _codes_by_metric(bundle):
    return {req.metric: codes(res.undefined) for req, res in bundle.entries}


def test_aux_entries_merged_after_ss_entries_and_field_written(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js)
    assert [q.metric for q, _ in res.ss.entries] == ["gain_ss_db", "offset_in_sigma_mv", "offset_sys_mv", "swing_out_v", "ff_gm_ratio"]
    aux = res.snapshot.value("graph", METRICS_KEY, "metrics_aux")
    assert isinstance(aux, MetricBundle)
    assert [q.metric for q, _ in aux.entries] == ["offset_in_sigma_mv", "offset_sys_mv", "swing_out_v", "ff_gm_ratio"]
    assert [q.metric for q, _ in res.snapshot.value("graph", METRICS_KEY, "metrics_ss").entries] == ["gain_ss_db"]


def test_missing_inputs_are_undefined_not_silent(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js)
    got = _codes_by_metric(res.ss)
    assert got["offset_in_sigma_mv"] == {"mismatch_source_missing"}
    assert got["offset_sys_mv"] == {"reference_undeclared"}
    assert got["swing_out_v"] == {"sat_unavailable"}
    assert got["ff_gm_ratio"] == {"structure_unavailable"}
    assert all(res_.value is None for q, res_ in res.ss.entries if q.metric != "gain_ss_db")


def test_mismatch_source_without_lut_table(case):
    spec, ctx, sealed, js = case
    rows = (("toxe", "toy_toxe_slope", 1e-3, 1),)
    model = PdkMismatchModel("nmos", ("toxe",), (PdkMismatchBlock("b", 1e-7, 1e-4, 1e-7, 1e-4, rows, 1),), "a", "0" * 64, "b", "0" * 64)
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, mismatch=MismatchSource((("nmos", model),), "1" * 64))
    assert _codes_by_metric(res.ss)["offset_in_sigma_mv"] == {"mismatch_lut_missing"}


def test_structure_gives_block_residual_and_nqs_reports(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    reports = dict(res.ss.reports)
    br = dict(reports[REPORT_BLOCK_RESIDUAL])
    exp = _expected(res.snapshot)
    assert br["full_gain_db"] == pytest.approx(exp["gain_db"], rel=1e-12)
    assert br["gain_residual_db"] == pytest.approx(0.0, abs=1e-9)
    assert br["view"] == "transfer:0"
    gain = {req.metric: r.value for req, r in res.ss.entries}["gain_ss_db"]
    assert br["full_gain_db"] == pytest.approx(gain, rel=1e-12)            # 같은 계(같은 뷰 = 같은 계, 계약 10.2)
    nqs = dict(reports["nqs_ratio"])
    assert nqs["undefined"] == ("ugf_unavailable",)                          # ugf 제약 없음 -> 분자 없음
    assert _codes_by_metric(res.ss)["ff_gm_ratio"] == {"no_feedforward"}


def test_aux_does_not_change_ss_metric_values(case):
    spec, ctx, sealed, js = case
    plain = ss_evaluate(sealed, ctx, theta(), tuple(c for c in spec.constraints if c.metric == "gain_ss_db"), junction=js)
    full = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    a = {q.metric: r.value for q, r in plain.ss.entries}
    b = {q.metric: r.value for q, r in full.ss.entries}
    assert a["gain_ss_db"] == b["gain_ss_db"]


def test_no_aux_request_no_structure_keeps_metrics_ss_bundle(case):
    spec, ctx, sealed, js = case
    res = ss_evaluate(sealed, ctx, theta(), tuple(c for c in spec.constraints if c.metric == "gain_ss_db"), junction=js)
    assert res.ss is res.snapshot.value("graph", METRICS_KEY, "metrics_ss")


def test_deterministic(case):
    spec, ctx, sealed, js = case
    a = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    b = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js, structure=H.MetricStructure_of(_struct()))
    assert a.ss == b.ss
