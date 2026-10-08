"""graph/structure_load.py -- `load_structure_facts(path, topology_fp, rule_fp)`(계약 10.1, pipeline CONTRACT 1절 ratified 사실).

계약: 파일 없음 = 사실 0, 형식 위반 = `SchemaRejectedError` gate `structure_json`, 해시 불일치 = 사실 미적용 + `structure_fact_stale`
review_needed. 파일 형식(최상위 schema_version·topology_hash·rule_hash·facts, 사실 concept·subject·value·status·evidence·approval_id)은
pipeline CONTRACT 1절과 기존 통합 test(tests/integration/test_stage_a_library.py `_structure_file`)의 예를 따른다 -- graph 계약에
스키마 표가 없다(보고서의 계약 결함 항목).
oracle (a): 해시는 입력으로 정해진다(맞는 지문 = S1 topology 지문·`s1v_rule_fp()`, 틀린 지문 = "0"*64).
[U1b 2026-10-09] 시그니처 `load_structure_facts(path, topology_fp, rule_fp, net_names=())`(계약 10.1). 어휘·값 범위·schema_version·
'->' 모호 거부와 `structure_rule_fp` stale 키는 파일 끝 test(설계 40 3.2-3). 로더는 넘겨받은 rule_fp 와 비교하므로 위 기존 test 는
그대로 유효하다(단계 A 가 넘기는 값이 structure_rule_fp 로 바뀐 것은 tests/pipeline 에서 본다).
"""
from __future__ import annotations

import json

import pytest

from gmid_engine.core import SchemaRejectedError, exit_code_for
from gmid_engine.graph import StructureFact, StructureFacts, load_structure_facts, s1v_rule_fp, structure_rule_fp

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


# ---------------------------------------------------------------- [U1b] 40 3.2-3 concept 어휘·값 범위·schema_version 거부
# oracle (d) 40 3.2-3: 닫힌 어휘(concept 7개), 밖의 이름은 SchemaRejectedError gate structure_json. graph 계약 10.6 '로더 거부' 의
# hit rule 이름 4개. 거부를 '실제로 하는지' 확인한다(통과만 보면 거부하지 않는 로더도 통과한다).
import jrules_hand as J  # noqa: E402

CONCEPT_VALUES = {                                    # 40 3.2-3 concept 표의 value 어휘(정본)
    "drive_kind": ("voltage", "current"),
    "dc_role": ("signal", "bias_current_source", "diode_reference", "diode_reference_composite",
                "diode_reference_composite_cascode"),
    "loop_role": ("loop_view", "compensation_internal", "composite_diode_internal", "bias_scc"),
    "feedforward_cell": ("ff:a->b", "ff_bias:a->b", "ff_load:a->b"),
    "matching_pair": ("branch_symmetric",),
}
SUBJECT = {"drive_kind": "x", "dc_role": "M1", "loop_role": "loop:M1:x", "feedforward_cell": "M1",
           "matching_pair": '["M1","M2"]'}


def _rejected_rules(tmp_path, facts, schema_version="1", net_names=()):
    p = J.write_structure(tmp_path / "f.json", TOPO_FP, s1v_rule_fp(), facts, schema_version=schema_version)
    with pytest.raises(SchemaRejectedError) as ei:
        load_structure_facts(p, TOPO_FP, s1v_rule_fp(), net_names)
    d = dict(ei.value.record.detail)
    assert d["gate"] == "structure_json"
    assert exit_code_for(ei.value) == 7
    return [h.rule for h in d["hits"]]


def test_every_closed_vocabulary_value_loads(tmp_path):
    rows = [J.fact_dict(c, SUBJECT[c], v, "V-%d" % i) for i, (c, vals) in enumerate(sorted(CONCEPT_VALUES.items())) for v in vals]
    rows += [J.fact_dict("ac_ground_exception", "n", "loop:M1:n", "V-ac"), J.fact_dict("stage_members", "s", "M1 M2", "V-st")]
    p = J.write_structure(tmp_path / "ok.json", TOPO_FP, s1v_rule_fp(), rows)
    got = load_structure_facts(p, TOPO_FP, s1v_rule_fp(), ("a", "b", "n", "x"))
    assert got.findings == ()
    assert len(got.facts) == len(rows)
    assert {f.concept for f in got.facts} == set(CONCEPT_VALUES) | {"ac_ground_exception", "stage_members"}


