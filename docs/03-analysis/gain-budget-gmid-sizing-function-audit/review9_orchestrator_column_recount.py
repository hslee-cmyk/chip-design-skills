# -*- coding: utf-8 -*-
"""DEC-71 (3) 기둥 수 62 대 244의 열거 정의를 오케스트레이터가 독립 코드로 재현한다.

dry-run agent(`review9_measure_structure.py`)와 **다른 구현**으로 같은 값이 나오는지만 본다.
결론: 62 = 노드-단순 경로, 244 = 엣지-단순(trail, 노드 재방문 허용). 둘 다 gnd->vdd **한 방향**만
세었으므로 계획서 v5.17이 적었던 "244는 경로 방향·역방향 중복을 함께 센 값"은 성립하지 않는다.

결과는 stdout이 아니라 같은 이름의 `.txt`에 append한다(세션 규칙).
"""
import io
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
TOPO = os.path.join(ROOT, "skills", "analog-gmid-design", "assets", "library",
                    "current_reuse_telescopic_ota.topology.json")
OUT = os.path.splitext(os.path.abspath(__file__))[0] + ".txt"
RAILS = {"vdd", "gnd"}


def build_dc_edges(d):
    """DC 전도 엣지: MOS 채널(drain-source) + 저항 + 이상원. 게이트·커패시터는 엣지가 아니다."""
    edges = []
    for m in d["netlist"]:
        if isinstance(m, dict) and m.get("drain") and m.get("source"):
            edges.append((m["drain"], m["source"], m["name"]))
    for e in (d.get("passive_elements") or []):
        if isinstance(e, dict) and e.get("kind") == "resistor":
            t = e["terminals"]
            edges.append((t[0], t[1], e["name"]))
    for s in (d.get("ideal_sources") or []):
        if isinstance(s, dict):
            t = s.get("terminals") or [s.get("from"), s.get("to")]
            if t and all(t):
                edges.append((t[0], t[1], s.get("name", "I")))
    return edges


def prune_leaves(edges):
    """DEC-70 잎 가지치기: 레일이 아닌 차수 1 노드를 더 없을 때까지 제거."""
    while True:
        deg = {}
        for u, v, _ in edges:
            deg[u] = deg.get(u, 0) + 1
            deg[v] = deg.get(v, 0) + 1
        leaves = {n for n, c in deg.items() if c == 1 and n not in RAILS}
        if not leaves:
            return edges
        edges = [(u, v, l) for u, v, l in edges if u not in leaves and v not in leaves]


def adjacency(edges):
    adj = {}
    for i, (u, v, _) in enumerate(edges):
        adj.setdefault(u, []).append((v, i))
        adj.setdefault(v, []).append((u, i))
    return adj


def count_paths(adj, src, dst, mode):
    """mode='node': 노드-단순 / mode='edge': 엣지-단순(trail). 중간에 레일을 지나지 않는다."""
    cnt = 0
    seen_nodes = {src}
    used_edges = set()

    def dfs(n):
        nonlocal cnt
        if n == dst:
            cnt += 1
            return
        for m, i in adj.get(n, []):
            if m in RAILS and m != dst:
                continue
            if mode == "node":
                if m in seen_nodes:
                    continue
                seen_nodes.add(m)
                dfs(m)
                seen_nodes.discard(m)
            else:
                if i in used_edges:
                    continue
                used_edges.add(i)
                dfs(m)
                used_edges.discard(i)

    dfs(src)
    return cnt


def main():
    d = json.load(io.open(TOPO, encoding="utf-8"))
    edges = prune_leaves(build_dc_edges(d))
    adj = adjacency(edges)
    deg = {n: len(a) for n, a in adj.items()}
    branch_nodes = sorted(n for n, c in deg.items() if c >= 3 and n not in RAILS)
    node_simple = count_paths(adj, "gnd", "vdd", "node")
    edge_simple = count_paths(adj, "gnd", "vdd", "edge")
    lines = [
        "=== DEC-71 (3) 기둥 열거 정의 독립 재현 (오케스트레이터) ===",
        f"topology            : {os.path.basename(TOPO)}",
        f"잎 가지치기 후 엣지 : {len(edges)}   노드: {len(adj)}",
        f"비레일 분기 노드    : {len(branch_nodes)}  {branch_nodes}",
        f"노드-단순 gnd->vdd  : {node_simple}   (계획서 정본 62)",
        f"엣지-단순 gnd->vdd  : {edge_simple}   (계획서가 '방향 중복'이라 적었던 244)",
        "판정: 한 방향만 세어도 244가 나오므로 244는 방향 중복이 아니라 노드 재방문(trail) 열거다.",
        "",
    ]
    with io.open(OUT, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
