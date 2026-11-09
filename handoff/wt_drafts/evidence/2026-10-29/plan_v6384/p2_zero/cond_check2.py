"""plan v6.38.4 P2 조건 재계수(검증 2 MJ-1 반영) -- 결합 꼴을 소자 종류가 아니라 구조로: S 밖 출력 소자(drain = B)의 gate 넷 G가
교류 접지(레일·bias_inputs·입력 포트)가 아니고 A와 고주파 결합 경로가 있으면 조건 밖.
결합 경로 = (a) 선언 커패시터 {A, G} (b) MOS 한 단자가 A, 다른 단자가 G -- gate 낀 쌍(Cgs·Cgd) / 채널 두 단자(Cds)로 나눠 셈.
출력: cond2.out.jsonl"""
import json, os, glob
LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384/skills/analog-gmid-design/assets/library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cond2.out.jsonl")
prev = {json.loads(l)["circuit"]: json.loads(l) for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cond.out.jsonl"), encoding="utf-8")}
rows = []
for f in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    if os.path.basename(f).startswith("_"): continue
    t = json.load(open(f, encoding="utf-8")); name = os.path.basename(f)[:-len(".topology.json")]
    acgnd = set(t.get("supply_nets") or []) | set(t.get("bias_inputs") or []) | {k for k, v in (t.get("ports") or {}).items() if not k.startswith("_") and v.get("direction") == "input"}
    caps = [p for p in t.get("passive_elements", []) if p["kind"] == "capacitor"]
    found = []
    for pth in prev[name]["paths"]:
        A, B, S = pth["A"], pth["B"], set(pth["S_cells"])
        for d in t["netlist"]:
            if d["drain"] != B or d["name"] in S: continue
            G = d["gate"]
            if G in acgnd:
                found.append({"path": pth["R"], "device": d["name"], "G": G, "coupling": "G = 교류 접지(h = 0)"}); continue
            cap = [c["name"] for c in caps if set(c["terminals"]) == {A, G}]
            gate_pair = [m["name"] for m in t["netlist"] if (m["gate"] == A and G in (m["drain"], m["source"])) or (m["gate"] == G and A in (m["drain"], m["source"]))]
            chan_pair = [m["name"] for m in t["netlist"] if {m["drain"], m["source"]} == {A, G}]
            found.append({"path": pth["R"], "device": d["name"], "G": G, "declared_cap": cap, "mos_gate_coupling": gate_pair, "mos_channel_coupling_cds": chan_pair})
    out_decl_or_gate = any(x.get("declared_cap") or x.get("mos_gate_coupling") for x in found)
    out_any = out_decl_or_gate or any(x.get("mos_channel_coupling_cds") for x in found)
    rows.append({"circuit": name, "checks": found, "out_decl_or_gate": out_decl_or_gate, "out_including_cds": out_any})
with open(OUT, "w", encoding="utf-8") as fh:
    for r in rows: fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print("조건 밖(선언 C·gate 낀 MOS) n =", sum(r["out_decl_or_gate"] for r in rows), "/ 9;  Cds 포함 n =", sum(r["out_including_cds"] for r in rows), "/ 9")
for r in rows:
    if r["checks"]: print(r["circuit"], r["checks"])
