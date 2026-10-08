"""`dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)` -- CONTRACT 5.4: 노드전압 정본.

기대값: conftest `expected_columns`(writer 식·창 규칙을 독립 구현, VGS 는 toy LUT 닫힌 식 `Oracle.vgs_of`)와 손계산.
순환 SCC 는 [r4] VDS 정의역 하한의 반복 중/strict 규칙 test 와 [r9] 성능 항목 1·6 절(끝 두 절)에서 쓴다(수렴값은 θ 를 해에서
거꾸로 만들어 손으로 안다).
"""
import collections
import math

import pytest

from gmid_engine.core import NonconvergentError, SealViolationError
from gmid_engine.lut import LutMemo
from gmid_engine.sizing import (DC_KEY, REASON_NO_ROOT, REASON_TOL_UNDEFINED, SCC_GAUSS_SEIDEL, LutAccess, PathValue, SccLog,
                                Window, dc_columns, size_and_seal)

from .conftest import (LAM, R4_L, W_KEYS, Oracle, build_ctx, circuit_cs_res, circuit_empty_window, detail,
                       expected_columns, free_currents, mos, new_access, node_voltages, r4_arrays, r4_ln_idu, r4_vds_floor,
                       r4_vgs_of, rel_close, run_blocks, theta_a, theta_c, theta_r4c, topo, two, write_r4_lut)

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
               {"in": ("input", "x"), "o1": ("output", "y")}, bias=["pb"])                 # pb: M3·M4 gate 에만
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
               {"in": ("input", "x"), "out": ("output", "y")}, bias=["pb", "vb5"])        # pb: M2 gate, vb5: M5 gate
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
               {"in": ("input", "x"), "out": ("output", "y")}, bias=["vb"])               # vb: M2 gate 에만
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


# ===========================================================================
# [r9] 성능 항목 1·6 (사용자 승인 2026-10-08) -- solve_self 입력 재사용, tol_V 셀 한 평가 안 재사용 (CONTRACT 5.4, 5.6c)
# ===========================================================================
# 관찰 방법(공개 주입점): lut `LutMemo.lookup(region, fn_name, key, compute)`(lut CONTRACT 2절)를 감싼 하위 클래스를 `LutAccess` 에
# 넣는다. 계약 5.6c 가 solve_self 저장 위치를 'LUT memo root 영역, 함수 이름 칸 solve_self' 로 정했으므로 그 조회의 compute 가
# 돌았는지(= 적중 아님)와 그 compute 안에서 일어난 VGS 역산 조회 수(= h 평가 수: 5.4 'VGS(좌표) = lut vgs_for_current_density'
# -- [U3] 계획 DEC-88 '쓰기 소자 VGS 는 vgs_for_current_density 로' 에 따라 옛 임시 우회 gm_id_for_target 을 대체, memo 함수 이름 칸
# `vgs_for_current_density`; h(x) = x − g(x) 한 번에 VGS 역산 한 번)를 센다. `tol_v_table` 조회 결과는 `.at` 호출을 세는 대리로 돌려준다(5.6c '한 평가 안에서
# 같은 (소자, VDS) 의 tol_v_cell 조회를 한 번만'; tol_v_cell = tol_v_table(kind, w_key).at(L, vds, "id_equivalent"), 6절 표 tol 행).

SOLVE_SELF = "solve_self"                    # CONTRACT 5.6c: memo root 영역 함수 이름 칸


class _AtCounter:
    """TolVTable 대리: `.at(...)` 인자를 (kind,) + 인자 로 기록하고 원래 표에 넘긴다."""

    def __init__(self, table, sink, kind):
        self._table, self._sink, self._kind = table, sink, kind

    def at(self, *args, **kw):
        self._sink.append((self._kind,) + tuple(args) + tuple(sorted(kw.items())))
        return self._table.at(*args, **kw)

    def __getattr__(self, name):
        return getattr(self._table, name)


