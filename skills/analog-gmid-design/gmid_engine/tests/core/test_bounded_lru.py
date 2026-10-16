"""CONTRACT §7 BoundedLRU -- 상한 LRU memo: 적중은 compute 미호출·같은 객체, 미적중 1회 호출, 퇴출 계수, 상한 도달 뒤 캐싱 계속."""
import dataclasses
import math
import struct

import pytest

from gmid_engine.core import BoundedLRU, LruStats


class _Counter:
    """키별 compute 호출 횟수를 센다. 반환값은 매 호출 새 객체(적중이 같은 객체를 돌려주는지 보려고)."""

    def __init__(self):
        self.calls = {}

    def for_key(self, key):
        def compute():
            self.calls[key] = self.calls.get(key, 0) + 1
            return ["value", key, self.calls[key]]
        return compute

    def total(self):
        return sum(self.calls.values())


# ---------- capacity ----------

@pytest.mark.parametrize("cap", [0, -1, 1.0, 2.5, True, False, "2", None])
def test_bad_capacity_rejected(cap):
    with pytest.raises(ValueError):
        BoundedLRU(cap)


def test_capacity_one_ok():
    lru = BoundedLRU(1)
    assert lru.stats().capacity == 1
    assert len(lru) == 0


# ---------- 계약 예 ----------

def test_contract_example_trace():
    # capacity 2, 키 1,2,1,3,2,2 손계산:
    # 1 miss [1] / 2 miss [1,2] / 1 hit [2,1] / 3 miss 퇴출 2 -> [1,3] / 2 miss(퇴출됐던 키) 퇴출 1 -> [3,2] / 2 hit
    lru = BoundedLRU(2)
    c = _Counter()
    for k in (1, 2, 1, 3, 2, 2):
        lru.lookup(k, c.for_key(k))
    st = lru.stats()
    assert isinstance(st, LruStats)
    assert st.hits == 2
    assert st.misses == 4
    assert st.evictions == 2
    assert st.recomputes_after_eviction == 1
    assert st.size == 2
    assert st.capacity == 2
    assert len(lru) == 2
    assert c.calls == {1: 1, 2: 2, 3: 1}
    assert st.hits + st.misses == 6


def test_contract_example_final_contents():
    # 위 순서 끝 상태 [3, 2]: 3·2 는 적중, 1 은 미적중
    lru = BoundedLRU(2)
    c = _Counter()
    for k in (1, 2, 1, 3, 2, 2):
        lru.lookup(k, c.for_key(k))
    before = c.total()
    lru.lookup(3, c.for_key(3))
    lru.lookup(2, c.for_key(2))
    assert c.total() == before
    lru.lookup(1, c.for_key(1))
    assert c.total() == before + 1
    assert lru.stats().recomputes_after_eviction == 2


# ---------- 적중 / 미적중 ----------

def test_hit_returns_same_object_without_compute():
    lru = BoundedLRU(4)
    c = _Counter()
    v1 = lru.lookup(("a", 1), c.for_key("a"))
    v2 = lru.lookup(("a", 1), c.for_key("a"))
    assert v2 is v1
    assert c.calls == {"a": 1}
    st = lru.stats()
    assert (st.hits, st.misses, st.evictions) == (1, 1, 0)


def test_miss_calls_compute_once_and_returns_result():
    lru = BoundedLRU(3)
    sentinel = ("result",)
    calls = []

    def compute():
        calls.append(1)
        return sentinel

    assert lru.lookup("k", compute) is sentinel
    assert calls == [1]


def test_no_eviction_means_one_compute_per_key():
    lru = BoundedLRU(10)
    c = _Counter()
    keys = ["a", "b", "c", "a", "b", "c", "a", "a", "c"]
    for k in keys:
        lru.lookup(k, c.for_key(k))
    assert c.calls == {"a": 1, "b": 1, "c": 1}
    st = lru.stats()
    assert (st.hits, st.misses, st.evictions, st.recomputes_after_eviction, st.size) == (6, 3, 0, 0, 3)


def test_hit_refreshes_recency():
    # capacity 2: a, b, a(적중 -> a 최근), c -> 퇴출은 b 여야 한다
    lru = BoundedLRU(2)
    c = _Counter()
    for k in ("a", "b", "a", "c"):
        lru.lookup(k, c.for_key(k))
    n = c.total()
    lru.lookup("a", c.for_key("a"))
    assert c.total() == n  # a 는 남아 있다
    lru.lookup("b", c.for_key("b"))
    assert c.calls["b"] == 2  # b 가 퇴출됐었다


