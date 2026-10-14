"""metrics/s0_fields.py -- metrics 의 S0 수준 graph 필드 이름·writer·권한표 조각 (설계 40 v1.9.1 §2.4.1·§2.4.2·§2.4.8 D2·D7·D9).

oracle (d) 설계 문장:
- §2.4.2 '레코드 key … 신규는 s1v, coupling, ach, start, kernel' -> GB4 레코드 key = "ach".
- §2.4.8 GB4 행(D2): `graph/ach` 필드 = curve_checks, gain_checks, area_bound, headroom_rows, buffer_window_report, warnings, reasons, verdict, dof,
  count_budget, local_inputs(11개, 옛 block_bounds 없음), writer `achievability`(GB4).
- §2.4.8 'metric 구조 입력' 행: `graph/s1v: metric_structure`, writer `metric_structure`(MOD5).
- §2.4.7 SearchContext 칸 배정: `graph/kernel: junction_source`, `mismatch_source`, `model_error`(writer 이름은 설계가 정하지 않음 -- 항목 하나·필드 이름만 본다).
- 권한표 = 필드마다 writer 하나(§2.4.1 '필드마다 writer 하나').
"""
from __future__ import annotations

from gmid_engine.core import WriterTable
from gmid_engine.metrics import ACH_KEY, ACH_WRITES, ACHIEVABILITY_WRITER, METRIC_STRUCTURE_WRITER, METRICS_S0_WRITERS

ACH_FIELDS = {"curve_checks", "gain_checks", "area_bound", "headroom_rows", "buffer_window_report", "warnings", "reasons", "verdict", "dof",
              "count_budget", "local_inputs"}


def test_ach_record_key_and_fields():
    assert ACH_KEY == "ach"
    assert {f for _k, f in ACH_WRITES} == ACH_FIELDS and len(ACH_WRITES) == 11
    assert all(kind == "graph" for kind, _f in ACH_WRITES)
    assert "block_bounds" not in {f for _k, f in ACH_WRITES}


def test_writer_table_entries():
    assert isinstance(METRICS_S0_WRITERS, WriterTable)
    assert ACHIEVABILITY_WRITER == "achievability" and METRIC_STRUCTURE_WRITER == "metric_structure"
    for field in ACH_FIELDS:
        assert METRICS_S0_WRITERS.writer_of("graph", field) == "achievability", field
    assert METRICS_S0_WRITERS.writer_of("graph", "metric_structure") == "metric_structure"
    for field in ("junction_source", "mismatch_source", "model_error"):
        assert METRICS_S0_WRITERS.writer_of("graph", field) is not None, field


def test_one_writer_per_field():
    keys = [kf for kf, _w in METRICS_S0_WRITERS.entries]
    assert len(keys) == len(set(keys))
    assert len(keys) == len(ACH_FIELDS) + 1 + 3
