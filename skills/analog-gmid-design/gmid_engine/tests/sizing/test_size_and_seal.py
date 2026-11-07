"""`size_and_seal(ctx, theta, parent=None) -> DcEvaluation` -- CONTRACT 7절(API·재사용 계약), 8절(실패 규약), 9절(결정론).

재사용은 실행 계수(XRUN-F1 card B C1 `RunCounters`, ctx 의 실행)로 잰다. 기대값은 계약 7절 문장(같은 θ·parent -> computes 0·reuse 12·dc_seal_report graft 1, 한 성분 섭동 ->
지정 블록만 다시)이다. 9회로 §10 숫자는 쓰지 않는다.
"""
import json
import os
import random
import subprocess
import sys
import types
from pathlib import Path

import pytest

from gmid_engine.core import (CANDIDATE_FAILURE_CLASSES, InfeasibleTargetError, NonconvergentError,
                              SealViolationError, StructureUnresolvedError)
from gmid_engine import sizing as S
from gmid_engine.graph import s1_symmetry   # [U17 ①-d] 계획 블록 dc_struct_colour -> graph 대칭 블록(40 §6-8 D-2)
from gmid_engine.sizing import DcEvaluation, check_theta
from fs1_wf import size_and_seal      # [FS-1 서명 맞춤] 손 wf 를 끼운 래퍼

from .conftest import (HERE, Oracle, SKILL_DIR, build_ctx, circuit_cs_res, circuit_empty_window, detail, free_currents, mos,
                       theta_a, theta_c, topo, two)
from .conftest import COUNT_FIELDS, block_row, row_delta  # [XRUN-F1 card B C1] 실행 계수 행
from .conftest import kschema, kties  # [U17 ①-b] graph/kernel 필드 읽기(설계 40 v1.9.1 §2.4.7 KernelContext 행)

EVAL11 = (S.dc_currents, S.dc_lengths, S.dc_solve, S.dc_tolerances, S.dc_seal_node_conflict,
          S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_region, S.dc_seal_kvl_branch,
          S.dc_seal_report)       # [EO-1 범위 4] 3 평가(WB-1: dc_solve 하나) + 7 봉인(tol·1·2·3·6·7/9 영역 판정 하나·8) + report = 11
# 해석: dc_seal_region 의 자리는 옛 봉인 7 자리(6 다음, 8 앞) -- interface 는 순서를 적지 않았다.
PLAN5 = (S.dc_rails, s1_symmetry, S.dc_current_basis, S.dc_writer_plan, S.dc_scc_order, S.dc_theta_schema)


def _assert_dc_outcomes(st):
    """[IT-2a T-L11d, 승인 20261022-it2a-o94-ext 범위 2; oracle (d) 사용자 선언 design 41 v1.12.8 L11 (d)] 같은 입력 재평가의 DC 열세 블록:
    computes 0, 커널 3 + 봉인 항목 7 = 블록마다 outcome reuse 1회(합 10), dc_seal_report = outcome graft 1회(keep 밖 -> S3 graft)."""
    kernel3 = (S.dc_currents, S.dc_lengths, S.dc_solve)
    items7 = EVAL11[3:10]
    assert len(kernel3) + len(items7) == 10 and EVAL11[10] is S.dc_seal_report
    for b in kernel3 + items7:
        r = st[b.name]
        assert (r.reuses, r.grafts, r.replays, r.computes) == (1, 0, 0, 0), (b.name, r)
    rep = st[S.dc_seal_report.name]
    assert (rep.reuses, rep.grafts, rep.replays, rep.computes) == (0, 1, 0, 0), rep
    assert sum(st[b.name].reuses for b in EVAL11) == 10 and sum(st[b.name].grafts for b in EVAL11) == 1


def stats(ctx):
    """[XRUN-F1 card B C1·C4] ctx 실행 계수의 블록 행(옛 블록 객체 stats 대체 -- 블록은 상태가 없다)."""
    return {b.name: block_row(ctx.counters, b.name) for b in EVAL11 + PLAN5}


def stats_since(ctx, before):
    """stats(ctx) 의 before 이후 증분 -- 속성 calls·reuses·grafts·replays·computes·recomputes_same_input."""
    now = stats(ctx)
    return {n: types.SimpleNamespace(**dict(zip(COUNT_FIELDS, row_delta(now[n], before[n])))) for n in now}


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
    b = size_and_seal(ctx, check_theta(kschema(ctx), theta_c()))
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
    before = stats(ctx)
    ev2 = size_and_seal(ctx, theta_c(y=0.45), parent=ev1)
    st = stats_since(ctx, before)
    assert all(st[b.name].computes == 0 for b in EVAL11)
    _assert_dc_outcomes(st)
    assert all(st[b.name].calls == 0 for b in PLAN5)          # 계획 블록은 평가에서 부르지 않는다
    assert ev2.snapshot.fp == ev1.snapshot.fp
    assert ev2.report == ev1.report


