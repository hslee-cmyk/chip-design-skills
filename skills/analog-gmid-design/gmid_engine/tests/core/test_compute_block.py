"""CONTRACT §6 @compute_block -- 선언 검사, 입력 버전 같으면 함수 미호출(호출 계수로 확인: '같은 값 반복 계산 금지'),
선언 밖 열 KeyError, 결과 키 불일치 ValueError, 권한 위반, 계수 불변식과 recomputes_same_input."""
import dataclasses
import functools
import importlib.util
import inspect
import json
import os
import string
import subprocess
import sys
import types
from pathlib import Path

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


# =====================================================================================================================
# v1.9.3 결정 10 -- `ComputeBlock.code_hash` = 블록 함수 code 객체의 코드 내용만의 지문.
# 계약 출처(oracle (d), design 원문): 설계 40 v1.9.3 §2.4.3 '블록 코드 해시' 행 (1)~(9) -- (9) (a) 완료 조건 단위 test 전부.
# oracle 종류: (a) 구성 -- 쌍마다 design (1)'넣는 칸'·(2)'넣지 않는 칸' 가운데 정해진 칸만 다르게 만든 code 객체(같은 소스를 다른 경로에서
# import, 같은 소스를 다른 줄 위치에, `code.replace` 로 칸 하나만 바꿈). 기대값은 '같다/다르다' 관계와 거부 예외뿐이고, test 는 해시 문자열을
# 만들지도 피검 식을 다시 쓰지도 않는다. 각 쌍은 '정말 그 칸만 다르다'를 전제(assert)로 먼저 확인한다.
# =====================================================================================================================

_SKILL_DIR = Path(__file__).resolve().parents[3]          # tests/core -> tests -> gmid_engine -> analog-gmid-design(패키지 부모)

# 경로 무관·결정론 test 의 블록 모듈 소스: lambda·내부 함수(키워드 전용 인자)·generator 식(그 안에 문자열 frozenset 상수)·모듈 수준 tuple 상수와
# 같은 모양의 tuple 리터럴(설계 초안 2.3절 '참조 수' 재현 조건)을 담는다.
_MODULE_SRC = '''\
from gmid_engine.core import compute_block

SCALE = (2.0, "k", -0.0)


@compute_block("sizer", reads=(("node", "v"),), writes=(("device", "w"),))
def block(projection):
    """경로 무관 test 블록."""
    bump = lambda x: x + SCALE[0]
    def inner(y, *, k=3):
        return y * k
    total = sum(val for _key, val in projection.column("node", "v"))
    picked = tuple(k for k in ("alpha", "beta") if k in {"alpha", "beta", "gamma", "delta", "eps"})
    return {("device", "w"): {"m": inner(bump(total)) + len(picked) + (2.0, "k", -0.0)[0]}}
'''
_MODULE_NESTED = {"<lambda>", "inner", "<genexpr>"}


def _code_hash(fn):
    return compute_block("sizer", reads=READS, writes=WRITES)(fn).code_hash


def _fn_from(src, filename="codehash_case.py"):
    """소스를 컴파일해 그 안의 함수 하나를 돌려준다(이름 무관)."""
    ns = {}
    exec(compile(src, filename, "exec"), ns)
    fns = [v for k, v in ns.items() if k != "__builtins__" and isinstance(v, types.FunctionType)]
    assert len(fns) == 1
    return fns[0]


def _fn_with(code, closure=None):
    return types.FunctionType(code, {}, None, None, closure)


def _nested_codes(code):
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            yield c
            yield from _nested_codes(c)


