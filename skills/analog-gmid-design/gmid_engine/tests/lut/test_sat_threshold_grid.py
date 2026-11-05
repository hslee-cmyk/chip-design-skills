"""`sat_threshold_grid(memo, kind, w_key) -> ndarray | None` -- interface card 20261104-hcs §1 (S6).

oracle (b): 격자 입구 원소 = npz 의 VDSAT 배열(sizing conftest `r4_arrays`, 파일에 쓴 그 식)을 직접 읽은 값. 격자점에서 `sat_threshold(...)`
는 저장값 그대로(lut 4.3 '격자점에서는 저장값 그대로')라 같은 값이다. 축 순서 (L, VGS, VDS, VS) 는 비대칭 모양(2, 17, 9, 11)로 가린다.
열 출처 세 가지: 슬라이스 열 / 기기준 LUT(cap.npz) 열만 / 한 kind 는 슬라이스, 다른 kind 는 기준 LUT.
"""
import numpy as np
import pytest

import gmid_engine.lut as lutmod

from sizing.conftest import R4_GRIDS, W_KEY, r4_arrays, write_r4_lut

from .hcs_cases import memo_of

SHAPE = tuple(len(g) for g in R4_GRIDS)
CASES = {
    "slice_column": dict(),
    "cap_column_only": dict(vdsat=(), cap_vdsat=("nmos", "pmos")),
    "mixed": dict(vdsat=("nmos",), cap_vdsat=("pmos",)),
}


@pytest.mark.parametrize("case", sorted(CASES))
@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sat_threshold_grid_entries_equal_sat_threshold_at_every_grid_point(tmp_path, case, kind):
    lut = write_r4_lut(tmp_path, **CASES[case])
    m = memo_of(lut)
    g = lutmod.sat_threshold_grid(m, kind, W_KEY)
    assert isinstance(g, np.ndarray) and g.shape == SHAPE
    want = r4_arrays(kind)["VDSAT"]                                    # npz 직접(피검 함수 아님)
    assert np.allclose(g, want, rtol=1e-12, atol=1e-15)
    gL, gG, gD, gS = R4_GRIDS
    step = 1 if case == "slice_column" else 3                          # 전수는 슬라이스 열, 나머지는 3칸 간격 + 끝점
    for iL, L in enumerate(gL):
        for iG in sorted(set(range(0, len(gG), step)) | {len(gG) - 1}):
            for iD in sorted(set(range(0, len(gD), step)) | {len(gD) - 1}):
                for iS in sorted(set(range(0, len(gS), step)) | {len(gS) - 1}):
                    sb = lutmod.sat_threshold(m, kind, W_KEY, L, gG[iG], gD[iD], gS[iS])
                    assert sb.reason is None
                    assert sb.vdsat_v == pytest.approx(float(g[iL, iG, iD, iS]), rel=1e-12, abs=1e-15), (iL, iG, iD, iS)


@pytest.mark.parametrize("kind", ["nmos", "pmos"])
def test_sat_threshold_grid_is_none_without_a_vdsat_column(tmp_path, kind):
    lut = write_r4_lut(tmp_path, vdsat=())
    assert lutmod.sat_threshold_grid(memo_of(lut), kind, W_KEY) is None
