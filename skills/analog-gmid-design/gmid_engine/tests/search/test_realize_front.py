"""실현 평가 `realize_front(sctx, points) -> RealizeOutcome` (WB-1 R-1·R-4·R-7·R-9, FS-1 §6 O-1·O-3·O-4).

[FS-1 재작성] 옛 R-2·R-3·R-5·R-6 계열·R-8·R-10(후반)·R-12·R-15·R-16·S3-6 test 는 '탐색 스냅샷 `dc_finger` (m, w_s) 를 실현 입력으로 바꿔치기(tamper)' 하는 구성이라
입력 경로 자체가 사라졌다 (실현 m 은 실현 평가 DC 블록이 `realize_fingers` 로 정한다 -- interface §4.3). 이름·사유는 tests/RETIRED_TESTS_fs1.md.

oracle 종류와 출처
- R-1 (식): 탐색 W = I·L/exp(ln IDu); 실현 W' = m·(w_key·grid), 실현 `dc_finger.residual` = m·w_f/W_탐색 − 1, 실현 전류밀도 = I'·L/W' (dc_op 의 current·L·ln_idu·W 항등식).
- O-1 (식, interface §6): JSON `front[i].finger_residual` = 실현 스냅샷 `dc_finger` residual (탐색 residual 은 0.0), front 행에 `slice_rounds` 키 없음.
- O-3 (식, 계획 Q-FS1 (2)): `realize.lost` 항목에 `small_m` (m ≤ 2 인 MOS 이름 정렬 목록, dc_finger 없으면 None).
- R-4·R-7·R-9 (d): interface 표의 사유 어휘·분기 -- 실현 평가 실패 점은 lost, servo 분기 불일치는 lost, find_front 가 realize 를 한 번 부른다.
"""
import dataclasses
import json
import math
import sys
from pathlib import Path

import pytest

from .conftest import CELLS_C, circuit_c, evaluate, theta_r4c
from .wb1_flow import R2_CELLS, R2_ELEMENTS, bins_case, circuit_r2, r2_theta, sorted_theta

GRID = 1e-8


def mod(name):
    return sys.modules["gmid_engine.search." + name]


def replace_snap(ev, snap):
    return dataclasses.replace(ev, evaluation=dataclasses.replace(ev.evaluation, snapshot=snap))


@pytest.fixture(scope="module")
def r2(tmp_path_factory):
    case = bins_case(tmp_path_factory.mktemp("wb1_r2"), circuit_r2(), elements=R2_ELEMENTS)
    th = r2_theta(case.dc)
    ev = evaluate(case.sctx, sorted_theta(th), R2_CELLS)
    ops = dict(ev.evaluation.snapshot.column("device", "dc_op"))
    # 전제 (손): 탐색 W_M1 = W_M2 = 2e-6 (V(out) = V(x) 로 고정)
    assert abs(ops["M1"].W - 2e-6) <= 1e-3 * 2e-6 and abs(ops["M2"].W - 2e-6) <= 1e-2 * 2e-6, (ops["M1"].W, ops["M2"].W)
    fing = dict(ev.evaluation.snapshot.column("device", "dc_finger"))
    assert fing["M1"].residual == 0.0 and fing["M1"].m == ops["M1"].W / (ops["M1"].w_key * GRID)        # [FS-1 §4.2] 탐색 = 실수 m, residual 0.0
    return case, th, ev


def realize(case, *evs, ids=None):
    from gmid_engine.search import FrontPoint, realize_front
    ids = ids or ["p%d" % i for i in range(len(evs))]
    pts = tuple(FrontPoint(i, e, ()) for i, e in zip(ids, evs))
    return pts, realize_front(case.sctx, pts)


def lost_of(out):
    return {pid: (reason, detail) for pid, reason, detail in out.lost}


