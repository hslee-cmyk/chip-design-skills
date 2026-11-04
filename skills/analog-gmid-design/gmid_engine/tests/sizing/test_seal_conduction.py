"""봉인 9 `dc_seal_conduction(snapshot, lut)` -- CONTRACT r8 6절 표 9행, 2절 새 필드, 8절 실패 규약, 12절 O17.

기준은 `gmid_engine/sizing/CONTRACT.md` r8 만 쓴다(`seal_conduction.py` 소스는 열람하지 않았다).
- 행 = `dc_op.current > 0` 인 MOS(이름순, linear_devices 포함), n_checked = 그 수.
- I_off = lut op_point(L, VGS = 0, VDS, VSB).IDu · W/L, ε = gm_id · dc_tol_v. 크기 = I_off, tol = ε·ID -> margin = I_off/(ε·ID),
  margin > 1 이면 fail(= 1 은 pass). dc_tol_v None -> 그 행 undefined.
- writes device.dc_off_current = I_off, device.dc_conduction_floor = I_off/ε(tol None 이면 None) -- 행이 있는 소자만.
- VGS = 0 조회 lut 실패 -> SealViolationError(devices (소자,), reason lut_query_failed, lut_reason, device_query off_current).

기대값: I_off 는 이 파일이 npz 배열을 직접 읽어 lut CONTRACT 4.2 의 보간(VGS = 0 마디, VDS 2점 cubic-Hermite(기울기 GDS/ID),
VS 선형, L 앵커)으로 다시 계산한다(`npz_off_idu`). 판정 규칙은 conftest `judge_expect`(6절 judge 의 독립 구현). 블록 입력
(dc_op·dc_tol_v)은 스냅샷에서 읽는다 -- 그 값의 정확성은 각 블록 test 몫이다.
"""
import bisect
import dataclasses
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.search import open_run
from gmid_engine.sizing import DC_KEY, SEAL_CONDUCTION, dc_seal_conduction, dc_tolerances, seal_dc, size_and_seal

from .conftest import (R4_L, R4_VDS, R4_VS, Oracle, _hermite, assert_item, build_ctx, circuit_cs_pmos_load,
                       circuit_cs_res, detail, eval_calls, judge_expect, new_access, r4_arrays, r4_ln_idu,
                       resistances_of, tamper, theta_c, theta_r4c, toy_arrays, with_tol, write_r4_lut)
from .conftest import block_row, row_delta, run_of  # [XRUN-F1 card B C1·C4]


# ---------------------------------------------------------------------------
# 독립 oracle
# ---------------------------------------------------------------------------

def _cell(grid, x):
    """lut 4.2 칸 규칙: i = min(max(bisect_right(grid, x) − 1, 0), n − 2), t = (x − grid[i])/(grid[i+1] − grid[i])."""
    n = len(grid)
    i = min(max(bisect.bisect_right(grid, x) - 1, 0), n - 2)
    return i, (x - grid[i]) / (grid[i + 1] - grid[i])


def npz_off_idu(arrays, L, vds, vsb):
    """op_point(L, VGS = 0, vds, vsb).IDu 를 npz 배열로 직접(lut 4.2): VGS = 0 은 격자 마디(t = 0 -> 마디 값 그대로),
    VDS = 2점 Hermite(ln ID, 기울기 GDS/ID; 격자점이면 그 값), VS = 선형, L = 앵커(1 ulp). IDu = exp(lnID)·L/w_m."""
    vgs = [float(v) for v in arrays["VGS"]]
    assert 0.0 in vgs, "이 oracle 은 VGS = 0 이 격자 마디인 LUT 전용"
    ia = vgs.index(0.0)
    Ls = [float(v) for v in arrays["L"]]
    iL = min(range(len(Ls)), key=lambda i: abs(Ls[i] - L))
    assert abs(Ls[iL] - L) <= math.ulp(Ls[iL]), "L 앵커만"
    lnI = np.log(np.asarray(arrays["ID"], dtype=float))
    slope = np.asarray(arrays["GDS"], dtype=float) / np.asarray(arrays["ID"], dtype=float)
    vs = [float(v) for v in arrays["VS"]]
    j, u = _cell(vs, vsb)
    ws = [(s, w) for s, w in ((j, 1.0 - u), (j + 1, u)) if w != 0.0]

    def node(b):
        return (sum(w * float(lnI[iL, ia, b, s]) for s, w in ws), sum(w * float(slope[iL, ia, b, s]) for s, w in ws))
    vd = [float(v) for v in arrays["VDS"]]
    k, t = _cell(vd, vds)
    if t == 0.0:
        V = node(k)[0]
    elif t == 1.0:
        V = node(k + 1)[0]
    else:
        (y0, m0), (y1, m1) = node(k), node(k + 1)
        V = _hermite(y0, y1, m0, m1, vd[k + 1] - vd[k], t)
    return math.exp(V) * Ls[iL] / float(arrays["W"])


