"""C19 진단(기록만): forced `diagnosis`(KCL 넷 대 tol_I, 게이트 공유 넷 dVGS 퍼짐) + free `diagnosis_free` 분류.

손계산: tol_I(넷) = sum |ID_pred| x tol_ID_rel (드레인/소스가 그 넷에 물린 소자), |KCL 잔차| 는
|I_R - ID_spice|(독립 넷리스트에서 같은 넷을 이상 전압원으로 고정), dVGS = (ID_spice - ID_pred)/gm_pred.
분류: free FAIL 이 아니면 not_applicable, forced 없음/막힘 -> unknown, dc_consistent True -> boundary_condition,
False -> engine_dc_inconsistent, None -> unknown.
"""
import copy

import pytest

from conftest import CS, by_name, cs_input, independent_cs, make_lut, preds_from_independent, run_oracle

VOUT, POUT = 0.8, 0.2
TOL = 0.01


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


@pytest.fixture(scope="module")
def held(ref_root):
    return independent_cs(ref_root, vout_hold=VOUT, pout_hold=POUT)


def _devs(src, tols):
    # [C23 조정] off_current_A 0 = 옛 'ID > 0 이면 전도' 규칙을 명시(없으면 free 가 PASS 대신 INCOMPLETE)
    d = {n: {"ID": src[n]["id"], "gm": src[n]["gm"], "off_current_A": 0.0} for n in ("M1", "MP1")}
    for n, t in tols.items():
        d[n]["tol"] = {"ID_rel": t}
    return d


# ------------------------------------------------------------------ forced diagnosis: KCL
def test_kcl_nets_against_tol_I_hand(tmp_path, held):
    """nout=0.8 V, pout=0.2 V 로 고정. ID 예측 = 그 고정에서의 독립 ID(소자 자체는 정확) -> 잔차는 R 전류와의 차.
    잔차: nout = |(VDD-0.8)/RL - ID_M1| ~ 1.4 uA, pout = |ID_MP1 - 0.2/RP|."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": VOUT, "pout": POUT},
                   preds_devices=_devs(held, {"M1": TOL, "MP1": TOL}))
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced",))
    dg = res["forced"]["diagnosis"]
    res_hand = {"nout": abs((CS["vdd"] - VOUT) / CS["rload"] - held["M1"]["id"]),
                "pout": abs(held["MP1"]["id"] - POUT / CS["rp"])}
    tol_hand = {"nout": held["M1"]["id"] * TOL, "pout": held["MP1"]["id"] * TOL}
    for net in ("nout", "pout"):
        k = by_name(dg["kcl_nets"], "net", net)
        assert abs(k["hold_current_A"]) == pytest.approx(res_hand[net], rel=5e-3)
        assert k["tol_I_sum_A"] == pytest.approx(tol_hand[net], rel=1e-9)
        assert k["within"] is (res_hand[net] <= tol_hand[net])
    exceeding = sorted(n for n in res_hand if res_hand[n] > tol_hand[n])
    assert exceeding, "조건 점검: 최소 한 넷은 tol_I 를 넘어야 한다"
    assert sorted(dg["kcl_nets_exceeding"]) == exceeding
    assert dg["dc_consistent"] is False
    assert res["forced"]["summary"]["verdict"] == "INCOMPLETE"


def test_kcl_net_with_untoleranced_device_not_judged(tmp_path, held):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": VOUT, "pout": POUT},
                   preds_devices=_devs(held, {"M1": TOL}))
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced",))
    dg = res["forced"]["diagnosis"]
    assert by_name(dg["kcl_nets"], "net", "pout")["within"] is None
    assert dg["kcl_nets_judged"] == 1


def test_dc_consistent_true_when_self_consistent(tmp_path, ind):
    pr = preds_from_independent(ind)
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes=pr["nodes"],
                   preds_devices=_devs(ind, {"M1": TOL, "MP1": TOL}))
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced",))
    dg = res["forced"]["diagnosis"]
    assert dg["kcl_nets_judged"] == 2 and dg["kcl_nets_exceeding"] == [] and dg["dc_consistent"] is True


def test_dc_consistent_none_without_any_tol(tmp_path, held):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": VOUT, "pout": POUT},
                   preds_devices=_devs(held, {}))
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced",))
    dg = res["forced"]["diagnosis"]
    assert dg["kcl_nets_judged"] == 0 and dg["dc_consistent"] is None


# ------------------------------------------------------------------ forced diagnosis: 게이트 공유 넷
def test_gate_shared_nets_dvgs_and_order(tmp_path, held):
    """M2(nmos, n=1)가 M1 과 게이트 nin 을, MP2(pmos, n=1)가 MP1 과 게이트 pb 를 공유. 같은 finger 기하이므로
    finger 하나의 ID = 독립 총합 / n. 예측 ID 를 소자마다 다르게 틀려 dVGS 를 손계산한다."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": VOUT, "pout": POUT})
    inp["devices"] += [
        {"name": "M2", "kind": "nmos", "drain": "nout", "gate": "nin", "source": "gnd", "bulk": "gnd",
         "L": CS["L"], "finger_w": CS["finger_w"], "n_fingers": 1, "W": CS["finger_w"]},
        {"name": "MP2", "kind": "pmos", "drain": "pout", "gate": "pb", "source": "vsp", "bulk": "vdd",
         "L": CS["pL"], "finger_w": CS["pfinger_w"], "n_fingers": 1, "W": CS["pfinger_w"]}]
    id_sp = {"M1": held["M1"]["id"], "M2": held["M1"]["id"] / CS["n"],
             "MP1": held["MP1"]["id"], "MP2": held["MP1"]["id"] / CS["pn"]}
    gm = {"M1": held["M1"]["gm"], "M2": held["M1"]["gm"] / CS["n"],
          "MP1": held["MP1"]["gm"], "MP2": held["MP1"]["gm"] / CS["pn"]}
    scale = {"M1": 1.0, "M2": 0.9, "MP1": 1.0, "MP2": 0.5}
    inp["predictions"]["devices"] = {n: {"ID": id_sp[n] * scale[n], "gm": gm[n]} for n in id_sp}
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced",))
    gs = res["forced"]["diagnosis"]["gate_shared_nets"]
    assert [g["net"] for g in gs] == ["pb", "nin"], gs          # 퍼짐 큰 순
    for g, members in zip(gs, (("MP1", "MP2"), ("M1", "M2"))):
        hand = {n: (id_sp[n] - id_sp[n] * scale[n]) / gm[n] for n in members}
        for n in members:
            assert g["dVGS_eq_V"][n] == pytest.approx(hand[n], rel=5e-3, abs=2e-6), (n, g)
        assert g["spread_V"] == pytest.approx(max(hand.values()) - min(hand.values()), rel=5e-3, abs=2e-6)


