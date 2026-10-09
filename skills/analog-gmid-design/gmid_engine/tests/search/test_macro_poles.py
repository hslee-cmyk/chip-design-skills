"""search/macro_poles.py -- S1v 매크로 모델(설계 41 §6.5, §6.3 비주극점 조건; search CONTRACT U13 '매크로 모델').

입력: 이상 VCCS 사슬이 되도록 만든 손 회로(n 단 CS 사슬, 단마다 선언 부하 커패시터)와 해석식 toy LUT(u13_hand -- gm/gds = (gm/ID)/LAM,
소자 용량 배율 1e-12 이라 소자 cgg·cdd 는 선언 커패시터의 1e-9 배 미만 -> 망은 이상 VCCS 사슬과 같다).
피검 함수로 기대값을 만들지 않는다. 기대값 출처:
- oracle (a) 닫힌 식: H(jω) = Π gm_k/(gm_k/A_k + jωC_k), 극점 = gm_k/(2π A_k C_k), PM = 180 − Σ atan(ω/p_k)(u13_hand `chain_*`). A_k = 블록 입력 소자의
  gm/ID(보고 행의 선택값 -- 매크로 2회차의 입력)/LAM 은 toy LUT 구성 식이다.
- oracle (b) 같은 문제를 다른 방법으로: 주극점 단 전수 + 비주극점 u 격자·황금 분할 + 이득 식 닫힌 해(`chain_min_current`).
- oracle (d) 설계 41 §6.5 '특수 경우': 단일 블록·Miller 없음이면 gm_1 = 2π·GBW·C_out.
허용오차: 상대 1e-6 -- 남는 차이는 소자 용량(≤ 1e-9 상대)과 매크로의 √ε 분해능 등식 풀이(SLSQP 등식 제약)뿐이다. 최소성 비교는 상대 1e-4 --
SLSQP 의 목적 수렴 허용오차(scipy 기본 ftol 1e-6, 목적 척도 1e-4 A)와 oracle 의 격자·황금 분할 해상도를 덮는 값.
"""
import math

import pytest

from .u13_hand import (
    LAM,
    chain_min_current,
    chain_poles_hz,
    chain_pm_deg,
    chain_response,
    cs_chain,
    rows_by_name,
    toy_case,
)

GBW = 1e6
PM = 60.0
TARGETS = (("gbw_ss_hz", ">=", GBW), ("pm_ss_deg", ">=", PM))
TINY = 1e-12            # 소자 용량 배율


def _chain(caps, constraints=TARGETS):
    n = len(caps)
    els = tuple(("C%d" % (k + 1), "capacitor", c) for k, c in enumerate(caps))
    case = toy_case(cs_chain(n), cap_scale=TINY, elements=els, constraints=constraints)
    st = case.start
    rows = rows_by_name(st)
    nets = ["n%d" % k for k in range(1, n)] + ["out"]
    gm = dict(st.macro.gm)
    gms = [gm[(x,)] for x in nets]
    g = [rows["MN%d" % (k + 1)].gm_id_chosen for k in range(n)]
    a = [x / LAM for x in g]                     # toy 구성: gm/gds = (gm/ID)/(gds/ID) = g/LAM
    return st, gms, g, a


CASES = ((1e-12, 4e-12), (4e-12, 1e-12), (1e-12, 2e-12, 3e-12))


@pytest.mark.parametrize("caps", CASES, ids=["2p_1_4", "2p_4_1", "3p_1_2_3"])
def test_macro_meets_gbw_and_pm_in_closed_form(caps):
    st, gms, g, a = _chain(caps)
    m = st.macro
    assert m.records == ()                                               # 근 없음·비수렴 기록 없음
    assert m.ugf_hz == pytest.approx(GBW, rel=1e-6)
    # oracle (a): 닫힌 식 |H(jω_GBW)| = 1 (UGF = GBW), 위상 여유 ≥ 목표
    assert abs(chain_response(gms, caps, a, GBW)) == pytest.approx(1.0, rel=1e-6)
    assert chain_pm_deg(gms, caps, a, GBW) >= PM - 1e-6
    assert m.pm_deg == pytest.approx(chain_pm_deg(gms, caps, a, GBW), abs=1e-4)
    # 극점 = G_k/(2π C_k) -- 보고 극점과 닫힌 식
    poles = chain_poles_hz(gms, caps, a)
    assert len(m.poles_hz) == len(caps)
    for got, want in zip(m.poles_hz, poles):
        assert got == pytest.approx(want, rel=1e-6)
    # 41 §6.3 비주극점 조건: 주극점(가장 낮은 극점)을 뺀 극점 ≥ GBW·tan(PM)
    assert min(poles[1:]) >= GBW * math.tan(math.radians(PM)) * (1 - 1e-6)


