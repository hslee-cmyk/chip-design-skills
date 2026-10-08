"""U6 `.noise` 대조(설계 41 §7.6, 설계 40 §11 U6 'noise 손계산 저항 분압', README "U6 -- .noise").

기대값 출처(피검 코드 출력으로 만들지 않음):
  * oracle (a) 손계산: conftest RC 회로(rin -Ra- rout, rout -Rb- gnd, rout -C- gnd, Ra = Rb = 2 kΩ)의 입력 환산 열잡음.
    rout 에서 본 두 저항은 (이상 입력원으로 AC 접지된 rin 을 통해) 병렬 -> 출력 PSD = 4kT·(Ra‖Rb)/(1 + (f/fc)²),
    전달 |H|² = (Rb/(Ra+Rb))²/(1 + (f/fc)²) -> 입력 환산 = 4kT·(Ra‖Rb)/H0² (주파수 무관, H0 = 0.5),
    T = LUT temp_c 27 + 273.15 K, k_B = 1.380649e-23 J/K(SI 정의값). 두 저항 몫은 대칭이라 각 0.5.
  * oracle (c) 독립 적분: conftest 되먹임 회로(CS + Rf + Cin, β 루프)를 손으로 쓴 닫힌 넷리스트(입력 DC 는 같은 1e20 H choke 로
    0.7 V 에 고정 -- 오라클 입력 testbench.loop_dc_choke_H 와 같은 회로)로 ngspice .noise -> onoise_spectrum 을 이 파일이
    ln f 격자 사다리꼴(∫S df = ∫S·f dln f)로 적분한 rms(오라클의 격자 두 배 반복·꼬리 상계와 다른 방법).
"""
import json
import math
from pathlib import Path

import numpy as np
import pytest

import conftest
from conftest import FB, NFET, fb_input, make_lut, rc_input, run_oracle, stem_of, zero_diffusion
from test_oracle_c10_stability import SAT, _head, _ngspice

K_B = 1.380649e-23
T_K = 27.0 + 273.15
RELTOL = 1e-4                                    # conftest.testbench_block options.reltol


