"""metrics/model_error_field.py -- 계산 블록 `model_error_field(snapshot, pairs)` -> S0 수준 필드 `graph/kernel: model_error`
(설계 40 v1.9.1 §2.4.7 'SearchContext 칸 배정' `model_error` -> `graph/kernel: model_error`(오라클 대조 결과는 spec `derived.model_error_*` 선언에서 온다), DEC-72).

oracle (a): 필드 값 = 넘긴 ((metric, 크기), ...) 쌍(이 test 가 손으로 정한 값), 빈 선언은 빈 tuple. 값이 바뀌면 다시 계산, 같으면 재사용.
writer = 권한표 `METRICS_S0_WRITERS` 의 (graph, model_error) 항목.
"""
from __future__ import annotations

from gmid_engine.core import GraphSnapshot
from gmid_engine.metrics import METRICS_S0_WRITERS, model_error_field

from .conftest import block_row, fresh_run

PAIRS = (("gain_ss_db", 0.5), ("ugf_ss_hz", 1.0e5))


def _empty():
    return GraphSnapshot.empty(METRICS_S0_WRITERS)


def test_block_declaration():
    assert model_error_field.name == METRICS_S0_WRITERS.writer_of("graph", "model_error")
    assert tuple(model_error_field.writes) == (("graph", "model_error"),)


def test_field_holds_pairs_and_empty():
    run = fresh_run()
    assert model_error_field(_empty(), PAIRS, **run).value("graph", "kernel", "model_error") == PAIRS
    assert model_error_field(_empty(), (), **run).value("graph", "kernel", "model_error") == ()


def test_reuse_and_recompute():
    # oracle 대조: card B C4 판정 1·4 -- 실행 계수(C1) 행: 손 순서(compute, reuse, compute)
    run = fresh_run()
    a = model_error_field(_empty(), PAIRS, **run)
    b = model_error_field(a, PAIRS, **run)
    assert b.fp == a.fp
    c = model_error_field(b, (("gain_ss_db", 0.7),), **run)
    assert block_row(run["counters"], model_error_field.name) == (3, 1, 0, 0, 2, 0)
    assert c.value("graph", "kernel", "model_error") == (("gain_ss_db", 0.7),)
