"""[CM 2026-10-08, 0e487b3] 오라클 CM 루프 -- README 'CM 루프 PM'(cm_output_loop, cmloop 넷리스트, sim.cm_loop, 판정 cm_loop_ineffective)
+ metrics CONTRACT 7.11(엔진과 같은 정의: 출력 넷의 구동자 channel 단자 절단, 동일 부호 가중 ½·½, 입력 AC 접지).

기대값 출처:
- 넷리스트 모양: README 동작 계약 문장(oracle (d)).
- CM 루프 이득·PM: (a) 손유도 폐형식 T = gmp/((Go + sCL)(1 + sR·Cg) + sCg)(반회로마다 R·Cg -- 감지 넷 c 의 총 용량 2Cg 를 반씩),
  gm·gds 는 이 파일이 손으로 쓴 독립 ngspice .op 넷리스트에서(conftest run_spice). 측정 정의는 conftest measure(README '측정 정의'의
  독립 구현)를 같은 격자에 적용해 보간 방법 차이를 없앤다.
- 허용오차(유도): 폐형식은 MOS 단자 용량을 뺀다. 그 크기의 상계 = 노드마다 소자 둘 × W·L·Cox(sky130 1.8 V 산화막 tox 4.1 nm ->
  Cox = 3.9·ε0/tox ≈ 8.4e-3 F/m², W = 4 µm(finger 2 µm × 2), L = 0.5 µm -> 소자당 ≈ 17 fF). 이 용량을 출력 노드·감지 넷에 더한 폐형식과
  더하지 않은 폐형식의 PM·UGF 차를 허용으로 쓴다(새 상수 아님 -- 입력 기하와 물리 상수에서 계산). DC 이득은 ngspice reltol(1e-4)
  × 10 의 상대 허용.
- 엔진 대 ngspice: 같은 gm·gds·용량을 엔진 MNA(cut_circuit LoopCut("mos") + probe_factor + analyze_loop)에 넣은 PM 이 위 허용 안.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from conftest import (NFET, PFET, ac_grid, make_lut, measure, probe, process_block, require_spice, run_netlist,
                      run_oracle, run_spice, testbench_block, zero_diffusion)

CM = dict(vdd=1.8, vin=0.6, L=0.5e-6, fw=2e-6, n=2, r=1e6, cl=10e-12, cg=5e-12, rl=2e5)
EPS0 = 8.854187817e-12
COX = 3.9 * EPS0 / 4.1e-9                       # sky130 1.8 V 소자 산화막(tox 4.1 nm)
C_DEV = CM["fw"] * CM["n"] * CM["L"] * COX      # 소자당 게이트 용량 규모 상계 ≈ 17 fF


def _dev(name, kind, d, g, s, b):
    return {"name": name, "kind": kind, "drain": d, "gate": g, "source": s, "bulk": b, "L": CM["L"], "finger_w": CM["fw"],
            "n_fingers": CM["n"], "W": CM["fw"] * CM["n"]}


def cm_input(lut: Path, variant="cmfb", cm_output_loop=True, ports=None, constraint=True) -> dict:
    """variant cmfb: NMOS 입력쌍 M1·M2 + PMOS 부하 M3·M4, 부하 gate c = 출력 저항 평균(R1·R2) + Cg(c, gnd) -- CM 루프 있음.
    variant none: 같은 입력쌍 + 저항 부하 RL(vdd, 출력) -- CMFB 없음(출력 CM 주입 루프 이득 0)."""
    devs = [_dev("M1", "nmos", "op", "ip", "gnd", "gnd"), _dev("M2", "nmos", "om", "im", "gnd", "gnd")]
    pas = [{"name": "CL1", "kind": "capacitor", "terminals": ["op", "gnd"], "value": CM["cl"]},
           {"name": "CL2", "kind": "capacitor", "terminals": ["om", "gnd"], "value": CM["cl"]}]
    if variant == "cmfb":
        devs += [_dev("M3", "pmos", "op", "c", "vdd", "vdd"), _dev("M4", "pmos", "om", "c", "vdd", "vdd")]
        pas += [{"name": "R1", "kind": "resistor", "terminals": ["op", "c"], "value": CM["r"]},
                {"name": "R2", "kind": "resistor", "terminals": ["c", "om"], "value": CM["r"]},
                {"name": "Cg", "kind": "capacitor", "terminals": ["c", "gnd"], "value": CM["cg"]}]
    else:
        pas += [{"name": "RL1", "kind": "resistor", "terminals": ["vdd", "op"], "value": CM["rl"]},
                {"name": "RL2", "kind": "resistor", "terminals": ["vdd", "om"], "value": CM["rl"]}]
    inp = {"schema": "spice_oracle_input/1", "circuit": "tcm_" + variant, "process": process_block(lut, diffusion=False),
           "rails": [{"net": "vdd", "voltage": CM["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
           "devices": devs, "sources": [], "passives": pas,
           "ports": ports or {"input_p": "ip", "input_n": "im", "output_p": "op", "output_n": "om"},
           "predictions": {"nodes": {"ip": CM["vin"], "im": CM["vin"]}, "devices": {}, "metrics": []},
           "testbench": testbench_block()}
    zero_diffusion(inp)
    if cm_output_loop is not None:
        inp["cm_output_loop"] = cm_output_loop
    if constraint:
        inp["acceptance"] = {"constraints": [{"name": "pm_cm", "measure": "cm_pm_deg", "op": ">=", "limit": 60.0}]}
    return inp


def _tok(text, name):
    for ln in text.splitlines():
        t = ln.split()
        if t and t[0].lower() == name.lower():
            return t
    return None


# ---------------------------------------------------------------- 넷리스트(ngspice 없이)

def test_cmloop_netlist_cuts_driver_channel_terminals(tmp_path):
    """README: 두 출력 넷에서 구동자 쪽 단자(그 넷에 d 또는 s 가 물린 MOS 의 channel 단자)만 lbx_<넷> 으로 떼고, 수동소자·gate 는
    원래 넷에 남는다. Vlb_<넷> <넷> lbx_<넷>(수신 쪽 +) AC ½, Ilb_<넷> 0 <넷>, 입력은 AC 0. meta.cm_loop break_nets·weights ½."""
    inp = cm_input(make_lut(tmp_path / "lut.npz"))
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-800:]
    cl = (tmp_path / "t.free.cmloop.cir").read_text(encoding="utf-8")
    assert _tok(cl, "XM1")[1] == "lbx_op" and _tok(cl, "XM2")[1] == "lbx_om"          # NMOS 구동자 drain
    assert _tok(cl, "XM3")[1] == "lbx_op" and _tok(cl, "XM4")[1] == "lbx_om"          # PMOS 부하 drain(구동자)
    assert _tok(cl, "XM3")[2] == "c" and _tok(cl, "XM3")[3] == "vdd"                  # gate·source 그대로
    assert _tok(cl, "Rp_R1")[1:3] == ["op", "c"] and _tok(cl, "Rp_R2")[1:3] == ["c", "om"]   # 소비자(평균망)는 n 쪽
    assert _tok(cl, "Cp_CL1")[1:3] == ["op", "0"]
    for net in ("op", "om"):
        v = _tok(cl, "Vlb_" + net)
        assert v[1:3] == [net, "lbx_" + net]
        up = [x.upper() for x in v]
        assert float(v[up.index("AC") + 1]) == 0.5 and float(v[up.index("DC") + 1]) == 0.0
        i = _tok(cl, "Ilb_" + net)
        assert i[1:3] == ["0", net]
    for net in ("ip", "im"):
        v = _tok(cl, "Vac_" + net)
        up = [x.upper() for x in v]
        assert float(v[up.index("AC") + 1]) == 0.0
    cm = meta["cm_loop"]
    assert sorted(cm["break_nets"]) == ["om", "op"] and cm["weights"] == [0.5, 0.5]
    assert "lbx_" not in text                                                          # 주 넷리스트는 그대로


@pytest.mark.parametrize("flag", [None, False])
def test_no_cmloop_files_without_flag(tmp_path, flag):
    """cm_output_loop 이 없거나 false 면 cmloop 파일을 만들지 않는다(기존 출력 비트 동일 -- README)."""
    inp = cm_input(make_lut(tmp_path / "lut.npz"), cm_output_loop=flag, constraint=False)
    p, _, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0
    assert not (tmp_path / "t.free.cmloop.cir").exists()
    assert not meta.get("cm_loop")


def test_cmloop_without_output_pair_blocks(tmp_path):
    """README: cm_output_loop true 인데 ports.output_p·output_n 이 없으면 막힘."""
    inp = cm_input(make_lut(tmp_path / "lut.npz"), ports={"input_p": "ip", "input_n": "im", "output": "op"},
                   constraint=False)
    p, _, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"], (p.stdout + p.stderr)[-800:]


# ---------------------------------------------------------------- ngspice

def _independent_op(root: Path):
    """CMFB 회로 DC 동작점(손 넷리스트: 입력은 이상 전압원 0.6 V, finger 마다 인스턴스) -> M1·M3 gm, gds."""
    body = [f"Vdd vdd 0 DC {CM['vdd']}", f"Vip ip 0 DC {CM['vin']}", f"Vim im 0 DC {CM['vin']}",
            f"R1 op c {CM['r']}", f"R2 c om {CM['r']}"]
    for i in range(CM["n"]):
        body += [f"XM1_{i} op ip 0 0 {NFET} l={CM['L']} w={CM['fw']}", f"XM2_{i} om im 0 0 {NFET} l={CM['L']} w={CM['fw']}",
                 f"XM3_{i} op c vdd vdd {PFET} l={CM['L']} w={CM['fw']}", f"XM4_{i} om c vdd vdd {PFET} l={CM['L']} w={CM['fw']}"]
    prints = [probe(k, f"{inst}_{i}", q) for k, inst in (("nmos", "xm1"), ("pmos", "xm3")) for i in range(CM["n"])
              for q in ("gm", "gds")]
    op = run_spice("\n".join(body), root, prints)["op"]
    g = lambda k, inst, q: sum(op[probe(k, f"{inst}_{i}", q).lower()] for i in range(CM["n"]))   # noqa: E731
    return {"gm1": g("nmos", "xm1", "gm"), "gds1": g("nmos", "xm1", "gds"),
            "gmp": g("pmos", "xm3", "gm"), "gdsp": g("pmos", "xm3", "gds")}


def _hand_t(f, d, extra_c=0.0):
    """(a) 손유도 CM 루프 이득(반회로): T = gmp/((Go + sCL')(1 + sR·Cg')+ sCg'), Go = gds1 + gdsp, Cg' = Cg/2 (+ extra), CL' = CL (+ extra)."""
    s = 2j * np.pi * np.asarray(f)
    go = d["gds1"] + d["gdsp"]
    cl, cg = CM["cl"] + extra_c, CM["cg"] / 2.0 + extra_c
    return d["gmp"] / ((go + s * cl) * (1.0 + s * CM["r"] * cg) + s * cg)


@pytest.fixture(scope="module")
def cmfb_run(tmp_path_factory):
    require_spice()
    tmp = tmp_path_factory.mktemp("cmfb")
    inp = cm_input(make_lut(tmp / "lut.npz"))
    p, res = run_oracle(inp, tmp / "out", biases=("free",), sat_margin=0.0)
    sim = json.loads((tmp / "out" / "tcm_cmfb.free.sim.json").read_text(encoding="utf-8"))
    return p, res["free"], sim, _independent_op(tmp / "ind")


def test_cm_loop_gain_and_pm_match_hand_closed_form(cmfb_run):
    p, cmp, sim, d = cmfb_run
    cm = sim["cm_loop"]
    assert cm["singular"] is None and cm["pm_undefined"] is None
    grid = ac_grid(0.01, 1e10, 40)                                    # testbench ac 격자(conftest testbench_block)
    m0 = measure(grid, _hand_t(grid, d))
    m1 = measure(grid, _hand_t(grid, d, extra_c=2.0 * C_DEV))
    tol_pm = abs(m1["pm_deg"] - m0["pm_deg"])
    tol_ugf = abs(m1["ugf_hz"] - m0["ugf_hz"]) / m0["ugf_hz"]
    assert 0.0 < tol_pm < 1.0                                          # 허용이 유의미한 크기인지(입력 확인)
    t0 = d["gmp"] / (d["gds1"] + d["gdsp"])
    assert cm["measures"]["gain_dc"] == pytest.approx(t0, rel=1e-3)
    assert cm["pm_deg"] == pytest.approx(m0["pm_deg"], abs=tol_pm)
    assert cm["measures"]["ugf_hz"] == pytest.approx(m0["ugf_hz"], rel=tol_ugf)
    s = cmp["summary"]["cm_loop"]
    assert s["pm_deg"] == cm["pm_deg"] and sorted(s["break_nets"]) == ["om", "op"]


def test_cm_constraint_judged_with_value(cmfb_run):
    """CM 루프 이득 > 1 이고 PM 값이 있으면 제약은 값으로 판정(PM ≈ 33° < 60 -> FAIL), undefined 없음(cm_loop_ineffective 아님)."""
    _, cmp, sim, _ = cmfb_run
    (c,) = [c for c in cmp["constraints"] if c["measure"] == "cm_pm_deg"]
    assert c["spice"] == sim["cm_loop"]["pm_deg"]
    assert c["judge"] == ("PASS" if c["spice"] >= 60.0 else "FAIL")
    assert c.get("undefined") is None


def test_engine_mna_matches_ngspice_cm_pm(cmfb_run):
    """엔진 대 ngspice: 같은 gm·gds·명시 용량을 엔진 MNA 에 넣고 출력 구동자 channel 단자를 LoopCut("mos") 로 끊은 probe_factor·
    analyze_loop 의 PM = 오라클 PM(위 허용 안), 엔진 T(0) = 손유도(상대 1e-12)."""
    from gmid_engine.metrics import (Capacitor, LoopCut, MosSmallSignal, Resistor, SmallSignalCircuit, analyze_loop, build_mna,
                                     cut_circuit, probe_factor, solve_responses)
    _, _, sim, d = cmfb_run
    # 노드: 0 = gnd/vdd/ip/im(교류접지), 1 = op, 2 = om, 3 = c
    mos = (MosSmallSignal(1, 0, 0, 0, d["gm1"], 0.0, d["gds1"]), MosSmallSignal(2, 0, 0, 0, d["gm1"], 0.0, d["gds1"]),
           MosSmallSignal(1, 3, 0, 0, d["gmp"], 0.0, d["gdsp"]), MosSmallSignal(2, 3, 0, 0, d["gmp"], 0.0, d["gdsp"]))
    ck = SmallSignalCircuit(mos=mos, resistors=(Resistor(1, 3, CM["r"]), Resistor(3, 2, CM["r"])),
                            capacitors=(Capacitor(1, 0, CM["cl"]), Capacitor(2, 0, CM["cl"]), Capacitor(3, 0, CM["cg"])),
                            ac_ground=(0,))
    cut = cut_circuit(ck, tuple(LoopCut("mos", i, "d") for i in range(4)))
    (r,) = solve_responses((build_mna(cut.circuit, cut.excitations, cut.senses),))
    pf = probe_factor(r, cut.pairs, (0.5, 0.5))
    la = analyze_loop((pf,))
    assert tuple(cut.pairs) == ((1, 4), (2, 5))
    assert la.dc_value == pytest.approx(d["gmp"] / (d["gds1"] + d["gdsp"]), rel=1e-12)
    grid = ac_grid(0.01, 1e10, 40)
    tol_pm = abs(measure(grid, _hand_t(grid, d, extra_c=2.0 * C_DEV))["pm_deg"] - measure(grid, _hand_t(grid, d))["pm_deg"])
    assert la.phase_margin_deg == pytest.approx(sim["cm_loop"]["pm_deg"], abs=tol_pm)


def test_no_cmfb_is_cm_loop_ineffective(tmp_path):
    """결정 A(README '판정'): CMFB 없는 회로 -- 출력 CM 주입 루프 이득 0 -> 기준점 |T_cm| ≤ 1, UGF 없음 -> cm_pm_deg 제약 FAIL,
    undefined = cm_loop_ineffective(SPICE PM 값 None), free verdict FAIL."""
    require_spice()
    inp = cm_input(make_lut(tmp_path / "lut.npz"), variant="none")
    p, res = run_oracle(inp, tmp_path / "out", biases=("free",), sat_margin=0.0)
    cmp = res["free"]
    assert cmp is not None, (p.stdout + p.stderr)[-800:]
    sim = json.loads((tmp_path / "out" / "tcm_none.free.sim.json").read_text(encoding="utf-8"))
    assert sim["cm_loop"]["measures"]["gain_dc"] <= 1.0
    assert sim["cm_loop"]["measures"]["ugf_hz"] is None
    (c,) = [c for c in cmp["constraints"] if c["measure"] == "cm_pm_deg"]
    assert c["judge"] == "FAIL" and c["undefined"] == "cm_loop_ineffective"
    assert cmp["summary"]["verdict"] == "FAIL"
