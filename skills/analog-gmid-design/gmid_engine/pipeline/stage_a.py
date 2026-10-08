"""파이프라인 단계 A 진입점 (설계 40 §2.1 GB0~GB2, 41 §0 단계 A1~A3).

진입점: `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None) -> StageAResult`.

순서(40 §3.2-3): A1 `load_topology`·`load_sizing_spec`(spec_path 가 None 이면 구조만 -- 기본 전달 뷰) -> `structure.json` 사실 로드(ratified 사실, 기본 경로 = topology 파일 옆
`<회로>.structure.json`, 없으면 사실 0 이고 declared 대조는 하지 않았다고 보고서에 적는다; topology 지문 = `doc.connectivity_fp` 라 `build_s1` 전에 이미 있고, rule_hash 는
`structure_rule_fp()`) -> A2 `build_s1(structure=)`(`dc_role`·`matching_pair` 소비) -> A3 `build_s1v`(N_S = `structure_count_budget`, `structure=`, spec 에서 직접 모은 `declared_loop_cuts`)
-> A4 `coupling_vars(s1, s1v)`(GB3: 결합 변수 y K1~K4·K7·K8 + 기둥↔블록 매핑표; 어느 블록에도 기둥에도 속하지 않는 소자가 있으면 `column_unassigned` 정지, exit 2)
-> 보고서(`write_stage_a_report`: 구조 표 + review_needed + 정지 사유 + N_S + declared 대조 여부 + 적용한 사실 + feedforward 비율 후보 + 루프 역할 + `coupling`).
* `coupling` 보고 키: `{"vars": [{kind, members, blocks[[뷰, 블록 키]], domain, init_rule, nets}], "column_block_map": [{column, block, device, shared, basis}], "bias_columns": [...],
  "kind_counts": {kind: 수}}` (정지 전 단계거나 `column_unassigned` 정지면 None). 소비자는 U15 층 0 조립(41 §5.5)이다 -- 아직 읽는 코드가 없고 보고서가 유일한 출구다.
* `declared_loop_cuts` = spec 제약 중 안정도 metric(`pm_*`)의 루프 뷰 선언(`ViewDecl` mode loop)의 끊는 넷 -- 안정도 제약이 걸린 루프 뷰는 `undeclared_loop_constraint` 정지가 풀린다.
* 로드·구조 단계의 예외(`SchemaRejectedError`·`StructureUnresolvedError`)는 전파하지 않고 보고서에 정지 사유로 적은 뒤 그 분류의 exit code 를 낸다(exit 7·2).
* `기록만`(unsupported_rule_branch) 기록이 있으면 정지, `review_needed` 가 남아 있으면 GB4 앞 정지 -- 둘 다 exit 2(StructureUnresolvedError 분류). 둘 다 없으면 exit 0.
  보고서에는 정지 여부와 무관하게 전체 구조 표를 쓴다(`build_s1v(stop_on_unsupported=False)` 로 기록을 받아 여기서 판정한다).
* ratified 사실 개념: `drive_kind`(대상 = 넷, 값 = voltage|current)는 구동 종류를 고정하고, `stage_members`(대상 = stage 이름, 값 = 공백으로 이은 소자 이름)는
  유도 stage 와 대조하는 declared 로 쓴다. topology 태그 섹션은 읽지 않는다(IC4).
* 결과 `StageAResult` 는 `S1v`(`l_classes` 를 `sizing.build_kernel_context(..., l_classes=)` 가 받는다)와 보고서 경로를 담는다.
"""
import dataclasses
from pathlib import Path

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.core import SchemaRejectedError, StructureUnresolvedError, exit_code_for
from gmid_engine.graph import (
    ELEMENT_MOS,
    SPEC_VIEW_LOOP,
    BASIS_COLUMN_MATE,
    build_s1,
    build_s1v,
    coupling_vars,
    load_structure_facts,
    structure_rule_fp,
    structure_tables,
)
from gmid_engine.metrics import metric_catalog

from .stage_a_budget import structure_count_budget
from .stage_a_report import write_stage_a_report

