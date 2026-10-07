"""CONTRACT §2 require_immutable -- 허용 값은 None 반환, 가변 값은 어디에 있든 TypeError."""
import dataclasses

import pytest

from gmid_engine.core import require_immutable


class _MyFloat(float):
    pass


@dataclasses.dataclass(frozen=True)
class _Frozen:
    a: int
    b: tuple


@dataclasses.dataclass(frozen=True)
class _FrozenWithList:
    a: list


@dataclasses.dataclass
class _NotFrozen:
    a: int


class _CanonOk:
    def __canonical__(self):
        return ("ok", (1, 2.0))


class _CanonBad:
    def __canonical__(self):
        return ["mutable"]


class _Plain:
    pass


@pytest.mark.parametrize(
    "value",
    [
        None, True, False, 0, -7, 1.5, -0.0, _MyFloat(2.5), "s", "", b"b",
        (), (1, "a", (2.0, None)), frozenset(), frozenset({1, "x", (2, 3)}),
        _Frozen(1, (2, 3)), (_Frozen(1, ()),), _CanonOk(), (_CanonOk(), frozenset({4})),
    ],
)
def test_allowed_returns_none(value):
    assert require_immutable(value) is None


@pytest.mark.parametrize(
    "value",
    [
        {}, {"a": 1}, [], [1], set(), {1}, bytearray(b"x"), _Plain(), _NotFrozen(1), object(),
    ],
    ids=["dict_empty", "dict", "list_empty", "list", "set_empty", "set", "bytearray", "plain", "nonfrozen_dc", "object"],
)
def test_mutable_rejected(value):
    with pytest.raises(TypeError):
        require_immutable(value)


@pytest.mark.parametrize(
    "value",
    [
        (1, [2]),
        ((1, (2, {3: 4})),),
        frozenset({(1, _Plain())}),
        _FrozenWithList([1]),
        _Frozen(1, (2, [3])),
        _CanonBad(),
        (_CanonOk(), bytearray(b"z")),
    ],
    ids=["list_in_tuple", "dict_deep", "obj_in_frozenset", "frozen_dc_list_field", "frozen_dc_nested_list",
         "canonical_returns_list", "bytearray_in_tuple"],
)
def test_mutable_nested_rejected(value):
    with pytest.raises(TypeError):
        require_immutable(value)
