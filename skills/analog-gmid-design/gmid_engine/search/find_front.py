"""MOD6 공개 API -- 탐색 축 (전력, 면적) 비지배 front (설계 design_mod6_search_front 0절·6절·7.4·8절, REQ 3.2, DEC-77).

진입점: `find_front(sctx, given_starts) -> SearchFront`.

순서: 시작점(`start_points`: S3 이전 front 점 + `given_starts`, 평가 1회로 봉인 상태 확인) -> `sweep_front`(끝점·ε 두 방향·
비지배 필터·L-b) -> S3 기록(front·대기 front 점 스냅샷 파일, runs 한 줄) -> `SearchFront`.

* **최종 front = 봉인된 점만.** 봉인 7 이 VDSAT 부재로 미정인 동안(`seal7_pending`) 모든 점은 `pending_front` 에만 있고
  `front` 는 비어 있다 -- 대기 front 는 '봉인 7 대기·추정'이며 판정·보고 값으로 쓰지 않는다(DEC-72·77).
* 기록하는 판정 보류(`notes`): spec 성능 제약 중 잴 수 없는 것(ss 영역, S-1), 수동소자 면적·값 미선언(DEC-79 -- 보상·부하
  수동소자가 있으면 `review_needed`), 층 0 시작점 미구현(S-4), 판정 축 재필터 미실행(MOD8 몫), 모델 오차 미측정('추정').
* 계측 `perf`(설계 7.4): requests·kernel_calls·hits·fail_hits·disk_hits·outside_domain·recompute_same_key, 고유 키 수,
  평가 시간 중앙값, sizing 계산 블록 calls·reuses·computes·recomputes_same_input 델타, LUT memo 퇴출 수.
  합격 기준(NFR-2): kernel_calls == 고유 키 수, recompute_same_key == 0, LUT memo 퇴출 0.
"""
import statistics
import time

from gmid_engine.core import fp_of
from gmid_engine.sizing import (
    dc_columns,
    dc_currents,
    dc_lengths,
    dc_seal_bulk_reverse,
    dc_seal_kcl,
    dc_seal_kvl_branch,
    dc_seal_node_conflict,
    dc_seal_report,
    dc_seal_saturation,
    dc_seal_vgs_match,
    dc_tolerances,
    dc_widths,
)

from .eps_sweep import sweep_front
from .search_values import AXIS_AREA, AXIS_POWER, STATUS_PENDING_SEAL7, SearchFront
from .start_points import start_points

# sizing 공개 계산 블록 12개(S-9: `dc_seal_vgs_match` 를 sizing `__all__` 에 더했다)
_BLOCKS = (dc_currents, dc_lengths, dc_columns, dc_widths, dc_tolerances, dc_seal_node_conflict, dc_seal_vgs_match,
           dc_seal_kcl, dc_seal_bulk_reverse, dc_seal_saturation, dc_seal_kvl_branch, dc_seal_report)
_LAYER0_MISSING = ("LR5 knee 격자(measure_L_knee: gm/ID·VDS 입력 필요)",
                   "DEC-71 (4)(a) 필요 gm(블록 gain 예산 -- GB4 상한표·GB5·ss_linearize)",
                   "DEC-71 (4)(c) VDS 배분의 VDsat 하한(lut VDSAT 접근자 -- 봉인 7 과 같은 대기)")


def _block_totals():
    totals = [0, 0, 0, 0]
    for block in _BLOCKS:
        s = block.stats()
        for i, v in enumerate((s.calls, s.reuses, s.computes, s.recomputes_same_input)):
            totals[i] += v
    return totals


def _point_record(sctx, point):
    res = point.result
    ref = None if sctx.archive is None else sctx.archive.write_snapshot(res.evaluation.snapshot)
    return {"point_id": point.point_id, "status": res.status, "seq": res.seq,
            "theta_hex": [[list(k), float(v).hex()] for k, v in res.theta], "cells": list(res.key.cells),
            AXIS_POWER: res.objectives.power_w, AXIS_AREA: res.objectives.area_m2,
            "gate_area_m2": res.objectives.gate_area_m2, "passives_in_area": False,
            "power_resolution_w": res.objectives.power_resolution_w, "unmeasured": [list(u) for u in res.unmeasured],
            "active": [{"name": r.name, "c": r.c} for r in res.constraints if r.active],
            "origin": dict(point.origin), "snapshot_fp": res.evaluation.snapshot.fp, "snapshot_ref": ref}


