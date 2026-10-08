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


# =====================================================================================================================
# 2026-10-08 개정(core 성능 5 '정확 타입 경로', CONTRACT §0 개정 (3) 'fp_of 출력(영속 지문)은 한 바이트도 바뀌지 않았다').
# oracle 종류:
# - (c) 기준선: 변경 전 엔진 6a3351a(ng-perf-core 의 부모)에서 _golden_values() 의 fp_of 출력을 구해 _BASE_FP 에 적었다
#   (6a3351a 를 git archive 로 푼 트리를 sys.path 앞에 두고 이 파일의 _golden_values() 를 실행 -- 새 구현은 쓰지 않음).
#   동작 보존 변경이라 바이트까지 같아야 한다.
# - (a)+§1 규칙: 정확한 내장 타입(빠른 경로)과 하위 클래스·다른 Mapping·list·bytearray·set(일반 경로)이 §1 상 같은 태그이면
#   같은 지문. 하위 클래스 동치는 §1 이 명시하지 않아 (c) 기준선(6a3351a 에서 같은 지문, 계약 결함으로 보고)과 §2 '하위 클래스
#   허용'에 근거한다.
# =====================================================================================================================

import collections  # noqa: E402
import enum  # noqa: E402

from gmid_engine.core import FailureRecord, FieldValue, GraphRecord  # noqa: E402


class _SubFloat(float):
    pass


class _SubInt(int):
    pass


class _SubStr(str):
    pass


class _SubBytes(bytes):
    pass


class _SubTuple(tuple):
    pass


class _SubFrozenset(frozenset):
    pass


class _IntE(enum.IntEnum):
    ONE = 1


_NT = collections.namedtuple("_NT", "a b")


class _UserMapping(collections.abc.Mapping):
    def __init__(self, d):
        self._d = dict(d)

    def __getitem__(self, k):
        return self._d[k]

    def __iter__(self):
        return iter(self._d)

    def __len__(self):
        return len(self._d)


@pytest.mark.parametrize("sub, exact", [
    (_SubFloat(1.5), 1.5),
    (_SubFloat(-0.0), -0.0),
    (_SubInt(3), 3),
    (_SubInt(-(10 ** 30)), -(10 ** 30)),
    (_SubStr("한글"), "한글"),
    (_SubBytes(b"\x00x"), b"\x00x"),
    (_SubTuple((1, "a")), (1, "a")),
    (_SubFrozenset({1, 2}), frozenset({1, 2})),
    (_NT(1, 2.0), (1, 2.0)),
    (_IntE.ONE, 1),
], ids=["float", "float_negzero", "int", "bigint", "str", "bytes", "tuple", "frozenset", "namedtuple", "intenum"])
def test_builtin_subclass_same_fp_as_exact_type(sub, exact):
    # oracle (c)(6a3351a 에서 같음) + §2(하위 클래스 허용): 빠른 경로(정확 타입)와 일반 경로(하위 클래스)가 같은 바이트.
    assert fp_of(sub) == fp_of(exact)
    assert fp_of((sub, "tail")) == fp_of((exact, "tail"))


def test_bool_not_routed_as_int_or_subclass():
    # oracle §1 'bool 과 int 는 다른 태그': bool 은 int 하위 클래스지만 별도 태그 -- int 하위 클래스와도 다르다.
    assert fp_of(True) != fp_of(_SubInt(1))
    assert fp_of(False) != fp_of(_SubInt(0))
    assert fp_of((True,)) != fp_of((_IntE.ONE,))


def test_general_path_containers_match_exact_types_nested():
    # oracle (a)+§1: tuple≡list, bytes≡bytearray, 모든 Mapping 은 dict 처럼 키 정렬, set≡frozenset. 깊게 섞어도 같다.
    exact = {"a": (1, b"x", frozenset({2.5, "s"})), "b": {"c": (None, -0.0)}}
    general = collections.OrderedDict([
        ("b", _UserMapping({"c": [None, -0.0]})),
        ("a", [1, bytearray(b"x"), {"s", 2.5}]),
    ])
    proxied = types.MappingProxyType({"b": types.MappingProxyType({"c": _SubTuple((None, _SubFloat(-0.0)))}),
                                      "a": _SubTuple((_SubInt(1), _SubBytes(b"x"), _SubFrozenset({_SubStr("s"), 2.5})))})
    assert fp_of(general) == fp_of(exact)
    assert fp_of(proxied) == fp_of(exact)


