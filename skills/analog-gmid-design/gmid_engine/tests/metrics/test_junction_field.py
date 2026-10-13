"""metrics/junction_field.py -- 계산 블록 `junction_field(snapshot, pdk_decl, lut_rule_decl, lut)` -> S0 수준 필드 `graph/kernel: junction_source`
(설계 40 v1.9.1 §2.4.7 'SearchContext 칸 배정' `junction`(`JunctionSource`) 행 -> `graph/kernel: junction_source`(PDK 선언·LUT 생성 규칙 선언의 파생), §2.4.8 SearchDomain 등 행,
§2.4.2 'S0 수준 값은 계산 블록으로 만들고 … 입력 버전이 같으면 다시 계산하지 않는다').

oracle (d)·(a): 필드 값의 내용은 toy 선언에 test 가 직접 쓴 값(conftest `TOY_JUNCTION`), toy LUT 측정 온도 27 °C, 선언 파일 바이트 sha256(test_junction_source 와 같은 출처).
writer = 권한표 `METRICS_S0_WRITERS` 의 (graph, junction_source) 항목(이름은 설계가 정하지 않아 표와 블록 이름이 같은지만 본다). 재사용: 같은 입력이면 계산 0,
선언이 바뀌면 다시 계산.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from gmid_engine.core import GraphSnapshot
from gmid_engine.metrics import METRICS_S0_WRITERS, JunctionParams, JunctionSource, junction_field

from .conftest import JUNCTION_FIELDS, TOY_JUNCTION, load_lut_v2, lut_access, read_decls, toy_junction_decls

KERNEL = "kernel"


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    lut = load_lut_v2(tmp_path_factory.mktemp("jf_lut"))
    paths = toy_junction_decls(tmp_path_factory.mktemp("jf_decl"))
    pdk, rule = read_decls(*paths)
    return lut, paths, pdk, rule, lut_access(lut)


def _snap():
    return GraphSnapshot.empty(METRICS_S0_WRITERS)


def test_block_declaration():
    assert junction_field.name == METRICS_S0_WRITERS.writer_of("graph", "junction_source")
    assert tuple(junction_field.writes) == (("graph", "junction_source"),)


def test_field_holds_declared_junction_source(env):
    lut, paths, pdk, rule, access = env
    out = junction_field(_snap(), pdk, rule, access)
    js = out.value("graph", KERNEL, "junction_source")
    assert isinstance(js, JunctionSource)
    assert [k for k, _ in js.params] == ["nmos", "pmos"]
    for kind, p in js.params:
        assert isinstance(p, JunctionParams)
        for f in JUNCTION_FIELDS:
            assert getattr(p, f) == TOY_JUNCTION[kind][f], (kind, f)
    assert js.temp_c == 27.0
    assert js.lut_rule_decl == rule
    assert js.pdk_decl_sha256 == hashlib.sha256(Path(paths[0]).read_bytes()).hexdigest()
    assert out.field("graph", KERNEL, "junction_source").writer == junction_field.name


def test_same_input_reuses_and_changed_decl_recomputes(env, tmp_path):
    lut, _paths, pdk, rule, access = env
    junction_field.reset_stats()
    a = junction_field(_snap(), pdk, rule, access)
    b = junction_field(a, pdk, rule, access)
    assert b is a or b.fp == a.fp
    st = junction_field.stats()
    assert (st.computes, st.reuses, st.recomputes_same_input) == (1, 1, 0)
    other = dict(TOY_JUNCTION)
    other["nmos"] = dict(TOY_JUNCTION["nmos"], cjs=2.2e-3)
    pdk2, rule2 = read_decls(*toy_junction_decls(tmp_path / "d2", params=other))
    c = junction_field(b, pdk2, rule2, access)
    assert junction_field.stats().computes == 2
    assert dict(c.value("graph", KERNEL, "junction_source").params)["nmos"].cjs == 2.2e-3
