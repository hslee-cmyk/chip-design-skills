"""성능 제약 `human.constraints` 와 결정 대기 제약 `human.pending_constraints` (설계 design_spec_format 1.5·1.7).

진입점: `constraint_declaration(raw, raw_pending, topology, metric_catalog)
         -> (tuple[ConstraintDecl] | None, tuple[(metric, 결정 ID)] | None, tuple[SchemaHit])`.

제약 항목 `{metric, op, value | value_from_constraint | value_from_file, view?, source}`:
* `metric` -- `metric_catalog`(주입된 MOD5 레지스트리 이름표) 원소(`metric_unknown`, 옛 이름이면 `legacy_name`). 이름이
  아직 레지스트리에 없는 제약은 `{"pending": <ID>}` 로 적는다(값·출처는 남고 `metric_decision` 에 ID, `judged` False,
  `view` None).
* `op` ∈ `OPS`(`op_value`). 값 자리는 `value`(유한 수) / `value_from_constraint`(같은 파일의 제약 metric 이름) /
  `value_from_file`(`<회로>#<이름>`) 중 정확히 하나(`value_and_ref`; `value` 비유한 수는 `type`). 참조 문자열 안 옛 이름은
  `legacy_name`. 참조는 `source.kind == reference` 와 함께만(`ref_kind_mismatch`), 해석은 `spec_refs`.
* `view` -- metric 의 `view_kind`(`MetricSignature`)로 판정: None(뷰 없음)은 view 가 오면 `view_not_applicable`; `transfer`·`loop`·
  `output_port` 는 없으면 포트 뷰 -- topology output 포트가 정확히 하나가 아니면 `view_required`; `loop`·`output_port`
  (`PENDING_ONLY_VIEW_KINDS`)의 선언 view 는 결정 대기 표지만 받고 그 밖은 `view_not_defined_yet`(A·β 절단점·출력 포트
  모양은 7a design, metrics CONTRACT M1); `ratio` 는 `{num, den}` 필수
  (`view_required`). 전달 뷰 모양 = `{ac_excite: {넷: 진폭}, sense_p, sense_n(null 가능), sense_mode}`
  (`SENSE_MODES`; differential 이면 sense_n 필수, single_ended 면 null) -- 형식 위반 `type`, 넷이 어느 단자에도 없으면
  `view_net_unknown`. `{"pending": <ID>}` 뷰는 받는다(뷰 정의 결정 대기).
* `constraint_duplicate` -- 같은 (metric, op, view)가 두 번. metric 이나 view 가 결정 대기인 제약은 비교할 키가 아직
  없어 이 검사 밖이다(그 표지가 `pending` 에 남아 실행 전 정지하므로 조용히 통과하지 않는다).
* 판정 여부 `judged`: `user_spec` True, `pending_spice` False(U-17), `reference` 는 참조 해석 때 대상에서 정한다.
`pending_constraints` = `[{metric, decision}]`(metric 은 이름표 원소, decision 은 결정 ID 형식) -- 보고서가 '보고만(결정
대기)'과 '보고만(선언 안 함)'을 구분하는 데 쓴다. 판정·실행 정지 대상이 아니다.
`topology` 가 None 이면 포트 뷰·넷 교차 검사를 하지 않는다.
"""
from ._spec_fields import (LEGACY_NAMES, REF_KEYS, at, finite_number, is_pending, key_hits, pending_decision,
                           value_slot)
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .spec_model import ConstraintDecl, ExciteSense, ViewDecl
from .spec_schema import PENDING_ID_PATTERN
from .spec_sources import PENDING_SPICE, REFERENCE, USER_SPEC, source_declaration_checks
from .topology_model import SchemaHit

WHERE = "human.constraints"
PENDING_WHERE = "human.pending_constraints"
OPS = (">=", "<=")
ITEM_KEYS = ("metric", "op", "value", "view", "source") + REF_KEYS
TRANSFER_KEYS = ("ac_excite", "sense_p", "sense_n", "sense_mode")
RATIO_KEYS = ("num", "den")
SENSE_MODES = ("differential", "single_ended")
# 선언 뷰 모양이 아직 정의되지 않은 view_kind(core `VIEW_KINDS` 의 부분집합): loop 는 A·β 절단점, output_port 는 관측만
# 받는 출력 포트 모양이 7a design 몫이다(metrics CONTRACT 3.10·3.11·M1). 선언 view 는 결정 대기 표지만 받는다.
PENDING_ONLY_VIEW_KINDS = ("loop", "output_port")
OUTPUT_DIRECTION = "output"


