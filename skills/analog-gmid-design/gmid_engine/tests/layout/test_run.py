"""CONTRACT 4.12~4.14 `run_layout(layout_input, memo, design_point, previous=None) -> LayoutResult` -- 입력·출력 계약, 불변식 4.13, 재검증 요청,
캐시(필드 = 캐시, LUT 지문 + 보존량 키), 결정론, M3a 회귀(toy).

[U17 1-e] design 40 v1.6 §2.4.7 `LayoutResult` 행·§2.4.8 '레이아웃 결과' 행: 레이아웃 결과는 그 **설계점 스냅샷**의 S2 `layout` 필드이고
`LayoutResult` 는 (스냅샷, 이번 호출의 계산 블록 목록)뿐이다. 옛 결과 칸(devices·groups·rows·floorplan·diffusion·w_requests·...)이 확인하던
판정 내용은 그대로 두고 읽는 곳만 바꿨다 -- 그룹·행·floorplan·확산은 스냅샷 `ly_*` 필드, 필드 파생 항목(review_needed·DeviceLayout·coverage·
W_requests·불변식·재검증 요청)은 `layout_outputs(snapshot)`(`test_outputs.py` 가 파생 규칙 자체를 본다).
설계점 스냅샷은 conftest `design_point`(레이아웃 writer 를 모르는 S2 대역)로 만든다.

실 LUT M3a 회귀는 `test_run_realdata.py` 가 아니라 이 파일 끝(마커 `layout_realdata`)에 둔다(규칙 H 1:1).
"""
from __future__ import annotations

import dataclasses
import math
from collections import Counter

import pytest

from gmid_engine.core import GraphSnapshot
from gmid_engine.layout import LayoutResult, layout_outputs, run_layout
from gmid_engine.layout import _ly_fields as lf
from gmid_engine.layout import run as run_mod
from gmid_engine.layout.contract_output import (REVALIDATION_CONSUMER, REVALIDATION_PENDING, REVALIDATION_PENDING_REASON,
                                                REVALIDATION_SEALS, DeviceLayout, LayoutOutputs, MatchingDisposition,
                                                RealizedDevice, ReviewItem, Revalidation, WRequest)
from gmid_engine.layout.finger_candidates import finger_candidates
from gmid_engine.layout.finger_geometry import finger_geometry
from gmid_engine.layout.pattern_select import pattern_select
from gmid_engine.layout.rows import compose_rows

from .conftest import (DP_GRAPH_KEY, DP_METRIC_VERSION, DP_OP_VERSION, build_toy_lut, design_point, design_point_of, dev, dp_writers,
                       layout_fields, make_input, mg, new_memo, rg, strip_volatile, toy_pdk)
from .conftest import block_row, fresh_run  # [XRUN-F1 card B C0·C1]

ALL_WRITERS = ("ly_slice_density", "ly_finger_candidates", "ly_pattern_select", "ly_finger_geometry", "ly_rows")


def composite(pdk, extra=(), extra_rgs=(), rejected=(), adj=True, diode_C=False):
    """4.15 손계산 오라클 묶음: 차동쌍 g1(A·B ID 2e-6), branch_symmetric g2(E·F), bias_distribution g3(C·D), C 는 0.75e-6."""
    ds = [dev("A", "h", "da", 2e-6, adj=adj), dev("B", "h", "db", 2e-6, adj=adj),
          dev("E", "p", "q", 2e-6, gate="gc"), dev("F", "r", "t", 2e-6, gate="gc"),
          dev("C", "x", "y", 0.75e-6, gate="gb", diode=diode_C), dev("D", "y", "z", 1e-6, gate="gb")] + list(extra)
    groups = [mg("g2", ("E", "F"), "branch_symmetric", None), mg("g1", ("A", "B"), "diff_pair", "h"),
              mg("g3", ("C", "D"), "bias_distribution", "y")]
    rgs = [rg("r1", ("A", "B")), rg("r2", ("E", "F")), rg("r", ("C", "D") + tuple(d.name for d in extra))] + list(extra_rgs)
    return make_input(ds, groups, rgs, pdk, rejected)


def run(inp, memo, previous=None, rp=None):
    """`run_layout` 을 그 입력 소자들의 설계점 대역 위에서 부른다(재시도 `previous` 는 같은 설계점 lineage).
    [XRUN-F1 card B C6] rp = 실행 두 객체 키워드(dict), 없으면 새 실행 하나."""
    return run_layout(inp, memo, design_point_of(inp), previous, **(rp if rp is not None else fresh_run()))


def G(res, field):
    return res.snapshot.value(lf.GRAPH, lf.GRAPH_KEY, field)


def groups(res):
    return G(res, lf.F_GROUPS)


def rows(res):
    return G(res, lf.F_ROWS).rows


def floorplan(res):
    return G(res, lf.F_FLOORPLAN)


def diffusion(res):
    return G(res, lf.F_DIFFUSION)


def outs(res):
    return layout_outputs(res.snapshot)


@pytest.fixture
def result(toy_lut):
    return run(composite(toy_pdk(toy_lut)), new_memo(toy_lut))


# --- 입력 계약 --------------------------------------------------------------------------------------------------------

def test_lut_fingerprint_mismatch_rejected(toy_lut, tmp_path):
    other = build_toy_lut(tmp_path / "other", id_scale=2.0)
    assert other.fp != toy_lut.fp
    with pytest.raises(ValueError):
        run(composite(toy_pdk(other)), new_memo(toy_lut))


def test_design_point_must_be_snapshot(toy_lut):
    # 4.12 1: `design_point` 가 GraphSnapshot 이 아니면 TypeError (§2.4.7: 레이아웃 필드는 설계점 스냅샷 위에만)
    inp = composite(toy_pdk(toy_lut))
    with pytest.raises(TypeError):
        run_layout(inp, new_memo(toy_lut), None, **fresh_run())
    with pytest.raises(TypeError):
        run_layout(inp, new_memo(toy_lut), {"not": "a snapshot"}, **fresh_run())


@pytest.mark.parametrize("missing", ["donors", "counters", "both"])
def test_run_pair_keywords_required(toy_lut, missing):
    """B-T16(XRUN-F1 card B C6): run_layout 의 donors·counters 는 필수 키워드(기본값 없음) -- 빠지면 TypeError."""
    inp = composite(toy_pdk(toy_lut))
    kw = {k: v for k, v in fresh_run().items() if missing != "both" and k != missing}
    with pytest.raises(TypeError):
        run_layout(inp, new_memo(toy_lut), design_point_of(inp), **kw)


