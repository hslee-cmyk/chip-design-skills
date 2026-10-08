"""graph/dc_roles.py -- `s1_dc_roles`: MOS 소자 DC 역할(계약 4.4 표 (1)~(5), 4.6, 7.4).

기대값 = 독립 oracle(교류접지 G = 레일 ∪ gate 전용 미구동 넷을 JSON 에서 다시 구하고 표 순서대로 적용)과 계약 7.4 표.

[U1b 2026-10-09] 설계 41 1.12.1 소비 1(복합 diode = 규칙 1c diode 기준, 같은 gs 묶음 나머지는 바이어스)과 40 3.2-3(`dc_role` 사실
override/confirm, 규칙 4)이 표를 바꾼다. 복합 diode 집합은 oracle 이 다시 걷지 않고 `jrules_hand.LIB_COMPOSITE`(손 걷기 표)를
받는다. 바뀐 칸: 파일럿 M58·M63 signal -> diode(1c), sf M5·M6·M7·M8·M13·M14 -> diode(1c), sf 의 J-U3-c 세 묶음 해소 -> M9·M17·M11·
M16·M20 바이어스(41 1.13 '1.12.1 -> DC 역할' 기대 행과 같다). ngcc {M8, M14} 는 기준 없는 묶음이라 그대로 review_needed.
"""
from __future__ import annotations

import collections

import pytest

from gmid_engine.core import ComputeBlock
from gmid_engine.graph import (
    ROLE_RULE_FACT,
    S1_DC_ROLES_WRITER,
    STATUS_RATIFIED,
    DcRole,
    build_s1,
    s1_dc_roles,
    s1_gs_groups,
)
from graph_u2_oracle import U2Oracle

import jrules_hand as J

SIX = (
    "common_gate_amplifier", "current_reuse_telescopic_ota", "ngcc_3stage_ff",
    "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota_sf",
)
NINE = tuple(sorted(SIX + ("folded_cascode", "nmcnr_amplifier", "two_stage_ota")))
# 계약 7.4 표: (diode, bias, signal, review_needed 묶음)
TABLE = {
    "common_gate_amplifier": (0, 2, 1, ()),
    "current_reuse_telescopic_ota": (18, 15, 18, ()),            # [U1b] M58·M63 signal -> diode(1c)
    "folded_cascode": (4, 4, 5, ()),
    "ngcc_3stage_ff": (3, 8, 5, (("M14", "M8"),)),
    "nmcnr_amplifier": (2, 7, 6, ()),
    "pushpull_follower_buffer": (0, 2, 4, ()),
    # [U1b] diode = M4 + 복합 6(M5·M6·M7·M8·M13·M14), bias = M3 + 기준 있는 묶음 나머지 M9·M17·M11·M16·M20, signal = 나머지 9,
    # J-U3-c 세 묶음은 복합 diode 기준이 생겨 해소(41 1.13). 합 22 = MOS 수.
    "sf_pushpull_output_opamp": (7, 6, 9, ()),
    "two_stage_ota": (1, 3, 3, ()),
    "two_stage_ota_sf": (1, 4, 4, ()),
}


def _s1(gh, name):
    return build_s1(gh.load_lib(name), gh.supplies_for(name))


def _oracle(gh, name):
    return U2Oracle(gh.raw(name), composite=J.LIB_COMPOSITE.get(name))


def _counts(roles):
    c = collections.Counter(r[0] for r in roles.values())
    review = tuple(sorted({r[2][2] for r in roles.values() if r[1] == "review_needed"}))
    return c["diode_reference"], c["bias_current_source"], c["signal"], review


@pytest.mark.parametrize("name", NINE)
def test_oracle_matches_contract_table(gh, name):
    assert _counts(_oracle(gh, name).dc_roles) == TABLE[name]


def test_table_totals():
    # MOS 총수 142 는 그대로(28+46+68 = 36+51+55). [U1b] 복합 diode 8 소자가 diode 로, sf 세 묶음 해소로 5 소자가 bias 로 옮겨
    # 남는 review_needed 묶음은 ngcc {M8, M14} 하나(멤버 2)
    tot = [sum(v[i] for v in TABLE.values()) for i in range(3)]
    assert tot == [36, 51, 55]
    groups = [g for v in TABLE.values() for g in v[3]]
    assert len(groups) == 1 and sum(len(g) for g in groups) == 2


