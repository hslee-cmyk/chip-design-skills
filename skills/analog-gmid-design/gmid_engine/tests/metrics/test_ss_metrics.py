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
