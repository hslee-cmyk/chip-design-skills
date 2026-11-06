"""`ss_dev` 계산 블록(봉인 op -> MOS 소신호) -- metrics CONTRACT 7.2 (+ 7.7 S-6·S-7·S-12, lut CONTRACT r6 4.1·4.3·4.4) + [JC-1] interface card
20261106-jc1 §3 (D-0, D-a~D-g)·§4 (G-1~G-5).

입력: 손 S2 스냅샷(S1 -> lift_s1 -> 권한표 writer `dc_solve` 로 `device.dc_op` 열을, writer `dc_tolerances` 로 `device.dc_gm` 열을 손으로 쓴다)
+ toy LUT(r6 `load_lut_v2`, JC-1 toy C `jc1_toy`) + toy 규칙 선언(conftest `toy_rule_decl`, `JunctionSource.from_decls(규칙 선언, LUT)`).
기대값: conftest `oracle_ss`(gm·gds·gmb·용량 = toy LUT npz 해석식·numpy 다중선형 보간) 와 [JC-1] 접합 항 = 정의 문장 `cdb = (CDD − CGD)·r_d`, `csb = (CSS − CGS)·r_s`
(조회 좌표 = 기준 폭 표 VGS 축 첫 값, 면적 비 r) -- conftest `oracle_junction`(닫힌 식)·`jc1_toy.hand_junction`(격자 마디 손 식, 비트 동일). 피검 함수·
`junction_at_vgs_min` 으로 기대값을 만들지 않는다. 공통 ε_d 식은 쓰지 않는다.
[JC-1] 옛 BSIM4 접합 test(S-11 `junction_caps` 비트 동일·BSIM4 ValueError 전파·온도 변화 값·sky130 파라미터)는 `tests/RETIRED_TESTS_jc1.md` 에 있다.
"""
from __future__ import annotations

import dataclasses
import math
import sys

import pytest

from gmid_engine.core import SealViolationError, fp_of
from gmid_engine.metrics import (
    GMB_COLUMN,
    GMB_VS_CELL_SECANT,
    JUNCTION_LAYOUT_DIFFUSION,
    JUNCTION_LUT_RULE,
    DiffusionGeometry,
    JunctionSource,
    SsDevice,
    ss_dev,
)
from gmid_engine.sizing import S2_WRITERS, SS_DEV_WRITER, DeviceOp, FingerGeom

from lut.conftest import R5_A, R5_B, R5_C

from .conftest import block_row, fresh_run, row_delta
from .conftest import (
    JUNCTION_RTOL,
    LUT_WM,
    device_op,
    hand_write,
    load_lut_v2,
    lut_access,
    oracle_junction,
    oracle_ss,
    read_rule_decl,
    rel_close,
    s2_of,
    toy_junction,
    toy_rule_decl,
    toy_rule_values,
    topo_doc,
    topo_only,
)
from .jc1_toy import hand_junction, rule_values, toyc_cap_arrays, toyc_lut, node_of

SUP = {"vdd": 1.8, "gnd": 0.0}
OPS = {
    # 모든 축 격자 밖(L 은 앵커), VS 칸 안 -- nmos 는 VS 양수, pmos 는 VS 격자점
    "M1": ("nmos", 1e-6, 0.63, 0.85, 0.2, 3.7e-6),
    "M2": ("pmos", 2e-6, 0.71, 1.13, 0.0, 5.3e-6),
}
RULE_SHA_LINE_OTHER = "xdut d g s b dev l=1e-6 w=4e-6 ad=3e-12 as=1.2e-12 pd=9e-6 ps=7e-6"