def _perturb(ctx, base_th, key, value):
    ev1 = size_and_seal(ctx, base_th)
    th = dict(base_th)
    th[key] = value
    before = stats(ctx)
    ev2 = size_and_seal(ctx, th, parent=ev1)
    st = stats_since(ctx, before)
    assert sum(s.recomputes_same_input for s in st.values()) == 0
    return {n: s.computes for n, s in st.items()}, ev1, ev2


def test_current_perturbation_recomputes_dc_solve_not_lengths(ctx_c):
    # [WB-1] 옛 노드 풀이 블록 건너뛰기 단언은 소멸: dc_solve 가 노드 풀이와 W 를 한 블록으로 합쳤고 dc_current 를 읽는다
    c, _, _ = _perturb(ctx_c[2], theta_c(), ("current", "M2"), 2e-5)
    assert c["dc_currents"] == 1 and c["dc_solve"] == 1 and c["dc_tolerances"] == 1
    assert c["dc_lengths"] == 0 and c["dc_seal_node_conflict"] == 0
    assert c["dc_seal_region"] == 1          # [EO-1 범위 4] dc_op(W·current) 가 바뀌어 하류 영역 판정(봉인 7·9)도 다시


@pytest.mark.parametrize("key,val", [(("ln_idu", "M1"), Oracle.ln_idu("nmos", 0.62, 0.9, 0.0)),
                                     (("ln_idu", "M2"), Oracle.ln_idu("pmos", 0.75, 0.9, 0.0)),
                                     (("y", "out"), 0.55)])
def test_coordinate_perturbation_recomputes_columns_only_downstream(ctx_c, key, val):
    c, _, _ = _perturb(ctx_c[2], theta_c(), key, val)
    assert c["dc_solve"] == 1
    assert c["dc_currents"] == 0 and c["dc_lengths"] == 0


def test_resistance_perturbation(ctx_a):
    c, _, _ = _perturb(ctx_a[2], theta_a(), ("resistance", "R1"), 8e4)
    assert c["dc_solve"] == 1 and c["dc_currents"] == 0 and c["dc_lengths"] == 0


def test_current_through_resistor_recomputes_columns(ctx_a):
    c, _, _ = _perturb(ctx_a[2], theta_a(), ("current", "R1"), 1.1e-5)
    assert c["dc_currents"] == 1 and c["dc_solve"] == 1 and c["dc_lengths"] == 0


# [XRUN-F1 card B 규칙 M M-d] KernelContext(실행 두 객체를 칸으로 쥠)는 function 범위
@pytest.fixture
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
    keys = set(kschema(ctx_passive).components)
    assert ("capacitance", "Cz") in keys and ("ss_resistance", "Rz") in keys
    assert {k for t, k in keys if t in S.THETA_PASSIVE_KINDS} == {"Cz", "Rz"}


@pytest.mark.parametrize("key,val", [(("capacitance", "Cz"), 1.1e-12), (("ss_resistance", "Rz"), 1.1e4), ("both", None)])
def test_passive_theta_only_change_zero_dc_compute(ctx_passive, key, val):
    """[r5] 7절: capacitance·ss_resistance 성분만 다른 θ 를 parent 에서 부르면 dc 블록 전부 computes 0(reuse 10 + dc_seal_report graft 1), 계획 블록
    호출 0, 결과는 parent 와 같은 봉인 상태(스냅샷 지문·report 같음)."""
    ctx = ctx_passive
    ev1 = size_and_seal(ctx, theta_passive())
    th = theta_passive(cz=2e-12, rz=3e4) if key == "both" else {**theta_passive(), key: val}
    before = stats(ctx)
    ev2 = size_and_seal(ctx, th, parent=ev1)
    st = stats_since(ctx, before)
    assert all(st[b.name].computes == 0 for b in EVAL11), {b.name: st[b.name].computes for b in EVAL11}
    _assert_dc_outcomes(st)
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
        check_theta(kschema(ctx_passive), th)
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
    assert set(th) == set(kschema(ctx).components)
    # [r2] 원뿔 밖 θ 는 check_theta 의 ValueError(정의역 밖) -- 후보 실패가 아니다
    with pytest.raises(ValueError) as ei:
        size_and_seal(ctx, th)
    assert not isinstance(ei.value, CANDIDATE_FAILURE_CLASSES)
    assert "M1" in str(ei.value)
    with pytest.raises(ValueError):
        check_theta(kschema(ctx), th)


