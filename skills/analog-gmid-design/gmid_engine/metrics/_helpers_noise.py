"""잡음 metric 공용 계산 -- 입력 환산 가중과 그 파라미터 미분 (설계 41 §7.3, 단위 U8).

`noise_analysis`(입력 환산 평탄값·corner·excess)와 `noise_integral`(폐루프 출력 적분)이 같이 쓴다.

* `weights(tr)`: W_k = |Z_k|²/|H|²(전달 뷰 H 가 없으면 |Z_k|²) -- 잡음원 k 의 단위 PSD 가 입력(또는 출력)에 기여하는 가중. 입력 환산 S_in = Σ_k W_k·S_k.
* `source_gradient(tr, coeff, sources)`: Q = Σ_k coeff_k·W_k 의 ∂Q/∂p (k=ω, P). ∂W_k/∂p = 2·Re(conj(Z_k)·∂Z_k)/|H|² − |Z_k|²·2·Re(conj(H)·∂H)/|H|⁴ 를 잡음원에 대해 먼저 합쳐
  (ω, 파라미터, 잡음원) 3차원 실수 중간 배열을 만들지 않는다. `tr` 의 `dz`·`dh`(`noise_transfer(parameters=)`)가 있어야 한다.
  coeff_k 가 잡음원 PSD(gm²·B 등)이면 S_k 가 gm_k 에 직접 의존하는 항 ∂S_k/∂gm_k = 2·S_k/gm_k 를 그 MOS 의 gm 파라미터 번호(`sources.gm_param`)에 더한다 --
  분해능 전파가 한 파라미터의 두 경로(회로 전달·잡음원 크기)를 부호째 합쳐 절댓값을 취하도록.
"""
import numpy


def weights(tr):
    power = numpy.abs(tr.z) ** 2
    return power if tr.h is None else power / (numpy.abs(tr.h) ** 2)[:, None]


def source_gradient(tr, coeff, sources):
    """`coeff` (k, N) 또는 (N,) -> (k, P)."""
    coeff = numpy.broadcast_to(numpy.asarray(coeff, dtype=float), tr.z.shape)
    grad = 2 * numpy.einsum("kpn,kn->kp", tr.dz, coeff * numpy.conj(tr.z)).real
    if tr.h is not None:
        h2 = numpy.abs(tr.h) ** 2
        total = (coeff * numpy.abs(tr.z) ** 2).sum(axis=1)
        grad = grad / h2[:, None] - (total / (h2 * h2))[:, None] * 2 * (numpy.conj(tr.h)[:, None] * tr.dh).real
    valid = (sources.gm_param >= 0) & (sources.gm > 0)
    if valid.any():
        direct = 2 * weights(tr)[:, valid] * coeff[:, valid] / sources.gm[valid]
        select = numpy.zeros((int(valid.sum()), grad.shape[1]))
        select[numpy.arange(select.shape[0]), sources.gm_param[valid]] = 1.0
        grad = grad + direct @ select
    return grad
