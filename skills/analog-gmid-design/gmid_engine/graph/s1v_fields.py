"""S1v 필드 계산 블록 -- S1 위에서 뷰·셀·구동 종류·stage·블록·극점 노드·루프를 유도해 S0 수준 필드 `graph/s1v` 에 쓴다
(설계 40 §2.4.2·§2.4.8 v1.9.1 D1, 41 §0 단계 A3·§1).

진입점: `s1v_fields`(`@compute_block`, writer `build_s1v`) -- `s1v_fields(snapshot, judged, count_budget, declared, facts, stale, declared_loop_cuts)`.

* reads = S1 필드 전부(`S1_READS`), extras: `judged` = spec 판정 제약 tuple(spec 이 없으면 빈 tuple -- 기본 전달 뷰만), `count_budget` = 계수 예산 N_S,
  `declared` = declared stage 묶음 ((출처, (소자 이름 tuple, ...)), ...)(대조용, U-50), `facts`·`stale` = `structure.json` 의 적용 가능한 ratified 사실·해시 불일치 기록,
  `declared_loop_cuts` = 안정도 제약이 선언된 루프 뷰의 끊는 gate 넷 이름들.
* writes `graph/s1v`(key `S1V_KEY`): `views`(ViewS1v tuple -- 블록·복합 블록·극점 노드·루프·끊는 점은 뷰 안 칸), `l_classes`, `findings`(뷰 밖 기록),
  `declared`(declared 대조 요약 ((출처, stage 묶음 수), ...)), `applied_facts`(적용한 ratified 사실 (개념, 대상)). 묶음 객체는 없다(v1.9.1 D1, 사본 금지).
* 순서: 뷰 수집(`collect_views`) -> 전달 뷰마다 `analyze_view` -> 전달 뷰의 (3) 루프가 만든 루프 뷰(끊는 점마다 하나, 중첩 Miller 내부 루프는 제외)를 같은 `analyze_view` 로 분석
  -> 루프 뷰 판정(포트쌍 CM 루프 대응 R31, 선언 안 된 안정도 제약, 루프 뷰 극성 = 그 뷰의 DC 사이클 극성) -> L 동치류(`l_equivalence_classes`) -> declared 대조(`declared_compare`)
  -> ratified 사실 대조(override 적용 기록·confirm 일치·`structure_fact_mismatch`·`structure_fact_orphan`, 40 §3.2-3).
* 사실 소비(40 §3.2-3): `drive_kind`·`ac_ground_exception` 은 `analyze_view` 에, `l_owner` 는 `l_equivalence_classes` 에 넘기고(override), `dc_role`·`matching_pair` 는 S1 이 이미
  적용했으며, `loop_role`·`feedforward_cell` 은 유도 결과와 대조한다(confirm). 전달 뷰의 전체 안정도 선언(`pm_ss_deg`)·gain 제약 뷰는 spec 제약에서 직접 모은다.
* 정지 판정(`unsupported_rule_branch`)은 이 블록이 아니라 진입점 `build_s1v` 가 필드를 읽어 한다 -- 블록은 기록을 그대로 쓴다.
"""
import dataclasses
import json
import types

from gmid_engine.core import compute_block, sorted_items

