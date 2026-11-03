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
from .conftest import run_of  # [XRUN-F1 card B C4] 블록 호출 = ctx 의 실행 두 객체
from .conftest import kfixed, kres, kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)

TOL = 1e-12


def assert_voltages(snap, ctx, theta):
    V_exp, win_exp, ln_exp = expected_columns(snap, theta, kfixed(ctx), kres(ctx))
    V = node_voltages(snap)
    assert set(V) == set(V_exp)
    for n in V_exp:
        assert abs(V[n] - V_exp[n]) <= TOL, (n, V[n], V_exp[n])
    # [IT-2b 갱신 -- 대조 대상 명시] `node.dc_window` 범위는 W4 뿌리 + 모든 입력 포트로 넓어졌다(design 41 4.7-2). `expected_columns` 는 W4 뿌리 창
    # (writer relation free_window)만 안다 -> 뿌리 항목으로 좁혀 이전과 같은 키 집합 등식·끝 값을 대조하고, 입력 포트 항목은 아래 test_it2b_k1_*·
    # test_it2b_k2_* 가 따로 본다.
    win_all = dict(snap.column("node", "dc_window"))
    roots = {n for n, w in dict(snap.column("node", "dc_writer")).items() if w.relation == "free_window"}
    win = {n: w for n, w in win_all.items() if n in roots}
    # 단언 둘로 나눈다(약화 해소): (1) 뿌리 키 집합 등식, (2) 뿌리 밖 키는 모두 입력 포트(`node.port_direction` == "input" -- 피검 출력이 아닌 입력 필드).
    # 측정 실패(A6 a)면 뿌리 아닌 포트 항목이 없으므로 '뿌리 ∪ 입력 포트' 전체 등식은 일반 불변식이 아니다(design 41 4.7-3 4).
    input_ports = {n for n, d in dict(snap.column("node", "port_direction")).items() if d == "input"}
    assert set(win_all) & roots == set(win_exp)
    assert set(win_all) - roots <= input_ports
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
    assert kres(ctx) == (("R1", 6e4),)
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
    assert set(dict(th)) == set(kschema(ctx).components)
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
    comps = dict.fromkeys(kschema(ctx).components)
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
    assert kfixed(ctx) == (("s1", 0.3),)
    y = 0.4
    vout = 0.3 + y * 1.5
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M5"): 2e-6,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.5, vout - 0.3, 0.3),
          ("ln_idu", "M2"): Oracle.ln_idu("pmos", 0.7, 1.8 - vout, 0.0),
          ("ln_idu", "M5"): Oracle.ln_idu("nmos", 0.65, 0.3, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M5": 1e-5}))   # KCL: 세 소자 같은 전류
    assert set(th) == set(kschema(ctx).components)
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
    for kind, key in kschema(ctx).components:
        if kind != "current":
            th[(kind, key)] = {"L": 1e-6, "y": 0.5, "ln_idu": Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}[kind]
    # KCL x: MA + MC = MB (MB 는 pmos, x 로 들어옴)
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 2e-5, "MC": 1e-5}))
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_columns(snap, items, kfixed(ctx), kres(ctx), ctx.lut, **run_of(ctx))
    d = detail(ei.value)
    assert d["reason"] == "empty_window" and d["item"] == 7
    assert d["node"] == "x" and d["lo"] == 1.8 and d["hi"] == 0.0
    assert "constraints" in d
    assert ei.value.record.devices == () and ei.value.record.margin is None


def _lut_fail(ctx, th):
    snap = run_blocks(ctx, th, upto="lengths")
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    with pytest.raises(SealViolationError) as ei:
        dc_columns(snap, items, kfixed(ctx), kres(ctx), ctx.lut, **run_of(ctx))
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
    assert set(th) == set(kschema(ctx).components)
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
    for k, key in kschema(ctx).components:
        if k == "y":
            th[(k, key)] = 0.7
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
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
        dc_columns(snap, items, kfixed(ctx), kres(ctx), ctx.lut, **run_of(ctx))
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
    assert set(th) == set(kschema(ctx).components)
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


def _cycle_ctx(tmp_path, acc, kind_a, vin):
    """다변수 순환 SCC {x, y}: MA(kind_a) 가 gate x 를 쓰고(vgs_gate, drain = y -> y 에 의존), MB nmos (d = x, g = in, s = y,
    b = y) 가 y 를 쓴다(vgs_source, 1변수 -- drain x 에 의존). 이상 전류원 IX·IY 가 KCL 을 닫는다.
    [U4 갱신] in 은 **입력 DC 선언**(`input_dc_v = vin`, writer input_dc). 옛 판은 in 을 입력 DC 미선언 W4(창 = 레일 범위,
    V(in) = y·1.8)로 두었으나, 사용자 결정 J-E(설계 41 §4.6 '입력 DC 정책' SP-2 (c), 40 §11 'J 추가 범위' U4, 확인 행 D-J5)로
    입력 DC 대기 회로의 y_icm 범위는 레일이 아니라 입력 포화 창이 되었다 -- 이 test 들이 겨냥하는 규칙(5.4 [r4] 반복 중 일시
    이탈·strict 재검증)은 V(in) 값과 무관하므로 J-E 의 '선언 입력 DC 유지'(같은 절) 경로로 V(in) 을 그대로 고정한다."""
    if kind_a == "pmos":
        net = [mos("MA", "pmos", "y", "x", "vdd", "vdd"), mos("MB", "nmos", "x", "in", "y", "y")]
        src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "y", "gnd")]
    else:
        net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y")]
        src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    doc = topo("r4_cycle_%s" % kind_a, net, {"in": ("input", "x"), "y": ("output", "y")}, sources=src)
    ctx = build_ctx(tmp_path, doc, acc, input_dc_v=vin)[2]
    assert dict(ctx.base.column("node", "dc_writer"))["in"].relation == "input_dc"
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
            ("ln_idu", "MB"): r4_ln_idu("nmos", vgs_b, x - y, 0.0)}           # [U4] in = 선언 입력 DC -> y 성분 없음


def test_cyclic_transient_below_floor_tolerated(tmp_path, acc_f):
    """[r4] 5.4: 반복 중(strict=False)에는 MOS writer 의 하한 아래 lut_curve_undefined 가 일시 이탈(현재 값 유지).
    MA pmos(하한 1.0)의 시작값 계산은 계약 5.4 2단계 'VDS = 레일 범위/2 = 0.9' 라 하한 아래 -> 거부하면 안 된다.
    수렴점: x = 1.8 − 0.6 = 1.2, y = vin − 0.6 = 0.5 (VDS(MA) = 1.3 ≥ 1.0, VDS(MB) = 0.7 ≥ 0.25 -> strict 검증도 통과)."""
    assert 0.9 < _floor("pmos", "F")                           # 전제: 2단계 시작 VDS 가 하한 아래
    ctx = _cycle_ctx(tmp_path, acc_f, "pmos", 1.1)
    th = _cycle_theta("pmos", 1.1, 1.2, 0.5)
    assert set(th) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    log = [e for e in snap.value("graph", DC_KEY, "dc_scc_log") if set(e.nodes) == {"x", "y"}][0]
    assert abs(V["x"] - 1.2) <= log.tol and abs(V["y"] - 0.5) <= log.tol


@pytest.mark.parametrize("vin,ok", [(0.7, False), (0.75, False), (0.9, True)])
def test_cyclic_strict_recheck_below_floor_fails(tmp_path, acc_f, vin, ok):
    """MA nmos(하한 0.25)의 수렴점 VDS = V(y) = vin − 0.6 이 하한 아래(0.1·0.15)면 반복 중 일시 이탈이어도 수렴 뒤 strict 검증에서
    lut_curve_undefined 실패(투영이 최종값에 남지 않는다). 0.9 -> y = 0.3 ≥ 0.25 이면 풀린다."""
    ctx = _cycle_ctx(tmp_path, acc_f, "nmos", vin)
    y = vin - 0.6
    th = _cycle_theta("nmos", vin, 0.6, y)
    assert set(th) == set(kschema(ctx).components)
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
    assert set(kschema(ctx).components) == set(_tolrep_theta())
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
          ("ln_idu", "M3"): r4_ln_idu("pmos", 0.7, 1.8 - vout, 0.0), ("y", "vin"): y1, ("y", "vout"): y2}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
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


