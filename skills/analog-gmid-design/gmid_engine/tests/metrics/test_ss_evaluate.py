"""`ss_evaluate`(봉인 스냅샷 -> ss_dev -> metrics_ss -> metrics_dc) -- metrics CONTRACT 7.6 (+ 7.7 S-6·S-10, 접합 S-11~S-13,
DEC-92 수동 θ S-14~S-16, 7.9 Q2·Q4·Q5).

회로: CS 증폭기 M1 nmos (out, in, gnd) + 저항 부하 R1 (vdd, out, 값 = θ resistance) + CL (out, gnd, 값 = spec 1 pF).
DC 점은 실제 sizing 경로(build_kernel_context -> size_and_seal, toy LUT r6)로 만든다. 봉인 7 판정 결과와 무관하게 같은 점을 쓰려고
test 가 7.8 시연과 같이 `SealedSnapshot(ev.snapshot, ev.report)` 로 명시적으로 감싼다.
접합 묶음 `junction`(7.6 필수 키워드): 8.5 소비자 호출 그대로 `JunctionSource.from_decls(PDK 선언, LUT 규칙 선언, ctx.lut.memo.lut)` --
선언은 conftest toy 선언(core 9.1 형식), sky130 실선언 경로는 원본이 있을 때만(7.2 작성자 실측 예와 대조).
기대값: 봉인 스냅샷의 dc_op·dc_v(입력)에서 conftest oracle_ss(npz 해석식)·oracle_junction(8.2 독립 식)·폐형식으로 계산 --
gain = 20·log10(gm/(gds + 1/R)), rout = 1/(gds + 1/R), power = 1.8·(1.8 − V_out)/R, area = W·L.
"""
from __future__ import annotations

import dataclasses
import math

import pytest

from gmid_engine.metrics import (
    JUNCTION_LUT_RULE,
    JunctionSource,
    MetricBundle,
    SsEvaluation,
    junction_caps,
    metrics_dc,
    metrics_ss,
    ss_dev,
    ss_evaluate,
)
from gmid_engine.sizing import (
    METRICS_KEY,
    DcEvaluation,
    SealedSnapshot,
    build_kernel_context,
    dc_inputs_from_spec,
    size_and_seal,
)

from .conftest import COUNT_FIELDS, block_row, fresh_run, row_delta
from .conftest import (
    JUNCTION_RTOL,
    schema_of,
    LUT_WM,
    bundle_map,
    load_case,
    load_lut_v2,
    lut_access,
    lut_ln_idu,
    oracle_junction,
    oracle_ss,
    read_decls,
    ref_caps,
    rel_close,
    topo_doc,
    toy_junction,
)

SUP = {"vdd": 1.8, "gnd": 0.0}
I0, R0, VGS0, L0 = 1e-5, 9e4, 0.6, 1e-6
CONS = (
    ("gain_ss_db", ">=", 20.0, None),
    ("gain_ss_db", "<=", 80.0, None),            # 같은 (metric, view) 두 번 -> 요청 하나(중복 제거)
    ("rout_ss_ohm", "<=", 1e6, None),
    ("pm_ss_deg", ">=", 45.0, None),             # feedback [] -> β = 1 포트 뷰
    ("parasitic_pm_ss_deg", ">=", 45.0, None),
    ("power_dc_w", "<=", 1e-3, None),
    ("area_search_m2", "<=", 1e-9, None),
)
BLOCKS = (ss_dev, metrics_ss, metrics_dc)
APPROX = (("cap", "lut_cgs_cgb"), ("gmb", "lut_gmbs_column"), ("junction", "pdk_bsim4_lut_rule_diffusion"))


def _counts(ctx, blocks=BLOCKS):
    """[XRUN-F1 card B C1] ctx 실행 계수의 블록 행(옛 블록 객체 stats 대체 -- 블록은 상태가 없다, C4)."""
    return {b.name: block_row(ctx.counters, b.name) for b in blocks}


def _since(ctx, before, blocks=BLOCKS):
    """_counts 의 before 이후 증분 -- 속성 calls·reuses·grafts·replays·computes·recomputes_same_input."""
    import types
    now = _counts(ctx, blocks)
    return {n: types.SimpleNamespace(**dict(zip(COUNT_FIELDS, row_delta(now[n], before[n])))) for n in now}


def _topo(cl_engine=False):
    return topo_doc("sse_cs_res" + ("_e" if cl_engine else ""), mos=[("M1", "nmos", "out", "in", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))


def theta(i=I0, r=R0, vgs=VGS0, l1=L0, cl=None):
    """cl: [r5] engine CL 의 θ capacitance 값(None 이면 성분 없음)."""
    vout = 1.8 - i * r
    th = {("L", "M1"): l1, ("ln_idu", "M1"): lut_ln_idu("nmos", vgs, vout, 0.0),
          ("current", "R1"): i, ("resistance", "R1"): r}
    if cl is not None:
        th[("capacitance", "CL")] = cl
    return th


def build(tmp, cl_engine=False, cons=CONS, th=None):
    """(spec, ctx, ev, junction) -- spec 로더 -> dc_inputs_from_spec -> build_s1 -> build_kernel_context -> size_and_seal,
    접합 묶음은 S0 당 1회 from_decls(toy 선언, ctx.lut.memo.lut)."""
    from gmid_engine.graph import build_s1
    els = (("R1", "resistor", None), ("CL", "capacitor", None if cl_engine else 1e-12))
    td, spec = load_case(tmp / "case", _topo(cl_engine), SUP, els, (), cons)
    inputs = dc_inputs_from_spec(spec)
    lut = load_lut_v2(tmp / "lut")
    run = fresh_run()                 # [XRUN-F1 card B C0·C6] 실행 하나 = 이 build 하나
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, lut_access(lut), **run)
    ev = size_and_seal(ctx, theta() if th is None else th)
    return spec, ctx, ev, toy_junction(tmp / "junction", ctx.lut.memo.lut)


