"""성능 제약 `human.constraints` 와 결정 대기 제약 `human.pending_constraints` (설계 design_spec_format 1.5·1.7, 7a design 2.9·3.1).

진입점: `constraint_declaration(raw, raw_pending, topology, metric_catalog, feedback)
         -> (tuple[ConstraintDecl] | None, tuple[(metric, 결정 ID)] | None, tuple[SchemaHit])`.

제약 항목 `{metric, op, value | value_from_constraint | value_from_file, view?, source}`:
* `metric` -- `metric_catalog`(주입된 MOD5 레지스트리 이름표) 원소(`metric_unknown`, 옛 이름이면 `legacy_name`). 이름이
  아직 레지스트리에 없는 제약은 `{"pending": <ID>}` 로 적는다(값·출처는 남고 `metric_decision` 에 ID, `judged` False,
  `view` None).
* `op` ∈ `OPS`(`op_value`). 값 자리는 `value`(유한 수) / `value_from_constraint`(같은 파일의 제약 metric 이름) /
  `value_from_file`(`<회로>#<이름>`) 중 정확히 하나(`value_and_ref`; `value` 비유한 수는 `type`). 참조 문자열 안 옛 이름은
  `legacy_name`. 참조는 `source.kind == reference` 와 함께만(`ref_kind_mismatch`), 해석은 `spec_refs`.
* `view` -- metric 의 `view_kind`(`MetricSignature`)로 판정. `{"pending": <ID>}` 뷰는 어느 종류든 받는다(뷰 정의 결정 대기).
  view 를 적지 않으면 기본 뷰(`spec_views.default_views` -- 로드 한 번에 한 번 유도, 선언에서만):
  - None(뷰 없음): view 가 오면 `view_not_applicable`, 결과 mode `none`.
  - `transfer`: 없으면 포트 뷰(mode `port`, 입력 포트 role 가중·출력 포트 관측) -- 입력 포트가 차동쌍 1개·단일 1개가
    아니거나 출력 포트가 단일 1개·차동쌍 1개가 아니면 `view_required`. 선언 모양 `{ac_excite: {넷: 진폭}, sense_p,
    sense_n(null 가능), sense_mode}`(`SENSE_MODES`; differential 이면 sense_n 필수, single_ended 면 null 또는 없음).
  - `loop`(`pm_ss_deg`): 적지 않는다 -- feedback·ports 에서 유도한 루프 뷰(mode `loop`, β 루프 절단·가중 또는 β = 1
    포트 뷰), feedback 이 결정 대기면 mode `pending`(그 ID 전파). 유도 불가면 `view_required`. 결정 대기 아닌 선언 view 는
    `view_not_applicable`. 단 명시 모양 `{"cut_weights": …}`(7a design 2.9 예약 -- 계약에만 있고 첫 소비 spec 이 생길 때
    구현)은 조용히 무시하지 않고 `view_shape_not_supported` 로 거부한다.
  - `cm_loop` 선언 view [CM 2026-10-08]: `{"cm_sense_elements": [MOS…]}` 만 받는다(닫힌 어휘; 그 밖 모양은 `view_not_applicable`). 구조 분류가 모호할 때 필요하고,
    분류가 명확하면 구조와 같아야 한다. 이 제약의 `source.kind` 는 `user_spec`(`cm_sense_source`). 규칙: `cm_sense_unknown`, `cm_sense_not_on_output`,
    `cm_sense_disagrees`, `cm_partition_ambiguous`(선언해도 절단 교차 검사 실패), `cm_pair_missing`, `cm_switched`.
  - `cm_loop`(`pm_cm_ss_deg`, 공통 모드 루프 PM): `loop` 와 같이 view 를 적지 않는다(결정 대기 표지만) -- 선언된 차동 출력 포트 쌍의 출력 CM 주입
    뷰(mode `cm_output`, `spec_views.default_views().cm_loop`). 차동 출력쌍이 없거나 스위치드 커패시터 선언이 있는 회로의 이 제약은 `view_required`(사유 포함).
  - `output_port`(`rout_ss_ohm`): 감지 전용 `{sense_p, sense_n?, sense_mode}`(mode `sense`). `ac_excite` 는
    `view_excite_not_allowed`(여기는 DEC-66 이 고정), 감지 넷이 고정 넷(레일·입력 포트·gate 전용 미구동 넷)이면
    `view_sense_fixed_net`. 적지 않으면 출력 포트가 1개일 때 그 넷 single_ended, 아니면 `view_required`.
  - `ratio`: `{num, den}` 필수(`view_required`), 각 칸은 전달 뷰 모양.
  형식 위반 `type`, 넷이 어느 단자에도 없으면 `view_net_unknown`.
* `constraint_duplicate` -- 같은 (metric, op, view)가 두 번. metric 이나 view 가 결정 대기인 제약은 비교할 키가 아직
  없어 이 검사 밖이다(그 표지가 `pending` 에 남아 실행 전 정지하므로 조용히 통과하지 않는다).
* 판정 여부 `judged`: `user_spec` True, `pending_spice` False(U-17), `reference` 는 참조 해석 때 대상에서 정한다.
`pending_constraints` = `[{metric, decision}]`(metric 은 이름표 원소, decision 은 결정 ID 형식) -- 보고서가 '보고만(결정
대기)'과 '보고만(선언 안 함)'을 구분하는 데 쓴다. 판정·실행 정지 대상이 아니다.
`topology` 가 None 이면 기본 뷰 유도·넷 교차 검사를 하지 않는다(유도하지 않은 mode 만 담는다 -- 로드는 meta 위반으로 거부된다).
`feedback` = `element_value_declaration` 의 feedback 결과(이름순 tuple / `PendingMark` / 거부면 None).
"""
from ._spec_fields import (LEGACY_NAMES, REF_KEYS, at, finite_number, is_pending, key_hits, pending_decision,
                           value_slot)
