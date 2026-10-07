"""C23 꺼진 소자(Q5 (i)) + 합격 정의 2·3 + C8 verdict.

근거: README C23·C8·C7·합격 정의, schema predictions.devices[].off_current_A / region off 만.
- predicted_conducting: 예측 없음 None, region off False, 아니면 True.
- conduction_check: None -> N/A(예측 없음); False -> N/A(엔진 예측 off); off_current_A 없음 -> N/A(off_current_A 없음);
  SPICE ID 없음 -> N/A(SPICE ID 없음); ID_spice(크기 규칙, 부호 포함) <= off_current_A -> FAIL; 아니면 PASS.
- free verdict: FAIL 하나라도 -> FAIL. N/A(off_current_A 없음/예측 없음/SPICE ID 없음) -> PASS 불가(INCOMPLETE).
- 합격 정의 2 의 전도 문턱: 소자별 off_current_A > judge.off_current_A > 0.

'엔진 예측'과 기대값은 독립 ngspice 넷리스트(conftest.independent_cs)와 손 논리로만 만든다.
"""
import copy

import pytest

from conftest import (CS, NFET, PFET, ZERO_DIFFUSION, by_name, cs_input, independent_cs, make_lut, preds_from_independent,
                      probe, run_compare, run_netlist, run_oracle, run_simulate, run_spice)


def _prep(d, inp, bias="free"):
    p, text, meta = run_netlist(inp, d, bias)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-1500:]
    cir, sim = d / f"t.{bias}.cir", d / f"t.{bias}.sim.json"
    q = run_simulate(cir, sim, d)
    assert q.returncode == 0, (q.stdout + q.stderr)[-1500:]
    return cir, sim


class Case:
    def __init__(self, d, inp, bias="free"):
        self.d, self.inp, self.bias = d, inp, bias
        self.cir, self.sim = _prep(d, inp, bias)
        self.n = 0

    def cmp(self, devs=None, judge=None):
        """predictions.devices 만 바꿔 compare(넷리스트는 예측 소자값을 쓰지 않음 -- nodeset 끔)."""
        self.n += 1
        inp = copy.deepcopy(self.inp)
        if devs is not None:
            inp["predictions"]["devices"] = devs
        p, c = run_compare(inp, self.cir, self.sim, self.d / f"c{self.n}", judge=judge)
        assert c is not None, (p.stdout + p.stderr)[-1500:]
        return c


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


