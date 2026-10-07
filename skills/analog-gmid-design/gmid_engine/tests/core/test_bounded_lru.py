"""CONTRACT §7 BoundedLRU -- 상한 LRU memo: 적중은 compute 미호출·같은 객체, 미적중 1회 호출, 퇴출 계수, 상한 도달 뒤 캐싱 계속."""
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
