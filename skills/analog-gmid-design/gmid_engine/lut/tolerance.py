"""tol_V 표 -- 보간 축 leave-one-out(운영 보간과 같은 방법) 오차를 Richardson 환산해 VGS 단위로, 셀((kind, w_key, L 앵커,
VDS))별 (계획 N3.6 사용자 확정 2026-10-07, DEC-87 tol_V 연동, 설계 MOD1 2.7; L 방향은 같은 모델 bin 안에서만).

진입점: `tol_v_table`.

* 모든 L 앵커가 셀을 가진다. 보간 축 = VGS·VDS·VS + **L(같은 bin 안에서만)**.
* **같은 방법**(DEC-87): 축 a 의 **내부** 격자점 x_j(0 < j < n_a − 1)를 빼고 이웃 x_{j-1}·x_{j+1} 로 운영 보간과 같은 방법의
  추정을 만든다 -- ln ID 는 VGS 축 Hermite(기울기 GM/ID)·VDS 축 Hermite(기울기 GDS/ID)·VS·L 축 선형, gm/ID 는 VGS 축이면
  Hermite 미분, 다른 축이면 선형(운영 보간의 마디 기울기 S_a 와 같은 규칙). 두 이웃의 기울기 자료가 다 있지 않으면 그 점은
  선형(운영 보간의 대체 규칙과 같다). 양끝 격자점은 그 축 방향 추정이 없다(다른 축 방향은 있다).
* **Richardson 환산**(Q2 (ii) (A)): LOO 는 간격 2배 격자의 오차라 운영 칸(간격 h)의 칸 중앙 오차보다 2^p 배 크다(p = 보간
  차수). 그래서 점마다 LOO 값을 그 (지표, 축, 방법) 의 차수 p 로 2^p 나눠 셀 값에 넣는다(`LOO_ORDERS`). 차수는 방법에서
  유도한다: 선형 값 p = 조건 수 2, Hermite 값 p = 조건 수 4, Hermite 미분(gm/ID 의 VGS 축) p = 4 − 1 = 3, VDS·VS·L 축의
  gm/ID(선형) p = 2. 환산 전 값도 셀에 따로 둔다(`*_loo_v`).
* L 축: 앵커 i 의 양옆 앵커 i-1·i+1 이 **모두 i 와 같은 bin**(`LBinMap.anchor_bin`)일 때만(= bin 안 내부 앵커) 추정한다.
  앵커 2개 bin 은 부르는 쪽이 bin 중점 검증 시뮬레이션의 보간 오차를 `l_bin_checks` 로 줄 수 있고(그 값은 이미 운영 보간의
  칸 중앙 오차라 환산하지 않는다), 주지 않으면 "missing_external" 로 남는다 -- 앵커마다 `TolVTable.l_loo`, bin 마다
  `TolVTable.l_loo_bins` 에 명시한다(조용히 빼지 않음).
* 셀별 값만 낸다(전역 최댓값 하나로 줄이지 않는다). 두 지표(`TOL_V_METRICS`) -- 소비자 배정은 계획 N3.6:
  - `id_equivalent`: 점마다 |ln ID_loo − ln ID| / (gm/ID) / 2^p. 그 점과 축 방향 두 이웃이 모두 on_mask.
  - `gm_id_inverse`: 곡선 (L 앵커, VDS_k, VS_s) 이 on_mask 전부 참일 때, 목표 j = 정점 이후 격자점 중 오른쪽 모든 점보다
    gm/ID 가 큰 점(VGS_j 가 그 곡선의 강반전 분지 해). LOO 곡선: VGS 축 = 마디 j 를 뺀 곡선(j 가 VGS 양끝이면 없음),
    VDS·VS·L 축 = 이웃 두 곡선으로 위 규칙대로 추정한 곡선(축 내부·두 곡선 on_mask 전부 참·L 은 bin 안 내부 앵커일 때).
    값 = |strong_inversion_root(LOO 곡선, g_j) − VGS_j| / 2^p (역산 = 운영 `vgs_for_gm_id` 와 같은 Hermite 칸 근).
    해가 없으면 값에 넣지 않고 `n_inverse_failed` 로 센다. LOO 는 측정이라 단조 검사로 거르지 않는다.
* 셀 값 = 그 (L 앵커 i, VDS_k) 안의 모든 VGS·VS·목표·축 최댓값, 없으면 None.
"""
import bisect

