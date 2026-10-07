"""CONTRACT §5.2 WriterPermissionError -- Exception 하위, N3.14 실패 클래스가 아니다."""
import pytest

from gmid_engine.core import (
    CANDIDATE_FAILURE_CLASSES,
    FAILURE_CLASSES,
    InfeasibleSizingError,
    WriterPermissionError,
    exit_code_for,
)


def test_is_exception_not_n314():
    assert issubclass(WriterPermissionError, Exception)
    assert not issubclass(WriterPermissionError, InfeasibleSizingError)
    assert WriterPermissionError not in CANDIDATE_FAILURE_CLASSES
    assert all(fc.exc is not WriterPermissionError for fc in FAILURE_CLASSES.values())


def test_exit_code_is_unexpected():
    assert exit_code_for(WriterPermissionError("x")) == 1


def test_raise_and_catch():
    with pytest.raises(WriterPermissionError):
        raise WriterPermissionError("no permission")