def test_previous_from_other_design_point_rejected(toy_lut):
    # 4.12 2: `previous` 는 같은 설계점 lineage 만 -- 설계점 writer 의 block_version 이 하나라도 다르면 ValueError
    rp = fresh_run()
    memo = new_memo(toy_lut)
    inp = composite(toy_pdk(toy_lut))
    names = tuple(d.name for d in inp.devices)
    r1 = run_layout(inp, memo, design_point(names), **rp)
    other = GraphSnapshot.empty(dp_writers())
    other = other.write("dp_kernel", "dp-op-v2", {("device", "dp_op"): {n: ("op2", n) for n in names}})
    other = other.write("dp_metrics", DP_METRIC_VERSION, {("graph", "dp_metric"): {DP_GRAPH_KEY: 1.0}})
    with pytest.raises(ValueError):
        run_layout(inp, memo, other, previous=r1, **rp)
    # 같은 설계점(같은 block_version)의 다른 스냅샷 객체는 같은 lineage 로 받는다
    r2 = run_layout(inp, memo, design_point(names), previous=r1, **rp)
    assert r2.computed_blocks == ()


# --- 출력 계약 --------------------------------------------------------------------------------------------------------

def test_output_shape(result):
    assert isinstance(result, LayoutResult)
    assert [f.name for f in dataclasses.fields(result)] == ["snapshot", "computed_blocks"]        # §2.4.7: 두 칸뿐
    assert isinstance(result.snapshot, GraphSnapshot)
    assert result.computed_blocks == ALL_WRITERS
    o = outs(result)
    assert isinstance(o, LayoutOutputs)
    assert [f.name for f in dataclasses.fields(o)][0] == "review_needed"                           # Q8 (iv): 파생 출력의 첫 칸
    # 4.12 5: `devices` = 소자 이름순(`ly_device` key 순 -- graph 열은 key 정렬이라 입력 순은 필드에 없다). 집합은 입력 소자 전부.
    assert [d.name for d in o.devices] == sorted(["A", "B", "E", "F", "C", "D"])
    assert all(isinstance(d, DeviceLayout) for d in o.devices)
    assert [g.gid for g in groups(result)] == ["g1", "g2"]                                         # LAYOUT_ROLES 입력 그룹 전부, gid 정렬
    disp = G(result, lf.F_DISPOSITIONS)
    assert [(d.gid, d.disposition) for d in disp] == [("g3", "excluded_from_layout_matching")]
    assert all(isinstance(d, MatchingDisposition) for d in disp)
    rl = G(result, lf.F_ROWS)
    assert [f.name for f in dataclasses.fields(rl)] == ["rows", "box", "fold_attempts", "merge_decisions", "rebuilt_groups"]
    assert floorplan(result).outline_area_m2 > 0
    # 설계점 필드는 그대로 남아 있다(레이아웃 필드가 그 위에 더해졌다)
    for n in ("A", "B", "E", "F", "C", "D"):
        assert result.snapshot.value("device", n, "dp_op") == ("op", n)
    assert result.snapshot.block_version("dp_kernel") == DP_OP_VERSION


def test_hand_oracle_composite(result):
    g1, g2 = groups(result)
    assert (g1.method, g1.reason, g1.dx, g1.dy) == ("rotation_exact", "cc_same_W", 0.0, 0.0)
    assert (g2.method, g2.reason, g2.dx, g2.dy) == ("row_swap", "cc_same_W", 0.0, 0.0)
    o = outs(result)
    assert o.review_needed == ()
    by = {d.name: d for d in o.devices}
    # C: finger_quantization 요청 WRequest("C", 0.75e-6, 1e-6, ...)
    reqs = [w for w in o.w_requests if w.device == "C"]
    assert len(reqs) == 1 and isinstance(reqs[0], WRequest)
    assert (reqs[0].reason, reqs[0].group) == ("finger_quantization", None)
    assert reqs[0].W_old_m == pytest.approx(0.75e-6, rel=1e-9) and reqs[0].W_new_m == pytest.approx(1e-6)
    assert (by["C"].finger_w_m, by["C"].n_fingers) == (pytest.approx(1e-6), 1)
    # bias_distribution 멤버 C·D 는 일반 행 소자(그룹 행 아님)
    for n in ("C", "D"):
        assert by[n].origin == "row"
        assert all("/g3" not in rid for rid, _ in by[n].rows)
    assert o.coverage_ok is True and o.coverage_missing == ()
    assert o.w_invariant_ok is True


def test_preserved_quantities_and_tolerance(result):
    # 4.13 1·2·3: W_need = ID/J(toy J = 1 -> ID), err = |W_real − W_need| / W_need, err <= effective 또는 요청, W_m 그대로
    inp_W = 4e-6
    o = outs(result)
    names_with_req = {w.device for w in o.w_requests}
    for d in o.devices:
        assert d.W_m == inp_W
        ID = {"A": 2e-6, "B": 2e-6, "E": 2e-6, "F": 2e-6, "C": 0.75e-6, "D": 1e-6}[d.name]
        assert d.W_need_m == pytest.approx(ID, rel=1e-9)
        assert d.W_realized_m == pytest.approx(d.n_fingers * d.finger_w_m, rel=1e-12)
        assert d.W_err_rel == pytest.approx(abs(d.W_realized_m - d.W_need_m) / d.W_need_m, rel=1e-9, abs=1e-15)
        assert d.W_tol_effective == max(d.W_tol_upper, d.W_tol_lower)
        assert d.grid_dominated is (d.W_tol_lower > d.W_tol_upper)
        assert d.W_tol_lower == pytest.approx(1e-8 / (2 * d.finger_w_m), rel=1e-12)
        assert abs(d.W_tol_upper) <= 1e-12                                       # toy tol_V 0
        assert d.W_err_rel <= d.W_tol_effective or d.name in names_with_req
        assert sum(n for _, n in d.rows) == d.n_fingers
        assert list(d.rows) == sorted(d.rows)
        assert d.excluded_slices == ()
    by = {d.name: d for d in o.devices}
    assert by["A"].finger_w_m == by["B"].finger_w_m and by["E"].finger_w_m == by["F"].finger_w_m


def test_rows_finger_sums_match_devices(result):
    tot = Counter()
    for r in rows(result):
        for n, k in r.devices:
            tot[n] += k
    assert tot == Counter({d.name: d.n_fingers for d in outs(result).devices})
    for r in rows(result):                                                      # 행별 finger_w 하나
        assert len({r.finger_w_m}) == 1


def test_no_usable_slice_device(toy_lut):
    Z = dev("Z", "a", "b", 2e-6, gm_id=25.0, W=3e-6)
    res = run(composite(toy_pdk(toy_lut), extra=(Z,)), new_memo(toy_lut))
    o = outs(res)
    z = [d for d in o.devices if d.name == "Z"][0]
    assert z.W_m == 3e-6
    assert (z.finger_w_m, z.n_fingers, z.W_need_m, z.W_realized_m, z.W_err_rel, z.W_tol_lower, z.W_tol_upper,
            z.W_tol_effective, z.grid_dominated, z.origin) == (None,) * 10
    assert z.rows == ()
    assert z.excluded_slices == ((100, "lut_no_strong_inversion_root"), (200, "lut_no_strong_inversion_root"))
    assert res.snapshot.field(lf.DEVICE, "Z", lf.F_FINGER) is None                     # 필드: Z 는 ly_finger 없음
    zr = [w for w in o.w_requests if w.device == "Z"]
    assert len(zr) == 1 and (zr[0].W_old_m, zr[0].W_new_m, zr[0].reason, zr[0].group) == (3e-6, 3e-6, "no_usable_slice", None)
    assert o.coverage_ok is False and o.coverage_missing == ("Z",)
    assert o.w_invariant_ok is False
    assert "Z" not in [d.name for d in o.revalidation.devices]
    keys = [(w.device, w.reason) for w in o.w_requests]
    assert keys == sorted(keys)


