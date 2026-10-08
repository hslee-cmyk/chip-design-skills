"""README "PM 정의" [신규 2026-10-08] 분모 0 = 정의 불가(`loop_probe_singular`) + C8(PASS 불가) + C14(막힘 아님).

근거: README "PM 정의"·C8·C14 만(오라클 소스는 열지 않는다).
- Middlebrook 세 분모 Σw·V(넷), Σw·(w − I_x), Tv + Ti + 2 중 하나라도 **데이터 파일 값으로 정확히 0** 인 표본이 있으면
  루프 측정 전체를 쓰지 않는다: sim.loop.measures = None, sim.loop.singular = {count, first{f_hz, which}, points(앞 20 개)},
  ac.pm_deg = None, ac.pm_undefined = "loop_probe_singular", ac.stability.reason 에 첫 표본. 막힘이 아니다.
  pm 제약·metric 판정 칸 `N/A(정의 불가: loop_probe_singular)` -> PASS 불가(INCOMPLETE, 다른 FAIL 이 있으면 FAIL).
- 0 이 아닌 아주 작은 분모는 그대로 계산한다.

손 회로(단일 입력 nin): Cf(nout–nin)·Cin(nin–ng) 둘 다 feedback_passives, ng = M1(CS, RL) 게이트(Rg 로 바이어스 레일).
  입력 넷 nin 에는 두 되먹임 C 말고 아무것도 없다 -> 루프 넷리스트에서 절단 넷 nin 의 증폭기 쪽은 loop choke(1e20 H) 뿐 ->
  손계산: 주입 전류 w 중 choke 로 가는 몫 = |Z_fb/(Z_fb + jωL)| ~ 1/(ω²·L·C) -- f >= 1 Hz 에서 < 3e-8 이고 891 Hz 쯤부터
  파일 가수 9 자리 아래(< 5e-9)라 I_x 가 정확히 w 로 찍힌다 -> Σw·(w − I_x) = 0.
대조: 같은 회로 + 입력 넷에 게이트(M2, 드레인 vdd) -> 증폭기 쪽에 게이트 용량 -> 분모 0 아님 -> PM 값, 막힘 없음.
기대값은 오라클이 쓴 루프 데이터 파일을 이 파일이 README 식대로 다시 읽어 센 값과 손계산에서 만든다.
"""
import json
import math
from pathlib import Path

import numpy as np
import pytest

import conftest
from conftest import by_name, make_lut, run_netlist, run_oracle, stem_of, zero_diffusion

SAT = 0.05
SG = dict(vdd=1.8, vb=0.7, vin=0.7, rl=129409.146, rg=1e7, cf=1e-12, cin=1e-12, L=0.5e-6, fw=2e-6, n=2)