def expected(snap, arrays_of):
    """-> (rows, offs, floors). rows = judge_expect 형식 (소자, I_off, ε·ID | None, (소자,), ())."""
    rows, offs, floors = [], {}, {}
    for name, op in sorted(snap.column("device", "dc_op")):
        if not op.current > 0:
            continue
        i_off = npz_off_idu(arrays_of(op.kind), op.L, op.vds, op.vsb) * op.W / op.L
        tv = snap.value("device", name, "dc_tol_v")
        eps = None if tv is None else op.gm_id * tv
        rows.append((name, i_off, None if eps is None else eps * op.current, (name,), ()))
        offs[name] = i_off
        floors[name] = None if eps is None else i_off / eps
    return rows, offs, floors


def item9(snap):
    return snap.value("graph", DC_KEY, "dc_seal_9")


def check_fields(out, offs, floors, rtol=1e-12):
    got_off = dict(out.column("device", "dc_off_current"))
    got_floor = dict(out.column("device", "dc_conduction_floor"))
    assert set(got_off) == set(offs) and set(got_floor) == set(floors)
    for n, v in offs.items():
        assert isinstance(got_off[n], float) and abs(got_off[n] - v) <= rtol * v, (n, got_off[n], v)
    for n, v in floors.items():
        if v is None:
            assert got_floor[n] is None
        else:
            assert isinstance(got_floor[n], float) and abs(got_floor[n] - v) <= rtol * v, (n, got_floor[n], v)


def run9(snap, lut, run=None):
    """[XRUN-F1 card B C4] run = 실행 두 객체 키워드(dict), 없으면 새 실행 하나."""
    if run is None:
        donors, counters = open_run()
        run = dict(donors=donors, counters=counters)
    return dc_seal_conduction(snap, lut, **run)


def set_op(snap, name, **changes):
    op = snap.value("device", name, "dc_op")
    return tamper(snap, "dc_widths", "device", "dc_op", {name: dataclasses.replace(op, **changes)})


def set_tol(snap, name, value):
    return tamper(snap, "dc_tolerances", "device", "dc_tol_v", {name: value})


R4_ARR = {k: r4_arrays(k) for k in ("nmos", "pmos")}
TOY_ARR = {k: toy_arrays(k) for k in ("nmos", "pmos")}


# ---------------------------------------------------------------------------
# 값·판정 (실제 평가 스냅샷)
# ---------------------------------------------------------------------------

def test_item_number():
    assert SEAL_CONDUCTION == 9


@pytest.mark.parametrize("y,v1,v2", [(0.5, 0.6, 0.7), (0.4, 0.8, 0.55), (0.5, 0.3, 0.25), (0.5, 0.02, 0.7)])
def test_values_and_judge_r4(ctx_r4c, y, v1, v2):
    """r4 toy(VDSAT 열): 크기·tol·margin·status·devices·n_checked 와 새 S2 필드 값이 npz 독립 계산과 같다."""
    snap, _ = with_tol(ctx_r4c, theta_r4c(y=y, v1=v1, v2=v2))
    out = run9(snap, ctx_r4c.lut)
    rows, offs, floors = expected(snap, R4_ARR.get)
    exp = judge_expect(rows)
    assert exp["n_checked"] == 2
    assert_item(item9(out), exp, 9, rtol=1e-12)
    check_fields(out, offs, floors)
    if exp["status"] == "fail":
        assert item9(out).margin > 1.0
    # 판별력: 이 매개변수 묶음은 pass 와 fail 을 둘 다 포함한다
    assert (v1 == 0.02) == (exp["status"] == "fail")


