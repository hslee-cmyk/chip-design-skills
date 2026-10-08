"""CONTRACT §6 @compute_block -- 선언 검사, 입력 버전 같으면 함수 미호출(호출 계수로 확인: '같은 값 반복 계산 금지'),
선언 밖 열 KeyError, 결과 키 불일치 ValueError, 권한 위반, 계수 불변식과 recomputes_same_input."""
import dataclasses
import string

import pytest

from gmid_engine.core import (
    BlockStats,
    ComputeBlock,
    GraphSnapshot,
    Projection,
    WriterPermissionError,
    WriterTable,
    compute_block,
    fp_of,
)

TABLE = WriterTable([
    ("node", "v", "bias"),        # 입력 열(외부 writer)
    ("node", "u", "other"),       # 선언 밖 열
    ("device", "w", "sizer"),     # 블록 출력 열
    ("device", "gm", "sizer"),    # 블록 출력 열 2
])

READS = (("node", "v"),)
WRITES = (("device", "w"),)


def _base(v=None, u=None):
    s = GraphSnapshot.empty(TABLE)
    s = s.write("bias", "in1", {("node", "v"): v if v is not None else {"a": 1.0, "b": 2.0}})
    if u is not None:
        s = s.write("other", "o1", {("node", "u"): u})
    return s


def _make_block(log, name="sizer", reads=READS, writes=WRITES):
    """호출마다 log 에 (projection 열, extras) 를 남기는 블록. w[m_<key>] = 2 * v[key] + sum(extras 숫자)."""

    @compute_block(name, reads=reads, writes=writes)
    def block(projection):
        col = projection.column("node", "v")
        log.append((col, projection.extras))
        bump = sum(x for x in projection.extras if isinstance(x, (int, float)))
        return {("device", "w"): {"m_" + k: 2.0 * val + bump for k, val in col}}

    return block


def _assert_invariant(st):
    assert st.calls == st.reuses + st.computes


# ---------- 선언 ----------

def test_decorator_returns_compute_block():
    def fn(p):
        return {}

    b = compute_block("sizer", reads=[("node", "v")], writes=[("device", "gm"), ("device", "w")])(fn)
    assert isinstance(b, ComputeBlock)
    assert b.name == "sizer"
    assert b.fn is fn
    assert b.writes == (("device", "gm"), ("device", "w"))
    assert type(b.writes) is tuple
    assert set(b.reads) == {("node", "v")}
    assert isinstance(b.code_hash, str) and len(b.code_hash) == 64
    assert set(b.code_hash) <= set(string.hexdigits.lower())


def test_writes_keep_declaration_order():
    b = compute_block("sizer", writes=[("device", "w"), ("device", "gm")])(lambda p: {})
    assert b.writes == (("device", "w"), ("device", "gm"))


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(name="", writes=WRITES),
        dict(name=3, writes=WRITES),
        dict(name=None, writes=WRITES),
        dict(name="sizer", writes=()),
        dict(name="sizer", writes=[("vertex", "w")]),
        dict(name="sizer", reads=[("vertex", "v")], writes=WRITES),
        dict(name="sizer", writes=[("device", "")]),
        dict(name="sizer", writes=[("device", 1)]),
        dict(name="sizer", reads=[("node", "")], writes=WRITES),
        dict(name="sizer", writes=[("device", "w"), ("device", "w")]),
        dict(name="sizer", reads=[("node", "v"), ("node", "v")], writes=WRITES),
        dict(name="sizer", writes=["dw"]),
        dict(name="sizer", reads=["nv"], writes=WRITES),
        dict(name="sizer", writes=[("device", "w", "x")]),
        dict(name="sizer", writes=[("device",)]),
    ],
    ids=["name_empty", "name_int", "name_none", "writes_empty", "writes_kind_bad", "reads_kind_bad",
         "field_empty", "field_int", "reads_field_empty", "writes_dup", "reads_dup", "writes_pair_str2",
         "reads_pair_str2", "pair_len3", "pair_len1"],
)
def test_bad_declaration_value_error(kwargs):
    name = kwargs.pop("name")
    with pytest.raises(ValueError):
        compute_block(name, **kwargs)(lambda p: {})


# ---------- 계산과 기록 ----------

def test_compute_writes_result_with_meta():
    log = []
    block = _make_block(log)
    s0 = _base()
    s1 = block(s0)
    assert len(log) == 1
    assert s1 is not s0
    assert s1.column("device", "w") == (("m_a", 2.0), ("m_b", 4.0))
    v = fp_of((block.name, block.code_hash, Projection.from_snapshot(s0, READS).fp))
    for key in ("m_a", "m_b"):
        fv = s1.field("device", key, "w")
        assert fv.writer == "sizer"
        assert fv.input_version == v
    assert s1.block_version("sizer") == v
    # 원본 불변
    assert s0.column("device", "w") == ()
    assert s0.block_version("sizer") is None


