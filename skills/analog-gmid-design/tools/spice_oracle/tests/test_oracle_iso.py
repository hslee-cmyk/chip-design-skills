"""C17 --bias iso (단독 소자): 소자마다 X 인스턴스 하나를 자기 노드에 두고 소스 0, V(g)=s VGS, V(d)=s VDS, V(b)=-s VSB
(s = polarity n:+1, p:-1). .op 만. iso summary 판정 = |ID_rel| <= 소자 tol(C16).

손계산: 단자 전압은 위 식 그대로. SPICE ID 기대값은 독립 넷리스트(conftest.independent_cs 에서 nout=0.9, pout=0.16 을
이상 전압원으로 고정 -> M1 은 VGS 0.7/VDS 0.9/VSB 0, MP1 은 VGS 1.2/VDS 1.34/VSB 0.3 -- iso 와 같은 단자 조건).
"""
import copy

import pytest

from conftest import (CS, by_name, cs_input, dc_value, elem, independent_cs, kv, make_lut, run_netlist, run_oracle,
                      require_spice, x_lines)

PRED = {"M1": {"VGS": 0.7, "VDS": 0.9, "VSB": 0.0},
        "MP1": {"VGS": CS["vsp"] - CS["pb"], "VDS": CS["vsp"] - 0.16, "VSB": CS["vdd"] - CS["vsp"]}}


def iso_input(lut, devs=None, polarity=("n", "p")):
    inp = cs_input(lut, preds_devices=copy.deepcopy(devs if devs is not None else PRED))
    for kind, pol in zip(("nmos", "pmos"), polarity):
        if pol is not None:
            inp["process"]["models"][kind]["polarity"] = pol
    return inp


@pytest.fixture
def lut(tmp_path):
    return make_lut(tmp_path / "lut.npz")


# ------------------------------------------------------------------ 넷리스트
def test_iso_terminal_voltages_and_polarity(tmp_path, lut):
    inp = iso_input(lut)
    p, text, meta = run_netlist(inp, tmp_path, "iso")
    assert p.returncode == 0 and meta["blockers"] == [], (p.stdout + p.stderr)[-1000:]
    exp = {"M1": (0.7, 0.9, -0.0), "MP1": (-1.2, -1.34, +0.3)}     # (s VGS, s VDS, -s VSB)
    for name, (vg, vd, vb) in exp.items():
        for term, v in (("g", vg), ("d", vd), ("b", vb)):
            t = elem(text, f"Viso_{term}_{name}")
            assert t is not None and t[1] == f"iso_{term}_{name}" and t[2] == "0", t
            assert dc_value(t) == pytest.approx(v, abs=1e-12), (name, term)
        x = [ln.split() for ln in x_lines(text) if ln.split()[0].lower() == f"x{name}".lower()]
        assert len(x) == 1
        assert x[0][1:5] == [f"iso_d_{name}", f"iso_g_{name}", "0", f"iso_b_{name}"]
        d = next(d for d in inp["devices"] if d["name"] == name)
        k = kv(x[0])
        assert float(k["w"]) == pytest.approx(d["finger_w"]) and float(k["m"]) == d["n_fingers"] and "nf" not in k


def test_iso_has_no_circuit_or_testbench(tmp_path, lut):
    p, text, meta = run_netlist(iso_input(lut), tmp_path, "iso")
    first = [ln.split()[0] for ln in text.split(".control")[0].splitlines() if ln.split() and ln[0] not in "*."]
    assert all(n.startswith(("Viso_", "X", "x")) for n in first), first
    ctl = text.split(".control", 1)[1].lower()
    assert "ac dec" not in ctl and "\nop" in ctl


def test_iso_skips_device_without_prediction(tmp_path, lut):
    devs = copy.deepcopy(PRED)
    del devs["M1"]["VDS"]
    p, text, meta = run_netlist(iso_input(lut, devs), tmp_path, "iso")
    assert "M1" in meta["iso_skipped"] and "MP1" not in meta["iso_skipped"]
    assert elem(text, "XM1") is None and elem(text, "XMP1") is not None
    assert meta["blockers"] == []


def test_iso_skips_kind_without_polarity(tmp_path, lut):
    p, text, meta = run_netlist(iso_input(lut, polarity=("n", None)), tmp_path, "iso")
    assert "MP1" in meta["iso_skipped"] and elem(text, "XMP1") is None
    assert elem(text, "XM1") is not None


def test_iso_no_device_built_blocks(tmp_path, lut):
    p, text, meta = run_netlist(iso_input(lut, polarity=(None, None)), tmp_path, "iso")
    assert meta is not None and meta["blockers"]
    require_spice()
    p, res = run_oracle(iso_input(lut, polarity=(None, None)), tmp_path / "o", biases=("iso",))
    assert res["iso"]["summary"]["verdict"] == "BLOCKED" and p.returncode == 2


# ------------------------------------------------------------------ 시뮬레이션 + 판정
@pytest.fixture(scope="module")
def held(ref_root):
    return independent_cs(ref_root, vout_hold=0.9, pout_hold=0.16)


def _with_ids(held, scale=None, tols=None):
    devs = copy.deepcopy(PRED)
    for n in devs:
        devs[n]["ID"] = held[n]["id"] * (scale or {}).get(n, 1.0)
        if tols and n in tols:
            devs[n]["tol"] = {"ID_rel": tols[n]}
    return devs


def test_iso_spice_values_match_independent(tmp_path, lut, held):
    p, res = run_oracle(iso_input(lut, _with_ids(held)), tmp_path / "o", biases=("iso",))
    r = res["iso"]
    for n in ("M1", "MP1"):
        d = by_name(r["devices"], "name", n)
        assert d["ID_spice"] == pytest.approx(held[n]["id"], rel=2e-4), n
        assert d["VGS_spice"] == pytest.approx(PRED[n]["VGS"], abs=1e-6)
        assert d["VDS_spice"] == pytest.approx(PRED[n]["VDS"], abs=1e-6)
        assert d["VSB_spice"] == pytest.approx(PRED[n]["VSB"], abs=1e-6)
        assert d["ID_spice"] > 0


@pytest.mark.parametrize("case", ["all_within", "one_outside", "one_not_judged", "none_judged"])
def test_iso_summary_verdict(tmp_path, lut, held, case):
    tols = {"all_within": {"M1": 0.01, "MP1": 0.01}, "one_outside": {"M1": 0.01, "MP1": 0.01},
            "one_not_judged": {"M1": 0.01}, "none_judged": None}[case]
    scale = {"MP1": 1.5} if case == "one_outside" else None
    p, res = run_oracle(iso_input(lut, _with_ids(held, scale, tols)), tmp_path / "o", biases=("iso",))
    iso = res["iso"]["summary"]["iso"]
    exp = {"all_within": "PASS", "one_outside": "FAIL", "one_not_judged": "INCOMPLETE", "none_judged": "INCOMPLETE"}
    assert iso["verdict"] == exp[case], iso
    if case == "one_outside":
        assert iso["outside_tol"] == ["MP1"] and iso["within_tol"] == ["M1"]
    if case == "one_not_judged":
        assert "MP1" in iso["not_judged"] and iso["within_tol"] == ["M1"]
    assert res["iso"]["summary"]["verdict"] == "INCOMPLETE"     # iso 는 진단 모드
    assert p.returncode == 0