# [XRUN-F1 card B 규칙 M M-d] KernelContext(실행 두 객체를 칸으로 쥠)를 돌려주므로 function 범위(test 하나 = 실행 하나)
@pytest.fixture
def base(tmp_path_factory):
    spec, ctx, ev, js = build(tmp_path_factory.mktemp("sse"))
    sealed = SealedSnapshot(ev.snapshot, ev.report)
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    return spec, ctx, ev, sealed, res, js


def _expected(snap, r=R0):
    op = snap.value("device", "M1", "dc_op")
    ss = oracle_ss(op, "slice", "lut_cgs_cgb")
    vout = snap.value("node", "out", "dc_v")
    g_out = ss["gds"] + 1.0 / r
    return dict(gain_db=20.0 * math.log10(ss["gm"] / g_out), rout=1.0 / g_out, i_vdd=(1.8 - vout) / r,
                power=1.8 * (1.8 - vout) / r, area=op.W * op.L, ss=ss)


def test_input_dc_evaluation_is_dc_evaluation(base):
    """입력 전제: size_and_seal 결과는 DcEvaluation -- test 는 그 스냅샷을 명시적으로 SealedSnapshot 으로 감싼다."""
    _, _, ev, _, _, _ = base
    assert isinstance(ev, DcEvaluation)


def test_result_shape_and_lineage(base):
    """SsEvaluation(snapshot, ss, dc, lineage): ss·dc = 그 필드 값, lineage = DcEvaluation(snapshot, report, SealedSnapshot)."""
    _, _, _, sealed, res, _ = base
    assert isinstance(res, SsEvaluation)
    assert isinstance(res.ss, MetricBundle) and isinstance(res.dc, MetricBundle)
    assert res.ss is res.snapshot.value("graph", METRICS_KEY, "metrics_ss")
    assert res.dc is res.snapshot.value("graph", METRICS_KEY, "metrics_dc")
    lin = res.lineage
    assert isinstance(lin, DcEvaluation) and isinstance(lin.sealed, SealedSnapshot)
    assert lin.snapshot is res.snapshot and lin.sealed.snapshot is res.snapshot
    assert lin.report is sealed.report and lin.sealed.report is sealed.report
    assert set(dict(res.snapshot.column("device", "ss_dev"))) == {"M1"}


def test_requests_split_and_dedup(base):
    """view_kind 있는 metric 만 metrics_ss 로(중복 (metric, view) 제거·문서 순서), dc 묶음은 7.5 의 고정 3개."""
    _, _, _, _, res, _ = base
    assert [q.metric for q, _ in res.ss.entries] == ["gain_ss_db", "rout_ss_ohm", "pm_ss_deg", "parasitic_pm_ss_deg"]
    assert [q.metric for q, _ in res.dc.entries] == ["power_dc_w", "supply_current_dc", "area_search_m2"]


def test_values_against_closed_form(base):
    """ss 값 = 봉인 op 의 독립 소신호(npz) + 폐형식, dc 값 = 봉인 dc_v·R 의 손계산."""
    _, _, _, _, res, _ = base
    exp = _expected(res.snapshot)
    ss = res.snapshot.value("device", "M1", "ss_dev")
    for f in ("gm", "gds", "gmb", "cgs", "cgd", "cgb"):
        assert rel_close(getattr(ss, f), exp["ss"][f], 1e-12), f
    m = bundle_map(res.ss)
    assert rel_close(m["gain_ss_db"].value, exp["gain_db"], 1e-12)
    assert rel_close(m["rout_ss_ohm"].value, exp["rout"], 1e-12)
    assert m["pm_ss_deg"].value == m["parasitic_pm_ss_deg"].value          # β = 1 (I-15·S-3)
    d = bundle_map(res.dc)
    assert rel_close(d["power_dc_w"].value, exp["power"], 1e-12)
    assert rel_close(d["supply_current_dc"].value, exp["i_vdd"], 1e-12)
    assert rel_close(d["area_search_m2"].value, exp["area"], 1e-12)


def test_s11_junction_caps_and_approximation(base):
    """S-11: ss_dev 의 cdb·csb = 같은 dc_op·JunctionSource 로 부른 junction_caps 값(비트) = 독립 8.2 식(상대 오차),
    junction_model == JUNCTION_LUT_RULE, approximations 에 ("junction", "pdk_bsim4_lut_rule_diffusion")."""
    _, _, _, _, res, js = base
    op = res.snapshot.value("device", "M1", "dc_op")
    ss = res.snapshot.value("device", "M1", "ss_dev")
    jc = junction_caps(js.params_of(op.kind), js.pre_layout_geometry(LUT_WM, op.W / LUT_WM), op.vds + op.vsb, op.vsb,
                       js.temp_c)
    assert (ss.cdb, ss.csb) == (jc.cdb, jc.csb)
    cdb, csb = oracle_junction(op)
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL) and rel_close(ss.csb, csb, JUNCTION_RTOL)
    assert ss.cdb > 0.0 and ss.csb > 0.0
    assert ss.junction_model == JUNCTION_LUT_RULE == "pdk_bsim4_lut_rule_diffusion"
    assert ("junction", "pdk_bsim4_lut_rule_diffusion") in res.ss.approximations
    assert tuple(res.ss.approximations) == APPROX                          # 7.4: 집합 정렬
    assert not any(v == "pending_pdk_junction_params" for _, v in res.ss.approximations)


def test_junction_enters_frequency_metrics(tmp_path, base):
    """접합 용량이 실제로 계에 스탬프된다: 접합 파라미터만 바꾼 묶음 -> 주파수 metric(pm_ss_deg)이 바뀌고 DC 이득은 그대로."""
    spec, ctx, _, sealed, res, js = base
    from .conftest import TOY_JUNCTION
    params = {k: dict(v) for k, v in TOY_JUNCTION.items()}
    for f in ("cjd", "cjswd", "cjswgd"):
        params["nmos"][f] *= 20.0                   # drain 쪽(out 노드) 용량만 크게
    js2 = toy_junction(tmp_path / "j2", ctx.lut.memo.lut, params=params)
    r2 = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js2)
    a, b = bundle_map(res.ss), bundle_map(r2.ss)
    assert a["gain_ss_db"].value == b["gain_ss_db"].value
    assert a["pm_ss_deg"].value != b["pm_ss_deg"].value
    assert r2.snapshot.value("device", "M1", "ss_dev").cdb > res.snapshot.value("device", "M1", "ss_dev").cdb


