"""WB-1 R-1~R-10, R-12 (interface card 20261104-wb1 §6): 실현 평가 `realize_front(sctx, points) -> RealizeOutcome`.

oracle 종류와 출처
- R-1 (a/d): 탐색 W = I·L/exp(ln IDu), 실현 W = m·w_s, 실현 전류밀도 = I'·L/W' -- dc_op 의 current·L·ln_idu·W 사이 항등식(값은 스냅샷 입력 열).
- R-2 (식): r4 닫힌 식 ln IDu = const + B·V - C·V²/2 (B = 20, C = 8, sizing conftest r4 toy 상수), 입력 차 이동 Δ = [-g + √(g² + 2C·ln(1 + r))]/C,
  g = B - C·VGS0, r = W'/W - 1. 곧 I_u(VGS0 - Δ) = I_u(VGS0)/(1 + r) (같은 L·VDS). ln(1 + r)/g 근사는 쓰지 않는다. 단언 = ||V_id(실현) - V_id(탐색)| - Δ| <= tol_V
  와 |V_id 이동| >= Δ/2 (공허 방지). VGS0 는 탐색 스냅샷 dc_op 값(입력).
- R-3~R-8, R-12 (d): interface 표의 사유 어휘·r = 0 이면 입력 값 유지·`finger_slice` 호출 0(관찰 지점 §9) -- 같은 test 에서 탐색 평가의 호출 >= 1 을 먼저 단언.
- R-5 (구성): 탐색에서 비지배인 두 점(전력 낮음·면적 큼 / 전력 높음·면적 작음), 한 점 M1 을 큰 W' 로 tamper -> 실현 면적이 커져 다른 점이 지배.
- R-9: `find_front` 모듈 전역 `sweep_front`·`realize_front` (관찰 지점 §9).
**미측정**: R-2 회로의 실제 통과·실현 평가 c < 0 발생 수는 card 가 미측정으로 적었다. 전제 단언이 깨지면 회로·기대값을 고치지 말고 멈추고 보고한다.
기존 fixture 이행은 이번 범위가 아니라 `wb1_flow.bins_case`(합성 bin LUT, 새 LutAccess)를 쓴다.
"""
import dataclasses
import json
import math
import sys
from pathlib import Path

import pytest

from sizing.conftest import B, C, column_dict

from .conftest import CELLS_C, circuit_c, theta_r4c
from .wb1_flow import R2_CELLS, R2_ELEMENTS, bins_case, circuit_r2, r2_theta, sorted_theta

GRID = 1e-8


def mod(name):
    return sys.modules["gmid_engine.search." + name]


def replace_snap(ev, snap):
    return dataclasses.replace(ev, evaluation=dataclasses.replace(ev.evaluation, snapshot=snap))


def with_fingers(ev, updates=None, remove=()):
    from gmid_engine.sizing import DC_SOLVE_WRITER
    snap = ev.evaluation.snapshot
    col = column_dict(snap, "device", "dc_finger")
    col.update(updates or {})
    for k in remove:
        col.pop(k)
    return replace_snap(ev, snap.write(DC_SOLVE_WRITER, "tampered", {("device", "dc_finger"): col}))


class Count:
    def __init__(self, orig):
        self.orig, self.n = orig, 0

    def __call__(self, *a, **k):
        self.n += 1
        return self.orig(*a, **k)


@pytest.fixture(scope="module")
def r2(tmp_path_factory):
    from gmid_engine.search import evaluate
    case = bins_case(tmp_path_factory.mktemp("wb1_r2"), circuit_r2(), elements=R2_ELEMENTS)
    th = r2_theta(case.dc)
    ev = evaluate(case.sctx, sorted_theta(th), R2_CELLS)
    ops = dict(ev.evaluation.snapshot.column("device", "dc_op"))
    # 전제 (손): 탐색 W_M1 = W_M2 = 2e-6 (V(out) = V(x) 로 고정), 자연 선택 (1, 2e-6)
    assert abs(ops["M1"].W - 2e-6) <= 1e-3 * 2e-6 and abs(ops["M2"].W - 2e-6) <= 1e-2 * 2e-6, (ops["M1"].W, ops["M2"].W)
    fing = dict(ev.evaluation.snapshot.column("device", "dc_finger"))
    assert (fing["M1"].m, round(fing["M1"].w_f_m / GRID)) == (1, 200)
    return case, th, ev


