"""출발 구간 공용 LUT 곡선 묶음 (설계 41 §6 -- U3 곡선 API `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve`를 gm/ID 축으로 읽는 얇은 층).

진입점: `CurveBook(memo, w_keys)`.
(소자별 동작점은 `assign` 으로 한 번 정한 뒤 `bundle_of` 가 쓴다 -- 헤드룸 예산의 중점 `start_intervals`.)

* 곡선 = U3 `GmIdAxisCurve`(강반전 분지 VGS 마디, gm/ID 는 분지에서 내려간다). 이 클래스는 곡선 값을 새로 만들지 않고 읽기만 한다(보간·역산은 `_helpers_curves`).
* **기준 (VDS, VSB)**: 출발 단계에는 동작점이 없다. 기준 VDS = 그 kind 의 포화 경계 -- LUT VDS 격자 중 `edge_costs` 의 VDS 엣지 비용(VDSAT 최솟값 + tol_vdsat 최솟값)
  이상인 첫 격자점(소자가 포화에 머물 수 있는 가장 낮은 VDS), 곡선이 정의되지 않으면(`lut_curve_undefined` 등) 그 위 격자점으로 올린다. 기준 VSB = LUT VS 격자 첫 점
  (소스–벌크 0 V). 둘 다 상수가 아니라 LUT 격자와 U9 엣지 비용에서 읽은 값이다. 실제 동작점은 외층 커널이 푼다(출발값은 EP-7 로 판정에 쓰이지 않는다).
* 같은 인자는 한 번만 부른다: 곡선 자체는 `LutMemo` 의 curve 영역이 상한 있는 캐시를 가지고, 이 객체는 (kind, L) 별 기준 VDS 와 (kind, L, VDS) 별 tol_vdsat 만
  작은 사전(키 수 ≤ kind 수 × L 앵커 수 × VDS 격자 수)에 둔다.
"""
import numpy as np

from gmid_engine.core import SchemaRejectedError, SealViolationError
from gmid_engine.lut import ft_curve, idu_curve, intrinsic_gain_curve, tol_vdsat_table, vdsat_curve
from gmid_engine.metrics import edge_costs

from ._helpers_curves import at_gm_id

QUANTITY_FT = "ft"
QUANTITY_GAIN = "intrinsic_gain"
QUANTITY_VDSAT = "vdsat"
QUANTITY_IDU = "idu"
QUANTITY_VGS = "vgs"
_CURVE_FN = ((QUANTITY_FT, ft_curve), (QUANTITY_GAIN, intrinsic_gain_curve), (QUANTITY_VDSAT, vdsat_curve), (QUANTITY_IDU, idu_curve))
_UNDEFINED = (SealViolationError, SchemaRejectedError, KeyError, ValueError)
_LOG_QUANTITIES = (QUANTITY_FT, QUANTITY_IDU)


