"""search/iv_headroom.py -- gm/ID 하한(헤드룸, 설계 41 §6.2, 사용자 결정 2026-10-08 Q4 스윙 예산 분할; D-SIa·D-SIg).

손 회로: CS + nmos 캐스코드 + pmos 캐스코드 부하(u13_hand `cascode_cs(pmos_cascode=True)`) -- 레일 사이 한 기둥에 소자 4개(M1·M2 nmos 아래, M4·M3 pmos 위),
출력 out 은 M2 와 M4 사이. toy LUT: VDSAT = 2/(gm/ID)(구성), gm/ID 최댓값 20 -> VDSAT_min = 0.1 V(n·p 같은 식).
oracle (d)+(a) -- 설계 41 §6.2 를 손으로:
- `swing_out_v >= s`, 단일 출력, 출력 DC 미선언 -> 위·아래 예산 합 = ΔV_rail − s(= 2h, h = s/2), 나눔은 '남는 여유의 최솟값이 가장 크도록' -- 위·아래 부분 기둥이
  같은 구성(소자 2개, 같은 VDSAT 식)이라 같은 몫 V_part = (1.8 − s)/2.
- M1 하한: VDSAT_M1(g) ≤ V_part − (VDSAT_M2,min + tol_M2) (− tol_M1, 포화 규칙 VDS ≥ VDSAT + tol) -> g ≥ 2/(V_part − 0.1 − tol 들).
  tol_vdsat(LUT LOO, 그 kind·L·VDS 의 칸 값)은 이 toy 에서 1~2 mV 라 그 상한 TOL_MAX = 5 mV 로 기대 구간을 잡는다:
  g ∈ [2/(V_part − 0.1), 2/(V_part − 0.1 − 2·TOL_MAX)].
"""
import pytest

from .u13_hand import all_inactive, bound_values, cascode_cs, rows_by_name, toy_case

SRC_VDSAT = "headroom_vdsat_6.2"
ELS = (("CL", "capacitor", 1e-12),)
VDSAT_MIN = 0.1             # 2/20 (toy 구성)
TOL_MAX = 5e-3              # toy tol_vdsat 상한(기대 구간 폭)
RAIL = 1.8


def _rows(constraints):
    st = toy_case(cascode_cs(pmos_cascode=True), elements=ELS, constraints=constraints).start
    return st, rows_by_name(st)


@pytest.mark.parametrize("swing", [1.2, 1.35])
def test_swing_budget_binds_cascode_stack_lower_bound(swing):
    # [기대 red] 구현은 이 회로에서 헤드룸 경계를 하나도 내지 않는다(M1 하한 = LUT 역산 정의역 6.4, 단계 B 창 out 폭 1.395 V·요구 s 는 계산됨).
    st, rows = _rows((("swing_out_v", ">=", swing),))
    v_part = (RAIL - swing) / 2
    lo_want = 2 / (v_part - VDSAT_MIN)
    hi_want = 2 / (v_part - VDSAT_MIN - 2 * TOL_MAX)
    for dev in ("M1", "M3"):                 # 레일 쪽 소자(나머지 하나 = 캐스코드가 최소 비용)
        got = bound_values(rows[dev], SRC_VDSAT, "gm_id", "lo")
        assert got, (dev, rows[dev].sources)
        assert lo_want * (1 - 1e-9) <= max(got) <= hi_want, (dev, got, lo_want, hi_want)
        assert rows[dev].gm_id_lo >= max(got) * (1 - 1e-12)


def test_swing_bound_is_monotone_in_required_swing():
    # (a) 단조: 요구 스윙이 커지면 가용 예산이 줄어 하한이 오른다(같거나 크다)
    _, r1 = _rows((("swing_out_v", ">=", 1.2),))
    _, r2 = _rows((("swing_out_v", ">=", 1.35),))
    a = bound_values(r1["M1"], SRC_VDSAT, "gm_id", "lo")
    b = bound_values(r2["M1"], SRC_VDSAT, "gm_id", "lo")
    assert a and b
    assert max(b) >= max(a)


def test_without_swing_constraint_rail_budget_does_not_bind():
    # 스윙 제약이 없으면 기둥 가용 폭 1.8 V − 다른 소자 최소 비용(3 × (0.1 V + tol)) -> g ≥ 2/(1.8 − 3·(0.1 + tol) − tol) ≈ 1.35 < LUT gm/ID 최솟값 5.6:
    # 헤드룸 하한이 있더라도 그 값 이하다(구간을 좁히지 않는다)
    st, rows = _rows(())
    cap = 2 / (RAIL - 3 * (VDSAT_MIN + TOL_MAX) - TOL_MAX)
    for r in rows.values():
        got = bound_values(r, SRC_VDSAT, "gm_id", "lo")
        assert all(v <= cap for v in got), (r.device, got, cap)
        assert r.gm_id_lo >= 5.6 - 1e-9                                  # LUT gm/ID 최솟값(VGS 1.8: 20 − 8·1.8) 아래로 내려가지 않는다
    assert all(src != SRC_VDSAT for src, _ in all_inactive(st))     # 레일 전위가 선언돼 있다 -> 비활성 사유 없음
