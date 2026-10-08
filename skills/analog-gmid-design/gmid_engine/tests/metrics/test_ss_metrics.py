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
                                     ("node", "port_direction"), ("node", "port_role")}   # [CM] 7.4 reads + port_role
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
    """예 7c([CM 2026-10-08] 갱신): Cs 대신 저항 -> 절단 노드 n(전도)·x(용량 전용) 섞임. 섞인 절단 T(0) 는 이제 값 0(폐형식 분자에 s,
    metrics CONTRACT 예 7c·I-18) -> pm_ss_deg 정의 불가 사유는 dc_not_above_level(loop_cut_mixed_charge 아님), 예외 0."""
    case = ex7_case(tmp_path, (("pm_ss_deg", ">=", 60.0, None), ("gain_ss_db", ">=", 30.0, None)), cs_resistor=True)
    _, _, b = _run(case, passives=ex7_passives(cs_resistor=True))
    m = bundle_map(b)
    assert m["pm_ss_deg"].value is None
    assert [u.code for u in m["pm_ss_deg"].undefined] == ["dc_not_above_level"]
    assert "loop_cut_mixed_charge" not in {u.code for u in m["pm_ss_deg"].undefined}
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


# =====================================================================================================================
# 3.10 PM 전제(2절 표: loop_open_rhp_poles 는 phase_margin_deg 만 -> pm_ss_deg·parasitic_pm_ss_deg, I-17, 예 8·8a) -- spec 뷰 경로.
# 예 8 을 topology 로(넷 gnd·in·out·x, 교차 결합 M2·M3), 예 8a = 예 7 topology + 같은 쌍. 손 S2 ss_dev(lut_rel_tol 0.02).
# 기대값: conftest 폐형식 closed_ex8·closed_ex8a, 포트 뷰 극점은 이 파일의 2차식 근(노드 방정식 소거). 값 None -> resolution None(9.4).
# =====================================================================================================================

from .conftest import EX8, check_rhp_detail, closed_ex8, closed_ex8a, quad_roots, topo_doc, load_case, s2_of

PM_RHP = "loop_open_rhp_poles"
RHP_SS = (
    ("pm_ss_deg", ">=", 60.0, None),
    ("parasitic_pm_ss_deg", ">=", 45.0, None),
    ("gain_ss_db", ">=", 10.0, None),
    ("ugf_ss_hz", ">=", 1.0, None),
    ("gbw_ss_hz", ">=", 1.0, None),
)
RHP_EPS = 0.02


def _cross_ss(gx2, eps=RHP_EPS):
    gx = math.sqrt(gx2)
    rep = lambda s: _dc.replace(s, lut_rel_tol=eps)                       # noqa: E731
    return {"M1": rep(hand_ss(EX8["gm"], EX8["gds"])), "M2": rep(hand_ss(gx, EX8["gds"])),
            "M3": rep(hand_ss(gx, EX8["gds"]))}


