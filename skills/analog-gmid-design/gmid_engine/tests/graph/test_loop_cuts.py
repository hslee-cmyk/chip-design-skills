"""graph/loop_cuts.py -- 끊는 점·루프 뷰·루프 제약 선언 대조(계약 10.2 '루프', 불변량 7, 설계 41 1.8, 계획 N3.2-2 '끊는 점').

oracle (a) 손 유도(CMFB): 루프 (cm, cmfb, om)의 CS gate 엣지 후보 = (M5, cm)(cm -> cmfb)·(M3, cmfb)(cmfb -> om), 루프 (cm, cmfb, op)
의 후보 = (M5, cm)·(M4, cmfb). 뷰 안 루프에서 가장 많이 나타나는 후보 = (M5, cm)(2회) -> 두 루프 모두 끊는 점 (M5, cm),
루프 뷰 하나 `loop:M5:cm`. 차동 출력 포트쌍(op/om)을 루프 뷰의 루프 노드가 모두 포함 -> cm_pair, 기록 `cm_loop_unconstrained`
(info). 같은 회로에서 출력 role 을 단일 출력으로 바꾸면 포트쌍이 없어 cm_pair 아님 -> `declared_loop_cuts` 에 gate 넷 cm 이
없으면 `undeclared_loop_constraint`(기록만), 있으면 기록 없음. Miller 루프((2))는 끊는 점이 없다(루프 뷰 없음).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import StructureUnresolvedError

import s1v_hand as H

CMFB_SE = H.topo("cmfb_se", tuple((e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in H.CMFB["netlist"]),
                 {"inp": H.DIFF_P, "inn": H.DIFF_N, "op": H.SE_OUT, "om": H.SE_OUT},
                 passives=tuple((e["name"], e["kind"], tuple(e["terminals"])) for e in H.CMFB["passive_elements"]),
                 bias=("vb", "vref"))


def test_cmfb_cut_is_most_frequent_cs_gate(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    v = H.view(s1v)
    assert [lp.cut for lp in v.loops] == [("M5", "cm"), ("M5", "cm")]
    assert v.cuts == (("M5", "cm"),)


def test_cut_is_cs_gate_edge_on_the_loop(tmp_path):
    # 불변량 7: loop_view 루프의 끊는 점은 그 루프 위 CS 셀의 gate 엣지
    _, s1v = H.build(tmp_path, H.CMFB)
    for v in s1v.views:
        for lp in v.loops:
            if "loop_view" not in lp.classes:
                continue
            dev, gate = lp.cut
            assert dev in lp.devices and gate in lp.nodes
            assert H.cells(H.view(s1v, "loop:%s:%s" % (dev, gate)))[dev] == "cs"


def test_differential_output_pair_loop_is_cm_pair(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    loop = H.view(s1v, "loop:M5:cm")
    assert loop.cm_pair is True
    hits = [f for f in loop.findings if f.code == "cm_loop_unconstrained"]
    assert [(h.severity, h.subject) for h in hits] == [("info", ("cm",))]
    assert "undeclared_loop_constraint" not in H.all_codes(s1v)


def test_loop_view_without_port_pair_needs_declared_cut(tmp_path):
    _, s1v = H.build(tmp_path, CMFB_SE)
    assert [v.cm_pair for v in s1v.views] == [False, False]
    assert H.all_codes(s1v) == ["undeclared_loop_constraint"]
    assert [f.severity for f in s1v.unsupported] == ["unsupported_rule_branch"]
    with pytest.raises(StructureUnresolvedError) as ei:
        H.build(tmp_path, CMFB_SE, stop_on_unsupported=True)
    assert dict(ei.value.record.detail)["rule_branch"] == "undeclared_loop_constraint"


def test_declared_loop_cut_removes_the_record(tmp_path):
    _, s1v = H.build(tmp_path, CMFB_SE, declared_loop_cuts=("cm",))
    assert H.all_codes(s1v) == []
    _, other = H.build(tmp_path, CMFB_SE, declared_loop_cuts=("cmfb",))     # 다른 gate 넷 선언은 대조되지 않는다
    assert H.all_codes(other) == ["undeclared_loop_constraint"]


def test_miller_loop_has_no_cut(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    v = H.view(s1v)
    assert [lp.cut for lp in v.loops] == [()]
    assert v.cuts == ()


def test_library_loop_view_needs_declared_cut():
    # ngcc_3stage_ff: 루프 뷰가 있고 차동 출력 포트쌍이 없다(출력 Vout 하나) -> 끊는 gate 넷을 선언하면 기록이 사라진다
    _, s1v = H.build_lib("ngcc_3stage_ff")
    loops = [v for v in s1v.views if v.kind == "loop"]
    assert loops and all(not v.cm_pair for v in loops)
    assert "undeclared_loop_constraint" in H.all_codes(s1v)
    gates = tuple(sorted({g for v in loops for _, g in v.cuts}))
    _, declared = H.build_lib("ngcc_3stage_ff", declared_loop_cuts=gates)
    assert "undeclared_loop_constraint" not in H.all_codes(declared)