# ---------------------------------------------------------------- [U17 ①-d] d/s 반대 선언 -> 봉인 7 거부
# 사용자 결정 2026-10-13 "1은 권고"(라)(오케스트레이터 전달): "topology d/s 표기 = 물리 방향 선언 ... 사이징 결과(writer 계획·θ 스키마·ties)는 선언 방향을
# 따름. 틀린 선언은 봉인 7(VDS−VDsat ≥ tol)이 거부."
# 손 유도: 회로 C(M1 nmos (out, in, gnd) + M2 pmos (out, pb, vdd))의 두 MOS 를 모두 d/s 반대로 선언한다 -- M1 d=gnd·s=out, M2 d=vdd·s=out.
# (하나만 뒤집으면 KCL 이 I_M1 = −I_M2 < 0 을 요구해 전류 원뿔에서 먼저 거부되고, 둘 다 뒤집어야 선언 방향 전류가 양수로 맞는다.)
# 선언 방향의 VDS: M1 = V(gnd) − V(out) = −V(out), M2(pmos VSD) = V(out) − V(vdd). out 은 레일 창 [0, 1.8] V 안이므로 M1 의 VDS ≤ 0 이고
# VDS ≥ VDsat + tol > 0 을 만족하는 V(out) 이 창 안에 없다 -> 봉인 7(item 7) 거부, 소자 M1, 노드 out(M1 의 vgs_source 로 쓰는 노드), 원인 축 VDS.
# 대조: 바르게 선언한 같은 회로·같은 θ 값은 봉인 7 을 통과한다(test_seal_saturation R4_SCENARIOS (0.5, 0.6, 0.7) 과 같은 동작점).

def _reversed_c():
    return topo("hand_cs_pload_rev", [mos("M1", "nmos", "gnd", "in", "out"), mos("M2", "pmos", "vdd", "pb", "out")],
                {"in": ("input", "single_ended_input"), "out": ("output", "single_ended_output")}, bias=["pb"])


def _theta_for(ctx, v1=0.6, v2=0.6, y=0.5):
    from .conftest import r4_ln_idu
    th = {}
    for t, k in kschema(ctx).components:
        if t == "L":
            th[(t, k)] = 1e-6
        elif t == "current":
            th[(t, k)] = 1e-5
        elif t == "y":
            th[(t, k)] = y
        elif t == "ln_idu":
            th[(t, k)] = r4_ln_idu("nmos" if k == "M1" else "pmos", v1 if k == "M1" else v2, 0.5, 0.0)
    return th


def test_reversed_ds_declaration_rejected_by_seal7(tmp_path, r4_access):
    from .conftest import with_tol
    ctx = build_ctx(tmp_path, _reversed_c(), r4_access)[2]
    writer = dict(ctx.base.column("node", "dc_writer"))["out"]
    assert (writer.relation, writer.element) == ("vgs_source", "M1")     # 전제: out = V(in) − VGS(M1), 선언 source 기준
    with pytest.raises(SealViolationError) as e:
        with_tol(ctx, _theta_for(ctx))
    d = detail(e.value)
    assert d["item"] == 7
    assert tuple(e.value.record.devices) == ("M1",)
    assert d["node"] == "out"
    assert "vds_axis" in d["bounds"]                                         # 원인 = 선언 방향 VDS 축(VDS ≥ 0 이 되는 V(out) ≤ 0)
    assert d["hi"] <= 0.0                                                    # 창 상한: −V(out) ≥ 0 -> V(out) ≤ 0(손 유도 VDS 부호)


def test_correct_ds_declaration_same_point_passes_seal7(tmp_path, r4_access):
    from gmid_engine.sizing import dc_seal_saturation
    from .conftest import circuit_cs_pmos_load, seal_item, theta_r4c, with_tol
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), r4_access)[2]
    snap, _ = with_tol(ctx, theta_r4c(y=0.5, v1=0.6, v2=0.7))
    assert seal_item(dc_seal_saturation(snap, (), ctx.lut, **run_of(ctx)), 7).status == "pass"


# ===========================================================================
# [card IT-2b] 커널 창 `node.dc_window`(모든 입력 포트 + W4 뿌리) -- design 41 v1.12.8 4.7-2·4.7-3, 4.7-7 K1·K2·P(b)·L12(b)
# 칸 `Window(lo, hi, constraints, input_status=None, tol_v=None, status_detail=())`.
# 입력 포트 항목: 입력 DC 선언 포트 = 같은 x 로 함께 움직이는 묶음의 이동량 창(4.7-3 3), 미선언 뿌리 = A6 되풀이 창, 뿌리 아닌 포트 = 뿌리 창 끝을 같은 해의
# 감도로 옮긴 [min, max] ∩ 레일(4.7-3 2), F 성분 미선언 포트 = 창 정의 불능(`f_component_undeclared`, lo·hi None).
# 기대값은 모두 toy 연결의 손계산과 이 test 안의 독립 풀이(이분법)에서 만든다. 피검 함수(`dc_columns` 출력)로 기대값을 만들지 않는다.
# ===========================================================================
from .conftest import circuit_cs_pmos_load, r4_vdsat_at, r4_tol_vdsat  # noqa: E402


def _bisect(f, lo, hi, n=200):
    flo = f(lo)
    assert (flo > 0) != (f(hi) > 0), "근을 끼지 않은 구간"
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _window_of(snap):
    return dict(snap.column("node", "dc_window"))


# ---- 미선언 입력 포트 둘 toy: follower 순환(MA·MB) + 포트 z 를 y 위 소스 팔로어(MC)로 -------------------------------------------
# MA nmos (y, x, gnd) 가 x 를, MB nmos (x, in, y, b = y) 가 y 를 쓴다(입력 포트 in = 뿌리), MC nmos (vdd, z, y, b = gnd) 가 z = V(y) + VGS(MC) 를 쓴다
# (입력 포트 z = 뿌리 아닌 포트, 같은 성분 {in, y, z} 에 레일 없음).
def _f2_doc():
    net = [mos("MA", "nmos", "y", "x", "gnd", "gnd"), mos("MB", "nmos", "x", "in", "y", "y"),
           mos("MC", "nmos", "vdd", "z", "y", "gnd")]
    src = [two("IX", "current_source", "vdd", "x"), two("IY", "current_source", "vdd", "y")]
    return topo("it2b_f2", net, {"in": ("input", "x"), "z": ("input", "x"), "y": ("output", "y")}, sources=src)


F2_TA = r4_ln_idu("nmos", 0.9, 0.3, 0.0)
F2_TB = r4_ln_idu("nmos", 0.3, 0.3, 0.0)
F2_TC = r4_ln_idu("nmos", 0.5, 1.2, 0.6)


def _f2_theta(ctx, y):
    th = {("L", "MA"): 1e-6, ("L", "MB"): 1e-6, ("L", "MC"): 1e-6, ("ln_idu", "MA"): F2_TA, ("ln_idu", "MB"): F2_TB,
          ("ln_idu", "MC"): F2_TC, ("y", "in"): y}
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 1e-5, "MC": 1e-5, "IX": 1e-5, "IY": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def _f2_solve(vin):
    """독립 풀이(이분법): x = VGS_A(vds = y), y = V(in) − VGS_B(vds = x − y, vsb = 0), z = y + VGS_C(vds = 1.8 − y, vsb = y). -> (x, y, z)"""
    def g(y):
        x = r4_vgs_of("nmos", F2_TA, y, 0.0)
        return vin - r4_vgs_of("nmos", F2_TB, x - y, 0.0) - y
    y = _bisect(g, 1e-9, 1.2)
    x = r4_vgs_of("nmos", F2_TA, y, 0.0)
    return x, y, y + r4_vgs_of("nmos", F2_TC, 1.8 - y, y)


