"""`ss_evaluate`(봉인 스냅샷 -> ss_dev -> metrics_ss -> metrics_dc) -- metrics CONTRACT 7.6 (+ 7.7 S-6·S-10·S-11·S-12·S-13,
7.9 Q2·Q4·Q5).

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

from .conftest import (
    JUNCTION_RTOL,
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


def _topo(cl_engine=False):
    return topo_doc("sse_cs_res" + ("_e" if cl_engine else ""), mos=[("M1", "nmos", "out", "in", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))


def theta(i=I0, r=R0, vgs=VGS0, l1=L0):
    vout = 1.8 - i * r
    return {("L", "M1"): l1, ("ln_idu", "M1"): lut_ln_idu("nmos", vgs, vout, 0.0),
            ("current", "R1"): i, ("resistance", "R1"): r}


def build(tmp, cl_engine=False, cons=CONS):
    """(spec, ctx, ev, junction) -- spec 로더 -> dc_inputs_from_spec -> build_s1 -> build_kernel_context -> size_and_seal,
    접합 묶음은 S0 당 1회 from_decls(toy 선언, ctx.lut.memo.lut)."""
    from gmid_engine.graph import build_s1
    els = (("R1", "resistor", None), ("CL", "capacitor", None if cl_engine else 1e-12))
    td, spec = load_case(tmp / "case", _topo(cl_engine), SUP, els, (), cons)
    inputs = dc_inputs_from_spec(spec)
    lut = load_lut_v2(tmp / "lut")
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v)), inputs, lut_access(lut))
    ev = size_and_seal(ctx, theta())
    return spec, ctx, ev, toy_junction(tmp / "junction", ctx.lut.memo.lut)


@pytest.fixture(scope="module")
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
    for blk in BLOCKS:
        blk.reset_stats()
    with pytest.raises(TypeError):
        ss_evaluate(arg, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    assert all(b.stats().calls == 0 for b in BLOCKS)          # 거부는 블록 호출 전


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
    """θ = check_theta(ctx.schema, ...) -- 키 빠짐은 ValueError(sizing 5.1)."""
    spec, ctx, _, sealed, _, js = base
    th = theta()
    del th[("resistance", "R1")]
    with pytest.raises(ValueError):
        ss_evaluate(sealed, ctx, th, spec.constraints, junction=js)


@pytest.mark.parametrize("pt", [(("CL", 2e-12),), (("M1", 1.0),), (("nope", 1.0),), (("R1", 5e4),)],
                         ids=["spec_valued", "not_passive", "unknown", "theta_resistance_too"])
def test_s10_passive_theta_conflicts_rejected(base, pt):
    """S-10: passive_theta 가 spec 값 있는 소자·S1 수동소자 아닌 이름·θ resistance 와 겹침 -> ValueError."""
    spec, ctx, _, sealed, _, js = base
    with pytest.raises(ValueError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), pt, junction=js)


def test_passive_theta_supplies_engine_value(tmp_path):
    """Q5: spec 값이 engine 인 수동소자(CL) -- passive_theta 가 없으면 소신호 요청 passive_value_undeclared,
    주면 그 값으로 평가(같은 CL 1 pF 를 spec 에 둔 경우와 값이 같다)."""
    spec, ctx, ev, js = build(tmp_path / "e", cl_engine=True)
    sealed = SealedSnapshot(ev.snapshot, ev.report)
    r0 = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    for _, r in r0.ss.entries:
        assert r.value is None and [u.code for u in r.undefined] == ["passive_value_undeclared"]
        assert dict(r.undefined[0].detail)["elements"] == ("CL",)
    assert bundle_map(r0.dc)["power_dc_w"].value is not None
    r1 = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), (("CL", 1e-12),), junction=js)
    spec2, ctx2, ev2, js2 = build(tmp_path / "v", cl_engine=False)
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx2, theta(), spec2.constraints, ("vdd",), junction=js2)
    assert [(q.metric, r.value) for q, r in r1.ss.entries] == [(q.metric, r.value) for q, r in r2.ss.entries]


def test_s6_lineage_reuse_zero_compute(base):
    """7.6 재사용: ss_evaluate(res.lineage.sealed, 같은 인자) -> 세 블록 computes 0·reuses 1, snapshot is res.snapshot."""
    spec, ctx, _, _, res, js = base
    for b in BLOCKS:
        b.reset_stats()
    again = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js)
    assert again.snapshot is res.snapshot
    for b in BLOCKS:
        st = b.stats()
        assert (st.computes, st.reuses) == (0, 1), b.name


def test_s12_junction_change_recomputes_ss_blocks_only(base):
    """S-12: temp_c 만 바꾼 묶음 -> ss_dev 재계산 1회(→ metrics_ss 도 1회), metrics_dc 는 ss 를 읽지 않아 재사용(7.10-3),
    recomputes_same_input 0. 같은 묶음으로 다시 -> 세 블록 computes 0."""
    spec, ctx, _, _, res, js = base
    js_t = dataclasses.replace(js, temp_c=js.temp_c + 10.0)
    for b in BLOCKS:
        b.reset_stats()
    r2 = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js_t)
    assert [b.stats().computes for b in BLOCKS] == [1, 1, 0]
    assert all(b.stats().recomputes_same_input == 0 for b in BLOCKS)
    op = r2.snapshot.value("device", "M1", "dc_op")
    cdb, csb = oracle_junction(op, temp_c=37.0)
    ss = r2.snapshot.value("device", "M1", "ss_dev")
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL) and rel_close(ss.csb, csb, JUNCTION_RTOL)
    for b in BLOCKS:
        b.reset_stats()
    again = ss_evaluate(r2.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",), junction=js_t)
    assert again.snapshot is r2.snapshot
    assert [b.stats().computes for b in BLOCKS] == [0, 0, 0]


def test_fd_step_recomputes_and_no_same_input_recompute(base):
    """FD(θ current +1 %, parent = lineage): dc_op 가 바뀌어 세 블록 재계산 1회씩, recomputes_same_input 0, 값이 새 op 를 따른다."""
    spec, ctx, _, _, res, js = base
    th2 = theta(i=I0 * 1.01)
    for b in BLOCKS:
        b.reset_stats()
    ev2 = size_and_seal(ctx, th2, parent=res.lineage)
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx, th2, spec.constraints, ("vdd",), junction=js)
    for b in BLOCKS:
        st = b.stats()
        assert (st.computes, st.recomputes_same_input) == (1, 0), (b.name, st)
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
    for b in BLOCKS:
        b.reset_stats()
    ss_evaluate(sealed, ctx, theta(), spec.constraints, (), junction=js)
    assert [b.stats().computes for b in BLOCKS] == [0, 0, 1]
    for b in BLOCKS:
        b.reset_stats()
    fewer = tuple(c for c in spec.constraints if c.metric != "rout_ss_ohm")
    r = ss_evaluate(sealed, ctx, theta(), fewer, ("vdd",), junction=js)
    assert [b.stats().computes for b in BLOCKS] == [0, 1, 0]
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
