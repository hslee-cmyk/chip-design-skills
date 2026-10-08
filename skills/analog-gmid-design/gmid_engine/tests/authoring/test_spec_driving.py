"""[U5 2026-10-08] spec `human.driving_spec` -- 설계 40 §3.1 필드 표(`{slew_rate_v_per_s?, load_peak_amp?, load_dc_amp?, source}`,
소비자 §3.8 `ls`), §3.8-3('driving_spec 이 선언되면 이 값들로 제약 행을 만든다'), SPEC_CONTRACT 1절·2절·3절.

기대값 출처(oracle):
* (d) 설계 문장: 칸 3개는 모두 선택(`?`), source 필수.
* (d) 계약 문장: 값 칸 = 양의 유한 수(`type`), 하나 이상(`driving_spec_empty`), 결과 `DrivingDecl`(없는 칸 None) 또는 None, kind user_spec 만.
* (a) 합성 입력: 이 test 가 정한 수를 넣고 그대로 나오는지 본다(변환 없음 -- SI 단위 이름이 키에 있다).
"""
from __future__ import annotations

import copy
import json

import pytest

from gmid_engine.core import SchemaRejectedError

from gmid_engine.authoring import DrivingDecl, SpecSource

GATE = "driving_spec"
FIELDS = ("slew_rate_v_per_s", "load_peak_amp", "load_dc_amp")
US = {"kind": "user_spec", "record": "fixture driving", "decided": "2026-10-08"}
VALUES = {"slew_rate_v_per_s": 5e6, "load_peak_amp": 2e-3, "load_dc_amp": 1e-4}   # (a) 손으로 정한 양수


def _set(sc, **fields):
    sc.human[GATE] = dict(fields, source=copy.deepcopy(US))


def test_absent_is_none(sc):
    assert GATE not in sc.human
    assert sc.load().driving_spec is None


def test_all_three_fields(sc):
    _set(sc, **VALUES)
    d = sc.load().driving_spec
    assert isinstance(d, DrivingDecl)
    assert (d.slew_rate_v_per_s, d.load_peak_amp, d.load_dc_amp) == tuple(VALUES[f] for f in FIELDS)
    assert isinstance(d.source, SpecSource) and d.source.kind == "user_spec"


@pytest.mark.parametrize("field", FIELDS)
def test_each_field_alone_others_none(sc, field):
    _set(sc, **{field: VALUES[field]})
    d = sc.load().driving_spec
    for f in FIELDS:
        assert getattr(d, f) == (VALUES[field] if f == field else None), f


def test_integer_value_accepted_as_number(sc):
    _set(sc, slew_rate_v_per_s=10000000)
    assert sc.load().driving_spec.slew_rate_v_per_s == 1e7


# ---------------------------------------------------------------- 거부

def test_empty_rejected(sc):
    sc.human[GATE] = {"source": copy.deepcopy(US)}
    sc.reject_only("driving_spec_empty", GATE)


@pytest.mark.parametrize("field", FIELDS)
@pytest.mark.parametrize("bad", [0, 0.0, -1e-3, "1e-3", True, None, [1.0]],
                         ids=["zero_int", "zero", "negative", "str", "bool", "null", "list"])
def test_value_not_positive_finite(sc, field, bad):
    _set(sc, **{field: bad})
    sc.reject_only("type", GATE)


@pytest.mark.parametrize("token", ["NaN", "Infinity"])
def test_value_non_finite(sc, token, catalog):
    _set(sc, load_peak_amp=1.5)
    path = sc.write_spec(sc.spec)
    text = open(path, encoding="utf-8").read().replace('"load_peak_amp": 1.5', '"load_peak_amp": ' + token)
    assert ('"load_peak_amp": ' + token) in text
    open(path, "w", encoding="utf-8").write(text)
    _reject_raw_file(sc, path, catalog)


@pytest.mark.parametrize("section", [[{"load_dc_amp": 1e-4}], "x", 1.0], ids=["list", "str", "num"])
def test_section_not_object(sc, section):
    sc.human[GATE] = section
    d = sc.reject()
    assert sc.rules(d) == ["type"]


def test_pending_marker_not_accepted(sc):
    """결정 대기 표지는 받지 않는다(계약 1절 U5 문단). 규칙 이름은 이 섹션에 대해 계약이 정하지 않아 게이트만 본다(보고서 이의 참조)."""
    sc.human[GATE] = {"pending": "SP-2"}
    d = sc.reject()
    assert d["rejected_gates"] == (GATE,)


def test_unknown_key(sc):
    _set(sc, load_dc_amp=1e-4, load_cap_farad=1e-12)
    sc.reject_only("unknown_key", GATE)


def test_source_missing(sc):
    sc.human[GATE] = {"load_dc_amp": 1e-4}
    sc.reject_only("source_missing", GATE)


@pytest.mark.parametrize("src", [{"kind": "pending_spice", "record": "r"}, {"kind": "reference"},
                                 {"kind": "plan_rule", "plan_id": "DEC-65"}], ids=["pending_spice", "reference", "plan_rule"])
def test_source_kind_not_user_spec(sc, src):
    sc.human[GATE] = {"load_dc_amp": 1e-4, "source": src}
    sc.reject_only("source_kind_not_allowed_here", GATE)


def _reject_raw_file(sc, path, catalog):
    """비유한 토큰(NaN·Infinity)은 JSON 수준 위반 -- SPEC_CONTRACT 0절 'JSON 수준 위반은 json_read 예외 그대로'(gate json_read).
    섹션 게이트까지 가지 않고 읽기에서 거부된다(계약 2절 '비유한 수 -> type' 보다 앞)."""
    from gmid_engine.authoring import load_sizing_spec
    with pytest.raises(SchemaRejectedError) as ei:
        load_sizing_spec(path, sc.topology(), catalog)
    assert dict(ei.value.record.detail)["gate"] == "json_read"