def test_w_requests_collect_group_and_device_requests(toy_lut):
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6), dev("C", "x", "y", 0.75e-6)]
    res = run(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B", "C"))], toy_pdk(toy_lut)),
              new_memo(toy_lut))
    o = outs(res)
    assert [(w.device, w.reason, w.group) for w in o.w_requests] == [
        ("A", "cc_nf", "g1"), ("B", "cc_nf", "g1"), ("C", "finger_quantization", None)]
    assert o.review_needed == ()                                                 # pending 은 review 대상 아님
    assert o.w_invariant_ok is True


# --- review_needed (Q8 (iv)) -----------------------------------------------------------------------------------------

def test_review_needed_not_adjustable_diff_pair_no_relax(toy_lut):
    # [U12] CONTRACT 4.15 예(oracle (d) 계약 손계산): 조정 불가 c 1 -> 즉시 완화 없음(LY5 마지막 문장, D-LY2/R21), pattern None,
    # review_needed = (ReviewItem("g1", "diff_pair", "w_not_adjustable", None, None),) -- 옛 relaxed:w_not_adjustable(dx 1.0) 아님.
    ds = [dev("A", "h", "da", 1e-6, adj=False), dev("B", "h", "db", 1e-6, adj=False)]
    res = run(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))], toy_pdk(toy_lut)), new_memo(toy_lut))
    o = outs(res)
    assert o.review_needed == (ReviewItem("g1", "diff_pair", "w_not_adjustable", None, None),)
    g = groups(res)[0]
    steps = [a.step for a in g.attempts]
    assert "w_request" in steps and "relax" not in steps
    assert not [r for r in rows(res) if r.group == "g1"]                        # 패턴 행 없음(완화 배치 채택 안 함)
    assert sorted(n for r in rows(res) for n, _k in r.devices) == ["A", "B"]    # 멤버는 일반 행에 남는다(커버리지)
    assert o.coverage_ok is True


def test_review_needed_cc_only_not_adjustable(toy_lut):
    # 4.15 [r5]: c 1, 조정 불가, allowed_patterns=("common_centroid",) -> pattern None, reason w_not_adjustable,
    # review_needed = (ReviewItem("g1", "diff_pair", "w_not_adjustable", None, None),)  [U12: relaxed 필드 삭제]
    ds = [dev("A", "h", "da", 1e-6, adj=False), dev("B", "h", "db", 1e-6, adj=False)]
    res = run(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h", patterns=("common_centroid",))],
                         [rg("r1", ("A", "B"))], toy_pdk(toy_lut)), new_memo(toy_lut))
    g = groups(res)[0]
    assert (g.pattern, g.pending, g.provisional, g.reason) == (None, False, False, "w_not_adjustable")
    assert outs(res).review_needed == (ReviewItem("g1", "diff_pair", "w_not_adjustable", None, None),)


def test_review_needed_failed_cc_and_not_mirror(toy_lut):
    ds = [dev("E", "p", "q", 2e-6, gate="gc"), dev("F", "r", "t", 2e-6, gate="gx"),
          dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6)]
    gs = [mg("g2", ("E", "F"), "branch_symmetric", None), mg("m1", ("A", "B"), "mirror", None)]
    res = run(make_input(ds, gs, [rg("r1", ("E", "F")), rg("r2", ("A", "B"))], toy_pdk(toy_lut)), new_memo(toy_lut))
    assert [g.reason for g in groups(res)] == ["branch_gate_differs", "no_hub_net"]
    assert outs(res).review_needed == (ReviewItem("g2", "branch_symmetric", "branch_gate_differs", None, None),)


def test_review_needed_is_first_and_in_group_order(toy_lut):
    ds = [dev("A", "h", "da", 1e-6, adj=False), dev("B", "h", "db", 1e-6, adj=False),
          dev("E", "p", "q", 1e-6, gate="gc", adj=False), dev("F", "r", "t", 1e-6, gate="gc", adj=False)]
    gs = [mg("z2", ("E", "F"), "branch_symmetric", None), mg("a1", ("A", "B"), "diff_pair", "h")]
    res = run(make_input(ds, gs, [rg("r1", ("A", "B")), rg("r2", ("E", "F"))], toy_pdk(toy_lut)), new_memo(toy_lut))
    o = outs(res)
    # [U12] 즉시 완화 없음 -> 사유 = (iii) 사유 그대로, 무게중심 불일치 행 swap 은 채택하지 않아 그룹 dx·dy 없음
    assert [(r.gid, r.reason) for r in o.review_needed] == [("a1", "w_not_adjustable"), ("z2", "w_not_adjustable")]
    assert [f.name for f in dataclasses.fields(o)][0] == "review_needed"


def test_review_needed_uncentred_branch_symmetric_not_adopted(toy_lut):
    # branch_symmetric E·F ID 3e-6 조정 불가: 키 100 nf 3 만 ok -> 행 swap 2행(E2F2 / F1E1) dx 1.0.
    # [U12] 옛 동작은 이 무게중심 불일치 배치를 relax 로 채택하고 4.11 3 재구성(k = 3, dx 1/3)까지 갔다. LY5 즉시 완화 제거(D-LY2/R21)로
    # 이제 pattern None -> 패턴 행이 없어 재구성 대상도 없고, review_needed 에 (iii) 사유로 남는다(판정은 MOD8 몫).
    ds = [dev("E", "p", "q", 3e-6, gate="gc", adj=False), dev("F", "r", "t", 3e-6, gate="gc", adj=False)]
    res = run(make_input(ds, [mg("g2", ("E", "F"), "branch_symmetric", None)], [rg("r1", ("E", "F"))], toy_pdk(toy_lut)),
              new_memo(toy_lut))
    g = groups(res)[0]
    assert g.pattern is None and g.reason == "w_not_adjustable"
    assert ("cc_same_W", "row_swap", 1.0, 0.0) in [(a.step, a.method, a.dx, a.dy) for a in g.attempts]   # (i) 시도는 기록
    assert G(res, lf.F_ROWS).rebuilt_groups == ()
    assert not [r for r in rows(res) if r.group == "g2"]
    assert outs(res).review_needed == (ReviewItem("g2", "branch_symmetric", "w_not_adjustable", None, None),)


