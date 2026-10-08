"""spec 최상위 스키마 (gate `spec_schema`) -- SPEC_CONTRACT 1절(meta·human 키, 표지 ID 형식)·2절 표의 spec_schema 행.
모두 `load_sizing_spec` 로 실제 거부를 확인한다(`check_spec_schema` 의 반환 형식은 계약 표에 없어 진입점으로만 건다)."""
from __future__ import annotations

import pytest

from gmid_engine.authoring import SPEC_SCHEMA_VERSION

HUMAN_REQUIRED = ("supplies_v", "input_dc", "element_values", "feedback", "constraints", "node_voltage_targets_v",
                  "intended_region", "objective", "search", "spice_check", "front_refilter")
HUMAN_OPTIONAL = ("pending_constraints", "compensation_targets")
META_KEYS = ("schema_version", "circuit", "topology_fp", "origin")


def test_schema_version_constant():
    assert SPEC_SCHEMA_VERSION == "5"


@pytest.mark.parametrize("top", [[], "x", 5, None])
def test_top_not_object(sc, top):
    sc.spec = top
    d = sc.reject()
    assert sc.rules(d) == ["top_not_object"]
    assert d["rejected_gates"] == ("spec_schema",)
    assert "all_sections" in d["not_evaluated"]


@pytest.mark.parametrize("key", ["meta", "human"])
def test_missing_top_key(sc, key):
    del sc.spec[key]
    d = sc.reject()
    assert "missing_key" in sc.rules(d)
    assert d["rejected_gates"] == ("spec_schema",)


def test_unknown_top_key(sc):
    sc.spec["extra"] = {}
    sc.reject_only("unknown_key", "spec_schema")


def test_underscore_top_keys_ignored(sc):
    sc.spec["_anything"] = [1, {"pending": "not an id"}]
    sc.human["_comment"] = "x"
    sc.spec["meta"]["_note"] = "y"
    sc.load()


@pytest.mark.parametrize("key", META_KEYS)
def test_missing_meta_key(sc, key):
    del sc.spec["meta"][key]
    d = sc.reject()
    assert "missing_key" in sc.rules(d)
    assert "spec_schema" in d["rejected_gates"]


def test_unknown_meta_key(sc):
    sc.spec["meta"]["version"] = "5"
    sc.reject_only("unknown_key", "spec_schema")


@pytest.mark.parametrize("val", ["4", 5, "5.0", None])
def test_schema_version(sc, val):
    sc.spec["meta"]["schema_version"] = val
    sc.reject_only("schema_version", "spec_schema")


@pytest.mark.parametrize("val", ["paper", "user", "", 1])
def test_meta_origin_vocab(sc, val):
    sc.spec["meta"]["origin"] = val
    sc.reject_only("type", "spec_schema")


@pytest.mark.parametrize("origin", ["canonical", "fixture"])
def test_meta_origin_ok(sc, origin):
    sc.spec["meta"]["origin"] = origin
    assert sc.load().origin == origin


@pytest.mark.parametrize("key", HUMAN_REQUIRED)
def test_missing_required_human_key_single_hit(sc, key):
    """0절: 필수 human 키가 없으면 missing_key 하나만 내고 그 섹션 검사는 하지 않는다."""
    del sc.human[key]
    sc.reject_only("missing_key", "spec_schema")


@pytest.mark.parametrize("key", HUMAN_OPTIONAL)
def test_optional_human_key_may_be_absent(sc, key):
    del sc.human[key]
    if key == "compensation_targets":
        doc = sc.load()
        assert doc.compensation_targets == ()
    else:
        assert sc.load().pending_constraints == ()


def test_unknown_human_key(sc):
    # [U5 2026-10-08] gain_budget_db_override 는 이제 선택 키(설계 40 §3.1)라 어휘 밖 이름으로 바꿨다.
    sc.human["gain_budget_override_db"] = 3
    sc.reject_only("unknown_key", "spec_schema")


@pytest.mark.parametrize("key", ["gain_budget_db_override", "driving_spec", "structure_count_budget"])
def test_u5_optional_human_keys_are_vocabulary(sc, key):
    """[U5] 설계 40 §3.1 표의 새 필드는 human 키 어휘다 -- 형식이 틀리면 unknown_key 가 아니라 형식 위반(type)으로 거부된다."""
    sc.human[key] = 3
    d = sc.reject()
    assert "unknown_key" not in sc.rules(d) and "legacy_name" not in sc.rules(d)
    assert "type" in sc.rules(d)


@pytest.mark.parametrize("key", ["input_dc_net", "topology_hash", "derived"])
def test_canonical_names_are_not_legacy(sc, key):
    """[U5] 설계 40 §3.1 '옛 이름 거부' 행·§11 U5 '옛 이름 표 수정(input_dc_net·topology_hash·derived)': 이 세 이름은 정본 이름이라
    옛 이름 표에서 빠진다 -- human 키로 오면 어휘 밖(unknown_key)이지 legacy_name 이 아니다."""
    sc.human[key] = {"x": 1}
    sc.reject_only("unknown_key", "spec_schema")


@pytest.mark.parametrize("key", ["compensation", "function", "kg", "Z", "NDP", "stage_devices", "minimize",
                                 "inherits", "spec_fn"])
def test_circuit_specific_key_at_human_level(sc, key):
    sc.human[key] = {"x": 1}
    sc.reject_only("circuit_specific_key", "spec_schema")


@pytest.mark.parametrize("pid", ["SP1", "sp-1", "XX-1", "MOD", "MODx", "", "PA-", "SP-1a"])
def test_pending_id_format(sc, pid):
    sc.human["input_dc"] = {"pending": pid}
    d = sc.reject()
    assert sc.rules(d) == ["pending_id_format"]
    assert d["rejected_gates"] == ("spec_schema",)


def test_pending_id_format_each_marker(sc):
    sc.human["input_dc"] = {"pending": "bad-1"}
    sc.human["intended_region"] = {"pending": "worse"}
    sc.human["search"]["front_budget_s"] = {"pending": 7}
    d = sc.reject()
    assert sc.rules(d).count("pending_id_format") == 3


@pytest.mark.parametrize("val", ["", 3, None])
def test_meta_circuit_type(sc, val):
    sc.spec["meta"]["circuit"] = val
    d = sc.reject()
    assert "type" in sc.rules(d)
    assert "spec_schema" in d["rejected_gates"]


@pytest.mark.parametrize("val", ["", 3, None])
def test_meta_topology_fp_type(sc, val):
    sc.spec["meta"]["topology_fp"] = val
    d = sc.reject()
    assert "type" in sc.rules(d)
    assert "spec_schema" in d["rejected_gates"]
