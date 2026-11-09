"""DR-1 구조 규칙 발동 자리 전수: 9 library + 4 heldout topology, 연결만(주석·태그 미사용).
비레일 넷마다 DC 전도 원소(MOS 채널 단자, 저항, 이상 전류원, 이상 전압원)를 세고,
DC 원소가 MOS 채널 하나뿐인 넷(DR-1 발동 후보)과 그 MOS의 bulk == source 여부를 적는다."""
import json, pathlib, collections
A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
OUT = pathlib.Path(__file__).with_name("dr1_net_audit.txt")
files = sorted((A/"library").glob("*.topology.json")) + sorted((A/"heldout").glob("*.topology.json"))
files = [f for f in files if not f.name.startswith("_")]
lines = []
kinds = collections.Counter()
for f in files:
    t = json.loads(f.read_text(encoding="utf-8"))
    rails = set(t.get("supply_nets", []))
    ports = {k for k in t.get("ports", {}) if not k.startswith("_")}
    bias = t.get("bias_inputs", [])
    if isinstance(bias, dict): bias = [k for k in bias if not k.startswith("_")]
    bias = set(b if isinstance(b, str) else b.get("net", str(b)) for b in bias)
    net = collections.defaultdict(list)
    mos = {}
    for m in t["netlist"]:
        mos[m["name"]] = m
        for term in ("drain", "source"):
            net[m[term]].append(("mos_channel", m["name"], term))
        net[m["gate"]].append(("gate", m["name"], "gate"))
        if "bulk" in m: net[m["bulk"]].append(("bulk", m["name"], "bulk"))
    for p in t.get("passive_elements", []):
        kinds[("passive", p["kind"])] += 1
        tag = "resistor" if p["kind"] == "resistor" else ("cap" if "cap" in p["kind"] else "passive_" + p["kind"])
        for i, n in enumerate(p["terminals"]):
            net[n].append((tag, p["name"], f"t{i}"))
    for s in t.get("ideal_sources", []):
        kinds[("source", s["kind"])] += 1
        for i, n in enumerate(s["terminals"]):
            net[n].append(("ideal_" + s["kind"], s["name"], f"t{i}"))
    dc_tags = lambda e: e[0] == "mos_channel" or e[0] == "resistor" or e[0].startswith("ideal_") or e[0].startswith("passive_")
    hits = []; single_other = []; zero_dc = []
    for n in sorted(net):
        if n in rails: continue
        dc = [e for e in net[n] if dc_tags(e)]
        if len(dc) == 1:
            e = dc[0]
            if e[0] == "mos_channel":
                m = mos[e[1]]
                other = m["source"] if e[2] == "drain" else m["drain"]
                hits.append((n, e, m.get("bulk"), other, other in rails, m.get("bulk") == other))
            else:
                single_other.append((n, e))
        elif len(dc) == 0:
            zero_dc.append(n)
    lines.append(f"== {f.parent.name}/{f.name}  rails={sorted(rails)}")
    for h in hits:
        n, e, bulk, other, other_rail, bs = h
        lines.append(f"   DR-1 후보: net {n} <- {e[1]}.{e[2]} 채널 하나뿐; 반대 단자 넷 = {other} (rail={other_rail}); bulk = {bulk}; bulk==반대단자(source) = {bs}; port={n in ports}; bias_input={n in bias}")
    for n, e in single_other:
        lines.append(f"   (참고) DC 원소 하나뿐(MOS 아님): net {n} <- {e[0]} {e[1]}.{e[2]}; port={n in ports}")
    lines.append(f"   DC 원소 0인 비레일 넷: {zero_dc}  (port∩={sorted(set(zero_dc)&ports)}, bias_inputs∩={sorted(set(zero_dc)&bias)})")
    lines.append(f"   DR-1 후보 수 = {len(hits)}")
lines.append(f"\n소자 종류: {dict(kinds)}")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