# --- 재검증 요청 (Q4 (ii)(iii)) ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("with_requests", [False, True])
def test_revalidation_always_required(toy_lut, with_requests):
    if with_requests:
        inp = composite(toy_pdk(toy_lut), diode_C=True)
    else:
        ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6, diode=True)]
        inp = make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))], toy_pdk(toy_lut))
    res = run(inp, new_memo(toy_lut))
    o = outs(res)
    assert bool(o.w_requests) is with_requests
    rv = o.revalidation
    assert isinstance(rv, Revalidation)
    assert rv.required is True
    assert rv.status == REVALIDATION_PENDING == "pending_wiring"
    assert rv.seals == REVALIDATION_SEALS
    assert (rv.consumer, rv.reason) == (REVALIDATION_CONSUMER, REVALIDATION_PENDING_REASON)
    by_in = {d.name: d for d in inp.devices}
    by_out = {d.name: d for d in o.devices}
    # 4.14: devices = 이름순 배치 소자(`ly_finger` 있는 소자)의 RealizedDevice
    assert [r.name for r in rv.devices] == sorted(d.name for d in inp.devices if by_out[d.name].n_fingers is not None)
    for r in rv.devices:
        assert isinstance(r, RealizedDevice)
        d, o_ = by_in[r.name], by_out[r.name]
        assert (r.kind, r.ID_A, r.gm_id, r.L_m, r.vds_V, r.vsb_V) == (d.kind, d.ID_A, d.gm_id, d.L_m, d.vds_V, d.vsb_V)
        assert (r.finger_w_m, r.n_fingers, r.W_need_m, r.W_realized_m) == (o_.finger_w_m, o_.n_fingers, o_.W_need_m, o_.W_realized_m)
        assert r.finger_w_key == round(o_.finger_w_m / 1e-8)
        assert r.recalibrate_id is (not d.diode)                                 # diode 는 ID 재보정 불필요
        assert r.recompute_node_voltages is True                                 # diode 도 노드전압·봉인은 다시
    assert any(not r.recalibrate_id for r in rv.devices)


# --- M3a 회귀 (toy) ----------------------------------------------------------------------------------------------------

def test_m3a_regression_toy(toy_lut):
    # 옛 규칙(err 대 W_m)이면 W_m 4e-6 에 정확히 맞는 키 200 nf 2(err 0)가 뽑힌다. 새 규칙은 W_need(= ID/J = 0.75e-6) 대비라
    # 그 후보는 존재하지 않고, 실현 W 는 W_need 쪽(1e-6, 키 100 nf 1)이며 허용오차 밖이라 요청이 난다.
    res = run(make_input([dev("M3a", "x", "y", 0.75e-6, W=4e-6)], [], [rg("r", ("M3a",))], toy_pdk(toy_lut)), new_memo(toy_lut))
    o = outs(res)
    d = o.devices[0]
    assert (d.finger_w_m, d.n_fingers) != (pytest.approx(2e-6), 2)
    assert d.W_realized_m == pytest.approx(1e-6)
    assert d.W_err_rel == pytest.approx(1 / 3, rel=1e-9)
    assert d.W_err_rel > d.W_tol_effective
    assert [(w.device, w.reason) for w in o.w_requests] == [("M3a", "finger_quantization")]


# --- 캐시 (4.13 10, L11) ----------------------------------------------------------------------------------------------

def _misses(memo):
    return {r: s.misses for r, s in memo.stats()}


def _assert_no_same_input_recompute(rp):
    """[XRUN-F1 card B C1] 그 test 실행(rp)의 계수에서 레이아웃 블록 4개 같은 입력 재계산 0."""
    for b in (finger_candidates, pattern_select, finger_geometry, compose_rows):
        assert block_row(rp["counters"], b.name)[5] == 0, b.name


def test_previous_same_input_computes_nothing(toy_lut):
    rp = fresh_run()
    memo = new_memo(toy_lut)
    inp = composite(toy_pdk(toy_lut))
    r1 = run(inp, memo, rp=rp)
    m1 = _misses(memo)
    r2 = run(inp, memo, previous=r1, rp=rp)
    assert r2.computed_blocks == ()
    assert r2.snapshot is r1.snapshot                                             # 4.13 10: 스냅샷이 previous.snapshot 그대로
    assert strip_volatile(r2) == strip_volatile(r1)
    assert _misses(memo) == m1                                                   # LUT 조회 재계산 0
    _assert_no_same_input_recompute(rp)


def test_rejected_only_change_reuses_slices_and_candidates(toy_lut):
    rp = fresh_run()
    memo = new_memo(toy_lut)
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6)]
    g, r = [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))]
    r1 = run(make_input(ds, g, r, toy_pdk(toy_lut)), memo, rp=rp)
    m1 = _misses(memo)
    r2 = run(make_input(ds, g, r, toy_pdk(toy_lut), rejected=("A",)), memo, previous=r1, rp=rp)
    assert "ly_slice_density" not in r2.computed_blocks
    assert "ly_finger_candidates" not in r2.computed_blocks
    assert "ly_pattern_select" in r2.computed_blocks
    assert _misses(memo) == m1
    assert groups(r2)[0].reason == "w_request_rejected"                         # [U12] 즉시 완화 없음(옛 "relaxed:" 접두 없음)
    assert groups(r2)[0].pattern is None
    _assert_no_same_input_recompute(rp)


def test_id_change_recomputes_from_slices(toy_lut):
    memo = new_memo(toy_lut)
    inp1 = composite(toy_pdk(toy_lut))
    r1 = run(inp1, memo)
    devs = tuple(dataclasses.replace(d, ID_A=1.5 * d.ID_A) if d.name == "D" else d for d in inp1.devices)
    r2 = run(dataclasses.replace(inp1, devices=devs), memo, previous=r1)
    assert r2.computed_blocks[:1] == ("ly_slice_density",)
    assert "ly_finger_candidates" in r2.computed_blocks
    assert list(r2.computed_blocks) == [w for w in ALL_WRITERS if w in r2.computed_blocks]


def test_reference_w_change_does_not_recompute_slices(toy_lut):
    # 슬라이스 키 = 보존량(kind, L, ID, gm/ID, vds, vsb) -- 참고 W_m 은 키가 아니다
    memo = new_memo(toy_lut)
    inp1 = composite(toy_pdk(toy_lut))
    r1 = run(inp1, memo)
    m1 = _misses(memo)
    devs = tuple(dataclasses.replace(d, W_m=7e-6) for d in inp1.devices)
    r2 = run(dataclasses.replace(inp1, devices=devs), memo, previous=r1)
    assert "ly_slice_density" not in r2.computed_blocks
    assert _misses(memo) == m1
    assert all(d.W_m == 7e-6 for d in outs(r2).devices)
    assert all(d.W_m == 7e-6 for _n, d in r2.snapshot.column(lf.DEVICE, lf.F_DEVICE))


