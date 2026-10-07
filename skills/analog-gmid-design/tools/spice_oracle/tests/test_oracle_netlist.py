"""oracle_netlist.py -- 계약 C2(코너·온도), C3(finger), C4(레일), C5(free/forced 테스트벤치), C6(게이트 전용 넷).

넷리스트 텍스트와 <out>.cir.meta.json 만 본다(시뮬레이션 없음). 기대값은 입력 값과 계약 문장에서 직접 만든다.
"""
import copy
import math

import pytest

from conftest import (CS, FB, cs_input, dc_value, elem, fb_input, kv, make_lut, run_netlist, x_lines)


@pytest.fixture
def lut(tmp_path):
    return make_lut(tmp_path / "lut.npz")


def ok(p, meta):
    assert p.returncode == 0, (p.stdout + p.stderr)[-2000:]
    assert meta is not None


def close(a, b, rel=1e-9):
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=1e-30)


# ------------------------------------------------------------------ C2
@pytest.mark.parametrize("corner,temp", [("tt", 27.0), ("ff", 50.0), ("ss", -40.0)])
def test_c2_temp_and_corner_from_npz(tmp_path, corner, temp):
    lut = make_lut(tmp_path / "lut.npz", corner=corner, temp_c=temp)
    p, text, meta = run_netlist(cs_input(lut), tmp_path)
    ok(p, meta)
    temps = [ln.split()[1] for ln in text.splitlines() if ln.lower().startswith(".temp")]
    assert len(temps) == 1 and float(temps[0]) == temp
    incs = [ln for ln in text.splitlines() if ln.lower().startswith(".include")]
    assert incs and not any("{corner}" in ln for ln in incs)
    assert any(f"nfet_01v8__{corner}.pm3.spice" in ln for ln in incs)
    assert any(f"pfet_01v8__{corner}.pm3.spice" in ln for ln in incs)
    assert meta["lut_meta"]["corner"] == corner and float(meta["lut_meta"]["temp_c"]) == temp
    assert meta["blockers"] == []


@pytest.mark.parametrize("missing", ["corner", "temp_c"])
def test_c2_missing_npz_meta_blocks(tmp_path, missing):
    kw = {"corner": "tt", "temp_c": 27.0}
    kw[missing] = None
    lut = make_lut(tmp_path / "lut.npz", **kw)
    p, text, meta = run_netlist(cs_input(lut), tmp_path)
    assert meta is not None, (p.stdout + p.stderr)[-1500:]
    assert meta["blockers"], f"npz 에 {missing} 가 없는데 막힘이 없다"
    if missing == "temp_c":   # C2 [변경]: temp_c 가 없으면 .temp 줄을 쓰지 않는다
        assert text is not None and not any(ln.lower().startswith(".temp") for ln in text.splitlines())


# ------------------------------------------------------------------ C3
def _dev_line(text, name):
    xs = [ln for ln in x_lines(text) if ln.split()[0].lower() == f"x{name}".lower()]
    assert len(xs) == 1, f"X{name} 줄이 {len(xs)}개: {xs}"
    return xs[0].split()


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_c3_one_instance_w_finger_m_nfingers_no_nf(tmp_path, lut, bias):
    inp = cs_input(lut, preds_nodes={"nout": 0.9, "pout": 0.16})
    p, text, meta = run_netlist(inp, tmp_path, bias=bias)
    ok(p, meta)
    assert len(x_lines(text)) == len(inp["devices"])
    for d in inp["devices"]:
        t = _dev_line(text, d["name"])
        assert t[1:5] == [d["drain"] if d["drain"] != "gnd" else "0", d["gate"],
                          d["source"] if d["source"] != "gnd" else "0", d["bulk"] if d["bulk"] != "gnd" else "0"]
        assert t[5] == inp["process"]["models"][d["kind"]]["subckt"]
        p_ = kv(t[6:])
        assert "nf" not in p_
        assert close(p_["w"], d["finger_w"]) and close(p_["l"], d["L"])
        assert int(float(p_["m"])) == d["n_fingers"] and float(p_["m"]) == d["n_fingers"]


def test_c3_diffusion_rule(tmp_path, lut):
    inp = cs_input(lut)
    ad_per_w, pd_extra = inp["process"]["diffusion"]["ad_per_w_m"], inp["process"]["diffusion"]["pd_extra_m"]
    p, text, meta = run_netlist(inp, tmp_path)
    ok(p, meta)
    for d in inp["devices"]:
        p_ = kv(_dev_line(text, d["name"])[6:])
        fw = d["finger_w"]
        assert close(p_["ad"], ad_per_w * fw) and close(p_["as"], ad_per_w * fw)
        assert close(p_["pd"], fw + pd_extra) and close(p_["ps"], fw + pd_extra)


