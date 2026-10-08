"""graph/composite_diode.py -- `composite_diodes(projection)`: 복합 diode D1(설계 41 1.12.1, 계약 graph 10.6, 40 3.2-3).

oracle (a) 손 유도(이름 없는 손 회로, `jrules_hand` 머리 주석에 걷기를 적었다):
- 정의: MOS X 의 drain 에서 'DC 가지 걷기'(직렬 노드 = 레일·포트·이상원 단자 넷이 아니고 DC 전류 단자(MOS d·s, 저항 단자)가
  정확히 둘)를 해서 지나간 원소가 하나 이상이고 X 의 gate 넷에 닿으면 복합 diode 소자. 걷기가 원소를 공유하면 한 묶음.
  다른 복합 소자의 걷기에 들지 않는 것이 기준, 나머지 복합 소자는 캐스코드 기준 멤버.
- 무동작: 단순 diode(gate = drain), 직렬 노드에 세 번째 DC 전류 단자, 포트 넷, 이상원 단자 넷. 커패시터·gate 단자는 세지 않는다.
- 소비: DC 역할 규칙 1c(evidence group = 묶음, basis = 하위 구분), 셀 `diode_load`, 미러 입력 넷 확장(복합 소자 gate 넷을 gate 로
  읽는 다른 순방향 셀 -> 미러 입력, 그 셀은 stage 를 시작하지 않고 블록이 미러 출력 쪽으로 이어진다), 묶음 내부 사이클
  `composite_diode_internal`(루프 뷰 없음), L 동치류 주인 `current_source_member`.
oracle (d) 41 1.13 실측 행: library 9회로 발동 = sf {M5, M6, M7, M8, M13, M14}, 파일럿 {M58, M63}, 나머지 7회로 0 -- 손 걷기 표
`jrules_hand.LIB_COMPOSITE` 로 독립 유도해 같은 집합임을 확인했다.
graph `.py` 소스는 열람하지 않았다(계약·설계 문장과 공개 이름만).
"""
from __future__ import annotations

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import Projection
from gmid_engine.graph import (
    ROLE_DIODE_COMPOSITE,
    ROLE_DIODE_COMPOSITE_CASCODE,
    ROLE_RULE_COMPOSITE,
    CompositeDiode,
    build_s1,
    composite_diodes,
    s1_dc_roles,
)

import jrules_hand as J
import s1v_hand as H

NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
        "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")


def _cd(s1):
    """S1 스냅샷에서 소비자(s1_dc_roles)가 선언한 열로 만든 Projection 으로 직접 호출(core 계약 8절 '직접 생성은 test 에서만')."""
    return composite_diodes(Projection.from_snapshot(s1.snapshot, s1_dc_roles.reads))


def _toy(tmp_path, doc, stem=None, **kw):
    return H.build(tmp_path, doc, stem=stem, **kw)


def _lib_s1(name):
    return build_s1(load_topology(str(H.LIBRARY / (name + ".topology.json"))), H.lib_supplies(name))


def test_constants_are_design_vocabulary():
    # 40 3.2-3 `dc_role` 값 어휘·graph 계약 4.4 (1c) 행
    assert (ROLE_DIODE_COMPOSITE, ROLE_DIODE_COMPOSITE_CASCODE, ROLE_RULE_COMPOSITE) == (
        "diode_reference_composite", "diode_reference_composite_cascode", "1c")


def test_resistor_self_biased_cascode_reference(tmp_path):
    s1, _ = _toy(tmp_path, J.RSELF)
    # 손 걷기(jrules_hand RSELF): Ma -> {Mb}, Mb -> {Rx}. 공유 원소 Mb 로 한 묶음 {Ma, Mb, Rx}. Mb 는 Ma 걷기에 들므로 캐스코드,
    # 기준은 Ma 뿐. Mc 는 레일에서, Md·Mi 는 포트에서 걷기 실패.
    assert _cd(s1) == (CompositeDiode(members=("Ma", "Mb", "Rx"), reference=("Ma",), cascode_members=("Mb",),
                                      walk=(("Ma", ("Mb",)), ("Mb", ("Rx",)))),)


