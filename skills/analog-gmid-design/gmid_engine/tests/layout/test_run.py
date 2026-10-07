"""CONTRACT 4.12~4.14 `run_layout(layout_input, memo, previous=None) -> LayoutResult` -- 입력·출력 계약, 불변식 4.13, 재검증 요청,
캐시(필드 = 캐시, LUT 지문 + 보존량 키), 결정론, M3a 회귀(toy).

실 LUT M3a 회귀는 `test_run_realdata.py` 가 아니라 이 파일 끝(마커 `layout_realdata`)에 둔다(규칙 H 1:1).
"""
from __future__ import annotations

import dataclasses
import math
from collections import Counter
from fractions import Fraction

import pytest

from gmid_engine.layout import LayoutResult, run_layout
from gmid_engine.layout import run as run_mod
from gmid_engine.layout.contract_output import (REVALIDATION_CONSUMER, REVALIDATION_PENDING, REVALIDATION_PENDING_REASON,
                                                REVALIDATION_SEALS, DeviceLayout, MatchingDisposition, RealizedDevice,
                                                ReviewItem, Revalidation, WRequest)
from gmid_engine.layout.finger_candidates import finger_candidates
from gmid_engine.layout.finger_geometry import finger_geometry
from gmid_engine.layout.pattern_select import pattern_select
from gmid_engine.layout.rows import compose_rows

from .conftest import (build_toy_lut, centroid_offsets, dev, make_input, mg, new_memo, rg, strip_volatile, toy_pdk)

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


@pytest.fixture
def result(toy_lut):
    return run_layout(composite(toy_pdk(toy_lut)), new_memo(toy_lut))


# --- 입력 계약 --------------------------------------------------------------------------------------------------------

def test_lut_fingerprint_mismatch_rejected(toy_lut, tmp_path):
    other = build_toy_lut(tmp_path / "other", id_scale=2.0)
    assert other.fp != toy_lut.fp
    with pytest.raises(ValueError):
        run_layout(composite(toy_pdk(other)), new_memo(toy_lut))


# --- 출력 계약 --------------------------------------------------------------------------------------------------------

def test_output_shape(result):
    assert isinstance(result, LayoutResult)
    assert [f.name for f in dataclasses.fields(result)][0] == "review_needed"
    assert [d.name for d in result.devices] == ["A", "B", "E", "F", "C", "D"]          # 입력 순
    assert all(isinstance(d, DeviceLayout) for d in result.devices)
    assert [g.gid for g in result.groups] == ["g1", "g2"]                             # LAYOUT_ROLES 입력 그룹 전부, gid 정렬
    assert [(d.gid, d.disposition) for d in result.matching_dispositions] == [("g3", "excluded_from_layout_matching")]
    assert all(isinstance(d, MatchingDisposition) for d in result.matching_dispositions)
    assert result.computed_blocks == ALL_WRITERS
    rl = result.snapshot.value("graph", "layout", "ly_rows")
    assert (result.rows, result.box, result.fold_attempts, result.merge_decisions) == (
        rl.rows, rl.box, rl.fold_attempts, rl.merge_decisions)
    assert result.floorplan is result.snapshot.value("graph", "layout", "ly_floorplan")


def test_hand_oracle_composite(result):
    g1, g2 = result.groups
    assert (g1.method, g1.reason, g1.dx, g1.dy) == ("rotation_exact", "cc_same_W", 0.0, 0.0)
    assert (g2.method, g2.reason, g2.dx, g2.dy) == ("row_swap", "cc_same_W", 0.0, 0.0)
    assert result.review_needed == ()
    by = {d.name: d for d in result.devices}
    # C: finger_quantization 요청 WRequest("C", 0.75e-6, 1e-6, ...)
    reqs = [w for w in result.w_requests if w.device == "C"]
    assert len(reqs) == 1 and isinstance(reqs[0], WRequest)
    assert (reqs[0].reason, reqs[0].group) == ("finger_quantization", None)
    assert reqs[0].W_old_m == pytest.approx(0.75e-6, rel=1e-9) and reqs[0].W_new_m == pytest.approx(1e-6)
    assert (by["C"].finger_w_m, by["C"].n_fingers) == (pytest.approx(1e-6), 1)
    # bias_distribution 멤버 C·D 는 일반 행 소자(그룹 행 아님)
    for n in ("C", "D"):
        assert by[n].origin == "row"
        assert all("/g3" not in rid for rid, _ in by[n].rows)
    assert result.coverage_ok is True and result.coverage_missing == ()
    assert result.w_invariant_ok is True


