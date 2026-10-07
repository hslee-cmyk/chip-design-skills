"""공용 helper `_two_terminal.py` -- 수동·이상원 공통 원소 규칙(CONTRACT 3.6 표, 3.7 '원소 규칙은 3.6 과 같다', 5절 2).
helper 는 비공개라 공개 접근자 `passive_declaration`·`source_declaration` 양쪽에 같은 위반을 넣어 확인한다."""
from __future__ import annotations

import math

import pytest

from gmid_engine.authoring import TWO_TERMINAL_NAMES, passive_declaration, source_declaration

# (접근자, 최상위 키, gate, 원소 이름, 값 필드 2개)
SIDES = [
    (passive_declaration, "passive_elements", "passives", "Rf", ("value_ohm", "value_farad")),
    (source_declaration, "ideal_sources", "ideal_sources", "Ib", ("value_amp", "value_volt")),
]
IDS = ["passives", "ideal_sources"]


def _elem(doc, key, name):
    return next(e for e in doc[key] if e["name"] == name)


def _reject(ah, fn, doc, gate):
    exc, detail = ah.rejected(fn, doc)
    assert detail["gate"] == gate
    assert detail["where"] == {"passives": "passive_elements", "ideal_sources": "ideal_sources"}[gate]
    return detail["hits"]


def test_two_terminal_names():
    assert TWO_TERMINAL_NAMES == ("t0", "t1")


@pytest.mark.parametrize("side", SIDES, ids=IDS)
def test_element_type_each(ah, side):
    fn, key, gate, name, _ = side
    d = ah.base()
    d[key] += [7, "x", None]
    assert ah.rules(_reject(ah, fn, d, gate)) == ["element_type"] * 3


@pytest.mark.parametrize("side", SIDES, ids=IDS)
@pytest.mark.parametrize("field", ["name", "kind"])
@pytest.mark.parametrize("bad", ["<missing>", "", 5, None])
def test_element_field(ah, side, field, bad):
    fn, key, gate, name, _ = side
    d = ah.base()
    e = _elem(d, key, name)
    if bad == "<missing>":
        del e[field]
    else:
        e[field] = bad
    assert ah.rules(_reject(ah, fn, d, gate)) == ["element_field"]


@pytest.mark.parametrize("side", SIDES, ids=IDS)
@pytest.mark.parametrize("bad", ["n_a,n_b", {"t0": "n_a", "t1": "n_b"}, ["n_outp"], ["n_outp", "n_mid", "n_rzn"], [],
                                 ["n_outp", ""], ["n_outp", 3], ["n_outp", None], ["n_mid", "n_mid"], "<missing>"])
def test_terminals(ah, side, bad):
    fn, key, gate, name, _ = side
    d = ah.base()
    e = _elem(d, key, name)
    if bad == "<missing>":
        del e["terminals"]
    else:
        e["terminals"] = bad
    # 키 없음도 'list 아님'(3.6 terminals 행)으로 읽었다 -- element_field 는 name·kind 만 다룬다
    assert ah.rules(_reject(ah, fn, d, gate)) == ["terminals"]


@pytest.mark.parametrize("side", SIDES, ids=IDS)
@pytest.mark.parametrize("bad", [True, False, "1k", [1.0], {"v": 1}, math.inf, -math.inf, math.nan])
def test_element_value_bad(ah, side, bad):
    fn, key, gate, name, vf = side
    d = ah.base()
    e = _elem(d, key, name)
    for f in vf:
        e.pop(f, None)
    e[vf[0]] = bad
    hits = _reject(ah, fn, d, gate)
    assert ah.rules(hits) == ["element_value"]
    assert name in hits[0].elements


@pytest.mark.parametrize("side", SIDES, ids=IDS)
def test_two_value_fields(ah, side):
    fn, key, gate, name, vf = side
    d = ah.base()
    e = _elem(d, key, name)
    e[vf[0]] = 1.0
    e[vf[1]] = 2.0
    assert ah.rules(_reject(ah, fn, d, gate)) == ["element_value"]


@pytest.mark.parametrize("side", SIDES, ids=IDS)
@pytest.mark.parametrize("good", [None, 0, 3, -2.5, 1e-15, 1e300])
def test_element_value_null_or_finite_ok(ah, side, good):
    fn, key, gate, name, vf = side
    d = ah.base()
    e = _elem(d, key, name)
    for f in vf:
        e.pop(f, None)
    e[vf[1]] = good
    got = {x.name: x for x in fn(d)}
    assert got[name].value_key == vf[1]
    assert got[name].value == good


@pytest.mark.parametrize("side", SIDES, ids=IDS)
def test_unknown_key_and_underscore(ah, side):
    fn, key, gate, name, _ = side
    d = ah.base()
    _elem(d, key, name)["_comment"] = "fine"
    fn(d)
    _elem(d, key, name)["pins"] = 2
    assert ah.rules(_reject(ah, fn, d, gate)) == ["element_unknown_key"]


@pytest.mark.parametrize("side", SIDES, ids=IDS)
def test_all_hits_collected(ah, side):
    fn, key, gate, name, vf = side
    d = ah.base()
    e = _elem(d, key, name)
    e["kind"] = ""
    e["terminals"] = ["n_mid", "n_mid"]
    e[vf[0]] = True
    e["zz"] = 0
    d[key].append(0)
    rules = ah.rules(_reject(ah, fn, d, gate))
    assert sorted(rules) == sorted(["element_field", "terminals", "element_value", "element_unknown_key", "element_type"])
