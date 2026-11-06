"""`metrics_dc` 계산 블록(레일 전류·전력·탐색 축 면적) -- metrics CONTRACT 7.5 (+ 3.13·3.14, 7.7 S-9, 7.9 Q4).

입력: 3레일 손 회로(vdd 1.8, vmid 0.9, gnd 0). 계획 블록 결과(dc_rail_v·dc_current_basis)는 sizing build_kernel_context 의
ctx.base 에서 받고, 평가 결과 열(dc_current·dc_v·dc_op)은 권한표 writer 로 손으로 쓴다.
기대값(손계산): I_vdd = M2 10 µA + R1 (1.8 − 1.3)/100 kΩ = 15 µA, I_vmid = I1 2 µA, I_gnd = −(M1 10 + M4 5 + M3 2) µA = −17 µA,
power = 1.8·15 + 0.9·2 = 28.8 µW, 잔차 0.
"""
from __future__ import annotations

import pytest

from gmid_engine.metrics import MetricRequest, metrics_dc, ss_dev
from gmid_engine.sizing import METRICS_DC_WRITER, METRICS_KEY, S2_WRITERS, DcInputs, build_kernel_context

from .conftest import (
    block_row,
    device_op,
    fresh_run,
    hand_ss,
    hand_write,
    load_lut_v2,
    lut_access,
    rel_close,
    topo_doc,
    topo_only,
    with_ss,
)

SUP = {"vdd": 1.8, "vmid": 0.9, "gnd": 0.0}
CUR = {"M1": 10e-6, "M2": 10e-6, "M4": 5e-6, "R1": 5e-6, "I1": 2e-6, "M3": 2e-6}
VOLT = {"in": 0.6, "out": 0.8, "pb": 1.0, "x": 1.3, "y": 0.5}
WL = {"M1": (2e-6, 1e-6), "M2": (4e-6, 2e-6), "M3": (1e-6, 1e-6), "M4": (3e-6, 1e-6)}
R1 = 1e5
EXP_RAIL = {"vdd": 15e-6, "vmid": 2e-6, "gnd": -17e-6}
EXP_POWER = 1.8 * 15e-6 + 0.9 * 2e-6
EXP_AREA = sum(w * l for w, l in WL.values())


def _topo():
    return topo_doc(
        "dcm_three_rail",
        mos=[("M1", "nmos", "out", "in", "gnd", "gnd"), ("M2", "pmos", "out", "pb", "vdd", "vdd"),
             ("M4", "nmos", "x", "in", "gnd", "gnd"), ("M3", "nmos", "y", "y", "gnd", "gnd")],
        passives=[("R1", "resistor", "vdd", "x"), ("CL", "capacitor", "out", "gnd")],
        sources=[("I1", "current_source", "vmid", "y")], rails=("vdd", "vmid", "gnd"),
        bias=["pb"])                                          # pb: M2 gate 에만 (authoring 9절 입력 선언)


@pytest.fixture(scope="module")
def snap(tmp_path_factory):
    from gmid_engine.graph import build_s1
    td = topo_only(tmp_path_factory.mktemp("dcm"), _topo())
    lut = load_lut_v2(tmp_path_factory.mktemp("dcm_lut"))
    inputs = DcInputs(tuple(sorted(SUP.items())), element_values=(("CL", None), ("I1", 2e-6), ("R1", None)))
    run = fresh_run()                 # [XRUN-F1 card B] 지역 실행 -- 손 입력 스냅샷만 돌려준다(두 객체는 남기지 않는다)
    ctx = build_kernel_context(build_s1(td, SUP, **run), inputs, lut_access(lut), **run)
    s = ctx.base
    s = hand_write(s, "device", "dc_current", CUR)
    s = hand_write(s, "node", "dc_v", VOLT)
    # [dispute 7.4, 계약 23] MOS 채널 레일 전류의 전력 축 = `DeviceOp.current` 이므로 손 dc_op 전류를 같은 소자의 손 dc_current(CUR, 위 기대 주석의 출처)와 같게 둔다
    # (device_op 기본 10 µA 면 gnd 레일이 -30 µA 가 되어 기대 -17 µA 와 어긋난다). 기대값(EXP_RAIL)은 그대로.
    ops = {m: device_op("pmos" if m == "M2" else "nmos", l, 0.7, 0.9, 0.0, w, current=CUR[m]) for m, (w, l) in WL.items()}
    return hand_write(s, "device", "dc_op", ops)


