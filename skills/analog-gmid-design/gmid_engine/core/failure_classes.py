"""N3.14 분류표 -- 분류 키마다 예외 클래스·exit code·상위 분류·탐색 중 처리 (계획 N3.14, 설계 00-common §7.1).

데이터 선언 모듈(공개 정의는 dataclass `FailureClass` 뿐).

* exit code 는 N3.14 표의 '분류 순서대로 배정' 규칙을 순서 tuple `_EXIT_ORDER` 의 위치로 계산한다
  (숫자를 박지 않는다 -- WP-03). 예상 밖 예외가 첫 자리(`UNEXPECTED_EXIT_CODE` = 1).
* 탐색 루프는 `CANDIDATE_FAILURE_CLASSES` 만 이름으로 잡는다(기반 `InfeasibleSizingError` 를 잡지 않는다).
"""
import dataclasses
import types

from .failure_errors import (
    InfeasibleTargetError,
    NonconvergentError,
    SchemaRejectedError,
    SealViolationError,
    SearchFailedError,
    StructureUnresolvedError,
)

# N3.14 표의 분류 순서. None = '예상 밖 예외'(exit code 기본값).
_EXIT_ORDER = (
    None,
    "STRUCTURE_UNRESOLVED",
    "INFEASIBLE_TARGET",
    "NONCONVERGENT",
    "SEAL_VIOLATION",
    "SEARCH_FAILED",
    "SCHEMA_REJECTED",
)


@dataclasses.dataclass(frozen=True)
class FailureClass:
    """분류표 한 항목. 후보 실패 레코드(예외 없음)는 exc·exit_code 가 None 이고 parent 가 상위 분류 키다."""

    exc: object
    exit_code: object
    parent: object
    recorded_in_search: bool


def _exit_code(key):
    return _EXIT_ORDER.index(key) + 1


def _failure_table():
    stop, record = False, True
    rows = (
        ("STRUCTURE_UNRESOLVED", StructureUnresolvedError, None, stop),
        ("structure_inconsistent", None, "STRUCTURE_UNRESOLVED", record),
        ("local_infeasible", None, "SEAL_VIOLATION", record),
        ("INFEASIBLE_TARGET", InfeasibleTargetError, None, stop),
        ("NONCONVERGENT", NonconvergentError, None, record),
        ("SEAL_VIOLATION", SealViolationError, None, record),
        ("SEARCH_FAILED", SearchFailedError, None, stop),
        ("SCHEMA_REJECTED", SchemaRejectedError, None, stop),
    )
    table = {}
    for key, exc, parent, recorded in rows:
        code = None if exc is None else _exit_code(key)
        table[key] = FailureClass(exc, code, parent, recorded)
    return types.MappingProxyType(table)


def _candidate_classes(table):
    return tuple(
        entry.exc
        for _, entry in sorted(table.items())
        if entry.exc is not None and entry.recorded_in_search
    )


FAILURE_CLASSES = _failure_table()

CANDIDATE_FAILURE_CLASSES = _candidate_classes(FAILURE_CLASSES)

UNEXPECTED_EXIT_CODE = _exit_code(None)
