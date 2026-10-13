"""graph/orbit_matching_crosstab.py -- `orbit_matching_crosstab(s1) -> OrbitMatchingCrosstab(orbits, records, findings)` (graph CONTRACT 4.8,
설계 40 v1.8 §6-5 '불변식', §10.2 행 'diff_pair review(§6-5, (나'))', 사용자 결정 2026-10-12 "나'로 진행해").

판정(40 §6-5 문언):
- 궤도와 matching 사이 포함 관계를 불변식으로 두지 않고 대조 표를 보고한다: MOS 궤도마다 걸친 matching 레코드, matching 레코드마다 걸친 궤도.
  수동소자 궤도는 표에서 뺀다.
- review 는 하나뿐(`diff_pair_orbit_split`): `diff_pair` 두 멤버가 다른 궤도이고 (a) 출력 포트가 차동 쌍(`differential_output_p/n`), (b) 두 gate 가
  차동 입력 포트 p/n 일 때만. 그 밖의 diff_pair 궤도 불일치는 기록만.
- 9 library 회로 review 0. 파일럿 M1a/M1b 같은 궤도, M37a/M37b 는 gate 가 Voc/Voc_des 라 대상 아님, 단일 출력 회로는 (a)에 걸리지 않는다.
- 실제 거부: 파일럿에서 넷 하나를 비대칭으로 바꾼 합성 회로(§10.2).
oracle (a): topology 연결표 손 유도(궤도 분리 원인·포트 role), (d) 9회로 기대(design 문언).
"""
from __future__ import annotations

import json

import pytest

from gmid_engine.graph import GRAPH_KEY, OrbitMatchingCrosstab, build_s1, orbit_matching_crosstab

import s1v_hand as H

NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
        "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")
PILOT = "current_reuse_telescopic_ota"
CODE = "diff_pair_orbit_split"


def _raw(name):
    return json.loads((H.LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def _s1(tmp_path, doc, name):
    return build_s1(H.load(tmp_path, doc), H.lib_supplies(name))


def _passive_names(doc):
    return {e["name"] for k in ("passive_elements", "ideal_sources") for e in (doc.get(k) or [])}


@pytest.mark.parametrize("name", NINE)
def test_library_crosstab_recorded_and_no_review(name, tmp_path):
    doc = _raw(name)
    s1 = _s1(tmp_path, doc, name)
    t = orbit_matching_crosstab(s1)
    assert isinstance(t, OrbitMatchingCrosstab)
    assert t.findings == ()                                                  # 9회로 review 0
    mos = {e["name"] for e in doc["netlist"]}
    in_rows = {m for members, _recs in t.orbits for m in members}
    assert in_rows == mos                                                    # MOS 궤도마다 행(모든 MOS 가 한 행에)
    assert not (in_rows & _passive_names(doc))                               # 수동소자·이상원 궤도는 표에서 뺀다
    groups = s1.value("graph", GRAPH_KEY, "matching_groups")
    assert [(k, m) for k, m, _o in t.records] == [(g.kind, g.members) for g in groups]   # 레코드마다 한 행(S1 순서)
    for kind, members, orbit_rows in t.records:                             # 레코드가 걸친 궤도 = 멤버를 품는 궤도 행
        assert {m for row in orbit_rows for m in row} >= set(members) & mos
        assert all(row in [r for r, _ in t.orbits] for row in orbit_rows)


def test_pilot_rows_by_hand(tmp_path):
    """파일럿: diff_pair {M1a, M1b} 는 한 궤도(반회로 반사 Vip<->Vim, Vop<->Vom), diff_pair {M37a, M37b} 는 gate Voc / Voc_des 가 다른 구조라 두 궤도
    -- gate 가 입력 포트가 아니므로 기록만."""
    t = orbit_matching_crosstab(_s1(tmp_path, _raw(PILOT), PILOT))
    rec = {(k, m): o for k, m, o in t.records}
    assert rec[("diff_pair", ("M1a", "M1b"))] == (("M1a", "M1b"),)
    assert len(rec[("diff_pair", ("M37a", "M37b"))]) == 2
    assert t.findings == ()


def test_single_output_split_diff_pair_is_record_only(tmp_path):
    """folded_cascode: 단일 출력(out 하나) -> M1·M2 가 다른 궤도여도 (a) 불충족, 기록만."""
    t = orbit_matching_crosstab(_s1(tmp_path, _raw("folded_cascode"), "folded_cascode"))
    rec = {(k, m): o for k, m, o in t.records}
    assert len(rec[("diff_pair", ("M1", "M2"))]) == 2
    assert t.findings == ()


def _pilot_asym():
    """파일럿에서 넷 하나만 비대칭으로: 입력 샘플 커패시터 Cs2 의 접지 끝 gnd -> vdd(Cs1 은 gnd 그대로). Vip 와 Vim 의 이웃 구조가 달라져
    Vip<->Vim 반사가 자기동형이 아니다 -> 입력 gate diff_pair {M1a, M1b}·{M4a, M4b} 가 다른 궤도. 출력 포트는 차동 쌍(Vop/Vom) 그대로."""
    doc = _raw(PILOT)
    doc["topology_name"] = "pilot_asym_cs2"
    for e in doc["passive_elements"]:
        if e["name"] == "Cs2":
            assert e["terminals"] == ["Vim", "gnd"]                         # 전제(연결표)
            e["terminals"] = ["Vim", "vdd"]
    doc.pop("source_manifest", None)
    return doc


def test_pilot_asymmetric_synthetic_is_review(tmp_path):
    t = orbit_matching_crosstab(_s1(tmp_path, _pilot_asym(), PILOT))
    rec = {(k, m): o for k, m, o in t.records}
    assert len(rec[("diff_pair", ("M1a", "M1b"))]) == 2                      # 전제: 다른 궤도가 됐다
    hits = {f.subject: f for f in t.findings}
    assert set(hits) == {("M1a", "M1b"), ("M4a", "M4b")}                    # (a)(b) 를 만족하는 diff_pair 만
    assert all(f.code == CODE and f.severity == "review_needed" for f in t.findings)
    assert ("M37a", "M37b") not in hits                                      # gate 가 입력 포트 아님 -> 기록만


def test_asymmetric_but_single_output_is_record_only(tmp_path):
    """같은 비대칭 합성 회로에서 출력 포트 하나(Vom)를 포트에서 빼 단일 출력으로 -> (a) 불충족 -> review 없음."""
    doc = _pilot_asym()
    doc["topology_name"] = "pilot_asym_se"
    doc["ports"] = {k: v for k, v in doc["ports"].items() if k != "Vom"}
    t = orbit_matching_crosstab(_s1(tmp_path, doc, PILOT))
    assert len({(k, m): o for k, m, o in t.records}[("diff_pair", ("M1a", "M1b"))]) == 2
    assert t.findings == ()


def test_crosstab_does_not_recompute_symmetry(tmp_path, monkeypatch):
    """§2.4.8: 표는 graph/s1 orbits 를 읽는다 -- 정준형을 다시 계산하지 않는다."""
    import sys
    s1 = _s1(tmp_path, _raw(PILOT), PILOT)
    calls = []
    for modname in ("gmid_engine.graph.canonical_form", "gmid_engine.graph.s1_symmetry", "gmid_engine.graph.orbit_matching_crosstab"):
        mod = sys.modules[modname]
        orig = getattr(mod, "canonical_form", None)
        if orig is not None:
            monkeypatch.setattr(mod, "canonical_form", lambda *a, _o=orig, **k: calls.append(1) or _o(*a, **k))
    orbit_matching_crosstab(s1)
    assert calls == []
