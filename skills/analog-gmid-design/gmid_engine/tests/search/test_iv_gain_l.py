"""search/iv_gain_l.py -- 이득 L 하한 활성 판정 (설계 41 §6.4-1, H3; D-SIc).

oracle (d) 설계 41 §6.4-1: '블록 목표 g_i = G·A_i,max/ΣA_max 를 만족하는 최소 L ... A_max 가 미상이거나 gain 제약이 없으면 비활성이다.'
+ CONTRACT U13 비활성 사유 어휘(constraint_not_declared, u9_value_not_certified) -- 비활성은 조용히 빠지지 않는다.
손 회로 = 2단 CS 사슬(toy LUT: 단마다 A_max = 20/(0.1 + 0.1) = 100 = 40 dB, Π = 19²·2²·7² = 70756 -- tests/pipeline test_stage_b 와 같은 손계산):
spec `structure_count_budget` 10⁶ 이면 인증, 미선언(기본 N_S < Π)이면 미상.
"""
from .u13_hand import all_inactive, bound_values, cs_chain, toy_case

SRC = "gain_l_6.4_1"
ELS = (("C1", "capacitor", 1e-12), ("C2", "capacitor", 1e-12))
GAIN = (("gain_ss_db", ">=", 60.0),)


def _start(constraints, count_budget, with_ach=True):
    return toy_case(cs_chain(2), elements=ELS, constraints=constraints, count_budget=count_budget, with_ach=with_ach).start


def _reasons(st):
    return {why for src, why in all_inactive(st) if src == SRC}


def test_no_gain_constraint_inactive_not_declared():
    st = _start((), 10 ** 6)
    assert _reasons(st) == {"constraint_not_declared"}
    assert not any(bound_values(r, SRC) for r in st.rows)


def test_uncertified_a_max_inactive_with_reason():
    st = _start(GAIN, None)
    assert _reasons(st) == {"u9_value_not_certified"}
    assert not any(bound_values(r, SRC) for r in st.rows)


def test_without_achievability_reason_is_reported():
    st = _start(GAIN, 10 ** 6, with_ach=False)
    assert _reasons(st)                       # 단계 B 결과가 없으면 비활성 사유가 남는다(조용히 빠지지 않는다)


def test_certified_a_max_and_gain_constraint_activates_l_lower_bound():
    # 41 §6.4-1: A_max 인증 + gain 제약 -> 활성. toy LUT 에서 블록 gain 은 L 무관(gds/ID·gm/ID 가 L 에 무관)이라 최소 L = LUT L 최솟값 1 µm.
    # [기대 red] 구현은 인증된 블록의 L 풀이를 연결하지 않고 `certified_block_local_model_not_wired` 를 비활성 사유로 낸다(iv_gain_l docstring).
    st = _start(GAIN, 10 ** 6)
    assert not _reasons(st), _reasons(st)
    got = {r.device: bound_values(r, SRC, "L", "lo") for r in st.rows}
    for dev in ("MN1", "MN2"):
        assert got[dev] and min(got[dev]) == 1e-6
