"""CONTRACT 4.4 `finger_candidates`(@compute_block) -- device `ly_fw_cand`.

슬라이스(`ly_slices`, reason == "" 만)마다 nf ∈ {max(1, floor(W_need/fw)), max(1, ceil(W_need/fw))}, err = |nf fw − W_need| / W_need,
ok = err <= effective(w_tolerance). 기대값은 스냅샷에 쓴 슬라이스 값에서 독립 계산한다. M3a 회귀(옛 err = |nf fw − W_m| / W_m)를
toy 로 재현: 참고 W_m 에 정확히 맞는 후보가 아니라 W_need 기준 후보만 나와야 한다.
"""
from __future__ import annotations

import math

import pytest

from gmid_engine.layout.contract_output import FingerCandidate
from gmid_engine.layout.finger_candidates import finger_candidates

from .conftest import block_row, dev, device_column, fresh_run, make_input, new_memo, rg, staged_snapshot, toy_pdk

FW = {100: 1e-6, 200: 2e-6}


def _expected(sl, gm_id, grid=1e-8):
    out = []
    for s in sl:
        if s.reason != "":
            continue
        fw = s.finger_w_m
        q = s.W_need_m / fw
        for nf in sorted({max(1, math.floor(q)), max(1, math.ceil(q))}):
            err = abs(nf * fw - s.W_need_m) / s.W_need_m
            upper = s.tol_v_V * gm_id
            lower = grid / (2 * fw)
            eff = max(upper, lower)
            out.append((s.finger_w_key, nf, err, lower, upper, eff, lower > upper, err <= eff))
    return out


def _run(toy_lut, devices, rgs=None, run=None):
    """[XRUN-F1 card B C4] run = 실행 두 객체 키워드(dict), 없으면 새 실행 하나."""
    memo = new_memo(toy_lut)
    inp = make_input(devices, [], rgs or [rg("r", [d.name for d in devices])], toy_pdk(toy_lut))
    snap = staged_snapshot(inp, memo)
    return snap, finger_candidates(snap, **(run if run is not None else fresh_run()))


def test_candidates_match_independent_rule(toy_lut):
    devs = [dev("C", "x", "y", 0.75e-6), dev("A", "h", "da", 2e-6), dev("H", "k", "m", 12e-6), dev("P", "u", "v", 1.5e-6)]
    snap0, snap = _run(toy_lut, devs)
    slices = device_column(snap0, "ly_slices")
    cand = device_column(snap, "ly_fw_cand")
    for d in devs:
        got = cand[d.name]
        assert isinstance(got, tuple)
        exp = _expected(slices[d.name], d.gm_id)
        assert len(got) == len(exp), d.name
        for c, (key, nf, err, lower, upper, eff, gdom, ok) in zip(got, exp):
            assert isinstance(c, FingerCandidate)
            assert (c.finger_w_key, c.n_fingers) == (key, nf)
            assert c.finger_w_m == pytest.approx(FW[key], rel=1e-12)
            assert c.W_realized_m == pytest.approx(nf * FW[key], rel=1e-12)
            assert c.W_need_m == pytest.approx(slices[d.name][[100, 200].index(key)].W_need_m, rel=1e-12)
            assert c.err_rel == pytest.approx(err, rel=1e-9, abs=1e-12)
            assert c.lower == pytest.approx(lower, rel=1e-12)
            assert c.upper == pytest.approx(upper, abs=1e-12)
            assert c.tol_effective == pytest.approx(eff, rel=1e-12)
            assert c.grid_dominated is gdom
            assert c.ok is ok


def test_hand_oracle_device_C(toy_lut):
    # 4.15: C(ID 0.75e-6) 키 100 nf 1 err 1/3, 키 200 nf 1 err 5/3, 둘 다 ok False -- 밖 후보도 남는다
    _, snap = _run(toy_lut, [dev("C", "x", "y", 0.75e-6)])
    got = device_column(snap, "ly_fw_cand")["C"]
    assert [(c.finger_w_key, c.n_fingers) for c in got] == [(100, 1), (200, 1)]
    assert got[0].err_rel == pytest.approx(1 / 3, rel=1e-9)
    assert got[1].err_rel == pytest.approx(5 / 3, rel=1e-9)
    assert [c.ok for c in got] == [False, False]
    assert got[0].tol_effective == pytest.approx(0.005) and got[1].tol_effective == pytest.approx(0.0025)
    assert all(c.grid_dominated for c in got)


