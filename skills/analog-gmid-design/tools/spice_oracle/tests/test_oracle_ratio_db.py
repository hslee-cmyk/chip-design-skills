"""C24 CMRR·PSRR = ratio_db + C9(제약 판정) + C13(스키마: ratio_db 는 view 필수) + C21(캐시에 ratio 파일).

근거: README C24·C9·C8·C21, schema ratio_view/transfer_view 만.
- 뷰 {num, den} 마다 .ac 한 번(fstart 한 점). ac_excite 넷은 그 진폭(위상 0, 음수 = 반대 위상), 테스트벤치가 이상 전압원으로
  구동하는 나머지 넷(레일·입력·게이트 바이어스)은 AC 0. H = V(sense_p)-V(sense_n) 또는 V(sense_p).
  ratio_db = 20 log10(|H_num|/|H_den|).
- 여기 가능 넷: 입력(Vac_), 레일(Vrail_), 게이트 전용 바이어스(Vbias_). 그 밖(내부 넷, forced 고정 넷) 또는 reference 레일
  -> 막힘. sense 넷이 회로 넷(reference 제외)이 아니면 막힘.

기대값: (a) 손계산 -- CS 단(M1 바디=소스=gnd, 게이트는 AC 로 고정)에서 nout 의 두 전달은 분모가 같다:
    H_in = -gm/(1/RL + gds),  H_vdd = (1/RL)/(1/RL + gds)  ->  ratio = 20 log10(gm*RL)   (fstart = 0.01 Hz, 용량 무시)
  gm 은 독립 넷리스트(conftest.independent_cs)의 M1 finger 합.
  (b) 손으로 쓴 독립 2회 .ac 넷리스트(이상 전압원에 AC 진폭을 직접, ac lin 1 f f).
"""
import copy
import json
import math
import subprocess
from pathlib import Path

import numpy as np
import pytest

from conftest import (CS, NFET, NGSPICE, PFET, _includes, by_name, cs_input, elem, fb_input, independent_cs, make_lut,
                      preds_from_independent, run_netlist, run_oracle, stem_of)

F0 = 0.01   # testbench_block fstart_hz


def se(ex, sp="nout"):
    return {"ac_excite": ex, "sense_p": sp, "sense_n": None, "sense_mode": "single_ended"}


def df(ex, sp="nout", sn="pout"):
    return {"ac_excite": ex, "sense_p": sp, "sense_n": sn, "sense_mode": "differential"}


PSRR = {"num": se({"nin": 1.0}), "den": se({"vdd": 1.0})}


# ------------------------------------------------------------------ 독립 2회 .ac
def _ind_h(workdir: Path, amps: dict, sp: str, sn=None) -> complex:
    """CS 회로를 손으로(finger 마다 인스턴스, m 없음) 쓰고 이상 전압원에 AC 진폭을 직접 건 .ac 한 점."""
    c = CS
    a = {k: amps.get(k, 0.0) for k in ("vdd", "vsp", "nin", "pb")}
    body = [f"Vdd vdd 0 DC {c['vdd']} AC {a['vdd']}", f"Vsp vsp 0 DC {c['vsp']} AC {a['vsp']}",
            f"Vin nin 0 DC {c['vin']} AC {a['nin']}", f"Vpb pb 0 DC {c['pb']} AC {a['pb']}",
            f"RL vdd nout {c['rload']}", f"CL nout 0 {c['cl']}", f"RP pout 0 {c['rp']}"]
    for i in range(c["n"]):
        body.append(f"XM1_{i} nout nin 0 0 {NFET} l={c['L']} w={c['finger_w']}")
    for i in range(c["pn"]):
        body.append(f"XMP1_{i} pout pb vsp vdd {PFET} l={c['pL']} w={c['pfinger_w']}")
    expr = f"v({sp})" if sn is None else f"v({sp})-v({sn})"
    workdir.mkdir(parents=True, exist_ok=True)
    lines = ["* independent ratio run", _includes("tt"), ".temp 27.0",
             ".option gmin=1e-15 reltol=1e-4 abstol=1e-14 vntol=1e-7", *body, ".control", "set noaskquit",
             f"ac lin 1 {F0} {F0}", f"let h = {expr}", "let hr = real(h)", "let hi = imag(h)",
             "set wr_singlescale", "wrdata h.txt hr hi", "quit", ".endc", ".end"]
    (workdir / "r.cir").write_text("\n".join(lines) + "\n", encoding="utf-8")
    p = subprocess.run([str(NGSPICE), "-b", "r.cir"], capture_output=True, text=True, cwd=str(workdir),
                       encoding="utf-8", errors="replace", timeout=120)
    arr = np.atleast_2d(np.loadtxt(workdir / "h.txt"))
    assert arr.shape[0] == 1, p.stdout[-1500:]
    return complex(arr[0, 1], arr[0, 2])


