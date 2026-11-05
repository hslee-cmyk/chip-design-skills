"""IT-2c 판정 탐침(복제본 전용): 이름 전단사 뒤 구조 색 대응 + _p_port_first 의 cert 불변·자기동형을 직접 잰다. base·head 양쪽."""
import json
import os
import random
import sys

import pytest

from gmid_engine.authoring import load_topology
from gmid_engine.core import fp_of
from gmid_engine.graph import build_s1
import gmid_engine.graph  # noqa: F401
from gmid_engine.search import open_run

from .canon_cases import library_doc, rename_doc

sym = sys.modules["gmid_engine.graph.s1_symmetry"]
cf = sys.modules["gmid_engine.graph.canonical_form"]
OUT = os.environ["PROBE_OUT"]
CIRCUITS = ["cnr_ota", "common_gate_amplifier", "current_reuse_telescopic_ota", "erfc_ota", "folded_cascode", "ngcc_3stage_ff", "nmcnr_amplifier",
            "pushpull_follower_buffer", "r2r_opamp", "rfc_ota", "sf_pushpull_output_opamp", "two_stage_ota", "two_stage_ota_sf"]


def rec(**kw):
    with open(OUT, "ab") as f:
        f.write((json.dumps(kw, ensure_ascii=False, default=str) + "\n").encode("utf-8"))


def _names(doc):
    out = set()
    for e in doc["netlist"]:
        out.add(e["name"])
        for k in ("drain", "gate", "source", "bulk"):
            if k in e:
                out.add(e[k])
    for key in ("passive_elements", "ideal_sources"):
        for e in doc.get(key) or []:
            out.add(e["name"])
            out.update(e["terminals"])
    out.update(doc["supply_nets"])
    out.update(k for k in doc["ports"] if not k.startswith("_"))
    out.update(doc.get("bias_inputs") or [])
    return sorted(out)


def _build(tmp, doc, tag, seen):
    p = tmp / (tag + ".topology.json")
    p.write_text(json.dumps(doc), encoding="utf-8")
    td = load_topology(p)
    donors, counters = open_run()
    sup = {n: 0.9 * i for i, n in enumerate(doc["supply_nets"])}
    seen.clear()
    return build_s1(td, sup, donors=donors, counters=counters)


@pytest.mark.parametrize("circuit", CIRCUITS)
@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
def test_rename(tmp_path, circuit, seed, monkeypatch):
    seen = {}
    real_graph = cf._graph
    real_pf = getattr(sym, "_p_port_first", None)

    def spy_graph(source, em, nm):
        out = real_graph(source, em, nm)
        seen["marked"], seen["nb"] = out
        return out
    monkeypatch.setattr(cf, "_graph", spy_graph)
    if real_pf is not None:
        def spy_pf(position, generators, p_port):
            new = real_pf(position, generators, p_port)
            seen["pf"] = (dict(position), dict(new), p_port)
            return new
        monkeypatch.setattr(sym, "_p_port_first", spy_pf)
    doc = library_doc(circuit)[0]
    for tag in ("symmetry", "device_roles", "sizing_roles", "compensation"):
        doc.pop(tag, None)
    names = _names(doc)
    new = ["z%03d" % i for i in range(len(names))]
    random.Random(seed).shuffle(new)
    sig = dict(zip(names, new))
    a = _build(tmp_path, doc, "a", seen)
    b = _build(tmp_path, rename_doc(doc, sig, circuit + "_r"), "b", seen)
    row = {"circuit": circuit, "seed": seed}
    if "pf" in seen:
        old, pos, p = seen["pf"]
        nb, marked = seen["nb"], seen["marked"]
        ranks = {s: i for i, s in enumerate(sorted(set(marked.values()), key=repr))}
        order = lambda q: tuple(ranks[marked[v]] for v in sorted(q, key=lambda v: q[v]))   # noqa: E731
        edges = lambda q: tuple(sorted((q[v], lab, q[u]) for v in q for lab, u in nb[v]))   # noqa: E731
        row.update(pf_moved=sum(old[v] != pos[v] for v in old), pf_cert_same=(order(old), edges(old)) == (order(pos), edges(pos)), pf_p_pos=(old[p], pos[p]))
    for kind in ("node", "device"):
        ca, cb = dict(a.column(kind, "dc_colour")), dict(b.column(kind, "dc_colour"))
        row[kind + "_mismatch"] = sorted(n for n in ca if ca[n] != cb[sig[n]])
    roles = dict(a.column("node", "port_role"))
    row["p_port_colour_same"] = [dict(a.column("node", "dc_colour"))[n] == dict(b.column("node", "dc_colour"))[sig[n]] for n, r in roles.items() if r == "differential_input_p"]
    row["orbits_same"] = fp_of(a.value("graph", "s1", "orbits").devices and sorted(o for _n, o in a.value("graph", "s1", "orbits").devices)) == fp_of(sorted(o for _n, o in b.value("graph", "s1", "orbits").devices))
    rec(**row)
