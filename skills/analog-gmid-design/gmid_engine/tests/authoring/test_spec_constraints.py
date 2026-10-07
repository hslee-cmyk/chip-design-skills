"""성능 제약 `human.constraints`·`pending_constraints` (gate `constraints`) -- SPEC_CONTRACT 2절 metric_unknown·op_value·
value_and_ref·ref_kind_mismatch·view_*·constraint_duplicate·pending_id_format 행, 3절 ConstraintDecl(judged·view.mode)."""
from __future__ import annotations

import copy

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
TRANSFER = {"ac_excite": {"n_inp": 0.5, "n_inn": -0.5}, "sense_p": "n_outp", "sense_n": None, "sense_mode": "single_ended"}


def _add(sc, **c):
    c.setdefault("source", copy.deepcopy(US))
    sc.human["constraints"].append(c)
    return c


def test_result_order_and_judged(sc):
    """문서 순서 그대로, judged = user_spec True / pending_spice False / reference 는 대상, metric 결정 대기 False."""
    doc = sc.load()
    raw = sc.human["constraints"]
    assert len(doc.constraints) == len(raw)
    by_metric = {c["metric"]: c for c in raw if isinstance(c["metric"], str)}

    def judged_of(c):
        if not isinstance(c["metric"], str):
            return False
        k = c["source"]["kind"]
        if k == "user_spec":
            return True
        if k == "pending_spice":
            return False
        if "value_from_constraint" in c:
            return judged_of(by_metric[c["value_from_constraint"]])
        return True  # fx_spec_ref#ugf_ss_hz 는 user_spec(픽스처 JSON 확인은 아래 test)

    for got, c in zip(doc.constraints, raw):
        if isinstance(c["metric"], str):
            assert got.metric == c["metric"] and got.metric_decision is None
        else:
            assert got.metric is None and got.metric_decision == c["metric"]["pending"] and got.view is None
        assert got.op == c["op"]
        assert got.judged is judged_of(c)
    assert [c.metric for c in doc.judged_constraints] == [c.metric for c in doc.constraints if c.judged]


def test_ref_target_fixture_kind(sc):
    ref = sc.read_spec("fx_spec_ref")
    ugf = [c for c in ref["human"]["constraints"] if c["metric"] == "ugf_ss_hz"][0]
    assert ugf["source"]["kind"] == "user_spec"


def test_view_modes(sc):
    doc = sc.load()
    modes = {c.metric: c.view.mode for c in doc.constraints if c.metric}
    assert modes["gain_ss_db"] == "port"            # transfer metric, view 없음, output 포트 1개
    assert modes["pm_ss_deg"] == "loop"             # loop metric(6절 9번), view 없음 -> feedback·ports 유도 루프 뷰(7a)
    assert modes["parasitic_pm_ss_deg"] == "transfer"
    assert modes["ratio_ss_db"] == "pending"
    assert modes["mismatch_sigma_mv"] == "none"     # view_kind None


def test_transfer_view_projection(sc):
    doc = sc.load()
    v = [c for c in doc.constraints if c.metric == "parasitic_pm_ss_deg"][0].view.transfer
    assert v.ac_excite == tuple(sorted(TRANSFER["ac_excite"].items()))
    assert (v.sense_p, v.sense_n, v.sense_mode) == ("n_outp", None, "single_ended")


def test_differential_view_ok(sc):
    sc.constraint("parasitic_pm_ss_deg")["view"] = {"ac_excite": {"n_inp": 1.0}, "sense_p": "n_outp", "sense_n": "n_mid",
                                                    "sense_mode": "differential"}
    sc.load()


# --- loop(pm_ss_deg)·output_port(rout_ss_ohm) metric 뷰: SPEC_CONTRACT 2절 view_not_applicable·view_excite_not_allowed·
# view_required, 6절 9번 (7a design 2.9·3.1 -- 옛 view_not_defined_yet 규칙은 삭제됐다) ---
ROUT = {"metric": "rout_ss_ohm", "op": "<=", "value": 5000.0}
DIFFERENTIAL = {"ac_excite": {"n_inp": 1.0}, "sense_p": "n_outp", "sense_n": "n_mid", "sense_mode": "differential"}
DECLARED_VIEW_RULE = {"pm_ss_deg": "view_not_applicable", "rout_ss_ohm": "view_excite_not_allowed"}


