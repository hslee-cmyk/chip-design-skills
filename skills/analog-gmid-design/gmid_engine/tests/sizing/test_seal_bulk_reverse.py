"""봉인 6 `dc_seal_bulk_reverse(snapshot)` -- CONTRACT 6절: MOS 마다 max(0, −vsb, −(vds + vsb)) ≤ tol_v.

위반 회로: 회로 A 의 M1 bulk 를 out 에 선언 -> vsb = V(gnd) − V(out) < 0. toy LUT VS 축이 −0.45 를 포함해 LUT 조회는 통과하고
봉인 6 만 걸린다.
"""
import dataclasses

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import dc_seal_bulk_reverse, size_and_seal

from .conftest import (Oracle, assert_item, build_ctx, circuit_cs_res, judge_expect, rel_close, seal_item, tamper,
                       theta_a, theta_c, with_tol)


def rows_of(snap):
    ops = dict(snap.column("device", "dc_op"))
    tolv = dict(snap.column("device", "dc_tol_v"))
    return [(m, max(0.0, -ops[m].vsb, -(ops[m].vds + ops[m].vsb)), tolv[m], (m,), ()) for m in sorted(ops)]


def run(snap):
    from gmid_engine.search import open_run
    donors, counters = open_run()          # [XRUN-F1 card B C4] 블록 단독 호출 = 새 실행 하나
    return seal_item(dc_seal_bulk_reverse(snap, donors=donors, counters=counters), 6)


def test_pass_zero_magnitude(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    exp = judge_expect(rows_of(snap))
    item = run(snap)
    assert_item(item, exp, 6)
    assert item.magnitude == 0.0


@pytest.fixture
def ctx_bulk_out(tmp_path, toy_access):
    doc = circuit_cs_res(bulk_m1="out")
    doc["topology_name"] = "hand_cs_res_bulk_out"
    return build_ctx(tmp_path, doc, toy_access)[2]


def theta_bulk(vout):
    i, r = 1e-5, (1.8 - vout) / 1e-5
    return {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, vout, -vout),
            ("current", "R1"): i, ("resistance", "R1"): r}


def test_fail_hand(ctx_bulk_out):
    snap, _ = with_tol(ctx_bulk_out, theta_bulk(0.3))
    exp = judge_expect(rows_of(snap))
    assert exp["status"] == "fail" and exp["devices"] == ("M1",)
    item = run(snap)
    assert_item(item, exp, 6)
    # 손계산: vsb = 0 − 0.3 = −0.3, vds = 0.3 -> max(0, 0.3, 0) = 0.3
    assert rel_close(item.magnitude, 0.3, 1e-9)
    assert rel_close(item.margin, 0.3 / Oracle.tol_v(), 1e-9)


def test_drain_below_bulk_term(ctx_c):
    """−(vds + vsb) 항: vds = 0.1, vsb = −0.2 로 바꾼 DeviceOp -> max(0, 0.2, 0.1) = 0.2."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    op = dict(snap.column("device", "dc_op"))["M1"]
    s2 = tamper(snap, "dc_widths", "device", "dc_op", {"M1": dataclasses.replace(op, vds=0.05, vsb=0.1 - 0.2)})
    exp = judge_expect(rows_of(s2))
    assert_item(run(s2), exp, 6)
    assert rel_close(run(s2).magnitude, 0.1, 1e-9)
    s3 = tamper(snap, "dc_widths", "device", "dc_op", {"M1": dataclasses.replace(op, vds=-0.3, vsb=0.1)})
    assert rel_close(run(s3).magnitude, 0.2, 1e-9)                    # −(−0.3 + 0.1) = 0.2


def test_size_and_seal_raises_item6(ctx_bulk_out):
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx_bulk_out, theta_bulk(0.3))
    d = dict(ei.value.record.detail)
    assert d["item"] == 6
    assert ei.value.record.devices == ("M1",)
    assert rel_close(ei.value.record.margin, 0.3 / Oracle.tol_v(), 1e-9)


def test_small_forward_below_tol_now_fails(ctx_bulk_out):
    """vsb = −0.01 (순방향 0.01 < tol_v 0.018) -> fail. [EO-1 범위 4 A-49] 옛 '순방향 ≤ tol_v 통과' 전제를 지웠다 -- 봉인 6 경계는 0 V 이고
    tol_v 는 띠 기록(indistinct)에만 쓴다(card §2). 기준을 강화하는 방향."""
    snap, _ = with_tol(ctx_bulk_out, theta_bulk(0.01))
    item = run(snap)
    assert item.status == "fail" and item.devices == ("M1",)


# ---------------------------------------------------------------------------------------------------------------
# [EO-1 범위 4, interface card 20261104-eo1r4-sf1l §2 '봉인 6'] 순방향은 문턱 없이 거부, tol_V 는 띠 기록(`indistinct`)에만 쓴다.
# oracle (손): 입력 dc_op 의 (vds, vsb) 를 2진 분수로 직접 정하고 max(0, -vsb, -(vds+vsb)) 를 손으로 셈한다. tol_V 는 스냅샷의 dc_tol_v 칸(입력).
# 단언 금지: tol·margin 값. (위 test_small_reverse_within_tol_passes 는 옛 판정 '순방향 ≤ tol_V 통과'를 전제한다 -- 새 계약과 충돌, 판정자 몫.)
# ---------------------------------------------------------------------------------------------------------------

def _ops_of(snap):
    return dict(snap.column("device", "dc_op"))


def _put(snap, m1_vds, m1_vsb, m2_vds=0.5, m2_vsb=0.25):
    """M1·M2 의 dc_op (vds, vsb) 를 정해 넣는다(M2 는 기본으로 깊은 역바이어스 -- 띠·순방향 모두 아님)."""
    ops = _ops_of(snap)
    upd = {"M1": dataclasses.replace(ops["M1"], vds=m1_vds, vsb=m1_vsb),
           "M2": dataclasses.replace(ops["M2"], vds=m2_vds, vsb=m2_vsb)}
    return tamper(snap, "dc_widths", "device", "dc_op", upd)


def _tol_m1(snap):
    return dict(snap.column("device", "dc_tol_v"))["M1"]


def _pairs(value):
    return tuple((d, v) for d, v in value)


def test_region_bulk_forward_half_tol_now_fails(ctx_c):
    """순방향 크기 = tol_V/2 (< tol_V) -> fail. 옛 판정(크기 ≤ tol_V 통과)이면 pass 라 red."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    tol = _tol_m1(snap)
    assert tol > 0
    s = _put(snap, 0.5, -tol / 2)                # source-bulk 순방향 tol/2: max(0, tol/2, -(0.5 - tol/2)) = tol/2
    item = run(s)
    assert item.status == "fail" and item.devices == ("M1",)
    s2 = _put(snap, -0.25, 0.25 - tol / 2)       # drain-bulk 순방향: -(vds+vsb) = tol/2, -vsb < 0
    item2 = run(s2)
    assert item2.status == "fail" and item2.devices == ("M1",)


