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
    # [FS-1 §3.1] FingerGeom = (m, residual) (w_f_m 칸 없음), RealizeInput(search_ref) (RealizedFinger 대체), slice_rounds 칸 삭제
    assert names(S.FingerGeom) == ["m", "residual"]
    assert names(S.RealizeInput) == ["search_ref"]
    assert names(S.WfCell) == ["members", "w_key"]
    assert names(S.WfInput) == ["cells_ref", "keys"]
    assert names(S.RealizedGeometry) == ["layout_ref", "w_request"]
    assert names(S.LutAccess) == ["memo"]                                           # w_keys 칸 없음
    assert "slice_rounds" not in names(S.SccLog)
    assert not hasattr(S, "RealizedFinger")
    objs = (S.FingerGeom(2, 0.0), S.RealizeInput("ref"), S.RealizedGeometry("ly", ()),
            S.WfCell(("A",), 100), S.WfInput((S.WfCell(("A",), 100),), (100,)),
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


def _canon(o):
    c = o.__canonical__
    return c() if callable(c) else c


def test_wf_input_validation_and_canonical():
    """FS-1 §3.1: len(keys) == len(cells_ref), 원소 int 아니면 ValueError. `__canonical__` = ("wf_input", 칸 멤버 tuple, keys) -- 출발값 w_key 는 지문 밖."""
    from gmid_engine.core import fp_of
    cells = (S.WfCell(("A", "B"), 100), S.WfCell(("C",), None))
    wf = S.WfInput(cells, (100, 200))
    assert _canon(wf) == ("wf_input", (("A", "B"), ("C",)), (100, 200))
    with pytest.raises(ValueError):
        S.WfInput(cells, (100,))                                  # 길이 다름
    with pytest.raises(ValueError):
        S.WfInput(cells, (100, 2.5))                              # int 아님
    same_structure = S.WfInput((S.WfCell(("A", "B"), 50), S.WfCell(("C",), 300)), (100, 200))   # 출발값만 다름
    assert fp_of(same_structure) == fp_of(wf)                     # 칸 구조 + keys 같으면 지문 같음
    other_keys = S.WfInput(cells, (100, 201))
    assert fp_of(other_keys) != fp_of(wf)                         # keys 하나 다르면 다름
    other_struct = S.WfInput((S.WfCell(("A",), 100), S.WfCell(("B", "C"), None)), (100, 200))
    assert fp_of(other_struct) != fp_of(wf)


def test_realize_input_canonical_is_marker_only():
    """FS-1 §3.1: `RealizeInput.__canonical__` = ("realize_input",) -- 스냅샷 지문을 덧대지 않는다 (참조가 달라도 같음)."""
    from gmid_engine.core import fp_of
    a, b = S.RealizeInput(search_ref=object()), S.RealizeInput(search_ref=object())
    assert _canon(a) == ("realize_input",) == _canon(b)
    assert fp_of(a) == fp_of(b)


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