def test_counted_rails_default_undeclared(base):
    """counted_rails 기본 () -> supply_current_dc = counted_rails_undeclared(Q4), 전력은 값."""
    spec, ctx, _, sealed, _, js = base
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, junction=js)
    d = bundle_map(res.dc)
    assert d["supply_current_dc"].value is None
    assert [u.code for u in d["supply_current_dc"].undefined] == ["counted_rails_undeclared"]
    assert d["power_dc_w"].value is not None


@pytest.mark.parametrize("bad", ["dc_evaluation", "snapshot", "none"])
def test_s10_only_sealed_snapshot_accepted(base, bad):
    """S-10 / DEC-67: SealedSnapshot 아닌 값(DcEvaluation·GraphSnapshot·None) -> TypeError."""
    spec, ctx, ev, _, _, js = base
    arg = {"dc_evaluation": ev, "snapshot": ev.snapshot, "none": None}[bad]
    before = _counts(ctx)
    with pytest.raises(TypeError):
        ss_evaluate(arg, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    assert all(s.calls == 0 for s in _since(ctx, before).values())          # 거부는 블록 호출 전


def test_ctx_must_be_kernel_context(base):
    spec, ctx, _, sealed, _, js = base
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx.base, theta(), spec.constraints, junction=js)


def test_s13_junction_keyword_required(base):
    """S-13: junction 없이 부르면 TypeError(필수 키워드, 기본값 없음 -- 옛 대기 경로를 남기지 않는다)."""
    spec, ctx, _, sealed, _, _ = base
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",))
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints)


@pytest.mark.parametrize("bad", ["none", "params_tuple", "junction_params", "pdk_decl", "dict", "positional_only"])
def test_s13_junction_must_be_junction_source(base, bad):
    """S-13: JunctionSource 아닌 값(None·묶음의 일부·선언 그대로·dict) -> TypeError. 키워드 전용이라 위치 인자로도 못 준다."""
    spec, ctx, _, sealed, _, js = base
    if bad == "positional_only":
        with pytest.raises(TypeError):
            ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), (), js)
        return
    val = {"none": None, "params_tuple": js.params, "junction_params": js.params_of("nmos"),
           "pdk_decl": js.lut_rule_decl, "dict": {"temp_c": js.temp_c}}[bad]
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), junction=val)


def test_s13_negative_check_valid_junction_accepted(base):
    """S-13 대조: 같은 인자에 JunctionSource 를 주면 예외 없음(위 TypeError 가 junction 때문임을 확인)."""
    spec, ctx, _, sealed, _, js = base
    assert isinstance(js, JunctionSource)
    r = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    assert isinstance(r, SsEvaluation)


def test_theta_checked(base):
    """θ = check_theta(θ 스키마 필드, ...) -- 키 빠짐은 ValueError(sizing 5.1)."""
    spec, ctx, _, sealed, _, js = base
    th = theta()
    del th[("resistance", "R1")]
    with pytest.raises(ValueError):
        ss_evaluate(sealed, ctx, th, spec.constraints, junction=js)


def test_s10_passive_theta_argument_removed(base):
    """S-10 [r5]: passive_theta 인자 삭제 -- 6번째 위치 인자·passive_theta 키워드 모두 TypeError(junction 을 바르게 줘도,
    블록 호출 전)."""
    spec, ctx, _, sealed, _, js = base
    before = _counts(ctx)
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), (), junction=js)
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), passive_theta=(("CL", 1e-12),), junction=js)
    assert all(s.calls == 0 for s in _since(ctx, before).values())


@pytest.mark.parametrize("case", ["spec_valued", "not_passive", "unknown", "theta_resistance_too", "rule_and_theta"])
def test_passive_value_two_sources_or_non_passive_rejected(base, case):
    """7.6 [r5]: passive_values 의 출처(spec 값 ∪ θ resistance ∪ θ capacitance·ss_resistance ∪ 구조 규칙 값)에서 이름이 S1
    수동소자가 아니거나 같은 소자 값이 두 출처면 ValueError. 정상 경로(build_kernel_context)는 이런 스키마를 만들지 않으므로
    θ 스키마 필드(graph/kernel: theta_schema)를 손으로 바꿔 계약 위반 표지를 직접 만든다(θ 는 그 스키마의 components 에 맞춘다)."""
    from gmid_engine.sizing import ZeroCancel
    spec, ctx, _, sealed, _, js = base
    s = schema_of(ctx)
    th = theta()
    zc = s.zero_cancel
    extra = {"spec_valued": ("capacitance", "CL"),           # CL 은 spec 값 1 pF -> 두 출처
             "not_passive": ("capacitance", "M1"),           # MOS
             "unknown": ("capacitance", "nope"),             # S1 에 없는 이름
             "theta_resistance_too": ("ss_resistance", "R1"),  # R1 은 이미 θ resistance
             "rule_and_theta": None}[case]
    comps = s.components
    if extra is not None:
        comps = tuple(sorted(comps + (extra,)))
        th[extra] = 1e-12 if extra[0] == "capacitance" else 5e4
    else:                                                    # 구조 규칙 값(R1 = 1/gm(M1))과 θ resistance R1 -> 두 출처
        zc = (ZeroCancel("R1", "out", ("in",), ("M1",), None),)
    # [U17 ①-b] θ 스키마는 S0 수준 필드 graph/kernel: theta_schema(40 v1.9.1 §2.4.8 D8, writer dc_theta_schema) -- 그 필드를 손으로 바꿔 쓴다
    from gmid_engine.sizing import KERNEL_KEY
    tampered = ctx.base.write(ctx.base.writers.writer_of("graph", "theta_schema"), "test-tampered-schema",
                              {("graph", "theta_schema"): {KERNEL_KEY: dataclasses.replace(s, components=comps, zero_cancel=zc)}})
    bad = dataclasses.replace(ctx, base=tampered)
    with pytest.raises(ValueError):
        ss_evaluate(sealed, bad, th, spec.constraints, ("vdd",), junction=js)