from .l_classes import l_equivalence_classes, RULE_FACT, RULE_NAME_ORDER
from .declared_compare import declared_compare
from .net_model import net_model
from .s1_values import (
    BASIS_FACT_MISMATCH,
    BUILD_S1V_WRITER,
    GRAPH_KEY,
    J_UNRESOLVED_GROUP,
    MATCH_BRANCH_SYMMETRIC,
    S1_READS,
    S1V_KEY,
    S1V_WRITES,
    STATUS_RATIFIED,
    STATUS_REVIEW_NEEDED,
)
from .s1v_values import (
    CONCEPT_AC_GROUND_EXCEPTION,
    CONCEPT_DC_ROLE,
    CONCEPT_DRIVE_KIND,
    CONCEPT_FEEDFORWARD_CELL,
    CONCEPT_L_OWNER,
    CONCEPT_LOOP_ROLE,
    CONCEPT_MATCHING_PAIR,
    CONCEPT_STAGE_MEMBERS,
    F_CM_LOOP_UNCONSTRAINED,
    F_DC_ROLE_UNRESOLVED,
    F_FACT_MISMATCH,
    F_FACT_ORPHAN,
    F_L_OWNER_NAME_ORDER,
    F_LOOP_POLARITY,
    F_LOOP_POLARITY_AC_ONLY,
    F_LOOP_POLARITY_CONFLICT,
    F_UNDECLARED_LOOP,
    FF_BIAS,
    FF_CELL,
    FF_LOAD,
    FF_SEPARATOR,
    MATCH_PAIR_VALUE,
    METRIC_GAIN_SS,
    METRIC_PM_SS,
    PORT_ROLE_DIFF_OUT_N,
    PORT_ROLE_DIFF_OUT_P,
    SEVERITY_INFO,
    SEVERITY_REVIEW,
    SEVERITY_UNSUPPORTED,
    SPEC_VIEW_LOOP,
    SPEC_VIEW_PORT,
    SPEC_VIEW_RATIO,
    SPEC_VIEW_TRANSFER,
    VIEW_SOURCE_DECLARED,
    BASIS_RATIFIED,
    Finding,
)
from .view_analysis import analyze_view
from .views import collect_views

_VIEW_MODES = (SPEC_VIEW_PORT, SPEC_VIEW_LOOP, SPEC_VIEW_TRANSFER, SPEC_VIEW_RATIO)


def _cm_pair(model, nodes):
    roles = {role: net for net, role in model.outputs}
    pair = (roles.get(PORT_ROLE_DIFF_OUT_P), roles.get(PORT_ROLE_DIFF_OUT_N))
    return None not in pair and all(net in nodes for net in pair)


def _loop_findings(view, cut, model, nodes, declared_cuts):
    pair = _cm_pair(model, nodes)
    if pair:
        return pair, (Finding(F_CM_LOOP_UNCONSTRAINED, SEVERITY_INFO, view.id, (cut[1],),
                              "포트쌍 CM 루프 대응(R31): 안정도 metric 은 pm_cm_ss_deg, 제약이 선언되지 않으면 T_cm 만 보고한다", ("40 §5", "H5")),)
    if cut[1] in declared_cuts:
        return pair, ()
    return pair, (Finding(F_UNDECLARED_LOOP, SEVERITY_UNSUPPORTED, view.id, (cut[1],),
                          "루프 뷰의 안정도 제약이 선언되지 않았다(포트쌍 CM 루프 대응이 아님)", ("41 §1.8", "U-24")),)


def _polarity(view_id, cut, polarity):
    """루프 뷰 극성 = 그 뷰에 속한 DC 사이클들의 극성(41 §1.12.4). (극성 값, 기록 tuple)."""
    dc, ac = polarity.get(cut, ((), ()))
    findings = []
    value = dc[0] if len(dc) == 1 else 0
    if len(dc) > 1:
        findings.append(Finding(F_LOOP_POLARITY_CONFLICT, SEVERITY_REVIEW, view_id, (cut[1],),
                                "루프 뷰에 속한 DC 사이클들의 극성이 서로 다르다: " + repr(dc), ("41 §1.12.4", "J7")))
    elif not dc:
        findings.append(Finding(F_LOOP_POLARITY, SEVERITY_REVIEW, view_id, (cut[1],),
                                "루프 뷰에 속한 DC 사이클이 하나도 없어 극성이 정의되지 않는다", ("41 §1.12.4", "J7")))
    if ac:
        findings.append(Finding(F_LOOP_POLARITY_AC_ONLY, SEVERITY_INFO, view_id, ac,
                                "커패시터를 지나 DC 극성이 없는 사이클의 수동소자(GB5 보상 후보)", ("41 §1.12.4",)))
    return value, tuple(findings)