def test_it2b_k1_declared_input_port_has_measured_window(tmp_path, r4_access):
    """oracle 대조: (손) K1 입력 DC 선언 toy(회로 C, in = 0.7 V 선언). 입력 포트 in 의 창 항목이 있고 input_status == "measured".
    out 은 W4 뿌리(y 로 고정, 레일 사이)라 in 이 움직여도 out·VDS(M1)·VSD(M2)가 변하지 않는다 -> 어느 행도 x 에 기울지 않아 창 = 레일 [0, 1.8].
    뿌리 아닌 포트·선언 포트의 constraints 는 0, 입력 포트가 아닌 W4 뿌리 out 의 input_status 는 None."""
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), r4_access, input_dc_v=0.7)[2]
    snap = run_blocks(ctx, theta_r4c(), upto="columns")
    win = _window_of(snap)
    assert set(win) == {"in", "out"}
    w = win["in"]
    assert w.input_status == "measured"
    assert (w.lo, w.hi, w.constraints) == (0.0, 1.8, 0)
    assert w.tol_v is not None and w.tol_v > 0
    assert win["out"].input_status is None


def test_it2b_k1_undeclared_input_ports_both_have_windows(tmp_path, r4_access):
    """oracle 대조: (손) K1 미선언 2입력 toy(in = 뿌리, z = 같은 성분의 뿌리 아닌 포트). 두 포트 항목이 모두 있고 둘 다 "measured"
    (뿌리 아닌 포트의 input_status 는 뿌리 항목과 같다, 4.7-3 2). base 는 뿌리 항목뿐이다."""
    ctx = build_ctx(tmp_path, _f2_doc(), r4_access)[2]
    assert dict(ctx.base.column("node", "dc_writer"))["in"].relation == "free_window"          # 전제: in = W4 뿌리
    assert dict(ctx.base.column("node", "dc_writer"))["z"].relation == "vgs_gate"              # 전제: z = 트리 경로 포트
    win = _window_of(run_blocks(ctx, _f2_theta(ctx, 0.5), upto="columns"))
    assert set(win) == {"in", "z"}
    assert win["in"].input_status == "measured" and win["z"].input_status == "measured"
    assert win["z"].constraints == 0


def test_it2b_k1_unmeasurable_root_is_unmeasured_with_order_window(tmp_path, toy_access):
    """oracle 대조: (손) K1 창을 잴 수 없는 toy(VDSAT 열 없는 LUT). source follower M1 nmos (vdd, in, out) + M2 nmos (out, vb, gnd):
    in = 입력 DC 미선언 뿌리, 게이트에만 닿아 순서 창 = 레일 [0, 1.8]. 측정 못 함 -> input_status "unmeasured" 이고 창은 순서 창 그대로
    (세 metric 정의 불능은 IT-2d 몫)."""
    doc = topo("it2b_sf", [mos("M1", "nmos", "vdd", "in", "out"), mos("M2", "nmos", "out", "vb", "gnd")],
               {"in": ("input", "x"), "out": ("output", "y")}, bias=["vb"])
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.5),
          ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.55, 0.6, 0.0)}
    th.update({(k, key): 0.7 for k, key in kschema(ctx).components if k == "y"})
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5}))
    win = _window_of(run_blocks(ctx, th, upto="columns"))
    assert set(win) == {"in"}
    assert win["in"].input_status == "unmeasured"
    assert (win["in"].lo, win["in"].hi) == (0.0, 1.8)


def test_it2b_k2_non_root_port_window_is_root_ends_moved_by_the_same_solution_sensitivity(tmp_path, r4_access):
    """oracle 대조: (손)+독립 풀이 K2. 뿌리 아닌 포트 z 의 창 = 뿌리 창 끝 [lo_x, hi_x] 를 같은 해의 감도 s_z = dV_z/dx 로 옮긴 두 끝 전압의 [min, max].
    기대 끝 = 뿌리 in 을 lo_x·hi_x 로 고정한 독립 풀이(toy 닫힌 식 이분법)의 V(z) 의 [min, max] -- 감도 옮김은 '추정'(선형)이라 비선형 오차를 허용한다
    (이 toy 에서 V(z) 곡률 오차 ≈ 4e-4 V, 허용 2e-3 V; 창 폭 0.28 V). 감도가 양인 toy 라 z(lo_x) < z(hi_x), lo ≤ hi."""
    ctx = build_ctx(tmp_path, _f2_doc(), r4_access)[2]
    snap = run_blocks(ctx, _f2_theta(ctx, 0.5), upto="columns")
    V = node_voltages(snap)
    x, y, z = _f2_solve(V["in"])
    assert abs(V["z"] - z) <= 1e-6 and abs(V["y"] - y) <= 1e-6 and abs(V["x"] - x) <= 1e-6        # 전제: 독립 풀이가 이 toy 의 해를 재현
    win = _window_of(snap)
    root, port = win["in"], win["z"]
    z_lo, z_hi = _f2_solve(root.lo)[2], _f2_solve(root.hi)[2]
    assert z_hi - z_lo > 0.1                                                                     # 전제: 감도가 분명한 양수
    assert port.lo <= port.hi
    assert abs(port.lo - min(z_lo, z_hi)) <= 2e-3 and abs(port.hi - max(z_lo, z_hi)) <= 2e-3


# ---- 입력 DC 둘 선언 toy (P(b)): 차동쌍 -------------------------------------------------------------------------------------
# M1 nmos (o1, ina, t), M2 nmos (o2, inb, t), 꼬리 M5 nmos (t, vb, gnd), 부하 저항 R1 (vdd, o1)·R2 (vdd, o2). bulk = gnd. 입력 DC 0.9 V 선언(두 입력 포트 모두).
# o1 = o2 = 1.8 − I·R(= 1.0 V, 저항 강하라 입력에 무관), t = V(in) − VGS(M_writer, vds = o − t, vsb = t) (1변수), M5 가 t 를 받친다.
def _dp_doc():
    return topo("it2b_dp", [mos("M1", "nmos", "o1", "ina", "t", "gnd"), mos("M2", "nmos", "o2", "inb", "t", "gnd"),
                            mos("M5", "nmos", "t", "vb", "gnd")],
                {"ina": ("input", "x"), "inb": ("input", "x"), "o1": ("output", "y")},
                passives=[two("R1", "resistor", "vdd", "o1"), two("R2", "resistor", "vdd", "o2")], bias=["vb"])


DP_R = 8e4
DP_I = 1e-5
DP_VO = 1.8 - DP_I * DP_R                                      # 1.0 V (저항 강하 손계산)
DP_TD = r4_ln_idu("nmos", 0.5, 0.6, 0.4)                        # 쌍 소자 writer 의 ln IDu(두 소자 같은 좌표)
DP_T5 = r4_ln_idu("nmos", 0.6, 0.4, 0.0)


def _dp_theta(ctx):
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M5"): 1e-6, ("ln_idu", "M5"): DP_T5,
          ("resistance", "R1"): DP_R, ("resistance", "R2"): DP_R}
    th.update({("ln_idu", m): DP_TD for t, m in kschema(ctx).components if t == "ln_idu" and m != "M5"})
    th.update(free_currents(ctx, {"M1": DP_I, "M2": DP_I, "M5": 2 * DP_I, "R1": DP_I, "R2": DP_I}))
    assert set(th) == set(kschema(ctx).components)
    return th


