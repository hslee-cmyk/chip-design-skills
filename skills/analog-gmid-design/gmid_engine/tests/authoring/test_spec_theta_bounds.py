"""`gmid_engine/authoring/spec_theta_bounds.py` 의 동작 test -- spec `search.theta_bounds`(사용자 결정 8·10, 2026-10-08).

기준은 `gmid_engine/authoring/SPEC_CONTRACT.md` 0절(게이트 순서 -- theta_bound_declaration 은 settings·elements 가 둘 다 나왔을 때만),
1절(형식: {원소: {min, max, source}}, 단위 = kind SI, 원소 = topology 저항·커패시터 중 spec 값 mode engine), 2절(위반 규칙 표),
3절(결과 SettingValue("theta_bounds", (ThetaBound(element, kind, lo, hi, source), ...) 원소 이름순) 맨 앞, 지문) 만 쓴다.
피검 함수로 기대값을 만들지 않는다 -- 기대값은 픽스처 JSON(fx_spec_amp: Rfb 고정 저항·Cfb engine 커패시터·Cld 고정 커패시터·
Ibs 이상 전류원·Vcm 결정 대기 전압원·Q1~Q5 MOS)과 계약 문장(oracle (d) 계약·사용자 결정 문장 + 구성으로 정해진 합성 입력 (a)).
"""
from __future__ import annotations

import copy

import pytest

from gmid_engine.authoring import THETA_BOUNDS, SettingValue, ThetaBound

US = {"kind": "user_spec", "record": "fixture theta box", "decided": "2026-10-08"}
C_BOX = {"min": 1e-13, "max": 1e-11, "source": US}          # 결정 10 의 커패시터 상자 [0.1 pF, 10 pF] (F)
R_BOX = {"min": 1e3, "max": 1e6, "source": US}              # 결정 8 의 sf_pushpull 저항 상자 [1 kΩ, 1 MΩ] (Ω)


def _set(sc, bounds):
    sc.human["search"]["theta_bounds"] = bounds


def _engine(sc, name):
    """fx_spec_amp 의 원소 값을 engine 으로(입력 구성)."""
    sc.human["element_values"][name] = {"engine": True, "source": copy.deepcopy(US)}


def _theta_setting(doc):
    return [s for s in doc.search if s.field == THETA_BOUNDS]


# ---------------------------------------------------------------- 통과 형식 (1절·3절)

def test_constant_name():
    assert THETA_BOUNDS == "theta_bounds"


def test_engine_capacitor_box_loads_first_in_search(sc):
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    doc = sc.load()
    assert isinstance(doc.search[0], SettingValue) and doc.search[0].field == THETA_BOUNDS   # 맨 앞(3절)
    assert len(_theta_setting(doc)) == 1
    (tb,) = doc.search[0].value
    assert isinstance(tb, ThetaBound)
    assert (tb.element, tb.kind, tb.lo, tb.hi) == ("Cfb", "capacitor", 1e-13, 1e-11)
    assert tb.source.kind == "user_spec"


def test_resistor_and_capacitor_boxes_sorted_by_element(sc):
    """원소 이름순(3절): JSON 순서 Rfb, Cfb -> 결과 Cfb, Rfb. kind 는 topology 가 정한다(키 이름에 단위 없음, 1절)."""
    _engine(sc, "Rfb")
    _set(sc, {"Rfb": copy.deepcopy(R_BOX), "Cfb": copy.deepcopy(C_BOX)})
    doc = sc.load()
    got = [(t.element, t.kind, t.lo, t.hi) for t in doc.search[0].value]
    assert got == [("Cfb", "capacitor", 1e-13, 1e-11), ("Rfb", "resistor", 1e3, 1e6)]


def test_plan_rule_source_allowed(sc):
    """search 섹션 허용 출처 kind = user_spec·plan_rule(1절 표)."""
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "plan_rule", "plan_id": "DEC-92"}}})
    (tb,) = sc.load().search[0].value
    assert tb.source.kind == "plan_rule"


def test_comment_key_allowed_in_entry(sc):
    _set(sc, {"Cfb": dict(copy.deepcopy(C_BOX), _c="comment")})
    (tb,) = sc.load().search[0].value
    assert (tb.lo, tb.hi) == (1e-13, 1e-11)


def test_absent_or_empty_theta_bounds_loads(sc):
    """칸이 없거나 빈 객체여도 로드는 통과(1절). 칸이 없으면 theta_bounds SettingValue 도 없다(3절 '있으면')."""
    doc = sc.load()
    assert _theta_setting(doc) == []
    _set(sc, {})
    assert sc.load().circuit == "fx_spec_amp"


