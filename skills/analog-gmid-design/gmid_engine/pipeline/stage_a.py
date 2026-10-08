"""파이프라인 단계 A 진입점 (설계 40 §2.1 GB0~GB2, 41 §0 단계 A1~A3).

진입점: `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None) -> StageAResult`.

순서(40 §3.2-3): A1 `load_topology`·`load_sizing_spec`(spec_path 가 None 이면 구조만 -- 기본 전달 뷰) -> `structure.json` 사실 로드(ratified 사실, 기본 경로 = topology 파일 옆
`<회로>.structure.json`, 없으면 사실 0 이고 declared 대조는 하지 않았다고 보고서에 적는다; topology 지문 = `doc.connectivity_fp` 라 `build_s1` 전에 이미 있고, rule_hash 는
`structure_rule_fp()`) -> A2 `build_s1(structure=)`(`dc_role`·`matching_pair` 소비) -> A3 `build_s1v`(N_S = `structure_count_budget`, `structure=`, spec 에서 직접 모은 `declared_loop_cuts`)
-> 보고서(`write_stage_a_report`: 구조 표 + review_needed + 정지 사유 + N_S + declared 대조 여부 + 적용한 사실 + feedforward 비율 후보 + 루프 역할).
* `declared_loop_cuts` = spec 제약 중 안정도 metric(`pm_*`)의 내부 루프 뷰 선언(`ViewDecl` mode loop, `beta != declared`)의 끊는 넷 -- feedback 소자에서 유도된 β 루프(beta declared)는 제외 -- 안정도 제약이 걸린 루프 뷰는 `undeclared_loop_constraint` 정지가 풀린다.
  선언 끊는 넷은 엔진 루프 뷰의 끊는 gate 넷(보고서 `views[].cuts[*][1]`)이어야 하고, 어느 뷰에도 맞지 않은 선언은 `loop_cut_unmatched`(review_needed)로 보고서 `review_needed` 에 오른다.
* 로드·구조 단계의 예외(`SchemaRejectedError`·`StructureUnresolvedError`)는 전파하지 않고 보고서에 정지 사유로 적은 뒤 그 분류의 exit code 를 낸다(exit 7·2).
* `기록만`(unsupported_rule_branch) 기록이 있으면 정지, `review_needed` 가 남아 있으면 GB4 앞 정지 -- 둘 다 exit 2(StructureUnresolvedError 분류). 둘 다 없으면 exit 0.
  보고서에는 정지 여부와 무관하게 전체 구조 표를 쓴다(`build_s1v(stop_on_unsupported=False)` 로 기록을 받아 여기서 판정한다).
* ratified 사실 개념: `drive_kind`(대상 = 넷, 값 = voltage|current)는 구동 종류를 고정하고, `stage_members`(대상 = stage 이름, 값 = 공백으로 이은 소자 이름)는
  유도 stage 와 대조하는 declared 로 쓴다. topology 태그 섹션은 읽지 않는다(IC4).
* 결과 `StageAResult` 는 `S1v`(`l_classes` 를 `sizing.build_kernel_context(..., l_classes=)` 가 받는다)와 보고서 경로를 담는다.
"""
import dataclasses
from pathlib import Path

from gmid_engine.authoring import BETA_DECLARED, load_sizing_spec, load_topology
from gmid_engine.core import SchemaRejectedError, StructureUnresolvedError, exit_code_for
from gmid_engine.graph import (
    ELEMENT_MOS,
    F_LOOP_CUT_UNMATCHED,
    SEVERITY_REVIEW,
    SPEC_VIEW_LOOP,
    Finding,
    build_s1,
    build_s1v,
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
            "review_needed": [], "views": [], "applied_facts": [], "ff_ratio_candidates": [], "tables": None}


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


def _declared_loop_cuts(spec):
    """안정도 제약(`pm_*` metric)이 걸린 **내부 루프 뷰** 선언의 끊는 넷 -- `build_s1v(declared_loop_cuts=)` 로 넘긴다(41 §1.8). spec 이 없으면 빈 tuple.
    spec `feedback` 소자에서 유도된 β 루프(`ViewDecl.beta == BETA_DECLARED`, 입력 포트에서 되먹임 수동소자를 거쳐 끊는 테스트벤치 루프)는 엔진 내부 루프 뷰가 아니라
    metric 의 되먹임 뷰가 평가하므로 제외한다(U1b-jrules 결정)."""
    if spec is None:
        return ()
    return tuple(sorted({net for c in spec.judged_constraints if c.metric is not None and c.metric.startswith(STABILITY_PREFIX)
                         and c.view is not None and c.view.mode == SPEC_VIEW_LOOP and c.view.beta != BETA_DECLARED
                         for _, net in c.view.cuts}))


def _unmatched_loop_cuts(s1v, declared_cuts):
    """spec 루프 뷰 선언의 끊는 넷 중 엔진 루프 뷰의 끊는 gate 넷(`ViewS1v.cuts[*][1]`, 보고서 `views[].cuts`)과 맞지 않는 것마다 `loop_cut_unmatched`(review_needed) --
    어느 뷰에도 걸리지 않는 선언이 조용히 무동작이 되지 않게 한다(U1b-jrules 결정, graph CONTRACT)."""
    engine = {cut[1] for v in s1v.views for cut in v.cuts}
    return tuple(Finding(F_LOOP_CUT_UNMATCHED, SEVERITY_REVIEW, "", (net,),
                         "spec 루프 뷰 선언의 끊는 넷이 엔진 루프 뷰의 끊는 gate 넷과 맞지 않아 선언이 아무 뷰에도 걸리지 않는다(보고서 views[].cuts 의 gate 넷을 쓴다)",
                         ("41 §1.8", "U-24")) for net in sorted(set(declared_cuts) - engine))


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
    declared_cuts = _declared_loop_cuts(spec)
    s1v = build_s1v(s1, spec, count_budget=budget, declared=declared, structure=structure,
                    declared_loop_cuts=declared_cuts, stop_on_unsupported=False)
    unsupported = [_finding_line(f) for f in s1v.unsupported]
    review = [_finding_line(f) for f in s1v.review_needed] + [_finding_line(f) for f in _unmatched_loop_cuts(s1v, declared_cuts)]
    note = " has no stage_members facts" if path.is_file() else " absent"
    comparison = "performed" if declared else "not_performed: " + path.name + note
    status = STATUS_STOPPED if unsupported else STATUS_REVIEW if review else STATUS_OK
    code = 0 if status == STATUS_OK else exit_code_for(StructureUnresolvedError())
    report = {"circuit": circuit, "status": status, "exit_code": code, "count_budget": budget, "declared_comparison": comparison,
              "stop_reasons": unsupported, "review_needed": review, "views": [_view_summary(v) for v in s1v.views],
              "applied_facts": [list(f) for f in s1v.facts_applied], "ff_ratio_candidates": _ff_ratio_rows(s1v),
              "tables": structure_tables(s1v)}
    return _finish(report, s1v, output_dir, circuit)