def _dp_t(vin):
    """독립 풀이: t = vin − VGS(TD; vds = DP_VO − t, vsb = t)."""
    return _bisect(lambda t: vin - r4_vgs_of("nmos", DP_TD, DP_VO - t, t) - t, 1e-9, vin - 1e-9)


def test_it2b_pb_declared_input_ports_share_one_shift_window(tmp_path, r4_access):
    """oracle 대조: (손) P(b) 입력 DC 둘 선언 toy -- 두 포트 창 끝의 차 = 선언 차(둘 다 0.9 V 선언 -> 0), 즉 같은 x 이동량 Δ 로 함께 움직인 하나의 창.
    포트별로 따로 훑으면 다른 포트가 서 있어 t 가 덜 움직여 끝이 달라진다(red). 손계산(독립 풀이로 t0 = t(0.9), 감도 s_t = dt/dV_in 은 중심 차분):
    행 M_d(o, t, +1): 여유 (o − t) − VDsat(vgs = 0.9 − t, vsb = t) − tol, 율 −s_t -> Δ ≤ 여유/s_t.  행 M5(t, gnd, +1): 여유 t − VDsat(vgs5, 0) − tol,
    율 +s_t -> Δ ≥ −여유/s_t. o 는 저항 강하라 x 에 무관(s_o = 0). 창 = [0.9 + Δlo, 0.9 + Δhi] ∩ 레일 [0, 1.8]."""
    ctx = build_ctx(tmp_path, _dp_doc(), r4_access, input_dc_v=0.9)[2]
    th = _dp_theta(ctx)
    snap = run_blocks(ctx, th, upto="columns")
    V = node_voltages(snap)
    t0 = _dp_t(0.9)
    assert abs(V["t"] - t0) <= 1e-5 and abs(V["o1"] - DP_VO) <= 1e-9                             # 전제: 독립 풀이가 이 toy 의 해를 재현
    h = 1e-5
    s_t = (_dp_t(0.9 + h) - _dp_t(0.9 - h)) / (2 * h)
    tol = r4_tol_vdsat("nmos")
    vgs_d = 0.9 - t0
    slack_d = (DP_VO - t0) - r4_vdsat_at("nmos", 1e-6, vgs_d, t0) - tol
    vgs5 = r4_vgs_of("nmos", DP_T5, t0, 0.0)
    slack_5 = t0 - r4_vdsat_at("nmos", 1e-6, vgs5, 0.0) - tol
    lo_e, hi_e = 0.9 - slack_5 / s_t, 0.9 + slack_d / s_t
    assert 0.0 < lo_e < 0.9 < hi_e < 1.8                                                         # 전제: 두 끝 모두 행에서 나온다(레일 아님)
    win = _window_of(snap)
    assert set(win) == {"ina", "inb"}
    for p in ("ina", "inb"):
        assert win[p].input_status == "measured" and win[p].constraints == 0
        assert abs(win[p].lo - lo_e) <= 1e-5 and abs(win[p].hi - hi_e) <= 1e-5, (p, win[p], lo_e, hi_e)
    assert abs(win["ina"].lo - win["inb"].lo) <= 1e-12 and abs(win["ina"].hi - win["inb"].hi) <= 1e-12     # 끝의 차 = 선언 차(0)


# ---------------------------------------------------------------------------------------------------------------------------
# P(a) 감도 음수 포트 toy (design 41 4.7-3 2·4.7-7 P (a)) -- 이름 없는 toy + VDS 의존이 가파른 LUT 픽스처(이 파일 안에서 만든다)
#
# 연결: 입력 포트 x(뿌리) -MA follower-> t, 저항 R (t -> d), t -MB follower-> u, MT (d = d, g = p, s = u) triode 선언, 둘째 입력 포트 p,
# 풀다운 MS (u, vs, gnd). 쓰기: t = x − VGS_A, u = t − VGS_B, d = t − I·R, p = u + VGS_T(vds = d − u) (p 는 vgs_gate, known u).
# 손 유도(전류 고정 writer 식): F = ∂VGS/∂VDS = −h′(VDS)/G′ (전류 고정, 이득의 역수 꼴), η = ∂VGS/∂VSB = KS/G′.
#   t -> u 엣지: s_u·(1 + |F_B| + η_B) = s_t, d: s_d = s_t (저항), u -> p 엣지(vgs_gate): s_p = s_u·(1 + |F_T| + η_T) − |F_T|·s_d.
#   s_p < 0 조건: |F_T| > (1 + η_T)/(η_B + |F_B|). r4 LUT 는 |F| ≤ 0.018 이라 이 조건이 불가능 -> VDS < 0.2 V 에서 ln ID 기울기가 가파른(deep triode) LUT 를 둔다.
# 픽스처 LUT: ln ID = ln I0 + B·VGS − CN·VGS²/2 + h(VDS) − KS·VS (+ VDSAT 열 = r4 식), h(VDS) = S1·min(VDS, D1) + S2·max(VDS − D1, 0).
# 격자 VDS 0.0125 V 간격(노드에서 기울기 GDS = ID·h′ 정확 -> 구간 선형 ln ID 가 정확). VS 항을 선형으로 두어 η 를 상수로 한다(곡률은 VGS 축 CN 이 준다).
# ---------------------------------------------------------------------------------------------------------------------------
import json as _json  # noqa: E402

import numpy as _np  # noqa: E402

from gmid_engine.lut import load_lut_set as _load_lut_set  # noqa: E402

from .conftest import (A as _A, B as _B, DEVICE_OF as _DEVICE_OF, I0 as _I0, R4_VDSAT as _R4_VDSAT, R4_VGS as _R4_VGS,  # noqa: E402
                       R4_VS as _R4_VS, SUFFIX as _SUFFIX, TOY_SPEC as _TOY_SPEC, W_M as _W_M, _sha as _file_sha)

NEG_CN, NEG_KS, NEG_S1, NEG_S2, NEG_D1 = 2.0, 2.0, 250.0, 0.1, 0.2
NEG_VDS = tuple(round(0.0125 * i, 10) for i in range(161))                 # 0 .. 2.0 V
NEG_I = 1e-5
NEG_R = 17935.0                       # t -> d 저항(Ω): VDS(MT) ≈ 0.1 V (뿌리 창 중앙에서 손으로 맞춘 입력 값, 기대값 아님)


NEG_QD = 20.0                       # 곡률 계수에 (1 + QD·VDS) 를 곱해 tol_V 셀이 VDS 에 따라 달라지게 한다(해마다 tolerance 가 다른 toy -- L12 (a) tol_v 판정)
NEG_QV, NEG_VS_KINK = 0.005, 1.6   # VS > 1.6 V 에서만 ln ID 에 −QV·(VS − 1.6)² (동작 범위 밖): LUT 허용오차 tol_V 가 극소(1e-17)가 되어
                                    # A6 되풀이가 수렴 판정을 못 하는 일을 막는 곡률(구간 선형 ln ID 의 LOO 오차가 tol_V 를 정의한다)


def _neg_h(d):
    return NEG_S1 * min(d, NEG_D1) + NEG_S2 * max(d - NEG_D1, 0.0)


def _neg_slope(d):
    return NEG_S1 if d < NEG_D1 else NEG_S2


def _neg_ln_idu(vgs, vds, vsb):
    return math.log(_I0["nmos"]) + _B * vgs - 0.5 * NEG_CN * vgs * vgs + _neg_h(vds) - NEG_KS * vsb


def _neg_vgs_of(ln_idu, vds, vsb):
    r = ln_idu - math.log(_I0["nmos"]) - _neg_h(vds) + NEG_KS * vsb
    return (_B - math.sqrt(_B * _B - 2.0 * NEG_CN * r)) / NEG_CN