import numpy as np

from ._helpers_anchor import l_position
from ._helpers_interp import HERMITE_CONDITIONS, LINEAR_CONDITIONS, hermite
from ._helpers_root import strong_inversion_root
from .axis_guard import check_axes
from .lut_types import AXES, TOL_V_METRICS, TolVCell

LINEAR_ORDER = len(LINEAR_CONDITIONS)
HERMITE_ORDER = len(HERMITE_CONDITIONS)
HERMITE_SLOPE_ORDER = HERMITE_ORDER - 1
LOO_ORDERS = (
    ("gm_id_inverse", "L", "linear", LINEAR_ORDER),
    ("gm_id_inverse", "VDS", "linear_slope", LINEAR_ORDER),
    ("gm_id_inverse", "VGS", "hermite_slope", HERMITE_SLOPE_ORDER),
    ("gm_id_inverse", "VS", "linear", LINEAR_ORDER),
    ("id_equivalent", "L", "linear", LINEAR_ORDER),
    ("id_equivalent", "VDS", "hermite", HERMITE_ORDER),
    ("id_equivalent", "VGS", "hermite", HERMITE_ORDER),
    ("id_equivalent", "VS", "linear", LINEAR_ORDER),
)


def _l_interior(l_bins, n):
    """앵커마다 bin 안 내부(양옆 앵커가 같은 bin) 여부 tuple. 지도가 없으면 모두 거짓."""
    if not l_bins.bins:
        return (False,) * n
    ab = l_bins.anchor_bin
    return tuple(0 < i < n - 1 and ab[i - 1] == ab[i] == ab[i + 1] for i in range(n))


def _external_by_model(l_bin_checks):
    """`l_bin_checks` ((model, gm_id_inverse_v, id_equivalent_v), ...) -> {model: {metric 필드: 값}}. 같은 model 두 번 -> ValueError."""
    out = {}
    for model, inv, eq in l_bin_checks:
        if model in out:
            raise ValueError("tol_v_table: l_bin_checks 에 bin %r 가 두 번 있다" % (model,))
        out[model] = {"gm_id_inverse_v": None if inv is None else float(inv),
                      "id_equivalent_v": None if eq is None else float(eq)}
    return out


def _l_loo_report(l_bins, interior, external):
    """(앵커별 상태 tuple, bin 별 (model, 앵커 index tuple, 상태) tuple, {앵커 index: 외부 값 dict}).

    bin 상태: 내부 앵커 있음(앵커 3개 이상) "computed", 앵커 1개 "single_point"(그 bin 안 L 보간 자체가 없다 --
    거부 `lut_l_bin_unbracketed`), 그 밖(앵커 2개) 외부 값이 있으면 "external", 없으면 "missing_external".
    외부 값은 앵커 2개 bin 에만 받는다 -- 다른 bin·지도에 없는 model 이면 ValueError(조용히 버리지 않음).
    """
    if not l_bins.bins:
        if external:
            raise ValueError("tol_v_table: bin 지도가 없는 슬라이스에 l_bin_checks 가 주어졌다: %r" % (sorted(external),))
        return ("bins_unavailable",) * len(interior), (), {}
    ab = l_bins.anchor_bin
    has_interior = {b for b, inner in zip(ab, interior) if inner}
    status, per_bin, ext_rows = {}, [], {}
    for b in sorted(set(ab)):
        model = l_bins.bins[b].model
        members = tuple(i for i, m in enumerate(ab) if m == b)
        if b in has_interior:
            status[b] = "computed"
        elif len(members) <= 1:
            status[b] = "single_point"
        elif model in external:
            status[b] = "external"
            ext_rows.update({i: external[model] for i in members})
        else:
            status[b] = "missing_external"
        per_bin.append((model, members, status[b]))
    allowed = {model for model, _, st in per_bin if st == "external"}
    unused = sorted(set(external) - allowed)
    if unused:
        raise ValueError("tol_v_table: l_bin_checks 는 앵커 2개 bin 에만 준다 -- 해당 없는 bin: %r" % (unused,))
    anchor_status = {"computed": "bin_edge", "single_point": "bin_single_point", "external": "bin_external",
                     "missing_external": "bin_missing_external"}
    per_anchor = tuple("in_bin_interior" if inner else anchor_status[status[b]] for b, inner in zip(ab, interior))
    return per_anchor, tuple(per_bin), ext_rows


