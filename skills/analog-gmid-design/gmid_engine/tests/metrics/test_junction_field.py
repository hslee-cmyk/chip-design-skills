"""metrics/junction_field.py -- 계산 블록 `junction_field(snapshot, lut_rule_decl, lut)` -> S0 수준 필드 `graph/kernel: junction_source` (interface card
20261106-jc1 §2 S-4). [JC-1] extras 에서 `pdk_decl` 이 빠졌다(접합 값이 PDK 접합 키를 읽지 않는다).

oracle (d)·(a): 필드 값의 내용 = toy 규칙 선언을 core 가 읽은 값 × 기준 폭 w_ref(손 DiffusionGeometry), 측정 온도 = toy LUT 에 쓴 27 °C.
writer = 권한표 `METRICS_S0_WRITERS` 의 (graph, junction_source) 항목. 재사용: 같은 입력이면 계산 0, 선언이 바뀌면 다시 계산.
"""
from __future__ import annotations

import pytest

from gmid_engine.core import GraphSnapshot
from gmid_engine.metrics import METRICS_S0_WRITERS, DiffusionGeometry, JunctionSource, junction_field

from .conftest import TOY_RULE_LINE, block_row, fresh_run, lut_access, read_rule_decl, toy_rule_decl
from .jc1_toy import rule_values, toyc_lut

KERNEL = "kernel"


@pytest.fixture
def env(tmp_path):
    lut = toyc_lut(tmp_path / "lut")
    return lut, lut_access(lut), read_rule_decl(toy_rule_decl(tmp_path / "rule")), rule_values(tmp_path / "v")


def _snap():
    return GraphSnapshot.empty(METRICS_S0_WRITERS)


def test_block_declaration():
    assert junction_field.name == METRICS_S0_WRITERS.writer_of("graph", "junction_source")
    assert tuple(junction_field.writes) == (("graph", "junction_source"),)


def test_junction_field_holds_proportional_reference(env):
    lut, access, rule, v = env
    out = junction_field(_snap(), rule, access, **fresh_run())
    js = out.value("graph", KERNEL, "junction_source")
    assert isinstance(js, JunctionSource)
    assert js.reference_of("nmos") == DiffusionGeometry(1e-6, v["a"] * 1e-6, v["b"] * 1e-6, 1e-6 + v["pd"], 1e-6 + v["ps"], 1.0)
    assert js.temp_c == 27.0 and js.lut_rule_decl == rule
    assert out.field("graph", KERNEL, "junction_source").writer == junction_field.name


def test_junction_s4_same_input_reuses_and_changed_decl_recomputes(env, tmp_path):
    """S-4: 같은 선언·LUT 두 번(같은 donors·counters) -> 둘째 호출 계산 0(블록 계수 (calls, reuses, grafts, replays, computes, recomputes_same_input) = (2, 1, 0, 0, 1, 0)),
    값 같음. 선언이 바뀌면 다시 계산(computes 2). 알고 있는 계수 행 = 손 순서 (compute, reuse, compute)."""
    lut, access, rule, v = env
    run = fresh_run()
    a = junction_field(_snap(), rule, access, **run)
    b = junction_field(a, rule, access, **run)
    assert b is a or b.fp == a.fp
    assert block_row(run["counters"], junction_field.name) == (2, 1, 0, 0, 1, 0)
    rule2 = read_rule_decl(toy_rule_decl(tmp_path / "d2", "xdut d g s b dev l=1e-6 w=4e-6 ad=3e-12 as=1.2e-12 pd=9e-6 ps=7e-6"))
    c = junction_field(b, rule2, access, **run)
    assert block_row(run["counters"], junction_field.name)[4] == 2
    assert c.value("graph", KERNEL, "junction_source").reference_of("nmos").ad_m2 != \
        a.value("graph", KERNEL, "junction_source").reference_of("nmos").ad_m2
