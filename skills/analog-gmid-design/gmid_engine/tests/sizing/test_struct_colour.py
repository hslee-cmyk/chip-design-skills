"""`dc_struct_colour(snapshot)` -- CONTRACT 3.0 [r2]: 이름 없는 구조 색(1-WL).

- 기대값: conftest `wl_colours`(3.0 문장 그대로 독립 구현: 처음 서명, 라벨 엣지 d·g·s·b·t0·t1·t, 서명 정렬 순위, 색 수가 늘지 않는
  회에서 직전 색)와 정확히 같은 int.
- 성질: 이름 전단사·순서 섞기를 해도 색이 그 전단사로 옮겨진다. 같은 색 = 1-WL 로 구별 안 되는 정점.
"""
import json
import random

import pytest

from gmid_engine.graph import build_s1
from gmid_engine.sizing import dc_struct_colour, lift_s1

from .conftest import (NINE, SUPPLIES, build_ctx, circuit_cs_pmos_load, circuit_cs_res, library_ctx, load_doc, mos,
                       topo, two, wl_colours)


def colours(snap):
    return dict(snap.column("node", "dc_colour")), dict(snap.column("device", "dc_colour"))


def rename(doc, seed):
    """넷·원소 이름 전단사 σ(무작위). 반환 (새 doc, σ_net, σ_el)."""
    d = json.loads(json.dumps(doc))
    nets = set(d["supply_nets"]) | {k for k in d["ports"] if not k.startswith("_")}
    for e in d["netlist"]:
        nets |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
    for key in ("passive_elements", "ideal_sources"):
        for e in d.get(key) or []:
            nets |= set(e["terminals"])
    els = [e["name"] for e in d["netlist"]] + [e["name"] for k in ("passive_elements", "ideal_sources")
                                                for e in (d.get(k) or [])]
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
        if k in ("device_roles", "symmetry", "sizing_roles", "compensation") or (k.startswith("_") and k != "_comment"):
            d.pop(k)
    if "bias_inputs" in d:                                   # authoring 9절 선언도 같은 σ 로 옮긴다(이름 전단사의 일부)
        d["bias_inputs"] = [sn[n] for n in d["bias_inputs"]]
    d["topology_name"] = d["topology_name"] + "_r%d" % seed
    return d, sn, se


def test_hand_circuit_matches_oracle(ctx_c, ctx_a):
    for ctx in (ctx_c[2], ctx_a[2]):
        assert colours(ctx.base) == wl_colours(ctx.base)


@pytest.mark.parametrize("name", NINE)
def test_library_matches_oracle(name, toy_access):
    base = library_ctx(name, toy_access)[5].base
    assert colours(base) == wl_colours(base)
    nc, ec = colours(base)
    assert all(isinstance(v, int) for v in list(nc.values()) + list(ec.values()))
    assert set(nc) == set(base.keys("node")) and set(ec) == set(base.keys("device"))


def test_symmetric_pair_same_colour_and_port_direction_separates(tmp_path, toy_access):
    doc = topo("hand_sym",
               [mos("M1", "nmos", "o1", "inp", "t"), mos("M2", "nmos", "o2", "inn", "t"),
                mos("M5", "nmos", "t", "vb", "gnd"), mos("M3", "pmos", "o1", "pb", "vdd"),
                mos("M4", "pmos", "o2", "pb", "vdd")],
               {"inp": ("input", "a"), "inn": ("input", "a"), "o1": ("output", "b"), "o2": ("output", "b")},
               bias=["pb", "vb"])                                                            # vb: M5 gate, pb: M3·M4 gate
    _, _, ctx = build_ctx(tmp_path, doc, toy_access)
    nc, ec = colours(ctx.base)
    assert ec["M1"] == ec["M2"] and ec["M3"] == ec["M4"] and ec["M1"] != ec["M5"]
    assert nc["inp"] == nc["inn"] and nc["o1"] == nc["o2"]
    # o2 를 출력 포트에서 빼면 대칭이 깨진다 -> 색이 갈린다
    doc2 = json.loads(json.dumps(doc))
    doc2["topology_name"] = "hand_sym2"
    del doc2["ports"]["o2"]
    _, _, ctx2 = build_ctx(tmp_path, doc2, toy_access)
    nc2, ec2 = colours(ctx2.base)
    assert nc2["o1"] != nc2["o2"] and ec2["M1"] != ec2["M2"]
    assert colours(ctx2.base) == wl_colours(ctx2.base)


def test_current_source_direction_matters(tmp_path, toy_access):
    """이상 전류원은 t0·t1 방향 라벨: 같은 넷 쌍에 반대 방향으로 놓으면 두 넷 색이 다르다. 저항(t)은 방향 없음."""
    net = [mos("M1", "nmos", "a", "in", "gnd"), mos("M2", "nmos", "b", "in", "gnd"),
           mos("M3", "pmos", "a", "pb", "vdd"), mos("M4", "pmos", "b", "pb", "vdd")]
    ports = {"in": ("input", "x"), "a": ("output", "y"), "b": ("output", "y")}
    src = topo("hand_src_dir", net, ports, sources=[two("I1", "current_source", "a", "b")], bias=["pb"])  # pb: M3·M4 gate
    res = topo("hand_res_dir", net, ports, passives=[two("R1", "resistor", "a", "b")], bias=["pb"])
    _, _, cs = build_ctx(tmp_path, src, toy_access)
    _, _, cr = build_ctx(tmp_path, res, toy_access)
    assert colours(cs.base) == wl_colours(cs.base) and colours(cr.base) == wl_colours(cr.base)
    assert colours(cr.base)[0]["a"] == colours(cr.base)[0]["b"]           # 저항: a·b 구별 안 됨
    assert colours(cs.base)[0]["a"] != colours(cs.base)[0]["b"]           # 전류원 방향: a·b 구별


@pytest.mark.parametrize("seed", [1, 2, 3])
@pytest.mark.parametrize("name", ["two_stage_ota", "folded_cascode", "current_reuse_telescopic_ota"])
def test_renaming_transports_colours(name, seed, tmp_path, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    d2, sn, se = rename(raw, seed)
    s1b = build_s1(load_doc(tmp_path, d2), {sn[k]: v for k, v in inputs.supplies_v})
    snap2 = dc_struct_colour(lift_s1(s1b))
    nc, ec = colours(ctx.base)
    nc2, ec2 = colours(snap2)
    assert {sn[k]: v for k, v in nc.items()} == nc2
    assert {se[k]: v for k, v in ec.items()} == ec2


@pytest.mark.parametrize("name", ["two_stage_ota", "sf_pushpull_output_opamp"])
def test_reordering_identical(name, tmp_path, toy_access):
    raw, td, spec, inputs, s1, ctx = library_ctx(name, toy_access)
    d = json.loads(json.dumps(raw))
    random.Random(7).shuffle(d["netlist"])
    d["passive_elements"] = list(reversed(d["passive_elements"]))
    snap2 = dc_struct_colour(lift_s1(build_s1(load_doc(tmp_path, d), dict(inputs.supplies_v))))
    assert colours(snap2) == colours(ctx.base)


def test_block_reuse_and_writer(ctx_c):
    base = ctx_c[2].base
    dc_struct_colour.reset_stats()
    assert dc_struct_colour(base) is base                       # 컨텍스트가 이미 계산 -> reuse
    assert dc_struct_colour.stats().reuses == 1
    k = base.keys("node")[0]
    assert base.field("node", k, "dc_colour").writer == "dc_struct_colour"
