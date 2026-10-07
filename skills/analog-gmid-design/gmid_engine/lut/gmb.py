"""body 트랜스컨덕턴스 gmb -- 같은 보간면의 VS 방향 해석 미분 (설계 MOD1 2.8, 계획 N3.8 'MOD1 수치미분').

진입점: `gmb`.

조회점이 든 VS 칸 [vs_k, vs_k+1] (보간과 같은 `bisect_right - 1` 규칙, 마지막 격자점은 마지막 칸) 에서
ln ID 는 VS 에 대해 선형이므로 `d ln ID / d vsb = (lnID(vs_k+1) - lnID(vs_k)) / (vs_k+1 - vs_k)`
(L·VGS·VDS 는 조회점 값으로 보간). gmb = dID/dVBS = -dID/dVSB = -ID · d ln ID / d vsb. 스텝 상수 없음(격자 칸 = 스텝).
값은 슬라이스 폭 w_m 기준(A/V); 소자 총 폭 W 의 값은 부르는 쪽이 `× W / w_m`.
"""
import bisect
import math

from ._helpers_interp import multilinear_interp_point_multi
from .axis_guard import check_axes
from .lut_types import AXES


def gmb(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 (L, vgs, vds, vsb) 에서 gmb(A/V, 폭 w_m 기준). memo 영역 point.

    실패: 축 밖 -> `SealViolationError`(lut_axis_out_of_range), 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    point = (float(L), float(vgs), float(vds), float(vsb))
    check_axes(sl.grids, AXES, point, (("kind", kind), ("w_key", w_key)))

    def compute():
        vs = sl.grids_list[3]
        k = min(bisect.bisect_right(vs, point[3]) - 1, len(vs) - 2)
        lo = multilinear_interp_point_multi(sl.grids_list, (sl.log_ID,), point[:3] + (vs[k],))[0]
        hi = multilinear_interp_point_multi(sl.grids_list, (sl.log_ID,), point[:3] + (vs[k + 1],))[0]
        here = multilinear_interp_point_multi(sl.grids_list, (sl.log_ID,), point)[0]
        return -math.exp(here) * (hi - lo) / (vs[k + 1] - vs[k])

    return memo.lookup("point", "gmb", (kind, w_key) + point, compute)
