"""CONTRACT 4.1 입력 계약(`contract_input.py`) -- frozen dataclass, 검증 거부(ValueError), `LayoutPdk.from_lut`, 상수."""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.layout import LayoutDevice, LayoutInput, LayoutPdk, MatchingGroup, RowGroup
from gmid_engine.layout import contract_input as ci
from gmid_engine.layout import __all__ as public
from gmid_engine.lut import widths

from .conftest import dev, make_input, mg, rg, rule_ids, toy_pdk


def test_public_api():
    assert set(public) == {"LayoutDevice", "LayoutInput", "LayoutPdk", "LayoutResult", "MatchingGroup", "RowGroup", "run_layout"}


def test_constants():
    assert ci.LAYOUT_ROLES == ("diff_pair", "mirror", "branch_symmetric")
    assert ci.EXCLUDED_ROLES == ("bias_distribution", "feedback_shared")
    assert set(ci.ROLES) == set(ci.LAYOUT_ROLES) | set(ci.EXCLUDED_ROLES)
    assert set(ci.CC_REQUIRED_ROLES) == {"diff_pair", "branch_symmetric"}
    assert set(ci.PATTERNS) == {"common_centroid", "interdigitation"}
    assert ci.PDK_RULE_QUANTITIES == ("finger_pitch_overhead_m", "row_gap_m", "dummy_w_m", "tap_w_m", "well_spacing_m")


def test_field_order():
    f = lambda c: [x.name for x in dataclasses.fields(c)]          # noqa: E731
    assert f(LayoutDevice) == ["name", "kind", "drain", "gate", "source", "body", "W_m", "L_m", "ID_A", "gm_id", "vds_V",
                               "vsb_V", "diode", "W_adjustable"]
    assert f(MatchingGroup) == ["gid", "members", "role", "hub_net", "allowed_patterns"]
    assert f(RowGroup) == ["rid", "kind", "body_net", "members"]
    assert f(LayoutPdk) == ["manufacturing_grid_m", "slice_width_keys", "finger_pitch_overhead_m", "row_gap_m", "dummy_w_m",
                            "tap_w_m", "well_spacing_m", "rule_ids", "source_fp"]
    assert f(LayoutInput) == ["devices", "matching_groups", "row_groups", "pdk", "rejected_requests"]
    assert "tol_v_V" not in f(LayoutDevice)                           # 옛 필드 없음(tol_V 는 슬라이스마다 LUT 에서)
    assert "box_max_row_ratio" not in f(LayoutInput) + f(LayoutPdk)   # 하드 box 허용치 없음(Q8 (vi))


def test_frozen():
    d = dev("A", "s", "d", 1e-6)
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.ID_A = 2e-6


# --- LayoutDevice ---------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("field, bad", [
    ("W_m", 4), ("L_m", 1), ("ID_A", 1), ("gm_id", 10),               # int 거부
    ("W_m", 0.0), ("L_m", -1e-6), ("ID_A", 0.0), ("gm_id", -10.0),     # 양수 아님
    ("kind", "jfet"),
])
def test_device_rejects(field, bad):
    kw = dict(name="A", kind="nmos", drain="d", gate="g", source="s", body="sub", W_m=1e-6, L_m=1e-6, ID_A=1e-6,
              gm_id=10.0, vds_V=0.5, vsb_V=0.0, diode=False, W_adjustable=True)
    kw[field] = bad
    with pytest.raises(ValueError):
        LayoutDevice(**kw)


# --- MatchingGroup --------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("args", [
    ("g", ("A",), "diff_pair", "h", ("common_centroid",)),                        # 멤버 1개
    ("g", ("A", "A"), "diff_pair", "h", ("common_centroid",)),                    # 중복
    ("g", ("A", "B"), "cascode", "h", ("common_centroid",)),                      # role 밖
    ("g", ("A", "B"), "mirror", "h", ()),                                         # 빈 패턴
    ("g", ("A", "B"), "mirror", "h", ("spiral",)),                                # 패턴 밖
    ("g", ("A", "B"), "diff_pair", "h", ("interdigitation",)),                    # cc 필수 role 에 cc 없음
    ("g", ("A", "B"), "branch_symmetric", None, ("interdigitation",)),
])
def test_group_rejects(args):
    with pytest.raises(ValueError):
        MatchingGroup(*args)


def test_group_accepts():
    MatchingGroup("g", ("A", "B"), "mirror", "h", ("interdigitation",))           # mirror 는 cc 필수 아님
    MatchingGroup("g", ("A", "B"), "branch_symmetric", None, ("common_centroid",))  # hub None 가능
    MatchingGroup("g", ("A", "B"), "bias_distribution", "h", ("common_centroid",))


def test_rowgroup_rejects():
    with pytest.raises(ValueError):
        RowGroup("r", "nmos", "sub", ("A", "A"))
    with pytest.raises(ValueError):
        RowGroup("r", "jfet", "sub", ("A",))


# --- LayoutPdk ------------------------------------------------------------------------------------------------------

