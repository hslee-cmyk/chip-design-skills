"""`seal_dc(snapshot, calls, lut, resistances) -> DcEvaluation` -- CONTRACT 6절.

순서 tol -> 1·2·3·6·7·8·[r8] 9 -> 4(calls + 위 8개) -> 5 -> report. violated -> SealViolationError(devices = margin 최대 fail
항목의 devices, margin = 그 margin, detail = item·nodes·items((번호, 상태, margin) [r8] 9개)·item_detail). undefined ->
DcEvaluation(sealed=None). [r4] VDSAT 열이 없는 LUT(conftest 기본 toy)에서는 항목 7 이 undefined 라 SealedSnapshot 이 나오지
않고(음성 확인), 열이 있는 LUT(r4 toy)에서는 1~9 가 모두 pass 인 점이 SealedSnapshot 이 된다 -- 7 fail 이면 나오지 않는다(음성).
봉인 9 단독 실패의 음성 확인은 test_seal_region.py. [EO-1 범위 4] linear_devices 인자는 없어지고(interface §2) 선언은 ctx 의 regions 로 온다.
위반은 출력 필드를 자기 block_version 그대로 바꿔 넣어 만든다(입력 투영이 같아 봉인 4 는 pass 로 남는다).
"""
import dataclasses

import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.sizing import DC_KEY, DcEvaluation, PathValue, SealReport, SealedSnapshot, seal_dc
from fs1_wf import size_and_seal      # [FS-1 서명 맞춤] 손 wf 를 끼운 래퍼

from .conftest import (eval_calls, node_voltages, resistances_of, run_of, tamper, theta_a, theta_c, theta_r4c)


def _seal(ctx, snap, calls, th):
    return seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), base=ctx.base, **run_of(ctx))


def test_undefined_evaluation(ctx_c):
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert isinstance(ev, DcEvaluation)
    assert ev.sealed is None
    assert isinstance(ev.report, SealReport) and ev.report.status == "undefined"
    assert [i.item for i in ev.report.items] == list(range(1, 10))
    assert ev.snapshot.value("graph", DC_KEY, "dc_seal_report") == ev.report
    for n in (1, 2, 3, 6, 7, 8, 9):
        assert ev.snapshot.value("graph", DC_KEY, "dc_seal_%d" % n) == ev.report.items[n - 1]
    # 봉인 4 = calls 4개 + 봉인 계산 블록 7개(tol + 1·2·3·6·영역 판정(7·9)·8)
    assert dict(ev.report.items[3].detail)["n_checked"] == len(calls) + 7      # [EO-1 범위 4] 봉인 계산 블록 7개(tol + 1·2·3·6·7/9·8)


def test_triode_declaration_reaches_item7(tmp_path, toy_access):
    """[EO-1 범위 4] 옛 test_linear_devices_reach_item7: M2 를 선언하면 봉인 7 행이 달라진다. 새 계약(card §1 행 6)에서 triode 도 VDSAT 열이 없으면
    unresolved 행이라, 열 없는 toy 에서 M1(선언 없음)·M2(triode) 둘 다 미정 -> devices ("M1", "M2") (옛: M2 가 빠져 ("M1",))."""
    from gmid_engine.authoring import RegionDecl
    from .conftest import build_ctx, circuit_cs_pmos_load
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), toy_access, regions=(RegionDecl("M2", "triode"),))[2]
    th = theta_c()
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert ev.report.items[6].status == "undefined" and ev.report.items[6].devices == ("M1", "M2")


@pytest.mark.parametrize("y", [0.2, 0.5, 0.8])
@pytest.mark.parametrize("i2", [1e-6, 1e-5, 1e-4])
def test_never_sealed_snapshot(ctx_c, y, i2):
    """음성: 일관 DC 점이어도 항목 7 undefined -> SealedSnapshot 0."""
    ctx, th = ctx_c[2], theta_c(y=y, i2=i2)
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert ev.sealed is None and not isinstance(ev.sealed, SealedSnapshot)
    assert ev.report.status == "undefined"
    assert all(i.status == "pass" for i in ev.report.items if i.item != 7)


def test_violation_reports_worst_item(ctx_c):
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    v_in = node_voltages(snap)["in"]
    ops = dict(snap.column("device", "dc_op"))
    bad = tamper(snap, "dc_solve", "node", "dc_path_values", {"in": (PathValue(("vgs", "M1"), v_in + 0.5),)},
                 version=snap.block_version("dc_solve"))
    bad = tamper(bad, "dc_solve", "device", "dc_op",
                 {"M1": dataclasses.replace(ops["M1"], idu_forward=ops["M1"].idu_forward * 2.0)},
                 version=snap.block_version("dc_solve"))
    with pytest.raises(SealViolationError) as ei:
        _seal(ctx, bad, calls, th)
    rec = ei.value.record
    d = dict(rec.detail)
    items = d["items"]
    assert [x[0] for x in items] == list(range(1, 10))
    st = {x[0]: x[1] for x in items}
    assert st[1] == "fail" and st[2] == "fail" and st[4] == "pass" and st[7] == "undefined"
    margins = {x[0]: x[2] for x in items if x[1] == "fail"}
    worst = max(margins, key=margins.get)
    assert worst == 1                                   # 0.5/tol ≫ ln2/gm/tol
    assert d["item"] == 1
    assert rec.margin == margins[1]
    assert "in" in d["nodes"]
    assert "item_detail" in d


