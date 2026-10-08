"""요소 값 `human.element_values`·되먹임 `human.feedback` (gate `elements`) -- SPEC_CONTRACT 2절 element_*·feedback 행,
F4(전부 선언)·F5(요소 값 정본 = spec, 옛 값과 어긋나면 element_value_conflict). 교차: 이름·kind 가 topology 와 일치."""
from __future__ import annotations

import pytest

SRC = {"kind": "user_spec", "record": "r", "decided": "2026-10-07"}
VALUE_KEY_BY_KIND = {"capacitor": "value_farad", "resistor": "value_ohm", "current_source": "value_dc_amp",
                     "voltage_source": "value_dc_v"}


def _topo_elements(topo):
    return {e["name"]: e["kind"] for e in topo["passive_elements"] + topo.get("ideal_sources", [])}


def test_names_equal_topology_elements(sc):
    """JSON 교차: 픽스처 element_values 이름 집합 = topology 수동·이상원 이름 집합."""
    assert set(sc.human["element_values"]) == set(_topo_elements(sc.topo))


def test_result_matches_json(sc):
    doc = sc.load()
    got = {e.name: e for e in doc.element_values}
    assert [e.name for e in doc.element_values] == sorted(sc.human["element_values"])
    for name, raw in sc.human["element_values"].items():
        e = got[name]
        if "pending" in raw:
            assert (e.mode, e.decision) == ("pending", raw["pending"])
        elif raw.get("engine") is True:
            assert e.mode == "engine"
        else:
            vk = VALUE_KEY_BY_KIND[_topo_elements(sc.topo)[name]]
            assert (e.mode, e.value_key, e.value) == ("value", vk, raw[vk])


def test_feedback_result(sc):
    assert sc.load().feedback == tuple(sorted(sc.human["feedback"]["elements"]))


def test_feedback_empty_and_pending(sc):
    sc.human["feedback"]["elements"] = []
    assert sc.load().feedback == ()
    sc.human["feedback"] = {"pending": "CI-10"}
    fb = sc.load().feedback
    assert fb.decision == "CI-10"


def test_element_unknown(sc):
    sc.human["element_values"]["Rzz"] = {"value_ohm": 5.0, "source": SRC}
    hit = sc.reject_only("element_unknown", "elements")
    assert "Rzz" in hit.elements or "Rzz" in hit.where


def test_device_name_is_not_an_element(sc):
    """MOS 소자는 값 선언 대상(수동·이상원)이 아니다."""
    sc.human["element_values"]["Q1"] = {"engine": True, "source": SRC}
    sc.reject_only("element_unknown", "elements")


@pytest.mark.parametrize("name", ["Rfb", "Cld", "Ibs", "Vcm"])
def test_element_undeclared(sc, name):
    """F4: topology 원소를 spec 에서 빼면(조용한 기본값 금지) 거부."""
    del sc.human["element_values"][name]
    hit = sc.reject_only("element_undeclared", "elements")
    assert name in hit.elements or name in hit.where


@pytest.mark.parametrize("name,wrong", [("Rfb", "value_farad"), ("Cld", "value_ohm"), ("Ibs", "value_dc_v"),
                                        ("Rfb", "value_dc_amp")])
def test_element_value_key(sc, name, wrong):
    raw = sc.human["element_values"][name]
    for k in list(raw):
        if k.startswith("value"):
            del raw[k]
    raw[wrong] = 1.0
    d = sc.reject()
    assert sc.rules(d) == ["element_value_key"], sc.rules(d)
    assert d["rejected_gates"] == ("elements",)


@pytest.mark.parametrize("name,key", [("Vcm", "value_dc_v"), ("Ibs", "value_dc_amp")])
def test_source_value_keys(sc, name, key):
    sc.human["element_values"][name] = {key: 0.5, "source": SRC}
    got = {e.name: e for e in sc.load().element_values}[name]
    assert (got.value_key, got.value) == (key, 0.5)


@pytest.mark.parametrize("name,key,v", [("Rfb", "value_ohm", 0.0), ("Rfb", "value_ohm", -5.0),
                                        ("Cld", "value_farad", 0.0), ("Cld", "value_farad", -1e-12)])
def test_element_value_non_positive_passive(sc, name, key, v):
    sc.human["element_values"][name][key] = v
    sc.reject_only("element_value", "elements")


def test_negative_source_value_allowed(sc):
    """element_value 는 '수동소자 값 <= 0' 만 -- 이상원 값의 부호는 제한이 없다."""
    sc.human["element_values"]["Vcm"] = {"value_dc_v": -0.3, "source": SRC}
    sc.load()


@pytest.mark.parametrize("raw", [
    {"value_ohm": 1.0, "engine": True, "source": SRC},
    {"source": SRC},
    {"engine": False, "source": SRC},
    {"value_ohm": "1k", "source": SRC},
    {"value_ohm": None, "source": SRC},
    5.0,
])
def test_type(sc, raw):
    sc.human["element_values"]["Rfb"] = raw
    d = sc.reject()
    assert sc.rules(d) == ["type"], sc.rules(d)
    assert d["rejected_gates"] == ("elements",)


def _set_topology_old_value(sc, name, key, value):
    t = sc.read_topo("fx_spec_amp")
    for e in t["passive_elements"] + t["ideal_sources"]:
        if e["name"] == name:
            e[key] = value
    sc.write_topo(t)
    sc.resync_fp()


def test_conflict_same_value_ok(sc):
    _set_topology_old_value(sc, "Rfb", "value_ohm", 10000.0)
    sc.load()


def test_conflict_different_value(sc):
    _set_topology_old_value(sc, "Rfb", "value_ohm", 2000.0)
    sc.reject_only("element_value_conflict", "elements")


