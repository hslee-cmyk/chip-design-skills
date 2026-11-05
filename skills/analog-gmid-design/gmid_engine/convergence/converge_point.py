"""front 점 하나의 사이징↔레이아웃 수렴 루프 (계획 N3.17 LY1·LY3·LY5·LY7·LY8, DEC-84·89·91, 설계 40 §3.9 MOD8 알고리즘 (1)~(3)).

진입점: `converge_point(sctx, pdk, point) -> ConvergedPoint`.

`sctx` = 탐색 컨텍스트(커널 컨텍스트·평가 캐시·계수), `pdk` = `layout.LayoutPdk`(폭 키 후보 -- 호출부가 만든다), `point` = `search.FrontPoint`(봉인된 front 점).
`run_layout` 의 유일한 프로덕션 호출처(`place_layout` 이 부른다)이자 `evaluate(geometry=)` 의 유일한 호출처다.

루프(점마다, 평가 커널 호출은 모두 `evaluate` 한 곳):
1. 현재 점(처음엔 front 점)의 봉인 스냅샷으로 `LayoutInput` 을 만들어 레이아웃을 놓는다(`place_layout` -- 폭 키 좁히기·완화 판정 포함, 커널 0). 레이아웃 필드는
   그 설계점 스냅샷의 S2 `layout` 필드다(설계 40 v1.6 §2.4.7): 같은 현재 점에서의 재시도(거부·키 제외)는 앞 레이아웃 스냅샷 위에, 새 현재 점은 그 설계점 스냅샷 위에 쓴다.
2. 실효 배치에서 `RealizedGeometry`(실현 W 고정 입력 + 실현 폭 슬라이스 + 실현 확산 기하)를 만든다. **이 기하가 직전에 평가한 기하와 같으면 고정점이다**
   (그 평가 점으로 놓은 레이아웃이 같은 기하를 낳음) -> 수렴.
3. 아니면 같은 θ·L 칸으로 그 기하를 고정해 평가 커널 1회 + 봉인 1~8(+ spec 제약 행)을 다시 돈다(LY7 -- W_request 유무와 관계없이 레이아웃 결과마다 1회). 통과하면 그 점이
   새 현재 점이다. 위반하면 W_request 응답 대기 그룹(cc_nf)의 요청을 **거부**(`rejected_requests`)하고 같은 현재 점에서 1 로 돌아간다 -- 레이아웃이 그 그룹을 W_request 로 못 내므로
   LY5 완화 판정(`relaxation_decision`)으로 간다. 거부할 요청이 없으면 사이징 W 어긋남이 가장 큰 kind 의 지금 폭 키를 레이아웃 후보에서 빼고(`key_exclusion`, 단조 감소)
   같은 현재 점에서 1 로 돌아간다. 뺄 키가 남지 않으면 `STATUS_INFEASIBLE`.
같은 상태에서 이미 평가한 DC 상태(고정 W·폭 슬라이스; 직전 것은 확산 기하만 바뀌는 재평가라 제외)로 돌아오면(주기) 바로 NONCONVERGENT 다(결정론적 사상이라 K_max 까지 돌아도 벗어나지 못한다).
반복 상한 `K_max` = `w_loop_bound`(첫 레이아웃에서 한 번, 키 제외 재시도는 세지 않는다 -- 그것은 PDK 폭 키 수로 끝난다): 재평가가 K_max 번째까지 가고도 고정점이 아니면 `STATUS_NONCONVERGENT`(FailureRecord NONCONVERGENT).
레이아웃 안 재시도(폭 키 좁히기·완화)는 평가 커널을 부르지 않는다. 결과의 `kernel_calls` 는 이 점이 새로 부른 커널 호출 수(캐시 적중은 세지 않는다).
"""
import dataclasses

from gmid_engine.core import NonconvergentError
from gmid_engine.layout import F_FLOORPLAN, F_GROUPS, F_ROW_GROUPS, LAYOUT_KEY, passives_from_decl
from gmid_engine.metrics import PassiveAreaDecl
from gmid_engine.search import STATUS_SEALED, evaluate

