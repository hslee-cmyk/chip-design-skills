"""U6 offset Monte-Carlo(설계 40 §10.2 '오라클 offset Monte-Carlo' 행, §11 U6 'MC 표본 수 유도', README "offset Monte-Carlo").

기대값 출처(피검 코드 출력으로 만들지 않음):
  * 표본 수 N: oracle (b) -- 정규 표본 표준편차의 상대 표준오차 1/sqrt(2(N−1)) 가 목표 r 이하가 되는 최소 N 을 N = 2, 3, ... 전수
    탐색으로 찾는다(폐형식 ceil(1 + 1/(2r²)) 과 다른 방법).
  * σ_in: oracle (c) -- u6_toy5t 의 독립 넷리스트에서 소자·mismatch 변수마다 1σ 결정적 섭동으로 잰 입력 환산 offset 변화의 RSS
    (선형 합성 σ). MC 표본 σ 의 상대 표준오차가 r 이므로 |σ_MC/σ_RSS − 1| <= 3r(정규 근사 3σ) 를 허용한다. 또 입력쌍 vth0
    1σ 섭동 하나는 손계산(oracle (a)) Δvth0 = vth0_slope/sqrt(L_µm·W_µm)(PDK mismatch 카드 값)과 같아야 한다(단위 확인).
"""
import json
import math
import re

import pytest

import conftest
import u6_toy5t as toy
from conftest import cs_input, make_lut, run_oracle, stem_of
from test_oracle_c10_stability import SAT

R_MC = 0.05                                   # 목표 상대 표준오차(입력 offset_mc.rel_resolution)


def n_by_scan(r, cap=None):
    """oracle (b): 1/sqrt(2(N−1)) <= r 인 최소 N(N >= 2) -- 전수 탐색. cap 이 있으면 min(N, cap)."""
    n = 2
    while 1.0 / math.sqrt(2.0 * (n - 1)) > r:
        n += 1
    return n if cap is None else min(n, cap)


def _mc_mod():
    import importlib
    import sys
    d = str(conftest.ORACLE_DIR)
    if d not in sys.path:
        sys.path.insert(0, d)
    return importlib.import_module("oracle_offset_mc")


@pytest.mark.parametrize("r", [0.05, 0.1, 0.07, 0.3, 0.5])
def test_sample_count_formula_matches_scan(r):
    n, capped, se = _mc_mod().sample_count(r)
    assert n == n_by_scan(r) and capped is False, (r, n, n_by_scan(r))
    assert se == pytest.approx(1.0 / math.sqrt(2.0 * (n - 1)), rel=1e-12) and se <= r * (1 + 1e-12)


def test_sample_count_cap():
    """max_samples 가 유도값보다 작으면 N = 상한, n_capped, 실제 상대 표준오차 = 1/sqrt(2(N−1)) (> r)."""
    n, capped, se = _mc_mod().sample_count(0.01, max_samples=30)
    assert (n, capped) == (30, True) and se == pytest.approx(1.0 / math.sqrt(58.0), rel=1e-12) and se > 0.01


@pytest.fixture(scope="module")
def mc_run(tmp_path_factory):
    conftest.require_spice()
    d = tmp_path_factory.mktemp("mc5t")
    nom = toy.nominal_op(d / "ind_op")
    sens = toy.mismatch_sensitivities(d / "ind_mm", nom["out"])
    inp = toy.toy_input(d, nom, offset_mc={"rel_resolution": R_MC, "seed": 0})
    p, res = run_oracle(inp, d / "o", sat_margin=SAT)
    assert res["free"] is not None, (p.stdout + p.stderr)[-1500:]
    sim = json.loads((d / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))
    return inp, sim, res["free"], sens, p


def test_mc_sample_count_and_record(mc_run):
    inp, sim, cmp, sens, p = mc_run
    mc = sim["offset_mc"]
    assert mc["status"] == "ok" and mc["n_failed"] == 0, mc
    assert mc["n_samples"] == n_by_scan(R_MC) == 201 and mc["n_capped"] is False, mc     # 201: 1/sqrt(2·200) = 0.05
    assert mc["rel_se_achieved"] == pytest.approx(1 / math.sqrt(2 * (mc["n_samples"] - 1)), rel=1e-12)
    assert mc["seed"] == 0
    # 소자마다 독립 변수(PDK mismatch 카드의 *_slope_spectre 전부: nfet toxe·vth0·voff, pfet + nfactor)
    assert {k: [re.sub(r"^.*__(\w+)_slope_spectre$", r"\1", v) for v in vs] for k, vs in mc["mismatch_vars"].items()} == {
        nm: list(toy.VARS[toy.DEV[nm][0]]) for nm in toy.DEV}, mc["mismatch_vars"]
    assert p.returncode == 0