def test_failure_empty_window(tmp_path, toy_access):
    ctx = build_ctx(tmp_path, circuit_empty_window(), toy_access)[2]
    th = {}
    for kind, key in kschema(ctx).components:
        if kind != "current":
            th[(kind, key)] = {"L": 1e-6, "y": 0.5, "ln_idu": Oracle.ln_idu("nmos", 0.6, 0.9, 0.0)}[kind]
    th.update(free_currents(ctx, {"MA": 1e-5, "MB": 2e-5, "MC": 1e-5}))
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, th)
    d = detail(ei.value)
    assert d["reason"] == "empty_window" and d["item"] == 7
    assert ei.value.record.devices == () and ei.value.record.margin is None


@pytest.mark.parametrize("which,lut_reason", [("target", "lut_target_out_of_range"), ("anchor", "lut_l_bin_unbracketed"),
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
    from .test_block_dc import _mirror_ctx, _mirror_theta
    ctx = _mirror_ctx(tmp_path, toy_access)
    ev = size_and_seal(ctx, _mirror_theta(ctx, 0.6))
    assert ev.sealed is None and ev.report.status == "undefined"
    assert [i.status for i in ev.report.items] == ["pass"] * 6 + ["undefined", "pass", "pass"]


def test_failure_no_root_in_window(tmp_path, toy_access):
    from .test_block_dc import _mirror_ctx, _mirror_theta
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
sys.path.insert(0, sys.argv[3]); sys.path.insert(0, sys.argv[1]); sys.path.insert(0, sys.argv[2])
import conftest as C
from gmid_engine.lut import load_lut_set
from fs1_wf import size_and_seal      # [FS-1 서명 맞춤] 손 wf 를 끼운 래퍼
tmp = Path(tempfile.mkdtemp())
m, c = C.write_toy_lut(tmp / "lut")
acc = C.new_access(load_lut_set(str(m), str(c), C.TOY_SPEC, bin_rule=C.bin_rule_of(m), pdk_root=C.pdk_of(m)))
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
        r = subprocess.run([sys.executable, str(script), str(SKILL_DIR), str(HERE), str(HERE.parent)], capture_output=True, text=True,
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


from .conftest import (B as _B, C as _C, LClassStub, build_ctx_u4, circuit_mirror, mirror_w_request, mos_table,  # noqa: E402
                       node_voltages, r4_ln_idu, rel_close, terminal_mag, theta_mirror, theta_r4c, with_hand_ss)


@pytest.fixture
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
# 9회로 봉인 해는 탐색(U15/U16)이 만든다 -- 이 단위의 IC1 은 U4 경로(L 동치류·W_request·S2p·입력 창)로 봉인된 toy
# 점 전부에 같은 단언을 건다. oracle (a): 노드전압에서 다시 만든 VGS·VDS·VSB 로 r4 닫힌 식 ln IDu 를 계산하고, 쓰기 소자의 좌표
# (θ ln_idu, W 요청이 있으면 ln(ID·L/W_req) -- CONTRACT 14.3)와의 차를 gm/ID = B − C·VGS 로 나눈 값이 tol_V(그 소자 dc_tol_v) 이하.
# 종속 소자는 DeviceOp.ln_idu 가 같은 닫힌 식의 순방향 값과 tol_V 안에서 같다.


# [TB-1 retired/broken] 옛 mir_hint 점(순서 힌트 independent=M2 로 M2 를 writer 로 만든 점)은 지웠다: 힌트가 없어졌고 평행 관계의 독립 유지는
# diode(M1)라 그 점은 mir_plain 과 같아진다 -- 이유 O-187·O-189·O-194. 거울 점은 5개에서 4개(tied 1 + plain 의 W 요청 3)가 된다.
def _ic1_points(ctx_r4c, mir_tied, mir_plain):
    pts = []
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    pts.append((ctx_r4c, theta_r4c(), {}, e0))
    th = theta_r4c(v1=0.62)
    pts.append((ctx_r4c, th, {}, size_and_seal(ctx_r4c, th, parent=with_hand_ss(e0))))
    th = _tied_theta(2e-6)
    pts.append((mir_tied, th, {}, size_and_seal(mir_tied, th)))
    th = theta_mirror()
    # [U17 ①] 종속 소자 M2 의 요청은 봉인 3 허용오차 안(δ = 0.05 < δ_max, conftest `mirror_w_request` 주석) -- 옛 3e-5(δ ≈ 0.27)는
    # 자기 동작점 gm 의 tol_I(설계 40 §3.7-3)에서 봉인 3 위반이라 봉인 점이 아니다(판정 변화).
    for wr in ({"M3": 1e-5}, {"M1": 2e-5}, {"M2": mirror_w_request()}):
        pts.append((mir_plain, th, wr, size_and_seal(mir_plain, th, w_request=wr)))
    return pts


@pytest.fixture
def mir_plain(tmp_path_factory, r4_access):
    return build_ctx_u4(tmp_path_factory.mktemp("ss_plain"), circuit_mirror(), r4_access, element_values=(("I1", 1e-5),))[1]


def test_ic1_vgs_consistency_all_devices(ctx_r4c, mir_tied, mir_plain):
    n = 0
    for ctx, th, wr, ev in _ic1_points(ctx_r4c, mir_tied, mir_plain):
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
    assert n == 2 * 2 + 4 * 3                                          # 회로 C 점 2개 × 2 + 거울 점 4개 × 3 (mir_hint 점 폐기, 위 주석)


# ===========================================================================
# [U4] IC2 -- 순서 섞기 불변 (설계 40 §10.3 IC2, 계획 N3.5 SC-a)
# ===========================================================================

def test_ic2_order_shuffle_invariance(tmp_path, r4_access):
    """netlist 순서·L 동치류 목록/멤버 순서·순서 힌트 tuple 순서·W_request 순서를 섞은 두 입력 -> 계획·평가 스냅샷 지문 같음
    (이산 필드 동일, 연속 필드 비트 동일)."""
    import random as _random
    doc_a = circuit_mirror()
    doc_b = json.loads(json.dumps(doc_a))
    _random.Random(7).shuffle(doc_b["netlist"])
    assert [e["name"] for e in doc_b["netlist"]] != [e["name"] for e in doc_a["netlist"]]
    lc_a = (LClassStub("M1", ("M1", "M2")), LClassStub("M3", ("M3",)))
    # [U17 ①-b] L 동치류 목록 순서는 이제 S0 수준 필드 graph/s1v: l_classes(writer build_s1v)의 값이다(설계 40 v1.9.1 §2.4.8 D1) -- 그 정준 순서는
    # build_s1v 몫이라 이 test 의 입력 주입(inject_l_classes)은 같은 정준 순서로 준다. 나머지 섞기(netlist·순서 힌트·W_request)는 그대로.
    lc_b = (LClassStub("M1", ("M1", "M2")), LClassStub("M3", ("M3",)))
    _, a = build_ctx_u4(tmp_path / "a", doc_a, r4_access, l_classes=lc_a, element_values=(("I1", 1e-5),))     # [TB-1] 순서 힌트 입력 폐기(O-187·O-189·O-194)
    _, b = build_ctx_u4(tmp_path / "b", doc_b, r4_access, l_classes=lc_b, element_values=(("I1", 1e-5),))
    assert a.base.fp == b.base.fp and kschema(a) == kschema(b) and kties(a) == kties(b)
    th = _tied_theta(2e-6)
    w2 = mirror_w_request(l=2e-6)                             # [U17 ①] 종속 소자 M2 요청 = 봉인 3 허용오차 안(L = 주인 2e-6; 옛 3e-5 는 위반)
    ea = size_and_seal(a, th, w_request={"M3": 1e-5, "M2": w2})
    eb = size_and_seal(b, th, w_request=(("M2", w2), ("M3", 1e-5)))
    assert ea.snapshot.fp == eb.snapshot.fp and ea.report == eb.report


# =====================================================================================================================
# [IT-2e 20261104-it2e-partial-snapshot, T-E2·T-E3·T-E4·T-E7] 실패 평가의 부분 스냅샷 -- 봉인 항목 블록, parent 유무 대조, 봉인 위반 경로.
# oracle (변성): 부분 스냅샷은 (평가 키, 실패 지점)만으로 정해진다 -- parent 가 있든 없든 같은 θ·같은 주입이면 지문이 같다.
# 기대 집합·주입·유효 조건 (가)(나)는 test_kernel_run 의 IT-2e 절과 같은 helper 를 쓴다(피검 함수로 기대값을 만들지 않는다).
# =====================================================================================================================

from .test_kernel_run import (IT2E_KERNEL, IT2E_SEAL, it2e_assert_parent_had_k_fields, it2e_assert_rule,  # noqa: E402
                              it2e_record, it2e_run)


@pytest.mark.parametrize("k", IT2E_SEAL)
def test_it2e_seal_item_block_failure_with_parent_partial_rule(tmp_path_factory, toy_access, monkeypatch, k):
    """T-E2: 봉인 항목 블록 k(봉인 7 항목 + dc_seal_report) 후보 실패 + parent -> 키 = base writer ∪ k 앞 블록, k 이후 없음."""
    rec = it2e_record(tmp_path_factory, toy_access)
    r = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, True, rec)
    it2e_assert_parent_had_k_fields(r, k)
    it2e_assert_rule(r, k)


@pytest.mark.parametrize("k", IT2E_KERNEL + IT2E_SEAL)
def test_it2e_partial_fingerprint_parent_independent(tmp_path_factory, toy_access, monkeypatch, k):
    """T-E3: 같은 θ·같은 주입을 parent 없이(다른 컨텍스트, 평가 키 캐시를 거치지 않음) 부른 대조의 부분 스냅샷 지문 = parent 경로 지문.
    대조도 규칙을 충족한다. (나) 두 결과는 같은 객체가 아니다. 지문 절대값은 단언하지 않는다(같음만)."""
    rec = it2e_record(tmp_path_factory, toy_access)
    rp = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, True, rec)
    rc = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, False, rec)
    assert rc.parent is None and rp.parent is not None
    assert rp.ctx is not rc.ctx and rp.exc is not rc.exc and rp.exc.partial is not rc.exc.partial     # 사례 유효 (나)
    it2e_assert_rule(rc, k)
    assert set(rp.exc.partial.block_versions) == set(rc.exc.partial.block_versions)
    assert rp.exc.partial.fp == rc.exc.partial.fp


