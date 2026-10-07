"""위반 주입: 로드가 통과하는 doc 에 위반 하나를 넣고, 계약이 정한 기대 hit 을 함께 돌려준다(피검 함수로 만들지 않는다).

기대 hit = (rule, 반드시 들어 있어야 할 elements 집합, elements 가 정확히 그 집합인가). 근거는 authoring CONTRACT:
| kind | 주입 | rule | elements |
|---|---|---|---|
| hidden_rail | 출력 포트 넷과 새 넷 사이 커패시터 | `hidden_rail`(3.11) | 정확히 {새 넷, 커패시터}(3.11 "elements = 넷 + 그 넷을 쓰는 2단자 원소") |
| rail_not_connected | supply_nets 에 아무 데도 없는 새 넷 | `rail_not_connected`(3.11) | 새 넷 포함 |
| name_duplicate | 둘째 소자 이름 = 첫째 소자 이름 | `name_duplicate`(3.8) | 그 이름 포함 |
| name_case_collision | 둘째 소자 이름 = 첫째 이름의 대소문자만 바꾼 것 | `name_case_collision`(3.8) | 정확히 두 이름(3.8 "elements = 그 이름들") |
| port_net_unknown | 어느 단자에도 없는 새 넷을 입력 포트로 | `port_net_unknown`(3.9) | 새 넷 포함 |
| port_on_rail | 레일 넷(이름순 첫째)을 입력 포트로 | `port_on_rail`(3.9) | 그 레일 포함 |
| element_unknown_key | 첫 netlist 원소에 `n_fingers` | `element_unknown_key`(3.4) | 조건 없음 |
'첫째'·'둘째'는 문서 순서다 -- 이름이 아니라 위치로 고르므로 이름 치환·순서 섞기와 무관하게 같은 종류의 위반이 들어간다.
"""
from __future__ import annotations

from ._doc_walk import collect_names

KINDS = ("hidden_rail", "rail_not_connected", "name_duplicate", "name_case_collision",
         "port_net_unknown", "port_on_rail", "element_unknown_key")


def _fresh(doc, stem):
    elements, nets = collect_names(doc)
    taken = {x.casefold() for x in elements | nets}
    k = 0
    while (stem + str(k)).casefold() in taken:
        k += 1
    return stem + str(k)


def _other_case(name):
    flipped = name.swapcase()
    if flipped == name:
        raise ValueError("대소문자로 바꿀 글자가 없는 이름: %r" % name)
    return flipped


def inject_violation(doc, kind):
    """(새 doc, (rule, elements frozenset, 정확히 일치 여부))."""
    out = dict(doc)
    out["netlist"] = [dict(e) for e in doc["netlist"]]
    out["ports"] = dict(doc["ports"])
    if kind == "hidden_rail":
        net, cap = _fresh(doc, "zfloat"), _fresh(doc, "Czinj")
        outputs = sorted(k for k, v in doc["ports"].items() if isinstance(v, dict) and v.get("direction") == "output")
        out["passive_elements"] = list(doc.get("passive_elements", [])) + [
            {"name": cap, "kind": "capacitor", "terminals": [outputs[0], net], "value_farad": 1e-13}]
        return out, ("hidden_rail", frozenset((net, cap)), True)
    if kind == "rail_not_connected":
        net = _fresh(doc, "zrail")
        out["supply_nets"] = list(doc["supply_nets"]) + [net]
        return out, ("rail_not_connected", frozenset((net,)), False)
    if kind == "name_duplicate":
        name = out["netlist"][0]["name"]
        out["netlist"][1]["name"] = name
        return out, ("name_duplicate", frozenset((name,)), False)
    if kind == "name_case_collision":
        name = out["netlist"][0]["name"]
        other = _other_case(name)
        out["netlist"][1]["name"] = other
        return out, ("name_case_collision", frozenset((name, other)), True)
    if kind == "port_net_unknown":
        net = _fresh(doc, "zport")
        out["ports"][net] = {"direction": "input", "role": "extra_input"}
        return out, ("port_net_unknown", frozenset((net,)), False)
    if kind == "port_on_rail":
        rail = sorted(doc["supply_nets"])[0]
        out["ports"][rail] = {"direction": "input", "role": "extra_input"}
        return out, ("port_on_rail", frozenset((rail,)), False)
    if kind == "element_unknown_key":
        out["netlist"][0]["n_fingers"] = 4
        return out, ("element_unknown_key", frozenset(), False)
    raise ValueError("모르는 위반 종류: %r" % kind)
