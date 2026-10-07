"""`size_and_seal(ctx, theta, parent=None) -> DcEvaluation` -- CONTRACT 7절(API·재사용 계약), 8절(실패 규약), 9절(결정론).

재사용은 core 블록 계수(`stats()`)로 잰다. 기대값은 계약 7절 문장(같은 θ·parent -> computes 0·reuses 12, 한 성분 섭동 ->
지정 블록만 다시)이다. 9회로 §10 숫자는 쓰지 않는다.
"""
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

from gmid_engine.core import (CANDIDATE_FAILURE_CLASSES, InfeasibleTargetError, NonconvergentError,
                              SealViolationError, StructureUnresolvedError)
from gmid_engine import sizing as S
from gmid_engine.sizing import DcEvaluation, check_theta, size_and_seal

from .conftest import (HERE, Oracle, SKILL_DIR, build_ctx, circuit_cs_res, circuit_empty_window, detail, free_currents, mos,
                       theta_a, theta_c, topo, two)

EVAL12 = (S.dc_currents, S.dc_lengths, S.dc_columns, S.dc_widths, S.dc_tolerances, S.dc_seal_node_conflict,
          S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_saturation, S.dc_seal_kvl_branch,
          S.dc_seal_report)
PLAN5 = (S.dc_rails, S.dc_struct_colour, S.dc_current_basis, S.dc_writer_plan, S.dc_scc_order, S.dc_theta_schema)


def reset():
    for b in EVAL12 + PLAN5:
        b.reset_stats()


def stats():
    return {b.name: b.stats() for b in EVAL12 + PLAN5}


def computes():
    return {n: s.computes for n, s in stats().items()}


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def test_returns_evaluation(ctx_c):
    ev = size_and_seal(ctx_c[2], theta_c())
    assert isinstance(ev, DcEvaluation)
    assert ev.snapshot.writers == S.S2_WRITERS
    assert ev.sealed is None and ev.report.status == "undefined"


def test_theta_object_equivalent(ctx_c):
    ctx = ctx_c[2]
    a = size_and_seal(ctx, theta_c())
    b = size_and_seal(ctx, check_theta(ctx.schema, theta_c()))
    assert a.snapshot.fp == b.snapshot.fp


def test_type_error_ctx(ctx_c):
    with pytest.raises(TypeError):
        size_and_seal(ctx_c[2].base, theta_c())


def test_bad_theta_is_value_error(ctx_c):
    th = theta_c()
    del th[("y", "out")]
    with pytest.raises(ValueError):
        size_and_seal(ctx_c[2], th)


def test_parent_not_evaluation(ctx_c):
    with pytest.raises(ValueError):
        size_and_seal(ctx_c[2], theta_c(), parent=ctx_c[2].base)


def test_parent_from_other_plan(ctx_c, ctx_a):
    ev_a = size_and_seal(ctx_a[2], theta_a())
    with pytest.raises(ValueError):
        size_and_seal(ctx_c[2], theta_c(), parent=ev_a)


# ---------------------------------------------------------------------------
# 재사용 계약 (7절)
# ---------------------------------------------------------------------------

def test_same_theta_with_parent_zero_compute(ctx_c):
    ctx = ctx_c[2]
    ev1 = size_and_seal(ctx, theta_c(y=0.45))
    reset()
    ev2 = size_and_seal(ctx, theta_c(y=0.45), parent=ev1)
    st = stats()
    assert all(st[b.name].computes == 0 for b in EVAL12)
    assert sum(st[b.name].reuses for b in EVAL12) == 12
    assert all(st[b.name].calls == 0 for b in PLAN5)          # 계획 블록은 평가에서 부르지 않는다
    assert ev2.snapshot.fp == ev1.snapshot.fp
    assert ev2.report == ev1.report


def _perturb(ctx, base_th, key, value):
    ev1 = size_and_seal(ctx, base_th)
    th = dict(base_th)
    th[key] = value
    reset()
    ev2 = size_and_seal(ctx, th, parent=ev1)
    st = stats()
    assert sum(s.recomputes_same_input for s in st.values()) == 0
    return {n: s.computes for n, s in st.items()}, ev1, ev2


def test_current_perturbation_skips_columns(ctx_c):
    c, _, _ = _perturb(ctx_c[2], theta_c(), ("current", "M2"), 2e-5)
    assert c["dc_currents"] == 1 and c["dc_widths"] == 1 and c["dc_tolerances"] == 1
    assert c["dc_lengths"] == 0 and c["dc_columns"] == 0 and c["dc_seal_node_conflict"] == 0


