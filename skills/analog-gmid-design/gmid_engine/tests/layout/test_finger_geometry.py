"""CONTRACT 4.7 `finger_geometry`(@compute_block) -- device `ly_finger`.

그룹 멤버 = 그 그룹 폭 키·nf(origin group). 나머지 = 행 그룹마다 '가장 많은 소자에게 ok 인 폭 키 -> nf 합 최소 -> 큰 키' 반복.
ok 후보 없는 소자 = (err, nf, −키) 최소 잠정 + finger_quantization 요청(그룹 요청이 있으면 None). 후보 없는 소자는 값 없음.
"""
from __future__ import annotations

import pytest

from gmid_engine.layout.contract_output import DeviceFinger, WRequest
from gmid_engine.layout.finger_geometry import finger_geometry

from .conftest import dev, device_column, make_input, mg, new_memo, rg, staged_snapshot, toy_pdk


def geometry(toy_lut, devices, groups=(), rgs=None):
    rgs = rgs or [rg("r1", [d.name for d in devices])]
    inp = make_input(devices, groups, rgs, toy_pdk(toy_lut))
    snap = staged_snapshot(inp, new_memo(toy_lut), "finger_geometry")
    return device_column(snap, "ly_finger"), device_column(snap, "ly_fw_cand")


def test_hand_oracle_C_finger_quantization(toy_lut):
    fin, cand = geometry(toy_lut, [dev("C", "x", "y", 0.75e-6)])
    c = fin["C"]
    assert isinstance(c, DeviceFinger)
    assert (c.finger_w_key, c.n_fingers, c.ok, c.origin, c.group) == (100, 1, False, "row", None)
    assert c.err_rel == pytest.approx(1 / 3, rel=1e-9)
    w = c.w_request
    assert isinstance(w, WRequest)
    assert (w.device, w.reason, w.group) == ("C", "finger_quantization", None)
    assert w.W_old_m == pytest.approx(0.75e-6, rel=1e-9) and w.W_new_m == pytest.approx(1e-6, rel=1e-12)
    # [dispute 8.4, 계획 LY3·MOD7 스키마] 요청 손가락 (nf, finger_w_m): 잠정 배치의 손가락(키 100 x 격자 1e-8 = 1e-6, nf 1)이고 W_new = nf x finger_w_m
    assert w.nf == 1 == c.n_fingers and w.finger_w_m == pytest.approx(1e-6, rel=1e-12)
    assert w.W_new_m == pytest.approx(w.nf * w.finger_w_m, rel=1e-12)
    # 잠정 후보 = 전체 후보 중 (err, nf, −키) 최소
    best = min(cand["C"], key=lambda x: (x.err_rel, x.n_fingers, -x.finger_w_key))
    assert (c.finger_w_key, c.n_fingers) == (best.finger_w_key, best.n_fingers)


def test_tie_on_count_prefers_smaller_nf_sum(toy_lut):
    # 4.15 접기 소자 H(ID 12e-6): 키 100 nf 12·키 200 nf 6 모두 ok, 소자 수 동률 -> nf 합 최소 = 키 200 nf 6
    fin, _ = geometry(toy_lut, [dev("H", "k", "m", 12e-6)])
    h = fin["H"]
    assert (h.finger_w_key, h.n_fingers, h.ok, h.w_request) == (200, 6, True, None)


def test_most_devices_key_wins(toy_lut):
    # P(ID 1e-6) 는 키 100 만 ok, Q(ID 2e-6) 는 둘 다 ok -> 키 100 이 소자 2개에 ok -> 둘 다 키 100
    fin, _ = geometry(toy_lut, [dev("P", "u", "v", 1e-6), dev("Q", "q1", "q2", 2e-6)])
    assert (fin["P"].finger_w_key, fin["P"].n_fingers) == (100, 1)
    assert (fin["Q"].finger_w_key, fin["Q"].n_fingers) == (100, 2)
    for d in fin.values():
        assert d.ok and d.origin == "row" and d.w_request is None


def test_other_row_groups_not_consulted(toy_lut):
    # 다른 행 그룹이면 Q 는 혼자 판정 -> 키 100(nf 2)·200(nf 1) 동률 -> nf 합 최소 = 키 200
    fin, _ = geometry(toy_lut, [dev("P", "u", "v", 1e-6), dev("Q", "q1", "q2", 2e-6)],
                      rgs=[rg("r1", ("P",)), rg("r2", ("Q",))])
    assert fin["P"].finger_w_key == 100
    assert (fin["Q"].finger_w_key, fin["Q"].n_fingers) == (200, 1)


def test_group_members_take_group_geometry(toy_lut):
    ds = [dev("A", "h", "da", 2e-6), dev("B", "h", "db", 2e-6), dev("Q", "q1", "q2", 2e-6)]
    fin, _ = geometry(toy_lut, ds, [mg("g1", ("A", "B"), "diff_pair", "h")])
    for n in ("A", "B"):
        assert (fin[n].finger_w_key, fin[n].n_fingers, fin[n].origin, fin[n].group) == (100, 2, "group", "g1")
    assert fin["Q"].origin == "row" and fin["Q"].group is None
    assert fin["A"].finger_w_m == fin["B"].finger_w_m                     # 같은 matching 그룹 = 같은 finger_w


def test_group_request_suppresses_device_request(toy_lut):
    # 차동쌍 ID 1e-6 조정 가능: 그룹 cc_nf 요청이 있으므로 멤버의 finger_quantization 요청은 None
    ds = [dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6)]
    fin, _ = geometry(toy_lut, ds, [mg("g1", ("A", "B"), "diff_pair", "h")])
    for n in ("A", "B"):
        assert fin[n].w_request is None


def test_device_without_candidates_has_no_value(toy_lut):
    fin, cand = geometry(toy_lut, [dev("Z", "a", "b", 2e-6, gm_id=25.0), dev("Y", "c", "e", 2e-6)])
    assert cand["Z"] == ()
    assert "Z" not in fin and "Y" in fin


def test_fields_consistent_with_candidates(toy_lut):
    ds = [dev("C", "x", "y", 0.75e-6), dev("H", "k", "m", 12e-6), dev("P", "u", "v", 1e-6)]
    fin, cand = geometry(toy_lut, ds)
    for name, f in fin.items():
        match = [c for c in cand[name] if (c.finger_w_key, c.n_fingers) == (f.finger_w_key, f.n_fingers)]
        assert len(match) == 1
        c = match[0]
        assert (f.W_need_m, f.W_realized_m, f.err_rel, f.lower, f.upper, f.tol_effective, f.grid_dominated, f.ok) == (
            c.W_need_m, c.W_realized_m, c.err_rel, c.lower, c.upper, c.tol_effective, c.grid_dominated, c.ok)
