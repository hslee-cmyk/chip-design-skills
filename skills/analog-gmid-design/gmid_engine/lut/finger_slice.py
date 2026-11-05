"""레이아웃 전 소자의 실현 손가락 기하 (m, w_s) 선택 -- LUT 슬라이스 위에서 고른다 (WB-1 DC 블록, 설계 40 §3.7-A 5, interface §2).

진입점: `finger_slice`.

* `reachable_slices(lut, kind, L)`: 도달 가능한 슬라이스 키 오름차순 tuple. w_hi = 기준 폭 슬라이스(`cap_map[kind].w_key`)의 W bin 위 끝(`l_bins.w_bin[1]`, J-7),
  L 은 그 슬라이스 L bin 안 소속 검사(`bin_index`, 선언 규칙 `lut.bin_rule`)만 한다. 기준 키 None·기준 슬라이스 없음·bin 지도 비었음·L 을 품는 bin 없음 -> `()`.
  아니면 `round(W_min/g) <= 키 <= round(w_hi/g)`(격자 정수 비교).
* `finger_slice(lut, kind, L, w_of)`: 후보 키마다 `w_of(키)` = 그 슬라이스에서의 총 폭 W(m)를 부르고(None·비유한·<= 0 이면 그 키를 뺀다), x = W/(키·g),
  k = floor(x), k = 0 이면 m = 1, 아니면 x − k <= k + 1 − x 일 때 m = k 아니면 k + 1. 잔차 = |(m·키)·g/W − 1|, 최소 잔차(동률은 큰 키). 저장 0, graph 읽지 않음.
  `w_of` 가 던지는 예외는 그대로 올린다. 실패 `SealViolationError`(reason `slice_missing`, detail `kind`, `L`, `why` ∈ {`no_w_hi`, `no_candidate`}, `excluded`).
* `lut` = `LutSet`(읽는 칸: `spec.manufacturing_grid_m`, `spec.min_finger_w_m`, `slice_map`, `cap_map[kind].w_key`, `bin_rule`).
"""
import dataclasses
import math

from ._helpers_bins import bin_index
from ._helpers_fail import seal_violation

REASON_SLICE_MISSING = "slice_missing"
WHY_NO_W_HI = "no_w_hi"
WHY_NO_CANDIDATE = "no_candidate"


@dataclasses.dataclass(frozen=True)
class FingerSlice:
    """선택 결과: 손가락 수 `m`, 슬라이스 폭 `w_f_m`(= 키·g), 슬라이스 키 `w_key`."""

    m: int
    w_f_m: float
    w_key: int


def reachable_slices(lut, kind, L):
    """kind 의 도달 가능한 슬라이스 키 오름차순 tuple(없으면 `()`)."""
    grid = lut.spec.manufacturing_grid_m
    ref = lut.cap_map[kind].w_key
    sl = None if ref is None else lut.slice_map.get((kind, ref))
    if sl is None or not sl.l_bins.bins or sl.l_bins.w_bin is None:
        return ()
    if bin_index(tuple((b.lmin, b.lmax) for b in sl.l_bins.bins), L, grid, lut.bin_rule) is None:
        return ()
    floor, ceil = round(dict(lut.spec.min_finger_w_m)[kind] / grid), round(sl.l_bins.w_bin[1] / grid)
    return tuple(sorted(key for (k, key) in lut.slice_map if k == kind and floor <= key <= ceil))


def _finger_count(x):
    k = math.floor(x)
    if k == 0:
        return 1
    return k if x - k <= k + 1 - x else k + 1


def finger_slice(lut, kind, L, w_of):
    """`(m, w_f_m, w_key)` = 후보 슬라이스마다 `w_of(키)` 의 총 폭 W 를 손가락으로 쪼갰을 때 잔차가 가장 작은 것(동률은 큰 키)."""
    grid = lut.spec.manufacturing_grid_m
    keys = reachable_slices(lut, kind, L)
    if not keys:
        raise seal_violation(REASON_SLICE_MISSING, kind=kind, L=L, why=WHY_NO_W_HI, excluded=())
    best, excluded = None, []
    for key in keys:
        width = w_of(key)
        if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width) or not width > 0:
            excluded.append(key)
            continue
        m = _finger_count(width / (key * grid))
        residual = abs((m * key) * grid / width - 1)
        if best is None or residual < best[0] or (residual == best[0] and key > best[2]):
            best = (residual, m, key)
    if best is None:
        raise seal_violation(REASON_SLICE_MISSING, kind=kind, L=L, why=WHY_NO_CANDIDATE, excluded=tuple(sorted(excluded)))
    return FingerSlice(best[1], best[2] * grid, best[2])
