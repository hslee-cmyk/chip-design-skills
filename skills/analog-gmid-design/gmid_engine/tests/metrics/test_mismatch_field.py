"""metrics/mismatch_field.py -- 계산 블록 `mismatch_field(snapshot, pdk_decl)` -> S0 수준 필드 `graph/kernel: mismatch_source`
(설계 40 v1.9.1 §2.4.7 'SearchContext 칸 배정' `mismatch`(`MismatchSource`) -> `graph/kernel: mismatch_source`(PDK 선언의 파생), §2.4.2 입력 버전이 같으면 재계산 없음).

oracle (d): 필드 값 = PDK 선언의 mismatch 모델(kind 목록)과 선언 파일 바이트 sha256 -- 저장소 `assets/sky130_pdk_decl.json` 을 test 가 직접 해시한다.
writer = 권한표 `METRICS_S0_WRITERS` 의 (graph, mismatch_source) 항목.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from gmid_engine.core import BoundedLRU, GraphSnapshot, read_pdk_decl
from gmid_engine.metrics import METRICS_S0_WRITERS, MismatchSource, mismatch_field

from .conftest import block_row, fresh_run

SKILL = Path(__file__).resolve().parents[3]
DECL = SKILL / "assets" / "sky130_pdk_decl.json"


@pytest.fixture(scope="module")
def pdk():
    return read_pdk_decl(str(DECL), BoundedLRU(4))


def test_block_declaration():
    assert mismatch_field.name == METRICS_S0_WRITERS.writer_of("graph", "mismatch_source")
    assert tuple(mismatch_field.writes) == (("graph", "mismatch_source"),)


def test_field_holds_pdk_mismatch_source(pdk):
    out = mismatch_field(GraphSnapshot.empty(METRICS_S0_WRITERS), pdk, **fresh_run())
    src = out.value("graph", "kernel", "mismatch_source")
    assert isinstance(src, MismatchSource)
    assert src.sha256 == hashlib.sha256(DECL.read_bytes()).hexdigest()
    assert [k for k, _ in src.models] == ["nmos", "pmos"]
    assert out.field("graph", "kernel", "mismatch_source").writer == mismatch_field.name


def test_same_decl_reuses(pdk):
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행 (compute, reuse)
    run = fresh_run()
    a = mismatch_field(GraphSnapshot.empty(METRICS_S0_WRITERS), pdk, **run)
    b = mismatch_field(a, pdk, **run)
    assert b.fp == a.fp
    assert block_row(run["counters"], mismatch_field.name) == (2, 1, 0, 0, 1, 0)
