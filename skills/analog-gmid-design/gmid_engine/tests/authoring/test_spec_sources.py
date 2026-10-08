"""출처 `source` 규칙 -- SPEC_CONTRACT 1절 출처 표, 2절 source_* 행(gate = 그 출처가 놓인 섹션).
모든 값 선언에 source 필수, 논문 계열 kind 거부(paper_source_not_adopted), user_spec + origin paper 는 record·citation 필수."""
from __future__ import annotations

import pytest

PAPER_KINDS = ("paper", "paper_reference", "literature", "drawing")

# (섹션 이름 -> (출처 dict 를 꺼내는 함수, gate))
SITES = {
    "supplies": (lambda h: h["supplies_v"], "supplies"),
    "input_dc": (lambda h: h["input_dc"], "input_dc"),
    "elements": (lambda h: h["element_values"]["Rfb"], "elements"),
    "feedback": (lambda h: h["feedback"], "elements"),
    "constraints": (lambda h: h["constraints"][0], "constraints"),
    "targets": (lambda h: h["compensation_targets"]["gbw_target_hz"], "compensation_targets"),
    "settling": (lambda h: h["compensation_targets"]["settling"], "compensation_targets"),
    "node_targets": (lambda h: h["node_voltage_targets_v"]["n_mid"], "node_targets"),
    "objective": (lambda h: h["objective"]["budgets"]["supply_current_dc"], "settings"),
    "search": (lambda h: h["search"]["wall_clock_budget_s"], "settings"),
    "spice_check": (lambda h: h["spice_check"]["acceptance_rule"], "settings"),
    "front_refilter": (lambda h: h["front_refilter"]["axis_rule"], "settings"),
}
SITE_IDS = list(SITES)


def _src(sc, site):
    get, gate = SITES[site]
    return get(sc.human), gate


@pytest.mark.parametrize("site", SITE_IDS)
def test_source_missing(sc, site):
    obj, gate = _src(sc, site)
    del obj["source"]
    sc.reject_only("source_missing", gate)


@pytest.mark.parametrize("site", SITE_IDS)
@pytest.mark.parametrize("kind", PAPER_KINDS)
def test_paper_source_not_adopted(sc, site, kind):
    obj, gate = _src(sc, site)
    obj["source"] = {"kind": kind, "record": "r", "decided": "2026-10-07", "citation": "c"}
    d = sc.reject()
    assert "paper_source_not_adopted" in sc.rules(d)
    assert set(sc.rules(d)) <= {"paper_source_not_adopted", "unknown_key"}
    assert d["rejected_gates"] == (gate,)


@pytest.mark.parametrize("kind", PAPER_KINDS)
def test_paper_source_not_adopted_minimal(sc, kind):
    sc.human["constraints"][0]["source"] = {"kind": kind}
    sc.reject_only("paper_source_not_adopted", "constraints")


def test_adopted_paper_value_via_user_spec(sc):
    """채택된 논문 값 = user_spec + origin paper + record + citation(픽스처 Cld) -> 통과."""
    src = sc.human["element_values"]["Cld"]["source"]
    assert (src["kind"], src["origin"]) == ("user_spec", "paper") and src["record"] and src["citation"]
    got = {e.name: e for e in sc.load().element_values}["Cld"]
    assert (got.source.kind, got.source.origin) == ("user_spec", "paper")


@pytest.mark.parametrize("site", ["constraints", "elements", "supplies"])
def test_user_spec_origin_paper_requires_record(sc, site):
    obj, gate = _src(sc, site)
    obj["source"] = {"kind": "user_spec", "decided": "2026-10-07", "origin": "paper", "citation": "c"}
    sc.reject_only("source_record_missing", gate)


@pytest.mark.parametrize("bad", [{"record": ""}, {"record": None}, {"decided": "07/10/2026"}, {"decided": "2026-10"},
                                 {"decided": None}])
def test_user_spec_record_and_decided(sc, bad):
    src = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
    for k, v in bad.items():
        if v is None:
            src.pop(k)
        else:
            src[k] = v
    sc.human["constraints"][0]["source"] = src
    sc.reject_only("source_record_missing", "constraints")