def _order(metric, axis):
    return next(p for m, a, _, p in LOO_ORDERS if m == metric and a == axis)


def _pairs(arr, axis):
    """축 `axis` 방향 (이전 이웃, 다음 이웃) 보기(첫 축으로 옮긴 모양, 길이 n − 2)."""
    a = np.moveaxis(arr, axis, 0)
    return a[:-2], a[2:]


def _loo(lid, slope, slope_ok, axis, grid, hermite_axis):
    """축 `axis` 내부 격자점의 LOO 추정 ln ID 와 점마다 차수 p (첫 축으로 옮긴 모양, 길이 n − 2).

    `hermite_axis` 이고 두 이웃의 기울기 자료가 다 있으면 Hermite(차수 HERMITE_ORDER), 아니면 선형(LINEAR_ORDER)."""
    x = np.asarray(grid, dtype=float)
    shape = (-1,) + (1,) * (lid.ndim - 1)
    h = (x[2:] - x[:-2]).reshape(shape)
    t = ((x[1:-1] - x[:-2]) / (x[2:] - x[:-2])).reshape(shape)
    y0, y1 = _pairs(lid, axis)
    linear = y0 + t * (y1 - y0)
    if not hermite_axis:
        return linear, np.full(linear.shape, LINEAR_ORDER)
    m0, m1 = _pairs(slope, axis)
    ok0, ok1 = _pairs(slope_ok, axis)
    use = ok0 & ok1
    with np.errstate(invalid="ignore", over="ignore"):
        herm, _ = hermite(y0, y1, m0, m1, h, t)
    return np.where(use, herm, linear), np.where(use, HERMITE_ORDER, LINEAR_ORDER)


def _id_equivalent(sl, lid, gm_id, gds_id, interior):
    """([L, VDS] 환산 셀 최댓값, [L, VDS] 환산 전 셀 최댓값) 배열(정의 없음 = NaN). L 축 추정은 `interior` 에서만."""
    best = np.full(lid.shape, np.nan)
    raw_best = np.full(lid.shape, np.nan)
    in_bin = np.asarray(interior, dtype=bool).reshape((-1,) + (1,) * (lid.ndim - 1))
    slopes = {"VGS": (gm_id, sl.on_mask), "VDS": (gds_id, sl.vds_slope_ok)}
    for axis, name in enumerate(AXES):
        slope, ok_mask = slopes.get(name, (lid, sl.on_mask))
        est, order = _loo(lid, slope, ok_mask, axis, sl.grids[axis], name in slopes)
        mid = np.moveaxis(lid, axis, 0)[1:-1]
        on = np.moveaxis(sl.on_mask, axis, 0)
        ok = on[:-2] & on[1:-1] & on[2:]
        if name == "L":
            ok = ok & np.moveaxis(np.broadcast_to(in_bin, lid.shape), axis, 0)[1:-1]
        raw = np.where(ok, np.abs(est - mid) / np.moveaxis(gm_id, axis, 0)[1:-1], np.nan)
        for target, value in ((raw_best, raw), (best, raw / 2.0 ** order)):
            view = np.moveaxis(target, axis, 0)
            view[1:-1] = np.fmax(view[1:-1], value)
    return _cell_max(best), _cell_max(raw_best)


def _cell_max(per_point):
    per_cell = np.moveaxis(per_point, (AXES.index("L"), AXES.index("VDS")), (0, 1))
    flat = per_cell.reshape(per_cell.shape[0], per_cell.shape[1], -1)
    out = np.full(flat.shape[:-1], np.nan)
    has = ~np.isnan(flat).all(axis=-1)
    out[has] = np.nanmax(flat[has], axis=-1)
    return out