def sg_input(lut, gate_on_input=False, constraints=None, metrics=None):
    c = SG

    def dev(name, d, g, n):
        return {"name": name, "kind": "nmos", "drain": d, "gate": g, "source": "gnd", "bulk": "gnd",
                "L": c["L"], "finger_w": c["fw"], "n_fingers": n, "W": c["fw"] * n}

    devs = [dev("M1", "nout", "ng", c["n"])]
    if gate_on_input:
        devs.append(dev("M2", "vdd", "nin", 1))
    inp = {"schema": "spice_oracle_input/1", "circuit": "tsingular",
           "process": conftest.process_block(lut),
           "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "vb", "voltage": c["vb"]},
                     {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": devs, "sources": [],
           "passives": [{"name": "RL", "kind": "resistor", "terminals": ["vdd", "nout"], "value": c["rl"]},
                        {"name": "Rg", "kind": "resistor", "terminals": ["vb", "ng"], "value": c["rg"]},
                        {"name": "Cf", "kind": "capacitor", "terminals": ["nout", "nin"], "value": c["cf"]},
                        {"name": "Cin", "kind": "capacitor", "terminals": ["nin", "ng"], "value": c["cin"]}],
           "ports": {"input": "nin", "output": "nout"},
           "feedback_passives": ["Cf", "Cin"],
           "predictions": {"nodes": {"nin": c["vin"]},
                           "devices": {d["name"]: {"off_current_A": 0.0} for d in devs},
                           "metrics": metrics or []},
           "testbench": conftest.testbench_block()}
    inp["testbench"]["loop_dc_choke_H"] = 1e20
    if constraints is not None:
        inp["acceptance"] = {"constraints": constraints}
    return zero_diffusion(inp)


def pm_con(op, limit, name="pmc"):
    return {"name": name, "measure": "pm_deg", "op": op, "limit": limit}


def _sim(o, inp):
    return json.loads((o / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))


def singular_samples(o: Path, stem: str):
    """README 식의 세 분모를 오라클이 쓴 루프 데이터 파일 값으로 계산(끊은 넷 1개 nin, 가중 w = input_ac = 1).
    v 파일: f, Re/Im V(lbx), Re/Im V(nin); i 파일: f, Re/Im i(Vlb), Re/Im V(nin)."""
    v = np.loadtxt(o / f"{stem}.loop.v.txt")
    i = np.loadtxt(o / f"{stem}.loop.i.txt")
    f = v[:, 0]
    vlbx, vn = v[:, 1] + 1j * v[:, 2], v[:, 3] + 1j * v[:, 4]
    ix = i[:, 1] + 1j * i[:, 2]
    w = 1.0
    d1 = w * vn                    # Σ w·V(넷)
    d2 = w * (w - ix)              # Σ w·(w − I_x)
    with np.errstate(divide="ignore", invalid="ignore"):
        tv = -w * vlbx / d1
        ti = w * ix / d2
        d3 = tv + ti + 2
    bad = (d1 == 0) | (d2 == 0) | (np.isfinite(d3) & (d3 == 0))
    return f, bad, d2


@pytest.fixture(scope="module")
def singular_run(tmp_path_factory, ref_root):      # ref_root: ngspice/PDK 없으면 skip
    d = tmp_path_factory.mktemp("singular")
    inp = sg_input(make_lut(d / "lut.npz"), constraints=[pm_con(">=", 45.0)],
                   metrics=[{"name": "pm", "measure": "pm_deg", "value": 60.0}])
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.returncode, (p.stdout + p.stderr)[-2000:])
    return d, inp, res, p


def test_hand_calc_predicts_exact_zero_denominator():
    """손계산 전제: choke 로 새는 주입 전류 몫 |Z_fb/(Z_fb + jωL)| 가 고주파에서 파일 가수 9 자리 반 단위(5e-9) 아래."""
    c = SG
    f = 1e3
    w = 2 * math.pi * f
    # 절단 넷에서 본 되먹임 쪽 임피던스 크기 척도: 두 C(각 1 pF) 경로 + 그 뒤 노드(nout ~RL, ng ~Rg 10 MΩ) -- 넉넉히 1e3 배
    z_fb = 1e3 * (abs(1 / (1j * w * min(c["cf"], c["cin"]))) + c["rg"] + c["rl"])
    leak = abs(z_fb / (z_fb + 1j * w * 1e20))
    assert leak < 5e-9, leak


def test_singular_detected_from_data(singular_run):
    d, inp, res, _ = singular_run
    o, stem = d / "o", stem_of(inp, "free")
    f, bad, d2 = singular_samples(o, stem)
    assert bad.sum() > 0, "데이터 파일에 분모 0 표본이 없다 -- 조건 점검"
    loop = _sim(o, inp)["loop"]
    sg = loop["singular"]
    assert sg is not None and sg["count"] == int(bad.sum()), (sg, int(bad.sum()))
    assert sg["first"]["f_hz"] == pytest.approx(f[bad][0], rel=1e-9) and sg["first"]["which"], sg["first"]
    assert isinstance(sg["points"], list) and len(sg["points"]) == min(20, int(bad.sum())), len(sg["points"])
    assert loop["measures"] is None, loop["measures"]


