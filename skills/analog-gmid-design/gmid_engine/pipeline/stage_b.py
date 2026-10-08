"""파이프라인 단계 B 진입점 -- GB4 달성가능성 (설계 41 §0 단계 A5~A7, 40 §3.4; 단계 A 보고서 뒤, 탐색 앞).

진입점: `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, diagnostic=False) -> StageBResult`.

순서: 단계 A 결과(`StageAResult`: s1·s1v·spec)가 `ok` 일 때만(`review_needed`·정지는 GB4 앞 정지라 그 exit code 를 그대로 낸다; `diagnostic=True` 면 s1v 가 있는 한 정지 상태에서도
GB4 를 계산해 측정만 한다 -- 정지 판정은 바뀌지 않고 `StageBResult.diagnostic` 이 True) -> `dc_inputs_from_spec` -> `build_kernel_context(l_classes=)`(쓰기 계획·전류 기저·θ 스키마) ->
`search_domain`(θ 전류 상자·자기동형 묶음·b_A) -> `passive_area_decl` -> `search.count_budget`(N_S) -> `metrics.achievability`(`stop=True`).
`InfeasibleTargetError` 는 전파하지 않고 보고서에 정지 사유와 모든 인증/미상 수치를 쓴 뒤 그 분류의 exit code(3)를 낸다(단계 A 와 같은 방식, 보고서는 항상 기록).
커널 컨텍스트·search 정의역의 정지(`StructureUnresolvedError`·`SchemaRejectedError`·`InfeasibleTargetError`)도 같은 방식으로 보고서에 정지 사유로 쓰고 exit code 를 낸다.
산출 `<회로>.stage_b.json`(전체)·`<회로>.stage_b.md`(요약): 블록별 A_i,max·Π·미상 사유, Σ 판정, A_lb 대 예산, 헤드룸 창 상한(유도 포함), 경고, 버퍼 창 보고, DOF, 곡선 검사.
`memo` = 호출자가 상한을 정해 만든 `lut.LutMemo`(곡선 영역 상한 ≥ GB4 가 만드는 곡선 수 Σ_kind |L|·|VDS|·|VS| 이면 재계산이 없다).
"""
import dataclasses
import json
import math
from pathlib import Path

from gmid_engine.core import InfeasibleTargetError, SchemaRejectedError, StructureUnresolvedError, exit_code_for
from gmid_engine.metrics import achievability
from gmid_engine.search import SearchSettings, count_budget, passive_area_decl, search_domain
from gmid_engine.sizing import (
    THETA_CURRENT,
    build_kernel_context,
    dc_inputs_from_spec,
    pre_layout_lut_access,
)
from gmid_engine.authoring import THETA_BOUNDS, UNTIE_ORBITS

STAGE_OK = "ok"
STAGE_SKIPPED = "skipped"
STAGE_INFEASIBLE = "infeasible"
STAGE_STOPPED = "stopped"
SETTING_WALL = "wall_clock_budget_s"
SETTING_FRONT = "front_budget_s"


@dataclasses.dataclass(frozen=True)
class StageBResult:
    """`exit_code`, `status`(ok|skipped|infeasible|stopped), `diagnostic`(단계 A 정지에도 GB4 를 계산했는가), `achievability`(`metrics.Achievability` 또는 None),
    `report`(dict), `report_paths`((json, md))."""

    exit_code: int
    status: str
    diagnostic: bool
    achievability: object
    report: object
    report_paths: tuple


def _setting(spec, name):
    section = spec.search if isinstance(spec.search, tuple) else ()
    return next((s.value for s in section if s.field == name and s.value is not None), None)


def _theta_currents(domain):
    """`SearchDomain` -> ({원소: (대표, 부호)}, {대표: (하한 A, 상한 A)}). 묶인 구성원은 (대표, ±1), 구조적 0 은 (None, 0)."""
    rep, box = {}, {}
    for variable in domain.variables:
        kind, key = variable.component
        if kind == THETA_CURRENT:
            box[key] = (math.exp(variable.lo), math.exp(variable.hi)) if variable.log else (variable.lo, variable.hi)
    negated = {c for c in domain.negated}
    for head, members in domain.ties:
        if head[0] != THETA_CURRENT:
            continue
        for member in members:
            rep[member[1]] = (head[1], -1 if member in negated else 1)
    for zero in domain.zeros:
        if zero[0] == THETA_CURRENT:
            rep[zero[1]] = (None, 0)
    return rep, box


