"""`offset_analysis` -- 설계 40 §3.8-8 `offset_in_sigma_mv`·`offset_excess`·`offset_contrib`, 41 §6.4-2, 체크리스트 D-OF1·D-OF2,
metrics CONTRACT 10.2. σ²_in = Σ_i (Z_i·gm_i·σ_VGS,i)² / A_dm² (모든 MOS, A_dm = 뷰 여기의 DC 관측값, 부호 포함).

oracle:
* (a) 물리 불변식: 소자 i 의 채널 전류 오차 gm_i·σ_i 는 그 소자 gate 에 직렬로 놓인 전압 σ_i 와 같다 -- 입력 소자(gate = 입력 포트)의
  입력 환산은 회로와 무관하게 정확히 σ_i 다. 대칭 차동쌍의 꼬리는 차동 출력에 0 을 보낸다. 단일 소자 회로는 σ_in = σ_1.
* (a) 폐형식(이 파일 docstring 유도): 캐스코드 CS 의 단락 출력 전류법 -- 입력 Gm = gm1·(gmc+gdsc)/(gmc+gdsc+gds1),
  캐스코드 오차 δc 의 단락 전류 δc·gds1/(gmc+gdsc+gds1) -> 입력 환산 σc·gmc·gds1/(gm1·(gmc+gdsc)) (설계 표 '캐스코드 기여가
  1/(gm·ro) 배로 감쇠'), 전류원 부하 오차 δl -> δl/Gm. 5T OTA 의 gds -> 0 극한 σ_in² = σ1² + σ2² + (gm3/gm1)²(σ3² + σ4²).
* (b) 소자별 섭동 DC 재풀이: 소자 i 에 전류원 gm_i·σ_i(d -> s)를 넣고 `u7_hand.ref_solve`(독립 numpy KCL)로 출력 변화를 소자마다 따로 푼다
  (엔진은 수반 1회) -- 설계 40 §11 'offset toy 손계산·섭동 재풀이(b)'.
* (a) 이름 전단사 불변, 결정론.
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.authoring import ViewDecl
from gmid_engine.metrics import OffsetAnalysis, offset_analysis

from . import u7_hand as H
from .conftest import codes

MV = 1e3


def _sig(rows, sigma=None, tol=None):
    sigma = sigma or {}
    return tuple((r["label"], sigma.get(r["label"], 1e-3), tol) for r in rows)


def _perturb_ref(m, r, ground, inputs, excite, sense, sigmas):
    """(b) 독립 섭동 재풀이: -> (σ_in V, A_dm, {소자: 출력 변화 / 오차 전류})."""
    zero = {n: 0.0 for n in ground + inputs}
    drive = dict(zero, **excite)
    a = H.sense_of(H.ref_solve(m, r, drive), *sense)
    out = {}
    total = 0.0
    for row in m:
        delta = row["gm"] * sigmas[row["label"]]
        v = H.ref_solve(m, r, zero, {row["d"]: -delta, row["s"]: delta})       # 채널 전류 d -> s 가 delta 만큼 더 흐른다
        dy = H.sense_of(v, *sense)
        out[row["label"]] = dy / delta if delta else 0.0
        total += dy * dy
    return math.sqrt(total) / abs(a), a, out


# ---------------------------------------------------------------- (a) 대칭 저항 부하 차동쌍

def test_symmetric_pair_sigma_root2_and_excess_one():
    """입력쌍 σ 1 mV 씩, 꼬리 2 mV: σ_in = √2 mV(입력 소자는 정확히 σ_i, 꼬리는 대칭이라 0), excess = 1.
    A_dm = gm·(R ∥ 1/gds) = 1e-3/(1e-4 + 1e-5) = 9.0909...(감지 op − om, ip = +½)."""
    nets, m, r, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, r, ground, inputs)
    got = offset_analysis(ss, H.transfer({"ip": 0.5, "im": -0.5}, "op", "om"), _sig(m, {"M3": 2e-3}), ("M1", "M2"))
    assert isinstance(got, OffsetAnalysis) and got.undefined == ()
    assert got.a_dm == pytest.approx(1e-3 / (1e-4 + 1e-5), rel=1e-12)
    assert got.sigma_in_mv == pytest.approx(math.sqrt(2.0), rel=1e-12)
    assert got.excess == pytest.approx(1.0, rel=1e-12)
    shares = {c.device: c.share for c in got.contrib}
    assert shares["M1"] == pytest.approx(0.5, rel=1e-12) and shares["M2"] == pytest.approx(0.5, rel=1e-12)
    assert shares["M3"] == pytest.approx(0.0, abs=1e-20)


def test_a_dm_sign_follows_sense_order():
    """감지 쌍을 뒤집으면 A_dm 부호만 바뀌고 σ_in 은 같다(크기 |A_dm| 로 나눈다)."""
    nets, m, r, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, r, ground, inputs)
    a = offset_analysis(ss, H.transfer({"ip": 0.5, "im": -0.5}, "op", "om"), _sig(m), ("M1", "M2"))
    b = offset_analysis(ss, H.transfer({"ip": 0.5, "im": -0.5}, "om", "op"), _sig(m), ("M1", "M2"))
    assert b.a_dm == pytest.approx(-a.a_dm, rel=1e-14) and a.a_dm > 0
    assert b.sigma_in_mv == pytest.approx(a.sigma_in_mv, rel=1e-14)


# ---------------------------------------------------------------- (a) 캐스코드 CS 폐형식

def test_cascode_closed_form_and_attenuation():
    nets, m, r, ground, inputs = H.cascode_cs()
    p = {row["label"]: row for row in m}
    s1, sc, sl = 1.0e-3, 1.5e-3, 0.7e-3
    ss = H.circuit(nets, m, r, ground, inputs)
    got = offset_analysis(ss, H.transfer({"in": 1.0}, "out"), _sig(m, {"M1": s1, "Mc": sc, "Ml": sl}), ("M1",))
    gm1, gds1, gmc, gdsc, gml = p["M1"]["gm"], p["M1"]["gds"], p["Mc"]["gm"], p["Mc"]["gds"], p["Ml"]["gm"]
    in_c = sc * gmc * gds1 / (gm1 * (gmc + gdsc))                          # 캐스코드: 1/(gm·ro) 감쇠
    in_l = gml * sl * (gmc + gdsc + gds1) / (gm1 * (gmc + gdsc))           # 부하 전류원: δl / Gm
    want = math.sqrt(s1 ** 2 + in_c ** 2 + in_l ** 2)
    assert got.sigma_in_mv == pytest.approx(want * MV, rel=1e-10)
    assert got.excess == pytest.approx(want / s1, rel=1e-10)
    var = {c.device: c.variance_v2 for c in got.contrib}
    assert var["M1"] == pytest.approx(s1 ** 2, rel=1e-10)
    assert var["Mc"] == pytest.approx(in_c ** 2, rel=1e-10)
    assert var["Ml"] == pytest.approx(in_l ** 2, rel=1e-10)
    assert var["Mc"] < var["M1"] * (gds1 / gmc) ** 2 * (sc / s1) ** 2 * 1.0001     # 감쇠 인수 ≤ gds1/gmc (gm 같은 축척)


def test_five_transistor_ota_low_gds_limit():
    """(a) gds -> 0 극한(ideal 꼬리): σ_in² = σ1² + σ2² + (gm3/gm1)²(σ3² + σ4²), 꼬리 기여 0."""
    nets, m, r, ground, inputs = H.ota5(gm1=1e-3, gm3=4e-4, gds_in=1e-13, gds_ld=1e-13, gds_tail=1e-13, gmb_in=1.5e-4)
    sig = {"M1": 1e-3, "M2": 1.2e-3, "M3": 2e-3, "M4": 2.5e-3, "M5": 3e-3}
    got = offset_analysis(H.circuit(nets, m, r, ground, inputs), H.transfer({"ip": 0.5, "im": -0.5}, "out"), _sig(m, sig),
                          ("M1", "M2"))
    k = 4e-4 / 1e-3
    want = math.sqrt(sig["M1"] ** 2 + sig["M2"] ** 2 + k * k * (sig["M3"] ** 2 + sig["M4"] ** 2))
    assert got.sigma_in_mv == pytest.approx(want * MV, rel=1e-6)
    assert got.excess == pytest.approx(want / math.hypot(sig["M1"], sig["M2"]), rel=1e-6)
    assert {c.device: c.share for c in got.contrib}["M5"] == pytest.approx(0.0, abs=1e-6)


# ---------------------------------------------------------------- (b) 섭동 재풀이

@pytest.mark.parametrize("case", ["ota5", "cascode", "pair_asym"])
def test_matches_independent_perturbation_resolve(case):
    if case == "ota5":
        nets, m, r, ground, inputs = H.ota5()
        excite, sense, cells = {"ip": 0.5, "im": -0.5}, ("out", None), ("M1", "M2")
    elif case == "cascode":
        nets, m, r, ground, inputs = H.cascode_cs()
        excite, sense, cells = {"in": 1.0}, ("out", None), ("M1",)
    else:                                   # 비대칭(입력쌍 gm 다름, gmb 있음) -- 꼬리 기여가 0 이 아니다
        nets, m, r, ground, inputs = H.diff_pair(gmb=2e-4)
        m = (dict(m[0], gm=1.3e-3),) + tuple(m[1:])
        excite, sense, cells = {"ip": 0.5, "im": -0.5}, ("op", "om"), ("M1", "M2")
    sig = {row["label"]: 1e-3 * (1 + 0.37 * i) for i, row in enumerate(m)}
    got = offset_analysis(H.circuit(nets, m, r, ground, inputs), H.transfer(excite, *sense), _sig(m, sig), cells)
    sigma, a, z = _perturb_ref(m, r, ground, inputs, excite, sense, sig)
    assert got.a_dm == pytest.approx(a, rel=1e-10)
    assert got.sigma_in_mv == pytest.approx(sigma * MV, rel=1e-10)
    for c in got.contrib:
        assert c.z_ohm == pytest.approx(z[c.device], rel=1e-9, abs=1e-9 * max(abs(v) for v in z.values()))
    total = sum(c.variance_v2 for c in got.contrib)
    assert total == pytest.approx(sigma ** 2, rel=1e-10)
    assert sum(c.share for c in got.contrib) == pytest.approx(1.0, rel=1e-12)
    assert [c.variance_v2 for c in got.contrib] == sorted((c.variance_v2 for c in got.contrib), reverse=True)


def test_contrib_matching_tag_is_label_only():
    nets, m, r, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, r, ground, inputs)
    view = H.transfer({"ip": 0.5, "im": -0.5}, "op", "om")
    a = offset_analysis(ss, view, _sig(m), ("M1", "M2"), matching={"M1": "diff_pair", "M2": "diff_pair"})
    b = offset_analysis(ss, view, _sig(m), ("M1", "M2"))
    assert {c.device: c.matching for c in a.contrib} == {"M1": "diff_pair", "M2": "diff_pair", "M3": ""}
    assert a.sigma_in_mv == b.sigma_in_mv and a.excess == b.excess


# ---------------------------------------------------------------- 정의 불가·구조 입력 없음

def test_excess_undefined_without_input_cells_or_zero_variance():
    nets, m, r, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, r, ground, inputs)
    view = H.transfer({"ip": 0.5, "im": -0.5}, "op", "om")
    a = offset_analysis(ss, view, _sig(m))
    assert a.excess is None and codes(a.undefined) == {"input_cells_undeclared"}
    assert a.sigma_in_mv == pytest.approx(math.sqrt(2.0), rel=1e-12)          # σ_in 은 그대로 낸다
    b = offset_analysis(ss, view, _sig(m, {"M1": 0.0, "M2": 0.0}), ("M1", "M2"))
    assert b.excess is None and codes(b.undefined) == {"input_cell_variance_zero"}


def test_undefined_codes():
    nets, m, r, ground, inputs = H.cascode_cs()
    ss = H.circuit(nets, m, r, ground, inputs)
    view = H.transfer({"in": 1.0}, "out")
    for view_, sig, want in ((ViewDecl("ratio"), _sig(m), "unsupported_view"),
                             (H.transfer({"in": 1.0}, "vdd"), _sig(m), "sense_fixed"),
                             (view, _sig(m)[:2], "sigma_missing")):
        got = offset_analysis(ss, view_, sig, ("M1",))
        assert got.sigma_in_mv is None and got.excess is None and codes(got.undefined) == {want}
    dead = tuple(dict(row, gm=0.0) if row["label"] == "M1" else row for row in m)       # 입력 소자 gm 0 -> A_dm = 0
    got = offset_analysis(H.circuit(nets, dead, r, ground, inputs), view, _sig(dead), ("M1",))
    assert codes(got.undefined) == {"gain_zero"} and got.sigma_in_mv is None
    nets2 = nets + ("y", "z")
    float_pair = (H.res("Rf", "y", "z", 1e3),)                                         # 접지 경로 없는 두 노드 -> 특이
    got = offset_analysis(H.circuit(nets2, m, float_pair, ground, inputs), view, _sig(m), ("M1",))
    assert codes(got.undefined) == {"singular_dc"}


# ---------------------------------------------------------------- 분해능

def test_resolution_single_device_is_mismatch_tol():
    """단일 CS(저항 부하): σ_in = σ_1 은 gm·gds 와 무관 -> LUT 허용오차 항 0, mismatch 허용오차 t 만 남는다: 분해능 = t."""
    nets = ("gnd", "vdd", "in", "out")
    m = (H.mos("M1", "out", "in", "gnd", "gnd", 1e-3, 2e-5),)
    r = (H.res("R1", "vdd", "out", 2e4),)
    ss = H.circuit(nets, m, r, ("gnd", "vdd"), ("in",))
    got = offset_analysis(ss, H.transfer({"in": 1.0}, "out"), (("M1", 1e-3, 1e-4),), ("M1",), rel_tols={"M1": 1e-3})
    assert got.sigma_in_mv == pytest.approx(1.0, rel=1e-12)
    assert got.resolution_mv == pytest.approx(0.1, rel=1e-6)
    assert got.excess == pytest.approx(1.0, rel=1e-12)


def test_resolution_none_when_any_tolerance_missing():
    nets, m, r, ground, inputs = H.diff_pair()
    ss = H.circuit(nets, m, r, ground, inputs)
    view = H.transfer({"ip": 0.5, "im": -0.5}, "op", "om")
    full = {row["label"]: 1e-3 for row in m}
    a = offset_analysis(ss, view, _sig(m, tol=1e-5), ("M1", "M2"), rel_tols=full)
    assert a.resolution_mv is not None and a.resolution_mv > 0
    b = offset_analysis(ss, view, _sig(m, tol=1e-5), ("M1", "M2"), rel_tols=dict(full, M3=None))
    c = offset_analysis(ss, view, _sig(m, tol=None), ("M1", "M2"), rel_tols=full)
    assert b.resolution_mv is None and c.resolution_mv is None


# ---------------------------------------------------------------- 불변

def test_name_bijection_and_node_order_invariance():
    nets, m, r, ground, inputs = H.ota5()
    sig = {row["label"]: 1e-3 * (1 + 0.2 * i) for i, row in enumerate(m)}
    a = offset_analysis(H.circuit(nets, m, r, ground, inputs), H.transfer({"ip": 0.5, "im": -0.5}, "out"), _sig(m, sig),
                        ("M1", "M2"))
    nmap = {"ip": "n_q", "im": "n_a", "t": "n_z", "x": "n_b", "out": "n_c", "vb": "n_y", "vdd": "n_vv", "gnd": "n_00"}
    dmap = {"M1": "Z9", "M2": "A1", "M3": "Q", "M4": "B", "M5": "C0"}
    nets2, m2, r2 = H.rename(nets, m, r, nmap, dmap, order_seed=7)
    sig2 = {dmap[k]: v for k, v in sig.items()}
    b = offset_analysis(H.circuit(nets2, m2, r2, [nmap[g] for g in ground], [nmap[i] for i in inputs]),
                        H.transfer({"n_q": 0.5, "n_a": -0.5}, "n_c"), _sig(m2, sig2), ("Z9", "A1"))
    assert b.sigma_in_mv == pytest.approx(a.sigma_in_mv, rel=1e-12)
    assert b.excess == pytest.approx(a.excess, rel=1e-12)
    assert b.a_dm == pytest.approx(a.a_dm, rel=1e-12)
    va = {dmap[c.device]: c.variance_v2 for c in a.contrib}
    vb = {c.device: c.variance_v2 for c in b.contrib}
    assert set(va) == set(vb)
    for k in va:
        assert vb[k] == pytest.approx(va[k], rel=1e-10, abs=1e-30)


def test_deterministic():
    nets, m, r, ground, inputs = H.ota5()
    args = (H.circuit(nets, m, r, ground, inputs), H.transfer({"ip": 0.5, "im": -0.5}, "out"), _sig(m, tol=1e-5), ("M1", "M2"),
            {row["label"]: 1e-3 for row in m})
    assert offset_analysis(*args) == offset_analysis(*args)
