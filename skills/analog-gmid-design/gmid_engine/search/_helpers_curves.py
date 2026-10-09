"""출발 구간 공용 보간 helper -- gm/ID 축 곡선 값을 읽는 두 함수 (설계 41 §6, `iv_*` 가 함께 쓴다).

* `at_gm_id(gm_id, values, g, log=False)`: 곡선 마디 값을 gm/ID = g 에서 선형(또는 log) 보간. 마디 gm/ID 는 분지에서 내려가는 순서(`GmIdAxisCurve`), 정의역 밖은 끝 값.
* `hull(gm_id, values, level, below=True)`: {g : values(g) ≤ level}(below) 또는 {g : values(g) ≥ level} 의 gm/ID 폭 (최소, 최대). 마디 사이는 선형 교차점이고
  비단조 곡선(격자 전용 칸)도 모든 칸을 센다. 비면 None -- 단조 가정으로 역산하지 않는 이유다(41 §4.1 해법 매핑).
"""
import math

import numpy as np


def at_gm_id(gm_id, values, g, log=False):
    xs = np.asarray(gm_id, dtype=float)[::-1]
    ys = np.asarray(values, dtype=float)[::-1]
    if log:
        return float(math.exp(np.interp(g, xs, np.log(ys))))
    return float(np.interp(g, xs, ys))


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