def _targets(g, on_curve):
    """(곡선 index, VGS index) 목표 쌍: 정점 이후이고 오른쪽 모든 점보다 gm/ID 가 큰 점."""
    right = np.full(g.shape, -np.inf)
    right[:, :-1] = np.maximum.accumulate(g[:, :0:-1], axis=1)[:, ::-1]
    cols = np.arange(g.shape[1])
    mask = (g > right) & (cols[None, :] >= np.argmax(g, axis=1)[:, None]) & on_curve[:, None]
    return np.nonzero(mask)


def _vs_pairs(grid):
    """VS 축 곡선 s 마다 (아래 이웃 index, 위 이웃 index, t 열벡터, 내부 여부) -- 슬라이스당 1회(셀 반복 밖)."""
    x = np.asarray(grid, dtype=float)
    rows = np.arange(len(x))
    inner = (rows > 0) & (rows < len(x) - 1)
    lo_c = np.where(inner, rows - 1, rows)
    hi_c = np.where(inner, rows + 1, rows)
    t = np.where(inner, (x - x[lo_c]) / np.where(inner, x[hi_c] - x[lo_c], 1.0), 0.0)[:, None]
    return lo_c, hi_c, t, inner


def _vs_neighbor_curves(sl, lid, gm_id, i, k, vs_pairs):
    """VS 축 LOO 곡선 묶음 (Y, G, 정의 여부) -- 곡선 s 마다 이웃 s−1·s+1 로 선형(모양 (VS, VGS)), s 가 VS 양끝이면 정의 없음."""
    lo_c, hi_c, t, inner = vs_pairs
    y = lid[i, :, k, :].T
    g = gm_id[i, :, k, :].T
    on = sl.on_mask[i, :, k, :].T.all(axis=1)
    valid = inner & on[lo_c] & on[hi_c]
    return y[lo_c] + t * (y[hi_c] - y[lo_c]), g[lo_c] + t * (g[hi_c] - g[lo_c]), valid


def _neighbor_curves(sl, lid, gm_id, gds_id, i, k, axis, idx, vs_pairs):
    """축 `axis`(L·VDS·VS) 방향 LOO 곡선 묶음 (Y, G, 정의 여부) -- 모양 (VS, VGS). L·VDS 는 그 축에서 뺄 index `idx` 가
    내부일 때만 정의(아니면 None), VS 는 곡선마다(`_vs_neighbor_curves`). VDS 축 ln ID 는 Hermite(기울기 GDS/ID, 두 이웃
    기울기 자료가 다 있을 때), 그 밖은 선형. gm/ID 는 모든 축 선형(운영 보간의 마디 기울기 규칙)."""
    if axis == AXES.index("VS"):
        return _vs_neighbor_curves(sl, lid, gm_id, i, k, vs_pairs)
    if not 0 < idx < len(sl.grids[axis]) - 1:
        return None
    x = sl.grids[axis]
    t = (x[idx] - x[idx - 1]) / (x[idx + 1] - x[idx - 1])
    h = x[idx + 1] - x[idx - 1]

    def at(arr, j):
        pos = [i, slice(None), k, slice(None)]
        pos[axis] = j
        return np.asarray(arr[tuple(pos)])

    y0, y1 = at(lid, idx - 1).T, at(lid, idx + 1).T
    g0, g1 = at(gm_id, idx - 1).T, at(gm_id, idx + 1).T
    valid = at(sl.on_mask, idx - 1).all(axis=0) & at(sl.on_mask, idx + 1).all(axis=0)
    y = y0 + t * (y1 - y0)
    if axis == AXES.index("VDS"):
        m0, m1 = at(gds_id, idx - 1).T, at(gds_id, idx + 1).T
        use = at(sl.vds_slope_ok, idx - 1).T & at(sl.vds_slope_ok, idx + 1).T
        with np.errstate(invalid="ignore", over="ignore"):
            y = np.where(use, hermite(y0, y1, m0, m1, h, t)[0], y)
    return y, g0 + t * (g1 - g0), valid