def _write_neg_lut(root):
    root.mkdir(parents=True, exist_ok=True)
    g_l, g_g, g_d, g_s = (_np.asarray(g, dtype=float) for g in (R4_L, _R4_VGS, NEG_VDS, _R4_VS))
    lg, g, s = g_l[:, None, None, None], g_g[None, :, None, None], g_s[None, None, None, :]
    h_d = _np.vectorize(_neg_h)(g_d)[None, None, :, None]
    s_d = _np.vectorize(_neg_slope)(g_d)[None, None, :, None]
    entries = []
    for kind in ("nmos", "pmos"):
        idc = (_W_M / lg) * _I0[kind] * _np.exp(_B * g - 0.5 * NEG_CN * g * g + h_d - NEG_KS * s
                                                       - NEG_QV * (1.0 + NEG_QD * g_d[None, None, :, None])
                                                       * _np.maximum(s - NEG_VS_KINK, 0.0) ** 2)
        c0, c1, c2, cs, cl = _R4_VDSAT[kind]
        il = _np.arange(len(g_l), dtype=float)[:, None, None, None]
        arr = {"W": _np.float64(_W_M), "L": g_l, "VGS": g_g, "VDS": g_d, "VS": g_s, "ID": idc, "GM": idc * (_B - NEG_CN * g),
               "GDS": idc * s_d, "VTH": _np.full(idc.shape, 0.4), "meta_json": _np.str_('{"model_files_sha256": {}}'),
               "corner": _np.str_("tt"), "temp_c": _np.float64(27.0),
               "VDSAT": (c0 + c1 * g + c2 * g * g + cs * s + cl * il) + _np.zeros(idc.shape)}
        path = root / ("neg_%s.npz" % kind)
        _np.savez(path, **arr)
        entries.append({"device": _DEVICE_OF[kind], "file": path.name, "sha256": _file_sha(path)})
    (root / "manifest.json").write_text(_json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    shape = (len(g_l), len(g_g), len(g_d), len(g_s))
    cap = {"L": g_l, "VGS": g_g, "VDS": g_d, "VS": g_s, "w_ref_m": _np.float64(_W_M), "corner": _np.str_("tt"),
           "temp_c": _np.float64(27.0)}
    for kind in ("nmos", "pmos"):
        cap["CGG" + _SUFFIX[kind]] = _np.full(shape, 1e-15)
        cap["CGD" + _SUFFIX[kind]] = _np.full(shape, 2e-16)
    _np.savez(root / "cap.npz", **cap)
    return _load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), _TOY_SPEC)


def _neg_doc():
    net = [mos("MA", "nmos", "vdd", "x", "t", "gnd"), mos("MB", "nmos", "vdd", "t", "u", "gnd"),
           mos("MT", "nmos", "d", "p", "u", "gnd"), mos("MS", "nmos", "u", "vs", "gnd")]
    return topo("it2b_neg", net, {"x": ("input", "x"), "p": ("input", "x"), "u": ("output", "y")},
                passives=[two("R", "resistor", "t", "d")], bias=["vs"])


# θ 좌표: 소자 MA·MB 는 VGS 0.25 V, MT 는 VGS 0.8 V(VDS 0.1 V), MS 는 VGS 0.45 V 가 나오는 ln IDu(입력 값). 근사 동작점 t0 = 0.65, u0 = 0.4.
NEG_LN = {"MA": _neg_ln_idu(0.25, 1.8 - 0.65, 0.65), "MB": _neg_ln_idu(0.25, 1.8 - 0.4, 0.4),
          "MT": _neg_ln_idu(0.8, 0.1, 0.4), "MS": _neg_ln_idu(0.45, 0.4, 0.0)}


def _neg_solve(x):
    """독립 풀이(이분법): t = x − VGS_A(vds = 1.8 − t, vsb = t), u = t − VGS_B(vds = 1.8 − u, vsb = u), d = t − I·R, p = u + VGS_T(vds = d − u, vsb = u)."""
    t = _bisect(lambda v: x - _neg_vgs_of(NEG_LN["MA"], 1.8 - v, v) - v, 1e-6, x - 1e-6)
    u = _bisect(lambda v: t - _neg_vgs_of(NEG_LN["MB"], 1.8 - v, v) - v, 1e-6, t - 1e-6)
    d = t - NEG_I * NEG_R
    return t, u, d, u + _neg_vgs_of(NEG_LN["MT"], d - u, u)


def _columns_with_declared(ctx, theta):
    """`dc_columns` 를 커널과 같은 호출로 부른다: 5번째 extras = 선언 영역 소자 tuple(비어 있지 않을 때만, sizing CONTRACT 5.4). conftest `run_blocks` 는
    이 extras 를 주지 않으므로 triode 선언 toy 는 이 함수로 부른다."""
    from gmid_engine.sizing import dc_columns, dc_currents, dc_lengths
    run = dict(donors=ctx.donors, counters=ctx.counters)
    th = dict(theta)
    snap = dc_currents(ctx.base, tuple(sorted((k, v) for (t, k), v in th.items() if t == "current")), **run)
    snap = dc_lengths(snap, tuple(sorted((k, v) for (t, k), v in th.items() if t == "L")), **run)
    items = tuple(sorted(((t, k), v) for (t, k), v in th.items() if t in ("ln_idu", "resistance", "y")))
    extras = (kfixed(ctx), kres(ctx), ctx.lut)
    if ctx.inputs.linear_devices:
        extras += (tuple(ctx.inputs.linear_devices),)
    return dc_columns(snap, items, *extras, **run)


def test_it2b_pa_negative_sensitivity_port_window_is_min_max_of_the_two_end_voltages(tmp_path):
    """oracle 대조: (손)+독립 풀이 P (a). 경로 위 triode 선언 소자 MT(gds/gm 큼)가 있으면 비F 성분에서도 s_p < 0 이 된다.
    손 유도: |F_B| = 0.1/G′_B, η_B = KS/G′_B, |F_T| = S1/G′_T, η_T = KS/G′_T (G′ = B − CN·VGS: MB 0.25 V -> 19.5, MT 0.8 V -> 18.4)
    => η_B + |F_B| ≈ 0.108, |F_T| ≈ 13.6 > (1 + η_T)/(η_B + |F_B|) ≈ 10.3 이므로 s_p = s_u(1 + |F_T| + η_T) − |F_T|·s_t < 0 (s_u = s_t/(1 + |F_B| + η_B)).
    포트 창 = 뿌리 끝 [lo_x, hi_x] 를 같은 해의 감도로 옮긴 두 끝 전압의 [min, max]: 뿌리를 두 끝으로 고정한 독립 풀이의 V(p) 로
    기대 끝을 만든다(감도 옮김은 선형 '추정' -- 이 toy 에서 끝 오차 ≈ 0.02 V, 허용 0.06 V; 두 끝 전압 차 ≈ 0.33 V).
    감도 음수라 뿌리 아래 끝이 포트 위 끝이 된다: 옛 식 V_p + s_p·(끝 − x_k) 를 정렬 없이 쓰면 lo > hi(red)."""
    acc = new_access(_write_neg_lut(tmp_path / "neg_lut"))
    (tmp_path / "ctx").mkdir()
    ctx = build_ctx(tmp_path / "ctx", _neg_doc(), acc, linear_devices=("MT",))[2]
    writers = dict(ctx.base.column("node", "dc_writer"))
    assert writers["x"].relation == "free_window" and writers["p"].relation == "vgs_gate"        # 전제: x = 뿌리, p = 트리 경로 포트
    th = {("L", m): 1e-6 for m in ("MA", "MB", "MS", "MT")}
    th.update({("ln_idu", m): NEG_LN[m] for m in ("MA", "MB", "MS", "MT")})
    th.update({("resistance", "R"): NEG_R, ("y", "x"): 0.5})
    th.update(free_currents(ctx, {"MA": NEG_I, "MB": NEG_I, "MT": NEG_I, "MS": 2 * NEG_I, "R": NEG_I}))
    assert set(th) == set(kschema(ctx).components)
    snap = _columns_with_declared(ctx, th)
    V = node_voltages(snap)
    win = _window_of(snap)
    root = win["x"]
    # --- 전제: 독립 풀이가 이 toy 의 해를 재현하고, 부등식 조건이 손계산으로 성립하며, 음수 감도다
    t, u, d, p = _neg_solve(V["x"])
    assert max(abs(V["t"] - t), abs(V["u"] - u), abs(V["d"] - d), abs(V["p"] - p)) <= 2e-3
    g_b, g_t = _B - NEG_CN * 0.25, _B - NEG_CN * 0.8
    f_t, eta_t, f_b, eta_b = NEG_S1 / g_t, NEG_KS / g_t, 0.1 / g_b, NEG_KS / g_b
    assert f_t > (1 + eta_t) / (eta_b + f_b)                                  # 손 유도 조건 (≈ 13.6 > 10.3)
    assert 0.0 < d - u < NEG_D1                                               # MT 의 VDS 가 가파른 구간 안
    h_x = 1e-5
    s_p = (_neg_solve(V["x"] + h_x)[3] - _neg_solve(V["x"] - h_x)[3]) / (2 * h_x)
    assert s_p < -0.1                                                         # 전제: dV_p/dx 음수 (≈ −0.30)
    p_at_lo, p_at_hi = _neg_solve(root.lo)[3], _neg_solve(root.hi)[3]
    assert p_at_lo - p_at_hi > 0.2                                            # 뿌리 아래 끝에서 p 가 더 높다
    assert 0.0 < p_at_hi < p_at_lo < 1.8                                      # 레일 교집합이 끝을 자르지 않는다
    # --- 관측: 입력 포트 p 의 창
    port = win["p"]
    assert port.input_status == "measured"
    assert port.lo <= port.hi
    assert abs(port.lo - p_at_hi) <= 0.06 and abs(port.hi - p_at_lo) <= 0.06, (port, p_at_hi, p_at_lo)


