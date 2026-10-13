"""search/iv_domain.py -- gm/ID 구간의 LUT 역산 정의역 (lut CONTRACT 3.1 `vgs_for_current_density`, 설계 41 §6.2 '곡선'; D-SIa).

oracle:
- (a) toy 구성: 곡선 gm/ID 범위 = [20 − 8·1.8, 20] = [5.6, 20] -- 정의역은 그 안이다(역산은 강반전 분지 [정점, 단조 끝] 안의 목표만 받는다).
- (a) lut 3.1 역산 왕복: 출발점의 ln IDu 는 그 소자 L 에서 `vgs_for_current_density` 로 역산된다(lut 공개 API -- 피검 search 함수 아님).
  기준 VDS·VS 는 같은 toy 의 포화 경계 0.3 V(toy 구성 식의 VDSAT 열)·VS 0.
"""
import pytest

from gmid_engine.lut import vgs_for_current_density

from .u13_hand import B, C, VGS_GRID, bound_values, cs_chain, memo_of, rows_by_name, toy_case, toy_env

SRC = "lut_inverse_domain"
ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))
G_MIN, G_MAX = B - C * VGS_GRID[-1], B


def _start():
    return toy_case(cs_chain(2), elements=ELS, constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))).start


def test_domain_bounds_inside_curve_range():
    st = _start()
    for r in st.rows:
        lo = bound_values(r, SRC, "gm_id", "lo")
        hi = bound_values(r, SRC, "gm_id", "hi")
        assert lo and hi, r.device
        assert G_MIN - 1e-9 <= max(lo) < min(hi) <= G_MAX + 1e-9
        assert r.gm_id_lo >= max(lo) - 1e-12 and r.gm_id_hi <= min(hi) + 1e-12


def test_start_ln_idu_is_invertible():
    st = _start()
    memo = memo_of(toy_env(1.0).lut)
    for name, r in rows_by_name(st).items():
        vgs = vgs_for_current_density(memo, r.kind, 100, r.ln_idu, r.l_chosen, 0.3, 0.0)
        assert 0.0 <= vgs <= VGS_GRID[-1]
        assert (B - C * vgs) == pytest.approx(r.gm_id_chosen, rel=2e-2)      # 같은 곡면의 gm/ID(기준 점 차이: LAM·VDS 만큼 -- 2 % 안)
