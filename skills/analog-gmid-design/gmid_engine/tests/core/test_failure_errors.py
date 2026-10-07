"""CONTRACT §4.2 N3.14 예외 클래스 -- 계층, 키워드 전용 생성, .record, 기반 클래스 직접 생성 거부."""
import pytest

from gmid_engine.core import (
    FailureRecord,
    InfeasibleSizingError,
    InfeasibleTargetError,
    NonconvergentError,
    SchemaRejectedError,
    SealViolationError,
    SearchFailedError,
    StructureUnresolvedError,
)

TABLE = [
    (StructureUnresolvedError, "STRUCTURE_UNRESOLVED"),
    (InfeasibleTargetError, "INFEASIBLE_TARGET"),
    (NonconvergentError, "NONCONVERGENT"),
    (SealViolationError, "SEAL_VIOLATION"),
    (SearchFailedError, "SEARCH_FAILED"),
    (SchemaRejectedError, "SCHEMA_REJECTED"),
]
SIZING_SUBS = [c for c, _ in TABLE if c is not SchemaRejectedError]


def test_base_is_value_error():
    assert issubclass(InfeasibleSizingError, ValueError)


@pytest.mark.parametrize("cls", SIZING_SUBS)
def test_sizing_subclasses(cls):
    assert issubclass(cls, InfeasibleSizingError)
    assert issubclass(cls, ValueError)


def test_schema_rejected_bases_exactly_exception():
    assert SchemaRejectedError.__bases__ == (Exception,)
    assert not issubclass(SchemaRejectedError, ValueError)
    assert not issubclass(SchemaRejectedError, InfeasibleSizingError)


@pytest.mark.parametrize("cls, key", TABLE)
def test_failure_class_attribute_and_record(cls, key):
    assert cls.failure_class == key
    e = cls()
    assert isinstance(e.record, FailureRecord)
    assert e.record.failure_class == key == e.failure_class
    assert e.record.devices == ()
    assert e.record.margin is None


@pytest.mark.parametrize("cls, key", TABLE)
def test_keyword_args_flow_into_record(cls, key):
    e = cls(devices=("m2", "m1", "m2"), margin=2, detail={"b": 1, "a": "x"})
    assert e.record.devices == ("m1", "m2")
    assert e.record.margin == 2.0 and type(e.record.margin) is float
    assert e.record.detail == (("a", "x"), ("b", 1))
    assert e.record.to_json()["class"] == key


@pytest.mark.parametrize("cls, key", TABLE)
def test_raisable_and_catchable(cls, key):
    with pytest.raises(cls) as ei:
        raise cls(devices=("m1",))
    assert ei.value.record.failure_class == key


@pytest.mark.parametrize("cls", SIZING_SUBS)
def test_caught_as_base(cls):
    with pytest.raises(InfeasibleSizingError):
        raise cls()


@pytest.mark.parametrize("cls, key", TABLE)
def test_positional_arg_rejected(cls, key):
    with pytest.raises(TypeError):
        cls("message")


def test_base_direct_construction_rejected():
    with pytest.raises(TypeError):
        InfeasibleSizingError()
    with pytest.raises(TypeError):
        InfeasibleSizingError(devices=("m1",))
