"""LUT 보간 공용 helper -- 축별 보간 방법(계획 DEC-87, lut/CONTRACT.md 4.2).

* 축별 방법: ln ID 는 **VGS 축 2점 cubic-Hermite**(기울기 = 저장 GM/ID = d lnID/dVGS)와 **VDS 축 2점 cubic-Hermite**
  (기울기 = 저장 GDS/ID = d lnID/dVDS), VS·L 축은 선형이다. gm/ID 는 따로 보간하지 않고 **그 다항식의 VGS 미분**으로
  정의한다 -- 그래서 op_point·gm_id_curve·역산·gm 이 한 곡면이다. ln GDS·VTH·용량은 모든 축 선형이다.
* 텐서곱 순서: VGS 마디 a 마다 (1) 값 V_a = VDS Hermite(ln ID, 기울기 GDS/ID; L·VS 는 선형 가중) (2) 기울기
  S_a = 저장 GM/ID 의 (L, VDS, VS) 선형 가중(교차 도함수 자료가 없어 VDS 방향은 선형) (3) 조회 VGS 에서
  ln ID = VGS Hermite(V_a, S_a), gm/ID = 그 미분. 격자점에서는 저장값 그대로다(값·기울기 모두).
* **Hermite 칸 = 두 끝 기울기 자료가 정의되고 Fritsch–Carlson 단조 조건을 만족하는 칸**(로드 기록 `fc_ok_*`, 가중치 0 이
  아닌 모서리 모두). 아니면 그 축은 그 칸에서 선형이다(gm/ID 는 그 직선의 기울기 -- 미분 정의 유지, 선형은 단조).
  기울기 자료가 없는 마디 = VGS: on_mask 거짓, VDS: `vds_slope_ok` 거짓. 위반 칸 수는 로드 때 기록되고(`hermite_fc`,
  `curve_report`), 역산 함수는 Hermite 칸이 아닌 칸의 근을 내지 않는다(`Curve.cell_ok`). 축 밖 입력은 부르는 쪽이
  `check_axes` 로 먼저 거부한다(클램프·외삽 없음).
* Hermite 다항식은 Bernstein(Bézier) 형으로 계산한다: 조건 4개(`HERMITE_CONDITIONS` -- 두 끝 값·두 끝 기울기)에서
  차수 n = 조건 수 − 1, 제어점 (y0, y0 + m0·h/n, y1 − m1·h/n, y1), de Casteljau 로 값과 미분을 함께 낸다.
* 옛 다선형 보간(`legacy/sizing_recipe.py` 141·206행 `_multilinear_interp*`)은 운영 경로에서 빠졌고 기대값 비교의 참조로만
  남는다(CONTRACT 6절).
"""
import bisect
import math

import numpy as np

LINEAR_CONDITIONS = ("y0", "y1")
HERMITE_CONDITIONS = ("y0", "m0", "y1", "m1")
HERMITE_DEGREE = len(HERMITE_CONDITIONS) - 1


def cell(grid, x):
    """오름차순 격자 `grid` 에서 x 가 든 칸 `(i, t)`: i = `min(bisect_right(grid, x) − 1, len − 2)`(마지막 격자점은
    마지막 칸, t = 1), t = (x − grid[i]) / (grid[i+1] − grid[i]). 격자점이 하나면 `(0, 0.0)`."""
    if len(grid) == 1:
        return 0, 0.0
    i = min(max(bisect.bisect_right(grid, x) - 1, 0), len(grid) - 2)
    return i, (x - grid[i]) / (grid[i + 1] - grid[i])


def _nodes(grid, x):
    """선형 가중의 마디 index·가중치(가중치 0 마디는 뺀다): 격자점 위면 그 마디 하나, 아니면 칸 양끝."""
    i, t = cell(grid, x)
    if t == 0.0:
        return (i,), (1.0,), t
    if t == 1.0:
        return (i + 1,), (1.0,), t
    return (i, i + 1), (1.0 - t, t), t


