"""`JunctionSource` (접합 용량 입력 묶음, `from_decls`·`params_of`·`pre_layout_geometry`) -- metrics CONTRACT 7.2·7.6·8.5
(+ core CONTRACT 9 선언 형식).

독립 검증(작성자 ≠ 검증자): 기대값 출처는 toy 선언에 test 가 직접 쓴 값(conftest `TOY_JUNCTION`·`TOY_RULE_LINE`), toy LUT 에
쓴 측정 온도, 선언 파일 바이트의 sha256, core 9.4 표(sky130, 원본이 있을 때만)뿐이다.
"""
from __future__ import annotations

import dataclasses
import hashlib
from pathlib import Path

import pytest

from gmid_engine.core import SchemaRejectedError, fp_of, require_immutable
from gmid_engine.metrics import DiffusionGeometry, JunctionParams, JunctionSource

from .conftest import (
    JUNCTION_FIELDS,
    TOY_JUNCTION,
    load_lut_v2,
    read_decls,
    toy_junction_decls,
    toy_rule_values,
)


@pytest.fixture(scope="module")
def lut(tmp_path_factory):
    return load_lut_v2(tmp_path_factory.mktemp("lut"))


@pytest.fixture(scope="module")
def paths(tmp_path_factory):
    return toy_junction_decls(tmp_path_factory.mktemp("decl"))


def _src(paths, lut):
    pdk, rule = read_decls(*paths)
    return JunctionSource.from_decls(pdk, rule, lut), pdk, rule


def test_fields_order():
    """7.2: JunctionSource(params, lut_rule_decl, temp_c, pdk_decl_sha256)."""
    assert [f.name for f in dataclasses.fields(JunctionSource)] == ["params", "lut_rule_decl", "temp_c", "pdk_decl_sha256"]


def test_from_decls_kinds_params_temp_sha(paths, lut):
    """from_decls: kind = LUT device_kinds 의 kind 집합(정렬), params = 그 kind 의 선언 값, temp_c = LUT 측정 온도,
    lut_rule_decl = 규칙 선언, pdk_decl_sha256 = PDK 선언 파일 sha256."""
    js, pdk, rule = _src(paths, lut)
    assert [k for k, _ in js.params] == ["nmos", "pmos"]
    for kind, p in js.params:
        assert isinstance(p, JunctionParams)
        for f in JUNCTION_FIELDS:
            assert getattr(p, f) == TOY_JUNCTION[kind][f], (kind, f)       # 선언에 단위 글자 없이 repr 로 쓴 값 그대로
        assert p == JunctionParams.from_pdk_decl(pdk, kind)
    assert js.temp_c == 27.0 and isinstance(js.temp_c, float)
    assert js.lut_rule_decl == rule
    assert js.pdk_decl_sha256 == hashlib.sha256(Path(paths[0]).read_bytes()).hexdigest() == pdk.decl_sha256


def test_temperature_comes_from_lut_cap_conditions(tmp_path, paths):
    """temp_c = dict(lut_set.provenance.cap_conditions)["temp_c"] -- LUT 를 60 °C 로 쓰면 60."""
    lut60 = load_lut_v2(tmp_path / "lut60", temp_c=60.0)
    assert dict(lut60.provenance.cap_conditions)["temp_c"] == 60.0
    js, _, _ = _src(paths, lut60)
    assert js.temp_c == 60.0


def test_missing_lut_temperature_rejected(tmp_path, paths):
    """LUT 측정 조건에 temp_c 가 없으면 ValueError."""
    lut_nt = load_lut_v2(tmp_path / "lut_nt", temp_c=None)
    assert "temp_c" not in dict(lut_nt.provenance.cap_conditions)
    pdk, rule = read_decls(*paths)
    with pytest.raises(ValueError):
        JunctionSource.from_decls(pdk, rule, lut_nt)


def test_kinds_follow_lut_not_decl(tmp_path, lut):
    """kind 는 LUT 에서: 선언에 LUT 밖 kind 가 더 있어도 params 는 LUT kind 만, LUT kind 가 선언에 없으면 core 거부."""
    extra = dict(TOY_JUNCTION, nhv=dict(TOY_JUNCTION["nmos"], cjs=2e-3))
    js = JunctionSource.from_decls(*read_decls(*toy_junction_decls(tmp_path / "x", params=extra,
                                                                   kinds=("nhv", "nmos", "pmos"))), lut)
    assert [k for k, _ in js.params] == ["nmos", "pmos"]
    with pytest.raises(KeyError):
        js.params_of("nhv")
    pdk, rule = read_decls(*toy_junction_decls(tmp_path / "n", kinds=("nmos",)))
    with pytest.raises(SchemaRejectedError) as ei:
        JunctionSource.from_decls(pdk, rule, lut)
    assert dict(ei.value.record.detail)["reason"] == "pdk_quantity_undeclared"