def test_projection_matches_snapshot_column_and_extras():
    log = []
    block = _make_block(log)
    s0 = _base(v={"x": 3.0, "a": 0.5})
    block(s0, 7, "tag")
    col, extras = log[0]
    assert col == s0.column("node", "v") == (("a", 0.5), ("x", 3.0))
    assert extras == (7, "tag")


# ---------- 재사용: 같은 입력 버전이면 함수 미호출 ----------

def test_second_call_same_snapshot_is_reuse_without_call():
    log = []
    block = _make_block(log)
    s1 = block(_base())
    s2 = block(s1)
    assert s2 is s1
    assert len(log) == 1
    st = block.stats()
    assert isinstance(st, BlockStats)
    assert (st.name, st.calls, st.reuses, st.computes, st.recomputes_same_input) == ("sizer", 2, 1, 1, 0)
    _assert_invariant(st)


def test_many_repeat_calls_zero_extra_computation():
    log = []
    block = _make_block(log)
    s = block(_base())
    for _ in range(50):
        assert block(s) is s
    assert len(log) == 1
    st = block.stats()
    assert (st.calls, st.reuses, st.computes, st.recomputes_same_input) == (51, 50, 1, 0)


def test_reuse_when_only_undeclared_field_changes():
    log = []
    block = _make_block(log)
    s1 = block(_base())
    s2 = s1.write("other", "o9", {("node", "u"): {"a": 123.0}})
    assert s2 is not s1
    assert block(s2) is s2
    assert len(log) == 1


def test_reuse_when_input_value_restored_same_value_new_object():
    log = []
    block = _make_block(log)
    s1 = block(_base(v={"a": 1.0}))
    s2 = s1.write("bias", "in2", {("node", "v"): {"a": 5.0}})
    s3 = s2.write("bias", "in3", {("node", "v"): {"a": 1.0}})  # 값 복원, 다른 객체·다른 출처 버전
    assert s3 is not s1
    assert block(s3) is s3
    assert len(log) == 1
    assert block.stats().reuses == 1


def test_recompute_when_declared_column_changes():
    log = []
    block = _make_block(log)
    s1 = block(_base(v={"a": 1.0}))
    s2 = s1.write("bias", "in2", {("node", "v"): {"a": 1.5}})
    s3 = block(s2)
    assert len(log) == 2
    assert s3.value("device", "m_a", "w") == 3.0
    assert s3.block_version("sizer") != s1.block_version("sizer")
    assert block.stats().recomputes_same_input == 0


def test_recompute_when_declared_column_key_set_changes():
    log = []
    block = _make_block(log)
    s1 = block(_base(v={"a": 1.0}))
    s3 = block(s1.write("bias", "in2", {("node", "v"): {"a": 1.0, "c": 4.0}}))
    assert len(log) == 2
    assert s3.column("device", "w") == (("m_a", 2.0), ("m_c", 8.0))


def test_recompute_when_extras_change_and_reuse_when_same():
    log = []
    block = _make_block(log)
    s0 = _base(v={"a": 1.0})
    s1 = block(s0, 1)
    assert block(s1, 1) is s1
    assert len(log) == 1
    s2 = block(s1, 2)
    assert len(log) == 2
    assert s2.value("device", "m_a", "w") == 4.0
    assert block(s2, 2) is s2
    assert len(log) == 2
    # extras 0.0 과 -0.0 은 다른 입력
    s3 = block(s2, 0.0)
    s4 = block(s3, -0.0)
    assert len(log) == 4
    assert s4 is not s3


def test_column_replace_from_block_result():
    log = []
    block = _make_block(log)
    s1 = block(_base(v={"a": 1.0, "b": 2.0}))
    s2 = block(s1.write("bias", "in2", {("node", "v"): {"b": 2.0}}))
    assert s2.keys("device") == ("m_b",)
    assert s2.record("device", "m_a") is None


# ---------- recomputes_same_input ----------

def test_recompute_same_input_other_lineage_counted():
    log = []
    block = _make_block(log)
    block(_base(v={"a": 1.0}))
    other_lineage = _base(v={"a": 1.0})      # 블록 결과 없는 다른 lineage, 같은 입력
    out = block(other_lineage)
    assert len(log) == 2
    st = block.stats()
    assert st.recomputes_same_input == 1
    assert (st.calls, st.computes, st.reuses) == (2, 2, 0)
    assert out.block_version("sizer") is not None


