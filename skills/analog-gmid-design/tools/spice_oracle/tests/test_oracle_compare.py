"""oracle_compare.py -- 판정 계약 C7(오차·허용오차·영역), C8(verdict), C9(제약), W_rel, PMOS 크기 규칙, forced KCL 잔차.

넷리스트+시뮬레이션은 모듈마다 한 번 만들고 oracle_compare.py 만 입력/판정 설정을 바꿔 여러 번 부른다.
'엔진 예측'은 손계산과 독립 ngspice 넷리스트(conftest.independent_cs) 값으로만 만든다.
"""
import copy
import json
import math

import pytest

from conftest import (CS, all_judges, by_name, cs_input, independent_cs, make_lut, preds_from_independent,
                      run_compare, run_netlist, run_simulate)

PENDING = pytest.mark.acceptance_change_pending

FULL_TOL = {"ID_rel": 1e-3, "VGS_abs_V": 1e-4, "VDS_abs_V": 1e-4, "VSB_abs_V": 1e-4, "gm_rel": 1e-3,
            "gds_rel": 1e-2, "gm_id_rel": 1e-3, "node_abs_V": 1e-4, "W_rel": 1e-9, "kcl_abs_A": 1e-8,
            "dc_gain_db_abs": 0.01, "pm_deg_abs": 0.3, "ugf_hz_rel": 3e-3, "f3db_hz_rel": 1e-4,
            "supply_current_A_rel": 1e-3}


def _prep(d, inp, bias):
    p, text, meta = run_netlist(inp, d, bias)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-1500:]
    cir, sim = d / f"t.{bias}.cir", d / f"t.{bias}.sim.json"
    q = run_simulate(cir, sim, d)
    assert q.returncode == 0, (q.stdout + q.stderr)[-1500:]
    return cir, sim


class Case:
    def __init__(self, d, inp, bias):
        self.d, self.inp, self.bias = d, inp, bias
        self.cir, self.sim = _prep(d, inp, bias)
        self.n = 0

    def cmp(self, inp=None, judge=None, sat_margin=None):
        self.n += 1
        p, c = run_compare(inp if inp is not None else self.inp, self.cir, self.sim, self.d / f"c{self.n}",
                           judge=judge, sat_margin=sat_margin)
        assert c is not None, (p.stdout + p.stderr)[-1500:]
        return p, c


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


@pytest.fixture(scope="module")
def free_case(tmp_path_factory, ind):
    d = tmp_path_factory.mktemp("cmp_free")
    pr = preds_from_independent(ind)
    inp = cs_input(make_lut(d / "lut.npz"), diffusion=False, preds_nodes=pr["nodes"],
                   preds_devices=pr["devices"], metrics=pr["metrics"])
    return Case(d, inp, "free")


def _with(inp, **kw):
    x = copy.deepcopy(inp)
    for k, v in kw.items():
        x[k] = v
    return x


