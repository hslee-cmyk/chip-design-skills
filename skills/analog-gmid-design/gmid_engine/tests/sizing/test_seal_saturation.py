"""봉인 7 `dc_seal_saturation(snapshot, linear_devices)` -- CONTRACT 6절·12절 O1: LUT 에 VDSAT 열이 없어 항상 undefined
(reason lut_vdsat_column_missing), devices = current > 0 이고 linear_devices 밖인 MOS, n_checked = 그 수.
그래서 SealedSnapshot 은 나오지 않는다(음성 확인은 test_seal·test_size_and_seal)."""
import dataclasses

import pytest

from gmid_engine.sizing import dc_seal_saturation

from .conftest import seal_item, tamper, theta_a, theta_c, with_tol


def run(snap, lin=()):
    return seal_item(dc_seal_saturation(snap, tuple(lin)), 7)


@pytest.mark.parametrize("which", ["C", "A"])
def test_always_undefined(ctx_c, ctx_a, which):
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    item = run(snap)
    mos = tuple(sorted(dict(snap.column("device", "dc_op"))))
    assert item.item == 7 and item.status == "undefined"
    assert item.devices == mos
    d = dict(item.detail)
    assert d["reason"] == "lut_vdsat_column_missing"
    assert d["n_checked"] == len(mos)
    assert item.margin is None


def test_linear_devices_excluded(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap, ("M1",))
    assert item.status == "undefined" and item.devices == ("M2",)
    assert dict(item.detail)["n_checked"] == 1


def test_all_linear_still_undefined_not_sealed(ctx_c):
    """판정할 소자가 0개여도 VDSAT 열이 없다는 사실은 그대로(항상 undefined -- 계약 6절 표)."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap, ("M1", "M2"))
    assert item.status == "undefined"
    assert item.devices == () and dict(item.detail)["n_checked"] == 0


def test_zero_current_device_excluded(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_currents", "device", "dc_current", {"M2": 0.0})
    op = dict(snap.column("device", "dc_op"))["M2"]
    s2 = tamper(s2, "dc_widths", "device", "dc_op", {"M2": dataclasses.replace(op, current=0.0)})
    item = run(s2)
    assert item.devices == ("M1",)