class CurveBook:
    """`memo`(`lut.LutMemo`)와 `w_keys`({kind: 폭 키})로 gm/ID 축 곡선을 읽는다. 정의되지 않은 (L, VDS) 조합은 `None`."""

    def __init__(self, memo, w_keys):
        self.memo = memo
        self.w_keys = dict(w_keys)
        self._edges = {}
        self._ref = {}
        self._tol = {}
        self.points = {}

    # ---------------------------------------------------------------- LUT 격자
    def slice_of(self, kind):
        return self.memo.lut.slice_map[(kind, self.w_keys[kind])]

    def l_anchors(self, kind):
        return tuple(float(a) for a in self.slice_of(kind).grids[0])

    def edge(self, kind):
        if kind not in self._edges:
            self._edges[kind] = edge_costs(self.memo, kind, self.w_keys[kind])
        return self._edges[kind]

    def vds_grid(self, kind):
        return tuple(float(a) for a in self.slice_of(kind).grids[2])

    def vsb_ref(self, kind):
        return float(self.slice_of(kind).grids[3][0])

    # ---------------------------------------------------------------- 곡선
    def curve(self, quantity, kind, L, vds=None, vsb=None):
        """`GmIdAxisCurve` 또는 None(정의 안 됨). `quantity` ∈ QUANTITY_FT·GAIN·VDSAT·IDU. vds 를 안 주면 기준 VDS 부터 위 격자점으로 올리며 처음 정의된 곡선."""
        vsb = self.vsb_ref(kind) if vsb is None else vsb
        fn = dict(_CURVE_FN)[quantity]
        if vds is not None:
            return self._try(fn, kind, L, vds, vsb)
        for v in self.vds_grid(kind):
            if v < self.edge(kind).vds_min_v:
                continue
            found = self._try(fn, kind, L, v, vsb)
            if found is not None:
                return found
        return None

    def _try(self, fn, kind, L, vds, vsb):
        try:
            return fn(self.memo, kind, self.w_keys[kind], float(L), float(vds), float(vsb))
        except _UNDEFINED:
            return None

    def ref_vds(self, kind, L):
        """(kind, L) 의 기준 VDS: vdsat 곡선이 처음 정의된 포화 경계 이상 격자점. 없으면 None."""
        key = (kind, float(L))
        if key not in self._ref:
            curve = self.curve(QUANTITY_VDSAT, kind, L)
            self._ref[key] = None if curve is None else curve.vds
        return self._ref[key]

    def bundle(self, kind, L, vds=None, vsb=None):
        """같은 (L, VDS, VSB) 의 곡선 묶음 {양: GmIdAxisCurve}. 하나라도 정의되지 않으면 None. (vds, vsb) 를 안 주면 기준 점(포화 경계 VDS, 첫 VS 격자점)."""
        vds = self.ref_vds(kind, L) if vds is None else vds
        if vds is None:
            return None
        out = {}
        for quantity, _fn in _CURVE_FN:
            curve = self.curve(quantity, kind, L, vds, vsb)
            if curve is None:
                return None
            out[quantity] = curve
        return out

    def assign(self, points):
        """소자별 동작점 {소자 이름: (VDS, VSB)} 를 정한다(`bundle_of` 가 쓴다). 소자 이름은 키일 뿐이다."""
        self.points = dict(points)

    def bundle_of(self, name, kind, L):
        """소자 `name` 의 동작점(`assign`)에서의 곡선 묶음. 동작점이 없거나 그 점에서 곡선이 정의되지 않으면 기준 점 묶음."""
        point = self.points.get(name)
        found = None if point is None else self.bundle(kind, L, point[0], point[1])
        return self.bundle(kind, L) if found is None else found

    def snap_up_vds(self, kind, target):
        """LUT VDS 격자 중 `target` 이상인 첫 점(없으면 마지막 점)."""
        grid = self.vds_grid(kind)
        return next((v for v in grid if v >= target), grid[-1])

    def snap_vds(self, kind, target):
        """LUT VDS 격자 중 `target` 에 가장 가까운 점(같으면 큰 쪽)."""
        grid = self.vds_grid(kind)
        return min(grid, key=lambda v: (abs(v - target), -v))

    def tol_vdsat(self, kind, L, vds):
        """VDSAT 허용오차 tol_vdsat(L, VDS 칸) -- L 을 감싸는 두 앵커와 VDS 가 든 격자 칸 중 정의된 것의 최댓값(보수). 표를 못 만들면 0."""
        key = (kind, float(L), float(vds))
        if key not in self._tol:
            try:
                table = tol_vdsat_table(self.memo, kind, self.w_keys[kind])
            except _UNDEFINED:
                self._tol[key] = 0.0
                return 0.0
            anchors = np.asarray(self.l_anchors(kind))
            vgrid = np.asarray(self.vds_grid(kind))
            i_hi = int(np.searchsorted(anchors, L, side="left"))
            rows = sorted({max(i_hi - 1, 0), min(i_hi, anchors.size - 1)})
            j_hi = int(np.searchsorted(vgrid, vds, side="left"))
            cols = sorted({max(j_hi - 1, 0), min(j_hi, vgrid.size - 1)})
            vals = [float(table.cells[i][k].vdsat_v) for i in rows for k in cols if table.cells[i][k].vdsat_v is not None]
            self._tol[key] = max(vals) if vals else 0.0
        return self._tol[key]

    # ---------------------------------------------------------------- 값 읽기
    def gm_id_range(self, bundle):
        """곡선 분지의 gm/ID 범위 (최솟값, 최댓값). 분지 맨 앞 마디가 gm/ID 정점이다."""
        g = np.asarray(bundle[QUANTITY_FT].gm_id, dtype=float)
        return float(g.min()), float(g.max())

    def value(self, bundle, quantity, g):
        """묶음의 `quantity` 를 gm/ID = g 에서 읽는다(idu·ft 는 log 보간, 나머지는 선형, QUANTITY_VGS 는 VGS 마디)."""
        if quantity == QUANTITY_VGS:
            curve = bundle[QUANTITY_FT]
            return at_gm_id(curve.gm_id, curve.vgs, g)
        curve = bundle[quantity]
        return at_gm_id(curve.gm_id, curve.values, g, log=quantity in _LOG_QUANTITIES)