# ---------------------------------------------------------------- R-1
def test_realize_r1_search_and_realized_widths_and_current_density(r2):
    case, th, ev = r2
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == ()
    s_ops = dict(ev.evaluation.snapshot.column("device", "dc_op"))
    for m, o in s_ops.items():                                     # 탐색: W = I·L/IDu
        assert o.W == pytest.approx(o.current * o.L / math.exp(o.ln_idu), rel=1e-9), m
    rsnap = out.points[0].result.evaluation.snapshot
    r_ops, r_fing = dict(rsnap.column("device", "dc_op")), dict(rsnap.column("device", "dc_finger"))
    assert len(r_fing) == len(r_ops) >= 4
    for m, o in r_ops.items():                                     # 실현: W' = m·w_f, 전류밀도 = I'·L/W', residual = m·w_f/W_탐색 − 1
        f = r_fing[m]
        w_f = o.w_key * GRID
        assert type(f.m) is int and f.m >= 1
        assert o.W == pytest.approx(f.m * w_f, rel=1e-12), m
        assert o.current * o.L / o.W == pytest.approx(math.exp(o.ln_idu), rel=1e-9), m
        assert f.residual == f.m * w_f / s_ops[m].W - 1.0, m


# ---------------------------------------------------------------- R-4
def test_realize_r4_failed_point_is_lost_and_survivor_stays(r2, monkeypatch):
    from gmid_engine.core import SealViolationError
    case, th, ev = r2
    th_b = dict(th)
    th_b[("current", "M3")] = math.nextafter(th_b[("current", "M3")], 1.0)
    th_b[("current", "M4")] = th_b[("current", "M3")]
    ev_b = evaluate(case.sctx, sorted_theta(th_b), R2_CELLS)
    rf = mod("realize_front")
    real = rf.evaluate
    bad_theta = tuple(ev_b.theta)
    state = {"n": 0}

    def wrapped(sctx, theta, cells, *a, **k):
        state["n"] += 1
        if tuple(theta) == bad_theta:
            raise SealViolationError(devices=("M1",), margin=0.5, detail={"item": 7, "reason": "wb1_test_forced_failure"})
        return real(sctx, theta, cells, *a, **k)
    monkeypatch.setattr(rf, "evaluate", wrapped)
    pts, out = realize(case, ev, ev_b, ids=["good", "bad"])
    assert state["n"] >= 2
    assert [p.point_id for p in out.points] == ["good"]
    lost = lost_of(out)
    assert set(lost) == {"bad"} and isinstance(lost["bad"][0], str) and lost["bad"][0]


# ---------------------------------------------------------------- R-7
def test_realize_r7_servo_branch_mismatch_is_lost(r2, monkeypatch):
    from gmid_engine.sizing import ICM_CONFIG_WRITER
    from sizing.conftest import tamper
    case, th, ev = r2
    cfg0 = next(iter(dict(ev.evaluation.snapshot.column("graph", "icm_config")).values()))
    assert cfg0.config == "servo"                                   # 전제 (미측정: R-2 회로 servo 갈래)
    rf = mod("realize_front")
    real = rf.evaluate
    seen = {"n": 0}

    def wrapped(*a, **k):
        r = real(*a, **k)
        seen["n"] += 1
        snap = r.evaluation.snapshot
        key, cfg = next(iter(dict(snap.column("graph", "icm_config")).items()))
        new = dataclasses.replace(cfg, config="as_is_single_input")
        return replace_snap(r, tamper(snap, ICM_CONFIG_WRITER, "graph", "icm_config", {key: new}))
    monkeypatch.setattr(rf, "evaluate", wrapped)
    _, out = realize(case, ev)
    assert seen["n"] >= 1
    assert out.points == () and lost_of(out)["p0"][0] == "realized_servo_branch_mismatch"


# ---------------------------------------------------------------- R-9
def test_realize_r9_find_front_calls_realize_once_and_front_is_realized(tmp_path, monkeypatch, short_root):
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep, real_rf = ff.sweep_front, ff.realize_front
    rec = []

    def sweep(*a, **k):
        out = dict(real_sweep(*a, **k))
        out["front"] = tuple(out["front"])[:1]                      # front 한 점을 낸 stub
        return out

    def rf(sctx, points):
        o = real_rf(sctx, points)
        rec.append((tuple(points), o))
        return o
    monkeypatch.setattr(ff, "sweep_front", sweep)
    monkeypatch.setattr(ff, "realize_front", rf)
    fr = find_front(case.sctx, [theta_r4c()])
    assert len(rec) == 1                                            # 호출 0 이면 red
    pts_in, out = rec[0]
    assert len(pts_in) == 1
    assert [p.point_id for p in fr.front] == [p.point_id for p in out.points]
    assert all(a.result is b.result and a.result is not pts_in[0].result for a, b in zip(fr.front, out.points))


