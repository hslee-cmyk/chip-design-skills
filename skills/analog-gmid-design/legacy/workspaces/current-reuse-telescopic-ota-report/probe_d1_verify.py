# -*- coding: utf-8 -*-
"""세션17 D-1 구현 검증용 격리 스크립트 (프로덕션 코드 변경 없음).

질문: `_select_crossover_pairing()`(세션17 신설)이 세션16 D-1이 손으로 찾은 대안
짝짓기(Vbias2를 Vom1/Vop1과, 나머지를 Vx와 짝짓기 -- crossover는 미매칭 M57/M58
쪽에서만)를 실제로 자동으로 찾아내는지, M6 그룹(current_reuse_telescopic_ota) 실제
connectivity로 확인한다. `probe_crossover_pairing_alternatives.py`(세션16, 손으로
3가지 완전짝짓기를 전수 대입)의 발견을 자동화 로직으로 재확인하는 후속 스크립트.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "..", "..", "skills", "analog-gmid-design", "assets"))

from stick_diagram import (  # noqa: E402
    load_topology, geometry_colocation_union, build_graph, check_euler_condition,
    _dc_replace, _mirror_node_map_from_pairs, _pair_odd_nodes_by_mirror,
    _build_crossover_segments, _count_matching_pair_splits, _select_crossover_pairing,
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
m6_inside_pairs = [tuple(p["names"]) for p in pairs_meta if set(p["names"]) <= set(m6_names)]
print("M6 그룹:", sorted(m6_names))
print("그룹 내 matching_pairs:", m6_inside_pairs)

g = build_graph(m6_trs)
odd = check_euler_condition(g).odd_nodes
print("odd_nodes:", odd)

node_map = _mirror_node_map_from_pairs(m6_inside_pairs, m6_trs)
heuristic_pairs, fallback_used = _pair_odd_nodes_by_mirror(odd, node_map)
heuristic_segments = _build_crossover_segments(m6_trs, heuristic_pairs)
heuristic_splits = _count_matching_pair_splits(heuristic_segments, m6_inside_pairs)
print(f"\n옛 tier1 짝짓기(세션15/16): {heuristic_pairs}")
for i, seg in enumerate(heuristic_segments):
    print(f"  seg{i}: {seg['transistor_sequence']}")
print(f"  splits={heuristic_splits} (세션16 D-1이 발견한 값과 일치해야 함: 2)")

pairs, segments, fb, skipped = _select_crossover_pairing(odd, node_map, m6_trs, m6_inside_pairs)
final_splits = _count_matching_pair_splits(segments, m6_inside_pairs)
print(f"\n세션17 _select_crossover_pairing() 결과: {pairs}")
for i, seg in enumerate(segments):
    print(f"  seg{i}: {seg['transistor_sequence']}")
print(f"  splits={final_splits} (0이어야 함 -- D-1이 손으로 찾은 대안과 일치하는지 확인)")

assert heuristic_splits == 2, "회귀: 옛 tier1 짝짓기가 더 이상 M6 그룹을 안 갈라놓음"
assert final_splits == 0, "세션17 재작성이 목표(matching_pairs 분할 0)를 못 달성함"
print("\nPASS: splits 2 -> 0 개선 확인, D-1 발견이 자동 로직으로 재현됨")
