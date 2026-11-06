"""슬라이스별 tol 표 구성 (WB-1, interface §8 J-6) -- `widths` 의 모든 (kind, 슬라이스 키)에 tol_V·tol_VDsat 표를 만든다.

진입점: `build_slice_tables`.

`build_slice_tables(memo) -> int`: kind 마다 `widths(lut, kind)` 키마다 `tol_v_table`·`tol_vdsat_table` 를 부른다(memo derived 영역 + 디스크 표 캐시 `TableCache`,
같은 표는 다시 계산하지 않는다). VDSAT 열이 그 슬라이스에도 기준 LUT 에도 없으면(`column_source(required=False)` 가 None) tol_VDsat 표는 만들지 않는다 -- 열이 없는 LUT 의
VDSAT 조회는 어차피 `lut_column_unavailable` 로 끝나므로 표를 미리 만들 대상이 없다(조용한 대체값 없음). 반환 = 부른 표 수.
호출 자리 = memo 를 확정하는 자리(`build_kernel_context`, `_wire_sweep_memo` 교체 직후).
"""
from ._helpers_columns import column_source
from .tolerance import tol_v_table
from .vdsat_tolerance import tol_vdsat_table
from .widths import widths


def build_slice_tables(memo):
    """슬라이스별 tol 표를 모두 만들고(memo·디스크 캐시에 적재) 만든 표 수를 돌려준다."""
    count = 0
    for kind in sorted({k for (k, _key) in memo.lut.slice_map}):
        for key in widths(memo.lut, kind):
            tol_v_table(memo, kind, key)
            count += 1
            if column_source(memo.lut, kind, key, "VDSAT", required=False) is not None:
                tol_vdsat_table(memo, kind, key)
                count += 1
    return count
