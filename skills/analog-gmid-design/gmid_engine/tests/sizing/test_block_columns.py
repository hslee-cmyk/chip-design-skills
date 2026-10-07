"""`dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)` -- CONTRACT 5.4: 노드전압 정본.

기대값: conftest `expected_columns`(writer 식·창 규칙을 독립 구현, VGS 는 toy LUT 닫힌 식 `Oracle.vgs_of`)와 손계산.
순환 SCC 는 [r4] VDS 정의역 하한의 반복 중/strict 규칙 test(끝 절)에서만 쓴다(수렴값은 θ 를 해에서 거꾸로 만들어 손으로 안다).
"""
import math

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, PathValue, SccLog, Window, dc_columns

from .conftest import (Oracle, build_ctx, circuit_cs_res, circuit_empty_window, detail, expected_columns, free_currents, mos,
                       new_access, node_voltages, r4_arrays, r4_ln_idu, r4_vds_floor, r4_vgs_of, rel_close, run_blocks,
                       theta_a, theta_c, theta_r4c, topo, two, write_r4_lut)

TOL = 1e-12


def assert_voltages(snap, ctx, theta):
    V_exp, win_exp, ln_exp = expected_columns(snap, theta, ctx.fixed_values, ctx.resistor_values)
    V = node_voltages(snap)
    assert set(V) == set(V_exp)
    for n in V_exp:
        assert abs(V[n] - V_exp[n]) <= TOL, (n, V[n], V_exp[n])
    win = dict(snap.column("node", "dc_window"))
    assert set(win) == set(win_exp)
    for n, (lo, hi) in win_exp.items():
        assert isinstance(win[n], Window)
        assert abs(win[n].lo - lo) <= TOL and abs(win[n].hi - hi) <= TOL
    ln = dict(snap.column("device", "dc_ln_idu"))
    assert set(ln) == set(ln_exp)
    for m in ln_exp:
        assert abs(ln[m] - ln_exp[m]) <= 1e-9, (m, ln[m], ln_exp[m])
    return V


# ---------------------------------------------------------------------------
# 회로 C: W4 창 + vgs_gate (nmos·pmos 부호)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("y,vgs1,vgs2", [(0.5, 0.6, 0.7), (0.3, 0.55, 0.95), (0.8, 0.43, 0.61)])
def test_circuit_c_hand(ctx_c, y, vgs1, vgs2):
    ctx = ctx_c[2]
    th = theta_c(y=y, x1=Oracle.ln_idu("nmos", vgs1, 1.8 * y, 0.0), x2=Oracle.ln_idu("pmos", vgs2, 1.8 * (1 - y), 0.0))
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    # 손계산: out = 0 + y·(1.8 − 0) (창 = 레일 범위, VDsat 항 없음), in = 0 + VGS1, pb = 1.8 − VGS2
    assert abs(V["out"] - 1.8 * y) <= TOL
    assert abs(V["in"] - vgs1) <= 1e-9
    assert abs(V["pb"] - (1.8 - vgs2)) <= 1e-9
    assert dict(snap.column("node", "dc_window"))["out"].lo == 0.0
    assert dict(snap.column("node", "dc_window"))["out"].hi == 1.8


def test_circuit_c_path_values(ctx_c):
    ctx = ctx_c[2]
    th = theta_c()
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    pv = dict(snap.column("node", "dc_path_values"))
    assert set(pv) == set(V)                       # 모든 노드
    for n, vals in pv.items():
        assert all(isinstance(p, PathValue) for p in vals)
        assert [p.relation for p in vals] == sorted(p.relation for p in vals)
    rel = {n: {p.relation: p.value for p in vals} for n, vals in pv.items()}
    vgs1 = Oracle.vgs_of("nmos", th[("ln_idu", "M1")], V["out"], 0.0)
    vgs2 = Oracle.vgs_of("pmos", th[("ln_idu", "M2")], 1.8 - V["out"], 0.0)
    assert set(rel["in"]) == {("vgs", "M1")} and abs(rel["in"][("vgs", "M1")] - (0.0 + vgs1)) <= 1e-9
    assert set(rel["gnd"]) == {("fixed", "rail"), ("vgs", "M1")}
    assert rel["gnd"][("fixed", "rail")] == 0.0 and abs(rel["gnd"][("vgs", "M1")] - (V["in"] - vgs1)) <= 1e-9
    assert set(rel["vdd"]) == {("fixed", "rail"), ("vgs", "M2")}
    assert abs(rel["vdd"][("vgs", "M2")] - (V["pb"] + vgs2)) <= 1e-9         # pmos: V(s) = V(g) − s·VGS
    assert set(rel["pb"]) == {("vgs", "M2")}
    assert rel["out"] == {("y", "out"): V["out"]}


