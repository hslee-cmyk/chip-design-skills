"""`lut_types` -- 데이터 선언(CONTRACT 0절): 상수 AXES·TOL_V_METRICS, 모든 레코드는 frozen dataclass(조회 결과 불변)."""
import dataclasses

import pytest

from gmid_engine.lut import (AXES, TOL_V_METRICS, CapTable, Caps, Curve, CurveReport, CurveRow, DcSlice, LutProvenance,
                             LutSet, LutSpec, OpPoint, SliceSource, TargetSolution, TolVCell, caps, curve_report,
                             gm_id_curve, gm_id_for_target, op_point, tol_v_table)

from .conftest import TOY_SPEC


def test_constants():
    assert AXES == ("L", "VGS", "VDS", "VS")
    assert TOL_V_METRICS == ("gm_id_inverse", "id_equivalent")


@pytest.mark.parametrize("cls", [CapTable, Caps, Curve, CurveReport, CurveRow, DcSlice, LutProvenance, LutSet, LutSpec,
                                 OpPoint, SliceSource, TargetSolution, TolVCell])
def test_frozen_dataclass(cls):
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen


def test_lutspec_fields_and_value_semantics():
    assert [f.name for f in dataclasses.fields(LutSpec)] == [
        "manufacturing_grid_m", "min_finger_w_m", "device_kinds", "cap_column_suffix"]
    again = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
    assert again == TOY_SPEC and hash(again) == hash(TOY_SPEC)


def test_tolvcell_fields():
    assert [f.name for f in dataclasses.fields(TolVCell)] == [
        "gm_id_inverse_v", "id_equivalent_v", "n_targets", "n_inverse_failed"]
    assert TolVCell(None, None, 0, 0) == TolVCell(None, None, 0, 0)


def test_query_results_are_immutable(toy, toy_memo):
    objs = [
        toy, toy.spec, toy.provenance, toy.provenance.slices[0], toy.slice_map[("nmos", 100)], toy.cap_map["nmos"],
        op_point(toy_memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.0),
        gm_id_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0),
        gm_id_for_target(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6),
        caps(toy_memo, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6),
        tol_v_table(toy_memo, "nmos", 100).cells[1][0],
        curve_report(toy_memo), curve_report(toy_memo).rows[0],
    ]
    for o in objs:
        f = dataclasses.fields(o)[0].name
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(o, f, getattr(o, f))
