"""oracle_compare.py -- 합격 정의(사용자 확정 2026-10-07) + 계약 C7(기록·영역·경고), C8(verdict), C9(제약),
W_rel, PMOS 크기 규칙, forced KCL 잔차.

합격 = free 모드에서만: (1) 선언 제약 전부 만족 (2) ID > 0(off_current_A 있으면 > 그 값) 인 MOS 전부 포화
(VDS - VDSAT >= sat_margin_V). 노드·소자·성능의 엔진-SPICE 차이는 기록만(verdict 무관). forced 는 막힘이 없으면
늘 INCOMPLETE, 경고는 forced 에서 |ID_rel|>ID_rel tol 또는 |gm_rel|>gm_rel tol 인 소자.

넷리스트+시뮬레이션은 모듈마다 한 번 만들고 oracle_compare.py 만 입력/판정 설정을 바꿔 여러 번 부른다.
'엔진 예측'은 손계산과 독립 ngspice 넷리스트(conftest.independent_cs) 값으로만 만든다.
"""
import copy

import pytest

from conftest import (CS, all_judges, by_name, cs_input, independent_cs, make_lut, measure,
                      preds_from_independent, rc_input, run_compare, run_netlist, run_simulate)

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
        prefix = self.d / f"c{self.n}"
        p, c = run_compare(inp if inp is not None else self.inp, self.cir, self.sim, prefix,
                           judge=judge, sat_margin=sat_margin)
        assert c is not None, (p.stdout + p.stderr)[-1500:]
        self.last_md = prefix.with_name(prefix.name + ".compare.md")
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


def _margins(ind):
    """독립 .op 의 포화 여유 VDS - VDSAT (M1 ~0.83 V, MP1 ~1.14 V)."""
    return {n: ind[n]["vds"] - ind[n]["vdsat"] for n in ("M1", "MP1")}


# ------------------------------------------------------------------ 합격 정의: free verdict
def test_accept_no_sat_margin_no_constraints_is_incomplete(free_case):
    """C8: sat_margin_V 미설정 -> INCOMPLETE. 기록 칸은 허용오차가 없으니 전부 N/A, 영역은 None."""
    p, c = free_case.cmp()
    assert c["summary"]["verdict"] == "INCOMPLETE"
    js = all_judges(c)
    assert js and all(str(v).startswith("N/A") for _, v in js), [x for x in js if not str(x[1]).startswith("N/A")]
    for d in c["devices"]:
        assert d["region_spice"] is None and "sat_margin" in d["judge"]["region"]
        assert "tol" in d["judge"]["ID"]


def test_accept_all_conducting_saturated_is_pass(free_case, ind):
    """손계산 여유보다 0.05 V 작은 sat_margin -> 두 MOS 모두 포화, 제약 없음 -> PASS(반환 0 은 run test)."""
    m = _margins(ind)
    _, c = free_case.cmp(judge={"sat_margin_V": min(m.values()) - 0.05})
    assert c["summary"]["verdict"] == "PASS", c["summary"]
    acc = c["summary"]["acceptance"]
    assert acc["conducting_devices"] == 2   # 전도 MOS 수(M1, MP1)
    assert acc["unsaturated_conducting"] == [] and acc["constraints_failed"] == []


def test_accept_unsaturated_conducting_mos_fails(free_case, ind):
    """M1 여유(~0.83 V) + 0.05 V 를 요구 -> M1 만 포화 아님(MP1 여유 ~1.14 V) -> FAIL."""
    m = _margins(ind)
    assert m["MP1"] > m["M1"] + 0.1
    _, c = free_case.cmp(judge={"sat_margin_V": m["M1"] + 0.05})
    assert c["summary"]["verdict"] == "FAIL"
    assert c["summary"]["acceptance"]["unsaturated_conducting"] == ["M1"]
    assert by_name(c["devices"], "name", "M1")["region_spice"] == "triode"
    assert by_name(c["devices"], "name", "MP1")["region_spice"] == "sat"


