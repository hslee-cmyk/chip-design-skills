"""search/_helpers_area.py -- `area_estimate(ctx, currents, gm_id, lengths, cap_values, res_values) -> (총 m², {MOS: W·L 또는 None}, 수동소자 m²)`
(설계 41 §6.4-5, 40 §7.1 결정 11).

oracle (a) 정의: W·L = I·L²/IDu(gm/ID, L) -- IDu 는 `CurveBook` 기준 점 값(test_iv_curves 가 toy 구성 식과 마디에서 대조한 입력), 커패시터 면적 = 값/ρ_MIM
(toy PDK 4e-3 F/m²). 전류를 모르는 MOS 는 합에서 빠지고 None(조용히 0 이 되지 않는다). 면적은 전류에 선형.
"""
import pytest

from gmid_engine.search._helpers_area import area_estimate
from gmid_engine.search.iv_context import build_start_context
from gmid_engine.search.iv_curves import QUANTITY_IDU

from .u13_hand import MIM_DENSITY, cs_chain, toy_case

ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 3e-12))
MOS = ("MN1", "MN2", "MP1", "MP2")
G_ALL = {n: 12.0 for n in MOS}           # gm/ID·L 은 모든 MOS 에 준다(전류만 일부)
L_ALL = {n: 1e-6 for n in MOS}


@pytest.fixture(scope="module")
def ctx():
    c = toy_case(cs_chain(2), elements=ELS, constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    return build_start_context(c.s1v, c.ach, c.kctx, c.spec, c.pdk, c.sctx.domain)


def test_mos_area_is_current_times_l_squared_over_idu(ctx):
    g, L, i = 12.0, 1e-6, 2e-6
    total, per, passive = area_estimate(ctx, {"MN1": i}, G_ALL, L_ALL, (), ())
    idu = ctx.curves.value(ctx.curves.bundle_of("MN1", "nmos", L), QUANTITY_IDU, g)
    assert per["MN1"] == pytest.approx(i * L * L / idu, rel=1e-12)
    assert passive == pytest.approx((1e-12 + 3e-12) / MIM_DENSITY, rel=1e-12)
    assert total == pytest.approx(per["MN1"] + passive, rel=1e-12)


def test_unknown_current_is_none_not_zero(ctx):
    _total, per, _p = area_estimate(ctx, {"MN1": 1e-6}, G_ALL, L_ALL, (), ())
    for name in ("MN2", "MP1", "MP2"):
        assert name in per and per[name] is None


def test_area_linear_in_current(ctx):
    a1 = area_estimate(ctx, {"MN1": 1e-6}, G_ALL, L_ALL, (), ())[1]["MN1"]
    a3 = area_estimate(ctx, {"MN1": 3e-6}, G_ALL, L_ALL, (), ())[1]["MN1"]
    assert a3 == pytest.approx(3 * a1, rel=1e-12)
