"""`ss_dev` 계산 블록(봉인 op -> MOS 소신호) -- metrics CONTRACT 7.2 (+ 7.7 S-6·S-7·S-11·S-12, lut CONTRACT r6 4.1·4.3·4.4).

입력: 손 S2 스냅샷(S1 -> lift_s1 -> 권한표 writer `dc_widths` 로 `device.dc_op` 열을 손으로 쓴다) + toy LUT r6 + toy 접합 선언
(conftest `toy_junction_decls` -- core 9.1 형식 PDK 선언·LUT 규칙 선언, 8.5 소비자 호출 `JunctionSource.from_decls`).
기대값: conftest `oracle_ss` -- toy LUT npz 의 해석식과 numpy 다중선형 보간으로 7.2 식을 따로 계산(피검 함수·lut 조회 함수 미사용).
접합 용량: conftest `oracle_junction` -- 8.2 식의 독립 구현(`ref_caps`)에 toy 선언에 쓴 파라미터·규칙 줄 값을 넣는다.
S-11 의 비트 동일은 계약 문장 그대로(같은 `dc_op`·`JunctionSource` 로 공개 `junction_caps` 를 부른 값)만 그 경로로 확인한다.
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import SealViolationError, fp_of
from gmid_engine.metrics import (
    GMB_COLUMN,
    GMB_VS_CELL_SECANT,
    JUNCTION_LUT_RULE,
    JunctionSource,
    SsDevice,
    junction_caps,
    ss_dev,
)
from gmid_engine.sizing import S2_WRITERS, SS_DEV_WRITER

from .conftest import (
    JUNCTION_RTOL,
    LUT_WM,
    TOY_JUNCTION,
    device_op,
    hand_write,
    load_lut_v2,
    lut_access,
    oracle_junction,
    oracle_ss,
    read_decls,
    rel_close,
    s2_of,
    topo_doc,
    topo_only,
    toy_junction,
    toy_junction_decls,
    toy_rule_values,
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


@pytest.fixture(scope="module")
def decl_paths(tmp_path_factory):
    """toy 접합 선언 파일 (pdk, rule) -- 모듈 안에서 한 번 쓰고 여러 JunctionSource 를 같은 파일에서 만든다."""
    return toy_junction_decls(tmp_path_factory.mktemp("jdecl"))


def _js(decl_paths, lut):
    return JunctionSource.from_decls(*read_decls(*decl_paths), lut)


def _bit_junction(op, js):
    """S-11: 계약 문장 그대로 -- 같은 dc_op·JunctionSource 로 공개 junction_caps 를 부른 값(w_m = 슬라이스 폭)."""
    jc = junction_caps(js.params_of(op.kind), js.pre_layout_geometry(LUT_WM, op.W / LUT_WM), op.vds + op.vsb, op.vsb,
                       js.temp_c)
    return jc.cdb, jc.csb


def _check(ss, exp, op, js, rtol=1e-12, temp_c=27.0, params=None, rule=None):
    assert isinstance(ss, SsDevice)
    assert ss.gm == exp["gm"]                       # gm = op.gm_id · op.current (LUT 미사용, 같은 곱)
    for f in ("gds", "gmb", "cgg", "cgd", "cgs", "cgb"):
        assert rel_close(getattr(ss, f), exp[f], rtol), (f, getattr(ss, f), exp[f])
    # 접합 용량(DEC-91): 독립 8.2 식(선언에 쓴 값) 과 상대 오차, 계약 S-11 경로와 비트 동일
    cdb, csb = oracle_junction(op, params=params, temp_c=temp_c, rule=rule)
    assert cdb > 0.0 and csb > 0.0
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL), ("cdb", ss.cdb, cdb)
    assert rel_close(ss.csb, csb, JUNCTION_RTOL), ("csb", ss.csb, csb)
    assert (ss.cdb, ss.csb) == _bit_junction(op, js)
    assert ss.junction_model == JUNCTION_LUT_RULE == "pdk_bsim4_lut_rule_diffusion"


def test_block_declaration():
    """reads device.dc_op, writes device.ss_dev, writer = 권한표 writer_of(device, ss_dev)."""
    assert ss_dev.name == SS_DEV_WRITER == S2_WRITERS.writer_of("device", "ss_dev") == "ss_dev"
    assert tuple(ss_dev.reads) == (("device", "dc_op"),)
    assert tuple(ss_dev.writes) == (("device", "ss_dev"),)


def test_old_pending_name_removed():
    """7.2: 옛 JUNCTION_PENDING(cdb = csb = 0) 경로와 이름은 삭제됐다."""
    import gmid_engine.metrics as metrics
    assert not hasattr(metrics, "JUNCTION_PENDING")
    assert "JUNCTION_PENDING" not in metrics.__all__
    assert "JUNCTION_LUT_RULE" in metrics.__all__ and "JunctionSource" in metrics.__all__


def test_values_lut_v2_columns(tmp_path, lut_a, decl_paths):
    """S-7·S-11: gm·gds·gmb·용량 = 7.2 식(GMBS 열 정본, 용량 lut_cgs_cgb 부호 보존), cdb·csb = 8.2 식(LUT 규칙 기하)."""
    snap, ops = _snap(tmp_path)
    js = _js(decl_paths, lut_a)
    out = ss_dev(snap, lut_access(lut_a), js)
    col = dict(out.column("device", "ss_dev"))
    assert set(col) == {"M1", "M2"}                 # MOS(= dc_op 있는 소자)만, 커패시터 없음
    for m, op in ops.items():
        ss = col[m]
        _check(ss, oracle_ss(op, "slice", "lut_cgs_cgb"), op, js)
        assert ss.cap_model == "lut_cgs_cgb"
        assert ss.gmb_model == GMB_COLUMN == "lut_gmbs_column"
    # 음의 용량은 절댓값·클램프 없이 그대로(lut 1.2 부호 보존, Q7)
    assert col["M1"].cgb < 0.0 and col["M2"].cgb < 0.0
    assert out.field("device", "M1", "ss_dev").writer == SS_DEV_WRITER


def test_junction_bias_and_side_mapping(tmp_path, lut_a, decl_paths):
    """v_db = vds + vsb(drain 쪽 파라미터·ad·pd), v_sb = vsb(source 쪽·as·ps), kind 별 params, m = W / w_m 가 실제로 갈린다:
    toy 선언은 drain/source·nmos/pmos 값이 모두 다르므로 쪽·bias·kind 를 바꾼 대안 식과는 값이 어긋나야 한다."""
    snap, ops = _snap(tmp_path)
    js = _js(decl_paths, lut_a)
    col = dict(ss_dev(snap, lut_access(lut_a), js).column("device", "ss_dev"))
    op = ops["M1"]
    ss = col["M1"]
    swapped_bias = oracle_junction(dataclasses.replace(op, vds=op.vds - op.vsb))   # v_db = vds 로 잘못 쓴 경우
    other_kind = oracle_junction(dataclasses.replace(op, kind="pmos"))
    m_one = oracle_junction(dataclasses.replace(op, W=LUT_WM))
    for alt in (swapped_bias, other_kind):
        assert not rel_close(ss.cdb, alt[0], 1e-6), alt
    assert not rel_close(ss.csb, other_kind[1], 1e-6)
    assert rel_close(ss.cdb, m_one[0] * op.W / LUT_WM, JUNCTION_RTOL)      # 소자 전체 = m 배
    assert ss.cdb != ss.csb


def test_values_old_lut_secant_and_cap_fallback(tmp_path, lut_b, decl_paths):
    """GMBS 열 없는 옛 LUT: gmb = r5 VS 칸 할선(GMB_VS_CELL_SECANT), 용량 cgs = cgg − cgd, cgb = 0. 접합 용량은 LUT 와 무관."""
    snap, ops = _snap(tmp_path)
    js = _js(decl_paths, lut_b)
    col = dict(ss_dev(snap, lut_access(lut_b), js).column("device", "ss_dev"))
    for m, op in ops.items():
        _check(col[m], oracle_ss(op, "secant", "cgg_minus_cgd_at_gs"), op, js)
        assert col[m].gmb_model == GMB_VS_CELL_SECANT == "lut_vs_cell_secant"
        assert col[m].cap_model == "cgg_minus_cgd_at_gs"


def test_gmb_column_from_cap_table(tmp_path, lut_c, decl_paths):
    """슬라이스에 열이 없어도 기준 LUT w_key == op.w_key 이고 GMBS_PER_ID 가 있으면 GMB_COLUMN(lut 4.3 출처 규칙)."""
    snap, ops = _snap(tmp_path)
    col = dict(ss_dev(snap, lut_access(lut_c), _js(decl_paths, lut_c)).column("device", "ss_dev"))
    for m, op in ops.items():
        exp = oracle_ss(op, "cap", "lut_cgs_cgb")
        assert col[m].gmb_model == GMB_COLUMN
        assert rel_close(col[m].gmb, exp["gmb"], 1e-12), (col[m].gmb, exp["gmb"])
        # 슬라이스 출처 계수로 계산한 값과는 다르다(출처를 실제로 기준 LUT 에서 읽었다)
        assert not rel_close(col[m].gmb, oracle_ss(op, "slice")["gmb"], 1e-6)


def test_gmb_secant_differs_from_column(tmp_path, lut_a, lut_b, decl_paths):
    """두 gmb 정의가 이 점에서 실제로 다른 값이다(모형 표시가 값과 함께 바뀐다는 확인의 전제)."""
    snap, _ = _snap(tmp_path)
    a = ss_dev(snap, lut_access(lut_a), _js(decl_paths, lut_a)).value("device", "M1", "ss_dev").gmb
    b = ss_dev(snap, lut_access(lut_b), _js(decl_paths, lut_b)).value("device", "M1", "ss_dev").gmb
    assert not rel_close(a, b, 1e-3)


@pytest.mark.parametrize("case", ["caps_vs_axis", "op_point_vds_axis", "op_point_l_not_anchor"])
def test_lut_failure_is_seal_violation(tmp_path, tmp_path_factory, decl_paths, case):
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
        ss_dev(snap, lut_access(lut), _js(decl_paths, lut))
    rec = ei.value.record
    det = dict(rec.detail)
    assert rec.devices == ("M1",)
    assert det["reason"] == "lut_query_failed"
    assert (det["device_query"], det["lut_reason"]) == want


def test_negative_check_valid_point_does_not_raise(tmp_path, tmp_path_factory, decl_paths):
    """위 실패 test 의 대조: 좁은 VS 축 LUT 라도 축 안 점이면 예외 없이 값이 나온다(실패가 축 밖 때문임을 확인)."""
    lut = load_lut_v2(tmp_path_factory.mktemp("lut_narrow_ok"), cap_vs=(-0.45, 0.0, 0.45, 0.9))
    snap, ops = _snap(tmp_path)
    js = _js(decl_paths, lut)
    col = dict(ss_dev(snap, lut_access(lut), js).column("device", "ss_dev"))
    _check(col["M1"], oracle_ss(ops["M1"], "slice", "lut_cgs_cgb"), ops["M1"], js)


@pytest.mark.parametrize("case", ["weffcj_zero", "pb_t_nonpositive"])
def test_junction_value_error_propagates_unwrapped(tmp_path, lut_a, case):
    """7.2: junction_caps 의 ValueError(Weffcj ≤ 0, 보정 뒤 PB ≤ 0)는 그대로 전파 -- SealViolationError 로 감싸지 않는다."""
    params = {k: dict(v) for k, v in TOY_JUNCTION.items()}
    if case == "weffcj_zero":
        params["nmos"]["dwj"] = LUT_WM / 2           # Weffcj = w_m − 2·dwj = 0
    else:
        params["pmos"]["tpb"] = 0.4                  # ΔT = 27 − 20 = 7 -> PB(T) = 0.66 − 0.4·7 < 0
        params["pmos"]["tnom"] = 20.0
    js = toy_junction(tmp_path / "j", lut_a, params=params)
    snap, _ = _snap(tmp_path)
    with pytest.raises(ValueError) as ei:
        ss_dev(snap, lut_access(lut_a), js)
    assert not isinstance(ei.value, SealViolationError), ei.value


def test_negative_check_junction_ok_params_do_not_raise(tmp_path, lut_a):
    """위 전파 test 의 대조: 같은 경로에서 dwj 만 w_m/2 바로 아래면 예외 없이 값(실패가 그 파라미터 때문임을 확인)."""
    params = {k: dict(v) for k, v in TOY_JUNCTION.items()}
    params["nmos"]["dwj"] = LUT_WM / 2 * 0.99
    js = toy_junction(tmp_path / "j", lut_a, params=params)
    snap, ops = _snap(tmp_path)
    ss = ss_dev(snap, lut_access(lut_a), js).value("device", "M1", "ss_dev")
    cdb, csb = oracle_junction(ops["M1"], params=params)
    assert rel_close(ss.cdb, cdb, JUNCTION_RTOL) and rel_close(ss.csb, csb, JUNCTION_RTOL)


def test_reuse_and_recompute(tmp_path, lut_a, decl_paths):
    """S-6: 같은 dc_op·LUT·접합 묶음 -> 재사용(`is`, computes 0). dc_op 하나 바꾸면 블록 재계산 1회, recomputes_same_input 0."""
    acc = lut_access(lut_a)
    js = _js(decl_paths, lut_a)
    snap, ops = _snap(tmp_path)
    ss_dev.reset_stats()
    s1 = ss_dev(snap, acc, js)
    s2 = ss_dev(s1, acc, js)
    assert s2 is s1
    st = ss_dev.stats()
    assert (st.calls, st.computes, st.reuses) == (2, 1, 1)
    # 읽지 않는 열(dc_L)만 바뀐 스냅샷에서도 재사용
    s3 = hand_write(s1, "device", "dc_L", {"M1": 1e-6, "M2": 2e-6})
    assert ss_dev(s3, acc, js) is s3
    # M1 의 dc_op 만 바꿈 -> 재계산, 새 값은 새 op 의 식
    new = dict(ops)
    op1 = ops["M1"]
    new["M1"] = device_op(op1.kind, op1.L, 0.66, op1.vds, op1.vsb, op1.W, op1.current, op1.gm_id)
    s4 = hand_write(s1, "device", "dc_op", new, version="hand2")
    s5 = ss_dev(s4, acc, js)
    assert s5 is not s4
    _check(s5.value("device", "M1", "ss_dev"), oracle_ss(new["M1"], "slice"), new["M1"], js)
    st = ss_dev.stats()
    assert st.computes == 2 and st.recomputes_same_input == 0


def test_s12_temp_change_recomputes_once_same_bundle_reuses(tmp_path, lut_a, decl_paths):
    """S-12: temp_c 만 바꾼 묶음 -> computes +1(값 = 그 온도의 8.2 식), 같은 파일에서 따로 만든 같은 묶음 -> computes 0."""
    acc = lut_access(lut_a)
    js = _js(decl_paths, lut_a)
    snap, ops = _snap(tmp_path)
    s1 = ss_dev(snap, acc, js)
    ss_dev.reset_stats()
    js_same = _js(decl_paths, lut_a)                 # 따로 읽은 같은 선언·같은 LUT -> 같은 묶음
    assert js_same is not js and fp_of(js_same) == fp_of(js)
    assert ss_dev(s1, acc, js_same) is s1
    assert (ss_dev.stats().computes, ss_dev.stats().reuses) == (0, 1)
    js_t = dataclasses.replace(js, temp_c=js.temp_c + 10.0)
    s2 = ss_dev(s1, acc, js_t)
    st = ss_dev.stats()
    assert s2 is not s1
    assert (st.computes, st.recomputes_same_input) == (1, 0)
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    for m, op in ops.items():
        _check(s2.value("device", m, "ss_dev"), oracle_ss(op, "slice"), op, js_t, temp_c=37.0)
        assert s2.value("device", m, "ss_dev").cdb != s1.value("device", m, "ss_dev").cdb
    # 다시 같은 묶음(js_t)으로 -> 재사용
    assert ss_dev(s2, acc, js_t) is s2
    assert ss_dev.stats().computes == 1 and ss_dev.stats().recomputes_same_input == 0


@pytest.mark.parametrize("field", ["params_other_pdk_decl", "lut_rule_decl", "pdk_decl_sha256"])
def test_s12_each_bundle_field_changes_input_version(tmp_path, lut_a, decl_paths, field):
    """S-12 / 7.2: 접합 파라미터(다른 PDK 선언)·LUT 규칙 선언·PDK 선언 sha256 중 하나만 바뀌어도 ss_dev 재계산."""
    acc = lut_access(lut_a)
    js = _js(decl_paths, lut_a)
    snap, ops = _snap(tmp_path)
    s1 = ss_dev(snap, acc, js)
    params, rule = None, None
    if field == "params_other_pdk_decl":
        params = {k: dict(v) for k, v in TOY_JUNCTION.items()}
        params["nmos"]["cjd"] *= 1.5
        js2 = toy_junction(tmp_path / "j2", lut_a, params=params)
        assert js2.pdk_decl_sha256 != js.pdk_decl_sha256
    elif field == "lut_rule_decl":
        line = "xdut d g s b dev l=1e-6 w=4e-6 ad=3e-12 as=1.2e-12 pd=9e-6 ps=7e-6"
        js2 = toy_junction(tmp_path / "j2", lut_a, rule_line=line)
        rule = toy_rule_values(line)
        assert js2.params == js.params or fp_of(js2.params) == fp_of(js.params)
    else:
        js2 = dataclasses.replace(js, pdk_decl_sha256="0" * 64)
    ss_dev.reset_stats()
    s2 = ss_dev(s1, acc, js2)
    st = ss_dev.stats()
    assert s2 is not s1 and (st.computes, st.recomputes_same_input) == (1, 0)
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    for m, op in ops.items():
        _check(s2.value("device", m, "ss_dev"), oracle_ss(op, "slice"), op, js2, params=params, rule=rule)
    if field == "pdk_decl_sha256":                   # 출처만 바뀜 -> 값은 같다(재계산은 지문 때문)
        assert fp_of(s2.column("device", "ss_dev")) == fp_of(s1.column("device", "ss_dev"))
    else:
        assert s2.value("device", "M1", "ss_dev").cdb != s1.value("device", "M1", "ss_dev").cdb


def test_lut_temperature_is_junction_temperature(tmp_path, decl_paths):
    """7.2: temp_c = LUT 측정 온도(cap_conditions) -- 60 °C LUT 의 묶음으로 계산한 cdb·csb = 60 °C 의 8.2 식."""
    lut60 = load_lut_v2(tmp_path / "lut60", temp_c=60.0)
    js = _js(decl_paths, lut60)
    assert js.temp_c == 60.0
    snap, ops = _snap(tmp_path)
    col = dict(ss_dev(snap, lut_access(lut60), js).column("device", "ss_dev"))
    for m, op in ops.items():
        _check(col[m], oracle_ss(op, "slice"), op, js, temp_c=60.0)
        assert not rel_close(col[m].cdb, oracle_junction(op, temp_c=27.0)[0], 1e-6)


def test_lut_content_changes_input_version(tmp_path, lut_a, lut_b, decl_paths):
    """extras(LutAccess) 지문은 LUT 내용을 따른다 -> 다른 LUT 로 부르면 재사용하지 않는다. memo 만 새것이면 재사용."""
    snap, _ = _snap(tmp_path)
    js = _js(decl_paths, lut_a)
    s1 = ss_dev(snap, lut_access(lut_a), js)
    s2 = ss_dev(s1, lut_access(lut_b), _js(decl_paths, lut_b))
    assert s2 is not s1
    assert s2.block_version(SS_DEV_WRITER) != s1.block_version(SS_DEV_WRITER)
    assert ss_dev(s1, lut_access(lut_a), js) is s1


def test_determinism(tmp_path, tmp_path_factory):
    """같은 입력(따로 만든 LUT·memo·선언 파일) 두 번 -> ss_dev 열 값 지문 동일."""
    fps = []
    for i in range(2):
        lut = load_lut_v2(tmp_path_factory.mktemp("lut_det%d" % i))
        js = toy_junction(tmp_path_factory.mktemp("jdet%d" % i), lut)
        snap, _ = _snap(tmp_path / ("d%d" % i))
        fps.append(fp_of(ss_dev(snap, lut_access(lut), js).column("device", "ss_dev")))
    assert fps[0] == fps[1]
