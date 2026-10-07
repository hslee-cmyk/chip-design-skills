"""구간 bisection (설계 3.4 '1변수 SCC: 창 양 끝 부호가 다르면 bisection', 계획 N3.6 K_max).

진입점: `bisect_root(f, lo, hi, iterations) -> (x | None, f_lo, f_hi)`.

* `f(x)` 는 실수 또는 ±inf(조회 정의역 밖이지만 부호가 정해지는 쪽 -- 부르는 쪽이 정한다)를 돌려준다.
* f(lo)·f(hi) 부호가 같으면(어느 쪽도 0 이 아님) 근 없음 -> (None, f_lo, f_hi). 끝점이 0 이면 그 끝점.
* 아니면 `iterations` 번 반으로 줄이고(가운데 값이 0 이면 그 점) 마지막 구간의 가운데를 돌려준다. 반복 수는 부르는 쪽이
  `k_max(hi − lo, tol)` 로 정한다 -- 그러면 마지막 구간 폭 ≤ tol 이다. 상수 없음.
"""


def bisect_root(f, lo, hi, iterations):
    f_lo, f_hi = f(lo), f(hi)
    if f_lo == 0:
        return lo, f_lo, f_hi
    if f_hi == 0:
        return hi, f_lo, f_hi
    if (f_lo > 0) == (f_hi > 0):
        return None, f_lo, f_hi
    a, b, fa = lo, hi, f_lo
    for _ in range(iterations):
        mid = (a + b) / 2
        fm = f(mid)
        if fm == 0:
            return mid, f_lo, f_hi
        if (fm > 0) == (fa > 0):
            a, fa = mid, fm
        else:
            b = mid
    return (a + b) / 2, f_lo, f_hi