def test_writer_ln_idu_is_theta(ctx_c):
    th = theta_c()
    snap = run_blocks(ctx_c[2], th, upto="columns")
    assert dict(snap.column("device", "dc_ln_idu")) == {"M1": th[("ln_idu", "M1")], "M2": th[("ln_idu", "M2")]}


def test_scc_log_matches_order(ctx_c):
    snap = run_blocks(ctx_c[2], theta_c(), upto="columns")
    log = snap.value("graph", DC_KEY, "dc_scc_log")
    order = snap.value("graph", DC_KEY, "dc_scc_order")
    assert all(isinstance(x, SccLog) for x in log)
    assert [(x.index, x.nodes) for x in log] == [(e.index, e.nodes) for e in order]


# ---------------------------------------------------------------------------
# 회로 A: resistor_drop 부호(t0/t1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("i,r", [(1e-5, 9e4), (2e-6, 3e5), (5e-5, 1e4)])
def test_resistor_drop_known_t0(ctx_a, i, r):
    ctx = ctx_a[2]
    th = theta_a(i=i, r=r)
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    assert abs(V["out"] - (1.8 - i * r)) <= TOL                   # known vdd = t0 -> V = V(vdd) − I·R
    rel = {p.relation: p.value for p in dict(snap.column("node", "dc_path_values"))["vdd"]}
    assert abs(rel[("resistor", "R1")] - (V["out"] + i * r)) <= TOL
    rel_out = {p.relation: p.value for p in dict(snap.column("node", "dc_path_values"))["out"]}
    assert abs(rel_out[("resistor", "R1")] - (1.8 - i * r)) <= TOL


def test_resistor_drop_known_t1(tmp_path, toy_access):
    doc = topo("hand_cs_res_rev2", [mos("M1", "nmos", "out", "in", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R1", "resistor", "out", "vdd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    i_r1, r = -1e-5, 9e4                                           # R1 전류(out -> vdd 방향) 음수 = M1 양수
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.0),
          ("current", "R1"): i_r1, ("resistance", "R1"): r}
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    assert abs(V["out"] - (1.8 + i_r1 * r)) <= TOL                 # known vdd = t1 -> V = V(vdd) + I·R


def test_declared_resistor_value_used(tmp_path, toy_access):
    doc = circuit_cs_res()
    doc["topology_name"] = "hand_cs_res_declared"
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("R1", 6e4),))[2]
    assert ctx.resistor_values == (("R1", 6e4),)
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 1.2, 0.0), ("current", "R1"): 1e-5}
    snap = run_blocks(ctx, th, upto="columns")
    assert abs(node_voltages(snap)["out"] - (1.8 - 1e-5 * 6e4)) <= TOL


def test_zero_current_drop_is_zero_and_cycle_dependent(tmp_path, toy_access):
    """R2(g3, vdd) 는 잎 가지치기 저항(전류 0) -> V(g3) = V(vdd) 정확. M2 (gate g3) 는 G_vgs 비트리 -> 종속,
    ln_idu = ln IDu(노드 vgs = 0)."""
    doc = topo("hand_zero_drop",
               [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "g3", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, passives=[two("R2", "resistor", "g3", "vdd")])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.72, 0.0),
          ("y", "out"): 0.4}
    th.update(free_currents(ctx, {"M1": 1e-6, "M2": 1e-6, "R2": 0.0}))
    assert set(dict(th)) == set(ctx.schema.components)
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    assert V["g3"] == 1.8
    assert dict(snap.column("device", "dc_drop_current"))["R2"] == 0.0
    assert snap.value("device", "M2", "dc_coord").role == "dependent"
    exp = Oracle.ln_idu("pmos", 0.0, 1.8 - 0.72, 0.0)
    assert abs(dict(snap.column("device", "dc_ln_idu"))["M2"] - exp) <= 1e-9


