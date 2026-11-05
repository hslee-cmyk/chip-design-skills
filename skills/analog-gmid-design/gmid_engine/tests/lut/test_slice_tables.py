"""WB-1 T-1 -- `build_slice_tables(memo) -> int` (interface card §8 '표(J-6)'). oracle (손): 슬라이스 키 {100, 200} x kind 2 x 표 2 = 8.

합성 LUT 슬라이스 키 {100, 200}, kind 둘(nmos, pmos), 표 둘(`tol_v_table`, `tol_vdsat_table`). TOY_SPEC W_min 1e-6 = 키 100 이라 둘 다 `widths` 에 든다.
"""
from gmid_engine.lut import LutMemo, build_slice_tables

from sizing.wb1_toy import write_r4_bins_lut


def test_slice_tables_count_is_keys_times_kinds_times_tables(tmp_path):
    lut, _, _ = write_r4_bins_lut(tmp_path, widths=(1e-6, 2e-6))
    memo = LutMemo(lut, point=256, curve=256, root=256)
    assert build_slice_tables(memo) == 8


def test_slice_tables_single_slice_lut_counts_four(tmp_path):
    lut, _, _ = write_r4_bins_lut(tmp_path, widths=(1e-6,))
    assert build_slice_tables(LutMemo(lut, point=256, curve=256, root=256)) == 4     # 1 키 x 2 kind x 2 표