def test_c3_no_diffusion_no_area_params(tmp_path, lut):
    p, text, meta = run_netlist(cs_input(lut, diffusion=False), tmp_path)
    ok(p, meta)
    for ln in x_lines(text):
        assert not set(kv(ln.split())) & {"ad", "as", "pd", "ps", "nf"}, ln


def test_c3_declared_W_does_not_change_instance(tmp_path, lut):
    """W 는 보고용(W_rel). 선언 W 가 finger 곱과 달라도 인스턴스는 w=finger_w m=n_fingers."""
    p, text, meta = run_netlist(cs_input(lut, W=CS["finger_w"] * CS["n"] / 2), tmp_path)
    ok(p, meta)
    p_ = kv(_dev_line(text, "M1")[6:])
    assert close(p_["w"], CS["finger_w"]) and float(p_["m"]) == CS["n"]


# ------------------------------------------------------------------ C4
def test_c4_reference_is_node0_other_rails_sources(tmp_path, lut):
    p, text, meta = run_netlist(cs_input(lut), tmp_path)
    ok(p, meta)
    assert meta["blockers"] == []
    body = [ln.split() for ln in text.splitlines() if ln and ln[0] not in "*." and not ln.startswith("print")]
    assert not any("gnd" in t for t in body), "reference 넷 gnd 가 SPICE 노드 0 으로 바뀌지 않았다"
    for net, v in (("vdd", CS["vdd"]), ("vsp", CS["vsp"])):
        t = elem(text, f"Vrail_{net}")
        assert t is not None and t[1] == net and t[2] == "0" and close(dc_value(t), v)
    assert elem(text, "Vrail_gnd") is None


@pytest.mark.parametrize("case", ["none", "two"])
def test_c4_reference_count_not_one_blocks(tmp_path, lut, case):
    inp = cs_input(lut)
    if case == "none":
        inp["rails"][2].pop("reference")
    else:
        inp["rails"][1]["reference"] = True
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"], f"reference {case}: 막힘 없음 rc={p.returncode}"


def test_c4_case_only_different_nets_block(tmp_path, lut):
    inp = cs_input(lut)
    inp["passives"][0]["terminals"] = ["vdd", "NOUT"]  # 소자 드레인은 nout
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"], "nout/NOUT 대소문자 충돌인데 막힘 없음"


def test_c4_case_alias_of_rail_with_same_voltage_is_not_blocked(tmp_path, lut):
    inp = cs_input(lut)
    inp["rails"].append({"net": "VDD", "voltage": CS["vdd"]})
    inp["devices"][1]["bulk"] = "VDD"
    p, text, meta = run_netlist(inp, tmp_path)
    ok(p, meta)
    assert meta["blockers"] == []


def test_c4_case_alias_of_rail_with_other_voltage_blocks(tmp_path, lut):
    inp = cs_input(lut)
    inp["rails"].append({"net": "VDD", "voltage": 1.2})
    inp["devices"][1]["bulk"] = "VDD"
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"]


# ------------------------------------------------------------------ C5 free
def test_c5_free_single_input_dc_source_and_choke(tmp_path, lut):
    inp = cs_input(lut)
    p, text, meta = run_netlist(inp, tmp_path, "free")
    ok(p, meta)
    v = elem(text, "Vdc_nin")
    assert v is not None and close(dc_value(v), CS["vin"])
    ls = [ln.split() for ln in text.splitlines() if ln.split() and ln.split()[0][:1] in "Ll"
          and "nin" in ln.split()[1:3]]
    assert len(ls) == 1 and close(ls[0][3], inp["testbench"]["dc_choke_H"])
    assert not any(ln.split()[0].lower().startswith("efb_") for ln in text.splitlines() if ln.split())
    assert not any(ln.split()[0].lower().startswith("vhold_") for ln in text.splitlines() if ln.split())


def _diff_in_single_out(lut):
    inp = cs_input(lut, preds_nodes={"nout": 0.9, "nin2": 0.65, "pout": 0.16})
    inp["devices"].append({"name": "M2", "kind": "nmos", "drain": "nout", "gate": "nin2", "source": "gnd",
                           "bulk": "gnd", "L": 0.5e-6, "finger_w": 2e-6, "n_fingers": 1, "W": 2e-6})
    inp["ports"] = {"input_p": "nin", "input_n": "nin2", "output": "nout"}
    return inp


def test_c5_free_single_output_feeds_back_to_input_n(tmp_path, lut):
    inp = _diff_in_single_out(lut)
    p, text, meta = run_netlist(inp, tmp_path, "free")
    ok(p, meta)
    e = elem(text, "Efb_nin2")
    assert e is not None, "단일 출력인데 out -> input_n 되먹임 Efb_nin2 없음"
    assert e[3:5] == ["nout", "0"] and close(e[5], 1.0)
    o = elem(text, "Vofs_nin2")
    assert o is not None and close(dc_value(o), 0.9 - 0.65)
    assert elem(text, "Efb_nin") is None
    v = elem(text, "Vdc_nin")
    assert v is not None and close(dc_value(v), CS["vin"])