@pytest.fixture
def r2_own(tmp_path):
    """R-3 전용: 경우마다 독립 sctx(평가 캐시 `sctx.cache` 공유 0) -- 모듈 fixture 를 쓰면 첫 경우가 채운 캐시 때문에 둘째 경우의 양성 대조(`finger_slice` 호출 >= 1)가 항상 0 이다."""
    case = bins_case(tmp_path, circuit_r2(), elements=R2_ELEMENTS)
    return case, r2_theta(case.dc)


def realize(case, *evs, ids=None):
    from gmid_engine.search import FrontPoint, realize_front
    ids = ids or ["p%d" % i for i in range(len(evs))]
    pts = tuple(FrontPoint(i, e, ()) for i, e in zip(ids, evs))
    return pts, realize_front(case.sctx, pts)


def lost_of(out):
    return {pid: (reason, detail) for pid, reason, detail in out.lost}


def vid(snap):
    v = dict(snap.column("node", "dc_v"))
    return v["inp"] - v["inn"]


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
    for m, o in r_ops.items():                                     # 실현: W' = m·w_s, 전류밀도 = I'·L/W'
        f = r_fing[m]
        assert o.W == pytest.approx(f.m * f.w_f_m, rel=1e-12), m
        assert o.current * o.L / o.W == pytest.approx(math.exp(o.ln_idu), rel=1e-9), m
        assert f.residual == 0.0
        assert o.w_key == round(f.w_f_m / GRID)


# ---------------------------------------------------------------- R-2
def test_realize_r2_input_difference_shift_matches_closed_form(r2):
    case, th, ev = r2
    snap = ev.evaluation.snapshot
    op1 = dict(snap.column("device", "dc_op"))["M1"]
    r = 3e-6 / op1.W - 1.0                                          # W' = 3e-6 (3, 1e-6)
    assert r == pytest.approx(0.5, abs=2e-3)                        # 전제
    from gmid_engine.sizing import FingerGeom
    tam = with_fingers(ev, {"M1": FingerGeom(3, 1e-6, 0.0)})
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(3e-6, rel=1e-12)
    g = B - C * op1.vgs
    delta = (-g + math.sqrt(g * g + 2.0 * C * math.log(1.0 + r))) / C
    shift = abs(vid(rsnap) - vid(snap))
    tol = min(v for _, v in rsnap.column("device", "dc_tol_v") if v is not None)
    assert shift >= delta / 2.0                                     # 공허 방지
    assert abs(shift - delta) <= tol


# ---------------------------------------------------------------- R-3
@pytest.mark.parametrize("m, w_s_key", [(2, 100), (1, 200)])
def test_realize_r3_zero_residual_keeps_input_finger_without_reselecting(r2_own, monkeypatch, m, w_s_key):
    from gmid_engine.search import evaluate
    from gmid_engine.sizing import FingerGeom
    case, th = r2_own
    bd = sys.modules["gmid_engine.sizing.block_dc"]                  # 관찰 지점 §9 (패키지가 재수출하지 않음)
    c = Count(bd.finger_slice)
    monkeypatch.setattr(bd, "finger_slice", c)
    # `r2_theta` 의 고정점 반복이 이미 이 θ 로 `size_and_seal` 을 불러 실행 색인(donors)에 DC 블록 결과가 있다 -> 입력 버전이 다른 θ(전류 1 ulp)로 평가해야
    # 탐색 경로가 `finger_slice` 를 실제로 부른다(양성 대조). 평가 캐시는 이 경우의 새 sctx 라 경우 사이 공유가 없다.
    th = dict(th)
    th[("current", "M3")] = math.nextafter(th[("current", "M3")], 1.0)
    ev = evaluate(case.sctx, sorted_theta(th), R2_CELLS)
    assert c.n >= 1
    c.n = 0
    op1 = dict(ev.evaluation.snapshot.column("device", "dc_op"))["M1"]
    assert abs(m * w_s_key * GRID - op1.W) <= 1e-3 * op1.W           # 전제: r = 0 에 가까운 입력(W' = 2e-6 = W)
    tam = with_fingers(ev, {"M1": FingerGeom(m, w_s_key * GRID, 0.0)})
    _, out = realize(case, tam)
    assert len(out.points) == 1
    got = dict(out.points[0].result.evaluation.snapshot.column("device", "dc_finger"))["M1"]
    assert (got.m, got.w_f_m, got.residual) == (m, w_s_key * GRID, 0.0)
    assert c.n == 0                                                  # finger_slice 호출 0
    assert not hasattr(mod("realize_front"), "finger_slice")


