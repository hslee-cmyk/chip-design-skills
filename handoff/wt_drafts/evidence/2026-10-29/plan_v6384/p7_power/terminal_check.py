"""plan v6.38.4 P7 조건 실측 -- library 9회로에서 '레일이 아닌 DUT 단자에 DC 전류 경로가 있는가'(있으면 레일 단자 합 ≠ DUT 소산, 기준 전위 의존).

DUT 단자 = ports(입력·출력) ∪ bias_inputs. DC 전류 경로:
  (a) 입력 쪽(입력 포트·bias_inputs -- 구동 원이 거는 단자): 그 넷에 MOS 채널 단자(d/s) 또는 DUT 저항(측정 부하 아님)이 닿음
  (b) 출력 포트(구동 원 없음 -- 밖의 DC 경로는 측정 부하뿐): 저항성 측정 부하(spec element_values measurement_load 인 저항)가 닿음
      -> 출력 DC ≠ 부하 귀환 넷 전위이면 DC 전류(용량성 측정 부하는 DC 전류 0)
출력: terminal.out.jsonl
"""
import json, os, glob
LIB = "C:/Users/HSLEE/Documents/Todoc/fpga/wt/plan-v6384/skills/analog-gmid-design/assets/library"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "terminal.out.jsonl")
rows = []
for f in sorted(glob.glob(os.path.join(LIB, "*.topology.json"))):
    if os.path.basename(f).startswith("_"):
        continue
    name = os.path.basename(f)[:-len(".topology.json")]
    t = json.load(open(f, encoding="utf-8"))
    s = json.load(open(f.replace(".topology.json", ".sizing_spec.json"), encoding="utf-8"))["human"]
    ev = s.get("element_values", {})
    mload = {k for k, v in ev.items() if isinstance(v, dict) and v.get("measurement_load")}
    rails = set(t.get("supply_nets") or [])
    ports = {k: v for k, v in (t.get("ports") or {}).items() if not k.startswith("_")}
    terms = set(ports) | set(t.get("bias_inputs") or [])
    found = []
    for n in sorted(terms - rails):
        chan = [d["name"] for d in t["netlist"] if n in (d["drain"], d["source"])]
        dres = [p["name"] for p in t.get("passive_elements", []) if p["kind"] == "resistor" and n in p["terminals"] and p["name"] not in mload]
        mres = [p["name"] for p in t.get("passive_elements", []) if p["kind"] == "resistor" and n in p["terminals"] and p["name"] in mload]
        direction = ports.get(n, {}).get("direction", "input")      # bias_inputs = 구동 원이 거는 입력 쪽
        dc = bool(mres) if direction == "output" else bool(chan or dres)
        if dc:
            found.append({"net": n, "role": ports.get(n, {}).get("role", "bias_input"), "channel_terminals": chan,
                          "dut_resistors": dres, "measurement_load_resistors": mres})
    rows.append({"circuit": name, "rails": sorted(rails), "nonrail_terminal_dc_paths": found, "differs_possible": bool(found)})
with open(OUT, "w", encoding="utf-8") as fh:
    for r in rows:
        fh.write(json.dumps(r, ensure_ascii=False) + "\n")
print("differs_possible n =", sum(r["differs_possible"] for r in rows), "/", len(rows))
for r in rows:
    print(r["circuit"], r["nonrail_terminal_dc_paths"])
