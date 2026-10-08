"""CONTRACT §1.1 canonical_key -- fp_of 와 같은 동치 관계(양방향), 항상 hashable, 가변 값은 require_immutable 과 같은 거부 집합.

oracle 종류(test 마다 주석에 다시 적는다):
- (a) 구성으로 정답이 정해진 합성 입력: 쌍둥이(twin) 값은 객체를 새로 만들고 frozenset 삽입 순서·NaN 비트 패턴만 바꿔 만든다 --
  §1 규칙(순서 무관 frozenset, NaN 은 float.hex 가 모두 'nan')으로 fp_of 가 같아야 하므로 canonical_key 도 같아야 한다.
- (§1 참조 의미) 동치의 기준은 §1.1 이 정한 `fp_of` 다(계약 '동치: canonical_key(a) == canonical_key(b) <=> fp_of(a) == fp_of(b)').
  fp_of 는 이번 변경에서 출력이 바뀌지 않는 별개 함수(§0 개정 (3) '한 바이트도 바뀌지 않았다', 기준선은 test_fingerprint 의 (c))이고,
  canonical_key 출력 형태는 계약 밖이라 키 값 자체를 기대값으로 쓰지 않는다.
- 거부 집합의 기준은 §2 require_immutable(계약 §1.1 '실패: require_immutable 이 거부하는 값').
"""
import dataclasses
import math
import os
import random
import struct
import subprocess
import sys
from collections import OrderedDict
from types import MappingProxyType

import pytest

from gmid_engine.core import canonical_key, fp_of, require_immutable


# ---------- 합성 입력 재료 ----------

@dataclasses.dataclass(frozen=True)
class _P:
    x: object
    y: object


@dataclasses.dataclass(frozen=True)
class _Q:
    """_P 와 필드 이름·순서가 같은 다른 클래스(§1 '클래스가 다르면 다른 지문')."""
    x: object
    y: object


@dataclasses.dataclass(frozen=True)
class _R:
    """_P 와 필드 순서만 다른 클래스."""
    y: object
    x: object


class _CanonA:
    def __init__(self, v):
        self._v = v

    def __canonical__(self):
        return self._v


class _CanonB:
    def __init__(self, v):
        self._v = v

    def __canonical__(self):
        return self._v


class _Outer1:
    @dataclasses.dataclass(frozen=True)
    class Inner:
        x: object


class _Outer2:
    @dataclasses.dataclass(frozen=True)
    class Inner:
        """_Outer1.Inner 와 __name__ 은 같고 __qualname__ 만 다르다."""
        x: object


class _MyFloat(float):
    pass


class _MyInt(int):
    pass


class _MyStr(str):
    pass


def _nan_with_payload(bits):
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


_NAN_PLAIN = float("nan")
_NAN_PAYLOAD = _nan_with_payload(0x7FF8000000000123)
_NAN_NEG = -math.nan

_ATOMS = (
    None, True, False, 0, 1, -1, 2, 10 ** 30,
    0.0, -0.0, 1.0, -1.0, 2.0, 0.1, math.nextafter(0.1, 1.0), math.inf, -math.inf, _NAN_PLAIN, _NAN_PAYLOAD, _NAN_NEG,
    "", "1", "a", "ab", "b", "한",
    b"", b"1", b"a", b"ab",
    _MyFloat(1.0), _MyInt(1), _MyStr("a"),
)


def _gen(rng, depth):
    """불변 값 하나. 작은 알파벳이라 서로 다른 생성물 사이에도 같은 값이 자주 나온다(동치 쌍 확보)."""
    if depth <= 0 or rng.random() < 0.35:
        return rng.choice(_ATOMS)
    kind = rng.randrange(7)
    n = rng.randrange(0, 3)
    if kind == 0:
        return tuple(_gen(rng, depth - 1) for _ in range(n))
    if kind == 1:
        return frozenset(_gen_hashable(rng, depth - 1) for _ in range(n))
    if kind == 2:
        return _P(_gen(rng, depth - 1), _gen(rng, depth - 1))
    if kind == 3:
        return _Q(_gen(rng, depth - 1), _gen(rng, depth - 1))
    if kind == 4:
        return _R(_gen(rng, depth - 1), _gen(rng, depth - 1))
    if kind == 5:
        return rng.choice((_CanonA, _CanonB))(_gen(rng, depth - 1))
    return rng.choice((_Outer1.Inner, _Outer2.Inner))(_gen(rng, depth - 1))


def _gen_hashable(rng, depth):
    """frozenset 원소용 -- 파이썬 hash 가 되는 값(__canonical__ 객체는 객체 동일성 hash 라 괜찮다)."""
    return _gen(rng, depth)


