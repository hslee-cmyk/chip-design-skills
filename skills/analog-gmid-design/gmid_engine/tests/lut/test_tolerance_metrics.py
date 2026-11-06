"""WB-1 M-2 (interface card 20261104-wb1 §8 M 표): r4 toy 의 `tol_v_table(...).at(L, vds, "id_equivalent")` 는 지표 삭제(gm_id_inverse) 전 손 값과 같다
(지표 독립). 표 하나의 지표 수 = 1.

oracle (손): lut conftest 의 r4 toy 손계산 -- cells[0][0] id_equivalent_loo_v = |ln10/2 − 0.75 − 18.5/8| / 4, id_equivalent_v = 그 값/16
(`test_tolerance.test_r4_toy_cells` 와 같은 닫힌 값, 독립 구현 `tol_cell_ref` 의 유도 상한 안). 합성 LUT 는 §4 모양(bin 선언 + 모델 파일, 앵커마다 bin 하나)이다.
앵커마다 bin 하나면 L 축 LOO 가 없어 L 방향 셀이 바뀔 수 있어(card §4: r4 tol 손 값 불변은 '미측정') 단언은 L 끝 앵커 셀 [0][0] 으로 한정한다.
"""
import json
import math

import numpy as np
import pytest

from gmid_engine.lut import LutMemo, load_lut_set, tol_v_table
from toy_bins import write_toy_bins

from .conftest import (TOY_L, TOY_SPEC, TOY_VDS, RefSlice, r4_toy_slice_arrays, sha256_file, tol_cell_ref, toy_cap_arrays)

R4_EQ_LOO_00 = abs(math.log(10.0) / 2 - 0.75 - 18.5 / 8) / 4        # 손 값 (test_tolerance 머리 식과 같은 닫힌 식)


@pytest.fixture(scope="module")
def r4_bins_memo(tmp_path_factory):
    root = tmp_path_factory.mktemp("wb1_m2")
    tb = write_toy_bins(root, ("nmos",), TOY_L, (1e-6, 2e-6), grid_m=1e-8)
    entries = []
    for name, W, scale in (("toy_w100.npz", 1e-6, 1.0), ("toy_w200.npz", 2e-6, 2.0)):
        a = r4_toy_slice_arrays(W, scale)
        a["meta_json"] = np.str_(json.dumps(tb.meta("nmos")))
        np.savez(root / name, **a)
        entries.append({"device": "toyn", "file": name, "sha256": sha256_file(root / name)})
    (root / "manifest.json").write_text(json.dumps({"generator_sha256": "0" * 64, "slices": entries}), encoding="utf-8")
    cap = toy_cap_arrays()
    cap["meta_json"] = np.str_(json.dumps(tb.meta("nmos")))
    np.savez(root / "cap.npz", **cap)
    lut = load_lut_set(str(root / "manifest.json"), str(root / "cap.npz"), TOY_SPEC, bin_rule=tb.bin_rule)
    return LutMemo(lut, point=256, curve=256, root=256)


def test_tolerance_id_equivalent_end_anchor_cell_equals_hand_value(r4_bins_memo):
    t = tol_v_table(r4_bins_memo, "nmos", 100)
    c = t.cells[0][0]
    r00 = tol_cell_ref(RefSlice(r4_toy_slice_arrays(1e-6)), 0, 0)
    assert abs(c.id_equivalent_loo_v - R4_EQ_LOO_00) <= r00["eq_loo_bound"]
    assert abs(c.id_equivalent_v - R4_EQ_LOO_00 / 16) <= r00["eq_bound"]
    v = t.at(TOY_L[0], TOY_VDS[0], "id_equivalent")
    assert v is not None and v >= c.id_equivalent_v                  # at = 인접 칸 최댓값 (끝 앵커 L 의 첫 VDS 칸을 품는다)


def test_tolerance_table_has_one_metric_and_rejects_retired_metric(r4_bins_memo):
    t = tol_v_table(r4_bins_memo, "nmos", 100)
    assert {row[0] for row in t.loo_orders} == {"id_equivalent"}
    assert not hasattr(t.cells[0][0], "gm_id_inverse_v")
    with pytest.raises(ValueError):
        t.at(TOY_L[0], TOY_VDS[0], "gm_id_inverse")
