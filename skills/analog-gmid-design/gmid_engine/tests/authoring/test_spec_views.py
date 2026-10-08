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


# =====================================================================================================================
# [CM 2026-10-08] pm_cm_ss_deg(view_kind cm_loop) -- SPEC_CONTRACT 2절 view_not_applicable·view_shape_not_supported·view_required
# 행(loop·cm_loop), 3절 cm_loop 'view 를 적지 않는다(결정 대기 표지만 허용)'. 감지 넷 구조 유도 규칙 자체는 여기서 확인하지 않는다
# (오케스트레이터 2026-10-08: 유도 규칙이 차동 출력쌍 공통 모드 주입으로 바뀌는 중 -- 규칙과 무관한 거부 조건만).
# 픽스처 fx_spec_amp 는 출력 포트 1개(single_ended_output, 차동 출력쌍 없음) -- 손으로 읽은 JSON.
# =====================================================================================================================

CM = {"metric": "pm_cm_ss_deg", "op": ">=", "value": 60.0}


def _cm(sc, view=None):
    c = _add(sc, **copy.deepcopy(CM))
    if view is not None:
        c["view"] = copy.deepcopy(view)
    return c


def test_cm_loop_required_without_differential_outputs(sc):
    """차동 출력쌍이 없는 회로에 pm_cm_ss_deg(view 없음) -> view_required 하나(SPEC_CONTRACT 2절 view_required cm_loop 행)."""
    _cm(sc)
    sc.reject_only("view_required", "constraints")


@pytest.mark.parametrize("decl", [
    {"sense_p": "n_outp", "sense_mode": "single_ended"},
    {"ac_excite": {"n_inp": 0.5, "n_inn": -0.5}, "sense_p": "n_outp", "sense_n": None, "sense_mode": "single_ended"},
], ids=["sense_shape", "transfer_shape"])
def test_cm_loop_explicit_view_not_applicable(sc, decl):
    """cm_loop metric 에 결정 대기 아닌 view -> view_not_applicable(루프 뷰는 유도만, CM 루프도 같다). 차동 출력쌍 없는
    픽스처라도 명시 view 거부가 먼저 하나만 나온다(view 를 적었으므로 유도를 하지 않는다)."""
    _cm(sc, decl)
    sc.reject_only("view_not_applicable", "constraints")


def test_cm_loop_cut_weights_shape_not_supported(sc):
    """명시 모양 {"cut_weights": …} 는 loop·cm_loop 모두 예약 -> view_shape_not_supported(조용히 무시하지 않음, S3)."""
    _cm(sc, {"cut_weights": {"n_outp": 1.0}})
    sc.reject_only("view_shape_not_supported", "constraints")


def test_cm_loop_pending_view_accepted(sc):
    """결정 대기 표지 view 는 허용(3절 cm_loop '결정 대기 표지만 허용') -> 뷰 mode pending, 결정 ID 그대로."""
    _cm(sc, {"pending": "MOD5"})
    v = _view(sc.load(), "pm_cm_ss_deg")
    assert v.mode == "pending" and v.decision == "MOD5"


# =====================================================================================================================
# [CM 2026-10-08 개정, 0e487b3] cm_loop 유도 = 선언된 차동 출력 포트 쌍의 출력 CM 주입 (SPEC_CONTRACT 3절 cm_loop, metrics 7.11, S-21)
# 기대값(oracle (d)): 3절 문장 'ViewDecl("cm_output", weights=((p, 1/2), (n, 1/2)))(넷순)' 을 손으로 읽은 파일럿 ports role(Vop = _p,
# Vom = _n)에 적용한 리터럴, 차동 출력쌍 없음·SWITCHED_KINDS("switch", "clock") 는 view_required 사유 문자열.
# 입력: library 파일럿 topology 의 연결 키만 옮긴 최소 사본(태그·주석 키는 유도 입력이 아님 -- authoring CONTRACT) 을 test 가 고친다.
# =====================================================================================================================

import json as _json  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

from gmid_engine.authoring import load_topology as _load_topology  # noqa: E402

_LIB = _Path(__file__).resolve().parents[3] / "assets" / "library"
_LIB9 = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
         "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")
_PILOT = "current_reuse_telescopic_ota"
_PILOT_CM = ViewDecl("cm_output", weights=(("Vom", 0.5), ("Vop", 0.5)))        # 넷순 "Vom" < "Vop", 각 1/2
_CONN_KEYS = ("schema_version", "topology_name", "netlist", "supply_nets", "ports", "passive_elements", "ideal_sources",
              "bias_inputs")


def _pilot_mini():
    t = _json.loads((_LIB / (_PILOT + ".topology.json")).read_text(encoding="utf-8"))
    d = {k: copy.deepcopy(t[k]) for k in _CONN_KEYS if k in t}
    d["ports"] = {k: v for k, v in d["ports"].items() if not k.startswith("_")}
    for e in d["passive_elements"] + d.get("ideal_sources", []) + d["netlist"]:
        for k in [k for k in e if k.startswith("_")]:
            del e[k]
    return d


