"""MOD6 공개 API -- 탐색 축 (전력, 면적) 비지배 front (설계 design_mod6_search_front 0절·6절·7.4·8절, REQ 3.2, DEC-77).

진입점: `find_front(sctx, given_starts) -> SearchFront`.

진입(FS-1): 평가 입력 w_f 칸 출발값 `initial_wf(base)` 가 None(출발 불능 칸 -- `graph/start: wf_start` 에 `w_key` None)이면 평가 0회로 끝낸다: notes 에
`{"verdict": "start_undefined", "rule": "DEC-108 (3)", "records": [...]}`(`wf_start_undefined` 출발 기록 그대로), front·pending·unmeasured_front 빈 tuple.

순서: 층 0 시작점(`layer0_start`, DEC-71 최소형) -> 시작점(`start_points`: 층 0 점 + `given_starts`,
평가 1회로 봉인 상태 확인) -> `sweep_front`(끝점·ε 두 방향·
비지배 필터·L-b) -> S3 기록(front·대기 front 점 스냅샷 파일, runs 한 줄) -> `SearchFront`.

* **최종 front = 봉인된 점만.** 봉인 7 이 VDSAT 부재로 미정인 동안(`seal7_pending`) 모든 점은 `pending_front` 에만 있고
  `front` 는 비어 있다 -- 대기 front 는 '봉인 7 대기·추정'이며 판정·보고 값으로 쓰지 않는다(DEC-72·77).
* 기록하는 판정 보류(`notes`): spec 성능 제약 중 잴 수 없는 것(ss 영역, S-1), 수동소자 면적·값 미선언(DEC-79 -- 보상·부하
  수동소자가 있으면 `review_needed`), 층 0 결과(최소형 -- 정밀화 GB3·GB4·knee 는 범위 밖, S-4), 판정 축 재필터 미실행(MOD8 몫 -- `convergence.converge(sctx, pdk_decl, front.front)` 가 이 front 를 받아 한다; 패키지 순서상 여기서 부를 수 없고 U16 파이프라인이 부른다), 모델 오차 미측정('추정').
* [NFR-4] 진입에서 `core.blas_environment()` 로 BLAS 스레드 1 을 다시 확인하고(재확인 (c)) 그 값의 `fp_of` 를 runs 줄 최상위 키 `env_fp` 에 둔다. notes 에는 L-b 정지 사유
  `{"verdict": "l_search", "rule": "LR10", "stops": [...]}` 가 언제나 한 줄 더해진다(`sweep_front` 의 `lb_stops`, L-b 가 돌지 않았으면 빈 목록).
* 계측 `perf.solver_stops`(WB-1 범위 3a-0, 출력 전용): 풀이 종류 {eps, layer0}마다 정지 사유 집계(converged 수·abnormal {사유: 수}·budget {eval_budget, wall_budget}).
* 계측 `perf`(설계 7.4): requests·kernel_calls·hits·fail_hits·outside_domain·recompute_same_key, 고유 키 수,
  평가 시간 중앙값, LUT memo 퇴출 수, 블록 계수(`blocks` = 실행 하나가 단계 A 부터 부른 모든 (블록, 분할)의 행 -- `sctx.dc.counters.snapshot()`,
  `block_totals` = 여섯 계수 칸의 합), 블록 결과 색인 크기(`block_index_entries` = `entry_count()`, `block_index_bound` = `donors.index_bound(E_total)` 또는 null,
  E_total 은 `_helpers_ceiling.e_total`). `eval_budget` 칸의 뜻은 선언 실행 = E_B, 유도 실행 = D 로 갈린다(`eval_budget_source` 가 구분, 결과 JSON 칸 이름은 그대로).
* [WB-1 범위 7 (b)] 실현 관문: `sweep_front` 뒤 front ∪ unmeasured_front 의 점을 `realize_front` 로 실현 평가하고, 결과를 실현 평가의 측정 상태로 S-1 분류(`eps_sweep.classify`)해
  front·unmeasured_front 둘로 나눈다(집합 이동은 `realize.moved` 기록). 감도 게이트 대상 = 실현 front 첫 점이고 실현 front 가 비면 '대상 없음'(`gate_empty`) 기록·호출 0이다.
* [XRUN-F1 card C] 예산: 진입에서 `donors.open_bound(E_total)`(색인 항목 수 상한 검사 열기), `sweep_front` 뒤 `search_ceiling(sctx, final=True)` 한 번(평가가 적어
  유도 전이가 없었던 실행의 D 를 정한다). 실현 관문의 평가 수 n_real 은 E_total(탐색 + 게이트) 밖이라 관문 앞에서 `close_bound()` 하고(삽입 검사 끔), 게이트 뒤 끝 확인(`kernel_calls − n_real` >
  E_total 또는 색인 항목 수 > 상한(E_total + n_real)이면 `RuntimeError`)이 대신 한다. 게이트는 탐색 예산을 다 써도 실현 front 점이 있으면 언제나 돈다.
  합격 기준(NFR-2): kernel_calls == 고유 키 수, recompute_same_key == 0, 모든 행 recomputes_same_input == 0, LUT memo 퇴출 0.
"""
import dataclasses
import statistics
import time

