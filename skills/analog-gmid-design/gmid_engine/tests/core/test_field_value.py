"""CONTRACT §5.4 FieldValue -- value_fp 는 생성 시 계산(인자 불가), 가변 값·잘못된 메타 거부."""
import dataclasses

import pytest

from gmid_engine.core import FieldValue, fp_of


def test_basic_fields_and_default_write_count():
    fv = FieldValue(1.5, "sizer", "v1")
    assert fv.value == 1.5
    assert fv.writer == "sizer"
    assert fv.input_version == "v1"
    assert fv.write_count == 1
    assert dataclasses.is_dataclass(fv)
    with pytest.raises(dataclasses.FrozenInstanceError):
        fv.value = 2.0


@pytest.mark.parametrize("value", [1.5, -0.0, 0.0, ("a", (1, 2)), None, "s", frozenset({1})])
def test_value_fp_is_content_fingerprint(value):
    assert FieldValue(value, "w", "v").value_fp == fp_of(value)


def test_value_fp_independent_of_meta():
    a = FieldValue((1, 2), "w1", "v1", 1)
    b = FieldValue((1, 2), "w2", "v9", 5)
    assert a.value_fp == b.value_fp
    assert FieldValue(0.0, "w", "v").value_fp != FieldValue(-0.0, "w", "v").value_fp


def test_value_fp_not_accepted_as_argument():
    with pytest.raises(TypeError):
        FieldValue(1, "w", "v", 1, "0" * 64)
    with pytest.raises(TypeError):
        FieldValue(1, "w", "v", value_fp="0" * 64)


def test_write_count_explicit():
    assert FieldValue(1, "w", "v", 3).write_count == 3


@pytest.mark.parametrize("value", [[1], {"a": 1}, {1}, bytearray(b"x"), (1, [2])])
def test_mutable_value_rejected(value):
    with pytest.raises(TypeError):
        FieldValue(value, "w", "v")


@pytest.mark.parametrize("writer", ["", 1, None])
def test_bad_writer_rejected(writer):
    with pytest.raises(ValueError):
        FieldValue(1, writer, "v")


@pytest.mark.parametrize("iv", ["", 1, None])
def test_bad_input_version_rejected(iv):
    with pytest.raises(ValueError):
        FieldValue(1, "w", iv)


@pytest.mark.parametrize("wc", [0, -1, True, False, 1.0, 2.5, "2"])
def test_bad_write_count_rejected(wc):
    with pytest.raises(ValueError):
        FieldValue(1, "w", "v", wc)