@pytest.mark.parametrize("name", NINE)
def test_roles_match_oracle(gh, name):
    o = _oracle(gh, name)
    s1 = _s1(gh, name)
    col = s1.column("device", "dc_role")
    assert tuple(k for k, _ in col) == tuple(sorted(o.mos))         # MOS 레코드에만
    assert all(isinstance(v, DcRole) for _, v in col)
    assert {k: gh.role_plain(v) for k, v in col} == o.dc_roles
    for n in list(o.passives) + list(o.sources):
        with pytest.raises(KeyError):
            s1.value("device", n, "dc_role")


@pytest.mark.parametrize("name", NINE)
def test_diode_always_role_1(gh, name):
    agg = gh.agg(gh.raw(name))
    s1 = _s1(gh, name)
    for n in agg.diodes:
        r = s1.value("device", n, "dc_role")
        assert (r.role, r.status, r.evidence.rule) == ("diode_reference", "derived", "1")


def test_review_needed_group_is_signal_not_stop(gh):
    s1 = _s1(gh, "ngcc_3stage_ff")
    for n in ("M14", "M8"):
        r = s1.value("device", n, "dc_role")
        assert (r.role, r.status, r.evidence.rule, r.evidence.group, r.evidence.basis) == (
            "signal", "review_needed", "2", ("M14", "M8"), ("J-U3-c",))


def test_gate_ground_group_rule(gh, tmp_path):
    # (2) 둘째 행: diode 멤버 없는 묶음의 gate 가 gate 전용 미구동 넷 -> 멤버 전부 bias, basis J-U3-a
    raw = gh.raw("pushpull_follower_buffer")
    raw["netlist"] += [{"name": "Mq1", "kind": "nmos", "drain": "A", "gate": "VNB1", "source": "vss"},
                       {"name": "Mq2", "kind": "nmos", "drain": "B", "gate": "VNB1", "source": "vss"}]
    o = gh.oracle(raw)
    raw.pop("source_manifest", None)    # 변형 문서: 소자 수가 출처 그림과 달라졌다 -- 출처 개수 선언을 뗀다(authoring 10절, 키 없으면 검사 안 함)
    s1 = build_s1(gh.load_raw(tmp_path, raw), gh.supplies_for("pushpull_follower_buffer"))
    # 원본 M6(nmos, gate VNB1, source vss)도 같은 묶음이 된다(JSON 확인)
    m6 = next(e for e in raw["netlist"] if e["name"] == "M6")
    assert (m6["kind"], m6["gate"], m6["source"]) == ("nmos", "VNB1", "vss")
    for n in ("M6", "Mq1", "Mq2"):
        assert gh.role_plain(s1.value("device", n, "dc_role")) == o.dc_roles[n] == (
            "bias_current_source", "derived", ("2", ("VNB1", "vss"), ("M6", "Mq1", "Mq2"), ("J-U3-a",)))


def test_block_declaration():
    assert isinstance(s1_dc_roles, ComputeBlock)
    assert s1_dc_roles.name == S1_DC_ROLES_WRITER
    # [U1b] 41 1.12.1 걷기 조건 (i) '포트 넷이 아니다' -> 포트 방향 열을 읽는다(graph 계약 4.4 끝 문장)
    assert set(s1_dc_roles.reads) == {("device", "element_class"), ("device", "is_diode"), ("device", "kind"),
                                      ("device", "pins"), ("node", "ac_ground_class"), ("node", "is_rail"),
                                      ("node", "port_direction"), ("graph", "gs_groups")}
    assert tuple(s1_dc_roles.writes) == (("device", "dc_role"),)


def test_direct_call_unsupported_mos_stops(gh, tmp_path):
    # 블록 단독 호출에서는 s1_dc_roles 자신이 mos_kind_unsupported 로 정지(4.6)
    raw = gh.raw("two_stage_ota")
    name = raw["netlist"][1]["name"]
    raw["netlist"][1]["kind"] = "njfet"
    doc = gh.load_raw(tmp_path, raw)
    snap = s1_gs_groups(gh.structure_and_bulk(doc, None))
    d, devices = gh.stop(lambda: s1_dc_roles(snap))
    assert d["rule_branch"] == "mos_kind_unsupported"
    assert devices == (name,)




# ---------------------------------------------------------------- [U1b] 규칙 1c·4 (41 1.12.1 소비 1, 40 3.2-3 `dc_role`)
def _s1_facts(gh, name, *rows):
    return build_s1(gh.load_lib(name), gh.supplies_for(name), structure=J.facts(*rows))