from ._terminal_nets import mos_terminal_nets, two_terminal_nets
from .spec_model import ConstraintDecl, ExciteSense, SenseDecl, ViewDecl
from .spec_schema import PENDING_ID_PATTERN
from .spec_sources import PENDING_SPICE, REFERENCE, USER_SPEC, source_declaration_checks
from .spec_views import SENSE_MODES, default_views
from .topology_model import SchemaHit

WHERE = "human.constraints"
PENDING_WHERE = "human.pending_constraints"
OPS = (">=", "<=")
ITEM_KEYS = ("metric", "op", "value", "view", "source") + REF_KEYS
EXCITE_KEY = "ac_excite"
SENSE_KEYS = ("sense_p", "sense_n", "sense_mode")
TRANSFER_KEYS = (EXCITE_KEY,) + SENSE_KEYS
RATIO_KEYS = ("num", "den")
# 명시 루프 뷰 모양 `{"cut_weights": {<절단 넷>: 가중}}` -- 7a design 2.9 예약(계약에만 정의, 첫 소비 spec 과 함께 구현).
RESERVED_LOOP_VIEW_KEY = "cut_weights"
CM_SENSE_KEY = "cm_sense_elements"       # cm_loop 뷰 선언 키(소비자 MOS 이름 list, source user_spec)
_UNRESOLVED = (("transfer", "port"), ("loop", "loop"), ("cm_loop", "loop"), ("output_port", "sense"))


def _sense_fields(raw, where, nets, hits):
    """감지 칸(sense_p·sense_n·sense_mode) -> (sense_p, sense_n, mode). 위반은 hits 에 더한다."""
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
        for net in (n for n in (sense_p, sense_n) if isinstance(n, str)):
            if net not in nets:
                hits.append(SchemaHit("view_net_unknown", where, "뷰 넷 " + repr(net) + " 이 어느 단자에도 없다", (net,)))
    return sense_p, sense_n, mode


def _transfer(raw, where, nets, hits):
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, "전달 뷰는 객체여야 한다: " + type(raw).__name__))
        return None
    before = len(hits)
    hits.extend(key_hits(raw, TRANSFER_KEYS, where))
    excite = raw.get(EXCITE_KEY)
    if not isinstance(excite, dict) or not excite or not all(finite_number(v) for v in excite.values()):
        hits.append(SchemaHit("type", at(where, EXCITE_KEY), "ac_excite 는 비어 있지 않은 {넷: 진폭(유한 수)} 객체여야 한다"))
        excite = {}
    if nets is not None:
        for net in excite:
            if net not in nets:
                hits.append(SchemaHit("view_net_unknown", where, "뷰 넷 " + repr(net) + " 이 어느 단자에도 없다", (net,)))
    sense_p, sense_n, mode = _sense_fields(raw, where, nets, hits)
    if len(hits) != before:
        return None
    return ExciteSense(tuple(sorted((n, float(v)) for n, v in excite.items())), sense_p, sense_n, mode)


def _sense_view(raw, where, nets, views, hits):
    """출력 포트 뷰(감지 전용, 7a design 3.1)."""
    if not isinstance(raw, dict):
        hits.append(SchemaHit("type", where, "출력 포트 뷰는 객체여야 한다: " + type(raw).__name__))
        return None
    before = len(hits)
    hits.extend(key_hits(raw, TRANSFER_KEYS, where))
    if EXCITE_KEY in raw:
        hits.append(SchemaHit("view_excite_not_allowed", at(where, EXCITE_KEY), "출력 포트 뷰는 감지 전용이다 -- 여기는 "
                              "DEC-66 이 고정(모든 여기원 진폭 0 + 감지 노드 전류 주입), ac_excite 를 적지 않는다"))
    sense_p, sense_n, mode = _sense_fields(raw, where, nets, hits)
    if views is not None:
        for net in (n for n in (sense_p, sense_n) if isinstance(n, str)):
            if net in views.fixed_nets:
                hits.append(SchemaHit("view_sense_fixed_net", where, "감지 넷 " + repr(net) + " 이 고정 넷(레일·입력 포트·"
                                      "gate 전용 미구동 넷)이다 -- 고정 노드에는 시험 전류를 넣을 수 없다", (net,)))
    if len(hits) != before:
        return None
    return ViewDecl("sense", sense=SenseDecl(sense_p, sense_n, mode))


