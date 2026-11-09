# R3 표지 조건 실측 -- '용량 전용 노드(DC 경로 없음)'가 있는 library 회로 수.
# DC 경로 = MOS drain·source, 저항 단자, 이상 전원 단자, 공급 넷, 입력 포트, bias_inputs(구동 넷). MOS gate·bulk·커패시터 단자는 DC 경로가 아니다.
# 연결 필드만 읽는다(태그 미사용). 결과 = r3_capnode_count.txt(덮어씀).
import json, glob, pathlib
HERE = pathlib.Path(__file__).parent
A = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets/library")
out = ["# R3 용량 전용 노드 수 (topology.json 연결 필드)"]
hit = tot = 0
for f in sorted(glob.glob(str(A / "*.topology.json"))):
    if f.endswith("_TEMPLATE.topology.json"):
        continue
    d = json.loads(pathlib.Path(f).read_text(encoding="utf-8"))
    nets, dc = set(), set(d.get("supply_nets") or [])
    dc |= {n for n, p in (d.get("ports") or {}).items() if not n.startswith("_") and isinstance(p, dict) and p.get("direction") == "input"}
    dc |= set(d.get("bias_inputs") or [])
    for e in d.get("netlist", []):
        if e.get("kind") in ("nmos", "pmos"):
            nets |= {e["drain"], e["gate"], e["source"]} | ({e["bulk"]} if e.get("bulk") else set())
            dc |= {e["drain"], e["source"]}
    for e in d.get("passive_elements") or []:
        t = e.get("terminals") or []
        nets |= set(t)
        if e.get("kind") != "capacitor":
            dc |= set(t)
    for e in d.get("ideal_sources") or []:
        t = e.get("terminals") or [e.get(k) for k in ("plus", "minus", "pos", "neg") if e.get(k)]
        nets |= set(t); dc |= set(t)
    caponly = sorted(nets - dc)
    tot += 1; hit += bool(caponly)
    out.append(f"{pathlib.Path(f).name} | 넷 {len(nets)} | 용량 전용(DC 경로 없음) {caponly}")
out.append(f"용량 전용 노드가 있는 회로 {hit}/{tot} (gate 전용 넷은 bias_inputs·포트가 아니면 여기에 들어간다 -- 그 넷이 커패시터에만 닿는지는 행에서 읽는다)")
(HERE / "r3_capnode_count.txt").write_bytes(("\n".join(out) + "\n").encode("utf-8"))
print("\n".join(out))