def test_parallel_dependent_ln_idu(tmp_path, toy_access):
    """M1·M2 같은 (gate, source), 다른 drain(VDS 다름) -> 종속 쪽 ln_idu 는 자기 VDS 의 op_point 값(writer 값과 다름)."""
    doc = topo("hand_parallel",
               [mos("M1", "nmos", "o1", "in", "gnd"), mos("M2", "nmos", "o2", "in", "gnd"),
                mos("M3", "pmos", "o1", "pb", "vdd"), mos("M4", "pmos", "o2", "pb", "vdd")],
               {"in": ("input", "x"), "o1": ("output", "y")})
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    comps = dict.fromkeys(ctx.schema.components)
    th = {}
    for kind, key in comps:
        th[(kind, key)] = {"L": 1e-6, "current": 1e-5, "y": 0.3 if key == "o1" else 0.7}.get(kind)
    for m in ("M1", "M2"):
        if ("ln_idu", m) in comps:
            th[("ln_idu", m)] = Oracle.ln_idu("nmos", 0.6, 0.5, 0.0)
    for m in ("M3", "M4"):
        if ("ln_idu", m) in comps:
            th[("ln_idu", m)] = Oracle.ln_idu("pmos", 0.7, 0.9, 0.0)
    assert None not in th.values()
    snap = run_blocks(ctx, th, upto="columns")
    assert_voltages(snap, ctx, th)
    roles = {m: snap.value("device", m, "dc_coord").role for m in ("M1", "M2", "M3", "M4")}
    assert sorted(roles[m] for m in ("M1", "M2")) == ["dependent", "writer"]


def test_window_with_declared_target(tmp_path, toy_access):
    """s1 = W3 0.3 V: out 창 = [V(s1), V(vdd)] = [0.3, 1.8]; in = 0.3 + VGS(vsb 0.3)."""
    doc = topo("hand_w3",
               [mos("M1", "nmos", "out", "in", "s1"), mos("M2", "pmos", "out", "pb", "vdd"),
                mos("M5", "nmos", "s1", "vb5", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")})
    ctx = build_ctx(tmp_path, doc, toy_access, node_targets=(("s1", 0.3),))[2]
    assert ctx.fixed_values == (("s1", 0.3),)
    y = 0.4
    vout = 0.3 + y * 1.5
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M5"): 2e-6,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.5, vout - 0.3, 0.3),
          ("ln_idu", "M2"): Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0),
          ("ln_idu", "M5"): Oracle.ln_idu("nmos", 0.65, 0.3, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M5": 1e-5}))   # KCL: 세 소자 같은 전류
    assert set(th) == set(ctx.schema.components)
    snap = run_blocks(ctx, th, upto="columns")
    V = assert_voltages(snap, ctx, th)
    w = dict(snap.column("node", "dc_window"))["out"]
    assert (w.lo, w.hi) == (0.3, 1.8)
    assert abs(V["out"] - vout) <= TOL
    assert abs(V["in"] - (0.3 + 0.5)) <= 1e-9
    assert abs(V["vb5"] - 0.65) <= 1e-9
    assert V["s1"] == 0.3
    assert {p.relation: p.value for p in dict(snap.column("node", "dc_path_values"))["s1"]}[
        ("fixed", "declared_target")] == 0.3


# ---------------------------------------------------------------------------
# 실패
# ---------------------------------------------------------------------------

def test_empty_window(tmp_path, toy_access):
    ctx = build_ctx(tmp_path, circuit_empty_window(), toy_access)[2]
    th = {}
    for kind, key in ctx.schema.components:
        if kind != "current":
            th[(kind, key)] = {"L": 1e-6, "y": 0.5, "ln_idu": Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}[kind]
    # KCL x: MA + MC = MB (MB 는 pmos, x 로 들어옴)
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 2e-5, "MC": 1e-5}))
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_columns(snap, items, ctx.fixed_values, ctx.resistor_values, ctx.lut)
    d = detail(ei.value)
    assert d["reason"] == "empty_window" and d["item"] == 7
    assert d["node"] == "x" and d["lo"] == 1.8 and d["hi"] == 0.0
    assert "constraints" in d
    assert ei.value.record.devices == () and ei.value.record.margin is None


def _lut_fail(ctx, th):
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_columns(snap, items, ctx.fixed_values, ctx.resistor_values, ctx.lut)
    return ei.value


def test_lut_target_out_of_range(ctx_c):
    th = theta_c(x1=Oracle.ln_idu("nmos", 2.5, 0.9, 0.0))          # VGS 2.5 > 격자 최대 1.8
    e = _lut_fail(ctx_c[2], th)
    d = detail(e)
    assert d["reason"] == "lut_query_failed"
    assert d["lut_reason"] == "lut_target_out_of_range"
    assert d["device_query"] == "vgs_of_coordinate"
    assert e.record.devices == ("M1",)


