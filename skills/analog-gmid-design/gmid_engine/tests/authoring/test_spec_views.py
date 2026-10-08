"""`spec_views` -- 뷰 유도 `default_views(topology, feedback)` 와 7a 뷰 규칙(SPEC_CONTRACT 2절 view_excite_not_allowed·
view_sense_fixed_net·view_shape_not_supported·view_not_applicable·view_required·view_net_unknown, 3절 ViewDecl mode
port/loop/sense + SenseDecl, '로드 한 번에 한 번 유도', constraints_fp 가 feedback 을 따라감, 6절 12~14번, 7절 S3).
기대값은 픽스처 JSON(손으로 읽은 포트 role·단자)과 계약 문장에서 만든다. 피검 함수로 기대값을 만들지 않는다."""
from __future__ import annotations

import copy
import sys
from contextlib import contextmanager

import pytest

from gmid_engine.authoring import BETA_UNITY, SenseDecl, ViewDecl, default_views

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
TRANSFER = {"ac_excite": {"n_inp": 0.5, "n_inn": -0.5}, "sense_p": "n_outp", "sense_n": None, "sense_mode": "single_ended"}
ROUT = {"metric": "rout_ss_ohm", "op": "<=", "value": 5000.0}
PORT_WEIGHTS = (("n_inn", -0.5), ("n_inp", 0.5))         # 픽스처: differential_input_n / _p, |D| = 2 -> ∓½, 넷순
OUT_SENSE = SenseDecl("n_outp", None, "single_ended")     # 출력 포트 1개(single_ended_output)


def _add(sc, **c):
    c.setdefault("source", copy.deepcopy(US))
    sc.human["constraints"].append(c)
    return c


def _rout(sc, view=None):
    c = _add(sc, **copy.deepcopy(ROUT))
    if view is not None:
        c["view"] = copy.deepcopy(view)
    return c


def _view(doc, metric):
    return [c for c in doc.constraints if c.metric == metric][0].view


@contextmanager
def _count(func):
    """func 코드 객체 호출 횟수(sys.setprofile -- 소스 경로를 몰라도 된다)."""
    code = func.__code__
    n = {"calls": 0}
    prev = sys.getprofile()

    def prof(frame, event, arg):
        if event == "call" and frame.f_code is code:
            n["calls"] += 1

    sys.setprofile(prof)
    try:
        yield n
    finally:
        sys.setprofile(prev)


# =====================================================================================================================
# 유도 뷰 (3절)
# =====================================================================================================================

def test_port_view_derived_for_transfer(sc):
    v = _view(sc.load(), "gain_ss_db")
    assert isinstance(v, ViewDecl)
    assert v.mode == "port"
    assert tuple(v.weights) == PORT_WEIGHTS
    assert v.sense == OUT_SENSE


def test_loop_view_beta_unity_equals_port(sc):
    """feedback 빈 list: beta unity, weights·sense 가 port 와 같다(같은 MnaSystem, 6절 12번)."""
    sc.human["feedback"]["elements"] = []
    doc = sc.load()
    v, p = _view(doc, "pm_ss_deg"), _view(doc, "gain_ss_db")
    assert v.mode == "loop" and v.beta == BETA_UNITY == "unity"
    assert tuple(v.weights) == tuple(p.weights) == PORT_WEIGHTS
    assert v.sense == p.sense == OUT_SENSE


def test_sense_view_default_single_output(sc):
    _rout(sc)
    v = _view(sc.load(), "rout_ss_ohm")
    assert v.mode == "sense"
    assert v.sense == OUT_SENSE


@pytest.mark.parametrize("decl,want", [
    ({"sense_p": "n_outp", "sense_mode": "single_ended"}, SenseDecl("n_outp", None, "single_ended")),
    ({"sense_p": "n_outp", "sense_n": None, "sense_mode": "single_ended"}, SenseDecl("n_outp", None, "single_ended")),
    ({"sense_p": "n_mid", "sense_mode": "single_ended"}, SenseDecl("n_mid", None, "single_ended")),
    ({"sense_p": "n_outp", "sense_n": "n_mid", "sense_mode": "differential"}, SenseDecl("n_outp", "n_mid", "differential")),
], ids=["single_no_n", "single_null_n", "other_net", "differential"])
def test_sense_view_declared_shapes_load(sc, decl, want):
    """output_port 선언 view = 감지 전용 {sense_p, sense_n?, sense_mode} -> ViewDecl(mode sense, sense = 그 칸)."""
    _rout(sc, decl)
    v = _view(sc.load(), "rout_ss_ohm")
    assert v.mode == "sense" and v.sense == want


