"""공통 실패 규약 -- N3.14 예외 클래스·분류표·exit code (계획 N3.14, 설계 00-common §7.1; 위치는 core 층 0 -- 설계 요건 5절 C4).

진입점: `exit_code_for(exc) -> int`.

* 예외 클래스 이름은 계획 N3.14 표 그대로다. `SchemaRejectedError` 만 `Exception` 직접 하위이고 나머지는
  `InfeasibleSizingError(ValueError)` 하위다.
* 모든 예외는 `.record: FailureRecord` 를 갖는다(키워드 인자 devices·margin·detail 로 만든다).
* exit code 는 N3.14 표의 '분류 순서대로 배정' 규칙을 순서 tuple `_EXIT_ORDER` 의 위치로 계산한다
  (숫자를 박지 않는다 -- WP-03). 예상 밖 예외가 첫 자리(= 1).
* 탐색 루프는 `CANDIDATE_FAILURE_CLASSES` 만 이름으로 잡는다(기반 `InfeasibleSizingError` 를 잡지 않는다).
"""
import dataclasses
import types

from .failure_record import FailureRecord

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


def _make_record(cls, devices, margin, detail):
    key = cls.failure_class
    if key is None:
        raise TypeError(
            cls.__qualname__ + " 은 기반 클래스라 직접 만들지 않는다 -- N3.14 분류 하위 클래스를 쓸 것"
        )
    return FailureRecord(key, devices, margin, () if detail is None else detail)


class InfeasibleSizingError(ValueError):
    """N3.14 분류 예외의 기반(직접 생성·raise 금지, 탐색 루프가 잡지 않는다)."""

    failure_class = None

    def __init__(self, *, devices=(), margin=None, detail=None):
        self.record = _make_record(type(self), devices, margin, detail)
        super().__init__(str(self.record.to_json()))


class StructureUnresolvedError(InfeasibleSizingError):
    """STRUCTURE_UNRESOLVED -- review_needed 잔존·undetermined·unsupported_rule_branch 등. 탐색 시작 전 정지."""

    failure_class = "STRUCTURE_UNRESOLVED"


class InfeasibleTargetError(InfeasibleSizingError):
    """INFEASIBLE_TARGET -- GB4 달성 불가, DOF overconstrained. 탐색 시작 전 정지."""

    failure_class = "INFEASIBLE_TARGET"


class NonconvergentError(InfeasibleSizingError):
    """NONCONVERGENT -- 순환 블록 반복 상한 도달. 탐색 중이면 실패 기록(margin = 잔차 / tol_V)."""

    failure_class = "NONCONVERGENT"


class SealViolationError(InfeasibleSizingError):
    """SEAL_VIOLATION -- 봉인 항목 위반. 탐색 중이면 실패 기록(margin = 위반 크기 / 허용오차)."""

    failure_class = "SEAL_VIOLATION"


class SearchFailedError(InfeasibleSizingError):
    """SEARCH_FAILED -- 모든 시작점에서 feasible 없음."""

    failure_class = "SEARCH_FAILED"


class SchemaRejectedError(Exception):
    """SCHEMA_REJECTED -- 로드 게이트 거부. `Exception` 직접 하위(ValueError·InfeasibleSizingError 하위가 아니다)."""

    failure_class = "SCHEMA_REJECTED"

    def __init__(self, *, devices=(), margin=None, detail=None):
        self.record = _make_record(type(self), devices, margin, detail)
        super().__init__(str(self.record.to_json()))


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


FAILURE_CLASSES = _failure_table()

CANDIDATE_FAILURE_CLASSES = tuple(
    entry.exc
    for _, entry in sorted(FAILURE_CLASSES.items())
    if entry.exc is not None and entry.recorded_in_search
)

_EXIT_BY_CLASS = types.MappingProxyType(
    {entry.exc: entry.exit_code for entry in FAILURE_CLASSES.values() if entry.exc is not None}
)

_UNEXPECTED_EXIT_CODE = _exit_code(None)


def exit_code_for(exc):
    """예외 `exc` 의 파이프라인 exit code. MRO 앞에서부터 분류표에 등록된 첫 클래스의 code, 없으면 예상 밖(1)."""
    if not isinstance(exc, BaseException):
        raise TypeError("exit_code_for 는 예외 인스턴스를 받는다")
    for cls in type(exc).__mro__:
        code = _EXIT_BY_CLASS.get(cls)
        if code is not None:
            return code
    return _UNEXPECTED_EXIT_CODE