def test_lut_l_not_anchor(ctx_c):
    e = _lut_fail(ctx_c[2], theta_c(l2=1.5e-6))
    d = detail(e)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_l_not_anchor"
    assert e.record.devices == ("M2",)


def test_lut_axis_out_of_range_vsb(tmp_path, toy_access):
    """bulk 를 out 에 선언: vsb = V(gnd) − V(out) = −0.6 < VS 격자 최소 −0.45 -> 축 밖(클램프 없음)."""
    ctx = build_ctx(tmp_path, circuit_cs_res(bulk_m1="out"), toy_access)[2]
    e = _lut_fail(ctx, theta_a(i=1e-5, r=1.2e5))
    d = detail(e)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_axis_out_of_range"
    assert e.record.devices == ("M1",)


# ---------------------------------------------------------------------------
# [r2] 1변수 노드 = 구간 bisection (5.4)
# ---------------------------------------------------------------------------

def _mirror_ctx(tmp_path, toy_access):
    doc = topo("bc_mirror",
               [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                mos("M3", "pmos", "out", "in", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "nb")])
    return build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5),))[2]


def _mirror_theta(ctx, v_diode):
    import math as _m
    x1 = Oracle.ln_idu("nmos", v_diode, v_diode, 0.0)       # diode: vds = vgs, vsb 0
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("ln_idu", "M1"): x1,
          ("ln_idu", "M3"): Oracle.ln_idu("pmos", 0.7, 0.9, 0.0), ("y", "out"): 0.5}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5, "I1": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    return th


@pytest.mark.parametrize("v_star", [0.35, 0.6, 1.1])
def test_diode_one_variable_bisection(tmp_path, toy_access, v_star):
    ctx = _mirror_ctx(tmp_path, toy_access)
    snap = run_blocks(ctx, _mirror_theta(ctx, v_star), upto="columns")
    V = node_voltages(snap)
    tol = Oracle.tol_v()
    from .conftest import LAM
    # bisection 마지막 구간 폭 ≤ tol -> 가운데 오차 ≤ tol/2, 한 번 다듬기(g) 로 |g'| = LAM/(gm/ID) 배 줄어든다
    assert abs(V["nb"] - v_star) <= tol / 2 * (LAM / Oracle.gm_id(v_star)) + 1e-12
    log = {e.nodes: e for e in snap.value("graph", DC_KEY, "dc_scc_log")}[("nb",)]
    # 구간 = 레일 [0, 1.8] ∩ vds(= x) ∈ [0, 1.8] ∩ vsb(= 0) ∈ VS 격자 -> [0, 1.8]; 반복 수 = k_max(1.8, tol)
    assert log.iterations == math.ceil(math.log2(1.8 / tol))
    assert log.k_max == log.iterations and log.tol == pytest.approx(tol, rel=1e-9)
    # M2 는 종속(parallel): ln_idu = ln IDu(vgs = V(nb), vds = V(out))
    assert abs(dict(snap.column("device", "dc_ln_idu"))["M2"] - Oracle.ln_idu("nmos", V["nb"], V["out"], 0.0)) <= 1e-9


def test_source_follower_one_variable(tmp_path, toy_access):
    """M1 nmos (vdd, in, out): out 은 vgs_source 1변수(vds = 1.8 − x, vsb = x). 근은 이 test 의 독립 이분법(1e-12)으로."""
    doc = topo("bc_sf", [mos("M1", "nmos", "vdd", "in", "out"), mos("M2", "nmos", "out", "vb", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")})
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["out"].relation, w["out"].element) == ("vgs_source", "M1")
    x1 = Oracle.ln_idu("nmos", 0.6, 0.9, 0.5)
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): x1,
          ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.55, 0.6, 0.0)}
    for k, key in ctx.schema.components:
        if k == "y":
            th[(k, key)] = 0.7
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    vin = V["in"]

    def h(x):
        return x - (vin - Oracle.vgs_of("nmos", x1, 1.8 - x, x))
    lo, hi = 0.0, 1.8
    for _ in range(200):
        m = 0.5 * (lo + hi)
        if (h(m) > 0) == (h(lo) > 0):
            lo = m
        else:
            hi = m
    root = 0.5 * (lo + hi)
    assert abs(V["out"] - root) <= Oracle.tol_v() / 2