def _inverse_cell(sl, lid, gm_id, gds_id, i, k, l_inner, vs_pairs, orders):
    """셀 (i, k) 의 (환산 최댓값, 환산 전 최댓값, 시도 수, 실패 수) -- gm_id_inverse 지표. `vs_pairs`·`orders`(축 이름 ->
    gm_id_inverse 차수)는 슬라이스당 1회 계산해 넘긴다."""
    v = sl.VGS_grid
    n = len(v)
    on_curve = sl.on_mask[i, :, k, :].all(axis=0)
    Y = lid[i, :, k, :].T
    G = gm_id[i, :, k, :].T
    s_t, j_t = _targets(G, on_curve)
    families = []
    inner = (j_t > 0) & (j_t < n - 1)
    if inner.any():
        s_r, j_r = s_t[inner], j_t[inner]
        keep = np.arange(n - 1)[None, :]
        cols = keep + (keep >= j_r[:, None])
        families.append((v[cols], Y[s_r[:, None], cols], G[s_r[:, None], cols], G[s_r, j_r], v[j_r], orders["VGS"]))
    for name, idx in (("VDS", k), ("VS", None)) + ((("L", i),) if l_inner else ()):
        axis = AXES.index(name)
        got = _neighbor_curves(sl, lid, gm_id, gds_id, i, k, axis, idx, vs_pairs)
        if got is None:
            continue
        y_loo, g_loo, valid = got
        sel = valid[s_t]
        if not sel.any():
            continue
        s_r, j_r = s_t[sel], j_t[sel]
        families.append((np.broadcast_to(v, (len(s_r), n)), y_loo[s_r], g_loo[s_r], G[s_r, j_r], v[j_r], orders[name]))
    worst = raw_worst = None
    n_try = n_failed = 0
    for vv, yy, gg, target, truth, order in families:
        root, _ = strong_inversion_root(vv, yy, gg, target)
        n_try += len(target)
        found = np.isfinite(root)
        n_failed += int(np.count_nonzero(~found))
        if found.any():
            err = np.abs(root[found] - truth[found])
            raw_worst = max(float(err.max()), raw_worst if raw_worst is not None else float(err.max()))
            conv = float(err.max()) / 2.0 ** order
            worst = max(conv, worst if worst is not None else conv)
    return worst, raw_worst, n_try, n_failed


class TolVTable:
    """(kind, w_key) 슬라이스의 tol_V 표. `cells[i_L][i_vds]` = TolVCell, 축은 `L_anchors`·`vds_grid`.

    `l_bins`: 슬라이스의 `LBinMap`(at() 의 L 위치 판정). `l_loo`: 앵커마다 L 방향 상태 -- "in_bin_interior"(L 방향 LOO
    가 셀에 들어감), "bin_edge"(내부 앵커가 있는 bin 의 첫·끝 앵커 -- 같은 bin 의 L 보간 오차는 내부 앵커 셀에 있다),
    "bin_external"(앵커 2개 bin, 외부 값이 셀에 들어감), "bin_missing_external"(앵커 2개 bin, 외부 값 없음 -- L 방향 오차
    미반영), "bin_single_point"(앵커 1개 bin -- 그 bin 에선 L 보간이 없다), "bins_unavailable"(bin 지도 없음).
    `l_loo_bins`: bin 마다 `(model, 앵커 index tuple, 상태)`, 상태 "computed"·"external"·"missing_external"·"single_point".
    `loo_orders`: Richardson 환산 기록 ((지표, 축, 방법, 차수 p, 환산 배수 2^-p), ...) -- `LOO_ORDERS` 그대로(VGS·VDS 축
    id_equivalent 에서 기울기 자료가 없어 선형으로 추정한 점은 선형 차수를 쓴다).
    """

    def __init__(self, kind, w_key, L_anchors, vds_grid, cells, l_bins, l_loo, l_loo_bins, loo_orders):
        self.kind = kind
        self.w_key = w_key
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells
        self.l_bins = l_bins
        self.l_loo = l_loo
        self.l_loo_bins = l_loo_bins
        self.loo_orders = loo_orders

    def at(self, L, vds, metric):
        """조회점 (L, vds) 의 tol_V(V): L 이 앵커면 그 앵커 행, 같은 bin 안 보간이면 양옆 앵커 두 행(CONTRACT 4.0),
        VDS 가 든 격자 칸 [k, k+1] (`bisect_right - 1`, 마지막 격자점은 마지막 칸) -- 그 셀들 중 정의된 값의 최댓값.
        정의된 값이 없으면 None.

        실패: `metric` 이 `TOL_V_METRICS` 밖 -> `ValueError`, L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`.
        """
        if metric not in TOL_V_METRICS:
            raise ValueError("TolVTable.at: metric 은 %s 중 하나" % (TOL_V_METRICS,))
        context = (("kind", self.kind), ("table", "tol_v"), ("w_key", self.w_key))
        lo, hi, _ = l_position(self.L_anchors, self.l_bins, L, context)
        vds = float(vds)
        check_axes((self.vds_grid,), (AXES[2],), (vds,), context)
        k = min(bisect.bisect_right(self.vds_grid, vds) - 1, len(self.vds_grid) - 2)
        field = metric + "_v"
        vals = [getattr(self.cells[i][b], field) for i in sorted({lo, hi}) for b in (k, k + 1)]
        vals = [v for v in vals if v is not None]
        return max(vals) if vals else None


