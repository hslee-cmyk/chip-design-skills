"""C27 정의 일치 검사(가중 정의 막힘 + choke 유효 조건·루프 정의 기록) + C14 보강(두 단자 모두 입력 넷 -> 막힘,
루프 i 파일 열 순서) + C12 보충(compare.summary.pm_loop 옮김) + C11(가중 검사는 정의값 검사, 키 없음은 C11 막힘).

근거: README "PM 정의"(가중 정의), C11·C12 보충·C14·C27, schema 만.
- 가중 검사: metric·제약에 dc_gain_db·ugf_hz·pm_deg 가 있으면 차동 input_p_ac - input_n_ac == 1 이고 합 == 0,
  단일 input_ac == 1(정확 비교). 아니면 막힘(문장 'C27 가중 정의' 로 시작, 실제 값·measure). f3db_hz 등만 있으면 보지 않음.
- 기록: ac.dc_path_isolation(입력 넷마다 (2π fstart)² dc_choke_H ac_couple_F, output_feedback = Efb 걸림),
  ac.loop_choke_ratio(β 루프: 2회 첫 점 |V(n_k)/w_k| 와 |2π f loop_dc_choke_H| / 그 값), ac.loop_break_nets, ac.loop_weights.

기대값: 손계산 -- 되먹임 회로(conftest FB) 2회(전류 주입) 실행에서 끊은 넷 nin 의 노드 임피던스(Vlb AC 0 = 단락):
    Z = 1/(s Cin + 1/(s Lloop) + (1 - A)/Rf),  A = (-gm + 1/Rf)/(1/RL + gds + s CL + 1/Rf)   (gm, gds 독립 .op)
  차동 회로는 같은 반회로 둘(가중 ±1/2)이라 |V(n_k)/w_k| = 같은 Z, 루프 T 도 단일 반회로 T 와 같다.
"""
import copy
import json
import math
import re

import numpy as np
import pytest

import conftest

from conftest import (CS, FB, ORACLE_DIR, ac_grid, cs_input, elem, fb_input, fb_loop_gain, independent_fb, make_lut,
                      measure, run_netlist, run_oracle, run_simulate, stem_of, zero_diffusion)

F0 = 0.01
SMOKE = ORACLE_DIR / "smoke"
GAIN_MEASURES = ("dc_gain_db", "ugf_hz", "pm_deg")


