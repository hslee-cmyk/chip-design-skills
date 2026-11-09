"""SPICE 동작점 대 손계산 대조 표(소자 전류·gm/ID·여유, 노드)."""
import json, sys
des = json.load(open(sys.argv[1], encoding="utf-8"))
sp = json.load(open(sys.argv[2], encoding="utf-8"))
R = json.load(open(sys.argv[3], encoding="utf-8"))
out = open(sys.argv[4], "w", encoding="utf-8")
out.write("node hand spice\n")
for n, v in R["nodes"].items():
    out.write("%-6s %.4f %s\n" % (n, v, sp.get(n)))
out.write("dev m w_s  ID_hand  ID_spice  gmid_hand gmid_spice  margin_hand margin_spice\n")
for n, d in des["devices"].items():
    if n.startswith("DUM"):
        continue
    s = sp["dev"].get(n.upper(), {})
    h = R["dev"].get(n, {})
    idt = s.get("id", 0) * d["m"]
    gmt = s.get("gm", 0) * d["m"]
    out.write("%-4s %3d %.2f %8.3f %8.3f %6.2f %6.2f %7.3f %7.3f\n" % (n, d["m"], d["w_s"] * 1e6, h.get("ID", 0) * 1e6, abs(idt) * 1e6,
              h.get("gmid", 0), gmt / abs(idt) if idt else 0, h.get("margin", 0), sp["margins"].get(n.upper(), float("nan"))))
out.close()
