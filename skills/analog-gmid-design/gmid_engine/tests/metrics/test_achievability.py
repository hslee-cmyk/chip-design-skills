"""metrics/achievability.py -- 계산 블록 `achievability(snapshot, spec, element_values, lut, count_budget)` -> S0 수준 필드 `graph/ach`
(metrics CONTRACT 10, 설계 41 4.3~4.6, FR-8; [U17 ①-b] 설계 40 v1.9.1 §2.4.8 GB4 행 D2: 필드 curve_checks·gain_checks·…·reasons·verdict·count_budget,
묶음 `Achievability` 없음, 정지는 블록이 아니라 단계 B 가 `reasons` 필드를 읽어 낸다).

입력 조립: 블록의 입력(S0 수준 스냅샷·extras)은 파이프라인(`pipeline.run_stage_b`, 유일한 호출처)이 만든다. 이 test 는 공개 진입점(단계 A -> B)을 돌리고
단계 B 결과 스냅샷(`StageBResult.s1`)의 `graph/ach` 필드를 읽는다. 기대값은 손 계산(oracle (a), gb4_hand toy):
- 소스 팔로워 + 이상 전류원 부하, gain ≥ 10 dB: 인증된 상한 20·log10(5.6/3.9) + b 20·log10((5.6/3.9)/(5.6/5.7)) < 10 ->
  verdict infeasible, reasons = gain_target_above_upper_bound, 단계 B 정지(exit 3).
- 계수 예산을 격자 곱보다 작게 주면 블록이 미상 -> 판정하지 않는다(정지 없음, verdict ok, gain verdict undetermined).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from .gb4_hand import db, mos_e, stage_ab, toy_pdk, topology, two_e, write_case, write_lut

FOL_AMAX_DB = db(5.6 / 3.9)
FOL_B_DB = db((5.6 / 3.9) / (5.6 / 5.7))
PI_FOL = 19 * 2 * 7 * 6
ACH = "ach"


def _ach(b, field):
    """단계 B 결과 스냅샷의 `graph/ach` 필드(40 v1.9.1 §2.4.8)."""
    return b.s1.value("graph", ACH, field)


@pytest.fixture(scope="module")
def follower(tmp_path_factory):
    root = tmp_path_factory.mktemp("ach")
    lut = write_lut(root / "lut")
    pdk = toy_pdk(root / "pdk")
    topo = topology("achfol", [mos_e("M1", "nmos", "vdd", "in", "out")], sources=[two_e("I1", "current_source", "out", "gnd")])

    def run(sub, count_budget=None):
        tp, sp = write_case(root / sub, topo, elements=(("I1", "current_source", None),), constraints=(("gain_ss_db", ">=", 10.0),),
                            count_budget=count_budget)
        return stage_ab(root / sub, lut, tp, sp, pdk)[1]
    return run


def test_infeasible_reasons_field_stops_stage_b(follower):
    b = follower("stop")
    assert _ach(b, "verdict") == "infeasible"
    assert [r[0] for r in _ach(b, "reasons")] == ["gain_target_above_upper_bound"]
    assert (b.status, b.exit_code) == ("infeasible", 3)          # 정지는 단계 B 가 reasons 필드를 읽어 낸다


def test_gain_checks_field_is_hand_bound(follower):
    b = follower("bound")
    g = _ach(b, "gain_checks")
    (blk,) = g.blocks
    assert blk.status == "certified" and blk.pi == PI_FOL
    assert blk.a_max_db == pytest.approx(FOL_AMAX_DB, abs=1e-9) and blk.b_db == pytest.approx(FOL_B_DB, abs=1e-9)
    assert g.target_db == 10.0
    assert g.sum_db == pytest.approx(FOL_AMAX_DB, abs=1e-9)
    assert g.b_db == pytest.approx(FOL_B_DB, abs=1e-9)
    assert g.verdict == "infeasible" and g.n_unknown == 0
    assert _ach(b, "count_budget") == b.report["count_budget"]


def test_small_count_budget_makes_bound_unknown_and_no_stop(follower):
    b = follower("small", count_budget=PI_FOL - 1)                # 미상은 정지 근거가 아니다
    assert _ach(b, "verdict") == "ok"
    g = _ach(b, "gain_checks")
    (blk,) = g.blocks
    assert blk.status == "unknown" and blk.reason == "grid_product_over_budget"
    assert g.verdict == "undetermined" and g.n_unknown == 1
    assert _ach(b, "count_budget") == PI_FOL - 1
    assert (b.status, b.exit_code) == ("ok", 0)


def test_deterministic(follower):
    a, b = follower("det_a"), follower("det_b")
    for name in ("gain_checks", "area_bound", "headroom_rows", "reasons", "verdict", "dof"):
        assert _ach(a, name) == _ach(b, name), name


# ---------------------------------------------------------------- feedforward 뷰의 Σ 판정 (41 4.3 'feedforward 가 있는 뷰', 1.12.2-6)
# 손 회로 s1v_hand.FF: 주경로 in -> CS(M1, 부하 M2) -> a -> CS(M3) -> out, 병렬 FF 셀 PMOS CS M4(gate in -> out).
# 주경로 블록 a = {M1, M2}: x1/(y1 + y2) 최대 20/0.2 = 100; 블록 out = {M3}(FF 셀 소자는 주경로 블록에서 빠진다): x3/y3 최대 20/0.1 = 200.
# FF 상한 = (입력 -> 탭 in 체인 = 1) × (FF 국소 모델 {M4} ∪ 합류 블록 {M3}: x4/(y3 + y4) 최대 100).
# 총 상한 = 20·log10(100·200 + 100), b_GB4 = 주경로 블록 b 의 합 = 2·20·log10(20/19.2) (각 블록 최대 행의 VGS 이웃 0 -> 0.1).

FF_SUM_DB = db(100.0 * 200.0 + 100.0)
FF_B_DB = 2 * db(20.0 / 19.2)


@pytest.fixture(scope="module")
def ff_case(tmp_path_factory):
    _graph_tests_on_path()
    import s1v_hand as H
    root = tmp_path_factory.mktemp("ach_ff")
    lut = write_lut(root / "lut")
    pdk = toy_pdk(root / "pdk")

    def run(target, budget=10 ** 6, sub="x"):
        tp, sp = write_case(root / sub, H.FF, constraints=(("gain_ss_db", ">=", target),), count_budget=budget)
        return stage_ab(root / sub, lut, tp, sp, pdk)[1]
    return run


def _graph_tests_on_path():
    p = str(Path(__file__).resolve().parents[1] / "graph")
    if p not in sys.path:
        sys.path.insert(0, p)


def test_feedforward_sum_uses_product_plus_ff_bound(ff_case):
    _graph_tests_on_path()
    b = ff_case(87.0, sub="a")
    g = _ach(b, "gain_checks")
    main = {blk.key: blk for blk in g.blocks}
    assert main[("a",)].a_max_db == pytest.approx(40.0, abs=1e-9)
    assert main[("out",)].a_max_db == pytest.approx(db(200.0), abs=1e-9)
    assert tuple(main[("out",)].members) == ("M3",)
    (ff,) = g.ff
    assert ff.role == "ff" and ff.status == "certified"
    assert ff.a_max_db == pytest.approx(40.0, abs=1e-9)
    assert g.sum_db == pytest.approx(FF_SUM_DB, abs=1e-9)
    # 86.06 + 0.71 = 86.77 < 87 -> 정지
    assert (b.status, b.exit_code) == ("infeasible", 3)


def test_feedforward_resolution_is_sum_of_main_path_b(ff_case):
    # 41 4.3: 'b_GB4 는 주경로 블록 b 의 합', GainCheck 문서 'b_db = 주경로 b 의 합'
    _graph_tests_on_path()
    g = _ach(ff_case(87.0, sub="b"), "gain_checks")
    assert g.b_db == pytest.approx(sum(blk.b_db for blk in g.blocks), abs=1e-12)
    assert g.b_db == pytest.approx(FF_B_DB, abs=1e-9)


def test_feedforward_target_within_bound_is_not_stopped(ff_case):
    _graph_tests_on_path()
    b = ff_case(86.5, sub="c")
    assert (b.status, b.exit_code) == ("ok", 0)


def test_feedforward_unknown_bound_prevents_verdict(ff_case):
    # 예산 70755 < Π(블록 a = FF 묶음 = 19²·2²·7² = 70756) -> 미상이 있어 판정하지 않는다(목표가 아무리 커도 정지 없음)
    _graph_tests_on_path()
    b = ff_case(500.0, budget=70755, sub="d")
    g = _ach(b, "gain_checks")
    assert g.verdict == "undetermined" and g.sum_db is None
    assert (b.status, b.exit_code) == ("ok", 0)


def _it1_sym_nocap_doc():
    """T-1f DOF 용 대칭 차동 toy(커패시터 없음): M1(o1, inp, t) M2(o2, inn, t) M5(t, vb, gnd) M3(o1, pb, vdd) M4(o2, pb, vdd), p inp · n inn."""
    return topology("achsymdof",
                    [mos_e("M1", "nmos", "o1", "inp", "t"), mos_e("M2", "nmos", "o2", "inn", "t"), mos_e("M5", "nmos", "t", "vb", "gnd"),
                     mos_e("M3", "pmos", "o1", "pb", "vdd"), mos_e("M4", "pmos", "o2", "pb", "vdd")],
                    ports={"inp": ("input", "differential_input_p"), "inn": ("input", "differential_input_n"),
                           "o1": ("output", "differential_output_p"), "o2": ("output", "differential_output_n")},
                    bias=["pb", "vb"])


def test_it1_t1f_structural_dof_of_symmetric_pair(tmp_path):
    """T-1f (손): 커패시터 없는 대칭 차동 toy 의 단계 B graph/ach dof. 구조 rank 는 이분 매칭 rank(41 §4.5). 손 유도: 입력 점 병합으로 노드전압 변수
    V:inn 하나가 줄어 변수 17 (base 18), 방정식 5, 구조 rank 5, 매칭 안 된 방정식 없음, 자유 변수 = 17 - 5 = 12."""
    root = tmp_path
    lut = write_lut(root / "lut")
    pdk = toy_pdk(root / "pdk")
    tp, sp = write_case(root / "case", _it1_sym_nocap_doc())
    _, b = stage_ab(root / "case", lut, tp, sp, pdk)
    d = _ach(b, "dof")
    assert (d.status, d.n_variables, d.n_equations, d.structural_rank) == ("free_dof", 17, 5, 5)
    assert len(d.free_variables) == 12 and d.unmatched_equations == ()
    assert "V:inn" not in d.free_variables