def _diff_outputs(sc):
    t = sc.read_topo("fx_spec_amp")
    t["ports"]["n_outp"] = {"direction": "output", "role": "differential_output_p"}
    t["ports"]["n_mid"] = {"direction": "output", "role": "differential_output_n"}
    sc.write_topo(t)
    sc.resync_fp()


def test_differential_output_pair_port_and_unity_loop(sc):
    """차동 출력쌍(differential_output_p·_n) -> 포트 뷰 sense differential (p, n). β = 1 루프도 같은 sense."""
    _diff_outputs(sc)
    sc.human["feedback"]["elements"] = []
    doc = sc.load()
    want = SenseDecl("n_outp", "n_mid", "differential")
    assert _view(doc, "gain_ss_db").sense == want
    assert _view(doc, "pm_ss_deg").sense == want


def test_differential_outputs_rout_needs_view(sc):
    """output_port 에 view 없고 출력 포트가 1개가 아님 -> view_required(차동쌍이어도)."""
    _diff_outputs(sc)
    _rout(sc)
    sc.reject_only("view_required", "constraints")


def test_default_views_fixed_nets(sc):
    """고정 넷 = 레일 ∪ 입력 포트 넷 ∪ gate 전용 미구동 넷(픽스처: gate 전용 넷 없음 -- n_bias 는 Ibs 단자, n_mid 는 drain)."""
    dv = default_views(sc.topology(), ("Cfb",))
    assert set(dv.fixed_nets) == {"rail_hi", "rail_lo", "n_inp", "n_inn"}
    assert dv.port.mode == "port" and tuple(dv.port.weights) == PORT_WEIGHTS and dv.port.sense == OUT_SENSE
    assert dv.sense.mode == "sense" and dv.sense.sense == OUT_SENSE


def _gate_only_net(sc):
    """레일·입력 포트가 아니고 단자가 전부 MOS gate 인 넷 n_gx 를 만든다(Q6 gate)."""
    t = sc.read_topo("fx_spec_amp")
    t["netlist"].append({"name": "Q6", "kind": "nmos", "drain": "n_outp", "gate": "n_gx", "source": "rail_lo"})
    # gate 전용 넷은 bias_inputs 선언이 필요하다(authoring CONTRACT 9절 gate_only_undeclared, 2026-10-08 Q6).
    t["bias_inputs"] = ["n_gx"]
    sc.write_topo(t)
    sc.resync_fp()


def test_gate_only_net_is_fixed(sc):
    _gate_only_net(sc)
    assert "n_gx" in default_views(sc.topology(), ("Cfb",)).fixed_nets


# =====================================================================================================================
# 로드 한 번에 한 번 유도, 지문 (3절)
# =====================================================================================================================

def test_default_views_called_once_per_load(sc):
    """view 없는 transfer·loop·output_port 제약이 여럿이어도 default_views 는 로드 한 번에 한 번.
    (value_from_file 대상 spec 은 자기 로드를 따로 하므로 그 제약은 값으로 바꿔 둔다.)"""
    u = sc.constraint("ugf_ss_hz")
    del u["value_from_file"]
    u["value"] = 1e6
    u["source"] = copy.deepcopy(US)
    _rout(sc)
    with _count(default_views) as n:
        sc.load()
    assert n["calls"] == 1


def _fps(doc):
    return dict(doc.section_fps)


def test_feedback_change_moves_constraints_fp_with_loop_constraint(sc):
    """유도된 루프 뷰가 ViewDecl 에 들어가므로 feedback 만 바꿔도(loop 제약 있음) feedback_fp 와 constraints_fp 가 바뀐다."""
    _add_passive_cq(sc)
    base = sc.load()
    sc.human["feedback"]["elements"] = ["Cfb", "Cq"]
    other = sc.load()
    a, b = _fps(base), _fps(other)
    assert {k for k in a if a[k] != b[k]} == {"feedback_fp", "constraints_fp"}
    assert _view(other, "pm_ss_deg") != _view(base, "pm_ss_deg")


