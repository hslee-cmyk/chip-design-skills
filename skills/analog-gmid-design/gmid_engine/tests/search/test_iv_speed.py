"""search/iv_speed.py -- gm/ID 상한(속도, 설계 41 §6.3)과 L 상한(§6.4-4) (D-SIb).

손 회로 = CS + nmos 캐스코드 + pmos 캐스코드 부하(u13_hand `cascode_cs(pmos_cascode=True)`): 극점 노드 x(M2 소스)·y(M4 소스)·out(출력 포트, 주극점).
toy LUT(용량 배율 1): f_T 는 gm/ID 가 높을수록 떨어진다(구성 식 f_T = (gm/ID)·IDu·W_ref/(2π·CGG·L), IDu 는 gm/ID 가 오를수록 지수로 줄어든다).
oracle:
- (d) 설계 41 §6.3: 비주극점 조건 f_np = GBW / tan(90° − PM) = GBW·tan(PM) -- GBW·tan(PM) 이 같은 두 spec 은 같은 속도 경계를 내야 한다(그 밖 입력 동일,
  보간 규칙과 무관하게 정확히 같은 값). 감도 확인: f_np 가 다른 spec 은 다른 값.
- (a) 구조: 대상 = 주극점 노드를 뺀 극점 노드에 낮은 등급 단자(소스)를 주는 소자 = M2·M4 뿐(M1·M3 은 드레인만 그 노드에 닿는다).
- (a) 단조성: f_T 가 gm/ID 에 대해 감소하므로 f_np 가 커지면 상한은 내려간다(같거나 작다).
- (d) 설계 41 §6.3 '전제: gbw_target_hz 와 pm_target_deg 가 있어야 한다. 없으면 비활성이다.'
"""
import math

import pytest

from .u13_hand import all_inactive, bound_values, cascode_cs, rows_by_name, toy_case

SRC_FT = "speed_ft_6.3"
ELS = (("CL", "capacitor", 1e-12),)


def _speed(constraints):
    st = toy_case(cascode_cs(pmos_cascode=True), elements=ELS, constraints=constraints).start
    rows = rows_by_name(st)
    return st, {n: bound_values(r, SRC_FT, "gm_id", "hi") for n, r in rows.items()}, rows


def test_f_np_is_gbw_times_tan_pm():
    _, a, ra = _speed((("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    _, b, rb = _speed((("gbw_ss_hz", ">=", 1e6 * math.tan(math.radians(60.0))), ("pm_ss_deg", ">=", 45.0)))
    _, c, _ = _speed((("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 45.0)))
    for dev in ("M2", "M4"):
        assert ra[dev].l_chosen == rb[dev].l_chosen                      # 같은 L 에서 비교
        assert len(a[dev]) == 1 and len(b[dev]) == 1
        assert b[dev][0] == pytest.approx(a[dev][0], rel=1e-12)           # 같은 f_np -> 같은 경계
        assert c[dev][0] > a[dev][0] * (1 + 1e-6)                          # f_np 가 작으면(GBW·tan45 = GBW) 상한이 높다


def test_speed_bound_only_on_low_impedance_providers():
    _, b, _ = _speed((("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    assert {n for n, v in b.items() if v} == {"M2", "M4"}


def test_speed_upper_bound_decreases_with_gbw():
    _, lo, _ = _speed((("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)))
    _, hi, _ = _speed((("gbw_ss_hz", ">=", 2e6), ("pm_ss_deg", ">=", 60.0)))
    for dev in ("M2", "M4"):
        assert hi[dev][0] < lo[dev][0]


def test_chosen_gm_id_respects_speed_bound():
    _, b, rows = _speed((("gbw_ss_hz", ">=", 2e6), ("pm_ss_deg", ">=", 60.0)))
    for dev in ("M2", "M4"):
        assert rows[dev].gm_id_hi <= b[dev][0] * (1 + 1e-12)
        assert rows[dev].gm_id_chosen <= b[dev][0] * (1 + 1e-12)


def test_no_gbw_target_speed_inactive_with_reason():
    st, b, _ = _speed((("pm_ss_deg", ">=", 60.0),))
    assert not any(b.values())
    assert any(src == SRC_FT for src, _why in all_inactive(st))


def test_no_pm_target_speed_bound_inactive_per_design():
    # 설계 41 §6.3 전제: PM 목표가 없으면 속도 상한은 비활성이고 그 사유가 보고에 남는다.
    # [기대 red, 이견] 구현은 PM_FLOOR_DEG = 45° 로 상한을 계산한다(GBW·tan45 경계 = PM 45 spec 과 같은 값; iv_speed docstring '설계 공백으로 보고').
    st, b, _ = _speed((("gbw_ss_hz", ">=", 1e6),))
    assert not any(b.values())
    assert any(src == SRC_FT for src, _why in all_inactive(st))
