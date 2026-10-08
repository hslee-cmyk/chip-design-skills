"""소자 하나의 게이트 환산 mismatch σ -- LUT 감도 열 DVGS_k × PDK bin slope × 기하 환산 (설계 41 §6.4-2, lut/CONTRACT.md 10.4).

진입점: `mismatch_sigma_vgs`.

  σ_VGS(W, L, 점) = √(Σ_k (DVGS_k(L, 점) · slope_k(bin(W, L)) / slope_k(bin_ref)))² · √(W_ref / W)

* DVGS_k·slope_ref = `mismatch_dvgs`(기준 폭 W_ref = `MismatchSens.w_m`, 그 L 의 bin_ref 에서 잰 1σ 감도 -- 1σ 는 인스턴스 기하의 1σ 라 이미 1/√(W_ref·L) 를 품는다).
* slope_k(bin(W, L)) = PDK 선언의 mismatch 모델(`core.PdkMismatchModel`: `.model` 블록마다 변수별 slope)에서 소자 폭 W·길이 L 이 든 블록의 값 -- W bin 을 먼저,
  그 안에서 L bin 을 `bin_index` 규칙(양끝 닫힘, 경계 공유 시 아래 bin)으로 고른다. 블록이 변수를 안 쓰면 slope 0.
* 기하: 감도는 √(W_ref·L)/√(W·L) 로 환산한다(같은 L 이라 √(W_ref/W)). `W` = 모델 카드에 넘기는 인스턴스 폭 `w`(m) -- 카드의 sqrt(l·w·mult) 가 읽는 값.
* 쌍의 σ(ΔVGS) 는 √2·σ_VGS, A_eff = σ_쌍·√(W·L) 이고 읽는 쪽이 계산한다(열로 저장하지 않는다).
* 기준 bin 이 변수를 안 쓰는데(slope_ref 0) 소자 bin 은 쓰면(slope ≠ 0) 감도를 환산할 수 없어 실패한다(`lut_mismatch_slope_unscalable`).
* 실패(`SealViolationError`): `mismatch_dvgs` 사유, 소자 (W, L) 을 품는 블록 없음 `lut_mismatch_no_block`, 위 환산 불가 사유. `W <= 0` -> `ValueError`.
"""
import math

from ._helpers_bins import bin_index
from ._helpers_fail import seal_violation
from .lut_types import MismatchSigma
from .mismatch_query import mismatch_dvgs


def _block_of(model, W, L):
    """모델 블록 중 폭 W·길이 L 을 품는 것(W bin 우선, 그 안 L bin), 없으면 None."""
    w_rows = sorted({(b.wmin_m, b.wmax_m) for b in model.blocks})
    j = bin_index(w_rows, W)
    if j is None:
        return None
    row = sorted((b for b in model.blocks if (b.wmin_m, b.wmax_m) == w_rows[j]), key=lambda b: (b.lmin_m, b.lmax_m, b.model))
    i = bin_index([(b.lmin_m, b.lmax_m) for b in row], L)
    return None if i is None else row[i]


def mismatch_sigma_vgs(memo, model, kind, w_key, L, vgs, vds, vsb, W):
    """폭 `W`(m)·길이 `L`(m) 소자의 `MismatchSigma`(σ_VGS V, 변수별 기여 V). `model` = `core.PdkMismatchModel`(kind 의 것). memo 영역 point."""
    W = float(W)
    if not W > 0:
        raise ValueError("mismatch_sigma_vgs: W 는 양수여야 한다")
    L = float(L)
    sens = mismatch_dvgs(memo, kind, w_key, L, vgs, vds, vsb)
    block = _block_of(model, W, L)
    detail = dict(kind=kind, w_key=w_key, W=W, L=L)
    if block is None:
        raise seal_violation("lut_mismatch_no_block", **detail)
    actual = {param: (0.0 if value is None else value) for param, _ident, value, _line in block.slopes}

    def compute():
        parts = []
        for param, dvgs in sens.dvgs.items():
            ref, now = sens.slope_ref[param], actual.get(param, 0.0)
            if now == 0.0:
                parts.append((param, 0.0))
            elif ref == 0.0:
                raise seal_violation("lut_mismatch_slope_unscalable", parameter=param, slope_ref=ref, slope=now, **detail)
            else:
                parts.append((param, abs(dvgs) * now / ref))
        scale = math.sqrt(sens.w_m / W)
        return MismatchSigma(scale * math.sqrt(sum(v * v for _p, v in parts)), tuple((p, scale * v) for p, v in parts), block.model)

    return memo.lookup("point", "mismatch_sigma_vgs", (kind, w_key, L, float(vgs), float(vds), float(vsb), W, block.model), compute)