def _constrained_keys(model, judged, metric):
    """`metric` 제약이 걸린 전달 뷰의 (여기, 감지) 키 집합. spec 의 해당 제약만 골라 `collect_views` 에 다시 넣는다(뷰 키 정의를 한 곳에 둔다)."""
    chosen = tuple(c for c in judged if c.metric == metric and c.view is not None and c.view.mode in _VIEW_MODES)
    if not chosen:
        return frozenset()
    seeds, _ = collect_views(model, types.SimpleNamespace(judged_constraints=chosen))
    return frozenset((s.excite, s.sense) for s in seeds if s.source == VIEW_SOURCE_DECLARED)


def _ff_values(views):
    """{소자: {`feedforward_cell` 값}} -- 전달 뷰들이 유도한 feedforward 묶음에서."""
    table = {}
    for view in views:
        for ff in view.feedforward:
            for kind, names in ((FF_CELL, ff.cells), (FF_BIAS, ff.bias_cells), (FF_LOAD, ff.load_cells)):
                for name in names:
                    table.setdefault(name, set()).add(kind + FF_SEPARATOR + ff.id)
    return table


def _ratify_derived(views, confirmed):
    """confirm 이 일치한 유도 레코드(루프 역할·feedforward 묶음)의 status 를 ratified 로 올리고 approval_id 를 붙인다(40 §3.2-3)."""
    out = []
    for v in views:
        roles = tuple(dataclasses.replace(r, status=STATUS_RATIFIED, approval_id=confirmed[key])
                      if (key := (CONCEPT_LOOP_ROLE, r.loop_id, r.role)) in confirmed else r for r in v.loop_roles)
        ffs = []
        for ff in v.feedforward:
            keys = [(CONCEPT_FEEDFORWARD_CELL, name, kind + FF_SEPARATOR + ff.id)
                    for kind, names in ((FF_CELL, ff.cells), (FF_BIAS, ff.bias_cells), (FF_LOAD, ff.load_cells)) for name in names]
            if keys and all(key in confirmed for key in keys):
                ff = dataclasses.replace(ff, status=STATUS_RATIFIED, approval_id=",".join(sorted({confirmed[key] for key in keys})))
            ffs.append(ff)
        out.append(dataclasses.replace(v, loop_roles=roles, feedforward=tuple(ffs)))
    return out


def _unresolved_role_groups(s1):
    """구조로 못 가르는 DC 역할 그룹(J-U3-c, S1 status review_needed)마다 `dc_role_unresolved_group` -- 그룹을 정하는 `dc_role` 사실이 필요하다(40 §3.2-3)."""
    groups = {record.evidence.group for _, record in s1.column("device", "dc_role")
              if record.status == STATUS_REVIEW_NEEDED and J_UNRESOLVED_GROUP in record.evidence.basis}
    return tuple(Finding(F_DC_ROLE_UNRESOLVED, SEVERITY_REVIEW, "", group,
                         "같은 gate·source 묶음에 diode 기준이 없고 gate 가 신호 넷이라 DC 역할을 구조로 못 가른다 -- dc_role 사실이 필요하다",
                         ("J-U3-c", "40 §3.2-3")) for group in sorted(groups))


