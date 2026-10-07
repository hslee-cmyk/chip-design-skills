"""봉인 7 `dc_seal_saturation(snapshot, linear_devices, lut)` -- CONTRACT r4 6절 표.

- 행 = `dc_op.current > 0` 이고 linear_devices 밖인 MOS(이름순), n_checked = 그 수(0 이면 행 없음 -> pass).
- 행마다 VDsat = lut `vdsat(memo, kind, w_key, L, vgs, vds, vsb)`, tol = `tol_vdsat_table(memo, kind, w_key).at(L, vds)`
  (None -> 그 행 undefined). 크기 = VDsat − VDS + 2·tol, tol = tol -> margin = 크기/tol = 1 − (VDS − VDsat − tol)/tol(> 1 ⇔ fail).
- 대표 행이 있으면 detail `slack_v` = 그 행 VDS − VDsat − tol. VDSAT 열이 없는 소자는 tol None 행 + detail `reason` =
  `lut_vdsat_column_missing`(열이 있으면 이 키가 없다). 그 밖 lut 실패 -> SealViolationError(devices (소자,), reason
  `lut_query_failed`, lut_reason, device_query `vdsat`·`tol_vdsat_cell`).

기대값: VDsat 는 npz 열을 직접 선형 보간(conftest `r4_vdsat_at`, 실데이터는 이 파일 `_real_vdsat`), tol 은 lut 5.2 LOO 를 독립
구현(toy 는 닫힌 식 c2·h²/4 = 2^-10·2^-9, 실데이터는 `_real_tol`). 피검 함수로 기대값을 만들지 않는다.

[독립 test 작성자 검토, r4] 작성자 조정 2건 -- (1) 인자 lut 추가: 계약 r4 서명 그대로라 유지 (2) `test_all_linear_still_undefined_not_sealed`
-> `test_all_linear_no_rows_pass`: 계약 r4 표 '0 이면 행 없음 -> pass' 문장 그대로라 유지(행이 없을 때 magnitude·margin None 을 더
확인). 열 없는 toy 의 undefined test 는 이름을 r4 뜻으로 바꾸고 n_undefined·magnitude·slack_v 부재를 더 확인한다.
"""
import bisect
import dataclasses
import math

import numpy as np
import pytest

from gmid_engine.core import SealViolationError
from gmid_engine.lut import LutMemo, op_point, tol_vdsat_table
from gmid_engine.sizing import dc_seal_saturation, pre_layout_lut_access, size_and_seal

from .conftest import (R4_L, build_ctx, circuit_cs_pmos_load, judge_expect, new_access, r4_tol_vdsat, r4_vdsat_at,
                       rel_close, seal_item, tamper, theta_a, theta_c, theta_r4c, with_tol, write_r4_lut)

REASON_MISSING = "lut_vdsat_column_missing"


def run(snap, lin=(), lut=None):
    return seal_item(dc_seal_saturation(snap, tuple(lin), lut), 7)


def ops_of(snap):
    return dict(snap.column("device", "dc_op"))


def retamper(snap, upd):
    """dc_op 를 같은 block_version 으로 바꿔 넣는다(봉인 7 블록 입력만 바꾼다)."""
    return tamper(snap, "dc_widths", "device", "dc_op", upd, version=snap.block_version("dc_widths"))


# ---------------------------------------------------------------------------
# VDSAT 열 없는 toy(conftest 기본 toy) -- 작성자 test 검토 후 유지·보강
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("which", ["C", "A"])
def test_no_vdsat_column_all_rows_undefined(ctx_c, ctx_a, which):
    """열 없는 LUT 세트: 모든 판정 행 undefined + reason lut_vdsat_column_missing(6절 표·r4 머리말 (1))."""
    ctx, th = (ctx_c[2], theta_c()) if which == "C" else (ctx_a[2], theta_a())
    snap, _ = with_tol(ctx, th)
    item = run(snap, (), ctx.lut)
    mos = tuple(sorted(ops_of(snap)))
    assert item.item == 7 and item.status == "undefined"
    assert item.devices == mos
    d = dict(item.detail)
    assert d["reason"] == REASON_MISSING
    assert d["n_checked"] == len(mos) and d["n_undefined"] == len(mos)
    assert item.margin is None and item.magnitude is None and item.tol is None
    assert "slack_v" not in d                                  # VDsat 를 모르면 여유도 없다


