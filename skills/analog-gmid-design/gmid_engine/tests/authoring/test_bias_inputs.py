"""`bias_inputs` -- gate 전용 외부 바이어스 넷 선언과 게이트 (authoring CONTRACT 9절, 2026-10-08 Q6).

근거(계약만, authoring 소스 미열람):
- 9절: gate 전용 넷 = MOS gate 에만 나타나고 drain/source/선언 bulk·수동소자·이상원 terminals·레일·포트 어디에도 없는 넷.
  거부 gate `bias_inputs`: `gate_only_undeclared`, `bias_input_not_gate_only`(레일·포트·d/s/bulk/2단자 단자, gate 에도
  없는 넷 포함), `bias_inputs_type`, `bias_input_entry`, `bias_input_duplicate`. 소자·수동·이상원·레일·포트 선언이 모두
  통과했을 때만 돈다(거부된 문서에서는 건너뛰고 `not_evaluated` 이름은 늘리지 않는다).
- `TopologyDoc.bias_inputs` = 정렬 tuple, 기본 `()`. `connectivity_fp` 에 넣지 않는다.
- 0절: test 는 rule·where·elements 로 판정(message 문구는 판정하지 않는다).

oracle: (a) 구성으로 정답이 정해진 합성 입력 -- base_valid 픽스처(gate 전용 넷 없음, 손으로 확인: n_inp 는 입력 포트,
n_bias 는 Ib terminals, n_mid 는 drain)에 MOS 하나(Q5, gate `n_gb`)를 더해 gate 전용 넷을 정확히 하나 만든다. 기대 넷
집합은 test 쪽 `gate_only_nets`(JSON 직접 집계, 9절 정의 문장 그대로)로 계산한다.
"""
from __future__ import annotations

import pytest

import gmid_engine.authoring as authoring
from gmid_engine.authoring import TopologyDoc, load_topology

GATE = "bias_inputs"                  # CONTRACT 9절 gate 이름
NOT_EVALUATED_NAMES = {               # CONTRACT 0절 표 -- 9절 "not_evaluated 이름은 늘리지 않는다"
    "all_declarations", "name_uniqueness", "ports.port_net_unknown", "ports.port_on_rail", "hidden_rails"}


def gate_only_nets(doc):
    """test 쪽 oracle (a): CONTRACT 9절 정의 문장을 JSON 에서 직접 집계."""
    gates, other = set(), set()
    for e in doc["netlist"]:
        gates.add(e["gate"])
        other |= {e["drain"], e["source"]}
        if "bulk" in e:
            other.add(e["bulk"])
    for key in ("passive_elements", "ideal_sources"):
        for e in doc.get(key, []):
            other |= set(e["terminals"])
    other |= set(doc["supply_nets"])
    other |= {k for k in doc["ports"] if not k.startswith("_")}
    return gates - other


_ABSENT = object()                    # 키를 쓰지 않음(None 은 JSON null 로 실제로 쓴다)


def with_gate_only(ah, declared=_ABSENT):
    """base_valid + Q5(gate n_gb, drain n_outp, source rail_lo) -> gate 전용 넷 정확히 {n_gb}(구성)."""
    doc = ah.base()
    doc["netlist"].append({"name": "Q5", "kind": "nmos", "drain": "n_outp", "gate": "n_gb", "source": "rail_lo"})
    if declared is not _ABSENT:
        doc["bias_inputs"] = declared
    return doc


def load_rejected(ah, tmp_path, doc):
    exc, detail = ah.rejected(load_topology, ah.write(tmp_path, doc))
    assert detail["gate"] == "topology_load"
    return detail


def bias_hits(detail):
    return [h for h in detail["hits"] if h.where == GATE or h.where.startswith(GATE)]


# ---------------------------------------------------------------------------------------------------- 픽스처 확인
def test_fixture_construction(ah):
    """구성 확인: base 는 gate 전용 넷이 없고 Q5 를 더하면 정확히 {n_gb}(oracle 이 의도대로인가)."""
    assert gate_only_nets(ah.base()) == set()
    assert gate_only_nets(with_gate_only(ah)) == {"n_gb"}


# ---------------------------------------------------------------------------------------------------- 통과
def test_absent_key_without_gate_only_nets_is_empty(ah, tmp_path):
    """키 없음 + gate 전용 넷 없음 -> 통과, bias_inputs == () (9절 기본 `()`)."""
    td = load_topology(ah.write(tmp_path, ah.base()))
    assert td.bias_inputs == ()