def test_singular_pm_undefined_not_blocked(singular_run):
    d, inp, res, p = singular_run
    o = d / "o"
    ac = _sim(o, inp)["ac"]
    assert ac["pm_deg"] is None and ac["pm_undefined"] == "loop_probe_singular", ac
    assert ac["stability"]["reason"], ac["stability"]
    c = res["free"]
    assert c["blockers"] == [], c["blockers"]
    k = by_name(c["constraints"], "name", "pmc")
    assert k["spice"] is None and k["judge"] == "N/A(정의 불가: loop_probe_singular)", k
    assert k["undefined"] == "loop_probe_singular"
    m = by_name(c["performance"], "name", "pm")
    assert m["spice"] is None and m["judge"] == "N/A(정의 불가: loop_probe_singular)", m
    a = c["summary"]["acceptance"]
    assert a["constraints_unmeasured"] == ["pmc"] and a["constraints_failed"] == [], a
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


@pytest.mark.parametrize("op,limit", [(">=", -1e9), ("<=", 1e9)])
def test_singular_never_pass(tmp_path, ref_root, op, limit):
    """어떤 limit 이든 PASS 불가(INCOMPLETE, 반환 0)."""
    inp = sg_input(make_lut(tmp_path / "lut.npz"), constraints=[pm_con(op, limit)])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


def test_singular_with_other_fail_is_fail(tmp_path, ref_root):
    inp = sg_input(make_lut(tmp_path / "lut.npz"),
                   constraints=[pm_con(">=", 0.0), {"name": "g", "measure": "dc_gain_db", "op": ">=", "limit": 200.0}])
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]
    assert c["summary"]["acceptance"]["constraints_failed"] == ["g"]


def test_gate_on_input_control_not_singular(tmp_path, ref_root):
    """음성 대조: 입력 넷에 게이트(M2)가 있으면 증폭기 쪽 어드미턴스가 choke 뿐이 아니다 -> 분모 0 표본 없음(데이터 재계산)
    -> singular 없음, 루프 측정 사용(pm_definition beta_loop, pm_undefined 가 loop_probe_singular 아님), 막힘 없음."""
    inp = sg_input(make_lut(tmp_path / "lut.npz"), gate_on_input=True)
    p, text, meta = run_netlist(inp, tmp_path / "n")
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-800:]
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None and c["blockers"] == [], (p.stdout + p.stderr)[-1500:]
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, bad, d2 = singular_samples(o, stem)
    assert bad.sum() == 0 and np.all(np.abs(d2) > 0), int(bad.sum())
    s = _sim(o, inp)
    assert not s["loop"].get("singular"), s["loop"].get("singular")
    assert s["loop"]["measures"] is not None
    ac = s["ac"]
    assert ac["pm_definition"] == "beta_loop" and ac.get("pm_undefined") is None, ac
    # 루프 측정은 쓰인다: Cin 이 DC 를 막아(Rg 10 MΩ 대 1/(2π·0.01 Hz·1 pF) = 1.6e13 Ω) fstart 의 |T| < 1 이라 PM 원값은 없고
    # (C10 '측정 정의': 첫 점부터 1 미만이면 None) 안정성 검사는 '검사 대상 아님' -- 분모 0 경로와 다르다.
    assert s["loop"]["measures"]["gain_dc"] == pytest.approx(10 ** (ac["loop_gain_dc_db"] / 20), rel=1e-9)
    assert ac["pm_deg"] is None and ac["stability"]["reason"]


def test_tiny_nonzero_denominator_computed(tmp_path, ref_root):
    """'0 이 아닌 아주 작은 분모는 그대로 계산': 대조 회로에서 가장 작은 |Σw·(w − I_x)| 가 1 보다 훨씬 작아도(게이트 용량
    몫) 표본은 singular 가 아니다 -- 위 대조와 같은 데이터에서 최소 분모를 기록하고 singular 없음을 다시 확인."""
    inp = sg_input(make_lut(tmp_path / "lut.npz"), gate_on_input=True)
    run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    o, stem = tmp_path / "o", stem_of(inp, "free")
    f, bad, d2 = singular_samples(o, stem)
    mn = float(np.abs(d2).min())
    assert 0 < mn < 1e-2, mn
    assert not _sim(o, inp)["loop"].get("singular")
