"""CONTRACT §3 sorted_items -- 항상 tuple, Mapping 은 키 정렬 (키, 값) 쌍, 입력 순서 무관, 비교 불가 혼합은 TypeError."""
import types

import pytest

from gmid_engine.core import sorted_items


def test_mapping_sorted_pairs():
    d = {"b": 2, "c": 3, "a": 1}
    out = sorted_items(d)
    assert type(out) is tuple
    assert out == (("a", 1), ("b", 2), ("c", 3))


def test_mapping_insertion_order_irrelevant():
    d1 = {"z": 0, "a": 1, "m": 2}
    d2 = {"m": 2, "z": 0, "a": 1}
    assert sorted_items(d1) == sorted_items(d2) == (("a", 1), ("m", 2), ("z", 0))


def test_mapping_with_key_function_sorts_by_key_of_key():
    d = {"a": 10, "bbb": 30, "cc": 20}
    # key=len: "a"(1) < "cc"(2) < "bbb"(3)
    assert sorted_items(d, key=len) == (("a", 10), ("cc", 20), ("bbb", 30))


def test_mapping_proxy_is_mapping():
    d = {"y": 1, "x": 2}
    assert sorted_items(types.MappingProxyType(d)) == (("x", 2), ("y", 1))


def test_empty_inputs():
    assert sorted_items({}) == ()
    assert sorted_items(set()) == ()
    assert type(sorted_items([])) is tuple


@pytest.mark.parametrize(
    "items",
    [{3, 1, 2}, frozenset({2, 3, 1}), [3, 1, 2], (2, 3, 1), (x for x in (2, 1, 3))],
    ids=["set", "frozenset", "list", "tuple", "generator"],
)
def test_iterables_sorted_to_tuple(items):
    out = sorted_items(items)
    assert type(out) is tuple
    assert out == (1, 2, 3)


def test_iterable_with_key():
    assert sorted_items(["ccc", "a", "bb"], key=len) == ("a", "bb", "ccc")
    assert sorted_items({1, -3, 2}, key=abs) == (1, 2, -3)


def test_list_keeps_duplicates():
    assert sorted_items([2, 1, 2]) == (1, 2, 2)


@pytest.mark.parametrize("items", [{1, "a"}, [1, "a"], {1: "x", "b": "y"}], ids=["set", "list", "mapping_keys"])
def test_incomparable_mix_rejected(items):
    with pytest.raises(TypeError):
        sorted_items(items)