@pytest.mark.parametrize("v_star", [2.0, -0.3])
def test_no_root_in_window(tmp_path, toy_access, v_star):
    """근이 레일 밖(2.0 V) 또는 VGS 격자 아래(−0.3 V): g 가 ±inf(목표 밖) -> 끝 부호 같음 -> no_root_in_window."""
    ctx = _mirror_ctx(tmp_path, toy_access)
    th = _mirror_theta(ctx, v_star)
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_columns(snap, items, ctx.fixed_values, ctx.resistor_values, ctx.lut)
    d = detail(ei.value)
    assert d["reason"] == "no_root_in_window"
    assert d["item"] in (6, 7)
    assert ei.value.record.devices == ("M1",)
    assert d["node"] == "nb"
    for k in ("lo", "hi", "h_lo", "h_hi", "bounds"):
        assert k in d
    assert d["lo"] == 0.0 and d["hi"] == 1.8
    assert ei.value.record.margin is None                     # 두 끝 |h| 모두 무한


def test_vdsat_not_in_window(ctx_c):
    """창은 인접 전도 소자 반대 단자 전압만으로 정해진다(VDsat 여유 없음): y = 0 -> out 이 정확히 0 V."""
    th = theta_c(y=0.0, x1=Oracle.ln_idu("nmos", 0.6, 0.0, 0.0), x2=Oracle.ln_idu("pmos", 0.7, 1.8, 0.0))
    snap = run_blocks(ctx_c[2], th, upto="columns")
    assert node_voltages(snap)["out"] == 0.0


def test_vdsat_not_in_window_even_with_column(ctx_r4c):
    """[r4] (3) VDSAT 열이 있는 LUT 에서도 W4 창에 VDsat 항이 없다: y = 0 / 1 -> out 이 정확히 레일(창 = [0, 1.8])."""
    for y in (0.0, 1.0):
        snap = run_blocks(ctx_r4c, theta_r4c(y=y), upto="columns")
        w = dict(snap.column("node", "dc_window"))["out"]
        assert (w.lo, w.hi) == (0.0, 1.8)
        assert node_voltages(snap)["out"] == 1.8 * y


# ---------------------------------------------------------------------------
# [r4] 1변수 구간의 VDS 정의역 하한(on_mask 유도) + 구간 끝 부동소수 안쪽 보정 + 반복 중/strict 의 lut_curve_undefined
# ---------------------------------------------------------------------------
# LUT F : nmos VDS 열 0 꺼짐(하한 0.25), pmos 열 0~3 꺼짐(하한 1.0) -- LUT v2 의 VDS = 0 열(ID = GM = 0) 모양.
# LUT F2: nmos 는 열 0 켜짐, 열 1 에 꺼진 점 하나(L 2e-6·VGS 0.625·VS 0.25) -> '끝 열까지 모두 켜진 첫 열' = 열 2(0.5);
#         pmos 는 열 0 꺼짐 + 마지막 열에 꺼진 점 하나(L 2e-6·VS 2.0) -> 끝까지 켜진 열이 없다 -> VDS 격자 최소(0.0).
F_OFF = {"nmos": 1, "pmos": 4}
F2_OFF_COLS = {"pmos": 1}
F2_OFF_POINTS = {"nmos": [(1, 5, 1, 3)], "pmos": [(1, 3, 8, 10)]}


def _floor(kind, which):
    if which == "F":
        return r4_vds_floor(r4_arrays(kind, off_cols=F_OFF[kind]))
    return r4_vds_floor(r4_arrays(kind, off_cols=F2_OFF_COLS.get(kind, 0), off_points=F2_OFF_POINTS[kind]))


def test_floor_oracle_values():
    """기대값 원천 확인(피검 아님): on_mask 로 유도한 하한."""
    assert _floor("nmos", "F") == 0.25 and _floor("pmos", "F") == 1.0
    assert _floor("nmos", "F2") == 0.5 and _floor("pmos", "F2") == 0.0
    # 판별력: '처음 모두 켜진 열'(끝까지 요구 없음) 규칙이면 F2 nmos 0.0, F2 pmos 0.25 가 된다
    a = r4_arrays("pmos", off_cols=1, off_points=F2_OFF_POINTS["pmos"])
    on = (a["ID"] > 0) & (a["GM"] > 0)
    assert on[:, :, 1, :].all() and not on[:, :, 8, :].all()


@pytest.fixture(scope="module")
def acc_f(tmp_path_factory):
    return new_access(write_r4_lut(tmp_path_factory.mktemp("lut_f"), off_cols=F_OFF))


@pytest.fixture(scope="module")
def acc_f2(tmp_path_factory):
    return new_access(write_r4_lut(tmp_path_factory.mktemp("lut_f2"), off_cols=F2_OFF_COLS, off_points=F2_OFF_POINTS))