# ---------------------------------------------------------------- R-4
def test_realize_r4_failed_point_is_lost_and_survivor_stays(r2, monkeypatch):
    from gmid_engine.core import SealViolationError
    from gmid_engine.search import evaluate
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


# ---------------------------------------------------------------- R-5
def test_realize_r5_search_nondominated_point_dominated_by_realized_values(r2):
    from gmid_engine.search import evaluate
    from gmid_engine.sizing import FingerGeom
    case, th, ev_b = r2                                             # B: L = 1e-6, 전류 2·I0
    th_a = r2_theta(case.dc, l=2e-6)                                # A: L = 2e-6, W 같고 전류 절반 -> 전력 낮고 면적 큼
    ev_a = evaluate(case.sctx, sorted_theta(th_a), (1, 1, 1, 1))
    pa, aa = ev_a.objectives.power_w, ev_a.objectives.area_m2
    pb, ab = ev_b.objectives.power_w, ev_b.objectives.area_m2
    assert pa < pb and aa > ab                                      # 전제: 탐색에서 서로 지배하지 않는다
    tam_b = with_fingers(ev_b, {"M1": FingerGeom(12, 1e-6, 0.0)})   # B 의 M1 W' = 12e-6 (r = 5) -> 실현 면적 증가
    _, out = realize(case, ev_a, tam_b, ids=["pa", "pb"])
    assert [p.point_id for p in out.points] == ["pa"]               # 재필터로 B 가 빠진다
    assert out.lost == ()                                           # 지배 탈락은 lost 가 아니라 재필터


# ---------------------------------------------------------------- R-6
def test_realize_r6_unresolved_servo_pivot_keeps_input_value(tmp_path):
    from gmid_engine.search import evaluate
    from gmid_engine.sizing import FingerGeom
    case = bins_case(tmp_path, circuit_c())
    ev = evaluate(case.sctx, sorted_theta(theta_r4c()), CELLS_C)
    snap = ev.evaluation.snapshot
    cfg = next(iter(dict(snap.column("graph", "icm_config")).values()))
    assert cfg.config in (None, "as_is_single_input")               # 전제: 피벗 판정 불능 갈래
    w1 = dict(snap.column("device", "dc_op"))["M1"].W
    m = max(1, round(w1 / 1e-6))
    tam = with_fingers(ev, {"M1": FingerGeom(m, 1e-6, 0.0)})
    assert m * 1e-6 != w1                                           # 전제: W' != W (공허 방지)
    _, out = realize(case, tam)
    assert len(out.points) == 1 and out.lost == ()
    rsnap = out.points[0].result.evaluation.snapshot
    assert dict(rsnap.column("node", "dc_v"))["in"] == dict(snap.column("node", "dc_v"))["in"]   # 입력 = 봉인점 값
    assert dict(rsnap.column("device", "dc_op"))["M1"].W == pytest.approx(m * 1e-6, rel=1e-12)


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


# ---------------------------------------------------------------- R-8
def test_realize_r8_missing_search_finger_is_a_reason_not_keyerror(r2):
    case, th, ev = r2
    _, out = realize(case, with_fingers(ev, remove=("M1",)))
    assert out.points == () and lost_of(out)["p0"][0] == "realized_finger_missing"


# ---------------------------------------------------------------- R-12
def test_realize_r12_finger_not_a_slice_is_slice_missing(r2):
    from gmid_engine.sizing import FingerGeom
    case, th, ev = r2
    _, out = realize(case, with_fingers(ev, {"M1": FingerGeom(1, 3e-6, 0.0)}))        # 슬라이스 {1, 2} µm 에 3 µm 없음
    assert out.points == () and lost_of(out)["p0"][0] == "slice_missing"


# ---------------------------------------------------------------- R-9 / R-10
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


