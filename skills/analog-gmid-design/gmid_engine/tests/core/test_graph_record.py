"""CONTRACT §5.5 GraphRecord -- 필드 이름 정렬, get/field_names, 값 내용만의 fp, 잘못된 입력 거부."""
import dataclasses

import pytest

from gmid_engine.core import FieldValue, GraphRecord, fp_of


def _fv(v, writer="w", iv="v1", wc=1):
    return FieldValue(v, writer, iv, wc)


def test_fields_sorted_by_name():
    fz, fa = _fv(1.0), _fv(2.0)
    r = GraphRecord("device", "m1", (("z", fz), ("a", fa)))
    assert r.fields == (("a", fa), ("z", fz))
    assert r.field_names() == ("a", "z")
    assert r.kind == "device" and r.key == "m1"
    assert dataclasses.is_dataclass(r)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.key = "m2"


def test_get():
    fa = _fv(2.0)
    r = GraphRecord("node", "n1", [("a", fa)])
    assert r.get("a") is fa
    assert r.get("missing") is None


def test_fp_formula_from_contract():
    fa, fb = _fv(1.0), _fv("x")
    r = GraphRecord("node", "n1", (("b", fb), ("a", fa)))
    assert r.fp == fp_of(("node", "n1", (("a", fa.value_fp), ("b", fb.value_fp))))


def test_fp_ignores_meta():
    r1 = GraphRecord("node", "n1", (("a", _fv(1.0, "w1", "v1", 1)),))
    r2 = GraphRecord("node", "n1", (("a", _fv(1.0, "w2", "v7", 4)),))
    assert r1.fp == r2.fp


def test_fp_input_order_irrelevant():
    r1 = GraphRecord("node", "n1", (("a", _fv(1)), ("b", _fv(2))))
    r2 = GraphRecord("node", "n1", (("b", _fv(2)), ("a", _fv(1))))
    assert r1.fp == r2.fp


def test_fp_differs_on_content():
    base = GraphRecord("node", "n1", (("a", _fv(1.0)),))
    assert base.fp != GraphRecord("node", "n1", (("a", _fv(2.0)),)).fp
    assert base.fp != GraphRecord("node", "n2", (("a", _fv(1.0)),)).fp
    assert base.fp != GraphRecord("device", "n1", (("a", _fv(1.0)),)).fp
    assert base.fp != GraphRecord("node", "n1", (("b", _fv(1.0)),)).fp
    assert GraphRecord("node", "n1", (("a", _fv(0.0)),)).fp != GraphRecord("node", "n1", (("a", _fv(-0.0)),)).fp


@pytest.mark.parametrize("key", [1, None, ("n",)])
def test_bad_key_type_error(key):
    with pytest.raises(TypeError):
        GraphRecord("node", key, (("a", _fv(1)),))


@pytest.mark.parametrize("name", ["", 1, None])
def test_bad_field_name_value_error(name):
    with pytest.raises(ValueError):
        GraphRecord("node", "n1", ((name, _fv(1)),))


@pytest.mark.parametrize("val", [1.0, "x", None, (1.0, "w", "v")])
def test_field_value_not_fieldvalue_type_error(val):
    with pytest.raises(TypeError):
        GraphRecord("node", "n1", (("a", val),))


def test_duplicate_field_name_value_error():
    with pytest.raises(ValueError):
        GraphRecord("node", "n1", (("a", _fv(1)), ("a", _fv(1))))
