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
    sc.constraint("swing_out_v")["source"]["kind"] = "pending_7a"
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


# =====================================================================================================================
# [U5 2026-10-08] 정합 metric 옛 이름 -- 설계 40 §3.8-8('옛 이름 mismatch_sigma_mv·mirror_ratio_error_mv·mismatch_sigma_v 는 spec 옛
# 이름 표에 넣어 거부한다(새 이름으로 안내)'), §9.2(대체 관계), §3.8-4(mismatch_sigma_v 대체).
# oracle (d) 설계 문장: 새 이름 안내 = mismatch_sigma_mv -> offset_in_sigma_mv(§9.2 파일럿 행 '옛 mismatch_sigma_mv <= 5 대체'),
#   mirror_ratio_error_mv -> offset_sys_mv(§9.2 '옛 mirror_ratio_error_mv 대체'), mismatch_sigma_v -> offset_in_sigma_mv·
#   mirror_ratio_sigma_pct(§3.8-4). 대문자 V 판(mismatch_sigma_V)은 SPEC_CONTRACT 2절 문장(설계에는 없음 -- 계약 출처).
# 자리: 제약 metric, pending_constraints metric, value_from_constraint, value_from_file 대상 metric, 모든 객체의 키.
# =====================================================================================================================
LEGACY_REPLACEMENTS = {
    "mismatch_sigma_mv": ("offset_in_sigma_mv",),
    "mirror_ratio_error_mv": ("offset_sys_mv",),
    "mismatch_sigma_v": ("offset_in_sigma_mv", "mirror_ratio_sigma_pct"),
}
LEGACY = tuple(LEGACY_REPLACEMENTS)
LEGACY_UPPER = "mismatch_sigma_V"   # SPEC_CONTRACT 2절 '(및 대문자 V 판)' -- 계약 출처
# [U5 후속 2026-10-09] SPEC_CONTRACT 2절 legacy_name 행 '제약 metric 또는 value_from_constraint·value_from_file 문자열이 ...(및 대문자 V 판)'
# + 2절 '모든 객체의 키' -> 대문자 V 판도 모든 자리(pending_constraints·참조·파일 참조·키)에서 확인한다. 안내 이름은 소문자 판과 같은
# 옛 이름이므로 §3.8-4 대체(offset_in_sigma_mv·mirror_ratio_sigma_pct)를 그대로 쓴다(oracle d).
LEGACY_ALL = LEGACY + (LEGACY_UPPER,)
LEGACY_REPLACEMENTS_ALL = dict(LEGACY_REPLACEMENTS, **{LEGACY_UPPER: LEGACY_REPLACEMENTS["mismatch_sigma_v"]})


def _legacy_hit(sc, gate):
    d = sc.reject()
    assert sc.rules(d) == ["legacy_name"], [(h.rule, h.where) for h in d["hits"]]
    assert d["rejected_gates"] == (gate,)
    return d["hits"][0]


@pytest.mark.parametrize("name", LEGACY + (LEGACY_UPPER,))
def test_legacy_metric_in_constraint(sc, name):
    sc.constraint("swing_out_v")["metric"] = name
    _legacy_hit(sc, "constraints")


@pytest.mark.parametrize("name", list(LEGACY_REPLACEMENTS_ALL))
def test_legacy_metric_message_names_replacement(sc, name):
    sc.constraint("swing_out_v")["metric"] = name
    hit = _legacy_hit(sc, "constraints")
    for new in LEGACY_REPLACEMENTS_ALL[name]:
        assert new in hit.message, (name, hit.message)


@pytest.mark.parametrize("name", LEGACY_ALL)
def test_legacy_metric_in_pending_constraints(sc, name):
    sc.human["pending_constraints"].append({"metric": name, "decision": "SP-93"})
    _legacy_hit(sc, "constraints")


@pytest.mark.parametrize("name", LEGACY_ALL)
def test_legacy_value_from_constraint(sc, name):
    sc.constraint("icmr_v")["value_from_constraint"] = name
    _legacy_hit(sc, "constraints")


@pytest.mark.parametrize("name", LEGACY_ALL)
def test_legacy_value_from_constraint_in_compensation_target(sc, name):
    sc.human["compensation_targets"]["pm_target_deg"]["value_from_constraint"] = name
    _legacy_hit(sc, "compensation_targets")


@pytest.mark.parametrize("name", LEGACY_ALL)
def test_legacy_value_from_file_target(sc, name):
    c = next(c for c in sc.human["constraints"] if "value_from_file" in c)
    c["value_from_file"] = "fx_spec_ref#" + name
    _legacy_hit(sc, "constraints")


@pytest.mark.parametrize("where", list(OBJECTS))
@pytest.mark.parametrize("name", LEGACY_ALL)
def test_legacy_name_as_key_everywhere(sc, where, name):
    get, gate = OBJECTS[where]
    get(sc.spec)[name] = {"value": 1.0, "source": dict(US)}
    _legacy_hit(sc, gate)


@pytest.mark.parametrize("name", ["offset_in_sigma_mv", "offset_excess", "offset_sys_mv", "mirror_ratio_sigma_pct",
                                  "icm_margin_v", "ff_gm_ratio"])
def test_new_names_are_not_legacy(sc, name):
    """새 이름은 옛 이름 표에 없다: 제약 metric 으로 받는다(합성 입력 -- 제약 하나 추가, view 없음 -> 유도 또는 none).
    swing_out_v·icmr_v 는 픽스처 제약으로 이미 매 로드에 쓰인다."""
    sc.human["constraints"].append({"metric": name, "op": "<=", "value": 1.0, "source": dict(US)})
    doc = sc.load()
    assert [c.metric for c in doc.constraints].count(name) == 1
