"""body 트랜스컨덕턴스 gmb -- 같은 보간면의 VS 방향 해석 미분 (설계 MOD1 2.8, 계획 N3.8 'MOD1 수치미분').

진입점: `gmb`.

L 앵커 하나에서(L 보간 없음, 계획 LR3) 조회점이 든 VS 칸 [vs_k, vs_k+1] (보간과 같은 `bisect_right - 1` 규칙, 마지막
격자점은 마지막 칸) 에서 ln ID 는 VS 에 대해 선형이므로 `d ln ID / d vsb = (lnID(vs_k+1) - lnID(vs_k)) / (vs_k+1 - vs_k)`
(VGS·VDS 는 조회점 값으로 보간). gmb = dID/dVBS = -dID/dVSB = -ID · d ln ID / d vsb. 스텝 상수 없음(격자 칸 = 스텝).
값은 슬라이스 폭 w_m 기준(A/V); 소자 총 폭 W 의 값은 부르는 쪽이 `× W / w_m`.
"""
import bisect
import math

from ._helpers_anchor import l_anchor_index
from ._helpers_interp import multilinear_interp
from .axis_guard import check_axes
from .lut_types import AXES


def gmb(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 L 앵커 `L`, (vgs, vds, vsb) 에서 gmb(A/V, 폭 w_m 기준). memo 영역 point.

    실패: L 이 앵커가 아님·축 밖 -> `SealViolationError`, 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    i = l_anchor_index(sl.grids[0], L, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(sl.grids[1:], AXES[1:], rest, context)

    def compute():
        grids = sl.grids_list[1:]
        vs = grids[2]
        k = min(bisect.bisect_right(vs, rest[2]) - 1, len(vs) - 2)
        pts = (rest[:2] + (vs[k],), rest[:2] + (vs[k + 1],), rest)
        lo, hi, here = multilinear_interp(grids, sl.log_ID[i], pts)
        return -math.exp(here) * (hi - lo) / (vs[k + 1] - vs[k])

    return memo.lookup("point", "gmb", (kind, w_key, i) + rest, compute)