def test_accept_off_device_excluded_from_saturation_check(free_case, ind):
    """off_current_A = 1.2*ID(M1) (< ID(MP1)) -> M1 은 전도 소자가 아니어서 포화 검사에서 빠진다 -> PASS."""
    m = _margins(ind)
    assert ind["MP1"]["id"] > 1.2 * ind["M1"]["id"]
    _, c = free_case.cmp(judge={"sat_margin_V": m["M1"] + 0.05, "off_current_A": 1.2 * ind["M1"]["id"]})
    assert by_name(c["devices"], "name", "M1")["region_spice"] == "off"
    assert c["summary"]["acceptance"]["conducting_devices"] == 1   # MP1 만
    assert c["summary"]["acceptance"]["unsaturated_conducting"] == []
    assert c["summary"]["verdict"] == "PASS"


def test_accept_sat_margin_cli_overrides_input(free_case, ind):
    m = _margins(ind)
    inp = _with(free_case.inp, judge={"sat_margin_V": m["M1"] + 0.05})
    _, c0 = free_case.cmp(inp)
    assert c0["summary"]["verdict"] == "FAIL"                    # 입력 judge 가 쓰였다
    _, c1 = free_case.cmp(inp, sat_margin=m["M1"] - 0.05)
    assert c1["summary"]["verdict"] == "PASS"
    assert c1["summary"]["acceptance"]["sat_margin_V"] == pytest.approx(m["M1"] - 0.05)
    _, c2 = free_case.cmp(inp, judge={"sat_margin_V": m["M1"] - 0.05})  # --judge 파일도 덮어쓴다
    assert c2["summary"]["verdict"] == "PASS"


def test_accept_constraints_decide_with_saturation(free_case, ind):
    """C8/C9: 선언 제약은 판정 대상. 손계산 gain(~22.2 dB), I(vdd) = (VDD - Vout)/RL."""
    g = measure(ind["f"], ind["H"])["dc_gain_db"]
    ivdd = (CS["vdd"] - ind["V"]["nout"]) / CS["rload"]
    sat = min(_margins(ind).values()) - 0.05
    ok = [{"name": "g_ge_lo", "measure": "dc_gain_db", "op": ">=", "limit": g - 1},
          {"name": "g_le_hi", "measure": "dc_gain_db", "op": "<=", "limit": g + 1},
          {"name": "i_le", "measure": "supply_current_A", "op": "<=", "limit": ivdd * 1.1, "rail": "vdd"}]
    bad = [{"name": "g_ge_hi", "measure": "dc_gain_db", "op": ">=", "limit": g + 1},
           {"name": "i_ge", "measure": "supply_current_A", "op": ">=", "limit": ivdd * 1.1, "rail": "vdd"}]
    _, c = free_case.cmp(_with(free_case.inp, acceptance={"constraints": ok}), judge={"sat_margin_V": sat})
    assert {x["name"]: x["judge"] for x in c["constraints"]} == {"g_ge_lo": "PASS", "g_le_hi": "PASS", "i_le": "PASS"}
    assert c["summary"]["verdict"] == "PASS"
    _, c = free_case.cmp(_with(free_case.inp, acceptance={"constraints": ok + bad}), judge={"sat_margin_V": sat})
    got = {x["name"]: x["judge"] for x in c["constraints"]}
    assert got == {"g_ge_lo": "PASS", "g_le_hi": "PASS", "i_le": "PASS", "g_ge_hi": "FAIL", "i_ge": "FAIL"}
    assert sorted(c["summary"]["acceptance"]["constraints_failed"]) == ["g_ge_hi", "i_ge"]
    assert c["summary"]["verdict"] == "FAIL"


def test_accept_constraint_fail_without_sat_margin_is_fail(free_case, ind):
    """C8 순서: 제약 FAIL 이 있으면 sat_margin 미설정이어도 FAIL."""
    g = measure(ind["f"], ind["H"])["dc_gain_db"]
    inp = _with(free_case.inp, acceptance={"constraints": [
        {"name": "g", "measure": "dc_gain_db", "op": ">=", "limit": g + 1}]})
    _, c = free_case.cmp(inp)
    assert c["summary"]["verdict"] == "FAIL"