def test_caching_continues_after_capacity_reached():
    lru = BoundedLRU(2)
    c = _Counter()
    for k in range(10):
        lru.lookup(k, c.for_key(k))
        assert len(lru) <= 2
        # 방금 넣은 키는 바로 다시 적중해야 한다(상한 도달 뒤에도 저장)
        lru.lookup(k, c.for_key(k))
        assert c.calls[k] == 1
    st = lru.stats()
    assert st.misses == 10 and st.hits == 10 and st.evictions == 8 and st.size == 2


# ---------- 키 동일성 = fp_of ----------

def test_zero_and_negative_zero_are_different_keys():
    lru = BoundedLRU(4)
    c = _Counter()
    lru.lookup((0.0,), c.for_key("pos"))
    lru.lookup((-0.0,), c.for_key("neg"))
    assert c.calls == {"pos": 1, "neg": 1}
    assert lru.stats().misses == 2


def test_int_and_bool_are_different_keys():
    lru = BoundedLRU(4)
    c = _Counter()
    lru.lookup((1,), c.for_key("int"))
    lru.lookup((True,), c.for_key("bool"))
    assert c.calls == {"int": 1, "bool": 1}


def test_equal_content_different_objects_hit():
    lru = BoundedLRU(4)
    c = _Counter()
    lru.lookup(frozenset({"x", "y"}), c.for_key("s"))
    lru.lookup(frozenset({"y", "x"}), c.for_key("s"))
    lru.lookup(("a", (1, 2.0)), c.for_key("t"))
    lru.lookup(("a", (1, 2.0)), c.for_key("t"))
    assert c.calls == {"s": 1, "t": 1}
    assert lru.stats().hits == 2


@pytest.mark.parametrize("key", [[1, 2], {"a": 1}, {1}, (1, [2]), bytearray(b"x")],
                         ids=["list", "dict", "set", "list_in_tuple", "bytearray"])
def test_mutable_key_rejected_without_compute(key):
    lru = BoundedLRU(2)
    calls = []
    with pytest.raises(TypeError):
        lru.lookup(key, lambda: calls.append(1))
    assert calls == []
    st = lru.stats()
    assert (st.hits, st.misses, st.size) == (0, 0, 0)
    assert len(lru) == 0


# ---------- compute 예외 ----------

def test_compute_exception_not_stored_and_propagates():
    lru = BoundedLRU(2)

    class Boom(Exception):
        pass

    def bad():
        raise Boom("x")

    with pytest.raises(Boom):
        lru.lookup("k", bad)
    st = lru.stats()
    assert st.misses == 1 and st.size == 0 and len(lru) == 0
    # 저장되지 않았으므로 다음 조회는 다시 compute
    calls = []
    lru.lookup("k", lambda: calls.append(1) or "ok")
    assert calls == [1]
    assert lru.stats().misses == 2


# =====================================================================================================================
# 2026-10-08 개정(core 성능 2: memo 키 = canonical_key, CONTRACT §7·§1.1) -- 키 구분·계수가 fp_of 동치 그대로인지.
# oracle 종류: (a) 구성으로 정답이 정해진 합성 키 + §7 문장(구분 목록·계약 예 1,2,1,3,2,2 손계산). 기대 계수는 §7 의 예를
# 손으로 따라간 값이고 피검 함수로 만들지 않는다.
# =====================================================================================================================

@dataclasses.dataclass(frozen=True)
class _KA:
    x: object


@dataclasses.dataclass(frozen=True)
class _KB:
    x: object


@dataclasses.dataclass
class _KMut:
    x: object


class _KPlain:
    pass


def test_one_float_bool_str_tuple_keys_all_distinct():
    # oracle (a)+§7 '(1,) 와 (1.0,) 와 (True,) 는 서로 다른 키': 파이썬 == 로는 셋이 같다(전제 assert). ("1",) 도 다른 태그(§1).
    assert (1,) == (1.0,) == (True,)
    lru = BoundedLRU(8)
    c = _Counter()
    keys = [(1,), (1.0,), (True,), ("1",), (b"1",)]
    for i, k in enumerate(keys):
        lru.lookup(k, c.for_key(i))
    assert c.calls == {0: 1, 1: 1, 2: 1, 3: 1, 4: 1}
    st = lru.stats()
    assert (st.hits, st.misses, st.size) == (0, 5, 5)
    # 다시 같은 순서로 -> 모두 적중, compute 추가 호출 0
    for i, k in enumerate(keys):
        lru.lookup(k, c.for_key(i))
    assert c.total() == 5
    assert lru.stats().hits == 5