# ------------------------------------------------------------------ free diagnosis_free 분류
def _run_pair(tmp_path, preds_nodes, devs, sat, biases=("free", "forced")):
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes=preds_nodes, preds_devices=devs)
    p, res = run_oracle(inp, tmp_path / "o", biases=biases, sat_margin=sat)
    return p, res


def test_free_fail_with_consistent_forced_is_boundary_condition(tmp_path, ind):
    pr = preds_from_independent(ind)
    p, res = _run_pair(tmp_path, pr["nodes"], _devs(ind, {"M1": TOL, "MP1": TOL}), sat=1.0)  # M1 여유 ~0.83 < 1
    assert res["free"]["summary"]["verdict"] == "FAIL"
    assert res["forced"]["diagnosis"]["dc_consistent"] is True
    assert res["free"]["diagnosis_free"]["classification"] == "boundary_condition"


def test_free_fail_with_inconsistent_forced_is_engine_dc_inconsistent(tmp_path, held):
    p, res = _run_pair(tmp_path, {"nout": VOUT, "pout": POUT}, _devs(held, {"M1": TOL, "MP1": TOL}), sat=1.0)
    assert res["free"]["summary"]["verdict"] == "FAIL"
    assert res["free"]["diagnosis_free"]["classification"] == "engine_dc_inconsistent"


def test_free_fail_without_tol_is_unknown(tmp_path, held):
    p, res = _run_pair(tmp_path, {"nout": VOUT, "pout": POUT}, _devs(held, {}), sat=1.0)
    assert res["free"]["summary"]["verdict"] == "FAIL"
    assert res["free"]["diagnosis_free"]["classification"] == "unknown"


def test_free_fail_without_forced_run_is_unknown(tmp_path, held):
    """free 만 돌리면 diagnosis_free 는 없거나 unknown."""
    p, res = _run_pair(tmp_path, {"nout": VOUT, "pout": POUT}, _devs(held, {"M1": TOL}), sat=1.0, biases=("free",))
    df = res["free"].get("diagnosis_free")
    assert df is None or df["classification"] == "unknown"


def test_free_not_fail_is_not_applicable(tmp_path, held):
    p, res = _run_pair(tmp_path, {"nout": VOUT, "pout": POUT}, _devs(held, {"M1": TOL, "MP1": TOL}), sat=0.05)
    assert res["free"]["summary"]["verdict"] == "PASS"
    assert res["free"]["diagnosis_free"]["classification"] == "not_applicable"
