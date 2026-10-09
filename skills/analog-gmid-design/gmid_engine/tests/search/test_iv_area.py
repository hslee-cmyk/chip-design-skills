"""search/iv_area.py -- 면적 예산 L·gm/ID 상한, 최소 폭 gm/ID 하한 (설계 41 §6.4-5, 40 §7.1 결정 11; D-SIc).

oracle:
- (a) 정의(40 §7.1): 면적 = Σ_MOS W·L + 커패시터 값/ρ_MIM(ρ = toy PDK 선언 4e-3 F/m²). 출발점 보고의 `area_est_m2` = 행의 w_m·l_chosen 합 + 선언 커패시터 면적.
- (a) W = I·L/IDu (IDu = ID·L/W 의 정의) -- 행의 i_start·l_chosen/exp(ln_idu) = w_m.
- (d) 사용자 결정 11: 예산 `area_search_m2 <= A` 가 있으면 출발점 면적 ≤ A, 아니면 '충돌(보고만)'(41 §6.6 'A_est > 예산').
- (d) CONTRACT U13: 최소 폭 W ≥ W_min(PDK `min_finger_w_m`; toy 5e-7 m, sky130 은 search 정의역 `w_min_m`) -- 출발점의 모든 MOS.
- (d) 41 §6.4-5 '예산이 선언된 회로에서만' -- 없으면 비활성 사유 `constraint_not_declared`.
"""
import math

import pytest

from .u13_hand import MIM_DENSITY, W_MIN, all_inactive, bound_values, cs_chain, toy_case

TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))
CAPS = (1e-12, 1e-12)
ELS = tuple(("C%d" % (k + 1), "capacitor", c) for k, c in enumerate(CAPS))
CAP_AREA = sum(CAPS) / MIM_DENSITY


def _start(budget=None):
    cons = TARGETS + ((("area_search_m2", "<=", budget),) if budget is not None else ())
    return toy_case(cs_chain(2), elements=ELS, constraints=cons).start


@pytest.mark.parametrize("budget", [None, 5.3e-10])
def test_area_estimate_is_mos_plus_capacitor_area(budget):
    st = _start(budget)
    mos = sum(r.w_m * r.l_chosen for r in st.rows)
    assert st.area_est_m2 == pytest.approx(mos + CAP_AREA, rel=1e-9)
    assert st.area_budget_m2 == budget


@pytest.mark.parametrize("budget", [None, 5.3e-10])
def test_width_identity_and_minimum_width(budget):
    st = _start(budget)
    for r in st.rows:
        assert r.w_m == pytest.approx(r.i_start * r.l_chosen / math.exp(r.ln_idu), rel=1e-9)
        assert r.w_m >= W_MIN * (1 - 1e-9), (r.device, r.w_m)


def test_area_budget_respected_or_reported():
    budget = 5.3e-10
    st = _start(budget)
    over = [c for c in st.conflicts if c.quantity == "area"]
    assert st.area_est_m2 <= budget * (1 + 1e-12) or over
    # 예산이 있으면 면적 경계가 계산된다(전류가 정해진 소자마다 gm/ID 상한)
    assert any(bound_values(r, "area_gm_id_6.4_5", "gm_id", "hi") for r in st.rows)
    assert ("area_gm_id_6.4_5", "constraint_not_declared") not in all_inactive(st)


def test_no_budget_area_bounds_inactive():
    st = _start(None)
    assert not any(bound_values(r, "area_gm_id_6.4_5") or bound_values(r, "area_l_6.4_5") for r in st.rows)
    inactive = all_inactive(st)
    assert ("area_gm_id_6.4_5", "constraint_not_declared") in inactive
    assert ("area_l_6.4_5", "constraint_not_declared") in inactive
