"""`SizingSpecDoc` 와 선언 레코드 -- SPEC_CONTRACT 3절(frozen·require_immutable·fp_of, 섹션 지문 SECTION_GROUPS, spec_fp 결정론,
지문 불변식: SpecSource 는 kind 만, `_` 주석 밖, 참조는 해석된 값, 제약 순서 무관, spice_check 만 바꾸면 그 지문만)."""
from __future__ import annotations

import copy
import dataclasses
import random

import pytest

from gmid_engine.authoring import (
    SECTION_GROUPS,
    ConstraintDecl,
    ElementValue,
    InputDc,
    PendingMark,
    SizingSpecDoc,
    SpecSource,
)
from gmid_engine.core import fp_of, require_immutable

SECTIONS = {
    "supplies_fp": ("supplies_v",),
    "operating_fp": ("input_dc", "node_voltage_targets_v", "intended_region"),
    "elements_fp": ("element_values",),
    "feedback_fp": ("feedback",),
    "constraints_fp": ("constraints", "pending_constraints"),
    "compensation_fp": ("compensation_targets",),
    "objective_fp": ("objective",),
    "search_fp": ("search",),
    "spice_check_fp": ("spice_check",),
    "refilter_fp": ("front_refilter",),
    # [U5 2026-10-08] 선택 섹션 3개(설계 40 §3.1)의 지문 묶음 -- 이름은 SPEC_CONTRACT 3절, 기존 묶음 뒤에 붙는다.
    "gain_override_fp": ("gain_budget_db_override",),
    "driving_fp": ("driving_spec",),
    "count_budget_fp": ("structure_count_budget",),
}


def test_section_groups_constant():
    assert {name: tuple(fields) for name, fields in SECTION_GROUPS} == SECTIONS
    assert [name for name, _ in SECTION_GROUPS] == list(SECTIONS)


def test_doc_immutable_and_fingerprintable(sc):
    doc = sc.load()
    require_immutable(doc)
    assert fp_of(doc) == fp_of(sc.load())
    with pytest.raises(dataclasses.FrozenInstanceError):
        doc.spec_fp = "0" * 64
    for c in doc.constraints:
        require_immutable(c)


def test_section_fps_and_spec_fp(sc):
    doc = sc.load()
    names = [n for n, _ in doc.section_fps]
    assert names == list(SECTIONS)
    for _, fp in doc.section_fps:
        assert isinstance(fp, str) and len(fp) == 64
    assert doc.spec_fp == fp_of(doc.section_fps)


def _fps(doc):
    return dict(doc.section_fps)


def _changed(a, b):
    fa, fb = _fps(a), _fps(b)
    return {k for k in fa if fa[k] != fb[k]}


def test_spec_fp_deterministic_across_loads(sc):
    assert sc.load().spec_fp == sc.load().spec_fp


def test_comment_keys_out_of_fp(sc):
    base = sc.load()
    sc.spec["_comment"] = "changed"
    sc.spec["_new"] = {"pending": "SP-1"}
    sc.human["_x"] = 1
    sc.human["constraints"][0]["_c"] = "changed"
    sc.human["element_values"]["Rfb"]["_why"] = "note"
    other = sc.load()
    assert other.spec_fp == base.spec_fp and _changed(base, other) == set()
    assert other.file_sha256 != base.file_sha256


def test_source_text_out_of_fp(sc):
    """SpecSource 는 kind 만 지문: record·citation·decided·origin 문구를 바꿔도 같다."""
    base = sc.load()
    for c in sc.human["constraints"]:
        s = c["source"]
        if s["kind"] in ("user_spec", "pending_spice"):
            s["record"] = "rewritten record"
        if s["kind"] == "user_spec":
            s["decided"] = "2025-01-01"
            s["origin"] = "lecture"
            s["citation"] = "some lecture"
    cl = sc.human["element_values"]["Cld"]["source"]
    cl["citation"] = "another page"
    cl["origin"] = "drawing"
    assert sc.load().spec_fp == base.spec_fp