# ---------------------------------------------------------------------------------------------------------------------------
# L12 (a) 커널 되풀이 k_max 소진 -> 뿌리 `unsettled` (design 41 4.7-7 L12 (a), A6 c) -- 주입 지점 `gmid_engine.sizing.block_columns.k_max` 하나만
# (monkeypatch 허용 지점, 상한 1). toy = 위 P(a) toy(입력 포트 x = 뿌리).
# ---------------------------------------------------------------------------------------------------------------------------
def _neg_ctx(tmp_path):
    acc = new_access(_write_neg_lut(tmp_path / "neg_lut"))
    (tmp_path / "ctx").mkdir()
    return acc, build_ctx(tmp_path / "ctx", _neg_doc(), acc, linear_devices=("MT",))[2]


def _neg_theta(ctx, y):
    th = {("L", m): 1e-6 for m in ("MA", "MB", "MS", "MT")}
    th.update({("ln_idu", m): NEG_LN[m] for m in ("MA", "MB", "MS", "MT")})
    th.update({("resistance", "R"): NEG_R, ("y", "x"): y})
    th.update(free_currents(ctx, {"MA": NEG_I, "MB": NEG_I, "MT": NEG_I, "MS": 2 * NEG_I, "R": NEG_I}))
    return th


def test_it2b_l12a_k_max_exhausted_root_window_is_unsettled_and_y_range_kept(tmp_path, monkeypatch):
    """oracle 대조: (손) L12 (a) k_max 소진. 전제 단언: (1) 요청 y = 0.3 ≠ 1/2 (2) 주입 없이 y = 1/2 풀이가 성공하고 되풀이가 수렴한 창 W* 는
    input_status "measured" (3) 주입 k_max = 1 이면 되풀이가 한 번에 끝나 창이 W* 와 다르고 그 차 > tol(이 LUT 의 id_equivalent 허용오차, 공개
    `tol_v_table` 의 셀 값 -- 엔진 실행 두 번의 비교이며 손계산이 아니다: 첫 회 창(손 선형 창 [0.688, 1.8])과 둘째 측정 창의 차는 hi 쪽 약 0.025 V).
    관측: 소진된 평가의 뿌리 항목 input_status == "unsettled" 이고 창은 y 범위 그대로 쓰인다 -- V(x) = lo + y·(hi − lo), 창은 레일 순서 창 [0, 1.8] 안.
    base 는 Window 에 input_status 칸이 없다(AttributeError)."""
    acc, ctx = _neg_ctx(tmp_path)
    y_req = 0.3
    assert y_req != 0.5
    from gmid_engine.sizing import dc_widths
    star_snap = _columns_with_declared(ctx, _neg_theta(ctx, 0.5))                           # (2) y = 1/2 풀이 성공
    star = _window_of(star_snap)["x"]
    # 기준 tol = 수렴 해의 소자 tol_V 셀 최솟값 -- 공개 표 API `tol_v_table(...).at(L, VDS, "id_equivalent")` 로 직접 읽는다(엔진 `tol_v` 출력을 쓰지 않는다;
    # 해의 L·VDS 는 `dc_op` graph 필드). 이 LUT 는 VDS 에 따라 셀이 달라 한 점의 표 값을 쓰지 않는다.
    ops = dict(dc_widths(star_snap, ctx.lut, donors=ctx.donors, counters=ctx.counters).column("device", "dc_op"))
    tol = min(tol_v_table(acc.memo, op.kind, op.w_key).at(op.L, op.vds, "id_equivalent") for op in ops.values())
    assert tol is not None and 0.0 < tol < 1e-3
    # 주입 값은 블록 입력 버전에 들지 않아 같은 ctx·같은 θ 로 다시 부르면 graph reuse 로 앞 결과가 돌아온다 -> 실행마다 새 ctx(새 실행)를 쓴다.
    (tmp_path / "two").mkdir()
    _, ctx_two = _neg_ctx(tmp_path / "two")
    monkeypatch.setattr("gmid_engine.sizing.block_columns.k_max", lambda width, tol_: 2)
    w_two = _window_of(_columns_with_declared(ctx_two, _neg_theta(ctx_two, y_req)))["x"]
    monkeypatch.setattr("gmid_engine.sizing.block_columns.k_max", lambda width, tol_: 1)
    snap = _columns_with_declared(ctx, _neg_theta(ctx, y_req))
    w = _window_of(snap)["x"]
    # (3) 소진 분기에 도달 -- 공개 관측만(회차 수 자체는 엔진 출력으로만 알 수 있어 쓰지 않는다): 같은 toy·같은 θ 로 상한만 바꿔 새 실행에서 돌린 결과,
    # 상한 2 는 수렴("measured")하고 상한 1 만 미수렴("unsettled")이다 -- 창 차 > tol 전제로는 소진을 증명하지 못한다(감사 반례: 창 차가 커도 소진이 없을 수 있음,
    # 그리고 이 toy 에서는 창 차가 tol 보다 작아도 상한 1 에서 소진된다). 상한이 상태를 가른다는 것이 소진 도달의 직접 증거다.
    assert w_two.input_status == "measured" and star.input_status == "measured"
    assert w.input_status == "unsettled"
    assert w.tol_v is not None                            # A6 b(tol 미정)로 생긴 unsettled 가 아니라 k_max 소진(A6 c)이다
    assert 0.0 <= w.lo < w.hi <= 1.8
    assert abs(node_voltages(snap)["x"] - (w.lo + y_req * (w.hi - w.lo))) <= 1e-9


# ---------------------------------------------------------------------------------------------------------------------------
# D (S4-나) -- triode 행 영 교차 = 창 끝, region_rows 종류 집합·EO-1 무관 부재 단언 (정적 AST, docstring·주석 제외), 어휘 부재 (d)
# `_helpers_dc_solve` 모듈은 IT-2d 에서 생긴다(IT-2b 에는 없다) -- `region_rows` 는 block_columns 안 비공개 이름이라 공개 진입점 `dc_columns` 로 본다.
# ---------------------------------------------------------------------------------------------------------------------------
import ast as _ast  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

