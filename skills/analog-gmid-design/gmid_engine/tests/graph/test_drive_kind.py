"""graph/drive_kind.py -- 입력 노드 구동 종류(계약 10.2 '구동 종류', 설계 41 1.5, 계획 N3.2-5·9 (a), 용어집).

oracle (a) 손 유도. 규칙: 1 여기 포트·source 진입 = 전압, drain 진입만 = 전류 후보. 3 전류 진입 노드는 나가는 쪽으로 -- gate 로만
= 전압, 채널로만 = 전류, 둘 다면 gate 쪽 셀 출력이 순방향 위일 때 전압 아니면 tap(전류로 기록, gate 쪽 셀은 9 (a) 기록만).
4 혼재(source 진입 + 다른 소자 drain) = drain 쪽 DC 역할: 바이어스 전류원 -> 전압, 신호 소자 -> mixed_drive_signal_drain.
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


def test_mixed_node_with_signal_drain_is_review_needed(tmp_path):
    _, s1v = H.build(tmp_path, H.MIXED)
    v = H.view(s1v)
    # out: M1 source 진입 + M2 drain. M2 DC 역할 = 신호(gate 가 입력 포트 -> G 밖, gs 묶음 없음) -> review_needed
    hits = [f for f in v.findings if f.code == "mixed_drive_signal_drain"]
    assert [h.severity for h in hits] == ["review_needed"]
    assert "out" in hits[0].subject


def test_bias_drain_on_mixed_node_gives_voltage_without_record(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    # OTA5 tail 이 혼재 노드(4)이고 drain 쪽 M5 가 바이어스 전류원 -> 기록 없이 전압
    v = H.view(s1v)
    assert H.drive(v)["tail"] == "voltage"
    assert "mixed_drive_signal_drain" not in H.codes(v)


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
