"""search/iv_matching_l.py -- matching L 하한(절대 offset, 설계 41 §6.4-2)과 offset 가드 부하 gm/ID 상한(§6.4-2a) (사용자 결정 2026-10-08 Q3; D-SId·D-SIg).

oracle (d) 설계 41 §6.4-2: '절대 offset 제약(offset_in_sigma_mv <= 값)이 있는 회로에서만 활성', 하한은 '입력 셀 소자 면적 하한 ... L ≥ √(A_min·IDu/I)';
구조 가드(offset_excess)만 있으면 L 하한이 아니라 부하 gm/ID 상한(§6.4-2a).
oracle (a):
- 구조: 입력 셀 소자 = gate 가 입력 포트에 닿는 MOS(two_stage_ota: M1·M2 -- topology 에서 읽는다).
- 단조: σ_target 이 작을수록 A_min = A_eff²/σ_share² 가 커져 L 하한은 같거나 커진다(A_eff 는 L·gm/ID 의 함수, 같은 1회차 전류·gm/ID).
실경로 = 실 LUT v2 + mismatch r1 감도 파일(데이터 위치 선언으로 명시 로드, u13_real) + library two_stage_ota(사용자 선언 offset_excess 가드 포함),
추가 제약 offset_in_sigma_mv 3.3 mV(파일럿 값, 설계 41 §6.4-2)·1.0 mV(단조 확인용 test 입력).
toy LUT(mismatch 데이터 없음): 설계 41 §6.4-2b '감도 데이터가 없는데 offset 제약이 선언되면 `SchemaRejectedError(mismatch_lut_missing)`'
(lut CONTRACT 9.5 `require_lut_data` -- 호출부는 search 시작) -> 절대 offset 제약은 탐색 문맥을 만들 때 거부된다. 그 거부를 거치지 않은 출발 입력 묶음
(u13_hand `start_ctx_with`)에서는 `matching_bounds` 가 계산하지 않고 그 사유가 남는다(CONTRACT U13 비활성 사유).
CONTRACT U13 'mismatch/잡음 질의의 폭은 W_min 이상으로 맞춘다(모델 bin 밖 폭 방지)' + (a) 설계 41 §6.4-2 σ_VGS ∝ 1/√(W·L): W < W_min 인 전류에서는
폭이 W_min 으로 고정돼 같은 σ, 폭이 커지면 σ 가 줄어든다(bin 이 바뀌면 slope 비가 바뀌므로 비례 상수는 확인하지 않는다).
"""
import ast
import math

import pytest

from gmid_engine.core.failure_errors import SchemaRejectedError
from gmid_engine.search.iv_context import build_start_context
from gmid_engine.search.iv_matching_l import matching_bounds

from .u13_hand import all_inactive, bound_values, cs_chain, rows_by_name, start_ctx_with, toy_case
from .u13_real import input_gate_devices, real_case, real_env

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
    # (24cfecd 에서 red: σ 질의 폭이 W_min 아래라 `lut_mismatch_no_block` -- 75626c8 의 폭 보정으로 해소)
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
    # (24cfecd 에서 red: 같은 `lut_mismatch_no_block` -- 75626c8 에서 해소)
    case = real_case("two_stage_ota")
    st = case.start
    assert not _reasons(st, SRC_GUARD), _reasons(st, SRC_GUARD)
    guarded = {r.device for r in st.rows if bound_values(r, SRC_GUARD, "gm_id", "hi")}
    assert guarded and not (guarded & input_gate_devices(case.topology))


TOY_ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))
TOY_TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))


def test_toy_absolute_offset_without_mismatch_data_is_rejected():
    # 설계 41 §6.4-2b·lut CONTRACT 9.5: mismatch 감도 데이터가 없는 LUT 에 절대 offset 제약 -> SchemaRejectedError(mismatch_lut_missing)
    # [기대 red, 75626c8] search 시작 검사(search CONTRACT U8 절)는 잡음만 부른다 -- offset 제약은 거부되지 않고 출발 구간까지 간다.
    with pytest.raises(SchemaRejectedError) as ei:
        toy_case(cs_chain(2), elements=TOY_ELS, constraints=TOY_TARGETS + OFFSET, fresh=True)
    assert ast.literal_eval(ei.value.args[0])["detail"]["reason"] == "mismatch_lut_missing"


def test_toy_without_mismatch_data_reports_reason_at_iv_matching():
    ctx, cur, lengths, lo = start_ctx_with(cs_chain(2), TOY_ELS, TOY_TARGETS, OFFSET)
    mb = matching_bounds(ctx, cur, lengths, lo)
    assert not [b for bs in mb.bounds.values() for b in bs if b.source == SRC_L]
    why = {w for s, w in mb.inactive if s == SRC_L}
    # 사유 이름은 입력이 없는 쪽(LUT 감도 열)을 가리킨다 -- 제약 미선언이 아니다
    assert why and "constraint_not_declared" not in why, why


@pytest.mark.parametrize("dev", ["M1", "M3"])
def test_sigma_query_width_is_at_least_w_min(dev):
    # CONTRACT U13 'mismatch 질의의 폭은 W_min 이상' -- 내부 helper `_sigma_vgs(ctx, name, g, L, current)` 를 직접 부른다.
    from gmid_engine.search.iv_matching_l import _sigma_vgs
    case = real_case("two_stage_ota", OFFSET)
    ctx = build_start_context(case.s1v, case.ach, case.kctx, case.spec, real_env().pdk, case.sctx.domain)
    r = rows_by_name(case.start)[dev]
    g, L = r.gm_id_chosen, r.l_chosen
    idu = math.exp(r.ln_idu)                          # W = I·L/IDu (IDu 정의)
    w_min = float(ctx.w_min_m)
    tiny = (1e-14, 1e-13, 1e-12)
    for i in tiny:
        assert i * L / idu < w_min * 1e-2              # 입력 확인: W ≪ W_min (W_min 고정이 없으면 모델 bin 밖 폭)
    s = [_sigma_vgs(ctx, dev, g, L, i) for i in tiny]
    assert s[0] == pytest.approx(s[1], rel=1e-12) and s[1] == pytest.approx(s[2], rel=1e-12)
    wider = _sigma_vgs(ctx, dev, g, L, w_min * 4 * idu / L)    # W ≈ 4·W_min (같은 소자 kind 의 모델 bin 안 폭)
    assert wider < s[0]
