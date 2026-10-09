"""search/iv_matching_l.py -- matching L 하한(절대 offset, 설계 41 §6.4-2)과 offset 가드 부하 gm/ID 상한(§6.4-2a) (사용자 결정 2026-10-08 Q3; D-SId·D-SIg).

oracle (d) 설계 41 §6.4-2: '절대 offset 제약(offset_in_sigma_mv <= 값)이 있는 회로에서만 활성', 하한은 '입력 셀 소자 면적 하한 ... L ≥ √(A_min·IDu/I)';
구조 가드(offset_excess)만 있으면 L 하한이 아니라 부하 gm/ID 상한(§6.4-2a).
oracle (a):
- 구조: 입력 셀 소자 = gate 가 입력 포트에 닿는 MOS(two_stage_ota: M1·M2 -- topology 에서 읽는다).
- 단조: σ_target 이 작을수록 A_min = A_eff²/σ_share² 가 커져 L 하한은 같거나 커진다(A_eff 는 L·gm/ID 의 함수, 같은 1회차 전류·gm/ID).
실경로 = 실 LUT v2 + mismatch r1 감도 파일(데이터 위치 선언으로 명시 로드, u13_real) + library two_stage_ota(사용자 선언 offset_excess 가드 포함),
추가 제약 offset_in_sigma_mv 3.3 mV(파일럿 값, 설계 41 §6.4-2)·1.0 mV(단조 확인용 test 입력).
toy LUT(mismatch 데이터 없음) 에서는 offset 제약이 있어도 계산하지 않고 그 사유가 남는다(CONTRACT U13 비활성 사유).
"""
from .u13_hand import all_inactive, bound_values, cs_chain, toy_case
from .u13_real import input_gate_devices, real_case

SRC_L = "matching_l_6.4_2"
SRC_GUARD = "offset_guard_6.4_2a"
OFFSET = (("offset_in_sigma_mv", "<=", 3.3),)
OFFSET_TIGHT = (("offset_in_sigma_mv", "<=", 1.0),)


def _reasons(st, src):
    return {why for s, why in all_inactive(st) if s == src}


def test_no_absolute_offset_constraint_no_l_lower_bound():
    st = real_case("two_stage_ota").start
    assert not any(bound_values(r, SRC_L) for r in st.rows)
    assert _reasons(st, SRC_L) == {"constraint_not_declared"}


def test_absolute_offset_activates_l_lower_bound_on_input_cell_only():
    # [기대 red] 실경로에서 구현은 σ_VGS 를 얻지 못하고 `lut_mismatch_no_block`(소자 (W, L) 을 품는 모델 블록 없음)을 비활성 사유로 낸다.
    case = real_case("two_stage_ota", OFFSET)
    st = case.start
    inputs = input_gate_devices(case.topology)
    assert inputs == {"M1", "M2"}
    assert not _reasons(st, SRC_L), _reasons(st, SRC_L)
    have = {r.device for r in st.rows if bound_values(r, SRC_L, "L", "lo")}
    assert have == inputs
    for r in st.rows:
        if r.device in inputs:
            assert r.l_lo >= max(bound_values(r, SRC_L, "L", "lo")) * (1 - 1e-12)


def test_tighter_offset_target_gives_larger_l_lower_bound():
    a = {r.device: bound_values(r, SRC_L, "L", "lo") for r in real_case("two_stage_ota", OFFSET).start.rows}
    b = {r.device: bound_values(r, SRC_L, "L", "lo") for r in real_case("two_stage_ota", OFFSET_TIGHT).start.rows}
    for dev in ("M1", "M2"):
        assert a[dev] and b[dev], (a, b)
        assert max(b[dev]) >= max(a[dev])


def test_offset_guard_gives_load_upper_bound_not_l_bound():
    # library spec 은 offset_excess 가드를 선언한다 -> 부하 gm/ID 상한(§6.4-2a), 입력 소자에는 L 하한 없음.
    # [기대 red] 구현은 같은 `lut_mismatch_no_block` 으로 가드를 비활성으로 남긴다.
    case = real_case("two_stage_ota")
    st = case.start
    assert not _reasons(st, SRC_GUARD), _reasons(st, SRC_GUARD)
    guarded = {r.device for r in st.rows if bound_values(r, SRC_GUARD, "gm_id", "hi")}
    assert guarded and not (guarded & input_gate_devices(case.topology))


def test_toy_without_mismatch_data_reports_reason():
    st = toy_case(cs_chain(2), elements=(("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12)),
                  constraints=(("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0)) + OFFSET).start
    assert not any(bound_values(r, SRC_L) for r in st.rows)
    why = _reasons(st, SRC_L)
    # 사유 이름은 입력이 없는 쪽(LUT 감도 열 `lut_mismatch_unavailable` 또는 toy PDK 의 mismatch 모델 선언)을 가리킨다 -- 제약 미선언이 아니다
    assert why and "constraint_not_declared" not in why, why
