"""봉인 7 `dc_seal_saturation(snapshot, linear_devices, lut)` -- CONTRACT r4 6절: VDSAT 열이 없는 LUT 세트(이 파일의 toy LUT)
에서는 판정 대상 소자 행이 모두 undefined(reason lut_vdsat_column_missing), devices = current > 0 이고 linear_devices 밖인 MOS,
n_checked = 그 수. [code author r4 조정: 인자 lut 추가, 판정 대상 0 개면 pass -- 열 있는 LUT 의 판정식 test 는 독립 test 작성자 몫]"""
import dataclasses

import pytest

from gmid_engine.sizing import dc_seal_saturation

from .conftest import seal_item, tamper, theta_a, theta_c, with_tol


def run(snap, lin=(), lut=None):
    return seal_item(dc_seal_saturation(snap, tuple(lin), lut), 7)


@pytest.mark.parametrize("which", ["C", "A"])
def test_always_undefined(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    item = run(snap, (), ctx.lut)
    mos = tuple(sorted(dict(snap.column("device", "dc_op"))))
    assert item.item == 7 and item.status == "undefined"
    assert item.devices == mos
    d = dict(item.detail)
    assert d["reason"] == "lut_vdsat_column_missing"
    assert d["n_checked"] == len(mos)
    assert item.margin is None


def test_linear_devices_excluded(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap, ("M1",), ctx_c[2].lut)
    assert item.status == "undefined" and item.devices == ("M2",)
    assert dict(item.detail)["n_checked"] == 1


def test_all_linear_no_rows_pass(ctx_c):
    """[r4] 판정할 소자가 0개면 행이 없어 pass(n_checked 0) -- 열 조회를 하지 않는다(계약 r4 6절 표)."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap, ("M1", "M2"), ctx_c[2].lut)
    assert item.status == "pass"
    assert item.devices == () and dict(item.detail)["n_checked"] == 0


def test_zero_current_device_excluded(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_currents", "device", "dc_current", {"M2": 0.0})
    op = dict(snap.column("device", "dc_op"))["M2"]
    s2 = tamper(s2, "dc_widths", "device", "dc_op", {"M2": dataclasses.replace(op, current=0.0)})
    item = run(s2, (), ctx_c[2].lut)
    assert item.devices == ("M1",)