def test_input_pair_vth0_sensitivity_unit_hand_calc(mc_run):
    """oracle (a): 입력쌍 M1 의 vth0 1σ 섭동(독립 넷리스트)이 입력 환산 offset 을 손계산 σ_vth0 = slope/sqrt(L_µm·W_µm) 만큼
    옮긴다(입력쌍 문턱 변화는 입력 offset 과 1:1 -- 1 % 안: 꼬리 이상 전류원이라 몸체 효과 외 2 차 효과가 작다). slope 는 PDK
    mismatch 카드에서 읽고, 이 크기(L 1 µm, finger W 2 µm) 가 드는 tt 카드 bin(lmin <= L < lmax, wmin <= W < wmax)의 vth0 식이 쓰는
    slope 이름(vth0_slope 또는 vth0_slope1)을 카드에서 찾는다."""
    inp, sim, cmp, sens, p = mc_run
    c = toy.T5
    cells = conftest.PDK / "cells/nfet_01v8"
    mm = (cells / "sky130_fd_pr__nfet_01v8__mismatch.corner.spice").read_text(encoding="utf-8")
    slopes = {k: float(v) for k, v in re.findall(r"\.param\s+sky130_fd_pr__nfet_01v8__(vth0_slope1?)\s*=\s*([-+0-9.eE]+)", mm)}
    card = (cells / "sky130_fd_pr__nfet_01v8__tt.pm3.spice").read_text(encoding="utf-8")
    names = []
    for blk in re.split(r"\n\.model\s+", card)[1:]:
        g = {k: float(v) for k, v in re.findall(r"\b(lmin|lmax|wmin|wmax)\s*=\s*([-+0-9.eE]+)", blk)}
        if g and g["lmin"] <= c["L"] < g["lmax"] and g["wmin"] <= c["fw"] < g["wmax"]:
            names += re.findall(r"vth0\s*=\s*\{[^}]*?(vth0_slope1?)/sqrt", blk)
    assert len(names) == 1, names                                  # 정확히 한 bin
    sig = slopes[names[0]] / math.sqrt(c["L"] * 1e6 * c["fw"] * 1e6 * c["n"])
    assert abs(sens["M1:vth0"]) == pytest.approx(sig, rel=0.01), (sens["M1:vth0"], sig, names)


def test_mc_sigma_matches_deterministic_rss(mc_run):
    """oracle (c): σ_MC(오라클) 와 독립 1σ 섭동 RSS 의 비 -- |σ_MC/σ_RSS − 1| <= 3r (r = 표본 σ 의 상대 표준오차)."""
    inp, sim, cmp, sens, p = mc_run
    rss_mv = 1e3 * math.sqrt(sum(v * v for v in sens.values()))
    s = sim["offset_mc"]["sigma_in_mV"]
    assert abs(s / rss_mv - 1) <= 3 * R_MC, (s, rss_mv)
    # 제약 measure 이름으로도 같은 값이 나온다(README U6: offset_in_sigma_mv)
    u6 = cmp["summary"]["u6"]
    assert u6["offset_mc"]["sigma_in_mV"] == s


def test_mc_unavailable_without_differential_input(tmp_path):
    """README offset MC: 입력이 차동 쌍이 아니거나 servo(Lfb_)가 없으면 status = unavailable + 이유(값을 지어내지 않음)."""
    ind = conftest.independent_cs(tmp_path / "ind")
    pr = conftest.preds_from_independent(ind)
    inp = cs_input(make_lut(tmp_path / "lut.npz"), diffusion="zero", preds_nodes=pr["nodes"], preds_devices=pr["devices"])
    inp["offset_mc"] = {"rel_resolution": 0.3}
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    sim = json.loads((tmp_path / "o" / f"{stem_of(inp, 'free')}.sim.json").read_text(encoding="utf-8"))
    mc = sim["offset_mc"]
    assert mc["status"] == "unavailable" and mc["reason"] and mc.get("sigma_in_mV") is None, mc


@pytest.mark.parametrize("blk", [{}, {"rel_resolution": 0.0}, {"rel_resolution": 0.05, "max_samples": 1}])
def test_offset_mc_block_schema_rejected(tmp_path, blk):
    """C13 + 스키마 offset_mc: rel_resolution 필수·양수, max_samples >= 2 -- 위반이면 산출물 없이 반환 2."""
    inp = toy.toy_input(tmp_path, {k: 0.9 for k in toy.NODES}, offset_mc=blk)
    p, res = run_oracle(inp, tmp_path / "o", sat_margin=SAT)
    assert p.returncode == 2 and res["free"] is None, (p.returncode, (p.stdout + p.stderr)[-800:])