def _dv(tmp_path, doc, name="cmv"):
    p = tmp_path / (name + ".topology.json")
    p.write_text(_json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return default_views(_load_topology(str(p)), ()).cm_loop


def _pas(doc, name):
    return next(e for e in doc["passive_elements"] if e["name"] == name)


def _single_ended(d):
    d["ports"]["Vop"] = {"direction": "output", "role": "single_ended_output"}
    del d["ports"]["Vom"]
    return d


def test_cm_view_library_pilot_and_eight_without_pair():
    """S-21: library 9회로 -- 파일럿만 cm_output(Vom 1/2, Vop 1/2), 나머지 8회로는 사유 문자열(차동 출력쌍 없음)."""
    for name in _LIB9:
        v = default_views(_load_topology(str(_LIB / (name + ".topology.json"))), ()).cm_loop
        if name == _PILOT:
            assert v == _PILOT_CM, v
        else:
            assert isinstance(v, str) and v, (name, v)


def test_cm_view_pilot_minimal_copy_same(tmp_path):
    """입력 확인: 연결 키만 옮긴 사본도 같은 뷰(태그 키를 읽지 않는다)."""
    assert _dv(tmp_path, _pilot_mini()) == _PILOT_CM


@pytest.mark.parametrize("variant", ["drop_R2", "R2_as_capacitor", "ref_resistor_on_sense", "ref_cap_on_sense",
                                     "sense_mos_drain", "triode_mos_average"])
def test_cm_view_independent_of_sense_structure(tmp_path, variant):
    """S-21 '평균 구조가 바뀌어도 뷰는 같다(감지 구조를 보지 않는다)': 감지 넷(Voc) 쪽을 하나씩 고친 사본 -> 같은 cm_output 뷰."""
    d = _pilot_mini()
    if variant == "drop_R2":
        d["passive_elements"] = [e for e in d["passive_elements"] if e["name"] != "R2"]
    elif variant == "R2_as_capacitor":
        _pas(d, "R2")["kind"] = "capacitor"
    elif variant == "ref_resistor_on_sense":
        d["passive_elements"].append({"name": "Rref_t", "kind": "resistor", "terminals": ["Voc", "gnd"]})
    elif variant == "ref_cap_on_sense":
        d["passive_elements"].append({"name": "Cref_t", "kind": "capacitor", "terminals": ["Voc", "gnd"]})
    elif variant == "sense_mos_drain":
        d["netlist"].append({"name": "Mt_x", "kind": "nmos", "drain": "Voc", "gate": "vdd", "source": "gnd"})
    else:   # 평균 저항 둘을 triode MOS 둘로(gate = vdd 레일, channel 이 출력 -> Voc)
        d["passive_elements"] = [e for e in d["passive_elements"] if e["name"] not in ("R1", "R2")]
        d["netlist"] += [{"name": "Mtri1", "kind": "nmos", "drain": "Vom", "gate": "vdd", "source": "Voc"},
                         {"name": "Mtri2", "kind": "nmos", "drain": "Vop", "gate": "vdd", "source": "Voc"}]
    assert _dv(tmp_path, d) == _PILOT_CM


def test_cm_view_name_bijection(tmp_path):
    """S-21 이름 전단사: 모든 넷·소자 이름을 바꾼 사본 -> 출력 두 넷이 새 이름으로 옮겨진 같은 뷰(가중은 새 이름의 넷순)."""
    d = _pilot_mini()
    nets = set(d["supply_nets"]) | set(d["ports"]) | set(d.get("bias_inputs", ()))
    for e in d["netlist"]:
        nets |= {e[k] for k in ("drain", "gate", "source", "bulk") if k in e}
    for e in d["passive_elements"] + d.get("ideal_sources", []):
        nets |= set(e["terminals"])
    order = sorted(nets)
    nm = {n: "z%03d" % (len(order) - i) for i, n in enumerate(order)}     # 원래 이름순을 뒤집는 새 이름
    dev = {e["name"]: "q%03d" % i
           for i, e in enumerate(d["netlist"] + d["passive_elements"] + d.get("ideal_sources", []))}
    for e in d["netlist"]:
        e["name"] = dev[e["name"]]
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = nm[e[k]]
    for e in d["passive_elements"] + d.get("ideal_sources", []):
        e["name"] = dev[e["name"]]
        e["terminals"] = [nm[t] for t in e["terminals"]]
    d["supply_nets"] = [nm[n] for n in d["supply_nets"]]
    d["ports"] = {nm[k]: v for k, v in d["ports"].items()}
    if "bias_inputs" in d:
        d["bias_inputs"] = [nm[n] for n in d["bias_inputs"]]
    assert nm["Vop"] < nm["Vom"]                                   # 넷순이 원래와 뒤집힌 경우
    want = ViewDecl("cm_output", weights=((nm["Vop"], 0.5), (nm["Vom"], 0.5)))
    assert _dv(tmp_path, d) == want


@pytest.mark.parametrize("where,kind", [("passive_elements", "switch"), ("ideal_sources", "clock"),
                                        ("ideal_sources", "switch")])
def test_cm_view_switched_capacitor_explicit_stop(tmp_path, where, kind):
    """S-21·SPEC_CONTRACT 3절: 차동 출력 회로에 kind ∈ SWITCHED_KINDS 선언 -> 명시적 정지 사유(문자열, 차동 출력쌍 없음 사유와 다름)."""
    d = _pilot_mini()
    d.setdefault(where, []).append({"name": "Ksw_t", "kind": kind, "terminals": ["Voc", "gnd"]})
    v = _dv(tmp_path, d)
    assert isinstance(v, str) and v
    single = _dv(tmp_path, _single_ended(_pilot_mini()), "se")
    assert isinstance(single, str) and v != single


@pytest.mark.parametrize("variant", ["single_ended", "only_p", "extra_output"])
def test_cm_view_requires_exactly_one_declared_pair(tmp_path, variant):
    """3절 '차동 출력 포트 쌍(role _p·_n 각 하나, 다른 출력 없음)' 밖 -> 사유 문자열(뷰 없음)."""
    d = _pilot_mini()
    if variant == "single_ended":
        _single_ended(d)
    elif variant == "only_p":
        del d["ports"]["Vom"]
    else:
        d["ports"]["Voc"] = {"direction": "output", "role": "single_ended_output"}
    v = _dv(tmp_path, d)
    assert isinstance(v, str) and v