# ------------------------------------------------------------------ C7: 판정 설정 없음 -> 전부 N/A
# ------------------------------------------------------------------ C7: 오차 정의와 경계
def test_c7_error_definitions(free_case, ind):
    """abs: SPICE - 예측, rel: (SPICE - 예측)/|예측|."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["nodes"]["nout"] = ind["V"]["nout"] + 0.01
    inp["predictions"]["devices"]["M1"]["ID"] = ind["M1"]["id"] / 1.05
    inp["predictions"]["devices"]["M1"]["VGS"] = CS["vin"] - 0.02
    _, c = free_case.cmp(inp)
    n = by_name(c["nodes"], "net", "nout")
    assert n["err_V"] == pytest.approx(-0.01, abs=1e-5)
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["ID_rel"] == pytest.approx(0.05, rel=1e-3)
    assert m1["VGS_err_V"] == pytest.approx(0.02, abs=1e-9)


# ------------------------------------------------------------------ C7: 영역
def test_c7_sat_margin_regions(free_case, ind):
    """손계산: M1 의 VDS - VDSAT(독립 값) 보다 작은 여유면 sat, 큰 여유면 triode."""
    vm = ind["M1"]["vds"] - ind["M1"]["vdsat"]
    _, c = free_case.cmp(judge={"sat_margin_V": vm - 0.05})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["region_spice"] == "sat" and m1["judge"]["region"] == "PASS"
    _, c = free_case.cmp(judge={"sat_margin_V": vm + 0.05})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["region_spice"] == "triode" and m1["judge"]["region"] == "FAIL"
    assert c["summary"]["verdict"] == "FAIL"


def test_c7_off_current(free_case, ind):
    _, c = free_case.cmp(judge={"sat_margin_V": 0.0, "off_current_A": ind["M1"]["id"] * 2})
    assert by_name(c["devices"], "name", "M1")["region_spice"] == "off"
    _, c = free_case.cmp(judge={"sat_margin_V": 0.0, "off_current_A": ind["M1"]["id"] / 2})
    assert by_name(c["devices"], "name", "M1")["region_spice"] == "sat"


# ------------------------------------------------------------------ C8
# ------------------------------------------------------------------ C9
def test_c9_constraints(free_case, ind):
    from conftest import measure
    g = measure(ind["f"], ind["H"])["dc_gain_db"]          # ~22.2 dB
    ivdd = (CS["vdd"] - ind["V"]["nout"]) / CS["rload"]
    cons = [{"name": "g_ge_lo", "measure": "dc_gain_db", "op": ">=", "limit": g - 1},
            {"name": "g_ge_hi", "measure": "dc_gain_db", "op": ">=", "limit": g + 1},
            {"name": "g_le_hi", "measure": "dc_gain_db", "op": "<=", "limit": g + 1},
            {"name": "i_le", "measure": "supply_current_A", "op": "<=", "limit": ivdd * 1.1, "rail": "vdd"},
            {"name": "i_ge", "measure": "supply_current_A", "op": ">=", "limit": ivdd * 1.1, "rail": "vdd"}]
    inp = _with(free_case.inp, acceptance={"constraints": cons})
    _, c = free_case.cmp(inp)
    got = {x["name"]: x["judge"] for x in c["constraints"]}
    assert got == {"g_ge_lo": "PASS", "g_ge_hi": "FAIL", "g_le_hi": "PASS", "i_le": "PASS", "i_ge": "FAIL"}
    assert c["summary"]["verdict"] == "FAIL"   # 판정 설정이 없어도 제약 FAIL 은 FAIL


def test_c9_constraint_without_spice_value_is_na(tmp_path):
    from conftest import rc_input
    inp = rc_input(make_lut(tmp_path / "lut.npz"))
    inp["acceptance"] = {"constraints": [{"name": "u", "measure": "ugf_hz", "op": ">=", "limit": 1.0},
                                         {"name": "p", "measure": "pm_deg", "op": ">=", "limit": 45.0}]}
    case = Case(tmp_path, inp, "free")
    _, c = case.cmp()
    for x in c["constraints"]:
        assert x["spice"] is None and x["judge"].startswith("N/A"), x


# ------------------------------------------------------------------ W_rel
# ------------------------------------------------------------------ PMOS 크기 규칙
def test_pmos_magnitude_convention(free_case):
    """손계산: MP1 소스 vsp=1.5, 게이트 pb=0.3, 바디 vdd=1.8 -> VGS=+1.2, VSB=+0.3, VDS=1.5-V(pout),
    ID = V(pout)/RP > 0. NMOS M1 의 VSB = 0."""
    _, c = free_case.cmp()
    mp = by_name(c["devices"], "name", "MP1")
    vpout = by_name(c["nodes"], "net", "pout")["V_spice"]
    assert mp["VGS_spice"] == pytest.approx(CS["vsp"] - CS["pb"], abs=1e-6)
    assert mp["VSB_spice"] == pytest.approx(CS["vdd"] - CS["vsp"], abs=1e-6)
    assert mp["VDS_spice"] == pytest.approx(CS["vsp"] - vpout, abs=1e-5)
    assert mp["ID_spice"] > 0 and mp["ID_spice"] == pytest.approx(vpout / CS["rp"], rel=1e-3)
    assert mp["gm_id_spice"] == pytest.approx(mp["gm_spice"] / mp["ID_spice"], rel=1e-9)
    m1 = by_name(c["devices"], "name", "M1")
    assert abs(m1["VSB_spice"]) < 1e-6 and m1["VGS_spice"] == pytest.approx(CS["vin"], abs=1e-9)


# ------------------------------------------------------------------ forced: KCL 잔차
@pytest.fixture(scope="module")
def forced_consistent(tmp_path_factory, ind):
    d = tmp_path_factory.mktemp("cmp_forced_ok")
    pr = preds_from_independent(ind)
    inp = cs_input(make_lut(d / "lut.npz"), diffusion=False, preds_nodes=pr["nodes"], preds_devices=pr["devices"])
    return Case(d, inp, "forced")


VOUT_F, POUT_F = 0.8, 0.2


@pytest.fixture(scope="module")
def forced_off(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("cmp_forced_off")
    inp = cs_input(make_lut(d / "lut.npz"), diffusion=False, preds_nodes={"nout": VOUT_F, "pout": POUT_F})
    return Case(d, inp, "forced"), independent_cs(ref_root, vout_hold=VOUT_F, pout_hold=POUT_F)


def test_kcl_list_is_held_nets_only(forced_consistent):
    _, c = forced_consistent.cmp()
    assert sorted(k["net"] for k in c["kcl_residual"]) == ["nout", "pout"]


def test_kcl_residual_value_recorded_hand_calc(forced_off):
    """기록값(판정 무관): nout 을 0.8 V 로 묶으면 |잔차| = |(VDD-0.8)/RL - ID_M1(VDS=0.8)|,
    pout 을 0.2 V 로 묶으면 |잔차| = |ID_MP1(VSD=1.3) - 0.2/RP|. ID 는 독립 넷리스트(같은 넷을 이상 전압원으로 묶음).
    부호는 계약에 정의가 없어 크기만 본다."""
    case, ref = forced_off
    _, c = case.cmp()
    exp = {"nout": (CS["vdd"] - VOUT_F) / CS["rload"] - ref["M1"]["id"],
           "pout": ref["MP1"]["id"] - POUT_F / CS["rp"]}
    for net, e in exp.items():
        k = by_name(c["kcl_residual"], "net", net)
        assert abs(e) > 1e-7
        assert abs(k["hold_current_A"]) == pytest.approx(abs(e), rel=2e-3), (net, k, e)


def test_kcl_residual_value_zero_when_self_consistent(forced_consistent):
    _, c = forced_consistent.cmp()
    for k in c["kcl_residual"]:
        assert abs(k["hold_current_A"]) < 5e-9, k


@pytest.mark.parametrize("W_decl,rel", [(2e-6, 1.0), (8e-6, -0.5)])
def test_w_rel_value_recorded(tmp_path, W_decl, rel):
    """기록값(판정 무관): W_rel = (finger_w*n_fingers - W)/|W|, finger_w*n = 2 um x 2 = 4 um."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion=False, W=W_decl)
    _, c = Case(tmp_path, inp, "free").cmp()
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["W_rel"] == pytest.approx(rel, abs=1e-12)


