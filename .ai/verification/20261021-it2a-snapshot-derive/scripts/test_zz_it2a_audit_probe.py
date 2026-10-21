"""IT-2a 감사 탐침(감사 전용, 격리 복제본에만 복사해 쓴다 -- 엔진·저장소 test 아님).

같은 파일을 base(d3bdbd39) 복제본과 head(병합본) 복제본에서 돌려 결과를 IT2A_PROBE_OUT(JSONL)에 append 한다.
기대값을 단언하지 않는다(측정만) -- 판정은 감사가 원자료를 읽어 한다.
"""
import inspect
import json
import os

import pytest

from gmid_engine import sizing as S
from gmid_engine.sizing import size_and_seal, seal_versions

from .conftest import (COUNT_FIELDS, block_row, eval_calls, resistances_of, run_of, theta_c, theta_r4c, with_hand_ss,
                       with_tol)

OUT = os.environ.get("IT2A_PROBE_OUT")
SIDE = os.environ.get("IT2A_SIDE", "?")
HAS_BASE = "base" in inspect.signature(seal_versions).parameters
EVAL13 = (S.dc_currents, S.dc_lengths, S.dc_columns, S.dc_widths, S.dc_tolerances, S.dc_seal_node_conflict,
          S.dc_seal_vgs_match, S.dc_seal_kcl, S.dc_seal_bulk_reverse, S.dc_seal_saturation, S.dc_seal_kvl_branch,
          S.dc_seal_conduction, S.dc_seal_report)


def emit(name, value):
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(json.dumps({"side": SIDE, "probe": name, "value": value}, ensure_ascii=False, sort_keys=True, default=repr) + "\n")


def sv(snap, calls, base):
    item = seal_versions(snap, calls, base) if HAS_BASE else seal_versions(snap, calls)
    return {"status": item.status, "magnitude": item.magnitude, "detail": [[k, list(v) if isinstance(v, tuple) else v] for k, v in item.detail]}


def rows(ctx):
    return {b.name: block_row(ctx.counters, b.name) for b in EVAL13}


def delta(a, b):
    return {n: dict(zip(COUNT_FIELDS, (x - y for x, y in zip(a[n], b[n])))) for n in a}


def test_probe_seal4_fixtures(ctx_c):
    ctx = ctx_c[2]
    snap, calls = eval_calls(ctx, theta_c())
    emit("seal4_clean_ctxbase", sv(snap, calls, ctx.base))
    snap_tol, _ = with_tol(ctx, theta_c())
    emit("seal4_foreign_fixture", sv(snap_tol, calls, ctx.base))
    emit("seal4_overlap_fixture", sv(snap, calls, snap))
    emit("base_writers", sorted(ctx.base.block_versions))


def test_probe_dc13_outcome(ctx_c):
    ctx = ctx_c[2]
    ev1 = size_and_seal(ctx, theta_c(y=0.45))
    before = rows(ctx)
    ev2 = size_and_seal(ctx, theta_c(y=0.45), parent=ev1)
    emit("dc13_same_theta_parent_delta", delta(rows(ctx), before))
    emit("dc13_fp_equal", [ev2.snapshot.fp == ev1.snapshot.fp, ev2.report == ev1.report])
    emit("child_writers", sorted({fv.writer for recs in ev2.snapshot.tables.values() for r in recs.values() for _n, fv in r.fields}))
    emit("item4", [ev2.report.items[3].status, [[k, list(v) if isinstance(v, tuple) else v] for k, v in ev2.report.items[3].detail]])


def test_probe_parent_foreign_field(ctx_r4c):
    ss_w = S.S2_WRITERS.writer_of("device", "ss_dev")
    e0 = size_and_seal(ctx_r4c, theta_r4c())
    parent = with_hand_ss(e0)
    child = size_and_seal(ctx_r4c, theta_r4c(v1=0.62), parent=parent)
    emit("parent_has_ss_dev", parent.snapshot.column("device", "ss_dev") != ())
    emit("child_ss_dev_rows", len(child.snapshot.column("device", "ss_dev")))
    emit("child_ss_block_version", child.snapshot.block_version(ss_w))
    emit("child_item4", child.report.items[3].status)