def _pdk_kw(toy_lut):
    p = toy_pdk(toy_lut)
    return {f.name: getattr(p, f.name) for f in dataclasses.fields(p)}


def test_from_lut(toy_lut):
    rules = rule_ids()
    p = LayoutPdk.from_lut(toy_lut, 1, 2e-7, 3e-7, 4e-7, 5e-7, list(rules))
    assert p.manufacturing_grid_m == toy_lut.spec.manufacturing_grid_m
    assert p.slice_width_keys == (("nmos", widths(toy_lut, "nmos")),) == (("nmos", (100, 200)),)
    assert (p.finger_pitch_overhead_m, p.row_gap_m, p.dummy_w_m, p.tap_w_m, p.well_spacing_m) == (1.0, 2e-7, 3e-7, 4e-7, 5e-7)
    assert isinstance(p.finger_pitch_overhead_m, float)
    assert p.rule_ids == rules
    assert p.source_fp == toy_lut.fp


@pytest.mark.parametrize("mutate", [
    lambda kw: kw.update(manufacturing_grid_m=0.0),
    lambda kw: kw.update(row_gap_m=-1e-9),
    lambda kw: kw.update(well_spacing_m=-1e-9),
    lambda kw: kw.update(rule_ids=tuple(r for r in kw["rule_ids"] if r[0] != "tap_w_m")),           # 규칙 번호 누락
    lambda kw: kw.update(rule_ids=tuple((n, "" if n == "dummy_w_m" else v) for n, v in kw["rule_ids"])),  # 빈 규칙 번호
    lambda kw: kw.update(rule_ids=kw["rule_ids"] + (("row_gap_m", "X.1"),)),                       # 이름 중복
])
def test_pdk_rejects(toy_lut, mutate):
    kw = _pdk_kw(toy_lut)
    LayoutPdk(**kw)                                    # 기준값은 통과
    mutate(kw)
    with pytest.raises(ValueError):
        LayoutPdk(**kw)


def test_pdk_missing_rule_id_rejected_via_from_lut(toy_lut):
    with pytest.raises(ValueError):
        toy_pdk(toy_lut, rules=rule_ids()[:-1])


# --- LayoutInput ----------------------------------------------------------------------------------------------------

def _base(toy_lut):
    A, B, C = dev("A", "h", "da", 1e-6), dev("B", "h", "db", 1e-6), dev("C", "x", "y", 1e-6)
    return [A, B, C], [mg("g1", ("A", "B"), "diff_pair", "h")], [rg("r1", ("A", "B")), rg("r2", ("C",))], toy_pdk(toy_lut)


def test_input_accepts_base(toy_lut):
    devs, groups, rgs, pdk = _base(toy_lut)
    inp = make_input(devs, groups, rgs, pdk, ("A",))
    assert inp.rejected_requests == ("A",)


@pytest.mark.parametrize("case", [
    "dup_device", "dup_gid", "dup_rid", "rowgroup_unknown_member", "device_in_two_rowgroups", "kind_body_mismatch",
    "device_without_rowgroup", "kind_without_pdk_keys", "group_unknown_member", "layout_group_spans_rowgroups",
    "dup_rejected",
])
def test_input_rejects(toy_lut, case):
    devs, groups, rgs, pdk = _base(toy_lut)
    rej = ()
    if case == "dup_device":
        devs = devs + [dev("C", "x", "y", 1e-6)]
    elif case == "dup_gid":
        groups = groups + [mg("g1", ("A", "B"), "mirror", "h")]
    elif case == "dup_rid":
        rgs = [rg("r1", ("A", "B")), rg("r1", ("C",))]
    elif case == "rowgroup_unknown_member":
        rgs = [rg("r1", ("A", "B")), rg("r2", ("C", "Q"))]
    elif case == "device_in_two_rowgroups":
        rgs = [rg("r1", ("A", "B", "C")), rg("r2", ("C",))]
    elif case == "kind_body_mismatch":
        rgs = [rg("r1", ("A", "B")), rg("r2", ("C",), body="nw")]
    elif case == "device_without_rowgroup":
        rgs = [rg("r1", ("A", "B"))]
    elif case == "kind_without_pdk_keys":
        devs = devs + [dev("P", "vdd", "o", 1e-6, kind="pmos", body="nw")]
        rgs = rgs + [rg("r3", ("P",), kind="pmos", body="nw")]
    elif case == "group_unknown_member":
        groups = [mg("g1", ("A", "Q"), "diff_pair", "h")]
    elif case == "layout_group_spans_rowgroups":
        groups = [mg("g1", ("A", "C"), "mirror", "h")]
    elif case == "dup_rejected":
        rej = ("A", "A")
    with pytest.raises(ValueError):
        make_input(devs, groups, rgs, pdk, rej)


def test_excluded_role_group_may_span_rowgroups(toy_lut):
    devs, groups, rgs, pdk = _base(toy_lut)
    make_input(devs, groups + [mg("g3", ("A", "C"), "bias_distribution", "h")], rgs, pdk)
    make_input(devs, groups + [mg("g4", ("B", "C"), "feedback_shared", None)], rgs, pdk)