from .convergence_values import (
    STATUS_CONVERGED,
    STATUS_INFEASIBLE,
    STATUS_NONCONVERGENT,
    STATUS_UNPLACEABLE,
    ConvergedPoint,
    Iteration,
)
from .junction_change import junction_change
from .key_exclusion import key_exclusion
from .place_layout import place_layout
from .realized_geometry import realized_geometry
from .relaxation_records import relaxation_records
from .w_loop_bound import w_loop_bound

_ORIGIN = (("stage", "mod8"),)


def _passives(sctx, result):
    """판정 축 면적 입력의 수동소자 값 = 그 평가 스냅샷의 GB5 필드 `device.passive_value`(다시 계산하지 않는다, 설계 40 §2.4.8)."""
    decl = sctx.area_decl if sctx.area_decl is not None else PassiveAreaDecl()
    return passives_from_decl(decl, dict(result.evaluation.snapshot.column("device", "passive_value")))


def _accepted(result, start):
    """재검증 통과 = 봉인 상태이고, 제약 행이 모두 c >= 0 이고, 출발 점이 재던 spec 제약을 잃지 않는다(새 미측정 (metric, 연산) 없음 -- 사유 문자열은 비교하지 않는다)."""
    lost = {u[:2] for u in result.unmeasured} - {u[:2] for u in start.unmeasured}
    return result.status == STATUS_SEALED and not lost and all(row.c >= 0 for row in result.constraints)


def _margin(result):
    if result.failure is not None:
        return result.failure.margin
    return min((row.c for row in result.constraints), default=None)


