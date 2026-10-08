"""pipeline/stage_a_report.py -- 단계 A 보고서 `<output_dir>/<회로>.stage_a.json`·`.stage_a.md`(pipeline CONTRACT 2절·4절).

oracle (d) 계약 문장 그대로: JSON 키 = circuit·status·exit_code·count_budget·declared_comparison·stop_reasons·review_needed·views·tables
(키 정렬로 기록), stop_reasons·review_needed 항목 = `severity|code|view|대상,...|근거`, views 항목 = id·kind·blocks[kind,key,stage]·
loop_count·cuts, tables = `graph.structure_tables(s1v)`, 기존 파일은 덮어쓰고 보고서는 항상 쓰인다.
oracle (a): 손 회로 XCOUP 의 정지 사유는 graph test 손 유도(교차결합 -> loop_record_only, 뷰 transfer:0, 대상 om·op).
"""
from __future__ import annotations

import json
from pathlib import Path

from gmid_engine.core import fp_of
from gmid_engine.graph import structure_tables
from gmid_engine.pipeline import run_stage_a

import s1v_hand as H

KEYS = ["circuit", "count_budget", "declared_comparison", "exit_code", "review_needed", "status", "stop_reasons", "tables",
        "views"]


def _run(tmp_path, real_lut, doc, out="out"):
    p = tmp_path / (doc["topology_name"] + ".topology.json")
    p.write_text(json.dumps(doc), encoding="utf-8")
    return run_stage_a(p, None, real_lut, output_dir=tmp_path / out, supplies_v=H.SUPPLIES)


def _pairs_hook(seen):
    def hook(pairs):
        seen.append([k for k, _ in pairs])
        return dict(pairs)
    return hook


def test_files_and_sorted_keys(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.CS)
    json_path, md_path = map(Path, r.report_paths)
    assert (json_path.name, md_path.name) == ("cs.stage_a.json", "cs.stage_a.md")
    assert json_path.parent == md_path.parent == tmp_path / "out"
    seen = []
    data = json.loads(json_path.read_text(encoding="utf-8"), object_pairs_hook=_pairs_hook(seen))
    assert seen[-1] == KEYS                                    # 최상위 키는 정렬되어 기록
    assert all(keys == sorted(keys) for keys in seen)          # 하위 객체도 키 정렬
    assert data == json.loads(json.dumps(r.report))            # 결과의 report 와 같은 내용
    assert data["circuit"] == "cs" and data["exit_code"] == 0 and data["status"] == "ok"


def test_stop_reason_format(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.XCOUP)
    loop = [s for s in r.report["stop_reasons"] if s.split("|")[1] == "loop_record_only"]
    assert len(loop) == 1
    severity, code, view, subjects, basis = loop[0].split("|", 4)
    assert (severity, code, view, subjects) == ("unsupported_rule_branch", "loop_record_only", "transfer:0", "om,op")
    assert basis
    for s in r.report["review_needed"]:
        assert s.split("|")[0] == "review_needed" and len(s.split("|")) >= 5


def test_views_summary(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.MILLER)
    # 손 유도(test_blocks·test_loops): 블록 (o1) stage 1·(out) stage 2, Miller 루프 1, 끊는 점 없음
    assert r.report["views"] == [{"id": "transfer:0", "kind": "transfer", "loop_count": 1, "cuts": [],
                                  "blocks": [{"kind": "gain", "key": ["o1"], "stage": 1},
                                             {"kind": "gain", "key": ["out"], "stage": 2}]}]


def test_tables_are_structure_tables(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.CMFB)
    assert fp_of(r.report["tables"]) == fp_of(json.loads(json.dumps(structure_tables(r.s1v))))


def test_markdown_mentions_status_and_reasons(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.XCOUP)
    md = Path(r.report_paths[1]).read_text(encoding="utf-8")
    assert "xcoup" in md and "stopped" in md and "loop_record_only" in md


def test_existing_report_is_overwritten(tmp_path, real_lut):
    first = _run(tmp_path, real_lut, H.CS)
    stale = H.topo("cs", (("M1", "nmos", "a", "in", "gnd"), ("M2", "pmos", "a", "vb", "vdd"), ("M3", "nmos", "out", "a", "gnd"),
                          ("M4", "pmos", "out", "in", "vdd")), {"in": H.SE_IN, "out": H.SE_OUT}, bias=("vb",))
    second = _run(tmp_path, real_lut, stale)                  # 같은 회로 이름, 다른 구조(FF 형) -> review_needed
    assert first.report_paths == second.report_paths
    data = json.loads(Path(second.report_paths[0]).read_text(encoding="utf-8"))
    assert data["status"] == "review_needed" and data["exit_code"] == 2