def test_linear_devices_excluded(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap, ("M1",), ctx_c[2].lut)
    assert item.status == "undefined" and item.devices == ("M2",)
    assert dict(item.detail)["n_checked"] == 1


def test_all_linear_no_rows_pass(ctx_c):
    """[r4] 판정할 소자가 0개면 행이 없어 pass(n_checked 0) -- 계약 r4 6절 표 '0 이면 행 없음 -> pass'."""
    snap, _ = with_tol(ctx_c[2], theta_c())
    item = run(snap, ("M1", "M2"), ctx_c[2].lut)
    assert item.status == "pass"
    assert item.devices == () and dict(item.detail)["n_checked"] == 0
    assert item.magnitude is None and item.margin is None


def test_zero_current_device_excluded(ctx_c):
    snap, _ = with_tol(ctx_c[2], theta_c())
    s2 = tamper(snap, "dc_currents", "device", "dc_current", {"M2": 0.0})
    op = ops_of(snap)["M2"]
    s2 = tamper(s2, "dc_widths", "device", "dc_op", {"M2": dataclasses.replace(op, current=0.0)})
    item = run(s2, (), ctx_c[2].lut)
    assert item.devices == ("M1",)


# ---------------------------------------------------------------------------
# VDSAT 열 있는 r4 toy -- 판정식·경계·margin·slack_v
# ---------------------------------------------------------------------------

def expected_rows(snap, lin=(), missing=()):
    """6절 표 행의 독립 계산. missing = VDSAT 열이 없는 kind(그 행은 tol None -- 크기 칸은 판정에 안 쓰여 0 자리표).
    -> (judge 행, {소자: (VDsat, tol, VDS − VDsat − tol)})."""
    rows, extra = [], {}
    for name, op in sorted(ops_of(snap).items()):
        if not op.current > 0 or name in lin:
            continue
        if op.kind in missing:
            rows.append((name, 0.0, None, (name,), ()))
            continue
        vd = r4_vdsat_at(op.kind, op.L, op.vgs, op.vsb)
        tol = r4_tol_vdsat(op.kind)
        rows.append((name, vd - op.vds + 2.0 * tol, tol, (name,), ()))
        extra[name] = (vd, tol, op.vds - vd - tol)
    return rows, extra


def check_item(item, rows, column_missing=False):
    """status·devices·n_checked·n_undefined·worst·magnitude·tol·margin·reason 키. slack_v 는 있음만(값은 전용 test)."""
    exp = judge_expect(rows)
    assert item.item == 7 and item.status == exp["status"]
    d = dict(item.detail)
    assert [k for k, _ in item.detail] == sorted(d)
    assert d["n_checked"] == exp["n_checked"] and d["n_undefined"] == exp["n_undefined"]
    assert item.devices == exp["devices"] and item.nodes == ()
    if column_missing:
        assert d["reason"] == REASON_MISSING
    else:
        assert "reason" not in d                                # 열이 있으면 이 키가 없다
    if exp["worst"] is None:
        assert item.margin is None and "slack_v" not in d
        return exp
    assert d["worst"] == exp["worst"]
    mag, tol = exp["ties"][exp["worst"]]
    assert rel_close(item.magnitude, mag, 1e-12, 1e-15) and item.tol == tol
    assert rel_close(item.margin, mag / tol, 1e-12, 1e-12)
    assert "slack_v" in d, "대표 행이 있으면 detail slack_v(6절 표)"
    return exp


