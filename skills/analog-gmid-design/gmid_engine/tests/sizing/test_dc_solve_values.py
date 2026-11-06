"""WB-1 D-8 (값 타입 칸·frozen), D-6 (`dc_sat_v` writer = `dc_solve`), D-9 (봉인 전 항목 불변식) -- interface card 20261104-wb1 §3.

oracle (식): card §3 의 타입 선언(칸 이름·순서·frozen)과 writer 이름 상수. D-9 는 손 거울 회로(test_block_dc 와 같은 θ)에서 봉인 점이 9 항목 전부 pass.
D-6 의 '정의 1곳·자기 사본 0' 소스 grep 은 `tests/structure/test_wb1_source.py` 가 담는다(여기는 스냅샷 writer 기록으로 관찰).
"""
import dataclasses
from types import SimpleNamespace

import pytest

from gmid_engine import sizing as S
from gmid_engine.sizing import size_and_seal

from .test_block_dc import mirror_setup, two_slice_access  # noqa: F401  (fixture 재사용)


def names(cls):
    return [f.name for f in dataclasses.fields(cls)]


def test_dc_solve_value_types_fields_and_frozen():
    assert names(S.FingerGeom) == ["m", "w_f_m", "residual"]
    assert names(S.RealizedFinger) == ["search_ref", "fp"]
    assert names(S.RealizedGeometry) == ["layout_ref", "w_request"]
    assert names(S.LutAccess) == ["memo"]                                           # w_keys 칸 없음
    assert "slice_rounds" in names(S.SccLog)
    objs = (S.FingerGeom(2, 2e-6, 0.0), S.RealizedFinger("ref", "fp"), S.RealizedGeometry("ly", ()),
            S.LutAccess(SimpleNamespace(lut=SimpleNamespace(fp="abc"))))
    for o in objs:
        assert type(o).__dataclass_params__.frozen is True
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(o, dataclasses.fields(o)[0].name, None)


def test_dc_solve_lut_access_canonical_is_the_lut_fingerprint():
    a = S.LutAccess(SimpleNamespace(lut=SimpleNamespace(fp="abc")))
    b = S.LutAccess(SimpleNamespace(lut=SimpleNamespace(fp="abd")))
    ca, cb = a.__canonical__, b.__canonical__
    ca, cb = (ca() if callable(ca) else ca), (cb() if callable(cb) else cb)
    assert ca == "abc" and cb == "abd"


def test_dc_solve_writer_constant_and_dc_sat_v_writer(tmp_path, two_slice_access):
    assert S.DC_SOLVE_WRITER == "dc_solve"
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    ev = size_and_seal(ctx, th)
    writers = {w for kf, w in ev.snapshot.writers.entries if "dc_sat_v" in repr(kf)}
    assert writers == {"dc_solve"}                                                   # 양성 대조: 필드 기록이 실제로 있다
    assert any("dc_sat_v" in repr(kf) for kf, _ in ev.snapshot.writers.entries)


def test_dc_solve_sealed_point_passes_all_nine_items(tmp_path, two_slice_access):
    ctx, th = mirror_setup(tmp_path, two_slice_access)
    ev = size_and_seal(ctx, th)
    assert ev.sealed is not None
    assert [i.status for i in ev.report.items] == ["pass"] * 9
