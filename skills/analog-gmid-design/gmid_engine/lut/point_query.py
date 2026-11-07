"""동작점 1점 조회 -- 축별 보간(DEC-87)으로 IDu·gm/ID·gm/gds·gds/W·vth (설계 MOD1 2.3, lut/CONTRACT.md 4.2).
L 은 앵커이거나 같은 모델 bin 안 두 앵커 사이만(lut/CONTRACT.md 4.0).

진입점: `op_point`.

* ln ID: 조회 VGS 가 든 VGS 칸 [a, a+1] (`cell` 규칙) 의 두 마디 값·기울기(`node_values` -- VDS Hermite, L·VS 선형)로
  VGS Hermite. gm/ID = 그 Hermite 의 VGS 미분(따로 보간하지 않는다). 두 마디 중 기울기 자료가 정의되지 않은 것이
  있거나 그 VGS 칸이 단조 위반(로드 기록 `fc_ok_vgs`)이면 칸 안쪽 점은 VGS 방향 선형(격자 마디는 저장값 그대로, 폴백 없음)(gm/ID = 그 칸 직선의 기울기).
* [r7] VS 축도 GMBS 열이 있는 슬라이스에서 Hermite(기울기 −GMBS/ID, `node_values`). Hermite 가 가능한 칸인데 선형으로 간 축은
  `OpPoint.fallbacks` 에 ((축, 사유), ...) 로 남긴다(사유 "slope_undefined"·"fc_violation" -- 조용한 선형 폴백 금지, DEC-87 FC 정책).
* ln GDS·VTH: 모든 축 선형(`linear_point`, ln GDS 는 로그공간). gm/gds = gm/ID · exp(ln ID − ln GDS).
* 정규화: `IDu = ID·L / w_m`(L = 앵커 값 또는 보간 조회 L), `gds_per_w = GDS / w_m`.
"""
import math

from ._helpers_anchor import l_position
from ._helpers_interp import REASON_FC, REASON_SLOPE, cell, hermite, linear_point, node_values
from .axis_guard import check_axes
from .lut_types import AXES, OpPoint


def slice_l_position(memo, kind, w_key, L):
    """(kind, w_key) 슬라이스의 L 위치 판정 `(lo, hi, l_value)` -- `op_point` 가 L 단계에서 부르는 판정 그 함수(전압 인자 없음, 조회 0).

    앵커면 `(i, i, 앵커 값)`, 같은 모델 bin 안 두 앵커 사이면 `(k - 1, k, L)`. 실패 = `l_position` 사유(CONTRACT 4.0) -- `is_slice_gap` 이 판정한다. 폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    return l_position(sl.grids[0], sl.l_bins, L, memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule, (("kind", kind), ("w_key", w_key)))


def op_point(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 슬라이스의 `L`, (vgs, vds, vsb) 동작점 `OpPoint`. memo 영역 point.

    실패: L 이 앵커도 같은 bin 보간도 아님·축 밖 -> `SealViolationError`(CONTRACT 4.0 사유 / lut_axis_out_of_range),
    폭 키 없음 -> `KeyError`.
    """
    sl = memo.lut.slice_map[(kind, w_key)]
    context = (("kind", kind), ("w_key", w_key))
    lo, hi, l_val = slice_l_position(memo, kind, w_key, L)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(sl.grids[1:], AXES[1:], rest, context)

    def compute():
        vgs_grid = sl.grids[1]
        a, t = cell(vgs_grid, rest[0])
        v, s, cell_fc_ok, fallbacks = node_values(sl, lo, hi, l_val, rest[1], rest[2], range(a, a + 2))
        h = vgs_grid[a + 1] - vgs_grid[a]
        if t in (0.0, 1.0):                  # 격자 마디: 저장값 그대로(4.2) -- 이웃 칸의 FC 위반은 이 점과 무관하다
            hermite_vgs = bool(math.isfinite(s[int(t)]))
        else:
            hermite_vgs = math.isfinite(s[0]) and math.isfinite(s[1]) and bool(cell_fc_ok[0])
        if not hermite_vgs:
            fallbacks = tuple(sorted(set(fallbacks) | {("VGS", REASON_FC if math.isfinite(s[0] + s[1]) else REASON_SLOPE)}))
        if hermite_vgs:
            if t in (0.0, 1.0):              # 격자 마디: Hermite 의 끝 값·끝 기울기 그 자체(반올림 없이)
                end = int(t)
                log_id, gm_id = float(v[end]), float(s[end])
            else:
                log_id, gm_id = (float(x) for x in hermite(v[0], v[1], s[0], s[1], h, t))
        else:
            log_id, gm_id = float(v[0] + t * (v[1] - v[0])), float((v[1] - v[0]) / h)
        part = slice(lo, hi + 1)
        log_gds, vth = linear_point((sl.grids[0][part],) + tuple(sl.grids[1:]),
                                    (sl.log_GDS[part], sl.VTH[part]), (l_val,) + rest)
        return OpPoint(
            math.exp(log_id) * l_val / sl.w_m,
            gm_id,
            gm_id * math.exp(log_id - log_gds),
            math.exp(log_gds) / sl.w_m,
            vth,
            fallbacks,
        )

    return memo.lookup("point", "op_point", (kind, w_key, lo, hi, l_val) + rest, compute)
