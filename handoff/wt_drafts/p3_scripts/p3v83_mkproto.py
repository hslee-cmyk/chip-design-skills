import sys, re, json, os
root, variant = sys.argv[1], sys.argv[2]
A = os.path.join(root, "skills", "analog-gmid-design", "assets")
sdp = os.path.join(A, "stick_diagram.py")
s = open(sdp, encoding="utf-8").read()
old = "    }\n    return transistors, meta\n"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, "    }\n    meta[\"rails\"] = rail_declaration(data)\n" + ("    meta[\"_g149_unexpected\"] = 1\n" if variant == "p3" else "") + "    return transistors, meta\n")
nets_expr = 'frozenset(topology["supply_nets"])' if variant != "p2" else 'frozenset(list(topology["supply_nets"])[:-1])'
extra = "    polarity: str = 'junk-g149'\n" if variant == "p4" else ""
s += ("\n\nimport dataclasses as _g149_dc\n@_g149_dc.dataclass(frozen=True)\nclass RailDeclaration:\n    nets: frozenset\n" + extra +
      "\n\ndef rail_declaration(topology):\n    return RailDeclaration(nets=" + nets_expr + ")\n")
open(sdp, "w", encoding="utf-8", newline="").write(s)
if variant == "p5":
    lp = os.path.join(A, "library", "two_stage_ota.topology.json")
    t = open(lp, encoding="utf-8").read()
    o = '"supply_nets": ["vdd", "gnd"]'
    assert t.count(o) == 1
    open(lp, "w", encoding="utf-8", newline="").write(t.replace(o, '"supply_nets": ["vdd", "gnd", "agnd"]'))
print("patched", variant)
