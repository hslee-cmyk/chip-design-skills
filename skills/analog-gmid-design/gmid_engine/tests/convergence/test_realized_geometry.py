"""`realized_geometry(snapshot, placements) -> sizing.RealizedGeometry(layout_ref, w_request)` (CONTRACT 4절, 계획 LY7·LY8, WB-1 §3·§8).

oracle (a): 손으로 만든 배치·확산 기하 -- w_request = 요청 대기(pending) 소자의 요청 손가락 행 참조(A-139, 배치 소자는 두지 않음), layout_ref = `ly_diffusion` 필드 중 pending 아닌 소자의
(finger_w, ad, as, pd, ps, m = float(nf)) 참조. [WB-1] 폭 키(kind당 슬라이스) 인자·칸은 없다: 인자는 (snapshot, placements) 둘, 값 칸은 (layout_ref, w_request) 둘.

[FS-1] 옛 R-13a·R-13b·L-2 (레이아웃 뒤 재평가) test 4개는 '탐색 스냅샷 dc_finger (m, w_f_m) 를 레이아웃 입력으로 놓고 finger_slice 호출 0 을 센다' 는 구성이라 삭제했다
(tests/RETIRED_TESTS_fs1.md). 레이아웃 뒤 평가의 새 입력(요청 행 (nf, finger_w) -> `slice_of_finger`, 없는 소자 = 기준(실현) 스냅샷 dc_finger.m·w_key)은
tests/sizing/test_block_dc.py D-7 이 함수 수준으로 본다.
"""
from __future__ import annotations

import dataclasses
import inspect
from pathlib import Path

import pytest

from gmid_engine.convergence import realized_geometry
from gmid_engine.metrics import DiffusionGeometry
from gmid_engine.sizing import RealizedGeometry

from .conftest import GRID, ddiff, layout, placement


def test_all_placed_devices_fixed_and_pending_diffusion_dropped():
    pl = (placement("A", 100, 3, 3e-6), placement("B", 50, 2, 1e-6, pending=True), placement("C", 70, 1, 7e-7))
    diff = (ddiff("C", 7e-7, 1, 1e-13, 2e-13, 1.5e-6, 2.5e-6), ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),
            ddiff("B", 9e-7, 4, 5e-13, 6e-13, 1.1e-6, 1.2e-6))
    g = realized_geometry(layout(diffusion=diff).snapshot, pl)
    assert isinstance(g, RealizedGeometry)
    # [개정 여섯째 A-139, interface §3] w_request = 요청 대기 소자(배치 아님 + 요청 행 있음)마다 요청 손가락 행 참조 -- 배치 소자는 w_request 에 두지 않는다 (옛 '배치 소자 전부의 W').
    # 요청 행의 값 모양((nf, finger_w) 참조)은 interface 가 칸 형태를 정하지 않아 이름만 단언한다.
    assert tuple(n for n, _ in g.w_request) == ("B",)
    # [dispute 8.4, 위임 A-141] 요청 행 값 = (nf, finger_w): 요청 대기 배치 B(폭 키 50, nf 2)의 손가락 -- 레이아웃 요청 레코드(Placement)에서 온다 (W 1e-6 에서 다시 고르지 않음)
    assert g.w_request == (("B", (2, 50 * GRID)),)
    assert g.layout_ref == (("A", DiffusionGeometry(1e-6, 3e-13, 4e-13, 2.0e-6, 3.0e-6, 3.0)),
                            ("C", DiffusionGeometry(7e-7, 1e-13, 2e-13, 1.5e-6, 2.5e-6, 1.0)))     # B(대기) 는 탐색 규칙·LUT 규칙 기하로 둔다
    assert all(isinstance(d.m, float) for _n, d in g.layout_ref)


def test_realized_geometry_has_no_width_key_argument_or_field():
    """[WB-1] kind 당 폭 키 운반 삭제: 서명은 (snapshot, placements) 둘, 값 칸은 (layout_ref, w_request) 둘 -- 옛 finger·diffusion·w_keys 칸 없음."""
    assert list(inspect.signature(realized_geometry).parameters) == ["snapshot", "placements"]
    assert [f.name for f in dataclasses.fields(RealizedGeometry)] == ["layout_ref", "w_request"]


def test_geometry_equality_is_value_based():
    pl = (placement("A", 100, 3, 3e-6),)
    diff = (ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),)
    a = realized_geometry(layout(diffusion=diff).snapshot, pl)
    b = realized_geometry(layout(diffusion=diff).snapshot, pl)
    c = realized_geometry(layout(diffusion=(ddiff("A", 1e-6, 3, 3e-13, 4.5e-13, 2.0e-6, 3.0e-6),)).snapshot, pl)
    assert a == b and a != c                # 고정점 판정(CONTRACT 7절)은 값 비교 -- 확산 기하만 달라도 다른 기하


def test_geometry_device_class_helper_is_not_defined_anywhere():
    """부류 helper `geometry_device_class` 정의·호출 0 (소스 grep -- 엔진 소스, tests 제외)."""
    root = Path(__file__).resolve().parents[2]
    files = [p for p in root.rglob("*.py") if "tests" not in p.relative_to(root).parts]
    assert len(files) > 50                                                          # 양성 대조: 엔진 소스를 실제로 훑었다
    assert [str(p) for p in files if "geometry_device_class" in p.read_text(encoding="utf-8")] == []
