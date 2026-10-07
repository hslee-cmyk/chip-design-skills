"""tol_V 표 -- 보간 축 leave-one-out 보간 오차를 VGS 단위로, 셀((kind, w_key, L 앵커, VDS))별
(계획 N3.6 사용자 확정 2026-10-07, 설계 MOD1 2.7; L 방향은 같은 모델 bin 안에서만 -- 사용자 결정 2026-10-07).

진입점: `tol_v_table`.

* 모든 L 앵커가 셀을 가진다. 보간 축 = VGS·VDS·VS + **L(같은 bin 안에서만)**.
* 축 a ∈ (VGS, VDS, VS) 의 **내부** 격자점 x_j(0 < j < n_a - 1)를 빼고 이웃 x_{j-1}·x_{j+1} 로 같은 선형 보간
  (운영 보간 `multilinear_interp` 의 1축 2점 경우와 같은 식: lnX_{j-1} + t·(lnX_{j+1} - lnX_{j-1}), t = (x_j - x_{j-1}) / (x_{j+1} - x_{j-1}),
  ln ID·ln GM 로그공간)한 값을 그 점의 LUT 값과 비교한다. 양끝 격자점은 그 축 방향 추정이 없다(다른 축 방향은 있다).
* L 축: 앵커 i 의 양옆 앵커 i-1·i+1 이 **모두 i 와 같은 bin**(`LBinMap.anchor_bin`)일 때만(= bin 안 내부 앵커) 같은 식으로
  추정한다(운영 L 보간이 같은 bin 의 두 앵커만 쓰므로 bin 경계를 건너는 추정은 만들지 않는다). 그래서 앵커가 3개 미만인
  bin 은 LOO 가 없다. 앵커 2개 bin 은 부르는 쪽이 bin 중점 검증 시뮬레이션의 보간 오차를 `l_bin_checks` 로 줄 수 있고
  (lut_regen_plan.md 2절 K2'), 주지 않으면 "missing_external" 로 남는다 -- 앵커마다 `TolVTable.l_loo`, bin 마다
  `TolVTable.l_loo_bins` 에 명시한다(조용히 빼지 않음).
* 셀별 값만 낸다(전역 최댓값 하나로 줄이지 않는다). 두 지표(`TOL_V_METRICS`) -- 소비자 배정은 계획 N3.6:
  - `id_equivalent`(KCL·W 보존·소자 경고): 점마다 |ln ID_loo - ln ID| / (gm/ID). 그 점과 축 방향 두 이웃이 모두 on_mask.
  - `gm_id_inverse`(봉인 2 VGS 정합): 곡선 (L 앵커, VDS_k, VS_s) 이 on_mask 전부 참일 때, 목표 j = 정점 이후 격자점 중
    오른쪽 모든 점보다 gm/ID 가 큰 점(VGS_j 가 그 곡선의 강반전 분지 해). LOO 곡선:
    VGS 축 = 그 곡선의 j 점 값만 이웃 보간값으로 바꾼 곡선(j 가 VGS 양끝이면 없음),
    VDS 축 = 곡선 VDS_{k-1}·VDS_{k+1} 로 보간한 곡선(k 내부, 두 곡선 on_mask 전부 참일 때),
    VS 축 = 곡선 VS_{s-1}·VS_{s+1} 로 보간한 곡선(같은 조건),
    L 축 = 곡선 L_{i-1}·L_{i+1} 로 보간한 곡선(i 가 bin 안 내부 앵커, 같은 on_mask 조건). 값 = |strong_inversion_root(LOO 곡선, g_j) - VGS_j|,
    해가 없으면 값에 넣지 않고 `n_inverse_failed` 로 센다.
* 셀 값 = 그 (L 앵커 i, VDS_k) 안의 모든 VGS·VS·목표·축 최댓값, 없으면 None. `n_targets` = 그 셀의 gm/ID 역산 시도 수
  ((목표, 축) 쌍), `n_inverse_failed` = 그중 해 없음 수.
"""
import bisect

