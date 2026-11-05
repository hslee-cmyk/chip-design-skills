"""WB-1 W-1 (interface card 20261104-wb1 §8 `perf.solver_stops`): `dict(fr.perf)["solver_stops"]` =
{풀이 종류: {"converged": n, "abnormal": {사유: n}, "budget": {"eval_budget": n, "wall_budget": n}}}, 종류 ∈ {eps, layer0}.

oracle (식): 이 card 의 집계 규칙. 기대값은 test 가 stub 에 심은 stop 열을 독립 Counter 로 센 것이다(피검 집계가 아님).
관찰 지점 §9: `find_front` 모듈 전역 `sweep_front`·`layer0_start` (실행 결과 stop 값을 스크립트로 바꾸는 stub; 나머지는 원 함수).
**애매한 계약(보고)**: stub 이 바꾸는 값은 `sweep_front` 결과 dict 의 `solves` 항목 `(id, 결과)` 의 `stop` 이다(card 는 stub 모양을 적지 않았다).
`failed_eps` 항목이 집계에 들어가는지 card 에 없어 stub 이 비운다. L-b 풀이(`L:` id)가 eps 종류에 드는지도 card 에 없어 모든 `solves` 항목을 eps 로 센다.
"""
import collections
import dataclasses
import sys

import pytest

from .conftest import circuit_c, theta_r4c
from .wb1_flow import bins_case

SCRIPT = ("converged", "slsqp_4", "restart_cap", "all_columns_frozen", "eval_budget", "wall_budget")
ABNORMAL = ("slsqp_4", "restart_cap", "all_columns_frozen")


def norm(x):
    """매핑 또는 (이름, 값) 쌍의 tuple 을 dict 로 재귀 정규화."""
    if isinstance(x, dict):
        return {k: norm(v) for k, v in x.items()}
    if isinstance(x, (tuple, list)) and x and all(isinstance(p, (tuple, list)) and len(p) == 2 and isinstance(p[0], str) for p in x):
        return {k: norm(v) for k, v in x}
    return x


def nonzero(d):
    return {k: v for k, v in d.items() if v}


def test_solver_stops_counts_follow_scripted_stops(tmp_path):
    from gmid_engine.search import find_front
    case = bins_case(tmp_path, circuit_c(), eval_budget=40)
    ff = sys.modules["gmid_engine.search.find_front"]
    real_sweep, real_l0 = ff.sweep_front, ff.layer0_start
    planted = []
    seen = {"sweep": 0, "l0": 0}

    def sweep(*a, **k):
        out = dict(real_sweep(*a, **k))
        seen["sweep"] += 1
        sols = list(out["solves"])
        new = []
        for i, (pid, r) in enumerate(sols):
            stop = SCRIPT[i % len(SCRIPT)]
            planted.append(stop)
            new.append((pid, dataclasses.replace(r, stop=stop)))
        out["solves"] = type(out["solves"])(new)
        out["failed_eps"] = type(out["failed_eps"])()
        return out

    def l0(*a, **k):
        seen["l0"] += 1
        return dataclasses.replace(real_l0(*a, **k), stop="converged")
    ff.sweep_front, ff.layer0_start = sweep, l0
    try:
        fr = find_front(case.sctx, [theta_r4c()])
    finally:
        ff.sweep_front, ff.layer0_start = real_sweep, real_l0
    assert seen["sweep"] >= 1 and seen["l0"] >= 1 and len(planted) >= 1       # 호출 >= 1 (공허 통과 방지)
    st = norm(dict(fr.perf)["solver_stops"])
    assert set(st) == {"eps", "layer0"}
    cnt = collections.Counter(planted)
    assert st["eps"]["converged"] == cnt["converged"]
    assert nonzero(st["eps"]["abnormal"]) == {r: cnt[r] for r in ABNORMAL if cnt[r]}
    assert {k: st["eps"]["budget"].get(k, 0) for k in ("eval_budget", "wall_budget")} == \
        {"eval_budget": cnt["eval_budget"], "wall_budget": cnt["wall_budget"]}
    assert st["layer0"]["converged"] == 1
    assert nonzero(st["layer0"]["abnormal"]) == {} and nonzero(st["layer0"]["budget"]) == {}