from gmid_engine.core import blas_environment, fp_of
from gmid_engine.metrics import GATE_EMPTY, GATE_REASON_FRONT_EMPTY, GateResult, verified_by

from .eps_sweep import classify, sweep_front
from .gate_run import run_sensitivity_gate
from ._helpers_ceiling import e_total, gate_reserve
from .initial_wf import initial_wf
from .layer0_center import layer0_start
from .realize_front import realize_front
from .search_ceiling import search_ceiling
from .s0_fields import START_KEY
from .search_values import AXIS_AREA, AXIS_POWER, STATUS_PENDING_SEAL7, SearchFront
from .start_points import start_points
from .wf_start import RECORD_START_UNDEFINED

# 층 0 = DEC-71 최소형(R D18·U-49): 봉인 여유 최대-최소 중심 시작점 하나(`layer0_start`, 오케스트레이터 결정 2026-10-08).
# 블록 gain 예산(GB3·GB4)·LR5 knee·GB5 근사식은 최소형 밖의 정밀화라 쓰지 않는다 -- notes 에 그 사실을 남긴다.
_LAYER0_REFINEMENTS_OUT_OF_SCOPE = ("GB3 블록 분해·GB4 블록 gain 상한표(블록 gain 예산, DEC-71 (3)(6)·DEC-73)",
                                    "LR5 knee 앵커(집계·측정점·격자 의존 열린 항목)",
                                    "GB5 층 0 근사식(DEC-92 (2), comp_approx_gap)")


_STOP_CONVERGED = "converged"
_STOP_BUDGETS = ("eval_budget", "wall_budget")


def _stop_counts(stops):
    """풀이 정지 사유 열 -> {"converged": n, "abnormal": {사유: n}, "budget": {"eval_budget": n, "wall_budget": n}}(출력 전용, WB-1 범위 3a-0)."""
    abnormal = {}
    for s in stops:
        if s != _STOP_CONVERGED and s not in _STOP_BUDGETS:
            abnormal[str(s)] = abnormal.get(str(s), 0) + 1
    return {"converged": sum(1 for s in stops if s == _STOP_CONVERGED), "abnormal": dict(sorted(abnormal.items())),
            "budget": {b: sum(1 for s in stops if s == b) for b in _STOP_BUDGETS}}


def _bin_rule_note(lut):
    """bin 규칙 적용 기록(WB-1, DEC-105 (2), 판정 불변): 적용한 규칙·줄바꿈 때문에 기록 sha 가 raw 인 (세트, 모델 파일) 쌍(기계 의존).
    (LM-1e: '중점 미검증 슬라이스' 표지는 삭제 -- `widths` 슬라이스는 중점이 없으면 LUT 적재가 거부된다.)"""
    return {"verdict": "recorded", "rule": "DEC-105 (2)", "bin_rule": lut.bin_rule,
            "bin_rule_machine_dependent": [list(pair) for pair in lut.provenance.bin_rule_machine_dependent]}


def _point_record(sctx, point, residual=None):
    res = point.result
    ref = None if sctx.archive is None else sctx.archive.write_snapshot(res.evaluation.snapshot)
    extra = {}
    if residual is not None:
        extra["finger_residual"] = {m: r for m, r in residual}      # 실현 평가 `FingerGeom.residual` (= m·w_f/W_θ − 1, 탐색 평가 값 0.0 이 아니다)
    return {**extra, "point_id": point.point_id, "status": res.status, "seq": res.seq,
            "theta_hex": [[list(k), float(v).hex()] for k, v in res.theta], "cells": list(res.key.cells),
            AXIS_POWER: res.objectives.power_w, AXIS_AREA: res.objectives.area_m2,
            "gate_area_m2": res.objectives.gate_area_m2, "passives_in_area": sctx.area_decl is not None,
            "power_resolution_w": res.objectives.power_resolution_w, "unmeasured": [list(u) for u in res.unmeasured],
            "warnings": [[w[0], [list(kv) for kv in w[1]]] for w in res.warnings],
            "active": [{"name": r.name, "c": r.c} for r in res.constraints if r.active],
            "origin": dict(point.origin), "snapshot_fp": res.evaluation.snapshot.fp, "snapshot_ref": ref}


