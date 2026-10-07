"""CONTRACT §4.1 FailureRecord -- 정규화, to_json 4 키, 불변·지문 결정론, 잘못된 입력 거부."""
import dataclasses

import pytest

from gmid_engine.core import FailureRecord, fp_of, require_immutable


def test_is_frozen_dataclass():
    r = FailureRecord("NONCONVERGENT")
    assert dataclasses.is_dataclass(r)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.failure_class = "X"


def test_defaults():
    r = FailureRecord("SEAL_VIOLATION")
    assert r.failure_class == "SEAL_VIOLATION"
    assert r.devices == ()
    assert r.margin is None
    assert r.detail == ()


def test_devices_dedup_sorted_tuple():
    r = FailureRecord("C", devices=["m3", "m1", "m3", "m2"])
    assert r.devices == ("m1", "m2", "m3")
    assert type(r.devices) is tuple


def test_margin_int_to_float():
    r = FailureRecord("C", margin=3)
    assert type(r.margin) is float and r.margin == 3.0
    assert FailureRecord("C", margin=-0.5).margin == -0.5


def test_detail_mapping_sorted_pairs():
    r = FailureRecord("C", detail={"z": 1, "a": "x", "m": (1, 2)})
    assert r.detail == (("a", "x"), ("m", (1, 2)), ("z", 1))


def test_detail_pair_iterable_sorted():
    r = FailureRecord("C", detail=[("b", 2), ("a", 1)])
    assert r.detail == (("a", 1), ("b", 2))


def test_to_json_exact_shape():
    r = FailureRecord("INFEASIBLE_TARGET", devices=("m2", "m1"), margin=2, detail={"k": "v", "a": 1})
    j = r.to_json()
    assert set(j) == {"class", "devices", "margin", "detail"}
    assert j["class"] == "INFEASIBLE_TARGET"
    assert j["devices"] == ["m1", "m2"] and type(j["devices"]) is list
    assert j["margin"] == 2.0 and type(j["margin"]) is float
    assert j["detail"] == {"a": 1, "k": "v"} and type(j["detail"]) is dict


def test_to_json_none_margin_empty_detail():
    j = FailureRecord("X").to_json()
    assert j == {"class": "X", "devices": [], "margin": None, "detail": {}}


def test_immutable_and_fp_deterministic():
    r1 = FailureRecord("C", devices=("b", "a"), margin=1.5, detail={"x": 1, "y": 2})
    r2 = FailureRecord("C", devices=["a", "b", "a"], margin=1.5, detail=[("y", 2), ("x", 1)])
    assert require_immutable(r1) is None
    assert fp_of(r1) == fp_of(r2)


def test_fp_differs_on_content():
    base = FailureRecord("C", devices=("a",), margin=1.0, detail={"x": 1})
    assert fp_of(base) != fp_of(FailureRecord("D", devices=("a",), margin=1.0, detail={"x": 1}))
    assert fp_of(base) != fp_of(FailureRecord("C", devices=("b",), margin=1.0, detail={"x": 1}))
    assert fp_of(base) != fp_of(FailureRecord("C", devices=("a",), margin=2.0, detail={"x": 1}))
    assert fp_of(base) != fp_of(FailureRecord("C", devices=("a",), margin=1.0, detail={"x": 2}))


@pytest.mark.parametrize("fc", ["", 1, None, b"X"])
def test_bad_failure_class_value_error(fc):
    with pytest.raises(ValueError):
        FailureRecord(fc)


def test_devices_str_rejected():
    with pytest.raises(TypeError):
        FailureRecord("C", devices="m1")


def test_devices_non_str_element_rejected():
    with pytest.raises(TypeError):
        FailureRecord("C", devices=("m1", 2))


@pytest.mark.parametrize("m", [True, False, "1.0", (1,)])
def test_bad_margin_rejected(m):
    with pytest.raises(TypeError):
        FailureRecord("C", margin=m)


def test_detail_non_str_key_rejected():
    with pytest.raises(TypeError):
        FailureRecord("C", detail={1: "x"})


@pytest.mark.parametrize("v", [[1], {"a": 1}, {1}])
def test_detail_mutable_value_rejected(v):
    with pytest.raises(TypeError):
        FailureRecord("C", detail={"k": v})