def test_violation_item6_devices(tmp_path, toy_access):
    from .conftest import Oracle, build_ctx, circuit_cs_res
    doc = circuit_cs_res(bulk_m1="out")
    doc["topology_name"] = "hand_seal_bulk"
    ctx = build_ctx(tmp_path, doc, toy_access)[2]
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): Oracle.ln_idu("nmos", 0.6, 0.3, -0.3),
          ("current", "R1"): 1e-5, ("resistance", "R1"): 1.5e5}
    snap, calls = eval_calls(ctx, th)
    with pytest.raises(SealViolationError) as ei:
        _seal(ctx, snap, calls, th)
    assert dict(ei.value.record.detail)["item"] == 6
    assert ei.value.record.devices == ("M1",)


def test_circuit_a_undefined(ctx_a):
    ctx, th = ctx_a[2], theta_a()
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert ev.sealed is None and ev.report.status == "undefined"


# ---------------------------------------------------------------------------
# [r4] VDSAT 열이 있는 LUT -- SealedSnapshot (양성·음성)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("y,v1,v2", [(0.5, 0.6, 0.7), (0.4, 0.8, 0.55)])
def test_sealed_snapshot_when_all_pass(ctx_r4c, y, v1, v2):
    """1~9 가 모두 pass -> REPORT_SEALED, DcEvaluation(sealed=SealedSnapshot(snapshot, report))."""
    th = theta_r4c(y=y, v1=v1, v2=v2)
    snap, calls = eval_calls(ctx_r4c, th)
    ev = _seal(ctx_r4c, snap, calls, th)
    assert [i.status for i in ev.report.items] == ["pass"] * 9
    assert ev.report.status == "sealed"
    assert isinstance(ev.sealed, SealedSnapshot)
    assert ev.sealed.report == ev.report
    assert ev.sealed.snapshot.fp == ev.snapshot.fp
    assert ev.snapshot.value("graph", DC_KEY, "dc_seal_report") == ev.report
    # size_and_seal 경로도 같다
    ev2 = size_and_seal(ctx_r4c, th)
    assert isinstance(ev2.sealed, SealedSnapshot) and ev2.report.status == "sealed"
    assert ev2.snapshot.fp == ev.snapshot.fp


@pytest.mark.parametrize("y,dev", [(0.1, "M1"), (0.9, "M2")])
def test_no_sealed_snapshot_when_item7_fails(ctx_r4c, y, dev):
    """음성: 다른 항목이 모두 pass 여도 봉인 7 fail -> violated -> SealViolationError(DcEvaluation 없음)."""
    th = theta_r4c(y=y)
    snap, calls = eval_calls(ctx_r4c, th)
    with pytest.raises(SealViolationError) as ei:
        _seal(ctx_r4c, snap, calls, th)
    rec = ei.value.record
    d = dict(rec.detail)
    st = {x[0]: x[1] for x in d["items"]}
    assert st[7] == "fail" and all(st[n] == "pass" for n in st if n != 7)
    assert d["item"] == 7 and rec.devices == (dev,)
    m7 = {x[0]: x[2] for x in d["items"]}[7]
    # [EO-1 범위 4, interface §2 / A-88] 봉인 7·9 의 tol·margin 은 None(판정에 문턱이 없다), detail 키는 slack_v·reverse_vds·indistinct… (worst 없음).
    # fail 과 devices 단언은 그대로. 여유는 slack_v: VDS < vdsat 인 fail 소자라 음수.
    assert rec.margin is None and m7 is None
    assert dict(d["item_detail"])["slack_v"] < 0.0
    with pytest.raises(SealViolationError):
        size_and_seal(ctx_r4c, th)


def test_triode_declared_triode_point_still_sealed(tmp_path, r4_access):
    """[EO-1 범위 4] 옛 'linear 선언 소자는 봉인 7 행에서 빠진다' -> 새 계약: triode 선언 소자는 VDS < vdsat(실제로 triode)일 때 표 행 9 로 통과한다
    (포화 위반이어도 봉인을 막지 않는다는 옛 뜻은 triode 점이 통과한다로 바뀜 -- 반대로 포화면 행 10 으로 거부, test_seal_region 이 본다)."""
    from gmid_engine.authoring import RegionDecl
    from .conftest import build_ctx, circuit_cs_pmos_load
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), r4_access, regions=(RegionDecl("M1", "triode"),))[2]
    th = theta_r4c(y=0.1)                                       # M1 VDS 0.18 < VDsat
    snap, calls = eval_calls(ctx, th)
    ev = _seal(ctx, snap, calls, th)
    assert ev.report.status == "sealed" and isinstance(ev.sealed, SealedSnapshot)


@pytest.mark.parametrize("missing", ["donors", "counters", "both"])
def test_seal_dc_run_pair_keywords_required(ctx_c, missing):
    """B-T16(XRUN-F1 card B C6): seal_dc 의 donors·counters 는 필수 키워드(기본값 없음) -- 빠지면 TypeError."""
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    kw = {k: v for k, v in run_of(ctx).items() if missing != "both" and k != missing}
    with pytest.raises(TypeError):
        seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), base=ctx.base, **kw)


# [IT-2a T-L11e, design 41 v1.12.8 L11 (d); oracle (a)/(d) 계약 선언: base 는 필수 -- None·생략은 건너뛰어 pass 하지 않고 TypeError]
def test_it2a_seal_versions_base_none_type_error(ctx_c):
    from gmid_engine.sizing import seal_versions
    snap, calls = eval_calls(ctx_c[2], theta_c())
    with pytest.raises(TypeError):
        seal_versions(snap, calls, None)


def test_it2a_seal_dc_base_none_type_error(ctx_c):
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    with pytest.raises(TypeError):
        seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), base=None, **run_of(ctx))


def test_it2a_seal_dc_base_keyword_required(ctx_c):
    """B-T16 꼴: donors·counters 는 넘기고 base 만 생략 -> TypeError."""
    ctx, th = ctx_c[2], theta_c()
    snap, calls = eval_calls(ctx, th)
    with pytest.raises(TypeError):
        seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), **run_of(ctx))