class CountingMemo(LutMemo):
    """조회 기록: log = [(solve_self compute 안 깊이, region, fn_name)], at_calls = tol_v_table.at 인자."""

    def __init__(self, lut, n=4096):
        super().__init__(lut, point=n, curve=n, root=n)
        self.log, self.at_calls, self.self_computes, self._depth = [], [], 0, 0

    def lookup(self, region, fn_name, key, compute):
        self.log.append((self._depth, region, fn_name))
        if fn_name == SOLVE_SELF:
            def counted():
                self.self_computes += 1
                self._depth += 1
                try:
                    return compute()
                finally:
                    self._depth -= 1
            return super().lookup(region, fn_name, key, counted)
        value = super().lookup(region, fn_name, key, compute)
        if fn_name == "tol_v_table":
            return _AtCounter(value, self.at_calls, tuple(key)[0])
        return value

    def reset(self):
        self.log.clear()
        self.at_calls.clear()
        self.self_computes = 0

    def solve_self_lookups(self):
        return sum(1 for _, r, fn in self.log if (r, fn) == ("root", SOLVE_SELF))

    def h_evaluations(self):
        return sum(1 for d, r, fn in self.log if d > 0 and fn == "vgs_for_current_density")


def kmax_ref(width, tol):
    """CONTRACT 5.6 독립 구현."""
    return 1 if width <= tol else math.ceil(math.log2(width / tol))


def _counting_ctx(tmp_path, toy_lut, doc, **kw):
    memo = CountingMemo(toy_lut)
    return memo, build_ctx(tmp_path, doc, LutAccess(memo, W_KEYS), **kw)[2]


def _mirror_doc():
    """_mirror_ctx 와 같은 회로: M1 diode (nb, nb, gnd) = 1변수 노드 nb(SCC 0), M2 (out, nb, gnd), M3 pmos (out, in, vdd), I1 -> nb."""
    return topo("bc_mirror_r9",
                [mos("M1", "nmos", "nb", "nb", "gnd"), mos("M2", "nmos", "out", "nb", "gnd"),
                 mos("M3", "pmos", "out", "in", "vdd")],
                {"in": ("input", "x"), "out": ("output", "y")}, sources=[two("I1", "current_source", "vdd", "nb")])


def _nb_log(snap):
    (log,) = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if tuple(e.nodes) == ("nb",)]
    return log


def test_solve_self_identical_inputs_reused_zero_h_evaluations(tmp_path, toy_lut):
    """5.6c: 풀이는 (종류, L, ln IDu, 관계, known, 1차식 계수, 구간, tol) 만의 함수라 memo 에 저장 -- 적중하면 h 평가 0, 같은 결과.
    nb 의 입력과 무관한 θ 성분(y(out) -- out 은 nb 뒤 비순환 W4)만 바꿔 dc_columns 를 다시 계산하게 한다(FD 형제 평가 모양).
    oracle: (a) 근 = θ 를 만든 v* = 0.6(toy 닫힌 식), 오차 상계 = 기존 diode test 와 같은 tol/2·|g'|; (c) 첫 평가 결과와 비트 동일."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), element_values=(("I1", 1e-5),))
    th = _mirror_theta(ctx, 0.6)
    tol = Oracle.tol_v()
    memo.reset()
    s1 = run_blocks(ctx, th, upto="columns")
    h1 = memo.h_evaluations()
    assert memo.solve_self_lookups() == 1 and memo.self_computes == 1          # 1변수 노드 하나, 첫 호출은 계산
    K = kmax_ref(1.8, tol)
    assert 2 <= h1 <= 2 * K + 6 + 1                                            # 끝점 2 + 상계(5.6c) + 한 번 다듬기
    th2 = dict(th)
    th2[("y", "out")] = 0.7
    memo.reset()
    s2 = run_blocks(ctx, th2, upto="columns")
    V1, V2 = node_voltages(s1), node_voltages(s2)
    assert V2["out"] != V1["out"]                                              # 전제: dc_columns 가 실제로 다시 계산됐다
    assert memo.solve_self_lookups() == 1 and memo.self_computes == 0          # 적중
    assert memo.h_evaluations() == 0                                           # h 평가 0
    assert V2["nb"] == V1["nb"]                                                # 같은 결과(비트)
    assert _nb_log(s2) == _nb_log(s1)
    assert abs(V2["nb"] - 0.6) <= tol / 2 * (LAM / Oracle.gm_id(0.6)) + 1e-12


@pytest.mark.parametrize("change", ["ln_idu", "L"])
def test_solve_self_key_sensitive(tmp_path, toy_lut, change):
    """키에 든 입력(ln IDu, L -- 5.6c 키 목록)이 바뀌면 적중하지 않고 다시 푼다(h 평가 > 0). toy 는 IDu 가 L 무관이라 L 만 바꾸면
    근이 같다 -- 그래도 키가 다르므로 다시 계산해야 한다(실 LUT 는 L 마다 곡선이 다르다). oracle (a): 근 v*."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), element_values=(("I1", 1e-5),))
    th = _mirror_theta(ctx, 0.6)
    run_blocks(ctx, th, upto="columns")
    th2 = _mirror_theta(ctx, 0.62) if change == "ln_idu" else dict(th, **{})
    v_star = 0.62 if change == "ln_idu" else 0.6
    if change == "L":
        th2[("L", "M1")] = 2e-6
        th2[("L", "M2")] = 2e-6
    memo.reset()
    s2 = run_blocks(ctx, th2, upto="columns")
    assert memo.self_computes == 1 and memo.h_evaluations() >= 2
    tol = Oracle.tol_v()
    assert abs(node_voltages(s2)["nb"] - v_star) <= tol / 2 * (LAM / Oracle.gm_id(v_star)) + 1e-12


