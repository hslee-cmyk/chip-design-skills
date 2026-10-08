"""U6 스윙·ICMR DC 스윕(설계 40 §10.2 '오라클 스윙·ICMR DC 스윕' 행, README "스윙·ICMR", 사용자 결정 Q4).

기대값 출처(피검 코드 출력으로 만들지 않음): oracle (c) -- u6_toy5t 의 독립 servo 넷리스트 `.dc` 스윕(0.5 mV 격자)에서 README 포화
조건 문안(도통 MOS 전부 VDS >= VDSAT + 여유, 회로 노드가 레일 ± reltol·레일 폭 안)을 독립 구현해 찾은 창 끝(선형 보간).
비교 허용오차 = 오라클의 목표 분해능 reltol·레일 폭(README '목표 분해능 reltol·레일 폭') 의 2 배(두 쪽 각각의 분해능).
손계산 확인(oracle (a)): 스윙 아래 끝에서 M2 의 VDS − VDSAT = 여유(= 출력 − 꼬리 노드 − VDSAT2), 위 끝에서 M4 의 같은 양,
ICMR 아래 끝은 꼬리 노드가 0 − tol(이상 전류원 꼬리 -- MOS 가 아니라 레일 조건이 끝을 정함).
좌표: 스윙은 출력 전압, ICMR 은 README '입력 공통모드 Δ' 의 좌표 = 공칭 (inp+inn)/2 + Δ(Δ = 두 입력 원에 더한 같은 이동).
"""
import json

import pytest

import conftest
import u6_toy5t as toy
from conftest import cs_input, make_lut, run_oracle, stem_of
from test_oracle_c10_stability import SAT

TOL = 2 * toy.RELTOL * (toy.T5["vdd"] - 0.0)          # 2 x 목표 분해능(reltol·레일 폭)


@pytest.fixture(scope="module")
def sw_run(tmp_path_factory):
    conftest.require_spice()
    d = tmp_path_factory.mktemp("sw5t")
    nom = toy.nominal_op(d / "ind_op")
    sw = toy.dc_window(d / "ind_sw", "swing", nom["out"], 0.16, 1.75, 0.0005, SAT)
    ic = toy.dc_window(d / "ind_ic", "icmr", toy.T5["vin"], 0.5, 1.6, 0.0005, SAT, vout=nom["out"])
    inp = toy.toy_input(d, nom, judge={"sat_margin_V": SAT},
                        swing_icmr={"swing": True, "icmr": True, "input_dc_V": toy.T5["vin"]})
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    sim = json.loads((d / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))
    return inp, sim, res["free"], nom, sw, ic, p


def test_swing_window_matches_independent_sweep(sw_run):
    inp, sim, cmp, nom, sw, ic, p = sw_run
    s = sim["swing_icmr"]
    assert s["status"] == "ok" and s["margin_V"] == SAT and s["swing"]["status"] == "ok", s
    assert s["swing"]["v_lo"] == pytest.approx(sw["lo"], abs=TOL), (s["swing"], sw)
    assert s["swing"]["v_hi"] == pytest.approx(sw["hi"], abs=TOL), (s["swing"], sw)
    vo = inp["predictions"]["nodes"]["out"]
    # README: 단일 출력 swing_out_v = 2·min(V_hi − Vo, Vo − V_lo) (설계 40 §3.8-8 과 같은 정의) -- 독립 창 끝으로 셈
    assert s["swing_out_v"] == pytest.approx(2 * min(sw["hi"] - vo, vo - sw["lo"]), abs=2 * TOL), (s["swing_out_v"], sw)
    assert p.returncode == 0


