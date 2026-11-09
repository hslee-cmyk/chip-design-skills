"""q2_cbox m1: 13 spec 수동소자 면적 선언·면적 제약·θ 상자 전수 (읽기 전용).
출력: m1_spec_census.txt (회로마다 append)."""
import glob, json, pathlib

A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
OUT = pathlib.Path(__file__).with_suffix(".txt")
OUT.write_text("", encoding="utf-8")


def emit(s):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(s + "\n")


tot = {"n": 0, "area_c": 0, "theta_c": 0, "theta_c_no_box": 0, "undef_passive": 0}
for spec in sorted(glob.glob(str(A / "library/*.sizing_spec.json")) + glob.glob(str(A / "heldout/*.sizing_spec.json"))):
    sp = pathlib.Path(spec)
    name = sp.name.replace(".sizing_spec.json", "")
    s = json.loads(sp.read_text(encoding="utf-8"))
    t = json.loads((sp.parent / f"{name}.topology.json").read_text(encoding="utf-8"))
    h = s["human"]
    ev = h.get("element_values", {}) or {}
    tb = ((h.get("search") or {}).get("theta_bounds") or {})
    area = [c for c in h.get("constraints", []) if c.get("metric") == "area_search_m2"]
    pend_area = [c for c in h.get("pending_constraints", []) if "area" in json.dumps(c)]
    pm = [c.get("value") for c in h.get("constraints", []) if c.get("metric") == "pm_ss_deg"]
    tot["n"] += 1
    tot["area_c"] += bool(area)
    rows = []
    for e in t.get("passive_elements", []):
        el = e["name"]; kind = e["kind"]
        tv = e.get("value_farad", e.get("value_ohm"))
        d = ev.get(el, {})
        if d.get("measurement_load"):
            src = "measurement_load(면적 제외)"
        elif d.get("engine"):
            box = tb.get(el)
            src = "θ(engine) box=" + (f"[{box['min']:.3g},{box['max']:.3g}]" if box else "미선언")
            if kind == "capacitor":
                tot["theta_c"] += 1
                if not box:
                    tot["theta_c_no_box"] += 1
        elif any(k.startswith("value") for k in d) or tv is not None:
            v = next((d[k] for k in d if k.startswith("value")), tv)
            src = f"선언값 {v}"
        else:
            src = "값 미정"
            tot["undef_passive"] += 1
        rows.append(f"    {el:10s} {kind:9s} {src}")
    emit(f"{sp.parent.name}/{name}: area_search_m2={'%g' % area[0]['value'] if area else '없음'}"
         f"{' (pending: ' + str(pend_area) + ')' if pend_area else ''}  pm_ss_deg={pm or '없음'}  passives={len(rows)}")
    for r in rows:
        emit(r)
emit("")
emit("요약: " + json.dumps(tot, ensure_ascii=False))
