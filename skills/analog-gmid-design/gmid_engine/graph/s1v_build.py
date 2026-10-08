"""SP1 진입점 -- S1 위에서 뷰·셀·구동 종류·stage·블록·극점 노드·루프를 유도해 S1v 를 만든다 (설계 40 §10.1, 41 §0 단계 A3·§1).

진입점: `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None, stop_on_unsupported=True) -> S1v`.

* `s1` = `build_s1` 결과. `spec` = `SizingSpecDoc` 또는 None(None 이면 기본 전달 뷰만). `count_budget` = 계수 예산 N_S(양의 정수 -- 사이클 열거·복합 블록
  경로 수의 상한. 시간과 무관해 같은 입력은 늘 같은 S1v, 41 §0).
* `declared` = declared stage 묶음 ((출처, (소자 이름 tuple, ...)), ...) -- 유도의 입력이 아니라 대조용(U-50). `structure` = `load_structure_facts` 결과(ratified
  사실과 해시 불일치 기록) 또는 None. `declared_loop_cuts` = 안정도 제약이 선언된 루프 뷰의 끊는 gate 넷 이름들(단계 A 진입점이 spec 에서 계산해 넘긴다).
* 순서: 뷰 수집(`collect_views`) -> 전달 뷰마다 `analyze_view` -> 전달 뷰의 (3) 루프가 만든 루프 뷰(끊는 점마다 하나, 중첩 Miller 내부 루프는 제외)를 같은 `analyze_view` 로 분석
  -> 루프 뷰 판정(포트쌍 CM 루프 대응 R31, 선언 안 된 안정도 제약, 루프 뷰 극성 = 그 뷰의 DC 사이클 극성) -> L 동치류(`l_equivalence_classes`) -> declared 대조(`declared_compare`)
  -> ratified 사실 대조(override 적용 기록·confirm 일치·`structure_fact_mismatch`·`structure_fact_orphan`, 40 §3.2-3).
* 사실 소비(40 §3.2-3): `drive_kind`·`ac_ground_exception` 은 `analyze_view` 에 넘기고(override), `dc_role`·`matching_pair` 는 `build_s1` 이 이미 적용했으며(S1 안), `loop_role`·
  `feedforward_cell` 은 유도 결과와 대조한다(confirm). 전달 뷰의 전체 안정도 선언(`pm_ss_deg`)·gain 제약 뷰는 spec 제약에서 직접 모은다(authoring 소유 파일을 고치지 않는다).
* **정지**: `기록만`(unsupported_rule_branch) 기록이 하나라도 있으면 `StructureUnresolvedError`(reason `unsupported_rule_branch`, exit 2)로 멈춘다 --
  `stop_on_unsupported=False` 는 구조 표·측정을 위해 기록을 그대로 돌려받는 진단 모드다(정지 규칙을 우회하는 경로가 아니다: 호출자가 `S1v.unsupported` 를 보고
  멈춰야 한다). `review_needed` 는 정지가 아니라 기록이며 GB4 앞에서 `S1v.review_needed` 로 정지한다.
* 같은 `previous`(키 = S1 지문·뷰 입력·예산·S1v 규칙 코드 지문·declared·ratified·선언 루프+안정도/gain 선언 뷰) 면 그 객체를 그대로 돌려준다.
"""
import dataclasses
import json
import types

from gmid_engine.core import StructureUnresolvedError, fp_of, sorted_items

