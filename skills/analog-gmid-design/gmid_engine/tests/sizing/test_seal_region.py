"""봉인 7·9 `dc_seal_region(snapshot, lut, *, donors, counters)` -- interface card 20261104-eo1r4-sf1l §1·§2 (T-S1~S7, T-M1, T-R3, T-NO).

입력: r4 toy LUT(VDSAT 열, 격자 2진 분수)로 만든 회로 C(M1 nmos + M2 pmos 부하), `dc_op` 칸은 conftest `tamper` 꼴로 점을 직접 정해 넣는다.
선언 `triode` 는 `build_ctx(..., regions=(RegionDecl(...),))` 입력으로 준다.
oracle (손): VDSAT 는 npz 열 직접 선형 보간(conftest `r4_vdsat_at`; M1 nmos L = 1 µm vgs 0.5 vsb 0 -> 0.25, 2진 분수), tol 은 conftest
`r4_tol_vdsat`(= c2·h²/4, nmos 2^-10). 표 행 판정은 card §1 표를 손으로 옮긴 것. 피검 함수로 기대값을 만들지 않는다.
단언 금지: magnitude·tol·margin 값(card §2).
해석(모호점): `indistinct_undefined`·`band_undefined` 의 원소는 소자 이름(str), `reverse_vds` 는 소자 이름 tuple, `indistinct` 는 (소자, 값) 쌍 tuple 로 읽는다.
"""
import dataclasses
import importlib
import math

import pytest

from gmid_engine.authoring import RegionDecl
from gmid_engine.core import SealViolationError
from gmid_engine.search import STATUS_PENDING_SEAL7, open_run, seal_status
from gmid_engine.sizing import DcInputs, dc_seal_region, size_and_seal

from .call_sites import ENGINE_ROOT, calls_of, engine_sources, imported_modules, words_in_engine
from .conftest import (R4_L, SKILL_DIR, build_ctx, circuit_cs_pmos_load, new_access, r4_tol_vdsat, r4_vdsat_at,
                       seal_item, tamper, theta_r4c, with_tol, write_r4_lut)

REASON_MISSING = "lut_vdsat_column_missing"
VDSAT_M1 = 0.25                      # nmos L=1e-6 vgs=0.5 vsb=0: 0.0625 + 0.25*0.5 + 0.25*0.25 = 0.25 (손계산)
TOL_M1 = 2.0 ** -10                  # r4_tol_vdsat("nmos") 손계산: c2*h^2/4 = 0.25*2^-6/4
M1_OK = dict(vgs=0.5, vds=1.5, vsb=0.0)
M2_OK = dict(vgs=0.5, vds=1.5, vsb=0.0)


def test_hand_constants_match_conftest_oracle():
    """기대값 원천 확인(피검 아님): 손계산 상수 = npz 열 독립 계산."""
    assert r4_vdsat_at("nmos", 1e-6, 0.5, 0.0) == VDSAT_M1
    assert r4_tol_vdsat("nmos") == TOL_M1


@pytest.fixture
def mk(tmp_path_factory, r4_access):
    """(regions, access) -> KernelContext. 실행 두 객체를 쥐므로 function 범위(규칙 M)."""
    def make(regions=(), access=None):
        return build_ctx(tmp_path_factory.mktemp("rg"), circuit_cs_pmos_load(), access or r4_access,
                         regions=tuple(regions))[2]
    return make


def state(ctx, m1=None, m2=None):
    """봉인 전 스냅샷의 dc_op 를 점으로 정해 넣는다(기본 = 둘 다 깊은 포화)."""
    snap, _ = with_tol(ctx, theta_r4c())
    ops = dict(snap.column("device", "dc_op"))
    upd = {"M1": dataclasses.replace(ops["M1"], **{**M1_OK, **(m1 or {})}),
           "M2": dataclasses.replace(ops["M2"], **{**M2_OK, **(m2 or {})})}
    return tamper(snap, "dc_widths", "device", "dc_op", upd, version=snap.block_version("dc_widths"))


def run(snap, lut):
    donors, counters = open_run()
    return dc_seal_region(snap, lut, donors=donors, counters=counters)


def items(snap, lut):
    out = run(snap, lut)
    return seal_item(out, 7), seal_item(out, 9)


TRIODE_M1 = (RegionDecl("M1", "triode"),)


