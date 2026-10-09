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

from .u13_hand import I0, MIM_DENSITY, W_MIN, all_inactive, bound_values, cs_chain, mos_e, rows_by_name, toy_case, topology, two_e

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


# ---------------------------------------------------------------- 최소 폭 보정 (CONTRACT U13 '최소 폭 보정', 설계 41 §6.5 as-built §6.2 문장)
# 손 회로: CS 입력 MN1 (pd, in, gnd) + pmos 다이오드 MP0 (pd, pd, vdd) + 미러 MP1 (out, pd, vdd) + nmos 전류 싱크 MN2 (out, nb, gnd), CL (out, gnd).
# MP0·MP1 은 gate·source 넷이 같아 같은 VGS 묶음(구조 사실) -- CONTRACT '같은 VGS 묶음은 함께' gm/ID 를 올린다.
# toy LUT: W = I·L/IDu(g), IDu = I0·exp(f(VGS) + LAM·VDS − A·VS²) 는 gm/ID 가 오를수록(VGS 가 내려갈수록) 지수로 줄어 W 는 g 에 대해 증가 ->
# W ≥ W_min 은 gm/ID 하한이다.


def mirror_cs(name="u13mir"):
    devs = [mos_e("MN1", "nmos", "pd", "in", "gnd"), mos_e("MP0", "pmos", "pd", "pd", "vdd"),
            mos_e("MP1", "pmos", "out", "pd", "vdd"), mos_e("MN2", "nmos", "out", "nb", "gnd")]
    return topology(name, devs, passives=[two_e("CL", "capacitor", "out", "gnd")], bias=["nb"])


def _mirror(gbw, cl):
    return toy_case(mirror_cs(), cap_scale=1e-12, elements=(("CL", "capacitor", cl),),
                    constraints=(("gbw_ss_hz", ">=", gbw), ("pm_ss_deg", ">=", 60.0))).start


def test_w_min_raises_gm_id_for_whole_same_vgs_group():
    st = _mirror(1e6, 1e-12)
    rows = rows_by_name(st)
    b0 = bound_values(rows["MP0"], "w_min_gm_id", "gm_id", "lo")
    b1 = bound_values(rows["MP1"], "w_min_gm_id", "gm_id", "lo")
    assert b0 and b1, (rows["MP0"].sources, rows["MP1"].sources)
    assert max(b0) == pytest.approx(max(b1), rel=1e-12)                     # 묶음이 한 하한을 공유
    for d in ("MP0", "MP1"):
        assert rows[d].gm_id_lo >= max(b0) * (1 - 1e-12)
        assert rows[d].w_m >= W_MIN * (1 - 1e-9)
    assert rows["MP0"].gm_id_chosen == pytest.approx(rows["MP1"].gm_id_chosen, rel=1e-12)
    assert rows["MP0"].gm_id_lo == pytest.approx(rows["MP1"].gm_id_lo, rel=1e-12)
    # 보정이 실제로 구간을 좁힌다(다른 하한보다 높다): 하한 출처 중 최댓값이 w_min 하한이다
    others = [b.value for b in rows["MP0"].sources if b.quantity == "gm_id" and b.side == "lo" and b.source != "w_min_gm_id"]
    assert max(b0) > max(others)


@pytest.mark.parametrize("circuit", ["cs1", "mirror"])
def test_w_min_beyond_upper_bound_is_conflict(circuit):
    # oracle (a) 손계산: GBW 100 Hz, C_out 10 fF -> 입력 gm ≈ 2π·100·1e-14 = 6.3e-12 S. gm/ID 를 LUT 최댓값 20(VGS 0)까지 올려도
    # I = gm/20 ≈ 3.1e-13 A, IDu(VGS 0) ≤ I0_n·e^{LAM·1.8} = 1.2e-11 A (nmos source = gnd -> VS 0), L ≤ 2 µm 이므로
    # W ≤ 3.1e-13·2e-6/1e-11 ≈ 6.3e-8 m < W_min 5e-7 m -- 어떤 gm/ID·L 로도 W ≥ W_min 을 만들 수 없다.
    # CONTRACT U13 '최소 폭 보정 ... 상한을 넘기면 충돌 레코드로 남긴다', 설계 41 §6.6 '충돌이 있어도 자르지 않는다'.
    # [기대 red, 75626c8] 구현은 W = 6.3e-9 m(< W_min) 행을 남기면서 w_min 하한도 충돌 레코드도 내지 않는다(조용한 최소 폭 위반).
    gbw, cl = 1e2, 1e-14
    gm_in = 2 * math.pi * gbw * cl
    w_max = (gm_in / 20.0) * 2e-6 / (I0["nmos"] * math.exp(0.1 * 1.8))
    assert w_max < W_MIN                                                     # 입력 확인(손계산)
    if circuit == "cs1":
        st = toy_case(cs_chain(1), cap_scale=1e-12, elements=(("C1", "capacitor", cl),),
                      constraints=(("gbw_ss_hz", ">=", gbw), ("pm_ss_deg", ">=", 60.0))).start
    else:
        st = _mirror(gbw, cl)
    rows = rows_by_name(st)
    assert rows["MN1"].w_m < W_MIN                                           # 손계산과 같은 사실(행이 자르지 않고 남긴다)
    narrow = [d for d, r in rows.items() if r.w_m < W_MIN * (1 - 1e-9)]
    conflicts = list(st.conflicts) + [c for r in st.rows for c in r.conflicts]
    for d in narrow:
        hit = [c for c in conflicts if c.device == d and c.quantity == "gm_id" and any(src == "w_min_gm_id" for src, _ in c.bounds)]
        assert hit, (d, rows[d].w_m, conflicts)
        assert all(c.gap > 0 for c in hit)
