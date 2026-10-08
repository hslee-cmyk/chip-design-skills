"""잡음 분해 면 -- S_vg(f) = A/f^EF + B 의 A·B 를 (L, VGS, VDS, VS) 격자점마다 (설계 41 §7.2 분해 규칙, lut/CONTRACT.md 9.2).

진입점: `noise_planes`.

* S_vg(f_lo) 에서 flicker 가 지배하는 낮은 끝 점을 기준으로 한다(기준 LUT 의 `SVG2_1HZ`, f_lo = 1 Hz). 주파수 점 j(> lo) 마다 열잡음 평탄값 추정
  B_j = (S_j − S_lo·r_j) / (1 − r_j), r_j = (f_j/f_lo)^−EF 이고 A = (S_lo − B)·f_lo^EF (f_lo = 1 Hz 면 A = S_vg(1 Hz) − B).
* **B 를 읽는 점**: 점마다 아래 두 조건을 모두 만족하는 **가장 높은** 주파수 점 j.
  (1) **피드스루**: (2π·f_j·|Cgd|/gm)² ≤ 그 점의 허용오차 `tol_point`. Cgd·gm 은 같은 LUT 칸(`CapTable.CGD`·기준 LUT `GM` 열)에서 읽는다 -- 새 상수 없음.
  (2) **평탄(plateau)**: j 가 가장 낮은 이분 점이 아니면 |B_j − B_{j−1}| ≤ `tol_point`·|B_{j−1}| + (두 추정의 부동소수 반올림 허용분 eps·(|S_j| + |S_lo|·r_j)/|1 − r_j|)
      (열잡음 평탄값은 주파수와 무관해야 한다 -- 모델이 정확하면 flicker 가 지배하는
      낮은 주파수에서도 B_j 가 같다). 실측(2026-10-08 r1): 긴 L(20 µm)·약반전에서는 입력 환산 잡음이 Cgd 피드스루가 예측하는 것보다 훨씬 낮은 주파수에서 1차 저역 통과로
      떨어진다(L = 20 µm, gm/ID 25 점: B_j 가 1e4 Hz 까지 6.8e-14 인데 1e6 Hz 에서 9.4e-15 -- 피드스루 식은 6e-4). (1) 만으로는 이런 점의 B 를 86 % 낮게 읽는다.
      평탄 조건이 있으면 같은 점은 1e5 Hz(6 % 낮음)를 고른다.
  그런 점이 없으면 B 는 미상(`no_feedthrough_free_point`).
* 허용오차 `tol_point` = min(그 점의 ln S_vg(f_lo) 면 LOO 오차, 그 셀 `tol_a`); 점의 LOO 가 정의 안 되면(격자 가장자리) `tol_a`. `tol_a`(셀 (L 앵커, VDS)) = ln S_vg(f_lo) 면의
  leave-one-out(선형, 네 축; L 은 같은 bin 안 내부 앵커) 오차 ÷ 2^2 의 셀 안 최댓값 -- 잡음 면 자체의 보간 해상도다. 정의 안 되면 NaN -> 판정 근거 없음 = B 미상.
  (설계의 '그 칸의 tol' 보다 엄격한 쪽이다: 셀 최댓값은 몇 개 병적 점(VDS ≈ 0·VGS 끝)이 정해 셀 전체 허용오차를 부풀린다 -- 실측 아래. 점 허용오차 ≤ 셀 허용오차라 셀 허용오차 보증은 유지된다.
  B 의 주파수를 고르는 데 B 의 tol 을 쓸 수 없어(순환) flicker 면 tol 을 쓴다.)
* B ≤ 0 이거나 A ≤ 0 이면 `nonpositive`(미상으로 취급). 미상인 점은 A := S_vg(f_lo)·f_lo^EF(B 를 0 으로 둠), ln B = NaN.
"""
import math

import numpy as np

from ._helpers_loo import l_interior, linear_loo_cells
from .lut_types import AXES, NOISE_B_STATUS, NoisePlanes

STATUS_KNOWN, STATUS_NO_POINT, STATUS_NONPOSITIVE = range(len(NOISE_B_STATUS))


def noise_planes(memo, kind):
    """kind 의 `NoisePlanes`. memo 영역 derived(디스크 캐시 대상). 잡음 r1 파일이 없는 LutSet -> `KeyError`."""
    table = memo.lut.noise[kind]
    cap = memo.lut.cap_map[kind]
    gm, cgd = cap.columns["GM"], cap.CGD

    def compute():
        f = np.asarray(table.freqs, dtype=float)
        s = np.asarray(table.S, dtype=float)
        lo = s[0]
        valid = lo > 0
        ln_lo = np.where(valid, np.log(np.where(valid, lo, 1.0)), np.nan)
        interior = l_interior(table.l_bins, len(table.grids[0]))
        tol_a = linear_loo_cells(ln_lo, table.grids, interior)
        tol_pt = linear_loo_cells(ln_lo, table.grids, interior, per_point=True)
        tol_cell = np.broadcast_to(tol_a[:, None, :, None], lo.shape)
        tol = np.where(np.isfinite(tol_pt), np.minimum(tol_pt, tol_cell), tol_cell)
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            feed = (math.tau * np.abs(cgd) / np.where(gm > 0, gm, np.nan)) ** 2
            ratio = [(f[j] / f[0]) ** -table.ef for j in range(1, len(f))]
            b_j = [None] + [(s[j] - lo * ratio[j - 1]) / (1 - ratio[j - 1]) for j in range(1, len(f))]
            eps = np.finfo(float).eps
            slack = [None] + [eps * (np.abs(s[j]) + np.abs(lo) * ratio[j - 1]) / np.abs(1 - ratio[j - 1]) for j in range(1, len(f))]
            chosen = np.full(lo.shape, -1)
            b_at = np.full(lo.shape, np.nan)
            for j in reversed(range(1, len(f))):
                ok = valid & (feed * f[j] ** 2 <= tol)
                if j > 1:
                    ok = ok & (np.abs(b_j[j] - b_j[j - 1]) <= tol * np.abs(b_j[j - 1]) + slack[j] + slack[j - 1])
                take = (chosen < 0) & ok
                chosen = np.where(take, j, chosen)
                b_at = np.where(take, b_j[j], b_at)
            a_known = (lo - b_at) * f[0] ** table.ef
            known = (chosen >= 0) & (b_at > 0) & (a_known > 0)
            status = np.where(chosen < 0, STATUS_NO_POINT, np.where(known, STATUS_KNOWN, STATUS_NONPOSITIVE))
            a_val = np.where(known, a_known, lo * f[0] ** table.ef)
            ln_a = np.where(a_val > 0, np.log(np.where(a_val > 0, a_val, 1.0)), np.nan)
            ln_b = np.where(known, np.log(np.where(known, b_at, 1.0)), np.nan)
        planes = (ln_a, ln_b, status.astype(np.int8), tol_a, np.where(known, ln_b, 0.0),
                  (status == STATUS_NO_POINT).astype(float), (status == STATUS_NONPOSITIVE).astype(float), tol)
        for arr in planes:
            arr.setflags(write=False)
        return NoisePlanes(kind, *planes)

    return memo.lookup_persistent("derived", "noise_planes", (kind,), compute, (table, gm, cgd),
                                  (AXES, NOISE_B_STATUS))