# ---------------------------------------------------------------------------------------------------------------
# T-S1 선언 없는 소자: 꺼짐 -> 봉인 9 fail
# ---------------------------------------------------------------------------------------------------------------

def test_region_seal_both_on_deep_saturation_pass(mk):
    ctx = mk()
    i7, i9 = items(state(ctx), ctx.lut)
    assert (i7.status, i9.status) == ("pass", "pass")


@pytest.mark.parametrize("current", [0.0, -1e-6, -math.ulp(0.0)])
def test_region_seal_undeclared_cutoff_fails_item9(mk, current):
    ctx = mk()
    i7, i9 = items(state(ctx, m1=dict(current=current)), ctx.lut)
    assert i9.status == "fail" and i9.devices == ("M1",)
    assert i7.status == "pass"                    # 꺼짐(행 2)은 봉인 7 의 fail 행이 아니다


def test_region_seal_undeclared_current_boundary_smallest_positive_is_not_cutoff(mk):
    ctx = mk()
    i7, i9 = items(state(ctx, m1=dict(current=math.ulp(0.0))), ctx.lut)
    assert i9.status == "pass" and i7.status == "pass"


# ---------------------------------------------------------------------------------------------------------------
# T-S2 triode: 꺼짐 거부, VDS >= vdsat 거부(등호 포함), VDS < vdsat 통과
# ---------------------------------------------------------------------------------------------------------------

def test_region_seal_triode_cutoff_rejected(mk):
    ctx = mk(TRIODE_M1)
    i7, i9 = items(state(ctx, m1=dict(vds=0.125, current=0.0)), ctx.lut)
    assert i9.status == "fail" and i9.devices == ("M1",)


@pytest.mark.parametrize("vds", [VDSAT_M1, 0.5, 1.5])
def test_region_seal_triode_saturated_or_equal_rejected(mk, vds):
    ctx = mk(TRIODE_M1)
    i7, i9 = items(state(ctx, m1=dict(vds=vds)), ctx.lut)
    assert i7.status == "fail" and i7.devices == ("M1",)
    assert i9.status == "pass"


@pytest.mark.parametrize("vds", [math.nextafter(VDSAT_M1, 0.0), 0.125, 0.0])
def test_region_seal_triode_below_vdsat_passes(mk, vds):
    ctx = mk(TRIODE_M1)
    i7, i9 = items(state(ctx, m1=dict(vds=vds)), ctx.lut)
    assert (i7.status, i9.status) == ("pass", "pass")


def test_region_seal_both_fail_names_sorted(mk):
    ctx = mk()
    i7, _ = items(state(ctx, m1=dict(vds=0.125), m2=dict(vds=0.25)), ctx.lut)   # M2 vdsat 0.5 (손계산)
    assert i7.status == "fail" and i7.devices == ("M1", "M2")


# ---------------------------------------------------------------------------------------------------------------
# T-S3 tol 은 판정 문턱이 아니다: VDS = vdsat 가 경계, tol 은 indistinct 기록
# ---------------------------------------------------------------------------------------------------------------

def _indistinct(item):
    return tuple((d, v) for d, v in dict(item.detail).get("indistinct", ()))


def test_region_seal_below_vdsat_by_half_tol_fails_and_is_indistinct(mk):
    ctx = mk()
    i7, _ = items(state(ctx, m1=dict(vds=VDSAT_M1 - TOL_M1 / 2)), ctx.lut)
    assert i7.status == "fail" and i7.devices == ("M1",)
    assert _indistinct(i7) == (("M1", -TOL_M1 / 2),)
    assert dict(i7.detail)["slack_v"] == -TOL_M1 / 2


def test_region_seal_above_vdsat_by_half_tol_passes_and_is_indistinct(mk):
    """옛 판정(VDS - VDsat >= +tol 요구)이면 fail 이라 red."""
    ctx = mk()
    i7, _ = items(state(ctx, m1=dict(vds=VDSAT_M1 + TOL_M1 / 2)), ctx.lut)
    assert i7.status == "pass"
    assert _indistinct(i7) == (("M1", TOL_M1 / 2),)
    assert dict(i7.detail)["slack_v"] == TOL_M1 / 2


