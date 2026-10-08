"""graph/stage_bfs.py -- 0-1 BFS 거리와 stage 시작 셀(계약 10.2 'stage', 불변량 5, 설계 41 1.6, 계획 N3.2-4·5).

oracle (a) 손 유도. 엣지 비용: gate->drain 1(gate 가 diode 단자면 0), source->drain·gate->source 0(source 가 전압 구동인 CG 의
source->drain 은 1), 수동소자 0. `dist` = 수동소자 엣지 포함, `stage_dist` = 수동소자 제외. 시작 셀 = 순방향 CS(gate 전압 구동,
미러 입력 노드를 gate 로 읽지 않음, DC 역할이 바이어스 전류원 아님) / source 가 전압 구동인 CG.
"""
from __future__ import annotations

import pytest

import s1v_hand as H


def test_common_source_distance(tmp_path):
    _, s1v = H.build(tmp_path, H.CS)
    v = H.view(s1v)
    assert dict(v.dist) == {"in": 0, "out": 1}           # in -gate->drain(1)-> out
    assert v.stage_starts == ("M1",)


def test_voltage_driven_common_gate_costs_one_and_starts_stage(tmp_path):
    _, s1v = H.build(tmp_path, H.CG)
    v = H.view(s1v)
    # in(여기 포트, 전압) = CG source -> source->drain 비용 1
    assert dict(v.dist) == {"in": 0, "out": 1}
    assert v.stage_starts == ("M1",)


def test_current_driven_cascode_costs_zero(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    v = H.view(s1v)
    # fx·fy = 1(gate->drain), out = fy + 0(전류 구동 CG s->d), ox = fx + 0. tail = gate->source 0
    assert dict(v.dist) == {"inn": 0, "inp": 0, "tail": 0, "fx": 1, "fy": 1, "ox": 1, "out": 1}
    # 캐스코드 M5/M6 은 전류 구동 CG 라 시작하지 않고, M8 은 미러 입력 ox 를 gate 로 읽어 시작하지 않는다
    assert v.stage_starts == ("M1", "M2")
    assert v.mirror_inputs == ("ox",)


def test_diode_gate_costs_zero(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    v = H.view(s1v)
    # x = 1, out = min(inn->out 1, x->out 0(gate 가 diode 단자)) = 1
    assert dict(v.dist) == {"inn": 0, "inp": 0, "tail": 0, "x": 1, "out": 1}
    assert v.stage_starts == ("M1", "M2")
    assert v.mirror_inputs == ("x",)


def test_passive_edges_count_in_dist_not_in_stage_dist(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    v = H.view(s1v)
    # out: Cc(o1-out) 경유 0 -> dist 1 / 수동소자 제외 -> M6 gate->drain -> stage_dist 2
    assert dict(v.dist)["out"] == 1
    assert dict(v.stage_dist)["out"] == 2
    assert dict(v.stage_dist)["o1"] == 1
    assert v.stage_starts == ("M1", "M2", "M6")


def test_dead_end_branch_cell_does_not_start(tmp_path):
    _, s1v = H.build(tmp_path, H.LCREV)
    # M5(gate a, 출력 z 는 순방향 밖)는 시작 셀이 아니다 -- 시작 셀은 순방향 CS 만
    assert H.view(s1v).stage_starts == ("M1", "M3")


ALL = [H.OTA5, H.MILLER, H.FOLDED, H.CS, H.CG, H.CMFB, H.REPLICA, H.REPLICA_SE, H.LCREV, H.FF, H.TAP, H.FOLLOWER,
       H.PUSHPULL, H.PASS]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_invariant5_stage_start_cells(tmp_path, doc):
    s1, s1v = H.build(tmp_path, doc)
    for v in s1v.views:
        info = {c.dev: c for c in v.cells}
        gates = {e["name"]: e["gate"] for e in doc["netlist"]}
        for dev in v.stage_starts:
            assert info[dev].forward, (v.id, dev)
            assert info[dev].kind in ("cs", "cg"), (v.id, dev)            # CD 가 아니다
            assert s1.value("device", dev, "dc_role").role != "bias_current_source", (v.id, dev)
            assert gates[dev] not in v.mirror_inputs, (v.id, dev)
        sd = dict(v.stage_dist)
        assert set(sd) <= set(dict(v.dist))
        assert all(sd[n] >= d for n, d in v.dist if n in sd)   # 수동소자 엣지를 빼면 거리는 줄지 않는다(경로 부분집합)
