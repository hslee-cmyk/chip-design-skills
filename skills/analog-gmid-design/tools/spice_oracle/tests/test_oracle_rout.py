"""C26 출력 저항 rout_ohm + C9(제약 판정) + C8(정의 불가 -> INCOMPLETE) + C13(감지 전용 뷰 스키마) + C15(Irout_ 접두사)
+ C21(캐시에 rout 파일).

근거: README C26·C9·C8·C13·C15·C21, schema sense_view 만(오라클 소스는 열지 않는다).
- 뷰마다 .ac 한 번(fstart 한 점). 테스트벤치 이상 전압원(Vrail_/Vac_/Vbias_) AC 0, 감지 넷에 단위 AC 전류
  (single_ended: Irout_<k> 0 <sense_p>, differential: + Irout_<k>n <sense_n> 0). H = V(sp)-V(sn) 또는 V(sp).
  rout_ohm = Re(H); Re(H) < 0 -> None, undefined = negative_real_part -> 제약 N/A(정의 불가: ...) -> PASS 불가(INCOMPLETE).
- 막힘(문장 'C26 rout_ohm' 으로 시작, rout 실행 하나도 없음): reference 레일, 회로 넷 아님, 테스트벤치 구동 넷
  (비-reference 레일·입력·게이트 바이어스), differential sense_p == sense_n.

기대값(피검 코드 출력으로 만들지 않음):
  (a) 손계산 -- gm·gds·gmbs 는 손으로 쓴 독립 넷리스트의 .op(finger 마다 인스턴스, m 없음, finger 합).
      CS(nout): RL || 1/gds_M1 (M1 바디=소스=gnd, 게이트 AC 고정).  PMOS 가지(pout): RP || 1/gds_MP1(소스·바디 = 레일).
      두 가지는 이상 레일로 갈라져 차동(nout-pout) = Ro1 + Ro2.
      소스 팔로워: 1/(gm + gmbs + gds + 1/RS).  교차 결합 쌍 차동: 2/(1/RX + gds - gm) < 0.
  (b) 손으로 쓴 독립 .ac 넷리스트(이상 전압원 AC 0, 감지 넷에 AC 1 A 전류원, ac lin 1 f f).
  fstart = 0.01 Hz: 결합 C 1 F = 16 Ohm, choke 1e12 H = 6.3e10 Ohm, CL 1 pF = 1.6e13 Ohm -> 영향 < 1e-5 상대.
"""
import copy
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
import pytest

import conftest

from conftest import (CS, NFET, NGSPICE, PFET, OFF_ZERO, _includes, by_name, cs_input, elem, fb_input, independent_cs,
                      make_lut, preds_from_independent, probe, run_netlist, run_oracle, stem_of,
                      zero_diffusion)

F0 = 0.01   # testbench_block fstart_hz
SAT = 0.05


def se(sp, sn="__absent__"):
    v = {"sense_p": sp, "sense_mode": "single_ended"}
    if sn != "__absent__":
        v["sense_n"] = sn
    return v


def df(sp, sn):
    return {"sense_p": sp, "sense_n": sn, "sense_mode": "differential"}


def canon(v):
    """README C26 정규형 {sense_p, sense_n(없으면 null), sense_mode}."""
    return {"sense_p": v["sense_p"], "sense_n": v.get("sense_n"), "sense_mode": v["sense_mode"]}


# ------------------------------------------------------------------ 회로: CS(+ PMOS 가지) + 교차 결합 쌍
XC = dict(rx=1e5, L=0.5e-6, finger_w=2e-6, n=2)


def _cs_body(amps=None):
    c = CS
    body = [f"Vdd vdd 0 DC {c['vdd']} AC 0", f"Vsp vsp 0 DC {c['vsp']} AC 0",
            f"Vin nin 0 DC {c['vin']} AC 0", f"Vpb pb 0 DC {c['pb']} AC 0",
            f"RL vdd nout {c['rload']}", f"CL nout 0 {c['cl']}", f"RP pout 0 {c['rp']}"]
    for i in range(c["n"]):
        body.append(f"XM1_{i} nout nin 0 0 {NFET} l={c['L']} w={c['finger_w']}")
    for i in range(c["pn"]):
        body.append(f"XMP1_{i} pout pb vsp vdd {PFET} l={c['pL']} w={c['pfinger_w']}")
    return body


def _xc_body():
    x = XC
    body = [f"RXa vdd na {x['rx']}", f"RXb vdd nb {x['rx']}"]
    for i in range(x["n"]):
        body.append(f"XMX1_{i} na nb 0 0 {NFET} l={x['L']} w={x['finger_w']}")
        body.append(f"XMX2_{i} nb na 0 0 {NFET} l={x['L']} w={x['finger_w']}")
    return body