def test_region_seal_exactly_at_vdsat_passes_and_one_ulp_below_fails(mk):
    ctx = mk()
    snap_at = state(ctx, m1=dict(vds=VDSAT_M1))
    i7_at, _ = items(snap_at, ctx.lut)
    assert i7_at.status == "pass" and _indistinct(i7_at) == (("M1", 0.0),)
    i7_below, _ = items(state(ctx, m1=dict(vds=math.nextafter(VDSAT_M1, 0.0))), ctx.lut)
    assert i7_below.status == "fail"


@pytest.mark.parametrize("sign", [-1, 1])
def test_region_seal_tol_apart_is_outside_indistinct_band(mk, sign):
    """|VDS - vdsat| = tol 정확히는 띠(< tol) 밖 -- 목록에 M1 이 없다. 판정은 부호로만."""
    ctx = mk()
    i7, _ = items(state(ctx, m1=dict(vds=VDSAT_M1 + sign * TOL_M1)), ctx.lut)
    assert i7.status == ("pass" if sign > 0 else "fail")
    assert "M1" not in [d for d, _v in _indistinct(i7)]


# ---------------------------------------------------------------------------------------------------------------
# T-S4 미정 경로: tol 미정, 열 없음, 축 밖, domain_edge
# ---------------------------------------------------------------------------------------------------------------

def test_region_seal_tol_undefined_keeps_judgment_and_lists_indistinct_undefined(mk, tmp_path_factory):
    """VGS·VDS·VS 축 2점이면 tol 셀이 None(내부 격자점 없음). 판정은 그대로, 소자는 indistinct_undefined 에 든다."""
    lut = write_r4_lut(tmp_path_factory.mktemp("r4_2pt"), grids=(R4_L, (0.0, 2.0), (0.0, 2.0), (0.0, 2.0)))
    ctx = mk(access=new_access(lut))
    ok = state(ctx, m1=dict(vgs=0.0, vds=0.5), m2=dict(vgs=0.0, vds=1.0))     # vdsat: M1 0.0625, M2 0.25 (격자점, 손계산)
    i7, i9 = items(ok, ctx.lut)
    assert (i7.status, i9.status) == ("pass", "pass")
    assert set(dict(i7.detail)["indistinct_undefined"]) == {"M1", "M2"}
    bad = state(ctx, m1=dict(vgs=0.0, vds=0.03125), m2=dict(vgs=0.0, vds=1.0))   # M1 0.03125 < 0.0625
    j7, _ = items(bad, ctx.lut)
    assert j7.status == "fail" and j7.devices == ("M1",)
    assert set(dict(j7.detail)["indistinct_undefined"]) == {"M1", "M2"}


def test_region_seal_column_missing_item7_undefined_and_pending_seal7(mk, tmp_path_factory):
    """VDSAT 열 없는 LUT: 모든 소자 행 6 -> 7 undefined(reason 열 없음), 보고서 상태 = 봉인 7 대기 그대로."""
    lut = write_r4_lut(tmp_path_factory.mktemp("r4_nocol"), vdsat=())
    ctx = mk(access=new_access(lut))
    i7, i9 = items(state(ctx), ctx.lut)
    assert i7.status == "undefined" and i7.devices == ("M1", "M2")
    assert dict(i7.detail)["reason"] == REASON_MISSING
    assert i9.status == "pass"
    ev = size_and_seal(ctx, theta_r4c())
    assert ev.report.items[6].status == "undefined" and ev.report.items[8].status == "pass"
    assert seal_status(ev) == STATUS_PENDING_SEAL7


def test_region_seal_vdsat_axis_out_item9_undefined(mk):
    ctx = mk()
    i7, i9 = items(state(ctx, m1=dict(vgs=2.25)), ctx.lut)          # VGS 축 끝 2.0 밖
    assert i9.status == "undefined" and i9.devices == ("M1",)
    assert dict(i9.detail)["reason"] == "out_of_domain"
    assert i7.status == "pass"                                       # 행 5 는 봉인 7 의 fail·undefined 행이 아니다


def test_region_seal_cutoff_outranks_out_of_domain_in_item9(mk):
    ctx = mk()
    _, i9 = items(state(ctx, m1=dict(vgs=2.25), m2=dict(current=0.0)), ctx.lut)
    assert i9.status == "fail" and i9.devices == ("M2",)


