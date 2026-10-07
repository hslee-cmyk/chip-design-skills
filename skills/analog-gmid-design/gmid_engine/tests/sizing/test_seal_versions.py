"""봉인 4 `seal_versions(snapshot, calls)` -- CONTRACT 6절: calls 의 블록마다
fp_of((이름, code_hash, Projection.from_snapshot(snapshot, reads, extras).fp)) == block_version 이고 그 블록 writes 필드의
input_version == block_version. 위반 블록 = detail `blocks`, magnitude = 위반 수, tol 0.

`calls` 형식은 계약에 없다 -- 공개 함수가 받는 ((블록, extras tuple), ...) 를 쓴다(conftest eval_calls, 보고: 모호).
기대 버전은 이 test 가 core `fp_of`·`Projection` 으로 직접 계산한다.
"""
from gmid_engine.core import Projection, fp_of
from gmid_engine.sizing import SealItem, seal_versions

from .conftest import eval_calls, tamper, theta_c


def expected_version(snap, blk, extras):
    return fp_of((blk.name, blk.code_hash, Projection.from_snapshot(snap, blk.reads, extras).fp))


def test_pass_and_independent_version_formula(ctx_c):
    snap, calls = eval_calls(ctx_c[2], theta_c())
    for blk, ex in calls:
        assert snap.block_version(blk.name) == expected_version(snap, blk, ex)
    item = seal_versions(snap, calls)
    assert isinstance(item, SealItem) and item.item == 4
    assert item.status == "pass"
    assert item.magnitude == 0 and item.tol == 0
    assert dict(item.detail)["blocks"] == ()
    assert dict(item.detail)["n_checked"] == len(calls)


def test_input_changed_after_compute_is_violation(ctx_c):
    """dc_L 를 dc_lengths 자기 버전 그대로 바꿔 넣으면 dc_L 을 읽는 하류(dc_columns·dc_widths)의 투영이 달라진다."""
    snap, calls = eval_calls(ctx_c[2], theta_c())
    bad = tamper(snap, "dc_lengths", "device", "dc_L", {"M1": 2e-6}, version=snap.block_version("dc_lengths"))
    exp = sorted(b.name for b, ex in calls if bad.block_version(b.name) != expected_version(bad, b, ex))
    assert {"dc_columns", "dc_widths"} <= set(exp)
    assert "dc_currents" not in exp
    item = seal_versions(bad, calls)
    assert item.status == "fail"
    assert tuple(dict(item.detail)["blocks"]) == tuple(exp)
    assert item.magnitude == len(exp) and item.tol == 0


def test_output_written_with_other_version_is_violation(ctx_c):
    """dc_op 를 다른 input_version 으로 다시 쓰면 block_version(dc_widths) 이 계산 버전과 다르다."""
    snap, calls = eval_calls(ctx_c[2], theta_c())
    bad = tamper(snap, "dc_widths", "device", "dc_op", {}, version="tampered")
    item = seal_versions(bad, calls)
    assert item.status == "fail"
    assert dict(item.detail)["blocks"] == ("dc_widths",)
    assert item.magnitude == 1


def test_empty_calls_pass(ctx_c):
    snap, _ = eval_calls(ctx_c[2], theta_c())
    item = seal_versions(snap, ())
    assert item.status == "pass" and dict(item.detail)["n_checked"] == 0
