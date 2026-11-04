"""XRUN-F1 card B interface card C2 -- `S3Index`(Donors 구현) 조회·등록·fail-closed·`entry_count`(B-T13).

색인은 언제나 `open_run()` 으로 얻는다(C0, 규칙 M M-b -- `S3Index()` 를 test 가 직접 만들지 않는다).

oracle 종류: (손) 손으로 만든 스냅샷·실패 기록과 등록 순서. 기대값은 C2 원문 -- 키 = (writer, part, input_version),
'find·find_failure 는 등록한 그 객체(is)', '없는 키 -> None'(writer·input_version 이 다른 키), '같은 키 두 번째 register -> ValueError, 첫 등록 유지',
'register_failure 두 번째도 ValueError', 'block_version(writer) != 키의 입력 버전 -> ValueError', '성공과 실패를 함께(순서 무관)
ValueError', 'entry_count = 성공 키 수 + 실패 키 수'.
"""
import pytest

from gmid_engine.core import FailureRecord, GraphSnapshot, WriterTable
from gmid_engine.search import open_run

_TABLE = WriterTable([("node", "v", "blk"), ("node", "u", "oth")])


def _snap(writer="blk", version="v1", value=1.0):
    field = "v" if writer == "blk" else "u"
    return GraphSnapshot.empty(_TABLE).write(writer, version, {("node", field): {"a": value}})


def _record(cls="NONCONVERGENT"):
    return FailureRecord(cls, devices=("M1",), margin=0.5, detail={"why": "hand"})


def test_s3_index_register_then_find_is_same_object():
    # oracle 대조: C2 'find 는 등록한 그 객체(is)'
    donors, _counters = open_run()
    s = _snap()
    donors.register("blk", "*", "v1", s)
    assert donors.find("blk", "*", "v1") is s


def test_s3_index_missing_keys_none():
    # oracle 대조: C2 '없는 키 -> None' -- 키 세 칸 중 하나만 달라도 없는 키
    donors, _counters = open_run()
    donors.register("blk", "*", "v1", _snap())
    donors.register_failure("blk", "*", "v2", _record())
    assert donors.find("blk", "*", "v9") is None
    assert donors.find("oth", "*", "v1") is None
    assert donors.find("blk", "*", "v2") is None           # 실패 키는 성공 조회에 없다
    assert donors.find_failure("blk", "*", "v1") is None   # 성공 키는 실패 조회에 없다
    assert donors.find_failure("blk", "*", "v9") is None


def test_index_single_source():
    # oracle 대조: C2 '같은 키 두 번째 register -> ValueError, 첫 등록 유지(원천은 키마다 하나)'
    donors, _counters = open_run()
    first = _snap(value=1.0)
    second = _snap(value=1.0)          # 같은 값의 다른 객체
    other = _snap(value=2.0)
    donors.register("blk", "*", "v1", first)
    with pytest.raises(ValueError):
        donors.register("blk", "*", "v1", second)
    with pytest.raises(ValueError):
        donors.register("blk", "*", "v1", other)
    assert donors.find("blk", "*", "v1") is first
    assert donors.entry_count() == 1


def test_s3_index_register_version_mismatch_value_error():
    # oracle 대조: C2 'register 하는 스냅샷의 block_version(writer) != 키의 입력 버전 -> ValueError'
    donors, _counters = open_run()
    with pytest.raises(ValueError):
        donors.register("blk", "*", "v2", _snap(version="v1"))
    # 그 writer 의 블록 결과가 없는 스냅샷(block_version None)도 불일치
    with pytest.raises(ValueError):
        donors.register("blk", "*", "v1", _snap(writer="oth", version="v1"))
    assert donors.find("blk", "*", "v2") is None
    assert donors.find("blk", "*", "v1") is None
    assert donors.entry_count() == 0


