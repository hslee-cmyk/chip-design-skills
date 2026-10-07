"""`metrics_ss` 계산 블록(spec 뷰 -> 계 -> 제약 metric 묶음) -- metrics CONTRACT 7.4 (+ 7.7 S-1~S-6·S-8, 예 7·7c).

입력: 예 7 회로를 topology·spec 으로 만들어 authoring 로더가 유도한 뷰(`ViewDecl`)를 쓰고, S2 스냅샷의 `device.ss_dev` 열은
권한표 writer 로 손으로 쓴다(gm 1e-3, gds 1e-5, 용량 0). 수동소자 값은 `passive_values` 인자.
기대값: conftest 폐형식(`closed_ex7` -- 예 7 되돌림 비, `ex7_port_closed` -- 포트 전달 H(s) 와 brentq 교차).
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.metrics import MetricBundle, MetricRequest, MetricResult, Undefined, metrics_ss
from gmid_engine.sizing import METRICS_KEY, METRICS_SS_WRITER, S2_WRITERS

from .conftest import (
    EX7,
    HAND,
    bundle_map,
    closed_ex7,
    ex7_case,
    ex7_passives,
    ex7_port_closed,
    hand_ss,
    rel_close,
    requests_of,
    with_ss,
)

PORT = {"ac_excite": {"in": 1.0}, "sense_p": "out", "sense_n": None, "sense_mode": "single_ended"}
HALF = {"ac_excite": {"in": 0.5}, "sense_p": "out", "sense_n": None, "sense_mode": "single_ended"}

ALL_SS = (
    ("pm_ss_deg", ">=", 60.0, None),                 # loop: feedback 에 따라 β 루프(declared) / β = 1(unity) 유도
    ("gain_ss_db", ">=", 30.0, None),                # port 유도 뷰
    ("parasitic_pm_ss_deg", ">=", 45.0, None),
    ("ugf_ss_hz", ">=", 1.0, None),
    ("gbw_ss_hz", ">=", 1.0, None),
    ("rout_ss_ohm", "<=", 1e6, None),                # sense 유도 뷰(출력 포트 1개)
    ("ratio_ss_db", ">=", 1.0, {"num": PORT, "den": HALF}),
)


# Undefined.quantity 기대값 = 레지스트리 결과 형식의 필드 이름(3.15 표 -- 7.4 '필드 = 레지스트리 field')
QUANTITY ={"pm_ss_deg": "phase_margin_deg", "parasitic_pm_ss_deg": "phase_margin_deg", "gain_ss_db": "gain_db",
            "ugf_ss_hz": "ugf_hz", "gbw_ss_hz": "gbw_hz", "rout_ss_ohm": "rout_ohm", "ratio_ss_db": "ratio_db"}


@pytest.fixture(scope="module")
def declared(tmp_path_factory):
    """예 7, feedback = [Cf] -> pm_ss_deg 는 β 루프(절단 Cf 의 in 쪽 단자)."""
    return ex7_case(tmp_path_factory.mktemp("ex7d"), ALL_SS)


@pytest.fixture(scope="module")
def unity(tmp_path_factory):
    """예 7 소자, feedback = [] -> pm_ss_deg 는 β = 1 포트 뷰."""
    return ex7_case(tmp_path_factory.mktemp("ex7u"), ALL_SS, feedback=())


def _run(case, metrics=None, passives=None):
    td, spec, snap = case
    reqs = requests_of(spec, metrics)
    out = metrics_ss(snap, reqs, ex7_passives() if passives is None else passives)
    return out, reqs, out.value("graph", METRICS_KEY, "metrics_ss")


def test_block_declaration():
    """7.4 reads, writes graph.metrics_ss(key METRICS_KEY = "metrics"), writer = 권한표 writer_of."""
    assert metrics_ss.name == METRICS_SS_WRITER == S2_WRITERS.writer_of("graph", "metrics_ss") == "metrics_ss"
    assert METRICS_KEY == "metrics"
    assert set(metrics_ss.reads) == {("device", "ss_dev"), ("device", "element_class"), ("device", "kind"),
                                     ("device", "pins"), ("device", "bulk"), ("node", "ac_ground_class"),
                                     ("node", "port_direction")}
    assert tuple(metrics_ss.writes) == (("graph", "metrics_ss"),)


def test_views_derived_as_expected(declared, unity):
    """입력 확인(피검 아님): 로더가 유도한 뷰 모양이 test 가 가정한 것과 같다."""
    v = {c.metric: c.view for c in declared[1].constraints}
    assert v["pm_ss_deg"].mode == "loop" and v["pm_ss_deg"].beta == "declared" and v["pm_ss_deg"].cuts == (("Cf", "in"),)
    assert v["gain_ss_db"].mode == "port" and v["rout_ss_ohm"].mode == "sense" and v["ratio_ss_db"].mode == "ratio"
    u = {c.metric: c.view for c in unity[1].constraints}
    assert u["pm_ss_deg"].mode == "loop" and u["pm_ss_deg"].beta == "unity"


def test_s1_beta_loop_pm_example7(declared):
    """S-1: β 루프 `pm_ss_deg` = 예 7 폐형식 180° − atan√624 (작성자 실측 92.29244277595588)."""
    _, reqs, b = _run(declared)
    assert isinstance(b, MetricBundle)
    r = bundle_map(b)["pm_ss_deg"]
    exp = closed_ex7()
    assert r.undefined == () or not r.undefined
    assert rel_close(r.value, exp["pm_deg"], 1e-12), (r.value, exp["pm_deg"])
    assert rel_close(r.value, 92.29244277595588, 1e-12)


def test_s2_port_gain_and_rout(declared):
    """S-2: 포트 뷰 gain = 20·log10(gm/gds) = 40 dB, sense 뷰 rout = 1/gds = 1e5 Ω."""
    _, _, b = _run(declared)
    m = bundle_map(b)
    assert rel_close(m["gain_ss_db"].value, 20.0 * math.log10(EX7["gm"] / EX7["gds"]), 1e-12)
    assert rel_close(m["gain_ss_db"].value, 40.0, 1e-12)
    assert rel_close(m["rout_ss_ohm"].value, 1.0 / EX7["gds"], 1e-12)


def test_port_view_ugf_gbw_parasitic_pm(declared):
    """포트 전달 뷰 H(s) = −(gm − sCf)/(gds + s(CL + Cf)) 의 UGF·GBW·위상 여유(폐형식 brentq)."""
    _, _, b = _run(declared)
    m = bundle_map(b)
    exp = ex7_port_closed()
    assert rel_close(m["ugf_ss_hz"].value, exp["ugf_hz"], 1e-9)
    assert rel_close(m["gbw_ss_hz"].value, exp["gbw_hz"], 1e-9)
    assert rel_close(m["parasitic_pm_ss_deg"].value, exp["pm_deg"], 1e-9)


def test_loop_cut_probe_differs_from_port_factor(declared):
    """β 루프(절단·프로브 Middlebrook)는 포트 Factor(β = 1)와 다른 계 -- 같은 소자에서 PM 값이 다르다(뷰가 실제로 갈린다)."""
    _, _, b = _run(declared)
    m = bundle_map(b)
    assert not rel_close(m["pm_ss_deg"].value, m["parasitic_pm_ss_deg"].value, 1e-6)


def test_s3_unity_pm_bit_identical_to_parasitic(unity):
    """S-3: feedback 빈 list(β = 1) -> 한 요청 집합 안에서 pm_ss_deg == 같은 포트 뷰 parasitic_pm_ss_deg (비트)."""
    _, _, b = _run(unity)
    m = bundle_map(b)
    assert m["pm_ss_deg"].value == m["parasitic_pm_ss_deg"].value
    assert rel_close(m["pm_ss_deg"].value, ex7_port_closed()["pm_deg"], 1e-9)


def test_values_are_float_and_entries_in_request_order(declared):
    _, reqs, b = _run(declared)
    assert tuple(q for q, _ in b.entries) == reqs
    for q, r in b.entries:
        assert isinstance(r, MetricResult) and r.name == q.metric
        assert type(r.value) is float


def test_ratio_view(declared):
    """ratio 뷰: 같은 계의 num(in 1 V)·den(in 0.5 V) 두 열 -> 20·log10 2."""
    _, _, b = _run(declared, ("ratio_ss_db",))
    assert rel_close(bundle_map(b)["ratio_ss_db"].value, 20.0 * math.log10(2.0), 1e-12)


def test_ratio_sense_mismatch_raises(tmp_path):
    """뷰 정의 결함(ratio num·den 관측 불일치) -> ValueError."""
    other = dict(HALF, sense_p="in")
    case = ex7_case(tmp_path, (("ratio_ss_db", ">=", 1.0, {"num": PORT, "den": other}),))
    with pytest.raises(ValueError):
        _run(case)


def test_unregistered_metric_keyerror(declared):
    _, spec, snap = declared
    view = next(c.view for c in spec.constraints if c.metric == "gain_ss_db")
    with pytest.raises(KeyError):
        metrics_ss(snap, (MetricRequest("bogus_ss_db", view),), ex7_passives())


def test_s4_missing_passive_value_all_undefined(declared):
    """S-4: 수동소자 값 하나(Cs)를 빼면 모든 소신호 요청이 passive_value_undeclared(elements = 빠진 이름), 예외 0."""
    _, reqs, b = _run(declared, passives=ex7_passives(drop=("Cs",)))
    assert len(b.entries) == len(reqs)
    for q, r in b.entries:
        assert r.value is None
        assert r.undefined == (Undefined(QUANTITY[q.metric], "passive_value_undeclared", "definitional",
                                         (("elements", ("Cs",)),)),)
    assert b.detail == (("missing_passives", ("Cs",)),)


def test_s4_negative_all_values_present_are_defined(declared):
    """S-4 대조: 값이 다 있으면 같은 요청에 passive_value_undeclared 가 하나도 없다."""
    _, _, b = _run(declared)
    for _, r in b.entries:
        assert all(u.code != "passive_value_undeclared" for u in r.undefined)
        assert r.value is not None


def test_s5_pending_view(tmp_path, declared):
    """S-5: pending 뷰 요청 -> view_pending(decision = 뷰 decision), 다른 요청 값은 그대로."""
    cons = (("gain_ss_db", ">=", 30.0, {"pending": "CI-10"}), ("rout_ss_ohm", "<=", 1e6, None))
    case = ex7_case(tmp_path, cons)
    _, _, b = _run(case)
    m = bundle_map(b)
    assert m["gain_ss_db"].value is None
    assert m["gain_ss_db"].undefined == (Undefined("gain_db", "view_pending", "definitional", (("decision", "CI-10"),)),)
    ref = bundle_map(_run(declared, ("rout_ss_ohm",))[2])["rout_ss_ohm"].value
    assert m["rout_ss_ohm"].value == ref


def test_s5_pending_precedes_missing(tmp_path):
    """7.4 처리 순서: (1) pending 이 (2) missing 보다 먼저 -- 값이 빠져도 pending 요청은 view_pending."""
    cons = (("gain_ss_db", ">=", 30.0, {"pending": "CI-10"}), ("rout_ss_ohm", "<=", 1e6, None))
    _, _, b = _run(ex7_case(tmp_path, cons), passives=ex7_passives(drop=("CL",)))
    m = bundle_map(b)
    assert [u.code for u in m["gain_ss_db"].undefined] == ["view_pending"]
    assert [u.code for u in m["rout_ss_ohm"].undefined] == ["passive_value_undeclared"]


def test_systems_shared_by_fixed_net_set(declared):
    """같은 고정 넷 집합 F 의 뷰는 한 계: port·sense·ratio(전부 F = gnd ∪ in) -> 계 1, β 루프를 더하면 계 2."""
    _, _, b1 = _run(declared, ("gain_ss_db", "rout_ss_ohm", "ratio_ss_db"))
    d1 = dict(b1.detail)
    assert [k for k, _ in b1.detail] == ["grid_points", "systems"]
    assert d1["systems"] == 1 and d1["grid_points"] >= 1
    _, _, b2 = _run(declared, ("gain_ss_db", "rout_ss_ohm", "ratio_ss_db", "pm_ss_deg"))
    assert dict(b2.detail)["systems"] == 2


def test_approximations_and_empty_requests(declared):
    """approximations = 모든 ss_dev 의 (cap, gmb, junction) 모형 집합 정렬. 요청 0 이면 entries·detail 빈 tuple."""
    _, _, b = _run(declared)
    assert b.approximations == (("cap", HAND), ("gmb", HAND), ("junction", HAND))
    _, spec, snap = declared
    out = metrics_ss(snap, (), ex7_passives())
    e = out.value("graph", METRICS_KEY, "metrics_ss")
    assert e.entries == () and e.detail == ()


def test_s6_reuse_and_recompute(declared):
    """S-6: 같은 입력 두 번 -> 두 번째 computes 0·`is`. 요청·수동 값이 바뀌면 재계산."""
    _, spec, snap = declared
    reqs = requests_of(spec)
    metrics_ss.reset_stats()
    s1 = metrics_ss(snap, reqs, ex7_passives())
    s2 = metrics_ss(s1, reqs, ex7_passives())
    assert s2 is s1
    assert (metrics_ss.stats().computes, metrics_ss.stats().reuses) == (1, 1)
    s3 = metrics_ss(s1, reqs[:2], ex7_passives())
    assert s3 is not s1
    pv = tuple((k, v * 2.0 if k == "CL" else v) for k, v in ex7_passives())
    s4 = metrics_ss(s3, reqs, pv)
    assert s4 is not s3
    st = metrics_ss.stats()
    assert st.computes == 3 and st.recomputes_same_input == 0
    # ss_dev 값이 바뀌면(손 S2 의 다른 gds) 재계산되고 rout 이 따라 바뀐다
    s5 = with_ss(s4, {"M1": hand_ss(EX7["gm"], 2 * EX7["gds"])}, version="hand_ss2")
    out = metrics_ss(s5, reqs, ex7_passives())
    assert rel_close(bundle_map(out.value("graph", METRICS_KEY, "metrics_ss"))["rout_ss_ohm"].value,
                     0.5 / EX7["gds"], 1e-12)


@pytest.mark.parametrize("names", [{"out": "zout", "in": "ain", "gnd": "mgnd"},
                                   {"out": "a1", "in": "b2", "gnd": "c3"}])
def test_s8_net_rename_invariance(tmp_path, declared, names):
    """S-8: 넷 이름 전단사(이름순 노드 인덱스가 바뀜) 뒤 metric 값 같음."""
    ref = bundle_map(_run(declared)[2])

    def ren(view):
        if view is None:
            return None
        out = {}
        for k, v in view.items():
            if isinstance(v, dict):
                v = ren(v) if k != "ac_excite" else {names[n]: a for n, a in v.items()}
            elif k in ("sense_p", "sense_n") and v is not None:
                v = names[v]
            out[k] = v
        return out

    cons = tuple((m, op, val, ren(view)) for m, op, val, view in ALL_SS)
    case = ex7_case(tmp_path, cons, names=names)
    got = bundle_map(_run(case)[2])
    assert set(got) == set(ref)
    for k in ref:
        assert rel_close(got[k].value, ref[k].value, 1e-12), (k, got[k].value, ref[k].value)


def test_example7c_mixed_cut_undefined_not_exception(tmp_path):
    """예 7c: Cs 대신 저항 -> 절단 노드 n(전도)·x(용량 전용) 섞임 -> pm_ss_deg 정의 불가 loop_cut_mixed_charge, 예외 0."""
    case = ex7_case(tmp_path, (("pm_ss_deg", ">=", 60.0, None), ("gain_ss_db", ">=", 30.0, None)), cs_resistor=True)
    _, _, b = _run(case, passives=ex7_passives(cs_resistor=True))
    m = bundle_map(b)
    assert m["pm_ss_deg"].value is None
    assert "loop_cut_mixed_charge" in {u.code for u in m["pm_ss_deg"].undefined}
    assert m["gain_ss_db"].value is not None


def test_determinism(declared):
    """같은 입력 두 번(새 블록 이력) -> 값 비트 동일."""
    _, spec, snap = declared
    reqs = requests_of(spec)
    a = metrics_ss(snap, reqs, ex7_passives()).value("graph", METRICS_KEY, "metrics_ss")
    metrics_ss.reset_stats()
    b = metrics_ss(with_ss(snap, {"M1": hand_ss(EX7["gm"], EX7["gds"])}, version="again"), reqs,
                   ex7_passives()).value("graph", METRICS_KEY, "metrics_ss")
    assert [(q, r.value) for q, r in a.entries] == [(q, r.value) for q, r in b.entries]
    assert a.detail == b.detail


# =====================================================================================================================
# 9절 분해능 배선(7.4 [9절]·9.4, 7.7 S-15·S-16). 손 S2 의 SsDevice 에 lut_rel_tol = gm/ID · tol_V 를 쓴다(gm/ID 10 S/A, tol_V 2 mV --
# 9.5 의 예). 기대값: 9.5 폐형식(test_resolution 의 closed_ex7_resolution 과 같은 식) / 같은 회로를 test 쪽에서 다시 세워 공개
# lut_parameters·metric_resolutions 를 부른 값(S-15 계약 문장).
# =====================================================================================================================

import dataclasses as _dc

from gmid_engine.metrics import (
    Capacitor,
    Excitation,
    LoopCut,
    MosSmallSignal,
    Sense,
    SmallSignalCircuit,
    build_mna,
    cut_circuit,
    lut_parameters,
    metric_resolutions,
    output_resistance,
    response_sensitivity,
    solve_responses,
)

from .conftest import DB_PER_NEPER, count_calls
from .test_resolution import closed_ex7_resolution

GM_ID, TOL_V = 10.0, 0.002
EPS7 = GM_ID * TOL_V                          # ss_dev 가 쓰는 곱 그대로(7.2)


def _ss_eps(eps, gds=None):
    return {"M1": _dc.replace(hand_ss(EX7["gm"], EX7["gds"] if gds is None else gds), lut_rel_tol=eps)}


@pytest.fixture(scope="module")
def declared_eps(tmp_path_factory):
    """예 7, feedback = [Cf], M1 lut_rel_tol = 10 · 0.002."""
    return ex7_case(tmp_path_factory.mktemp("ex7e"), ALL_SS, ss=_ss_eps(EPS7))


def test_s16_beta_loop_pm_resolution_closed_form(declared_eps):
    """S-16: β 루프 pm_ss_deg 분해능 = 9.5 폐형식 0.0917466739° (상대 ≤ 1e-9). 포트 gain = 2·D·ε(gain = 20log(gm/gds)),
    sense rout = ε·rout(rout = 1/gds) -- 같은 9.3 식의 폐형식."""
    _, _, b = _run(declared_eps)
    m = bundle_map(b)
    exp = closed_ex7_resolution(EPS7)
    assert abs(m["pm_ss_deg"].resolution - exp["phase_margin_deg"]) <= 1e-9 * exp["phase_margin_deg"]
    assert abs(m["pm_ss_deg"].resolution - 0.0917466739) <= 0.5e-10 + 1e-9 * 0.0917466739    # 계약 표기 자릿수 반 단위 + R-1
    g = 2.0 * DB_PER_NEPER * EPS7
    assert abs(m["gain_ss_db"].resolution - g) <= 1e-9 * g
    ro = EPS7 / EX7["gds"]
    assert abs(m["rout_ss_ohm"].resolution - ro) <= 1e-9 * ro
    for q, r in b.entries:                                # 값 있는 결과는 모두 분해능 값(ε 정의됨)
        assert r.value is not None and isinstance(r.resolution, float) and r.resolution >= 0.0, q


def _sense_system():
    """S-15 test 쪽 재구성(7.4): 노드 = 넷 이름순(gnd 0, in 1, out 2), sense 뷰 계 F = ground ∪ input = {0, 1}, out 에 +1 A."""
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 1, 0, 0, EX7["gm"], 0.0, EX7["gds"]),),
                            capacitors=(Capacitor(2, 0, EX7["cl"]), Capacitor(2, 1, EX7["cf"]), Capacitor(1, 0, EX7["cs"])),
                            ac_ground=(0, 1))
    return ck, build_mna(ck, (Excitation("i_out", currents=((2, 1.0),)),), (Sense(2),))


def test_s15_rout_resolution_bit_identical_to_direct_call(declared_eps):
    """S-15: metrics_ss 의 rout 분해능 = test 쪽이 같은 회로·같은 ε 로 lut_parameters·metric_resolutions 를 부른 value(비트).
    (rout 은 ω = 0 극한 하나라 공유 격자와 무관 -- 재구성이 계약 문장 그대로 같다.)"""
    _, _, b = _run(declared_eps, ("rout_ss_ohm",))
    got = bundle_map(b)["rout_ss_ohm"]
    ck, sysm = _sense_system()
    (resp,) = solve_responses((sysm,))
    ro = output_resistance(resp, 0, 0)
    assert ro.rout_ohm == got.value                       # 재구성이 같은 계라는 입력 확인
    (r,) = metric_resolutions(ro, resp, lut_parameters(ck, (EPS7,)))
    assert got.resolution == r.value


def test_s15_beta_loop_resolution_matches_direct_call(declared_eps):
    """S-15(루프): pm_ss_deg 만 요청 -> 계 1개(절단 계). test 쪽 재구성(ac_ground = ground ∪ (input − 절단 넷) = {gnd}, Cf 의 in 단자
    절단, 가중 1)으로 부른 metric_resolutions 와 같다(비트)."""
    _, _, b = _run(declared_eps, ("pm_ss_deg",))
    got = bundle_map(b)["pm_ss_deg"]
    assert dict(b.detail)["systems"] == 1
    from gmid_engine.metrics import analyze_loop, probe_factor
    ck = SmallSignalCircuit(mos=(MosSmallSignal(2, 1, 0, 0, EX7["gm"], 0.0, EX7["gds"]),),
                            capacitors=(Capacitor(2, 0, EX7["cl"]), Capacitor(2, 1, EX7["cf"]), Capacitor(1, 0, EX7["cs"])),
                            ac_ground=(0,))
    cut = cut_circuit(ck, (LoopCut("capacitor", 1, "b"),))
    (resp,) = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),))
    pf = probe_factor(resp, cut.pairs, (1.0,))
    la = analyze_loop((pf,))
    assert la.phase_margin_deg == got.value               # 재구성이 같은 계라는 입력 확인
    res = {r.quantity: r for r in metric_resolutions(la, (pf,), lut_parameters(ck, (EPS7,)))}
    assert got.resolution == res["phase_margin_deg"].value


def test_s15_one_mos_undetermined_all_none_values_unchanged(tmp_path, declared_eps):
    """S-15: lut_rel_tol None -> 모든 소신호 결과 resolution None, 값은 ε 가 있을 때와 같다(같은 요청 집합 -> 비트)."""
    case = ex7_case(tmp_path, ALL_SS, ss=_ss_eps(None))
    _, _, bn = _run(case)
    _, _, be = _run(declared_eps)
    assert [q for q, _ in bn.entries] == [q for q, _ in be.entries]
    for (q, rn), (_, re_) in zip(bn.entries, be.entries):
        assert rn.resolution is None, q
        assert rn.value == re_.value, q
        assert re_.resolution is not None, q


def test_resolution_none_for_undefined_pending_missing(tmp_path, declared_eps):
    """9.4: 값 None 결과(예 7c 섞인 절단)·pending·passive 누락 결과의 resolution 은 None. 같은 묶음의 값 있는 결과는 분해능 값."""
    case = ex7_case(tmp_path / "c", (("pm_ss_deg", ">=", 60.0, None), ("gain_ss_db", ">=", 30.0, None)), cs_resistor=True,
                    ss=_ss_eps(EPS7))
    m = bundle_map(_run(case, passives=ex7_passives(cs_resistor=True))[2])
    assert m["pm_ss_deg"].value is None and m["pm_ss_deg"].resolution is None
    assert m["gain_ss_db"].value is not None and m["gain_ss_db"].resolution is not None
    cons = (("gain_ss_db", ">=", 30.0, {"pending": "CI-10"}), ("rout_ss_ohm", "<=", 1e6, None))
    m = bundle_map(_run(ex7_case(tmp_path / "p", cons, ss=_ss_eps(EPS7)))[2])
    assert m["gain_ss_db"].resolution is None
    assert m["rout_ss_ohm"].resolution is not None
    for _, r in _run(declared_eps, passives=ex7_passives(drop=("Cs",)))[2].entries:
        assert r.value is None and r.resolution is None


def test_resolution_reused_with_block(declared_eps):
    """9.4·S-16: 같은 입력 두 번째 평가 -> 블록 재사용(`is`, computes 0), 분해능 재계산 0(lut_parameters·metric_resolutions·
    response_sensitivity 호출 0), 결과 묶음 비트 동일."""
    _, spec, snap = declared_eps
    reqs = requests_of(spec)
    metrics_ss.reset_stats()
    s1 = metrics_ss(snap, reqs, ex7_passives())
    with count_calls(lut_parameters, metric_resolutions, response_sensitivity) as n:
        s2 = metrics_ss(s1, reqs, ex7_passives())
    assert s2 is s1
    assert (metrics_ss.stats().computes, metrics_ss.stats().reuses) == (1, 1)
    assert n == {"lut_parameters": 0, "metric_resolutions": 0, "response_sensitivity": 0}


def test_resolution_computed_once_per_call(declared_eps):
    """7.4 [9절]: 계 조립이 있는 호출에서 lut_parameters 1회, 분석 열쇠마다 metric_resolutions 1회(β = 1 pm·parasitic_pm 은 같은
    열쇠 -- unity 케이스는 다른 fixture). declared 의 열쇠: β 루프 1, 포트 1, sense 1, ratio 1 = 4."""
    _, spec, snap = declared_eps
    reqs = requests_of(spec)
    with count_calls(lut_parameters, metric_resolutions) as n:
        metrics_ss(with_ss(snap, _ss_eps(EPS7), version="once"), reqs, ex7_passives())
    assert n["lut_parameters"] == 1
    assert n["metric_resolutions"] == 4


def test_epsilon_change_recomputes_and_scales_exactly(declared_eps):
    """lut_rel_tol 만 두 배 -> 블록 재계산(입력 버전이 바뀜), 값 그대로, 분해능 정확히 두 배(R-3, 이 예는 value = lut)."""
    _, spec, snap = declared_eps
    reqs = requests_of(spec)
    a = metrics_ss(snap, reqs, ex7_passives())
    b = metrics_ss(with_ss(a, _ss_eps(2.0 * EPS7), version="eps2"), reqs, ex7_passives())
    assert b is not a
    ea, eb = a.value("graph", METRICS_KEY, "metrics_ss"), b.value("graph", METRICS_KEY, "metrics_ss")
    for (q, ra), (_, rb) in zip(ea.entries, eb.entries):
        assert ra.value == rb.value, q
        if q.metric != "ratio_ss_db":                     # ratio: 두 열이 같은 계·비례 -> LUT 몫 0, value = 수치 몫(ε 무관)
            assert rb.resolution == 2.0 * ra.resolution, (q, ra.resolution, rb.resolution)
        else:
            assert rb.resolution == ra.resolution


def test_unity_beta_pm_and_parasitic_share_resolution(tmp_path):
    """7.4: 같은 열쇠의 두 요청(β = 1 pm_ss_deg·parasitic_pm_ss_deg)은 분해능도 같다(S-3 확장)."""
    case = ex7_case(tmp_path, ALL_SS, feedback=(), ss=_ss_eps(EPS7))
    m = bundle_map(_run(case)[2])
    assert m["pm_ss_deg"].resolution is not None
    assert m["pm_ss_deg"].resolution == m["parasitic_pm_ss_deg"].resolution