def _diode_ctx(tmp_path, acc, kind, supplies=None):
    """kind 의 diode M1(1변수 노드 nb) + 거울 M2 + 반대 kind 부하 M3. bulk = source 레일(vsb 0)."""
    if kind == "nmos":
        net = [mos("M1", "nmos", "nb", "nb", "gnd", "gnd"), mos("M2", "nmos", "out", "nb", "gnd", "gnd"),
               mos("M3", "pmos", "out", "in", "vdd", "vdd")]
        src = two("I1", "current_source", "vdd", "nb")
    else:
        net = [mos("M1", "pmos", "nb", "nb", "vdd", "vdd"), mos("M2", "pmos", "out", "nb", "vdd", "vdd"),
               mos("M3", "nmos", "out", "in", "gnd", "gnd")]
        src = two("I1", "current_source", "nb", "gnd")
    doc = topo("r4_diode_%s" % kind, net, {"in": ("input", "x"), "out": ("output", "y")}, sources=[src])
    return build_ctx(tmp_path, doc, acc, supplies=supplies, element_values=(("I1", 1e-5),))[2]


def _diode_theta(ctx, kind, vgs1):
    """M1 diode 의 vgs = vds = vgs1 이 근이 되는 좌표. out 은 y = 0.25(M2·M3 VDS 가 두 LUT 하한 위)."""
    other = "pmos" if kind == "nmos" else "nmos"
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6, ("ln_idu", "M1"): r4_ln_idu(kind, vgs1, vgs1, 0.0),
          ("ln_idu", "M3"): r4_ln_idu(other, 0.7, 1.35, 0.0), ("y", "out"): 0.25}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5, "I1": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    return th


def _no_root(ctx, th):
    with pytest.raises(SealViolationError) as ei:
        run_blocks(ctx, th, upto="columns")
    d = detail(ei.value)
    assert d["reason"] == "no_root_in_window" and ei.value.record.devices == ("M1",) and d["node"] == "nb"
    return d


@pytest.mark.parametrize("which", ["F", "F2"])
def test_floor_is_interval_lo_nmos_diode(tmp_path, acc_f, acc_f2, which):
    """nmos diode: vds = x -> 구간 lo = VDS 정의역 하한(on_mask 유도), 끝 출처 vds_axis -> item 7."""
    ctx = _diode_ctx(tmp_path, acc_f if which == "F" else acc_f2, "nmos")
    d = _no_root(ctx, _diode_theta(ctx, "nmos", 2.0))          # 근이 레일 위 -> 두 끝 h 같은 부호
    assert d["lo"] == _floor("nmos", which) and d["hi"] == 1.8
    assert "vds_axis" in d["bounds"] and d["item"] == 7


def test_floor_is_interval_hi_pmos_diode(tmp_path, acc_f):
    """pmos diode: vds = 1.8 − x ≥ 하한 1.0 -> 구간 hi = 0.8."""
    ctx = _diode_ctx(tmp_path, acc_f, "pmos")
    d = _no_root(ctx, _diode_theta(ctx, "pmos", 2.0))
    assert d["lo"] == 0.0 and d["hi"] == 1.8 - _floor("pmos", "F")
    assert "vds_axis" in d["bounds"] and d["item"] == 7


def test_root_below_floor_is_no_root(tmp_path, acc_f):
    """근(vds 0.6)이 pmos 하한 1.0 아래 -> 구간 밖 -> no_root_in_window(item 7, 유한 끝 |h| -> margin 있음)."""
    ctx = _diode_ctx(tmp_path, acc_f, "pmos")
    d = _no_root(ctx, _diode_theta(ctx, "pmos", 0.6))
    assert d["hi"] == 0.8 and d["item"] == 7


@pytest.mark.parametrize("kind,vgs1", [("nmos", 0.3), ("nmos", 0.6), ("pmos", 1.2)])
def test_root_above_floor_solved(tmp_path, acc_f, kind, vgs1):
    """하한 위의 근은 풀린다(r3 는 구간 끝 VDS = 0 의 lut_curve_undefined 로 실패하던 모양). 반복 수 = k_max(구간 폭, tol)."""
    ctx = _diode_ctx(tmp_path, acc_f, kind)
    snap = run_blocks(ctx, _diode_theta(ctx, kind, vgs1), upto="columns")
    V = node_voltages(snap)
    log = {e.nodes: e for e in snap.value("graph", DC_KEY, "dc_scc_log")}[("nb",)]
    want = vgs1 if kind == "nmos" else 1.8 - vgs1
    assert abs(V["nb"] - want) <= log.tol
    width = 1.8 - _floor(kind, "F")
    assert log.iterations == math.ceil(math.log2(width / log.tol))


