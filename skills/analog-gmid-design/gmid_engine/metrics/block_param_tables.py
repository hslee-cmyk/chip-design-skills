"""블록 국소 모델의 소자 파라미터 표 -- LUT 곡선 API 에서 한 번만 조회해 격자 index 로 읽는다 (설계 41 §4.2 '소자 파라미터는 LUT memo 에서 한 번만 조회', 행 memo).

진입점: `ParamTables(memo, w_keys, grids)`  (`memo` = `lut.LutMemo`, `w_keys` = {kind: 폭 슬라이스 키}, `grids` = (L, VGS, VDS, VS) LUT 격자).

표 항목 (kind, L 앵커, VDS, VS) 마다 곡선 한 개를 `lut.intrinsic_gain_curve`(강반전 분지 VGS 마디, 마디의 gm/ID 와 gm/gds)와 `lut.gmb`(마디의 GMBS)로 만든다:
`x = gm/ID`, `y = gds/ID = (gm/ID) / (gm/gds)`, `z = gmb/ID` (모두 1/V, 전류 규모와 무관 -- 소자 gm = x·ID 등). 분지 밖 마디(곡선 정점 아래)와 곡선을 만들 수 없는 항목
(`lut_curve_undefined` 등 `SealViolationError`)은 NaN 이라 그 행은 유효하지 않다. 항목은 처음 읽을 때 만들고(지연) 배열은 격자 크기로 정해져 상한이 있다(행 memo 상한 =
kind 마다 |L|·|VDS|·|VS|·|VGS|·3 개 실수 -- LUT 격자에서 유도). 조회 호출은 곡선 memo(`LutMemo` curve 영역)에 의해서도 중복되지 않는다. `loads` = 만든 곡선 수.
"""
import numpy as np

from gmid_engine.core import SealViolationError
from gmid_engine.lut import gmb, intrinsic_gain_curve, op_point


PARAMETERS = ("x", "y", "z")             # gm/ID, gds/ID, gmb/ID


class ParamTables:
    def __init__(self, memo, w_keys, grids):
        self._memo = memo
        self._w_keys = dict(w_keys)
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

    def _load(self, kind, i_l, i_d, i_s):
        values, loaded = self._kind_arrays(kind)
        loaded[i_l, i_d, i_s] = True
        w_key = self._w_keys[kind]
        w_m = self._memo.lut.slice_map[(kind, w_key)].w_m
        length, vds, vsb = float(self.grids[0][i_l]), float(self.grids[2][i_d]), float(self.grids[3][i_s])
        try:
            curve = intrinsic_gain_curve(self._memo, kind, w_key, length, vds, vsb)
            nodes = np.searchsorted(self.grids[1], np.asarray(curve.vgs, dtype=float))
            ids = [op_point(self._memo, kind, w_key, length, float(v), vds, vsb).IDu * w_m / length for v in curve.vgs]
            body = [gmb(self._memo, kind, w_key, length, float(v), vds, vsb) for v in curve.vgs]
        except SealViolationError:
            return
        self.loads += 1
        x = np.asarray(curve.gm_id, dtype=float)
        values[i_l, i_d, i_s, nodes, 0] = x
        values[i_l, i_d, i_s, nodes, 1] = x / np.asarray(curve.values, dtype=float)
        values[i_l, i_d, i_s, nodes, 2] = np.asarray(body, dtype=float) / np.asarray(ids, dtype=float)

    def lookup(self, kind, i_l, i_d, i_s, i_v):
        """같은 모양 정수 배열 (L, VDS, VS, VGS index) -> (x, y, z) 배열 셋. 유효하지 않은 항목은 NaN."""
        values, loaded = self._kind_arrays(kind)
        triples = np.unique(np.stack([np.asarray(i_l).ravel(), np.asarray(i_d).ravel(), np.asarray(i_s).ravel()], axis=1), axis=0)
        for a, b, c in triples:
            if not loaded[a, b, c]:
                self._load(kind, int(a), int(b), int(c))
        picked = values[i_l, i_d, i_s, i_v]
        return picked[..., 0], picked[..., 1], picked[..., 2]