def test_preserved_quantities_and_tolerance(result):
    # 4.13 1·2·3: W_need = ID/J(toy J = 1 -> ID), err = |W_real − W_need| / W_need, err <= effective 또는 요청, W_m 그대로
    inp_W = 4e-6
    names_with_req = {w.device for w in result.w_requests}
    for d in result.devices:
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
    by = {d.name: d for d in result.devices}
    assert by["A"].finger_w_m == by["B"].finger_w_m and by["E"].finger_w_m == by["F"].finger_w_m


def test_rows_finger_sums_match_devices(result):
    tot = Counter()
    for r in result.rows:
        for n, k in r.devices:
            tot[n] += k
    assert tot == Counter({d.name: d.n_fingers for d in result.devices})
    for r in result.rows:                                                       # 행별 finger_w 하나
        assert len({r.finger_w_m}) == 1


def test_no_usable_slice_device(toy_lut):
    Z = dev("Z", "a", "b", 2e-6, gm_id=25.0, W=3e-6)
    res = run_layout(composite(toy_pdk(toy_lut), extra=(Z,)), new_memo(toy_lut))
    z = [d for d in res.devices if d.name == "Z"][0]
    assert z.W_m == 3e-6
    assert (z.finger_w_m, z.n_fingers, z.W_need_m, z.W_realized_m, z.W_err_rel, z.W_tol_lower, z.W_tol_upper,
            z.W_tol_effective, z.grid_dominated, z.origin) == (None,) * 10
    assert z.rows == ()
    assert z.excluded_slices == ((100, "lut_no_strong_inversion_root"), (200, "lut_no_strong_inversion_root"))
    zr = [w for w in res.w_requests if w.device == "Z"]
    assert len(zr) == 1 and (zr[0].W_old_m, zr[0].W_new_m, zr[0].reason, zr[0].group) == (3e-6, 3e-6, "no_usable_slice", None)
    assert res.coverage_ok is False and res.coverage_missing == ("Z",)
    assert res.w_invariant_ok is False
    assert "Z" not in [d.name for d in res.revalidation.devices]
    keys = [(w.device, w.reason) for w in res.w_requests]
    assert keys == sorted(keys)


def test_w_requests_collect_group_and_device_requests(toy_lut):
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6), dev("C", "x", "y", 0.75e-6)]
    res = run_layout(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B", "C"))],
                                toy_pdk(toy_lut)), new_memo(toy_lut))
    assert [(w.device, w.reason, w.group) for w in res.w_requests] == [
        ("A", "cc_nf", "g1"), ("B", "cc_nf", "g1"), ("C", "finger_quantization", None)]
    assert res.review_needed == ()                                               # pending 은 review 대상 아님
    assert res.w_invariant_ok is True


# --- review_needed (Q8 (iv)) -----------------------------------------------------------------------------------------

def test_review_needed_relaxed_diff_pair(toy_lut):
    ds = [dev("A", "h", "da", 1e-6, adj=False), dev("B", "h", "db", 1e-6, adj=False)]
    res = run_layout(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))], toy_pdk(toy_lut)),
                     new_memo(toy_lut))
    assert res.review_needed == (ReviewItem("g1", "diff_pair", "relaxed:w_not_adjustable", 1.0, 0.0),)
    g = res.groups[0]
    steps = [a.step for a in g.attempts]
    assert g.relaxed and "w_request" in steps and steps.index("w_request") < steps.index("relax")   # LY5


def test_review_needed_failed_cc_and_not_mirror(toy_lut):
    ds = [dev("E", "p", "q", 2e-6, gate="gc"), dev("F", "r", "t", 2e-6, gate="gx"),
          dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6)]
    groups = [mg("g2", ("E", "F"), "branch_symmetric", None), mg("m1", ("A", "B"), "mirror", None)]
    res = run_layout(make_input(ds, groups, [rg("r1", ("E", "F")), rg("r2", ("A", "B"))], toy_pdk(toy_lut)),
                     new_memo(toy_lut))
    assert [g.reason for g in res.groups] == ["branch_gate_differs", "no_hub_net"]
    assert res.review_needed == (ReviewItem("g2", "branch_symmetric", "branch_gate_differs", None, None),)