def with_passive_value(s, passives):
    """[U17 ①] 수동소자 값은 S2 필드 `device.passive_value`(설계 40 §2.4.8, writer = 권한표 writer_of) -- 손 값을 그 필드로 쓴다
    (블록 입력 버전은 읽는 열 값의 지문이라 version 표지는 임의)."""
    return hand_write(s, "device", "passive_value", dict(passives), version="hand_pv:%r" % (tuple(sorted(passives)),))


def _bundle(s, passives=(("CL", 1e-12), ("R1", R1)), counted=(), run=None):
    """run = 실행 두 객체 키워드(dict, card B C4), 없으면 새 실행 하나."""
    out = metrics_dc(with_passive_value(s, passives), counted, **(run if run is not None else fresh_run()))
    return out, out.value("graph", METRICS_KEY, "metrics_dc")


def _entries(b):
    return {q.metric: r for q, r in b.entries}


def test_block_declaration():
    assert metrics_dc.name == METRICS_DC_WRITER == S2_WRITERS.writer_of("graph", "metrics_dc") == "metrics_dc"
    # [U17 ①] reads = 종전 7.5 읽기 열(설계가 바꾸지 않음) ∪ 설계 40 v1.6 §2.4.7 Objectives 행의 b_P 입력(dc_gm·dc_tol_v·
    # dc_current_basis·dc_rail_v) ∪ §2.4.8 '수동소자 값 | device: passive_value | ... 엔진이 이 필드를 읽는다'(DC 저항 값·면적 항).
    assert set(metrics_dc.reads) == {("device", "dc_op"), ("device", "dc_current"), ("device", "element_class"),
                                     ("device", "pins"), ("node", "dc_v"), ("node", "dc_rail_v"),
                                     ("graph", "dc_current_basis"),
                                     ("device", "dc_colour"), ("node", "dc_colour"),    # [r12] 합산·나열 순서 = dc_colour(CONTRACT r12)
                                     ("device", "dc_gm"), ("device", "dc_tol_v"),       # [U17 ①] b_P 입력(§2.4.7)
                                     ("device", "passive_value")}                       # [U17 ①] 수동소자 값 필드(§2.4.8)
    # [U17 ①] §2.4.8 소유표 '게이트 면적·전력 분해능 | graph/metrics: gate_area_m2, power_resolution_w | metrics_dc'
    assert set(metrics_dc.writes) == {("graph", "metrics_dc"), ("graph", "gate_area_m2"), ("graph", "power_resolution_w")}
    # ss 값은 읽지 않는다(7.10 3: ss 변경에 재계산되지 않게)
    assert ("device", "ss_dev") not in set(metrics_dc.reads)


def test_entries_order_and_views(snap):
    _, b = _bundle(snap, counted=("vdd",))
    assert [q for q, _ in b.entries] == [MetricRequest("power_dc_w", None), MetricRequest("supply_current_dc", None),
                                         MetricRequest("area_search_m2", None)]


def test_power_over_all_declared_rails(snap):
    """Q4: power_dc_w = 선언된 모든 공급 레일의 Σ V_k·I_k -- counted_rails 선언과 무관."""
    vals = []
    for counted in ((), ("vdd",), ("vdd", "vmid")):
        _, b = _bundle(snap, counted=counted)
        p = _entries(b)["power_dc_w"]
        assert p.undefined == () or not p.undefined
        assert rel_close(p.value, EXP_POWER, 1e-12), (counted, p.value)
        vals.append(p.value)
    assert vals[0] == vals[1] == vals[2]


