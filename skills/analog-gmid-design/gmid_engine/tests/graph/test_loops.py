"""graph/loops.py -- 루프 탐지(계약 10.2 '루프', 불변량 7, 설계 41 1.8, 계획 N3.2-2 '기본 폐경로의 정의').

oracle (a) 손 유도. 방향 신호 그래프(교류접지·그 뷰의 여기 포트 제거): gate->drain·gate->source, CG 또는 전류 진입 source 의
source->drain, 수동소자·pass 는 양방향. 단순 사이클 전수, 시작 = 사이클 이름 최소 노드. 세지 않는 것: 수동소자 하나의 왕복,
pass 묶음 내부 왕복, 자기 엣지(diode), 수동소자만의 사이클. 사이클 개수·걸음 수가 count_budget 초과 ->
`cycle_enumeration_over_budget`(기록만 -> 기본 모드 정지).
"""
from __future__ import annotations

import pytest

from gmid_engine.core import StructureUnresolvedError, exit_code_for

import s1v_hand as H

PASSIVES = {"Cc", "R1", "R2", "Rf", "Rin", "C1", "C2", "CL"}


def _loops(v):
    return sorted((lp.nodes, lp.devices) for lp in v.loops)


def test_miller_loop(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    # o1 -M6 gate->drain-> out -Cc-> o1 (o1 < out 이므로 o1 에서 시작)
    assert _loops(H.view(s1v)) == [(("o1", "out"), ("M6", "Cc"))]


def test_cmfb_two_loops_in_unreduced_view(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    # 비축약 기준(cm 은 축약 뷰에서 가상접지지만 루프는 비축약에서 센다): cm -M5-> cmfb -M3-> om -R1-> cm, 같은 길의 op/M4/R2.
    # om -R1-> cm -R2-> op 는 op 에서 cm 으로 R2 를 되돌아가는 왕복뿐이라 사이클이 아니다.
    expected = [(("cm", "cmfb", "om"), ("M5", "M3", "R1")), (("cm", "cmfb", "op"), ("M5", "M4", "R2"))]
    assert _loops(H.view(s1v)) == expected
    assert _loops(H.view(s1v, "loop:M5:cm")) == expected


def test_cross_coupled_loop(tmp_path):
    _, s1v = H.build(tmp_path, H.XCOUP)
    # om -M4 gate->drain-> op -M3 gate->drain-> om
    assert _loops(H.view(s1v)) == [(("om", "op"), ("M4", "M3"))]


def test_passive_only_round_trips_are_not_loops(tmp_path):
    _, s1v = H.build(tmp_path, H.CAPROUND)
    # x-tail 사이 C1·C2 는 수동소자만의 왕복·사이클뿐, 능동 엣지로 돌아오는 길(x -> out, tail -> ?)이 없다
    assert H.view(s1v).loops == ()


def test_feedforward_has_no_loop(tmp_path):
    for doc in (H.OTA5, H.FOLDED, H.FF, H.CS, H.CG, H.FOLLOWER, H.PUSHPULL, H.LCREV):
        _, s1v = H.build(tmp_path, doc)
        assert all(v.loops == () for v in s1v.views), doc["topology_name"]


def test_cycle_budget_exceeded_is_recorded_and_stops(tmp_path):
    _, rec = H.build(tmp_path, H.CMFB, count_budget=1)
    codes = H.all_codes(rec)
    assert "cycle_enumeration_over_budget" in codes
    assert all(f.severity == "unsupported_rule_branch" for v in rec.views for f in v.findings
               if f.code == "cycle_enumeration_over_budget")
    with pytest.raises(StructureUnresolvedError) as ei:
        H.build(tmp_path, H.CMFB, count_budget=1, stop_on_unsupported=True)
    assert exit_code_for(ei.value) == 2
    detail = dict(ei.value.record.detail)
    assert detail["reason"] == "unsupported_rule_branch"
    assert "cycle_enumeration_over_budget" in detail["branches"]


def test_large_budget_has_no_budget_record(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    assert "cycle_enumeration_over_budget" not in H.all_codes(s1v)


ALL = [H.MILLER, H.CMFB, H.XCOUP, H.RFB, H.BIASSCC, H.CAPROUND, H.REPLICA_SE, H.REPLICA, H.TAP]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_invariant7_simple_cycles_start_at_min_node(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    for v in s1v.views:
        seen = set()
        for lp in v.loops:
            assert len(set(lp.nodes)) == len(lp.nodes), (v.id, lp.nodes)          # 단순
            assert lp.nodes[0] == min(lp.nodes), (v.id, lp.nodes)                   # 첫 노드 = 최소
            assert len(lp.devices) == len(lp.nodes), (v.id, lp)                     # 노드마다 나가는 엣지 하나
            assert not set(lp.devices) <= PASSIVES, (v.id, lp)                      # 수동소자만의 사이클 제외
            assert len(lp.nodes) >= 2                                               # 자기 엣지 없음
            assert set(lp.nodes) <= {p.net for p in v.pole_nodes} | set(v.virtual_ground)
            key = (lp.nodes, lp.devices)
            assert key not in seen
            seen.add(key)