def test_region_seal_domain_edge_lists_touching_axes(mk):
    """축 끝에 닿은 ((소자, 축), ...): M1 vgs 2.0(VGS 끝)·vsb -0.5(VS 첫)·L 1e-6(L 첫), M2 L 2e-6(L 끝). 순서는 단언하지 않는다."""
    ctx = mk()
    _, i9 = items(state(ctx, m1=dict(vgs=2.0, vds=0.5, vsb=-0.5)), ctx.lut)
    assert i9.status == "pass"
    edges = {tuple(e) for e in dict(i9.detail)["domain_edge"]}
    assert edges == {("M1", "L"), ("M1", "VGS"), ("M1", "VS"), ("M2", "L")}


# ---------------------------------------------------------------------------------------------------------------
# T-S6 VDS < 0: LUT 조회 없이 판정
# ---------------------------------------------------------------------------------------------------------------

def test_region_seal_reverse_vds_undeclared_fails_without_lut_query(mk):
    """vgs 2.25 는 VGS 축 밖 -- VDS >= 0 이면 조회가 OUT_OF_DOMAIN 이 되지만 VDS < 0 이면 조회 자체가 없어 영향 없다."""
    ctx = mk()
    i7, i9 = items(state(ctx, m1=dict(vds=-0.125, vgs=2.25)), ctx.lut)
    assert i7.status == "fail" and i7.devices == ("M1",)
    assert tuple(dict(i7.detail)["reverse_vds"]) == ("M1",)
    assert i9.status == "pass"                                       # 조회가 있었다면 out_of_domain -> undefined


def test_region_seal_reverse_vds_boundary_both_sides_of_zero(mk):
    ctx = mk()
    _, i9_neg = items(state(ctx, m1=dict(vds=-math.ulp(0.0), vgs=2.25)), ctx.lut)
    _, i9_zero = items(state(ctx, m1=dict(vds=0.0, vgs=2.25)), ctx.lut)
    assert i9_neg.status == "pass"                                   # VDS < 0: 조회 0
    assert i9_zero.status == "undefined" and i9_zero.devices == ("M1",)   # VDS = 0: 조회 -> 축 밖


def test_region_seal_reverse_vds_same_with_column_missing_lut(mk, tmp_path_factory):
    """열 없는 LUT 에서도 VDS < 0 소자는 undefined 가 아니라 fail(행 3). 다른 소자(행 6)는 fail 의 devices 에 들지 않는다."""
    lut = write_r4_lut(tmp_path_factory.mktemp("r4_nocol_rv"), vdsat=())
    ctx = mk(access=new_access(lut))
    i7, _ = items(state(ctx, m1=dict(vds=-0.125)), ctx.lut)
    assert i7.status == "fail" and i7.devices == ("M1",)
    assert tuple(dict(i7.detail)["reverse_vds"]) == ("M1",)


def _point_lookups(ctx):
    """LutMemo point 영역(vdsat 등 점 조회)의 조회 수 = hits + misses."""
    return sum(v.hits + v.misses for k, v in ctx.lut.memo.stats() if k == "point")


def test_region_seal_reverse_vds_costs_no_vdsat_lookup(mk):
    """두 소자 모두 VDS < 0: LUT VDSAT 조회 0 (point 영역 조회 수 불변). 대조: 정상 점은 소자마다 조회가 있다."""
    ctx = mk()
    snap = state(ctx, m1=dict(vds=-0.125), m2=dict(vds=-0.25))
    before = _point_lookups(ctx)
    i7, _ = items(snap, ctx.lut)
    assert i7.status == "fail" and i7.devices == ("M1", "M2")
    assert _point_lookups(ctx) == before
    run(state(ctx), ctx.lut)
    assert _point_lookups(ctx) - before >= 2


def test_region_seal_reverse_vds_triode_passes(mk):
    ctx = mk(TRIODE_M1)
    i7, i9 = items(state(ctx, m1=dict(vds=-0.125, vgs=2.25)), ctx.lut)
    assert (i7.status, i9.status) == ("pass", "pass")
    assert "reverse_vds" not in dict(i7.detail)


# ---------------------------------------------------------------------------------------------------------------
# T-S5 삭제 이름·호출 계수, T-R3 호출 자리, T-NO oracle 호출 0
# ---------------------------------------------------------------------------------------------------------------

REMOVED = ("dc_seal_" + "saturation", "dc_seal_" + "conduction", "dc_off_" + "current", "dc_conduction_" + "floor")


def test_region_removed_names_absent_from_engine_sources():
    assert words_in_engine(REMOVED) == set()


