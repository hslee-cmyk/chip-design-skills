"""봉인 8 `dc_seal_kvl_branch(snapshot)` -- CONTRACT 6절: S1 rel_kvl_branch 엣지마다 Σ_멤버 |ln idu_forward − ln_idu|/gm_id ≤
Σ 멤버 tol_v (하나라도 None 이면 None).

손 회로에는 G_vgs v2 사이클이 없어 rel_kvl_branch 가 비어 있다(행 0 -> pass, magnitude None). 공식 확인은 S1 필드
graph.rel_kvl_branch 를 권한표 writer(s1_gvgs)로 바꿔 넣은 스냅샷에서 한다.
"""
import dataclasses
import math

from gmid_engine.graph import GRAPH_KEY, Evidence, RelEdge
from gmid_engine.sizing import dc_seal_kvl_branch

from .conftest import assert_item, judge_expect, rel_close, seal_item, tamper, theta_c, with_tol


def set_branches(snap, members_list):
    edges = tuple(RelEdge("kvl_branch", "dc", tuple(m), "derived", Evidence("v2_rail")) for m in members_list)
    return snap.write("s1_gvgs", "tampered", {("graph", "rel_kvl_branch"): {GRAPH_KEY: edges}})


def rows_of(snap):
    ops = dict(snap.column("device", "dc_op"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    ln = dict(snap.column("device", "dc_ln_idu"))
    rows = []
    for i, e in enumerate(snap.value("graph", GRAPH_KEY, "rel_kvl_branch")):
        mag = sum(abs(math.log(ops[m].idu_forward) - ln[m]) / ops[m].gm_id for m in e.members)
        tols = [tolv[m] for m in e.members]
        tol = None if any(t is None for t in tols) else sum(tols)
        # 행 대상 이름(detail worst)은 계약에 적혀 있지 않다 -- 실행에서 본 '멤버를 + 로 이은 것'을 쓴다(보고: 모호)
        rows.append(("+".join(e.members), mag, tol, tuple(sorted(e.members)), ()))
    return rows


def run(snap):
    return seal_item(dc_seal_kvl_branch(snap), 8)


def test_no_branch_pass_none(ev_c):
    item = seal_item(ev_c.snapshot, 8)
    assert item.status == "pass" and item.magnitude is None and item.margin is None
    assert dict(item.detail)["n_checked"] == 0


def test_branch_sum_pass(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = set_branches(snap, [("M1", "M2")])
    exp = judge_expect(rows_of(s2))
    assert exp["status"] == "pass"
    item = run(s2)
    assert item.status == "pass" and dict(item.detail)["n_checked"] == 1
    tolv = dict(snap.column("device", "dc_tol_v"))
    assert rel_close(item.tol, tolv["M1"] + tolv["M2"], 1e-12)


def test_branch_sum_fail_hand(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    ops = dict(snap.column("device", "dc_op"))
    s2 = tamper(snap, "dc_widths", "device", "dc_op",
                {"M1": dataclasses.replace(ops["M1"], idu_forward=ops["M1"].idu_forward * 10.0)})
    s2 = set_branches(s2, [("M1", "M2")])
    exp = judge_expect(rows_of(s2))
    assert exp["status"] == "fail"
    item = run(s2)
    assert_item(item, exp, 8, check_nodes=False)
    # 손계산: ln10 / gm_id(M1) + 0 (M2 는 정확)
    assert rel_close(item.magnitude, math.log(10.0) / ops["M1"].gm_id, 1e-6)


def test_branch_each_member_within_tol_passes(ctx_c):
    """멤버마다 0.9·tol_v 의 차 -> 합 0.9·Σtol_v ≤ Σtol_v -> pass."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    ops = dict(snap.column("device", "dc_op"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    upd = {m: dataclasses.replace(ops[m], idu_forward=ops[m].idu_forward * math.exp(0.9 * tolv[m] * ops[m].gm_id))
           for m in ("M1", "M2")}
    s2 = set_branches(tamper(snap, "dc_widths", "device", "dc_op", upd), [("M1", "M2")])
    assert run(s2).status == "pass"


def test_undefined_when_member_tol_none(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = set_branches(tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M2": None}), [("M1", "M2")])
    exp = judge_expect(rows_of(s2))
    assert exp["status"] == "undefined"
    assert run(s2).status == "undefined"
    assert set(run(s2).devices) == {"M1", "M2"}