def test_m3a_regression_err_is_against_w_need_not_reference_w(toy_lut):
    # 옛 규칙: err = |nf fw − W_m| / W_m. W_m 4e-6 이면 키 200 nf 2(=4e-6)가 err 0 으로 '통과'했다.
    # 새 규칙: W_need = ID/J = 0.75e-6 기준 -> 키 200 의 nf 집합은 {1} 뿐, err 5/3, ok False.
    _, snap = _run(toy_lut, [dev("C", "x", "y", 0.75e-6, W=4e-6)])
    got = device_column(snap, "ly_fw_cand")["C"]
    assert (200, 2) not in [(c.finger_w_key, c.n_fingers) for c in got]
    assert not any(c.ok for c in got)
    for c in got:
        assert c.err_rel == pytest.approx(abs(c.W_realized_m - c.W_need_m) / c.W_need_m, rel=1e-12)
        assert c.err_rel != pytest.approx(abs(c.W_realized_m - 4e-6) / 4e-6)


def test_excluded_slices_skipped_and_empty_tuple(toy_lut):
    devs = [dev("Z", "a", "b", 2e-6, gm_id=25.0), dev("Y", "c", "e", 2e-6)]
    _, snap = _run(toy_lut, devs)
    cand = device_column(snap, "ly_fw_cand")
    assert cand["Z"] == ()                                   # 사용 가능 슬라이스 없음 -> 빈 tuple
    # W_need 은 부동소수로 2e-6 를 몇 ulp 넘을 수 있어 ceil 후보(nf+1)가 더 나올 수 있다 -- ok 인 것만 본다
    assert [(c.finger_w_key, c.n_fingers) for c in cand["Y"] if c.ok] == [(100, 2), (200, 1)]
    assert {c.finger_w_key for c in cand["Y"]} == {100, 200}


def test_same_inputs_share_tuple_object(toy_lut):
    devs = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("Q", "q1", "q2", 3e-6)]
    _, snap = _run(toy_lut, devs)
    cand = device_column(snap, "ly_fw_cand")
    assert cand["A"] is cand["B"]
    assert cand["A"] is not cand["Q"]


def test_block_reuse_counts(toy_lut):
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행 (calls, computes, reuses, recomputes_same_input)
    run = fresh_run()
    snap0, snap = _run(toy_lut, [dev("A", "h", "da", 2e-6)], run=run)
    again = finger_candidates(snap, **run)
    assert again is snap                                     # 같은 입력 -> 재사용(함수 호출 0)
    st = block_row(run["counters"], finger_candidates.name)
    assert (st[0], st[4], st[1], st[5]) == (2, 1, 1, 0)


def test_reads_declaration():
    # oracle (d): design 40 v1.11.2 §2.4.8 '세 블록 READS' 행(O-36 (3) (a)·O-39 (2)) -- `ly_finger_candidates` READS device `ly_point`(gm_id)·
    # `ly_slices`, graph `ly_pdk`. 옛 소자 통째 필드 열 읽기 없음, 참고 W 를 담은 `ly_attrs` 를 읽지 않는다.
    assert set(finger_candidates.reads) == {("device", "ly_point"), ("device", "ly_slices"), ("graph", "ly_pdk")}


def test_reference_w_not_in_input_version(toy_lut):
    # 같은 근거: W_m 은 `ly_attrs` 칸이라 이 블록의 투영 밖 -> 참고 W 만 다른 두 입력의 입력 버전이 같다(완료 조건 W-1·W-3 의 '+0' 블록 단위)
    devs = [dev("A", "h", "da", 2e-6, W=4e-6), dev("C", "x", "y", 0.75e-6, W=3e-6)]
    other = [dev("A", "h", "da", 2e-6, W=9e-6), dev("C", "x", "y", 0.75e-6, W=1e-6)]
    snaps = [staged_snapshot(make_input(ds, [], [rg("r", [d.name for d in ds])], toy_pdk(toy_lut)), new_memo(toy_lut))
             for ds in (devs, other)]
    assert finger_candidates.input_version(snaps[0]) == finger_candidates.input_version(snaps[1])