def _fact_findings(s1, model, facts, views, roles, l_classes):
    """ratified 사실 대조(40 §3.2-3): (적용·확인한 (concept, subject) 목록, 기록 목록, confirm 일치 {(concept, subject, 값): approval_id}). override 가 쓰인 곳과 confirm 이 일치한 곳은
    applied, 어긋나면 mismatch, subject 가 없으면 orphan."""
    applied = []
    findings = []
    confirmed = {}
    dc_role = dict(s1.column("device", "dc_role"))
    pairs = {(g.members, g.status) for g in s1.value("graph", GRAPH_KEY, "matching_groups") if g.kind == MATCH_BRANCH_SYMMETRIC}
    ff = _ff_values(views)
    by_id = {}
    for role in roles:
        by_id.setdefault(role.loop_id, set()).add(role.role)
    view_ids = {v.id: v for v in views}
    elements = frozenset(model.mos_by_name) | {p.name for p in model.passives}
    for f in facts:
        mark = (f.concept, f.subject)

        def orphan():
            findings.append(Finding(F_FACT_ORPHAN, SEVERITY_REVIEW, "", (f.subject,),
                                    f.concept + " 사실의 대상을 엔진이 만들지 않았다(" + f.approval_id + ")", ("40 §3.2-3",)))

        def mismatch(derived):
            findings.append(Finding(F_FACT_MISMATCH, SEVERITY_REVIEW, "", (f.subject,),
                                    "concept=" + f.concept + " subject=" + f.subject + " derived=" + str(derived) + " ratified=" + f.value
                                    + " (" + f.approval_id + ")", ("40 §3.2-3",)))

        if f.concept == CONCEPT_STAGE_MEMBERS:
            continue
        if f.concept == CONCEPT_DRIVE_KIND:
            if f.subject not in model.nets:
                orphan()
            elif any(d.net == f.subject and d.basis == BASIS_RATIFIED for v in views for d in v.drive_kind):
                applied.append(mark)
        elif f.concept == CONCEPT_DC_ROLE:
            record = dc_role.get(f.subject)
            if record is None:
                orphan()
            elif BASIS_FACT_MISMATCH in record.evidence.basis:
                mismatch(record.evidence.basis[record.evidence.basis.index(BASIS_FACT_MISMATCH) + 1])
            elif record.status == STATUS_RATIFIED:
                applied.append(mark)
        elif f.concept == CONCEPT_LOOP_ROLE:
            derived = by_id.get(f.subject)
            if derived is None:
                orphan()
            elif f.value in derived:
                applied.append(mark)
                confirmed[(f.concept, f.subject, f.value)] = f.approval_id
            else:
                mismatch(",".join(sorted(derived)))
        elif f.concept == CONCEPT_FEEDFORWARD_CELL:
            derived = ff.get(f.subject)
            if derived is None:
                orphan()
            elif f.value in derived:
                applied.append(mark)
                confirmed[(f.concept, f.subject, f.value)] = f.approval_id
            else:
                mismatch(",".join(sorted(derived)))
        elif f.concept == CONCEPT_AC_GROUND_EXCEPTION:
            view = view_ids.get(f.value)
            if f.subject not in model.nets or view is None:
                orphan()
            elif f.subject in view.ac_ground:
                applied.append(mark)
        elif f.concept == CONCEPT_MATCHING_PAIR:
            names = tuple(sorted(json.loads(f.subject)))
            if not all(name in elements for name in names):
                orphan()
            elif f.value == MATCH_PAIR_VALUE and (names, STATUS_RATIFIED) in pairs:
                applied.append(mark)
        elif f.concept == CONCEPT_L_OWNER:
            # 동치류가 엔진 유도와 같고 주인이 멤버면 적용(l_classes 가 덮음). 멤버가 겹치는 동치류가 있으나 다르거나 주인이 멤버가 아니면 mismatch, 겹치는 동치류가 없으면 orphan
            names = tuple(sorted(json.loads(f.subject)))
            exact = next((c for c in l_classes if c.members == names), None)
            overlap = [c for c in l_classes if set(c.members) & set(names)]
            if exact is not None and exact.owner_rule == RULE_FACT and exact.owner == f.value:
                applied.append(mark)
            elif exact is not None or overlap:
                derived = exact.owner if exact is not None else ";".join(",".join(c.members) for c in overlap)
                mismatch(derived)
            else:
                orphan()
    return tuple(sorted(set(applied))), tuple(findings), confirmed


