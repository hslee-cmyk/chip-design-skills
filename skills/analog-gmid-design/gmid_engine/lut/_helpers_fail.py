"""MOD1 실패 객체 공용 helper -- 로드 거부(`SchemaRejectedError`)와 조회 실패(`SealViolationError`) 레코드 조립.

* `detail` 은 `{"reason": <사유 키>, ...}` 이다. 사유 키 목록은 lut/CONTRACT.md 5절.
* LUT 는 소자 이름을 모른다 -- `devices` 는 비우고, 소자를 아는 호출부(MOD4 이상)가 덧붙여 다시 올린다(P-28 원인 보존).
* margin 은 None: 축 범위·분지 판정에는 허용오차가 없다(N3.14 margin = 위반 크기 / 허용오차 -> 정의 안 됨).
"""
from gmid_engine.core import SchemaRejectedError, SealViolationError


def schema_rejected(reason, **detail):
    """로드 게이트 거부 예외 객체(부르는 쪽이 raise)."""
    return SchemaRejectedError(detail={"reason": reason, **detail})


def seal_violation(reason, **detail):
    """조회 실패 예외 객체(SEAL_VIOLATION 계열, 부르는 쪽이 raise)."""
    return SealViolationError(detail={"reason": reason, **detail})