import numpy as np

from ._helpers_anchor import l_position
from ._helpers_root import peak_index, strong_inversion_root
from .axis_guard import check_axes
from .lut_types import AXES, TOL_V_METRICS, TolVCell


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


def _loo(arr, axis, grid):
    """축 `axis` 내부 격자점마다 이웃 두 점 선형 보간값(배열 모양 그대로, 양끝 = NaN)."""
    x = np.asarray(grid, dtype=float)
    t = (x[1:-1] - x[:-2]) / (x[2:] - x[:-2])
    a = np.moveaxis(arr, axis, 0)
    out = np.full(a.shape, np.nan)
    out[1:-1] = a[:-2] + t.reshape((-1,) + (1,) * (a.ndim - 1)) * (a[2:] - a[:-2])
    return np.moveaxis(out, 0, axis)


def _neighbors_on(mask, axis):
    """축 `axis` 방향으로 자기와 두 이웃이 모두 on 인 점(양끝 = 거짓)."""
    m = np.moveaxis(mask, axis, 0)
    out = np.zeros(m.shape, dtype=bool)
    out[1:-1] = m[:-2] & m[1:-1] & m[2:]
    return np.moveaxis(out, 0, axis)


def _id_equivalent(sl, interior):
    """[L, VDS] 셀 최댓값 배열(정의 없음 = NaN). L 축 추정은 `interior`(bin 안 내부 앵커)에서만."""
    gm_id = np.exp(sl.log_GM - sl.log_ID)
    best = np.full(sl.on_mask.shape, np.nan)
    l_axis = AXES.index("L")
    in_bin = np.asarray(interior, dtype=bool).reshape((-1,) + (1,) * (sl.on_mask.ndim - 1))
    for axis in range(len(AXES)):
        est = _loo(sl.log_ID, axis, sl.grids[axis])
        ok = _neighbors_on(sl.on_mask, axis)
        if axis == l_axis:
            ok = ok & in_bin
        err = np.where(ok, np.abs(est - sl.log_ID) / gm_id, np.nan)
        best = np.fmax(best, err)
    per_cell = np.moveaxis(best, (AXES.index("L"), AXES.index("VDS")), (0, 1))
    flat = per_cell.reshape(per_cell.shape[0], per_cell.shape[1], -1)
    out = np.full(flat.shape[:-1], np.nan)
    has = ~np.isnan(flat).all(axis=-1)
    out[has] = np.nanmax(flat[has], axis=-1)
    return out


def _targets(g):
    p = peak_index(g)
    out = []
    right_max = -np.inf
    for j in range(len(g) - 1, p - 1, -1):
        if g[j] > right_max:
            out.append(j)
        right_max = max(right_max, g[j])
    return out


def _curve_loo(sl, i, k, s, axis, idx):
    """L·VDS·VS 축(`axis`, 그 축 index `idx`) 방향 LOO 곡선 gm/ID, 정의 안 되면 None."""
    if not 0 < idx < len(sl.grids[axis]) - 1:
        return None
    pos = [i, slice(None), k, s]
    lo_pos, hi_pos = list(pos), list(pos)
    lo_pos[axis], hi_pos[axis] = idx - 1, idx + 1
    if not (sl.on_mask[tuple(lo_pos)].all() and sl.on_mask[tuple(hi_pos)].all()):
        return None
    x = sl.grids[axis]
    t = (x[idx] - x[idx - 1]) / (x[idx + 1] - x[idx - 1])
    lid = sl.log_ID[tuple(lo_pos)] + t * (sl.log_ID[tuple(hi_pos)] - sl.log_ID[tuple(lo_pos)])
    lgm = sl.log_GM[tuple(lo_pos)] + t * (sl.log_GM[tuple(hi_pos)] - sl.log_GM[tuple(lo_pos)])
    return np.exp(lgm - lid)


