"""`sizing/local_values.py` (U4) -- 국소 봉인 값 형식 `LocalSeal`·`SnapshotFragment` (설계 41 §5.3 반환값
`LocalSeal{ok, failures[FailureRecord], snapshot_fragment, gain_db, power_w, area_m2}`, CONTRACT 14.5).

oracle (d): 설계 문언의 필드 목록. 값 형식은 S2 값과 같이 불변(core require_immutable)이어야 캐시 키·결과 비교에 쓸 수 있다.
"""
import dataclasses

import pytest

from gmid_engine.core import require_immutable
from gmid_engine.sizing import LocalSeal, SnapshotFragment


def test_fields_match_design():
    assert [f.name for f in dataclasses.fields(LocalSeal)] == ["ok", "failures", "snapshot_fragment", "gain_db",
                                                                "power_w", "area_m2"]
    assert [f.name for f in dataclasses.fields(SnapshotFragment)] == ["devices", "nodes"]


def test_defaults():
    """gain_db·power_w·area_m2 기본 None(실패 점·U7 병합 전), 빈 조각 = ((), ())."""
    s = LocalSeal(False, (), SnapshotFragment())
    assert s.gain_db is None and s.power_w is None and s.area_m2 is None
    assert SnapshotFragment() == SnapshotFragment((), ())


def test_frozen_and_comparable():
    a = LocalSeal(True, (), SnapshotFragment((), (("n", 0.5),)), None, 1e-5, 2e-12)
    b = LocalSeal(True, (), SnapshotFragment((), (("n", 0.5),)), None, 1e-5, 2e-12)
    assert a == b and hash(a) == hash(b)
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.ok = False
    with pytest.raises(dataclasses.FrozenInstanceError):
        a.snapshot_fragment.nodes = ()
    require_immutable(a)
