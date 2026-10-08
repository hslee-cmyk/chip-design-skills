"""pipeline/stage_a_budget.py -- `structure_count_budget(lut, kinds)` = 계수 예산 N_S(pipeline CONTRACT 1절, 설계 41 0절).

oracle (b) 다른 방법의 직접 집계: N_S = 회로가 쓰는 kind 의 모든 폭 슬라이스에 대해 |L|·|VGS|·|VDS|·|VS| 의 합. 이 test 는 LUT
manifest 의 슬라이스 목록과 각 슬라이스 npz 파일의 축 배열 길이를 numpy 로 직접 읽어 곱하고 더한다(엔진 LUT 로더 미사용).
결정론(같은 LUT -> 같은 값, 시간 무관)과 kind 집합 의존(쓰는 kind 만 센다)을 함께 본다.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from gmid_engine.pipeline import structure_count_budget

DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))      # sky130 LUT manifest 장치 이름 -> MOS kind


def _direct(location, manifest, kinds):
    names = dict(DEVICE_KINDS)
    total = 0
    root = Path(location.manifest_path).parent
    for entry in manifest["slices"]:
        if names[entry["device"]] not in kinds:
            continue
        with np.load(root / entry["file"]) as z:
            total += len(z["L"]) * len(z["VGS"]) * len(z["VDS"]) * len(z["VS"])
    return total


@pytest.mark.parametrize("kinds", [("nmos",), ("pmos",), ("nmos", "pmos")])
def test_budget_is_sum_of_slice_grid_sizes(real_lut, lut_location, manifest, kinds):
    assert structure_count_budget(real_lut, kinds) == _direct(lut_location, manifest, set(kinds))


def test_budget_is_additive_over_kinds_and_deterministic(real_lut):
    n, p = structure_count_budget(real_lut, ("nmos",)), structure_count_budget(real_lut, ("pmos",))
    assert structure_count_budget(real_lut, ("pmos", "nmos")) == n + p
    assert structure_count_budget(real_lut, ("nmos", "pmos")) == n + p
    assert n > 0 and p > 0
