"""graph/ac_ground_view.py -- 뷰별 교류접지(계약 10.2 '교류접지', 불변량 3, 설계 41 1.2, 계획 N3.2-1 (1)(2)(4)).

oracle (a) 손 유도:
- 정적 집합 = 레일 ∪ gate 전용 미구동 넷(입력 포트 아님) -- topology JSON 을 직접 집계한다(`_static`).
- 여기하지 않는 입력 포트는 그 뷰의 교류접지다(루프 뷰에서는 입력 포트 전부).
- (4) 바이어스 종속 넷 술어(N3.2-1): REPLICA 의 b 는 (0) 신호 넷(tail 에서 Mr source->drain), (i) gate 로만 나감(M5·M6·Mr gate),
  (ii) 구동 채널 단자 = b 를 gate 로 읽는 Mr + gate 가 신호 밖인 Mi, (iii) Mr 사슬 출발 = tail(b 없이도 M1/M2 gate->source 로 신호).
  기모드 여기에서 tail 은 자기대응(가상접지)이라 움직이지 않는다 -> b 는 교류접지, 근거 사슬 출발 넷 (tail,).
  같은 회로를 단일 입력으로 여기하면 tail 이 움직인다 -> b 는 교류접지가 아니고 `bias_moving`.
- 전류 미러 diode 넷(OTA5 x)은 사슬 출발이 자기 자신 때문에 신호라 (iii) 불만족 -> 접지가 아니다(N3.2-1 본문 명시).
"""
from __future__ import annotations

import pytest

import s1v_hand as H


def _static(doc):
    """정적 교류접지(계약 graph 4.1 `ac_ground_class`, N3.2-1 (1)(2)) -- JSON 직접 집계."""
    rails = set(doc["supply_nets"])
    inputs = {k for k, v in doc["ports"].items() if v["direction"] == "input"}
    terms = {}
    for e in doc["netlist"]:
        for t, key in (("d", "drain"), ("g", "gate"), ("s", "source")):
            terms.setdefault(e[key], set()).add(t)
    for e in doc["passive_elements"]:
        for net in e["terminals"]:
            terms.setdefault(net, set()).add("t")
    gate_only = {n for n, ts in terms.items() if ts == {"g"} and n not in rails and n not in inputs}
    return rails | gate_only


def test_transfer_view_ground_is_rails_and_gate_only_nets(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    # 손 유도: 레일 vdd·gnd + gate 전용 vb. 두 입력 모두 여기, 미러 diode 넷 x 는 접지 아님
    assert H.view(s1v).ac_ground == ("gnd", "vb", "vdd")


def test_loop_view_grounds_every_input_port(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    # 손 유도: 루프 뷰는 외부 여기원을 모두 접지 -> 입력 포트 inn·inp 추가. x6 은 diode M9 의 source 가 vdd(접지)라
    # (iii) 사슬이 없어 후보 아님, cmfb 는 M5(gate cm 신호) drain 이 구동해 (ii) 불만족 -> 둘 다 접지 아님
    loop = H.view(s1v, "loop:M5:cm")
    assert loop.ac_ground == ("gnd", "inn", "inp", "vb", "vdd", "vref")
    assert loop.bias_dependent == ()


def test_bias_dependent_net_grounded_when_chain_origin_does_not_move(tmp_path):
    _, s1v = H.build(tmp_path, H.REPLICA)
    v = H.view(s1v)
    assert v.bias_dependent == (("b", ("tail",)),)
    assert v.bias_moving == ()
    assert v.ac_ground == ("b", "gnd", "vb", "vbp", "vdd")


def test_bias_dependent_net_not_grounded_when_chain_origin_moves(tmp_path):
    _, s1v = H.build(tmp_path, H.REPLICA_SE)
    for vid, other_input in (("transfer:0", "in2"), ("transfer:1", "in1")):
        v = H.view(s1v, vid)
        assert v.bias_moving == (("b", ("tail",)),)
        assert v.bias_dependent == ()
        assert "b" not in v.ac_ground
        assert v.ac_ground == tuple(sorted({"gnd", "vb", "vbp", "vdd", other_input}))


def test_mirror_diode_node_is_not_ground(tmp_path):
    for doc in (H.OTA5, H.MILLER):
        _, s1v = H.build(tmp_path, doc)
        assert "x" not in H.view(s1v).ac_ground


ALL = [H.OTA5, H.MILLER, H.FOLDED, H.FOLLOWER, H.PUSHPULL, H.CMFB, H.CS, H.CG, H.PASS, H.XCOUP, H.FF, H.REPLICA,
       H.REPLICA_SE, H.AMB, H.MIXED, H.TAP, H.BMULTI, H.CSDIODE, H.BIASSCC, H.RFB, H.RSER, H.CAPROUND, H.LCREV]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_invariant3_ground_superset_of_static_and_excludes_excite_and_sense(tmp_path, doc):
    # 불변량 3: 접지 ⊇ 정적 집합, 여기 넷·감지 넷은 접지가 아니다
    _, s1v = H.build(tmp_path, doc)
    static = _static(doc)
    for v in s1v.views:
        ground = set(v.ac_ground)
        assert static <= ground, (v.id, static - ground)
        assert not ({n for n, _ in v.excite} & ground), v.id
        assert not (set(v.sense) & ground), v.id
        assert list(v.ac_ground) == sorted(v.ac_ground)
