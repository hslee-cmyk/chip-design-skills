"""XRUN-F1 card B interface card C0 -- `open_run()` 는 색인·계수의 유일한 생성 자리(B-T0).

oracle 종류: (a) 구성 -- C0 원문 '부를 때마다 새 두 객체(앞 호출의 것과 `is`가 아님, 항목·계수 0)', 타입은 C0·C1·C2 공개 이름.
기대값은 같음/다름·타입·0 뿐이고 피검 함수 출력에서 만들지 않는다.
"""
from gmid_engine.core import Donors, PerfCounters, RunCounters
from gmid_engine.search import S3Index, open_run


def test_open_run_returns_new_pair_each_call():
    # oracle 대조: C0 '부를 때마다 새 두 객체(앞 호출의 것과 is 가 아님)'
    first = open_run()
    second = open_run()
    assert isinstance(first, tuple) and len(first) == 2
    assert isinstance(second, tuple) and len(second) == 2
    d1, c1 = first
    d2, c2 = second
    assert d1 is not d2
    assert c1 is not c2
    assert d1 is not c1


def test_open_run_types():
    # oracle 대조: C0 'donors = 새 S3Index, counters = 새 RunCounters', C2 'S3Index(Donors)'
    donors, counters = open_run()
    assert isinstance(donors, S3Index)
    assert isinstance(donors, Donors)
    assert isinstance(counters, RunCounters)


def test_open_run_new_pair_is_empty():
    # oracle 대조: C0 '항목·계수 0' -- C2 entry_count = 성공 키 수 + 실패 키 수 = 0, C1 blocks = 한 번이라도 record 된 행만 = ()
    donors, counters = open_run()
    assert donors.entry_count() == 0
    snap = counters.snapshot()
    assert isinstance(snap, PerfCounters)
    assert snap.blocks == ()
    for name in ("calls", "reuses", "grafts", "replays", "computes", "recomputes_same_input"):
        assert getattr(snap.block_totals, name) == 0
