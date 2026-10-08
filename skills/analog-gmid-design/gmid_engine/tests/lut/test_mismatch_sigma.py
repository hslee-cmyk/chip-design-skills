"""`mismatch_sigma_vgs` -- CONTRACT 10.4 [r7], 설계 41 §6.4-2 'mismatch 모델(옛 식 대체)':
σ_VGS(W, L, 점) = √(Σ_k (DVGS_k · slope_k(bin(W, L)) / slope_k(bin_ref))²) · √(W_ref·L)/√(W·L).

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
    return PdkMismatchModel("nmos", ("toxe", "voff", "vth0"), tuple(blocks), "toy.pm3", "0" * 64, "toy.mm", "0" * 64)


@pytest.fixture
def mm_lut(tmp_path):
    t = MismatchToy(tmp_path / "m", {p: np.full(TOY_SHAPE, v) for p, v in DV.items()}, slope_ref=REF)
    return t.load()


def test_hand_calc_reference_width(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert isinstance(r, MismatchSigma)
    assert math.isclose(r.sigma_v, 3e-3, rel_tol=1e-12)             # √(1 + 4 + 4) mV
    assert dict(r.parts) == pytest.approx(DV, rel=1e-12)
    assert r.model == "toy_model.1"


def test_hand_calc_four_times_width(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 4e-6)
    assert math.isclose(r.sigma_v, 1.5e-3, rel_tol=1e-12)           # √(W_ref/W) = 1/2


def test_hand_calc_device_bin_slope_twice(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block(toxe=4e-3)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert math.isclose(r.sigma_v, math.sqrt(1 + 16 + 4) * 1e-3, rel_tol=1e-12)


def test_hand_calc_variable_unused_in_device_bin(mm_lut):
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(_block(voff=None)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert math.isclose(r.sigma_v, math.sqrt(5) * 1e-3, rel_tol=1e-12)


def test_memo_key_distinguishes_pdk_model(mm_lut):
    """[RED 예상 -- 결함 보고] 같은 memo 에서 PDK mismatch 모델만 다른 두 호출은 다른 값이어야 한다(10.4 식의 slope_k(bin(W, L)) 는
    model 인자에서 온다). memo 키가 model 을 빼면 두 번째 호출이 첫 호출 값을 돌려준다 -- 같은 LUT 로 다른 PDK 선언(slope 정정)을
    쓰면 조용히 옛 값이 나온다."""
    m = new_memo(mm_lut)
    a = mismatch_sigma_vgs(m, _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    b = mismatch_sigma_vgs(m, _model(_block(toxe=4e-3)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert math.isclose(a.sigma_v, 3e-3, rel_tol=1e-12)
    assert math.isclose(b.sigma_v, math.sqrt(21) * 1e-3, rel_tol=1e-12)


def test_no_block_rejected(mm_lut):
    with pytest.raises(SealViolationError) as ei:
        mismatch_sigma_vgs(new_memo(mm_lut), _model(_block(lmin=2e-6)), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert detail_of(ei.value)["reason"] == "lut_mismatch_no_block"


def test_unscalable_slope_rejected(tmp_path):
    """기준 bin 이 voff 를 안 쓰는데(slope_ref 0) 소자 bin 은 쓰면 비율이 정의되지 않는다 -> `lut_mismatch_slope_unscalable`."""
    t = MismatchToy(tmp_path / "u", {p: np.full(TOY_SHAPE, v) for p, v in DV.items()}, slope_ref=dict(REF, voff=None))
    with pytest.raises(SealViolationError) as ei:
        mismatch_sigma_vgs(new_memo(t.load()), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
    assert detail_of(ei.value)["reason"] == "lut_mismatch_slope_unscalable"


@pytest.mark.parametrize("W", [0.0, -1e-6])
def test_nonpositive_width(mm_lut, W):
    with pytest.raises(ValueError):
        mismatch_sigma_vgs(new_memo(mm_lut), _model(_block()), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, W)


def test_bin_boundary_belongs_to_lower_block(mm_lut):
    """bin 규칙(CONTRACT 4.0.1): L 이 두 블록이 공유한 경계값이면 아래 블록. 아래 블록 toxe slope 2배 -> √21 mV."""
    lo = _block("low", lmin=0.5e-6, lmax=1e-6, toxe=4e-3)
    hi = _block("high", lmin=1e-6, lmax=5e-6)
    r = mismatch_sigma_vgs(new_memo(mm_lut), _model(lo, hi), "nmos", 100, 1e-6, 0.5, 0.5, 0.0, 1e-6)
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
                           float(raw_cap["VGS"][g]), float(raw_cap["VDS"][k]), 0.0, W)
    assert r.model.lower() == b_dev[0].lower()
    parts = dict(r.parts)
    for p in ("vth0", "toxe", "voff"):
        d = abs(float(raw_mismatch["DVGS_%s_n" % p][i, g, k, 0]))
        exp = d * (b_dev[5][p] / b_ref[5][p]) * math.sqrt(5e-6 / W)
        assert math.isclose(parts[p], exp, rel_tol=1e-12), p
    assert math.isclose(r.sigma_v, math.sqrt(sum(v * v for v in parts.values())), rel_tol=1e-12)


@pytest.mark.lut_realdata
@pytest.mark.parametrize("kind,dev", [("nmos", "nfet_01v8"), ("pmos", "pfet_01v8")])
def test_real_vth0_component_equals_sqrt2_slope(real_nm_memo, real_pdk_decl, real_paths, raw_cap, kind, dev):
    """설계 41 §6.4-2: 'LUT 감도 열의 vth0 성분은 √2·slope(bin별) 과 같아야 한다'. 쌍 A_VT 성분 = √2·parts[vth0]·√(W·L[µm²]).
    판정(test 기준): W = 5 µm, L 앵커 ≥ 0.3 µm, |VDS| 0.9 V, VS 0, 격자 gm/ID 5~15 점에서 비 A_VT/(√2·slope) 가 1 ± 0.05.
    - 0.05 의 근거: bin slope 를 잘못 고르면 비가 pfet 7.356/5.856 = 1.256(또는 그 역수), 단위(µm↔m) 오류면 10³ 배라 둘 다 밖이다.
      짧은 채널(L < 0.3 µm)은 같은 ID 의 ΔVGS 가 ΔVT 와 다른 물리 효과가 커 이 판정에서 뺀다(계약 10.6 의 pfet 0.18 µm 9.71 대 10.40)."""
    blocks = _parse_card(real_paths["pdk_root"], dev)
    model = real_pdk_decl.mismatch_model(kind)
    suf = "_n" if kind == "nmos" else "_p"
    k = int(np.argmin(np.abs(raw_cap["VDS"] - 0.9)))
    gm = raw_cap["GM" + suf][:, :, k, 0]
    idd = raw_cap["ID" + suf][:, :, k, 0]
    checked = 0
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
                                       float(raw_cap["VDS"][k]), 0.0, 5e-6)
            except SealViolationError:
                continue
            a_vt = math.sqrt(2) * dict(r.parts)["vth0"] * math.sqrt(5.0 * float(L) * 1e6)    # V·µm
            ratio = a_vt / (math.sqrt(2) * slope)
            assert abs(ratio - 1.0) <= 0.05, (kind, float(L), gmid, ratio)
            checked += 1
    assert checked > 50