def test_review_needed_is_first_and_in_group_order(toy_lut):
    ds = [dev("A", "h", "da", 1e-6, adj=False), dev("B", "h", "db", 1e-6, adj=False),
          dev("E", "p", "q", 1e-6, gate="gc", adj=False), dev("F", "r", "t", 1e-6, gate="gc", adj=False)]
    groups = [mg("z2", ("E", "F"), "branch_symmetric", None), mg("a1", ("A", "B"), "diff_pair", "h")]
    res = run_layout(make_input(ds, groups, [rg("r1", ("A", "B")), rg("r2", ("E", "F"))], toy_pdk(toy_lut)),
                     new_memo(toy_lut))
    assert [(r.gid, r.reason) for r in res.review_needed] == [("a1", "relaxed:w_not_adjustable"),
                                                              ("z2", "relaxed:w_not_adjustable")]
    z = res.review_needed[1]
    assert (z.dx, z.dy) == (1.0, 0.0)                                            # 행 swap 무게중심 불일치 그대로 기록


def test_review_needed_uses_rebuild_offsets(toy_lut):
    # branch_symmetric E·F ID 3e-6 조정 불가: 키 100 nf 3 만 ok -> 행 swap 2행(E2F2 / F1E1) dx 1.0 -> relax.
    # 4.11 3 재구성 k = 3(조각 1·1·1) 은 무게중심이 덜 어긋나고(1/3) 면적이 줄면 채택 -> review_needed 의 dx·dy = GroupRebuild 값.
    ds = [dev("E", "p", "q", 3e-6, gate="gc", adj=False), dev("F", "r", "t", 3e-6, gate="gc", adj=False)]
    res = run_layout(make_input(ds, [mg("g2", ("E", "F"), "branch_symmetric", None)], [rg("r1", ("E", "F"))], toy_pdk(toy_lut)),
                     new_memo(toy_lut))
    g = res.groups[0]
    assert g.relaxed and (g.dx, g.dy) == (1.0, 0.0)
    rebuilt = res.snapshot.value("graph", "layout", "ly_rows").rebuilt_groups
    assert len(res.review_needed) == 1
    item = res.review_needed[0]
    assert len(rebuilt) == 1, "k = 3 재구성(무게중심 1/3, 면적 감소)이 채택되지 않았다"
    gr = rebuilt[0]
    assert gr.n_rows == 3
    assert (item.dx, item.dy) == (gr.dx, gr.dy)
    dx, dy = centroid_offsets([r.transistor_sequence for r in res.rows if r.group == "g2"], ("E", "F"))
    assert (dx, dy) == (Fraction(1, 3), 0)
    assert (item.dx, item.dy) == pytest.approx((float(dx), float(dy)))


# --- 재검증 요청 (Q4 (ii)(iii)) ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("with_requests", [False, True])
def test_revalidation_always_required(toy_lut, with_requests):
    if with_requests:
        inp = composite(toy_pdk(toy_lut), diode_C=True)
    else:
        ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6, diode=True)]
        inp = make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))], toy_pdk(toy_lut))
    res = run_layout(inp, new_memo(toy_lut))
    assert bool(res.w_requests) is with_requests
    rv = res.revalidation
    assert isinstance(rv, Revalidation)
    assert rv.required is True
    assert rv.status == REVALIDATION_PENDING == "pending_wiring"
    assert rv.seals == REVALIDATION_SEALS
    assert (rv.consumer, rv.reason) == (REVALIDATION_CONSUMER, REVALIDATION_PENDING_REASON)
    by_in = {d.name: d for d in inp.devices}
    by_out = {d.name: d for d in res.devices}
    assert [r.name for r in rv.devices] == [d.name for d in inp.devices if by_out[d.name].n_fingers is not None]
    for r in rv.devices:
        assert isinstance(r, RealizedDevice)
        d, o = by_in[r.name], by_out[r.name]
        assert (r.kind, r.ID_A, r.gm_id, r.L_m, r.vds_V, r.vsb_V) == (d.kind, d.ID_A, d.gm_id, d.L_m, d.vds_V, d.vsb_V)
        assert (r.finger_w_m, r.n_fingers, r.W_need_m, r.W_realized_m) == (o.finger_w_m, o.n_fingers, o.W_need_m, o.W_realized_m)
        assert r.finger_w_key == round(o.finger_w_m / 1e-8)
        assert r.recalibrate_id is (not d.diode)                                 # diode 는 ID 재보정 불필요
        assert r.recompute_node_voltages is True                                 # diode 도 노드전압·봉인은 다시
    assert any(not r.recalibrate_id for r in rv.devices)


