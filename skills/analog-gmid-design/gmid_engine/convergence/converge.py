"""MOD8 수렴 -- front 점마다 사이징↔레이아웃 W_request 루프, 판정 축 재필터, 교대 (계획 N3.17 LY1~LY8, DEC-79·84·89·91, LR9, 설계 40 §3.9 MOD8, D-M8·R12).

진입점: `converge(sctx, pdk_decl, points, pool=(), slice_keys=None) -> ConvergedFront`.

호출 순서 (U16 `run_gmid_design_pipeline` 이 부른다): `front = find_front(sctx, starts)` -> `converge(sctx, pdk_decl, front.front)` -> `.front` 가 최종 front.

* `sctx` = `search.build_search_context` 결과, `pdk_decl` = core `read_pdk_decl` 결과(레이아웃 PDK 규칙·제조 격자 -- `LayoutPdk.from_decl`), `points` = 봉인된 `search.FrontPoint`
  (`SearchFront.front` 또는 `.unmeasured_front` -- 호출부가 고른다. 봉인 7 대기 점은 재검증할 봉인 스냅샷이 없어 받지 않는다. 미측정 제약은 재검증 점이 늘리지 않는 한 그대로 둔다), `pool` = 교대 후보 `FrontPoint`(탐색 축에서 지배당한 봉인 점;
  기본 비어 있음), `slice_keys` = None 또는 ((kind, (폭 키, ...)), ...) -- 레이아웃의 폭 키 후보를 줄인다(None = PDK 특성화 폭 전부; 슬라이스마다 LUT tol_V 표를 처음 한 번 만드는
  비용이 크다).
* 순서: (1) 점마다 `converge_point` (2) 수렴한 점의 (전력, 레이아웃 면적)으로 `refilter` (3) 첫 재필터 뒤 `alternation_bound` 로 K_alt, pool 후보 중 `admit_candidates` 가 뽑은 점이
  있으면 (1) 로 돌아가 그 점을 수렴시키고 다시 거른다 -- 재실행이 K_alt 번이 되도록 후보가 남으면 교대 NONCONVERGENT 를 `notes` 에 남긴다. 수렴하지 못한 점은 `nonconverged` 에 상태별로 남고
  재필터에는 들지 않는다. `front` = 마지막 재필터 통과 점.
* 판정 축 값·탐색 축 값·차는 점마다 `ConvergedPoint` 에, 판정 축 포함 항목(DEC-79)은 `notes` 의 `judged_axis` 에 적는다.
"""
import dataclasses
import time

from gmid_engine.layout import F_FLOORPLAN, LAYOUT_KEY, LayoutPdk
from gmid_engine.search import STATUS_SEALED

from .admission import admit_candidates
from .alternation_bound import alternation_bound
from .convergence_values import (
    DROP_DOMINATED,
    DROP_FOLDED,
    DROP_NONCONVERGED,
    STATUS_CONVERGED,
    ConvergedFront,
    DroppedPoint,
)
from .converge_point import converge_point
from .refilter import refilter


def _restrict(pdk, slice_keys):
    if slice_keys is None:
        return pdk
    pick = dict(slice_keys)
    keys = tuple((kind, tuple(sorted(pick[kind])) if kind in pick else tuple(ks)) for kind, ks in pdk.slice_width_keys)
    return dataclasses.replace(pdk, slice_width_keys=keys)


def _eligible(candidate):
    result = candidate.result
    return (result is not None and result.status == STATUS_SEALED and result.evaluation is not None
            and result.evaluation.sealed is not None and all(row.c >= 0 for row in result.constraints))


def converge(sctx, pdk_decl, points, pool=(), slice_keys=None):
    started = time.perf_counter()
    kernel0 = sctx.counters["kernel_calls"]
    pdk = _restrict(LayoutPdk.from_decl(sctx.dc.lut.memo.lut, pdk_decl), slice_keys)
    points = tuple(points)
    for p in points:
        if not _eligible(p):
            raise ValueError("converge: 봉인되고 모든 제약 행이 c >= 0 인 점만 받는다: " + repr(p.point_id))
    queue = {p.point_id: p for p in pool if _eligible(p)}
    for p in points:
        queue.pop(p.point_id, None)
    done, order, admitted, notes = {}, [], [], []
    todo, rounds, k_alt = points, 0, None
    while True:
        for p in todo:
            done[p.point_id] = converge_point(sctx, pdk, p)
            order.append(p.point_id)
        rounds += 1
        converged = tuple(done[i] for i in order if done[i].status == STATUS_CONVERGED)
        kept, dominated, folded = refilter(converged) if converged else ((), (), ())
        if k_alt is None and converged:
            k_alt = alternation_bound(converged)
        survivors = tuple(done[i] for i in kept)
        candidates = admit_candidates(survivors, tuple(queue.values()))
        if not candidates:
            break
        if rounds - 1 >= k_alt:
            notes.append((("rule", "DEC-79/LR9"), ("verdict", "nonconvergent_alternation"), ("k_alt", k_alt),
                          ("pending", tuple(sorted(c.point_id for c in candidates)))))
            break
        todo = candidates
        admitted.extend(c.point_id for c in candidates)
        for c in candidates:
            queue.pop(c.point_id)
    front = tuple(done[i] for i in kept)
    dropped = tuple(DroppedPoint(i, DROP_DOMINATED, by) for i, by in dominated)
    dropped += tuple(DroppedPoint(i, DROP_FOLDED, by) for i, by in folded)
    nonconverged = tuple(done[i] for i in order if done[i].status != STATUS_CONVERGED)
    dropped += tuple(DroppedPoint(c.point_id, DROP_NONCONVERGED, None) for c in nonconverged)
    if front:
        included = tuple(name for name, _value, _rule in front[0].layout.snapshot.value("graph", LAYOUT_KEY, F_FLOORPLAN).included)
        notes.append((("rule", "DEC-79"), ("verdict", "judged_axis"), ("axis", "layout_outline_area_m2"), ("included", included),
                      ("search_axis_differs", True)))
    notes.append((("rule", "DEC-79"), ("verdict", "area_model_error_undeclared"),
                  ("reason", "DEC-80_ii_area_axis_model_error_bin_not_declared_difference_recorded_per_point")))
    perf = (("points", len(order)), ("rounds", rounds), ("kernel_calls", sctx.counters["kernel_calls"] - kernel0),
            ("layout_calls", sum(done[i].layout_calls for i in order)), ("wall_s", time.perf_counter() - started))
    return ConvergedFront(front, tuple(sorted(dropped, key=lambda d: (d.reason, d.point_id))), nonconverged, tuple(done[i] for i in order), rounds, k_alt,
                          tuple(admitted), perf, tuple(notes))
