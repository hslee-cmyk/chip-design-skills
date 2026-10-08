"""gm/ID 축 곡선 표 공용 helper -- `ft_curve`·`intrinsic_gain_curve`·`vdsat_curve`·`idu_curve` 가 같은 분지·마디·memo 규칙을 쓴다
(설계 40 §2.3, 41 §6, lut/CONTRACT.md 4.5).

곡선 = 고정 (L, VDS, VS) 의 `gm_id_curve`(op_point 와 같은 곡면). 표의 마디는 **강반전 분지**(VGS ≥ 곡선 정점 -- gm/ID 최댓값 마디)의 VGS
격자 마디다: 값은 그 마디에서 LUT 가 말하는 양이라 새 추정이 없고, 마디 사이는 소비자가 `op_point` 등으로 읽는다. 곡선에 정점 아래가 아닌
분지 안에 정의 안 된 마디(gm/ID NaN)가 있으면 `lut_curve_undefined` 로 실패한다(역산 함수와 같은 규칙). `monotone` = 분지에서 gm/ID 가 엄격히
감소(그러면 gm/ID 축으로 값을 역산할 수 있다 -- 아니면 소비자는 마디 전수로 쓴다, 41 §4.1 해법 매핑).
"""
import numpy as np

from ._helpers_fail import seal_violation
from .gm_id_curve import gm_id_curve
from .lut_types import CURVE_QUANTITIES, GmIdAxisCurve


def axis_curve(memo, quantity, kind, w_key, L, vds, vsb, node_values):
    """`quantity`(`CURVE_QUANTITIES` 이름)의 `GmIdAxisCurve`. `node_values(curve, nodes)` = 분지 마디 index 배열 `nodes` 의 값 배열을 내는
    함수(부르는 쪽이 그 양의 정의를 가진다). memo 영역 curve(같은 인자 1회)."""
    if quantity not in CURVE_QUANTITIES:
        raise ValueError("axis_curve: quantity 는 %s 중 하나" % (CURVE_QUANTITIES,))
    L, vds, vsb = float(L), float(vds), float(vsb)
    curve = gm_id_curve(memo, kind, w_key, L, vds, vsb)

    def compute():
        g = curve.gm_id_vals
        detail = dict(kind=kind, w_key=w_key, quantity=quantity, L=L, vds=vds, vsb=vsb)
        if not np.isfinite(g).any():
            raise seal_violation("lut_curve_undefined", n_undefined=int(g.size), **detail)
        p = int(np.nanargmax(g))
        nodes = np.arange(p, g.size)
        undefined = int(np.count_nonzero(~np.isfinite(g[nodes])))
        if undefined:
            raise seal_violation("lut_curve_undefined", n_undefined=undefined, **detail)
        arrays = (g[nodes], np.asarray(node_values(curve, nodes), dtype=float), curve.vgs_grid[nodes], curve.cell_ok[p:])
        for arr in arrays:
            arr.setflags(write=False)
        return GmIdAxisCurve(quantity, kind, w_key, L, vds, vsb, arrays[0], arrays[1], arrays[2], arrays[3],
                             bool(np.all(np.diff(arrays[0]) < 0)))

    return memo.lookup("curve", quantity + "_curve", (kind, w_key, L, vds, vsb), compute)