def hermite(y0, y1, m0, m1, h, t):
    """2점 cubic-Hermite 의 (값, x 미분): 끝 값 y0·y1, 끝 기울기 m0·m1(x 단위), 칸 폭 h, 칸 안 위치 t = (x − x0)/h.
    numpy 배열이면 원소마다 계산한다. t = 0·1 에서 값·미분은 끝 값·끝 기울기다."""
    n = HERMITE_DEGREE
    p1 = y0 + m0 * h / n
    p2 = y1 - m1 * h / n
    a, b, c = y0 + t * (p1 - y0), p1 + t * (p2 - p1), p2 + t * (y1 - p2)
    q0, q1 = a + t * (b - a), b + t * (c - b)
    return q0 + t * (q1 - q0), n * (q1 - q0) / h


def hermite_root(v0, v1, y0, y1, m0, m1, residual):
    """칸 [v0, v1] 의 Hermite p 에서 `residual(p(v), p'(v)) = 0` 인 v(bisection, 원소마다 독립인 numpy 배열).

    부르는 쪽은 칸을 마디 값으로 골라 두 끝 residual 의 곱 ≤ 0 을 보장한다. 위 끝 residual 이 0 이면 위 끝(가장 큰 v).
    반올림으로 두 끝 residual 이 같은 부호가 되면(목표가 마디 값과 같을 때 로그 왕복 오차) |residual| 이 작은 끝.
    반복 수 = K_max = ceil(log2(칸 폭 / 끝값의 부동소수 간격)) -- 계획 N3.6 K_max 규칙의 tol 자리에 부동소수 분해능을 둔
    것(이 역산은 tol_V 자체를 재는 데도 쓰이므로 tol_V 를 쓸 수 없다). 불변식: residual(lo) 가 위 끝 residual 과 같은
    부호가 아님. 결과 = 마지막 구간의 아래 끝 lo(아래 끝이 정확한 근이면 그 값 그대로).
    """
    if all(np.ndim(x) == 0 for x in (v0, v1, y0, y1, m0, m1)):
        return _hermite_root_scalar(float(v0), float(v1), float(y0), float(y1), float(m0), float(m1), residual)
    v0 = np.asarray(v0, dtype=float)
    v1 = np.asarray(v1, dtype=float)
    h = v1 - v0

    def f(v):
        return residual(*hermite(y0, y1, m0, m1, h, (v - v0) / h))

    f_hi = f(v1)
    sign = np.sign(f_hi)
    lo, hi = v0, v1
    if h.size:
        spacing = np.spacing(np.maximum(np.abs(v0), np.abs(v1)))
        for _ in range(int(np.max(np.ceil(np.log2(h / spacing))))):
            mid = lo + (hi - lo) / 2
            right = f(mid) * sign > 0
            hi = np.where(right, mid, hi)
            lo = np.where(right, lo, mid)
    f_lo = f(v0)
    nearer = np.where(np.abs(f_lo) < np.abs(f_hi), v0, v1)
    return np.where(f_hi == 0, v1, np.where(f_lo * f_hi > 0, nearer, lo))


def _hermite_root_scalar(v0, v1, y0, y1, m0, m1, residual):
    """`hermite_root` 의 스칼라 경로(같은 산술·같은 반복 수 -- 원소 하나의 배열 경로와 같은 결과)."""
    h = v1 - v0

    def f(v):
        return residual(*hermite(y0, y1, m0, m1, h, (v - v0) / h))

    f_hi = f(v1)
    if f_hi == 0:
        return v1
    f_lo = f(v0)
    if f_lo * f_hi > 0:
        return v0 if abs(f_lo) < abs(f_hi) else v1
    lo, hi = v0, v1
    for _ in range(math.ceil(math.log2(h / math.ulp(max(abs(v0), abs(v1)))))):
        mid = lo + (hi - lo) / 2
        if f(mid) * f_hi > 0:
            hi = mid
        else:
            lo = mid
    return lo


def _corners(picks):
    """축별 (마디 index tuple, 가중치 tuple) 의 텐서곱 모서리 list: (index tuple, 가중치 곱)."""
    out = [((), 1.0)]
    for idx, w in picks:
        out = [(c + (i,), cw * wi) for c, cw in out for i, wi in zip(idx, w)]
    return out