def test_accept_unmeasured_constraint_is_incomplete(tmp_path):
    """C9: SPICE 값 없는 제약(RC 회로는 |H| 가 처음부터 1 미만이라 UGF/PM None) -> N/A(SPICE 값 없음),
    포화는 만족(다이오드 연결 MD: VDS=VGS, 여유 0) -> INCOMPLETE."""
    inp = rc_input(make_lut(tmp_path / "lut.npz"))
    inp["acceptance"] = {"constraints": [{"name": "u", "measure": "ugf_hz", "op": ">=", "limit": 1.0},
                                         {"name": "p", "measure": "pm_deg", "op": ">=", "limit": 45.0}]}
    _, c = Case(tmp_path, inp, "free").cmp(judge={"sat_margin_V": 0.0})
    for x in c["constraints"]:
        assert x["spice"] is None and x["judge"] == "N/A(SPICE 값 없음)", x
    assert sorted(c["summary"]["acceptance"]["constraints_unmeasured"]) == ["p", "u"]
    assert c["summary"]["acceptance"]["unsaturated_conducting"] == []
    assert c["summary"]["verdict"] == "INCOMPLETE"


def test_accept_record_fails_do_not_change_verdict(free_case, ind):
    """C7: 허용오차 밖 기록(FAIL) 이 여럿이어도 verdict 는 제약+포화로만 -> PASS. 기록 칸에는 FAIL 이 남는다.
    예측 region 이 틀려도(triode 로 예측) verdict 무관."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["nodes"]["nout"] = ind["V"]["nout"] + 0.2
    inp["predictions"]["devices"]["MP1"]["ID"] = ind["MP1"]["id"] * 1.5
    inp["predictions"]["devices"]["M1"]["region"] = "triode"
    inp["predictions"]["metrics"] = [dict(x, value=x["value"] * 2) for x in inp["predictions"]["metrics"]]
    _, c = free_case.cmp(inp, judge={"tolerances": FULL_TOL, "sat_margin_V": min(_margins(ind).values()) - 0.05})
    fails = {k for k, v in all_judges(c) if v == "FAIL"}
    assert {"node:nout", "dev:MP1:ID", "dev:M1:region"} <= fails, fails
    assert any(k.startswith("perf:") for k in fails), fails
    assert c["summary"]["record_counts"]["FAIL"] >= 4
    assert c["summary"]["verdict"] == "PASS"
    assert not c["summary"]["warnings"]   # 경고는 forced 에서만


# ------------------------------------------------------------------ C7: 기록(오차 정의·허용오차 경계)
def test_c7_error_definitions(free_case, ind):
    """abs: SPICE - 예측, rel: (SPICE - 예측)/|예측|."""
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["nodes"]["nout"] = ind["V"]["nout"] + 0.01
    inp["predictions"]["devices"]["M1"]["ID"] = ind["M1"]["id"] / 1.05
    inp["predictions"]["devices"]["M1"]["VGS"] = CS["vin"] - 0.02
    _, c = free_case.cmp(inp)
    assert by_name(c["nodes"], "net", "nout")["err_V"] == pytest.approx(-0.01, abs=1e-5)
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["ID_rel"] == pytest.approx(0.05, rel=1e-3)
    assert m1["VGS_err_V"] == pytest.approx(0.02, abs=1e-9)


@pytest.mark.parametrize("tol,expect", [(0.012, "PASS"), (0.008, "FAIL")])
def test_c7_record_node_abs_tolerance_boundary(free_case, ind, tol, expect):
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["nodes"]["nout"] = ind["V"]["nout"] + 0.01
    _, c = free_case.cmp(inp, judge={"tolerances": {"node_abs_V": tol}})
    assert by_name(c["nodes"], "net", "nout")["judge"] == expect


@pytest.mark.parametrize("tol,expect", [(0.06, "PASS"), (0.04, "FAIL")])
def test_c7_record_rel_tolerance_boundary(free_case, ind, tol, expect):
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["M1"]["ID"] = ind["M1"]["id"] / 1.05   # 오차 +5 %
    inp["predictions"]["devices"]["M1"]["gm"] = ind["M1"]["gm"] * 1.05   # 오차 -4.76 %
    _, c = free_case.cmp(inp, judge={"tolerances": {"ID_rel": tol, "gm_rel": tol}})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["judge"]["ID"] == expect and m1["judge"]["gm"] == expect


def test_c7_record_missing_tol_key_is_na(free_case):
    _, c = free_case.cmp(judge={"tolerances": {"ID_rel": 1e-2}})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["judge"]["ID"] == "PASS"
    assert m1["judge"]["VGS"].startswith("N/A") and "tol" in m1["judge"]["VGS"]


def test_c7_record_fixed_nets_are_na_testbench(free_case):
    _, c = free_case.cmp(judge={"tolerances": {"node_abs_V": 10.0}})
    for net in ("nin", "pb"):
        n = by_name(c["nodes"], "net", net)
        assert n["judge"].startswith("N/A") and "테스트벤치" in n["judge"], n
    assert by_name(c["nodes"], "net", "nout")["judge"] == "PASS"


def test_c7_region_record_compares_prediction(free_case):
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["M1"]["region"] = "triode"
    _, c = free_case.cmp(inp, judge={"sat_margin_V": 0.0})
    assert by_name(c["devices"], "name", "M1")["judge"]["region"] == "FAIL"
    assert by_name(c["devices"], "name", "MP1")["judge"]["region"] == "PASS"


# ------------------------------------------------------------------ W_rel (기록)
@pytest.mark.parametrize("W_decl,rel", [(4e-6, 0.0), (2e-6, 1.0), (8e-6, -0.5)])
def test_w_rel_recorded(tmp_path, W_decl, rel):
    """손계산: W_rel = (finger_w * n_fingers - W)/|W|, finger_w*n = 2 um x 2 = 4 um. 기록 칸만, verdict 무관.
    (넷리스트 meta 가 기하를 나르므로 W 를 바꾼 입력으로 넷리스트부터 다시 만든다)"""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion=False, W=W_decl)
    _, c = Case(tmp_path, inp, "free").cmp(judge={"tolerances": {"W_rel": 0.01}, "sat_margin_V": 0.05})
    m1 = by_name(c["devices"], "name", "M1")
    assert m1["W_from_fingers"] == pytest.approx(4e-6, rel=1e-12)
    assert m1["W_declared"] == pytest.approx(W_decl, rel=1e-12)
    assert m1["W_rel"] == pytest.approx(rel, abs=1e-12)
    assert m1["judge"]["W"] == ("PASS" if rel == 0 else "FAIL")
    assert c["summary"]["verdict"] == "PASS"


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


@pytest.mark.parametrize("sign,expect", [(+1, "PASS"), (-1, "FAIL")])
def test_pmos_prediction_in_magnitude_form(free_case, sign, expect):
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["MP1"].update({"VGS": sign * 1.2, "VSB": sign * 0.3})
    _, c = free_case.cmp(inp, judge={"tolerances": {"VGS_abs_V": 1e-4, "VSB_abs_V": 1e-4}})
    mp = by_name(c["devices"], "name", "MP1")
    assert mp["judge"]["VGS"] == expect and mp["judge"]["VSB"] == expect


# ------------------------------------------------------------------ forced: 진단 모드
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


def test_forced_verdict_always_incomplete(forced_consistent, ind):
    """C8: forced 는 막힘이 없으면 늘 INCOMPLETE -- 제약 FAIL 과 포화 아님이 있어도."""
    g = measure(ind["f"], ind["H"])["dc_gain_db"]
    inp = _with(forced_consistent.inp, acceptance={"constraints": [
        {"name": "g", "measure": "dc_gain_db", "op": ">=", "limit": g + 10}]})
    _, c = forced_consistent.cmp(inp, judge={"sat_margin_V": 5.0})
    assert by_name(c["constraints"], "name", "g")["judge"] == "FAIL"
    assert c["summary"]["verdict"] == "INCOMPLETE"
    _, c = forced_consistent.cmp(judge={"sat_margin_V": 0.0})
    assert c["summary"]["verdict"] == "INCOMPLETE"


def test_forced_warnings_when_device_diff_exceeds_tolerance(forced_consistent, ind):
    """C7: forced 에서 |ID_rel| > ID_rel tol 또는 |gm_rel| > gm_rel tol 인 소자 -> summary.warnings + Markdown 맨 앞."""
    inp = copy.deepcopy(forced_consistent.inp)
    inp["predictions"]["devices"]["MP1"]["ID"] = ind["MP1"]["id"] * 1.5    # ID 오차 -33 %
    inp["predictions"]["devices"]["M1"]["gm"] = ind["M1"]["gm"] * 1.2      # gm 오차 -17 %
    _, c = forced_consistent.cmp(inp, judge={"tolerances": {"ID_rel": 0.05, "gm_rel": 0.05}})
    w = c["summary"]["warnings"]
    assert any("MP1" in str(x) for x in w) and any("M1" in str(x).replace("MP1", "") for x in w), w
    md = forced_consistent.last_md.read_text(encoding="utf-8")
    head = "\n".join(md.splitlines()[:8])
    assert "MP1" in head, head
    assert c["summary"]["verdict"] == "INCOMPLETE"


def test_forced_no_warnings_when_within_tolerance(forced_consistent):
    _, c = forced_consistent.cmp(judge={"tolerances": {"ID_rel": 0.05, "gm_rel": 0.05}})
    assert not c["summary"]["warnings"]


def test_free_mode_never_warns(free_case, ind):
    inp = copy.deepcopy(free_case.inp)
    inp["predictions"]["devices"]["MP1"]["ID"] = ind["MP1"]["id"] * 1.5
    _, c = free_case.cmp(inp, judge={"tolerances": {"ID_rel": 0.05, "gm_rel": 0.05}})
    assert by_name(c["devices"], "name", "MP1")["judge"]["ID"] == "FAIL"
    assert not c["summary"]["warnings"]


def test_kcl_list_is_held_nets_only(forced_consistent):
    _, c = forced_consistent.cmp()
    assert sorted(k["net"] for k in c["kcl_residual"]) == ["nout", "pout"]


def test_kcl_residual_zero_when_prediction_self_consistent(forced_consistent):
    _, c = forced_consistent.cmp(judge={"tolerances": {"kcl_abs_A": 1e-8}})
    for k in c["kcl_residual"]:
        assert abs(k["hold_current_A"]) < 5e-9, k
        assert k["judge"] == "PASS"


def test_kcl_residual_matches_hand_calculation(forced_off):
    """손계산: nout 을 0.8 V 로 묶으면 |잔차| = |(VDD-0.8)/RL - ID_M1(VDS=0.8)|,
    pout 을 0.2 V 로 묶으면 |잔차| = |ID_MP1(VSD=1.3) - 0.2/RP|. ID 는 독립 넷리스트(같은 넷을 이상 전압원으로 묶음).
    부호는 계약에 정의가 없어 크기만 본다. 기록 칸 FAIL 이어도 forced verdict 는 INCOMPLETE."""
    case, ref = forced_off
    _, c = case.cmp(judge={"tolerances": {"kcl_abs_A": 1e-8}})
    exp = {"nout": (CS["vdd"] - VOUT_F) / CS["rload"] - ref["M1"]["id"],
           "pout": ref["MP1"]["id"] - POUT_F / CS["rp"]}
    for net, e in exp.items():
        k = by_name(c["kcl_residual"], "net", net)
        assert abs(e) > 1e-7  # 조건 자체가 잔차를 만든다
        assert abs(k["hold_current_A"]) == pytest.approx(abs(e), rel=2e-3), (net, k, e)
        assert k["judge"] == "FAIL"
    assert c["summary"]["verdict"] == "INCOMPLETE"
