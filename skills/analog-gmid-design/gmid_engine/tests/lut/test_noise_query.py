"""`noise_params` -- CONTRACT 9.3 [r7], 설계 41 §7.2 API `noise_params(kind, w_key, L, VGS, VDS, VS) -> NoiseParams{A, B, ef, b_status}`.

oracle:
- (a) 구성: ln A·ln B 가 모든 축에서 1차식인 합성 입력(Cgd = 0 -> 분해가 대수적으로 정확) -> 격자 밖 조회의 기대값은 닫힌 식
  (보간 = ln A·ln B 모든 축 선형이라 1차식을 정확히 재현).
- (c) 실데이터: 분해의 정의 S_vg(f) = A/f^EF + B 가 f_lo 점(A + B = S(1 Hz))과 B 를 읽은 주파수 점(그중 한 점에서 S_j 재현)에서 성립하는지를
  r1·기준 LUT 원본 배열(numpy 직접)로 확인 -- 어느 점을 골랐는지에 기대지 않는 관계.
"""
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import NoiseParams, noise_params

from .conftest import NoiseToy, TOY_SHAPE, detail_of, new_memo, toy_grid_mesh

A_LN = (math.log(1e-12), 1.0, 0.5, -1.0)        # ln A = c0 + c_v·v + c_d·d + c_s·s
B_LN = (math.log(1e-16), 0.5, 0.3, -0.4)


def _lin(c, v, d, s):
    return c[0] + c[1] * v + c[2] * d + c[3] * s


@pytest.fixture
def lin_toy(tmp_path):
    L, v, d, s = toy_grid_mesh()
    A = np.exp(_lin(A_LN, v, d, s))
    B = np.exp(_lin(B_LN, v, d, s))
    t = NoiseToy(tmp_path / "lin", A, B, cgd=0.0)
    return new_memo(t.load())


@pytest.mark.parametrize("pt", [(0.5, 0.5, 0.0), (0.25, 0.75, 0.25), (0.9, 0.6, 0.4), (1.0, 1.0, 0.5)])
def test_off_grid_is_loglinear_closed_form(lin_toy, pt):
    v, d, s = pt
    p = noise_params(lin_toy, "nmos", 100, 1e-6, v, d, s)
    assert isinstance(p, NoiseParams)
    assert p.b_status == "known"
    assert p.ef == 1.0 and p.w_m == pytest.approx(1e-6, rel=1e-15)
    assert math.isclose(p.A, math.exp(_lin(A_LN, v, d, s)), rel_tol=1e-9)
    assert math.isclose(p.B, math.exp(_lin(B_LN, v, d, s)), rel_tol=1e-9)


def test_unknown_corner_makes_B_none(tmp_path):
    """(a) VGS = 1.0 행만 B0 = 0(nonpositive) -> 그 행을 가중치로 쓰는 조회는 B = None·b_status 'nonpositive', 쓰지 않는 조회는 known.
    A 는 면의 값 그대로(9.3)."""
    L, v, d, s = toy_grid_mesh()
    A = np.exp(_lin(A_LN, v, d, s))
    B = np.where(v == 1.0, 0.0, np.exp(_lin(B_LN, v, d, s)))
    m = new_memo(NoiseToy(tmp_path / "u", A, B, cgd=0.0).load())
    p = noise_params(m, "nmos", 100, 1e-6, 0.75, 0.5, 0.0)
    assert p.B is None and p.b_status == "nonpositive"
    assert math.isclose(p.A, math.exp(_lin(A_LN, 0.75, 0.5, 0.0)), rel_tol=1e-9)
    q = noise_params(m, "nmos", 100, 1e-6, 0.25, 0.5, 0.0)
    assert q.b_status == "known" and q.B is not None


def test_no_point_corner_status(tmp_path):
    A = np.full(TOY_SHAPE, 1e-12)
    B = np.full(TOY_SHAPE, 1e-16)
    m = new_memo(NoiseToy(tmp_path / "np", A, B, cgd=2e-16).load())
    p = noise_params(m, "nmos", 100, 1e-6, 0.3, 0.6, 0.1)
    assert p.B is None and p.b_status == "no_feedthrough_free_point"


def test_other_width_rejected(lin_toy):
    with pytest.raises(SealViolationError) as ei:
        noise_params(lin_toy, "nmos", 200, 1e-6, 0.5, 0.5, 0.0)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_column_unavailable" and d["column"] == "SVG2" and d["w_key"] == 200