# ====================================================================================================
# [합격 정의 변경 예정(2026-10-07 확정)] -- 현재 README 계약 C7~C9 의 '허용오차로 노드전압·소자값·W·KCL 을
# 판정하고 그것이 verdict 를 정하는' 부분을 확인하는 test 묶음. 사용자 확정(2026-10-07): 합격 = free 모드 성능
# 스펙 만족 + ID>0 인 전 MOS 포화, 둘뿐. 엔진-SPICE 차이는 기록만, 경고는 forced 소자 차이가 계산된 허용오차를
# 넘을 때만. 오라클 코드·계약이 바뀌면 이 묶음은 새 계약으로 다시 쓴다. 선택 실행: -m acceptance_change_pending
# ====================================================================================================

@PENDING
def test_pending_accept_c7_no_judge_everything_na(free_case):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    p, c = free_case.cmp()
    js = all_judges(c)
    assert js and all(str(v).startswith("N/A") for _, v in js), [x for x in js if not str(x[1]).startswith("N/A")]
    assert c["summary"]["counts"]["PASS"] == 0 and c["summary"]["counts"]["FAIL"] == 0
    for d in c["devices"]:
        assert d["region_spice"] is None
        assert "sat_margin" in d["judge"]["region"]
        assert "tol" in d["judge"]["ID"]
    assert by_name(c["nodes"], "net", "nout")["judge"].startswith("N/A")
    assert c["summary"]["verdict"] == "INCOMPLETE"


@PENDING
@pytest.mark.parametrize("tol,expect", [(0.012, "PASS"), (0.008, "FAIL")])
def test_pending_accept_c7_node_abs_tolerance_boundary(free_case, ind, tol, expect):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["nodes"]["nout"] = ind["V"]["nout"] + 0.01
    _, c = free_case.cmp(inp, judge={"tolerances": {"node_abs_V": tol}})
    assert by_name(c["nodes"], "net", "nout")["judge"] == expect