def test_toy_vdsat_oracle_values():
    """기대값 원천 자체의 확인(피검 아님): 2진 격자라 VDsat·tol 이 정확한 2진 분수."""
    assert r4_vdsat_at("nmos", 1e-6, 0.5, 0.0) == 0.25
    assert r4_vdsat_at("pmos", 2e-6, 0.5, 0.0) == 0.5
    assert r4_tol_vdsat("nmos") == 2.0 ** -10 and r4_tol_vdsat("pmos") == 2.0 ** -9


R4_SCENARIOS = [(0.5, 0.6, 0.7, "pass"),           # 둘 다 포화
                (0.4, 0.8, 0.55, "pass"),
                (0.1, 0.6, 0.7, "fail"),           # M1 VDS 0.18 < VDsat
                (0.9, 0.6, 0.7, "fail")]           # M2 VDS 0.18 < VDsat


@pytest.mark.parametrize("y,v1,v2,status", R4_SCENARIOS)
def test_r4_rows_circuit_c(ctx_r4c, y, v1, v2, status):
    snap, _ = with_tol(ctx_r4c, theta_r4c(y=y, v1=v1, v2=v2))
    item = run(snap, (), ctx_r4c.lut)
    rows, extra = expected_rows(snap)
    assert judge_expect(rows)["status"] == status                # 시나리오 자체 확인
    exp = check_item(item, rows)
    w = exp["worst"]
    # margin = 1 − (VDS − VDsat − tol)/tol (N3.14 방향 -- 계획 N3.6 margin 의 1 − x)
    assert rel_close(item.margin, 1.0 - extra[w][2] / extra[w][1], 1e-12, 1e-12)
    assert (item.margin > 1.0) == (status == "fail")


@pytest.mark.parametrize("y,v1,v2,status", R4_SCENARIOS)
def test_slack_v_is_vds_minus_vdsat_minus_tol(ctx_r4c, y, v1, v2, status):
    """6절 표: 대표 행이 있으면 detail slack_v = 그 행 VDS − VDsat − tol(V)."""
    snap, _ = with_tol(ctx_r4c, theta_r4c(y=y, v1=v1, v2=v2))
    item = run(snap, (), ctx_r4c.lut)
    rows, extra = expected_rows(snap)
    w = judge_expect(rows)["worst"]
    d = dict(item.detail)
    assert d["worst"] == w
    vd, tol, slack = extra[w]
    assert rel_close(d["slack_v"], slack, 1e-12, 1e-15), \
        ("slack_v 는 VDS − VDsat − tol", d["slack_v"], slack, "VDS − VDsat =", slack + tol)


def _boundary_snap(ctx, dev, vds):
    """dev 의 dc_op 를 격자점 동작점(vgs 0.5, vsb 0)·주어진 vds 로, 다른 소자는 VDS 1.5(깊은 포화)로 바꾼다."""
    snap, _ = with_tol(ctx, theta_r4c())
    ops = ops_of(snap)
    other = "M2" if dev == "M1" else "M1"
    return retamper(snap, {dev: dataclasses.replace(ops[dev], vgs=0.5, vds=vds, vsb=0.0),
                           other: dataclasses.replace(ops[other], vds=1.5)})


BOUNDARY = [("M1", "nmos", 1e-6), ("M2", "pmos", 2e-6)]


def _boundary_vds(kind, L, step):
    vds = r4_vdsat_at(kind, L, 0.5, 0.0) + r4_tol_vdsat(kind)
    if step < 0:
        return math.nextafter(vds, 0.0)
    if step > 0:
        return math.nextafter(vds, 10.0)
    return vds