def test_region_bulk_forward_smallest_positive_fails_and_zero_passes(ctx_c):
    """경계 0 V 양쪽: 순방향 0 정확히 = pass, 0 바로 위(5e-324) = fail (수치 문턱 없음)."""
    import math
    snap, _ = with_tol(ctx_c[2], theta_c())
    assert run(_put(snap, 0.5, 0.0)).status == "pass"
    assert run(_put(snap, 0.5, -math.ulp(0.0))).status == "fail"
    assert run(_put(snap, -0.25, 0.25)).status == "pass"                 # vdb = 0 정확히
    assert run(_put(snap, -0.25, 0.25 - math.ulp(0.25))).status == "fail"  # vdb < 0


def test_region_bulk_reverse_half_tol_passes_with_indistinct(ctx_c):
    """역바이어스 tol_V/2 -> pass + detail indistinct = ((M1, 역바이어스 크기),) -- min(vsb, vds+vsb) = tol/2 < tol_V."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    tol = _tol_m1(snap)
    item = run(_put(snap, 0.5, tol / 2))
    assert item.status == "pass"
    assert _pairs(dict(item.detail)["indistinct"]) == (("M1", tol / 2),)
    # 띠 밖(역바이어스 0.25 >= tol_V)인 M2 는 목록에 없다(_put 의 M2 기본값).


def test_region_bulk_boundary_zero_is_pass_and_in_band(ctx_c):
    """경계 vsb = 0 및 vdb = 0 -> pass. 값 0 < tol_V 라 띠 안(indistinct)에 든다."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    for vds, vsb in ((0.5, 0.0), (-0.25, 0.25)):
        item = run(_put(snap, vds, vsb))
        assert item.status == "pass"
        assert _pairs(dict(item.detail)["indistinct"]) == (("M1", 0.0),)


def test_region_bulk_tol_none_keeps_judgment_and_marks_band_undefined(ctx_c):
    """tol_V None: 항목 6 은 판정 그대로(순방향 0 -> pass) + band_undefined, 같은 주입 스냅샷에서 봉인 2 는 undefined(보고서가 sealed 일 수 없다)."""
    from gmid_engine.search import open_run
    from gmid_engine.sizing import dc_seal_vgs_match
    snap, _ = with_tol(ctx_c[2], theta_c())
    s = tamper(snap, "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    item = run(s)
    assert item.status == "pass"
    assert tuple(dict(item.detail)["band_undefined"]) == ("M1",)
    donors, counters = open_run()
    item2 = seal_item(dc_seal_vgs_match(s, donors=donors, counters=counters), 2)
    assert item2.status == "undefined" and "M1" in item2.devices


def test_region_bulk_tol_none_does_not_hide_forward(ctx_c):
    """tol_V None 이어도 순방향 > 0 이면 fail (문턱이 없으니 띠 정의 여부와 무관)."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    s = tamper(_put(snap, 0.5, -0.25), "dc_tolerances", "device", "dc_tol_v", {"M1": None})
    item = run(s)
    assert item.status == "fail" and item.devices == ("M1",)