def test_pending_spice_requires_record(sc):
    sc.constraint("swing_out_v")["source"] = {"kind": "pending_spice"}
    sc.reject_only("source_record_missing", "constraints")


def test_plan_rule_requires_plan_id(sc):
    sc.human["search"]["wall_clock_budget_s"]["source"] = {"kind": "plan_rule", "record": "r"}
    sc.reject_only("source_record_missing", "settings")


@pytest.mark.parametrize("origin", ["paper", "drawing", "lecture"])
def test_citation_missing(sc, origin):
    sc.human["constraints"][0]["source"] = {"kind": "user_spec", "record": "r", "decided": "2026-10-07", "origin": origin}
    sc.reject_only("citation_missing", "constraints")


@pytest.mark.parametrize("origin", ["user", "legacy_harness"])
def test_origin_without_citation_ok(sc, origin):
    sc.human["constraints"][0]["source"] = {"kind": "user_spec", "record": "r", "decided": "2026-10-07", "origin": origin}
    sc.load()


@pytest.mark.parametrize("origin", ["blog", "Paper", "", 3])
def test_source_origin(sc, origin):
    sc.human["constraints"][0]["source"] = {"kind": "user_spec", "record": "r", "decided": "2026-10-07", "origin": origin,
                                            "citation": "c"}
    sc.reject_only("source_origin", "constraints")


@pytest.mark.parametrize("kind", ["guess", "user", "", "spec"])
def test_source_kind_unknown(sc, kind):
    sc.human["constraints"][0]["source"] = {"kind": kind, "record": "r", "decided": "2026-10-07"}
    sc.reject_only("source_kind_unknown", "constraints")


def test_legacy_kind_pending_7a(sc):
    sc.constraint("swing_out_v")["source"] = {"kind": "pending_7a", "record": "r"}
    sc.reject_only("legacy_name", "constraints")


@pytest.mark.parametrize("site,kind,extra", [
    ("elements", "pending_spice", {"record": "r"}),
    ("supplies", "pending_spice", {"record": "r"}),
    ("supplies", "reference", {}),
    ("elements", "reference", {}),
    ("node_targets", "reference", {}),
    ("constraints", "plan_rule", {"plan_id": "DEC-1"}),
    ("elements", "plan_rule", {"plan_id": "DEC-1"}),
    ("targets", "plan_rule", {"plan_id": "DEC-1"}),
    ("spice_check", "pending_spice", {"record": "r"}),
])
def test_source_kind_not_allowed_here(sc, site, kind, extra):
    obj, gate = _src(sc, site)
    obj["source"] = dict(kind=kind, **extra)
    d = sc.reject()
    assert "source_kind_not_allowed_here" in sc.rules(d)
    # 값 자리와 참조 kind 짝(ref_kind_mismatch)이 걸리는 섹션은 그 hit 도 함께 나올 수 있다
    assert set(sc.rules(d)) <= {"source_kind_not_allowed_here", "ref_kind_mismatch"}
    assert d["rejected_gates"] == (gate,)


@pytest.mark.parametrize("raw", ["user_spec", ["user_spec"], 3])
def test_source_not_object(sc, raw):
    sc.human["constraints"][0]["source"] = raw
    sc.reject_only("type", "constraints")


def test_source_unknown_key(sc):
    sc.human["constraints"][0]["source"]["url"] = "http://x"
    sc.reject_only("unknown_key", "constraints")


def test_source_underscore_key_ok(sc):
    sc.human["constraints"][0]["source"]["_why"] = "note"
    sc.load()


def test_every_value_declaration_has_source_in_fixture(sc):
    """JSON 직접 집계: 픽스처의 모든 값 선언(표지·참조 대상 아닌 것)에 source 가 있다 -- 위 test 들이 빼는 대상이 실재함."""
    for site in SITE_IDS:
        obj, _ = _src(sc, site)
        assert "source" in obj, site