# --- M3a 회귀 (toy) ----------------------------------------------------------------------------------------------------

def test_m3a_regression_toy(toy_lut):
    # 옛 규칙(err 대 W_m)이면 W_m 4e-6 에 정확히 맞는 키 200 nf 2(err 0)가 뽑힌다. 새 규칙은 W_need(= ID/J = 0.75e-6) 대비라
    # 그 후보는 존재하지 않고, 실현 W 는 W_need 쪽(1e-6, 키 100 nf 1)이며 허용오차 밖이라 요청이 난다.
    res = run_layout(make_input([dev("M3a", "x", "y", 0.75e-6, W=4e-6)], [], [rg("r", ("M3a",))], toy_pdk(toy_lut)),
                     new_memo(toy_lut))
    d = res.devices[0]
    assert (d.finger_w_m, d.n_fingers) != (pytest.approx(2e-6), 2)
    assert d.W_realized_m == pytest.approx(1e-6)
    assert d.W_err_rel == pytest.approx(1 / 3, rel=1e-9)
    assert d.W_err_rel > d.W_tol_effective
    assert [(w.device, w.reason) for w in res.w_requests] == [("M3a", "finger_quantization")]


# --- 캐시 (4.13 10, L11) ----------------------------------------------------------------------------------------------

def _misses(memo):
    return {r: s.misses for r, s in memo.stats()}


def _reset_blocks():
    for b in (finger_candidates, pattern_select, finger_geometry, compose_rows):
        b.reset_stats()


def _assert_no_same_input_recompute():
    for b in (finger_candidates, pattern_select, finger_geometry, compose_rows):
        assert b.stats().recomputes_same_input == 0, b.name


def test_previous_same_input_computes_nothing(toy_lut):
    _reset_blocks()
    memo = new_memo(toy_lut)
    inp = composite(toy_pdk(toy_lut))
    r1 = run_layout(inp, memo)
    m1 = _misses(memo)
    r2 = run_layout(inp, memo, previous=r1)
    assert r2.computed_blocks == ()
    assert strip_volatile(r2) == strip_volatile(r1)
    assert _misses(memo) == m1                                                   # LUT 조회 재계산 0
    _assert_no_same_input_recompute()