# ---------------------------------------------------------------- O-1 / O-4
def _runs_line(root, sctx):
    (run,) = [json.loads(x) for x in (Path(root) / sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    return run


def test_realize_o1_json_finger_residual_is_the_realized_value_and_no_slice_rounds(tmp_path, short_root):
    """[FS-1 O-1·O-4] JSON `front[i].finger_residual` = {MOS: 실현 스냅샷 dc_finger residual} (탐색 residual 은 0.0 이라 다르다 -- 정수가 아닌 W/w_f 소자가
    있을 때), front 행에 `slice_rounds` 키 없음. 손 값 residual = m·w_f/W_θ − 1 (탐색 DeviceOp.W 와 실현 m·w_f 로 기대값을 만든다)."""
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep, searched = ff.sweep_front, []

    def sweep(*a, **k):
        out = real_sweep(*a, **k)
        searched.extend(out["front"])                                # 탐색 점(탐색 스냅샷 DeviceOp.W 가 기대값의 입력)
        return out
    ff.sweep_front = sweep
    try:
        fr = find_front(case.sctx, [theta_r4c()])
    finally:
        ff.sweep_front = real_sweep
    assert len(searched) >= 1 and len(fr.front) >= 1
    by_id = {p.point_id: p for p in searched}
    run = _runs_line(short_root, case.sctx)
    assert len(run["front"]) == len(fr.front)
    nonzero = 0
    for entry, p in zip(run["front"], fr.front):
        s_ops = dict(by_id[p.point_id].result.evaluation.snapshot.column("device", "dc_op"))
        r_snap = p.result.evaluation.snapshot
        r_fing, r_ops = dict(r_snap.column("device", "dc_finger")), dict(r_snap.column("device", "dc_op"))
        got = dict(entry["finger_residual"])
        assert set(got) == set(r_fing)
        for m, f in r_fing.items():
            w_f = r_ops[m].w_key * GRID
            assert got[m] == f.m * w_f / s_ops[m].W - 1.0           # 손 식: 실현 m·w_f / 탐색 W − 1
            nonzero += got[m] != 0.0
        assert "slice_rounds" not in entry                         # O-4
    assert nonzero >= 1                                            # 전제: 탐색 residual(0.0)과 다른 소자가 있다
    assert {"lost", "n_lost"} <= set(dict(run["realize"]))


# ---------------------------------------------------------------- O-3
# O-3 는 아래 R-6c 시나리오(실현에서 실제로 잃는 점: 근 없음 -> fail-closed)에서 본다 -- `test_realize_r6c_..._small_m` (A-190 M-3: 동작 대체 stub 없음).


# =====================================================================================================================
# [FS-1 A-190 M-5] 실현·재풀이 성질 test 를 새 실현 경로로 다시 쓴다 (옛 구성 = 탐색 dc_finger 바꿔치기, 삭제됨).
# 입력 만들기: 실현 m 은 interface §1 손 oracle (`sizing/test_realize_fingers.hand_oracle`) 로 미리 정한다. 칸 키 200 (w_f = 2e-6) 에서 탐색 W 가 w_f/(1 + r) 가 되도록 θ 전류를
# 스케일하면 (W ∝ I: IDu 는 (VSD, VSG) 좌표만의 함수) x = W/w_f < 1 -> m = 1 (W < w_f -> 1, interface R-6), 실현 W' = w_f, r = W'/W − 1 = 목표 r.
# 기대값(oracle (a)): 옛 test 와 같은 독립 이분법 `wb1_hand` 해 -- r 은 스냅샷의 실현 W / 탐색 W 에서 읽는다 (m·w_f 를 피검 함수 출력으로 만들지 않는다).
# =====================================================================================================================
from sizing.conftest import LAM, seal_item                                     # noqa: E402
from wb1_hand import mos_load_out_shift, source_load_kcl_at_vdd, source_load_out_shift  # noqa: E402
from .conftest import hand_wf_of                                               # noqa: E402
from .wb1_flow import R6_ELEMENTS, R6_I, R6_R, VDD, VGS0, circuit_r16, circuit_s36, circuit_r6, single_mos_resistor_theta  # noqa: E402

def hand_oracle(*a, **k):
    """interface §1 손 oracle (`sizing/test_realize_fingers`) -- 새 이름 import 가 이 파일 전체의 수집 오류가 되지 않게 호출 때 가져온다 (판정 n-6)."""
    from sizing.test_realize_fingers import hand_oracle as _hand_oracle
    return _hand_oracle(*a, **k)


KEY = 200
WF = KEY * GRID                         # 칸 키 200 -> w_f = 2e-6
WIDE_R = (1e3, 1e9)                     # 스케일한 θ 저항을 품는 탐색 정의역 입력
R16_I, R16_R, R16_IB = 1e-5, 2.5e4, 2e-6
S36_VOUT, S36_I = 0.4, 5e-6


def _ev(case, th, cells=(0,), keys=None):
    return evaluate(case.sctx, sorted_theta(th), cells, wf=hand_wf_of(case.sctx, keys or {"M1": KEY, "M2": KEY}))


def _w_of(ev, m="M1"):
    return dict(ev.evaluation.snapshot.column("device", "dc_op"))[m].W


def _scaled_single_mos(case, theta_fn, i0, a, r_target):
    """탐색 W(M1) = w_f/(1 + r_target) 인 점. theta_fn(i, res) -> θ. a = I·R (고정: V(out) 또는 V(s) 의 손 값). -> (ev, i, res)."""
    w0 = _w_of(_ev(case, theta_fn(i0, a / i0)))
    i = i0 * (WF / (1.0 + r_target)) / w0                                       # W ∝ I
    ev = _ev(case, theta_fn(i, a / i))
    assert _w_of(ev) == pytest.approx(WF / (1.0 + r_target), rel=1e-6), "스케일 전제 불성립 -- 멈추고 보고"
    return ev, i, a / i


def _r_from_oracle(ev, m="M1"):
    w = _w_of(ev, m)
    mm = hand_oracle((w,), WF, ())[4][0]
    return mm, mm * WF / w - 1.0


def _r6_case(tmp_path):
    return bins_case(tmp_path, circuit_r6(), elements=R6_ELEMENTS, rbounds=WIDE_R)


def _r6_point(case, r_target, icm_none=False):
    a = R6_I * R6_R
    ev, i, res = _scaled_single_mos(case, lambda ii, rr: single_mos_resistor_theta(case.dc, ii, rr, VDD - a, kind="pmos"), R6_I, a, r_target)
    m, r = _r_from_oracle(ev)
    assert m == 1 and r == pytest.approx(r_target, rel=1e-5)                    # 전제: W < w_f -> m = 1 (손 oracle), r = 목표
    if icm_none:
        from gmid_engine.sizing import ICM_CONFIG_WRITER
        from sizing.conftest import tamper
        snap = ev.evaluation.snapshot
        key, cfg = next(iter(dict(snap.column("graph", "icm_config")).items()))
        ev = replace_snap(ev, tamper(snap, ICM_CONFIG_WRITER, "graph", "icm_config", {key: dataclasses.replace(cfg, config=None)}))
    return ev, r, a, i, res


@pytest.mark.parametrize("icm_none", [False, True], ids=["natural_as_is_single_input", "icm_config_none"])
def test_realize_r6_input_fixed_branch_resolves_kcl_and_reseals(tmp_path, icm_none):
    case = _r6_case(tmp_path)
    ev, r, a, i, res = _r6_point(case, 0.5, icm_none)
    cfg = next(iter(dict(ev.evaluation.snapshot.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                           # 전제: 입력 고정 갈래
    hand = source_load_out_shift(a, r, LAM)
    assert VDD - (a + hand) > 0.455                                             # 전제 (손): 재풀이 점에서도 M1 포화 (VSD >= VDSAT_p(0.6))
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == (), out.lost
    snap, rsnap = ev.evaluation.snapshot, out.points[0].result.evaluation.snapshot
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    assert v1["in"] == pytest.approx(v0["in"], rel=1e-12)
    dv = v1["out"] - v0["out"]
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(dv) >= abs(hand) / 2.0, (dv, hand)
    assert abs(dv - hand) <= tol, ("measured_dV_V", dv, "hand_dV_V", hand, "tol_V", tol)
    assert seal_item(rsnap, 3).status == "pass" and seal_item(rsnap, 7).status == "pass"
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(WF, rel=1e-12)       # W' = m·w_f = w_f


def test_realize_r6c_no_root_inside_rails_is_lost_fail_closed_and_lost_entry_has_small_m(tmp_path):
    """R-6c (fail-closed) + O-3: r = 2 (W = w_f/3 -> m = 1, 손 oracle) 이면 F(V_dd) < 0 = 레일 안 근 없음 -> lost. lost 항목은 `small_m` 키를 가진다
    (실현에서 실제로 잃는 점 -- 동작 대체 stub 없음, A-190 M-3)."""
    case = _r6_case(tmp_path)
    ok_ev, r_ok, a, i_ok, res_ok = _r6_point(case, 0.5)
    v0_ok = dict(ok_ev.evaluation.snapshot.column("node", "dc_v"))["out"]
    assert source_load_kcl_at_vdd(VDD, res_ok, i_ok, v0_ok, r_ok, LAM) > 0.0    # 전제 (손): 통제 점은 근이 레일 안에 있다
    bad_ev, r_bad, _, i_bad, res_bad = _r6_point(case, 2.0)
    v0_bad = dict(bad_ev.evaluation.snapshot.column("node", "dc_v"))["out"]
    assert source_load_kcl_at_vdd(VDD, res_bad, i_bad, v0_bad, r_bad, LAM) < 0.0    # 전제 (손): 근 없음
    _, out = realize(case, ok_ev, bad_ev, ids=["ok", "bad"])
    assert [p.point_id for p in out.points] == ["ok"]
    lost = lost_of(out)
    assert set(lost) == {"bad"} and isinstance(lost["bad"][0], str) and lost["bad"][0]
    detail = lost["bad"][1]
    d = dict(detail) if not isinstance(detail, dict) else detail
    # [FS-1 A-196 판정 #8-6, interface §6 O-3] 이 실패는 dc_solve 안에서 난다(레일 안 근 없음) -> 그 부분 스냅샷에는 `dc_finger` 가 없고 `small_m` = None
    # ('dc_finger 가 없으면 None'). (옛 기대 ['M1'] 은 탐색 `dc_finger` 행을 읽던 시절의 값.) 키는 있어야 한다.
    assert "small_m" in d and d["small_m"] is None


def test_realize_r15_input_fixed_realized_point_satisfies_output_kcl(tmp_path):
    """R-15 (식): 저항 전류 V(out)_실현/R = M1 채널 전류 I' (= dc_op.current), 허용 tol_V/R, 출력이 실제로 움직임(재풀이 호출)."""
    case = _r6_case(tmp_path)
    ev, r, a, i, res = _r6_point(case, 0.5)
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    v1, v0 = dict(rsnap.column("node", "dc_v")), dict(ev.evaluation.snapshot.column("node", "dc_v"))
    assert abs(v1["out"] - v0["out"]) > 0.1
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(v1["out"] / res - dict(rsnap.column("device", "dc_op"))["M1"].current) <= tol / res


def test_realize_r6_unresolved_servo_pivot_keeps_input_value(tmp_path):
    """R-6 (피벗 판정 불능 갈래): 입력 노드 값은 봉인점 값, W' = m·w_f (m 은 손 oracle). 전제 W' ≠ W."""
    case = bins_case(tmp_path, circuit_c())
    ev = evaluate(case.sctx, sorted_theta(theta_r4c()), CELLS_C)
    snap = ev.evaluation.snapshot
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")
    w1 = dict(snap.column("device", "dc_op"))["M1"].W
    key = dict(snap.column("device", "dc_op"))["M1"].w_key
    m = hand_oracle((w1,), key * GRID, ())[4][0]
    assert m * key * GRID != w1                                                 # 전제: W' != W (공허 방지)
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    assert dict(rsnap.column("node", "dc_v"))["in"] == dict(snap.column("node", "dc_v"))["in"]
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(m * key * GRID, rel=1e-12)


@pytest.mark.parametrize("with_source", [False, True], ids=["mos_channel_only", "with_ideal_current_source"])
def test_realize_r16_power_is_rail_current_of_realized_channel_current(tmp_path, with_source):
    """R-16 (식): 전력 = V_dd·(V(s)_실현/R + I_b), 허용 = power_resolution_w; 공허 방지 = θ 전류 전력과의 차 > power_resolution_w."""
    els = R6_ELEMENTS + ((("I2", "current_source", R16_IB),) if with_source else ())
    case = bins_case(tmp_path, circuit_r16(with_source), constraints=(), elements=els, rbounds=WIDE_R)
    a = R16_I * R16_R
    ev, i, res = _scaled_single_mos(case, lambda ii, rr: single_mos_resistor_theta(case.dc, ii, rr, VDD - a), R16_I, a, 3.0)
    ib = R16_IB if with_source else 0.0
    snap = ev.evaluation.snapshot
    assert dict(snap.column("node", "dc_v"))["s"] == pytest.approx(i * res, abs=1e-9) == pytest.approx(R16_I * R16_R, abs=1e-9)    # 전제 (손): 탐색 V(s) = I·R (= 스케일 전 a)
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                           # 전제: 입력 고정 갈래
    assert ev.objectives.power_w == pytest.approx(VDD * (i + ib), rel=1e-12)    # 같은 θ 탐색 평가: V_dd·(I + I_b) (불변)
    m, r = _r_from_oracle(ev)
    assert m == 1 and 2.5 <= r <= 5.0                                           # 전제: r ≈ 3 (W < w_f -> m = 1)
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == (), out.lost
    r_res = out.points[0].result
    rsnap = r_res.evaluation.snapshot
    v1 = dict(rsnap.column("node", "dc_v"))
    p_res = r_res.objectives.power_resolution_w
    assert p_res is not None and p_res > 0.0
    hand = VDD * (v1["s"] / res + ib)
    got = r_res.objectives.power_w
    assert abs(got - hand) <= p_res
    assert abs(got - VDD * (i + ib)) > p_res                                    # 공허 방지 (θ 전류를 읽으면 red)
    assert abs(dict(rsnap.column("device", "dc_op"))["M1"].current - v1["s"] / res) <= p_res / VDD
    if with_source:
        assert dict(rsnap.column("device", "dc_current"))["I2"] == pytest.approx(R16_IB, rel=1e-12)       # 이상 전류원 항의 출처(선언 입력)


def test_realize_s3_6_target_net_is_unknown_in_resolve_and_its_row_is_judged(tmp_path):
    """S3-6 (식): 목표 넷 out 은 실현 입력 고정 KCL 재풀이의 미지수 -- 손 닫힌 식 mos_load_out_shift(r1, r2). r1·r2 는 스냅샷 실현 W / 탐색 W 에서 읽는다."""
    from gmid_engine.search import STATUS_SEALED
    from sizing.conftest import r4_ln_idu
    case = bins_case(tmp_path, circuit_s36(), node_targets=(("out", S36_VOUT),))

    def theta(i):
        return {("L", "M1"): 1e-6, ("L", "M2"): 1e-6, ("current", "M1"): i,
                ("ln_idu", "M1"): r4_ln_idu("pmos", VGS0, VDD - S36_VOUT, 0.0), ("ln_idu", "M2"): r4_ln_idu("nmos", VGS0, S36_VOUT, 0.0)}
    # [FS-1 A-196 판정 §6 realize_s3_6] 두 소자 모두 칸 키 200(w_f 2 µm)이면 M2 W ≈ W1·IDu_p/IDu_n ≈ 0.48·w_f -> m = 1, r2 ≈ +108 % 라 재풀이 점이 레일 밖이다(손). M2 칸 키를
    # 100(w_f 1 µm)으로 두면 x2 ≈ 0.96, r2 ≈ +4 %, 손 이동 ≈ ln(1.15/1.04)/(2λ) ≈ +0.5 V -> out ≈ 0.9 V (두 포화 전제 안). 입력 키만 바꿨고 전제 단언·기대 식은 그대로다.
    keys36 = {"M1": KEY, "M2": 100}
    wf36 = {"M1": WF, "M2": 100 * GRID}
    w0 = _w_of(_ev(case, theta(S36_I), keys=keys36))
    # 손: W2 ≈ 0.552·W1 (같은 θ 전류 비·IDu 비). x1 = W1/w_f1 = 0.7 -> m1 = 1, r1 = 1/0.7 − 1 = 0.4286; x2 = W2/w_f2 = 0.552·2·0.7 = 0.773 -> m2 = 1, r2 = 0.294.
    # 두 MOS 비 (1 + r1)/(1 + r2) = 1.104 -> 손 이동 ln(1.104)/(2λ) ≈ +0.49 V (out ≈ 0.89 V, 두 포화 안), |r1 − r2| = 0.134 > 0.119 = tol_I/I (아래 전제 단언이 확인).
    # (옛 x1 = 1/1.15 는 |r1 − r2|·I = 4.22e-8 < tol_I 4.58e-8 라 목표 넷 고정 행 잔차 전제가 서지 않았다 -- 판정 대략값을 측정으로 고친 입력.)
    i = S36_I * (WF * 0.7) / w0                                                 # M1: W = 0.7·w_f -> m = 1, r1 = 0.4286 (손 oracle)
    ev = _ev(case, theta(i), keys=keys36)
    snap = ev.evaluation.snapshot
    v0 = dict(snap.column("node", "dc_v"))
    assert ev.status == STATUS_SEALED and v0["out"] == pytest.approx(S36_VOUT, abs=1e-9)
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")                           # 전제: 입력 고정 갈래
    ops = dict(snap.column("device", "dc_op"))
    r = {}
    for dev in ("M1", "M2"):
        mm = hand_oracle((ops[dev].W,), wf36[dev], ())[4][0]
        r[dev] = mm * wf36[dev] / ops[dev].W - 1.0
    tol_i = seal_item(snap, 3).tol
    assert abs(i * (r["M1"] - r["M2"])) > tol_i, (r, tol_i)                      # 전제 (손): 목표 넷을 고정하면 out 행 잔차 > tol_I -- 아니면 멈추고 보고
    hand = mos_load_out_shift(r["M1"], r["M2"], LAM)
    assert VDD - (S36_VOUT + hand) > 0.455 and S36_VOUT + hand > 0.3025, hand    # 전제 (손): 재풀이 점에서도 두 MOS 포화
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == (), out.lost
    rsnap = out.points[0].result.evaluation.snapshot
    v1 = dict(rsnap.column("node", "dc_v"))
    assert v1["in"] == pytest.approx(v0["in"], rel=1e-12) and v1["vb"] == pytest.approx(v0["vb"], abs=1e-9)
    dv = v1["out"] - v0["out"]
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs(dv) >= abs(hand) / 2.0 and abs(dv - hand) <= tol, ("measured_dV_V", dv, "hand_dV_V", hand, "tol_V", tol)
    item = seal_item(rsnap, 3)
    assert item.status == "pass" and dict(item.detail)["worst"] == "out" and dict(item.detail)["n_checked"] == 1
    assert seal_item(rsnap, 7).status == "pass"


# ---------------------------------------------------------------- R-2 (A-191: 삭제 유지 + 구조 성질 test)
# 옛 R-2 의 '입력 차 이동 닫힌 식'은 M1 만 W' 가 달라지는 비대칭 실현을 전제했다. 해법 S(DEC-108)에서 diff_pair 멤버는 한 칸에 들어가 같은 w_f 로 정수화된다 --
# 같은 전류·L·VGS 면 θ W 도 같아 m 이 같으므로 비대칭 실현은 구조상 일어날 수 없다 (검사 대상 소멸, 기준 약화 아님). 대신 그 성질을 단언한다.
def test_realize_diff_pair_cell_members_get_same_m_and_realization_makes_no_input_shift(tmp_path):
    from .wb1_flow import R2_CELLS, R2_ELEMENTS, circuit_r2, r2_theta
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    th = r2_theta(case.dc, scale=2.0 / 3.0)                                      # W_M1 = W_M2 = 4/3 µm (칸 키 200: w_f = 2 µm -> x = 2/3 -> m = 1, r = 0.5)
    wf = hand_wf_of(case.sctx, {m: KEY for m in ("M1", "M2", "M3", "M4")})
    ev = evaluate(case.sctx, sorted_theta(th), R2_CELLS, wf=wf)
    snap = ev.evaluation.snapshot
    ops = dict(snap.column("device", "dc_op"))
    cell = next(c.members for c in wf.cells_ref if "M1" in c.members)
    assert set(cell) == {"M1", "M2"}                                              # 전제: diff_pair 칸
    assert ops["M1"].W == pytest.approx(ops["M2"].W, rel=1e-2)                    # 전제: 같은 전류·L·VGS -> 같은 θ W
    want = hand_oracle(tuple(ops[m].W for m in cell), WF, ())[4]                  # 손 oracle (interface §1)
    assert len(set(want)) == 1 and want[0] == 1 and ops["M1"].W < WF / 1.2        # 전제: 공허 방지 -- 두 멤버 같은 m = 1, r >= 0.2
    _, out = realize(case, ev)
    assert len(out.points) == 1 and out.lost == (), out.lost
    rsnap = out.points[0].result.evaluation.snapshot
    rf = dict(rsnap.column("device", "dc_finger"))
    assert rf["M1"].m == rf["M2"].m == want[0]
    rops = dict(rsnap.column("device", "dc_op"))
    assert rops["M1"].W == rops["M2"].W                                           # 같은 m·w_f -> 같은 W'
    v0, v1 = dict(snap.column("node", "dc_v")), dict(rsnap.column("node", "dc_v"))
    tol = min(x for _, x in rsnap.column("device", "dc_tol_v") if x is not None)
    assert abs((v1["inp"] - v1["inn"]) - (v0["inp"] - v0["inn"])) <= tol           # 실현이 입력 차 이동을 만들지 않는다


# ---------------------------------------------------------------- R-5 (A-191 다시 씀): 탐색 비지배 -> 실현 면적 역전 -> 재필터
# 3 슬라이스 LUT (키 100·200·300). A: L = 2 µm, W = 1 µm (키 100 -> x = 1, m = 1: 실현 불변). B: L = 1 µm, W = 1.8 µm (키 300, w_f = 3 µm -> x = 0.6 -> m = 1, W' = 3 µm):
# 탐색 면적 B < A, 전력 B > A (비지배) -> 실현 면적 B > A, 전력 B > A 그대로 -> A 가 B 를 지배해 재필터.
def test_realize_r5_search_nondominated_point_dominated_by_realized_values(tmp_path):
    from .wb1_flow import R2_CELLS, R2_ELEMENTS, circuit_r2, r2_theta
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS, widths=(1e-6, 2e-6, 3e-6))
    keys_a = {m: 100 for m in ("M1", "M2", "M3", "M4")}
    keys_b = {m: 300 for m in ("M1", "M2", "M3", "M4")}
    ev_a = evaluate(case.sctx, sorted_theta(r2_theta(case.dc, l=2e-6, scale=0.5)), (1, 1, 1, 1), wf=hand_wf_of(case.sctx, keys_a))
    ev_b = evaluate(case.sctx, sorted_theta(r2_theta(case.dc, l=1e-6, scale=0.9)), R2_CELLS, wf=hand_wf_of(case.sctx, keys_b))
    pa, aa = ev_a.objectives.power_w, ev_a.objectives.area_m2
    pb, ab = ev_b.objectives.power_w, ev_b.objectives.area_m2
    assert pa < pb and aa > ab                                                   # 전제: 탐색에서 서로 지배하지 않는다
    for dev in ("M1", "M2", "M3", "M4"):                                         # 전제 (손 oracle): B 모든 소자 m = 1 (W < w_f)
        assert hand_oracle((_w_of(ev_b, dev),), 300 * GRID, ())[4][0] == 1 and _w_of(ev_b, dev) < 300 * GRID / 1.2
    _, only_b = realize(case, ev_b)
    assert len(only_b.points) == 1 and only_b.points[0].result.objectives.area_m2 > aa      # 전제: 실현 면적 B > A (역전)
    _, out = realize(case, ev_a, ev_b, ids=["pa", "pb"])
    assert [p.point_id for p in out.points] == ["pa"]                            # 재필터로 B 가 빠진다
    assert out.lost == ()                                                        # 지배 탈락은 lost 가 아니라 재필터