def _diff_in_diff_out(lut):
    inp = cs_input(lut, preds_nodes={"nout": 0.9, "nout2": 0.95, "nin2": 0.65, "pout": 0.16})
    inp["devices"].append({"name": "M2", "kind": "nmos", "drain": "nout2", "gate": "nin2", "source": "gnd",
                           "bulk": "gnd", "L": 0.5e-6, "finger_w": 2e-6, "n_fingers": 2, "W": 4e-6})
    inp["passives"].append({"name": "RL2", "kind": "resistor", "terminals": ["vdd", "nout2"], "value": 1e5})
    inp["ports"] = {"input_p": "nin", "input_n": "nin2", "output_p": "nout", "output_n": "nout2"}
    return inp


def test_c5_free_diff_out_feeds_differential_component(tmp_path, lut):
    inp = _diff_in_diff_out(lut)
    k = inp["testbench"]["ac"]["diff_feedback_gain"]
    p, text, meta = run_netlist(inp, tmp_path, "free")
    ok(p, meta)
    ep, en = elem(text, "Efb_nin"), elem(text, "Efb_nin2")
    assert ep is not None and en is not None
    # 반대 극성 입력으로: input_p <- k*(out_n - out_p), input_n <- k*(out_p - out_n)
    assert ep[3:5] == ["nout2", "nout"] and close(ep[5], k)
    assert en[3:5] == ["nout", "nout2"] and close(en[5], k)
    assert close(dc_value(elem(text, "Vofs_nin")), -CS["vin"])
    assert close(dc_value(elem(text, "Vofs_nin2")), -0.65)


def test_c5_free_nodeset_from_predictions(tmp_path, lut):
    inp = cs_input(lut, preds_nodes={"nout": 0.9, "pout": 0.16})
    inp["testbench"]["nodeset_from_predictions"] = True
    p, text, meta = run_netlist(inp, tmp_path, "free")
    ok(p, meta)
    ns = " ".join(ln for ln in text.splitlines() if ln.lower().startswith(".nodeset"))
    assert "v(nout)=0.9" in ns.replace(" ", "") and "v(pout)=0.16" in ns.replace(" ", "")
    p, text, meta = run_netlist(inp, tmp_path / "f", "forced")
    ok(p, meta)
    assert not any(ln.lower().startswith(".nodeset") for ln in text.splitlines())


# ------------------------------------------------------------------ C5 forced
def test_c5_forced_holds_device_nets_except_rails_inputs_gate_bias(tmp_path, lut):
    inp = cs_input(lut, preds_nodes={"nout": 0.9, "pout": 0.16, "pb": 0.3})
    p, text, meta = run_netlist(inp, tmp_path, "forced")
    ok(p, meta)
    holds = {ln.split()[0][6:] for ln in text.splitlines() if ln.split() and ln.split()[0].lower().startswith("vhold_")}
    assert holds == {"nout", "pout"}
    for net, v in (("nout", 0.9), ("pout", 0.16)):
        t = elem(text, f"Vhold_{net}")
        assert close(dc_value(t), v)
        ls = [ln.split() for ln in text.splitlines()
              if ln.split() and ln.split()[0][:1] in "Ll" and net in ln.split()[1:3]]
        assert len(ls) == 1 and close(ls[0][3], inp["testbench"]["dc_choke_H"])
    assert sorted(meta["held"]) == ["nout", "pout"]


def test_c5_forced_unpredicted_net_not_held(tmp_path, lut):
    inp = cs_input(lut, preds_nodes={"nout": 0.9})
    p, text, meta = run_netlist(inp, tmp_path, "forced")
    ok(p, meta)
    assert elem(text, "Vhold_nout") is not None
    assert elem(text, "Vhold_pout") is None


# ------------------------------------------------------------------ C6
def test_c6_gate_only_net_from_bias_voltages(tmp_path, lut):
    inp = cs_input(lut, preds_nodes={"pb": 0.35})  # bias_voltages(0.3) 가 우선
    p, text, meta = run_netlist(inp, tmp_path)
    ok(p, meta)
    t = elem(text, "Vbias_pb")
    assert t is not None and t[1] == "pb" and t[2] == "0" and close(dc_value(t), CS["pb"])
    assert elem(text, "Vbias_nin") is None, "입력 넷은 게이트 전용 넷이 아니다"
    assert meta["blockers"] == []


