"""[U5 2026-10-08] spec `human.structure_count_budget` -- 설계 40 §3.1 필드 표(`{value, source}`, 선택 항목, 없으면 LUT 격자 유도값
-- 41 §0), SPEC_CONTRACT 1절·2절·3절.

기대값 출처(oracle):
* (d) 설계 문장: 형식 `{value, source}`, 선택 항목(없으면 None -- 유도값은 GB4/search 몫).
* (d) 계약 문장: value = 양의 정수(bool·실수 아님, 0·음수 아님) 아니면 `type`, 결과 `CountBudgetDecl` 또는 None, kind user_spec 만.
* (a) 합성 입력: 이 test 가 고른 정수.
"""
from __future__ import annotations

import copy

import pytest

from gmid_engine.authoring import CountBudgetDecl, SpecSource

GATE = "structure_count_budget"
US = {"kind": "user_spec", "record": "fixture count budget", "decided": "2026-10-08"}


def _set(sc, value):
    sc.human[GATE] = {"value": value, "source": copy.deepcopy(US)}


def test_absent_is_none(sc):
    assert GATE not in sc.human
    assert sc.load().structure_count_budget is None


@pytest.mark.parametrize("n", [1, 7, 4096])
def test_positive_int(sc, n):
    _set(sc, n)
    c = sc.load().structure_count_budget
    assert isinstance(c, CountBudgetDecl)
    assert c.value == n and type(c.value) is int
    assert isinstance(c.source, SpecSource) and c.source.kind == "user_spec"


@pytest.mark.parametrize("bad", [0, -3, 2.5, 5.0, True, False, "5", None, [5]],
                         ids=["zero", "negative", "real", "integral_real", "true", "false", "str", "null", "list"])
def test_value_not_positive_int(sc, bad):
    _set(sc, bad)
    sc.reject_only("type", GATE)


def test_missing_value_rejected(sc):
    sc.human[GATE] = {"source": copy.deepcopy(US)}
    d = sc.reject()
    assert d["rejected_gates"] == (GATE,)


def test_section_not_object(sc):
    sc.human[GATE] = 5
    d = sc.reject()
    assert sc.rules(d) == ["type"]


def test_pending_marker_not_accepted(sc):
    sc.human[GATE] = {"pending": "SP-2"}
    d = sc.reject()
    assert d["rejected_gates"] == (GATE,)          # 규칙 이름은 계약이 이 섹션에 대해 정하지 않음(보고서 이의)


def test_unknown_key(sc):
    _set(sc, 5)
    sc.human[GATE]["grid"] = "lut"
    sc.reject_only("unknown_key", GATE)


def test_source_missing(sc):
    sc.human[GATE] = {"value": 5}
    sc.reject_only("source_missing", GATE)


@pytest.mark.parametrize("src", [{"kind": "pending_spice", "record": "r"}, {"kind": "plan_rule", "plan_id": "N3.7"}],
                         ids=["pending_spice", "plan_rule"])
def test_source_kind_not_user_spec(sc, src):
    sc.human[GATE] = {"value": 5, "source": src}
    sc.reject_only("source_kind_not_allowed_here", GATE)
