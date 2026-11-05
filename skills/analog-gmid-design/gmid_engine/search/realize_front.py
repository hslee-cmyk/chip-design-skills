"""front 점의 실현 평가 관문 -- 탐색 front 의 점을 실현 기하(W' = m·w_s)로 다시 평가해 봉인·spec·지배를 다시 거른다 (설계 40 §3.7-A 2-5 (ii), 계획 DEC-105 (2), card WB-1).

진입점: `realize_front(sctx, points) -> RealizeOutcome`. `find_front` 가 `sweep_front` 뒤 front 출력 전에 부른다. 실현을 거치지 않은 점은 front·선택·oracle 입력이 될 수 없다.

* `points` = `FrontPoint` tuple. 점마다 `search_ref` = `point.result.evaluation.snapshot`(탐색 스냅샷 참조), 입력 = `RealizedFinger(search_ref, fp)`,
  fp = (MOS, m, w_s) 열의 지문(평가 키 성분, 값 사본이 아니라 참조 + 지문). 평가 = `evaluate(sctx, θ, cells, origin, realized=)` -- 같은 θ 를 `ctx.base` 에서 따로 시작한다
  (`dc_solve` 가 W' 고정 KCL 을 servo 갈래면 입력 차 미지수로, 입력 고정 갈래면 입력 값 고정으로 다시 풀고 -- 노드 재풀이 없는 갈래는 없다 -- 뒤에 봉인 전 항목을 적용한다. 비수렴·레일 안 근 없음은
  후보 실패 클래스로 `lost`). 선택 함수는 부르지 않는다(실현 평가는 탐색 `dc_finger` 값이 입력).
* 잃는 점(`lost` = ((point_id, 사유, 상세), ...)): 평가가 후보 실패 클래스를 낸 점(봉인 실패·`slice_missing`·`realized_finger_missing` 등), 봉인 아닌 상태, 실현 스냅샷의 피벗 판정이
  탐색 스냅샷과 다른 점(`realized_servo_branch_mismatch`), spec 제약(`spec:`·`ss:`·`ls:` 행)을 못 재거나 c < 0 인 점. `inversion_floor` 행은 읽지 않는다(card 원래 취지와 다름 9).
* 남은 점을 실현 값(전력·면적)으로 비지배 재필터한다(`pareto.nondominated_results`, 탐색 front 와 같은 함수). 지배당한 점은 잃은 점이 아니라 `removed` 다.
* `finger_residual` = 점마다 탐색 `FingerGeom.residual`({MOS: r}) -- 결과 JSON `front[i].finger_residual` 의 출처(이 모듈이 residual 을 읽는 유일한 자리).
"""
import dataclasses

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES, fp_of
from gmid_engine.sizing import REASON_SERVO_BRANCH_MISMATCH, RealizedFinger, is_servo_branch

from .kernel import evaluate
from .pareto import nondominated_results
from .search_values import STATUS_SEALED, FrontPoint

_SPEC_ROWS = ("spec:", "ss:", "ls:")
REASON_NOT_SEALED = "realized_not_sealed"
REASON_SPEC_UNMEASURED = "realized_spec_unmeasured"
REASON_SPEC_VIOLATED = "realized_spec_violated"


@dataclasses.dataclass(frozen=True)
class RealizeOutcome:
    """`points` = 실현 평가 값으로 다시 거른 FrontPoint(`result` 만 실현 평가 값), `lost` = ((point_id, 사유, 상세), ...), `removed` = 실현 값으로 지배당한 ((point_id, 지배한 point_id), ...),
    `finger_residual` = ((point_id, ((MOS, 탐색 residual), ...)), ...) 남은 점의 탐색 residual."""

    points: tuple
    lost: tuple
    removed: tuple = ()
    finger_residual: tuple = ()


def _reason(record):
    detail = dict(record.detail)
    if detail.get("reason"):
        return str(detail["reason"])
    return ("seal_item_" + str(detail["item"])) if "item" in detail else record.failure_class


def _search_fingers(snapshot):
    return tuple(snapshot.column("device", "dc_finger"))


def _judge(point, result):
    """실현 평가 결과 -> (사유, 상세) 또는 None(통과). 상태·피벗 갈래·spec 행."""
    if result.status != STATUS_SEALED:
        if result.failure is not None:
            return _reason(result.failure), result.failure.to_json()
        return REASON_NOT_SEALED, {"status": result.status}
    search_servo = is_servo_branch(point.result.evaluation.snapshot)
    realized_servo = is_servo_branch(result.evaluation.snapshot)
    if search_servo != realized_servo:          # 비교는 갈래(servo / 입력 고정)이지 config 원값이 아니다
        return REASON_SERVO_BRANCH_MISMATCH, {"search_servo": search_servo, "realized_servo": realized_servo}
    if result.unmeasured:
        return REASON_SPEC_UNMEASURED, {"constraints": [list(u) for u in result.unmeasured]}
    violated = [row.name for row in result.constraints if row.name.startswith(_SPEC_ROWS) and row.c < 0]
    if violated:
        return REASON_SPEC_VIOLATED, {"rows": violated}
    return None


def realize_front(sctx, points):
    kept, lost = [], []
    for point in points:
        search = point.result
        fingers = _search_fingers(search.evaluation.snapshot)
        fp = fp_of(("realized", tuple((m, f.m, f.w_f_m) for m, f in fingers)))
        try:
            result = evaluate(sctx, search.theta, search.key.cells, origin=(("stage", "realize"), ("search_point", point.point_id)),
                              realized=RealizedFinger(search.evaluation.snapshot, fp))
        except CANDIDATE_FAILURE_CLASSES as exc:
            lost.append((point.point_id, _reason(exc.record), exc.record.to_json()))
            continue
        verdict = _judge(point, result)
        if verdict is not None:
            lost.append((point.point_id, verdict[0], verdict[1]))
            continue
        kept.append((point, result, tuple((m, f.residual) for m, f in fingers)))
    pool = tuple((point.point_id, result) for point, result, _r in kept)
    ordered = nondominated_results(pool, sctx.domain.area_resolution_m2)
    by = {i: pool[k][0] for i, k in ordered.dominated}
    survivors = tuple(FrontPoint(kept[i][0].point_id, kept[i][1], kept[i][0].origin, None) for i in ordered.kept)
    removed = tuple((pool[i][0], by[i]) for i in sorted(by))
    residual = tuple((kept[i][0].point_id, kept[i][2]) for i in ordered.kept)
    return RealizeOutcome(survivors, tuple(lost), removed, residual)