def test_floor_cached_in_lut_memo(tmp_path, acc_f):
    """값은 LUT memo derived 영역 키 ("sizing_vds_floor", kind, w_key) 에 슬라이스당 1회."""
    ctx = _diode_ctx(tmp_path, acc_f, "nmos")
    run_blocks(ctx, _diode_theta(ctx, "nmos", 0.6), upto="columns")
    misses = dict(acc_f.memo.stats())["derived"].misses

    def not_cached():
        raise AssertionError("하한이 derived memo 에 없다")
    assert acc_f.memo.lookup("derived", "sizing_vds_floor", ("nmos", 100), not_cached) == _floor("nmos", "F")
    run_blocks(ctx, _diode_theta(ctx, "nmos", 0.45), upto="columns")
    assert dict(acc_f.memo.stats())["derived"].misses == misses


def test_no_fully_on_suffix_falls_back_to_vds_min(tmp_path, acc_f2):
    """끝 열까지 모두 켜진 열이 없으면 하한 = VDS 격자 최소(r3 그대로): pmos diode 구간 끝 vds = 0 이 꺼진 열이라 strict 1변수
    bisection 의 끝점 평가가 lut_curve_undefined -> lut_query_failed. (잘못된 '처음 켜진 열' 규칙이면 하한 0.25 로 풀린다.)"""
    ctx = _diode_ctx(tmp_path, acc_f2, "pmos")
    with pytest.raises(SealViolationError) as ei:
        run_blocks(ctx, _diode_theta(ctx, "pmos", 0.6), upto="columns")
    d = detail(ei.value)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_curve_undefined"
    assert ei.value.record.devices == ("M1",)
    assert d["vds"] == 0.0


def test_interval_end_nextafter_inside_axis(tmp_path, acc_f):
    """gnd = 0.1 V: x_lo = (0.25 − a)/b 가 부동소수 반올림으로 vds = 0.24999999999999997(하한 밖, 꺼진 열과 보간)이 되는 구성.
    구간 끝은 축 안으로 nextafter 된다 -> 끝점 조회가 정의역 밖이 되지 않는다(근 풀림, no_root 의 lo 도 축 안)."""
    sup = {"vdd": 1.8, "gnd": 0.1}
    F = _floor("nmos", "F")
    a = 1.0 * (0.0 - 0.1)
    b = 1.0 * (1.0 - 0.1) - a
    x_naive = (F - a) / b
    assert 1.0 * (x_naive - 0.1) < F                           # 전제: 보정 없으면 축 밖
    ctx = _diode_ctx(tmp_path, acc_f, "nmos", supplies=sup)
    d = _no_root(ctx, _diode_theta(ctx, "nmos", 2.0))
    assert 1.0 * (d["lo"] - 0.1) >= F and d["lo"] > x_naive
    assert d["lo"] - x_naive <= 4 * math.ulp(x_naive)
    snap = run_blocks(ctx, _diode_theta(ctx, "nmos", 0.6), upto="columns")
    log = {e.nodes: e for e in snap.value("graph", DC_KEY, "dc_scc_log")}[("nb",)]
    assert abs(node_voltages(snap)["nb"] - 0.7) <= log.tol


@pytest.mark.parametrize("vout,ok", [(0.1, False), (0.24, False), (0.26, True), (0.5, True)])
def test_acyclic_writer_below_floor_is_strict_failure(tmp_path, acc_f, vout, ok):
    """비순환(strict) writer 의 VDS 가 하한 아래면 lut_curve_undefined 그대로 실패(일시 이탈 규칙은 반복 중에만)."""
    ctx = build_ctx(tmp_path, circuit_cs_res(bulk_m1="gnd"), acc_f)[2]
    i = 1e-5
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, max(vout, 0.25), 0.0),
          ("current", "R1"): i, ("resistance", "R1"): (1.8 - vout) / i}
    if ok:
        V = node_voltages(run_blocks(ctx, th, upto="columns"))
        assert abs(V["out"] - vout) <= 1e-12
        assert abs(V["in"] - r4_vgs_of("nmos", th[("ln_idu", "M1")], V["out"], 0.0)) <= 1e-9
    else:
        with pytest.raises(SealViolationError) as ei:
            run_blocks(ctx, th, upto="columns")
        d = detail(ei.value)
        assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_curve_undefined"
        assert d["device_query"] == "vgs_of_coordinate" and ei.value.record.devices == ("M1",)