def find_front(sctx, given_starts):
    t_start = time.perf_counter()
    blocks_before = _block_totals()
    sctx.deadline = t_start + sctx.settings.front_budget_s
    starts, start_log = start_points(sctx, tuple(given_starts))
    out = sweep_front(sctx, starts)
    blocks_after = _block_totals()
    notes = [dict(n) for n in sctx.constraint_notes]
    probe = next((s.best for _p, s in out["solves"] if s.best is not None), None)
    if probe is not None and (probe.objectives.passive_value_undetermined or probe.objectives.passive_area_undeclared):
        notes.append({"verdict": "review_needed", "rule": "DEC-79",
                      "passive_value_undetermined": list(probe.objectives.passive_value_undetermined),
                      "passive_area_undeclared": list(probe.objectives.passive_area_undeclared)})
    notes.append({"verdict": "judgment_pending", "rule": "DEC-72", "reason": "model_error_unmeasured_front_estimated"})
    notes.append({"verdict": "not_run", "rule": "DEC-79", "reason": "layout_axis_refilter_is_mod8"})
    notes.append({"verdict": "provisional", "rule": "S-3b",
                  "reason": "current_upper_is_single_finger_max_slice_needs_declared_max_nf_or_area_cap",
                  "current_box": [[k, list(v)] for k, v in sctx.domain.current_box]})
    notes.append({"verdict": "blocked", "rule": "DEC-71", "reason": "layer0_inputs_missing",
                  "missing": list(_LAYER0_MISSING)})
    notes.append({"verdict": "not_computed", "rule": "DEC-78", "reason": "supply_current_dc_needs_counted_rails_declaration",
                  "axis_used": AXIS_POWER})
    unmeasured = sorted({u for res in sctx.cache.values() for u in res.unmeasured})
    if unmeasured:
        notes.append({"verdict": "unmeasured", "rule": "S-1", "constraints": [list(u) for u in unmeasured],
                      "points": sum(1 for res in sctx.cache.values() if res.unmeasured)})
    if out["pending_front"]:
        notes.append({"verdict": "pending", "rule": "DEC-88", "reason": "seal_7_undefined_vdsat_accessor_missing",
                      "pending_points": len(out["pending_front"])})
    memo_evictions = sum(s.evictions for _r, s in sctx.dc.lut.memo.stats())
    perf = dict(sctx.counters)
    perf.update(unique_keys=len(sctx.computed_keys),
                eval_time_median_s=statistics.median(sctx.eval_times) if sctx.eval_times else None,
                wall_s=time.perf_counter() - t_start, lut_memo_evictions=memo_evictions,
                block_calls=blocks_after[0] - blocks_before[0], block_reuses=blocks_after[1] - blocks_before[1],
                block_computes=blocks_after[2] - blocks_before[2],
                block_recomputes_same_input=blocks_after[3] - blocks_before[3], n_starts=len(starts),
                n_solves=len(out["solves"]), eval_budget=sctx.eval_budget, eval_budget_source=sctx.eval_budget_source,
                frozen_columns=sum(len(s.frozen) for _p, s in out["solves"]),
                stops_eval_budget=sum(1 for _p, s in out["solves"] if s.stop == "eval_budget"),
                stops_wall_budget=sum(1 for _p, s in out["solves"] if s.stop == "wall_budget"))
    run_id = fp_of((sctx.context_fp, sctx.code_fp, sctx.settings, sctx.eval_budget, tuple(s.theta for s in starts)))
    if sctx.archive is not None:
        sctx.archive.append_run({
            "run_id": run_id, "s0": sctx.context_fp, "schema_fp": sctx.schema_fp, "settings": sctx.settings,
            "starts": list(start_log), "resolution": dict(out["resolution"]),
            "front": [_point_record(sctx, p) for p in out["front"]],
            "pending_front": [_point_record(sctx, p) for p in out["pending_front"]],
            "removed": [{"point_id": a, "reason": "dominated", "by": b}
                        for a, b in out["front_removed"] + out["pending_front_removed"]],
            "failed_eps": list(out["failed_eps"]), "notes": notes, "perf": perf})
    pending = tuple(p for p in out["pending_front"] if p.result.status == STATUS_PENDING_SEAL7)
    return SearchFront(run_id, out["front"], pending, out["failed_eps"], out["resolution"],
                       tuple(sorted(perf.items())), tuple(notes))
