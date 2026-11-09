"""묶음 III (봉인 9 구조적 0 전류) -- KCL 항등 0 MOS 전수 (13 회로, 엔진 import 없음).

정의(넷리스트 연결에서 유도):
  DC 전도 그래프 G: 노드 = 넷, 간선 = MOS 채널(drain-source), 저항, 이상 전류원.
    MOS gate·커패시터는 DC 전류 0 (간선 아님). bulk 접합은 이상 KCL에서 0 (누설은 SPICE 단계에서 따로 본다).
  고정 넷(외부가 전위를 정하고 전류를 대는 넷): supply_nets ∪ bias_inputs ∪ 방향 input 포트 -> 하나의 노드 FIXED 로 합침.
  MOS m 의 채널 간선 e = (d, s):
    (Z1) d == s                                     -> VDS = 0 이므로 ID = 0
    (Z2) G - e 에서 d 쪽 또는 s 쪽 연결 성분이 FIXED 를 포함하지 않음
         -> 그 성분(섬)의 경계를 지나는 DC 간선이 e 하나뿐 -> KCL: I_e = 0 (섬 안 원소 값과 무관)
  출력 포트는 고정이 아님(개루프). 민감도로 출력 포트도 고정한 경우를 같이 센다(폐루프 측정 구성 가정).
결과는 kcl_zero_audit.txt 에 회로마다 append.
"""
import glob, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "kcl_zero_audit.txt"
ASSETS = pathlib.Path(r"C:/Users/HSLEE/Documents/Todoc/fpga/chip-design-skills/skills/analog-gmid-design/assets")


def log(t):
    with OUT.open("a", encoding="utf-8") as f:
        f.write(t + "\n")
    print(t)


def comp(adj, start, banned_edge):
    seen = {start}
    stack = [start]
    while stack:
        n = stack.pop()
        for (m, eid) in adj.get(n, ()):
            if eid == banned_edge or m in seen:
                continue
            seen.add(m)
            stack.append(m)
    return seen


def audit(path, fix_outputs):
    t = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    fixed = set(t.get("supply_nets") or [])
    bi = t.get("bias_inputs") or []
    for b in bi:
        fixed.add(b if isinstance(b, str) else b.get("net") or b.get("name"))
    for p, v in (t.get("ports") or {}).items():
        if p.startswith("_") or not isinstance(v, dict):
            continue
        if v.get("direction") == "input" or (fix_outputs and v.get("direction") == "output"):
            fixed.add(p)
    F = "__FIXED__"
    nn = lambda x: F if x in fixed else x
    edges = []  # (eid, a, b, label)
    for m in t["netlist"]:
        edges.append((m["name"], nn(m["drain"]), nn(m["source"]), "mos"))
    for p in t.get("passive_elements") or []:
        if p.get("kind") == "resistor":
            a, b = p["terminals"]
            edges.append((p["name"], nn(a), nn(b), "res"))
    for s in t.get("ideal_sources") or []:
        if s.get("kind") == "current_source":
            a, b = s["terminals"]
            edges.append((s["name"], nn(a), nn(b), "isrc"))
        else:
            a, b = s["terminals"]  # 전압원: 두 넷을 묶는 DC 간선(전류 자유)
            edges.append((s["name"], nn(a), nn(b), "vsrc"))
    adj = {}
    for eid, a, b, _ in edges:
        adj.setdefault(a, []).append((b, eid))
        adj.setdefault(b, []).append((a, eid))
    hits = []
    for m in t["netlist"]:
        d, s = nn(m["drain"]), nn(m["source"])
        if d == s:
            if m["drain"] == m["source"]:
                hits.append((m["name"], "Z1 d==s", m["drain"]))
            # 두 단자가 모두 고정 넷(서로 다른 레일)이면 섬 아님 -> 제외
            continue
        cd = comp(adj, d, m["name"])
        if s in cd:
            continue  # e 가 다리(bridge)가 아님 -> 다른 DC 경로 있음
        cs = comp(adj, s, m["name"])
        isl = [side for side, c in (("drain", cd), ("source", cs)) if F not in c]
        if isl:
            side = isl[0]
            c = cd if side == "drain" else cs
            hits.append((m["name"], f"Z2 섬={side}", "{" + ",".join(sorted(c)) + "}"))
    return hits, len(t["netlist"])


if __name__ == "__main__":
    OUT.write_text("# KCL 항등 0 MOS 전수 (kcl_zero_audit.py, 엔진 import 0)\n", encoding="utf-8")
    files = [f for f in sorted(glob.glob(str(ASSETS / "library" / "*.topology.json"))) if "_TEMPLATE" not in f]
    files += sorted(glob.glob(str(ASSETS / "heldout" / "*.topology.json")))
    for fix_out in (False, True):
        log(f"\n## 출력 포트 고정 = {fix_out}")
        log("| 회로 | MOS 수 | KCL 항등 0 MOS | 근거 |")
        log("|---|---|---|---|")
        n_hit = 0
        for f in files:
            hits, n = audit(f, fix_out)
            name = pathlib.Path(f).parent.name + "/" + pathlib.Path(f).name.replace(".topology.json", "")
            n_hit += bool(hits)
            log(f"| {name} | {n} | {', '.join(h[0] for h in hits) or '-'} | {'; '.join(h[1] + ' ' + h[2] for h in hits) or '-'} |")
        log(f"해당 회로 수 = {n_hit}/{len(files)}")