def test_probe_base_none(ctx_c):
    if not HAS_BASE:
        emit("base_none", "n/a base side")
        return
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    out = {}
    for label, fn in (("seal_versions_None", lambda: seal_versions(snap, calls, None)),
                      ("seal_dc_base_None", lambda: S.seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), (), base=None, **run_of(ctx))),
                      ("seal_dc_base_omitted", lambda: S.seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), (), **run_of(ctx)))):
        try:
            fn()
            out[label] = "NO_EXCEPTION"
        except Exception as e:     # 측정: 예외 타입만 기록
            out[label] = type(e).__name__ + ": " + str(e)[:120]
    emit("base_none", out)


def test_probe_extras_fail_closed(ctx_c, monkeypatch):
    if not HAS_BASE:
        emit("extras_fail_closed", "n/a base side")
        return
    import gmid_engine.sizing.seal as seal_mod
    ctx, th = ctx_c[2], theta_c()
    out = {}
    orig = seal_mod.SEAL_ITEM_BLOCKS
    for label, patched in (("missing_key_in_constant(drop last)", orig[:-1]),
                           ("extra_key_in_constant(+dc_seal_report)", orig + (S.dc_seal_report,)),
                           ("reordered_constant", orig[1:] + orig[:1])):
        monkeypatch.setattr(seal_mod, "SEAL_ITEM_BLOCKS", patched)
        snap, calls = eval_calls(ctx, th)
        try:
            ev = seal_mod.seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), (), base=ctx.base, raise_on_violation=False, **run_of(ctx))
            out[label] = "NO_EXCEPTION status=" + repr([i.status for i in ev.report.items])
        except Exception as e:
            out[label] = type(e).__name__ + ": " + str(e)[:120]
    monkeypatch.setattr(seal_mod, "SEAL_ITEM_BLOCKS", orig)
    emit("extras_fail_closed", out)
    emit("same_object_kernel_run_seal", __import__("gmid_engine.sizing.kernel_run", fromlist=["x"]).SEAL_ITEM_BLOCKS is orig)


def test_probe_b69_partial_on_seal_item_failure(ctx_c, monkeypatch):
    """B69 관찰(판정 아님): 봉인 항목 dc_seal_kcl 단계에서 후보 실패가 나면 부분 스냅샷에 parent 의 뒤 봉인 항목 필드가 남는가."""
    import gmid_engine.sizing.seal as seal_mod
    from gmid_engine.core import NonconvergentError
    ctx = ctx_c[2]
    ev1 = size_and_seal(ctx, theta_c(y=0.45))
    real = seal_mod.dc_seal_kcl

    class Boom:
        name = real.name

        def __call__(self, *a, **k):
            raise NonconvergentError(detail={"probe": "b69"})
    boom = Boom()
    monkeypatch.setattr(seal_mod, "dc_seal_kcl", boom)
    if hasattr(seal_mod, "SEAL_ITEM_BLOCKS"):
        monkeypatch.setattr(seal_mod, "SEAL_ITEM_BLOCKS", tuple(boom if b is real else b for b in seal_mod.SEAL_ITEM_BLOCKS))
    try:
        size_and_seal(ctx, theta_c(y=0.5), parent=ev1)
        emit("b69", "NO_EXCEPTION")
        return
    except NonconvergentError as e:
        part = e.partial
    later = ("dc_seal_bulk_reverse", "dc_seal_saturation", "dc_seal_kvl_branch", "dc_seal_conduction", "dc_seal_kcl", "dc_seal_report")
    emit("b69", {"partial_fp": part.fp, "parent_fp": ev1.snapshot.fp,
                 "later_items_version_equals_parent": {w: [part.block_version(w) is not None, part.block_version(w) == ev1.snapshot.block_version(w)] for w in later},
                 "fresh_items_version_equals_parent": {w: part.block_version(w) == ev1.snapshot.block_version(w) for w in ("dc_columns", "dc_tolerances", "dc_seal_vgs_match")}})
