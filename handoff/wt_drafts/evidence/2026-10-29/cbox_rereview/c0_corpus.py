"""C0. library·heldout 13회로 커패시터 전수: 연결·값·spec(engine)·theta_bounds·양 끝 넷의 단자 -> 역할 분류 근거.
결과: c0_corpus.txt (덮어씀). 읽기 전용."""
import json, glob, os, pathlib
A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
OUT = pathlib.Path(__file__).with_suffix(".txt")
lines = []
for top in sorted(glob.glob(str(A / "library/*.topology.json")) + glob.glob(str(A / "heldout/*.topology.json"))):
    if "_TEMPLATE" in top:
        continue
    t = json.load(open(top, encoding="utf-8"))
    name = os.path.basename(top).replace(".topology.json", "")
    sp = top.replace(".topology.json", ".sizing_spec.json")
    s = json.load(open(sp, encoding="utf-8")) if os.path.exists(sp) else {}
    h = s.get("human", s)
    ev = h.get("element_values", {}) or {}
    tb = (h.get("search", {}) or {}).get("theta_bounds", {}) or {}
    term = {}
    for m in t["netlist"]:
        for r in ("gate", "drain", "source"):
            term.setdefault(m[r], []).append(f"{m['name']}.{r[0]}")
    for p in t.get("passive_elements", []) or []:
        for x in p["terminals"]:
            term.setdefault(x, []).append(p["name"])
    caps = [p for p in (t.get("passive_elements") or []) if p["kind"] == "capacitor"]
    lines.append(f"## {name}  (caps {len(caps)})")
    for p in caps:
        a, b = p["terminals"]
        e = ev.get(p["name"]) if isinstance(ev, dict) else None
        eng = e.get("engine") if isinstance(e, dict) else None
        val = p.get("value_farad")
        if isinstance(e, dict) and e.get("value") is not None:
            val = e["value"]
        bx = tb.get(p["name"])
        lines.append(f"- {p['name']}: {a} -- {b} | value {val} | engine {eng} | theta_bounds "
                     f"{None if bx is None else (bx.get('min'), bx.get('max'))}")
        lines.append(f"    {a}: {term.get(a)}")
        lines.append(f"    {b}: {term.get(b)}")
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
