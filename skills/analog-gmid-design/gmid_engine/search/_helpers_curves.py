"""출발 구간 공용 보간 helper -- gm/ID 축 곡선 값을 읽는 두 함수 (설계 41 §6, `iv_*` 가 함께 쓴다).

* `at_gm_id(gm_id, values, g, log=False)`: 곡선 마디 값을 gm/ID = g 에서 선형(또는 log) 보간. 마디 gm/ID 는 분지에서 내려가는 순서(`GmIdAxisCurve`), 정의역 밖은 끝 값.
  비단조 곡선(중반전 상승)은 g 를 품는 칸 중 가장 오른쪽(강반전 쪽)에서 읽는다(lut 3절).
* `hull(gm_id, values, level, below=True)`: {g : values(g) ≤ level}(below) 또는 {g : values(g) ≥ level} 의 gm/ID 폭 (최소, 최대). 마디 사이는 선형 교차점이고
  비단조 곡선(격자 전용 칸)도 모든 칸을 센다. 비면 None -- 단조 가정으로 역산하지 않는 이유다(41 §4.1 해법 매핑).
"""
import math

import numpy as np


def at_gm_id(gm_id, values, g, log=False):
    xs = np.asarray(gm_id, dtype=float)
    ys = np.asarray(values, dtype=float)
    if log:
        ys = np.log(ys)
    # 가장 오른쪽(VGS 가 큰, 강반전 쪽) 마디 칸에서 보간한다 -- lut 3절 분지 규칙(`vgs_for_gm_id`)과 같다. 단조 곡선이면 칸이 하나뿐이라 선형 보간과 같고,
    # 중반전에서 gm/ID 가 한 번 올라가는 곡선(pmos)에서는 g 가 여러 칸에 있어도 강반전 쪽 값을 읽는다(np.interp 는 단조를 가정해 엉뚱한 칸을 읽는다).
    a, b = xs[:-1], xs[1:]
    hit = np.flatnonzero(((a - g) * (b - g) <= 0) & (a != b))
    if hit.size:
        j = int(hit[-1])
        out = ys[j] + (g - a[j]) / (b[j] - a[j]) * (ys[j + 1] - ys[j])
    else:                                              # 정의역 밖 -- 끝 값(g 가 최대 gm/ID 보다 크면 그 마디, 작으면 마지막 마디)
        out = ys[int(np.argmax(xs))] if g > xs.max() else ys[-1]
    return float(math.exp(out)) if log else float(out)


def hull(gm_id, values, level, below=True):
    g = np.asarray(gm_id, dtype=float)
    v = np.asarray(values, dtype=float)
    ok = (v <= level) if below else (v >= level)
    points = []
    for j in range(g.size):
        if ok[j]:
            points.append(float(g[j]))
        if j + 1 < g.size and ok[j] != ok[j + 1] and v[j + 1] != v[j]:
            t = (level - v[j]) / (v[j + 1] - v[j])
            points.append(float(g[j] + t * (g[j + 1] - g[j])))
    return (min(points), max(points)) if points else None