def test_solve_self_log_fields_unchanged(tmp_path, toy_lut):
    """5.4 [r9]: SccLog.iterations·k_max 는 변함없이 k_max(hi − lo, tol)(선언 상한 -- 실제 평가 수 아님), tol = 구간 가운데 writer
    tol_v_cell, method bisection. 구간 = 레일 [0, 1.8] ∩ vds(= x) ∈ [0, 1.8](toy 는 꺼진 열이 없어 하한 = 격자 최소). 적중 평가도 같다.
    oracle (a): toy tol_V 셀(Oracle.tol_v, 모든 셀 같은 값)과 손으로 정한 구간."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), element_values=(("I1", 1e-5),))
    tol = Oracle.tol_v()
    logs = []
    for y in (0.5, 0.3):
        th = _mirror_theta(ctx, 0.45)
        th[("y", "out")] = y
        logs.append(_nb_log(run_blocks(ctx, th, upto="columns")))
    for log in logs:
        assert log.tol == pytest.approx(tol, rel=1e-9)
        assert log.iterations == log.k_max == kmax_ref(1.8 - 0.0, log.tol)
        assert log.method == "bisection" and log.fallback is None
    assert logs[0] == logs[1]


def _no_root_case(tmp_path, toy_lut):
    """vdd = 0.5: diode nb 의 구간 = 레일 [0, 0.5] ∩ vds ∈ [0, 1.8] = [0, 0.5], 근 v* = 0.6 은 구간 밖 -> 두 끝 h 가 유한하고 음수."""
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _mirror_doc(), supplies={"vdd": 0.5, "gnd": 0.0},
                              element_values=(("I1", 1e-5),))
    th = _mirror_theta(ctx, 0.6)
    th[("ln_idu", "M3")] = Oracle.ln_idu("pmos", 0.7, 0.25, 0.0)
    order = ctx.base.value("graph", DC_KEY, "dc_scc_order")
    assert order[0].nodes == ("nb",)                                           # 전제: nb 를 먼저 푼다
    return memo, ctx, th


def test_no_root_strict_failure_and_not_cached_as_exception(tmp_path, toy_lut):
    """5.4: 끝 부호가 같으면 SealViolationError(devices (writer,), no_root_in_window, item = 구간 끝 출처에 vds_axis 가 있으면 7
    아니면 6, margin = 유한한 끝 |h| 최솟값/tol, detail node·lo·hi·h_lo·h_hi·bounds). 5.6c: 근 없음 (None, h_lo, h_hi) 도 저장되나
    예외는 저장하지 않는다(부르는 쪽이 만든다) -- 같은 입력 두 번째 평가는 h 평가 0 이고 같은 실패를 다시 낸다.
    oracle (a): h(x) = x − VGS(T, vds = x, vsb = 0)(toy 닫힌 식 Oracle.vgs_of), tol = Oracle.tol_v()."""
    memo, ctx, th = _no_root_case(tmp_path, toy_lut)
    T = th[("ln_idu", "M1")]
    tol = Oracle.tol_v()
    h_lo = 0.0 - Oracle.vgs_of("nmos", T, 0.0, 0.0)
    h_hi = 0.5 - Oracle.vgs_of("nmos", T, 0.5, 0.0)
    assert h_lo < 0 and h_hi < 0                                               # 전제: 같은 부호, 둘 다 유한
    recs = []
    for y in (0.5, 0.7):
        th2 = dict(th)
        th2[("y", "out")] = y
        memo.reset()
        with pytest.raises(SealViolationError) as ei:
            run_blocks(ctx, th2, upto="columns")
        recs.append((ei.value.record, memo.self_computes, memo.h_evaluations()))
    (r1, c1, n1), (r2, c2, n2) = recs
    d = dict(r1.detail)
    assert d["reason"] == REASON_NO_ROOT == "no_root_in_window"
    assert r1.devices == ("M1",) and d["node"] == "nb"
    assert d["lo"] == 0.0 and d["hi"] == 0.5
    assert abs(d["h_lo"] - h_lo) <= 1e-9 and abs(d["h_hi"] - h_hi) <= 1e-9
    assert r1.margin == pytest.approx(min(abs(h_lo), abs(h_hi)) / tol, rel=1e-9)
    assert set(d["bounds"]) <= {"rail", "vds_axis", "vs_axis"}
    assert d["item"] == (7 if "vds_axis" in d["bounds"] else 6)
    assert c1 == 1 and n1 >= 2                                                 # 첫 번째: 계산(끝점 h 2회 이상)
    assert c2 == 0 and n2 == 0                                                 # 두 번째: 저장된 (None, h_lo, h_hi) 적중
    assert r2 == r1                                                            # 같은 실패를 다시 만든다


def _tolrep_doc():
    """다변수 SCC {w, g}: MA nmos (d = vdd, g = g, s = gnd, b = w) 가 g 를 쓰고(vgs_gate, VDS = 1.8 고정 -- 반복 내내 같은 (소자, VDS)),
    MC nmos (d = g, g = gc, s = w) 가 w 를 쓴다(vgs_source 1변수), gc = 입력 DC 1.2 V. MD nmos (w, nb, gnd) 는 w 의 전류 경로."""
    return topo("r9_tol_reuse", [mos("MA", "nmos", "vdd", "g", "gnd", "w"), mos("MC", "nmos", "g", "gc", "w", "gnd"),
                                 mos("MD", "nmos", "w", "nb", "gnd")],
                {"gc": ("input", "x"), "w": ("output", "y")}, sources=[two("IG", "current_source", "vdd", "g")],
                bias=["nb"])                                                     # nb: MD gate 에만


def _tolrep_theta(w_star=0.3, g_star=0.7, la=2e-6):
    """해 (w*, g*) 가 정확히 나오는 θ(toy 닫힌 식): MA vgs = g*, vds 1.8, vsb = −w*; MC vgs = 1.2 − w*, vds = g* − w*, vsb = w*."""
    return {("L", "MA"): la, ("L", "MC"): 1e-6, ("L", "MD"): 1e-6,
            ("ln_idu", "MA"): Oracle.ln_idu("nmos", g_star, 1.8, -w_star),
            ("ln_idu", "MC"): Oracle.ln_idu("nmos", 1.2 - w_star, g_star - w_star, w_star),
            ("ln_idu", "MD"): Oracle.ln_idu("nmos", 0.6, w_star, 0.0), ("current", "MA"): 1e-5, ("current", "MD"): 1e-5}


def _tolrep_ctx(tmp_path, toy_lut):
    memo, ctx = _counting_ctx(tmp_path, toy_lut, _tolrep_doc(), input_dc_v=1.2)
    w = dict(ctx.base.column("node", "dc_writer"))
    assert (w["g"].relation, w["g"].element) == ("vgs_gate", "MA")             # 전제: 계획(입력)
    assert (w["w"].relation, w["w"].element) == ("vgs_source", "MC")
    cyc = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert [set(e.nodes) for e in cyc] == [{"w", "g"}]
    assert set(ctx.schema.components) == set(_tolrep_theta())
    return memo, ctx


def test_tol_v_cell_once_per_device_vds_within_one_evaluation(tmp_path, toy_lut):
    """5.6c 성능 항목 6: 한 평가(= 한 dc_columns) 안에서 같은 (소자, VDS) 의 tol_v_cell 조회는 한 번. MA 는 SCC writer MOS(5.4
    Gauss-Seidel 허용오차 = SCC writer MOS tol_v_cell 최솟값, 5.5 'tol = tolerance(current)' 반복마다)이고 VDS = 1.8 이 반복 내내
    같다 -> Gauss-Seidel 이 여러 바퀴 돌아도 (nmos, L 2 µm, 1.8) 조회는 1회. 소자마다 (kind, L) 를 달리해(MA 만 L 2 µm) .at 인자가
    소자를 가른다. oracle (a): 수렴값 = θ 를 만든 해 (0.3, 0.7), tol = toy tol_V 셀(모든 셀 같은 값)."""
    memo, ctx = _tolrep_ctx(tmp_path, toy_lut)
    memo.reset()
    snap = run_blocks(ctx, _tolrep_theta(), upto="columns")
    (log,) = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if set(e.nodes) == {"w", "g"}]
    assert log.method == SCC_GAUSS_SEIDEL and log.iterations >= 2              # 전제: 허용오차를 여러 번 물었다
    V = node_voltages(snap)
    assert abs(V["w"] - 0.3) <= log.tol and abs(V["g"] - 0.7) <= log.tol
    assert log.tol == pytest.approx(Oracle.tol_v(), rel=1e-9)
    calls = collections.Counter(memo.at_calls)
    ma_key = [k for k in calls if k[0] == "nmos" and k[1] == 2e-6 and k[2] == 1.8]
    assert len(ma_key) == 1 and calls[ma_key[0]] == 1                          # MA: (소자, VDS) 하나, 조회 1회
    assert max(calls.values()) == 1                                            # 어떤 (소자, VDS) 도 두 번 묻지 않는다


def test_tol_v_cell_values_identical_across_evaluations(tmp_path, toy_lut):
    """재사용이 값을 바꾸지 않는다: 같은 θ 의 두 평가(사이에 다른 θ 평가)에서 SccLog(tol 포함)·노드전압이 같다."""
    memo, ctx = _tolrep_ctx(tmp_path, toy_lut)
    a = run_blocks(ctx, _tolrep_theta(), upto="columns")
    run_blocks(ctx, _tolrep_theta(w_star=0.25, g_star=0.75), upto="columns")
    b = run_blocks(ctx, _tolrep_theta(), upto="columns")
    assert a.value("graph", DC_KEY, "dc_scc_log") == b.value("graph", DC_KEY, "dc_scc_log")
    assert node_voltages(a) == node_voltages(b)


# ---------------------------------------------------------------------------
# [r9 명시] Gauss-Seidel 수렴 전 SealViolationError 는 Newton 으로 넘기지 않고 그대로 (회귀: r8 까지 UnboundLocalError)
# ---------------------------------------------------------------------------
# 수렴 뒤(경우 2) Newton 인계는 test_scc_newton.py::test_case_two_seal_violation_kept_with_newton_cause 가 본다.

def _scc_s_doc():
    """W4–W4 선형 SCC {vin, vout}(1변수 노드 없음): M1 nmos (vin, nb1, gnd), M2 nmos (vout, nb2, vin), M3 pmos (vout, pb, vdd)."""
    return topo("r9_scc_s", [mos("M1", "nmos", "vin", "nb1", "gnd"), mos("M2", "nmos", "vout", "nb2", "vin"),
                             mos("M3", "pmos", "vout", "pb", "vdd")],
                {"vin": ("input", "single_ended_input"), "vout": ("output", "single_ended_output")},
                bias=["nb1", "nb2", "pb"])                                       # nb1: M1, nb2: M2, pb: M3 gate 에만


@pytest.fixture(scope="module")
def acc_two_point(tmp_path_factory):
    """CONTRACT 5.4 [r3] tol_v_undefined 최소 구성: 보간 축 VGS·VDS·VS 가 모두 2점(0, 1.8) -> 내부 격자점이 없어 모든 tol_V 셀 None."""
    return new_access(write_r4_lut(tmp_path_factory.mktemp("two_point"), grids=(R4_L, (0.0, 1.8), (0.0, 1.8), (0.0, 1.8))))


@pytest.mark.parametrize("y1,y2", [(0.6, 0.4), (0.98, 0.3)])
def test_tol_undefined_before_convergence_propagates(tmp_path, acc_two_point, y1, y2):
    """다변수 SCC 의 허용오차(5.4: SCC writer MOS 가 없으면 d·s·bulk 값이 있는 entry.devices 의 tol_v_cell 최솟값)가 모두 None ->
    Gauss-Seidel 이 수렴하기 전에 SealViolationError(tol_v_undefined, devices = SCC 소자, margin None) 그대로(Newton 인계 없음).
    y1·y2 = 빠른 수축(0.6, 0.4)·느린 수축(0.98, 0.3, Newton 경우 1 이 되는 θ). pytest.raises(SealViolationError) 라 UnboundLocalError
    는 이 test 의 실패가 된다. 공개 경로 두 개(dc_columns 직접, size_and_seal)."""
    ctx = build_ctx(tmp_path, _scc_s_doc(), acc_two_point)[2]
    (entry,) = [e for e in ctx.base.value("graph", DC_KEY, "dc_scc_order") if e.cyclic]
    assert set(entry.nodes) == {"vin", "vout"}
    vout = 1.8 * y2 / (1.0 - y1 * (1.0 - y2))
    vin = y1 * vout
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, vin, 0.0), ("ln_idu", "M2"): r4_ln_idu("nmos", 0.7, vout - vin, vin),
          ("ln_idu", "M3"): r4_ln_idu("pmos", 0.7, 1.8 - vout, 0.0), ("y", "input_common_mode"): y1, ("y", "vout"): y2}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(ctx.schema.components)
    for call in (lambda: run_blocks(ctx, th, upto="columns"), lambda: size_and_seal(ctx, th)):
        with pytest.raises(SealViolationError) as ei:
            call()
        e = ei.value
        assert dict(e.record.detail)["reason"] == REASON_TOL_UNDEFINED == "tol_v_undefined"
        assert e.record.devices == entry.devices and e.record.margin is None
        assert not isinstance(e.__cause__, NonconvergentError)                # Newton 으로 넘기지 않았다


def test_non_transient_lut_failure_before_convergence_propagates(tmp_path, toy_lut):
    """반복 중(strict=False)에도 일시 이탈로 보지 않는 LUT 실패(5.4: 일시 이탈 = axis/target 밖·하한 아래 curve_undefined 뿐) --
    다변수 SCC 의 MOS writer MA 의 L 이 앵커가 아님(1.5 µm, toy L 앵커 1·2 µm) -> 수렴 전 SealViolationError(lut_query_failed,
    lut_reason lut_l_not_anchor, devices (MA,)) 그대로. device_query 는 MA 를 처음 묻는 곳(VGS 역산 또는 허용오차 셀)."""
    memo, ctx = _tolrep_ctx(tmp_path, toy_lut)
    for call in (lambda: run_blocks(ctx, _tolrep_theta(la=1.5e-6), upto="columns"),
                 lambda: size_and_seal(ctx, _tolrep_theta(la=1.5e-6))):
        with pytest.raises(SealViolationError) as ei:
            call()
        e = ei.value
        d = dict(e.record.detail)
        assert d["reason"] == "lut_query_failed" and d["lut_reason"] == "lut_l_not_anchor"
        assert d["device_query"] in ("vgs_of_coordinate", "tol_v_cell")
        assert e.record.devices == ("MA",)
        assert not isinstance(e.__cause__, NonconvergentError)
