"""graph/view_analysis.py -- 뷰 하나의 유도 묶음(계약 10.2 축약/비축약, 불변량 3·6, 설계 41 1.7 (6), 계획 N3.2-3·8 (vi)).

oracle (a) 손 유도(CMFB 기모드 전달 뷰): 축약 뷰에서 cm·cmfb·t2 는 가상접지 -> M5(gate cm)·M3/M4(gate cmfb) 는 gate 접지·source
신호 아님 -> off. 비축약 뷰에서는 om/op 가 R1/R2 로 cm 을 움직여 M5·M3·M4 가 cs. 계획 N3.2-8 (vi)은 '축약·비축약에서 수가 달라지는
셀'을 순방향 셀로 센다 -> M6(비축약 cg 이지만 출력 x6 이 막다른 diode 라 순방향 밖)은 목록에 없다 -> unreduced_diff 소자 = {M3, M4, M5}.
XCOUP 는 두 뷰 모두 M1~M4 가 cs -> 차이 없음.
"""
from __future__ import annotations

import pytest

import s1v_hand as H


def test_cmfb_cells_differing_between_reduced_and_unreduced(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    v = H.view(s1v)
    assert sorted(d for d, _, _ in v.unreduced_diff) == ["M3", "M4", "M5"]
    assert all(H.cells(v)[d] == "off" for d, _, _ in v.unreduced_diff)       # 축약 판독 = 셀 목록


def test_symmetric_circuit_without_cm_path_has_no_difference(tmp_path):
    for doc in (H.XCOUP, H.FOLLOWER, H.CS, H.OTA5):
        _, s1v = H.build(tmp_path, doc)
        assert H.view(s1v).unreduced_diff == (), doc["topology_name"]


def test_view_level_findings_carry_their_view_id(tmp_path):
    for doc in (H.CMFB, H.XCOUP, H.FF, H.TAP):
        _, s1v = H.build(tmp_path, doc)
        for v in s1v.views:
            assert all(f.view == v.id for f in v.findings), v.id
        assert all(f.view == "" for f in s1v.findings)


ALL = [H.OTA5, H.MILLER, H.FOLDED, H.FOLLOWER, H.PUSHPULL, H.CMFB, H.CS, H.CG, H.PASS, H.XCOUP, H.FF, H.REPLICA,
       H.REPLICA_SE, H.TAP, H.BMULTI, H.CSDIODE, H.BIASSCC, H.RFB, H.RSER, H.CAPROUND, H.LCREV, H.AMB, H.MIXED]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_invariants_3_and_6_for_every_view(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    nets = H.json_nets(doc)
    for v in s1v.views:
        # 3: 접지·여기·감지, 순방향 ⊆ 신호, MOS 마다 셀 하나
        assert set(v.forward_nets) <= set(v.signal_nets)
        assert not ({n for n, _ in v.excite} | set(v.sense)) & set(v.ac_ground)
        assert sorted(c.dev for c in v.cells) == sorted(H.json_mos(doc))
        # 6: 극점 노드 = 접지가 아닌 모든 넷
        assert {p.net for p in v.pole_nodes} == nets - set(v.ac_ground)
        # 모음은 이름순 tuple(ViewS1v docstring)
        for field in (v.ac_ground, v.signal_nets, v.forward_nets, v.virtual_ground, v.stage_starts, v.mirror_inputs):
            assert list(field) == sorted(field)