def test_reset_stats_clears_counts_and_history():
    log = []
    block = _make_block(log)
    block(_base(v={"a": 1.0}))
    block.reset_stats()
    st = block.stats()
    assert (st.calls, st.reuses, st.computes, st.recomputes_same_input) == (0, 0, 0, 0)
    block(_base(v={"a": 1.0}))  # 같은 v 지만 이력이 비워졌으므로 recompute 아님
    st = block.stats()
    assert (st.calls, st.computes, st.recomputes_same_input) == (1, 1, 0)


# ---------- 실패 ----------

@pytest.mark.parametrize("extra", [[1], {"a": 1}, {1}, bytearray(b"x"), object()],
                         ids=["list", "dict", "set", "bytearray", "object"])
def test_mutable_extras_rejected_no_call_no_count(extra):
    log = []
    block = _make_block(log)
    s0 = _base()
    with pytest.raises(TypeError):
        block(s0, extra)
    assert log == []
    st = block.stats()
    assert (st.calls, st.reuses, st.computes, st.recomputes_same_input) == (0, 0, 0, 0)


def test_undeclared_column_read_key_error():
    calls = []

    @compute_block("sizer", reads=READS, writes=WRITES)
    def sneaky(projection):
        calls.append(1)
        projection.column("node", "u")   # 선언 밖
        return {("device", "w"): {}}

    s0 = _base(u={"a": 1.0})
    with pytest.raises(KeyError):
        sneaky(s0)
    assert calls == [1]
    st = sneaky.stats()
    assert (st.calls, st.computes) == (1, 1)
    _assert_invariant(st)


def test_undeclared_value_read_key_error():
    @compute_block("sizer", reads=READS, writes=WRITES)
    def sneaky(projection):
        projection.value("node", "a", "u")
        return {("device", "w"): {}}

    with pytest.raises(KeyError):
        sneaky(_base(u={"a": 1.0}))


@pytest.mark.parametrize(
    "result",
    [
        None,
        [(("device", "w"), {"m": 1.0})],
        {},
        {("device", "gm"): {"m": 1.0}},
        {("device", "w"): {"m": 1.0}, ("device", "gm"): {"m": 1.0}},
    ],
    ids=["none", "list", "empty_mapping", "wrong_key", "extra_key"],
)
def test_result_keys_mismatch_value_error(result):
    @compute_block("sizer", reads=READS, writes=WRITES)
    def bad(projection):
        return result

    s0 = _base()
    with pytest.raises(ValueError):
        bad(s0)
    assert s0.column("device", "w") == ()


def test_result_missing_declared_write_value_error():
    @compute_block("sizer", reads=READS, writes=(("device", "w"), ("device", "gm")))
    def bad(projection):
        return {("device", "w"): {"m": 1.0}}

    with pytest.raises(ValueError):
        bad(_base())


def test_writer_permission_violation():
    calls = []

    @compute_block("bias", reads=READS, writes=WRITES)   # device.w 는 sizer 소유
    def intruder(projection):
        calls.append(1)
        return {("device", "w"): {"m": 1.0}}

    s0 = _base()
    with pytest.raises(WriterPermissionError):
        intruder(s0)
    assert s0.column("device", "w") == ()


def test_block_exception_propagates_and_counts():
    class Boom(Exception):
        pass

    calls = []

    @compute_block("sizer", reads=READS, writes=WRITES)
    def failing(projection):
        calls.append(1)
        raise Boom()

    s0 = _base()
    fp0 = s0.fp
    with pytest.raises(Boom):
        failing(s0)
    assert s0.fp == fp0 and s0.block_version("sizer") is None
    st = failing.stats()
    assert (st.calls, st.computes, st.reuses, st.recomputes_same_input) == (1, 1, 0, 0)
    # 같은 입력으로 다시 부르면 다시 계산되고 recompute 로 센다(실패 캐시는 search 층 몫)
    with pytest.raises(Boom):
        failing(s0)
    assert len(calls) == 2
    st = failing.stats()
    assert (st.calls, st.computes, st.recomputes_same_input) == (2, 2, 1)
    _assert_invariant(st)


def test_projection_does_not_expose_snapshot_write():
    seen = []

    @compute_block("sizer", reads=READS, writes=WRITES)
    def peek(projection):
        seen.append(projection)
        return {("device", "w"): {}}

    peek(_base())
    p = seen[0]
    assert not isinstance(p, GraphSnapshot)
    assert not hasattr(p, "write")


