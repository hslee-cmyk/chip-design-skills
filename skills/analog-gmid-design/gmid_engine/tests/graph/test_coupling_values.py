"""graph/coupling_values.py -- GB3 값 형식·어휘(U10, 설계 40 §3.3, graph CONTRACT 11.1).

oracle (d) 선언값 그대로:
- 설계 40 §3.3: 레코드 `CouplingVar{kind, members, blocks, domain, init_rule}` + as-built 보완(6707424) `nets`,
  매핑표 `column_block_map{column, block, device, shared}` + `basis`(`block_member`·`column_mate`·`bias_column`),
  결합 종류 K1·K2·K3·K4·K7·K8, 정지 사유 `column_unassigned`(DEC-71 (2)).
- graph CONTRACT 11.1: `BlockRef(view, key)` 정렬 가능, 같은 키라도 뷰가 다르면 다른 블록. 모두 frozen.
- [U17 ①-b] 설계 40 v1.9.1 §2.4.8 D8: 묶음 `Coupling`·`ColumnBlockMap` 은 없어지고 필드 `graph/coupling: vars·column_block_map(=옛 rows)·
  bias_columns` 로 풀렸다 -- 두 묶음의 필드·frozen 단언은 삭제(필드 존재·writer 는 tests/integration/test_s0_layer_9circuits.py 가 본다).
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import fp_of
from gmid_engine.graph import (
    BASIS_BIAS_COLUMN,
    BASIS_BLOCK_MEMBER,
    BASIS_COLUMN_MATE,
    COUPLING_KINDS,
    REASON_COLUMN_UNASSIGNED,
    BlockRef,
    ColumnBlockRow,
    CouplingVar,
)


def test_vocabulary_matches_design():
    # 설계 40 §3.3 결합 종류 목록(K5·K6 은 설계에 없다) -- 순서는 설계 나열 순
    assert tuple(COUPLING_KINDS) == ("K1", "K2", "K3", "K4", "K7", "K8")
    assert REASON_COLUMN_UNASSIGNED == "column_unassigned"                 # DEC-71 (2) 사유 이름
    assert (BASIS_BLOCK_MEMBER, BASIS_COLUMN_MATE, BASIS_BIAS_COLUMN) == ("block_member", "column_mate", "bias_column")


@pytest.mark.parametrize("cls, fields", [
    (BlockRef, ("view", "key")),
    (CouplingVar, ("kind", "members", "blocks", "domain", "init_rule", "nets")),
    (ColumnBlockRow, ("column", "block", "device", "shared", "basis")),
])
def test_record_fields_are_design_fields(cls, fields):
    # 설계 레코드 필드(+ as-built nets·basis) 그대로, 더하거나 빼지 않는다
    assert tuple(f.name for f in dataclasses.fields(cls)) == fields


def _samples():
    a = BlockRef("transfer:0", ("o1",))
    b = BlockRef("transfer:0", ("out",))
    var = CouplingVar("K2", ("M5", "M7"), (a, b), "dc", "common_vgs_candidates", ("vb", "gnd"))
    row = ColumnBlockRow(0, a, "M5", True, BASIS_BLOCK_MEMBER)
    return a, var, row


@pytest.mark.parametrize("idx, field", [(0, "key"), (1, "kind"), (2, "shared")])
def test_values_are_frozen(idx, field):
    obj = _samples()[idx]
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, field, None)


def test_blockref_identity_includes_view_and_is_orderable():
    # 계약 11.1: 같은 키의 블록도 뷰가 다르면 다른 블록, 정렬 가능
    t = BlockRef("transfer:0", ("om", "op"))
    lp = BlockRef("loop:M5:cm", ("om", "op"))
    assert t != lp and len({t, lp}) == 2
    assert sorted([t, lp]) == [lp, t]                      # (view, key) 사전순: "loop:..." < "transfer:..."
    assert sorted([BlockRef("v", ("b",)), BlockRef("v", ("a",))])[0].key == ("a",)


def test_values_have_fingerprint():
    # 결정론 비교와 보고서 기록에 쓰이는 지문이 정의된다(같은 값 -> 같은 지문, 다른 값 -> 다른 지문)
    # [U17 ①-b] 필드 값 형식(graph/coupling: vars = CouplingVar tuple, column_block_map = ColumnBlockRow tuple)으로 본다
    _, var, row = _samples()
    _, var2, row2 = _samples()
    assert fp_of(((var,), (row,))) == fp_of(((var2,), (row2,)))
    assert fp_of(((), (row,))) != fp_of(((var,), (row,)))