def _ind_ratio(root: Path, view: dict, tag: str) -> float:
    def h(v, k):
        return _ind_h(root / f"{tag}_{k}", v["ac_excite"], v["sense_p"], v["sense_n"])
    return 20 * math.log10(abs(h(view["num"], "num")) / abs(h(view["den"], "den")))


@pytest.fixture(scope="module")
def ind(ref_root):
    return independent_cs(ref_root)


@pytest.fixture(scope="module")
def hand_psrr(ind):
    return 20 * math.log10(ind["M1"]["gm"] * CS["rload"])


def _inp(lut, ind, metrics=None, constraints=None):
    pr = preds_from_independent(ind)
    return cs_input(lut, diffusion="zero", preds_nodes=pr["nodes"], preds_devices=pr["devices"],
                    metrics=metrics, constraints=constraints)


VIEWS = {
    "psrr_vdd_se": PSRR,
    "neg_amp_multi": {"num": se({"nin": -2.0, "vsp": 1.0}), "den": se({"vdd": 1.0})},
    "sum_two_nets": {"num": se({"nin": 1.0, "vdd": 1.0}), "den": se({"vdd": 1.0})},
    "diff_sense": {"num": df({"nin": 1.0}), "den": df({"vdd": 1.0})},
    "gate_bias_vsp": {"num": se({"pb": 1.0}, "pout"), "den": se({"vsp": 0.5}, "pout")},
}