@pytest.fixture(scope="module")
def case(tmp_path_factory, ind):
    d = tmp_path_factory.mktemp("c23_free")
    pr = preds_from_independent(ind)
    inp = cs_input(make_lut(d / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"], preds_devices=pr["devices"])
    return Case(d, inp)


def _devs(ind, **upd):
    """독립 값 예측(전부 region sat, 문턱 0) + 소자별 덮어쓰기. 값 None 이면 그 키 삭제, 소자 값 None 이면 소자 삭제."""
    devs = preds_from_independent(ind)["devices"]
    for name, u in upd.items():
        if u is None:
            devs.pop(name)
            continue
        for k, v in u.items():
            if v is None:
                devs[name].pop(k, None)
            else:
                devs[name][k] = v
    return devs


SAT = {"sat_margin_V": 0.05}   # 손계산 여유 M1 ~0.83 V, MP1 ~1.14 V -> 둘 다 포화


def _row(c, name):
    return by_name(c["devices"], "name", name)


# ------------------------------------------------------------------ 기준선(음성 대조의 짝)
def test_baseline_all_conducting_pass(case, ind):
    c = case.cmp(_devs(ind), SAT)
    assert c["summary"]["verdict"] == "PASS", c["summary"]
    for n in ("M1", "MP1"):
        r = _row(c, n)
        assert r["predicted_conducting"] is True and r["conduction_check"] == "PASS", r
        assert r["off_current_A_pred"] == 0.0 and r["conduction_threshold_A"] == 0.0
    acc = c["summary"]["acceptance"]
    assert acc["off_in_spice"] == [] and acc["conduction_not_evaluated"] == {}


# ------------------------------------------------------------------ FAIL: 예측 전도인데 SPICE ID <= 문턱
@pytest.mark.parametrize("scale,exp", [(1.2, "FAIL"), (0.8, "PASS")])
def test_predicted_conducting_below_threshold_fails(case, ind, scale, exp):
    """M1 문턱 = scale * ID_ind(M1). 1.2 -> SPICE ID <= 문턱 -> FAIL(그 밖은 전부 만족하므로 C23 이 유일한 원인).
    0.8 -> PASS(같은 입력에서 문턱만 바꾼 음성 대조)."""
    thr = scale * ind["M1"]["id"]
    c = case.cmp(_devs(ind, M1={"off_current_A": thr}), SAT)
    r = _row(c, "M1")
    assert r["off_current_A_pred"] == pytest.approx(thr, rel=1e-12)
    assert r["conduction_check"] == exp, r
    acc = c["summary"]["acceptance"]
    assert c["summary"]["verdict"] == exp, c["summary"]
    if exp == "FAIL":
        assert acc["off_in_spice"] == ["M1"]
        # 포화 검사도 소자별 문턱을 쓴다 -> M1 은 전도 소자가 아니어서 포화 검사로 FAIL 난 것이 아님
        assert acc["conducting_devices"] == 1 and acc["unsaturated_conducting"] == []
    else:
        assert acc["off_in_spice"] == [] and acc["conducting_devices"] == 2


def test_run_return_code_1_on_c23_fail(tmp_path, ind):
    pr = preds_from_independent(ind)
    devs = _devs(ind, M1={"off_current_A": 1.2 * ind["M1"]["id"]})
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"], preds_devices=devs)
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    assert res["free"]["summary"]["verdict"] == "FAIL" and p.returncode == 1, (p.stdout + p.stderr)[-1500:]


# ------------------------------------------------------------------ 역방향 전류 -> FAIL
@pytest.fixture(scope="module")
def rev_case(tmp_path_factory, ind):
    """M2(NMOS): drain=gnd, gate=vdd(1.8 V), source=pout. pout 은 RP(10k) 로 gnd 에 물린 양전위 넷이라 M2 가 켜지면
    전류가 pout -> M2 -> gnd 로, 즉 드레인 단자로 '나가는' 방향(ID < 0, 크기 규칙 NMOS 그대로). MP1 은 VDS =
    vsp - V(pout) 가 더 커져 포화 유지, M1 가지는 무관. M2 는 전도 문턱 0 의 포화 검사에서 ID > 0 이 아니므로
    전도 소자가 아니다 -> verdict 에 영향을 줄 수 있는 것은 C23 하나뿐."""
    d = tmp_path_factory.mktemp("c23_rev")
    pr = preds_from_independent(ind)
    inp = cs_input(make_lut(d / "lut.npz"), diffusion="zero", preds_nodes={"nout": pr["nodes"]["nout"]},
                   preds_devices=pr["devices"])
    inp["devices"].append({"name": "M2", "kind": "nmos", "drain": "gnd", "gate": "vdd", "source": "pout",
                           "bulk": "gnd", "L": 0.5e-6, "finger_w": 2e-6, "n_fingers": 1, "W": 2e-6,
                           "diffusion": dict(ZERO_DIFFUSION)})
    return Case(d, inp)


@pytest.fixture(scope="module")
def rev_drain_current(ref_root):
    """독립 넷리스트: rev_case 의 PMOS 가지 + M2 를 손으로 쓰고 M2 드레인에 0 V 감지원(Vsd md 0)을 넣는다.
    드레인 단자로 들어가는 전류 I_D = -i(Vsd)(i(V) = + 단자로 회로에서 들어오는 전류)."""
    c = CS
    body = [f"Vdd vdd 0 DC {c['vdd']}", f"Vsp vsp 0 DC {c['vsp']}", f"Vpb pb 0 DC {c['pb']}",
            f"RP pout 0 {c['rp']}", "Vsd md 0 DC 0", f"XM2 md vdd pout 0 {NFET} l=0.5e-6 w=2e-6"]
    for i in range(c["pn"]):
        body.append(f"XMP1_{i} pout pb vsp vdd {PFET} l={c['pL']} w={c['pfinger_w']}")
    op = run_spice("\n".join(body), ref_root / "ind_rev", ["i(vsd)", probe("nmos", "xm2", "id")])["op"]
    return {"I_D": -op["i(vsd)"], "at_id": op[probe("nmos", "xm2", "id").lower()]}


def test_reverse_current_counts_as_off(rev_case, ind, rev_drain_current):
    """C23: 'ID_spice(크기 규칙, 부호 포함) <= off_current_A -> FAIL(꺼짐 -- 역방향 전류도 여기에 든다)'.
    전제는 독립 넷리스트의 감지원 전류로 확인(I_D < 0). 엔진이 M2 를 전도(sat, 문턱 0)로 예측 -> FAIL."""
    assert rev_drain_current["I_D"] < -1e-6, rev_drain_current      # 역방향 전도(수 uA 이상)
    devs = _devs(ind)
    devs["M2"] = {"region": "sat", "off_current_A": 0.0}
    c = rev_case.cmp(devs, SAT)
    r = _row(c, "M2")
    assert r["predicted_conducting"] is True
    # 크기 규칙(NMOS 그대로, 부호 포함)이면 SPICE ID = 드레인 유입 전류 = 독립 I_D
    assert r["ID_spice"] == pytest.approx(rev_drain_current["I_D"], rel=1e-3), (r["ID_spice"], rev_drain_current)
    assert r["conduction_check"] == "FAIL", r
    assert "M2" in c["summary"]["acceptance"]["off_in_spice"]
    assert c["summary"]["verdict"] == "FAIL", c["summary"]


def test_reverse_device_predicted_off_not_c23(rev_case, ind):
    """같은 회로에서 엔진이 M2 를 off 로 예측 -> C23 대상 아님(N/A(엔진 예측 off)), off_in_spice 에 없음.
    (역방향 전도 소자가 합격 정의 2 의 '전도 MOS' 인지는 README 가 부호를 명시하지 않아 verdict 는 보지 않는다.)"""
    devs = _devs(ind)
    devs["M2"] = {"region": "off", "off_current_A": 0.0}
    c = rev_case.cmp(devs, SAT)
    r = _row(c, "M2")
    assert r["predicted_conducting"] is False and r["conduction_check"] == "N/A(엔진 예측 off)", r
    assert c["summary"]["acceptance"]["off_in_spice"] == []


# ------------------------------------------------------------------ N/A -> INCOMPLETE (조용한 통과 금지)
def test_missing_threshold_incomplete_not_pass(case, ind):
    c = case.cmp(_devs(ind, MP1={"off_current_A": None}), SAT)
    r = _row(c, "MP1")
    assert r["predicted_conducting"] is True and r["conduction_check"] == "N/A(off_current_A 없음)", r
    assert set(c["summary"]["acceptance"]["conduction_not_evaluated"]) == {"MP1"}
    assert c["summary"]["verdict"] == "INCOMPLETE", c["summary"]


def test_judge_scalar_does_not_replace_engine_threshold(case, ind):
    """C23 문턱 = 엔진이 낸 소자별 off_current_A. judge.off_current_A 는 C23 판정을 대신하지 않는다."""
    c = case.cmp(_devs(ind, MP1={"off_current_A": None}), dict(SAT, off_current_A=1e-12))
    assert _row(c, "MP1")["conduction_check"] == "N/A(off_current_A 없음)"
    assert c["summary"]["verdict"] == "INCOMPLETE", c["summary"]


def test_missing_prediction_incomplete(case, ind):
    c = case.cmp(_devs(ind, MP1=None), SAT)
    r = _row(c, "MP1")
    assert r["predicted_conducting"] is None and r["conduction_check"] == "N/A(예측 없음)", r
    assert c["summary"]["acceptance"]["conduction_not_evaluated"].keys() == {"MP1"}
    assert c["summary"]["verdict"] == "INCOMPLETE", c["summary"]


def test_region_off_prediction_no_effect(case, ind):
    """엔진이 M1 을 off 로 예측(SPICE 에서는 켜짐, 포화) -> N/A(엔진 예측 off), verdict 영향 없음(PASS)."""
    c = case.cmp(_devs(ind, M1={"region": "off"}), SAT)
    r = _row(c, "M1")
    assert r["predicted_conducting"] is False and r["conduction_check"] == "N/A(엔진 예측 off)", r
    assert c["summary"]["acceptance"]["conduction_not_evaluated"] == {}
    assert c["summary"]["verdict"] == "PASS", c["summary"]


def test_missing_spice_id_incomplete(tmp_path, ind):
    """PMOS op_probe 를 존재하지 않는 내부 소자로 -> MP1 SPICE ID 없음 -> N/A(SPICE ID 없음) -> INCOMPLETE."""
    pr = preds_from_independent(ind)
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"],
                   preds_devices=pr["devices"])
    inp["process"]["models"]["pmos"]["op_probe"] = "@m.{inst}.mnonexistent[{param}]"
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    r = _row(c, "MP1")
    assert r["ID_spice"] is None and r["conduction_check"] == "N/A(SPICE ID 없음)", r
    assert "MP1" in c["summary"]["acceptance"]["conduction_not_evaluated"]
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


def test_fail_dominates_incomplete(case, ind):
    """M1 꺼짐(FAIL) + MP1 문턱 없음(N/A) -> FAIL."""
    c = case.cmp(_devs(ind, M1={"off_current_A": 1.2 * ind["M1"]["id"]}, MP1={"off_current_A": None}), SAT)
    assert c["summary"]["verdict"] == "FAIL", c["summary"]


# ------------------------------------------------------------------ 합격 정의 2: 전도 문턱 우선순위
def _m1_unsat_margin(ind):
    return ind["M1"]["vds"] - ind["M1"]["vdsat"] + 0.05     # M1 만 비포화가 되는 여유(MP1 여유가 더 큼)


def test_per_device_threshold_beats_judge_in_saturation_check(case, ind):
    """judge.off_current_A = 1 A(두 소자 ID 보다 훨씬 큼)여도 소자별 문턱 0 이 우선 -> 둘 다 전도 소자,
    M1 비포화 -> FAIL."""
    assert ind["MP1"]["vds"] - ind["MP1"]["vdsat"] > _m1_unsat_margin(ind)
    c = case.cmp(_devs(ind), {"sat_margin_V": _m1_unsat_margin(ind), "off_current_A": 1.0})
    assert _row(c, "M1")["conduction_threshold_A"] == 0.0
    acc = c["summary"]["acceptance"]
    assert acc["conducting_devices"] == 2 and acc["unsaturated_conducting"] == ["M1"], acc
    assert c["summary"]["verdict"] == "FAIL"


@pytest.mark.parametrize("judge_off,exp_thr,exp_cond,exp_verdict", [(1.0, 1.0, 0, "PASS"), (None, 0.0, 2, "FAIL")])
def test_threshold_fallback_judge_then_zero(case, ind, judge_off, exp_thr, exp_cond, exp_verdict):
    """소자별 문턱이 없을 때(엔진 예측 off 라 C23 무관): judge.off_current_A, 그것도 없으면 0."""
    devs = _devs(ind, M1={"region": "off", "off_current_A": None}, MP1={"region": "off", "off_current_A": None})
    judge = {"sat_margin_V": _m1_unsat_margin(ind)}
    if judge_off is not None:
        judge["off_current_A"] = judge_off
    c = case.cmp(devs, judge)
    if judge_off is not None:
        assert _row(c, "M1")["conduction_threshold_A"] == exp_thr
    # 문턱 둘 다 없을 때 기록 칸 conduction_threshold_A 의 값(0 또는 None)은 README 가 정하지 않음 -> 동작(0 문턱)만 본다
    assert c["summary"]["acceptance"]["conducting_devices"] == exp_cond
    assert c["summary"]["verdict"] == exp_verdict, c["summary"]


def test_judge_scalar_fallback_excludes_off_device(case, ind):
    """(옛 test_accept_off_device_excluded_from_saturation_check 의 scalar 경로 보존) 엔진이 M1 을 off 로 예측하고
    소자별 문턱이 없으면 judge.off_current_A = 1.2*ID(M1) 가 포화 검사 문턱 -> M1 전도 아님 -> PASS, 영역 off."""
    devs = _devs(ind, M1={"region": "off", "off_current_A": None})
    c = case.cmp(devs, {"sat_margin_V": _m1_unsat_margin(ind), "off_current_A": 1.2 * ind["M1"]["id"]})
    assert _row(c, "M1")["region_spice"] == "off"
    assert c["summary"]["acceptance"]["conducting_devices"] == 1
    assert c["summary"]["verdict"] == "PASS", c["summary"]


def test_c7_region_off_uses_device_threshold(case, ind):
    """C7: 영역 기록의 off 문턱도 소자별 off_current_A 가 우선(judge 없음)."""
    c = case.cmp(_devs(ind, M1={"region": "off", "off_current_A": 1.2 * ind["M1"]["id"]}), SAT)
    assert _row(c, "M1")["region_spice"] == "off"
    assert _row(c, "MP1")["region_spice"] == "sat"


# ------------------------------------------------------------------ forced·iso 기록, forced 는 FAIL 안 냄
def test_forced_and_iso_rows_carry_fields(tmp_path, ind):
    pr = preds_from_independent(ind)
    devs = _devs(ind, M1={"off_current_A": 1.2 * ind["M1"]["id"]})
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"], preds_devices=devs)
    inp["process"]["models"]["nmos"]["polarity"] = "n"
    inp["process"]["models"]["pmos"]["polarity"] = "p"
    p, res = run_oracle(inp, tmp_path / "o", biases=("forced", "iso"), sat_margin=0.05)
    for b in ("forced", "iso"):
        c = res[b]
        assert c is not None, (b, (p.stdout + p.stderr)[-1500:])
        for r in c["devices"]:
            assert {"off_current_A_pred", "predicted_conducting", "conduction_check"} <= set(r), (b, r)
        assert _row(c, "M1")["conduction_check"] == "FAIL", (b, _row(c, "M1"))
        assert c["summary"]["verdict"] == "INCOMPLETE", (b, c["summary"])   # 진단 모드
