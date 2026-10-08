"""봉인 게이트 -- 9항목을 모두 재고 봉인 스냅샷으로 승격하거나 구조화 실패를 낸다 (계획 N3.6, DEC-67, N3.14, 설계 3.6).

진입점: `seal_dc(snapshot, calls, lut, resistances, linear_devices) -> DcEvaluation`.

1. `dc_tolerances` -> 봉인 1·2·3·6·7·8·[r8] 9(전도 여유) 계산 블록(필드마다 기록, 첫 실패에서 멈추지 않는다).
2. 봉인 4(`seal_versions`, 이번 평가의 모든 dc 블록 호출 `calls` + 1 의 블록) · 봉인 5(`seal_writers`).
3. `dc_seal_report` 가 묶음을 graph 에 쓴다.
4. 판정: violated -> `SealViolationError`(devices·margin = margin 이 가장 큰 fail 항목, detail = item·사유·전 항목 요약 --
   모든 항목 결과를 남긴다). undefined(fail 없음, 미정 있음 -- 예: VDSAT 열이 없는 LUT 세트의 항목 7, 셀 미정 tol) -> `DcEvaluation(sealed=None)`.
   sealed -> `DcEvaluation(sealed=SealedSnapshot)`.
"""
import math

from gmid_engine.core import SealViolationError

from .s2_values import DC_KEY, REPORT_SEALED, REPORT_VIOLATED, SEAL_FAIL, DcEvaluation, SealedSnapshot
from .seal_bulk_reverse import dc_seal_bulk_reverse
from .seal_conduction import dc_seal_conduction
from .seal_kcl import dc_seal_kcl
from .seal_kvl_branch import dc_seal_kvl_branch
from .seal_node_conflict import dc_seal_node_conflict
from .seal_report import dc_seal_report
from .seal_saturation import dc_seal_saturation
from .seal_tolerances import dc_tolerances
from .seal_versions import seal_versions
from .seal_vgs_match import dc_seal_vgs_match
from .seal_writers import seal_writers


def seal_dc(snapshot, calls, lut, resistances, linear_devices):
    steps = (
        (dc_tolerances, (lut,)),
        (dc_seal_node_conflict, ()),
        (dc_seal_vgs_match, ()),
        (dc_seal_kcl, (resistances,)),
        (dc_seal_bulk_reverse, ()),
        (dc_seal_saturation, (linear_devices, lut)),
        (dc_seal_kvl_branch, ()),
        (dc_seal_conduction, (lut,)),
    )
    calls = tuple(calls)
    for block, extras in steps:
        snapshot = block(snapshot, *extras)
        calls += ((block, extras),)
    item4 = seal_versions(snapshot, calls)
    item5 = seal_writers(snapshot)
    snapshot = dc_seal_report(snapshot, item4, item5)
    report = snapshot.value("graph", DC_KEY, "dc_seal_report")
    if report.status == REPORT_VIOLATED:
        failed = [item for item in report.items if item.status == SEAL_FAIL]
        worst = max(failed, key=lambda item: (math.inf if item.margin is None else item.margin, item.item))
        summary = tuple((item.item, item.status, item.margin) for item in report.items)
        raise SealViolationError(devices=worst.devices, margin=worst.margin,
                                 detail={"item": worst.item, "nodes": worst.nodes, "items": summary,
                                         "item_detail": worst.detail})
    sealed = SealedSnapshot(snapshot, report) if report.status == REPORT_SEALED else None
    return DcEvaluation(snapshot, report, sealed)