def _with_external(value, ext):
    """셀 값과 외부 bin 값의 최댓값. 셀 값이 None(그 셀에 켜진 격자점 없음)이면 None 그대로."""
    if value is None or ext is None:
        return value
    return max(value, ext)


def _opt(x):
    return None if x is None or np.isnan(x) else float(x)


def tol_v_table(memo, kind, w_key, l_bin_checks=()):
    """(kind, w_key) 슬라이스의 `TolVTable`. memo 영역 derived(같은 인자당 1회 계산). 폭 키 없음 -> `KeyError`.

    `l_bin_checks`: 앵커 2개 bin 의 외부 L 방향 오차 `((model, gm_id_inverse_v, id_equivalent_v), ...)`(V, 값 None 허용) --
    bin 중점 검증 시뮬레이션에서 잰 보간 오차(lut_regen_plan.md 2절 K2'). 그 bin 앵커 행의 정의된 셀 값과 최댓값을 취한다.
    앵커 2개 bin 이 아닌 model·중복 model·지도 없는 슬라이스 -> `ValueError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    checks = tuple(sorted((str(m), None if a is None else float(a), None if b is None else float(b))
                          for m, a, b in l_bin_checks))

    def compute():
        interior = _l_interior(sl.l_bins, len(sl.grids[0]))
        l_loo, l_loo_bins, ext_rows = _l_loo_report(sl.l_bins, interior, _external_by_model(checks))
        lid = sl.log_ID
        gm_id = np.exp(sl.log_GM - lid)
        gds_id = np.exp(sl.log_GDS - lid)
        eq, eq_raw = _id_equivalent(sl, lid, gm_id, gds_id, interior)
        vs_pairs = _vs_pairs(sl.grids[3])
        orders = {a: _order("gm_id_inverse", a) for a in AXES}
        cells = []
        for i in range(len(sl.grids[0])):
            ext = ext_rows.get(i, {})
            row = []
            for k in range(len(sl.grids[2])):
                inv, inv_raw, n_try, n_failed = _inverse_cell(sl, lid, gm_id, gds_id, i, k, interior[i], vs_pairs, orders)
                row.append(TolVCell(
                    _with_external(_opt(inv), ext.get("gm_id_inverse_v")),
                    _with_external(_opt(eq[i, k]), ext.get("id_equivalent_v")),
                    n_try, n_failed, _opt(inv_raw), _opt(eq_raw[i, k])))
            cells.append(tuple(row))
        orders = tuple((m, a, meth, p, 2.0 ** -p) for m, a, meth, p in LOO_ORDERS)
        return TolVTable(kind, w_key, sl.grids[0], sl.grids[2], tuple(cells), sl.l_bins, l_loo, l_loo_bins, orders)

    return memo.lookup("derived", "tol_v_table", (kind, w_key, checks), compute)