def test_s3_index_success_then_failure_same_key_value_error():
    # oracle 대조: C2 '한 키에 성공과 실패를 함께 등록하려 하면(순서 무관) ValueError' -- 성공 먼저
    donors, _counters = open_run()
    s = _snap()
    donors.register("blk", "*", "v1", s)
    with pytest.raises(ValueError):
        donors.register_failure("blk", "*", "v1", _record())
    assert donors.find("blk", "*", "v1") is s
    assert donors.find_failure("blk", "*", "v1") is None
    assert donors.entry_count() == 1


def test_s3_index_failure_then_success_same_key_value_error():
    # oracle 대조: C2 같은 문장 -- 실패 먼저
    donors, _counters = open_run()
    rec = _record()
    donors.register_failure("blk", "*", "v1", rec)
    with pytest.raises(ValueError):
        donors.register("blk", "*", "v1", _snap())
    assert donors.find_failure("blk", "*", "v1") is rec
    assert donors.find("blk", "*", "v1") is None
    assert donors.entry_count() == 1


def test_s3_index_failure_register_find_is_and_second_value_error():
    # oracle 대조: C2 'find_failure 는 등록한 그 객체(is)', '같은 키 두 번째 register_failure 도 ValueError'
    donors, _counters = open_run()
    rec = _record("SEAL_VIOLATION")
    donors.register_failure("blk", "*", "v1", rec)
    assert donors.find_failure("blk", "*", "v1") is rec
    with pytest.raises(ValueError):
        donors.register_failure("blk", "*", "v1", _record("SEAL_VIOLATION"))
    assert donors.find_failure("blk", "*", "v1") is rec


def test_s3_index_entry_count_counts_success_and_failure_keys():
    # oracle 대조: (손) C2 'entry_count = 성공 키 수 + 실패 키 수' -- 손으로 등록한 성공 3 + 실패 2 = 5, 거부된 등록은 세지 않는다
    donors, _counters = open_run()
    assert donors.entry_count() == 0
    donors.register("blk", "*", "v1", _snap(version="v1"))
    donors.register("blk", "*", "v2", _snap(version="v2"))
    donors.register("oth", "*", "v1", _snap(writer="oth", version="v1"))
    donors.register_failure("blk", "*", "v3", _record())
    donors.register_failure("oth", "*", "v4", _record())
    assert donors.entry_count() == 5
    with pytest.raises(ValueError):
        donors.register("blk", "*", "v1", _snap(version="v1"))
    assert donors.entry_count() == 5


def test_s3_index_two_open_runs_share_nothing():
    # oracle 대조: C0 '부를 때마다 새 두 객체(항목 0)' -- 한 실행의 등록은 다른 실행 색인에 없다
    d1, _c1 = open_run()
    d2, _c2 = open_run()
    d1.register("blk", "*", "v1", _snap())
    d1.register_failure("blk", "*", "v2", _record())
    assert d2.find("blk", "*", "v1") is None
    assert d2.find_failure("blk", "*", "v2") is None
    assert d2.entry_count() == 0


# =====================================================================================================================
# [XRUN-F1 card C] interface card xrunf1c C9 -- open_bound(total_of)·close_bound()·index_bound(total) (C-T12).
# oracle: (손) 정의 -- index_bound(total) = (등록된 서로 다른 (블록, 분할) 수) × (total + 1). 등록 직후 entry_count() > index_bound(total_of())
# 이면 RuntimeError, 같은 값이면 통과. 한 쌍(blk, "*")만 등록하면 total = 2 -> 상한 = 1 × 3 = 3: 항목 3개까지 통과, 네 번째 RuntimeError.
# 메시지 전문·내부 자료 구조는 단언하지 않는다(C11).
# =====================================================================================================================

def _fill(donors, n, writer="blk", part="*", start=1):
    for k in range(start, start + n):
        v = "v%d" % k
        donors.register(writer, part, v, _snap(writer=writer, version=v))