def _read_fp(record):
    _ = record.fp
    return record


def _golden_values():
    """기준선(c) 대상 -- 이름 -> 값. §1 의 모든 태그와 빠른/일반 경로를 덮는다."""
    import struct as _struct
    return {
        "none": None, "true": True, "false": False, "zero": 0, "neg": -7, "big": 2 ** 100, "negbig": -(3 ** 70),
        "f0": 0.0, "fneg0": -0.0, "f": 0.1, "fulp": math.nextafter(0.1, 1.0), "inf": math.inf, "ninf": -math.inf,
        "nan": float("nan"), "nanpay": _struct.unpack("<d", _struct.pack("<Q", 0x7FF8000000000123))[0],
        "tiny": 5e-324, "s0": "", "s": "abc", "su": "한글\x00", "b0": b"", "b": b"\x00\xff", "ba": bytearray(b"\x01"),
        "t0": (), "t": (1, 1.0, True, "1", b"1", None), "l": [1, [2, (3,)]], "fs0": frozenset(), "fs": frozenset({1, "a", 2.5}),
        "set": {3, 1, 2}, "d0": {}, "d": {"z": 1, "a": (2, {"m": -0.0})}, "dnum": {1: "a", 2: "b"},
        "proxy": types.MappingProxyType({"k": 1}), "od": collections.OrderedDict([("b", 1), ("a", 2)]),
        # dataclass 경로는 모듈 이름이 test 수집 방식과 무관한 core 공개 dataclass 로 본다(이 파일의 _DcA 는 pytest import 방식에
        # 따라 모듈 이름이 달라 기준선에 쓰지 않는다). GraphRecord 는 지연 보관 fp 필드까지 fp_of 에 들어간다.
        "fv": FieldValue(1.5, "w", "v1"), "fv2": FieldValue((0.0, -0.0), "w", "v2", 3),
        "rec": GraphRecord("node", "n", [("b", FieldValue("x", "w", "v")), ("a", FieldValue(1, "w", "v"))]),
        "rec_read": _read_fp(GraphRecord("node", "n", [("b", FieldValue("x", "w", "v")), ("a", FieldValue(1, "w", "v"))])),
        "frec": FailureRecord("SEARCH_FAILED", devices=("m2", "m1"), margin=1, detail={"b": 1, "a": (2,)}),
        "nest": ((1,), 2, ((("x",),),)), "subs": (_SubFloat(1.5), _SubInt(3), _SubStr("q"), _NT(1, 2), _IntE.ONE),
    }


