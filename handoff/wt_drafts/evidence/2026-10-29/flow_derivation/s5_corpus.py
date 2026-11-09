"""S5. 13 회로 전수: '결합 C + 고저항 DC 바이어스' 꼴(AC 결합 노드) 탐지 -- 연결만 사용(태그·주석 미사용).
정의: 비레일 넷 n 에 커패시터가 닿고, n 의 DC 전도 원소(MOS 채널 단자·저항 단자·이상원 단자)가
(a) 하나뿐이고 그 원소가 저항 또는 MOS 채널(= 그 원소 전류 KCL 0)  -> 'AC 결합 바이어스 노드'.
(b) 0 개                                                         -> 'DC 부유 노드'.
결과: s5_corpus.txt"""
import json, pathlib

ROOT = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
OUT = pathlib.Path(__file__).parent / "s5_corpus.txt"
files = sorted(p for d in ("library", "heldout") for p in (ROOT / d).glob("*.topology.json") if not p.name.startswith("_"))
lines = [f"# S5 corpus scan ({len(files)} topology files)", "| 회로 | 커패시터(단자) | AC 결합/부유 넷 | 그 넷 DC 원소 | 넷의 다른 단자 |", "|---|---|---|---|---|"]
summary = []
for p in files:
    t = json.loads(p.read_text(encoding="utf-8"))
    rails = set(t.get("supply_nets", [])) | {"gnd", "vdd", "vss"}
    for b in t.get("bias_inputs", []) or []:
        rails.add(b if isinstance(b, str) else b.get("net", ""))
    ports = set((t.get("ports") or {}).keys())
    conn = {}
    for m in t["netlist"]:
        for term in ("drain", "gate", "source"):
            kind = "channel" if term != "gate" else "gate"
            conn.setdefault(m[term], []).append((m["name"], m["kind"], term, kind))
    caps = []
    for e in t.get("passive_elements", []) or []:
        for i, n in enumerate(e["terminals"]):
            kind = {"resistor": "resistor", "capacitor": "capacitor"}.get(e["kind"], e["kind"])
            conn.setdefault(n, []).append((e["name"], e["kind"], f"t{i}", kind))
        if e["kind"] == "capacitor":
            caps.append(e)
    for s in t.get("ideal_sources", []) or []:
        for i, n in enumerate(s["terminals"]):
            conn.setdefault(n, []).append((s["name"], s["kind"], f"t{i}", "source"))
    hits = 0
    for c in caps:
        for n in c["terminals"]:
            if n in rails or n in ports:
                continue
            dc = [x for x in conn.get(n, []) if x[3] in ("channel", "resistor", "source")]
            if len(dc) <= 1:
                hits += 1
                lines.append(f"| {t.get('topology_name', p.stem)} | {c['name']}({'-'.join(c['terminals'])}) | {n} | {[f'{x[0]}.{x[2]}' for x in dc] or '없음(부유)'} | {[f'{x[0]}.{x[2]}' for x in conn[n] if x[3] not in ('channel','resistor','source')]} |")
    summary.append((t.get("topology_name", p.stem), p.parent.name, len(caps), hits))
lines += ["", "## 요약 (회로, 위치, 커패시터 수, AC 결합/부유 넷 수)"] + [f"- {s}" for s in summary]
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
