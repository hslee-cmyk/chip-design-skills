"""CONTRACT §4.3·4.4 FAILURE_CLASSES 분류표·CANDIDATE_FAILURE_CLASSES·UNEXPECTED_EXIT_CODE."""
import collections.abc

import pytest

from gmid_engine.core import (
    CANDIDATE_FAILURE_CLASSES,
    FAILURE_CLASSES,
    UNEXPECTED_EXIT_CODE,
    FailureClass,
    InfeasibleSizingError,
    InfeasibleTargetError,
    NonconvergentError,
    SchemaRejectedError,
    SealViolationError,
    SearchFailedError,
    StructureUnresolvedError,
)

# (key, exc, exit_code(§4.5), parent, recorded_in_search) -- 계약 문장에서 옮긴 기대값
EXPECTED = {
    "STRUCTURE_UNRESOLVED": (StructureUnresolvedError, 2, None, False),
    "INFEASIBLE_TARGET": (InfeasibleTargetError, 3, None, False),
    "NONCONVERGENT": (NonconvergentError, 4, None, True),
    "SEAL_VIOLATION": (SealViolationError, 5, None, True),
    "SEARCH_FAILED": (SearchFailedError, 6, None, False),
    "SCHEMA_REJECTED": (SchemaRejectedError, 7, None, False),
    "structure_inconsistent": (None, None, "STRUCTURE_UNRESOLVED", True),
    "local_infeasible": (None, None, "SEAL_VIOLATION", True),
}


def test_is_mapping_with_exactly_8_keys():
    assert isinstance(FAILURE_CLASSES, collections.abc.Mapping)
    assert set(FAILURE_CLASSES) == set(EXPECTED)
    assert len(FAILURE_CLASSES) == 8


@pytest.mark.parametrize("key", sorted(EXPECTED))
def test_entry_fields(key):
    exc, code, parent, recorded = EXPECTED[key]
    fc = FAILURE_CLASSES[key]
    assert isinstance(fc, FailureClass)
    assert fc.exc is exc
    assert fc.exit_code == code
    assert fc.parent == parent
    assert fc.recorded_in_search is recorded


def test_failure_class_field_order():
    fc = FailureClass(NonconvergentError, 4, None, True)
    assert (fc.exc, fc.exit_code, fc.parent, fc.recorded_in_search) == (NonconvergentError, 4, None, True)


def test_candidate_parents_are_registered_classification_keys():
    for key in ("structure_inconsistent", "local_infeasible"):
        parent = FAILURE_CLASSES[key].parent
        assert parent in FAILURE_CLASSES
        assert FAILURE_CLASSES[parent].parent is None


def test_class_key_matches_exception_failure_class():
    for key, fc in FAILURE_CLASSES.items():
        if fc.exc is not None:
            assert fc.exc.failure_class == key


def test_read_only_assignment_rejected():
    with pytest.raises(TypeError):
        FAILURE_CLASSES["NEW"] = FailureClass(None, None, None, False)
    with pytest.raises(TypeError):
        FAILURE_CLASSES["NONCONVERGENT"] = FailureClass(None, None, None, False)
    assert len(FAILURE_CLASSES) == 8
    assert FAILURE_CLASSES["NONCONVERGENT"].exc is NonconvergentError


def test_base_not_registered():
    assert all(fc.exc is not InfeasibleSizingError for fc in FAILURE_CLASSES.values())


def test_exit_codes_distinct_and_not_unexpected():
    codes = [fc.exit_code for fc in FAILURE_CLASSES.values() if fc.exit_code is not None]
    assert sorted(codes) == [2, 3, 4, 5, 6, 7]
    assert UNEXPECTED_EXIT_CODE not in codes


def test_unexpected_exit_code_is_one():
    assert UNEXPECTED_EXIT_CODE == 1


def test_candidate_failure_classes_exact_tuple():
    assert type(CANDIDATE_FAILURE_CLASSES) is tuple
    assert CANDIDATE_FAILURE_CLASSES == (NonconvergentError, SealViolationError)
    assert InfeasibleSizingError not in CANDIDATE_FAILURE_CLASSES
    assert SchemaRejectedError not in CANDIDATE_FAILURE_CLASSES
