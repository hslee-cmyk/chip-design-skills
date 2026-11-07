"""`JunctionSource` (S0 비례 기준 묶음: `lut_rule_decl`, `reference`, `temp_c`) -- interface card 20261106-jc1 §2 (S-1~S-3).

[JC-1] 옛 test(params·pdk_decl_sha256·params_of·BSIM4 파라미터 선언 값, sky130 core 9.4 표)는 모두 `retired_tests`(`tests/RETIRED_TESTS_jc1.md`, covered_by = S-1~S-4).

독립 검증(작성자 ≠ 검증자): 기대값 출처 = toy 규칙 선언을 core `read_pdk_decl` 로 읽은 값(a·b·pd_extra·ps_extra)과 toy LUT 에 쓴 기준 폭 `w_ref_m`·측정 온도
(구성으로 정해진 입력, oracle (a)/(d)). `from_decls`·`DiffusionGeometry.from_lut_rule` 로 기대값을 만들지 않는다 -- 손 `DiffusionGeometry(...)` 생성자 직접.
"""
from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from gmid_engine.core import SchemaRejectedError, fp_of, require_immutable
from gmid_engine.metrics import DiffusionGeometry, JunctionSource

from .conftest import TOY_RULE_LINE, read_rule_decl, toy_rule_decl
from .jc1_toy import W_REF, rule_values, toyc_build, toyc_cap_arrays, toyc_lut, toyc_slices


@pytest.fixture
def lut(tmp_path):
    return toyc_lut(tmp_path / "lut")


@pytest.fixture
def rule(tmp_path):
    return read_rule_decl(toy_rule_decl(tmp_path / "rule"))


def _reason(excinfo):
    return dict(excinfo.value.record.detail)


def test_junction_s1_fields_names_and_reference(tmp_path, lut, rule):
    """S-1: `dataclasses.fields(JunctionSource)` 이름 = (lut_rule_decl, reference, temp_c) -- params·pdk_decl_sha256 없음; kind 마다 기준 기하 =
    손 DiffusionGeometry(w_ref, a·w_ref, b·w_ref, w_ref + pd_extra, w_ref + ps_extra, 1.0); temp_c = LUT 측정 온도."""
    v = rule_values(tmp_path / "v")
    js = JunctionSource.from_decls(rule, lut)
    assert tuple(f.name for f in dataclasses.fields(JunctionSource)) == ("lut_rule_decl", "reference", "temp_c")
    assert [k for k, _ in js.reference] == ["nmos"]
    hand = DiffusionGeometry(1e-6, v["a"] * 1e-6, v["b"] * 1e-6, 1e-6 + v["pd"], 1e-6 + v["ps"], 1.0)
    assert js.reference_of("nmos") == hand
    assert js.temp_c == 27.0 and isinstance(js.temp_c, float)         # oracle (d): toy LUT 에 쓴 측정 온도(jc1_toy: temp_c = 27.0)
    assert js.lut_rule_decl == rule


def test_junction_reference_of_unknown_kind_keyerror(lut, rule):
    js = JunctionSource.from_decls(rule, lut)
    for bad in ("pmos", "NMOS", ""):
        with pytest.raises(KeyError):
            js.reference_of(bad)


@pytest.mark.parametrize("w,m", [(1e-6, 3.7), (0.42e-6, 8.0), (2e-6, 1.0)])
def test_junction_pre_layout_geometry_is_rule_geometry(tmp_path, lut, rule, w, m):
    """pre_layout_geometry(w, m) = 생성 규칙 기하(finger_w = w, ad = a·w, as = b·w, pd = w + pd_extra, ps = w + ps_extra, m). oracle (a): 읽은 선언 값 × w."""
    v = rule_values(tmp_path / "v")
    g = JunctionSource.from_decls(rule, lut).pre_layout_geometry(w, m)
    assert isinstance(g, DiffusionGeometry)
    assert (g.finger_w_m, g.ad_m2, g.as_m2, g.pd_m, g.ps_m, g.m) == (w, v["a"] * w, v["b"] * w, w + v["pd"], w + v["ps"], m)
    with pytest.raises(ValueError):
        JunctionSource.from_decls(rule, lut).pre_layout_geometry(0.0, m)


