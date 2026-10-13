"""graph/drive_kind.py -- 입력 노드 구동 종류(계약 10.2 '구동 종류', 설계 41 1.5, 계획 N3.2-5·9 (a), 용어집).

oracle (a) 손 유도. 규칙: 1 여기 포트·source 진입 = 전압, drain 진입만 = 전류 후보. 3 전류 진입 노드는 나가는 쪽으로 -- gate 로만
= 전압, 채널로만 = 전류, 둘 다면 gate 쪽 셀 출력이 순방향 위일 때 전압 아니면 tap(전류로 기록, gate 쪽 셀은 9 (a) 기록만).
4 혼재(source 진입 + 다른 소자 drain) = 41 v1.8 §1.5-4: (i) source 쪽 follower -> 전압(`follower`), (ii) drain 쪽 gate 신호 -> 전류(`cascode`), 아니면 전압.
2·5 저항·pass 로만 들어오면 이웃 종류 상속(저항은 value_dependent). ratified `drive_kind` 사실은 그 넷을 고정(근거 ratified_fact).
"""
from __future__ import annotations

import json

from gmid_engine.graph import load_structure_facts, s1v_rule_fp

import s1v_hand as H


def test_ports_and_source_entry_are_voltage(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLLOWER)
    # in = 여기 포트, out = CD source 진입
    assert H.drive(H.view(s1v)) == {"in": "voltage", "out": "voltage"}


