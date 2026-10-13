"""파이프라인 단계 B 진입점 -- GB4 달성가능성 (설계 41 §0 단계 A5~A7, 40 §3.4; 단계 A 보고서 뒤, 탐색 앞).

진입점: `run_stage_b(stage_a, memo, pdk_decl, *, output_dir, diagnostic=False, settings=None) -> StageBResult`.

순서: 단계 A 결과(`StageAResult`: s1(S0 수준 스냅샷 위 S1Graph, S1v 필드 포함)·spec)가 `ok` 일 때만(`review_needed`·정지는 GB4 앞 정지라 그 exit code 를 그대로 낸다;
`diagnostic=True` 면 S1v 필드가 있는 한 정지 상태에서도 GB4 를 계산해 측정만 한다 -- 정지 판정은 바뀌지 않고 `StageBResult.diagnostic` 이 True) -> `dc_inputs_from_spec` ->
`build_kernel_context`(쓰기 계획·전류 기저·커널 구조 파생·θ 스키마 -- L 동치류는 필드 `graph/s1v: l_classes`) -> S0 수준 권한표(search `S0_WRITERS`)로 넓힘 ->
계산 블록 `search_domain`(θ 전류 상자·자기동형 묶음·b_A) -> `passive_area_decl` -> `search.count_budget`(N_S) -> 계산 블록 `metrics.achievability`(S0 수준 필드 `graph/ach`) ->
`graph/ach: reasons` 가 있으면 `InfeasibleTargetError` 분류로 정지(exit 3). 모든 블록은 입력 버전이 같으면 재사용(같은 S0 의 디스크 스냅샷 위에서 계산 0).
`settings` = 탐색 실행 설정(`SearchSettings`, `build_search_context` 와 같은 값을 넘기면 정의역 블록이 한 번만 계산된다 -- 수동소자 상자가 정의역 입력이다, v1.9.1 D6) 또는 None
(spec `search` 의 벽시계만으로 만든 설정 -- 수동소자 상자는 spec `theta_bounds`).
`InfeasibleTargetError` 는 전파하지 않고 보고서에 정지 사유와 모든 인증/미상 수치를 쓴 뒤 그 분류의 exit code(3)를 낸다(단계 A 와 같은 방식, 보고서는 항상 기록).
커널 컨텍스트·search 정의역의 정지(`StructureUnresolvedError`·`SchemaRejectedError`·`InfeasibleTargetError`)도 같은 방식으로 보고서에 정지 사유로 쓰고 exit code 를 낸다.
산출 `<회로>.stage_b.json`(전체)·`<회로>.stage_b.md`(요약): 블록별 A_i,max·Π·미상 사유, Σ 판정, A_lb 대 예산, 헤드룸 창 상한(유도 포함), 경고, 버퍼 창 보고, DOF, 곡선 검사.
`memo` = 호출자가 상한을 정해 만든 `lut.LutMemo`(곡선 영역 상한 ≥ GB4 가 만드는 곡선 수 Σ_kind |L|·|VDS|·|VS| 이면 재계산이 없다).
결과 `StageBResult` 는 S0 수준 스냅샷 참조(`s1` = 그 스냅샷 위 S1Graph -- GB4 필드 포함)와 보고서만 담는다. 묶음 `Achievability` 는 없다(설계 40 §2.4.7 v1.9.1 D2).
"""
import dataclasses
import json
from pathlib import Path