def _twin(v):
    """v 와 §1 상 같은 지문이어야 하는 새 객체: 컨테이너는 새로 만들고, frozenset 은 역순 삽입, NaN 은 다른 비트 패턴의 새 객체."""
    if isinstance(v, float) and type(v) is float and math.isnan(v):
        return _nan_with_payload(0x7FF8000000000456)  # 매번 새 NaN 객체(frozenset 안에서 다른 NaN 과 합쳐지지 않게)
    if type(v) is tuple:
        return tuple(_twin(e) for e in v)
    if type(v) is frozenset:
        return frozenset(reversed([_twin(e) for e in v]))
    if dataclasses.is_dataclass(v):
        return type(v)(**{f.name: _twin(getattr(v, f.name)) for f in dataclasses.fields(v)})
    if type(v) in (_CanonA, _CanonB):
        return type(v)(_twin(v.__canonical__()))
    if type(v) is str:
        return "".join(list(v))  # 같은 내용 새 문자열(인터닝 여부와 무관하게 내용 같음)
    if type(v) is bytes:
        return bytes(bytearray(v))
    return v


def _corpus(seed, n):
    rng = random.Random(seed)
    vals = [_gen(rng, 3) for _ in range(n)]
    vals += [_twin(v) for v in vals[: n // 2]]
    return vals


# ---------- (1) 동치 양방향 ----------

@pytest.mark.parametrize("seed", [0, 1, 2, 3])
def test_equivalence_iff_fp_of_property(seed):
    # oracle: 동치의 기준 = §1.1 '<=> fp_of'. 모든 쌍에서 (키 같음) == (지문 같음). 같은 쌍·다른 쌍이 둘 다 충분히 있어야
    # 양방향을 실제로 본 것이다(아래 계수 assert).
    vals = _corpus(seed, 160)
    keys = [canonical_key(v) for v in vals]
    fps = [fp_of(v) for v in vals]
    same = diff = 0
    for i in range(len(vals)):
        for j in range(i + 1, len(vals)):
            k_eq = keys[i] == keys[j]
            f_eq = fps[i] == fps[j]
            assert k_eq == f_eq, (vals[i], vals[j])
            if f_eq:
                same += 1
            else:
                diff += 1
    assert same >= 80
    assert diff >= 1000


@pytest.mark.parametrize("seed", [10, 11])
def test_twins_have_equal_key(seed):
    # oracle (a): _twin 은 §1 규칙(frozenset 순서 무관, NaN 은 모두 'nan', 새 객체)으로 지문이 같도록 만든 값이다.
    rng = random.Random(seed)
    for _ in range(200):
        v = _gen(rng, 4)
        t = _twin(v)
        assert canonical_key(v) == canonical_key(t)
        assert hash(canonical_key(v)) == hash(canonical_key(t))
        assert fp_of(v) == fp_of(t)


@pytest.mark.parametrize("a, b", [
    (0.0, -0.0),
    ((0.0,), (-0.0,)),
    (1, 1.0),
    (1, True),
    (1.0, True),
    (1, "1"),
    (1.0, "1"),
    (True, "1"),
    (0, False),
    (0, None),
    ("", None),
    ("a", b"a"),
    ("", b""),
    ((1, 2), frozenset({1, 2})),
    ((), frozenset()),
    ((1, 2), (2, 1)),
    (_P(1, 2), _Q(1, 2)),
    (_P(1, 2), _R(2, 1)),
    (_P(1, 2), _P(1, 2.0)),
    (_Outer1.Inner(1), _Outer2.Inner(1)),
    (_CanonA(1), _CanonB(1)),
    (_CanonA((1,)), (1,)),
    (("ab", "c"), ("a", "bc")),
    (((1,), 2), (1, (2,))),
    (math.inf, -math.inf),
    (_NAN_PLAIN, math.inf),
    (0.1, math.nextafter(0.1, 1.0)),
], ids=["zero_negzero", "tuple_zero_negzero", "int_float", "int_bool", "float_bool", "int_str", "float_str", "bool_str",
        "zero_false", "zero_none", "empty_str_none", "str_bytes", "empty_str_bytes", "tuple_frozenset",
        "empty_tuple_frozenset", "tuple_order", "dc_other_class", "dc_field_order", "dc_field_value_tag",
        "dc_same_name_other_qualname", "canon_other_class", "canon_vs_bare", "self_delim_str", "self_delim_nest",
        "inf_neginf", "nan_inf", "one_ulp"])
def test_explicit_distinctions(a, b):
    # oracle (a)+§1/§1.1 문장: 각 쌍은 계약이 '다른 지문/다른 키'로 명시한 구분(0.0/-0.0, 1/1.0/True/"1", str/bytes,
    # tuple/frozenset, 클래스가 다른 dataclass, 자기 구분 인코딩, 1 ulp). 파이썬 ==/hash 가 뭉개는 것도 있다(0.0==-0.0, 1==1.0==True).
    assert fp_of(a) != fp_of(b)          # 전제: §1 이 구별
    assert canonical_key(a) != canonical_key(b)


def test_python_equal_values_still_distinct_as_dict_keys():
    # oracle (a): 파이썬 dict 는 0.0/-0.0, 1/1.0/True 를 한 칸으로 합친다. canonical_key 를 키로 쓰면 칸이 나뉘어야 한다(§1.1 목적).
    vals = [0.0, -0.0, 1, 1.0, True, "1", b"1"]
    assert len({v: None for v in vals}) < len(vals)               # 전제: 파이썬 키로는 뭉개짐
    assert len({canonical_key(v): None for v in vals}) == len(vals)


@pytest.mark.parametrize("a, b", [
    (_NAN_PLAIN, _NAN_PAYLOAD),
    (_NAN_PLAIN, _NAN_NEG),
    ((_NAN_PLAIN, 1), (_NAN_PAYLOAD, 1)),
    (frozenset({1, 2, 3}), frozenset([3, 2, 1])),
    (frozenset({"b", "a"}), frozenset(["a", "b"])),
    (_P(1, ("x",)), _P(1, ("x",))),
    (_CanonA(("p", 1.5)), _CanonA(("p", 1.5))),
    (0.1 + 1e-18, 1.0 / 10.0),
], ids=["nan_payload", "nan_sign", "nan_in_tuple", "frozenset_order_int", "frozenset_order_str", "dc_same", "canon_same",
        "same_float_bits"])
def test_explicit_equalities(a, b):
    # oracle (a)+§1/§1.1 문장: 'NaN 은 같은 키(float.hex 가 모두 nan)', 'frozenset 순서 무관', 같은 클래스·같은 필드 값,
    # 같은 비트의 float. NaN 은 파이썬 == 로는 자기 자신과도 다르다.
    assert fp_of(a) == fp_of(b)          # 전제: §1 이 같다고 정함
    assert canonical_key(a) == canonical_key(b)
    assert hash(canonical_key(a)) == hash(canonical_key(b))


def test_same_qualname_distinct_class_objects_follow_fp_of():
    # oracle (§1 참조 의미): §1.1 은 클래스를 (모듈.qualname) 으로 식별한다. 같은 함수를 두 번 불러 만든 두 클래스 객체는
    # 모듈·qualname 이 같다 -> fp_of 와 canonical_key 가 같은 결론을 내야 한다(클래스 객체 동일성으로 키를 나누면 안 됨).
    def make():
        @dataclasses.dataclass(frozen=True)
        class Local:
            x: object
        return Local

    c1, c2 = make(), make()
    assert c1 is not c2 and c1.__qualname__ == c2.__qualname__
    a, b = c1(1), c2(1)
    assert (canonical_key(a) == canonical_key(b)) == (fp_of(a) == fp_of(b))
    assert fp_of(a) == fp_of(b)          # §1 '(모듈.클래스 이름, ...)' -- 이름이 같으면 같은 지문
    assert canonical_key(a) == canonical_key(b)


@pytest.mark.parametrize("sub, base", [
    (_MyFloat(1.5), 1.5),
    (_MyInt(3), 3),
    (_MyStr("ab"), "ab"),
], ids=["float_sub", "int_sub", "str_sub"])
def test_builtin_subclass_same_class_as_fp_of(sub, base):
    # oracle (§1 참조 의미): §2 는 float 하위 클래스를 불변으로 허용한다. 하위 클래스 값의 키 동치는 fp_of 의 결론을 따른다.
    assert (canonical_key(sub) == canonical_key(base)) == (fp_of(sub) == fp_of(base))


# ---------- (2) hashable, 반복 정준화 ----------

@pytest.mark.parametrize("seed", [20, 21])
def test_always_hashable_and_repeatable(seed):
    # oracle (a): §1.1 불변식 (b) '반환값은 항상 hash 가능하고, 같은 값을 여러 번 정준화하면 =='.
    rng = random.Random(seed)
    for _ in range(300):
        v = _gen(rng, 4)
        k1 = canonical_key(v)
        k2 = canonical_key(v)
        hash(k1)
        assert k1 == k2
        assert hash(k1) == hash(k2)
        assert {k1: 1}[k2] == 1


def test_independent_of_pythonhashseed():
    # oracle (a): §1.1 불변식 (c) 'PYTHONHASHSEED 와 무관하게 같은 동치'. 키 값 자체가 아니라 동치 분할(같은 칸 묶음)을 비교한다.
    skill_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from gmid_engine.core import canonical_key\n"
        "vals = [frozenset({'a', 'b', 'c'}), frozenset({'c', 'b', 'a'}), frozenset({'a', 'b'}),\n"
        "        frozenset({('x', 0.0), ('y', -0.0)}), frozenset({('y', -0.0), ('x', 0.0)}), frozenset({('x', -0.0), ('y', 0.0)}),\n"
        "        (1, frozenset({1.0, 'k'})), (1, frozenset({'k', 1.0})), (1, frozenset({'k', True}))]\n"
        "ks = [canonical_key(v) for v in vals]\n"
        "print([[int(ks[i] == ks[j]) for j in range(len(ks))] for i in range(len(ks))])\n"
    ) % skill_dir
    outs = []
    for seed in ("0", "1", "4242"):
        env = dict(os.environ)
        env["PYTHONHASHSEED"] = seed
        r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True)
        outs.append(r.stdout.strip())
    assert outs[0] == outs[1] == outs[2]
    # 구성상 같은 값: 0==1, 3==4, 6==7 / 나머지는 다름(-0.0 위치, 원소 하나 빠짐, 1.0 vs True)
    m = eval(outs[0])  # noqa: S307 -- 자기 subprocess 출력(0/1 행렬)
    assert m[0][1] == 1 and m[3][4] == 1 and m[6][7] == 1
    assert m[0][2] == 0 and m[3][5] == 0 and m[6][8] == 0