@pytest.mark.parametrize("version", ["2", "0", "1.0", "01"])
def test_schema_version_other_than_1_is_rejected(tmp_path, version):
    assert _rejected_rules(tmp_path, [J.fact_dict("drive_kind", "x", "voltage")], schema_version=version) == [
        "structure_schema_version"]


@pytest.mark.parametrize("concept", ["l_owner", "frobnicate", "dc_roles", "DriveKind"])
def test_unknown_concept_is_rejected(tmp_path, concept):
    # 40 3.2-3 'L 동치류 주인은 사실로 두지 않는다' -- l_owner 도 어휘 밖
    assert _rejected_rules(tmp_path, [J.fact_dict(concept, "x", "voltage")]) == ["structure_concept_unknown"]


@pytest.mark.parametrize("concept,subject,value", [
    ("drive_kind", "x", "sideways"),
    ("dc_role", "M1", "tail"),
    ("dc_role", "M1", "diode_reference_cascode"),
    ("loop_role", "loop:M1:x", "record_only"),
    ("feedforward_cell", "M1", "a->b"),                  # 종류 접두 없음
    ("feedforward_cell", "M1", "ff_tap:a->b"),            # 어휘 밖 종류
    ("feedforward_cell", "M1", "ff:ab"),                  # '->' 없음
    ("matching_pair", '["M1","M2"]', "mirror"),
    ("matching_pair", "M1", "branch_symmetric"),          # 대상이 JSON 배열이 아님
    ("matching_pair", '["M1"]', "branch_symmetric"),      # 멤버 하나
])
def test_value_or_subject_outside_vocabulary_is_rejected(tmp_path, concept, subject, value):
    assert _rejected_rules(tmp_path, [J.fact_dict(concept, subject, value)]) == ["structure_value_range"]


def test_arrow_in_net_name_is_ambiguous_only_with_feedforward_facts(tmp_path):
    # 40 3.2-3: feedforward_cell value 는 '<탭>-><merge>' 이므로 넷 이름에 '->' 가 든 topology 는 로드에서 거부(structure_value_ambiguous).
    # feedforward_cell 사실이 없으면 모호할 것이 없다(거부하지 않는다)
    nets = ("a->x", "b")
    assert _rejected_rules(tmp_path, [J.fact_dict("feedforward_cell", "M1", "ff:b->b")], net_names=nets) == [
        "structure_value_ambiguous"]
    p = J.write_structure(tmp_path / "plain.json", TOPO_FP, s1v_rule_fp(), [J.fact_dict("drive_kind", "b", "voltage")])
    assert len(load_structure_facts(p, TOPO_FP, s1v_rule_fp(), nets).facts) == 1


def test_structure_rule_fp_is_the_stale_key(tmp_path):
    # 40 3.2-3 rule_hash: structure_rule_fp() = S1V 규칙 파일 + S1 쪽 소비 파일 지문 -> s1v_rule_fp() 와 다르다. 단계 A 가 넘기는
    # 지문(structure_rule_fp)과 다른 rule_hash 로 쓴 사실(옛 s1v_rule_fp 로 쓴 파일 포함)은 stale 이다
    assert structure_rule_fp() != s1v_rule_fp()
    old = J.write_structure(tmp_path / "old.json", TOPO_FP, s1v_rule_fp(), [_fact()])
    got = load_structure_facts(old, TOPO_FP, structure_rule_fp())
    assert got.facts == () and [f.code for f in got.findings] == ["structure_fact_stale"]
    new = J.write_structure(tmp_path / "new.json", TOPO_FP, structure_rule_fp(), [_fact()])
    assert len(load_structure_facts(new, TOPO_FP, structure_rule_fp()).facts) == 1