def test_region_dc_inputs_has_regions_and_no_linear_devices():
    names = {f.name for f in dataclasses.fields(DcInputs)}
    assert "regions" in names
    assert "linear_" + "devices" not in names


def test_region_judge_called_once_per_device_in_seal(mk, monkeypatch):
    """한 평가(블록 한 번)에서 judge_region 은 소자당 1회 -- 봉인 쪽 호출 계수(M1, M2 = 2)."""
    ctx = mk()
    snap = state(ctx)
    mod = importlib.import_module(dc_seal_region.__module__)
    real = mod.judge_region
    seen = []

    def counting(device, declared, current, vds, vdsat):
        seen.append(device)
        return real(device, declared, current, vds, vdsat)
    monkeypatch.setattr(mod, "judge_region", counting)
    run(snap, ctx.lut)
    assert sorted(seen) == ["M1", "M2"]


def test_region_judge_call_sites_are_the_seal_and_the_gate():
    sites = calls_of("judge_region")
    assert {fn for _f, fn in sites} == {"dc_seal_region", "off_region_gate"}, sorted(sites)


def test_region_oracle_tool_has_no_lut_interpolation_or_engine_import():
    root = SKILL_DIR / "tools" / "spice_oracle"
    files = sorted(root.glob("*.py"))
    assert files, "tools/spice_oracle 가 비어 있다"
    for p in files:
        mods = imported_modules(p)
        assert not any(m == "gmid_engine" or m.startswith("gmid_engine.") for m in mods), (p.name, sorted(mods))
        assert not any(m.startswith("scipy.interpolate") for m in mods), (p.name, sorted(mods))


def test_region_engine_never_imports_the_oracle():
    """T-NO: 봉인·ss 층은 oracle 을 부르지 않는다 -- 엔진 소스의 import 에 spice_oracle 이 없다."""
    bad = []
    for p in engine_sources():
        for m in imported_modules(p):
            if "spice_oracle" in m or m == "tools" or m.startswith("tools."):
                bad.append((p.relative_to(ENGINE_ROOT).as_posix(), m))
    assert bad == []


# ---------------------------------------------------------------------------------------------------------------
# T-S7 통과 점 불변식, T-M1 triode 거부·측정 구성 블록 호출 0
# ---------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("y,v1,v2", [(0.5, 0.6, 0.7), (0.4, 0.8, 0.55)])
def test_region_sealed_points_are_on_and_saturated(mk, y, v1, v2):
    """봉인을 통과한 점의 선언 없는 MOS 는 모두 ID > 0, VDS >= VDSAT(npz 열 독립 보간)."""
    ctx = mk()
    ev = size_and_seal(ctx, theta_r4c(y=y, v1=v1, v2=v2))
    assert ev.sealed is not None
    for name, op in sorted(dict(ev.snapshot.column("device", "dc_op")).items()):
        assert op.current > 0.0, name
        assert op.vds >= r4_vdsat_at(op.kind, op.L, op.vgs, op.vsb), name


def test_region_triode_declared_saturated_point_rejected_without_window_blocks(mk):
    ctx = mk(TRIODE_M1)
    with pytest.raises(SealViolationError) as ei:
        size_and_seal(ctx, theta_r4c(y=0.5, v1=0.6, v2=0.7))         # M1 VDS 0.9 > vdsat ≈ 0.30 (포화)
    assert dict(ei.value.record.detail)["item"] == 7
    assert ei.value.record.devices == ("M1",)
    window_rows = [(r.block, r.calls) for r in ctx.counters.snapshot().blocks if "window" in r.block]
    assert all(c == 0 for _b, c in window_rows), window_rows


def test_region_triode_declared_triode_point_seals_with_no_window_config_field(mk):
    ctx = mk(TRIODE_M1)
    ev = size_and_seal(ctx, theta_r4c(y=0.1, v1=0.6, v2=0.7))        # M1 VDS 0.18 < vdsat ≈ 0.30 (triode)
    assert ev.sealed is not None
    for snap in (ctx.base, ev.snapshot):
        assert [n for n in snap.keys("node") if snap.field("node", n, "dc_window_cfg") is not None] == []


def test_region_word_input_window_mismatch_absent_from_engine_sources():
    word = "input_window_operating_point_" + "mismatch"
    assert words_in_engine((word,)) == set()
