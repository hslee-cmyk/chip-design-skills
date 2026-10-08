"""`noise_planes` -- CONTRACT 9.2 [r7], 설계 41 §7.2 '분해 규칙'(S_vg = A/f^EF + B, B 는 피드스루 오차 (ωCgd/gm)² 가 tol 이하인
가장 높은 주파수 점에서, 없으면 '미상').

oracle 은 모두 (a) 구성(합성 입력의 물리 모형): 측정값 S_vg(f) = A0/f^EF + B0/(1 + (2πf·Cgd/gm)²) 를 conftest `NoiseToy` 가 만든다.
피드스루가 있는 점에서 열잡음 평탄값을 읽으면 그 점의 깎인 값 B0·g(f), g(f) = 1/(1 + (2πf·Cgd/gm)²) 이 나와야 하고, flicker 분리의
치우침은 |g(f) − g(f_lo)|/(f/f_lo − 1) 이하다(EF = 1: (f·g_j − g_lo)/(f − 1) = g_j + (g_j − g_lo)/(f − 1) -- 물리 모형의 대수,
피검 식이 아니라 측정 모형에서 유도). 그래서 '어느 주파수 점을 골랐는가' 가 B 값으로 관찰된다.
"""
import math

import numpy as np
import pytest

from gmid_engine.lut import NOISE_B_STATUS, NoisePlanes, noise_planes

from .conftest import NOISE_F_LO, NoiseToy, TOY_SHAPE, new_memo, toy_grid_mesh

CGD_SEL = 1e-7          # toy 피드스루: x(f) = 2π f·Cgd/gm, gm = 1e-3 -> x² = 3.9e-5 (10 Hz), 3.9e-3 (100 Hz), 0.39 (1 kHz), 39 (10 kHz)
GM = 1e-3


def g_ft(f, cgd=CGD_SEL, gm=GM):
    return 1.0 / (1.0 + (2 * math.pi * f * cgd / gm) ** 2)


def _quad_flicker_toy(tmp_path, cgd, B0=1e-19, sub="q"):
    """ln A 가 VGS 의 2차식(ln A = ln 1e-12 + v²) -> ln S(f_lo) 면의 VGS LOO(선형, 간격 0.5) 오차 = h² = 0.25, ÷ 2² = 0.0625
    (CONTRACT 9.2 tol_a). 다른 축은 2점이라 내부점 없음, toy 는 bin 지도가 비어 L LOO 없음. B0 ≪ A 라 ln(A + B) 의 섭동 ≤ 1.7e-7."""
    L, v, d, s = toy_grid_mesh()
    A = 1e-12 * np.exp(v * v)
    B = np.full(TOY_SHAPE, B0)
    return NoiseToy(tmp_path / sub, A, B, cgd=cgd, gm=GM), A, B


def test_status_vocabulary():
    assert NOISE_B_STATUS == ("known", "no_feedthrough_free_point", "nonpositive")


def test_exact_spectrum_reads_B0_and_A0(tmp_path):
    """CONTRACT 9.6 첫 줄: CGD = 0 -> 모든 점 known, B = B0, A = A0(대수적으로 정확)."""
    t, A, B = _quad_flicker_toy(tmp_path, cgd=0.0, B0=1e-16)
    P = noise_planes(new_memo(t.load()), "nmos")
    assert isinstance(P, NoisePlanes)
    st = np.asarray(P.status)
    assert st.shape == TOY_SHAPE
    assert set(np.unique(st).tolist()) <= {0, "known"} and (st == st.flat[0]).all()
    assert np.allclose(np.exp(np.asarray(P.ln_b)), B, rtol=1e-9, atol=0)
    assert np.allclose(np.exp(np.asarray(P.ln_a)), A, rtol=1e-9, atol=0)


def test_tol_a_is_quarter_of_linear_loo(tmp_path):
    """(a) tol_a[L, VDS] = 0.25/4 = 0.0625 (모든 셀에 VGS 내부점이 있다). 섭동 상한 2·max(B/A)/4 ≤ 1e-7."""
    t, A, B = _quad_flicker_toy(tmp_path, cgd=0.0)
    P = noise_planes(new_memo(t.load()), "nmos")
    tol_a = np.asarray(P.tol_a)
    assert tol_a.shape == (TOY_SHAPE[0], TOY_SHAPE[2])
    assert np.all(np.abs(tol_a - 0.0625) <= 1e-7)


