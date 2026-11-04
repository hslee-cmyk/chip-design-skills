"""graph/s1_symmetry.py -- 대칭 블록 `s1_symmetry(snapshot, supplies, marks)` (graph CONTRACT 4.8, 설계 40 v1.8 §6-5·§6-7·§6-8, §2.4.8 `graph/s1: orbits,
current_symmetry`, 사용자 결정 2026-10-12 "6. 가"·D-1~D-3).

[U17 ①-d] 삭제된 원본 `sizing/struct_colour.py`(`dc_struct_colour`)의 test(`tests/sizing/test_struct_colour.py`)를 새 원본으로 옮겼다(규칙 H).
옮기면서 바뀐 것(design 이 폐기한 동작만):
- 블록 입구: sizing 커널 컨텍스트가 아니라 `build_s1(doc, supplies, marks=SymmetryMarks)` 의 마지막 블록(D-2 그래프 하나, S1 하나에서 정한다).
  선언 표시는 test 가 계약 4.8 형식(`SymmetryMarks(input_dc_v, elements, targets)`, 레일 전위는 supplies 에서)으로 손으로 만든다.
- 필드 이름: `node.dc_orbit`·`device.dc_orbit`·`graph.dc_symmetry` -> `graph/s1: orbits`(`Orbits(devices, nodes)`)·`current_symmetry`(`CurrentSigns`).
- 1-WL 색 `wl` 은 선언 표시를 넣은 같은 그래프에서 정한다(§6-8 D-2) -- 색 계약의 '1-WL 색' 은 표시를 넣은 독립 1-WL(`canon_graphs.wl_classes`) 분할로 본다.
- MOS d·s = 같은 라벨 c(§6-8 D-2·D-3): d/s 표기 뒤집기 metamorphic, d/s 맞바꿈 전류 부호 −1, 자기 맞바꿈 정지(`ds_self_swap_zero_current`).
oracle: (a) 손 회로의 구성 자기동형·손 부호 유도, (b) 독립 1-WL(`canon_graphs.labeled_graph`·`wl_classes`), (d) 사용자 결정(대칭 묶음 방식 b, 6. 가).
graph `.py` 소스는 기대값에 쓰지 않는다.
"""
from __future__ import annotations

import json
import random

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import StructureUnresolvedError, exit_code_for
from gmid_engine.graph import (GRAPH_KEY, NO_MARKS, CurrentSigns, Orbits, SymmetryMarks, build_s1, s1_symmetry,
                               supplies_declaration)

import s1v_hand as H
from canon_graphs import Circuit, labeled_graph, partition, wl_classes