def test_feedback_change_without_derived_loop_view_keeps_constraints_fp(sc):
    """loop 제약의 view 가 결정 대기 선언(유도 아님)이면 feedback 변경은 constraints_fp 를 옮기지 않는다
    (constraints_fp 가 feedback 을 따라가는 이유 = 유도 내용이 ViewDecl 에 들어가기 때문, 3절)."""
    _add_passive_cq(sc)
    sc.constraint("pm_ss_deg")["view"] = {"pending": "MOD7"}
    base = sc.load()
    sc.human["feedback"]["elements"] = ["Cfb", "Cq"]
    other = sc.load()
    a, b = _fps(base), _fps(other)
    assert {k for k in a if a[k] != b[k]} == {"feedback_fp"}


def _add_passive_cq(sc):
    t = sc.read_topo("fx_spec_amp")
    t["passive_elements"].append({"name": "Cq", "kind": "capacitor", "terminals": ["n_outp", "n_inp"]})
    sc.write_topo(t)
    sc.human["element_values"]["Cq"] = {"value_farad": 1e-13, "source": copy.deepcopy(US)}
    sc.resync_fp()


def test_derivation_deterministic(sc):
    _rout(sc)
    a, b = sc.load(), sc.load()
    assert a.spec_fp == b.spec_fp
    assert [c.view for c in a.constraints] == [c.view for c in b.constraints]


# =====================================================================================================================
# 거부 규칙 (2절) -- 규칙마다 원본 한 곳만 깨서 그 hit 하나
# =====================================================================================================================

@pytest.mark.parametrize("extra", [{"n_inp": 1.0}, {}], ids=["one_net", "empty_map"])
def test_view_excite_not_allowed(sc, extra):
    """output_port view 에 ac_excite 키 -> view_excite_not_allowed(감지 전용, 여기는 DEC-66 고정)."""
    _rout(sc, {"ac_excite": extra, "sense_p": "n_outp", "sense_mode": "single_ended"})
    sc.reject_only("view_excite_not_allowed", "constraints")


@pytest.mark.parametrize("decl", [
    {"sense_p": "rail_lo", "sense_mode": "single_ended"},
    {"sense_p": "rail_hi", "sense_mode": "single_ended"},
    {"sense_p": "n_inp", "sense_mode": "single_ended"},
    {"sense_p": "n_inn", "sense_mode": "single_ended"},
    {"sense_p": "n_outp", "sense_n": "n_inp", "sense_mode": "differential"},
    {"sense_p": "n_outp", "sense_n": "rail_lo", "sense_mode": "differential"},
], ids=["rail_lo", "rail_hi", "input_p", "input_n", "sense_n_input", "sense_n_rail"])
def test_view_sense_fixed_net(sc, decl):
    _rout(sc, decl)
    sc.reject_only("view_sense_fixed_net", "constraints")


def test_view_sense_fixed_net_gate_only(sc):
    _gate_only_net(sc)
    _rout(sc, {"sense_p": "n_gx", "sense_mode": "single_ended"})
    sc.reject_only("view_sense_fixed_net", "constraints")


def test_sense_on_non_fixed_driven_net_ok(sc):
    """레일·입력·gate 전용이 아닌 넷(n_mid, n_tail)은 감지 가능."""
    for net in ("n_mid", "n_tail"):
        sc.human["constraints"] = [c for c in sc.human["constraints"] if c.get("metric") != "rout_ss_ohm"]
        _rout(sc, {"sense_p": net, "sense_mode": "single_ended"})
        assert _view(sc.load(), "rout_ss_ohm").sense == SenseDecl(net, None, "single_ended")


@pytest.mark.parametrize("weights", [{"n_inn": 1.0}, {"n_inn": -0.5, "n_inp": 0.5}])
def test_view_shape_not_supported_cut_weights(sc, weights):
    """loop metric 의 명시 모양 {"cut_weights": …} 는 예약(S3) -- 조용히 무시하지 않고 거부."""
    sc.constraint("pm_ss_deg")["view"] = {"cut_weights": weights}
    sc.reject_only("view_shape_not_supported", "constraints")


def test_view_shape_not_supported_beta_unity(sc):
    sc.human["feedback"]["elements"] = []
    sc.constraint("pm_ss_deg")["view"] = {"cut_weights": {"n_inp": 0.5, "n_inn": -0.5}}
    sc.reject_only("view_shape_not_supported", "constraints")


@pytest.mark.parametrize("decl", [
    {"sense_p": "n_outp", "sense_mode": "single_ended"},
    {"sense_p": "n_outp", "sense_n": None, "sense_mode": "single_ended"},
], ids=["sense_shape", "sense_shape_null_n"])
def test_view_not_applicable_loop_sense_shape(sc, decl):
    """loop metric 에 결정 대기 아닌 view(감지 모양) -> view_not_applicable(루프 뷰는 유도만)."""
    sc.constraint("pm_ss_deg")["view"] = copy.deepcopy(decl)
    sc.reject_only("view_not_applicable", "constraints")