# =====================================================================================================================
# 2026-10-08 개정(사용자 승인 1, sizing O9) 회귀 -- 투영 지문을 값 지문 합성으로 바꿔도 §6.2 재사용 규칙은 그대로.
# oracle 종류: (a) 구성 -- 같은 스냅샷 두 번 호출이면 입력이 구성상 같으므로 두 번째는 함수 호출 0·`is`(§6.2 '재사용').
# 호출 수는 블록 함수 안 log 길이(피검 함수 밖 계수)와 stats 둘로 본다.
# =====================================================================================================================

MULTI_READS = (("node", "v"), ("node", "u"), ("device", "gm"))   # u 는 처음에 비어 있는 선언 열


def _make_multi_block(log):
    @compute_block("sizer", reads=MULTI_READS, writes=WRITES)
    def block(projection):
        v = projection.column("node", "v")
        u = projection.column("node", "u")
        log.append((v, u, projection.extras))
        return {("device", "w"): {"m_" + k: val + len(u) for k, val in v}}

    return block


def test_reuse_regression_multi_reads_extras_and_empty_column():
    log = []
    block = _make_multi_block(log)
    extras = (1, "x", (2.0, -0.0))
    s0 = _base()                                       # node u 없음(빈 선언 열)
    s1 = block(s0, *extras)
    assert len(log) == 1
    assert block(s1, *extras) is s1                    # 같은 스냅샷 두 번째 -> 함수 호출 0, 그대로
    assert len(log) == 1
    st = block.stats()
    assert (st.calls, st.reuses, st.computes, st.recomputes_same_input) == (2, 1, 1, 0)
    # 빈 선언 열에 값이 생기면 입력이 바뀐 것이다 -> 재계산(빈 열도 투영의 일부, §8)
    s2 = s1.write("other", "o1", {("node", "u"): {"z": 0.0}})
    s3 = block(s2, *extras)
    assert s3 is not s2
    assert len(log) == 2
    assert block(s3, *extras) is s3
    assert len(log) == 2
    # extras 의 -0.0 -> 0.0 은 다른 입력(§1 float.hex) -> 재계산
    block(s3, 1, "x", (2.0, 0.0))
    assert len(log) == 3
    _assert_invariant(block.stats())


def test_reuse_regression_only_undeclared_field_changes():
    log = []
    block = _make_block(log)                           # reads = node v 만
    s1 = block(_base(u={"a": 1.0}), "e")
    s2 = s1.write("other", "o2", {("node", "u"): {"a": 2.0, "b": 3.0}})   # 선언 밖 열만 바뀜
    s3 = s2.write("other", "o3", {("node", "u"): {}})                     # 선언 밖 열을 지움
    for s in (s2, s3):
        assert block(s, "e") is s
    assert len(log) == 1
    st = block.stats()
    assert (st.calls, st.reuses, st.computes, st.recomputes_same_input) == (3, 2, 1, 0)


# =====================================================================================================================
# 2026-10-08 개정(core 성능 5, CONTRACT §6.2·§8) -- 가변 extras 거부는 투영 지문 식 개정 뒤에도 그대로(계수 불변, 함수 미호출).
# oracle 종류: 거부 기준 = §6.2 'extras 는 각각 불변 -- 가변 -> TypeError(계수 변화 없음, 블록 함수 미호출)' + §2 거부 집합.
# =====================================================================================================================


@dataclasses.dataclass
class _MutDc:
    x: int


class _PlainObj:
    pass


@pytest.mark.parametrize("extras", [
    ((1, [2]),),
    ((1, (2, {"a": 3})),),
    (frozenset({(1, _PlainObj())}),),
    (_MutDc(1),),
    (1, "ok", [3]),
    ("ok", bytearray(b"x")),
], ids=["list_in_tuple", "dict_deep", "plain_in_frozenset", "dc_not_frozen", "last_of_three", "bytearray_second"])
def test_mutable_extras_rejected_after_prior_calls_counters_unchanged(extras):
    # oracle §6.2: 앞선 정상 호출(계산 1·재사용 1)로 계수를 만든 뒤 가변 extras 호출 -> TypeError, 계수·로그 그대로.
    log = []
    block = _make_block(log)
    s0 = _base()
    s1 = block(s0, 1)
    assert block(s1, 1) is s1
    before = block.stats()
    n_log = len(log)
    with pytest.raises(TypeError):
        block(s1, *extras)
    assert len(log) == n_log
    after = block.stats()
    assert (after.calls, after.reuses, after.computes, after.recomputes_same_input) == (
        before.calls, before.reuses, before.computes, before.recomputes_same_input) == (2, 1, 1, 0)
    # 거부 뒤에도 정상 호출은 그대로 재사용
    assert block(s1, 1) is s1
