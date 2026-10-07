"""layout/transistor.py -- `Transistor`(복사, CONTRACT 0 표·1). 기대값: 옛 SD `Transistor` 와 같은 필드·기본값·검증 동작."""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.layout.transistor import Transistor


def test_fields_and_defaults_same_as_oracle(sd):
    new = [(f.name, f.default) for f in dataclasses.fields(Transistor)]
    old = [(f.name, f.default) for f in dataclasses.fields(sd.Transistor)]
    assert new == old
    # 손 확인: 필수 4 + 선택 기본값
    names = [n for n, _ in new]
    assert names[:4] == ["name", "kind", "source", "drain"]
    assert dict(new)["n_fingers"] == 1


def test_construct_and_equality():
    t = Transistor("M1", "nmos", source="s", drain="d", n_fingers=3)
    assert (t.name, t.kind, t.source, t.drain, t.n_fingers) == ("M1", "nmos", "s", "d", 3)
    assert t.finger_w is None and t.w is None and t.l is None and t.gate is None and t.stack_id is None
    assert t == Transistor("M1", "nmos", "s", "d", 3)
    assert t != Transistor("M1", "nmos", "s", "d", 2)


@pytest.mark.parametrize("bad", [0, -1])
def test_n_fingers_below_one_rejected(bad, sd):
    with pytest.raises(ValueError):
        Transistor("M1", "nmos", "s", "d", n_fingers=bad)
    with pytest.raises(ValueError):
        sd.Transistor("M1", "nmos", "s", "d", n_fingers=bad)


@pytest.mark.parametrize("kind", ["NMOS", "pfet", ""])
def test_kind_must_be_nmos_or_pmos(kind):
    with pytest.raises(ValueError):
        Transistor("M1", kind, "s", "d")


def test_pmos_accepted():
    assert Transistor("M1", "pmos", "s", "d").kind == "pmos"