def _load_module(path, modname):
    spec = importlib.util.spec_from_file_location(modname, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_module(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_MODULE_SRC.encode("utf-8"))
    return path


# ---------- (1)(2) 경로 무관: 같은 소스를 서로 다른 두 경로에서 import ----------

def test_code_hash_same_source_two_checkout_paths(tmp_path):
    p1 = _write_module(tmp_path / "a" / "blk.py")
    p2 = _write_module(tmp_path / "second_checkout_with_longer_path" / "pkg" / "deeper" / "blk.py")
    m1 = _load_module(p1, "_codehash_ck1")
    m2 = _load_module(p2, "_codehash_ck2")
    c1, c2 = m1.block.fn.__code__, m2.block.fn.__code__
    assert c1.co_filename != c2.co_filename                                   # 전제: 경로만 다르다
    assert _MODULE_NESTED <= {c.co_name for c in _nested_codes(c1)}           # 전제: lambda·내부 함수·generator 식 포함
    assert m1.block.code_hash == m2.block.code_hash


# ---------- (9)(a) 데코레이트 시점 값 = import 가 끝난 뒤 다시 잰 값 ----------

def test_code_hash_decorate_time_equals_remeasured_after_import(tmp_path):
    mod = _load_module(_write_module(tmp_path / "blk.py"), "_codehash_remeasure")
    at_decorate = mod.block.code_hash
    code = mod.block.fn.__code__
    # 상수 객체에 참조를 더 만든다(참조 수가 바뀌어도 코드 내용은 같다 -- 설계 (3) 'marshal 바이트는 참조 수에 따라 달라진다')
    held = [code.co_consts, mod.SCALE] + list(code.co_consts) + [c.co_consts for c in _nested_codes(code)]
    again = compute_block("sizer", reads=(("node", "v"),), writes=(("device", "w"),))(mod.block.fn).code_hash
    assert held and again == at_decorate
    assert _code_hash(mod.block.fn) == at_decorate                            # 선언(name·reads·writes)은 코드 지문 밖


# ---------- (9)(a) PYTHONHASHSEED 가 다른 하위 프로세스 사이에서 같다 (frozenset 상수 포함) ----------

_SUBPROC_SRC = '''\
import importlib.util, json, sys, types
order, path, out = sys.argv[1], sys.argv[2], sys.argv[3]
if order == "core_first":
    import gmid_engine.core
    _warm = [frozenset(("alpha", "beta", "gamma")) for _ in range(3)]
spec = importlib.util.spec_from_file_location("_codehash_sub", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
def walk(c):
    for k in c.co_consts:
        if isinstance(k, types.CodeType):
            yield from walk(k)
        elif isinstance(k, frozenset):
            yield list(k)
with open(out, "w", encoding="utf-8") as f:
    json.dump({"hash": mod.block.code_hash, "frozensets": list(walk(mod.block.fn.__code__))}, f)
'''


def test_code_hash_same_across_hashseed_subprocesses(tmp_path):
    mod_path = _write_module(tmp_path / "blk.py")
    script = tmp_path / "measure.py"
    script.write_text(_SUBPROC_SRC, encoding="utf-8")
    results = []
    for seed, order in (("1", "module_first"), ("2", "core_first")):
        out = tmp_path / ("out_%s.json" % seed)
        env = dict(os.environ, PYTHONHASHSEED=seed, PYTHONPATH=str(_SKILL_DIR))
        proc = subprocess.run([sys.executable, str(script), order, str(mod_path), str(out)], env=env, capture_output=True,
                              text=True, timeout=300)
        assert proc.returncode == 0, proc.stderr
        results.append(json.loads(out.read_text(encoding="utf-8")))
    # 전제: 문자열 frozenset 상수가 있고, 두 프로세스에서 순회 순서가 실제로 다르다(순서 무관을 시험하는 조건)
    assert results[0]["frozensets"] and results[0]["frozensets"] != results[1]["frozensets"]
    assert sorted(map(sorted, results[0]["frozensets"])) == sorted(map(sorted, results[1]["frozensets"]))
    assert len(results[0]["hash"]) == 64
    assert results[0]["hash"] == results[1]["hash"]


def test_code_hash_frozenset_iteration_order_free_in_process():
    # 1 과 9 는 8칸 표에서 같은 슬롯이라 넣는 순서대로 순회한다 -> 같은 집합, 다른 순회 순서(설계 (4) 'frozenset 은 원소 순회 순서와 무관').
    fn = _fn_from("def f(p):\n    return p in {1, 9}\n")
    code = fn.__code__
    i = [k for k, c in enumerate(code.co_consts) if isinstance(c, frozenset)][0]
    a, b = frozenset([1, 9]), frozenset([9, 1])
    assert list(a) != list(b) and a == b                                      # 전제
    consts_a = code.co_consts[:i] + (a,) + code.co_consts[i + 1:]
    consts_b = code.co_consts[:i] + (b,) + code.co_consts[i + 1:]
    assert _code_hash(_fn_with(code.replace(co_consts=consts_a))) == _code_hash(_fn_with(code.replace(co_consts=consts_b)))


# ---------- (9)(a) 의미 변경 쌍은 값이 다르다 (소스 쌍, 같은 파일 이름) ----------

_DIFF_PAIRS = [
    ("const", "def f(p):\n    return p + 1.5\n", "def f(p):\n    return p + 2.5\n"),
    ("nested_const_lambda", "def f(p):\n    g = lambda x: x + 1\n    return g(p)\n",
     "def f(p):\n    g = lambda x: x + 2\n    return g(p)\n"),
    ("nested_const_inner_def", "def f(p):\n    def h(x):\n        return x * 3\n    return h(p)\n",
     "def f(p):\n    def h(x):\n        return x * 4\n    return h(p)\n"),
    ("nested_const_genexpr", "def f(p):\n    return sum(x + 1 for x in p)\n", "def f(p):\n    return sum(x + 2 for x in p)\n"),
    ("local_name", "def f(p):\n    a = p\n    return a\n", "def f(p):\n    b = p\n    return b\n"),
    ("arg_name", "def f(p):\n    return p\n", "def f(q):\n    return q\n"),
    ("docstring", 'def f(p):\n    """one"""\n    return p\n', 'def f(p):\n    """two"""\n    return p\n'),
    ("docstring_added", "def f(p):\n    return p\n", 'def f(p):\n    """one"""\n    return p\n'),
    ("kwonly_arg", "def f(p, q=1):\n    return p\n", "def f(p, *, q=1):\n    return p\n"),
    ("posonly_arg", "def f(p, q=1):\n    return p\n", "def f(p, /, q=1):\n    return p\n"),
    ("arg_count", "def f(p, q=1):\n    return p\n", "def f(p, q=1, r=2):\n    return p\n"),
    ("global_name", "def f(p):\n    return GA + p\n", "def f(p):\n    return GB + p\n"),
    ("attr_name", "def f(p):\n    return p.x\n", "def f(p):\n    return p.y\n"),
    ("bytecode_op", "def f(p):\n    return p + 1\n", "def f(p):\n    return p - 1\n"),
    ("func_name", "def f(p):\n    return p\n", "def g(p):\n    return p\n"),
    ("closure_name", "def f(p):\n    k = 1\n    def h():\n        return k\n    return h\n",
     "def f(p):\n    m = 1\n    def h():\n        return m\n    return h\n"),
    ("neg_zero_src", "def f(p):\n    return p + 0.0\n", "def f(p):\n    return p + -0.0\n"),
    ("true_vs_one_src", "def f(p):\n    return (p, 1)\n", "def f(p):\n    return (p, True)\n"),
]


@pytest.mark.parametrize("src_a,src_b", [(a, b) for _i, a, b in _DIFF_PAIRS], ids=[i for i, _a, _b in _DIFF_PAIRS])
def test_code_hash_semantic_change_differs(src_a, src_b):
    assert _code_hash(_fn_from(src_a)) != _code_hash(_fn_from(src_b))


# 상수만 바꾼 쌍(`code.replace(co_consts=)` -- 바이트코드·이름은 그대로): -0.0/0.0, True/1, 그 tuple·frozenset 원소, 중첩 code 안의 상수,
# complex 실수부 부호(설계 (4) 'complex 실수부·허수부는 float 규칙'), 같은 모양 tuple 과 slice·complex(설계 (3) '타입 이름이 인코딩에 들어간다').
_CONST_SWAPS = [
    ("neg_zero", 0.0, -0.0),
    ("true_vs_one", 1, True),
    ("false_vs_zero", 0, False),
    ("int_vs_float", 1, 1.0),
    ("neg_zero_in_tuple", (0.0, "a"), (-0.0, "a")),
    ("true_in_tuple", (1, "a"), (True, "a")),
    ("true_in_frozenset", frozenset({1, "a"}), frozenset({True, "a"})),
    ("nested_tuple", ((1, 2), 3), ((1, 2), 4)),
    ("complex_real_sign", complex(0.0, 1.0), complex(-0.0, 1.0)),
    ("complex_imag", 1j, 2j),
    ("slice_vs_tuple", slice(1, 3, None), (1, 3, None)),
    ("complex_vs_tuple", complex(1.0, 2.0), (1.0, 2.0)),
    ("ellipsis_vs_none", Ellipsis, None),
    ("bytes_vs_str", b"x", "x"),
    ("slice_in_tuple", (slice(1, 3, None), 1j), (slice(1, 4, None), 1j)),
    ("complex_in_tuple", (slice(1, 3, None), 1j), (slice(1, 3, None), 2j)),
]


def _swap_const(code, index, value):
    return code.replace(co_consts=code.co_consts[:index] + (value,) + code.co_consts[index + 1:])


@pytest.mark.parametrize("old,new", [(o, n) for _i, o, n in _CONST_SWAPS], ids=[i for i, _o, _n in _CONST_SWAPS])
def test_code_hash_constant_swap_differs(old, new):
    code = _fn_from("def f(p):\n    return (p, 'marker')\n").__code__.replace(co_consts=(old,))
    other = code.replace(co_consts=(new,))
    assert code.co_code == other.co_code and code.co_names == other.co_names       # 전제: 상수 칸만 다르다
    assert _code_hash(_fn_with(code)) != _code_hash(_fn_with(other))


@pytest.mark.parametrize("old,new", [(0.0, -0.0), (1, True), ("a", "b")], ids=["neg_zero", "true_vs_one", "str"])
def test_code_hash_constant_swap_inside_nested_code_differs(old, new):
    outer = _fn_from("def f(p):\n    g = lambda x: (x, 'slot')\n    return g(p)\n").__code__
    li = [k for k, c in enumerate(outer.co_consts) if isinstance(c, types.CodeType)][0]
    lam = outer.co_consts[li]
    si = lam.co_consts.index("slot")
    a = _swap_const(outer, li, _swap_const(lam, si, old))
    b = _swap_const(outer, li, _swap_const(lam, si, new))
    assert _code_hash(_fn_with(a)) != _code_hash(_fn_with(b))


# ---------- (9)(a) 함수 이동·주석 줄·빈 줄·줄 끝 주석은 값이 같다 ----------

_SAME_BASE = (
    "def f(p):\n"
    "    g = lambda x: x + 1\n"
    "    a = sum(g(i) for i in p)\n"
    "    return a * 2\n"
)
# (id, 소스, 줄 정보 칸(co_firstlineno·co_linetable)이 실제로 바뀌는가 -- 3.14 실측: 줄 끝 주석만은 줄 정보도 그대로다)
_SAME_PAIRS = [
    ("moved_by_blank_lines", "\n\n\n\n" + _SAME_BASE, True),
    ("moved_by_code_above", "X_ABOVE = 1\nY_ABOVE = 2\n\n\n" + _SAME_BASE, True),
    ("comment_line_above", "# 주석 줄\n" + _SAME_BASE, True),
    ("comment_line_inside", _SAME_BASE.replace("    a = sum", "    # 안쪽 주석 줄\n    a = sum"), True),
    ("blank_line_inside", _SAME_BASE.replace("    a = sum", "\n    a = sum"), True),
    ("blank_lines_inside_twice", _SAME_BASE.replace("    a = sum", "\n\n    a = sum").replace("    return", "\n    return"), True),
    ("eol_comment", _SAME_BASE.replace("x + 1\n", "x + 1  # 줄 끝 주석\n"), False),
]


@pytest.mark.parametrize("src,line_info_changes", [(s, c) for _i, s, c in _SAME_PAIRS], ids=[i for i, _s, _c in _SAME_PAIRS])
def test_code_hash_line_only_edit_same(src, line_info_changes):
    base = _fn_from(_SAME_BASE).__code__
    moved = _fn_from(src).__code__
    assert base.co_code == moved.co_code                                           # 전제: 바이트코드 같음
    # 전제: 줄 정보 칸이 바뀌는 쌍은 실제로 바뀌었다('줄 정보 제외'를 시험하는 조건)
    assert ((base.co_firstlineno, base.co_linetable) != (moved.co_firstlineno, moved.co_linetable)) == line_info_changes
    assert _code_hash(_fn_with(base)) == _code_hash(_fn_with(moved))


def test_code_hash_other_filename_same():
    assert _code_hash(_fn_from(_SAME_BASE, "a/one.py")) == _code_hash(_fn_from(_SAME_BASE, "b/c/other_checkout.py"))


# ---------- (9)(a) slice·complex·Ellipsis·bytes 상수: 데코레이트 성공, 각 상수를 바꾸면 값이 바뀐다 ----------

_TYPED_SRC = "def f(a):\n    return (a[1:3], 1j, ..., b'x')\n"
_TYPED_EDITS = [
    ("slice", "a[1:3]", "a[1:4]", slice),
    ("complex", "1j", "2j", complex),
    ("ellipsis", "...", "None", type(Ellipsis)),
    ("bytes", "b'x'", "b'y'", bytes),
]


def test_code_hash_typed_constants_decorate():
    fn = _fn_from(_TYPED_SRC)
    kinds = {type(c) for c in fn.__code__.co_consts}
    assert {slice, complex, type(Ellipsis), bytes} <= kinds                         # 전제: 그 타입 상수가 실제로 co_consts 에 있다
    h = _code_hash(fn)
    assert isinstance(h, str) and len(h) == 64 and set(h) <= set(string.hexdigits.lower())


@pytest.mark.parametrize("old,new,kind", [(o, n, k) for _i, o, n, k in _TYPED_EDITS], ids=[i for i, _o, _n, _k in _TYPED_EDITS])
def test_code_hash_typed_constant_change_differs(old, new, kind):
    assert old in _TYPED_SRC
    a, b = _fn_from(_TYPED_SRC), _fn_from(_TYPED_SRC.replace(old, new))
    assert kind in {type(c) for c in a.__code__.co_consts}
    assert _code_hash(a) != _code_hash(b)


# ---------- (9)(a) 미지원 상수 타입 -> 데코레이트 시점 TypeError (fail-closed) ----------

class _Opaque:
    pass


def _with_lambda_const(value):
    outer = _fn_from("def f(p):\n    g = lambda x: x\n    return g(p)\n").__code__
    li = [k for k, c in enumerate(outer.co_consts) if isinstance(c, types.CodeType)][0]
    lam = outer.co_consts[li]
    return _swap_const(outer, li, lam.replace(co_consts=lam.co_consts + (value,)))


_UNSUPPORTED = [
    ("object", lambda c: c.replace(co_consts=c.co_consts + (object(),))),
    ("plain_instance", lambda c: c.replace(co_consts=c.co_consts + (_Opaque(),))),
    ("list", lambda c: c.replace(co_consts=c.co_consts + ([1],))),
    ("dict", lambda c: c.replace(co_consts=c.co_consts + ({"a": 1},))),
    ("type_object", lambda c: c.replace(co_consts=c.co_consts + (int,))),
    ("in_tuple", lambda c: c.replace(co_consts=c.co_consts + ((1, object()),))),
    ("in_frozenset", lambda c: c.replace(co_consts=c.co_consts + (frozenset({1, _Opaque()}),))),
    ("in_nested_code", lambda c: _with_lambda_const(object())),
]


@pytest.mark.parametrize("mutate", [m for _i, m in _UNSUPPORTED], ids=[i for i, _m in _UNSUPPORTED])
def test_code_hash_unsupported_constant_type_error(mutate):
    code = mutate(_fn_from("def f(p):\n    return p\n").__code__)
    with pytest.raises(TypeError):
        compute_block("sizer", reads=READS, writes=WRITES)(_fn_with(code))


# ---------- (9)(a) __wrapped__ 사슬 (설계 (5)) ----------

def _wrap(fn):
    @functools.wraps(fn)
    def outer(projection):
        return fn(projection)
    return outer


def test_code_hash_wrapped_inner_body_differs():
    in_a = _fn_from("def body(p):\n    return p + 1\n")
    in_b = _fn_from("def body(p):\n    return p + 2\n")
    wa, wb = _wrap(in_a), _wrap(in_b)
    assert wa.__code__ is wb.__code__ and wa.__wrapped__ is in_a and wb.__wrapped__ is in_b   # 전제: 감싸는 함수 code 가 같다
    assert _code_hash(wa) != _code_hash(wb)


def test_code_hash_wrapped_chain_order_matters():
    # 설계 (5) '순서도 지문에 든다': 머리(감싸는 함수) code 가 같고 사슬 원소 집합이 같으며 순서만 다른 두 블록.
    x = _fn_from("def body(p):\n    return p + 1\n")
    y = _fn_from("def body(p):\n    return p + 2\n")
    x2, y2 = _fn_with(x.__code__), _fn_with(y.__code__)
    head1 = _wrap(x)
    head2 = _wrap(y2)
    x.__wrapped__ = y                       # 사슬 (head, x, y)
    y2.__wrapped__ = x2                     # 사슬 (head, y, x)
    assert head1.__code__ is head2.__code__                                        # 전제: 머리 code 같다
    assert _code_hash(head1) != _code_hash(head2)


def test_code_hash_wrapped_cycle_self_value_error():
    f = _fn_from("def body(p):\n    return p\n")
    f.__wrapped__ = f
    with pytest.raises(ValueError):
        compute_block("sizer", reads=READS, writes=WRITES)(f)


def test_code_hash_wrapped_cycle_two_value_error():
    f = _fn_from("def body(p):\n    return p\n")
    g = _fn_from("def other(p):\n    return p\n")
    f.__wrapped__ = g
    g.__wrapped__ = f
    with pytest.raises(ValueError):
        compute_block("sizer", reads=READS, writes=WRITES)(f)


@pytest.mark.parametrize("make_tail", [lambda: len, lambda: types.SimpleNamespace(), lambda: functools.partial(max, 1)],
                         ids=["builtin", "namespace", "partial"])
def test_code_hash_wrapped_element_without_code_type_error(make_tail):
    f = _fn_from("def body(p):\n    return p\n")
    tail = make_tail()
    assert not hasattr(tail, "__code__")                                           # 전제
    f.__wrapped__ = tail
    with pytest.raises(TypeError):
        compute_block("sizer", reads=READS, writes=WRITES)(f)


# ---------- (9)(a) code 타입 co_* 이름 전체 = 넣는 13 + 넣지 않는 9 (설계 (1)·(2), 3.14 기준 22개) ----------
# 목록 출처 (d): 설계 40 §2.4.3 '블록 코드 해시' 행 (1)·(2) 원문. 모르는 co_* 이름이 생기면(새 Python 판) 이 test 가 실패한다.

_INCLUDED = ("co_code", "co_consts", "co_names", "co_varnames", "co_freevars", "co_cellvars", "co_argcount",
             "co_posonlyargcount", "co_kwonlyargcount", "co_flags", "co_exceptiontable", "co_name", "co_qualname")
_EXCLUDED = ("co_filename", "co_firstlineno", "co_linetable", "co_lnotab", "co_lines", "co_positions", "co_branches",
             "co_nlocals", "co_stacksize")
# 넣지 않는 칸 가운데 따로 바꿀 수 없는 파생 칸 -> 그 원천 칸(설계 (2): co_nlocals = len(co_varnames), 줄 정보 메서드·co_lnotab 은 co_linetable 에서)
_DERIVED = {"co_nlocals": "co_varnames", "co_lnotab": "co_linetable", "co_lines": "co_linetable",
            "co_positions": "co_linetable", "co_branches": "co_linetable"}


def test_code_type_co_names_fully_partitioned():
    names = {n for n in dir(types.CodeType) if n.startswith("co_")}
    assert len(_INCLUDED) == 13 and len(_EXCLUDED) == 9
    assert not set(_INCLUDED) & set(_EXCLUDED)
    unknown = names - set(_INCLUDED) - set(_EXCLUDED)
    assert not unknown, "설계 (1)·(2) 어디에도 없는 co_* 이름: %r" % sorted(unknown)
    assert names == set(_INCLUDED) | set(_EXCLUDED)


def _code_of(src):
    return _fn_from(src).__code__


def _closure_inner():
    outer = _fn_from("def f(p):\n    k = 1\n    def h():\n        return k\n    return h\n")
    inner = outer(0)
    return inner.__code__, inner.__closure__


# 칸 하나만 바꾼 (원래 code, 바꾼 code, closure) -- 칸마다 `code.replace` 한 번(co_code·co_linetable 은 다른 컴파일 결과의 같은 칸).
def _mutations():
    plain = _code_of("def f(p, q):\n    return p.x + q\n")
    plus, minus = _code_of("def f(p):\n    return p + 1\n"), _code_of("def f(p):\n    return p - 1\n")
    spaced = _code_of("def f(p):\n\n    # c\n\n    return p + 1\n")
    tryc = _code_of("def f(p):\n    try:\n        return p.x\n    except KeyError:\n        return 0\n")
    outer = _code_of("def f(p):\n    k = 1\n    def h():\n        return k\n    return h\n")
    inner, cells = _closure_inner()
    return {
        "co_code": (plus, plus.replace(co_code=minus.co_code), None),
        "co_consts": (plain, plain.replace(co_consts=plain.co_consts + ("extra",)), None),
        "co_names": (plain, plain.replace(co_names=("y",)), None),
        "co_varnames": (plain, plain.replace(co_varnames=("p", "r")), None),
        "co_freevars": (inner, inner.replace(co_freevars=("zz",)), cells),
        "co_cellvars": (outer, outer.replace(co_cellvars=("zz",)), None),
        "co_argcount": (plain, plain.replace(co_argcount=1), None),
        "co_posonlyargcount": (plain, plain.replace(co_posonlyargcount=1), None),
        "co_kwonlyargcount": (plain.replace(co_argcount=1), plain.replace(co_argcount=1, co_kwonlyargcount=1), None),
        "co_flags": (plain, plain.replace(co_flags=plain.co_flags ^ inspect.CO_NESTED), None),
        "co_exceptiontable": (tryc, tryc.replace(co_exceptiontable=b""), None),
        "co_name": (plain, plain.replace(co_name="g"), None),
        "co_qualname": (plain, plain.replace(co_qualname="Outer.f"), None),
        "co_filename": (plain, plain.replace(co_filename="elsewhere/checkout/x.py"), None),
        "co_firstlineno": (plain, plain.replace(co_firstlineno=plain.co_firstlineno + 100), None),
        "co_linetable": (plus, plus.replace(co_linetable=spaced.co_linetable), None),
        "co_stacksize": (plain, plain.replace(co_stacksize=plain.co_stacksize + 5), None),
    }


def test_code_hash_mutation_cases_cover_every_co_name():
    covered = set(_mutations()) | set(_DERIVED)
    assert covered == {n for n in dir(types.CodeType) if n.startswith("co_")}
    assert set(_DERIVED.values()) <= set(_mutations())


@pytest.mark.parametrize("field", _INCLUDED)
def test_code_hash_included_field_change_differs(field):
    before, after, closure = _mutations()[field]
    changed = [f for f in _INCLUDED if getattr(before, f) != getattr(after, f)]
    assert changed == [field]                                                      # 전제: 넣는 칸 가운데 그 칸 하나만 바뀌었다
    assert _code_hash(_fn_with(before, closure)) != _code_hash(_fn_with(after, closure))


@pytest.mark.parametrize("field", [f for f in _EXCLUDED if f not in _DERIVED])
def test_code_hash_excluded_field_change_same(field):
    before, after, closure = _mutations()[field]
    assert getattr(before, field) != getattr(after, field)                         # 전제: 그 칸이 바뀌었다
    changed = [f for f in _INCLUDED if getattr(before, f) != getattr(after, f)]
    assert changed == []                                                           # 전제: 넣는 칸은 하나도 안 바뀌었다
    assert _code_hash(_fn_with(before, closure)) == _code_hash(_fn_with(after, closure))