def _jsonable(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: _jsonable(getattr(value, f.name)) for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, frozenset, set)):
        return [_jsonable(v) for v in (sorted(value, key=repr) if isinstance(value, (frozenset, set)) else value)]
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        return value.item()
    return value


def _fmt(x):
    return "n/a" if x is None else ("%.4g" % x)


def _markdown(report):
    lines = ["# 단계 B 보고서(GB4 달성가능성): " + report["circuit"], "", "- 상태: " + report["status"] + " (exit " + str(report["exit_code"]) + ")"
             + (" [진단 모드: 단계 A 정지에도 계산]" if report["diagnostic"] else ""), "- N_S(계수 예산): " + str(report["count_budget"]), ""]
    for reason in report["stop_reasons"]:
        lines.append("- 정지 사유: " + reason)
    res = report["achievability"]
    if res is None:
        return "\n".join(lines) + "\n"
    gain = res["gain"]
    if gain is not None:
        lines += ["", "## gain (뷰 " + gain["view"] + ", 목표 " + _fmt(gain["target_db"]) + " dB, 판정 " + gain["verdict"] + ")"]
        lines += ["- 상한 합 " + _fmt(gain["sum_db"]) + " dB (+b " + _fmt(gain["b_db"]) + "), 하한 추정 합(found) " + _fmt(gain["found_sum_db"]) + " dB, 미상 " + str(gain["n_unknown"])]
        for b in gain["blocks"] + gain["ff"]:
            lines.append("  - " + b["role"] + " " + str(b["key"]) + ": " + b["status"] + " A_max=" + _fmt(b["a_max_db"]) + " dB, b=" + _fmt(b["b_db"])
                         + ", found=" + _fmt(b["found_db"]) + " dB, Π=" + str(b["pi"]) + ", 사유=" + str(b["reason"]))
    area = res["area"]
    lines += ["", "## 면적", "- A_lb=" + _fmt(area["a_lb_m2"]) + " m², 예산=" + _fmt(area["budget_m2"]) + " m², b_A=" + _fmt(area["b_a_m2"]) + " m², 판정 " + area["verdict"]]
    lines += ["", "## 헤드룸 창"]
    for row in res["headroom"] + res["buffer_window_report"]:
        lines.append("- " + row["window_kind"] + " " + row["net"] + ": 폭 상한 " + _fmt(row["upper_bound_v"]) + " V [" + _fmt(row["lo_edge_v"]) + ", "
                     + _fmt(row["hi_edge_v"]) + "], " + row["status"] + ", 판정 " + row["verdict"] + ", 소자 " + ",".join(row["binding_devices"]))
    for code, detail in res["warnings"]:
        lines.append("- 경고 " + code + " " + json.dumps(detail, ensure_ascii=False))
    dof = res["dof"]
    lines += ["", "## DOF", "- " + dof["status"] + ": rank " + str(dof["structural_rank"]) + ", 변수 " + str(dof["n_variables"]) + ", 등식 " + str(dof["n_equations"])
              + ", 자유 변수 " + str(len(dof["free_variables"])), ""]
    return "\n".join(lines) + "\n"


def _write(report, output_dir, circuit):
    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    json_path, md_path = folder / (circuit + ".stage_b.json"), folder / (circuit + ".stage_b.md")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    return str(json_path), str(md_path)