def test_source_kind_in_fp(sc):
    base = sc.load()
    sc.constraint("gain_ss_db")["source"] = {"kind": "pending_spice", "record": "r"}
    other = sc.load()
    assert other.spec_fp != base.spec_fp
    assert _changed(base, other) == {"constraints_fp"}


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_constraint_order_and_key_order_out_of_fp(sc, seed):
    base = sc.load()
    rnd = random.Random(seed)
    rnd.shuffle(sc.human["constraints"])
    items = list(sc.human.items())
    rnd.shuffle(items)
    sc.spec["human"] = dict(items)
    ev = list(sc.spec["human"]["element_values"].items())
    rnd.shuffle(ev)
    sc.spec["human"]["element_values"] = dict(ev)
    assert sc.load().spec_fp == base.spec_fp


def test_constraints_tuple_keeps_document_order(sc):
    sc.human["constraints"].reverse()
    doc = sc.load()
    want = [c["metric"] if isinstance(c["metric"], str) else None for c in sc.human["constraints"]]
    assert [c.metric for c in doc.constraints] == want


@pytest.mark.parametrize("section,mutate", [
    ("supplies_fp", lambda h: h["supplies_v"]["values"].update(rail_hi=1.3)),
    ("operating_fp", lambda h: h["input_dc"].update(value_v=0.5)),
    ("operating_fp", lambda h: h["node_voltage_targets_v"]["n_mid"].update(value_v=0.8)),
    ("elements_fp", lambda h: h["element_values"]["Rfb"].update(value_ohm=20000.0)),
    ("constraints_fp", lambda h: h["pending_constraints"].append({"metric": "rout_ss_ohm", "decision": "SP-7"})),
    ("compensation_fp", lambda h: h["compensation_targets"]["gbw_target_hz"].update(value=2e7)),
    ("objective_fp", lambda h: h["objective"]["budgets"]["supply_current_dc"].update(value=0.002)),
    ("search_fp", lambda h: h["search"]["search_method"].update(value="precision")),
    ("spice_check_fp", lambda h: h["spice_check"]["saturation_rule"].update(rule="vds_ge_vdsat_plus_tol_v")),
    ("refilter_fp", lambda h: h["front_refilter"]["cycle_cap_rule"].update(source={"kind": "user_spec", "record": "x",
                                                                                   "decided": "2026-10-07"})),
])
def test_one_section_change_moves_only_its_fp(sc, section, mutate):
    base = sc.load()
    mutate(sc.human)
    other = sc.load()
    assert _changed(base, other) == {section}
    assert other.spec_fp != base.spec_fp


def test_feedback_change_moves_feedback_and_loop_constraint_fp(sc):
    """feedback 변경은 feedback_fp 와, 그 feedback 에서 유도한 루프 뷰를 담은 constraints_fp 를 함께 옮긴다
    (SPEC_CONTRACT 3절 -- 유도된 내용이 ViewDecl 에 들어가 constraints_fp 가 feedback 을 따라간다, 7a design 4.2)."""
    base = sc.load()
    sc.human["feedback"].update(elements=[])
    other = sc.load()
    assert _changed(base, other) == {"feedback_fp", "constraints_fp"}
    assert other.spec_fp != base.spec_fp


def test_reference_enters_fp_as_resolved_value(sc):
    """참조는 해석된 값으로 지문: 대상 값을 바꾸면 참조 제약 지문도 바뀌고, 같은 값을 직접 적으면 kind 차만 남는다."""
    base = sc.load()
    sc.constraint("swing_out_v")["value"] = 3.0
    assert sc.load().spec_fp != base.spec_fp
    ref = sc.read_spec("fx_spec_ref")
    ref["human"]["constraints"][0]["value"] = 3e8
    sc.write_spec(ref, "fx_spec_ref")
    other = sc.load()
    assert "constraints_fp" in _changed(base, other)


def test_judged_constraints_property(sc):
    doc = sc.load()
    assert tuple(doc.judged_constraints) == tuple(c for c in doc.constraints if c.judged)
    assert all(isinstance(c, ConstraintDecl) for c in doc.judged_constraints)


def test_record_types(sc):
    doc = sc.load()
    assert isinstance(doc.input_dc, InputDc)
    assert all(isinstance(e, ElementValue) for e in doc.element_values)
    assert all(isinstance(p, PendingMark) for p in doc.pending)
    assert all(isinstance(c.source, SpecSource) for c in doc.constraints)


