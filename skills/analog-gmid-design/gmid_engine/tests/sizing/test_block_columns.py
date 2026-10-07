"""`dc_columns(snapshot, theta_items, fixed_values, resistor_values, lut)` -- CONTRACT 5.4: 노드전압 정본.

기대값: conftest `expected_columns`(writer 식·창 규칙을 독립 구현, VGS 는 toy LUT 닫힌 식 `Oracle.vgs_of`)와 손계산.
이 파일은 순환 SCC 가 없는 회로만 쓴다(순환 SCC 의 고정점 풀이는 fixed_point 변경 대상이라 이번 판 밖).
"""
import math

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, PathValue, SccLog, Window, dc_columns

from .conftest import (Oracle, build_ctx, circuit_cs_res, circuit_empty_window, detail, expected_columns, mos,
                       node_voltages, rel_close, run_blocks, theta_a, theta_c, topo, two)

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
          ("current", "M2"): 1e-6, ("y", "out"): 0.4}
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
          ("ln_idu", "M5"): Oracle.ln_idu("nmos", 0.65, 0.3, 0.0),
          ("current", "M5"): 1e-5, ("y", "out"): y}     # 손 RREF: 열 (M1, M2, M5) -> pivot M1·M2, free M5
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
        th[(kind, key)] = {"L": 1e-6, "current": 1e-5, "y": 0.5, "ln_idu": Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}[kind]
    # 손 RREF: x 행 MA(+1) − MB(+1 to) + MC(+1) -> pivot MA = MB − MC, free MB·MC
    assert {k for t, k in th if t == "current"} == {"MB", "MC"}
    th[("current", "MB")] = 2e-5
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


def test_vdsat_not_in_window(ctx_c):
    """창은 인접 전도 소자 반대 단자 전압만으로 정해진다(VDsat 여유 없음): y = 0 -> out 이 정확히 0 V."""
    th = theta_c(y=0.0, x1=Oracle.ln_idu("nmos", 0.6, 0.0, 0.0), x2=Oracle.ln_idu("pmos", 0.7, 1.8, 0.0))
    snap = run_blocks(ctx_c[2], th, upto="columns")
    assert node_voltages(snap)["out"] == 0.0
