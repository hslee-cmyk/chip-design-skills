"""XRUN-F1 card B interface card C5 -- `attach_partial(exc, snapshot)`·예외 칸 `partial`·`from_record`(B-T15).

oracle 종류:
* (식) C5 원문 -- 'exc 가 InfeasibleSizingError 하위가 아니면 TypeError, snapshot 이 GraphSnapshot 이 아니면 TypeError, exc.partial 이 이미
  있으면 바꾸지 않는다(첫 부착 유지)', 'exc.partial ... InfeasibleSizingError 하위, 생성 직후 None', 'from_record(record) -- classmethod,
  하위 클래스에서 부르면 그 클래스. .record is record'.
* (비교) 부착한 스냅샷 객체와 `is` 비교.
분류 키·클래스 표는 core CONTRACT 4.2(N3.14) 원문을 옮긴 것이다(피검 코드에서 읽지 않는다).
"""
import pytest

from gmid_engine.core import (
    FAILURE_CLASSES,
    FailureRecord,
    GraphSnapshot,
    InfeasibleSizingError,
    InfeasibleTargetError,
    NonconvergentError,
    SchemaRejectedError,
    SealViolationError,
    SearchFailedError,
    StructureUnresolvedError,
    WriterTable,
    attach_partial,
)

# core CONTRACT 4.2 표(N3.14 이름 그대로)
_INFEASIBLE = [
    (StructureUnresolvedError, "STRUCTURE_UNRESOLVED"),
    (InfeasibleTargetError, "INFEASIBLE_TARGET"),
    (NonconvergentError, "NONCONVERGENT"),
    (SealViolationError, "SEAL_VIOLATION"),
    (SearchFailedError, "SEARCH_FAILED"),
]
_ALL = _INFEASIBLE + [(SchemaRejectedError, "SCHEMA_REJECTED")]
_IDS_INF = [c.__name__ for c, _k in _INFEASIBLE]
_IDS_ALL = [c.__name__ for c, _k in _ALL]

_TABLE = WriterTable([("node", "v", "blk")])


def _snap(value):
    return GraphSnapshot.empty(_TABLE).write("blk", "v_%s" % value, {("node", "v"): {"a": value}})


# ---------- 칸 partial ----------

@pytest.mark.parametrize("cls,_key", _INFEASIBLE, ids=_IDS_INF)
def test_failure_partial_new_exception_partial_none(cls, _key):
    # oracle 대조: C5 'exc.partial -> GraphSnapshot | None, InfeasibleSizingError 하위, 생성 직후 None'
    exc = cls(devices=("M1",), detail={"k": "v"})
    assert exc.partial is None


# ---------- attach_partial ----------

@pytest.mark.parametrize("cls,_key", _INFEASIBLE, ids=_IDS_INF)
def test_failure_partial_attach_then_first_kept(cls, _key):
    # oracle 대조: C5 'exc.partial 이 이미 있으면 바꾸지 않는다(첫 부착 유지)'
    exc = cls()
    first, second = _snap(1.0), _snap(2.0)
    assert attach_partial(exc, first) is None
    assert exc.partial is first
    attach_partial(exc, second)
    assert exc.partial is first


@pytest.mark.parametrize("exc", [SchemaRejectedError(), ValueError("x"), RuntimeError("y"), KeyError("z")],
                         ids=["schema_rejected", "value_error", "runtime_error", "key_error"])
def test_failure_partial_rejects_non_infeasible_exc(exc):
    # oracle 대조: C5 'exc 가 InfeasibleSizingError 하위가 아니면 TypeError' -- SchemaRejectedError 는 core CONTRACT 4.2 로 기반이 Exception
    with pytest.raises(TypeError):
        attach_partial(exc, _snap(1.0))


@pytest.mark.parametrize("bad", [None, {"a": 1}, "snapshot", object()], ids=["none", "dict", "str", "object"])
def test_failure_partial_rejects_non_snapshot(bad):
    # oracle 대조: C5 'snapshot 이 GraphSnapshot 이 아니면 TypeError'
    exc = SealViolationError()
    with pytest.raises(TypeError):
        attach_partial(exc, bad)
    assert exc.partial is None


# ---------- from_record ----------

@pytest.mark.parametrize("cls,key", _ALL, ids=_IDS_ALL)
def test_from_record_returns_that_class_with_same_record(cls, key):
    # oracle 대조: C5 'from_record(record) classmethod, 하위 클래스에서 부르면 그 클래스. .record is record' (두 기반 하위 모두)
    rec = FailureRecord(key, devices=("M2", "M1"), margin=-0.25, detail={"why": "hand"})
    exc = cls.from_record(rec)
    assert type(exc) is cls
    assert exc.record is rec


@pytest.mark.parametrize("cls,key", _ALL, ids=_IDS_ALL)
def test_from_record_through_failure_classes_table(cls, key):
    # oracle 대조: C4 단계 3 '클래스 = FAILURE_CLASSES[record.failure_class].exc' 와 C5 from_record 의 합성 -- 표의 클래스가 그 클래스
    rec = FailureRecord(key)
    exc = FAILURE_CLASSES[rec.failure_class].exc.from_record(rec)
    assert type(exc) is cls
    assert exc.record is rec


@pytest.mark.parametrize("cls,key", _INFEASIBLE, ids=_IDS_INF)
def test_from_record_new_exception_partial_none(cls, key):
    # oracle 대조: C5 'exc.partial ... 생성 직후 None' -- from_record 로 만든 예외도 생성 직후다
    exc = cls.from_record(FailureRecord(key))
    assert isinstance(exc, InfeasibleSizingError)
    assert exc.partial is None