def test_five_transistor_ota(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    # x: M1 drain 진입 -> M3/M4 gate 로만 나감 = 전압. tail: M1/M2 source 진입 + 꼬리 M5 drain(DC 역할 바이어스 전류원:
    # gate vb ∈ G, source 레일) = 전압. out: drain 진입, 나가는 단자 없음 = 전류
    assert H.drive(H.view(s1v)) == {"inn": "voltage", "inp": "voltage", "out": "current", "tail": "voltage",
                                    "x": "voltage"}


def test_folded_node_is_current_driven(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    d = H.drive(H.view(s1v))
    # fx/fy: drain 진입(M1/M2) -> 채널(M5/M6 source)로만 나감 = 전류. ox: M5 drain 진입 -> M8·M7 gate 로만 = 전압
    assert (d["fx"], d["fy"], d["ox"], d["out"]) == ("current", "current", "voltage", "current")


def test_pass_bundle_inherits_neighbour_kind(tmp_path):
    _, s1v = H.build(tmp_path, H.PASS)
    d = H.drive(H.view(s1v))
    # a: drain 진입 -> pass 채널로만 = 전류. b: pass 묶음으로만 들어옴 -> a 의 종류 상속
    assert d["a"] == "current"
    assert d["b"] == d["a"]


def test_resistor_inheritance_is_value_dependent(tmp_path):
    _, s1v = H.build(tmp_path, H.RSER)
    info = {i.net: i for i in H.view(s1v).drive_kind}
    # out 은 R1 로만 들어온다 -> a(전류) 상속 + value_dependent
    assert info["out"].kind == info["a"].kind == "current"
    assert info["out"].value_dependent is True
    assert info["a"].value_dependent is False


def test_tap_node_and_gate_on_current_node(tmp_path):
    _, s1v = H.build(tmp_path, H.TAP)
    v = H.view(s1v)
    info = {i.net: i for i in v.drive_kind}
    # fx: drain 진입 -> 채널(M5 source)과 gate(Mt) 양쪽, Mt 출력 t 는 순방향 밖 -> tap(전류로 기록)
    assert info["fx"].kind == "current" and info["fx"].tap is True
    hits = [f for f in v.findings if f.code == "gate_on_current_node"]
    assert len(hits) == 1 and hits[0].severity == "unsupported_rule_branch"
    assert "Mt" in hits[0].subject


# [U17 ①-d 다시 씀] 41 v1.8 §1.5-4 혼재 노드 C-1 + 보완 (가)(사용자 결정 2026-10-12 "7절 권고대로"·"1, 가로 해"): 옛 규칙 4 'drain 쪽 DC
# 역할로 가름(신호 소자 -> mixed_drive_signal_drain review)'은 design 이 통째로 대체했다. 41 §9 표 toy 셋(이름 없는 구조):
#  (i) source 쪽 소자 drain = 교류 접지(레일), gate = 그 뷰의 신호 넷 -> follower, 전압 구동(근거 `follower`)
#  (ii) 아니면 drain 쪽 소자 gate 가 신호 넷 -> 전류 구동(근거 `cascode`), 신호 넷이 아니면 전압 구동(그 뷰에서 고정 전류원)
# 혼재 판정에서 review 기록은 더 나오지 않는다(옛 코드 mixed_drive_signal_drain·mixed_drive_unresolved_group 없음).
_OLD_MIXED_CODES = ("mixed_drive_signal_drain", "mixed_drive_unresolved_group")

# 둘째 toy: x = M1 drain(gate in = 신호) + M2 source(gate in 신호, drain out -- 레일 아님 -> follower 아님)
CASCODE_MIX = H.topo("cascmix", (("M1", "nmos", "x", "in", "gnd"), ("M2", "nmos", "out", "in", "x"), ("M3", "pmos", "out", "vbp", "vdd")),
                     {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vbp",))
# 셋째 toy: x = M1 drain(CG, gate vb = 바이어스 넷 -- 신호 아님) + M2 source(drain out -- 레일 아님)
BIAS_MIX = H.topo("biasmix", (("M1", "nmos", "x", "vb", "in"), ("M2", "nmos", "out", "in", "x"), ("M3", "pmos", "out", "vbp", "vdd"),
                              ("M4", "nmos", "in", "vb2", "gnd")),
                  {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vb", "vbp", "vb2"))


def test_mixed_node_source_follower_is_voltage(tmp_path):
    # 첫째 toy(H.MIXED): out = M1 source(drain vdd 레일, gate in = 입력 포트 신호) + M2 drain -> (i) follower, 전압, review 없음
    _, s1v = H.build(tmp_path, H.MIXED)
    v = H.view(s1v)
    info = {i.net: i for i in v.drive_kind}
    assert (info["out"].kind, info["out"].basis) == ("voltage", "follower")
    assert not set(_OLD_MIXED_CODES) & set(H.codes(v))


def test_mixed_node_signal_drain_gate_is_current(tmp_path):
    _, s1v = H.build(tmp_path, CASCODE_MIX)
    v = H.view(s1v)
    info = {i.net: i for i in v.drive_kind}
    assert "x" in v.forward_nets                                            # 전제: x 는 신호 경로 위
    assert (info["x"].kind, info["x"].basis) == ("current", "cascode")
    assert not set(_OLD_MIXED_CODES) & set(H.codes(v))


def test_mixed_node_bias_drain_gate_is_voltage(tmp_path):
    _, s1v = H.build(tmp_path, BIAS_MIX)
    v = H.view(s1v)
    info = {i.net: i for i in v.drive_kind}
    assert "vb" not in v.signal_nets and "x" in v.forward_nets              # 전제: drain 쪽 gate 는 신호 넷 아님
    assert info["x"].kind == "voltage" and info["x"].basis not in ("follower", "cascode")
    assert not set(_OLD_MIXED_CODES) & set(H.codes(v))


def test_bias_drain_on_mixed_node_gives_voltage_without_record(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    # OTA5 tail: 꼬리 M5 는 바이어스 전류원 -> 전압, 혼재 기록 없음
    v = H.view(s1v)
    assert H.drive(v)["tail"] == "voltage"
    assert not set(_OLD_MIXED_CODES) & set(H.codes(v))


def test_ratified_drive_fact_fixes_net(tmp_path):
    s1, plain = H.build(tmp_path, H.CS)
    assert H.drive(H.view(plain))["out"] == "current"      # drain 진입·나감 없음
    path = tmp_path / "cs.structure.json"
    # structure.json 형식: pipeline CONTRACT 1절(개념 drive_kind, 대상 넷, 값 voltage|current) + 해시 = S1 topology 지문·s1v_rule_fp
    path.write_text(json.dumps({
        "schema_version": "1", "topology_hash": s1.key.topology_fp, "rule_hash": s1v_rule_fp(),
        "facts": [{"concept": "drive_kind", "subject": "out", "value": "voltage", "status": "ratified",
                   "evidence": {"rule": "hand", "nets": ["out"]}, "approval_id": "T-1"}]}), encoding="utf-8")
    facts = load_structure_facts(str(path), s1.key.topology_fp, s1v_rule_fp())
    _, fixed = H.build(tmp_path, H.CS, structure=facts)
    info = {i.net: i for i in H.view(fixed).drive_kind}
    assert (info["out"].kind, info["out"].basis) == ("voltage", "ratified_fact")
    assert fixed.facts_applied == (("drive_kind", "out"),)


def test_drive_entries_cover_forward_nets(tmp_path):
    # 구동 종류는 stage 경계(셀 입력 노드)용이다 -- 순방향 넷은 모두 종류를 갖고, 신호 넷 밖에는 없다(계약에 범위 명시 없음:
    # 최소 범위만 고정)
    for doc in (H.OTA5, H.FOLDED, H.MILLER, H.CG, H.PASS, H.TAP, H.AMB):
        _, s1v = H.build(tmp_path, doc)
        v = H.view(s1v)
        nets = [i.net for i in v.drive_kind]
        assert nets == sorted(set(nets)), doc["topology_name"]
        assert set(v.forward_nets) <= set(nets) <= set(v.signal_nets), doc["topology_name"]
        assert {i.kind for i in v.drive_kind} <= {"voltage", "current"}