def _derived(found, where, hits):
    if isinstance(found, str):
        hits.append(SchemaHit("view_required", where, found + " -- view 를 선언한다"))
        return None
    return found


def _cm_declared_view(raw, place, views, source, hits):
    """공통 모드 루프 뷰 선언 `{"cm_sense_elements": [소비자(CM 감지) MOS 이름…]}` -- 구조 분류(`spec_views.cm_loop_view`)를 덮어쓴다. 닫힌 어휘: 키 하나,
    값은 서로 다른 이름 list(빈 list 가능 = 소비자 없음), source.kind == user_spec 필수(`cm_sense_source`), 그 밖 규칙은 `cm_loop_view` 의 문제 규칙."""
    before = len(hits)
    hits.extend(key_hits(raw, (CM_SENSE_KEY,), place))
    names = raw.get(CM_SENSE_KEY)
    if not isinstance(names, list) or not all(isinstance(n, str) and n for n in names) or len(set(names)) != len(names):
        hits.append(SchemaHit("type", at(place, CM_SENSE_KEY), "cm_sense_elements 는 서로 다른 MOS 이름 list 여야 한다: " + repr(names)))
    if source is not None and source.kind != USER_SPEC:
        hits.append(SchemaHit("cm_sense_source", place, "CM 감지 요소 선언은 source.kind == user_spec 이어야 한다: " + repr(source.kind)))
    if len(hits) != before:
        return None
    if views is None or views.cm_declared is None:
        return ViewDecl("loop")
    view, problems = views.cm_declared(tuple(names))
    for rule, reason in problems:
        hits.append(SchemaHit(rule, at(place, CM_SENSE_KEY), reason))
    return view


def _view(raw, signature, where, nets, views, hits, source=None):
    place = at(where, "view")
    if is_pending(raw):
        return ViewDecl("pending", decision=pending_decision(raw))
    kind = signature.view_kind
    if kind is None:
        if raw is not None:
            hits.append(SchemaHit("view_not_applicable", place, "이 metric 은 뷰를 쓰지 않는다(view_kind None)"))
        return ViewDecl("none")
    if kind == "cm_loop" and isinstance(raw, dict) and CM_SENSE_KEY in raw:
        return _cm_declared_view(raw, place, views, source, hits)
    if kind in ("loop", "cm_loop") and raw is not None:
        if isinstance(raw, dict) and RESERVED_LOOP_VIEW_KEY in raw:
            hits.append(SchemaHit("view_shape_not_supported", place, "명시 루프 뷰 {cut_weights} 는 계약에 예약된 모양이지만 "
                                  "아직 구현하지 않았다(첫 소비 spec 과 함께 구현 -- 7a design 2.9, SPEC_CONTRACT 7절 S3)"))
        else:
            hits.append(SchemaHit("view_not_applicable", place, "loop metric 은 view 를 적지 않는다 -- 루프 뷰는 spec "
                                  "feedback·topology ports 에서 유도한다(7a design 2.9). 결정 대기면 표지로 적는다"))
        return None
    if raw is None:
        if kind == "ratio":
            hits.append(SchemaHit("view_required", where, "ratio metric 은 view {num, den} 선언이 필수다"))
            return None
        if views is None:
            return ViewDecl(dict(_UNRESOLVED)[kind])
        return _derived({"transfer": views.port, "loop": views.loop, "cm_loop": views.cm_loop, "output_port": views.sense}[kind], where, hits)
    if kind == "output_port":
        return _sense_view(raw, place, nets, views, hits)
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


def _item(raw, where, nets, views, catalog, hits):
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
        view = _view(raw.get("view"), signature, where, nets, views, hits, source)
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


def constraint_declaration(raw, raw_pending, topology, metric_catalog, feedback):
    hits = []
    nets = views = None
    if topology is not None:
        nets = mos_terminal_nets(topology.devices) | two_terminal_nets(topology.passives + topology.sources)
        views = default_views(topology, feedback)
    constraints = None
    if not isinstance(raw, list):
        hits.append(SchemaHit("type", WHERE, "constraints 는 list 여야 한다(없으면 []): " + type(raw).__name__))
    else:
        parsed = [_item(item, at(WHERE, i), nets, views, metric_catalog, hits) for i, item in enumerate(raw)]
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