import gmid_engine as _gmid_engine  # noqa: E402

from gmid_engine.lut import tol_v_table  # noqa: E402

ENGINE = _Path(_gmid_engine.__file__).resolve().parent
TRI_VIN, TRI_VGS1, TRI_VGS3 = 0.8, 0.8, 0.6      # 입력 DC 선언 값, M1(triode 선언)·M3(풀다운) 의 VGS -- 손으로 정한 입력


def _tri_doc():
    """M1 nmos (d = out, g = vb, s = in, b = gnd) triode 선언 소자(source 가 입력 포트 in), M2 pmos 부하, M3 nmos (in, vc, gnd) 가 in 의 전류 경로를 닫는다.
    V(out) = lo + y·(hi − lo), lo = V(in)(M1 의 소스 쪽 이웃), hi = V(vdd)."""
    return topo("it2b_triode", [mos("M1", "nmos", "out", "vb", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"),
                                mos("M3", "nmos", "in", "vc", "gnd")],
                {"in": ("input", "x"), "out": ("output", "y")}, bias=["vb", "pb", "vc"])


def _tri_theta(ctx, y, vsg2):
    out = TRI_VIN + y * (1.8 - TRI_VIN)
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("L", "M3"): 1e-6,
          ("ln_idu", "M1"): r4_ln_idu("nmos", TRI_VGS1, out - TRI_VIN, TRI_VIN),
          ("ln_idu", "M2"): r4_ln_idu("pmos", vsg2, 1.8 - out, 0.0),
          ("ln_idu", "M3"): r4_ln_idu("nmos", TRI_VGS3, TRI_VIN, 0.0), ("y", "out"): y}
    th.update(free_currents(ctx, {"M1": 1e-5, "M2": 1e-5, "M3": 1e-5}))
    assert set(th) == set(kschema(ctx).components)
    return th


def test_it2b_d_triode_row_zero_crossing_is_the_window_end(tmp_path, r4_access):
    """oracle 대조: (손) D (a) -- `triode` 선언 소자가 훑기 중 포화로 가는 toy: 그 점이 창 끝. 행 `(d, s, −부호, VDsat − VDS − tol_VDsat, "triode")` 의 영 교차.
    y = 0.4: V(out) = 0.8 + 0.4·(1.8 − 0.8) = 1.2 (뿌리 식), 소스 in 이 움직이면 s_out = 1 − y = 0.6.
    M1(triode): VDS = out − in = 0.4, VDsat = r4_vdsat_at(vgs 0.8, vsb 0.8); 여유 = VDsat − VDS − tol, 율 = −(s_out − s_in) = y -> Δ ≥ −여유/y (아래 끝).
    M2(pmos 포화): VSD = 1.8 − out = 0.6; 여유 = VSD − VDsat(vsg 0.4, vsb 0) − tol_p, 율 = −s_out -> Δ ≤ 여유/(1 − y) (위 끝).
    M3(nmos 포화, d = in, s = gnd): VDS = in; 여유 = in − VDsat(vgs 0.6, 0) − tol, 율 +1 -> Δ ≥ −여유 (더 느슨).
    전제 단언: 세 소자 모두 선언 영역 안(M1 은 동작점에서 triode). base 는 선언 소자 행이 없어 M1 아래 끝을 놓친다(red)."""
    y, vsg2 = 0.4, 0.4
    (tmp_path / "t").mkdir()
    ctx = build_ctx(tmp_path / "t", _tri_doc(), r4_access, input_dc_v=TRI_VIN, linear_devices=("M1",))[2]
    snap = _columns_with_declared(ctx, _tri_theta(ctx, y, vsg2))
    V = node_voltages(snap)
    out = TRI_VIN + y * (1.8 - TRI_VIN)
    assert abs(V["out"] - out) <= 1e-9 and V["in"] == TRI_VIN                                   # 전제: 뿌리 식 손계산
    tol_n, tol_p = r4_tol_vdsat("nmos"), r4_tol_vdsat("pmos")
    slack1 = r4_vdsat_at("nmos", 1e-6, TRI_VGS1, TRI_VIN) - (out - TRI_VIN) - tol_n
    slack2 = (1.8 - out) - r4_vdsat_at("pmos", 1e-6, vsg2, 0.0) - tol_p
    slack3 = TRI_VIN - r4_vdsat_at("nmos", 1e-6, TRI_VGS3, 0.0) - tol_n
    assert slack1 > 0 and slack2 > 0 and slack3 > 0                                              # 전제: 세 소자 모두 선언 영역 안
    dlo = max(-slack1 / y, -slack3)
    dhi = slack2 / (1.0 - y)
    assert dlo == -slack1 / y                                                                    # 전제: 아래 끝은 triode 행에서 나온다
    w = _window_of(snap)["in"]
    assert w.input_status == "measured"
    assert abs(w.lo - (TRI_VIN + dlo)) <= 1e-9 and abs(w.hi - (TRI_VIN + dhi)) <= 1e-9, (w, TRI_VIN + dlo, TRI_VIN + dhi)


def _docstring_ids(tree):
    ids = set()
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.Module, _ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, _ast.Expr) and isinstance(first.value, _ast.Constant) and isinstance(first.value.value, str):
                ids.add(id(first.value))
    return ids


def _identifiers_and_strings(tree):
    """식별자(이름·속성·정의·인자·키워드·import 이름)와 문자열 상수(docstring 제외)만 -- 주석은 AST 에 없다."""
    skip = _docstring_ids(tree)
    names, strings = set(), set()
    for node in _ast.walk(tree):
        if isinstance(node, _ast.Name):
            names.add(node.id)
        elif isinstance(node, _ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, _ast.arg):
            names.add(node.arg)
        elif isinstance(node, _ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, _ast.alias):
            names.update(part for part in ((node.asname or node.name).split(".")) if part)
        elif isinstance(node, _ast.ImportFrom) and node.module:
            names.update(node.module.split("."))
        elif isinstance(node, _ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            strings.add(node.value)
    return names, strings


def test_it2b_d_no_operating_point_mismatch_vocabulary_in_engine_sources():
    """oracle 대조: (독립) D (d), 계획 v6.33 (9)(d), 사용자 결정 O-98·O-101. (S4-나) 에서 동작점 불일치 묶음(상태 `op_mismatch`·`Window.status_detail`·metric
    code)은 EO-1 card 몫이다 -- 죽은 코드를 두지 않는다. 비test 엔진 소스(tests 폴더 제외 모든 .py)를 AST 로 읽어 식별자와 문자열 상수(docstring·주석 제외)에
    `op_mismatch`·`status_detail`·`input_window_operating_point_mismatch`·`INPUT_STATUS_OP_MISMATCH`·`CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH` 가 0 이다."""
    words = ("op_mismatch", "status_detail", "input_window_operating_point_mismatch", "INPUT_STATUS_OP_MISMATCH",
             "CODE_INPUT_WINDOW_OPERATING_POINT_MISMATCH")
    hits = []
    for path in ENGINE.rglob("*.py"):
        if "tests" in path.relative_to(ENGINE).parts:
            continue
        names, strings = _identifiers_and_strings(_ast.parse(path.read_text(encoding="utf-8")))
        for word in words:
            if word in names or any(word in s for s in strings):
                hits.append((str(path.relative_to(ENGINE)), word))
    assert hits == [], hits


# ---------------------------------------------------------------------------------------------------------------------------
# L12 (a) tol 미정 -> 뿌리 `unsettled` (design 41 4.7-3 1 A6 b: '`tolerance` 가 미정이면 창을 한 번만 적용하고 되풀이 수렴 판정 없이 푼다')
# 도달 조건: 비순환 쓰기 계획(순환 SCC·자기참조 없음), 해의 모든 MOS 에서 tol_VDsat 정의(열 출처 = 기준 LUT), id_equivalent tol_V 셀은 전부 미정.
# 픽스처: 슬라이스에 VDSAT 열 없음 + 기준 LUT(cap)에 VDSAT 열, 슬라이스 VDS = 0 열 끔, 격자 VGS 2점·VDS 3점(0 포함)·VS 2점, L 앵커만.
# 회로(이름 없는 공통 게이트 꼴): M1 nmos (out, vb, in, gnd), RL (vdd, out), IS (in, gnd 전류 싱크); in = 입력 W4 뿌리, out = resistor_drop.
# ---------------------------------------------------------------------------------------------------------------------------
A6B_GRIDS = (R4_L, (0.2, 1.2), (0.0, 0.3, 1.8), (0.0, 1.8))        # 축소 격자 표현용 test 입력(엔진 상수 아님)


def _a6b_doc():
    return topo("it2b_a6b", [mos("M1", "nmos", "out", "vb", "in", "gnd")], {"in": ("input", "x"), "out": ("output", "y")},
                passives=[two("RL", "resistor", "vdd", "out")], sources=[two("IS", "current_source", "in", "gnd")], bias=["vb"])


def _a6b_access(tmp_path, slice_vdsat, cap_vdsat):
    from .conftest import write_r4_lut
    return new_access(write_r4_lut(tmp_path / "lut", vdsat=slice_vdsat, off_cols={"nmos": 1, "pmos": 1}, grids=A6B_GRIDS,
                                   cap_vdsat=cap_vdsat))


def _a6b_window(tmp_path, slice_vdsat, cap_vdsat, check_structure=False):
    acc = _a6b_access(tmp_path, slice_vdsat, cap_vdsat)
    (tmp_path / "ctx").mkdir()
    ctx = build_ctx(tmp_path / "ctx", _a6b_doc(), acc)[2]
    if check_structure:                                           # 전제: 순환 SCC 0·자기참조 0
        assert not any(e.cyclic for e in ctx.base.value("graph", DC_KEY, "dc_scc_order"))
        assert not any(v for _, v in ctx.base.column("device", "dc_self_referential"))
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): r4_ln_idu("nmos", 0.4, 0.6, 0.6), ("resistance", "RL"): 6e4}
    th.update(free_currents(ctx, {"M1": 1e-5, "RL": 1e-5, "IS": 1e-5}))
    th.update({(k, key): 0.5 for k, key in kschema(ctx).components if k == "y"})
    assert set(th) == set(kschema(ctx).components)
    snap = run_blocks(ctx, th, upto="columns")
    return acc, snap


