"""봉인 8항목 묶음 계산 블록 (계획 N3.6, 설계 3.6 `seal.py` 의 graph 기록 부분).

진입점: `dc_seal_report`(`@compute_block`) -- `dc_seal_report(snapshot, item4, item5)`.

reads 봉인 1·2·3·6·7·8 필드, extras = 봉인 4·5 결과(메타데이터 검사라 함수가 만든 SealItem). writes `graph.dc_seal_report`
= SealReport(items 항목 순, status): fail 이 하나라도 있으면 violated, 없고 undefined 가 있으면 undefined, 모두 pass 면 sealed.
"""
from gmid_engine.core import compute_block

from .s2_values import (
    DC_KEY,
    DC_SEAL_REPORT_WRITER,
    REPORT_SEALED,
    REPORT_UNDEFINED,
    REPORT_VIOLATED,
    SEAL_FAIL,
    SEAL_UNDEFINED,
    SealReport,
)

ITEM_FIELDS = ("dc_seal_1", "dc_seal_2", "dc_seal_3", "dc_seal_6", "dc_seal_7", "dc_seal_8")
READS = tuple(("graph", field) for field in ITEM_FIELDS)
WRITES = (("graph", "dc_seal_report"),)


@compute_block(DC_SEAL_REPORT_WRITER, reads=READS, writes=WRITES)
def dc_seal_report(projection):
    items = [projection.value("graph", DC_KEY, field) for field in ITEM_FIELDS]
    items.extend(projection.extras)
    items = tuple(sorted(items, key=lambda item: item.item))
    statuses = {item.status for item in items}
    if SEAL_FAIL in statuses:
        status = REPORT_VIOLATED
    elif SEAL_UNDEFINED in statuses:
        status = REPORT_UNDEFINED
    else:
        status = REPORT_SEALED
    return {("graph", "dc_seal_report"): {DC_KEY: SealReport(items, status)}}
