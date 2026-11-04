"""봉인 게이트 -- 9항목을 모두 재고 봉인 스냅샷으로 승격하거나 구조화 실패를 낸다 (계획 N3.6, DEC-67, N3.14, 설계 3.6).

진입점: `seal_dc(snapshot, calls, lut, resistances, linear_devices, raise_on_violation=True, *, base, donors, counters) -> DcEvaluation`.
`base` = 커널 컨텍스트 `ctx.base`(봉인 4 의 base writer 정본 -- 사본 없음). 기본값 없는 필수 키워드, None 이면 `TypeError`. 봉인 항목 블록 여덟의 구성원·순서는 모듈 상수 `SEAL_ITEM_BLOCKS`(정의 하나).
`donors`·`counters` = 필수 키워드(기본값 없음) -- 호출자(`run_kernel`)가 `KernelContext` 에서 꺼내 넘기는 실행 하나의 블록 결과 색인·계수. 봉인 항목 블록·`dc_seal_report` 에 넘긴다.
위반 예외(`SealViolationError`)에는 `dc_seal_report` 까지 쓴 스냅샷을 부분 스냅샷(`exc.partial`)으로 붙여 낸다(`core.attach_partial`, 설계 40 §2.4.7).
tol_I 의 gm 은 `dc_tolerances` 가 쓴 자기 동작점 `dc_gm`(parent 무관, 설계 40 §3.7-3). `raise_on_violation=False` 면 violated 도 예외 없이 `DcEvaluation(sealed=None)` 으로 낸다
(`size_and_seal_local` 이 항목별 위반 대상을 읽는다 -- 판정 식은 같다).

1. `dc_tolerances` -> 봉인 1·2·3·6·7·8·[r8] 9(전도 여유) 계산 블록(필드마다 기록, 첫 실패에서 멈추지 않는다).
2. 봉인 4(`seal_versions`, 이번 평가의 모든 dc 블록 호출 `calls` + 1 의 블록) · 봉인 5(`seal_writers`).
3. `dc_seal_report` 가 묶음을 graph 에 쓴다.
4. 판정: violated -> `SealViolationError`(devices·margin = margin 이 가장 큰 fail 항목, detail = item·사유·전 항목 요약 --
   모든 항목 결과를 남긴다). undefined(fail 없음, 미정 있음 -- 예: VDSAT 열이 없는 LUT 세트의 항목 7, 셀 미정 tol) -> `DcEvaluation(sealed=None)`.
   sealed -> `DcEvaluation(sealed=SealedSnapshot)`.
"""
import math

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, SealViolationError, attach_partial

from .s2_values import DC_KEY, REPORT_SEALED, REPORT_VIOLATED, SEAL_FAIL, DcEvaluation, SealedSnapshot
from .seal_bulk_reverse import dc_seal_bulk_reverse
from .seal_conduction import dc_seal_conduction
from .seal_kcl import dc_seal_kcl
from .seal_kvl_branch import dc_seal_kvl_branch
from .seal_node_conflict import dc_seal_node_conflict
from .seal_report import dc_seal_report
from .seal_saturation import dc_seal_saturation
from .seal_tolerances import dc_tolerances
from .seal_versions import seal_versions, writers_in_scope
from .seal_vgs_match import dc_seal_vgs_match
from .seal_writers import seal_writers


# 봉인 항목 블록 여덟 -- 구성원·순서의 정의 하나. `seal_dc` 호출 순서와 `run_kernel` 의 derive_child keep(블록 이름)이 모두 이 상수를 읽는다(설계 41 4.7-3c).
SEAL_ITEM_BLOCKS = (
    dc_tolerances,
    dc_seal_node_conflict,
    dc_seal_vgs_match,
    dc_seal_kcl,
    dc_seal_bulk_reverse,
    dc_seal_saturation,
    dc_seal_kvl_branch,
    dc_seal_conduction,
)


def seal_dc(snapshot, calls, lut, resistances, linear_devices, raise_on_violation=True, *, base, donors, counters):
    if base is None:
        raise TypeError("seal_dc: base 는 필수다(봉인 4 (3)(4)의 base writer 정본 -- ctx.base)")
    extras_of = {       # 호출마다 만들고 버리는 인자 매핑(저장 아님)
        dc_tolerances: (lut,),
        dc_seal_node_conflict: (),
        dc_seal_vgs_match: (),
        dc_seal_kcl: (resistances,),
        dc_seal_bulk_reverse: (),
        dc_seal_saturation: (linear_devices, lut),
        dc_seal_kvl_branch: (),
        dc_seal_conduction: (lut,),
    }
    if set(extras_of) != set(SEAL_ITEM_BLOCKS):
        raise ValueError("seal_dc: extras 매핑의 블록이 SEAL_ITEM_BLOCKS 와 다르다")
    calls = tuple(calls)
    for block in SEAL_ITEM_BLOCKS:
        extras = extras_of[block]
        try:
            snapshot = block(snapshot, *extras, donors=donors, counters=counters)
        except CANDIDATE_FAILURE_CLASSES as exc:
            attach_partial(exc, snapshot.derive_child(writers_in_scope(base, (b for b, _ in calls))))      # 봉인 항목 블록 단계 실패: 그 블록에 들어간 스냅샷을 앞 블록 범위로 줄인 것이 부분 스냅샷(X-3)
            raise
        calls += ((block, extras),)
    item4 = seal_versions(snapshot, calls, base)
    item5 = seal_writers(snapshot)
    try:
        snapshot = dc_seal_report(snapshot, item4, item5, donors=donors, counters=counters)
    except CANDIDATE_FAILURE_CLASSES as exc:
        attach_partial(exc, snapshot.derive_child(writers_in_scope(base, (b for b, _ in calls))))
        raise
    report = snapshot.value("graph", DC_KEY, "dc_seal_report")
    if report.status == REPORT_VIOLATED and raise_on_violation:
        failed = [item for item in report.items if item.status == SEAL_FAIL]
        worst = max(failed, key=lambda item: (math.inf if item.margin is None else item.margin, item.item))
        summary = tuple((item.item, item.status, item.margin) for item in report.items)
        violation = SealViolationError(devices=worst.devices, margin=worst.margin,
                                       detail={"item": worst.item, "nodes": worst.nodes, "items": summary,
                                               "item_detail": worst.detail})
        attach_partial(violation, snapshot.derive_child(writers_in_scope(base, [b for b, _ in calls] + [dc_seal_report])))      # 부분 스냅샷 = 보고서까지 쓴 스냅샷을 평가 범위로 줄인 것(X-3)
        raise violation
    sealed = SealedSnapshot(snapshot, report) if report.status == REPORT_SEALED else None
    return DcEvaluation(snapshot, report, sealed)