def _start_undefined(sctx, env_fp, t_start):
    """출발 w_f 칸이 정의되지 않은 실행(`initial_wf` None) -- 평가 0회, notes 에 출발 기록(`wf_start_undefined`)을 그대로 싣고 빈 front 를 낸다(성능 판정 보류, DEC-108 (3))."""
    records = [[code, dict(detail)] for code, detail in sctx.dc.base.value("graph", START_KEY, "records") if code == RECORD_START_UNDEFINED]
    notes = [{"verdict": "start_undefined", "rule": "DEC-108 (3)", "records": records}]
    perf = dict(sctx.counters)
    perf.update(wall_s=time.perf_counter() - t_start, wf_neighbor_evals=0, wf_neighbor_wall_s=0.0)
    run_id = fp_of((sctx.context_fp, sctx.code_fp, sctx.settings, sctx.eval_budget, ()))
    if sctx.archive is not None:
        sctx.archive.append_run({"run_id": run_id, "s0": sctx.context_fp, "schema_fp": sctx.schema_fp, "settings": sctx.settings, "starts": [], "resolution": {},
                                 "front": [], "pending_front": [], "unmeasured_front": [], "removed": [],
                                 "realize": {"lost": [], "n_lost": 0, "moved": []}, "failed_eps": [], "notes": notes, "perf": perf, "env_fp": env_fp})
    return SearchFront(run_id, (), (), (), {}, tuple(sorted(perf.items())), tuple(notes), ())