def converge_point(sctx, pdk, point):
    start = point.result
    ops = dict(start.evaluation.snapshot.column("device", "dc_op"))
    kinds = {m: op.kind for m, op in ops.items()}
    sized_w = {m: op.W for m, op in ops.items()}
    memo = sctx.dc.lut.memo
    kernel0 = sctx.counters["kernel_calls"]

    narrowed, excluded = {}, []

    def done(status, current, placed, geometry, iterations, k_max, failure, rejected, relaxed, first_seen, layouts, notes=()):
        layout = None if placed is None else placed.layout
        verified = current if current is not start else None
        area = None if layout is None else layout.snapshot.value("graph", LAYOUT_KEY, F_FLOORPLAN).outline_area_m2
        junction = () if verified is None else junction_change(start.evaluation.snapshot, verified.evaluation.snapshot)
        seen = {} if placed is None else first_seen
        records = () if placed is None else relaxation_records(seen, layout, relaxed)
        unmatched = () if layout is None else tuple((g.gid, g.role, g.reason) for g in layout.snapshot.value("graph", LAYOUT_KEY, F_GROUPS)
                                                    if g.pattern is None)
        return ConvergedPoint(point.point_id, status, point, verified, layout, geometry, start.objectives.area_m2, area,
                              None if verified is None else verified.objectives.power_w,
                              None if verified is None else verified.objectives.power_resolution_w, k_max, tuple(iterations),
                              records, tuple(sorted(rejected)), tuple(sorted(narrowed.items())), tuple(excluded), junction, unmatched,
                              () if placed is None else placed.undelivered, sctx.counters["kernel_calls"] - kernel0, layouts,
                              failure, tuple(notes))

    nonpositive = tuple(sorted(m for m, op in ops.items() if not op.current > 0))
    if nonpositive:
        return done(STATUS_UNPLACEABLE, start, None, None, (), None, None, (), frozenset(), {}, 0,
                    (("nonpositive_current", nonpositive),))
    current, pdk_now = start, pdk
    excluded_groups = ()                                  # ((행 그룹 rid, (뺀 폭 키, ...)), ...) -- 키 제외는 행 그룹 단위(설계 40 §3.7-A 6)
    rejected, relaxed, first_seen, previous_geometry, previous_layout = frozenset(), frozenset(), {}, None, None
    iterations, k_bound, layouts, visited = [], None, 0, []
    while True:
        placed = place_layout(memo, current.evaluation.snapshot, pdk_now, _passives(sctx, current), rejected, relaxed, first_seen,
                              previous_layout, kinds, excluded_groups, donors=sctx.dc.donors, counters=sctx.dc.counters)
        layouts += placed.layout_calls
        pdk_now, relaxed, first_seen, previous_layout = placed.pdk, placed.relaxed, placed.first_seen, placed.layout
        if placed.unplaced:
            return done(STATUS_UNPLACEABLE, current, placed, None, iterations, k_bound, None, rejected, relaxed, first_seen,
                        layouts, (("unplaced_devices", placed.unplaced),))
        geometry = realized_geometry(placed.layout.snapshot, placed.placements)
        if geometry == previous_geometry:
            return done(STATUS_CONVERGED, current, placed, geometry, iterations, k_bound, None, rejected, relaxed, first_seen, layouts)
        bound, dlnw, tol = w_loop_bound(placed.placements, sized_w)
        if k_bound is None:
            k_bound = bound
        dc_state = geometry.w_request        # 다음 레이아웃은 평가 점의 DC 상태(고정 W)만 읽는다 -- 확산 기하는 출력이다
        cycle = dc_state in visited[:-1]
        if cycle or sum(1 for i in iterations if i.status != "excluded") >= k_bound:
            # 같은 상태(PDK 후보·거부·완화)에서 이미 평가한 DC 상태(고정 W·폭 슬라이스)로 돌아왔다 = 주기 -- 결정론적 반복이라 K_max 까지 돌아도 벗어나지 못한다
            failure = NonconvergentError(devices=tuple(sorted(m for m, _w in geometry.w_request)), margin=dlnw / tol if tol > 0 else None,
                                         detail=(("cycle", cycle), ("k_max", k_bound), ("iterations", len(iterations)), ("width", dlnw),
                                                 ("tol", tol))).record
            return done(STATUS_NONCONVERGENT, current, placed, geometry, iterations, k_bound, failure, rejected, relaxed,
                        first_seen, layouts)
        calls0 = sctx.counters["kernel_calls"]
        result = evaluate(sctx, start.theta, start.key.cells, parent=current, origin=_ORIGIN + (("iter", len(iterations) + 1),),
                          geometry=geometry)
        pending = tuple(sorted(p.name for p in placed.placements if p.pending))
        accepted = _accepted(result, start)
        reject = () if accepted or not pending or set(pending) <= rejected else pending
        status = "sealed" if accepted else ("rejected" if reject else "failed")
        iterations.append(Iteration(len(iterations) + 1, tuple((p.name, p.key, p.n_fingers) for p in placed.placements), pending,
                                    reject, status, sctx.counters["kernel_calls"] - calls0, placed.layout.snapshot.value("graph", LAYOUT_KEY, F_FLOORPLAN).outline_area_m2,
                                    dlnw, None if accepted else _margin(result)))
        if accepted:
            current, previous_geometry = result, geometry
            previous_layout = None                               # 새 설계점: 레이아웃은 그 설계점 스냅샷 위에 다시 쓴다(설계 40 v1.6 §2.4.7, 별도 lineage 없음)
            if not visited or visited[-1] != dc_state:
                visited.append(dc_state)
            continue
        visited.clear()                                          # 상태(후보·거부)가 바뀌면 지나온 기하는 같은 사상의 점이 아니다
        if reject:
            rejected = rejected | frozenset(reject)
            continue
        gone, narrower = key_exclusion(pdk, placed.layout.snapshot.value("graph", LAYOUT_KEY, F_ROW_GROUPS), placed.placements, sized_w,
                                       excluded_groups, dict(current.evaluation.snapshot.column("device", "dc_colour")))
        if narrower is not None:
            excluded.append(gone)
            iterations[-1] = dataclasses.replace(iterations[-1], status="excluded", excluded=(gone,))
            excluded_groups = narrower                       # 그 행 그룹의 후보만 줄인다(다른 행 그룹은 그대로) -- 같은 현재 점에서 다시 놓는다
            continue
        violated = tuple(sorted((row.c, row.name) for row in result.constraints if row.c < 0))
        return done(STATUS_INFEASIBLE, current, placed, geometry, iterations, k_bound, result.failure, rejected, relaxed, first_seen,
                    layouts, (("status", result.status), ("violated_rows", tuple((name, c) for c, name in violated))))