def test_feedthrough_picks_highest_admissible_point(tmp_path):
    """(a) tol ≈ 0.0625: 피드스루 x² 는 10 Hz·100 Hz 에서 통과, 1 kHz(0.39)·10 kHz(39) 에서 탈락 -> 100 Hz 점의 B.
    기대 B/B0 = g(100) (치우침 ≤ |g(100) − g(1)|/99 = 4e-5). 10 Hz 를 골랐다면 g(10) ≈ 0.99996 -- 차 3.9e-3 이라 구별된다.
    1 kHz 를 골랐다면 0.72 근처."""
    t, A, B = _quad_flicker_toy(tmp_path, cgd=CGD_SEL)
    P = noise_planes(new_memo(t.load()), "nmos")
    st = np.asarray(P.status)
    b = np.exp(np.asarray(P.ln_b)) / B
    bias = abs(g_ft(100.0) - g_ft(NOISE_F_LO)) / (100.0 - 1.0)
    assert np.all(np.abs(b - g_ft(100.0)) <= bias + 1e-12)
    assert np.all(np.abs(b - g_ft(10.0)) > 10 * bias)
    # A = (S_lo − B)·f_lo^EF = A0 + B0·g(f_lo) − B -> A0 와 상대 B0/A0 수준
    assert np.allclose(np.exp(np.asarray(P.ln_a)), A, rtol=1e-6, atol=0)
    assert (st == st.flat[0]).all()


def test_no_admissible_point_is_unknown(tmp_path):
    """CONTRACT 9.6 둘째 줄: 면이 모든 점에서 같으면 LOO = 0 -> 허용오차 0, CGD > 0 이면 모든 점 탈락 ->
    `no_feedthrough_free_point`, ln B = NaN, A = S_lo·f_lo^EF = A0 + B0 (설계 41 §7.2 '조건을 만족하는 점이 없으면 B 는 미상')."""
    A = np.full(TOY_SHAPE, 1e-12)
    B = np.full(TOY_SHAPE, 1e-16)
    t = NoiseToy(tmp_path / "u", A, B, cgd=2e-16, gm=GM)
    P = noise_planes(new_memo(t.load()), "nmos")
    assert np.all(np.isnan(np.asarray(P.ln_b)))
    assert np.asarray(P.flag_no_point).all()
    S_lo = A + B / (1 + (2 * math.pi * 1.0 * 2e-16 / GM) ** 2)
    assert np.allclose(np.exp(np.asarray(P.ln_a)), S_lo, rtol=1e-12, atol=0)


def test_zero_thermal_floor_is_nonpositive(tmp_path):
    """(a) B0 = 0 (순수 1/f): 모든 이분 점 B_j = 0 -> B ≤ 0 -> `nonpositive`(CONTRACT 9.2 상태), A = S_lo."""
    L, v, d, s = toy_grid_mesh()
    A = 1e-12 * np.exp(v)
    t = NoiseToy(tmp_path / "z", A, np.zeros(TOY_SHAPE), cgd=0.0)
    P = noise_planes(new_memo(t.load()), "nmos")
    assert np.asarray(P.flag_nonpositive).all()
    assert np.all(np.isnan(np.asarray(P.ln_b)))
    assert np.allclose(np.exp(np.asarray(P.ln_a)), A, rtol=1e-12, atol=0)


FC_LP = 700.0           # 저역 통과 모사의 꺾임 주파수: h(f) = 1/(1 + (f/fc)²) -> h(10) 0.9998, h(100) 0.980, h(1e3) 0.329, h(1e4) 0.0049


def h_lp(f):
    return 1.0 / (1.0 + (f / FC_LP) ** 2)


