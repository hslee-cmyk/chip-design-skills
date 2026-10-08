"""graph/net_model.py -- 뷰가 다루는 넷 모델(계약 10.2·10.3 불변량 3·6: 접지 집합·신호 넷·극점 노드가 모두 같은 넷 공간 위).

oracle (a): topology JSON 의 단자 넷 집합(MOS d/g/s + 수동소자 단자 + 레일, 직접 집계)이 뷰마다 교류접지와 극점 노드로 정확히
나뉜다(불변량 6 의 여집합 형태). 신호·순방향·가상접지·여기·감지 넷은 모두 그 넷 공간 안이다. 원소 이름(MOS·수동소자)은
셀·블록 역할에서 넷 이름과 섞이지 않는다.
"""
from __future__ import annotations

import pytest

import s1v_hand as H

ALL = [H.OTA5, H.MILLER, H.FOLDED, H.FOLLOWER, H.PUSHPULL, H.CMFB, H.CS, H.CG, H.PASS, H.XCOUP, H.FF, H.REPLICA,
       H.REPLICA_SE, H.TAP, H.CSDIODE, H.BIASSCC, H.RFB, H.RSER, H.CAPROUND, H.LCREV]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_views_partition_topology_nets(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    nets = H.json_nets(doc)
    for v in s1v.views:
        ground, poles = set(v.ac_ground), {p.net for p in v.pole_nodes}
        assert ground | poles == nets, v.id
        assert not ground & poles, v.id
        for field in (v.signal_nets, v.forward_nets, v.virtual_ground, v.sense, tuple(n for n, _ in v.excite)):
            assert set(field) <= nets, v.id


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_role_subjects_are_elements(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    elements = H.json_mos(doc) | {e["name"] for e in doc["passive_elements"]}
    for v in s1v.views:
        for b in v.blocks:
            assert {d for d, _ in b.roles} <= elements, (v.id, b.key)
            assert set(b.nodes) <= H.json_nets(doc)
