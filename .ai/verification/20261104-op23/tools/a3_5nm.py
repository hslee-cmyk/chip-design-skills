# -*- coding: utf-8 -*-
"""A3-5 (2): name_map 단사·전체 덮음, 대소문자 접기 포함. R1~R5 벤치 전부. 사용: a3_5nm.py <iso_v> <run1> <out.json>"""
import json, os, sys
ISO, RUN, OUT = sys.argv[1:4]
O = os.path.join(ISO, "skills/analog-gmid-design/tools/spice_oracle")
sys.path.insert(0, O)
from adapters.ngspice import dialect  # noqa: E402
from core.build_benches import iso_bench, loop_bench  # noqa: E402
from core.build_circuit import circuit_ir  # noqa: E402
from core.descriptor import load_descriptor  # noqa: E402
from core.requests import Condition  # noqa: E402
D = load_descriptor(os.path.join(O, "descriptors/sky130.oracle_descriptor.json"), env=os.environ)
C = Condition(27.0, "tt")
BIAS = {"R1": ["free"], "R2": ["free"], "R3": ["free", "forced"], "R4": ["free", "forced"], "R5": ["iso"]}
res = {}
for rid, bs in BIAS.items():
    inp = json.load(open(os.path.join(RUN, rid, "t.input.json"), encoding="utf-8"))
    for b in bs:
        cs = {"main": iso_bench(inp, C, D)[0] if b == "iso" else circuit_ir(inp, b, descriptor=D)[0]}
        if inp.get("feedback_passives") and b != "iso":
            cs["loop"] = loop_bench(inp, b, C, (), (), D)[0]
        for k, c in cs.items():
            nm = dialect.build_name_map(c)
            names = [e.name for e in c.elements]
            vals = [nm[n] for n in names]
            res[f"{rid}.{b}.{k}"] = {"n": len(names), "covers": set(names) == set(nm), "injective_casefold": len({v.lower() for v in vals}) == len(vals)}
json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(all(v["covers"] and v["injective_casefold"] for v in res.values()), len(res), sum(v["n"] for v in res.values()))