def test_c6_gate_only_net_from_predictions_with_warning(tmp_path, lut):
    inp = cs_input(lut, preds_nodes={"pb": 0.35}, bias_voltages=None)
    p, text, meta = run_netlist(inp, tmp_path)
    ok(p, meta)
    t = elem(text, "Vbias_pb")
    assert t is not None and close(dc_value(t), 0.35)
    assert any("pb" in n for n in meta["notes"]), meta["notes"]
    assert meta["blockers"] == []


def test_c6_gate_only_net_without_value_blocks(tmp_path, lut):
    inp = cs_input(lut, bias_voltages=None)
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"]
    assert any("pb" in b for b in meta["blockers"])


# ------------------------------------------------------------------ 결정론
@pytest.mark.parametrize("bias", ["free", "forced"])
def test_netlist_deterministic(tmp_path, lut, bias):
    inp = cs_input(lut, preds_nodes={"nout": 0.9, "pout": 0.16})
    _, t1, m1 = run_netlist(inp, tmp_path / "a", bias)
    _, t2, m2 = run_netlist(copy.deepcopy(inp), tmp_path / "a", bias)
    assert t1 == t2 and m1 == m2


# ------------------------------------------------------------------ C14 β 루프 넷리스트
def _loop_text(tmp_path, inp, bias="free"):
    p, text, meta = run_netlist(inp, tmp_path, bias)
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    lp = tmp_path / f"t.{bias}.loop.cir"
    return text, meta, (lp.read_text(encoding="utf-8", errors="replace") if lp.exists() else None)


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_c14_loop_netlist_breaks_feedback_at_input(tmp_path, lut, bias):
    inp = fb_input(lut)
    inp["predictions"]["nodes"]["nout"] = 0.93
    text, meta, loop = _loop_text(tmp_path, inp, bias)
    assert meta["blockers"] == [] and loop is not None, meta["blockers"]
    # 되먹임 소자의 입력 넷 단자만 lbx_nin 으로, 반대쪽 단자는 그대로
    rf, cin = elem(loop, "Rp_Rf"), elem(loop, "Cp_Cin")
    assert rf is not None and rf[1:3] == ["nout", "lbx_nin"], rf
    assert cin is not None and cin[1:3] == ["lbx_nin", "0"], cin
    # 되먹임이 아닌 소자는 그대로
    assert elem(loop, "Rp_RL")[1:3] == ["vdd", "nout"] and elem(loop, "Cp_CL")[1:3] == ["nout", "0"]
    # 끊은 자리: 직렬 전압원(증폭기 쪽 +) + 증폭기 쪽 주입 전류원
    v = elem(loop, "Vlb_nin")
    i = elem(loop, "Ilb_nin")
    assert v is not None and v[1:3] == ["nin", "lbx_nin"], v
    assert i is not None and i[1:3] == ["0", "nin"], i
    # 그 넷의 결합 C / AC 원은 없다
    assert elem(loop, "Cac_nin") is None and elem(loop, "Vac_nin") is None
    # 입력 DC 경로 = loop_dc_choke_H
    ls = [ln.split() for ln in loop.splitlines() if ln.split() and ln.split()[0][:1] in "Ll"
          and "nin" in ln.split()[1:3]]
    assert ls and all(math.isclose(float(t[3]), FB["loop_choke"], rel_tol=1e-9) for t in ls), ls
    # 본 넷리스트는 바뀌지 않는다(되먹임 소자는 nin 에 그대로)
    assert elem(text, "Rp_Rf")[1:3] == ["nout", "nin"] and "lbx_" not in text


def test_c14_no_feedback_passives_no_loop_netlist(tmp_path, lut):
    text, meta, loop = _loop_text(tmp_path, fb_input(lut, feedback=None, loop_choke=None))
    assert loop is None and meta["blockers"] == []


@pytest.mark.parametrize("case", ["unknown_name", "not_on_input_net", "only_not_on_input_net", "no_loop_choke"])
def test_c14_bad_declaration_blocks(tmp_path, lut, case):
    """C14: 선언 이름이 passives 에 없거나, (선언 소자가) 입력 넷에 안 물리거나, loop_dc_choke_H 가 없으면 막힘.
    not_on_input_net = 입력 넷에 물린 Rf 와 함께 입력 넷에 안 물린 RL 을 선언(소자 단위 해석)."""
    if case == "only_not_on_input_net":
        inp = fb_input(lut, feedback=("RL",))
    elif case == "unknown_name":
        inp = fb_input(lut, feedback=("Rf", "Cxx"))
    elif case == "not_on_input_net":
        inp = fb_input(lut, feedback=("Rf", "RL"))
    else:
        inp = fb_input(lut, loop_choke=None)
    p, text, meta = run_netlist(inp, tmp_path)
    assert meta is not None and meta["blockers"], f"{case}: 막힘 없음 rc={p.returncode}"
