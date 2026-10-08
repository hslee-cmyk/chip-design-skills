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
    device_op,
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
    ctx = build_kernel_context(build_s1(td, SUP), inputs, lut_access(lut))
    s = ctx.base
    s = hand_write(s, "device", "dc_current", CUR)
    s = hand_write(s, "node", "dc_v", VOLT)
    ops = {m: device_op("pmos" if m == "M2" else "nmos", l, 0.7, 0.9, 0.0, w) for m, (w, l) in WL.items()}
    return hand_write(s, "device", "dc_op", ops)


def _bundle(s, passives=(("CL", 1e-12), ("R1", R1)), counted=()):
    out = metrics_dc(s, passives, counted)
    return out, out.value("graph", METRICS_KEY, "metrics_dc")


def _entries(b):
    return {q.metric: r for q, r in b.entries}


def test_block_declaration():
    assert metrics_dc.name == METRICS_DC_WRITER == S2_WRITERS.writer_of("graph", "metrics_dc") == "metrics_dc"
    assert set(metrics_dc.reads) == {("device", "dc_op"), ("device", "dc_current"), ("device", "element_class"),
                                     ("device", "pins"), ("node", "dc_v"), ("node", "dc_rail_v"),
                                     ("graph", "dc_current_basis")}
    assert tuple(metrics_dc.writes) == (("graph", "metrics_dc"),)
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
    metrics_dc.reset_stats()
    s1, _ = _bundle(snap, counted=("vdd",))
    s2, _ = _bundle(s1, counted=("vdd",))
    assert s2 is s1
    s3 = with_ss(s1, {m: hand_ss(1e-3, 1e-5) for m in WL})
    s4, _ = _bundle(s3, counted=("vdd",))
    assert s4 is s3
    s5, _ = _bundle(s4, counted=("vdd", "vmid"))
    assert s5 is not s4
    st = metrics_dc.stats()
    assert (st.computes, st.reuses, st.recomputes_same_input) == (2, 2, 0)


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


def _bundle_decl(s, decl, passives=(("CL", CL_F), ("R1", R1)), counted=("vdd",)):
    out = metrics_dc(s, passives, counted, decl)
    return out, out.value("graph", METRICS_KEY, "metrics_dc")


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
    metrics_dc.reset_stats()
    s1, b1 = _bundle_decl(snap, PassiveAreaDecl())
    s2, b2 = _bundle_decl(s1, PassiveAreaDecl(unit_area=(("CL", U_C),)))
    assert s2 is not s1
    assert _entries(b2)["area_search_m2"].value != _entries(b1)["area_search_m2"].value
    s3, _ = _bundle_decl(s2, PassiveAreaDecl(unit_area=(("CL", U_C),)))
    assert s3 is s2
    st = metrics_dc.stats()
    assert (st.computes, st.reuses, st.recomputes_same_input) == (2, 1, 0)
