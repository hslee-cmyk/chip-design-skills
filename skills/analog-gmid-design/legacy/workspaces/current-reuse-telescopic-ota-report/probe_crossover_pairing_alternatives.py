# -*- coding: utf-8 -*-
"""세션16 재설계 조사용 격리 스크립트 (프로덕션 코드 변경 없음).

질문: M6 그룹(odd_nodes=4: Vx, Vom1, Vop1, Vbias2)에서 crossover 가상엣지 짝짓기를
현재 방식(node_map 우선순위: Vom1<->Vop1, Vx<->Vbias2)이 아니라 **다른 두 가지 방식**
으로 하면, M1a/M1b 또는 M2a/M2b가 같은 세그먼트에 남는 경우가 있는가?
-- 4개 홀수차수 노드의 완전짝짓기(perfect matching)는 정확히 3가지뿐이므로 전수 확인 가능.
"""
import os
import sys
import itertools

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "skills", "analog-gmid-design", "assets"))

from stick_diagram import (  # noqa: E402
    load_topology, geometry_colocation_union, build_graph, check_euler_condition,
    hierholzer, _dc_replace,
)

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "..", "skills", "analog-gmid-design", "assets", "library")

trs, meta = load_topology(os.path.join(LIB, "current_reuse_telescopic_ota.topology.json"))
pairs_meta = meta["symmetry"]["matching_pairs"]
forced = [tuple(p["names"]) for p in pairs_meta if p.get("current_forced")]
groups = geometry_colocation_union(trs, forced)
m6_names = groups["M6"]
by_name = {t.name: t for t in trs}
m6_trs = [_dc_replace(by_name[n], stack_id="M6") for n in m6_names]


def decompose(virtual_pairs):
    g = build_graph(m6_trs)
    for k, (u, w) in enumerate(virtual_pairs):
        edge_id = f"__crossover_virtual__{k}"
        g.edges[edge_id] = ("__virtual__", u, w)
        g.adjacency[u].append((edge_id, w))
        g.adjacency[w].append((edge_id, u))
    verdict = check_euler_condition(g)
    assert verdict.kind == "circuit", verdict
    node_seq, tr_seq = hierholzer(g, verdict.start)

    virtual_positions = [i for i, name in enumerate(tr_seq) if name == "__virtual__"]
    rotate_at = virtual_positions[0] + 1
    tr_seq = tr_seq[rotate_at:] + tr_seq[:rotate_at]
    node_seq = node_seq[rotate_at:] + node_seq[1:rotate_at + 1]

    segments = []
    cur_tr, cur_nodes = [], [node_seq[0]]
    for i, name in enumerate(tr_seq):
        if name == "__virtual__":
            if cur_tr:
                segments.append({"transistor_sequence": cur_tr, "node_sequence": cur_nodes})
            cur_tr, cur_nodes = [], [node_seq[i + 1]]
        else:
            cur_tr.append(name)
            cur_nodes.append(node_seq[i + 1])
    if cur_tr:
        segments.append({"transistor_sequence": cur_tr, "node_sequence": cur_nodes})
    return segments


baseline_g = build_graph(m6_trs)
odd = check_euler_condition(baseline_g).odd_nodes
print(f"odd_nodes = {odd}")
assert len(odd) == 4

# 4개 노드의 완전짝짓기는 정확히 3가지뿐이다.
a, b, c, d = odd
matchings = [
    [(a, b), (c, d)],
    [(a, c), (b, d)],
    [(a, d), (b, c)],
]

for i, mp in enumerate(matchings):
    print()
    print(f"=== 짝짓기 옵션 {i+1}: {mp} ===")
    segs = decompose(mp)
    seg_of = {}
    for si, seg in enumerate(segs):
        names = sorted(set(seg["transistor_sequence"]))
        seg_of.update({n: si for n in names})
        print(f"  segment{si}: devices={names}  seq={seg['transistor_sequence']}")
    same_m1 = seg_of.get("M1a") == seg_of.get("M1b")
    same_m2 = seg_of.get("M2a") == seg_of.get("M2b")
    print(f"  M1a/M1b 같은 세그먼트? {same_m1}   M2a/M2b 같은 세그먼트? {same_m2}")
