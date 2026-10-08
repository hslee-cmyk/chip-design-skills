"""pipeline/stage_a_report.py -- 단계 A 보고서 `<output_dir>/<회로>.stage_a.json`·`.stage_a.md`(pipeline CONTRACT 2절·4절).

oracle (d) 계약 문장 그대로: JSON 키 = circuit·status·exit_code·count_budget·declared_comparison·stop_reasons·review_needed·views·tables
(키 정렬로 기록), stop_reasons·review_needed 항목 = `severity|code|view|대상,...|근거`, views 항목 = id·kind·blocks[kind,key,stage]·
loop_count·cuts, tables = `graph.structure_tables(s1v)`, 기존 파일은 덮어쓰고 보고서는 항상 쓰인다.
oracle (a): 손 회로 XCOUP 의 정지 사유는 graph test 손 유도(교차결합 -> loop_record_only, 뷰 transfer:0, 대상 om·op).
[U10] oracle (a): 보고서 `coupling` 내용은 graph `test_coupling_vars.test_miller_k1_k2_across_stages`·`test_column_block_map` 의
MILLER 손 유도와 같은 리터럴, 귀속 안 된 소자(`coupling_hand.ORPHAN`)는 A4 정지(DEC-71 (2)) -> status stopped, exit 2.
"""
from __future__ import annotations

import json
from pathlib import Path

from gmid_engine.core import fp_of
from gmid_engine.graph import structure_tables
from gmid_engine.pipeline import run_stage_a

import coupling_hand as CH
import s1v_hand as H

# [U1b] applied_facts·ff_ratio_candidates (pipeline CONTRACT 2절), [U10] coupling (설계 40 §3.3 as-built: 단계 A 보고서 `coupling` 이
# U15 전까지 유일한 출구)
KEYS = ["applied_facts", "circuit", "count_budget", "coupling", "declared_comparison", "exit_code", "ff_ratio_candidates",
        "review_needed", "status", "stop_reasons", "tables", "views"]


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


def test_coupling_section_miller(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, H.MILLER)
    cpl = json.loads(Path(r.report_paths[0]).read_text(encoding="utf-8"))["coupling"]
    assert sorted(cpl) == ["bias_columns", "column_block_map", "column_mate_devices", "kind_counts", "vars"]
    blocks = [["transfer:0", ["o1"]], ["transfer:0", ["out"]]]
    # 손 유도(graph test_coupling_vars): 꼬리 M5(o1)·전류원 M7(out) 미러 -> K1 dc·geom, equal_vgs (vb, gnd) -> K2
    assert cpl["vars"] == [
        {"kind": "K1", "members": ["M5", "M7"], "blocks": blocks, "domain": "dc", "init_rule": "class_owner_value", "nets": []},
        {"kind": "K1", "members": ["M5", "M7"], "blocks": blocks, "domain": "geom", "init_rule": "class_owner_value", "nets": []},
        {"kind": "K2", "members": ["M5", "M7"], "blocks": blocks, "domain": "dc", "init_rule": "common_vgs_candidates",
         "nets": ["vb", "gnd"]},
    ]
    assert {k: v for k, v in cpl["kind_counts"].items() if v} == {"K1": 2, "K2": 1}
    assert cpl["bias_columns"] == [] and cpl["column_mate_devices"] == []
    # 매핑표: 커패시터 Cc 는 기둥 밖 두 블록 멤버(column null), 꼬리 M5 는 두 기둥 -> shared
    rows = {(row["column"] is None, tuple(row["block"][1]), row["device"]): (row["shared"], row["basis"]) for row in cpl["column_block_map"]}
    assert rows[(True, ("o1",), "Cc")] == rows[(True, ("out",), "Cc")] == (True, "block_member")
    assert {k[2] for k in rows} == {"Cc", "M1", "M2", "M3", "M4", "M5", "M6", "M7"}
    m5 = [(row["column"], row["shared"], row["basis"]) for row in cpl["column_block_map"] if row["device"] == "M5"]
    assert len({c for c, _s, _b in m5}) == 2 and all(c is not None for c, _s, _b in m5)
    assert {(s_, b_) for _c, s_, b_ in m5} == {(True, "block_member")}
    assert r.status == "ok" and r.exit_code == 0


def test_coupling_section_column_mate(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, CH.MATE)
    # 손 유도(graph test_column_block_map): 캐스코드 부하 위 전류원 M3 는 블록 밖, 같은 기둥 블록 out 에 귀속
    assert r.report["coupling"]["column_mate_devices"] == ["M3"]
    assert r.report["coupling"]["vars"] == []


def test_column_unassigned_stops_stage_a(tmp_path, real_lut):
    r = _run(tmp_path, real_lut, CH.ORPHAN)
    # DEC-71 (2): 가지에 들었으나 블록·기둥 어디에도 없는 Mx -> StructureUnresolvedError(column_unassigned) -> A4 정지
    assert (r.status, r.exit_code) == ("stopped", 2)
    a4 = [s for s in r.report["stop_reasons"] if s.startswith("A4_coupling:")]
    assert len(a4) == 1 and "column_unassigned" in a4[0] and "Mx" in a4[0]
    assert r.report["coupling"] is None
    assert Path(r.report_paths[0]).exists()                    # 정지해도 보고서는 쓴다(pipeline CONTRACT 4)