def find_front(sctx, given_starts):
    env_fp = fp_of(blas_environment())      # [NFR-4 재확인 (c)] 진입에서 한 번 -- 확인 실패는 RuntimeError, 반환값 지문이 runs 줄 `env_fp`
    t_start = time.perf_counter()
    if initial_wf(sctx.dc.base) is None:
        return _start_undefined(sctx, env_fp, t_start)
    sctx.deadline = t_start + sctx.settings.front_budget_s
    sctx.dc.donors.open_bound(lambda: e_total(sctx))      # 색인 항목 수 상한 검사 열기 -- E_total 은 참조로 읽는다(값 사본 없음)
    layer0 = layer0_start(sctx)
    starts, start_log = start_points(sctx, tuple(given_starts), () if layer0.start is None else (layer0.start,))
    out = sweep_front(sctx, starts)
    search_ceiling(sctx, final=True)      # 게이트 전: 평가가 n_θ + 1 개 미만이라 유도 전이가 없었다면 지금 D 를 정한다(D − R 보다 탐색이 더 썼으면 ValueError)
    notes = [dict(n) for n in sctx.constraint_notes]
    sctx.dc.donors.close_bound()      # 실현 관문의 평가는 E_total(탐색 + 게이트) 밖이다 -- 색인 항목 수 삽입 검사는 이 뒤로 끄고, 아래 끝 확인이 그 수(n_real)를 뺀 값으로 대신 한다
    k_real = sctx.counters["kernel_calls"]
    realized = realize_front(sctx, tuple(out["front"]) + tuple(out["unmeasured_front"]))      # front 출력 전 관문(WB-1): 실현 평가를 거친 점만 front·선택·oracle 입력이 된다
    n_real = sctx.counters["kernel_calls"] - k_real
    realized_sets = {name: tuple(p for p in realized.points if classify(p.result) == name) for name in ("front", "unmeasured_front")}      # 실현 값의 S-1 분류(탐색과 같은 함수)
    front, unmeasured_front = realized_sets["front"], realized_sets["unmeasured_front"]
    residual = dict(realized.finger_residual)
    k_gate = sctx.counters["kernel_calls"]
    gate = (run_sensitivity_gate(sctx, front[0].result) if front       # [U7] 감도 게이트(40 §3.8-2) 대상 = 실현 front 첫 점, 탐색 예산을 다 써도 돈다 -- 언제나 한 행(E-01); 비면 '대상 없음' 기록, 호출 0
            else GateResult(False, (), (), None, GATE_EMPTY, GATE_REASON_FRONT_EMPTY, ()))
    if sctx.counters["kernel_calls"] - k_gate > gate_reserve(sctx):
        raise RuntimeError("find_front: 감도 게이트가 예약 R=" + str(gate_reserve(sctx)) + " 보다 많은 커널 평가를 썼다: " + str(sctx.counters["kernel_calls"] - k_gate))
    total = e_total(sctx)
    if total is not None and sctx.counters["kernel_calls"] - n_real > total:
        raise RuntimeError("find_front: kernel_calls=" + str(sctx.counters["kernel_calls"] - n_real) + " 가 E_total=" + str(total) + " 를 넘었다")
    if total is not None and sctx.dc.donors.entry_count() > sctx.dc.donors.index_bound(total + n_real):
        raise RuntimeError("find_front: 블록 결과 색인 항목 수 " + str(sctx.dc.donors.entry_count()) + " 가 상한 " + str(sctx.dc.donors.index_bound(total + n_real)) + " 를 넘었다")
    notes.append({"verdict": gate.verdict, "reason": gate.reason, "rule": "sensitivity_gate", "errors": list(gate.errors),
                  "checks": len(gate.checks), "unchecked": sum(1 for c in gate.checks if c[4] is None), "unmeasured": list(gate.unmeasured),
                  "epsilon_db": gate.epsilon})
    probe = next((s.best for _p, s in out["solves"] if s.best is not None), None)
    if probe is not None and (probe.objectives.passive_value_undetermined or probe.objectives.passive_area_undeclared):
        notes.append({"verdict": "review_needed", "rule": "DEC-79",
                      "passive_value_undetermined": list(probe.objectives.passive_value_undetermined),
                      "passive_area_undeclared": list(probe.objectives.passive_area_undeclared)})
    notes.append({"verdict": "judgment_pending", "rule": "DEC-72", "reason": "model_error_unmeasured_front_estimated"})
    declared = sorted({d.metric for d in sctx.ss_constraints} | {m for m, _op, _v in sctx.judged_constraints})      # [U7] 판정 metric 의 검증 출처(DEC-90 (3))
    notes.append({"verdict": "verified_by", "rule": "DEC-72/DEC-90",
                  "metrics": [[v.metric, v.kind, v.measure, v.model_error_ref] for v in map(verified_by, declared)],
                  "model_error": [list(p) for p in sctx.model_error]})
    notes.append({"verdict": "not_run", "rule": "DEC-79", "reason": "layout_axis_refilter_is_mod8"})
    box = [[k, list(v)] for k, v in sctx.domain.current_box]
    if sctx.domain.area_budget_m2 is None:
        notes.append({"verdict": "provisional", "rule": "S-3b",
                      "reason": "current_upper_is_single_finger_max_slice_needs_declared_max_nf_or_area_cap",
                      "current_box": box})
    else:
        notes.append({"verdict": "closed", "rule": "S-3b", "reason": "current_upper_from_area_budget_IDu_max_A_over_L2",
                      "area_budget_m2": sctx.domain.area_budget_m2, "current_box": box})
    notes.append({"verdict": "layer0_minimal" if layer0.start is not None else "layer0_no_start", "rule": "DEC-71",
                  "reason": "seal_margin_maxmin_centre", "stop": layer0.stop, "t": layer0.t, "hard_ok": layer0.hard_ok,
                  "start_status": layer0.start_status, "centre_u": layer0.centre_u, "kernel_calls": layer0.kernel_calls,
                  "probes": layer0.probes, "origin_point": layer0.origin_point, "meaning": "feasibility_only",
                  "meaning_reason": ("w_area_upper_bound_undeclared_S-3b" if sctx.domain.area_budget_m2 is None
                                     else "w_bounded_by_area_budget"),
                  "refinements_out_of_scope": list(_LAYER0_REFINEMENTS_OUT_OF_SCOPE)})
    notes.append(_bin_rule_note(sctx.dc.lut.memo.lut))
    notes.append({"verdict": "l_search", "rule": "LR10", "stops": list(out["lb_stops"])})      # [NFR-4] L-b 정지 사유 -- 언제나 한 줄(L-b 가 돌지 않았으면 빈 목록)
    notes.append({"verdict": "not_computed", "rule": "DEC-78", "reason": "supply_current_dc_needs_counted_rails_declaration",
                  "axis_used": AXIS_POWER})
    for code in sorted({w[0] for res in sctx.cache.values() for w in res.warnings}):
        notes.append({"verdict": "warning", "code": code,
                      "points": sum(1 for res in sctx.cache.values() if any(w[0] == code for w in res.warnings))})
    unmeasured = sorted({u for res in sctx.cache.values() for u in res.unmeasured})
    if unmeasured:
        notes.append({"verdict": "unmeasured", "rule": "S-1", "constraints": [list(u) for u in unmeasured],
                      "points": sum(1 for res in sctx.cache.values() if res.unmeasured)})
    if out["pending_front"]:
        notes.append({"verdict": "pending", "rule": "DEC-88", "reason": "seal_7_undefined_vdsat_accessor_missing",
                      "pending_points": len(out["pending_front"])})
    memo_evictions = sum(s.evictions for _r, s in sctx.dc.lut.memo.stats())
    block_counts = sctx.dc.counters.snapshot()        # 실행 하나의 계수 -- 단계 A 부터 불린 모든 (블록, 분할), 구간 차를 계산하지 않는다
    perf = dict(sctx.counters)
    perf.update(unique_keys=len(sctx.computed_keys),
                eval_time_median_s=statistics.median(sctx.eval_times) if sctx.eval_times else None,
                wall_s=time.perf_counter() - t_start, lut_memo_evictions=memo_evictions,
                lut_memo_bound="fixed" if sctx.dc.lut.memo.bound_state == "fixed" else "unfixed_no_kernel_eval",
                blocks=[dataclasses.asdict(row) for row in block_counts.blocks],
                block_totals=dataclasses.asdict(block_counts.block_totals),
                block_index_entries=sctx.dc.donors.entry_count(),
                block_index_bound=None if total is None else sctx.dc.donors.index_bound(total), n_starts=len(starts),
                n_solves=len(out["solves"]), eval_budget=sctx.eval_budget, eval_budget_source=sctx.eval_budget_source,
                wf_neighbor_evals=out["wf_neighbor"][0], wf_neighbor_wall_s=out["wf_neighbor"][1],      # [FS-1] w_f 이웃 시험 비용(출력 전용)
                frozen_columns=sum(len(s.frozen) for _p, s in out["solves"]),
                stops_eval_budget=sum(1 for _p, s in out["solves"] if s.stop == "eval_budget"),
                stops_wall_budget=sum(1 for _p, s in out["solves"] if s.stop == "wall_budget"),
                solver_stops={"eps": _stop_counts(tuple(s.stop for _p, s in out["solves"])),
                              "layer0": _stop_counts((layer0.stop,))})
    run_id = fp_of((sctx.context_fp, sctx.code_fp, sctx.settings, sctx.eval_budget, tuple(s.theta for s in starts)))
    if sctx.archive is not None:
        sctx.archive.append_run({
            "run_id": run_id, "s0": sctx.context_fp, "schema_fp": sctx.schema_fp, "settings": sctx.settings,
            "starts": list(start_log), "resolution": dict(out["resolution"]),
            "front": [_point_record(sctx, p, residual[p.point_id]) for p in front],
            "pending_front": [_point_record(sctx, p) for p in out["pending_front"]],
            "unmeasured_front": [_point_record(sctx, p, residual[p.point_id]) for p in unmeasured_front],
            "removed": [{"point_id": a, "reason": "dominated", "by": b}
                        for a, b in out["front_removed"] + out["pending_front_removed"]
                        + out["unmeasured_front_removed"]]
                       + [{"point_id": a, "reason": "dominated_realized", "by": b} for a, b in realized.removed],
            "realize": {"lost": [{"point_id": pid, "reason": reason, "detail": detail} for pid, reason, detail in realized.lost],
                        "n_lost": len(realized.lost), "moved": [list(m) for m in realized.moved]},      # moved = (점, 탐색 집합, 실현 집합) -- 출력 전용 기록
            "failed_eps": list(out["failed_eps"]), "notes": notes, "perf": perf, "env_fp": env_fp})
    pending = tuple(p for p in out["pending_front"] if p.result.status == STATUS_PENDING_SEAL7)
    return SearchFront(run_id, front, pending, out["failed_eps"], out["resolution"],
                       tuple(sorted(perf.items())), tuple(notes), unmeasured_front)