def test_replica_with_passed_simple_diode(tmp_path):
    s1, _ = _toy(tmp_path, J.REPL)
    # 손 걷기: Mx q{Mx.d, My.s} -> My(지나간 단순 diode) -> b = gate. My 는 단순 diode(걷기 원소 0) 라 복합 소자가 아니고
    # 묶음 멤버로만 기록. Mi 는 b -> My -> q -> Mx -> tail(DC 단자 4개) 에서 실패.
    assert _cd(s1) == (CompositeDiode(members=("Mx", "My"), reference=("Mx",), cascode_members=(),
                                      walk=(("Mx", ("My",)),)),)


@pytest.mark.parametrize("doc", [H.OTA5, H.MILLER, H.FOLDED, H.CS, J.REPL_3RD, J.PORTSTOP],
                         ids=lambda d: d["topology_name"])
def test_no_composite_without_a_walk(tmp_path, doc):
    # 무동작: 단순 diode 만 있는 회로(OTA5·MILLER·FOLDED), diode 없는 회로(CS), 직렬 노드 q 에 세 번째 DC 단자 Rq(REPL_3RD),
    # 직렬 노드가 출력 포트(PORTSTOP, o 에서 멈춤)
    s1, _ = _toy(tmp_path, doc)
    assert _cd(s1) == ()
    roles = {k: v for k, v in s1.column("device", "dc_role")}
    assert all(r.evidence.rule != ROLE_RULE_COMPOSITE for r in roles.values())


def test_ideal_source_terminal_stops_the_walk(tmp_path):
    # 41 1.12.1 (i): 직렬 노드 q 가 이상 전류원 단자 넷이면 걷기 실패. 같은 회로에 커패시터만 붙인 변형(REPL_CAP)은 그대로 복합.
    stopped, _ = _toy(tmp_path, J.with_ideal_source(J.REPL, "Iq", ("q", "gnd"), "replisrc"))
    capped, _ = _toy(tmp_path, J.REPL_CAP)
    assert _cd(stopped) == ()
    assert [c.reference for c in _cd(capped)] == [("Mx",)]


def test_port_stop_versus_free_series_node(tmp_path):
    # 같은 소자 연결, 출력 포트 위치만 다르다: o 가 포트면 실패(PORTSTOP, 위 test), b 가 포트면 o 는 직렬 노드라 성공
    # (걷기의 첫 판정은 'w = gate 이면 성공' 이라 gate 넷 b 가 포트여도 된다)
    s1, _ = _toy(tmp_path, J.PORTFREE)
    assert [(c.members, c.reference, c.walk) for c in _cd(s1)] == [(("Mx", "My"), ("Mx",), (("Mx", ("My",)),))]


def test_dc_role_rule_1c_and_group_mate_bias(tmp_path):
    s1, _ = _toy(tmp_path, J.RSELF)
    role = {k: (v.role, v.status, v.evidence.rule, v.evidence.group, v.evidence.basis) for k, v in s1.column("device", "dc_role")}
    # 소비 1: 복합 소자 = diode 기준(규칙 1c, group = 묶음, basis = 하위 구분). (pmos, p2, vdd) 묶음 {Ma, Md} 는 기준이 있어
    # Md = 바이어스(규칙 2 첫 행). Mc: gate vb(gate 전용 미구동) + source 레일 -> 규칙 3. Mi: 나머지 signal(규칙 5).
    assert role == {
        "Ma": ("diode_reference", "derived", "1c", ("Ma", "Mb", "Rx"), (ROLE_DIODE_COMPOSITE,)),
        "Mb": ("diode_reference", "derived", "1c", ("Ma", "Mb", "Rx"), (ROLE_DIODE_COMPOSITE_CASCODE,)),
        "Mc": ("bias_current_source", "derived", "3", (), ("J-U3-a",)),
        "Md": ("bias_current_source", "derived", "2", ("Ma", "Md"), ()),
        "Mi": ("signal", "derived", "5", (), ()),
    }


