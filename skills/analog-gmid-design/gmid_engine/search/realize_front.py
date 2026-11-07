"""front 점의 실현 평가 관문 -- 탐색 front·unmeasured_front 의 점을 실현 기하(W' = m·w_f, m = 칸 단위 실현 정수화)로 다시 평가해 봉인·spec·집합 소속·지배를 다시 거른다
(설계 40 §3.7-A 2-5 (ii)·§3.7-B 4 (ii), 계획 DEC-105 (2)·DEC-108 (5)(6), card WB-1·FS-1).

진입점: `realize_front(sctx, points) -> RealizeOutcome`. `find_front` 가 `sweep_front` 뒤 front 출력 전에 부른다. 실현을 거치지 않은 점은 front·선택·oracle 입력이 될 수 없다.

* `points` = `FrontPoint` tuple(front ∪ unmeasured_front). 점마다 `search_ref` = `point.result.evaluation.snapshot`(탐색 스냅샷 참조), 입력 = `RealizeInput(search_ref)`(지문 = 실현 표지 --
  탐색 스냅샷은 같은 평가 입력의 함수라 평가 키에 덧대지 않는다), 평가 입력 w_f 칸 = 그 탐색 스냅샷이 쓴 칸(`point_wf` -- 사본 없음). 평가 = `evaluate(sctx, θ, cells, wf, origin, realized=)` -- 같은 θ 를
  `ctx.base` 에서 따로 시작한다(`dc_solve` 가 칸마다 `realize_fingers` 로 m 을 정하고, W' 고정 KCL 을 servo 갈래면 입력 차 미지수로, 입력 고정 갈래면 입력 값 고정으로 다시 풀고 -- 노드 재풀이 없는 갈래는
  없다 -- 뒤에 봉인 전 항목을 적용한다. 비수렴·레일 안 근 없음은 후보 실패 클래스로 `lost`).
* 잃는 점(`lost` = ((point_id, 사유, 상세), ...), 상세는 매핑): 평가가 후보 실패 클래스를 낸 점(봉인 실패·`slice_missing`·`realized_finger_missing`·`realize_tie_unresolved` 등), 봉인 아닌 상태,
  실현 스냅샷의 피벗 판정이 탐색 스냅샷과 다른 점(`realized_servo_branch_mismatch`), 측정된 spec 제약(`spec:`·`ss:`·`ls:` 행)의 c < 0 인 점. 미측정 행이 있다는 사실은 손실 사유가 아니다(집합 재분류).
  `inversion_floor` 행은 읽지 않는다(card 원래 취지와 다름 9). 상세에 출력 전용 칸 `small_m` = 그 점 실현 스냅샷(실패면 부분 스냅샷) `dc_finger` 에서 m ≤ 2 인 MOS 이름 정렬 목록(없으면 None) -- 계획 Q-FS1 (2) '작은 m(1~2)' 표지.
* 남은 점을 실현 평가의 측정 상태로 탐색과 같은 S-1 분류(`eps_sweep.classify`)로 다시 나누고, 집합마다 실현 값(전력·면적)으로 비지배 재필터한다(`pareto.nondominated_results`, 탐색 front 와 같은 함수).
  지배당한 점은 잃은 점이 아니라 `removed` 다. 탐색 집합 ≠ 실현 집합인 점은 `moved` = ((point_id, 탐색 집합, 실현 집합), ...) 에 기록한다(손실 아님, 출력 전용). `points` 는 front 집합 점이 먼저, 그다음
  unmeasured_front 집합 점이다.
* `finger_residual` = 점마다 **실현** 스냅샷 `FingerGeom.residual`({MOS: r} = m·w_f/W_θ − 1) -- 결과 JSON `front[i].finger_residual` 의 출처(이 모듈이 residual 을 읽는 유일한 자리).
"""
import dataclasses

from gmid_engine.core import CANDIDATE_FAILURE_CLASSES
from gmid_engine.sizing import REASON_SERVO_BRANCH_MISMATCH, RealizeInput, is_servo_branch

from .eps_sweep import classify
from .kernel import evaluate
from .pareto import nondominated_results
from .point_wf import point_wf
from .search_values import STATUS_SEALED, FrontPoint

_SPEC_ROWS = ("spec:", "ss:", "ls:")
_SETS = ("front", "unmeasured_front")                 # 실현 관문을 거치는 집합(봉인 7 대기 점은 관문 밖)
REASON_NOT_SEALED = "realized_not_sealed"
REASON_SPEC_VIOLATED = "realized_spec_violated"


