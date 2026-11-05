"""판정자 직접 측정(복제본 전용, 커밋 안 함): 합성 LUT 손 대조. 결과를 JSON 줄로 AUDIT_OUT 에 쓴다."""
import json
import os
from types import SimpleNamespace

import numpy as np
import pytest

from gmid_engine.lut import LutMemo, SatBound, derived, sat_threshold, sat_threshold_grid
from gmid_engine.search import iv_domain as dom  # noqa
import importlib
maux = importlib.import_module("gmid_engine.metrics.metrics_aux")
from gmid_engine.sizing import size_and_seal
from gmid_engine.sizing._helpers_dc_solve import Circuit

from lut.hcs_cases import write_lut_with_vdsat
from .conftest import (R4_GRIDS, R4_L, W_KEY, build_ctx, circuit_cs_pmos_load, new_access, r4_tol_vdsat, write_r4_lut, theta_r4c, with_tol, tamper)
from .test_seal_region import items, state, _inject, M1_OK

OUT = os.environ["AUDIT_OUT"]


def rec(name, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": name, **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def memo_of(lut):
    return LutMemo(lut, point=4096, curve=4096, root=4096)


def test_rows_1_to_5_hand(tmp_path):
    lut = write_r4_lut(tmp_path / "c")
    nocol = write_r4_lut(tmp_path / "n", vdsat=())
    two = write_r4_lut(tmp_path / "t", grids=(R4_L, (0.0, 2.0), (0.0, 2.0), (0.0, 2.0)))
    m = memo_of(lut)
    before = {k: (v.hits, v.misses) for k, v in m.stats()}
    r1 = sat_threshold(m, "nmos", W_KEY, 1e-6, 0.5, -1e-9, 0.0)
    after = {k: (v.hits, v.misses) for k, v in m.stats()}
    assert r1 == SatBound(None, None, "reverse_vds") and before == after
    r2 = sat_threshold(memo_of(nocol), "nmos", W_KEY, 1e-6, 0.5, 1.5, 0.0)
    assert r2 == SatBound(None, None, "vdsat_column_unavailable")
    r3 = sat_threshold(m, "nmos", W_KEY, 1e-6, 2.5, 1.5, 0.0)
    assert r3 == SatBound(None, None, "lut_domain")
    r4 = sat_threshold(memo_of(two), "nmos", W_KEY, 1e-6, 0.0, 0.5, 0.0)
    assert r4.tol_v is None and r4.reason is None and r4.vdsat_v == 0.0625           # 손: c0 = 0.0625, VGS 0, VS 0, iL 0
    r5 = sat_threshold(m, "nmos", W_KEY, 1e-6, 0.5, 1.5, 0.0)
    assert r5.vdsat_v == 0.25 and r5.reason is None                                 # 손: .0625 + .25*.5 + .25*.25
    assert r5.tol_v == pytest.approx(2.0 ** -10, rel=1e-9)                           # 손: c2 h^2 / 4 = .25 * 2^-6 / 4
    rec("rows_1_5", r1=r1, r2=r2, r3=r3, r4=r4, r5=r5)


def test_seal_boundary_tol_not_subtracted(tmp_path_factory, r4_access):
    """봉인 7: VDS = VDSAT 정확 pass, VDS = VDSAT - tol/2 fail, VDS = VDSAT + tol/2 pass. tol 은 기록만. 필드 값이 LUT 와 달라도 필드 기준."""
    ctx = build_ctx(tmp_path_factory.mktemp("rg"), circuit_cs_pmos_load(), r4_access)[2]
    v, t = 0.75, 0.125                                                               # 주입 값(LUT 0.25 / 2^-10 과 다르다)
    out = {}
    for name, vds in (("eq", v), ("minus_half", v - t / 2), ("plus_half", v + t / 2), ("minus_ulp", np.nextafter(v, 0.0))):
        snap = _inject(state(ctx, m1=dict(vds=float(vds)), m2=dict(vds=1.5)), M1=SatBound(v, t, None), M2=SatBound(0.25, 2.0 ** -10, None))
        i7, i9 = items(snap, ctx.lut)
        out[name] = (i7.status, i7.devices, dict(i7.detail).get("slack_v"), dict(i7.detail).get("indistinct"), i9.status)
    assert out["eq"][0] == "pass" and out["eq"][2] == 0.0
    assert out["minus_half"][0] == "fail" and out["minus_half"][2] == -t / 2
    assert out["plus_half"][0] == "pass"
    assert out["minus_ulp"][0] == "fail"
    rec("seal7_boundary", **out)


def test_seal_real_chain_field_matches_seal(tmp_path_factory, r4_access):
    """필드를 주입하지 않은 실제 사슬: dc_sat_v(실제 writer) 값 = 손 닫힌 식, 봉인이 그 값을 읽는다."""
    ctx = build_ctx(tmp_path_factory.mktemp("rg"), circuit_cs_pmos_load(), r4_access)[2]
    snap, _ = with_tol(ctx, theta_r4c())
    col = dict(snap.column("device", "dc_sat_v"))
    ops = dict(snap.column("device", "dc_op"))
    rec("real_chain", field={k: (v.vdsat_v, v.tol_v, v.reason) for k, v in col.items()}, ops={k: (o.vgs, o.vds, o.vsb, o.L) for k, o in ops.items()})
    assert set(col) == set(ops)
    for name, b in col.items():
        assert b.vdsat_v is not None and b.reason is None


def test_s13_window_rows(tmp_path_factory, r4_access):
    """S13: 시도 전압 행 여유 = VDS - vdsat(tol 없음), triode = vdsat - VDS, 값 없으면 행 집합 None. A-90 test 공백 직접 측정."""
    ctx = build_ctx(tmp_path_factory.mktemp("rg"), circuit_cs_pmos_load(), r4_access)[2]
    snap, _ = with_tol(ctx, theta_r4c())
    values = dict(snap.column("node", "dc_v"))
    ops = dict(snap.column("device", "dc_op"))
    col = dict(snap.column("device", "dc_sat_v"))
    rows = Circuit(snap, lut=ctx.lut, linear=frozenset()).region_rows(values)
    got = {r[0] + "/" + r[1]: (r[2], r[3], r[4]) for r in rows}
    for r in rows:
        assert r[4] == "sat"
    expect = sorted(ops[m].vds - col[m].vdsat_v for m in ops)
    assert sorted(r[3] for r in rows) == pytest.approx(expect, abs=1e-15)
    rows_t = Circuit(snap, lut=ctx.lut, linear=frozenset(ops)).region_rows(values)
    assert all(r[4] == "triode" for r in rows_t)
    assert sorted(-r[3] for r in rows_t) == pytest.approx(expect, abs=1e-15)
    # 필드 입구: 다른 값 주입이 그대로 반영, LUT 호출 없음
    fake = {m: SatBound(0.5, 0.125, None) for m in ops}
    rows_f = Circuit(snap, lut=ctx.lut, linear=frozenset()).region_rows(values, fake)
    assert sorted(r[3] for r in rows_f) == pytest.approx(sorted(ops[m].vds - 0.5 for m in ops), abs=1e-15)
    # 사유 -> None
    for why in ("reverse_vds", "lut_domain", "vdsat_column_unavailable"):
        assert Circuit(snap, lut=ctx.lut, linear=frozenset()).region_rows(values, {m: SatBound(None, None, why) for m in ops}) is None
    # 시도 전압: tol None 영향 없음 / 역방향 시도 전압 -> None
    a, _lo, *_rest = (None, None)
    vdd_hi = dict(values)
    m0 = sorted(ops)[0]
    rec("s13_rows", rows=got, expect=expect, tol_absent=True)


def test_s13_no_column_none(tmp_path_factory):
    lut = write_r4_lut(tmp_path_factory.mktemp("nc"), vdsat=())
    ctx = build_ctx(tmp_path_factory.mktemp("rg"), circuit_cs_pmos_load(), new_access(lut))[2]
    ev = size_and_seal(ctx, theta_r4c())
    values = dict(ev.snapshot.column("node", "dc_v"))
    assert Circuit(ev.snapshot, lut=ctx.lut, linear=frozenset()).region_rows(values) is None
    rec("s13_no_column", rows=None)


class _P:
    def __init__(self, cols):
        self.cols = cols

    def column(self, kind, name):
        return tuple(self.cols[(kind, name)].items())


def test_s12_sat_devices():
    op = SimpleNamespace(vgs=0.5, vds=1.0, vsb=0.0)
    pins = (("d", "dn"), ("g", "gn"), ("s", "sn"))
    from gmid_engine.graph import MOS_TERMINAL_NAMES
    pins = tuple(zip(MOS_TERMINAL_NAMES, ("dn", "gn", "sn")))
    cases = {"A": SatBound(0.25, 2.0 ** -10, None), "B": SatBound(None, None, "reverse_vds"), "C": SatBound(None, None, "lut_domain"),
             "D": SatBound(None, None, "vdsat_column_unavailable"), "E": SatBound(0.25, None, None)}
    names = tuple(cases)
    p = _P({("device", "kind"): {n: "nmos" for n in names}, ("device", "pins"): {n: pins for n in names},
            ("device", "dc_tol_v"): {n: 0.001 for n in names}, ("device", "dc_sat_v"): cases, ("device", "dc_op"): {n: op for n in names}})
    rows = {r.label: r for r in maux._sat_devices(p, frozenset(), lambda n: n)}
    assert rows["A"].sat_v == 0.25 and rows["A"].sat_tol_v == 2.0 ** -10
    for n in "BCD":
        assert rows[n].sat_v is None and rows[n].sat_tol_v is None
    assert rows["E"].sat_v == 0.25 and rows["E"].sat_tol_v is None
    rec("s12", **{n: (r.sat_v, r.sat_tol_v) for n, r in rows.items()})


def _domain_ctx(lut, name="M1", kind="nmos"):
    return SimpleNamespace(memo=memo_of(lut), w_keys={kind: W_KEY}, points={}, devices=(SimpleNamespace(name=name, kind=kind),))


def test_s10_domain_probe(tmp_path, monkeypatch):
    """S10: 탐침 = VDSAT 격자 올림, tol 없음. VGS 0.5 마디 VDSAT = 0.2495(격자 0.25 바로 아래), tol ~ 0.25*2^-8 = 0.000977 -> 옛 값 0.5, 새 값 0.25."""
    h = 0.125
    assert r4_tol_vdsat("nmos") == 0.25 * h * h / 4

    def vdsat_of(kind, a):
        G = np.asarray(R4_GRIDS[1])[None, :, None, None]
        return 0.2495 + 0.25 * (G - 0.5) ** 2 + 0.0 * a["ID"]

    lut = write_lut_with_vdsat(tmp_path, vdsat_of)
    m = memo_of(lut)
    assert sat_threshold(m, "nmos", W_KEY, 1e-6, 0.5, 1.5, 0.0).vdsat_v == pytest.approx(0.2495)
    tol = sat_threshold(m, "nmos", W_KEY, 1e-6, 0.5, 1.5, 0.0).tol_v
    assert tol > 0.0005                                                            # 0.2495 + tol > 0.25
    ctx = _domain_ctx(lut)
    probes = []
    real = dom._window

    def spy(c, cache, kind, L, vds):
        probes.append(vds)
        return real(c, cache, kind, L, vds)

    monkeypatch.setattr(dom, "_window", spy)
    out = dom.domain_bounds(ctx, {"M1": 1e-6}, {})
    from gmid_engine.search._helpers_curves import curve_bundle_of, QUANTITY_VDSAT
    ref = curve_bundle_of(ctx, "M1", "nmos", 1e-6)
    vals = np.asarray(ref[QUANTITY_VDSAT].values, dtype=float)
    expect = sorted({float(np.ceil(v / 0.25) * 0.25) for v in vals if v <= 2.0} | ({2.0} if (vals > 2.0).any() else set()))
    assert sorted(set(probes)) == expect
    node = np.argmin(np.abs(vals - 0.2495))
    rec("s10", tol=tol, ref_vds=ref[QUANTITY_VDSAT].vds, node_vdsat=float(vals[node]), probes=sorted(set(probes)), expect=expect, bounds=repr(out.bounds), contains_grid_025=0.25 in probes)
    assert 0.25 in probes


def test_s10_no_column(tmp_path):
    lut = write_r4_lut(tmp_path, vdsat=())
    ctx = _domain_ctx(lut)
    out = dom.domain_bounds(ctx, {"M1": 1e-6}, {})
    assert sat_threshold_grid(ctx.memo, "nmos", W_KEY) is None
    assert "M1" not in out.bounds and out.conflicts == ()
    ec = derived(ctx.memo, "edge_costs", "nmos", W_KEY)
    assert ec.vds_min_v == 0.0
    ref = derived(ctx.memo, "reference_vds", "nmos", W_KEY, 1e-6)
    from gmid_engine.lut import idu_curve
    rec("s10_no_col", bounds=repr(out.bounds), edge_vds=ec.vds_min_v, reference_vds_no_column=ref)


def test_edge_costs_equality_saturable(tmp_path):
    """포화 술어 등호: VDSAT = 0.25 = VDS 격자점이면 포화 가능. tol 합 없음."""
    def vdsat_of(kind, a):
        G = np.asarray(R4_GRIDS[1])[None, :, None, None]
        return 0.25 + 0.25 * (G - 0.0) ** 2 + 0.0 * a["ID"]

    lut = write_lut_with_vdsat(tmp_path, vdsat_of)
    ec = derived(memo_of(lut), "edge_costs", "nmos", W_KEY)
    assert ec.vds_min_v == 0.25
    rec("edge_eq", vds_min_v=ec.vds_min_v)


def test_reverse_vds_reaches_writer(tmp_path_factory, r4_access):
    """실제 writer: 노드 전압을 VDS < 0 으로 두면 dc_widths 가 사유를 쓰는가, forward_point 축 오류로 멈추는가."""
    from gmid_engine.core import SealViolationError
    from gmid_engine.search import open_run
    from gmid_engine.sizing import dc_widths
    ctx = build_ctx(tmp_path_factory.mktemp("rv"), circuit_cs_pmos_load(), r4_access)[2]
    snap, _ = with_tol(ctx, theta_r4c())
    bad = tamper(snap, "dc_columns", "node", "dc_v", {"out": -0.25}, version=snap.block_version("dc_columns"))
    donors, counters = open_run()
    try:
        out = dc_widths(bad, ctx.lut, donors=donors, counters=counters)
        rec("reverse_writer", outcome="field", field={k: (v.vdsat_v, v.reason) for k, v in out.column("device", "dc_sat_v")})
    except SealViolationError as exc:
        rec("reverse_writer", outcome="raised", detail=dict(exc.record.detail), devices=exc.record.devices)


def test_edge_equality_only_saturable(tmp_path):
    """VDSAT = max(VDS, 0.25): 포화 가능 점은 전부 등호(VDS = VDSAT). >= 면 0.25, > 면 거를 점이 없어 edge_cost_no_conducting_row."""
    def vdsat_of(kind, a):
        D = np.asarray(R4_GRIDS[2])[None, None, :, None]
        return np.maximum(D, 0.25) + 0.0 * a["ID"]
    ec = derived(memo_of(write_lut_with_vdsat(tmp_path, vdsat_of)), "edge_costs", "nmos", W_KEY)
    assert ec.vds_min_v == 0.25
    rec("edge_eq2", vds_min_v=ec.vds_min_v)
