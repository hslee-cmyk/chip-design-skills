"""`realized_geometry(layout, placements, keys) -> search.RealizedGeometry` (CONTRACT 4절, 계획 LY7·LY8).

oracle (a): 손으로 만든 배치·확산 기하 -- w_request = 배치 소자 전부(이름순, Placement.W_m), w_keys = 입력 그대로, diffusion = `LayoutResult.diffusion`
중 pending 아닌 소자의 (finger_w, ad, as, pd, ps, m = float(nf)).
"""
from __future__ import annotations

from gmid_engine.convergence import realized_geometry
from gmid_engine.metrics import DiffusionGeometry
from gmid_engine.search import RealizedGeometry

from .conftest import ddiff, layout, placement


def test_all_placed_devices_fixed_and_pending_diffusion_dropped():
    pl = (placement("A", 100, 3, 3e-6), placement("B", 50, 2, 1e-6, pending=True), placement("C", 70, 1, 7e-7))
    diff = (ddiff("C", 7e-7, 1, 1e-13, 2e-13, 1.5e-6, 2.5e-6), ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),
            ddiff("B", 9e-7, 4, 5e-13, 6e-13, 1.1e-6, 1.2e-6))
    keys = (("nmos", 100), ("pmos", 70))
    g = realized_geometry(layout(diffusion=diff), pl, keys)
    assert isinstance(g, RealizedGeometry)
    assert g.w_request == (("A", 3e-6), ("B", 1e-6), ("C", 7e-7))       # LY7: pending 포함 모든 배치 소자
    assert g.w_keys == keys
    assert g.diffusion == (("A", DiffusionGeometry(1e-6, 3e-13, 4e-13, 2.0e-6, 3.0e-6, 3.0)),
                           ("C", DiffusionGeometry(7e-7, 1e-13, 2e-13, 1.5e-6, 2.5e-6, 1.0)))     # B(대기) 는 LUT 규칙 기하로 둔다
    assert all(isinstance(d.m, float) for _n, d in g.diffusion)


def test_geometry_equality_is_value_based():
    pl = (placement("A", 100, 3, 3e-6),)
    diff = (ddiff("A", 1e-6, 3, 3e-13, 4e-13, 2.0e-6, 3.0e-6),)
    a = realized_geometry(layout(diffusion=diff), pl, (("nmos", 100),))
    b = realized_geometry(layout(diffusion=diff), pl, (("nmos", 100),))
    c = realized_geometry(layout(diffusion=(ddiff("A", 1e-6, 3, 3e-13, 4.5e-13, 2.0e-6, 3.0e-6),)), pl, (("nmos", 100),))
    assert a == b and a != c                # 고정점 판정(CONTRACT 7절)은 값 비교 -- 확산 기하만 달라도 다른 기하