def test_s14_engine_capacitor_value_from_theta(tmp_path):
    """S-14 [r5] (DEC-92): spec mode engine 커패시터 CL 은 θ capacitance -- θ 값으로 소신호 요청이 값을 갖고, 같은 값을 spec
    에 선언한 회로와 metric 값이 같다(비트). (θ 값이 소신호 회로에 실제로 들어가는지는 아래 영점 상쇄 회로의 ugf 폐형식이 잰다.)"""
    spec, ctx, ev, js = build(tmp_path / "e", cl_engine=True, th=theta(cl=1e-12))
    assert ("capacitance", "CL") in schema_of(ctx).components
    sealed = SealedSnapshot(ev.snapshot, ev.report)
    r1 = ss_evaluate(sealed, ctx, theta(cl=1e-12), spec.constraints, ("vdd",), junction=js)
    for _, r in r1.ss.entries:
        assert r.value is not None and r.undefined == ()
    spec2, ctx2, ev2, js2 = build(tmp_path / "v", cl_engine=False)
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx2, theta(), spec2.constraints, ("vdd",), junction=js2)
    assert [(q.metric, r.value) for q, r in r1.ss.entries] == [(q.metric, r.value) for q, r in r2.ss.entries]
    assert [(q.metric, r.value) for q, r in r1.dc.entries] == [(q.metric, r.value) for q, r in r2.dc.entries]


def _spec_with_pending(tmp, name, topo, elements, pending, cons):
    """spec_json 에 element_values.<이름> = {"pending": ID} 표지를 넣어 로더로 읽는다(SPEC_CONTRACT 결정 대기 표지)."""
    import json
    from gmid_engine.authoring import load_sizing_spec
    from gmid_engine.metrics import metric_catalog
    from .conftest import spec_json, topo_only
    tmp.mkdir(parents=True, exist_ok=True)
    td = topo_only(tmp, topo)
    d = spec_json(td, SUP, elements, (), cons)
    for el, decision in pending:
        d["human"]["element_values"][el] = {"pending": decision}
    p = tmp / (name + ".sizing_spec.json")
    p.write_text(json.dumps(d, indent=1), encoding="utf-8")
    return td, load_sizing_spec(str(p), td, metric_catalog())


def test_pending_capacitor_stays_missing(tmp_path):
    """sizing 1.2·metrics 7.6 [r5]: mode pending 커패시터는 engine_elements 에 들지 않아 θ 도 아니고 -> 소신호 요청 전부
    passive_value_undeclared(elements = (CL,)), dc 묶음은 값."""
    from gmid_engine.graph import build_s1
    td, spec = _spec_with_pending(tmp_path / "p", "sse_cs_res_p", _topo(True) | {"topology_name": "sse_cs_res_p"},
                                  (("R1", "resistor", None),), (("CL", "SP-9"),), CONS)
    inputs = dc_inputs_from_spec(spec)
    assert "CL" not in inputs.engine_elements
    run = fresh_run()
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs,
                               lut_access(load_lut_v2(tmp_path / "lut")), **run)
    assert not any(k == "CL" for _, k in schema_of(ctx).components)
    js = toy_junction(tmp_path / "junction", ctx.lut.memo.lut)
    ev = size_and_seal(ctx, theta())
    r = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, theta(), spec.constraints, ("vdd",), junction=js)
    for _, x in r.ss.entries:
        assert x.value is None and [u.code for u in x.undefined] == ["passive_value_undeclared"]
        assert dict(x.undefined[0].detail)["elements"] == ("CL",)
    assert bundle_map(r.dc)["power_dc_w"].value is not None


def test_s6_lineage_reuse_zero_compute(base):
    """7.6 재사용: ss_evaluate(res.lineage.sealed, 같은 인자) -> 세 블록 computes 0·reuses 1, snapshot is res.snapshot."""
    spec, ctx, _, _, res, js = base
    before = _counts(ctx)
    again = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    assert again.snapshot is res.snapshot
    for name, st in _since(ctx, before).items():
        assert (st.computes, st.reuses) == (0, 1), name


def test_s12_junction_change_recomputes_ss_blocks_only(base):
    """S-12: temp_c 만 바꾼 묶음 -> ss_dev 재계산 1회(→ metrics_ss 도 1회), metrics_dc 는 ss 를 읽지 않아 재사용(7.10-3),
    recomputes_same_input 0. 같은 묶음으로 다시 -> 세 블록 computes 0."""
    spec, ctx, _, _, res, js = base
    js_t = dataclasses.replace(js, temp_c=js.temp_c + 10.0)
    before = _counts(ctx)
    r2 = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js_t)
    st = _since(ctx, before)
    assert [st[b.name].computes for b in BLOCKS] == [1, 1, 0]
    assert all(st[b.name].recomputes_same_input == 0 for b in BLOCKS)
    op = r2.snapshot.value("device", "M1", "dc_op")
    cdb, csb = oracle_junction(op, temp_c=37.0)
    ss = r2.snapshot.value("device", "M1", "ss_dev")
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL) and rel_close(ss.csb, csb, JUNCTION_RTOL)
    before = _counts(ctx)
    again = ss_evaluate(r2.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js_t)
    assert again.snapshot is r2.snapshot
    st = _since(ctx, before)
    assert [st[b.name].computes for b in BLOCKS] == [0, 0, 0]