@pytest.mark.parametrize("key,val", [(("ln_idu", "M1"), Oracle.ln_idu("nmos", 0.62, 0.9, 0.0)),
                                     (("ln_idu", "M2"), Oracle.ln_idu("pmos", 0.75, 0.9, 0.0)),
                                     (("y", "out"), 0.55)])
def test_coordinate_perturbation_recomputes_columns_only_downstream(ctx_c, key, val):
    c, _, _ = _perturb(ctx_c[2], theta_c(), key, val)
    assert c["dc_columns"] == 1
    assert c["dc_currents"] == 0 and c["dc_lengths"] == 0


def test_resistance_perturbation(ctx_a):
    c, _, _ = _perturb(ctx_a[2], theta_a(), ("resistance", "R1"), 8e4)
    assert c["dc_columns"] == 1 and c["dc_currents"] == 0 and c["dc_lengths"] == 0


def test_current_through_resistor_recomputes_columns(ctx_a):
    c, _, _ = _perturb(ctx_a[2], theta_a(), ("current", "R1"), 1.1e-5)
    assert c["dc_currents"] == 1 and c["dc_columns"] == 1 and c["dc_lengths"] == 0


def test_parent_chain_then_back_reuses_nothing_wrongly(ctx_c):
    """θ0 -> θ1 -> θ0 (parent = θ1 평가): 값은 θ0 첫 평가와 같다(재사용이 값을 바꾸지 않는다)."""
    ctx = ctx_c[2]
    e0 = size_and_seal(ctx, theta_c())
    e1 = size_and_seal(ctx, theta_c(i2=3e-5), parent=e0)
    e2 = size_and_seal(ctx, theta_c(), parent=e1)
    assert e2.snapshot.fp == e0.snapshot.fp
    assert e1.snapshot.fp != e0.snapshot.fp


# ---------------------------------------------------------------------------
# 실패 규약 (8절) -- 행마다 실제로 그 예외·사유가 나는지
# ---------------------------------------------------------------------------

def test_failure_resistor_cycle(tmp_path, toy_access):
    doc = topo("f_rcycle", [mos("M1", "nmos", "out", "in", "gnd")], {"in": ("input", "x"), "out": ("output", "y")},
               passives=[two("R1", "resistor", "vdd", "out"), two("R2", "resistor", "out", "gnd")])
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc, toy_access)
    assert detail(ei.value)["rule_branch"] == "dc_resistor_cycle"
    assert set(ei.value.record.devices) <= {"R1", "R2"} and ei.value.record.margin is None
    assert not isinstance(ei.value, CANDIDATE_FAILURE_CLASSES)


def test_failure_zero_current_mos(tmp_path, toy_access):
    doc = topo("f_zero", [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd"),
                          mos("M3", "nmos", "z", "in", "gnd")], {"in": ("input", "x"), "out": ("output", "y")})
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc, toy_access)
    assert detail(ei.value)["rule_branch"] == "mos_zero_current_structural"
    assert ei.value.record.devices == ("M3",)


def test_failure_declared_kcl(tmp_path, toy_access):
    doc = topo("f_kcl", [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "m"), two("I2", "current_source", "m", "gnd")])
    with pytest.raises(InfeasibleTargetError) as ei:
        build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-6), ("I2", 5e-6)))
    assert detail(ei.value)["reason"] == "declared_source_kcl_conflict" and ei.value.record.margin is None


def test_failure_mos_current_nonpositive(tmp_path, toy_access):
    doc = topo("f_neg", [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "n")])
    ctx = build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-5),))[2]
    th = {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("y", "n"): 0.5,
          ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.0), ("ln_idu", "M2"): Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}
    th.update(free_currents(ctx, {"M1": -2e-5, "M2": 3e-5}))     # KCL M1 + M2 = I1 -> 한 MOS 가 음수
    assert set(th) == set(ctx.schema.components)
    # [r2] 원뿔 밖 θ 는 check_theta 의 ValueError(정의역 밖) -- 후보 실패가 아니다
    with pytest.raises(ValueError) as ei:
        size_and_seal(ctx, th)
    assert not isinstance(ei.value, CANDIDATE_FAILURE_CLASSES)
    assert "M1" in str(ei.value)
    with pytest.raises(ValueError):
        check_theta(ctx.schema, th)


def test_failure_empty_window(tmp_path, toy_access):
    ctx = build_ctx(tmp_path, circuit_empty_window(), toy_access)[2]
    th = {}
    for kind, key in ctx.schema.components:
        if kind != "current":
            th[(kind, key)] = {"L": 1e-6, "y": 0.5, "ln_idu": Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}[kind]
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 2e-5, "MC": 1e-5}))
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    d = detail(ei.value)
    assert d["reason"] == "empty_window" and d["item"] == 7
    assert ei.value.record.devices == () and ei.value.record.margin is None