@pytest.mark.parametrize("k", [IT2E_KERNEL[0], IT2E_KERNEL[3], IT2E_SEAL[0], IT2E_SEAL[-1]])
def test_it2e_parentless_partial_unchanged(tmp_path_factory, toy_access, monkeypatch, k):
    """T-E7 (동작 보존): parent 없는 평가의 부분 스냅샷은 종래와 같다 -- 기존 규칙(키 = base writer ∪ k 앞 블록, k 이후 없음)이 그대로이고
    같은 입력의 두 독립 실행이 같은 지문을 낸다(결정성). 지문 절대 기준선은 두지 않는다(interface '단언 금지')."""
    rec = it2e_record(tmp_path_factory, toy_access)
    a = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, False, rec)
    b = it2e_run(tmp_path_factory, toy_access, monkeypatch, k, False, rec)
    assert a.ctx is not b.ctx and a.exc.partial is not b.exc.partial
    it2e_assert_rule(a, k)
    assert a.exc.partial.fp == b.exc.partial.fp


def test_it2e_seal_violation_with_parent_keeps_report_fields(tmp_path_factory, r4_access):
    """T-E4: 봉인 위반 경로 + parent -- 부분 스냅샷에 dc_seal_report 필드까지 남고(지우면 red) 커널 밖 writer(ss_dev) 필드는 없다.
    키 = base writer ∪ 평가 12 블록, 지문 = parent 없는 대조 평가와 같다. 위반 θ = test_candidate_failure_recorded_and_cached 와 같은 구성
    (y = 0.1, VGS1 = 1.5 -> 봉인 위반), parent = 봉인된 평가에 손 ss 를 실은 것(커널 밖 writer 필드가 실려 있음)."""
    from .conftest import circuit_cs_pmos_load, theta_r4c, with_hand_ss

    def mk(tag):
        return build_ctx(tmp_path_factory.mktemp(tag), circuit_cs_pmos_load(), r4_access)[2]

    bad = theta_r4c(y=0.1, v1=1.5)
    ctx = mk("it2e_v_p")
    e0 = size_and_seal(ctx, theta_r4c())
    assert e0.sealed is not None                                                          # 전제
    parent = with_hand_ss(e0)
    assert parent.snapshot.column("device", "ss_dev") != ()                               # 전제: 지워질 낡은 필드가 실려 있다
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, bad, parent=parent)
    assert "items" in detail(ei.value)                                                    # 전제: 봉인 보고 위반 경로
    ctx2 = mk("it2e_v_c")
    with pytest.raises(SealViolationError) as ec:
        size_and_seal(ctx2, bad)
    assert "items" in detail(ec.value)
    p, c = ei.value.partial, ec.value.partial
    assert p is not None and c is not None and p is not c and ctx is not ctx2             # (나)
    exp = set(ctx.base.block_versions) | {b.name for b in EVAL11}
    assert set(p.block_versions) == exp and "ss_dev" not in p.block_versions
    rep = [kf for kf, w in p.writers.entries if w == S.dc_seal_report.name]
    assert rep and any(p.column(*kf) != () for kf in rep)                                 # 봉인 보고 필드가 남아 있다
    assert p.column("device", "ss_dev") == ()
    assert p.fp == c.fp