def _topo():
    return topo_doc("ssdev_cs", mos=[("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "pmos", "out", "pb", "vdd", "vdd")],
                    passives=[("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"),
                    bias=["pb"])                                 # pb: M2 gate 에만 (authoring 9절 입력 선언)


def _with_ops(s, col, version="hand"):
    """손 dc_op 열 + 같은 동작점의 dc_gm 열(writer dc_tolerances, 값 = gm_id × current -- 설계 40 §3.7-3 의 정의를 손 op 에 적용한 값)."""
    s = hand_write(s, "device", "dc_op", col, version=version)
    return hand_write(s, "device", "dc_gm", {m: o.gm_id * o.current for m, o in col.items()}, version=version)


def _snap(tmp_path, ops=None):
    td = topo_only(tmp_path / "t", _topo())
    ops = OPS if ops is None else ops
    col = {m: device_op(k, L, vgs, vds, vsb, W, current=1e-5 * (i + 1), gm_id=10.0 + i)
           for i, (m, (k, L, vgs, vds, vsb, W)) in enumerate(sorted(ops.items()))}
    return _with_ops(s2_of(td, SUP), col), col


@pytest.fixture(scope="module")
def lut_a(tmp_path_factory):
    """LUT v2 형: 슬라이스 GMBS 열 + 기준 LUT CGS·CGB·CDD·CSS 열."""
    return load_lut_v2(tmp_path_factory.mktemp("lut_a"))


@pytest.fixture(scope="module")
def lut_b(tmp_path_factory):
    """옛 LUT 형: GMBS 열 없음, 용량 CGS(접합 항 입력)·CGG·CGD 만 -- CGB 가 없어 용량 모형은 cgg_minus_cgd_at_gs."""
    return load_lut_v2(tmp_path_factory.mktemp("lut_b"), slice_gmbs=False, cap_cgb=False)


@pytest.fixture(scope="module")
def lut_c(tmp_path_factory):
    """슬라이스 GMBS 없음 + 기준 LUT(w_key = 슬라이스 폭 키)에 GMBS·ID 열 -> 열 출처 cap_table."""
    return load_lut_v2(tmp_path_factory.mktemp("lut_c"), slice_gmbs=False, cap_gmbs=True)


@pytest.fixture(scope="module")
def decl_path(tmp_path_factory):
    """toy 규칙 선언 파일 -- 모듈 안에서 한 번 쓰고 여러 JunctionSource 를 같은 파일에서 만든다."""
    return toy_rule_decl(tmp_path_factory.mktemp("jdecl"))


def _ss(snapshot, acc, js, run=None, *extra):
    """블록 `ss_dev(snapshot, acc, js[, diffusion], donors=, counters=)` 호출. run = 실행 두 객체 키워드(dict), 없으면 새 실행 하나."""
    return ss_dev(snapshot, acc, js, *extra, **(run if run is not None else fresh_run()))


def _ss_row(run):
    return block_row(run["counters"], ss_dev.name)


def _js(decl_path, lut):
    return JunctionSource.from_decls(read_rule_decl(decl_path), lut)


def _check(ss, exp, op, rule=None):
    assert isinstance(ss, SsDevice)
    assert ss.gm == exp["gm"]                       # gm = op.gm_id · op.current (LUT 미사용, 같은 곱)
    for f in ("gds", "gmb", "cgg", "cgd", "cgs", "cgb"):
        assert rel_close(getattr(ss, f), exp[f], 1e-12), (f, getattr(ss, f), exp[f])
    # [JC-1] 접합 용량: 정의 문장의 손 식(VGS 최소 조회 열 × 면적 비) -- 레이아웃 전 규칙 기하(W = 그 평가가 쓴 W, m = 1)
    cdb, csb = oracle_junction(op, rule=rule)
    assert cdb > 0.0 and csb > 0.0
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL), ("cdb", ss.cdb, cdb)
    assert rel_close(ss.csb, csb, JUNCTION_RTOL), ("csb", ss.csb, csb)
    assert ss.junction_model == JUNCTION_LUT_RULE == "lut_vgs_min_rule_area"


def test_block_declaration():
    """reads device.dc_op·dc_tol_v·dc_gm·off_op·region_decl·kind -- [JC-1] `device.dc_finger` 없음(G-1), writes device.ss_dev, writer = 권한표 writer_of."""
    assert ss_dev.name == SS_DEV_WRITER == S2_WRITERS.writer_of("device", "ss_dev") == "ss_dev"
    assert set(ss_dev.reads) == {("device", "dc_op"), ("device", "dc_tol_v"), ("device", "dc_gm"), ("device", "off_op"),
                                 ("device", "region_decl"), ("device", "kind")}
    assert ("device", "dc_finger") not in set(ss_dev.reads)
    assert tuple(ss_dev.writes) == (("device", "ss_dev"),)


def test_gm_is_dc_gm_field_not_recomputed(tmp_path, lut_a, decl_path):
    """[U17 ①] 설계 40 §3.7-3: ss gm = `device.dc_gm` 필드 하나 -- 손 dc_gm 을 정의값의 2 배로 쓰면 ss gm 도 그 값(비트 동일)이고, dc_gm 만 바뀌어도 블록은 다시 계산한다."""
    acc = lut_access(lut_a)
    js = _js(decl_path, lut_a)
    snap, ops = _snap(tmp_path)
    run = fresh_run()
    s1 = _ss(snap, acc, js, run)
    for m, op in ops.items():
        assert s1.value("device", m, "ss_dev").gm == op.gm_id * op.current
    doubled = {m: 2.0 * op.gm_id * op.current for m, op in ops.items()}
    s2 = hand_write(s1, "device", "dc_gm", doubled, version="gm2")
    before = _ss_row(run)
    s3 = _ss(s2, acc, js, run)
    assert s3 is not s2 and row_delta(_ss_row(run), before)[4] == 1
    for m in ops:
        assert s3.value("device", m, "ss_dev").gm == doubled[m]
        assert s3.value("device", m, "ss_dev").gds == s1.value("device", m, "ss_dev").gds


def test_old_pending_name_removed():
    """7.2: 옛 JUNCTION_PENDING(cdb = csb = 0) 경로와 이름은 삭제됐다."""
    import gmid_engine.metrics as metrics
    assert not hasattr(metrics, "JUNCTION_PENDING")
    assert "JUNCTION_PENDING" not in metrics.__all__
    assert "JUNCTION_LUT_RULE" in metrics.__all__ and "JunctionSource" in metrics.__all__


def test_junction_model_identifiers():
    """§3: `junction_model` 값 식별자 -- 레이아웃 전 규칙 면적 / 레이아웃 뒤 배치 면적(옛 `pdk_bsim4_*` 값은 1:1 교체)."""
    assert JUNCTION_LUT_RULE == "lut_vgs_min_rule_area"
    assert JUNCTION_LAYOUT_DIFFUSION == "lut_vgs_min_layout_area"


def test_values_lut_v2_columns(tmp_path, lut_a, decl_path):
    """S-7·S-11: gm·gds·gmb·용량 = 7.2 식(GMBS 열 정본, 용량 lut_cgs_cgb 부호 보존), cdb·csb = VGS 최소 조회 비례 손 식."""
    snap, ops = _snap(tmp_path)
    js = _js(decl_path, lut_a)
    out = _ss(snap, lut_access(lut_a), js)
    col = dict(out.column("device", "ss_dev"))
    assert set(col) == {"M1", "M2"}                 # MOS(= dc_op 있는 소자)만, 커패시터 없음
    for m, op in ops.items():
        ss = col[m]
        _check(ss, oracle_ss(op, "slice", "lut_cgs_cgb"), op)
        assert ss.cap_model == "lut_cgs_cgb"
        assert ss.gmb_model == GMB_COLUMN == "lut_gmbs_column"
    assert col["M1"].cgb < 0.0 and col["M2"].cgb < 0.0
    assert out.field("device", "M1", "ss_dev").writer == SS_DEV_WRITER


def test_junction_lookup_point_and_kind_and_width_mapping(tmp_path, lut_a, decl_path):
    """조회점 (L, vds, vsb)·kind·W 가 실제로 갈린다: toy LUT 열은 kind 마다 배율이 다르고 점 의존이라 점·kind 를 바꾼 대안 식과는 값이 어긋나야 하고,
    소자 전체 값은 r = W/w_ref 배(레이아웃 전 규칙 면적, 둘째 폭 m·w_s 없음)다."""
    snap, ops = _snap(tmp_path)
    js = _js(decl_path, lut_a)
    ss = dict(_ss(snap, lut_access(lut_a), js).column("device", "ss_dev"))["M1"]
    op = ops["M1"]
    other_point = oracle_junction(dataclasses.replace(op, vds=op.vds - op.vsb))      # vds 를 vds − vsb 로 잘못 쓴 경우
    other_kind = oracle_junction(dataclasses.replace(op, kind="pmos"))
    assert not rel_close(ss.cdb, other_point[0], 1e-6)
    assert not rel_close(ss.cdb, other_kind[0], 1e-6) and not rel_close(ss.csb, other_kind[1], 1e-6)
    one = oracle_junction(dataclasses.replace(op, W=LUT_WM))                          # W = w_ref 일 때 r = 1
    assert rel_close(ss.cdb, one[0] * (op.W / LUT_WM), 1e-11) and rel_close(ss.csb, one[1] * (op.W / LUT_WM), 1e-11)
    assert ss.cdb != ss.csb


def test_values_old_lut_secant_and_cap_fallback(tmp_path, lut_b, decl_path):
    """GMBS 열 없는 옛 LUT: gmb = r5 VS 칸 할선, 용량 cgs = cgg − cgd, cgb = 0(CGB 열 없음). 접합 항은 CGS·CDD·CSS 열이 있어 계산된다."""
    snap, ops = _snap(tmp_path)
    js = _js(decl_path, lut_b)
    col = dict(_ss(snap, lut_access(lut_b), js).column("device", "ss_dev"))
    for m, op in ops.items():
        _check(col[m], oracle_ss(op, "secant", "cgg_minus_cgd_at_gs"), op)
        assert col[m].gmb_model == GMB_VS_CELL_SECANT == "lut_vs_cell_secant"
        assert col[m].cap_model == "cgg_minus_cgd_at_gs"


def test_gmb_column_from_cap_table(tmp_path, lut_c, decl_path):
    """슬라이스에 열이 없어도 기준 LUT w_key == op.w_key 이고 GMBS_PER_ID 가 있으면 GMB_COLUMN(lut 4.3 출처 규칙)."""
    snap, ops = _snap(tmp_path)
    col = dict(_ss(snap, lut_access(lut_c), _js(decl_path, lut_c)).column("device", "ss_dev"))
    for m, op in ops.items():
        exp = oracle_ss(op, "cap", "lut_cgs_cgb")
        assert col[m].gmb_model == GMB_COLUMN
        assert rel_close(col[m].gmb, exp["gmb"], 1e-12), (col[m].gmb, exp["gmb"])
        assert not rel_close(col[m].gmb, oracle_ss(op, "slice")["gmb"], 1e-6)


def test_gmb_secant_differs_from_column(tmp_path, lut_a, lut_b, decl_path):
    """두 gmb 정의가 이 점에서 실제로 다른 값이다(모형 표시가 값과 함께 바뀐다는 확인의 전제)."""
    snap, _ = _snap(tmp_path)
    a = _ss(snap, lut_access(lut_a), _js(decl_path, lut_a)).value("device", "M1", "ss_dev").gmb
    b = _ss(snap, lut_access(lut_b), _js(decl_path, lut_b)).value("device", "M1", "ss_dev").gmb
    assert not rel_close(a, b, 1e-3)


@pytest.mark.parametrize("case", ["caps_vs_axis", "op_point_vds_axis", "op_point_l_not_anchor"])
def test_lut_failure_is_seal_violation(tmp_path, tmp_path_factory, decl_path, case):
    """LUT 조회 실패 -> SealViolationError(devices = (소자,)), reason lut_query_failed, lut_reason, device_query."""
    if case == "caps_vs_axis":
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_narrow"), cap_vs=(-0.45, 0.0, 0.45, 0.9))
        ops = {"M1": ("nmos", 1e-6, 0.63, 0.85, 1.35, 3.7e-6), "M2": OPS["M2"]}
        want = ("caps", "lut_axis_out_of_range")
    elif case == "op_point_vds_axis":
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_vds"))
        ops = {"M1": ("nmos", 1e-6, 0.63, 2.0, 0.2, 3.7e-6), "M2": OPS["M2"]}
        want = ("op_point", "lut_axis_out_of_range")
    else:
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_l"), empty_bins=True)       # [WB-1 §4] 앵커 전용(빈 지도) 합성 LUT
        ops = {"M1": ("nmos", 1.5e-6, 0.63, 0.85, 0.2, 3.7e-6), "M2": OPS["M2"]}
        want = ("op_point", "lut_l_not_anchor")          # 모델 bin 지도 없음 -> 앵커 아닌 L 거부(lut 4.0)
    snap, _ = _snap(tmp_path, ops)
    with pytest.raises(SealViolationError) as ei:
        _ss(snap, lut_access(lut), _js(decl_path, lut))
    rec = ei.value.record
    det = dict(rec.detail)
    assert rec.devices == ("M1",)
    assert det["reason"] == "lut_query_failed"
    assert (det["device_query"], det["lut_reason"]) == want


def test_negative_check_valid_point_does_not_raise(tmp_path, tmp_path_factory, decl_path):
    """위 실패 test 의 대조: 좁은 VS 축 LUT 라도 축 안 점이면 예외 없이 값이 나온다(실패가 축 밖 때문임을 확인)."""
    lut = load_lut_v2(tmp_path_factory.mktemp("lut_narrow_ok"), cap_vs=(-0.45, 0.0, 0.45, 0.9))
    snap, ops = _snap(tmp_path)
    js = _js(decl_path, lut)
    col = dict(_ss(snap, lut_access(lut), js).column("device", "ss_dev"))
    _check(col["M1"], oracle_ss(ops["M1"], "slice", "lut_cgs_cgb"), ops["M1"])


def test_reuse_and_recompute(tmp_path, lut_a, decl_path):
    """S-6: 같은 dc_op·LUT·접합 묶음 -> 재사용(`is`, computes 0). dc_op 하나 바꾸면 블록 재계산 1회, recomputes_same_input 0."""
    acc = lut_access(lut_a)
    js = _js(decl_path, lut_a)
    snap, ops = _snap(tmp_path)
    run = fresh_run()                                      # 손 순서 (compute, reuse, reuse, compute)
    s1 = _ss(snap, acc, js, run)
    s2 = _ss(s1, acc, js, run)
    assert s2 is s1
    assert _ss_row(run) == (2, 1, 0, 0, 1, 0)
    s3 = hand_write(s1, "device", "dc_L", {"M1": 1e-6, "M2": 2e-6})        # 읽지 않는 열(dc_L)만 바뀐 스냅샷에서도 재사용
    assert _ss(s3, acc, js, run) is s3
    new = dict(ops)
    op1 = ops["M1"]
    new["M1"] = device_op(op1.kind, op1.L, 0.66, op1.vds, op1.vsb, op1.W, op1.current, op1.gm_id)
    s4 = _with_ops(s1, new, version="hand2")
    s5 = _ss(s4, acc, js, run)
    assert s5 is not s4
    _check(s5.value("device", "M1", "ss_dev"), oracle_ss(new["M1"], "slice"), new["M1"])
    assert _ss_row(run) == (4, 2, 0, 0, 2, 0)


def test_s12_temp_change_recomputes_once_same_bundle_reuses(tmp_path, lut_a, decl_path):
    """S-12: temp_c 만 바꾼 묶음 -> computes +1 (묶음은 블록 입력 버전에 든다; 접합 값은 온도를 읽지 않아 값은 그대로), 같은 파일에서 따로 만든 같은 묶음 -> computes 0."""
    acc = lut_access(lut_a)
    js = _js(decl_path, lut_a)
    snap, ops = _snap(tmp_path)
    run = fresh_run()
    s1 = _ss(snap, acc, js, run)
    before = _ss_row(run)
    js_same = _js(decl_path, lut_a)
    assert js_same is not js and fp_of(js_same) == fp_of(js)
    assert _ss(s1, acc, js_same, run) is s1
    assert row_delta(_ss_row(run), before) == (1, 1, 0, 0, 0, 0)
    js_t = dataclasses.replace(js, temp_c=js.temp_c + 10.0)
    s2 = _ss(s1, acc, js_t, run)
    st = row_delta(_ss_row(run), before)
    assert s2 is not s1
    assert (st[4], st[5]) == (1, 0)
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    for m, op in ops.items():
        _check(s2.value("device", m, "ss_dev"), oracle_ss(op, "slice"), op)
    assert _ss(s2, acc, js_t, run) is s2


@pytest.mark.parametrize("field", ["lut_rule_decl", "temp_c"])
def test_s12_each_bundle_field_changes_input_version(tmp_path, lut_a, decl_path, field):
    """S-12 / 7.2: 접합 묶음의 필드(LUT 규칙 선언·온도) 하나만 바뀌어도 ss_dev 재계산 1회(묶음 지문이 입력 버전에 든다). 면적 비는 a 가 약분되어 값은 같다."""
    acc = lut_access(lut_a)
    js = _js(decl_path, lut_a)
    snap, ops = _snap(tmp_path)
    run = fresh_run()
    s1 = _ss(snap, acc, js, run)
    rule = None
    if field == "lut_rule_decl":
        js2 = toy_junction(tmp_path / "j2", lut_a, rule_line=RULE_SHA_LINE_OTHER)
        rule = toy_rule_values(RULE_SHA_LINE_OTHER)
    else:
        js2 = dataclasses.replace(js, temp_c=js.temp_c + 10.0)
    assert fp_of(js2) != fp_of(js)
    before = _ss_row(run)
    s2 = _ss(s1, acc, js2, run)
    st = row_delta(_ss_row(run), before)
    assert s2 is not s1 and (st[4], st[5]) == (1, 0)
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    for m, op in ops.items():
        _check(s2.value("device", m, "ss_dev"), oracle_ss(op, "slice"), op, rule=rule)


def test_lut_content_changes_input_version(tmp_path, lut_a, lut_b, decl_path):
    """extras(LutAccess) 지문은 LUT 내용을 따른다 -> 다른 LUT 로 부르면 재사용하지 않는다. memo 만 새것이면 재사용."""
    snap, _ = _snap(tmp_path)
    js = _js(decl_path, lut_a)
    s1 = _ss(snap, lut_access(lut_a), js)
    s2 = _ss(s1, lut_access(lut_b), _js(decl_path, lut_b))
    assert s2 is not s1
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    assert _ss(s1, lut_access(lut_a), js) is s1


def test_determinism(tmp_path, tmp_path_factory):
    """같은 입력(따로 만든 LUT·memo·선언 파일) 두 번 -> ss_dev 열 값 지문 동일."""
    fps = []
    for i in range(2):
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_det%d" % i))
        js = toy_junction(tmp_path_factory.mktemp("jdet%d" % i), lut)
        snap, _ = _snap(tmp_path / ("d%d" % i))
        fps.append(fp_of(_ss(snap, lut_access(lut), js).column("device", "ss_dev")))
    assert fps[0] == fps[1]


# ---------------------------------------------------------------- 9절: lut_rel_tol = gm/ID · dc_tol_v (S-14)

def test_s14_lut_rel_tol_is_gm_id_times_dc_tol_v(tmp_path, lut_a, decl_path):
    """S-14: lut_rel_tol = 같은 소자 dc_op.gm_id · dc_tol_v(손으로 쓴 셀, 같은 곱 -> 비트), 셀 None 이면 None. 다른 필드는 ε 와 무관."""
    acc = lut_access(lut_a)
    js = _js(decl_path, lut_a)
    snap, ops = _snap(tmp_path)
    base = dict(_ss(snap, acc, js).column("device", "ss_dev"))
    s1 = hand_write(snap, "device", "dc_tol_v", {"M1": 0.002, "M2": None})
    col = dict(_ss(s1, acc, js).column("device", "ss_dev"))
    assert col["M1"].lut_rel_tol == ops["M1"].gm_id * 0.002
    assert col["M2"].lut_rel_tol is None
    s2 = hand_write(snap, "device", "dc_tol_v", {"M1": 0.002, "M2": 0.0035})
    col2 = dict(_ss(s2, acc, js).column("device", "ss_dev"))
    assert col2["M2"].lut_rel_tol == ops["M2"].gm_id * 0.0035
    for m in ops:
        assert dataclasses.replace(col2[m], lut_rel_tol=None) == dataclasses.replace(base[m], lut_rel_tol=None)


def test_s14_no_dc_tol_v_column_gives_none(tmp_path, lut_a, decl_path):
    snap, ops = _snap(tmp_path)
    col = dict(_ss(snap, lut_access(lut_a), _js(decl_path, lut_a)).column("device", "ss_dev"))
    assert all(col[m].lut_rel_tol is None for m in ops)


def test_s14_dc_tol_v_change_recomputes_once(tmp_path, lut_a, decl_path):
    acc = lut_access(lut_a)
    js = _js(decl_path, lut_a)
    snap, ops = _snap(tmp_path)
    run = fresh_run()
    s1 = _ss(hand_write(snap, "device", "dc_tol_v", {"M1": 0.002, "M2": 0.003}), acc, js, run)
    before = _ss_row(run)
    assert _ss(s1, acc, js, run) is s1
    s2 = _ss(hand_write(s1, "device", "dc_tol_v", {"M1": 0.004, "M2": 0.003}, version="tol2"), acc, js, run)
    st = row_delta(_ss_row(run), before)
    assert (st[4], st[1], st[5]) == (1, 1, 0)
    assert s2.value("device", "M1", "ss_dev").lut_rel_tol == ops["M1"].gm_id * 0.004


# =====================================================================================================================
# [JC-1] toy D -- 격자 마디 위의 단일 nmos (interface §3): 기준 폭 표 toy C(VGS 축 (0.25, 0.5, 1.0)), dc_op L = 2e-6, vds = 1.0, vsb = 0.5.
# 기대값 = §1 J-1 식(손, 비트 동일): cdb = (CDD − CGD)[1,0,1,1]·r_d, csb = (CSS − CGS)[1,0,1,1]·r_s.
# =====================================================================================================================

D_POINT = (2e-6, 0.63, 1.0, 0.5)             # L, vgs(켜진 점 -- 접합 조회와 무관), vds, vsb
NODE = node_of(2e-6, 1.0, 0.5)               # (1, 1, 1)
W_D = 3e-6


def _topo_d(two=False):
    mos = [("M1", "nmos", "out", "in", "gnd", "gnd")]
    pas = [("CL", "capacitor", "out", "gnd")]
    if two:
        mos.append(("M3", "nmos", "out3", "in", "gnd", "gnd"))
        pas.append(("CL3", "capacitor", "out3", "gnd"))
    return topo_doc("jc1_d%d" % two, mos=mos, passives=pas, rails=("gnd",))       # 레일은 단자에 연결된 것만 선언(미연결 레일은 topology_load 가 거부)


def _op_d(W, vgs=0.63, current=1e-5, gm_id=12.0):
    """toy C 슬라이스(r5 닫힌 식)에 맞는 손 DeviceOp: ln IDu = ln 1e-7 + 20v − 6v² + 0.1·vds + ln(0.5)·vsb/0.5."""
    L, _, vds, vsb = D_POINT
    ln = math.log(1e-7) + R5_A * vgs - R5_B * vgs * vgs + R5_C * vds + math.log(0.5) * vsb / 0.5
    return DeviceOp("nmos", current, ln, gm_id, L, W, vgs, vds, vsb, 100, math.exp(ln))


def _snap_d(tmp_path, widths=(("M1", W_D),), finger=None, with_finger=True, two=False):
    """손 S2 스냅샷(toy D). finger = {소자: FingerGeom} (dc_finger 열, with_finger 거짓이면 열 자체를 쓰지 않는다)."""
    td = topo_only(tmp_path / "td", _topo_d(two))
    col = {m: _op_d(W) for m, W in widths}
    s = s2_of(td, {"gnd": 0.0})
    if with_finger:
        s = hand_write(s, "device", "dc_op", col, finger=finger)
    else:
        s = s.write(S2_WRITERS.writer_of("device", "dc_op"), "hand", {("device", "dc_op"): dict(col)})
    s = hand_write(s, "device", "dc_gm", {m: o.gm_id * o.current for m, o in col.items()})
    return s


@pytest.fixture
def toyd(tmp_path):
    lut = toyc_lut(tmp_path / "toyc")
    rule = read_rule_decl(toy_rule_decl(tmp_path / "rule"))
    return lut, lut_access(lut), JunctionSource.from_decls(rule, lut), rule_values(tmp_path / "v")


def test_vgs_min_d0_premise_toy_d_runs_for_other_reasons_free(tmp_path, toyd):
    """D-0 전제: toy D 로 `ss_dev` 가 접합 경로 밖 이유로 실패하지 않는다(켜진 점 조회가 toy C 정의역 안) -- 안 서면 멈추고 보고."""
    lut, acc, js, v = toyd
    out = _ss(_snap_d(tmp_path), acc, js)
    assert isinstance(out.value("device", "M1", "ss_dev"), SsDevice)


def test_vgs_min_da_search_evaluation_uses_evaluated_width_not_finger_product(tmp_path, toyd):
    """D-a: 탐색 평가 -- DeviceOp.W = 3e-6, dc_finger 행 (m = 2, w_f = 1.7e-6: m·w_f = 3.4e-6 ≠ W) -> r 의 면적 = a·W (그 평가가 쓴 W 하나).
    cdb = (CDD − CGD)·((a·3e-6·1.0)/(a·1e-6·1.0)) 비트 동일, 그리고 m·w_f 기하로 낸 값과 다르다. junction_model == lut_vgs_min_rule_area. oracle (a)."""
    lut, acc, js, v = toyd
    fg = {"M1": FingerGeom(2, 1.7e-6, 2 * 1.7e-6 / W_D - 1.0)}
    ss = _ss(_snap_d(tmp_path, finger=fg), acc, js).value("device", "M1", "ss_dev")
    l, d, s = NODE
    exp = hand_junction(l, d, s, v["a"] * W_D, v["b"] * W_D, 1.0, v)
    assert (ss.cdb, ss.csb) == exp
    alt = hand_junction(l, d, s, v["a"] * (2 * 1.7e-6), v["b"] * (2 * 1.7e-6), 1.0, v)       # m·w_f 기하(옛 dc_finger 규칙)
    assert exp[0] != alt[0] and ss.cdb != alt[0] and ss.csb != alt[1]
    assert ss.junction_model == "lut_vgs_min_rule_area"


@pytest.mark.parametrize("variant", ["other_finger_row", "no_finger_column"])
def test_vgs_min_da2_dc_finger_does_not_matter(tmp_path, toyd, variant):
    """D-a2: D-a 에서 dc_finger 행 값만 (m = 5, w_f = 0.9e-6)으로, 또는 dc_finger 열을 쓰지 않은 스냅샷 -> cdb·csb 비트 같음, 정지 없음."""
    lut, acc, js, v = toyd
    ref = _ss(_snap_d(tmp_path / "a", finger={"M1": FingerGeom(2, 1.7e-6, 2 * 1.7e-6 / W_D - 1.0)}), acc, js).value("device", "M1", "ss_dev")
    if variant == "other_finger_row":
        snap = _snap_d(tmp_path / "b", finger={"M1": FingerGeom(5, 0.9e-6, 5 * 0.9e-6 / W_D - 1.0)})
    else:
        snap = _snap_d(tmp_path / "b", with_finger=False)
    got = _ss(snap, acc, js).value("device", "M1", "ss_dev")
    assert (got.cdb, got.csb, got.junction_model) == (ref.cdb, ref.csb, ref.junction_model)


def test_vgs_min_dc_layout_arrangement_uses_placed_area(tmp_path, toyd):
    """D-c: 레이아웃 뒤 -- extra diffusion = (("M1", DiffusionGeometry(1.5e-6, 2.2e-12, 1.9e-12, 4e-6, 4e-6, 2.0)),) ->
    cdb = (CDD − CGD)·((2.2e-12·2.0)/(a·1e-6·1.0)), csb = (CSS − CGS)·((1.9e-12·2.0)/(b·1e-6·1.0)), junction_model == lut_vgs_min_layout_area. oracle (a)."""
    lut, acc, js, v = toyd
    geo = DiffusionGeometry(1.5e-6, 2.2e-12, 1.9e-12, 4e-6, 4e-6, 2.0)
    diffusion = (("M1", geo),)
    ss = _ss(_snap_d(tmp_path), acc, js, None, diffusion).value("device", "M1", "ss_dev")
    l, d, s = NODE
    assert (ss.cdb, ss.csb) == hand_junction(l, d, s, 2.2e-12, 1.9e-12, 2.0, v)
    assert ss.junction_model == "lut_vgs_min_layout_area"
    no_layout = _ss(_snap_d(tmp_path / "n"), acc, js).value("device", "M1", "ss_dev")
    assert no_layout.cdb != ss.cdb                       # 공허 방지: 배치 면적이 값을 실제로 바꾼다


# D-d(D-a 결과 대 base 값 다름): 별도 단언 없이 D-a 의 red 로 갈음한다(interface §3 표 D-d 행의 허용 문언).


@pytest.mark.parametrize("drop,column", [(("CDD",), "CDD"), (("CSS",), "CSS"), (("CGS",), "CGS")], ids=["CDD", "CSS", "CGS"])
def test_vgs_min_de_column_unavailable_is_wrapped_with_device(tmp_path, drop, column):
    """D-e: 기준 표에 CDD(CSS, CGS) 열 없음 + D-a 스냅샷 -> SealViolationError, devices == ("M1",), reason lut_query_failed, lut_reason == lut_column_unavailable,
    column, device_query == junction_at_vgs_min. oracle (d): 계약(열 결손 = 소자 붙여 감쌈)."""
    lut = toyc_lut(tmp_path / "lut", cap=toyc_cap_arrays(drop=drop))
    js = JunctionSource.from_decls(read_rule_decl(toy_rule_decl(tmp_path / "rule")), lut)
    with pytest.raises(SealViolationError) as ei:
        _ss(_snap_d(tmp_path), lut_access(lut), js)
    det = dict(ei.value.record.detail)
    assert ei.value.record.devices == ("M1",)
    assert det["reason"] == "lut_query_failed" and det["lut_reason"] == "lut_column_unavailable"
    assert det["column"] == column and det["kind"] == "nmos" and det["device_query"] == "junction_at_vgs_min"


@pytest.mark.parametrize("bad", ["negative", "nan"], ids=["D-f", "D-g"])
def test_vgs_min_df_dg_negative_or_nan_junction_cap_not_wrapped(tmp_path, bad):
    """D-f/D-g: J-3 꼴 음수(또는 J-6 꼴 NaN) 표 + D-a 스냅샷 -> `ss_dev` 직접: SealViolationError junction_cap_negative(lut_query_failed 로 감싸지 않음 -- lut_reason 키 없음),
    devices == ("M1",), terminal "d", value 음수(NaN). `ss_evaluate` 경유 test 는 test_ss_evaluate.py."""
    node = (1, 0, 1, 1)
    from .jc1_toy import cgd
    val = cgd(*node) - 1e-16 if bad == "negative" else float("nan")
    lut = toyc_lut(tmp_path / "lut", cap=toyc_cap_arrays(set_node={"CDD": {node: val}}))
    js = JunctionSource.from_decls(read_rule_decl(toy_rule_decl(tmp_path / "rule")), lut)
    with pytest.raises(SealViolationError) as ei:
        _ss(_snap_d(tmp_path), lut_access(lut), js)
    det = dict(ei.value.record.detail)
    assert ei.value.record.devices == ("M1",)
    assert det["reason"] == "junction_cap_negative" and det["terminal"] == "d" and "lut_reason" not in det
    assert (det["value"] < 0.0) if bad == "negative" else math.isnan(det["value"])


def test_vgs_min_db_declared_width_device_uses_declared_width_and_declared_point(tmp_path):
    """D-b: `off` 선언 소자 Mx(nmos, 선언 w_m = 2e-6, l_m = 2e-6, off_op vds = 1.0, vsb = 0.5) -> r = 선언 w_m/w_ref = 2.0 (기준 폭 표 상수 열이라 점 무관),
    cdb = (CDD − CGD)·((a·2e-6·1.0)/(a·1e-6·1.0)), csb 같은 꼴, junction_model == lut_vgs_min_rule_area. oracle (a): 합성 상수 열 × 손 면적 비.
    합성 LUT = sizing/wb1_toy r4 bins LUT + 접합 항 입력 열(JC1_CGS·JC1_CDD·JC1_CSS)."""
    from sizing.conftest import W_M
    from sizing.wb1_toy import JC1_CDD, JC1_CGD, JC1_CGS, JC1_CSS
    from .test_ss_off_op_slices import build, evaluate
    pin = ("Mx", "nmos", "vd", "vs", "vs", "gnd")                    # vgs = V(vs) − V(vs) = 0, vds = 1.5 − 0.5 = 1.0, vsb = 0.5 − 0 = 0.5
    case = build(tmp_path, [pin], {"vd": 1.5, "vs": 0.5}, w_m=2e-6, l_m=2e-6)
    snap = evaluate(case).snapshot
    o = snap.value("device", "Mx", "off_op")
    assert (o.vds, o.vsb) == (1.0, 0.5)                                # 전제: off_op 점
    ss = snap.value("device", "Mx", "ss_dev")
    v = rule_values(tmp_path / "v")
    r_d, r_s = (v["a"] * 2e-6 * 1.0) / (v["a"] * W_M * 1.0), (v["b"] * 2e-6 * 1.0) / (v["b"] * W_M * 1.0)
    assert rel_close(ss.cdb, (JC1_CDD - JC1_CGD) * r_d, 1e-12)
    assert rel_close(ss.csb, (JC1_CSS - JC1_CGS) * r_s, 1e-12)
    assert ss.junction_model == "lut_vgs_min_rule_area"


# ---------------------------------------------------------------- 4. graph (G-1 은 test_block_declaration)

def test_vgs_min_g2_same_kind_point_two_widths_one_lookup(tmp_path, monkeypatch, toyd):
    """G-2: 같은 kind·같은 (L, vds, vsb)·다른 W 의 소자 둘(M1 W = 3e-6, M3 W = 1e-6) -> 그 평가의 VGS 최소 조회 `caps` 계산(LUT memo point 영역 miss) 1회,
    둘째 소자는 적중. 관찰: 통과 spy 가 `junction_cap.caps` 호출마다 point 영역 miss 증분을 기록한다(조회 W = 기준 폭이라 두 소자가 같은 키).
    oracle (d): 계약 8(키에 소자 폭이 없다)."""
    import inspect
    lut, acc, js, v = toyd
    mod = sys.modules["gmid_engine.metrics.junction_cap"]
    orig = mod.caps
    sig = inspect.signature(orig)
    seen = []

    def spy(*a, **k):
        before = dict(acc.memo.stats())["point"].misses
        out = orig(*a, **k)
        args = list(sig.bind(*a, **k).arguments.values())
        seen.append((args[3], args[6], dict(acc.memo.stats())["point"].misses - before))      # (vgs, W, miss 증분)
        return out

    monkeypatch.setattr(mod, "caps", spy)
    snap = _snap_d(tmp_path, widths=(("M1", 3e-6), ("M3", 1e-6)), two=True)
    out = _ss(snap, acc, js)
    assert {m for m, _ in out.column("device", "ss_dev")} == {"M1", "M3"}
    assert [x[0] for x in seen] == [0.25, 0.25] and [x[1] for x in seen] == [1e-6, 1e-6]
    assert sorted(x[2] for x in seen) == [0, 1]


def test_vgs_min_g3_dc_finger_only_difference_reuses(tmp_path, toyd):
    """G-3: D-a2 두 스냅샷(dc_finger 만 다름)에 같은 donors·counters 로 ss_dev -> 둘째 계산 0(재사용) -- READS 에서 dc_finger 가 빠진 효과."""
    lut, acc, js, v = toyd
    s_a = _snap_d(tmp_path / "a", finger={"M1": FingerGeom(2, 1.7e-6, 2 * 1.7e-6 / W_D - 1.0)})
    s_b = _snap_d(tmp_path / "b", finger={"M1": FingerGeom(5, 0.9e-6, 5 * 0.9e-6 / W_D - 1.0)})
    run = fresh_run()
    out_a = _ss(s_a, acc, js, run)
    out_b = _ss(s_b, acc, js, run)
    assert _ss_row(run) == (2, 1, 0, 0, 1, 0)
    assert out_b.value("device", "M1", "ss_dev") == out_a.value("device", "M1", "ss_dev")


def test_vgs_min_g4_same_snapshot_twice_second_compute_zero(tmp_path, toyd):
    lut, acc, js, v = toyd
    snap = _snap_d(tmp_path)
    run = fresh_run()
    a = _ss(snap, acc, js, run)
    b = _ss(a, acc, js, run)
    assert b is a
    assert _ss_row(run) == (2, 1, 0, 0, 1, 0)


def test_vgs_min_g5_two_fresh_process_states_bit_identical(tmp_path):
    """G-5: 같은 입력 새 프로세스 상태 두 실행(새 LUT·memo·선언 파일 둘) -> cdb·csb·junction_model 비트 같음, S0 `junction_source` 값 같음."""
    res = []
    for i in range(2):
        root = tmp_path / ("run%d" % i)
        lut = toyc_lut(root / "lut")
        js = JunctionSource.from_decls(read_rule_decl(toy_rule_decl(root / "rule")), lut)
        ss = _ss(_snap_d(root), lut_access(lut), js).value("device", "M1", "ss_dev")
        res.append(((ss.cdb, ss.csb, ss.junction_model), js))
    assert res[0][0] == res[1][0]
    assert res[0][1] == res[1][1] and fp_of(res[0][1]) == fp_of(res[1][1])