def test_supply_current_counted_rails(snap):
    """supply_current_dc = Σ_{k ∈ counted_rails} I_k."""
    _, b1 = _bundle(snap, counted=("vdd",))
    assert rel_close(_entries(b1)["supply_current_dc"].value, 15e-6, 1e-12)
    _, b2 = _bundle(snap, counted=("vdd", "vmid"))
    assert rel_close(_entries(b2)["supply_current_dc"].value, 17e-6, 1e-12)


def test_supply_current_undefined_without_counted_rails(snap):
    """counted_rails == () -> supply_current_dc 값 None + Undefined(supply_current_dc, counted_rails_undeclared,
    definitional), 예외 없음. 전력·면적은 값이 있다."""
    _, b = _bundle(snap, counted=())
    e = _entries(b)
    r = e["supply_current_dc"]
    assert r.value is None
    assert [(u.quantity, u.code, u.category) for u in r.undefined] == [
        ("supply_current_dc", "counted_rails_undeclared", "definitional")]
    assert e["power_dc_w"].value is not None and e["area_search_m2"].value is not None
    assert dict(b.detail)["counted_rails"] == ()


@pytest.mark.parametrize("bad", [("nope",), ("out",), ("vdd", "vdd")], ids=["unknown_net", "non_rail_net", "duplicate"])
def test_counted_rails_invalid_rejected(snap, bad):
    """합산 레일 선언이 레일 밖·중복이면 ValueError(2절 표: '합산 레일 선언' 결함은 ValueError, KeyError 는 미등록 metric
    이름 전용; 3.13 '레일 밖·중복은 ValueError'). 회로에 없는 넷 이름도 '레일 밖'이다."""
    with pytest.raises(ValueError):
        _bundle(snap, counted=bad)


def test_s9_per_rail_and_kcl_residual(snap):
    """S-9: per_rail 합 = kcl_residual(≈ 0), power = Σ V_k·I_k(per_rail 로 다시 계산)."""
    _, b = _bundle(snap, counted=("vdd",))
    d = dict(b.detail)
    assert [k for k, _ in b.detail] == sorted(d)
    assert set(d) == {"counted_rails", "kcl_residual_amp", "passive_area_undeclared", "passive_value_missing",
                      "per_rail_amp"}
    per = dict(d["per_rail_amp"])
    assert set(per) == set(SUP)
    for k, v in EXP_RAIL.items():
        assert rel_close(per[k], v, 1e-12, 1e-21), (k, per[k], v)
    assert abs(d["kcl_residual_amp"] - sum(per.values())) <= 1e-21
    assert abs(d["kcl_residual_amp"]) <= 1e-18
    assert rel_close(_entries(b)["power_dc_w"].value, sum(SUP[k] * per[k] for k in per), 1e-12)


def test_area_and_passive_records(snap):
    """area_search_m2 = Σ W·L(MOS dc_op) -- 수동소자는 단위 면적 None 이라 미선언 목록으로."""
    _, b = _bundle(snap, counted=("vdd",))
    assert rel_close(_entries(b)["area_search_m2"].value, EXP_AREA, 1e-12)
    d = dict(b.detail)
    assert tuple(d["passive_area_undeclared"]) == ("CL", "R1")
    assert tuple(d["passive_value_missing"]) == ()
    _, b2 = _bundle(snap, passives=(("R1", R1),), counted=("vdd",))
    d2 = dict(b2.detail)
    assert tuple(d2["passive_value_missing"]) == ("CL",)
    assert tuple(d2["passive_area_undeclared"]) == ("R1",)
    assert rel_close(_entries(b2)["area_search_m2"].value, EXP_AREA, 1e-12)


def test_resistor_value_drives_rail_current(snap):
    """R1 값이 바뀌면 그 저항 전류(노드 전압 차 / R)가 따라 바뀐다 -- 값은 passive_values 에서 읽는다."""
    _, b = _bundle(snap, passives=(("CL", 1e-12), ("R1", 2 * R1)), counted=("vdd",))
    per = dict(dict(b.detail)["per_rail_amp"])
    assert rel_close(per["vdd"], 10e-6 + 0.5 / (2 * R1), 1e-12)


