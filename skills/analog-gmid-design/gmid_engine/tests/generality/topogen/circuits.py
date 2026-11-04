"""library 밖 합성 topology 4종(손으로 만든 소형 회로). 형식은 authoring CONTRACT 3.2~3.9 의 받는 키만 쓴다.

| 이름 | 회로 | 원소 |
|---|---|---|
| syn_cs_load | 공통 소스 + PMOS 전류원 부하(다이오드 미러 바이어스) | MOS 3, C 1, 전류원 1 |
| syn_diffpair5 | 5T OTA(차동쌍 + 미러 부하 + 꼬리 전류원) | MOS 6, 수동 0(`[]`), 전류원 1 |
| syn_follower | 소스 팔로워(NMOS) + 전류원 바이어스 + R·C 부하 | MOS 3, R 1, C 1, 전류원 1 |
| syn_cascode | 텔레스코픽 캐스코드 공통 소스(NMOS CS + CG, PMOS 캐스코드 부하) + 전압원 바이어스 3 | MOS 4, 수동 0, 전압원 3 |

모든 회로는 레일 2개(`qp_hi`, `qp_lo`)라 극성 뒤집기(polarity.py)가 정의된다. 이름은 library 이름 집합과
겹치지 않는다(test_generator_sanity 가 확인). 넷 이름은 글자로 시작한다(`_` 로 시작하면 포트가 아니다).
같은 생성기를 S1 그래프·구조 유도 test 가 그대로 쓴다(README).
"""
from __future__ import annotations

SCHEMA_VERSION = "2.0"          # authoring CONTRACT 3.2 schema_version
RAIL_HI, RAIL_LO = "qp_hi", "qp_lo"


def _mos(name, kind, d, g, s, bulk=None):
    e = {"name": name, "kind": kind, "drain": d, "gate": g, "source": s}
    if bulk is not None:
        e["bulk"] = bulk
    return e


def _two(name, kind, a, b, value_key, value):
    return {"name": name, "kind": kind, "terminals": [a, b], value_key: value}


def _doc(name, netlist, passives, sources, ports):
    return {
        "schema_version": SCHEMA_VERSION,
        "topology_name": name,
        "source": "generality test generator (not a library circuit)",
        "supply_nets": [RAIL_HI, RAIL_LO],
        "netlist": netlist,
        "passive_elements": passives,
        "ideal_sources": sources,
        "ports": {net: {"direction": direction, "role": role} for net, direction, role in ports},
    }


def _cs_load():
    return _doc("syn_cs_load", [
        _mos("Xamp", "nmos", "cs_out", "cs_in", RAIL_LO),
        _mos("Xload", "pmos", "cs_out", "cs_pb", RAIL_HI, bulk=RAIL_HI),
        _mos("Xref", "pmos", "cs_pb", "cs_pb", RAIL_HI),
    ], [
        _two("Ccs", "capacitor", "cs_out", RAIL_LO, "value_farad", 2e-12),
    ], [
        _two("Ics", "current_source", "cs_pb", RAIL_LO, "value_amp", 2e-5),
    ], [
        ("cs_in", "input", "single_ended_input"),
        ("cs_out", "output", "single_ended_output"),
    ])


def _diffpair5():
    return _doc("syn_diffpair5", [
        _mos("Ya", "nmos", "dp_x", "dp_ip", "dp_t"),
        _mos("Yb", "nmos", "dp_o", "dp_im", "dp_t"),
        _mos("Yc", "pmos", "dp_x", "dp_x", RAIL_HI),
        _mos("Yd", "pmos", "dp_o", "dp_x", RAIL_HI),
        _mos("Ye", "nmos", "dp_t", "dp_bn", RAIL_LO),
        _mos("Yf", "nmos", "dp_bn", "dp_bn", RAIL_LO),
    ], [], [
        _two("Idp", "current_source", RAIL_HI, "dp_bn", "value_amp", 1e-5),
    ], [
        ("dp_ip", "input", "differential_input_p"),            # [IT-1 DEC-106] 입력 점 규칙의 차동쌍 role(옛 noninverting/inverting 은 차동쌍 아님)
        ("dp_im", "input", "differential_input_n"),
        ("dp_o", "output", "single_ended_output"),
    ])


def _follower():
    return _doc("syn_follower", [
        _mos("Za", "nmos", RAIL_HI, "sf_in", "sf_out"),
        _mos("Zb", "nmos", "sf_out", "sf_bn", RAIL_LO),
        _mos("Zc", "nmos", "sf_bn", "sf_bn", RAIL_LO),
    ], [
        _two("Rsf", "resistor", "sf_out", RAIL_LO, "value_ohm", 5e4),
        _two("Csf", "capacitor", "sf_out", RAIL_LO, "value_farad", 1e-12),
    ], [
        _two("Isf", "current_source", RAIL_HI, "sf_bn", "value_amp", 1e-5),
    ], [
        ("sf_in", "input", "single_ended_input"),
        ("sf_out", "output", "single_ended_output"),
    ])


def _cascode():
    return _doc("syn_cascode", [
        _mos("Wa", "nmos", "cc_x", "cc_in", RAIL_LO),
        _mos("Wb", "nmos", "cc_out", "cc_vbn", "cc_x"),
        _mos("Wc", "pmos", "cc_out", "cc_vbp", "cc_y", bulk=RAIL_HI),
        _mos("Wd", "pmos", "cc_y", "cc_vbq", RAIL_HI),
    ], [], [
        _two("Vbn", "voltage_source", "cc_vbn", RAIL_LO, "value_volt", 0.9),
        _two("Vbp", "voltage_source", RAIL_HI, "cc_vbp", "value_volt", 0.7),
        _two("Vbq", "voltage_source", RAIL_HI, "cc_vbq", "value_volt", 0.4),
    ], [
        ("cc_in", "input", "single_ended_input"),
        ("cc_out", "output", "single_ended_output"),
    ])


def synthetic_topologies():
    """{회로 이름: topology dict} -- 부를 때마다 새 객체(호출자가 고쳐도 다음 호출에 새지 않는다)."""
    docs = (_cs_load(), _diffpair5(), _follower(), _cascode())
    return {d["topology_name"]: d for d in docs}