def linear_point(grids, arrays, point):
    """단일 좌표 `point` 에서 `arrays` 를 모든 축 선형(다중선형)으로 보간한 값 list. 가중치 0 마디는 읽지 않는다."""
    corners = _corners([_nodes(g, x)[:-1] for g, x in zip(grids, point)])
    return [sum(w * arr.item(idx) for idx, w in corners) for arr in arrays]


def node_values(sl, lo, hi, l_val, vds, vsb, g_nodes):
    """VGS 마디 `g_nodes`(range) 의 `(V, S, cell_fc_ok)` numpy 배열 -- 모듈 docstring 의 텐서곱 (1)(2).

    V = ln ID(VDS Hermite -- 가중치 0 이 아닌 모서리 모두 VDS 기울기 자료가 있고 그 VDS 칸이 단조 조건을 만족할 때,
    아니면 VDS 선형), S = gm/ID(가중치 0 이 아닌 모서리에 on_mask 거짓이 있으면 NaN), cell_fc_ok[j] = 마디 j·j+1 사이
    VGS 칸의 모서리(가중치 0 이 아닌 L·VDS·VS) 가 모두 단조 조건 만족(VGS Hermite 사용 조건의 한쪽).
    `lo, hi, l_val` = `l_position` 결과(L 장 index·L 값). 작은 창을 list 로 한 번 꺼내 스칼라로 계산한다(조회 1점 비용).
    """
    l_idx, l_w, _ = _nodes(sl.grids[0][lo:hi + 1], l_val)
    k, td = cell(sl.grids[2], vds)
    d_idx, d_w, _ = _nodes(sl.grids[2], vds)
    s0, _ = cell(sl.grids[3], vsb)
    s_idx, s_w, _ = _nodes(sl.grids[3], vsb)
    ls = _corners(((l_idx, l_w), (tuple(s - s0 for s in s_idx), s_w)))
    lin_d = tuple((b - k, w) for b, w in zip(d_idx, d_w))
    window = (slice(lo, hi + 1), slice(g_nodes.start, g_nodes.stop), slice(k, k + 2), slice(s0, s0 + 2))
    log_id, log_gm, log_gds = (arr[window].tolist() for arr in (sl.log_ID, sl.log_GM, sl.log_GDS))
    on, vds_ok, fc_vds = (arr[window].tolist() for arr in (sl.on_mask, sl.vds_slope_ok, sl.fc_ok_vds))
    fc_vgs = sl.fc_ok_vgs[window[0], slice(g_nodes.start, g_nodes.stop - 1), window[2], window[3]].tolist()
    hermite_d = len(d_idx) > 1
    h_d = sl.grids[2][k + 1] - sl.grids[2][k]
    ends = range(len(LINEAR_CONDITIONS))
    v_out, s_out = [], []
    for a in range(len(g_nodes)):
        s_val = 0.0
        for b, wd in lin_d:
            for (l, s), w in ls:
                if on[l][a][b][s]:
                    s_val += wd * w * math.exp(log_gm[l][a][b][s] - log_id[l][a][b][s])
                else:
                    s_val = math.nan
        if not hermite_d:
            b = lin_d[0][0]
            v = sum(w * log_id[l][a][b][s] for (l, s), w in ls)
        else:
            y = [sum(w * log_id[l][a][b][s] for (l, s), w in ls) for b in ends]
            if (all(vds_ok[l][a][b][s] for (l, s), _ in ls for b in ends)
                    and all(fc_vds[l][a][0][s] for (l, s), _ in ls)):
                m = [sum(w * math.exp(log_gds[l][a][b][s] - log_id[l][a][b][s]) for (l, s), w in ls) for b in ends]
                v, _ = hermite(y[0], y[1], m[0], m[1], h_d, td)
            else:
                v = y[0] + td * (y[1] - y[0])
        v_out.append(v)
        s_out.append(s_val)
    cell_ok = [all(fc_vgs[l][a][b][s] for (l, s), _ in ls for b, _ in lin_d) for a in range(len(g_nodes) - 1)]
    return np.asarray(v_out), np.asarray(s_out), np.asarray(cell_ok, dtype=bool)
