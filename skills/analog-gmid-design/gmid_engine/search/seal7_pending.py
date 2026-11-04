"""★ 봉인 7 대기 스위치 -- 이 파일 하나가 '봉인 7 미정'을 다룬다 (sizing CONTRACT 6절·12절 O1, 계획 DEC-88).

진입점: `seal_status(evaluation) -> str`(search_values `STATUS_*`).

* `STATUS_SEALED`: `evaluation.sealed` 가 있다(8항목 pass) -> 최종 front 후보.
* `STATUS_PENDING_SEAL7`: 보고서가 undefined 이고 **미정 항목이 봉인 7 하나뿐이며 그 사유가 VDSAT 열 부재**
  (`REASON_VDSAT_MISSING`)다. 탐색은 이 점을 따라가지만(제약·목적이 정의된다) **최종 front 에 넣지 않는다** -- 후보는
  `SearchFront.pending_front` 에 '봉인 7 대기'로만 남는다. 봉인 7 을 통과로 치거나 2/(gm/ID) 로 대신하지 않는다(우회 없음).
* `STATUS_UNDEFINED`: 그 밖 미정(봉인 7 이 다른 사유로 미정이거나 다른 항목이 미정) -> front 후보 아님.

**스위치가 꺼지는 조건(코드 변경 없음)**: lut 에 VDSAT 접근자가 생겨 `dc_seal_region` 이 봉인 7 판정을 실제로 재면 봉인 7 이
pass/fail 을 내고 `REASON_VDSAT_MISSING` 사유가 사라진다 -> 이 함수는 `STATUS_PENDING_SEAL7` 을 더 내지 않고(발동 0),
모든 점이 `STATUS_SEALED` 또는 실패로 갈린다. 그때 이 파일은 지워도 되는 무동작 상태가 된다.
"""
from gmid_engine.sizing import (
    REASON_VDSAT_MISSING,
    REPORT_SEALED,
    REPORT_UNDEFINED,
    SEAL_SATURATION,
    SEAL_UNDEFINED,
    DcEvaluation,
)

from .search_values import STATUS_PENDING_SEAL7, STATUS_SEALED, STATUS_UNDEFINED


def seal_status(evaluation):
    if not isinstance(evaluation, DcEvaluation):
        raise TypeError("seal_status: DcEvaluation 을 받는다")
    report = evaluation.report
    if report.status == REPORT_SEALED and evaluation.sealed is not None:
        return STATUS_SEALED
    if report.status != REPORT_UNDEFINED:
        raise ValueError("seal_status: 위반 보고서는 size_and_seal 이 예외로 낸다 -- 여기 올 수 없다: " + repr(report.status))
    undefined = tuple(item for item in report.items if item.status == SEAL_UNDEFINED)
    only_seal7 = len(undefined) == 1 and undefined[0].item == SEAL_SATURATION
    if only_seal7 and dict(undefined[0].detail).get("reason") == REASON_VDSAT_MISSING:
        return STATUS_PENDING_SEAL7
    return STATUS_UNDEFINED