def test_mutable_into_doc_is_type_error(sc):
    doc = sc.load()
    with pytest.raises(TypeError):
        dataclasses.replace(doc, constraints=list(doc.constraints))
    with pytest.raises(TypeError):
        dataclasses.replace(doc, pending=list(doc.pending))


def test_file_sha256_out_of_spec_fp(sc):
    base = sc.load()
    sc.spec["_comment"] = "x" * 10
    other = sc.load()
    assert other.file_sha256 != base.file_sha256 and other.spec_fp == base.spec_fp


def test_doc_equal_after_copy_roundtrip(sc):
    a = sc.load()
    sc.spec = copy.deepcopy(sc.spec)
    assert sc.load() == a


# ---------------------------------------------------------------- [U5 2026-10-08] 선택 섹션 3개의 지문 격리
# oracle (d) SPEC_CONTRACT 3절 '섹션 지문' 문장(한 섹션만 바꾸면 그 지문과 spec_fp 만 바뀐다, SpecSource 는 kind 만) + (a) 합성 입력.
U5_US = {"kind": "user_spec", "record": "fixture u5", "decided": "2026-10-08"}


def _with_u5_sections(h):
    h["gain_budget_db_override"] = [{"block": ["n_outp"], "value_db": 30.0, "source": dict(U5_US)}]
    h["driving_spec"] = {"slew_rate_v_per_s": 1e6, "source": dict(U5_US)}
    h["structure_count_budget"] = {"value": 64, "source": dict(U5_US)}


@pytest.mark.parametrize("section,key", [("gain_override_fp", "gain_budget_db_override"), ("driving_fp", "driving_spec"),
                                         ("count_budget_fp", "structure_count_budget")])
def test_u5_section_added_moves_only_its_fp(sc, section, key):
    base = sc.load()
    _with_u5_sections(sc.human)
    for other in ("gain_budget_db_override", "driving_spec", "structure_count_budget"):
        if other != key:
            del sc.human[other]
    doc = sc.load()
    assert _changed(base, doc) == {section}
    assert doc.spec_fp != base.spec_fp


@pytest.mark.parametrize("section,mutate", [
    ("gain_override_fp", lambda h: h["gain_budget_db_override"][0].update(value_db=31.0)),
    ("gain_override_fp", lambda h: h["gain_budget_db_override"][0].update(block=["n_mid", "n_outp"])),
    ("driving_fp", lambda h: h["driving_spec"].update(slew_rate_v_per_s=2e6)),
    ("driving_fp", lambda h: h["driving_spec"].update(load_dc_amp=1e-4)),
    ("count_budget_fp", lambda h: h["structure_count_budget"].update(value=65)),
])
def test_u5_section_change_moves_only_its_fp(sc, section, mutate):
    _with_u5_sections(sc.human)
    base = sc.load()
    mutate(sc.human)
    other = sc.load()
    assert _changed(base, other) == {section}
    assert other.spec_fp != base.spec_fp


def test_u5_source_text_out_of_fp(sc):
    _with_u5_sections(sc.human)
    base = sc.load()
    for k in ("driving_spec", "structure_count_budget"):
        sc.human[k]["source"] = dict(U5_US, record="rewritten", decided="2025-01-01")
    sc.human["gain_budget_db_override"][0]["source"] = dict(U5_US, record="rewritten")
    sc.human["driving_spec"]["_why"] = "comment"
    assert sc.load().spec_fp == base.spec_fp


def test_u5_override_item_order_out_of_fp(sc):
    """결과가 블록 키순 tuple 이므로(3절) JSON 항목 순서만 바꾼 spec 은 같은 지문."""
    sc.human["gain_budget_db_override"] = [
        {"block": ["n_outp"], "value_db": 30.0, "source": dict(U5_US)},
        {"block": ["n_mid"], "value_db": 10.0, "source": dict(U5_US)}]
    base = sc.load()
    sc.human["gain_budget_db_override"].reverse()
    assert sc.load().spec_fp == base.spec_fp