CONCEPT_STAGE_MEMBERS = "stage_members"
STABILITY_PREFIX = "pm_"          # 안정도 metric 이름 접두(`pm_ss_deg`·`pm_cm_ss_deg`, metrics 카탈로그)
STRUCTURE_SUFFIX = ".structure.json"
TOPOLOGY_SUFFIX = ".topology.json"
STATUS_OK = "ok"
STATUS_REVIEW = "review_needed"
STATUS_STOPPED = "stopped"


@dataclasses.dataclass(frozen=True)
class StageAResult:
    """`exit_code`, `status`(ok|review_needed|stopped), `s1v`(정지 전이면 None), `report`(dict), `report_paths`((json, md))."""

    exit_code: int
    status: str
    s1v: object
    report: object
    report_paths: tuple


def _stopped(circuit, exc, stage):
    return {"circuit": circuit, "status": STATUS_STOPPED, "exit_code": exit_code_for(exc), "count_budget": 0,
            "declared_comparison": "not_performed", "stop_reasons": [stage + ": " + str(exc.record.to_json())],
            "review_needed": [], "views": [], "applied_facts": [], "ff_ratio_candidates": [], "coupling": None, "tables": None}


def _supplies(spec, supplies_v):
    if supplies_v is not None:
        return dict(supplies_v)
    if spec is not None and isinstance(spec.supplies_v, tuple):
        return dict(spec.supplies_v)
    return None


def _view_summary(view):
    return {"id": view.id, "kind": view.kind, "loop_count": len(view.loops), "cuts": [list(c) for c in view.cuts],
            "blocks": [{"kind": b.kind, "key": list(b.key), "stage": b.stage} for b in view.blocks],
            "feedforward": [{"id": f.id, "cells": list(f.cells), "bias_cells": list(f.bias_cells), "load_cells": list(f.load_cells),
                             "bypassed_blocks": [list(k) for k in f.bypassed_blocks], "sign": f.sign, "status": f.status,
                             "approval_id": f.approval_id} for f in view.feedforward],
            "loop_roles": [{"loop_id": r.loop_id, "role": r.role, "reason": r.reason, "status": r.status, "approval_id": r.approval_id}
                           for r in view.loop_roles],
            "polarity": view.polarity}


def _ff_ratio_rows(s1v):
    return [{"view": v.id, "ff": c.ff, "bypassed_block": list(c.bypassed_block), "relation": c.relation, "source": c.source}
            for v in s1v.views for c in v.ff_ratio_candidates]


def _ref_row(ref):
    return None if ref is None else [ref.view, list(ref.key)]


def _coupling_report(coupling):
    """JSON 으로 쓸 수 있는 GB3 결과(결합 변수 + 기둥↔블록 매핑표)."""
    counts = {}
    for v in coupling.vars:
        counts[v.kind] = counts.get(v.kind, 0) + 1
    cbm = coupling.column_block_map
    return {"vars": [{"kind": v.kind, "members": list(v.members), "blocks": [_ref_row(b) for b in v.blocks], "domain": v.domain,
                      "init_rule": v.init_rule, "nets": list(v.nets)} for v in coupling.vars],
            "column_block_map": [{"column": r.column, "block": _ref_row(r.block), "device": r.device, "shared": r.shared, "basis": r.basis}
                                 for r in cbm.rows],
            "bias_columns": list(cbm.bias_columns), "kind_counts": counts,
            "column_mate_devices": sorted({r.device for r in cbm.rows if r.basis == BASIS_COLUMN_MATE})}


def _coupling_stage(s1, s1v):
    """A4: (보고용 dict 또는 None, 정지 사유 목록). 소자가 귀속되지 않으면(`column_unassigned`) 보고서에는 정지 사유만 적는다."""
    try:
        return _coupling_report(coupling_vars(s1, s1v)), []
    except StructureUnresolvedError as exc:
        return None, ["A4_coupling: " + str(exc.record.to_json())]


