"""보상 목표 `human.compensation_targets` (gate `compensation_targets`) -- SPEC_CONTRACT 2절 settling_order·value_and_ref·
ref_kind_mismatch 행, 1절(reference 허용 섹션), 회로 전용 키 거부(circuit_specific_key)."""
from __future__ import annotations

import pytest

US = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}


def test_result_name_order_and_values(sc):
    doc = sc.load()
    raw = sc.human["compensation_targets"]
    assert [k for k, _ in doc.compensation_targets] == sorted(raw)
    got = dict(doc.compensation_targets)
    assert got["gbw_target_hz"].value == raw["gbw_target_hz"]["value"]
    # pm_target_deg -> value_from_constraint pm_ss_deg (JSON 의 그 제약 값)
    pm = [c for c in sc.human["constraints"] if c.get("metric") == "pm_ss_deg"][0]["value"]
    assert got["pm_target_deg"].value == pm
    assert (got["settling"].total_s, got["settling"].linear_s) == (raw["settling"]["total_s"], raw["settling"]["linear_s"])


def test_pending_target_and_settling(sc):
    sc.human["compensation_targets"] = {"gbw_target_hz": {"pending": "SP-5"}, "settling": {"pending": "ET-2"}}
    doc = sc.load()
    got = dict(doc.compensation_targets)
    assert got["gbw_target_hz"].decision == "SP-5" and got["gbw_target_hz"].value is None
    assert got["settling"].decision == "ET-2"


def test_empty_ok(sc):
    sc.human["compensation_targets"] = {}
    assert sc.load().compensation_targets == ()


def test_settling_order(sc):
    sc.human["compensation_targets"]["settling"]["linear_s"] = 5e-08
    sc.reject_only("settling_order", "compensation_targets")


def test_settling_equal_ok(sc):
    sc.human["compensation_targets"]["settling"]["linear_s"] = 4e-08
    sc.load()


@pytest.mark.parametrize("field,val", [("total_s", 0.0), ("total_s", -1e-08), ("linear_s", "3e-8"), ("linear_s", None)])
def test_settling_type(sc, field, val):
    sc.human["compensation_targets"]["settling"][field] = val
    d = sc.reject()
    assert "type" in sc.rules(d) and d["rejected_gates"] == ("compensation_targets",)


def test_value_and_ref(sc):
    sc.human["compensation_targets"]["gbw_target_hz"]["value_from_constraint"] = "pm_ss_deg"
    sc.reject_only("value_and_ref", "compensation_targets")


def test_value_and_ref_none(sc):
    del sc.human["compensation_targets"]["gbw_target_hz"]["value"]
    sc.reject_only("value_and_ref", "compensation_targets")


def test_ref_kind_mismatch(sc):
    sc.human["compensation_targets"]["pm_target_deg"]["source"] = dict(US)
    sc.reject_only("ref_kind_mismatch", "compensation_targets")


def test_value_with_reference_kind(sc):
    sc.human["compensation_targets"]["gbw_target_hz"]["source"] = {"kind": "reference"}
    sc.reject_only("ref_kind_mismatch", "compensation_targets")


def test_value_from_file_target_key(sc):
    """value_from_file 이 대상 회로의 보상 목표 키를 가리키면 그 값(fx_spec_ref JSON 의 gbw_target_hz)."""
    sc.human["compensation_targets"]["gbw_target_hz"] = {"value_from_file": "fx_spec_ref#gbw_target_hz",
                                                         "source": {"kind": "reference"}}
    want = sc.read_spec("fx_spec_ref")["human"]["compensation_targets"]["gbw_target_hz"]["value"]
    assert dict(sc.load().compensation_targets)["gbw_target_hz"].value == want


@pytest.mark.parametrize("key", ["compensation", "function", "kg", "Z", "NDP", "stage_devices", "spec_fn", "inherits"])
def test_circuit_specific_key(sc, key):
    sc.human["compensation_targets"][key] = {"value": 1.0, "source": dict(US)}
    sc.reject_only("circuit_specific_key", "compensation_targets")


def test_unknown_target_key(sc):
    sc.human["compensation_targets"]["ugf_target_hz"] = {"value": 1.0, "source": dict(US)}
    sc.reject_only("unknown_key", "compensation_targets")


def test_load_cap_is_not_a_target_key(sc):
    """부하 용량은 요소 이름으로 element_values 에서 -- 목표 키가 아니다."""
    sc.human["compensation_targets"]["cl_farad"] = {"value": 1e-12, "source": dict(US)}
    d = sc.reject()
    assert sc.rules(d) in (["unknown_key"], ["legacy_name"], ["circuit_specific_key"])
    assert d["rejected_gates"] == ("compensation_targets",)


@pytest.mark.parametrize("kind,extra", [("pending_spice", {"record": "r"}), ("plan_rule", {"plan_id": "DEC-1"})])
def test_source_kind_not_allowed(sc, kind, extra):
    sc.human["compensation_targets"]["gbw_target_hz"]["source"] = dict(kind=kind, **extra)
    sc.reject_only("source_kind_not_allowed_here", "compensation_targets")