def _cross_case(tmp_path, base7, gx2=EX8["gx2"], feedback=(), constraints=RHP_SS):
    """base7 False: 예 8(M1 + 교차 쌍, CL(out)·Cx(x)). True: 예 8a(예 7 소자 + 교차 쌍 + Cx). 반환 (td, spec, 손 S2, passive 값)."""
    mos = [("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "nmos", "out", "x", "gnd", "gnd"),
           ("M3", "nmos", "x", "out", "gnd", "gnd")]
    pas = [("CL", "capacitor", "out", "gnd"), ("Cx", "capacitor", "x", "gnd")]
    vals = {"CL": EX8["c"], "Cx": EX8["c"]}
    if base7:
        pas += [("Cf", "capacitor", "out", "in"), ("Cs", "capacitor", "in", "gnd")]
        vals.update(CL=EX7["cl"], Cf=EX7["cf"], Cs=EX7["cs"])
    topo = topo_doc("rhp8" + ("a" if base7 else "") + "_" + str(len(feedback)), mos=mos, passives=pas,
                    ports={"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, rails=("gnd",))
    els = tuple((n, k, vals[n]) for n, k, _, _ in pas)
    td, spec = load_case(tmp_path, topo, {"gnd": 0.0}, els, feedback, constraints, input_dc_v=0.0)
    snap = with_ss(s2_of(td, {"gnd": 0.0}), _cross_ss(gx2))
    return td, spec, snap, tuple(sorted(vals.items()))


def _assert_pm_rhp(r, expected_root):
    assert r.value is None
    assert r.resolution is None                                           # 9.4: 값 None -> resolution None
    assert r.undefined and r.undefined[0].code == PM_RHP
    u = r.undefined[0]
    assert (u.quantity, u.category) == ("phase_margin_deg", "definitional")
    roots = check_rhp_detail(u)                                           # 3.10 형식: float 쌍·정렬·개수·저장 순서
    assert len(roots) == 1
    re, im = roots[0]
    assert abs(re - expected_root) <= 1e-9 * expected_root and abs(im) <= 1e-9 * expected_root


def test_ex8_unity_both_pm_metrics_undefined_rhp(tmp_path):
    """예 8, feedback [] -> pm_ss_deg(β = 1 포트)·parasitic_pm_ss_deg 둘 다 None + loop_open_rhp_poles(근 +2e7). gain·UGF·GBW 는 값과
    분해능(gain lut = D·ε·4.8 -- test_resolution 의 폐형식), 옛 PM 271.145° 는 나오지 않는다."""
    td, spec, snap, pv = _cross_case(tmp_path, base7=False)
    v = {c.metric: c.view for c in spec.constraints}
    assert v["pm_ss_deg"].mode == "loop" and v["pm_ss_deg"].beta == "unity"        # 입력 확인
    m = bundle_map(metrics_ss(snap, requests_of(spec), pv).value("graph", METRICS_KEY, "metrics_ss"))
    d = closed_ex8()
    for q in ("pm_ss_deg", "parasitic_pm_ss_deg"):
        _assert_pm_rhp(m[q], d["poles"][1])
    assert rel_close(m["gain_ss_db"].value, 20.0, 1e-12)
    assert rel_close(m["ugf_ss_hz"].value, d["ugf_hz"], 1e-9)
    assert m["gbw_ss_hz"].value is not None
    g = DB_PER_NEPER * RHP_EPS * 4.8
    assert abs(m["gain_ss_db"].resolution - g) <= 1e-9 * g
    for q in ("gain_ss_db", "ugf_ss_hz", "gbw_ss_hz"):
        assert m[q].undefined == () or not m[q].undefined, q
        assert isinstance(m[q].resolution, float), q


def test_ex8a_beta_loop_and_port_pm_both_undefined_rhp(tmp_path):
    """예 8a, feedback [Cf]: β 루프 pm_ss_deg -> 근 15481601.1727(T 의 우반면 극점, 폐루프는 안정). 같은 소자의 포트 뷰
    parasitic_pm_ss_deg 도 우반면 극점(포트 H 분모 (CL + Cf)·C5 s² + (g2·C5 + g5(CL + Cf))s + (g2·g5 − gx²) 의 양근) -> 둘 다 None."""
    td, spec, snap, pv = _cross_case(tmp_path, base7=True, feedback=("Cf",))
    v = {c.metric: c.view for c in spec.constraints}
    assert v["pm_ss_deg"].mode == "loop" and v["pm_ss_deg"].beta == "declared"     # 입력 확인
    m = bundle_map(metrics_ss(snap, requests_of(spec), pv).value("graph", METRICS_KEY, "metrics_ss"))
    _assert_pm_rhp(m["pm_ss_deg"], closed_ex8a(EX8["gx2"])["poles"][1])
    cp, g2, g5, c5 = EX7["cl"] + EX7["cf"], 2.0 * EX8["gds"], EX8["gds"], EX8["c"]
    port_rhp = quad_roots(cp * c5, g2 * c5 + g5 * cp, g2 * g5 - EX8["gx2"])[1]
    assert port_rhp > 0.0
    _assert_pm_rhp(m["parasitic_pm_ss_deg"], port_rhp)
    assert m["gain_ss_db"].value is not None and m["gain_ss_db"].resolution is not None


def test_no_rhp_ex7_pm_values_unchanged_with_rhp_neighbour(tmp_path, declared_eps):
    """I-17 부정(뷰 경로): 우반면 극점 없는 예 7 의 PM 두 개는 폐형식 값 그대로이고 사유 없음 -- 예 8 평가를 먼저 해도 같다."""
    _cross_case(tmp_path, base7=False)
    m = bundle_map(_run(declared_eps)[2])
    assert rel_close(m["pm_ss_deg"].value, closed_ex7()["pm_deg"], 1e-12)
    assert rel_close(m["parasitic_pm_ss_deg"].value, ex7_port_closed()["pm_deg"], 1e-9)
    for q in ("pm_ss_deg", "parasitic_pm_ss_deg"):
        assert PM_RHP not in {u.code for u in (m[q].undefined or ())}
        assert m[q].resolution is not None


# =====================================================================================================================
# [CM 0e487b3] 출력 포트 CM 주입 pm_cm_ss_deg (7.4 cm_output 행, 7.11, S-21~S-28) -- 합성 CMFB 변형(conftest cm_variant).
# 기대값: (a) 손유도 T_cm(0)(cm_variant "t0"), "direct" 는 예 7d 형 폐형식 전체(closed_ex7d, gm = gmp, gds = Go, Cg = PMOS cgs 하나 --
# 반회로마다 R·Cg 하나), (b) 독립 Middlebrook ref_cm_output + ref_pm(brentq 교차·언랩 위상). 허용: PM·UGF 상대 ≤ 1e-9(I-18 과 같은
# PM 규약), dc_db 상대 ≤ 1e-12(dB 는 T(0) 의 log -- 상대 1e-12 는 차원·eps 규모 여유).
# =====================================================================================================================

from .conftest import CM_CG, CM_CL, CM_GO, CM_R, closed_ex7d, cm_case, cm_variant, ref_cm_output, ref_pm  # noqa: E402

CM_REQ = (("pm_cm_ss_deg", ">=", 60.0, None),)
GAIN_DIFF = {"ac_excite": {"ip": 0.5, "im": -0.5}, "sense_p": "op", "sense_n": "om", "sense_mode": "differential"}


def _cm_run(case, metrics=None):
    td, spec, snap, pv, v = case
    reqs = requests_of(spec, metrics)
    out = metrics_ss(snap, reqs, pv)
    return out, reqs, out.value("graph", METRICS_KEY, "metrics_ss")


def _report(b):
    assert len(b.reports) == 1 and b.reports[0][0] == "cm_loop", b.reports
    return dict(b.reports[0][1])


@pytest.fixture(scope="module")
def cm_direct(tmp_path_factory):
    return cm_case(tmp_path_factory.mktemp("cmd"), "direct", CM_REQ)


def test_cm_view_derived_from_output_pair(cm_direct):
    """입력 확인: 로더가 유도한 pm_cm_ss_deg 뷰 = cm_output, 가중 (om ½, op ½)(SPEC_CONTRACT 3절)."""
    (c,) = [c for c in cm_direct[1].constraints if c.metric == "pm_cm_ss_deg"]
    assert c.view.mode == "cm_output" and tuple(c.view.weights) == (("om", 0.5), ("op", 0.5))


def test_cm_direct_closed_form_s23(cm_direct):
    """S-23(값): '직접' 변형(평균 저항 -> PMOS 부하 gate) = 예 7d 형 폐형식 T = gmp/((Go + sCL)(1 + sRCg) + sCg) 의 PM(상대 ≤ 1e-9).
    출력 구동자(M1·M3 drain)에서 끊어도 단일 제어 변수 루프라 감지 넷에서 끊은 되돌림 비와 같다(I-12)."""
    ref = closed_ex7d(dict(gm=1e-4, gds=CM_GO, cg=CM_CG, cl=CM_CL, rf=CM_R))
    _, _, b = _cm_run(cm_direct)
    r = bundle_map(b)["pm_cm_ss_deg"]
    assert r.undefined == ()
    assert rel_close(r.value, ref["pm_deg"], 1e-9), (r.value, ref["pm_deg"])
    rep = _report(b)
    assert rel_close(rep["ugf_hz"], ref["ugf_hz"], 1e-9)
    assert rel_close(rep["dc_db"], ref["gain_db"], 1e-12)


@pytest.mark.parametrize("variant", ["direct", "ref_rc", "err_amp", "sf_buffer", "dda"])
def test_cm_variants_match_independent_middlebrook(tmp_path, variant):
    """S-21 일반성(연속시간 CMFB 변형 -- 저항 평균 직접, 감지 넷 기준 R·C, 저항 평균 -> 오차 증폭 2단, 소스 팔로어 버퍼 -> 저항 평균,
    DDA): T_cm(0) dB = 손유도(상대 ≤ 1e-12), PM·UGF = 독립 Middlebrook(상대 ≤ 1e-9), 값 있으면 undefined 비어 있음."""
    case = cm_case(tmp_path, variant, CM_REQ)
    v = case[4]
    _, _, b = _cm_run(case)
    r = bundle_map(b)["pm_cm_ss_deg"]
    rep = _report(b)
    assert rel_close(rep["dc_db"], 20.0 * math.log10(v["t0"]), 1e-12), (rep["dc_db"], v["t0"])
    assert abs(ref_cm_output(variant, 1e-2) - v["t0"]) <= 1e-6 * v["t0"]          # 손유도와 독립 MNA 가 서로 맞음(입력 확인)
    ugf, pm = ref_pm(lambda w: ref_cm_output(variant, w))
    assert pm is not None
    assert r.undefined == () and rel_close(r.value, pm, 1e-9), (r.value, pm)
    assert rel_close(rep["ugf_hz"], ugf, 1e-9)
    assert rep["pm_deg"] == r.value and rep["undefined"] == ()
    assert rep["break_nets"] == ("om", "op")


def test_cm_triode_average_is_definitional_false_violation(tmp_path):
    """7.11 변형 4(정의의 한계, 계약에 '거짓 위반'으로 명시): 평균 소자가 triode MOS(channel 이 출력에 물림)면 그 MOS 가 구동자로 옮겨져
    루프가 절단선을 지나지 않는다 -> T_cm(0) = 0 -> dc_not_above_level(dc_magnitude 0). 바이어스(소신호 값)와 무관한 구조 결과다:
    gm = 0·gds = 1/R 로 둔 triode 판은 전기적으로 '직접' 변형과 같은 회로이고 물리 CM 루프 이득은 gmp/Go = 50 이다(아래 입력 확인).
    -- 이 test 는 계약이 적은 현재 동작을 고정하고, 물리 이득과의 차이를 숫자로 남긴다(사용자 결정 대기 항목)."""
    case = cm_case(tmp_path, "triode", CM_REQ)
    _, _, b = _cm_run(case)
    r = bundle_map(b)["pm_cm_ss_deg"]
    assert r.value is None
    assert [u.code for u in r.undefined] == ["dc_not_above_level"]
    assert dict(r.undefined[0].detail)["dc_magnitude"] == 0.0
    assert abs(ref_cm_output("triode", 1.0)) <= 1e-12                      # 독립 구현도 같은 절단 규칙이면 0
    assert cm_variant("triode")["t0"] == pytest.approx(50.0, rel=1e-15)    # 물리 루프 이득(손유도) -- 정의가 놓치는 값
    assert ref_cm_output("direct", 1e-2) == pytest.approx(50.0, rel=1e-6)  # 같은 전기 회로를 저항으로 쓰면 50


def test_cm_low_gain_violation_detail_s25(tmp_path):
    """S-25·결정 A: T_cm(0) = gmp/Go = 0.5 ≤ 1 -> value None, undefined dc_not_above_level + detail dc_magnitude = 0.5, 경고 없음,
    reports dc_db = 20·log10 0.5, pm·ugf None."""
    case = cm_case(tmp_path, "low_gain", CM_REQ)
    _, _, b = _cm_run(case)
    r = bundle_map(b)["pm_cm_ss_deg"]
    assert r.value is None
    assert [u.code for u in r.undefined] == ["dc_not_above_level"]
    assert rel_close(dict(r.undefined[0].detail)["dc_magnitude"], 0.5, 1e-12)
    rep = _report(b)
    assert rel_close(rep["dc_db"], 20.0 * math.log10(0.5), 1e-12)
    assert rep["pm_deg"] is None and rep["ugf_hz"] is None and rep["undefined"] == ("dc_not_above_level",)
    assert b.warnings == ()


def test_cm_report_only_and_warning_without_declaration_s26_s27(tmp_path, cm_direct):
    """S-26·S-27: pm_cm_ss_deg 요청이 없어도 차동 출력 회로는 reports 에 같은 T_cm(같은 값), T_cm(0) = 50 > 1 이라
    warnings == (("cm_loop_unconstrained", (("dc_db", 20·log10 50),)),). 요청이 있으면 경고 없음, 선언 결과 값 == reports pm_deg."""
    case = cm_case(tmp_path, "direct", (("gain_ss_db", ">=", 0.0, GAIN_DIFF),))
    _, _, b = _cm_run(case)
    assert [q.metric for q, _ in b.entries] == ["gain_ss_db"]
    rep = _report(b)
    _, _, bd = _cm_run(cm_direct)
    rd = _report(bd)
    assert rep["break_nets"] == rd["break_nets"] == ("om", "op")
    assert rel_close(rep["pm_deg"], rd["pm_deg"], 1e-12) and rel_close(rep["dc_db"], rd["dc_db"], 1e-12)
    assert len(b.warnings) == 1
    code, det = b.warnings[0]
    assert code == "cm_loop_unconstrained" and [k for k, _ in det] == ["dc_db"]
    assert rel_close(dict(det)["dc_db"], 20.0 * math.log10(50.0), 1e-12)
    assert bd.warnings == ()
    assert bundle_map(bd)["pm_cm_ss_deg"].value == rd["pm_deg"]


def test_cm_no_report_for_single_ended(declared):
    """S-26: 차동 출력 포트 쌍이 없는 회로(예 7)는 reports == ()·warnings == ()."""
    _, _, b = _run(declared)
    assert b.reports == () and b.warnings == ()


@pytest.mark.parametrize("variant", ["low_gain"])
def test_cm_no_warning_when_dc_not_above_one(tmp_path, variant):
    """S-27: 요청이 없어도 T_cm(0) ≤ 1 이면 경고 없음(보고는 있다)."""
    case = cm_case(tmp_path, variant, (("gain_ss_db", ">=", 0.0, GAIN_DIFF),))
    _, _, b = _cm_run(case)
    assert b.warnings == () and _report(b)["undefined"] == ("dc_not_above_level",)


def test_cm_reuse_and_shared_system_s28(cm_direct):
    """S-28: 같은 입력 두 번 -> computes 0(`is`), reports·warnings 같음; 선언 요청과 보고가 같은 절단 계를 공유 -> systems 1."""
    td, spec, snap, pv, _ = cm_direct
    reqs = requests_of(spec)
    metrics_ss.reset_stats()
    s1 = metrics_ss(snap, reqs, pv)
    s2 = metrics_ss(s1, reqs, pv)
    assert s2 is s1 and metrics_ss.stats().computes == 1
    b = s1.value("graph", METRICS_KEY, "metrics_ss")
    assert dict(b.detail)["systems"] == 1


def test_cm_inputs_are_ac_ground_s24(tmp_path, cm_direct):
    """S-24: 같은 평가에 입력을 구동하는 포트 뷰(gain_ss_db)가 함께 있어도 pm_cm_ss_deg 값 같음(상대 ≤ 1e-12, 공유 격자만 다를 수 있음)."""
    case = cm_case(tmp_path, "direct", CM_REQ + (("gain_ss_db", ">=", 0.0, GAIN_DIFF),))
    _, _, b = _cm_run(case)
    _, _, bd = _cm_run(cm_direct)
    assert rel_close(bundle_map(b)["pm_cm_ss_deg"].value, bundle_map(bd)["pm_cm_ss_deg"].value, 1e-12)
    assert dict(b.detail)["systems"] == 2                                   # 포트 계 + CM 절단 계


def test_cm_net_rename_invariance(tmp_path, cm_direct):
    """S-8 확장: 넷 이름 전단사(이름순 노드 번호가 바뀜) 뒤 pm_cm_ss_deg·reports 같음(break_nets 는 새 이름)."""
    names = {"op": "zp", "om": "aa", "c": "mm", "ip": "q1", "im": "b0", "gnd": "g0", "vdd": "zz"}
    case = cm_case(tmp_path, "direct", CM_REQ, names=names)
    _, _, b = _cm_run(case)
    _, _, bd = _cm_run(cm_direct)
    assert rel_close(bundle_map(b)["pm_cm_ss_deg"].value, bundle_map(bd)["pm_cm_ss_deg"].value, 1e-12)
    assert _report(b)["break_nets"] == ("aa", "zp")


def test_cm_report_only_adds_one_system_s28(tmp_path):
    """S-28(bea18e0): 선언 pm_cm_ss_deg 가 없고 보고 전용 T_cm 이 계산되면 cm_output 계 1개 추가 -- gain_ss_db 하나 + 차동 출력 회로
    -> systems = 2(포트 계 + cm 계); pm_cm_ss_deg 하나 -> 1(test_cm_reuse_and_shared_system_s28); 둘 다 -> 2(공유, S-24 test)."""
    case = cm_case(tmp_path, "direct", (("gain_ss_db", ">=", 0.0, GAIN_DIFF),))
    _, _, b = _cm_run(case)
    assert dict(b.detail)["systems"] == 2
    assert len(b.reports) == 1
