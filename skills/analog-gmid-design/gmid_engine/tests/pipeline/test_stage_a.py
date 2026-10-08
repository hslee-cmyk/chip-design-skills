"""pipeline/stage_a.py -- `run_stage_a(topology_path, spec_path, lut, *, output_dir, supplies_v=None, structure_path=None)`
(pipeline CONTRACT 1·3·4절, 설계 41 0절 단계 A1~A3).

oracle (a): 손 회로의 구조 유도 결과(graph test 의 손 유도)로 단계 A 판정이 정해진다 --
CS(정지 없음) -> ok/0, FF(복합 블록 review_needed 만) -> review_needed/2, XCOUP(교차결합 loop_record_only) -> stopped/2,
topology 거부(passive_elements 키 없음) -> exit 7, s1v None, count_budget 0, tables None.
oracle (b): N_S 는 test_stage_a_budget 의 직접 집계와 같은 정의 -- 여기서는 회로가 쓰는 kind 로만 센다(nmos 만 쓰는 FOLLOWER <
nmos·pmos 를 쓰는 CS).
oracle (d): structure.json `stage_members` 사실(값 = 공백으로 이은 소자 이름)로 declared 대조 -- MILLER 유도 stage 와 맞는 선언은
performed·ok, 섞인 선언은 declared_stage_mismatch(review_needed), 해시 불일치는 structure_fact_stale + not_performed.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gmid_engine.graph import s1v_rule_fp
from gmid_engine.pipeline import StageAResult, run_stage_a, structure_count_budget

import s1v_hand as H


def _write(tmp_path, doc):
    p = tmp_path / (doc["topology_name"] + ".topology.json")
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _run(tmp_path, real_lut, doc, out="out", **kw):
    return run_stage_a(_write(tmp_path, doc), None, real_lut, output_dir=tmp_path / out, supplies_v=H.SUPPLIES, **kw)


def test_clean_circuit_is_ok_exit_0(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.CS)
    assert isinstance(r, StageAResult)
    assert (r.exit_code, r.status) == (0, "ok")
    assert r.report["stop_reasons"] == [] and r.report["review_needed"] == []
    assert r.s1v is not None and [v.id for v in r.s1v.views] == ["transfer:0"]


def test_review_needed_only_is_exit_2(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.FF)
    assert (r.exit_code, r.status) == (2, "review_needed")
    assert r.report["stop_reasons"] == []
    assert any("composite_block_pending_ratify" in x for x in r.report["review_needed"])


def test_record_only_branch_stops_exit_2(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.XCOUP)
    assert (r.exit_code, r.status) == (2, "stopped")
    assert any("loop_record_only" in x for x in r.report["stop_reasons"])
    assert r.s1v is not None                                   # 진단 모드로 기록을 받아 단계 A 가 판정한다


def test_topology_rejection_is_exit_7(tmp_path, real_lut):
    bad = {k: v for k, v in H.CS.items() if k != "passive_elements"}
    bad["topology_name"] = "cs_bad"
    r = _run(tmp_path, real_lut, bad)
    assert r.exit_code == 7
    assert r.s1v is None
    assert r.report["count_budget"] == 0 and r.report["tables"] is None
    assert len(r.report["stop_reasons"]) == 1 and r.report["stop_reasons"][0].startswith("A1_load: ")
    assert all((tmp_path / "out" / name).is_file() for name in ("cs_bad.stage_a.json", "cs_bad.stage_a.md"))


def test_count_budget_uses_only_kinds_of_the_circuit(tmp_path, real_lut):
    both = _run(tmp_path, real_lut, H.CS, out="a")                 # nmos + pmos
    nmos_only = _run(tmp_path, real_lut, H.FOLLOWER, out="b")      # nmos 만
    assert both.report["count_budget"] == structure_count_budget(real_lut, ("nmos", "pmos"))
    assert nmos_only.report["count_budget"] == structure_count_budget(real_lut, ("nmos",))
    assert nmos_only.report["count_budget"] < both.report["count_budget"]


def test_same_input_same_tables_and_budget(tmp_path, real_lut):
    a = _run(tmp_path, real_lut, H.CMFB, out="a")
    b = _run(tmp_path, real_lut, H.CMFB, out="b")
    assert a.report["tables"] == b.report["tables"]
    assert a.report["count_budget"] == b.report["count_budget"]


def _structure(path, s1_fp, facts, topology_hash=None):
    path.write_text(json.dumps({
        "schema_version": "1", "topology_hash": s1_fp if topology_hash is None else topology_hash,
        "rule_hash": s1v_rule_fp(),
        "facts": [{"concept": "stage_members", "subject": name, "value": value, "status": "ratified",
                   "evidence": {"rule": "hand", "nets": []}, "approval_id": "T-%d" % i}
                  for i, (name, value) in enumerate(facts)]}), encoding="utf-8")


def test_declared_comparison_states(tmp_path, real_lut):
    absent = _run(tmp_path, real_lut, H.MILLER, out="o0")
    assert absent.report["declared_comparison"] == "not_performed: miller.structure.json absent"
    s1_fp = absent.s1v.key[0].topology_fp
    side = tmp_path / "miller.structure.json"                       # 기본 경로 = topology 옆 <회로>.structure.json
    _structure(side, s1_fp, [("stage_one", "M1 M2"), ("stage_two", "M6")])
    good = _run(tmp_path, real_lut, H.MILLER, out="o1")
    assert good.report["declared_comparison"] == "performed"
    assert (good.exit_code, good.status) == (0, "ok")

    other = tmp_path / "other.json"
    _structure(other, s1_fp, [("stage_one", "M1 M6"), ("stage_two", "M2")])
    bad = _run(tmp_path, real_lut, H.MILLER, out="o2", structure_path=other)
    assert (bad.exit_code, bad.status) == (2, "review_needed")
    assert any("declared_stage_mismatch" in x for x in bad.report["review_needed"])

    _structure(other, s1_fp, [("stage_one", "M1 M2")], topology_hash="0" * 64)
    stale = _run(tmp_path, real_lut, H.MILLER, out="o3", structure_path=other)
    assert stale.status == "review_needed"
    assert any("structure_fact_stale" in x for x in stale.report["review_needed"])
    assert stale.report["declared_comparison"].startswith("not_performed")

    other.write_text(json.dumps({"schema_version": "1", "topology_hash": s1_fp, "rule_hash": s1v_rule_fp(),
                                 "facts": [{"concept": "drive_kind", "subject": "out", "value": "current",
                                            "status": "ratified", "evidence": {"rule": "h", "nets": ["out"]},
                                            "approval_id": "T-9"}]}), encoding="utf-8")
    no_stage = _run(tmp_path, real_lut, H.MILLER, out="o4", structure_path=other)
    assert no_stage.report["declared_comparison"] == "not_performed: other.json has no stage_members facts"


def test_malformed_structure_file_is_rejected(tmp_path, real_lut):
    side = tmp_path / "cs.structure.json"
    side.write_text(json.dumps({"schema_version": "1"}), encoding="utf-8")
    r = _run(tmp_path, real_lut, H.CS)
    # 계약 1절: structure 거부 -> 7 또는 2(정지 전 단계라 s1v None), 보고서는 항상 쓰인다(4절)
    assert r.exit_code in (2, 7) and r.status == "stopped"
    assert r.s1v is None
    assert all(Path(p).is_file() for p in r.report_paths)


@pytest.mark.parametrize("circuit", ["two_stage_ota", "two_stage_ota_sf", "folded_cascode", "common_gate_amplifier",
                                     "pushpull_follower_buffer"])
def test_library_circuits_without_stop(tmp_path, real_lut, circuit):
    # oracle (a)·(d): 아래 회로의 구조 유도 손 요약은 tests/integration/test_sp1_library_summary.py -- 정지 분기·review_needed 없음
    r = run_stage_a(H.LIBRARY / (circuit + ".topology.json"), None, real_lut, output_dir=tmp_path,
                    supplies_v=H.lib_supplies(circuit))
    assert (r.exit_code, r.status) == (0, "ok"), r.report["stop_reasons"] + r.report["review_needed"]


RECORD_ONLY = {"cell_ambiguous", "pass_group_unsupported", "gate_on_current_node", "cs_output_low_impedance",
               "buffer_multi_output", "composite_dag_not_chain", "composite_over_budget", "loop_record_only",
               "cycle_enumeration_over_budget", "undeclared_loop_constraint"}     # 계약 10.3 불변량 8


@pytest.mark.parametrize("circuit,expected", [
    ("ngcc_3stage_ff", {"undeclared_loop_constraint"}),           # 루프 뷰 + 차동 출력 포트쌍 없음(출력 Vout 하나)
    ("nmcnr_amplifier", {"undeclared_loop_constraint"}),          # 같은 이유
    ("sf_pushpull_output_opamp", {"loop_record_only"}),           # 계획 N3.2-2: 복합 diode 3건이 (나)로 `기록만`
    ("current_reuse_telescopic_ota", set()),                      # 정지 코드 손 유도 불가(파일럿 -- J ratify 대상), 정지만 확인
])
def test_library_stopping_circuits(tmp_path, real_lut, circuit, expected):
    r = run_stage_a(H.LIBRARY / (circuit + ".topology.json"), None, real_lut, output_dir=tmp_path,
                    supplies_v=H.lib_supplies(circuit))
    assert (r.exit_code, r.status) == (2, "stopped")
    codes = {s.split("|")[1] for s in r.report["stop_reasons"]}
    assert codes <= RECORD_ONLY
    assert expected <= codes


def test_non_json_structure_file_still_writes_report(tmp_path, real_lut):
    # 계약 1절 'structure 거부 -> 7 또는 2', 4절 '보고서 파일은 항상 쓰인다'
    (tmp_path / "cs.structure.json").write_text("{not json", encoding="utf-8")
    r = _run(tmp_path, real_lut, H.CS)
    assert r.exit_code in (2, 7) and r.status == "stopped"
    assert all(Path(p).is_file() for p in r.report_paths)