@PENDING
@pytest.mark.parametrize("tol,expect", [(0.06, "PASS"), (0.04, "FAIL")])
def test_pending_accept_c7_rel_tolerance_boundary(free_case, ind, tol, expect):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["M1"]["ID"] = ind["M1"]["id"] / 1.05   # 오차 +5 %
    inp["predictions"]["devices"]["M1"]["gm"] = ind["M1"]["gm"] * 1.05   # 오차 -4.76 %
    _, c = free_case.cmp(inp, judge={"tolerances": {"ID_rel": tol, "gm_rel": tol}})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["judge"]["ID"] == expect and m1["judge"]["gm"] == expect


@PENDING
def test_pending_accept_c7_missing_tol_key_is_na_others_judged(free_case):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    _, c = free_case.cmp(judge={"tolerances": {"ID_rel": 1e-3}})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["judge"]["ID"] == "PASS"
    assert m1["judge"]["VGS"].startswith("N/A") and "tol" in m1["judge"]["VGS"]
    assert by_name(c["nodes"], "net", "nout")["judge"].startswith("N/A")


@PENDING
def test_pending_accept_c7_fixed_nets_are_na_testbench(free_case):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    _, c = free_case.cmp(judge={"tolerances": {"node_abs_V": 10.0}})
    for net in ("nin", "pb"):
        n = by_name(c["nodes"], "net", net)
        assert n["judge"].startswith("N/A") and "테스트벤치" in n["judge"], n
    assert by_name(c["nodes"], "net", "nout")["judge"] == "PASS"


@PENDING
def test_pending_accept_c7_region_judge_compares_prediction(free_case):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["M1"]["region"] = "triode"
    _, c = free_case.cmp(inp, judge={"sat_margin_V": 0.0})
    assert by_name(c["devices"], "name", "M1")["judge"]["region"] == "FAIL"
    assert by_name(c["devices"], "name", "MP1")["judge"]["region"] == "PASS"


@PENDING
def test_pending_accept_cli_judge_file_and_sat_margin_override_input_judge(free_case, ind):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    vm = ind["M1"]["vds"] - ind["M1"]["vdsat"]
    inp = _with(free_case.inp, judge={"tolerances": {"ID_rel": 1e-3}, "sat_margin_V": vm + 0.05})
    inp["predictions"]["devices"]["M1"]["ID"] = ind["M1"]["id"] / 1.01      # 오차 +1 %
    _, c0 = free_case.cmp(inp)
    m1 = by_name(c0["devices"], "name", "M1")
    assert m1["judge"]["ID"] == "FAIL" and m1["region_spice"] == "triode"   # 입력 judge 가 쓰였다
    _, c1 = free_case.cmp(inp, judge={"tolerances": {"ID_rel": 2e-2}}, sat_margin=vm - 0.05)
    m1 = by_name(c1["devices"], "name", "M1")
    assert m1["judge"]["ID"] == "PASS" and m1["region_spice"] == "sat"


@PENDING
def test_pending_accept_c8_all_within_tolerance_no_fail_only_fixed_na(free_case):
    """[합격 정의 변경 예정(2026-10-07 확정)] 예측이 전부 독립 값이고 모든 허용오차·sat_margin 이 있으면 FAIL 이 없고, PASS 가 아닌 판정은
    C7 의 '테스트벤치가 고정'(입력 nin, 게이트 바이어스 pb) 과 예측 없는 레일 넷뿐이다.
    C7(고정 넷 = N/A) + C8(N/A 있으면 INCOMPLETE) 을 글자 그대로 따르면 verdict 는 INCOMPLETE 다.
    (입력 넷 예측은 스키마상 필수라 입력이 있는 회로는 PASS 에 닿지 못한다 -- 보고 대상)"""
    _, c = free_case.cmp(judge={"tolerances": FULL_TOL, "sat_margin_V": 0.05})
    non_pass = [x for x in all_judges(c) if x[1] != "PASS"]
    assert not [x for x in non_pass if x[1] == "FAIL"], non_pass
    fixed = {k for k, v in non_pass if "테스트벤치" in v}
    assert fixed == {"node:nin", "node:pb"}, non_pass
    rest = [x for x in non_pass if "테스트벤치" not in x[1]]
    assert {k for k, _ in rest} <= {"node:vdd", "node:vsp"}, rest
    assert c["summary"]["counts"]["FAIL"] == 0 and c["summary"]["counts"]["PASS"] >= 20
    assert c["summary"]["verdict"] == "INCOMPLETE"