def _loop_or_port(sc, metric):
    """pm_ss_deg 는 픽스처에 있다(loop). rout_ss_ohm(output_port) 은 제약을 하나 더한다."""
    if metric == "rout_ss_ohm":
        _add(sc, **copy.deepcopy(ROUT))
    return sc.constraint(metric)


@pytest.mark.parametrize("metric", ["pm_ss_deg", "rout_ss_ohm"])
@pytest.mark.parametrize("view", [TRANSFER, DIFFERENTIAL], ids=["transfer_shaped", "differential_shaped"])
def test_declared_transfer_shaped_view_on_loop_output_port(sc, metric, view):
    """loop metric 에 결정 대기 아닌 선언 view -> view_not_applicable(루프 뷰는 유도만), output_port 에 ac_excite 가 있는
    view -> view_excite_not_allowed(감지 전용)."""
    _loop_or_port(sc, metric)["view"] = copy.deepcopy(view)
    sc.reject_only(DECLARED_VIEW_RULE[metric], "constraints")


@pytest.mark.parametrize("metric", ["pm_ss_deg", "rout_ss_ohm"])
def test_loop_output_port_pending_view_accepted(sc, metric):
    """선언 view 는 결정 대기 표지만 받는다 -- 결과 view.mode pending, 그 ID 가 doc.pending 에 모인다(1절)."""
    _loop_or_port(sc, metric)["view"] = {"pending": "MOD7"}
    doc = sc.load()
    got = [c for c in doc.constraints if c.metric == metric][0]
    assert got.view.mode == "pending"
    assert "MOD7" in {p.decision for p in doc.pending}


@pytest.mark.parametrize("metric,mode", [("pm_ss_deg", "loop"), ("rout_ss_ohm", "sense")])
def test_loop_output_port_undeclared_view_is_derived(sc, metric, mode):
    """view 를 적지 않으면 유도 뷰: loop(feedback·ports), output_port 는 감지 뷰(output 포트 1개인 픽스처)."""
    _loop_or_port(sc, metric)
    got = [c for c in sc.load().constraints if c.metric == metric][0]
    assert got.view.mode == mode


@pytest.mark.parametrize("metric", ["pm_ss_deg", "rout_ss_ohm"])
def test_loop_output_port_undeclared_view_two_outputs_required(sc, metric):
    """포트 뷰 규칙: view 없고 output 포트가 1개가 아니면 view_required. 다른 view 없는 제약은 뷰를 채워 hit 1개로 만든다.
    loop 는 β = 1(feedback 빈 list)일 때만 출력 포트가 루프 뷰를 정한다(β 루프는 절단 넷만 쓴다) -- β = 1 로 둔다."""
    sc.human["feedback"]["elements"] = []
    _two_outputs(sc)
    for m in ("gain_ss_db", "ugf_ss_hz"):
        sc.constraint(m)["view"] = copy.deepcopy(TRANSFER)
    if metric == "rout_ss_ohm":
        sc.constraint("pm_ss_deg")["view"] = {"pending": "MOD7"}
    _loop_or_port(sc, metric)
    sc.reject_only("view_required", "constraints")


@pytest.mark.parametrize("metric", ["mismatch_sigma_mv", "power_dc_w", "area_search_m2"])
@pytest.mark.parametrize("view", [TRANSFER, DIFFERENTIAL], ids=["transfer_shaped", "differential_shaped"])
def test_view_not_applicable_none_view_kind(sc, metric, view):
    """view_kind None(픽스처 이름표) metric 에 선언 view -> view_not_applicable."""
    if metric != "mismatch_sigma_mv":
        _add(sc, metric=metric, op="<=", value=1.0)
    sc.constraint(metric)["view"] = copy.deepcopy(view)
    sc.reject_only("view_not_applicable", "constraints")


def test_ratio_view_num_den_transfer(sc):
    """ratio 뷰 {num, den} -- 각 칸을 전달 뷰 모양으로 읽었다(계약은 '{num, den} 필수'만 적음)."""
    sc.constraint("ratio_ss_db")["view"] = {"num": copy.deepcopy(TRANSFER), "den": {
        "ac_excite": {"n_inp": 0.5, "n_inn": 0.5}, "sense_p": "n_outp", "sense_n": None, "sense_mode": "single_ended"}}
    v = [c for c in sc.load().constraints if c.metric == "ratio_ss_db"][0].view
    assert v.mode == "ratio" and v.num is not None and v.den is not None


@pytest.mark.parametrize("metric", ["slew_ss_vps", "GAIN_SS_DB", ""])
def test_metric_unknown(sc, metric):
    _add(sc, metric=metric, op=">=", value=1.0)
    sc.reject_only("metric_unknown", "constraints")