def _curve_summary(curves):
    """곡선 검사: 슬라이스·축별 개수 전부 + 격자 전용(FC 위반) 칸은 (kind, w_key, 축)별 개수만(행은 결과 객체에 있다 -- 보고서 크기가 LUT 격자를 따라가지 않게)."""
    counts = {}
    for cell in curves.grid_only:
        key = (cell.kind, cell.w_key, cell.axis, cell.reason)
        counts[key] = counts.get(key, 0) + 1
    return {"lut_fp": curves.lut_fp, "n_unit_mismatch": curves.n_unit_mismatch, "slices": _jsonable(curves.slices),
            "n_grid_only_cells": len(curves.grid_only),
            "grid_only_by_slice": [{"kind": k, "w_key": w, "axis": a, "reason": r, "n_cells": n} for (k, w, a, r), n in sorted(counts.items())]}


def _finish(circuit, status, code, diagnostic, result, reasons, budget, output_dir):
    body = None
    if result is not None:
        body = _jsonable(result)
        body["curves"] = _curve_summary(result.curves)
    report = {"circuit": circuit, "status": status, "exit_code": code, "diagnostic": diagnostic, "count_budget": budget,
              "stop_reasons": list(reasons), "achievability": body}
    return StageBResult(code, status, diagnostic, result, report, _write(report, output_dir, circuit))


def run_stage_b(stage_a, memo, pdk_decl, *, output_dir, diagnostic=False):
    circuit = stage_a.report["circuit"]
    budget = stage_a.report["count_budget"]
    if stage_a.s1v is None or stage_a.spec is None or (stage_a.status != "ok" and not diagnostic):
        return _finish(circuit, STAGE_SKIPPED, stage_a.exit_code, False, None, ["stage_a_" + stage_a.status], budget, output_dir)
    spec, s1 = stage_a.spec, stage_a.s1
    try:
        inputs = dc_inputs_from_spec(spec)
        kctx = build_kernel_context(s1, inputs, pre_layout_lut_access(memo), l_classes=stage_a.s1v.l_classes)
        budgets = [float(d.value) for d in spec.judged_constraints if d.metric == "area_search_m2" and d.op == "<=" and d.value is not None]
        search = spec.search if isinstance(spec.search, tuple) else ()
        spec_bounds = next((s.value for s in search if s.field == THETA_BOUNDS and s.value), ())
        untie = tuple(name for name, _source in next((s.value for s in search if s.field == UNTIE_ORBITS and s.value), ()))
        wall = _setting(spec, SETTING_FRONT) or _setting(spec, SETTING_WALL)
        settings = SearchSettings(0.0 if wall is None else float(wall), None, None, ((SETTING_WALL, "spec.search"),))   # 정의역 계산은 벽시계를 읽지 않는다
        domain = search_domain(kctx, settings, pdk_decl, spec_bounds, min(budgets) if budgets else None, untie)
    except (SchemaRejectedError, StructureUnresolvedError, InfeasibleTargetError) as exc:
        return _finish(circuit, STAGE_STOPPED, exit_code_for(exc), diagnostic, None, [json.dumps(exc.record.to_json(), ensure_ascii=False, default=str)],
                       budget, output_dir)
    cur_rep, current_box = _theta_currents(domain)
    declared = spec.structure_count_budget
    n_s = count_budget(memo.lut, {k for k, _w in kctx.lut.w_keys}, declared)
    try:
        result = achievability(s1, stage_a.s1v, spec, kctx, count_budget=n_s, cur_rep=cur_rep, current_box=current_box,
                               area_resolution_m2=domain.area_resolution_m2, passive_area=passive_area_decl(kctx, spec, pdk_decl))
        return _finish(circuit, STAGE_OK, 0, diagnostic, result, [], n_s, output_dir)
    except InfeasibleTargetError as exc:
        reasons = [code + " " + json.dumps(dict(detail), ensure_ascii=False, default=str) for code, detail in exc.achievability.reasons]
        return _finish(circuit, STAGE_INFEASIBLE, exit_code_for(exc), diagnostic, exc.achievability, reasons, n_s, output_dir)
    except SchemaRejectedError as exc:        # LUT 이 GB4 입력을 못 만든다(예: 전도 행 없음) -- 조용히 통과하지 않고 정지 사유로 보고
        return _finish(circuit, STAGE_STOPPED, exit_code_for(exc), diagnostic, None,
                       [json.dumps(exc.record.to_json(), ensure_ascii=False, default=str)], n_s, output_dir)