def test_empty_list_without_gate_only_nets_is_empty(ah, tmp_path):
    doc = ah.base()
    doc["bias_inputs"] = []
    assert load_topology(ah.write(tmp_path, doc)).bias_inputs == ()


def test_declared_gate_only_net_loads(ah, tmp_path):
    td = load_topology(ah.write(tmp_path, with_gate_only(ah, ["n_gb"])))
    assert td.bias_inputs == ("n_gb",)
    assert isinstance(td.bias_inputs, tuple)


def test_declared_sorted_regardless_of_order(ah, tmp_path):
    """두 gate 전용 넷(n_gb, n_ga)을 역순으로 선언 -> 정렬 tuple (9절 '정렬 tuple')."""
    doc = with_gate_only(ah, ["n_gb", "n_ga"])
    doc["netlist"].append({"name": "Q6", "kind": "pmos", "drain": "n_outp", "gate": "n_ga", "source": "rail_hi"})
    assert gate_only_nets(doc) == {"n_ga", "n_gb"}
    assert load_topology(ah.write(tmp_path, doc)).bias_inputs == ("n_ga", "n_gb")


# ---------------------------------------------------------------------------------------------------- 거부: 미선언
def test_gate_only_undeclared_absent_key(ah, tmp_path):
    detail = load_rejected(ah, tmp_path, with_gate_only(ah))
    assert ah.rules(detail["hits"]) == ["gate_only_undeclared"]
    assert detail["hits"][0].elements == ("n_gb",)
    assert detail["rejected_gates"] == (GATE,)
    assert detail["not_evaluated"] == ()


def test_gate_only_undeclared_empty_list(ah, tmp_path):
    """키가 있어도 빈 list 면 미선언과 같다."""
    detail = load_rejected(ah, tmp_path, with_gate_only(ah, []))
    assert ah.rules(detail["hits"]) == ["gate_only_undeclared"]
    assert detail["hits"][0].elements == ("n_gb",)


def test_gate_only_undeclared_one_of_two(ah, tmp_path):
    """두 gate 전용 넷 중 하나만 선언 -> 빠진 하나만 걸린다."""
    doc = with_gate_only(ah, ["n_gb"])
    doc["netlist"].append({"name": "Q6", "kind": "pmos", "drain": "n_outp", "gate": "n_ga", "source": "rail_hi"})
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["gate_only_undeclared"]
    assert detail["hits"][0].elements == ("n_ga",)


# ---------------------------------------------------------------------------------------------------- 거부: gate 전용 아님
# 각 넷이 gate 전용이 아닌 이유(base_valid 픽스처를 손으로 읽음):
NOT_GATE_ONLY = {
    "rail": "rail_hi",            # supply_nets
    "port_input": "n_inp",        # ports 의 실제 input 포트(Q1 gate 에만 물리지만 포트라 gate 전용 아님)
    "port_output": "n_outp",      # ports 의 output 포트(drain 이기도 함)
    "drain_and_gate": "n_mid",    # Q1·Q2 drain, Q3 gate
    "nonexistent": "n_ghost",     # 어느 단자에도 없음
    "passive_only": "n_rzn",      # Rf·Cf terminals 에만
    "gate_and_source_terminal": "n_bias",  # Q2·Q4 gate + 이상원 Ib terminals
}


@pytest.mark.parametrize("case", sorted(NOT_GATE_ONLY))
def test_bias_input_not_gate_only(ah, tmp_path, case):
    net = NOT_GATE_ONLY[case]
    doc = with_gate_only(ah, ["n_gb", net])
    assert net not in gate_only_nets(doc)
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["bias_input_not_gate_only"], detail["hits"]
    assert detail["hits"][0].elements == (net,)
    assert detail["rejected_gates"] == (GATE,)


def test_bias_input_not_gate_only_declared_bulk(ah, tmp_path):
    """gate 이면서 다른 소자의 선언 bulk 인 넷은 gate 전용 아님(9절 '선언 bulk')."""
    doc = with_gate_only(ah, ["n_gb"])
    doc["netlist"].append({"name": "Q6", "kind": "nmos", "drain": "n_outp", "gate": "n_mid", "source": "rail_lo",
                           "bulk": "n_gb"})
    assert gate_only_nets(doc) == set()
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["bias_input_not_gate_only"]
    assert detail["hits"][0].elements == ("n_gb",)