def test_fd_step_recomputes_and_no_same_input_recompute(base):
    """FD(θ current +1 %, parent = lineage): dc_op 가 바뀌어 세 블록 재계산 1회씩, recomputes_same_input 0, 값이 새 op 를 따른다."""
    spec, ctx, _, _, res, js = base
    th2 = theta(i=I0 * 1.01)
    before = _counts(ctx)
    ev2 = size_and_seal(ctx, th2, parent=res.lineage)
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx, th2, spec.constraints, ("vdd",), junction=js)
    for name, st in _since(ctx, before).items():
        assert (st.computes, st.recomputes_same_input) == (1, 0), (name, st)
    exp = _expected(r2.snapshot)
    assert rel_close(bundle_map(r2.ss)["gain_ss_db"].value, exp["gain_db"], 1e-12)
    assert not rel_close(bundle_map(r2.ss)["gain_ss_db"].value, bundle_map(res.ss)["gain_ss_db"].value, 1e-9)
    op = r2.snapshot.value("device", "M1", "dc_op")
    cdb, _ = oracle_junction(op)
    assert rel_close(r2.snapshot.value("device", "M1", "ss_dev").cdb, cdb, JUNCTION_RTOL)


def test_only_changed_blocks_recompute(base):
    """입력이 바뀐 블록만 재계산: counted_rails 만 -> metrics_dc 만, 제약 집합만 -> metrics_ss 만."""
    spec, ctx, _, _, res, js = base
    sealed = res.lineage.sealed
    before = _counts(ctx)
    ss_evaluate(sealed, ctx, theta(), spec.constraints, (), junction=js)
    st = _since(ctx, before)
    assert [st[b.name].computes for b in BLOCKS] == [0, 0, 1]
    before = _counts(ctx)
    fewer = tuple(c for c in spec.constraints if c.metric != "rout_ss_ohm")
    r = ss_evaluate(sealed, ctx, theta(), fewer, ("vdd",), junction=js)
    st = _since(ctx, before)
    assert [st[b.name].computes for b in BLOCKS] == [0, 1, 0]
    assert "rout_ss_ohm" not in bundle_map(r.ss)


def test_determinism(tmp_path, base):
    """같은 입력을 따로 만든 ctx·LUT memo·선언 파일로 다시 -> 모든 metric 값 비트 동일."""
    _, _, _, _, res, _ = base
    spec, ctx, ev, js = build(tmp_path / "again")
    r = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, theta(), spec.constraints, ("vdd",), junction=js)
    for a, b in ((res.ss, r.ss), (res.dc, r.dc)):
        assert [(q.metric, x.value) for q, x in a.entries] == [(q.metric, x.value) for q, x in b.entries]


# ---------------------------------------------------------------- sky130 실선언(원본이 있을 때만) -- 7.2 작성자 실측 예와 대조

def _sky():
    from . import test_junction_cap as tj
    if not tj._SKY_PRESENT:
        pytest.skip("sky130 원본 없음")
    return tj


def test_sky130_decls_ss_dev_junction_matches_reference(base):
    """8.5 호출 그대로 sky130 PDK 선언 + LUT 규칙 선언 -> ss_dev cdb·csb = core 9.4 표 파라미터·규칙 기하의 독립 8.2 식.
    7.2 예(이 CS 픽스처, W 2.3700841597752005e-05, vds 0.9, vsb 0)의 작성자 실측 숫자와도 같은 허용 오차로 맞는지 본다."""
    tj = _sky()
    spec, ctx, _, _, res, _ = base
    pdk, rule = read_decls(str(tj.PDK_DECL), str(tj.LUT_RULE_DECL))
    js = JunctionSource.from_decls(pdk, rule, ctx.lut.memo.lut)
    assert js.pdk_decl_sha256 == pdk.decl_sha256 and js.lut_rule_decl == rule
    r = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    op = r.snapshot.value("device", "M1", "dc_op")
    ss = r.snapshot.value("device", "M1", "ss_dev")
    # 규칙 기하: core 9.4 표 lut_diffusion_* (ad/w = 2.5e-12/5e-6, pd − w = 7e-6 − 5e-6) 를 같은 식으로 따로 계산
    ad_w, pd_x = 2.5e-12 / 5e-6, 7e-6 - 5e-6
    geo = (LUT_WM, ad_w * LUT_WM, ad_w * LUT_WM, LUT_WM + pd_x, LUT_WM + pd_x, op.W / LUT_WM)
    cdb, csb = ref_caps(tj.sky_ref_params("nmos"), geo, op.vds + op.vsb, op.vsb, 27.0)
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL) and rel_close(ss.csb, csb, JUNCTION_RTOL), (ss.cdb, cdb, ss.csb, csb)
    # 7.2 예의 전제(같은 픽스처 점) -- 같으면 작성자 실측 숫자와도 대조
    assert (op.W, op.vds, op.vsb) == (2.3700841597752005e-05, 0.9, 0.0)
    assert rel_close(ss.cdb, 1.6192271478167327e-14, JUNCTION_RTOL)
    assert rel_close(ss.csb, 2.3226455532310698e-14, JUNCTION_RTOL)
    r_t = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",),
                      junction=dataclasses.replace(js, temp_c=js.temp_c + 10.0))
    cdb_t, _ = ref_caps(tj.sky_ref_params("nmos"), geo, op.vds + op.vsb, op.vsb, 37.0)
    got_t = r_t.snapshot.value("device", "M1", "ss_dev").cdb
    assert rel_close(got_t, cdb_t, JUNCTION_RTOL) and rel_close(got_t, 1.6234719737286454e-14, JUNCTION_RTOL)


