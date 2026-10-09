"""metrics/achievability.py -- `achievability(s1, s1v, spec, kctx, *, count_budget, cur_rep, current_box, area_resolution_m2,
passive_area, stop=True) -> Achievability` (metrics CONTRACT 10, 설계 41 4.3~4.6, FR-8).

입력 조립: 진입점의 인자는 파이프라인(`pipeline.run_stage_b`, 유일한 호출처)이 S0 에서 만든다. 이 test 는 그 공개 진입점을 한 번 돌리며
`sys.setprofile` 로 `achievability` 호출 인자를 그대로 받아(소스 경로를 몰라도 되는 관찰 -- metrics conftest `count_calls` 와 같은 방법)
같은 인자로 진입점을 직접 부른다. 기대값은 손 계산(oracle (a), gb4_hand toy):
- 소스 팔로워 + 이상 전류원 부하, gain ≥ 10 dB: 인증된 상한 20·log10(5.6/3.9) + b 20·log10((5.6/3.9)/(5.6/5.7)) < 10 ->
  `stop=True` 면 `InfeasibleTargetError`(`.achievability` 에 결과), `stop=False` 면 verdict infeasible 을 돌려준다.
- 계수 예산을 격자 곱보다 작게 주면 블록이 미상 -> 판정하지 않는다(정지 없음, verdict ok, gain verdict undetermined).
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

from gmid_engine.core import InfeasibleTargetError
from gmid_engine.metrics import Achievability, achievability

from .gb4_hand import db, mos_e, stage_ab, toy_pdk, topology, two_e, write_case, write_lut

FOL_AMAX_DB = db(5.6 / 3.9)
FOL_B_DB = db((5.6 / 3.9) / (5.6 / 5.7))
PI_FOL = 19 * 2 * 7 * 6


@contextmanager
def capture_args(func):
    """func 호출 인자(첫 호출)를 frame locals 로 받는다."""
    code = func.__code__
    got = {}
    prev = sys.getprofile()

    def prof(frame, event, arg):
        if event == "call" and frame.f_code is code and not got:
            got.update(frame.f_locals)

    sys.setprofile(prof)
    try:
        yield got
    finally:
        sys.setprofile(prev)


@pytest.fixture(scope="module")
def captured(tmp_path_factory):
    root = tmp_path_factory.mktemp("ach")
    lut = write_lut(root / "lut")
    pdk = toy_pdk(root / "pdk")
    topo = topology("achfol", [mos_e("M1", "nmos", "vdd", "in", "out")], sources=[two_e("I1", "current_source", "out", "gnd")])
    tp, sp = write_case(root, topo, elements=(("I1", "current_source", None),), constraints=(("gain_ss_db", ">=", 10.0),))
    with capture_args(achievability) as args:
        _, b = stage_ab(root, lut, tp, sp, pdk)
    assert args, "run_stage_b did not call metrics.achievability"
    names = ("s1", "s1v", "spec", "kctx", "count_budget", "cur_rep", "current_box", "area_resolution_m2", "passive_area")
    return {k: args[k] for k in names}, b


def _call(args, **over):
    a = dict(args)
    a.update(over)
    pos = (a.pop("s1"), a.pop("s1v"), a.pop("spec"), a.pop("kctx"))
    return achievability(*pos, **a)


def test_stop_raises_infeasible_with_result_attached(captured):
    args, _ = captured
    with pytest.raises(InfeasibleTargetError) as ei:
        _call(args, stop=True)
    res = ei.value.achievability
    assert isinstance(res, Achievability)
    assert res.verdict == "infeasible"
    assert [r[0] for r in res.reasons] == ["gain_target_above_upper_bound"]


def test_no_stop_returns_hand_bound(captured):
    args, _ = captured
    res = _call(args, stop=False)
    assert res.verdict == "infeasible"
    (blk,) = res.gain.blocks
    assert blk.status == "certified" and blk.pi == PI_FOL
    assert blk.a_max_db == pytest.approx(FOL_AMAX_DB, abs=1e-9) and blk.b_db == pytest.approx(FOL_B_DB, abs=1e-9)
    assert res.gain.target_db == 10.0
    assert res.gain.sum_db == pytest.approx(FOL_AMAX_DB, abs=1e-9)
    assert res.gain.b_db == pytest.approx(FOL_B_DB, abs=1e-9)
    assert res.gain.verdict == "infeasible" and res.gain.n_unknown == 0
    assert res.count_budget == args["count_budget"]
    # 같은 결과가 단계 B 보고서에도 실린다
    assert res == captured[1].achievability


def test_small_count_budget_makes_bound_unknown_and_no_stop(captured):
    args, _ = captured
    res = _call(args, count_budget=PI_FOL - 1, stop=True)            # 던지지 않아야 한다(미상은 정지 근거가 아니다)
    assert res.verdict == "ok"
    (blk,) = res.gain.blocks
    assert blk.status == "unknown" and blk.reason == "grid_product_over_budget"
    assert res.gain.verdict == "undetermined" and res.gain.n_unknown == 1
    assert res.count_budget == PI_FOL - 1


def test_deterministic(captured):
    args, _ = captured
    assert _call(args, stop=False) == _call(args, stop=False)


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
    g = b.achievability.gain
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
    g = ff_case(87.0, sub="b").achievability.gain
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
    g = b.achievability.gain
    assert g.verdict == "undetermined" and g.sum_db is None
    assert (b.status, b.exit_code) == ("ok", 0)
