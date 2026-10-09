"""search/iv_context.py -- `build_start_context(s1v, ach, kctx, spec, pdk_decl, domain) -> StartContext` (설계 41 §6 입력 묶음).

oracle (d) spec 선언값과 (a) 구성:
- 보상 목표: 판정 제약 `gbw_ss_hz >= v`·`pm_ss_deg >= v` 의 값(compensation_targets 없음), 없으면 None(41 §6.3 전제).
- 면적 예산 = `area_search_m2 <= v`(결정 11), 없으면 None.
- 최소 finger 폭 = toy PDK 선언 0.5 µm, 레일 전위 = spec supplies(vdd 1.8, gnd 0).
- 소자 = 회로의 MOS 전부, 순서는 구조 색 오름차순(이름 무관 -- 이름 전단사 불변식의 전제).
"""
import pytest

from gmid_engine.search.iv_context import build_start_context

from .u13_hand import W_MIN, cs_chain, toy_case

ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))


def _ctx(constraints):
    c = toy_case(cs_chain(2), elements=ELS, constraints=constraints)
    return build_start_context(c.s1v, c.ach, c.kctx, c.spec, c.pdk, c.sctx.domain)


def test_targets_and_budget_from_spec():
    ctx = _ctx((("gbw_ss_hz", ">=", 2e6), ("pm_ss_deg", ">=", 55.0), ("area_search_m2", "<=", 1e-9)))
    assert ctx.gbw_hz == pytest.approx(2e6)
    assert ctx.pm_deg == pytest.approx(55.0)
    assert ctx.area_budget_m2 == pytest.approx(1e-9)
    assert ctx.w_min_m == pytest.approx(W_MIN, rel=1e-12)
    assert dict(ctx.rail_v) == {"vdd": 1.8, "gnd": 0.0}
    assert ctx.transfer is not None and ctx.transfer.blocks


def test_missing_targets_are_none():
    ctx = _ctx(())
    assert ctx.gbw_hz is None and ctx.pm_deg is None and ctx.area_budget_m2 is None


def test_devices_are_all_mos_in_colour_order():
    ctx = _ctx((("gbw_ss_hz", ">=", 1e6),))
    names = [d.name for d in ctx.devices]
    assert sorted(names) == ["MN1", "MN2", "MP1", "MP2"]
    colours = [d.colour for d in ctx.devices]
    assert colours == sorted(colours)
    assert set(ctx.by_name) == set(names)
    assert {ctx.by_name[n].kind for n in ("MN1", "MN2")} == {"nmos"}
    assert {ctx.by_name[n].kind for n in ("MP1", "MP2")} == {"pmos"}