@pytest.mark.parametrize("which,lut_reason", [("target", "lut_target_out_of_range"), ("anchor", "lut_l_not_anchor"),
                                              ("axis", "lut_axis_out_of_range")])
def test_failure_lut(ctx_c, tmp_path, toy_access, which, lut_reason):
    if which == "target":
        ctx, th = ctx_c[2], theta_c(x1=Oracle.ln_idu("nmos", 2.5, 0.9, 0.0))
    elif which == "anchor":
        ctx, th = ctx_c[2], theta_c(l1=1.25e-6)
    else:
        doc = circuit_cs_res(bulk_m1="out")
        doc["topology_name"] = "f_axis"
        ctx, th = build_ctx(tmp_path, doc, toy_access)[2], theta_a(i=1e-5, r=1.3e5)
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    d = detail(ei.value)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == lut_reason
    assert ei.value.record.devices == ("M1",)
    assert "device_query" in d


def test_failure_seal_violation(tmp_path, toy_access):
    doc = circuit_cs_res(bulk_m1="out")
    doc["topology_name"] = "f_seal"
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.3, -0.3),
          ("current", "R1"): 1e-5, ("resistance", "R1"): 1.5e5}
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    d = detail(ei.value)
    assert d["item"] == 6 and len(d["items"]) == 8
    assert ei.value.record.margin > 1


def test_diode_mirror_full_evaluation(tmp_path, toy_access):
    """1변수 노드(diode) 가 있는 회로도 봉인 1·2·3·4·5·6·8 pass, 7 undefined -> sealed None."""
    from .test_block_columns import _mirror_ctx, _mirror_theta
    ctx = _mirror_ctx(tmp_path, toy_access)
    ev = size_and_seal(ctx, _mirror_theta(ctx, 0.6))
    assert ev.sealed is None and ev.report.status == "undefined"
    assert [i.status for i in ev.report.items] == ["pass"] * 6 + ["undefined", "pass"]


def test_failure_no_root_in_window(tmp_path, toy_access):
    from .test_block_columns import _mirror_ctx, _mirror_theta
    ctx = _mirror_ctx(tmp_path, toy_access)
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, _mirror_theta(ctx, 2.0))
    assert detail(ei.value)["reason"] == "no_root_in_window"
    assert isinstance(ei.value, CANDIDATE_FAILURE_CLASSES)


def test_candidate_failure_classes_exact():
    assert CANDIDATE_FAILURE_CLASSES == (NonconvergentError, SealViolationError)


# ---------------------------------------------------------------------------
# 결정론 (9절) -- PYTHONHASHSEED·netlist 순서
# ---------------------------------------------------------------------------

_SCRIPT = r'''
import json, random, sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import conftest as C
from gmid_engine.lut import load_lut_set
from gmid_engine.sizing import size_and_seal
tmp = Path(tempfile.mkdtemp())
m, c = C.write_toy_lut(tmp / "lut")
acc = C.new_access(load_lut_set(str(m), str(c), C.TOY_SPEC))
out = {}
for tag, doc, th in (("C", C.circuit_cs_pmos_load(), C.theta_c()), ("A", C.circuit_cs_res(), C.theta_a())):
    for k, seed in enumerate((None, 1, 2)):
        d = json.loads(json.dumps(doc))
        if seed is not None:
            random.Random(seed).shuffle(d["netlist"])
            d["passive_elements"] = list(reversed(d["passive_elements"]))
        sub = tmp / ("%s%d" % (tag, k)); sub.mkdir()
        _, _, ctx = C.build_ctx(sub, d, acc)
        ev = size_and_seal(ctx, th)
        out["%s_%s" % (tag, seed)] = [ev.snapshot.fp, ctx.base.fp]
print(json.dumps(out))
'''


def test_determinism_hashseed_and_netlist_order(tmp_path):
    script = tmp_path / "det.py"
    script.write_text(_SCRIPT, encoding="utf-8")
    results = []
    for seed in ("0", "1", "4242"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        r = subprocess.run([sys.executable, str(script), str(SKILL_DIR), str(HERE)], capture_output=True, text=True,
                           env=env, timeout=300)
        assert r.returncode == 0, r.stderr[-2000:]
        results.append(json.loads(r.stdout.strip().splitlines()[-1]))
    assert results[0] == results[1] == results[2]
    for tag in ("C", "A"):
        fps = {tuple(v) for k, v in results[0].items() if k.startswith(tag)}
        assert len(fps) == 1, "netlist 순서에 따라 결과가 달라짐: %s" % tag