def test_zero_negzero_both_stored_and_hit_separately():
    # oracle (a)+§7 '(0.0,) 와 (-0.0,) 는 다른 키': 각자 저장된 값(is)을 각자 돌려준다.
    lru = BoundedLRU(4)
    c = _Counter()
    vp = lru.lookup((0.0,), c.for_key("pos"))
    vn = lru.lookup((-0.0,), c.for_key("neg"))
    assert vp is not vn
    assert lru.lookup((0.0,), c.for_key("pos")) is vp
    assert lru.lookup((-0.0,), c.for_key("neg")) is vn
    assert c.calls == {"pos": 1, "neg": 1}
    st = lru.stats()
    assert (st.hits, st.misses, st.evictions) == (2, 2, 0)


def test_nan_keys_hit():
    # oracle (a)+§7 'NaN 을 담은 같은 내용 키는 적중'(§1.1: 모든 NaN 은 같은 키). 다른 NaN 객체·부호·비트라도 적중.
    nan_other = struct.unpack("<d", struct.pack("<Q", 0x7FF8000000000777))[0]
    lru = BoundedLRU(4)
    c = _Counter()
    v = lru.lookup(("x", float("nan")), c.for_key("n"))
    assert lru.lookup(("x", nan_other), c.for_key("n")) is v
    assert lru.lookup(("x", -math.nan), c.for_key("n")) is v
    assert c.calls == {"n": 1}
    assert lru.stats().hits == 2


@pytest.mark.parametrize("ka, kb", [
    ("a", b"a"),
    ((1, 2), frozenset({1, 2})),
    (_KA(1), _KB(1)),
    (_KA(1), _KA(1.0)),
    (("ab", "c"), ("a", "bc")),
], ids=["str_bytes", "tuple_frozenset", "dc_class", "dc_field_tag", "self_delimiting"])
def test_contract_distinctions_are_distinct_keys(ka, kb):
    # oracle (a)+§1.1 구분 목록(str/bytes, tuple/frozenset, 다른 dataclass 클래스) + §1 자기 구분 인코딩.
    lru = BoundedLRU(4)
    c = _Counter()
    lru.lookup(ka, c.for_key("a"))
    lru.lookup(kb, c.for_key("b"))
    assert c.calls == {"a": 1, "b": 1}
    assert lru.stats().misses == 2


def test_contract_example_trace_with_tag_sensitive_keys():
    # oracle (a)+§7 계약 예(capacity 2, 1,2,1,3,2,2 -> hits 2, misses 4, evictions 2, recomputes_after_eviction 1, size 2) 를
    # 파이썬 == 로는 같지만 §1.1 로는 다른 키 세 개로 다시 한다: 1 -> (0.0,), 2 -> (-0.0,), 3 -> (False,).
    # 키 구분이 뭉개지면(0.0 == -0.0 == False) 계수가 바뀐다(예: 1·2 가 한 키 -> hits 4).
    k1, k2, k3 = (0.0,), (-0.0,), (False,)
    assert k1 == k2 == k3                # 전제: 파이썬 == 로는 같다
    lru = BoundedLRU(2)
    c = _Counter()
    for name, k in (("1", k1), ("2", k2), ("1", k1), ("3", k3), ("2", k2), ("2", k2)):
        lru.lookup(k, c.for_key(name))
    st = lru.stats()
    assert (st.hits, st.misses, st.evictions, st.recomputes_after_eviction, st.size) == (2, 4, 2, 1, 2)
    assert c.calls == {"1": 1, "2": 2, "3": 1}


@pytest.mark.parametrize("key", [_KMut(1), _KPlain(), (1, (2, {"a": 1})), _KA([1]), frozenset({(1, _KPlain())}),
                                 (_KA(1), [2])],
                         ids=["dc_not_frozen", "plain_obj", "dict_deep", "frozen_dc_list_field", "plain_in_frozenset",
                              "list_after_dc"])
