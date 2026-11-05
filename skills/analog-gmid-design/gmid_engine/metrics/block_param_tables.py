"""블록 국소 모델의 소자 파라미터 표 -- LUT 곡선 API 에서 한 번만 조회해 격자 index 로 읽는다 (설계 41 §4.2 '소자 파라미터는 LUT memo 에서 한 번만 조회', 행 memo).

진입점: `ParamTables(memo, grids, side, z_side)`  (`memo` = `lut.LutMemo`, `grids` = (L, VGS, VDS, VS) LUT 격자, `side` ∈ {"upper", "lower"}, `z_side` ∈ {"min", "max"}).

**W 가 없는 단계의 포락 표**(WB-1, 설계 40 §3.7-A 12): 칸마다 도달 가능한 슬라이스(`reachable_slices(lut, kind, L)`) 전부의 행을 만들어(조회 불능 사유 다섯이면 그 슬라이스는 뺀다) 합친다:
upper = x(gm/ID) 최댓값·y(gds/ID) 최솟값, lower = x 최솟값·y 최댓값, z(gmb/ID) = `z_side` 쪽(`min`/`max`). 행 값이 정의되지 않은 슬라이스는 그 칸 포락에서 빼고 남는 항이 없으면 NaN.
슬라이스 수는 격자 곱 Π 에 들지 않는다(표 크기는 격자 크기).

표 항목 (kind, L 앵커, VDS, VS) 마다 LUT 파생 행 `lut.derived(memo, "param_row", ...)`(강반전 분지 VGS 마디의 x·y·z -- LUT memo 가 담는다, 설계 40 §2.4.6 v1.9.1 D10)을 읽는다:
`x = gm/ID`, `y = gds/ID = (gm/ID) / (gm/gds)`, `z = gmb/ID` (모두 1/V, 전류 규모와 무관 -- 소자 gm = x·ID 등). 분지 밖 마디(곡선 정점 아래)와 곡선을 만들 수 없는 항목
(`lut_curve_undefined` 등 `SealViolationError`)은 NaN 이라 그 행은 유효하지 않다. 항목은 처음 읽을 때 만들고(지연) 배열은 격자 크기로 정해져 상한이 있다(행 memo 상한 =
kind 마다 |L|·|VDS|·|VS|·|VGS|·3 개 실수 -- LUT 격자에서 유도). 조회 호출은 곡선 memo(`LutMemo` curve 영역)에 의해서도 중복되지 않는다. `loads` = 만든 곡선 수.

`lookup_at_l(kind, l_m, i_d, i_s, i_v)` = 앵커가 아닌 L(m)의 같은 파생 행(`derived(memo, "param_row", ...)` -- LUT memo 가 담는다, 이 객체는 새 저장 자리를 두지 않는다)을 읽어 VGS 마디 i_v 의
(x, y, z); 정의 안 되는 항목은 NaN. `same_l_bin(kind, i_a, i_b)` = 두 L 앵커가 같은 L bin 에 드는가(LUT `l_bins.anchor_bin`; bin 지도가 없으면 앵커 사이 값이 정의되지 않아 거짓).
"""
import numpy as np

from gmid_engine.lut import derived, is_slice_gap, reachable_slices
from gmid_engine.core import SealViolationError


PARAMETERS = ("x", "y", "z")             # gm/ID, gds/ID, gmb/ID


SIDES = ("upper", "lower")
Z_SIDES = ("min", "max")


