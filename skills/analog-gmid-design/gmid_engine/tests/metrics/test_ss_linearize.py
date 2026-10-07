"""`ss_dev` 계산 블록(봉인 op -> MOS 소신호) -- metrics CONTRACT 7.2 (+ 7.7 S-6·S-7, lut CONTRACT r6 4.1·4.3·4.4).

입력: 손 S2 스냅샷(S1 -> lift_s1 -> 권한표 writer `dc_widths` 로 `device.dc_op` 열을 손으로 쓴다).
기대값: conftest `oracle_ss` -- toy LUT npz 의 해석식과 numpy 다중선형 보간으로 7.2 식을 따로 계산(피검 함수·lut 조회 함수 미사용).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import SealViolationError, fp_of
from gmid_engine.metrics import GMB_COLUMN, GMB_VS_CELL_SECANT, JUNCTION_PENDING, SsDevice, ss_dev
from gmid_engine.sizing import S2_WRITERS, SS_DEV_WRITER

from .conftest import (
    device_op,
    hand_write,
    load_lut_v2,
    lut_access,
    oracle_ss,
    rel_close,
    s2_of,
    topo_doc,
    topo_only,
)

SUP = {"vdd": 1.8, "gnd": 0.0}
OPS = {
    # 모든 축 격자 밖(L 은 앵커), VS 칸 안 -- nmos 는 VS 양수, pmos 는 VS 격자점
    "M1": ("nmos", 1e-6, 0.63, 0.85, 0.2, 3.7e-6),
    "M2": ("pmos", 2e-6, 0.71, 1.13, 0.0, 5.3e-6),
}


def _topo():
    return topo_doc("ssdev_cs", mos=[("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "pmos", "out", "pb", "vdd", "vdd")],
                    passives=[("CL", "capacitor", "out", "gnd")], rails=("vdd", "gnd"))


def _snap(tmp_path, ops=None):
    td = topo_only(tmp_path / "t", _topo())
    ops = OPS if ops is None else ops
    col = {m: device_op(k, L, vgs, vds, vsb, W, current=1e-5 * (i + 1), gm_id=10.0 + i)
           for i, (m, (k, L, vgs, vds, vsb, W)) in enumerate(sorted(ops.items()))}
    return hand_write(s2_of(td, SUP), "device", "dc_op", col), col


@pytest.fixture(scope="module")
def lut_a(tmp_path_factory):
    """LUT v2 형: 슬라이스 GMBS 열 + 기준 LUT CGS·CGB 열."""
    return load_lut_v2(tmp_path_factory.mktemp("lut_a"))


@pytest.fixture(scope="module")
def lut_b(tmp_path_factory):
    """옛 LUT 형: GMBS 열 없음, 용량 CGG·CGD 만."""
    return load_lut_v2(tmp_path_factory.mktemp("lut_b"), slice_gmbs=False, cap_cgs_cgb=False)


@pytest.fixture(scope="module")
def lut_c(tmp_path_factory):
    """슬라이스 GMBS 없음 + 기준 LUT(w_key = 슬라이스 폭 키)에 GMBS·ID 열 -> 열 출처 cap_table."""
    return load_lut_v2(tmp_path_factory.mktemp("lut_c"), slice_gmbs=False, cap_gmbs=True)


def _check(ss, exp, rtol=1e-12):
    assert isinstance(ss, SsDevice)
    assert ss.gm == exp["gm"]                       # gm = op.gm_id · op.current (LUT 미사용, 같은 곱)
    for f in ("gds", "gmb", "cgg", "cgd", "cgs", "cgb"):
        assert rel_close(getattr(ss, f), exp[f], rtol), (f, getattr(ss, f), exp[f])
    assert ss.cdb == 0.0 and ss.csb == 0.0          # 접합 용량 명시 대기(Q3)
    assert ss.junction_model == JUNCTION_PENDING == "pending_pdk_junction_params"


def test_block_declaration():
    """reads device.dc_op, writes device.ss_dev, writer = 권한표 writer_of(device, ss_dev)."""
    assert ss_dev.name == SS_DEV_WRITER == S2_WRITERS.writer_of("device", "ss_dev") == "ss_dev"
    assert tuple(ss_dev.reads) == (("device", "dc_op"),)
    assert tuple(ss_dev.writes) == (("device", "ss_dev"),)


def test_values_lut_v2_columns(tmp_path, lut_a):
    """S-7: gm·gds·gmb·용량 = 7.2 식(GMBS 열 정본, 용량 lut_cgs_cgb 부호 보존)."""
    snap, ops = _snap(tmp_path)
    out = ss_dev(snap, lut_access(lut_a))
    col = dict(out.column("device", "ss_dev"))
    assert set(col) == {"M1", "M2"}                 # MOS(= dc_op 있는 소자)만, 커패시터 없음
    for m, op in ops.items():
        ss = col[m]
        _check(ss, oracle_ss(op, "slice", "lut_cgs_cgb"))
        assert ss.cap_model == "lut_cgs_cgb"
        assert ss.gmb_model == GMB_COLUMN == "lut_gmbs_column"
    # 음의 용량은 절댓값·클램프 없이 그대로(lut 1.2 부호 보존, Q7)
    assert col["M1"].cgb < 0.0 and col["M2"].cgb < 0.0
    assert out.field("device", "M1", "ss_dev").writer == SS_DEV_WRITER


def test_values_old_lut_secant_and_cap_fallback(tmp_path, lut_b):
    """GMBS 열 없는 옛 LUT: gmb = r5 VS 칸 할선(GMB_VS_CELL_SECANT), 용량 cgs = cgg − cgd, cgb = 0."""
    snap, ops = _snap(tmp_path)
    col = dict(ss_dev(snap, lut_access(lut_b)).column("device", "ss_dev"))
    for m, op in ops.items():
        _check(col[m], oracle_ss(op, "secant", "cgg_minus_cgd_at_gs"))
        assert col[m].gmb_model == GMB_VS_CELL_SECANT == "lut_vs_cell_secant"
        assert col[m].cap_model == "cgg_minus_cgd_at_gs"


def test_gmb_column_from_cap_table(tmp_path, lut_c):
    """슬라이스에 열이 없어도 기준 LUT w_key == op.w_key 이고 GMBS_PER_ID 가 있으면 GMB_COLUMN(lut 4.3 출처 규칙)."""
    snap, ops = _snap(tmp_path)
    col = dict(ss_dev(snap, lut_access(lut_c)).column("device", "ss_dev"))
    for m, op in ops.items():
        exp = oracle_ss(op, "cap", "lut_cgs_cgb")
        assert col[m].gmb_model == GMB_COLUMN
        assert rel_close(col[m].gmb, exp["gmb"], 1e-12), (col[m].gmb, exp["gmb"])
        # 슬라이스 출처 계수로 계산한 값과는 다르다(출처를 실제로 기준 LUT 에서 읽었다)
        assert not rel_close(col[m].gmb, oracle_ss(op, "slice")["gmb"], 1e-6)


def test_gmb_secant_differs_from_column(tmp_path, lut_a, lut_b):
    """두 gmb 정의가 이 점에서 실제로 다른 값이다(모형 표시가 값과 함께 바뀐다는 확인의 전제)."""
    snap, _ = _snap(tmp_path)
    a = ss_dev(snap, lut_access(lut_a)).value("device", "M1", "ss_dev").gmb
    b = ss_dev(snap, lut_access(lut_b)).value("device", "M1", "ss_dev").gmb
    assert not rel_close(a, b, 1e-3)


@pytest.mark.parametrize("case", ["caps_vs_axis", "op_point_vds_axis", "op_point_l_not_anchor"])
def test_lut_failure_is_seal_violation(tmp_path, tmp_path_factory, case):
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
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_l"))
        ops = {"M1": ("nmos", 1.5e-6, 0.63, 0.85, 0.2, 3.7e-6), "M2": OPS["M2"]}
        want = ("op_point", "lut_l_not_anchor")          # 모델 bin 지도 없음 -> 앵커 아닌 L 거부(lut 4.0)
    snap, _ = _snap(tmp_path, ops)
    with pytest.raises(SealViolationError) as ei:
        ss_dev(snap, lut_access(lut))
    rec = ei.value.record
    det = dict(rec.detail)
    assert rec.devices == ("M1",)
    assert det["reason"] == "lut_query_failed"
    assert (det["device_query"], det["lut_reason"]) == want


def test_negative_check_valid_point_does_not_raise(tmp_path, tmp_path_factory):
    """위 실패 test 의 대조: 좁은 VS 축 LUT 라도 축 안 점이면 예외 없이 값이 나온다(실패가 축 밖 때문임을 확인)."""
    lut = load_lut_v2(tmp_path_factory.mktemp("lut_narrow_ok"), cap_vs=(-0.45, 0.0, 0.45, 0.9))
    snap, ops = _snap(tmp_path)
    col = dict(ss_dev(snap, lut_access(lut)).column("device", "ss_dev"))
    _check(col["M1"], oracle_ss(ops["M1"], "slice", "lut_cgs_cgb"))


def test_reuse_and_recompute(tmp_path, lut_a):
    """S-6: 같은 dc_op·LUT -> 재사용(`is`, computes 0). dc_op 하나 바꾸면 블록 재계산 1회, recomputes_same_input 0."""
    acc = lut_access(lut_a)
    snap, ops = _snap(tmp_path)
    ss_dev.reset_stats()
    s1 = ss_dev(snap, acc)
    s2 = ss_dev(s1, acc)
    assert s2 is s1
    st = ss_dev.stats()
    assert (st.calls, st.computes, st.reuses) == (2, 1, 1)
    # 읽지 않는 열(dc_L)만 바뀐 스냅샷에서도 재사용
    s3 = hand_write(s1, "device", "dc_L", {"M1": 1e-6, "M2": 2e-6})
    assert ss_dev(s3, acc) is s3
    # M1 의 dc_op 만 바꿈 -> 재계산, 새 값은 새 op 의 식
    new = dict(ops)
    op1 = ops["M1"]
    new["M1"] = device_op(op1.kind, op1.L, 0.66, op1.vds, op1.vsb, op1.W, op1.current, op1.gm_id)
    s4 = hand_write(s1, "device", "dc_op", new, version="hand2")
    s5 = ss_dev(s4, acc)
    assert s5 is not s4
    _check(s5.value("device", "M1", "ss_dev"), oracle_ss(new["M1"], "slice"))
    st = ss_dev.stats()
    assert st.computes == 2 and st.recomputes_same_input == 0


def test_lut_content_changes_input_version(tmp_path, lut_a, lut_b):
    """extras(LutAccess) 지문은 LUT 내용을 따른다 -> 다른 LUT 로 부르면 재사용하지 않는다. memo 만 새것이면 재사용."""
    snap, _ = _snap(tmp_path)
    s1 = ss_dev(snap, lut_access(lut_a))
    s2 = ss_dev(s1, lut_access(lut_b))
    assert s2 is not s1
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    assert ss_dev(s1, lut_access(lut_a)) is s1


def test_determinism(tmp_path, tmp_path_factory):
    """같은 입력(따로 만든 LUT·memo) 두 번 -> ss_dev 열 값 지문 동일."""
    fps = []
    for i in range(2):
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_det%d" % i))
        snap, _ = _snap(tmp_path / ("d%d" % i))
        fps.append(fp_of(ss_dev(snap, lut_access(lut)).column("device", "ss_dev")))
    assert fps[0] == fps[1]
