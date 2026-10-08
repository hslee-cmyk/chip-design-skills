"""graph/blocks.py -- 블록·출력노드·차동 블록·AC 역할(계약 10.2 '블록', 불변량 4, 설계 41 1.7, 계획 N3.2-6·9 (c)).

oracle (a) 손 유도. 시작 셀마다 블록을 열고 캐스코드·미러 연장·pass 를 따라 다음 시작 셀 입력이나 출력 포트에 닿은 노드가
출력노드. 같은 stage 블록이 넷을 공유하면 합친다(차동 블록). 블록 stage = 시작 셀 입력 넷 stage_dist + 1. 키 = 출력노드 정렬 tuple.
AC 역할 이름(계획 N3.2-6): input = 시작 셀(신호 입력 단자가 stage 입력 넷에), cascode = CG 사슬, follower = CD, pass = pass 구성
소자, load = 블록 노드에 단자가 붙었으나 신호 셀이 아닌 소자. 출력노드 등급이 낮은 CS 블록 = 9 (c) `cs_output_low_impedance`(기록만).
"""
from __future__ import annotations

import pytest

import s1v_hand as H


def test_five_transistor_ota_is_one_block(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    v = H.view(s1v)
    # M1 블록이 미러(x -> M4)로 out 까지 연장되고 M2 블록(out)과 tail·out 을 공유 -> 같은 stage 1 차동 블록 하나
    assert list(H.blocks(v)) == [("out",)]
    b = H.blocks(v)[("out",)]
    assert (b.kind, b.stage, b.inputs, b.outputs, b.status) == ("gain", 1, ("inn", "inp"), ("out",), "derived")
    r = H.roles(b)
    assert (r["M1"], r["M2"]) == ("input", "input")
    assert {"M3", "M4", "M5"} <= set(r)
    # 블록 노드 = 입력 넷부터 출력노드까지 신호 경로 노드 ∪ 셀 단자 노드(교류접지 제외, degeneration 노드 포함)
    assert b.nodes == ("inn", "inp", "out", "tail", "x")


def test_two_stage_miller_has_two_gain_blocks(tmp_path):
    _, s1v = H.build(tmp_path, H.MILLER)
    v = H.view(s1v)
    bl = H.blocks(v)
    assert sorted(bl) == [("o1",), ("out",)]
    first, second = bl[("o1",)], bl[("out",)]
    assert (first.stage, first.inputs, first.outputs) == (1, ("inn", "inp"), ("o1",))
    # 2단: M6 이 o1(전압 구동, 앞 블록 출력노드)을 gate 로 받아 stage 2 를 연다
    assert (second.stage, second.inputs, second.outputs) == (2, ("o1",), ("out",))
    assert H.roles(second)["M6"] == "input"
    assert H.roles(second)["M7"] == "load"


def test_fully_differential_block_key_has_both_outputs(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    v = H.view(s1v)
    # 반쪽 블록 om·op 가 tail 을 공유하는 같은 stage -> 차동 블록 하나, 키 = 두 출력노드 정렬
    assert list(H.blocks(v)) == [("om", "op")]
    b = H.blocks(v)[("om", "op")]
    assert (b.stage, b.inputs, b.outputs) == (1, ("inn", "inp"), ("om", "op"))
    r = H.roles(b)
    assert (r["M1"], r["M2"], r["M3"], r["M4"], r["R1"], r["R2"]) == ("input", "input", "load", "load", "load", "load")


def test_cascode_extends_block(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    v = H.view(s1v)
    assert list(H.blocks(v)) == [("out",)]
    r = H.roles(H.blocks(v)[("out",)])
    assert (r["M1"], r["M2"], r["M5"], r["M6"], r["M3"], r["M4"]) == ("input", "input", "cascode", "cascode", "load", "load")


def test_common_gate_block_input_is_source(tmp_path):
    _, s1v = H.build(tmp_path, H.CG)
    b = H.blocks(H.view(s1v))[("out",)]
    assert (b.stage, b.inputs, H.roles(b)["M1"], H.roles(b)["M2"]) == (1, ("in",), "input", "load")


def test_pass_devices_belong_to_block(tmp_path):
    _, s1v = H.build(tmp_path, H.PASS)
    blocks = H.view(s1v).blocks
    roles = {d: r for b in blocks for d, r in b.roles}
    assert (roles["M3"], roles["M4"]) == ("pass", "pass")


def test_diode_loaded_cs_output_low_impedance_is_recorded(tmp_path):
    _, s1v = H.build(tmp_path, H.CSDIODE)
    v = H.view(s1v)
    # out 은 diode M2 의 drain+gate(낮음)이고 out 을 gate 로 읽는 다른 소자가 없다 -> 종단 diode 부하, 9 (c)
    hits = [f for f in v.findings if f.code == "cs_output_low_impedance"]
    assert [(h.severity, h.subject) for h in hits] == [("unsupported_rule_branch", ("out",))]


def test_mirror_load_does_not_trigger_low_impedance(tmp_path):
    for doc in (H.OTA5, H.MILLER, H.FOLDED):
        _, s1v = H.build(tmp_path, doc)
        assert "cs_output_low_impedance" not in H.codes(H.view(s1v)), doc["topology_name"]


OK_CIRCUITS = [H.OTA5, H.MILLER, H.FOLDED, H.CMFB, H.CS, H.CG, H.FOLLOWER, H.PUSHPULL, H.REPLICA, H.REPLICA_SE,
               H.LCREV, H.FF, H.TAP, H.CAPROUND]


@pytest.mark.parametrize("doc", OK_CIRCUITS, ids=lambda d: d["topology_name"])
def test_invariant4_block_keys_and_exclusive_owned_nodes(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    for v in s1v.views:
        keys = [b.key for b in v.blocks]
        assert len(set(keys)) == len(keys), v.id                       # 한 뷰 안 블록 키는 하나씩
        merges = {n for c in v.composites for n in c.merge_nodes}
        overlap_recorded = "block_node_overlap" in H.codes(v)
        owned = {}
        for b in v.blocks:
            assert b.key == tuple(sorted(b.outputs)), (v.id, b.key)
            assert set(b.outputs) <= set(b.nodes)
            assert not set(b.nodes) & set(v.ac_ground)
            for n in set(b.nodes) - set(b.inputs):
                if n in owned:
                    assert n in merges or overlap_recorded, (v.id, n, owned[n], b.key)
                owned[n] = b.key


def test_pass_bundle_extends_block_to_output_port(tmp_path):
    # 41 1.7 (1) '캐스코드 사슬, 미러 연장, pass 묶음을 따라가 ... 출력 포트에 닿은 노드가 출력노드', 계획 N3.2-6 'CD·pass 로 끝나면
    # 그 소자의 출력 단자 노드'. PASS: CS M1 -> a -> 역병렬 pass M3/M4 -> b(출력 포트) -> 출력노드 b.
    _, s1v = H.build(tmp_path, H.PASS)
    v = H.view(s1v)
    assert [b.key for b in v.blocks] == [("b",)]
    assert "cs_output_low_impedance" not in H.codes(v)


def test_invariant4_overlap_needs_composite_or_record(tmp_path):
    # MIXED: out 에 CD(M1) 버퍼와 CS(M2) 이득 블록이 함께 출력 -> 두 블록이 out 을 소유. 불변량 4: 겹침은 복합 블록 합류이거나
    # block_node_overlap 기록이어야 하고, 한 뷰의 블록 키는 하나씩이어야 한다.
    _, s1v = H.build(tmp_path, H.MIXED)
    v = H.view(s1v)
    keys = [b.key for b in v.blocks]
    merges = {n for c in v.composites for n in c.merge_nodes}
    assert len(keys) == len(set(keys)) or "out" in merges or "block_node_overlap" in H.codes(v), (keys, H.codes(v))