def test_junction_temperature_follows_lut_not_a_constant(tmp_path, rule):
    """temp_c = LUT cap_conditions 의 측정 온도: 60 °C 로 쓴 LUT -> 60."""
    cap = toyc_cap_arrays()
    cap["temp_c"] = np.float64(60.0)
    sl = toyc_slices()
    for _, _, a in sl:
        a["temp_c"] = np.float64(60.0)
    lut60 = toyc_build(tmp_path / "lut60", cap=cap, slices=sl).load()
    assert JunctionSource.from_decls(rule, lut60).temp_c == 60.0


def test_missing_lut_temperature_rejected(tmp_path, rule):
    """LUT 측정 조건에 temp_c 가 없으면 ValueError(기존 그대로)."""
    cap = toyc_cap_arrays()
    del cap["temp_c"]
    sl = toyc_slices()
    for _, _, a in sl:
        del a["temp_c"]
    lut_nt = toyc_build(tmp_path / "lut_nt", cap=cap, slices=sl).load()
    with pytest.raises(ValueError):
        JunctionSource.from_decls(rule, lut_nt)


@pytest.mark.parametrize("line,quantity", [
    ("xdut d g s b dev l=1e-6 w=4e-6 ad=0 as=1.2e-12 pd=9e-6 ps=7e-6", "lut_diffusion_ad_per_w_m"),
    ("xdut d g s b dev l=1e-6 w=4e-6 ad=2e-12 as=0 pd=9e-6 ps=7e-6", "lut_diffusion_as_per_w_m"),
    ("xdut d g s b dev l=1e-6 w=4e-6 ad=0 as=0 pd=9e-6 ps=7e-6", "lut_diffusion_ad_per_w_m"),
], ids=["S-2", "S-3", "ad_first"])
def test_junction_s2_s3_zero_reference_area_rejected(tmp_path, lut, line, quantity):
    """S-2/S-3: 기준 면적 0(ad_per_w = 0 또는 as_per_w = 0) -> SchemaRejectedError pdk_quantity_invalid, quantity, value 0.0 (AD 먼저).
    oracle (d): 계약(비례 기준 0 = 0 나눗셈 방지) -- base 는 그 선언으로 JunctionSource 를 만들고 정지 없음."""
    rule0 = read_rule_decl(toy_rule_decl(tmp_path / "r0", line))      # 전제: core 는 정확히 0 을 받아들인다(선언 적재 통과)
    with pytest.raises(SchemaRejectedError) as ei:
        JunctionSource.from_decls(rule0, lut)
    d = _reason(ei)
    assert d["reason"] == "pdk_quantity_invalid" and d["quantity"] == quantity and d["value"] == 0.0


def test_junction_s_negative_check_nonzero_areas_accepted(lut, rule):
    """S-2/S-3 음성 대조: 같은 호출이 0 아닌 기준 면적에서는 정지하지 않는다."""
    assert isinstance(JunctionSource.from_decls(rule, lut), JunctionSource)


def test_frozen_immutable_fingerprint(tmp_path, lut, rule):
    """frozen·require_immutable 통과, 따로 만든 같은 묶음 fp 같음, 필드 하나만 달라도 fp 다름(규칙 선언·온도)."""
    js = JunctionSource.from_decls(rule, lut)
    with pytest.raises(dataclasses.FrozenInstanceError):
        js.temp_c = 30.0
    require_immutable(js)
    js2 = JunctionSource.from_decls(read_rule_decl(toy_rule_decl(tmp_path / "again")), lut)
    assert js2 is not js and fp_of(js2) == fp_of(js)
    other_line = "xdut d g s b dev l=1e-6 w=4e-6 ad=3e-12 as=1.2e-12 pd=9e-6 ps=7e-6"
    js3 = JunctionSource.from_decls(read_rule_decl(toy_rule_decl(tmp_path / "other", other_line)), lut)
    variants = [dataclasses.replace(js, temp_c=js.temp_c + 10.0), js3]
    assert len({fp_of(x) for x in variants} | {fp_of(js)}) == len(variants) + 1