def _transfer(raw, where, nets, hits):
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, "전달 뷰는 객체여야 한다: " + type(raw).__name__))
        return None
    before = len(hits)
    hits.extend(key_hits(raw, TRANSFER_KEYS, where))
    excite = raw.get("ac_excite")
    if not isinstance(excite, dict) or not excite or not all(finite_number(v) for v in excite.values()):
        hits.append(SchemaHit("type", at(where, "ac_excite"), "ac_excite 는 비어 있지 않은 {넷: 진폭(유한 수)} 객체여야 한다"))
        excite = {}
    mode = raw.get("sense_mode")
    sense_p = raw.get("sense_p")
    sense_n = raw.get("sense_n")
    if mode not in SENSE_MODES:
        hits.append(SchemaHit("type", at(where, "sense_mode"), "sense_mode 는 " + repr(SENSE_MODES) + " 중 하나: "
                              + repr(mode)))
    if not isinstance(sense_p, str) or not sense_p:
        hits.append(SchemaHit("type", at(where, "sense_p"), "sense_p 는 넷 이름이어야 한다: " + repr(sense_p)))
    differential = mode == SENSE_MODES[0]
    if differential != (isinstance(sense_n, str) and bool(sense_n)) or (not differential and sense_n is not None):
        hits.append(SchemaHit("type", at(where, "sense_n"), "sense_n 은 differential 이면 넷 이름, single_ended 면 null: "
                              + repr(sense_n)))
    if nets is not None:
        for net in tuple(excite) + tuple(n for n in (sense_p, sense_n) if isinstance(n, str)):
            if net not in nets:
                hits.append(SchemaHit("view_net_unknown", where, "뷰 넷 " + repr(net) + " 이 어느 단자에도 없다", (net,)))
    if len(hits) != before:
        return None
    return ExciteSense(tuple(sorted((n, float(v)) for n, v in excite.items())), sense_p, sense_n, mode)


def _view(raw, signature, where, topology, nets, hits):
    place = at(where, "view")
    if is_pending(raw):
        return ViewDecl("pending", decision=pending_decision(raw))
    kind = signature.view_kind
    if kind is None:
        if raw is not None:
            hits.append(SchemaHit("view_not_applicable", place, "이 metric 은 뷰를 쓰지 않는다(view_kind None)"))
        return ViewDecl("none")
    if kind in PENDING_ONLY_VIEW_KINDS and raw is not None:
        hits.append(SchemaHit("view_not_defined_yet", place, "view_kind " + repr(kind) + " 의 선언 뷰 모양은 아직 정의되지 "
                              "않았다(7a design, metrics CONTRACT M1) -- view 를 빼서 포트 뷰를 쓰거나 결정 대기 표지로 적는다"))
        return None
    if raw is None:
        if kind == "ratio":
            hits.append(SchemaHit("view_required", where, "ratio metric 은 view {num, den} 선언이 필수다"))
            return None
        if topology is not None and sum(1 for p in topology.ports if p.direction == OUTPUT_DIRECTION) != 1:
            hits.append(SchemaHit("view_required", where, "output 포트가 하나가 아니라 포트 뷰가 정해지지 않는다 -- "
                                  "view(sense_p·sense_n·sense_mode)를 선언한다"))
            return None
        return ViewDecl("port")
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", place, "view 는 객체여야 한다: " + type(raw).__name__))
        return None
    if kind == "ratio":
        before = len(hits)
        hits.extend(key_hits(raw, RATIO_KEYS, place))
        num = _transfer(raw.get("num"), at(place, "num"), nets, hits)
        den = _transfer(raw.get("den"), at(place, "den"), nets, hits)
        return ViewDecl("ratio", num=num, den=den) if len(hits) == before else None
    transfer = _transfer(raw, place, nets, hits)
    return ViewDecl("transfer", transfer=transfer) if transfer is not None else None


