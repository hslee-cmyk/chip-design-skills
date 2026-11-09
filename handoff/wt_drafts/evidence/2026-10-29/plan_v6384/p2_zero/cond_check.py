"""plan v6.38.4 P2 조건 실측 -- library 9회로에서 'S 밖 출력 소자의 gate 넷이 경로 구동 끝 A와 선언 커패시터로 결합'(C_AG ≠ 0, 조건 밖) 수.

S 정의 = DEC-92 (3)(v6.38.3): 보상 R의 한 끝 넷(mid)에 R과 보상 C만 닿을 때 경로 = R의 다른 끝 ~ 각 C의 다른 끝,
S = 경로 두 끝에 gate·drain이 걸린 MOS 합집합. A = S 셀 gate 끝, B = drain 끝. 대상 = drain이 B에 있고 S 밖인 MOS의 gate 넷 g:
선언 커패시터 {A, g}가 있으면 조건 밖(fail-closed 대상). 측정 부하 원소도 커패시터면 셈(보수 쪽).
출력: cond.out.jsonl
"""
import json, os, glob
LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384/skills/analog-gmid-design/assets/library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cond.out.jsonl")
rows = []
for f in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    if os.path.basename(f).startswith("_"):
        continue
    t = json.load(open(f, encoding="utf-8"))
    name = os.path.basename(f)[:-len(".topology.json")]
    pes = t.get("passive_elements", [])
    mos = t["netlist"]
    touch = {}
    for p in pes:
        for n in p["terminals"]:
            touch.setdefault(n, []).append(p)
    for d in mos:
        for k in ("gate", "drain", "source"):
            touch.setdefault(d[k], []).append(d)
    caps = [p for p in pes if p["kind"] == "capacitor"]
    paths = []
    for r in (p for p in pes if p["kind"] == "resistor"):
        for i, mid in enumerate(r["terminals"]):
            other = r["terminals"][1 - i]
            at = touch.get(mid, [])
            cs = [x for x in at if x is not r and x.get("kind") == "capacitor" and "gate" not in x]
            if not cs or len(cs) + 1 != len(at):
                continue
            for c in cs:
                cend = [n for n in c["terminals"] if n != mid][0]
                for e1, e2 in ((other, cend), (cend, other)):
                    cells = [d["name"] for d in mos if d["gate"] == e1 and d["drain"] == e2]
                    paths.append({"R": r["name"], "C": c["name"], "A": e1, "B": e2, "S_cells": cells})
    viol = []
    for pth in paths:
        if not pth["S_cells"]:
            continue
        S = set(pth["S_cells"])
        for d in mos:
            if d["drain"] == pth["B"] and d["name"] not in S:
                g = d["gate"]
                coupled = [c["name"] for c in caps if set(c["terminals"]) == {pth["A"], g}]
                viol.append({"path": pth["R"] + "-" + pth["C"], "A": pth["A"], "B": pth["B"], "device": d["name"], "gate": g,
                             "declared_cap_A_gate": coupled})
    rec = {"circuit": name, "paths": [p for p in paths if p["S_cells"]], "other_output_devices": viol,
           "condition_out": any(v["declared_cap_A_gate"] for v in viol)}
    rows.append(rec)
with open(OUT, "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print("condition_out n =", sum(r["condition_out"] for r in rows), "/", len(rows))
for r in rows:
    print(r["circuit"], [(p["R"], p["A"], p["B"], p["S_cells"]) for p in r["paths"]], [(v["device"], v["gate"], v["declared_cap_A_gate"]) for v in r["other_output_devices"]])