def _sim(o: Path, inp):
    return json.loads((o / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def rc_noise(tmp_path_factory):
    conftest.require_spice()
    d = tmp_path_factory.mktemp("rc_noise")
    inp = zero_diffusion(rc_input(make_lut(d / "lut.npz")))
    inp["noise"] = {"f_lo_hz": 10.0}
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    return inp, _sim(d / "o", inp), res["free"], p


def test_rc_input_referred_thermal_hand_calc(rc_noise):
    """oracle (a): noise_th_in_v2hz = 4kT·(Ra‖Rb)/H0² (= 6.630e-17 V²/Hz), 상대 reltol 안. 격자 모든 점에서 같은 값(입력 환산은
    주파수 무관 -- RC 극 fc = 159 kHz 위아래 모두)."""
    inp, sim, cmp, p = rc_noise
    c = conftest.RC
    rpar = c["ra"] * c["rb"] / (c["ra"] + c["rb"])
    h0 = c["rb"] / (c["ra"] + c["rb"])
    hand = 4 * K_B * T_K * rpar / h0 ** 2
    ol = sim["noise"]["open_loop"]
    assert ol["status"] == "ok", ol
    assert ol["th_in_v2hz"] == pytest.approx(hand, rel=RELTOL), (ol["th_in_v2hz"], hand)
    grid = ol["grid"]
    assert grid and all(g["thermal_in_v2hz"] == pytest.approx(hand, rel=10 * RELTOL) for g in grid), grid[:3]
    assert p.returncode == 0


def test_rc_contributions_split_evenly_and_no_flicker(rc_noise):
    """oracle (a): 열잡음 기여는 Ra·Rb 둘(다른 가지 R1·R2·Rd·MD 는 rout 에 닿지 않아 0), 대칭이라 몫 각 0.5, 합 = 전체.
    이상 저항에는 1/f 가 없다 -> flicker 0 -> noise_fc_in_hz = None, 사유 below_f_lo(README: f_lo 에서 이미 열잡음 아래)."""
    inp, sim, cmp, p = rc_noise
    ol = sim["noise"]["open_loop"]
    nz = [r for r in ol["contrib"] if r["thermal_in_v2hz"] > 0]
    assert len(nz) == 2 and sorted(r["share_thermal"] for r in nz) == pytest.approx([0.5, 0.5], abs=1e-6), ol["contrib"]
    assert sum(r["thermal_in_v2hz"] for r in nz) == pytest.approx(ol["th_in_v2hz"], rel=1e-9)
    assert all(r["flicker_in_v2hz"] == 0 for r in ol["contrib"]), ol["contrib"]
    assert ol["fc_in_hz"] is None and ol["fc_reason"] == "below_f_lo", ol


def test_rc_noise_metric_constraint_judged(tmp_path, rc_noise):
    """README U6: noise_th_in_v2hz 는 acceptance 제약 measure 로 판정된다 -- 손계산 값의 2 배 상한 PASS, 0.5 배 상한 FAIL."""
    inp, *_ = rc_noise
    c = conftest.RC
    # C23: MD(다이오드 가지)는 전도 예측 소자라 꺼짐 문턱이 있어야 INCOMPLETE 가 아니다 -- 문턱 0(= 'ID > 0 이면 전도') 명시
    hand = 4 * K_B * T_K * (c["ra"] * c["rb"] / (c["ra"] + c["rb"])) / (c["rb"] / (c["ra"] + c["rb"])) ** 2
    out = {}
    for tag, lim in (("ok", 2 * hand), ("bad", 0.5 * hand)):
        inp2 = json.loads(json.dumps(inp))
        inp2["predictions"]["devices"] = {"MD": {"off_current_A": 0.0}}
        inp2["acceptance"] = {"constraints": [{"name": "nth", "measure": "noise_th_in_v2hz", "op": "<=", "limit": lim}]}
        p, res = run_oracle(inp2, tmp_path / tag, sat_margin=SAT)
        out[tag] = (p.returncode, conftest.by_name(res["free"]["constraints"], "name", "nth")["judge"],
                    res["free"]["summary"]["verdict"])
    assert out["ok"] == (0, "PASS", "PASS") and out["bad"] == (1, "FAIL", "FAIL"), out


# ---------------------------------------------------------------- 폐루프 적분(독립 적분)
def _fb_closed_body():
    c = FB
    b = [f"Vdd vdd 0 DC {c['vdd']}", f"Vb vb 0 DC {c['vin']} AC 1", f"Lb vb nin {c['loop_choke']}",
         f"RL vdd nout {c['rload']}", f"CL nout 0 {c['cl']}", f"Rf nout nin {c['rf']}", "Cin nin 0 1e-12"]
    b += [f"XM1_{i} nout nin 0 0 {NFET} l={c['L']} w={c['finger_w']}" for i in range(c["n"])]
    return b


def _independent_out_noise_rms(wd: Path, f_lo, f_hi, ppd):
    lines = _head() + _fb_closed_body() + [
        ".control", "set noaskquit", f"noise v(nout) Vb dec {ppd} {f_lo} {f_hi}", "setplot noise1",
        "set wr_singlescale", "wrdata ns.txt onoise_spectrum", "quit", ".endc", ".end"]
    p, _ = _ngspice(lines, wd, name="n.cir")
    a = np.loadtxt(wd / "ns.txt")
    f, s = a[:, 0], a[:, 1] ** 2                         # onoise_spectrum [V/sqrt(Hz)] -> V²/Hz
    lf = np.log(f)
    return math.sqrt(float(np.sum(0.5 * (s[1:] * f[1:] + s[:-1] * f[:-1]) * np.diff(lf)))), f, s


@pytest.fixture(scope="module")
def fb_noise(tmp_path_factory):
    conftest.require_spice()
    d = tmp_path_factory.mktemp("fb_noise")
    inp = fb_input(make_lut(d / "lut.npz"), cin=1e-12)
    inp["predictions"]["devices"] = {"M1": {"off_current_A": 0.0}}
    inp["noise"] = {"f_lo_hz": 1.0, "closed_loop": True}
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    return d, inp, _sim(d / "o", inp), res["free"]


def test_closed_loop_integral_matches_independent_integration(fb_noise):
    """oracle (c): noise_out_int_vrms(오라클) = 독립 닫힌 넷리스트 .noise 출력 PSD 를 [f_lo, f_hi(오라클이 수렴으로 정한 상한)]
    에서 ln f 사다리꼴(100/decade)로 적분한 rms, 상대 1e-3(두 적분 모두 격자 분해능 안). 독립 적분은 위 상한을 10 배 넓혀도
    reltol 안에서 같다(꼬리 수렴의 독립 확인)."""
    d, inp, sim, cmp = fb_noise
    cl = sim["noise"]["closed_loop"]
    assert cl["status"] == "ok" and cl["converged"] is True, cl
    f_lo, f_hi = cl["f_lo_hz"], cl["f_hi_hz"]
    assert f_lo == inp["noise"]["f_lo_hz"]
    mine, f, s = _independent_out_noise_rms(d / "ind", f_lo, f_hi, 100)
    wider, *_ = _independent_out_noise_rms(d / "ind_w", f_lo, 10 * f_hi, 100)
    assert wider == pytest.approx(mine, rel=RELTOL), (wider, mine)
    assert cl["out_int_vrms"] == pytest.approx(mine, rel=1e-3), (cl["out_int_vrms"], mine)
    assert cl["out_int_v2"] == pytest.approx(cl["out_int_vrms"] ** 2, rel=1e-9)


def test_closed_loop_ktc_not_measured_is_explicit(fb_noise):
    """설계 41 §7.6 '샘플링 kT/C 는 과도 기반으로 따로 잰다' -- 이 모듈은 재지 않으므로 값 대신 명시적 not_measured(+ 사유)."""
    d, inp, sim, cmp = fb_noise
    k = sim["noise"]["closed_loop"]["ktc_sampling"]
    assert k["status"] == "not_measured" and k["reason"], k


# ---------------------------------------------------------------- 거부(스키마)
@pytest.mark.parametrize("blk", [{"f_lo_hz": 0.0}, {"points_per_decade": 10}, {"f_lo_hz": 1.0, "rel_resolution": 0.0}])
def test_noise_block_schema_rejected(tmp_path, blk):
    """C13 + 스키마 noise: f_lo_hz 필수·양수, rel_resolution 양수 -- 위반이면 산출물 없이 반환 2."""
    inp = zero_diffusion(rc_input(make_lut(tmp_path / "lut.npz")))
    inp["noise"] = blk
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    assert p.returncode == 2 and res["free"] is None, (p.returncode, (p.stdout + p.stderr)[-800:])
    assert not list((tmp_path / "o").glob("*.sim.json"))

# ---------------------------------------------------------------- noise_excess_th 입력 셀 이름 사상(설계 40 §4 C10 8 (v))
def _noise_mod():
    """피검 순수 함수 `oracle_noise.oracle_element_names(name)`(README '.noise' 이름) -- 소스는 열지 않고 import 만."""
    import importlib
    import sys
    d = str(conftest.ORACLE_DIR)
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module("oracle_noise")


@pytest.mark.parametrize("name,must", [
    ("M1a", {"m1a"}),                                              # MOS: 이름 자체(소문자)
    ("RL", {"rp_rl", "cp_rl", "isrc_rl", "vsrc_rl"}),              # 수동·이상원: CIRCUIT_PREFIXES 접두 + 이름(소문자)
    ("Rp_RL", {"rp_rl"}),                                          # 이미 접두가 붙은 이름은 그대로도 후보
])
def test_oracle_element_names_mapping(name, must):
    """설계 40 §4 C10 8 'U6 test 후속 정의' (v)(a1e1d2c): noise_excess_th 의 입력 셀 소자 이름은 오라클 넷리스트 이름으로 사상해 찾는다
    (수동소자 접두 포함). 기대 후보는 README 문장(oracle (d)): MOS `M1a` -> `m1a`, 수동소자 `RL` -> `rp_rl`·`cp_rl`·`isrc_rl`·`vsrc_rl`."""
    got = {str(x) for x in _noise_mod().oracle_element_names(name)}
    assert must <= got, (name, got)
    assert all(x == x.lower() for x in got), got


def _rc_excess_run(tmp_path, cells, constraints=None):
    inp = zero_diffusion(rc_input(make_lut(tmp_path / "lut.npz")))
    inp["noise"] = {"f_lo_hz": 10.0, "input_cell_devices": list(cells)}
    inp["predictions"]["devices"] = {"MD": {"off_current_A": 0.0}}         # C23(위 test 와 같은 이유)
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    return _sim(tmp_path / "o", inp)["noise"]["open_loop"], res["free"], p


def test_noise_excess_th_maps_passive_and_mos_names(tmp_path):
    """(v) + README `noise_excess_th` = noise_th_in_v2hz / (input_cell_devices 소자만의 열 성분 합). 입력 셀 = 수동소자 `Ra`(넷리스트 이름
    Rp_Ra) + MOS `MD`(다이오드 가지, rout 에 닿지 않아 기여 0). oracle (a) 손계산: Ra·Rb 는 rout 에서 대칭(각 몫 0.5, 위
    test_rc_contributions_split_evenly_and_no_flicker) -> 전체 / (Ra + MD) = 1 / 0.5 = 2, 상대 reltol. 두 이름 모두 찾음(누락 없음).
    제약 noise_excess_th <= 2.5 는 값 2 로 판정(PASS)."""
    ol, cmp, p = _rc_excess_run(tmp_path, ["Ra", "MD"],
                                [{"name": "ex", "measure": "noise_excess_th", "op": "<=", "limit": 2.5}])
    assert ol["excess_th"] == pytest.approx(2.0, rel=RELTOL), ol
    assert not ol.get("input_cell_missing"), ol.get("input_cell_missing")
    k = conftest.by_name(cmp["constraints"], "name", "ex")
    assert k["judge"] == "PASS" and k["spice"] == pytest.approx(2.0, rel=RELTOL), k


def test_noise_excess_th_reports_missing_name(tmp_path):
    """(v) README '못 찾은 이름은 input_cell_missing': 넷리스트에 없는 이름 `Rzz` 는 input_cell_missing 에 그대로 남는다. 찾은 `Ra` 는
    누락 목록에 없다."""
    ol, cmp, p = _rc_excess_run(tmp_path, ["Ra", "Rzz"])
    assert "Rzz" in ol["input_cell_missing"] and "Ra" not in ol["input_cell_missing"], ol


def test_noise_excess_th_none_when_no_input_cell_found(tmp_path):
    """README '입력 셀이 없으면 None + excess_reason': 이름이 하나도 사상되지 않으면(`Rzz` 만) 값 없음 + 이유 + 누락 목록, 그
    metric 의 제약은 값 없음 판정(N/A) -> PASS 불가(README '값이 없으면 N/A -> INCOMPLETE')."""
    ol, cmp, p = _rc_excess_run(tmp_path, ["Rzz"], [{"name": "ex", "measure": "noise_excess_th", "op": "<=", "limit": 2.5}])
    assert ol["excess_th"] is None and ol.get("excess_reason"), ol
    assert ol["input_cell_missing"] == ["Rzz"], ol
    k = conftest.by_name(cmp["constraints"], "name", "ex")
    assert k["spice"] is None and str(k["judge"]).startswith("N/A"), k
    assert cmp["summary"]["verdict"] != "PASS", cmp["summary"]