def test_plateau_break_rejects_point(tmp_path):
    """CONTRACT 9.2 (2) 평탄 조건 -- [r7] **설계 41 §7.2 밖 추가**(사용자 승인 대상으로 보고). 피드스루는 0(Cgd = 0) 인데 입력 환산
    열잡음이 1차 저역 통과로 떨어지는 입력(계약이 근거로 든 긴 L·약반전 실측의 모사): S(f) = A0/f + B0·h(f).
    - 계약(평탄 조건): 10 kHz(vs 1 kHz 98 % 차)·1 kHz(vs 100 Hz 66 %) 탈락, 100 Hz(vs 10 Hz 2 % ≤ tol 0.0625) 통과 -> B/B0 = h(100)
      (+ flicker 분리 치우침 ≤ |h(100) − h(1)|/99).
    - 설계 문구만(피드스루 조건만)이면 가장 높은 10 kHz 의 B ≈ 0.0049·B0 를 읽는다 -- 이 test 는 계약 쪽을 고정한다."""
    L, v, d, s = toy_grid_mesh()
    A = 1e-12 * np.exp(v * v)
    B = np.full(TOY_SHAPE, 1e-19)
    from .conftest import NOISE_F_MID

    def lp(arr):
        arr["SVG2_F_n"] = np.stack([A / f + B * h_lp(f) for f in NOISE_F_MID])
    t2 = NoiseToy(tmp_path / "p", A, B, cgd=0.0, gm=GM, noise_mutate=lp,
                  cap_mutate=lambda c: c.update(SVG2_HF_n=A / 1e4 + B * h_lp(1e4), SVG2_1HZ_n=A + B * h_lp(1.0)))
    P = noise_planes(new_memo(t2.load()), "nmos")
    b = np.exp(np.asarray(P.ln_b)) / B
    bias = abs(h_lp(100.0) - h_lp(1.0)) / 99.0
    assert np.all(np.abs(b - h_lp(100.0)) <= bias + 1e-9)


def test_plateau_rule_only_compares_adjacent_points(tmp_path):
    """[r7 평탄 조건의 한계 -- 보고용 기록] 열잡음이 1 kHz 부터 반으로 떨어진 뒤 평탄하면(계단) 10 kHz 와 1 kHz 가 서로 평탄해
    10 kHz 의 B ≈ 0.5·B0 를 읽는다(계약 9.2 (2) 는 바로 아래 이웃만 비교). 계약 문장 그대로의 동작이라 통과가 기대값이고,
    값이 절반으로 틀리는 경로가 남는다는 사실을 고정한다(설계 문구만 따라도 같은 값)."""
    L, v, d, s = toy_grid_mesh()
    A = 1e-12 * np.exp(v * v)
    B = np.full(TOY_SHAPE, 1e-19)

    def halve(arr):
        arr["SVG2_F_n"][2] = A / 1000.0 + 0.5 * B
    t2 = NoiseToy(tmp_path / "s", A, B, cgd=0.0, gm=GM, noise_mutate=halve,
                  cap_mutate=lambda c: c.update(SVG2_HF_n=A / 1e4 + 0.5 * B))
    P = noise_planes(new_memo(t2.load()), "nmos")
    b = np.exp(np.asarray(P.ln_b)) / B
    # (0.5 − 1/1e4)/(1 − 1/1e4): EF = 1 분리에서 S_lo 의 B0 몫이 r_j 만큼 빠진 값(측정 모형 대수)
    assert np.allclose(b, (0.5 - 1e-4) / (1 - 1e-4), rtol=1e-9, atol=0)


def test_missing_noise_is_keyerror(tmp_path, toy_build):
    lut = toy_build("plain").load()
    with pytest.raises(KeyError):
        noise_planes(new_memo(lut), "nmos")


def test_memo_derived_second_call_hits(tmp_path):
    t, _, _ = _quad_flicker_toy(tmp_path, cgd=0.0)
    m = new_memo(t.load())
    p1 = noise_planes(m, "nmos")
    before = dict(m.stats())["derived"]
    p2 = noise_planes(m, "nmos")
    after = dict(m.stats())["derived"]
    assert p2 is p1
    assert after.hits == before.hits + 1 and after.misses == before.misses


@pytest.mark.lut_realdata
def test_real_known_fraction_and_status_partition(real_nm_memo, raw_cap):
    """(c) 실데이터: 상태 코드(NOISE_B_STATUS 의 index)와 보조 플래그(0/1)가 일치하고, known 점에서만 ln B 가 유한(정의)."""
    for kind in ("nmos", "pmos"):
        P = noise_planes(real_nm_memo, kind)
        st = np.asarray(P.status)
        no_pt = np.asarray(P.flag_no_point) != 0
        nonpos = np.asarray(P.flag_nonpositive) != 0
        lnb = np.asarray(P.ln_b)
        assert set(np.unique(st).tolist()) <= {0, 1, 2}
        assert np.array_equal(no_pt, st == NOISE_B_STATUS.index("no_feedthrough_free_point"))
        assert np.array_equal(nonpos, st == NOISE_B_STATUS.index("nonpositive"))
        known = st == NOISE_B_STATUS.index("known")
        assert np.all(np.isfinite(lnb[known]))
        assert np.all(np.isnan(lnb[~known]))
        assert known.mean() > 0.5, (kind, known.mean())
