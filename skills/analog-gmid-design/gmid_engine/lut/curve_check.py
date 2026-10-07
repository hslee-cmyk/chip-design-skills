"""LUT 곡선 검사 -- 격자점 gm/ID 곡선의 분지 단조성·범위·gm/gds 최대 (설계 MOD1 2.3 `curve_report`, 계획 N3.7, GB4 입력).

진입점: `curve_report`.

격자점 값만 쓴다(보간 없음). 곡선 = 한 (L, VDS, VS) 의 VGS 축 gm/ID = exp(lnGM - lnID). ID·GM 에 0 이하 격자점이
있는 곡선(예: VDS = 0)은 gm/ID 가 정의되지 않아 세지 않고 `n_skipped` 로만 센다. 분지 규칙은 `_helpers_root`
(정점 index 부터 오른쪽). Hermite 칸 단조 위반 수(`n_hermite_nonmonotone`)는 로드 기록 `DcSlice.fc_ok_vgs`·`fc_ok_vds`
의 그 L 앵커 몫을 센다(DEC-87 FC 검사, 다시 계산하지 않는다).
"""
import numpy as np

from ._helpers_root import peak_index
from .lut_types import CurveReport, CurveRow


def _rows_of(sl):
    rows = []
    gm_id_all = np.exp(sl.log_GM - sl.log_ID)
    gm_gds_all = np.exp(sl.log_GM - sl.log_GDS)
    for i, L in enumerate(sl.grids[0]):
        on = sl.on_mask[i]
        curve_ok = on.all(axis=0)
        n_curves = n_nonmono = 0
        max_rise = gm_id_max = 0.0
        for k, s in zip(*np.nonzero(curve_ok)):
            g = gm_id_all[i, :, k, s]
            p = peak_index(g)
            rises = np.diff(g[p:])
            n_curves += 1
            gm_id_max = max(gm_id_max, float(g[p]))
            if rises.size and rises.max() > 0:
                n_nonmono += 1
                max_rise = max(max_rise, float(rises.max() / g[p]))
        gm_gds = gm_gds_all[i][on]
        n_fc_bad = int(np.count_nonzero(~sl.fc_ok_vgs[i]) + np.count_nonzero(~sl.fc_ok_vds[i]))
        rows.append(CurveRow(sl.kind, sl.w_key, L, n_curves, int(curve_ok.size - n_curves), n_nonmono, max_rise,
                             gm_id_max, float(gm_gds.max()) if gm_gds.size else 0.0, n_fc_bad))
    return rows


def curve_report(memo):
    """LutSet 전체의 `CurveReport`(행 = (kind, w_key, L 앵커)). memo 영역 derived."""
    lut = memo.lut

    def compute():
        rows = []
        for key in sorted(lut.slice_map):
            rows.extend(_rows_of(lut.slice_map[key]))
        return CurveReport(lut.fp, tuple(rows))

    return memo.lookup("derived", "curve_report", (), compute)
