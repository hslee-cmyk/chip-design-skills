"""search/iv_noise.py -- 열잡음 가드 부하 gm/ID 상한(설계 41 §7.5)과 폐루프 잡음 경계 활성 여부(§7.5·§6.4-3) (D-NZ5, D-SIf).

oracle (d) 설계 41 §7.5: `noise_excess_th ≤ 2` 가드 -> 부하 열잡음 비 Σ(γ_k gm_k)/(γ_in gm_in) ≤ 1 이 되도록 **부하 gm/ID 상한**(속도 상한과 교집합).
oracle (a) 존재 논증(two_stage_ota, 입력쌍 M1·M2 + 미러 부하 M3·M4, 가지 전류 같음 r = 1): 부하 gm/ID 를 LUT 최솟값(≈ 1.4, 강반전)까지 낮추면
비 = Σ_load γ_p·g_load / Σ_in γ_n·g_in ≈ (γ_p/γ_n)·1.4/16 -- γ 비가 10 미만인 한 1 보다 작다. 그러므로 가드는 LUT 범위 안의 유한한 부하 상한을 내야 하고
'어느 g 도 만족하지 않는다'는 충돌은 나올 수 없다.
oracle (d) CONTRACT U13 비활성 사유: 잡음 데이터 없음 `lut_noise_unavailable`, 제약 없음 `constraint_not_declared`, `noise_out_int_vrms` 의 C_eff·1/f 하한은
U8 미병합 의존(`depends_on_unmerged_unit`) -- 사유가 조용히 빠지지 않는다.
"""
from .u13_hand import all_inactive, bound_values, cs_chain, toy_case
from .u13_real import input_gate_devices, real_case

SRC = "noise_guard_7.5"
ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))
TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))


def _reasons(st, src):
    return {why for s, why in all_inactive(st) if s == src}


def test_toy_guard_without_noise_data_reports_reason():
    st = toy_case(cs_chain(2), elements=ELS, constraints=TARGETS + (("noise_excess_th", "<=", 2.0),)).start
    assert not any(bound_values(r, SRC) for r in st.rows)
    assert _reasons(st, SRC) == {"lut_noise_unavailable"}


def test_toy_guard_not_declared():
    st = toy_case(cs_chain(2), elements=ELS, constraints=TARGETS).start
    assert _reasons(st, SRC) == {"constraint_not_declared"}


def test_toy_closed_loop_noise_bounds_report_reason():
    st = toy_case(cs_chain(2), elements=ELS, constraints=TARGETS + (("noise_out_int_vrms", "<=", 1e-4),)).start
    for src in ("thermal_c_7.5", "flicker_l_6.4_3"):
        assert _reasons(st, src), src
        assert not any(bound_values(r, src) for r in st.rows)


def test_real_thermal_guard_bounds_loads_without_conflict():
    # [기대 red] 실경로(잡음 r1 로드)에서 구현은 미러 부하 M3·M4 에 수준 ≈ 1.9e-25 의 '만족하는 g 없음' 충돌을 낸다(경계 없음).
    case = real_case("two_stage_ota")
    st = case.start
    assert not _reasons(st, SRC), _reasons(st, SRC)
    conflicts = [c for c in st.conflicts if any(s == SRC for s, _ in c.bounds)]
    conflicts += [c for r in st.rows for c in r.conflicts if any(s == SRC for s, _ in c.bounds)]
    assert conflicts == []
    inputs = input_gate_devices(case.topology)
    guarded = {r.device: bound_values(r, SRC, "gm_id", "hi") for r in st.rows}
    have = {d for d, v in guarded.items() if v}
    assert {"M3", "M4"} <= have and not (have & inputs)
    for d in have:
        row = next(r for r in st.rows if r.device == d)
        assert min(guarded[d]) >= row.gm_id_lo                  # 유한하고 LUT 범위 하한 이상(존재 논증)
