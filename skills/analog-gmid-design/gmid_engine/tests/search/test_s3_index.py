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