def test_bias_input_not_gate_only_all_collected(ah, tmp_path):
    """0절 '걸린 곳 전부': 잘못 선언한 넷 3개 -> hit 3개(넷마다)."""
    doc = with_gate_only(ah, ["n_gb", "rail_lo", "n_inp", "n_ghost"])
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["bias_input_not_gate_only"] * 3
    assert sorted(h.elements for h in detail["hits"]) == [("n_ghost",), ("n_inp",), ("rail_lo",)]


# ---------------------------------------------------------------------------------------------------- 거부: 형식
def test_bias_input_duplicate(ah, tmp_path):
    """9절: 중복 where = bias_inputs[i] -- i 는 그 넷이 놓인 위치 중 하나(계약이 첫/둘째 중 어느 쪽인지 정하지 않음)."""
    detail = load_rejected(ah, tmp_path, with_gate_only(ah, ["n_gb", "n_gb"]))
    assert ah.rules(detail["hits"]) == ["bias_input_duplicate"]
    assert detail["hits"][0].elements == ("n_gb",)
    assert detail["hits"][0].where in ("bias_inputs[0]", "bias_inputs[1]")


@pytest.mark.parametrize("value", ["n_gb", {"n_gb": 1}, None, 3], ids=["str", "object", "null", "int"])
def test_bias_inputs_type(ah, tmp_path, value):
    """9절(78ebbbd 보강): null·list 아닌 값은 bias_inputs_type 하나만(gate_only_undeclared 동반 없음), where = bias_inputs.
    문서에 gate 전용 넷 n_gb 가 있어도 선언 집합이 없으므로 미선언 hit 가 따라오지 않는다."""
    doc = with_gate_only(ah, value)
    assert "bias_inputs" in doc and doc["bias_inputs"] == value      # null 이 실제로 JSON 에 쓰인다
    detail = load_rejected(ah, tmp_path, doc)
    assert [(h.rule, h.where) for h in detail["hits"]] == [("bias_inputs_type", GATE)], detail["hits"]
    assert detail["rejected_gates"] == (GATE,)


def test_bias_inputs_type_null_without_gate_only_nets(ah, tmp_path):
    """gate 전용 넷이 없는 문서에서도 null 은 키 없음과 다르다 -> bias_inputs_type."""
    doc = ah.base()
    doc["bias_inputs"] = None
    detail = load_rejected(ah, tmp_path, doc)
    assert ah.rules(detail["hits"]) == ["bias_inputs_type"]


@pytest.mark.parametrize("entry", ["", 3, None, ["n_gb"]], ids=["empty", "int", "null", "list"])
def test_bias_input_entry(ah, tmp_path, entry):
    """9절: 형식 위반 where = bias_inputs[i] (i = 문서 안 위치, 여기서는 1)."""
    detail = load_rejected(ah, tmp_path, with_gate_only(ah, ["n_gb", entry]))
    assert [(h.rule, h.where) for h in detail["hits"]] == [("bias_input_entry", "bias_inputs[1]")], detail["hits"]
    assert detail["rejected_gates"] == (GATE,)


def test_bias_input_entry_where_index_follows_position(ah, tmp_path):
    detail = load_rejected(ah, tmp_path, with_gate_only(ah, ["", "n_gb", 7]))
    assert [(h.rule, h.where) for h in detail["hits"]] == [
        ("bias_input_entry", "bias_inputs[0]"), ("bias_input_entry", "bias_inputs[2]")], detail["hits"]


def test_set_violation_where_is_key(ah, tmp_path):
    """9절: 집합 위반(gate_only_undeclared·bias_input_not_gate_only)의 where = bias_inputs."""
    d1 = load_rejected(ah, tmp_path, with_gate_only(ah))
    d2 = load_rejected(ah, tmp_path, with_gate_only(ah, ["n_gb", "n_ghost"]))
    assert [(h.rule, h.where) for h in d1["hits"] + d2["hits"]] == [
        ("gate_only_undeclared", GATE), ("bias_input_not_gate_only", GATE)]


