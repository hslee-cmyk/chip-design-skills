"""참조 해석 `value_from_constraint`·`value_from_file` (설계 design_spec_format 1.4·1.7, DEC-20, F6).

진입점: `resolve_spec_references(constraints, targets, load_referenced)
         -> (constraints, targets, tuple[PendingMark], tuple[SchemaHit])`.

* `value_from_constraint: <metric>` -- 같은 파일에서 metric 이 그 이름인 제약 **하나**의 값(0개 `ref_unresolved`,
  둘 이상 `ref_ambiguous`). 대상이 다시 참조면 따라가고, 되돌아오면 `ref_cycle`.
* `value_from_file: "<회로>#<이름>"` -- `load_referenced(<회로>)` 가 돌려준 그 회로의 로드된 `SizingSpecDoc` 에서
  `<이름>` 이 보상 목표 키면 그 목표 값, 아니면 metric 이 그 이름인 제약 하나의 값. 형식이 틀리면 `ref_unresolved`.
  `load_referenced` 는 (doc 또는 None, hits) 를 돌려준다 -- 대상 파일 거부·순환(`ref_cycle`)·대상 topology 지문 불일치는
  그 hits 로 온다(`spec_load` 가 대상 topology 를 읽어 대상 spec 을 같은 로더로 읽는다).
* 판정 여부: 참조 제약의 `judged` = 대상 제약의 `judged`(대상이 `pending_spice` 면 판정 안 함, U-17). 보상 목표처럼
  판정이 없는 대상이면 True.
* 대상 값이 결정 대기면 참조한 칸도 결정 대기다: 값 None + `value_decision`(목표는 `decision`), 그 ID 를 PendingMark 로
  낸다(실행 전 정지 목록에 들어간다).
"""
import dataclasses

from .spec_model import PendingMark
from .topology_model import SchemaHit

FILE_SEPARATOR = "#"


def _resolve_in(constraints, targets, name, where, visiting, follow):
    """`constraints`·`targets` 안에서 `name` 을 찾아 (value, judged, decision) 또는 hit 를 낸다. `follow` 가 None 이면
    로드가 끝난(참조가 이미 해석된) 다른 파일의 선언이라 `ref` 를 따라가지 않고 해석된 값을 읽는다."""
    for key, decl in targets:
        if key == name:
            if getattr(decl, "decision", None) is not None:
                return (None, True, decl.decision), None
            if decl.ref is not None and follow is not None:
                return follow(("target", key), decl.ref, where, visiting)
            return (decl.value, True, None), None
    found = tuple(i for i, c in enumerate(constraints) if c.metric == name)
    if not found:
        return None, SchemaHit("ref_unresolved", where, "참조 대상 " + repr(name) + " 이 없다", (name,))
    if len(found) > 1:
        return None, SchemaHit("ref_ambiguous", where, "참조 대상 metric " + repr(name) + " 제약이 둘 이상", (name,))
    target = constraints[found[0]]
    if target.ref is not None and follow is not None:
        return follow(("constraint", found[0]), target.ref, where, visiting)
    return (target.value, target.judged, target.value_decision), None


def resolve_spec_references(constraints, targets, load_referenced):
    hits = []
    marks = []
    cache = {}

    def follow(node, ref, where, visiting):
        if node in visiting:
            return None, SchemaHit("ref_cycle", where, "참조가 순환한다: " + repr(ref[1]))
        if node in cache:
            return cache[node], None
        key, text = ref
        if key == "value_from_constraint":
            result, hit = _resolve_in(constraints, (), text, where, visiting | {node}, follow)
        else:
            circuit, sep, name = text.partition(FILE_SEPARATOR)
            if not sep or not circuit or not name:
                return None, SchemaHit("ref_unresolved", where, "value_from_file 형식은 '<회로>#<이름>': " + repr(text))
            doc, file_hits = load_referenced(circuit)
            if doc is None:
                elements = tuple(sorted({h.rule for h in file_hits}))
                rule = "ref_cycle" if "ref_cycle" in elements else "ref_file_rejected"
                return None, SchemaHit(rule, where, "참조 파일 " + repr(circuit) + " 을 로드하지 못했다: "
                                       + repr(elements), elements)
            result, hit = _resolve_in(doc.constraints, doc.compensation_targets, name, where, frozenset(), None)
        if hit is None:
            cache[node] = result
        return result, hit

    out_constraints = []
    for index, decl in enumerate(constraints):
        if decl.ref is None:
            out_constraints.append(decl)
            continue
        where = "human.constraints[" + str(index) + "]." + decl.ref[0]
        result, hit = follow(("constraint", index), decl.ref, where, frozenset())
        if hit is not None:
            hits.append(hit)
            continue
        value, judged, decision = result
        if decision is not None:
            marks.append(PendingMark(where, decision))
        judged = bool(judged) and decl.metric_decision is None  # metric 결정 대기 제약은 참조여도 판정 안 함
        out_constraints.append(dataclasses.replace(decl, value=value, judged=judged, value_decision=decision))
    out_targets = []
    for key, decl in targets:
        if getattr(decl, "ref", None) is None:
            out_targets.append((key, decl))
            continue
        where = "human.compensation_targets." + key + "." + decl.ref[0]
        if decl.ref[0] == "value_from_constraint":
            result, hit = _resolve_in(constraints, (), decl.ref[1], where, frozenset(), follow)
        else:
            result, hit = follow(("target", key), decl.ref, where, frozenset())
        if hit is not None:
            hits.append(hit)
            continue
        value, _judged, decision = result
        if decision is not None:
            marks.append(PendingMark(where, decision))
        out_targets.append((key, dataclasses.replace(decl, value=value, decision=decision)))
    return tuple(out_constraints), tuple(out_targets), tuple(marks), tuple(hits)