def test_params_of(paths, lut):
    js, _, _ = _src(paths, lut)
    assert js.params_of("nmos") == dict(js.params)["nmos"]
    assert js.params_of("pmos").cjs == TOY_JUNCTION["pmos"]["cjs"]
    for bad in ("nfet", "NMOS", ""):
        with pytest.raises(KeyError):
            js.params_of(bad)


@pytest.mark.parametrize("fw,m", [(1e-6, 3.7), (0.42e-6, 8.0), (2e-6, 1.0)])
def test_pre_layout_geometry(paths, lut, fw, m):
    """pre_layout_geometry(finger_w, m) = DiffusionGeometry.from_lut_rule(규칙 선언, finger_w, m) = 규칙 줄 비율(8.1)."""
    js, _, rule = _src(paths, lut)
    g = js.pre_layout_geometry(fw, m)
    assert isinstance(g, DiffusionGeometry)
    assert g == DiffusionGeometry.from_lut_rule(rule, fw, m)
    r = toy_rule_values()
    assert (g.finger_w_m, g.ad_m2, g.as_m2, g.pd_m, g.ps_m, g.m) == (
        fw, r["ad_per_w"] * fw, r["as_per_w"] * fw, fw + r["pd_extra"], fw + r["ps_extra"], m)
    assert g.ad_m2 != g.as_m2 and g.pd_m != g.ps_m
    with pytest.raises(ValueError):
        js.pre_layout_geometry(0.0, m)
    with pytest.raises(ValueError):
        js.pre_layout_geometry(fw, 0.0)


def test_frozen_immutable_fingerprint(tmp_path, paths, lut):
    """frozen·require_immutable 통과(블록 extras 로 지문에 든다), 따로 만든 같은 묶음 fp 같음, 필드 하나만 달라도 fp 다름."""
    js, _, _ = _src(paths, lut)
    with pytest.raises(dataclasses.FrozenInstanceError):
        js.temp_c = 30.0
    require_immutable(js)
    js2, _, _ = _src(paths, lut)
    assert js2 is not js and fp_of(js2) == fp_of(js)
    variants = [dataclasses.replace(js, temp_c=js.temp_c + 10.0), dataclasses.replace(js, pdk_decl_sha256="0" * 64)]
    params = {k: dict(v) for k, v in TOY_JUNCTION.items()}
    params["pmos"]["mjswgd"] = 0.81
    variants.append(JunctionSource.from_decls(*read_decls(*toy_junction_decls(tmp_path / "p", params=params)), lut))
    variants.append(JunctionSource.from_decls(*read_decls(*toy_junction_decls(
        tmp_path / "r", rule_line="xdut d g s b dev l=1e-6 w=4e-6 ad=2e-12 as=1.2e-12 pd=9e-6 ps=8e-6")), lut))
    fps = {fp_of(v) for v in variants} | {fp_of(js)}
    assert len(fps) == len(variants) + 1


def test_sky130_decls(lut):
    """sky130 실선언(원본이 있을 때만): core 9.4 표 값, kind 는 toy LUT 의 nmos·pmos."""
    from . import test_junction_cap as tj
    if not tj._SKY_PRESENT:
        pytest.skip("sky130 원본 없음")
    pdk, rule = read_decls(str(tj.PDK_DECL), str(tj.LUT_RULE_DECL))
    js = JunctionSource.from_decls(pdk, rule, lut)
    assert [k for k, _ in js.params] == ["nmos", "pmos"]
    for kind in ("nmos", "pmos"):
        ref = tj.sky_ref_params(kind)
        for f in JUNCTION_FIELDS:
            assert getattr(js.params_of(kind), f) == pytest.approx(ref[f], rel=1e-12, abs=0.0), (kind, f)
    assert js.pdk_decl_sha256 == pdk.decl_sha256
    g = js.pre_layout_geometry(2e-6, 3)
    assert g.ad_m2 == pytest.approx(1e-12, rel=1e-12) and g.pd_m == pytest.approx(4e-6, rel=1e-12)
