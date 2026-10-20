"""CONTRACT 3.15 [r2·r4] `sweep_front(sctx, starts) -> dict`.

독립 계산: ε 격자(conftest `ref_eps_values`: 열린 구간 안 hi − k·간격), 예산 게이트(N_ε = ⌊(E_B − E_fixed)/e_ε⌋, 총수 > N_ε 면
간격 ×2), 전력 간격 = max(b_P(E_P), b_P(E_A)), 비지배(전력 폭 max(b_P(p), b_P(q)), 면적 폭 b_A).
최종 front = 봉인·미측정 없음, unmeasured_front = 봉인·미측정 있음, pending_front = 봉인 7 대기.
"""
import math
import re

import pytest

from gmid_engine.search import (
    AXIS_AREA,
    AXIS_POWER,
    STATUS_PENDING_SEAL7,
    STATUS_SEALED,
    FrontPoint,
    start_points,
    sweep_front,
)

from .conftest import GRID, PENDING, W_MIN, all_tied, build_case, circuit_c, dominates, ref_eps_values, theta_r4c

SS = (("gain_ss_db", ">=", 10.0, None),)
ID_RE = re.compile(r"^(EP:s\d+|EA:s\d+|eps:(power_dc_w|area_search_m2):\d+|L:.+:\d+)$")


def _sweep(tmp, lut, eval_budget=60, **kw):
    case = build_case(tmp, circuit_c(**kw.pop("topo_kw", {})), lut, eval_budget=eval_budget, **kw)
    starts, _ = start_points(case.sctx, [theta_r4c()])
    return case, sweep_front(case.sctx, starts)


@pytest.fixture(scope="module")
def sealed_sweep(tmp_path_factory, lut_sealed):
    """(None, sweep 결과) -- [XRUN-F1 card B 규칙 M M-d] 모듈 범위라 case(커널·탐색 컨텍스트 = 실행의 두 객체)는 두지 않고 sweep 결과만 둔다
    (이 모듈 test 는 case 를 읽지 않는다)."""
    _case, out = _sweep(tmp_path_factory.mktemp("sw"), lut_sealed, constraints=SS)
    return None, out


def test_keys_and_ids(sealed_sweep):
    _, out = sealed_sweep
    for k in ("solves", "failed_eps", "resolution", "front", "pending_front", "unmeasured_front",
              "front_removed", "front_folded", "pending_front_removed", "pending_front_folded"):
        assert k in out, k
    ids = [i for i, _ in out["solves"]]
    assert "EP:s1" in ids and "EA:s1" in ids
    assert all(ID_RE.match(i) for i in ids), ids
    for e in out["failed_eps"]:
        e = dict(e)
        assert {"eps", "minimize", "stop", "aborts", "accepted"} <= set(e)


def test_resolution_record(sealed_sweep):
    case, out = sealed_sweep
    res = dict(out["resolution"])
    assert res["b_A_m2"] == pytest.approx(GRID * W_MIN, rel=1e-12)
    assert res["estimated"] is True and res["E_refilter"] == 0 and res["refilter"] == "mod8_not_implemented"
    assert res["E_B"] == 60
    assert res["N_eps"] == math.floor((res["E_B"] - res["E_fixed"]) / res["e_eps"])
    sol = dict(out["solves"])
    bp = [sol[k].best.objectives.power_resolution_w for k in ("EP:s1", "EA:s1")]
    assert res["b_P_grid_w"] == pytest.approx(max(bp), rel=1e-15)


def _grid(out):
    res = dict(out["resolution"])
    sol = dict(out["solves"])
    ep, ea = sol["EP:s1"].best.objectives, sol["EA:s1"].best.objectives
    return res, (ep.power_w, ea.power_w), (ea.area_m2, ep.area_m2)


