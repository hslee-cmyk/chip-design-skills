"""공용 helper `_spec_fields.py`(옛 이름 표·회로 전용 키 표·key_hits·value_slot) -- SPEC_CONTRACT 2절 unknown_key·legacy_name·
circuit_specific_key 행이 '모든 객체'에 같은 규칙으로 걸리는지, 6절 3(library 이름과 같은 옛 이름은 표에서 빼 unknown_key).
helper 는 비공개라 여러 섹션의 공개 진입점(load_sizing_spec)으로 확인한다."""
from __future__ import annotations

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
CIRCUIT_SPECIFIC = ("compensation", "function", "kg", "Z", "NDP", "stage_devices", "minimize", "inherits", "spec_fn")

# (객체 자리, gate) -- 키를 더할 dict 를 꺼낸다
OBJECTS = {
    "human": (lambda s: s["human"], "spec_schema"),
    "supplies_v": (lambda s: s["human"]["supplies_v"], "supplies"),
    "input_dc": (lambda s: s["human"]["input_dc"], "input_dc"),
    "element": (lambda s: s["human"]["element_values"]["Rfb"], "elements"),
    "feedback": (lambda s: s["human"]["feedback"], "elements"),
    "constraint": (lambda s: s["human"]["constraints"][0], "constraints"),
    "compensation_targets": (lambda s: s["human"]["compensation_targets"], "compensation_targets"),
    "objective": (lambda s: s["human"]["objective"], "settings"),
    "search": (lambda s: s["human"]["search"], "settings"),
    "search_field": (lambda s: s["human"]["search"]["front_budget_s"], "settings"),
    "spice_field": (lambda s: s["human"]["spice_check"]["saturation_rule"], "settings"),
}


@pytest.mark.parametrize("where", list(OBJECTS))
def test_unknown_key_everywhere(sc, where):
    get, gate = OBJECTS[where]
    get(sc.spec)["zz_unknown_field"] = 1
    sc.reject_only("unknown_key", gate)


@pytest.mark.parametrize("where", list(OBJECTS))
def test_underscore_keys_ignored_everywhere(sc, where):
    get, gate = OBJECTS[where]
    get(sc.spec)["_note"] = {"anything": [1, 2]}
    sc.load()


@pytest.mark.parametrize("where", ["human", "compensation_targets", "objective", "constraint", "search"])
@pytest.mark.parametrize("key", CIRCUIT_SPECIFIC)
def test_circuit_specific_key(sc, where, key):
    get, gate = OBJECTS[where]
    get(sc.spec)[key] = {"x": 1}
    sc.reject_only("circuit_specific_key", gate)


@pytest.mark.parametrize("name", ["CL", "vdd", "Voc_des"])
def test_library_like_old_names_are_unknown_key(sc, name):
    """6절 3: library 이름과 글자가 같은 옛 이름(CL·vdd·Voc_des)은 옛 이름 표에서 빠져 unknown_key 로 거부."""
    sc.human["compensation_targets"][name] = {"value": 1.0, "source": dict(US)}
    sc.reject_only("unknown_key", "compensation_targets")


def test_legacy_source_kind(sc):
    sc.constraint("mismatch_sigma_mv")["source"]["kind"] = "pending_7a"
    sc.reject_only("legacy_name", "constraints")


def test_unread_value_slots_need_exactly_one(sc):
    """값 자리 규칙(value_slot)이 제약·보상 목표에 같게: 값/참조 정확히 하나."""
    sc.human["constraints"][0]["value_from_file"] = "fx_spec_ref#ugf_ss_hz"
    sc.human["compensation_targets"]["gbw_target_hz"]["value_from_constraint"] = "pm_ss_deg"
    d = sc.reject()
    assert sorted(sc.rules(d)) == ["value_and_ref", "value_and_ref"]
    assert d["rejected_gates"] == ("compensation_targets", "constraints")


def test_pending_marker_with_extra_key_is_not_a_marker(sc):
    """표지 = 주석 밖 키가 pending 하나. 다른 키가 붙으면 표지가 아니다 -> 거부(그 자리 형식/키 위반)."""
    sc.human["input_dc"] = {"pending": "SP-2", "value_v": 0.6}
    d = sc.reject()
    assert d["rejected_gates"] == ("input_dc",)


def test_pending_marker_with_comment_is_marker(sc):
    sc.human["input_dc"] = {"pending": "SP-2", "_why": "waiting"}
    assert sc.load().input_dc.mode == "pending"