def test_lut_fingerprint_is_part_of_slice_key(toy_lut, tmp_path):
    other = build_toy_lut(tmp_path / "other", id_scale=2.0)
    r1 = run(composite(toy_pdk(toy_lut)), new_memo(toy_lut))
    r2 = run(composite(toy_pdk(other)), new_memo(other), previous=r1)
    assert r2.computed_blocks[:1] == ("ly_slice_density",)
    # 슬라이스 ID 2배 -> J 2배 -> W_need 절반
    a1 = [d for d in outs(r1).devices if d.name == "A"][0]
    a2 = [d for d in outs(r2).devices if d.name == "A"][0]
    assert a2.W_need_m == pytest.approx(a1.W_need_m / 2, rel=1e-9)


def test_identical_preserved_quantities_computed_once(toy_lut, monkeypatch):
    calls = Counter()
    real = run_mod.slice_density

    def spy(memo, device, keys):
        calls[(device.kind, device.L_m, device.ID_A, device.gm_id, device.vds_V, device.vsb_V, tuple(keys))] += 1
        return real(memo, device, keys)

    monkeypatch.setattr(run_mod, "slice_density", spy)
    ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("Q", "q1", "q2", 2e-6, W=9e-6)]
    run(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B", "Q"))], toy_pdk(toy_lut)), new_memo(toy_lut))
    assert sum(calls.values()) > 0, "계측이 걸리지 않았다"
    assert set(calls.values()) == {1}, dict(calls)


# --- 결정론 (4.13 9) --------------------------------------------------------------------------------------------------

DET_CODE = r'''
import tempfile, dataclasses
from conftest import build_toy_lut, new_memo, toy_pdk, dev, make_input, mg, rg, strip_volatile, design_point_of
from gmid_engine.layout import run_layout
lut = build_toy_lut(tempfile.mkdtemp())
pdk = toy_pdk(lut, overhead=0.05e-6, gap=0.1e-6, dummy=0.2e-6, tap=0.3e-6, well=1e-6)
ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("E", "p", "q", 16e-6, gate="gc"),
      dev("F", "r", "t", 16e-6, gate="gc"), dev("C", "x", "y", 1e-6), dev("D", "y", "z", 1e-6), dev("G", "y", "w", 1e-6),
      dev("H", "k", "m", 12e-6), dev("P", "vdd", "o", 2e-6, kind="nmos", body="sub2")]
groups = [mg("g1", ("A", "B"), "diff_pair", "h"), mg("g2", ("E", "F"), "branch_symmetric", None),
          mg("g3", ("C", "G"), "bias_distribution", "y")]
rgs = [rg("r1", ("A", "B")), rg("r2", ("E", "F")), rg("r", ("C", "D")), rg("r4", ("G", "H")), rg("rp", ("P",), body="sub2")]
inp = make_input(ds, groups, rgs, pdk)
from gmid_engine.search import open_run
donors, counters = open_run()
res = run_layout(inp, new_memo(lut), design_point_of(inp), donors=donors, counters=counters)
RESULT = repr(strip_volatile(res))
'''


def test_determinism_across_hash_seeds(seed_runner):
    outs_ = {seed: seed_runner(DET_CODE, seed) for seed in (1, 2, 3)}
    assert len(set(outs_.values())) == 1


# --- 실 LUT M3a 회귀 (CONTRACT 4.18 [r5] -- 계약 수치는 r5 이전 참고값이라 기대값으로 쓰지 않는다) ------------------------
# 기대값 경로: 슬라이스 값(vgs·J·tol_V)은 4.2 의 정의 그대로 lut 공개 API(vgs_for_gm_id·op_point·tol_v_table.at -- lut 계약·test 소관)로
# 따로 구하고, 그 위의 레이아웃 규칙(4.2 W_need·4.3 허용오차·4.4 후보·4.7 폭 키 선택)은 이 파일에서 독립 구현해 대조한다.
# 회귀 판정은 계약이 고정한 비교 방법만: 옛 규칙(err 대 참고 W_m)의 후보가 아니라 W_need 기준으로 고른다.

import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

_SKILL = Path(__file__).resolve().parents[3]
REAL_MANIFEST = os.environ.get("GMID_LUT_MANIFEST", r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\engine\lut_slices\manifest.json")
REAL_CAP = os.environ.get("GMID_LUT_CAP_NPZ", str(_SKILL / "assets" / "sky130_nfet_pfet_lut_sample.npz"))
REAL_TLEF = os.environ.get("GMID_PDK_TLEF", r"C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef")
REAL_KEYS = (600, 1000)          # 실행 시간(슬라이스당 tol_V 표) 때문에 4.18 의 두 후보 키만 PDK 폭 키로 준다
# 파일럿 소자(4.18; ID·gm/ID·VDS·VSB 는 tools/spice_oracle/smoke 의 sizing oracle_input, W_m = DM T1 표의 참고 W)
PILOT = (("M3a", 1e-6, 4.9822534479836025e-06, 15.0, 0.2, 0.4772784768243529, 3.495e-6),
         ("M3b", 1e-6, 4.9822534479836025e-06, 15.0, 0.2, 0.47727847682435304, 3.393e-6),
         ("M4a", 1.5e-6, 4.9822534479836025e-06, 16.0, 0.45, 0.02727847682435297, 5.215e-6),
         ("M4b", 1.5e-6, 4.9822534479836025e-06, 16.0, 0.45, 0.02727847682435297, 5.215e-6))


def _need(p, what):
    if not Path(p).is_file():
        pytest.fail("실데이터 없음: %s (%s) -- skip 하지 않는다" % (what, p), pytrace=False)
    return p


def _grid(tlef):
    m = re.search(r"^\s*MANUFACTURINGGRID\s+([0-9.eE+-]+)\s*;", Path(tlef).read_text(encoding="utf-8", errors="replace"), re.M)
    return float(m.group(1)) * 1e-6


def _real_spec(manifest, grid):
    from gmid_engine.lut import LutSpec
    base = Path(manifest).parent
    mins = {}
    kinds = {"nfet_01v8": "nmos", "pfet_01v8": "pmos"}
    for s in json.loads(Path(manifest).read_text(encoding="utf-8"))["slices"]:
        with np.load(base / s["file"]) as z:
            W = float(z["W"])
        k = kinds[s["device"]]
        mins[k] = min(W, mins.get(k, W))
    return LutSpec(grid, tuple(sorted(mins.items())), tuple(sorted(kinds.items())), (("nmos", "_n"), ("pmos", "_p")))


def _slice_values(memo, kind, key, L, ID_A, gm_id, vds, vsb):
    """4.2 의 정의 그대로(lut 공개 API): vgs, J = IDu / L, W_need = ID_A / J, tol = id_equivalent 셀."""
    from gmid_engine.lut import op_point, tol_v_table, vgs_for_gm_id
    vgs = vgs_for_gm_id(memo, kind, key, gm_id, L, vds, vsb)
    J = op_point(memo, kind, key, L, vgs, vds, vsb).IDu / L
    tol = tol_v_table(memo, kind, key).at(L, vds, "id_equivalent")
    return {"vgs": vgs, "J": J, "W_need": ID_A / J, "tol": float(tol)}


def _oracle_geometry(memo, devs, grid):
    """4.3·4.4 후보 + 4.7 비그룹 행 그룹 규칙(독립 구현). 반환 ({이름: (키, nf, W_need, err, effective, ok)}, 후보)."""
    cands = {}
    for name, L, ID, gm, vds, vsb, _W in devs:
        out = []
        for key in REAL_KEYS:
            o = _slice_values(memo, "nmos", key, L, ID, gm, vds, vsb)
            fw = key * grid
            q = o["W_need"] / fw
            for nf in sorted({max(1, math.floor(q)), max(1, math.ceil(q))}):
                err = abs(nf * fw - o["W_need"]) / o["W_need"]
                eff = max(o["tol"] * gm, grid / (2 * fw))
                out.append((key, nf, o["W_need"], err, eff, err <= eff))
        cands[name] = out
    chosen, remaining = {}, [d[0] for d in devs]
    while remaining:
        keys = sorted({c[0] for n in remaining for c in cands[n] if c[5]})
        if not keys:
            break

        def score(key):
            okd = [n for n in remaining if any(c[0] == key and c[5] for c in cands[n])]
            nfsum = sum(min((c for c in cands[n] if c[0] == key and c[5]), key=lambda c: (c[3], c[1]))[1] for n in okd)
            return (-len(okd), nfsum, -key), okd
        key = min(keys, key=lambda k: score(k)[0])
        for n in score(key)[1]:
            chosen[n] = min((c for c in cands[n] if c[0] == key and c[5]), key=lambda c: (c[3], c[1]))
            remaining.remove(n)
    for n in remaining:
        chosen[n] = min(cands[n], key=lambda c: (c[3], c[1], -c[0]))
    return chosen, cands


@pytest.mark.layout_realdata
def test_m3a_regression_real_lut():
    """4.18 [r5]: 실 LUT 에서 레이아웃이 W_need(fw) 기준 규칙으로 고르고, 옛 규칙(err 대 참고 W_m)의 후보를 고르지 않는다.

    r5 이전 계약 수치(키 600·17.1 %·1.4 %)는 기대값으로 쓰지 않는다. 선택은 독립 구현(_oracle_geometry) 결과와 같아야 하고,
    옛 규칙의 '43 %' 후보(M3a 키 1000 nf 1)가 새 규칙에서 행 공통 키 밖이 되면(M4a·M4b 에게 키 1000 이 ok 아님) 선택되지 않아야 한다.
    """
    from gmid_engine.layout import LayoutPdk
    from gmid_engine.lut import load_lut_set
    grid = _grid(_need(REAL_TLEF, "PDK tlef"))
    manifest = _need(REAL_MANIFEST, "폭 슬라이스 manifest")
    lut = load_lut_set(manifest, _need(REAL_CAP, "기준 LUT"), _real_spec(manifest, grid))
    full = toy_pdk(lut)
    pdk = LayoutPdk(full.manufacturing_grid_m, (("nmos", REAL_KEYS),), 0.0, 0.0, 0.0, 0.0, 0.0, full.rule_ids, lut.fp)
    ds = [dev(n, "s_" + n, "d_" + n, None, ID_A=ID, L=L, gm_id=gm, vds=vds, vsb=vsb, W=W) for n, L, ID, gm, vds, vsb, W in PILOT]
    memo = new_memo(lut)
    res = run(make_input(ds, [], [rg("rp", [d.name for d in ds])], pdk), memo)
    o = outs(res)
    chosen, cands = _oracle_geometry(memo, PILOT, grid)
    by = {d.name: d for d in o.devices}
    for name, (key, nf, W_need, err, eff, ok) in chosen.items():
        d = by[name]
        assert d.W_need_m == pytest.approx(W_need, rel=1e-12), name
        assert (round(d.finger_w_m / grid), d.n_fingers) == (key, nf), name
        assert d.W_err_rel == pytest.approx(err, rel=1e-9, abs=1e-15), name
        assert d.W_tol_effective == pytest.approx(eff, rel=1e-12), name
        assert d.W_err_rel == pytest.approx(abs(d.W_realized_m - d.W_need_m) / d.W_need_m, rel=1e-12)   # 대 W_need, 대 W_m 아님
        assert d.W_m == dict((p[0], p[6]) for p in PILOT)[name]                                       # W 를 바꾸지 않는다
    reqs = {w.device for w in o.w_requests}
    for d in o.devices:
        assert d.W_err_rel <= d.W_tol_effective or d.name in reqs
    # 옛 규칙의 후보(대 참고 W_m 오차): M3a 키 1000 nf 1 = |5 µm − 3.495 µm| / 3.495 µm
    old_err = abs(1000 * grid - 3.495e-6) / 3.495e-6
    assert old_err == pytest.approx(0.431, abs=1e-3)
    key1000_ok_for_m4 = any(c[0] == 1000 and c[5] for n in ("M4a", "M4b") for c in cands[n])
    if not key1000_ok_for_m4:
        assert (round(by["M3a"].finger_w_m / grid), by["M3a"].n_fingers) != (1000, 1)
    assert o.revalidation.required is True and o.revalidation.status == "pending_wiring"


# --- [U12] ly.diffusion(LY8, 4.10a·4.12 7) 과 수동소자 블록(D-LY4, 4.10·4.12 2) -- run_layout 경로 ------------------------------
# oracle (a) 물리 불변식: 확산 영역은 남김없이 finger 에 나뉜다(KCL 처럼 보존) --
#   Σ_소자 n_f·(ad + as) = Σ_섬 (k + 1)·W·D,   Σ_소자 n_f·(pd + ps) = Σ_섬 (2kW + 2D(k + 1) + 2W)
#   (섬 하나 = finger k 개·영역 k+1 개: 게이트 쪽 변 2k 개, 영역마다 위·아래 STI 변 2D, 양끝 반대쪽 변 둘).
#   finger 평균은 [공유, 섬 끝] 사이: W·D/2 <= ad, as <= W·D,  W + D <= pd, ps <= 2W + 2D.

from gmid_engine.layout.contract_input import LayoutPassive  # noqa: E402
from gmid_engine.layout.contract_output import DeviceDiffusion  # noqa: E402

OVH = 0.28e-6


def _islands(r):
    return r.segments if r.segments else ((r.transistor_sequence, r.node_sequence),)


def _diffusion_case(toy_lut, passives=()):
    pdk = toy_pdk(toy_lut, overhead=OVH, gap=0.47e-6, dummy=0.54e-6, tap=0.68e-6, well=1.63e-6)
    return run(composite(pdk, extra=(dev("G", "y", "w", 1e-6), dev("H", "k", "m", 3e-6))), new_memo(toy_lut)), pdk


def test_diffusion_output_and_revalidation_carry(toy_lut):
    res, _ = _diffusion_case(toy_lut)
    dif = diffusion(res)
    assert all(isinstance(d, DeviceDiffusion) for d in dif)
    names = [d.name for d in dif]
    assert names == sorted(names)
    o = outs(res)
    by_dev = {d.name: d for d in o.devices}
    assert set(names) == {n for n, d in by_dev.items() if d.n_fingers is not None}
    for d in dif:
        assert d.n_fingers == by_dev[d.name].n_fingers                       # 행 finger 수 합 == 소자 nf
        assert d.finger_w_m == by_dev[d.name].finger_w_m
    by_name = {d.name: d for d in dif}
    for r in o.revalidation.devices:                                         # RealizedDevice.diffusion = 그 소자의 DeviceDiffusion
        assert r.diffusion == by_name[r.name]


def test_diffusion_conserves_regions(toy_lut):
    res, _ = _diffusion_case(toy_lut)
    dif = diffusion(res)
    area_sum = sum(d.n_fingers * (d.ad_m2 + d.as_m2) for d in dif)
    perim_sum = sum(d.n_fingers * (d.pd_m + d.ps_m) for d in dif)
    exp_area = exp_perim = 0.0
    for r in rows(res):
        W = r.finger_w_m
        for seq, _nodes in _islands(r):
            k = len(seq)
            exp_area += (k + 1) * W * OVH
            exp_perim += 2 * k * W + 2 * OVH * (k + 1) + 2 * W
    assert area_sum == pytest.approx(exp_area, rel=1e-9)
    assert perim_sum == pytest.approx(exp_perim, rel=1e-9)
    for d in dif:
        W = d.finger_w_m
        for a in (d.ad_m2, d.as_m2):
            assert W * OVH / 2 * (1 - 1e-9) <= a <= W * OVH * (1 + 1e-9)
        for p in (d.pd_m, d.ps_m):
            assert (W + OVH) * (1 - 1e-9) <= p <= (2 * W + 2 * OVH) * (1 + 1e-9)


def test_passives_reach_floorplan(toy_lut):
    # 손계산: A = 3e-12 m² = 3e4 칸(g 1e-8) -> 174 x 173 칸 = 3.0102e-12 m² (test_floorplan PASSIVE_HAND 와 같은 수)
    res0, pdk = _diffusion_case(toy_lut)
    inp = composite(pdk, extra=(dev("G", "y", "w", 1e-6), dev("H", "k", "m", 3e-6)))
    res = run(dataclasses.replace(inp, passives=(LayoutPassive("Cc", 3e-12),)), new_memo(toy_lut))
    assert G(res, lf.F_PASSIVES) == (LayoutPassive("Cc", 3e-12),)
    assert floorplan(res).passive_area_m2 == pytest.approx(30102e-16, rel=1e-9)
    assert floorplan(res).outline_area_m2 > floorplan(res0).outline_area_m2
    assert floorplan(res).included[-1][0] == "passive_blocks_mim_poly_resistor"
    assert rows(res) == rows(res0) and outs(res).devices == outs(res0).devices   # 수동소자는 MOS 배치를 바꾸지 않는다


def test_passives_only_change_recomputes_rows_block_only(toy_lut):
    # 4.12 캐시: 수동소자만 바뀌면 슬라이스·후보·패턴·finger 블록은 다시 계산하지 않고 ly_rows(floorplan) 만 다시 계산한다
    rp = fresh_run()
    memo = new_memo(toy_lut)
    inp = composite(toy_pdk(toy_lut))
    r1 = run(inp, memo, rp=rp)
    r2 = run(dataclasses.replace(inp, passives=(LayoutPassive("Cc", 3e-12),)), memo, previous=r1, rp=rp)
    assert r2.computed_blocks == ("ly_rows",)
    assert floorplan(r2).passive_area_m2 == pytest.approx(30102e-16, rel=1e-9)
    _assert_no_same_input_recompute(rp)
    # 되돌리면 수동소자 없음(스냅샷은 직전 값만 들고 있다). [XRUN-F1 card B C4·C6] 같은 실행이면 r1 의 ly_rows 입력은 색인에 있어 이식된다 --
    # computed_blocks 는 '값을 쓴 writer(계산 또는 이식)'라 그대로 ("ly_rows",), 같은 입력 재계산은 여전히 0
    r3 = run(inp, memo, previous=r2, rp=rp)
    _assert_no_same_input_recompute(rp)
    assert r3.computed_blocks == ("ly_rows",)
    assert floorplan(r3).passive_area_m2 == 0.0
    assert floorplan(r3) == floorplan(r1)


# --- [U17 1-e] 레이아웃 결과 = 설계점 스냅샷의 S2 `layout` 필드 (design 40 v1.6 §2.4.7 `LayoutResult` 행, §2.4.8 '레이아웃 결과' 행,
#     §2.4.1 설계점 층(S2), EP-2 '필드가 곧 캐시') ---------------------------------------------------------------------------
# 독립 기대값: 필드 이름·writer = `_ly_fields.py`(design 이 "as-built 필드 이름 그대로"로 지정), 쓰기 횟수·입력 버전·값 유지 =
# core `GraphSnapshot.write` 계약. 피검 결과로 기대값을 만들지 않는다.
# 호출 형식(as-built 서명, CONTRACT 4.12): 셋째 위치 인자 `design_point` = 설계점 스냅샷(`GraphSnapshot`), 넷째 `previous` = 같은 설계점 위
# 앞 호출의 `LayoutResult`(재시도 = 같은 설계점 lineage 의 새 스냅샷, §2.4.7). 레이아웃 필드를 이미 가진 설계점 스냅샷(앞 결과의 스냅샷)을
# `design_point` 로 다시 주는 것도 같은 lineage 다(권한표가 이미 넓혀져 있고 설계점 block_version 이 같다).
# `LayoutResult` 두 칸의 이름은 as-built `snapshot`·`computed_blocks` 를 쓴다(design 은 '스냅샷, 이번 호출의 계산 블록 목록'만 적음).

DP_WRITERS = dp_writers()
MOD7_WRITERS = frozenset((lf.WRITER_INPUT, lf.WRITER_SLICES) + lf.BLOCK_WRITERS)


def _assert_design_point_kept(snap, dp, names):
    for n in names:
        assert snap.field("device", n, "dp_op") == dp.field("device", n, "dp_op")
    assert snap.field("graph", DP_GRAPH_KEY, "dp_metric") == dp.field("graph", DP_GRAPH_KEY, "dp_metric")
    assert snap.block_version("dp_kernel") == DP_OP_VERSION
    assert snap.block_version("dp_metrics") == DP_METRIC_VERSION


def test_layout_fields_written_on_design_point_snapshot(toy_lut):
    # §2.4.8: 레이아웃 결과 -> S2 `layout` 필드(`_ly_fields.py` 이름 그대로), §2.4.7: 레이아웃 필드는 그 설계점 스냅샷의 필드
    inp = composite(toy_pdk(toy_lut))
    names = tuple(d.name for d in inp.devices)
    dp = design_point(names)
    r = run_layout(inp, new_memo(toy_lut), dp, **fresh_run())
    snap = r.snapshot
    assert isinstance(snap, GraphSnapshot)
    for (kind, key, field), fv in layout_fields(snap, names).items():
        assert fv is not None, (kind, key, field)
    _assert_design_point_kept(snap, dp, names)
    for n in names:                                    # 같은 소자 레코드에 설계점 필드와 레이아웃 필드가 함께 있다(사본 레코드 없음)
        rec = snap.record("device", n)
        assert rec.get("dp_op") is not None and rec.get(lf.F_FINGER) is not None, n


def test_layout_field_writers_are_single_mod7_blocks(toy_lut):
    # §2.4.8 writer = MOD7 블록, 필드마다 writer 하나(SC-a). 레이아웃 writer 는 레이아웃 필드만 쓴다.
    inp = composite(toy_pdk(toy_lut))
    names = tuple(d.name for d in inp.devices)
    r = run_layout(inp, new_memo(toy_lut), design_point(names), **fresh_run())
    table = r.snapshot.writers
    for (kind, field), writer in lf.LY_WRITERS.entries:
        assert writer in MOD7_WRITERS
        assert table.writer_of(kind, field) == writer, (kind, field)
    for (kind, key, field), fv in layout_fields(r.snapshot, names).items():
        assert fv.writer == lf.LY_WRITERS.writer_of(kind, field), (kind, key, field)
    for writer in MOD7_WRITERS:
        assert set(table.fields_of(writer)) == set(lf.LY_WRITERS.fields_of(writer)), writer
    for (kind, field), writer in DP_WRITERS.entries:   # 설계점 필드의 writer 는 그대로
        assert table.writer_of(kind, field) == writer


def test_no_separate_layout_lineage(toy_lut, monkeypatch):
    # §2.4.7: "별도 lineage는 없다" -- 설계점 스냅샷이 주어지면 레이아웃은 빈 스냅샷에서 새 lineage 를 시작하지 않는다
    def no_new_lineage(cls, writers):
        raise AssertionError("run_layout 이 GraphSnapshot.empty 로 별도 lineage 를 만들었다")

    inp = composite(toy_pdk(toy_lut))
    names = tuple(d.name for d in inp.devices)
    dp = design_point(names)
    rp = fresh_run()                       # open_run() 은 GraphSnapshot.empty 를 부르지 않는다는 가정 없이 monkeypatch 앞에서 만든다
    monkeypatch.setattr(GraphSnapshot, "empty", classmethod(no_new_lineage))
    r = run_layout(inp, new_memo(toy_lut), dp, **rp)
    _assert_design_point_kept(r.snapshot, dp, names)


def test_layout_result_carries_only_snapshot_and_computed_blocks(toy_lut):
    # §2.4.7: `LayoutResult` 는 (스냅샷, 이번 호출의 계산 블록 목록)만 둔다 -- 결과 값 사본 없음
    inp = composite(toy_pdk(toy_lut))
    r = run_layout(inp, new_memo(toy_lut), design_point(tuple(d.name for d in inp.devices)), **fresh_run())
    assert isinstance(r.snapshot, GraphSnapshot)
    assert isinstance(r.computed_blocks, tuple) and all(isinstance(w, str) for w in r.computed_blocks)
    assert set(r.computed_blocks) <= MOD7_WRITERS


def test_same_design_point_second_request_reuses_fields(toy_lut):
    # EP-2·§2.4.1: 필드가 곧 캐시 -- 같은 설계점 lineage 에서 같은 입력으로 다시 요청하면 계산 0, 같은 필드(입력 버전·쓰기 횟수 불변)
    memo = new_memo(toy_lut)
    inp = composite(toy_pdk(toy_lut))
    names = tuple(d.name for d in inp.devices)
    dp = design_point(names)
    rp = fresh_run()
    r1 = run_layout(inp, memo, dp, **rp)
    m1 = _misses(memo)
    r2 = run_layout(inp, memo, r1.snapshot, **rp)
    assert r2.computed_blocks == ()
    assert _misses(memo) == m1                                                   # LUT 조회도 다시 하지 않는다
    assert r2.snapshot.fp == r1.snapshot.fp
    assert layout_fields(r2.snapshot, names) == layout_fields(r1.snapshot, names)   # value·writer·입력 버전·쓰기 횟수
    for writer in MOD7_WRITERS:
        assert r2.snapshot.block_version(writer) == r1.snapshot.block_version(writer), writer
    _assert_design_point_kept(r2.snapshot, dp, names)


def test_layout_retry_stays_on_design_point_lineage(toy_lut):
    # §2.4.7: 레이아웃 재시도는 같은 설계점 lineage 의 새 스냅샷 -- 설계점 필드 유지, 바뀐 레이아웃 입력 필드는 같은 lineage 의 둘째 쓰기
    memo = new_memo(toy_lut)
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6)]
    g, rgs = [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))]
    dp = design_point(("A", "B"))
    rp = fresh_run()
    r1 = run_layout(make_input(ds, g, rgs, toy_pdk(toy_lut)), memo, dp, **rp)
    r2 = run_layout(make_input(ds, g, rgs, toy_pdk(toy_lut), rejected=("A",)), memo, r1.snapshot, **rp)
    _assert_design_point_kept(r2.snapshot, dp, ("A", "B"))
    rej = r2.snapshot.field(lf.GRAPH, lf.GRAPH_KEY, lf.F_REJECTED)
    assert rej.value == ("A",)
    assert (rej.writer, rej.write_count) == (lf.WRITER_INPUT, 2)
    assert r2.snapshot.field(lf.GRAPH, lf.GRAPH_KEY, lf.F_GROUPS).write_count == 2


def test_layout_retry_via_previous_keyword_is_same_lineage(toy_lut):
    # 4.12 2 as-built 호출 형식: `previous=앞 결과` 도 같은 설계점 lineage 의 둘째 쓰기(위 test 와 같은 판정, 호출 형식만 다름)
    memo = new_memo(toy_lut)
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6)]
    g, rgs = [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))]
    dp = design_point(("A", "B"))
    rp = fresh_run()
    r1 = run_layout(make_input(ds, g, rgs, toy_pdk(toy_lut)), memo, dp, **rp)
    r2 = run_layout(make_input(ds, g, rgs, toy_pdk(toy_lut), rejected=("A",)), memo, dp, previous=r1, **rp)
    _assert_design_point_kept(r2.snapshot, dp, ("A", "B"))
    rej = r2.snapshot.field(lf.GRAPH, lf.GRAPH_KEY, lf.F_REJECTED)
    assert (rej.value, rej.writer, rej.write_count) == (("A",), lf.WRITER_INPUT, 2)
    assert r2.snapshot.field(lf.GRAPH, lf.GRAPH_KEY, lf.F_GROUPS).write_count == 2
    assert r2.snapshot.writers == r1.snapshot.writers
