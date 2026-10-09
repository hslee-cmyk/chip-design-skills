"""ngcc_3stage_ff 실제 구조(S1v -> metric_structure) 위에 **합성 소신호 값**을 얹은 손 회로 (U7 test 입력 생성기).

* 구조: library topology `ngcc_3stage_ff` 를 graph test helper(`tests/graph/s1v_hand.build_lib`)로 단계 A 까지 만든 S1v.
  기대 구조 사실의 출처는 설계 41 §1.13·40 §3.2-3 사실 표(FF1 = {M6B, M7}·load M6A·bias M5, 탭 ND, merge Vout; FF2 = {M14}, 탭 V1,
  merge Vout; 주경로 V1 -> V2 -> Vout) -- `tests/graph/test_feedforward_cells.py` docstring 의 oracle (d) 와 같다.
* 소신호 값: LUT 없이 손으로 정한 gm·gds(test 입력, 기준값 아님). 바디 = 기본 규칙(NMOS gnd, PMOS vdd). 교류접지 = 레일 ∪ bias 입력.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

GRAPH_TESTS = Path(__file__).resolve().parents[1] / "graph"
if str(GRAPH_TESTS) not in sys.path:                                # 손 회로 helper(s1v_hand) 재사용 -- tests/pipeline/conftest 와 같은 방식
    sys.path.insert(0, str(GRAPH_TESTS))

import s1v_hand  # noqa: E402

from . import u7_hand as H  # noqa: E402

LIB = Path(__file__).resolve().parents[3] / "assets" / "library"
NAME = "ngcc_3stage_ff"

# (gm, gds) -- 합성 값. M1·M2 대칭, 미러 M3/M4 대칭.
VALUES = {
    "M0": (4e-4, 1e-6), "M1": (5e-4, 5e-6), "M2": (5e-4, 5e-6), "M3": (4e-4, 4e-6), "M4": (4e-4, 4e-6),
    "M5": (3e-4, 3e-6), "M6A": (2e-4, 2e-6), "M6B": (2.6e-4, 2.5e-6), "M7": (7e-4, 7e-6),
    "M8": (6e-4, 6e-6), "M9": (3e-4, 3e-6), "M10": (3.3e-4, 3.5e-6), "M11": (2e-4, 2e-6),
    "M12": (9e-4, 9e-6), "M13": (2e-3, 2e-5), "M14": (1.5e-3, 1.8e-5),
}


def topology():
    return json.loads((LIB / (NAME + ".topology.json")).read_text(encoding="utf-8"))


def s1v():
    _s1, v = s1v_hand.build_lib(NAME)
    return v


def hand_circuit(values=None, gds_scale=1.0):
    values = dict(VALUES, **(values or {}))
    doc = topology()
    nets = set(doc["supply_nets"]) | set(doc.get("bias_inputs") or ())
    rows = []
    for e in doc["netlist"]:
        gm, gds = values[e["name"]]
        body = "gnd" if e["kind"] == "nmos" else "vdd"
        rows.append(H.mos(e["name"], e["drain"], e["gate"], e["source"], body, gm, gds * gds_scale))
        nets |= {e["drain"], e["gate"], e["source"]}
    ground = tuple(doc["supply_nets"]) + tuple(doc.get("bias_inputs") or ())
    inputs = tuple(n for n, p in doc["ports"].items() if p["direction"] == "input")
    nets = tuple(sorted(nets))
    return nets, tuple(rows), (), ground, inputs


def view():
    return H.transfer({"Vinp": 0.5, "Vinn": -0.5}, "Vout")


# ---------------------------------------------------------------- library 9회로 일반화 측정용(이름 없는 합성 값 규칙)

def library_case(name):
    """library 회로 하나 -> (SsCircuit, ViewStruct tuple, 뷰 선언 tuple). 합성 값: k 번째 MOS gm = 1e-4·(1 + 7k mod 11), gds = gm/(40 + 13k mod 37),
    gmb = 0.1·gm, 바디 = 최저/최고 레일(기본 규칙), 저항 = 1e4·(1 + i) Ω, 용량·이상 전류원은 DC 에서 열림. 교류접지 = 레일 ∪ bias 입력."""
    from gmid_engine.metrics import MosSmallSignal, Resistor, SmallSignalCircuit, SsCircuit, metric_structure
    doc = json.loads((LIB / (name + ".topology.json")).read_text(encoding="utf-8"))
    rails = list(doc["supply_nets"])
    bias = list(doc.get("bias_inputs") or ())
    nets = set(rails) | set(bias)
    for e in doc["netlist"]:
        nets |= {e["drain"], e["gate"], e["source"]}
    for e in list(doc.get("passive_elements") or ()) + list(doc.get("ideal_sources") or ()):
        nets |= set(e["terminals"])
    nets = tuple(sorted(nets))
    idx = {n: i for i, n in enumerate(nets)}
    supplies = s1v_hand.lib_supplies(name)
    lo_rail = min((r for r in rails if r in supplies), key=lambda r: supplies[r])
    hi_rail = max((r for r in rails if r in supplies), key=lambda r: supplies[r])
    mos = []
    for k, e in enumerate(doc["netlist"]):
        gm = 1e-4 * (1 + (k * 7) % 11)
        body = lo_rail if e["kind"] == "nmos" else hi_rail
        mos.append(MosSmallSignal(idx[e["drain"]], idx[e["gate"]], idx[e["source"]], idx[body], gm, 0.1 * gm, gm / (40 + (k * 13) % 37),
                                  label=e["name"]))
    res = [Resistor(idx[e["terminals"][0]], idx[e["terminals"][1]], 1e4 * (1 + i), label=e["name"])
           for i, e in enumerate(doc.get("passive_elements") or ()) if e["kind"] == "resistor"]
    inputs = tuple(sorted(n for n, q in doc["ports"].items() if isinstance(q, dict) and q.get("direction") == "input"))
    ss = SsCircuit(nets, SmallSignalCircuit(mos=tuple(mos), resistors=tuple(res)), tuple(r.label for r in res), (),
                   tuple(sorted(set(rails) | set(bias))), inputs)
    _s1, s1v_ = s1v_hand.build_lib(name)
    views = metric_structure(s1v_).views
    decls = tuple(H.transfer(dict(v.excite), v.sense[0], v.sense[1] if len(v.sense) > 1 else None) for v in views)
    return ss, views, decls
