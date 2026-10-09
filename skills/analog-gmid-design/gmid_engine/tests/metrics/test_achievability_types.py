"""metrics/achievability_types.py -- GB4 값 형식·어휘(metrics CONTRACT 10.1 층 0, 모듈 문서 '공개 정의는 frozen dataclass 와 상수뿐').

oracle (d) 계약 선언값: 결과 레코드는 frozen 이고 `core.fp_of` 로 지문할 수 있다(S0 지문 필드). 어휘 문자열(계약 10.2~10.7)은 공개 API 로
상수를 내보내지 않으므로(계약 10: test 는 `from gmid_engine.metrics import ...` 만) 각 계산 test 가 결과 값으로 확인한다.
"""
from __future__ import annotations

import dataclasses

import pytest

import gmid_engine.metrics as M
from gmid_engine.core import fp_of

RECORDS = ("CurveCheck", "SliceCurveCheck", "CurveChecks", "BlockBound", "GainCheck", "AreaBound", "EdgeCost", "HeadroomRow",
           "HeadroomResult", "DofReport", "Achievability", "BlockSpec", "AxisSpec", "MosLocal", "ResLocal", "BlockModel", "LocalInputs")


@pytest.mark.parametrize("name", RECORDS)
def test_records_are_frozen_dataclasses(name):
    cls = getattr(M, name)
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen


def test_result_records_are_fingerprintable_and_frozen():
    bb = M.BlockBound(key=("out",), role="main", status="certified", a_max_db=1.0, b_db=0.1, pi=10, axes=(("vgs", 10),),
                      row_condition=(("vgs:M1", 0.5),), reason=None, found_db=None, members=("M1",), n_rows=10)
    dof = M.DofReport(status="square", structural_rank=1, n_variables=1, n_equations=1, unmatched_equations=(),
                      free_variables=(), numeric_ranks=(), competing_pairs=())
    a = fp_of(bb)
    assert a == fp_of(dataclasses.replace(bb)) and a != fp_of(dataclasses.replace(bb, a_max_db=2.0))
    assert isinstance(fp_of(dof), str)
    with pytest.raises(dataclasses.FrozenInstanceError):
        bb.status = "unknown"
