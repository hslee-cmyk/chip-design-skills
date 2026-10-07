"""`_helpers_fail` (schema_rejected·seal_violation) -- 공개 API 실패 경로로 실패 객체 형식을 확인한다(CONTRACT 머리말).

record.detail = {"reason": 사유, ...} 의 키 정렬 쌍 tuple, devices == (), margin is None. 로드 실패 = SchemaRejectedError,
조회 실패 = SealViolationError.
"""
import pytest

from gmid_engine.core import InfeasibleSizingError, SchemaRejectedError, SealViolationError
from gmid_engine.lut import load_lut_set, op_point, vgs_for_gm_id

from .conftest import TOY_SPEC, detail_of


def test_schema_rejected_record_shape(tmp_path):
    with pytest.raises(SchemaRejectedError) as ei:
        load_lut_set(str(tmp_path / "nope.json"), str(tmp_path / "nope.npz"), TOY_SPEC)
    exc = ei.value
    assert exc.record.failure_class == "SCHEMA_REJECTED"
    det = detail_of(exc)
    assert det["reason"] == "lut_manifest_missing"
    # 로드 거부는 ValueError 계열이 아니다(core 4.2)
    assert not isinstance(exc, ValueError)
    js = exc.record.to_json()
    assert js["detail"]["reason"] == "lut_manifest_missing"
    assert js["devices"] == [] and js["margin"] is None


def test_seal_violation_record_shape(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        op_point(toy_memo, "nmos", 100, 1e-6, 0.25, 0.5, 0.6)
    exc = ei.value
    assert isinstance(exc, InfeasibleSizingError) and isinstance(exc, ValueError)
    assert exc.record.failure_class == "SEAL_VIOLATION"
    det = detail_of(exc)
    assert det["reason"] == "lut_axis_out_of_range"
    # detail 키 정렬: reason 이 다른 키와 섞여 정렬돼 있다
    keys = [k for k, _ in exc.record.detail]
    assert "reason" in keys and keys == sorted(keys)


def test_seal_violation_root_record_shape(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        vgs_for_gm_id(toy_memo, "nmos", 100, 25.0, 1e-6, 0.5, 0.0)
    det = detail_of(ei.value)
    assert det["reason"] == "lut_no_strong_inversion_root"
    for key in ("gm_id", "L", "vds", "vsb", "kind", "w_key", "branch_gm_id_min", "branch_gm_id_max", "peak_vgs"):
        assert key in det, key