@pytest.fixture(scope="module")
def run_views(tmp_path_factory, ind):
    """모든 뷰를 metric 으로 한 입력 하나를 free+forced 로 한 번 돌린다(같은 뷰 metric 2개 + 제약 1개 = 중복 제거 확인)."""
    d = tmp_path_factory.mktemp("ratio")
    metrics = [{"name": k, "measure": "ratio_db", "value": 0.0, "view": v} for k, v in VIEWS.items()]
    metrics.append({"name": "psrr_dup", "measure": "ratio_db", "value": 0.0, "view": copy.deepcopy(PSRR)})
    cons = [{"name": "psrr_c", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": copy.deepcopy(PSRR)}]
    inp = _inp(make_lut(d / "lut.npz"), ind, metrics, cons)
    p, res = run_oracle(inp, d / "o", biases=("free", "forced"), sat_margin=0.05)
    assert res["free"] is not None and res["forced"] is not None, (p.stdout + p.stderr)[-2000:]
    return d, inp, res


def _perf(c, name):
    return by_name(c["performance"], "name", name)


# ------------------------------------------------------------------ 값
def test_psrr_matches_hand_calc(run_views, hand_psrr):
    _, _, res = run_views
    assert _perf(res["free"], "psrr_vdd_se")["spice"] == pytest.approx(hand_psrr, abs=2e-3)


@pytest.mark.parametrize("name", list(VIEWS))
def test_ratio_matches_independent_two_run_netlist(run_views, ref_root, name):
    _, _, res = run_views
    exp = _ind_ratio(ref_root, VIEWS[name], name)
    for b in ("free", "forced"):     # forced 도 잰다(진단 기록); 이 입력은 예측 노드 = 독립 해라 forced DC 도 같다
        assert _perf(res[b], name)["spice"] == pytest.approx(exp, abs=1e-3), (b, name)


def test_negative_amplitude_and_superposition_hand(run_views):
    """음수 진폭 = 반대 위상, 여러 넷 동시 여기 = 중첩. vsp 는 nout 에 닿지 않으므로
    neg_amp_multi = psrr + 20log10(2);  sum_two_nets = 20log10(|H_in + H_vdd|/|H_vdd|) (H_in 은 음수 실수)."""
    _, _, res = run_views
    c = res["free"]
    ratio = c["summary"]["spice_ratio"]
    base = [r for r in ratio if r["view"] == PSRR][0]
    h_in, h_vdd = base["num"]["re"], base["den"]["re"]
    assert h_in < 0 < h_vdd
    assert _perf(c, "neg_amp_multi")["spice"] == pytest.approx(base["ratio_db"] + 20 * math.log10(2), abs=1e-4)
    assert _perf(c, "sum_two_nets")["spice"] == pytest.approx(20 * math.log10(abs(h_in + h_vdd) / h_vdd), abs=1e-4)


def test_sim_ratio_record_shape_and_dedup(run_views):
    d, inp, res = run_views
    sim = json.loads((d / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))
    views = [r["view"] for r in sim["ratio"]]
    assert len(views) == len(VIEWS), views                         # psrr_dup·psrr_c 는 같은 뷰라 한 번만
    assert sum(v == PSRR for v in views) == 1
    for r in sim["ratio"]:
        assert r["f_hz"] == pytest.approx(F0)
        for k in ("num", "den"):
            assert r[k]["mag"] == pytest.approx(abs(complex(r[k]["re"], r[k]["im"])), rel=1e-6)
        assert r["ratio_db"] == pytest.approx(20 * math.log10(r["num"]["mag"] / r["den"]["mag"]), abs=1e-9)
    stem = d / "o" / stem_of(inp, "free")
    for k in range(len(VIEWS)):
        assert Path(f"{stem}.ratio{k}.num.txt").exists() and Path(f"{stem}.ratio{k}.den.txt").exists()
    assert not Path(f"{stem}.ratio{len(VIEWS)}.num.txt").exists()
    c = res["free"]
    assert _perf(c, "psrr_dup")["spice"] == _perf(c, "psrr_vdd_se")["spice"]
    assert by_name(c["constraints"], "name", "psrr_c")["spice"] == _perf(c, "psrr_vdd_se")["spice"]


# ------------------------------------------------------------------ 판정(C9) / 기록
@pytest.mark.parametrize("op,delta,exp,rc", [(">=", -1.0, "PASS", 0), (">=", +1.0, "FAIL", 1),
                                             ("<=", +1.0, "PASS", 0), ("<=", -1.0, "FAIL", 1)])
def test_constraint_judged(tmp_path, ind, hand_psrr, op, delta, exp, rc):
    cons = [{"name": "psrr", "measure": "ratio_db", "op": op, "limit": hand_psrr + delta, "view": PSRR}]
    p, res = run_oracle(_inp(make_lut(tmp_path / "lut.npz"), ind, constraints=cons), tmp_path / "o", sat_margin=0.05)
    c = res["free"]
    assert by_name(c["constraints"], "name", "psrr")["judge"] == exp
    assert c["summary"]["verdict"] == exp and p.returncode == rc, c["summary"]
    assert c["summary"]["acceptance"]["constraints_failed"] == (["psrr"] if exp == "FAIL" else [])


def test_constraint_unmeasurable_den_zero_incomplete(tmp_path, ind):
    """den = pb 여기, nout 감지: pb 는 PMOS 가지에만 물리고 두 가지는 이상 레일로 갈라져 |H_den| = 0
    (독립 넷리스트로 확인) -> ratio_db None -> 제약 N/A(SPICE 값 없음) -> INCOMPLETE(PASS 아님)."""
    view = {"num": se({"nin": 1.0}), "den": se({"pb": 1.0})}
    assert abs(_ind_h(tmp_path / "ind", {"pb": 1.0}, "nout")) == 0.0
    cons = [{"name": "c0", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": view}]
    p, res = run_oracle(_inp(make_lut(tmp_path / "lut.npz"), ind, constraints=cons), tmp_path / "o", sat_margin=0.05)
    c = res["free"]
    assert by_name(c["constraints"], "name", "c0")["judge"] == "N/A(SPICE 값 없음)"
    assert c["summary"]["acceptance"]["constraints_unmeasured"] == ["c0"]
    assert c["summary"]["verdict"] == "INCOMPLETE" and p.returncode == 0


@pytest.mark.parametrize("tol,exp", [(0.1, "FAIL"), (1.0, "PASS")])
def test_metric_record_only(tmp_path, ind, hand_psrr, tol, exp):
    """metric 은 기록(tolerances.ratio_db_abs, 오차 = SPICE - 예측): 예측을 0.5 dB 틀리게 -> 기록 판정만 바뀌고 verdict PASS."""
    m = [{"name": "psrr", "measure": "ratio_db", "value": hand_psrr - 0.5, "view": PSRR}]
    p, res = run_oracle(_inp(make_lut(tmp_path / "lut.npz"), ind, metrics=m), tmp_path / "o",
                        judge={"sat_margin_V": 0.05, "tolerances": {"ratio_db_abs": tol}})
    c = res["free"]
    r = _perf(c, "psrr")
    assert r["err"] == pytest.approx(0.5, abs=2e-3) and r["judge"] == exp, r
    assert c["summary"]["verdict"] == "PASS", c["summary"]


# ------------------------------------------------------------------ 막힘
BLOCK = {
    "internal_net": {"num": se({"nout": 1.0}), "den": se({"vdd": 1.0})},
    "reference_rail": {"num": se({"nin": 1.0}), "den": se({"gnd": 1.0})},
    "sense_not_net": {"num": se({"nin": 1.0}, "nosuch"), "den": se({"vdd": 1.0})},
    "sense_n_not_net": {"num": df({"nin": 1.0}, "nout", "nosuch"), "den": df({"vdd": 1.0})},
    "sense_reference": {"num": se({"nin": 1.0}, "gnd"), "den": se({"vdd": 1.0})},
}


@pytest.mark.parametrize("kind", list(BLOCK))
@pytest.mark.parametrize("where", ["constraint", "metric"])
def test_blocked_views(tmp_path, ind, kind, where):
    item = {"name": "x", "measure": "ratio_db", "view": BLOCK[kind]}
    if where == "constraint":
        inp = _inp(make_lut(tmp_path / "lut.npz"), ind, constraints=[dict(item, op=">=", limit=0.0)])
    else:
        inp = _inp(make_lut(tmp_path / "lut.npz"), ind, metrics=[dict(item, value=0.0)])
    p, text, meta = run_netlist(inp, tmp_path / "n")
    assert meta is not None and meta["blockers"], (kind, (p.stdout + p.stderr)[-800:])
    q, res = run_oracle(inp, tmp_path / "o", sat_margin=0.05)
    assert res["free"]["summary"]["verdict"] == "BLOCKED" and q.returncode == 2, res["free"]["summary"]


def test_blocked_control_valid_view_not_blocked(tmp_path, ind):
    """음성 대조: 같은 입력 모양에 유효한 뷰(입력·레일·게이트 바이어스)는 막히지 않는다."""
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind, constraints=[
        {"name": "ok", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": VIEWS["gate_bias_vsp"]},
        {"name": "ok2", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": PSRR}])
    p, text, meta = run_netlist(inp, tmp_path / "n")
    assert p.returncode == 0 and meta["blockers"] == [], meta and meta["blockers"]
    # 여기 수단은 넷리스트 이름 그대로 alter (README): Vac_nin, Vrail_vdd, Vbias_pb, Vrail_vsp
    low = text.lower()
    for src in ("vac_nin", "vrail_vdd", "vbias_pb", "vrail_vsp"):
        assert f"alter @{src}[acmag]" in low, src


def test_forced_held_net_excite_blocked(tmp_path, ind):
    """forced 는 예측 노드(nout, pout)를 Vhold 로 고정 -> 고정 넷 여기 = 막힘. 같은 뷰를 레일로 바꾸면 안 막힘."""
    for net, blocked in (("nout", True), ("vdd", False)):
        view = {"num": se({net: 1.0}, "pout"), "den": se({"vsp": 1.0}, "pout")}
        inp = _inp(make_lut(tmp_path / f"lut_{net}.npz"), ind,
                   constraints=[{"name": "x", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": view}])
        p, text, meta = run_netlist(inp, tmp_path / f"n_{net}", "forced")
        assert meta is not None and bool(meta["blockers"]) is blocked, (net, meta and meta["blockers"])
        if not blocked:
            assert elem(text, "Vhold_nout") is not None


# ------------------------------------------------------------------ 스키마(C13), iso·루프, 캐시(C21)
@pytest.mark.parametrize("where", ["constraint", "metric"])
def test_ratio_db_without_view_rejected_by_schema(tmp_path, ind, where):
    if where == "constraint":
        inp = _inp(make_lut(tmp_path / "lut.npz"), ind,
                   constraints=[{"name": "x", "measure": "ratio_db", "op": ">=", "limit": 0.0}])
    else:
        inp = _inp(make_lut(tmp_path / "lut.npz"), ind, metrics=[{"name": "x", "measure": "ratio_db", "value": 0.0}])
    out = tmp_path / "o"
    p, res = run_oracle(inp, out, sat_margin=0.05)
    assert p.returncode == 2 and res["free"] is None
    assert sorted(x.name for x in out.iterdir()) == ["t.input.json"], list(out.iterdir())


def test_no_ratio_in_iso_or_loop_netlists(tmp_path, ind):
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind, constraints=[
        {"name": "x", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": PSRR}])
    inp["process"]["models"]["nmos"]["polarity"] = "n"
    inp["process"]["models"]["pmos"]["polarity"] = "p"
    p, text, meta = run_netlist(inp, tmp_path / "iso", "iso")
    assert p.returncode == 0 and "acmag" not in text.lower() and "ratio" not in text.lower()
    fb = fb_input(make_lut(tmp_path / "lut_fb.npz"))
    fb["acceptance"] = {"constraints": [{"name": "x", "measure": "ratio_db", "op": ">=", "limit": 0.0,
                                         "view": {"num": se({"nin": 1.0}), "den": se({"vdd": 1.0})}}]}
    p, text, meta = run_netlist(fb, tmp_path / "fb")
    assert p.returncode == 0 and meta["blockers"] == [], meta and meta["blockers"]
    assert "ratio0" in text                                           # 본 넷리스트에는 있다
    loop = (tmp_path / "fb" / "t.free.loop.cir").read_text(encoding="utf-8")
    # 루프 넷리스트도 Middlebrook 주입에 acmag 를 쓰므로, ratio 측정의 흔적(ratio 파일·한 점 ac lin)이 없음을 본다
    assert "ratio" not in loop.lower() and "ac lin" not in loop.lower()


def test_cache_restores_ratio(tmp_path, ind):
    inp = _inp(make_lut(tmp_path / "lut.npz"), ind, constraints=[
        {"name": "x", "measure": "ratio_db", "op": ">=", "limit": 0.0, "view": PSRR}])
    cache = tmp_path / "cache"
    p1, r1 = run_oracle(inp, tmp_path / "o1", sat_margin=0.05, extra=["--cache-dir", cache])
    p2, r2 = run_oracle(inp, tmp_path / "o2", sat_margin=0.05, extra=["--cache-dir", cache])
    s2 = json.loads((tmp_path / "o2" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))
    assert s2["cache"]["main"] == "hit", s2["cache"]
    assert r2["free"]["summary"]["spice_ratio"][0]["ratio_db"] is not None
    assert r2["free"]["summary"]["spice_ratio"][0]["ratio_db"] == r1["free"]["summary"]["spice_ratio"][0]["ratio_db"]
    assert (tmp_path / "o2" / f"{stem_of(inp, 'free')}.ratio0.num.txt").exists()