def test_box_is_not_a_pending_place(sc):
    """상자는 결정 대기 표지를 받지 않는다(1절) -- 상자가 생겨도 표지 수는 그대로."""
    before = sc.load().pending
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    assert sc.load().pending == before


# ---------------------------------------------------------------- 위반 규칙 (2절) -- 규칙마다 hit 하나

@pytest.mark.parametrize("bad", [[], "box", 1.0, None])
def test_theta_bounds_not_object_type(sc, bad):
    _set(sc, bad)
    sc.reject_only("type", "settings")


@pytest.mark.parametrize("bad", [[1e-13, 1e-11], "1p..10p", 1e-12])
def test_entry_not_object_type(sc, bad):
    _set(sc, {"Cfb": bad})
    sc.reject_only("type", "settings")


@pytest.mark.parametrize("key", ["min", "max"])
@pytest.mark.parametrize("bad", [0, 0.0, -1e-12, "1e-12", True, False])
def test_min_max_not_positive_finite_type(sc, key, bad):
    """min·max 양의 유한 수(bool 아님) -- 0·음수·문자열·bool 은 type(2절). 비유한(Infinity·NaN)은 JSON 수준에서 json_read 가
    먼저 거부한다(0절) -- 이 게이트까지 오지 않아 여기서 다루지 않는다."""
    box = copy.deepcopy(C_BOX)
    box[key] = bad
    _set(sc, {"Cfb": box})
    sc.reject_only("type", "settings")


@pytest.mark.parametrize("lo, hi", [(1e-11, 1e-11), (1e-11, 1e-13)])
def test_min_not_below_max_range(sc, lo, hi):
    _set(sc, {"Cfb": {"min": lo, "max": hi, "source": US}})
    sc.reject_only("theta_bound_range", "settings")


@pytest.mark.parametrize("missing", ["min", "max"])
def test_missing_min_or_max(sc, missing):
    box = copy.deepcopy(C_BOX)
    del box[missing]
    _set(sc, {"Cfb": box})
    hit = sc.reject_only("missing_key", "settings")
    assert hit.where.endswith("theta_bounds.Cfb." + missing), hit.where


def test_missing_both_one_hit_per_key(sc):
    """없는 키마다 하나(2절)."""
    _set(sc, {"Cfb": {"source": US}})
    d = sc.reject()
    assert sc.rules(d) == ["missing_key", "missing_key"]
    assert sorted(h.where.rsplit(".", 1)[1] for h in d["hits"]) == ["max", "min"]
    assert d["rejected_gates"] == ("settings",)


@pytest.mark.parametrize("key", ["unit", "lo", "value_farad"])
def test_unknown_entry_key(sc, key):
    _set(sc, {"Cfb": dict(copy.deepcopy(C_BOX), **{key: 1.0})})
    sc.reject_only("unknown_key", "settings")


def test_source_missing(sc):
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11}})
    sc.reject_only("source_missing", "settings")


def test_source_kind_reference_not_allowed(sc):
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "reference"}}})
    sc.reject_only("source_kind_not_allowed_here", "settings")


def test_source_kind_pending_spice_not_allowed(sc):
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "pending_spice", "record": "x"}}})
    sc.reject_only("source_kind_not_allowed_here", "settings")


def test_source_paper_not_adopted(sc):
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "paper"}}})
    sc.reject_only("paper_source_not_adopted", "settings")


def test_source_kind_unknown(sc):
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "guess"}}})
    sc.reject_only("source_kind_unknown", "settings")


def test_source_record_missing(sc):
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "user_spec", "decided": "2026-10-08"}}})
    sc.reject_only("source_record_missing", "settings")


@pytest.mark.parametrize("name", [
    "Nope",     # topology 에 없는 이름
    "Cld",      # 고정 값 커패시터
    "Rfb",      # 고정 값 저항
    "Q1",       # MOS
    "Ibs",      # 이상 전류원(값 있음)
    "Vcm",      # 이상 전압원(결정 대기)
])
def test_element_not_engine_passive(sc, name):
    """원소 = topology 저항·커패시터 중 spec 값 mode engine 만(1절) -- 그 밖은 theta_bound_element(gate theta_bounds)."""
    _set(sc, {name: copy.deepcopy(R_BOX)})
    sc.reject_only("theta_bound_element", "theta_bounds")


def test_pending_valued_resistor_not_accepted(sc):
    """결정 대기 값 저항(Rfb 를 pending 으로) -> mode engine 아님 -> theta_bound_element."""
    sc.human["element_values"]["Rfb"] = {"pending": "SP-93"}
    _set(sc, {"Rfb": copy.deepcopy(R_BOX)})
    sc.reject_only("theta_bound_element", "theta_bounds")