# ---------------------------------------------------------------------------
# [r5] DEC-92: θ 수동 성분·영점 상쇄 구조 규칙 값이 소신호 회로에 들어간다 (S-15·S-16 + 폐형식)
# ---------------------------------------------------------------------------
# 회로: 위 CS(M1, R1 θ resistance, CL spec 1 pF) + 보상망.
#  "cell":   Rz(out, m)–Cc(m, in), 둘 다 engine. 망 경계 {out, in}, end out, far (in,), M1 drain 쪽 셀 -> 구조 규칙
#            (sizing 4.4) Rz = 1/gm(M1), θ = capacitance Cc.
#  "nocell": Rz(out, m)–Cz(m, gnd), 둘 다 engine. far (gnd,) -> no_cs_cell -> θ ss_resistance Rz, θ capacitance Cz.
#  "cell_decl": "cell" 과 같은 topology, Rz 를 spec 값으로 선언(S-15 대조용).
# 폐형식(포트 전달 뷰: in 1 V 구동·고정, gnd·vdd 교류접지, m 은 소거): Yz = sC/(1 + sCR),
#   H(s) = −(gm − s·cgd − Yz_in)/(gds + 1/R1 + s(CL + cgd + cdb) + Yz_in + Yz_gnd)
#   ("cell" 은 Cc 가 in 쪽이라 Yz_in = Yz, Yz_gnd = 0 / "nocell" 은 Yz_in = 0, Yz_gnd = Yz). cdb = 접합(d = out, b = gnd, 7.2·8절
#   독립 식 oracle_junction), csb·cgs·cgb 는 고정 넷 사이, gmb 는 vbs = 0 이라 들지 않는다. ugf = |H| = 1 교차(3.10) -- brentq.

ZC_CONS = (
    ("gain_ss_db", ">=", 0.0, None),
    ("ugf_ss_hz", ">=", 1.0, None),
    ("power_dc_w", "<=", 1.0, None),
)


def zc_topo(case):
    pas = [("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")]
    if case in ("cell", "cell_decl"):
        pas += [("Rz", "resistor", "out", "m"), ("Cc", "capacitor", "m", "in")]
    else:
        pas += [("Rz", "resistor", "out", "m"), ("Cz", "capacitor", "m", "gnd")]
    return topo_doc("sse_zc_" + case, mos=[("M1", "nmos", "out", "in", "gnd", "gnd")], passives=pas,
                    rails=("vdd", "gnd"))


def zc_theta(ctx, c=1e-12, rz=None, **kw):
    """θ: 위 CS θ + 수동 성분. 전류 free 원소는 스키마에서 고른다(R1·M1 직렬 -- 값 같음)."""
    base_th = theta(**kw)
    i = base_th.pop(("current", "R1"))
    th = dict(base_th)
    for t, k in schema_of(ctx).components:
        if t == "current":
            th[(t, k)] = i
        elif t == "capacitance":
            th[(t, k)] = c
        elif t == "ss_resistance":
            th[(t, k)] = rz
    return th


def zc_build(tmp, case, rz_decl=None):
    """(spec, ctx, junction) -- 접합 묶음은 S0 당 1회 from_decls(toy 선언, ctx.lut.memo.lut)(8.5)."""
    from gmid_engine.graph import build_s1
    cap = "Cc" if case != "nocell" else "Cz"
    els = (("R1", "resistor", None), ("CL", "capacitor", 1e-12), (cap, "capacitor", None),
           ("Rz", "resistor", rz_decl))
    td, spec = load_case(tmp / "case", zc_topo(case), SUP, els, (), ZC_CONS)
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()                 # [XRUN-F1 card B C0·C6] 실행 하나 = 이 build 하나
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs,
                               lut_access(load_lut_v2(tmp / "lut")), **run)
    return spec, ctx, toy_junction(tmp / "junction", ctx.lut.memo.lut)


def zc_ugf(snap, case, c, rz, r1=R0, cl=1e-12):
    """폐형식 ugf(Hz). 소신호 값은 봉인 dc_op 에서 독립 oracle(npz 해석식·8.2 접합 식)로."""
    from scipy.optimize import brentq
    op = snap.value("device", "M1", "dc_op")
    ss = oracle_ss(op, "slice", "lut_cgs_cgb")
    cdb, _ = oracle_junction(op)
    gm, gds, cgd = ss["gm"], ss["gds"], ss["cgd"]

    def h(w):
        s = 1j * w
        yz = s * c / (1.0 + s * c * rz)
        y_in, y_gnd = (yz, 0.0) if case == "cell" else (0.0, yz)
        return -(gm - s * cgd - y_in) / (gds + 1.0 / r1 + s * (cl + cgd + cdb) + y_in + y_gnd)

    assert abs(h(1e-3)) > 1.0
    wu = brentq(lambda w: abs(h(w)) - 1.0, 1.0, 1e13, xtol=1e-12, rtol=1e-15, maxiter=500)
    return wu / (2.0 * math.pi), gm


# [XRUN-F1 card B 규칙 M M-d] KernelContext 를 돌려주므로 function 범위
@pytest.fixture
def zc_cell(tmp_path_factory):
    spec, ctx, js = zc_build(tmp_path_factory.mktemp("zc_cell"), "cell")
    th = zc_theta(ctx)
    ev = size_and_seal(ctx, th)
    res = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, th, spec.constraints, ("vdd",), junction=js)
    return spec, ctx, th, res, js


@pytest.fixture
def zc_nocell(tmp_path_factory):
    spec, ctx, js = zc_build(tmp_path_factory.mktemp("zc_nocell"), "nocell")
    th = zc_theta(ctx, rz=1e4)
    ev = size_and_seal(ctx, th)
    res = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, th, spec.constraints, ("vdd",), junction=js)
    return spec, ctx, th, res, js


def test_zc_schema_premise(zc_cell, zc_nocell):
    """전제(sizing 4.4 -- 독립 판정은 tests/sizing/test_theta_schema): cell 은 Rz 가 구조 규칙(θ 아님), nocell 은 θ 폴백."""
    from gmid_engine.sizing import ZC_NO_CELL
    ctx = zc_cell[1]
    (z,) = schema_of(ctx).zero_cancel
    assert (z.resistor, z.end_net, z.far_nets, z.cells, z.reason) == ("Rz", "out", ("in",), ("M1",), None)
    assert ("capacitance", "Cc") in schema_of(ctx).components
    assert not any(k == "Rz" for _, k in schema_of(ctx).components)
    ctx2 = zc_nocell[1]
    (z2,) = schema_of(ctx2).zero_cancel
    assert z2.reason == ZC_NO_CELL
    assert {("capacitance", "Cz"), ("ss_resistance", "Rz")} <= set(schema_of(ctx2).components)