def test_reuse_and_independence_from_ss(snap):
    """같은 입력 -> `is`. ss_dev 열만 바뀐 스냅샷 -> 재사용(소신호 값을 읽지 않음). counted_rails 가 바뀌면 재계산."""
    # oracle 대조: card B C4 판정 1·4 -- 손 순서(compute, reuse, reuse, compute)의 실행 계수(C1) 행
    run = fresh_run()
    s1, _ = _bundle(snap, counted=("vdd",), run=run)
    s2, _ = _bundle(s1, counted=("vdd",), run=run)
    assert s2 is s1
    s3 = with_ss(s1, {m: hand_ss(1e-3, 1e-5) for m in WL})
    s4, _ = _bundle(s3, counted=("vdd",), run=run)
    assert s4 is s3
    s5, _ = _bundle(s4, counted=("vdd", "vmid"), run=run)
    assert s5 is not s4
    assert block_row(run["counters"], metrics_dc.name) == (4, 2, 0, 0, 2, 0)


def test_ss_dev_not_required(snap):
    """metrics_dc 는 ss_dev 없이도 돈다(입력 스냅샷에 ss_dev 열 없음) -- 블록 순서의 독립성."""
    assert snap.column("device", "ss_dev") == ()
    _bundle(snap, counted=("vdd",))
    assert ss_dev.name != metrics_dc.name


def test_power_area_resolution_none(snap):
    """[9절] 7.5: 전력·면적 결과의 resolution 은 None(LUT 소신호 불확실성 전파 대상 아님) -- 값이 있어도."""
    _, b = _bundle(snap, counted=("vdd",))
    e = _entries(b)
    assert set(e) == {"power_dc_w", "supply_current_dc", "area_search_m2"}
    for name, r in e.items():
        assert r.value is not None, name
        assert r.resolution is None, name


# ---------------------------------------------------------------- [사용자 결정 11, 2026-10-08] 네 번째 extra area_decl (7.5)
# oracle (a) 구성으로 정해진 합성 입력: 손 회로 CL = 1 pF, R1 = 100 kΩ, 단위 면적 U_C = 1/(2e-3 F/m²) = 500 m²/F(이 test 가 고른 값)
# -> 면적 = Σ W·L(EXP_AREA, 손 표) + CL·U_C = EXP_AREA + 5e-10. excluded 소자는 면적 항·미선언 목록 둘 다에서 빠진다(계약 문장).

U_C = 1.0 / 2e-3                        # m²/F -- 2 fF/µm² 의 역수(구성 값)
CL_F = 1e-12


def _bundle_decl(s, decl, passives=(("CL", CL_F), ("R1", R1)), counted=("vdd",), run=None):
    out = metrics_dc(with_passive_value(s, passives), counted, decl, **(run if run is not None else fresh_run()))
    return out, out.value("graph", METRICS_KEY, "metrics_dc")


# ---------------------------------------------------------------- [U17 ①] graph/metrics 필드 gate_area_m2·power_resolution_w
# 설계 40 v1.6 §2.4.7 Objectives 행·§2.4.8 소유표: metrics_dc 가 gate_area_m2(Σ dc_op W·L)와 power_resolution_w(b_P = Σ_레일 |V_k|·tol_I,k,
# tol_I,k = 채널 끝이 레일 k 인 MOS 의 dc_tol_v × dc_gm 최댓값, 정의된 행 없음·합 0 -> None)를 쓴다. 손 회로: vdd 1.8 V 에 채널이 닿는
# MOS 는 M2 뿐(R1 은 저항, I1 은 vmid 의 이상원), gnd 0 V 는 기여 0, vmid 0.9 V 는 채널 없음(행 없음).

TOL_V = {"M1": 0.01, "M2": 0.02, "M3": None, "M4": 0.005}          # 손 tol_V 셀(M3 미정) -- writer dc_tolerances 로 쓴다


def _with_tol_gm(s):
    ops = dict(s.column("device", "dc_op"))
    gm = {m: o.gm_id * o.current for m, o in ops.items()}          # 설계 §3.7-3 dc_gm 정의 = ID × gm/ID(손 dc_op 의 값)
    s = hand_write(s, "device", "dc_tol_v", TOL_V, version="hand_tol")
    return hand_write(s, "device", "dc_gm", gm, version="hand_gm"), gm