@pytest.mark.parametrize("dev,kind,L", BOUNDARY)
@pytest.mark.parametrize("step", [-1, 0, 1])
def test_boundary_slack_equals_tol(ctx_r4c, dev, kind, L, step):
    """요구 VDS − VDsat ≥ +tol: 여유 = tol 정확히 -> pass(margin 1.0), 1 ulp 아래 -> fail, 1 ulp 위 -> pass.
    2진 격자라 VDsat(0.25 / 0.5)·tol(2^-10 / 2^-9)·VDS = VDsat + tol 과 그 ±1 ulp 의 모든 산술이 정확하다."""
    tol = r4_tol_vdsat(kind)
    base = _boundary_vds(kind, L, 0)
    vds = _boundary_vds(kind, L, step)
    snap = _boundary_snap(ctx_r4c, dev, vds)
    assert ops_of(snap)[dev].L == L
    item = run(snap, (), ctx_r4c.lut)
    assert dict(item.detail)["worst"] == dev
    if step == 0:
        assert item.status == "pass" and item.margin == 1.0 and item.magnitude == tol
    elif step < 0:
        assert item.status == "fail" and item.devices == (dev,)
        assert item.margin == 1.0 + (base - vds) / tol            # 크기 = tol + 1 ulp 정확
    else:
        assert item.status == "pass" and item.margin == 1.0 - (vds - base) / tol
    rows, _ = expected_rows(snap)
    check_item(item, rows)


@pytest.mark.parametrize("dev,kind,L", BOUNDARY)
@pytest.mark.parametrize("step", [-1, 0, 1])
def test_boundary_slack_v(ctx_r4c, dev, kind, L, step):
    """경계에서 slack_v = VDS − VDsat − tol = 0 / −1 ulp / +1 ulp (정확)."""
    vds = _boundary_vds(kind, L, step)
    item = run(_boundary_snap(ctx_r4c, dev, vds), (), ctx_r4c.lut)
    exp = vds - r4_vdsat_at(kind, L, 0.5, 0.0) - r4_tol_vdsat(kind)
    assert dict(item.detail)["slack_v"] == exp, (dict(item.detail)["slack_v"], exp)


def test_vdsat_reads_op_L_vgs_vsb(ctx_r4c):
    """VDsat 는 op 의 (L, vgs, vsb) 에서 잰다: 열이 L·VS 에 따라 달라지게 만든 toy 에서 격자 밖 vgs·vsb 와 다른 L 앵커."""
    snap, _ = with_tol(ctx_r4c, theta_r4c())
    ops = ops_of(snap)
    s2 = retamper(snap, {"M1": dataclasses.replace(ops["M1"], L=2e-6, vgs=0.55, vsb=0.3, vds=0.47),
                         "M2": dataclasses.replace(ops["M2"], L=1e-6, vgs=0.8, vsb=0.1, vds=0.6)})
    item = run(s2, (), ctx_r4c.lut)
    rows, extra = expected_rows(s2)
    # 판별력: L 앵커·vsb 를 무시하면 VDsat 가 달라진다
    assert extra["M1"][0] != r4_vdsat_at("nmos", 1e-6, 0.55, 0.0)
    assert extra["M1"][0] != r4_vdsat_at("nmos", 2e-6, 0.55, 0.0)
    check_item(item, rows)


def test_both_fail_device_names(ctx_r4c):
    snap, _ = with_tol(ctx_r4c, theta_r4c())
    ops = ops_of(snap)
    s2 = retamper(snap, {"M1": dataclasses.replace(ops["M1"], vds=0.05), "M2": dataclasses.replace(ops["M2"], vds=0.1)})
    item = run(s2, (), ctx_r4c.lut)
    rows, _ = expected_rows(s2)
    check_item(item, rows)
    assert item.status == "fail" and item.devices == ("M1", "M2")


def test_linear_and_zero_current_excluded_r4(ctx_r4c):
    """포화 위반 소자라도 linear 선언·ID ≤ 0 이면 행이 아니다(음성: 그 소자를 넣으면 fail 이다)."""
    snap, _ = with_tol(ctx_r4c, theta_r4c(y=0.1))               # M1 VDS 0.18 -> 포화 위반
    assert run(snap, (), ctx_r4c.lut).status == "fail"
    item = run(snap, ("M1",), ctx_r4c.lut)
    rows, _ = expected_rows(snap, lin=("M1",))
    check_item(item, rows)
    assert item.status == "pass" and dict(item.detail)["n_checked"] == 1
    for cur in (0.0, -1e-6):
        op = ops_of(snap)["M1"]
        it = run(retamper(snap, {"M1": dataclasses.replace(op, current=cur)}), (), ctx_r4c.lut)
        assert it.status == "pass" and dict(it.detail)["n_checked"] == 1 and dict(it.detail)["worst"] == "M2"


