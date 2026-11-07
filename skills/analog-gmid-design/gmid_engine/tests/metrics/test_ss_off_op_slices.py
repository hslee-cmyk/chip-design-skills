"""WB-1 O-1 (interface card 20261104-wb1 §7): off 소자 폭 = 슬라이스 키 (T-O3c~g, T-O5', T-O7).

oracle (손/식): off 소자 ΔI_off = IDu(0, vds, 0)·w_m/l_m, r4 닫힌 식 IDu = I0·exp(LAM·VDS) (VGS = 0, VSB = 0) -- `off_cases.i_off_at_vgs0_vsb0`
(해석식 helper; 피검 함수 아님). 슬라이스 키 = round(w_m / 격자). 정지 순서(g2): off_vgs_negative -> off_bulk_forward -> slice_missing ->
off_outside_lut; 위 행에서 끝나면 `slice_of_finger`·`lut_axis_bounds` 호출 0 (관찰 지점 §9: `sys.modules["gmid_engine.metrics.ss_off_op"]`).
호출 0 단언마다 같은 test 에서 양성 대조(호출 >= 1)를 둔다.
합성 LUT = sizing/wb1_toy.write_r4_bins_lut (슬라이스 폭 여럿 + bin 선언). 기존 fixture 이행은 이번 범위가 아니다 -- 이 파일이 자기 builder 를 쓴다.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from gmid_engine.authoring import load_sizing_spec, load_topology
from gmid_engine.core import SealViolationError
from gmid_engine.graph import build_s1
from gmid_engine.metrics import metric_catalog, ss_evaluate
from gmid_engine.sizing import build_kernel_context, dc_inputs_from_spec
from fs1_wf import size_and_seal      # [FS-1 서명 맞춤] 손 wf 를 끼운 래퍼

from sizing.wb1_toy import access_of, write_r4_bins_lut

from .conftest import fresh_run, rel_close, spec_json, toy_junction
from .off_cases import BASE_RAILS, CONS, circuit_a, graph_field, i_off_at_vgs0_vsb0, off_entry, theta_a

GRID = 1e-8
WIDTHS = (1e-6, 2e-6, 5e-6)                     # 기준 폭 1e-6 (cap w_ref_m) 포함, 슬라이스 키 100·200·500


def build(tmp, pins, rails, w_m, l_m=1e-6, widths=WIDTHS, name="wb1o", jc1_cols=True):
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    sup = dict(BASE_RAILS)
    sup.update(rails)
    doc = circuit_a(list(pins), name=name, rails=tuple(sorted(rails)))
    tp = tmp / (name + ".topology.json")
    tp.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    td = load_topology(str(tp))
    raw = spec_json(td, sup, (("R1", "resistor", None), ("CL", "capacitor", 1e-12)), (), CONS)
    raw["human"]["intended_region"] = {p[0]: off_entry(w_m, l_m) for p in pins}
    sp = tmp / (name + ".sizing_spec.json")
    sp.write_text(json.dumps(raw, indent=1), encoding="utf-8")
    spec = load_sizing_spec(str(sp), td, metric_catalog())
    inputs = dc_inputs_from_spec(spec)
    run = fresh_run()
    lut, _, _ = write_r4_bins_lut(tmp / "lut", widths=widths, jc1_cols=jc1_cols)     # [JC-1] 접합 항 입력 열(CGS·CDD·CSS)
    ctx = build_kernel_context(build_s1(td, dict(inputs.supplies_v), **run), inputs, access_of(lut), **run)
    theta = theta_a(ctx)
    ev = size_and_seal(ctx, theta)
    return SimpleNamespace(spec=spec, ctx=ctx, theta=theta, sealed=ev.sealed, rails=sup,
                           js=toy_junction(tmp / "junction", ctx.lut.memo.lut))


def evaluate(case):
    ac = tuple(sorted(n for n in case.rails if n != "gnd"))
    return ss_evaluate(case.sealed, case.ctx, case.theta, case.spec.constraints, ac, junction=case.js)


def stop_reason(case):
    with pytest.raises(SealViolationError) as ei:
        evaluate(case)
    return dict(ei.value.record.detail)["reason"], ei.value.record.devices, dict(ei.value.record.detail)


class Count:
    def __init__(self, orig):
        self.orig, self.n = orig, 0

    def __call__(self, *a, **k):
        self.n += 1
        return self.orig(*a, **k)


def counted(monkeypatch, name):
    mod = sys.modules["gmid_engine.metrics.ss_off_op"]
    c = Count(getattr(mod, name))                       # 관찰 지점이 없으면 AttributeError (red)
    monkeypatch.setattr(mod, name, c)
    return c


GOOD_PIN = ("Mx", "nmos", "vz", "gnd", "gnd", "gnd")    # vgs = 0, vds = 0 (vz = 0 V), vsb = 0: 정지 없음
GOOD_RAILS = {"vz": 0.0}


def test_slice_off_t_o3c_w_key_is_slice_key_and_delta_uses_w_m(tmp_path):
    case = build(tmp_path, [GOOD_PIN], GOOD_RAILS, w_m=5e-6)
    snap = evaluate(case).snapshot
    assert snap.value("device", "Mx", "off_op").w_key == 500                       # round(5e-6 / 1e-8)
    dI = dict(graph_field(snap, "ss_off_delta").sources)["Mx"]
    assert rel_close(dI, i_off_at_vgs0_vsb0("nmos", 0.0, 5e-6, 1e-6), 1e-9)        # ΔI_off 의 W = w_m = 5e-6


def test_slice_off_t_o3d_non_slice_width_is_slice_missing(tmp_path):
    case = build(tmp_path, [GOOD_PIN], GOOD_RAILS, w_m=4e-6)
    reason, devices, d = stop_reason(case)
    assert reason == "slice_missing" and devices == ("Mx",)
    from .conftest import block_row
    assert block_row(case.ctx.counters, "ss_off_delta")[0] == 0                    # ΔI 호출 0
    ok = build(tmp_path / "ok", [GOOD_PIN], GOOD_RAILS, w_m=5e-6, name="wb1o_ok")  # 양성 대조: 슬라이스 폭이면 ΔI 가 불린다
    evaluate(ok)
    assert block_row(ok.ctx.counters, "ss_off_delta")[0] >= 1


def test_slice_off_t_o3e_vgs_negative_precedes_slice_check(tmp_path, monkeypatch):
    pin = ("Mx", "nmos", "vdd", "gnd", "vh", "gnd")                                  # vgs = 0 - 0.5 < 0
    c = counted(monkeypatch, "slice_of_finger")
    reason, devices, _ = stop_reason(build(tmp_path, [pin], {"vh": 0.5}, w_m=4e-6))
    assert reason == "off_vgs_negative" and devices == ("Mx",)
    assert c.n == 0
    evaluate(build(tmp_path / "ok", [GOOD_PIN], GOOD_RAILS, w_m=5e-6, name="wb1o_ok"))
    assert c.n >= 1                                                                  # 양성 대조: 호출 경로가 살아 있다


def test_slice_off_t_o3f_bulk_forward_precedes_slice_check(tmp_path, monkeypatch):
    pin = ("Mx", "nmos", "vh", "gnd", "gnd", "vdd")                                  # vgs 0, vsb = -1.8 -> 벌크 순방향
    c = counted(monkeypatch, "slice_of_finger")
    reason, devices, _ = stop_reason(build(tmp_path, [pin], {"vh": 0.5}, w_m=4e-6))
    assert reason == "off_bulk_forward" and devices == ("Mx",)
    assert c.n == 0
    evaluate(build(tmp_path / "ok", [GOOD_PIN], GOOD_RAILS, w_m=5e-6, name="wb1o_ok"))
    assert c.n >= 1


def test_slice_off_t_o3g_slice_check_precedes_axis_bounds(tmp_path, monkeypatch):
    pin = ("Mx", "nmos", "vz", "vg", "gnd", "gnd")                                   # vgs = 2.5 > VGS 축 끝 2.0 (순방향 아님)
    rails = {"vg": 2.5, "vz": 0.0}
    c = counted(monkeypatch, "lut_axis_bounds")
    reason, devices, _ = stop_reason(build(tmp_path, [pin], rails, w_m=4e-6))
    assert reason == "slice_missing" and devices == ("Mx",)
    assert c.n == 0
    reason2, _, _ = stop_reason(build(tmp_path / "ok", [pin], rails, w_m=5e-6, name="wb1o_ok"))
    assert reason2 == "off_outside_lut" and c.n >= 1                                 # 양성 대조: 슬라이스 폭이면 축 검사까지 간다


def test_slice_off_t_o5p_delta_and_gm_gds_double_with_width(tmp_path):
    """g4: 슬라이스 w, 2w 는 같은 IDu 열 -> w_m = w -> 2w 에서 ΔI_off 두 배 (손 W/L 환산)."""
    a = evaluate(build(tmp_path / "a", [GOOD_PIN], GOOD_RAILS, w_m=1e-6, name="wb1o_a")).snapshot
    b = evaluate(build(tmp_path / "b", [GOOD_PIN], GOOD_RAILS, w_m=2e-6, name="wb1o_b")).snapshot
    da = dict(graph_field(a, "ss_off_delta").sources)["Mx"]
    db = dict(graph_field(b, "ss_off_delta").sources)["Mx"]
    assert rel_close(da, i_off_at_vgs0_vsb0("nmos", 0.0, 1e-6, 1e-6), 1e-9)
    assert rel_close(db, 2.0 * da, 1e-9)
    assert a.value("device", "Mx", "off_op").w_key == 100 and b.value("device", "Mx", "off_op").w_key == 200


def test_slice_off_t_o7_non_reference_slice_reads_cap_columns_from_reference_table(tmp_path):
    """g3: w_m = 비기준 슬라이스(200, 기준 키 100) -> C 열은 기준 폭 표(cap_map)에서 환산, lut_column_unavailable 0."""
    snap = evaluate(build(tmp_path, [GOOD_PIN], GOOD_RAILS, w_m=2e-6)).snapshot       # 예외 없이 끝난다
    assert snap.value("device", "Mx", "off_op").w_key == 200
    assert dict(graph_field(snap, "ss_off_delta").sources)["Mx"] > 0.0