def test_open_bound_exact_bound_passes_and_one_more_raises():
    donors, _c = open_run()
    donors.open_bound(lambda: 2)                       # 한 쌍 -> 상한 1 × (2 + 1) = 3
    _fill(donors, 3)                                   # 항목 1, 2, 3 -- 3 은 상한과 같다: 통과
    assert donors.entry_count() == 3
    with pytest.raises(RuntimeError):
        _fill(donors, 1, start=4)                      # 항목 4 > 3


def test_open_bound_failures_count_as_entries():
    donors, _c = open_run()
    donors.open_bound(lambda: 2)                       # 상한 3
    donors.register("blk", "*", "v1", _snap(version="v1"))
    donors.register_failure("blk", "*", "v2", _record())
    donors.register_failure("blk", "*", "v3", _record())      # 성공 1 + 실패 2 = 3: 통과
    with pytest.raises(RuntimeError):
        donors.register_failure("blk", "*", "v4", _record())  # 4 > 3


def test_open_bound_bound_grows_with_distinct_block_part_pairs():
    donors, _c = open_run()
    donors.open_bound(lambda: 1)                       # 쌍 하나당 1 × 2 = 2
    _fill(donors, 2, writer="blk")                     # 쌍 1 -> 상한 2, 항목 2: 통과
    _fill(donors, 2, writer="oth")                     # 쌍 2 -> 상한 4, 항목 4: 통과
    assert donors.entry_count() == 4
    donors.register("oth", "p2", "v1", _snap(writer="oth", version="v1"))   # 쌍 3(분할이 다르면 다른 쌍) -> 상한 6, 항목 5: 통과
    donors.register("oth", "p2", "v2", _snap(writer="oth", version="v2"))   # 항목 6 = 상한 6: 통과
    assert donors.entry_count() == 6
    with pytest.raises(RuntimeError):
        donors.register("oth", "p2", "v3", _snap(writer="oth", version="v3"))   # 항목 7 > 6


def test_open_bound_total_none_means_no_check_until_set():
    donors, _c = open_run()
    holder = [None]
    donors.open_bound(lambda: holder[0])
    _fill(donors, 10)                                  # total None: 검사 없음 (상한 3 을 한참 넘는다)
    assert donors.entry_count() == 10
    holder[0] = 2                                      # 정해진 뒤 첫 등록에서 잰다: 상한 3, 항목 11 > 3
    with pytest.raises(RuntimeError):
        _fill(donors, 1, start=11)


def test_open_bound_outside_open_window_no_check():
    donors, _c = open_run()
    _fill(donors, 5)                                   # 열기 전: 검사 없음
    donors.open_bound(lambda: 100)
    donors.close_bound()
    _fill(donors, 3, start=6)                          # 닫은 뒤: 검사 없음
    assert donors.entry_count() == 8
    donors.open_bound(lambda: 0)                       # 다시 열 수 있다: 상한 1 × 1 = 1, 항목 8 -> 다음 등록에서 검사
    with pytest.raises(RuntimeError):
        _fill(donors, 1, start=9)
    donors.close_bound()


def test_open_bound_second_open_before_close_value_error():
    donors, _c = open_run()
    donors.open_bound(lambda: 2)
    with pytest.raises(ValueError):
        donors.open_bound(lambda: 2)
    donors.close_bound()
    donors.open_bound(lambda: 2)                       # 닫은 뒤에는 다시 열린다
    donors.close_bound()


def test_open_bound_index_bound_value_is_pairs_times_total_plus_one():
    donors, _c = open_run()
    assert donors.index_bound(5) == 0                  # 등록된 쌍 0
    _fill(donors, 1, writer="blk")
    assert donors.index_bound(5) == 1 * 6
    _fill(donors, 2, writer="blk", start=2)            # 같은 쌍의 다른 버전: 쌍 수 그대로
    assert donors.index_bound(5) == 1 * 6
    _fill(donors, 1, writer="oth")
    assert donors.index_bound(5) == 2 * 6
    donors.register("oth", "p2", "v1", _snap(writer="oth", version="v1"))
    assert donors.index_bound(0) == 3 * 1
    assert donors.index_bound(7) == 3 * 8
