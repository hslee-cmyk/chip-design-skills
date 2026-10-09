"""LUT 곡선 검사 → 해법 매핑 (설계 41 §4.1, D-GB4a; GB4 단계 A5 `curve_checks`).

진입점: `curve_checks(lut) -> CurveChecks`  (`lut` = `lut.LutSet`).

as-built `DcSlice` 의 칸 분류 자료(`on_mask`·`vds_slope_ok`·`vs_slope_ok` = 끝 기울기 정의, `fc_ok_vgs`·`fc_ok_vds`·`fc_ok_vs` = Fritsch–Carlson 단조 조건, lut CONTRACT 1.4·4.2)를
소비해 (kind, w_key, 축)마다 칸을 세 갈래로 가른다.
* **단조 Hermite 칸**(`CELL_HERMITE`, 끝 기울기 둘 다 정의 + FC 조건 참) -> 역산 허용(`METHOD_INVERSE`; `vgs_for_gm_id`·`vgs_for_current_density`).
* **Fritsch–Carlson 위반 칸**(`CELL_FC_VIOLATION`) -> `METHOD_GRID_ONLY`: 그 칸은 격자 전수만 쓴다. 역산은 `lut_hermite_nonmonotone_cell` 로 실패시키고(lut `vgs_for_gm_id`),
  순방향 조회는 선형 폴백(사유 `OpPoint.fallbacks`, DEC-87)이다. 위반 칸마다 `CurveCheck` 행(kind, w_key, L, VDS, VS, 축, 칸 index)을 낸다.
* **끝 기울기 미정의 칸**(`CELL_SLOPE_UNDEFINED`, 꺼진 점 ID ≤ 0 등) -> 선형 칸(역산 없음). 개수만 `SliceCurveCheck` 에 두고 행으로 내지 않는다(꺼진 점 열이 슬라이스마다 수천 칸이라
  행 수가 격자 크기를 따라가기 때문 -- 칸 판정은 `on_mask` 가 정본이다).
* **단위 불일치**: 로드 거부(`SchemaRejectedError` reason `lut_unit_mismatch`, lut `load_lut_set` 1.4). 로드된 LUT 에는 없으므로 `n_unit_mismatch` 는 늘 0 이다.

격자 통계(전 슬라이스 배열 한 번 훑기)이고 보간 조회가 아니다 -- 보간이 필요한 값은 lut 곡선 API 를 쓴다. 같은 LUT 면 결과가 같다(결정론, 시간 무관).
소비처: `achievability`(보고·`Achievability.curves`), U15 층 0 국소 후보의 역산 가능 칸 판정(41 §5.3).
"""
import numpy as np

from gmid_engine.lut import AXES

from .achievability_types import (
    AXIS_VDS,
    AXIS_VGS,
    AXIS_VS,
    CELL_FC_VIOLATION,
    METHOD_GRID_ONLY,
    CurveCheck,
    CurveChecks,
    SliceCurveCheck,
)


def _cells(defined, fc_ok, axis):
    """칸(축 `axis` 의 index k, k+1)마다 (Hermite 칸 마스크, 위반 마스크). `defined`·`fc_ok` 는 4축 배열(fc_ok 는 그 축 길이 − 1)."""
    lo = np.take(defined, np.arange(defined.shape[axis] - 1), axis=axis)
    hi = np.take(defined, np.arange(1, defined.shape[axis]), axis=axis)
    hermite = lo & hi
    return hermite, hermite & ~np.asarray(fc_ok, dtype=bool)


def _slice_axes(sl):
    all_off = np.zeros(sl.on_mask.shape, dtype=bool)
    vs_ok = all_off if sl.vs_slope_ok is None else np.asarray(sl.vs_slope_ok, dtype=bool)
    vs_fc = np.ones(sl.on_mask.shape[:3] + (sl.on_mask.shape[3] - 1,), dtype=bool) if sl.fc_ok_vs is None else sl.fc_ok_vs
    on = np.asarray(sl.on_mask, dtype=bool)
    return ((AXIS_VGS, AXES.index(AXIS_VGS), on, sl.fc_ok_vgs),
            (AXIS_VDS, AXES.index(AXIS_VDS), np.asarray(sl.vds_slope_ok, dtype=bool), sl.fc_ok_vds),
            (AXIS_VS, AXES.index(AXIS_VS), vs_ok, vs_fc))


def curve_checks(lut):
    summaries, rows = [], []
    for (kind, w_key), sl in sorted(lut.slice_map.items()):
        grid_l, grid_vgs, grid_vds, grid_vs = (np.asarray(g, dtype=float) for g in sl.grids)
        for axis_name, axis, defined, fc_ok in _slice_axes(sl):
            hermite, violation = _cells(defined, fc_ok, axis)
            summaries.append(SliceCurveCheck(kind, w_key, axis_name, int(hermite.size), int(hermite.sum()), int(violation.sum()),
                                             int((~hermite).sum())))
            for i_l, i_vgs, i_vds, i_vs in np.argwhere(violation):
                at = (int(i_l), int(i_vgs), int(i_vds), int(i_vs))
                rows.append(CurveCheck(kind, w_key, float(grid_l[at[0]]), float(grid_vds[at[2]]), float(grid_vs[at[3]]), axis_name,
                                       at[axis], CELL_FC_VIOLATION, METHOD_GRID_ONLY))
    rows.sort(key=lambda r: (r.kind, r.w_key, r.axis, r.L, r.vds, r.vs, r.cell))
    return CurveChecks(tuple(summaries), tuple(rows), 0, lut.fp)