def _inverse_cell(sl, i, k, l_inner):
    vgs = sl.VGS_grid
    x = sl.grids[1]
    worst = None
    n_try = n_failed = 0
    for s in range(len(sl.grids[3])):
        if not sl.on_mask[i, :, k, s].all():
            continue
        lid = sl.log_ID[i, :, k, s]
        lgm = sl.log_GM[i, :, k, s]
        g = np.exp(lgm - lid)
        cands = [_curve_loo(sl, i, k, s, AXES.index("VDS"), k), _curve_loo(sl, i, k, s, AXES.index("VS"), s)]
        if l_inner:
            cands.append(_curve_loo(sl, i, k, s, AXES.index("L"), i))
        curves = [c for c in cands if c is not None]
        for j in _targets(g):
            loo = list(curves)
            if 0 < j < len(vgs) - 1:
                t = (x[j] - x[j - 1]) / (x[j + 1] - x[j - 1])
                gv = g.copy()
                gv[j] = np.exp((lgm[j - 1] + t * (lgm[j + 1] - lgm[j - 1])) - (lid[j - 1] + t * (lid[j + 1] - lid[j - 1])))
                loo.append(gv)
            for c in loo:
                n_try += 1
                est = strong_inversion_root(c, vgs, g[j])
                if est is None:
                    n_failed += 1
                    continue
                e = abs(est - vgs[j])
                worst = e if worst is None else max(worst, e)
    return worst, n_try, n_failed


class TolVTable:
    """(kind, w_key) 슬라이스의 tol_V 표. `cells[i_L][i_vds]` = TolVCell, 축은 `L_anchors`·`vds_grid`.

    `l_bins`: 슬라이스의 `LBinMap`(at() 의 L 위치 판정). `l_loo`: 앵커마다 L 방향 상태 -- "in_bin_interior"(L 방향 LOO
    가 셀에 들어감), "bin_edge"(내부 앵커가 있는 bin 의 첫·끝 앵커 -- 같은 bin 의 L 보간 오차는 내부 앵커 셀에 있다),
    "bin_external"(앵커 2개 bin, 외부 값이 셀에 들어감), "bin_missing_external"(앵커 2개 bin, 외부 값 없음 -- L 방향 오차
    미반영), "bin_single_point"(앵커 1개 bin -- 그 bin 에선 L 보간이 없다), "bins_unavailable"(bin 지도 없음).
    `l_loo_bins`: bin 마다 `(model, 앵커 index tuple, 상태)`, 상태 "computed"·"external"·"missing_external"·"single_point".
    """

    def __init__(self, kind, w_key, L_anchors, vds_grid, cells, l_bins, l_loo, l_loo_bins):
        self.kind = kind
        self.w_key = w_key
        self.L_anchors = L_anchors
        self.vds_grid = vds_grid
        self.cells = cells
        self.l_bins = l_bins
        self.l_loo = l_loo
        self.l_loo_bins = l_loo_bins

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
        eq = _id_equivalent(sl, interior)
        cells = []
        for i in range(len(sl.grids[0])):
            ext = ext_rows.get(i, {})
            row = []
            for k in range(len(sl.grids[2])):
                inv, n_try, n_failed = _inverse_cell(sl, i, k, interior[i])
                e = eq[i, k]
                row.append(TolVCell(
                    _with_external(None if inv is None else float(inv), ext.get("gm_id_inverse_v")),
                    _with_external(None if np.isnan(e) else float(e), ext.get("id_equivalent_v")),
                    n_try, n_failed))
            cells.append(tuple(row))
        return TolVTable(kind, w_key, sl.grids[0], sl.grids[2], tuple(cells), sl.l_bins, l_loo, l_loo_bins)

    return memo.lookup("derived", "tol_v_table", (kind, w_key, checks), compute)