class ParamTables:
    def __init__(self, memo, grids, side, z_side):
        if side not in SIDES or z_side not in Z_SIDES:
            raise ValueError("ParamTables: side 는 %s, z_side 는 %s 중 하나" % (SIDES, Z_SIDES))
        self._memo = memo
        self._side, self._z_side = side, z_side
        self.grids = tuple(np.asarray(g, dtype=float) for g in grids)
        self.shape = tuple(len(g) for g in self.grids)                   # (nL, nVGS, nVDS, nVS)
        self._values = {}
        self._loaded = {}
        self.vds_of_vgs = np.asarray([int(np.argmin(np.abs(self.grids[2] - v))) for v in self.grids[1]], dtype=int)
        self.loads = 0

    def _kind_arrays(self, kind):
        if kind not in self._values:
            n_l, n_v, n_d, n_s = self.shape
            self._values[kind] = np.full((n_l, n_d, n_s, n_v, len(PARAMETERS)), np.nan)
            self._loaded[kind] = np.zeros((n_l, n_d, n_s), dtype=bool)
        return self._values[kind], self._loaded[kind]

    def _envelope(self, kind, l_value, vds, vs):
        """(VGS 마디 수, 3) 포락 표(정의 안 되면 NaN): 도달 가능한 슬라이스 행을 합친다. 한 슬라이스도 행을 못 내면 None."""
        table, found = np.full((self.shape[1], len(PARAMETERS)), np.nan), False
        for key in reachable_slices(self._memo.lut, kind, l_value):
            try:
                row = derived(self._memo, "param_row", kind, key, l_value, vds, vs)
            except SealViolationError as exc:
                if is_slice_gap(exc):
                    continue
                raise
            if row is None:
                continue
            vgs, x, y, z = (np.asarray(part, dtype=float) for part in row)
            nodes = np.searchsorted(self.grids[1], vgs)
            if nodes.size and (nodes.max() >= self.shape[1] or not np.array_equal(self.grids[1][nodes], vgs)):
                # 표 격자 `grids[1]`(기준 폭 슬라이스의 VGS 축)과 이 슬라이스의 VGS 마디가 다르면 index 대응이 거짓이다 -- 슬라이스마다 축 일치를 재고 다르면 거부한다(s3)
                raise SealViolationError(devices=(), detail={"reason": "slice_vgs_grid_mismatch", "kind": kind, "w_key": key, "L": l_value})
            one =np.full((self.shape[1], len(PARAMETERS)), np.nan)
            one[nodes, 0], one[nodes, 1], one[nodes, 2] = x, y, z
            upper = self._side == "upper"                                  # x: upper = 최댓값, y: upper = 최솟값 (lower 는 반대)
            table[:, 0] = (np.fmax if upper else np.fmin)(table[:, 0], one[:, 0])
            table[:, 1] = (np.fmin if upper else np.fmax)(table[:, 1], one[:, 1])
            table[:, 2] = (np.fmin if self._z_side == "min" else np.fmax)(table[:, 2], one[:, 2])
            found = True
        return table if found else None

    def _load(self, kind, i_l, i_d, i_s):
        values, loaded = self._kind_arrays(kind)
        loaded[i_l, i_d, i_s] = True
        table = self._envelope(kind, float(self.grids[0][i_l]), float(self.grids[2][i_d]), float(self.grids[3][i_s]))
        if table is None:
            return
        self.loads += 1
        values[i_l, i_d, i_s] = table

    def lookup(self, kind, i_l, i_d, i_s, i_v):
        """같은 모양 정수 배열 (L, VDS, VS, VGS index) -> (x, y, z) 배열 셋. 유효하지 않은 항목은 NaN."""
        values, loaded = self._kind_arrays(kind)
        triples = np.unique(np.stack([np.asarray(i_l).ravel(), np.asarray(i_d).ravel(), np.asarray(i_s).ravel()], axis=1), axis=0)
        for a, b, c in triples:
            if not loaded[a, b, c]:
                self._load(kind, int(a), int(b), int(c))
        picked = values[i_l, i_d, i_s, i_v]
        return picked[..., 0], picked[..., 1], picked[..., 2]

    def lookup_at_l(self, kind, l_m, i_d, i_s, i_v):
        """같은 모양 배열 (L m, VDS, VS, VGS index) -> (x, y, z) 배열 셋. L 은 앵커 사이 값. 유효하지 않은 항목은 NaN."""
        l_arr, i_d, i_s, i_v = np.broadcast_arrays(np.asarray(l_m, dtype=float), np.asarray(i_d), np.asarray(i_s), np.asarray(i_v))
        out = np.full(l_arr.shape + (len(PARAMETERS),), np.nan)
        keys = np.unique(np.stack([l_arr.ravel(), i_d.ravel(), i_s.ravel()], axis=1), axis=0)
        for l_value, a, b in keys:
            table = self._envelope(kind, float(l_value), float(self.grids[2][int(a)]), float(self.grids[3][int(b)]))
            if table is None:
                continue
            hit = (l_arr == l_value) & (i_d == a) & (i_s == b)
            out[hit] = table[i_v[hit]]
        return out[..., 0], out[..., 1], out[..., 2]

    def same_l_bin(self, kind, i_a, i_b):
        """L 앵커 index 둘이 같은 L bin 인가."""
        bins = self._memo.lut.slice_map[(kind, self._memo.lut.cap_map[kind].w_key)].l_bins.anchor_bin
        return bool(bins) and bins[int(i_a)] == bins[int(i_b)]