def _cycle_ctx(tmp_path, acc, kind_a):
    """다변수 순환 SCC {x, y}: MA(kind_a) 가 gate x 를 쓰고(vgs_gate, drain = y -> y 에 의존), MB nmos (d = x, g = in, s = y,
    b = y) 가 y 를 쓴다(vgs_source, 1변수 -- drain x 에 의존). in = W4(창 = 레일). 이상 전류원 IX·IY 가 KCL 을 닫는다."""
    if kind_a == "pmos":
        net = [mos("MA", "pmos", "y", "x", "vdd", "vdd"), mos("MB", "nmos", "x", "in", "y", "y")]
        src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "y", "gnd")]
    else:
        net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
        src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    doc = topo("r4_cycle_%s" % kind_a, net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)
    ctx = build_ctx(tmp_path, doc, acc)[2]
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["x"].relation, w["x"].element) == ("vgs_gate", "MA")
    assert (w["y"].relation, w["y"].element) == ("vgs_source", "MB")
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [set(e.nodes) for e in cyc] == [{"x", "y"}]
    return ctx


def _cycle_theta(kind_a, vin, x, y, vgs_a=0.6, vgs_b=0.6):
    """해 (x, y) 가 정확히 나오는 θ: MA 는 vgs_a 를 VDS(MA) 에서, MB 는 vgs_b 를 VDS(MB) = x − y 에서 낸다."""
    vds_a = (1.8 - y) if kind_a == "pmos" else y
    return {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("current", "MA"): 1e-5, ("current", "MB"): 1e-5,
            ("ln_idu", "MA"): r4_ln_idu(kind_a, vgs_a, max(vds_a, 0.25), 0.0),
            ("ln_idu", "MB"): r4_ln_idu("nmos", vgs_b, x - y, 0.0), ("y", "input_common_mode"): vin / 1.8}


def test_cyclic_transient_below_floor_tolerated(tmp_path, acc_f):
    """[r4] 5.4: 반복 중(strict=False)에는 MOS writer 의 하한 아래 lut_curve_undefined 가 일시 이탈(현재 값 유지).
    MA pmos(하한 1.0)의 시작값 계산은 계약 5.4 2단계 'VDS = 레일 범위/2 = 0.9' 라 하한 아래 -> 거부하면 안 된다.
    수렴점: x = 1.8 − 0.6 = 1.2, y = vin − 0.6 = 0.5 (VDS(MA) = 1.3 ≥ 1.0, VDS(MB) = 0.7 ≥ 0.25 -> strict 검증도 통과)."""
    assert 0.9 < _floor("pmos", "F")                           # 전제: 2단계 시작 VDS 가 하한 아래
    ctx = _cycle_ctx(tmp_path, acc_f, "pmos")
    snap = run_blocks(ctx, _cycle_theta("pmos", 1.1, 1.2, 0.5), upto="columns")
    V = node_voltages(snap)
    log = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if set(e.nodes) == {"x", "y"}][0]
    assert abs(V["x"] - 1.2) <= log.tol and abs(V["y"] - 0.5) <= log.tol


@pytest.mark.parametrize("vin,ok", [(0.7, False), (0.75, False), (0.9, True)])
def test_cyclic_strict_recheck_below_floor_fails(tmp_path, acc_f, vin, ok):
    """MA nmos(하한 0.25)의 수렴점 VDS = V(y) = vin − 0.6 이 하한 아래(0.1·0.15)면 반복 중 일시 이탈이어도 수렴 뒤 strict 검증에서
    lut_curve_undefined 실패(투영이 최종값에 남지 않는다). 0.9 -> y = 0.3 ≥ 0.25 이면 풀린다."""
    ctx = _cycle_ctx(tmp_path, acc_f, "nmos")
    y = vin - 0.6
    th = _cycle_theta("nmos", vin, 0.6, y)
    if ok:
        V = node_voltages(run_blocks(ctx, th, upto="columns"))
        assert V["y"] >= _floor("nmos", "F") and abs(V["y"] - y) <= 0.01 and abs(V["x"] - 0.6) <= 0.01
    else:
        with pytest.raises(SealViolationError) as ei:
            run_blocks(ctx, th, upto="columns")
        d = detail(ei.value)
        assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_curve_undefined"
        assert ei.value.record.devices == ("MA",)
        assert d["vds"] < _floor("nmos", "F")