def _declared_loop_cuts(spec):
    """안정도 제약(`pm_*` metric)이 걸린 루프 뷰 선언의 끊는 넷 -- `build_s1v(declared_loop_cuts=)` 로 넘긴다(41 §1.8). spec 이 없으면 빈 tuple."""
    if spec is None:
        return ()
    return tuple(sorted({net for c in spec.judged_constraints if c.metric is not None and c.metric.startswith(STABILITY_PREFIX)
                         and c.view is not None and c.view.mode == SPEC_VIEW_LOOP for _, net in c.view.cuts}))


def _net_names(topology):
    nets = set(topology.rails)
    for d in topology.devices:
        nets.update((d.d, d.g, d.s))
    for p in topology.passives + topology.sources:
        nets.update(p.terminals)
    return tuple(sorted(nets))


def _finding_line(f):
    return f.severity + "|" + f.code + "|" + f.view + "|" + ",".join(f.subject) + "|" + f.detail


def _finish(report, s1v, output_dir, circuit):
    paths = write_stage_a_report(report, output_dir, circuit)
    return StageAResult(report["exit_code"], report["status"], s1v, report, paths)


def run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None):
    circuit = Path(topology_path).name.removesuffix(TOPOLOGY_SUFFIX)
    try:
        topology = load_topology(str(topology_path))
        spec = None if spec_path is None else load_sizing_spec(str(spec_path), topology, metric_catalog())
    except SchemaRejectedError as exc:
        return _finish(_stopped(circuit, exc, "A1_load"), None, output_dir, circuit)
    path = Path(structure_path) if structure_path is not None else Path(topology_path).with_name(circuit + STRUCTURE_SUFFIX)
    try:
        structure = load_structure_facts(path, topology.connectivity_fp, structure_rule_fp(), _net_names(topology))
    except SchemaRejectedError as exc:
        return _finish(_stopped(circuit, exc, "A2_structure_json"), None, output_dir, circuit)
    try:
        s1 = build_s1(topology, _supplies(spec, supplies_v), structure=structure)
    except (SchemaRejectedError, StructureUnresolvedError) as exc:
        return _finish(_stopped(circuit, exc, "A2_build_s1"), None, output_dir, circuit)
    classes = dict(s1.column("device", "element_class"))
    kinds = {kind for name, kind in s1.column("device", "kind") if classes[name] == ELEMENT_MOS}
    try:
        budget = structure_count_budget(lut, kinds)
    except ValueError as exc:   # N_S 정의역 밖(MOS 없음·LUT 슬라이스 없음) -- 보고서를 쓰고 정지
        return _finish(_stopped(circuit, StructureUnresolvedError(detail={"reason": "count_budget_undefined", "message": str(exc)}),
                                "A2_count_budget"), None, output_dir, circuit)
    groups = tuple(tuple(f.value.split()) for f in structure.facts if f.concept == CONCEPT_STAGE_MEMBERS)
    declared = ((path.name, groups),) if groups else ()
    s1v = build_s1v(s1, spec, count_budget=budget, declared=declared, structure=structure,
                    declared_loop_cuts=_declared_loop_cuts(spec), stop_on_unsupported=False)
    unsupported = [_finding_line(f) for f in s1v.unsupported]
    review = [_finding_line(f) for f in s1v.review_needed]
    note = " has no stage_members facts" if path.is_file() else " absent"
    comparison = "performed" if declared else "not_performed: " + path.name + note
    coupling, coupling_stop = _coupling_stage(s1, s1v)
    unsupported += coupling_stop
    status = STATUS_STOPPED if unsupported else STATUS_REVIEW if review else STATUS_OK
    code = 0 if status == STATUS_OK else exit_code_for(StructureUnresolvedError())
    report = {"circuit": circuit, "status": status, "exit_code": code, "count_budget": budget, "declared_comparison": comparison,
              "stop_reasons": unsupported, "review_needed": review, "views": [_view_summary(v) for v in s1v.views],
              "applied_facts": [list(f) for f in s1v.facts_applied], "ff_ratio_candidates": _ff_ratio_rows(s1v),
              "coupling": coupling, "tables": structure_tables(s1v)}
    return _finish(report, s1v, output_dir, circuit)
