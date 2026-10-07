"""CONTRACT §4.5 exit_code_for -- 분류 순서대로 2~7, 예상 밖 1, MRO 앞에서부터 등록 클래스, 비예외 인자 TypeError."""
import pytest

from gmid_engine.core import (
    InfeasibleTargetError,
    NonconvergentError,
    SchemaRejectedError,
    SealViolationError,
    SearchFailedError,
    StructureUnresolvedError,
    WriterPermissionError,
    exit_code_for,
)

CODES = [
    (StructureUnresolvedError, 2),
    (InfeasibleTargetError, 3),
    (NonconvergentError, 4),
    (SealViolationError, 5),
    (SearchFailedError, 6),
    (SchemaRejectedError, 7),
]


@pytest.mark.parametrize("cls, code", CODES)
def test_registered_codes(cls, code):
    assert exit_code_for(cls()) == code


def test_all_codes_distinct_including_unexpected():
    codes = [exit_code_for(cls()) for cls, _ in CODES] + [exit_code_for(RuntimeError())]
    assert len(set(codes)) == len(codes) == 7


@pytest.mark.parametrize("cls, code", CODES)
def test_user_subclass_inherits_parent_code(cls, code):
    sub = type("User" + cls.__name__, (cls,), {})
    assert exit_code_for(sub()) == code


def test_grandchild_subclass():
    class A(SealViolationError):
        pass

    class B(A):
        pass

    assert exit_code_for(B()) == 5


@pytest.mark.parametrize(
    "exc",
    [RuntimeError("x"), ValueError("x"), KeyError("x"), TypeError("x"), Exception(), WriterPermissionError("x")],
    ids=["RuntimeError", "ValueError", "KeyError", "TypeError", "Exception", "WriterPermissionError"],
)
def test_unregistered_is_one(exc):
    assert exit_code_for(exc) == 1


@pytest.mark.parametrize(
    "bad",
    [NonconvergentError, RuntimeError, "NONCONVERGENT", 4, None],
    ids=["registered_class_obj", "builtin_class_obj", "str", "int", "None"],
)
def test_non_exception_instance_rejected(bad):
    with pytest.raises(TypeError):
        exit_code_for(bad)