@pytest.mark.parametrize("doc,mos", [(J.RSELF, {"Ma", "Mb"}), (J.SFLOAD, {"Ma", "Mb"}), (J.REPL, {"Mx", "My"})],
                         ids=["rself", "sfload", "repl"])
def test_bundle_mos_members_are_diode_load_cells(tmp_path, doc, mos):
    # 소비 2(셀 분류 41 1.4-1): 묶음의 MOS 멤버(손 걷기 묶음의 MOS)는 diode_load(신호 경로 밖이어도 -- 규칙 1 과 같은 자리, 계약 불변량 (a))
    _, s1v = _toy(tmp_path, doc)
    for v in s1v.views:
        cells = H.cells(v)
        assert {m: cells[m] for m in mos} == {m: "diode_load" for m in mos}


def test_mirror_input_extends_through_bundle_to_mirror_output(tmp_path):
    # 소비 2(41 1.12.1-2, 1.6 적용 순서 ⑧): SFLOAD 신호 in -M1-> n1, 묶음 {Ma, Mb, R1} 이 n1 에 걸린 diode 부하 하나이고
    # 묶음 내부 넷 n5(복합 기준 Ma 의 gate)를 다른 순방향 셀 Mo 가 gate 로 읽는다 -> n5 = 미러 입력(블록 내부 노드), Mo 는 stage 를
    # 시작하지 않고 블록은 미러 출력 out(출력 포트)까지 이어진다. 블록 하나: 키 (out,), stage 1, M1 input·Ma/Mb diode_load·
    # Mo mirror. 출력 포트 out 이 어느 블록에도 들지 않으면 감지 넷의 gain 블록이 없다.
    _, s1v = _toy(tmp_path, J.SFLOAD)
    v = H.view(s1v)
    assert "n5" in v.mirror_inputs
    assert v.stage_starts == ("M1",)
    blocks = H.blocks(v)
    assert list(blocks) == [("out",)]
    b = blocks[("out",)]
    assert (b.kind, b.stage) == ("gain", 1)
    assert {k: r for k, r in b.roles if k in ("M1", "Ma", "Mb", "Mo")} == {
        "M1": "input", "Ma": "diode_load", "Mb": "diode_load", "Mo": "mirror"}


def test_mirror_reading_the_entry_net_extends_the_block(tmp_path):
    # 같은 묶음에서 미러 출력이 진입 넷 n1(캐스코드 기준 Mb 의 gate)을 읽는 변형: n1 = 미러 입력, 블록 (out,) 하나(Mo mirror)
    doc = H.topo("sfn1", tuple((n, k, d, ("n1" if n == "Mo" else g), s) for n, k, d, g, s in (
        (e["name"], e["kind"], e["drain"], e["gate"], e["source"]) for e in J.SFLOAD["netlist"])),
        {"in": H.SE_IN, "out": H.SE_OUT}, passives=(("R1", "resistor", ("n1", "n5")),), bias=("vb",))
    _, s1v = _toy(tmp_path, doc)
    v = H.view(s1v)
    assert "n1" in v.mirror_inputs and v.stage_starts == ("M1",)
    assert [(b.key, dict(b.roles)["Mo"]) for b in v.blocks] == [(("out",), "mirror")]


