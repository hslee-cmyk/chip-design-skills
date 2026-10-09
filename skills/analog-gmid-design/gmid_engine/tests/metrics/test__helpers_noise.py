"""[U8 2026-10-09] `metrics/_helpers_noise` -- `weights`(W_k = |Z_k|²/|H|²)·`source_gradient`(∂Q/∂p, Q = Σ_k coeff_k·W_k) (metrics CONTRACT 10.0·10.2).

oracle:
* (a) 구성한 합성 입력: Z_k(p) = Z_k + ∂Z_k·p, H(p) = H + ∂H·p(1차식으로 정한 전달)와 잡음원 크기 coeff_k(p) = coeff_k·((gm_k + p)/gm_k)²(그 MOS 의 gm 파라미터일 때 --
  S_k = gm²·B 의 gm 직접 의존, 계약 10.2). Q(p) 를 test 가 직접 계산해 중앙 차분과 비교한다.
* (a) H 가 없으면 W = |Z|²(폐루프·출력 잡음, 계약 10.1).
"""
import numpy as np

from gmid_engine.metrics import NoiseSources, NoiseTransfer
from gmid_engine.metrics._helpers_noise import source_gradient, weights

RNG = np.random.default_rng(20261009)
K, P, N = 3, 4, 5
FD = 1e-6


def _cplx(*shape):
    return RNG.normal(size=shape) + 1j * RNG.normal(size=shape)


Z, H = _cplx(K, N), _cplx(K) + 3.0
DZ, DH = _cplx(K, P, N), _cplx(K, P)
GM = np.array([1e-3, 2e-4, 0.0, 5e-4, 0.0])
GM_PARAM = np.array([0, 2, -1, 3, -1])          # 원소 0·1·3 은 MOS(gm 파라미터 0·2·3), 2·4 는 저항(파라미터 없음)
COEFF = np.abs(RNG.normal(size=(K, N))) * 1e-20


def _sources():
    n = np.arange(N)
    return NoiseSources(tuple("e%d" % i for i in n), GM > 0, n, n, COEFF[0], np.zeros(N), np.ones(N), np.zeros(N), np.zeros(N),
                        GM, GM_PARAM)


def _q(k, p, step, with_h=True):
    z = Z[k] + DZ[k, p] * step
    coeff = COEFF[k].copy()
    hit = GM_PARAM == p
    coeff[hit] *= ((GM[hit] + step) / GM[hit]) ** 2
    h2 = abs(H[k] + DH[k, p] * step) ** 2 if with_h else 1.0
    return float((coeff * np.abs(z) ** 2).sum() / h2)


def test_weights_with_and_without_view():
    tr = NoiseTransfer(np.ones(K), z=Z, h=H)
    np.testing.assert_allclose(weights(tr), np.abs(Z) ** 2 / (np.abs(H) ** 2)[:, None], rtol=1e-14)
    tr0 = NoiseTransfer(np.ones(K), z=Z, h=None)
    np.testing.assert_allclose(weights(tr0), np.abs(Z) ** 2, rtol=1e-14)


def test_source_gradient_matches_central_difference_with_view():
    tr = NoiseTransfer(np.ones(K), z=Z, h=H, dz=DZ, dh=DH)
    g = source_gradient(tr, COEFF, _sources())
    assert g.shape == (K, P)
    for k in range(K):
        for p in range(P):
            fd = (_q(k, p, FD * 1e-3) - _q(k, p, -FD * 1e-3)) / (2 * FD * 1e-3)
            assert abs(g[k, p] - fd) <= 1e-5 * max(abs(fd), 1e-22), (k, p, g[k, p], fd)


def test_source_gradient_without_view():
    tr = NoiseTransfer(np.ones(K), z=Z, h=None, dz=DZ, dh=None)
    g = source_gradient(tr, COEFF, _sources())
    for k in range(K):
        for p in range(P):
            fd = (_q(k, p, FD * 1e-3, False) - _q(k, p, -FD * 1e-3, False)) / (2 * FD * 1e-3)
            assert abs(g[k, p] - fd) <= 1e-5 * max(abs(fd), 1e-22)


def test_source_gradient_broadcasts_one_dimensional_coeff():
    """coeff (N,) 는 모든 ω 행에 같은 값(계약: '(k, N) 또는 (N,)') -- (k, N) 로 펼친 것과 같다."""
    tr = NoiseTransfer(np.ones(K), z=Z, h=H, dz=DZ, dh=DH)
    flat = COEFF[0]
    np.testing.assert_allclose(source_gradient(tr, flat, _sources()),
                               source_gradient(tr, np.broadcast_to(flat, (K, N)), _sources()), rtol=1e-14)