def test_composite_group_mates_become_bias_sources(gh):
    # oracle (a) 41 1.12.1 소비 1: sf gs 묶음 (pmos, N5, vdd) = {M6, M9, M17} 에 복합 diode 기준 M6 이 있어 '기준이 있는 묶음'
    # -> M9·M17 은 규칙 2 첫 행 바이어스 전류원(basis 없음). (pmos, N7, vdd) {M8, M11}, (nmos, N13, vss) {M14, M16, M20} 도 같다.
    s1 = _s1(gh, "sf_pushpull_output_opamp")
    for group, mates in ((("M17", "M6", "M9"), ("M9", "M17")), (("M11", "M8"), ("M11",)), (("M14", "M16", "M20"), ("M16", "M20"))):
        for m in mates:
            r = s1.value("device", m, "dc_role")
            assert (r.role, r.status, r.evidence.rule, r.evidence.group, r.evidence.basis) == (
                "bias_current_source", "derived", "2", group, ())


def test_dc_role_fact_overrides_unresolved_group(gh):
    # oracle (d) 40 3.2-3 사실 표 ngcc `dc_role` M8·M14 = signal(override -- 유도 status 가 J-U3-c review_needed 인 소자)
    # -> status ratified, 규칙 4(계약 4.4 (4) 행: evidence basis = (approval_id, 값))
    s1 = _s1_facts(gh, "ngcc_3stage_ff", ("dc_role", "M8", "signal", "A-8"), ("dc_role", "M14", "signal", "A-14"))
    for dev, appr in (("M8", "A-8"), ("M14", "A-14")):
        r = s1.value("device", dev, "dc_role")
        assert (r.role, r.status, r.evidence.rule) == ("signal", STATUS_RATIFIED, ROLE_RULE_FACT)
        assert appr in r.evidence.basis


def test_dc_role_fact_confirm_ratifies_matching_derivation(gh):
    # oracle (d) 40 3.2-3: confirm 사실 값 == 유도 값(복합은 기준·캐스코드 구분 포함)이면 그 유도 레코드 status -> ratified,
    # 역할·규칙은 유도 그대로, approval_id 가 붙는다
    s1 = _s1_facts(gh, "sf_pushpull_output_opamp", ("dc_role", "M6", J.COMPOSITE, "C-6"), ("dc_role", "M5", J.CASCODE, "C-5"),
                   ("dc_role", "M9", "bias_current_source", "C-9"))
    for dev, rule, appr in (("M6", "1c", "C-6"), ("M5", "1c", "C-5"), ("M9", "2", "C-9")):
        r = s1.value("device", dev, "dc_role")
        assert (r.status, r.evidence.rule) == (STATUS_RATIFIED, rule)
        assert appr in r.evidence.basis


@pytest.mark.parametrize("dev,value", [("M8", "bias_current_source"),          # 유도 = 복합 기준
                                       ("M5", J.COMPOSITE),                      # 유도 = 캐스코드 기준(구분이 다르다)
                                       ("M9", "signal")])                        # 유도 = 바이어스
def test_dc_role_fact_mismatch_keeps_derivation_and_is_review_needed(gh, dev, value):
    # oracle (d) 40 3.2-3: 사실 값 != 유도 값 -> 유도 역할 그대로, status review_needed(structure_fact_mismatch)
    base = _s1(gh, "sf_pushpull_output_opamp").value("device", dev, "dc_role")
    r = _s1_facts(gh, "sf_pushpull_output_opamp", ("dc_role", dev, value, "M-1")).value("device", dev, "dc_role")
    assert r.role == base.role and r.evidence.rule == base.evidence.rule
    assert r.status == "review_needed"
    assert "structure_fact_mismatch" in r.evidence.basis


def test_dc_role_facts_enter_s1_key(gh):
    # oracle (d) 40 3.2-3 파이프라인 3: S1 키에 적용된 dc_role 사실 지문 -- 같은 topology 라도 사실이 다르면 S1 이 다르다
    plain = _s1(gh, "ngcc_3stage_ff")
    a = _s1_facts(gh, "ngcc_3stage_ff", ("dc_role", "M8", "signal", "A-8"))
    b = _s1_facts(gh, "ngcc_3stage_ff", ("dc_role", "M8", "signal", "A-9"))
    assert plain.key.facts_fp == "none"
    assert len({plain.key, a.key, b.key}) == 3
    assert a.key.topology_fp == plain.key.topology_fp and a.key.rule_fp == plain.key.rule_fp