from gmid_engine.core import InfeasibleTargetError, SchemaRejectedError, StructureUnresolvedError, exit_code_for
from gmid_engine.graph import ELEMENT_MOS, S1V_KEY, S1Graph
from gmid_engine.metrics import ACH_KEY, achievability
from gmid_engine.search import S0_WRITERS, SearchSettings, count_budget, passive_area_decl, search_domain
from gmid_engine.sizing import (
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
    """`exit_code`, `status`(ok|skipped|infeasible|stopped), `diagnostic`(단계 A 정지에도 GB4 를 계산했는가), `report`(dict), `report_paths`((json, md)),
    `s1` = S0 수준 스냅샷 위 S1Graph(GB4 를 계산했으면 `graph/ach` 필드 포함, 건너뛰거나 커널 컨텍스트에서 정지했으면 단계 A 의 것 그대로)."""

    exit_code: int
    status: str
    diagnostic: bool
    report: object
    report_paths: tuple
    s1: object = None


def _setting(spec, name):
    section = spec.search if isinstance(spec.search, tuple) else ()
    return next((s.value for s in section if s.field == name and s.value is not None), None)


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


_REPORT_FIELDS = (("verdict", "verdict"), ("reasons", "reasons"), ("gain", "gain_checks"), ("area", "area_bound"), ("headroom", "headroom_rows"),
                  ("warnings", "warnings"), ("buffer_window_report", "buffer_window_report"), ("dof", "dof"), ("count_budget", "count_budget"))


def _ach_body(s1):
    """보고서 `achievability` 칸 -- 필드 `graph/ach` 에서(보고 키는 옛 보고서 키 그대로), 곡선 검사는 요약."""
    body = {key: _jsonable(s1.value("graph", ACH_KEY, name)) for key, name in _REPORT_FIELDS}
    body["curves"] = _curve_summary(s1.value("graph", ACH_KEY, "curve_checks"))
    return body


def _finish(circuit, status, code, diagnostic, s1, computed, reasons, budget, output_dir):
    report = {"circuit": circuit, "status": status, "exit_code": code, "diagnostic": diagnostic, "count_budget": budget,
              "stop_reasons": list(reasons), "achievability": _ach_body(s1) if computed else None}
    return StageBResult(code, status, diagnostic, report, _write(report, output_dir, circuit), s1)


def run_stage_b(stage_a, memo, pdk_decl, *, output_dir, diagnostic=False, settings=None):
    circuit = stage_a.report["circuit"]
    budget = stage_a.report["count_budget"]
    s1 = stage_a.s1
    has_s1v = s1 is not None and s1.snapshot.field("graph", S1V_KEY, "views") is not None
    if not has_s1v or stage_a.spec is None or (stage_a.status != "ok" and not diagnostic):
        return _finish(circuit, STAGE_SKIPPED, stage_a.exit_code, False, s1, False, ["stage_a_" + stage_a.status], budget, output_dir)
    spec = stage_a.spec
    held = stage_a.status != "ok"     # 진단 모드: 측정만 하고 단계 A 의 상태·exit code 를 그대로 둔다(계약 5절)

    def finish(status, code, graph, computed, reasons, budget_value):
        if held:
            status, code = stage_a.status, stage_a.exit_code
        return _finish(circuit, status, code, diagnostic, graph, computed, reasons, budget_value, output_dir)
    try:
        inputs = dc_inputs_from_spec(spec)
        kctx = build_kernel_context(s1, inputs, pre_layout_lut_access(memo))
        budgets = [float(d.value) for d in spec.judged_constraints if d.metric == "area_search_m2" and d.op == "<=" and d.value is not None]
        search = spec.search if isinstance(spec.search, tuple) else ()
        spec_bounds = next((s.value for s in search if s.field == THETA_BOUNDS and s.value), ())
        untie = tuple(name for name, _source in next((s.value for s in search if s.field == UNTIE_ORBITS and s.value), ()))
        if settings is None:
            wall = _setting(spec, SETTING_FRONT) or _setting(spec, SETTING_WALL)
            settings = SearchSettings(0.0 if wall is None else float(wall), None, None, ((SETTING_WALL, "spec.search"),))   # 정의역 계산은 벽시계를 읽지 않는다
        graph = kctx.base.widen(S0_WRITERS)
        graph = search_domain(graph, kctx.lut, settings.resistance_bounds_ohm, settings.capacitance_bounds_f, pdk_decl, spec_bounds,
                              min(budgets) if budgets else None, untie)
    except (SchemaRejectedError, StructureUnresolvedError, InfeasibleTargetError) as exc:
        return finish(STAGE_STOPPED, exit_code_for(exc), s1, False, [json.dumps(exc.record.to_json(), ensure_ascii=False, default=str)], budget)
    declared = spec.structure_count_budget
    classes = dict(s1.column("device", "element_class"))     # 단계 A 와 같은 kind 집합(회로가 쓰는 MOS kind 만) -> 같은 S0 면 같은 N_S
    kinds = {kind for name, kind in s1.column("device", "kind") if classes[name] == ELEMENT_MOS}
    n_s = count_budget(memo.lut, kinds, declared)
    try:
        graph = passive_area_decl(graph, tuple(sorted(e.name for e in spec.element_values if e.measurement_load)), pdk_decl)
        graph = achievability(graph, spec, inputs.element_values, kctx.lut, n_s)
    except SchemaRejectedError as exc:        # LUT 이 GB4 입력을 못 만든다(예: 전도 행 없음) -- 조용히 통과하지 않고 정지 사유로 보고
        return finish(STAGE_STOPPED, exit_code_for(exc), S1Graph(s1.key, graph), False, [json.dumps(exc.record.to_json(), ensure_ascii=False, default=str)], n_s)
    result = S1Graph(s1.key, graph)
    reasons = result.value("graph", ACH_KEY, "reasons")
    if reasons:
        lines = [code + " " + json.dumps(dict(detail), ensure_ascii=False, default=str) for code, detail in reasons]
        return finish(STAGE_INFEASIBLE, exit_code_for(InfeasibleTargetError()), result, True, lines, n_s)
    return finish(STAGE_OK, 0, result, True, [], n_s)
