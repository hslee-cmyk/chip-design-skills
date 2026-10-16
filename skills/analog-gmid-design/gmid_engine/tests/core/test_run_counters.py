"""XRUN-F1 card B interface card C1 -- `RunCounters`(record·result·snapshot)·`PerfCounters`(B-T1~B-T3).

두 객체는 언제나 `open_run()` 으로 얻는다(C0, 규칙 M M-b -- test 도 `RunCounters(...)` 를 직접 만들지 않는다).

oracle 종류:
* (손) 손으로 정한 `record` 순서. 기대 계수는 그 순서를 C1 원문 규칙('calls = reuses + grafts + replays + computes',
  'recomputes_same_input: record(..., "compute", v) 때 같은 (block, part, v) 의 "compute" 가 이미 있었으면 +1, reuse·graft·replay 는
  바꾸지 않는다')로 손으로 센 표(아래 `_HAND_EXPECTED`) -- 피검 계수에서 만들지 않는다.
* (식) C1 'result 섞임 ValueError', '(block, part) 정렬, 한 번이라도 record 된 것만', 'block_totals = 여섯 칸 합'.
* (비교) snapshot 을 기록 앞뒤로 비교, 두 open_run() 계수 비교.
"""
import pytest

from gmid_engine.core import PerfCounters
from gmid_engine.search import open_run

_FIELDS = ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input")
_ROW_ATTRS = ("block", "part") + _FIELDS

# 손으로 정한 기록 순서 -- 이름은 정렬 순서와 다르게 넣는다(정렬 검사), part 는 card B 에서 늘 "*".
_HAND_SEQUENCE = (
    ("zeta", "compute", "v1"),
    ("alpha", "compute", "v1"),
    ("alpha", "compute", "v1"),     # 같은 키 두 번째 compute -> alpha recomputes +1
    ("alpha", "compute", "v2"),     # 다른 입력 버전 -> +0
    ("alpha", "reuse", "v1"),
    ("alpha", "graft", "v1"),
    ("alpha", "replay", "v2"),
    ("alpha", "compute", "v1"),     # 같은 키 세 번째 compute -> 이미 있었다 -> +1
    ("mid", "reuse", "v9"),         # reuse 는 compute 이력을 만들지 않는다
    ("mid", "graft", "v9"),
    ("mid", "replay", "v9"),
    ("mid", "compute", "v9"),       # 그 키의 첫 compute -> +0
    ("zeta", "compute", "v2"),
    ("zeta", "reuse", "v1"),
)

# 위 순서를 C1 규칙으로 손으로 센 값: (calls, reuses, grafts, replays, computes, recomputes_same_input)
_HAND_EXPECTED = {
    "alpha": (7, 1, 1, 1, 4, 2),
    "mid": (4, 1, 1, 1, 1, 0),
    "zeta": (3, 1, 0, 0, 2, 0),
}


def _row_tuple(row):
    return tuple(getattr(row, f) for f in _FIELDS)


def _replay(counters, seq):
    for block, outcome, version in seq:
        counters.record(block, "*", outcome, version)


# ---------- B-T1: 손 순서에서 행 여섯 칸·항등식 ----------

def test_run_counters_hand_sequence_rows():
    # oracle 대조: (손) _HAND_EXPECTED -- C1 규칙으로 손으로 센 표
    _donors, counters = open_run()
    _replay(counters, _HAND_SEQUENCE)
    snap = counters.snapshot()
    assert isinstance(snap, PerfCounters)
    got = {row.block: _row_tuple(row) for row in snap.blocks}
    assert got == _HAND_EXPECTED
    for row in snap.blocks:
        assert row.part == "*"
        # oracle 대조: (식) C1 'calls = reuses + grafts + replays + computes'
        assert row.calls == row.reuses + row.grafts + row.replays + row.computes
        for attr in _ROW_ATTRS:
            assert hasattr(row, attr)


def test_run_counters_only_second_same_key_compute_counts():
    # oracle 대조: (손) C1 'recomputes_same_input -- 같은 (block, part, v) 의 compute 가 이미 있었으면 +1'.
    # 기록마다 그 시점 snapshot 을 떠서 recomputes_same_input 이 바뀌는 자리가 같은 키 두 번째 compute 하나뿐임을 본다.
    _donors, counters = open_run()
    steps = (
        ("b", "compute", "v1", 0),
        ("b", "reuse", "v1", 0),
        ("b", "graft", "v1", 0),
        ("b", "replay", "v1", 0),
        ("b", "compute", "v2", 0),
        ("b", "compute", "v1", 1),      # 같은 키 두 번째 compute
        ("c", "compute", "v1", 1),      # 다른 블록·같은 입력 버전 문자열 -> 다른 키. b 행은 누적값 1 그대로(C1: 행 계수는 누적, c 기록은 b 를 바꾸지 않는다)
    )
    for block, outcome, version, expect_b in steps:
        counters.record(block, "*", outcome, version)
        rows = {r.block: r for r in counters.snapshot().blocks}
        assert rows["b"].recomputes_same_input == expect_b
    rows = {r.block: r for r in counters.snapshot().blocks}
    assert rows["c"].recomputes_same_input == 0


# ---------- B-T2: result 섞임 ValueError ----------