@pytest.mark.parametrize("y,i2", [(0.5, 1e-5), (0.3, 1e-4), (0.7, 1e-6)])
def test_values_and_judge_toy(ctx_c, y, i2):
    """conftest 기본 toy(VDSAT 열 없음) 회로 C: 봉인 9 는 VDSAT 열과 무관하게 판정한다."""
    ctx = ctx_c[2]
    snap, _ = with_tol(ctx, theta_c(y=y, i2=i2))
    out = run9(snap, ctx.lut)
    rows, offs, floors = expected(snap, TOY_ARR.get)
    exp = judge_expect(rows)
    assert_item(item9(out), exp, 9, rtol=1e-12)
    check_fields(out, offs, floors)


def test_closed_form_ratio_toy(ctx_c):
    """toy 닫힌 식 교차: writer MOS 는 W = ID·L/exp(ln_idu) 라 I_off/ID = IDu(0, vds, vsb)/exp(ln_idu) =
    exp(−(B·vgs − C·vgs²/2))(같은 vds·vsb) -> margin = exp(−f(vgs))/(gm_id·tol_V)."""
    ctx = ctx_c[2]
    snap, _ = with_tol(ctx, theta_c())
    out = run9(snap, ctx.lut)
    offs = dict(out.column("device", "dc_off_current"))
    for name in ("M1", "M2"):
        op = snap.value("device", name, "dc_op")
        ln = snap.value("device", name, "dc_ln_idu")
        ratio = math.exp(Oracle.ln_idu(op.kind, 0.0, op.vds, op.vsb) - ln)
        assert abs(offs[name] / op.current - ratio) <= 1e-10 * ratio
    op = snap.value("device", "M1", "dc_op")
    tv = snap.value("device", "M1", "dc_tol_v")
    m = math.exp(-Oracle.f(Oracle.vgs_of("nmos", snap.value("device", "M1", "dc_ln_idu"), op.vds, op.vsb))) / (op.gm_id * tv)
    assert abs(offs["M1"] / (op.gm_id * tv * op.current) - m) <= 1e-9 * m
    assert dict(item9(out).detail)["n_checked"] == 2 and item9(out).status == "pass"


# ---------------------------------------------------------------------------
# 경계: margin 정확히 1 은 pass, 1 ulp 위는 fail
# ---------------------------------------------------------------------------

def test_margin_exactly_one_passes_one_ulp_above_fails(ctx_r4c):
    """gm_id = 16, ID = 2^−17 로 바꿔 ε·ID = tol_V·2^−13 을 부동소수 정확하게 만들고(2 의 거듭제곱 곱 -- 곱 순서 무관),
    tol_V* = I_off·2^13 이면 크기 == tol(margin 정확히 1) -> pass. tol_V 를 1 ulp 내리면 tol < I_off -> fail(margin > 1).
    I_off 는 W·L·vds·vsb 만의 함수라 gm_id·ID·tol_V 를 바꿔도 같다."""
    snap, _ = with_tol(ctx_r4c, theta_r4c())
    snap = set_op(snap, "M1", gm_id=16.0, current=2.0 ** -17)
    _, offs, _ = expected(snap, R4_ARR.get)
    first = run9(snap, ctx_r4c.lut)
    i_off = dict(first.column("device", "dc_off_current"))["M1"]
    assert abs(i_off - offs["M1"]) <= 1e-12 * offs["M1"]
    tv_star = i_off * 2.0 ** 13
    assert (16.0 * tv_star) * 2.0 ** -17 == i_off and 16.0 * (tv_star * 2.0 ** -17) == i_off   # 전제: 정확
    at = run9(set_tol(snap, "M1", tv_star), ctx_r4c.lut)
    it = item9(at)
    assert dict(it.detail)["worst"] == "M1"                        # M2 margin ≪ 1 -> 대표 행은 M1
    assert it.status == "pass" and it.margin == 1.0 and it.magnitude == it.tol == i_off
    assert dict(at.column("device", "dc_conduction_floor"))["M1"] == i_off / (16.0 * tv_star)
    below = math.nextafter(tv_star, 0.0)
    bad = run9(set_tol(snap, "M1", below), ctx_r4c.lut)
    it2 = item9(bad)
    assert it2.status == "fail" and it2.devices == ("M1",) and it2.margin > 1.0
    assert it2.magnitude == i_off and it2.tol == 16.0 * below * 2.0 ** -17 < i_off
    rows, _, _ = expected(set_tol(snap, "M1", below), R4_ARR.get)
    assert judge_expect(rows)["status"] == "fail"