def test_zc_rule_value_enters_small_signal(zc_cell):
    """7.6 [r5]: 구조 규칙 값 Rz = 1/Σ_{c∈cells} gm_c(gm = ss_dev.gm) 와 θ capacitance Cc 가 소신호 회로에 든다 -- ugf 가
    그 값으로 세운 폐형식과 같다. 다른 Rz(≈0·10·1/10 배)로 세운 폐형식과는 다르다(값이 실제로 쓰였다는 음성 대조)."""
    res = zc_cell[3]
    m = bundle_map(res.ss)
    assert m["ugf_ss_hz"].undefined == ()
    gm_ss = res.snapshot.value("device", "M1", "ss_dev").gm
    ugf, gm = zc_ugf(res.snapshot, "cell", 1e-12, 1.0 / gm_ss)
    assert rel_close(gm, gm_ss, 1e-12)
    assert rel_close(m["ugf_ss_hz"].value, ugf, 1e-7), (m["ugf_ss_hz"].value, ugf)
    for k in (1e-9, 10.0, 0.1):
        other, _ = zc_ugf(res.snapshot, "cell", 1e-12, k / gm_ss)
        assert not rel_close(m["ugf_ss_hz"].value, other, 1e-5)


def test_zc_fallback_theta_enters_small_signal(zc_nocell):
    """θ ss_resistance Rz·θ capacitance Cz 가 소신호 회로에 든다 -- ugf 폐형식(Rz–Cz 를 out–gnd 에)."""
    th, res = zc_nocell[2], zc_nocell[3]
    ugf, _ = zc_ugf(res.snapshot, "nocell", th[("capacitance", "Cz")], th[("ss_resistance", "Rz")])
    assert rel_close(bundle_map(res.ss)["ugf_ss_hz"].value, ugf, 1e-7)


def test_s15_rule_equals_spec_declared_value(zc_cell, tmp_path):
    """S-15 (DEC-92): 구조 규칙 Rz = 1/gm(M1) 회로의 metric 값 == 같은 값을 spec 에 선언한 회로(Rz value)의 metric 값(비트)."""
    res = zc_cell[3]
    op = res.snapshot.value("device", "M1", "dc_op")
    rz = 1.0 / (op.gm_id * op.current)                  # 7.2 gm = gm_id·current
    spec2, ctx2, js2 = zc_build(tmp_path, "cell_decl", rz_decl=rz)
    assert schema_of(ctx2).zero_cancel == () and not any(k == "Rz" for _, k in schema_of(ctx2).components)
    th2 = zc_theta(ctx2)
    ev2 = size_and_seal(ctx2, th2)
    assert ev2.snapshot.column("node", "dc_v") == res.snapshot.column("node", "dc_v")
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx2, th2, spec2.constraints, ("vdd",), junction=js2)
    for a, b in ((res.ss, r2.ss), (res.dc, r2.dc)):
        assert [(q.metric, x.value) for q, x in a.entries] == [(q.metric, x.value) for q, x in b.entries]


def _dc_blocks():
    from gmid_engine import sizing as S
    return (S.dc_currents, S.dc_lengths, S.dc_columns, S.dc_widths, S.dc_tolerances, S.dc_seal_node_conflict,
            S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_saturation, S.dc_seal_kvl_branch,
            S.dc_seal_report)


@pytest.mark.parametrize("which", ["cell", "nocell_c", "nocell_r"])
def test_s16_passive_theta_fd_reuses_dc_and_ss_dev(zc_cell, zc_nocell, which):
    """S-16 (DEC-92) / 7.6 [r5] / sizing 7절 r5: θ capacitance·ss_resistance 만 바꾼 FD(parent = lineage, 같은 junction 묶음)
    -> dc 블록 computes 0, ss_dev reuse(computes 0), metrics_ss·metrics_dc computes 1, recomputes_same_input 0,
    gain_ss_db 수치상 불변(S-16: 비트 동일 아님 -- ss_resistance 만 바꾼 경우 1 ulp 차 허용), ugf 는 새 θ 로 세운 폐형식과 같다."""
    spec, ctx, th, res, js = zc_cell if which == "cell" else zc_nocell
    th2 = dict(th)
    if which in ("cell", "nocell_c"):
        key = ("capacitance", "Cc" if which == "cell" else "Cz")
    else:
        key = ("ss_resistance", "Rz")
    th2[key] = th[key] * 1.1
    dc = _dc_blocks()
    before = _counts(ctx, dc + BLOCKS)
    ev2 = size_and_seal(ctx, th2, parent=res.lineage)
    st_dc = _since(ctx, before, dc)
    assert all(s.computes == 0 for s in st_dc.values()), {n: s.computes for n, s in st_dc.items()}
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx, th2, spec.constraints, ("vdd",), junction=js)
    st = _since(ctx, before, BLOCKS)
    # [IT-2a 20261021-it2a-snapshot-derive, design 41:756 (i)·승인 20261021-it2-o67-scope 'ss 블록 reuse -> graft 계수'] child 스냅샷은 keep 밖
    # writer(ss_dev)의 필드를 지우므로 입력 버전이 같은 ss_dev 는 S3 색인에서 이식(graft)한다: computes 0·grafts 1·reuses 0 (옛: reuses 1).
    assert (st[ss_dev.name].computes, st[ss_dev.name].grafts, st[ss_dev.name].reuses) == (0, 1, 0)
    assert st[metrics_ss.name].computes == 1 and st[metrics_dc.name].computes == 1
    assert all(s.recomputes_same_input == 0 for s in st.values())
    assert all(s.computes == 0 for s in _since(ctx, before, dc).values())
    m1, m2 = bundle_map(res.ss), bundle_map(r2.ss)
    assert rel_close(m2["gain_ss_db"].value, m1["gain_ss_db"].value, 1e-13)
    if which == "cell":
        exp, _ = zc_ugf(r2.snapshot, "cell", th2[key], 1.0 / r2.snapshot.value("device", "M1", "ss_dev").gm)
    elif which == "nocell_c":
        exp, _ = zc_ugf(r2.snapshot, "nocell", th2[key], th2[("ss_resistance", "Rz")])
    else:
        exp, _ = zc_ugf(r2.snapshot, "nocell", th2[("capacitance", "Cz")], th2[key])
    assert rel_close(m2["ugf_ss_hz"].value, exp, 1e-7)
    assert not rel_close(m2["ugf_ss_hz"].value, m1["ugf_ss_hz"].value, 1e-9)
    # 같은 θ' 를 lineage 에서 다시 -> 세 블록 모두 reuse
    before = _counts(ctx)
    again = ss_evaluate(r2.lineage.sealed, ctx, th2, spec.constraints, ("vdd",), junction=js)
    assert again.snapshot is r2.snapshot
    assert all(s.computes == 0 for s in _since(ctx, before).values())


