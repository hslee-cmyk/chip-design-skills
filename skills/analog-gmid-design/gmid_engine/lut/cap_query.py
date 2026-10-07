"""소자 용량 조회 -- 기준 LUT 용량 열을 소자 폭으로 비례 (설계 MOD1 2.8, DF-28).

진입점: `caps`.

* L 은 앵커이거나 같은 모델 bin 안 두 앵커 사이(`l_position`, lut/CONTRACT.md 4.0 -- 기준 LUT L 축 = 슬라이스 L 축,
  로드에서 확인; bin 지도는 채택 폭과 같은 슬라이스의 것). 보간은 (L, VGS, VDS, VS) 모든 축 선형(`linear_point`,
  DEC-87 축별 표에서 용량은 기울기 열이 없어 선형), CGG·CGD(·CGS·CGB) 는 선형공간(옛 B15 LOO 실측에서 CGG 만 선형이
  이김 -- 같은 규칙 유지).
* 비례: 값 × W / `w_ref_m`(CapTable 채택 폭, `load_lut_set` 의 근거 규칙).
* 모델은 열 존재로 갈린다: CGS·CGB 열이 있으면 "lut_cgs_cgb", 없으면 "cgg_minus_cgd_at_gs"(cgs = cgg - cgd, cgb = 0).
* 축은 기준 LUT 축이다 -- VS 상한이 슬라이스보다 낮을 수 있고 그 밖은 실패(클램프 없음, U-27 재생성 전 상태를 숨기지 않음).
"""
from ._helpers_anchor import l_position
from ._helpers_interp import linear_point
from .axis_guard import check_axes
from .lut_types import AXES, Caps


def caps(memo, kind, L, vgs, vds, vsb, W):
    """총 폭 `W`(m) 소자의 `Caps`(F). memo 영역 point.

    실패: L 이 앵커도 같은 bin 보간도 아님·기준 LUT 축 밖 -> `SealViolationError`(context kind·table "cap"),
    kind 용량 표 없음 -> `KeyError`.
    """
    cap = memo.lut.cap_map[kind]
    context = (("kind", kind), ("table", "cap"))
    lo, hi, l_val = l_position(cap.grids[0], cap.l_bins, L, context)
    rest = (float(vgs), float(vds), float(vsb))
    W = float(W)
    check_axes(cap.grids[1:], AXES[1:], rest, context)

    def compute():
        part = slice(lo, hi + 1)
        full = cap.CGS is not None and cap.CGB is not None
        arrays = (cap.CGG[part], cap.CGD[part]) + ((cap.CGS[part], cap.CGB[part]) if full else ())
        vals = linear_point((cap.grids[0][part],) + tuple(cap.grids_list[1:]), arrays, (l_val,) + rest)
        scale = W / cap.w_ref_m
        cgg, cgd = vals[0] * scale, vals[1] * scale
        if full:
            return Caps(cgg, cgd, vals[2] * scale, vals[3] * scale, "lut_cgs_cgb")
        return Caps(cgg, cgd, cgg - cgd, 0.0, "cgg_minus_cgd_at_gs")

    return memo.lookup("point", "caps", (kind, lo, hi, l_val) + rest + (W,), compute)