def _explicit_transfer_views(sc):
    for m in ("gain_ss_db", "ugf_ss_hz"):
        sc.constraint(m)["view"] = copy.deepcopy(TRANSFER)


def test_view_required_beta_loop_cut_role_outside_vocabulary(sc):
    """β 루프의 절단 넷(n_inn) role 이 가중 어휘 밖 -> view_required. 전달 metric 은 명시 view 로 두어 hit 1개."""
    t = sc.read_topo("fx_spec_amp")
    t["ports"]["n_inn"] = {"direction": "input", "role": "aux_input"}
    sc.write_topo(t)
    sc.resync_fp()
    _explicit_transfer_views(sc)
    sc.reject_only("view_required", "constraints")


def test_view_required_unity_two_single_inputs(sc):
    """β = 1 에 view 없음 + 입력 포트가 차동쌍 1개·단일 1개가 아님(단일 2개) -> view_required."""
    t = sc.read_topo("fx_spec_amp")
    t["ports"]["n_inp"] = {"direction": "input", "role": "single_ended_input"}
    t["ports"]["n_inn"] = {"direction": "input", "role": "single_ended_input"}
    sc.write_topo(t)
    sc.resync_fp()
    sc.human["feedback"]["elements"] = []
    _explicit_transfer_views(sc)
    sc.reject_only("view_required", "constraints")


def test_view_required_transfer_input_shape(sc):
    """6절 12번: transfer 기본 포트 뷰에도 입력 포트 모양 검사 -- 단일 입력 2개면 view 없는 gain_ss_db·ugf_ss_hz 가 hit."""
    t = sc.read_topo("fx_spec_amp")
    t["ports"]["n_inp"] = {"direction": "input", "role": "single_ended_input"}
    t["ports"]["n_inn"] = {"direction": "input", "role": "single_ended_input"}
    sc.write_topo(t)
    sc.resync_fp()
    sc.constraint("pm_ss_deg")["view"] = {"pending": "MOD7"}
    d = sc.reject()
    assert sc.rules(d) == ["view_required", "view_required"]
    assert d["rejected_gates"] == ("constraints",)


def test_beta_loop_ignores_output_count(sc):
    """β 루프(feedback 비지 않음)는 절단 넷만 쓴다 -- 출력 포트가 2개여도 pm_ss_deg 는 view_required 가 아니다."""
    t = sc.read_topo("fx_spec_amp")
    t["ports"]["n_mid"] = {"direction": "output", "role": "aux_output"}
    sc.write_topo(t)
    sc.resync_fp()
    _explicit_transfer_views(sc)
    v = _view(sc.load(), "pm_ss_deg")
    assert v.mode == "loop" and tuple(v.cuts) == (("Cfb", "n_inn"),)


@pytest.mark.parametrize("field", ["sense_p", "sense_n"])
def test_view_net_unknown_sense_view(sc, field):
    decl = {"sense_p": "n_outp", "sense_mode": "single_ended"}
    if field == "sense_n":
        decl.update(sense_n="n_ghost", sense_mode="differential")
    else:
        decl["sense_p"] = "n_ghost"
    _rout(sc, decl)
    sc.reject_only("view_net_unknown", "constraints")


@pytest.mark.parametrize("decl", [
    {"sense_p": "n_outp", "sense_mode": "bogus"},
    {"sense_p": "n_outp", "sense_mode": "differential"},                     # differential 인데 sense_n 없음
    {"sense_p": "n_outp", "sense_n": "n_mid", "sense_mode": "single_ended"},  # single_ended 인데 sense_n 있음
    {"sense_p": 3, "sense_mode": "single_ended"},
    {"sense_mode": "single_ended"},
], ids=["mode_vocab", "diff_without_n", "single_with_n", "sense_p_type", "no_sense_p"])
def test_sense_view_type(sc, decl):
    """2절 type: 값 자리·모드 키 개수·sense_mode 어휘 위반."""
    _rout(sc, decl)
    sc.reject_only("type", "constraints")


def test_pending_sense_view_accepted(sc):
    _rout(sc, {"pending": "MOD7"})
    v = _view(sc.load(), "rout_ss_ohm")
    assert v.mode == "pending" and v.decision == "MOD7"
