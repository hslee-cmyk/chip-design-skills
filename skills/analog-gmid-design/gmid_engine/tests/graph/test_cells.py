"""graph/cells.py -- 셀 분류(계약 10.2 '셀', 불변량 3, 설계 41 1.4, 계획 N3.2-3).

oracle (a) 손 유도. 규칙(우선순위): gate==drain -> diode_load. gate 가 신호(S): drain 접지 -> cd, source 접지 -> cs, 둘 다 아니면
source 가 순방향 위 다른 신호 셀 입력·출력 포트에 닿을 때 cell_ambiguous(기록만), 아니면 cs(degeneration). gate 가 S 밖: 같은 두
노드 사이 반대 방향 둘(둘 다 gate S 밖) -> pass 묶음(셋 이상·방향 섞임 -> pass_group_unsupported), 아니고 source ∈ S -> cg, 그 밖 off.
셀 이름은 소문자(계약 10.2 규칙 E). `CellInfo.forward` = 출력 단자가 순방향 집합 위.
"""
from __future__ import annotations

import pytest

import s1v_hand as H

VOCAB = {"cs", "cg", "cd", "pass", "diode_load", "off"}


def test_common_source(tmp_path):
    _, s1v = H.build(tmp_path, H.CS)
    # M1: gate in(S), source gnd 접지 -> cs. M2: gate vb(접지), source vdd(S 밖) -> off
    assert H.cells(H.view(s1v)) == {"M1": "cs", "M2": "off"}


def test_common_gate(tmp_path):
    _, s1v = H.build(tmp_path, H.CG)
    # M1: gate vb 신호 밖, source in(여기 포트, S) -> cg. M2·M3: gate 신호 밖, source 레일 -> off
    assert H.cells(H.view(s1v)) == {"M1": "cg", "M2": "off", "M3": "off"}


def test_common_drain(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLLOWER)
    # M1: gate in(S), drain vdd 접지 -> cd. M2 off
    assert H.cells(H.view(s1v)) == {"M1": "cd", "M2": "off"}


def test_five_transistor_ota(tmp_path):
    _, s1v = H.build(tmp_path, H.OTA5)
    v = H.view(s1v)
    # M3 gate==drain -> diode_load. M1/M2: gate S, drain·source 비접지, source tail 이 다른 셀 입력(gate)·출력 포트에 닿지 않음
    # -> cs(degeneration). M4: gate x(S), source vdd 접지 -> cs. M5: gate vb 접지, source gnd -> off
    assert H.cells(v) == {"M1": "cs", "M2": "cs", "M3": "diode_load", "M4": "cs", "M5": "off"}
    deg = {c.dev: c.degeneration for c in v.cells}
    assert (deg["M1"], deg["M2"], deg["M4"]) == (True, True, False)


def test_folded_cascode(tmp_path):
    _, s1v = H.build(tmp_path, H.FOLDED)
    # M5/M6: gate vbc 신호 밖, source fx/fy ∈ S -> cg(캐스코드). M7 diode. M8: gate ox(S), source gnd -> cs
    assert H.cells(H.view(s1v)) == {"M0": "off", "M1": "cs", "M2": "cs", "M3": "off", "M4": "off", "M5": "cg",
                                    "M6": "cg", "M7": "diode_load", "M8": "cs"}


def test_anti_parallel_pass_bundle(tmp_path):
    _, s1v = H.build(tmp_path, H.PASS)
    v = H.view(s1v)
    # M3(a->b)·M4(b->a): 같은 두 노드 a·b 사이 반대 방향, 둘 다 gate 신호 밖 -> pass 묶음 하나
    assert H.cells(v) == {"M1": "cs", "M2": "off", "M3": "pass", "M4": "pass", "M5": "off"}
    assert [(b.members, b.nodes) for b in v.pass_bundles] == [(("M3", "M4"), ("a", "b"))]


def test_three_device_bundle_is_recorded_unsupported(tmp_path):
    _, s1v = H.build(tmp_path, H.PASS3)
    v = H.view(s1v)
    hits = [f for f in v.findings if f.code == "pass_group_unsupported"]
    assert len(hits) == 1
    assert hits[0].severity == "unsupported_rule_branch"
    assert set(hits[0].subject) == {"M3", "M4", "M6"}
    assert v.pass_bundles == ()


def test_source_on_output_port_is_ambiguous(tmp_path):
    _, s1v = H.build(tmp_path, H.AMB)
    v = H.view(s1v)
    # M1: gate in(S), drain x·source s1 모두 비접지, source s1 이 출력 포트 -> CD·CS 이중 출력(기록만)
    hits = [f for f in v.findings if f.code == "cell_ambiguous"]
    assert [h.severity for h in hits] == ["unsupported_rule_branch"]
    assert "M1" in hits[0].subject


def test_forward_flag_follows_output_terminal(tmp_path):
    _, amb = H.build(tmp_path, H.AMB)
    _, lat = H.build(tmp_path, H.BIASSCC)
    fwd_amb = {c.dev: c.forward for c in H.view(amb).cells}
    fwd_lat = {c.dev: c.forward for c in H.view(lat).cells}
    # AMB M1 출력 x 는 순방향 밖 / BIASSCC: M1 출력 out 은 순방향, 막다른 Mg·Mp1·Mp2 출력 p·q 는 밖
    assert fwd_amb["M1"] is False
    assert (fwd_lat["M1"], fwd_lat["Mg"], fwd_lat["Mp1"], fwd_lat["Mp2"]) == (True, False, False, False)


def test_loop_view_reads_cells_from_its_own_excitation(tmp_path):
    _, s1v = H.build(tmp_path, H.CMFB)
    # 루프 뷰 loop:M5:cm: 입력 포트 접지 -> M1/M2 gate 접지·source tail 은 신호 아님 -> off. cm -> M5 cs(source t2 비접지).
    # cmfb -> M3/M4 cs. t2 ∈ S, M6 gate vref 접지 -> cg. diode M8/M9, 꼬리 M0/M7 off
    assert H.cells(H.view(s1v, "loop:M5:cm")) == {"M0": "off", "M1": "off", "M2": "off", "M3": "cs", "M4": "cs",
                                                  "M5": "cs", "M6": "cg", "M7": "off", "M8": "diode_load",
                                                  "M9": "diode_load"}


ALL = [H.OTA5, H.MILLER, H.FOLDED, H.FOLLOWER, H.PUSHPULL, H.CMFB, H.CS, H.CG, H.PASS, H.PASS3, H.XCOUP, H.FF,
       H.REPLICA, H.REPLICA_SE, H.AMB, H.MIXED, H.TAP, H.BMULTI, H.CSDIODE, H.BIASSCC, H.RFB, H.RSER, H.LCREV]


@pytest.mark.parametrize("doc", ALL, ids=lambda d: d["topology_name"])
def test_invariant3_every_mos_has_exactly_one_cell(tmp_path, doc):
    _, s1v = H.build(tmp_path, doc)
    for v in s1v.views:
        devs = [c.dev for c in v.cells]
        assert sorted(devs) == sorted(H.json_mos(doc)), v.id
        assert devs == sorted(devs)
        assert {c.kind for c in v.cells} <= VOCAB
