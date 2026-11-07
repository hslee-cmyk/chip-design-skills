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

from .conftest import circuit_c, evaluate, theta_r4c
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
def test_realize_o3_lost_entries_carry_small_m_key(tmp_path, monkeypatch, short_root):
    """[FS-1 O-3] 실현에서 잃는 점(R-4 꼴: realize_front 가 부르는 평가를 SealViolationError 로 바꿈)의 JSON `realize.lost` 항목에 `small_m` 키 --
    값 = 그 점 (부분) 실현 스냅샷 dc_finger 에서 m ≤ 2 인 MOS 이름 정렬 목록, dc_finger 가 없으면 None."""
    from gmid_engine.core import SealViolationError
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    rf = mod("realize_front")
    real = rf.evaluate

    def wrapped(sctx, theta, cells, *a, **k):
        if k.get("realized") is not None:
            raise SealViolationError(devices=("M1",), margin=0.5, detail={"item": 7, "reason": "fs1_test_forced_failure"})
        return real(sctx, theta, cells, *a, **k)
    monkeypatch.setattr(rf, "evaluate", wrapped)
    fr = find_front(case.sctx, [theta_r4c()])
    lost = dict(_runs_line(short_root, case.sctx)["realize"])["lost"]
    assert len(lost) >= 1                                                   # 양성 대조: 잃은 점이 있다
    for item in lost:
        assert "small_m" in dict(item)
        sm = dict(item)["small_m"]
        assert sm is None or (list(sm) == sorted(sm) and all(isinstance(n, str) for n in sm))