def test_conflict_spec_engine(sc):
    _set_topology_old_value(sc, "Cfb", "value_farad", 1e-12)
    sc.reject_only("element_value_conflict", "elements")


def test_conflict_spec_pending(sc):
    """2절: 옛 값이 있는데 spec 이 pending 이어도 element_value_conflict."""
    _set_topology_old_value(sc, "Ibs", "value_amp", 1e-06)
    sc.human["element_values"]["Ibs"] = {"pending": "CI-17"}
    sc.reject_only("element_value_conflict", "elements")


def test_conflict_spec_pending_passive(sc):
    _set_topology_old_value(sc, "Cld", "value_farad", 2e-12)
    sc.human["element_values"]["Cld"] = {"pending": "SP-10"}
    sc.reject_only("element_value_conflict", "elements")


def test_feedback_element_unknown(sc):
    # Cfb = 입력 포트 넷(n_inn)에 단자 하나 -- 절단 규칙(7a design 2.2 L2) 위반 없는 알려진 소자 + 모르는 이름
    sc.human["feedback"]["elements"] = ["Cfb", "Rzz"]
    sc.reject_only("feedback_element_unknown", "elements")


@pytest.mark.parametrize("name", ["Ibs", "Q1"])
def test_feedback_must_be_passive(sc, name):
    sc.human["feedback"]["elements"] = [name]
    sc.reject_only("feedback_element_unknown", "elements")


@pytest.mark.parametrize("raw", [{"elements": ["Rfb", "Rfb"], "source": SRC}, {"elements": "Rfb", "source": SRC},
                                 {"elements": [3], "source": SRC}, ["Rfb"]])
def test_feedback_type(sc, raw):
    sc.human["feedback"] = raw
    d = sc.reject()
    assert sc.rules(d) == ["type"], sc.rules(d)
    assert d["rejected_gates"] == ("elements",)


def test_feedback_source_required(sc):
    del sc.human["feedback"]["source"]
    sc.reject_only("source_missing", "elements")


def test_cross_checks_skipped_on_fp_mismatch(sc):
    sc.spec["meta"]["topology_fp"] = "0" * 64
    del sc.human["element_values"]["Rfb"]
    sc.human["feedback"]["elements"] = ["Rzz"]
    d = sc.reject()
    assert "element_undeclared" not in sc.rules(d) and "feedback_element_unknown" not in sc.rules(d)


# ---------------------------------------------------------------- [사용자 결정 11, 2026-10-08] 측정 부하 표지 measurement_load
# oracle (d): SPEC_CONTRACT '측정 부하 표지' 문단(결정 11 "Cl을 빼는 것에 동의해") -- 커패시터·저항 요소 항목(값 또는 engine)에 선택 키
# "measurement_load": true, ElementValue.measurement_load(기본 False). true 가 아닌 값·커패시터/저항이 아닌 요소는 `type`.
# 기대값은 이 test 가 JSON 에 적은 선언(구성으로 정해진 합성 입력)이다 -- 피검 로더 출력으로 만들지 않는다.

def test_measurement_load_default_false(sc):
    """선언하지 않으면 모든 요소의 measurement_load 는 False(기본)."""
    doc = sc.load()
    assert [(e.name, e.measurement_load) for e in doc.element_values] == [
        (n, False) for n in sorted(sc.human["element_values"])]


@pytest.mark.parametrize("name", ["Cld", "Rfb", "Cfb"])
def test_measurement_load_true_on_rc_value_or_engine(sc, name):
    """커패시터(값 Cld·engine Cfb)·저항(값 Rfb) 항목의 true 는 그 요소만 True 로 싣는다. 값·mode 는 그대로."""
    before = {e.name: (e.mode, e.value_key, e.value) for e in sc.load().element_values}
    sc.human["element_values"][name]["measurement_load"] = True
    got = {e.name: e for e in sc.load().element_values}
    assert {n: e.measurement_load for n, e in got.items()} == {n: n == name for n in got}
    assert {n: (e.mode, e.value_key, e.value) for n, e in got.items()} == before


@pytest.mark.parametrize("name,key", [("Ibs", "value_dc_amp"), ("Vcm", "value_dc_v")])
def test_measurement_load_on_source_rejected(sc, name, key):
    """전류원·전압원(커패시터/저항이 아닌 요소)의 measurement_load -> `type`(gate elements)."""
    sc.human["element_values"][name] = {key: 0.5, "source": SRC, "measurement_load": True}
    d = sc.reject()
    assert sc.rules(d) == ["type"], sc.rules(d)
    assert d["rejected_gates"] == ("elements",)


@pytest.mark.parametrize("bad", [False, 1, 1.0, "true", None, [True], {"v": True}],
                         ids=["false", "int", "float", "str", "null", "list", "obj"])
def test_measurement_load_non_true_rejected(sc, bad):
    """true 가 아닌 값 -> `type`(gate elements). SPEC_CONTRACT 문장 그대로 false 도 거부(표지는 '있으면 true' 하나), bool 아닌
    1·"true"·null 등도 거부 -- 1 == True 혼동을 받지 않는다."""
    sc.human["element_values"]["Cld"]["measurement_load"] = bad
    d = sc.reject()
    assert sc.rules(d) == ["type"], sc.rules(d)
    assert d["rejected_gates"] == ("elements",)


def test_measurement_load_changes_spec_fp(sc):
    """선언은 spec 내용이다 -- 같은 spec 에 표지만 더하면 spec_fp 가 바뀐다(조용히 버리지 않는다)."""
    a = sc.load().spec_fp
    sc.human["element_values"]["Cld"]["measurement_load"] = True
    assert sc.load().spec_fp != a