def test_pending_marker_in_place_of_box_rejected(sc):
    """결정 대기 표지는 받지 않는다(1절) -- 원소 칸 자리의 표지는 거부(규칙 이름은 계약이 정하지 않음 -- 보고 항목)."""
    _set(sc, {"Cfb": {"pending": "SP-94"}})
    d = sc.reject()
    assert d["rejected_gates"] == ("settings",), d["rejected_gates"]


def test_element_gate_skipped_when_elements_rejected(sc):
    """theta_bound_declaration 은 settings·elements 가 둘 다 나왔을 때만(0절) -- elements 위반이 있으면 원소 검사는 하지 않는다."""
    sc.human["element_values"]["Rfb"]["value_ohm"] = -1.0          # element_value(≤ 0) -> elements 거부
    _set(sc, {"Nope": copy.deepcopy(R_BOX)})
    d = sc.reject()
    assert "elements" in d["rejected_gates"]
    assert "theta_bounds" not in d["rejected_gates"]
    assert "theta_bound_element" not in sc.rules(d)


def test_element_gate_skipped_when_settings_rejected(sc):
    """settings 에 위반(theta_bounds 형식 type)이 있으면 원소 게이트는 돌지 않는다(0절)."""
    _set(sc, {"Cfb": dict(copy.deepcopy(C_BOX), min=-1.0), "Nope": copy.deepcopy(R_BOX)})
    d = sc.reject()
    assert d["rejected_gates"] == ("settings",)
    assert "theta_bound_element" not in sc.rules(d)


# ---------------------------------------------------------------- 지문 (3절)

def _fps(doc):
    return dict(doc.section_fps)


def _changed(a, b):
    fa, fb = _fps(a), _fps(b)
    assert set(fa) == set(fb)
    return [k for k in fa if fa[k] != fb[k]]


def test_box_enters_search_fp_only(sc):
    """theta_bounds(원소·kind·min·max·출처 kind)는 search_fp 에 든다 -- 상자를 더하거나 min 만 바꾸면 search_fp·spec_fp 만 바뀐다."""
    base = sc.load()
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    with_box = sc.load()
    box2 = copy.deepcopy(C_BOX)
    box2["min"] = 2e-13
    _set(sc, {"Cfb": box2})
    min_changed = sc.load()
    for a, b in ((base, with_box), (with_box, min_changed)):
        assert _changed(a, b) == ["search_fp"]
        assert a.spec_fp != b.spec_fp


def test_max_change_changes_search_fp(sc):
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    a = sc.load()
    box2 = copy.deepcopy(C_BOX)
    box2["max"] = 2e-11
    _set(sc, {"Cfb": box2})
    b = sc.load()
    assert _changed(a, b) == ["search_fp"] and a.spec_fp != b.spec_fp


def test_source_kind_change_changes_search_fp(sc):
    """출처 kind 는 지문에 든다(3절 '출처 kind')."""
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    a = sc.load()
    _set(sc, {"Cfb": {"min": 1e-13, "max": 1e-11, "source": {"kind": "plan_rule", "plan_id": "DEC-92"}}})
    b = sc.load()
    assert _changed(a, b) == ["search_fp"]


def test_record_text_change_keeps_fingerprints(sc):
    """출처 record·decided 문구만 바꾸면 section_fps·spec_fp 불변(3절 SpecSource 는 kind 만 지문)."""
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    a = sc.load()
    box2 = copy.deepcopy(C_BOX)
    box2["source"] = {"kind": "user_spec", "record": "다른 문구", "decided": "2026-10-09"}
    _set(sc, {"Cfb": box2})
    b = sc.load()
    assert _fps(a) == _fps(b) and a.spec_fp == b.spec_fp


def test_comment_key_outside_fingerprint(sc):
    _set(sc, {"Cfb": copy.deepcopy(C_BOX)})
    a = sc.load()
    _set(sc, {"Cfb": dict(copy.deepcopy(C_BOX), _c="note")})
    b = sc.load()
    assert a.spec_fp == b.spec_fp


def test_element_order_in_json_keeps_fingerprint(sc):
    _engine(sc, "Rfb")
    _set(sc, {"Rfb": copy.deepcopy(R_BOX), "Cfb": copy.deepcopy(C_BOX)})
    a = sc.load()
    _set(sc, {"Cfb": copy.deepcopy(C_BOX), "Rfb": copy.deepcopy(R_BOX)})
    b = sc.load()
    assert a.spec_fp == b.spec_fp