# ---------------------------------------------------------------------------
# 행 범위: linear 선언 포함, 꺼진 소자(current ≤ 0) 제외
# ---------------------------------------------------------------------------

def test_linear_declared_devices_included(ctx_r4c):
    """봉인 7 과 달리 linear_devices 도 행이다(전도면 영역과 무관): M1 을 linear 로 선언해도 봉인 9 는 M1 을 재고 fail."""
    th = theta_r4c(v1=0.02)
    snap, calls = eval_calls(ctx_r4c, th)
    with pytest.raises(SealViolationError) as ei:
        seal_dc(snap, calls, ctx_r4c.lut, resistances_of(ctx_r4c, th), ("M1",), base=ctx_r4c.base, **run_of(ctx_r4c))
    d = detail(ei.value)
    assert d["item"] == 9 and ei.value.record.devices == ("M1",)
    assert dict(d["item_detail"])["n_checked"] == 2
    st = {x[0]: x[1] for x in d["items"]}
    assert st[7] == "pass" and st[9] == "fail"
    # 통과 θ 에서도 n_checked 는 linear 선언과 무관하게 2(봉인 7 은 1)
    th2 = theta_r4c()
    snap2, calls2 = eval_calls(ctx_r4c, th2)
    ev = seal_dc(snap2, calls2, ctx_r4c.lut, resistances_of(ctx_r4c, th2), ("M1",), base=ctx_r4c.base, **run_of(ctx_r4c))
    assert dict(ev.report.items[8].detail)["n_checked"] == 2
    assert dict(ev.report.items[6].detail)["n_checked"] == 1


@pytest.mark.parametrize("cur", [0.0, -1e-6])
def test_nonconducting_devices_excluded(ctx_r4c, cur):
    """dc_op.current ≤ 0 인 MOS 는 행이 아니고(n_checked), 새 필드도 쓰지 않는다('행이 있는 소자만')."""
    snap, _ = with_tol(ctx_r4c, theta_r4c(v1=0.02))
    snap = set_op(snap, "M1", current=cur)                       # 위반하던 M1 을 끈다
    out = run9(snap, ctx_r4c.lut)
    rows, offs, floors = expected(snap, R4_ARR.get)
    assert [r[0] for r in rows] == ["M2"]
    exp = judge_expect(rows)
    assert exp["status"] == "pass"
    assert_item(item9(out), exp, 9, rtol=1e-12)
    assert set(dict(out.column("device", "dc_off_current"))) == {"M2"}
    assert set(dict(out.column("device", "dc_conduction_floor"))) == {"M2"}
    check_fields(out, offs, floors)


def test_all_nonconducting_no_rows_pass(ctx_r4c):
    snap, _ = with_tol(ctx_r4c, theta_r4c(v1=0.02))
    snap = set_op(set_op(snap, "M1", current=0.0), "M2", current=0.0)
    it = item9(run9(snap, ctx_r4c.lut))
    assert it.status == "pass" and dict(it.detail)["n_checked"] == 0
    assert it.magnitude is None and it.margin is None


# ---------------------------------------------------------------------------
# tol_V 미정 -> undefined
# ---------------------------------------------------------------------------

def test_tol_none_row_undefined(ctx_r4c):
    """M1 dc_tol_v None -> 그 행 undefined(devices (M1,)), dc_conduction_floor None, dc_off_current 는 값."""
    snap, _ = with_tol(ctx_r4c, theta_r4c())
    snap = set_tol(snap, "M1", None)
    out = run9(snap, ctx_r4c.lut)
    rows, offs, floors = expected(snap, R4_ARR.get)
    exp = judge_expect(rows)
    assert exp["status"] == "undefined" and exp["n_undefined"] == 1
    assert_item(item9(out), exp, 9)
    assert item9(out).devices == ("M1",)
    assert floors["M1"] is None
    check_fields(out, offs, floors)