@pytest.mark.parametrize("field,value,lut_reason", [("vgs", 2.25, "lut_axis_out_of_range"),
                                                    ("vsb", -0.75, "lut_axis_out_of_range"),
                                                    ("L", 1.5e-6, "lut_l_not_anchor")])
def test_lut_failure_is_structured(ctx_r4c, field, value, lut_reason):
    snap, _ = with_tol(ctx_r4c, theta_r4c())
    op = ops_of(snap)["M1"]
    with pytest.raises(SealViolationError) as ei:
        run(retamper(snap, {"M1": dataclasses.replace(op, **{field: value})}), (), ctx_r4c.lut)
    rec = ei.value.record
    d = dict(rec.detail)
    assert rec.devices == ("M1",)
    assert d["reason"] == "lut_query_failed" and d["lut_reason"] == lut_reason
    assert d["device_query"] in ("vdsat", "tol_vdsat_cell")
    if field in ("vgs", "vsb"):
        assert d["device_query"] == "vdsat"                     # tol 표 조회는 vgs·vsb 를 받지 않는다


# ---------------------------------------------------------------------------
# 열이 일부 kind 에만 있는 LUT, tol 이 정의되지 않는 LUT
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ctx_mixed(tmp_path_factory):
    """nmos 슬라이스만 VDSAT 열, pmos 는 열 없음(기준 LUT 에도 없음 -> lut_column_unavailable)."""
    lut = write_r4_lut(tmp_path_factory.mktemp("r4_mixed"), vdsat=("nmos",))
    return build_ctx(tmp_path_factory.mktemp("ctx_mixed"), circuit_cs_pmos_load(), new_access(lut))[2]


@pytest.mark.parametrize("y,status", [(0.5, "undefined"), (0.1, "fail")])
def test_column_missing_for_one_kind(ctx_mixed, y, status):
    snap, _ = with_tol(ctx_mixed, theta_r4c(y=y))
    item = run(snap, (), ctx_mixed.lut)
    rows, extra = expected_rows(snap, missing=("pmos",))
    exp = judge_expect(rows)
    assert exp["status"] == status
    assert item.status == status
    d = dict(item.detail)
    assert d["reason"] == REASON_MISSING                       # 열 없는 소자 행이 있다
    assert d["n_checked"] == 2 and d["n_undefined"] == 1
    assert item.devices == (("M2",) if status == "undefined" else ("M1",))
    vd, tol, _ = extra["M1"]                                   # 대표 행 = 정의된 행(M1)
    assert d["worst"] == "M1"
    assert rel_close(item.margin, (vd - ops_of(snap)["M1"].vds + 2 * tol) / tol, 1e-12, 1e-12)
    assert "slack_v" in d


def test_tol_undefined_with_column_present(tmp_path_factory):
    """열은 있는데 tol 셀이 None(VGS·VDS·VS 축 2점 -> 내부 격자점 없음, L bin 지도 없음 -> LOO 없음, lut 5.2·5절 양끝 규칙):
    행은 undefined 지만 reason 키는 없다(reason 은 열 없음 전용)."""
    grids = (R4_L, (0.0, 2.0), (0.0, 2.0), (0.0, 2.0))
    lut = write_r4_lut(tmp_path_factory.mktemp("r4_2pt"), grids=grids)
    ctx = build_ctx(tmp_path_factory.mktemp("ctx_2pt"), circuit_cs_pmos_load(), new_access(lut))[2]
    snap, _ = with_tol(ctx, theta_r4c())
    item = run(snap, (), ctx.lut)
    d = dict(item.detail)
    assert item.status == "undefined" and item.devices == ("M1", "M2")
    assert d["n_checked"] == 2 and d["n_undefined"] == 2
    assert "reason" not in d
    assert item.margin is None and "slack_v" not in d