def _item(raw, where, topology, nets, catalog, hits):
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, "제약 항목은 객체여야 한다: " + type(raw).__name__))
        return None
    before = len(hits)
    hits.extend(key_hits(raw, ITEM_KEYS, where))
    source, source_hits = source_declaration_checks(raw.get("source"), where, "constraints")
    hits.extend(source_hits)
    metric = raw.get("metric")
    metric_decision = None
    signature = None
    if is_pending(metric):
        metric_decision = pending_decision(metric)
        metric = None
    else:
        if isinstance(metric, str) and metric in LEGACY_NAMES:
            hits.append(SchemaHit("legacy_name", at(where, "metric"), "옛 metric 이름 " + repr(metric) + " (N3.16)"))
        elif not isinstance(metric, str) or metric not in catalog:
            hits.append(SchemaHit("metric_unknown", at(where, "metric"),
                                  "metric " + repr(metric) + " 이 metric 레지스트리 이름표에 없다"))
        else:
            signature = catalog[metric]
    op = raw.get("op")
    if op not in OPS:
        hits.append(SchemaHit("op_value", at(where, "op"), "op 는 " + repr(OPS) + " 중 하나여야 한다: " + repr(op)))
    value, ref = value_slot(raw, where, None if source is None else source.kind == REFERENCE, hits)
    view = None
    if metric_decision is not None:
        if "view" in raw and not is_pending(raw["view"]):
            hits.append(SchemaHit("view_not_applicable", at(where, "view"), "metric 이 결정 대기인 제약은 뷰를 정할 수 없다"))
    elif signature is not None:
        view = _view(raw.get("view"), signature, where, topology, nets, hits)
    if len(hits) != before:
        return None
    # 참조(reference)의 판정 여부는 대상에서 정해진다 -- 해석 전에는 None(spec_refs 가 채운다).
    # metric 이 결정 대기인 제약은 잴 metric 이 없어 판정하지 않는다(값·출처는 기록으로 남는다).
    judged = True if source.kind == USER_SPEC else (False if source.kind == PENDING_SPICE else None)
    if metric_decision is not None:
        judged = False
    return ConstraintDecl(metric, op, value, judged, view, source, metric_decision=metric_decision, ref=ref)


def _pending_list(raw, catalog, hits):
    if raw is None:
        return ()
    if not isinstance(raw, list):
        hits.append(SchemaHit("type", PENDING_WHERE, "pending_constraints 는 list 여야 한다: " + type(raw).__name__))
        return None
    out = []
    for index, item in enumerate(raw):
        where = at(PENDING_WHERE, index)
        if not isinstance(item, dict):
            hits.append(SchemaHit("type", where, "항목은 {metric, decision} 객체여야 한다"))
            continue
        hits.extend(key_hits(item, ("metric", "decision"), where))
        metric = item.get("metric")
        decision = item.get("decision")
        if not isinstance(metric, str) or metric not in catalog:
            hits.append(SchemaHit("metric_unknown", at(where, "metric"), "metric " + repr(metric) + " 이 이름표에 없다"))
        if not isinstance(decision, str) or PENDING_ID_PATTERN.fullmatch(decision) is None:
            hits.append(SchemaHit("pending_id_format", at(where, "decision"), "결정 ID 형식 밖: " + repr(decision)))
        out.append((metric, decision))
    return tuple(out)


def constraint_declaration(raw, raw_pending, topology, metric_catalog):
    hits = []
    nets = None
    if topology is not None:
        nets = mos_terminal_nets(topology.devices) | two_terminal_nets(topology.passives + topology.sources)
    constraints = None
    if not isinstance(raw, list):
        hits.append(SchemaHit("type", WHERE, "constraints 는 list 여야 한다(없으면 []): " + type(raw).__name__))
    else:
        parsed = [_item(item, at(WHERE, i), topology, nets, metric_catalog, hits) for i, item in enumerate(raw)]
        seen = set()
        for index, decl in enumerate(parsed):
            if decl is None or decl.metric is None or decl.view.mode == "pending":
                continue
            key = (decl.metric, decl.op, decl.view)
            if key in seen:
                hits.append(SchemaHit("constraint_duplicate", at(WHERE, index), "같은 (metric, op, view) 제약이 두 번: "
                                      + repr((decl.metric, decl.op)), (decl.metric,)))
            seen.add(key)
        constraints = tuple(parsed)
    pending = _pending_list(raw_pending, metric_catalog, hits)
    if hits:
        return None, None, tuple(hits)
    return constraints, pending, ()