def test_u17_gate_area_and_power_resolution_fields(snap):
    s, gm = _with_tol_gm(snap)
    out = metrics_dc(with_passive_value(s, (("CL", CL_F), ("R1", R1))), ("vdd",), **fresh_run())
    assert S2_WRITERS.writer_of("graph", "gate_area_m2") == S2_WRITERS.writer_of("graph", "power_resolution_w") == "metrics_dc"
    assert rel_close(out.value("graph", METRICS_KEY, "gate_area_m2"), EXP_AREA, 1e-12)
    want = 1.8 * TOL_V["M2"] * gm["M2"]                            # 손: vdd 행만 정의, max over {M2}
    assert rel_close(out.value("graph", METRICS_KEY, "power_resolution_w"), want, 1e-12)
    assert rel_close(want, 1.8 * 0.02 * 12.0 * 10e-6, 1e-12)        # = 4.32e-6 W


def test_u17_power_resolution_none_without_defined_rows(snap):
    """dc_tol_v 열이 없거나(합산할 행 없음) 레일에 닿는 MOS 의 tol 이 모두 None 이면 power_resolution_w = None; gate_area 는 그대로."""
    out = metrics_dc(with_passive_value(snap, (("CL", CL_F), ("R1", R1))), ("vdd",), **fresh_run())
    assert out.value("graph", METRICS_KEY, "power_resolution_w") is None
    assert rel_close(out.value("graph", METRICS_KEY, "gate_area_m2"), EXP_AREA, 1e-12)
    s, _gm = _with_tol_gm(snap)
    s = hand_write(s, "device", "dc_tol_v", {"M1": 0.01, "M2": None, "M3": None, "M4": 0.005}, version="hand_tol2")
    out2 = metrics_dc(with_passive_value(s, (("CL", CL_F), ("R1", R1))), ("vdd",), **fresh_run())
    assert out2.value("graph", METRICS_KEY, "power_resolution_w") is None     # gnd 0 V 행만 정의 -> 합 0 -> None


def test_area_decl_absent_equals_old_and_empty_decl(snap):
    """area_decl 없음 = 종전 동작(값 있는 수동소자 전부 미선언, 면적 = Σ W·L) -- 빈 PassiveAreaDecl() 과 값이 비트 단위로 같다."""
    from gmid_engine.metrics import PassiveAreaDecl
    _, b0 = _bundle(snap, counted=("vdd",))
    _, b1 = _bundle_decl(snap, PassiveAreaDecl())
    e0, e1 = _entries(b0), _entries(b1)
    for k in ("power_dc_w", "supply_current_dc", "area_search_m2"):
        assert e0[k].value == e1[k].value, k
    assert b0.detail == b1.detail
    assert tuple(dict(b0.detail)["passive_area_undeclared"]) == ("CL", "R1")
    assert rel_close(e0["area_search_m2"].value, EXP_AREA, 1e-12)


def test_area_decl_unit_area_adds_capacitor_area(snap):
    from gmid_engine.metrics import PassiveAreaDecl
    _, b = _bundle_decl(snap, PassiveAreaDecl(unit_area=(("CL", U_C),)))
    assert rel_close(_entries(b)["area_search_m2"].value, EXP_AREA + CL_F * U_C, 1e-12)
    assert tuple(dict(b.detail)["passive_area_undeclared"]) == ("R1",)       # 저항은 단위 면적 미선언 -> 보고


def test_area_decl_excluded_capacitor_not_in_area_nor_undeclared(snap):
    from gmid_engine.metrics import PassiveAreaDecl
    _, b = _bundle_decl(snap, PassiveAreaDecl(excluded=("CL",)))
    assert rel_close(_entries(b)["area_search_m2"].value, EXP_AREA, 1e-12)
    assert tuple(dict(b.detail)["passive_area_undeclared"]) == ("R1",)