def _ind_rout(workdir: Path, body, sp, sn=None, prints=()):
    """손으로 쓴 넷리스트 + 감지 넷 단위 AC 전류 -> (H 복소, .op print dict)."""
    inj = [f"Iinj 0 {sp} DC 0 AC 1"] + ([f"Iinjn {sn} 0 DC 0 AC 1"] if sn else [])
    expr = f"v({sp})" if sn is None else f"v({sp})-v({sn})"
    workdir.mkdir(parents=True, exist_ok=True)
    lines = ["* independent rout run", _includes("tt"), ".temp 27.0",
             ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7", *body, *inj, ".control", "set noaskquit", "op",
             *[f"print {e}" for e in prints],
             f"ac lin 1 {F0} {F0}", f"let h = {expr}", "let hr = real(h)", "let hi = imag(h)",
             "set wr_singlescale", "wrdata h.txt hr hi", "quit", ".endc", ".end"]
    (workdir / "r.cir").write_text("\n".join(lines) + "\n", encoding="utf-8")
    p = subprocess.run([str(NGSPICE), "-b", "r.cir"], capture_output=True, text=True, cwd=str(workdir),
                       encoding="utf-8", errors="replace", timeout=120)
    op = {}
    for ln in p.stdout.splitlines():
        if " = " in ln:
            k, v = ln.split(" = ", 1)
            try:
                op[k.strip().lower()] = float(v.split()[0])
            except ValueError:
                pass
    for e in prints:
        assert e.lower() in op, (e, p.stdout[-1500:])
    arr = np.atleast_2d(np.loadtxt(workdir / "h.txt"))
    assert arr.shape[0] == 1, p.stdout[-1500:]
    return complex(arr[0, 1], arr[0, 2]), op


def _fsum(op, kind, inst, n, q):
    return sum(op[probe(kind, f"{inst}_{i}", q).lower()] for i in range(n))


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


@pytest.fixture(scope="module")
def xc_ref(ref_root):
    """교차 결합 쌍 독립 .op + 차동 rout(대칭 해인지 확인)."""
    x = XC
    pr = ["v(na)", "v(nb)"] + [probe("nmos", f"xmx1_{i}", q) for i in range(x["n"]) for q in ("gm", "gds", "id")]
    h, op = _ind_rout(ref_root / "xc", [f"Vdd vdd 0 DC {CS['vdd']} AC 0", *_xc_body()], "na", "nb", pr)
    assert op["v(na)"] == pytest.approx(op["v(nb)"], abs=1e-9), "독립 해가 대칭(준안정)이 아니다 -- 조건 점검"
    gm, gds = _fsum(op, "nmos", "xmx1", x["n"], "gm"), _fsum(op, "nmos", "xmx1", x["n"], "gds")
    hand = 2.0 / (1.0 / x["rx"] + gds - gm)
    assert hand < 0, "교차 결합 조건(gm > 1/RX + gds) 미충족"
    return {"H": h, "hand": hand, "v": op["v(na)"], "gm": gm, "gds": gds}


@pytest.fixture(scope="module")
def hand(ind):
    r_n = 1.0 / (1.0 / CS["rload"] + ind["M1"]["gds"])
    r_p = 1.0 / (1.0 / CS["rp"] + ind["MP1"]["gds"])
    return {"nout": r_n, "pout": r_p, "diff": r_n + r_p}


def _inp(lut, ind, metrics=None, constraints=None, xc=None):
    pr = preds_from_independent(ind)
    inp = cs_input(lut, diffusion="zero", preds_nodes=pr["nodes"], preds_devices=pr["devices"],
                   metrics=metrics, constraints=constraints)
    if xc is not None:      # 교차 결합 쌍 가지 추가(이상 레일 vdd/gnd 로 다른 가지와 갈라짐)
        x = XC
        for nm, d, g in (("MX1", "na", "nb"), ("MX2", "nb", "na")):
            inp["devices"].append({"name": nm, "kind": "nmos", "drain": d, "gate": g, "source": "gnd", "bulk": "gnd",
                                   "L": x["L"], "finger_w": x["finger_w"], "n_fingers": x["n"],
                                   "W": x["finger_w"] * x["n"]})
            inp["predictions"]["devices"][nm] = {"off_current_A": 0.0}
        inp["passives"] += [{"name": "RXa", "kind": "resistor", "terminals": ["vdd", "na"], "value": x["rx"]},
                            {"name": "RXb", "kind": "resistor", "terminals": ["vdd", "nb"], "value": x["rx"]}]
        inp["predictions"]["nodes"].update({"na": xc["v"], "nb": xc["v"]})
        zero_diffusion(inp)
    return inp