@dataclasses.dataclass(frozen=True)
class RealizeOutcome:
    """`points` = 실현 평가 값으로 다시 거른 FrontPoint(`result` 만 실현 평가 값; front 집합 점 먼저), `lost` = ((point_id, 사유, 상세), ...), `removed` = 실현 값으로 지배당한 ((point_id, 지배한 point_id), ...),
    `finger_residual` = ((point_id, ((MOS, 실현 residual), ...)), ...) 남은 점의 실현 residual, `moved` = ((point_id, 탐색 집합, 실현 집합), ...) 집합이 바뀐 남은 점(출력 전용)."""

    points: tuple
    lost: tuple
    removed: tuple = ()
    finger_residual: tuple = ()
    moved: tuple = ()


def _reason(record):
    detail = dict(record.detail)
    if detail.get("reason"):
        return str(detail["reason"])
    return ("seal_item_" + str(detail["item"])) if "item" in detail else record.failure_class


def _small_m(snapshot):
    """그 평가 스냅샷 `dc_finger` 에서 손가락 수 m ≤ 2 인 MOS 이름 정렬 목록(출력 전용 표지). 스냅샷이 없거나 `dc_finger` 가 없으면 None."""
    fingers = () if snapshot is None else tuple(snapshot.column("device", "dc_finger"))
    return sorted(m for m, f in fingers if f.m <= 1 + 1) if fingers else None


def _judge(point, result):
    """실현 평가 결과 -> (사유, 상세) 또는 None(통과). 상태·피벗 갈래·측정된 spec 행."""
    if result.status != STATUS_SEALED:
        if result.failure is not None:
            return _reason(result.failure), {**result.failure.to_json(), "small_m": _small_m(result.partial)}
        return REASON_NOT_SEALED, {"status": result.status, "small_m": _small_m(None if result.evaluation is None else result.evaluation.snapshot)}
    snapshot = result.evaluation.snapshot
    search_servo = is_servo_branch(point.result.evaluation.snapshot)
    realized_servo = is_servo_branch(snapshot)
    if search_servo != realized_servo:          # 비교는 갈래(servo / 입력 고정)이지 config 원값이 아니다
        return REASON_SERVO_BRANCH_MISMATCH, {"search_servo": search_servo, "realized_servo": realized_servo, "small_m": _small_m(snapshot)}
    violated = [row.name for row in result.constraints if row.name.startswith(_SPEC_ROWS) and row.c < 0]
    if violated:
        return REASON_SPEC_VIOLATED, {"rows": violated, "small_m": _small_m(snapshot)}
    return None


def realize_front(sctx, points):
    kept, lost = [], []
    for point in points:
        search = point.result
        snapshot = search.evaluation.snapshot
        try:
            result = evaluate(sctx, search.theta, search.key.cells, point_wf(snapshot), origin=(("stage", "realize"), ("search_point", point.point_id)),
                              realized=RealizeInput(snapshot))
        except CANDIDATE_FAILURE_CLASSES as exc:
            lost.append((point.point_id, _reason(exc.record), {**exc.record.to_json(), "small_m": _small_m(exc.partial)}))
            continue
        verdict = _judge(point, result)
        if verdict is not None:
            lost.append((point.point_id, verdict[0], verdict[1]))
            continue
        kept.append((point, result, tuple((m, f.residual) for m, f in result.evaluation.snapshot.column("device", "dc_finger"))))
    survivors, removed, residual, moved = [], [], [], []
    for name in _SETS:                              # 실현 평가의 측정 상태로 다시 나눈 집합마다 실현 값으로 지배 재필터
        group = [entry for entry in kept if classify(entry[1]) == name]
        pool = tuple((point.point_id, result) for point, result, _r in group)
        ordered = nondominated_results(pool, sctx.domain.area_resolution_m2)
        by = {i: pool[k][0] for i, k in ordered.dominated}
        removed.extend((pool[i][0], by[i]) for i in sorted(by))
        for i in ordered.kept:
            point, result, res = group[i]
            survivors.append(FrontPoint(point.point_id, result, point.origin, None))
            residual.append((point.point_id, res))
            searched = classify(point.result)
            if searched != name:
                moved.append((point.point_id, searched, name))
    return RealizeOutcome(tuple(survivors), tuple(lost), tuple(removed), tuple(residual), tuple(moved))