def test_icmr_window_matches_independent_sweep(sw_run):
    inp, sim, cmp, nom, sw, ic, p = sw_run
    s = sim["swing_icmr"]
    x0 = toy.T5["vin"]                                          # 스윕 변수(inp) 의 공칭값
    lo = ic["nominal_cm"] + (ic["lo"] - x0)                     # README 좌표: 공칭 공통모드 + Δ
    hi = ic["nominal_cm"] + (ic["hi"] - x0)
    assert s["icmr"]["status"] == "ok", s["icmr"]
    assert s["icmr"]["v_cm_nominal"] == pytest.approx(ic["nominal_cm"], abs=TOL)
    assert s["icmr"]["v_in_min"] == pytest.approx(lo, abs=TOL), (s["icmr"], lo)
    assert s["icmr"]["v_in_max"] == pytest.approx(hi, abs=TOL), (s["icmr"], hi)
    # README: icmr_v = [Vin,min, Vin,max] ∩ [레일] 의 폭, icm_margin_v = min(V_icm − Vin,min, Vin,max − V_icm), V_icm = 선언 input_dc_V
    assert s["icmr_v"] == pytest.approx(hi - lo, abs=2 * TOL)
    v_icm = inp["swing_icmr"]["input_dc_V"]
    assert s["icm_margin_v"] == pytest.approx(min(v_icm - lo, hi - v_icm), abs=2 * TOL)


@pytest.mark.parametrize("which,edge,limiter", [
    ("swing", "lo", "M2"),          # 출력이 내려가면 M2: VDS = out − tail 이 VDSAT2 + 여유에 닿는다
    ("swing", "hi", "M4"),          # 출력이 올라가면 M4: VSD = VDD − out 이 VDSAT4 + 여유에 닿는다
    ("icmr", "lo", "rail:tail"),    # 공통모드가 내려가면 꼬리 노드가 0 − tol 에 닿는다(이상 전류원 -- MOS 조건 아님)
    ("icmr", "hi", "M1"),           # 공통모드가 올라가면 M1: VDS = d1 − tail(d1 = VDD − VSG3 고정)이 VDSAT1 + 여유에 닿는다
])
def test_window_edges_hand_limiter(sw_run, which, edge, limiter):
    """oracle (a) 회로 해석(손): 각 창 끝을 정하는 조건이 위 표의 소자/노드다 -- 독립 스윕의 그 끝에서 해당 여유가 0(다른 여유는
    모두 양수). 이 대조가 독립 스윕 창 끝의 물리적 의미를 고정한다(위 두 test 의 기대값 근거)."""
    inp, sim, cmp, nom, sw, ic, p = sw_run
    sl = {"swing": sw, "icmr": ic}[which][edge + "_slack"]
    assert sl[limiter] == pytest.approx(0.0, abs=1e-6), sl
    assert all(v > 1e-4 for k, v in sl.items() if k != limiter), sl


def test_icm_margin_pending_not_reported(tmp_path):
    """README 입력 블록: input_dc_pending = true 면 icm_margin_v 를 내지 않고 input_dc_pending 으로 보고(SP-2 대기)."""
    nom = toy.nominal_op(tmp_path / "ind_op")
    inp = toy.toy_input(tmp_path, nom, judge={"sat_margin_V": SAT},
                        swing_icmr={"swing": False, "icmr": True, "input_dc_pending": True})
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    s = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["swing_icmr"]
    assert s["icm_margin_v"] is None and s.get("icmr_v") is not None, s
    assert s["icmr"]["icm_margin_reason"] == "input_dc_pending", s["icmr"]


def test_swing_unavailable_without_servo(tmp_path):
    """README 스윙·ICMR: 출력 목표를 움직일 servo 가 없는 단일 입력 회로의 스윙은 status = unavailable + 이유 -- 값을 지어내지
    않는다. (같은 회로의 ICMR 은 이 test 가 단언하지 않는다 -- 보고 항목: servo 없이 입력만 옮긴 창을 ok 로 낸다.)"""
    ind = conftest.independent_cs(tmp_path / "ind")
    pr = conftest.preds_from_independent(ind)
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"], preds_devices=pr["devices"])
    inp["swing_icmr"] = {"swing": True, "icmr": True}
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    s = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))["swing_icmr"]
    assert s["swing_out_v"] is None and s["swing"]["status"] == "unavailable" and s["swing"]["reason"], s