def test_metric_unknown_in_pending_constraints(sc):
    sc.human["pending_constraints"].append({"metric": "slew_ss_vps", "decision": "SP-6"})
    sc.reject_only("metric_unknown", "constraints")


@pytest.mark.parametrize("dec", ["SP6", "later", "", 6])
def test_pending_constraint_decision_format(sc, dec):
    sc.human["pending_constraints"][0]["decision"] = dec
    d = sc.reject()
    if isinstance(dec, str):
        assert sc.rules(d) == ["pending_id_format"]
    else:  # 문자열 아님: 계약이 type / pending_id_format 중 무엇인지 적지 않았다
        assert sc.rules(d) in (["pending_id_format"], ["type"])
    assert d["rejected_gates"] == ("constraints",)


@pytest.mark.parametrize("op", ["==", ">", "<", "=>", "", None])
def test_op_value(sc, op):
    sc.constraint("gain_ss_db")["op"] = op
    sc.reject_only("op_value", "constraints")


def test_value_and_ref_two(sc):
    sc.constraint("gain_ss_db")["value_from_constraint"] = "pm_ss_deg"
    sc.reject_only("value_and_ref", "constraints")


def test_value_and_ref_none(sc):
    del sc.constraint("gain_ss_db")["value"]
    sc.reject_only("value_and_ref", "constraints")


def test_value_and_ref_three(sc):
    c = sc.constraint("mirror_ratio_error_mv")
    c["value"] = 1.0
    c["value_from_file"] = "fx_spec_ref#ugf_ss_hz"
    sc.reject_only("value_and_ref", "constraints")


def test_value_type(sc):
    sc.constraint("gain_ss_db")["value"] = "40"
    sc.reject_only("type", "constraints")


def test_ref_kind_mismatch_value_with_reference(sc):
    sc.constraint("gain_ss_db")["source"] = {"kind": "reference"}
    sc.reject_only("ref_kind_mismatch", "constraints")


def test_ref_kind_mismatch_ref_with_user_spec(sc):
    sc.constraint("mirror_ratio_error_mv")["source"] = copy.deepcopy(US)
    sc.reject_only("ref_kind_mismatch", "constraints")


def test_view_not_applicable_none_metric(sc):
    sc.constraint("mismatch_sigma_mv")["view"] = copy.deepcopy(TRANSFER)
    sc.reject_only("view_not_applicable", "constraints")


def test_view_not_applicable_pending_metric(sc):
    c = [c for c in sc.human["constraints"] if not isinstance(c["metric"], str)][0]
    c["view"] = copy.deepcopy(TRANSFER)
    sc.reject_only("view_not_applicable", "constraints")


def test_pending_view_on_pending_metric_ok(sc):
    c = [c for c in sc.human["constraints"] if not isinstance(c["metric"], str)][0]
    c["view"] = {"pending": "MOD5"}
    sc.load()


def test_view_required_ratio(sc):
    del sc.constraint("ratio_ss_db")["view"]
    sc.reject_only("view_required", "constraints")


def _two_outputs(sc):
    t = sc.read_topo("fx_spec_amp")
    t["ports"]["n_mid"] = {"direction": "output", "role": "aux_output"}
    sc.write_topo(t)
    sc.resync_fp()


def test_view_required_transfer_two_outputs(sc):
    sc.human["feedback"]["elements"] = []   # β = 1: pm_ss_deg 루프 뷰도 포트 뷰 규칙을 따른다(β 루프면 출력 포트와 무관)
    _two_outputs(sc)
    d = sc.reject()
    # view 없는 transfer·loop·output_port 제약 전부(gain_ss_db·ugf_ss_hz transfer, pm_ss_deg loop)
    want = sum(1 for c in sc.human["constraints"] if isinstance(c["metric"], str)
               and c["metric"] in ("gain_ss_db", "parasitic_pm_ss_deg", "ugf_ss_hz", "pm_ss_deg", "rout_ss_ohm")
               and "view" not in c)
    assert want == 3  # 픽스처 JSON 집계: gain_ss_db, pm_ss_deg, ugf_ss_hz
    assert sc.rules(d) == ["view_required"] * want
    assert d["rejected_gates"] == ("constraints",)


