"""`ss_evaluate`(봉인 스냅샷 -> ss_dev -> metrics_ss -> metrics_dc) -- metrics CONTRACT 7.6 (+ 7.7 S-6·S-10, 7.9 Q2·Q4·Q5).

회로: CS 증폭기 M1 nmos (out, in, gnd) + 저항 부하 R1 (vdd, out, 값 = θ resistance) + CL (out, gnd, 값 = spec 1 pF).
DC 점은 실제 sizing 경로(build_kernel_context -> size_and_seal, toy LUT r6)로 만든다. 봉인 7 이 아직 항상 undefined 라
`SealedSnapshot` 이 나오지 않으므로(Q2) test 가 7.8 시연과 같이 `SealedSnapshot(ev.snapshot, ev.report)` 로 명시적으로 감싼다.
기대값: 봉인 스냅샷의 dc_op·dc_v(입력)에서 conftest oracle_ss(npz 해석식)·폐형식으로 계산 -- gain = 20·log10(gm/(gds + 1/R)),
rout = 1/(gds + 1/R), power = 1.8·(1.8 − V_out)/R, area = W·L.
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.metrics import MetricBundle, SsEvaluation, metrics_dc, metrics_ss, ss_dev, ss_evaluate
from gmid_engine.sizing import (
    METRICS_KEY,
    DcEvaluation,
    SealedSnapshot,
    build_kernel_context,
    dc_inputs_from_spec,
    size_and_seal,
)

from .conftest import (
    bundle_map,
    load_case,
    load_lut_v2,
    lut_access,
    lut_ln_idu,
    oracle_ss,
    rel_close,
    topo_doc,
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


def _topo(cl_engine=False):
    return topo_doc("sse_cs_res" + ("_e" if cl_engine else ""), mos=[("M1", "nmos", "out", "in", "gnd", "gnd")],
                    passives=[("R1", "resistor", "vdd", "out"), ("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))


def theta(i=I0, r=R0, vgs=VGS0, l1=L0):
    vout = 1.8 - i * r
    return {("L", "M1"): l1, ("ln_idu", "M1"): lut_ln_idu("nmos", vgs, vout, 0.0),
            ("current", "R1"): i, ("resistance", "R1"): r}


def build(tmp, cl_engine=False, cons=CONS):
    """(spec, ctx, ev) -- spec 로더 -> dc_inputs_from_spec -> build_s1 -> build_kernel_context -> size_and_seal."""
    from gmid_engine.graph import build_s1
    els = (("R1", "resistor", None), ("CL", "capacitor", None if cl_engine else 1e-12))
    td, spec = load_case(tmp / "case", _topo(cl_engine), SUP, els, (), cons)
    inputs = dc_inputs_from_spec(spec)
    lut = load_lut_v2(tmp / "lut")
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v)), inputs, lut_access(lut))
    ev = size_and_seal(ctx, theta())
    return spec, ctx, ev


@pytest.fixture(scope="module")
def base(tmp_path_factory):
    spec, ctx, ev = build(tmp_path_factory.mktemp("sse"))
    sealed = SealedSnapshot(ev.snapshot, ev.report)
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",))
    return spec, ctx, ev, sealed, res


def _expected(snap, r=R0):
    op = snap.value("device", "M1", "dc_op")
    ss = oracle_ss(op, "slice", "lut_cgs_cgb")
    vout = snap.value("node", "out", "dc_v")
    g_out = ss["gds"] + 1.0 / r
    return dict(gain_db=20.0 * math.log10(ss["gm"] / g_out), rout=1.0 / g_out, i_vdd=(1.8 - vout) / r,
                power=1.8 * (1.8 - vout) / r, area=op.W * op.L, ss=ss)


def test_input_dc_evaluation_is_not_sealed_by_engine(base):
    """입력 전제(Q2): 지금 엔진은 봉인 7 미정이라 DcEvaluation.sealed 가 None -- test 의 명시 래핑이 필요한 이유."""
    _, _, ev, _, _ = base
    assert isinstance(ev, DcEvaluation) and ev.sealed is None


def test_result_shape_and_lineage(base):
    """SsEvaluation(snapshot, ss, dc, lineage): ss·dc = 그 필드 값, lineage = DcEvaluation(snapshot, report, SealedSnapshot)."""
    _, _, _, sealed, res = base
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
    _, _, _, _, res = base
    assert [q.metric for q, _ in res.ss.entries] == ["gain_ss_db", "rout_ss_ohm", "pm_ss_deg", "parasitic_pm_ss_deg"]
    assert [q.metric for q, _ in res.dc.entries] == ["power_dc_w", "supply_current_dc", "area_search_m2"]


def test_values_against_closed_form(base):
    """ss 값 = 봉인 op 의 독립 소신호(npz) + 폐형식, dc 값 = 봉인 dc_v·R 의 손계산."""
    _, _, _, _, res = base
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


def test_counted_rails_default_undeclared(base):
    """counted_rails 기본 () -> supply_current_dc = counted_rails_undeclared(Q4), 전력은 값."""
    spec, ctx, _, sealed, _ = base
    res = ss_evaluate(sealed, ctx, theta(), spec.constraints)
    d = bundle_map(res.dc)
    assert d["supply_current_dc"].value is None
    assert [u.code for u in d["supply_current_dc"].undefined] == ["counted_rails_undeclared"]
    assert d["power_dc_w"].value is not None


@pytest.mark.parametrize("bad", ["dc_evaluation", "snapshot", "none"])
def test_s10_only_sealed_snapshot_accepted(base, bad):
    """S-10 / DEC-67: SealedSnapshot 아닌 값(DcEvaluation·GraphSnapshot·None(= 엔진이 낸 ev.sealed)) -> TypeError."""
    spec, ctx, ev, _, _ = base
    arg = {"dc_evaluation": ev, "snapshot": ev.snapshot, "none": ev.sealed}[bad]
    for blk in BLOCKS:
        blk.reset_stats()
    with pytest.raises(TypeError):
        ss_evaluate(arg, ctx, theta(), spec.constraints, ("vdd",))
    assert all(b.stats().calls == 0 for b in BLOCKS)          # 거부는 블록 호출 전


def test_ctx_must_be_kernel_context(base):
    spec, ctx, _, sealed, _ = base
    with pytest.raises(TypeError):
        ss_evaluate(sealed, ctx.base, theta(), spec.constraints)


def test_theta_checked(base):
    """θ = check_theta(ctx.schema, ...) -- 키 빠짐은 ValueError(sizing 5.1)."""
    spec, ctx, _, sealed, _ = base
    th = theta()
    del th[("resistance", "R1")]
    with pytest.raises(ValueError):
        ss_evaluate(sealed, ctx, th, spec.constraints)


@pytest.mark.parametrize("pt", [(("CL", 2e-12),), (("M1", 1.0),), (("nope", 1.0),), (("R1", 5e4),)],
                         ids=["spec_valued", "not_passive", "unknown", "theta_resistance_too"])
def test_s10_passive_theta_conflicts_rejected(base, pt):
    """S-10: passive_theta 가 spec 값 있는 소자·S1 수동소자 아닌 이름·θ resistance 와 겹침 -> ValueError."""
    spec, ctx, _, sealed, _ = base
    with pytest.raises(ValueError):
        ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), pt)


def test_passive_theta_supplies_engine_value(tmp_path):
    """Q5: spec 값이 engine 인 수동소자(CL) -- passive_theta 가 없으면 소신호 요청 passive_value_undeclared,
    주면 그 값으로 평가(같은 CL 1 pF 를 spec 에 둔 경우와 값이 같다)."""
    spec, ctx, ev = build(tmp_path / "e", cl_engine=True)
    sealed = SealedSnapshot(ev.snapshot, ev.report)
    r0 = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",))
    for _, r in r0.ss.entries:
        assert r.value is None and [u.code for u in r.undefined] == ["passive_value_undeclared"]
        assert dict(r.undefined[0].detail)["elements"] == ("CL",)
    assert bundle_map(r0.dc)["power_dc_w"].value is not None
    r1 = ss_evaluate(sealed, ctx, theta(), spec.constraints, ("vdd",), (("CL", 1e-12),))
    spec2, ctx2, ev2 = build(tmp_path / "v", cl_engine=False)
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx2, theta(), spec2.constraints, ("vdd",))
    assert [(q.metric, r.value) for q, r in r1.ss.entries] == [(q.metric, r.value) for q, r in r2.ss.entries]


def test_s6_lineage_reuse_zero_compute(base):
    """7.6 재사용: ss_evaluate(res.lineage.sealed, 같은 인자) -> 세 블록 computes 0·reuses 1, snapshot is res.snapshot."""
    spec, ctx, _, _, res = base
    for b in BLOCKS:
        b.reset_stats()
    again = ss_evaluate(res.lineage.sealed, ctx, theta(), spec.constraints, ("vdd",))
    assert again.snapshot is res.snapshot
    for b in BLOCKS:
        st = b.stats()
        assert (st.computes, st.reuses) == (0, 1), b.name


def test_fd_step_recomputes_and_no_same_input_recompute(base):
    """FD(θ current +1 %, parent = lineage): dc_op 가 바뀌어 세 블록 재계산 1회씩, recomputes_same_input 0, 값이 새 op 를 따른다."""
    spec, ctx, _, _, res = base
    th2 = theta(i=I0 * 1.01)
    for b in BLOCKS:
        b.reset_stats()
    ev2 = size_and_seal(ctx, th2, parent=res.lineage)
    r2 = ss_evaluate(SealedSnapshot(ev2.snapshot, ev2.report), ctx, th2, spec.constraints, ("vdd",))
    for b in BLOCKS:
        st = b.stats()
        assert (st.computes, st.recomputes_same_input) == (1, 0), (b.name, st)
    exp = _expected(r2.snapshot)
    assert rel_close(bundle_map(r2.ss)["gain_ss_db"].value, exp["gain_db"], 1e-12)
    assert not rel_close(bundle_map(r2.ss)["gain_ss_db"].value, bundle_map(res.ss)["gain_ss_db"].value, 1e-9)


def test_only_changed_blocks_recompute(base):
    """입력이 바뀐 블록만 재계산: counted_rails 만 -> metrics_dc 만, 제약 집합만 -> metrics_ss 만."""
    spec, ctx, _, _, res = base
    sealed = res.lineage.sealed
    for b in BLOCKS:
        b.reset_stats()
    ss_evaluate(sealed, ctx, theta(), spec.constraints, ())
    assert [b.stats().computes for b in BLOCKS] == [0, 0, 1]
    for b in BLOCKS:
        b.reset_stats()
    fewer = tuple(c for c in spec.constraints if c.metric != "rout_ss_ohm")
    r = ss_evaluate(sealed, ctx, theta(), fewer, ("vdd",))
    assert [b.stats().computes for b in BLOCKS] == [0, 1, 0]
    assert "rout_ss_ohm" not in bundle_map(r.ss)


def test_determinism(tmp_path, base):
    """같은 입력을 따로 만든 ctx·LUT memo 로 다시 -> 모든 metric 값 비트 동일."""
    _, _, _, _, res = base
    spec, ctx, ev = build(tmp_path / "again")
    r = ss_evaluate(SealedSnapshot(ev.snapshot, ev.report), ctx, theta(), spec.constraints, ("vdd",))
    for a, b in ((res.ss, r.ss), (res.dc, r.dc)):
        assert [(q.metric, x.value) for q, x in a.entries] == [(q.metric, x.value) for q, x in b.entries]
