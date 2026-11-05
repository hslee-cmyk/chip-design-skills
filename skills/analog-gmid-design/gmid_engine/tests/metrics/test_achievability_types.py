"""metrics/achievability_types.py -- GB4 값 형식·어휘(metrics CONTRACT 10.1 층 0, 모듈 문서 '공개 정의는 frozen dataclass 와 상수뿐').

oracle (d) 계약 선언값: 결과 레코드는 frozen 이고 `core.fp_of` 로 지문할 수 있다(S0 지문 필드). 어휘 문자열(계약 10.2~10.7)은 공개 API 로
상수를 내보내지 않으므로(계약 10: test 는 `from gmid_engine.metrics import ...` 만) 각 계산 test 가 결과 값으로 확인한다.
"""
from __future__ import annotations

import dataclasses

import pytest

import gmid_engine.metrics as M
from gmid_engine.core import fp_of

# [U17 ①-b] 설계 40 v1.9.1 §2.4.2·§2.4.8 D2: 묶음 `Achievability` 는 필드 `graph/ach` 로 풀려 없어졌다(필드 11개는 test_s0_fields·
# tests/pipeline/test_stage_b 가 본다). `EdgeCost` 는 LUT 파생 값이라 lut 값 형식으로 옮겼다(§2.4.6 D10 -- tests/lut/test_derived_fns 가 본다).
RECORDS = ("CurveCheck", "SliceCurveCheck", "CurveChecks", "BlockBound", "GainCheck", "AreaBound", "HeadroomRow",
           "HeadroomResult", "DofReport", "BlockSpec", "AxisSpec", "MosLocal", "ResLocal", "BlockModel", "LocalInputs")


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


def test_ub1_new_fields_defaults_and_fingerprint():
    """[UB-1] 새 칸은 끝에 있고 기본값이 있다: BlockBound.load_note None, BlockSpec.others (), BlockModel.omitted_load ()·decomposed_only False.
    load_note 는 지문에 든다(값이 다르면 지문이 다르다). oracle (a) 구성."""
    from .gb4_hand import block_spec, cs_model
    bb = M.BlockBound(key=("out",), role="main", status="certified", a_max_db=1.0, b_db=0.1, pi=10, axes=(("vgs", 10),),
                      row_condition=(("vgs:M1", 0.5),), reason=None, found_db=None, members=("M1",), n_rows=10)
    assert getattr(bb, "load_note", "absent") is None
    note = ("load_admittance_unfixed", ("M2",))
    noted = dataclasses.replace(bb, load_note=note)
    assert noted.load_note == note and fp_of(noted) != fp_of(bb)
    names = [f.name for f in dataclasses.fields(M.BlockBound)]
    assert names[-1] == "load_note"
    assert getattr(block_spec(("out",), ("M1",), ("in",), ("out",), ("in", "out")), "others", "absent") == ()
    m = cs_model()
    assert getattr(m, "omitted_load", "absent") == () and getattr(m, "decomposed_only", "absent") is False
