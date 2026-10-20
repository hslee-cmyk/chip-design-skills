"""N3.14 예외 클래스 모음 -- 데이터 선언 모듈(공개 정의는 예외 클래스뿐) (계획 N3.14, 설계 00-common §7.1; 위치는 core -- 설계 요건 5절 C4).

* 클래스 이름은 계획 N3.14 표 그대로다. `SchemaRejectedError` 만 `Exception` 직접 하위이고 나머지는
  `InfeasibleSizingError(ValueError)` 하위다.
* 모든 예외는 `.record: FailureRecord` 를 갖는다(키워드 인자 devices·margin·detail 로 만든다).
* `from_record(record)`: 두 기반 모두의 classmethod -- 등록된 실패 기록(같은 객체)을 `.record` 로 가진 새 예외(실패 재연, 설계 40 §2.4.4).
* `InfeasibleSizingError.partial`: 후보 실패가 난 평가의 부분 스냅샷 칸(생성 직후 None). 부착은 `failure_partial.attach_partial`.
* 분류표·후보 실패 클래스는 `failure_classes.py`, exit code 는 `exit_code.py`.
"""
from .failure_record import FailureRecord


def _make_record(cls, devices, margin, detail):
    key = cls.failure_class
    if key is None:
        raise TypeError(
            cls.__qualname__ + " 은 기반 클래스라 직접 만들지 않는다 -- N3.14 분류 하위 클래스를 쓸 것"
        )
    return FailureRecord(key, devices, margin, () if detail is None else detail)


def _from_record(cls, record):
    """등록된 `record`(같은 객체)를 `.record` 로 가진 `cls` 예외. 기반 클래스에서 부르면 TypeError."""
    if cls.failure_class is None:
        raise TypeError(cls.__qualname__ + " 은 기반 클래스라 from_record 로 만들지 않는다 -- N3.14 분류 하위 클래스를 쓸 것")
    if not isinstance(record, FailureRecord):
        raise TypeError("from_record: record 는 FailureRecord 여야 한다")
    exc = cls(devices=record.devices, margin=record.margin, detail=record.detail)
    exc.record = record
    return exc


class InfeasibleSizingError(ValueError):
    """N3.14 분류 예외의 기반(직접 생성·raise 금지, 탐색 루프가 잡지 않는다)."""

    failure_class = None

    def __init__(self, *, devices=(), margin=None, detail=None):
        self.record = _make_record(type(self), devices, margin, detail)
        self.partial = None
        super().__init__(str(self.record.to_json()))

    @classmethod
    def from_record(cls, record):
        return _from_record(cls, record)


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

    @classmethod
    def from_record(cls, record):
        return _from_record(cls, record)
