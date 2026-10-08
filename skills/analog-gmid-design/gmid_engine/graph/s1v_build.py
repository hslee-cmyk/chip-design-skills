"""SP1 진입점 -- S1 위에서 뷰·셀·구동 종류·stage·블록·극점 노드·루프를 유도해 S1v 를 만든다 (설계 40 §10.1, 41 §0 단계 A3·§1).

진입점: `build_s1v(s1, spec, *, count_budget, declared=(), structure=None, declared_loop_cuts=(), previous=None, stop_on_unsupported=True) -> S1v`.

* `s1` = `build_s1` 결과. `spec` = `SizingSpecDoc` 또는 None(None 이면 기본 전달 뷰만). `count_budget` = 계수 예산 N_S(양의 정수 -- 사이클 열거·복합 블록
  경로 수의 상한. 시간과 무관해 같은 입력은 늘 같은 S1v, 41 §0).
* `declared` = declared stage 묶음 ((출처, (소자 이름 tuple, ...)), ...) -- 유도의 입력이 아니라 대조용(U-50). `structure` = `load_structure_facts` 결과(ratified
  사실과 해시 불일치 기록) 또는 None. `declared_loop_cuts` = 안정도 제약이 선언된 루프 뷰의 끊는 gate 넷 이름들.
* 순서: 뷰 수집(`collect_views`) -> 전달 뷰마다 `analyze_view` -> 전달 뷰의 (3) 루프가 만든 루프 뷰(끊는 점마다 하나)를 같은 `analyze_view` 로 분석
  -> 루프 뷰 판정(포트쌍 CM 루프 대응 R31, 선언 안 된 안정도 제약) -> L 동치류(`l_equivalence_classes`) -> declared 대조(`declared_compare`).
* **정지**: `기록만`(unsupported_rule_branch) 기록이 하나라도 있으면 `StructureUnresolvedError`(reason `unsupported_rule_branch`, exit 2)로 멈춘다 --
  `stop_on_unsupported=False` 는 구조 표·측정을 위해 기록을 그대로 돌려받는 진단 모드다(정지 규칙을 우회하는 경로가 아니다: 호출자가 `S1v.unsupported` 를 보고
  멈춰야 한다). `review_needed` 는 정지가 아니라 기록이며 GB4 앞에서 `S1v.review_needed` 로 정지한다.
* 같은 `previous`(키 = S1 지문·뷰 입력·예산·S1v 규칙 코드 지문·declared·ratified·선언 루프) 면 그 객체를 그대로 돌려준다.
"""
import dataclasses

from gmid_engine.core import StructureUnresolvedError, fp_of, sorted_items

from .l_classes import l_equivalence_classes
from .declared_compare import declared_compare
from .net_model import net_model
from .s1_values import UNSUPPORTED_RULE_BRANCH
from .s1_model import S1Graph
from .s1v_key import s1v_rule_fp
from .s1v_values import (
    CONCEPT_DRIVE_KIND,
    F_CM_LOOP_UNCONSTRAINED,
    F_UNDECLARED_LOOP,
    PORT_ROLE_DIFF_OUT_N,
    PORT_ROLE_DIFF_OUT_P,
    SEVERITY_INFO,
    SEVERITY_UNSUPPORTED,
    VIEW_TRANSFER,
    BASIS_RATIFIED,
    Finding,
    S1v,
)
from .view_analysis import analyze_view
from .views import collect_views


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
    key = (s1.key, fp_of(seeds), count_budget, s1v_rule_fp(), fp_of(tuple(declared)), fp_of(facts), fp_of(tuple(declared_loop_cuts)))
    if previous is not None and previous.key == key:
        return previous
    ratified = {f.subject: f.value for f in facts if f.concept == CONCEPT_DRIVE_KIND}
    results = [analyze_view(model, seed, "transfer:" + str(i), count_budget, ratified) for i, seed in enumerate(seeds)]
    cut_nodes = {}
    for result in results:
        for cut, nodes in result.cut_nodes.items():
            cut_nodes.setdefault(cut, set()).update(nodes)
    views = [r.view for r in results]
    for cut in sorted(cut_nodes):
        seed = next(s for r in results for s in r.loop_seeds if s.cut == cut)
        loop_view = analyze_view(model, seed, "loop:" + cut[0] + ":" + cut[1], count_budget, ratified).view
        pair, extra = _loop_findings(loop_view, cut, model, cut_nodes[cut], frozenset(declared_loop_cuts))
        views.append(dataclasses.replace(loop_view, cm_pair=pair, findings=loop_view.findings + extra))
    l_classes = l_equivalence_classes(s1, model, views)
    mismatches = declared_compare(views, tuple(declared))
    applied = tuple(sorted({(CONCEPT_DRIVE_KIND, d.net) for v in views for d in v.drive_kind if d.basis == BASIS_RATIFIED}))
    findings = sorted_items(set(view_findings + stale + mismatches), key=lambda f: (f.code, f.view, f.subject, f.detail))
    s1v = S1v(key, tuple(views), l_classes, findings, tuple((source, len(stages)) for source, stages in declared), applied)
    if stop_on_unsupported and s1v.unsupported:
        _stop(s1v, model)
    return s1v