def test_entry_and_duplicate_cooccur_with_set_violations(ah, tmp_path):
    """9절: entry·duplicate 는 gate_only_undeclared·bias_input_not_gate_only 와 한 번에 같이 나온다(예외 1개).
    선언 ["", "rail_hi", "rail_hi"]: [0] 형식, rail_hi 중복, rail_hi gate 전용 아님, n_gb 미선언."""
    detail = load_rejected(ah, tmp_path, with_gate_only(ah, ["", "rail_hi", "rail_hi"]))
    got = {(h.rule, h.elements) for h in detail["hits"]}
    assert ("gate_only_undeclared", ("n_gb",)) in got
    assert ("bias_input_not_gate_only", ("rail_hi",)) in got
    assert ("bias_input_duplicate", ("rail_hi",)) in got
    assert {h.rule for h in detail["hits"]} == {
        "gate_only_undeclared", "bias_input_not_gate_only", "bias_input_duplicate", "bias_input_entry"}
    entry = [h for h in detail["hits"] if h.rule == "bias_input_entry"]
    assert [h.where for h in entry] == ["bias_inputs[0]"]
    dup = [h for h in detail["hits"] if h.rule == "bias_input_duplicate"]
    assert [h.where for h in dup][0] in ("bias_inputs[1]", "bias_inputs[2]")
    assert detail["rejected_gates"] == (GATE,)


def test_public_export():
    """9절: 공개 이름 bias_input_declaration 이 gmid_engine.authoring.__all__ 에 있고 호출 가능하다."""
    assert "bias_input_declaration" in authoring.__all__
    assert callable(authoring.bias_input_declaration)


# ---------------------------------------------------------------------------------------------------- 건너뛰기
def test_skipped_when_ports_rejected(ah, tmp_path):
    """포트 선언이 거부되면 bias_inputs 검사는 돌지 않는다 -- gate 전용 넷이 미선언이어도 그 hit 가 없다(9절)."""
    doc = with_gate_only(ah)
    doc["ports"]["n_inp"]["direction"] = "sideways"
    detail = load_rejected(ah, tmp_path, doc)
    assert "gate_only_undeclared" not in ah.rules(detail["hits"])
    assert GATE not in detail["rejected_gates"]
    assert set(detail["not_evaluated"]) <= NOT_EVALUATED_NAMES


def test_skipped_when_devices_rejected(ah, tmp_path):
    doc = with_gate_only(ah, ["rail_hi"])
    doc["netlist"][0]["n_fingers"] = 4                 # element_unknown_key (3.4)
    detail = load_rejected(ah, tmp_path, doc)
    assert not bias_hits(detail)
    assert GATE not in detail["rejected_gates"]
    assert set(detail["not_evaluated"]) <= NOT_EVALUATED_NAMES


def test_runs_alongside_other_passing_gates_only(ah, tmp_path):
    """다른 선언이 모두 통과한 문서에서는 gate 전용 위반 하나만 -- 다른 게이트를 건드리지 않는다."""
    detail = load_rejected(ah, tmp_path, with_gate_only(ah, ["n_gb", "n_mid"]))
    assert detail["rejected_gates"] == (GATE,)


# ---------------------------------------------------------------------------------------------------- 지문
def test_bias_inputs_not_in_connectivity_fp(ah, tmp_path):
    """같은 연결을 bias_inputs 없이 만든 TopologyDoc 과 지문이 같다(9절 'connectivity_fp 에 넣지 않는다').
    비교 대상은 공개 생성자 from_declarations(2절)로 같은 선언에서 bias_inputs 만 () 로 둔 것."""
    td = load_topology(ah.write(tmp_path, with_gate_only(ah, ["n_gb"])))
    bare = TopologyDoc.from_declarations(td.name, td.devices, td.passives, td.sources, td.rails, td.ports,
                                         td.file_sha256)
    assert bare.bias_inputs == ()
    assert bare.connectivity_fp == td.connectivity_fp
    other = TopologyDoc.from_declarations(td.name, td.devices, td.passives, td.sources, td.rails, td.ports,
                                          td.file_sha256, bias_inputs=("zz_other",))
    assert other.connectivity_fp == td.connectivity_fp


def test_empty_vs_absent_key_same_fp(ah, tmp_path):
    base = ah.base()
    a = load_topology(ah.write(tmp_path, base, "a"))
    base["bias_inputs"] = []
    b = load_topology(ah.write(tmp_path, base, "b"))
    assert a.connectivity_fp == b.connectivity_fp
    assert a.file_sha256 != b.file_sha256