def test_no_noise_file_rejected(toy_memo):
    with pytest.raises(SealViolationError) as ei:
        noise_params(toy_memo, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_noise_unavailable"


@pytest.mark.parametrize("args,axis", [((1e-6, 0.5, 0.5, 0.6), "VS"), ((1e-6, 1.1, 0.5, 0.0), "VGS"),
                                       ((1e-6, 0.5, 0.4, 0.0), "VDS"), ((4e-6, 0.5, 0.5, 0.0), "L")])
def test_axis_out_of_range(lin_toy, args, axis):
    with pytest.raises(SealViolationError) as ei:
        noise_params(lin_toy, "nmos", 100, *args)
    d = detail_of(ei.value)
    assert d["reason"] == "lut_axis_out_of_range" and d["axis"] == axis


def test_non_anchor_L_on_empty_bin_map(tmp_path):
    """빈 bin 지도(bin 블록 없는 합성 모델 파일, [WB-1 §4]) 는 L 보간 없음(4.0) -> 비앵커 L 은 `lut_l_not_anchor`."""
    L, v, d, s = toy_grid_mesh()
    t = NoiseToy(tmp_path / "lin_empty", np.exp(_lin(A_LN, v, d, s)), np.exp(_lin(B_LN, v, d, s)), cgd=0.0, empty_bins=True)
    lin_empty = new_memo(t.load())
    noise_params(lin_empty, "nmos", 100, 1e-6, 0.5, 0.5, 0.0)                    # 호출 >= 1: 앵커는 된다
    with pytest.raises(SealViolationError) as ei:
        noise_params(lin_empty, "nmos", 100, 1.5e-6, 0.5, 0.5, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_l_not_anchor"


def test_memo_point_region(lin_toy):
    p1 = noise_params(lin_toy, "nmos", 100, 1e-6, 0.3, 0.6, 0.1)
    before = dict(lin_toy.stats())["point"]
    p2 = noise_params(lin_toy, "nmos", 100, 1e-6, 0.3, 0.6, 0.1)
    after = dict(lin_toy.stats())["point"]
    assert p2 is p1 and after.hits == before.hits + 1 and after.misses == before.misses


@pytest.mark.lut_realdata
def test_real_decomposition_reproduces_measured_spectrum(real_nm_memo, raw_cap, raw_noise):
    """(c) 실데이터 격자점 400개(seed 20261008, VGS index ≥ 8, VDS index ≥ 4): known 이면 A + B = S(1 Hz) 이고 B 를 읽은 점
    (f_hz 또는 100 MHz 중 하나)에서 A/f^EF + B = S_j(상대 1e-9); 미상이면 A = S(1 Hz)."""
    rng = np.random.default_rng(20261008)
    L, VGS, VDS, VS = (raw_cap[a] for a in ("L", "VGS", "VDS", "VS"))
    f_all = [float(x) for x in raw_noise["f_hz"]] + [1e8]
    for kind, suf in (("nmos", "_n"), ("pmos", "_p")):
        n_known = 0
        for _ in range(200):
            i, g, k, s = (int(rng.integers(len(L))), int(rng.integers(8, len(VGS))), int(rng.integers(4, len(VDS))),
                          int(rng.integers(len(VS))))
            p = noise_params(real_nm_memo, kind, 1000, float(L[i]), float(VGS[g]), float(VDS[k]), float(VS[s]))
            S_lo = float(raw_cap["SVG2_1HZ" + suf][i, g, k, s])
            S_f = [float(raw_noise["SVG2_F" + suf][j, i, g, k, s]) for j in range(len(f_all) - 1)]
            S_f.append(float(raw_cap["SVG2_HF" + suf][i, g, k, s]))
            if p.B is None:
                assert math.isclose(p.A, S_lo, rel_tol=1e-9), (kind, i, g, k, s)
                continue
            n_known += 1
            assert p.b_status == "known" and p.A > 0 and p.B > 0
            assert math.isclose(p.A + p.B, S_lo, rel_tol=1e-9)
            rec = min(abs(p.A / f ** p.ef + p.B - Sj) / Sj for f, Sj in zip(f_all, S_f))
            assert rec <= 1e-9, (kind, i, g, k, s, rec)
        assert n_known > 100


@pytest.mark.lut_realdata
def test_real_other_width_rejected(real_nm_memo):
    with pytest.raises(SealViolationError) as ei:
        noise_params(real_nm_memo, "nmos", 72, 1e-6, 0.9, 0.9, 0.0)
    assert detail_of(ei.value)["reason"] == "lut_column_unavailable"
