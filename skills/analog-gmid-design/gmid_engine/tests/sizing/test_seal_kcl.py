"""봉인 3 `dc_seal_kcl(snapshot, resistances)` -- CONTRACT 6절: 레일 아닌 넷마다 |Σ from − Σ to|, MOS = idu_forward·W/L,
저항 = (V(from) − V(to))/R, 이상원 = dc_current; tol = 채널이 닿는 MOS 의 tol_v·dc_gm 최댓값(정의된 것; MOS 는 있는데
모두 None 이면 None), MOS 없는 넷은 n·eps·Σ|I|.
[U17 ①] tol_I 의 gm = 후보 자기 동작점의 `device.dc_gm`(= ID × 그 동작점 LUT gm/ID, 설계 40 v1.6 §3.7-3·§2.4.11). 옛 `dc_gm_bound`
(S2p·곡선 최대 상계)는 폐기. 손 test 의 gm 은 conftest `hand_dc_gm`(LUT 파일을 직접 읽은 gm/ID × ID)이다.

비고: DC 원소가 하나도 닿지 않는 넷(gate 만 있는 넷)을 행으로 세는지는 계약 문장으로 정해지지 않아(그 행은 0 ≤ 0 pass),
n_checked 는 원소가 닿는 넷만으로 비교한다(보고: 모호).
"""
import dataclasses

import pytest

from gmid_engine.sizing import dc_seal_kcl

from .conftest import (EPS, assert_item, build_ctx, hand_dc_gm, judge_expect, mos, node_voltages, rel_close,
                       resistances_of, seal_item, tamper, theta_a, theta_c, topo, toy_npz, two, with_tol)
from .conftest import kschema  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)


def rows_of(snap, resistances):
    V = node_voltages(snap)
    R = dict(resistances)
    ops = dict(snap.column("device", "dc_op"))
    cur = dict(snap.column("device", "dc_current"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    gmb = dict(snap.column("device", "dc_gm"))
    rails = {n for n, r in snap.column("node", "is_rail") if r}
    basis = snap.value("graph", "dc", "dc_current_basis")
    acc = {}
    for name, f, t in basis.ends:
        cls = snap.value("device", name, "element_class")
        if cls == "mos":
            i = ops[name].idu_forward * ops[name].W / ops[name].L
        elif snap.value("device", name, "kind") == "resistor":
            i = (V[f] - V[t]) / R[name]
        else:
            i = cur[name]
        for net, sgn in ((f, 1.0), (t, -1.0)):
            if net in rails:
                continue
            a = acc.setdefault(net, {"sum_from": 0.0, "sum_to": 0.0, "abs": [], "mos": []})
            if sgn > 0:
                a["sum_from"] += i
            else:
                a["sum_to"] += i
            a["abs"].append(abs(i))
            if cls == "mos":
                a["mos"].append(name)
    rows = []
    for net in sorted(acc):
        a = acc[net]
        if a["mos"]:
            d = [tolv[m] * gmb[m] for m in a["mos"] if tolv[m] is not None]
            tol = max(d) if d else None
        else:
            tol = len(a["abs"]) * EPS * sum(a["abs"])
        rows.append((net, abs(a["sum_from"] - a["sum_to"]), tol, tuple(sorted(set(a["mos"]))), (net,)))
    return rows


def run(snap, res=()):
    return seal_item(dc_seal_kcl(snap, tuple(res)), 3)


@pytest.mark.parametrize("which", ["C", "A"])
def test_pass(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    res = resistances_of(ctx, th)
    exp = judge_expect(rows_of(snap, res))
    assert exp["status"] == "pass"
    assert_item(run(snap, res), exp, 3, atol=1e-18)


def test_hand_tol_is_max_tolv_times_own_dc_gm(ctx_c, toy_lut_paths):
    """설계 40 §3.7-3: tol_I(out) = max(tol_V·gm) over out 에 채널이 닿는 MOS(M1·M2), gm = 자기 동작점 ID × LUT 파일 gm/ID(손계산)."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap)
    tolv = dict(snap.column("device", "dc_tol_v"))
    ops = dict(snap.column("device", "dc_op"))
    gm = {m: hand_dc_gm(lambda kind: toy_npz(toy_lut_paths[0], kind), ops[m]) for m in ("M1", "M2")}
    assert dict(item.detail)["worst"] == "out"
    assert rel_close(item.tol, max(tolv["M1"] * gm["M1"], tolv["M2"] * gm["M2"]), 1e-9)


def test_fail_mos_current_mismatch(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    op = dict(snap.column("device", "dc_op"))["M1"]
    bad = tamper(snap, "dc_widths", "device", "dc_op", {"M1": dataclasses.replace(op, idu_forward=op.idu_forward * 1e6)})
    exp = judge_expect(rows_of(bad, ()))
    assert exp["status"] == "fail" and exp["nodes"] == ("out",)
    assert_item(run(bad), exp, 3)
    # 손계산: |1e6·I − I| = 999999·1e-5 (tol_I = tol_V × 동작점 gm 보다 훨씬 큰 잔차)
    assert rel_close(run(bad).magnitude, 999999 * 1e-5, 1e-6)


def test_fail_wrong_resistance(ctx_a):
    ctx, th = ctx_a[2], theta_a()
    snap, _ = with_tol(ctx, th)
    res = (("R1", 1.0),)                    # 노드전압은 R = 9e4 로 풀었는데 봉인에 1 Ω -> 저항 전류 0.9 A
    exp = judge_expect(rows_of(snap, res))
    assert exp["status"] == "fail" and exp["nodes"] == ("out",)
    item = run(snap, res)
    assert_item(item, exp, 3)
    assert rel_close(item.magnitude, abs(0.9 / 1.0 - 1e-5), 1e-9)


def test_undefined_when_all_mos_tol_none(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None, "M2": None})
    exp = judge_expect(rows_of(s2, ()))
    assert exp["status"] == "undefined"
    assert_item(run(s2), exp, 3)


def test_one_mos_tol_none_uses_other(ctx_c, toy_lut_paths):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    item = run(s2)
    assert item.status == "pass"
    gm2 = hand_dc_gm(lambda kind: toy_npz(toy_lut_paths[0], kind), dict(snap.column("device", "dc_op"))["M2"])
    assert rel_close(item.tol, dict(s2.column("device", "dc_tol_v"))["M2"] * gm2, 1e-9)


def test_ideal_source_term(tmp_path, toy_access):
    """n 넷: I1·I2(고정) 가 들어오고 M1·M2 가 나간다. 이상원 항 = dc_current."""
    doc = topo("hand_two_src_kcl",
               [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "n"), two("I2", "current_source", "vdd", "n")],
               bias=["b2"])                                                                  # b2: M2 gate 에만
    from .conftest import Oracle
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5), ("I2", 2e-5)))[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("y", "n"): 0.5,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.0), ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.5, 0.9, 0.0)}
    from .conftest import free_currents
    th.update(free_currents(ctx, {"M1": 2e-5, "M2": 1e-5}))              # M1 + M2 = I1 + I2
    assert set(th) == set(kschema(ctx).components)
    snap, _ = with_tol(ctx, th)
    exp = judge_expect(rows_of(snap, ()))
    assert exp["status"] == "pass"
    assert_item(run(snap), exp, 3, atol=1e-18)
    bad = tamper(snap, "dc_currents", "device", "dc_current", {"I1": 1e3})
    exp = judge_expect(rows_of(bad, ()))
    assert exp["status"] == "fail" and exp["nodes"] == ("n",)
    assert_item(run(bad), exp, 3)
