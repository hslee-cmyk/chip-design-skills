"""graph/s1v_values.py -- SP1 값 형식(계약 10.1: frozen dataclass, `fp_of` 가능, 필드 뜻은 docstring).

oracle (d): 계약 10.1 표와 각 공개 dataclass docstring 이 이름을 적은 필드(아래 FIELDS)는 반드시 있어야 한다.
oracle (a): frozen(대입 거부), 같은 입력의 두 결과는 `==` 이고 `fp_of` 가 같다. `Finding.severity` 어휘 = review_needed /
unsupported_rule_branch / info(계약 10.2 '기록과 정지').
[U17 ①-b] 묶음 `S1v` 는 설계 40 v1.9.1 §2.4.2·§2.4.8 D1 로 없어지고 필드 `graph/s1v: views·l_classes·findings·declared·applied_facts` 가 됐다 --
S1v 칸 단언은 삭제(필드 존재는 test_s1v_fields.py), 결과 비교는 필드 값으로 한다.
"""
from __future__ import annotations

import dataclasses

import pytest

from gmid_engine.core import fp_of
from gmid_engine.graph import (Block, CompositeBlock, Finding, LClass, Loop, StructureFact, StructureFacts,
                               ViewS1v, ViewSeed)

import s1v_hand as H

FIELDS = {   # docstring 이 이름으로 적은 필드
    ViewS1v: {"ac_ground", "bias_dependent", "bias_moving", "virtual_ground", "signal_nets", "forward_nets", "cells",
              "pass_bundles", "drive_kind", "dist", "stage_dist", "stage_starts", "mirror_inputs", "blocks", "composites",
              "pole_nodes", "output_direction", "loops", "cuts", "cm_pair", "unreduced_diff", "findings"},
    ViewSeed: {"excite", "sense", "source", "cut"},
    Finding: {"code", "severity", "view", "subject", "detail", "basis"},
    Block: {"key", "kind", "stage", "inputs", "outputs", "roles", "nodes", "impedance", "status"},
    CompositeBlock: {"merge_nodes", "members", "inputs", "outputs", "paths", "cells", "chain", "status"},
    Loop: {"nodes", "devices", "classes", "cut", "polarity", "cm_pair"},
    LClass: {"members", "owner", "owner_rule", "status"},
    StructureFact: {"concept", "subject", "value", "approval_id", "nets"},
    StructureFacts: {"facts", "findings"},
}


@pytest.mark.parametrize("cls", list(FIELDS), ids=lambda c: c.__name__)
def test_documented_fields_exist_and_frozen(cls):
    assert dataclasses.is_dataclass(cls)
    assert FIELDS[cls] <= {f.name for f in dataclasses.fields(cls)}
    assert cls.__dataclass_params__.frozen


def test_instances_reject_assignment(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    v = H.view(s1v)
    for obj, field in ((v, "cells"), (v.blocks[0], "key"), (v.loops[0], "cut"), (s1v.l_classes[0], "owner")):
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(obj, field, ())


def test_equal_inputs_equal_values_and_fingerprints(tmp_path):
    _, a = H.build(tmp_path, H.CMFB, stem="a")
    _, b = H.build(tmp_path, H.CMFB, stem="b")
    fields = ("views", "l_classes", "findings", "declared", "applied_facts")
    assert [getattr(a, f) for f in fields] == [getattr(b, f) for f in fields]
    assert [fp_of(getattr(a, f)) for f in fields] == [fp_of(getattr(b, f)) for f in fields]


def test_finding_severity_vocabulary(tmp_path):
    sev = set()
    for doc in (H.CMFB, H.XCOUP, H.FF, H.AMB, H.MIXED, H.TAP, H.BMULTI, H.CSDIODE, H.PASS3, H.RFB):
        _, s1v = H.build(tmp_path, doc)
        sev |= {f.severity for v in s1v.views for f in v.findings} | {f.severity for f in s1v.findings}
    assert sev == {"review_needed", "unsupported_rule_branch", "info"}


def test_review_needed_and_unsupported_partition_findings(tmp_path):
    for doc in (H.CMFB, H.XCOUP, H.FF, H.MIXED, H.TAP):
        _, s1v = H.build(tmp_path, doc)
        every = list(s1v.findings) + [f for v in s1v.views for f in v.findings]
        assert sorted(map(repr, s1v.review_needed)) == sorted(repr(f) for f in every if f.severity == "review_needed")
        assert sorted(map(repr, s1v.unsupported)) == sorted(repr(f) for f in every
                                                            if f.severity == "unsupported_rule_branch")
