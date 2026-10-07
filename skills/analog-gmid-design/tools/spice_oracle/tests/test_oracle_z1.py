"""C18 Z1 제거법: --omit <원소..>(넷리스트에서 뺌), --short <수동소자..>(Vshort_<name> 0 V 원). 막힘 4종.
free verdict 는 막힘이 없으면 INCOMPLETE. 손계산: RL(vdd-nout) 단락 -> V(nout) = VDD = 1.8 V.
"""
import pytest

import copy

from conftest import (CS, OFF_ZERO, by_name, cs_input, dc_value, elem, fb_input, make_lut, run_netlist, run_oracle,
                      require_spice)


@pytest.fixture
def lut(tmp_path):
    return make_lut(tmp_path / "lut.npz")


def cs(lut):
    inp = cs_input(lut, preds_devices=copy.deepcopy(OFF_ZERO))  # [C23 조정] 전도 문턱 0(옛 ID > 0 규칙) 명시
    inp["sources"] = [{"name": "I1", "kind": "current", "terminals": ["vdd", "nout"], "value": 1e-7}]
    return inp


def test_omit_removes_elements(tmp_path, lut):
    p, text, meta = run_netlist(cs(lut), tmp_path, extra=["--omit", "MP1", "RP", "I1"])
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-800:]
    assert elem(text, "XMP1") is None and elem(text, "Rp_RP") is None and elem(text, "Isrc_I1") is None
    assert elem(text, "XM1") is not None and elem(text, "Rp_RL") is not None


def test_short_replaces_passive_with_zero_volt_source(tmp_path, lut):
    p, text, meta = run_netlist(cs(lut), tmp_path, extra=["--short", "CL"])
    assert meta["blockers"] == []
    assert elem(text, "Cp_CL") is None
    t = elem(text, "Vshort_CL")
    assert t is not None and set(t[1:3]) == {"nout", "0"} and dc_value(t) == 0.0


def test_short_rl_hand_value_and_verdict_incomplete(tmp_path, lut):
    require_spice()
    p, res = run_oracle(cs(lut), tmp_path / "o", sat_margin=0.0, tag="z1", extra=["--short", "RL"])
    r = res["free"]
    assert by_name(r["nodes"], "net", "nout")["V_spice"] == pytest.approx(CS["vdd"], abs=1e-6)
    assert r["blockers"] == [] and r["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0


def test_omit_device_no_row_and_listed_verdict_incomplete(tmp_path, lut):
    """대조: 같은 입력·sat_margin 으로 Z1 없이 돌리면 PASS(M1/MP1 여유 ~0.83/1.14 V > 0.05) -- omit 하면 INCOMPLETE."""
    require_spice()
    p0, res0 = run_oracle(cs(lut), tmp_path / "base", sat_margin=0.05)
    assert res0["free"]["summary"]["verdict"] == "PASS"
    p, res = run_oracle(cs(lut), tmp_path / "o", sat_margin=0.05, tag="z1", extra=["--omit", "MP1"])
    r = res["free"]
    assert [d["name"] for d in r["devices"]] == ["M1"]
    assert r["summary"]["z1"]["omitted_devices"] == ["MP1"]
    assert r["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0


@pytest.mark.parametrize("args", [["--omit", "Nope"], ["--short", "Nope"], ["--short", "M1"], ["--short", "I1"],
                                  ["--omit", "RL", "RL"], ["--omit", "RL", "--short", "RL"]],
                         ids=["omit_unknown", "short_unknown", "short_device", "short_source", "omit_dup",
                              "omit_and_short_same"])
def test_bad_z1_blocks(tmp_path, lut, args):
    p, text, meta = run_netlist(cs(lut), tmp_path, extra=args)
    assert meta is not None and meta["blockers"], (args, p.returncode, (p.stdout + p.stderr)[-500:])


@pytest.mark.parametrize("args", [["--short", "Rf"], ["--omit", "Cin"]])
def test_feedback_passive_change_blocks(tmp_path, lut, args):
    p0, _, meta0 = run_netlist(fb_input(lut), tmp_path / "ok")
    assert meta0["blockers"] == []
    p, text, meta = run_netlist(fb_input(lut), tmp_path / "bad", extra=args)
    assert meta is not None and meta["blockers"], args
