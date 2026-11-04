"""IT-1 판정 탐침(격리 복제본 안에서만, 커밋 안 함). 결과 = 환경 변수 PROBE_OUT 파일에 케이스마다 append."""
import dataclasses
import json
import os
import traceback

from conftest import build_ctx, mos, r4_ln_idu, run_blocks, topo, two
from gmid_engine.core import SealViolationError, StructureUnresolvedError, CANDIDATE_FAILURE_CLASSES
from gmid_engine.sizing import dc_widths, size_and_seal
from gmid_engine.graph import GRAPH_KEY

OUT = os.environ["PROBE_OUT"]
P = ("input", "differential_input_p")
N = ("input", "differential_input_n")
O = ("output", "b")


def rec(case, **kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps({"case": case, **kw}, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def schema(ctx):
    from gmid_engine.sizing import KERNEL_KEY
    return ctx.base.value("graph", KERNEL_KEY, "theta_schema")


def fill(ctx, vgs=0.6, vds=0.6, vsb=0.1, y=0.5, cur=1e-5):
    kinds = dict(ctx.base.column("device", "kind"))
    th = {}
    for k, key in schema(ctx).components:
        if k == "L":
            th[(k, key)] = 1e-6
        elif k == "y":
            th[(k, key)] = y
        elif k == "current":
            th[(k, key)] = cur
        elif k == "resistance":
            th[(k, key)] = 2e4
        elif k == "ln_idu":
            th[(k, key)] = r4_ln_idu(kinds[key], vgs, vds, 0.0 if kinds[key] == "pmos" else vsb)
        else:
            th[(k, key)] = 1e-12
    return th


def plan(ctx):
    nw = dict(ctx.base.column("node", "dc_writer"))
    co = dict(ctx.base.column("device", "dc_coord"))
    return nw, co


def diff_res():
    """저항 부하 차동쌍: M1(o1, inp, t), M2(o2, inn, t), M5(t, vb, gnd), R1(vdd, o1), R2(vdd, o2)."""
    return topo("p_diffres", [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd")],
                {"inp": P, "inn": N, "o1": O, "o2": O}, passives=[two("R1", "resistor", "vdd", "o1"), two("R2", "resistor", "vdd", "o2")], bias=["vb"])


def diff_mos():
    return topo("p_diff", [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                           mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd")],
                {"inp": P, "inn": N, "o1": O, "o2": O}, bias=["vb", "pb3", "pb4"])


def eval_all(case, ctx, th):
    """봉인 전 열과 봉인 결과. KVL·KCL 잔차를 스냅샷에서 직접 잰다."""
    snap = run_blocks(ctx, th, upto="columns")
    V = dict(snap.column("node", "dc_v"))
    w = dc_widths(snap, ctx.lut, donors=ctx.donors, counters=ctx.counters)
    ops = dict(w.column("device", "dc_op"))
    cur = dict(w.column("device", "dc_drop_current")) if any(f == "dc_drop_current" for f in ["dc_drop_current"]) else {}
    rec(case, V=V, ids={m: getattr(o, "id", None) for m, o in ops.items()}, vgs={m: getattr(o, "vgs", None) for m, o in ops.items()},
        drop_current=cur, op_fields=[f.name for f in dataclasses.fields(next(iter(ops.values())))] if ops else [])
    try:
        ev = size_and_seal(ctx, th)
        rec(case + ":seal", result="PASS", ev=type(ev).__name__)
    except BaseException as exc:
        rec(case + ":seal", result=type(exc).__name__, detail=str(getattr(getattr(exc, "record", None), "detail", exc))[:500], devices=str(getattr(getattr(exc, "record", None), "devices", ""))[:200])


def test_p1_input_point_kvl_kcl(tmp_path, r4_access):
    ctx = build_ctx(tmp_path, diff_res(), r4_access)[2]
    nw, co = plan(ctx)
    rec("p1:plan", inp=nw["inp"], inn=nw["inn"], dep={m: c for m, c in co.items() if c.role == "dependent"}, comps=sorted(schema(ctx).components))
    eval_all("p1", ctx, fill(ctx))


def test_p2_nonrail_g_eq_s(tmp_path, r4_access):
    doc = topo("p_gs", [mos("M1", "nmos", "o", "in", "t"), mos("M5", "nmos", "t", "vb", "gnd"), mos("Mgs", "nmos", "x", "t", "t"), mos("M3", "pmos", "o", "pb", "vdd"),
                        mos("M6", "pmos", "x", "pc", "vdd")],
               {"in": ("input", "single_ended_input"), "o": O}, bias=["vb", "pb", "pc"])
    ctx = build_ctx(tmp_path, doc, r4_access)[2]
    nw, co = plan(ctx)
    rec("p2:plan", coord_gs=co["Mgs"], comps=[c for c in schema(ctx).components if c[1] == "Mgs"])
    th = fill(ctx)
    try:
        eval_all("p2", ctx, th)
    except BaseException as exc:
        rec("p2:eval", exc=type(exc).__name__, detail=str(getattr(getattr(exc, "record", None), "detail", exc))[:500], tb=traceback.format_exc()[-300:])


def test_p3_target_on_one_diff_port(tmp_path, r4_access):
    for tg in (("inn",), ("inp",), ("inp", "inn")):
        try:
            ctx = build_ctx(tmp_path / "_".join(tg), diff_mos(), r4_access, node_targets=tuple((n, 0.9) for n in tg))[2]
            nw, co = plan(ctx)
            rec("p3", target=tg, inp=nw["inp"], inn=nw["inn"], dep={m: c.relation for m, c in co.items() if c.role == "dependent"},
                y=[c for c in schema(ctx).components if c[0] == "y"])
            th = fill(ctx)
            snap = run_blocks(ctx, th, upto="columns")
            V = dict(snap.column("node", "dc_v"))
            rec("p3:V", target=tg, inp=V["inp"], inn=V["inn"], diff=V["inp"] - V["inn"])
        except BaseException as exc:
            rec("p3", target=tg, exc=type(exc).__name__, detail=str(getattr(getattr(exc, "record", None), "detail", exc))[:300])


def test_p4_target_on_tail_input_point_kvl(tmp_path, r4_access):
    ctx = build_ctx(tmp_path, diff_mos(), r4_access, node_targets=(("t", 0.3),))[2]
    nw, co = plan(ctx)
    rec("p4:plan", inp=nw["inp"], inn=nw["inn"], dep={m: c for m, c in co.items() if c.role == "dependent"}, y=[c for c in schema(ctx).components if c[0] == "y"])


def test_p5_channel_on_n_port_window(tmp_path, r4_access):
    """n 포트에만 채널이 닿는 MOS: 창이 그 VDS >= 0 제약을 받는가."""
    doc = topo("p_nchan", [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                           mos("M3", "pmos", "o1", "pb3", "vdd"), mos("M4", "pmos", "o2", "pb4", "vdd"), mos("M6", "pmos", "inn", "pb6", "vdd")],
               {"inp": P, "inn": N, "o1": O, "o2": O}, bias=["vb", "pb3", "pb4", "pb6"])
    ctx = build_ctx(tmp_path, doc, r4_access)[2]
    nw, co = plan(ctx)
    th = fill(ctx)
    snap = run_blocks(ctx, th, upto="columns")
    win = dict(snap.column("node", "dc_window"))
    V = dict(snap.column("node", "dc_v"))
    rec("p5", inp=nw["inp"], inn=nw["inn"], win_inp=win.get("inp"), has_inn="inn" in win, V_inp=V["inp"], V_inn=V["inn"])
