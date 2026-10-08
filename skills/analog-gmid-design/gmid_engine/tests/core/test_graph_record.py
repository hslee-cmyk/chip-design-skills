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


# =====================================================================================================================
# 2026-10-08 개정(core 성능 3, CONTRACT §5.5): fp 는 처음 읽을 때 한 번 계산해 보관 -- 값은 §5.5 식 그대로, 읽기 전에도
# ==·hash·fp_of·require_immutable 이 같게 동작하고, dataclasses.fields 에 fp 가 있다.
# oracle 종류: (a)+§5.5 식 `fp_of((kind, key, ((이름, value_fp), ...)))` -- 기대값은 계약 식에 이 test 가 넣은 값으로 직접
# 계산한다(fp_of 는 피검 대상이 아닌 §1 기준 함수, value_fp 는 §5.4 `== fp_of(value)`).
# =====================================================================================================================

from gmid_engine.core import require_immutable  # noqa: E402


def _rec(kind="device", key="m1", **vals):
    return GraphRecord(kind, key, [(n, _fv(v)) for n, v in vals.items()])


def _formula(kind, key, vals):
    return fp_of((kind, key, tuple((n, fp_of(vals[n])) for n in sorted(vals))))


@pytest.mark.parametrize("kind, key, vals", [
    ("device", "m1", {"w": 1e-6, "l": 0.15, "nf": 2}),
    ("node", "", {"v": -0.0}),
    ("graph", "g", {"theta": (0.5, float("nan"), "x"), "a": frozenset({1, 2})}),
    ("edge", "e1", {}),
], ids=["device_three_fields", "empty_key_negzero", "graph_nested", "no_fields"])
def test_lazy_fp_equals_contract_formula(kind, key, vals):
    # oracle (a)+§5.5 식(값만, 이름 정렬). 처음 읽기·두 번째 읽기 모두 식 값.
    r = GraphRecord(kind, key, [(n, _fv(v)) for n, v in vals.items()])
    expected = _formula(kind, key, vals)
    assert r.fp == expected
    assert r.fp == expected


def test_fp_stable_on_repeated_reads():
    # oracle (a): 레코드는 불변(§5.5 frozen) -> 읽을 때마다 같은 값.
    r = _rec(w=1.0, l=2.0)
    first = r.fp
    for _ in range(5):
        assert r.fp == first
    assert isinstance(first, str) and len(first) == 64


def test_eq_and_hash_before_fp_read():
    # oracle (a): 같은 인자로 만든 두 레코드는 frozen dataclass 로 == 이고 hash 가 같다 -- fp 를 읽기 전에도(§5.5 '만들 때 계산하지
    # 않는다'), 한쪽만 읽은 뒤에도(보관 상태가 비교를 바꾸면 안 됨), 둘 다 읽은 뒤에도.
    fa = _fv(1.0)
    r1 = GraphRecord("node", "n1", [("a", fa)])
    r2 = GraphRecord("node", "n1", [("a", fa)])
    assert r1 == r2
    assert hash(r1) == hash(r2)
    _ = r1.fp
    assert r1 == r2 and r2 == r1
    assert hash(r1) == hash(r2)
    _ = r2.fp
    assert r1 == r2
    assert hash(r1) == hash(r2)
    assert len({r1, r2}) == 1


def test_different_content_not_equal_before_fp_read():
    # oracle (a): 값이 다른 두 레코드는 fp 를 읽기 전에도 != (fp 보관 칸이 비교를 뭉개지 않음).
    r1 = _rec(w=1.0)
    r2 = _rec(w=2.0)
    assert r1 != r2
    assert r1.fp != r2.fp


def test_fp_of_record_same_before_and_after_fp_read():
    # oracle (a): fp_of(dataclass) 는 §1 '(모듈.클래스 이름, 선언 순서 (필드 이름, 값))'. 보관 여부로 레코드 내용 지문이
    # 바뀌면 안 된다 -- 읽기 전 레코드와 읽은 뒤 레코드(같은 인자)의 fp_of 가 같아야 한다.
    fa, fb = _fv(1.0), _fv("x")
    unread = GraphRecord("node", "n1", [("a", fa), ("b", fb)])
    read = GraphRecord("node", "n1", [("a", fa), ("b", fb)])
    _ = read.fp
    before = fp_of(unread)
    _ = unread.fp
    after = fp_of(unread)
    assert before == after == fp_of(read)


def test_require_immutable_before_and_after_fp_read():
    # oracle §2: frozen dataclass 이고 필드가 모두 허용 값 -> None. 읽기 전·후 모두.
    r = _rec(w=1.0)
    assert require_immutable(r) is None
    _ = r.fp
    assert require_immutable(r) is None


def test_dataclass_fields_still_lists_fp():
    # oracle §5.5 문장 '`dataclasses.fields` 에 `fp` 가 그대로 있다'.
    names = [f.name for f in dataclasses.fields(GraphRecord)]
    assert "fp" in names
    for n in ("kind", "key", "fields"):
        assert n in names
    r = _rec(w=1.0)
    assert "fp" in [f.name for f in dataclasses.fields(r)]


def test_frozen_record_rejects_assignment():
    # oracle §5.5 'frozen dataclass': fp 를 포함해 대입 불가.
    r = _rec(w=1.0)
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.fp = "0" * 64
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.key = "other"