def test_realize_r10_json_finger_residual_and_selection_residual(tmp_path, short_root):
    """JSON `front[i].finger_residual` = {MOS: 탐색 residual} (reader 잠금) + 선택 경로 손 값: 슬라이스 {5 µm}, W = 12e-6 -> (2, 5e-6), r = -1/6."""
    from types import SimpleNamespace
    from gmid_engine.lut import LBin, LBinMap, finger_slice
    from gmid_engine.search import find_front
    g = 1e-8
    lut = SimpleNamespace(spec=SimpleNamespace(manufacturing_grid_m=g, min_finger_w_m=(("nmos", 1e-6),)),
                          slice_map={("nmos", 500): SimpleNamespace(l_bins=LBinMap(("m",), (1e-6, 5e-6), (LBin("b", 5e-7, 3e-6),), ()))},
                          cap_map={"nmos": SimpleNamespace(w_key=500)}, bin_rule="lower")
    fs = finger_slice(lut, "nmos", 1e-6, lambda key: 12e-6)
    assert (fs.m, fs.w_f_m, fs.w_key) == (2, 5e-6, 500)
    assert 2 * 500 * g / 12e-6 - 1.0 == pytest.approx(-1.0 / 6.0, rel=1e-12)       # 손: r = m·w_s/W - 1
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep, searched = ff.sweep_front, []

    def sweep(*a, **k):
        out = real_sweep(*a, **k)
        searched.extend(out["front"])                                # 탐색 점(탐색 스냅샷의 dc_finger 가 기대값의 출처)
        return out
    ff.sweep_front = sweep
    try:
        fr = find_front(case.sctx, [theta_r4c()])
    finally:
        ff.sweep_front = real_sweep
    assert len(searched) >= 1 and len(fr.front) >= 1
    by_id = {p.point_id: p for p in searched}
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(run["front"]) == len(fr.front)
    for entry, p in zip(run["front"], fr.front):
        want = {m: f.residual for m, f in dict(by_id[p.point_id].result.evaluation.snapshot.column("device", "dc_finger")).items()}
        assert dict(entry["finger_residual"]) == want                 # 탐색 residual (실현 후 0.0 이 아님)
        assert "slice_rounds" in entry
    assert {"lost", "n_lost"} <= set(dict(run["realize"]))


def test_realize_r10_json_finger_residual_is_the_tampered_search_value(tmp_path, monkeypatch, short_root):
    """R-10 후반 (interface §6, reader 잠금 S-4): 탐색 점의 `dc_finger` 한 소자를 `FingerGeom(m, w_f, -0.5)` 로 바꾸면(같은 m·w_f 라 실현 평가는 그대로 통과) JSON
    `front[i].finger_residual[소자]` = -0.5 이다. 단언 = 바꾼 값 그대로(탐색 `FingerGeom.residual` 을 읽는다 -- 실현 평가의 0.0 이 아니다).
    oracle (d): interface 표 '탐색 FingerGeom.residual'. 선택 경로 손 값(슬라이스 {5 µm}, W = 12e-6 -> (2, 5e-6), r = -1/6)은 위 test 가 본다."""
    from gmid_engine.sizing import FingerGeom
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), archive_root=short_root)
    ff = mod("find_front")
    real_sweep = ff.sweep_front
    seen = []

    def sweep(*a, **k):
        out = dict(real_sweep(*a, **k))
        pts = []
        for p in out["front"]:
            fing = dict(p.result.evaluation.snapshot.column("device", "dc_finger"))
            m1 = fing["M1"]
            tam = with_fingers(p.result, {"M1": FingerGeom(m1.m, m1.w_f_m, -0.5)})        # 실현 평가가 쓰는 m·w_f 는 그대로, residual 만 바꾼다
            pts.append(dataclasses.replace(p, result=tam))
            seen.append(p.point_id)
        out["front"] = tuple(pts)
        return out
    monkeypatch.setattr(ff, "sweep_front", sweep)
    fr = find_front(case.sctx, [theta_r4c()])
    assert seen and len(fr.front) >= 1                                    # 양성 대조: 탐색 점을 실제로 바꿨고 실현 뒤 front 가 남았다
    (run,) = [json.loads(x) for x in (Path(short_root) / case.sctx.context_fp / "runs.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    assert len(run["front"]) == len(fr.front)
    for entry in run["front"]:
        assert dict(entry["finger_residual"])["M1"] == -0.5

