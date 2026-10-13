"""search/iv_noise.py -- 열잡음 가드 부하 gm/ID 상한(설계 41 §7.5)과 폐루프 잡음 경계 활성 여부(§7.5·§6.4-3) (D-NZ5, D-SIf).

oracle (d) 설계 41 §7.5: `noise_excess_th ≤ 2` 가드 -> 부하 열잡음 비 Σ(γ_k gm_k)/(γ_in gm_in) ≤ 1 이 되도록 **부하 gm/ID 상한**(속도 상한과 교집합).
oracle (a) 존재 논증(two_stage_ota, 입력쌍 M1·M2 + 미러 부하 M3·M4, 가지 전류 같음 r = 1): 부하 gm/ID 를 LUT 최솟값(≈ 1.4, 강반전)까지 낮추면
비 = Σ_load γ_p·g_load / Σ_in γ_n·g_in ≈ (γ_p/γ_n)·1.4/16 -- γ 비가 10 미만인 한 1 보다 작다. 그러므로 가드는 LUT 범위 안의 유한한 부하 상한을 내야 하고
'어느 g 도 만족하지 않는다'는 충돌은 나올 수 없다.
oracle (d) 설계 41 §7.2 '잡음 데이터가 없는데 잡음 제약이 선언되면 `SchemaRejectedError(noise_lut_missing)`' -- toy LUT(잡음 r1 없음)에 잡음 제약을
선언한 회로는 출발 구간까지 가지 못하고 탐색 문맥을 만들 때 거부된다(U8 시작 시 검사).
oracle (d) CONTRACT U13 비활성 사유: 잡음 데이터 없음 `lut_noise_unavailable`, 제약 없음 `constraint_not_declared`, `noise_out_int_vrms` 의 C_eff·1/f 하한은
의존 단위 사유 -- 사유가 조용히 빠지지 않는다. 위 거부 때문에 '데이터 없음' 사유는 공개 진입점으로는 닿지 않으므로 `iv_noise.noise_bounds` 수준에서
(잡음 제약이 있는 spec + 잡음 r1 없는 LUT 로 만든 출발 입력 묶음) 직접 확인한다.
oracle (d) CONTRACT U13 'mismatch/잡음 질의의 폭은 W_min 이상으로 맞춘다' + (a) 설계 41 §7.2 B 의 폭 환산(게이트 환산 S_vg ∝ W_ref/W):
W ≥ W_min 인 전류에서는 같은 gm/ID·L 이면 W ∝ I 라 밀도 ∝ 1/I, W < W_min 인 전류에서는 폭이 W_min 으로 고정돼 같은 값.
"""
import ast
import math

import pytest

from gmid_engine.core.failure_errors import SchemaRejectedError
from gmid_engine.search.iv_noise import noise_bounds

from .u13_hand import all_inactive, bound_values, cs_chain, rows_by_name, start_ctx_with, start_view_of, toy_case
from .u13_real import input_gate_devices, real_case, real_env

SRC = "noise_guard_7.5"
CLOSED_SRCS = ("thermal_c_7.5", "flicker_l_6.4_3")
ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))
TARGETS = (("gbw_ss_hz", ">=", 1e6), ("pm_ss_deg", ">=", 60.0))
GUARD = (("noise_excess_th", "<=", 2.0),)
CLOSED = (("noise_out_int_vrms", "<=", 1e-4),)


def _reasons(st, src):
    return {why for s, why in all_inactive(st) if s == src}


def _rejection_reason(exc):
    return ast.literal_eval(exc.args[0])["detail"]["reason"]


@pytest.mark.parametrize("extra", [GUARD, CLOSED], ids=["noise_excess_th", "noise_out_int_vrms"])
def test_toy_noise_constraint_without_noise_data_is_rejected(extra):
    # 설계 41 §7.2: 잡음 데이터(잡음 r1)가 없는 LUT 에 잡음 제약 -> SchemaRejectedError(noise_lut_missing); 출발 구간을 만들지 않는다
    with pytest.raises(SchemaRejectedError) as ei:
        toy_case(cs_chain(2), elements=ELS, constraints=TARGETS + extra, fresh=True)
    assert _rejection_reason(ei.value) == "noise_lut_missing"


def _direct_noise_bounds(extra):
    """잡음 제약이 있는 spec + 잡음 r1 없는 toy LUT 의 출발 입력 묶음으로 `noise_bounds` 를 부른다(u13_hand `start_ctx_with`)."""
    ctx, cur, lengths, lo = start_ctx_with(cs_chain(2), ELS, TARGETS, extra)
    return noise_bounds(ctx, cur, lengths, lo)


def _all_bounds(nb):
    return [b for bs in nb.bounds.values() for b in bs]


def test_toy_guard_without_noise_data_reports_reason_at_iv_noise():
    nb = _direct_noise_bounds(GUARD)
    assert not [b for b in _all_bounds(nb) if b.source == SRC]
    assert {why for s, why in nb.inactive if s == SRC} == {"lut_noise_unavailable"}


def test_toy_closed_loop_noise_bounds_report_reason_at_iv_noise():
    nb = _direct_noise_bounds(CLOSED)
    for src in CLOSED_SRCS:
        why = {w for s, w in nb.inactive if s == src}
        assert why and "constraint_not_declared" not in why, (src, why)
    assert not [b for b in _all_bounds(nb) if b.source in CLOSED_SRCS]


def test_toy_guard_not_declared():
    st = toy_case(cs_chain(2), elements=ELS, constraints=TARGETS).start
    assert _reasons(st, SRC) == {"constraint_not_declared"}


def test_real_thermal_guard_bounds_loads_without_conflict():
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


@pytest.mark.parametrize("dev", ["M1", "M3"])
def test_noise_density_query_width_is_at_least_w_min(dev):
    # CONTRACT U13 '잡음 질의의 폭은 W_min 이상' -- 내부 helper `_white_density(ctx, name, g, L, current)` 를 직접 부른다.
    from gmid_engine.search.iv_noise import _white_density
    case = real_case("two_stage_ota")
    ctx = start_view_of(case, pdk=real_env().pdk)
    r = rows_by_name(case.start)[dev]
    g, L = r.gm_id_chosen, r.l_chosen
    idu = math.exp(r.ln_idu)                         # 행의 IDu(같은 g·L) -- W = I·L/IDu (IDu 정의)
    w_min = float(ctx.w_min_m)
    tiny = (1e-13, 1e-12)
    for i in tiny:
        assert i * L / idu < w_min * 1e-2             # 입력 확인: 두 전류 모두 W ≪ W_min
    s = [_white_density(ctx, dev, g, L, i) for i in tiny]
    assert s[0] == pytest.approx(s[1], rel=1e-12)     # 폭이 W_min 으로 고정 -> 전류 10 배에도 같은 값(고정이 없으면 10 배 차)
    big = [w_min * 10 * idu / L, w_min * 100 * idu / L]       # W ≈ 10·W_min, 100·W_min
    sb = [_white_density(ctx, dev, g, L, i) for i in big]
    assert sb[0] / sb[1] == pytest.approx(10.0, rel=1e-6)    # W ≥ W_min 에서는 S_vg ∝ W_ref/W ∝ 1/I
    assert s[0] > sb[0]
