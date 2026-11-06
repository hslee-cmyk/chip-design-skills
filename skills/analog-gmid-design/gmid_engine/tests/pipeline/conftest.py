"""tests/pipeline 공용 -- 실 LUT(session 한 번 로드)와 단계 A 입력 helper. 근거: pipeline CONTRACT.md, lut CONTRACT 1.4.

실 LUT 데이터가 없으면 FAIL 이다(skip 아님 -- tests/integration/test_stage_a_library.py 와 같은 정책).
LutSpec 인자(폭 최소값·kind 이름표)는 manifest 에서 직접 읽는다 -- 기존 통합 test 의 로드 절차와 같다.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

from gmid_engine.lut import LutSpec, load_lut_set, resolve_lut_location

SKILL = Path(__file__).resolve().parents[3]
LIBRARY = SKILL / "assets" / "library"
DEVICE_KINDS = (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos"))      # sky130 LUT 장치 이름 -> MOS kind
CAP_SUFFIX = (("nmos", "_n"), ("pmos", "_p"))

GRAPH_TESTS = Path(__file__).resolve().parents[1] / "graph"
if str(GRAPH_TESTS) not in sys.path:                                # 손 회로(s1v_hand)를 단계 A 입력으로 재사용
    sys.path.insert(0, str(GRAPH_TESTS))


@pytest.fixture(scope="session")
def lut_location():
    return resolve_lut_location(str(SKILL / "assets" / "lut_v2_location.json"), os.environ)


@pytest.fixture(scope="session")
def manifest(lut_location):
    return json.loads(Path(lut_location.manifest_path).read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def real_lut(lut_location, manifest):
    kinds = dict(DEVICE_KINDS)
    from pdk_min_w import min_finger_w_m
    mins = min_finger_w_m(kinds.values())      # PDK 선언 양(card 20261104-wb1)
    spec = LutSpec(float(manifest.get("manufacturing_grid_m", 5e-9)), tuple(sorted(mins.items())), DEVICE_KINDS, CAP_SUFFIX)
    return load_lut_set(lut_location.manifest_path, lut_location.cap_npz_path, spec, pdk_root=lut_location.pdk_root,
                        verify_midpoints=lut_location.midpoints_paths, bin_rule=lut_location.bin_rule_path)
