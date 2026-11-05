"""card IT-2d test 공용 -- 손 toy 회로를 사이징 경로(spec -> build_s1 -> 커널 컨텍스트 -> 탐색 컨텍스트 -> 평가)로 올리는 helper.

회로·LUT·θ 는 search 하네스(`tests/search/conftest.py`: r4 toy LUT = VDSAT 열 있음, 회로 C = M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd),
`theta_r4c`)를 그대로 쓴다. 입력 DC 선언 모드(`engine`·`pending`·값)만 다르게 쓰려고 spec 을 여기서 만든다.
이 파일은 test 가 아니다(접두 it2d_). 기대값은 여기서 만들지 않는다.
"""
from __future__ import annotations

import json
from pathlib import Path

from .conftest import spec_json

PENDING_ELEMENT = "pending"


def build(tmp, lut, topo, *, elements=(), constraints=(), input_dc="engine", feedback=(), archive_root=None):
    """-> SimpleNamespace(td, spec, dc, sctx). input_dc: "engine" | "pending"(SP-2 결정 대기) | 숫자(V, 선언 값).
    elements: (이름, kind, 값 | None(engine) | PENDING_ELEMENT(수동소자 값 미선언))."""
    import types

    import search.conftest as SC
    from gmid_engine.authoring import load_sizing_spec, load_topology
    from gmid_engine.graph import build_s1
    from gmid_engine.metrics import metric_catalog
    from gmid_engine.search import SearchSettings, build_search_context
    from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec

    tmp = Path(tmp)
    case_dir = tmp / "case"
    case_dir.mkdir(parents=True, exist_ok=True)
    tp = case_dir / (topo["topology_name"] + ".topology.json")
    tp.write_text(json.dumps(topo, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    els = [(n, k, None if v == PENDING_ELEMENT else v) for n, k, v in elements]
    value = input_dc if isinstance(input_dc, (int, float)) else None
    doc = spec_json(td, SC.SUPPLIES, els, feedback, constraints, value)
    for n, _, v in elements:
        if v == PENDING_ELEMENT:
            doc["human"]["element_values"][n] = {"pending": "SP-1"}
    if input_dc == "pending":
        doc["human"]["input_dc"] = {"pending": "SP-2"}
    sp = case_dir / (topo["topology_name"] + ".sizing_spec.json")
    sp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    acc = SC.new_access(lut)
    inputs = dc_inputs_from_spec(spec)
    run = SC.fresh_run()
    s1 = build_s1(td, dict(inputs.supplies_v), **run)
    dc = build_kernel_context(s1, inputs, acc, **run)
    pdk, rule = SC.write_decls(tmp / "pdk")
    settings = SearchSettings(600.0, 40, None, tuple(SC.SRC), None)
    sctx = build_search_context(dc, spec, settings, archive_root, pdk, rule, code_fp=SC.CODE_FP)
    return types.SimpleNamespace(td=td, spec=spec, dc=dc, sctx=sctx)


def sealed_ss(case, theta, cells, structure=None):
    """봉인 점 하나를 평가해 (EvalResult, SsEvaluation) -- search 의 `evaluate` 와 같은 점을 `ss_evaluate` 로 직접 부른다(test_kernel 방식)."""
    from gmid_engine.metrics import ss_evaluate
    from gmid_engine.search import STATUS_SEALED, evaluate

    th = tuple(sorted(dict(theta).items()))
    r = evaluate(case.sctx, th, cells)
    assert r.status == STATUS_SEALED, r.status          # 전제: 봉인 점(아니면 이 사례는 무효)
    ref = ss_evaluate(r.evaluation.sealed, case.dc, dict(theta), case.sctx.ss_constraints, (), junction=case.sctx.junction,
                      structure=structure)
    return r, ref


def by_metric(ss):
    """MetricBundle -> {metric: MetricResult} (같은 metric 이 여러 뷰면 마지막)."""
    return {req.metric: res for req, res in ss.entries}


def undefined_codes(res):
    return {u.code for u in (res.undefined or ())}


def field(report, name):
    """보고 항목(칸 이름 접근 또는 (이름, 값) 쌍 tuple 둘 다) 읽기."""
    if hasattr(report, name):
        return getattr(report, name)
    return dict(report)[name]