def test_fail_takes_precedence_over_undefined(ctx_r4c):
    snap, _ = with_tol(ctx_r4c, theta_r4c(v1=0.02))                # M1 fail
    snap = set_tol(snap, "M2", None)                                # M2 undefined
    out = run9(snap, ctx_r4c.lut)
    rows, offs, floors = expected(snap, R4_ARR.get)
    exp = judge_expect(rows)
    assert exp["status"] == "fail"
    assert_item(item9(out), exp, 9, rtol=1e-12)
    assert item9(out).devices == ("M1",) and dict(item9(out).detail)["n_undefined"] == 1
    check_fields(out, offs, floors)


def test_two_point_axes_lut_all_undefined(tmp_path):
    """보간 축이 모두 2점인 LUT(lut 5절 축 양끝 규칙 -> tol_V 셀 전부 None): 실제 평가에서 봉인 9 행이 모두 undefined,
    dc_conduction_floor 는 모두 None, dc_off_current 는 npz 값 -> 평가는 undefined(SealedSnapshot 없음)."""
    grids = (R4_L, (0.0, 2.0), (0.0, 2.0), (-0.5, 2.0))
    lut = write_r4_lut(tmp_path / "lut2", grids=grids)
    ctx = build_ctx(tmp_path, circuit_cs_pmos_load(), new_access(lut))[2]
    arr = {k: r4_arrays(k, grids=grids) for k in ("nmos", "pmos")}
    th = theta_r4c()
    snap, calls = eval_calls(ctx, th)
    s_tol = dc_tolerances(snap, ctx.lut, **run_of(ctx))
    assert all(v is None for _, v in s_tol.column("device", "dc_tol_v"))     # 전제
    out = run9(s_tol, ctx.lut, run_of(ctx))
    rows, offs, floors = expected(s_tol, arr.get)
    exp = judge_expect(rows)
    assert exp["status"] == "undefined" and exp["n_undefined"] == 2
    assert_item(item9(out), exp, 9)
    check_fields(out, offs, floors)
    ev = seal_dc(snap, calls, ctx.lut, resistances_of(ctx, th), (), base=ctx.base, **run_of(ctx))
    assert ev.report.items[8].status == "undefined" and ev.sealed is None


# ---------------------------------------------------------------------------
# W 무관성(12절 O17): W 와 ID 를 같이 k 배 -> 같은 margin, I_off·floor 는 k 배
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("k", [0.25, 3.0, 1e3])
@pytest.mark.parametrize("v1", [0.6, 0.02])
def test_condition_independent_of_width(ctx_r4c, k, v1):
    snap, _ = with_tol(ctx_r4c, theta_r4c(v1=v1))
    base = run9(snap, ctx_r4c.lut)
    op = snap.value("device", "M1", "dc_op")
    scaled = set_op(snap, "M1", W=op.W * k, current=op.current * k)
    out = run9(scaled, ctx_r4c.lut)
    m0 = {r[0]: r[1] / r[2] for r in expected(snap, R4_ARR.get)[0]}["M1"]
    m1 = {r[0]: r[1] / r[2] for r in expected(scaled, R4_ARR.get)[0]}["M1"]
    assert abs(m1 - m0) <= 1e-12 * m0
    assert item9(out).status == item9(base).status
    if v1 == 0.02:                                                  # M1 이 대표 행일 때 margin 비교
        assert dict(item9(out).detail)["worst"] == "M1"
        assert abs(item9(out).margin - item9(base).margin) <= 1e-12 * item9(base).margin
    for field in ("dc_off_current", "dc_conduction_floor"):
        a = dict(base.column("device", field))["M1"]
        b = dict(out.column("device", field))["M1"]
        assert abs(b - k * a) <= 1e-12 * k * a


# ---------------------------------------------------------------------------
# VGS = 0 조회 실패
# ---------------------------------------------------------------------------

