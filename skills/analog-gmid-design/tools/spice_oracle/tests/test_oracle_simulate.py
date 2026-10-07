"""oracle_simulate.py -- .op/.ac 추출이 손계산 및 독립 ngspice 넷리스트와 맞는가 (측정 정의, C10, finger m 의미).

독립 기준: conftest.independent_cs 는 finger 마다 인스턴스 하나(w=finger_w, m/nf 없음)를 병렬로 둔 손 넷리스트를
ngspice 에 직접 돌린다. 오라클은 X 한 줄 m=n_fingers 로 같은 회로를 만든다 -- 둘이 같아야 finger 규칙이 물리적으로
'finger_w 폭 n 개 병렬'이라는 뜻이 된다. 독립 측은 입력을 이상 AC 원으로 직접 구동한다(오라클의 choke 1e12 H,
결합 C 1 F 는 fstart 0.01 Hz 에서 각각 6e10 Ohm, 16 Ohm 이라 영향 < 1e-5 dB).
"""
import json
import math

import numpy as np
import pytest

from conftest import (CS, FB, RC, ac_grid, cs_input, fb_input, fb_loop_gain, fb_open_loop, independent_cs,
                      independent_fb, make_lut, measure, rc_input, require_spice, run_netlist, run_simulate)


def _simulate(inp, d, bias="free"):
    p, text, meta = run_netlist(inp, d, bias)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-1500:]
    cir = d / f"t.{bias}.cir"
    sim = d / f"t.{bias}.sim.json"
    q = run_simulate(cir, sim, d)
    assert q.returncode == 0 and sim.exists(), (q.stdout + q.stderr)[-1500:]
    return json.loads(sim.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def cs_sim(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("sim_cs")
    inp = cs_input(make_lut(d / "lut.npz"), diffusion="zero")
    return _simulate(inp, d), independent_cs(ref_root)


@pytest.fixture(scope="module")
def rc_sim(tmp_path_factory):
    require_spice()
    d = tmp_path_factory.mktemp("sim_rc")
    return _simulate(rc_input(make_lut(d / "lut.npz")), d)


# ------------------------------------------------------------------ .op
def test_op_nodes_match_independent(cs_sim):
    s, ind = cs_sim
    assert s["nodes"]["nout"] == pytest.approx(ind["V"]["nout"], abs=2e-6)
    assert s["nodes"]["pout"] == pytest.approx(ind["V"]["pout"], abs=2e-6)
    assert s["nodes"]["nin"] == pytest.approx(CS["vin"], abs=1e-9)
    assert s["nodes"]["pb"] == pytest.approx(CS["pb"], abs=1e-9)


@pytest.mark.parametrize("dev", ["M1", "MP1"])
def test_op_device_values_match_parallel_fingers(cs_sim, dev):
    """X 한 줄 m=n 의 @id/gm/gds 가 finger 인스턴스 n 개 병렬의 총합과 같다."""
    s, ind = cs_sim
    got, ref = s["devices"][dev], ind[dev]
    for q in ("id", "gm", "gds"):
        assert got[q] == pytest.approx(ref[q], rel=2e-4), q
    for q in ("vgs", "vds", "vbs", "vdsat"):
        assert got[q] == pytest.approx(ref[q], abs=2e-6), q


def test_op_hand_kcl_nmos_load(cs_sim):
    """손계산: R 부하 KCL -> ID(M1) = (VDD - V(nout)) / RL."""
    s, _ = cs_sim
    assert s["devices"]["M1"]["id"] == pytest.approx((CS["vdd"] - s["nodes"]["nout"]) / CS["rload"], rel=1e-4)


def test_op_hand_rail_current(cs_sim):
    """손계산: vdd 가 공급하는 전류 = RL 전류(PMOS 바디 누설 무시), vsp 공급 = PMOS 드레인 전류 = V(pout)/RP."""
    s, _ = cs_sim
    assert s["rail_current_A"]["vdd"] == pytest.approx((CS["vdd"] - s["nodes"]["nout"]) / CS["rload"], rel=1e-3)
    assert s["rail_current_A"]["vsp"] == pytest.approx(s["nodes"]["pout"] / CS["rp"], rel=1e-3)


def test_op_rc_hand_values(rc_sim):
    s = rc_sim
    assert s["nodes"]["rout"] == pytest.approx(RC["vin"] * RC["rb"] / (RC["ra"] + RC["rb"]), abs=1e-6)
    assert s["nodes"]["dmid"] == pytest.approx(RC["vdd"] * RC["r2"] / (RC["r1"] + RC["r2"]), abs=1e-6)
    i_hand = RC["vdd"] / (RC["r1"] + RC["r2"]) + (RC["vdd"] - s["nodes"]["ndio"]) / RC["rd"]
    assert s["rail_current_A"]["vdd"] == pytest.approx(i_hand, rel=1e-4)
    assert s["devices"]["MD"]["id"] == pytest.approx((RC["vdd"] - s["nodes"]["ndio"]) / RC["rd"], rel=1e-3)


# ------------------------------------------------------------------ .ac
def test_ac_rc_hand_gain_and_f3db(rc_sim):
    """손계산: H0 = Rb/(Ra+Rb) = 0.5 -> -6.0206 dB. f-3dB = 첫 격자점 f 에서 |H|<|H0|/sqrt2,
    |H(f)| = H0/sqrt(1+(f/fc)^2), fc = 1/(2 pi (Ra||Rb) C)."""
    ac = rc_sim["ac"]
    h0 = RC["rb"] / (RC["ra"] + RC["rb"])
    assert ac["dc_gain_db"] == pytest.approx(20 * math.log10(h0), abs=1e-3)
    rp = RC["ra"] * RC["rb"] / (RC["ra"] + RC["rb"])
    fc = 1 / (2 * math.pi * rp * RC["c"])
    g = ac_grid(0.01, 1e10, 40)
    mag = h0 / np.sqrt(1 + (g / fc) ** 2)
    f_exp = g[np.nonzero(mag < mag[0] / math.sqrt(2))[0][0]]
    assert ac["f3db_hz"] == pytest.approx(f_exp, rel=1e-6)


def test_c10_rc_first_point_below_one_no_ugf_pm(rc_sim):
    ac = rc_sim["ac"]
    assert ac["ugf_hz"] is None and ac["pm_deg"] is None


def test_ac_cs_matches_independent_measurement(cs_sim):
    s, ind = cs_sim
    m = measure(ind["f"], ind["H"])
    ac = s["ac"]
    assert ac["dc_gain_db"] == pytest.approx(m["dc_gain_db"], abs=2e-3)
    assert ac["ugf_hz"] == pytest.approx(m["ugf_hz"], rel=2e-3)
    assert ac["pm_deg"] == pytest.approx(m["pm_deg"], abs=0.2)
    assert ac["f3db_hz"] == pytest.approx(m["f3db_hz"], rel=1e-6)
    # feedback_passives 선언 없음 -> β=1: PM = 개루프 A 의 PM
    assert ac["pm_definition"] == "beta_1"
    assert ac["pm_open_loop_deg"] == pytest.approx(ac["pm_deg"], abs=1e-9)


def test_ac_cs_hand_small_signal(cs_sim):
    """손계산(독립 .op 의 gm, gds 로): |A0| = gm (RL || 1/gds), UGF ~ gm / (2 pi CL)(단극점, 기생 C 무시 -> 10 %)."""
    s, ind = cs_sim
    gm, gds = ind["M1"]["gm"], ind["M1"]["gds"]
    a0 = gm / (1 / CS["rload"] + gds)
    assert s["ac"]["dc_gain_db"] == pytest.approx(20 * math.log10(a0), abs=0.05)
    assert s["ac"]["ugf_hz"] == pytest.approx(gm / (2 * math.pi * CS["cl"]), rel=0.10)
    assert 80.0 < s["ac"]["pm_deg"] < 100.0  # 단극점 증폭기: PM ~ 90 deg


def test_c10_gain_never_below_one_no_ugf_pm(tmp_path):
    """fstop 을 1 kHz 로 줄이면 |H|(~12.9) 가 1 아래로 내려가지 않는다 -> UGF/PM None."""
    require_spice()
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero")
    inp["testbench"]["ac"]["fstop_hz"] = 1e3
    ac = _simulate(inp, tmp_path)["ac"]
    assert ac["dc_gain_db"] > 20
    assert ac["ugf_hz"] is None and ac["pm_deg"] is None


@pytest.mark.parametrize("corner,temp", [("ff", 50.0)])
def test_c2_corner_temp_reach_simulation(tmp_path, ref_root, corner, temp):
    """C2 가 실제 모델에 닿는지: npz(ff, 50 C) 로 만든 오라클 결과 = 독립 넷리스트(ff, .temp 50)."""
    inp = cs_input(make_lut(tmp_path / "lut.npz", corner=corner, temp_c=temp), diffusion="zero")
    s = _simulate(inp, tmp_path)
    ind = independent_cs(ref_root, corner=corner, temp_c=temp)
    tt = independent_cs(ref_root)
    assert s["devices"]["M1"]["id"] == pytest.approx(ind["M1"]["id"], rel=2e-4)
    assert abs(ind["M1"]["id"] / tt["M1"]["id"] - 1) > 0.01  # 코너/온도가 실제로 결과를 바꾸는 조건


# ------------------------------------------------------------------ C14 β 루프 PM (손계산 해석식 대조)
GRID = ac_grid(0.01, 1e10, 40)


@pytest.fixture(scope="module")
def fb_ref(ref_root):
    r = independent_fb(ref_root)
    T = fb_loop_gain(GRID, r["gm"], r["gds"])
    A = fb_open_loop(GRID, r["gm"], r["gds"])
    return r, measure(GRID, T), measure(GRID, A)


@pytest.fixture(scope="module")
def fb_sim(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("sim_fb")
    return _simulate(fb_input(make_lut(d / "lut.npz")), d)


@pytest.fixture(scope="module")
def fb_sim_beta1(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("sim_fb_b1")
    return _simulate(fb_input(make_lut(d / "lut.npz"), feedback=None, loop_choke=None), d)


def test_c14_reference_is_not_trivial(fb_ref):
    """해석식 조건 점검: β 루프 PM 과 개루프 A PM 이 크게 달라야 정의 구분이 의미 있다."""
    _, mt, ma = fb_ref
    assert mt["pm_deg"] is not None and ma["pm_deg"] is not None
    assert 20 < mt["pm_deg"] < 80 and abs(ma["pm_deg"] - mt["pm_deg"]) > 20


def test_c14_dc_operating_point_matches_independent(fb_sim, fb_ref):
    r, _, _ = fb_ref
    assert fb_sim["nodes"]["nout"] == pytest.approx(r["vout"], abs=2e-6)


def test_c14_beta_loop_pm_matches_analytic_T(fb_sim, fb_ref):
    """T = gm Zo Zp/(Rf+Zp) (gm, gds 는 독립 .op, MOS 용량 무시: Cin, CL 10 pF 대비 fF) 의 위상여유."""
    _, mt, _ = fb_ref
    ac = fb_sim["ac"]
    assert ac["pm_definition"] == "beta_loop"
    assert ac["pm_deg"] == pytest.approx(mt["pm_deg"], abs=0.5)
    assert ac["loop_ugf_hz"] == pytest.approx(mt["ugf_hz"], rel=1e-2)
    assert ac["loop_gain_dc_db"] == pytest.approx(mt["dc_gain_db"], abs=0.05)


def test_c14_open_loop_pm_still_reported(fb_sim, fb_ref):
    _, _, ma = fb_ref
    ac = fb_sim["ac"]
    assert ac["pm_open_loop_deg"] == pytest.approx(ma["pm_deg"], abs=0.5)
    assert ac["dc_gain_db"] == pytest.approx(ma["dc_gain_db"], abs=0.05)
    assert ac["ugf_hz"] == pytest.approx(ma["ugf_hz"], rel=1e-2)


def test_c14_undeclared_feedback_is_beta_1(fb_sim_beta1, fb_ref):
    """같은 회로라도 feedback_passives 미선언이면 β=1: PM = 개루프 A(해석식) 의 PM."""
    _, mt, ma = fb_ref
    ac = fb_sim_beta1["ac"]
    assert ac["pm_definition"] == "beta_1"
    assert ac["pm_deg"] == pytest.approx(ma["pm_deg"], abs=0.5)
    assert ac["pm_deg"] == pytest.approx(ac["pm_open_loop_deg"], abs=1e-9)
    assert abs(ac["pm_deg"] - mt["pm_deg"]) > 20
