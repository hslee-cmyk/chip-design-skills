# 13회로(library 9 + heldout 4) 연결만으로 부유 배터리 꼴 탐지 -- 태그 미사용. 결과: scan13.out.txt
# (A) 부유 상보쌍: nmos·pmos 한 쌍이 같은 두 비레일 넷 {X, Y} 사이에 채널을 두고(한쪽 S=X·D=Y, 다른 쪽 S=Y·D=X), 각 gate 가 서로 다른 비레일 넷
# (B) 그 쌍의 각 소자가 레일 병합 G_vgs 의 순환(gate-source 고리)에 들어 있는가(= translinear 고리) -- 고리 = 그 소자 엣지를 빼도 양 끝이 연결
# (C) 출력단 짝: X·Y 를 gate 로 읽는 소자 중 source 가 레일인 것(push-pull 출력 소자)
import json, pathlib, collections
SK = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")
OUT = pathlib.Path(__file__).with_suffix(".out.txt")
files = sorted((SK / "library").glob("*.topology.json")) + sorted((SK / "heldout").glob("*.topology.json"))
lines = []
for p in files:
    if p.name.startswith("_"):
        continue
    t = json.loads(p.read_text(encoding="utf-8"))
    rails = set(t.get("supply_nets") or [])
    mos = [d for d in t["netlist"] if d.get("kind") in ("nmos", "pmos")]
    F = "<RAIL>"
    node = lambda n: F if n in rails else n
    edges = [(d["name"], node(d["gate"]), node(d["source"])) for d in mos if node(d["gate"]) != node(d["source"])]

    def connected(a, b, skip):
        adj = collections.defaultdict(list)
        for nm, u, v in edges:
            if nm in skip:
                continue
            adj[u].append(v); adj[v].append(u)
        seen, st = {a}, [a]
        while st:
            x = st.pop()
            for y in adj[x]:
                if y not in seen:
                    seen.add(y); st.append(y)
        return b in seen
    pairs = []
    for i, a in enumerate(mos):
        for b in mos[i + 1:]:
            if a["kind"] == b["kind"]:
                continue
            A = {a["source"], a["drain"]}
            if A != {b["source"], b["drain"]} or A & rails or len(A) != 2:
                continue
            if a["source"] != b["drain"]:
                continue
            if a["gate"] in rails or b["gate"] in rails or a["gate"] in A or b["gate"] in A:
                continue
            loops = {}
            for d in (a, b):
                e = (d["name"], node(d["gate"]), node(d["source"]))
                loops[d["name"]] = connected(e[1], e[2], {d["name"]})
            outs = sorted({d["name"] for d in mos if d["gate"] in A and d["source"] in rails})
            pairs.append(dict(pair=(a["name"], b["name"]), nets=sorted(A), gates=(a["gate"], b["gate"]), in_gs_loop=loops, output_devices=outs))
    lines.append(f"{p.parent.name}/{p.name.replace('.topology.json','')}: floating_pairs={len(pairs)}")
    for q in pairs:
        lines.append("   " + json.dumps(q))
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