def test_off_current_lookup_failure(tmp_path):
    """VGS 축이 0 을 포함하지 않는 LUT(0.125 V 부터): 평가·봉인 1~8 은 VGS ≥ 0.125 에서 돌지만 VGS = 0 조회가 축 밖 ->
    SealViolationError(devices ("M1",), reason lut_query_failed, lut_reason lut_axis_out_of_range, device_query off_current)."""
    grids = (R4_L, tuple(0.125 * i for i in range(1, 17)), R4_VDS, R4_VS)
    lut = write_r4_lut(tmp_path / "lut_novgs0", grids=grids)
    doc = circuit_cs_res()
    doc["topology_name"] = "seal9_lookup"
    ctx = build_ctx(tmp_path, doc, new_access(lut))[2]
    vout = 0.9
    th = {("L", "M1"): 1e-6, ("ln_idu", "M1"): r4_ln_idu("nmos", 0.6, vout, 0.0),
          ("current", "R1"): 1e-5, ("resistance", "R1"): (1.8 - vout) / 1e-5}
    snap, _ = with_tol(ctx, th)
    with pytest.raises(SealViolationError) as ei:
        run9(snap, ctx.lut)
    d = detail(ei.value)
    assert d["reason"] == "lut_query_failed" and d["device_query"] == "off_current"
    assert d["lut_reason"] == "lut_axis_out_of_range"
    assert ei.value.record.devices == ("M1",)
    with pytest.raises(SealViolationError) as ei2:
        size_and_seal(ctx, th)
    d2 = detail(ei2.value)
    assert d2["reason"] == "lut_query_failed" and d2["device_query"] == "off_current"
    assert ei2.value.record.devices == ("M1",)


# ---------------------------------------------------------------------------
# SealedSnapshot 음성: 봉인 9 만 fail 이면 나오지 않는다
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("v1,v2,dev", [(0.02, 0.7, "M1"), (0.6, 0.01, "M2")])
def test_no_sealed_snapshot_when_item9_fails(ctx_r4c, v1, v2, dev):
    """봉인 1~8 이 모두 pass 여도 9 fail -> violated -> SealViolationError(item 9, devices = 위반 소자, margin = 그 margin) --
    DcEvaluation·SealedSnapshot 은 없다. 같은 회로·LUT 의 vgs 0.6·0.7 점은 SealedSnapshot(test_seal.py 양성)."""
    th = theta_r4c(v1=v1, v2=v2)
    snap, calls = eval_calls(ctx_r4c, th)
    s_tol, _ = with_tol(ctx_r4c, th)
    exp = judge_expect(expected(s_tol, R4_ARR.get)[0])
    assert exp["status"] == "fail" and exp["devices"] == (dev,)
    with pytest.raises(SealViolationError) as ei:
        seal_dc(snap, calls, ctx_r4c.lut, resistances_of(ctx_r4c, th), (), base=ctx_r4c.base, **run_of(ctx_r4c))
    rec = ei.value.record
    d = dict(rec.detail)
    st = {x[0]: x[1] for x in d["items"]}
    assert len(st) == 9 and st[9] == "fail" and all(st[n] == "pass" for n in st if n != 9)
    assert d["item"] == 9 and rec.devices == (dev,)
    assert abs(rec.margin - exp["margin"]) <= 1e-12 * exp["margin"] and rec.margin > 1.0
    assert dict(d["item_detail"])["worst"] == dev
    with pytest.raises(SealViolationError) as ei2:
        size_and_seal(ctx_r4c, th)
    assert dict(ei2.value.record.detail)["item"] == 9


# ---------------------------------------------------------------------------
# 재사용
# ---------------------------------------------------------------------------

def test_block_reuse(ctx_r4c):
    # oracle 대조: card B C4 판정 1 -- 같은 lineage 재호출은 reuse, 실행 계수(C1) 증분 = (calls 1, reuses 1, computes 0)
    snap, _ = with_tol(ctx_r4c, theta_r4c())
    out = run9(snap, ctx_r4c.lut, run_of(ctx_r4c))
    before = block_row(ctx_r4c.counters, dc_seal_conduction.name)
    assert run9(out, ctx_r4c.lut, run_of(ctx_r4c)) is out
    assert row_delta(block_row(ctx_r4c.counters, dc_seal_conduction.name), before) == (1, 1, 0, 0, 0, 0)