def test_explicit_view_ok_with_two_outputs(sc):
    _two_outputs(sc)
    for m in ("gain_ss_db", "parasitic_pm_ss_deg", "ugf_ss_hz"):
        sc.constraint(m)["view"] = copy.deepcopy(TRANSFER)
    sc.constraint("pm_ss_deg")["view"] = {"pending": "MOD7"}  # loop: 선언 view 는 결정 대기 표지만
    sc.load()


@pytest.mark.parametrize("field,val", [("sense_p", "n_ghost"), ("sense_n", "n_ghost")])
def test_view_net_unknown_sense(sc, field, val):
    v = sc.constraint("parasitic_pm_ss_deg")["view"]
    v[field] = val
    if field == "sense_n":
        v["sense_mode"] = "differential"
    sc.reject_only("view_net_unknown", "constraints")


def test_view_net_unknown_excite(sc):
    sc.constraint("parasitic_pm_ss_deg")["view"]["ac_excite"]["n_ghost"] = 0.1
    sc.reject_only("view_net_unknown", "constraints")


@pytest.mark.parametrize("mutate", [
    lambda v: v.update(sense_mode="bogus"),
    lambda v: v.update(sense_mode="differential"),             # differential 인데 sense_n null
    lambda v: v.update(sense_n="n_mid"),                         # single_ended 인데 sense_n 있음
    lambda v: v.update(ac_excite=[["n_inp", 1.0]]),
    lambda v: v.update(ac_excite={"n_inp": "1"}),
    lambda v: v.pop("sense_p"),
    lambda v: v.update(sense_p=3),
])
def test_view_type(sc, mutate):
    mutate(sc.constraint("parasitic_pm_ss_deg")["view"])
    sc.reject_only("type", "constraints")


def test_constraint_duplicate(sc):
    sc.human["constraints"].append(copy.deepcopy(sc.constraint("gain_ss_db")))
    sc.reject_only("constraint_duplicate", "constraints")


def test_same_metric_different_op_not_duplicate(sc):
    _add(sc, metric="gain_ss_db", op="<=", value=80)
    sc.load()


def test_same_metric_different_view_not_duplicate(sc):
    """gain_ss_db(포트 뷰)와 같은 metric·op 에 전달 뷰를 둘 -- view 가 달라 중복 아님(참조 대상이 아닌 metric)."""
    for exc in ({"n_inp": 1.0}, {"n_inn": 1.0}):
        v = copy.deepcopy(TRANSFER)
        v["ac_excite"] = exc
        _add(sc, metric="gain_ss_db", op=">=", value=40, view=v)
    sc.load()


def test_pending_metric_or_view_not_compared(sc):
    sc.human["constraints"].append(copy.deepcopy([c for c in sc.human["constraints"] if not isinstance(c["metric"], str)][0]))
    sc.human["constraints"].append(copy.deepcopy(sc.constraint("ratio_ss_db")))
    sc.load()


def test_pending_spice_allowed_only_here(sc):
    sc.constraint("gain_ss_db")["source"] = {"kind": "pending_spice", "record": "spice later"}
    doc = sc.load()
    assert [c for c in doc.constraints if c.metric == "gain_ss_db"][0].judged is False


def test_ref_judged_follows_target(sc):
    """mirror_ratio_error_mv -> mismatch_sigma_mv(pending_spice) 이므로 judged False, 값은 대상 값."""
    doc = sc.load()
    c = [c for c in doc.constraints if c.metric == "mirror_ratio_error_mv"][0]
    assert c.judged is False
    assert c.value == sc.constraint("mismatch_sigma_mv")["value"]


def test_pending_constraints_result(sc):
    doc = sc.load()
    assert doc.pending_constraints == tuple((p["metric"], p["decision"]) for p in sc.human["pending_constraints"])


def test_constraints_type(sc):
    sc.human["constraints"] = {"gain_ss_db": 40}
    d = sc.reject()
    assert "type" in sc.rules(d) and "constraints" in d["rejected_gates"]


def test_constraint_unknown_key(sc):
    sc.constraint("gain_ss_db")["stage_gain_db"] = 20
    d = sc.reject()
    assert sc.rules(d) in (["unknown_key"], ["legacy_name"])
    assert d["rejected_gates"] == ("constraints",)


def test_all_constraint_hits_collected(sc):
    sc.constraint("gain_ss_db")["op"] = "=="
    sc.constraint("parasitic_pm_ss_deg")["view"]["sense_p"] = "n_ghost"
    _add(sc, metric="slew_ss_vps", op=">=", value=1.0)
    d = sc.reject()
    assert sc.rules(d) == ["op_value", "view_net_unknown", "metric_unknown"]