def test_reason_key_absent_whenever_column_present(ctx_r4c):
    """음성: 열 있는 LUT 에서는 pass·fail 어느 θ 에서도 reason 키가 없다."""
    for y in (0.1, 0.5, 0.9):
        snap, _ = with_tol(ctx_r4c, theta_r4c(y=y))
        assert "reason" not in dict(run(snap, (), ctx_r4c.lut).detail)


# ---------------------------------------------------------------------------
# 실데이터 LUT v2 -- 소자 몇 개의 봉인 7 값 대 독립 VDsat·tol
# ---------------------------------------------------------------------------

def _cell(g, x):
    i = min(max(bisect.bisect_right(list(g), x) - 1, 0), len(g) - 2)
    return i, (x - g[i]) / (g[i + 1] - g[i])


def _anchor(Lg, L):
    i = int(np.argmin(np.abs(Lg - L)))
    assert abs(Lg[i] - L) <= math.ulp(Lg[i]), "이 test 는 L 앵커에서만 독립 계산한다"
    return i


def _real_vdsat(a, L, vgs, vds, vsb):
    """lut 4.3: VDSAT 열 모든 축 선형(L 앵커), 가중치 0 마디 생략."""
    iL = _anchor(a["L"], L)
    (ig, tg), (idd, td), (iv, tv) = _cell(a["VGS"], vgs), _cell(a["VDS"], vds), _cell(a["VS"], vsb)
    v = 0.0
    for g, wg in ((ig, 1 - tg), (ig + 1, tg)):
        for k, wk in ((idd, 1 - td), (idd + 1, td)):
            for s, ws in ((iv, 1 - tv), (iv + 1, tv)):
                w = wg * wk * ws
                if w != 0.0:
                    v += w * float(a["VDSAT"][iL, g, k, s])
    return v


def _real_cell(a, on, i, k):
    """lut 5.2 셀 (i, k): VGS·VDS·VS 축 선형 LOO |추정 − 값|(점과 축 방향 두 이웃이 on) 최댓값 / 2^2. L 방향 몫은 이 test 가
    쓰는 앵커(bin 앵커 2개·외부 값 없음 = missing_external)에 없다(fixture 가 확인)."""
    V = a["VDSAT"]
    best = None
    nD = V.shape[2]
    for ax, name in ((1, "VGS"), (2, "VDS"), (3, "VS")):
        g = a[name]
        js = range(1, len(g) - 1) if ax != 2 else ([k] if 0 < k < nD - 1 else [])
        for j in js:
            t = (g[j] - g[j - 1]) / (g[j + 1] - g[j - 1])

            def at(jj):
                idx = [i, slice(None), k, slice(None)]
                idx[ax] = jj
                return tuple(idx)
            cond = on[at(j - 1)] & on[at(j)] & on[at(j + 1)]
            if cond.any():
                y0, y1 = V[at(j - 1)], V[at(j + 1)]
                e = float(np.max(np.abs(y0 + t * (y1 - y0) - V[at(j)])[cond])) / 4.0
                best = e if best is None else max(best, e)
    return best


def _real_tol(a, L, vds):
    on = (a["ID"] > 0) & (a["GM"] > 0)
    i = _anchor(a["L"], L)
    k = min(bisect.bisect_right(list(a["VDS"]), vds) - 1, len(a["VDS"]) - 2)
    vals = [v for v in (_real_cell(a, on, i, k), _real_cell(a, on, i, k + 1)) if v is not None]
    return max(vals) if vals else None


@pytest.fixture(scope="module")
def real_ctx(real_lut_v2, tmp_path_factory):
    lut, files = real_lut_v2
    memo = LutMemo(lut, point=8192, curve=8192, root=8192)
    acc = pre_layout_lut_access(memo)
    ctx = build_ctx(tmp_path_factory.mktemp("real_c"), circuit_cs_pmos_load(), acc)[2]
    arrays = {}
    for kind, wk in acc.w_keys:
        with np.load(files[(kind, wk)]) as z:
            arrays[kind] = {k: np.array(z[k]) for k in ("L", "VGS", "VDS", "VS", "ID", "GM", "VDSAT")}
    # 독립 계산 범위 확인: 이 test 가 쓰는 L 앵커의 tol 행에는 L 방향 몫(LOO·외부 값)이 없다
    for kind, wk in acc.w_keys:
        t = tol_vdsat_table(memo, kind, wk)
        for L in (1e-6, 2e-6):
            assert t.l_loo[_anchor(arrays[kind]["L"], L)] in ("bin_missing_external", "bin_edge")
    return ctx, memo, arrays


