"""소자 용량 조회 -- 기준 LUT 용량 열을 소자 폭으로 비례 (설계 MOD1 2.8, DF-28).

진입점: `caps`.

* L 은 앵커 이산 키(계획 LR3 -- 기준 LUT L 축 = 슬라이스 L 축, 로드에서 확인). 보간은 (VGS, VDS, VS) 3축,
  CGG·CGD(·CGS·CGB) 는 선형공간(옛 B15 LOO 실측에서 CGG 만 선형이 이김 -- 같은 규칙 유지).
* 비례: 값 × W / `w_ref_m`(CapTable 채택 폭, `load_lut_set` 의 근거 규칙).
* 모델은 열 존재로 갈린다: CGS·CGB 열이 있으면 "lut_cgs_cgb", 없으면 "cgg_minus_cgd_at_gs"(cgs = cgg - cgd, cgb = 0).
* 축은 기준 LUT 축이다 -- VS 상한이 슬라이스보다 낮을 수 있고 그 밖은 실패(클램프 없음, U-27 재생성 전 상태를 숨기지 않음).
"""
from ._helpers_anchor import l_anchor_index
from ._helpers_interp import multilinear_interp_point_multi
from .axis_guard import check_axes
from .lut_types import AXES, Caps


def caps(memo, kind, L, vgs, vds, vsb, W):
    """총 폭 `W`(m) 소자의 `Caps`(F). memo 영역 point.

    실패: L 이 앵커가 아님·기준 LUT 축 밖 -> `SealViolationError`(context kind·table "cap"), kind 용량 표 없음 -> `KeyError`.
    """
    cap = memo.lut.cap_map[kind]
    context = (("kind", kind), ("table", "cap"))
    i = l_anchor_index(cap.grids[0], L, context)
    rest = (float(vgs), float(vds), float(vsb))
    W = float(W)
    check_axes(cap.grids[1:], AXES[1:], rest, context)

    def compute():
        full = cap.CGS is not None and cap.CGB is not None
        arrays = (cap.CGG[i], cap.CGD[i]) + ((cap.CGS[i], cap.CGB[i]) if full else ())
        vals = multilinear_interp_point_multi(cap.grids_list[1:], arrays, rest)
        scale = W / cap.w_ref_m
        cgg, cgd = vals[0] * scale, vals[1] * scale
        if full:
            return Caps(cgg, cgd, vals[2] * scale, vals[3] * scale, "lut_cgs_cgb")
        return Caps(cgg, cgd, cgg - cgd, 0.0, "cgg_minus_cgd_at_gs")

    return memo.lookup("point", "caps", (kind, i) + rest + (W,), compute)