@pytest.mark.parametrize("caps", CASES[:2], ids=["2p_1_4", "2p_4_1"])
def test_two_pole_supply_current_is_minimum(caps):
    # CONTRACT U13 '전원 전류 합 최소' -- 가지 전류 = gm_k/(gm/ID)_k (θ 전류 = 단마다 pmos 부하 가지)
    st, gms, g, a = _chain(caps)
    want, want_gm, d = chain_min_current(list(caps), g, a, GBW, PM)
    got = sum(x / y for x, y in zip(gms, g))
    assert got == pytest.approx(want, rel=1e-4)
    # 주극점은 큰 커패시터 단(비주극점 비용 ∝ C) -- oracle 의 단과 같다
    assert max(range(len(caps)), key=lambda k: caps[k]) == d
    assert gms[d] < gms[1 - d]


def test_three_pole_supply_current_is_global_minimum():
    # oracle (b): C = (1, 2, 3) pF 에서 전역 최소는 주극점을 가장 큰 커패시터 단(3 pF)에 두는 것.
    # [기대 red] 매크로의 SLSQP 는 실행 가능한 출발점의 국소 최소(주극점 = 1 pF 단)에 머문다(실측 Σ gm/g = 1.160e-3 A 대 전역 6.82e-4 A).
    st, gms, g, a = _chain(CASES[2])
    want, _gm, d = chain_min_current(list(CASES[2]), g, a, GBW, PM)
    got = sum(x / y for x, y in zip(gms, g))
    assert got <= want * (1 + 1e-4), (got, want, d)


def test_single_block_gm_is_2pi_gbw_cout():
    # 41 §6.5 특수 경우(oracle (d)): 단일 블록·Miller 없음 -> gm_1 = 2π·GBW·C_out.
    # 정확한 닫힌 식(oracle (a)): |gm/(gm/A + jωC)| = 1 -> gm = ωC/√(1 − 1/A²); 설계 근사와의 차는 1/(2A²) 이하.
    c = 2e-12
    st, gms, g, a = _chain((c,))
    w = 2 * math.pi * GBW
    exact = w * c / math.sqrt(1 - 1 / a[0] ** 2)
    assert gms[0] == pytest.approx(exact, rel=1e-6)
    assert gms[0] == pytest.approx(w * c, rel=1 / a[0] ** 2)


def test_no_pm_target_uses_floor_and_records_it():
    # CONTRACT U13: PM 목표가 없으면 PM_FLOOR_DEG = atan(1) = 45°, 기록 `pm_floor_pole_at_ugf`.
    # (설계 41 §6.5 는 PM 목표 없는 경우를 정하지 않는다 -- 설계 대조는 보고의 '이견' 절.)
    caps = (1e-12, 4e-12)
    st, gms, g, a = _chain(caps, constraints=(("gbw_ss_hz", ">=", GBW),))
    codes = [code for code, _ in st.macro.records]
    assert "pm_floor_pole_at_ugf" in codes
    assert "macro_root_missing" not in codes and "macro_nonconvergent" not in codes
    assert abs(chain_response(gms, caps, a, GBW)) == pytest.approx(1.0, rel=1e-6)
    assert chain_pm_deg(gms, caps, a, GBW) >= 45.0 - 1e-6
    poles = chain_poles_hz(gms, caps, a)
    assert poles[1] >= GBW * (1 - 1e-6)                                   # f_np = GBW·tan(45°) = GBW


def test_no_gbw_target_macro_inactive():
    # 41 §6.3 전제·CONTRACT: GBW 목표가 없으면 매크로 비활성(`macro_inactive`, 사유 gbw_target_missing), gm 값 없음
    st = toy_case(cs_chain(1), cap_scale=TINY, elements=(("C1", "capacitor", 1e-12),),
                  constraints=(("pm_ss_deg", ">=", PM),)).start
    assert st.macro.gm == ()
    assert ("macro_inactive", (("reason", "gbw_target_missing"),)) in st.macro.records
