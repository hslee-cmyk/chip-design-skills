"""`mismatch_sigma_vgs` -- CONTRACT 10.4 [r7], 설계 41 §6.4-2 'mismatch 모델(옛 식 대체)':
σ_VGS(W, L, 점) = √(Σ_k (DVGS_k · slope_k(bin(W, L)) / slope_k(bin_ref))²) · √(W_ref·L)/√(W·L).
[WB-1 D-3] 서명 `mismatch_sigma_vgs(memo, model, kind, w_key, L, vgs, vds, vsb, w_bin_m, w_area_m)`: slope bin 은 손가락 폭 `w_bin_m`(= w_f), 면적 항은 총 폭 `w_area_m`(= DeviceOp.W)로 센다.
아래 옛 호출은 두 폭이 같은 소자(손가락 하나)라 `X, X` 로 옮겼다(기대값 불변).

oracle:
- (a) 손계산(설계 식에 합성 값을 넣은 산수 -- 계약 10.4 손계산 행 그대로): DVGS = (1, 2, 2) mV.
- (a) PDK 원본 독립 파싱: 모델 카드 `.model` 블록의 lmin·lmax·wmin·wmax 와 변수 식의 slope 이름, mismatch 파일의 `.param` 값을
  이 파일이 정규식으로 읽어 bin(W, L) 을 정한다(bin 규칙: 양끝 닫힘, 경계 공유 시 아래 bin -- CONTRACT 4.0.1, 실측 근거 384/384).
- (c)/(a) 설계 41 §6.4-2 '참고 유도값 ... LUT 감도 열의 vth0 성분은 이 값과 같아야 한다(U3 test (c))': √2·σ_vth0·√(W·L) = √2·vth0_slope(bin).
"""
import math
import re

import numpy as np
import pytest

from gmid_engine.core import PdkMismatchBlock, PdkMismatchModel, SealViolationError
from gmid_engine.lut import MismatchSigma, mismatch_dvgs, mismatch_sigma_vgs

from .conftest import TOY_SHAPE, MismatchToy, detail_of, new_memo

DV = {"vth0": 1e-3, "toxe": 2e-3, "voff": 2e-3}       # 계약 10.4 손계산 (1, 2, 2) mV
REF = {"vth0": 3e-3, "toxe": 2e-3, "voff": 1e-3}


def _block(name="toy_model.1", lmin=0.5e-6, lmax=5e-6, wmin=0.5e-6, wmax=10e-6, **slopes):
    s = dict(REF, **slopes)
    rows = tuple((p, None, None, None) if s[p] is None else (p, "toy_%s_slope" % p, s[p], 1 + i)
                 for i, p in enumerate(("toxe", "voff", "vth0")))
    return PdkMismatchBlock(name, lmin, lmax, wmin, wmax, rows, 10)


def _model(*blocks):
    return PdkMismatchModel("nmos", ("toxe", "voff", "vth0"), tuple(blocks), "0" * 64, "0" * 64)  # [U17 ①-b 3차, 결정 7] 경로 칸 없음: (model_sha256, slope_sha256)


@pytest.fixture
def mm_lut(tmp_path):
    t = MismatchToy(tmp_path / "m", {p: np.full(TOY_SHAPE, v) for p, v in DV.items()}, slope_ref=REF)
    return t.load()


