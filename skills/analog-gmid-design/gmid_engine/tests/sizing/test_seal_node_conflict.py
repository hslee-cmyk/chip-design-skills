"""봉인 1 `dc_seal_node_conflict(snapshot)` -- CONTRACT 6절: 노드마다 spread = max − min of {노드 값} ∪ path_values;
tol = 닿는 PATH_MOS 소자 tol_v 최댓값(정의된 것), 없으면 None; MOS 관계가 없는 노드는 n·eps·max|V|(n = 값 수).
judge 규칙(conftest `judge_expect`)으로 SealItem 을 독립 계산해 비교한다. 위반은 path_values 를 바꿔 넣어 만든다.
"""
import math

import numpy as np
import pytest

from gmid_engine.sizing import PathValue, dc_seal_node_conflict

from .conftest import (EPS, assert_item, judge_expect, node_voltages, rel_close, seal_item, tamper, theta_a,
                       theta_c, with_tol)


def rows_of(snap):
    V = node_voltages(snap)
    pv = dict(snap.column("node", "dc_path_values"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    rows = []
    for n in sorted(V):
        vals = [V[n]] + [p.value for p in pv.get(n, ())]
        mos = sorted({p.relation[1] for p in pv.get(n, ()) if p.relation[0] == "vgs"})
        if mos:
            defined = [tolv[m] for m in mos if tolv[m] is not None]
            tol = max(defined) if defined else None
        else:
            tol = len(vals) * EPS * max(abs(v) for v in vals)
        rows.append((n, max(vals) - min(vals), tol, tuple(mos), (n,)))
    return rows


def run(snap):
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C4] 블록 단독 호출 = 새 실행 하나
    return seal_item(dc_seal_node_conflict(snap, donors=donors, counters=counters), 1)


@pytest.mark.parametrize("which", ["C", "A"])
def test_pass(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    exp = judge_expect(rows_of(snap))
    assert exp["status"] == "pass"
    assert_item(run(snap), exp, 1, atol=1e-15)


def test_fail_on_mos_node(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    v_in = node_voltages(snap)["in"]
    bad = tamper(snap, "dc_solve", "node", "dc_path_values", {"in": (PathValue(("vgs", "M1"), v_in + 0.1),)})
    exp = judge_expect(rows_of(bad))
    assert exp["status"] == "fail" and exp["nodes"] == ("in",)
    item = run(bad)
    assert_item(item, exp, 1, check_devices=False)
    # 손계산: spread 0.1, tol = tol_v(M1)
    assert rel_close(item.magnitude, 0.1, 1e-9)
    assert item.tol == dict(snap.column("device", "dc_tol_v"))["M1"]
    assert rel_close(item.margin, 0.1 / item.tol, 1e-9)


def test_eps_tolerance_on_node_without_mos_relation(ctx_c):
    """out 은 PATH_Y 만 있다 -> tol = 2·eps·max|V|. 1 ulp 대의 차도 그 tol 을 넘으면 fail."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    v = node_voltages(snap)["out"]                 # 0.9: ulp = eps/2 -> tol 2·eps·0.9 = 3.6 ulp

    def up(x, k):
        for _ in range(k):
            x = float(np.nextafter(x, 2.0))
        return x
    v5 = up(v, 5)                                  # 5 ulp > 3.6 ulp -> fail
    bad = tamper(snap, "dc_solve", "node", "dc_path_values", {"out": (PathValue(("y", "out"), v5),)})
    exp = judge_expect(rows_of(bad))
    assert exp["status"] == "fail" and exp["nodes"] == ("out",)
    item = run(bad)
    assert_item(item, exp, 1, check_devices=False)
    assert rel_close(item.tol, 2 * EPS * v5, 1e-12)
    v3 = up(v, 3)                                  # 3 ulp < 3.6 ulp -> pass
    ok = tamper(snap, "dc_solve", "node", "dc_path_values", {"out": (PathValue(("y", "out"), v3),)})
    assert run(ok).status == "pass"


def test_undefined_when_mos_tol_none(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    exp = judge_expect(rows_of(s2))
    assert exp["status"] == "undefined"
    assert_item(run(s2), exp, 1, check_devices=False)


def test_fail_wins_over_undefined(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    v_pb = node_voltages(snap)["pb"]
    s3 = tamper(s2, "dc_solve", "node", "dc_path_values", {"pb": (PathValue(("vgs", "M2"), v_pb - 0.2),)})
    exp = judge_expect(rows_of(s3))
    assert exp["status"] == "fail" and exp["nodes"] == ("pb",)
    assert_item(run(s3), exp, 1, check_devices=False)