# ---------- (3) 거부 집합 = require_immutable ----------

class _Plain:
    pass


@dataclasses.dataclass
class _NotFrozen:
    x: int


@dataclasses.dataclass(frozen=True)
class _FrozenWithList:
    x: object


_MUTABLES = [
    {"a": 1},
    OrderedDict(a=1),
    MappingProxyType({"a": 1}),
    [1, 2],
    [],
    {1, 2},
    set(),
    bytearray(b"x"),
    _Plain(),
    object(),
    _NotFrozen(1),
    (1, [2]),
    (1, (2, {"a": 1})),
    frozenset({(1, _Plain())}),
    _FrozenWithList([1]),
    _P(1, {2}),
    _CanonA([1, 2]),
    _CanonA((1, {"k": 2})),
]
_MUTABLE_IDS = ["dict", "ordered_dict", "mapping_proxy", "list", "empty_list", "set", "empty_set", "bytearray", "plain_obj",
                "object", "dc_not_frozen", "list_in_tuple", "dict_deep", "plain_obj_in_frozenset", "frozen_dc_list_field",
                "frozen_dc_set_field", "canon_returns_list", "canon_returns_dict_deep"]


@pytest.mark.parametrize("value", _MUTABLES, ids=_MUTABLE_IDS)
def test_mutable_rejected_same_as_require_immutable(value):
    # oracle: 거부 기준 = §2 require_immutable(§1.1 '실패: require_immutable 이 거부하는 값 ... TypeError').
    with pytest.raises(TypeError):
        require_immutable(value)         # 전제: §2 가 거부
    with pytest.raises(TypeError):
        canonical_key(value)