def test_area_decl_excluded_resistor_keeps_power(snap):
    """측정 부하 저항을 면적에서 빼도 전력·레일 전류는 그대로(저항 값은 DC 해에 그대로 쓰인다) -- 면적만의 선언이다."""
    from gmid_engine.metrics import PassiveAreaDecl
    _, b0 = _bundle(snap, counted=("vdd",))
    _, b = _bundle_decl(snap, PassiveAreaDecl(unit_area=(("CL", U_C),), excluded=("R1",)))
    e0, e = _entries(b0), _entries(b)
    assert e["power_dc_w"].value == e0["power_dc_w"].value
    assert dict(b.detail)["per_rail_amp"] == dict(b0.detail)["per_rail_amp"]
    assert tuple(dict(b.detail)["passive_area_undeclared"]) == ()
    assert rel_close(e["area_search_m2"].value, EXP_AREA + CL_F * U_C, 1e-12)


def test_area_decl_is_block_input(snap):
    """area_decl 이 바뀌면 재계산(옛 면적 재사용 금지), 같은 area_decl 이면 재사용."""
    from gmid_engine.metrics import PassiveAreaDecl
    run = fresh_run()                 # oracle 대조: 손 순서(compute, compute, reuse)의 실행 계수(card B C1) 행
    s1, b1 = _bundle_decl(snap, PassiveAreaDecl(), run=run)
    s2, b2 = _bundle_decl(s1, PassiveAreaDecl(unit_area=(("CL", U_C),)), run=run)
    assert s2 is not s1
    assert _entries(b2)["area_search_m2"].value != _entries(b1)["area_search_m2"].value
    s3, _ = _bundle_decl(s2, PassiveAreaDecl(unit_area=(("CL", U_C),)), run=run)
    assert s3 is s2
    assert block_row(run["counters"], metrics_dc.name) == (3, 1, 0, 0, 2, 0)


# ---------------------------------------------------------------- [LM-1e §5 P-1] 전력 분해능: 레일 항에 None 이 있으면 None
# 계획 N3.6 표 10행·interface §5: power_resolution_w = Σ_레일 |V_k|·tol_I,k 의 레일 항 중 하나라도 None 이면 None(정의된 항만 합하지 않는다).
# 입력 = J-a 스냅샷(toy R + `_scc_s_doc`, M3 의 dc_op.vds = 0.1 -> `dc_tolerances` 가 `table_at` 으로 dc_tol_v["M3"] = None; 주입 없음).
# M3 는 pmos (vout, pb, vdd) 라 채널이 vdd 레일에 닿는다 -> 그 레일 항이 None. oracle (d)(식) + 대조(바꾸기 전과 같은 회로, vds 0.5 -> 값).

def test_lm1e_p1_power_resolution_none_when_rail_term_is_none(tmp_path):
    from gmid_engine.sizing import DC_KEY
    from sizing.conftest import ja_state, run_of
    ctx, _th, _changed, snap = ja_state(tmp_path / "none")
    tolv = dict(snap.column("device", "dc_tol_v"))
    assert tolv["M3"] is None and tolv["M1"] is not None and tolv["M2"] is not None          # 전제 (J-a)
    basis = snap.value("graph", DC_KEY, "dc_current_basis")
    assert any(name == "M3" and "vdd" in (f, t) for name, f, t in basis.ends)                # M3 채널이 vdd 레일에 닿는다
    out = metrics_dc(snap, (), **run_of(ctx))
    assert out.value("graph", METRICS_KEY, "power_resolution_w") is None
    # 대조: M3 의 vds 만 0.5 (칸 [0.5, 0.75) -- 켜진 칸)로 바꾸면 모든 레일 항이 정의 -> 값(전제: tol 모두 정의)
    ctx2, _th2, _c2, snap2 = ja_state(tmp_path / "defined", vds=0.5)
    assert all(v is not None for v in dict(snap2.column("device", "dc_tol_v")).values())
    val = metrics_dc(snap2, (), **run_of(ctx2)).value("graph", METRICS_KEY, "power_resolution_w")
    assert val is not None and val > 0.0
