"""`gmid_engine/authoring/spec_untie.py` + settings 의 `search.untie_orbits` -- SPEC_CONTRACT 1절 [2026-10-08]·2절 표·3절(사용자 결정 '정준 라벨링 +
대칭 변수 묶음, 기본값 묶음', search CONTRACT r12 3.24 5).

기대값은 픽스처 JSON(fx_spec_amp: Mfx1~Mfx5 MOS, Rfb·Cfb·Cld 수동소자, Ibs 이상 전류원, Vcm 전압원)과 계약 문장(oracle (d))으로 정한다.
- 형식: {원소: {source}} 닫힌 어휘(`_` 주석 키 허용), 출처 필수·kind user_spec 만(record·decided 필수), 결정 대기 표지 안 받음.
- 위반: `type`(객체 아님/원소 칸 객체 아님, gate settings), `unknown_key`(칸 키가 {source} 밖, settings), `source_missing`·
  `source_kind_not_allowed_here`(settings), `untie_element`(MOS·수동소자 이름 아님, gate untie_orbits, where human.search.untie_orbits.<원소>).
- 결과: SettingValue("untie_orbits", ((원소, source), ...) 이름순), theta_bounds 다음, 공개 상수 `UNTIE_ORBITS`.
"""
from __future__ import annotations

import copy

import pytest

from gmid_engine.authoring import THETA_BOUNDS, UNTIE_ORBITS, SettingValue

US = {"kind": "user_spec", "record": "fixture asymmetric sizing", "decided": "2026-10-08"}


def _set(sc, value):
    sc.human["search"]["untie_orbits"] = value


def _entry():
    return {"source": copy.deepcopy(US)}


def _untie(doc):
    return [s for s in doc.search if s.field == UNTIE_ORBITS]


def test_constant_name():
    assert UNTIE_ORBITS == "untie_orbits"


def test_loads_sorted_by_element(sc):
    """JSON 순서 Mfx3, Cfb, Mfx1 -> 결과 이름순 (Cfb, Mfx1, Mfx3). source kind 는 user_spec."""
    _set(sc, {"Mfx3": _entry(), "Cfb": _entry(), "Mfx1": _entry()})
    doc = sc.load()
    (sv,) = _untie(doc)
    assert isinstance(sv, SettingValue)
    assert [e for e, _ in sv.value] == ["Cfb", "Mfx1", "Mfx3"]
    assert all(src.kind == "user_spec" for _, src in sv.value)


def test_after_theta_bounds(sc):
    """theta_bounds 가 있으면 그 바로 다음(3절)."""
    sc.human["element_values"]["Cfb"] = {"engine": True, "source": copy.deepcopy(US)}
    sc.human["search"]["theta_bounds"] = {"Cfb": {"min": 1e-13, "max": 1e-11, "source": copy.deepcopy(US)}}
    _set(sc, {"Mfx1": _entry()})
    fields = [s.field for s in sc.load().search]
    assert fields.index(UNTIE_ORBITS) == fields.index(THETA_BOUNDS) + 1


def test_absent_no_setting(sc):
    sc.human["search"].pop("untie_orbits", None)
    assert _untie(sc.load()) == []


def test_comment_key_allowed(sc):
    e = _entry()
    e["_why"] = "비대칭 사이징 의도"
    _set(sc, {"Mfx2": e})
    assert [x for x, _ in _untie(sc.load())[0].value] == ["Mfx2"]


@pytest.mark.parametrize("name", ["Mfx1", "Rfb", "Cfb", "Cld"])
def test_mos_and_passive_accepted(sc, name):
    _set(sc, {name: _entry()})
    assert [x for x, _ in _untie(sc.load())[0].value] == [name]


# ---------------------------------------------------------------- 위반 (2절)

@pytest.mark.parametrize("name", ["Nope", "Ibs", "Vcm"])
def test_untie_element_not_mos_or_passive(sc, name):
    """topology 에 없는 이름·이상 전류원·전압원 -> untie_element(gate untie_orbits), where·elements 지정."""
    _set(sc, {name: _entry()})
    hit = sc.reject_only("untie_element", "untie_orbits")
    assert hit.where == "human.search.untie_orbits." + name
    assert tuple(hit.elements) == (name,)


@pytest.mark.parametrize("bad", [[], "Mfx1", 1.0, None, ["Mfx1"]])
def test_not_object_type(sc, bad):
    _set(sc, bad)
    sc.reject_only("type", "settings")


@pytest.mark.parametrize("bad", ["user_spec", 1, ["source"], None])
def test_entry_not_object_type(sc, bad):
    _set(sc, {"Mfx1": bad})
    sc.reject_only("type", "settings")


@pytest.mark.parametrize("key", ["min", "orbit", "value"])
def test_unknown_entry_key(sc, key):
    e = _entry()
    e[key] = 1
    _set(sc, {"Mfx1": e})
    sc.reject_only("unknown_key", "settings")


def test_source_missing(sc):
    _set(sc, {"Mfx1": {}})
    sc.reject_only("source_missing", "settings")


@pytest.mark.parametrize("kind", ["plan_rule", "reference", "pending_spice"])
def test_source_kind_not_user_spec(sc, kind):
    """비대칭 선택은 사용자 결정 -- plan_rule 도 받지 않는다(1절)."""
    src = {"kind": kind, "record": "x", "decided": "2026-10-08"}
    if kind == "plan_rule":
        src = {"kind": "plan_rule", "section": "N3.7", "record": "x"}
    _set(sc, {"Mfx1": {"source": src}})
    sc.reject_has("source_kind_not_allowed_here", "settings")


def test_pending_marker_rejected(sc):
    """결정 대기 표지는 받지 않는다(1절) -- 로드가 거부된다(규칙 이름은 계약이 정하지 않아 gate 만 본다)."""
    _set(sc, {"pending": "SP-1"})
    d = sc.reject()
    assert d["rejected_gates"]


def test_good_and_bad_entries_one_hit(sc):
    """좋은 칸과 나쁜 원소가 섞이면 나쁜 원소 하나만 hit."""
    _set(sc, {"Mfx1": _entry(), "Nope": _entry()})
    hit = sc.reject_only("untie_element", "untie_orbits")
    assert tuple(hit.elements) == ("Nope",)