def _gen_maybe_mutable(rng, depth):
    if depth <= 0 or rng.random() < 0.3:
        return rng.choice(_ATOMS + (_Plain(), bytearray(b"z")))
    kind = rng.randrange(6)
    items = [_gen_maybe_mutable(rng, depth - 1) for _ in range(rng.randrange(0, 3))]
    if kind == 0:
        return tuple(items)
    if kind == 1:
        return list(items)
    if kind == 2:
        return _P(items[0] if items else None, tuple(items))
    if kind == 3:
        return _CanonA(tuple(items))
    if kind == 4:
        return {"k%d" % i: x for i, x in enumerate(items)}
    try:
        return frozenset(items)
    except TypeError:                    # 원소가 unhashable(list·dict) 이면 frozenset 을 못 만든다 -> tuple 로
        return tuple(items)


@pytest.mark.parametrize("seed", [30, 31, 32])
def test_rejection_set_equals_require_immutable_property(seed):
    # oracle: §1.1 '실패' = §2 거부 집합. 무작위 중첩(가변이 어느 깊이에든 섞임)에서 두 함수의 거부 여부가 같아야 한다.
    rng = random.Random(seed)
    rejected = accepted = 0
    for _ in range(400):
        v = _gen_maybe_mutable(rng, 3)
        try:
            require_immutable(v)
            imm = True
        except TypeError:
            imm = False
        try:
            k = canonical_key(v)
            ck = True
        except TypeError:
            ck = False
        assert imm == ck, v
        if ck:
            hash(k)
            accepted += 1
        else:
            rejected += 1
    assert rejected >= 50 and accepted >= 50