def test_it2b_l12a_tol_undefined_root_window_is_unsettled_and_y_range_kept(tmp_path):
    """oracle 대조: (손) L12 (a) tol 미정. 전제 단언(공개 표 API): (1) 슬라이스 id_equivalent tol_V 셀이 전부 None (2) tol_VDsat 가 정의되고 출처가 기준 LUT (3) 쓰기
    계획이 비순환(순환 SCC 0·자기참조 0). 관측: 뿌리 in 의 input_status == "unsettled", tol_v is None(되풀이 수렴 판정 없음), 창은 한 번 잰 창이고 레일 안이며
    V(in) = lo + y·(hi − lo) (y = 1/2). 대조군: 기준 LUT 에도 VDSAT 가 없으면(출처 열 없음) 또는 슬라이스에 VDSAT 가 있으면(출처 = 슬라이스라 두 표가 함께 None)
    창을 잴 수 없어 "unmeasured"(A6 a). base 는 Window 에 input_status 칸이 없다(AttributeError)."""
    from gmid_engine.lut import tol_vdsat_table
    acc, snap = _a6b_window(tmp_path / "a", slice_vdsat=(), cap_vdsat=("nmos",), check_structure=True)
    tv = tol_v_table(acc.memo, "nmos", 100)
    td = tol_vdsat_table(acc.memo, "nmos", 100)
    for vds in (0.1, 0.3, 1.0, 1.7):
        assert tv.at(1e-6, vds, "id_equivalent") is None, vds                                   # 전제 (1)
        assert td.at(1e-6, vds) is not None, vds                                                # 전제 (2) 정의됨
    assert "cap" in str(td.origin), td.origin                                                   # 전제 (2) 출처 = 기준 LUT(cap table)
    w = _window_of(snap)["in"]
    assert w.input_status == "unsettled"
    assert w.tol_v is None
    assert 0.0 <= w.lo < w.hi <= 1.8
    assert abs(node_voltages(snap)["in"] - (w.lo + 0.5 * (w.hi - w.lo))) <= 1e-9
    # 대조군 -- 창을 잴 수 없다
    _, snap_c = _a6b_window(tmp_path / "c", slice_vdsat=(), cap_vdsat=())
    assert _window_of(snap_c)["in"].input_status == "unmeasured"
    _, snap_d = _a6b_window(tmp_path / "d", slice_vdsat=("nmos", "pmos"), cap_vdsat=())
    assert _window_of(snap_d)["in"].input_status == "unmeasured"


def test_it2b_l12a_window_tol_v_is_the_tolerance_of_the_last_measured_solution(tmp_path):
    """oracle 대조: (식) design 41 v1.12.10 4.7-2·4.7-3 5 -- `Window.tol_v` = 그 창을 잰 해의 tolerance(소자 tol_V 셀 최솟값), A6 되풀이 판정에도 매 측정 해의
    tol 을 쓴다(첫 해의 tol 하나를 모든 회차에 쓰면 red). 기대값 = 공개 표 API `tol_v_table(...).at(L, VDS, "id_equivalent")` 를 마지막 해의 소자마다 읽은
    최솟값(L·VDS = 그 해의 `dc_op` graph 필드). 피검 `tol_v` 로 기대값을 만들지 않는다.
    toy = P(a) toy + 곡률 계수가 (1 + QD·VDS) 라 tol_V 셀이 VDS 에 따라 달라지는 LUT. 전제 단언: (1) 첫 해(y = 1/2 해: 순서 창 [0, 1.8] 중앙 x = 0.9)의 tol 을
    같은 공개 표 API 와 독립 풀이(`_neg_solve(0.9)`)로 구해 마지막 해의 tol 과 다르다(이 전제가 없으면 test 가 공허하다). 이 toy 의 A6 되풀이는 앞 test
    (k_max 주입)가 보였듯 한 번 넘게 돈다. 마지막 해 = 최종 평가점(y = 1/2)은 창을 잰 마지막 해와 x 가 tol 안에서 같다 -- 허용 2e-6."""
    from gmid_engine.sizing import dc_widths
    acc, ctx = _neg_ctx(tmp_path)
    t, u, d, _ = _neg_solve(0.9)
    first_vds = (1.8 - t, 1.8 - u, d - u, u)                                   # MA, MB, MT, MS 의 VDS (손: 소자 단자 전압 차)
    tv = tol_v_table(acc.memo, "nmos", 100)
    tol_first = min(tv.at(1e-6, v, "id_equivalent") for v in first_vds)
    snap = _columns_with_declared(ctx, _neg_theta(ctx, 0.5))
    run = dict(donors=ctx.donors, counters=ctx.counters)
    ops = dict(dc_widths(snap, ctx.lut, **run).column("device", "dc_op"))
    tol_last = min(tol_v_table(acc.memo, op.kind, op.w_key).at(op.L, op.vds, "id_equivalent") for op in ops.values())
    assert tol_first is not None and tol_last is not None
    assert abs(tol_last - tol_first) > 0.1 * tol_last                          # 전제 (1) (상대: 이 LUT 의 tol 은 1e-5 규모)
    w = _window_of(snap)["x"]
    assert w.tol_v is not None
    assert abs(w.tol_v - tol_last) <= 0.02 * tol_last, (w.tol_v, tol_last, tol_first)
    assert abs(w.tol_v - tol_first) > 0.1 * tol_last
