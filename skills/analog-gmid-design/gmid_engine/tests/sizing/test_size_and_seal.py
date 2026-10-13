"""`size_and_seal(ctx, theta, parent=None) -> DcEvaluation` -- CONTRACT 7절(API·재사용 계약), 8절(실패 규약), 9절(결정론).

재사용은 core 블록 계수(`stats()`)로 잰다. 기대값은 계약 7절 문장(같은 θ·parent -> computes 0·reuses 13, 한 성분 섭동 ->
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
from gmid_engine.graph import s1_symmetry   # [U17 ①-d] 계획 블록 dc_struct_colour -> graph 대칭 블록(40 §6-8 D-2)
from gmid_engine.sizing import DcEvaluation, check_theta, size_and_seal

from .conftest import (HERE, Oracle, SKILL_DIR, build_ctx, circuit_cs_res, circuit_empty_window, detail, free_currents, mos,
                       theta_a, theta_c, topo, two)

EVAL13 = (S.dc_currents, S.dc_lengths, S.dc_columns, S.dc_widths, S.dc_tolerances, S.dc_seal_node_conflict,
          S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_saturation, S.dc_seal_kvl_branch,
          S.dc_seal_conduction, S.dc_seal_report)       # [r8] 4 평가 + 8 봉인(tol·1·2·3·6·7·8·9) + report = 13
PLAN5 = (S.dc_rails, s1_symmetry, S.dc_current_basis, S.dc_writer_plan, S.dc_scc_order, S.dc_theta_schema)


def reset():
    for b in EVAL13 + PLAN5:
        b.reset_stats()


def stats():
    return {b.name: b.stats() for b in EVAL13 + PLAN5}


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
    assert all(st[b.name].computes == 0 for b in EVAL13)
    assert sum(st[b.name].reuses for b in EVAL13) == 13
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
    assert c["dc_seal_conduction"] == 1          # [r8] dc_op(W·current) 가 바뀌어 하류 봉인 9 도 다시


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


@pytest.fixture(scope="module")
def ctx_passive(tmp_path_factory, toy_access):
    """회로 A + Rz(out, m)–Cz(m, gnd) (둘 다 engine): Rz 는 가지치기 저항이고 구조 규칙 no_cs_cell -> θ ss_resistance,
    Cz -> θ capacitance (4.4 r5). 그 밖 θ 는 회로 A 와 같다."""
    doc = circuit_cs_res()
    doc["topology_name"] = "ss_passive_theta"
    doc["passive_elements"] += [two("Rz", "resistor", "out", "m"), two("Cz", "capacitor", "m", "gnd")]
    return build_ctx(tmp_path_factory.mktemp("ctx_passive"), doc, toy_access,
                     element_values=(("Cz", None), ("R1", None), ("Rz", None)), engine_elements=("Cz", "Rz"))[2]


def theta_passive(cz=1e-12, rz=1e4, **kw):
    th = theta_a(**kw)
    th[("capacitance", "Cz")] = cz
    th[("ss_resistance", "Rz")] = rz
    return th


def test_passive_theta_components_present(ctx_passive):
    keys = set(ctx_passive.schema.components)
    assert ("capacitance", "Cz") in keys and ("ss_resistance", "Rz") in keys
    assert {k for t, k in keys if t in S.THETA_PASSIVE_KINDS} == {"Cz", "Rz"}


@pytest.mark.parametrize("key,val", [(("capacitance", "Cz"), 1.1e-12), (("ss_resistance", "Rz"), 1.1e4), ("both", None)])
def test_passive_theta_only_change_zero_dc_compute(ctx_passive, key, val):
    """[r5] 7절: capacitance·ss_resistance 성분만 다른 θ 를 parent 에서 부르면 dc 블록 전부 computes 0(reuses 13), 계획 블록
    호출 0, 결과는 parent 와 같은 봉인 상태(스냅샷 지문·report 같음)."""
    ctx = ctx_passive
    ev1 = size_and_seal(ctx, theta_passive())
    th = theta_passive(cz=2e-12, rz=3e4) if key == "both" else {**theta_passive(), key: val}
    reset()
    ev2 = size_and_seal(ctx, th, parent=ev1)
    st = stats()
    assert all(st[b.name].computes == 0 for b in EVAL13), {b.name: st[b.name].computes for b in EVAL13}
    assert sum(st[b.name].reuses for b in EVAL13) == 13
    assert all(st[b.name].calls == 0 for b in PLAN5)
    assert ev2.snapshot.fp == ev1.snapshot.fp and ev2.report == ev1.report


def test_passive_theta_not_in_dc_values(ctx_passive):
    """수동 θ 를 크게 바꿔 parent 없이 새로 평가해도 DC 노드전압·소자 op 는 비트 동일(DC 블록이 읽지 않는다)."""
    ctx = ctx_passive
    a = size_and_seal(ctx, theta_passive())
    b = size_and_seal(ctx, theta_passive(cz=7e-11, rz=123.0))
    assert a.snapshot.fp == b.snapshot.fp
    assert a.snapshot.column("node", "dc_v") == b.snapshot.column("node", "dc_v")


@pytest.mark.parametrize("key", [("capacitance", "Cz"), ("ss_resistance", "Rz")])
@pytest.mark.parametrize("bad", [0.0, -1e-12])
def test_passive_theta_domain(ctx_passive, key, bad):
    """5.1 [r5]: capacitance ≤ 0, ss_resistance ≤ 0 -> ValueError(check_theta, size_and_seal 경로 모두)."""
    th = {**theta_passive(), key: bad}
    with pytest.raises(ValueError):
        check_theta(ctx_passive.schema, th)
    with pytest.raises(ValueError):
        size_and_seal(ctx_passive, th)


def test_passive_theta_key_required(ctx_passive):
    """수동 θ 성분도 components 의 일부 -- 빠지면 키 불일치 ValueError(5.1)."""
    th = theta_passive()
    del th[("capacitance", "Cz")]
    with pytest.raises(ValueError):
        size_and_seal(ctx_passive, th)


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
                          mos("M3", "nmos", "z", "in", "gnd")], {"in": ("input", "x"), "out": ("output", "y")},
               bias=["pb"])                                                                  # pb: M2 gate 에만
    with pytest.raises(StructureUnresolvedError) as ei:
        build_ctx(tmp_path, doc, toy_access)
    assert detail(ei.value)["rule_branch"] == "mos_zero_current_structural"
    assert ei.value.record.devices == ("M3",)


def test_failure_declared_kcl(tmp_path, toy_access):
    doc = topo("f_kcl", [mos("M1", "nmos", "out", "in", "gnd"), mos("M2", "pmos", "out", "pb", "vdd")],
               {"in": ("input", "x"), "out": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "m"), two("I2", "current_source", "m", "gnd")],
               bias=["pb"])                                                                  # pb: M2 gate 에만
    with pytest.raises(InfeasibleTargetError) as ei:
        build_ctx(tmp_path, doc, toy_access, element_values=(("I1", 1e-6), ("I2", 5e-6)))
    assert detail(ei.value)["reason"] == "declared_source_kcl_conflict" and ei.value.record.margin is None


def test_failure_mos_current_nonpositive(tmp_path, toy_access):
    doc = topo("f_neg", [mos("M1", "nmos", "n", "in", "gnd"), mos("M2", "nmos", "n", "b2", "gnd")],
               {"in": ("input", "x"), "n": ("output", "y")},
               sources=[two("I1", "current_source", "vdd", "n")], bias=["b2"])             # b2: M2 gate 에만
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
    assert d["item"] == 6 and len(d["items"]) == 9                       # [r8] 9개
    assert ei.value.record.margin > 1


def test_diode_mirror_full_evaluation(tmp_path, toy_access):
    """1변수 노드(diode) 가 있는 회로도 봉인 1·2·3·4·5·6·8·[r8] 9 pass, 7 undefined -> sealed None."""
    from .test_block_columns import _mirror_ctx, _mirror_theta
    ctx = _mirror_ctx(tmp_path, toy_access)
    ev = size_and_seal(ctx, _mirror_theta(ctx, 0.6))
    assert ev.sealed is None and ev.report.status == "undefined"
    assert [i.status for i in ev.report.items] == ["pass"] * 6 + ["undefined", "pass", "pass"]


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


# ===========================================================================
# [U4] L 동치류 L 공유의 평가 (D-GB7a, 설계 40 §3.7-1, CONTRACT 14.1 'size_and_seal: 멤버 L = 주인 θ L')
# ===========================================================================

import math as _math                                                                       # noqa: E402

from gmid_engine.sizing import OrderHints                                                  # noqa: E402

from .conftest import (B as _B, C as _C, LClassStub, build_ctx_u4, circuit_mirror, mos_table, node_voltages,  # noqa: E402
                       r4_ln_idu, rel_close, terminal_mag, theta_mirror, theta_r4c, with_hand_ss)


@pytest.fixture(scope="module")
def mir_tied(tmp_path_factory, r4_access):
    return build_ctx_u4(tmp_path_factory.mktemp("ss_tied"), circuit_mirror(), r4_access,
                        l_classes=(LClassStub("M1", ("M1", "M2")),), element_values=(("I1", 1e-5),))[1]


def _tied_theta(l_owner, l3=1e-6):
    th = theta_mirror(l=(l_owner, l_owner, l3))
    del th[("L", "M2")]
    return th


@pytest.mark.parametrize("l_owner", [1e-6, 2e-6])
def test_member_l_is_owner_theta_l(mir_tied, l_owner):
    """멤버 M2 의 dc_L·DeviceOp.L = 주인 M1 의 θ L(정확히). M2 의 W = ID·L_owner / IDu_forward(V(nb), 0.9)(닫힌 식) -- L 이 W 계산
    까지 실제로 쓰였다. M3(동치류 밖)는 자기 θ L."""
    ev = size_and_seal(mir_tied, _tied_theta(l_owner))
    ops = dict(ev.snapshot.column("device", "dc_op"))
    assert dict(ev.snapshot.column("device", "dc_L")) == {"M1": l_owner, "M2": l_owner, "M3": 1e-6}
    assert ops["M2"].L == ops["M1"].L == l_owner and ops["M3"].L == 1e-6
    V = node_voltages(ev.snapshot)
    w2 = 1e-5 * l_owner / _math.exp(r4_ln_idu("nmos", V["nb"], 0.9, 0.0))
    assert rel_close(ops["M2"].W, w2, 1e-9)


def test_owner_l_perturbation_moves_member(mir_tied):
    """FD 관점: 주인 L 성분 하나만 바꾸면 멤버 L 도 따라 바뀐다(동치류당 변수 하나, 설계 41 §5.3 'L 동치류별 L' 축)."""
    a = size_and_seal(mir_tied, _tied_theta(1e-6))
    b = size_and_seal(mir_tied, _tied_theta(2e-6), parent=a)
    la, lb = dict(a.snapshot.column("device", "dc_L")), dict(b.snapshot.column("device", "dc_L"))
    assert (la["M2"], lb["M2"]) == (1e-6, 2e-6)


# ===========================================================================
# [U4] IC1 -- 모든 소자 VGS 정합 (설계 40 §10.3 IC1, 계획 N3.6 봉인 2·'tol_V 를 IC1 test 의 허용오차로')
# ===========================================================================
# 9회로 봉인 해는 탐색(U15/U16)이 만든다 -- 이 단위의 IC1 은 U4 경로(L 동치류·W_request·S2p·입력 창·OrderHints)로 봉인된 toy
# 점 전부에 같은 단언을 건다. oracle (a): 노드전압에서 다시 만든 VGS·VDS·VSB 로 r4 닫힌 식 ln IDu 를 계산하고, 쓰기 소자의 좌표
# (θ ln_idu, W 요청이 있으면 ln(ID·L/W_req) -- CONTRACT 14.3)와의 차를 gm/ID = B − C·VGS 로 나눈 값이 tol_V(그 소자 dc_tol_v) 이하.
# 종속 소자는 DeviceOp.ln_idu 가 같은 닫힌 식의 순방향 값과 tol_V 안에서 같다.


def _ic1_points(ctx_r4c, mir_tied, mir_plain, mir_hint):
    pts = []
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    pts.append((ctx_r4c, theta_r4c(), {}, e0))
    th = theta_r4c(v1=0.62)
    pts.append((ctx_r4c, th, {}, size_and_seal(ctx_r4c, th, parent=with_hand_ss(e0))))
    th = _tied_theta(2e-6)
    pts.append((mir_tied, th, {}, size_and_seal(mir_tied, th)))
    th = theta_mirror()
    for wr in ({"M3": 1e-5}, {"M1": 2e-5}, {"M2": 3e-5}):
        pts.append((mir_plain, th, wr, size_and_seal(mir_plain, th, w_request=wr)))
    th = theta_mirror()
    th[("ln_idu", "M2")] = th.pop(("ln_idu", "M1"))
    pts.append((mir_hint, th, {}, size_and_seal(mir_hint, th)))
    return pts


@pytest.fixture(scope="module")
def mir_plain(tmp_path_factory, r4_access):
    return build_ctx_u4(tmp_path_factory.mktemp("ss_plain"), circuit_mirror(), r4_access, element_values=(("I1", 1e-5),))[1]


@pytest.fixture(scope="module")
def mir_hint(tmp_path_factory, r4_access):
    return build_ctx_u4(tmp_path_factory.mktemp("ss_hint"), circuit_mirror(), r4_access,
                        order_hints=OrderHints(independent=("M2",)), element_values=(("I1", 1e-5),))[1]


def test_ic1_vgs_consistency_all_devices(ctx_r4c, mir_tied, mir_plain, mir_hint):
    n = 0
    for ctx, th, wr, ev in _ic1_points(ctx_r4c, mir_tied, mir_plain, mir_hint):
        assert ev.sealed is not None
        snap = ev.snapshot
        V = node_voltages(snap)
        ops = dict(snap.column("device", "dc_op"))
        tolv = dict(snap.column("device", "dc_tol_v"))
        for m, (kind, d, g, s, b) in mos_table(snap).items():
            vgs, vds, vsb = terminal_mag(kind, V, d, g, s, b)
            fwd = r4_ln_idu(kind, vgs, vds, vsb)
            role = snap.value("device", m, "dc_coord").role
            if role == "writer":
                coord = _math.log(ops[m].current * ops[m].L / wr[m]) if m in wr else th[("ln_idu", m)]
            else:
                coord = ops[m].ln_idu
            assert abs(fwd - coord) / (_B - _C * vgs) <= tolv[m], (m, role, fwd, coord)
            n += 1
    assert n == 2 * 2 + 5 * 3                                          # 회로 C 점 2개 × 2 + 거울 점 5개 × 3


# ===========================================================================
# [U4] IC2 -- 순서 섞기 불변 (설계 40 §10.3 IC2, 계획 N3.5 SC-a)
# ===========================================================================

def test_ic2_order_shuffle_invariance(tmp_path, r4_access):
    """netlist 순서·L 동치류 목록/멤버 순서·OrderHints tuple 순서·W_request 순서를 섞은 두 입력 -> 계획·평가 스냅샷 지문 같음
    (이산 필드 동일, 연속 필드 비트 동일)."""
    import random as _random
    doc_a = circuit_mirror()
    doc_b = json.loads(json.dumps(doc_a))
    _random.Random(7).shuffle(doc_b["netlist"])
    assert [e["name"] for e in doc_b["netlist"]] != [e["name"] for e in doc_a["netlist"]]
    lc_a = (LClassStub("M1", ("M1", "M2")), LClassStub("M3", ("M3",)))
    lc_b = (LClassStub("M3", ("M3",)), LClassStub("M1", ("M2", "M1")))
    h_a = OrderHints(gm_required=("M2", "M3"), stage=(("M1", 1), ("M2", 2)))
    h_b = OrderHints(gm_required=("M3", "M2"), stage=(("M2", 2), ("M1", 1)))
    _, a = build_ctx_u4(tmp_path / "a", doc_a, r4_access, l_classes=lc_a, order_hints=h_a, element_values=(("I1", 1e-5),))
    _, b = build_ctx_u4(tmp_path / "b", doc_b, r4_access, l_classes=lc_b, order_hints=h_b, element_values=(("I1", 1e-5),))
    assert a.base.fp == b.base.fp and a.schema == b.schema and a.l_ties == b.l_ties
    th = _tied_theta(2e-6)
    ea = size_and_seal(a, th, w_request={"M3": 1e-5, "M2": 3e-5})
    eb = size_and_seal(b, th, w_request=(("M2", 3e-5), ("M3", 1e-5)))
    assert ea.snapshot.fp == eb.snapshot.fp and ea.report == eb.report