from .l_classes import l_equivalence_classes, RULE_NAME_ORDER
from .declared_compare import declared_compare
from .net_model import net_model
from .s1_values import (
    BASIS_FACT_MISMATCH,
    GRAPH_KEY,
    J_UNRESOLVED_GROUP,
    MATCH_BRANCH_SYMMETRIC,
    STATUS_RATIFIED,
    STATUS_REVIEW_NEEDED,
    UNSUPPORTED_RULE_BRANCH,
)
from .s1_model import S1Graph
from .s1v_key import s1v_rule_fp
from .s1v_values import (
    CONCEPT_AC_GROUND_EXCEPTION,
    CONCEPT_DC_ROLE,
    CONCEPT_DRIVE_KIND,
    CONCEPT_FEEDFORWARD_CELL,
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
    VIEW_TRANSFER,
    BASIS_RATIFIED,
    Finding,
    S1v,
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


def _stop(s1v, model):
    names = frozenset(model.mos_by_name) | {p.name for p in model.passives} | {s.name for s in model.sources}
    unsupported = s1v.unsupported
    devices = sorted({name for f in unsupported for name in f.subject if name in names})
    raise StructureUnresolvedError(devices=devices, detail={
        "reason": UNSUPPORTED_RULE_BRANCH,
        "rule_branch": unsupported[0].code,
        "branches": tuple(sorted({f.code for f in unsupported})),
        "findings": tuple(f.code + "|" + f.view + "|" + ",".join(f.subject) for f in unsupported),
    })


def _constrained_keys(model, spec, metric):
    """`metric` 제약이 걸린 전달 뷰의 (여기, 감지) 키 집합. spec 의 해당 제약만 골라 `collect_views` 에 다시 넣는다(뷰 키 정의를 한 곳에 둔다)."""
    chosen = () if spec is None else tuple(c for c in spec.judged_constraints
                                           if c.metric == metric and c.view is not None and c.view.mode in _VIEW_MODES)
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


def _fact_findings(s1, model, facts, views, roles):
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
    return tuple(sorted(set(applied))), tuple(findings), confirmed


def build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None,
              stop_on_unsupported=True):
    if not isinstance(s1, S1Graph):
        raise TypeError("build_s1v: s1 은 graph.build_s1 결과 S1Graph 여야 한다")
    if isinstance(count_budget, bool) or not isinstance(count_budget, int) or count_budget < 1:
        raise TypeError("build_s1v: count_budget 은 1 이상 int 여야 한다")
    if previous is not None and not isinstance(previous, S1v):
        raise TypeError("build_s1v: previous 는 S1v 여야 한다")
    model = net_model(s1)
    seeds, view_findings = collect_views(model, spec)
    facts = () if structure is None else structure.facts
    stale = () if structure is None else structure.findings
    pm_keys = _constrained_keys(model, spec, METRIC_PM_SS)
    gain_keys = _constrained_keys(model, spec, METRIC_GAIN_SS)
    flags = tuple(((s.excite, s.sense) in pm_keys, (s.excite, s.sense) in gain_keys) for s in seeds)
    key = (s1.key, fp_of(seeds), count_budget, s1v_rule_fp(), fp_of(tuple(declared)), fp_of(facts),
           fp_of((tuple(declared_loop_cuts), flags)))
    if previous is not None and previous.key == key:
        return previous
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
    l_classes = l_equivalence_classes(s1, model, views, gain_views)
    mismatches = declared_compare(views, tuple(declared))
    all_roles = tuple(r for v in views for r in v.loop_roles)
    applied, fact_findings, confirmed = _fact_findings(s1, model, facts, views, all_roles)
    views = _ratify_derived(views, confirmed)
    owner_order = tuple(Finding(F_L_OWNER_NAME_ORDER, SEVERITY_REVIEW, "", c.members,
                                "L 동치류 주인을 tail·전류 출처·주경로 규칙으로 못 정해 이름 순서로 골랐다: " + c.owner, ("41 §1.12.5", "DEC-17"))
                        for c in l_classes if c.owner_rule == RULE_NAME_ORDER)
    findings = sorted_items(set(view_findings + stale + mismatches + fact_findings + owner_order + _unresolved_role_groups(s1)),
                            key=lambda f: (f.code, f.view, f.subject, f.detail))
    s1v = S1v(key, tuple(views), l_classes, findings, tuple((source, len(stages)) for source, stages in declared), applied)
    if stop_on_unsupported and s1v.unsupported:
        _stop(s1v, model)
    return s1v