def test_hand_calc_reference_width(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert isinstance(r, MismatchSigma)
    assert math.isclose(r.sigma_v, 3e-3, rel_tol=1e-12)             # √(1 + 4 + 4) mV
    assert dict(r.parts) == pytest.approx(DV, rel=1e-12)
    assert r.model == "toy_model.1"


def test_hand_calc_four_times_width(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 4e-6, 4e-6)
    assert math.isclose(r.sigma_v, 1.5e-3, rel_tol=1e-12)           # √(W_ref/W) = 1/2


def test_hand_calc_device_bin_slope_twice(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block(toxe=4e-3)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert math.isclose(r.sigma_v, math.sqrt(1 + 16 + 4) * 1e-3, rel_tol=1e-12)


def test_hand_calc_variable_unused_in_device_bin(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block(voff=None)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert math.isclose(r.sigma_v, math.sqrt(5) * 1e-3, rel_tol=1e-12)


def test_memo_key_distinguishes_pdk_model(mm_lut):
    """[RED 예상 -- 결함 보고] 같은 memo 에서 PDK mismatch 모델만 다른 두 호출은 다른 값이어야 한다(10.4 식의 slope_k(bin(W, L)) 는
    model 인자에서 온다). memo 키가 model 을 빼면 두 번째 호출이 첫 호출 값을 돌려준다 -- 같은 LUT 로 다른 PDK 선언(slope 정정)을
    쓰면 조용히 옛 값이 나온다."""
    m = new_memo(mm_lut)
    a = mismatch_sigma_vgs(m, _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    b = mismatch_sigma_vgs(m, _model(_block(toxe=4e-3)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert math.isclose(a.sigma_v, 3e-3, rel_tol=1e-12)
    assert math.isclose(b.sigma_v, math.sqrt(21) * 1e-3, rel_tol=1e-12)


def test_no_block_rejected(mm_lut):
    with pytest.raises(SealViolationError) as ei:
        mismatch_sigma_vgs(new_memo(mm_lut), _model(_block(lmin=2e-6)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert detail_of(ei.value)["reason"] == "lut_mismatch_no_block"


def test_unscalable_slope_rejected(tmp_path):
    """기준 bin 이 voff 를 안 쓰는데(slope_ref 0) 소자 bin 은 쓰면 비율이 정의되지 않는다 -> `lut_mismatch_slope_unscalable`."""
    t = MismatchToy(tmp_path / "u", {p: np.full(TOY_SHAPE, v) for p, v in DV.items()}, slope_ref=dict(REF, voff=None))
    with pytest.raises(SealViolationError) as ei:
        mismatch_sigma_vgs(new_memo(t.load()), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert detail_of(ei.value)["reason"] == "lut_mismatch_slope_unscalable"


@pytest.mark.parametrize("W", [0.0, -1e-6])
def test_nonpositive_width(mm_lut, W):
    with pytest.raises(ValueError):
        mismatch_sigma_vgs(new_memo(mm_lut), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, W, W)


def test_bin_boundary_belongs_to_lower_block(mm_lut):
    """bin 규칙(CONTRACT 4.0.1): L 이 두 블록이 공유한 경계값이면 아래 블록. 아래 블록 toxe slope 2배 -> √21 mV."""
    lo = _block("low", lmin=0.5e-6, lmax=1e-6, toxe=4e-3)
    hi = _block("high", lmin=1e-6, lmax=5e-6)
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(lo, hi), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    assert r.model == "low" and math.isclose(r.sigma_v, math.sqrt(21) * 1e-3, rel_tol=1e-12)


# ---------------------------------------------------------------- 실데이터: PDK 원본 독립 파싱

def _parse_card(pdk_root, dev):
    card = open("%s/cells/%s/sky130_fd_pr__%s__tt.pm3.spice" % (pdk_root, dev, dev), encoding="utf-8").read()
    vals = {}
    for line in open("%s/cells/%s/sky130_fd_pr__%s__mismatch.corner.spice" % (pdk_root, dev, dev), encoding="utf-8"):
        mm = re.match(r"\s*\.param\s+(\S+)\s*=\s*(\S+)", line)
        if mm:
            vals[mm.group(1).lower()] = float(mm.group(2))
    blocks = []
    for part in re.split(r"(?im)^\.model\s+", card)[1:]:
        name = part.split()[0]

        def num(k):
            m2 = re.search(r"(?i)\b%s\s*=\s*([-+0-9.eE]+)" % k, part)
            return float(m2.group(1)) if m2 else None
        sl = {}
        for var in ("vth0", "toxe", "voff", "nfactor"):
            m3 = re.search(r"(?i)\b%s\s*=\s*\{[^}]*?(\w+_slope\d*)\s*/\s*sqrt" % var, part)
            if m3:
                sl[var] = vals[m3.group(1).lower()]
        blocks.append((name, num("lmin"), num("lmax"), num("wmin"), num("wmax"), sl))
    return blocks


def _in(x, lo, hi):
    return (lo <= x or abs(x - lo) <= math.ulp(lo)) and (x <= hi or abs(x - hi) <= math.ulp(hi))


def _bin(blocks, W, L):
    """양끝 닫힘, 공유 경계는 아래 구간(W 먼저, 그 W bin 안 L)."""
    wbins = sorted({(b[3], b[4]) for b in blocks})
    wb = next((w for w in wbins if _in(W, *w)), None)
    cand = sorted((b for b in blocks if (b[3], b[4]) == wb), key=lambda b: (b[1], b[2]))
    return next((b for b in cand if _in(L, b[1], b[2])), None)


@pytest.mark.lut_realdata
def test_real_slope_ref_is_reference_width_bin(real_nm_memo, real_nm_lut, real_paths):
    """(a) slope_ref(조회 L) = PDK 파싱 bin(W_ref = 5 µm, L) 의 slope -- pfet L ≤ 0.5 µm 은 vth0_slope1 7.356e-3, 그 위 5.856e-3."""
    for kind, dev in (("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")):
        blocks = _parse_card(real_paths["pdk_root"], dev)
        w_ref = real_nm_lut.mismatch[kind].w_ref_m
        for L in real_nm_lut.mismatch[kind].grids[0]:
            r = mismatch_dvgs(real_nm_memo, kind, 1000, L, 0.9, 0.9, 0.0)
            b = _bin(blocks, w_ref, L)
            for p in real_nm_lut.mismatch[kind].params:
                assert math.isclose(r.slope_ref[p], b[5].get(p, 0.0), rel_tol=1e-15), (kind, L, p)
    blocks = _parse_card(real_paths["pdk_root"], "pfet_01v8")
    assert _bin(blocks, 5e-6, 0.5e-6)[5]["vth0"] == 7.356e-3 and _bin(blocks, 5e-6, 0.7e-6)[5]["vth0"] == 5.856e-3


@pytest.mark.lut_realdata
def test_real_narrow_width_bin_scales_by_slope_ratio(real_nm_memo, real_pdk_decl, real_paths, raw_mismatch, raw_cap):
    """(a) nfet W = 0.45 µm·L = 8 µm 는 PDK 카드에서 vth0_slope1(7.356e-3) 블록, 기준 폭 5 µm·8 µm 블록은 vth0_slope(3.356e-3).
    parts[vth0] = |DVGS_vth0(npz 격자점)|·(7.356/3.356)·√(5/0.45) (설계 41 §6.4-2 σ_VGS 식, 기하 √(W_ref/W))."""
    blocks = _parse_card(real_paths["pdk_root"], "nfet_01v8")
    W, L = 0.45e-6, 8e-6
    b_dev, b_ref = _bin(blocks, W, L), _bin(blocks, 5e-6, L)
    assert b_dev[5]["vth0"] == 7.356e-3 and b_ref[5]["vth0"] == 3.356e-3
    i = int(np.argmin(np.abs(raw_cap["L"] - L)))
    g = int(np.argmin(np.abs(raw_cap["VGS"] - 0.9)))
    k = int(np.argmin(np.abs(raw_cap["VDS"] - 0.9)))
    r = mismatch_sigma_vgs(real_nm_memo, real_pdk_decl.mismatch_model("nmos"), "nmos", 1000, float(raw_cap["L"][i]),
                           float(raw_cap["VGS"][g]), float(raw_cap["VDS"][k]), 0.0, W, W)
    assert r.model.lower() == b_dev[0].lower()
    parts = dict(r.parts)
    for p in ("vth0", "toxe", "voff"):
        d = abs(float(raw_mismatch["DVGS_%s_n" % p][i, g, k, 0]))
        exp = d * (b_dev[5][p] / b_ref[5][p]) * math.sqrt(5e-6 / W)
        assert math.isclose(parts[p], exp, rel_tol=1e-12), p
    assert math.isclose(r.sigma_v, math.sqrt(sum(v * v for v in parts.values())), rel_tol=1e-12)


# 기준값 √2·vth0_slope 를 확인한 소자 쌍 Monte Carlo 의 표본 수(계약 10.6·기록 docs/03-analysis/...u3-lut-pdk-record.md §5:
# `sky130_pair_mc.py --n 1000`, 사례마다 표본 1000).
PAIR_MC_SAMPLES = 1000


def _expected_max_abs_normal(n):
    """E[max_{i ≤ n} |Z_i|], Z ~ N(0, 1) 독립 = ∫_0^∞ f(x) dx, f = 1 − F^n, F(x) = erf(x/√2) (|Z| 의 분포함수).
    중점 규칙(칸 폭 h = 2^-10) + 오차 상한을 함께 낸다 -> (값, 상한). 오차 상한(유도):
      절단: x_hi = f 의 상계 n·erfc(x/√2) 가 2^-53 아래가 되는 첫 정수 -> 꼬리 ∫_{x_hi}^∞ f ≤ n·∫ erfc ≤ n·erfc(x_hi/√2)·√(π/2)
      (erfc(x/√2) ≤ e^(−x²/2) 의 꼬리 적분 상계), 중점 규칙: |E| ≤ x_hi·h²·max|f''|/24,
      f'' = −n[(n − 1)F^(n−2)F'² + F^(n−1)F''], F' = √(2/π)e^(−x²/2) ≤ √(2/π), |F''| = x·F' ≤ √(2/π)e^(−1/2)
      -> max|f''| ≤ n(n − 1)·2/π + n·√(2/π)·e^(−1/2)."""
    x_hi = 1
    while n * math.erfc(x_hi / math.sqrt(2.0)) >= 2.0 ** -53:
        x_hi += 1
    h = 2.0 ** -10
    steps = int(round(x_hi / h))
    val = h * sum(1.0 - math.erf((j + 0.5) * h / math.sqrt(2.0)) ** n for j in range(steps))
    f2 = n * (n - 1) * 2.0 / math.pi + n * math.sqrt(2.0 / math.pi) * math.exp(-0.5)
    err = x_hi * h * h * f2 / 24.0 + n * math.erfc(x_hi / math.sqrt(2.0)) * math.sqrt(math.pi / 2.0)
    return val, err


def _vth0_ratio_bound(n_compared, n_mc=PAIR_MC_SAMPLES):
    """vth0 성분 비의 허용 상한 -- 표본 수에서 유도(고른 상수 없음).
    1) 기준값 √2·slope 는 N = n_mc 표본 쌍 MC 의 σ 추정으로 확인된 값이다(그 MC 가 이 비교의 기준). 정규 표본 표준편차의 상대
       표준오차 SE = 1/√(2(N − 1)) (χ²(N − 1) 의 1차 근사 -- 기록 §5 '통계 오차 1/√(2(N−1)) = 2.2 %'). 그 MC 는 SE 보다 작은 차를 가리지 못한다.
    2) 이 test 는 n_compared 개 격자점을 각각 그 분해능으로 비교한다 -- n 개 비교에서 표집만으로 생기는 가장 큰 |편차| 의 기댓값
       = SE · E[max_{i ≤ n} |Z_i|] (`_expected_max_abs_normal`, 적분 오차 상한까지 더한다).
    상한 = SE · (E[max |Z|] + 적분 오차 상한). (n = 1 이면 E|Z| = √(2/π).)"""
    val, err = _expected_max_abs_normal(n_compared)
    return (val + err) / math.sqrt(2.0 * (n_mc - 1))


def test_vth0_ratio_bound_derivation():
    """유도 상한 자체의 확인(oracle (a) 닫힌 식): n = 1 이면 E|Z| = √(2/π) -- 적분값과 닫힌 값의 차 ≤ 같은 함수의 오차 상한.
    n 이 늘면 상한은 단조 증가(최댓값의 기댓값)."""
    val, err = _expected_max_abs_normal(1)
    assert abs(val - math.sqrt(2.0 / math.pi)) <= err
    b = [_vth0_ratio_bound(n) for n in (1, 10, 100, 1000)]
    assert all(x < y for x, y in zip(b, b[1:]))


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,dev", [("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")])
def test_real_vth0_component_equals_sqrt2_slope(real_nm_memo, real_pdk_decl, real_paths, raw_cap, kind, dev):
    """설계 41 §6.4-2: 'LUT 감도 열의 vth0 성분은 √2·slope(bin별) 과 같아야 한다'. 쌍 A_VT 성분 = √2·parts[vth0]·√(W·L[µm²]).
    판정: W = 5 µm, L 앵커 ≥ 0.3 µm, |VDS| 0.9 V, VS 0, 격자 gm/ID 5~15 점(n 개)에서 |A_VT/(√2·slope) − 1| ≤ `_vth0_ratio_bound(n)`.
    [2026-10-09 오케스트레이터 결정 '고른 허용오차 금지'] 옛 ±0.05(고른 수)를 표본 수에서 유도한 상한으로 바꿨다(아래 함수 주석).
    짧은 채널(L < 0.3 µm)은 같은 ID 의 ΔVGS 가 ΔVT 와 다른 물리 효과가 커 이 판정에서 뺀다(계약 10.6 의 pfet 0.18 µm 9.71 대 10.40)."""
    blocks = _parse_card(real_paths["pdk_root"], dev)
    model = real_pdk_decl.mismatch_model(kind)
    suf = "_n" if kind == "nmos" else "_p"
    k = int(np.argmin(np.abs(raw_cap["VDS"] - 0.9)))
    gm = raw_cap["GM" + suf][:, :, k, 0]
    idd = raw_cap["ID" + suf][:, :, k, 0]
    checked = 0
    ratios = []
    for i, L in enumerate(raw_cap["L"]):
        if L < 0.3e-6:
            continue
        slope = _bin(blocks, 5e-6, float(L))[5]["vth0"]
        for g in range(len(raw_cap["VGS"])):
            if idd[i, g] <= 0:
                continue
            gmid = gm[i, g] / idd[i, g]
            if not 5.0 <= gmid <= 15.0:
                continue
            try:
                r = mismatch_sigma_vgs(real_nm_memo, model, kind, 1000, float(L), float(raw_cap["VGS"][g]),
                                       float(raw_cap["VDS"][k]), 0.0, 5e-6, 5e-6)
            except SealViolationError:
                continue
            a_vt = math.sqrt(2) * dict(r.parts)["vth0"] * math.sqrt(5.0 * float(L) * 1e6)    # V·µm
            ratio = a_vt / (math.sqrt(2) * slope)
            ratios.append((ratio, float(L), gmid))
            checked += 1
    assert checked > 50
    bound = _vth0_ratio_bound(checked)
    # 판별력 전제: 틀린 bin slope(pfet 7.356/5.856 = 1.256 또는 역수)·단위 오류(10³ 배)는 이 상한 밖
    assert bound < min(abs(7.356 / 5.856 - 1.0), abs(5.856 / 7.356 - 1.0))
    for ratio, L, gmid in ratios:
        assert abs(ratio - 1.0) <= bound, (kind, L, gmid, ratio, bound)


def test_wb1_d3_slope_bin_by_finger_width_and_area_by_total_width(mm_lut):
    """[D-3] oracle (a) 손: W bin (1e-6, 3e-6) slope 1배, (3e-6, 7e-6) slope 2배, W_ref = 1e-6, DVGS = (1, 2, 2) mV.
    w_f = 2e-6, W = 8e-6: 기여 x (slope 1 / slope_ref)·√(1/8) -> σ = 3 mV/√8. w_f = 5e-6 (둘째 bin): 6 mV/√8. 총 폭 8e-6 로 bin 을 고르면 어느 bin 에도 없다(lut_mismatch_no_block)."""
    lo = _block("toy.1", wmin=1e-6, wmax=3e-6)
    hi = _block("toy.2", wmin=3e-6, wmax=7e-6, **{p: 2 * v for p, v in REF.items()})
    memo = new_memo(mm_lut)
    a = mismatch_sigma_vgs(memo, _model(lo, hi), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 2e-6, 8e-6)
    b = mismatch_sigma_vgs(memo, _model(lo, hi), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 5e-6, 8e-6)
    assert math.isclose(a.sigma_v, 3e-3 / math.sqrt(8.0), rel_tol=1e-12) and a.model == "toy.1"
    assert math.isclose(b.sigma_v, 6e-3 / math.sqrt(8.0), rel_tol=1e-12) and b.model == "toy.2"
    with pytest.raises(SealViolationError) as ei:
        mismatch_sigma_vgs(memo, _model(lo, hi), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 8e-6, 8e-6)
    assert detail_of(ei.value)["reason"] == "lut_mismatch_no_block"


@pytest.mark.parametrize("factor", [1 + 32 * 2.0 ** -52, 1 - 32 * 2.0 ** -52])
def test_wb1_b7_wmin_roundtrip_point_belongs_to_the_block(mm_lut, factor):
    """[B-7] oracle (a) 손: 격자 1e-8 에서 round(w / g) 정수 비교 -- 블록 W 하한 1e-6(= 정수 100)을 왕복 오차(+-32 eps) 점이 벗어나지 않는다.
    같은 입력의 원값(1e-6)과 같은 소속·같은 값이다."""
    memo = new_memo(mm_lut)
    ref = mismatch_sigma_vgs(memo, _model(_block(wmin=1e-6)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6, 1e-6)
    got = mismatch_sigma_vgs(memo, _model(_block(wmin=1e-6)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6 * factor, 1e-6)
    assert got.model == ref.model and math.isclose(got.sigma_v, ref.sigma_v, rel_tol=1e-12)