# ---------------------------------------------------------------- [회귀 9065d5f, _audit_u17_1c_r2 §F-2] 봉인점 경로의 passive_values extras
# 설계 40 §2.4.1 'FD 스텝은 그 성분을 읽는 블록만 계산(WP-23 (5))': 같은 봉인 스냅샷(같은 dc_gm·passive_value lineage)에서 MOS θ 만 다른 θ 로
# ss_evaluate 를 부르면 GB5 블록 `passive_values` 는 재사용(computes 0)이어야 한다 -- 호출부가 θ 전체를 extras 로 넘기면 투영 지문이 달라져
# computes 1 이 되므로 이 계수로 관찰된다. 수동소자 θ(capacitance·ss_resistance)를 바꾸면 computes 1, 값은 새 θ 값(손).

def _mos_step(th):
    """MOS θ 성분(ln_idu·L·current)만 1 % 바꾼 θ -- 수동소자 성분은 그대로."""
    return {k: (v * 1.01 if k[0] in ("L", "ln_idu", "current") else v) for k, v in th.items()}


@pytest.mark.parametrize("which", ["cell", "nocell"])
def test_passive_values_reused_on_mos_theta_only_change(zc_cell, zc_nocell, which):
    from gmid_engine.metrics import passive_values
    spec, ctx, th, res, js = zc_cell if which == "cell" else zc_nocell
    sealed = res.lineage.sealed
    pv0 = dict(res.snapshot.column("device", "passive_value"))
    th_mos = _mos_step(th)
    assert th_mos != th and {k for k in th if th[k] != th_mos[k]} and         all(th[k] == th_mos[k] for k in th if k[0] in ("capacitance", "ss_resistance", "resistance"))   # 전제
    before = _counts(ctx, (passive_values,))
    r = ss_evaluate(sealed, ctx, th_mos, spec.constraints, ("vdd",), junction=js)
    st = _since(ctx, before, (passive_values,))[passive_values.name]
    assert (st.computes, st.reuses) == (0, 1), st
    assert dict(r.snapshot.column("device", "passive_value")) == pv0
    # 수동소자 θ 성분을 바꾸면 계산 1 -- 새 값이 필드에 든다
    key = ("capacitance", "Cc") if which == "cell" else ("ss_resistance", "Rz")
    th_p = dict(th)
    th_p[key] = th[key] * 1.1
    before = _counts(ctx, (passive_values,))
    r2 = ss_evaluate(sealed, ctx, th_p, spec.constraints, ("vdd",), junction=js)
    st = _since(ctx, before, (passive_values,))[passive_values.name]
    assert (st.computes, st.recomputes_same_input) == (1, 0), st
    assert dict(r2.snapshot.column("device", "passive_value"))[key[1]] == th[key] * 1.1


# =====================================================================================================================
# [IT-2a 20261021-it2a-snapshot-derive, T-L11c] 같은 θ ss 재평가 -> ss 블록 outcome graft, computes 증분 0 (design 41 4.7-3c).
# child 스냅샷은 keep 밖 writer(ss 블록)의 필드를 지우므로, 같은 θ 의 ss 블록은 같은 입력 버전의 S3 색인 결과를 이식(graft)한다 -- 재계산 0.
# oracle: (독립) 실행 계수(RunCounters) 행의 구간 증분 + 값 대조(첫 ss_evaluate 결과와 같은 열). 피검 함수로 기대값을 만들지 않는다.
# base(parent.snapshot 통째 출발): child 가 ss_dev 필드를 이미 가져 outcome reuse -> red.
# =====================================================================================================================

def test_it2a_same_theta_ss_reevaluation_from_child_grafts(base):
    spec, ctx, _, _, res, js = base
    before = _counts(ctx)
    ev2 = size_and_seal(ctx, theta(), parent=res.lineage)                   # 같은 θ, parent = ss 가 실린 lineage
    again = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx, theta(), spec.constraints, ("vdd",), junction=js)
    st = _since(ctx, before)
    assert (st[ss_dev.name].computes, st[ss_dev.name].grafts, st[ss_dev.name].reuses) == (0, 1, 0), st[ss_dev.name]
    assert (st[metrics_ss.name].computes, st[metrics_ss.name].grafts, st[metrics_ss.name].reuses) == (0, 1, 0), st[metrics_ss.name]
    assert all(s.computes == 0 and s.recomputes_same_input == 0 for s in st.values()), st
    # 이식한 값은 첫 평가 값과 같다
    assert again.snapshot.column("device", "ss_dev") == res.snapshot.column("device", "ss_dev")
    assert bundle_map(again.ss)["gain_ss_db"].value == bundle_map(res.ss)["gain_ss_db"].value
