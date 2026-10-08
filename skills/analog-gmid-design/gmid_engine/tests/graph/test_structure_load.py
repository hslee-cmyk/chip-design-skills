"""graph/structure_load.py -- `load_structure_facts(path, topology_fp, rule_fp)`(계약 10.1, pipeline CONTRACT 1절 ratified 사실).

계약: 파일 없음 = 사실 0, 형식 위반 = `SchemaRejectedError` gate `structure_json`, 해시 불일치 = 사실 미적용 + `structure_fact_stale`
review_needed. 파일 형식(최상위 schema_version·topology_hash·rule_hash·facts, 사실 concept·subject·value·status·evidence·approval_id)은
pipeline CONTRACT 1절과 기존 통합 test(tests/integration/test_stage_a_library.py `_structure_file`)의 예를 따른다 -- graph 계약에
스키마 표가 없다(보고서의 계약 결함 항목).
oracle (a): 해시는 입력으로 정해진다(맞는 지문 = S1 topology 지문·`s1v_rule_fp()`, 틀린 지문 = "0"*64).
"""
from __future__ import annotations

import json

import pytest

from gmid_engine.core import SchemaRejectedError, exit_code_for
from gmid_engine.graph import StructureFact, StructureFacts, load_structure_facts, s1v_rule_fp

import s1v_hand as H

TOPO_FP = "a" * 64


def _fact(**over):
    f = {"concept": "stage_members", "subject": "stage_a", "value": "M1 M2", "status": "ratified",
         "evidence": {"rule": "j_ratified", "nets": ["x", "y"]}, "approval_id": "H1-test"}
    f.update(over)
    return f


def _write(path, facts, topology_hash=TOPO_FP, rule_hash=None):
    path.write_text(json.dumps({"schema_version": "1", "topology_hash": topology_hash,
                                "rule_hash": s1v_rule_fp() if rule_hash is None else rule_hash, "facts": facts}),
                    encoding="utf-8")
    return str(path)


def test_missing_file_means_no_facts(tmp_path):
    got = load_structure_facts(str(tmp_path / "absent.structure.json"), TOPO_FP, s1v_rule_fp())
    assert got == StructureFacts(facts=(), findings=())


def test_valid_file_gives_facts(tmp_path):
    p = _write(tmp_path / "ok.json", [_fact(), _fact(concept="drive_kind", subject="x", value="voltage", approval_id="H2",
                                                     evidence={"rule": "j", "nets": ["x"]})])
    got = load_structure_facts(p, TOPO_FP, s1v_rule_fp())
    assert got.findings == ()
    assert set(got.facts) == {StructureFact("stage_members", "stage_a", "M1 M2", "H1-test", ("x", "y")),
                              StructureFact("drive_kind", "x", "voltage", "H2", ("x",))}


@pytest.mark.parametrize("which", ["topology", "rule"])
def test_hash_mismatch_drops_facts_and_records_stale(tmp_path, which):
    kw = {"topology_hash": "0" * 64} if which == "topology" else {"rule_hash": "0" * 64}
    p = _write(tmp_path / "stale.json", [_fact()], **kw)
    got = load_structure_facts(p, TOPO_FP, s1v_rule_fp())
    assert got.facts == ()
    assert [(f.code, f.severity) for f in got.findings] == [("structure_fact_stale", "review_needed")]


@pytest.mark.parametrize("payload", [
    [],                                                                   # 객체가 아님
    {"schema_version": "1"},                                              # 키 부족
    {"schema_version": "1", "topology_hash": TOPO_FP, "rule_hash": "r", "facts": [{"subject": "x"}]},   # 사실 키 부족
    {"schema_version": "1", "topology_hash": TOPO_FP, "rule_hash": "r", "facts": [_fact(status="proposed")]},  # ratified 아님
    {"schema_version": "1", "topology_hash": TOPO_FP, "rule_hash": "r", "facts": [], "extra": 1},       # 모르는 최상위 키
], ids=["list", "missing_keys", "fact_keys", "not_ratified", "unknown_key"])
def test_malformed_file_is_schema_rejected(tmp_path, payload):
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(SchemaRejectedError) as ei:
        load_structure_facts(str(p), TOPO_FP, s1v_rule_fp())
    assert dict(ei.value.record.detail)["gate"] == "structure_json"
    assert exit_code_for(ei.value) == 7


def test_stale_fact_is_not_applied_by_build(tmp_path):
    s1, _ = H.build(tmp_path, H.CS)
    p = _write(tmp_path / "cs.json", [_fact(concept="drive_kind", subject="out", value="voltage",
                                            evidence={"rule": "j", "nets": ["out"]})], topology_hash="0" * 64)
    facts = load_structure_facts(p, s1.key.topology_fp, s1v_rule_fp())
    _, s1v = H.build(tmp_path, H.CS, structure=facts)
    assert s1v.facts_applied == ()
    assert {i.net: i.kind for i in H.view(s1v).drive_kind}["out"] == "current"      # 고정되지 않았다
    assert "structure_fact_stale" in [f.code for f in s1v.findings]


def test_non_json_file_is_schema_rejected(tmp_path):
    # 계약 10.1: 형식 위반 = SchemaRejectedError gate structure_json -- JSON 이 아닌 파일도 형식 위반이다
    p = tmp_path / "broken.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(SchemaRejectedError) as ei:
        load_structure_facts(str(p), TOPO_FP, s1v_rule_fp())
    assert dict(ei.value.record.detail)["gate"] == "structure_json"