_BASE_FP = {
    # 생성: 6a3351a 엔진(변경 전)으로 _golden_values() 의 fp_of -- 아래 값은 그 출력(oracle (c)).
    "none": "36a8ba4c0e098d79d32cb016121aadab24d203c442a29b01a37a18ce12232c6d",
    "true": "86adf9311985772634198158f3acfe079d5cd46900a5245440e9913b805d9e14",
    "false": "dab63bb128f667c42693bccd121c5a6c99cfda4204eb9e05de70b4d48352c331",
    "zero": "bc9e34c1df51acf2c849b487f237da6bfc0b9914d76cdb023dcd0161c55ed440",
    "neg": "323bdecfc9793497dcd304f58cab7bc197911a15a7305bfd0a2e4e61e4b7db14",
    "big": "c8e64afb9644d5ce4a9d29bb4b5dd8964cbb5c7f38472d252f1ec48d8d89ebdc",
    "negbig": "aa4d4ddd52cd567627890f6cdeace89515e127ab2db76ba40fdf7e198e04711f",
    "f0": "397507edd963e25f2e23fe4600679a5f71ecd072957241c1abd388fffedc0380",
    "fneg0": "c878a8afae9cbcb9a59893cd28de77abc204965a0296dd37c7d6b563d10843d7",
    "f": "81eeddb49dea2520d22251f22ba27b67447544cc9c66e847e96b49b73c16a7c8",
    "fulp": "484f47e995c2bc43f57d68ac7c3f05deafe556a78da54a67b840961bc68c8107",
    "inf": "c5dd47d673083476f17da39a3e7de980f5b9ec9dd476b49ccb44274d83d7c99a",
    "ninf": "18a39b1f8b79306d27a2c80cd6f62d42346e41cfe5b633fc6a1aa0312e75a152",
    "nan": "13bc92c22a4a8d1685447d12b5125d1bf8f55d6a369bdd7ba703f779362c09b8",
    "nanpay": "13bc92c22a4a8d1685447d12b5125d1bf8f55d6a369bdd7ba703f779362c09b8",
    "tiny": "12a6db3806e6a47fae17a5ec62aca7328f15bf3ccc8a1d7bff85f450669bda45",
    "s0": "ddb96cc8b84783be42425ddae4eeab1e528dd7cd18fd7ccc9eba246f76ecbf84",
    "s": "0014f47c7171c56b4842f65a8c9fef60d84c703a2698c8353d84daae3197bc84",
    "su": "01940b5b1da2c0d9dbe0e379057baf37697694f4af9dde10db8821999ade776d",
    "b0": "8af4b006cb08aeb5545f959c9af4b8d1636e219203a0b2e4e01195896a3b8910",
    "b": "8a43ed0040754492af6f5adc18421ac58936c5be91ae65c933edc40cf06b9762",
    "ba": "6c696a64a1c7ae467f75cde81c0c8cd4b8b79b5aa121132d4eadbda71512b178",
    "t0": "cbe8f1e75e355108b9d490d167749b94f622a6337e5e4f2e921a5ff58ce4bf24",
    "t": "af61d84404ba5bf971fc0a3eca4f63f6c619071d7faa6e6d33474f913e1ace23",
    "l": "5f7fdc1aa3f2d9d28f775727d6642e15d0663d29f1a31de7063f03a88fe2eaae",
    "fs0": "3bd747a89ea3d9de6ec8b4658b464fab66bc71a467389facadd772d3b0af5bdf",
    "fs": "c84f1d2976aa16d60d513c0d404cb060d833447741f9dbd993e1d7dfe61740f2",
    "set": "5befd9225320baf7867f9d637f0bb70a64b4ac099ad0db2f1893b4b1c36f04a6",
    "d0": "7c067c1cf48862a412110fabc351b8ecffd7c53f1cc7a49ebe48324a204586ac",
    "d": "f266c7e73609ad14d3e4d33b7a85bf5c26c31a755ef7669eb705e8914f4a2f7c",
    "dnum": "66a6b927bfcdc82cf134efbc88518d76e3d45783713867cd5794e673b6dec886",
    "proxy": "12ae96401039567a146749910452b653a58ebcbc7175706d4f9609eb9ee06268",
    "od": "263df1eb9e644203f5b48a512f1981fe8bf1453513ff42d56b22c9f8dbf304e8",
    "fv": "b759ff1f8d1fc6f51cd4540397bbc628cda7891a7dd221039c7e0c2041d6af5e",
    "fv2": "cca31e3763a90c57585923bcc7721f2e4ce70494e5c43512d3412ddc3a7670fd",
    "rec": "55388d91ae4a91e6d86f1b31de93d3c1653138cc0cf2b1c63e99531fd91b5079",
    "rec_read": "55388d91ae4a91e6d86f1b31de93d3c1653138cc0cf2b1c63e99531fd91b5079",
    "frec": "939c40c09c76cd81e9ed2495220ab55f0815f8175009dee95ea6c7a9d901bfbc",
    "nest": "31cbfc43f6323e2a28021c036c60cc0238a5a87daca4588913ed757cbf1e6586",
    "subs": "7e11d67c0afd37314f2082e229400360d3e2e8714240ec9e94265ddb65549d6b",
}


def test_fp_of_bytes_unchanged_from_pre_change_baseline():
    # oracle (c): §0 개정 (3) 'fp_of 출력(영속 지문)은 한 바이트도 바뀌지 않았다' -- 변경 전 엔진 출력과 같아야 한다.
    vals = _golden_values()
    assert set(vals) == set(_BASE_FP)
    for name, v in vals.items():
        assert fp_of(v) == _BASE_FP[name], name