def test_bundle_internal_cycle_is_composite_diode_internal(tmp_path):
    # 소비 3(41 1.8 분류 (1.6), 1.12.1-3): SFLOAD 신호 그래프의 사이클 n1 -Mb(gate->drain)-> n5 -R1-> n1 은 원소 {Mb, R1} 이
    # 모두 한 묶음 안 -> composite_diode_internal(info), 끊는 점·루프 뷰 없음, `기록만` 정지 없음.
    # 묶음 내부 넷 n56 은 Mb source 진입과 Ma drain 이 함께 든 혼재 노드인데 구동 종류 혼재 판정 대상이 아니라(1.12.1-2) 전류
    # 진입으로 정해지지 않으므로 n56 -> n5(Mb source->drain) 엣지가 없다 -> 묶음 안 사이클은 이 하나뿐.
    _, s1v = _toy(tmp_path, J.SFLOAD, stop_on_unsupported=True)
    v = H.view(s1v)
    assert [(set(lp.nodes), set(lp.devices), lp.classes, lp.cut) for lp in v.loops] == [
        ({"n1", "n5"}, {"Mb", "R1"}, ("composite_diode_internal",), ())]
    assert [v2.kind for v2 in s1v.views] == ["transfer"]
    assert [(f.code, f.severity) for f in v.findings] == [("composite_diode_internal", "info")]
    assert s1v.unsupported == () and s1v.review_needed == ()


def test_l_class_owner_is_composite_reference(tmp_path):
    # 41 1.12.5-2: current_source_member 는 diode 기준(복합 포함)을 고른다 -- {Ma, Md}(pmos, p2, vdd) 주인 Ma
    _, s1v = _toy(tmp_path, J.RSELF)
    assert [(lc.members, lc.owner, lc.owner_rule, lc.status) for lc in s1v.l_classes] == [
        (("Ma", "Md"), "Ma", "current_source_member", "derived")]


@pytest.mark.parametrize("name", NINE)
def test_library_firing_set_matches_hand_walk(name):
    # oracle (a) 손 걷기 표(jrules_hand.LIB_COMPOSITE) = oracle (d) 41 1.13 실측 행. 묶음·기준·캐스코드까지 같다.
    got = _cd(_lib_s1(name))
    hand = J.LIB_COMPOSITE.get(name, {})
    assert {m for c in got for m in c.reference + c.cascode_members} == set(hand)
    bundles = {c.members for c in got}
    assert bundles == {b for b, _ in hand.values()}
    for c in got:
        assert {m: J.COMPOSITE for m in c.reference} == {m: hand[m][1] for m in c.reference}
        assert {m: J.CASCODE for m in c.cascode_members} == {m: hand[m][1] for m in c.cascode_members}


def test_library_seven_circuits_do_not_fire():
    # 41 1.13: 나머지 7회로 0
    quiet = [n for n in NINE if n not in J.LIB_COMPOSITE]
    assert len(quiet) == 7
    assert {n: _cd(_lib_s1(n)) for n in quiet} == {n: () for n in quiet}


@pytest.mark.parametrize("doc", [J.RSELF, J.SFLOAD, J.REPL], ids=lambda d: d["topology_name"])
def test_name_bijection_maps_bundles(tmp_path, doc):
    # 41 1.11 불변식: 이름을 전단사로 바꾸면 결과는 그 사상으로만 바뀐다(정렬 순서를 뒤집는 새 이름 + netlist 순서 섞기)
    nets = sorted(H.json_nets(doc))
    elems = sorted(H.json_mos(doc) | {e["name"] for e in doc["passive_elements"]})
    nm = {n: "w%02d" % (len(nets) - i) for i, n in enumerate(nets)}
    dm = {n: "E%02d" % (len(elems) - i) for i, n in enumerate(elems)}
    base, _ = H.build(tmp_path, doc, stem="base")
    moved, _ = H.build(tmp_path, H.rename(doc, nm, dm, seed=5), stem="moved", supplies={nm[r]: v for r, v in H.SUPPLIES.items()})

    def canon(cds, f):
        return {(frozenset(map(f, c.members)), frozenset(map(f, c.reference)), frozenset(map(f, c.cascode_members)),
                 frozenset((f(x), frozenset(map(f, w))) for x, w in c.walk)) for c in cds}

    assert canon(_cd(base), dm.get) == canon(_cd(moved), lambda x: x)
