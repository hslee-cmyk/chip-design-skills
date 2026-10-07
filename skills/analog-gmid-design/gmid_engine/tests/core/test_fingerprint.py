"""CONTRACT §1 내용 지문 fp_of -- 정준성(같은 내용 같은 지문)과 구분(다른 내용 다른 지문), 미지원 타입 거부."""
import dataclasses
import math
import os
import subprocess
import sys
import types

import pytest

from gmid_engine.core import fp_of


def _is_sha256_hex(s):
    return isinstance(s, str) and len(s) == 64 and set(s) <= set("0123456789abcdef")


# ---------- 출력 형식 ----------

@pytest.mark.parametrize("obj", [None, 0, 1.5, "x", b"x", (1, 2), [1], {"a": 1}, {1, 2}, frozenset({3})])
def test_output_is_64_lowercase_hex(obj):
    assert _is_sha256_hex(fp_of(obj))


def test_same_content_same_fp_repeated_calls():
    obj = {"b": (1, 2.5, "x"), "a": [None, True, b"z"]}
    assert fp_of(obj) == fp_of(obj)
    assert fp_of(obj) == fp_of({"a": [None, True, b"z"], "b": (1, 2.5, "x")})


# ---------- 결정론: PYTHONHASHSEED 무관 ----------

def test_fp_independent_of_pythonhashseed():
    skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from gmid_engine.core import fp_of\n"
        "print(fp_of({'k%%d' %% i: frozenset({'a%%d' %% i, 'b', 'c'}) for i in range(20)}))\n"
        "print(fp_of({'alpha', 'beta', 'gamma', 'delta', 'eps'}))\n"
    ) % skill_dir
    outs = []
    for seed in ("0", "1", "12345"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
        outs.append(r.stdout)
    assert outs[0] == outs[1] == outs[2]
    assert len(outs[0].split()) == 2


# ---------- float ----------

def test_zero_and_negative_zero_differ():
    assert 0.0 == -0.0  # 값 비교로는 같다 -- 지문은 비트(float.hex)로 구분해야 한다
    assert fp_of(0.0) != fp_of(-0.0)
    assert fp_of((0.0,)) != fp_of((-0.0,))


def test_same_float_bits_same_fp():
    # 계약 예 '0.1 + 1e-17' 은 실제로는 0.1 과 1 ulp 다른 float 이다(0.1 의 ulp ~1.39e-17, 반올림 위로).
    # 같은 비트가 되는 식(1e-18, 1/10)으로 같은 성질을 본다.
    a = 0.1
    b = 0.1 + 1e-18
    c = 1.0 / 10.0
    assert a == b == c and a.hex() == b.hex() == c.hex()  # 전제: 같은 float
    assert fp_of(a) == fp_of(c)
    assert fp_of(a) == fp_of(b)


def test_one_ulp_differs():
    a = 0.1
    b = math.nextafter(0.1, 1.0)
    assert a != b
    assert fp_of(a) != fp_of(b)


# ---------- 타입 태그 ----------

def test_bool_int_float_str_distinct():
    assert fp_of(True) != fp_of(1)
    assert fp_of(False) != fp_of(0)
    assert fp_of(1) != fp_of(1.0)
    assert fp_of("1") != fp_of(1)
    assert fp_of(None) != fp_of(0)
    assert fp_of(None) != fp_of("")


def test_tuple_and_list_same_tag():
    assert fp_of((1, 2)) == fp_of([1, 2])
    assert fp_of(((1, "a"), [2.0])) == fp_of([[1, "a"], (2.0,)])


def test_sequence_order_matters():
    assert fp_of((1, 2)) != fp_of((2, 1))
    assert fp_of([1, 2]) != fp_of([2, 1])


def test_dict_insertion_order_irrelevant():
    d1 = {}
    d1["z"] = 1
    d1["a"] = 2
    d1["m"] = (3, 4)
    d2 = {"a": 2, "m": (3, 4), "z": 1}
    assert list(d1) != list(d2)
    assert fp_of(d1) == fp_of(d2)


def test_dict_value_change_differs():
    assert fp_of({"a": 1}) != fp_of({"a": 2})
    assert fp_of({"a": 1}) != fp_of({"b": 1})


def test_any_mapping_same_as_dict():
    d = {"x": 1, "y": (2,)}
    assert fp_of(types.MappingProxyType(d)) == fp_of(d)


def test_set_order_irrelevant_and_differs_from_tuple():
    assert fp_of({1, 2, 3}) == fp_of({3, 2, 1})
    assert fp_of(frozenset({"b", "a"})) == fp_of(frozenset({"a", "b"}))
    assert fp_of({1, 2}) != fp_of((1, 2))
    assert fp_of({1, 2}) != fp_of([1, 2])
    assert fp_of({1, 2}) != fp_of({1, 3})


def test_bytes_and_bytearray_same_tag():
    assert fp_of(b"abc") == fp_of(bytearray(b"abc"))
    assert fp_of(b"abc") != fp_of(b"abd")


def test_none_supported_and_str_utf8():
    assert _is_sha256_hex(fp_of(None))
    assert _is_sha256_hex(fp_of("한글"))
    assert fp_of("한글") != fp_of("한")


# ---------- __canonical__ ----------

class _CanonA:
    def __init__(self, v):
        self.v = v

    def __canonical__(self):
        return ("payload", self.v)


class _CanonB:
    def __init__(self, v):
        self.v = v

    def __canonical__(self):
        return ("payload", self.v)


def test_canonical_same_class_same_value_equal():
    assert fp_of(_CanonA(1)) == fp_of(_CanonA(1))


def test_canonical_different_value_differs():
    assert fp_of(_CanonA(1)) != fp_of(_CanonA(2))


def test_canonical_different_class_same_return_differs():
    assert _CanonA(1).__canonical__() == _CanonB(1).__canonical__()
    assert fp_of(_CanonA(1)) != fp_of(_CanonB(1))


def test_canonical_differs_from_bare_return_value():
    assert fp_of(_CanonA(1)) != fp_of(("payload", 1))


# ---------- dataclass ----------

@dataclasses.dataclass(frozen=True)
class _DcA:
    x: int
    y: str


@dataclasses.dataclass(frozen=True)
class _DcB:
    x: int
    y: str


def test_dataclass_same_fields_equal():
    assert fp_of(_DcA(1, "a")) == fp_of(_DcA(1, "a"))


def test_dataclass_any_field_change_differs():
    assert fp_of(_DcA(1, "a")) != fp_of(_DcA(2, "a"))
    assert fp_of(_DcA(1, "a")) != fp_of(_DcA(1, "b"))


def test_dataclass_class_name_matters():
    assert fp_of(_DcA(1, "a")) != fp_of(_DcB(1, "a"))


# ---------- 자기 구분적 인코딩 ----------

def test_self_delimiting_strings():
    assert fp_of(("ab", "c")) != fp_of(("a", "bc"))
    assert fp_of(("", "abc")) != fp_of(("abc", ""))


def test_self_delimiting_nesting():
    assert fp_of(((1,), 2)) != fp_of((1, (2,)))
    assert fp_of(((),)) != fp_of(())
    assert fp_of({"a": "bc"}) != fp_of({"ab": "c"})


# ---------- 실패 ----------

def _f():
    return 1


class _Plain:
    pass


@pytest.mark.parametrize(
    "bad",
    [object(), _Plain(), _f, lambda: 0, os, _Plain, int, _CanonA],
    ids=["object", "plain_instance", "function", "lambda", "module", "class_obj", "builtin_type", "canon_class_obj"],
)
def test_unsupported_type_rejected(bad):
    with pytest.raises(TypeError):
        fp_of(bad)


@pytest.mark.parametrize(
    "bad",
    [(1, object()), [1, [2, _f]], {"a": _Plain()}, {"k": (1, {"deep": os})}, frozenset({_f})],
    ids=["in_tuple", "in_nested_list", "dict_value", "deep_dict", "in_frozenset"],
)
def test_unsupported_nested_rejected(bad):
    with pytest.raises(TypeError):
        fp_of(bad)
