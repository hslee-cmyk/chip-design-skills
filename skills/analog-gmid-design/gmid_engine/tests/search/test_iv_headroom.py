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
    # (24cfecd 에서 red: 헤드룸 경계 없음 -- 75626c8 에서 해소)
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


@pytest.mark.parametrize("swing", [1.2, 1.35])
def test_unequal_sub_columns_split_remaining_margin_equally(swing):
    # 설계 41 §6.2(출력 DC 미선언): 위·아래 예산 합 = ΔV_rail − s, 나눔은 '남는 여유의 최솟값이 가장 크도록' = 남는 여유를 같은 몫으로
    # (41 §6.5 as-built 절 §6.2 문장). 손 회로 cascode_cs(pmos_cascode=False): 아래 부분 기둥 M1·M2(nmos 2개), 위 M3(pmos 1개).
    # 요구 = Σ(VDSAT_min + tol): 아래 2·(0.1 + t), 위 (0.1 + t); 남는 여유 m = (1.8 − s − 0.3 − 3t)/2.
    # 경계: 위 M3: VDSAT ≤ (0.1 + t + m) − t = 0.1 + m; 아래 M1: VDSAT ≤ (0.2 + 2t + m) − (0.1 + t) − t = 0.1 + m -> g = 2/(0.1 + m) (두 쪽 같은 값).
    # t ∈ [0, TOL_MAX], 자기 tol 을 빼지 않는 해석(+t)까지 덮으면 g ∈ [2/(0.1 + (1.5 − s)/2), 2/(0.1 + (1.5 − s)/2 − 1.5·TOL_MAX)].
    # 대조: 예산을 반씩 나누면(V_part = (1.8 − s)/2) M3 = 2/V_part, M1 = 2/(V_part − 0.1) 로 서로 다르고 둘 다 이 구간 밖이다.
    st = toy_case(cascode_cs(), elements=ELS, constraints=(("swing_out_v", ">=", swing),)).start
    rows = rows_by_name(st)
    m0 = (1.5 - swing) / 2
    lo_want, hi_want = 2 / (0.1 + m0), 2 / (0.1 + m0 - 1.5 * TOL_MAX)
    half = (RAIL - swing) / 2
    for dev in ("M1", "M3"):
        got = bound_values(rows[dev], SRC_VDSAT, "gm_id", "lo")
        assert got, (dev, rows[dev].sources)
        assert lo_want * (1 - 1e-9) <= max(got) <= hi_want, (dev, got, lo_want, hi_want)
        assert rows[dev].gm_id_lo >= max(got) * (1 - 1e-12)
    for half_split in (2 / half, 2 / (half - VDSAT_MIN)):
        assert not (lo_want <= half_split <= hi_want)                 # 대조 값이 구간 밖임을 확인(입력 검사)