def test_more_mutable_keys_rejected_without_compute(key):
    # 거부(§7 '가변 -> TypeError, compute 미호출', §1.1 '실패' = §2 거부 집합). 계수 불변.
    lru = BoundedLRU(2)
    lru.lookup("seed", lambda: "s")
    before = lru.stats()
    calls = []
    with pytest.raises(TypeError):
        lru.lookup(key, lambda: calls.append(1))
    assert calls == []
    assert lru.stats() == before
    assert len(lru) == 1


# =====================================================================================================================
# [XRUN-F1 card A] `BoundedLRU.adopt(key, value)` -- interface card xrunf1a C3b: 원 key 를 받아 lookup 과 같은 canonical_key 로 넣는다,
# 그 뒤 같은 원 key 의 lookup 은 적중(compute 미호출), adopt 는 hits·misses 를 바꾸지 않는다, 상한을 넘으면 lookup 과 같은 규칙으로 가장
# 오래된 것을 퇴출해 evictions 에 세고 퇴출 키를 기록한다(그 키를 lookup 으로 다시 계산하면 recomputes_after_eviction).
# oracle (손): 넣는 순서·상한은 이 test 가 정하고 계수를 손으로 센다. 이름은 test_bounded_lru_adopt_…(CanonPointer.adopt 와 구분).
# =====================================================================================================================

def test_bounded_lru_adopt_then_lookup_hits_without_compute():
    lru = BoundedLRU(3)
    c = _Counter()
    v = ["adopted"]
    lru.adopt(("k", 1.0), v)
    st = lru.stats()
    assert (st.hits, st.misses, st.size, st.evictions) == (0, 0, 1, 0)        # adopt 는 hits·misses 불변
    assert lru.lookup(("k", 1.0), c.for_key("k")) is v
    assert c.total() == 0
    st = lru.stats()
    assert (st.hits, st.misses) == (1, 0)


def test_bounded_lru_adopt_canonical_equivalent_key_hits():
    """같은 내용 NaN(다른 비트) 키로 넣고 부르면 적중 -- adopt 도 lookup 과 같은 canonical_key 를 쓴다."""
    nan_other = struct.unpack("<d", struct.pack("<Q", 0x7FF8000000000777))[0]
    lru = BoundedLRU(2)
    c = _Counter()
    v = ("nan-value",)
    lru.adopt(("x", float("nan")), v)
    assert lru.lookup(("x", nan_other), c.for_key("n")) is v
    assert c.total() == 0


def test_bounded_lru_adopt_keeps_tag_distinctions():
    """adopt 로 (0.0,) 를 넣어도 (-0.0,)·(False,) 는 다른 키 -- 그 조회는 compute 한다(키 구분이 lookup 과 같다)."""
    lru = BoundedLRU(4)
    c = _Counter()
    lru.adopt((0.0,), "pos")
    lru.lookup((-0.0,), c.for_key("neg"))
    lru.lookup((False,), c.for_key("false"))
    assert c.calls == {"neg": 1, "false": 1}
    assert lru.lookup((0.0,), c.for_key("pos")) == "pos" and "pos" not in c.calls


def test_bounded_lru_adopt_over_capacity_evicts_oldest_and_records():
    """capacity 2 에 a, b, c 를 차례로 adopt -> a 퇴출(evictions 1), size 2, hits·misses 0. b·c 는 적중, a 는 lookup 으로 다시 계산되고
    recomputes_after_eviction 1(퇴출 기록)."""
    lru = BoundedLRU(2)
    c = _Counter()
    for k in ("a", "b", "c"):
        lru.adopt(k, "adopted-" + k)
    st = lru.stats()
    assert (st.hits, st.misses, st.evictions, st.size, st.recomputes_after_eviction) == (0, 0, 1, 2, 0)
    assert lru.lookup("c", c.for_key("c")) == "adopted-c"
    assert lru.lookup("b", c.for_key("b")) == "adopted-b"
    assert c.total() == 0
    lru.lookup("a", c.for_key("a"))
    assert c.calls == {"a": 1}
    st = lru.stats()
    assert (st.hits, st.misses, st.recomputes_after_eviction) == (2, 1, 1)
    assert st.evictions == 2                                     # a 를 다시 넣으며 가장 오래 접근하지 않은 c 퇴출(b 는 방금 적중)