# ------------------------------------------------------------------ 차동(유사 차동) 되먹임 회로: FB 반회로 두 개
def diff_input(lut, vout, *, feedback=("Rfp", "Rfn", "Cinp", "Cinn"), extra_passives=(), circuit="tdiff_fb"):
    c = FB
    devs, pas = [], []
    for s, vi, vo in (("p", "nip", "op"), ("n", "nin", "on")):
        devs.append({"name": f"M{s}", "kind": "nmos", "drain": vo, "gate": vi, "source": "gnd", "bulk": "gnd",
                     "L": c["L"], "finger_w": c["finger_w"], "n_fingers": c["n"], "W": c["finger_w"] * c["n"]})
        pas += [{"name": f"RL{s}", "kind": "resistor", "terminals": ["vdd", vo], "value": c["rload"]},
                {"name": f"CL{s}", "kind": "capacitor", "terminals": [vo, "gnd"], "value": c["cl"]},
                {"name": f"Rf{s}", "kind": "resistor", "terminals": [vo, vi], "value": c["rf"]},
                {"name": f"Cin{s}", "kind": "capacitor", "terminals": [vi, "gnd"], "value": c["cin"]}]
    inp = {
        "schema": "spice_oracle_input/1", "circuit": circuit,
        "process": fb_input(lut)["process"],
        "rails": [{"net": "vdd", "voltage": c["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": devs, "passives": pas + list(extra_passives),
        "ports": {"input_p": "nip", "input_n": "nin", "output_p": "op", "output_n": "on"},
        "predictions": {"nodes": {"nip": c["vin"], "nin": c["vin"], "op": vout, "on": vout},
                        "devices": {"Mp": {"off_current_A": 0.0}, "Mn": {"off_current_A": 0.0}}, "metrics": []},
        "testbench": conftest.testbench_block(),
    }
    inp["testbench"]["loop_dc_choke_H"] = c["loop_choke"]
    if feedback is not None:
        inp["feedback_passives"] = list(feedback)
    return zero_diffusion(inp)


def _item(measure, where):
    if where == "constraint":
        return {"acceptance": {"constraints": [{"name": "k", "measure": measure, "op": ">=", "limit": -1e30}]}}
    return {"metrics": [{"name": "k", "measure": measure, "value": 1.0}]}


def _with(inp, measure, where):
    x = _item(measure, where)
    if "acceptance" in x:
        inp["acceptance"] = x["acceptance"]
    else:
        inp["predictions"]["metrics"] = x["metrics"]
    return inp


def _c27(meta):
    return [b for b in meta["blockers"] if b.startswith("C27 가중 정의")]


@pytest.fixture(scope="module")
def fbref(ref_root):
    return independent_fb(ref_root)


@pytest.fixture
def lut(tmp_path):
    return make_lut(tmp_path / "lut.npz")


# ------------------------------------------------------------------ 가중 검사: 단일 입력
@pytest.mark.parametrize("measure", GAIN_MEASURES)
@pytest.mark.parametrize("where", ["constraint", "metric"])
@pytest.mark.parametrize("amp", [2.0, 0.5, -1.0, 1.0 + 1e-12])
def test_single_input_weight_not_one_blocks(tmp_path, lut, measure, where, amp):
    inp = _with(cs_input(lut), measure, where)
    inp["testbench"]["ac"]["input_ac"] = amp
    p, text, meta = run_netlist(inp, tmp_path)
    b = _c27(meta)
    assert b, (measure, where, amp, meta["blockers"])
    assert measure in b[0] and (repr(amp) in b[0] or f"{amp:g}" in b[0]), b[0]


@pytest.mark.parametrize("measure", GAIN_MEASURES)
def test_single_input_weight_one_not_blocked(tmp_path, lut, measure):
    inp = _with(cs_input(lut), measure, "metric")
    inp["testbench"]["ac"]["input_ac"] = 1.0
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and meta["blockers"] == [], meta["blockers"]


@pytest.mark.parametrize("measure", ["f3db_hz", "supply_current_A", None])
def test_scale_free_measures_do_not_trigger_check(tmp_path, lut, measure):
    """f3db_hz(배율 무관)·supply_current_A 만 있거나 아무 measure 도 없으면 input_ac = 2 여도 검사하지 않는다."""
    inp = cs_input(lut)
    if measure is not None:
        _with(inp, measure, "metric")
        if measure == "supply_current_A":
            inp["predictions"]["metrics"][0]["rail"] = "vdd"
    inp["testbench"]["ac"]["input_ac"] = 2.0
    p, text, meta = run_netlist(inp, tmp_path)
    assert p.returncode == 0 and _c27(meta) == [] and meta["blockers"] == [], meta["blockers"]


def test_rout_and_ratio_measures_do_not_trigger_check(tmp_path, lut):
    inp = cs_input(lut, constraints=[
        {"name": "r", "measure": "rout_ohm", "op": ">=", "limit": 0.0,
         "view": {"sense_p": "nout", "sense_mode": "single_ended"}},
        {"name": "q", "measure": "ratio_db", "op": ">=", "limit": 0.0,
         "view": {"num": {"ac_excite": {"nin": 1.0}, "sense_p": "nout", "sense_n": None, "sense_mode": "single_ended"},
                  "den": {"ac_excite": {"vdd": 1.0}, "sense_p": "nout", "sense_n": None,
                          "sense_mode": "single_ended"}}}])
    inp["testbench"]["ac"]["input_ac"] = 2.0
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta["blockers"] == [], meta["blockers"]


def test_missing_weight_key_is_c11_not_c27(tmp_path, lut):
    """해당 키가 없으면 C27 은 보지 않고 C11(필요한 선택 testbench 값 없음 -> 막힘)이 막는다."""
    inp = _with(cs_input(lut), "dc_gain_db", "metric")
    del inp["testbench"]["ac"]["input_ac"]
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"] and _c27(meta) == [], meta and meta["blockers"]


def test_weight_block_in_run_is_blocked_rc2(tmp_path, lut):
    inp = _with(cs_input(lut), "pm_deg", "constraint")
    inp["testbench"]["ac"]["input_ac"] = 2.0
    p, res = run_oracle(inp, tmp_path / "o", biases=("free", "forced"), sat_margin=0.05)
    assert p.returncode == 2
    for b in ("free", "forced"):
        assert res[b]["summary"]["verdict"] == "BLOCKED", b


# ------------------------------------------------------------------ 가중 검사: 차동 입력
@pytest.mark.parametrize("pn,ok", [((0.5, -0.5), True), ((1.0, -1.0), False), ((0.6, -0.4), False),
                                   ((-0.5, 0.5), False), ((0.5, 0.5), False), ((1.0, 0.0), False)])
@pytest.mark.parametrize("measure", GAIN_MEASURES)
def test_differential_weights(tmp_path, lut, fbref, pn, ok, measure):
    inp = _with(diff_input(lut, fbref["vout"]), measure, "metric")
    inp["testbench"]["ac"].update({"input_p_ac": pn[0], "input_n_ac": pn[1], "input_ac": 3.0})  # input_ac 는 무관
    p, text, meta = run_netlist(inp, tmp_path)
    if ok:
        assert meta["blockers"] == [], meta["blockers"]
    else:
        b = _c27(meta)
        assert b and measure in b[0], meta["blockers"]


def test_differential_weight_check_absent_without_gain_measure(tmp_path, lut, fbref):
    inp = diff_input(lut, fbref["vout"])
    inp["testbench"]["ac"].update({"input_p_ac": 1.0, "input_n_ac": -1.0})
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta["blockers"] == [], meta["blockers"]


def test_weight_check_also_with_beta_loop(tmp_path, lut):
    """β 루프 선언 회로(가중이 루프 절단 가중)에서도 막힘."""
    inp = _with(fb_input(lut), "pm_deg", "metric")
    inp["testbench"]["ac"]["input_ac"] = 0.5
    p, text, meta = run_netlist(inp, tmp_path)
    assert _c27(meta), meta["blockers"]


# ------------------------------------------------------------------ 기록: dc_path_isolation, loop_* (sim.ac)
def _sim(inp, d, bias="free"):
    p, text, meta = run_netlist(inp, d, bias)
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-1500:]
    cir, sim = d / f"t.{bias}.cir", d / f"t.{bias}.sim.json"
    q = run_simulate(cir, sim, d)
    assert q.returncode == 0 and sim.exists(), (q.stdout + q.stderr)[-1500:]
    return json.loads(sim.read_text(encoding="utf-8")), text


def _hand_z(f, gm, gds):
    c = FB
    s = 2j * math.pi * f
    a = (-gm + 1 / c["rf"]) / (1 / c["rload"] + gds + s * c["cl"] + 1 / c["rf"])
    return 1 / (s * c["cin"] + 1 / (s * c["loop_choke"]) + (1 - a) / c["rf"])


@pytest.fixture(scope="module")
def fb_free(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("c27_fb")
    return _sim(fb_input(make_lut(d / "lut.npz")), d)


@pytest.fixture(scope="module")
def diff_free(tmp_path_factory, ref_root):
    d = tmp_path_factory.mktemp("c27_diff")
    return _sim(diff_input(make_lut(d / "lut.npz"), independent_fb(ref_root)["vout"]), d)


def _iso_expect(text, nets):
    tb = conftest.testbench_block()
    w = (2 * math.pi * tb["ac"]["fstart_hz"]) ** 2 * tb["dc_choke_H"] * tb["ac_couple_F"]
    return {n: {"choke_H": tb["dc_choke_H"], "couple_F": tb["ac_couple_F"], "f_hz": F0, "omega2_LC": w,
                "output_feedback": elem(text, f"Efb_{n}") is not None} for n in nets}


@pytest.mark.parametrize("which", ["fb", "diff"])
def test_dc_path_isolation_record(fb_free, diff_free, which):
    (sim, text), nets = (fb_free, ["nin"]) if which == "fb" else (diff_free, ["nip", "nin"])
    rows = sim["ac"]["dc_path_isolation"]
    assert sorted(r["net"] for r in rows) == sorted(nets), rows
    exp = _iso_expect(text, nets)
    for r in rows:
        e = exp[r["net"]]
        for k in ("choke_H", "couple_F", "f_hz", "omega2_LC"):
            assert r[k] == pytest.approx(e[k], rel=1e-9), (k, r)
        assert r["output_feedback"] is e["output_feedback"], (r, e)


def test_dc_path_isolation_forced_has_no_output_feedback(tmp_path, lut, fbref):
    inp = fb_input(lut)
    inp["predictions"]["nodes"]["nout"] = fbref["vout"]
    sim, text = _sim(inp, tmp_path, "forced")
    rows = sim["ac"]["dc_path_isolation"]
    assert [r["net"] for r in rows] == ["nin"]
    assert rows[0]["output_feedback"] is False and elem(text, "Efb_nin") is None


@pytest.mark.parametrize("which", ["fb", "diff"])
def test_loop_choke_ratio_matches_hand_impedance(fb_free, diff_free, fbref, which):
    sim, _ = fb_free if which == "fb" else diff_free
    nets = {"nin": 1.0} if which == "fb" else {"nip": 0.5, "nin": -0.5}
    rows = sim["ac"]["loop_choke_ratio"]
    assert sorted(r["net"] for r in rows) == sorted(nets), rows
    z = abs(_hand_z(F0, fbref["gm"], fbref["gds"]))
    for r in rows:
        assert r["f_hz"] == pytest.approx(F0) and r["choke_H"] == pytest.approx(FB["loop_choke"], rel=1e-12)
        assert r["node_impedance_ohm"] == pytest.approx(z, rel=2e-3), (r, z)
        assert r["ratio"] == pytest.approx(2 * math.pi * F0 * FB["loop_choke"] / r["node_impedance_ohm"], rel=1e-9)
        assert r["ratio"] > 1e6                                    # choke 열림 조건(이 회로)
    assert sim["ac"]["loop_break_nets"] and sorted(sim["ac"]["loop_break_nets"]) == sorted(nets)
    assert sim["ac"]["loop_weights"] == nets


def test_diff_beta_loop_pm_equals_half_circuit_T(diff_free, fbref):
    """가중 ±1/2 차동 루프 T = 반회로 T(해석식): 가중 정의가 차동 모드를 고른다."""
    sim, _ = diff_free
    grid = ac_grid(0.01, 1e10, 40)
    mt = measure(grid, fb_loop_gain(grid, fbref["gm"], fbref["gds"]))
    assert sim["ac"]["pm_definition"] == "beta_loop"
    assert sim["ac"]["pm_deg"] == pytest.approx(mt["pm_deg"], abs=0.5)
    assert sim["ac"]["loop_gain_dc_db"] == pytest.approx(mt["dc_gain_db"], abs=0.05)


def test_beta1_loop_records(tmp_path, lut):
    inp = cs_input(lut, diffusion="zero")
    inp["testbench"]["ac"]["input_ac"] = 1.0
    sim, _ = _sim(inp, tmp_path)
    ac = sim["ac"]
    assert ac["pm_definition"] == "beta_1"
    assert ac["loop_break_nets"] == [] and ac["loop_choke_ratio"] is None
    assert ac["loop_weights"] == {"nin": 1.0}


# ------------------------------------------------------------------ C12 보충: compare.summary.pm_loop
@pytest.mark.parametrize("basis", ["spec_feedback_elements", "legacy_c12_input_net_passives", "임의 표지 x", None])
def test_pm_loop_summary_carries_basis_verbatim(tmp_path, lut, basis):
    inp = fb_input(lut)
    inp["predictions"]["devices"] = {"M1": {"off_current_A": 0.0}}
    if basis is not None:
        inp["feedback_passives_basis"] = basis
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    pl = c["summary"]["pm_loop"]
    assert pl["feedback_passives_basis"] == basis
    assert pl["pm_definition"] == "beta_loop" and sorted(pl["feedback_passives"]) == ["Cin", "Rf"]
    assert pl["loop_break_nets"] == ["nin"] and pl["loop_weights"] == {"nin": 1.0}


def test_basis_empty_string_rejected_by_schema(tmp_path, lut):
    inp = fb_input(lut)
    inp["feedback_passives_basis"] = ""
    out = tmp_path / "o"
    p, res = run_oracle(inp, out, sat_margin=0.05)
    assert p.returncode == 2 and sorted(x.name for x in out.iterdir()) == ["t.input.json"]


# ------------------------------------------------------------------ C14 보강: 두 단자 모두 입력 넷 -> 막힘
def test_c14_both_terminals_same_input_net_blocks(tmp_path, lut):
    inp = fb_input(lut, feedback=("Rf", "Cin", "Cx"))
    inp["passives"].append({"name": "Cx", "kind": "capacitor", "terminals": ["nin", "nin"], "value": 1e-12})
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and any("Cx" in b for b in meta["blockers"]), meta and meta["blockers"]
    q, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    assert res["free"]["summary"]["verdict"] == "BLOCKED" and q.returncode == 2
    assert not list((tmp_path / "o").glob("*.loop.i.txt"))          # ngspice 루프를 돌리지 않음


def test_c14_between_two_input_nets_blocks(tmp_path, lut, fbref):
    cpn = {"name": "Cpn", "kind": "capacitor", "terminals": ["nip", "nin"], "value": 1e-12}
    inp = diff_input(lut, fbref["vout"], feedback=("Rfp", "Rfn", "Cinp", "Cinn", "Cpn"), extra_passives=[cpn])
    p, text, meta = run_netlist(inp, tmp_path)
    bl = [b for b in meta["blockers"] if "Cpn" in b]
    assert bl, meta["blockers"]
    assert "nip" in bl[0] and "nin" in bl[0], bl                     # 단자도 적는다
    for other in ("Rfp", "Rfn", "Cinp", "Cinn"):                     # 정상 소자는 막힘 문장에 없다
        assert all(other not in b for b in meta["blockers"]), meta["blockers"]


def test_c14_input_to_input_passive_not_declared_is_fine(tmp_path, lut, fbref):
    """대조: 같은 Cpn 이 있어도 되먹임으로 선언하지 않으면 막히지 않는다."""
    cpn = {"name": "Cpn", "kind": "capacitor", "terminals": ["nip", "nin"], "value": 1e-12}
    inp = diff_input(lut, fbref["vout"], extra_passives=[cpn])
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta["blockers"] == [], meta["blockers"]


# ------------------------------------------------------------------ C14: 루프 i 파일 열(i 다음 같은 순서 v)
def _wrdata_i(loop_text):
    lines = [ln.split() for ln in loop_text.splitlines() if ln.strip().lower().startswith("wrdata")
             and ln.split()[1].lower().endswith(".loop.i.txt")]
    assert len(lines) == 1, lines
    return [t.lower() for t in lines[0][2:]]


def _check_i_columns(cols, nets):
    nets = [n.lower() for n in nets]
    k = len(nets)
    assert len(cols) == 2 * k, cols
    i_nets = [re.fullmatch(r"i\(vlb_(.+)\)", c).group(1) for c in cols[:k]]
    v_nets = [re.fullmatch(r"v\((.+)\)", c).group(1) for c in cols[k:]]
    assert sorted(i_nets) == sorted(nets) and v_nets == i_nets, cols


@pytest.mark.parametrize("which", ["fb", "diff"])
def test_loop_i_file_columns(tmp_path, lut, fbref, which):
    inp = fb_input(lut) if which == "fb" else diff_input(lut, fbref["vout"])
    nets = ["nin"] if which == "fb" else ["nip", "nin"]
    p, text, meta = run_netlist(inp, tmp_path)
    loop = (tmp_path / "t.free.loop.cir").read_text(encoding="utf-8")
    _check_i_columns(_wrdata_i(loop), nets)


@pytest.mark.parametrize("v", ["sizing.engine", "layout.engine", "layout.topology"])
def test_committed_smoke_input_carries_legacy_basis(v):
    """C12 보충: 어댑터(옛 기준선)는 feedback_passives_basis = 'legacy_c12_input_net_passives' 를 쓴다.
    커밋된 smoke 입력은 어댑터 산출물이고 --run-legacy 의 '새 실행 = 커밋된 smoke 입력' test 기준이기도 하다."""
    inp = json.loads((SMOKE / f"current_reuse_telescopic_ota.{v}.oracle_input.json").read_text(encoding="utf-8"))
    assert inp.get("feedback_passives_basis") == "legacy_c12_input_net_passives", inp.get("feedback_passives_basis")


@pytest.mark.parametrize("v", ["sizing.engine", "layout.engine", "layout.topology"])
@pytest.mark.parametrize("bias", ["free", "forced"])
def test_committed_smoke_loop_i_columns_follow_c14(v, bias):
    """커밋된 smoke 루프 넷리스트(재생성 일치 test 의 기준 파일)가 C14 열 규칙을 따르는지 독립 확인:
    끊은 넷 = smoke 입력에서 직접 계산(feedback_passives 가 물린 입력 포트 넷)."""
    circ = "current_reuse_telescopic_ota"
    inp = json.loads((SMOKE / f"{circ}.{v}.oracle_input.json").read_text(encoding="utf-8"))
    in_nets = {inp["ports"][k] for k in ("input_p", "input_n", "input") if k in inp["ports"]}
    pas = {x["name"]: x for x in inp["passives"]}
    nets = sorted({t for n in inp["feedback_passives"] for t in pas[n]["terminals"] if t in in_nets})
    loop = (SMOKE / f"{circ}.{v}.{bias}.loop.cir").read_text(encoding="utf-8", errors="replace")
    _check_i_columns(_wrdata_i(loop), nets)
