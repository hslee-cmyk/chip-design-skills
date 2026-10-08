"""`lut_types` -- 데이터 선언(CONTRACT 0절): 상수 AXES·TOL_V_METRICS, 모든 레코드는 frozen dataclass(조회 결과 불변)."""
import dataclasses

import pytest

from gmid_engine.lut import (AXES, CLASS_HERMITE, CURVE_QUANTITIES, NOISE_B_STATUS, TOL_NOISE_METRICS, TOL_V_METRICS, CapTable,
                             Caps, Curve, CurveReport, CurveRow, DcSlice, GmIdAxisCurve, LutProvenance, LutSet, LutSpec,
                             MismatchSens, MismatchSigma, MismatchTable, NoiseParams, NoisePlanes, NoiseTable, OpPoint,
                             SliceSource, TargetSolution, TolMismatchCell, TolNoiseCell, TolVCell, caps, curve_report,
                             gm_id_curve, gm_id_for_target, idu_curve, op_point, tol_v_table)

from .conftest import TOY_SPEC


def test_constants():
    assert AXES == ("L", "VGS", "VDS", "VS")
    assert TOL_V_METRICS == ("gm_id_inverse", "id_equivalent")
    # [r7] 4.5·9.2·9.4·4.1: 곡선 표 양 4개, 잡음 B 상태 3개(설계 41 §7.2 '미상'), 잡음 tol 지표 2개, Hermite 칸 분류 이름
    assert set(CURVE_QUANTITIES) == {"ft_hz", "intrinsic_gain", "vdsat_v", "idu_a"}
    assert NOISE_B_STATUS == ("known", "no_feedthrough_free_point", "nonpositive")
    assert TOL_NOISE_METRICS == ("flicker", "thermal")
    assert CLASS_HERMITE == "hermite"


@pytest.mark.parametrize("cls", [CapTable, Caps, Curve, CurveReport, CurveRow, DcSlice, LutProvenance, LutSet, LutSpec,
                                 OpPoint, SliceSource, TargetSolution, TolVCell,
                                 GmIdAxisCurve, MismatchSens, MismatchSigma, MismatchTable, NoiseParams, NoisePlanes,
                                 NoiseTable, TolMismatchCell, TolNoiseCell])
def test_frozen_dataclass(cls):
    assert dataclasses.is_dataclass(cls)
    assert cls.__dataclass_params__.frozen


def test_lutspec_fields_and_value_semantics():
    # [r7] 1.1: noise_ef = ((kind, EF), ...) 기본 () -- 설계 41 §7.2 'EF 는 PDK 모델 카드에서 파싱해 core PDK 선언에' 를 부르는 쪽이 넘기는 칸
    assert [f.name for f in dataclasses.fields(LutSpec)] == [
        "manufacturing_grid_m", "min_finger_w_m", "device_kinds", "cap_column_suffix", "noise_ef"]
    again = LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),))
    assert again == TOY_SPEC and hash(again) == hash(TOY_SPEC)
    assert again.noise_ef == ()
    assert LutSpec(1e-8, (("nmos", 1.5e-6),), (("toyn", "nmos"),), (("nmos", "_n"),), noise_ef=(("nmos", 0.84),)) != TOY_SPEC


def test_tolvcell_fields():
    # [r5] 환산 전 값 gm_id_inverse_loo_v·id_equivalent_loo_v 가 뒤에 더해졌다(기본값 None -- 4칸 생성자 호출도 받는다)
    assert [f.name for f in dataclasses.fields(TolVCell)] == [
        "gm_id_inverse_v", "id_equivalent_v", "n_targets", "n_inverse_failed",
        "gm_id_inverse_loo_v", "id_equivalent_loo_v"]
    c = TolVCell(None, None, 0, 0)
    assert c == TolVCell(None, None, 0, 0)
    assert c.gm_id_inverse_loo_v is None and c.id_equivalent_loo_v is None
    assert c == TolVCell(None, None, 0, 0, None, None)
    assert TolVCell(0.1, 0.2, 3, 1, 0.4, 0.8) != TolVCell(0.1, 0.2, 3, 1)
    assert {f.name: f.default for f in dataclasses.fields(TolVCell)[4:]} == {
        "gm_id_inverse_loo_v": None, "id_equivalent_loo_v": None}


def test_query_results_are_immutable(toy, toy_memo):
    objs = [
        toy, toy.spec, toy.provenance, toy.provenance.slices[0], toy.slice_map[("nmos", 100)], toy.cap_map["nmos"],
        op_point(toy_memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.0),
        gm_id_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0),
        gm_id_for_target(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0, W=2e-6, current=2e-6),
        caps(toy_memo, "nmos", 1e-6, 0.5, 0.5, 0.0, 3e-6),
        tol_v_table(toy_memo, "nmos", 100).cells[1][0],
        curve_report(toy_memo), curve_report(toy_memo).rows[0],
        idu_curve(toy_memo, "nmos", 100, 1e-6, 0.5, 0.0),
    ]
    for o in objs:
        f = dataclasses.fields(o)[0].name
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(o, f, getattr(o, f))