def test_eps_grid_matches_budget_gate(sealed_sweep):
    _, out = sealed_sweep
    res, (p_lo, p_hi), (a_lo, a_hi) = _grid(out)
    cf = res["coarse_factor"]
    assert cf >= 1 and (cf & (cf - 1)) == 0                       # 2 의 거듭제곱
    n_cap = max(res["N_eps"], 0)

    def total(f):
        return (len(ref_eps_values(p_lo, p_hi, res["b_P_grid_w"] * f))
                + len(ref_eps_values(a_lo, a_hi, res["b_A_m2"] * f)))
    assert total(cf) <= n_cap
    if cf > 1:
        assert total(cf // 2) > n_cap
    exp = {AXIS_POWER: sorted(ref_eps_values(p_lo, p_hi, res["b_P_grid_w"] * cf)),
           AXIS_AREA: sorted(ref_eps_values(a_lo, a_hi, res["b_A_m2"] * cf))}
    got = {tuple(r.eps) for i, r in out["solves"] if i.startswith("eps:")}
    got |= {tuple(dict(e)["eps"]) for e in out["failed_eps"]}
    for ax in (AXIS_POWER, AXIS_AREA):
        g = sorted(v for a, v in got if a == ax)
        assert len(g) == len(exp[ax]), (ax, g, exp[ax])
        assert g == pytest.approx(exp[ax], rel=1e-12)
    for i, r in out["solves"]:
        if i.startswith("eps:"):
            ax = tuple(r.eps)[0]
            assert r.minimize == (AXIS_AREA if ax == AXIS_POWER else AXIS_POWER)
            assert i.startswith("eps:%s:" % ax)


def _eligible(out):
    """끝점·ε·L-b 풀이의 best 중 봉인·미측정 없음."""
    return [(i, r.best) for i, r in out["solves"]
            if r.best is not None and r.best.status == STATUS_SEALED and not tuple(r.best.unmeasured)]


def test_front_is_nondominated_and_covers_candidates(sealed_sweep):
    _, out = sealed_sweep
    b_a = dict(out["resolution"])["b_A_m2"]
    front = out["front"]
    assert front and all(isinstance(p, FrontPoint) for p in front)
    for p in front:
        assert p.result.status == STATUS_SEALED and tuple(p.result.unmeasured) == ()

    def vec(r):
        return (r.objectives.power_w, r.objectives.area_m2)

    def wp(r, q):
        return max(r.objectives.power_resolution_w, q.objectives.power_resolution_w)
    for p in front:
        for q in front:
            if p is q:
                continue
            assert not dominates(vec(q.result), vec(p.result), wp(p.result, q.result), b_a)
            assert not all_tied(vec(q.result), vec(p.result), wp(p.result, q.result), b_a)
    for i, r in _eligible(out):
        if any(p.result is r or p.result.key == r.key for p in front):
            continue
        assert any(dominates(vec(p.result), vec(r), wp(p.result, r), b_a)
                   or all_tied(vec(p.result), vec(r), wp(p.result, r), b_a) for p in front), i


def test_pending_never_in_final_front(tmp_path, lut_pending):
    """I-6: 봉인 7 대기 점은 front 0, pending_front 로만."""
    _, out = _sweep(tmp_path, lut_pending, constraints=SS)
    assert tuple(out["front"]) == ()
    assert len(out["pending_front"]) >= 1
    assert all(p.result.status == STATUS_PENDING_SEAL7 for p in out["pending_front"])


def test_unmeasured_never_in_final_front(tmp_path, lut_sealed):
    """r4: ss 제약 미측정(수동소자 값 없음) 점은 최종 front 0, unmeasured_front 로만."""
    _, out = _sweep(tmp_path, lut_sealed, constraints=SS, elements=(("CL", "capacitor", PENDING),),
                    topo_kw={"with_cap": True})
    assert tuple(out["front"]) == ()
    assert len(out["unmeasured_front"]) >= 1
    for p in out["unmeasured_front"]:
        assert p.result.status == STATUS_SEALED and len(tuple(p.result.unmeasured)) >= 1