@PENDING
def test_pending_accept_c8_one_fail_makes_fail(free_case, ind):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["MP1"]["ID"] = ind["MP1"]["id"] * 1.5
    _, c = free_case.cmp(inp, judge={"tolerances": FULL_TOL, "sat_margin_V": 0.05})
    assert by_name(c["devices"], "name", "MP1")["judge"]["ID"] == "FAIL"
    assert c["summary"]["verdict"] == "FAIL"
    assert c["summary"]["counts"]["FAIL"] >= 1


@PENDING
def test_pending_accept_c8_counts_match_judges(free_case, ind):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["nodes"]["nout"] = ind["V"]["nout"] + 0.01
    _, c = free_case.cmp(inp, judge={"tolerances": {"ID_rel": 1e-3, "node_abs_V": 1e-9}, "sat_margin_V": 0.05})
    js = [v for _, v in all_judges(c)]
    cnt = c["summary"]["counts"]
    assert cnt["PASS"] == sum(v == "PASS" for v in js)
    assert cnt["FAIL"] == sum(v == "FAIL" for v in js)
    assert cnt["FAIL"] >= 1 and c["summary"]["verdict"] == "FAIL"


@PENDING
@pytest.mark.parametrize("W_decl,rel", [(4e-6, 0.0), (2e-6, 1.0), (8e-6, -0.5)])
def test_pending_accept_w_rel_reported_and_judged(tmp_path, W_decl, rel):
    """[합격 정의 변경 예정(2026-10-07 확정)] 손계산: W_rel = (finger_w * n_fingers - W)/|W|, finger_w*n = 2 um x 2 = 4 um.
    (넷리스트 meta 가 기하를 나르므로 W 를 바꾼 입력으로 넷리스트부터 다시 만든다)"""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion=False, W=W_decl)
    case = Case(tmp_path, inp, "free")
    _, c = case.cmp(judge={"tolerances": {"W_rel": 0.01}})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["W_from_fingers"] == pytest.approx(4e-6, rel=1e-12)
    assert m1["W_declared"] == pytest.approx(W_decl, rel=1e-12)
    assert m1["W_rel"] == pytest.approx(rel, abs=1e-12)
    assert m1["judge"]["W"] == ("PASS" if rel == 0 else "FAIL")


@PENDING
@pytest.mark.parametrize("sign,expect", [(+1, "PASS"), (-1, "FAIL")])
def test_pending_accept_pmos_prediction_in_magnitude_form(free_case, sign, expect):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["MP1"].update({"VGS": sign * 1.2, "VSB": sign * 0.3})
    _, c = free_case.cmp(inp, judge={"tolerances": {"VGS_abs_V": 1e-4, "VSB_abs_V": 1e-4}})
    mp = by_name(c["devices"], "name", "MP1")
    assert mp["judge"]["VGS"] == expect and mp["judge"]["VSB"] == expect


@PENDING
def test_pending_accept_kcl_residual_zero_when_prediction_self_consistent(forced_consistent):
    """[합격 정의 변경 예정(2026-10-07 확정)] 현재 계약(C7~C9)의 허용오차·예측 비교 판정 확인용. 확정 합격 = free 성능 스펙 만족 + ID>0 전 MOS 포화; 엔진-SPICE 차이는 기록만."""
    _, c = forced_consistent.cmp(judge={"tolerances": {"kcl_abs_A": 1e-8}})
    for k in c["kcl_residual"]:
        assert abs(k["hold_current_A"]) < 5e-9, k
        assert k["judge"] == "PASS"


@PENDING
def test_pending_accept_kcl_residual_matches_hand_calculation(forced_off):
    """[합격 정의 변경 예정(2026-10-07 확정)] 손계산: nout 을 0.8 V 로 묶으면 잔차 = (VDD-0.8)/RL - ID_M1(VDS=0.8),
    pout 을 0.2 V 로 묶으면 잔차 = ID_MP1(VSD=1.3) - 0.2/RP. ID 는 독립 넷리스트(같은 넷을 이상 전압원으로 묶음)."""
    case, ref = forced_off
    _, c = case.cmp(judge={"tolerances": {"kcl_abs_A": 1e-8}})
    exp = {"nout": (CS["vdd"] - VOUT_F) / CS["rload"] - ref["M1"]["id"],
           "pout": ref["MP1"]["id"] - POUT_F / CS["rp"]}
    for net, e in exp.items():
        k = by_name(c["kcl_residual"], "net", net)
        assert abs(e) > 1e-7  # 조건 자체가 잔차를 만든다
        assert abs(k["hold_current_A"]) == pytest.approx(abs(e), rel=2e-3), (net, k, e)
        assert k["judge"] == "FAIL"
    assert c["summary"]["verdict"] == "FAIL"
