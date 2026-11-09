"""erfc_ota 넷별 원소 열거 (연결만 -- 주석·태그 미사용). 결과는 net_audit.txt 에 쓴다."""
import json, pathlib, collections

TOPO = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/heldout/erfc_ota.topology.json")
OUT = pathlib.Path(__file__).with_name("net_audit.txt")
t = json.loads(TOPO.read_text(encoding="utf-8"))
rails = set(t["supply_nets"])
net = collections.defaultdict(list)          # net -> [(elem, terminal, dc_path?)]
for m in t["netlist"]:
    for term in ("drain", "gate", "source", "bulk"):
        dc = {"drain": "channel", "source": "channel", "gate": "gate(no DC)", "bulk": "bulk junction(reverse, ~0)"}[term]
        net[m[term]].append((m["name"], m["kind"], term, dc))
for p in t["passive_elements"]:
    dc = "resistor" if p["kind"] == "resistor" else "capacitor(no DC)"
    for i, n in enumerate(p["terminals"]):
        net[n].append((p["name"], p["kind"], f"t{i}", dc))
for s in t["ideal_sources"]:
    for i, n in enumerate(s["terminals"]):
        net[n].append((s["name"], s["kind"], f"t{i}", "ideal current source"))

lines = []
focus = ["n_m5g", "n_m6g", "n_m8g", "Z", "X", "Y", "vcn", "vcp"]
for n in focus:
    lines.append(f"== {n} (rail={n in rails})")
    for e in net[n]:
        lines.append(f"   {e[0]:8s} {e[1]:16s} {e[2]:7s} {e[3]}")
    dc_paths = [e for e in net[n] if e[3] in ("channel", "resistor", "ideal current source")]
    lines.append(f"   -> DC 전도 원소(채널·저항·이상원) = {[f'{e[0]}.{e[2]}' for e in dc_paths]}")

# 구조적 0 전류 판정: 비레일 넷 중 DC 전도 원소가 정확히 하나인 넷 -> 그 원소 전류 = 0 (KCL)
lines.append("\n== 구조적 0 전류 (비레일 넷의 DC 전도 원소가 하나뿐)")
for n in sorted(net):
    if n in rails:
        continue
    dc_paths = [e for e in net[n] if e[3] in ("channel", "resistor", "ideal current source")]
    if len(dc_paths) == 1:
        lines.append(f"   {n}: {dc_paths[0][0]}.{dc_paths[0][2]} -> I = 0 (KCL)")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