def test_rejected_only_change_reuses_slices_and_candidates(toy_lut):
    _reset_blocks()
    memo = new_memo(toy_lut)
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6)]
    g, r = [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B"))]
    r1 = run_layout(make_input(ds, g, r, toy_pdk(toy_lut)), memo)
    m1 = _misses(memo)
    r2 = run_layout(make_input(ds, g, r, toy_pdk(toy_lut), rejected=("A",)), memo, previous=r1)
    assert "ly_slice_density" not in r2.computed_blocks
    assert "ly_finger_candidates" not in r2.computed_blocks
    assert "ly_pattern_select" in r2.computed_blocks
    assert _misses(memo) == m1
    assert r2.groups[0].reason == "relaxed:w_request_rejected"
    _assert_no_same_input_recompute()


def test_id_change_recomputes_from_slices(toy_lut):
    memo = new_memo(toy_lut)
    inp1 = composite(toy_pdk(toy_lut))
    r1 = run_layout(inp1, memo)
    devs = tuple(dataclasses.replace(d, ID_A=1.5e-6) if d.name == "D" else d for d in inp1.devices)
    r2 = run_layout(dataclasses.replace(inp1, devices=devs), memo, previous=r1)
    assert r2.computed_blocks[:1] == ("ly_slice_density",)
    assert "ly_finger_candidates" in r2.computed_blocks
    assert list(r2.computed_blocks) == [w for w in ALL_WRITERS if w in r2.computed_blocks]


def test_reference_w_change_does_not_recompute_slices(toy_lut):
    # 슬라이스 키 = 보존량(kind, L, ID, gm/ID, vds, vsb) -- 참고 W_m 은 키가 아니다
    memo = new_memo(toy_lut)
    inp1 = composite(toy_pdk(toy_lut))
    r1 = run_layout(inp1, memo)
    m1 = _misses(memo)
    devs = tuple(dataclasses.replace(d, W_m=7e-6) for d in inp1.devices)
    r2 = run_layout(dataclasses.replace(inp1, devices=devs), memo, previous=r1)
    assert "ly_slice_density" not in r2.computed_blocks
    assert _misses(memo) == m1
    assert all(d.W_m == 7e-6 for d in r2.devices)


def test_lut_fingerprint_is_part_of_slice_key(toy_lut, tmp_path):
    other = build_toy_lut(tmp_path / "other", id_scale=2.0)
    r1 = run_layout(composite(toy_pdk(toy_lut)), new_memo(toy_lut))
    r2 = run_layout(composite(toy_pdk(other)), new_memo(other), previous=r1)
    assert r2.computed_blocks[:1] == ("ly_slice_density",)
    # 슬라이스 ID 2배 -> J 2배 -> W_need 절반
    a1 = [d for d in r1.devices if d.name == "A"][0]
    a2 = [d for d in r2.devices if d.name == "A"][0]
    assert a2.W_need_m == pytest.approx(a1.W_need_m / 2, rel=1e-9)


def test_identical_preserved_quantities_computed_once(toy_lut, monkeypatch):
    calls = Counter()
    real = run_mod.slice_density

    def spy(memo, device, keys):
        calls[(device.kind, device.L_m, device.ID_A, device.gm_id, device.vds_V, device.vsb_V, tuple(keys))] += 1
        return real(memo, device, keys)

    monkeypatch.setattr(run_mod, "slice_density", spy)
    ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("Q", "q1", "q2", 2e-6, W=9e-6)]
    run_layout(make_input(ds, [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B", "Q"))], toy_pdk(toy_lut)),
               new_memo(toy_lut))
    assert sum(calls.values()) > 0, "계측이 걸리지 않았다"
    assert set(calls.values()) == {1}, dict(calls)


# --- 결정론 (4.13 9) --------------------------------------------------------------------------------------------------

DET_CODE = r'''
import tempfile, dataclasses
from conftest import build_toy_lut, new_memo, toy_pdk, dev, make_input, mg, rg, strip_volatile
from gmid_engine.layout import run_layout
lut = build_toy_lut(tempfile.mkdtemp())
pdk = toy_pdk(lut, overhead=0.05e-6, gap=0.1e-6, dummy=0.2e-6, tap=0.3e-6, well=1e-6)
ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("E", "p", "q", 16e-6, gate="gc"),
      dev("F", "r", "t", 16e-6, gate="gc"), dev("C", "x", "y", 1e-6), dev("D", "y", "z", 1e-6), dev("G", "y", "w", 1e-6),
      dev("H", "k", "m", 12e-6), dev("P", "vdd", "o", 2e-6, kind="nmos", body="sub2")]
groups = [mg("g1", ("A", "B"), "diff_pair", "h"), mg("g2", ("E", "F"), "branch_symmetric", None),
          mg("g3", ("C", "G"), "bias_distribution", "y")]
rgs = [rg("r1", ("A", "B")), rg("r2", ("E", "F")), rg("r", ("C", "D")), rg("r4", ("G", "H")), rg("rp", ("P",), body="sub2")]
res = run_layout(make_input(ds, groups, rgs, pdk), new_memo(lut))
RESULT = repr(strip_volatile(res))
'''


def test_determinism_across_hash_seeds(seed_runner):
    outs = {seed: seed_runner(DET_CODE, seed) for seed in (1, 2, 3)}
    assert len(set(outs.values())) == 1


# --- 실 LUT M3a 회귀 (CONTRACT 4.18 -- 계약 수치는 참고, 기대값은 npz 독립 계산) ----------------------------------------

import bisect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

_SKILL = Path(__file__).resolve().parents[3]
REAL_MANIFEST = os.environ.get("GMID_LUT_MANIFEST", r"C:\Users\HSLEE\Documents\Todoc\fpga\wt\_drafts\engine\lut_slices\manifest.json")
REAL_CAP = os.environ.get("GMID_LUT_CAP_NPZ", str(_SKILL / "assets" / "sky130_nfet_pfet_lut_sample.npz"))
REAL_TLEF = os.environ.get("GMID_PDK_TLEF", r"C:/pdk/sky130_fd_sc_hd/tech/sky130_fd_sc_hd.tlef")
REAL_KEYS = (600, 1000)          # 실행 시간(슬라이스당 tol_V 표 15~24 s) 때문에 4.18 의 두 후보 키만 PDK 폭 키로 준다
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


def _real_slices(manifest, grid):
    base = Path(manifest).parent
    out = {}
    for s in json.loads(Path(manifest).read_text(encoding="utf-8"))["slices"]:
        if s["device"] != "nfet_01v8":
            continue
        with np.load(base / s["file"]) as z:
            arr = {k: np.array(z[k]) for k in ("W", "L", "VGS", "VDS", "VS", "ID", "GM")}
        out[int(round(float(arr["W"]) / grid))] = arr
    return out


def _logf(a):
    return np.log(np.clip(a, a[a > 0].min(), None))


def _cell(grid, x):
    g = list(grid)
    if x == g[-1]:
        return len(g) - 2, 1.0
    i = min(max(bisect.bisect_right(g, x) - 1, 0), len(g) - 2)
    return i, (x - g[i]) / (g[i + 1] - g[i])


def _oracle_slice(arr, L, ID_A, gm_id, vds, vsb):
    """lut 계약 3·4·5절의 독립 구현(numpy): vgs 분지 해, J = ID/W(슬라이스), W_need, id_equivalent tol(at)."""
    Lg = arr["L"]
    i = int(np.argmin(np.abs(Lg - L)))
    assert abs(Lg[i] - L) <= np.spacing(Lg[i])
    lI, lG = _logf(arr["ID"])[i], _logf(arr["GM"])[i]                     # [VGS, VDS, VS]
    on = ((arr["ID"] > 0) & (arr["GM"] > 0))[i]
    VGS, VDS, VS = arr["VGS"], arr["VDS"], arr["VS"]
    k, fk = _cell(VDS, vds)
    s, fs = _cell(VS, vsb)

    def bil(x):            # x[VGS, VDS, VS] -> VGS 곡선
        return ((1 - fk) * (1 - fs) * x[:, k, s] + fk * (1 - fs) * x[:, k + 1, s]
                + (1 - fk) * fs * x[:, k, s + 1] + fk * fs * x[:, k + 1, s + 1])
    g = np.exp(bil(lG) - bil(lI))
    p = int(np.argmax(g))
    d = g - gm_id
    cand = [j for j in range(p, len(g) - 1) if d[j] * d[j + 1] <= 0.0]
    assert cand, "독립 계산: 강반전 분지 해 없음"
    j = cand[-1]
    ga, gb, va, vb = g[j], g[j + 1], VGS[j], VGS[j + 1]
    x0, x1, y0, y1 = (ga, gb, va, vb) if ga <= gb else (gb, ga, vb, va)
    vgs = vb if x1 == x0 else (y1 - y0) / (x1 - x0) * (gm_id - x0) + y0
    gi, fg = _cell(VGS, vgs)
    curve_lo, curve_hi = bil(lI)[gi], bil(lI)[gi + 1]
    ID_slice = float(np.exp((1 - fg) * curve_lo + fg * curve_hi))
    J = ID_slice / float(arr["W"])
    # id_equivalent: 셀 (i, kk) 의 모든 g·s·축 LOO 최댓값, at = 칸 kk·kk+1 중 정의된 값 최댓값
    kk = min(bisect.bisect_right(list(VDS), vds) - 1, len(VDS) - 2)
    gmid_pt = np.exp(lG - lI)
    vals = []
    for kc in (kk, kk + 1):
        best = None
        # VGS 축
        for a_axis, grid_ax in ((0, VGS), (1, VDS), (2, VS)):
            n = len(grid_ax)
            for m in range(1, n - 1):
                if a_axis == 1 and m != kc:
                    continue
                t = (grid_ax[m] - grid_ax[m - 1]) / (grid_ax[m + 1] - grid_ax[m - 1])
                if a_axis == 0:
                    lo, mid, hi = lI[m - 1, kc, :], lI[m, kc, :], lI[m + 1, kc, :]
                    ok = on[m - 1, kc, :] & on[m, kc, :] & on[m + 1, kc, :]
                    gm_ = gmid_pt[m, kc, :]
                elif a_axis == 1:
                    lo, mid, hi = lI[:, m - 1, :], lI[:, m, :], lI[:, m + 1, :]
                    ok = on[:, m - 1, :] & on[:, m, :] & on[:, m + 1, :]
                    gm_ = gmid_pt[:, m, :]
                else:
                    lo, mid, hi = lI[:, kc, m - 1], lI[:, kc, m], lI[:, kc, m + 1]
                    ok = on[:, kc, m - 1] & on[:, kc, m] & on[:, kc, m + 1]
                    gm_ = gmid_pt[:, kc, m]
                if not ok.any():
                    continue
                e = (np.abs(lo + t * (hi - lo) - mid) / gm_)[ok]
                v = float(e.max())
                best = v if best is None else max(best, v)
        if best is not None:
            vals.append(best)
    tol = max(vals) if vals else None
    return {"vgs": vgs, "J": J, "W_need": ID_A / J, "tol": tol}


def _oracle_geometry(devs, slices, grid):
    """4.4 후보 + 4.7 비그룹 행 그룹 규칙(독립 구현). 반환 {이름: (키, nf, W_need, err, effective, ok)}."""
    cands = {}
    for name, L, ID, gm, vds, vsb, _W in devs:
        out = []
        for key in REAL_KEYS:
            o = _oracle_slice(slices[key], L, ID, gm, vds, vsb)
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
            nfsum = sum(min((c for c in cands[n] if c[0] == key), key=lambda c: (c[3], c[1]))[1] for n in okd)
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
    """4.18 M3a: 옛 규칙(err 대 참고 W_m)의 키 1000 nf 1(M3a 43 %)은, M4a·M4b 에게 키 1000 이 ok 가 아니게 된 새 규칙에서 선택되지 않는다.

    기대값은 npz 를 numpy 로 직접 읽은 독립 계산(_oracle_*)이고 계약의 수치(17.1 %·1.4 %)는 참고만 한다.
    """
    from gmid_engine.lut import LutSpec, load_lut_set
    grid = _grid(_need(REAL_TLEF, "PDK tlef"))
    slices = _real_slices(_need(REAL_MANIFEST, "폭 슬라이스 manifest"), grid)
    widths_by_kind = {"nmos": min(float(a["W"]) for a in slices.values())}
    pf = [float(np.load(Path(REAL_MANIFEST).parent / s["file"])["W"]) for s in
          json.loads(Path(REAL_MANIFEST).read_text(encoding="utf-8"))["slices"] if s["device"] == "pfet_01v8"]
    spec = LutSpec(grid, (("nmos", widths_by_kind["nmos"]), ("pmos", min(pf))),
                   (("nfet_01v8", "nmos"), ("pfet_01v8", "pmos")), (("nmos", "_n"), ("pmos", "_p")))
    lut = load_lut_set(REAL_MANIFEST, _need(REAL_CAP, "기준 LUT"), spec)
    full = toy_pdk(lut)
    from gmid_engine.layout import LayoutPdk
    pdk = LayoutPdk(full.manufacturing_grid_m, (("nmos", REAL_KEYS),), 0.0, 0.0, 0.0, 0.0, 0.0, full.rule_ids, lut.fp)
    ds = [dev(n, "s_" + n, "d_" + n, ID, L=L, gm_id=gm, vds=vds, vsb=vsb, W=W) for n, L, ID, gm, vds, vsb, W in PILOT]
    res = run_layout(make_input(ds, [], [rg("rp", [d.name for d in ds])], pdk), new_memo(lut))
    chosen, cands = _oracle_geometry(PILOT, slices, grid)
    by = {d.name: d for d in res.devices}
    for name, (key, nf, W_need, err, eff, ok) in chosen.items():
        d = by[name]
        assert d.W_need_m == pytest.approx(W_need, rel=1e-6), name
        assert (round(d.finger_w_m / grid), d.n_fingers) == (key, nf), name
        assert d.W_err_rel == pytest.approx(err, rel=1e-6, abs=1e-12), name
        assert d.W_tol_effective == pytest.approx(eff, rel=1e-6), name
    # 회귀 전제(독립 계산): M4a·M4b 는 키 1000 에서 ok 가 아니다
    for n in ("M4a", "M4b"):
        assert not any(c[0] == 1000 and c[5] for c in cands[n]), "전제 불성립: %s 키 1000 이 ok" % n
    # 옛 규칙 후보(키 1000 nf 1, 대 W_m 오차 43 %)는 선택되지 않는다
    old_err = abs(1000 * grid - 3.495e-6) / 3.495e-6
    assert old_err == pytest.approx(0.431, abs=1e-3)
    m3a = by["M3a"]
    assert (round(m3a.finger_w_m / grid), m3a.n_fingers) != (1000, 1)
    assert m3a.W_err_rel == pytest.approx(abs(m3a.W_realized_m - m3a.W_need_m) / m3a.W_need_m, rel=1e-12)
    assert res.revalidation.required is True
