"""포화 전압 VDsat 조회 -- LUT VDSAT 열(BSIM `@m[vdsat]`, 오라클과 같은 양) 보간 (lut/CONTRACT.md 4.3, r6; sizing 계약 12절 O1).

진입점: `vdsat`.

* 열 출처: `column_source`(슬라이스 열 우선, 아니면 같은 폭 키의 기준 LUT 열, 아니면 `lut_column_unavailable` -- 다른 폭 값으로
  대신하지 않는다). LUT v2 에서는 기준 LUT(W = w_ref, 폭 키 = `CapTable.w_key`)에만 있다.
* 보간: (L, VGS, VDS, VS) **모든 축 선형**(`linear_point`), 값 공간(VDSAT > 0 이고 매끈 -- 로그 불필요). VDSAT 의 도함수 열이
  LUT 에 없으므로 Hermite 를 쓸 근거가 없다: 2점 cubic-Hermite 는 끝 기울기 자료가 있어야 하고(DEC-87 은 저장 GM/ID·GDS/ID 가
  ln ID 의 정확한 편미분이라서 Hermite 를 썼다), 격자 차분으로 기울기를 지어내면 그 기울기 자체가 새 추정이다. 오차는
  같은 방법(선형) LOO 로 잰다(`tol_vdsat_table`).
* L 은 4.0 규칙(앵커 또는 같은 bin 안 두 앵커 사이, bin 지도 = 그 표의 지도). 축 밖은 실패(클램프 없음). 축은 그 열 표의 축.
"""
from ._helpers_anchor import l_position
from ._helpers_columns import column_source
from ._helpers_interp import linear_point
from .axis_guard import check_axes
from .lut_types import AXES


def vdsat(memo, kind, w_key, L, vgs, vds, vsb):
    """(kind, w_key) 의 `L`, (vgs, vds, vsb) 에서 VDsat(V, 크기). memo 영역 point.

    실패: 열 없음 -> `SealViolationError` `lut_column_unavailable`, L 이 앵커도 같은 bin 보간도 아님·축 밖 ->
    `SealViolationError`(op_point 와 같은 사유, context 에 `table` = 열 출처), 슬라이스 없음 -> `KeyError`.
    """
    src = column_source(memo.lut, kind, w_key, "VDSAT")
    context = (("kind", kind), ("table", src.origin), ("w_key", w_key))
    lo, hi, l_val = l_position(src.grids[0], src.l_bins, L, memo.lut.spec.manufacturing_grid_m, memo.lut.bin_rule, context)
    rest = (float(vgs), float(vds), float(vsb))
    check_axes(src.grids[1:], AXES[1:], rest, context)

    def compute():
        part = slice(lo, hi + 1)
        (value,) = linear_point((src.grids[0][part],) + tuple(src.grids[1:]), (src.array[part],), (l_val,) + rest)
        return float(value)

    return memo.lookup("point", "vdsat", (kind, w_key, lo, hi, l_val) + rest, compute)
