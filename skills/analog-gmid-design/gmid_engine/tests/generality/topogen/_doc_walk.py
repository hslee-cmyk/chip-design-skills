"""topology JSON(dict) 공용 순회 -- 넷·원소 이름을 한 곳에서 바꾼다(여러 변형기가 같은 위치 목록을 쓴다).

위치 목록의 근거는 authoring CONTRACT 3.4~3.9·9절(엔진 소스 아님): netlist 원소 drain·gate·source·bulk, 2단자 원소
(passive_elements·ideal_sources) terminals, supply_nets, ports 의 키(`_` 접두 키는 포트가 아니다), `bias_inputs` 원소
(9절, 2026-10-08 -- 문자열 원소만 바꾸고 형식 위반 원소는 그대로 둔다).
태그 키(device_roles 등)와 `_` 주석 키는 건드리지 않는다 -- 로더가 읽지 않는다(CONTRACT 머리).
"""
from __future__ import annotations

MOS_NET_KEYS = ("drain", "gate", "source", "bulk")
ELEMENT_LISTS = ("netlist", "passive_elements", "ideal_sources")
TWO_TERMINAL_LISTS = ("passive_elements", "ideal_sources")
COMMENT_PREFIX = "_"
BIAS_INPUTS_KEY = "bias_inputs"     # CONTRACT 9절 gate 전용 바이어스 넷 선언(넷 이름 list)


def map_nets(doc, fn):
    """넷 이름이 놓이는 모든 자리에 fn 을 적용한 새 doc(입력은 바꾸지 않는다). 포트 키 순서는 유지한다."""
    out = dict(doc)
    out["netlist"] = [{k: (fn(v) if k in MOS_NET_KEYS else v) for k, v in e.items()} for e in doc.get("netlist", [])]
    for key in TWO_TERMINAL_LISTS:
        if key in doc:
            out[key] = [{k: ([fn(t) for t in v] if k == "terminals" else v) for k, v in e.items()} for e in doc[key]]
    out["supply_nets"] = [fn(n) for n in doc.get("supply_nets", [])]
    out["ports"] = {(k if k.startswith(COMMENT_PREFIX) else fn(k)): dict(v) if isinstance(v, dict) else v
                    for k, v in doc.get("ports", {}).items()}
    if isinstance(doc.get(BIAS_INPUTS_KEY), list):
        out[BIAS_INPUTS_KEY] = [fn(n) if isinstance(n, str) else n for n in doc[BIAS_INPUTS_KEY]]
    return out


def map_element_names(doc, fn):
    """원소(netlist·수동·이상원) 이름에 fn 을 적용한 새 doc."""
    out = dict(doc)
    for key in ELEMENT_LISTS:
        if key in doc:
            out[key] = [{k: (fn(v) if k == "name" else v) for k, v in e.items()} for e in doc[key]]
    return out


def collect_names(doc):
    """(원소 이름 집합, 넷 이름 집합). 넷 = MOS 단자·2단자 terminals·supply_nets·포트 키."""
    elements, nets = set(), set()
    for key in ELEMENT_LISTS:
        for e in doc.get(key, []):
            elements.add(e["name"])
            if key == "netlist":
                nets.update(e[k] for k in MOS_NET_KEYS if k in e)
            else:
                nets.update(e["terminals"])
    nets.update(doc.get("supply_nets", []))
    nets.update(k for k in doc.get("ports", {}) if not k.startswith(COMMENT_PREFIX))
    return elements, nets