@pytest.mark.parametrize("first,second", [(True, False), (False, True)], ids=["ok_then_fail", "fail_then_ok"])
def test_run_counters_result_mixed_value_error(first, second):
    # oracle 대조: (식) C1 'result: 한 (block, part, v) 에 ok=True 와 ok=False 가 섞이면 섞이는 그 호출에서 ValueError'
    _donors, counters = open_run()
    counters.record("blk", "*", "compute", "v1")
    counters.result("blk", "*", "v1", first)
    with pytest.raises(ValueError):
        counters.result("blk", "*", "v1", second)


def test_run_counters_result_other_key_not_mixed():
    # oracle 대조: (식) 섞임 판정 단위는 (block, part, v) -- 다른 v·다른 블록의 반대 결과는 섞임이 아니다
    _donors, counters = open_run()
    counters.record("blk", "*", "compute", "v1")
    counters.record("blk", "*", "compute", "v2")
    counters.record("oth", "*", "compute", "v1")
    counters.result("blk", "*", "v1", True)
    counters.result("blk", "*", "v2", False)
    counters.result("oth", "*", "v1", False)
    rows = {r.block: _row_tuple(r) for r in counters.snapshot().blocks}
    assert rows == {"blk": (2, 0, 0, 0, 2, 0), "oth": (1, 0, 0, 0, 1, 0)}


# ---------- B-T3: snapshot 불변·정렬·불린 것만·합·실행 독립 ----------

def test_run_counters_snapshot_is_immutable_value():
    # oracle 대조: (식) C1 'PerfCounters ... frozen', '행 = frozen 값' -- 속성 대입 실패
    _donors, counters = open_run()
    counters.record("blk", "*", "compute", "v1")
    snap = counters.snapshot()
    assert isinstance(snap.blocks, tuple)
    with pytest.raises((AttributeError, TypeError)):
        snap.blocks = ()
    with pytest.raises((AttributeError, TypeError)):
        snap.blocks[0].calls = 99
    with pytest.raises((AttributeError, TypeError)):
        snap.block_totals.calls = 99


def test_run_counters_snapshot_unchanged_by_later_records():
    # oracle 대조: (비교) C1 'snapshot() 결과는 그 뒤 기록에 따라 바뀌지 않는다'
    _donors, counters = open_run()
    counters.record("blk", "*", "compute", "v1")
    before = counters.snapshot()
    frozen_rows = [(r.block, r.part) + _row_tuple(r) for r in before.blocks]
    frozen_totals = tuple(getattr(before.block_totals, f) for f in _FIELDS)
    counters.record("blk", "*", "compute", "v1")
    counters.record("new", "*", "reuse", "v3")
    assert [(r.block, r.part) + _row_tuple(r) for r in before.blocks] == frozen_rows == [("blk", "*", 1, 0, 0, 0, 1, 0)]
    assert tuple(getattr(before.block_totals, f) for f in _FIELDS) == frozen_totals == (1, 0, 0, 0, 1, 0)
    after = counters.snapshot()
    assert [(r.block, r.part) + _row_tuple(r) for r in after.blocks] == [
        ("blk", "*", 2, 0, 0, 0, 2, 1), ("new", "*", 1, 1, 0, 0, 0, 0)]


def test_run_counters_rows_sorted_and_only_recorded():
    # oracle 대조: (식) C1 '(block, part) 정렬, 한 번이라도 record 된 것만'
    _donors, counters = open_run()
    for name in ("m", "z", "a", "q"):
        counters.record(name, "*", "reuse", "v")
    keys = [(r.block, r.part) for r in counters.snapshot().blocks]
    assert keys == sorted(keys) == [("a", "*"), ("m", "*"), ("q", "*"), ("z", "*")]
    # result 는 여섯 칸을 바꾸지 않는다 -- 칸은 record 의 outcome 으로만 정해진다(C1 'calls = reuses + grafts + replays + computes')
    _d2, other = open_run()
    other.record("x", "*", "compute", "v")
    other.result("x", "*", "v", True)
    assert [(r.block,) + _row_tuple(r) for r in other.snapshot().blocks] == [("x", 1, 0, 0, 0, 1, 0)]


def test_run_counters_block_totals_equal_test_sum():
    # oracle 대조: (손) block_totals 의 여섯 칸 = test 가 행에서 직접 더한 합, 그리고 손 표(_HAND_EXPECTED)의 합
    _donors, counters = open_run()
    _replay(counters, _HAND_SEQUENCE)
    snap = counters.snapshot()
    for i, f in enumerate(_FIELDS):
        row_sum = sum(getattr(r, f) for r in snap.blocks)
        hand_sum = sum(v[i] for v in _HAND_EXPECTED.values())
        assert getattr(snap.block_totals, f) == row_sum == hand_sum


def test_run_counters_two_open_runs_independent():
    # oracle 대조: (비교) C1 '서로 다른 open_run() 의 계수는 서로 보지 않는다'
    _d1, first = open_run()
    _d2, second = open_run()
    first.record("blk", "*", "compute", "v1")
    assert second.snapshot().blocks == ()
    second.record("blk", "*", "compute", "v1")       # 다른 실행에서는 첫 compute -- recompute 아님
    r1 = first.snapshot().blocks
    r2 = second.snapshot().blocks
    assert [_row_tuple(r) for r in r1] == [(1, 0, 0, 0, 1, 0)]
    assert [_row_tuple(r) for r in r2] == [(1, 0, 0, 0, 1, 0)]