@compute_block(BUILD_S1V_WRITER, reads=S1_READS, writes=S1V_WRITES)
def s1v_fields(projection):
    judged, count_budget, declared, facts, stale, declared_loop_cuts = projection.extras
    s1 = projection                     # S1 필드 투영 -- `column`·`value` 질의만 쓴다(net_model·l_classes·사실 대조)
    model = net_model(s1)
    seeds, view_findings = collect_views(model, types.SimpleNamespace(judged_constraints=judged))
    pm_keys = _constrained_keys(model, judged, METRIC_PM_SS)
    gain_keys = _constrained_keys(model, judged, METRIC_GAIN_SS)
    flags = tuple(((s.excite, s.sense) in pm_keys, (s.excite, s.sense) in gain_keys) for s in seeds)
    ratified = {f.subject: f.value for f in facts if f.concept == CONCEPT_DRIVE_KIND}
    exceptions = tuple((f.subject, f.value) for f in facts if f.concept == CONCEPT_AC_GROUND_EXCEPTION)

    def exceptions_of(view_id):
        return frozenset(net for net, view in exceptions if view == view_id)

    results = [analyze_view(model, seed, "transfer:" + str(i), count_budget, ratified, exceptions_of("transfer:" + str(i)), flags[i][0])
               for i, seed in enumerate(seeds)]
    cut_nodes = {}
    cut_polarity = {}
    for result in results:
        for cut, nodes in result.cut_nodes.items():
            cut_nodes.setdefault(cut, set()).update(nodes)
        for cut, (dc, ac) in result.cut_polarity.items():
            old_dc, old_ac = cut_polarity.get(cut, ((), ()))
            cut_polarity[cut] = (tuple(sorted(set(old_dc) | set(dc))), tuple(sorted(set(old_ac) | set(ac))))
    views = [r.view for r in results]
    for cut in sorted(cut_nodes):
        seed = next(s for r in results for s in r.loop_seeds if s.cut == cut)
        view_id = "loop:" + cut[0] + ":" + cut[1]
        loop_view = analyze_view(model, seed, view_id, count_budget, ratified, exceptions_of(view_id)).view
        pair, extra = _loop_findings(loop_view, cut, model, cut_nodes[cut], frozenset(declared_loop_cuts))
        polarity, polarity_findings = _polarity(view_id, cut, cut_polarity)
        views.append(dataclasses.replace(loop_view, cm_pair=pair, polarity=polarity,
                                         findings=loop_view.findings + extra + polarity_findings))
    gain_views = frozenset(r.view.id for r, flag in zip(results, flags) if flag[1])
    owner_facts = tuple((tuple(sorted(json.loads(f.subject))), f.value, f.approval_id) for f in facts if f.concept == CONCEPT_L_OWNER)
    l_classes = l_equivalence_classes(s1, model, views, gain_views, owner_facts)
    mismatches = declared_compare(views, tuple(declared))
    all_roles = tuple(r for v in views for r in v.loop_roles)
    applied, fact_findings, confirmed = _fact_findings(s1, model, facts, views, all_roles, l_classes)
    views = _ratify_derived(views, confirmed)
    owner_order = tuple(Finding(F_L_OWNER_NAME_ORDER, SEVERITY_REVIEW, "", c.members,
                                "L 동치류 주인을 tail·전류 출처·주경로 규칙으로 못 정해 이름 순서로 골랐다: " + c.owner, ("41 §1.12.5", "DEC-17"))
                        for c in l_classes if c.owner_rule == RULE_NAME_ORDER and c.status == STATUS_REVIEW_NEEDED)
    findings = sorted_items(set(view_findings + tuple(stale) + mismatches + fact_findings + owner_order + _unresolved_role_groups(s1)),
                            key=lambda f: (f.code, f.view, f.subject, f.detail))
    return {("graph", "views"): {S1V_KEY: tuple(views)}, ("graph", "l_classes"): {S1V_KEY: l_classes},
            ("graph", "findings"): {S1V_KEY: findings},
            ("graph", "declared"): {S1V_KEY: tuple((source, len(stages)) for source, stages in declared)},
            ("graph", "applied_facts"): {S1V_KEY: applied}}