def _perf(c, name):
    return by_name(c["performance"], "name", name)


def _cons(c, name):
    return by_name(c["constraints"], "name", name)


def _sim(d: Path, inp, bias="free"):
    return json.loads((d / f"{stem_of(inp, bias)}.sim.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ 값(손계산·독립 넷리스트)
VIEWS = {
    "cs_nout": se("nout"),
    "pmos_pout": se("pout", None),        # sense_n: null 명시
    "diff_np": df("nout", "pout"),
    "xc_diff": df("na", "nb"),
}


@pytest.fixture(scope="module")
def run_views(tmp_path_factory, ind, xc_ref):
    """모든 뷰를 metric 으로, 같은 뷰 중복(metric 1 + 제약 1)을 넣어 free+forced 한 번."""
    d = tmp_path_factory.mktemp("rout")
    metrics = [{"name": k, "measure": "rout_ohm", "value": 1.0, "view": v} for k, v in VIEWS.items()]
    metrics.append({"name": "cs_dup_null", "measure": "rout_ohm", "value": 1.0, "view": se("nout", None)})
    cons = [{"name": "pmos_c", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("pout")}]
    inp = _inp(make_lut(d / "lut.npz"), ind, metrics, cons, xc=xc_ref)
    p, res = run_oracle(inp, d / "o", biases=("free", "forced"), sat_margin=SAT)
    assert res["free"] is not None and res["forced"] is not None, (p.stdout + p.stderr)[-2000:]
    return d, inp, res


def test_cs_rout_matches_hand_calc(run_views, hand):
    _, _, res = run_views
    assert _perf(res["free"], "cs_nout")["spice"] == pytest.approx(hand["nout"], rel=1e-4)
    assert _perf(res["free"], "pmos_pout")["spice"] == pytest.approx(hand["pout"], rel=1e-4)


def test_differential_rout_is_sum_of_halves(run_views, hand):
    _, _, res = run_views
    assert _perf(res["free"], "diff_np")["spice"] == pytest.approx(hand["diff"], rel=1e-4)


@pytest.mark.parametrize("name", ["cs_nout", "pmos_pout", "diff_np"])
def test_rout_matches_independent_netlist(run_views, ref_root, name):
    _, _, res = run_views
    v = VIEWS[name]
    h, _ = _ind_rout(ref_root / f"rv_{name}", _cs_body(), v["sense_p"], v.get("sense_n"))
    for b in ("free", "forced"):    # forced 도 잰다(진단 기록); 예측 = 독립 해라 forced DC 도 같다. Vhold 는 choke 경유
        assert _perf(res[b], name)["spice"] == pytest.approx(h.real, rel=1e-5), (b, name)


def test_sim_rout_record_shape_and_dedup(run_views):
    d, inp, res = run_views
    sim = _sim(d / "o", inp)
    views = [r["view"] for r in sim["rout"]]
    # 중복 제거 + 순서: 제약 먼저(pout), 그다음 metric 처음 나온 순서(nout, (pout 중복), diff, xc, (nout null 중복))
    assert views == [canon(se("pout")), canon(se("nout")), canon(VIEWS["diff_np"]), canon(VIEWS["xc_diff"])], views
    for r in sim["rout"]:
        assert r["f_hz"] == pytest.approx(F0)
        assert r["mag"] == pytest.approx(abs(complex(r["re"], r["im"])), rel=1e-9)
        if r["re"] >= 0:
            assert r["rout_ohm"] == r["re"] and r["undefined"] is None, r
    stem = d / "o" / stem_of(inp, "free")
    for k in range(4):
        assert Path(f"{stem}.rout{k}.txt").exists(), k
    assert not Path(f"{stem}.rout4.txt").exists()
    c = res["free"]
    assert c["summary"]["spice_rout"] == sim["rout"]
    assert _perf(c, "cs_dup_null")["spice"] == _perf(c, "cs_nout")["spice"]
    assert _cons(c, "pmos_c")["spice"] == _perf(c, "pmos_pout")["spice"]
    meta = json.loads(Path(f"{stem}.cir.meta.json").read_text(encoding="utf-8"))
    assert [r["view"] for r in meta["rout_runs"]] == views
    assert all(r["f_hz"] == pytest.approx(F0) for r in meta["rout_runs"])


def test_netlist_rout_sources_and_alters(run_views):
    """Irout_<k> 는 본문에 DC 0 AC 0, 자기 .ac 직전에만 acmag 1; 모든 테스트벤치 이상 전압원 acmag 0."""
    d, inp, _ = run_views
    text = (d / "o" / f"{stem_of(inp, 'free')}.cir").read_text(encoding="utf-8")
    i0 = elem(text, "Irout_0")
    assert i0 is not None and i0[1:3] == ["0", "pout"], i0
    assert elem(text, "Irout_0n") is None                       # single_ended 는 n 쪽 없음
    i2, i2n = elem(text, "Irout_2"), elem(text, "Irout_2n")
    assert i2[1:3] == ["0", "nout"] and i2n[1:3] == ["pout", "0"], (i2, i2n)
    for t in (i0, i2, i2n):
        up = [x.upper() for x in t]
        assert float(t[up.index("DC") + 1]) == 0.0 and float(t[up.index("AC") + 1]) == 0.0, t
    low = text.lower()
    assert "alter @irout_0[acmag] = 1" in low and "alter @irout_2n[acmag] = 1" in low
    for src in ("vac_nin", "vrail_vdd", "vrail_vsp", "vbias_pb"):
        assert f"alter @{src}[acmag] = 0" in low, src
    # 한 rout .ac 앞에서 켜진 전류원은 그 뷰 것뿐(다른 뷰 것은 0): 각 'ac lin' 직전 alter 묶음 확인
    blocks = re.split(r"\n\s*ac lin 1 [^\n]*\n", low)
    on_sets = []
    for b in blocks[:-1]:
        on = set(re.findall(r"alter @(irout_\d+n?)\[acmag\] = 1\b", b.split("wrdata")[-1]))
        if on:
            on_sets.append(on)
    assert on_sets == [{"irout_0"}, {"irout_1"}, {"irout_2", "irout_2n"}, {"irout_3", "irout_3n"}], on_sets


# ------------------------------------------------------------------ 소스 팔로워(gmbs 포함)
SF = dict(vdd=1.8, vin=1.2, rs=1e4, L=0.5e-6, finger_w=2e-6, n=2)


def _sf_body():
    s = SF
    body = [f"Vdd vdd 0 DC {s['vdd']} AC 0", f"Vin nin 0 DC {s['vin']} AC 0", f"RS nout 0 {s['rs']}"]
    for i in range(s["n"]):
        body.append(f"XM1_{i} vdd nin nout 0 {NFET} l={s['L']} w={s['finger_w']}")
    return body


@pytest.fixture(scope="module")
def sf_ref(ref_root):
    s = SF
    pr = ["v(nout)"] + [probe("nmos", f"xm1_{i}", q) for i in range(s["n"]) for q in ("gm", "gds", "gmbs", "id")]
    h, op = _ind_rout(ref_root / "sf", _sf_body(), "nout", None, pr)
    g = {q: _fsum(op, "nmos", "xm1", s["n"], q) for q in ("gm", "gds", "gmbs")}
    assert g["gmbs"] > 0.05 * g["gm"], "바디 효과가 의미 있는 조건 점검"
    return {"H": h, "vout": op["v(nout)"], "hand": 1.0 / (g["gm"] + g["gmbs"] + g["gds"] + 1.0 / s["rs"]),
            "no_body": 1.0 / (g["gm"] + g["gds"] + 1.0 / s["rs"])}


def sf_input(lut, sf_ref, metrics=None, constraints=None):
    s = SF
    inp = {
        "schema": "spice_oracle_input/1", "circuit": "tsf_rout",
        "process": {**cs_input(lut)["process"]},
        "rails": [{"net": "vdd", "voltage": s["vdd"]}, {"net": "gnd", "voltage": 0.0, "reference": True}],
        "devices": [{"name": "M1", "kind": "nmos", "drain": "vdd", "gate": "nin", "source": "nout", "bulk": "gnd",
                     "L": s["L"], "finger_w": s["finger_w"], "n_fingers": s["n"], "W": s["finger_w"] * s["n"]}],
        "passives": [{"name": "RS", "kind": "resistor", "terminals": ["nout", "gnd"], "value": s["rs"]}],
        "ports": {"input": "nin", "output": "nout"},
        "predictions": {"nodes": {"nin": s["vin"], "nout": sf_ref["vout"]},
                        "devices": {"M1": {"off_current_A": 0.0}}, "metrics": metrics or []},
        "testbench": conftest.testbench_block(),
    }
    if constraints:
        inp["acceptance"] = {"constraints": constraints}
    return zero_diffusion(inp)


def test_source_follower_rout(tmp_path, sf_ref):
    m = [{"name": "ro", "measure": "rout_ohm", "value": sf_ref["hand"], "view": se("nout")}]
    p, res = run_oracle(sf_input(make_lut(tmp_path / "lut.npz"), sf_ref, metrics=m), tmp_path / "o",
                        biases=("free", "forced"), sat_margin=SAT)
    for b in ("free", "forced"):
        c = res[b]
        assert c is not None, (p.stdout + p.stderr)[-1500:]
        got = _perf(c, "ro")["spice"]
        assert got == pytest.approx(sf_ref["hand"], rel=1e-4), b
        assert got == pytest.approx(sf_ref["H"].real, rel=1e-5), b
        assert abs(got / sf_ref["no_body"] - 1) > 1e-2      # gmbs 를 뺀 값과는 구분된다


# ------------------------------------------------------------------ 음의 실수부 = 정의 불가
def test_cross_coupled_negative_real_part(run_views, xc_ref):
    d, inp, res = run_views
    assert xc_ref["H"].real == pytest.approx(xc_ref["hand"], rel=1e-4)       # 독립 넷리스트 = 손계산(음수)
    sim = _sim(d / "o", inp)
    r = [x for x in sim["rout"] if x["view"] == canon(VIEWS["xc_diff"])][0]
    assert r["re"] == pytest.approx(xc_ref["H"].real, rel=1e-5) and r["re"] < 0
    assert r["rout_ohm"] is None and r["undefined"] == "negative_real_part", r
    pr = _perf(res["free"], "xc_diff")
    assert pr["spice"] is None and pr["judge"] == "N/A(정의 불가: negative_real_part)", pr


@pytest.fixture(scope="module")
def xc_lut(tmp_path_factory):
    return make_lut(tmp_path_factory.mktemp("xc_lut") / "lut.npz")


@pytest.mark.parametrize("op,limit", [(">=", -1e9), ("<=", 1e9), (">=", 0.0), ("<=", 0.0)])
def test_negative_rout_constraint_never_pass(tmp_path, ind, xc_ref, xc_lut, op, limit):
    """어떤 limit 이든(음수 값이 수치로는 '만족'할 limit 포함) 제약 N/A -> free verdict INCOMPLETE, 반환 0."""
    cons = [{"name": "rx", "measure": "rout_ohm", "op": op, "limit": limit, "view": df("na", "nb")}]
    p, res = run_oracle(_inp(xc_lut, ind, constraints=cons, xc=xc_ref), tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c is not None, (p.stdout + p.stderr)[-1500:]
    k = _cons(c, "rx")
    assert k["judge"] == "N/A(정의 불가: negative_real_part)" and k["spice"] is None, k
    assert k["undefined"] == "negative_real_part", k
    a = c["summary"]["acceptance"]
    assert a["constraints_unmeasured"] == ["rx"] and a["constraints_failed"] == [], a
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0, c["summary"]


def test_negative_rout_control_pass_without_it(tmp_path, ind, xc_ref, xc_lut):
    """대조: 같은 회로에서 정의 가능한 뷰 제약만 있으면 PASS -- INCOMPLETE 는 음의 실수부 때문."""
    cons = [{"name": "ok", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")}]
    p, res = run_oracle(_inp(xc_lut, ind, constraints=cons, xc=xc_ref), tmp_path / "o", sat_margin=SAT)
    assert res["free"]["summary"]["verdict"] == "PASS" and p.returncode == 0, res["free"]["summary"]


def test_negative_rout_with_other_fail_is_fail(tmp_path, ind, xc_ref, xc_lut, hand):
    cons = [{"name": "rx", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": df("na", "nb")},
            {"name": "bad", "measure": "rout_ohm", "op": ">=", "limit": hand["nout"] * 2, "view": se("nout")}]
    p, res = run_oracle(_inp(xc_lut, ind, constraints=cons, xc=xc_ref), tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c["summary"]["verdict"] == "FAIL" and p.returncode == 1, c["summary"]
    assert c["summary"]["acceptance"]["constraints_failed"] == ["bad"]


def test_negative_rout_forced_incomplete(run_views):
    _, _, res = run_views
    assert res["forced"]["summary"]["verdict"] == "INCOMPLETE"
    assert _perf(res["forced"], "xc_diff")["judge"] == "N/A(정의 불가: negative_real_part)"


# ------------------------------------------------------------------ 판정(C9) / 기록
@pytest.mark.parametrize("op,f,exp,rc", [(">=", 0.99, "PASS", 0), (">=", 1.01, "FAIL", 1),
                                         ("<=", 1.01, "PASS", 0), ("<=", 0.99, "FAIL", 1)])
def test_constraint_judged(tmp_path, ind, hand, op, f, exp, rc):
    cons = [{"name": "ro", "measure": "rout_ohm", "op": op, "limit": hand["nout"] * f, "view": se("nout")}]
    p, res = run_oracle(_inp(make_lut(tmp_path / "lut.npz"), ind, constraints=cons), tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert _cons(c, "ro")["judge"] == exp
    assert c["summary"]["verdict"] == exp and p.returncode == rc, c["summary"]
    assert c["summary"]["acceptance"]["constraints_failed"] == (["ro"] if exp == "FAIL" else [])


@pytest.mark.parametrize("tol,exp", [(0.01, "FAIL"), (0.1, "PASS")])
def test_metric_record_only(tmp_path, ind, hand, tol, exp):
    """metric 은 기록(tolerances.rout_ohm_rel, 오차 = (SPICE - 예측)/|예측|): 예측을 5 % 낮게 -> 기록 판정만, verdict PASS."""
    pred = hand["nout"] / 1.05
    m = [{"name": "ro", "measure": "rout_ohm", "value": pred, "view": se("nout")}]
    p, res = run_oracle(_inp(make_lut(tmp_path / "lut.npz"), ind, metrics=m), tmp_path / "o",
                        judge={"sat_margin_V": SAT, "tolerances": {"rout_ohm_rel": tol}})
    c = res["free"]
    r = _perf(c, "ro")
    assert r["err"] == pytest.approx(0.05, abs=2e-4) and r["judge"] == exp, r
    assert c["summary"]["verdict"] == "PASS", c["summary"]


# ------------------------------------------------------------------ 막힘
BLOCK = {
    "input_net": se("nin"),
    "rail": se("vdd"),
    "rail_vsp": se("vsp"),
    "gate_bias": se("pb"),
    "reference": se("gnd"),
    "nonexistent": se("nosuch"),
    "diff_n_input": df("nout", "nin"),
    "diff_n_rail": df("nout", "vdd"),
    "diff_n_reference": df("nout", "gnd"),
    "diff_n_nonexistent": df("nout", "nosuch"),
    "diff_p_gate_bias": df("pb", "nout"),
    "diff_same": df("nout", "nout"),
}


@pytest.mark.parametrize("kind", list(BLOCK))
@pytest.mark.parametrize("where", ["constraint", "metric"])
def test_blocked_views(tmp_path, ind, kind, where):
    item = {"name": "x", "measure": "rout_ohm", "view": BLOCK[kind]}
    lut = make_lut(tmp_path / "lut.npz")
    if where == "constraint":
        inp = _inp(lut, ind, constraints=[dict(item, op=">=", limit=0.0)])
    else:
        inp = _inp(lut, ind, metrics=[dict(item, value=1.0)])
    p, text, meta = run_netlist(inp, tmp_path / "n")
    assert meta is not None and meta["blockers"], (kind, (p.stdout + p.stderr)[-800:])
    assert any(b.startswith("C26 rout_ohm") for b in meta["blockers"]), meta["blockers"]
    if text is not None:
        assert "irout_" not in text.lower()
    q, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    c = res["free"]
    assert c["summary"]["verdict"] == "BLOCKED" and q.returncode == 2, c["summary"]
    assert _sim(tmp_path / "o", inp)["rout"] == []


def test_one_blocked_view_removes_all_rout_runs(tmp_path, ind):
    """막힘이 하나라도 있으면 rout 실행을 하나도 넣지 않는다(유효 뷰 포함)."""
    cons = [{"name": "ok", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")},
            {"name": "bad", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nin")}]
    p, text, meta = run_netlist(_inp(make_lut(tmp_path / "lut.npz"), ind, constraints=cons), tmp_path / "n")
    assert meta["blockers"] and any(b.startswith("C26 rout_ohm") for b in meta["blockers"])
    assert not meta.get("rout_runs"), meta.get("rout_runs")
    assert text is None or "irout_" not in text.lower()


def test_valid_views_not_blocked_control(tmp_path, ind):
    """음성 대조: 내부 넷(single/differential, 게이트 바이어스 가지의 드레인 포함)은 막히지 않는다."""
    cons = [{"name": "a", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")},
            {"name": "b", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": df("pout", "nout")}]
    p, text, meta = run_netlist(_inp(make_lut(tmp_path / "lut.npz"), ind, constraints=cons), tmp_path / "n")
    assert p.returncode == 0 and meta["blockers"] == [], meta["blockers"]
    assert len(meta["rout_runs"]) == 2


@pytest.mark.parametrize("bias", ["forced"])
def test_forced_held_net_is_measurable(tmp_path, ind, bias):
    """forced 고정 넷(Vhold + choke)은 막힘 목록(레일·입력·게이트 바이어스)에 없다 -> 막히지 않는다."""
    cons = [{"name": "a", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")}]
    p, text, meta = run_netlist(_inp(make_lut(tmp_path / "lut.npz"), ind, constraints=cons), tmp_path / "n", bias)
    assert meta["blockers"] == [] and elem(text, "Vhold_nout") is not None and elem(text, "Irout_0") is not None


def test_no_fstart_is_schema_or_block(tmp_path, ind):
    """fstart_hz 는 스키마 필수(ac.required) -> 없으면 C13 거부(산출물 없음, 반환 2)."""
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind,
               constraints=[{"name": "a", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")}])
    del inp["testbench"]["ac"]["fstart_hz"]
    out = tmp_path / "o"
    p, res = run_oracle(inp, out, sat_margin=SAT)
    assert p.returncode == 2 and res["free"] is None
    assert sorted(x.name for x in out.iterdir()) == ["t.input.json"]


# ------------------------------------------------------------------ 스키마(C13)
SCHEMA_BAD = {
    "ac_excite_in_sense_view": {"sense_p": "nout", "sense_n": None, "sense_mode": "single_ended",
                                "ac_excite": {"nin": 1.0}},
    "differential_without_sense_n": {"sense_p": "nout", "sense_mode": "differential"},
    "differential_null_sense_n": {"sense_p": "nout", "sense_n": None, "sense_mode": "differential"},
    "differential_empty_sense_n": {"sense_p": "nout", "sense_n": "", "sense_mode": "differential"},
    "single_ended_with_sense_n": {"sense_p": "nout", "sense_n": "pout", "sense_mode": "single_ended"},
    "empty_sense_p": {"sense_p": "", "sense_mode": "single_ended"},
    "bad_mode": {"sense_p": "nout", "sense_mode": "diff"},
    "ratio_view_shape": {"num": {"ac_excite": {"nin": 1.0}, "sense_p": "nout", "sense_n": None,
                                 "sense_mode": "single_ended"},
                         "den": {"ac_excite": {"vdd": 1.0}, "sense_p": "nout", "sense_n": None,
                                 "sense_mode": "single_ended"}},
    "no_view": None,
}


@pytest.mark.parametrize("case", list(SCHEMA_BAD))
@pytest.mark.parametrize("where", ["constraint", "metric"])
def test_schema_rejects(tmp_path, ind, case, where):
    item = {"name": "x", "measure": "rout_ohm"}
    if SCHEMA_BAD[case] is not None:
        item["view"] = SCHEMA_BAD[case]
    lut = make_lut(tmp_path / "lut.npz")
    if where == "constraint":
        inp = _inp(lut, ind, constraints=[dict(item, op=">=", limit=0.0)])
    else:
        inp = _inp(lut, ind, metrics=[dict(item, value=1.0)])
    out = tmp_path / "o"
    p, res = run_oracle(inp, out, sat_margin=SAT)
    assert p.returncode == 2 and res["free"] is None, (case, (p.stdout + p.stderr)[-600:])
    assert sorted(x.name for x in out.iterdir()) == ["t.input.json"], list(out.iterdir())
    q, text, meta = run_netlist(inp, tmp_path / "n")
    assert q.returncode == 2 and text is None and meta is None


@pytest.mark.parametrize("view", [se("nout"), se("nout", None), df("nout", "pout")])
def test_schema_accepts_valid_sense_views(tmp_path, ind, view):
    """음성 대조: single_ended 의 sense_n 없음/null, differential 의 문자열 sense_n 은 받는다."""
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind,
               constraints=[{"name": "x", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": view}])
    p, text, meta = run_netlist(inp, tmp_path / "n")
    assert p.returncode == 0 and meta is not None and meta["blockers"] == [], (p.stdout + p.stderr)[-600:]


# ------------------------------------------------------------------ iso·루프 넷리스트, C15 Irout_, 캐시(C21)
def test_no_rout_in_iso_or_loop_netlists(tmp_path, ind):
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind,
               constraints=[{"name": "x", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")}])
    inp["process"]["models"]["nmos"]["polarity"] = "n"
    inp["process"]["models"]["pmos"]["polarity"] = "p"
    p, text, meta = run_netlist(inp, tmp_path / "iso", "iso")
    assert p.returncode == 0 and "irout" not in text.lower() and "rout0" not in text.lower()
    fb = fb_input(make_lut(tmp_path / "lut_fb.npz"))
    fb["acceptance"] = {"constraints": [{"name": "x", "measure": "rout_ohm", "op": ">=", "limit": 0.0,
                                         "view": se("nout")}]}
    p, text, meta = run_netlist(fb, tmp_path / "fb")
    assert p.returncode == 0 and meta["blockers"] == [], meta and meta["blockers"]
    assert elem(text, "Irout_0") is not None                          # 본 넷리스트에는 있다
    loop = (tmp_path / "fb" / "t.free.loop.cir").read_text(encoding="utf-8")
    assert "irout" not in loop.lower() and "rout0" not in loop.lower()


TOPO_REL = "skills/analog-gmid-design/tools/spice_oracle/tests/fixtures/tcs_nmos_rload.topology.json"


@pytest.mark.parametrize("bias", ["free", "forced"])
def test_c15_irout_is_testbench_element(tmp_path, bias):
    """C15: Irout_ 는 테스트벤치 원소 -- 비교에서 빠지고 excluded_testbench 에 적히며 연결 동일성은 verified."""
    inp = cs_input(make_lut(tmp_path / "lut.npz"), preds_nodes={"nout": 0.9, "pout": 0.16},
                   preds_devices=copy.deepcopy(OFF_ZERO),
                   constraints=[{"name": "a", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")},
                                {"name": "b", "measure": "rout_ohm", "op": ">=", "limit": 0.0,
                                 "view": df("nout", "pout")}])
    inp["sources"] = [{"name": "I1", "kind": "current", "terminals": ["vdd", "nout"], "value": 1e-7}]
    inp["topology"] = {"path": TOPO_REL}
    p, text, meta = run_netlist(inp, tmp_path / "n", bias, extra=["--require-topology"])
    assert p.returncode == 0, (p.stdout + p.stderr)[-1500:]
    t = meta["topology_identity"]
    assert t["status"] == "verified" and t["diffs"] == [] and meta["blockers"] == [], (t, meta["blockers"])
    assert {"Irout_0", "Irout_1", "Irout_1n"} <= set(t["excluded_testbench"]), t["excluded_testbench"]


def test_cache_restores_rout(tmp_path, ind, hand):
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind,
               constraints=[{"name": "x", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")}])
    cache = tmp_path / "cache"
    p1, r1 = run_oracle(inp, tmp_path / "o1", sat_margin=SAT, extra=["--cache-dir", cache])
    p2, r2 = run_oracle(inp, tmp_path / "o2", sat_margin=SAT, extra=["--cache-dir", cache])
    s1, s2 = _sim(tmp_path / "o1", inp), _sim(tmp_path / "o2", inp)
    assert s1["cache"]["main"] == "miss" and s2["cache"]["main"] == "hit", (s1["cache"], s2["cache"])
    v2 = r2["free"]["summary"]["spice_rout"][0]["rout_ohm"]
    assert v2 is not None and v2 == r1["free"]["summary"]["spice_rout"][0]["rout_ohm"]
    assert v2 == pytest.approx(hand["nout"], rel=1e-4)
    assert (tmp_path / "o2" / f"{stem_of(inp, 'free')}.rout0.txt").exists()
    assert r2["free"]["summary"]["verdict"] == "PASS"


def test_cache_key_distinguishes_rout_view(tmp_path, ind, hand):
    """뷰가 다르면 넷리스트가 달라 캐시 키가 다르다(다른 뷰 결과를 복원하지 않는다)."""
    cache = tmp_path / "cache"
    lut = make_lut(tmp_path / "lut.npz")
    a = _inp(lut, ind, constraints=[{"name": "x", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("nout")}])
    b = _inp(lut, ind, constraints=[{"name": "x", "measure": "rout_ohm", "op": ">=", "limit": 0.0, "view": se("pout")}])
    run_oracle(a, tmp_path / "oa", sat_margin=SAT, extra=["--cache-dir", cache])
    p, rb = run_oracle(b, tmp_path / "ob", sat_margin=SAT, extra=["--cache-dir", cache])
    assert _sim(tmp_path / "ob", b)["cache"]["main"] == "miss"
    assert rb["free"]["summary"]["spice_rout"][0]["rout_ohm"] == pytest.approx(hand["pout"], rel=1e-4)