REAL_THETAS = [(0.5, 0.7, 0.8, 1e-6, 1e-6), (0.1, 1.2, 0.8, 1e-6, 2e-6),
               (0.95, 0.7, 1.2, 2e-6, 1e-6), (0.3, 0.65, 0.9, 2e-6, 2e-6)]


def _real_eval(real_ctx, y, v1, v2, l1, l2):
    ctx, memo, arrays = real_ctx
    vout = y * 1.8
    th = {("L", "M1"): l1, ("L", "M2"): l2,
          ("ln_idu", "M1"): math.log(op_point(memo, "nmos", 1000, l1, v1, vout, 0.0).IDu),
          ("ln_idu", "M2"): math.log(op_point(memo, "pmos", 1000, l2, v2, 1.8 - vout, 0.0).IDu),
          ("current", "M2"): 1e-5, ("y", "out"): y}
    snap, _ = with_tol(ctx, th)
    item = run(snap, (), ctx.lut)
    rows, extra = [], {}
    for name, op in sorted(ops_of(snap).items()):
        a = arrays[op.kind]
        vd = _real_vdsat(a, op.L, op.vgs, op.vds, op.vsb)
        tol = _real_tol(a, op.L, op.vds)
        assert tol is not None and tol > 0
        rows.append((name, vd - op.vds + 2 * tol, tol, (name,), ()))
        extra[name] = (vd, tol, op.vds - vd - tol)
    return ctx, th, item, rows, extra


@pytest.mark.sizing_realdata
@pytest.mark.parametrize("y,v1,v2,l1,l2", REAL_THETAS)
def test_real_lut_v2_seal7_vs_independent(real_ctx, y, v1, v2, l1, l2):
    ctx, th, item, rows, _ = _real_eval(real_ctx, y, v1, v2, l1, l2)
    exp = judge_expect(rows)
    assert item.status == exp["status"]
    assert item.devices == exp["devices"]
    d = dict(item.detail)
    assert "reason" not in d and d["n_checked"] == 2 and d["n_undefined"] == 0
    assert d["worst"] == exp["worst"]
    mag, tol = exp["ties"][exp["worst"]]
    assert rel_close(item.tol, tol, 1e-12) and rel_close(item.magnitude, mag, 1e-9, 1e-15)
    assert rel_close(item.margin, mag / tol, 1e-9, 1e-12)
    # 판정이 봉인 결과로 이어진다: 1~8 pass 면 SealedSnapshot, 7 fail 이면 위반(item 7, 같은 소자)
    if exp["status"] == "pass":
        ev = size_and_seal(ctx, th)
        assert ev.report.items[6].status == "pass"
        if ev.report.status == "sealed":
            assert ev.sealed is not None and ev.sealed.report == ev.report
    else:
        with pytest.raises(SealViolationError) as ei:
            size_and_seal(ctx, th)
        assert dict(ei.value.record.detail)["item"] == 7
        assert ei.value.record.devices == exp["devices"]


@pytest.mark.sizing_realdata
@pytest.mark.parametrize("y,v1,v2,l1,l2", REAL_THETAS[:2])
def test_real_lut_v2_slack_v(real_ctx, y, v1, v2, l1, l2):
    _, _, item, rows, extra = _real_eval(real_ctx, y, v1, v2, l1, l2)
    w = judge_expect(rows)["worst"]
    d = dict(item.detail)
    assert rel_close(d["slack_v"], extra[w][2], 1e-9, 1e-15), \
        ("slack_v 는 VDS − VDsat − tol", d["slack_v"], extra[w][2])