NINE = ("common_gate_amplifier", "current_reuse_telescopic_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
        "pushpull_follower_buffer", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf")
SUP = {"vdd": 1.8, "gnd": 0.0}


# ---------------------------------------------------------------- 입력 만들기(기대값 아님)

def mos(name, kind, d, g, s):
    return (name, kind, d, g, s)


def build(tmp_path, doc, marks=NO_MARKS, supplies=None, stem=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    sv = supplies or {r: SUP.get(r, 0.9) for r in doc["supply_nets"]}
    return build_s1(H.load(tmp_path, doc, stem), sv, marks=marks, **H.fresh_run())      # [XRUN-F1 card B C6] 새 실행 하나


def lib_doc(name):
    return json.loads((H.LIBRARY / (name + ".topology.json")).read_text(encoding="utf-8"))


def build_lib(tmp_path, doc, name, marks=NO_MARKS, supplies=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    return build_s1(H.load(tmp_path, doc), supplies or H.lib_supplies(name), marks=marks, **H.fresh_run())


def element_marks(values=(), engine=(), linear=()):
    """계약 4.8 / 40 §6-8 형식: ((원소, ((표시, 수), ...)), ...) 원소 이름순, 표시 이름순."""
    table = {}
    for name, v in values:
        table.setdefault(name, []).append(("value", float(v)))
    for name in engine:
        table.setdefault(name, []).append(("engine", 0.0))
    for name in linear:
        table.setdefault(name, []).append(("linear", 0.0))
    return tuple((n, tuple(sorted(m))) for n, m in sorted(table.items()))


def orbits(s1):
    o = s1.value("graph", GRAPH_KEY, "orbits")
    return dict(o.nodes), dict(o.devices)


def colours(s1):
    return dict(s1.column("node", "dc_colour")), dict(s1.column("device", "dc_colour"))


def signs(s1):
    return s1.value("graph", GRAPH_KEY, "current_symmetry").generators


def oracle_graph(s1, supplies, marks=NO_MARKS):
    """S1 구조 필드(입력 사실)에서 4.8 그래프를 독립으로 다시 만든다: 노드 표시 = 레일 전위·노드 목표·입력 DC, 원소 표시 = marks.elements."""
    classes = dict(s1.column("device", "element_class"))
    kinds = dict(s1.column("device", "kind"))
    pins = {n: dict(p) for n, p in s1.column("device", "pins")}
    diode = dict(s1.column("device", "is_diode"))
    bulk = {n: getattr(b, "net", None) for n, b in s1.column("device", "bulk")}
    rails = {n for n, f in s1.column("node", "is_rail") if f}
    ports = {n: d for n, d in s1.column("node", "port_direction") if d}
    nets = [n for n, _ in s1.column("node", "is_rail")]
    els = [(n, classes[n], kinds[n], pins[n], bool(diode.get(n)), bulk.get(n) if classes[n] == "mos" else None) for n in sorted(classes)]
    node = {}
    for net, v in supplies.items():
        node.setdefault(net, []).append(("rail_v", float(v)))
    for net, v in marks.targets:
        node.setdefault(net, []).append(("target_v", float(v)))
    if marks.input_dc_v is not None:
        for net, d in ports.items():
            if d == "input":
                node.setdefault(net, []).append(("input_dc_v", float(marks.input_dc_v)))
    nm = tuple((n, tuple(sorted(m))) for n, m in sorted(node.items()))
    return labeled_graph(Circuit(els, rails, ports, nets), marks.elements, nm)


def check_colour_contract(s1, supplies, marks=NO_MARKS):
    nc, ec = colours(s1)
    assert set(nc) == {n for n, _ in s1.column("node", "is_rail")} and set(ec) == {n for n, _ in s1.column("device", "kind")}
    allv = list(nc.values()) + list(ec.values())
    assert all(isinstance(v, int) and not isinstance(v, bool) for v in allv)
    assert sorted(allv) == list(range(len(allv)))                          # 정점마다 다른 정수
    col, nb = oracle_graph(s1, supplies, marks)
    wl = wl_classes(col, nb)                                               # 독립 1-WL(표시를 넣은 같은 그래프, D-2)
    on, oe = orbits(s1)
    o = {("n", k): v for k, v in on.items()} | {("e", k): v for k, v in oe.items()}
    assert set(o) == set(col)
    groups = {}
    for v, g in o.items():
        groups.setdefault(g, set()).add(wl[v])
    assert all(len(g) == 1 for g in groups.values())                       # 궤도 ⊆ 1-WL 클래스(CONTRACT 4.7 (h), §6-8)
    # 같은 1-WL 클래스는 dc_colour 에서 연속 구간이다(서로 다른 1-WL 색 사이 순서 = wl 순서 -- 클래스가 섞이지 않는다)
    dc = {("n", k): v for k, v in nc.items()} | {("e", k): v for k, v in ec.items()}
    by_class = {}
    for v, c in dc.items():
        by_class.setdefault(wl[v], []).append(c)
    spans = sorted((min(cs), max(cs), len(cs)) for cs in by_class.values())
    assert all(hi - lo + 1 == n for lo, hi, n in spans)
    assert all(a[1] < b[0] for a, b in zip(spans, spans[1:]))


# ---------------------------------------------------------------- 블록 선언·필드(CONTRACT 4.8, 40 §2.4.8)

def test_block_declaration():
    assert s1_symmetry.name == "s1_symmetry"
    assert set(s1_symmetry.writes) == {("node", "dc_colour"), ("device", "dc_colour"), ("graph", "orbits"), ("graph", "current_symmetry")}
    assert set(s1_symmetry.reads) == {("device", "bulk"), ("device", "element_class"), ("device", "is_diode"), ("device", "kind"),
                                      ("device", "pins"), ("node", "is_rail"), ("node", "port_direction"), ("node", "port_role"), ("graph", "dc_pruned")}


@pytest.mark.parametrize("name", NINE)
def test_library_fields_and_colour_contract(name, tmp_path):
    s1 = build_lib(tmp_path, lib_doc(name), name)
    assert isinstance(s1.value("graph", GRAPH_KEY, "orbits"), Orbits)
    assert isinstance(s1.value("graph", GRAPH_KEY, "current_symmetry"), CurrentSigns)
    sv = dict(supplies_declaration(H.lib_supplies(name), load_topology(str(H.LIBRARY / (name + ".topology.json"))).rails))
    check_colour_contract(s1, sv)
    for f in ("dc_colour",):
        k = s1.snapshot.keys("device")[0]
        assert s1.snapshot.field("device", k, f).writer == "s1_symmetry"
    assert s1.snapshot.field("graph", GRAPH_KEY, "orbits").writer == "s1_symmetry"


# ---------------------------------------------------------------- 손 회로 궤도(옛 test_struct_colour 옮김)

def sym_doc(name="hand_sym", o2_port=True, caps=False):
    ports = {"inp": H.DIFF_P, "inn": H.DIFF_N, "o1": H.OUT_P, "o2": H.OUT_N}
    if not o2_port:
        del ports["o2"]
    return H.topo(name, (mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"), mos("M5", "nmos", "t", "vb", "gnd"),
                         mos("M3", "pmos", "o1", "pb", "vdd"), mos("M4", "pmos", "o2", "pb", "vdd")),
                  ports, passives=(("CL1", "capacitor", ("o1", "gnd")), ("CL2", "capacitor", ("o2", "gnd"))) if caps else (),
                  bias=("pb", "vb"))


def test_symmetric_pair_same_orbit_and_port_separates(tmp_path):
    """(a) 구성 자기동형 (M1 M2)(M3 M4)(inp inn)(o1 o2) -> 같은 궤도, M5 고정. o2 를 포트에서 빼면 대칭이 깨져 궤도가 갈린다."""
    s1 = build(tmp_path, sym_doc())
    on, oe = orbits(s1)
    assert oe["M1"] == oe["M2"] and oe["M3"] == oe["M4"] and oe["M1"] != oe["M5"] and oe["M1"] != oe["M3"]
    assert on["inp"] == on["inn"] and on["o1"] == on["o2"] and on["t"] != on["o1"]
    check_colour_contract(s1, SUP)
    s2 = build(tmp_path, sym_doc("hand_sym2", o2_port=False))
    on2, oe2 = orbits(s2)
    assert on2["o1"] != on2["o2"] and oe2["M1"] != oe2["M2"] and oe2["M3"] != oe2["M4"]
    check_colour_contract(s2, SUP)


def test_declared_values_split_orbits(tmp_path):
    """40 §6-8 선언 표시: 같은 값 CL1·CL2 -> 같은 궤도, 다른 값 -> 다른 궤도(대칭 쌍 M1·M2 도 따라 갈린다)."""
    same_m = SymmetryMarks(None, element_marks((("CL1", 1e-12), ("CL2", 1e-12))), ())
    diff_m = SymmetryMarks(None, element_marks((("CL1", 1e-12), ("CL2", 2e-12))), ())
    same = build(tmp_path, sym_doc("hand_sym_c", caps=True), same_m)
    diff = build(tmp_path, sym_doc("hand_sym_c", caps=True), diff_m)
    so, do = orbits(same)[1], orbits(diff)[1]
    assert so["CL1"] == so["CL2"] and so["M1"] == so["M2"]
    assert do["CL1"] != do["CL2"] and do["M1"] != do["M2"]
    check_colour_contract(diff, SUP, diff_m)


def test_node_target_splits_orbits(tmp_path):
    eq_m, ne_m = SymmetryMarks(None, (), (("o1", 0.9), ("o2", 0.9))), SymmetryMarks(None, (), (("o1", 0.9), ("o2", 1.0)))
    eq, ne = build(tmp_path, sym_doc("hand_sym_t"), eq_m), build(tmp_path, sym_doc("hand_sym_t"), ne_m)
    assert orbits(eq)[1]["M1"] == orbits(eq)[1]["M2"] and orbits(eq)[0]["o1"] == orbits(eq)[0]["o2"]
    assert orbits(ne)[1]["M1"] != orbits(ne)[1]["M2"] and orbits(ne)[0]["o1"] != orbits(ne)[0]["o2"]
    check_colour_contract(ne, SUP, ne_m)


def test_input_dc_mark_keeps_input_symmetry(tmp_path):
    """입력 DC 표시는 모든 입력 포트에 같은 값 -> 입력쌍 대칭 유지."""
    m = SymmetryMarks(0.9, (), ())
    s1 = build(tmp_path, sym_doc("hand_sym_i"), m)
    assert orbits(s1)[1]["M1"] == orbits(s1)[1]["M2"]
    check_colour_contract(s1, SUP, m)


NET = (mos("M1", "nmos", "a", "in", "gnd"), mos("M2", "nmos", "b", "in", "gnd"), mos("M3", "pmos", "a", "pb", "vdd"), mos("M4", "pmos", "b", "pb", "vdd"))
PORTS = {"in": H.SE_IN, "a": H.SE_OUT, "b": H.SE_OUT}


def _with_source(name, a, b):
    d = H.topo(name, NET, PORTS, bias=("pb",))
    d["ideal_sources"] = [{"name": "I1", "kind": "current_source", "terminals": [a, b]}]
    return d


def test_current_source_direction_matters(tmp_path):
    """이상 전류원은 t0·t1 방향 라벨: a -> b 전류원은 a·b 를 구별. 커패시터(무향)는 a·b 같은 궤도."""
    cs = build(tmp_path, _with_source("hand_src_dir", "a", "b"))
    cc = build(tmp_path, H.topo("hand_cap_dir", NET, PORTS, passives=(("C1", "capacitor", ("a", "b")),), bias=("pb",)))
    check_colour_contract(cs, SUP)
    check_colour_contract(cc, SUP)
    assert orbits(cs)[0]["a"] != orbits(cs)[0]["b"]
    assert orbits(cc)[0]["a"] == orbits(cc)[0]["b"] and orbits(cc)[1]["M1"] == orbits(cc)[1]["M2"]


def test_b_dc_resistor_is_undirected(tmp_path):
    """[사용자 결정 '대칭 묶음 방식: b'] DC 저항 R1(a, b) 도 a·b 를 구별하지 않는다 -> a·b, M1·M2, M3·M4 같은 궤도."""
    s1 = build(tmp_path, H.topo("hand_res_dir", NET, PORTS, passives=(("R1", "resistor", ("a", "b")),), bias=("pb",)))
    on, oe = orbits(s1)
    assert on["a"] == on["b"] and oe["M1"] == oe["M2"] and oe["M3"] == oe["M4"]
    # 40 §6-7 전류 변수: a<->b 는 R1 의 단자 순서를 뒤집는다 -> R1 부호 −1(자기 자신으로, 손 유도)
    assert any(("R1", "R1", -1) in g for g in signs(s1))


def test_b_resistor_terminal_order_irrelevant(tmp_path):
    a = build(tmp_path, H.topo("hand_res_ab", NET, PORTS, passives=(("R1", "resistor", ("vdd", "a")), ("R2", "resistor", ("vdd", "b"))),
                               bias=("pb",)))
    b = build(tmp_path, H.topo("hand_res_ba", NET, PORTS, passives=(("R1", "resistor", ("vdd", "a")), ("R2", "resistor", ("b", "vdd"))),
                               bias=("pb",)))
    assert orbits(a)[1]["R1"] == orbits(a)[1]["R2"]
    assert orbits(b)[1]["R1"] == orbits(b)[1]["R2"] and orbits(b)[1]["M1"] == orbits(b)[1]["M2"]
    # 손 유도 부호: a 에서 R1 첫 단자 vdd -> R2 첫 단자 vdd(+1), b 에서 R2 첫 단자는 b(≠ vdd) -> −1
    assert any(("R1", "R2", 1) in g for g in signs(a))
    assert any(("R1", "R2", -1) in g for g in signs(b))


# ---------------------------------------------------------------- 이름 전단사·순서 섞기·결정론(옛 test_struct_colour 옮김)

def rename(doc, seed):
    d = json.loads(json.dumps(doc))
    nets = set(d["supply_nets"]) | {k for k in d["ports"] if not k.startswith("_")}
    for e in d["netlist"]:
        nets |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            nets |= set(e["terminals"])
    els = [e["name"] for e in d["netlist"]] + [e["name"] for k in ("passive_elements", "ideal_sources") for e in (d.get(k) or [])]
    rng = random.Random(seed)
    nl = sorted(nets)
    tn = ["n%03d_%d" % (i, seed) for i in range(len(nl))]
    rng.shuffle(tn)
    sn = dict(zip(nl, tn))
    te = ["E%03d_%d" % (i, seed) for i in range(len(els))]
    rng.shuffle(te)
    se = dict(zip(sorted(els), te))
    for e in d["netlist"]:
        e["name"] = se[e["name"]]
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                e[k] = sn[e[k]]
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            e["name"] = se[e["name"]]
            e["terminals"] = [sn[t] for t in e["terminals"]]
    d["supply_nets"] = [sn[n] for n in d["supply_nets"]]
    d["ports"] = {(k if k.startswith("_") else sn[k]): v for k, v in d["ports"].items()}
    for k in list(d):
        if k in ("device_roles", "symmetry", "sizing_roles", "compensation", "source_manifest") or (k.startswith("_") and k != "_comment"):
            d.pop(k)
    if "bias_inputs" in d:
        d["bias_inputs"] = [sn[n] for n in d["bias_inputs"]]
    d["topology_name"] = d["topology_name"] + "_r%d" % seed
    return d, sn, se


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("name", ["two_stage_ota", "folded_cascode", "current_reuse_telescopic_ota"])
def test_renaming_transports_orbits(name, seed, tmp_path):
    """이름 전단사 σ -> 궤도 id 가 σ 로 옮겨진다(궤도 id = 정준 위치 최솟값, 이름에 불변)."""
    raw = lib_doc(name)
    s1 = build_lib(tmp_path / "a", raw, name)
    d2, sn, se = rename(raw, seed)
    s2 = build_lib(tmp_path / "b", d2, name, supplies={sn[k]: v for k, v in H.lib_supplies(name).items()})
    on, oe = orbits(s1)
    on2, oe2 = orbits(s2)
    assert {sn[k]: v for k, v in on.items()} == on2
    assert {se[k]: v for k, v in oe.items()} == oe2


@pytest.mark.parametrize("seed", [1, 2])
def test_renaming_colours_equal_for_trivial_orbits(seed, tmp_path):
    """궤도가 모두 단일인 회로(two_stage_ota)의 dc_colour 는 σ 로 그대로 옮겨진다."""
    raw = lib_doc("two_stage_ota")
    s1 = build_lib(tmp_path / "a", raw, "two_stage_ota")
    d2, sn, se = rename(raw, seed)
    s2 = build_lib(tmp_path / "b", d2, "two_stage_ota", supplies={sn[k]: v for k, v in H.lib_supplies("two_stage_ota").items()})
    on, oe = orbits(s1)
    assert len(set(oe.values())) == len(oe) and len(set(on.values())) == len(on)     # 전제
    nc, ec = colours(s1)
    nc2, ec2 = colours(s2)
    assert {sn[k]: v for k, v in nc.items()} == nc2 and {se[k]: v for k, v in ec.items()} == ec2


@pytest.mark.parametrize("name", ["two_stage_ota", "sf_pushpull_output_opamp", "current_reuse_telescopic_ota"])
def test_reordering_identical(name, tmp_path):
    raw = lib_doc(name)
    s1 = build_lib(tmp_path / "a", raw, name)
    d = json.loads(json.dumps(raw))
    random.Random(7).shuffle(d["netlist"])
    d["passive_elements"] = list(reversed(d["passive_elements"]))
    s2 = build_lib(tmp_path / "b", d, name)
    assert orbits(s2) == orbits(s1) and colours(s2) == colours(s1) and signs(s2) == signs(s1)


def test_deterministic(tmp_path):
    a = build(tmp_path, sym_doc("hand_sym_det", caps=True))
    b = build(tmp_path, sym_doc("hand_sym_det", caps=True))
    assert colours(a) == colours(b) and orbits(a) == orbits(b) and signs(a) == signs(b)
    assert list(a.column("device", "dc_colour")) == list(b.column("device", "dc_colour"))


# ---------------------------------------------------------------- 블록 재사용·키(40 §6-8, NFR-2)

def test_block_reuse_with_same_marks(tmp_path):
    """같은 (supplies, marks) 로 다시 부르면 reuse, 표시가 다르면 다시 계산. S1 키는 marks 지문을 품는다."""
    m = SymmetryMarks(None, element_marks((("CL1", 1e-12), ("CL2", 1e-12))), ())
    s1 = build(tmp_path, sym_doc("hand_sym_r", caps=True), m)
    sup = supplies_declaration(SUP, ("vdd", "gnd"))
    # card B C4 판정 1·4 -- 새 실행 계수(C1)마다 그 호출 하나의 행
    run = H.fresh_run()
    assert s1_symmetry(s1.snapshot, sup, m, **run) is s1.snapshot
    assert [(r.reuses, r.computes) for r in run["counters"].snapshot().blocks if r.block == s1_symmetry.name] == [(1, 0)]
    run2 = H.fresh_run()
    other = SymmetryMarks(None, element_marks((("CL1", 1e-12), ("CL2", 2e-12))), ())
    assert s1_symmetry(s1.snapshot, sup, other, **run2) is not s1.snapshot
    assert [(r.reuses, r.computes) for r in run2["counters"].snapshot().blocks if r.block == s1_symmetry.name] == [(0, 1)]
    plain = build(tmp_path, sym_doc("hand_sym_r", caps=True))
    assert plain.key.marks_fp == "none" and s1.key.marks_fp != "none" and plain.key != s1.key


# ---------------------------------------------------------------- 40 §6-8 MOS d/s 맞바꿈(D-2·D-3) -- red-first test 022467f 를 옮김

def _flip_ds(doc, names, new_name):
    d = json.loads(json.dumps(doc))
    for e in d["netlist"]:
        if e["name"] in names:
            e["drain"], e["source"] = e["source"], e["drain"]
    d["topology_name"] = new_name
    return d


@pytest.mark.parametrize("names", [("M1",), ("M3",), ("M5",), ("M1", "M2", "M3", "M4", "M5")])
def test_ds_flip_colours_and_orbits_bit_identical(names, tmp_path):
    """§6-8 D-3: d/s 표기를 뒤집은 입력(gate 가 d·s 가 아닌 MOS) -> 궤도·정준 위치 기반 dc_colour 비트 동일."""
    doc = sym_doc("hand_sym_ds", caps=True)
    base = build(tmp_path / "a", doc)
    flip = build(tmp_path / "b", _flip_ds(doc, names, "hand_sym_ds_f"))
    assert colours(flip) == colours(base)
    assert orbits(flip) == orbits(base)


def test_ds_flip_library_bit_identical(tmp_path):
    raw = lib_doc("two_stage_ota")
    names = {e["name"] for e in raw["netlist"] if e["gate"] not in (e["drain"], e["source"])}
    assert names
    a = build_lib(tmp_path / "a", raw, "two_stage_ota")
    b = build_lib(tmp_path / "b", _flip_ds(raw, names, raw["topology_name"]), "two_stage_ota")
    assert colours(b) == colours(a) and orbits(b) == orbits(a)


def test_drain_to_source_pair_sign_is_minus_one(tmp_path):
    """§6-8 '전류 부호': Ma(d=a, s=gnd)·Mb(d=gnd, s=b), 같은 gate, a·b 에 같은 커패시터. a<->b 자기동형은 Ma 의 drain(a)을 Mb 의 source(b)로
    보낸다 -> Ma·Mb 같은 궤도, 부호 −1(손 유도)."""
    doc = H.topo("hand_d2s", (mos("Ma", "nmos", "a", "vb", "gnd"), mos("Mb", "nmos", "gnd", "vb", "b"), mos("Mp", "pmos", "a", "pb", "vdd"),
                              mos("Mq", "pmos", "b", "pb", "vdd")),
                 {"vb": H.SE_IN, "a": H.OUT_P, "b": H.OUT_N}, passives=(("CA", "capacitor", ("a", "vdd")), ("CB", "capacitor", ("b", "vdd"))),
                 bias=("pb",))
    s1 = build(tmp_path, doc)
    on, oe = orbits(s1)
    assert oe["Ma"] == oe["Mb"] and on["a"] == on["b"]
    assert any(("Ma", "Mb", -1) in g for g in signs(s1))
    assert any(("Mp", "Mq", 1) in g for g in signs(s1))                      # Mp·Mq: drain a -> drain b (+1)


def test_symmetric_pair_sign_is_plus_one(tmp_path):
    s1 = build(tmp_path, sym_doc("hand_sym_sign"))
    rows = [r for g in signs(s1) for r in g if r[0] in ("M1", "M2")]
    assert rows and all(r[2] == 1 for r in rows)


def test_pilot_r1_r2_one_orbit_sign_minus_one(tmp_path):
    """40 §10.2 '파일럿 R1/R2가 한 궤도로 묶이고 전류 부호는 −1': R1 = (Vom, Voc), R2 = (Voc, Vop) -- Vom<->Vop 반사에서 R1 첫 단자 Vom 의 상은 Vop,
    R2 첫 단자는 Voc -> 부호 −1(topology 연결표 손 유도). M1a/M1b 도 한 궤도(§6-5 '파일럿 M1a/M1b는 같은 궤도')."""
    name = "current_reuse_telescopic_ota"
    s1 = build_lib(tmp_path, lib_doc(name), name)
    oe = orbits(s1)[1]
    assert oe["R1"] == oe["R2"] and oe["M1a"] == oe["M1b"]
    assert any(("R1", "R2", -1) in g for g in signs(s1))


# ---------------------------------------------------------------- 40 §6-8 자기 맞바꿈 = 구조적 0 전류 -> 정지

def _pass_device(with_mx=True):
    """U11 `pass_device` 변형: 완전 차동 M1~M4 + 평균 저항 R1(op, c)·R2(c, om) + 두 출력 사이 통과 MOS Mx(d=op, g=vbx, s=om).
    op<->om 반사는 Mx 를 자기 자신으로 보내며 d/s 를 맞바꾼다(손 유도)."""
    m = [mos("M1", "nmos", "op", "ip", "gnd"), mos("M2", "nmos", "om", "im", "gnd"),
         mos("M3", "pmos", "op", "c", "vdd"), mos("M4", "pmos", "om", "c", "vdd")]
    if with_mx:
        m.append(mos("Mx", "nmos", "op", "vbx", "om"))
    return H.topo("hand_pass_ds%d" % int(with_mx), tuple(m), {"ip": H.DIFF_P, "im": H.DIFF_N, "op": H.OUT_P, "om": H.OUT_N},
                  passives=(("R1", "resistor", ("op", "c")), ("R2", "resistor", ("c", "om"))), bias=("vbx",) if with_mx else ())


def test_ds_self_swap_zero_current_stops(tmp_path):
    with pytest.raises(StructureUnresolvedError) as e:
        build(tmp_path, _pass_device())
    assert exit_code_for(e.value) == 2
    det = dict(e.value.record.detail)
    assert (det["reason"], det["rule_branch"]) == ("unsupported_rule_branch", "ds_self_swap_zero_current")
    assert tuple(e.value.record.devices) == ("Mx",)
    gens = dict(det["generators"])["Mx"]
    assert any(("Mx", "Mx", -1) in g for g in gens)                          # 소자·생성자 기록: Mx 자기 자신, 부호 −1


def test_without_self_swap_device_builds(tmp_path):
    s1 = build(tmp_path, _pass_device(with_mx=False))
    oe = orbits(s1)[1]
    assert oe["M1"] == oe["M2"] and oe["R1"] == oe["R2"]


def test_self_swap_on_rail_anchored_loop_stops(tmp_path):
    """옛 test_branches 의 고리(gnd - Mra - ra - Mrb - rb - Mrc - gnd, gate 모두 같음): ra<->rb 반사(Mra<->Mrc)가 Mrb 를 자기 자신으로 보내며
    d/s 를 맞바꾼다 -> 정지(손 유도). Mrc 의 gate 를 바꾸면 반사가 없어 정지하지 않는다(test_branches 쪽)."""
    raw = lib_doc("two_stage_ota")
    gate = raw["netlist"][0]["gate"]
    raw["netlist"] += [{"name": "Mra", "kind": "nmos", "drain": "ra", "gate": gate, "source": "gnd"},
                       {"name": "Mrb", "kind": "nmos", "drain": "rb", "gate": gate, "source": "ra"},
                       {"name": "Mrc", "kind": "nmos", "drain": "gnd", "gate": gate, "source": "rb"}]
    raw.pop("source_manifest", None)
    with pytest.raises(StructureUnresolvedError) as e:
        build_lib(tmp_path, raw, "two_stage_ota")
    assert tuple(e.value.record.devices) == ("Mrb",)
    assert dict(e.value.record.detail)["rule_branch"] == "ds_self_swap_zero_current"


@pytest.mark.parametrize("name", NINE)
def test_library_no_self_swap(name, tmp_path):
    """40 §6-8 '9 library 회로는 발동 0이다(측정 2026-10-12)' -- build_s1 이 멈추지 않는다."""
    build_lib(tmp_path, lib_doc(name), name)
